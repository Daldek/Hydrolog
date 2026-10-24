"""Tests for the catalog-generated command line (``hydrolog.cli.main``)."""

import importlib
import io
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

import hydrolog
from hydrolog.catalog import command_schema, data_commands, run_command
from hydrolog.cli import main as exported_main
from hydrolog.cli.main import main
from hydrolog.exceptions import MissingDependencyError

# `hydrolog.cli.main` is also the name of the re-exported function; the module is here.
CLI_MAIN = importlib.import_module("hydrolog.cli.main")
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
KIRPICH = ["tc", "kirpich", "--length-km", "8.2", "--slope-m-per-m", "0.023"]


@pytest.fixture(autouse=True)
def _stable_environment(monkeypatch):
    """No language from the environment, a fixed terminal width."""
    monkeypatch.delenv("HYDROLOG_LANG", raising=False)
    monkeypatch.setenv("COLUMNS", "100")


def _run(capsys, *argv):
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _json_run(capsys, *argv):
    code, out, err = _run(capsys, *argv)
    assert err == ""
    return code, json.loads(out)


def _error(capsys, *argv):
    """Run with ``--json`` and return (exit code, error document)."""
    code, out, err = _run(capsys, "--json", *argv)
    assert out == ""
    lines = err.splitlines()
    assert len(lines) == 1, "an error is exactly one JSON line"
    return code, json.loads(lines[0])


class TestEntryPoint:
    """``main`` is the console-script entry and keeps its old import path."""

    def test_package_exports_main(self):
        assert exported_main is main

    def test_version(self, capsys):
        assert _run(capsys, "--version") == (
            0,
            f"hydrolog {hydrolog.__version__}\n",
            "",
        )

    def test_version_is_available_after_the_command_too(self, capsys):
        assert _run(capsys, *KIRPICH, "--version")[:2] == (
            0,
            f"hydrolog {hydrolog.__version__}\n",
        )

    def test_short_version_flag(self, capsys):
        assert _run(capsys, "-V") == (0, f"hydrolog {hydrolog.__version__}\n", "")


class TestHelp:
    """Help is generated from the catalog, in Polish or English."""

    def test_no_arguments_print_the_root_help(self, capsys):
        code, out, err = _run(capsys)
        assert code == 0 and err == ""
        assert out.startswith("użycie: hydrolog")

    def test_root_help_lists_every_group_and_command(self, capsys):
        code, out, _ = _run(capsys, "--help")
        assert code == 0
        for command in data_commands():
            assert f"  {command.group} " in out
            assert command.subcommand in out
        assert "  mcp " in out

    def test_help_in_english(self, capsys):
        _, out, _ = _run(capsys, "--lang", "en", "--help")
        assert out.startswith("usage: hydrolog")
        assert "command groups:" in out

    def test_language_from_the_environment(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _, out, _ = _run(capsys, "--help")
        assert out.startswith("usage: hydrolog")

    def test_group_help_lists_its_commands_with_summaries(self, capsys):
        _, out, _ = _run(capsys, "stats", "--help")
        for command in data_commands():
            if command.group == "stats":
                assert command.subcommand in out
                assert " ".join(command.summary.split()[:3]) in out
        assert "hydrometrics" not in out

    def test_language_may_precede_the_help_flag_in_equals_form(self, capsys):
        _, out, _ = _run(capsys, "--lang=en", "--help")
        assert out.startswith("usage: hydrolog")

    def test_a_group_without_a_command_prints_its_help(self, capsys):
        code, out, _ = _run(capsys, "stats")
        assert code == 0
        assert out == _run(capsys, "stats", "--help")[1]

    def test_command_help_documents_the_options(self, capsys):
        code, out, _ = _run(capsys, "tc", "kirpich", "--help")
        assert code == 0
        assert out.startswith("użycie: hydrolog tc kirpich --length-km NUMBER")
        assert "opcje wymagane:" in out
        assert "--slope-m-per-m NUMBER" in out
        assert "--json" in out and "--schema" in out and "--lang {pl,en}" in out
        assert "hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023" in out
        # Summary and description come from the catalog.
        assert "Czas koncentracji wzorem Kirpicha" in out

    def test_command_help_in_english_uses_the_english_texts(self, capsys):
        _, out, _ = _run(capsys, "tc", "kirpich", "--help", "--lang", "en")
        assert out.startswith("usage: hydrolog tc kirpich")
        assert "required options:" in out
        assert "Time of concentration by the Kirpich formula" in out

    def test_help_is_the_same_before_and_after_the_command(self, capsys):
        after = _run(capsys, "tc", "kirpich", "--help")
        before = _run(capsys, "--help", "tc", "kirpich")
        assert after == before

    def test_help_shows_choices_defaults_and_boolean_pairs(self, capsys):
        _, out, _ = _run(capsys, "scs", "effective", "--help")
        assert "--amc {I,II,III}" in out
        assert "(domyślnie: II)" in out
        _, out, _ = _run(capsys, "hydrometrics", "rating-curve", "--help")
        assert "--remove-outliers, --no-remove-outliers" in out
        assert "(domyślnie: nie)" in out

    def test_help_explains_one_of_groups(self, capsys):
        _, out, _ = _run(capsys, "stats", "mann-kendall", "--help", "--lang", "en")
        assert "(--values N1,N2,... | --input-file PATH --value-column TEXT)" in out
        assert "Exactly one of these option groups is required:" in out

    def test_percent_signs_in_texts_do_not_break_the_help(self, capsys):
        # `uh nash` has options with the unit "%".
        code, out, _ = _run(capsys, "uh", "nash", "--help")
        assert code == 0
        assert "[%]" in out


class TestRunning:
    """Running a command: summary, JSON, option syntax."""

    def test_human_summary(self, capsys):
        code, out, err = _run(capsys, *KIRPICH)
        assert code == 0 and err == ""
        lines = out.splitlines()
        assert lines[0].startswith("tc kirpich: Czas koncentracji wzorem Kirpicha")
        assert "Wejście:" in lines and "Wynik:" in lines
        assert "  length_km:     8.2 km" in lines
        assert any(line.startswith("  tc_min:") and "85.9733" in line for line in lines)

    def test_json_is_the_envelope_on_one_line(self, capsys):
        code, out, err = _run(capsys, *KIRPICH, "--json")
        assert code == 0 and err == ""
        assert out.count("\n") == 1
        expected = run_command(
            "tc kirpich", {"length_km": 8.2, "slope_m_per_m": 0.023}
        ).to_dict()
        assert json.loads(out) == expected
        assert expected["schema"] == "hydrolog-result/1"

    @pytest.mark.parametrize(
        "argv",
        [
            ["--json", *KIRPICH],
            [
                "tc",
                "--json",
                "kirpich",
                "--length-km",
                "8.2",
                "--slope-m-per-m",
                "0.023",
            ],
            [*KIRPICH, "--json"],
            [
                "tc",
                "kirpich",
                "--json",
                "--length-km",
                "8.2",
                "--slope-m-per-m",
                "0.023",
            ],
        ],
    )
    def test_general_flags_are_accepted_everywhere(self, capsys, argv):
        code, document = _json_run(capsys, *argv)
        assert code == 0
        assert document["command"] == "tc kirpich"

    def test_equals_form(self, capsys):
        _, equals = _json_run(
            capsys,
            "tc",
            "kirpich",
            "--length-km=8.2",
            "--slope-m-per-m=0.023",
            "--json",
        )
        _, spaced = _json_run(capsys, *KIRPICH, "--json")
        assert equals == spaced

    def test_number_list_and_negative_values(self, capsys):
        values = [-5, -3, -4, -1, 0, 2, 1, 3, 4, 6]
        _, document = _json_run(
            capsys,
            "stats",
            "mann-kendall",
            "--values",
            ",".join(map(str, values)),
            "--alpha",
            "1e-2",
            "--json",
        )
        expected = run_command("stats mann-kendall", {"values": values, "alpha": 0.01})
        assert document == expected.to_dict()
        assert document["inputs"]["values"][0] == -5.0

    @pytest.mark.parametrize("flag", ["--h0-initial", "--h0-initial="])
    def test_negative_number_after_a_flag(self, capsys, flag):
        levels = ["62", "88", "115", "142", "170", "200", "235", "270"]
        flows = ["1.05", "3.4", "6.32", "10.48", "15.7", "20.5", "26.63", "34.92"]
        base = [
            "hydrometrics",
            "rating-curve",
            "--water-levels",
            ",".join(levels),
            "--discharges",
            ",".join(flows),
        ]
        tail = [flag + "-5"] if flag.endswith("=") else [flag, "-5"]
        _, document = _json_run(capsys, *base, *tail, "--json")
        assert document["inputs"]["h0_initial"] == -5.0

    def test_boolean_flag_and_its_negation(self, capsys):
        base = [
            "hydrometrics",
            "rating-curve",
            "--input-file",
            str(FIXTURES / "rating_curve_pairs.csv"),
        ]
        base += ["--level-column", "H", "--discharge-column", "Q", "--h0-initial", "40"]
        _, default = _json_run(capsys, *base, "--json")
        _, enabled = _json_run(capsys, *base, "--remove-outliers", "--json")
        _, disabled = _json_run(
            capsys, *base, "--remove-outliers", "--no-remove-outliers", "--json"
        )
        assert default["inputs"]["remove_outliers"] is False
        assert enabled["inputs"]["remove_outliers"] is True
        assert disabled["inputs"]["remove_outliers"] is False

    def test_json_text_options(self, capsys):
        parts = [{"cn": 55, "area": 27.2}, {"cn": 69, "area": 13.6}]
        _, document = _json_run(
            capsys, "cn", "weighted", "--parts", json.dumps(parts), "--json"
        )
        assert document == run_command("cn weighted", {"parts": parts}).to_dict()

    def test_object_option_with_non_ascii_text(self, capsys):
        watershed = {
            "name": "Młynówka",
            "area_km2": 12.0,
            "perimeter_km": 18.0,
            "length_km": 6.0,
            "elevation_min_m": 200.0,
            "elevation_max_m": 420.0,
            "cn": 70,
        }
        _, document = _json_run(
            capsys,
            "tc",
            "watershed",
            "--watershed",
            json.dumps(watershed, ensure_ascii=False),
            "--json",
        )
        assert document["result"]["watershed_name"] == "Młynówka"

    def test_defaults_are_applied_like_in_python(self, capsys):
        _, document = _json_run(
            capsys,
            "scs",
            "effective",
            "--cn",
            "72",
            "--precipitation-mm",
            "50",
            "--json",
        )
        assert document["inputs"]["amc"] == "II"
        assert document["inputs"]["ia_coefficient"] == 0.2

    def test_relative_paths_are_resolved_against_the_working_directory(
        self, capsys, monkeypatch
    ):
        monkeypatch.chdir(REPO_ROOT)
        _, document = _json_run(
            capsys,
            "stats",
            "mann-kendall",
            "--input-file",
            "tests/fixtures/annual_maxima.csv",
            "--value-column",
            "Qmax",
            "--json",
        )
        assert document["inputs"]["input_file"] == str(FIXTURES / "annual_maxima.csv")

    def test_notices_are_part_of_the_summary(self, capsys):
        code, out, _ = _run(
            capsys,
            "stats",
            "low-flow",
            "--input-file",
            str(FIXTURES / "daily_flows_3y.csv"),
            "--value-column",
            "Q",
            "--date-column",
            "date",
        )
        assert code == 0
        assert "Uwagi:" in out and "[ostrzeżenie]" in out

    def test_written_files_are_listed(self, capsys, tmp_path):
        pytest.importorskip("rasterio")
        target = tmp_path / "hsg.tif"
        code, out, _ = _run(
            capsys,
            "soil",
            "hsg",
            "--clay-path",
            str(FIXTURES / "hsg_clay.tif"),
            "--sand-path",
            str(FIXTURES / "hsg_sand.tif"),
            "--silt-path",
            str(FIXTURES / "hsg_silt.tif"),
            "--output-path",
            str(target),
        )
        assert code == 0
        assert target.is_file()
        assert f"Pliki:\n  {target}" in out


class TestLanguage:
    """``--lang``, ``HYDROLOG_LANG`` and the ``lang`` option of a command."""

    def test_default_is_polish(self, capsys):
        _, document = _json_run(capsys, "commands", "list", "--json")
        assert document["inputs"] == {"lang": "pl"}
        assert document["result"][0]["summary"] == data_commands()[0].summary

    def test_lang_flag_is_the_lang_option(self, capsys):
        _, document = _json_run(capsys, "commands", "list", "--lang", "en", "--json")
        assert document["inputs"] == {"lang": "en"}
        assert document["result"][0]["summary"] == data_commands()[0].summary_en

    def test_lang_flag_before_the_command(self, capsys):
        _, before = _json_run(capsys, "--lang", "en", "commands", "list", "--json")
        _, after = _json_run(capsys, "commands", "list", "--lang", "en", "--json")
        assert before == after
        assert before["inputs"]["lang"] == "en"

    def test_lang_equals_form(self, capsys):
        _, document = _json_run(capsys, "commands", "list", "--lang=en", "--json")
        assert document["inputs"]["lang"] == "en"

    def test_environment_selects_the_language_of_the_result(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _, document = _json_run(capsys, "commands", "list", "--json")
        assert document["inputs"]["lang"] == "en"

    def test_flag_wins_over_the_environment(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _, document = _json_run(capsys, "commands", "list", "--lang", "pl", "--json")
        assert document["inputs"]["lang"] == "pl"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("EN", "en"),
            ("en_US.UTF-8", "en"),
            ("pl_PL.UTF-8", "pl"),
            ("de", "pl"),
            ("", "pl"),
        ],
    )
    def test_environment_is_read_leniently(self, capsys, monkeypatch, value, expected):
        monkeypatch.setenv("HYDROLOG_LANG", value)
        _, document = _json_run(capsys, "commands", "list", "--json")
        assert document["inputs"]["lang"] == expected

    def test_lang_applies_to_commands_without_a_lang_option(self, capsys):
        code, out, _ = _run(capsys, *KIRPICH, "--lang", "en")
        assert code == 0
        assert out.startswith("tc kirpich: Time of concentration by the Kirpich")
        assert "Input:" in out and "Result:" in out

    def test_invalid_lang_is_a_validation_error(self, capsys):
        code, document = _error(capsys, *KIRPICH, "--lang", "de")
        assert code == 2
        assert document["details"] == {
            "option": "lang",
            "reason": "choice",
            "allowed": ["pl", "en"],
            "value": "de",
        }

    def test_lang_without_a_value(self, capsys):
        code, document = _error(capsys, *KIRPICH, "--lang")
        assert code == 2
        assert document["details"]["reason"] == "usage"
        assert "--lang" in document["message"]

    def test_error_titles_follow_the_language(self, capsys):
        _, polish = _error(capsys, "tc", "kirpich")
        _, english = _error(capsys, "tc", "kirpich", "--lang", "en")
        assert polish["title"] == "Nieprawidłowe dane wejściowe"
        assert english["title"] == "Invalid input"
        assert polish["message"] == english["message"]


class TestSchema:
    """``--schema`` prints the option schema and runs nothing."""

    def test_command_schema(self, capsys):
        code, out, err = _run(capsys, "tc", "kirpich", "--schema")
        assert code == 0 and err == ""
        assert json.loads(out) == command_schema("tc kirpich")

    def test_schema_needs_no_options_and_in_any_position(self, capsys):
        expected = command_schema("tc kirpich")
        for argv in (
            ["--schema", "tc", "kirpich"],
            ["tc", "--schema", "kirpich"],
            ["tc", "kirpich", "--schema", "--json"],
        ):
            code, out, _ = _run(capsys, *argv)
            assert code == 0
            assert json.loads(out) == expected

    def test_schema_language(self, capsys):
        _, out, _ = _run(capsys, "tc", "kirpich", "--schema", "--lang", "en")
        document = json.loads(out)
        assert document == command_schema("tc kirpich", lang="en")
        assert document["lang"] == "en"

    def test_group_schema_has_only_its_commands(self, capsys):
        _, out, _ = _run(capsys, "tc", "--schema")
        names = [entry["name"] for entry in json.loads(out)["commands"]]
        assert names == [c.name for c in data_commands() if c.group == "tc"]

    def test_catalog_schema(self, capsys):
        _, out, _ = _run(capsys, "--schema")
        assert json.loads(out) == command_schema()

    def test_schema_does_not_run_the_command(self, capsys, tmp_path):
        target = tmp_path / "never.tif"
        code, out, _ = _run(
            capsys, "soil", "hsg", "--output-path", str(target), "--schema"
        )
        assert code == 0
        assert json.loads(out)["commands"][0]["name"] == "soil hsg"
        assert not target.exists()


class TestErrors:
    """Exit codes and error documents."""

    def test_unknown_group_suggests_a_group(self, capsys):
        code, document = _error(capsys, "tcc", "kirpich")
        assert code == 3
        assert document["schema"] == "hydrolog-error/1"
        assert document["code"] == "not_found"
        assert document["details"]["suggestions"] == ["tc"]
        assert "command" not in document

    def test_operation_id_is_not_a_command_but_is_suggested(self, capsys):
        code, document = _error(capsys, "tc_kirpich")
        assert code == 3
        assert "tc kirpich" in document["details"]["suggestions"]

    def test_unknown_command_suggests_commands_of_the_group(self, capsys):
        code, document = _error(capsys, "tc", "kirpish", "--length-km", "1")
        assert code == 3
        assert document["details"]["suggestions"][0] == "tc kirpich"
        assert "Did you mean: tc kirpich" in document["hint"]

    def test_unknown_option_suggests_the_kebab_spelling(self, capsys):
        code, document = _error(capsys, "tc", "kirpich", "--length_km", "8.2")
        assert code == 2
        assert document["command"] == "tc kirpich"
        assert document["details"]["reason"] == "unknown_option"
        assert document["details"]["option"] == "--length_km"
        assert "Did you mean --length-km?" in document["hint"]

    def test_leading_lang_without_a_value(self, capsys):
        code, document = _error(capsys, "--lang")
        assert code == 2
        assert document["details"]["reason"] == "usage"

    def test_unknown_option_before_the_command(self, capsys):
        code, document = _error(capsys, "--length-km", "5", "tc", "kirpich")
        assert code == 2
        assert "before the command" in document["message"]

    def test_unexpected_word(self, capsys):
        code, document = _error(capsys, *KIRPICH, "extra")
        assert code == 2
        assert document["details"]["reason"] == "unexpected_argument"

    def test_flag_without_its_value(self, capsys):
        code, document = _error(capsys, "tc", "kirpich", "--length-km")
        assert code == 2
        assert document["details"]["reason"] == "usage"
        assert "expected one argument" in document["message"]

    def test_missing_required_option_comes_from_the_catalog(self, capsys):
        code, document = _error(capsys, "tc", "kirpich", "--length-km", "8.2")
        assert code == 2
        assert document["details"] == {"option": "slope_m_per_m", "reason": "required"}
        assert "--slope-m-per-m" in document["hint"]

    def test_text_of_the_wrong_type(self, capsys):
        code, document = _error(
            capsys, "tc", "kirpich", "--length-km", "abc", "--slope-m-per-m", "0.02"
        )
        assert code == 2
        assert document["details"]["option"] == "length_km"
        assert document["details"]["reason"] == "type"
        assert document["command"] == "tc kirpich"

    def test_value_out_of_range_comes_from_the_catalog(self, capsys):
        code, document = _error(
            capsys, "tc", "kirpich", "--length-km", "-1", "--slope-m-per-m", "0.02"
        )
        assert code == 2
        assert document["details"]["reason"] == "exclusive_minimum"

    def test_value_not_among_the_choices(self, capsys):
        code, document = _error(
            capsys,
            "scs",
            "effective",
            "--cn",
            "72",
            "--precipitation-mm",
            "5",
            "--amc",
            "IV",
        )
        assert code == 2
        assert document["details"]["reason"] == "choice"
        assert document["details"]["allowed"] == ["I", "II", "III"]

    def test_one_of_violation(self, capsys):
        code, document = _error(capsys, "stats", "mann-kendall")
        assert code == 2
        assert document["details"]["reason"] == "one_of"

    def test_missing_input_file_is_not_found(self, capsys, tmp_path):
        code, document = _error(
            capsys,
            "stats",
            "mann-kendall",
            "--input-file",
            str(tmp_path / "no.csv"),
            "--value-column",
            "Q",
        )
        assert code == 3
        assert document["code"] == "not_found"

    def test_malformed_input_file_is_a_data_error(self, capsys, tmp_path):
        bad = tmp_path / "bad.csv"
        bad.write_text("a,b\n1,2\n", encoding="utf-8")
        code, document = _error(
            capsys,
            "stats",
            "mann-kendall",
            "--input-file",
            str(bad),
            "--value-column",
            "Q",
        )
        assert code == 7
        assert document["code"] == "data_error"

    def test_impossible_calculation(self, capsys):
        code, document = _error(capsys, "stats", "mann-kendall", "--values", "1,2")
        assert code == 13
        assert document["code"] == "calculation_error"

    def test_unwritable_output_is_an_io_error(self, capsys, tmp_path):
        pytest.importorskip("rasterio")
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed", encoding="utf-8")
        code, document = _error(
            capsys,
            "soil",
            "hsg",
            "--clay-path",
            str(FIXTURES / "hsg_clay.tif"),
            "--sand-path",
            str(FIXTURES / "hsg_sand.tif"),
            "--silt-path",
            str(FIXTURES / "hsg_silt.tif"),
            "--output-path",
            str(blocker / "hsg.tif"),
        )
        assert code == 9
        assert document["code"] == "io_error"

    def test_a_bug_is_an_internal_error(self, capsys, monkeypatch):
        def broken(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(CLI_MAIN, "run_command", broken)
        code, document = _error(capsys, *KIRPICH)
        assert code == 1
        assert document["code"] == "internal_error"
        assert document["details"] == {"exception": "RuntimeError"}
        assert document["command"] == "tc kirpich"

    def test_readable_error_without_json(self, capsys):
        code, out, err = _run(capsys, "tc", "kirpich", "--length-km", "8.2")
        assert code == 2 and out == ""
        assert err.splitlines() == [
            "Błąd (validation_error): Nieprawidłowe dane wejściowe",
            "  Option 'slope_m_per_m' is required by command 'tc kirpich'",
            "Podpowiedź: Give 'slope_m_per_m' (CLI: --slope-m-per-m); "
            "'commands schema' lists all options.",
        ]

    def test_json_flag_anywhere_selects_the_json_error(self, capsys):
        # --json after a broken option: the error is still reported as JSON.
        code, out, err = _run(capsys, "tc", "kirpich", "--bogus", "--json")
        assert code == 2 and out == ""
        assert json.loads(err)["code"] == "validation_error"

    def test_ctrl_c(self, capsys, monkeypatch):
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(CLI_MAIN, "run_command", interrupted)
        code, out, err = _run(capsys, *KIRPICH)
        assert code == 130 and out == ""
        assert err == "Przerwano.\n"


class TestStreams:
    """Output encoding and closed pipes."""

    def test_unencodable_summary_is_degraded_not_fatal(self, monkeypatch):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", write_through=True)
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "list"]) == 0
        text = stdout.buffer.getvalue().decode("ascii")
        assert text.startswith("commands list: Lista komend katalogu")
        assert "?" in text

    def test_unencodable_json_is_escaped_and_lossless(self, monkeypatch):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", write_through=True)
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "list", "--json"]) == 0
        raw = stdout.buffer.getvalue().decode("ascii")
        assert "\\u" in raw
        assert json.loads(raw) == run_command("commands list").to_dict()

    def test_a_stream_without_an_encoding_keeps_the_text(self, monkeypatch):
        stdout = io.StringIO()
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "list", "--json"]) == 0
        raw = stdout.getvalue()
        assert "ą" in raw and "\\u" not in raw

    def test_closed_pipe_ends_quietly(self, monkeypatch, capsys):
        class ClosedPipe(io.StringIO):
            def write(self, text):
                raise BrokenPipeError

        monkeypatch.setattr(sys, "stdout", ClosedPipe())
        assert main(["commands", "list"]) == 0
        assert capsys.readouterr().err == ""


@pytest.fixture
def mcp_stub(monkeypatch):
    """A stand-in for ``hydrolog.mcp`` that records how the server is started."""
    calls = []

    def run_stdio(*, allowed_dirs=(), lang="pl"):
        calls.append({"allowed_dirs": list(allowed_dirs), "lang": lang})

    module = types.ModuleType("hydrolog.mcp")
    module.run_stdio = run_stdio
    monkeypatch.setitem(sys.modules, "hydrolog.mcp", module)
    return calls


class TestMcp:
    """``hydrolog mcp`` starts the server; it is not a catalog command."""

    def test_starts_the_server_with_defaults(self, capsys, mcp_stub):
        assert _run(capsys, "mcp") == (0, "", "")
        assert mcp_stub == [{"allowed_dirs": [], "lang": "pl"}]

    def test_allowed_directories_are_resolved_and_repeatable(
        self, capsys, mcp_stub, tmp_path, monkeypatch
    ):
        (tmp_path / "data").mkdir()
        (tmp_path / "out").mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        code, out, err = _run(
            capsys, "mcp", "--allow-dir", "data", "--allow-dir", "~/out", "--lang", "en"
        )
        assert (code, out, err) == (0, "", "")
        assert mcp_stub == [
            {
                "allowed_dirs": [
                    (tmp_path / "data").resolve(),
                    (tmp_path / "out").resolve(),
                ],
                "lang": "en",
            }
        ]
        assert all(
            isinstance(path, Path) and path.is_absolute()
            for path in mcp_stub[0]["allowed_dirs"]
        )

    def test_language_from_the_environment_or_before_the_word(
        self, capsys, mcp_stub, monkeypatch
    ):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _run(capsys, "mcp")
        monkeypatch.delenv("HYDROLOG_LANG")
        _run(capsys, "--lang", "en", "mcp")
        _run(capsys, "--lang", "en", "mcp", "--lang", "pl")
        assert [call["lang"] for call in mcp_stub] == ["en", "en", "pl"]

    def test_help_flag_before_the_word(self, capsys, mcp_stub):
        code, out, _ = _run(capsys, "--help", "mcp")
        assert code == 0
        assert "--allow-dir DIR" in out
        assert mcp_stub == []

    def test_missing_directory_is_not_found(self, capsys, mcp_stub, tmp_path):
        code, document = _error(capsys, "mcp", "--allow-dir", str(tmp_path / "nope"))
        assert code == 3
        assert document["details"]["option"] == "allow_dir"
        assert mcp_stub == []

    def test_a_file_is_not_a_directory(self, capsys, mcp_stub, tmp_path):
        file = tmp_path / "file.txt"
        file.write_text("x", encoding="utf-8")
        code, document = _error(capsys, "mcp", "--allow-dir", str(file))
        assert code == 2
        assert document["details"]["reason"] == "not_a_directory"
        assert mcp_stub == []

    def test_unknown_argument(self, capsys, mcp_stub):
        code, document = _error(capsys, "mcp", "--bogus")
        assert code == 2
        assert mcp_stub == []

    def test_help(self, capsys, mcp_stub):
        code, out, _ = _run(capsys, "mcp", "--help")
        assert code == 0
        assert "--allow-dir DIR" in out
        assert mcp_stub == []

    def test_missing_extra_is_a_missing_dependency(self, capsys, monkeypatch):
        def run_stdio(*, allowed_dirs=(), lang="pl"):
            raise MissingDependencyError(
                "The MCP server needs the 'mcp' package",
                hint="pip install hydrolog[mcp]",
            )

        module = types.ModuleType("hydrolog.mcp")
        module.run_stdio = run_stdio
        monkeypatch.setitem(sys.modules, "hydrolog.mcp", module)
        code, document = _error(capsys, "mcp")
        assert code == 6
        assert document["code"] == "missing_dependency"
        assert document["hint"] == "pip install hydrolog[mcp]"

    def test_real_server_module_reports_a_missing_sdk(self, capsys, monkeypatch):
        # A None entry makes an import fail like an uninstalled package; the SDK
        # modules may be cached by other tests, so every one of them is blocked.
        for name in ("mcp", "mcp.server", "mcp_types", "anyio"):
            monkeypatch.setitem(sys.modules, name, None)
        code, out, err = _run(capsys, "mcp")
        assert code == 6 and out == ""
        assert "missing_dependency" in err
        assert "hydrolog[mcp]" in err


class TestModuleExecution:
    """The package runs as ``python -m hydrolog.cli`` and reports its status."""

    def _python(self, *argv):
        return subprocess.run(
            [sys.executable, "-m", "hydrolog.cli", *argv],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )

    def test_version(self):
        result = self._python("--version")
        assert result.returncode == 0
        assert result.stdout == f"hydrolog {hydrolog.__version__}\n"
        assert result.stderr == ""

    def test_exit_status_is_the_error_code(self):
        result = self._python("tc", "kirpich", "--length-km", "8.2", "--json")
        assert result.returncode == 2
        assert result.stdout == ""
        assert json.loads(result.stderr)["code"] == "validation_error"
