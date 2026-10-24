"""Tests for the catalog-generated command line (``hydrolog.cli.main``)."""

import importlib
import io
import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import hydrolog
from hydrolog.catalog import (
    catalog_document,
    command_schema,
    data_commands,
    run_command,
)
from hydrolog.catalog.spec import Command
from hydrolog.cli import main as exported_main
from hydrolog.cli.main import main
from hydrolog.cli.parser import format_example
from hydrolog.exceptions import (
    CalculationError,
    ForbiddenPathError,
    MissingDependencyError,
)

# `hydrolog.cli.main` is also the name of the re-exported function; the module is here.
CLI_MAIN = importlib.import_module("hydrolog.cli.main")
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
KIRPICH = ["tc", "kirpich", "--length-km", "8.2", "--slope-m-per-m", "0.023"]
GUIDE = ["commands", "guide", "--format", "llms"]


def _command(name: str) -> Command:
    return next(command for command in data_commands() if command.name == name)


@pytest.fixture(autouse=True)
def _stable_environment(monkeypatch):
    """A fixed terminal width (the settings are isolated by ``conftest``)."""
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
    assert len(lines) == 1, "with --json stderr holds only the error document"
    return code, json.loads(lines[0])


def _readable_error(capsys, *argv):
    """Run without ``--json``; return (exit code, readable lines, error document)."""
    code, out, err = _run(capsys, *argv)
    assert out == ""
    *readable, last = err.splitlines()
    return code, readable, json.loads(last)


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
    """Help is generated from the catalog, in Polish or English (AGI-3.7)."""

    def test_no_arguments_print_the_root_help(self, capsys):
        code, out, err = _run(capsys)
        assert code == 0 and err == ""
        assert out.startswith("Hydrolog: obliczenia hydrologiczne")
        assert "\nużycie: hydrolog" in out

    def test_root_help_lists_every_group_and_command(self, capsys):
        code, out, _ = _run(capsys, "--help")
        assert code == 0
        for command in data_commands():
            assert f"  {command.group} " in out
            assert command.subcommand in out
        assert "  mcp " in out

    def test_help_in_english(self, capsys):
        _, out, _ = _run(capsys, "--lang", "en", "--help")
        assert out.startswith("Hydrolog: hydrological calculations")
        assert "\nusage: hydrolog" in out
        assert "command groups:" in out

    def test_language_from_the_environment(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _, out, _ = _run(capsys, "--help")
        assert "\nusage: hydrolog" in out

    def test_group_help_lists_its_commands_with_summaries(self, capsys):
        _, out, _ = _run(capsys, "stats", "--help", "--lang", "en")
        for command in data_commands():
            if command.group == "stats":
                assert command.subcommand in out
                assert " ".join(command.summary.split()[:3]) in out
        assert "hydrometrics" not in out
        assert out.splitlines()[0].endswith("stats of the Hydrolog catalog.")

    def test_language_may_precede_the_help_flag_in_equals_form(self, capsys):
        _, out, _ = _run(capsys, "--lang=en", "--help")
        assert "\nusage: hydrolog" in out

    def test_a_group_without_a_command_prints_its_help(self, capsys):
        code, out, _ = _run(capsys, "stats")
        assert code == 0
        assert out == _run(capsys, "stats", "--help")[1]

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_command_help_starts_with_what_the_command_does(self, capsys, lang):
        for name in ("tc kirpich", "scs effective", "report generate"):
            command = _command(name)
            _, out, _ = _run(capsys, *name.split(), "--help", "--lang", lang)
            lines = out.splitlines()
            assert lines[0] == command.summarize(lang)
            assert lines[1] == ""
            assert lines[2].startswith(("użycie: hydrolog", "usage: hydrolog"))

    def test_command_help_documents_the_options(self, capsys):
        code, out, _ = _run(capsys, "tc", "kirpich", "--help")
        assert code == 0
        assert "użycie: hydrolog tc kirpich --length-km NUMBER" in out
        assert "opcje wymagane:" in out
        assert "--slope-m-per-m NUMBER" in out
        assert "--json" in out and "--schema" in out and "--lang {pl,en}" in out
        assert "-v, --verbose" in out and "-q, --quiet" in out
        assert "[-o" not in out and "-o," not in out, "there is no short -o option"

    def test_command_help_in_english_uses_the_english_texts(self, capsys):
        _, out, _ = _run(capsys, "tc", "kirpich", "--help", "--lang", "en")
        assert out.startswith("Compute time of concentration with the Kirpich")
        assert "required options:" in out

    def test_help_is_the_same_before_and_after_the_command(self, capsys):
        after = _run(capsys, "tc", "kirpich", "--help")
        before = _run(capsys, "--help", "tc", "kirpich")
        assert after == before

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_help_lists_enum_values_with_their_meanings(self, capsys, lang):
        command = _command("scs effective")
        option = command.option("amc")
        meanings = option.meanings_pl if lang == "pl" else option.meanings
        _, out, _ = _run(capsys, "scs", "effective", "--help", "--lang", lang)
        assert "--amc {I,II,III}" in out
        block = out[out.index("  --amc:\n") :]
        for value in option.choices:
            line = next(item for item in block.splitlines() if f"  {value} " in item)
            assert meanings[value].split()[0] in line

    @pytest.mark.parametrize("lang", ["pl", "en"])
    def test_help_ends_with_the_examples(self, capsys, lang):
        for name in ("scs effective", "stats mann-kendall", "commands guide"):
            command = _command(name)
            _, out, _ = _run(capsys, *name.split(), "--help", "--lang", lang)
            lines = out.rstrip("\n").splitlines()
            expected = [format_example(command, item) for item in command.examples]
            assert [line.strip() for line in lines[-len(expected) :]] == expected
            assert lines[-len(expected) - 1] == (
                "Przykłady:" if lang == "pl" else "Examples:"
            )

    def test_help_shows_defaults_and_boolean_pairs(self, capsys):
        _, out, _ = _run(capsys, "hydrometrics", "rating-curve", "--help")
        assert "--remove-outliers, --no-remove-outliers" in out
        assert "(domyślnie: nie)" in out

    def test_writing_commands_offer_check_and_force(self, capsys):
        _, out, _ = _run(capsys, "commands", "guide", "--help", "--lang", "en")
        assert "--output PATH" in out
        assert "--force, --no-force" in out
        assert "--check, --no-check" in out

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
        assert lines[0] == f"tc kirpich: {_command('tc kirpich').summary_pl}"
        assert "Wejście:" in lines and "Wynik:" in lines
        assert "  length_km:     8.2 km" in lines
        assert any(line.startswith("  tc_min:") and "85.9733" in line for line in lines)
        assert not any(line.startswith("  schema:") for line in lines)

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

    def test_commands_list_pages_through_the_catalog(self, capsys):
        names: list[str] = []
        argv = ["commands", "list", "--limit", "10", "--json"]
        while True:
            _, document = _json_run(capsys, *argv)
            names += [entry["name"] for entry in document["result"]["commands"]]
            cursor = document["page"]["next_cursor"]
            if not cursor:
                break
            argv = ["commands", "list", "--limit", "10", "--cursor", cursor, "--json"]
        assert names == [command.name for command in data_commands()]

    def test_commands_list_summary_is_a_table_with_the_page(self, capsys):
        _, out, _ = _run(capsys, "commands", "list", "--limit", "3")
        lines = out.splitlines()
        assert lines[1].split()[:2] == ["komenda", "opis"]
        assert lines[3].split()[:2] == [
            data_commands()[0].group,
            data_commands()[0].subcommand,
        ]
        assert lines[-2] == f"Pokazano 3 z {len(data_commands())}."
        assert lines[-1].startswith("Następna strona: --cursor ")

    def test_commands_schema_describes_one_command(self, capsys):
        _, document = _json_run(
            capsys, "commands", "schema", "--command", "hydrolog_tc_kirpich", "--json"
        )
        assert document["result"]["commands"][0]["name"] == "tc kirpich"
        _, out, _ = _run(
            capsys, "--lang", "en", "commands", "schema", "--command", "tc kirpich"
        )
        assert out.startswith("tc kirpich (hydrolog_tc_kirpich): ")
        assert "  length_km " in out


class TestOutputFiles:
    """``--output``, ``--force`` and ``--check`` with real files (AGI-3.4)."""

    def test_the_file_is_written_and_listed(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        code, out, err = _run(capsys, *GUIDE, "--output", str(target))
        assert (code, err) == (0, "")
        assert target.read_text(encoding="utf-8").startswith("# Hydrolog")
        assert f"Pliki:\n  {target}  (zapisano," in out

    def test_json_lists_the_written_file_in_the_result(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        _, document = _json_run(capsys, *GUIDE, "--output", str(target), "--json")
        (record,) = document["result"]["files"]
        assert record["path"] == str(target)
        assert record["status"] == "written"
        assert record["size_bytes"] == target.stat().st_size
        assert document["check"] is False and "files" not in document

    def test_an_existing_file_is_a_conflict_and_stays_untouched(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        code, readable, document = _readable_error(
            capsys, *GUIDE, "--output", str(target)
        )
        assert code == 4
        assert document["code"] == "conflict"
        assert document["details"] == {
            "reason": "output_exists",
            "paths": [str(target)],
        }
        assert document["command"] == "commands guide"
        assert readable[0] == "Błąd (conflict): Konflikt stanu"
        assert str(target) in "\n".join(readable)
        assert "--force" in readable[-1]
        assert target.read_text(encoding="utf-8") == "mine"

    def test_the_conflict_explanation_follows_the_language(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        code, readable, document = _readable_error(
            capsys, *GUIDE, "--output", str(target), "--lang", "en"
        )
        assert code == 4
        assert readable[0] == "Error (conflict): State conflict"
        assert "already exists" in readable[1]
        assert document["title"] == "State conflict"

    def test_force_replaces_the_file(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        _, document = _json_run(
            capsys, *GUIDE, "--output", str(target), "--force", "--json"
        )
        assert document["result"]["files"][0]["status"] == "replaced"
        assert target.read_text(encoding="utf-8").startswith("# Hydrolog")

    def test_check_plans_a_new_file_and_writes_nothing(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        _, document = _json_run(
            capsys, *GUIDE, "--output", str(target), "--check", "--json"
        )
        assert document["check"] is True
        assert document["result"] == {
            "schema": "hydrolog-plan/1",
            "targets": [{"option": "output", "path": str(target), "action": "write"}],
        }
        assert not target.exists()

    def test_check_with_a_conflict_is_still_a_success(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        code, document = _json_run(
            capsys, *GUIDE, "--output", str(target), "--check", "--json"
        )
        assert code == 0
        (entry,) = document["result"]["targets"]
        assert (entry["action"], entry["reason"]) == ("conflict", "output_exists")
        assert target.read_text(encoding="utf-8") == "mine"

    def test_check_with_force_plans_a_replacement(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        _, document = _json_run(
            capsys, *GUIDE, "--output", str(target), "--check", "--force", "--json"
        )
        assert document["result"]["targets"][0]["action"] == "replace"
        assert target.read_text(encoding="utf-8") == "mine"

    def test_the_plan_is_readable_and_says_nothing_was_written(self, capsys, tmp_path):
        target = tmp_path / "llms.txt"
        target.write_text("mine", encoding="utf-8")
        code, out, err = _run(
            capsys, *GUIDE, "--output", str(target), "--check", "--lang", "en"
        )
        assert (code, err) == (0, "")
        lines = out.splitlines()
        assert lines[1] == "Plan (--check): nothing was written."
        assert any(line.startswith("conflict  output  ") for line in lines)
        assert lines[-1].startswith("Running without --check would fail")

    def test_without_a_target_the_guide_text_is_printed(self, capsys):
        code, out, err = _run(capsys, *GUIDE)
        assert (code, err) == (0, "")
        assert out.startswith("# Hydrolog")

    def test_a_read_only_command_has_no_check_option(self, capsys):
        code, document = _error(capsys, *KIRPICH, "--check")
        assert code == 2
        assert document["details"]["reason"] == "unknown_option"

    def test_an_unwritable_output_is_an_io_error(self, capsys, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed", encoding="utf-8")
        code, document = _error(capsys, *GUIDE, "--output", str(blocker / "llms.txt"))
        assert code == 9
        assert document["code"] == "io_error"

    def test_raster_output_is_listed(self, capsys, tmp_path):
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
            "--output",
            str(target),
        )
        assert code == 0
        assert target.is_file()
        assert f"Pliki:\n  {target}" in out


class TestLanguage:
    """``--lang``, the settings and machine output (AGI-9.2)."""

    def test_machine_output_is_english_whatever_the_language(self, capsys):
        english = _command("commands list").summary
        for argv in (["--lang", "pl"], ["--lang", "en"], []):
            _, document = _json_run(capsys, "commands", "list", *argv, "--json")
            assert document["result"]["commands"][0]["summary"] == (
                data_commands()[0].summary
            )
            assert "inputs" in document and "lang" not in document["inputs"]
        assert english

    def test_default_is_polish(self, capsys):
        _, out, _ = _run(capsys, "commands", "list")
        assert out.startswith(f"commands list: {_command('commands list').summary_pl}")

    def test_lang_flag_selects_english(self, capsys):
        _, out, _ = _run(capsys, "commands", "list", "--lang", "en")
        assert out.startswith(f"commands list: {_command('commands list').summary}")
        assert out.splitlines()[1].split()[:2] == ["command", "summary"]

    def test_lang_flag_before_the_command(self, capsys):
        before = _run(capsys, "--lang", "en", "commands", "list")
        after = _run(capsys, "commands", "list", "--lang", "en")
        assert before == after

    def test_lang_equals_form(self, capsys):
        _, out, _ = _run(capsys, "commands", "list", "--lang=en")
        assert "Input" not in out and out.splitlines()[1].startswith("command")

    @pytest.mark.parametrize("variable", ["HYDROLOG_LANG", "NOGAT_LANG"])
    def test_environment_selects_the_language(self, capsys, monkeypatch, variable):
        monkeypatch.setenv(variable, "en")
        _, out, _ = _run(capsys, *KIRPICH)
        assert "Input:" in out and "Result:" in out

    def test_the_tool_variable_wins_over_the_shared_one(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "pl")
        monkeypatch.setenv("NOGAT_LANG", "en")
        _, out, _ = _run(capsys, *KIRPICH)
        assert "Wejście:" in out

    def test_the_settings_file_selects_the_language(
        self, capsys, monkeypatch, tmp_path
    ):
        settings = tmp_path / "nogat.toml"
        settings.write_text('[nogat]\nlang = "en"\n', encoding="utf-8")
        monkeypatch.setenv("NOGAT_CONFIG", str(settings))
        _, out, _ = _run(capsys, *KIRPICH)
        assert "Input:" in out
        settings.write_text(
            '[nogat]\nlang = "en"\n[hydrolog]\nlang = "pl"\n', encoding="utf-8"
        )
        _, out, _ = _run(capsys, *KIRPICH)
        assert "Wejście:" in out

    def test_flag_wins_over_the_environment(self, capsys, monkeypatch):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        _, out, _ = _run(capsys, *KIRPICH, "--lang", "pl")
        assert "Wejście:" in out

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("EN", "Input:"),
            ("en_US.UTF-8", "Input:"),
            ("pl_PL.UTF-8", "Wejście:"),
            ("de", "Wejście:"),
            ("", "Wejście:"),
        ],
    )
    def test_environment_is_read_leniently(self, capsys, monkeypatch, value, expected):
        monkeypatch.setenv("HYDROLOG_LANG", value)
        _, out, _ = _run(capsys, *KIRPICH)
        assert expected in out.splitlines()

    def test_config_show_reports_where_the_language_comes_from(
        self, capsys, monkeypatch
    ):
        monkeypatch.setenv("NOGAT_LANG", "en")
        _, document = _json_run(capsys, "config", "show", "--json")
        setting = next(
            item for item in document["result"]["settings"] if item["key"] == "lang"
        )
        assert (setting["value"], setting["source"]) == ("en", "environment")
        assert setting["detail"] == "NOGAT_LANG"
        assert document["result"]["credentials"] == []
        assert document["result"]["store"] is None

    def test_config_show_summary(self, capsys, tmp_path):
        code, out, err = _run(capsys, "config", "show", "--lang", "en")
        assert (code, err) == (0, "")
        lines = out.splitlines()
        assert lines[1].split() == ["setting", "value", "source"]
        assert any(line.startswith("lang") and "default" in line for line in lines)
        assert f"Settings file: {tmp_path / 'absent.toml'} (no such file)" in lines
        assert lines[-2:] == ["Credentials: n/a", "Data store: n/a"]

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

    def test_the_error_document_is_english_the_explanation_follows_the_language(
        self, capsys
    ):
        _, polish, polish_document = _readable_error(capsys, "tc", "kirpich")
        _, english, english_document = _readable_error(
            capsys, "tc", "kirpich", "--lang", "en"
        )
        assert polish[0] == "Błąd (validation_error): Nieprawidłowe dane wejściowe"
        assert english[0] == "Error (validation_error): Invalid input"
        assert polish_document == english_document
        assert polish_document["title"] == "Invalid input"


class TestSchema:
    """``--schema`` prints the command description and runs nothing."""

    def test_command_schema(self, capsys):
        code, out, err = _run(capsys, "tc", "kirpich", "--schema")
        assert code == 0 and err == ""
        assert json.loads(out) == command_schema("tc kirpich").to_dict()

    def test_schema_needs_no_options_and_in_any_position(self, capsys):
        expected = command_schema("tc kirpich").to_dict()
        for argv in (
            ["--schema", "tc", "kirpich"],
            ["tc", "--schema", "kirpich"],
            ["tc", "kirpich", "--schema", "--json"],
        ):
            code, out, _ = _run(capsys, *argv)
            assert code == 0
            assert json.loads(out) == expected

    def test_schema_is_english_with_the_polish_texts_inside(self, capsys):
        _, out, _ = _run(capsys, "tc", "kirpich", "--schema", "--lang", "pl")
        document = json.loads(out)
        assert document["schema"] == "hydrolog-commands/1"
        entry = document["commands"][0]
        assert entry["operation_id"] == "hydrolog_tc_kirpich"
        assert entry["summary"] == _command("tc kirpich").summary
        assert entry["i18n"]["pl"]["summary"] == _command("tc kirpich").summary_pl

    def test_group_schema_has_only_its_commands(self, capsys):
        _, out, _ = _run(capsys, "tc", "--schema")
        names = [entry["name"] for entry in json.loads(out)["commands"]]
        assert names == [c.name for c in data_commands() if c.group == "tc"]

    def test_catalog_schema(self, capsys):
        _, out, _ = _run(capsys, "--schema")
        assert json.loads(out) == catalog_document(data_commands())

    def test_schema_does_not_run_the_command(self, capsys, tmp_path):
        target = tmp_path / "never.txt"
        code, out, _ = _run(capsys, *GUIDE, "--output", str(target), "--schema")
        assert code == 0
        assert json.loads(out)["commands"][0]["name"] == "commands guide"
        assert not target.exists()


class TestErrors:
    """Exit codes and error documents (AGI-3.3)."""

    def test_unknown_group_suggests_a_group(self, capsys):
        code, document = _error(capsys, "tcc", "kirpich")
        assert code == 3
        assert document["schema"] == "hydrolog-error/1"
        assert document["code"] == "not_found"
        assert document["details"]["suggestions"] == ["tc"]
        assert "command" not in document

    def test_operation_id_is_not_a_command_but_is_suggested(self, capsys):
        code, document = _error(capsys, "hydrolog_tc_kirpich")
        assert code == 3
        assert document["details"]["suggestions"] == ["tc kirpich"]

    def test_a_mistyped_operation_id_suggests_the_command(self, capsys):
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

    def test_the_removed_output_path_option_is_unknown(self, capsys):
        code, document = _error(capsys, *GUIDE, "--output-path", "x.txt")
        assert code == 2
        assert "Did you mean --output?" in document["hint"]

    def test_there_is_no_short_o_option(self, capsys):
        code, document = _error(capsys, *GUIDE, "-o", "x.txt")
        assert code == 2
        assert document["details"]["reason"] in ("unknown_option", "usage")

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

    def test_a_forbidden_path_has_its_own_exit_code(self, capsys, monkeypatch):
        def refused(*args, **kwargs):
            raise ForbiddenPathError(
                "Path is outside the allowed directories",
                details={"option": "output", "path": "/etc/x"},
            )

        monkeypatch.setattr(CLI_MAIN, "run_command", refused)
        code, document = _error(capsys, *KIRPICH)
        assert code == 12
        assert document["code"] == "forbidden"

    def test_a_bug_is_an_internal_error(self, capsys, monkeypatch):
        def broken(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(CLI_MAIN, "run_command", broken)
        code, document = _error(capsys, *KIRPICH)
        assert code == 1
        assert document["code"] == "internal_error"
        assert document["details"] == {"exception": "RuntimeError"}
        assert document["command"] == "tc kirpich"

    @pytest.mark.parametrize("flag", [[], ["--json"]])
    def test_the_last_line_of_stderr_is_the_error_document(self, capsys, flag):
        code, out, err = _run(capsys, "tc", "kirpich", "--length-km", "8.2", *flag)
        assert code == 2 and out == ""
        document = json.loads(err.splitlines()[-1])
        assert document["schema"] == "hydrolog-error/1"
        assert document["exit_code"] == code
        assert err.endswith("\n") and "\n" not in err.splitlines()[-1]

    def test_readable_error_comes_before_the_document(self, capsys):
        code, readable, document = _readable_error(
            capsys, "tc", "kirpich", "--length-km", "8.2"
        )
        assert code == 2
        assert readable == [
            "Błąd (validation_error): Nieprawidłowe dane wejściowe",
            "  Option 'slope_m_per_m' is required by command 'tc kirpich'",
            "Podpowiedź: Give 'slope_m_per_m' (CLI: --slope-m-per-m); "
            "'commands schema' lists all options.",
        ]
        assert document["code"] == "validation_error"

    def test_with_json_stderr_holds_only_the_document(self, capsys):
        code, out, err = _run(capsys, "tc", "kirpich", "--length-km", "8.2", "--json")
        assert code == 2 and out == ""
        assert len(err.splitlines()) == 1

    def test_json_flag_anywhere_selects_the_json_only_error(self, capsys):
        # --json after a broken option: the error has no readable part.
        code, out, err = _run(capsys, "tc", "kirpich", "--bogus", "--json")
        assert code == 2 and out == ""
        assert json.loads(err)["code"] == "validation_error"

    def test_a_usage_error_is_reported_like_the_others(self, capsys):
        code, readable, document = _readable_error(capsys, "tc", "kirpich", "--bogus")
        assert code == 2
        assert readable[0].startswith("Błąd (validation_error)")
        assert document["details"]["reason"] == "unknown_option"

    def test_ctrl_c_is_an_outcome_without_an_error_document(self, capsys, monkeypatch):
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(CLI_MAIN, "run_command", interrupted)
        code, out, err = _run(capsys, *KIRPICH)
        assert code == 130 and out == ""
        assert err == "Przerwano.\n"
        code, out, err = _run(capsys, *KIRPICH, "--json", "--lang", "en")
        assert (code, out, err) == (130, "", "Interrupted.\n")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
class TestSigterm:
    """``SIGTERM`` ends the command with the registry code ``terminated``."""

    @staticmethod
    def _terminate(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGTERM)
        raise AssertionError("the handler should have raised")

    def test_the_signal_becomes_the_terminated_error(self, capsys, monkeypatch):
        monkeypatch.setattr(CLI_MAIN, "run_command", self._terminate)
        code, readable, document = _readable_error(capsys, *KIRPICH)
        assert code == 143
        assert document["code"] == "terminated"
        assert document["exit_code"] == 143
        assert document["command"] == "tc kirpich"
        assert readable[0] == "Błąd (terminated): Przerwano"

    def test_with_json_only_the_document_is_printed(self, capsys, monkeypatch):
        monkeypatch.setattr(CLI_MAIN, "run_command", self._terminate)
        code, document = _error(capsys, *KIRPICH)
        assert (code, document["code"]) == (143, "terminated")

    def test_the_previous_handler_is_restored(self, capsys, monkeypatch):
        def previous(signum, frame):
            raise AssertionError("not called")

        monkeypatch.setattr(CLI_MAIN, "run_command", self._terminate)
        old = signal.signal(signal.SIGTERM, previous)
        try:
            assert _run(capsys, *KIRPICH, "--json")[0] == 143
            assert signal.getsignal(signal.SIGTERM) is previous
            assert _run(capsys, "--version")[0] == 0
            assert signal.getsignal(signal.SIGTERM) is previous
        finally:
            signal.signal(signal.SIGTERM, old)

    def test_a_real_process_exits_with_143(self):
        code = (
            "import os, signal, sys\n"
            "import importlib\n"
            "m = importlib.import_module('hydrolog.cli.main')\n"
            "def run(*a, **k):\n"
            "    os.kill(os.getpid(), signal.SIGTERM)\n"
            "m.run_command = run\n"
            "sys.exit(m.main(['tc', 'kirpich', '--length-km', '1', "
            "'--slope-m-per-m', '0.1']))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 143
        assert result.stdout == ""
        assert json.loads(result.stderr.splitlines()[-1])["code"] == "terminated"


class TestLogging:
    """``-v``, ``-q`` and ``HYDROLOG_LOG_LEVEL`` set the log on stderr (DEV-12.2)."""

    @staticmethod
    def _noisy(monkeypatch):
        """Make the operation log at every level."""

        def run(command, options=None):
            logger = logging.getLogger("hydrolog.test_noise")
            logger.debug("a debug note")
            logger.info("an info note")
            logger.warning("a warning note")
            logger.error("an error note")
            return run_command(command, options)

        monkeypatch.setattr(CLI_MAIN, "run_command", run)

    def test_default_shows_warnings_and_errors(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        code, out, err = _run(capsys, *KIRPICH, "--json")
        assert code == 0
        assert json.loads(out)["command"] == "tc kirpich"
        assert "WARNING hydrolog.test_noise: a warning note" in err
        assert "ERROR hydrolog.test_noise: an error note" in err
        assert "an info note" not in err and "a debug note" not in err

    def test_verbose_shows_debug(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        code, out, err = _run(capsys, *KIRPICH, "--json", "-v")
        assert code == 0
        assert out.count("\n") == 1, "logs never reach stdout"
        assert "DEBUG hydrolog.test_noise: a debug note" in err
        assert "DEBUG hydrolog.cli.main: Running tc kirpich" in err

    def test_verbose_flag_may_come_before_the_command(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        _, _, err = _run(capsys, "--verbose", *KIRPICH)
        assert "a debug note" in err

    def test_quiet_shows_errors_only(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        _, _, err = _run(capsys, *KIRPICH, "--quiet")
        assert "an error note" in err
        assert "a warning note" not in err

    def test_the_environment_sets_the_level(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        monkeypatch.setenv("HYDROLOG_LOG_LEVEL", "info")
        _, _, err = _run(capsys, *KIRPICH)
        assert "an info note" in err and "a debug note" not in err

    def test_the_flags_win_over_the_environment(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        monkeypatch.setenv("HYDROLOG_LOG_LEVEL", "debug")
        _, _, err = _run(capsys, *KIRPICH, "-q")
        assert "a debug note" not in err and "a warning note" not in err

    def test_the_settings_file_sets_the_level(self, capsys, monkeypatch, tmp_path):
        self._noisy(monkeypatch)
        settings = tmp_path / "nogat.toml"
        settings.write_text('[hydrolog]\nlog_level = "error"\n', encoding="utf-8")
        monkeypatch.setenv("NOGAT_CONFIG", str(settings))
        _, _, err = _run(capsys, *KIRPICH)
        assert "a warning note" not in err and "an error note" in err

    def test_an_invalid_level_in_the_environment_is_ignored(self, capsys, monkeypatch):
        self._noisy(monkeypatch)
        monkeypatch.setenv("HYDROLOG_LOG_LEVEL", "loud")
        _, _, err = _run(capsys, *KIRPICH)
        assert "a warning note" in err and "an info note" not in err

    def test_verbose_and_quiet_exclude_each_other(self, capsys):
        code, document = _error(capsys, *KIRPICH, "-v", "-q")
        assert code == 2
        assert document["details"]["reason"] == "exclusive_options"

    def test_the_error_document_stays_the_last_line_with_logs(self, capsys):
        code, out, err = _run(capsys, "tc", "kirpich", "--length-km", "8.2", "-v")
        assert code == 2 and out == ""
        lines = err.splitlines()
        assert json.loads(lines[-1])["code"] == "validation_error"
        assert any("DEBUG hydrolog.cli.main: The command failed" in x for x in lines)

    def test_the_logger_is_left_as_it_was(self, capsys, monkeypatch):
        logger = logging.getLogger("hydrolog")
        handlers, level = list(logger.handlers), logger.level
        self._noisy(monkeypatch)
        _run(capsys, *KIRPICH, "-v")
        _run(capsys, "tc", "kirpich", "-q")  # an error
        assert logger.handlers == handlers and logger.level == level

    def test_nothing_is_logged_by_help_and_schema(self, capsys):
        for argv in (["--help"], ["tc", "kirpich", "--schema", "-v"], ["-V"]):
            _, _, err = _run(capsys, *argv)
            assert err == ""


class TestStreams:
    """Output encoding and closed pipes."""

    def test_unencodable_summary_is_degraded_not_fatal(self, monkeypatch):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", write_through=True)
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "list"]) == 0
        text = stdout.buffer.getvalue().decode("ascii")
        assert text.startswith("commands list: ")
        assert "?" in text

    def test_unencodable_json_is_escaped_and_lossless(self, monkeypatch):
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", write_through=True)
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "schema", "--command", "tc kirpich", "--json"]) == 0
        raw = stdout.buffer.getvalue().decode("ascii")
        assert "\\u" in raw
        expected = run_command("commands schema", {"command": "tc kirpich"})
        assert json.loads(raw) == expected.to_dict()

    def test_a_stream_without_an_encoding_keeps_the_text(self, monkeypatch):
        stdout = io.StringIO()
        monkeypatch.setattr(sys, "stdout", stdout)
        assert main(["commands", "schema", "--command", "tc kirpich", "--json"]) == 0
        raw = stdout.getvalue()
        assert "ł" in raw and "\\u" not in raw

    def test_closed_pipe_ends_quietly(self, monkeypatch, capsys):
        class ClosedPipe(io.StringIO):
            def write(self, text):
                raise BrokenPipeError

        monkeypatch.setattr(sys, "stdout", ClosedPipe())
        assert main(["commands", "list"]) == 0
        assert capsys.readouterr().err == ""


@pytest.fixture
def mcp_stub(monkeypatch):
    """Replace the server of ``hydrolog.mcp.server``; record how it is started."""
    server = pytest.importorskip("hydrolog.mcp.server")
    calls = []

    def run_stdio(*, allowed_dirs=(), allow_writes=False, families=None):
        calls.append(
            {
                "allowed_dirs": list(allowed_dirs),
                "allow_writes": allow_writes,
                "families": None if families is None else list(families),
            }
        )

    monkeypatch.setattr(server, "run_stdio", run_stdio)
    return calls


class TestMcp:
    """``hydrolog mcp`` starts the server; it is not a catalog command."""

    def test_starts_the_server_with_defaults(self, capsys, mcp_stub):
        assert _run(capsys, "mcp") == (0, "", "")
        assert mcp_stub == [
            {"allowed_dirs": [], "allow_writes": False, "families": None}
        ]

    def test_server_options_reach_the_server(self, capsys, mcp_stub):
        argv = ["mcp", "--allow-dir", "a", "--allow-dir", "b", "--allow-writes"]
        assert _run(capsys, *argv, "--tools", "core,stats") == (0, "", "")
        assert mcp_stub == [
            {
                "allowed_dirs": ["a", "b"],
                "allow_writes": True,
                "families": ["core", "stats"],
            }
        ]

    def test_help_flag_before_the_word(self, capsys, mcp_stub):
        code, out, _ = _run(capsys, "--help", "mcp")
        assert code == 0
        assert "--allow-dir DIR" in out
        assert mcp_stub == []

    def test_help_starts_with_what_the_command_does(self, capsys, mcp_stub):
        code, out, _ = _run(capsys, "mcp", "--help", "--lang", "en")
        assert code == 0
        assert out.splitlines()[0].startswith("Starts the MCP")
        assert "--allow-writes" in out and "--tools" in out
        assert mcp_stub == []

    def test_unknown_argument(self, capsys, mcp_stub):
        code, document = _error(capsys, "mcp", "--bogus")
        assert code == 2
        assert mcp_stub == []

    @pytest.mark.parametrize(
        "argv", [("mcp", "--lang", "en"), ("--lang", "pl", "mcp"), ("mcp", "--lang=en")]
    )
    def test_an_explicit_lang_is_refused_because_the_server_is_english(
        self, capsys, mcp_stub, argv
    ):
        code, document = _error(capsys, *argv)
        assert code == 2
        assert document["code"] == "validation_error"
        assert document["details"]["reason"] == "ineffective_option"
        assert document["details"]["option"] == "--lang"
        assert mcp_stub == []

    def test_the_language_setting_of_the_environment_does_not_matter(
        self, capsys, mcp_stub, monkeypatch
    ):
        monkeypatch.setenv("HYDROLOG_LANG", "en")
        assert _run(capsys, "mcp") == (0, "", "")
        assert len(mcp_stub) == 1

    def test_missing_extra_is_a_missing_dependency(self, capsys, monkeypatch):
        server = pytest.importorskip("hydrolog.mcp.server")

        def run_stdio(**kwargs):
            raise MissingDependencyError(
                "The MCP server needs the 'mcp' package",
                hint="pip install hydrolog[mcp]",
            )

        monkeypatch.setattr(server, "run_stdio", run_stdio)
        code, readable, document = _readable_error(capsys, "mcp")
        assert code == 6
        assert document["code"] == "missing_dependency"
        assert document["hint"] == "pip install hydrolog[mcp]"
        assert readable[0].startswith("Błąd (missing_dependency)")

    def test_real_server_module_reports_a_missing_sdk(self, capsys, monkeypatch):
        # A None entry makes an import fail like an uninstalled package; the SDK
        # modules may be cached by other tests, so every one of them is blocked.
        for name in ("mcp", "mcp.server", "mcp_types", "anyio"):
            monkeypatch.setitem(sys.modules, name, None)
        monkeypatch.delitem(sys.modules, "hydrolog.mcp.server", raising=False)
        code, out, err = _run(capsys, "mcp")
        assert code == 6 and out == ""
        assert json.loads(err.splitlines()[-1])["code"] == "missing_dependency"
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

    def test_the_last_stderr_line_is_the_document_without_json_too(self):
        result = self._python("tc", "kirpich", "--length-km", "8.2")
        assert result.returncode == 2
        assert result.stdout == ""
        assert json.loads(result.stderr.splitlines()[-1])["exit_code"] == 2
        assert len(result.stderr.splitlines()) > 1

    def test_calculation_error_exit_status(self):
        result = self._python("stats", "mann-kendall", "--values", "1,2", "--json")
        assert result.returncode == 13


def test_calculation_errors_keep_their_class_through_the_cli(capsys, monkeypatch):
    def failing(*args, **kwargs):
        raise CalculationError("no result", details={"reason": "degenerate"})

    monkeypatch.setattr(CLI_MAIN, "run_command", failing)
    code, document = _error(capsys, *KIRPICH)
    assert (code, document["code"]) == (13, "calculation_error")
    assert document["details"] == {"reason": "degenerate"}
