"""Tests for the conversion of command-line text into JSON-native option values."""

import math
from typing import Any

import pytest

from hydrolog.catalog import Option, validate_command
from hydrolog.cli.values import parse_option_value
from hydrolog.exceptions import InvalidParameterError


def _option(kind: Any, **kwargs: Any) -> Option:
    if kind == "choice":
        kwargs.setdefault("choices", ("a", "b"))
    return Option("value", kind, "Wartość", "Value", **kwargs)


class TestNumbers:
    """``number`` and ``integer`` text."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("8.2", 8.2),
            ("-1e-3", -0.001),
            ("+5", 5.0),
            (".5", 0.5),
            ("5.", 5.0),
            ("  7  ", 7.0),
            ("1E3", 1000.0),
        ],
    )
    def test_number_syntax(self, text, expected):
        assert parse_option_value(_option("number"), text) == expected

    @pytest.mark.parametrize("text", ["nan", "-inf", "Infinity"])
    def test_non_finite_text_parses_and_is_refused_by_the_catalog(self, text):
        value = parse_option_value(_option("number"), text)
        assert not math.isfinite(value)

    @pytest.mark.parametrize("text", ["", "abc", "1,5", "1 2", "0x10", "1_000", "--5"])
    def test_malformed_number_is_a_type_error_with_details(self, text):
        option = _option("number")
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(option, text)
        error = caught.value
        assert error.code == "validation_error"
        assert error.details == {
            "option": "value",
            "reason": "type",
            "expected": "number",
            "value": text,
        }
        assert "dot" in (error.hint or "")

    def test_integer_syntax_and_catalog_agree_on_fractions(self):
        option = _option("integer")
        assert parse_option_value(option, "5") == 5
        assert isinstance(parse_option_value(option, "-12"), int)
        # "1e3" and "5.0" are passed on; the catalog accepts a whole float ...
        assert option.normalize(parse_option_value(option, "1e3")) == 1000
        assert option.normalize(parse_option_value(option, "5.0")) == 5
        # ... and refuses a fraction exactly as it does for JSON input.
        with pytest.raises(InvalidParameterError) as caught:
            option.normalize(parse_option_value(option, "2.5"))
        assert caught.value.details["reason"] == "type"

    def test_malformed_integer(self):
        with pytest.raises(InvalidParameterError, match="expected integer"):
            parse_option_value(_option("integer"), "five")

    def test_long_offending_text_is_shortened_in_details(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option("number"), "x" * 500)
        shown = caught.value.details["value"]
        assert len(shown) == 200 and shown.endswith("…")


class TestTextTypes:
    """``string``, ``choice`` and ``path`` stay as given."""

    @pytest.mark.parametrize("kind", ["string", "choice", "path"])
    def test_text_is_unchanged(self, kind):
        assert parse_option_value(_option(kind), " a b ") == " a b "

    def test_validation_stays_with_the_catalog(self):
        # The CLI only converts; the choice list is checked by validate_command.
        option = _option("choice")
        assert parse_option_value(option, "zzz") == "zzz"
        with pytest.raises(InvalidParameterError) as caught:
            option.normalize("zzz")
        assert caught.value.details["reason"] == "choice"


class TestBoolean:
    """The flags carry no text: booleans arrive as ``bool``."""

    @pytest.mark.parametrize("flag", [True, False])
    def test_boolean_passes_through(self, flag):
        assert parse_option_value(_option("boolean"), flag) is flag


class TestLists:
    """Comma-separated lists and JSON arrays."""

    def test_number_list(self):
        option = _option("number_list")
        assert parse_option_value(option, "1.5, 2,3") == [1.5, 2.0, 3.0]
        assert parse_option_value(option, "-1,2") == [-1.0, 2.0]
        assert parse_option_value(option, "7") == [7.0]

    def test_number_list_from_json_array(self):
        assert parse_option_value(_option("number_list"), " [1, 2.5]") == [1, 2.5]

    @pytest.mark.parametrize(
        ("text", "index"), [("1,,3", 1), ("1,2,", 2), (",1", 0), ("1,x,3", 1)]
    )
    def test_bad_item_names_its_position(self, text, index):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option("number_list"), text)
        details = caught.value.details
        assert details["option"] == "value"
        assert details["reason"] == "type"
        assert details["expected"] == "number"
        assert details["index"] == index
        assert f"value[{index}]" in str(caught.value)

    def test_empty_text_is_one_empty_item(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option("number_list"), "")
        assert caught.value.details["index"] == 0

    def test_string_list(self):
        option = _option("string_list")
        assert parse_option_value(option, "2020-01-01, 2020-01-02") == [
            "2020-01-01",
            "2020-01-02",
        ]

    def test_string_list_item_with_a_comma_needs_json(self):
        option = _option("string_list")
        assert parse_option_value(option, '["a,b", "c"]') == ["a,b", "c"]

    def test_string_list_empty_item(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option("string_list"), "a,,b")
        assert caught.value.details["index"] == 1

    def test_broken_json_array(self):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option("number_list"), "[1, 2")
        assert caught.value.details["reason"] == "type"
        assert caught.value.details["expected"] == "array of numbers"
        assert "invalid JSON" in str(caught.value)


class TestJson:
    """``object`` and ``object_list`` are JSON text."""

    def test_object(self):
        value = parse_option_value(_option("object"), '{"name": "Młynówka", "cn": 72}')
        assert value == {"name": "Młynówka", "cn": 72}

    def test_object_list(self):
        text = '[{"cn": 55, "area": 27.2}, {"cn": 69, "area": 13.6}]'
        assert parse_option_value(_option("object_list"), text) == [
            {"cn": 55, "area": 27.2},
            {"cn": 69, "area": 13.6},
        ]

    @pytest.mark.parametrize("kind", ["object", "object_list"])
    def test_invalid_json(self, kind):
        with pytest.raises(InvalidParameterError) as caught:
            parse_option_value(_option(kind), "{not json")
        details = caught.value.details
        assert details["reason"] == "type"
        assert details["option"] == "value"
        assert "invalid JSON" in str(caught.value)
        assert "JSON" in (caught.value.hint or "")

    def test_wrong_json_shape_is_left_to_the_catalog(self):
        option = _option("object")
        value = parse_option_value(option, "[1, 2]")
        with pytest.raises(InvalidParameterError) as caught:
            option.normalize(value)
        assert caught.value.details["reason"] == "type"


def test_parsed_values_validate_like_json_input():
    """Text -> value -> catalog gives the same result as the JSON value."""
    from hydrolog.catalog import get_command

    command = get_command("stats mann-kendall")
    parsed = {
        "values": parse_option_value(command.option("values"), "1, 2, 3.5, 2"),
        "alpha": parse_option_value(command.option("alpha"), "1e-2"),
    }
    assert validate_command(command, parsed) == validate_command(
        command, {"values": [1, 2, 3.5, 2], "alpha": 0.01}
    )
