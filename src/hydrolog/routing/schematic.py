"""A schematic of a routing network in the style of a metro map (ADR-0013).

:meth:`RoutingNetwork.schematic <hydrolog.routing.RoutingNetwork.schematic>` computes
the picture once, in the library, so that every consumer draws the same one: Hydrograf
on a map, a report, ``route network --schematic``. The picture is the document
``hydrolog-network-schematic/1``, JSON-native, and :func:`schematic_svg` draws it as
SVG with nothing but the standard library. A consumer that draws it itself needs the
document alone.

The picture follows the rules of :mod:`hydrolog.routing._layout`: the **main stem**
(from the outlet up through the branch with the largest drained area, or with the most
nodes when a headwater has no area, or through the nodes that the caller declares) is a
straight horizontal line, the **tributaries** join it and each other at 45 degrees, on
alternating sides, and every segment of every line runs at 0, 45 or 90 degrees. The
nodes are on the integer grid, one unit apart along a line. The layout depends on the
network and never on a result, so a network has one picture whether or not it was
routed.

The document
------------
``schema``, ``name`` (when the network has one), ``outlet``, ``timestep_min``,
``has_result`` (whether the nodes carry the values of a result), ``grid`` (``width``
and ``height`` of the picture in grid units: the nodes have ``0 <= x <= width`` and
``0 <= y <= height``), and three lists:

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
    and ``parameters``, the values of the calculation of the node
    (:meth:`Node.describe <hydrolog.routing.Node.describe>`: ``name``, ``value``,
    ``unit``, ``source``). With a result every node also has ``peak_m3s``,
    ``time_to_peak_min`` and ``volume_m3`` of the hydrograph that leaves it, the
    ``parameters`` that the run used (the derived ones too) and its ``notices``
    (``level``, ``code``, ``message``): exactly the values of
    :class:`~hydrolog.routing.NetworkResult`.
``edges``
    One per node but the outlet, from the node to the node it flows into: ``from``,
    ``to``, ``line`` (that of ``from``) and ``points``, the corners of the polyline
    from the position of ``from`` to that of ``to`` (a list of ``[x, y]``). No two
    edges cross or touch except at a node they both end at; the edges that flow into a
    node that has more than two inflows run along the line before it for their last
    stretch and share that stretch.

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

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Final

from hydrolog._serialization import to_jsonable
from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._layout import Layout, layout
from hydrolog.routing._svg import schematic_svg

if TYPE_CHECKING:
    from hydrolog.routing.network import NetworkResult, RoutingNetwork

__all__ = ["SCHEMA", "network_schematic", "schematic_svg"]

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


def _node_entries(
    network: RoutingNetwork, drawn: Layout, result: NetworkResult | None
) -> list[dict[str, Any]]:
    """Return the entries of ``nodes`` of the document."""
    entries: list[dict[str, Any]] = []
    for node in network.nodes:
        x, y = drawn.positions[node.id]
        entry: dict[str, Any] = {
            "id": node.id,
            "type": node.kind,
            "x": x,
            "y": y,
            "line": drawn.line_of[node.id],
            "label": {"text": node.id, "side": drawn.labels[node.id]},
        }
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
        branch at every node, from the outlet.

    Returns
    -------
    dict
        The document (see the module docstring), JSON-native.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``result_mismatch`` (``result`` is not the result of
        this network), ``unknown_node`` or ``main_stem_not_a_path``
        (``details.node_id``), or ``type`` (``main_stem`` is not a string or a list of
        strings).
    """
    if result is not None:
        _check_result(network, result)
    inflows = {node.id: node.upstream for node in network.nodes}
    drawn = layout(
        network.outlet,
        inflows,
        weight=_weights(network),
        main_stem=_declared(main_stem),
    )
    downstream = {up: node for node, ups in inflows.items() for up in ups}
    edges = [
        {
            "from": node.id,
            "to": downstream[node.id],
            "line": drawn.line_of[node.id],
            "points": [list(point) for point in drawn.routes[node.id]],
        }
        for node in network.nodes
        if node.id != network.outlet
    ]
    document: dict[str, Any] = {"schema": SCHEMA}
    if network.name is not None:
        document["name"] = network.name
    document.update(
        outlet=network.outlet,
        timestep_min=network.timestep_min,
        has_result=result is not None,
        grid={"width": drawn.width, "height": drawn.height},
        lines=[
            {
                "index": line.index,
                "role": "main" if line.parent is None else "tributary",
                "nodes": list(line.nodes),
                **({} if line.joins is None else {"joins": line.joins}),
            }
            for line in drawn.lines
        ],
        nodes=_node_entries(network, drawn, result),
        edges=edges,
    )
    converted: dict[str, Any] = to_jsonable(document)
    return converted
