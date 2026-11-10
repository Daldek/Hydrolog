"""The network as a document: ``hydrolog-network/1`` (ADR-0010, ADR-0012).

A network is a JSON object. The document is the definition format of a network and the
serialization of a :class:`~hydrolog.routing.RoutingNetwork`:
:meth:`RoutingNetwork.from_document <hydrolog.routing.RoutingNetwork.from_document>`
reads it, and
:meth:`RoutingNetwork.to_document <hydrolog.routing.RoutingNetwork.to_document>`
writes it::

    {
      "schema": "hydrolog-network/1",
      "name": "Upper catchment",
      "nodes": [
        {"id": "A", "type": "subcatchment", "times_min": [...], "discharge_m3s": [...]},
        {"id": "R1", "type": "reach", "from": ["A"], "method": "lag", "lag_min": 25},
        {"id": "OUT", "type": "outlet", "from": ["R1"]}
      ]
    }

``schema`` is required and must be ``hydrolog-network/1`` (every machine-readable
document has one, AGI-4.1). Every node has ``id``, ``type`` (a name of
:data:`~hydrolog.routing.NODE_TYPES`) and ``from``, the list of the ids that flow into
it; the other fields belong to the type, which reads them
(:meth:`~hydrolog.routing.Node.read_document`), and a field that the type does not take
is an error. Nothing here lists the types, the methods of a reach or any other kind of
thing: each is found by its name in a registry
(:class:`~hydrolog.routing._registry.Registry`).

Every node may also have a ``description``, plain text for people of at most 500
characters, and a ``position``, its cell in the grid of the schematic
(``{"x": 2, "y": 0}``), and the document a ``description`` of the network at its top
(ADR-0023). :class:`~hydrolog.routing.Node` reads and writes them for every kind of
node, after the fields of the kind, and they change no calculation::

    {"id": "ZB1", "type": "reservoir", "from": ["R1"],
     "storage_m3": [0, 50000, 120000], "outflow_m3s": [0, 2.5, 8.0],
     "description": "Suchy zbiornik powyżej Świerzawy", "position": {"x": 2, "y": 0}}

A subcatchment makes its own hydrograph when it has a ``watershed`` (the object of
``WatershedParameters``), a ``runoff`` model (``model`` and its fields) and a
``rainfall`` (``kind`` and its fields) in the place of the hydrograph::

    {"id": "A", "type": "subcatchment",
     "watershed": {"area_km2": 12.0, "perimeter_km": 18.0, "length_km": 6.0,
                   "elevation_min_m": 210.0, "elevation_max_m": 330.0, "cn": 75},
     "runoff": {"model": "curve-number", "tc_min": 90.0},
     "rainfall": {"kind": "design", "hietogram_type": "euler_ii",
                  "total_mm": 45.0, "duration_min": 60.0}}

The rainfall belongs to the subcatchment; the document can also have ``rainfall`` at
its top, which the subcatchments that have none of their own take, and ``timestep_min``
to fix the step of the network (see :class:`~hydrolog.routing.RoutingNetwork`). The
names of the kinds, models and shapes are those of the registries
(:data:`~hydrolog.routing.RAINFALL_KINDS`, :data:`~hydrolog.routing.RUNOFF_MODELS`,
:data:`~hydrolog.routing.HIETOGRAMS`).

:func:`write_network` is the other direction: every node writes its own fields
(:meth:`~hydrolog.routing.Node.document_fields`, ``type`` is its registered name), the
nodes follow in the order of evaluation and nothing that has its default is written, so
a document that the library wrote is the canonical form of every document that makes
the same network: written, read and written again it does not change, and the network
that it makes routes as the first one did.

This module reads values that are in the document. A value that is in a file (a column
of an inflows table, a rating file) is for the code that owns the files to put in the
document first; :func:`read_network` calls its ``prepare`` for every node before the
node is read, for that.

:func:`read_structure` reads the structure alone (ADR-0025): the ids, the types and the
links of the nodes and the areas of the headwaters, checked by the same checks of the
graph as the network, for the layout of a draft whose values are not complete yet.

Errors
------
What is wrong with the document is an
:class:`~hydrolog.exceptions.InvalidParameterError`. ``details.reason`` says what:
``shape``, ``unknown_schema``, ``unknown_field``, ``missing_field``, ``type``,
``unknown_type``, ``unknown_method``, ``unknown_kind``, ``unknown_model``,
``unknown_hietogram_type``, ``conflict``, the reasons of the nodes and of the reaches
(``invalid_id``, ``reserved_name``, ``upstream_count``, ``duplicate_upstream``,
``reservoir_model``...), those of a description (``empty``, ``too_long``,
``control_character``) and of a position (``minimum``, ``maximum``), and the structure
reasons of :class:`~hydrolog.routing.RoutingNetwork` (``unknown_upstream``, ``cycle``,
``several_downstream``, ``no_outlet``...); ``details.node_id`` names the node and
``details.field`` the field (``rainfall.total_mm`` for a field of an object inside a
node, ``position.x`` for a coordinate).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final, NoReturn

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import shown
from hydrolog.routing._order import ordered
from hydrolog.routing._reading import within
from hydrolog.routing.network import (
    NODE_TYPES,
    Node,
    NodeEntry,
    RoutingNetwork,
    Subcatchment,
    check_description,
    check_graph,
    check_links,
    check_unique,
    upstream_from_document,
)
from hydrolog.routing.rainfall import (
    RainfallSource,
    rainfall_from_document,
    rainfall_to_document,
)

__all__ = ["SCHEMA", "Prepare", "read_network", "write_network"]

SCHEMA: Final = "hydrolog-network/1"
"""Value of the ``schema`` key of a network document."""

Prepare = Callable[[str, str, Mapping[str, Any]], Mapping[str, Any]]
"""``prepare(node_id, type, entry)``: returns the entry that is read in place of the one
the document has (see :func:`read_network`)."""

_TOP_LEVEL: Final = (
    "schema",
    "name",
    "description",
    "timestep_min",
    "rainfall",
    "nodes",
)


def _fail(
    message: str, *, reason: str, hint: str | None = None, **details: object
) -> NoReturn:
    """Raise the error of a document that is not valid."""
    raise InvalidParameterError(
        message, details={"reason": reason, **details}, hint=hint
    )


@dataclass(frozen=True)
class _Record:
    """A node as the document says it: the class, the id and what it reads."""

    cls: type[Node]
    id: str
    entry: NodeEntry


def _identify(index: int, entry: object) -> tuple[Mapping[str, Any], str, type[Node]]:
    """Return a node of the document with its id and its class.

    ``index`` is its position in the list (from 0). Both readers start a node here.
    """
    if not isinstance(entry, Mapping):
        _fail(f"node {index + 1} is not an object", reason="shape", index=index)
    node_id = entry.get("id")
    if node_id is None:
        _fail(
            f"node {index + 1} has no 'id'",
            reason="missing_field",
            field="id",
            index=index,
        )
    if not isinstance(node_id, str):
        _fail(
            f"node {index + 1} has the id {shown(node_id)}, which is not a string",
            reason="invalid_id",
            node_id=shown(node_id),
            index=index,
        )
    kind = entry.get("type")
    if kind is None:
        _fail(
            f"Node {node_id!r} has no 'type'",
            reason="missing_field",
            node_id=node_id,
            field="type",
        )
    return (
        entry,
        node_id,
        NODE_TYPES.resolve(kind, f"Node {node_id!r}", node_id=node_id),
    )


def _read_entry(index: int, entry: object, prepare: Prepare | None) -> _Record:
    """Read one node of the document; ``index`` is its position in the list (from 0)."""
    fields, node_id, cls = _identify(index, entry)
    if prepare is not None:
        fields = prepare(node_id, cls.kind, fields)
    return _Record(cls, node_id, cls.read_entry(node_id, fields))


def _object(document: object) -> Mapping[str, Any]:
    """Return the document when it is an object."""
    if not isinstance(document, Mapping):
        _fail(
            f"the document must be a JSON object, not {type(document).__name__}",
            reason="shape",
            hint=f"A network is an object with the fields {', '.join(_TOP_LEVEL)}.",
        )
    return document


def _check_schema(document: Mapping[str, Any]) -> None:
    """Refuse a document without ``schema`` or of another schema."""
    if "schema" not in document:
        _fail(
            "the document has no 'schema'",
            reason="missing_field",
            field="schema",
            hint=f'Every document begins with "schema": "{SCHEMA}".',
        )
    schema = document["schema"]
    if schema != SCHEMA:
        _fail(
            f"the schema is {shown(schema)}, this reads {SCHEMA}",
            reason="unknown_schema",
            value=shown(schema),
            expected=SCHEMA,
        )


def _entries(document: Mapping[str, Any]) -> list[Any]:
    """Return the list of the nodes of the document."""
    entries = document.get("nodes")
    if entries is None:
        _fail(
            "the document has no 'nodes'",
            reason="missing_field",
            field="nodes",
            hint="'nodes' is the list of the nodes of the network.",
        )
    if not isinstance(entries, list):
        _fail(
            f"'nodes' must be a list, not {type(entries).__name__}",
            reason="type",
            field="nodes",
        )
    return entries


def read_network(document: object, *, prepare: Prepare | None = None) -> RoutingNetwork:
    """Read a network from a ``hydrolog-network/1`` document.

    Parameters
    ----------
    document : mapping
        The document (see the module docstring); values are JSON-native.
    prepare : callable, optional
        Called as ``prepare(node_id, type, entry)`` for every node, after its ``type``
        is known and before it is read: it returns the entry (a mapping) that is read
        in place of the one the document has. A front door that takes the values of a
        node from files uses it. An error that it raises is not changed.

    Returns
    -------
    RoutingNetwork
        The network, checked.

    Raises
    ------
    InvalidParameterError
        If the document is not valid (see the module docstring).
    """
    top = _object(document)
    for key in top:
        if key not in _TOP_LEVEL:
            _fail(
                f"the document has the unknown field {shown(key)!r}",
                reason="unknown_field",
                field=shown(key),
                allowed=list(_TOP_LEVEL),
                hint=f"The fields are {', '.join(_TOP_LEVEL)}.",
            )
    _check_schema(top)
    name = top.get("name")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        _fail(
            "the name of the network must be a non-blank string",
            reason="type",
            field="name",
            value=shown(name),
        )
    description = top.get("description")
    if description is not None:
        check_description(description)
    entries = _entries(top)
    records = [
        _read_entry(index, entry, prepare) for index, entry in enumerate(entries)
    ]
    check_unique([record.id for record in records])
    by_id = {record.id: record for record in records}
    nodes: dict[str, Node] = {}
    for node_id in ordered({record.id: record.entry.upstream for record in records}):
        record = by_id[node_id]
        nodes[node_id] = record.cls.build(
            node_id, record.entry, [nodes[up] for up in record.entry.upstream]
        )
    rainfall: RainfallSource | None = None
    if top.get("rainfall") is not None:
        with within("rainfall"):
            rainfall = rainfall_from_document(top["rainfall"])
    return RoutingNetwork(
        list(nodes.values()),
        name=name,
        description=description,
        rainfall=rainfall,
        timestep_min=top.get("timestep_min"),
    )


@dataclass(frozen=True)
class NetworkStructure:
    """The structure of a network: its nodes, their kinds and links, and nothing else.

    What :func:`read_structure` reads of a document that may be a draft (ADR-0025):
    what the layout of the schematic needs, whatever values the nodes miss.

    Attributes
    ----------
    name : str or None
        The name of the network, when the document gives a non-blank one.
    timestep_min : float or None
        The time step of the network [min], when the document gives a positive one.
    order : tuple of str
        The ids in the order of evaluation, the order of
        :attr:`RoutingNetwork.order <hydrolog.routing.RoutingNetwork>`.
    outlet : str
        The id of the outlet.
    kinds : dict of str to str
        The kind of every node (its ``type``), in the order of evaluation.
    upstream : dict of str to tuple of str
        The ids that flow into every node (its ``from``), in the order of evaluation.
    areas : dict of str to float or None
        The ``watershed.area_km2`` of every headwater [km2] when every headwater is a
        subcatchment with a positive one, else ``None``: the areas that weigh the
        branches of the layout (ADR-0013).
    """

    name: str | None
    timestep_min: float | None
    order: tuple[str, ...]
    outlet: str
    kinds: dict[str, str]
    upstream: dict[str, tuple[str, ...]]
    areas: dict[str, float] | None


def _positive(value: object) -> float | None:
    """Return ``value`` as a float when it is a positive number, else ``None``."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def _area(node: Mapping[str, Any]) -> float | None:
    """Return the area of a node's watershed [km2] when it is a positive number."""
    watershed = node.get("watershed")
    return (
        _positive(watershed.get("area_km2")) if isinstance(watershed, Mapping) else None
    )


def read_structure(document: object) -> NetworkStructure:
    """Read the structure of a ``hydrolog-network/1`` document, which may be a draft.

    Of the document it reads ``schema``, ``name``, ``timestep_min``, each node's
    ``id``, ``type`` and ``from``, and the ``watershed.area_km2`` of each headwater
    (ADR-0025), and it checks the structure with the checks of the network
    (:func:`~hydrolog.routing.network.check_links` and
    :func:`~hydrolog.routing.network.check_graph`, which :func:`read_network` and
    :class:`RoutingNetwork` use too). Nothing else: any other field may be missing or
    wrong, a ``name`` that is not a non-blank string and a ``timestep_min`` that is not
    a positive number are left out, and no file that the document names is read.

    Parameters
    ----------
    document : mapping
        The document; values are JSON-native.

    Returns
    -------
    NetworkStructure
        The structure, checked.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``shape``, ``missing_field`` (``schema``, ``nodes``, a
        node's ``id`` or ``type``), ``unknown_schema``, ``type`` (``nodes``, a node's
        ``from``), ``unknown_type`` and the reasons of the structure: ``invalid_id``,
        ``reserved_name``, ``upstream_count``, ``duplicate_upstream``, ``empty``,
        ``duplicate_node``, ``unknown_upstream``, ``cycle``, ``several_downstream``,
        ``no_outlet``, ``several_outlets``, ``outlet_has_downstream`` and
        ``disconnected_node``, with ``details.node_id``. A document whose other fields
        are right gets from :func:`read_network` the same reason for the same node.

    Examples
    --------
    >>> draft = {"schema": "hydrolog-network/1", "nodes": [
    ...     {"id": "A", "type": "subcatchment"},
    ...     {"id": "R1", "type": "reach", "from": ["A"]},
    ...     {"id": "OUT", "type": "outlet", "from": ["R1"]}]}
    >>> read_structure(draft).order
    ('A', 'R1', 'OUT')
    """
    top = _object(document)
    _check_schema(top)
    links: list[tuple[str, type[Node], tuple[str, ...]]] = []
    heads: dict[str, float | None] = {}
    for index, entry in enumerate(_entries(top)):
        fields, node_id, cls = _identify(index, entry)
        upstream = upstream_from_document(fields.get("from"), node_id)
        check_links(node_id, cls, upstream)
        links.append((node_id, cls, upstream))
        if not upstream:
            heads[node_id] = _area(fields) if issubclass(cls, Subcatchment) else None
    order, outlet = check_graph(links)
    found = {node_id: (cls.kind, upstream) for node_id, cls, upstream in links}
    name = top.get("name")
    areas = {node_id: area for node_id, area in heads.items() if area is not None}
    return NetworkStructure(
        name=name if isinstance(name, str) and name.strip() else None,
        timestep_min=_positive(top.get("timestep_min")),
        order=tuple(order),
        outlet=outlet,
        kinds={node_id: found[node_id][0] for node_id in order},
        upstream={node_id: found[node_id][1] for node_id in order},
        areas=areas if len(areas) == len(heads) else None,
    )


def write_network(network: RoutingNetwork) -> dict[str, Any]:
    """Write a network as a ``hydrolog-network/1`` document.

    Parameters
    ----------
    network : RoutingNetwork
        The network.

    Returns
    -------
    dict
        The document, JSON-native: ``schema``, ``name``, ``description`` and
        ``timestep_min`` (only what was given), the default ``rainfall`` of the network
        and the ``nodes`` in the order of evaluation, each as its class writes it
        (:meth:`~hydrolog.routing.Node.to_document`).

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``unregistered`` if a class of the network is not in
        its registry: the document could not name it.
    """
    values: dict[str, Any] = {
        "schema": SCHEMA,
        "name": network.name,
        "description": network.description,
        "timestep_min": network.given_timestep_min,
        "rainfall": (
            None if network.rainfall is None else rainfall_to_document(network.rainfall)
        ),
        "nodes": [network.node(node_id).to_document() for node_id in network.order],
    }
    return {key: values[key] for key in _TOP_LEVEL if values[key] is not None}
