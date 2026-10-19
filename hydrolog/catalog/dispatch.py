"""Lookup, validation, JSON Schema and execution of catalog commands (spec 6.2).

The public entry points are re-exported by :mod:`hydrolog.catalog`:

* :func:`data_commands` and :func:`get_command` -- the catalog and its lookup;
* :func:`command_schema` -- the ``hydrolog-commands/1`` document (JSON Schema of the
  options of every command);
* :func:`validate_command` -- validation and normalization of option values;
* :func:`run_command` -- validation, path policy, execution and the result envelope.

Validation errors
-----------------
All validation failures are :class:`~hydrolog.exceptions.InvalidParameterError`
(``validation_error``) whose ``details`` hold ``option`` and a machine-readable
``reason``:

=====================  ============================================================
reason                 meaning (extra ``details`` keys)
=====================  ============================================================
``unknown_option``     option not declared by the command (``allowed``)
``required``           required option missing
``one_of``             no or several complete ``one_of`` groups (``groups``,
                       ``given``, ``missing``)
``type``               wrong JSON type (``expected``, ``value``, ``got``; ``index``
                       inside lists)
``not_finite``         NaN or infinity where a finite number is required
``minimum``,           bound violated (``minimum``/``maximum``/``exclusive_minimum``,
``maximum``,           ``value``)
``exclusive_minimum``
``choice``             value not among the choices (``allowed``, ``value``)
``empty``              empty string, path or list
``invalid_path``       path that cannot be used (NUL character, unresolvable)
=====================  ============================================================

A command that does not exist is a :class:`~hydrolog.exceptions.NotFoundError`; a path
outside ``allowed_dirs`` is a :class:`~hydrolog.exceptions.ForbiddenPathError`.
"""

from __future__ import annotations

import difflib
import importlib
import itertools
import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, cast

from hydrolog._serialization import to_jsonable
from hydrolog.catalog.envelope import CommandResult
from hydrolog.catalog.groups import collect_commands
from hydrolog.catalog.spec import LANGUAGES, Command, Lang
from hydrolog.exceptions import (
    ForbiddenPathError,
    HydrologError,
    InvalidParameterError,
    NotFoundError,
)

COMMANDS_SCHEMA: Final = "hydrolog-commands/1"
"""Value of the ``schema`` key of the :func:`command_schema` document."""
SCHEMA_DIALECT: Final = "https://json-schema.org/draft/2020-12/schema"
"""JSON Schema dialect of every ``input_schema``."""


# --- catalog --------------------------------------------------------------------------


def data_commands() -> tuple[Command, ...]:
    """Return the catalog.

    Returns
    -------
    tuple of Command
        All commands, ordered by group (the order of
        :data:`hydrolog.catalog.groups.GROUP_MODULES`), then by name.
    """
    return collect_commands()


def get_command(name_or_operation_id: str) -> Command:
    """Find a command by name or by ``operation_id``.

    Parameters
    ----------
    name_or_operation_id : str
        ``"tc kirpich"`` or ``"tc_kirpich"``; surrounding and repeated whitespace is
        ignored.

    Returns
    -------
    Command
        The declaration.

    Raises
    ------
    NotFoundError
        If no command has this name; ``details.suggestions`` lists similar names.
    InvalidParameterError
        If the argument is not a string.
    """
    if not isinstance(name_or_operation_id, str):
        raise InvalidParameterError(
            "Command name must be a string, "
            f"got {type(name_or_operation_id).__name__}",
            details={"option": "command", "reason": "type", "expected": "string"},
        )
    key = " ".join(name_or_operation_id.split())
    commands = data_commands()
    for command in commands:
        if key in (command.name, command.operation_id):
            return command
    candidates = {
        label: command.name
        for command in commands
        for label in (command.name, command.operation_id)
    }
    close = difflib.get_close_matches(key, list(candidates), n=5, cutoff=0.6)
    suggestions = list(dict.fromkeys(candidates[label] for label in close))[:3]
    hint = "Run 'commands list' to see all commands."
    if suggestions:
        hint = f"Did you mean: {', '.join(suggestions)}? " + hint
    raise NotFoundError(
        f"Unknown command {name_or_operation_id!r}",
        details={"command": name_or_operation_id, "suggestions": suggestions},
        hint=hint,
    )


def _resolve(command: str | Command) -> Command:
    return command if isinstance(command, Command) else get_command(command)


# --- validation -----------------------------------------------------------------------


def _check_one_of(command: Command, given: set[str]) -> None:
    if not command.one_of:
        return
    complete = [group for group in command.one_of if given.issuperset(group)]
    if len(complete) == 1:
        return
    groups = [list(group) for group in command.one_of]
    pretty = " or ".join("+".join(group) for group in command.one_of)
    details: dict[str, Any] = {
        "reason": "one_of",
        "groups": groups,
        "given": [
            name
            for name in dict.fromkeys(itertools.chain.from_iterable(command.one_of))
            if name in given
        ],
    }
    if complete:
        raise InvalidParameterError(
            f"Command {command.name!r} takes exactly one group of options "
            f"({pretty}), but several are given",
            details={"option": complete[1][0], **details},
            hint=f"Give only one of: {pretty}.",
        )
    closest = max(command.one_of, key=lambda group: len(given.intersection(group)))
    missing = [name for name in closest if name not in given]
    message = (
        f"Command {command.name!r} needs exactly one complete group of options: "
        f"{pretty}"
    )
    if given.intersection(closest):
        message += f"; missing for the closest group: {', '.join(missing)}"
    details["missing"] = missing
    raise InvalidParameterError(
        message,
        details={"option": missing[0], **details},
        hint=f"Give one complete group: {pretty}.",
    )


def validate_command(
    name: str | Command, options: Mapping[str, object] | None = None
) -> dict[str, Any]:
    """Validate option values against the declaration of a command.

    Values must be JSON-native (numbers, strings, booleans, lists, objects); text
    such as ``"12.5"`` is not converted to a number -- the CLI does that before
    calling. ``None`` counts as "not given". Defaults are applied for the options
    that are not given; paths are kept as given (``run_command`` resolves them).

    Parameters
    ----------
    name : str or Command
        Command name or ``operation_id`` (or a :class:`Command` instance).
    options : Mapping[str, object], optional
        Option values by option name.

    Returns
    -------
    dict
        Normalized options in catalog order, including defaults.

    Raises
    ------
    NotFoundError
        If the command does not exist.
    InvalidParameterError
        If ``options`` is not a mapping, an option is unknown, required but
        missing, of the wrong type or outside its bounds/choices, or the ``one_of``
        groups are not satisfied; see the module docstring for ``details``.
    """
    command = _resolve(name)
    given_options: Mapping[str, object] = {} if options is None else options
    if not isinstance(given_options, Mapping):
        raise InvalidParameterError(
            f"Options of command {command.name!r} must be a mapping name -> value, "
            f"got {type(given_options).__name__}",
            details={"option": "options", "reason": "type", "expected": "object"},
        )
    known = [option.name for option in command.options]
    for key in given_options:
        if key not in known:
            close = difflib.get_close_matches(str(key), known, n=1, cutoff=0.6)
            hint = f"Allowed options: {', '.join(known)}." if known else None
            if close:
                hint = f"Did you mean {close[0]!r}? " + (hint or "")
            raise InvalidParameterError(
                f"Unknown option {str(key)!r} for command {command.name!r}",
                details={
                    "option": str(key),
                    "reason": "unknown_option",
                    "allowed": known,
                },
                hint=hint or "This command takes no options.",
            )
    normalized: dict[str, Any] = {}
    given: set[str] = set()
    for option in command.options:
        raw = given_options.get(option.name)
        if raw is None:
            continue
        normalized[option.name] = option.normalize(raw)
        given.add(option.name)
    for option in command.options:
        if option.required and option.name not in given:
            raise InvalidParameterError(
                f"Option {option.name!r} is required by command {command.name!r}",
                details={"option": option.name, "reason": "required"},
                hint=(
                    f"Give '{option.name}' (CLI: {option.flag}); "
                    "'commands schema' lists all options."
                ),
            )
    _check_one_of(command, given)
    result: dict[str, Any] = {}
    for option in command.options:
        if option.name in normalized:
            result[option.name] = normalized[option.name]
        elif option.default is not None:
            result[option.name] = option.normalize(option.default)
    return result


# --- JSON Schema ----------------------------------------------------------------------


def _input_schema(command: Command, lang: Lang) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "$schema": SCHEMA_DIALECT,
        "type": "object",
        "properties": {
            option.name: option.json_schema(lang) for option in command.options
        },
    }
    required = [option.name for option in command.options if option.required]
    if required:
        schema["required"] = required
    if command.one_of:
        schema["oneOf"] = [{"required": list(group)} for group in command.one_of]
    schema["additionalProperties"] = False
    if command.examples:
        schema["examples"] = [to_jsonable(dict(item)) for item in command.examples]
    return schema


def _command_entry(command: Command, lang: Lang) -> dict[str, Any]:
    return {
        "name": command.name,
        "operation_id": command.operation_id,
        "summary": command.summarize(lang),
        "description": command.describe(lang),
        "input_schema": _input_schema(command, lang),
        "x-hydrolog": {
            "writes": command.writes,
            "function": command.function,
            "units": {
                option.name: option.unit for option in command.options if option.unit
            },
        },
    }


def command_schema(
    command: str | Command | None = None, *, lang: Lang = "pl"
) -> dict[str, Any]:
    """Describe the options of one command, or of the whole catalog, as JSON Schema.

    Parameters
    ----------
    command : str or Command, optional
        Command name or ``operation_id``; ``None`` describes every command.
    lang : {"pl", "en"}, optional
        Language of the summaries, descriptions and option descriptions.

    Returns
    -------
    dict
        ``{"schema": "hydrolog-commands/1", "version", "lang", "commands": [...]}``;
        each command is ``{"name", "operation_id", "summary", "description",
        "input_schema", "x-hydrolog"}``. ``input_schema`` is a JSON Schema
        (2020-12) object with ``properties`` (type, bounds, ``enum``, ``default``,
        ``description`` with the unit), ``required``, ``oneOf`` (one ``required``
        group per ``one_of`` alternative), ``additionalProperties: false`` and the
        declared ``examples``. ``x-hydrolog`` holds ``writes``, ``function`` and
        ``units`` (unit of each option that has one).

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    InvalidParameterError
        If ``lang`` is not ``"pl"`` or ``"en"``.
    """
    if lang not in LANGUAGES:
        raise InvalidParameterError(
            f"Unknown language {lang!r}; allowed: {', '.join(LANGUAGES)}",
            details={
                "option": "lang",
                "reason": "choice",
                "allowed": list(LANGUAGES),
                "value": str(lang),
            },
        )
    import hydrolog

    selected = data_commands() if command is None else (_resolve(command),)
    return {
        "schema": COMMANDS_SCHEMA,
        "version": hydrolog.__version__,
        "lang": lang,
        "commands": [_command_entry(item, lang) for item in selected],
    }


# --- execution ------------------------------------------------------------------------


def _resolve_path(text: str, option: str) -> Path:
    """Absolute path: ``~`` expanded, CWD-relative, symlinks resolved."""
    path = Path(os.path.expanduser(text))
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        return path.resolve()
    except (OSError, RuntimeError) as exc:
        raise InvalidParameterError(
            f"Option {option!r}: cannot resolve the path {text!r}: {exc}",
            details={"option": option, "reason": "invalid_path", "value": text},
        ) from exc


def _apply_path_policy(
    command: Command,
    options: dict[str, Any],
    allowed_dirs: Sequence[str | os.PathLike[str]] | None,
) -> dict[str, Any]:
    """Resolve every ``path`` option and check it against ``allowed_dirs``."""
    roots: tuple[Path, ...] | None = None
    if allowed_dirs is not None:
        if isinstance(allowed_dirs, str | os.PathLike):
            allowed_dirs = [allowed_dirs]
        roots = tuple(
            _resolve_path(os.fspath(item), "allowed_dirs") for item in allowed_dirs
        )
    resolved = dict(options)
    for option in command.options:
        if option.type != "path" or option.name not in resolved:
            continue
        path = _resolve_path(resolved[option.name], option.name)
        if roots is not None and not any(path.is_relative_to(root) for root in roots):
            hint = (
                "Use a path inside an allowed directory."
                if roots
                else "No directory is allowed for file access "
                "(MCP: start the server with --allow-dir DIR)."
            )
            raise ForbiddenPathError(
                f"Path {str(path)!r} of option {option.name!r} is outside the allowed "
                "directories",
                details={
                    "option": option.name,
                    "path": str(path),
                    "allowed_dirs": [str(root) for root in roots],
                },
                hint=hint,
            )
        resolved[option.name] = str(path)
    return resolved


def _load_function(path: str) -> Callable[..., Any]:
    """Import ``"package.module:attribute"``."""
    module_name, _, attribute = path.partition(":")
    try:
        function = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as exc:
        raise HydrologError(
            f"Operation {path!r} cannot be imported: {exc}",
            details={"function": path},
        ) from exc
    if not callable(function):
        raise HydrologError(
            f"Operation {path!r} is not callable", details={"function": path}
        )
    return cast(Callable[..., Any], function)


def run_command(
    name: str | Command,
    options: Mapping[str, object] | None = None,
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] | None = None,
) -> CommandResult:
    """Validate and run a catalog command.

    The steps are: validate and normalize the options (:func:`validate_command`);
    resolve every ``path`` option to an absolute path (``~`` expanded, relative paths
    against the working directory, symlinks resolved) and, when ``allowed_dirs`` is
    given, require it to lie inside one of the directories; import the operation
    lazily from ``Command.function`` and call it with the normalized options as
    keyword arguments; wrap its return value in a
    :class:`~hydrolog.catalog.envelope.CommandResult` (see
    :mod:`hydrolog.catalog.envelope` for the return protocol: notices and written
    files with SHA-256).

    Parameters
    ----------
    name : str or Command
        Command name or ``operation_id`` (or a :class:`Command` instance, e.g. a
        private declaration in a test).
    options : Mapping[str, object], optional
        Option values by option name (JSON-native).
    allowed_dirs : sequence of str or os.PathLike, optional
        Directories that all path options must stay inside. ``None`` (default) applies
        no restriction; an empty sequence forbids every path (pure-input commands
        still run).

    Returns
    -------
    CommandResult
        Envelope with the normalized ``inputs`` (paths absolute), the operation
        ``result``, written ``files`` and ``notices``.

    Raises
    ------
    NotFoundError
        If the command does not exist.
    InvalidParameterError
        If the options are invalid (see :func:`validate_command`).
    ForbiddenPathError
        If a path option lies outside ``allowed_dirs``.
    HydrologError
        Any error of the operation itself is propagated unchanged; an operation
        that cannot be imported is an ``internal_error``.
    """
    command = _resolve(name)
    normalized = validate_command(command, options)
    resolved = _apply_path_policy(command, normalized, allowed_dirs)
    function = _load_function(command.function)
    output = function(**resolved)
    return CommandResult.from_output(command.name, resolved, output)
