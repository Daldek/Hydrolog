"""MCP tools generated from the command catalog (AGI-5.2 to AGI-5.5, AGI-5.8, AGI-5.12).

Every catalog command is one tool, in catalog order (deterministic):

* ``name`` -- the ``operation_id`` (``hydrolog_tc_kirpich``), at most 48 characters;
* ``description`` -- the catalog ``summary``, ``description`` and ``rules``, English,
  at most 600 characters together (the catalog enforces it); nothing is appended;
* ``inputSchema`` -- :func:`hydrolog.catalog.input_schema` in English (2020-12,
  ``additionalProperties: false``, a ``description`` on every property) without the
  top-level ``oneOf`` of the ``one_of`` groups, which clients that pass the schema on
  to a model API reject. The alternatives are named in the ``description`` of each
  option that belongs to one, and
  :func:`hydrolog.catalog.validate_command` still enforces them
  (``details.reason = "one_of"``);
* ``outputSchema`` -- the ``hydrolog-result/1`` envelope (:mod:`hydrolog.mcp._output`);
* annotations ``title``, ``readOnlyHint``, ``destructiveHint``, ``idempotentHint`` and
  ``openWorldHint``, derived from ``Command.effects`` and the mode of the server.

Modes
-----
A writing command (``Command.check`` is not ``None``) runs on a server started with
``--allow-writes`` as the catalog declares it. Without it the server turns every call
into a plan (``check`` true, ``force`` ignored, see :mod:`hydrolog.mcp._calls`), so the
tool is read-only: ``readOnlyHint`` true, ``destructiveHint`` false, and the
descriptions of its ``check``, ``force`` and output options say so.

The selection of commands by family (``--tools``) is :mod:`hydrolog.mcp._families`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

import mcp.types as types

from hydrolog.catalog import Command, input_schema
from hydrolog.mcp._output import OUTPUT_SCHEMA

__all__ = [
    "ALWAYS_LOAD_COMMANDS",
    "ALWAYS_LOAD_KEY",
    "CatalogTool",
    "catalog_tools",
]

ALWAYS_LOAD_KEY: Final = "anthropic/alwaysLoad"
"""Key of ``_meta`` that tells Claude Code to load a tool's definition up front."""
ALWAYS_LOAD_COMMANDS: Final = ("commands list", "commands schema")
"""The discovery commands (AGI-5.9): the only tools marked :data:`ALWAYS_LOAD_KEY`."""

_DROPPED_KEYWORDS: Final = ("oneOf",)


@dataclass(frozen=True)
class CatalogTool:
    """MCP tool of one catalog command.

    Attributes
    ----------
    definition : mcp.types.Tool
        The tool announced by ``tools/list``.
    command : Command
        The catalog command the tool runs.
    plan_only : bool
        The command writes files but the server is read-only: every call is a plan.
    """

    definition: types.Tool
    command: Command
    plan_only: bool


# --- tool definitions -----------------------------------------------------------------


def _alternatives(command: Command) -> dict[str, str]:
    """Return the suffix of the ``description`` of each option of a ``one_of`` group."""
    groups = " or ".join(
        " + ".join(f"`{name}`" for name in group) for group in command.one_of
    )
    suffix = f" Give exactly one of these alternatives: {groups}."
    return {name: suffix for group in command.one_of for name in group}


def _write_notes(command: Command, *, plan_only: bool) -> dict[str, str]:
    """Return the suffixes of the ``description`` of the options that concern writes."""
    notes: dict[str, str] = {}
    for option in command.options:
        if option.writes:
            notes[option.name] = (
                " The server is read-only (started without `--allow-writes`): "
                "nothing is written, the call only plans."
                if plan_only
                else " The server writes only inside its allowed directories."
            )
    if plan_only:
        notes["check"] = " Always true on this read-only server."
        notes["force"] = " Ignored on this read-only server."
    return notes


def _input_schema(command: Command, *, plan_only: bool) -> dict[str, Any]:
    """Return the catalog ``input_schema`` as the tool schema (module docstring)."""
    schema = {
        keyword: value
        for keyword, value in input_schema(command, "en").items()
        if keyword not in _DROPPED_KEYWORDS
    }
    notes = _write_notes(command, plan_only=plan_only)
    if command.one_of:
        for name, suffix in _alternatives(command).items():
            notes[name] = notes.get(name, "") + suffix
    properties: dict[str, Any] = {}
    for name, definition in schema["properties"].items():
        entry = dict(definition)
        if name in notes:
            entry["description"] = entry["description"] + notes[name]
        if plan_only and name == "check":
            entry["default"] = True
        properties[name] = entry
    schema["properties"] = properties
    return schema


def _description(command: Command) -> str:
    """Return ``summary``, ``description`` and ``rules`` of the command as one text."""
    parts = [command.summary, command.description]
    if command.rules:
        parts.append(" ".join(command.rules))
    return "\n\n".join(parts)


def _tool(command: Command, *, allow_writes: bool) -> CatalogTool:
    """Build the tool of one command for a server in the given mode."""
    effects = command.effects
    plan_only = command.check is not None and not allow_writes
    read_only = effects.read_only or plan_only
    definition = types.Tool(
        name=command.operation_id,
        title=command.summary,
        description=_description(command),
        input_schema=_input_schema(command, plan_only=plan_only),
        output_schema=OUTPUT_SCHEMA,
        annotations=types.ToolAnnotations(
            title=command.summary,
            read_only_hint=read_only,
            destructive_hint=effects.destructive and not read_only,
            idempotent_hint=effects.idempotent,
            open_world_hint=effects.network,
        ),
        _meta=(
            {ALWAYS_LOAD_KEY: True} if command.name in ALWAYS_LOAD_COMMANDS else None
        ),
    )
    return CatalogTool(definition=definition, command=command, plan_only=plan_only)


def catalog_tools(
    commands: Sequence[Command], *, allow_writes: bool
) -> dict[str, CatalogTool]:
    """Build the tools of the given catalog commands.

    Parameters
    ----------
    commands : sequence of Command
        Catalog commands, normally the result of :func:`select_commands`.
    allow_writes : bool
        Whether the server writes files (``--allow-writes``); without it a writing
        command is a plan-only, read-only tool.

    Returns
    -------
    dict of {str : CatalogTool}
        Tools by name (``operation_id``), in the order of ``commands``.
    """
    tools: dict[str, CatalogTool] = {}
    for command in commands:
        tool = _tool(command, allow_writes=allow_writes)
        tools[tool.definition.name] = tool
    return tools
