"""The monthly estimators and the characteristic values against specs and sources.

The four Tier A formulas of :mod:`hydrolog.statistics.characteristic` (the standard
deviation, coefficient of variation and skewness of a month's values and the
half-width of the interval of its long-term mean) get the range, type and property
tests generated from their specs (Nogat CMP-6.5), the exact rational oracles and
closed forms of their limits (CMP-6.2) and NIST's certified standard deviations and
interval of ZARR13.DAT as reference cases (CMP-6.1). The Tier B formulas, the
hydrological year of IMGW-PIB and the characteristic values, are checked against the
cases of IMGW-PIB's public data and yearbooks in
``tests/fixtures/formulas/characteristic-cases.json``, on the station files of
``tests/oracles/characteristic/`` (IMGW-PIB's data, processed: its attribution lies
beside them); the reference module asserts Tier A cases only, so these are compared
here within the printed precision of their source.
"""

import csv
import math
import statistics
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given
from numpy.typing import NDArray
from scipy.stats import skew, variation
from scipy.stats import t as t_dist

from hydrolog._formula_versions import recording
from hydrolog._formulas import DELEGATED, ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics._hydrological_year import (
    days_in_hydrological_year,
    hydrological_day_of_year,
    hydrological_year,
    hydrological_year_start,
)
from hydrolog.statistics.characteristic import (
    COEFFICIENT_OF_VARIATION,
    MEAN_INTERVAL,
    SKEWNESS,
    SPECS,
    STANDARD_DEVIATION,
    HalfYearPart,
    HalfYearValues,
    annual_extremes_from_half_years,
    calculate_characteristic_values,
    calculate_daily_statistics,
    characteristic_values_from_half_years,
    coefficient_of_variation,
    fisher_pearson_skewness,
    mean_interval_half_width,
    sample_standard_deviation,
)

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "characteristic-cases.json"
ORACLES = ROOT / "tests" / "oracles" / "characteristic"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (STANDARD_DEVIATION, sample_standard_deviation),
    (COEFFICIENT_OF_VARIATION, coefficient_of_variation),
    (SKEWNESS, fisher_pearson_skewness),
    (MEAN_INTERVAL, mean_interval_half_width),
)
NAMES = [spec.name for spec, _ in FAMILY]


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


def _published() -> list[object]:
    return [
        pytest.param(spec, function, case, id=f"{spec.name}-{case.case_id}")
        for spec, function in FAMILY
        for case in load_cases(CASES, spec.name)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(("spec", "function", "case"), _published())
def test_reference_cases(spec: FormulaSpec, function, case: ReferenceCase):
    assert_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, function, ERRORS)


@given(inputs=strategies(STANDARD_DEVIATION))
def test_standard_deviation_properties(inputs):
    function = sample_standard_deviation
    assert_property_contract(STANDARD_DEVIATION, function, inputs, ERRORS)
    assert_properties(STANDARD_DEVIATION, function, inputs, ERRORS)


@given(inputs=strategies(COEFFICIENT_OF_VARIATION))
def test_coefficient_of_variation_properties(inputs):
    function = coefficient_of_variation
    assert_property_contract(COEFFICIENT_OF_VARIATION, function, inputs, ERRORS)
    assert_properties(COEFFICIENT_OF_VARIATION, function, inputs, ERRORS)


@given(inputs=strategies(SKEWNESS))
@example(inputs={"values": np.array([4.93359375, 5.0, 475711.0, 475711.0])}).via(
    "discovered failure: numpy.power's vector pow cubed the deviations of the sample "
    "and of its negation an ulp apart, of a skewness near 0 by cancellation"
)
def test_skewness_properties(inputs):
    assert_property_contract(SKEWNESS, fisher_pearson_skewness, inputs, ERRORS)
    assert_properties(SKEWNESS, fisher_pearson_skewness, inputs, ERRORS)


@given(inputs=strategies(MEAN_INTERVAL))
def test_mean_interval_properties(inputs):
    assert_property_contract(MEAN_INTERVAL, mean_interval_half_width, inputs, ERRORS)
    assert_properties(MEAN_INTERVAL, mean_interval_half_width, inputs, ERRORS)


SAMPLES = (
    [8.25, 7.86, 7.72, 7.75, 7.6, 7.47, 7.35, 7.35, 7.12, 6.99],
    [4.93, 96.0, 12.4, 19.1, 8.65, 31.7, 62.6, 5.2],
    list(np.random.default_rng(20261119).lognormal(2.5, 0.8, 400)),
)


@pytest.mark.parametrize("sample", SAMPLES, ids=["klodzko", "extremes", "lognormal"])
def test_the_estimators_are_numpys_and_scipys(sample):
    """CMP-6.3: numpy.std(ddof=1), scipy.stats.variation(ddof=1) and skew(bias=True),
    the conventions of the specs (the divisors n - 1 of s and n of the moments)."""
    reason = "the same definitions summed in another order: a few ulp of each sum"
    assert_within(
        sample_standard_deviation(sample),
        np.std(sample, ddof=1),
        rel=1e-13,
        reason=reason,
    )
    assert_within(
        coefficient_of_variation(sample),
        variation(sample, ddof=1),
        rel=1e-13,
        reason=reason,
    )
    assert_within(
        fisher_pearson_skewness(sample),
        skew(sample, bias=True),
        abs=1e-12,
        reason=reason + "; the third moment of both signs cancels",
    )


def test_the_delegated_t_quantile_is_a_known_one():
    """CMP-1.2: scipy.stats.t.isf, the smoke case of ``student_t_quantile``."""
    (delegated,) = [d for d in DELEGATED if d.name == "student_t_quantile"]

    assert delegated.library == "scipy.stats.t.isf"
    assert_within(
        t_dist.isf(0.025, 1),
        math.tan(0.475 * math.pi),
        rel=1e-13,
        reason="the Cauchy quantile in closed form; tan rounds a few ulp",
    )
    assert_within(
        t_dist.isf(0.025, 194),
        1.9723,
        abs=5e-5,
        reason="NIST e-Handbook sect. 1.3.5.2 prints t(0.975, 194) to 4 decimals",
    )


def _exact_std(values: list[float]) -> float:
    exact = [Fraction(value) for value in values]
    mean = sum(exact, Fraction(0)) / len(exact)
    square = sum(((v - mean) ** 2 for v in exact), Fraction(0)) / (len(exact) - 1)
    return math.sqrt(square)


@pytest.mark.parametrize(
    "values",
    [[3.0, 5.0], [0.0, 0.0, 3.0], [2.5, 2.5, 2.5, 4.0], [0.0, 7.0, 7.0, 7.0, 0.0]],
    ids=["two_values", "zeros", "ties", "zeros_and_ties"],
)
def test_small_samples_with_ties_and_zeros(values):
    """CMP-6.7: the definitions on two values, zeros and ties, rationally."""
    exact = _exact_std(values)
    mean = statistics.fmean(values)
    exact_moments = [Fraction(v) - Fraction(mean) for v in values]
    m2 = sum((d**2 for d in exact_moments), Fraction(0)) / len(values)
    m3 = sum((d**3 for d in exact_moments), Fraction(0)) / len(values)
    reason = "the exact rational statistics, rounded once to a float and once more"

    assert_within(sample_standard_deviation(values), exact, rel=1e-15, reason=reason)
    assert_within(
        coefficient_of_variation(values), exact / mean, rel=1e-15, reason=reason
    )
    assert_within(
        fisher_pearson_skewness(values),
        math.copysign(math.sqrt(m3**2 / m2**3), m3),
        abs=1e-15,
        reason=reason,
    )
    assert_within(
        mean_interval_half_width(values, 0.95),
        float(t_dist.isf(0.025, len(values) - 1)) * exact / math.sqrt(len(values)),
        rel=1e-15,
        reason=reason,
    )


@pytest.mark.parametrize(
    ("function", "values", "constraint"),
    [
        (sample_standard_deviation, [12.5], "enough_values"),
        (coefficient_of_variation, [0.0, 0.0, 0.0], "positive_mean"),
        (fisher_pearson_skewness, [12.5, 12.5, 12.5], "values_not_all_equal"),
    ],
    ids=["one_value", "all_zero", "constant"],
)
def test_undefined_statistics_are_refused(function, values, constraint):
    """CMP-6.7: one value, a mean of zero and a constant series, before dividing."""
    with pytest.raises(InvalidParameterError) as caught:
        function(values)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == constraint


def test_a_constant_series_has_no_spread():
    """CMP-6.7: equal values have s = 0, Cv = 0 and an interval of no width."""
    assert sample_standard_deviation([12.5] * 30) == 0.0
    assert coefficient_of_variation([12.5] * 30) == 0.0
    assert mean_interval_half_width([12.5] * 30, 0.95) == 0.0


def test_a_level_next_to_one_has_a_finite_half_width():
    """Trap singular_at_bound: the quantile grows without bound as c nears 1.

    At the largest float below 1 the tail (1 - c) / 2 = 2**-54 is exact; the Cauchy
    quantile cot(pi 2**-54) is 2**54 / pi to far below an ulp. The quantile of
    1 - tail, as the code took it before 0.9.0, is that of 1 and infinite.
    """
    level = math.nextafter(1.0, 0.0)

    assert_within(
        mean_interval_half_width([100.0, 102.0], level),
        2.0**54 / math.pi,
        rel=1e-13,
        reason="cot x = 1/x - x/3 at x = pi 2**-54: the second term is 1e-32 of the "
        "first; scipy's Cauchy quantile of a tiny tail rounds a few ulp",
    )


def test_the_formulas_record_their_versions():
    with recording() as used:
        sample_standard_deviation([1.0, 2.0])
        coefficient_of_variation([1.0, 2.0])
        fisher_pearson_skewness([1.0, 2.0, 4.0])
        mean_interval_half_width([1.0, 2.0], 0.95)

    assert used == {spec.name: spec.formula_version for spec in SPECS}


# --- Tier B: the hydrological year and the characteristic values -------------------


def _case(formula: str, case_id: str) -> ReferenceCase:
    (found,) = [c for c in load_cases(CASES, formula) if c.case_id == case_id]
    return found


def _within_print(case: ReferenceCase, name: str, actual: float) -> None:
    """Assert an output within half a unit of its printed digit and the tolerance."""
    expected = float(case.expected[name])  # type: ignore[arg-type]
    allowed = case.printed_precision.get(name, 0.0) / 2
    if case.tolerance is not None:
        allowed += (case.tolerance.abs or 0.0) + (case.tolerance.rel or 0.0) * abs(
            expected
        )
    assert_within(
        actual,
        expected,
        abs=allowed,
        reason=f"{case.case_id}: half a unit of the printed {name} (CMP-6.1)",
    )


def test_the_hydrological_calendar_is_imgw_pibs():
    dates = np.array(
        _case("hydrological_year", "imgw_hydrological_year_calendar").inputs["dates"],
        dtype="datetime64[D]",
    )
    year = _case("hydrological_year", "imgw_hydrological_year_calendar")
    day = _case("hydrological_day_of_year", "imgw_hydrological_year_calendar")
    length = _case("days_in_hydrological_year", "imgw_hydrological_year_calendar")
    start = _case("hydrological_year_start", "imgw_year_and_half_year_starts")

    assert hydrological_year(dates).tolist() == year.expected["hydrological_year"]
    assert hydrological_day_of_year(dates).tolist() == day.expected["day_of_year"]
    years = np.array(length.inputs["years"])
    assert days_in_hydrological_year(years).tolist() == length.expected["days_in_year"]
    starts = [str(hydrological_year_start(y)) for y in start.inputs["years"]]
    assert starts == start.expected["start"]


def _rows(name: str) -> list[dict[str, str]]:
    with (ORACLES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _daily_flows() -> tuple[NDArray[np.float64], NDArray[np.datetime64]]:
    """The daily discharges of a CODZ file, by calendar date."""
    days, flows = [], []
    for row in _rows("imgw_150160180_codz_2010.csv"):
        hydro, month = int(row["COROKH"]), int(row["COMSCK"])
        year = hydro - 1 if month >= 11 else hydro
        days.append(f"{year:04d}-{month:02d}-{int(row['CODZIEN']):02d}")
        flows.append(float(row["COPRZP"]))
    dates = np.array(days, dtype="datetime64[D]")
    order = np.argsort(dates)
    return np.array(flows)[order], dates[order]


def _half_years(name: str) -> HalfYearValues:
    """IMGW-PIB's half-year characteristics of a POLR file.

    PLWSKP 13 is the winter, 14 the summer, 15 the year; PLWSKEX 1 the minimum, 2 the
    mean, 3 the maximum; a repeated extremum keeps the date of its first row, and an
    extremum dated by its month alone (repeated on many days) has no date.
    """
    found: dict[int, dict[tuple[str, str], tuple[float, str | None]]] = {}
    for row in _rows(name):
        value = float(row["PLWLKS"])
        if value >= 99999.0:  # a break in observations
            continue
        start = (row["PLRKKLOD"], row["PLMCOD"], row["PLDZOD"])
        date = (
            "{:04d}-{:02d}-{:02d}".format(*(int(part) for part in start))
            if all(part.strip() for part in start)
            else None
        )
        key = (row["PLWSKP"].strip(), row["PLWSKEX"].strip())
        found.setdefault(int(row["PLROKH"]), {}).setdefault(key, (value, date))
    years = sorted(found)
    blank: tuple[float, str | None] = (math.nan, None)

    def values(part: str, kind: str) -> NDArray[np.float64]:
        return np.array([found[y].get((part, kind), blank)[0] for y in years])

    def dates(part: str, kind: str) -> tuple[str | None, ...]:
        return tuple(found[y].get((part, kind), blank)[1] for y in years)

    def half(part: str) -> HalfYearPart:
        return HalfYearPart(
            values(part, "1"),
            values(part, "2"),
            values(part, "3"),
            dates(part, "1"),
            dates(part, "3"),
        )

    return HalfYearValues(
        np.array(years, dtype=np.int64), half("13"), half("14"), values("15", "2")
    )


def test_the_daily_means_of_klodzko_are_imgw_pibs():
    case = _case(
        "characteristic_first_degree", "imgw_klodzko_hy2010_means_daily_vs_published"
    )
    flows, dates = _daily_flows()

    (year,) = calculate_characteristic_values(flows, dates, "Q").years

    _within_print(case, "SQ_winter", year.winter.mean or math.nan)
    _within_print(case, "SQ_summer", year.summer.mean or math.nan)
    _within_print(case, "SQ_year", year.annual.mean or math.nan)
    assert (year.winter.days, year.summer.days, year.annual.days) == (
        case.expected["days_winter"],
        case.expected["days_summer"],
        case.expected["days_year"],
    )
    assert year.annual.days_with_data == year.annual.days


def test_the_daily_extremes_of_klodzko_are_milder_than_imgw_pibs():
    """The declared discrepancy (CMP-5.2) holds as its cause says: IMGW-PIB's
    extremes are of all observations, so they bound those of the daily means."""
    case = _case(
        "characteristic_first_degree",
        "imgw_klodzko_hy2010_extremes_daily_vs_published",
    )
    flows, dates = _daily_flows()

    (year,) = calculate_characteristic_values(flows, dates, "Q").years

    assert case.status == "discrepancy"
    published = case.expected
    assert (year.summer.max or 0.0) < published["WQ_summer"]
    assert (year.winter.max or 0.0) < published["WQ_winter"]
    assert (year.winter.min or 0.0) > published["NQ_winter"]
    assert (year.summer.min or 0.0) > published["NQ_summer"]


def test_the_half_years_of_klodzko_give_imgw_pibs_annual_values():
    case = _case("characteristic_from_half_years", "imgw_klodzko_hy2010_half_years")

    result = characteristic_values_from_half_years(
        _half_years("imgw_150160180_polr_Q_2010.csv"), "Q"
    )

    (year,) = result.years
    assert (year.annual.max, year.annual.max_date) == (
        case.expected["WQ_year"],
        case.expected["WQ_year_date"],
    )
    assert (year.annual.min, year.annual.min_date) == (
        case.expected["NQ_year"],
        case.expected["NQ_year_date"],
    )
    assert year.annual.mean == case.expected["SQ_year"]
    assert year.winter.max == case.expected["WQ_winter"]
    assert year.summer.min == case.expected["NQ_summer"]


def test_the_annual_stages_of_the_yearbook_are_the_larger_half_year_maximum():
    case = _case(
        "characteristic_from_half_years", "rh2024_raciborz_miedonia_half_years"
    )
    winter, summer = case.inputs["winter"], case.inputs["summer"]

    def part(values: dict[str, float]) -> HalfYearPart:
        return HalfYearPart(
            np.array([values["min"]]),
            np.array([values["mean"]]),
            np.array([values["max"]]),
            (None,),
            (None,),
        )

    half = HalfYearValues(
        np.array([2024]),
        part(winter),
        part(summer),
        np.array([case.inputs["annual_mean"]], dtype=np.float64),
    )
    (year,) = characteristic_values_from_half_years(half, "H").years

    assert year.annual.max == case.expected["WW_year"]
    assert year.annual.min == case.expected["NW_year"]
    assert year.annual.mean == case.expected["SW_year"]


def test_the_second_degree_of_klodzko_1971_2015_is_exact():
    """The annual maxima, means and minima of IMGW-PIB's half-years of 1971-2015 (no
    hydrological year 1997 in the file): the larger half-year maximum and the smaller
    minimum taken here row by row, their highest, mean, median and lowest by the
    statistics module and exact fractions."""
    half = _half_years("imgw_150160180_polr_Q_1971_2015.csv")
    result = characteristic_values_from_half_years(half, "Q")
    maxima = annual_extremes_from_half_years(half, "max")
    both = np.isfinite(half.winter.max) & np.isfinite(half.summer.max)
    oracle = {
        "w": [max(w, s) for w, s in zip(half.winter.max, half.summer.max, strict=True)],
        "s": half.annual_mean.tolist(),
        "n": [min(w, s) for w, s in zip(half.winter.min, half.summer.min, strict=True)],
    }

    assert 1997 not in half.years.tolist() and half.years.size == 44
    assert maxima.years.tolist() == half.years[both].tolist()
    assert maxima.values.tolist() == [
        v for v, b in zip(oracle["w"], both, strict=True) if b
    ]
    for letter, annual in oracle.items():
        known = [float(v) for v in annual if math.isfinite(v)]
        exact_mean = float(sum(map(Fraction, known), Fraction(0)) / len(known))
        assert getattr(result, f"w{letter}x") == max(known)
        assert getattr(result, f"n{letter}x") == min(known)
        assert getattr(result, f"z{letter}x") == statistics.median(known)
        assert_within(
            getattr(result, f"s{letter}x"),
            exact_mean,
            rel=1e-15,
            reason="the exact mean of 44 values against numpy's pairwise sum: a few "
            "ulp",
        )


def test_a_day_of_the_hydrological_year_after_february_pools_two_dates():
    """The day numbering of ``stats daily`` (research finding 9, documented): day 121
    is 29 February of a leap year and 1 March of a common one, day 366 holds the
    31 October of leap years only."""
    dates = np.array(
        ["2020-02-29", "2021-03-01", "2020-03-01", "2020-10-31", "2021-10-31"],
        dtype="datetime64[D]",
    )

    result = calculate_daily_statistics(np.array([1.0, 2.0, 3.0, 4.0, 5.0]), dates)

    assert result.day_of_year.tolist() == [121.0, 122.0, 365.0, 366.0]
    assert result.mean_values.tolist() == [1.5, 3.0, 5.0, 4.0]
    assert result.count.tolist() == [2.0, 1.0, 1.0, 1.0]
