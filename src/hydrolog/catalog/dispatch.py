"""Lookup, validation, catalog documents and execution of catalog commands.

The entry points are re-exported by :mod:`hydrolog.catalog`; the top-level package
exposes the five of AGI-2.1 with keyword options (:func:`hydrolog.run_command`...):

* :func:`data_commands` and :func:`get_command` -- the catalog and its lookup;
* :func:`list_commands` and :func:`command_schema` -- the command list and the
  ``hydrolog-commands/1`` document of one command;
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
from typing import Any, cast

from hydrolog.catalog.document import (
    Document,
    catalog_document,
    command_list,
    paginate,
)
from hydrolog.catalog.envelope import CommandResult
from hydrolog.catalog.groups import collect_commands
from hydrolog.catalog.spec import Command
from hydrolog.exceptions import (
    ForbiddenPathError,
    HydrologError,
    InvalidParameterError,
    NotFoundError,
)

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
            f"Command name must be a string, got {type(name_or_operation_id).__name__}",
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


# --- catalog documents ----------------------------------------------------------------


def command_schema(command: str | Command) -> Document:
    """Describe one command as a ``hydrolog-commands/1`` document (AGI-2.1).

    Parameters
    ----------
    command : str or Command
        Command name (``"tc kirpich"``) or ``operation_id``
        (``"hydrolog_tc_kirpich"``), or a :class:`Command` instance.

    Returns
    -------
    Document
        The catalog document holding that one command: options with types, units,
        bounds, enum meanings and ``path_role``, result schema, effects, rules,
        examples, errors and the Polish texts (``i18n.pl``).

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    """
    return Document(catalog_document((_resolve(command),)))


def list_commands(*, limit: int | None = None, cursor: str | None = None) -> Document:
    """List the catalog commands as a ``hydrolog-command-list/1`` document (AGI-2.1).

    Parameters
    ----------
    limit : int, optional
        Commands per page; ``None`` (default) lists all.
    cursor : str, optional
        ``page.next_cursor`` of the previous page.

    Returns
    -------
    Document
        ``commands`` with ``name``, ``operation_id``, ``summary``, ``families`` and
        ``read_only`` of each command; with ``limit`` also ``page``.

    Raises
    ------
    InvalidParameterError
        If ``limit`` is not positive or ``cursor`` is invalid.
    """
    commands = data_commands()
    if limit is None:
        return Document(command_list(commands))
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise InvalidParameterError(
            f"Option 'limit': must be an integer >= 1, got {limit!r}",
            details={"option": "limit", "reason": "minimum", "minimum": 1},
        )
    selected, page = paginate(commands, limit, cursor)
    return Document({**command_list(selected), "page": page})


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
    """Import the function at the dotted path ``"package.module.function"``."""
    module_name, _, attribute = path.rpartition(".")
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


def check_command(
    name: str | Command,
    options: Mapping[str, object] | None = None,
    *,
    allowed_dirs: Sequence[str | os.PathLike[str]] | None = None,
) -> CommandResult:
    """Plan a command without effects: :func:`run_command` with ``check`` (AGI-2.1).

    Parameters
    ----------
    name : str or Command
        Command name or ``operation_id`` (or a :class:`Command` instance).
    options : Mapping[str, object], optional
        Option values by option name; ``check`` is added.
    allowed_dirs : sequence of str or os.PathLike, optional
        As in :func:`run_command`.

    Returns
    -------
    CommandResult
        Envelope with ``check`` true whose ``result`` is the ``hydrolog-plan/1``
        document: each target file with its action (``write``, ``replace`` or
        ``conflict``). A plan that lists a conflict is a successful result.

    Raises
    ------
    NotFoundError
        If the command does not exist.
    InvalidParameterError
        If the command is read-only (it has no ``check`` mode, ``details.reason``
        ``no_check``) or the options are invalid.
    """
    command = _resolve(name)
    if command.check is None:
        raise InvalidParameterError(
            f"Command {command.name!r} has no check mode: it is read-only",
            details={"option": "check", "reason": "no_check", "command": command.name},
            hint="Run it directly; only commands that write files have a plan.",
        )
    return run_command(
        command, {**(options or {}), "check": True}, allowed_dirs=allowed_dirs
    )


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
    return CommandResult.from_output(
        command.name, resolved, output, command.result_schema
    )
