"""Operation layer: one public function per catalog command (spec section 6.3).

Every command of :mod:`hydrolog.catalog` calls exactly one function of this module
(``Command.function`` = ``"hydrolog.operations:<name>"``). The functions are the
Python surface for Retman handlers and for ``retman-scaffold`` (signature and
docstring parsing), so each one is

* public and documented (NumPy docstring, English),
* fully type-hinted, keyword-only, with ``Literal`` for choices,
* taking JSON-friendly inputs (numbers, strings, lists, paths as ``str``) whose names
  equal the catalog options,
* returning a :class:`~hydrolog._serialization.JsonResultMixin` result (or a small
  result dataclass defined here), or a
  :class:`~hydrolog.catalog.envelope.OperationOutput` when it has notices or writes
  files (return protocol: :mod:`hydrolog.catalog.envelope`).

Operations compose the existing classes and functions; they contain no new
hydrology. Series, stations and watershed parameters are loaded with
:mod:`hydrolog.catalog.inputs`.

Layout: one section per command group, in the order of
``hydrolog.catalog.groups.GROUP_MODULES``. A new group adds its section (and its
functions to ``__all__``) above the ``commands`` section, which stays last.
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


# --- group: commands ------------------------------------------------------------------


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
