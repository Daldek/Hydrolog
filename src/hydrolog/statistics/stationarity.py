"""Mann-Kendall trend test and Sen's slope for hydrological time series.

The non-parametric Mann-Kendall test of a monotonic trend in a series ordered in time,
which KZGW (2017) asks for before a frequency analysis, and Sen's estimate of the slope
of the trend with Conover's intercept and Gilbert's confidence interval, declared by
their specs (Nogat's computation standard, ADR-0050, ADR-0063): :data:`MANN_KENDALL`
(``mann_kendall``, :func:`mann_kendall`), :data:`SEN_SLOPE` (``sen_slope``,
:func:`sen_line`) and :data:`SEN_INTERVAL` (``sen_interval``, :func:`sen_interval`);
``docs/FORMULAS.md`` shows their equations, constants, ranges and sources.
:func:`mann_kendall_test` and :func:`sen_slope` compose them into the results of
``stats mann-kendall``.

References
----------
Mann, H.B. (1945). Nonparametric tests against trend.
    Econometrica, 13, 245–259.
Kendall, M.G. (1975). Rank Correlation Methods, 4th ed.
    Griffin, London (the variance of S corrected for ties).
Hirsch, R.M., Slack, J.R., Smith, R.A. (1982). Techniques of trend analysis for
    monthly water quality data. Water Resources Research, 18(1), 107–121.
Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau.
    Journal of the American Statistical Association, 63, 1379–1389.
Conover, W.J. (1980). Practical Nonparametric Statistics, 2nd ed. Wiley, New York
    (the intercept median(x) − slope · median(t)).
Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring.
    Van Nostrand Reinhold, New York, Eq. 16.3 (the variance of S with ties),
    sections 16.4.1–16.4.2 (the exact distribution of S for small n, the normal one
    from n = 10) and section 16.5 (the confidence interval of the slope).
MacMahon, P.A. (1916). Combinatory Analysis, Vol. 1. Cambridge University Press
    (the numbers of inversions of the orderings of a multiset).

Examples
--------
>>> import numpy as np
>>> from hydrolog.statistics.stationarity import mann_kendall_test, sen_slope
>>> result = mann_kendall_test(np.arange(1.0, 21.0))
>>> result.trend_detected, result.trend_direction, result.sen_slope
(True, 'increasing', 1.0)

Helsel et al. (2020), Example 10.3: seven values, the exact p-value.

>>> small = mann_kendall_test(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 16.0, 7.0]))
>>> small.s_statistic, small.p_value_method, round(small.p_value, 6)
(19.0, 'exact', 0.002778)

Gilbert (1987), Example 16.5: eight values of five time periods.

>>> times = np.array([1, 1, 1, 2, 3, 3, 4, 5], dtype=float)
>>> data = np.array([10, 22, 21, 30, 22, 30, 40, 40], dtype=float)
>>> estimate = sen_slope(data, times, var_s=58.1, alpha=0.10)
>>> estimate.slope, round(estimate.lower, 1), round(estimate.upper, 1)
(5.5, 2.6, 9.3)
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, NamedTuple, cast

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
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
    "MANN_KENDALL",
    "SEN_INTERVAL",
    "SEN_SLOPE",
    "SPECS",
    "TIER_B",
    "MannKendall",
    "MannKendallResult",
    "SenInterval",
    "SenLine",
    "SenSlope",
    "mann_kendall",
    "mann_kendall_test",
    "sen_interval",
    "sen_line",
    "sen_slope",
]

# --- sources ---------------------------------------------------------------------

_GILBERT: Final = (
    "Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution "
    "Monitoring. Van Nostrand Reinhold, New York"
)
_GILBERT_URL: Final = (
    "https://digital.library.unt.edu/ark:/67531/metadc1197046/m2/1/high_res_d/"
    "7037501.pdf"
)
_KZGW: Final = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL: Final = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_HELSEL: Final = (
    "Helsel, D.R., Hirsch, R.M., Ryberg, K.R., Archfield, S.A., Gilroy, E.J. (2020). "
    "Statistical Methods in Water Resources. U.S. Geological Survey Techniques and "
    "Methods 4-A3"
)
_HELSEL_URL: Final = "https://pubs.usgs.gov/tm/04/a03/tm4a3.pdf"
_TREND: Final = (
    "Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point Detection, R "
    "package version 1.1.10, CRAN"
)
_TREND_URL: Final = "https://cran.r-project.org/package=trend"
_EXAMPLES: Final = (
    "examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 "
    "(p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the "
    "Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina "
    "at Rzepin"
)

_GILBERT_MK: Final = Source(
    citation=_GILBERT,
    locator="eqs. 16.1 to 16.4, pp. 209-211: S, Var(S) corrected for ties, Z with a "
    "continuity correction of one; section 16.4.1 and table A18: the exact "
    "probabilities of S below n = 10",
    url=_GILBERT_URL,
)
_HIRSCH: Final = Source(
    citation="Hirsch, R.M., Slack, J.R., Smith, R.A. (1981). Techniques of trend "
    "analysis for monthly water quality data. U.S. Geological Survey Open-File "
    "Report 81-488 (Water Resources Research 18(1), 107-121, 1982)",
    locator="eqs. 1, 2, 3b and 4, PDF pp. 6-7: S, its variance with ties after "
    "Kendall (1975) and Z; 'even for n = 10 the normal approximation is excellent, "
    "provided one uses a continuity correction of one unit'",
    url="https://pubs.usgs.gov/of/1981/0488/report.pdf",
)
_KZGW_MK: Final = Source(
    citation=_KZGW,
    locator="eqs. 1.1 to 1.4, pp. 10-11: S with sgn(0) = 0, its variance without the "
    "correction for ties, u = (S - sgn S) / sigma, the normal approximation 'już dla "
    "N >= 10'",
    url=_KZGW_URL,
)
_TREND_MK: Final = Source(
    citation=_TREND,
    locator="R/mk.test.R: at least 3 values ('x' must have at least 3 elements), S, "
    "varS corrected for ties, z = sgn(S) (|S| - 1) / sigma, the two-sided p "
    "2 min(0.5, P(Z > |z|))",
    url=_TREND_URL,
)
_MANN: Final = Source(
    citation="Mann, H.B. (1945). Nonparametric tests against trend. Econometrica 13, "
    "245-259",
    access="author-provided",
)
_KENDALL: Final = Source(
    citation="Kendall, M.G. (1975). Rank Correlation Methods, 4th ed. Griffin, London",
    locator="p. 55: the normal approximation of S from n = 10 (quoted by Gilbert "
    "1987, p. 211)",
    access="author-provided",
)
_GILBERT_SEN: Final = Source(
    citation=_GILBERT,
    locator="section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / "
    "(i' - i) of the pairs of data i' > i of different times (several values of one "
    "time give no slope among themselves), their median; Example 16.5, p. 219",
    url=_GILBERT_URL,
)
_GILBERT_INTERVAL: Final = Source(
    citation=_GILBERT,
    locator="section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), "
    "M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the "
    "ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, "
    "p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289",
    url=_GILBERT_URL,
)
_HELSEL_LINE: Final = Source(
    citation=_HELSEL,
    locator="section 10.1.1, eqs. 10.1 to 10.3, pp. 266-268: the Theil-Sen slope, the "
    "median of all pairwise slopes, and the intercept b0 = y_med - b1 x_med (Conover "
    "1999)",
    url=_HELSEL_URL,
)
_SEN: Final = Source(
    citation="Sen, P.K. (1968). Estimates of the regression coefficient based on "
    "Kendall's tau. Journal of the American Statistical Association 63, 1379-1389",
    access="author-provided",
)
_CONOVER: Final = Source(
    citation="Conover, W.J. (1980). Practical Nonparametric Statistics, 2nd ed. "
    "Wiley, New York",
    locator="the intercept median(x) - slope median(t)",
    access="author-provided",
)
_SCIPY_THEILSLOPES: Final = (
    "scipy.stats.theilslopes with method='separate': the median of the slopes of the "
    "pairs with x_j > x_i and the intercept median(y) - slope median(x)"
)

_UNIT: Final = "m3/s"
"""The unit of the series in the documents: the test counts signs, so a series in any
unit, a stage in cm, a sum of precipitation or a count of days, gives the same
statistics, and Sen's slope comes in its unit per unit of time."""

_ANY_VALUE: Final = Range(
    test_low=-1.0e6,
    test_high=1.0e6,
    test_reason=(
        "the test counts the signs of differences and Sen's slope scales with the "
        "unit of the series, so any bound tests their arithmetic: a million m3/s "
        "exceeds the discharge of every river, and a stage or a temperature may lie "
        "below 0, so the same bound holds below 0"
    ),
)
"""Any finite value of a series: a discharge, a stage, a sum or a count."""

_MAXIMA: Final = Range(
    low=0.81,
    high=111.0,
    source=Source(
        citation=_KZGW,
        locator=f"{_EXAMPLES}: annual maxima of 0.81 to 111 m3/s",
        url=_KZGW_URL,
    ),
)
"""The annual maxima of the Polish worked examples of the test."""

_BOBR: Final = (
    18.6, 13.2, 22.1, 20.4, 23.0, 10.7, 27.8, 14.7, 8.62, 15.9, 22.1, 16.6, 27.8,
    4.76, 11.3, 32.3, 32.3, 33.8, 21.7, 9.23, 14.3, 8.28, 10.7, 9.16, 10.3, 6.72,
    4.43, 6.72, 3.08, 7.26, 4.70, 6.05, 8.75, 5.24, 6.59, 4.7, 4.16, 4.97, 3.25,
    5.92, 1.9,
)  # fmt: skip
"""The annual maxima of the Bóbr at Bukówka [m3/s], 1965-2005 (KZGW 2017, example
1.1, table 1.1; 1995 printed „4,7,0”, read as 4.70): the typical series of the
generated tests, with six tied pairs."""
_BOBR_YEARS: Final = tuple(float(year) for year in range(1965, 2006))

_MOST_VALUES: Final = 5_000
"""The longest series Sen's slope and its interval take: they hold every slope of the
N' = n (n - 1) / 2 pairs, 12.5 million or 100 MB at 5,000 values (ADR-0063)."""

_EXACT: Final = Tolerance(
    abs=0.0,
    reason="the statistics count signs of differences and groups of equal values, "
    "which doubling, negating or reversing the series keeps or mirrors exactly",
)


def _series(description: str, most: int | None = None) -> Variable:
    return Variable(
        name="values",
        symbol="x_i",
        unit=_UNIT,
        kind="real_array",
        description=description,
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MAXIMA,
        max_length=most,
    )


# --- Mann-Kendall's S, Var(S), Z and p ----------------------------------------------


class MannKendall(NamedTuple):
    """Mann-Kendall's S, its variance, Z and p (spec ``mann_kendall``)."""

    s: int
    var_s: float
    z: float
    p_value: float
    p_value_method: str


def _q_factorial(m: int) -> list[int]:
    """Coefficients of [m]_q! = Π_{j=1}^{m} (1 + q + … + q^(j−1)), lowest first."""
    poly = [1]
    for j in range(2, m + 1):
        product = [0] * (len(poly) + j - 1)
        for power, coefficient in enumerate(poly):
            for shift in range(j):
                product[power + shift] += coefficient
        poly = product
    return poly


def _divided(numerator: list[int], divisor: list[int]) -> list[int]:
    """Exact quotient of two polynomials with integer coefficients, lowest first.

    The divisor has the constant term 1 and divides the numerator exactly.
    """
    quotient = [0] * (len(numerator) - len(divisor) + 1)
    for power in range(len(quotient)):
        quotient[power] = numerator[power] - sum(
            divisor[shift] * quotient[power - shift]
            for shift in range(1, min(power, len(divisor) - 1) + 1)
        )
    return quotient


def _exact_p_value(groups: list[int], s: int) -> float:
    """Two-sided P(|S| ≥ |s|) of Kendall's S under no trend, exactly.

    Every distinct ordering of the values (a multiset with groups of ``groups`` equal
    values) is equally likely; one with k inversions (pairs in descending order) has
    S = N − 2k, N the number of pairs of unequal values. The numbers of orderings by
    k are the coefficients of the q-multinomial [n]_q! / Π [t]_q! (MacMahon, 1916);
    S is symmetric about 0, so P(|S| ≥ |s|) = 2 P(S ≥ |s|) for s ≠ 0.
    """
    if s == 0:
        return 1.0
    counts = _q_factorial(sum(groups))
    for size in groups:
        counts = _divided(counts, _q_factorial(size))
    pairs = len(counts) - 1  # N: the largest number of inversions
    tail = sum(counts[: (pairs - abs(s)) // 2 + 1])
    return 2 * tail / sum(counts)


def _mann_kendall(data: NDArray[np.float64], exact_below: int) -> MannKendall:
    """Return S, Var(S), Z and p of a series of at least three finite values.

    S counts the signs row by row in integers; Var(S) is the integer
    n(n − 1)(2n + 5) − Σ t(t − 1)(2t + 5) over 18, divided once and correctly rounded.
    """
    n = data.size
    s = 0
    for i in range(n - 1):
        s += int(np.sum(np.sign(data[i + 1 :] - data[i])))
    _, counts = np.unique(data, return_counts=True)
    groups = [int(t) for t in counts]
    ties = sum(t * (t - 1) * (2 * t + 5) for t in groups if t > 1)
    var_s = (n * (n - 1) * (2 * n + 5) - ties) / 18
    if s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0
    if n < exact_below:
        return MannKendall(s, var_s, z, _exact_p_value(groups, s), "exact")
    return MannKendall(s, var_s, z, float(2.0 * norm.sf(abs(z))), "normal")


def _enough(least: int, source: Source) -> Constraint:
    """Return the precondition of at least ``least`` values."""
    return Constraint(
        name="enough_values",
        cls="precondition",
        check=lambda x: x.array("values").size >= least,
        text=f"n >= {least}",
        source=source,
        satisfied={"values": [1.0, 2.0, 4.0, 8.0, 16.0][: least + 1]},
        violated={"values": [1.0, 2.0, 4.0, 8.0][: least - 1]},
        boundary={"values": [1.0, 2.0, 4.0, 8.0][:least]},
    )


def _negated(x: Values) -> dict[str, object]:
    return {**x, "values": -x.array("values")}


def _reversed(x: Values) -> dict[str, object]:
    return {**x, "values": x.array("values")[::-1].copy()}


def _mirrored_test(out: Values) -> dict[str, object]:
    return {
        "s": -out.integer("s"),
        "var_s": out.real("var_s"),
        "z": -out.real("z"),
        "p_value": out.real("p_value"),
    }


def _monotone_series(run: Callable[..., Values]) -> None:
    """Check a strictly increasing series below ten values: p = 2 / n! exactly."""
    for n in range(3, 10):
        out = run(values=[float(value) for value in range(n)])
        assert_within(
            out.real("p_value"),
            2 / math.factorial(n),
            rel=4.5e-16,
            reason="one ordering of the n! has the largest S and one the smallest, "
            "so the exact two-sided p is 2/n!, a quotient of integers rounded once",
        )


def _normal_tail(run: Callable[..., Values]) -> None:
    """From ten values p = erfc(|z| / sqrt(2)), another algorithm of the normal tail."""
    for n in (10, 30, 50, 200):
        out = run(values=[float(value) for value in range(n)])
        z = out.real("z")
        assert_within(
            out.real("p_value"),
            math.erfc(abs(z) / math.sqrt(2.0)),
            rel=1e-13,
            reason="2 P(Z > |z|) by scipy's norm.sf against the C library's erfc, two "
            "implementations of the normal upper tail, each within a few ulp; at n = "
            "200 the tail is about 1e-163, far from 0",
        )


MANN_KENDALL: Final = FormulaSpec(
    name="mann_kendall",
    title="Mann-Kendall test of a monotonic trend: S, Var(S) with ties, Z and the "
    "two-sided p",
    function="hydrolog.statistics.stationarity.mann_kendall",
    family="statistic",
    equation=(
        "S = sum_{i<j} sgn(x_j - x_i); Var(S) = [n (n - 1) (2n + 5) - sum_p t_p (t_p "
        "- 1) (2 t_p + 5)] / 18 over the groups of t_p equal values; Z = (S - 1) / "
        "sqrt(Var(S)) for S > 0, 0 for S = 0, (S + 1) / sqrt(Var(S)) for S < 0; p = "
        "P(|S'| >= |S|) of the exact distribution of S below n0 values, else "
        "2 P(Z' > |Z|) of the standard normal"
    ),
    latex=(
        r"S = \sum_{i<j} \operatorname{sgn}(x_j - x_i),\quad \operatorname{Var}(S) = "
        r"\frac{n(n-1)(2n+5) - \sum_p t_p(t_p-1)(2t_p+5)}{18},\quad Z = "
        r"\frac{S - \operatorname{sgn} S}{\sqrt{\operatorname{Var}(S)}},\quad p = "
        r"\begin{cases} P(|S'| \ge |S|) & n < n_0 \\ 2\,P(Z' > |Z|) & n \ge n_0 "
        r"\end{cases}"
    ),
    variables=(
        _series(
            "The series in time order, one value per time step: annual maxima, means "
            "or minima, sums or counts, in any unit."
        ),
    ),
    outputs=(
        Output(
            name="s",
            unit="-",
            kind="integer",
            symbol="S",
            description="Kendall's score: the pairs in ascending order less the pairs "
            "in descending order.",
            physical=Range(),
        ),
        Output(
            name="var_s",
            unit="-",
            symbol=r"\operatorname{Var}(S)",
            description="The variance of S under no trend, corrected for the groups "
            "of equal values; 0 for a series of equal values.",
            physical=Range(low=0.0),
        ),
        Output(
            name="z",
            unit="-",
            symbol="Z",
            description="The standardised score with a continuity correction of one.",
            physical=Range(),
        ),
        Output(
            name="p_value",
            unit="-",
            symbol="p",
            description="Two-sided p-value of no trend; one below the smallest "
            "positive float is set to it.",
            physical=Range(low=0.0, low_inclusive=False, high=1.0),
        ),
        Output(
            name="p_value_method",
            unit="-",
            kind="choice",
            description="exact below n0 values, normal from n0.",
            choices=("exact", "normal"),
        ),
    ),
    sources=(_GILBERT_MK, _HIRSCH, _KZGW_MK, _TREND_MK, _MANN, _KENDALL),
    constraints=(_enough(3, _TREND_MK),),
    constants=(
        Constant(
            name="exact_below",
            value=Fraction(10),
            unit="values",
            symbol="n_0",
            source=Source(
                citation=_GILBERT,
                locator="section 16.4.2, p. 211: the normal approximation from n = 10 "
                "after Kendall (1975, p. 55), as KZGW (2017, p. 11) and Hirsch et al. "
                "(1981, PDF p. 7) state it; section 16.4.1 and table A18: the exact "
                "probabilities below",
                url=_GILBERT_URL,
            ),
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_series",
                inputs={"values": 1.0},
                outputs={},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="negated_series",
                text="the negated series has the negated S and Z, the same Var(S) and "
                "p",
                inputs=_negated,
                outputs=_mirrored_test,
                tolerance=_EXACT,
            ),
            Symmetry(
                name="reversed_series",
                text="the series in reverse order has the negated S and Z, the same "
                "Var(S) and p",
                inputs=_reversed,
                outputs=_mirrored_test,
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="equal_values",
                text="a series of equal values: S = 0, Var(S) = 0, Z = 0 (Gilbert's "
                "eq. 16.4 for S = 0) and p = 1, every ordering being the same",
                inputs={"values": [5.0] * 12},
                expected={"s": 0, "var_s": 0.0, "z": 0.0, "p_value": 1.0},
                tolerance=Tolerance(abs=0.0, reason="exact integers and their cases"),
                source=_GILBERT_MK,
            ),
            Limit(
                name="monotone_series_exact",
                text="a strictly monotone series below n0 values has the exact p 2/n!",
                check=_monotone_series,
            ),
            Limit(
                name="normal_tail",
                text="from n0 values p equals erfc(|Z| / sqrt(2)), the normal tail of "
                "another algorithm",
                check=_normal_tail,
            ),
        ),
    ),
    validation=(
        "none: a test of the hypothesis of no trend; its sources compare it with no "
        "observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "values tie when exactly equal (round a series computed in floating point to "
        "its precision first); sgn(0) = 0, as KZGW (2017) eq. 1.2 defines it, though "
        "its worked examples count a tied pair as -1",
        "Var(S) corrected for the groups of ties (Gilbert eq. 16.3, Hirsch et al. eq. "
        "3b, R's trend); KZGW (2017, p. 11) leaves the correction out",
        "Z with a continuity correction of one toward 0 and Z = 0 for S = 0 (Gilbert "
        "eq. 16.4, KZGW eq. 1.4)",
        "the p-value is two-sided: below n0 values the exact P(|S'| >= |S|) over every "
        "distinct ordering of the values, equally likely under no trend, ties "
        "respected (the q-multinomial coefficients, MacMahon 1916); from n0 values "
        "2 P(Z' > |Z|) from the upper tail of the normal distribution (scipy's "
        "norm.sf, as R's trend), which keeps its digits for a strong trend",
        "a p-value below the smallest positive float (|Z| above about 38.5) is set to "
        "it, the end of the physical range (0, 1]",
        "the series in any unit: the statistics have none",
    ),
    assumptions=(
        "the values are independent and identically distributed under no trend "
        "(Gilbert 1987, p. 213; KZGW 2017, p. 10): serial correlation, as of daily or "
        "monthly flows, makes the test reject too often",
        "the values are in time order, one per time step; gaps of the record do not "
        "enter the test",
    ),
    traps={
        "singular_at_bound": "sqrt(Var(S)) at Var(S) = 0, a series of equal values: "
        "Z = 0 by S = 0, limit equal_values",
        "exp_overflow": "the normal tail exp(-z^2/2) of a strong trend: 50 increasing "
        "values keep p = 1.3e-24 and 10,000 give the smallest positive float, not 0 "
        "(test_a_strong_trend_keeps_a_p_value_above_zero)",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "many_small_terms": "S sums n(n - 1)/2 signs in integers and Var(S) is one "
        "division of integers (test_s_of_a_long_series_is_exact)",
    },
    reference_cases=("tests/fixtures/formulas/trend-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the null distribution of S by every ordering of the series "
            "(the permutation test's definition), with Fraction probabilities: p and "
            "the variance of the distribution, which is Var(S) with ties",
            test="tests/unit/test_formulas_trend.py "
            "(test_the_exact_p_and_var_s_are_those_of_every_ordering)",
        ),
        Oracle(
            kind="exact",
            description="the Mahonian numbers of the inversions of the permutations "
            "of n by the recurrence M(n, k) = M(n, k - 1) + M(n - 1, k) - M(n - 1, k "
            "- n), not the product of the q-factorial",
            test="tests/unit/test_formulas_trend.py "
            "(test_the_exact_p_without_ties_is_that_of_the_mahonian_numbers)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.kendalltau of the series against its times "
            "(SciPy 1.18.1): S from tau-b and, without ties below n0 values, the exact "
            "p",
            test="tests/unit/test_formulas_trend.py "
            "(test_s_and_the_exact_p_are_scipys_kendalltau)",
            conventions=(
                "kendalltau(method='exact') is the two-sided p of the permutation "
                "distribution of the inversions without ties, the p of the spec below "
                "n0 values",
                "tau-b times sqrt(n0 (n0 - n1)), n0 = n (n - 1)/2 and n1 the tied "
                "pairs of the values, is S",
            ),
        ),
        Oracle(
            kind="frozen",
            description="R 4.4.3 trend 1.1.10 mk.test, modifiedmk 1.6 mkttest and "
            "Kendall 2.2.2 MannKendall on 13 series",
            test="tests/oracles/trend_regime/r_oracle_outputs_headed.csv "
            "(tests/unit/test_formulas_trend.py, test_mann_kendall_is_rs)",
            conventions=(
                "trend::mk.test: S, varS corrected for ties, z with the continuity "
                "correction, p = 2 min(0.5, P(Z > |z|)) for every n; Hydrolog's p "
                "below n0 values is exact, so only S, Var(S) and Z are compared there",
                "Kendall::MannKendall copies the data to single precision; the "
                "series of the oracle tie in both precisions",
            ),
        ),
    ),
    base={"values": list(_BOBR)},
)

_EXACT_BELOW: Final = int(MANN_KENDALL.constant("exact_below"))


def mann_kendall(values: NDArray[np.float64] | Sequence[float]) -> MannKendall:
    """Test a series for a monotonic trend, spec mann_kendall.

    Parameters
    ----------
    values : array_like of float
        The series in time order.

    Returns
    -------
    MannKendall
        Kendall's score, its variance under no trend, the standardised score and the
        two-sided p-value with the way it was found.

    Raises
    ------
    InvalidParameterError
        If the series is refused by the spec: too short or not finite.
    """
    x = checked_inputs(MANN_KENDALL, values=values)
    found = _mann_kendall(x.array("values"), _EXACT_BELOW)
    out = checked_outputs(MANN_KENDALL, found._asdict())
    return MannKendall(
        out.integer("s"),
        out.real("var_s"),
        out.real("z"),
        out.real("p_value"),
        out.choice("p_value_method"),
    )


# --- Sen's slope with Conover's intercept --------------------------------------------


class SenLine(NamedTuple):
    """Sen's slope with Conover's intercept (spec ``sen_slope``)."""

    slope: float
    intercept: float
    n_slopes: int


class SenInterval(NamedTuple):
    """Gilbert's confidence interval of Sen's slope (spec ``sen_interval``)."""

    lower: float
    upper: float


def _later(times: NDArray[np.float64]) -> NDArray[np.intp]:
    """Return, per value, the index of the first value of a later time."""
    return np.searchsorted(times, times, side="right")


def _pair_count(times: NDArray[np.float64]) -> int:
    """Return N', the pairs of values of different times, of times in order."""
    return int(np.sum(times.size - _later(times)))


def _pair_slopes(
    values: NDArray[np.float64], times: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return the N' slopes (x_j − x_i) / (t_j − t_i) of the pairs with t_i < t_j.

    The times are in order, so the later values of value i are those from the first
    of a later time on; the slopes are written row by row into one array, eight bytes
    a pair (ADR-0063), in no particular order.
    """
    later = _later(times)
    slopes = np.empty(int(np.sum(times.size - later)), dtype=np.float64)
    at = 0
    for i, start in enumerate(later.tolist()):
        stop = at + times.size - start
        slopes[at:stop] = (values[start:] - values[i]) / (times[start:] - times[i])
        at = stop
    return slopes


def _order_statistics(slopes: NDArray[np.float64], ranks: list[int]) -> list[float]:
    """Return the slopes of the given 1-based ranks; the array is partitioned."""
    slopes.partition([rank - 1 for rank in ranks])
    return [float(slopes[rank - 1]) for rank in ranks]


def _median(slopes: NDArray[np.float64]) -> float:
    """Return the median as numpy.median takes it: the mean of the middle two."""
    middle = slopes.size // 2
    if slopes.size % 2:
        return _order_statistics(slopes, [middle + 1])[0]
    low, high = _order_statistics(slopes, [middle, middle + 1])
    return float((np.float64(low) + np.float64(high)) / 2.0)


def _sen_line(values: NDArray[np.float64], times: NDArray[np.float64]) -> SenLine:
    slopes = _pair_slopes(values, times)
    slope = _median(slopes)
    intercept = float(np.median(values) - slope * np.median(times))
    return SenLine(slope, intercept, int(slopes.size))


def _steepest(x: Values) -> float:
    """Return the largest |slope| a pair can have, by its range over the least step."""
    values, times = x.array("values"), x.array("times")
    steps = np.diff(times)
    steps = steps[steps > 0.0]
    if steps.size == 0 or values.size == 0:
        return 0.0
    with np.errstate(over="ignore", invalid="ignore"):
        return float((np.max(values) - np.min(values)) / np.min(steps))


def _representable(x: Values) -> bool:
    """Whether every slope, their differences and the line are finite in float64."""
    values, times = x.array("values"), x.array("times")
    if values.size == 0 or times.size == 0:
        return True
    steepest = _steepest(x)
    with np.errstate(over="ignore", invalid="ignore"):
        line = steepest * float(np.max(np.abs(times))) + float(np.max(np.abs(values)))
    return math.isfinite(2.0 * steepest) and math.isfinite(line)


def _times_variable() -> Variable:
    return Variable(
        name="times",
        symbol="t_i",
        unit="a",
        kind="real_array",
        description="The time of each value in order: its year, or its step 0, 1, 2 "
        "… of the series; several values may share a time. The slope is per unit of "
        "these times.",
        physical=Range(
            test_low=-1.0e6,
            test_high=1.0e6,
            test_reason="years of the Common Era or steps of a series of at most "
            "5,000 values: a million exceeds both",
        ),
        applicability="unstated",
        typical=Range(
            low=1965.0,
            high=2005.0,
            source=Source(
                citation=_KZGW,
                locator=f"{_EXAMPLES}: the years 1965 to 2005",
                url=_KZGW_URL,
            ),
        ),
        max_length=_MOST_VALUES,
    )


def _pair_constraints(source: Source) -> tuple[Constraint, ...]:
    """Return the constraints of a series and its times that Sen's slopes share."""
    return (
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: x.array("values").shape == x.array("times").shape,
            text="one time per value",
            source=source,
            satisfied={"values": [1.0, 3.0, 2.0], "times": [1.0, 2.0, 3.0]},
            violated={"values": [1.0, 3.0, 2.0], "times": [1.0, 2.0]},
        ),
        Constraint(
            name="times_in_order",
            cls="physical",
            check=lambda x: bool(np.all(np.diff(x.array("times")) >= 0.0)),
            text="t[i+1] >= t[i]: the values in time order, several of one time "
            "allowed",
            source=source,
            satisfied={"values": [1.0, 3.0, 2.0], "times": [1.0, 2.0, 3.0]},
            boundary={"values": [1.0, 3.0, 2.0], "times": [1.0, 2.0, 2.0]},
            violated={"values": [1.0, 3.0, 2.0], "times": [1.0, 3.0, 2.0]},
        ),
        Constraint(
            name="two_times",
            cls="precondition",
            check=lambda x: x.array("times")[-1] > x.array("times")[0],
            text="t[-1] > t[0]: two values of different times make a slope",
            source=source,
            satisfied={"values": [1.0, 3.0], "times": [1.0, 2.0]},
            violated={"values": [1.0, 3.0], "times": [2.0, 2.0]},
        ),
        Constraint(
            name="slopes_in_float64",
            cls="precondition",
            check=_representable,
            text="2 (max x - min x) / (least step of t) and the line (max x - min x) / "
            "(least step of t) max|t| + max|x| are finite in float64: every slope, the "
            "difference of two slopes and the intercept are",
            source=source,
            satisfied={"values": [0.0, 1.0e6], "times": [0.0, 1.0e-6]},
            violated={"values": [0.0, 1.0e6], "times": [0.0, 1.0e-303]},
        ),
    )


def _negated_line(out: Values) -> dict[str, object]:
    return {
        "slope": -out.real("slope"),
        "intercept": -out.real("intercept"),
        "n_slopes": out.integer("n_slopes"),
    }


def _straight_line(run: Callable[..., Values]) -> None:
    for slope, intercept in ((0.5, 3.0), (-2.25, 410.0), (0.0, 7.5)):
        times = [float(t) for t in range(1971, 2001)]
        out = run(
            values=[intercept + slope * t for t in times],
            times=times,
        )
        assert_within(
            out.real("slope"),
            slope,
            abs=0.0,
            reason="slopes of 0.5, -2.25 and 0 over whole years: every value a + b t, "
            "difference and quotient is a binary fraction, exact",
        )


def _exact_median(run: Callable[..., Values]) -> None:
    """Check the slope against the median of the exact rational slopes."""
    rng = np.random.default_rng(20261119)
    for n in (5, 12, 31):
        times = np.sort(rng.integers(1951, 2025, size=n)).astype(float)
        values = np.round(rng.gamma(2.0, 20.0, size=n), 2)
        out = run(values=values.tolist(), times=times.tolist())
        exact = sorted(
            (Fraction(values[j]) - Fraction(values[i]))
            / (Fraction(times[j]) - Fraction(times[i]))
            for i in range(n)
            for j in range(i + 1, n)
            if times[j] > times[i]
        )
        middle = len(exact) // 2
        median = (
            exact[middle] if len(exact) % 2 else (exact[middle - 1] + exact[middle]) / 2
        )
        assert_within(
            out.integer("n_slopes"), len(exact), abs=0.0, reason="a count of pairs"
        )
        scale = max(abs(exact[middle - 1]), abs(exact[middle]))
        assert_within(
            out.real("slope"),
            float(median),
            abs=4.5e-16 * float(scale) + 1e-300,
            reason="each slope rounds its difference of values and its quotient, two "
            "ulp of the slope, and the mean of the middle two rounds once more, so "
            "within two ulp of the larger middle slope however the two cancel",
        )


SEN_SLOPE: Final = FormulaSpec(
    name="sen_slope",
    title="Sen's slope of a series with Conover's intercept",
    function="hydrolog.statistics.stationarity.sen_line",
    family="statistic",
    equation=(
        "b = median of the N' slopes (x_j - x_i) / (t_j - t_i) over the pairs with "
        "t_i < t_j; a = median(x) - b median(t)"
    ),
    latex=(
        r"b = \operatorname*{median}_{t_i < t_j} \frac{x_j - x_i}{t_j - t_i},\quad "
        r"a = \operatorname{median}(x) - b \operatorname{median}(t)"
    ),
    variables=(
        _series(
            "The series, one value per time of times, in any unit; the slope comes in "
            "its unit per unit of time.",
            _MOST_VALUES,
        ),
        _times_variable(),
    ),
    outputs=(
        Output(
            name="slope",
            unit="m3/s/a",
            symbol="b",
            description="Sen's slope: the median of the slopes of the pairs of "
            "different times, in the unit of the values per unit of time.",
            physical=Range(),
        ),
        Output(
            name="intercept",
            unit=_UNIT,
            symbol="a",
            description="Conover's intercept: the value of the line at time 0 (year "
            "0 with years).",
            physical=Range(),
        ),
        Output(
            name="n_slopes",
            unit="-",
            kind="integer",
            symbol="N'",
            description="The number of pairs of different times.",
            physical=Range(low=1.0),
        ),
    ),
    sources=(_GILBERT_SEN, _HELSEL_LINE, _SEN, _CONOVER),
    constraints=_pair_constraints(_GILBERT_SEN),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_values",
                inputs={"values": 1.0},
                outputs={"slope": 1.0, "intercept": 1.0},
                tolerance=Tolerance(
                    abs=2.2250738585072014e-308,
                    reason="doubling the values doubles every difference, slope and "
                    "product exactly, but for results below the smallest normal float",
                ),
            ),
            Scaling(
                name="unit_of_the_times",
                inputs={"times": 1.0},
                outputs={"slope": -1.0},
                tolerance=Tolerance(
                    abs=2.2250738585072014e-308,
                    reason="doubling the times halves every slope exactly and leaves "
                    "the product slope median(t), so the intercept, as it was",
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="negated_values",
                text="the negated values have the negated slope and intercept",
                inputs=_negated,
                outputs=_negated_line,
                tolerance=Tolerance(
                    abs=0.0, reason="negation is exact in every operation"
                ),
            ),
        ),
        limits=(
            Limit(
                name="straight_line",
                text="the values of a straight line give its slope",
                check=_straight_line,
            ),
            Limit(
                name="exact_median",
                text="the slope is the median of the slopes in exact rational "
                "arithmetic, rounded once",
                check=_exact_median,
            ),
        ),
    ),
    validation=(
        "none: an estimator of the slope of a monotonic trend; its sources compare it "
        "with no observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "the slopes of the pairs of different times only: several values of one time "
        "(Gilbert's eq. 16.5 case) give no slope among themselves",
        "per unit of the times given: per year with years, per step with the steps "
        "0, 1, 2 … of the series; R's trend and modifiedmk take the slopes per step "
        "of the index, the same where the years follow each other",
        "the median of an even number of slopes is the mean of the middle two",
        "Conover's intercept median(x) - b median(t) (Helsel et al. 2020, eq. 10.3), "
        "the line at t = 0; the trend vignette's alternative is the median of the "
        "residuals",
        "at most 5,000 values: every slope is held in memory, eight bytes each, 100 MB "
        "at 5,000 values; the estimator is meant for independent values, annual or "
        "monthly, whose longest records have a few hundred years",
    ),
    assumptions=(
        "a linear trend of the values in time; the estimator is robust to outliers, "
        "not to serial correlation of the values (as the Mann-Kendall test)",
    ),
    traps={
        "singular_at_bound": "1 / (t_j - t_i): pairs of one time give no slope and "
        "series of one time are refused by the precondition two_times; slopes beyond "
        "float64 by slopes_in_float64 "
        "(test_a_series_of_one_time_and_slopes_beyond_float64_are_refused)",
        "gap_propagation": "type cases values-nan_element and times-nan_element: a gap "
        "is refused",
    },
    reference_cases=("tests/fixtures/formulas/trend-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the median of the slopes in exact rational arithmetic "
            "(fractions)",
            test="tests/unit/test_formulas_trend.py (limit exact_median)",
        ),
        Oracle(
            kind="established",
            description=f"{_SCIPY_THEILSLOPES} (SciPy 1.18.1)",
            test="tests/unit/test_formulas_trend.py "
            "(test_the_line_is_scipys_theilslopes)",
            conventions=(
                "theilslopes takes the pairs with x_j > x_i, the pairs of different "
                "times of the spec",
                "method='separate' is Conover's intercept, the spec's",
            ),
        ),
        Oracle(
            kind="frozen",
            description="R 4.4.3 trend 1.1.10 sens.slope and modifiedmk 1.6 "
            "mkttest on 13 series",
            test="tests/oracles/trend_regime/r_oracle_outputs_headed.csv "
            "(tests/unit/test_formulas_trend.py, test_sens_slope_is_rs)",
            conventions=(
                "R's slopes are per step of the index, the spec's per unit of the "
                "times: equal for consecutive years, the only series compared",
            ),
        ),
    ),
    base={"values": list(_BOBR), "times": list(_BOBR_YEARS)},
)


def sen_line(
    values: NDArray[np.float64] | Sequence[float],
    times: NDArray[np.float64] | Sequence[float],
) -> SenLine:
    """Estimate Sen's slope and Conover's intercept, spec sen_slope.

    Parameters
    ----------
    values : array_like of float
        The values.
    times : array_like of float
        Their times in order (years, or the steps of the series).

    Returns
    -------
    SenLine
        The slope per unit of time, the intercept at time zero and the number of
        pairs of different times.

    Raises
    ------
    InvalidParameterError
        If the series is refused by the spec: arrays of different lengths, a value
        that is not finite, times out of order or of one time.
    """
    x = checked_inputs(SEN_SLOPE, values=values, times=times)
    found = _sen_line(x.array("values"), x.array("times"))
    out = checked_outputs(SEN_SLOPE, found._asdict())
    return SenLine(out.real("slope"), out.real("intercept"), out.integer("n_slopes"))


# --- Gilbert's interval of Sen's slope -----------------------------------------------


def _reach(var_s: float, alpha: float) -> float:
    """Return C = z(1 − alpha/2) √Var(S), the half-width of the ranks' interval."""
    return float(norm.ppf(1.0 - alpha / 2.0)) * math.sqrt(var_s)


def _ranks(count: int, var_s: float, alpha: float) -> tuple[float, float]:
    """Return the ranks M1 and M2 + 1 of the limits among the ordered slopes."""
    reach = _reach(var_s, alpha)
    return (count - reach) / 2.0, (count + reach) / 2.0 + 1.0


def _ranks_inside(x: Values) -> bool:
    """Whether both ranks lie within 1 … N' (Gilbert, section 16.5)."""
    times = x.array("times")
    if times.size == 0 or x.array("values").shape != times.shape:
        return True
    count = _pair_count(times)
    lower, upper = _ranks(count, x.real("var_s"), x.real("alpha"))
    return 1.0 <= lower <= count and 1.0 <= upper <= count


def _at_rank(slopes: NDArray[np.float64], rank: float) -> float:
    """Return the slope of a rank in 1 … N', interpolated linearly between ranks.

    numpy.interp on the two neighbouring ranks, whose arithmetic is that of the
    whole ladder of ranks.
    """
    below = int(math.floor(rank))
    if below >= slopes.size:
        return _order_statistics(slopes, [slopes.size])[0]
    pair = _order_statistics(slopes, [below, below + 1])
    return float(np.interp(rank, [float(below), float(below + 1)], pair))


def _sen_interval(
    values: NDArray[np.float64],
    times: NDArray[np.float64],
    var_s: float,
    alpha: float,
) -> SenInterval:
    slopes = _pair_slopes(values, times)
    lower, upper = _ranks(slopes.size, var_s, alpha)
    return SenInterval(_at_rank(slopes, lower), _at_rank(slopes, upper))


def _holds_the_slope(run: Callable[..., Values]) -> None:
    """Check that the interval holds Sen's slope, and the middle slopes at C = 0."""
    rng = np.random.default_rng(20261119)
    for n in (10, 25, 60):
        times = np.arange(1961.0, 1961.0 + n)
        values = np.round(50.0 + 0.3 * times + rng.normal(0.0, 8.0, size=n), 1)
        slope = sen_line(values, times).slope
        for var_s in (mann_kendall(values).var_s, 0.0):
            out = run(values=values, times=times, var_s=var_s, alpha=0.05)
            outside = max(out.real("lower") - slope, slope - out.real("upper"), 0.0)
            assert_within(
                outside,
                0.0,
                abs=0.0,
                reason="the ranks M1 and M2 + 1 lie on either side of the median's",
            )
        if n == 25:  # N' = 300: at C = 0 the ranks are 150 and 151, whole ranks
            slopes = np.sort(_pair_slopes(values, times))
            assert_within(
                [out.real("lower"), out.real("upper")],
                [slopes[149], slopes[150]],
                abs=0.0,
                reason="C = 0 puts the ranks at N'/2 and N'/2 + 1, the two middle "
                "slopes themselves for an even N'",
            )


SEN_INTERVAL: Final = FormulaSpec(
    name="sen_interval",
    title="Gilbert's confidence interval of Sen's slope",
    function="hydrolog.statistics.stationarity.sen_interval",
    family="statistic",
    equation=(
        "C = z(1 - alpha/2) sqrt(Var(S)); M1 = (N' - C) / 2, M2 = (N' + C) / 2; lower "
        "= the M1-th and upper = the (M2 + 1)-th of the N' ordered slopes, "
        "interpolated linearly between ranks"
    ),
    latex=(
        r"C = z_{1-\alpha/2}\sqrt{\operatorname{Var}(S)},\quad M_1 = \frac{N' - C}{2},"
        r"\quad M_2 = \frac{N' + C}{2},\quad b_L = Q_{(M_1)},\quad b_U = Q_{(M_2+1)}"
    ),
    variables=(
        _series(
            "The series, one value per time of times, in any unit.",
            _MOST_VALUES,
        ),
        _times_variable(),
        Variable(
            name="var_s",
            symbol=r"\operatorname{Var}(S)",
            unit="-",
            description="The variance of Kendall's S the interval is built on: that of "
            "the Mann-Kendall test of the values, corrected for ties (Gilbert's eq. "
            "16.3, or eq. 16.5 with several values of one time).",
            physical=Range(
                low=0.0,
                test_high=1.4e10,
                test_reason="Var(S) of 5,000 values without ties, the most the spec "
                "takes, is 1.389e10",
            ),
            applicability="unstated",
            typical=Range(
                low=3139.0,
                high=7921.0,
                source=Source(
                    citation=_KZGW,
                    locator=f"{_EXAMPLES}: n = 30 to 41 with ties, Var(S) 3,139.7 to "
                    "7,920.7",
                    url=_KZGW_URL,
                ),
            ),
        ),
        Variable(
            name="alpha",
            symbol=r"\alpha",
            unit="-",
            description="The interval covers 1 - alpha.",
            physical=Range(
                low=0.0, high=1.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(
                low=0.05,
                high=0.05,
                source=Source(
                    citation="Obserwator 3.1.0.dev0, analysis registry "
                    "(src/obserwator/store/analysis_registry.py), the stored "
                    "analyses mann_kendall.* of stats mann-kendall; KZGW (2017), p. 11",
                    locator="options alpha = 0.05; the significance level 0.05 of "
                    "KZGW's test",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="lower",
            unit="m3/s/a",
            symbol="b_L",
            description="The lower limit of the slope's interval.",
            physical=Range(),
        ),
        Output(
            name="upper",
            unit="m3/s/a",
            symbol="b_U",
            description="The upper limit of the slope's interval.",
            physical=Range(),
        ),
    ),
    sources=(_GILBERT_INTERVAL, _HELSEL_LINE, _SEN),
    constraints=(
        *_pair_constraints(_GILBERT_INTERVAL),
        Constraint(
            name="ranks_within_slopes",
            cls="precondition",
            check=_ranks_inside,
            text="1 <= M1 and M2 + 1 <= N': both ranks lie among the N' ordered "
            "slopes (C <= N' - 2)",
            source=_GILBERT_INTERVAL,
            satisfied={"var_s": 3139.0},
            violated={"var_s": 1.0e6},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"var_s": -1, "alpha": 1},
        scalings=(
            Scaling(
                name="unit_of_the_values",
                inputs={"values": 1.0},
                outputs={"lower": 1.0, "upper": 1.0},
                tolerance=Tolerance(
                    abs=2.2250738585072014e-308,
                    reason="doubling the values doubles every slope and the "
                    "interpolation between two of them exactly, but below the "
                    "smallest normal float",
                ),
            ),
            Scaling(
                name="unit_of_the_times",
                inputs={"times": 1.0},
                outputs={"lower": -1.0, "upper": -1.0},
                tolerance=Tolerance(
                    abs=2.2250738585072014e-308,
                    reason="doubling the times halves every slope and the "
                    "interpolation exactly, but below the smallest normal float",
                ),
            ),
        ),
        limits=(
            Limit(
                name="holds_the_slope",
                text="the interval holds Sen's slope, and at Var(S) = 0 it is the "
                "middle slopes",
                check=_holds_the_slope,
            ),
        ),
    ),
    validation=(
        "none: a non-parametric confidence interval of the slope (Gilbert 1987, "
        "section 16.5); its sources compare it with no observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "Gilbert's linear interpolation between ranks (his Example 16.5 and "
        "subroutine CONINT, appendix B); R's trend rounds the ranks (round(), half to "
        "even) and Helsel et al. (2020, eqs. 10.6-10.7) take whole ranks, which move "
        "the limits by up to 5 % of a limit at n <= 34 (frozen oracle, ADR-0063)",
        "the Var(S) of the test of the same values, given by the caller; Gilbert's "
        "Exercise 16.3 builds it without the correction for ties on purpose",
        "z(1 - alpha/2) of the standard normal distribution (scipy's norm.ppf); an "
        "alpha whose 1 - alpha/2 rounds to 1 has no interval",
        "stats mann-kendall gives the interval from ten values (Gilbert 1987, p. 218: "
        "the normal approximation of S it rests on), null below",
        "at most 5,000 values, as Sen's slope",
    ),
    assumptions=(
        "S approximately normal under no trend, from about ten values unless there "
        "are many ties (Gilbert 1987, p. 218)",
    ),
    traps={
        "singular_at_bound": "sqrt(Var(S)) at Var(S) = 0: the middle slopes, limit "
        "holds_the_slope; ranks outside the slopes are refused by the precondition "
        "ranks_within_slopes",
        "gap_propagation": "type cases values-nan_element and times-nan_element: a gap "
        "is refused",
    },
    reference_cases=("tests/fixtures/formulas/trend-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the ordered slopes sorted in full (numpy.sort) and the ranks "
            "interpolated on the whole ladder of ranks (numpy.interp), as Hydrolog "
            "0.9.0.dev2 computed them",
            test="tests/unit/test_formulas_trend.py "
            "(test_the_interval_is_the_interpolation_of_the_sorted_slopes)",
        ),
        Oracle(
            kind="frozen",
            description="R 4.4.3 trend 1.1.10 sens.slope at 90 and 95 % on 13 series",
            test="tests/oracles/trend_regime/r_oracle_outputs_headed.csv "
            "(tests/unit/test_formulas_trend.py, test_sens_interval_rounds_as_rs)",
            conventions=(
                "R takes the slope of the rounded rank, the spec interpolates between "
                "the slopes of the ranks around it: R's limit is one of those two",
            ),
        ),
    ),
    base={
        "values": list(_BOBR),
        "times": list(_BOBR_YEARS),
        "var_s": 7920.666666666667,
        "alpha": 0.05,
    },
)


def sen_interval(
    values: NDArray[np.float64] | Sequence[float],
    times: NDArray[np.float64] | Sequence[float],
    var_s: float,
    alpha: float,
) -> SenInterval:
    """Bound Sen's slope by Gilbert's confidence interval, spec sen_interval.

    Parameters
    ----------
    values : array_like of float
        The values.
    times : array_like of float
        Their times in order (years, or the steps of the series).
    var_s : float
        The variance of Kendall's S that the interval is built on.
    alpha : float
        The interval covers one less alpha.

    Returns
    -------
    SenInterval
        The lower and the upper limit of the slope.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec, also when a limit's rank falls
        outside the ordered slopes (``details.constraint`` ``ranks_within_slopes``).
    """
    x = checked_inputs(
        SEN_INTERVAL, values=values, times=times, var_s=var_s, alpha=alpha
    )
    found = _sen_interval(
        x.array("values"), x.array("times"), x.real("var_s"), x.real("alpha")
    )
    out = checked_outputs(SEN_INTERVAL, found._asdict())
    return SenInterval(out.real("lower"), out.real("upper"))


SPECS: Final[tuple[FormulaSpec, ...]] = (MANN_KENDALL, SEN_SLOPE, SEN_INTERVAL)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="trend_decision",
        function="hydrolog.statistics.stationarity.mann_kendall_test",
        definition="trend_detected is p < alpha; trend_direction is increasing for "
        "S > 0 and decreasing for S < 0 when a trend is detected, else none; Sen's "
        "interval is given from ten values and is null below them or when a rank "
        "falls outside the slopes",
        convention="a two-sided test at the caller's alpha, the interval at 1 - alpha; "
        "the times must increase strictly (one value a time step)",
        source=_GILBERT_MK,
    ),
    TierBSpec(
        name="trend_times",
        function="hydrolog.operations.stats_mann_kendall",
        definition="the times of the values: their years (years, year_column) or, "
        "without them, the steps 0, 1, 2 … of the series; a missing value is left "
        "out and keeps its step",
        convention="Sen's slope per year with years, per step without them",
        source=_GILBERT_SEN,
    ),
)
"""The Tier B formulas of the module (Nogat CMP-2.2)."""


# --- the test with Sen's slope, as stats mann-kendall gives it ------------------------


@dataclass
class SenSlope(JsonResultMixin):
    """Sen's slope of a series with its intercept and confidence interval.

    Attributes
    ----------
    slope : float
        Sen's slope (spec ``sen_slope``), in the unit of the values per unit of time.
    intercept : float
        Conover's intercept: the line at t = 0.
    lower, upper : float or None
        The limits of the 100 (1 − alpha) % confidence interval of the slope (spec
        ``sen_interval``); ``None`` when a limit's rank falls outside the slopes.
    n_slopes : int
        Number of pairs whose slope was taken.
    """

    slope: float
    intercept: float
    lower: float | None
    upper: float | None
    n_slopes: int


@dataclass
class MannKendallResult(JsonResultMixin):
    """Result of the Mann-Kendall trend test.

    Attributes
    ----------
    s_statistic : float
        Mann-Kendall S statistic (sum of sign differences), spec ``mann_kendall``.
    var_s : float
        Variance of S under the null hypothesis of no trend, corrected for the
        groups of tied values.
    z_score : float
        Standardised test statistic with the continuity correction.
    p_value : float
        Two-sided p-value for the null hypothesis of no trend: from the exact
        distribution of S below 10 values, else from the normal distribution of Z.
    p_value_method : str
        ``"exact"`` below 10 values (Gilbert, 1987, section 16.4.1: every distinct
        ordering of the values equally likely under no trend, ties included),
        ``"normal"`` from 10 values (section 16.4.2).
    trend_detected : bool
        True when p_value < significance_level.
    trend_direction : str
        "increasing", "decreasing", or "none".
    significance_level : float
        Alpha level used for the test decision.
    sen_slope : float or None
        Sen's slope per unit of the times of the values (per step without them).
    sen_intercept : float or None
        Conover's intercept of the line: its value at time 0.
    sen_slope_lower, sen_slope_upper : float or None
        The 100 (1 − significance_level) % confidence interval of the slope
        (Gilbert, 1987); ``None`` below 10 values, where the normal approximation
        of S it rests on does not apply (Gilbert, 1987, p. 218), or when a limit's
        rank falls outside the slopes.
    """

    s_statistic: float
    var_s: float
    z_score: float
    p_value: float
    p_value_method: str
    trend_detected: bool
    trend_direction: str
    significance_level: float
    sen_slope: float | None = None
    sen_intercept: float | None = None
    sen_slope_lower: float | None = None
    sen_slope_upper: float | None = None


def sen_slope(
    values: NDArray[np.floating],
    times: NDArray[np.floating],
    *,
    var_s: float,
    alpha: float = 0.05,
) -> SenSlope:
    """Estimate Sen's slope with Conover's intercept and Gilbert's interval.

    The slope and the intercept are those of the spec ``sen_slope``
    (:func:`sen_line`), the interval that of the spec ``sen_interval``
    (:func:`sen_interval`), whose limits are ``None`` when their ranks fall outside
    the ordered slopes.

    Parameters
    ----------
    values : NDArray[np.floating]
        The values.
    times : NDArray[np.floating]
        Their times (years, or the steps of the series), in order.
    var_s : float
        The variance of Kendall's S that the interval is built on: that of the
        Mann-Kendall test of the values, corrected for their ties
        (:func:`mann_kendall_test`).
    alpha : float, optional
        The interval covers 1 − alpha, by default 0.05 (95 %).

    Returns
    -------
    SenSlope
        The slope, the intercept and the interval.

    Raises
    ------
    InvalidParameterError
        If the specs refuse the inputs: arrays of different lengths, a value that is
        not finite, times that decrease or of one time, ``var_s`` below 0 or not
        finite, ``alpha`` outside (0, 1).
    """
    data = cast("NDArray[np.float64]", values)  # the spec checks what it is
    steps = cast("NDArray[np.float64]", times)
    line = sen_line(data, steps)
    try:
        lower, upper = sen_interval(data, steps, var_s, alpha)
    except InvalidParameterError as refused:
        if refused.details.get("constraint") != "ranks_within_slopes":
            raise
        return SenSlope(line.slope, line.intercept, None, None, line.n_slopes)
    return SenSlope(line.slope, line.intercept, lower, upper, line.n_slopes)


def mann_kendall_test(
    series: NDArray[np.floating],
    alpha: float = 0.05,
    times: NDArray[np.floating] | None = None,
) -> MannKendallResult:
    """Perform the Mann-Kendall non-parametric trend test with Sen's slope.

    The statistics are those of the spec ``mann_kendall`` (:func:`mann_kendall`), the
    slope and its interval those of :func:`sen_slope`; the decision and the direction
    follow the Tier B convention ``trend_decision``. Ties are values exactly equal:
    round a series computed in floating point to its precision first.

    Parameters
    ----------
    series : NDArray[np.floating]
        1-D array of observations ordered in time.  Must contain at least
        3 elements.
    alpha : float, optional
        Significance level for trend detection (default 0.05), in (0, 1).
    times : NDArray[np.floating], optional
        The times of the observations (e.g. their years), strictly increasing; by
        default the steps 0, 1, 2, ... of the series.

    Returns
    -------
    MannKendallResult
        Dataclass with all test statistics, the trend decision and Sen's slope.

    Raises
    ------
    InvalidParameterError
        If *series* is refused by the spec ``mann_kendall`` (fewer than 3
        observations, a value that is not finite), *times* differ in length from it
        or do not increase strictly, or the specs of Sen's slope refuse the inputs
        (*alpha* outside (0, 1), more than 5,000 values).
    """
    test = mann_kendall(cast("NDArray[np.float64]", series))
    data = np.asarray(series, dtype=np.float64)
    n = data.size
    if times is None:
        steps = np.arange(n, dtype=np.float64)
    else:
        steps = np.asarray(times, dtype=np.float64)
        if steps.shape != data.shape:
            raise InvalidParameterError(
                f"times must have one item per observation; received {steps.size} "
                f"for {n}."
            )
        if not np.all(np.diff(steps) > 0):
            raise InvalidParameterError("times must increase strictly.")
    estimate = sen_slope(data, steps, var_s=test.var_s, alpha=alpha)
    trend_detected = test.p_value < alpha
    if not trend_detected:
        trend_direction = "none"
    elif test.s > 0:
        trend_direction = "increasing"
    else:
        trend_direction = "decreasing"
    interval = n >= _EXACT_BELOW
    return MannKendallResult(
        s_statistic=float(test.s),
        var_s=test.var_s,
        z_score=test.z,
        p_value=test.p_value,
        p_value_method=test.p_value_method,
        trend_detected=trend_detected,
        trend_direction=trend_direction,
        significance_level=alpha,
        sen_slope=estimate.slope,
        sen_intercept=estimate.intercept,
        sen_slope_lower=estimate.lower if interval else None,
        sen_slope_upper=estimate.upper if interval else None,
    )
