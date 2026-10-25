"""Routing over a river network: a directed acyclic graph of routing elements.

A :class:`RoutingNetwork` composes the elements of this package along a stream. Each
node names the nodes that flow into it (``upstream``, the convention of
``StreamSegment.upstream_ids``), and water flows from node to node:

==============  ===========  ==========================================================
kind            upstream     what the node does
==============  ===========  ==========================================================
subcatchment    none         brings a source hydrograph into the network
reach           one          routes its upstream hydrograph through any :class:`Reach`
reservoir       one          the same, with a :class:`LevelPoolReach`
junction        one or more  adds the hydrographs that flow into it
outlet          one          the end of the network; its hydrograph is the result
==============  ===========  ==========================================================

The network is checked when it is made (:class:`RoutingNetwork`), with the vocabulary of
:class:`~hydrolog.network.StreamNetwork`: an id that is listed but not in the network
(``unknown_upstream``) and a cycle (``cycle``, the nodes in flow order) are errors, and
so are the shapes that a lumped model cannot route: a node that flows into two nodes
(``several_downstream``: a bifurcation would count its water twice), no outlet or two
(``no_outlet``, ``several_outlets``), an outlet that something flows out of
(``outlet_has_downstream``) and a node that does not reach the outlet
(``disconnected_node``). The nodes are evaluated headwaters first, and among the nodes
that are ready the smallest id first, so neither the order of the nodes in the list nor
in a file changes anything.

**Time axes.** One time step for the whole network: the source hydrographs must have the
same step and the same first time (``timestep_mismatch``, ``start_mismatch``); nothing
is resampled (ADR-0008). Their lengths may differ, and so do the lengths of the
hydrographs that come out of the reaches, which are extended until the outflow has
settled: where hydrographs of different lengths meet in a junction, the shorter ones are
held at their last value, as the inflow of a reach is held over its extension.

Examples
--------
Two tributaries joining above a reach:

>>> from hydrolog.routing import Hydrograph, LagReach
>>> from hydrolog.routing.network import NetworkNode, RoutingNetwork
>>> small = Hydrograph.from_step([1.0, 4.0, 1.0], timestep_min=10.0)
>>> large = Hydrograph.from_step([2.0, 8.0, 2.0], timestep_min=10.0)
>>> network = RoutingNetwork(
...     [
...         NetworkNode("A", "subcatchment", hydrograph=small),
...         NetworkNode("B", "subcatchment", hydrograph=large),
...         NetworkNode("J", "junction", upstream=["A", "B"]),
...         NetworkNode("R", "reach", upstream=["J"], reach=LagReach(lag_min=10.0)),
...         NetworkNode("OUT", "outlet", upstream=["R"]),
...     ]
... )
>>> network.order
('A', 'B', 'J', 'R', 'OUT')
>>> network.route().hydrographs["OUT"].peak_discharge_m3s
12.0
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.network._graph import UnknownUpstream, UpstreamCycle, upstream_first
from hydrolog.routing.hydrograph import STEP_TOLERANCE, Hydrograph
from hydrolog.routing.level_pool import LevelPoolReach
from hydrolog.routing.reach import Reach, RoutingResult

__all__ = [
    "MAX_ID_CHARS",
    "NODE_KINDS",
    "NetworkNode",
    "NetworkResult",
    "RoutingNetwork",
]

NodeKind = Literal["subcatchment", "reach", "reservoir", "junction", "outlet"]

NODE_KINDS: Final[tuple[str, ...]] = (
    "subcatchment",
    "reach",
    "reservoir",
    "junction",
    "outlet",
)
"""The kinds of node, in the order of a stream: source, channel, pool, sum, end."""
MAX_ID_CHARS: Final = 64
"""Longest node id; an id names the file of its node (``<id>.csv``)."""

_ID = re.compile(r"\w[\w.-]*")
_UPSTREAM_COUNT: Final[dict[str, tuple[int, int | None, str]]] = {
    "subcatchment": (0, 0, "no upstream node"),
    "reach": (1, 1, "exactly one upstream node"),
    "reservoir": (1, 1, "exactly one upstream node"),
    "junction": (1, None, "at least one upstream node"),
    "outlet": (1, 1, "exactly one upstream node"),
}
_PAYLOAD: Final[dict[str, tuple[frozenset[str], frozenset[str]]]] = {
    # kind: (fields the node must have, fields the node may have)
    "subcatchment": (frozenset({"hydrograph"}), frozenset({"hydrograph"})),
    "reach": (
        frozenset({"reach"}),
        frozenset({"reach", "initial_outflow_m3s", "extend_min"}),
    ),
    "reservoir": (
        frozenset({"reach"}),
        frozenset({"reach", "initial_outflow_m3s", "extend_min"}),
    ),
    "junction": (frozenset(), frozenset()),
    "outlet": (frozenset(), frozenset()),
}


def _check_id(value: object, *, role: str = "id") -> str:
    """Return ``value`` when it can be a node id: it names a file, so it is plain."""
    if (
        not isinstance(value, str)
        or len(value) > MAX_ID_CHARS
        or _ID.fullmatch(value) is None
        or value.endswith(".")
    ):
        shown = value if isinstance(value, str) else repr(value)
        raise InvalidParameterError(
            f"Node {role} {shown[:MAX_ID_CHARS]!r} is not valid",
            details={"reason": "invalid_id", "node_id": shown[:MAX_ID_CHARS]},
            hint=(
                "An id starts with a letter, a digit or an underscore, goes on with "
                "letters, digits, underscores, dots and hyphens, does not end with a "
                f"dot and has at most {MAX_ID_CHARS} characters: the file of the node "
                "is named after it."
            ),
        )
    return value


@dataclass(frozen=True)
class NetworkNode:
    """One node of a :class:`RoutingNetwork`.

    Parameters
    ----------
    id : str
        The name of the node, unique in the network without regard to case; it names
        the file of the node, so it is plain: letters, digits, ``_``, ``.`` and ``-``,
        at most :data:`MAX_ID_CHARS` characters.
    kind : {"subcatchment", "reach", "reservoir", "junction", "outlet"}
        What the node does (see the module docstring).
    upstream : sequence of str, optional
        The ids of the nodes that flow into this one: none for a ``subcatchment``,
        one for a ``reach``, a ``reservoir`` and the ``outlet``, at least one for a
        ``junction``; no id twice.
    hydrograph : Hydrograph, optional
        The source hydrograph of a ``subcatchment``.
    reach : Reach, optional
        The element a ``reach`` routes with; a :class:`LevelPoolReach` for a
        ``reservoir``.
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s] of a ``reach`` or ``reservoir``; default
        its first inflow ordinate (:meth:`Reach.route`).
    extend_min : float, optional
        Time added after the last inflow ordinate [min] of a ``reach`` or
        ``reservoir``; default until the outflow has settled (:meth:`Reach.route`).

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``invalid_id``, ``unknown_type``, ``upstream_count``,
        ``duplicate_upstream``, ``missing_field`` or ``unexpected_field`` (and
        ``details.node_id``).
    """

    id: str
    kind: NodeKind
    upstream: Sequence[str] = ()
    hydrograph: Hydrograph | None = None
    reach: Reach | None = None
    initial_outflow_m3s: float | None = None
    extend_min: float | None = None

    def __post_init__(self) -> None:
        """Check the node on its own."""
        _check_id(self.id)
        if self.kind not in NODE_KINDS:
            raise InvalidParameterError(
                f"Node {self.id!r} has the unknown type {self.kind!r}",
                details={
                    "reason": "unknown_type",
                    "node_id": self.id,
                    "value": str(self.kind),
                    "allowed": list(NODE_KINDS),
                },
                hint=f"The types are {', '.join(NODE_KINDS)}.",
            )
        upstream = tuple(self.upstream)
        for listed in upstream:
            _check_id(listed, role="upstream id")
        object.__setattr__(self, "upstream", upstream)
        low, high, rule = _UPSTREAM_COUNT[self.kind]
        if len(upstream) < low or (high is not None and len(upstream) > high):
            raise InvalidParameterError(
                f"Node {self.id!r} is a {self.kind} and takes {rule}, but lists "
                f"{len(upstream)}",
                details={
                    "reason": "upstream_count",
                    "node_id": self.id,
                    "type": self.kind,
                    "found": len(upstream),
                },
                hint=f"A {self.kind} takes {rule}.",
            )
        if len(set(upstream)) != len(upstream):
            raise InvalidParameterError(
                f"Node {self.id!r} lists an upstream node twice: its water would be "
                "counted twice",
                details={"reason": "duplicate_upstream", "node_id": self.id},
            )
        needed, allowed = _PAYLOAD[self.kind]
        given = {
            name
            for name in (
                "hydrograph",
                "reach",
                "initial_outflow_m3s",
                "extend_min",
            )
            if getattr(self, name) is not None
        }
        for name in sorted(needed - given):
            raise InvalidParameterError(
                f"Node {self.id!r} is a {self.kind} and needs {name!r}",
                details={"reason": "missing_field", "node_id": self.id, "field": name},
            )
        for name in sorted(given - allowed):
            raise InvalidParameterError(
                f"Node {self.id!r} is a {self.kind} and takes no {name!r}",
                details={
                    "reason": "unexpected_field",
                    "node_id": self.id,
                    "field": name,
                },
            )
        if self.kind == "reservoir" and not isinstance(self.reach, LevelPoolReach):
            raise InvalidParameterError(
                f"Node {self.id!r} is a reservoir and routes with a LevelPoolReach",
                details={
                    "reason": "reservoir_model",
                    "node_id": self.id,
                    "model": type(self.reach).__name__,
                },
                hint="A reach with another model is a node of type reach.",
            )


@dataclass
class NetworkResult(JsonResultMixin):
    """The outcome of routing a network.

    Attributes
    ----------
    name : str or None
        The name of the network.
    order : tuple of str
        The ids in the order they were evaluated: headwaters first.
    outlet : str
        The id of the outlet node.
    timestep_min : float
        The time step of every hydrograph [min].
    hydrographs : dict of str to Hydrograph
        The hydrograph that leaves each node: the source of a ``subcatchment``, the
        outflow of a ``reach`` or ``reservoir`` (extended until it settled), the sum
        of a ``junction`` and, for the ``outlet``, the hydrograph that reaches it.
    runs : dict of str to RoutingResult
        The result of each ``reach`` and ``reservoir``: parameters, storage at both
        ends, volume balance and notices.
    """

    name: str | None
    order: tuple[str, ...]
    outlet: str
    timestep_min: float
    hydrographs: dict[str, Hydrograph]
    runs: dict[str, RoutingResult]


def _sum(hydrographs: Sequence[Hydrograph]) -> Hydrograph:
    """Add hydrographs on one time axis; shorter ones are held at their last value."""
    longest = max(hydrographs, key=len)
    total = np.zeros(len(longest))
    for hydrograph in hydrographs:
        total += hydrograph.extended(len(longest) - len(hydrograph)).discharge_m3s
    return Hydrograph(longest.times_min, total)


class RoutingNetwork:
    """A directed acyclic network of routing elements, ready to route.

    Parameters
    ----------
    nodes : iterable of NetworkNode
        The nodes, in any order.
    name : str, optional
        A name for the network, reported in the result.

    Attributes
    ----------
    name : str or None
        The name of the network.
    order : tuple of str
        The ids in the order of evaluation: headwaters first, the smallest id first
        among the nodes that are ready, whatever the order of ``nodes``.
    outlet : str
        The id of the outlet.
    timestep_min : float
        The time step of the source hydrographs [min].

    Raises
    ------
    InvalidParameterError
        If the nodes do not make a network. ``details.reason`` and the facts that come
        with it: ``empty``; ``duplicate_node`` (``node_id``, ``other_id``: two ids
        equal without regard to case); ``unknown_upstream`` (``node_id``,
        ``upstream_id``, ``n_unknown``); ``cycle`` (``nodes`` in flow order);
        ``several_downstream`` (``node_id``, ``downstream``); ``no_outlet``;
        ``several_outlets`` (``nodes``); ``outlet_has_downstream`` (``node_id``,
        ``downstream``); ``disconnected_node`` (``node_id``: a node that feeds nothing
        and is not the outlet, ``n_disconnected``: the nodes that do not reach the
        outlet); ``timestep_mismatch`` and ``start_mismatch`` (``nodes``, and
        ``timesteps_min`` or ``starts_min``).
    """

    def __init__(self, nodes: Iterable[NetworkNode], name: str | None = None) -> None:
        """Check the network and put the nodes in the order of evaluation."""
        listed = list(nodes)
        if not listed:
            raise InvalidParameterError(
                "A network needs at least one node",
                details={"reason": "empty"},
            )
        by_id: dict[str, NetworkNode] = {}
        folded: dict[str, str] = {}
        for node in listed:
            earlier = folded.get(node.id.casefold())
            if earlier is not None:
                raise InvalidParameterError(
                    f"Node {node.id!r} repeats the id of node {earlier!r} (ids are "
                    "compared without regard to case)",
                    details={
                        "reason": "duplicate_node",
                        "node_id": node.id,
                        "other_id": earlier,
                    },
                    hint="Every node needs its own id: it names the file of the node.",
                )
            folded[node.id.casefold()] = node.id
            by_id[node.id] = node
        try:
            order = upstream_first(
                {node_id: node.upstream for node_id, node in by_id.items()}
            )
        except UnknownUpstream as unknown:
            raise InvalidParameterError(
                f"Node {unknown.key!r} lists upstream node {unknown.upstream!r}, "
                "which is not in the network",
                details={
                    "reason": "unknown_upstream",
                    "node_id": unknown.key,
                    "upstream_id": unknown.upstream,
                    "n_unknown": unknown.count,
                },
                hint="Every id in `from` must be the id of a node of the network.",
            ) from unknown
        except UpstreamCycle as looped:
            members = [str(member) for member in looped.members]
            if len(members) == 1:
                message = f"Node {members[0]!r} lists itself as upstream"
            else:
                chain = " -> ".join(repr(member) for member in [*members, members[0]])
                message = f"The nodes form a cycle: {chain}"
            raise InvalidParameterError(
                message,
                details={"reason": "cycle", "nodes": members},
                hint="Water flows from a node into each node that lists it; remove "
                "the link that closes the loop.",
            ) from looped
        self.name = name
        self._nodes: dict[str, NetworkNode] = {
            node_id: by_id[node_id] for node_id in order
        }
        self.order: tuple[str, ...] = tuple(order)
        self.outlet = self._check_shape()
        self.timestep_min = self._check_time_axes()

    @property
    def nodes(self) -> tuple[NetworkNode, ...]:
        """Tuple of NetworkNode: the nodes in the order of evaluation."""
        return tuple(self._nodes.values())

    def node(self, node_id: str) -> NetworkNode:
        """Return the node called ``node_id``.

        Parameters
        ----------
        node_id : str
            The id of a node of the network.

        Returns
        -------
        NetworkNode
            The node.

        Raises
        ------
        KeyError
            If the network has no such node.
        """
        return self._nodes[node_id]

    def _check_shape(self) -> str:
        """Check what a lumped model needs of a network and return the outlet's id."""
        downstream: dict[str, list[str]] = {node_id: [] for node_id in self._nodes}
        for node in self._nodes.values():
            for listed in node.upstream:
                downstream[listed].append(node.id)
        for node_id, receivers in downstream.items():
            if len(receivers) > 1:
                raise InvalidParameterError(
                    f"Node {node_id!r} flows into {len(receivers)} nodes "
                    f"({', '.join(map(repr, receivers))}): a bifurcation would count "
                    "its water twice",
                    details={
                        "reason": "several_downstream",
                        "node_id": node_id,
                        "downstream": receivers,
                    },
                    hint="A node flows into one node; bifurcations are not routed.",
                )
        outlets = [n.id for n in self._nodes.values() if n.kind == "outlet"]
        if not outlets:
            raise InvalidParameterError(
                "The network has no outlet",
                details={"reason": "no_outlet"},
                hint="Add a node of type outlet that lists the last node.",
            )
        if len(outlets) > 1:
            raise InvalidParameterError(
                f"The network has {len(outlets)} outlets "
                f"({', '.join(map(repr, outlets))}), it needs one",
                details={"reason": "several_outlets", "nodes": outlets},
                hint="Join the streams in a junction above a single outlet.",
            )
        outlet = outlets[0]
        if downstream[outlet]:
            raise InvalidParameterError(
                f"The outlet {outlet!r} is listed as upstream by "
                f"{', '.join(map(repr, downstream[outlet]))}",
                details={
                    "reason": "outlet_has_downstream",
                    "node_id": outlet,
                    "downstream": downstream[outlet],
                },
                hint="Nothing flows out of the outlet.",
            )
        reached = {outlet}
        pending = [outlet]
        while pending:
            for listed in self._nodes[pending.pop()].upstream:
                if listed not in reached:
                    reached.add(listed)
                    pending.append(listed)
        disconnected = [node_id for node_id in self._nodes if node_id not in reached]
        if disconnected:
            # every node that does not reach the outlet ends in a node that feeds
            # nothing and is not the outlet: that is the one to name
            dead_end = next(
                node_id for node_id in disconnected if not downstream[node_id]
            )
            raise InvalidParameterError(
                f"Node {dead_end!r} flows nowhere: it is not listed by any node and is "
                f"not the outlet ({len(disconnected)} nodes do not reach the outlet "
                f"{outlet!r})",
                details={
                    "reason": "disconnected_node",
                    "node_id": dead_end,
                    "n_disconnected": len(disconnected),
                },
                hint="List the node in the `from` of the node it flows into.",
            )
        return outlet

    def _check_time_axes(self) -> float:
        """Check that the sources share one time axis and return its step [min]."""
        sources = [n for n in self._nodes.values() if n.kind == "subcatchment"]
        first = sources[0]
        assert first.hydrograph is not None  # a subcatchment has its hydrograph
        step = first.hydrograph.timestep_min
        for other in sources[1:]:
            assert other.hydrograph is not None
            found = other.hydrograph.timestep_min
            if abs(found - step) > STEP_TOLERANCE * step:
                raise InvalidParameterError(
                    f"Nodes {first.id!r} and {other.id!r} have different time steps "
                    f"({step:g} and {found:g} min)",
                    details={
                        "reason": "timestep_mismatch",
                        "nodes": [first.id, other.id],
                        "timesteps_min": [step, found],
                    },
                    hint="Give every source hydrograph the same time step; nothing is "
                    "resampled.",
                )
            start, begun = first.hydrograph.start_min, other.hydrograph.start_min
            if abs(begun - start) > STEP_TOLERANCE * step:
                raise InvalidParameterError(
                    f"Nodes {first.id!r} and {other.id!r} start at different times "
                    f"({start:g} and {begun:g} min)",
                    details={
                        "reason": "start_mismatch",
                        "nodes": [first.id, other.id],
                        "starts_min": [start, begun],
                    },
                    hint="Give every source hydrograph the same first time.",
                )
        return step

    def route(self) -> NetworkResult:
        """Route the sources down the network.

        Returns
        -------
        NetworkResult
            The hydrograph that leaves every node and the run of every reach.

        Raises
        ------
        InvalidParameterError
            From a reach (an initial outflow outside a table, a step that no division
            keeps stable...), with ``details.node_id`` and the message naming the node.
        CalculationError
            From a reach (a flood beyond a table...), with ``details.node_id``.
        """
        hydrographs: dict[str, Hydrograph] = {}
        runs: dict[str, RoutingResult] = {}
        for node in self._nodes.values():
            if node.kind == "subcatchment":
                assert node.hydrograph is not None
                hydrographs[node.id] = node.hydrograph
            elif node.kind == "junction":
                hydrographs[node.id] = _sum([hydrographs[up] for up in node.upstream])
            elif node.kind == "outlet":
                hydrographs[node.id] = hydrographs[node.upstream[0]]
            else:
                assert node.reach is not None
                try:
                    run = node.reach.route(
                        hydrographs[node.upstream[0]],
                        initial_outflow_m3s=node.initial_outflow_m3s,
                        extend_min=node.extend_min,
                    )
                except (InvalidParameterError, CalculationError) as exc:
                    raise type(exc)(
                        f"Node {node.id!r}: {exc}",
                        details={**exc.details, "node_id": node.id},
                        hint=exc.hint,
                    ) from exc
                runs[node.id] = run
                hydrographs[node.id] = run.outflow
        return NetworkResult(
            name=self.name,
            order=self.order,
            outlet=self.outlet,
            timestep_min=self.timestep_min,
            hydrographs=hydrographs,
            runs=runs,
        )
