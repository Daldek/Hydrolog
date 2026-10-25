"""Metro-style layout of a tree of flow: octilinear lines on an integer grid (ADR-0013).

The layout takes a tree that flows to one root (the outlet of a network): each node has
the nodes that flow into it and flows into one node itself. It draws the tree like a
metro map of Beck: a **main stem** on a straight horizontal axis and **tributaries**
that join it, and each other, at 45 degrees, every segment running at 0, 45 or 90
degrees on the integer grid. Water flows to the right: the outlet is the node with the
largest ``x``, and ``y`` grows downwards (the convention of a screen and of SVG).

The rules, in the order the layout applies them:

1. **Rank.** The inflows of a node are ranked by what drains through them: the largest
   drained ``weight`` (an area that the caller gives) when the caller gives weights,
   else the most nodes; ties go to the smaller id. The best one continues the line
   that the node is on, the others start tributaries.
2. **Lines.** The *main stem* runs from the outlet up through the best inflow of every
   node (or through the nodes that the caller declares). A *tributary* starts at an
   inflow that is not the best one and follows the best inflow of every node above it.
   A line is straight: its nodes are on one row, one grid unit apart, and the main
   stem is on row 0.
3. **Joins.** A tributary flows into a node of another line at 45 degrees from the row
   above or below that line, after a vertical leg of 90 degrees when it lies further
   out. On the main stem the tributaries take the sides alternately, the first above;
   a tributary of a tributary lies on the side that points away from its parent line.
   Tributaries are drawn headwaters first, so one downstream passes outside the ones
   upstream of it and nothing crosses; each takes the row nearest to its parent whose
   cells are free.
4. **Taps.** A node of the main stem takes two joins, one from each side, and a node
   of a tributary takes one. More lines join the line just before the node, at *taps*,
   and run along it into the node, a tap for every two lines (every line on a
   tributary): the stretch before such a node is longer by the taps, and the edges that
   join at taps share their last stretch with the line and with each other, and nothing
   else.
5. **Labels.** The label of a node goes to the first of the eight compass points around
   it where it lies on no line, no other node and no other label.

Nothing here depends on a calculation: the input is ids and numbers, the output is
cells, so every consumer that draws it draws the same picture.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from hydrolog.exceptions import InvalidParameterError

__all__ = ["LABEL_SIDES", "Layout", "Line", "layout"]

Point = tuple[int, int]
Box = tuple[float, float, float, float]

ABOVE: Final = -1
BELOW: Final = 1

LABEL_SIDES: Final = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
"""The places of a label around its node, as compass points on the screen (``n`` is
above the node): the label is centred on the node for ``n`` and ``s``, begins at the
node and runs to the right for ``ne``, ``e`` and ``se``, and ends at the node and
runs to the left for ``nw``, ``w`` and ``sw``."""

_LABEL_BOXES: Final[Mapping[str, Box]] = {
    "n": (-0.5, 0.5, -0.55, -0.15),
    "s": (-0.5, 0.5, 0.15, 0.55),
    "ne": (0.05, 1.05, -0.55, -0.15),
    "se": (0.05, 1.05, 0.15, 0.55),
    "nw": (-1.05, -0.05, -0.55, -0.15),
    "sw": (-1.05, -0.05, 0.15, 0.55),
    "e": (0.3, 1.3, -0.2, 0.2),
    "w": (-1.3, -0.3, -0.2, 0.2),
}
"""The box that a label takes in grid units, relative to its node: ``(x0, x1, y0, y1)``.
A label is at most one unit wide and 0.4 units high, so the labels of two nodes one row
apart that face each other meet in the middle of the gap and do not overlap."""
_LABEL_ORDER: Final = ("n", "s", "ne", "se", "nw", "sw", "e", "w")
_NODE_CLEARANCE: Final = 0.12
"""Half the side of the square that a node keeps free of labels [grid units]."""


@dataclass(frozen=True)
class Line:
    """A line of the schematic: the main stem or one tributary.

    Attributes
    ----------
    index : int
        The number of the line: 0 is the main stem, the others follow in the order they
        were drawn.
    nodes : tuple of str
        The ids from the head (the farthest node upstream) to the last node of the
        line: the outlet for the main stem, else the node that flows into ``joins``.
    joins : str or None
        The id of the node of the parent line that the last node flows into; ``None``
        for the main stem.
    parent : int or None
        The index of the line that ``joins`` is on; ``None`` for the main stem.
    row : int
        The ``y`` of the nodes of the line.
    """

    index: int
    nodes: tuple[str, ...]
    joins: str | None
    parent: int | None
    row: int


@dataclass(frozen=True)
class Layout:
    """The picture of a tree: where every node is and how every edge runs.

    Attributes
    ----------
    positions : dict of str to tuple of int
        ``(x, y)`` of every node on the grid, ``0 <= x <= width`` and
        ``0 <= y <= height``; ``x`` grows downstream, ``y`` downwards.
    routes : dict of str to tuple of tuple of int
        For every node but the root the corners of the polyline of the edge from the
        node to the node it flows into, the first corner the node and the last the node
        it flows into. Every segment runs at 0, 45 or 90 degrees.
    lines : tuple of Line
        The lines, the main stem first.
    line_of : dict of str to int
        The index of the line each node is on.
    labels : dict of str to str
        The place of the label of every node (one of :data:`LABEL_SIDES`).
    width, height : int
        The extent of the nodes in grid units.
    """

    positions: dict[str, Point]
    routes: dict[str, tuple[Point, ...]]
    lines: tuple[Line, ...]
    line_of: dict[str, int]
    labels: dict[str, str]
    width: int
    height: int


class _Tree:
    """The tree with its inflows ranked and its subtrees measured."""

    def __init__(
        self,
        root: str,
        inflows: Mapping[str, Sequence[str]],
        weight: Mapping[str, float] | None,
    ) -> None:
        found = [root]
        depth = {root: 0}
        for node in found:  # a list that grows: breadth first
            for upstream in inflows.get(node, ()):
                if upstream in depth:
                    raise ValueError(f"{upstream!r} flows into two nodes or cycles")
                depth[upstream] = depth[node] + 1
                found.append(upstream)
        size: dict[str, int] = {}
        drained: dict[str, float] = {}
        for node in reversed(found):  # upstream before downstream
            above = sorted(inflows.get(node, ()))  # the same sum in any input order
            size[node] = 1 + sum(size[up] for up in above)
            drained[node] = (0.0 if weight is None else weight.get(node, 0.0)) + sum(
                drained[up] for up in above
            )

        def rank(up: str) -> tuple[float, int, str]:
            area = 0.0 if weight is None else -round(drained[up], 9)
            return (area, -size[up], up)

        self.root = root
        self.depth = depth
        self.inflows: dict[str, tuple[str, ...]] = {
            node: tuple(sorted(inflows.get(node, ()), key=rank)) for node in found
        }
        self.flows_into: dict[str, str | None] = {root: None}
        order = [root]
        for node in order:  # again, now in the order of the ranks
            for upstream in self.inflows[node]:
                self.flows_into[upstream] = node
                order.append(upstream)
        self.nodes: tuple[str, ...] = tuple(order)

    def chain(self, last: str, forced: Mapping[str, str] | None = None) -> list[str]:
        """Return the line that ends at ``last``: from its head down to ``last``.

        At every node the line follows the node that ``forced`` names, else the best
        inflow.
        """
        nodes = [last]
        while self.inflows[nodes[-1]]:
            node = nodes[-1]
            nodes.append(
                forced[node] if forced and node in forced else self.inflows[node][0]
            )
        nodes.reverse()
        return nodes

    def path_to_root(self, node: str) -> list[str]:
        """Return ``node`` and every node below it down to the root."""
        path = [node]
        while (below := self.flows_into[path[-1]]) is not None:
            path.append(below)
        return path


@dataclass
class _Placed:
    """A line that has its place on the grid."""

    index: int
    nodes: list[str]
    row: int
    side: int
    parent: int | None
    joins: str | None


@dataclass(frozen=True)
class _Join:
    """A tributary that waits for its place on a line that is drawn already."""

    line: _Placed
    node: str
    top: str
    tap: int
    side: int


class _Grid:
    """The cells that are taken: points of the lines and squares of their diagonals.

    A point is a node, a corner or a point that an edge runs through. Two diagonals in
    one square of the grid cross or overlap, so a square holds at most one.
    """

    def __init__(self) -> None:
        self.points: dict[Point, object] = {}
        self.squares: set[Point] = set()

    def free(
        self,
        points: Sequence[Point],
        squares: Sequence[Point],
        *,
        margins: Sequence[Point],
        shared: Sequence[Point],
        tap_of: str,
    ) -> bool:
        """Whether nothing lies on the given points and squares.

        ``shared`` are points of the stretch before the node ``tap_of``, which the
        edges that flow into that node may share; ``margins`` must be free but are not
        taken.
        """
        if any(point in self.points for point in (*points, *margins)):
            return False
        if any(
            (owner := self.points.get(point)) is not None and owner != ("tap", tap_of)
            for point in shared
        ):
            return False
        return not any(square in self.squares for square in squares)

    def take(
        self, points: Sequence[tuple[Point, object]], squares: Sequence[Point]
    ) -> None:
        """Take the points (with their owners) and the squares."""
        self.points.update(points)
        self.squares.update(squares)


def _taps(side_inflows: int, slots: int) -> int:
    """Return the taps that a node with this many side inflows needs.

    The node takes ``slots`` joins itself, and every tap before it takes as many more.
    """
    return max(0, -(-side_inflows // slots) - 1)


def layout(
    root: str,
    inflows: Mapping[str, Sequence[str]],
    *,
    weight: Mapping[str, float] | None = None,
    main_stem: Sequence[str] = (),
) -> Layout:
    """Draw a tree of flow as a metro map.

    Parameters
    ----------
    root : str
        The node every other node flows to (the outlet).
    inflows : mapping of str to sequence of str
        For every node the nodes that flow into it; a node that is missing has none.
        The nodes must make a tree below ``root``.
    weight : mapping of str to float, optional
        What each node adds to the area that drains through it, for example the area
        of a subcatchment (0 for a node that has none; a missing id counts 0). Without
        it the branch with more nodes is the larger.
    main_stem : sequence of str, optional
        Nodes that the main stem must pass. They must lie on one path to the root; the
        stem follows that path and, above its farthest node, the larger branch.

    Returns
    -------
    Layout
        Positions on the grid, the polyline of every edge, the lines and the place of
        every label.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``unknown_node`` (a declared node is not in the tree)
        or ``main_stem_not_a_path`` (the declared nodes are not on one path to the
        root); ``details.node_id`` names the node.
    ValueError
        If ``inflows`` is not a tree below ``root``.
    """
    tree = _Tree(root, inflows, weight)
    forced = _declared_path(tree, main_stem)
    drawing = _Drawing(tree)
    stem = _Placed(0, tree.chain(root, forced), 0, 0, None, None)
    drawing.place(stem, drawing.columns(stem.nodes, 0, slots=2))
    drawing.draw_tributaries(stem)
    return drawing.finish()


def _declared_path(tree: _Tree, declared: Sequence[str]) -> dict[str, str]:
    """Return for each node below the farthest declared node the node it must follow."""
    if not declared:
        return {}
    for node in declared:
        if node not in tree.depth:
            raise InvalidParameterError(
                f"Main stem: the network has no node {node!r}",
                details={"reason": "unknown_node", "node_id": node},
                hint="Name nodes of the network.",
            )
    farthest = max(declared, key=lambda node: (tree.depth[node], node))
    path = tree.path_to_root(farthest)
    on_path = set(path)
    for node in sorted(declared):
        if node not in on_path:
            raise InvalidParameterError(
                f"Main stem: {node!r} is not on the path from {farthest!r} to the "
                f"outlet {tree.root!r}",
                details={
                    "reason": "main_stem_not_a_path",
                    "node_id": node,
                    "other_id": farthest,
                },
                hint="A main stem is one path: name nodes that lie on a single line "
                "from a headwater to the outlet.",
            )
    return {below: above for above, below in zip(path, path[1:], strict=False)}


class _Drawing:
    """The lines drawn so far and the grid that they take."""

    def __init__(self, tree: _Tree) -> None:
        self.tree = tree
        self.grid = _Grid()
        self.x: dict[str, int] = {}
        self.line_of: dict[str, int] = {}
        self.lines: list[_Placed] = []
        self.routes: dict[str, tuple[Point, ...]] = {}
        self.limit = len(tree.nodes) + 4

    # --- the nodes of a line -------------------------------------------------------

    def side_inflows(self, nodes: Sequence[str], position: int) -> list[str]:
        """Return the inflows of a node of a line that are not the line itself."""
        before = nodes[position - 1] if position > 0 else None
        return [up for up in self.tree.inflows[nodes[position]] if up != before]

    def columns(self, nodes: Sequence[str], last: int, slots: int) -> list[int]:
        """Return the ``x`` of the nodes of a line whose last node is at ``last``.

        The nodes are one unit apart, and further apart before a node that needs taps;
        ``slots`` is how many tributaries a node or a tap takes: two on the main stem,
        one above and one below, and one on any other line.
        """
        columns = [last] * len(nodes)
        for position in range(len(nodes) - 1, 0, -1):
            taps = _taps(len(self.side_inflows(nodes, position)), slots)
            columns[position - 1] = columns[position] - 1 - taps
        return columns

    def place(self, line: _Placed, columns: Sequence[int]) -> None:
        """Register a line: its nodes, the stretches between them and their edges."""
        self.lines.append(line)
        owners: list[tuple[Point, object]] = []
        for position, node in enumerate(line.nodes):
            self.x[node] = columns[position]
            self.line_of[node] = line.index
            owners.append(((columns[position], line.row), node))
            if position == 0:
                continue
            before = line.nodes[position - 1]
            owners.extend(
                ((column, line.row), ("tap", node))
                for column in range(columns[position - 1] + 1, columns[position])
            )
            self.routes[before] = (
                (columns[position - 1], line.row),
                (columns[position], line.row),
            )
        self.grid.take(owners, ())

    # --- the tributaries -----------------------------------------------------------

    def joins_of(self, line: _Placed) -> list[_Join]:
        """List the tributaries of a line in the order that they are drawn.

        Headwaters first, so that a tributary downstream passes outside the ones
        upstream of it; at one node the taps come first and the node itself last. On
        the main stem the sides alternate along the list, the first above; every
        other line takes its tributaries on the side that points away from its parent.
        """
        stem = line.parent is None
        slots = 2 if stem else 1
        joins: list[_Join] = []
        for position, node in enumerate(line.nodes):
            sides = self.side_inflows(line.nodes, position)
            groups = [sides[i : i + slots] for i in range(0, len(sides), slots)]
            for tap in range(len(groups) - 1, -1, -1):
                for top in groups[tap]:
                    if stem:
                        side = ABOVE if len(joins) % 2 == 0 else BELOW
                    else:
                        side = line.side
                    joins.append(_Join(line, node, top, tap, side))
        return joins

    def draw_tributaries(self, stem: _Placed) -> None:
        """Draw every tributary of the main stem and of the lines that they start."""
        stack = [iter(self.joins_of(stem))]
        while stack:
            join = next(stack[-1], None)
            if join is None:
                stack.pop()
            else:
                stack.append(iter(self.joins_of(self.draw(join))))

    def draw(self, join: _Join) -> _Placed:
        """Find the place of the tributary of a join, draw it and return its line."""
        nodes = self.tree.chain(join.top)
        for distance in range(1, self.limit + 1):
            if (placed := self.fit(join, nodes, distance)) is not None:
                return placed
        raise AssertionError(  # pragma: no cover - see the module docstring
            f"no place for the line of {join.top!r}"
        )

    def fit(self, join: _Join, nodes: list[str], distance: int) -> _Placed | None:
        """Draw the tributary ``distance`` rows from its parent when all is free."""
        parent = join.line
        side = join.side
        base = parent.row
        row = base + side * distance
        node_x = self.x[join.node]
        tap = node_x - join.tap
        end = tap - 1
        columns = self.columns(nodes, end, slots=1)
        legs = [(end, base + side * step) for step in range(1, distance)]
        cells = [(column, row) for column in range(columns[0], columns[-1] + 1)]
        diagonal = (end, min(base + side, base))
        if not self.grid.free(
            [*cells, *legs],
            [diagonal],
            margins=[(columns[0] - 1, row), (end + 1, row)],
            shared=[(column, base) for column in range(tap, node_x)],
            tap_of=join.node,
        ):
            return None
        placed = _Placed(len(self.lines), nodes, row, side, parent.index, join.node)
        self.place(placed, columns)
        self.grid.take([(leg, ("leg", nodes[-1])) for leg in legs], [diagonal])
        corners = [(end, row)]
        if distance > 1:
            corners.append((end, base + side))
        corners.append((tap, base))
        if join.tap > 0:
            corners.append((node_x, base))
        self.routes[nodes[-1]] = tuple(corners)
        return placed

    # --- the result ----------------------------------------------------------------

    def finish(self) -> Layout:
        """Move the picture to the origin and place the labels."""
        rows = {node: self.lines[self.line_of[node]].row for node in self.tree.nodes}
        left = min(self.x.values())
        top = min(rows.values())
        positions = {
            node: (self.x[node] - left, rows[node] - top) for node in self.tree.nodes
        }
        routes = {
            node: tuple(_straight([(x - left, y - top) for x, y in route]))
            for node, route in self.routes.items()
        }
        lines = tuple(
            Line(line.index, tuple(line.nodes), line.joins, line.parent, line.row - top)
            for line in self.lines
        )
        return Layout(
            positions=positions,
            routes=routes,
            lines=lines,
            line_of=dict(self.line_of),
            labels=_Labels(positions, routes).place(self.tree.nodes),
            width=max(x for x, _ in positions.values()),
            height=max(y for _, y in positions.values()),
        )


def _straight(route: Sequence[Point]) -> list[Point]:
    """Drop the corners that lie on a straight line between their neighbours."""
    kept = [route[0]]
    for index in range(1, len(route) - 1):
        (x0, y0), (x1, y1), (x2, y2) = kept[-1], route[index], route[index + 1]
        if (x1 - x0) * (y2 - y1) != (y1 - y0) * (x2 - x1):
            kept.append(route[index])
    kept.append(route[-1])
    return kept


# --- labels ------------------------------------------------------------------------


def _hits(box: Box, start: Point, end: Point) -> bool:
    """Whether the segment from ``start`` to ``end`` runs through the box."""
    x0, x1, y0, y1 = box
    (ax, ay), (bx, by) = start, end
    low, high = 0.0, 1.0
    for delta, bound_low, bound_high, origin in (
        (bx - ax, x0, x1, ax),
        (by - ay, y0, y1, ay),
    ):
        if delta == 0:
            if not bound_low < origin < bound_high:
                return False
            continue
        entry, leave = (bound_low - origin) / delta, (bound_high - origin) / delta
        if entry > leave:
            entry, leave = leave, entry
        low, high = max(low, entry), min(high, leave)
        if low >= high:
            return False
    return True


def _overlap(first: Box, second: Box) -> bool:
    """Whether two boxes have an area in common."""
    return (
        first[0] < second[1]
        and second[0] < first[1]
        and first[2] < second[3]
        and second[2] < first[3]
    )


def _cells(box: Box) -> list[Point]:
    """Return the cells of the grid that a box can touch, and one more around it."""
    return [
        (x, y)
        for x in range(math.floor(box[0]) - 1, math.floor(box[1]) + 2)
        for y in range(math.floor(box[2]) - 1, math.floor(box[3]) + 2)
    ]


class _Labels:
    """The places of the labels: what a label must keep clear of, and what it took."""

    def __init__(
        self,
        positions: Mapping[str, Point],
        routes: Mapping[str, tuple[Point, ...]],
    ) -> None:
        self.positions = positions
        self.node_at = {point: node for node, point in positions.items()}
        self.segments: list[tuple[Point, Point]] = []
        self.near: dict[Point, list[int]] = {}
        for route in routes.values():
            for start, end in zip(route, route[1:], strict=False):
                number = len(self.segments)
                self.segments.append((start, end))
                for x in range(min(start[0], end[0]), max(start[0], end[0]) + 1):
                    for y in range(min(start[1], end[1]), max(start[1], end[1]) + 1):
                        self.near.setdefault((x, y), []).append(number)
        self.taken: dict[Point, list[Box]] = {}

    def box(self, node: str, side: str) -> Box:
        """Return the box of the label of ``node`` on ``side``."""
        x, y = self.positions[node]
        x0, x1, y0, y1 = _LABEL_BOXES[side]
        return (x + x0, x + x1, y + y0, y + y1)

    def crossings(self, node: str, side: str) -> int:
        """Count the lines and the other nodes that the label would lie on."""
        region = self.box(node, side)
        seen: set[int] = set()
        count = 0
        for cell in _cells(region):
            for number in self.near.get(cell, ()):
                if number not in seen:
                    seen.add(number)
                    count += _hits(region, *self.segments[number])
            other = self.node_at.get(cell)
            if other is not None and other != node:
                x, y = cell
                square = (
                    x - _NODE_CLEARANCE,
                    x + _NODE_CLEARANCE,
                    y - _NODE_CLEARANCE,
                    y + _NODE_CLEARANCE,
                )
                count += _overlap(region, square)
        return count

    def overlaps(self, region: Box) -> int:
        """Count the labels that are placed already and that lie on ``region``."""
        seen: set[Box] = set()
        for cell in _cells(region):
            seen.update(
                other for other in self.taken.get(cell, ()) if _overlap(region, other)
            )
        return len(seen)

    def take(self, region: Box) -> None:
        """Mark ``region`` as taken by a label."""
        for cell in _cells(region):
            self.taken.setdefault(cell, []).append(region)

    def fallback(self, node: str) -> str:
        """Return the place with the fewest lines and labels on it; first if tied."""
        costs = {
            side: self.crossings(node, side) + self.overlaps(self.box(node, side))
            for side in _LABEL_ORDER
        }
        return min(_LABEL_ORDER, key=costs.__getitem__)

    def place(self, nodes: Sequence[str]) -> dict[str, str]:
        """Choose the place of the label of every node.

        A label may not lie on a line, on another node or on another label. Each node
        takes the first place of :data:`_LABEL_ORDER` that is clear, the nodes that
        have the fewest clear places choosing first; a node that has none takes the
        place that lies on the fewest lines and labels.
        """
        clear = {
            node: [side for side in _LABEL_ORDER if self.crossings(node, side) == 0]
            for node in nodes
        }
        labels: dict[str, str] = {}
        for node in sorted(nodes, key=lambda n: (len(clear[n]), self.positions[n], n)):
            chosen = next(
                (s for s in clear[node] if not self.overlaps(self.box(node, s))), None
            )
            if chosen is None:
                chosen = self.fallback(node)
            labels[node] = chosen
            self.take(self.box(node, chosen))
        return labels
