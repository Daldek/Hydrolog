"""Network documents for the tests: small streams written as the dicts of the document.

Shared by the tests of the reader (``test_network_input``) and of the command
(``test_operations_route_network``); the fixture network of ``tests/fixtures`` is the
documented example, these are the small ones whose results can be known by hand.
``STRUCTURE_CORPUS`` holds documents with one problem of their structure each, which
the network's reader, the structure's reader (ADR-0025) and the editor of Sieć must
report alike.
"""

import json
from pathlib import Path
from typing import Any

from hydrolog.routing.document import SCHEMA

TIMES = [0, 10, 20, 30, 40, 50, 60, 70]
FLOOD = [0, 10, 40, 90, 60, 30, 10, 0]
SMALL = [0, 4, 12, 8, 3, 0, 0, 0]


def source(node_id: str, discharge: Any = FLOOD, **fields: Any) -> dict[str, Any]:
    """A subcatchment with its discharges inline."""
    return {
        "id": node_id,
        "type": "subcatchment",
        "times_min": TIMES,
        "discharge_m3s": discharge,
        **fields,
    }


def reach(node_id: str, upstream: str, **fields: Any) -> dict[str, Any]:
    """A reach by lag of 25 min; ``fields`` replace or add."""
    return {
        "id": node_id,
        "type": "reach",
        "from": [upstream],
        "method": "lag",
        "lag_min": 25,
        **fields,
    }


def junction(node_id: str, *upstream: str) -> dict[str, Any]:
    return {"id": node_id, "type": "junction", "from": list(upstream)}


def outlet(upstream: str, node_id: str = "OUT") -> dict[str, Any]:
    return {"id": node_id, "type": "outlet", "from": [upstream]}


def document(*nodes: dict[str, Any], **top: Any) -> dict[str, Any]:
    """A document of ``nodes``, in the order given, with its ``schema``."""
    return {"schema": SCHEMA, "nodes": list(nodes), **top}


def stream(**reach_fields: Any) -> dict[str, Any]:
    """A source, a reach by lag and the outlet."""
    return document(source("A"), reach("R", "A", **reach_fields), outlet("R"))


def confluence() -> dict[str, Any]:
    """Two sources, a reach below the first, a junction and the outlet."""
    return document(
        source("A"),
        source("B", SMALL),
        reach("R", "A"),
        junction("J", "R", "B"),
        outlet("J"),
    )


def written(directory: Path, content: Any, name: str = "network.json") -> Path:
    """Write a document (or text) into ``directory`` and return the path."""
    path = directory / name
    path.write_text(
        content if isinstance(content, str) else json.dumps(content), encoding="utf-8"
    )
    return path


# Each document has one structural problem where one is possible (a network without an
# outlet and a link out of the outlet leave a node that flows nowhere) and every field
# complete, as the library checks the fields before the structure; the reason is the
# one the library raises.
STRUCTURE_CORPUS: list[tuple[str, dict[str, Any], str]] = [
    ("no nodes", document(), "empty"),
    ("an id with a space", document(source("A B"), outlet("A B")), "invalid_id"),
    (
        "an invalid id in from",
        document(source("A"), junction("J", "A", "bad id"), outlet("J")),
        "invalid_id",
    ),
    ("a device name", document(source("con"), outlet("con")), "reserved_name"),
    (
        "a device name in from",
        document(source("A"), junction("J", "A", "LPT1.txt"), outlet("J")),
        "reserved_name",
    ),
    (
        "ids that differ in case",
        document(source("A"), source("a"), junction("J", "A", "a"), outlet("J")),
        "duplicate_node",
    ),
    (
        "ids equal when folded",
        document(
            source("STRASSE"),
            source("straße"),
            junction("J", "STRASSE", "straße"),
            outlet("J"),
        ),
        "duplicate_node",
    ),
    (
        "an unknown inflow",
        document(source("A"), junction("J", "A", "X"), outlet("J")),
        "unknown_upstream",
    ),
    (
        "a repeated inflow",
        document(source("A"), junction("J", "A", "A"), outlet("J")),
        "duplicate_upstream",
    ),
    (
        "a reach with two inflows",
        document(
            source("A"),
            source("B"),
            reach("R", "A", **{"from": ["A", "B"]}),
            outlet("R"),
        ),
        "upstream_count",
    ),
    (
        "a subcatchment with an inflow",
        document(source("A"), source("B", **{"from": ["A"]}), outlet("B")),
        "upstream_count",
    ),
    (
        "a junction without inflows",
        document(source("A"), junction("J"), junction("K", "A", "J"), outlet("K")),
        "upstream_count",
    ),
    (
        "a node that flows into two",
        document(
            source("A"), junction("J1", "A"), junction("J2", "A", "J1"), outlet("J2")
        ),
        "several_downstream",
    ),
    (
        "a loop beside the stream",
        document(
            source("A"),
            junction("J1", "A", "J2"),
            junction("J2", "J1"),
            source("B"),
            outlet("B"),
        ),
        "cycle",
    ),
    (
        "a node that flows into itself",
        document(source("A"), junction("S", "S"), outlet("A")),
        "cycle",
    ),
    ("no outlet", document(source("A"), junction("J", "A")), "no_outlet"),
    (
        "two outlets",
        document(source("A"), source("B"), outlet("A", "O1"), outlet("B", "O2")),
        "several_outlets",
    ),
    (
        "a link out of the outlet",
        document(source("A"), outlet("A", "O1"), junction("J", "O1")),
        "outlet_has_downstream",
    ),
    (
        "a node that flows nowhere",
        document(source("A"), source("B"), outlet("A")),
        "disconnected_node",
    ),
]
"""``(name, document, reason)``: one problem of the structure per document."""
