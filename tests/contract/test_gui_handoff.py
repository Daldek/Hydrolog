"""The hand-off envelope ``nogat-handoff/1`` the GUI writes and reads (plan D15, S6).

``schemas/nogat/handoff-1.schema.json`` is Nogat's schema copied unchanged (its SHA-256
is the one ``schemas/nogat/README.md`` records); Hydrolog never defines the envelope.
Its example, the complete form of D15, validates, and so does its payload against
``hydrolog-network/1``, which the envelope leaves to its owner. The example's watershed
predates ADR-0019: it has the main channel but not the longest flow path that Kirpich
takes, so ``route network`` refuses it, naming the fields, until Nogat's example gains
them. With Kamiennik's flow path its one subcatchment computes as ``hydrograph
generate`` computes the options it maps to: the equivalence by which Hydrogram zlewni
writes and reads a hand-off.
"""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError

ROOT = Path(__file__).resolve().parents[2]
COPY = ROOT / "schemas" / "nogat" / "handoff-1.schema.json"
README = ROOT / "schemas" / "nogat" / "README.md"
NETWORK = ROOT / "src" / "hydrolog" / "schemas" / "hydrolog-network-1.schema.json"
SCHEMA: dict[str, Any] = json.loads(COPY.read_text(encoding="utf-8"))
EXAMPLES: list[dict[str, Any]] = SCHEMA["examples"]
# The options of `hydrograph generate` a subcatchment's `runoff` and `rainfall` hold.
NOT_OPTIONS = {"model", "kind"}


def _errors(schema: dict[str, Any], document: Any) -> list[str]:
    return [
        error.message for error in Draft202012Validator(schema).iter_errors(document)
    ]


def _outlet(payload: dict[str, Any]) -> dict[str, Any]:
    result = run_command("route network", {"network": payload}).to_dict()["result"]
    found: dict[str, Any] = next(
        node for node in result["nodes"] if node["id"] == result["outlet"]
    )
    return found


def test_the_copy_is_nogats_schema_unchanged() -> None:
    recorded = re.search(
        r"SHA-256\s*`([0-9a-f]{64})`", README.read_text(encoding="utf-8")
    )

    assert recorded is not None
    assert hashlib.sha256(COPY.read_bytes()).hexdigest() == recorded.group(1)
    Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["title"] == "nogat-handoff/1"
    assert SCHEMA["properties"]["schema"] == {"const": "nogat-handoff/1"}


@pytest.mark.parametrize("index", range(len(EXAMPLES)))
def test_the_example_and_its_payload_validate(index: int) -> None:
    example = EXAMPLES[index]
    network = json.loads(NETWORK.read_text(encoding="utf-8"))

    assert _errors(SCHEMA, example) == []
    assert example["payload"]["schema"] == "hydrolog-network/1"
    assert _errors(network, example["payload"]) == []


@pytest.mark.parametrize("index", range(len(EXAMPLES)))
def test_the_payload_without_the_flow_path_is_refused(index: int) -> None:
    payload = EXAMPLES[index]["payload"]

    with pytest.raises(InvalidParameterError) as caught:
        _outlet(payload)

    assert caught.value.details["reason"] == "missing_field"
    assert caught.value.details["missing"] == [
        "flow_path_length_km",
        "flow_path_slope_m_per_m",
    ]


def test_one_subcatchment_computes_as_hydrograph_generate() -> None:
    payload = json.loads(json.dumps(EXAMPLES[0]["payload"]))
    node = next(node for node in payload["nodes"] if node["type"] == "subcatchment")
    # Kamiennik's longest flow path (tests/fixtures/kamiennik.json)
    node["watershed"].update(flow_path_length_km=15.88, flow_path_slope_m_per_m=0.0114)
    options: dict[str, Any] = {"watershed": node["watershed"]}
    for part in (node["runoff"], node.get("rainfall", payload.get("rainfall", {}))):
        options.update(
            {key: value for key, value in part.items() if key not in NOT_OPTIONS}
        )
    if "timestep_min" in payload:
        options["timestep_min"] = payload["timestep_min"]
    generated = run_command("hydrograph generate", options).to_dict()["result"]
    outlet = _outlet(payload)

    assert math.isclose(
        generated["peak_discharge_m3s"], outlet["peak_m3s"], rel_tol=1e-9
    )
    assert generated["time_to_peak_min"] == outlet["time_to_peak_min"]
    assert math.isclose(generated["total_volume_m3"], outlet["volume_m3"], rel_tol=1e-9)
