"""Serialization of the command catalog: documents and JSON Schemas of the options.

The catalog is published in three forms, all generated from the declarations in
:mod:`hydrolog.catalog.groups`:

* :func:`catalog_document` -- the ``hydrolog-commands/1`` document (Nogat
  ``commands-1``, AGI-2.4): every command with its options, result, effects, rules,
  examples, errors and Polish texts (``i18n.pl``);
* :func:`command_list` -- the ``hydrolog-command-list/1`` summary of ``commands list``
  (AGI-1.5: summary first, schema on demand);
* :func:`input_schema` -- the JSON Schema (2020-12) of the options of one command,
  the ``inputSchema`` of its MCP tool.

Documents are plain dictionaries; :class:`Document` wraps one for the library API
(``to_dict()``/``to_json()``, AGI-4.4).
"""

from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from hydrolog._serialization import to_jsonable
from hydrolog.catalog.spec import Command, Lang, Option
from hydrolog.exceptions import InvalidParameterError

__all__ = [
    "COMMANDS_SCHEMA",
    "COMMAND_LIST_SCHEMA",
    "SCHEMA_DIALECT",
    "Document",
    "catalog_document",
    "command_entry",
    "command_list",
    "input_schema",
    "paginate",
]

COMMANDS_SCHEMA: Final = "hydrolog-commands/1"
"""Value of the ``schema`` key of the catalog document."""
COMMAND_LIST_SCHEMA: Final = "hydrolog-command-list/1"
"""Value of the ``schema`` key of the command list."""
SCHEMA_DIALECT: Final = "https://json-schema.org/draft/2020-12/schema"
"""JSON Schema dialect of every ``input_schema``."""

_STANDARD_TYPES: Final[Mapping[str, str]] = {
    "number": "number",
    "integer": "integer",
    "string": "string",
    "boolean": "boolean",
    "choice": "string",
    "number_list": "array",
    "string_list": "array",
    "object_list": "array",
    "path": "string",
    "object": "object",
}
_ITEM_TYPES: Final[Mapping[str, str]] = {
    "number_list": "number",
    "string_list": "string",
    "object_list": "object",
}
_ALTERNATIVES: Final = "alternatives"
"""``one_of`` identifier of the options that are alternatives (see :func:`_option`)."""
_EXAMPLE_VALUES: Final = 3


@dataclass(frozen=True)
class Document:
    """A JSON document of the catalog with ``to_dict()`` and ``to_json()``.

    Parameters
    ----------
    data : Mapping
        The document; it is JSON-compatible and has a ``schema`` key.
    """

    data: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of the document as a dictionary."""
        copied: dict[str, Any] = json.loads(json.dumps(self.data, allow_nan=False))
        return copied

    def to_json(self, indent: int | None = None) -> str:
        """Return the document as JSON text (UTF-8 characters are not escaped)."""
        return json.dumps(self.data, ensure_ascii=False, allow_nan=False, indent=indent)


# --- pagination -----------------------------------------------------------------------


def _decode_cursor(cursor: str | None, total: int) -> int:
    if cursor is None:
        return 0
    try:
        offset = int(base64.urlsafe_b64decode(cursor.encode("ascii")).decode("ascii"))
    except (ValueError, binascii.Error, UnicodeError):
        offset = -1
    if not 0 <= offset <= total:
        raise InvalidParameterError(
            f"Option 'cursor': {cursor!r} is not a cursor of this collection",
            details={"option": "cursor", "reason": "invalid_cursor", "value": cursor},
            hint="Pass the next_cursor of the previous page unchanged.",
        )
    return offset


def paginate[T](
    items: Sequence[T], limit: int, cursor: str | None
) -> tuple[Sequence[T], dict[str, Any]]:
    """Return one page of ``items`` and its ``page`` document.

    Parameters
    ----------
    items : sequence
        The whole collection.
    limit : int
        Items per page (at least 1).
    cursor : str or None
        ``next_cursor`` of the previous page; ``None`` starts at the beginning.

    Returns
    -------
    tuple
        The page and ``{"total", "next_cursor", "truncated"}``.

    Raises
    ------
    InvalidParameterError
        If ``cursor`` was not produced by this function for this collection.
    """
    total = len(items)
    start = _decode_cursor(cursor, total)
    end = start + limit
    page: dict[str, Any] = {"total": total, "truncated": end < total}
    if end < total:
        page["next_cursor"] = base64.urlsafe_b64encode(str(end).encode()).decode()
    else:
        page["next_cursor"] = None
    return items[start:end], page


# --- options --------------------------------------------------------------------------


def _alternative_options(command: Command) -> set[str]:
    return {name for group in command.one_of for name in group}


def _example_values(command: Command, option: Option) -> list[Any]:
    values: list[Any] = []
    for example in command.examples:
        value = example.get(option.name)
        if value is None:
            continue
        converted = to_jsonable(value)
        if converted not in values:
            values.append(converted)
    return values[:_EXAMPLE_VALUES]


def _option(command: Command, option: Option, alternatives: set[str]) -> dict[str, Any]:
    """One entry of ``options`` (AGI-2.3)."""
    entry: dict[str, Any] = {
        "name": option.name,
        "type": _STANDARD_TYPES[option.type],
    }
    if option.type in _ITEM_TYPES:
        entry["items"] = _ITEM_TYPES[option.type]
    if option.unit is not None:
        entry["unit"] = option.unit
    entry["required"] = option.required
    if option.default is not None:
        entry["default"] = to_jsonable(option.normalize(option.default))
    if option.type == "choice":
        entry["enum"] = [
            {"value": value, "meaning": option.meanings.get(value, "")}
            for value in option.choices
        ]
    if option.minimum is not None:
        entry["min"] = option.minimum
    if option.maximum is not None:
        entry["max"] = option.maximum
    if option.exclusive_minimum is not None:
        entry["exclusive_minimum"] = option.exclusive_minimum
    examples = _example_values(command, option)
    if examples:
        entry["examples"] = examples
    entry["description"] = option.description
    if option.name in alternatives:
        entry["one_of"] = _ALTERNATIVES
    if option.path_role is not None:
        entry["path_role"] = option.path_role
    polish: dict[str, Any] = {"description": option.description_pl}
    if option.meanings_pl:
        polish["enum"] = dict(option.meanings_pl)
    entry["i18n"] = {"pl": polish}
    return entry


def command_entry(command: Command) -> dict[str, Any]:
    """Return the catalog entry of one command (Nogat ``commands-1`` ``command``).

    Parameters
    ----------
    command : Command
        The declaration.

    Returns
    -------
    dict
        ``name``, ``operation_id``, ``function``, ``summary``, ``description``,
        ``options``, ``result``, ``effects``, ``check``, ``families``, ``rules``,
        ``examples`` (``call`` and an ``result`` excerpt), ``errors``, ``i18n`` and,
        for alternative option groups, ``one_of`` (a Hydrolog addition: the groups,
        each a list of option names, exactly one of which must be given completely).
    """
    from hydrolog.cli.parser import format_example

    alternatives = _alternative_options(command)
    effects = command.effects
    entry: dict[str, Any] = {
        "name": command.name,
        "operation_id": command.operation_id,
        "function": command.function,
        "summary": command.summary,
        "description": command.description,
        "options": [_option(command, item, alternatives) for item in command.options],
        "result": {
            "schema": command.result_schema,
            "cardinality": command.cardinality,
        },
        "effects": {
            "read_only": effects.read_only,
            "writes": effects.writes,
            "idempotent": effects.idempotent,
            "network": effects.network,
            "destructive": effects.destructive,
        },
        "check": command.check,
        "families": list(command.families),
        "rules": list(command.rules),
        "examples": [
            {
                "call": format_example(command, example),
                "result": to_jsonable(dict(command.example_results[number])),
            }
            for number, example in enumerate(command.examples)
        ],
        "errors": list(command.errors),
        "i18n": {
            "pl": {
                "summary": command.summary_pl,
                "description": command.description_pl,
                "rules": list(command.rules_pl),
            }
        },
    }
    if command.one_of:
        entry["one_of"] = [list(group) for group in command.one_of]
    return entry


def catalog_document(commands: Iterable[Command]) -> dict[str, Any]:
    """Return the ``hydrolog-commands/1`` document of ``commands``.

    Parameters
    ----------
    commands : iterable of Command
        The commands to describe, in catalog order.

    Returns
    -------
    dict
        ``{"schema", "tool", "version", "commands"}``.
    """
    import hydrolog

    return {
        "schema": COMMANDS_SCHEMA,
        "tool": "hydrolog",
        "version": hydrolog.__version__,
        "commands": [command_entry(command) for command in commands],
    }


def command_list(commands: Iterable[Command], lang: Lang = "en") -> dict[str, Any]:
    """Return the ``hydrolog-command-list/1`` document of ``commands``.

    Parameters
    ----------
    commands : iterable of Command
        The commands to list, in catalog order.
    lang : {"pl", "en"}, optional
        Language of the summaries; machine output uses English (AGI-9.2).

    Returns
    -------
    dict
        ``{"schema", "tool", "version", "commands"}`` with, per command, ``name``,
        ``operation_id``, ``summary``, ``families`` and ``read_only``.
    """
    import hydrolog

    return {
        "schema": COMMAND_LIST_SCHEMA,
        "tool": "hydrolog",
        "version": hydrolog.__version__,
        "commands": [
            {
                "name": command.name,
                "operation_id": command.operation_id,
                "summary": command.summarize(lang),
                "families": list(command.families),
                "read_only": command.effects.read_only,
            }
            for command in commands
        ],
    }


# --- JSON Schema of the options -------------------------------------------------------


def input_schema(command: Command, lang: Lang = "en") -> dict[str, Any]:
    """Describe the options of ``command`` as a JSON Schema (2020-12) object.

    Parameters
    ----------
    command : Command
        The declaration.
    lang : {"pl", "en"}, optional
        Language of the option descriptions.

    Returns
    -------
    dict
        ``{"$schema", "type": "object", "properties", "required", "oneOf",
        "additionalProperties": false, "examples"}``; ``properties`` come from
        :meth:`hydrolog.catalog.spec.Option.json_schema`, ``oneOf`` holds one
        ``required`` group per ``one_of`` alternative.
    """
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
