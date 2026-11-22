"""The trend and homogeneity statistics against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs of
:mod:`hydrolog.statistics.stationarity` and :mod:`hydrolog.statistics.homogeneity`
(CMP-6.5), with strategies of valid series where the generic ones cannot draw them;
the reference cases are those of ``tests/fixtures/formulas/trend-cases.json``
(CMP-6.1); the exact null distributions are counted over every ordering and every
split (CMP-6.2); SciPy runs beside them (CMP-6.3) and R's trend, modifiedmk, Kendall
and stats through the frozen oracle ``tests/oracles/trend_regime`` (CMP-6.4), each
comparison naming the conventions of both sides. The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import csv
import hashlib
import itertools
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from scipy.stats import kendalltau, ks_2samp, mannwhitneyu, theilslopes

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
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
from hydrolog.statistics import homogeneity, stationarity
from hydrolog.statistics.homogeneity import (
    KS_EXACT,
    PETTITT,
    homogeneity_tests,
    ks_exact,
    pettitt,
)
from hydrolog.statistics.stationarity import (
    MANN_KENDALL,
    SEN_INTERVAL,
    SEN_SLOPE,
    mann_kendall,
    mann_kendall_test,
    sen_interval,
    sen_line,
    sen_slope,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

TESTS = Path(__file__).parents[1]
CASES = TESTS / "fixtures" / "formulas" / "trend-cases.json"
ORACLES = TESTS / "oracles" / "trend_regime"
R = read_frozen_oracle(ORACLES / "r_oracle_outputs_headed.csv")
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (MANN_KENDALL, mann_kendall),
    (SEN_SLOPE, sen_line),
    (SEN_INTERVAL, sen_interval),
    (PETTITT, pettitt),
    (KS_EXACT, ks_exact),
)
SINGLE_SERIES = (
    "gilbert_ex16_1",
    "helsel_ex10_1",
    "kzgw_bobr_bukowka",
    "kzgw_czarna_polana",
    "kzgw_rypienica_rypin",
    "kzgw_swislina_rzepin",
    "pettitt_page",
    "nile",
    "maxau_Q",
    "maxau_s",
    "seeded_ties",
    "seeded_step",
    "luke_peaks",
)
"""The series of r_oracle.R's single-series tests, all at consecutive times."""
TWO_SAMPLES = ("helsel_ex5_1", "luke_peaks", "seeded_step")
"""The pairs of samples of r_oracle.R's two-sample tests (groups 1 and 2)."""


def _datasets() -> dict[str, list[dict[str, str]]]:
    found: dict[str, list[dict[str, str]]] = {}
    with (ORACLES / "datasets.csv").open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            found.setdefault(row["dataset"], []).append(row)
    return found


DATASETS = _datasets()


def _values(dataset: str, group: str | None = None) -> np.ndarray:
    return np.array(
        [
            float(row["value"])
            for row in DATASETS[dataset]
            if group is None or row["group"] == group
        ]
    )


def _times(dataset: str) -> np.ndarray:
    return np.array([float(row["time"]) for row in DATASETS[dataset]])


def _r(dataset: str, package: str, function: str, statistic: str, args=None) -> float:
    """One number of the frozen R oracle."""
    found = [
        float(row["value"])
        for row in R.rows
        if row["dataset"] == dataset
        and row["package"] == package
        and row["fun"] == function
        and row["statistic"] == statistic
        and (args is None or row["args"] == args)
    ]
    assert len(found) == 1, (dataset, package, function, statistic, args)
    return found[0]


# --- generated tests and reference cases (CMP-6.5, CMP-6.1) ------------------------


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


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s, _ in FAMILY])
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s, _ in FAMILY])
@given(data=st.data())
def test_properties(spec: FormulaSpec, function, data):
    inputs = data.draw(strategies(spec))
    assert_property_contract(spec, as_standard(function), inputs, ERRORS)
    assert_properties(spec, as_standard(function), inputs, ERRORS)


@st.composite
def series_in_time(draw, interval: bool) -> dict[str, object]:
    """A series of annual values with its years, several values of a year at times.

    The generic strategy draws values and times of different lengths and out of order,
    which the specs refuse; Sen's slope and its interval need a series and its times.
    """
    n = draw(st.integers(2, 40))
    steps = draw(
        st.lists(st.sampled_from([0.0, 1.0, 1.0, 2.0, 0.5]), min_size=n, max_size=n)
    )
    start = draw(st.floats(-1000.0, 2100.0, allow_nan=False))
    times = start + np.cumsum(steps)
    values = draw(
        st.lists(
            st.one_of(
                st.floats(0.81, 111.0),
                st.sampled_from([0.0, 5.0, 23.0]),
                st.floats(-1.0e6, 1.0e6),
            ),
            min_size=n,
            max_size=n,
        )
    )
    inputs: dict[str, object] = {"values": np.array(values), "times": times}
    if interval:
        inputs["var_s"] = draw(st.floats(0.0, 2.0 * n**3))
        inputs["alpha"] = draw(st.sampled_from([0.01, 0.05, 0.1, 0.5]))
    return inputs


@given(inputs=series_in_time(interval=False))
def test_sen_slope_properties_of_series(inputs):
    assert_property_contract(SEN_SLOPE, as_standard(sen_line), inputs, ERRORS)
    assert_properties(SEN_SLOPE, as_standard(sen_line), inputs, ERRORS)


@given(inputs=series_in_time(interval=True))
def test_sen_interval_properties_of_series(inputs):
    assert_property_contract(SEN_INTERVAL, as_standard(sen_interval), inputs, ERRORS)
    assert_properties(SEN_INTERVAL, as_standard(sen_interval), inputs, ERRORS)


@given(
    inputs=st.fixed_dictionaries(
        {
            "first": st.lists(st.sampled_from([1.0, 2.0, 3.0, 5.0]), min_size=1),
            "second": st.lists(st.sampled_from([1.0, 2.0, 4.0, 5.0]), min_size=1),
        }
    )
)
def test_ks_exact_properties_of_tied_samples(inputs):
    """Samples of a few values, nearly all tied: the case ks_exact is for."""
    assert_property_contract(KS_EXACT, as_standard(ks_exact), inputs, ERRORS)
    assert_properties(KS_EXACT, as_standard(ks_exact), inputs, ERRORS)


# --- the exact null distributions (CMP-6.2) -----------------------------------------


def _s_of_every_ordering(values: list[float]) -> np.ndarray:
    """S of each of the n! orderings of the values (labelled, so ties repeat)."""
    n = len(values)
    orders = np.array(list(itertools.permutations(range(n))), dtype=np.int8)
    ordered = np.asarray(values)[orders]
    total = np.zeros(len(orders), dtype=np.int64)
    for i in range(n - 1):
        for j in range(i + 1, n):
            total += np.sign(ordered[:, j] - ordered[:, i]).astype(np.int64)
    return total


@pytest.mark.parametrize(
    "values",
    [
        [0.25, 1.1, 0.25, 3.0, 1.5, 1.2, 4.0],
        [3.0, 1.0, 2.0, 2.0, 2.0, 7.0, 6.0, 5.0, 9.0],
        [5.0, 5.0, 4.0, 4.0, 3.0, 9.0],
        [1.0, 2.0, 3.0, 4.0, 5.0, 16.0, 7.0],
        [0.0, 0.0, 1.0],
        [2.0, 1.0, 3.0, 0.0, 4.0, 6.0, 5.0, 8.0, 7.0],
        [4.0, 4.0, 4.0, 4.0, 1.0, 1.0, 1.0, 1.0],
    ],
)
def test_the_exact_p_and_var_s_are_those_of_every_ordering(values):
    """Oracle of mann_kendall: the permutation test's definition, in Fractions.

    Every one of the n! orderings of the labelled values is equally likely under no
    trend, so each distinct ordering of tied values counts t! times, as often as any
    other; the variance of S over them is Var(S) with the correction for ties.
    """
    every = _s_of_every_ordering(values)
    found = mann_kendall(values)
    orderings = math.factorial(len(values))
    extreme = int(np.sum(np.abs(every) >= abs(found.s)))
    variance = Fraction(int(np.sum(every.astype(object) ** 2)), orderings)

    assert found.p_value_method == "exact"
    assert_within(
        [found.p_value, found.var_s],
        [float(Fraction(extreme, orderings)), float(variance)],
        abs=0.0,
        reason="both sides round the same rational number once",
    )


def _mahonian(n: int) -> list[int]:
    """M(n, k), the permutations of n with k inversions, by the recurrence
    M(n, k) = M(n, k - 1) + M(n - 1, k) - M(n - 1, k - n), not by products."""
    row = [1]
    for size in range(2, n + 1):
        top = size * (size - 1) // 2
        new = [0] * (top + 1)
        for k in range(top + 1):
            new[k] = (
                (new[k - 1] if k >= 1 else 0)
                + (row[k] if k < len(row) else 0)
                - (row[k - size] if 0 <= k - size < len(row) else 0)
            )
        row = new
    return row


def _with_inversions(n: int, k: int) -> list[float]:
    """A permutation of 0 … n - 1 with k inversions, by its Lehmer code."""
    code = []
    for place in range(n):
        step = min(k, n - 1 - place)
        code.append(step)
        k -= step
    left = list(range(n))
    return [float(left.pop(digit)) for digit in code]


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8, 9])
def test_the_exact_p_without_ties_is_that_of_the_mahonian_numbers(n):
    """Oracle of mann_kendall below ten values: Mahonian numbers of the recurrence."""
    counts = _mahonian(n)
    pairs = n * (n - 1) // 2
    assert sum(counts) == math.factorial(n)
    for k in range(pairs + 1):
        s = pairs - 2 * k
        found = mann_kendall(_with_inversions(n, k))
        tail = sum(c for j, c in enumerate(counts) if abs(pairs - 2 * j) >= abs(s))
        assert found.s == s
        assert_within(
            found.p_value,
            float(Fraction(tail, math.factorial(n))),
            abs=0.0,
            reason="the same rational number rounded once",
        )


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_s_and_the_exact_p_are_scipys_kendalltau(seed):
    """CMP-6.3: SciPy's Kendall tau of the series against its times.

    Conventions: kendalltau(method='exact') is the two-sided p of the permutation
    distribution without ties, the spec's below ten values; tau-b times
    sqrt(n0 (n0 - n1)) is S, n0 = n(n - 1)/2 and n1 the tied pairs of the values.
    """
    rng = np.random.default_rng(seed)
    for n in (4, 6, 9):
        values = rng.permutation(n).astype(float) * 1.5 + 2.0
        found = mann_kendall(values)
        tau = kendalltau(np.arange(n), values, method="exact")
        assert_within(
            [found.p_value, found.s],
            [tau.pvalue, tau.statistic * n * (n - 1) / 2],
            rel=1e-12,
            reason="scipy sums the exact distribution in floating point",
        )
    tied = np.round(rng.gamma(2.0, 20.0, size=60), 0)
    n0 = 60 * 59 // 2
    n1 = sum(t * (t - 1) // 2 for t in np.unique(tied, return_counts=True)[1])
    tau = kendalltau(np.arange(60), tied)
    assert_within(
        mann_kendall(tied).s,
        tau.statistic * math.sqrt(n0 * (n0 - n1)),
        abs=1e-9,
        reason="tau-b is S over sqrt(n0 (n0 - n1)), a few roundings of a few thousand",
    )


def test_the_line_is_scipys_theilslopes():
    """CMP-6.3: scipy.stats.theilslopes, method 'separate' (Conover's intercept).

    Conventions: theilslopes takes the pairs with x_j > x_i, the spec's pairs of
    different times, and method='separate' gives median(y) - slope median(x).
    """
    for dataset in ("kzgw_bobr_bukowka", "maxau_s", "nile", "seeded_ties"):
        values, times = _values(dataset), _times(dataset)
        found = sen_line(values, times)
        scipy = theilslopes(values, times, method="separate")
        assert_within(
            [found.slope, found.intercept],
            [scipy.slope, scipy.intercept],
            rel=1e-13,
            reason="the same slopes and medians; scipy multiplies the median year "
            "of two thousand by the slope in another order",
        )


def test_the_interval_is_the_interpolation_of_the_sorted_slopes():
    """Oracle of sen_interval: the whole ladder of ranks of Hydrolog 0.9.0.dev2.

    The slopes of every pair (numpy.triu_indices), sorted, and numpy.interp over
    the ranks 1 … N': the spec writes the slopes into one array and partitions it.
    """
    from scipy.stats import norm

    for dataset in SINGLE_SERIES:
        values, times = _values(dataset), _times(dataset)
        var_s = mann_kendall(values).var_s
        first, second = np.triu_indices(values.size, 1)
        apart = times[second] > times[first]
        first, second = first[apart], second[apart]
        slopes = np.sort(
            (values[second] - values[first]) / (times[second] - times[first])
        )
        ranks = np.arange(1, slopes.size + 1)
        line = sen_line(values, times)
        median = float(np.median(slopes))
        assert_within(
            [line.slope, line.intercept],
            [median, float(np.median(values) - median * np.median(times))],
            abs=0.0,
            reason="the median of the same slopes, the mean of the middle two as "
            "numpy.median takes it",
        )
        for alpha in (0.05, 0.10):
            reach = float(norm.ppf(1.0 - alpha / 2.0)) * math.sqrt(var_s)
            lower, upper = (slopes.size - reach) / 2.0, (slopes.size + reach) / 2.0 + 1
            if not (lower >= 1.0 and upper <= slopes.size):
                with pytest.raises(InvalidParameterError):
                    sen_interval(values, times, var_s, alpha)
                continue
            found = sen_interval(values, times, var_s, alpha)
            assert_within(
                [found.lower, found.upper],
                [np.interp(lower, ranks, slopes), np.interp(upper, ranks, slopes)],
                abs=0.0,
                reason="the same slopes and the same interpolation on the same two "
                "neighbouring ranks",
            )


# --- the frozen R oracles (CMP-6.4) -------------------------------------------------


def test_the_frozen_inputs_are_those_r_read():
    """datasets.csv is byte for byte the file whose SHA-256 r_oracle_meta.txt names."""
    meta = (ORACLES / "r_oracle_meta.txt").read_text(encoding="utf-8")
    named = meta.split("sha256", 1)[1].split()[0]

    found = hashlib.sha256((ORACLES / "datasets.csv").read_bytes()).hexdigest()

    assert found == named


@pytest.mark.parametrize("dataset", SINGLE_SERIES)
def test_mann_kendall_is_rs(dataset):
    """trend::mk.test, modifiedmk::mkttest and Kendall::MannKendall (R 4.4.3).

    Conventions of R: S and varS corrected for ties, z with the continuity
    correction, the normal p = 2 min(0.5, P(Z > |z|)) for every n; Kendall copies the
    data to single precision. The spec's p is the same normal p from ten values and
    the exact one below, where only S, Var(S) and Z are compared.
    """
    values = _values(dataset)
    found = mann_kendall(values)

    for package, function, name in (
        ("trend", "mk.test", "S"),
        ("modifiedmk", "mkttest", "S"),
        ("Kendall", "MannKendall", "S"),
    ):
        assert found.s == _r(dataset, package, function, name)
    assert_within(
        [found.var_s, found.z],
        [_r(dataset, "trend", "mk.test", "varS"), _r(dataset, "trend", "mk.test", "z")],
        rel=1e-15,
        reason="the same integer quotient and continuity correction; R prints 17 "
        "significant digits",
    )
    if values.size >= 10:
        assert found.p_value_method == "normal"
        assert_within(
            found.p_value,
            _r(dataset, "trend", "mk.test", "p"),
            rel=1e-10,
            reason="scipy's norm.sf and R's pnorm(lower.tail = FALSE), two "
            "implementations of the normal tail, agree to about 1e-10 relative "
            "(8.3e-11 at z = -5.16, Bóbr at Bukówka)",
        )


@pytest.mark.parametrize("dataset", SINGLE_SERIES)
def test_sens_slope_is_rs(dataset):
    """trend::sens.slope and modifiedmk::mkttest's Sen's slope (R 4.4.3).

    Conventions: R's slopes are per step of the index, the spec's per unit of the
    times, here consecutive years or steps: the same slopes.
    """
    found = sen_line(_values(dataset), _times(dataset))

    assert_within(
        [found.slope, found.slope],
        [
            _r(dataset, "trend", "sens.slope", "slope", "conf.level=0.95"),
            _r(dataset, "modifiedmk", "mkttest", "Sen's slope"),
        ],
        rel=1e-15,
        reason="the median of the same slopes; R prints 17 significant digits",
    )


@pytest.mark.parametrize("dataset", SINGLE_SERIES)
@pytest.mark.parametrize(("alpha", "level"), [(0.05, "0.95"), (0.10, "0.90")])
def test_sens_interval_rounds_as_rs(dataset, alpha, level):
    """trend::sens.slope's interval (R 4.4.3) against the spec's convention.

    Conventions: R takes the slope of the rank rounded with round(), the spec
    interpolates linearly between the slopes of the two ranks around it (Gilbert's
    Example 16.5): R's limit is one of those two slopes and the spec's lies between.
    """
    from scipy.stats import norm

    values, times = _values(dataset), _times(dataset)
    var_s = mann_kendall(values).var_s
    slopes = np.sort(stationarity._pair_slopes(values, times))
    reach = float(norm.ppf(1.0 - alpha / 2.0)) * math.sqrt(var_s)
    ranks = ((slopes.size - reach) / 2.0, (slopes.size + reach) / 2.0 + 1.0)
    if not (ranks[0] >= 1.0 and ranks[1] <= slopes.size):
        pytest.skip("no interval of the spec: a rank falls outside the slopes")
    found = sen_interval(values, times, var_s, alpha)

    for limit, rank, name in zip(found, ranks, ("lower", "upper"), strict=True):
        below = slopes[max(math.floor(rank), 1) - 1]
        above = slopes[min(math.ceil(rank), slopes.size) - 1]
        oracle = _r(dataset, "trend", "sens.slope", name, f"conf.level={level}")
        closest = min((below, above), key=lambda slope: abs(slope - oracle))
        assert_within(
            oracle,
            closest,
            rel=1e-15,
            abs=1e-300,
            reason="R's limit is the slope of a whole rank next to the spec's",
        )
        assert below <= limit <= above


@pytest.mark.parametrize("dataset", SINGLE_SERIES)
def test_pettitt_is_rs(dataset):
    """trend::pettitt.test (R 4.4.3).

    Conventions: R's K is max |U_k| over k = 1 … n (U_n = 0) and its estimate every k
    of K, 1-based, the last value before the change; the spec's change point is the
    first such k. The p-value is the same approximation.
    """
    found = pettitt(_values(dataset))

    assert found.k == _r(dataset, "trend", "pettitt.test", "K")
    assert found.change_point_index == _r(dataset, "trend", "pettitt.test", "t_first")
    assert_within(
        found.p_value,
        _r(dataset, "trend", "pettitt.test", "p"),
        rel=4.5e-16,
        reason="the same exponential of the same quotient",
    )


@pytest.mark.parametrize("dataset", TWO_SAMPLES)
def test_ks_exact_is_rs(dataset):
    """stats::ks.test (R 4.4.3), exact with ties (psmirnov, Schröer and Trenkler).

    Conventions: both two-sided and exact with ties for n.x n.y < 10000; R takes D
    from floating-point distribution functions, the spec from whole numbers.
    """
    first, second = _values(dataset, "1"), _values(dataset, "2")
    found = ks_exact(first, second)

    assert _r(dataset, "stats", "ks.test", "exact") == 1.0
    assert_within(
        [found.d, found.p_value],
        [_r(dataset, "stats", "ks.test", "D"), _r(dataset, "stats", "ks.test", "p")],
        rel=1e-12,
        reason="R's D carries a rounding of its distribution functions (0.6 + 1 "
        "ulp) and its p the floating-point sums of psmirnov; the spec counts paths "
        "in integers",
    )


@pytest.mark.parametrize("dataset", TWO_SAMPLES)
def test_the_delegated_mann_whitney_is_helsels_and_rs(dataset):
    """Delegated mann_whitney_u (CMP-1.2): scipy's mannwhitneyu against R and Helsel.

    Conventions: U of the first sample is R's W; both two-sided with the normal
    approximation and the corrections for ties and continuity where ties are present.
    """
    first, second = _values(dataset, "1"), _values(dataset, "2")
    found = mannwhitneyu(first, second, alternative="two-sided")
    assert_within(
        [found.statistic, found.pvalue],
        [
            _r(dataset, "stats", "wilcox.test", "W", "default exact"),
            _r(dataset, "stats", "wilcox.test", "p", "default exact"),
        ],
        rel=1e-14,
        reason="the same rank sums and normal tail; R prints 17 significant digits",
    )


@pytest.mark.parametrize(
    "case", load_cases(CASES, "mann_whitney_u"), ids=lambda case: case.case_id
)
def test_the_delegated_mann_whitney_reference_cases(case: ReferenceCase):
    """Helsel et al. (2020): Example 5.1 and, as a discrepancy, Example 12.3."""
    if case.status == "discrepancy":
        pytest.skip(f"{case.case_id}: discrepancy, {case.discrepancy} (CMP-5.2)")
    found = mannwhitneyu(
        case.inputs["first"], case.inputs["second"], alternative="two-sided"
    )
    assert found.statistic == case.expected["u"]
    assert_within(
        found.pvalue,
        float(str(case.expected["p_value"])),
        abs=case.printed_precision["p_value"] / 2,
        reason="half a unit of the printed p",
    )


def test_the_delegated_ks_2samp_is_exact_without_ties():
    """Delegated ks_two_sample (CMP-1.2) and the established oracle of ks_exact.

    Conventions: scipy's exact two-sided p assumes a continuous distribution, which
    samples without ties keep; the spec counts the same paths in integers.
    """
    separated = ks_2samp([1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0], method="exact")
    assert_within(
        [separated.statistic, separated.pvalue],
        [1.0, 2.0 / 35.0],
        rel=1e-14,
        reason="three values all below four: D = 1, p = 2 / C(7, 3)",
    )
    rng = np.random.default_rng(20261119)
    for m, n in ((5, 7), (12, 12), (30, 41)):
        first, second = rng.normal(0.0, 1.0, m), rng.normal(0.3, 1.0, n)
        scipy = ks_2samp(first, second, method="exact")
        found = ks_exact(first, second)
        assert_within(
            [found.d, found.p_value],
            [scipy.statistic, scipy.pvalue],
            rel=1e-10,
            reason="scipy sums the paths in floating point, the spec in integers",
        )


# --- the traps (CMP-6.6) and statistical procedures (CMP-6.7) -----------------------


def test_a_strong_trend_keeps_a_p_value_above_zero():
    """Trap exp_overflow of mann_kendall: the normal tail of a strong trend.

    50 increasing values: p = 2 P(Z > z) = 1.3317e-24, where 2 (1 - Phi(z)) was 0;
    10,000 values put p below the smallest positive float, which the spec gives.
    """
    fifty = mann_kendall(np.arange(1.0, 51.0))
    long = mann_kendall(np.arange(10_000.0))

    assert_within(
        fifty.p_value,
        math.erfc(fifty.z / math.sqrt(2.0)),
        rel=1e-13,
        reason="norm.sf against the C library's erfc",
    )
    assert long.p_value == math.ulp(0.0)
    assert long.z > 149.0


def test_s_of_a_long_series_is_exact():
    """Trap many_small_terms of mann_kendall: S and Var(S) of 3,000 tied values."""
    rng = np.random.default_rng(20261119)
    values = np.round(rng.gamma(2.0, 20.0, size=3000), 0)
    signs = np.sign(values[np.newaxis, :] - values[:, np.newaxis]).astype(np.int64)
    s = int(np.triu(signs, 1).sum())
    groups = np.unique(values, return_counts=True)[1].tolist()
    n = values.size
    var_s = Fraction(
        n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in groups), 18
    )

    found = mann_kendall(values)

    assert found.s == s
    assert_within(
        found.var_s, float(var_s), abs=0.0, reason="one rounded integer quotient"
    )


def test_a_series_of_one_time_and_slopes_beyond_float64_are_refused():
    """Trap singular_at_bound of sen_slope and sen_interval: 1 / (t_j - t_i)."""
    with pytest.raises(InvalidParameterError) as one_time:
        sen_line([1.0, 2.0, 3.0], [2000.0, 2000.0, 2000.0])
    with pytest.raises(InvalidParameterError) as too_steep:
        sen_line([0.0, 1.0e300, 2.0e300], [0.0, 1.0e-300, 2.0e-300])
    with pytest.raises(InvalidParameterError) as no_interval:
        sen_interval([0.0, 1.0e300], [0.0, 1.0e-300], 1.0, 0.05)

    assert one_time.value.details["constraint"] == "two_times"
    assert too_steep.value.details["constraint"] == "slopes_in_float64"
    assert no_interval.value.details["constraint"] == "slopes_in_float64"


@pytest.mark.parametrize(
    ("var_s", "alpha", "option"),
    [(-5.0, 0.05, "var_s"), (math.nan, 0.05, "var_s"), (50.0, 1.5, "alpha")],
)
def test_sen_slope_refuses_an_impossible_var_s_or_alpha(var_s, alpha, option):
    """A missing check fixed: 0.9.0.dev2 took var_s -5 as 0, gave no interval for
    NaN and the limits swapped for alpha 1.5 (0.652 above 0.565)."""
    values = np.array([3.0, 1, 4, 1.5, 5, 9, 2, 6, 5.5, 8, 7, 10])

    with pytest.raises(InvalidParameterError) as caught:
        sen_slope(values, np.arange(12.0), var_s=var_s, alpha=alpha)

    assert caught.value.details["reason"] == "outside_physical_range"
    assert caught.value.details["option"] == option


def test_a_series_longer_than_sens_memory_bound_is_refused():
    """The O(n^2) slopes: 5,001 values are refused before the slopes are made."""
    with pytest.raises(InvalidParameterError) as caught:
        mann_kendall_test(np.arange(5001.0))

    assert caught.value.details["reason"] == "invalid_shape"
    assert caught.value.details["formula"] == "sen_slope"


@pytest.mark.parametrize("command", ["stats mann-kendall", "stats homogeneity"])
def test_alpha_of_one_is_refused_by_the_catalog(command):
    """Finding 10: the catalog's bound is the open interval its description states."""
    with pytest.raises(InvalidParameterError) as caught:
        run_command(command, {"values": [1.0, 3.0, 2.0, 5.0, 4.0], "alpha": 1})

    assert caught.value.details["option"] == "alpha"
    assert caught.value.details["reason"] == "exclusive_maximum"


def test_sens_interval_needs_six_values_without_ties():
    """sen_slope gives no interval of 5 values without ties at alpha 0.05.

    M1 = (10 - 1.95996 sqrt(16.667)) / 2 = 0.9992 < 1 (finding 8 of the research
    trend-regime: the description said fewer than 5); 6 values have one.
    """
    five = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
    six = np.array([1.0, 3.0, 2.0, 5.0, 4.0, 6.0])

    none = sen_slope(five, np.arange(5.0), var_s=mann_kendall(five).var_s)
    some = sen_slope(six, np.arange(6.0), var_s=mann_kendall(six).var_s)

    assert (none.lower, none.upper) == (None, None)
    assert some.lower is not None and some.upper is not None


def test_a_long_step_keeps_a_p_value_above_zero():
    """Trap exp_overflow of pettitt: exp(-6 K^2 / (n^3 + n^2)) of 4,000 values."""
    found = pettitt(np.r_[np.zeros(2000), np.ones(2000)])

    assert found.k == 2000 * 2000
    assert found.change_point_index == 2000
    assert found.p_value == math.ulp(0.0)


def test_k_of_a_long_series_is_exact():
    """Trap many_small_terms of pettitt: K by the row sums of the signs of pairs.

    U_t = sum_{i<=t} sum_j sgn(x_i - x_j), as the pairs among the first t cancel:
    whole numbers summed in integers, against the spec's mid-ranks in floats.
    """
    rng = np.random.default_rng(20261119)
    values = np.round(rng.gamma(2.0, 20.0, size=1500), 0)
    rows = np.sign(values[:, np.newaxis] - values[np.newaxis, :]).astype(np.int64)
    u = np.cumsum(rows.sum(axis=1))[:-1]

    found = pettitt(values)

    assert found.k == int(np.max(np.abs(u)))
    assert found.change_point_index == int(np.argmax(np.abs(u))) + 1


def test_small_samples_ties_zeros_and_constant_series():
    """CMP-6.7: the definitions on three values, zeros, ties and equal values."""
    equal = mann_kendall([0.0, 0.0, 0.0])
    two_zeros = mann_kendall([0.0, 0.0, 1.0])
    with pytest.raises(InvalidParameterError) as too_short:
        mann_kendall([0.0, 1.0])
    with pytest.raises(InvalidParameterError) as constant:
        pettitt([0.0, 0.0, 0.0])
    same = ks_exact([0.0, 0.0], [0.0, 0.0, 0.0])
    flat = sen_line([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])

    assert (equal.s, equal.var_s, equal.z, equal.p_value) == (0, 0.0, 0.0, 1.0)
    # the orderings of {0, 0, 1}: S = 2, 0, -2 each once; Var(S) = (66 - 18) / 18
    assert two_zeros.s == 2
    assert_within(
        [two_zeros.var_s, two_zeros.p_value],
        [48 / 18, 2 / 3],
        abs=0.0,
        reason="quotients of whole numbers rounded once",
    )
    assert too_short.value.details["constraint"] == "enough_values"
    assert constant.value.details["constraint"] == "values_not_all_equal"
    assert (same.d, same.p_value) == (0.0, 1.0)
    assert (flat.slope, flat.intercept, flat.n_slopes) == (0.0, 0.0, 3)


def test_the_composites_give_the_specs_numbers():
    """mann_kendall_test and homogeneity_tests return what the specs return."""
    values, years = _values("kzgw_bobr_bukowka"), _times("kzgw_bobr_bukowka")
    trend = mann_kendall_test(values, times=years)
    test = mann_kendall(values)
    line = sen_line(values, years)
    interval = sen_interval(values, years, test.var_s, 0.05)
    tested = homogeneity_tests(values, years.astype(int))
    change = pettitt(values)
    half = values.size // 2
    tied = ks_exact(values[:half], values[half:])

    assert (trend.s_statistic, trend.var_s, trend.z_score, trend.p_value) == (
        test.s,
        test.var_s,
        test.z,
        test.p_value,
    )
    assert (trend.sen_slope, trend.sen_intercept) == (line.slope, line.intercept)
    assert (trend.sen_slope_lower, trend.sen_slope_upper) == tuple(interval)
    assert (tested.pettitt.statistic, tested.pettitt.p_value) == (
        change.k,
        change.p_value,
    )
    assert tested.pettitt.change_point_index == change.change_point_index
    assert (tested.kolmogorov_smirnov.statistic, tested.kolmogorov_smirnov.p_value) == (
        tied.d,
        tied.p_value,
    )


def test_the_formulas_record_their_versions():
    values = list(homogeneity._BOBR)
    with recording() as used:
        mann_kendall(values)
        sen_line(values, list(range(len(values))))
        sen_interval(values, list(range(len(values))), 7920.0, 0.05)
        pettitt(values)
        ks_exact(values[:20], values[20:])

    assert used == {spec.name: spec.formula_version for spec, _ in FAMILY}
