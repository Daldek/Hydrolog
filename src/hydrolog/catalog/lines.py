"""Command lines of the catalog: the canonical line of a call and its reading (AGI-2.1).

A *line* is a call as a person types it, an agent stores it or a report prints it::

    hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json

:func:`format_command` writes the canonical line of a call and :func:`parse_command`
reads a line back into the call, the way the ``hydrolog`` command line reads it (the
same parser, :mod:`hydrolog.cli.parser`). Every example ``call`` of the catalog
document (``hydrolog-commands/1``) is a canonical line, and for any canonical line
``format_command(*parse_command(line)) == line``.

Canonical form
--------------
* ``hydrolog``, the group and the command (``tc kirpich``);
* the options that are given, in catalog order (``None`` is "not given"), each as its
  flag and value: a number in its shortest exact form (``8.2``, ``50``, ``1e-05``), a
  list comma-separated (a list of strings that holds a comma or a blank item as JSON
  text), an object as compact JSON, a boolean as ``--flag`` or ``--no-flag``; a value
  that starts with ``-`` is joined to its flag by ``=`` (``--offset=-5``);
* then the run flags, which change how a call is shown, not what it computes, in the
  order ``--json``, ``--lang pl|en``, ``--verbose``, ``--quiet``;
* every word quoted for a POSIX shell (``shlex``): ``--name 'Kamiennik — Świerzawa'``.

``--check``, ``--force`` and ``--output`` are options of the commands that write files,
not run flags. ``--help``, ``--version`` and ``--schema`` describe a command instead of
calling it, so they are no part of a call.
"""

from __future__ import annotations

import json
import os
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any, Final, NamedTuple

from hydrolog._serialization import to_jsonable
from hydrolog.catalog.dispatch import get_command
from hydrolog.catalog.spec import LANGUAGES, Command, Option
from hydrolog.exceptions import InvalidParameterError

__all__ = [
    "PROGRAM",
    "RUN_FLAGS",
    "ParsedCommand",
    "format_command",
    "option_arguments",
    "parse_command",
]

PROGRAM: Final = "hydrolog"
"""First word of a line: the program."""
RUN_FLAGS: Final = ("json", "lang", "verbose", "quiet")
"""Names of the run flags (the keys of ``run``), in the order of a canonical line."""

_SWITCHES: Final = ("json", "verbose", "quiet")
_DESCRIBING: Final = ("-h", "--help", "-V", "--version", "--schema")
_NUMERIC: Final = ("number", "integer", "number_list")


class ParsedCommand(NamedTuple):
    """A call read from a line: what :func:`format_command` takes, in its order.

    Attributes
    ----------
    command : str
        Catalog name of the command (``"tc kirpich"``).
    options : dict
        The options the line gives, as JSON-native values (``8.2``, ``[10, 50]``,
        ``{"cn": 72}``, ``True``), not validated:
        :func:`~hydrolog.catalog.validate_command` judges them, as it judges those of
        the command line.
    run : dict
        The run flags the line gives: ``json``, ``verbose`` and ``quiet`` as ``True``,
        ``lang`` as ``"pl"`` or ``"en"``.
    """

    command: str
    options: dict[str, Any]
    run: dict[str, Any]


# --- writing --------------------------------------------------------------------------


def _number_text(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    rendered = repr(float(value))
    return rendered[:-2] if rendered.endswith(".0") else rendered


def _value_text(option: Option, value: Any) -> str:
    """Command-line text that the command line reads back as ``value``."""
    kind = option.type
    if kind in ("number", "integer"):
        return _number_text(value)
    if kind == "number_list":
        return ",".join(_number_text(item) for item in value)
    if kind == "string_list":
        items = [str(item) for item in value]
        if any("," in item or not item.strip() for item in items) or (
            items and items[0].lstrip().startswith("[")
        ):
            return json.dumps(items, ensure_ascii=False)
        return ",".join(items)
    if kind in ("object", "object_list"):
        return json.dumps(to_jsonable(value), ensure_ascii=False, separators=(",", ":"))
    return os.fspath(value) if isinstance(value, os.PathLike) else str(value)


def option_arguments(command: Command, options: Mapping[str, object]) -> list[str]:
    """Return the words that give ``command`` its ``options`` on a command line.

    The writer of :func:`format_command`, which checks the options first; this one
    writes what it is given.

    Parameters
    ----------
    command : Command
        The command.
    options : Mapping[str, object]
        Option values (JSON-native), e.g. an entry of ``Command.examples``; ``None``
        values and names that are not options of the command are skipped.

    Returns
    -------
    list of str
        Words to put after ``hydrolog <group> <command>``: ``--flag value`` pairs
        (``--flag=value`` for a value that starts with ``-``) in catalog order and
        ``--flag``/``--no-flag`` for booleans.
    """
    words: list[str] = []
    for option in command.options:
        value = options.get(option.name)
        if value is None:
            continue
        if option.type == "boolean":
            words.append(option.flag if value else "--no-" + option.flag[2:])
            continue
        rendered = _value_text(option, value)
        if rendered.startswith("-"):
            words.append(f"{option.flag}={rendered}")
        else:
            words.extend((option.flag, rendered))
    return words


def _form(option: Option, value: object) -> Any:
    """Return ``value`` if it has the type of ``option``; bounds and choices aside.

    A value outside the bounds or the choices still has a line (the run refuses it);
    a value of another type has none, because the line would mean something else.
    """
    if option.type == "choice" and isinstance(value, str) and value.strip():
        return value
    if option.type in _NUMERIC:
        option = replace(option, minimum=None, maximum=None, exclusive_minimum=None)
    return option.normalize(value)


def _given_options(command: Command, options: object) -> dict[str, Any]:
    """Return the given options of a call in catalog order, each of its type."""
    if options is None:
        return {}
    if not isinstance(options, Mapping):
        raise InvalidParameterError(
            f"Options of command {command.name!r} must be a mapping name -> value, "
            f"got {type(options).__name__}",
            details={"option": "options", "reason": "type", "expected": "object"},
        )
    known = [option.name for option in command.options]
    for key in options:
        if key not in known:
            raise InvalidParameterError(
                f"Unknown option {str(key)!r} for command {command.name!r}",
                details={
                    "option": str(key),
                    "reason": "unknown_option",
                    "allowed": known,
                },
                hint=f"Allowed options: {', '.join(known)}."
                if known
                else "This command takes no options.",
            )
    return {
        option.name: _form(option, options[option.name])
        for option in command.options
        if options.get(option.name) is not None
    }


def _run_arguments(run: object) -> list[str]:
    """Return the words of the run flags, in the order of :data:`RUN_FLAGS`."""
    if run is None:
        return []
    if not isinstance(run, Mapping):
        raise InvalidParameterError(
            f"The run flags must be a mapping name -> value, got {type(run).__name__}",
            details={"option": "run", "reason": "type", "expected": "object"},
        )
    for key in run:
        if key not in RUN_FLAGS:
            raise InvalidParameterError(
                f"Unknown run flag {str(key)!r}",
                details={
                    "option": str(key),
                    "reason": "unknown_option",
                    "allowed": list(RUN_FLAGS),
                },
                hint="The run flags are json, lang, verbose and quiet; check, force "
                "and output are options of the commands that write files.",
            )
    words: list[str] = []
    for name in RUN_FLAGS:
        value = run.get(name)
        if value is None or value is False:
            continue
        if name == "lang":
            if value not in LANGUAGES:
                raise InvalidParameterError(
                    f"Run flag 'lang': {value!r} is not one of: {', '.join(LANGUAGES)}",
                    details={
                        "option": "lang",
                        "reason": "choice",
                        "allowed": list(LANGUAGES),
                        "value": value if isinstance(value, str) else repr(value),
                    },
                )
            words += ["--lang", str(value)]
        elif value is True:
            words.append(f"--{name}")
        else:
            raise InvalidParameterError(
                f"Run flag {name!r} must be true or false, got {value!r}",
                details={"option": name, "reason": "type", "expected": "boolean"},
            )
    return words


def format_command(
    command: str | Command,
    options: Mapping[str, Any] | None = None,
    run: Mapping[str, Any] | None = None,
) -> str:
    """Write the canonical command line of a call (AGI-2.1).

    Parameters
    ----------
    command : str or Command
        Command name (``"tc kirpich"``) or ``operation_id``, or a :class:`Command`.
    options : Mapping[str, Any], optional
        Option values by option name (JSON-native, as for
        :func:`~hydrolog.catalog.run_command`); ``None`` values are "not given".
    run : Mapping[str, Any], optional
        Run flags: ``json``, ``verbose``, ``quiet`` (``True`` writes the flag,
        ``False`` or ``None`` leaves it out) and ``lang`` (``"pl"`` or ``"en"``).

    Returns
    -------
    str
        The line, e.g. ``hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023``
        (the canonical form is described in :mod:`hydrolog.catalog.lines`).

    Raises
    ------
    NotFoundError
        If the command does not exist (``details.suggestions``).
    InvalidParameterError
        If an option or a run flag is unknown (``details.reason`` ``unknown_option``)
        or a value does not have the type of its option or flag (``type``, ``empty``,
        ``not_finite``, ``choice`` of ``lang``); ``details.option`` names it. Bounds,
        the choices of an option, required options and ``one_of`` groups are not
        checked: a line is written for any call, and the run judges it.

    Examples
    --------
    >>> format_command("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
    'hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023'
    >>> format_command(
    ...     "cn lookup", {"hsg": "B", "land_cover": "forest"}, {"json": True}
    ... )
    'hydrolog cn lookup --hsg B --land-cover forest --json'
    """
    spec = command if isinstance(command, Command) else get_command(command)
    words = [
        PROGRAM,
        *spec.name.split(),
        *option_arguments(spec, _given_options(spec, options)),
        *_run_arguments(run),
    ]
    return shlex.join(words)


# --- reading --------------------------------------------------------------------------


def _words(line: str | Sequence[str]) -> list[str]:
    """Return the words of a line, without the program name."""
    from hydrolog.cli.parser import UsageError

    if isinstance(line, str):
        try:
            words = shlex.split(line)
        except ValueError as exc:
            raise UsageError(
                f"The line cannot be split into words like a shell line: {exc}",
                details={"reason": "usage"},
                hint="Close the quotes; a canonical line comes from format_command.",
            ) from exc
    elif isinstance(line, Sequence) and all(isinstance(word, str) for word in line):
        words = list(line)
    else:
        raise InvalidParameterError(
            "A line must be a string or a sequence of strings",
            details={"option": "line", "reason": "type", "expected": "string"},
        )
    return words[1:] if words[:1] == [PROGRAM] else words


def _command(words: Sequence[str]) -> Command:
    """Return the catalog command that the words of a line name."""
    from hydrolog.catalog.dispatch import data_commands
    from hydrolog.cli.args import MCP_WORD
    from hydrolog.cli.parser import UsageError

    if not words:
        raise UsageError(
            "The line names no command",
            hint="A line is: hydrolog <group> <command> [--option VALUE ...].",
        )
    if words[0] == MCP_WORD:
        raise UsageError(
            "'hydrolog mcp' starts the MCP server; it is not a command of the catalog",
            details={"command": MCP_WORD},
        )
    if len(words) == 1:
        members = [c.name for c in data_commands() if c.group == words[0]]
        if members:
            raise UsageError(
                f"The line names the group {words[0]!r} but no command of it",
                details={"command": words[0], "allowed": members},
                hint=f"The commands of the group: {', '.join(members)}.",
            )
    return get_command(" ".join(words))


def parse_command(line: str | Sequence[str]) -> ParsedCommand:
    """Read a command line into its call, as the ``hydrolog`` command line reads it.

    The general flags may stand before the group or after the command; a flag takes
    its value from the next word or after ``=``; a later value of an option wins.

    Parameters
    ----------
    line : str or sequence of str
        The line, with or without the leading ``hydrolog``: a text is split like a
        POSIX shell line (``shlex.split``), a sequence holds its words.

    Returns
    -------
    ParsedCommand
        ``(command, options, run)``: the catalog name, the options as JSON-native
        values (not validated) and the run flags; ``format_command(*parsed)`` writes
        the canonical line of the same call.

    Raises
    ------
    NotFoundError
        If the line names a group or a command that does not exist.
    InvalidParameterError
        A ``validation_error`` with ``details.reason`` ``usage`` (a
        :class:`~hydrolog.cli.parser.UsageError`) for a text that is no shell line, a
        line without a command or with a group alone (``details.allowed``), ``mcp``,
        ``--help``, ``--version`` or ``--schema`` (a description, not a call), an
        unknown flag (``unknown_option``) or a flag without its value; ``type`` for
        the text of an option that does not have the syntax of its type; ``choice``
        for a ``--lang`` other than ``pl`` and ``en``.

    Examples
    --------
    >>> parse_command("hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json")
    ParsedCommand(command='tc kirpich', options={'length_km': 8.2, 'slope_m_per_m': 0.023}, run={'json': True})
    """  # noqa: E501
    from hydrolog.cli.args import peek, resolve_lang, split_arguments
    from hydrolog.cli.parser import UsageError, parse_command_line

    words = _words(line)
    describing = next((word for word in words if word in _DESCRIBING), None)
    if describing is not None:
        raise UsageError(
            f"The line asks for {describing}, which describes a command instead of "
            "calling it",
            details={"option": describing},
            hint="Leave out --help, --version and --schema.",
        )
    invocation = split_arguments(words)
    command = _command(invocation.words)
    parsed = parse_command_line(command, invocation.rest, "en")
    run: dict[str, Any] = {}
    flags = invocation.flags
    if flags.json or parsed.json:
        run["json"] = True
    _, lang = peek(words)
    if lang is not None:
        run["lang"] = resolve_lang(lang)
    if flags.verbose or parsed.verbose:
        run["verbose"] = True
    if flags.quiet or parsed.quiet:
        run["quiet"] = True
    return ParsedCommand(command.name, dict(parsed.options), run)
