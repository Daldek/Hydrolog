"""Entry point of the ``hydrolog`` command (``hydrolog.cli.main:main``).

The command line is generated from the catalog (:func:`hydrolog.catalog.data_commands`)::

    hydrolog <group> <command> --option VALUE ... [--json] [--schema] [--lang pl|en]
    hydrolog mcp [--allow-dir DIR]... [--lang pl|en]
    hydrolog [--version]

``main`` returns the exit status instead of exiting: ``0`` on success, the exit code of
the error (:data:`hydrolog.exceptions.ERROR_CODES`) on failure -- ``2`` for an invalid
command line or option value, ``3`` for an unknown command or a missing file, ``4`` for
an impossible calculation, ``6`` for a missing optional extra, ``7`` for malformed input
data, ``8`` for a forbidden path, ``9`` for an unwritable output and ``1`` for a bug --
and ``130`` after Ctrl-C. A reader that closes the pipe early (``... | head``) ends the
command quietly with ``0``.

Output
------
Without ``--json`` the result is a short summary in the language of ``--lang``
(:mod:`hydrolog.cli.render`); with ``--json`` it is the ``hydrolog-result/1`` envelope
on one line of stdout. ``--schema`` prints the JSON Schema of the command instead of
running it. A failure is a readable text on stderr or, with ``--json``, one
``hydrolog-error/1`` JSON line on stderr.
"""

from __future__ import annotations

import difflib
import json
import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from hydrolog.catalog import command_schema, data_commands, run_command
from hydrolog.catalog.spec import Command, Lang
from hydrolog.cli.args import MCP_WORD, Invocation, peek, resolve_lang, split_arguments
from hydrolog.cli.parser import (
    DEST_ALLOW_DIR,
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
from hydrolog.exceptions import InvalidParameterError, NotFoundError, error_document

__all__ = ["main"]

EXIT_INTERRUPTED = 130
"""Exit status after Ctrl-C (128 + SIGINT)."""

_DEFAULT_WIDTH = 100


@dataclass
class _Reporting:
    """How a failure is reported: as JSON or as text, in which language, for what."""

    json: bool
    lang: Lang
    command: str | None = None


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
    """JSON text of ``document``; escaped (``\\uXXXX``) only if ``stream`` needs it."""
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
    suggestions = [c.name for c in commands if word in (c.operation_id, c.name)]
    groups = [*by_group(commands), MCP_WORD]
    suggestions += difflib.get_close_matches(word, groups, n=3, cutoff=0.6)
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


def _group_schema(group: str, lang: Lang) -> dict[str, Any]:
    """The ``hydrolog-commands/1`` document restricted to one group."""
    document = command_schema(lang=lang)
    document["commands"] = [
        entry
        for entry in document["commands"]
        if entry["name"].split(" ", 1)[0] == group
    ]
    return document


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
        return _print_schema(command_schema(command, lang=lang))
    options = dict(line.options)
    if any(option.name == "lang" for option in command.options):
        options["lang"] = lang
    data = run_command(command, options).to_dict()
    _harden_stdout()
    if reporting.json:
        _write(sys.stdout, _json_text(data, sys.stdout) + "\n")
    else:
        summary = render_result(data, command, lang, _terminal_width())
        _write(sys.stdout, summary + "\n")
    return 0


def _allowed_directory(value: str) -> Path:
    """Resolve an ``--allow-dir`` value; it must be an existing directory."""
    path = Path(os.path.expanduser(value)).resolve()
    if not path.exists():
        raise NotFoundError(
            f"The directory {str(path)!r} of --allow-dir does not exist",
            details={"option": "allow_dir", "path": str(path)},
            hint="Give an existing directory.",
        )
    if not path.is_dir():
        raise InvalidParameterError(
            f"The path {str(path)!r} of --allow-dir is not a directory",
            details={
                "option": "allow_dir",
                "reason": "not_a_directory",
                "path": str(path),
            },
            hint="Give a directory, not a file.",
        )
    return path


def _run_mcp(invocation: Invocation, reporting: _Reporting) -> int:
    parser = build_mcp_parser(reporting.lang)
    if invocation.flags.help:
        return _print_help(parser)
    namespace, extras = parser.parse_known_args(invocation.rest)
    if extras:
        raise UsageError(
            f"Unrecognized arguments: {' '.join(extras)}", prog=parser.prog
        )
    directories = [
        _allowed_directory(item) for item in vars(namespace).get(DEST_ALLOW_DIR, [])
    ]
    # Imported here: the server is optional and stdout belongs to its protocol.
    from hydrolog.mcp import run_stdio

    run_stdio(allowed_dirs=directories, lang=reporting.lang)
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
            return _print_schema(command_schema(lang=lang))
        return _print_help(build_root_parser(commands, lang))
    group = words[0]
    if group == MCP_WORD:
        return _run_mcp(invocation, reporting)
    groups = by_group(commands)
    if group not in groups:
        raise _unknown_group(group, commands)
    if len(words) == 1:
        if flags.schema:
            return _print_schema(_group_schema(group, lang))
        return _print_help(build_group_parser(group, groups[group], lang))
    command = _find_command(group, words[1], groups[group])
    reporting.command = command.name
    return _run_command(command, invocation, reporting)


# --- failures -------------------------------------------------------------------------


def _fail(exc: BaseException, reporting: _Reporting) -> int:
    """Print the error (a JSON line or text) to stderr; return its exit status."""
    command = reporting.command
    if isinstance(exc, UsageError) and exc.command:
        command = exc.command
    document = error_document(exc, command, reporting.lang)
    if reporting.json:
        _write(sys.stderr, _json_text(document, sys.stderr) + "\n")
    else:
        _write(sys.stderr, render_error(document, reporting.lang) + "\n")
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
    try:
        return _execute(arguments, reporting, lang_text)
    except SystemExit as exit_request:
        code = exit_request.code
        return code if isinstance(code, int) else 0
    except KeyboardInterrupt:
        _write(sys.stderr, text("interrupted", reporting.lang) + "\n")
        return EXIT_INTERRUPTED
    except BrokenPipeError:
        _silence_stdout()
        return 0
    except Exception as exc:
        return _fail(exc, reporting)


if __name__ == "__main__":
    sys.exit(main())
