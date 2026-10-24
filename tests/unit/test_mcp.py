"""Tests for the MCP server: the catalog as tools, calls, errors, path policy, stdio.

The SDK client talks to the server in memory (``Client(create_server(...))``); one test
class starts the server as a real process on stdio. Commands of the real catalog are
exercised through their catalog examples; behaviours that need a particular shape of
command (path options, ``one_of``, failing operations) use private demo commands that
replace the catalog of the server for one test.
"""

import contextlib
import errno
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import anyio
import mcp.types as types
from jsonschema import Draft202012Validator
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import MCPError

from hydrolog.agent_guide import principles
from hydrolog.catalog import (
    Command,
    OperationOutput,
    Option,
    command_schema,
    data_commands,
    run_command,
)
from hydrolog.exceptions import (
    ERROR_CODES,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
)
from hydrolog.mcp import create_server, run_stdio
from hydrolog.mcp._instructions import MAX_BYTES, build_instructions
from hydrolog.time import ConcentrationTime

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = data_commands()
MODES = ["legacy", "auto"]


# --- demo operations and commands -----------------------------------------------------

MEETING = threading.Barrier(2)


def add_operation(*, a_km: float, b_km: float = 1.0):
    """Add two lengths."""
    return {"sum_km": a_km + b_km}


def series_operation(*, values=None, dates=None, input_file=None, value_column=None):
    """Report which group of the options arrived."""
    return {"values": values, "input_file": input_file, "column": value_column}


def copy_operation(*, input_file: str, output_file: str):
    """Write the upper-cased input to the output file and report it."""
    text = Path(input_file).read_text(encoding="utf-8").upper()
    Path(output_file).write_text(text, encoding="utf-8")
    return OperationOutput(result={"chars": len(text)}, files=(output_file,))


def nan_operation(*, x_mm: float):
    """Return a result with non-finite numbers and a tuple."""
    return {"value": float("nan"), "limit": float("inf"), "pair": (1, x_mm)}


def pick_operation(*, shape=None, shape_file=None):
    """Report which of the two alternative options arrived."""
    return {"shape": shape, "shape_file": shape_file}


def note_operation(*, note_path=None):
    """Write a note when asked to."""
    if note_path is None:
        return {"written": False}
    Path(note_path).write_text("note", encoding="utf-8")
    return OperationOutput(result={"written": True}, files=(note_path,))


def boom_operation():
    """Fail like a bug."""
    raise RuntimeError("boom")


def disk_operation():
    """Fail like a file-system error that no operation wrapped."""
    raise PermissionError(errno.EACCES, "Permission denied", "/data/x")


def meet_operation(*, label: str):
    """Wait until a second call is inside an operation too."""
    MEETING.wait(timeout=20)
    return {"label": label}


def _option(name, type_, **kwargs):
    return Option(name, type_, f"Opis {name}", f"Description {name}", **kwargs)


def _command(name, operation, *options, **kwargs):
    return Command(
        name=name,
        operation_id=name.replace(" ", "_").replace("-", "_"),
        summary=f"Podsumowanie {name}.",
        summary_en=f"Summary of {name}.",
        description=f"Opis komendy {name}.",
        description_en=f"Description of the command {name}.",
        function=f"{__name__}:{operation}",
        options=options,
        **kwargs,
    )


DEMO = (
    _command(
        "demo add",
        "add_operation",
        _option("a_km", "number", required=True, exclusive_minimum=0, unit="km"),
        _option("b_km", "number", default=1.0, unit="km"),
        examples=({"a_km": 2.5},),
    ),
    _command(
        "demo series",
        "series_operation",
        _option("values", "number_list"),
        _option("dates", "string_list"),
        _option("input_file", "path"),
        _option("value_column", "string"),
        one_of=(("values", "dates"), ("input_file", "value_column")),
        examples=({"values": [1, 2], "dates": ["2020-01-01", "2020-01-02"]},),
    ),
    _command(
        "demo copy",
        "copy_operation",
        _option("input_file", "path", required=True),
        _option("output_file", "path", required=True, writes=True),
        writes=True,
        examples=({"input_file": "in.txt", "output_file": "out.txt"},),
    ),
    _command(
        "demo nan",
        "nan_operation",
        _option("x_mm", "number", required=True),
        examples=({"x_mm": 3},),
    ),
    _command(
        "demo pick",
        "pick_operation",
        _option("shape", "object"),
        _option("shape_file", "path"),
        one_of=(("shape",), ("shape_file",)),
        examples=({"shape": {"area_km2": 1}},),
    ),
    _command(
        "demo note",
        "note_operation",
        _option("note_path", "path", writes=True),
        writes=True,
        examples=({},),
    ),
    _command("demo boom", "boom_operation", examples=({},)),
    _command("demo disk", "disk_operation", examples=({},)),
    _command(
        "demo meet",
        "meet_operation",
        _option("label", "string", required=True),
        examples=({"label": "a"},),
    ),
)


@pytest.fixture
def demo_catalog(monkeypatch):
    """The server serves the real catalog plus the demo commands (group ``demo``)."""
    commands = (*data_commands(), *DEMO)
    monkeypatch.setattr("hydrolog.mcp.server.data_commands", lambda: commands)
    MEETING.reset()
    return commands


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


def protocol_error(tool, arguments=None, **server_kwargs):
    """The MCP error a call of ``tool`` raises on a fresh in-memory server."""

    async def scenario():
        async with connected(**server_kwargs) as client:
            with pytest.raises(MCPError) as caught:
                await client.call_tool(tool, arguments)
            return caught.value

    return anyio.run(scenario)


def compact(document):
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"))


def document_of(result):
    """Structured content of a tool result; its only text content is the same JSON."""
    assert len(result.content) == 1
    assert result.content[0].type == "text"
    assert json.loads(result.content[0].text) == result.structured_content
    return result.structured_content


def error_of(result):
    assert result.is_error is True
    document = document_of(result)
    assert document["schema"] == "hydrolog-error/1"
    return document


def has_path_option(command, example):
    paths = {option.name for option in command.options if option.type == "path"}
    return bool(paths & set(example))


def catalog_examples(*, with_paths):
    return [
        pytest.param(command, example, id=f"{command.operation_id}-{index}")
        for command in COMMANDS
        for index, example in enumerate(command.examples)
        if has_path_option(command, example) is with_paths
    ]


# --- the tool list
# ---------------------------------------------------------------------


class TestTools:
    """``tools/list``: one tool per catalog command."""

    @pytest.mark.parametrize("mode", MODES)
    def test_one_tool_per_command_in_catalog_order(self, mode):
        """Tool names are the ``operation_id`` of every command, in catalog order."""
        tools, _ = listing(mode)

        assert len(tools) == len(data_commands())
        assert [tool.name for tool in tools] == [c.operation_id for c in COMMANDS]

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_texts_come_from_the_catalog_in_the_server_language(self, lang):
        """Title is ``hydrolog <name>``; the description starts with the catalog's."""
        tools, _ = listing(lang=lang)

        for tool, command in zip(tools, COMMANDS, strict=True):
            assert tool.title == f"hydrolog {command.name}"
            assert tool.description.startswith(command.describe(lang))

    def test_annotations_state_whether_the_command_writes(self):
        """Read-only and non-destructive unless the command writes (its output file is
        replaced); always idempotent, never open-world."""
        tools, _ = listing()

        for tool, command in zip(tools, COMMANDS, strict=True):
            hints = tool.annotations
            assert hints.read_only_hint is (not command.writes), command.name
            assert hints.destructive_hint is command.writes, command.name
            assert hints.idempotent_hint is True
            assert hints.open_world_hint is False

    def test_a_writing_command_is_neither_read_only_nor_harmless(self, demo_catalog):
        """File output means not read-only and destructive; a pure command is
        neither."""
        tools = {tool.name: tool for tool in listing()[0]}

        for name in ("demo_copy", "demo_note"):
            assert tools[name].annotations.read_only_hint is False
            assert tools[name].annotations.destructive_hint is True
        assert tools["demo_add"].annotations.read_only_hint is True
        assert tools["demo_add"].annotations.destructive_hint is False

    def test_input_schemas_are_the_catalog_schemas_a_client_can_pass_on(self):
        """The properties and requirements of the catalog, with no ``$schema`` and no
        top-level ``oneOf``/``anyOf``/``allOf`` (model APIs reject those)."""
        tools, _ = listing()

        for tool, command in zip(tools, COMMANDS, strict=True):
            schema = tool.input_schema
            catalog = command_schema(command)["commands"][0]["input_schema"]
            Draft202012Validator.check_schema(schema)
            assert not {"$schema", "oneOf", "anyOf", "allOf"} & set(schema)
            assert schema["type"] == "object"
            assert schema["additionalProperties"] is False
            assert schema.get("required") == catalog.get("required")
            assert list(schema["properties"]) == [o.name for o in command.options]
            for name, prop in schema["properties"].items():
                expected = dict(catalog["properties"][name])
                if name == "lang":
                    expected["default"] = "pl"
                assert prop == expected, (command.name, name)

    def test_the_schema_accepts_every_catalog_example(self):
        """What the catalog calls a valid example validates against the tool schema."""
        tools, _ = listing()

        for tool, command in zip(tools, COMMANDS, strict=True):
            validator = Draft202012Validator(tool.input_schema)
            for example in command.examples:
                assert validator.is_valid(example), (command.name, example)

    def test_option_groups_are_named_in_the_description_not_in_the_schema(
        self, demo_catalog
    ):
        """``one_of`` leaves the schema (top-level ``oneOf``) but not the contract."""
        tools = {tool.name: tool for tool in listing()[0]}
        series = tools["demo_series"]

        assert "oneOf" not in series.input_schema
        assert (
            "Podaj dokładnie jedną z grup opcji: (`values`, `dates`) albo "
            "(`input_file`, `value_column`)."
        ) in series.description
        assert tools["demo_add"].description == "Opis komendy demo add."

    def test_option_groups_are_named_in_english_too(self, demo_catalog):
        tools = {tool.name: tool for tool in listing(lang="en")[0]}

        assert (
            "Give exactly one of these option groups: (`values`, `dates`) or "
            "(`input_file`, `value_column`)."
        ) in tools["demo_series"].description

    @pytest.mark.parametrize(
        ("lang", "sentence"),
        [
            ("pl", "Podaj dokładnie jedną z opcji: `shape` albo `shape_file`."),
            ("en", "Give exactly one of these options: `shape` or `shape_file`."),
        ],
    )
    def test_alternative_single_options_are_named_as_options(
        self, demo_catalog, lang, sentence
    ):
        """Groups of one option each read as a choice of options, not of groups."""
        tools = {tool.name: tool for tool in listing(lang=lang)[0]}

        assert tools["demo_pick"].description.endswith(sentence)
        assert "oneOf" not in tools["demo_pick"].input_schema

    def test_output_options_are_named_in_the_description(self, demo_catalog):
        """A writing command says which options it writes and where they may point."""
        tools = {tool.name: tool for tool in listing()[0]}

        assert (
            "Zapisuje pliki (opcje wyjściowe: `output_file`); ścieżki muszą leżeć "
            "w katalogach dozwolonych serwera."
        ) in tools["demo_copy"].description

    @pytest.mark.parametrize(
        ("lang", "sentence"),
        [
            (
                "pl",
                "Zapisuje plik tylko wtedy, gdy podasz opcję wyjściową (`note_path`); "
                "ścieżka musi leżeć w katalogu dozwolonym serwera.",
            ),
            (
                "en",
                "Writes a file only when you give the output option (`note_path`); "
                "the path must lie inside a directory allowed by the server.",
            ),
        ],
    )
    def test_an_optional_output_option_is_described_as_optional(
        self, demo_catalog, lang, sentence
    ):
        """A command that writes only on request says so, and is still not read-only."""
        tools = {tool.name: tool for tool in listing(lang=lang)[0]}

        assert tools["demo_note"].description.endswith(sentence)
        assert tools["demo_note"].annotations.read_only_hint is False

    def test_language_option_defaults_to_the_server_language(self):
        """The schema of a ``lang`` option shows the server language as default."""
        for lang in ("pl", "en"):
            tools = {tool.name: tool for tool in listing(lang=lang)[0]}
            prop = tools["commands_list"].input_schema["properties"]["lang"]
            assert prop["default"] == lang
            assert prop["enum"] == ["pl", "en"]


# --- the instructions
# ------------------------------------------------------------------


class TestInstructions:
    """The ``instructions`` of the server: the rules of the agent guide, in short."""

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_instructions_are_short_and_carry_the_rules_of_the_guide(self, lang):
        """Every rule of the guide, the discovery tools and the documents appear."""
        _, instructions = listing(lang=lang)

        assert len(instructions.encode("utf-8")) <= MAX_BYTES
        for rule in principles(lang):
            assert rule in instructions
        for tool in ("commands_list", "commands_schema", "commands_guide"):
            assert tool in instructions
        assert "hydrolog-result/1" in instructions
        assert "hydrolog-error/1" in instructions

    def test_instructions_follow_the_server_language(self):
        assert "Zasady:" in listing(lang="pl")[1]
        assert "Rules:" in listing(lang="en")[1]
        assert "Zasady:" not in listing(lang="en")[1]

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_allowed_directories_are_listed(self, tmp_path, lang):
        """The agent learns where it may read and write."""
        data = tmp_path / "data"
        other = tmp_path / "other"

        _, instructions = listing(lang=lang, allowed_dirs=[data, other])

        assert f"{data.resolve()}, {other.resolve()}" in instructions
        assert "(--allow-dir)" not in instructions

    def test_without_directories_files_are_declared_refused(self):
        """No allowed directory: the text says path options are refused."""
        _, pl = listing()
        _, en = listing(lang="en")

        assert "Brak katalogów dozwolonych (--allow-dir)" in pl
        assert "No allowed directories (--allow-dir)" in en

    def test_a_catalog_without_the_discovery_commands_is_refused(self):
        """The text sends the agent to three tools; a catalog without one is an
        error."""
        for missing in ("commands list", "commands schema", "commands guide"):
            commands = tuple(c for c in COMMANDS if c.name != missing)

            with pytest.raises(NotFoundError) as caught:
                build_instructions(commands, lang="pl", allowed_dirs=())

            assert caught.value.details == {"command": missing}


# --- calls
# -----------------------------------------------------------------------------


class TestCalls:
    """``tools/call``: the envelope on success, the error document on failure."""

    @pytest.mark.parametrize("mode", MODES)
    def test_a_pure_tool_answers_with_the_envelope(self, mode):
        """The result is ``run_command(...).to_dict()`` as structured content and
        text."""
        result = call("commands_list", {"lang": "en"}, mode=mode)

        assert result.is_error is False
        assert (
            document_of(result)
            == run_command("commands list", {"lang": "en"}).to_dict()
        )
        assert result.content[0].text == compact(result.structured_content)

    @pytest.mark.parametrize(("command", "example"), catalog_examples(with_paths=False))
    def test_every_catalog_example_gives_the_same_result_as_the_python_api(
        self, command, example
    ):
        """Values over MCP equal what ``run_command`` returns for the same options."""
        result = call(command.operation_id, example)

        assert result.is_error is False, result.content[0].text
        expected = run_command(command, example).to_dict()
        assert document_of(result) == expected

    def test_a_real_command_gives_the_value_of_the_library(self):
        """``tc_kirpich`` over MCP is the Kirpich formula of ``ConcentrationTime``."""
        result = call("tc_kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})

        document = document_of(result)
        expected = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
        assert document["command"] == "tc kirpich"
        assert document["result"]["tc_min"] == pytest.approx(expected)
        assert document["notices"] == []

    def test_warnings_of_the_library_travel_as_notices(self):
        """A value outside the typical range of the formula is a notice, not an
        error."""
        result = call("tc_kirpich", {"length_km": 120, "slope_m_per_m": 0.02})

        document = document_of(result)
        assert result.is_error is False
        assert [notice["level"] for notice in document["notices"]] == ["warning"]
        assert "120" in document["notices"][0]["text"]

    def test_arguments_are_normalized_by_the_catalog(self, demo_catalog):
        """Defaults are applied and reported in ``inputs``; the result is the
        operation's."""
        document = document_of(call("demo_add", {"a_km": 2}))

        assert document["command"] == "demo add"
        assert document["status"] == "ok"
        assert document["inputs"] == {"a_km": 2.0, "b_km": 1.0}
        assert document["result"] == {"sum_km": 3.0}
        assert document["files"] == [] and document["notices"] == []

    def test_non_finite_numbers_become_null_in_strict_json(self, demo_catalog):
        """No ``NaN``/``Infinity`` token reaches the client, text or structured."""
        result = call("demo_nan", {"x_mm": 7})

        def refuse(token):
            raise AssertionError(f"non-standard JSON constant {token}")

        text = result.content[0].text
        assert json.loads(text, parse_constant=refuse) == result.structured_content
        assert result.structured_content["result"] == {
            "value": None,
            "limit": None,
            "pair": [1, 7],
        }

    def test_language_option_takes_the_server_language(self):
        """A call without ``lang`` gets the language the server was created with."""
        english = document_of(call("commands_list", {}, lang="en"))
        polish = document_of(call("commands_list", {}, lang="pl"))

        assert english["inputs"] == {"lang": "en"}
        assert english["result"][0]["summary"] == COMMANDS[0].summary_en
        assert polish["inputs"] == {"lang": "pl"}
        assert polish["result"][0]["summary"] == COMMANDS[0].summary

    def test_an_explicit_language_wins_over_the_server_language(self):
        document = document_of(call("commands_list", {"lang": "pl"}, lang="en"))

        assert document["inputs"] == {"lang": "pl"}
        assert document["result"][0]["summary"] == COMMANDS[0].summary

    def test_a_null_language_counts_as_not_given(self):
        document = document_of(call("commands_list", {"lang": None}, lang="en"))

        assert document["inputs"] == {"lang": "en"}

    def test_calls_run_in_worker_threads_side_by_side(self, demo_catalog):
        """Two calls are inside their operations at the same time (a barrier of two)."""

        async def scenario():
            answers = {}

            async with connected() as client:

                async def one(label):
                    answers[label] = await client.call_tool(
                        "demo_meet", {"label": label}
                    )

                async with anyio.create_task_group() as group:
                    group.start_soon(one, "a")
                    group.start_soon(one, "b")
            return answers

        answers = anyio.run(scenario)

        assert sorted(answers) == ["a", "b"]
        for label, result in answers.items():
            assert result.is_error is False, result.content[0].text
            assert document_of(result)["result"] == {"label": label}


# --- errors
# ----------------------------------------------------------------------------


class TestErrors:
    """Failures are ``isError`` results with a ``hydrolog-error/1`` document."""

    def test_invalid_arguments_are_a_validation_error(self):
        """The catalog validator answers; the document names the option and reason."""
        document = error_of(call("commands_list", {"bogus": 1}))

        assert document["code"] == "validation_error"
        assert document["exit_code"] == 2
        assert document["command"] == "commands list"
        assert document["title"] == ERROR_CODES["validation_error"].title
        assert document["details"] == {
            "option": "bogus",
            "reason": "unknown_option",
            "allowed": ["lang"],
        }
        assert document["hint"]

    def test_the_error_title_follows_the_server_language(self):
        document = error_of(call("commands_list", {"bogus": 1}, lang="en"))

        assert document["title"] == ERROR_CODES["validation_error"].title_en

    def test_a_value_out_of_range_is_a_validation_error(self, demo_catalog):
        document = error_of(call("demo_add", {"a_km": -1}))

        assert document["code"] == "validation_error"
        assert document["details"]["option"] == "a_km"
        assert document["details"]["reason"] == "exclusive_minimum"

    @pytest.mark.parametrize(
        ("arguments", "option", "reason"),
        [
            (
                {"length_km": -1, "slope_m_per_m": 0.02},
                "length_km",
                "exclusive_minimum",
            ),
            ({"length_km": "8.2", "slope_m_per_m": 0.02}, "length_km", "type"),
            ({"length_km": 8.2}, "slope_m_per_m", "required"),
            ({"length_km": 8.2, "slope_m_per_m": 0.02, "x": 1}, "x", "unknown_option"),
        ],
    )
    def test_a_real_command_rejects_bad_arguments_with_option_and_reason(
        self, arguments, option, reason
    ):
        """``tc_kirpich``: the validation error names the option and the reason."""
        document = error_of(call("tc_kirpich", arguments))

        assert document["code"] == "validation_error"
        assert document["command"] == "tc kirpich"
        assert (document["details"]["option"], document["details"]["reason"]) == (
            option,
            reason,
        )

    def test_a_missing_required_option_is_a_validation_error(self, demo_catalog):
        document = error_of(call("demo_add", {}))

        assert document["details"] == {"option": "a_km", "reason": "required"}

    def test_the_option_groups_are_enforced_although_the_schema_lacks_them(
        self, demo_catalog
    ):
        """``one_of`` is validated server-side: none given, or two groups at once."""
        none_given = error_of(call("demo_series", {}))
        both = error_of(
            call(
                "demo_series",
                {
                    "values": [1],
                    "dates": ["2020-01-01"],
                    "input_file": "a.csv",
                    "value_column": "q",
                },
                allowed_dirs=[Path.cwd()],
            )
        )

        assert none_given["code"] == both["code"] == "validation_error"
        assert none_given["details"]["reason"] == both["details"]["reason"] == "one_of"
        assert none_given["details"]["groups"] == [
            ["values", "dates"],
            ["input_file", "value_column"],
        ]

    def test_an_error_of_the_operation_keeps_its_code(self):
        """A ``HydrologError`` raised by an operation is reported as it is."""
        document = error_of(call("commands_schema", {"command": "zzz"}))

        assert document["code"] == "not_found"
        assert document["exit_code"] == 3
        assert document["command"] == "commands schema"
        assert document["details"]["command"] == "zzz"

    def test_a_bug_is_an_internal_error_without_a_traceback_for_the_client(
        self, demo_catalog, caplog
    ):
        """The client gets the class and message; the traceback goes to the log."""
        with caplog.at_level(logging.ERROR):
            document = error_of(call("demo_boom", {}))

        assert document["code"] == "internal_error"
        assert document["exit_code"] == 1
        assert document["message"] == "RuntimeError: boom"
        assert document["details"] == {"exception": "RuntimeError"}
        assert "Traceback" not in json.dumps(document)
        logged = [
            r for r in caplog.records if r.exc_info and r.exc_info[0] is RuntimeError
        ]
        assert [r.levelno for r in logged] == [logging.ERROR]
        assert "demo_boom" in logged[0].getMessage()

    def test_a_file_system_error_is_an_io_error(self, demo_catalog, caplog):
        with caplog.at_level(logging.ERROR):
            document = error_of(call("demo_disk", {}))

        assert document["code"] == "io_error"
        assert document["exit_code"] == 9
        assert document["details"] == {"errno": "EACCES", "path": "/data/x"}
        assert not caplog.records  # not a bug: nothing to log

    def test_an_unknown_tool_is_a_protocol_error_with_suggestions(self):
        """The MCP error for a tool the server does not have; it suggests a close
        name."""
        error = protocol_error("commands_lst")

        assert error.code == types.INVALID_PARAMS
        assert "Unknown tool 'commands_lst'" in error.message
        assert "Did you mean: commands_list" in error.message

    def test_a_command_name_with_a_space_is_not_a_tool_name(self):
        """Only ``operation_id`` names tools; ``commands list`` is not one."""
        assert protocol_error("commands list").code == types.INVALID_PARAMS


# --- paths
# -----------------------------------------------------------------------------


class TestPathPolicy:
    """Path options work only inside the directories the server allows."""

    def test_without_directories_a_path_option_is_forbidden(
        self, demo_catalog, tmp_path
    ):
        """No allowed directory: refused, and the operation never runs."""
        source = tmp_path / "in.txt"
        source.write_text("abc", encoding="utf-8")
        target = tmp_path / "out.txt"

        document = error_of(
            call("demo_copy", {"input_file": str(source), "output_file": str(target)})
        )

        assert document["code"] == "forbidden"
        assert document["exit_code"] == 8
        assert document["details"]["option"] == "input_file"
        assert document["details"]["allowed_dirs"] == []
        assert "--allow-dir" in document["hint"]
        assert not target.exists()

    def test_inside_an_allowed_directory_the_command_runs_and_reports_its_file(
        self, demo_catalog, tmp_path
    ):
        """Read and write inside; the envelope lists the written file with its
        SHA-256."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        (allowed / "in.txt").write_text("abc", encoding="utf-8")
        target = allowed / "out.txt"

        result = call(
            "demo_copy",
            {"input_file": str(allowed / "in.txt"), "output_file": str(target)},
            allowed_dirs=[allowed],
        )

        document = document_of(result)
        assert result.is_error is False
        assert document["result"] == {"chars": 3}
        assert target.read_text(encoding="utf-8") == "ABC"
        assert document["files"] == [
            {
                "role": "output",
                "path": str(target.resolve()),
                "sha256": hashlib.sha256(b"ABC").hexdigest(),
            }
        ]
        assert document["inputs"]["input_file"] == str((allowed / "in.txt").resolve())

    def test_a_path_outside_is_forbidden_and_names_the_allowed_directories(
        self, demo_catalog, tmp_path
    ):
        allowed = tmp_path / "data"
        allowed.mkdir()
        outside = tmp_path / "secret.txt"
        outside.write_text("x", encoding="utf-8")

        document = error_of(
            call(
                "demo_copy",
                {"input_file": str(outside), "output_file": str(allowed / "o.txt")},
                allowed_dirs=[allowed],
            )
        )

        assert document["code"] == "forbidden"
        assert document["details"] == {
            "option": "input_file",
            "path": str(outside.resolve()),
            "allowed_dirs": [str(allowed.resolve())],
        }
        assert not (allowed / "o.txt").exists()

    def test_the_output_path_is_checked_too(self, demo_catalog, tmp_path):
        """Reading inside is not enough: the file to write must be inside as well."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        (allowed / "in.txt").write_text("abc", encoding="utf-8")
        target = tmp_path / "out.txt"

        document = error_of(
            call(
                "demo_copy",
                {"input_file": str(allowed / "in.txt"), "output_file": str(target)},
                allowed_dirs=[allowed],
            )
        )

        assert document["code"] == "forbidden"
        assert document["details"]["option"] == "output_file"
        assert not target.exists()

    def test_dot_dot_and_symlinks_cannot_leave_the_directory(
        self, demo_catalog, tmp_path
    ):
        """The policy judges where a path points, not how it is written."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("x", encoding="utf-8")
        (allowed / "link").symlink_to(outside, target_is_directory=True)
        attempts = [
            str(allowed / ".." / "outside" / "secret.txt"),
            str(allowed / "link" / "secret.txt"),
        ]

        for attempt in attempts:
            document = error_of(
                call(
                    "demo_copy",
                    {"input_file": attempt, "output_file": str(allowed / "o.txt")},
                    allowed_dirs=[allowed],
                )
            )
            assert document["code"] == "forbidden", attempt

    def test_relative_paths_are_taken_against_the_working_directory(
        self, demo_catalog, tmp_path, monkeypatch
    ):
        allowed = tmp_path / "data"
        allowed.mkdir()
        (allowed / "in.txt").write_text("abc", encoding="utf-8")
        monkeypatch.chdir(allowed)

        result = call(
            "demo_copy",
            {"input_file": "in.txt", "output_file": "out.txt"},
            allowed_dirs=[allowed],
        )

        assert result.is_error is False, result.content[0].text
        assert (allowed / "out.txt").read_text(encoding="utf-8") == "ABC"

    def test_a_pure_tool_works_without_directories(self, demo_catalog):
        """Commands without path options are not affected by the missing directories."""
        document = document_of(call("demo_add", {"a_km": 1}))

        assert document["result"] == {"sum_km": 2.0}

    @pytest.mark.parametrize(("command", "example"), catalog_examples(with_paths=True))
    def test_every_catalog_command_with_files_is_refused_without_directories(
        self, command, example
    ):
        """The real catalog: a path option never works on a server without
        directories."""
        document = error_of(call(command.operation_id, example))

        assert document["code"] == "forbidden", document
        assert document["details"]["allowed_dirs"] == []

    @pytest.mark.parametrize(("command", "example"), catalog_examples(with_paths=True))
    def test_every_catalog_example_with_files_runs_inside_an_allowed_directory(
        self, command, example, tmp_path, monkeypatch
    ):
        """Inputs are read and outputs written inside the allowed directory, and the
        envelope equals the one of the Python API (the fixtures are copied there so
        that the relative paths of the examples point inside)."""
        if command.group == "soil":
            pytest.importorskip("rasterio")
        shutil.copytree(ROOT / "tests" / "fixtures", tmp_path / "tests" / "fixtures")
        monkeypatch.chdir(tmp_path)

        result = call(command.operation_id, example, allowed_dirs=[tmp_path])

        assert result.is_error is False, result.content[0].text
        expected = run_command(command, example, allowed_dirs=[tmp_path]).to_dict()
        assert document_of(result) == expected
        for record in expected["files"]:
            assert Path(record["path"]).is_relative_to(tmp_path.resolve())

    def test_directories_are_resolved_when_the_server_is_created(
        self, tmp_path, monkeypatch
    ):
        """``~``, relative entries and a single path instead of a list."""
        home = tmp_path / "home"
        home.mkdir()
        work = tmp_path / "work"
        (work / "sub").mkdir(parents=True)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.chdir(work)

        _, instructions = listing(allowed_dirs=["~/data", "sub", str(work / "sub")])
        _, single = listing(allowed_dirs=work)

        assert str(home.resolve() / "data") in instructions
        assert instructions.count(str((work / "sub").resolve())) == 1  # deduplicated
        assert str(work.resolve()) in single

    @pytest.mark.parametrize("empty", ["", "   "])
    def test_an_empty_directory_is_refused(self, empty):
        """An empty text would silently mean the working directory."""
        with pytest.raises(InvalidParameterError) as caught:
            create_server(allowed_dirs=[empty])

        assert caught.value.code == "validation_error"
        assert caught.value.details == {"option": "allowed_dirs", "reason": "empty"}


# --- creating the server
# ---------------------------------------------------------------


class TestCreateServer:
    """``create_server`` / ``run_stdio``: arguments and the optional dependency."""

    @pytest.mark.parametrize("function", [create_server, run_stdio])
    def test_an_unknown_language_is_a_validation_error(self, function):
        with pytest.raises(InvalidParameterError) as caught:
            function(lang="de")

        assert caught.value.code == "validation_error"
        assert caught.value.details == {
            "option": "lang",
            "reason": "choice",
            "allowed": ["pl", "en"],
            "value": "de",
        }

    @pytest.mark.parametrize("function", [create_server, run_stdio])
    @pytest.mark.parametrize("missing", ["mcp_types", "mcp.server", "anyio"])
    def test_a_missing_sdk_is_a_missing_dependency_error(
        self, function, missing, monkeypatch
    ):
        """No (usable) SDK: the install command is in the hint, nothing is served."""
        monkeypatch.setitem(sys.modules, missing, None)

        with pytest.raises(MissingDependencyError) as caught:
            function()

        assert caught.value.code == "missing_dependency"
        assert caught.value.exit_code == 6
        assert caught.value.hint == "pip install hydrolog[mcp]"
        assert caught.value.details["requirement"] == "mcp>=2.3,<3"
        assert caught.value.details["module"] == missing

    def test_the_package_imports_without_the_sdk(self):
        """``import hydrolog.mcp`` is safe without the extra; only calls need it."""
        script = (
            "import sys\n"
            "for name in ('mcp', 'mcp_types', 'anyio'):\n"
            "    sys.modules[name] = None\n"
            "from hydrolog.mcp import create_server, run_stdio\n"
            "from hydrolog.exceptions import MissingDependencyError\n"
            "try:\n"
            "    create_server()\n"
            "except MissingDependencyError as exc:\n"
            "    print(exc.code)\n"
        )

        finished = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            cwd=ROOT,
            timeout=120,
            check=False,
        )

        assert finished.returncode == 0, finished.stderr.decode()
        assert finished.stdout.decode().split() == ["missing_dependency"]

    def test_the_server_identifies_itself(self):
        """Name, title and version of the package."""
        import hydrolog

        async def scenario():
            async with connected() as client:
                return client.server_info

        info = anyio.run(scenario)

        assert info.name == "hydrolog"
        assert info.title == "Hydrolog"
        assert info.version == hydrolog.__version__


# --- a real process on stdio
# -----------------------------------------------------------


LAUNCHERS = ["python", "cli"]


def server_arguments(launcher, directory):
    """Arguments of ``sys.executable`` that start an English server on stdio whose
    only allowed directory is ``directory``: through the Python API or ``hydrolog
    mcp``."""
    if launcher == "python":
        code = (
            "from hydrolog.mcp import run_stdio; "
            f"run_stdio(allowed_dirs=[{str(directory)!r}], lang='en')"
        )
        return ["-c", code]
    return [
        "-m",
        "hydrolog.cli",
        "mcp",
        "--allow-dir",
        str(directory),
        "--lang",
        "en",
    ]


# A server whose catalog has one more command: its operation prints to stdout.
NOISY_SERVER = """\
import hydrolog.mcp.server as server
from hydrolog.catalog import Command, data_commands


def noisy():
    print("stray text of an operation")
    return {"ok": True}


demo = Command(
    name="demo noisy",
    operation_id="demo_noisy",
    summary="Prints to stdout.",
    summary_en="Prints to stdout.",
    description="Prints to stdout.",
    description_en="Prints to stdout.",
    function="__main__:noisy",
    options=(),
    examples=({},),
)
catalog = (*data_commands(), demo)
server.data_commands = lambda: catalog
server.run_stdio()
"""


class TestStdio:
    """The server as a separate process, spoken to over stdin and stdout."""

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_the_process_serves_the_same_tools_as_the_in_memory_server(
        self, launcher, tmp_path
    ):
        """List tools, read the instructions and call a tool over a real pipe."""
        server = StdioServerParameters(
            command=sys.executable,
            args=server_arguments(launcher, tmp_path),
            env=dict(os.environ),
            cwd=ROOT,
        )

        async def scenario(log):
            async with Client(stdio_client(server, errlog=log)) as client:
                tools = (await client.list_tools()).tools
                answer = await client.call_tool("commands_list", {})
                refused = await client.call_tool("commands_list", {"bogus": 1})
                return tools, client.instructions, answer, refused

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            tools, instructions, answer, refused = anyio.run(scenario, log)

        expected_tools, expected_instructions = listing(
            lang="en", allowed_dirs=[tmp_path]
        )
        assert [t.model_dump() for t in tools] == [
            t.model_dump() for t in expected_tools
        ]
        assert instructions == expected_instructions
        assert str(tmp_path.resolve()) in instructions
        assert answer.is_error is False
        assert (
            document_of(answer)
            == run_command("commands list", {"lang": "en"}).to_dict()
        )
        assert error_of(refused)["details"]["reason"] == "unknown_option"

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_a_pure_tool_runs_and_a_file_tool_obeys_the_directories_of_the_process(
        self, launcher, tmp_path
    ):
        """Over a real pipe: ``tc_kirpich`` computes; a file outside the allowed
        directory is refused with the allowed directory in the error."""
        outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
        outside.write_text("{}", encoding="utf-8")
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        server = StdioServerParameters(
            command=sys.executable,
            args=server_arguments(launcher, allowed),
            env=dict(os.environ),
            cwd=ROOT,
        )
        kirpich = {"length_km": 8.2, "slope_m_per_m": 0.023}

        async def scenario(log):
            async with Client(stdio_client(server, errlog=log)) as client:
                computed = await client.call_tool("tc_kirpich", kirpich)
                refused = await client.call_tool(
                    "tc_watershed", {"watershed_file": str(outside)}
                )
                return computed, refused

        with (tmp_path / "stderr.log").open("w+", encoding="utf-8") as log:
            computed, refused = anyio.run(scenario, log)

        assert computed.is_error is False
        assert document_of(computed) == run_command("tc kirpich", kirpich).to_dict()
        error = error_of(refused)
        assert error["code"] == "forbidden"
        assert error["details"]["allowed_dirs"] == [str(allowed.resolve())]
        assert error["details"]["path"] == str(outside.resolve())

    @pytest.mark.parametrize("launcher", LAUNCHERS)
    def test_the_process_ends_cleanly_without_a_byte_on_stdout_when_stdin_closes(
        self, launcher, tmp_path
    ):
        """End of input is the shutdown signal; stdout carries nothing but protocol."""
        finished = subprocess.run(
            [sys.executable, *server_arguments(launcher, tmp_path)],
            input=b"",
            capture_output=True,
            cwd=ROOT,
            timeout=120,
            check=False,
        )

        assert (finished.returncode, finished.stdout) == (0, b""), finished.stderr

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
                    "params": {"name": "demo_noisy", "arguments": {}},
                }
            )
            answer = json.loads(process.stdout.readline())
            rest, errors = process.communicate(timeout=120)  # closes stdin: shutdown
        finally:
            watchdog.cancel()
            process.kill()

        assert answer["id"] == 2
        assert answer["result"]["isError"] is False
        assert answer["result"]["structuredContent"]["result"] == {"ok": True}
        assert rest == ""
        assert "stray text of an operation" in errors
        assert process.returncode == 0
