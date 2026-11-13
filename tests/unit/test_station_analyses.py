"""Station analyses of plan 2026-11-13 (S1): hand-computed series for each method."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import run_command
from hydrolog.exceptions import CalculationError, InputDataError, InvalidParameterError
from hydrolog.operations import stats_low_flow_sequences
from hydrolog.statistics import (
    calculate_characteristic_values,
    duration_curve,
    exceedance_values,
    runoff_volumes,
    threshold_events,
    threshold_runs,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def days(first: str, count: int) -> np.ndarray:
    return np.datetime64(first, "D") + np.arange(count)


class TestThresholdRuns:
    def test_runs_merge_across_gaps_shorter_than_the_limit(self):
        beyond = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1], dtype=bool)
        starts, ends = threshold_runs(beyond, min_duration_days=1, max_gap_days=3)
        # the gap of 2 days merges, the gap of 4 does not
        assert starts.tolist() == [0, 9]
        assert ends.tolist() == [4, 11]

    def test_zero_gap_merges_nothing_and_the_duration_filters(self):
        beyond = np.array([1, 0, 1, 1, 1, 0, 1], dtype=bool)
        starts, ends = threshold_runs(beyond, min_duration_days=2, max_gap_days=0)
        assert (starts.tolist(), ends.tolist()) == ([2], [4])


class TestThresholdEvents:
    def test_a_missing_day_ends_an_event_and_peaks_are_dated(self):
        values = np.array([1.0, 5.0, 7.0, np.nan, 6.0, 2.0, 5.0])
        result = threshold_events(values, days("2020-10-30", 7), level=5.0)
        assert [e.start_date for e in result.events] == [
            "2020-10-31",
            "2020-11-03",
            "2020-11-05",
        ]
        first = result.events[0]
        assert (first.duration_days, first.peak, first.peak_date) == (
            2,
            7.0,
            "2020-11-01",
        )
        assert first.open_end and not first.open_start
        # 2020-10-31 is in hydrological year 2020, 2020-11-03 in 2021
        assert [(y.year, y.days_beyond, y.n_events) for y in result.years] == [
            (2020, 1, 1),
            (2021, 3, 2),
        ]
        assert result.n_missing_days == 1

    def test_below_counts_values_under_the_level_and_bridges_gaps(self):
        values = np.array([0.5, 2.0, 0.2, 3.0, 0.8])
        result = threshold_events(
            values,
            days("2021-01-01", 5),
            level=1.0,
            direction="below",
            max_gap_days=2,
        )
        assert result.n_events == 1
        event = result.events[0]
        assert (event.duration_days, event.days_beyond, event.peak) == (5, 3, 0.2)


class TestCharacteristicValues:
    def test_first_and_second_degree_of_years_and_half_years(self):
        dates = days("2019-11-01", 731)  # hydrological years 2020 and 2021
        values = np.arange(731, dtype=float)
        values[10] = -5.0  # the winter minimum of 2020
        result = calculate_characteristic_values(values, dates, parameter="H")
        first = result.years[0]
        assert (first.winter.min, first.winter.min_date) == (-5.0, "2019-11-11")
        assert first.winter.days == 182 and first.summer.days == 184
        assert first.annual.max == 365.0  # 2020-10-31, the last day of 2020
        assert result.labels["wwx"] == "WWW" and result.labels["snx"] == "SNW"
        assert result.wwx == 730.0 and result.nwx == 365.0
        assert result.swx == pytest.approx((365.0 + 730.0) / 2)
        assert result.winter is not None
        assert result.winter.wwx == 546.0  # 30 April 2021 is day 546
        assert result.incomplete_years == []  # 366 and 365 days, all with values
        assert result.period_years == 2

    def test_half_year_file_gives_the_larger_half_year_maximum(self, tmp_path):
        path = tmp_path / "half.csv"
        path.write_text(
            "year,period,Q_min [m3/s],Q_mean [m3/s],Q_max [m3/s],Q_max_start\n"
            "2020,winter,1.0,5.0,40.0,2020-03-01T07:00:00\n"
            "2020,summer,0.5,4.0,90.0,2020-06-24T18:00:00\n"
            "2020,annual,,4.5,,\n"
            "2021,winter,2.0,6.0,50.0,2021-02-02\n"
            "2021,summer,,,,\n"
            "2021,annual,,5.5,,\n",
            encoding="utf-8",
        )
        result = run_command(
            "stats characteristic", {"half_year_file": str(path)}
        ).to_dict()["result"]
        years = result["years"]
        assert years[0]["annual"] == {
            "min": 0.5,
            "mean": 4.5,
            "max": 90.0,
            "min_date": None,
            "max_date": "2020-06-24",
            "days_with_data": None,
            "days": None,
        }
        # a missing half-year leaves the annual extremes unknown
        assert years[1]["annual"]["max"] is None
        assert (result["wwx"], result["ssx"]) == (90.0, 5.0)
        assert result["winter"]["wwx"] == 50.0

    def test_half_year_file_errors_are_data_errors(self, tmp_path):
        path = tmp_path / "half.csv"
        path.write_text(
            "year,period,Q_min,Q_mean,Q_max\n2020,spring,1,2,3\n", encoding="utf-8"
        )
        with pytest.raises(InputDataError) as caught:
            run_command("stats characteristic", {"half_year_file": str(path)})
        assert caught.value.details["reason"] == "bad_period"

    def test_the_period_selects_years_and_notes_a_short_one(self):
        envelope = run_command(
            "stats characteristic",
            {
                "input_file": str(FIXTURES / "station_daily.csv"),
                "value_column": "Q",
                "date_column": "date",
                "first_year": 2021,
                "last_year": 2021,
            },
        ).to_dict()
        assert envelope["result"]["period_years"] == 1
        codes = [item["code"] for item in envelope["notices"]]
        assert "short_reference_period" in codes
        with pytest.raises(CalculationError) as caught:
            run_command(
                "stats characteristic",
                {
                    "input_file": str(FIXTURES / "station_daily.csv"),
                    "value_column": "Q",
                    "date_column": "date",
                    "first_year": 1990,
                    "last_year": 1991,
                },
            )
        assert caught.value.details["reason"] == "no_values_in_period"


class TestDurationCurve:
    def test_weibull_positions_interpolated_between_ranks(self):
        values = np.array([10.0, 20.0, 30.0, 40.0])  # positions 20, 40, 60, 80 %
        assert exceedance_values(values, [20, 50, 80]).tolist() == [40.0, 25.0, 10.0]

    def test_classes_from_a_multiple_of_the_width_with_cumulative_days(self):
        values = np.array([31.0, 38.0, 45.0, 45.0, 52.0])
        dates = np.array(
            ["2020-11-01", "2020-12-01", "2021-01-01", "2021-05-01", "2021-10-31"],
            dtype="datetime64[D]",
        )
        result = duration_curve(values, dates, class_width=10.0)
        assert [(c.lower, c.days) for c in result.classes] == [
            (50.0, 1),
            (40.0, 2),
            (30.0, 2),
        ]
        assert [c.days_with_higher for c in result.classes] == [1, 3, 5]
        assert [c.days_with_lower for c in result.classes] == [5, 4, 2]
        assert result.classes[1].months == [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        # 30-40 and 40-50 hold two days each: the lower one is modal
        assert result.modal_class is not None
        assert result.modal_class.lower == 30.0


class TestRunoffVolumes:
    def test_volumes_of_complete_and_incomplete_years(self):
        dates = days("2019-11-01", 366 + 365)  # 2020 (leap) and 2021
        flows = np.ones(dates.size)
        flows[400] = np.nan
        result = runoff_volumes(flows, dates)
        assert result.years[0].volume_m3 == pytest.approx(366 * 86_400.0)
        assert result.years[0].complete and not result.years[1].complete
        assert result.mean_annual_volume_m3 == pytest.approx(366 * 86_400.0)
        assert result.cumulative_year == 2020
        assert result.monthly_mean_volume_m3[0] == pytest.approx(30 * 86_400.0)


class TestLowFlowSequencesWithGaps:
    def test_sequences_bridge_missing_days_and_years_are_summarised(self):
        dates = days("2020-11-01", 20)
        values = np.full(20, 10.0)
        values[3:7] = 1.0
        values[7] = np.nan  # a missing day inside the dry spell
        values[8:10] = 1.0
        result = stats_low_flow_sequences(
            values=[None if np.isnan(v) else v for v in values.tolist()],
            dates=[str(d) for d in dates],
            threshold=2.0,
            min_duration_days=5,
            max_gap_days=4,
        ).result.to_dict()
        sequence = result["sequences"][0]
        assert (sequence["duration_days"], sequence["missing_days"]) == (7, 1)
        assert sequence["deficit_volume"] == pytest.approx(6.0)
        assert sequence["deficit_volume_m3"] == pytest.approx(6.0 * 86_400.0)
        assert result["years"][0]["n_events"] == 1

    def test_a_threshold_from_the_series_excludes_a_given_one(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "stats low-flow-sequences",
                {
                    "input_file": str(FIXTURES / "station_daily.csv"),
                    "value_column": "Q",
                    "date_column": "date",
                    "threshold": 2.0,
                    "threshold_method": "exceedance",
                },
            )
        assert caught.value.details == {"option": "threshold", "reason": "conflict"}


class TestRatingCurvePeriods:
    def test_periods_without_enough_pairs_have_no_curve(self):
        result = run_command(
            "hydrometrics rating-curve",
            {
                "input_file": str(FIXTURES / "station_daily.csv"),
                "level_column": "H",
                "discharge_column": "Q",
                "date_column": "date",
                "years_per_period": 10,
            },
        ).to_dict()["result"]
        assert [(p["first_year"], p["last_year"]) for p in result["periods"]] == [
            (2019, 2020),
            (2021, 2023),
        ]
        assert all(p["reason"] is None for p in result["periods"])

    def test_years_need_dates(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "hydrometrics rating-curve",
                {
                    "water_levels": [60, 80, 100, 120],
                    "discharges": [1.0, 3.0, 6.0, 10.0],
                    "first_year": 2020,
                },
            )
        assert caught.value.details == {"option": "dates", "reason": "required"}
