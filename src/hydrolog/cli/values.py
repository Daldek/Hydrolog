"""Conversion of command-line text into JSON-native option values.

The command line delivers text, whereas the catalog validates JSON-native values
(:mod:`hydrolog.catalog.spec`). :func:`parse_option_value` bridges the two by *syntax
only*: ranges, choices and emptiness stay with
:func:`~hydrolog.catalog.validate_command`, so the CLI, the MCP server and Python
callers get the same validation errors for the same values.

====================  ==========================================================
option type           accepted text
====================  ==========================================================
``number``            decimal number with a dot: ``8.2``, ``-1e-3`` (``nan`` and
                      ``inf`` parse and are then refused by the catalog)
``integer``           whole number ``5`` (``1e3`` and ``5.0`` parse and are
                      accepted or refused by the catalog like in JSON)
``string``            the text as given
``choice``            the text as given
``path``              the text as given (the catalog resolves it)
``boolean``           no text: ``--flag`` is ``true``, ``--no-flag`` is ``false``
``number_list``       ``1.5,2,3`` (spaces around items allowed) or a JSON array
``string_list``       ``a,b,c`` (spaces around items allowed) or a JSON array
``object``            JSON text: ``'{"area_km2": 45.3}'``
``object_list``       JSON array of objects
====================  ==========================================================

A list whose text starts with ``[`` is read as JSON; this is the way to give a
``string_list`` item that contains a comma.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final

from hydrolog.catalog.spec import Option
from hydrolog.exceptions import InvalidParameterError

__all__ = ["parse_option_value"]

_NUMBER: Final = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_INTEGER: Final = re.compile(r"[+-]?\d+")
_NON_FINITE: Final = re.compile(r"[+-]?(?:nan|inf|infinity)", re.IGNORECASE)
_SHOWN_MAX_CHARS: Final = 200

_EXPECTED: Final = {
    "number": "number",
    "integer": "integer",
    "number_list": "array of numbers",
    "string_list": "array of strings",
    "object": "object",
    "object_list": "array of objects",
}
_ITEM_EXPECTED: Final = {"number_list": "number", "string_list": "string"}
_HINTS: Final = {
    "number": "Give a decimal number with a dot, e.g. 8.2 or -1e-3.",
    "integer": "Give a whole number, e.g. 5.",
    "number_list": "Give comma-separated numbers, e.g. 1.5,2,3 (or a JSON array).",
    "string_list": "Give comma-separated items, e.g. a,b,c (or a JSON array).",
    "object": "Give a JSON object, e.g. '{\"area_km2\": 45.3}'.",
    "object_list": 'Give a JSON array of objects, e.g. \'[{"name": "A"}]\'.',
}


def _shown(text: str) -> str:
    """Bounded rendering of an offending text for messages and ``details``."""
    if len(text) <= _SHOWN_MAX_CHARS:
        return text
    return text[: _SHOWN_MAX_CHARS - 1] + "…"


def _fail(
    option: Option,
    expected: str,
    text: str,
    *,
    index: int | None = None,
    problem: str | None = None,
) -> InvalidParameterError:
    """Build the ``validation_error`` of a text that does not have the right syntax."""
    label = option.name if index is None else f"{option.name}[{index}]"
    message = f"Option {label!r}: expected {expected}, got {_shown(text)!r}"
    if problem:
        message += f" ({problem})"
    details: dict[str, object] = {
        "option": option.name,
        "reason": "type",
        "expected": expected,
        "value": _shown(text),
    }
    if index is not None:
        details["index"] = index
    return InvalidParameterError(
        message, details=details, hint=_HINTS.get(option.type, None)
    )


def _number(option: Option, text: str, index: int | None = None) -> float:
    token = text.strip()
    if _NUMBER.fullmatch(token) or _NON_FINITE.fullmatch(token):
        return float(token)
    raise _fail(option, _ITEM_EXPECTED.get(option.type, "number"), text, index=index)


def _integer(option: Option, text: str) -> int | float:
    token = text.strip()
    if _INTEGER.fullmatch(token):
        return int(token)
    if _NUMBER.fullmatch(token) or _NON_FINITE.fullmatch(token):
        return float(token)
    raise _fail(option, "integer", text)


def _json(option: Option, text: str) -> Any:
    """Parse JSON text; a syntax error is a ``validation_error`` of the option."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise _fail(
            option,
            _EXPECTED[option.type],
            text,
            problem=f"invalid JSON: {exc.msg}, column {exc.colno}",
        ) from exc


def _items(text: str) -> list[str]:
    return [item.strip() for item in text.split(",")]


def _number_list(option: Option, text: str) -> Any:
    if text.lstrip().startswith("["):
        return _json(option, text)
    return [_number(option, item, index) for index, item in enumerate(_items(text))]


def _string_list(option: Option, text: str) -> Any:
    if text.lstrip().startswith("["):
        return _json(option, text)
    items = _items(text)
    for index, item in enumerate(items):
        if not item:
            raise _fail(option, "string", item, index=index, problem="empty item")
    return items


def parse_option_value(option: Option, raw: str | bool) -> Any:
    """Convert the command-line text of one option into a JSON-native value.

    Parameters
    ----------
    option : Option
        Declaration of the option; its ``type`` selects the syntax.
    raw : str or bool
        Text given on the command line. Boolean options arrive as ``bool`` (the
        flags ``--name`` and ``--no-name`` carry no text) and are returned unchanged.

    Returns
    -------
    object
        ``float``/``int`` for numbers, ``str`` for strings, choices and paths,
        ``bool`` for booleans, ``list`` for lists and ``object`` values as parsed
        from JSON. Values are *not* checked against bounds or choices; use
        :func:`~hydrolog.catalog.validate_command` for that.

    Raises
    ------
    InvalidParameterError
        If the text does not have the syntax of the option type. ``details`` hold
        ``option``, ``reason="type"``, ``expected``, the (bounded) ``value`` and,
        for list items, the ``index`` -- the shape of the catalog's own type errors.

    Examples
    --------
    >>> from hydrolog.catalog import get_command
    >>> option = get_command("tc kirpich").option("length_km")
    >>> parse_option_value(option, "8.2")
    8.2
    """
    if isinstance(raw, bool):
        return raw
    kind = option.type
    if kind == "number":
        return _number(option, raw)
    if kind == "integer":
        return _integer(option, raw)
    if kind == "number_list":
        return _number_list(option, raw)
    if kind == "string_list":
        return _string_list(option, raw)
    if kind in ("object", "object_list"):
        return _json(option, raw)
    return raw
