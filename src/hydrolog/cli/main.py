"""Entry point of the ``hydrolog`` command (``hydrolog.cli.main:main``).

The command line is generated from the catalog
(:func:`hydrolog.catalog.data_commands`)::

    hydrolog <group> <command> --option VALUE ... [--json] [--schema] [--lang pl|en]
                                                  [-v | -q]
    hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]
    hydrolog [--version]

``main`` returns the exit status instead of exiting: ``0`` on success, the exit code of
the error (:data:`hydrolog.exceptions.ERROR_CODES`) on failure -- ``2`` for an invalid
command line or option value, ``3`` for an unknown command or a missing file, ``4`` for
an output file that already exists (``conflict``), ``6`` for a missing optional extra,
``7`` for malformed input data, ``9`` for an unwritable output, ``12`` for a forbidden
path, ``13`` for an impossible calculation and ``1`` for a bug -- ``130`` after Ctrl-C
and ``143`` after ``SIGTERM``. A reader that closes the pipe early (``... | head``)
ends the command quietly with ``0``.

Output
------
Without ``--json`` the result is a short summary in the language of ``--lang``
(:mod:`hydrolog.cli.render`); with ``--json`` it is the ``hydrolog-result/1`` envelope,
the only thing on stdout (AGI-3.2). ``--schema`` prints the ``hydrolog-commands/1``
description of the command instead of running it.

On an error stdout stays empty and the **last line of stderr** is the compact
``hydrolog-error/1`` document, in English, with and without ``--json`` (AGI-3.3).
Without ``--json`` a readable explanation in the language of ``--lang`` comes before
it. Ctrl-C prints only a short text (an outcome, not an error).

Logs
----
``-v/--verbose`` and ``-q/--quiet`` set the level of the ``hydrolog`` logger to
``debug`` and ``error``; otherwise ``HYDROLOG_LOG_LEVEL`` (or ``NOGAT_LOG_LEVEL``,
``nogat.toml``) decides, ``warning`` by default. The handler writes to stderr and
lives only while :func:`main` runs (DEV-12.2).
"""

from __future__ import annotations

import contextlib
import difflib
import json
import logging
import os
import shutil
import signal
import sys
import types
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NoReturn, TextIO

from hydrolog._settings import resolve_setting
from hydrolog.catalog import catalog_document, data_commands, run_command
from hydrolog.catalog.spec import Command, Lang
from hydrolog.cli.args import MCP_WORD, Invocation, peek, resolve_lang, split_arguments
from hydrolog.cli.parser import (
    CatalogParser,
    UsageError,
    build_command_parser,
    build_group_parser,
    build_mcp_parser,
    build_root_parser,
    by_group,
    parse_command_line,
)
from hydrolog.cli.render import render_error, render_result
from hydrolog.cli.texts import env_lang, text
from hydrolog.exceptions import (
    HydrologError,
    InvalidParameterError,
    NotFoundError,
    error_document,
)

__all__ = ["main"]

EXIT_INTERRUPTED = 130
"""Exit status after Ctrl-C (128 + SIGINT)."""

_DEFAULT_WIDTH = 100
_LOGGER = "hydrolog"
"""The one logger the command line configures; the library never does (DEV-12.1)."""
_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

LOG = logging.getLogger(__name__)


class _Terminated(BaseException):
    """Raised by the ``SIGTERM`` handler; reported as the error ``terminated``."""


@dataclass
class _Reporting:
    """How a failure is reported, in which language, for what; the log setup."""

    json: bool
    lang: Lang
    command: str | None = None
    log_handler: logging.Handler | None = None
    log_level: int = logging.NOTSET


def _raise_terminated(signum: int, frame: types.FrameType | None) -> NoReturn:
    raise _Terminated


@contextlib.contextmanager
def _sigterm_as_error() -> Iterator[None]:
    """Make ``SIGTERM`` raise :class:`_Terminated`; restore the old handler after."""
    try:
        previous = signal.signal(signal.SIGTERM, _raise_terminated)
    except ValueError:  # not the main thread: the signal cannot be handled here
        yield
        return
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_DFL if previous is None else previous)


def _start_logging(reporting: _Reporting, verbose: bool, quiet: bool) -> None:
    """Send the ``hydrolog`` log to stderr at the level of the flags or settings.

    ``-v`` is ``debug`` and ``-q`` is ``error``; without them ``HYDROLOG_LOG_LEVEL``
    and the other settings decide (default ``warning``, DEV-12.2).
    """
    if verbose and quiet:
        raise UsageError(
            "The options --verbose and --quiet exclude each other",
            details={"reason": "exclusive_options", "options": ["verbose", "quiet"]},
            hint="Give only one of -v and -q.",
        )
    explicit = "debug" if verbose else "error" if quiet else None
    level = resolve_setting("log_level", explicit=explicit).value
    logger = logging.getLogger(_LOGGER)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    reporting.log_handler = handler
    reporting.log_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(_LEVELS[level])


def _stop_logging(reporting: _Reporting) -> None:
    """Remove the handler of :func:`_start_logging` and restore the logger's level."""
    handler = reporting.log_handler
    if handler is None:
        return
    logger = logging.getLogger(_LOGGER)
    logger.removeHandler(handler)
    logger.setLevel(reporting.log_level)
    reporting.log_handler = None


# --- output ---------------------------------------------------------------------------


def _encodable(value: str, stream: TextIO) -> bool:
    encoding = getattr(stream, "encoding", None)
    if not encoding:
        return True
    try:
        value.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def _json_text(document: object, stream: TextIO, indent: int | None = None) -> str:
    r"""JSON text of ``document``; escaped (``\uXXXX``) only if ``stream`` needs it."""
    rendered = json.dumps(document, ensure_ascii=False, allow_nan=False, indent=indent)
    if _encodable(rendered, stream):
        return rendered
    return json.dumps(document, ensure_ascii=True, allow_nan=False, indent=indent)


def _write(stream: TextIO, value: str) -> None:
    stream.write(value)
    stream.flush()


def _harden_stdout() -> None:
    """Print a character that stdout cannot encode as ``?`` instead of failing."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="replace")


def _print_help(parser: CatalogParser) -> int:
    _harden_stdout()
    _write(sys.stdout, parser.format_help())
    return 0


def _print_schema(document: Mapping[str, Any]) -> int:
    _write(sys.stdout, _json_text(document, sys.stdout, indent=2) + "\n")
    return 0


def _terminal_width() -> int:
    return shutil.get_terminal_size((_DEFAULT_WIDTH, 24)).columns


# --- lookup ---------------------------------------------------------------------------


def _unknown_group(word: str, commands: Sequence[Command]) -> NotFoundError:
    """Error for a first word that is no group; suggests groups and operation ids."""
    by_operation = {command.operation_id: command.name for command in commands}
    suggestions: list[str] = []
    if word in by_operation:
        suggestions.append(by_operation[word])
    else:
        groups = [*by_group(commands), MCP_WORD]
        suggestions += difflib.get_close_matches(word, groups, n=3, cutoff=0.6)
        close = difflib.get_close_matches(word, list(by_operation), n=3, cutoff=0.6)
        suggestions += [by_operation[item] for item in close]
        suggestions = list(dict.fromkeys(suggestions))[:3]
    hint = "Run 'hydrolog --help' to see the command groups."
    if suggestions:
        hint = f"Did you mean: {', '.join(suggestions)}? " + hint
    return NotFoundError(
        f"Unknown command group {word!r}",
        details={"command": word, "suggestions": suggestions},
        hint=hint,
    )


def _find_command(group: str, word: str, members: Sequence[Command]) -> Command:
    for command in members:
        if command.subcommand == word:
            return command
    name = f"{group} {word}"
    close = difflib.get_close_matches(
        name, [command.name for command in members], n=3, cutoff=0.6
    )
    hint = f"Run 'hydrolog {group} --help' to see the commands of the group."
    if close:
        hint = f"Did you mean: {', '.join(close)}? " + hint
    raise NotFoundError(
        f"Unknown command {name!r}",
        details={"command": name, "suggestions": close},
        hint=hint,
    )


def _group_schema(group: str) -> dict[str, Any]:
    """Return the ``hydrolog-commands/1`` document restricted to one group."""
    return catalog_document(
        command for command in data_commands() if command.group == group
    )


# --- execution ------------------------------------------------------------------------


def _run_command(
    command: Command, invocation: Invocation, reporting: _Reporting
) -> int:
    flags = invocation.flags
    lang = reporting.lang
    if flags.help:
        return _print_help(build_command_parser(command, lang))
    line = parse_command_line(command, invocation.rest, lang)
    reporting.json = flags.json or line.json
    if flags.schema or line.schema:
        return _print_schema(catalog_document((command,)))
    _start_logging(reporting, flags.verbose or line.verbose, flags.quiet or line.quiet)
    options = dict(line.options)
    LOG.debug("Running %s; options: %s", command.name, ", ".join(options) or "none")
    data = run_command(command, options).to_dict()
    LOG.debug("Finished %s", command.name)
    _harden_stdout()
    if reporting.json:
        _write(sys.stdout, _json_text(data, sys.stdout) + "\n")
    else:
        summary = render_result(data, command, lang, _terminal_width())
        _write(sys.stdout, summary + "\n")
    return 0


def _run_mcp(
    invocation: Invocation, reporting: _Reporting, lang_text: str | None
) -> int:
    parser = build_mcp_parser(reporting.lang)
    if invocation.flags.help:
        return _print_help(parser)
    namespace, extras = parser.parse_known_args(invocation.rest)
    if lang_text is not None:
        # The server speaks English only (AGI-9.2); an option that changes nothing
        # is refused, not ignored. It still selects the language of the help above.
        raise UsageError(
            "The option --lang has no effect on the MCP server: its output is always "
            "English",
            prog=parser.prog,
            details={"reason": "ineffective_option", "option": "--lang"},
            hint=(
                "Remove --lang; it only selects the language of 'hydrolog mcp --help'."
            ),
        )
    if extras:
        raise UsageError(
            f"Unrecognized arguments: {' '.join(extras)}", prog=parser.prog
        )
    # Imported here: the server is optional and stdout belongs to its protocol.
    from hydrolog.mcp.server import run_arguments

    run_arguments(namespace)
    return 0


def _execute(
    arguments: Sequence[str], reporting: _Reporting, lang_text: str | None
) -> int:
    invocation = split_arguments(arguments)
    flags = invocation.flags
    lang = resolve_lang(lang_text)
    reporting.lang = lang
    if flags.version:
        import hydrolog

        _write(sys.stdout, f"hydrolog {hydrolog.__version__}\n")
        return 0
    commands = data_commands()
    words = invocation.words
    if not words:
        if flags.schema:
            return _print_schema(catalog_document(commands))
        return _print_help(build_root_parser(commands, lang))
    group = words[0]
    if group == MCP_WORD:
        if not flags.help:
            _start_logging(reporting, flags.verbose, flags.quiet)
        return _run_mcp(invocation, reporting, lang_text)
    groups = by_group(commands)
    if group not in groups:
        raise _unknown_group(group, commands)
    if len(words) == 1:
        if flags.schema:
            return _print_schema(_group_schema(group))
        return _print_help(build_group_parser(group, groups[group], lang))
    command = _find_command(group, words[1], groups[group])
    reporting.command = command.name
    return _run_command(command, invocation, reporting)


# --- failures -------------------------------------------------------------------------


def _fail(exc: BaseException, reporting: _Reporting) -> int:
    """Report an error on stderr and return its exit status (AGI-3.3).

    Without ``--json`` a readable explanation in the language of ``--lang`` comes
    first; in both modes the last line is the compact ``hydrolog-error/1`` document,
    in English.
    """
    command = reporting.command
    if isinstance(exc, UsageError) and exc.command:
        command = exc.command
    LOG.debug("The command failed", exc_info=exc)
    document = error_document(exc, command, "en")
    if not reporting.json:
        localized = error_document(exc, command, reporting.lang)
        _write(sys.stderr, render_error(localized, reporting.lang) + "\n")
    _write(sys.stderr, _json_text(document, sys.stderr) + "\n")
    return int(document["exit_code"])


def _silence_stdout() -> None:
    """Point stdout at ``/dev/null`` so that the flush at exit cannot fail again."""
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
    except (OSError, ValueError):
        pass


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``hydrolog`` command line.

    While it runs, ``SIGTERM`` is turned into the ``terminated`` error and the
    ``hydrolog`` logger writes to stderr; both are put back when it returns.

    Parameters
    ----------
    argv : sequence of str, optional
        Command-line words without the program name; defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit status: ``0`` on success (also after ``--help``, ``--version`` and a closed
        output pipe), the ``exit_code`` of the error otherwise (see the module
        docstring), ``130`` after Ctrl-C.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_requested, lang_text = peek(arguments)
    try:
        lang = resolve_lang(lang_text)
    except InvalidParameterError:
        lang = env_lang()
    reporting = _Reporting(json=json_requested, lang=lang)
    with _sigterm_as_error():
        try:
            return _execute(arguments, reporting, lang_text)
        except SystemExit as exit_request:
            code = exit_request.code
            return code if isinstance(code, int) else 0
        except KeyboardInterrupt:
            _write(sys.stderr, text("interrupted", reporting.lang) + "\n")
            return EXIT_INTERRUPTED
        except _Terminated:
            return _fail(
                HydrologError(
                    "The command was terminated by the signal SIGTERM",
                    code="terminated",
                ),
                reporting,
            )
        except BrokenPipeError:
            _silence_stdout()
            return 0
        except Exception as exc:
            return _fail(exc, reporting)
        finally:
            _stop_logging(reporting)


if __name__ == "__main__":
    sys.exit(main())
