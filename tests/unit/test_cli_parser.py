"""Tests for the generated parsers: option syntax, examples and declarations."""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from hydrolog.catalog import Command, Option, get_command
from hydrolog.cli.parser import (
    UsageError,
    build_command_parser,
    build_group_parser,
    build_root_parser,
    example_arguments,
    format_example,
    join_negative_values,
    parse_command_line,
)
from hydrolog.exceptions import InvalidParameterError


def _command(*options: Option, examples=(), one_of=()) -> Command:
    return Command(
        name="demo run",
        operation_id="demo_run",
        summary="Demo.",
        summary_en="Demo.",
        description="Opis.",
        description_en="Description.",
        function="tests.unit.test_cli_parser:unused",
        options=options,
        examples=examples,
        one_of=one_of,
    )


def _option(name: str, kind: Any = "number", **kwargs: Any) -> Option:
    if kind == "choice":
        kwargs.setdefault("choices", ("a", "b"))
    return Option(name, kind, "Opis", "Description", **kwargs)


class TestExamples:
    """An example becomes command-line words that read back as the same values."""

    def test_each_option_type(self):
        command = _command(
            _option("count", "integer"),
            _option("length_km", "number"),
            _option("values", "number_list"),
            _option("names", "string_list"),
            _option("mode", "choice"),
            _option("input_file", "path"),
            _option("watershed", "object"),
            _option("parts", "object_list"),
            _option("verbose", "boolean"),
            _option("quiet", "boolean"),
        )
        words = example_arguments(
            command,
            {
                "count": 5,
                "length_km": 72.0,
                "values": [1, 2.5, 1e-05],
                "names": ["a", "b"],
                "mode": "a",
                "input_file": Path("data") / "x.csv",
                "watershed": {"name": "Młynówka", "cn": 70},
                "parts": [{"cn": 55}],
                "verbose": True,
                "quiet": False,
            },
        )
        assert words == [
            "--count",
            "5",
            "--length-km",
            "72",
            "--values",
            "1,2.5,1e-05",
            "--names",
            "a,b",
            "--mode",
            "a",
            "--input-file",
            os.path.join("data", "x.csv"),
            "--watershed",
            '{"name":"Młynówka","cn":70}',
            "--parts",
            '[{"cn":55}]',
            "--verbose",
            "--no-quiet",
        ]

    def test_negative_values_use_the_equals_form(self):
        command = _command(_option("offset"), _option("values", "number_list"))
        words = example_arguments(command, {"offset": -5, "values": [-1, 2]})
        assert words == ["--offset=-5", "--values=-1,2"]

    def test_none_and_unknown_names_are_skipped(self):
        command = _command(_option("a"), _option("b"))
        assert example_arguments(command, {"a": None, "b": 1, "zzz": 3}) == ["--b", "1"]

    def test_text_items_with_commas_are_given_as_json(self):
        command = _command(_option("names", "string_list"))
        assert example_arguments(command, {"names": ["a,b", "c"]}) == [
            "--names",
            '["a,b", "c"]',
        ]
        assert example_arguments(command, {"names": ["[x]", "c"]}) == [
            "--names",
            '["[x]", "c"]',
        ]

    def test_format_example_is_a_quoted_shell_line(self):
        command = get_command("tc kirpich")
        assert (
            format_example(command, {"length_km": 8.2, "slope_m_per_m": 0.023})
            == "hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023"
        )
        quoted = format_example(
            get_command("cn weighted"), {"parts": [{"cn": 55, "area": 27.2}]}
        )
        assert quoted == 'hydrolog cn weighted --parts \'[{"cn":55,"area":27.2}]\''

    @pytest.mark.parametrize(
        ("kind", "value", "expected"),
        [
            ("number_list", [-1.5, 2, 3e-07], [-1.5, 2.0, 3e-07]),
            ("string_list", ["x", "a,b", "[c]"], ["x", "a,b", "[c]"]),
            ("string_list", ["2020-01-01", "2020-01-02"], ["2020-01-01", "2020-01-02"]),
            ("object", {"a": [1, 2], "b": {"c": "ł"}}, {"a": [1, 2], "b": {"c": "ł"}}),
            ("object_list", [{"a": 1}, {"b": "x y"}], [{"a": 1}, {"b": "x y"}]),
            ("integer", 7, 7),
            ("number", 0.1, 0.1),
            ("path", "a b/c.csv", "a b/c.csv"),
        ],
    )
    def test_values_survive_the_round_trip(self, kind, value, expected):
        command = _command(_option("value", kind))
        line = parse_command_line(command, example_arguments(command, {"value": value}))
        assert line.options == {"value": expected}


class TestParsing:
    """Reading the words after the command."""

    def test_only_given_options_are_reported(self):
        command = _command(_option("a"), _option("b", default=3))
        line = parse_command_line(command, ["--a", "1"])
        assert line.options == {"a": 1.0}
        assert (line.json, line.schema) == (False, False)

    def test_general_flags(self):
        command = _command(_option("a"))
        line = parse_command_line(command, ["--json", "--schema", "--lang", "en"])
        assert (line.json, line.schema, line.options) == (True, True, {})

    def test_abbreviations_are_not_accepted(self):
        command = _command(_option("length_km"))
        with pytest.raises(UsageError) as caught:
            parse_command_line(command, ["--length", "5"])
        assert caught.value.details["reason"] == "unknown_option"
        assert "Did you mean --length-km?" in caught.value.hint

    def test_boolean_takes_no_value(self):
        command = _command(_option("flag", "boolean"))
        assert parse_command_line(command, ["--flag"]).options == {"flag": True}
        assert parse_command_line(command, ["--no-flag"]).options == {"flag": False}
        with pytest.raises(UsageError):
            parse_command_line(command, ["--flag=yes"])

    def test_last_occurrence_wins(self):
        command = _command(_option("a"))
        assert parse_command_line(command, ["--a", "1", "--a", "2"]).options == {
            "a": 2.0
        }

    def test_a_type_error_is_a_validation_error_not_a_usage_error(self):
        command = _command(_option("a"))
        with pytest.raises(InvalidParameterError) as caught:
            parse_command_line(command, ["--a", "x"])
        assert not isinstance(caught.value, UsageError)
        assert caught.value.details["reason"] == "type"

    def test_usage_error_names_the_command(self):
        with pytest.raises(UsageError) as caught:
            parse_command_line(_command(_option("a")), ["--zzz"])
        assert caught.value.command == "demo run"
        assert caught.value.prog == "hydrolog demo run"
        assert caught.value.code == "validation_error"

    @pytest.mark.parametrize(
        ("words", "expected"),
        [
            (["--a", "-5"], ["--a=-5"]),
            (["--a", "-1e-3", "--b", "x"], ["--a=-1e-3", "--b", "x"]),
            (["--a", "-.5"], ["--a=-.5"]),
            (["--lang", "-1"], ["--lang=-1"]),
            (["--flag", "-5"], ["--flag", "-5"]),
            (["--a", "-x"], ["--a", "-x"]),
            (["--a", "5", "-5"], ["--a", "5", "-5"]),
            (["--a"], ["--a"]),
        ],
    )
    def test_negative_values_are_joined_to_their_flag(self, words, expected):
        command = _command(
            _option("a"), _option("b", "string"), _option("flag", "boolean")
        )
        assert join_negative_values(words, command) == expected

    def test_help_is_printed_by_the_parser(self, capsys):
        with pytest.raises(SystemExit) as caught:
            parse_command_line(_command(_option("a")), ["--help"])
        assert caught.value.code == 0
        assert "--a NUMBER" in capsys.readouterr().out


class TestDeclarations:
    """A declaration that cannot become a command line is reported early."""

    @pytest.mark.parametrize("name", ["json", "schema", "help", "version"])
    def test_option_named_like_a_general_flag(self, name):
        with pytest.raises(ValueError, match=f"--{name}"):
            build_command_parser(_command(_option(name)))

    def test_boolean_negation_collides_with_another_option(self):
        with pytest.raises(ValueError, match="--no-flag"):
            build_command_parser(
                _command(_option("flag", "boolean"), _option("no_flag", "boolean"))
            )

    def test_lang_option_is_the_general_flag(self):
        command = _command(
            _option("lang", "choice", choices=("pl", "en"), default="pl")
        )
        line = parse_command_line(command, ["--lang", "en"])
        assert line.options == {}  # reported through the language, not as an option


class TestHelpParsers:
    """The parsers that only print help."""

    def test_root_help_without_examples(self):
        parser = build_root_parser([_command(_option("a"))], "en")
        text = parser.format_help()
        assert "Examples:" not in text
        assert "  demo " in text

    def test_root_help_uses_the_first_example(self):
        command = _command(_option("a"), examples=({"a": 2},))
        text = build_root_parser([command], "pl").format_help()
        assert "  hydrolog demo run --a 2\n" in text
        assert "  hydrolog demo run --a 2 --json\n" in text
        assert "  hydrolog demo run --schema\n" in text

    def test_required_boolean_is_spelled_without_a_value_in_the_usage(self):
        command = _command(_option("flag", "boolean", required=True), _option("a"))
        usage = build_command_parser(command, "en").format_usage()
        assert usage == "usage: hydrolog demo run --flag [options]\n"

    def test_group_help_lists_summaries(self):
        text = build_group_parser("demo", [_command(_option("a"))], "en").format_help()
        assert text.startswith("usage: hydrolog demo [general options] <command>")
        assert "run" in text and "Demo." in text

    def test_defaults_are_shown_for_booleans_and_lists(self):
        command = _command(
            _option("flag", "boolean", default=True),
            _option("rps", "number_list", default=[2, 5]),
        )
        text = build_command_parser(command, "pl").format_help()
        assert "(domyślnie: tak)" in text
        assert "(domyślnie: 2,5)" in text

    def test_percent_signs_survive(self):
        command = _command(
            Option("share", "number", "Udział 100% powierzchni", "Share of 100% area")
        )
        assert "Udział 100% powierzchni" in build_command_parser(command).format_help()

    def test_example_with_unicode_is_printed_verbatim(self):
        command = _command(
            _option("watershed", "object"),
            examples=({"watershed": {"name": "Młynówka"}},),
        )
        text = build_command_parser(command).format_help()
        assert (
            json.dumps({"name": "Młynówka"}, ensure_ascii=False, separators=(",", ":"))
            in text
        )
