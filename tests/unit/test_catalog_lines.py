"""Command lines of the catalog: a call's canonical line and its reading (AGI-2.1)."""

import os
from pathlib import Path
from typing import Any

import pytest

from hydrolog.catalog import (
    Command,
    Option,
    format_command,
    get_command,
    parse_command,
)
from hydrolog.catalog.lines import option_arguments
from hydrolog.cli.parser import UsageError, parse_command_line
from hydrolog.exceptions import InvalidParameterError, NotFoundError


def _command(*options: Option) -> Command:
    return Command(
        name="demo run",
        operation_id="hydrolog_demo_run",
        summary="Demo.",
        summary_pl="Demo PL.",
        description="Description.",
        description_pl="Opis.",
        function="tests.unit.test_catalog_lines.unused",
        options=options,
        examples=({},),
        result_schema="hydrolog-demo-run/1",
        example_results=({},),
    )


def _option(name: str, kind: Any = "number", **kwargs: Any) -> Option:
    if kind == "choice":
        kwargs.setdefault("choices", ("a", "b"))
        kwargs.setdefault("meanings", {"a": "First one", "b": "Second one"})
        kwargs.setdefault("meanings_pl", {"a": "Pierwszy", "b": "Drugi"})
    if kind == "path":
        kwargs.setdefault("path_role", "input")
    return Option(name, kind, "Opis", "Description", **kwargs)


class TestOptionWords:
    """Option values become command-line words that read back as the same values."""

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
        words = option_arguments(
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
        words = option_arguments(command, {"offset": -5, "values": [-1, 2]})
        assert words == ["--offset=-5", "--values=-1,2"]

    def test_none_and_unknown_names_are_skipped(self):
        command = _command(_option("a"), _option("b"))
        assert option_arguments(command, {"a": None, "b": 1, "zzz": 3}) == ["--b", "1"]

    def test_text_items_with_commas_are_given_as_json(self):
        command = _command(_option("names", "string_list"))
        assert option_arguments(command, {"names": ["a,b", "c"]}) == [
            "--names",
            '["a,b", "c"]',
        ]
        assert option_arguments(command, {"names": ["[x]", "c"]}) == [
            "--names",
            '["[x]", "c"]',
        ]

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
        line = parse_command_line(command, option_arguments(command, {"value": value}))
        assert line.options == {"value": expected}


class TestFormatCommand:
    """The canonical line of a call."""

    def test_the_line_is_a_quoted_shell_line(self):
        assert (
            format_command("tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023})
            == "hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023"
        )
        quoted = format_command("cn weighted", {"parts": [{"cn": 55, "area": 27.2}]})
        assert quoted == 'hydrolog cn weighted --parts \'[{"cn":55,"area":27.2}]\''

    def test_a_text_with_spaces_and_polish_letters_is_one_quoted_word(self):
        line = format_command(
            "report generate",
            {"output": "raport.md", "watershed_name": "Kamiennik — Świerzawa"},
        )
        assert line == (
            "hydrolog report generate --output raport.md "
            "--watershed-name 'Kamiennik — Świerzawa'"
        )

    def test_options_follow_the_catalog_order_and_numbers_their_shortest_form(self):
        line = format_command("tc kirpich", {"slope_m_per_m": 0.023, "length_km": 8})
        assert line == "hydrolog tc kirpich --length-km 8 --slope-m-per-m 0.023"
        assert format_command("tc kirpich", {"length_km": 8.0}) == (
            "hydrolog tc kirpich --length-km 8"
        )

    def test_none_is_an_option_that_is_not_given(self):
        given = {"length_km": 2.5, "slope_m_per_m": None}
        line = format_command("tc kirpich", given)
        assert line == "hydrolog tc kirpich --length-km 2.5"

    def test_run_flags_come_last_in_a_fixed_order(self):
        run = {"quiet": True, "lang": "en", "json": True, "verbose": False}
        assert format_command("cn list", {}, run) == (
            "hydrolog cn list --json --lang en --quiet"
        )

    def test_a_command_is_named_by_its_name_its_operation_id_or_its_declaration(self):
        assert (
            format_command("cn list")
            == format_command("hydrolog_cn_list")
            == format_command(get_command("cn list"))
            == "hydrolog cn list"
        )

    def test_a_call_the_run_would_refuse_still_has_its_line(self):
        """Bounds, choices, required options and groups are the run's to judge."""
        assert format_command("cn lookup", {"hsg": "E", "land_cover": "forest"}) == (
            "hydrolog cn lookup --hsg E --land-cover forest"
        )
        assert format_command("hydrograph generate", {"area_km2": 2, "cn": 150}) == (
            "hydrolog hydrograph generate --area-km2 2 --cn 150"
        )
        assert format_command("tc kirpich", {"length_km": -1}) == (
            "hydrolog tc kirpich --length-km=-1"
        )

    @pytest.mark.parametrize(
        ("command", "options", "option", "reason"),
        [
            ("tc kirpich", {"length_km": "8.2"}, "length_km", "type"),
            ("tc kirpich", {"length_km": True}, "length_km", "type"),
            ("tc kirpich", {"length_km": float("nan")}, "length_km", "not_finite"),
            ("cn lookup", {"hsg": 3}, "hsg", "type"),
            ("cn weighted", {"parts": {"cn": 55}}, "parts", "type"),
            ("report generate", {"watershed_name": " "}, "watershed_name", "empty"),
        ],
    )
    def test_a_value_of_another_type_is_refused(self, command, options, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            format_command(command, options)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_an_unknown_option_is_refused_with_the_allowed_ones(self):
        with pytest.raises(InvalidParameterError) as caught:
            format_command("tc kirpich", {"length": 8.2})
        assert caught.value.details["reason"] == "unknown_option"
        assert caught.value.details["allowed"] == ["length_km", "slope_m_per_m"]

    @pytest.mark.parametrize(
        ("run", "option", "reason"),
        [
            ({"check": True}, "check", "unknown_option"),
            ({"lang": "de"}, "lang", "choice"),
            ({"json": "yes"}, "json", "type"),
            ({"quiet": 1}, "quiet", "type"),
        ],
    )
    def test_wrong_run_flags_are_refused(self, run, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            format_command("cn list", {}, run)
        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason

    def test_options_and_run_flags_must_be_mappings(self):
        with pytest.raises(InvalidParameterError) as options:
            format_command("cn list", ["limit", 3])  # type: ignore[arg-type]
        with pytest.raises(InvalidParameterError) as run:
            format_command("cn list", {}, ["json"])  # type: ignore[arg-type]
        assert options.value.details["option"] == "options"
        assert run.value.details["option"] == "run"

    def test_an_unknown_command_is_not_found_with_suggestions(self):
        with pytest.raises(NotFoundError) as caught:
            format_command("tc kirpic", {})
        assert "tc kirpich" in caught.value.details["suggestions"]


class TestParseCommand:
    """A line is read as the command line reads it."""

    def test_a_line_gives_its_command_options_and_run_flags(self):
        parsed = parse_command(
            "hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json"
        )
        assert parsed.command == "tc kirpich"
        assert parsed.options == {"length_km": 8.2, "slope_m_per_m": 0.023}
        assert parsed.run == {"json": True}

    def test_general_flags_may_stand_before_the_group_or_after_the_command(self):
        parsed = parse_command("hydrolog --json -v tc kirpich --length-km 2 --lang=en")
        assert parsed.run == {"json": True, "lang": "en", "verbose": True}
        assert parsed.options == {"length_km": 2.0}

    def test_the_program_name_is_optional_and_a_line_may_be_words(self):
        expected = ("cn list", {}, {})
        assert parse_command(["cn", "list"]) == expected
        assert parse_command("hydrolog cn list") == expected
        assert parse_command("cn list") == expected

    def test_a_later_value_wins_and_a_value_may_follow_an_equals_sign(self):
        parsed = parse_command(
            "hydrolog tc kirpich --length-km=8.2 --length-km 9 --slope-m-per-m=0.01"
        )
        assert parsed.options == {"length_km": 9.0, "slope_m_per_m": 0.01}

    def test_any_line_reads_back_into_its_canonical_form(self):
        line = "hydrolog --json tc kirpich --slope-m-per-m=0.023 --length-km 8.20 -q"
        assert format_command(*parse_command(line)) == (
            "hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json --quiet"
        )

    def test_a_negative_value_is_read_after_its_flag(self):
        parsed = parse_command("hydrolog tc kirpich --length-km -2")
        assert parsed.options == {"length_km": -2.0}
        assert format_command(*parsed) == "hydrolog tc kirpich --length-km=-2"

    @pytest.mark.parametrize("flag", ["--help", "-h", "--version", "-V", "--schema"])
    def test_a_description_is_not_a_call(self, flag):
        with pytest.raises(UsageError) as caught:
            parse_command(f"hydrolog tc kirpich --length-km 2 {flag}")
        assert caught.value.details["option"] == flag
        assert caught.value.details["reason"] == "usage"

    def test_a_group_alone_is_refused_with_its_commands(self):
        with pytest.raises(UsageError) as caught:
            parse_command("hydrolog tc")
        assert "tc kirpich" in caught.value.details["allowed"]

    @pytest.mark.parametrize("line", ["hydrolog tx kirpich", "hydrolog tc kirpic"])
    def test_an_unknown_group_or_command_is_not_found(self, line):
        with pytest.raises(NotFoundError):
            parse_command(line)

    @pytest.mark.parametrize(
        "line", ["", "hydrolog", "hydrolog --json", "hydrolog mcp --allow-dir ."]
    )
    def test_a_line_without_a_catalog_command_is_refused(self, line):
        with pytest.raises(UsageError):
            parse_command(line)

    def test_a_line_that_is_no_shell_line_is_refused(self):
        with pytest.raises(UsageError) as caught:
            parse_command("hydrolog report generate --watershed-name 'Kamiennik")
        assert caught.value.details["reason"] == "usage"

    def test_an_unknown_flag_is_a_usage_error_with_a_suggestion(self):
        with pytest.raises(UsageError) as caught:
            parse_command("hydrolog tc kirpich --length 8")
        assert caught.value.details["reason"] == "unknown_option"
        assert "--length-km" in caught.value.hint

    def test_a_value_of_the_wrong_syntax_is_a_type_error(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_command("hydrolog tc kirpich --length-km eight")
        assert not isinstance(caught.value, UsageError)
        assert caught.value.details["reason"] == "type"

    def test_an_unknown_language_is_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_command("hydrolog cn list --lang de")
        assert caught.value.details["reason"] == "choice"

    def test_a_line_must_be_text_or_words(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_command(5)  # type: ignore[arg-type]
        assert caught.value.details["reason"] == "type"
