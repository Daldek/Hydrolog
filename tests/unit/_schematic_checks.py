"""An independent check of a picture of a tree, and random trees to draw (ADR-0013).

The check does not use the layout code: it looks only at the cells of the picture. A
picture is right when every segment runs at 0, 45 or 90 degrees, every edge joins its
two nodes and flows to the right, no two nodes share a cell, no edge runs through a
node that it does not join, and no two edges cross or overlap. The one thing that two
edges may share is the last stretch before a node that they both flow into (a merge),
along a horizontal line.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

Point = tuple[int, int]


def unit_steps(route: Sequence[Point]) -> list[tuple[Point, Point]]:
    """Cut a polyline into steps of one grid unit (horizontal, vertical or diagonal)."""
    steps = []
    for (x0, y0), (x1, y1) in zip(route, route[1:], strict=False):
        dx, dy = x1 - x0, y1 - y0
        length = max(abs(dx), abs(dy))
        sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
        for number in range(length):
            steps.append(
                (
                    (x0 + sx * number, y0 + sy * number),
                    (x0 + sx * (number + 1), y0 + sy * (number + 1)),
                )
            )
    return steps


def cells(route: Sequence[Point]) -> set[Point]:
    """Return the grid points that a polyline runs through, its ends included."""
    return {point for step in unit_steps(route) for point in step}


def last_run(route: Sequence[Point]) -> set[Point]:
    """Return the points of the horizontal stretch that a polyline ends with."""
    (x0, y0), (x1, y1) = route[-2], route[-1]
    if y0 != y1:
        return {route[-1]}
    sign = 1 if x1 > x0 else -1
    return {(x, y1) for x in range(x1, x0 - sign, -sign)}


def violations(
    root: str, inflows: Mapping[str, Sequence[str]], drawn: Any
) -> list[str]:
    """Return what is wrong with a picture of a tree; an empty list when it is right."""
    problems: list[str] = []
    positions: Mapping[str, Point] = drawn.positions
    routes: Mapping[str, Sequence[Point]] = drawn.routes
    below = {up: node for node, ups in inflows.items() for up in ups}
    if set(positions) != set(below) | {root}:
        problems.append("the nodes of the picture are not the nodes of the tree")
    if set(routes) != set(below):
        problems.append("an edge is missing or one too many")
    owner: dict[Point, str] = {}
    for node, point in positions.items():
        if point in owner:
            problems.append(f"{node} and {owner[point]} are on one point {point}")
        owner[point] = node
        if not (0 <= point[0] <= drawn.width and 0 <= point[1] <= drawn.height):
            problems.append(f"{node} lies outside the picture")
    for node, route in routes.items():
        if route[0] != positions[node] or route[-1] != positions[below[node]]:
            problems.append(f"the edge of {node} does not join its nodes")
        for start, end in zip(route, route[1:], strict=False):
            dx, dy = end[0] - start[0], end[1] - start[1]
            if (dx, dy) == (0, 0) or not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                problems.append(f"the edge of {node} is not octilinear: {route}")
        for a, b, c in zip(route, route[1:], route[2:], strict=False):
            if (b[0] - a[0]) * (c[1] - b[1]) == (b[1] - a[1]) * (c[0] - b[0]):
                problems.append(f"the edge of {node} has a corner that is straight")
        if route[-1][0] <= route[0][0]:
            problems.append(f"the edge of {node} does not flow to the right")
        for point in cells(route):
            other = owner.get(point)
            if other is not None and other not in (node, below[node]):
                problems.append(f"the edge of {node} runs through {other}")
    problems.extend(_crossings(routes, below))
    problems.extend(_structure(root, positions, drawn))
    return problems


def _crossings(
    routes: Mapping[str, Sequence[Point]], below: Mapping[str, str]
) -> list[str]:
    """Return the places where two edges cross, touch or overlap."""
    problems: list[str] = []
    squares: dict[Point, list[str]] = {}
    for node, route in routes.items():
        for start, end in unit_steps(route):
            if start[0] != end[0] and start[1] != end[1]:
                square = (min(start[0], end[0]), min(start[1], end[1]))
                squares.setdefault(square, []).append(node)
    for square, nodes in squares.items():
        if len(nodes) > 1:
            problems.append(f"diagonals of {nodes} cross in the square {square}")
    points = {node: cells(route) for node, route in routes.items()}
    steps = {
        node: {frozenset(step) for step in unit_steps(route)}
        for node, route in routes.items()
    }
    for first, second in combinations(sorted(routes), 2):
        shared = points[first] & points[second]
        if not shared:
            continue
        allowed = {routes[first][0], routes[first][-1]} & {
            routes[second][0],
            routes[second][-1],
        }
        merge: set[Point] = set()
        if below[first] == below[second]:
            merge = last_run(routes[first]) & last_run(routes[second])
        if shared - allowed - merge:
            problems.append(f"the edges of {first} and {second} touch")
        if any(not step <= merge for step in steps[first] & steps[second]):
            problems.append(f"the edges of {first} and {second} overlap")
    return problems


def _structure(root: str, positions: Mapping[str, Point], drawn: Any) -> list[str]:
    """Return what is wrong with the lines: straight, increasing, the stem on a row."""
    problems: list[str] = []
    for line in drawn.lines:
        rows = {positions[node][1] for node in line.nodes}
        columns = [positions[node][0] for node in line.nodes]
        if len(rows) != 1 or rows != {line.row}:
            problems.append(f"line {line.index} is not straight")
        if any(
            after <= before for before, after in zip(columns, columns[1:], strict=False)
        ):
            problems.append(f"line {line.index} does not flow to the right")
    stem = drawn.lines[0]
    if stem.nodes[-1] != root or stem.joins is not None:
        problems.append("the main stem does not end at the outlet")
    if positions[root][0] != drawn.width:
        problems.append("the outlet is not the rightmost node")
    return problems


def random_tree(
    size: int, seed: int, *, fan_in: int = 3, deep: float = 0.0
) -> tuple[str, dict[str, list[str]]]:
    """Return a random tree of ``size`` nodes below ``OUT``: ``(root, inflows)``.

    No node has more than ``fan_in`` inflows; ``deep`` is the chance that a node is
    hung on the last one made, which makes long lines instead of bushes.
    """
    chance = random.Random(seed)
    inflows: dict[str, list[str]] = {"OUT": []}
    made = ["OUT"]
    for number in range(1, size):
        for _ in range(100):
            node = made[-1] if deep and chance.random() < deep else chance.choice(made)
            if len(inflows[node]) < fan_in:
                break
        name = f"n{number}"
        inflows[node].append(name)
        inflows[name] = []
        made.append(name)
    return "OUT", inflows
