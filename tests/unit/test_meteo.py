"""Meteorological statistics (``meteo`` group; plan 2026-11-13, D12).

Hand-computed sequences for each index, the WMO-No. 1203 rules on missing days, and
the ETCCDI counts of the fixture year 2021 (Zhang et al., 2011) counted directly from
the rows of ``tests/fixtures/meteo_daily.csv``.
"""

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import run_command
from hydrolog.exceptions import CalculationError, InputDataError, InvalidParameterError
from hydrolog.statistics import (
    fit_gamma,
    month_precipitation_class,
    pci_class,
    precipitation_concentration_index,
    precipitation_spells,
    precipitation_sums,
    si_class,
    sielianinov_class,
    year_precipitation_class,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "meteo_daily.csv"


def _days(first: str, count: int) -> list[str]:
    start = np.datetime64(first)
    return [str(start + np.timedelta64(n, "D")) for n in range(count)]


def _result(command: str, **options) -> dict:
    return run_command(command, options).to_dict()["result"]


def _rows(year: int) -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8") as stream:
        return [row for row in csv.DictReader(stream) if row["year"] == str(year)]


def _numbers(rows: list[dict[str, str]], column: str) -> list[float]:
    return [float(row[column]) for row in rows]


class TestMonthlyRulesOfWmo1203:
    """Sums need every day; a counted accumulated total stands for its days."""

    def test_a_month_with_a_missing_day_has_no_sum(self):
        dates = _days("2001-01-01", 31)
        values = [1.0] * 31
        values[10] = math.nan
        result = precipitation_sums(values, dates)
        assert result.years[0].months[0].total_mm is None

    def test_a_total_after_three_missing_days_stands_for_them(self):
        dates = _days("2001-01-01", 31)
        values = [1.0] * 31
        values[10:13] = [math.nan] * 3
        values[13] = 4.0  # the total of four days
        flags = [False] * 31
        flags[13] = True
        result = precipitation_sums(values, dates, accumulated=flags)
        assert result.years[0].months[0].total_mm == pytest.approx(31.0)

    def test_a_total_after_four_missing_days_does_not(self):
        dates = _days("2001-01-01", 31)
        values = [1.0] * 31
        values[10:14] = [math.nan] * 4
        values[14] = 5.0
        flags = [False] * 31
        flags[14] = True
        result = precipitation_sums(values, dates, accumulated=flags)
        assert result.years[0].months[0].total_mm is None

    def test_counts_are_scaled_and_missing_from_eleven_days(self):
        dates = _days("2001-04-01", 30)
        wet = [5.0 if day % 2 else 0.0 for day in range(30)]  # 15 wet days
        result = _result(
            "meteo precipitation",
            index="days",
            dates=dates[3:],  # three absent days: 27 known, 14 of them wet
            precipitation_mm=wet[3:],
        )
        assert result["years"][0]["months"][3]["days"][0] == pytest.approx(14 / 27 * 30)
        many = wet.copy()
        many[0:11] = [math.nan] * 11
        days = run_command(
            "meteo precipitation",
            {"index": "days", "dates": dates[11:], "precipitation_mm": many[11:]},
        ).to_dict()["result"]
        assert days["years"][0]["months"][3]["days"][0] is None


class TestPrecipitationIndices:
    """Hand-computed sequences of the indices of ``meteo precipitation``."""

    def test_the_normal_needs_eighty_percent_of_the_years(self):
        every = _days("2001-01-01", 1826)  # 2001-2005, 2004 a leap year
        dates = [day for n, day in enumerate(every) if n != 400]  # 2002-02-05 absent
        result = _result(
            "meteo precipitation",
            index="sums",
            dates=dates,
            precipitation_mm=[1.0] * len(dates),
        )
        assert result["period"]["normal_mm"] == pytest.approx(365.25)
        assert result["period"]["normal_years"] == 4
        dates = [day for n, day in enumerate(every) if n not in (400, 800)]
        output = run_command(
            "meteo precipitation",
            {"index": "sums", "dates": dates, "precipitation_mm": [1.0] * len(dates)},
        )
        assert output.result.period.normal_mm is None
        assert "normal_not_computed" in [item.code for item in output.notices]

    def test_maxima_of_one_and_two_days_with_their_dates(self):
        dates = _days("2001-01-01", 365)
        values = [0.0] * 365
        values[100], values[101], values[200] = 20.0, 15.0, 30.0
        result = _result(
            "meteo precipitation",
            index="maxima",
            dates=dates,
            precipitation_mm=values,
            durations_days=[2],
        )
        one, two = result["years"][0]["durations"]
        assert (one["sum_mm"], one["start_date"]) == (30.0, "2001-07-20")
        assert (two["sum_mm"], two["start_date"], two["end_date"]) == (
            35.0,
            "2001-04-11",
            "2001-04-12",
        )

    def test_intensity_heavy_and_days_of_a_known_year(self):
        dates = _days("2001-01-01", 365)
        values = [0.0] * 365
        for day in range(0, 360, 3):
            values[day] = float(day % 40) + 1.0  # 120 wet days of 1 to 40 mm
        days = _result(
            "meteo precipitation",
            index="days",
            dates=dates,
            precipitation_mm=values,
            thresholds_mm=[1.0, 10.0, 20.0],
        )["years"][0]["days"]
        wet = [v for v in values if v >= 1.0]
        assert days == [
            120.0,
            float(sum(v >= 10 for v in wet)),
            float(sum(v >= 20 for v in wet)),
        ]
        intensity = _result(
            "meteo precipitation",
            index="intensity",
            dates=dates,
            precipitation_mm=values,
        )["years"][0]
        assert intensity["sdii_mm"] == pytest.approx(sum(wet) / len(wet))
        heavy = _result(
            "meteo precipitation", index="heavy", dates=dates, precipitation_mm=values
        )
        p95 = heavy["period"]["thresholds_mm"][0]
        ranked = sorted(wet)
        h = (len(ranked) + 1 / 3) * 0.95 + 1 / 3  # quantile type 8 by hand
        low = math.floor(h)
        expected = ranked[low - 1] + (h - low) * (ranked[low] - ranked[low - 1])
        assert p95 == pytest.approx(expected)
        above = sum(v for v in wet if v > p95)
        assert heavy["years"][0]["shares_percent"][0] == pytest.approx(
            100 * above / sum(wet)
        )

    def test_pci_of_equal_months_and_of_one_month_and_the_classes(self):
        assert precipitation_concentration_index([10.0] * 12) == pytest.approx(100 / 12)
        assert precipitation_concentration_index([0.0] * 11 + [50.0]) == 100.0
        assert pci_class(10.0) == "uniform"
        assert pci_class(10.5) == "moderate"
        assert si_class(0.19) == "very_equable"
        assert si_class(1.2) == "extreme"


class TestSpells:
    """The run logic of ``stats threshold-events`` on dry and wet days."""

    def test_spells_end_at_a_wet_day_and_at_a_missing_one(self):
        values = [0.0, 0.0, 5.0, 0.0, 0.0, 0.0, math.nan, 0.0, 2.0]
        result = precipitation_spells(values, _days("2001-01-01", 9))
        lengths = [(s.start_date, s.length_days, s.open_end) for s in result.spells]
        assert lengths == [
            ("2001-01-01", 2, False),
            ("2001-01-04", 3, True),
            ("2001-01-08", 1, False),
        ]
        wet = precipitation_spells(values, _days("2001-01-01", 9), kind="wet")
        assert [s.length_days for s in wet.spells] == [1, 1]


class TestSpiAndClasses:
    """Thom's fit, the SPI and the classes of relative precipitation."""

    def test_thom_estimates_of_a_sample(self):
        sample = np.array([0.0, 10.0, 20.0, 40.0, 30.0])
        alpha, beta, q = fit_gamma(sample)
        positive = sample[sample > 0]
        a = math.log(positive.mean()) - np.log(positive).mean()
        assert alpha == pytest.approx((1 + math.sqrt(1 + 4 * a / 3)) / (4 * a))
        assert beta == pytest.approx(positive.mean() / alpha)
        assert q == pytest.approx(0.2)

    def test_classes_of_years_and_months(self):
        # Kaczorowska (1962), whole percent: 89 dry, 90 normal, 151 extremely wet
        assert year_precipitation_class(89.4) == "dry"
        assert year_precipitation_class(89.6) == "normal"
        assert year_precipitation_class(151.0) == "extremely_wet"
        # months (Gąsiorek and Musiał, 2011, Table 1): 24.9 extremely dry, 125 normal
        assert month_precipitation_class(24.9) == "extremely_dry"
        assert month_precipitation_class(125.0) == "normal"
        assert month_precipitation_class(200.5) == "extremely_wet"

    def test_sielianinov_classes_of_skowera_and_pula(self):
        assert sielianinov_class(0.4) == "extremely_dry"
        assert sielianinov_class(0.41) == "very_dry"
        assert sielianinov_class(1.6) == "optimal"
        assert sielianinov_class(3.01) == "extremely_wet"


class TestTemperatureSnowHydrothermal:
    """Degree days, the snow season and the hydrothermal coefficient by hand."""

    def test_degree_days_of_eurostat(self):
        dates = _days("2001-01-01", 365)
        tmean = [10.0] * 365
        tmean[0], tmean[1] = 16.0, 15.0  # no heating on 16 °C, 3 on 15 °C
        year = _result(
            "meteo temperature", index="degree_days", dates=dates, tmean_c=tmean
        )["years"][0]
        assert year["heating_degree_days"] == pytest.approx(3.0 + 363 * 8.0)
        assert year["growing_degree_days"] == pytest.approx(11.0 + 10.0 + 363 * 5.0)

    def test_october_snow_starts_the_winter_it_belongs_to(self):
        dates = _days("2020-08-01", 365)
        depth = [0.0] * 365
        depth[87] = 3.0  # 27 October 2020
        depth[180] = 12.0  # 28 January 2021
        winter = _result("meteo snow", dates=dates, snow_cover_cm=depth)["years"][0]
        assert winter["year"] == 2021
        assert (winter["first_date"], winter["last_date"]) == (
            "2020-10-27",
            "2021-01-28",
        )
        assert (winter["max_depth_cm"], winter["cover_days"]) == (12.0, 2.0)

    def test_the_monthly_and_season_coefficients(self):
        dates = _days("2001-01-01", 365)
        tmean = [12.0] * 365
        rain = [0.0] * 365
        rain[120:151] = [2.0] * 31  # May: 62 mm at 12 °C
        year = _result(
            "meteo hydrothermal", dates=dates, precipitation_mm=rain, tmean_c=tmean
        )["years"][0]
        may = year["months"][1]
        assert may["coefficient"] == pytest.approx(10 * 62 / (12 * 31))
        assert year["season_coefficient"] == pytest.approx(10 * 62 / (12 * 365))


class TestEtccdiCountsOfTheFixtureYear:
    """FD, ID, SU, TR, R10mm, R20mm, CDD, CWD, PRCPTOT, SDII, R95pTOT of 2021."""

    def test_the_counts_equal_the_rows_of_the_file(self):
        rows = _rows(2021)
        assert len(rows) == 365
        tmax, tmin = _numbers(rows, "Tmax [degC]"), _numbers(rows, "Tmin [degC]")
        rain = _numbers(rows, "P [mm]")
        days = _result("meteo temperature", index="days", input_file=str(FIXTURE))[
            "years"
        ]
        year = next(row for row in days if row["year"] == 2021)
        assert year["frost_days"] == sum(t < 0 for t in tmin)  # FD
        assert year["ice_days"] == sum(t < 0 for t in tmax)  # ID
        assert year["summer_days"] == sum(t > 25 for t in tmax)  # SU
        assert year["hot_days"] == sum(t > 30 for t in tmax)
        assert year["tropical_nights"] == sum(t > 20 for t in tmin)  # TR
        counts = _result(
            "meteo precipitation",
            index="days",
            input_file=str(FIXTURE),
            thresholds_mm=[10, 20],
        )["years"]
        assert next(r for r in counts if r["year"] == 2021)["days"] == [
            sum(p >= 10 for p in rain),  # R10mm
            sum(p >= 20 for p in rain),  # R20mm
        ]
        wet = [p for p in rain if p >= 1.0]
        intensity = _result(
            "meteo precipitation", index="intensity", input_file=str(FIXTURE)
        )["years"]
        mine = next(r for r in intensity if r["year"] == 2021)
        assert mine["wet_day_total_mm"] == pytest.approx(sum(wet))  # PRCPTOT
        assert mine["sdii_mm"] == pytest.approx(sum(wet) / len(wet))  # SDII

        def longest(flags: list[bool]) -> int:
            best = run = 0
            for flag in flags:
                run = run + 1 if flag else 0
                best = max(best, run)
            return best

        for kind, flags in (
            ("dry", [p < 1 for p in rain]),
            ("wet", [p >= 1 for p in rain]),
        ):
            spells = _result("meteo spells", input_file=str(FIXTURE), kind=kind)[
                "years"
            ]
            assert next(r for r in spells if r["year"] == 2021)[
                "longest_days"
            ] == longest(flags)  # CDD, CWD (no spell of 2021 crosses its ends)

    def test_r95ptot_with_the_percentile_of_the_period(self):
        heavy = _result("meteo precipitation", index="heavy", input_file=str(FIXTURE))
        p95 = heavy["period"]["thresholds_mm"][0]
        rain = _numbers(_rows(2021), "P [mm]")
        wet = sum(p for p in rain if p >= 1)
        year = next(row for row in heavy["years"] if row["year"] == 2021)
        assert year["shares_percent"][0] == pytest.approx(
            100 * sum(p for p in rain if p > p95) / wet
        )


class TestErrors:
    """Errors of the operations, by registry code and reason."""

    def test_a_negative_precipitation_in_a_file_is_a_data_error(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_text(
            "date,P [mm]\n2001-01-01,1.0\n2001-01-02,-2.0\n", encoding="utf-8"
        )
        with pytest.raises(InputDataError) as caught:
            run_command(
                "meteo precipitation", {"index": "sums", "input_file": str(path)}
            )
        assert caught.value.details["reason"] == "negative_value"

    def test_too_few_wet_days_for_percentiles(self):
        with pytest.raises(CalculationError) as caught:
            run_command(
                "meteo precipitation",
                {
                    "index": "heavy",
                    "dates": _days("2001-01-01", 30),
                    "precipitation_mm": [5.0] * 30,
                },
            )
        assert caught.value.details["reason"] == "too_few_wet_days"

    def test_a_period_without_values(self):
        with pytest.raises(CalculationError) as caught:
            run_command(
                "meteo spells",
                {"input_file": str(FIXTURE), "first_year": 1990, "last_year": 1991},
            )
        assert caught.value.details["reason"] == "no_values_in_period"

    def test_range_needs_both_extremes(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "meteo temperature",
                {"index": "range", "dates": ["2001-01-01"], "tmax_c": [3.0]},
            )
        assert caught.value.details["option"] == "tmin_c"
