"""Read the network of ``route network``: ``hydrolog-network/1`` (ADR-0010, ADR-0012).

A network is a JSON object, inline (``network``) or in a file (``network_file``)::

    {
      "schema": "hydrolog-network/1",
      "name": "Upper catchment",
      "nodes": [
        {"id": "A", "type": "subcatchment"},
        {"id": "B", "type": "subcatchment", "value_column": "B_m3s"},
        {"id": "R1", "type": "reach", "from": ["A"], "method": "lag", "lag_min": 25},
        {"id": "J1", "type": "junction", "from": ["R1", "B"]},
        {"id": "D", "type": "reservoir", "from": ["J1"], "rating_file": "pond.csv"},
        {"id": "OUT", "type": "outlet", "from": ["D"]}
      ]
    }

``schema`` is required and must be ``hydrolog-network/1`` (every machine-readable
document has one, AGI-4.1). Every node has ``id``, ``type`` (the kinds of
:data:`~hydrolog.routing.NODE_TYPES`) and ``from``, the list of the ids that flow into
it. The other fields depend on the type, and a field that the type does not take is an
error:

==============  =====================================================================
type            fields
==============  =====================================================================
subcatchment    ``times_min`` with ``discharge_m3s`` (inline), or ``value_column``
                (the column of ``inflows_file``, by default the ``id``)
reach           ``method`` (``lag``, ``muskingum``, ``muskingum-cunge``, ``cascade`` or
                ``level-pool``), the options of ``route <method>`` that describe the
                element (:func:`hydrolog.catalog.groups.route.model_options`, validated
                by their catalog declaration), ``initial_outflow_m3s``, ``extend_min``
reservoir       the options of ``route level-pool``, ``initial_outflow_m3s``,
                ``extend_min``
junction        nothing more: it adds the hydrographs of its ``from``
outlet          nothing more: the end of the network
==============  =====================================================================

The document is read by :meth:`~hydrolog.routing.RoutingNetwork.from_document`, which
knows the values that a document holds. This module is the front door of the command:
it puts into the document what lives in files (a column of ``inflows_file``, a
``rating_file``), checks every value by the catalog declaration of its option and gives
the error the class of its source.

A ``rating_file`` is relative to the directory of ``network_file`` and must lie inside
it (after links are resolved): the path rules of a server (``--allow-dir``) see the
options of a call, not the files that a document names, so a document may only name
files in the directory of the file that is allowed. An inline network has no such
directory and cannot name files.

Errors
------
What is wrong with the document is an :class:`~hydrolog.exceptions.InputDataError` with
``details.path`` when it comes from a file and an
:class:`~hydrolog.exceptions.InvalidParameterError` with ``details.option`` ``network``
when it is inline. ``details.reason`` says what: ``shape``, ``unknown_schema``,
``unknown_field``, ``unknown_method``, ``missing_field``, ``type``, ``conflict``,
``inline_file``, ``path_outside``, the reason of the option that breaks its declaration
(``minimum``, ``choice``...) or of the element that refuses it (``one_of``,
``unstable_timestep``...), and the structure reasons of
:class:`~hydrolog.routing.RoutingNetwork` (``unknown_upstream``, ``cycle``,
``several_downstream``, ``no_outlet``...) and the refusal of an id that names a file
badly (``invalid_id``, ``reserved_name``); ``details.node_id`` names the node and
``details.field`` the field. A time axis that the sources do not share
(``timestep_mismatch``, ``start_mismatch``) stays a ``validation_error`` whatever the
source of the document: it is a fact of the data, not of the document.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

from hydrolog.catalog.groups.route import (
    DISCHARGE_M3S,
    EXTEND_MIN,
    INITIAL_OUTFLOW_M3S,
    MODEL_METHODS,
    NETWORK,
    TIMES_MIN,
    VALUE_COLUMN,
    model_options,
)
from hydrolog.catalog.inputs import (
    Table,
    load_rating,
    read_json,
    read_table,
    table_hydrograph,
)
from hydrolog.catalog.spec import Option
from hydrolog.exceptions import InputDataError, InvalidParameterError, NotFoundError
from hydrolog.routing import RoutingNetwork
from hydrolog.routing._checks import shown

__all__ = ["LoadedNetwork", "load_network"]

_COMMON: Final = ("id", "type", "from")
_RUN_FIELDS: Final = (INITIAL_OUTFLOW_M3S.name, EXTEND_MIN.name)
_SOURCE_FIELDS: Final = (TIMES_MIN.name, DISCHARGE_M3S.name, VALUE_COLUMN.name)
_KEPT: Final = frozenset({"timestep_mismatch", "start_mismatch"})
"""Reasons of :class:`RoutingNetwork` that stay ``validation_error`` (data facts)."""


@dataclass(frozen=True)
class LoadedNetwork:
    """A network read from its document.

    Attributes
    ----------
    network : RoutingNetwork
        The checked network, ready to route.
    rating_files : dict of str to pathlib.Path
        The rating file of each node that reads one, by node id (absolute, links
        resolved): the files the document names, which an output must not overwrite.
    """

    network: RoutingNetwork
    rating_files: dict[str, Path] = field(default_factory=dict)


@dataclass(frozen=True)
class _Where:
    """Where the document came from; it decides the class of an error about it."""

    path: Path | None

    def fail(
        self,
        message: str,
        *,
        reason: str,
        hint: str | None = None,
        **details: object,
    ) -> NoReturn:
        """Raise the error of a bad document: a data error for a file, else a value."""
        if self.path is not None:
            raise InputDataError(
                f"{self.path}: {message}",
                details={"path": str(self.path), "reason": reason, **details},
                hint=hint,
            )
        raise InvalidParameterError(
            f"Option 'network': {message}",
            details={"option": "network", "reason": reason, **details},
            hint=hint,
        )

    def convert(
        self, exc: InvalidParameterError, node_id: str | None = None
    ) -> NoReturn:
        """Raise the error of the document that carries the facts of ``exc``.

        The ``option`` that a library error names is a field of the document here, so
        it becomes ``details.field``.
        """
        details = dict(exc.details)
        reason = str(details.pop("reason", "invalid"))
        if "option" in details:
            details["field"] = details.pop("option")
        if node_id is not None:
            details.setdefault("node_id", node_id)
        message = str(exc)
        if node_id is not None and repr(node_id) not in message:
            message = f"Node {node_id!r}: {message}"
        self.fail(message, reason=reason, hint=exc.hint, **details)


class _Reader:
    """Prepares the nodes of a document: values from files, values by the catalog."""

    def __init__(
        self,
        where: _Where,
        base: Path | None,
        inflows_file: str | os.PathLike[str] | None,
        time_column: str | None,
    ) -> None:
        self.where = where
        self.base = base
        self.inflows_file = inflows_file
        self.time_column = time_column
        self.used_inflows = False
        self.rating_files: dict[str, Path] = {}
        self._table: Table | None = None

    # --- one node -------------------------------------------------------------------

    def prepare(
        self, node_id: str, kind: str, entry: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Return the node with its values in place, for the library to read.

        This is the ``prepare`` of
        :meth:`~hydrolog.routing.RoutingNetwork.from_document`: it is called for every
        node, in the order of the document, with the node as the document has it.
        """
        method = self._method(node_id, kind, entry)
        self._known_fields(node_id, kind, method, entry)
        fields = {key: entry[key] for key in _COMMON if key in entry}
        if kind == "subcatchment":
            fields.update(self._hydrograph(node_id, entry))
        elif kind in ("reach", "reservoir"):
            if method is not None:
                fields["method"] = method
            fields.update(self._element(node_id, method or "level-pool", entry))
            for option in (INITIAL_OUTFLOW_M3S, EXTEND_MIN):
                value = entry.get(option.name)
                if value is not None:
                    fields[option.name] = float(self._normalize(node_id, option, value))
        return fields

    def _method(self, node_id: str, kind: str, entry: Mapping[str, Any]) -> str | None:
        """Return the ``method`` of a reach; a reservoir routes by level pool."""
        if kind != "reach":
            return None
        method = entry.get("method")
        if method is None:
            self.where.fail(
                f"Node {node_id!r} is a reach and needs a 'method'",
                reason="missing_field",
                node_id=node_id,
                field="method",
                hint=f"The methods are {', '.join(MODEL_METHODS)}.",
            )
        if not isinstance(method, str) or method not in MODEL_METHODS:
            self.where.fail(
                f"Node {node_id!r} has the unknown method {shown(method)}",
                reason="unknown_method",
                node_id=node_id,
                value=shown(method),
                allowed=list(MODEL_METHODS),
                hint=f"The methods are {', '.join(MODEL_METHODS)}.",
            )
        return method

    def _known_fields(
        self, node_id: str, kind: str, method: str | None, entry: Mapping[str, Any]
    ) -> None:
        """Refuse a field that the type of the node does not take."""
        allowed: tuple[str, ...]
        if kind == "subcatchment":
            allowed = (*_COMMON, *_SOURCE_FIELDS)
        elif kind == "reach":
            assert method is not None  # _method refused a reach without one
            allowed = (
                *_COMMON,
                "method",
                *_RUN_FIELDS,
                *(option.name for option in model_options(method)),
            )
        elif kind == "reservoir":
            allowed = (
                *_COMMON,
                *_RUN_FIELDS,
                *(option.name for option in model_options("level-pool")),
            )
        else:
            allowed = _COMMON
        for key in entry:
            if key not in allowed:
                self.where.fail(
                    f"Node {node_id!r} is a {kind} and takes no {shown(key)}",
                    reason="unknown_field",
                    node_id=node_id,
                    field=shown(key),
                    allowed=list(allowed),
                    hint=f"A {kind} takes {', '.join(allowed)}.",
                )

    # --- what a node holds ----------------------------------------------------------

    def _normalize(self, node_id: str, option: Option, value: object) -> Any:
        """Validate a field by the catalog declaration of the option of that name."""
        try:
            return option.normalize(value)
        except InvalidParameterError as exc:
            self.where.convert(exc, node_id)

    def _inflows(self, node_id: str) -> Table:
        """Return the table of ``inflows_file``, read at the first need."""
        if self.inflows_file is None:
            self.where.fail(
                f"Node {node_id!r} is a subcatchment without discharges",
                reason="missing_field",
                node_id=node_id,
                field="discharge_m3s",
                hint="Give 'times_min' with 'discharge_m3s' in the node, or give the "
                "option inflows_file with a column for the node.",
            )
        if self._table is None:
            self._table = read_table(self.inflows_file)
        self.used_inflows = True
        return self._table

    def _hydrograph(self, node_id: str, entry: Mapping[str, Any]) -> dict[str, Any]:
        """Return the discharges of a subcatchment, inline: from the node or a file."""
        times = entry.get(TIMES_MIN.name)
        values = entry.get(DISCHARGE_M3S.name)
        column = entry.get(VALUE_COLUMN.name)
        if times is not None or values is not None:
            absent = TIMES_MIN.name if times is None else DISCHARGE_M3S.name
            if times is None or values is None:
                self.where.fail(
                    f"Node {node_id!r} needs '{absent}' next to the other inline list",
                    reason="missing_field",
                    node_id=node_id,
                    field=absent,
                )
            if column is not None:
                self.where.fail(
                    f"Node {node_id!r}: 'value_column' names a column of inflows_file "
                    "and does not go with inline discharges",
                    reason="conflict",
                    node_id=node_id,
                    field=VALUE_COLUMN.name,
                )
            return {
                TIMES_MIN.name: self._normalize(node_id, TIMES_MIN, times),
                DISCHARGE_M3S.name: self._normalize(node_id, DISCHARGE_M3S, values),
            }
        table = self._inflows(node_id)
        name = (
            node_id
            if column is None
            else str(self._normalize(node_id, VALUE_COLUMN, column))
        )
        try:
            hydrograph = table_hydrograph(table, self.time_column, name)
        except InputDataError as exc:
            raise InputDataError(
                f"Node {node_id!r}: {exc}",
                details={**exc.details, "node_id": node_id},
                hint=exc.hint,
            ) from exc
        return {
            TIMES_MIN.name: hydrograph.times_min.tolist(),
            DISCHARGE_M3S.name: hydrograph.discharge_m3s.tolist(),
        }

    def _element(
        self, node_id: str, method: str, entry: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Return the options of the element of a reach or a reservoir, validated."""
        options = model_options(method)
        given: dict[str, Any] = {}
        for option in options:
            value = entry.get(option.name)
            if value is not None:
                given[option.name] = self._normalize(node_id, option, value)
        for option in options:
            if option.required and option.name not in given:
                self.where.fail(
                    f"Node {node_id!r} routes by {method} and needs {option.name!r}",
                    reason="missing_field",
                    node_id=node_id,
                    field=option.name,
                )
        if method == "level-pool":
            return self._level_pool(node_id, given)
        return given

    def _level_pool(self, node_id: str, given: Mapping[str, Any]) -> dict[str, Any]:
        """Return the table of a level pool, inline: from the node or a rating file."""
        name = given.get("rating_file")
        path = None if name is None else self._rating_path(node_id, name)
        try:
            rating = load_rating(
                storage_m3=given.get("storage_m3"),
                outflow_m3s=given.get("outflow_m3s"),
                stage_m=given.get("stage_m"),
                rating_file=path,
            )
        except InvalidParameterError as exc:
            self.where.convert(exc, node_id)
        except (InputDataError, NotFoundError) as exc:
            raise type(exc)(
                f"Node {node_id!r}: {exc}",
                details={**exc.details, "node_id": node_id},
                hint=exc.hint,
            ) from exc
        fields: dict[str, Any] = {
            "storage_m3": rating.storage_m3,
            "outflow_m3s": rating.outflow_m3s,
        }
        if rating.stage_m is not None:
            fields["stage_m"] = rating.stage_m
        if "subreaches" in given:
            fields["subreaches"] = given["subreaches"]
        return fields

    def _rating_path(self, node_id: str, name: str) -> Path:
        """Resolve a ``rating_file`` against the directory of the network file."""
        if self.base is None:
            self.where.fail(
                f"Node {node_id!r} names the rating file {shown(name)}, which an "
                "inline network cannot do",
                reason="inline_file",
                node_id=node_id,
                field="rating_file",
                hint="Give the network as network_file with the rating file beside it, "
                "or give the table inline (storage_m3 and outflow_m3s).",
            )
        resolved = Path(os.path.realpath(self.base / name))
        if not resolved.is_relative_to(self.base):
            self.where.fail(
                f"The rating file {shown(name)} of node {node_id!r} lies outside the "
                f"directory of the network file ({self.base})",
                reason="path_outside",
                node_id=node_id,
                field="rating_file",
                value=shown(name),
                hint="Put the rating file in the directory of the network file or "
                "below it.",
            )
        self.rating_files[node_id] = resolved
        return resolved


def _document(
    network: Mapping[str, Any] | None,
    network_file: str | os.PathLike[str] | None,
) -> tuple[object, _Where, Path | None]:
    """Return the document, where it came from and the directory it names files in."""
    if (network is None) == (network_file is None):
        raise InvalidParameterError(
            "Give either 'network' or 'network_file'",
            details={
                "option": "network_file" if network_file is not None else "network",
                "reason": "one_of",
                "groups": [["network"], ["network_file"]],
            },
        )
    if network_file is not None:
        path = Path(os.fspath(network_file)).expanduser()
        document = read_json(path)
        return document, _Where(path), Path(os.path.realpath(path)).parent
    # a value that is not an object is reported by the reader, like one from a file
    document = NETWORK.normalize(network) if isinstance(network, Mapping) else network
    return document, _Where(None), None


def load_network(
    *,
    network: Mapping[str, Any] | None = None,
    network_file: str | os.PathLike[str] | None = None,
    inflows_file: str | os.PathLike[str] | None = None,
    time_column: str | None = None,
) -> LoadedNetwork:
    """Read and check a network document (see the module docstring).

    Parameters
    ----------
    network : Mapping, optional
        The document inline: JSON-native values (numbers, strings, lists, objects).
    network_file : str or os.PathLike, optional
        JSON file with the document, instead of ``network``; the rating files of the
        nodes are read from its directory.
    inflows_file : str or os.PathLike, optional
        CSV or JSON file with a time column and a discharge column per subcatchment
        that has no inline discharges; read when a subcatchment needs it.
    time_column : str, optional
        Name of the time column [min] of ``inflows_file``; default ``time_min``.

    Returns
    -------
    LoadedNetwork
        The network and the rating files it reads.

    Raises
    ------
    InvalidParameterError
        If both or neither of ``network`` and ``network_file`` are given
        (``details.reason`` ``one_of``), ``time_column`` is given without
        ``inflows_file`` or ``inflows_file`` is given and no subcatchment reads it
        (``details.reason`` ``conflict``), the inline document is wrong (see the module
        docstring), or the sources have different time axes.
    NotFoundError
        If a file does not exist.
    InputDataError
        If a file cannot be read, the document in the file is wrong (see the module
        docstring) or a table of ``inflows_file`` or a rating file breaks a rule.
    """
    document, where, base = _document(network, network_file)
    if time_column is not None and inflows_file is None:
        raise InvalidParameterError(
            "Option 'time_column' applies to 'inflows_file', which is not given",
            details={"option": "time_column", "reason": "conflict"},
        )
    reader = _Reader(where, base, inflows_file, time_column)
    try:
        built = RoutingNetwork.from_document(document, prepare=reader.prepare)
    except InvalidParameterError as exc:
        # the reader has made the error of the document when it names the option
        # `network`; the time axes of the data stay what they are
        if exc.details.get("option") == "network" or exc.details.get("reason") in _KEPT:
            raise
        where.convert(exc)
    if inflows_file is not None and not reader.used_inflows:
        raise InvalidParameterError(
            "Option 'inflows_file' is not used: no subcatchment of the network reads "
            "its discharges from it",
            details={"option": "inflows_file", "reason": "conflict"},
            hint="Leave the inline discharges out of a subcatchment to read its "
            "column, or leave out inflows_file.",
        )
    return LoadedNetwork(built, reader.rating_files)
