"""MCP tools generated from the command catalog (spec section 7.2).

Every catalog command is one tool, in catalog order:

* ``name`` -- the ``operation_id`` (``tc_kirpich``);
* ``title`` -- ``hydrolog <name>`` (``hydrolog tc kirpich``);
* ``description`` -- the catalog description in the server language (method,
  literature, units, ranges, what the result holds), followed by a sentence on the
  alternative option groups of a command with ``one_of`` and, for a writing command,
  on its output options;
* ``inputSchema`` -- the ``input_schema`` of :func:`hydrolog.catalog.command_schema`
  (type, bounds, ``enum``, ``default``, units in the descriptions, ``required``,
  ``additionalProperties: false``, ``examples``) without ``$schema`` -- 2020-12, the
  dialect of the catalog, is the default dialect of MCP -- and without the top-level
  ``oneOf`` of the ``one_of`` groups (see below);
* annotations -- ``readOnlyHint`` unless the command writes files, ``destructiveHint``
  exactly for a writing command (its output file is replaced), idempotent, never
  open-world (Hydrolog uses no network).

The one departure from the catalog schema: clients that pass the tool schema on to a
model API (Claude Code and the Anthropic API among them) reject a tool whose input
schema has ``oneOf``, ``anyOf`` or ``allOf`` at the top level, and one such tool makes
every request of the session fail. The alternatives of ``one_of`` are therefore named
in the tool description instead; :func:`hydrolog.catalog.validate_command` still
enforces them and reports a violation with ``details.reason = "one_of"``.

An option named ``lang`` (a choice of ``pl`` and ``en``) defaults to the language of
the server, in the schema and in the call (see :mod:`hydrolog.mcp._calls`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

import mcp.types as types

from hydrolog.catalog import Command, command_schema
from hydrolog.catalog.spec import Lang

__all__ = ["LANG_OPTION", "CatalogTool", "catalog_tools"]

LANG_OPTION: Final = "lang"
"""Name of the option whose default is the language of the server."""

_DROPPED_KEYWORDS: Final = ("$schema", "oneOf")

_ONE_OF: Final[Mapping[Lang, str]] = {
    "pl": "Podaj dokładnie jedną z grup opcji: {groups}.",
    "en": "Give exactly one of these option groups: {groups}.",
}
_ONE_OPTION: Final[Mapping[Lang, str]] = {
    "pl": "Podaj dokładnie jedną z opcji: {options}.",
    "en": "Give exactly one of these options: {options}.",
}
_OR: Final[Mapping[Lang, str]] = {"pl": " albo ", "en": " or "}
_WRITES: Final[Mapping[Lang, str]] = {
    "pl": (
        "Zapisuje pliki (opcje wyjściowe: {options}); ścieżki muszą leżeć "
        "w katalogach dozwolonych serwera."
    ),
    "en": (
        "Writes files (output options: {options}); paths must lie inside the "
        "directories allowed by the server."
    ),
}
_WRITES_WHEN_GIVEN: Final[Mapping[Lang, str]] = {
    "pl": (
        "Zapisuje plik tylko wtedy, gdy podasz opcję wyjściową ({options}); ścieżka "
        "musi leżeć w katalogu dozwolonym serwera."
    ),
    "en": (
        "Writes a file only when you give the output option ({options}); the path "
        "must lie inside a directory allowed by the server."
    ),
}


@dataclass(frozen=True)
class CatalogTool:
    """MCP tool of one catalog command.

    Attributes
    ----------
    definition : mcp.types.Tool
        The tool announced by ``tools/list``.
    command : Command
        The catalog command the tool runs.
    lang_option : bool
        Whether the command has the ``lang`` option, which a call without it takes
        from the server language.
    """

    definition: types.Tool
    command: Command
    lang_option: bool


def _has_lang_option(command: Command) -> bool:
    return any(
        option.name == LANG_OPTION and option.type == "choice"
        for option in command.options
    )


def _input_schema(
    schema: Mapping[str, Any], *, lang_option: bool, lang: Lang
) -> dict[str, Any]:
    """Catalog ``input_schema`` as the tool schema (see the module docstring)."""
    result = {
        keyword: value
        for keyword, value in schema.items()
        if keyword not in _DROPPED_KEYWORDS
    }
    if lang_option:
        properties = dict(result["properties"])
        properties[LANG_OPTION] = {**properties[LANG_OPTION], "default": lang}
        result["properties"] = properties
    return result


def _alternatives(command: Command, lang: Lang) -> str:
    """The sentence that names the ``one_of`` alternatives."""
    if all(len(group) == 1 for group in command.one_of):
        names = _OR[lang].join(f"`{group[0]}`" for group in command.one_of)
        return _ONE_OPTION[lang].format(options=names)
    groups = _OR[lang].join(
        "(" + ", ".join(f"`{name}`" for name in group) + ")" for group in command.one_of
    )
    return _ONE_OF[lang].format(groups=groups)


def _description(command: Command, lang: Lang) -> str:
    """Catalog description plus the sentences the tool schema cannot carry."""
    parts = [command.describe(lang)]
    if command.one_of:
        parts.append(_alternatives(command, lang))
    if command.writes:
        outputs = [item for item in command.options if item.writes]
        names = ", ".join(f"`{item.name}`" for item in outputs)
        sentence = (
            _WRITES if all(item.required for item in outputs) else _WRITES_WHEN_GIVEN
        )
        parts.append(sentence[lang].format(options=names))
    return "\n\n".join(parts)


def _tool(command: Command, lang: Lang) -> CatalogTool:
    entry = command_schema(command, lang=lang)["commands"][0]
    lang_option = _has_lang_option(command)
    definition = types.Tool(
        name=command.operation_id,
        title=f"hydrolog {command.name}",
        description=_description(command, lang),
        input_schema=_input_schema(
            entry["input_schema"], lang_option=lang_option, lang=lang
        ),
        annotations=types.ToolAnnotations(
            read_only_hint=not command.writes,
            destructive_hint=command.writes,
            idempotent_hint=True,
            open_world_hint=False,
        ),
    )
    return CatalogTool(definition=definition, command=command, lang_option=lang_option)


def catalog_tools(commands: Sequence[Command], *, lang: Lang) -> dict[str, CatalogTool]:
    """Build the tools of the given catalog commands.

    Parameters
    ----------
    commands : sequence of Command
        Catalog commands, normally :func:`hydrolog.catalog.data_commands`.
    lang : {"pl", "en"}
        Language of the descriptions and of the ``lang`` default.

    Returns
    -------
    dict of {str : CatalogTool}
        Tools by name (``operation_id``), in the order of ``commands``.
    """
    tools: dict[str, CatalogTool] = {}
    for command in commands:
        tool = _tool(command, lang)
        tools[tool.definition.name] = tool
    return tools
