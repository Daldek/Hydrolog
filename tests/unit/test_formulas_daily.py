"""The daily statistics of a station against the computation standard (Nogat CMP §6).

The values of the duration curve are a Tier A formula (spec ``exceedance_values``):
its range, type and property tests are generated from the spec (CMP-6.5), its
reference cases are those of ``tests/fixtures/formulas/daily-cases.json`` (CMP-6.1)
and its limits hold the exact rational oracle (CMP-6.2); NumPy's ``weibull`` quantile
is its established oracle (CMP-6.3). The generic strategies draw no day without a
value, so :func:`daily_series` draws series with gaps, ties and zeros for the
properties.

The threshold level method, the low-flow sequences with their deficit volumes, the
duration classes and the runoff volumes are Tier B (CMP-2.2): the generator has no
spec to work from, so their reference cases and their oracles (runs found day by day
in a loop, sums in exact rational arithmetic, dates in :mod:`datetime`) are written
here by hand, on small samples, ties at the threshold, zeros, constant series and
seeded series with gaps (CMP-6.7).
"""

import math
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path
from typing import Any

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    UNITS,
    Case,
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
from hydrolog.operations import stats_low_flow_sequences
from hydrolog.statistics import (
    LowFlowAnalysis,
    duration_curve,
    runoff_volumes,
    threshold_events,
    threshold_runs,
)
from hydrolog.statistics.duration import EXCEEDANCE_VALUES, exceedance_values

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "daily-cases.json"
DAY = UNITS["d"].factor  # 86,400 s, exact
SEED = 20261119


def _days(first: str, count: int) -> np.ndarray:
    return np.datetime64(first, "D") + np.arange(count)


# --- exceedance_values (Tier A) -------------------------------------------------------


@pytest.mark.parametrize(
    "case", range_cases(EXCEEDANCE_VALUES) + type_cases(EXCEEDANCE_VALUES)
)
def test_ranges_and_types(case: Case):
    run_case(EXCEEDANCE_VALUES, exceedance_values, case, ERRORS)


def test_limits_and_oracles():
    assert_limits(EXCEEDANCE_VALUES, exceedance_values, ERRORS)


@given(inputs=strategies(EXCEEDANCE_VALUES))
def test_properties(inputs):
    assert_property_contract(EXCEEDANCE_VALUES, exceedance_values, inputs, ERRORS)
    assert_properties(EXCEEDANCE_VALUES, exceedance_values, inputs, ERRORS)


@st.composite
def daily_series(draw) -> dict[str, np.ndarray]:
    """A series of 1 to 60 days with gaps (NaN), zeros and ties at a few flows, and
    percentages anywhere in (0, 100); a series without a value now and then."""
    value = st.one_of(
        st.just(0.0),
        st.just(math.nan),
        st.sampled_from([1.24, 4.93, 96.0, 522.0]),
        st.floats(min_value=0.0, max_value=600.0),
    )
    count = draw(st.integers(min_value=1, max_value=60))
    values = draw(st.lists(value, min_size=count, max_size=count))
    percent = st.floats(
        min_value=0.0, max_value=100.0, exclude_min=True, exclude_max=True
    )
    percents = draw(st.lists(percent, min_size=1, max_size=12))
    return {
        "values": np.array(values, dtype=np.float64),
        "exceedance_percent": np.array(percents, dtype=np.float64),
    }


@given(inputs=daily_series())
def test_properties_of_series_with_gaps(inputs):
    assert_property_contract(EXCEEDANCE_VALUES, exceedance_values, inputs, ERRORS)
    assert_properties(EXCEEDANCE_VALUES, exceedance_values, inputs, ERRORS)


@pytest.mark.parametrize(
    "case",
    load_cases(CASES, "exceedance_values"),
    ids=lambda case: case.case_id,
)
def test_reference_cases(case: ReferenceCase):
    assert_case(EXCEEDANCE_VALUES, exceedance_values, case, ERRORS)


@given(inputs=daily_series())
def test_the_values_are_numpys_weibull_quantiles(inputs):
    values, percents = inputs["values"], inputs["exceedance_percent"]
    known = values[~np.isnan(values)]
    if known.size == 0:
        return
    expected = np.quantile(known, 1.0 - percents / 100.0, method="weibull")
    spread = float(np.ptp(known))
    assert_within(
        exceedance_values(values, percents),
        expected,
        abs=1e-15 * ((known.size + 1) * spread + 4.0 * float(np.max(np.abs(known)))),
        reason="numpy's virtual index (1 - p / 100)(n + 1) - 1 and Hydrolog's "
        "(n + 1) p / 100 round apart by a few units in the last place of n + 1, "
        "which moves the interpolation by that times the spread; each interpolation "
        "rounds by a few units in the last place of the largest value",
    )


def test_gaps_are_left_out():
    """Trap gap_propagation: the days without a value are left out, never a NaN."""
    flows = np.random.default_rng(SEED).gamma(0.8, 12.0, 365)
    with_gaps = flows.copy()
    with_gaps[::7] = np.nan
    percents = [0.1, 10.0, 50.0, 70.0, 90.0, 95.0, 99.9]

    assert_within(
        exceedance_values(with_gaps, percents),
        exceedance_values(with_gaps[~np.isnan(with_gaps)], percents),
        abs=0.0,
        reason="the same values in the same order: the same arithmetic",
    )


def test_values_near_the_largest_float_do_not_overflow():
    """q(i+1) - q(i) of 1e308 and -1e308 overflows; the curve runs on scaled values."""
    found = exceedance_values([1.0e308, -1.0e308, 5.0], [10.0, 50.0, 70.0])

    assert_within(
        found,
        [1.0e308, 5.0, 5.0 + 0.8 * (-1.0e308 - 5.0)],
        rel=1e-15,
        reason="the scaled values give the curve within a few roundings",
    )


def test_the_formula_records_its_version():
    with recording() as used:
        exceedance_values([1.0, 2.0, 3.0], [50.0])

    assert used == {"exceedance_values": EXCEEDANCE_VALUES.formula_version}


# --- the threshold level method (Tier B) ----------------------------------------------


def _runs_by_loop(
    flags: list[bool], min_duration: int, max_gap: int
) -> list[tuple[int, int]]:
    """Runs found day by day: the open run grows over a flagged day that follows it
    directly or after fewer than ``max_gap`` other days."""
    runs: list[tuple[int, int]] = []
    start = end = -1
    for day, flag in enumerate(flags):
        if not flag:
            continue
        if start >= 0 and (day == end + 1 or day - end - 1 < max_gap):
            end = day
            continue
        if start >= 0:
            runs.append((start, end))
        start = end = day
    if start >= 0:
        runs.append((start, end))
    return [(first, last) for first, last in runs if last - first + 1 >= min_duration]


@pytest.mark.parametrize(
    "case", load_cases(CASES, "threshold_runs"), ids=lambda case: case.case_id
)
def test_reference_cases_of_the_runs(case: ReferenceCase):
    inputs: dict[str, Any] = dict(case.inputs)

    starts, ends = threshold_runs(
        np.array(inputs["beyond"], dtype=bool),
        min_duration_days=inputs["min_duration_days"],
        max_gap_days=inputs["max_gap_days"],
    )

    assert (starts.tolist(), ends.tolist()) == (
        case.expected["starts"],
        case.expected["ends"],
    )


@given(
    flags=st.lists(st.booleans(), max_size=200),
    min_duration=st.integers(min_value=1, max_value=10),
    max_gap=st.integers(min_value=0, max_value=6),
)
def test_the_runs_are_those_found_day_by_day(flags, min_duration, max_gap):
    starts, ends = threshold_runs(
        np.array(flags, dtype=bool),
        min_duration_days=min_duration,
        max_gap_days=max_gap,
    )

    assert list(zip(starts.tolist(), ends.tolist(), strict=True)) == _runs_by_loop(
        flags, min_duration, max_gap
    )


def _hydrological_year(day: date) -> int:
    return day.year + 1 if day.month >= 11 else day.year


def _seeded_record(count: int, seed: int) -> tuple[list[date], list[float]]:
    """Daily flows of ``count`` days from 2019-10-15 with NaN gaps and absent dates,
    rounded to 0.1 m3/s so that ties and values at a threshold occur."""
    rng = np.random.default_rng(seed)
    flows = np.round(rng.gamma(1.2, 2.0, count), 1)
    flows[rng.random(count) < 0.05] = np.nan
    flows[rng.random(count) < 0.03] = 0.0
    first = date(2019, 10, 15)
    kept = rng.random(count) >= 0.04  # the absent dates
    days = [first + timedelta(days=i) for i in range(count) if kept[i]]
    return days, [float(v) for v, keep in zip(flows, kept, strict=True) if keep]


def _calendar(days: list[date], values: list[float]) -> tuple[list[date], list[float]]:
    """Every day from the first to the last, NaN where none is given."""
    given_on = dict(zip(days, values, strict=True))
    span = (days[-1] - days[0]).days + 1
    every = [days[0] + timedelta(days=i) for i in range(span)]
    return every, [given_on.get(day, math.nan) for day in every]


@pytest.mark.parametrize(
    ("threshold", "direction", "min_duration", "max_gap"),
    [
        (2.4, "below", 1, 0),
        (2.4, "below", 5, 4),
        (4.0, "above", 2, 3),
        (0.0, "below", 1, 2),
    ],
)
def test_the_events_are_those_counted_on_the_calendar(
    threshold, direction, min_duration, max_gap
):
    days, values = _seeded_record(900, SEED)
    every, daily = _calendar(days, values)
    has = [not math.isnan(v) for v in daily]
    if direction == "above":
        beyond = [h and v >= threshold for h, v in zip(has, daily, strict=True)]
    else:
        beyond = [h and v < threshold for h, v in zip(has, daily, strict=True)]

    found = threshold_events(
        np.array(values),
        np.array(days, dtype="datetime64[D]"),
        threshold=threshold,
        direction=direction,
        min_duration_days=min_duration,
        max_gap_days=max_gap,
    )

    runs = _runs_by_loop(beyond, min_duration, max_gap)
    pick = max if direction == "above" else min
    expected = []
    for first, last in runs:
        window = [v for v in daily[first : last + 1] if not math.isnan(v)]
        peak = pick(window)
        at = next(i for i in range(first, last + 1) if daily[i] == peak)
        expected.append(
            (
                str(every[first]),
                str(every[last]),
                last - first + 1,
                sum(beyond[first : last + 1]),
                sum(not h for h in has[first : last + 1]),
                peak,
                str(every[at]),
                _hydrological_year(every[first]),
                first == 0 or not has[first - 1],
                last == len(daily) - 1 or not has[last + 1],
            )
        )
    assert [
        (
            e.start_date,
            e.end_date,
            e.duration_days,
            e.days_beyond,
            e.missing_days,
            e.peak,
            e.peak_date,
            e.hydrological_year,
            e.open_start,
            e.open_end,
        )
        for e in found.events
    ] == expected
    years = sorted(
        {_hydrological_year(d) for d, h in zip(every, has, strict=True) if h}
    )
    assert [
        (y.year, y.days_beyond, y.n_events, y.days_with_data, y.days)
        for y in found.years
    ] == [
        (
            year,
            sum(
                b
                for d, b in zip(every, beyond, strict=True)
                if _hydrological_year(d) == year
            ),
            sum(1 for first, _ in runs if _hydrological_year(every[first]) == year),
            sum(
                h
                for d, h in zip(every, has, strict=True)
                if _hydrological_year(d) == year
            ),
            (date(year, 11, 1) - date(year - 1, 11, 1)).days,
        )
        for year in years
    ]
    assert (found.n_days, found.n_missing_days, found.days_beyond) == (
        len(every),
        len(every) - sum(has),
        sum(beyond),
    )


def test_a_day_at_the_threshold_is_beyond_it_above_and_not_below():
    days = _days("2021-06-01", 3)

    above = threshold_events([5.0, 5.0, 4.9], days, threshold=5.0)
    below = threshold_events([5.0, 4.9, 5.0], days, threshold=5.0, direction="below")

    assert (above.days_beyond, below.days_beyond) == (2, 1)


# --- the low-flow sequences and their volumes (Tier B) --------------------------------


def _sequences_by_loop(
    values: list[float], threshold: float, min_duration: int, max_gap: int
) -> list[tuple[int, int, int, float, Fraction, Fraction, int]]:
    """Low-flow sequences of a calendar series: runs day by day, deficits and means in
    exact rational arithmetic, over the days with a value."""
    below = [not math.isnan(v) and v < threshold for v in values]
    out = []
    for first, last in _runs_by_loop(below, min_duration, max_gap):
        known = [Fraction(v) for v in values[first : last + 1] if not math.isnan(v)]
        deficit = sum(
            (max(Fraction(threshold) - v, Fraction(0)) for v in known), Fraction(0)
        )
        out.append(
            (
                first,
                last,
                last - first + 1,
                float(min(known)),
                sum(known, Fraction(0)) / len(known),
                deficit,
                last - first + 1 - len(known),
            )
        )
    return out


@pytest.mark.parametrize(
    "case", load_cases(CASES, "low_flow_sequences"), ids=lambda case: case.case_id
)
def test_reference_cases_of_the_low_flow_sequences(case: ReferenceCase):
    inputs: dict[str, Any] = dict(case.inputs)
    flows = [math.nan if v is None else v for v in inputs["flows"]]

    found = LowFlowAnalysis(np.array(flows), _days("2021-06-01", len(flows)))
    result = found.detect_sequences(
        threshold=inputs["threshold"],
        min_duration_days=inputs["min_duration_days"],
        max_gap_days=inputs["max_gap_days"],
    )

    assert [s.duration_days for s in result.sequences] == case.expected["duration_days"]
    assert [s.min_flow for s in result.sequences] == case.expected["min_flow"]


@pytest.mark.parametrize(
    ("flows", "threshold"),
    [
        ([1.0, 1.0, 1.0, 10.0, 1.0, 1.0, 1.0], 2.0),  # lfstat's test: deficit 6
        ([2.0, 2.0, 2.0, 2.0, 2.0], 2.0),  # a constant series at the threshold
        ([0.5, 0.5, 0.5, 0.5, 0.5], 2.0),  # a constant series below it
        ([0.0, 0.0, 3.0, 0.0, math.nan, 0.0], 1.0),  # zeros and a gap
        ([0.3], 1.0),  # one day
    ],
)
def test_small_samples_ties_zeros_and_constant_series(flows, threshold):
    expected = _sequences_by_loop(flows, threshold, 1, 4)

    result = LowFlowAnalysis(
        np.array(flows), _days("2021-06-01", len(flows))
    ).detect_sequences(threshold=threshold, min_duration_days=1, max_gap_days=4)

    assert [
        (s.start_index, s.end_index, s.duration_days, s.min_flow, s.missing_days)
        for s in result.sequences
    ] == [(first, last, d, low, gaps) for first, last, d, low, _, _, gaps in expected]
    assert_within(
        [[s.mean_flow, s.deficit_volume] for s in result.sequences] or np.empty((0, 2)),
        [[float(mean), float(deficit)] for *_, mean, deficit, _ in expected]
        or np.empty((0, 2)),
        rel=4.5e-16,
        reason="a few values of one decimal digit: the means and deficits round once "
        "or twice",
    )


@pytest.mark.parametrize("seed", [SEED, SEED + 1])
def test_the_sequences_and_their_deficits_are_the_exact_ones(seed):
    days, values = _seeded_record(1500, seed)
    every, daily = _calendar(days, values)
    expected = _sequences_by_loop(daily, 2.4, 5, 4)

    result = LowFlowAnalysis(
        np.array(values), np.array(days, dtype="datetime64[D]")
    ).detect_sequences(threshold=2.4)

    assert [
        (str(days[s.start_index]), str(days[s.end_index]), s.duration_days)
        for s in result.sequences
    ] == [
        # a sequence starts and ends on a day below the threshold, which has a date
        (str(every[first]), str(every[last]), d)
        for first, last, d, *_ in expected
    ]
    assert [(s.min_flow, s.missing_days) for s in result.sequences] == [
        (low, gaps) for _, _, _, low, _, _, gaps in expected
    ]
    assert_within(
        [[s.mean_flow, s.deficit_volume] for s in result.sequences],
        [[float(mean), float(deficit)] for *_, mean, deficit, _ in expected],
        rel=1e-14,
        reason="NumPy's pairwise sums of up to a few hundred terms of one rounding "
        "each against the exact rational sums",
    )
    assert_within(
        result.total_deficit,
        float(sum((deficit for *_, deficit, _ in expected), Fraction(0))),
        rel=1e-14,
        reason="the deficits summed in a Python loop, each within 1e-14",
    )


def test_the_deficit_volumes_in_m3_are_the_exact_ones():
    days, values = _seeded_record(1500, SEED)
    every, daily = _calendar(days, values)
    expected = _sequences_by_loop(daily, 2.4, 5, 4)

    result = stats_low_flow_sequences(
        values=[None if math.isnan(v) else v for v in values],
        dates=[str(day) for day in days],
        threshold=2.4,
        parameter="Q",
    ).result

    assert_within(
        [s.deficit_volume_m3 for s in result.sequences],
        [float(deficit * DAY) for *_, deficit, _ in expected],
        rel=1e-14,
        reason="the deficit in m3/s x d times the exact 86,400 s/d: the deficit's "
        "pairwise sum within 1e-14 and one rounding of the product",
    )
    yearly: dict[int, Fraction] = {}
    for first, *_, deficit, _ in expected:
        year = _hydrological_year(every[first])
        yearly[year] = yearly.get(year, Fraction(0)) + deficit
    assert_within(
        [y.deficit_volume_m3 for y in result.years],
        [float(yearly.get(y.year, Fraction(0)) * DAY) for y in result.years],
        rel=1e-14,
        abs=0.0,
        reason="the deficits of the sequences that start in the year, summed, times "
        "the day",
    )
    assert_within(
        result.total_deficit_volume_m3,
        float(sum((deficit for *_, deficit, _ in expected), Fraction(0)) * DAY),
        rel=1e-14,
        reason="the sum of the deficits times the day",
    )


# --- the duration classes and the runoff volumes (Tier B) -----------------------------


@pytest.mark.parametrize(
    "case", load_cases(CASES, "duration_classes"), ids=lambda case: case.case_id
)
def test_reference_cases_of_the_classes(case: ReferenceCase):
    inputs: dict[str, Any] = dict(case.inputs)
    values = inputs["values"]

    result = duration_curve(
        np.array(values),
        _days("2020-11-01", len(values)),
        bin_width=inputs["bin_width"],
    )

    assert [[c.lower, c.upper, c.days] for c in result.classes] == case.expected[
        "classes"
    ]


@pytest.mark.parametrize(
    "case", load_cases(CASES, "runoff_volumes"), ids=lambda case: case.case_id
)
def test_reference_cases_of_the_volumes(case: ReferenceCase):
    days = np.arange(np.datetime64("2019-11-01"), np.datetime64("2021-11-01"))

    result = runoff_volumes(np.ones(days.size), days)

    assert [y.volume_m3 for y in result.years] == case.expected["volume_m3"]
    assert result.mean_annual_volume_m3 == case.expected["mean_annual_volume_m3"]


def test_the_volumes_are_the_exact_sums():
    """Three hydrological years from 2019-11-01: 2020 (366 days) and 2021 complete,
    2022 with gaps and absent dates."""
    rng = np.random.default_rng(SEED + 2)
    flows = np.round(rng.gamma(1.2, 2.0, 1096), 2)
    later = np.arange(1096) >= 731
    flows[later & (rng.random(1096) < 0.05)] = np.nan
    kept = ~later | (rng.random(1096) >= 0.04)
    all_days = [date(2019, 11, 1) + timedelta(days=i) for i in range(1096)]
    days = [day for day, keep in zip(all_days, kept, strict=True) if keep]
    flows = flows[kept]
    every, daily = _calendar(days, flows.tolist())

    result = runoff_volumes(flows, np.array(days, dtype="datetime64[D]"))

    for row in result.years:
        mine = [
            (d, v)
            for d, v in zip(every, daily, strict=True)
            if _hydrological_year(d) == row.year
        ]
        known = [Fraction(v) * DAY for _, v in mine if not math.isnan(v)]
        start = date(row.year - 1, 11, 1)
        calendar_days = (date(row.year, 11, 1) - start).days
        complete = len(known) == calendar_days
        assert (row.days, row.days_with_data, row.complete) == (
            calendar_days,
            len(known),
            complete,
        )
        assert_within(
            row.volume_m3,
            float(sum(known, Fraction(0))),
            rel=4e-15,
            reason="a pairwise sum of up to 366 volumes, each the correctly rounded "
            "product of a flow and the exact day",
        )
        for month in row.months:
            days_of = [
                v for d, v in mine if d.month == month.month and not math.isnan(v)
            ]
            if not days_of:
                assert month.volume_m3 is None
                continue
            assert_within(
                month.volume_m3,
                float(sum((Fraction(v) * DAY for v in days_of), Fraction(0))),
                rel=4e-15,
                reason="a pairwise sum of up to 31 volumes",
            )
    complete_years = [row for row in result.years if row.complete]
    assert complete_years, "the seeded record keeps its first year complete"
    assert_within(
        result.mean_annual_volume_m3,
        float(
            sum((Fraction(row.volume_m3) for row in complete_years), Fraction(0))
            / len(complete_years)
        ),
        rel=4.5e-16,
        reason="the mean of the complete years' volumes rounds once",
    )
    cumulative = [
        (d, v)
        for d, v in zip(every, daily, strict=True)
        if _hydrological_year(d) == result.cumulative_year
    ]
    running = Fraction(0)
    expected = []
    for _, v in cumulative:
        running += Fraction(0) if math.isnan(v) else Fraction(v) * DAY
        expected.append(float(running))
    start = date(result.cumulative_year - 1, 11, 1)
    lead = (cumulative[0][0] - start).days  # days of the year before the record
    assert_within(
        result.cumulative_volume_m3[lead:],
        expected,
        rel=1e-13,
        reason="NumPy's cumsum adds the days in order: up to 366 roundings of a "
        "growing sum",
    )


@pytest.mark.parametrize(
    "compute",
    [
        lambda v, d: threshold_events(v, d, threshold=1.0),
        lambda v, d: runoff_volumes(v, d),
        lambda v, d: duration_curve(v, d),
    ],
    ids=["threshold_events", "runoff_volumes", "duration_curve"],
)
def test_dates_that_do_not_increase_are_refused(compute):
    """Before 0.9.0 a repeated date let the later value overwrite the earlier (runoff
    volumes, events) or counted a day twice (the duration curve), without a word."""
    dates = np.array(["2021-01-01", "2021-01-02", "2021-01-02"], dtype="datetime64[D]")

    with pytest.raises(InvalidParameterError, match="increase strictly"):
        compute(np.array([1.0, 2.0, 3.0]), dates)
