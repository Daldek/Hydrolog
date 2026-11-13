"""The batch and IMGW-PIB's half-years in frequency commands (plan 2026-11-13, S2)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from hydrolog import run_command as run
from hydrolog.catalog import get_command, run_command
from hydrolog.catalog.lines import option_arguments
from hydrolog.cli.main import main
from hydrolog.exceptions import (
    CalculationError,
    ConflictError,
    InputDataError,
    InvalidParameterError,
)
from hydrolog.statistics import fit_fisher_tippett_minima

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DAILY = "station_daily.csv"
HALF_YEARS = "station_half_years.csv"
# The winter and summer maxima and minima of Q in station_half_years.csv, 2019-2023.
Q_MAXIMA = [72.18, 132.13, 102.57, 41.19, 76.55]
Q_MINIMA = [0.54, 1.54, 1.48, 0.52, 0.99]


@pytest.fixture
def station(tmp_path: Path) -> Path:
    """A directory with the station's files, as Obserwator would write them."""
    for name in (DAILY, HALF_YEARS):
        shutil.copy(FIXTURES / name, tmp_path / name)
    return tmp_path


def write_calls(directory: Path, *lines: object) -> Path:
    """A JSON Lines file of calls; a ``str`` line is written as it is."""
    path = directory / "calls.jsonl"
    text = [line if isinstance(line, str) else json.dumps(line) for line in lines]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")
    return path


def call(command: str, **options: object) -> dict[str, object]:
    return {"command": command, "options": options}


def batch(calls: Path, **options: object) -> tuple[dict, list[dict]]:
    """Run a batch; its envelope and the documents of its output lines."""
    output = calls.parent / "results.jsonl"
    envelope = run_command(
        "commands batch",
        {"input_file": str(calls), "output": str(output), **options},
    ).to_dict()
    lines = output.read_text(encoding="utf-8").splitlines()
    return envelope, [json.loads(line) for line in lines]


class TestBatch:
    def test_each_line_is_what_the_command_line_prints_for_the_call_alone(
        self, station, monkeypatch, capsys
    ):
        calls = [
            call(
                "stats characteristic",
                input_file=DAILY,
                value_column="H",
                date_column="date",
                parameter="H",
            ),
            call("hydrolog_stats_low_flow", half_year_file=HALF_YEARS),
            call("stats flood-frequency", values=[1.0, 2.0]),  # calculation_error
            call(
                "stats threshold-events",
                input_file="missing.csv",
                value_column="Q",
                date_column="date",
                level=1,
            ),
        ]
        path = write_calls(station, *calls)
        monkeypatch.chdir(station)
        _, documents = batch(path)
        output = (station / "results.jsonl").read_text(encoding="utf-8").splitlines()

        for line, (text, item) in enumerate(zip(output, calls, strict=True), start=1):
            command = get_command(str(item["command"]))
            argv = [
                *command.name.split(),
                *option_arguments(command, item["options"]),
                "--json",
            ]
            code = main(argv)
            out, err = capsys.readouterr()
            alone = out if code == 0 else err.splitlines()[-1] + "\n"
            assert text + "\n" == alone, f"line {line}"
        assert [d["schema"] for d in documents] == [
            "hydrolog-result/1",
            "hydrolog-result/1",
            "hydrolog-error/1",
            "hydrolog-error/1",
        ]
        assert [d["code"] for d in documents[2:]] == ["calculation_error", "not_found"]

    def test_a_failed_call_does_not_stop_the_batch_and_makes_it_partial(self, station):
        path = write_calls(
            station,
            call("tc kirpich", length_km=8.2, slope_m_per_m=0.023),
            "not json",
            ["a", "list"],
            {"command": "tc kirpich"},
            call("tc nothing"),
            call("gui serve"),
            call("commands batch", input_file="calls.jsonl", output="x.jsonl"),
            call("tc kirpich", length_km=-1, slope_m_per_m=0.023),
            call("hydrolog_tc_kirpich", length_km=1.5, slope_m_per_m=0.01),
        )
        envelope, documents = batch(path)

        assert envelope["status"] == "partial"
        result = envelope["result"]
        assert (result["n_calls"], result["n_ok"], result["n_failed"]) == (9, 2, 7)
        assert result["failed"] == [
            {"line": 2, "command": None, "code": "validation_error"},
            {"line": 3, "command": None, "code": "validation_error"},
            {"line": 4, "command": "tc kirpich", "code": "validation_error"},
            {"line": 5, "command": "tc nothing", "code": "not_found"},
            {"line": 6, "command": "gui serve", "code": "validation_error"},
            {"line": 7, "command": "commands batch", "code": "validation_error"},
            {"line": 8, "command": "tc kirpich", "code": "validation_error"},
        ]
        reasons = [d["details"].get("reason") for d in documents[1:7]]
        assert reasons == [
            "invalid_call",
            "invalid_call",
            "invalid_call",
            None,
            "not_in_batch",
            "not_in_batch",
        ]
        assert documents[7]["details"]["option"] == "length_km"
        assert documents[8]["result"]["tc_min"] > 0
        assert [item["status"] for item in envelope["items"]] == [
            "ok",
            *["failed"] * 7,
            "ok",
        ]
        assert envelope["items"][4] == {
            "id": 5,
            "status": "failed",
            "code": "not_found",
            "message": documents[4]["message"],
        }

    def test_the_command_line_prints_the_envelope_and_exits_with_the_outcome(
        self, station, capsys
    ):
        partial = write_calls(
            station, call("tc kirpich", length_km=8.2, slope_m_per_m=0.023), "{}"
        )
        output = station / "results.jsonl"
        argv = ["commands", "batch", "--input-file", str(partial), "--json"]

        assert main([*argv, "--output", str(output)]) == 10
        out, err = capsys.readouterr()
        assert (json.loads(out)["status"], err) == ("partial", "")

        write_calls(station, "{}", "[]")  # the same file, now without a good call
        assert main([*argv, "--output", str(output), "--force"]) == 11
        out, err = capsys.readouterr()
        assert (json.loads(out)["status"], err) == ("failed", "")

    def test_relative_paths_are_taken_from_the_directory_of_the_calls(
        self, station, tmp_path_factory, monkeypatch
    ):
        path = write_calls(station, call("stats low-flow", half_year_file=HALF_YEARS))
        monkeypatch.chdir(tmp_path_factory.mktemp("elsewhere"))
        envelope, documents = batch(path)

        assert envelope["status"] == "ok"
        assert documents[0]["inputs"]["half_year_file"] == str(station / HALF_YEARS)

    def test_the_path_policy_of_the_batch_covers_every_call(
        self, station, tmp_path_factory
    ):
        outside = tmp_path_factory.mktemp("outside") / HALF_YEARS
        shutil.copy(station / HALF_YEARS, outside)
        path = write_calls(
            station,
            call("stats low-flow", half_year_file=HALF_YEARS),
            call("stats low-flow", half_year_file=str(outside)),
        )
        envelope = run_command(
            "commands batch",
            {"input_file": str(path), "output": str(station / "results.jsonl")},
            allowed_dirs=[station],
        ).to_dict()
        assert envelope["result"]["failed"] == [
            {"line": 2, "command": "stats low-flow", "code": "forbidden"}
        ]

    def test_check_plans_the_output_and_runs_nothing(self, station):
        path = write_calls(station, call("tc kirpich", length_km=1, slope_m_per_m=0.01))
        envelope = run_command(
            "commands batch",
            {
                "input_file": str(path),
                "output": str(station / "r.jsonl"),
                "check": True,
            },
        ).to_dict()
        assert envelope["result"]["targets"][0]["action"] == "write"
        assert "items" not in envelope
        assert not (station / "r.jsonl").exists()

    def test_the_file_errors_of_the_batch_itself(self, station):
        empty = station / "empty.jsonl"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(InputDataError) as caught:
            batch(empty)
        assert caught.value.details["reason"] == "empty"

        path = write_calls(station, call("tc kirpich", length_km=1, slope_m_per_m=0.01))
        with pytest.raises(InvalidParameterError) as same:
            run_command(
                "commands batch", {"input_file": str(path), "output": str(path)}
            )
        assert same.value.details["reason"] == "conflict"

        batch(path)
        with pytest.raises(ConflictError):
            batch(path)
        assert batch(path, force=True)[0]["result"]["files"][0]["status"] == "replaced"


class TestHalfYearsInTheFrequencyCommands:
    def test_flood_frequency_fits_the_larger_half_year_maxima(self, station):
        half = run(
            "stats flood-frequency", half_year_file=str(station / HALF_YEARS)
        ).to_dict()["result"]
        given = run("stats flood-frequency", values=Q_MAXIMA).to_dict()["result"]

        assert half["source"] == "half_years" and given["source"] == "values"
        assert half["annual_maxima"] == Q_MAXIMA
        assert half["hydrological_years"] == [2019, 2020, 2021, 2022, 2023]
        assert half["incomplete_years"] == []
        assert half["distributions"] == given["distributions"]

    def test_a_year_with_one_half_year_is_left_out_and_named(self, station):
        path = station / HALF_YEARS
        rows = path.read_text(encoding="utf-8").splitlines()
        header = rows[0].split(",")
        column = header.index("Q_max [m3/s]")
        cells = rows[5].split(",")  # 2020, summer
        assert cells[1:3] == ["2020", "summer"]
        cells[column] = ""
        rows[5] = ",".join(cells)
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

        result = run("stats flood-frequency", half_year_file=str(path)).to_dict()
        assert result["result"]["hydrological_years"] == [2019, 2021, 2022, 2023]
        assert result["result"]["incomplete_years"] == [2020]
        # the minima of 2020 are both there
        low = run("stats low-flow", half_year_file=str(path)).to_dict()
        assert low["result"]["n_years"] == 5

    def test_low_flow_fits_the_smaller_half_year_minima(self, station):
        envelope = run(
            "stats low-flow",
            half_year_file=str(station / HALF_YEARS),
            return_periods=[2, 10],
        ).to_dict()
        result = envelope["result"]
        with pytest.warns(UserWarning, match="fewer than 10"):
            fitted = fit_fisher_tippett_minima(np.array(Q_MINIMA), np.array([2.0, 10]))

        assert (result["source"], result["annual_minima"]) == ("half_years", Q_MINIMA)
        assert result["fisher_tippett"]["quantiles"] == pytest.approx(
            fitted.quantiles.tolist(), rel=1e-12
        )
        assert result["empirical"]["values_ascending"] == sorted(Q_MINIMA)
        assert [n["code"] for n in envelope["notices"]] == ["small_sample"]

    def test_homogeneity_takes_the_years_of_the_file(self, station):
        result = run(
            "stats homogeneity",
            half_year_file=str(station / HALF_YEARS),
            split_year=2021,
        ).to_dict()["result"]
        given = run(
            "stats homogeneity",
            values=Q_MAXIMA,
            years=[2019, 2020, 2021, 2022, 2023],
            split_year=2021,
        ).to_dict()["result"]

        assert (result["source"], result["hydrological_years"]) == (
            "half_years",
            [2019, 2020, 2021, 2022, 2023],
        )
        assert (given["source"], given["hydrological_years"]) == ("values", None)
        for test in ("mann_whitney", "kolmogorov_smirnov", "pettitt"):
            assert result[test] == given[test]

    def test_the_period_chooses_the_years_of_a_daily_series_or_the_file(self, station):
        half = run(
            "stats flood-frequency",
            half_year_file=str(station / HALF_YEARS),
            first_year=2020,
            last_year=2022,
        ).to_dict()["result"]
        assert half["hydrological_years"] == [2020, 2021, 2022]

        # The daily series' complete years are 2019, 2020 and 2023 (days are missing in
        # 2021 and 2022): from 2020 on two are left.
        options = {"input_file": str(station / DAILY), "value_column": "Q"}
        daily = run("stats homogeneity", **options, date_column="date").to_dict()
        assert daily["result"]["hydrological_years"] == [2019, 2020, 2023]
        with pytest.raises(CalculationError) as short:
            run("stats homogeneity", **options, date_column="date", first_year=2020)
        assert short.value.details["count"] == 2

    def test_a_period_needs_years_and_the_sources_exclude_each_other(self, station):
        with pytest.raises(InvalidParameterError) as caught:
            run("stats flood-frequency", values=Q_MAXIMA, first_year=2020)
        assert caught.value.details == {
            "option": "first_year",
            "reason": "not_applicable",
        }
        with pytest.raises(InvalidParameterError) as both:
            run(
                "stats low-flow",
                half_year_file=str(station / HALF_YEARS),
                dates=["2020-01-01"],
            )
        assert both.value.details["reason"] == "conflict"
        with pytest.raises(CalculationError) as empty:
            run(
                "stats flood-frequency",
                half_year_file=str(station / HALF_YEARS),
                first_year=2030,
            )
        assert empty.value.details["reason"] == "no_values_in_period"
