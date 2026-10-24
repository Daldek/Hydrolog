"""Tests for the MCP server (AGI section 5): tools, schemas, modes, calls, stdio.

The SDK client talks to the server in memory (``Client(create_server(...))``); the
classes at the end start the server as a real process on stdio. Everything runs the
real catalog and its real operations.
"""

import contextlib
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import anyio
import mcp.types as types
from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import MCPError
from referencing import Registry, Resource

from hydrolog.catalog import data_commands, get_command, run_command
from hydrolog.exceptions import ERROR_CODES, InvalidParameterError, NotFoundError
from hydrolog.mcp import create_server
from hydrolog.mcp._output import OUTPUT_SCHEMA
from hydrolog.mcp.server import main

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas" / "nogat"
COMMANDS = data_commands()
WRITING = [c for c in COMMANDS if c.writes]
ALWAYS_LOAD = ["hydrolog_commands_list", "hydrolog_commands_schema"]
HEAVY_MODULES = ("numpy", "scipy", "rasterio", "matplotlib", "pandas", "pyproj")
MODES = ["legacy", "auto"]


# --- helpers --------------------------------------------------------------------------


@contextlib.asynccontextmanager
async def connected(mode="auto", **server_kwargs):
    """An initialized SDK client of an in-memory server."""
    async with Client(create_server(**server_kwargs), mode=mode) as client:
        yield client


def listing(mode="auto", **server_kwargs):
    """``(tools, instructions)`` a client sees after connecting."""

    async def scenario():
        async with connected(mode, **server_kwargs) as client:
            return (await client.list_tools()).tools, client.instructions

    return anyio.run(scenario)


def call(tool, arguments=None, *, mode="auto", **server_kwargs):
    """Result of one tool call on a fresh in-memory server."""

    async def scenario():
        async with connected(mode, **server_kwargs) as client:
            return await client.call_tool(tool, arguments)

    return anyio.run(scenario)


@functools.cache
def default_listing():
    return listing()


def tools_by_name(**server_kwargs):
    tools, _ = listing(**server_kwargs)
    return {tool.name: tool for tool in tools}


def vendored(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def registry():
    """The vendored Nogat schemas, so that their ``$ref`` between files resolve."""
    result = Registry()
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        result = result.with_resource(document["$id"], Resource.from_contents(document))
    return result


def inline_refs(schema):
    """The result schema with its ``$ref`` to the other vendored files copied in."""
    schema = json.loads(json.dumps(schema))
    others = {
        "commands-1.schema.json": vendored("commands-1.schema.json"),
        "error-1.schema.json": vendored("error-1.schema.json"),
    }
    definitions = schema["$defs"]

    def walk(node):
        if isinstance(node, dict):
            reference = node.get("$ref", "")
            if reference and not reference.startswith("#"):
                file_name, _, pointer = reference.partition("#")
                name = pointer.rsplit("/", 1)[1]
                assert name not in definitions
                definitions[name] = others[file_name]["$defs"][name]
                walk(definitions[name])
                node["$ref"] = f"#/$defs/{name}"
            for value in list(node.values()):
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return schema


def envelope_of(result):
    """The structured content of a call, after checking the text block repeats it."""
    assert result.structured_content is not None
    assert len(result.content) == 1
    assert json.loads(result.content[0].text) == result.structured_content
    return result.structured_content


def assert_valid_envelope(result):
    document = envelope_of(result)
    schema = default_listing()[0][0].output_schema
    Draft202012Validator(schema).validate(document)
    return document


def error_of(result):
    assert result.is_error is True
    document = envelope_of(result)
    assert document["schema"] == "hydrolog-error/1"
    validator = Draft202012Validator(
        vendored("error-1.schema.json"), registry=registry()
    )
    validator.validate(document)
    return document


def stats_arguments(directory):
    """Call of ``stats mann-kendall`` on a copy of a fixture inside ``directory``."""
    shutil.copy(ROOT / "tests" / "fixtures" / "annual_maxima.csv", directory)
    return {
        "input_file": str(Path(directory) / "annual_maxima.csv"),
        "value_column": "Qmax",
    }


# --- tools: names, descriptions, annotations ------------------------------------------


class TestToolList:
    """``tools/list``: names (AGI-5.2), descriptions (AGI-5.3), annotations (5.4)."""

    @pytest.mark.parametrize("mode", MODES)
    def test_every_catalog_command_is_one_tool_in_catalog_order(self, mode):
        tools, _ = listing(mode)

        assert [tool.name for tool in tools] == [c.operation_id for c in COMMANDS]
        assert [tool.name for tool in listing(mode)[0]] == [t.name for t in tools]

    def test_names_are_short_lowercase_identifiers_with_the_tool_prefix(self):
        for tool in default_listing()[0]:
            assert re.fullmatch(r"hydrolog_[a-z0-9_]+", tool.name), tool.name
            assert len(tool.name) <= 48, tool.name

    def test_descriptions_are_the_catalog_text_within_the_budget(self):
        by_name = {c.operation_id: c for c in COMMANDS}
        for tool in default_listing()[0]:
            command = by_name[tool.name]
            assert tool.description.startswith(command.summary), tool.name
            assert command.description in tool.description, tool.name
            assert len(tool.description) <= 600, tool.name
            assert tool.title == command.summary

    def test_every_tool_has_the_five_annotations(self):
        for tool in default_listing()[0]:
            annotations = tool.annotations
            assert annotations is not None, tool.name
            assert annotations.title
            for hint in (
                annotations.read_only_hint,
                annotations.destructive_hint,
                annotations.idempotent_hint,
                annotations.open_world_hint,
            ):
                assert isinstance(hint, bool), tool.name
            assert annotations.open_world_hint is False
            assert annotations.idempotent_hint is True

    def test_a_read_only_server_reports_every_tool_read_only(self):
        for tool in default_listing()[0]:
            assert tool.annotations.read_only_hint is True, tool.name
            assert tool.annotations.destructive_hint is False, tool.name

    def test_a_server_with_writes_reports_the_writing_tools_as_destructive(
        self, tmp_path
    ):
        tools = tools_by_name(allowed_dirs=[tmp_path], allow_writes=True)

        writing = {c.operation_id for c in WRITING}
        assert writing == {
            "hydrolog_commands_guide",
            "hydrolog_report_generate",
            "hydrolog_route_lag",
            "hydrolog_route_muskingum",
            "hydrolog_route_muskingum_cunge",
            "hydrolog_soil_hsg",
        }
        for name, tool in tools.items():
            expected_write = name in writing
            assert tool.annotations.read_only_hint is not expected_write, name
            assert tool.annotations.destructive_hint is expected_write, name

    @pytest.mark.parametrize("mode", MODES)
    def test_only_the_two_discovery_tools_are_always_loaded(self, mode):
        tools, _ = listing(mode)

        always = [t.name for t in tools if (t.meta or {}).get("anthropic/alwaysLoad")]
        assert always == ALWAYS_LOAD
        assert all(
            "anthropic/alwaysLoad" not in (t.meta or {})
            for t in tools
            if t.name not in ALWAYS_LOAD
        )


class TestSchemas:
    """``inputSchema`` (AGI-5.5) and ``outputSchema`` of the tools."""

    def test_input_schemas_are_closed_documented_2020_12_objects(self):
        for tool in default_listing()[0]:
            schema = tool.input_schema
            Draft202012Validator.check_schema(schema)
            assert schema["type"] == "object", tool.name
            assert schema["additionalProperties"] is False, tool.name
            for name, definition in schema["properties"].items():
                assert definition.get("description"), f"{tool.name}.{name}"
            for keyword in ("oneOf", "anyOf", "allOf"):
                assert keyword not in schema, tool.name

    def test_the_examples_of_a_schema_are_valid_arguments(self):
        for tool in default_listing()[0]:
            validator = Draft202012Validator(tool.input_schema)
            for example in tool.input_schema["examples"]:
                validator.validate(example)

    def test_the_options_of_a_one_of_group_name_the_alternatives(self):
        tools = {t.name: t for t in default_listing()[0]}
        properties = tools["hydrolog_stats_flood_frequency"].input_schema["properties"]

        assert (
            "`values` or `input_file` + `value_column`"
            in properties["values"]["description"]
        )
        assert (
            "`values` or `input_file` + `value_column`"
            in properties["value_column"]["description"]
        )
        assert "alternatives" not in properties["distribution"]["description"]

    def test_the_output_schema_is_the_vendored_result_schema_made_self_contained(self):
        expected = inline_refs(vendored("result-1.schema.json"))
        expected.pop("$id")
        expected["title"] = "hydrolog-result/1"

        assert expected == OUTPUT_SCHEMA
        for tool in default_listing()[0]:
            assert tool.output_schema == expected, tool.name

    @pytest.mark.parametrize(
        ("tool", "arguments"),
        [
            ("hydrolog_cn_lookup", {"hsg": "B", "land_cover": "forest"}),
            ("hydrolog_tc_kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023}),
            ("hydrolog_commands_list", {}),
            ("hydrolog_commands_schema", {"command": "tc kirpich"}),
            ("hydrolog_stats_mann_kendall", {"values": [3.0, 4.5, 4.0, 6.2, 7.9]}),
        ],
    )
    def test_the_structured_content_of_a_call_validates_against_the_output_schema(
        self, tool, arguments
    ):
        result = call(tool, arguments)

        assert result.is_error is False
        document = assert_valid_envelope(result)
        assert document["command"] == get_command(tool).name

    def test_a_plan_validates_against_the_output_schema_too(self, tmp_path):
        result = call(
            "hydrolog_commands_guide",
            {"format": "llms", "output": str(tmp_path / "llms.txt")},
            allowed_dirs=[tmp_path],
        )

        document = assert_valid_envelope(result)
        assert document["result"]["schema"] == "hydrolog-plan/1"


class TestInstructions:
    """The server ``instructions`` (AGI-5.10, DOC-1.7)."""

    def test_they_fit_the_budget_and_are_english(self, tmp_path):
        for kwargs in (
            {},
            {"allowed_dirs": [tmp_path], "allow_writes": True, "families": ["core"]},
        ):
            _, instructions = listing(**kwargs)

            assert instructions
            assert len(instructions) <= 4096
            assert not re.search("[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", instructions)

    def test_they_state_the_workflow_the_limits_and_the_provenance_of_data(self):
        _, instructions = default_listing()

        assert "discover" in instructions
        assert "hydrolog_commands_list" in instructions
        assert "hydrolog_commands_schema" in instructions
        assert "check" in instructions
        assert "Kartograf" in instructions
        assert "IMGWTools" in instructions
        assert "No allowed directory" in instructions
        assert "Read-only" in instructions

    def test_they_follow_the_state_of_the_server(self, tmp_path):
        _, instructions = listing(
            allowed_dirs=[tmp_path], allow_writes=True, families=["stats", "core"]
        )

        assert str(tmp_path.resolve()) in instructions
        assert "Writes are enabled" in instructions
        assert "stats, core" in instructions
        assert "Read-only" not in instructions


# --- calls ----------------------------------------------------------------------------


class TestCalls:
    """Results and errors (AGI-5.5, AGI-5.7)."""

    @pytest.mark.parametrize("mode", MODES)
    def test_a_read_only_call_returns_the_envelope_as_structured_content_and_text(
        self, mode
    ):
        arguments = {"hsg": "B", "land_cover": "forest"}

        result = call("hydrolog_cn_lookup", arguments, mode=mode)

        assert result.is_error is False
        document = assert_valid_envelope(result)
        assert document == run_command("cn lookup", arguments).to_dict()
        assert document["result"]["cn"] == 60

    def test_the_default_pages_of_the_discovery_tools_fit_the_result_budget(self):
        for tool, arguments in (
            ("hydrolog_commands_list", {}),
            ("hydrolog_commands_schema", {}),
            ("hydrolog_commands_schema", {"command": "report generate"}),
        ):
            result = call(tool, arguments)

            assert result.is_error is False
            assert len(result.content[0].text) <= 20_000, tool

    def test_the_discovery_tools_page_the_catalog(self):
        first = envelope_of(call("hydrolog_commands_list", {"limit": 5}))
        second = envelope_of(
            call(
                "hydrolog_commands_list",
                {"limit": 5, "cursor": first["page"]["next_cursor"]},
            )
        )

        assert first["page"]["truncated"] is True
        assert first["page"]["total"] == len(COMMANDS)
        assert first["result"]["commands"][0] != second["result"]["commands"][0]

    def test_an_invalid_option_is_an_error_result_with_code_hint_and_details(self):
        result = call("hydrolog_cn_lookup", {"hsg": "Z", "land_cover": "forest"})

        error = error_of(result)
        assert error["code"] == "validation_error"
        assert error["exit_code"] == 2
        assert error["command"] == "cn lookup"
        assert error["hint"]
        assert error["details"]["option"] == "hsg"
        assert error["details"]["allowed"] == ["A", "B", "C", "D"]
        assert error["code"] in ERROR_CODES

    def test_an_unknown_option_is_a_validation_error_not_a_protocol_error(self):
        error = error_of(call("hydrolog_cn_lookup", {"bogus": 1}))

        assert error["code"] == "validation_error"
        assert error["details"]["reason"] == "unknown_option"

    def test_the_error_title_is_english(self):
        error = error_of(call("hydrolog_cn_lookup", {"hsg": "Z"}))

        assert error["title"] == "Invalid input"

    def test_an_unknown_tool_is_a_protocol_error_with_a_suggestion(self):
        async def scenario():
            async with connected() as client:
                with pytest.raises(MCPError) as caught:
                    await client.call_tool("hydrolog_cn_lookpu", {})
                return caught.value

        error = anyio.run(scenario)

        assert error.error.code == types.INVALID_PARAMS
        assert "hydrolog_cn_lookup" in error.error.message

    def test_a_tool_outside_the_selected_families_is_a_protocol_error(self):
        async def scenario():
            async with connected(families=["stats"]) as client:
                with pytest.raises(MCPError) as caught:
                    await client.call_tool("hydrolog_cn_lookup", {})
                return caught.value

        assert anyio.run(scenario).error.code == types.INVALID_PARAMS

    def test_two_calls_of_one_connection_run_at_the_same_time(self):
        """A call runs in a worker thread: a second one is served meanwhile."""
        inside = threading.Barrier(2)
        original = run_command

        def meeting(command, options=None, *, allowed_dirs=None):
            inside.wait(timeout=20)  # returns only when both calls are inside
            return original(command, options, allowed_dirs=allowed_dirs)

        async def scenario():
            answers = []

            async def one(client, hsg):
                answers.append(
                    await client.call_tool(
                        "hydrolog_cn_lookup", {"hsg": hsg, "land_cover": "forest"}
                    )
                )

            async with connected() as client, anyio.create_task_group() as group:
                group.start_soon(one, client, "B")
                group.start_soon(one, client, "C")
            return answers

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr("hydrolog.mcp._calls.run_command", meeting)
            answers = anyio.run(scenario)

        assert [a.is_error for a in answers] == [False, False]


# --- paths and writes -----------------------------------------------------------------


class TestPathPolicy:
    """``--allow-dir`` (AGI-5.8): every path option is checked."""

    def test_without_allowed_directories_every_path_option_is_forbidden(self, tmp_path):
        arguments = stats_arguments(tmp_path)

        error = error_of(call("hydrolog_stats_mann_kendall", arguments))

        assert error["code"] == "forbidden"
        assert error["exit_code"] == ERROR_CODES["forbidden"].exit_code
        assert error["details"]["option"] == "input_file"
        assert error["details"]["allowed_dirs"] == []
        assert error["hint"]

    def test_commands_that_take_values_work_without_allowed_directories(self):
        result = call(
            "hydrolog_stats_mann_kendall", {"values": [1.0, 2.0, 4.0, 3.0, 6]}
        )

        assert result.is_error is False

    def test_a_file_inside_an_allowed_directory_is_read(self, tmp_path):
        arguments = stats_arguments(tmp_path)

        result = call("hydrolog_stats_mann_kendall", arguments, allowed_dirs=[tmp_path])

        assert result.is_error is False
        assert envelope_of(result)["inputs"]["input_file"] == str(
            (tmp_path / "annual_maxima.csv").resolve()
        )

    def test_a_file_outside_the_allowed_directories_is_forbidden(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        arguments = stats_arguments(outside)

        error = error_of(
            call("hydrolog_stats_mann_kendall", arguments, allowed_dirs=[allowed])
        )

        assert error["code"] == "forbidden"
        assert error["details"]["allowed_dirs"] == [str(allowed.resolve())]
        assert error["details"]["path"] == str(
            (outside / "annual_maxima.csv").resolve()
        )

    def test_a_relative_path_cannot_escape_through_dot_dot(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        (tmp_path / "secret.csv").write_text("Q\n1\n2\n3\n", encoding="utf-8")

        error = error_of(
            call(
                "hydrolog_stats_mann_kendall",
                {"input_file": str(allowed / ".." / "secret.csv"), "value_column": "Q"},
                allowed_dirs=[allowed],
            )
        )

        assert error["code"] == "forbidden"

    def test_a_missing_allowed_directory_is_refused_when_the_server_is_created(
        self, tmp_path
    ):
        with pytest.raises(NotFoundError):
            create_server(allowed_dirs=[tmp_path / "missing"])
        with pytest.raises(InvalidParameterError):
            create_server(allowed_dirs=[""])


class TestWriteModes:
    """``--allow-writes`` (AGI-5.8, DEV-19.3): plans without it, writes with it."""

    guide = staticmethod(
        lambda directory, **extra: {
            "format": "llms",
            "output": str(Path(directory) / "llms.txt"),
            **extra,
        }
    )

    def test_without_allow_writes_a_writing_tool_only_plans(self, tmp_path):
        arguments = self.guide(tmp_path, force=True, check=False)

        result = call("hydrolog_commands_guide", arguments, allowed_dirs=[tmp_path])

        document = envelope_of(result)
        assert result.is_error is False
        assert document["check"] is True
        assert document["result"]["schema"] == "hydrolog-plan/1"
        assert [t["action"] for t in document["result"]["targets"]] == ["write"]
        assert not (tmp_path / "llms.txt").exists()

    def test_without_allow_writes_force_is_ignored(self, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")

        result = call(
            "hydrolog_commands_guide",
            self.guide(tmp_path, force=True),
            allowed_dirs=[tmp_path],
        )

        targets = envelope_of(result)["result"]["targets"]
        assert targets[0]["action"] == "conflict"
        assert targets[0]["reason"] == "output_exists"
        assert target.read_text(encoding="utf-8") == "mine"

    def test_a_plan_still_obeys_the_allowed_directories(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        error = error_of(
            call(
                "hydrolog_commands_guide",
                self.guide(tmp_path),
                allowed_dirs=[allowed],
            )
        )

        assert error["code"] == "forbidden"

    def test_the_schema_of_a_plan_only_tool_says_so(self):
        properties = tools_by_name()["hydrolog_commands_guide"].input_schema[
            "properties"
        ]

        assert properties["check"]["default"] is True
        assert "read-only" in properties["check"]["description"]
        assert "Ignored" in properties["force"]["description"]
        assert "plans" in properties["output"]["description"]

    def test_with_allow_writes_the_file_is_written_and_reported(self, tmp_path):
        result = call(
            "hydrolog_commands_guide",
            self.guide(tmp_path),
            allowed_dirs=[tmp_path],
            allow_writes=True,
        )

        document = assert_valid_envelope(result)
        target = tmp_path / "llms.txt"
        assert result.is_error is False
        assert document["check"] is False
        record = document["result"]["files"][0]
        assert record["path"] == str(target.resolve())
        assert record["status"] == "written"
        assert record["size_bytes"] == target.stat().st_size

    def test_with_allow_writes_an_existing_file_is_a_conflict_without_force(
        self, tmp_path
    ):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")

        error = error_of(
            call(
                "hydrolog_commands_guide",
                self.guide(tmp_path),
                allowed_dirs=[tmp_path],
                allow_writes=True,
            )
        )

        assert error["code"] == "conflict"
        assert error["details"]["reason"] == "output_exists"
        assert error["details"]["paths"] == [str(target.resolve())]
        assert target.read_text(encoding="utf-8") == "mine"

    def test_with_allow_writes_force_replaces_the_file(self, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")

        result = call(
            "hydrolog_commands_guide",
            self.guide(tmp_path, force=True),
            allowed_dirs=[tmp_path],
            allow_writes=True,
        )

        assert result.is_error is False
        assert envelope_of(result)["result"]["files"][0]["status"] == "replaced"
        assert target.read_text(encoding="utf-8") != "mine"

    def test_with_allow_writes_check_still_plans(self, tmp_path):
        result = call(
            "hydrolog_commands_guide",
            self.guide(tmp_path, check=True),
            allowed_dirs=[tmp_path],
            allow_writes=True,
        )

        assert envelope_of(result)["check"] is True
        assert not (tmp_path / "llms.txt").exists()

    def test_with_allow_writes_the_output_must_lie_in_an_allowed_directory(
        self, tmp_path
    ):
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        error = error_of(
            call(
                "hydrolog_commands_guide",
                self.guide(tmp_path),
                allowed_dirs=[allowed],
                allow_writes=True,
            )
        )

        assert error["code"] == "forbidden"
        assert not (tmp_path / "llms.txt").exists()

    def test_a_server_without_directories_writes_nothing_even_with_allow_writes(
        self, tmp_path
    ):
        error = error_of(
            call(
                "hydrolog_commands_guide",
                self.guide(tmp_path),
                allow_writes=True,
            )
        )

        assert error["code"] == "forbidden"


class TestRouteWithoutAnOutput:
    """A routing tool computes on a read-only server unless it has a file to plan."""

    inflow = {"times_min": [0, 10, 20, 30, 40], "discharge_m3s": [0, 10, 40, 20, 0]}

    def test_a_read_only_server_returns_the_routed_hydrograph(self):
        result = call("hydrolog_route_lag", {"lag_min": 20, **self.inflow})

        document = assert_valid_envelope(result)
        assert result.is_error is False
        assert document["check"] is False
        assert document["result"]["schema"] == "hydrolog-route-lag/1"
        assert document["result"]["outflow_m3s"][:6] == [0, 0, 0, 10, 40, 20]
        assert "files" not in document["result"]

    def test_a_read_only_server_plans_the_output_file(self, tmp_path):
        target = tmp_path / "outflow.csv"

        result = call(
            "hydrolog_route_lag",
            {"lag_min": 20, "output": str(target), **self.inflow},
            allowed_dirs=[tmp_path],
        )

        document = envelope_of(result)
        assert document["check"] is True
        assert document["result"]["schema"] == "hydrolog-plan/1"
        assert not target.exists()

    def test_a_server_with_writes_writes_the_output_file(self, tmp_path):
        target = tmp_path / "outflow.csv"

        result = call(
            "hydrolog_route_lag",
            {"lag_min": 20, "output": str(target), **self.inflow},
            allowed_dirs=[tmp_path],
            allow_writes=True,
        )

        document = assert_valid_envelope(result)
        assert document["check"] is False
        assert document["result"]["outflow_m3s"] is None
        assert document["result"]["files"][0]["status"] == "written"
        assert target.read_text(encoding="utf-8").startswith("time_min,discharge_m3s")


# --- families -------------------------------------------------------------------------


class TestFamilies:
    """``--tools`` (AGI-5.8) and the ``core`` family (AGI-5.12)."""

    def test_a_group_family_exposes_the_commands_of_the_group(self):
        tools = tools_by_name(families=["stats"])

        assert list(tools) == [
            c.operation_id for c in COMMANDS if c.name.startswith("stats ")
        ]

    def test_the_core_family_has_at_most_ten_tools_including_discovery(self):
        tools = tools_by_name(families=["core"])

        assert list(tools) == [c.operation_id for c in COMMANDS if c.core]
        assert 0 < len(tools) <= 10
        assert set(ALWAYS_LOAD) <= set(tools)

    def test_several_families_are_joined_in_catalog_order(self):
        tools = tools_by_name(families=["scs", "tc"])

        assert list(tools) == [
            c.operation_id for c in COMMANDS if c.name.split()[0] in ("scs", "tc")
        ]

    def test_an_unknown_family_lists_the_allowed_ones(self):
        with pytest.raises(InvalidParameterError) as caught:
            create_server(families=["stat"])

        error = caught.value
        assert error.details["reason"] == "choice"
        assert "core" in error.details["allowed"]
        assert "stats" in error.details["allowed"]
        assert "stats" in str(error)

    def test_an_empty_list_of_families_is_refused(self):
        with pytest.raises(InvalidParameterError):
            create_server(families=[])


# --- console script and ``hydrolog mcp`` ----------------------------------------------


def script_entry(name):
    """``module:function`` of a console script declared in pyproject."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["scripts"][name]


def launcher_arguments(launcher, *server_arguments, prelude=""):
    """Arguments of ``sys.executable`` that start a server through a console script:
    ``hydrolog-mcp`` or ``hydrolog mcp``."""
    name, words = (
        ("hydrolog-mcp", []) if launcher == "console" else ("hydrolog", ["mcp"])
    )
    module, _, function = script_entry(name).partition(":")
    code = (
        f"{prelude}import sys; from {module} import {function}; "
        f"sys.exit({function}({words!r} + sys.argv[1:]))"
    )
    return ["-c", code, *server_arguments]


LAUNCHERS = ["console", "cli"]


class TestCommandLine:
    """The options are the same in ``hydrolog-mcp`` and in ``hydrolog mcp``."""

    def test_the_console_script_points_at_the_server_module(self):
        assert script_entry("hydrolog-mcp") == "hydrolog.mcp.server:main"

    def test_an_unknown_family_is_a_validation_error_on_stderr(self, capsys):
        status = main(["--tools", "bogus"])

        captured = capsys.readouterr()
        document = json.loads(captured.err)
        assert status == 2
        assert captured.out == ""
        assert document["schema"] == "hydrolog-error/1"
        assert document["code"] == "validation_error"
        assert "core" in document["details"]["allowed"]

    def test_a_missing_directory_is_a_not_found_error_on_stderr(self, capsys, tmp_path):
        status = main(["--allow-dir", str(tmp_path / "missing")])

        assert status == 3
        assert json.loads(capsys.readouterr().err)["code"] == "not_found"

    def test_the_server_has_no_language_option(self, capsys):
        status = main(["--lang", "en"])

        captured = capsys.readouterr()
        document = json.loads(captured.err)
        assert (status, captured.out) == (2, "")
        assert document["code"] == "validation_error"
        assert document["details"]["reason"] == "usage"
        assert "--lang" in document["message"]

    def test_help_lists_the_three_server_options(self, capsys):
        status = main(["--help"])

        assert status == 0
        output = capsys.readouterr().out
        for option in ("--allow-dir", "--allow-writes", "--tools"):
            assert option in output

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_a_process_serves_the_selected_tools_over_a_pipe(self, launcher, tmp_path):
        server = StdioServerParameters(
            command=sys.executable,
            args=launcher_arguments(
                launcher, "--allow-dir", str(tmp_path), "--tools", "core"
            ),
            env=dict(os.environ),
            cwd=ROOT,
        )

        async def scenario(log):
            async with Client(stdio_client(server, errlog=log)) as client:
                tools = (await client.list_tools()).tools
                answer = await client.call_tool(
                    "hydrolog_cn_lookup", {"hsg": "B", "land_cover": "forest"}
                )
                return tools, client.instructions, answer

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            tools, instructions, answer = anyio.run(scenario, log)

        assert [t.name for t in tools] == [c.operation_id for c in COMMANDS if c.core]
        assert str(tmp_path.resolve()) in instructions
        assert answer.is_error is False
        assert assert_valid_envelope(answer)["result"]["cn"] == 60

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_a_process_obeys_the_directories_and_the_write_mode_of_its_command_line(
        self, launcher, tmp_path
    ):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        server = StdioServerParameters(
            command=sys.executable,
            args=launcher_arguments(
                launcher, "--allow-dir", str(allowed), "--allow-writes"
            ),
            env=dict(os.environ),
            cwd=ROOT,
        )

        async def scenario(log):
            async with Client(stdio_client(server, errlog=log)) as client:
                tools = (await client.list_tools()).tools
                written = await client.call_tool(
                    "hydrolog_commands_guide",
                    {"format": "llms", "output": str(allowed / "llms.txt")},
                )
                refused = await client.call_tool(
                    "hydrolog_commands_guide",
                    {"format": "llms", "output": str(outside / "llms.txt")},
                )
                return tools, written, refused

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            tools, written, refused = anyio.run(scenario, log)

        guide = next(t for t in tools if t.name == "hydrolog_commands_guide")
        assert guide.annotations.read_only_hint is False
        assert written.is_error is False
        assert (allowed / "llms.txt").is_file()
        assert error_of(refused)["code"] == "forbidden"
        assert not (outside / "llms.txt").exists()

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_the_process_ends_cleanly_without_a_byte_on_stdout_when_stdin_closes(
        self, launcher, tmp_path
    ):
        finished = subprocess.run(
            [
                sys.executable,
                *launcher_arguments(launcher, "--allow-dir", str(tmp_path)),
            ],
            input=b"",
            capture_output=True,
            cwd=ROOT,
            timeout=120,
            check=False,
        )

        assert (finished.returncode, finished.stdout) == (0, b""), finished.stderr

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_a_process_without_the_sdk_reports_the_missing_extra(self, launcher):
        """Hiding ``mcp`` from the import system gives ``missing_dependency``."""
        prelude = "import sys; sys.modules['mcp'] = sys.modules['mcp_types'] = None; "
        finished = subprocess.run(
            [sys.executable, *launcher_arguments(launcher, prelude=prelude)],
            input=b"",
            capture_output=True,
            cwd=ROOT,
            timeout=120,
            check=False,
        )

        assert finished.returncode == ERROR_CODES["missing_dependency"].exit_code
        assert finished.stdout == b""
        assert b"hydrolog[mcp]" in finished.stderr


# --- cold start -----------------------------------------------------------------------

COLD_START_SERVER = """\
import atexit, json, sys
from hydrolog.mcp.server import main

HEAVY = {heavy!r}
atexit.register(
    lambda: print(
        "LOADED " + json.dumps([m for m in HEAVY if m in sys.modules]), file=sys.stderr
    )
)
sys.exit(main(sys.argv[1:]))
"""


class TestColdStart:
    """Cold start and ``tools/list`` take under 5 seconds (AGI-5.11)."""

    def test_the_start_and_the_tool_list_are_fast_and_import_no_numerical_library(
        self, tmp_path
    ):
        script = tmp_path / "server.py"
        script.write_text(
            COLD_START_SERVER.format(heavy=HEAVY_MODULES), encoding="utf-8"
        )
        server = StdioServerParameters(
            command=sys.executable, args=[str(script)], env=dict(os.environ), cwd=ROOT
        )

        async def scenario(log):
            started = time.perf_counter()
            async with Client(stdio_client(server, errlog=log)) as client:
                tools = (await client.list_tools()).tools
                elapsed = time.perf_counter() - started
            return tools, elapsed

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            tools, elapsed = anyio.run(scenario, log)
            log.seek(0)
            report = [ln for ln in log.read().splitlines() if ln.startswith("LOADED ")]

        assert len(tools) == len(COMMANDS)
        assert elapsed < 5, f"start + tools/list took {elapsed:.1f} s"
        assert report, "the server did not report its modules at exit"
        assert json.loads(report[-1].removeprefix("LOADED ")) == []

    def test_a_call_loads_the_operation_lazily(self, tmp_path):
        """The heavy libraries come with the first call that needs them, not before."""
        script = tmp_path / "server.py"
        script.write_text(
            COLD_START_SERVER.format(heavy=HEAVY_MODULES), encoding="utf-8"
        )
        server = StdioServerParameters(
            command=sys.executable, args=[str(script)], env=dict(os.environ), cwd=ROOT
        )

        async def scenario(log):
            async with Client(stdio_client(server, errlog=log)) as client:
                return await client.call_tool(
                    "hydrolog_tc_kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023}
                )

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            result = anyio.run(scenario, log)
            log.seek(0)
            report = [ln for ln in log.read().splitlines() if ln.startswith("LOADED ")]

        assert result.is_error is False
        assert "numpy" in json.loads(report[-1].removeprefix("LOADED "))


# --- stdout belongs to the protocol ---------------------------------------------------

NOISY_SERVER = """\
import sys
import hydrolog.mcp.server as server
from hydrolog.catalog import Command, data_commands


def noisy():
    print("stray text of an operation")
    return {"ok": True}


demo = Command(
    name="demo noisy",
    operation_id="hydrolog_demo_noisy",
    summary="Prints to stdout.",
    summary_pl="Drukuje na stdout.",
    description="Prints a line to stdout and returns.",
    description_pl="Drukuje linię na stdout i wraca.",
    function="__main__.noisy",
    options=(),
    examples=({},),
    example_results=({},),
    result_schema="hydrolog-demo-noisy/1",
)
catalog = (*data_commands(), demo)
server.data_commands = lambda: catalog
sys.exit(server.main([]))
"""


class TestStdout:
    def test_stray_output_of_an_operation_goes_to_stderr_never_to_the_client(
        self, tmp_path
    ):
        """A ``print`` inside an operation must not add a line to the protocol stream,
        neither during the session nor when the server shuts down."""
        script = tmp_path / "noisy_server.py"
        script.write_text(NOISY_SERVER, encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=ROOT,
            # clients start servers without PYTHONUNBUFFERED: stdout is block-buffered
            env={k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"},
        )
        watchdog = threading.Timer(120, process.kill)
        watchdog.start()

        def send(message):
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        try:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "0"},
                    },
                }
            )
            assert json.loads(process.stdout.readline())["id"] == 1
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "hydrolog_demo_noisy", "arguments": {}},
                }
            )
            answer = json.loads(process.stdout.readline())
            rest, errors = process.communicate(timeout=120)  # closes stdin: shutdown
        finally:
            watchdog.cancel()
            process.kill()

        assert answer["id"] == 2
        assert answer["result"]["isError"] is False
        assert answer["result"]["structuredContent"]["result"] == {
            "schema": "hydrolog-demo-noisy/1",
            "ok": True,
        }
        assert rest == ""
        assert "stray text of an operation" in errors
        assert process.returncode == 0
