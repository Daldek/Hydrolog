"""The reference period of the baselines, the variant options and exact sums of meteo.

``meteo precipitation`` (``sums``, ``heavy``, ``seasonality``), ``meteo spi`` and
``meteo temperature`` (``means``) take the normals, the wet-day percentiles and the
SPI's gamma fits from ``reference_first_year`` to ``reference_last_year`` (WMO-No.
1203, 2017; WMO-No. 1090, 2012), by default the analysed years; the values of the
analysed years come from their own days. Hand computations on
``tests/fixtures/meteo_daily.csv`` (2019-2023: an accumulated total after three
missing days in February 2019, gaps in 2022) and on synthetic series.
"""

import csv
import math
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pytest

from hydrolog.catalog import get_command, run_command
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics import fit_gamma, precipitation_sums, spi_values

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "meteo_daily.csv"
FILE = str(FIXTURE)
with FIXTURE.open(encoding="utf-8") as _stream:
    ROWS = list(csv.DictReader(_stream))
REFERENCE = (2019, 2020, 2021)


def _days(first: str, count: int) -> list[str]:
    start = np.datetime64(first)
    return [str(start + np.timedelta64(n, "D")) for n in range(count)]


def _result(command: str, **options) -> dict:
    return run_command(command, options).to_dict()["result"]


def _values(column: str, year: int, month: int | None = None) -> list[float]:
    prefix = f"{year}-{month:02d}-" if month else f"{year}-"
    return [
        float(row[column])
        for row in ROWS
        if row["date"].startswith(prefix) and row[column]
    ]


def _sum(year: int, month: int | None = None) -> float:
    """A sum of P of the fixture: every day has a value or an accumulated total."""
    return math.fsum(_values("P [mm]", year, month))


def _monthly_means(year: int) -> list[float]:
    """The monthly means of Tmean of a year of the fixture with every day."""
    return [
        math.fsum(days) / len(days)
        for days in (_values("Tmean [degC]", year, month) for month in range(1, 13))
    ]


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values)


def _applies(command: str, example: Mapping[str, object]) -> bool:
    if command == "meteo precipitation":
        return example["index"] in ("sums", "heavy", "seasonality")
    return command == "meteo spi" or example["index"] == "means"


def _default_examples() -> list:
    return [
        pytest.param(name, number, id=f"{name}#{number}")
        for name in ("meteo precipitation", "meteo spi", "meteo temperature")
        for number, example in enumerate(get_command(name).examples)
        if _applies(name, example) and "reference_first_year" not in example
    ]


class TestTheDefaultReference:
    """Without a reference period the result is that of the analysed years."""

    @pytest.mark.parametrize(("name", "number"), _default_examples())
    def test_a_catalog_example_gives_its_reference_as_its_period(self, name, number):
        example = dict(get_command(name).examples[number])
        default = run_command(name, example).to_dict()
        result = default["result"]
        keys = list(result)
        after = keys[keys.index("period_years") + 1 :][:3]
        assert after == [
            "reference_first_year",
            "reference_last_year",
            "reference_period_years",
        ]
        assert [result[key] for key in after] == [
            result["first_year"],
            result["last_year"],
            result["period_years"],
        ]
        given = run_command(
            name,
            {
                **example,
                "reference_first_year": result["first_year"],
                "reference_last_year": result["last_year"],
            },
        ).to_dict()
        assert given["result"] == result
        assert given["notices"] == default["notices"]


class TestBaselinesOfTheReferencePeriod:
    """Normals, percentiles and fits of 2019-2021 by hand; the years keep theirs."""

    def test_sums_in_percent_of_the_normals_of_the_reference(self):
        result = _result(
            "meteo precipitation",
            index="sums",
            input_file=FILE,
            first_year=2022,
            last_year=2023,
            reference_first_year=2019,
            reference_last_year=2021,
        )
        normal = _mean([_sum(year) for year in REFERENCE])
        july = _mean([_sum(year, 7) for year in REFERENCE])
        summer = _mean([sum(_sum(year, m) for m in range(5, 11)) for year in REFERENCE])
        period = result["period"]
        assert (period["normal_mm"], period["normal_years"]) == (
            pytest.approx(normal),
            3,
        )
        assert period["months"][6]["normal_mm"] == pytest.approx(july)
        assert period["summer_normal_mm"] == pytest.approx(summer)
        # the winter half-year of 2019 begins in November 2018, outside the reference
        assert period["winter_normal_mm"] is None
        year = result["years"][1]
        assert year["year"] == 2023
        assert year["percent_of_normal"] == pytest.approx(100 * _sum(2023) / normal)
        assert year["months"][6]["percent_of_normal"] == pytest.approx(
            100 * _sum(2023, 7) / july
        )
        # the statistics of the period stay those of the analysed years
        assert period["mean_mm"] == pytest.approx(_sum(2023))  # 2022 has gaps
        assert period["months"][6]["n_years"] == 1

    def test_temperature_anomalies_from_the_normals_of_the_reference(self):
        result = _result(
            "meteo temperature",
            index="means",
            input_file=FILE,
            reference_first_year=2019,
            reference_last_year=2021,
        )
        means = {year: _monthly_means(year) for year in (*REFERENCE, 2023)}
        normal = _mean([_mean(means[year]) for year in REFERENCE])
        july = _mean([means[year][6] for year in REFERENCE])
        assert result["period"]["normal_c"] == pytest.approx(normal)
        assert result["period"]["months"][6]["normal_c"] == pytest.approx(july)
        year = next(row for row in result["years"] if row["year"] == 2023)
        assert year["anomaly_c"] == pytest.approx(_mean(means[2023]) - normal)
        assert year["months"][6]["anomaly_c"] == pytest.approx(means[2023][6] - july)
        # the mean of the period is that of the analysed years with a mean
        assert result["period"]["tmean_c"] == pytest.approx(
            _mean([_mean(values) for values in means.values()])
        )

    def test_spi_fits_come_from_the_sums_of_the_reference_only(self):
        options = {
            "input_file": FILE,
            "scales_months": [1, 3],
            "reference_first_year": 2019,
            "reference_last_year": 2021,
        }
        result = _result("meteo spi", first_year=2022, **options)
        julys = [_sum(year, 7) for year in REFERENCE]
        alpha, beta, zero = fit_gamma(julys)
        fit = result["period"]["scales"][0]["fits"][6]
        assert (fit["alpha"], fit["beta"], fit["zero_probability"]) == pytest.approx(
            (alpha, beta, zero)
        )
        assert fit["n_values"] == 3
        july = next(
            row for row in result["months"] if (row["year"], row["month"]) == (2023, 7)
        )
        assert july["spi"][0] == pytest.approx(
            spi_values(np.array([_sum(2023, 7)]), alpha, beta, zero)[0]
        )
        assert july["percent_of_normal"] == pytest.approx(
            100 * _sum(2023, 7) / _mean(julys)
        )
        # the 3-month sums of January and February 2019 reach before the reference
        assert [f["n_values"] for f in result["period"]["scales"][1]["fits"]] == [
            2,
            2,
            *[3] * 10,
        ]
        whole = _result("meteo spi", **options)
        assert whole["period"] == result["period"]

    def test_heavy_thresholds_are_percentiles_of_the_reference_wet_days(self):
        dates = _days("2001-01-01", 4 * 365 + 1)  # 2001-2004
        values = [0.0] * len(dates)
        for day in range(0, len(dates), 3):
            scale = 1.0 if dates[day] < "2003" else 2.0
            values[day] = float(day % 40) * scale + 1.0
        result = _result(
            "meteo precipitation",
            index="heavy",
            dates=dates,
            precipitation_mm=values,
            first_year=2003,
            reference_first_year=2001,
            reference_last_year=2002,
        )
        wet = sorted(v for d, v in zip(dates, values, strict=True) if d < "2003" and v)
        h = (len(wet) + 1 / 3) * 0.95 + 1 / 3  # quantile type 8 by hand
        low = math.floor(h)
        p95 = wet[low - 1] + (h - low) * (wet[low] - wet[low - 1])
        assert result["period"]["wet_days"] == len(wet)
        assert result["period"]["thresholds_mm"][0] == pytest.approx(p95)
        mine = [v for d, v in zip(dates, values, strict=True) if d[:4] == "2003" and v]
        year = result["years"][0]
        assert year["year"] == 2003
        assert year["sums_mm"][0] == pytest.approx(sum(v for v in mine if v > p95))
        assert year["shares_percent"][0] == pytest.approx(
            100 * sum(v for v in mine if v > p95) / sum(mine)
        )

    def test_too_few_wet_days_in_the_reference_period(self):
        dates = _days("2001-01-01", 3 * 365)  # 2001-2003
        values = [5.0 if n % 2 and n >= 365 else 0.0 for n in range(len(dates))]
        values[10:40] = [5.0] * 30  # 30 wet days in 2001
        with pytest.raises(CalculationError) as caught:
            run_command(
                "meteo precipitation",
                {
                    "index": "heavy",
                    "dates": dates,
                    "precipitation_mm": values,
                    "reference_first_year": 2001,
                    "reference_last_year": 2001,
                },
            )
        assert caught.value.details == {
            "reason": "too_few_wet_days",
            "count": 30,
            "minimum": 100,
        }

    def test_the_seasonality_of_the_period_is_the_regime_of_the_reference(self):
        options = {"index": "seasonality", "input_file": FILE}
        own = _result("meteo precipitation", **options)
        other = _result(
            "meteo precipitation",
            reference_first_year=2019,
            reference_last_year=2021,
            **options,
        )
        normals = [
            _mean([_sum(year, month) for year in REFERENCE]) for month in range(1, 13)
        ]
        total = math.fsum(normals)
        assert [m["share_percent"] for m in other["period"]["months"]] == pytest.approx(
            [100 * value / total for value in normals]
        )
        assert other["period"]["pci"] == pytest.approx(
            100 * math.fsum(value**2 for value in normals) / total**2
        )
        assert other["years"] == own["years"]
        assert other["period"]["mean_pci"] == own["period"]["mean_pci"]

    @pytest.mark.parametrize(
        ("command", "options", "own"),
        [
            (
                "meteo precipitation",
                {"index": "sums"},
                lambda r: (
                    [
                        (y["year"], y["total_mm"], [m["total_mm"] for m in y["months"]])
                        for y in r["years"]
                    ]
                    + [r["period"]["mean_mm"], r["period"]["std_mm"]]
                ),
            ),
            (
                "meteo precipitation",
                {"index": "heavy"},
                lambda r: [(y["year"], y["wet_day_total_mm"]) for y in r["years"]],
            ),
            (
                "meteo spi",
                {"scales_months": [1]},
                lambda r: (
                    [m["total_mm"] for m in r["months"]]
                    + [y["total_mm"] for y in r["years"]]
                ),
            ),
            (
                "meteo temperature",
                {"index": "means"},
                lambda r: (
                    [(y["year"], y["tmean_c"], y["max_c"]) for y in r["years"]]
                    + [r["period"]["tmean_c"]]
                ),
            ),
        ],
    )
    def test_the_analysed_years_keep_their_values(self, command, options, own):
        first = _result(
            command,
            input_file=FILE,
            reference_first_year=2019,
            reference_last_year=2021,
            **options,
        )
        second = _result(
            command,
            input_file=FILE,
            reference_first_year=2021,
            reference_last_year=2023,
            **options,
        )
        assert own(first) == own(second)
        assert first["period"] != second["period"]


class TestTheReferencePeriodOfARecord:
    """Its years count whether the record covers them; it keeps its own days."""

    def test_a_normal_needs_eighty_percent_of_the_years_of_the_reference(self):
        dates = _days("2001-01-01", 1826)  # 2001-2005, 2004 a leap year
        options = {"index": "sums", "dates": dates, "precipitation_mm": [1.0] * 1826}
        four_of_five = run_command(
            "meteo precipitation",
            {**options, "reference_first_year": 2000, "reference_last_year": 2004},
        )
        assert four_of_five.result.period.normal_mm == pytest.approx(365.25)
        assert four_of_five.result.reference_period_years == 4
        four_of_six = run_command(
            "meteo precipitation",
            {**options, "reference_first_year": 1999, "reference_last_year": 2004},
        )
        assert four_of_six.result.period.normal_mm is None
        details = {n.code: n.details for n in four_of_six.notices}
        assert details["normal_not_computed"] == {
            "years": 4,
            "required": 5,
            "first_year": 1999,
            "last_year": 2004,
        }

    def test_an_spi_fit_needs_eighty_percent_of_the_years_of_the_reference(self):
        dates = _days("2001-01-01", 1826)
        values = [((n * 7) % 11) / 10 for n in range(1826)]
        options = {"dates": dates, "precipitation_mm": values, "scales_months": [1]}
        fitted = _result(
            "meteo spi", reference_first_year=2000, reference_last_year=2004, **options
        )
        assert all(fit["alpha"] for fit in fitted["period"]["scales"][0]["fits"])
        output = run_command(
            "meteo spi",
            {**options, "reference_first_year": 1999, "reference_last_year": 2004},
        )
        fits = output.result.period.scales[0].fits
        assert [(fit.alpha, fit.n_values) for fit in fits] == [(None, 4)] * 12
        assert {month.spi[0] for month in output.result.months} == {None}
        notice = next(n for n in output.notices if n.code == "spi_not_fitted")
        assert notice.details == {"scale_months": 1, "months": list(range(1, 13))}

    def test_each_period_keeps_the_days_of_its_own_years(self):
        dates = _days("2000-01-01", 3 * 365 + 1)  # 2000-2002, 2000 a leap year
        result = precipitation_sums(
            [1.0] * len(dates),
            dates,
            reference_first_year=2001,
            reference_last_year=2002,
        )
        # DJF of 2001 needs December 2000: in the analysed years, not the reference
        assert result.years[1].djf_mm == 90.0
        assert result.period.djf_normal_mm is None
        assert result.period.mam_normal_mm == 92.0

    def test_a_reference_period_has_its_own_short_period_notice(self):
        options = {"index": "means", "input_file": FILE}
        own = run_command("meteo temperature", options)
        other = run_command(
            "meteo temperature",
            {**options, "reference_first_year": 2019, "reference_last_year": 2021},
        )

        def short(output) -> list:
            return [
                n.details for n in output.notices if n.code == "short_reference_period"
            ]

        period = {"years": 5, "first_year": 2019, "last_year": 2023, "minimum": 30}
        assert short(own) == [period]
        assert short(other) == [
            period,
            {"years": 3, "first_year": 2019, "last_year": 2021, "minimum": 30},
        ]


class TestErrorsOfTheReferencePeriod:
    """``range``, ``no_values_in_period`` and ``not_applicable``."""

    def test_a_reference_period_that_ends_before_it_begins(self):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "meteo spi",
                {
                    "input_file": FILE,
                    "reference_first_year": 2021,
                    "reference_last_year": 2020,
                },
            )
        assert caught.value.details == {
            "option": "reference_first_year",
            "reason": "range",
            "first_year": 2021,
            "last_year": 2020,
        }
        with pytest.raises(InvalidParameterError) as caught:
            run_command(
                "meteo temperature",
                {"index": "means", "input_file": FILE, "reference_last_year": 2010},
            )
        assert caught.value.details["option"] == "reference_first_year"
        assert (
            caught.value.details["first_year"],
            caught.value.details["last_year"],
        ) == (
            2019,
            2010,
        )

    def test_a_reference_period_without_a_value(self):
        with pytest.raises(CalculationError) as caught:
            run_command(
                "meteo precipitation",
                {
                    "index": "sums",
                    "input_file": FILE,
                    "reference_first_year": 1991,
                    "reference_last_year": 2000,
                },
            )
        assert caught.value.details == {
            "reason": "no_values_in_period",
            "option": "reference_first_year",
            "first_year": 1991,
            "last_year": 2000,
            "available": [2019, 2023],
        }

    @pytest.mark.parametrize(
        ("command", "index", "option", "value"),
        [
            ("meteo precipitation", "maxima", "reference_first_year", 2019),
            ("meteo precipitation", "intensity", "reference_last_year", 2021),
            ("meteo precipitation", "sums", "durations_days", [2]),
            ("meteo precipitation", "maxima", "thresholds_mm", [1.0]),
            ("meteo precipitation", "days", "wet_day_mm", 1.0),
            ("meteo precipitation", "intensity", "percentiles", [95.0]),
            ("meteo temperature", "days", "reference_first_year", 2019),
            ("meteo temperature", "means", "frost_tmin_c", 0.0),
            ("meteo temperature", "degree_days", "hot_tmax_c", 30.0),
            ("meteo temperature", "range", "growing_base_c", 5.0),
            ("meteo temperature", "days", "heating_limit_c", 15.0),
        ],
    )
    def test_an_option_of_another_index_is_not_applicable(
        self, command, index, option, value
    ):
        with pytest.raises(InvalidParameterError) as caught:
            run_command(command, {"index": index, "input_file": FILE, option: value})
        assert caught.value.details == {"option": option, "reason": "not_applicable"}

    def test_the_operation_fills_the_documented_default_of_its_index(self):
        def run(command: str, index: str) -> dict:
            return _result(command, index=index, input_file=FILE)

        assert run("meteo precipitation", "maxima")["durations_days"] == [
            1,
            2,
            3,
            5,
            10,
        ]
        assert run("meteo precipitation", "days")["thresholds_mm"] == [0.1, 1, 10, 20]
        heavy = run("meteo precipitation", "heavy")
        assert (heavy["wet_day_mm"], heavy["percentiles"]) == (1.0, [95.0, 99.0])
        days = run("meteo temperature", "days")
        assert [days[name] for name in ("frost_tmin_c", "summer_tmax_c")] == [0, 25]
        bases = run("meteo temperature", "degree_days")
        assert [bases[f"{name}_c"] for name in ("growing_base", "heating_base")] == [
            5,
            18,
        ]


class TestExactSums:
    """A sum of 0.1-mm values is the number of its decimal value: equal sums tie."""

    def test_sums_equal_in_decimal_are_equal_numbers(self):
        dates = _days("2001-01-01", 3 * 365)  # 2001-2003
        values = [0.0] * len(dates)
        values[0], values[1] = 0.1, 0.2  # 0.1 + 0.2 = 0.30000000000000004 in binary
        values[365] = 0.3
        values[730] = 0.4
        series = {"dates": dates, "precipitation_mm": values}
        sums = _result("meteo precipitation", index="sums", **series)
        assert [year["total_mm"] for year in sums["years"]] == [0.3, 0.3, 0.4]
        assert sums["years"][0]["months"][0]["total_mm"] == 0.3
        assert sums["years"][0]["djf_mm"] is None  # December 2000 is not there
        assert sums["years"][1]["djf_mm"] == 0.3
        spi = _result("meteo spi", scales_months=[1], **series)
        assert [year["total_mm"] for year in spi["years"]] == [0.3, 0.3, 0.4]
        intensity = _result(
            "meteo precipitation", index="intensity", wet_day_mm=0.1, **series
        )
        assert [year["wet_day_total_mm"] for year in intensity["years"]] == [
            0.3,
            0.3,
            0.4,
        ]

    def test_the_sums_of_the_fixture_are_their_decimal_values(self):
        result = _result("meteo precipitation", index="sums", input_file=FILE)
        totals = {year["year"]: year["total_mm"] for year in result["years"]}
        assert totals[2020] == 736.7  # summed in binary: 736.6999999999999
        for year in result["years"]:
            sums = [year[key] for key in ("total_mm", "winter_mm", "summer_mm")]
            sums += [month["total_mm"] for month in year["months"]]
            assert [
                round(value, 1) if value is not None else None for value in sums
            ] == sums


class TestSpiMonths:
    """A month of ``meteo spi`` names its year of ``year_type`` and its month."""

    def test_november_belongs_to_the_next_hydrological_year(self):
        result = _result(
            "meteo spi", input_file=FILE, scales_months=[1], year_type="hydrological"
        )
        months = [(row["year"], row["month"]) for row in result["months"]]
        assert months[:12] == [(2019, month) for month in range(1, 11)] + [
            (2020, 11),
            (2020, 12),
        ]
        assert {year for year, _ in months} == {row["year"] for row in result["years"]}
