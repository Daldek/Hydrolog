"""Human-readable terminal rendering of command results and errors.

The summary is *generic*: it walks the JSON form of the envelope
(:meth:`~hydrolog.catalog.CommandResult.to_dict`) and needs no per-command code.

* scalar fields are listed as aligned ``key: value`` lines; numbers are shown with six
  significant digits, inputs with their declared unit (``length_km: 8.2 km``);
* nested objects are indented; objects nested deeper than :data:`MAX_DEPTH` levels are
  shortened to compact JSON;
* a list of scalars is shown in one line (a long one as head, last value, count and,
  for numbers, minimum and maximum);
* a list of objects (records) becomes a table when every cell is short, otherwise a
  list of ``- field: value`` blocks; at most :data:`RECORD_ROWS` rows of a table and
  :data:`RECORD_BLOCKS` blocks are shown;
* several long numeric arrays of equal length in one object (a time axis and its
  values) become one table of the first :data:`ARRAY_ROWS` rows;
* a result that identifies itself as a versioned document (a ``schema`` such as
  ``hydrolog-commands/1``) is printed as pretty JSON and a multi-line text result as it
  is, *without* title and inputs: such a result is meant to be redirected to a file.

Tables are fitted to the terminal width by shortening their text columns; numbers and
headers are never cut. The full data is always available with ``--json``.
"""

from __future__ import annotations

import json
import math
import re
import textwrap
from collections.abc import Mapping, Sequence
from typing import Any, Final

from hydrolog.catalog.spec import Command, Lang
from hydrolog.cli.texts import text

__all__ = [
    "ARRAY_ROWS",
    "INLINE_MAX",
    "MAX_DEPTH",
    "RECORD_BLOCKS",
    "RECORD_ROWS",
    "format_number",
    "render_error",
    "render_result",
]

INLINE_MAX: Final = 8
"""Longest list of scalars that is listed in full on one line."""
ARRAY_ROWS: Final = 12
"""Rows shown of a table of parallel numeric arrays."""
RECORD_ROWS: Final = 200
"""Rows shown of a table of records (a list of objects with short cells)."""
RECORD_BLOCKS: Final = 20
"""Records shown of a list of objects with long or nested cells."""
MAX_DEPTH: Final = 4
"""Levels of nested objects shown before the rest is shortened to compact JSON."""

_INDENT: Final = 2
_HEAD: Final = 5
_MIN_CELL: Final = 8
_CELL_MAX: Final = 60
_SLACK: Final = 2
"""A list that exceeds its limit by at most this much is shown in full."""
_DOCUMENT: Final = re.compile(r"[a-z][a-z0-9_-]*/\d+")


def format_number(value: float) -> str:
    """Format a number for the summary: six significant digits, whole numbers as ints.

    Parameters
    ----------
    value : float
        Number to format.

    Returns
    -------
    str
        ``3.0`` -> ``"3"``, ``85.97330594`` -> ``"85.9733"``, ``1234567.891`` ->
        ``"1234568"``, ``0.0000123`` -> ``"1.23e-05"``.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    rendered = f"{value:.6g}"
    if "e" in rendered and abs(value) >= 1e6:
        rendered = f"{value:.0f}"
    return rendered


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _as_list(value: object) -> Sequence[Any] | None:
    """The value as a list (JSON arrays are lists) or ``None``."""
    return value if isinstance(value, list | tuple) else None


def _is_long_numbers(value: object) -> bool:
    """A long list of numbers (``None`` allowed): material for a table of arrays."""
    items = _as_list(value)
    return (
        items is not None
        and len(items) > INLINE_MAX
        and all(item is None or _is_number(item) for item in items)
        and any(_is_number(item) for item in items)
    )


def _is_document(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    schema = value.get("schema")
    return isinstance(schema, str) and _DOCUMENT.fullmatch(schema) is not None


def _limit(total: int, limit: int) -> int:
    """Rows to show of ``total``: ``limit``, or all when only a few would be left."""
    return total if total <= limit + _SLACK else limit


class _Renderer:
    """Renders JSON-native values as lines of text for one language and width."""

    def __init__(self, lang: Lang, width: int) -> None:
        self.lang = lang
        self.width = max(width, 40)

    def label(self, key: str, **values: object) -> str:
        return text(key, self.lang, **values)

    # --- values ---------------------------------------------------------------------

    def scalar(self, value: object) -> str:
        if value is None:
            return self.label("none")
        if isinstance(value, bool):
            return self.label("yes" if value else "no")
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return format_number(value)
        return str(value)

    def compact(self, value: object, limit: int = _CELL_MAX) -> str:
        """Compact JSON of a nested value, shortened to ``limit`` characters."""
        rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        limit = max(limit, 8)
        return rendered if len(rendered) <= limit else rendered[: limit - 1] + "…"

    def scalar_list(self, values: Sequence[Any]) -> str:
        count = len(values)
        if count <= INLINE_MAX:
            return "[" + ", ".join(self.scalar(item) for item in values) + "]"
        head = ", ".join(self.scalar(item) for item in values[:_HEAD])
        summary = f"n={count}"
        present = [item for item in values if item is not None]
        if present and all(_is_number(item) for item in present):
            low = format_number(min(present))
            high = format_number(max(present))
            summary += f", min={low}, max={high}"
        return f"[{head}, …, {self.scalar(values[-1])}] ({summary})"

    def cell(self, value: object) -> str:
        if _is_scalar(value):
            return self.scalar(value).replace("\n", " ")
        return self.compact(value, _CELL_MAX)

    # --- tables ---------------------------------------------------------------------

    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        numeric: Sequence[bool],
        indent: int,
    ) -> list[str]:
        """Lay out a table; text columns are narrowed to fit and their cells wrapped."""
        widths = [
            max([len(header)] + [len(row[index]) for row in rows])
            for index, header in enumerate(headers)
        ]
        floors = [
            widths[i] if numeric[i] else min(widths[i], max(_MIN_CELL, len(headers[i])))
            for i in range(len(headers))
        ]
        budget = self.width - indent - 2 * (len(headers) - 1)
        while sum(widths) > budget:
            shrinkable = [i for i in range(len(widths)) if widths[i] > floors[i]]
            if not shrinkable:
                break
            widest = max(shrinkable, key=lambda index: widths[index])
            widths[widest] -= 1

        def line(cells: Sequence[str]) -> list[str]:
            wrapped = [
                (
                    [cell]
                    if numeric[index] or len(cell) <= widths[index]
                    else textwrap.wrap(
                        cell,
                        widths[index],
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                    or [""]
                )
                for index, cell in enumerate(cells)
            ]
            out = []
            for row in range(max(len(part) for part in wrapped)):
                parts = []
                for index, cell_lines in enumerate(wrapped):
                    shown = cell_lines[row] if row < len(cell_lines) else ""
                    parts.append(
                        shown.rjust(widths[index])
                        if numeric[index]
                        else shown.ljust(widths[index])
                    )
                out.append(" " * indent + "  ".join(parts).rstrip())
            return out

        lines = line(headers)
        lines.append(" " * indent + "  ".join("-" * w for w in widths))
        for row in rows:
            lines.extend(line(row))
        return lines

    def more(self, count: int, indent: int) -> str:
        return " " * indent + self.label("more_items", count=count)

    def records(
        self, records: Sequence[Mapping[str, Any]], indent: int, depth: int
    ) -> list[str]:
        """A list of objects: a table of short cells, else ``- field: value`` blocks."""
        shown = records[: _limit(len(records), RECORD_ROWS)]
        headers = self.columns(shown)
        flat = all(
            _is_scalar(value) or len(self.compact(value, 10**6)) <= _CELL_MAX
            for record in shown
            for value in record.values()
        )
        if flat and headers:
            rows = [[self.cell(record.get(key)) for key in headers] for record in shown]
            numeric = []
            for key in headers:
                column = [record.get(key) for record in shown]
                numeric.append(
                    any(_is_number(item) for item in column)
                    and all(item is None or _is_number(item) for item in column)
                )
            lines = self.table(headers, rows, numeric, indent)
            if len(records) > len(shown):
                lines.append(self.more(len(records) - len(shown), indent))
            return lines
        blocks = records[: _limit(len(records), RECORD_BLOCKS)]
        lines = []
        for record in blocks:
            body = self.mapping(record, indent + _INDENT, depth + 1)
            if not body:
                lines.append(" " * indent + "- {}")
                continue
            lines.append(body[0][:indent] + "- " + body[0][indent + _INDENT :])
            lines.extend(body[1:])
        if len(records) > len(blocks):
            lines.append(self.more(len(records) - len(blocks), indent))
        return lines

    @staticmethod
    def columns(records: Sequence[Mapping[str, Any]]) -> list[str]:
        headers: list[str] = []
        for record in records:
            for key in record:
                if key not in headers:
                    headers.append(key)
        return headers

    def arrays_table(
        self, columns: Mapping[str, Sequence[object]], indent: int
    ) -> list[str]:
        headers = list(columns)
        total = len(columns[headers[0]])
        shown = _limit(total, ARRAY_ROWS)
        rows = [[self.scalar(columns[key][i]) for key in headers] for i in range(shown)]
        lines = self.table(headers, rows, [True] * len(headers), indent)
        if total > shown:
            lines.append(self.more(total - shown, indent))
        return lines

    # --- objects --------------------------------------------------------------------

    def parallel_arrays(self, data: Mapping[str, Any]) -> list[list[str]]:
        """Groups (two or more) of long numeric arrays of equal length."""
        by_length: dict[int, list[str]] = {}
        for key, value in data.items():
            if _is_long_numbers(value):
                by_length.setdefault(len(value), []).append(key)
        return [keys for keys in by_length.values() if len(keys) >= 2]

    def entry(
        self,
        key: str,
        value: object,
        indent: int,
        depth: int,
        unit: str | None,
    ) -> tuple[str, str | None, list[str]]:
        """Render one field: ``(header, one-line text or None, block lines)``."""
        suffix = f" {unit}" if unit else ""
        if isinstance(value, str) and "\n" in value:
            pad = " " * (indent + _INDENT)
            return key, None, [pad + part for part in value.splitlines()]
        if _is_scalar(value):
            shown = self.scalar(value)
            return key, shown + (suffix if _is_number(value) else ""), []
        room = max(self.width - indent - len(key) - 2, 20)
        if isinstance(value, Mapping):
            if not value:
                return key, "{}", []
            if depth + 1 >= MAX_DEPTH:
                return key, self.compact(value, room), []
            return key, None, self.mapping(value, indent + _INDENT, depth + 1)
        items = _as_list(value)
        if items is not None:
            if not items:
                return key, "[]", []
            if all(_is_scalar(item) for item in items):
                numbers = all(item is None or _is_number(item) for item in items)
                inline = self.scalar_list(items) + (suffix if numbers else "")
                if numbers or len(key) + 2 + len(inline) <= self.width - indent:
                    return key, inline, []
                return key, None, self.bullets(items, indent + _INDENT)
            if all(isinstance(item, Mapping) for item in items) and depth < MAX_DEPTH:
                return (
                    f"{key} ({len(items)})",
                    None,
                    self.records(items, indent + _INDENT, depth),
                )
        return key, self.compact(value, room), []

    def bullets(self, items: Sequence[Any], indent: int) -> list[str]:
        """Items of a list of text, one per line (``- item``)."""
        shown = items[: _limit(len(items), RECORD_BLOCKS)]
        lines = [" " * indent + f"- {self.scalar(item)}" for item in shown]
        if len(items) > len(shown):
            lines.append(self.more(len(items) - len(shown), indent))
        return lines

    def mapping(
        self,
        data: Mapping[str, Any],
        indent: int,
        depth: int = 0,
        units: Mapping[str, str] | None = None,
    ) -> list[str]:
        """Lines of an object: aligned scalars, nested blocks and tables."""
        unit_of = units or {}
        groups = self.parallel_arrays(data)
        first = {group[0]: group for group in groups}
        tabled = {key for group in groups for key in group}
        parts: list[tuple[str, str | None, list[str]]] = []
        for key, value in data.items():
            if key in tabled:
                if key in first:
                    columns = {name: data[name] for name in first[key]}
                    parts.append(("", None, self.arrays_table(columns, indent)))
                continue
            parts.append(self.entry(key, value, indent, depth, unit_of.get(key)))
        width = max((len(h) for h, one, _ in parts if one is not None), default=0)
        pad = " " * indent
        lines: list[str] = []
        for number, (header, one_line, block) in enumerate(parts):
            if one_line is not None:
                lines.append(f"{pad}{(header + ':').ljust(width + 1)} {one_line}")
            elif header:
                lines.append(f"{pad}{header}:")
                lines.extend(block)
            else:
                # A table of arrays stands apart from the fields around it.
                if lines:
                    lines.append("")
                lines.extend(block)
                if number + 1 < len(parts):
                    lines.append("")
        return lines

    def result(self, value: object) -> list[str]:
        """Lines of the ``result`` of an envelope (``Wynik: ...``)."""
        title = self.label("result")
        if isinstance(value, Mapping):
            if not value:
                return [f"{title}: {{}}"]
            return [f"{title}:", *self.mapping(value, _INDENT)]
        items = _as_list(value)
        if items is not None:
            if not items:
                return [f"{title}: []"]
            if all(isinstance(item, Mapping) for item in items):
                return [f"{title} ({len(items)}):", *self.records(items, _INDENT, 0)]
            if all(_is_scalar(item) for item in items):
                return [f"{title}: {self.scalar_list(items)}"]
            return [f"{title}: {self.compact(value, self.width - len(title) - 2)}"]
        return [f"{title}: {self.scalar(value)}"]


def _content(result: object) -> str | None:
    """The result as it is meant to be read: a versioned document or a text.

    A result that names its ``schema`` (``hydrolog-commands/1``) is a document and is
    printed as pretty JSON; a multi-line text (a generated guide) is printed as it is.
    Either can then be redirected to a file.
    """
    if _is_document(result):
        return json.dumps(result, ensure_ascii=False, indent=2)
    if isinstance(result, str) and "\n" in result:
        return result.rstrip("\n")
    return None


def render_result(
    data: Mapping[str, Any],
    command: Command,
    lang: Lang = "pl",
    width: int = 100,
) -> str:
    """Render the ``hydrolog-result/1`` envelope of a command as a text summary.

    Parameters
    ----------
    data : Mapping[str, Any]
        The envelope as returned by ``CommandResult.to_dict()``.
    command : Command
        The command that produced it (its summary and the units of its options are
        shown).
    lang : {"pl", "en"}, optional
        Language of the section titles and of the command summary.
    width : int, optional
        Width of the terminal in characters; tables are fitted to it.

    Returns
    -------
    str
        The summary without a trailing newline: a title line, the inputs with their
        units, the result, the notices and the written files. A document or a text
        result (see the module docstring) replaces the title, inputs and result.
    """
    renderer = _Renderer(lang, width)
    units = {option.name: option.unit for option in command.options if option.unit}
    content = _content(data.get("result"))
    if content is not None:
        lines = [content]
    else:
        lines = [f"{command.name}: {command.summarize(lang)}"]
        inputs = data.get("inputs")
        if inputs:
            lines.append(f"{renderer.label('input')}:")
            lines.extend(renderer.mapping(inputs, _INDENT, units=units))
        lines.extend(renderer.result(data.get("result")))
    notices = data.get("notices") or []
    if notices:
        lines.append(f"{renderer.label('notices')}:")
        for notice in notices:
            level = renderer.label(f"level_{notice['level']}")
            lines.append(f"  [{level}] {notice['code']}: {notice['text']}")
    files = data.get("files") or []
    if files:
        lines.append(f"{renderer.label('files')}:")
        for record in files:
            lines.append(f"  {record['path']}  (sha256 {record['sha256'][:12]}…)")
    return "\n".join(lines)


def render_error(document: Mapping[str, Any], lang: Lang = "pl") -> str:
    """Render a ``hydrolog-error/1`` document as readable text.

    Parameters
    ----------
    document : Mapping[str, Any]
        The error document (:func:`hydrolog.exceptions.error_document`).
    lang : {"pl", "en"}, optional
        Language of the labels; the message and hint stay English.

    Returns
    -------
    str
        ``Błąd (code): title``, the indented message and, when present, the hint.
    """
    lines = [f"{text('error', lang)} ({document['code']}): {document['title']}"]
    message = str(document.get("message") or "").strip()
    if message:
        lines.extend("  " + part for part in message.splitlines())
    hint = document.get("hint")
    if hint:
        lines.append(f"{text('hint', lang)}: {hint}")
    return "\n".join(lines)
