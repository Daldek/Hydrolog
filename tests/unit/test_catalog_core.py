"""Tests for the catalog core: declarations, registry, schema, validation, run."""

import hashlib
import importlib
import inspect
import json
import math
import os
import threading
import time
import types
import warnings
from pathlib import Path
from typing import Any

import pytest

from hydrolog.catalog import (
    Command,
    CommandResult,
    Document,
    Notice,
    OperationOutput,
    Option,
    capture_warnings,
    command_schema,
    data_commands,
    get_command,
    input_schema,
    list_commands,
    run_command,
    validate_command,
)
from hydrolog.catalog.envelope import FileRecord, sha256_file
from hydrolog.catalog.groups import GROUP_MODULES, collect_commands
from hydrolog.catalog.spec import SUMMARY_MAX_CHARS
from hydrolog.exceptions import (
    CalculationError,
    ForbiddenPathError,
    HydrologError,
    InvalidParameterError,
    NotFoundError,
    OutputError,
)

CALLS: list[dict] = []


# --- operations used by the test-only commands ----------------------------------------


def echo_operation(**kwargs):
    """Return its keyword arguments; record the call."""
    CALLS.append(kwargs)
    return dict(kwargs)


def noisy_operation(*, length_km: float):
    """Return an OperationOutput with a notice."""
    return OperationOutput(
        result={"tc_min": length_km * 10.0},
        notices=(Notice("warning", "outside_typical_range", "length is large"),),
    )


def writing_operation(*, out: str, text: str = "hello"):
    """Write a file and report it through the OperationOutput wrapper."""
    Path(out).write_text(text, encoding="utf-8")
    return OperationOutput(result={"chars": len(text)}, files=(out,))


class FileResult:
    """Result that reports its file through the ``output_files()`` protocol."""

    def __init__(self, path: str) -> None:
        self.path = path

    def output_files(self):
        return [self.path, self.path]

    def to_dict(self):
        return {"path": self.path}


def protocol_operation(*, out: str):
    """Write a file and return a result exposing ``output_files()``."""
    Path(out).write_bytes(b"\x00\x01binary")
    return FileResult(out)


def ghost_file_operation(*, out: str):
    """Report an output file that was never written."""
    return OperationOutput(result={}, files=(out,))


def warning_operation(*, length_km: float):
    """Warn twice about the same thing and report it as a notice."""
    with capture_warnings() as notices:
        warnings.warn(
            f"length_km={length_km} is outside the typical range",
            UserWarning,
            stacklevel=2,
        )
        warnings.warn(
            f"length_km={length_km} is outside the typical range",
            UserWarning,
            stacklevel=2,
        )
    return OperationOutput(result={"ok": True}, notices=notices)


def failing_operation(*, length_km: float):
    """Fail like a computation that cannot be done."""
    raise CalculationError("no convergence", details={"iterations": 50})


def nan_operation(*, length_km: float):
    """Return a result with NaN and a tuple."""
    return {"value": float("nan"), "pair": (1, 2), "path": Path("/x/y")}


def _command(operation: str = "echo_operation", **overrides) -> Command:
    fields: dict[str, Any] = {
        "name": "demo run",
        "operation_id": "hydrolog_demo_run",
        "summary": "Demo.",
        "summary_pl": "Demo PL.",
        "description": "Demo description.",
        "description_pl": "Opis demonstracyjny.",
        "function": f"{__name__}.{operation}",
        "options": (),
        "result_schema": "hydrolog-demo-run/1",
        "examples": ({},),
    }
    fields.update(overrides)
    fields.setdefault("example_results", tuple({} for _ in fields["examples"]))
    return Command(**fields)


def _opt(name: str, type_: Any, **kwargs: Any) -> Option:
    if type_ == "choice" and "meanings" not in kwargs:
        kwargs["meanings"] = {c: f"Meaning {c}" for c in kwargs.get("choices", ())}
        kwargs["meanings_pl"] = {c: f"Znaczenie {c}" for c in kwargs["meanings"]}
    if type_ == "path" and "path_role" not in kwargs:
        kwargs["path_role"] = "input"
    return Option(name, type_, f"Description {name}", f"Opis {name}", **kwargs)


RICH = _command(
    options=(
        _opt("length_km", "number", required=True, exclusive_minimum=0, unit="km"),
        _opt("cn", "integer", minimum=0, maximum=100),
        _opt("method", "choice", choices=("kirpich", "nrcs"), default="kirpich"),
        _opt("verbose", "boolean"),
        _opt("label", "string"),
        _opt("values", "number_list", minimum=0),
        _opt("dates", "string_list"),
        _opt("stations", "object_list"),
        _opt("watershed", "object"),
        _opt("input_file", "path"),
        _opt("out", "path", path_role="output"),
        _opt("ratio", "number", default=0.5, minimum=0, maximum=1, unit="m/m"),
    ),
)

SERIES = _command(
    options=(
        _opt("values", "number_list"),
        _opt("dates", "string_list"),
        _opt("input_file", "path"),
        _opt("value_column", "string"),
    ),
    one_of=(("values", "dates"), ("input_file", "value_column")),
)


def _invalid(command, options) -> InvalidParameterError:
    with pytest.raises(InvalidParameterError) as caught:
        validate_command(command, options)
    return caught.value


# --- declarations ---------------------------------------------------------------------


class TestOptionDeclaration:
    """Declaration checks of ``Option``."""

    def test_flag_is_kebab_case_of_the_name(self):
        """The CLI flag derives from the snake_case name."""
        assert _opt("channel_length_km", "number").flag == "--channel-length-km"

    @pytest.mark.parametrize("name", ["Length", "1km", "length-km", "", "class", "a b"])
    def test_bad_names_are_rejected(self, name):
        """Names are snake_case identifiers that are not Python keywords."""
        with pytest.raises(ValueError, match="snake_case"):
            _opt(name, "number")

    def test_unknown_type_is_rejected(self):
        """Only the declared option types exist."""
        with pytest.raises(ValueError, match="unknown type 'float'"):
            _opt("x", "float")

    def test_choices_belong_to_choice_options_only(self):
        """A choice needs choices; other types must not have them."""
        with pytest.raises(ValueError, match="needs a non-empty tuple"):
            _opt("m", "choice")
        with pytest.raises(ValueError, match="only for type 'choice'"):
            _opt("m", "string", choices=("a",))
        with pytest.raises(ValueError, match="unique"):
            _opt("m", "choice", choices=("a", "a"))

    def test_bounds_belong_to_numeric_options_only(self):
        """Bounds on a string option are a declaration error."""
        with pytest.raises(ValueError, match="numeric"):
            _opt("s", "string", minimum=1)
        with pytest.raises(ValueError, match="mutually exclusive"):
            _opt("n", "number", minimum=0, exclusive_minimum=0)
        with pytest.raises(ValueError, match="exceeds maximum"):
            _opt("n", "number", minimum=5, maximum=1)

    def test_path_role_is_required_for_paths_and_forbidden_elsewhere(self):
        """A path is an input or an output; no other type has a role."""
        with pytest.raises(ValueError, match="path_role 'input' or 'output'"):
            Option("p", "path", "Path", "Ścieżka")
        with pytest.raises(ValueError, match="path_role 'input' or 'output'"):
            _opt("p", "path", path_role="both")
        with pytest.raises(ValueError, match="only for type 'path'"):
            _opt("n", "number", path_role="output")

    def test_only_output_paths_write(self):
        """``writes`` follows ``path_role``."""
        assert _opt("o", "path", path_role="output").writes is True
        assert _opt("i", "path", path_role="input").writes is False

    def test_every_choice_needs_a_meaning_in_both_languages(self):
        """Meanings cover exactly the choices (they feed the catalog document)."""
        with pytest.raises(ValueError, match="meanings must give a meaning"):
            Option("m", "choice", "D", "O", choices=("a", "b"), meanings={"a": "x"})
        with pytest.raises(ValueError, match="meanings_pl must give a meaning"):
            Option(
                "m",
                "choice",
                "D",
                "O",
                choices=("a",),
                meanings={"a": "x"},
                meanings_pl={"a": "x", "b": "y"},
            )
        with pytest.raises(ValueError, match="only for type 'choice'"):
            _opt("n", "number", meanings={"a": "x"})

    def test_required_option_cannot_have_default(self):
        """A required option with a default is contradictory."""
        with pytest.raises(ValueError, match="required option cannot have a default"):
            _opt("n", "number", required=True, default=1)

    def test_invalid_default_is_rejected_at_declaration(self):
        """A default that violates the option's own rules fails at import time."""
        with pytest.raises(ValueError, match="invalid default"):
            _opt("m", "choice", choices=("a", "b"), default="c")
        with pytest.raises(ValueError, match="invalid default"):
            _opt("n", "number", minimum=0, default=-1)

    def test_empty_descriptions_are_rejected(self):
        """Both languages need a description."""
        with pytest.raises(ValueError, match="description_pl"):
            Option("x", "number", "Description", " ")
        with pytest.raises(ValueError, match="description"):
            Option("x", "number", "", "Opis")

    def test_choices_must_be_non_empty_strings(self):
        """Empty or non-string choices are rejected."""
        with pytest.raises(ValueError, match="non-empty strings"):
            _opt("m", "choice", choices=("a", ""))

    def test_bounds_must_be_finite_numbers(self):
        """NaN, infinity and booleans are not bounds."""
        for bound in (math.nan, math.inf, True):
            with pytest.raises(ValueError, match="finite number"):
                _opt("n", "number", minimum=bound)

    def test_unit_must_not_be_empty(self):
        """A unit is a non-empty string when given."""
        with pytest.raises(ValueError, match="unit"):
            _opt("n", "number", unit="")


class TestCommandDeclaration:
    """Declaration checks of ``Command``."""

    def test_group_and_subcommand(self):
        """The name splits into group and subcommand."""
        command = _command(
            name="stats flood-frequency", operation_id="hydrolog_stats_flood_frequency"
        )
        assert (command.group, command.subcommand) == ("stats", "flood-frequency")
        assert command.families == ("stats",)

    @pytest.mark.parametrize(
        "name",
        ["kirpich", "tc  kirpich", "TC kirpich", "tc kirpich extra", "tc ki_rpich"],
    )
    def test_bad_names_are_rejected(self, name):
        """A name is ``<group> <command>`` in lowercase."""
        with pytest.raises(ValueError, match="name must be"):
            _command(name=name, operation_id="hydrolog_x")

    def test_operation_id_must_be_snake_case_of_name(self):
        """``operation_id`` is ``hydrolog_`` and the name with ``_`` for ``-``."""
        with pytest.raises(
            ValueError, match="operation_id must be 'hydrolog_demo_run_it'"
        ):
            _command(name="demo run-it", operation_id="demo_run_it")
        with pytest.raises(ValueError, match="operation_id must be"):
            _command(operation_id="hydrolog_demo_run-")

    def test_operation_id_length_limit(self):
        """MCP tool names have at most 48 characters."""
        long = "x" * 40
        with pytest.raises(ValueError, match="longer than 48"):
            _command(name=f"demo {long}", operation_id=f"hydrolog_demo_{long}")

    def test_summary_length_limit(self):
        """Summaries are one line of at most ``SUMMARY_MAX_CHARS`` characters."""
        _command(summary="x" * SUMMARY_MAX_CHARS)
        with pytest.raises(ValueError, match="longer than"):
            _command(summary="x" * (SUMMARY_MAX_CHARS + 1))
        with pytest.raises(ValueError, match="single line"):
            _command(summary_pl="a\nb")

    @pytest.mark.parametrize(
        "function",
        ["tc_kirpich", "hydrolog.operations:tc_kirpich", "a b.c", ".x", "x."],
    )
    def test_function_path_format(self, function):
        """The function is a dotted path ``package.module.function``."""
        with pytest.raises(ValueError, match="function must be a dotted path"):
            _command(function=function)

    @pytest.mark.parametrize(
        "schema", ["", "tc-kirpich/1", "hydrolog-tc/0", "hydrolog-x"]
    )
    def test_result_schema_format(self, schema):
        """The domain schema id is ``hydrolog-<kind>/<n>``."""
        with pytest.raises(ValueError, match="result_schema"):
            _command(result_schema=schema)

    def test_an_example_is_required_with_one_result_excerpt_each(self):
        """Examples and their result excerpts pair up one to one."""
        with pytest.raises(ValueError, match="at least one example"):
            _command(examples=(), example_results=())
        with pytest.raises(ValueError, match="one excerpt per example"):
            _command(examples=({}, {}), example_results=({},))
        with pytest.raises(ValueError, match="must be a mapping"):
            _command(example_results=([1],))

    def test_rules_exist_in_both_languages(self):
        """A rule without its translation is a declaration error."""
        _command(rules=("Do it.",), rules_pl=("Zrób to.",))
        with pytest.raises(ValueError, match="same number of entries"):
            _command(rules=("Do it.",), rules_pl=())

    def test_errors_are_unique_registry_codes(self):
        """``errors`` names codes of the error registry, each once."""
        assert _command(errors=("not_found", "conflict")).errors == (
            "not_found",
            "conflict",
        )
        with pytest.raises(ValueError, match="registry codes"):
            _command(errors=("nonsense",))
        with pytest.raises(ValueError, match="registry codes"):
            _command(errors=("conflict", "conflict"))

    def test_the_mcp_description_has_a_size_budget(self):
        """Summary, description and rules must fit a tool description."""
        with pytest.raises(ValueError, match="MCP description allows"):
            _command(description="x" * 600)

    def test_core_family(self):
        """A core command belongs to its group and to ``core``."""
        assert _command(core=True).families == ("demo", "core")

    def test_effects_derive_from_the_path_roles(self):
        """A command that writes a file is a destructive replace; others are pure."""
        pure = _command(options=(_opt("i", "path"),))
        assert pure.writes is False
        assert pure.effects.read_only is True
        assert pure.effects.writes == "none"
        assert pure.effects.destructive is False
        assert pure.check is None
        writing = _command(options=(_opt("o", "path", path_role="output"),))
        assert writing.writes is True
        assert writing.effects.read_only is False
        assert writing.effects.writes == "replace"
        assert writing.effects.destructive is True
        assert writing.check == "demo run"

    def test_option_names_must_be_unique(self):
        """Two options with one name are rejected."""
        with pytest.raises(ValueError, match="unique"):
            _command(options=(_opt("a", "number"), _opt("a", "string")))

    def test_options_must_be_a_tuple_of_options(self):
        """Lists would be mutable inside a frozen declaration."""
        with pytest.raises(ValueError, match="options must be a tuple"):
            _command(options=[_opt("a", "number")])

    def test_one_of_needs_two_groups_of_declared_options(self):
        """Alternatives refer to declared options and need at least two groups."""
        options = (_opt("a", "number"), _opt("b", "number"), _opt("c", "number"))
        with pytest.raises(ValueError, match="at least two"):
            _command(options=options, one_of=(("a",),))
        with pytest.raises(ValueError, match="unknown options"):
            _command(options=options, one_of=(("a",), ("zzz",)))
        with pytest.raises(ValueError, match="non-empty tuple"):
            _command(options=options, one_of=(("a",), ()))

    def test_required_option_cannot_be_in_one_of(self):
        """A required option is always present, so it cannot select an alternative."""
        options = (_opt("a", "number", required=True), _opt("b", "number"))
        with pytest.raises(
            ValueError, match="required options cannot be part of one_of"
        ):
            _command(options=options, one_of=(("a",), ("b",)))

    def test_examples_use_declared_options(self):
        """An example naming an undeclared option is a declaration error."""
        with pytest.raises(ValueError, match="unknown options"):
            _command(options=(_opt("a", "number"),), examples=({"b": 1},))
        with pytest.raises(ValueError, match="unknown options"):
            _command(options=(_opt("a", "number"),), examples=({"b": 1},))

    def test_examples_must_be_mappings(self):
        """An example is an options mapping."""
        with pytest.raises(ValueError, match="example #0 must be a mapping"):
            _command(options=(_opt("a", "number"),), examples=([1],))

    def test_descriptions_must_not_be_empty(self):
        """Both long descriptions are required."""
        with pytest.raises(ValueError, match="description_pl"):
            _command(description_pl=" ")
        with pytest.raises(ValueError, match="description"):
            _command(description="")

    def test_options_must_be_option_instances(self):
        """Plain dicts are not options."""
        with pytest.raises(ValueError, match="Option instances"):
            _command(options=({"name": "a"},))

    def test_one_of_group_must_not_repeat_an_option(self):
        """A group lists each option once."""
        options = (_opt("a", "number"), _opt("b", "number"))
        with pytest.raises(ValueError, match="repeats an option"):
            _command(options=options, one_of=(("a", "a"), ("b",)))

    def test_option_lookup_by_name(self):
        """``Command.option`` returns the declaration or raises ``KeyError``."""
        command = _command(options=(_opt("a", "number"),))
        assert command.option("a").type == "number"
        with pytest.raises(KeyError):
            command.option("zzz")


# --- registry -------------------------------------------------------------------------


def _group_module(name: str, *commands: Command) -> types.ModuleType:
    module = types.ModuleType(name)
    module.COMMANDS = tuple(commands)  # type: ignore[attr-defined]
    return module


def _named(name: str) -> Command:
    return _command(
        name=name, operation_id="hydrolog_" + name.replace(" ", "_").replace("-", "_")
    )


class TestRegistry:
    """Collection of group modules."""

    def test_commands_follow_module_order_then_name(self):
        """Groups keep the registry order; commands inside are sorted by name."""
        zebra = _group_module("zebra", _named("zz b"), _named("zz a"))
        alpha = _group_module("alpha", _named("aa y"), _named("aa x-y"))
        names = [c.name for c in collect_commands([zebra, alpha])]
        assert names == ["zz a", "zz b", "aa x-y", "aa y"]

    def test_group_must_not_be_split_over_modules(self):
        """Two modules cannot both define the group ``demo``."""
        one = _group_module("one", _named("demo a"))
        two = _group_module("two", _named("demo b"))
        with pytest.raises(ValueError, match="group 'demo' is already defined by one"):
            collect_commands([one, two])

    def test_module_must_hold_one_group(self):
        """A module is one group."""
        mixed = _group_module("mixed", _named("aa x"), _named("bb x"))
        with pytest.raises(ValueError, match="several groups"):
            collect_commands([mixed])

    def test_duplicate_command_is_rejected(self):
        """Command names are unique across the catalog."""
        module = _group_module("dup", _named("demo a"), _named("demo a"))
        with pytest.raises(ValueError, match="duplicate command 'demo a'"):
            collect_commands([module])

    def test_module_without_commands_is_rejected(self):
        """A group module must export a non-empty ``COMMANDS`` tuple."""
        with pytest.raises(ValueError, match="COMMANDS must be a non-empty tuple"):
            collect_commands([types.ModuleType("empty")])
        with pytest.raises(ValueError, match="COMMANDS must be a non-empty tuple"):
            collect_commands([_group_module("empty")])

    def test_catalog_contains_the_meta_group(self):
        """The registry starts with the ``commands`` group."""
        names = [command.name for command in data_commands()]
        assert "commands list" in names
        assert "commands schema" in names
        assert GROUP_MODULES[-1] == "meta"

    def test_modules_are_given_by_name_or_as_objects(self):
        """``"meta"`` and the imported module give the same commands."""
        from hydrolog.catalog.groups import meta

        assert collect_commands(["meta"]) == collect_commands([meta])

    def test_unknown_module_name_is_an_import_error(self):
        """A name without a module fails loudly instead of being skipped."""
        with pytest.raises(ModuleNotFoundError):
            collect_commands(["no_such_group"])


class TestLookup:
    """``data_commands`` and ``get_command``."""

    def test_catalog_is_ordered_by_group_then_name(self):
        """Within one group commands are sorted by name."""
        commands = data_commands()
        for group in {c.group for c in commands}:
            names = [c.name for c in commands if c.group == group]
            assert names == sorted(names)

    def test_lookup_by_name_and_operation_id(self):
        """Both spellings find the same declaration."""
        assert get_command("commands list") is get_command("hydrolog_commands_list")

    def test_lookup_ignores_extra_whitespace(self):
        """Surrounding and repeated spaces do not matter."""
        assert get_command("  commands   schema ").name == "commands schema"

    def test_unknown_command_is_not_found_with_suggestions(self):
        """The error is ``not_found`` and offers close names."""
        with pytest.raises(NotFoundError) as caught:
            get_command("commands lst")
        error = caught.value
        assert error.code == "not_found"
        assert error.details["command"] == "commands lst"
        assert "commands list" in error.details["suggestions"]
        assert "commands list" in error.hint

    def test_unknown_command_without_similar_names(self):
        """No suggestions: the hint still points to ``commands list``."""
        with pytest.raises(NotFoundError) as caught:
            get_command("zzzzzz qqqqqq")
        assert caught.value.details["suggestions"] == []
        assert "commands list" in caught.value.hint

    def test_non_string_name_is_a_validation_error(self):
        """A number is not a command name."""
        with pytest.raises(InvalidParameterError) as caught:
            get_command(42)  # type: ignore[arg-type]
        assert caught.value.details["reason"] == "type"


# --- schema ---------------------------------------------------------------------------


class TestCommandSchema:
    """The ``hydrolog-commands/1`` document and the input schema."""

    def test_command_schema_describes_one_command(self):
        """``command_schema`` gives a document of exactly that command."""
        document = command_schema("tc kirpich")
        assert isinstance(document, Document)
        data = document.to_dict()
        assert data["schema"] == "hydrolog-commands/1"
        assert data["tool"] == "hydrolog"
        assert [c["name"] for c in data["commands"]] == ["tc kirpich"]

    def test_lookup_by_operation_id_and_instance(self):
        """The three ways to name a command give one document."""
        by_name = command_schema("tc kirpich").to_dict()
        assert command_schema("hydrolog_tc_kirpich").to_dict() == by_name
        assert command_schema(get_command("tc kirpich")).to_dict() == by_name

    def test_the_version_is_the_package_version(self):
        import hydrolog

        assert command_schema("tc kirpich").to_dict()["version"] == hydrolog.__version__

    def test_unknown_command_is_not_found(self):
        """Asking for a command that does not exist is ``not_found``."""
        with pytest.raises(NotFoundError):
            command_schema("no such")

    def test_the_old_language_parameter_is_gone(self):
        """Machine output is English only (AGI-9.2): no ``lang`` parameter."""
        with pytest.raises(TypeError):
            command_schema("tc kirpich", lang="pl")  # type: ignore[call-arg]

    def test_document_serializes_to_json_text_and_back(self):
        document = command_schema(RICH)
        assert json.loads(document.to_json()) == document.to_dict()
        assert "\n  " in document.to_json(indent=2)

    def test_to_dict_is_a_copy(self):
        """Changing the returned dictionary does not change the document."""
        document = command_schema(RICH)
        document.to_dict()["commands"].clear()
        assert len(document.to_dict()["commands"]) == 1

    def test_entry_describes_an_option_of_each_kind(self):
        entry = command_schema(RICH).to_dict()["commands"][0]
        assert entry["name"] == "demo run"
        assert entry["operation_id"] == "hydrolog_demo_run"
        assert entry["function"] == f"{__name__}.echo_operation"
        assert entry["summary"] == "Demo."
        assert entry["description"] == "Demo description."
        assert entry["result"] == {
            "schema": "hydrolog-demo-run/1",
            "cardinality": "single",
        }
        options = {item["name"]: item for item in entry["options"]}
        assert options["length_km"] == {
            "name": "length_km",
            "type": "number",
            "unit": "km",
            "required": True,
            "exclusive_minimum": 0,
            "description": "Description length_km",
            "i18n": {"pl": {"description": "Opis length_km"}},
        }
        assert options["cn"]["type"] == "integer"
        assert (options["cn"]["min"], options["cn"]["max"]) == (0, 100)
        assert options["method"]["default"] == "kirpich"
        assert options["method"]["enum"] == [
            {"value": "kirpich", "meaning": "Meaning kirpich"},
            {"value": "nrcs", "meaning": "Meaning nrcs"},
        ]
        assert options["method"]["i18n"]["pl"]["enum"] == {
            "kirpich": "Znaczenie kirpich",
            "nrcs": "Znaczenie nrcs",
        }
        assert options["values"]["type"] == "array"
        assert options["values"]["items"] == "number"
        assert options["input_file"]["path_role"] == "input"
        assert options["out"]["path_role"] == "output"

    def test_polish_texts_are_in_i18n_only(self):
        entry = command_schema(RICH).to_dict()["commands"][0]
        assert entry["i18n"]["pl"] == {
            "summary": "Demo PL.",
            "description": "Opis demonstracyjny.",
            "rules": [],
        }
        assert "Opis" not in json.dumps(
            {k: v for k, v in entry.items() if k != "i18n" and k != "options"}
        )

    def test_effects_check_and_families_derive_from_the_declaration(self):
        entry = command_schema(RICH).to_dict()["commands"][0]
        assert entry["effects"] == {
            "read_only": False,
            "writes": "replace",
            "idempotent": True,
            "network": False,
            "destructive": True,
        }
        assert entry["check"] == "demo run"
        assert entry["families"] == ["demo"]
        pure = command_schema(SERIES).to_dict()["commands"][0]
        assert pure["effects"]["read_only"] is True
        assert pure["effects"]["writes"] == "none"
        assert pure["check"] is None

    def test_alternative_options_are_marked_and_listed(self):
        entry = command_schema(SERIES).to_dict()["commands"][0]
        assert entry["one_of"] == [["values", "dates"], ["input_file", "value_column"]]
        marked = {o["name"] for o in entry["options"] if o.get("one_of")}
        assert marked == {"values", "dates", "input_file", "value_column"}

    def test_examples_carry_the_call_and_the_result_excerpt(self):
        command = _command(
            options=(_opt("values", "number_list"),),
            examples=({"values": (1, 2)},),
            example_results=({"n": 2},),
        )
        entry = command_schema(command).to_dict()["commands"][0]
        assert entry["examples"] == [
            {"call": "hydrolog demo run --values 1,2", "result": {"n": 2}}
        ]
        options = {item["name"]: item for item in entry["options"]}
        assert options["values"]["examples"] == [[1, 2]]

    def test_catalog_documents_are_strict_json(self):
        """The whole catalog serializes without NaN or odd types."""
        json.dumps(
            [command_schema(c).to_dict() for c in data_commands()], allow_nan=False
        )

    def test_input_schema_per_option_type(self):
        """Every option type maps to its JSON Schema form."""
        schema = input_schema(RICH)
        props = schema["properties"]
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["length_km"]
        assert "oneOf" not in schema
        assert props["length_km"] == {
            "type": "number",
            "exclusiveMinimum": 0,
            "description": "Description length_km [km]",
        }
        assert props["cn"]["type"] == "integer"
        assert (props["cn"]["minimum"], props["cn"]["maximum"]) == (0, 100)
        assert props["method"] == {
            "type": "string",
            "enum": ["kirpich", "nrcs"],
            "description": "Description method",
            "default": "kirpich",
        }
        assert props["verbose"]["type"] == "boolean"
        assert props["label"] == {
            "type": "string",
            "minLength": 1,
            "description": "Description label",
        }
        assert props["values"]["type"] == "array"
        assert props["values"]["items"] == {"type": "number", "minimum": 0}
        assert props["values"]["minItems"] == 1
        assert props["dates"]["items"] == {"type": "string", "minLength": 1}
        assert props["stations"]["items"] == {"type": "object"}
        assert props["watershed"]["type"] == "object"
        assert props["input_file"]["x-hydrolog-type"] == "path"
        assert "x-hydrolog-writes" not in props["input_file"]
        assert props["out"]["x-hydrolog-writes"] is True
        assert props["ratio"]["default"] == 0.5

    def test_input_schema_language_selects_descriptions_only(self):
        pl = input_schema(RICH, "pl")["properties"]
        en = input_schema(RICH, "en")["properties"]
        assert pl["cn"]["description"] == "Opis cn"
        assert en["cn"]["description"] == "Description cn"
        strip = lambda props: json.dumps(  # noqa: E731
            [{k: v for k, v in p.items() if k != "description"} for p in props.values()]
        )
        assert strip(pl) == strip(en)

    def test_unit_is_not_repeated_when_the_text_names_it(self):
        """The unit is appended in brackets only when the description lacks it."""
        option = Option("x", "number", "Length [km]", "Długość [km]", unit="km")
        assert option.json_schema("pl")["description"] == "Długość [km]"
        assert option.json_schema("en")["description"] == "Length [km]"
        bare = Option("x", "number", "Length", "Długość", unit="km")
        assert bare.json_schema("pl")["description"] == "Długość [km]"

    def test_one_of_becomes_one_required_group_per_alternative(self):
        """``one_of`` maps to ``oneOf`` with ``required`` groups."""
        schema = input_schema(SERIES)
        assert schema["oneOf"] == [
            {"required": ["values", "dates"]},
            {"required": ["input_file", "value_column"]},
        ]
        assert "required" not in schema

    def test_examples_are_included_as_json(self):
        """Declared examples appear as ``examples`` of the input schema."""
        command = _command(
            options=(_opt("values", "number_list"),), examples=({"values": (1, 2)},)
        )
        assert input_schema(command)["examples"] == [{"values": [1, 2]}]

    def test_schemas_are_valid_json_schema_and_accept_their_examples(self):
        """Valid 2020-12 schemas that accept the examples of every command."""
        jsonschema = pytest.importorskip("jsonschema")
        for command in data_commands():
            schema = input_schema(command)
            jsonschema.Draft202012Validator.check_schema(schema)
            validator = jsonschema.Draft202012Validator(schema)
            for example in schema.get("examples", []):
                assert list(validator.iter_errors(example)) == [], command.name

    def test_json_schema_and_validate_command_agree_on_a_rich_command(self):
        """Valid inputs pass both, invalid fail both."""
        jsonschema = pytest.importorskip("jsonschema")
        validator = jsonschema.Draft202012Validator(input_schema(RICH))
        good = {"length_km": 2.5, "cn": 75, "method": "nrcs", "values": [0, 1.5]}
        assert validator.is_valid(good)
        validate_command(RICH, good)
        for bad in (
            {"length_km": 0},
            {"length_km": 1, "cn": 101},
            {"length_km": 1, "method": "x"},
            {"length_km": 1, "values": []},
            {"length_km": 1, "unknown": 1},
            {},
        ):
            assert not validator.is_valid(bad), bad
            with pytest.raises(InvalidParameterError):
                validate_command(RICH, bad)


class TestListCommands:
    """``list_commands``: the summary list, whole or paged."""

    def test_whole_catalog_without_limit(self):
        data = list_commands().to_dict()
        assert data["schema"] == "hydrolog-command-list/1"
        assert [c["name"] for c in data["commands"]] == [
            c.name for c in data_commands()
        ]
        assert "page" not in data
        first = data["commands"][0]
        assert sorted(first) == [
            "families",
            "name",
            "operation_id",
            "read_only",
            "summary",
        ]

    def test_pages_cover_the_catalog_exactly_once(self):
        names: list[str] = []
        cursor = None
        pages = 0
        while True:
            data = list_commands(limit=7, cursor=cursor).to_dict()
            names += [c["name"] for c in data["commands"]]
            pages += 1
            assert data["page"]["total"] == len(data_commands())
            cursor = data["page"]["next_cursor"]
            assert data["page"]["truncated"] is (cursor is not None)
            if cursor is None:
                break
        assert names == [c.name for c in data_commands()]
        assert pages == -(-len(data_commands()) // 7)

    def test_a_limit_above_the_total_gives_one_untruncated_page(self):
        total = len(data_commands())
        page = list_commands(limit=total + 5).to_dict()["page"]
        assert page == {"total": total, "truncated": False, "next_cursor": None}

    @pytest.mark.parametrize("limit", [0, -1, True, 2.5, "3"])
    def test_a_bad_limit_is_a_validation_error(self, limit):
        with pytest.raises(InvalidParameterError) as caught:
            list_commands(limit=limit)
        assert caught.value.details["option"] == "limit"

    @pytest.mark.parametrize("cursor", ["!!", "bm90LWEtbnVtYmVy", "OTk5OTk5"])
    def test_an_invalid_cursor_is_a_validation_error(self, cursor):
        """Not base64, not a number, or beyond the collection."""
        with pytest.raises(InvalidParameterError) as caught:
            list_commands(limit=3, cursor=cursor)
        assert caught.value.details["option"] == "cursor"
        assert caught.value.details["reason"] == "invalid_cursor"


# --- validation -----------------------------------------------------------------------


class TestValidateCommand:
    """``validate_command``: types, bounds, choices, defaults, one_of."""

    def test_normalizes_and_applies_defaults_in_catalog_order(self):
        """Result is in declaration order with defaults filled in."""
        result = validate_command(RICH, {"cn": 75, "length_km": 3})
        assert result == {
            "length_km": 3.0,
            "cn": 75,
            "method": "kirpich",
            "ratio": 0.5,
        }
        assert list(result) == ["length_km", "cn", "method", "ratio"]
        assert isinstance(result["length_km"], float)

    def test_none_counts_as_not_given(self):
        """``None`` values are dropped (defaults still apply)."""
        result = validate_command(RICH, {"length_km": 1, "cn": None, "method": None})
        assert result == {"length_km": 1.0, "method": "kirpich", "ratio": 0.5}

    def test_unknown_option(self):
        """An undeclared option is named, with the allowed ones and a suggestion."""
        error = _invalid(RICH, {"length_km": 1, "lenght": 2})
        assert error.code == "validation_error"
        assert error.details["option"] == "lenght"
        assert error.details["reason"] == "unknown_option"
        assert "length_km" in error.details["allowed"]
        assert "Did you mean" in error.hint

    def test_command_without_options_rejects_any_option(self):
        """A command that takes nothing says so."""
        error = _invalid(_command(), {"x": 1})
        assert error.details["allowed"] == []
        assert "no options" in error.hint

    def test_options_must_be_a_mapping(self):
        """A list of values is not an options object."""
        error = _invalid(RICH, [1, 2])
        assert error.details == {
            "option": "options",
            "reason": "type",
            "expected": "object",
        }

    def test_missing_required_option(self):
        """A required option that is absent (or ``None``) fails."""
        for options in ({}, {"length_km": None}):
            error = _invalid(RICH, options)
            assert error.details == {"option": "length_km", "reason": "required"}
            assert "--length-km" in error.hint

    @pytest.mark.parametrize(
        ("option", "value", "expected"),
        [
            ("length_km", "5", "number"),
            ("length_km", True, "number"),
            ("length_km", [1], "number"),
            ("cn", 75.5, "integer"),
            ("cn", "75", "integer"),
            ("cn", False, "integer"),
            ("verbose", 1, "boolean"),
            ("verbose", "true", "boolean"),
            ("label", 5, "string"),
            ("method", 3, "string"),
            ("values", 3, "array of numbers"),
            ("values", "1,2,3", "array of numbers"),
            ("dates", "2020-01-01", "array of strings"),
            ("stations", {"a": 1}, "array of objects"),
            ("watershed", [1], "object"),
            ("input_file", 3, "string (path)"),
        ],
    )
    def test_wrong_json_type(self, option, value, expected):
        """Wrong JSON types are ``type`` errors naming the expected type."""
        error = _invalid(RICH, {"length_km": 1, option: value})
        assert error.details["option"] == option
        assert error.details["reason"] == "type"
        assert error.details["expected"] == expected
        assert "got" in error.details

    def test_bool_is_not_a_number(self):
        """``True`` must not pass as 1 for number and integer options."""
        assert _invalid(RICH, {"length_km": True}).details["reason"] == "type"
        assert _invalid(RICH, {"length_km": 1, "cn": True}).details["reason"] == "type"

    def test_integer_accepts_integral_float_and_returns_int(self):
        """JSON ``75.0`` is an integer in JSON Schema; it normalizes to ``int``."""
        result = validate_command(RICH, {"length_km": 1, "cn": 75.0})
        assert result["cn"] == 75
        assert type(result["cn"]) is int

    def test_number_accepts_int_and_numpy_scalars(self):
        """Python callers may pass NumPy numbers."""
        import numpy as np

        result = validate_command(
            RICH, {"length_km": np.float32(2.5), "cn": np.int64(70)}
        )
        assert result["length_km"] == 2.5
        assert type(result["length_km"]) is float
        assert type(result["cn"]) is int

    @pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    def test_non_finite_numbers_are_rejected(self, value):
        """NaN and infinity are never valid option values."""
        error = _invalid(RICH, {"length_km": value})
        assert error.details["reason"] == "not_finite"
        json.dumps(error.details, allow_nan=False)

    @pytest.mark.parametrize("value", [math.nan, math.inf])
    def test_non_finite_values_are_rejected_for_integers_too(self, value):
        """A float NaN is not an integer, nor is infinity."""
        error = _invalid(RICH, {"length_km": 1, "cn": value})
        assert (error.details["option"], error.details["reason"]) == (
            "cn",
            "not_finite",
        )

    def test_boolean_values(self):
        """Both booleans are valid and kept; defaults of ``False`` are applied."""
        assert (
            validate_command(RICH, {"length_km": 1, "verbose": True})["verbose"] is True
        )
        assert (
            validate_command(RICH, {"length_km": 1, "verbose": False})["verbose"]
            is False
        )
        flag = _command(options=(_opt("quiet", "boolean", default=False),))
        assert validate_command(flag, {}) == {"quiet": False}

    def test_exclusive_minimum(self):
        """The exclusive bound itself is invalid."""
        error = _invalid(RICH, {"length_km": 0})
        assert error.details == {
            "option": "length_km",
            "reason": "exclusive_minimum",
            "exclusive_minimum": 0,
            "value": 0.0,
        }
        assert validate_command(RICH, {"length_km": 1e-9})["length_km"] == 1e-9

    def test_inclusive_bounds(self):
        """Bounds are inclusive; the details name the violated one."""
        assert validate_command(RICH, {"length_km": 1, "cn": 0})["cn"] == 0
        assert validate_command(RICH, {"length_km": 1, "cn": 100})["cn"] == 100
        low = _invalid(RICH, {"length_km": 1, "cn": -1})
        assert (low.details["reason"], low.details["minimum"]) == ("minimum", 0)
        high = _invalid(RICH, {"length_km": 1, "cn": 101})
        assert (high.details["reason"], high.details["maximum"]) == ("maximum", 100)
        assert high.details["value"] == 101

    def test_choice(self):
        """A value outside the choices lists the allowed values."""
        error = _invalid(RICH, {"length_km": 1, "method": "Kirpich"})
        assert error.details["reason"] == "choice"
        assert error.details["allowed"] == ["kirpich", "nrcs"]
        assert error.details["value"] == "Kirpich"
        assert "kirpich, nrcs" in error.hint

    def test_blank_string_and_path_are_empty(self):
        """Whitespace-only text and paths are ``empty``."""
        for option in ("label", "input_file"):
            error = _invalid(RICH, {"length_km": 1, option: "   "})
            assert error.details["option"] == option
            assert error.details["reason"] == "empty"

    def test_long_offending_values_are_truncated_in_details(self):
        """Details stay small: a huge string is cut, not echoed back whole."""
        error = _invalid(RICH, {"length_km": 1, "method": "x" * 5000})
        assert len(error.details["value"]) == 200
        assert error.details["value"].endswith("…")

    def test_container_values_are_reported_by_type_only(self):
        """A rejected list or object is not echoed into the error."""
        error = _invalid(RICH, {"length_km": [1, 2, 3]})
        assert error.details["value"] == "<list>"
        assert error.details["got"] == "list"

    def test_path_with_nul_is_invalid(self):
        """A NUL byte cannot be part of a file name."""
        error = _invalid(RICH, {"length_km": 1, "input_file": "a\0b"})
        assert error.details["reason"] == "invalid_path"

    def test_path_like_objects_become_text(self):
        """``pathlib.Path`` values become ``str``; validation does not touch disk."""
        result = validate_command(
            RICH, {"length_km": 1, "input_file": Path("rel/x.csv")}
        )
        assert result["input_file"] == "rel/x.csv"

    def test_number_list(self):
        """List items are validated with the option's bounds and report their index."""
        assert validate_command(RICH, {"length_km": 1, "values": (0, 1.5)})[
            "values"
        ] == [
            0.0,
            1.5,
        ]
        low = _invalid(RICH, {"length_km": 1, "values": [1, 2, -3]})
        assert low.details["reason"] == "minimum"
        assert low.details["index"] == 2
        wrong = _invalid(RICH, {"length_km": 1, "values": [1, "x"]})
        assert (wrong.details["reason"], wrong.details["index"]) == ("type", 1)
        assert wrong.details["expected"] == "number"
        empty = _invalid(RICH, {"length_km": 1, "values": []})
        assert empty.details["reason"] == "empty"

    def test_string_list_and_object_list(self):
        """Lists of strings and of objects check each item."""
        result = validate_command(
            RICH,
            {
                "length_km": 1,
                "dates": ["2020-01-01"],
                "stations": [{"name": "a", "x": 1}],
            },
        )
        assert result["dates"] == ["2020-01-01"]
        assert result["stations"] == [{"name": "a", "x": 1}]
        error = _invalid(RICH, {"length_km": 1, "dates": ["2020-01-01", 5]})
        assert (error.details["reason"], error.details["index"]) == ("type", 1)
        error = _invalid(RICH, {"length_km": 1, "stations": [{"a": 1}, 7]})
        assert (error.details["reason"], error.details["index"]) == ("type", 1)
        assert error.details["expected"] == "object"

    def test_objects_are_deep_copied_json(self):
        """Objects are copied, tuples become lists, non-JSON content is rejected."""
        source = {"area_km2": 45.0, "tags": ("a", "b"), "nested": {"k": [1, 2]}}
        result = validate_command(RICH, {"length_km": 1, "watershed": source})
        assert result["watershed"] == {
            "area_km2": 45.0,
            "tags": ["a", "b"],
            "nested": {"k": [1, 2]},
        }
        source["nested"]["k"].append(3)
        assert result["watershed"]["nested"]["k"] == [1, 2]
        for bad in (
            {"x": object()},
            {"x": {1: 2}},
            {"x": float("nan")},
            {"x": {"y": {1}}},
        ):
            error = _invalid(RICH, {"length_km": 1, "watershed": bad})
            assert error.details["option"] == "watershed"
            assert error.details["reason"] in ("type", "not_finite")

    def test_one_of_accepts_each_complete_group(self):
        """Either complete group is valid on its own."""
        assert validate_command(SERIES, {"values": [1], "dates": ["2020-01-01"]})
        assert validate_command(SERIES, {"input_file": "a.csv", "value_column": "Q"})

    def test_one_of_none_given(self):
        """No complete group: the error names the groups and the missing option."""
        error = _invalid(SERIES, {})
        assert error.details["reason"] == "one_of"
        assert error.details["groups"] == [
            ["values", "dates"],
            ["input_file", "value_column"],
        ]
        assert error.details["given"] == []
        assert error.details["missing"] == ["values", "dates"]
        assert error.details["option"] == "values"

    def test_one_of_partial_group_reports_what_is_missing(self):
        """A half-given group points at the missing option."""
        error = _invalid(SERIES, {"input_file": "a.csv"})
        assert error.details["missing"] == ["value_column"]
        assert error.details["option"] == "value_column"
        assert error.details["given"] == ["input_file"]
        assert "missing for the closest group: value_column" in str(error)

    def test_one_of_several_complete_groups(self):
        """Two complete groups at once are ambiguous."""
        error = _invalid(
            SERIES,
            {
                "values": [1],
                "dates": ["2020-01-01"],
                "input_file": "a.csv",
                "value_column": "Q",
            },
        )
        assert error.details["reason"] == "one_of"
        assert "several" in str(error)

    def test_validation_is_idempotent(self):
        """Validating normalized options yields the same options."""
        once = validate_command(RICH, {"length_km": 2, "cn": 70.0, "values": (1, 2)})
        assert validate_command(RICH, once) == once

    def test_validation_does_not_modify_its_input(self):
        """The caller's mapping is untouched."""
        options = {"length_km": 2, "values": [1, 2]}
        validate_command(RICH, options)
        assert options == {"length_km": 2, "values": [1, 2]}

    def test_catalog_command_by_name(self):
        """Catalog commands validate by name or operation id."""
        assert validate_command("commands list", {}) == {"limit": 100}
        assert validate_command("hydrolog_commands_schema", {"limit": 2}) == {
            "limit": 2
        }
        with pytest.raises(NotFoundError):
            validate_command("nope nope", {})


# --- running --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_calls():
    CALLS.clear()
    yield
    CALLS.clear()


class TestRunCommand:
    """``run_command`` through the meta commands and test-only commands."""

    def test_commands_list_through_the_catalog(self):
        """The meta command runs end to end and returns the envelope."""
        result = run_command("commands list", {"limit": 4})
        assert isinstance(result, CommandResult)
        assert result.command == "commands list"
        assert result.inputs == {"limit": 4}
        document = result.to_dict()
        assert document["result"]["schema"] == "hydrolog-command-list/1"
        assert [c["name"] for c in document["result"]["commands"]] == [
            c.name for c in data_commands()[:4]
        ]
        assert document["page"]["total"] == len(data_commands())
        assert result.files == ()
        assert result.notices == ()

    def test_commands_schema_of_one_command(self):
        """The schema operation returns the document of ``command_schema``."""
        result = run_command("commands schema", {"command": "hydrolog_commands_list"})
        document = result.to_dict()
        assert (
            document["result"]["commands"]
            == (command_schema("commands list").to_dict()["commands"])
        )
        assert "page" not in document
        assert result.inputs == {"command": "hydrolog_commands_list", "limit": 5}

    def test_commands_schema_unknown_command_is_not_found(self):
        """A bad ``command`` option surfaces the lookup error of the operation."""
        with pytest.raises(NotFoundError):
            run_command("commands schema", {"command": "tc kirpichh"})

    def test_run_by_command_instance_calls_the_function_with_keywords(self):
        """A private Command runs without being part of the catalog."""
        command = _command(options=(_opt("length_km", "number", required=True),))
        result = run_command(command, {"length_km": 3})
        assert CALLS == [{"length_km": 3.0}]
        assert result.result == {"length_km": 3.0}
        assert result.command == "demo run"
        assert result.inputs == {"length_km": 3.0}

    def test_defaults_are_passed_to_the_operation_and_recorded(self):
        """Defaults reach the function and the envelope ``inputs``."""
        command = _command(
            options=(_opt("method", "choice", choices=("a", "b"), default="b"),)
        )
        result = run_command(command, {})
        assert CALLS == [{"method": "b"}]
        assert result.inputs == {"method": "b"}

    def test_invalid_options_never_reach_the_operation(self):
        """Validation precedes the call."""
        command = _command(options=(_opt("n", "integer", minimum=1),))
        with pytest.raises(InvalidParameterError):
            run_command(command, {"n": 0})
        assert CALLS == []

    def test_operation_errors_propagate_unchanged(self):
        """A computation error keeps its class, code and details."""
        command = _command(
            "failing_operation", options=(_opt("length_km", "number", required=True),)
        )
        with pytest.raises(CalculationError) as caught:
            run_command(command, {"length_km": 1})
        assert caught.value.code == "calculation_error"
        assert caught.value.details == {"iterations": 50}

    def test_unimportable_operation_is_an_internal_error(self):
        """A declaration pointing nowhere is a bug, reported as ``internal_error``."""
        for function in (f"{__name__}.missing", "hydrolog.no_such_module.f"):
            with pytest.raises(HydrologError) as caught:
                run_command(_command(function=function), {})
            assert caught.value.code == "internal_error"
            assert caught.value.details == {"function": function}

    def test_operation_that_is_not_callable(self):
        """An attribute that is not a function is rejected."""
        with pytest.raises(HydrologError, match="not callable"):
            run_command(_command(function=f"{__name__}.CALLS"), {})


class TestEnvelope:
    """``CommandResult``, ``Notice`` and the operation return protocol."""

    def test_envelope_document(self):
        """``to_dict`` follows ``hydrolog-result/1``."""
        import hydrolog

        command = _command(
            "noisy_operation", options=(_opt("length_km", "number", required=True),)
        )
        document = run_command(command, {"length_km": 2.5}).to_dict()
        assert list(document) == [
            "schema",
            "tool",
            "version",
            "command",
            "check",
            "status",
            "result",
            "notices",
            "inputs",
        ]
        assert document == {
            "schema": "hydrolog-result/1",
            "tool": "hydrolog",
            "version": hydrolog.__version__,
            "command": "demo run",
            "check": False,
            "status": "ok",
            "result": {"schema": "hydrolog-demo-run/1", "tc_min": 25.0},
            "notices": [
                {
                    "level": "warning",
                    "code": "outside_typical_range",
                    "message": "length is large",
                }
            ],
            "inputs": {"length_km": 2.5},
        }

    def test_a_result_that_is_not_a_document_is_a_type_error(self):
        """The domain result is a mapping; a scalar or a list cannot get a schema."""
        for value in (3.5, [1, 2], None, "text"):
            envelope = CommandResult("demo run", {}, value, "hydrolog-demo-run/1")
            with pytest.raises(TypeError, match="must be a document"):
                envelope.to_dict()

    def test_the_domain_schema_comes_first_and_the_operation_may_set_it(self):
        envelope = CommandResult("demo run", {}, {"b": 1}, "hydrolog-demo-run/1")
        assert list(envelope.to_dict()["result"]) == ["schema", "b"]
        own = CommandResult(
            "demo run", {}, {"schema": "hydrolog-plan/1"}, "hydrolog-demo-run/1"
        )
        assert own.to_dict()["result"]["schema"] == "hydrolog-plan/1"

    def test_to_json_is_strict_utf8_json(self):
        """NaN becomes ``null``, tuples and paths become JSON, text stays readable."""
        command = _command("nan_operation", options=(_opt("length_km", "number"),))
        text = run_command(command, {"length_km": 1}).to_json()
        assert json.loads(text)["result"] == {
            "schema": "hydrolog-demo-run/1",
            "value": None,
            "pair": [1, 2],
            "path": "/x/y",
        }
        assert "\n" not in text
        pretty = run_command(command, {"length_km": 1}).to_json(indent=2)
        assert "\n  " in pretty
        accented = CommandResult(
            "x y", {}, {"nazwa": "Żółć"}, "hydrolog-x-y/1"
        ).to_json()
        assert "Żółć" in accented

    def test_written_file_is_listed_inside_the_result(self, tmp_path):
        """A file reported by the wrapper is recorded with size and digest."""
        command = _command(
            "writing_operation",
            options=(
                _opt("out", "path", required=True, path_role="output"),
                _opt("text", "string"),
            ),
        )
        target = tmp_path / "out.txt"
        result = run_command(command, {"out": str(target), "text": "zażółć"})
        content = "zażółć".encode()
        record = FileRecord(
            path=str(target.resolve()),
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        assert result.files == (record,)
        document = result.to_dict()
        assert document["result"]["files"] == [
            {
                "path": str(target.resolve()),
                "size_bytes": len(content),
                "sha256": record.sha256,
                "status": "written",
            }
        ]
        assert document["result"]["chars"] == 6
        assert "files" not in document

    def test_a_replaced_file_has_the_status_replaced(self, tmp_path):
        target = tmp_path / "out.txt"
        target.write_text("old")
        envelope = CommandResult.from_output(
            "demo run",
            {},
            OperationOutput({}, files=(target,), replaced=(target,)),
            "hydrolog-demo-run/1",
        )
        assert [record.status for record in envelope.files] == ["replaced"]

    def test_output_files_protocol_on_the_result(self, tmp_path):
        """A result exposing ``output_files()`` is listed once, duplicates removed."""
        command = _command(
            "protocol_operation",
            options=(_opt("out", "path", required=True, path_role="output"),),
        )
        target = tmp_path / "bin.dat"
        result = run_command(command, {"out": str(target)})
        assert len(result.files) == 1
        assert result.files[0].sha256 == hashlib.sha256(b"\x00\x01binary").hexdigest()
        assert result.files[0].path == str(target.resolve())

    def test_reported_file_that_does_not_exist_is_an_io_error(self, tmp_path):
        """The envelope never lists a file that is not there."""
        command = _command(
            "ghost_file_operation",
            options=(_opt("out", "path", required=True, path_role="output"),),
        )
        with pytest.raises(OutputError) as caught:
            run_command(command, {"out": str(tmp_path / "ghost.txt")})
        assert caught.value.code == "io_error"
        assert caught.value.details["path"].endswith("ghost.txt")

    def test_check_and_page_are_reported(self):
        output = OperationOutput(
            {"n": 1},
            check=True,
            page={"total": 9, "next_cursor": None, "truncated": False},
        )
        document = CommandResult.from_output(
            "demo run", {}, output, "hydrolog-demo-run/1"
        ).to_dict()
        assert document["check"] is True
        assert document["page"] == {"total": 9, "next_cursor": None, "truncated": False}

    def test_sha256_file_matches_hashlib_for_large_content(self, tmp_path):
        """Hashing in chunks equals hashing at once."""
        data = os.urandom(3 * 1024 * 1024 + 17)
        path = tmp_path / "big.bin"
        path.write_bytes(data)
        assert sha256_file(path) == hashlib.sha256(data).hexdigest()

    def test_notice_validation(self):
        """Notices have a known level, a snake_case code and a message."""
        assert Notice("info", "short_series", "n=5").to_dict() == {
            "level": "info",
            "code": "short_series",
            "message": "n=5",
        }
        with pytest.raises(ValueError, match="level"):
            Notice("error", "x", "y")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="snake_case"):
            Notice("info", "Short Series", "y")
        with pytest.raises(ValueError, match="message"):
            Notice("info", "x", " ")

    def test_status_is_ok(self):
        """A returned envelope is always a success."""
        assert CommandResult("a b", {}, {}, "hydrolog-a-b/1").status == "ok"


class TestCaptureWarnings:
    """``capture_warnings``: library warnings as notices."""

    def test_user_warnings_become_deduplicated_notices(self):
        """Warnings are recorded, not printed; the list fills when the block ends."""
        with warnings.catch_warnings(record=True) as leaked:
            warnings.simplefilter("always")
            with capture_warnings() as notices:
                warnings.warn("short series", UserWarning, stacklevel=2)
                warnings.warn("value out of range", UserWarning, stacklevel=2)
                warnings.warn("short series", UserWarning, stacklevel=2)
                assert notices == []
        assert leaked == []
        assert notices == [
            Notice("warning", "user_warning", "short series"),
            Notice("warning", "user_warning", "value out of range"),
        ]

    def test_other_categories_are_reissued_not_swallowed(self):
        """A ``RuntimeWarning`` is not a notice by default and is not swallowed."""
        with (
            pytest.warns(RuntimeWarning, match="invalid value") as outer,
            capture_warnings() as notices,
        ):
            warnings.warn("invalid value encountered", RuntimeWarning, stacklevel=2)
            warnings.warn("short series", UserWarning, stacklevel=2)
        assert [n.message for n in notices] == ["short series"]
        assert [str(w.message) for w in outer] == ["invalid value encountered"]

    def test_categories_are_chosen_by_the_caller(self):
        """``categories`` selects what becomes a notice; the code names the category."""
        with capture_warnings((RuntimeWarning,)) as notices:
            warnings.warn("nan produced", RuntimeWarning, stacklevel=2)
        assert notices == [Notice("warning", "runtime_warning", "nan produced")]

    def test_empty_message_still_gives_a_notice(self):
        """A warning without text is reported by its category."""
        with capture_warnings() as notices:
            warnings.warn("", UserWarning, stacklevel=2)
        assert notices == [Notice("warning", "user_warning", "UserWarning")]

    def test_exception_in_the_block_propagates_and_releases_the_lock(self):
        """A failing computation neither hides its error nor blocks later captures."""
        with pytest.raises(CalculationError), capture_warnings():
            raise CalculationError("no convergence")
        with capture_warnings() as notices:
            warnings.warn("again", UserWarning, stacklevel=2)
        assert [n.message for n in notices] == ["again"]

    def test_concurrent_captures_do_not_mix_their_warnings(self):
        """Threads each see exactly their own warnings (blocks are serialized)."""
        results: dict[int, list[str]] = {}

        def work(number: int) -> None:
            with capture_warnings() as notices:
                for _ in range(5):
                    warnings.warn(f"thread {number}", UserWarning, stacklevel=2)
                    time.sleep(0.002)  # invites a thread switch inside the block
            results[number] = [n.message for n in notices]

        threads = [threading.Thread(target=work, args=(n,)) for n in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert results == {n: [f"thread {n}"] for n in range(8)}

    def test_operation_notices_reach_the_envelope(self):
        """An operation returning captured notices gets them in the envelope."""
        command = _command(
            "warning_operation", options=(_opt("length_km", "number", required=True),)
        )
        document = run_command(command, {"length_km": 900}).to_dict()
        assert document["notices"] == [
            {
                "level": "warning",
                "code": "user_warning",
                "message": "length_km=900.0 is outside the typical range",
            }
        ]


class TestPathPolicy:
    """Resolution of ``path`` options and ``allowed_dirs``."""

    @staticmethod
    def _path_command() -> Command:
        return _command(
            options=(
                _opt("input_file", "path"),
                _opt("out", "path", path_role="output"),
                _opt("label", "string"),
            ),
        )

    def test_relative_paths_resolve_against_the_working_directory(
        self, tmp_path, monkeypatch
    ):
        """Relative paths become absolute in the call and in the envelope."""
        monkeypatch.chdir(tmp_path)
        result = run_command(
            self._path_command(), {"input_file": "data/in.csv", "out": "o.txt"}
        )
        base = tmp_path.resolve()
        assert [
            {"input_file": str(base / "data" / "in.csv"), "out": str(base / "o.txt")}
        ] == CALLS
        assert result.inputs == CALLS[0]

    def test_dot_dot_is_normalized(self, tmp_path, monkeypatch):
        """``..`` segments collapse before the path is used."""
        monkeypatch.chdir(tmp_path)
        run_command(self._path_command(), {"input_file": "a/../b.csv"})
        assert CALLS[0]["input_file"] == str(tmp_path.resolve() / "b.csv")

    def test_home_directory_is_expanded(self, tmp_path, monkeypatch):
        """``~`` means the home directory."""
        monkeypatch.setenv("HOME", str(tmp_path))
        run_command(self._path_command(), {"input_file": "~/x.csv"})
        assert CALLS[0]["input_file"] == str(tmp_path.resolve() / "x.csv")

    def test_no_policy_allows_any_path(self, tmp_path):
        """Without ``allowed_dirs`` every path is accepted."""
        run_command(self._path_command(), {"input_file": "/etc/hostname"})
        assert CALLS[0]["input_file"] == str(Path("/etc/hostname").resolve())

    def test_path_inside_an_allowed_directory(self, tmp_path):
        """Paths under an allowed directory (and the directory itself) pass."""
        run_command(
            self._path_command(),
            {"input_file": str(tmp_path / "sub" / "a.csv"), "out": str(tmp_path)},
            allowed_dirs=[tmp_path],
        )
        assert len(CALLS) == 1

    def test_path_outside_is_forbidden_before_the_call(self, tmp_path):
        """A path outside all allowed directories is ``forbidden``."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        with pytest.raises(ForbiddenPathError) as caught:
            run_command(
                self._path_command(),
                {
                    "input_file": str(allowed / "ok.csv"),
                    "out": str(tmp_path / "evil.txt"),
                },
                allowed_dirs=[allowed],
            )
        error = caught.value
        assert error.code == "forbidden"
        assert error.exit_code == 12
        assert error.details["option"] == "out"
        assert error.details["path"] == str((tmp_path / "evil.txt").resolve())
        assert error.details["allowed_dirs"] == [str(allowed.resolve())]
        assert CALLS == []

    def test_sibling_directory_with_common_prefix_is_outside(self, tmp_path):
        """``/data2`` is not inside ``/data`` (no string-prefix matching)."""
        allowed = tmp_path / "data"
        other = tmp_path / "data2"
        allowed.mkdir()
        other.mkdir()
        with pytest.raises(ForbiddenPathError):
            run_command(
                self._path_command(),
                {"input_file": str(other / "x.csv")},
                allowed_dirs=[allowed],
            )

    def test_dot_dot_cannot_escape(self, tmp_path):
        """``allowed/../outside`` resolves outside and is refused."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        with pytest.raises(ForbiddenPathError):
            run_command(
                self._path_command(),
                {"input_file": str(allowed / ".." / "secret.csv")},
                allowed_dirs=[allowed],
            )

    def test_symlink_cannot_escape(self, tmp_path):
        """A symlink inside the allowed directory that points outside is refused."""
        allowed = tmp_path / "data"
        outside = tmp_path / "outside"
        allowed.mkdir()
        outside.mkdir()
        (outside / "secret.csv").write_text("x")
        try:
            os.symlink(outside, allowed / "link")
        except (OSError, NotImplementedError):
            pytest.skip("symlinks are not available")
        with pytest.raises(ForbiddenPathError):
            run_command(
                self._path_command(),
                {"input_file": str(allowed / "link" / "secret.csv")},
                allowed_dirs=[allowed],
            )

    def test_relative_path_is_checked_after_resolution(self, tmp_path, monkeypatch):
        """A relative path is judged by where it points, not by how it is written."""
        allowed = tmp_path / "data"
        allowed.mkdir()
        monkeypatch.chdir(allowed)
        run_command(
            self._path_command(), {"input_file": "in.csv"}, allowed_dirs=[allowed]
        )
        with pytest.raises(ForbiddenPathError):
            run_command(
                self._path_command(),
                {"input_file": "../in.csv"},
                allowed_dirs=[allowed],
            )

    def test_empty_allowed_dirs_forbids_every_path_but_not_pure_commands(self):
        """The MCP default: no directory allowed means no file access."""
        with pytest.raises(ForbiddenPathError) as caught:
            run_command(self._path_command(), {"input_file": "x.csv"}, allowed_dirs=())
        assert "allow-dir" in caught.value.hint
        assert caught.value.details["allowed_dirs"] == []
        result = run_command(self._path_command(), {"label": "ok"}, allowed_dirs=())
        assert result.result == {"label": "ok"}
        assert run_command("commands list", allowed_dirs=()).command == "commands list"

    def test_allowed_dirs_may_be_a_single_path(self, tmp_path):
        """A bare string or Path is one directory, not a sequence of characters."""
        run_command(
            self._path_command(),
            {"input_file": str(tmp_path / "a.csv")},
            allowed_dirs=str(tmp_path),
        )
        run_command(
            self._path_command(),
            {"input_file": str(tmp_path / "b.csv")},
            allowed_dirs=tmp_path,
        )
        assert len(CALLS) == 2

    def test_several_allowed_directories(self, tmp_path):
        """A path inside any one of the directories passes."""
        first, second = tmp_path / "a", tmp_path / "b"
        first.mkdir()
        second.mkdir()
        run_command(
            self._path_command(),
            {"input_file": str(second / "x.csv")},
            allowed_dirs=[first, second],
        )
        assert len(CALLS) == 1


# --- integrity of the real catalog ----------------------------------------------------


def _operation(command: Command):
    module_name, _, attribute = command.function.rpartition(".")
    return module_name, getattr(importlib.import_module(module_name), attribute)


@pytest.mark.parametrize("command", data_commands(), ids=lambda c: c.name)
class TestCatalogIntegrity:
    """Every declared command is runnable: its operation exists and fits its options."""

    def test_operation_lives_in_the_operation_layer(self, command):
        """``function`` points at a public callable of ``hydrolog.operations``."""
        module_name, function = _operation(command)
        assert module_name == "hydrolog.operations"
        assert callable(function)
        assert not command.function.rpartition(".")[2].startswith("_")

    def test_every_option_is_a_keyword_parameter_of_the_operation(self, command):
        """The call ``function(**options)`` can bind every declared option."""
        _, function = _operation(command)
        parameters = inspect.signature(function).parameters
        accepts_any = any(p.kind is p.VAR_KEYWORD for p in parameters.values())
        for option in command.options:
            assert accepts_any or option.name in parameters, option.name
            if option.name in parameters:
                assert parameters[option.name].kind in (
                    inspect.Parameter.KEYWORD_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )

    def test_parameters_without_default_are_required_options(self, command):
        """A parameter the operation cannot do without is a required option."""
        _, function = _operation(command)
        required = {o.name for o in command.options if o.required}
        for name, parameter in inspect.signature(function).parameters.items():
            if parameter.kind is parameter.VAR_KEYWORD:
                continue
            if parameter.default is parameter.empty:
                assert name in required, name

    def test_command_has_an_example_and_every_example_validates(self, command):
        """Each command ships at least one valid example."""
        assert command.examples, f"{command.name} has no examples"
        for example in command.examples:
            validate_command(command, example)
