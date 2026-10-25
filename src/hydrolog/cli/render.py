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
* the ``schema`` of the result is not shown, its ``files`` come last as the written
  files, after the notices.

Five documents have a layout of their own: the plan of ``--check``
(``hydrolog-plan/1``: each target with its action, and a line that nothing was
written), ``commands list`` (a table of names and summaries and the page),
``commands schema`` (each command with its options, rules and examples), ``commands
guide`` (the text of the guide, or the written file) and ``config show`` (a table of
the settings with their source, the settings file, credentials and store).

Tables are fitted to the terminal width by shortening their text columns; numbers and
headers are never cut. The full data is always available with ``--json``.
"""

from __future__ import annotations

import json
import math
import textwrap
from collections.abc import Mapping, Sequence
from typing import Any, Final

from hydrolog.catalog.document import COMMAND_LIST_SCHEMA, COMMANDS_SCHEMA
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
_PLAN_SCHEMA: Final = "hydrolog-plan/1"
"""``schema`` of the plan of ``--check`` (``hydrolog.operations.PLAN_SCHEMA``)."""
_CONFIG_SCHEMA: Final = "hydrolog-config/1"
_GUIDE_SCHEMA: Final = "hydrolog-guide/1"
_ENVELOPE_KEYS: Final = ("schema", "files")
"""Keys of a result that the summary shows as sections, not as fields."""
_CONFLICT_REASONS: Final = ("output_exists", "duplicate_output_name", "output_in_store")


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
    """Return the value as a list (JSON arrays are lists) or ``None``."""
    return value if isinstance(value, list | tuple) else None


def _is_long_numbers(value: object) -> bool:
    """Check for a long list of numbers (``None`` allowed): material for a table."""
    items = _as_list(value)
    return (
        items is not None
        and len(items) > INLINE_MAX
        and all(item is None or _is_number(item) for item in items)
        and any(_is_number(item) for item in items)
    )


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
        """Render a list of objects: a table of short cells, else ``- field: value``."""
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
        """Find groups (two or more) of long numeric arrays of equal length."""
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
        if isinstance(value, str) and "\n" in value:
            return [f"{title}:", *(" " * _INDENT + part for part in value.splitlines())]
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


def _catalog_commands() -> dict[str, Command]:
    """Return the catalog by command name (for summaries in the user's language)."""
    from hydrolog.catalog import data_commands

    return {command.name: command for command in data_commands()}


def _header(command: Command, lang: Lang) -> str:
    return f"{command.name}: {command.summarize(lang)}"


def _page_lines(renderer: _Renderer, shown: int, page: object) -> list[str]:
    """Return the line(s) that tell how much of a collection is shown (``page``)."""
    if not isinstance(page, Mapping):
        return [renderer.label("page_total", total=shown)]
    total = page.get("total", shown)
    if not page.get("truncated"):
        return [renderer.label("page_total", total=total)]
    lines = [renderer.label("page_shown", shown=shown, total=total)]
    cursor = page.get("next_cursor")
    if cursor:
        lines.append(renderer.label("page_next", cursor=cursor))
    return lines


def _tail(renderer: _Renderer, data: Mapping[str, Any]) -> list[str]:
    """Return the notices and the written files that follow every result."""
    lines: list[str] = []
    notices = data.get("notices") or []
    if notices:
        lines.append(f"{renderer.label('notices')}:")
        for notice in notices:
            level = renderer.label(f"level_{notice['level']}")
            lines.append(f"  [{level}] {notice['code']}: {notice['message']}")
    result = data.get("result")
    files = (result.get("files") if isinstance(result, Mapping) else None) or []
    if files:
        lines.append(f"{renderer.label('files')}:")
        for record in files:
            status = renderer.label(f"file_{record['status']}")
            size = renderer.label("file_bytes", size=record["size_bytes"])
            digest = f"sha256 {record['sha256'][:12]}…"
            lines.append(f"  {record['path']}  ({status}, {size}, {digest})")
    return lines


# --- documents with their own rendering -----------------------------------------------


def _plan_lines(renderer: _Renderer, result: Mapping[str, Any]) -> list[str]:
    """Render the ``hydrolog-plan/1`` document: each target with its action."""
    lines = [renderer.label("plan_title")]
    targets = result.get("targets") or []
    if not targets:
        return [*lines, renderer.label("plan_empty")]
    headers = [
        renderer.label("plan_action"),
        renderer.label("plan_option"),
        renderer.label("plan_path"),
        renderer.label("plan_note"),
    ]
    rows = []
    for target in targets:
        reason = target.get("reason")
        note = renderer.label(f"plan_{reason}") if reason else ""
        action = renderer.label(f"plan_{target['action']}")
        rows.append([action, str(target["option"]), str(target["path"]), note])
    lines.extend(renderer.table(headers, rows, [False] * len(headers), 0))
    if any(target["action"] == "conflict" for target in targets):
        lines.append(renderer.label("plan_blocked"))
    return lines


def _command_list_lines(
    renderer: _Renderer, result: Mapping[str, Any], page: object
) -> list[str]:
    """Render ``hydrolog-command-list/1``: name and summary of each command."""
    known = _catalog_commands()
    entries = result.get("commands") or []
    rows = []
    for entry in entries:
        command = known.get(entry["name"])
        summary = command.summarize(renderer.lang) if command else entry["summary"]
        rows.append([entry["name"], summary])
    headers = [renderer.label("command"), renderer.label("summary")]
    lines = renderer.table(headers, rows, [False, False], 0)
    return [*lines, *_page_lines(renderer, len(entries), page)]


def _schema_option_row(
    renderer: _Renderer, option: Mapping[str, Any], polish: bool
) -> list[str]:
    """One row of the options table of ``commands schema``."""
    enum = option.get("enum")
    if enum:
        kind = "|".join(item["value"] for item in enum)
    else:
        kind = str(option["type"])
        if option.get("items"):
            kind = f"{kind}[{option['items']}]"
    if option.get("unit"):
        kind += f" [{option['unit']}]"
    translated = option.get("i18n", {}).get("pl", {}) if polish else {}
    description = translated.get("description") or option.get("description", "")
    default = option.get("default")
    return [
        option["name"],
        kind,
        renderer.label("yes" if option.get("required") else "no"),
        "" if default is None else renderer.cell(default),
        str(description),
    ]


def _schema_lines(renderer: _Renderer, entry: Mapping[str, Any]) -> list[str]:
    """One command of a ``hydrolog-commands/1`` document as readable text."""
    polish = renderer.lang == "pl"
    translated = entry.get("i18n", {}).get("pl", {}) if polish else {}
    summary = translated.get("summary") or entry["summary"]
    description = translated.get("description") or entry.get("description", "")
    lines = [f"{entry['name']} ({entry['operation_id']}): {summary}"]
    lines.extend(
        textwrap.wrap(
            description,
            renderer.width - _INDENT,
            initial_indent=" " * _INDENT,
            subsequent_indent=" " * _INDENT,
            break_on_hyphens=False,
        )
    )
    effects = entry.get("effects") or {}
    key = (
        "schema_effects_read_only"
        if effects.get("read_only")
        else "schema_effects_writes"
    )
    lines.append(" " * _INDENT + renderer.label(key))
    options = entry.get("options") or []
    if options:
        lines.append(f"{renderer.label('schema_options')}:")
        headers = [
            renderer.label("schema_name"),
            renderer.label("schema_type"),
            renderer.label("schema_required"),
            renderer.label("schema_default"),
            renderer.label("schema_description"),
        ]
        rows = [_schema_option_row(renderer, option, polish) for option in options]
        lines.extend(renderer.table(headers, rows, [False] * len(headers), _INDENT))
        for option in options:
            meanings = (
                option.get("i18n", {}).get("pl", {}).get("enum") if polish else None
            )
            for item in option.get("enum") or []:
                meaning = (meanings or {}).get(item["value"]) or item["meaning"]
                lines.append(f"  {option['name']}: {item['value']} = {meaning}")
    groups = entry.get("one_of") or []
    if groups:
        joined = " | ".join("+".join(group) for group in groups)
        lines.append(renderer.label("schema_one_of", groups=joined))
    rules = (translated.get("rules") if polish else None) or entry.get("rules") or []
    if rules:
        lines.append(f"{renderer.label('schema_rules')}:")
        lines.extend(f"  - {rule}" for rule in rules)
    examples = entry.get("examples") or []
    if examples:
        lines.append(f"{renderer.label('schema_examples')}:")
        lines.extend(f"  {example['call']}" for example in examples)
    errors = entry.get("errors") or []
    if errors:
        lines.append(f"{renderer.label('schema_errors')}: {', '.join(errors)}")
    return lines


def _catalog_lines(
    renderer: _Renderer, result: Mapping[str, Any], page: object
) -> list[str]:
    """Render ``hydrolog-commands/1``: every command, then the page."""
    entries = result.get("commands") or []
    lines: list[str] = []
    for entry in entries:
        if lines:
            lines.append("")
        lines.extend(_schema_lines(renderer, entry))
    if page is not None:
        lines.extend(["", *_page_lines(renderer, len(entries), page)])
    return lines


def _config_lines(renderer: _Renderer, result: Mapping[str, Any]) -> list[str]:
    """Render the ``hydrolog-config/1`` document of ``config show``."""
    headers = [
        renderer.label("config_setting"),
        renderer.label("config_value"),
        renderer.label("config_source"),
    ]
    rows = []
    for setting in result.get("settings") or []:
        source = renderer.label(f"source_{setting['source']}")
        if setting.get("detail"):
            source += f" ({setting['detail']})"
        rows.append([setting["key"], str(setting["value"]), source])
    lines = renderer.table(headers, rows, [False] * len(headers), 0)
    config_file = result.get("config_file") or {}
    state = renderer.label(
        "config_file_exists" if config_file.get("exists") else "config_file_absent"
    )
    lines.append(
        renderer.label("config_file", path=config_file.get("path", ""), state=state)
    )
    credentials = result.get("credentials") or []
    if credentials:
        lines.append(f"{renderer.label('config_credentials')}:")
        for item in credentials:
            state = renderer.label(
                "config_present" if item["present"] else "config_missing"
            )
            lines.append(f"  {item['name']}: {state}")
    else:
        lines.append(
            f"{renderer.label('config_credentials')}: {renderer.label('none')}"
        )
    store = result.get("store")
    shown = renderer.label("none") if store is None else renderer.compact(store)
    lines.append(f"{renderer.label('config_store')}: {shown}")
    return lines


def _generic_lines(
    renderer: _Renderer, command: Command, data: Mapping[str, Any]
) -> list[str]:
    """Render the inputs and the result of any command, walked generically."""
    units = {option.name: option.unit for option in command.options if option.unit}
    lines: list[str] = []
    inputs = data.get("inputs")
    if inputs:
        lines.append(f"{renderer.label('input')}:")
        lines.extend(renderer.mapping(inputs, _INDENT, units=units))
    result = data.get("result")
    if isinstance(result, Mapping):
        result = {k: v for k, v in result.items() if k not in _ENVELOPE_KEYS}
    lines.extend(renderer.result(result))
    return lines


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
        The summary without a trailing newline. A generic result is a title line, the
        inputs with their units and the result (without its ``schema`` and ``files``);
        the plan of ``--check``, ``commands list`` and ``schema``, ``commands guide``
        and ``config show`` have their own layout (see the module docstring). The
        notices and the written files (``result.files``) come last.
    """
    renderer = _Renderer(lang, width)
    result = data.get("result")
    schema = result.get("schema") if isinstance(result, Mapping) else None
    page = data.get("page")
    head = [_header(command, lang)]
    body: list[str]
    if schema == _PLAN_SCHEMA and isinstance(result, Mapping):
        body = _plan_lines(renderer, result)
    elif schema == COMMAND_LIST_SCHEMA and isinstance(result, Mapping):
        body = _command_list_lines(renderer, result, page)
    elif schema == COMMANDS_SCHEMA and isinstance(result, Mapping):
        head, body = [], _catalog_lines(renderer, result, page)
    elif schema == _CONFIG_SCHEMA and isinstance(result, Mapping):
        body = _config_lines(renderer, result)
    elif schema == _GUIDE_SCHEMA and isinstance(result, Mapping):
        if result.get("files"):
            body = []
        else:
            head, body = [], str(result.get("text", "")).rstrip("\n").splitlines()
    else:
        body = _generic_lines(renderer, command, data)
    return "\n".join([*head, *body, *_tail(renderer, data)])


def render_error(document: Mapping[str, Any], lang: Lang = "pl") -> str:
    """Render a ``hydrolog-error/1`` document as readable text.

    Parameters
    ----------
    document : Mapping[str, Any]
        The error document (:func:`hydrolog.exceptions.error_document`); its
        ``title`` is shown as it is, so pass the document made for ``lang``.
    lang : {"pl", "en"}, optional
        Language of the labels. The message and hint stay English, except for a
        ``conflict`` that names ``details.paths``: its explanation and remedy are
        written in ``lang``.

    Returns
    -------
    str
        ``Błąd (code): title``, the indented message and, when present, the hint.
    """
    lines = [f"{text('error', lang)} ({document['code']}): {document['title']}"]
    details = document.get("details") or {}
    reason = details.get("reason")
    paths = details.get("paths")
    if (
        document["code"] == "conflict"
        and reason in _CONFLICT_REASONS
        and isinstance(paths, list)
        and paths
    ):
        lines.append("  " + text(f"conflict_{reason}", lang))
        lines.extend(f"    {path}" for path in paths)
        lines.append(f"{text('hint', lang)}: {text(f'conflict_{reason}_hint', lang)}")
        return "\n".join(lines)
    message = str(document.get("message") or "").strip()
    if message:
        lines.extend("  " + part for part in message.splitlines())
    hint = document.get("hint")
    if hint:
        lines.append(f"{text('hint', lang)}: {hint}")
    return "\n".join(lines)
