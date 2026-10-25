"""The JSON Schemas of the domain documents (AGI-4.1): shipped, current and loose.

Each command declares the id of its result document (``Command.result_schema``); the
schemas in ``src/hydrolog/schemas`` are generated from the examples of the catalog by
``scripts/generate_result_schemas.py``. They are package data, so they are read here
through :mod:`importlib.resources`, as an installed package would.
"""

from __future__ import annotations

import importlib.util
import json
from importlib import resources
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from hydrolog.catalog import check_command, data_commands, run_command
from hydrolog.catalog.document import COMMANDS_SCHEMA
from hydrolog.catalog.spec import Command
from hydrolog.exceptions import HydrologError, MissingDependencyError
from hydrolog.operations._network_input import load_network

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = resources.files("hydrolog") / "schemas"
COMMANDS = data_commands()
PLAN = "hydrolog-plan/1"
NETWORK_DOCUMENT = "hydrolog-network/1"
EXAMPLES = [
    pytest.param(command, index, id=f"{command.name}#{index}")
    for command in COMMANDS
    if command.result_schema != COMMANDS_SCHEMA
    for index in range(len(command.examples))
]


def _file_name(schema_id: str) -> str:
    return schema_id.replace("/", "-") + ".schema.json"


def _schema(schema_id: str) -> dict[str, Any]:
    document: dict[str, Any] = json.loads(
        (SHIPPED / _file_name(schema_id)).read_text(encoding="utf-8")
    )
    return document


def _violations(schema_id: str, document: object) -> list[str]:
    validator = Draft202012Validator(_schema(schema_id))
    return [error.message for error in validator.iter_errors(document)]


def _scratch_example(command: Command, index: int, directory: Path) -> dict[str, Any]:
    """The example with its output paths moved into ``directory``."""
    example = dict(command.examples[index])
    for option in command.options:
        if option.writes and option.name in example:
            suffix = Path(str(example[option.name])).suffix
            example[option.name] = str(directory / f"{option.name}{suffix}")
    return example


@pytest.fixture(autouse=True)
def _repository_root(monkeypatch):
    """Examples use paths relative to the repository root."""
    monkeypatch.chdir(ROOT)


def test_every_result_document_of_the_catalog_has_a_shipped_schema():
    ids = {command.result_schema for command in COMMANDS} | {PLAN, NETWORK_DOCUMENT}
    ids.discard(COMMANDS_SCHEMA)  # the Nogat schema commands-1 describes it
    shipped = {
        entry.name for entry in SHIPPED.iterdir() if entry.name.endswith(".schema.json")
    }
    assert shipped == {_file_name(schema_id) for schema_id in ids}


@pytest.mark.parametrize(
    "schema_id",
    sorted({c.result_schema for c in COMMANDS} - {COMMANDS_SCHEMA} | {PLAN}),
)
def test_each_schema_is_valid_and_names_itself(schema_id):
    schema = _schema(schema_id)
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == schema_id
    assert schema["$id"].endswith("/" + _file_name(schema_id))
    assert schema["properties"]["schema"] == {"const": schema_id}
    assert "schema" in schema["required"]


def test_the_shipped_schemas_are_what_the_generator_writes():
    pytest.importorskip("rasterio")  # the soil examples need the raster extra
    spec = importlib.util.spec_from_file_location(
        "generate_result_schemas", ROOT / "scripts" / "generate_result_schemas.py"
    )
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    assert generator.main(["--check"]) == 0


@pytest.mark.parametrize(("command", "index"), EXAMPLES)
def test_the_result_of_every_example_obeys_its_schema(command, index, tmp_path):
    example = _scratch_example(command, index, tmp_path)
    try:
        result = run_command(command, example).to_dict()["result"]
    except MissingDependencyError as exc:
        pytest.skip(f"optional extra not installed: {exc}")

    assert _violations(command.result_schema, result) == []
    # A field added later keeps the version (AGI-4.1): unknown fields are allowed.
    assert _violations(command.result_schema, {**result, "added_later": [1]}) == []


FILE_COMMANDS = [
    c for c in COMMANDS if c.check and "output" in {o.name for o in c.options}
]
DIRECTORY_COMMANDS = [
    c for c in COMMANDS if c.check and "output_dir" in {o.name for o in c.options}
]


@pytest.mark.parametrize("command", FILE_COMMANDS, ids=lambda command: command.name)
def test_the_plan_of_a_check_run_obeys_its_schema(command, tmp_path):
    (tmp_path / "taken.out").write_text("x", encoding="utf-8")
    for target, action in (("fresh.out", "write"), ("taken.out", "conflict")):
        example = _scratch_example(command, 0, tmp_path)
        example["output"] = str(tmp_path / target)
        example.pop("inject", None)
        plan = check_command(command, example).to_dict()["result"]

        assert _violations(PLAN, plan) == []
        assert [item["action"] for item in plan["targets"]] == [action]


@pytest.mark.parametrize(
    "command", DIRECTORY_COMMANDS, ids=lambda command: command.name
)
def test_the_plan_of_a_directory_obeys_its_schema(command, tmp_path):
    example = _scratch_example(command, 0, tmp_path)
    directory = Path(example["output_dir"])

    def planned(**extra: Any) -> list[dict[str, Any]]:
        plan = check_command(command, {**example, **extra}).to_dict()["result"]
        assert _violations(PLAN, plan) == []
        assert {item["option"] for item in plan["targets"]} == {"output_dir"}
        return list(plan["targets"])

    fresh = planned()
    assert fresh and {item["action"] for item in fresh} == {"write"}
    assert not directory.exists(), "a plan creates nothing"

    run_command(command, example)
    taken = planned()
    assert {(item["action"], item["reason"]) for item in taken} == {
        ("conflict", "output_exists")
    }
    assert {item["action"] for item in planned(force=True)} == {"replace"}

    store = tmp_path / "store"
    store.mkdir()
    (store / "kartograf-store.json").write_text("{}", encoding="utf-8")
    inside = planned(output_dir=str(store / "plain"))
    assert {(item["action"], item["reason"]) for item in inside} == {
        ("conflict", "output_in_store")
    }


def test_the_plan_schema_accepts_every_action_and_rejects_an_unknown_one():
    target = {"option": "output", "path": "/tmp/a", "action": "replace"}
    assert _violations(PLAN, {"schema": PLAN, "targets": [target]}) == []
    bad = {**target, "action": "delete"}
    assert _violations(PLAN, {"schema": PLAN, "targets": [bad]})


def test_the_command_list_obeys_its_schema():
    result = run_command("commands list", {}).to_dict()["result"]
    assert _violations("hydrolog-command-list/1", result) == []


def test_a_schema_is_not_vacuous():
    result = run_command("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
    document = result.to_dict()["result"]
    schema_id = "hydrolog-tc-kirpich/1"
    assert _violations(schema_id, document) == []

    missing = {key: value for key, value in document.items() if key != "tc_min"}
    assert _violations(schema_id, missing)
    assert _violations(schema_id, {**document, "tc_min": "85.97"})
    assert _violations(schema_id, {**document, "schema": "hydrolog-tc-faa/1"})


NETWORK_FIXTURE = ROOT / "tests" / "fixtures" / "network_flood.json"


def test_the_network_document_schema_is_valid_and_names_itself():
    schema = _schema(NETWORK_DOCUMENT)
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == NETWORK_DOCUMENT
    assert schema["$id"].endswith("/" + _file_name(NETWORK_DOCUMENT))
    assert schema["properties"]["schema"] == {"const": NETWORK_DOCUMENT}
    assert schema["required"] == ["schema", "nodes"]


def test_the_fixture_network_and_the_inline_example_obey_the_network_schema():
    fixture = json.loads(NETWORK_FIXTURE.read_text(encoding="utf-8"))
    inline = next(c for c in COMMANDS if c.name == "route network").examples[1]

    assert _violations(NETWORK_DOCUMENT, fixture) == []
    assert _violations(NETWORK_DOCUMENT, inline["network"]) == []


def _stream(*nodes: dict[str, Any], **top: Any) -> dict[str, Any]:
    """A network of a source, a reach by lag and an outlet, with ``nodes`` added."""
    return {
        "schema": NETWORK_DOCUMENT,
        "nodes": [
            {
                "id": "A",
                "type": "subcatchment",
                "times_min": [0, 10],
                "discharge_m3s": [1, 2],
            },
            {"id": "R", "type": "reach", "from": ["A"], "method": "lag", "lag_min": 10},
            {"id": "OUT", "type": "outlet", "from": ["R"]},
            *nodes,
        ],
        **top,
    }


def _edited(node: int, **fields: Any) -> dict[str, Any]:
    """The stream above with fields of one node set, or removed when ``None``."""
    document = _stream()
    entry = document["nodes"][node]
    entry.update(fields)
    for name in [name for name, value in entry.items() if value is None]:
        del entry[name]
    return document


def _without_schema(document: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != "schema"}


# documents that the schema and the loader both refuse: field names, types and counts
REFUSED = {
    "unknown top-level field": _stream(color="blue"),
    "no schema": _without_schema(_stream()),
    "null schema": _stream(schema=None),
    "other schema": _stream(schema="hydrolog-network/2"),
    "empty name": _stream(name=""),
    "no nodes": {"schema": NETWORK_DOCUMENT, "name": "x"},
    **{
        f"reserved id {name}": _edited(2, id=name)
        for name in ("con", "CON", "Prn", "aux", "nul", "NUL.txt", "com1", "LPT9.x")
    },
    "unknown type": _edited(0, type="river"),
    "bad id": _edited(0, id="a b"),
    "id too long": _edited(0, id="x" * 65),
    "unknown field of a source": _edited(0, lag_min=10),
    "times without discharges": _edited(0, discharge_m3s=None),
    "column with inline discharges": _edited(0, value_column="A"),
    "a source with an upstream node": _edited(0, **{"from": ["R"]}),
    "negative discharge": _edited(0, discharge_m3s=[1, -2]),
    "a reach without a method": _edited(1, method=None),
    "an unknown method": _edited(1, method="kinematic"),
    "a reach without its parameter": _edited(1, lag_min=None),
    "a parameter of another method": _edited(1, k_min=20),
    "a lag that is not positive": _edited(1, lag_min=0),
    "a reach with two upstream nodes": _edited(1, **{"from": ["A", "OUT"]}),
    "a reach without upstream nodes": _edited(1, **{"from": None}),
    "an upstream id twice": _edited(1, **{"from": ["A", "A"]}),
    "an upstream list that is a string": _edited(1, **{"from": "A"}),
    "an outlet with a parameter": _edited(2, lag_min=10),
    "an outlet with two upstream nodes": _edited(2, **{"from": ["R", "A"]}),
}


@pytest.mark.parametrize("name", REFUSED)
def test_the_network_schema_and_the_loader_refuse_the_same_documents(name):
    document = REFUSED[name]

    assert _violations(NETWORK_DOCUMENT, document), "the schema accepts it"
    with pytest.raises(HydrologError):
        load_network(network=document)


def test_the_network_schema_and_the_loader_accept_the_same_documents():
    accepted = [
        _stream(),
        _stream(name="Upper catchment"),
        _edited(1, method="muskingum", lag_min=None, k_min=20, x=0.2, subreaches=2),
        _edited(1, extend_min=0, initial_outflow_m3s=1.5),
        _edited(2, id="console"),
        _edited(2, id="com10"),
        _edited(2, id="com0"),
        _edited(2, id="x.con"),
    ]
    for document in accepted:
        assert _violations(NETWORK_DOCUMENT, document) == []
        load_network(network=document)
