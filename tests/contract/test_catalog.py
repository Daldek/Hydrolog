"""Contract tests of the command catalog (AGI-2, AGI-4, DEV-19).

Every command of the catalog is exercised through its own examples: each one runs
offline from the repository root, produces a ``hydrolog-result/1`` envelope that
validates against the vendored Nogat schema, and contains the ``example_results``
excerpt that the catalog publishes.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import pytest

from hydrolog.catalog import (
    Command,
    catalog_document,
    check_command,
    command_schema,
    data_commands,
    run_command,
)
from hydrolog.exceptions import MissingDependencyError

from . import _nogat

ROOT = _nogat.ROOT
COMMANDS = data_commands()
ERROR_CODES = {
    entry["code"]
    for entry in json.loads(
        (_nogat.SCHEMAS / "error_registry.json").read_text(encoding="utf-8")
    )["errors"]
}
RELATIVE_TOLERANCE = 1e-5


def contains(actual: Any, excerpt: Any, path: str = "result") -> list[str]:
    """List how ``excerpt`` is not contained in ``actual`` (empty when it is).

    Containment: a mapping is a subset of the actual mapping, a list is a prefix of
    the actual list, numbers are equal within a relative tolerance of ``1e-5`` and
    everything else is equal.
    """
    if isinstance(excerpt, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected an object, got {type(actual).__name__}"]
        problems: list[str] = []
        for key, value in excerpt.items():
            if key not in actual:
                problems.append(f"{path}.{key}: missing")
            else:
                problems += contains(actual[key], value, f"{path}.{key}")
        return problems
    if isinstance(excerpt, list):
        if not isinstance(actual, list):
            return [f"{path}: expected a list, got {type(actual).__name__}"]
        if len(actual) < len(excerpt):
            return [f"{path}: {len(actual)} items, excerpt has {len(excerpt)}"]
        problems = []
        for index, value in enumerate(excerpt):
            problems += contains(actual[index], value, f"{path}[{index}]")
        return problems
    if isinstance(excerpt, bool) or excerpt is None or isinstance(excerpt, str):
        return (
            []
            if actual == excerpt and type(actual) is type(excerpt)
            else [f"{path}: {actual!r} != {excerpt!r}"]
        )
    if isinstance(actual, bool) or not isinstance(actual, int | float):
        return [f"{path}: {actual!r} is not a number"]
    if math.isclose(actual, excerpt, rel_tol=RELATIVE_TOLERANCE, abs_tol=0.0):
        return []
    return [f"{path}: {actual!r} != {excerpt!r}"]


class TestContains:
    """The containment rule that the example results are checked with."""

    def test_a_mapping_is_a_subset(self):
        assert contains({"a": 1, "b": 2}, {"a": 1}) == []
        assert contains({"a": 1}, {"b": 1}) == ["result.b: missing"]

    def test_a_list_is_a_prefix(self):
        assert contains([1, 2, 3], [1, 2]) == []
        assert contains([1, 2, 3], [2, 3]) != []
        assert contains([1], [1, 2]) != []

    def test_numbers_are_equal_within_the_relative_tolerance(self):
        assert contains(100000.0, 100000.5) == []
        assert contains(100000.0, 100002.0) != []
        assert contains(1, 1.0) == []

    def test_a_bool_is_not_a_number_and_strings_are_exact(self):
        assert contains(1, True) != []
        assert contains(True, 1) != []
        assert contains("a", "a") == []
        assert contains("a", "A") != []
        assert contains(None, None) == []


def _is_output(command: Command, name: str) -> bool:
    return command.option(name).path_role == "output"


def _example_options(command: Command, example: dict, tmp_path: Path) -> dict:
    """The options of an example with every output path moved into ``tmp_path``."""
    options = dict(example)
    for name, value in example.items():
        if _is_output(command, name):
            options[name] = str(tmp_path / Path(str(value)).name)
    return options


def _examples() -> list[Any]:
    return [
        pytest.param(command, number, id=f"{command.name}#{number}")
        for command in COMMANDS
        for number in range(len(command.examples))
    ]


def _run(command: Command, options: dict) -> dict:
    try:
        return run_command(command, options).to_dict()
    except MissingDependencyError:
        pytest.skip("an optional extra is not installed")


@pytest.fixture
def repository_root(monkeypatch):
    """Run from the repository root: examples name their input files relative to it."""
    monkeypatch.chdir(ROOT)


@pytest.mark.usefixtures("repository_root")
class TestExamples:
    """Each example of each command runs and yields what the catalog promises."""

    @pytest.mark.parametrize(("command", "number"), _examples())
    def test_the_example_runs_and_contains_its_excerpt(self, command, number, tmp_path):
        example = dict(command.examples[number])
        envelope = _run(command, _example_options(command, example, tmp_path))
        assert envelope["status"] == "ok"
        assert envelope["command"] == command.name
        problems = contains(envelope["result"], dict(command.example_results[number]))
        assert problems == []

    @pytest.mark.parametrize(("command", "number"), _examples())
    def test_the_envelope_validates_against_result_1(self, command, number, tmp_path):
        example = dict(command.examples[number])
        envelope = _run(command, _example_options(command, example, tmp_path))
        errors = list(_nogat.validator("result-1").iter_errors(envelope))
        assert [e.message for e in errors] == []

    @pytest.mark.parametrize(("command", "number"), _examples())
    def test_the_result_schema_is_the_declared_one(self, command, number, tmp_path):
        example = dict(command.examples[number])
        envelope = _run(command, _example_options(command, example, tmp_path))
        expected = "hydrolog-plan/1" if example.get("check") else command.result_schema
        assert envelope["result"]["schema"] == expected
        assert envelope["check"] is bool(example.get("check", False))

    @pytest.mark.parametrize(("command", "number"), _examples())
    def test_the_inputs_echo_the_example_options(self, command, number, tmp_path):
        example = dict(command.examples[number])
        envelope = _run(command, _example_options(command, example, tmp_path))
        assert set(example) <= set(envelope["inputs"])
        for option in command.options:
            if option.default is not None:
                assert option.name in envelope["inputs"], option.name

    @pytest.mark.parametrize(
        "command", [c for c in COMMANDS if c.writes], ids=lambda c: c.name
    )
    def test_a_writing_command_lists_its_files_inside_the_result(
        self, command, tmp_path
    ):
        example = dict(command.examples[0])
        if example.get("check"):
            pytest.skip("the example is a plan")
        options = _example_options(command, example, tmp_path)
        envelope = _run(command, options)
        listed = envelope["result"].get("files", [])
        outputs = [name for name in example if _is_output(command, name)]
        directories = [Path(options[name]) for name in outputs if name == "output_dir"]
        files = [name for name in outputs if name != "output_dir"]
        beside = [r for r in listed if Path(r["path"]).parent == tmp_path]
        inside = [r for r in listed if Path(r["path"]).parent in directories]
        assert len(beside) == len(files)
        assert len(beside) + len(inside) == len(listed), "a file outside the outputs"
        for record in [*beside, *inside]:
            assert record["status"] == "written"
            assert record["size_bytes"] == Path(record["path"]).stat().st_size
        for directory in directories:
            here = {
                Path(r["path"]).name
                for r in inside
                if Path(r["path"]).parent == directory
            }
            assert here, "a directory output lists the files it received"
            assert set(os.listdir(directory)) == here, "nothing else is left there"
        if not outputs:
            assert listed == []

    @pytest.mark.parametrize(
        "command", [c for c in COMMANDS if c.writes], ids=lambda c: c.name
    )
    def test_check_plans_the_first_example_and_writes_nothing(self, command, tmp_path):
        example = dict(command.examples[0])
        example.pop("check", None)
        options = _example_options(command, example, tmp_path)
        if not any(_is_output(command, name) for name in options):
            pytest.skip("the example writes no file")
        before = sorted(os.listdir(tmp_path))
        envelope = check_command(command, options).to_dict()
        assert envelope["check"] is True
        assert envelope["result"]["schema"] == "hydrolog-plan/1"
        assert {t["action"] for t in envelope["result"]["targets"]} == {"write"}
        assert "files" not in envelope["result"]
        assert sorted(os.listdir(tmp_path)) == before
        errors = list(_nogat.validator("result-1").iter_errors(envelope))
        assert [e.message for e in errors] == []


class TestCatalogDocument:
    """The ``hydrolog-commands/1`` document of the whole catalog."""

    def test_it_validates_against_commands_1(self):
        document = catalog_document(COMMANDS)
        errors = list(_nogat.validator("commands-1").iter_errors(document))
        assert [e.message for e in errors] == []

    def test_every_single_command_document_validates_too(self):
        validator = _nogat.validator("commands-1")
        for command in COMMANDS:
            document = catalog_document((command,), typical_ranges=True)
            assert list(validator.iter_errors(document)) == [], command.name

    @pytest.mark.parametrize(
        ("command", "method", "parameter", "served", "cited"),
        [
            (
                "tc kirpich",
                "kirpich",
                "slope_m_per_m",
                {
                    "inputs": ["slope_m_per_m"],
                    "minimum": 0.03,
                    "maximum": 0.1,
                    "unit": "m/m",
                },
                "Kirpich (1940)",
            ),
            # On a watershed the inputs are its fields, first choice first
            (
                "tc watershed",
                "kirpich",
                "slope_m_per_m",
                {
                    "inputs": ["channel_slope_m_per_m", "mean_slope_m_per_m"],
                    "minimum": 0.03,
                    "maximum": 0.1,
                    "unit": "m/m",
                },
                "Kirpich (1940)",
            ),
            (
                "tc watershed",
                "kirpich",
                "area_km2",
                {
                    "inputs": ["area_km2"],
                    "minimum": 0.005,
                    "maximum": 0.45,
                    "unit": "km2",
                },
                "Kirpich (1940)",
            ),
            (
                "uh nash",
                "lutz",
                "area_km2",
                {
                    "inputs": ["area_km2"],
                    "minimum": 0.0,
                    "maximum": 236.0,
                    "unit": "km2",
                },
                "KZGW (2017)",
            ),
            # Given parameters without a published source: kept, to be verified
            (
                "uh nash",
                "nash",
                "n",
                {
                    "inputs": ["n"],
                    "minimum": 1.0,
                    "maximum": 10.0,
                    "unit": "-",
                    "notice": "outside_unverified_range",
                    "verified": False,
                },
                "Hydrolog",
            ),
            # Bounds that are shares of a result field
            (
                "hydrograph generate",
                "scs",
                "timestep_min",
                {
                    "inputs": ["timestep_min"],
                    "minimum": 0.0,
                    "maximum": 0.25,
                    "unit": "min",
                    "relative_to": "uh_time_to_peak_min",
                },
                "NEH 630",
            ),
            # A value of the result, no upper bound, its own notice
            (
                "stats flood-frequency",
                "flood_frequency",
                "years",
                {
                    "inputs": [],
                    "result": "n_years",
                    "minimum": 30.0,
                    "maximum": None,
                    "unit": "years",
                    "notice": "short_record",
                },
                "KZGW (2017)",
            ),
        ],
    )
    def test_the_document_of_one_command_serves_its_typical_ranges(
        self,
        command: str,
        method: str,
        parameter: str,
        served: dict[str, Any],
        cited: str,
    ) -> None:
        """What a client reads instead of keeping numbers (ADR-0017): the bounds, the
        inputs the value comes from, the published source in both languages and whether
        the range is verified."""
        envelope = run_command("commands schema", {"command": command}).to_dict()
        (entry,) = envelope["result"]["commands"]
        assert command_schema(command).to_dict()["commands"] == [entry]
        found = {(r["method"], r["parameter"]): r for r in entry["typical_ranges"]}
        served_range = dict(found[(method, parameter)])
        source = served_range.pop("source")
        polish = served_range.pop("i18n")["pl"]["source"]
        assert served_range == {
            "method": method,
            "parameter": parameter,
            "notice": "outside_typical_range",
            "verified": True,
            **served,
        }
        assert cited in source and cited in polish

    def test_no_page_of_the_catalog_carries_typical_ranges(self) -> None:
        """Not even a page of one command: only the document of one command does."""
        entries: list[dict[str, Any]] = []
        options: dict[str, Any] = {"limit": 1}
        while True:
            envelope = run_command("commands schema", options).to_dict()
            entries += envelope["result"]["commands"]
            if not envelope["page"]["truncated"]:
                break
            options = {"limit": 1, "cursor": envelope["page"]["next_cursor"]}
        assert [entry["name"] for entry in entries] == [c.name for c in COMMANDS]
        assert [entry["name"] for entry in entries if "typical_ranges" in entry] == []

    def test_it_lists_every_command_once_in_catalog_order(self):
        names = [entry["name"] for entry in catalog_document(COMMANDS)["commands"]]
        assert names == [command.name for command in COMMANDS]
        assert len(set(names)) == len(names)


class TestInvariants:
    """Rules that every declaration of the catalog obeys."""

    def test_operation_ids_are_unique_prefixed_and_short(self):
        ids = [command.operation_id for command in COMMANDS]
        assert len(set(ids)) == len(ids)
        for command in COMMANDS:
            assert command.operation_id.startswith("hydrolog_")
            assert len(command.operation_id) <= 48

    def test_the_core_family_has_at_most_ten_commands(self):
        core = [c.name for c in COMMANDS if "core" in c.families]
        assert 0 < len(core) <= 10

    def test_effects_derive_from_the_path_roles(self):
        for command in COMMANDS:
            writes = any(o.path_role == "output" for o in command.options)
            assert command.effects.read_only is (not writes), command.name
            assert command.effects.writes == ("replace" if writes else "none")
            assert command.effects.destructive is writes
            assert command.effects.network is False

    def test_a_command_with_check_is_its_own_check_and_the_others_have_none(self):
        """Every writing command plans itself; ``gui serve`` plans where it serves."""
        for command in COMMANDS:
            options = {o.name for o in command.options}
            if command.writes:
                assert {"force", "check"} <= options, command.name
                assert command.option("force").type == "boolean"
            else:
                assert "force" not in options, command.name
            if "check" in options:
                assert command.check == command.name
                assert command.option("check").type == "boolean"
            else:
                assert command.check is None
        planning = [c.name for c in COMMANDS if c.check and not c.writes]
        assert planning == ["gui serve"]

    def test_errors_are_registry_codes(self):
        for command in COMMANDS:
            assert set(command.errors) <= ERROR_CODES, command.name
            assert "internal_error" not in command.errors

    def test_a_writing_command_declares_the_conflict(self):
        for command in COMMANDS:
            if command.writes:
                assert "conflict" in command.errors, command.name

    def test_the_result_schema_is_unique_per_command(self):
        schemas = [command.result_schema for command in COMMANDS]
        assert len(set(schemas)) == len(schemas)

    def test_every_choice_has_a_meaning_in_both_languages(self):
        for command in COMMANDS:
            for option in command.options:
                if option.type == "choice":
                    assert set(option.meanings) == set(option.choices), option.name
                    assert set(option.meanings_pl) == set(option.choices), option.name

    def test_every_example_is_a_valid_call(self):
        from hydrolog.catalog import validate_command

        for command in COMMANDS:
            for example in command.examples:
                validate_command(command, example)

    def test_machine_texts_are_english_and_translations_exist(self):
        """The catalog document has no Polish outside ``i18n``."""
        for entry in catalog_document(COMMANDS)["commands"]:
            assert entry["i18n"]["pl"]["summary"] != entry["summary"], entry["name"]
            assert len(entry["i18n"]["pl"]["rules"]) == len(entry["rules"])
