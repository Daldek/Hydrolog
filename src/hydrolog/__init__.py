"""Hydrolog: hydrological calculations as a Python library, a CLI and an MCP server.

The public API is exactly :data:`__all__` (AGI-7.1): the error classes, the error
registry and the five functions that drive any command of the catalog
(AGI-2.1) -- :func:`list_commands`, :func:`command_schema`, :func:`validate_command`,
:func:`check_command` and :func:`run_command`. The calculation classes live in the
subpackages (``hydrolog.runoff``, ``hydrolog.time``, ``hydrolog.precipitation``...)
and the operation of each command in :mod:`hydrolog.operations`.

Importing the package reads no files, uses no network and imports no numerical
library: the five functions import the catalog when they are first called.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hydrolog.exceptions import (
    ERROR_CODES,
    CalculationError,
    ConflictError,
    ForbiddenPathError,
    HydrologError,
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
)

if TYPE_CHECKING:
    from hydrolog.catalog import CommandResult, Document

__version__ = "1.0.0.dev0"
__author__ = "Piotr de Bever"

__all__ = [
    "ERROR_CODES",
    "CalculationError",
    "ConflictError",
    "ForbiddenPathError",
    "HydrologError",
    "InputDataError",
    "InvalidParameterError",
    "MissingDependencyError",
    "NotFoundError",
    "OutputError",
    "__version__",
    "check_command",
    "command_schema",
    "list_commands",
    "run_command",
    "validate_command",
]


def list_commands(*, limit: int | None = None, cursor: str | None = None) -> Document:
    """List the commands of the catalog.

    Parameters
    ----------
    limit : int, optional
        Commands per page; ``None`` lists all of them.
    cursor : str, optional
        ``page.next_cursor`` of the previous page.

    Returns
    -------
    Document
        The ``hydrolog-command-list/1`` document (``to_dict()``, ``to_json()``).

    Raises
    ------
    InvalidParameterError
        If ``limit`` or ``cursor`` is invalid.

    Examples
    --------
    >>> import hydrolog
    >>> hydrolog.list_commands().to_dict()["schema"]
    'hydrolog-command-list/1'
    """
    from hydrolog.catalog import list_commands as _list_commands

    return _list_commands(limit=limit, cursor=cursor)


def command_schema(command: str, /) -> Document:
    """Describe one command: options, result, effects, rules, examples and errors.

    Parameters
    ----------
    command : str
        Command name (``"tc kirpich"``) or ``operation_id`` (``"hydrolog_tc_kirpich"``).

    Returns
    -------
    Document
        The ``hydrolog-commands/1`` document holding that command.

    Raises
    ------
    NotFoundError
        If the command does not exist; ``details.suggestions`` lists similar names.

    Examples
    --------
    >>> import hydrolog
    >>> hydrolog.command_schema("tc kirpich").to_dict()["commands"][0]["name"]
    'tc kirpich'
    """
    from hydrolog.catalog import command_schema as _command_schema

    return _command_schema(command)


def validate_command(command: str, /, **options: Any) -> dict[str, Any]:
    """Validate the options of a command and fill in the defaults, without effects.

    Parameters
    ----------
    command : str
        Command name or ``operation_id``.
    **options
        The options of the command, named as in its catalog entry.

    Returns
    -------
    dict
        The normalized options with the defaults applied.

    Raises
    ------
    NotFoundError
        If the command does not exist.
    InvalidParameterError
        If an option is unknown, missing, of the wrong type or out of range
        (``details.option`` and ``details.reason`` say which).

    Examples
    --------
    >>> import hydrolog
    >>> hydrolog.validate_command("cn lookup", hsg="B", land_cover="forest")["hsg"]
    'B'
    """
    from hydrolog.catalog import validate_command as _validate_command

    return _validate_command(command, options)


def check_command(command: str, /, **options: Any) -> CommandResult:
    """Plan a writing command without effects (the plan of ``--check``).

    Parameters
    ----------
    command : str
        Command name or ``operation_id`` of a command that writes a file.
    **options
        The options of the command.

    Returns
    -------
    CommandResult
        The result envelope with ``check`` true; ``result`` lists each target file
        with its action (``write``, ``replace`` or ``conflict``).

    Raises
    ------
    InvalidParameterError
        If the command is read-only (it has no plan) or the options are invalid.
    """
    from hydrolog.catalog import check_command as _check_command

    return _check_command(command, options)


def run_command(command: str, /, **options: Any) -> CommandResult:
    """Run a command of the catalog and return its result envelope.

    Parameters
    ----------
    command : str
        Command name or ``operation_id``.
    **options
        The options of the command, named as in its catalog entry.

    Returns
    -------
    CommandResult
        The ``hydrolog-result/1`` envelope (``to_dict()``, ``to_json()``).

    Raises
    ------
    HydrologError
        The error of the command, with ``code``, ``details`` and ``hint``.

    Examples
    --------
    >>> import hydrolog
    >>> envelope = hydrolog.run_command("cn lookup", hsg="B", land_cover="forest")
    >>> envelope.to_dict()["status"]
    'ok'
    """
    from hydrolog.catalog import run_command as _run_command

    return _run_command(command, options)
