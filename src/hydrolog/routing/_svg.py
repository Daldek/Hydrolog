"""Draw the document ``hydrolog-network-schematic/1`` as SVG (ADR-0013).

The drawing is a function of the document alone: lines in the colours of their line,
a symbol for every kind of node, its label on the side that the document names, and a
legend. Everything is plain SVG made with the standard library, so the text is the same
on every machine: no timestamps, no random ids, numbers rounded the same way. The text
of the drawing is language-neutral: the ids of the nodes, the symbols ``Qp``, ``tp`` and
``V`` with their units, and the names of the kinds of node as the document has them.

The scale is chosen from the labels: a label must fit in one unit of the grid in width
and in four tenths of a unit in height, which is the room that the layout gives it.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any, Final
from xml.sax.saxutils import escape, quoteattr

__all__ = ["schematic_svg"]

_FONT: Final = "Helvetica, Arial, sans-serif"
_ID_SIZE: Final = 13.0
_VALUE_SIZE: Final = 11.0
_TITLE_SIZE: Final = 17.0
_LINE_HEIGHT: Final = 1.22
_MIN_UNIT: Final = 88.0
_UNIT_STEP: Final = 8.0
_MARGIN: Final = 28.0
_STROKE: Final = 7.0
_RADIUS: Final = 9.0
_LABEL_WIDTH: Final = 1.0
_LABEL_HEIGHT: Final = 0.4
_WRAP: Final = 16
_ID_LINES: Final = 3
_MAIN_COLOUR: Final = "#1f5fa8"
_COLOURS: Final = (
    "#d1495b",
    "#2e8b57",
    "#e08e0b",
    "#7b4fa3",
    "#0f8b8d",
    "#c4551d",
    "#5c6b73",
    "#a23b72",
    "#6a994e",
    "#3a86ff",
)
"""The colours of the tributaries, one after the other; the main stem has its own."""
_INK: Final = "#222222"
_PAPER: Final = "#ffffff"
_KIND_ORDER: Final = ("subcatchment", "reach", "reservoir", "junction", "outlet")
_NBSP: Final = "\u00a0"

# a label box is placed from the node: the x of its near edge and the vertical place
_LEFT: Final[Mapping[str, float]] = {
    "n": 0.0,
    "s": 0.0,
    "ne": 0.05,
    "se": 0.05,
    "e": 0.3,
}
_RIGHT: Final[Mapping[str, float]] = {"nw": 0.05, "sw": 0.05, "w": 0.3}


def _number(value: float) -> str:
    """Format a coordinate: two decimals at most, no trailing zeros."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _discharge(value: float) -> str:
    """Format a discharge [m3/s] with three significant digits."""
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2f}"
    return f"{value:.3f}"


def _volume(value: float) -> str:
    """Format a volume [m3] in whole cubic metres, grouped by thousands."""
    return f"{round(value):,}".replace(",", _NBSP)


def _width(text: str, size: float, bold: bool = False) -> float:
    """Return the width of a text in pixels, a little more than it is.

    There are no font metrics here, so the width is estimated from the kinds of the
    characters of a typical sans-serif face; a label that is a little narrower than
    this leaves a little more air, never less.
    """
    total = 0.0
    for char in text:
        if char in " \u00a0.,:;'|!il":
            total += 0.32
        elif char in "mwMW":
            total += 0.9
        elif char.isupper() or char in "/%@#&_":
            total += 0.7
        else:
            total += 0.6
    return total * size * (1.08 if bold else 1.0)


class _Block:
    """The text of a label: lines of ``(text, size, bold)`` and the room they take."""

    def __init__(self, lines: Sequence[tuple[str, float, bool]]) -> None:
        self.lines = list(lines)
        self.width = max(_width(text, size, bold) for text, size, bold in self.lines)
        self.height = sum(size * _LINE_HEIGHT for _, size, _ in self.lines)


def _wrap(text: str) -> list[str]:
    """Break a long id into lines of at most ``_WRAP`` characters, after a separator.

    A piece that is longer than a line is cut; at most ``_ID_LINES`` lines are kept and
    the last ends with an ellipsis when the id is longer (the tooltip has all of it).
    """
    if len(text) <= _WRAP:
        return [text]
    lines: list[str] = []
    current = ""
    for piece in re.findall(r"[^_.\-]+[_.\-]*|[_.\-]+", text):
        while len(piece) > _WRAP:
            if current:
                lines.append(current)
                current = ""
            lines.append(piece[:_WRAP])
            piece = piece[_WRAP:]
        if current and len(current) + len(piece) > _WRAP:
            lines.append(current)
            current = piece
        else:
            current += piece
    if current:
        lines.append(current)
    if len(lines) > _ID_LINES:
        lines = [*lines[: _ID_LINES - 1], lines[_ID_LINES - 1][: _WRAP - 1] + "\u2026"]
    return lines


def _label_lines(node: Mapping[str, Any]) -> list[tuple[str, float, bool]]:
    """Return the lines of the label of a node: its text and, with a result, values."""
    lines = [(part, _ID_SIZE, True) for part in _wrap(str(node["label"]["text"]))]
    if "peak_m3s" in node:
        lines.append(
            (f"Qp {_discharge(node['peak_m3s'])} m\u00b3/s", _VALUE_SIZE, False)
        )
        lines.append((f"tp {node['time_to_peak_min']:g} min", _VALUE_SIZE, False))
        lines.append((f"V {_volume(node['volume_m3'])} m\u00b3", _VALUE_SIZE, False))
    return lines


def _tooltip(node: Mapping[str, Any]) -> str:
    """Return the text that a viewer shows when the pointer rests on a node."""
    lines = [f"{node['id']} ({node['type']})"]
    if "peak_m3s" in node:
        peak = _discharge(node["peak_m3s"])
        lines.append(f"Qp {peak} m3/s at {node['time_to_peak_min']:g} min")
        lines.append(f"V {_volume(node['volume_m3'])} m3")
    for item in node["parameters"]:
        unit = "" if item["unit"] is None else f" {item['unit']}"
        value = item["value"]
        shown = f"{value:g}" if isinstance(value, float) else str(value)
        lines.append(f"{item['name']} = {shown}{unit} ({item['source']})")
    lines.extend(
        f"[{item['level']}] {item['code']}: {item['message']}"
        for item in node.get("notices", ())
    )
    return "\n".join(lines)


def _colour(line: int) -> str:
    """Return the colour of a line of the map."""
    return _MAIN_COLOUR if line == 0 else _COLOURS[(line - 1) % len(_COLOURS)]


class _Drawing:
    """The geometry of one drawing: the scale, the origin and the box of every label."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        self.document = document
        self.nodes: list[Mapping[str, Any]] = document["nodes"]
        self.blocks = {node["id"]: _Block(_label_lines(node)) for node in self.nodes}
        need_width = max(block.width for block in self.blocks.values()) / _LABEL_WIDTH
        need_height = (
            max(block.height for block in self.blocks.values()) / _LABEL_HEIGHT
        )
        self.unit = (
            math.ceil(max(_MIN_UNIT, need_width + 10, need_height + 4) / _UNIT_STEP)
            * _UNIT_STEP
        )
        self.title = self._title()
        boxes = [self.label_box(node, 0.0, 0.0) for node in self.nodes]
        reach = self.unit * 0.3
        left = min(box[0] for box in boxes)
        right = max(box[2] for box in boxes)
        top = min(box[1] for box in boxes)
        bottom = max(box[3] for box in boxes)
        grid = document["grid"]
        left = min(left, -reach)
        top = min(top, -reach)
        right = max(right, grid["width"] * self.unit + reach)
        bottom = max(bottom, grid["height"] * self.unit + reach)
        # the legend sits under the picture, the title above it
        self.legend = self._legend_kinds()
        legend_width = len(self.legend) * self.legend_step()
        head = _TITLE_SIZE * 2.4 if self.title else 0.0
        self.origin_x = _MARGIN - left
        self.origin_y = _MARGIN + head - top
        self.width = max(right - left, legend_width) + 2 * _MARGIN
        self.legend_y = self.origin_y + bottom + 22.0
        self.height = self.legend_y + 18.0 + _MARGIN

    def _title(self) -> str:
        """Return the title: the name of the network, if it has one."""
        name = self.document.get("name")
        return "" if name is None else str(name)

    def _legend_kinds(self) -> list[str]:
        """Return the kinds of node of the picture, in the order of the legend."""
        found = {str(node["type"]) for node in self.nodes}
        return [kind for kind in _KIND_ORDER if kind in found] + sorted(
            found.difference(_KIND_ORDER)
        )

    def legend_step(self) -> float:
        """Return the width that an item of the legend takes."""
        names = [*self._legend_kinds(), ""]
        return max(_width(name, _VALUE_SIZE) for name in names) + 56.0

    def px(self, x: float, y: float) -> tuple[float, float]:
        """Return the place on the drawing of the point ``(x, y)`` of the grid."""
        return (self.origin_x + x * self.unit, self.origin_y + y * self.unit)

    def label_box(
        self, node: Mapping[str, Any], origin_x: float, origin_y: float
    ) -> tuple[float, float, float, float]:
        """Return ``(left, top, right, bottom)`` of the label of a node."""
        block = self.blocks[node["id"]]
        side = node["label"]["side"]
        cx = origin_x + node["x"] * self.unit
        cy = origin_y + node["y"] * self.unit
        unit = self.unit
        if side in _LEFT:
            left = cx + unit * _LEFT[side] - (block.width / 2 if side in "ns" else 0.0)
        else:
            left = cx - unit * _RIGHT[side] - block.width
        if side.startswith("n"):
            top = cy - 0.15 * unit - block.height
        elif side.startswith("s"):
            top = cy + 0.15 * unit
        else:
            top = cy - block.height / 2
        return (left, top, left + block.width, top + block.height)


def _glyph(kind: str, x: float, y: float, colour: str) -> str:
    """Return the symbol of a kind of node, centred on ``(x, y)``."""
    r = _RADIUS
    cx, cy = _number(x), _number(y)
    if kind == "subcatchment":
        reach = 1.25 * r
        points = (
            f"{_number(x)},{_number(y - reach)} {_number(x + reach)},{cy} "
            f"{_number(x)},{_number(y + reach)} {_number(x - reach)},{cy}"
        )
        return (
            f'<polygon points="{points}" fill="{colour}" stroke="{_PAPER}" '
            'stroke-width="2.5" stroke-linejoin="round"/>'
        )
    if kind == "junction":
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{_number(1.15 * r)}" fill="{_PAPER}" '
            f'stroke="{_INK}" stroke-width="3.5"/>'
        )
    if kind == "reservoir":
        side = 2.0 * r
        return (
            f'<rect x="{_number(x - side / 2)}" y="{_number(y - 0.7 * r)}" '
            f'width="{_number(side)}" height="{_number(1.4 * r)}" rx="2" '
            f'fill="{_PAPER}" stroke="{colour}" stroke-width="3.5"/>'
            f'<path d="M{_number(x - 0.55 * r)},{cy} h{_number(1.1 * r)}" '
            f'stroke="{colour}" stroke-width="2" fill="none"/>'
        )
    if kind == "outlet":
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{_number(1.4 * r)}" fill="{_INK}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{_number(0.85 * r)}" fill="{_PAPER}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{_number(0.45 * r)}" fill="{_INK}"/>'
        )
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{_number(0.8 * r)}" fill="{_PAPER}" '
        f'stroke="{colour}" stroke-width="3.5"/>'
    )


def _text(
    x: float, y: float, text: str, size: float, anchor: str, *, bold: bool = False
) -> str:
    """Return a text element; a white outline keeps it readable over a line."""
    weight = ' font-weight="bold"' if bold else ""
    return (
        f'<text x="{_number(x)}" y="{_number(y)}" font-size="{_number(size)}"{weight} '
        f'text-anchor="{anchor}" fill="{_INK}" stroke="{_PAPER}" stroke-width="3" '
        f'stroke-linejoin="round" paint-order="stroke">{escape(text)}</text>'
    )


def _label(drawing: _Drawing, node: Mapping[str, Any]) -> list[str]:
    """Return the text elements of the label of a node."""
    block = drawing.blocks[node["id"]]
    left, top, right, _ = drawing.label_box(node, drawing.origin_x, drawing.origin_y)
    side = node["label"]["side"]
    if side in ("n", "s"):
        anchor, x = "middle", (left + right) / 2
    elif side in _LEFT:
        anchor, x = "start", left
    else:
        anchor, x = "end", right
    elements: list[str] = []
    y = top
    for text, size, bold in block.lines:
        y += size * _LINE_HEIGHT
        elements.append(_text(x, y - size * 0.25, text, size, anchor, bold=bold))
    return elements


def _badge(x: float, y: float) -> str:
    """Return the mark of a node that has a warning among its notices."""
    return (
        f'<circle cx="{_number(x)}" cy="{_number(y)}" r="7" fill="#d9480f" '
        f'stroke="{_PAPER}" stroke-width="1.5"/>'
        f'<text x="{_number(x)}" y="{_number(y + 3.8)}" font-size="10" '
        f'font-weight="bold" text-anchor="middle" fill="{_PAPER}">!</text>'
    )


def _legend(drawing: _Drawing) -> list[str]:
    """Return the legend: the symbol and the name of every kind of node."""
    step = drawing.legend_step()
    elements: list[str] = []
    for number, kind in enumerate(drawing.legend):
        x = _MARGIN + number * step + 12.0
        y = drawing.legend_y
        elements.append(_glyph(kind, x, y, "#5c6b73"))
        elements.append(
            f'<text x="{_number(x + 24)}" y="{_number(y + 4)}" '
            f'font-size="{_number(_VALUE_SIZE)}" fill="{_INK}">{escape(kind)}</text>'
        )
    return elements


def schematic_svg(document: Mapping[str, Any]) -> str:
    """Draw a ``hydrolog-network-schematic/1`` document as SVG.

    Parameters
    ----------
    document : mapping
        The document of :meth:`RoutingNetwork.schematic
        <hydrolog.routing.RoutingNetwork.schematic>`; the picture is a function of it
        alone.

    Returns
    -------
    str
        An SVG document (UTF-8 text, Unix line ends, a final newline): the lines in the
        colours of their line (the main stem in blue), a symbol for every kind of node,
        each node's id and, when the document has a result, its ``Qp`` (peak discharge,
        m3/s), ``tp`` (time to peak, min) and ``V`` (volume, m3); a node that has a
        warning carries a mark, and the parameters and notices of a node are the text
        that a viewer shows over it. The text is the same on every machine.

    Examples
    --------
    >>> document = {
    ...     "schema": "hydrolog-network-schematic/1", "outlet": "B",
    ...     "has_result": False,
    ...     "grid": {"width": 1, "height": 0}, "lines": [],
    ...     "nodes": [
    ...         {"id": "A", "type": "subcatchment", "x": 0, "y": 0, "line": 0,
    ...          "label": {"text": "A", "side": "n"}, "parameters": []},
    ...         {"id": "B", "type": "outlet", "x": 1, "y": 0, "line": 0,
    ...          "label": {"text": "B", "side": "n"}, "parameters": []},
    ...     ],
    ...     "edges": [{"from": "A", "to": "B", "line": 0, "points": [[0, 0], [1, 0]]}],
    ... }
    >>> schematic_svg(document).count("<polyline")
    1
    """
    drawing = _Drawing(document)
    width, height = _number(drawing.width), _number(drawing.height)
    name = drawing.title or "Network schematic"
    nodes = drawing.nodes
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="title desc" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family={quoteattr(_FONT)}>',
        f'<title id="title">{escape(name)}</title>',
        f'<desc id="desc">{escape(str(document["schema"]))}: {len(nodes)} nodes, '
        f"outlet {escape(str(document['outlet']))}</desc>",
        f'<rect width="{width}" height="{height}" fill="{_PAPER}"/>',
    ]
    if drawing.title:
        parts.append(
            f'<text x="{_number(_MARGIN)}" y="{_number(_MARGIN + _TITLE_SIZE)}" '
            f'font-size="{_number(_TITLE_SIZE)}" font-weight="bold" fill="{_INK}">'
            f"{escape(drawing.title)}</text>"
        )
    # the lines nearest the main stem are drawn last, so that a line that runs along
    # another one (the last stretch before a node with many inflows) shows the colour of
    # the line it runs into
    for edge in sorted(document["edges"], key=lambda item: -item["line"]):
        points = " ".join(
            f"{_number(x)},{_number(y)}"
            for x, y in (drawing.px(px, py) for px, py in edge["points"])
        )
        parts.append(
            f'<polyline points="{points}" fill="none" '
            f'stroke="{_colour(edge["line"])}" stroke-width="{_number(_STROKE)}" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for node in nodes:
        x, y = drawing.px(node["x"], node["y"])
        parts.append(f"<g><title>{escape(_tooltip(node))}</title>")
        parts.append(_glyph(str(node["type"]), x, y, _colour(node["line"])))
        if any(item["level"] == "warning" for item in node.get("notices", ())):
            parts.append(_badge(x + 1.1 * _RADIUS, y - 1.1 * _RADIUS))
        parts.append("</g>")
    for node in nodes:
        parts.extend(_label(drawing, node))
    parts.extend(_legend(drawing))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
