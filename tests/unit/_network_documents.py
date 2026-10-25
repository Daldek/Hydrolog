"""Network documents for the tests: small streams written as the dicts of the document.

Shared by the tests of the reader (``test_network_input``) and of the command
(``test_operations_route_network``); the fixture network of ``tests/fixtures`` is the
documented example, these are the small ones whose results can be known by hand.
"""

import json
from pathlib import Path
from typing import Any

from hydrolog.operations._network_input import SCHEMA

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
