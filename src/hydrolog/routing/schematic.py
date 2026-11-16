"""A schematic of a routing network in the style of a metro map (ADR-0013).

:meth:`RoutingNetwork.schematic <hydrolog.routing.RoutingNetwork.schematic>` computes
the picture once, in the library, so that every consumer draws the same one: Hydrograf
on a map, a report, ``route network --schematic``. The picture is the document
``hydrolog-network-schematic/1``, JSON-native, and :func:`schematic_svg` draws it as
SVG with nothing but the standard library. A consumer that draws it itself needs the
document alone.

The picture follows the rules of :mod:`hydrolog.routing._layout`. When every node of
the network has a position (:attr:`Node.position <hydrolog.routing.Node.position>`) and
no two share a cell, the **given** layout keeps them where they are, moved together so
that the smallest ``x`` and ``y`` are 0, and draws every edge by rule D from the
positions of its two ends (ADR-0023): a picture that a person arranged, which may cross
itself. Otherwise the layout is **computed** (ADR-0013): the **main stem** (from the
outlet up through the branch with the largest drained area, or with the most nodes
when a headwater has no area, or through the nodes that the caller declares) is a
straight horizontal line, the **tributaries** join it and each other at 45 degrees, on
alternating sides, and every segment of every line runs at 0, 45 or 90 degrees. The
nodes are on the integer grid, one unit apart along a line. A network whose nodes have
positions on some nodes only, or two on one cell, is computed with the warning
:class:`~hydrolog._warnings.PositionsIgnored` (code ``positions_ignored``, ``reason``
``partial`` or ``shared_cell``, ``node_id``). The lines are ranked the same way in both
layouts. The layout depends on the network and never on a result, so a network has one
picture whether or not it was routed.

:func:`structure_schematic` lays out the **structure** of a document alone (ADR-0025):
the ids, types and links of its nodes and the areas of its headwaters, checked with the
reasons of the network, whatever values the nodes miss. Its layout is always computed,
and for a document that makes a network it is the computed layout of that network.

The document
------------
``schema``, ``name`` (when the network has one), ``outlet``, ``timestep_min`` (always
for a network; for a structure only when its document gives it), ``has_result``
(whether the nodes carry the values of a result), ``layout`` (``given`` or
``computed``; a document without it is computed), ``structure_only`` (``true`` in the
schematic of a structure alone, whose nodes have empty ``parameters`` and no
``description``; absent otherwise), ``grid`` (``width`` and ``height`` of the picture
in grid units: the nodes have ``0 <= x <= width`` and ``0 <= y <= height``), and three
lists:

``lines``
    The lines of the map, the main stem first (``role`` ``main``; the others are
    ``tributary`` and name the node of their parent line that they flow into,
    ``joins``). ``index`` is the number that the nodes and the edges give as their
    ``line``, and ``nodes`` the ids from the head of the line to its last node.
``nodes``
    In the order of evaluation (headwaters first): ``id``, ``type`` (the kind of the
    node: ``subcatchment``, ``reach``, ``reservoir``, ``junction``, ``outlet``, or a
    kind that was added), ``x`` and ``y`` (grid units: ``x`` grows downstream, to the
    right, and ``y`` downwards, as on a screen), ``line``, ``label`` (``text`` and
    ``side``: where the label goes, as a compass point on the screen around the node,
    ``n`` above it and ``e`` to its right; a label is at most one unit wide and four
    tenths of a unit high, so the labels of nodes in neighbouring rows do not overlap)
    and, when the node has one, its ``description`` (plain text for people, which a
    drawing shows as text and never as markup), then ``parameters``, the values of
    the calculation of the node
    (:meth:`Node.describe <hydrolog.routing.Node.describe>`: ``name``, ``value``,
    ``unit``, ``source``). With a result every node also has ``peak_m3s``,
    ``time_to_peak_min`` and ``volume_m3`` of the hydrograph that leaves it, the
    ``parameters`` that the run used (the derived ones too) and its ``notices``
    (``level``, ``code``, ``message``): exactly the values of
    :class:`~hydrolog.routing.NetworkResult`.
``edges``
    One per node but the outlet, from the node to the node it flows into: ``from``,
    ``to``, ``line`` (that of ``from``) and ``points``, the corners of the polyline
    from the position of ``from`` to that of ``to`` (a list of ``[x, y]``). In a
    computed layout no two edges cross or touch except at a node they both end at, and
    the edges that flow into a node that has more than two inflows run along the line
    before it for their last stretch and share that stretch.

Examples
--------
>>> from hydrolog.routing import (
...     Channel, Hydrograph, Junction, LagReach, Outlet, RoutingNetwork, Subcatchment
... )
>>> flood = Hydrograph.from_step([1.0, 4.0, 1.0], timestep_min=10.0)
>>> heads = [Subcatchment("A", flood), Subcatchment("B", flood)]
>>> reach = Channel("R", LagReach(10.0), inflow=Junction("J", inflows=heads))
>>> network = RoutingNetwork(Outlet("OUT", inflow=reach))
>>> document = network.schematic(network.route())
>>> [(node["id"], node["x"], node["y"]) for node in document["nodes"]]
[('A', 0, 1), ('B', 0, 0), ('J', 1, 1), ('R', 2, 1), ('OUT', 3, 1)]
>>> schematic_svg(document).startswith("<svg")
True
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Final

from hydrolog._serialization import to_jsonable
from hydrolog._warnings import PositionsIgnored
from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._layout import Layout, Point, given_layout, layout
from hydrolog.routing._svg import schematic_svg
from hydrolog.routing.document import NetworkStructure, read_structure

if TYPE_CHECKING:
    from hydrolog.routing.network import NetworkResult, RoutingNetwork

__all__ = ["SCHEMA", "network_schematic", "schematic_svg", "structure_schematic"]

SCHEMA: Final = "hydrolog-network-schematic/1"
"""Value of the ``schema`` key of the document."""


def _weights(network: RoutingNetwork) -> dict[str, float] | None:
    """Return the area that each node brings, when every headwater has an area.

    The area of a subcatchment is the one of its watershed. When a headwater has none
    (it is given its hydrograph), the areas say nothing about the branches that it
    heads and the layout counts nodes instead.
    """
    weights: dict[str, float] = {}
    for node in network.nodes:
        if node.inflows:
            continue
        watershed = getattr(node, "watershed", None)
        if watershed is None:
            return None
        weights[node.id] = float(watershed.area_km2)
    return weights


def _declared(main_stem: str | Sequence[str] | None) -> list[str]:
    """Return the declared main stem as a list of ids."""
    if main_stem is None:
        return []
    if isinstance(main_stem, str):
        return [main_stem]
    if not all(isinstance(item, str) for item in main_stem):
        raise InvalidParameterError(
            "The main stem is a node id or a list of node ids",
            details={"reason": "type", "field": "main_stem"},
        )
    return list(main_stem)


def _check_result(network: RoutingNetwork, result: NetworkResult) -> None:
    """Refuse a result that is not the result of this network."""
    if result.outlet != network.outlet or set(result.nodes) != set(network.order):
        raise InvalidParameterError(
            "The result is not the result of this network: its nodes are not the "
            "nodes of the network",
            details={"reason": "result_mismatch", "field": "result"},
            hint="Pass the result of network.route() of the same network.",
        )


def _given(network: RoutingNetwork) -> dict[str, Point] | None:
    """Return the cells of the nodes when the network is drawn where they are.

    Every node needs a position and a cell of its own. A network in which no node has
    one is laid out without a word; otherwise the first node at fault in the order of
    evaluation, one without a position (``partial``) or on the cell of a node before it
    (``shared_cell``), is named by the warning ``positions_ignored``, and the layout is
    computed.
    """
    nodes = network.nodes
    if all(node.position is None for node in nodes):
        return None
    cells: dict[Point, str] = {}
    for node in nodes:
        if node.position is None:
            reason = "partial"
        elif (node.position.x, node.position.y) in cells:
            reason = "shared_cell"
        else:
            cells[(node.position.x, node.position.y)] = node.id
            continue
        warnings.warn(PositionsIgnored(reason=reason, node_id=node.id), stacklevel=4)
        return None
    return {node_id: cell for cell, node_id in cells.items()}


def _placed(node_id: str, kind: str, drawn: Layout) -> dict[str, Any]:
    """Return the start of a node's entry: its id, type, cell, line and label."""
    x, y = drawn.positions[node_id]
    return {
        "id": node_id,
        "type": kind,
        "x": x,
        "y": y,
        "line": drawn.line_of[node_id],
        "label": {"text": node_id, "side": drawn.labels[node_id]},
    }


def _node_entries(
    network: RoutingNetwork, drawn: Layout, result: NetworkResult | None
) -> list[dict[str, Any]]:
    """Return the entries of ``nodes`` of the document."""
    entries: list[dict[str, Any]] = []
    for node in network.nodes:
        entry = _placed(node.id, node.kind, drawn)
        if node.description is not None:
            entry["description"] = node.description
        if result is None:
            entry["parameters"] = node.describe()
        else:
            summary = result.nodes[node.id]
            entry["parameters"] = summary.parameters
            entry["peak_m3s"] = summary.peak_m3s
            entry["time_to_peak_min"] = summary.time_to_peak_min
            entry["volume_m3"] = summary.volume_m3
            entry["notices"] = [
                {"level": item.level, "code": item.code, "message": item.message}
                for item in summary.notices
            ]
        entries.append(entry)
    return entries


def _lines(drawn: Layout) -> list[dict[str, Any]]:
    """Return the entries of ``lines`` of the document."""
    return [
        {
            "index": line.index,
            "role": "main" if line.parent is None else "tributary",
            "nodes": list(line.nodes),
            **({} if line.joins is None else {"joins": line.joins}),
        }
        for line in drawn.lines
    ]


def _edges(
    order: Sequence[str],
    outlet: str,
    inflows: Mapping[str, Sequence[str]],
    drawn: Layout,
) -> list[dict[str, Any]]:
    """Return the entries of ``edges`` of the document, in the order of evaluation."""
    downstream = {up: node for node, ups in inflows.items() for up in ups}
    return [
        {
            "from": node_id,
            "to": downstream[node_id],
            "line": drawn.line_of[node_id],
            "points": [list(point) for point in drawn.routes[node_id]],
        }
        for node_id in order
        if node_id != outlet
    ]


def network_schematic(
    network: RoutingNetwork,
    result: NetworkResult | None = None,
    *,
    main_stem: str | Sequence[str] | None = None,
) -> dict[str, Any]:
    """Return the schematic of a network as a ``hydrolog-network-schematic/1`` document.

    Parameters
    ----------
    network : RoutingNetwork
        The network to draw.
    result : NetworkResult, optional
        The result of ``network.route()``: the nodes then carry its peak, time to peak,
        volume, parameters and notices. Without it they carry the parameters that are
        given. The layout is the same either way.
    main_stem : str or sequence of str, optional
        The ids of nodes that the main stem must pass, for example the head of the main
        river (a headwater) or the points along it. They must lie on one path to the
        outlet; the stem follows that path and, above its farthest node, the branch
        with the larger area (or more nodes). Without it the stem follows the larger
        branch at every node, from the outlet. It ranks the lines of a given layout
        too.

    Returns
    -------
    dict
        The document (see the module docstring), JSON-native: ``layout`` ``given``
        when every node has a position and a cell of its own, else ``computed``.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``result_mismatch`` (``result`` is not the result of
        this network), ``unknown_node`` or ``main_stem_not_a_path``
        (``details.node_id``), or ``type`` (``main_stem`` is not a string or a list of
        strings).

    Warns
    -----
    PositionsIgnored
        When some nodes have positions and another has none (``reason`` ``partial``)
        or two nodes share a cell (``shared_cell``); the layout is then computed.
    """
    if result is not None:
        _check_result(network, result)
    inflows = {node.id: node.upstream for node in network.nodes}
    declared = _declared(main_stem)
    weight = _weights(network)
    given = _given(network)
    drawn = (
        layout(network.outlet, inflows, weight=weight, main_stem=declared)
        if given is None
        else given_layout(
            network.outlet, inflows, given, weight=weight, main_stem=declared
        )
    )
    document: dict[str, Any] = {"schema": SCHEMA}
    if network.name is not None:
        document["name"] = network.name
    document.update(
        outlet=network.outlet,
        timestep_min=network.timestep_min,
        has_result=result is not None,
        layout="computed" if given is None else "given",
        grid={"width": drawn.width, "height": drawn.height},
        lines=_lines(drawn),
        nodes=_node_entries(network, drawn, result),
        edges=_edges(network.order, network.outlet, inflows, drawn),
    )
    converted: dict[str, Any] = to_jsonable(document)
    return converted


def schematic_of(
    structure: NetworkStructure, *, main_stem: str | Sequence[str] | None = None
) -> dict[str, Any]:
    """Return the schematic of a structure that :func:`read_structure` read.

    The document of :func:`structure_schematic`, for a structure already read (the
    command ``route schematic`` reads it first, to tell the errors of the document
    from those of ``main_stem``).

    Parameters
    ----------
    structure : NetworkStructure
        The structure (:func:`~hydrolog.routing.document.read_structure`).
    main_stem : str or sequence of str, optional
        As for :func:`structure_schematic`.

    Returns
    -------
    dict
        The document, JSON-native.

    Raises
    ------
    InvalidParameterError
        As :func:`structure_schematic`, for ``main_stem``.
    """
    drawn = layout(
        structure.outlet,
        structure.upstream,
        weight=structure.areas,
        main_stem=_declared(main_stem),
    )
    document: dict[str, Any] = {"schema": SCHEMA}
    if structure.name is not None:
        document["name"] = structure.name
    document["outlet"] = structure.outlet
    if structure.timestep_min is not None:
        document["timestep_min"] = structure.timestep_min
    document.update(
        has_result=False,
        layout="computed",
        structure_only=True,
        grid={"width": drawn.width, "height": drawn.height},
        lines=_lines(drawn),
        nodes=[
            {**_placed(node_id, structure.kinds[node_id], drawn), "parameters": []}
            for node_id in structure.order
        ],
        edges=_edges(structure.order, structure.outlet, structure.upstream, drawn),
    )
    converted: dict[str, Any] = to_jsonable(document)
    return converted


def structure_schematic(
    document: Mapping[str, Any], *, main_stem: str | Sequence[str] | None = None
) -> dict[str, Any]:
    """Return the schematic of the structure of a network document (ADR-0025).

    The layout of a draft: of the document ``hydrolog-network/1`` only ``schema``,
    ``name``, ``timestep_min``, each node's ``id``, ``type`` and ``from`` and each
    headwater's ``watershed.area_km2`` are read
    (:func:`~hydrolog.routing.document.read_structure`), and the structure is checked
    with the reasons of the network; any other field may be missing or wrong. The
    layout is always computed (ADR-0013), whatever positions the nodes have. For a
    document that :meth:`RoutingNetwork.from_document
    <hydrolog.routing.RoutingNetwork.from_document>` reads, the nodes, lines, edges,
    labels and grid are those of the computed layout of :meth:`RoutingNetwork.schematic
    <hydrolog.routing.RoutingNetwork.schematic>` with the same ``main_stem``.

    Parameters
    ----------
    document : mapping
        The document ``hydrolog-network/1``, which may be a draft; values are
        JSON-native.
    main_stem : str or sequence of str, optional
        The ids of nodes that the main stem must pass, as for
        :meth:`RoutingNetwork.schematic <hydrolog.routing.RoutingNetwork.schematic>`.

    Returns
    -------
    dict
        The document ``hydrolog-network-schematic/1``, JSON-native, with
        ``structure_only`` ``true`` after ``layout`` (``computed``), ``has_result``
        ``false``, every node's ``parameters`` empty and no node ``description``;
        ``name`` and ``timestep_min`` only when the document gives a non-blank name and
        a positive step.

    Raises
    ------
    InvalidParameterError
        If the structure is wrong, with the reasons of
        :func:`~hydrolog.routing.document.read_structure` and ``details.node_id``;
        with ``details.reason`` ``unknown_node`` or ``main_stem_not_a_path``
        (``details.node_id``), or ``type`` (``main_stem`` is not a string or a list of
        strings).

    Examples
    --------
    >>> draft = {"schema": "hydrolog-network/1", "nodes": [
    ...     {"id": "A", "type": "subcatchment"},
    ...     {"id": "B", "type": "subcatchment"},
    ...     {"id": "J", "type": "junction", "from": ["A", "B"]},
    ...     {"id": "OUT", "type": "outlet", "from": ["J"]}]}
    >>> drawn = structure_schematic(draft)
    >>> drawn["structure_only"], [(n["id"], n["x"], n["y"]) for n in drawn["nodes"]]
    (True, [('A', 0, 1), ('B', 0, 0), ('J', 1, 1), ('OUT', 2, 1)])
    """
    return schematic_of(read_structure(document), main_stem=main_stem)
