"""Offline builders of the documents and files that other projects read from Hydrolog.

Projects that read Hydrolog's files (Hydraulik reads the hydrograph tables of ``route
network --output-dir`` and the envelope of ``precip hietogram``; Hydrograf writes
``hydrolog-network/1`` documents) test their readers and writers against instances
built here instead of hand-written copies of the formats (DEV-10.6). Everything is
produced by the REAL code of the library: a table is written by
:meth:`Hydrograph.to_table`, a document is read back by the loader of ``route
network`` before it is returned, the tables of a network are routed by
:class:`RoutingNetwork` and an envelope is the one that ``run_command`` makes. So an
instance cannot drift from the format: a change of a format changes the instance, and
the contract test of a consumer sees it when it moves to the new Hydrolog.
``tests/contract/test_testing_module.py`` compares every builder with the files that
the ``hydrolog`` program writes.

Nothing here touches the network or the clock, the output is deterministic (two calls
with the same arguments give byte-identical text) and every written file is UTF-8 with
Unix line ends, as Hydrolog writes it.

Documents
---------
:func:`subcatchment`, :func:`reach`, :func:`junction`, :func:`outlet` and
:func:`network_document` build a ``hydrolog-network/1`` document that has no file: a
network document can name files (``rating_file``) only when it is itself a file, so
these builders make the nodes of a network that is inline or written by
:func:`write_network_document`. A subcatchment that makes its own hydrograph takes the
objects that :func:`watershed`, :func:`curve_number_runoff`, :func:`design_storm` and
:func:`rainfall_series` build (ADR-0012; each is read by the real reader of its kind
before it is returned), and :func:`network_document` the ``timestep_min`` and the
default ``rainfall`` of the network. :func:`example_network_document` is such a network
of three subcatchments and :func:`example_network` the
:class:`~hydrolog.routing.RoutingNetwork` that it makes, in memory.

Files
-----
:func:`hydrograph_table` is the text of a hydrograph table (``time_min,discharge_m3s``),
:func:`network_tables` the tables ``<id>.csv`` that ``route network --output-dir``
writes for an inline network and :func:`write_network_tables` writes them into a
directory. :func:`build_network_fixture` writes a small complete case (the network
document, its inflows and the tables the command makes of them) for a test that calls
``hydrolog route network`` itself or reads its tables.

Envelopes
---------
:func:`hietogram_envelope` is the ``hydrolog-result/1`` envelope of ``precip hietogram``
(what ``hydrolog precip hietogram --json`` prints) and :func:`write_hietogram_envelope`
writes it as a file.

Examples
--------
>>> from hydrolog.testing import hydrograph_table
>>> print(hydrograph_table([0, 5, 10], [0.0, 0.5, 0.0]), end="")
time_min,discharge_m3s
0.0,0.0
5.0,0.5
10.0,0.0
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from hydrolog.operations._network_input import load_network
from hydrolog.routing import Hydrograph, RoutingNetwork
from hydrolog.routing.document import SCHEMA as NETWORK_SCHEMA
from hydrolog.routing.rainfall import rainfall_from_document
from hydrolog.routing.runoff import runoff_from_document, watershed_from_document

__all__ = [
    "EXAMPLE_INFLOWS",
    "EXAMPLE_TIMES_MIN",
    "NETWORK_SCHEMA",
    "NetworkFixture",
    "build_network_fixture",
    "curve_number_runoff",
    "design_storm",
    "example_network",
    "example_network_document",
    "hietogram_envelope",
    "hydrograph_table",
    "junction",
    "network_document",
    "network_tables",
    "outlet",
    "rainfall_series",
    "reach",
    "subcatchment",
    "watershed",
    "write_hietogram_envelope",
    "write_network_document",
    "write_network_tables",
]

EXAMPLE_TIMES_MIN: Final[tuple[float, ...]] = (0, 5, 10, 15, 20, 25, 30, 35, 40)
"""Time axis [min] of the inflows of :func:`build_network_fixture`."""

EXAMPLE_INFLOWS: Final[Mapping[str, tuple[float, ...]]] = {
    "A": (0.0, 0.04, 0.12, 0.2, 0.16, 0.1, 0.05, 0.02, 0.0),
    "tributary_B": (0.0, 0.02, 0.06, 0.08, 0.05, 0.02, 0.01, 0.0, 0.0),
}
"""Discharges [m3/s] of the two subcatchments of :func:`build_network_fixture`, by the
column of the inflows table."""


# --- network documents --------------------------------------------------------------


def subcatchment(
    node_id: str,
    *,
    times_min: Sequence[float] | None = None,
    discharge_m3s: Sequence[float] | None = None,
    value_column: str | None = None,
    watershed: Mapping[str, Any] | None = None,
    runoff: Mapping[str, Any] | None = None,
    rainfall: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a ``subcatchment`` node.

    A subcatchment is given its hydrograph (``times_min`` with ``discharge_m3s``, or a
    column of the inflows file) or makes it (``watershed``, ``runoff`` and, unless the
    network has a ``rainfall`` for it, ``rainfall``).

    Parameters
    ----------
    node_id : str
        Id of the node (it names the table ``<id>.csv``).
    times_min, discharge_m3s : sequence of float, optional
        The hydrograph inline, both together.
    value_column : str, optional
        Column of the inflows file that holds the discharges; without it and without
        an inline hydrograph the column is named like the node.
    watershed, runoff, rainfall : mapping, optional
        The objects of a subcatchment that makes its hydrograph, from
        :func:`watershed`, :func:`curve_number_runoff`, :func:`design_storm` or
        :func:`rainfall_series`; not with a hydrograph.

    Returns
    -------
    dict
        The node, with only the fields that were given.
    """
    node: dict[str, Any] = {"id": node_id, "type": "subcatchment"}
    if times_min is not None:
        node["times_min"] = list(times_min)
    if discharge_m3s is not None:
        node["discharge_m3s"] = list(discharge_m3s)
    if value_column is not None:
        node["value_column"] = value_column
    for field, value in (
        ("watershed", watershed),
        ("runoff", runoff),
        ("rainfall", rainfall),
    ):
        if value is not None:
            node[field] = dict(value)
    return node


def reach(
    node_id: str, upstream: str, *, method: str = "lag", **options: Any
) -> dict[str, Any]:
    """Return a ``reach`` node that routes the hydrograph of ``upstream``.

    Parameters
    ----------
    node_id : str
        Id of the node.
    upstream : str
        Id of the node that flows into the reach.
    method : str, optional
        ``lag``, ``muskingum``, ``muskingum-cunge``, ``cascade`` or ``level-pool``.
    **options
        The options of ``route <method>`` that describe the element (``lag_min``;
        ``k_min`` and ``x``; ...), ``initial_outflow_m3s`` and ``extend_min``.
    """
    return {
        "id": node_id,
        "type": "reach",
        "from": [upstream],
        "method": method,
        **options,
    }


def junction(node_id: str, *upstream: str) -> dict[str, Any]:
    """Return a ``junction`` node that adds the hydrographs of ``upstream``."""
    return {"id": node_id, "type": "junction", "from": list(upstream)}


def outlet(upstream: str, node_id: str = "OUT") -> dict[str, Any]:
    """Return the ``outlet`` node that ends the network after ``upstream``."""
    return {"id": node_id, "type": "outlet", "from": [upstream]}


def watershed(
    *,
    area_km2: float = 12.0,
    perimeter_km: float = 18.0,
    length_km: float = 6.0,
    elevation_min_m: float = 210.0,
    elevation_max_m: float = 330.0,
    cn: float | None = 75,
    **options: Any,
) -> dict[str, Any]:
    """Return the ``watershed`` of a subcatchment that makes its hydrograph.

    The object of :class:`~hydrolog.morphometry.WatershedParameters`; the defaults are
    a small catchment of 12 km2 with a curve number of 75.

    Parameters
    ----------
    area_km2, perimeter_km, length_km : float, optional
        Area [km2], perimeter [km] and length [km] of the area.
    elevation_min_m, elevation_max_m : float, optional
        Lowest and highest point [m a.s.l.].
    cn : float, optional
        Curve number; ``None`` leaves it out (a model that needs it then refuses the
        subcatchment).
    **options
        The other fields of ``WatershedParameters`` (``name``, ``crs``...).

    Returns
    -------
    dict
        The object, JSON-native.

    Raises
    ------
    hydrolog.InvalidParameterError
        If a field is not one of the class or its value is not valid.
    """
    document: dict[str, Any] = {
        "area_km2": area_km2,
        "perimeter_km": perimeter_km,
        "length_km": length_km,
        "elevation_min_m": elevation_min_m,
        "elevation_max_m": elevation_max_m,
    }
    if cn is not None:
        document["cn"] = cn
    document.update(options)
    watershed_from_document(document)
    return document


def curve_number_runoff(**options: Any) -> dict[str, Any]:
    """Return the ``runoff`` of the model ``curve-number``.

    Parameters
    ----------
    **options
        The options of ``hydrograph generate`` that the model takes (``tc_min`` or
        ``tc_method``, ``ia_coefficient``, ``amc``, ``uh_model``, ``nash_n``...); none
        gives the Kirpich time of concentration, the SCS unit hydrograph and AMC II.

    Returns
    -------
    dict
        The object with its ``model``, JSON-native.

    Raises
    ------
    hydrolog.InvalidParameterError
        If an option is not one of the model, does not apply to its unit hydrograph or
        is out of range.
    """
    document: dict[str, Any] = {"model": "curve-number", **options}
    runoff_from_document(document)
    return document


def design_storm(
    *,
    hietogram_type: str = "euler_ii",
    total_mm: float = 40.0,
    duration_min: float = 60.0,
    **shape: float,
) -> dict[str, Any]:
    """Return a ``rainfall`` of the kind ``design``: a depth over a duration.

    Parameters
    ----------
    hietogram_type : {"block", "triangular", "beta", "euler_ii"}, optional
        The shape of the storm, by default ``euler_ii``.
    total_mm : float, optional
        Total depth [mm], by default 40.
    duration_min : float, optional
        Duration [min], by default 60.
    **shape
        ``alpha`` and ``beta`` or ``peak_position``, where the shape takes them.

    Returns
    -------
    dict
        The object with its ``kind``, JSON-native.

    Raises
    ------
    hydrolog.InvalidParameterError
        If the shape is unknown, takes no such option, or a value is out of range.
    """
    document: dict[str, Any] = {
        "kind": "design",
        "hietogram_type": hietogram_type,
        "total_mm": total_mm,
        "duration_min": duration_min,
        **shape,
    }
    rainfall_from_document(document)
    return document


def rainfall_series(
    depths_mm: Sequence[float] = (0.0, 2.0, 8.0, 12.0, 6.0, 2.0, 0.0),
    timestep_min: float = 10.0,
) -> dict[str, Any]:
    """Return a ``rainfall`` of the kind ``series``: the depth of every time step.

    Parameters
    ----------
    depths_mm : sequence of float, optional
        The depth of rain of each step [mm], from time 0; the default has 30 mm.
    timestep_min : float, optional
        The time step of the record [min], by default 10; a network that has another
        step refuses the series, nothing is resampled.

    Returns
    -------
    dict
        The object with its ``kind``, JSON-native.

    Raises
    ------
    hydrolog.InvalidParameterError
        If the depths or the step are not valid.
    """
    document: dict[str, Any] = {
        "kind": "series",
        "depths_mm": [float(depth) for depth in depths_mm],
        "timestep_min": timestep_min,
    }
    rainfall_from_document(document)
    return document


def _checkable(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``document`` in which every source that reads a file is inline.

    A subcatchment that names a column of the inflows file has no discharges in the
    document; the loader needs them to check the rest, so such a node gets a flat
    hydrograph on the time axis of the first inline source (or a short default one, at
    the time step of the network). A subcatchment that makes its hydrograph is left as
    it is.
    """
    nodes: Sequence[Mapping[str, Any]] = document["nodes"]
    step = document.get("timestep_min", 5)
    axis: list[float] = [0, step, 2 * step]
    for node in nodes:
        if "times_min" in node and "discharge_m3s" in node:
            axis = list(node["times_min"])
            break
    checked: list[dict[str, Any]] = []
    for node in nodes:
        copy = dict(node)
        if copy.get("type") == "subcatchment" and not any(
            field in copy
            for field in (
                "times_min",
                "discharge_m3s",
                "watershed",
                "runoff",
                "rainfall",
            )
        ):
            copy.pop("value_column", None)
            copy["times_min"] = axis
            copy["discharge_m3s"] = [0.0] * len(axis)
        checked.append(copy)
    return {**document, "nodes": checked}


def network_document(
    *nodes: Mapping[str, Any],
    name: str | None = None,
    timestep_min: float | None = None,
    rainfall: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a checked ``hydrolog-network/1`` document of ``nodes``.

    The nodes keep the order given (the order of nodes changes no result). The
    document is read by the loader of ``route network`` before it is returned, so it is
    a valid network: one outlet, no cycle, every ``from`` an id of the document, every
    field and option valid for its type. A subcatchment that reads the inflows file
    (:func:`subcatchment` without a hydrograph or the means to make one) is checked as
    if it were inline.

    Parameters
    ----------
    *nodes : mapping
        Nodes from :func:`subcatchment`, :func:`reach`, :func:`junction` and
        :func:`outlet`.
    name : str, optional
        Name of the network.
    timestep_min : float, optional
        The time step of the network [min]; without it the step of the sources.
    rainfall : mapping, optional
        The rainfall of every subcatchment that makes its hydrograph and has none of its
        own, from :func:`design_storm` or :func:`rainfall_series`.

    Returns
    -------
    dict
        The document, JSON-native.

    Raises
    ------
    hydrolog.InvalidParameterError
        If the document is not a valid network (``details.reason``, ``node_id``).
    """
    document: dict[str, Any] = {"schema": NETWORK_SCHEMA}
    if name is not None:
        document["name"] = name
    if timestep_min is not None:
        document["timestep_min"] = timestep_min
    if rainfall is not None:
        document["rainfall"] = dict(rainfall)
    document["nodes"] = [dict(node) for node in nodes]
    load_network(network=_checkable(document))
    return document


def write_network_document(
    path: str | os.PathLike[str], document: Mapping[str, Any]
) -> Path:
    """Write ``document`` as the JSON file ``route network`` reads; return its path."""
    target = Path(os.fspath(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def example_network_document() -> dict[str, Any]:
    """Return the document of a network of three subcatchments that make hydrographs.

    ``A`` has a design storm of its own (Euler II, 45 mm in 60 min), ``B`` a record of
    38 mm in steps of 5 min and ``C`` none: it takes the default of the network, a block
    storm of 30 mm in 60 min. ``A`` and ``B`` take the time of concentration from their
    watersheds (Kirpich), ``C`` is given 60 min. ``A`` reaches the junction ``J1`` by a
    lag reach of 25 min, where ``B`` joins it, a Muskingum reach (K 40 min, X 0.2)
    carries them to ``J2``, where ``C`` joins, and ``OUT`` ends the network. The time
    step is that of the record of ``B``, 5 min.

    Returns
    -------
    dict
        The document, JSON-native, checked by the loader of ``route network``.
    """
    return network_document(
        subcatchment(
            "A",
            watershed=watershed(),
            runoff=curve_number_runoff(),
            rainfall=design_storm(total_mm=45.0),
        ),
        subcatchment(
            "B",
            watershed=watershed(
                area_km2=5.0,
                perimeter_km=11.0,
                length_km=3.5,
                elevation_max_m=290.0,
                cn=70,
            ),
            runoff=curve_number_runoff(),
            rainfall=rainfall_series([0.0, 2.0, 5.0, 10.0, 12.0, 6.0, 3.0], 5.0),
        ),
        subcatchment(
            "C",
            watershed=watershed(
                area_km2=8.0,
                perimeter_km=14.0,
                length_km=4.5,
                elevation_min_m=200.0,
                elevation_max_m=300.0,
                cn=72,
            ),
            runoff=curve_number_runoff(tc_min=60.0),
        ),
        reach("R_A", "A", method="lag", lag_min=25),
        junction("J1", "R_A", "B"),
        reach("R_J1", "J1", method="muskingum", k_min=40, x=0.2),
        junction("J2", "R_J1", "C"),
        outlet("J2"),
        name="Three subcatchments",
        rainfall=design_storm(hietogram_type="block", total_mm=30.0),
    )


def example_network() -> RoutingNetwork:
    """Return the network of :func:`example_network_document`, in memory.

    It is made by :meth:`RoutingNetwork.from_document
    <hydrolog.routing.RoutingNetwork.from_document>` from the document, so it is the
    network that a consumer reads from what it writes; ``example_network().route()``
    is a result with every kind of value: hydrographs, the rain of the three
    subcatchments, parameters that are given, computed and default.
    """
    return RoutingNetwork.from_document(example_network_document())


# --- hydrograph tables --------------------------------------------------------------


def hydrograph_table(times_min: Sequence[float], discharge_m3s: Sequence[float]) -> str:
    r"""Return the text of a hydrograph table, as Hydrolog writes it.

    Parameters
    ----------
    times_min : sequence of float
        Time [min], strictly increasing at a regular step.
    discharge_m3s : sequence of float
        Discharge [m3/s], finite and not negative.

    Returns
    -------
    str
        ``time_min,discharge_m3s`` and a row per ordinate; every number in its shortest
        exact form (``0.0``, ``6.29e-05``), ``"\n"`` line ends.

    Raises
    ------
    hydrolog.InvalidParameterError
        If the table is not a hydrograph (different lengths, an irregular step...).
    """
    return Hydrograph(times_min, discharge_m3s).to_table()


def network_tables(network: Mapping[str, Any]) -> dict[str, str]:
    """Return the tables that ``route network --output-dir`` writes for ``network``.

    Parameters
    ----------
    network : mapping
        A ``hydrolog-network/1`` document whose sources are all inline.

    Returns
    -------
    dict of str to str
        File name ``<id>.csv`` to the text of the table of the hydrograph that leaves
        the node, for every node, in the order of the computation (headwaters first).

    Raises
    ------
    hydrolog.InvalidParameterError
        If the document is not valid.
    """
    return _tables(load_network(network=network).network)


def _tables(graph: RoutingNetwork) -> dict[str, str]:
    run = graph.route()
    return {f"{node}.csv": run.hydrographs[node].to_table() for node in graph.order}


def _write_tables(directory: Path, tables: Mapping[str, str]) -> tuple[Path, ...]:
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, text in tables.items():
        path = directory / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return tuple(written)


def write_network_tables(
    directory: str | os.PathLike[str], network: Mapping[str, Any]
) -> tuple[Path, ...]:
    """Write the tables of :func:`network_tables` into ``directory`` (made if missing).

    Returns
    -------
    tuple of pathlib.Path
        The files written, in the order of :func:`network_tables`. Existing files of
        the same names are replaced: the directory belongs to the test.
    """
    return _write_tables(Path(os.fspath(directory)), network_tables(network))


# --- a complete case ----------------------------------------------------------------


@dataclass(frozen=True)
class NetworkFixture:
    """The files of :func:`build_network_fixture`.

    Attributes
    ----------
    network_file : pathlib.Path
        The network document (``--network-file``).
    inflows_file : pathlib.Path
        The inflows table (``--inflows-file``).
    output_dir : pathlib.Path
        The directory with the tables that ``route network --output-dir`` writes for
        the two files above.
    nodes : tuple of str
        The ids of the nodes, headwaters first; ``output_dir`` holds ``<id>.csv`` of
        each.
    """

    network_file: Path
    inflows_file: Path
    output_dir: Path
    nodes: tuple[str, ...]


def build_network_fixture(directory: str | os.PathLike[str]) -> NetworkFixture:
    """Write a small network, its inflows and the tables the command makes of them.

    The network has two subcatchments (``A``, and ``B`` that reads the column
    ``tributary_B``), a Muskingum reach ``R1`` below ``A``, the junction ``J1`` of
    ``R1`` and ``B``, and the outlet ``OUT``; the inflows are
    :data:`EXAMPLE_INFLOWS` every 5 minutes for 40 minutes. Layout::

        <directory>/network.json
        <directory>/inflows.csv
        <directory>/out/<id>.csv      A, B, R1, J1, OUT

    Parameters
    ----------
    directory : str or os.PathLike
        Directory of the case (made if missing; files of these names are replaced).

    Returns
    -------
    NetworkFixture
        The paths.
    """
    root = Path(os.fspath(directory))
    document = network_document(
        subcatchment("A"),
        subcatchment("B", value_column="tributary_B"),
        reach("R1", "A", method="muskingum", k_min=10, x=0.2),
        junction("J1", "R1", "B"),
        outlet("J1"),
        name="Culvert inflow",
    )
    network_file = write_network_document(root / "network.json", document)
    rows = ["time_min,A,tributary_B"]
    for index, time in enumerate(EXAMPLE_TIMES_MIN):
        values = ",".join(repr(column[index]) for column in EXAMPLE_INFLOWS.values())
        rows.append(f"{time:g},{values}")
    inflows_file = root / "inflows.csv"
    inflows_file.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    loaded = load_network(network_file=network_file, inflows_file=inflows_file)
    out = root / "out"
    _write_tables(out, _tables(loaded.network))
    return NetworkFixture(network_file, inflows_file, out, tuple(loaded.network.order))


# --- result envelopes ---------------------------------------------------------------


def hietogram_envelope(
    *,
    hietogram_type: str = "euler_ii",
    total_mm: float = 40.0,
    duration_min: float = 60.0,
    timestep_min: float = 10.0,
    **options: float,
) -> dict[str, Any]:
    """Return the envelope of ``precip hietogram``, as ``--json`` prints it.

    Parameters
    ----------
    hietogram_type : {"block", "triangular", "beta", "euler_ii"}, optional
        Temporal distribution, by default ``euler_ii``.
    total_mm : float, optional
        Total depth [mm], by default 40.
    duration_min : float, optional
        Storm duration [min], by default 60.
    timestep_min : float, optional
        Time step [min], by default 10.
    **options
        ``alpha``, ``beta`` or ``peak_position`` where the type takes them.

    Returns
    -------
    dict
        The ``hydrolog-result/1`` envelope (``result.schema`` is
        ``hydrolog-precip-hietogram/1``), JSON-native. Its ``version`` is that of the
        installed Hydrolog.

    Raises
    ------
    hydrolog.InvalidParameterError
        If an option is out of range or does not apply to the type.
    """
    envelope: dict[str, Any] = json.loads(
        _hietogram_text(
            hietogram_type=hietogram_type,
            total_mm=total_mm,
            duration_min=duration_min,
            timestep_min=timestep_min,
            **options,
        )
    )
    return envelope


def _hietogram_text(**options: Any) -> str:
    from hydrolog import run_command

    return run_command("precip hietogram", **options).to_json()


def write_hietogram_envelope(
    path: str | os.PathLike[str],
    *,
    hietogram_type: str = "euler_ii",
    total_mm: float = 40.0,
    duration_min: float = 60.0,
    timestep_min: float = 10.0,
    **options: float,
) -> Path:
    """Write :func:`hietogram_envelope` to ``path`` and return the path.

    The file is the text that ``hydrolog precip hietogram --json`` prints (one line,
    UTF-8), which a consumer such as ``hydraulik rainfall build --hietogram`` reads.
    """
    target = Path(os.fspath(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    text = _hietogram_text(
        hietogram_type=hietogram_type,
        total_mm=total_mm,
        duration_min=duration_min,
        timestep_min=timestep_min,
        **options,
    )
    target.write_text(text + "\n", encoding="utf-8", newline="\n")
    return target
