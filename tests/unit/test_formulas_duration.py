"""The median annual flow-duration curve and its interval against the standard (CMP §6).

The spec ``duration_curve_annual_median_interval`` takes the values of the annual
curves of the complete hydrological years (Vogel and Fennessey 1994) and gives per
percentage their median and, per confidence level, the pair of order statistics whose
binomial coverage is at least the level. Its range, type and property tests are
generated from the spec (CMP-6.5), with the generated properties of an interval on
drawn samples with ties (``assert_interval_properties``, CMP-6.11); its limits hold
the binomial coverage in exact rational arithmetic (CMP-6.2); its reference case is
the interval of the median of Helsel and Hirsch (2002, CMP-6.1); SciPy's
``quantile_test`` is its established oracle (CMP-6.3); its simulated coverage runs
nightly (``test_coverage_duration.py``).

``duration_curve`` builds the annual curves from a daily series (Tier B
``annual_duration_curves``): its median annual curve and intervals are compared with
the spec applied to the curves of the complete years chosen here with ``datetime``,
and a level the complete years cannot reach is not computed, with the notice.
"""

import math
import warnings
from datetime import date, timedelta
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given
from scipy import stats

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog._warnings import IntervalNotComputed
from hydrolog.nogat_formulas import (
    Case,
    ReferenceCase,
    assert_case,
    assert_interval_properties,
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
from hydrolog.statistics.duration import (
    CURVE_PERCENTS,
    DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL,
    annual_median_interval,
    duration_curve,
    exceedance_values,
)

pytestmark = pytest.mark.formula

SPEC = DURATION_CURVE_ANNUAL_MEDIAN_INTERVAL
CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "duration-cases.json"
SEED = 20261125
LEVELS = (0.68, 0.95)


def _bounds(sample: np.ndarray, levels: tuple[float, ...]) -> list:
    """The interval of :func:`assert_interval_properties`: (lower, upper) per level."""
    found = annual_median_interval(sample, list(levels))
    return list(zip(found.lower, found.upper, strict=True))


# --- the spec (Tier A) ---------------------------------------------------------------


@pytest.mark.parametrize("case", range_cases(SPEC) + type_cases(SPEC))
def test_ranges_and_types(case: Case):
    run_case(SPEC, annual_median_interval, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(SPEC, annual_median_interval, ERRORS)


@given(inputs=strategies(SPEC))
def test_properties(inputs):
    assert_property_contract(SPEC, annual_median_interval, inputs, ERRORS)
    assert_properties(SPEC, annual_median_interval, inputs, ERRORS)


@st.composite
def annual_samples(draw) -> dict[str, np.ndarray]:
    """1 to 60 years of 1 to 4 percentages with ties, zeros and stages below the
    gauge's zero, and 1 to 4 distinct levels anywhere in (0, 1): the generic strategy
    draws mostly levels that repeat, which the spec refuses."""
    years = draw(st.integers(min_value=1, max_value=60))
    percents = draw(st.integers(min_value=1, max_value=4))
    value = st.one_of(
        st.sampled_from([0.0, 1.24, 4.93, 96.0, 522.0, -35.0]),
        st.floats(min_value=-1.0e6, max_value=1.0e6),
    )
    size = years * percents
    values = draw(st.lists(value, min_size=size, max_size=size))
    level = st.floats(min_value=0.0, max_value=1.0, exclude_min=True, exclude_max=True)
    levels = draw(st.lists(level, min_size=1, max_size=4, unique=True))
    return {
        "annual_values": np.array(values).reshape(years, percents),
        "confidence_levels": np.array(levels),
    }


@given(inputs=annual_samples())
def test_properties_of_samples_with_ties(inputs):
    assert_property_contract(SPEC, annual_median_interval, inputs, ERRORS)
    assert_properties(SPEC, annual_median_interval, inputs, ERRORS)
    assert_interval_properties(
        _bounds, inputs["annual_values"], tuple(inputs["confidence_levels"].tolist())
    )


@pytest.mark.parametrize(
    "case", load_cases(CASES, SPEC.name), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(SPEC, annual_median_interval, case, ERRORS)


def test_the_interval_is_scipys_quantile_test():
    """SciPy's two-sided interval of the quantile 0.5 takes the same order statistics,
    except at a level equal to a coverage, which uniform draws do not meet."""
    rng = np.random.default_rng(SEED)
    for years in (2, 3, 5, 6, 9, 13, 21, 30, 34, 55, 60, 89):
        sample = np.exp(rng.normal(2.0, 0.8, (years, 3)))
        levels = [0.68, 0.9, 0.95, 0.99, *rng.uniform(0.5, 0.999, 4).tolist()]

        found = annual_median_interval(sample, levels)

        for column in range(3):
            test = stats.quantile_test(sample[:, column], q=0.0, p=0.5)
            for row, level in enumerate(levels):
                interval = test.confidence_interval(confidence_level=level)
                assert_within(
                    [found.lower[row, column], found.upper[row, column]],
                    [interval.low, interval.high],
                    abs=0.0,
                    reason="both are values of the sample, NaN for a level the "
                    "years cannot reach",
                )
        assert_within(
            found.median,
            np.median(sample, axis=0),
            abs=0.0,
            reason="the middle value, or the two middle values halved and summed, "
            "as numpy's mean of them rounds them",
        )


def test_values_near_the_largest_float_do_not_overflow():
    """The mean of two middle values of 1.7e308 is their sum of halves, not inf."""
    found = annual_median_interval([[1.7e308], [-1.0], [1.7e308], [1.7e308]], [0.5])

    assert_within(
        found.median, [1.7e308], abs=0.0, reason="two exact halves summed exactly"
    )


# --- the annual curves of a daily series (Tier B annual_duration_curves) ------------


def _daily(first: date, last: date) -> tuple[list[date], np.ndarray]:
    """Every day from ``first`` to ``last`` with a seeded flow [m3/s]."""
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    flows = np.round(np.random.default_rng(SEED).gamma(0.8, 12.0, len(days)), 3)
    return days, flows


def _hydrological_year(day: date) -> int:
    return day.year + 1 if day.month >= 11 else day.year


def _expected(
    days: list[date], flows: np.ndarray, month: int | None, levels: tuple[float, ...]
):
    """The spec applied to the curves of the complete years, chosen day by day."""
    chosen: dict[int, list[float]] = {}
    for day, flow in zip(days, flows, strict=True):
        if math.isfinite(flow) and (month is None or day.month == month):
            chosen.setdefault(_hydrological_year(day), []).append(float(flow))
    curves = []
    for year, values in sorted(chosen.items()):
        if month is None:
            needed = (date(year, 11, 1) - date(year - 1, 11, 1)).days
        else:
            start = date(year - 1 if month >= 11 else year, month, 1)
            needed = (
                date(start.year + start.month // 12, start.month % 12 + 1, 1) - start
            ).days
        if len(values) == needed:
            curves.append(exceedance_values(values, CURVE_PERCENTS))
    return len(curves), annual_median_interval(np.array(curves), list(levels))


def _same_intervals(result, expected, levels: tuple[float, ...]) -> None:
    assert_within(
        result.annual_median_values,
        expected.median,
        abs=0.0,
        reason="the same curves of the same years: the same arithmetic",
    )
    assert [i.confidence_level for i in result.intervals] == list(levels)
    for row, interval in enumerate(result.intervals):
        assert (interval.ci_method, interval.ci_samples) == ("order_statistics", None)
        assert_within(
            interval.ci_lower, expected.lower[row], abs=0.0, reason="values of a year"
        )
        assert_within(
            interval.ci_upper, expected.upper[row], abs=0.0, reason="values of a year"
        )


def test_the_median_annual_curve_takes_the_complete_years():
    """From 15 March 2013 to 31 October 2021: 2013 begins late, 2015 has a day
    without a value and 2017 a date absent; 2014, 2016 and 2020 (366 days, the leap
    years count every day), 2018, 2019 and 2021 are complete: six years, enough at
    0.95."""
    days, flows = _daily(date(2013, 3, 15), date(2021, 10, 31))
    flows[days.index(date(2015, 6, 1))] = math.nan
    kept = [i for i, day in enumerate(days) if day != date(2017, 1, 10)]
    days, flows = [days[i] for i in kept], flows[kept]
    complete, expected = _expected(days, flows, None, LEVELS)
    assert complete == 6

    with warnings.catch_warnings(), recording() as used:
        warnings.simplefilter("error", IntervalNotComputed)
        result = duration_curve(
            flows, np.array(days, dtype="datetime64[D]"), confidence_level=LEVELS
        )

    _same_intervals(result, expected, LEVELS)
    assert used["duration_curve_annual_median_interval"] == SPEC.formula_version


@pytest.mark.parametrize("month", [2, 11])
def test_a_month_takes_that_month_of_each_complete_year(month):
    """February of 2014 to 2021 but 2017, one day absent, with 29 days in 2016 and
    2020; November of 2013 to 2020, in the hydrological years 2014 to 2021, but 2018,
    one day without a value."""
    days, flows = _daily(date(2013, 11, 1), date(2021, 10, 31))
    flows[days.index(date(2018, 11, 5))] = math.nan
    kept = [i for i, day in enumerate(days) if day != date(2017, 2, 10)]
    days, flows = [days[i] for i in kept], flows[kept]
    complete, expected = _expected(days, flows, month, LEVELS)
    assert complete == 7

    result = duration_curve(
        flows,
        np.array(days, dtype="datetime64[D]"),
        month=month,
        confidence_level=LEVELS,
    )

    _same_intervals(result, expected, LEVELS)


def test_too_few_complete_years_leave_their_levels_not_computed():
    """Four complete years reach 0.68 (three needed), not 0.95 (six)."""
    days, flows = _daily(date(2015, 11, 1), date(2019, 10, 31))
    complete, expected = _expected(days, flows, None, (0.95, 0.68))
    assert complete == 4

    with pytest.warns(IntervalNotComputed) as caught:
        result = duration_curve(
            flows, np.array(days, dtype="datetime64[D]"), confidence_level=(0.95, 0.68)
        )

    assert [warning.message.details for warning in caught] == [
        {
            "reason": "too_few_complete_years",
            "confidence_levels": [0.95],
            "distribution": None,
            "fit_method": None,
            "return_periods": None,
            "complete_years": 4,
            "required_years": [6],
        }
    ]
    assert result.to_dict()["intervals"][0] == {
        "confidence_level": 0.95,
        "ci_method": None,
        "ci_lower": None,
        "ci_upper": None,
        "ci_samples": None,
    }
    computed = result.intervals[1]
    assert (computed.confidence_level, computed.ci_method) == (0.68, "order_statistics")
    for found, wanted in (
        (result.annual_median_values, expected.median),
        (computed.ci_lower, expected.lower[1]),
        (computed.ci_upper, expected.upper[1]),
    ):
        assert_within(found, wanted, abs=0.0, reason="values of the same four years")


def test_without_a_complete_year_the_median_annual_curve_is_null():
    days, flows = _daily(date(2020, 1, 1), date(2020, 7, 18))

    with pytest.warns(IntervalNotComputed) as caught:
        result = duration_curve(
            flows, np.array(days, dtype="datetime64[D]"), confidence_level=(0.95, 0.68)
        )

    details = caught[0].message.details
    assert (details["complete_years"], details["required_years"]) == (0, [6, 3])
    assert details["confidence_levels"] == [0.95, 0.68]
    document = result.to_dict()
    assert document["annual_median_values"] == [None] * len(CURVE_PERCENTS)
    assert [entry["ci_method"] for entry in document["intervals"]] == [None, None]
