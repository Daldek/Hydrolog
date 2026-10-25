"""Routing over a river network: a directed acyclic graph of routing elements.

A :class:`RoutingNetwork` composes the elements of this package along a stream. The
nodes are objects that **link by reference**: a node holds the nodes that flow into it
(``inflows``, the convention of ``StreamSegment.upstream_ids``), so a network is built
by handing the upstream objects to the node below them, and it is the outlet that
holds the whole of it. Water flows from node to node:

==============  ===========  ==========================================================
class           inflows      what the node does
==============  ===========  ==========================================================
Subcatchment    none         brings a source hydrograph into the network
Channel         one          routes its inflow through any :class:`Reach`
Reservoir       one          the same, with a :class:`LevelPoolReach`
Junction        one or more  adds the hydrographs that flow into it
Outlet          one          the end of the network; its hydrograph is the result
==============  ===========  ==========================================================

An id still names every node (it names the results and the files): the document
``hydrolog-network/1`` writes the same graph with ids, ``from`` listing the ids of the
inflows (``"type"`` of a ``Channel`` is ``"reach"``), and
:meth:`RoutingNetwork.from_document` reads it. Nodes are immutable: a node that is not
connected yet is fed by :meth:`Node.with_inflows`, which returns a copy.

A network is checked when it is made, with the vocabulary of
:class:`~hydrolog.network.StreamNetwork`: the shapes that a lumped model cannot route
are errors: a node that flows into two nodes (``several_downstream``: a bifurcation
would count its water twice), no outlet or two (``no_outlet``, ``several_outlets``),
an outlet that something flows out of (``outlet_has_downstream``) and a node that does
not reach the outlet (``disconnected_node``). A document can also hold an id that is
listed but not in the network (``unknown_upstream``) or a cycle (``cycle``, the nodes
in flow order); objects cannot. The nodes are evaluated headwaters first, and among the
nodes that are ready the smallest id first, so neither the order of the nodes in a
list nor in a file changes anything.

**Time axes.** One time step for the whole network: the source hydrographs must have the
same step and the same first time (``timestep_mismatch``, ``start_mismatch``); nothing
is resampled (ADR-0008). Their lengths may differ, and so do the lengths of the
hydrographs that come out of the reaches, which are extended until the outflow has
settled: where hydrographs of different lengths meet in a junction, the shorter ones are
held at their last value, as the inflow of a reach is held over its extension.

**Extending the network.** A node is a class with a ``kind`` that implements the
protocol of :class:`Node` (``evaluate``, ``describe``, ``read_document``...) and is
registered in :data:`NODE_TYPES`; the network and the document code have no list of the
kinds (ADR-0012).

Examples
--------
Two tributaries joining above a reach:

>>> from hydrolog.routing import (
...     Channel, Hydrograph, Junction, LagReach, Outlet, RoutingNetwork, Subcatchment
... )
>>> small = Hydrograph.from_step([1.0, 4.0, 1.0], timestep_min=10.0)
>>> large = Hydrograph.from_step([2.0, 8.0, 2.0], timestep_min=10.0)
>>> sources = [Subcatchment("A", small), Subcatchment("B", large)]
>>> junction = Junction("J", inflows=sources)
>>> reach = Channel("R", LagReach(lag_min=10.0), inflow=junction)
>>> network = RoutingNetwork(Outlet("OUT", inflow=reach))
>>> network.order
('A', 'B', 'J', 'R', 'OUT')
>>> network.route().hydrographs["OUT"].peak_discharge_m3s
12.0
"""

from __future__ import annotations

import copy
import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Final, Self

import numpy as np

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing._checks import in_range, shown
from hydrolog.routing._order import ordered
from hydrolog.routing._registry import Registry
from hydrolog.routing.hydrograph import STEP_TOLERANCE, Hydrograph
from hydrolog.routing.level_pool import LevelPoolReach
from hydrolog.routing.parameters import Parameter, parameter
from hydrolog.routing.reach import REACH_METHODS, Reach, RoutingResult

if TYPE_CHECKING:
    from hydrolog.routing.document import Prepare

__all__ = [
    "MAX_ID_CHARS",
    "NODE_TYPES",
    "Axis",
    "Channel",
    "Context",
    "Junction",
    "NetworkResult",
    "Node",
    "NodeOutput",
    "NodeSummary",
    "Outlet",
    "Reservoir",
    "RoutingNetwork",
    "Subcatchment",
]

MAX_ID_CHARS: Final = 64
"""Longest node id; an id names the file of its node (``<id>.csv``)."""

_ID = re.compile(r"\w[\w.-]*")
_COMMON: Final = ("id", "type", "from")
_RUN_FIELDS: Final = ("initial_outflow_m3s", "extend_min")
_RESERVED = re.compile(
    r"(?:con|prn|aux|nul|(?:com|lpt)[1-9\u00b9\u00b2\u00b3])(?:\..*)?",
    re.IGNORECASE | re.DOTALL,
)
"""Device names of Windows: a file so named, with any extension, is the device."""


def _check_id(value: object, *, role: str = "id") -> str:
    """Return ``value`` when it can be a node id: it names a file, so it is plain."""
    if (
        not isinstance(value, str)
        or len(value) > MAX_ID_CHARS
        or _ID.fullmatch(value) is None
        or value.endswith(".")
    ):
        text = shown(value)
        raise InvalidParameterError(
            f"Node {role} {text[:MAX_ID_CHARS]!r} is not valid",
            details={"reason": "invalid_id", "node_id": text[:MAX_ID_CHARS]},
            hint=(
                "An id starts with a letter, a digit or an underscore, goes on with "
                "letters, digits, underscores, dots and hyphens, does not end with a "
                f"dot and has at most {MAX_ID_CHARS} characters: the file of the node "
                "is named after it."
            ),
        )
    if _RESERVED.fullmatch(value):
        raise InvalidParameterError(
            f"Node {role} {value!r} is a reserved name",
            details={"reason": "reserved_name", "node_id": value},
            hint=(
                "The file of the node is named after its id, and Windows reserves "
                "the names con, prn, aux, nul, com1 to com9 and lpt1 to lpt9, with "
                "any extension, whatever the case. Choose another id."
            ),
        )
    return value


def _of_node(exc: InvalidParameterError, node_id: str) -> InvalidParameterError:
    """Return ``exc`` as the error of a node: named in its message and ``details``."""
    return InvalidParameterError(
        f"Node {node_id!r}: {exc}",
        details={**exc.details, "node_id": node_id},
        hint=exc.hint,
    )


def _rule(fewest: int, most: int | None) -> str:
    """Return the number of inflows a node takes, in words."""
    if most == 0:
        return "no upstream node"
    if most is None:
        return "at least one upstream node" if fewest == 1 else f"{fewest} or more"
    if fewest == most:
        return "exactly one upstream node" if most == 1 else f"exactly {most} nodes"
    return f"{fewest} to {most} upstream nodes"


def _count_error(
    node_id: str, kind: str, found: int, rule: str
) -> InvalidParameterError:
    """Return the error of a node with the wrong number of inflows."""
    return InvalidParameterError(
        f"Node {node_id!r} is a {kind} and takes {rule}, but lists {found}",
        details={
            "reason": "upstream_count",
            "node_id": node_id,
            "type": kind,
            "found": found,
        },
        hint=f"A {kind} takes {rule}.",
    )


def _check_fields(
    node_id: str, kind: str, fields: Mapping[str, Any], allowed: Sequence[str]
) -> None:
    """Refuse a field that the type of the node does not take."""
    every = (*_COMMON, *allowed)
    for key in fields:
        if key not in every:
            raise InvalidParameterError(
                f"Node {node_id!r} is a {kind} and takes no {shown(key)}",
                details={
                    "reason": "unknown_field",
                    "node_id": node_id,
                    "field": shown(key),
                    "allowed": list(every),
                },
                hint=f"A {kind} takes {', '.join(every)}.",
            )


def _constructor_fields(cls: type) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the names of the arguments of a constructor and those it requires."""
    arguments = [
        item
        for item in inspect.signature(cls).parameters.values()
        if item.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    return (
        tuple(item.name for item in arguments),
        tuple(
            item.name for item in arguments if item.default is inspect.Parameter.empty
        ),
    )


@dataclass(frozen=True)
class Axis:
    """The time axis that a source node brings into the network.

    Attributes
    ----------
    timestep_min : float or None
        The step of the hydrograph [min]; ``None`` when the node takes the step of the
        network.
    start_min : float
        The first time of the hydrograph [min].
    """

    timestep_min: float | None
    start_min: float


@dataclass(frozen=True)
class Context:
    """What a node needs to know of the run that it is evaluated in.

    Attributes
    ----------
    timestep_min : float
        The time step of the network [min].
    """

    timestep_min: float


@dataclass
class NodeOutput:
    """What a node gives when it is evaluated.

    Attributes
    ----------
    hydrograph : Hydrograph
        The hydrograph that leaves the node.
    run : RoutingResult or None
        The run of the routing element of a ``Channel`` or a ``Reservoir``.
    """

    hydrograph: Hydrograph
    run: RoutingResult | None = None


NODE_TYPES: Registry[Node] = Registry("type", key="kind", reason="unknown_type")
"""The kinds of node by name, the ``type`` of a node in a document: a new kind is a new
:class:`Node` that is registered here (``@NODE_TYPES.register``)."""


class Node(ABC):
    """A node of a :class:`RoutingNetwork`: a source, an element, a sum or the end.

    The base of the node classes. It holds the ``id`` and the nodes that flow into the
    node (``inflows``) and is immutable: :meth:`with_inflows` returns a copy. A
    subclass sets the class attributes below, implements :meth:`evaluate`,
    :meth:`describe` and :meth:`read_document`, and is registered in
    :data:`NODE_TYPES`.

    Parameters
    ----------
    id : str
        The name of the node, unique in the network without regard to case; it names
        the file of the node, so it is plain: letters, digits, ``_``, ``.`` and ``-``,
        at most :data:`MAX_ID_CHARS` characters, and not a device name of Windows
        (``con``, ``prn``, ``aux``, ``nul``, ``com1`` to ``com9``, ``lpt1`` to
        ``lpt9``, in any case and with any extension).
    inflows : iterable of Node, optional
        The nodes that flow into this one. A node of a kind that takes fewer is refused
        when more are given; one that takes more is refused by the network when it has
        fewer (:meth:`with_inflows` connects a node afterwards).

    Attributes
    ----------
    kind : str
        The ``type`` of the node in a document.
    inflow_count : tuple of (int, int or None)
        The fewest and the most nodes that flow into a node of this kind (``None``: no
        limit).
    terminal : bool
        Whether the node is the end of the network: a network has exactly one.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``invalid_id`` or ``reserved_name``; ``type``,
        ``upstream_count`` or ``duplicate_upstream`` for the inflows (and
        ``details.node_id``).
    """

    kind: ClassVar[str]
    inflow_count: ClassVar[tuple[int, int | None]] = (1, 1)
    terminal: ClassVar[bool] = False

    def __init__(self, id: str, inflows: Iterable[Node] = ()) -> None:
        """Check the id and the inflows."""
        self._id = _check_id(id)
        self._inflows = self._checked(tuple(inflows))

    def _checked(self, inflows: tuple[Node, ...]) -> tuple[Node, ...]:
        """Return ``inflows`` when they are nodes, at most as many as the kind takes."""
        for item in inflows:
            if not isinstance(item, Node):
                raise InvalidParameterError(
                    f"Node {self._id!r}: an inflow must be a node, not "
                    f"{type(item).__name__}",
                    details={
                        "reason": "type",
                        "node_id": self._id,
                        "field": "inflows",
                    },
                )
        fewest, most = self.inflow_count
        if most is not None and len(inflows) > most:
            raise _count_error(self._id, self.kind, len(inflows), _rule(fewest, most))
        if len({id(item) for item in inflows}) != len(inflows):
            raise InvalidParameterError(
                f"Node {self._id!r} lists an upstream node twice: its water would be "
                "counted twice",
                details={"reason": "duplicate_upstream", "node_id": self._id},
            )
        return inflows

    @property
    def id(self) -> str:
        """Str: the name of the node."""
        return self._id

    @property
    def inflows(self) -> tuple[Node, ...]:
        """Tuple of Node: the nodes that flow into this one, in the order given."""
        return self._inflows

    @property
    def upstream(self) -> tuple[str, ...]:
        """Tuple of str: the ids of the nodes that flow into this one (``from``)."""
        return tuple(node.id for node in self._inflows)

    def with_inflows(self, *inflows: Node) -> Self:
        """Return a copy of the node that the given nodes flow into.

        Parameters
        ----------
        *inflows : Node
            The nodes that flow into the copy; they replace those of this node.

        Returns
        -------
        Node
            A node of the same class with the same fields.

        Raises
        ------
        InvalidParameterError
            If an inflow is not a node, is given twice or the kind takes fewer.
        """
        clone = copy.copy(self)
        clone._inflows = self._checked(tuple(inflows))
        return clone

    def __repr__(self) -> str:
        """Return the class, the id and the ids of the inflows."""
        return f"{type(self).__name__}({self._id!r}, inflows={list(self.upstream)})"

    def axis(self) -> Axis | None:
        """Return the time axis of the source that the node brings, if it is one.

        Returns
        -------
        Axis or None
            The step and the first time of the node's own hydrograph; ``None`` for a
            node that only works on its inflows.
        """
        return None

    @abstractmethod
    def evaluate(self, inflows: Sequence[Hydrograph], context: Context) -> NodeOutput:
        """Return the hydrograph that leaves the node.

        Parameters
        ----------
        inflows : sequence of Hydrograph
            The hydrographs that leave the nodes upstream, in the order of
            :attr:`inflows`.
        context : Context
            The run: the time step of the network.

        Returns
        -------
        NodeOutput
            The hydrograph and, for an element that routes, its run.
        """

    @abstractmethod
    def describe(self, output: NodeOutput | None = None) -> list[Parameter]:
        """List the parameters of the node, and what an evaluation used.

        Parameters
        ----------
        output : NodeOutput, optional
            What :meth:`evaluate` returned. With it the list holds the values that the
            calculation used, the derived ones too; without it, what is given.

        Returns
        -------
        list of Parameter
            Name, value, unit and source (``given``, ``computed`` or ``default``) of
            every value; empty for a node that has none.
        """

    @classmethod
    @abstractmethod
    def read_document(cls, node_id: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        """Read the fields of a node of a document.

        Parameters
        ----------
        node_id : str
            The id of the node.
        fields : mapping
            The node as the document has it: ``id``, ``type``, ``from`` and the fields
            of this kind. A value of ``None`` is a field that is not given.

        Returns
        -------
        dict
            The keyword arguments of the constructor (without the id and the inflows).

        Raises
        ------
        InvalidParameterError
            With ``details.reason`` ``unknown_field``, ``missing_field``, ``type``...
            and ``details.node_id`` and ``details.field``.
        """

    @classmethod
    def read_entry(
        cls, node_id: str, fields: Mapping[str, Any]
    ) -> tuple[tuple[str, ...], dict[str, Any]]:
        """Read a node of a document: the ids of its inflows and its arguments.

        Parameters
        ----------
        node_id : str
            The id of the node.
        fields : mapping
            The node as the document has it (see :meth:`read_document`).

        Returns
        -------
        tuple
            The ids in ``from`` and the arguments of the constructor
            (:meth:`read_document`).

        Raises
        ------
        InvalidParameterError
            If a field is not valid (:meth:`read_document`), an id is not
            (``invalid_id``, ``reserved_name``), ``from`` is not a list of ids
            (``type``), the kind takes another number of them (``upstream_count``) or
            an id is listed twice (``duplicate_upstream``).
        """
        listed = fields.get("from")
        upstream: tuple[str, ...] = ()
        if listed is not None:
            if not isinstance(listed, list) or not all(
                isinstance(item, str) for item in listed
            ):
                raise InvalidParameterError(
                    f"Node {node_id!r}: 'from' must be a list of node ids",
                    details={
                        "reason": "type",
                        "node_id": node_id,
                        "field": "from",
                    },
                    hint='Write the ids that flow into the node as a list: ["A", "B"].',
                )
            upstream = tuple(listed)
        arguments = cls.read_document(node_id, fields)
        _check_id(node_id)
        for item in upstream:
            _check_id(item, role="upstream id")
        fewest, most = cls.inflow_count
        if len(upstream) < fewest or (most is not None and len(upstream) > most):
            raise _count_error(node_id, cls.kind, len(upstream), _rule(fewest, most))
        if len(set(upstream)) != len(upstream):
            raise InvalidParameterError(
                f"Node {node_id!r} lists an upstream node twice: its water would be "
                "counted twice",
                details={"reason": "duplicate_upstream", "node_id": node_id},
            )
        return upstream, arguments

    @classmethod
    def build(
        cls, node_id: str, arguments: Mapping[str, Any], inflows: Sequence[Node]
    ) -> Node:
        """Make a node from what :meth:`read_entry` read and the nodes that flow in.

        Parameters
        ----------
        node_id : str
            The id of the node.
        arguments : mapping
            The keyword arguments of the constructor.
        inflows : sequence of Node
            The nodes that flow into it.

        Returns
        -------
        Node
            The node.

        Raises
        ------
        InvalidParameterError
            If the constructor refuses a value; ``details.node_id`` names the node.
        """
        try:
            return cls(node_id, **arguments).with_inflows(*inflows)
        except InvalidParameterError as exc:
            if exc.details.get("node_id") == node_id:
                raise
            raise _of_node(exc, node_id) from exc


@NODE_TYPES.register
class Subcatchment(Node):
    """A source: the hydrograph that a lumped catchment brings into the network.

    Parameters
    ----------
    id : str
        The id of the node (see :class:`Node`).
    hydrograph : Hydrograph
        The discharge that leaves the catchment [m3/s].

    Raises
    ------
    InvalidParameterError
        If the id is not valid or ``hydrograph`` is not a :class:`Hydrograph`.

    Examples
    --------
    >>> from hydrolog.routing import Hydrograph, Subcatchment
    >>> source = Subcatchment("A", Hydrograph.from_step([0.0, 2.0, 1.0], 10.0))
    >>> source.hydrograph.peak_discharge_m3s
    2.0
    """

    kind = "subcatchment"
    inflow_count = (0, 0)

    def __init__(self, id: str, hydrograph: Hydrograph) -> None:
        """Create the node."""
        super().__init__(id)
        if not isinstance(hydrograph, Hydrograph):
            raise InvalidParameterError(
                f"Node {id!r}: the hydrograph must be a Hydrograph, not "
                f"{type(hydrograph).__name__}",
                details={"reason": "type", "node_id": id, "field": "hydrograph"},
            )
        self._hydrograph = hydrograph

    @property
    def hydrograph(self) -> Hydrograph:
        """Hydrograph: the discharge that the node brings."""
        return self._hydrograph

    def axis(self) -> Axis:
        """Return the step and the first time of the hydrograph."""
        return Axis(self._hydrograph.timestep_min, self._hydrograph.start_min)

    def evaluate(self, inflows: Sequence[Hydrograph], context: Context) -> NodeOutput:
        """Return the hydrograph of the node."""
        return NodeOutput(self._hydrograph)

    def describe(self, output: NodeOutput | None = None) -> list[Parameter]:
        """Return no parameters: the hydrograph is the whole of the node."""
        return []

    @classmethod
    def read_document(cls, node_id: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        """Read ``times_min`` with ``discharge_m3s``, the hydrograph inline."""
        _check_fields(node_id, cls.kind, fields, ("times_min", "discharge_m3s"))
        times, values = fields.get("times_min"), fields.get("discharge_m3s")
        if times is None or values is None:
            absent = "discharge_m3s" if values is None else "times_min"
            raise InvalidParameterError(
                f"Node {node_id!r} is a subcatchment and needs {absent!r}",
                details={
                    "reason": "missing_field",
                    "node_id": node_id,
                    "field": absent,
                },
                hint="Give 'times_min' with 'discharge_m3s'.",
            )
        try:
            return {"hydrograph": Hydrograph(times, values)}
        except InvalidParameterError as exc:
            raise _of_node(exc, node_id) from exc


@NODE_TYPES.register
class Channel(Node):
    """A reach of the stream: it routes its inflow through a routing element.

    Parameters
    ----------
    id : str
        The id of the node (see :class:`Node`).
    reach : Reach
        The element that routes: a :class:`LagReach`, a :class:`MuskingumReach`, any
        other :class:`Reach`. A reach in the document is called ``"reach"``.
    inflow : Node, optional
        The node that flows into the channel; it can be given later
        (:meth:`Node.with_inflows`).
    initial_outflow_m3s : float, optional
        Outflow at the first ordinate [m3/s], >= 0; default the first inflow ordinate
        (:meth:`Reach.route`).
    extend_min : float, optional
        Time added after the last inflow ordinate [min], >= 0; default until the
        outflow has settled (:meth:`Reach.route`).

    Raises
    ------
    InvalidParameterError
        If the id, the element or a run option is not valid (``details.node_id``).

    Examples
    --------
    >>> from hydrolog.routing import Channel, Hydrograph, LagReach, Subcatchment
    >>> source = Subcatchment("A", Hydrograph.from_step([0.0, 2.0, 1.0], 10.0))
    >>> channel = Channel("R", LagReach(lag_min=20.0), inflow=source)
    >>> channel.upstream
    ('A',)
    """

    kind = "reach"
    _method_fields: ClassVar[tuple[str, ...]] = ("method",)

    def __init__(
        self,
        id: str,
        reach: Reach,
        *,
        inflow: Node | None = None,
        initial_outflow_m3s: float | None = None,
        extend_min: float | None = None,
    ) -> None:
        """Create the node."""
        super().__init__(id, () if inflow is None else (inflow,))
        self._check_reach(reach)
        self._reach = reach
        try:
            self._initial_outflow_m3s = (
                None
                if initial_outflow_m3s is None
                else in_range(initial_outflow_m3s, "initial_outflow_m3s", minimum=0.0)
            )
            self._extend_min = (
                None
                if extend_min is None
                else in_range(extend_min, "extend_min", minimum=0.0)
            )
        except InvalidParameterError as exc:
            raise _of_node(exc, id) from exc

    def _check_reach(self, reach: Reach) -> None:
        """Refuse an element that this kind of node does not route with."""
        if not isinstance(reach, Reach):
            raise InvalidParameterError(
                f"Node {self._id!r} routes with a Reach, not {type(reach).__name__}",
                details={"reason": "type", "node_id": self._id, "field": "reach"},
            )

    @property
    def reach(self) -> Reach:
        """Reach: the element that routes."""
        return self._reach

    @property
    def initial_outflow_m3s(self) -> float | None:
        """Float or None: the outflow at the first ordinate [m3/s], if it was given."""
        return self._initial_outflow_m3s

    @property
    def extend_min(self) -> float | None:
        """Float or None: the time added after the last ordinate [min], if given."""
        return self._extend_min

    def evaluate(self, inflows: Sequence[Hydrograph], context: Context) -> NodeOutput:
        """Route the inflow through the element."""
        run = self._reach.route(
            inflows[0],
            initial_outflow_m3s=self._initial_outflow_m3s,
            extend_min=self._extend_min,
        )
        return NodeOutput(run.outflow, run=run)

    def describe(self, output: NodeOutput | None = None) -> list[Parameter]:
        """List the parameters of the element and the run options.

        The initial outflow and the extension are ``"default"`` when they were not
        given: with a run, the values that the run used.
        """
        run = None if output is None else output.run
        listed = self._reach.describe(run)
        if self._initial_outflow_m3s is not None:
            listed.append(
                parameter("initial_outflow_m3s", self._initial_outflow_m3s, "given")
            )
        elif run is not None:
            listed.append(
                parameter(
                    "initial_outflow_m3s", float(run.inflow.discharge_m3s[0]), "default"
                )
            )
        if self._extend_min is not None:
            listed.append(parameter("extend_min", self._extend_min, "given"))
        elif run is not None:
            listed.append(parameter("extend_min", run.extension_min, "default"))
        return listed

    @classmethod
    def _method(cls, node_id: str, fields: Mapping[str, Any]) -> str:
        """Return the ``method`` of the node: a reach names it."""
        method = fields.get("method")
        if method is None:
            raise InvalidParameterError(
                f"Node {node_id!r} is a reach and needs a 'method'",
                details={
                    "reason": "missing_field",
                    "node_id": node_id,
                    "field": "method",
                },
                hint=f"The methods are {', '.join(REACH_METHODS.names)}.",
            )
        REACH_METHODS.resolve(method, f"Node {node_id!r}", node_id=node_id)
        return str(method)

    @classmethod
    def read_document(cls, node_id: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        """Read ``method`` and the options of that method, and the run options."""
        method = cls._method(node_id, fields)
        element = REACH_METHODS[method]
        names, required = _constructor_fields(element)
        _check_fields(
            node_id, cls.kind, fields, (*cls._method_fields, *_RUN_FIELDS, *names)
        )
        options = {name: fields[name] for name in names if fields.get(name) is not None}
        for name in required:
            if name not in options:
                raise InvalidParameterError(
                    f"Node {node_id!r} routes by {method} and needs {name!r}",
                    details={
                        "reason": "missing_field",
                        "node_id": node_id,
                        "field": name,
                    },
                )
        try:
            reach = element(**options)
        except InvalidParameterError as exc:
            raise _of_node(exc, node_id) from exc
        return {
            "reach": reach,
            "initial_outflow_m3s": fields.get("initial_outflow_m3s"),
            "extend_min": fields.get("extend_min"),
        }


@NODE_TYPES.register
class Reservoir(Channel):
    """A reservoir: a :class:`Channel` that routes by level pool.

    Parameters
    ----------
    id : str
        The id of the node (see :class:`Node`).
    reach : LevelPoolReach
        The storage-outflow table of the reservoir.
    inflow, initial_outflow_m3s, extend_min
        As in :class:`Channel`.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``reservoir_model`` if ``reach`` is another element.
    """

    kind = "reservoir"
    _method_fields = ()

    def _check_reach(self, reach: Reach) -> None:
        """Refuse an element that is not a level pool."""
        if not isinstance(reach, LevelPoolReach):
            raise InvalidParameterError(
                f"Node {self._id!r} is a reservoir and routes with a LevelPoolReach",
                details={
                    "reason": "reservoir_model",
                    "node_id": self._id,
                    "model": type(reach).__name__,
                },
                hint="A reach with another model is a node of type reach.",
            )

    @classmethod
    def _method(cls, node_id: str, fields: Mapping[str, Any]) -> str:
        """Return ``level-pool``: a reservoir has no ``method``."""
        return LevelPoolReach.model


@NODE_TYPES.register
class Junction(Node):
    """A confluence: it adds the hydrographs that flow into it.

    Hydrographs of different lengths are added on the longest axis; the shorter ones are
    held at their last value, as the inflow of a reach is held over its extension.

    Parameters
    ----------
    id : str
        The id of the node (see :class:`Node`).
    inflows : iterable of Node
        The nodes that flow into the junction, at least one by the time the network is
        made.

    Raises
    ------
    InvalidParameterError
        If the id or an inflow is not valid (see :class:`Node`).
    """

    kind = "junction"
    inflow_count = (1, None)

    def evaluate(self, inflows: Sequence[Hydrograph], context: Context) -> NodeOutput:
        """Add the hydrographs."""
        return NodeOutput(_sum(inflows))

    def describe(self, output: NodeOutput | None = None) -> list[Parameter]:
        """Return no parameters: a junction only adds."""
        return []

    @classmethod
    def read_document(cls, node_id: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        """Read nothing: a junction has no field of its own."""
        _check_fields(node_id, cls.kind, fields, ())
        return {}


@NODE_TYPES.register
class Outlet(Node):
    """The end of the network: its hydrograph is the result.

    Parameters
    ----------
    id : str
        The id of the node (see :class:`Node`).
    inflow : Node, optional
        The node that flows into the outlet; it can be given later
        (:meth:`Node.with_inflows`).

    Raises
    ------
    InvalidParameterError
        If the id or the inflow is not valid (see :class:`Node`).
    """

    kind = "outlet"
    terminal = True

    def __init__(self, id: str, inflow: Node | None = None) -> None:
        """Create the node."""
        super().__init__(id, () if inflow is None else (inflow,))

    def evaluate(self, inflows: Sequence[Hydrograph], context: Context) -> NodeOutput:
        """Return the hydrograph that reaches the outlet."""
        return NodeOutput(inflows[0])

    def describe(self, output: NodeOutput | None = None) -> list[Parameter]:
        """Return no parameters: the outlet only ends the network."""
        return []

    @classmethod
    def read_document(cls, node_id: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        """Read nothing: the outlet has no field of its own."""
        _check_fields(node_id, cls.kind, fields, ())
        return {}


@dataclass
class NodeSummary(JsonResultMixin):
    """What a result says of one node: its place, its figures and its parameters.

    Attributes
    ----------
    id : str
        The id of the node.
    type : str
        The kind of the node (``"subcatchment"``, ``"reach"``, ``"reservoir"``,
        ``"junction"``, ``"outlet"``, or the ``kind`` of a class added to
        :data:`NODE_TYPES`).
    inflows : tuple of str
        The ids of the nodes that flow into it.
    peak_m3s : float
        Peak of the hydrograph that leaves the node [m3/s].
    time_to_peak_min : float
        Time of the peak [min].
    volume_m3 : float
        Volume under the hydrograph (trapezoid sum) [m3].
    parameters : list of Parameter
        The values that the calculation of the node used (:meth:`Node.describe`): the
        ones given, the defaults and the ones derived by the run.
    """

    id: str
    type: str
    inflows: tuple[str, ...]
    peak_m3s: float
    time_to_peak_min: float
    volume_m3: float
    parameters: list[Parameter]


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
        The hydrograph that leaves each node: the source of a ``Subcatchment``, the
        outflow of a ``Channel`` or ``Reservoir`` (extended until it settled), the sum
        of a ``Junction`` and, for the ``Outlet``, the hydrograph that reaches it.
    runs : dict of str to RoutingResult
        The result of each ``Channel`` and ``Reservoir``: parameters, storage at both
        ends, volume balance and notices.
    nodes : dict of str to NodeSummary
        For each node its inflows, peak, time to peak, volume and the parameters of its
        calculation.
    """

    name: str | None
    order: tuple[str, ...]
    outlet: str
    timestep_min: float
    hydrographs: dict[str, Hydrograph]
    runs: dict[str, RoutingResult]
    nodes: dict[str, NodeSummary]


def _sum(hydrographs: Sequence[Hydrograph]) -> Hydrograph:
    """Add hydrographs on one time axis; shorter ones are held at their last value."""
    longest = max(hydrographs, key=len)
    total = np.zeros(len(longest))
    for hydrograph in hydrographs:
        total += hydrograph.extended(len(longest) - len(hydrograph)).discharge_m3s
    return Hydrograph(longest.times_min, total)


def _reachable(roots: Sequence[Node]) -> list[Node]:
    """Return the roots and every node upstream of them, each once, roots first."""
    found: dict[int, Node] = {}
    for root in roots:
        found.setdefault(id(root), root)
    queue = list(found.values())
    position = 0
    while position < len(queue):
        for node in queue[position].inflows:
            if id(node) not in found:
                found[id(node)] = node
                queue.append(node)
        position += 1
    return queue


def check_unique(ids: Iterable[str]) -> None:
    """Refuse two ids that are equal without regard to case: an id names a file.

    Parameters
    ----------
    ids : iterable of str
        The ids of the nodes, the earlier first.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``duplicate_node`` (``node_id`` is the later of the two
        ids, ``other_id`` the earlier).
    """
    folded: dict[str, str] = {}
    for node_id in ids:
        earlier = folded.get(node_id.casefold())
        if earlier is not None:
            raise InvalidParameterError(
                f"Node {node_id!r} repeats the id of node {earlier!r} (ids are "
                "compared without regard to case)",
                details={
                    "reason": "duplicate_node",
                    "node_id": node_id,
                    "other_id": earlier,
                },
                hint="Every node needs its own id: it names the file of the node.",
            )
        folded[node_id.casefold()] = node_id


class RoutingNetwork:
    """A directed acyclic network of routing elements, ready to route.

    The network is the nodes that its roots reach by their inflows: give the
    :class:`Outlet` and everything upstream of it is in the network.

    Parameters
    ----------
    nodes : Node or iterable of Node
        The outlet, or the nodes to start from (several roots are refused when they do
        not end in one outlet). Every node upstream of them belongs to the network,
        listed or not.
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
        equal without regard to case); ``upstream_count`` (``node_id``, ``type``,
        ``found``: a node that has fewer inflows than its kind takes);
        ``unknown_upstream`` and ``cycle`` (only from a node that is not immutable);
        ``several_downstream`` (``node_id``, ``downstream``); ``no_outlet``;
        ``several_outlets`` (``nodes``); ``outlet_has_downstream`` (``node_id``,
        ``downstream``); ``disconnected_node`` (``node_id``: a node that feeds nothing
        and is not the outlet, ``n_disconnected``: the nodes that do not reach the
        outlet); ``timestep_mismatch`` and ``start_mismatch`` (``nodes``, and
        ``timesteps_min`` or ``starts_min``).
    """

    def __init__(
        self, nodes: Node | Iterable[Node], *, name: str | None = None
    ) -> None:
        """Check the network and put the nodes in the order of evaluation."""
        roots = [nodes] if isinstance(nodes, Node) else list(nodes)
        if not roots:
            raise InvalidParameterError(
                "A network needs at least one node",
                details={"reason": "empty"},
            )
        for root in roots:
            if not isinstance(root, Node):
                raise InvalidParameterError(
                    f"A network is made of nodes, not {type(root).__name__}",
                    details={"reason": "type", "value": type(root).__name__},
                )
        listed = _reachable(roots)
        check_unique([node.id for node in listed])
        by_id = {node.id: node for node in listed}
        for node in listed:
            fewest, most = node.inflow_count
            found = len(node.inflows)
            if found < fewest or (most is not None and found > most):
                raise _count_error(node.id, node.kind, found, _rule(fewest, most))
        order = ordered({node_id: node.upstream for node_id, node in by_id.items()})
        self.name = name
        self._nodes: dict[str, Node] = {node_id: by_id[node_id] for node_id in order}
        self.order: tuple[str, ...] = tuple(order)
        self.outlet = self._check_shape()
        self.timestep_min = self._check_time_axes()

    @classmethod
    def from_document(
        cls, document: object, *, prepare: Prepare | None = None
    ) -> RoutingNetwork:
        """Read a network from a ``hydrolog-network/1`` document.

        Parameters
        ----------
        document : mapping
            The document: ``schema`` (``"hydrolog-network/1"``), optionally ``name``,
            and ``nodes``, each with ``id``, ``type``, ``from`` (the ids of the inflows)
            and the fields of its kind. Values are JSON-native.
        prepare : callable, optional
            Called as ``prepare(node_id, type, entry)`` for every node before it is
            read, to return the entry that is read instead (a front door that takes
            values from files uses it); an error that it raises is not changed.

        Returns
        -------
        RoutingNetwork
            The network.

        Raises
        ------
        InvalidParameterError
            If the document is not valid: ``details.reason`` ``shape``,
            ``unknown_field``, ``missing_field``, ``unknown_schema``, ``type``,
            ``unknown_type``, ``invalid_id``, ``upstream_count`` and the reasons of
            the nodes and of the network (see :class:`RoutingNetwork`), with
            ``details.node_id`` and ``details.field``.
        """
        from hydrolog.routing.document import read_network

        return read_network(document, prepare=prepare)

    @property
    def nodes(self) -> tuple[Node, ...]:
        """Tuple of Node: the nodes in the order of evaluation."""
        return tuple(self._nodes.values())

    def node(self, node_id: str) -> Node:
        """Return the node called ``node_id``.

        Parameters
        ----------
        node_id : str
            The id of a node of the network.

        Returns
        -------
        Node
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
        outlets = [n.id for n in self._nodes.values() if n.terminal]
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
                hint="Make the node an inflow of the node it flows into (the `from` "
                "of that node in a document).",
            )
        return outlet

    def _check_time_axes(self) -> float:
        """Check that the sources share one time axis and return its step [min]."""
        sources = [
            (node, axis)
            for node in self._nodes.values()
            if (axis := node.axis()) is not None
        ]
        timed = [
            (node, axis) for node, axis in sources if axis.timestep_min is not None
        ]
        first, first_axis = timed[0]
        step = first_axis.timestep_min
        assert step is not None  # a source with a given hydrograph has its step
        for other, axis in timed[1:]:
            assert axis.timestep_min is not None
            found = axis.timestep_min
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
            start, begun = first_axis.start_min, axis.start_min
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
            The hydrograph that leaves every node, the run of every reach and the
            figures and parameters of every node.

        Raises
        ------
        InvalidParameterError
            From a reach (an initial outflow outside a table, a step that no division
            keeps stable...), with ``details.node_id`` and the message naming the node.
        CalculationError
            From a reach (a flood beyond a table...), with ``details.node_id``.
        """
        context = Context(self.timestep_min)
        hydrographs: dict[str, Hydrograph] = {}
        runs: dict[str, RoutingResult] = {}
        summaries: dict[str, NodeSummary] = {}
        for node in self._nodes.values():
            inflows = [hydrographs[up.id] for up in node.inflows]
            try:
                output = node.evaluate(inflows, context)
            except (InvalidParameterError, CalculationError) as exc:
                raise type(exc)(
                    f"Node {node.id!r}: {exc}",
                    details={**exc.details, "node_id": node.id},
                    hint=exc.hint,
                ) from exc
            hydrograph = output.hydrograph
            hydrographs[node.id] = hydrograph
            if output.run is not None:
                runs[node.id] = output.run
            summaries[node.id] = NodeSummary(
                id=node.id,
                type=node.kind,
                inflows=node.upstream,
                peak_m3s=hydrograph.peak_discharge_m3s,
                time_to_peak_min=hydrograph.time_to_peak_min,
                volume_m3=hydrograph.volume_m3,
                parameters=node.describe(output),
            )
        return NetworkResult(
            name=self.name,
            order=self.order,
            outlet=self.outlet,
            timestep_min=self.timestep_min,
            hydrographs=hydrographs,
            runs=runs,
            nodes=summaries,
        )
