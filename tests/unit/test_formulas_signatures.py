"""The hydrological signatures against their specs and CAMELS-PL 2.1.0 (Nogat CMP §6).

The five Tier A formulas of :mod:`hydrolog.statistics.signatures` get the range, type
and property tests generated from their specs (CMP-6.5), the limits of their specs, an
established oracle (NumPy's Weibull quantiles for the slope of the duration curve,
CMP-6.3) and exact ones (the days counted one by one, the shares and the sums in
rational arithmetic, CMP-6.2). The generic strategies draw no day without a value, so
:func:`daily_series` draws series with gaps, zeros and ties for the properties.

Their reference cases are the signatures CAMELS-PL 2.1.0 publishes for thirteen gauges
(``tests/fixtures/formulas/camels-pl-cases.json``, CMP-6.1), on the daily discharge of
those gauges kept in ``tests/fixtures/camels_pl/`` with its attribution. A case names
the sample CAMELS-PL computed on, which :func:`_sample` builds, and lists each step
where CAMELS-PL's computation and Hydrolog's part; Q5 and Q95 are cases of the duration
curve (spec ``exceedance_values``), and the baseflow index, which CAMELS-PL computes by
another filter, is a discrepancy whose cause is checked here (CMP-5.2).
"""

import csv
import gzip
import math
import re
from collections.abc import Callable, Mapping
from fractions import Fraction
from functools import cache
from itertools import accumulate
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given
from numpy.typing import NDArray

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
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
    hydrological_year,
)
from hydrolog.statistics.baseflow import baseflow_index, lyne_hollick_filter
from hydrolog.statistics.duration import exceedance_values
from hydrolog.statistics.signatures import (
    FDC_SLOPE,
    HALF_FLOW_DATE,
    HIGH_FLOW_DAYS,
    LOW_FLOW_DAYS,
    ZERO_FLOW_FRACTION,
    FlowDays,
    fdc_slope,
    half_flow_date,
    high_flow_days,
    low_flow_days,
    zero_flow_fraction,
)

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "camels-pl-cases.json"
FAMILY: tuple[tuple[FormulaSpec, Callable[..., object]], ...] = (
    (FDC_SLOPE, fdc_slope),
    (HIGH_FLOW_DAYS, high_flow_days),
    (LOW_FLOW_DAYS, low_flow_days),
    (ZERO_FLOW_FRACTION, zero_flow_fraction),
    (HALF_FLOW_DATE, half_flow_date),
)
NAMES = [spec.name for spec, _ in FAMILY]
CAMELS_FIRST_DAY = np.datetime64("1951-01-01", "D")
CAMELS_LAST_DAY = np.datetime64("2025-10-31", "D")
"""The span of every series file of CAMELS-PL 2.1.0 (its data description, sect. 6.1:
27,333 daily rows); a day of it without a row in the fixture has no value."""
CAMELS_MISSING_PERCENT = 5
"""A year with more of its days without a value is left out (filter_complete_hydro_years
of the code of CAMELS-DE, tolerance 0.05)."""
CAMELS_BFI_LAST_DAY = np.datetime64("2023-12-31", "D")


# --- generated tests (CMP-6.5) ------------------------------------------------------


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_limits(spec: FormulaSpec, function):
    assert_limits(spec, function, ERRORS)


@given(inputs=strategies(FDC_SLOPE))
def test_slope_properties(inputs):
    assert_property_contract(FDC_SLOPE, fdc_slope, inputs, ERRORS)
    assert_properties(FDC_SLOPE, fdc_slope, inputs, ERRORS)


@given(inputs=strategies(HIGH_FLOW_DAYS))
def test_high_flow_properties(inputs):
    assert_property_contract(HIGH_FLOW_DAYS, high_flow_days, inputs, ERRORS)
    assert_properties(HIGH_FLOW_DAYS, high_flow_days, inputs, ERRORS)


@given(inputs=strategies(LOW_FLOW_DAYS))
def test_low_flow_properties(inputs):
    assert_property_contract(LOW_FLOW_DAYS, low_flow_days, inputs, ERRORS)
    assert_properties(LOW_FLOW_DAYS, low_flow_days, inputs, ERRORS)


@given(inputs=strategies(ZERO_FLOW_FRACTION))
def test_zero_flow_properties(inputs):
    assert_property_contract(ZERO_FLOW_FRACTION, zero_flow_fraction, inputs, ERRORS)
    assert_properties(ZERO_FLOW_FRACTION, zero_flow_fraction, inputs, ERRORS)


@given(inputs=strategies(HALF_FLOW_DATE))
def test_half_flow_properties(inputs):
    assert_property_contract(HALF_FLOW_DATE, half_flow_date, inputs, ERRORS)
    assert_properties(HALF_FLOW_DATE, half_flow_date, inputs, ERRORS)


@st.composite
def daily_series(draw, max_days: int = 60) -> NDArray[np.float64]:
    """A series of 1 to ``max_days`` days with gaps (NaN), zeros and ties at a few
    flows; one without a value now and then."""
    value = st.one_of(
        st.just(0.0),
        st.just(math.nan),
        st.sampled_from([0.075, 1.24, 4.93, 96.0, 6430.0]),
        st.floats(min_value=0.0, max_value=7000.0),
    )
    count = draw(st.integers(min_value=1, max_value=max_days))
    return np.array(draw(st.lists(value, min_size=count, max_size=count)))


@given(values=daily_series())
def test_properties_of_series_with_gaps(values):
    for spec, function in FAMILY[1:4]:
        inputs = {"values": values}
        assert_property_contract(spec, function, inputs, ERRORS)
        assert_properties(spec, function, inputs, ERRORS)


@given(
    values=daily_series(), points=st.tuples(st.floats(1.0, 99.0), st.floats(1.0, 99.0))
)
def test_slope_properties_of_series_with_gaps(values, points):
    inputs = {"values": values, "from_percent": min(points), "to_percent": max(points)}
    assert_property_contract(FDC_SLOPE, fdc_slope, inputs, ERRORS)
    assert_properties(FDC_SLOPE, fdc_slope, inputs, ERRORS)


@given(values=daily_series(max_days=366))
def test_half_flow_properties_of_series_with_gaps(values):
    inputs = {"values": values}
    assert_property_contract(HALF_FLOW_DATE, half_flow_date, inputs, ERRORS)
    assert_properties(HALF_FLOW_DATE, half_flow_date, inputs, ERRORS)


# --- oracles (CMP-6.2, CMP-6.3) ------------------------------------------------------


@given(
    values=daily_series(), points=st.tuples(st.floats(1.0, 99.0), st.floats(1.0, 99.0))
)
def test_the_slope_is_numpys_weibull_curve(values, points):
    """NumPy's curve of the values divided by the power of two of their largest, as
    Hydrolog's runs; a curve that numpy puts below the normal floats is not compared
    (the precondition and the properties cover it)."""
    first, second = min(points), max(points)
    known = values[~np.isnan(values)]
    if known.size == 0 or first == second or float(np.max(known)) == 0.0:
        return
    scaled = np.ldexp(known, -math.frexp(float(np.max(known)))[1])
    high, low = np.quantile(
        scaled, [1 - first / 100, 1 - second / 100], method="weibull"
    )
    if low < np.finfo(np.float64).tiny:
        return
    expected = (math.log(high) - math.log(low)) / ((second - first) / 100)
    spread = math.log(float(np.max(scaled)) / float(np.min(scaled[scaled >= low])))
    assert_within(
        fdc_slope(values, first, second),
        expected,
        abs=1e-12 * (spread + 1.0) * (known.size + 1) / ((second - first) / 100),
        reason="numpy's virtual index (1 - p / 100)(n + 1) - 1 and Hydrolog's "
        "(n + 1) p / 100 round apart by a few units in the last place of n + 1, which "
        "moves each value by that share of the gap to its neighbour, at most the "
        "spread of the logarithms; over the difference of the percentages",
    )


def _counted(values: NDArray[np.float64], threshold: Fraction, above: bool) -> FlowDays:
    """The days beyond a threshold and their runs, one day after another."""
    days = events = 0
    known = 0
    inside = False
    for value in values:
        if math.isnan(value):
            inside = False
            continue
        known += 1
        beyond = Fraction(value) > threshold if above else Fraction(value) < threshold
        if beyond:
            days += 1
            events += not inside
        inside = beyond
    return FlowDays(
        days_per_year=float(Fraction(days * 1461, 4 * known)),
        mean_duration_days=float(Fraction(days, events)) if events else 0.0,
        days=days,
        events=events,
    )


@given(values=daily_series())
def test_the_flow_days_are_counted_day_by_day(values):
    known = [Fraction(v) for v in values if not math.isnan(v)]
    if not known:
        return
    ordered = sorted(known)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    mean = sum(known, Fraction(0)) / len(known)
    for function, expected in (
        (high_flow_days, _counted(values, 9 * median, above=True)),
        (low_flow_days, _counted(values, mean / 5, above=False)),
    ):
        found = function(values)
        assert (found.days, found.events) == (expected.days, expected.events)
        assert_within(
            [found.days_per_year, found.mean_duration_days],
            [expected.days_per_year, expected.mean_duration_days],
            rel=4.5e-16,
            reason="the same count over the same days, one float rounding of the "
            "quotient each",
        )


@given(values=daily_series())
def test_the_zero_flow_fraction_is_the_exact_share(values):
    known = [v for v in values if not math.isnan(v)]
    if not known:
        return
    expected = Fraction(sum(v == 0.0 for v in known), len(known))
    assert zero_flow_fraction(values) == float(expected)


def _exact_date(values: NDArray[np.float64]) -> int:
    flows = [Fraction(0) if math.isnan(v) else Fraction(v) for v in values]
    total, running = sum(flows, Fraction(0)), Fraction(0)
    for day, flow in enumerate(flows, start=1):
        running += flow
        if 2 * running > total:
            return day
    raise AssertionError("no flow: the precondition refuses it")


@given(values=daily_series(max_days=366))
def test_the_date_is_the_exact_crossing(values):
    if not np.any(values[~np.isnan(values)] > 0):
        return
    assert half_flow_date(values) == _exact_date(values)


# --- traps (CMP-6.6) -----------------------------------------------------------------


def test_close_percents_give_a_finite_slope():
    values = np.linspace(1.0, 50.0, 40)
    first = 40.0

    slope = fdc_slope(values, first, math.nextafter(first, 100.0))

    assert math.isfinite(slope)
    assert slope >= 0.0


def test_a_tiny_flow_has_a_finite_slope():
    """Flows near the smallest normal float, beside flows of a few m3/s: ln Q of
    about -690 at the lower point."""
    values = [1e-300, 2e-300, 3e-300, 1.0, 2.0]

    slope = fdc_slope(values, 10.0, 80.0)

    high, low = exceedance_values(np.array(values), [10.0, 80.0])
    assert_within(
        slope,
        (math.log(high) - math.log(low)) / 0.7,
        rel=1e-14,
        reason="the logarithms of the mantissas and exponents against those of the "
        "values, a few units in the last place of about 690 over 0.7",
    )


def test_a_day_without_a_value_is_left_out():
    values = [9.0, 7.0, math.nan, 5.0, 3.0, math.nan, 1.0]

    assert fdc_slope(values, 30.0, 70.0) == fdc_slope([9.0, 7.0, 5.0, 3.0, 1.0], 30, 70)


def test_the_mean_of_many_days_is_summed_exactly():
    flows = np.full(50_000, 0.1)
    flows[::1000] = 0.0
    exact = sum((Fraction(v) for v in flows), Fraction(0)) / flows.size
    expected = _counted(flows, exact / 5, above=False)

    found = low_flow_days(flows)

    assert (found.days, found.events) == (expected.days, expected.events)


def test_a_tie_is_decided_exactly():
    """Ten flows of 0.1: summed one after another in floats, the first five pass half
    of the year's sum (0.5 against 0.49999999999999994), while exactly they only
    reach it, so the date is day 6, not 5."""
    flows = [0.1] * 10
    running = list(accumulate(flows))
    assert running[4] > running[-1] / 2

    assert half_flow_date(flows) == 6


def test_the_slope_records_the_curve_it_reads():
    with recording() as used:
        fdc_slope(np.linspace(1.0, 50.0, 40))

    assert used == {"fdc_slope": 1, "exceedance_values": 1}


# --- CAMELS-PL 2.1.0 (CMP-6.1, CMP-5.2) --------------------------------------------


@cache
def _series(file: str, column: str) -> NDArray[np.float64]:
    """A column of a fixture on every day of CAMELS-PL's span, NaN without a value."""
    days = int((CAMELS_LAST_DAY - CAMELS_FIRST_DAY).astype(int)) + 1
    values = np.full(days, math.nan)
    with gzip.open(ROOT / file, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            day = np.datetime64(row["date"], "D") - CAMELS_FIRST_DAY
            values[int(day.astype(int))] = float(row[column])
    values.flags.writeable = False
    return values


def _calendar() -> NDArray[np.datetime64]:
    days = int((CAMELS_LAST_DAY - CAMELS_FIRST_DAY).astype(int)) + 1
    return CAMELS_FIRST_DAY + np.arange(days)


def _kept_years(file: str) -> list[NDArray[np.intp]]:
    """The days of each hydrological year with at most 5 % of them without a value."""
    calendar = _calendar()
    known = ~np.isnan(_series(file, "discharge_vol_obs"))
    years = hydrological_year(calendar)
    kept = []
    for year in np.unique(years):
        inside = np.flatnonzero(years == year)
        length = int(days_in_hydrological_year(np.array([year]))[0])
        missing = length - int(np.count_nonzero(known[inside]))
        if 100 * missing <= CAMELS_MISSING_PERCENT * length:
            kept.append(inside)
    return kept


def _sample(case: ReferenceCase) -> NDArray[np.float64] | list[NDArray[np.float64]]:
    """The sample CAMELS-PL computed the case's signature on."""
    file, column = str(case.inputs["file"]), str(case.inputs["column"])
    values = _series(file, column)
    rule = case.inputs["sample"]
    if rule == "with_value_to_2023":
        window = values[_calendar() <= CAMELS_BFI_LAST_DAY]
        return window[~np.isnan(window)]
    years = _kept_years(file)
    if rule == "complete_years_each":
        return [values[days] for days in years]
    frame = values[np.concatenate(years)]
    if rule == "complete_years":
        return frame
    if rule == "complete_years_flowing":
        return frame[frame > 0.0]
    raise AssertionError(f"{case.case_id}: unknown sample {rule!r}")


def _within_case(case: ReferenceCase, found: Mapping[str, object]) -> None:
    """Assert the outputs within the case's tolerance of CMP-6.1: half a unit of each
    printed output, the source's intermediate roundings and the further tolerance."""
    for name, expected in case.expected.items():
        allowed = case.printed_precision.get(name, 0.0) / 2
        allowed += sum(
            step.effect.get(name, 0.0) for step in case.intermediate_rounding
        )
        if case.tolerance is not None:
            largest = float(np.max(np.abs(np.asarray(expected, dtype=np.float64))))
            allowed += (case.tolerance.abs or 0.0) + (
                case.tolerance.rel or 0.0
            ) * largest
        assert_within(
            np.asarray(found[name], dtype=np.float64),
            np.asarray(expected, dtype=np.float64),
            abs=allowed,
            reason=f"{case.case_id} of {case.source.text()}: half a unit of the "
            f"printed {name}, the source's intermediate roundings and the binary "
            "representation of decimals (CMP-6.1)",
        )


def _cases(formula: str) -> list[object]:
    return [pytest.param(case, id=case.case_id) for case in load_cases(CASES, formula)]


@pytest.mark.parametrize("case", _cases("exceedance_values"))
def test_q5_and_q95_of_camels_pl(case: ReferenceCase):
    sample = _sample(case)
    assert isinstance(sample, np.ndarray)

    found = exceedance_values(sample, case.inputs["exceedance_percent"])  # type: ignore[arg-type]

    _within_case(case, {"exceedance_values": found})


@pytest.mark.parametrize("case", _cases("fdc_slope"))
def test_slope_of_camels_pl(case: ReferenceCase):
    sample = _sample(case)
    assert isinstance(sample, np.ndarray)

    found = fdc_slope(
        sample,
        float(case.inputs["from_percent"]),  # type: ignore[arg-type]
        float(case.inputs["to_percent"]),  # type: ignore[arg-type]
    )

    _within_case(case, {"slope": found})


@pytest.mark.parametrize(
    "case",
    _cases("high_flow_days") + _cases("low_flow_days") + _cases("zero_flow_fraction"),
)
def test_flow_days_of_camels_pl(case: ReferenceCase):
    """CAMELS-PL counts per day of its frame, the days without a value too, Hydrolog per
    day with a value: the frequency and the share are compared times their ratio."""
    frame = _sample(case)
    assert isinstance(frame, np.ndarray)
    share_with_value = np.count_nonzero(~np.isnan(frame)) / frame.size

    if case.formula == "zero_flow_fraction":
        found: Mapping[str, object] = {
            "fraction": zero_flow_fraction(frame) * share_with_value
        }
    else:
        function = high_flow_days if case.formula == "high_flow_days" else low_flow_days
        days = function(frame)
        found = {
            "days_per_year": days.days_per_year * share_with_value,
            "mean_duration_days": days.mean_duration_days,
        }

    _within_case(case, found)


@pytest.mark.parametrize("case", _cases("half_flow_date"))
def test_half_flow_date_of_camels_pl(case: ReferenceCase):
    years = _sample(case)
    assert isinstance(years, list)

    days = [half_flow_date(year) for year in years]

    _within_case(case, {"mean_day": math.fsum(days) / len(days)})


def _two_pass_index(flows: NDArray[np.float64]) -> float:
    """The baseflow index of Xie et al.'s LH (alpha 0.925): forward from b = Q on the
    first day, the baseflow at most the flow, then backward on that baseflow."""
    beta = 0.925
    base = list(flows)
    for i in range(1, len(flows)):
        base[i] = min(
            beta * base[i - 1] + (1 - beta) / 2 * (flows[i - 1] + flows[i]), flows[i]
        )
    first = list(base)
    for i in range(len(flows) - 2, -1, -1):
        base[i] = min(
            beta * base[i + 1] + (1 - beta) / 2 * (first[i + 1] + first[i]), first[i]
        )
    return math.fsum(base) / math.fsum(flows)


@pytest.mark.parametrize("case", _cases("baseflow_index"))
def test_the_baseflow_index_of_camels_pl_is_another_filters(case: ReferenceCase):
    """The declared discrepancy (CMP-5.2) holds as its cause says: the two-pass filter
    of the second source gives CAMELS-PL's index on the case's days, and Hydrolog's
    standard approach gives the index the discrepancy names."""
    flows = _sample(case)
    assert isinstance(flows, np.ndarray)
    stated = re.search(
        r"filter gives ([0-9.]+) .*Hydrolog's ([0-9.]+)", case.discrepancy
    )
    assert case.status == "discrepancy" and stated is not None

    oracle = _two_pass_index(flows)
    hydrolog = baseflow_index(flows, lyne_hollick_filter(flows))

    _within_case(case, {"bfi": oracle})
    assert_within(
        [oracle, hydrolog],
        [float(stated.group(1)), float(stated.group(2))],
        abs=5e-5,
        reason="the discrepancy prints both indices to four decimals",
    )
