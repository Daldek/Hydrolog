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
from hydrolog.exceptions import MissingDependencyError

ROOT = Path(__file__).resolve().parents[2]
SHIPPED = resources.files("hydrolog") / "schemas"
COMMANDS = data_commands()
PLAN = "hydrolog-plan/1"
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
    ids = {command.result_schema for command in COMMANDS} | {PLAN}
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


@pytest.mark.parametrize(
    "command", [c for c in COMMANDS if c.check], ids=lambda command: command.name
)
def test_the_plan_of_a_check_run_obeys_its_schema(command, tmp_path):
    (tmp_path / "taken.out").write_text("x", encoding="utf-8")
    for target, action in (("fresh.out", "write"), ("taken.out", "conflict")):
        example = _scratch_example(command, 0, tmp_path)
        example["output"] = str(tmp_path / target)
        example.pop("inject", None)
        plan = check_command(command, example).to_dict()["result"]

        assert _violations(PLAN, plan) == []
        assert [item["action"] for item in plan["targets"]] == [action]


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
