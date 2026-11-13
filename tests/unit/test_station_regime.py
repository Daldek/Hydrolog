"""Station regime analyses of plan 2026-11-13 (S3): published worked examples.

Sources of the expected values:

* Sen's slope, its interval and the Mann-Kendall S: Gilbert, R.O. (1987), Statistical
  Methods for Environmental Pollution Monitoring, Example 16.5 (pp. 218-219) and
  Exercises 16.1-16.3 with their answers (p. 224).
* Dynowska's regime types: the mean Pardé coefficients of the five types in
  Wrzesiński, D. (2018), Badania Fizjograficzne A69, Table 1 (pp. 253-254).
* Walsh and Lawler's (1981) seasonality index: its bounds 0 and 1.83.
* The Lyne and Hollick filter: the data and BFIs of Ladson et al. (2013), Australasian
  Journal of Water Resources 17(1), as published with the authors' code
  (github.com/TonyLadson/BaseflowSeparation_LyneHollick, ``BFI_example.R``).
* Without a published example (computed by hand in the comments): Pardé's coefficients,
  the circular mean date, the harmonics of an exact sinusoid, the recession constant of
  an exponential recession.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from hydrolog import operations
from hydrolog.catalog import run_command
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics import (
    annual_cycle,
    circular_mean_date,
    dynowska_regime_type,
    flow_regime,
    lyne_hollick_filter,
    recession_constant,
    seasonality_index,
    sen_slope,
)

# Ladson et al. (2013): 67 daily flows of the Bass River at Loch [ML/d].
BASS_RIVER = [
    5, 7, 108, 117, 57, 36, 26, 95, 1169, 308, 144, 89, 62, 48, 40, 35, 73, 82, 342,
    393, 310, 275, 260, 245, 256, 141, 119, 934, 382, 158, 96, 122, 103, 83, 67, 148,
    366, 161, 119, 82, 330, 294, 261, 266, 153, 247, 703, 498, 286, 163, 124, 85, 94,
    81, 62, 47, 37, 30, 26, 24, 24, 22, 21, 20, 19, 18, 18,
]  # fmt: skip

# Wrzesiński (2018), Table 1: the mean Pardé coefficients (XI-X) of each regime type.
WRZESINSKI_TABLE_1 = {
    1: [1.03, 1.10, 1.12, 1.14, 1.21, 1.12, 0.96, 0.86, 0.85, 0.82, 0.86, 0.93],
    2: [0.93, 1.08, 1.16, 1.25, 1.52, 1.35, 0.95, 0.77, 0.76, 0.71, 0.71, 0.81],
    3: [0.88, 1.12, 1.23, 1.36, 1.90, 1.60, 0.89, 0.62, 0.61, 0.54, 0.55, 0.70],
    4: [0.74, 0.85, 0.85, 0.93, 1.45, 1.46, 1.12, 1.08, 1.15, 0.87, 0.79, 0.69],
    5: [0.71, 0.74, 0.72, 0.76, 1.13, 1.28, 1.27, 1.31, 1.36, 1.04, 0.91, 0.77],
}


def days(first: str, count: int) -> list[str]:
    start = np.datetime64(first, "D")
    return [str(day) for day in start + np.arange(count)]


def envelope(command: str, **options: Any) -> dict[str, Any]:
    return run_command(command, options).to_dict()


def direct(name: str, **options: Any) -> tuple[dict[str, Any], list[str]]:
    """Call an operation in Python: inline values may be None (missing)."""
    output = getattr(operations, name)(**options)
    return output.result.to_dict(), [notice.code for notice in output.notices]


class TestSenSlope:
    def test_gilbert_example_16_5_with_two_values_in_a_time_period(self):
        times = np.array([1, 1, 1, 2, 3, 3, 4, 5], dtype=float)
        data = np.array([10, 22, 21, 30, 22, 30, 40, 40], dtype=float)
        estimate = sen_slope(data, times, var_s=58.1, alpha=0.10)
        # 24 slopes (the pairs of one time period have none), median 5.5; the 90 %
        # interval interpolates between the 5th and 6th and the 19th and 20th slopes
        assert estimate.n_slopes == 24
        assert estimate.slope == 5.5
        assert estimate.lower == pytest.approx(2.6, abs=0.05)
        assert estimate.upper == pytest.approx(9.3, abs=0.05)

    def test_gilbert_exercises_16_1_to_16_3(self):
        # the two values below the detection limit at half of it, 0.25 (Exercise 16.2b)
        values = [0.25, 1.1, 0.25, 3, 1.5, 1.2, 4]
        document = envelope(
            "stats mann-kendall", values=values, years=[1, 2, 3, 4, 5, 6, 7], alpha=0.10
        )["result"]
        assert document["s_statistic"] == 12  # 16 - 4 (Exercise 16.1)
        # Exercise 16.1: the two NDs are one group of 2 tied values, Var(S) = 44.3 - 1
        assert document["var_s"] == pytest.approx(43.3, abs=0.05)
        assert document["z_score"] == pytest.approx(1.67, abs=0.005)
        assert document["sen_slope"] == pytest.approx(0.33, abs=0.005)  # 16.2 (b)
        # Conover's intercept: median(x) - slope * median(t) = 1.2 - 4/3
        assert document["sen_intercept"] == pytest.approx(1.2 - 4 / 3)
        # Exercise 16.3 leaves the correction out on purpose (the tied values were NDs
        # assigned to be equal): its 90 % interval is built on Var(S) = 44.3
        estimate = sen_slope(
            np.array(values, dtype=float), np.arange(1.0, 8.0), var_s=44.3, alpha=0.10
        )
        assert estimate.lower == pytest.approx(0.0, abs=0.005)
        assert estimate.upper == pytest.approx(0.94, abs=0.005)

    def test_gilbert_exercise_16_2a_drops_the_missing_values(self):
        document, codes = direct(
            "stats_mann_kendall",
            values=[None, 1.1, None, 3, 1.5, 1.2, 4],
            years=[1, 2, 3, 4, 5, 6, 7],
        )
        assert document["sen_slope"] == pytest.approx(0.23, abs=0.005)
        assert codes == ["missing_values_removed"]

    def test_without_years_the_slope_is_per_step_and_a_gap_keeps_its_step(self):
        document, _ = direct("stats_mann_kendall", values=[1.0, None, 3.0, 4.0])
        # times 0, 2, 3: every pair has the slope 1 (as 0, 1, 2 the median is 1.5)
        assert document["sen_slope"] == 1.0
        assert document["sen_intercept"] == pytest.approx(3.0 - 1.0 * 2)

    def test_years_move_the_intercept_not_the_slope(self):
        values = [3.0, 4.5, 4.0, 6.2, 5.9, 7.1]
        per_step = envelope("stats mann-kendall", values=values)["result"]
        per_year = envelope(
            "stats mann-kendall", values=values, years=list(range(2001, 2007))
        )["result"]
        assert per_year["sen_slope"] == per_step["sen_slope"]
        assert per_year["sen_intercept"] == pytest.approx(
            per_step["sen_intercept"] - 2001 * per_step["sen_slope"]
        )

    def test_a_short_series_has_no_interval(self):
        document = envelope("stats mann-kendall", values=[3.0, 4.5, 4.0, 6.2])["result"]
        # N' = 6 slopes, C = 1.96 sqrt(8.67) = 5.77: the ranks 0.11 and 6.9 are outside
        assert document["sen_slope_lower"] is None
        assert document["sen_slope_upper"] is None

    def test_years_must_increase(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "stats mann-kendall",
                {"values": [1.0, 2.0, 3.0], "years": [2001, 2001, 2002]},
            )
        assert caught.value.details["option"] == "years"


class TestRegime:
    @pytest.mark.parametrize("code", sorted(WRZESINSKI_TABLE_1))
    def test_the_mean_coefficients_of_wrzesinski_2018_give_their_type(self, code):
        assert dynowska_regime_type(WRZESINSKI_TABLE_1[code]).code == code

    def test_the_spring_and_summer_months_that_decide(self):
        # type 4: April 1.46 over March 1.45; July 1.15 is at least the mean flow but
        # below 0.95 of the spring coefficient
        criteria = dynowska_regime_type(WRZESINSKI_TABLE_1[4]).criteria
        assert (criteria.spring_month, criteria.spring_coefficient) == (4, 1.46)
        assert (criteria.summer_month, criteria.summer_coefficient) == (7, 1.15)

    def test_pardé_coefficients_share_and_index_of_a_spring_flood(self):
        # hydrological year 2021 (365 days): 3 m³/s in March and April, 1 otherwise
        dates = np.datetime64("2020-11-01") + np.arange(365)
        months = dates.astype("datetime64[M]").astype(int) % 12 + 1
        flows = np.where((months == 3) | (months == 4), 3.0, 1.0)
        regime = flow_regime(flows, dates)
        annual = (365 + 2 * 61) / 365  # the mean of the days
        assert regime.months == [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert regime.annual_mean == pytest.approx(annual)
        assert regime.parde[4] == pytest.approx(3 / annual)  # March, fifth of XI-X
        assert regime.parde[0] == pytest.approx(1 / annual)
        # volumes, the means times the days of the month (28.25 for February), January
        # to December; 487.25 in all
        volumes = np.array([31, 28.25, 93, 90, 31, 30, 31, 31, 30, 31, 30, 31])
        assert regime.spring_share == pytest.approx((93 + 90) / 487.25)
        assert regime.seasonality_index == pytest.approx(
            np.abs(volumes - 487.25 / 12).sum() / 487.25
        )
        assert regime.regime_type.code == 3  # a spring coefficient of 2.25 > 1.80

    def test_walsh_and_lawler_bounds(self):
        assert seasonality_index([10.0] * 12) == 0.0
        assert seasonality_index([12.0] + [0.0] * 11) == pytest.approx(11 / 6)

    def test_a_month_without_a_value_is_a_calculation_error(self):
        dates = [day for day in days("2020-11-01", 365) if day[5:7] != "07"]
        with pytest.raises(CalculationError) as caught:
            run_command("stats regime", {"values": [1.0] * len(dates), "dates": dates})
        assert caught.value.details == {"reason": "missing_months", "months": [7]}

    def test_the_period_and_its_notice(self):
        dates = days("2019-11-01", 731)  # hydrological years 2020 and 2021
        values = [1.0 + (index % 365) / 365 for index in range(731)]
        result = envelope(
            "stats regime", values=values, dates=dates, first_year=2021, last_year=2021
        )
        document = result["result"]
        assert (document["first_year"], document["last_year"]) == (2021, 2021)
        assert document["period_years"] == 1
        assert [n["code"] for n in result["notices"]] == ["short_reference_period"]


class TestSeasonality:
    def test_the_mean_of_dates_symmetric_about_a_day(self):
        mean = circular_mean_date(["2001-03-22", "2001-04-11"])  # days 81 and 101
        # the mean angle is that of day 91 (1 April) of the common year, read back on
        # a year of 365.25 days: (91 - 0.5) * 365.25 / 365 + 0.5
        assert mean.mean_day == pytest.approx(90.5 * 365.25 / 365 + 0.5)
        assert mean.mean_date == "04-01"
        assert mean.concentration == pytest.approx(math.cos(2 * math.pi * 10 / 365))

    def test_the_mean_crosses_the_new_year(self):
        mean = circular_mean_date(["2000-12-27", "2001-01-06"])
        assert mean.mean_date == "01-01"
        assert mean.concentration > 0.99

    def test_complete_years_of_a_daily_series_with_their_first_dates(self):
        dates = days("2019-11-01", 731)  # 2020 (366 days) and 2021
        values = [1.0] * 731
        values[100] = values[150] = 9.0  # 2020-02-09 and 2020-03-30: the first counts
        values[500] = 7.0  # 2021-03-15
        del dates[700], values[700]  # 2021-10-01 absent: 2021 is incomplete
        result = envelope("stats seasonality", values=values, dates=dates)
        document = result["result"]
        assert document["years"] == [{"year": 2020, "value": 9.0, "date": "2020-02-09"}]
        assert (document["winter_share"], document["summer_share"]) == (1.0, 0.0)
        assert [n["code"] for n in result["notices"]] == [
            "incomplete_years",
            "short_reference_period",
        ]

    def test_no_complete_year_is_a_calculation_error(self):
        with pytest.raises(CalculationError) as caught:
            run_command(
                "stats seasonality",
                {"values": [1.0] * 100, "dates": days("2019-11-01", 100)},
            )
        assert caught.value.details["reason"] == "no_complete_years"

    def test_half_years_give_the_larger_maximum_and_name_undated_ones(self, tmp_path):
        path = tmp_path / "half.csv"
        path.write_text(
            "year,period,Q_min,Q_mean,Q_max,Q_max_start\n"
            "2020,winter,1.0,5.0,40.0,2020-03-01T07:00:00\n"
            "2020,summer,0.5,4.0,90.0,2020-06-24\n"
            "2021,winter,2.0,6.0,50.0,2021-02-02\n"
            "2021,summer,1.0,5.0,30.0,\n"
            "2022,winter,2.0,6.0,50.0,2022-01-10\n"
            "2022,summer,1.0,5.0,70.0,\n",
            encoding="utf-8",
        )
        result = envelope("stats seasonality", half_year_file=str(path))
        document = result["result"]
        # 2021: the dated winter maximum is the larger; 2022: the larger summer one has
        # no date and is left out
        assert document["years"] == [
            {"year": 2020, "value": 90.0, "date": "2020-06-24"},
            {"year": 2021, "value": 50.0, "date": "2021-02-02"},
        ]
        assert document["source"] == "half_years"
        assert document["winter_share"] == 0.5
        undated = result["notices"][0]
        assert (undated["code"], undated["details"]["years"]) == (
            "undated_extremes",
            [2022],
        )


class TestHarmonics:
    def test_an_exact_sinusoid_is_recovered(self):
        dates, steps = [], []
        for year, length in ((2020, 366), (2021, 365), (2022, 365)):
            dates.append(np.datetime64(f"{year - 1}-11-01") + np.arange(length))
            steps.append(np.arange(length, dtype=float))  # t = 0 on 1 November
        t = np.concatenate(steps)
        values = 10 + 7 * np.cos(2 * np.pi * (t - 200) / 365.25)
        values += 0.5 * np.cos(4 * np.pi * (t - 30) / 365.25)
        cycle = annual_cycle(values, np.concatenate(dates), 2)
        fit = cycle.period
        first, second = fit.harmonics
        assert fit.mean == pytest.approx(10.0)
        assert first.amplitude == pytest.approx(7.0)
        assert first.phase_day == pytest.approx(201.0)  # t = 200 is day 201
        assert second.amplitude == pytest.approx(0.5)
        assert second.phase_day == pytest.approx(31.0)
        assert fit.r_squared == pytest.approx(1.0)
        assert first.explained_variance is not None
        assert second.explained_variance is not None
        assert first.explained_variance + second.explained_variance == pytest.approx(
            1.0
        )
        # the half-year harmonic adds its variance 0.5²/2 of the total 7²/2 + 0.5²/2
        assert second.explained_variance == pytest.approx(0.25 / 49.25, rel=0.01)
        assert [row.year for row in cycle.years] == [2020, 2021, 2022]

    def test_a_year_with_too_few_values_has_no_fit_of_its_own(self):
        dates = days("2019-11-01", 366 + 250)  # 2020 whole, 250 days of 2021
        values = [5 + 3 * math.sin(index / 58.1) for index in range(366 + 250)]
        result = envelope("stats harmonics", values=values, dates=dates, harmonics=1)
        document = result["result"]
        assert [row["year"] for row in document["years"]] == [2020]
        assert document["period"]["n_values"] == 616
        left_out = result["notices"][0]
        assert left_out["code"] == "short_years_left_out"
        assert left_out["details"] == {"count": 1, "minimum": 300, "years": [2021]}

    def test_too_few_values_and_too_many_harmonics(self):
        with pytest.raises(CalculationError) as caught:
            run_command(
                "stats harmonics",
                {"values": [1.0] * 9, "dates": days("2020-01-01", 9), "harmonics": 2},
            )
        assert caught.value.details == {
            "reason": "too_few_values",
            "count": 9,
            "minimum": 10,
        }
        with pytest.raises(InvalidParameterError):
            run_command(
                "stats harmonics",
                {"values": [1.0] * 30, "dates": days("2020-01-01", 30), "harmonics": 5},
            )


class TestBaseflow:
    def test_ladson_2013_bass_river(self):
        flows = np.array(BASS_RIVER, dtype=float)
        base = lyne_hollick_filter(flows, alpha=0.98)
        assert base.sum() / flows.sum() == pytest.approx(0.1965759, abs=5e-8)

    def test_ladson_2013_bass_river_through_the_command(self):
        document = envelope(
            "stats baseflow",
            values=BASS_RIVER,
            dates=days("2020-01-01", len(BASS_RIVER)),
            alpha=0.98,
        )["result"]
        assert document["bfi"] == pytest.approx(0.1965759, abs=5e-8)
        assert (document["n_values"], document["n_spans"]) == (67, 1)

    def test_ladson_2013_missing_values_by_spans(self):
        # BFI_example.R: two spans of the flows parted by missing days, 36 and 33
        # values; their BFIs weighted by their lengths give 0.1411197
        spans = [
            np.array(BASS_RIVER[:36], dtype=float),
            np.array([*BASS_RIVER[36:], 17, 16], dtype=float),
        ]
        weighted = sum(
            span.size * lyne_hollick_filter(span, alpha=0.98).sum() / span.sum()
            for span in spans
        )
        assert weighted / 69 == pytest.approx(0.1411197, abs=5e-8)

    def test_the_recession_constant_of_an_exponential_recession(self):
        recession = recession_constant(10 * 0.9 ** np.arange(20.0))
        assert recession.k == pytest.approx(0.9)
        assert recession.half_life_days == pytest.approx(math.log(2) / -math.log(0.9))
        assert recession.n_segments == 1

    def test_a_rise_or_a_missing_day_ends_a_recession(self):
        flows = np.array(
            [10, 8, 6.4, 5.12, 4.096, 3.2768,  # five falls of 0.8: a segment
             20, 16, 12.8, 10.24, 8.192,  # four falls: too short
             30, 24, 19.2, np.nan, 15.36, 12.288, 9.8304]  # a gap parts five falls
        )  # fmt: skip
        recession = recession_constant(flows)
        assert recession.n_segments == 1
        assert recession.k == pytest.approx(0.8)

    def test_short_spans_years_and_the_series_year(self):
        # 2020 whole (366 days); 2021 without 6 November and 22 December, which leave
        # a span of 45 days between them, too short to filter
        dates = days("2019-11-01", 366 + 365)
        values = [10.0 + 5 * math.sin(index / 9.0) ** 2 for index in range(731)]
        for index in (366 + 51, 366 + 5):
            del dates[index], values[index]
        document = envelope("stats baseflow", values=values, dates=dates)["result"]
        assert document["n_spans"] == 2
        assert document["n_values"] == 731 - 2 - 45
        assert [row["year"] for row in document["years"]] == [2020, 2021]
        assert document["series_year"] == 2020  # the last complete year
        assert len(document["series_dates"]) == 366
        assert None not in document["series_baseflow"]

    def test_the_options_are_checked(self):
        options: dict[str, Any] = {
            "values": BASS_RIVER,
            "dates": days("2020-01-01", 67),
        }
        with pytest.raises(InvalidParameterError) as caught:
            run_command("stats baseflow", {**options, "passes": 4})
        assert caught.value.details["reason"] == "odd"
        with pytest.raises(InvalidParameterError) as caught:
            run_command("stats baseflow", {**options, "series_year": 2019})
        assert caught.value.details["option"] == "series_year"
        with pytest.raises(CalculationError) as caught:
            run_command(
                "stats baseflow",
                {"values": BASS_RIVER[:59], "dates": days("2020-01-01", 59)},
            )
        assert caught.value.details["reason"] == "no_gapless_span"
