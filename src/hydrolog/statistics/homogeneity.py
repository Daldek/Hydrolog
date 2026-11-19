"""Homogeneity tests of a series of annual values: Mann-Whitney, K-S and Pettitt.

A flood frequency analysis takes the annual maxima as a sample of one
distribution; a change of the catchment or of the gauge (a reservoir, a
regulated reach, a moved station) breaks that. The Mann-Whitney U test and the
two-sample Kolmogorov-Smirnov test compare the values before and after a split
year; Pettitt's test finds the most probable change point itself (ADR-0022).

Pettitt's test and the exact Kolmogorov-Smirnov p-value of tied values are declared
by their specs (Nogat's computation standard, ADR-0050, ADR-0063): :data:`PETTITT`
(``pettitt``, :func:`pettitt`) and :data:`KS_EXACT` (``ks_exact``,
:func:`ks_exact`); ``docs/FORMULAS.md`` shows their equations, ranges and sources.
Mann-Whitney's U and the Kolmogorov-Smirnov test without ties are SciPy's, listed
as delegated computations (``hydrolog._formulas.DELEGATED``).

References
----------
Mann, H.B., Whitney, D.R. (1947). On a test of whether one of two random
    variables is stochastically larger than the other. Annals of
    Mathematical Statistics, 18, 50–60.
Smirnov, N.V. (1939). On the estimation of the discrepancy between empirical
    curves of distribution for two independent samples. Bulletin
    Mathématique de l'Université de Moscou, 2(2).
Schröer, G., Trenkler, D. (1995). Exact and randomization distributions of
    Kolmogorov-Smirnov tests two or three samples. Computational Statistics & Data
    Analysis, 20(2), 185–202 (the exact distribution with tied values).
Pettitt, A.N. (1979). A non-parametric approach to the change-point problem.
    Applied Statistics, 28, 126–135.

Examples
--------
>>> import numpy as np
>>> from hydrolog.statistics.homogeneity import homogeneity_tests, ks_exact, pettitt
>>> maxima = np.array([52.0, 48.0, 55.0, 50.0, 47.0, 81.0, 86.0, 79.0, 90.0, 84.0])
>>> result = homogeneity_tests(maxima, np.arange(2001, 2011))
>>> result.split_year, result.pettitt.change_point_year
(2006, 2006)
>>> result.mann_whitney.homogeneous, result.pettitt.homogeneous
(False, True)
>>> pettitt(maxima).k, pettitt(maxima).change_point_index
(25, 5)

Schröer and Trenkler's (1995) samples with ties, as R's ``ks.test`` quotes them:
D = 3/7 and p = 8/33.

>>> found = ks_exact([1.0, 2.0, 2.0, 3.0, 3.0], [1.0, 2.0, 3.0, 3.0, 4.0, 5.0, 6.0])
>>> round(found.d * 7, 12), round(found.p_value * 33, 12)
(3.0, 8.0)
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.stats import ks_2samp, mannwhitneyu, rankdata

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import (
    Constant,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)

__all__ = [
    "KS_EXACT",
    "PETTITT",
    "SPECS",
    "TIER_B",
    "HomogeneityResult",
    "KolmogorovSmirnov",
    "Pettitt",
    "PettittResult",
    "TwoSampleTestResult",
    "homogeneity_tests",
    "ks_exact",
    "pettitt",
]

_MIN_VALUES = 3
"""Fewest values the tests take (as the Mann-Kendall test)."""

# --- sources ---------------------------------------------------------------------

_KZGW: Final = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL: Final = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_TREND_PETTITT: Final = Source(
    citation="Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point "
    "Detection, R package version 1.1.10, CRAN",
    locator="R/pettitt.test.R and its help page: U_k = 2 sum_{i<=k} r_i - k (n + 1) "
    "of the ranks, U* = max |U_k|, the change point where |U_k| is largest, p = "
    "min(1, 2 exp(-6 U*^2 / (n^3 + n^2))), 'good for p <= 0.5' (after Verstraeten et "
    "al. 2006)",
    url="https://cran.r-project.org/package=trend",
)
_PYHOMOGENEITY: Final = Source(
    citation="Hussain, M.M. pyHomogeneity: a Python package for homogeneity tests of "
    "time series data, version 1.1, GitHub mmhs013/pyHomogeneity",
    locator="pyhomogeneity.py, __pettitt and pettitt_test: U = 2 cumsum(r) - k (n + "
    "1) over k = 1 … n - 1, the first k of max |U|, p = 2 exp(-6 U^2 / (n^3 + n^2))",
    url="https://github.com/mmhs013/pyHomogeneity",
)
_PETTITT_1979: Final = Source(
    citation="Pettitt, A.N. (1979). A non-parametric approach to the change-point "
    "problem. Journal of the Royal Statistical Society, Series C (Applied "
    "Statistics) 28(2), 126-135",
    access="author-provided",
)
_R_KS: Final = Source(
    citation="R Core Team. R: A Language and Environment for Statistical Computing, "
    "version 4.4.3, package stats, function ks.test",
    locator="help page ks.test, Details: in the two-sample case an exact p-value is "
    "computed if the product of the sample sizes is less than 10000, with or without "
    "ties (the algorithm of Schröer and Trenkler 1995); Examples: with ties, D = 3/7, "
    "p = 8/33",
    url="https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html",
)
_SCHROER: Final = Source(
    citation="Schröer, G., Trenkler, D. (1995). Exact and randomization distributions "
    "of Kolmogorov-Smirnov tests two or three samples. Computational Statistics & "
    "Data Analysis 20(2), 185-202",
    access="author-provided",
)
_EXAMPLES: Final = (
    "examples 1.1, 1.2, 3.3 and 3.4, tables 1.1, 1.2, 3.10 and 3.13 (pp. 11-56): the "
    "annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at "
    "Rypin and the Świślina at Rzepin"
)

_UNIT: Final = "m3/s"
"""The unit of the series in the documents: the tests rank the values, so a series in
any unit gives the same statistics."""

_ANY_VALUE: Final = Range(
    test_low=-1.0e6,
    test_high=1.0e6,
    test_reason=(
        "the tests rank the values, so any bound tests their arithmetic: a million "
        "m3/s exceeds the discharge of every river, and a stage may lie below 0, so "
        "the same bound holds below 0"
    ),
)
_MAXIMA: Final = Range(
    low=0.81,
    high=111.0,
    source=Source(
        citation=_KZGW,
        locator=f"{_EXAMPLES}: annual maxima of 0.81 to 111 m3/s",
        url=_KZGW_URL,
    ),
)
_BOBR: Final = (
    18.6, 13.2, 22.1, 20.4, 23.0, 10.7, 27.8, 14.7, 8.62, 15.9, 22.1, 16.6, 27.8,
    4.76, 11.3, 32.3, 32.3, 33.8, 21.7, 9.23, 14.3, 8.28, 10.7, 9.16, 10.3, 6.72,
    4.43, 6.72, 3.08, 7.26, 4.70, 6.05, 8.75, 5.24, 6.59, 4.7, 4.16, 4.97, 3.25,
    5.92, 1.9,
)  # fmt: skip
"""The annual maxima of the Bóbr at Bukówka [m3/s], 1965-2005 (KZGW 2017, example
1.1, table 1.1): the typical series of the generated tests, with six tied pairs."""

_RANKS_EXACT: Final = Tolerance(
    abs=0.0,
    reason="the statistics rank the values, which doubling or negating them keeps or "
    "mirrors exactly",
)


def _sample(name: str, symbol: str, description: str) -> Variable:
    return Variable(
        name=name,
        symbol=symbol,
        unit=_UNIT,
        kind="real_array",
        description=description,
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MAXIMA,
    )


# --- Pettitt's change-point test -----------------------------------------------------


class Pettitt(NamedTuple):
    """Pettitt's K, its p-value and the change point (spec ``pettitt``)."""

    k: int
    p_value: float
    change_point_index: int


def _pettitt(data: NDArray[np.float64]) -> Pettitt:
    """Return K, its approximate p-value and the split t of K of two values or more.

    U_t = 2 Σ_{i≤t} r_i − t(n + 1) of the mid-ranks: whole numbers, exact in float64
    below n of about 10⁷.
    """
    n = data.size
    t = np.arange(1, n)
    u = 2.0 * np.cumsum(rankdata(data))[:-1] - t * (n + 1.0)
    best = int(np.argmax(np.abs(u)))
    k = float(abs(u[best]))
    p_value = min(1.0, 2.0 * math.exp(-6.0 * k * k / (float(n) ** 3 + float(n) ** 2)))
    return Pettitt(int(k), p_value, best + 1)


def _pairwise_pettitt(values: Sequence[float]) -> tuple[int, int]:
    """K and its first t by the definition U_t = Σ_{i≤t} Σ_{j>t} sgn(x_i − x_j)."""
    n = len(values)
    found = [
        abs(
            sum(
                (values[i] > values[j]) - (values[i] < values[j])
                for i in range(t)
                for j in range(t, n)
            )
        )
        for t in range(1, n)
    ]
    k = max(found)
    return k, found.index(k) + 1


def _pairwise_definition(run: Callable[..., Values]) -> None:
    """K and t of the ranks equal those of the pairwise signs, ties included."""
    rng = np.random.default_rng(20261119)
    for n in (2, 3, 7, 25, 40):
        values = rng.integers(0, 8, size=n).astype(float).tolist()
        if len(set(values)) == 1:
            values[0] += 1.0
        out = run(values=values)
        k, t = _pairwise_pettitt(values)
        assert_within(
            [out.integer("k"), out.integer("change_point_index")],
            [k, t],
            abs=0.0,
            reason="whole numbers: the rank form and the double sum of signs agree "
            "exactly, mid-ranks for ties",
        )


def _negated(x: Values) -> dict[str, object]:
    return {name: -x.array(name) for name in x}


PETTITT: Final = FormulaSpec(
    name="pettitt",
    title="Pettitt's change-point test: K, the change point and the approximate p",
    function="hydrolog.statistics.homogeneity.pettitt",
    family="statistic",
    equation=(
        "U_t = 2 sum_{i<=t} r_i - t (n + 1) = sum_{i<=t} sum_{j>t} sgn(x_i - x_j) for "
        "t = 1 … n - 1 with the mid-ranks r_i; K = max_t |U_t|, the change point the "
        "first t of K; p = min(1, 2 exp(-6 K^2 / (n^3 + n^2)))"
    ),
    latex=(
        r"U_t = 2\sum_{i \le t} r_i - t(n + 1),\quad K = \max_{1 \le t < n} |U_t|,"
        r"\quad p = \min\left(1,\ 2 e^{-6K^2/(n^3 + n^2)}\right)"
    ),
    variables=(
        _sample(
            "values",
            "x_i",
            "The series in time order, e.g. annual maxima, in any unit.",
        ),
    ),
    outputs=(
        Output(
            name="k",
            unit="-",
            kind="integer",
            symbol="K",
            description="Pettitt's statistic, the largest |U_t|.",
            physical=Range(low=0.0),
        ),
        Output(
            name="p_value",
            unit="-",
            symbol="p",
            description="The approximate two-sided p-value of no change; one below "
            "the smallest positive float is set to it.",
            physical=Range(low=0.0, low_inclusive=False, high=1.0),
        ),
        Output(
            name="change_point_index",
            unit="-",
            kind="integer",
            symbol="t",
            description="The split t of K: the number of values before the change.",
            physical=Range(low=1.0),
        ),
    ),
    sources=(_TREND_PETTITT, _PYHOMOGENEITY, _PETTITT_1979),
    constraints=(
        Constraint(
            name="enough_values",
            cls="precondition",
            check=lambda x: x.array("values").size >= 2,
            text="n >= 2: a split t of 1 … n - 1",
            source=_PYHOMOGENEITY,
            satisfied={"values": [1.0, 2.0, 4.0]},
            boundary={"values": [1.0, 2.0]},
            violated={"values": [1.0]},
        ),
        Constraint(
            name="values_not_all_equal",
            cls="precondition",
            check=lambda x: bool(np.ptp(x.array("values")) > 0.0),
            text="min(x) < max(x): equal values give U_t = 0 for every t, no change "
            "point",
            source=_TREND_PETTITT,
            satisfied={"values": [5.0, 5.0, 5.0, 6.0]},
            violated={"values": [5.0, 5.0, 5.0, 5.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={},
                tolerance=_RANKS_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="negated_series",
                text="the negated series has the same K, change point and p",
                inputs=_negated,
                outputs=lambda out: {
                    "k": out.integer("k"),
                    "p_value": out.real("p_value"),
                    "change_point_index": out.integer("change_point_index"),
                },
                tolerance=_RANKS_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="complete_separation",
                text="ten increasing values: K = n^2/4 = 25 at t = 5 and p = 2 "
                "exp(-6 625 / 1100)",
                inputs={"values": [float(value) for value in range(1, 11)]},
                expected={
                    "k": 25,
                    "change_point_index": 5,
                    "p_value": 2.0 * math.exp(-3750.0 / 1100.0),
                },
                tolerance=Tolerance(
                    abs=1e-17,
                    reason="the same exponential of the same quotient of whole "
                    "numbers, rounded once each",
                ),
            ),
            Limit(
                name="pairwise_definition",
                text="K and its t from the ranks equal those of the double sum of "
                "signs",
                check=_pairwise_definition,
            ),
        ),
    ),
    validation=(
        "none: a test of the hypothesis of no change; its sources compare it with no "
        "observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "the mid-ranks of tied values (scipy's rankdata, R's rank)",
        "K over t = 1 … n - 1 (R's trend also takes t = n, where U_n = 0); the change "
        "point is the first t of K (R's trend returns every t of K), the number of "
        "values before the change, which names the year of the first value after it "
        "in homogeneity_tests",
        "p is Pettitt's approximation 2 exp(-6 K^2 / (n^3 + n^2)), capped at 1, good "
        "for p <= 0.5 (R's trend); it is conservative for short series: ten "
        "increasing values give 0.066 where the exact permutation p is 2 / C(10, 5) "
        "= 0.0079",
        "a p-value below the smallest positive float is set to it, the end of the "
        "physical range (0, 1]",
    ),
    assumptions=("independent values with one change of location at most",),
    traps={
        "exp_overflow": "exp(-6 K^2 / (n^3 + n^2)) of a long series with a step "
        "underflows: p is the smallest positive float, not 0 "
        "(test_a_long_step_keeps_a_p_value_above_zero)",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "many_small_terms": "the cumulative sums of the mid-ranks are whole numbers "
        "and half-numbers, exact in float64 (limit pairwise_definition, "
        "test_k_of_a_long_series_is_exact)",
    },
    reference_cases=("tests/fixtures/formulas/trend-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="U_t by its double sum of signs of the pairs on either side "
            "of t, not the ranks",
            test="tests/unit/test_formulas_trend.py (limit pairwise_definition)",
        ),
        Oracle(
            kind="frozen",
            description="R 4.4.3 trend 1.1.10 pettitt.test on 13 series",
            test="tests/oracles/trend_regime/r_oracle_outputs_headed.csv "
            "(tests/unit/test_formulas_trend.py, test_pettitt_is_rs)",
            conventions=(
                "R's estimate is every t of K, 1-based, the last value before the "
                "change: its smallest is the spec's change point",
            ),
        ),
    ),
    base={"values": list(_BOBR)},
)


def pettitt(values: NDArray[np.float64] | Sequence[float]) -> Pettitt:
    """Locate the most probable change point of a series, spec pettitt.

    Parameters
    ----------
    values : array_like of float
        The series in time order.

    Returns
    -------
    Pettitt
        Pettitt's statistic, its approximate two-sided p-value and the number of
        values before the change.

    Raises
    ------
    InvalidParameterError
        If the series is refused by the spec: too short, all equal or not finite.
    """
    x = checked_inputs(PETTITT, values=values)
    out = checked_outputs(PETTITT, _pettitt(x.array("values"))._asdict())
    return Pettitt(
        out.integer("k"), out.real("p_value"), out.integer("change_point_index")
    )


# --- the exact two-sample Kolmogorov-Smirnov p-value ---------------------------------


class KolmogorovSmirnov(NamedTuple):
    """D of two samples and its exact two-sided p-value (spec ``ks_exact``)."""

    d: float
    p_value: float


def _ks_exact(
    first: NDArray[np.float64], second: NDArray[np.float64]
) -> KolmogorovSmirnov:
    """D and the exact two-sided P(D ≥ d) of two samples, ties respected.

    Under homogeneity every choice of the m values of the first sample among the
    m + n pooled ones is equally likely: a lattice path from (0, 0) to (m, n), a step
    of i per value of the first sample and of j per value of the second, the values
    in ascending order. D = max |i/m − j/n| is taken only where a group of equal
    values ends; the paths that keep |i n − j m| below the observed m n D at every
    such end are counted, in integers, so P(D ≥ d) = 1 − count / C(m + n, m)
    (Schröer and Trenkler, 1995; R's ``ks.test`` from 4.x).
    """
    m, n = first.size, second.size
    values, counts = np.unique(np.concatenate([first, second]), return_counts=True)
    ends = {int(end) for end in np.cumsum(counts)}
    in_first = np.searchsorted(np.sort(first), values, side="right")
    in_second = np.searchsorted(np.sort(second), values, side="right")
    distance = int(np.max(np.abs(in_first * n - in_second * m)))
    paths = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                paths[0][0] = 1
                continue
            if i + j in ends and abs(i * n - j * m) >= distance:
                continue  # the path reaches the observed distance here
            paths[i][j] = (paths[i - 1][j] if i else 0) + (paths[i][j - 1] if j else 0)
    total = math.comb(m + n, m)
    return KolmogorovSmirnov(distance / (m * n), (total - paths[m][n]) / total)


def _ks_distance(first: Sequence[float], second: Sequence[float]) -> Fraction:
    """D of two samples in rational arithmetic, at every pooled value."""
    m, n = len(first), len(second)
    return max(
        abs(
            Fraction(sum(value <= cut for value in first), m)
            - Fraction(sum(value <= cut for value in second), n)
        )
        for cut in set(first) | set(second)
    )


def _every_split(run: Callable[..., Values]) -> None:
    """P(D ≥ d) over every split of the pooled values, counted one by one."""
    for first, second in (
        ([1.0, 2.0, 2.0, 3.0, 3.0], [1.0, 2.0, 3.0, 3.0, 4.0, 5.0, 6.0]),
        ([0.59, 0.87, 1.1, 1.1, 1.2], [0.3, 0.7, 0.7, 1.1, 1.3, 9.7]),
        ([5.0, 5.0, 5.0, 6.0], [5.0, 6.0, 6.0, 6.0]),
        ([2.0, 4.0, 6.0], [1.0, 3.0, 5.0, 7.0]),
    ):
        out = run(first=first, second=second)
        pooled = first + second
        observed = _ks_distance(first, second)
        splits = list(itertools.combinations(range(len(pooled)), len(first)))
        extreme = 0
        for chosen in splits:
            part = [pooled[i] for i in chosen]
            rest = [pooled[i] for i in range(len(pooled)) if i not in chosen]
            extreme += _ks_distance(part, rest) >= observed
        assert_within(
            [out.real("d"), out.real("p_value")],
            [float(observed), float(Fraction(extreme, len(splits)))],
            rel=2.3e-16,
            reason="D and p are quotients of whole numbers, each rounded once",
        )


def _swapped(x: Values) -> dict[str, object]:
    return {"first": x.array("second"), "second": x.array("first")}


KS_EXACT: Final = FormulaSpec(
    name="ks_exact",
    title="Exact two-sided p-value of the two-sample Kolmogorov-Smirnov D, ties "
    "respected",
    function="hydrolog.statistics.homogeneity.ks_exact",
    family="statistic",
    equation=(
        "D = max_x |F1(x) - F2(x)| of the empirical distribution functions; p = "
        "P(D' >= D) over the C(m + n, m) equally likely splits of the pooled values "
        "into samples of m and n, ties respected: 1 - (the lattice paths from (0, 0) "
        "to (m, n) that keep |i n - j m| < m n D wherever a group of equal values "
        "ends) / C(m + n, m)"
    ),
    latex=(
        r"D = \max_x |F_1(x) - F_2(x)|,\quad p = 1 - \frac{\#\{\text{paths with } "
        r"|i n - j m| < m n D \text{ at the ends of the ties}\}}{\binom{m + n}{m}}"
    ),
    variables=(
        _sample("first", "x", "The first sample, e.g. the values before a split."),
        _sample("second", "y", "The second sample, in the unit of the first."),
    ),
    outputs=(
        Output(
            name="d",
            unit="-",
            symbol="D",
            description="The largest distance between the samples' distribution "
            "functions.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="p_value",
            unit="-",
            symbol="p",
            description="The exact two-sided p-value of one distribution.",
            physical=Range(low=0.0, low_inclusive=False, high=1.0),
        ),
    ),
    sources=(_R_KS, _SCHROER),
    constraints=(
        Constraint(
            name="exact_size",
            cls="precondition",
            check=lambda x: (
                x.array("first").size * x.array("second").size < KS_EXACT_PRODUCT
            ),
            text="m n < 10000, R's bound of its exact test: the paths are counted on "
            "the lattice of the m n points",
            source=_R_KS,
            satisfied={"first": [1.0] * 99, "second": [2.0] * 100},
            violated={"first": [1.0] * 100, "second": [2.0] * 100},
        ),
    ),
    constants=(
        Constant(
            name="exact_product",
            value=Fraction(10_000),
            unit="-",
            symbol="m n",
            source=_R_KS,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_samples",
                inputs={"first": 1.0, "second": 1.0},
                outputs={},
                tolerance=_RANKS_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="swapped_samples",
                text="the samples swapped give the same D and p",
                inputs=_swapped,
                outputs=lambda out: {
                    "d": out.real("d"),
                    "p_value": out.real("p_value"),
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the lattice transposed: the same whole numbers, quotients",
                ),
            ),
            Symmetry(
                name="negated_samples",
                text="the negated samples give the same D and p",
                inputs=_negated,
                outputs=lambda out: {
                    "d": out.real("d"),
                    "p_value": out.real("p_value"),
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the paths run backwards through the same ends of ties",
                ),
            ),
        ),
        limits=(
            Limit(
                name="complete_separation",
                text="three values all below four others: D = 1 and p = 2 / C(7, 3)",
                inputs={"first": [1.0, 2.0, 3.0], "second": [4.0, 5.0, 6.0, 7.0]},
                expected={"d": 1.0, "p_value": 2.0 / 35.0},
                tolerance=Tolerance(abs=0.0, reason="a quotient of whole numbers"),
            ),
            Limit(
                name="every_split",
                text="p equals P(D' >= D) counted over every split of the pooled "
                "values in rational arithmetic",
                check=_every_split,
            ),
        ),
    ),
    validation=(
        "none: the exact null distribution of a test statistic; its sources compare "
        "it with no observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "two-sided; D taken only where a group of equal values ends, as the "
        "empirical distribution functions are steps there",
        "homogeneity_tests takes it for samples with ties and m n < 10000; scipy's "
        "ks_2samp, exact for a continuous distribution, without ties and beyond "
        "(conservative with ties: Helsel et al. 2020, Example 5.1, 0.0524 against "
        "0.0478)",
        "the samples in any unit: D and p have none",
    ),
    assumptions=(
        "independent values; under homogeneity every split of the pooled values is "
        "equally likely",
    ),
    traps={
        "gap_propagation": "type cases first-nan_element and second-nan_element: a "
        "gap is refused",
        "many_small_terms": "the paths are counted in Python integers, exact however "
        "many (C(198, 99) is about 2e58), and p is one quotient (limit every_split)",
    },
    reference_cases=("tests/fixtures/formulas/trend-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="P(D' >= D) over every split of the pooled values, counted "
            "one by one in rational arithmetic",
            test="tests/unit/test_formulas_trend.py (limit every_split)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.ks_2samp with method='exact' (SciPy 1.18.1) on "
            "samples without ties",
            test="tests/unit/test_formulas_trend.py "
            "(test_the_delegated_ks_2samp_is_exact_without_ties)",
            conventions=(
                "scipy's exact two-sided p assumes a continuous distribution, the "
                "spec's without ties",
            ),
        ),
        Oracle(
            kind="frozen",
            description="R 4.4.3 stats::ks.test, exact, on three pairs of samples "
            "with ties",
            test="tests/oracles/trend_regime/r_oracle_outputs_headed.csv "
            "(tests/unit/test_formulas_trend.py, test_ks_exact_is_rs)",
            conventions=(
                "R's ks.test from 4.3 computes the exact two-sided p with ties "
                "(psmirnov, Schröer and Trenkler 1995), the spec's",
            ),
        ),
    ),
    base={"first": list(_BOBR[:20]), "second": list(_BOBR[20:])},
)

KS_EXACT_PRODUCT: Final[int] = int(KS_EXACT.constant("exact_product"))


def ks_exact(
    first: NDArray[np.float64] | Sequence[float],
    second: NDArray[np.float64] | Sequence[float],
) -> KolmogorovSmirnov:
    """Compare two samples by the exact Kolmogorov-Smirnov test, spec ks_exact.

    Parameters
    ----------
    first, second : array_like of float
        The two samples.

    Returns
    -------
    KolmogorovSmirnov
        The largest distance between their distribution functions and its exact
        two-sided p-value, ties respected.

    Raises
    ------
    InvalidParameterError
        If the samples are refused by the spec: empty, not finite or too large for
        the exact count.
    """
    x = checked_inputs(KS_EXACT, first=first, second=second)
    found = _ks_exact(x.array("first"), x.array("second"))
    out = checked_outputs(KS_EXACT, found._asdict())
    return KolmogorovSmirnov(out.real("d"), out.real("p_value"))


SPECS: Final[tuple[FormulaSpec, ...]] = (PETTITT, KS_EXACT)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="homogeneity_split",
        function="hydrolog.statistics.homogeneity.homogeneity_tests",
        definition="the first part is the first n // 2 values, or the values of the "
        "years before split_year; the second part the rest",
        convention="split_year and Pettitt's change_point_year name the year of the "
        "first value of the second part (ADR-0022)",
        source=Source(
            citation="Hydrolog, ADR-0022 (2026-11-06): homogeneity tests of annual "
            "maxima",
            locator="decisions 2 and 5",
            url="docs/decisions/0022-homogeneity-tests.md",
        ),
    ),
    TierBSpec(
        name="homogeneity_decision",
        function="hydrolog.statistics.homogeneity.homogeneity_tests",
        definition="a test is homogeneous when its p-value is at least alpha; "
        "Mann-Whitney's U is scipy's mannwhitneyu, the Kolmogorov-Smirnov p scipy's "
        "ks_2samp without ties or with m n >= 10000, else the spec ks_exact",
        convention="two-sided tests at the caller's alpha",
        source=Source(
            citation="Hydrolog, ADR-0022 (2026-11-06): homogeneity tests of annual "
            "maxima",
            locator="decision 6",
            url="docs/decisions/0022-homogeneity-tests.md",
        ),
    ),
)
"""The Tier B formulas of the module (Nogat CMP-2.2)."""


# --- the three tests of a split series, as stats homogeneity gives them --------------


@dataclass
class TwoSampleTestResult(JsonResultMixin):
    """Result of a test that compares the two parts of the split series.

    Attributes
    ----------
    statistic : float
        Statistic of the test.
    p_value : float
        Two-sided p-value of the null hypothesis that both parts come from one
        distribution.
    homogeneous : bool
        True when ``p_value`` is not below the significance level (the test
        does not reject homogeneity).
    """

    statistic: float
    p_value: float
    homogeneous: bool


@dataclass
class PettittResult(JsonResultMixin):
    """Result of Pettitt's change-point test.

    Attributes
    ----------
    statistic : float
        K, the largest ``|U_t|`` over the splits ``t = 1, ..., n - 1`` (spec
        ``pettitt``).
    p_value : float
        Pettitt's approximate two-sided p-value, at most 1.
    homogeneous : bool
        True when ``p_value`` is not below the significance level (the test
        does not reject homogeneity).
    change_point_index : int
        The split ``t`` of K (the first if several give K): the number of values
        before the change, i.e. the 0-based index of the first value after it.
    change_point_year : int or None
        Year of the first value after the change; ``None`` without years.
    """

    statistic: float
    p_value: float
    homogeneous: bool
    change_point_index: int
    change_point_year: int | None


@dataclass
class HomogeneityResult(JsonResultMixin):
    """Result of the homogeneity tests of a series.

    Attributes
    ----------
    n_years : int
        Number of values of the series (one a year).
    split_index : int
        Number of values of the first part, i.e. the 0-based index of the first
        value of the second part.
    split_year : int or None
        Year of the first value of the second part; ``None`` without years.
    mann_whitney : TwoSampleTestResult
        Mann-Whitney U test of the two parts; the statistic is U of the first
        part (about ``n1·n2/2`` under homogeneity, 0 when every value of the
        first part is smaller than every value of the second).
    kolmogorov_smirnov : TwoSampleTestResult
        Two-sample Kolmogorov-Smirnov test of the two parts; the statistic is the
        largest distance D between their empirical distribution functions.
    pettitt : PettittResult
        Pettitt's change-point test of the whole series.
    significance_level : float
        Alpha level used for the decisions ``homogeneous``.
    """

    n_years: int
    split_index: int
    split_year: int | None
    mann_whitney: TwoSampleTestResult
    kolmogorov_smirnov: TwoSampleTestResult
    pettitt: PettittResult
    significance_level: float


def homogeneity_tests(
    series: NDArray[np.floating],
    years: NDArray[np.integer] | None = None,
    *,
    split_year: int | None = None,
    alpha: float = 0.05,
) -> HomogeneityResult:
    """Test a series of annual values for homogeneity.

    Splits the series in two and compares the parts with the Mann-Whitney U
    test and the two-sample Kolmogorov-Smirnov test (both two-sided, scipy's
    ``mannwhitneyu`` and ``ks_2samp``, the latter replaced for tied values, see the
    notes), and looks for the most probable change point with Pettitt's test
    (ADR-0022).

    Parameters
    ----------
    series : NDArray[np.floating]
        1-D array of the values in time order, e.g. annual maxima [m3/s]; at
        least 3, not all equal.
    years : NDArray[np.integer] or None, optional
        Year of every value: integers, strictly increasing (gaps allowed).
        Needed for ``split_year``; without them the result gives no years.
    split_year : int or None, optional
        First year of the second part: the values of the years before it form
        the first part. It need not be a year of the series but must leave a
        value in each part. By default the first part is the first ``n // 2``
        values.
    alpha : float, optional
        Significance level of the decisions ``homogeneous`` (default 0.05).

    Returns
    -------
    HomogeneityResult
        The split and the statistic, p-value and decision of each test.

    Raises
    ------
    InvalidParameterError
        If a value is not a finite number (``details.reason`` ``not_finite``);
        if ``years`` are not integers, not one per value or not strictly
        increasing (``type``, ``length_mismatch``, ``not_increasing``); if
        ``split_year`` is given without ``years`` (``option`` ``years``,
        ``required``) or leaves a part empty (``option`` ``split_year``,
        ``range``, with ``minimum`` and ``maximum``).
    CalculationError
        If there are fewer than 3 values (``too_few_values``, with ``count`` and
        ``minimum``) or all values are equal (``constant_values``).

    Notes
    -----
    Mann-Whitney's p-value is exact when a part has at most 8 values and there
    are no ties, otherwise it comes from the normal approximation with the
    corrections for ties and continuity. The Kolmogorov-Smirnov p-value is exact:
    scipy's without tied values, and with them (annual maxima published to three
    significant digits often tie) that of the spec ``ks_exact`` (:func:`ks_exact`),
    as R's ``ks.test`` (scipy's assumes no ties and is then too large), when
    m·n < 10 000; beyond, with ties, scipy's conservative value. Pettitt's test is
    the spec ``pettitt`` (:func:`pettitt`). The change point is given like the
    split, by the first value after the change, so
    ``split_year=result.pettitt.change_point_year`` makes the two-sample tests
    compare the parts Pettitt's test found. A test is ``homogeneous`` when
    ``p_value >= alpha`` (Tier B ``homogeneity_decision``); the module's examples
    test a series with a step.
    """
    values = np.asarray(series, dtype=float)
    broken = ~np.isfinite(values)
    if broken.any():
        index = int(np.argmax(broken))
        raise InvalidParameterError(
            f"series[{index}] is not a finite number",
            details={"option": "series", "reason": "not_finite", "index": index},
        )
    n = int(values.size)
    labels = _checked_years(years, n)
    if n < _MIN_VALUES:
        raise CalculationError(
            f"The homogeneity tests need at least {_MIN_VALUES} values, got {n}",
            details={"reason": "too_few_values", "count": n, "minimum": _MIN_VALUES},
            hint="Provide a longer series.",
        )
    split = _split_index(labels, n, split_year)
    if values.min() == values.max():
        raise CalculationError(
            f"All {n} values of the series are equal: the homogeneity tests have "
            "nothing to compare",
            details={"reason": "constant_values"},
        )

    first, second = values[:split], values[split:]
    mann_whitney = mannwhitneyu(first, second, alternative="two-sided")
    ks_statistic, ks_p_value = _kolmogorov_smirnov(first, second)
    change = pettitt(values)
    return HomogeneityResult(
        n_years=n,
        split_index=split,
        split_year=None if labels is None else int(labels[split]),
        mann_whitney=_decided(
            float(mann_whitney.statistic), float(mann_whitney.pvalue), alpha
        ),
        kolmogorov_smirnov=_decided(ks_statistic, ks_p_value, alpha),
        pettitt=PettittResult(
            statistic=float(change.k),
            p_value=change.p_value,
            homogeneous=change.p_value >= alpha,
            change_point_index=change.change_point_index,
            change_point_year=(
                None if labels is None else int(labels[change.change_point_index])
            ),
        ),
        significance_level=alpha,
    )


def _checked_years(
    years: NDArray[np.integer] | None, n: int
) -> NDArray[np.integer] | None:
    """Check the years: integers, one per value, strictly increasing."""
    if years is None:
        return None
    labels = np.asarray(years)
    if not np.issubdtype(labels.dtype, np.integer):
        raise InvalidParameterError(
            f"years must be integers, got {labels.dtype} values",
            details={"option": "years", "reason": "type", "expected": "integer"},
        )
    if labels.shape != (n,):
        raise InvalidParameterError(
            f"{labels.size} years for {n} values",
            details={
                "option": "years",
                "reason": "length_mismatch",
                "years": int(labels.size),
                "values": n,
            },
        )
    backwards = np.diff(labels) <= 0
    if backwards.any():
        index = int(np.argmax(backwards)) + 1
        raise InvalidParameterError(
            f"years must increase strictly; years[{index}] = {labels[index]} does "
            f"not follow {labels[index - 1]}",
            details={"option": "years", "reason": "not_increasing", "index": index},
        )
    return labels


def _split_index(
    labels: NDArray[np.integer] | None, n: int, split_year: int | None
) -> int:
    """Count the values of the first part: the halves or the years before the split."""
    if split_year is None:
        return n // 2
    if labels is None:
        raise InvalidParameterError(
            "split_year needs the years of the values",
            details={"option": "years", "reason": "required"},
            hint=(
                "Give the years, or leave out split_year to split the series into "
                "halves."
            ),
        )
    split = int(np.count_nonzero(labels < split_year))
    if 0 < split < n:
        return split
    first, last = int(labels[0]), int(labels[-1])
    part = "first" if split == 0 else "second"
    raise InvalidParameterError(
        f"split_year {split_year} leaves the {part} part empty: the years run from "
        f"{first} to {last}",
        details={
            "option": "split_year",
            "reason": "range",
            "value": str(split_year),
            "minimum": first + 1,
            "maximum": last,
        },
        hint=f"Give a split_year from {first + 1} to {last}.",
    )


def _kolmogorov_smirnov(
    first: NDArray[np.float64], second: NDArray[np.float64]
) -> tuple[float, float]:
    """Two-sample Kolmogorov-Smirnov D and its two-sided p-value.

    With tied values and m·n below the bound of the spec ``ks_exact`` the p-value is
    exact for the ties (:func:`ks_exact`); otherwise it is scipy's ``ks_2samp``,
    exact without ties for these sizes.
    """
    pooled = np.concatenate([first, second])
    if (
        np.unique(pooled).size == pooled.size
        or first.size * second.size >= KS_EXACT_PRODUCT
    ):
        found = ks_2samp(first, second, alternative="two-sided")
        return float(found.statistic), float(found.pvalue)
    exact = ks_exact(first, second)
    return exact.d, exact.p_value


def _decided(statistic: float, p_value: float, alpha: float) -> TwoSampleTestResult:
    """Decide a two-sample test at ``alpha``."""
    return TwoSampleTestResult(
        statistic=statistic, p_value=p_value, homogeneous=p_value >= alpha
    )
