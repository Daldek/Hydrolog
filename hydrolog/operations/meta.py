"""Operations of the group ``commands``: the catalog describing itself.

``commands list`` lists the catalog commands, ``commands schema`` returns the JSON
Schema of the options of one command or of the whole catalog. The functions are
re-exported by :mod:`hydrolog.operations`; the conventions of the operation layer are
described there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog import command_schema, data_commands
from hydrolog.catalog.spec import Lang

__all__ = [
    "CommandSummary",
    "commands_schema",
    "list_commands",
]


@dataclass
class CommandSummary(JsonResultMixin):
    """Name and summary of one catalog command.

    Attributes
    ----------
    name : str
        Command name, ``"<group> <command>"``.
    operation_id : str
        MCP tool name and Python identifier of the command.
    summary : str
        One-line summary in the requested language.
    """

    name: str
    operation_id: str
    summary: str


def list_commands(*, lang: Lang = "pl") -> list[CommandSummary]:
    """List the catalog commands (``commands list``).

    Parameters
    ----------
    lang : {"pl", "en"}, optional
        Language of the summaries, by default ``"pl"``.

    Returns
    -------
    list of CommandSummary
        All commands ordered by group, then by name.
    """
    return [
        CommandSummary(
            name=command.name,
            operation_id=command.operation_id,
            summary=command.summarize(lang),
        )
        for command in data_commands()
    ]


def commands_schema(*, command: str | None = None, lang: Lang = "pl") -> dict[str, Any]:
    """Describe command options as JSON Schema (``commands schema``).

    Parameters
    ----------
    command : str, optional
        Command name (``"tc kirpich"``) or ``operation_id`` (``"tc_kirpich"``);
        ``None`` describes the whole catalog.
    lang : {"pl", "en"}, optional
        Language of the descriptions, by default ``"pl"``.

    Returns
    -------
    dict
        The ``hydrolog-commands/1`` document, see
        :func:`hydrolog.catalog.command_schema`.

    Raises
    ------
    NotFoundError
        If ``command`` does not exist.
    """
    return command_schema(command, lang=lang)
