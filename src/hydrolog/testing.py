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
:func:`write_network_document`.

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

from hydrolog.operations._network_input import SCHEMA as NETWORK_SCHEMA
from hydrolog.operations._network_input import load_network
from hydrolog.routing import Hydrograph, RoutingNetwork

__all__ = [
    "EXAMPLE_INFLOWS",
    "EXAMPLE_TIMES_MIN",
    "NETWORK_SCHEMA",
    "NetworkFixture",
    "build_network_fixture",
    "hietogram_envelope",
    "hydrograph_table",
    "junction",
    "network_document",
    "network_tables",
    "outlet",
    "reach",
    "subcatchment",
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
) -> dict[str, Any]:
    """Return a ``subcatchment`` node.

    Parameters
    ----------
    node_id : str
        Id of the node (it names the table ``<id>.csv``).
    times_min, discharge_m3s : sequence of float, optional
        The hydrograph inline, both together.
    value_column : str, optional
        Column of the inflows file that holds the discharges; without it and without
        an inline hydrograph the column is named like the node.

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


def _checkable(nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return a copy of ``nodes`` in which every source that reads a file is inline.

    A subcatchment that names a column of the inflows file has no discharges in the
    document; the loader needs them to check the rest, so such a node gets a flat
    hydrograph on the time axis of the first inline source (or a short default one).
    """
    axis: list[float] = [0, 5, 10]
    for node in nodes:
        if "times_min" in node and "discharge_m3s" in node:
            axis = list(node["times_min"])
            break
    checked: list[dict[str, Any]] = []
    for node in nodes:
        copy = dict(node)
        if (
            copy.get("type") == "subcatchment"
            and "times_min" not in copy
            and "discharge_m3s" not in copy
        ):
            copy.pop("value_column", None)
            copy["times_min"] = axis
            copy["discharge_m3s"] = [0.0] * len(axis)
        checked.append(copy)
    return {"schema": NETWORK_SCHEMA, "nodes": checked}


def network_document(
    *nodes: Mapping[str, Any], name: str | None = None
) -> dict[str, Any]:
    """Return a checked ``hydrolog-network/1`` document of ``nodes``.

    The nodes keep the order given (the order of nodes changes no result). The
    document is read by the loader of ``route network`` before it is returned, so it is
    a valid network: one outlet, no cycle, every ``from`` an id of the document, every
    field and option valid for its type. A subcatchment that reads the inflows file
    (:func:`subcatchment` without a hydrograph) is checked as if it were inline.

    Parameters
    ----------
    *nodes : mapping
        Nodes from :func:`subcatchment`, :func:`reach`, :func:`junction` and
        :func:`outlet`.
    name : str, optional
        Name of the network.

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
    document["nodes"] = [dict(node) for node in nodes]
    load_network(network=_checkable(document["nodes"]))
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
