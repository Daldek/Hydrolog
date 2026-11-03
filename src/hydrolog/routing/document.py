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

Errors
------
What is wrong with the document is an
:class:`~hydrolog.exceptions.InvalidParameterError`. ``details.reason`` says what:
``shape``, ``unknown_schema``, ``unknown_field``, ``missing_field``, ``type``,
``unknown_type``, ``unknown_method``, ``unknown_kind``, ``unknown_model``,
``unknown_hietogram_type``, ``conflict``, the reasons of the nodes and of the reaches
(``invalid_id``, ``reserved_name``, ``upstream_count``, ``duplicate_upstream``,
``reservoir_model``...) and the structure reasons of
:class:`~hydrolog.routing.RoutingNetwork` (``unknown_upstream``, ``cycle``,
``several_downstream``, ``no_outlet``...); ``details.node_id`` names the node and
``details.field`` the field (``rainfall.total_mm`` for a field of an object inside a
node).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final, NoReturn

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import shown
from hydrolog.routing._order import ordered
from hydrolog.routing._reading import within
from hydrolog.routing.network import NODE_TYPES, Node, RoutingNetwork, check_unique
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

_TOP_LEVEL: Final = ("schema", "name", "timestep_min", "rainfall", "nodes")


def _fail(
    message: str, *, reason: str, hint: str | None = None, **details: object
) -> NoReturn:
    """Raise the error of a document that is not valid."""
    raise InvalidParameterError(
        message, details={"reason": reason, **details}, hint=hint
    )


@dataclass(frozen=True)
class _Record:
    """A node as the document says it: the class, the id, the inflows and the fields."""

    cls: type[Node]
    id: str
    upstream: tuple[str, ...]
    arguments: dict[str, Any]


def _read_entry(index: int, entry: object, prepare: Prepare | None) -> _Record:
    """Read one node of the document; ``index`` is its position in the list (from 0)."""
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
    cls = NODE_TYPES.resolve(kind, f"Node {node_id!r}", node_id=node_id)
    fields = entry if prepare is None else prepare(node_id, cls.kind, entry)
    upstream, arguments = cls.read_entry(node_id, fields)
    return _Record(cls, node_id, upstream, arguments)


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
    if not isinstance(document, Mapping):
        _fail(
            f"the document must be a JSON object, not {type(document).__name__}",
            reason="shape",
            hint=f"A network is an object with the fields {', '.join(_TOP_LEVEL)}.",
        )
    for key in document:
        if key not in _TOP_LEVEL:
            _fail(
                f"the document has the unknown field {shown(key)!r}",
                reason="unknown_field",
                field=shown(key),
                allowed=list(_TOP_LEVEL),
                hint=f"The fields are {', '.join(_TOP_LEVEL)}.",
            )
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
    name = document.get("name")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        _fail(
            "the name of the network must be a non-blank string",
            reason="type",
            field="name",
            value=shown(name),
        )
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
    records = [
        _read_entry(index, entry, prepare) for index, entry in enumerate(entries)
    ]
    check_unique([record.id for record in records])
    by_id = {record.id: record for record in records}
    nodes: dict[str, Node] = {}
    for node_id in ordered({record.id: record.upstream for record in records}):
        record = by_id[node_id]
        nodes[node_id] = record.cls.build(
            node_id, record.arguments, [nodes[up] for up in record.upstream]
        )
    rainfall: RainfallSource | None = None
    if document.get("rainfall") is not None:
        with within("rainfall"):
            rainfall = rainfall_from_document(document["rainfall"])
    return RoutingNetwork(
        list(nodes.values()),
        name=name,
        rainfall=rainfall,
        timestep_min=document.get("timestep_min"),
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
        The document, JSON-native: ``schema``, ``name`` and ``timestep_min`` (only what
        was given), the default ``rainfall`` of the network and the ``nodes`` in the
        order of evaluation, each as its class writes it
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
        "timestep_min": network.given_timestep_min,
        "rainfall": (
            None if network.rainfall is None else rainfall_to_document(network.rainfall)
        ),
        "nodes": [network.node(node_id).to_document() for node_id in network.order],
    }
    return {key: values[key] for key in _TOP_LEVEL if values[key] is not None}
