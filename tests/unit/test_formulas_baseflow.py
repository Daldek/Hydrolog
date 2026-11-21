"""The Lyne and Hollick filter, the baseflow index and the recession constant against
their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of Ladson et al. (2013) and their worked spreadsheet
(``tests/fixtures/formulas/baseflow-cases.json``); the oracles are the filter's
recursion, the index's ratio and the recession's median in exact rational arithmetic
(CMP-6.2), and Ladson's own R function ``BFI()`` run once (``tests/oracles/baseflow``,
CMP-6.4). The generic strategies draw series of one to fifty values, which the filter
refuses (it needs more than its thirty reflected values), baseflows above their flows
and series without a recession: the hand-written strategies :func:`gapless_series`,
:func:`flows_and_baseflows` and :func:`recessions` draw inputs the formulas compute,
for the properties. The filter's notice ``outside_applicability`` is read as the
standard's ``outside_applicability`` by :func:`as_standard` (ADR-0050, point 3).
"""

import math
import re
import statistics
import warnings
from collections.abc import Callable
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import hypothesis.strategies as st
import numpy as np
import pytest
from hypothesis import given
from hypothesis.extra.numpy import arrays
from scipy.signal import lfilter

from hydrolog._formula_versions import recording
from hydrolog._formulas import DELEGATED, ERRORS
from hydrolog._warnings import OutsideApplicability
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
    read_frozen_oracle,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics.baseflow import (
    BASEFLOW_INDEX,
    LYNE_HOLLICK,
    RECESSION,
    SPECS,
    baseflow_index,
    baseflow_separation,
    lyne_hollick_filter,
    recession_constant,
    recession_ratio,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[1]
CASES = ROOT / "fixtures" / "formulas" / "baseflow-cases.json"
ORACLES = ROOT / "oracles" / "baseflow"
FAMILY: tuple[tuple[FormulaSpec, Callable[..., object]], ...] = (
    (LYNE_HOLLICK, lyne_hollick_filter),
    (BASEFLOW_INDEX, baseflow_index),
    (RECESSION, recession_ratio),
)
BASS_RIVER = [
    float(value)
    for value in (ORACLES / "BassRiver@Loch.csv").read_text(encoding="utf-8").split()
]
"""The 67 daily flows [ML/d] of the Bass River at Loch (Ladson et al. 2013, Table 3)."""


# --- the exact oracles (CMP-6.2) ---------------------------------------------------


def _exact_filter(values: list[float], alpha: float, passes: int) -> list[Fraction]:
    """Ladson et al.'s standard approach (sect. 2.1 to 2.3) in rational arithmetic.

    The series is padded as q31, ..., q2, q1, ..., qn, qn-1, ..., qn-30; each pass runs
    over the baseflow of the one before, forward or backward, its quickflow starting
    at the first value it meets and never clipped; the baseflow of the n days below 0
    is set to 0.
    """
    q = [Fraction(value) for value in values]
    n = len(q)
    a = Fraction(alpha)
    padded = [q[i] for i in range(30, 0, -1)] + q + [q[n - 2 - i] for i in range(30)]
    flow = padded
    for number in range(passes):
        order = range(len(flow)) if number % 2 == 0 else range(len(flow) - 1, -1, -1)
        base = list(flow)
        quick = Fraction(0)
        previous = None
        for i in order:
            quick = (
                flow[i]
                if previous is None
                else (a * quick + (1 + a) / 2 * (flow[i] - flow[previous]))
            )
            base[i] = flow[i] - quick if quick > 0 else flow[i]
            previous = i
        flow = base
    return [max(value, Fraction(0)) for value in flow[30 : 30 + n]]


def _exact_index(values: list[float], baseflow: list[float]) -> Fraction:
    """Σ b / Σ Q over the days with both values, in rational arithmetic."""
    days = [
        (Fraction(q), Fraction(b))
        for q, b in zip(values, baseflow, strict=True)
        if math.isfinite(q) and math.isfinite(b)
    ]
    baseflow_sum = sum((b for _, b in days), Fraction(0))
    return baseflow_sum / sum((q for q, _ in days), Fraction(0))


def _exact_recession(values: list[float], min_days: int) -> tuple[Fraction, int]:
    """The median ratio and the count of the runs, by a scan of the days."""
    runs: list[list[Fraction]] = []
    run: list[Fraction] = []
    for today, tomorrow in pairwise(values):
        if math.isfinite(today) and math.isfinite(tomorrow) and 0 < tomorrow < today:
            run.append(Fraction(tomorrow) / Fraction(today))
        elif math.isfinite(today) and today > 0 and tomorrow == 0:
            run.append(Fraction(0))
        else:
            runs.append(run)
            run = []
    runs.append(run)
    kept = [run for run in runs if len(run) >= min_days]
    return statistics.median([ratio for run in kept for ratio in run]), len(kept)


def _quiet(function: Callable[..., object]) -> Callable[..., object]:
    """Return the function without its notice ``outside_applicability``."""

    def call(*args: object, **kwargs: object) -> object:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OutsideApplicability)
            return function(*args, **kwargs)

    return call


# --- generated tests (CMP-6.5) -----------------------------------------------------


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
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function", "case"), _published())
def test_reference_cases(spec: FormulaSpec, function, case: ReferenceCase):
    assert_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


def test_the_module_declares_its_three_specs():
    assert SPECS == (LYNE_HOLLICK, BASEFLOW_INDEX, RECESSION)


@given(inputs=strategies(LYNE_HOLLICK))
def test_filter_properties(inputs):
    function = as_standard(lyne_hollick_filter)
    assert_property_contract(LYNE_HOLLICK, function, inputs, ERRORS)
    assert_properties(LYNE_HOLLICK, function, inputs, ERRORS)


@given(inputs=strategies(BASEFLOW_INDEX))
def test_index_properties(inputs):
    assert_property_contract(BASEFLOW_INDEX, baseflow_index, inputs, ERRORS)
    assert_properties(BASEFLOW_INDEX, baseflow_index, inputs, ERRORS)


@given(inputs=strategies(RECESSION))
def test_recession_properties(inputs):
    assert_property_contract(RECESSION, recession_ratio, inputs, ERRORS)
    assert_properties(RECESSION, recession_ratio, inputs, ERRORS)


_FLOW = st.one_of(
    st.floats(min_value=0.5, max_value=125.0),
    st.floats(min_value=0.0, max_value=1.0e6),
    st.just(0.0),
)


@st.composite
def gapless_series(draw) -> dict[str, object]:
    """A gapless daily series of 31 to 200 days with any filter parameter."""
    values = draw(arrays(np.float64, st.integers(31, 200), elements=_FLOW))
    alpha = draw(
        st.one_of(
            st.floats(min_value=0.9, max_value=0.98),
            st.floats(min_value=0.0, max_value=1.0, exclude_min=True, exclude_max=True),
        )
    )
    passes = draw(st.sampled_from([3, 5, 7, 9]))
    return {"values": values, "alpha": alpha, "passes": passes}


@given(inputs=gapless_series())
def test_filter_properties_of_series(inputs):
    function = as_standard(lyne_hollick_filter)
    assert_property_contract(LYNE_HOLLICK, function, inputs, ERRORS)
    assert_properties(LYNE_HOLLICK, function, inputs, ERRORS)


@st.composite
def flows_and_baseflows(draw) -> dict[str, object]:
    """Flows with gaps and baseflows of 0 to 1 of them, gaps of their own too."""
    values = draw(arrays(np.float64, st.integers(1, 120), elements=_FLOW))
    shares = draw(arrays(np.float64, values.size, elements=st.floats(0.0, 1.0)))
    baseflow = values * shares
    for series in (values, baseflow):
        gaps = draw(arrays(np.bool_, values.size, elements=st.booleans()))
        series[gaps & draw(st.booleans())] = np.nan
    return {"values": values, "baseflow": baseflow}


@given(inputs=flows_and_baseflows())
def test_index_properties_of_series(inputs):
    assert_property_contract(BASEFLOW_INDEX, baseflow_index, inputs, ERRORS)
    assert_properties(BASEFLOW_INDEX, baseflow_index, inputs, ERRORS)


@st.composite
def recessions(draw) -> dict[str, object]:
    """Exponential recessions with noise, rises, days without flow and gaps."""
    pieces: list[float] = []
    for _ in range(draw(st.integers(1, 6))):
        start = draw(st.floats(min_value=0.0, max_value=1.0e6))
        k = draw(st.floats(min_value=0.0, max_value=1.0))
        days = draw(st.integers(1, 15))
        noise = draw(arrays(np.float64, days, elements=st.floats(0.99, 1.01)))
        pieces += list(start * k ** np.arange(days) * noise)
    values = np.array(pieces)
    gaps = draw(arrays(np.bool_, values.size, elements=st.booleans()))
    values[gaps & draw(st.booleans())] = np.nan
    return {"values": values, "min_days": draw(st.integers(1, 7))}


@given(inputs=recessions())
def test_recession_properties_of_series(inputs):
    assert_property_contract(RECESSION, recession_ratio, inputs, ERRORS)
    assert_properties(RECESSION, recession_ratio, inputs, ERRORS)


# --- oracles -----------------------------------------------------------------------


@pytest.mark.parametrize("alpha", [0.9, 0.925, 0.95, 0.98])
@pytest.mark.parametrize("passes", [3, 9])
def test_the_filter_is_the_exact_recursion(alpha, passes):
    exact = _exact_filter(BASS_RIVER, alpha, passes)

    assert_within(
        lyne_hollick_filter(BASS_RIVER, alpha=alpha, passes=passes),
        [float(value) for value in exact],
        abs=1e-11,
        reason="the double-precision recursion over 127 padded days and up to 9 "
        "passes against the exact one of its float inputs: the rounding of each step "
        "decays by alpha and stays below 1e-11 of flows up to 1,169 ML/d",
    )


def test_the_index_is_the_exact_ratio():
    baseflow = lyne_hollick_filter(BASS_RIVER, alpha=0.98).tolist()

    assert_within(
        baseflow_index(BASS_RIVER, baseflow),
        float(_exact_index(BASS_RIVER, baseflow)),
        rel=2.3e-16,
        reason="math.fsum rounds each sum once; the quotient rounds once more",
    )


@pytest.mark.parametrize(
    ("values", "min_days"),
    [
        ([10, 9, 8.1, 7.29, 6.561, 5.9049, 7, 6, 5, 4, 3, 2, 1, 0, 0, 3], 5),
        ([5, 4, 4, 3, 2, 1, 0.5, math.nan, 9, 8, 7, 6, 5, 4.5, 4.4, 4.3], 3),
        ([100 * 0.97**t for t in range(40)] + [300, 120, 60, 30, 15, 7.5], 2),
    ],
)
def test_the_recession_constant_is_the_exact_median(values, min_days):
    k, count = _exact_recession(values, min_days)
    result = recession_ratio(values, min_days=min_days)

    assert result.n_segments == count
    assert_within(
        result.k,
        float(k),
        rel=4.5e-16,
        reason="each ratio rounds once in floating point; the median of an even "
        "count averages two of them, one more rounding",
    )


def _frozen(name: str) -> dict[tuple[str, float, int], dict[str, np.ndarray]]:
    table = read_frozen_oracle(ORACLES / name)
    groups: dict[tuple[str, float, int], dict[str, np.ndarray]] = {}
    keys = list(
        zip(
            (row["dataset"] for row in table.rows),
            table.floats("alpha").tolist(),
            table.floats("passes").astype(int).tolist(),
            strict=True,
        )
    )
    for column in table.columns[3:]:
        values = table.floats(column)
        for key in dict.fromkeys(keys):
            mask = np.array([k == key for k in keys])
            groups.setdefault(key, {})[column] = values[mask]
    return groups


@pytest.mark.parametrize(
    ("key", "frozen"), list(_frozen("lyne_hollick_r.csv").items()), ids=str
)
def test_the_filter_is_ladsons_bfi_r(key, frozen):
    _, alpha, passes = key
    baseflow = _quiet(lyne_hollick_filter)(frozen["flow"], alpha=alpha, passes=passes)

    assert_within(
        baseflow,
        frozen["baseflow"],
        abs=1e-11,
        reason="Ladson's R loops and SciPy's lfilter run the same double-precision "
        "recursion in another order of operations; the CSV prints 17 digits",
    )


@pytest.mark.parametrize(
    ("key", "frozen"), list(_frozen("lyne_hollick_bfi_r.csv").items()), ids=str
)
def test_the_index_is_ladsons_bfi_r(key, frozen):
    dataset, alpha, passes = key
    flows = BASS_RIVER if dataset == "bass_river" else _synthetic()
    baseflow = _quiet(lyne_hollick_filter)(flows, alpha=alpha, passes=passes)

    assert_within(
        baseflow_index(flows, baseflow),
        frozen["bfi"][0],
        abs=1e-14,
        reason="R's sum(Qbase)/sum(Qin) adds in order, math.fsum rounds once; the "
        "baseflows agree within 1e-11 of the larger flows",
    )


def _synthetic() -> np.ndarray:
    table = read_frozen_oracle(ORACLES / "lyne_hollick_r.csv")
    rows = [
        row
        for row in table.rows
        if (row["dataset"], row["alpha"], row["passes"]) == ("synthetic", "0.9", "3")
    ]
    return np.array([float(row["flow"]) for row in rows])


def test_the_research_run_of_bfi_r_printed_the_same():
    """The R output of the research of 2026-11-18, kept as it was printed."""
    text = (ORACLES / "run_bfi_check.out").read_text(encoding="utf-8")
    printed = dict(re.findall(r"alpha=(\S+ passes=\d+) BFI=([\d.]+)", text))
    block = text.split("Qbase alpha=0.925:")[1].split("missing example")[0]
    daily = [float(v) for v in re.findall(r"(?<!\[)\b\d+\.\d+\b", block)]

    for label, value in printed.items():
        alpha, passes = label.split(" passes=")
        flows = lyne_hollick_filter(BASS_RIVER, alpha=float(alpha), passes=int(passes))
        assert_within(
            baseflow_index(BASS_RIVER, flows),
            float(value),
            abs=5e-8,
            reason="half a unit of the seventh printed decimal",
        )
    assert_within(
        lyne_hollick_filter(BASS_RIVER, alpha=0.925),
        daily,
        abs=5e-5,
        reason="half a unit of the fourth printed decimal",
    )


def test_the_delegated_recursion_is_the_first_pass_of_table_4():
    """DELEGATED lyne_hollick_recursion: lfilter gives Table 4's 155.46 (note b)."""
    alpha = 0.98
    flows = np.array([96.0, 158.0])
    quick = lfilter(
        [(1 + alpha) / 2], [1, -alpha], np.diff(flows), zi=[alpha * flows[0]]
    )[0]

    assert [entry.name for entry in DELEGATED].count("lyne_hollick_recursion") == 1
    assert_within(
        quick[0],
        155.46,
        abs=5e-3,
        reason="half a unit of the second decimal Table 4 prints "
        "(0.98 x 96 + (158 - 96) x 1.98 / 2 = 155.46 exactly in decimal)",
    )


def test_ladsons_bfi_falls_with_alpha_as_in_table_5():
    """Table 5 of Ladson et al. (2013), p. 15: the BFI of the Bass River per alpha.

    Hand-written: the spec of the index takes the baseflow, which Table 5 does not
    print; its alpha of 0 lies outside the filter's physical range (0, 1).
    """
    for alpha, printed in ((0.9, 0.41), (0.925, 0.39), (0.95, 0.34), (0.98, 0.20)):
        baseflow = lyne_hollick_filter(BASS_RIVER, alpha=alpha)
        assert_within(
            baseflow_index(BASS_RIVER, baseflow),
            printed,
            abs=5e-3,
            reason="half a unit of the second decimal Table 5 prints",
        )
    baseflow = _quiet(lyne_hollick_filter)(BASS_RIVER, alpha=0.987)
    assert_within(
        baseflow_index(BASS_RIVER, baseflow),
        0.12,
        abs=5e-3,
        reason="half a unit of the second decimal Table 5 prints",
    )


# --- traps (CMP-6.6) ---------------------------------------------------------------


def test_alpha_next_to_one_keeps_the_baseflow_within_the_flow():
    """Trap stability_bound: alpha just below 1, where the quickflow hardly decays."""
    alpha = math.nextafter(1.0, 0.0)
    with pytest.warns(OutsideApplicability):
        baseflow = lyne_hollick_filter(BASS_RIVER, alpha=alpha)

    assert np.all((baseflow >= 0.0) & (baseflow <= np.array(BASS_RIVER)))
    assert_within(
        baseflow,
        [float(value) for value in _exact_filter(BASS_RIVER, alpha, 3)],
        abs=1e-9,
        reason="with alpha = 1 - 2**-53 the rounding of each step is not damped: "
        "about 400 steps of a few ulp of 2,000 ML/d",
    )


def test_a_long_series_matches_the_exact_recursion():
    """Trap many_small_terms: 3,000 days; alpha 15/16 keeps the exact numbers short."""
    rng = np.random.default_rng(20261119)
    flows = (np.round(rng.lognormal(1.0, 1.0, 3000) * 8) / 8).tolist()
    exact = _exact_filter(flows, 0.9375, 3)

    assert_within(
        lyne_hollick_filter(flows, alpha=0.9375),
        [float(value) for value in exact],
        abs=1e-11,
        reason="the recursion forgets a rounding in about 1 / (1 - alpha) = 16 days, "
        "so the error stays a few ulp of the largest flow over 3,000 days",
    )


def test_a_gap_parts_the_spans():
    """Trap gap_propagation: the filter refuses a gap; the separation goes around it."""
    days = np.arange("2020-11-01", "2021-04-01", dtype="datetime64[D]")
    flows = 10.0 + 5.0 * np.sin(np.arange(days.size) / 9.0) ** 2
    flows[75] = np.nan

    with pytest.raises(InvalidParameterError) as caught:
        lyne_hollick_filter(flows)
    result = baseflow_separation(flows, days)

    assert caught.value.details["reason"] == "outside_physical_range"
    assert result.n_spans == 2
    assert result.n_values == days.size - 1
    assert_within(
        np.array(result.series_baseflow[:75], dtype=float),
        lyne_hollick_filter(flows[:75]),
        abs=0.0,
        reason="the span before the gap is filtered alone, the same computation",
    )


def test_a_trickle_has_a_finite_index():
    """Trap singular_at_bound: the smallest flows divide without underflow."""
    flows = [5e-324, 1e-320, 3e-310, 0.0]
    baseflow = [5e-324, 5e-321, 1e-310, 0.0]

    assert_within(
        baseflow_index(flows, baseflow),
        float(_exact_index(flows, baseflow)),
        rel=2.3e-16,
        reason="the subnormal sums are exact, the quotient a normal number",
    )


def test_a_day_without_a_value_is_left_out():
    """Trap gap_propagation: a gap in either series leaves its day out of both."""
    flows = [4.0, math.nan, 6.0, 8.0, 2.0]
    baseflow = [2.0, 1.0, 3.0, math.nan, 1.0]

    assert baseflow_index(flows, baseflow) == 0.5  # (2 + 3 + 1) / (4 + 6 + 2)


def test_a_long_series_sums_exactly():
    """Trap many_small_terms: 50,000 days against the exact rational sums."""
    rng = np.random.default_rng(7)
    flows = rng.lognormal(0.0, 2.0, 50_000)
    baseflow = flows * rng.uniform(0.0, 1.0, flows.size)

    assert_within(
        baseflow_index(flows, baseflow),
        float(_exact_index(flows.tolist(), baseflow.tolist())),
        rel=2.3e-16,
        reason="math.fsum rounds each sum of 50,000 terms once; the quotient once more",
    )


def test_a_ratio_next_to_one_has_a_finite_half_life():
    """Trap singular_at_bound: ln k next to 0 where k is next to 1."""
    k = 1.0 - 2.0**-40
    result = recession_ratio([1.0e6 * k**t for t in range(7)])

    assert result.half_life_days is not None
    assert math.isfinite(result.half_life_days)
    assert_within(
        result.half_life_days,
        math.log(2.0) / 2.0**-40,
        rel=1e-4,
        reason="each ratio of the rounded powers carries a few ulp, 2**-52, against "
        "-ln k = 2**-40: a relative error of about 2**-12 in the half-life",
    )


def test_a_fall_to_no_flow_has_a_half_life_of_zero():
    """Trap singular_at_bound: ln k at k = 0, a fall to no flow in runs of one day."""
    result = recession_ratio([5.0, 0.0, 3.0, 0.0, 4.0, 0.0], min_days=1)

    assert (result.k, result.half_life_days, result.n_segments) == (0.0, 0.0, 3)


def test_a_gap_ends_a_segment():
    """Trap gap_propagation: a day without a value ends a run and is never a ratio."""
    falling = [64.0, 32.0, 16.0, 8.0, 4.0, 2.0, 1.0]
    whole = recession_ratio(falling + [0.5])
    parted = recession_constant(falling[:4] + [math.nan] + falling[4:])

    assert (whole.k, whole.n_segments) == (0.5, 1)
    assert (parted.k, parted.half_life_days, parted.n_segments) == (None, None, 0)


# --- small samples, ties, zeros and constant series (CMP-6.7) -----------------------


def test_the_shortest_series_and_a_constant_one_are_the_exact_recursion():
    for flows in ([float(v) for v in range(31)], [10.0] * 400, [0.0] * 31):
        assert_within(
            lyne_hollick_filter(flows),
            [float(value) for value in _exact_filter(flows, 0.925, 3)],
            abs=1e-12,
            reason="the double-precision recursion against the exact one, flows up "
            "to 30",
        )


def test_a_constant_series_keeps_the_end_effect_of_the_standard():
    # q of the first pass starts at Q of the padded series, so the first day of a
    # constant 10 keeps 6.78 of it: Ladson et al.'s convention, documented in the spec
    baseflow = lyne_hollick_filter([10.0] * 400)

    assert_within(
        [baseflow[0], baseflow_index([10.0] * 400, baseflow)],
        [6.7778, 0.98295],
        abs=5e-5,
        reason="the values the spec's assumption quotes, to their printed digits",
    )


def test_ties_and_zero_flows_end_a_recession():
    tie = [8.0, 7.0, 6.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.5]
    zero = [0.0, 0.0, 0.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 0.0, 0.0]

    assert recession_ratio(tie, min_days=3).n_segments == 2
    assert recession_ratio(zero, min_days=6).n_segments == 1
    assert recession_constant(zero, min_days=7).k is None


def test_the_smallest_sample_of_the_index():
    assert baseflow_index([4.0], [1.0]) == 0.25
    with pytest.raises(InvalidParameterError) as caught:
        baseflow_index([0.0], [0.0])
    assert caught.value.details["constraint"] == "positive_flow_volume"


# --- the separation of a daily series (Tier B) and its defects -----------------------


def _days(first: str, count: int) -> np.ndarray:
    return np.datetime64(first) + np.arange(count)


def test_a_dry_year_has_no_index_instead_of_nan():
    """Fixed: a year without flow on its days had the BFI NaN (0 / 0)."""
    days = _days("2019-11-01", 731)
    flows = np.where(np.arange(days.size) < 366, 0.0, 3.0)

    result = baseflow_separation(flows, days)

    assert (result.years[0].year, result.years[0].bfi) == (2020, None)
    assert result.years[1].bfi is not None
    assert math.isfinite(result.bfi)


def test_a_period_without_flow_is_refused_instead_of_nan():
    """Fixed: a period without flow had the BFI NaN, null in the JSON."""
    days = _days("2020-11-01", 120)

    with pytest.raises(InvalidParameterError) as caught:
        baseflow_separation(np.zeros(days.size), days)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "positive_flow_volume"


def test_a_negative_discharge_is_refused():
    """Fixed: a negative discharge was filtered as if it were one."""
    days = _days("2020-11-01", 120)
    flows = np.full(days.size, 2.0)
    flows[10] = -1.0

    with pytest.raises(InvalidParameterError) as caught:
        baseflow_separation(flows, days)

    assert caught.value.details["reason"] == "outside_physical_range"


def test_the_separation_records_the_versions_of_its_formulas():
    days = _days("2020-11-01", 120)
    flows = 5.0 + np.cos(np.arange(days.size) / 5.0)

    with recording() as used:
        baseflow_separation(flows, days)

    assert used == {
        spec.name: spec.formula_version
        for spec in (LYNE_HOLLICK, BASEFLOW_INDEX, RECESSION)
    }
