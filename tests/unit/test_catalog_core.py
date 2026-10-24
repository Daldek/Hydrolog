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
    Notice,
    OperationOutput,
    Option,
    capture_warnings,
    command_schema,
    data_commands,
    get_command,
    run_command,
    validate_command,
)
from hydrolog.catalog.envelope import FileRecord, sha256_file
from hydrolog.catalog.groups import GROUP_MODULES, collect_commands
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
        "operation_id": "demo_run",
        "summary": "Demo.",
        "summary_en": "Demo.",
        "description": "Opis demonstracyjny.",
        "description_en": "Demo description.",
        "function": f"{__name__}:{operation}",
        "options": (),
    }
    fields.update(overrides)
    return Command(**fields)


def _opt(name: str, type_: Any, **kwargs: Any) -> Option:
    return Option(name, type_, f"Opis {name}", f"Description {name}", **kwargs)


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
        _opt("out", "path", writes=True),
        _opt("ratio", "number", default=0.5, minimum=0, maximum=1, unit="m/m"),
    ),
    writes=True,
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

    def test_writes_only_for_paths(self):
        """Only a path option can be written."""
        with pytest.raises(ValueError, match="writes"):
            _opt("n", "number", writes=True)

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
        with pytest.raises(ValueError, match="description_en"):
            Option("x", "number", "Opis", " ")

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
            name="stats flood-frequency", operation_id="stats_flood_frequency"
        )
        assert (command.group, command.subcommand) == ("stats", "flood-frequency")

    @pytest.mark.parametrize(
        "name",
        ["kirpich", "tc  kirpich", "TC kirpich", "tc kirpich extra", "tc ki_rpich"],
    )
    def test_bad_names_are_rejected(self, name):
        """A name is ``<group> <command>`` in lowercase."""
        with pytest.raises(ValueError, match="name must be"):
            _command(name=name, operation_id="x")

    def test_operation_id_must_be_snake_case_of_name(self):
        """``operation_id`` is the name with spaces and hyphens as underscores."""
        with pytest.raises(ValueError, match="operation_id must be 'demo_run_it'"):
            _command(name="demo run-it", operation_id="demo-run-it")

    def test_summary_length_limit(self):
        """Summaries are one line of at most 120 characters."""
        _command(summary="x" * 120)
        with pytest.raises(ValueError, match="longer than 120"):
            _command(summary="x" * 121)
        with pytest.raises(ValueError, match="single line"):
            _command(summary_en="a\nb")

    @pytest.mark.parametrize(
        "function", ["operations.tc_kirpich", "hydrolog.operations:", "a b:c", ":x"]
    )
    def test_function_path_format(self, function):
        """The function is ``package.module:attribute``."""
        with pytest.raises(ValueError, match="function must have the form"):
            _command(function=function)

    def test_option_names_must_be_unique(self):
        """Two options with one name are rejected."""
        with pytest.raises(ValueError, match="unique"):
            _command(options=(_opt("a", "number"), _opt("a", "string")))

    def test_options_must_be_a_tuple_of_options(self):
        """Lists would be mutable inside a frozen declaration."""
        with pytest.raises(ValueError, match="options must be a tuple"):
            _command(options=[_opt("a", "number")])

    def test_writes_must_match_write_options(self):
        """``writes`` is true exactly when an option writes."""
        out = _opt("out", "path", writes=True)
        with pytest.raises(ValueError, match="writes must be true"):
            _command(options=(out,), writes=False)
        with pytest.raises(ValueError, match="writes must be true"):
            _command(options=(_opt("a", "number"),), writes=True)

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

    def test_examples_must_be_mappings(self):
        """An example is an options mapping."""
        with pytest.raises(ValueError, match="example #0 must be a mapping"):
            _command(options=(_opt("a", "number"),), examples=([1],))

    def test_descriptions_must_not_be_empty(self):
        """Both long descriptions are required."""
        with pytest.raises(ValueError, match="description_en"):
            _command(description_en=" ")

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
    return _command(name=name, operation_id=name.replace(" ", "_").replace("-", "_"))


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
        assert get_command("commands list") is get_command("commands_list")

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
    """The ``hydrolog-commands/1`` document."""

    def test_root_document_describes_the_whole_catalog(self):
        """Without a command every catalog command is described."""
        doc = command_schema()
        assert doc["schema"] == "hydrolog-commands/1"
        assert doc["lang"] == "pl"
        assert [c["name"] for c in doc["commands"]] == [c.name for c in data_commands()]
        import hydrolog

        assert doc["version"] == hydrolog.__version__

    def test_single_command_by_operation_id(self):
        """A command selects one entry of the same document shape."""
        doc = command_schema("commands_schema")
        assert [c["name"] for c in doc["commands"]] == ["commands schema"]

    def test_entry_keys(self):
        """An entry has the fields of the spec."""
        entry = command_schema(RICH)["commands"][0]
        assert list(entry) == [
            "name",
            "operation_id",
            "summary",
            "description",
            "input_schema",
            "x-hydrolog",
        ]
        assert entry["x-hydrolog"] == {
            "writes": True,
            "function": f"{__name__}:echo_operation",
            "units": {"length_km": "km", "ratio": "m/m"},
        }

    def test_language_selects_texts_only(self):
        """Structure is identical in both languages; texts differ."""
        pl = command_schema(RICH, lang="pl")["commands"][0]
        en = command_schema(RICH, lang="en")["commands"][0]
        assert pl["description"] == "Opis demonstracyjny."
        assert en["description"] == "Demo description."
        assert pl["input_schema"]["properties"]["cn"]["description"] == "Opis cn"
        assert en["input_schema"]["properties"]["cn"]["description"] == "Description cn"
        strip = lambda schema: json.dumps(  # noqa: E731
            {k: v for k, v in schema.items() if k != "description"}, sort_keys=True
        )
        assert [strip(p) for p in pl["input_schema"]["properties"].values()] == [
            strip(p) for p in en["input_schema"]["properties"].values()
        ]

    def test_unknown_language_is_rejected(self):
        """Only ``pl`` and ``en`` are languages of the catalog."""
        with pytest.raises(InvalidParameterError) as caught:
            command_schema(lang="de")  # type: ignore[arg-type]
        assert caught.value.details["option"] == "lang"
        assert caught.value.details["allowed"] == ["pl", "en"]

    def test_unknown_command_is_not_found(self):
        """Asking for a command that does not exist is ``not_found``."""
        with pytest.raises(NotFoundError):
            command_schema("no such")

    def test_input_schema_per_option_type(self):
        """Every option type maps to its JSON Schema form."""
        schema = command_schema(RICH)["commands"][0]["input_schema"]
        props = schema["properties"]
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["length_km"]
        assert "oneOf" not in schema
        assert props["length_km"] == {
            "type": "number",
            "exclusiveMinimum": 0,
            "description": "Opis length_km [km]",
        }
        assert props["cn"]["type"] == "integer"
        assert (props["cn"]["minimum"], props["cn"]["maximum"]) == (0, 100)
        assert props["method"] == {
            "type": "string",
            "enum": ["kirpich", "nrcs"],
            "description": "Opis method",
            "default": "kirpich",
        }
        assert props["verbose"]["type"] == "boolean"
        assert props["label"] == {
            "type": "string",
            "minLength": 1,
            "description": "Opis label",
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

    def test_unit_is_not_repeated_when_the_text_names_it(self):
        """The unit is appended in brackets only when the description lacks it."""
        option = Option("x", "number", "Długość [km]", "Length [km]", unit="km")
        assert option.json_schema("pl")["description"] == "Długość [km]"
        assert option.json_schema("en")["description"] == "Length [km]"
        bare = Option("x", "number", "Długość", "Length", unit="km")
        assert bare.json_schema("pl")["description"] == "Długość [km]"

    def test_one_of_becomes_one_required_group_per_alternative(self):
        """``one_of`` maps to ``oneOf`` with ``required`` groups."""
        schema = command_schema(SERIES)["commands"][0]["input_schema"]
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
        schema = command_schema(command)["commands"][0]["input_schema"]
        assert schema["examples"] == [{"values": [1, 2]}]

    def test_document_is_strict_json(self):
        """The whole catalog serializes without NaN or odd types."""
        json.dumps(command_schema(), allow_nan=False)

    def test_schemas_are_valid_json_schema_and_accept_their_examples(self):
        """With ``jsonschema`` installed: valid 2020-12 schemas that accept examples."""
        jsonschema = pytest.importorskip("jsonschema")
        for entry in command_schema()["commands"]:
            schema = entry["input_schema"]
            jsonschema.Draft202012Validator.check_schema(schema)
            validator = jsonschema.Draft202012Validator(schema)
            for example in schema.get("examples", []):
                assert list(validator.iter_errors(example)) == [], entry["name"]

    def test_json_schema_and_validate_command_agree_on_a_rich_command(self):
        """With ``jsonschema`` installed: valid inputs pass both, invalid fail both."""
        jsonschema = pytest.importorskip("jsonschema")
        schema = command_schema(RICH)["commands"][0]["input_schema"]
        validator = jsonschema.Draft202012Validator(schema)
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
        assert validate_command("commands list", {}) == {"lang": "pl"}
        assert validate_command("commands_schema", {"lang": "en"}) == {"lang": "en"}
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
        result = run_command("commands list")
        assert isinstance(result, CommandResult)
        assert result.command == "commands list"
        assert result.inputs == {"lang": "pl"}
        names = [item.name for item in result.result]
        assert names == [c.name for c in data_commands()]
        assert result.files == ()
        assert result.notices == ()

    def test_commands_list_english_summaries(self):
        """``lang`` changes the summaries only."""
        pl = run_command("commands list", {"lang": "pl"}).result
        en = run_command("commands_list", {"lang": "en"}).result
        assert [a.name for a in pl] == [b.name for b in en]
        assert [a.summary for a in pl] != [b.summary for b in en]
        listing = next(item for item in en if item.name == "commands list")
        assert listing.summary.startswith("List the catalog commands")

    def test_commands_schema_of_one_command(self):
        """The schema operation returns the same document as ``command_schema``."""
        result = run_command(
            "commands schema", {"command": "commands_list", "lang": "en"}
        )
        assert result.result == command_schema("commands list", lang="en")
        assert result.inputs == {"command": "commands_list", "lang": "en"}

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
        for function in (f"{__name__}:missing", "hydrolog.no_such_module:f"):
            with pytest.raises(HydrologError) as caught:
                run_command(_command(function=function), {})
            assert caught.value.code == "internal_error"
            assert caught.value.details == {"function": function}

    def test_operation_that_is_not_callable(self):
        """An attribute that is not a function is rejected."""
        with pytest.raises(HydrologError, match="not callable"):
            run_command(_command(function=f"{__name__}:CALLS"), {})


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
            "command",
            "hydrolog_version",
            "status",
            "inputs",
            "result",
            "files",
            "notices",
        ]
        assert document == {
            "schema": "hydrolog-result/1",
            "command": "demo run",
            "hydrolog_version": hydrolog.__version__,
            "status": "ok",
            "inputs": {"length_km": 2.5},
            "result": {"tc_min": 25.0},
            "files": [],
            "notices": [
                {
                    "level": "warning",
                    "code": "outside_typical_range",
                    "text": "length is large",
                }
            ],
        }

    def test_to_json_is_strict_utf8_json(self):
        """NaN becomes ``null``, tuples and paths become JSON, text stays readable."""
        command = _command("nan_operation", options=(_opt("length_km", "number"),))
        text = run_command(command, {"length_km": 1}).to_json()
        assert json.loads(text)["result"] == {
            "value": None,
            "pair": [1, 2],
            "path": "/x/y",
        }
        assert "\n" not in text
        pretty = run_command(command, {"length_km": 1}).to_json(indent=2)
        assert "\n  " in pretty
        accented = CommandResult("x y", {}, {"nazwa": "Żółć"}).to_json()
        assert "Żółć" in accented

    def test_written_file_is_listed_with_sha256(self, tmp_path):
        """A file reported by the wrapper is recorded with its digest."""
        command = _command(
            "writing_operation",
            options=(
                _opt("out", "path", required=True, writes=True),
                _opt("text", "string"),
            ),
            writes=True,
        )
        target = tmp_path / "out.txt"
        result = run_command(command, {"out": str(target), "text": "zażółć"})
        digest = hashlib.sha256("zażółć".encode()).hexdigest()
        assert result.files == (FileRecord(path=str(target.resolve()), sha256=digest),)
        assert result.to_dict()["files"] == [
            {"role": "output", "path": str(target.resolve()), "sha256": digest}
        ]
        assert result.result == {"chars": 6}

    def test_output_files_protocol_on_the_result(self, tmp_path):
        """A result exposing ``output_files()`` is listed once, duplicates removed."""
        command = _command(
            "protocol_operation",
            options=(_opt("out", "path", required=True, writes=True),),
            writes=True,
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
            options=(_opt("out", "path", required=True, writes=True),),
            writes=True,
        )
        with pytest.raises(OutputError) as caught:
            run_command(command, {"out": str(tmp_path / "ghost.txt")})
        assert caught.value.code == "io_error"
        assert caught.value.details["path"].endswith("ghost.txt")

    def test_sha256_file_matches_hashlib_for_large_content(self, tmp_path):
        """Hashing in chunks equals hashing at once."""
        data = os.urandom(3 * 1024 * 1024 + 17)
        path = tmp_path / "big.bin"
        path.write_bytes(data)
        assert sha256_file(path) == hashlib.sha256(data).hexdigest()

    def test_notice_validation(self):
        """Notices have a known level, a snake_case code and a text."""
        assert Notice("info", "short_series", "n=5").to_dict() == {
            "level": "info",
            "code": "short_series",
            "text": "n=5",
        }
        with pytest.raises(ValueError, match="level"):
            Notice("error", "x", "y")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="snake_case"):
            Notice("info", "Short Series", "y")
        with pytest.raises(ValueError, match="text"):
            Notice("info", "x", " ")

    def test_status_is_ok(self):
        """A returned envelope is always a success."""
        assert CommandResult("a b", {}, None).status == "ok"


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
        assert [n.text for n in notices] == ["short series"]
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
        assert [n.text for n in notices] == ["again"]

    def test_concurrent_captures_do_not_mix_their_warnings(self):
        """Threads each see exactly their own warnings (blocks are serialized)."""
        results: dict[int, list[str]] = {}

        def work(number: int) -> None:
            with capture_warnings() as notices:
                for _ in range(5):
                    warnings.warn(f"thread {number}", UserWarning, stacklevel=2)
                    time.sleep(0.002)  # invites a thread switch inside the block
            results[number] = [n.text for n in notices]

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
                "text": "length_km=900.0 is outside the typical range",
            }
        ]


class TestPathPolicy:
    """Resolution of ``path`` options and ``allowed_dirs``."""

    @staticmethod
    def _path_command() -> Command:
        return _command(
            options=(
                _opt("input_file", "path"),
                _opt("out", "path", writes=True),
                _opt("label", "string"),
            ),
            writes=True,
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
    module_name, _, attribute = command.function.partition(":")
    return module_name, getattr(importlib.import_module(module_name), attribute)


@pytest.mark.parametrize("command", data_commands(), ids=lambda c: c.name)
class TestCatalogIntegrity:
    """Every declared command is runnable: its operation exists and fits its options."""

    def test_operation_lives_in_the_operation_layer(self, command):
        """``function`` points at a public callable of ``hydrolog.operations``."""
        module_name, function = _operation(command)
        assert module_name == "hydrolog.operations"
        assert callable(function)
        assert not command.function.split(":")[1].startswith("_")

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

    def test_schema_example_validates_against_its_input_schema(self, command):
        """With ``jsonschema`` installed the examples satisfy the generated schema."""
        jsonschema = pytest.importorskip("jsonschema")
        schema = command_schema(command)["commands"][0]["input_schema"]
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        for example in schema.get("examples", []):
            assert validator.is_valid(example)
