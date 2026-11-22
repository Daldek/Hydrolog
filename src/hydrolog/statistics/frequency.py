"""Distributions of annual extremes: sample statistics and parameter estimators.

The formulas of the frequency analyses of annual maxima
(:class:`~hydrolog.statistics.FloodFrequencyAnalysis`) and minima
(:func:`~hydrolog.statistics.fit_fisher_tippett_minima`), declared by their specs
(Nogat's computation standard, ADR-0050): the sample's product moments
(:data:`MOMENTS`, ``sample_moments``) and L-moments (:data:`L_MOMENTS`,
``sample_l_moments``), the estimators of the parameters of the log-normal, GEV,
Pearson type III and Weibull distributions of :mod:`scipy.stats` by L-moments,
moments, maximum likelihood and least squares, and the goodness of a fit: the
Anderson-Darling statistic (:data:`ANDERSON_DARLING`, ``anderson_darling``) and
the Akaike information criterion (:data:`AKAIKE`, ``akaike_information_criterion``).
``docs/FORMULAS.md`` shows their equations, constants, ranges and sources.

Examples
--------
>>> from hydrolog.statistics.frequency import sample_l_moments, sample_moments
>>> sample_l_moments([1.0, 2.0, 3.0, 4.0, 10.0])
SampleLMoments(l1=4.0, l2=2.0, t3=0.5)
>>> sample_moments([1.0, 2.0, 3.0, 4.0, 5.0]).skewness
0.0
"""

from __future__ import annotations

import math
from collections.abc import Callable
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from statistics import NormalDist
from typing import Any, Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq, minimize
from scipy.special import erfinv, gamma, gammaln, zeta
from scipy.stats import genextreme, lognorm, pearson3, weibull_min

from hydrolog._formulas import ERRORS, checked_inputs, checked_outputs
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
    Tolerance,
    Values,
    Variable,
    assert_within,
)

__all__ = [
    "AKAIKE",
    "ANDERSON_DARLING",
    "FIT_LEAST_SQUARES",
    "FIT_L_MOMENTS",
    "FIT_MAXIMUM_LIKELIHOOD",
    "FIT_MOMENTS",
    "GEV_QUANTILES",
    "LOG_NORMAL_QUANTILES",
    "L_MOMENTS",
    "MOMENTS",
    "PEARSON3_QUANTILES",
    "SPECS",
    "WEIBULL_QUANTILES",
    "FittedParameters",
    "SampleLMoments",
    "SampleMoments",
    "akaike_information_criterion",
    "anderson_darling",
    "fit_l_moments",
    "fit_least_squares",
    "fit_maximum_likelihood",
    "fit_moments",
    "gev_quantiles",
    "log_normal_quantiles",
    "pearson3_quantiles",
    "sample_l_moments",
    "sample_moments",
    "weibull_quantiles",
]

_DISTRIBUTIONS: Final[dict[str, Any]] = {
    "log_normal": lognorm,
    "gev": genextreme,
    "pearson3": pearson3,
    "weibull": weibull_min,
}
_MIN_VALUES: Final = 3  # the skewness and the L-skewness need three values
# Maximum likelihood needs more values than the distribution has parameters.
_PARAMETER_COUNTS: Final = {"log_normal": 2, "gev": 3, "pearson3": 3, "weibull": 3}
# The likelihood of a three-parameter distribution has no maximum where its density is
# infinite at a bound of the support: placed at the closest value, the bound makes the
# likelihood grow without limit (Smith 1985). That happens for the GEV with scipy's
# shape c >= 1 (xi <= -1), Pearson III with |skewness| >= 2 (gamma shape <= 1) and
# Weibull with shape <= 1, so the estimate is the maximum in the shapes short of these
# limits, if there is one. The search also stays within the GEVs that have a mean,
# c > -1 (xi < 1), and the Weibull shapes up to _ML_WEIBULL_SHAPE, beyond which the
# Weibull distribution is the reversed Gumbel's within a few per cent: a search that
# runs to one of these ends finds no maximum inside them.
_ML_WEIBULL_SHAPE: Final = 50.0
# Least squares searches the log-normal ln s below ln 5, the GEV c in (-1, 50),
# Pearson III's skewness in (-9, 9) and the Weibull ln k below ln 50: the shapes of
# the quantile functions' test bounds, beyond which the fit is a limit of the family.
_LS_SHAPES: Final = {
    "log_normal": (-math.inf, math.log(5.0)),
    "gev": (-1.0, 50.0),
    "pearson3": (-9.0, 9.0),
    "weibull": (-math.inf, math.log(50.0)),
}
# The searches for the maximum likelihood and the least squares (Nelder-Mead on the
# standardised sample): each is run again from the point found until a run gains no
# more than _SEARCH_GAIN, at most _SEARCH_RUNS times. The likelihood's start has a
# shape at least _ML_INSIDE short of the limit and a bound _ML_MARGIN standard
# deviations beyond the sample; an end closer to the limit than _ML_EDGE is the
# limit, where there is no maximum. Nor is there one where the search runs to a
# scale below exp(_ML_LEAST_LOG_SCALE) standard deviations: values tied at the
# smallest make the likelihood grow without limit as the scale falls to 0 (a heavy
# upper tail keeps the density of the others).
_NELDER_MEAD: Final = {
    "xatol": 1e-10,
    "fatol": 1e-12,
    "maxiter": 10_000,
    "maxfev": 20_000,
}
_SEARCH_RUNS: Final = 20
_SEARCH_GAIN: Final = 1e-9
_ML_INSIDE: Final = 0.1
_ML_MARGIN: Final = 0.05
_ML_EDGE: Final = 1e-3
_ML_LEAST_LOG_SCALE: Final = math.log(1e-6)
# The skewness and the L-skewness of the Gumbel distribution (the GEV with shape 0):
# the Weibull distribution of the moments and L-moments needs a sample statistic above
# minus these, the limit of its skewness and L-skewness as its shape grows.
_GUMBEL_SKEWNESS: Final = float(12.0 * np.sqrt(6.0) * zeta(3.0) / np.pi**3)  # 1.1395
_GUMBEL_L_SKEWNESS: Final = float(2.0 * np.log(3.0) / np.log(2.0) - 3.0)  # 0.1699
# Brackets of the GEV shape c (scipy's sign; Hosking's k, -ξ of Coles 2001): the
# skewness exists above c = -1/3 and the mean (so the L-moments) above c = -1; the
# gamma functions of the skewness overflow above c of about 56. The Weibull
# distribution is the GEV of the negated sample with c > 0 (its shape 1 / c at most
# a billion). Below |c| = _GUMBEL_SHAPE the GEV of the L-moments is the Gumbel's.
_GEV_SHAPES_BY_SKEWNESS: Final = (-1.0 / 3.0 + 1e-6, 50.0)
_GEV_SHAPES_BY_L_SKEWNESS: Final = (-1.0 + 1e-9, 50.0)
_WEIBULL_SHAPES: Final = (1e-9, 50.0)
_GUMBEL_SHAPE: Final = 1e-8


# --- sources ---------------------------------------------------------------------

_B17B: Final = (
    "Interagency Advisory Committee on Water Data (1982). Guidelines for Determining "
    "Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. "
    "Geological Survey, Reston, Virginia"
)
_B17B_URL: Final = "https://pubs.usgs.gov/unnumbered/70275162/report.pdf"
_WMO_168: Final = (
    "WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of "
    "Water Resources and Application of Hydrological Practices, WMO-No. 168"
)
_WMO_168_URL: Final = (
    "https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf"
)
_WMO_1029: Final = (
    "WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology "
    "Report No. 50, WMO-No. 1029"
)
_WMO_1029_URL: Final = "https://library.wmo.int/idurl/4/32176"
_KZGW: Final = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL: Final = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_HOSKING_1990: Final = Source(
    citation="Hosking, J.R.M. (1990). L-moments: analysis and estimation of "
    "distributions using linear combinations of order statistics. Journal of the "
    "Royal Statistical Society, Series B 52(1), 105-124",
    locator="sect. 2: probability-weighted moments and the sample L-moments of their "
    "unbiased estimators",
    access="author-provided",
)
_LMOM: Final = (
    "Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran "
    "routines of Hosking and Wallis 1997)"
)
_LMOM_URL: Final = "https://cran.r-project.org/package=lmom"
_LMOMCO: Final = (
    "Asquith, W.H. lmomco: L-moments, censored L-moments, trimmed L-moments, "
    "L-comoments, and many distributions, R package version 2.5.8, CRAN"
)
_LMOMCO_URL: Final = "https://cran.r-project.org/package=lmomco"
_SCIPY_SKEW: Final = Source(
    citation="Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for "
    "scientific computing in Python. Nature Methods 17, 261-272",
    locator="scipy.stats.skew with bias=False: the adjusted Fisher-Pearson "
    "standardized moment coefficient G1 = sqrt(n (n - 1)) / (n - 2) m3 / m2**1.5",
    url="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html",
)
_KZGW_MAXIMA: Final = Source(
    citation=_KZGW,
    locator="examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual "
    "maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana)",
    url=_KZGW_URL,
)

_UNIT: Final = "m3/s"
"""The unit of the samples in the documents: the formulas are homogeneous (their
scalings), so a sample in any unit, a stage in cm or logarithms of discharge, gives
its statistics and parameters in that unit."""

_ANY_VALUE: Final = Range(
    test_low=-1.0e6,
    test_high=1.0e6,
    test_reason=(
        "the formulas are homogeneous in the unit of the sample (their scalings), so "
        "any bound tests their arithmetic: a million m3/s exceeds the discharge of "
        "every river, and a stage may lie below its gauge's zero, so the same bound "
        "holds below 0"
    ),
)
"""Any finite value: an annual extreme of a discharge or of a stage."""

_MAXIMA: Final = Range(low=0.81, high=111.0, source=_KZGW_MAXIMA)
"""The annual maxima of the worked examples of Polish practice."""
_MINIMA: Final = Range(
    low=0.0,
    high=78.0,
    source=Source(
        citation=_WMO_1029,
        locator="table 7.1, p. 64: the AM(7) annual minima of stations 223204 and "
        "223207, 0 to 78 in the unit of the table",
        url=_WMO_1029_URL,
    ),
)
"""The annual minima of the worked examples of WMO-No. 1029."""


_POLANA: Final = (
    10.2, 9.24, 58.8, 8.23, 16.2, 4.92, 26.8, 25.1, 97.2, 23.5, 22.3, 21.1, 59.9,
    55.1, 16.2, 24.6, 14.8, 73.8, 28.9, 18.6, 18.2, 25.8, 14.5, 11.2, 54.5, 111.0,
    35.1, 43.0, 52.0, 45.4, 8.90, 9.72, 57.4, 50.8,
)  # fmt: skip
"""The annual maxima of the Czarna at Polana [m3/s], 34 years (KZGW 2017, example
3.2, table 3.5): the typical sample of the generated tests."""


def _sample_variable(description: str) -> Variable:
    return Variable(
        name="values",
        symbol="x_i",
        unit=_UNIT,
        kind="real_array",
        description=description,
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MAXIMA,
    )


def _count(least: int, source: Source, name: str = "values") -> Constraint:
    """Return the precondition of at least ``least`` values of input ``name``."""
    return Constraint(
        name="enough_values",
        cls="precondition",
        check=lambda x: x.array(name).size >= least,
        text=f"n >= {least}",
        source=source,
        satisfied={name: [1.0, 2.0, 4.0, 8.0, 16.0][: least + 1]},
        violated={name: [1.0, 2.0, 4.0, 8.0][: least - 1]},
        boundary={name: [1.0, 2.0, 4.0, 8.0][:least]},
    )


def _not_constant(
    source: Source,
    name: str = "values",
    satisfied: tuple[float, ...] = (5.0, 5.0, 5.0, 6.0),
) -> Constraint:
    """Return the precondition of values of input ``name`` not all equal."""
    return Constraint(
        name="values_not_all_equal",
        cls="precondition",
        check=lambda x: bool(np.ptp(x.array(name)) > 0.0),
        text="min(x) < max(x)",
        source=source,
        satisfied={name: list(satisfied)},
        violated={name: [5.0, 5.0, 5.0, 5.0]},
    )


def _normalised(data: NDArray[np.float64]) -> tuple[NDArray[np.float64], int]:
    """Return the sample over the power of two bringing its largest into [½, 1).

    The division is exact, so the sums of the statistics round as on the sample
    itself but never underflow or overflow; the exponent multiplies them back.
    """
    largest = float(np.max(np.abs(data)))
    exponent = math.frexp(largest)[1] if largest > 0.0 else 0
    return np.ldexp(data, -exponent), exponent


# --- product moments -------------------------------------------------------------


class SampleMoments(NamedTuple):
    """Mean, standard deviation and skewness of a sample (spec ``sample_moments``)."""

    mean: float
    std: float
    skewness: float


def _moments(data: NDArray[np.float64]) -> SampleMoments:
    """Return the product moments of three values or more, not all equal.

    The deviations are taken from the mean twice: the second pass removes the
    rounding of the first mean, which a large mean makes large next to a small
    spread (the corrected two-pass algorithm). The cubes are products, rounded
    alike on every platform and negated exactly with the sample; ``numpy.power``
    may call a vector pow that is neither.
    """
    scaled, exponent = _normalised(data)
    n = data.size
    centre = float(np.mean(scaled))
    deviations = scaled - centre
    residual = float(np.mean(deviations))
    deviations -= residual
    squares = deviations * deviations
    m2 = float(np.mean(squares))
    m3 = float(np.mean(squares * deviations))
    skewness = math.sqrt(n * (n - 1)) / (n - 2) * m3 / m2**1.5
    std = math.sqrt(m2 * n / (n - 1))
    return SampleMoments(
        math.ldexp(centre + residual, exponent), math.ldexp(std, exponent), skewness
    )


def _exact_moments(values: list[float]) -> tuple[float, float, float]:
    """Return the mean, standard deviation and skewness in rational arithmetic.

    Only the square roots round: s from the exact s², G from the exact G².
    """
    exact = [Fraction(value) for value in values]
    n = len(exact)
    mean = sum(exact, Fraction(0)) / n
    m2 = sum(((v - mean) ** 2 for v in exact), Fraction(0)) / n
    m3 = sum(((v - mean) ** 3 for v in exact), Fraction(0)) / n
    squared = Fraction(n * (n - 1), (n - 2) ** 2) * m3**2 / m2**3
    skewness = math.copysign(math.sqrt(float(squared)), float(m3))
    return float(mean), math.sqrt(float(m2 * n / (n - 1))), skewness


_RATIONAL_SAMPLES: Final = (
    (1.0, 2.0, 3.0, 4.0, 10.0),
    (0.1, 0.2, 0.3, 0.3, 0.7, 0.6),
    _POLANA,
    tuple(1.0e9 + value for value in (0.001, 0.002, 0.004, 0.0085, 0.016, 0.031)),
)
"""Samples of the exact oracles: integers, decimals, the Polana maxima and a large
mean with a small spread (the trap of cancellation)."""


def _rational_moments(run: Callable[..., Values]) -> None:
    for sample in _RATIONAL_SAMPLES:
        out = run(values=list(sample))
        mean, std, skewness = _exact_moments(list(sample))
        assert_within(
            [out.real("mean"), out.real("std")],
            [mean, std],
            rel=1e-14,
            reason="the exact rational mean and standard deviation; the code's "
            "pairwise sums of a few tens of values round within a few ulp",
        )
        assert_within(
            out.real("skewness"),
            skewness,
            abs=1e-12,
            reason="the exact rational skewness; the third moment of deviations of "
            "both signs loses digits to cancellation, by at most n ulp of the sum of "
            "their absolute cubes over m2**1.5",
        )


def _mirrored(x: Values) -> dict[str, object]:
    return {"values": -x.array("values")}


_EXACT: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="the statistics run on the sample scaled by a power of two, so doubling "
    "or negating it changes no rounding; a result below the normal floats keeps fewer "
    "bits",
)


MOMENTS: Final = FormulaSpec(
    name="sample_moments",
    title="Mean, standard deviation and skewness of a sample (product moments)",
    function="hydrolog.statistics.frequency.sample_moments",
    family="statistic",
    equation=(
        "mean = sum(x) / n; s = sqrt(sum((x - mean)**2) / (n - 1)); G = sqrt(n (n - "
        "1)) / (n - 2) * m3 / m2**1.5 with m_k = sum((x - mean)**k) / n"
    ),
    latex=(
        r"\bar{x} = \frac{1}{n}\sum_i x_i,\quad s = \sqrt{\frac{\sum_i (x_i - "
        r"\bar{x})^2}{n - 1}},\quad G = \frac{\sqrt{n(n - 1)}}{n - 2}\,"
        r"\frac{m_3}{m_2^{3/2}},\quad m_k = \frac{1}{n}\sum_i (x_i - \bar{x})^k"
    ),
    variables=(_sample_variable("The sample, annual maxima or minima."),),
    outputs=(
        Output(
            name="mean",
            unit=_UNIT,
            symbol=r"\bar{x}",
            description="Arithmetic mean.",
            physical=Range(),
        ),
        Output(
            name="std",
            unit=_UNIT,
            symbol="s",
            description="Standard deviation with the divisor n - 1.",
            physical=Range(low=0.0),
        ),
        Output(
            name="skewness",
            unit="-",
            symbol="G",
            description="Adjusted Fisher-Pearson coefficient of skewness.",
            physical=Range(),
        ),
    ),
    sources=(
        Source(
            citation=_B17B,
            locator="eqs. 2, 3a and 4a (equal to 3b and 4b), pp. 9-10; appendix 12, "
            "example 1, table 12-2 and eqs. 12-1 to 12-3",
            url=_B17B_URL,
        ),
        Source(
            citation=_WMO_1029,
            locator="sect. 7.6.1, eqs. 7.7 and 7.8, p. 63 (its eq. 7.9 is the biased "
            "skewness m3 / m2**1.5); table 7.1, p. 64",
            url=_WMO_1029_URL,
        ),
        _SCIPY_SKEW,
    ),
    constraints=(
        _count(
            3,
            Source(
                citation=_B17B,
                locator="eq. 4a: the skewness divides by (N - 1)(N - 2)",
                url=_B17B_URL,
            ),
        ),
        _not_constant(
            Source(
                citation=_B17B,
                locator="eq. 4a: the skewness divides by S cubed, 0 for equal values",
                url=_B17B_URL,
            )
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"values": 1},
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0},
                outputs={"mean": 1.0, "std": 1.0},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated sample has the negated mean and skewness and the "
                "same standard deviation",
                inputs=_mirrored,
                outputs=lambda out: {
                    "mean": -out.real("mean"),
                    "std": out.real("std"),
                    "skewness": -out.real("skewness"),
                },
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the statistics of the definition in exact rational arithmetic",
                check=_rational_moments,
            ),
        ),
    ),
    validation="none: the definitions of the sample statistics",
    formula_version=1,
    status="referenced",
    conventions=(
        "the standard deviation with the divisor n - 1 (Bulletin 17B eq. 3a; WMO-No. "
        "1029 eq. 7.8)",
        "the skewness G of Bulletin 17B eq. 4a, N sum((X - mean)**3) / ((N - 1)(N - "
        "2) S**3), which is the adjusted Fisher-Pearson coefficient G1 of "
        "scipy.stats.skew with bias=False; WMO-No. 1029 eq. 7.9 is the biased "
        "m3 / m2**1.5, G (n - 2) / sqrt(n (n - 1))",
        "the sample in any unit: the mean and the standard deviation in its unit, the "
        "skewness without one",
        "the moments of the deviations from the mean (eqs. 3a and 4a, which Bulletin "
        "17B p. 10 finds less sensitive to the digits carried than the sums of powers "
        "of eqs. 3b and 4b), centred twice, on the sample divided by a power of two",
    ),
    traps={
        "singular_at_bound": "constraint case values_not_all_equal-violated: m2 = 0 "
        "of equal values is refused before the division by m2**1.5",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "many_small_terms": "test_long_samples_keep_their_moments",
        "moment_cancellation": "limit exact_rational: a mean of 1e9 with a spread of "
        "0.03 against rational arithmetic",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the mean, the standard deviation and the skewness in exact "
            "rational arithmetic (fractions)",
            test="tests/unit/test_formulas_flood_frequency.py (limit exact_rational)",
        ),
        Oracle(
            kind="established",
            description="numpy.mean, numpy.std with ddof=1 and scipy.stats.skew with "
            "bias=False",
            test="tests/unit/test_formulas_flood_frequency.py "
            "(test_the_moments_are_numpys_and_scipys)",
            conventions=(
                "scipy.stats.skew(bias=False) is the adjusted Fisher-Pearson G1, the "
                "skewness of the spec",
                "numpy.std(ddof=1) has the divisor n - 1 of the spec",
            ),
        ),
    ),
    base={"values": list(_POLANA)},
)


def sample_moments(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> SampleMoments:
    """Return a sample's mean, standard deviation and skewness, spec sample_moments.

    Parameters
    ----------
    values : array_like of float
        The sample.

    Returns
    -------
    SampleMoments
        Its mean, standard deviation and skewness.

    Raises
    ------
    InvalidParameterError
        If the sample is refused by the spec: too short, all equal or not finite.
    """
    x = checked_inputs(MOMENTS, values=values)
    out = checked_outputs(MOMENTS, _moments(x.array("values"))._asdict())
    return SampleMoments(out.real("mean"), out.real("std"), out.real("skewness"))


# --- L-moments -------------------------------------------------------------------


class SampleLMoments(NamedTuple):
    """L-moments λ1, λ2 and L-skewness τ3 of a sample (spec ``sample_l_moments``)."""

    l1: float
    l2: float
    t3: float


def _l_moments(data: NDArray[np.float64]) -> SampleLMoments:
    """Return the L-moments of a sample of three values or more, not all equal.

    λ2 and λ3 are the weighted sums of the ordered deviations from the mean that the
    probability-weighted moments make, 2 b1 - b0 and 6 b2 - 6 b1 + b0, with their
    weights summed first: no difference of the large b_r rounds away the small
    L-moments, and a large mean leaves the spread its digits. λ1 is the mean of
    :func:`_moments`, centred twice.
    """
    scaled, exponent = _normalised(data)
    n = data.size
    centre = float(np.mean(scaled))
    deviations = scaled - centre
    residual = float(np.mean(deviations))
    ascending = np.sort(deviations)
    rank = np.arange(n, dtype=np.float64)  # j - 1
    weights_2 = (2.0 * rank - (n - 1)) / (n * (n - 1))
    weights_3 = (
        6.0 * rank * (rank - 1.0) / ((n - 1) * (n - 2)) - 6.0 * rank / (n - 1) + 1.0
    ) / n
    l2 = float(weights_2 @ ascending)
    return SampleLMoments(
        math.ldexp(centre + residual, exponent),
        math.ldexp(l2, exponent),
        float(weights_3 @ ascending) / l2,
    )


def _exact_l_moments(values: list[float]) -> tuple[float, float, float]:
    """λ1, λ2 and τ3 of the unbiased probability-weighted moments, rationally."""
    ascending = sorted(Fraction(value) for value in values)
    n = len(ascending)
    b = [
        sum(
            (math.comb(j, r) * x for j, x in enumerate(ascending)),
            Fraction(0),
        )
        / (n * math.comb(n - 1, r))
        for r in range(3)
    ]
    l2 = 2 * b[1] - b[0]
    return float(b[0]), float(l2), float((6 * b[2] - 6 * b[1] + b[0]) / l2)


def _rational_l_moments(run: Callable[..., Values]) -> None:
    for sample in _RATIONAL_SAMPLES:
        out = run(values=list(sample))
        assert_within(
            [out.real("l1"), out.real("l2"), out.real("t3")],
            list(_exact_l_moments(list(sample))),
            rel=1e-13,
            reason="the exact rational L-moments of b_r = n^-1 C(n - 1, r)^-1 sum "
            "C(j - 1, r) x(j); the code's weighted sums of a few tens of deviations "
            "round within tens of ulp",
        )


L_MOMENTS: Final = FormulaSpec(
    name="sample_l_moments",
    title="L-moments and L-skewness of a sample (unbiased probability-weighted "
    "moments)",
    function="hydrolog.statistics.frequency.sample_l_moments",
    family="statistic",
    equation=(
        "b_r = n^-1 C(n - 1, r)^-1 sum_j C(j - 1, r) x(j) over the ascending sample "
        "x(1) <= ... <= x(n); l1 = b0; l2 = 2 b1 - b0; t3 = (6 b2 - 6 b1 + b0) / l2"
    ),
    latex=(
        r"b_r = \frac{1}{n}\binom{n - 1}{r}^{-1}\sum_{j=1}^{n}\binom{j - 1}{r}"
        r"x_{(j)},\quad \lambda_1 = b_0,\quad \lambda_2 = 2b_1 - b_0,\quad "
        r"\tau_3 = \frac{6b_2 - 6b_1 + b_0}{\lambda_2}"
    ),
    variables=(_sample_variable("The sample, annual maxima or minima."),),
    outputs=(
        Output(
            name="l1",
            unit=_UNIT,
            symbol=r"\lambda_1",
            description="First L-moment, the mean.",
            physical=Range(),
        ),
        Output(
            name="l2",
            unit=_UNIT,
            symbol=r"\lambda_2",
            description="Second L-moment, half the mean difference of two values.",
            physical=Range(low=0.0),
        ),
        Output(
            name="t3",
            unit="-",
            symbol=r"\tau_3",
            description="L-skewness; 1 (or -1) for values all equal but the largest "
            "(the smallest).",
            physical=Range(low=-1.0, high=1.0),
            boundary_tolerance=1e-9,
        ),
    ),
    sources=(
        _HOSKING_1990,
        Source(
            citation=_LMOM,
            locator="samlmu: the sample L-moments of Hosking (1990) from the unbiased "
            "probability-weighted moments",
            url=_LMOM_URL,
        ),
        Source(
            citation=_LMOMCO,
            locator="pwm.ub: beta_r = n^-1 C(n - 1, r)^-1 sum C(j - 1, r) x(j:n); "
            "lmoms",
            url=_LMOMCO_URL,
        ),
        Source(
            citation=_WMO_168,
            locator="sect. 5.5.1, eqs. 5.25 to 5.27 and table II.5.4, pp. II.5-11 to "
            "II.5-12",
            url=_WMO_168_URL,
        ),
        Source(
            citation=_WMO_1029,
            locator="sect. 7.6.2, eqs. 7.11 and 7.12, p. 64; table 7.1, p. 64",
            url=_WMO_1029_URL,
        ),
    ),
    constraints=(
        _count(
            3,
            Source(
                citation=_LMOMCO,
                locator="pwm.ub: b2 divides by C(n - 1, 2), 0 for n < 3",
                url=_LMOMCO_URL,
            ),
        ),
        _not_constant(
            Source(
                citation=_WMO_168,
                locator="table II.5.4: the L-skewness is lambda3 / lambda2, and "
                "lambda2 is 0 for equal values",
                url=_WMO_168_URL,
            )
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"values": 1},
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0},
                outputs={"l1": 1.0, "l2": 1.0},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated sample has the negated l1 and t3 and the same l2",
                inputs=_mirrored,
                outputs=lambda out: {
                    "l1": -out.real("l1"),
                    "l2": out.real("l2"),
                    "t3": -out.real("t3"),
                },
                tolerance=Tolerance(
                    abs=1e-13,
                    rel=1e-13,
                    reason="the negated sample has the negated mean exactly and "
                    "sorts in the reverse order: l2 and l3 add the same terms in the "
                    "other order, within n ulp of the mean absolute deviation, at "
                    "most 2 l2, so t3 within 4 n ulp",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the L-moments of the definition in exact rational arithmetic",
                check=_rational_l_moments,
            ),
        ),
    ),
    validation="none: the definitions of the sample statistics",
    formula_version=1,
    status="referenced",
    conventions=(
        "the unbiased probability-weighted moments b_r of the ascending sample "
        "(Hosking 1990; lmom samlmu; lmomco pwm.ub), not the biased estimators of "
        "plotting positions",
        "the L-skewness t3 = lambda3 / lambda2 (WMO-No. 168 table II.5.4)",
        "the sample in any unit: l1 and l2 in its unit, t3 without one",
        "lambda2 and lambda3 as the weighted sums of the ordered deviations from the "
        "mean that the b_r make (their weights summed first), on the sample divided "
        "by a power of two; l1 the mean centred twice",
        "|t3| = 1 for values all equal but the largest or the smallest; the weighted "
        "sums of n values round by up to n ulp, so a t3 within 1e-9 beyond 1 or -1 "
        "is set to the bound (its boundary tolerance)",
    ),
    traps={
        "singular_at_bound": "constraint case values_not_all_equal-violated: l2 = 0 "
        "of equal values is refused before the division by l2",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "many_small_terms": "test_long_samples_keep_their_moments",
        "moment_cancellation": "limit exact_rational: a mean of 1e9 with a spread of "
        "0.03 against rational arithmetic",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the L-moments of the unbiased probability-weighted moments "
            "in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_flood_frequency.py (limit exact_rational)",
        ),
        Oracle(
            kind="frozen",
            description="lmom 3.3 samlmu (Hosking) and lmomco 2.5.8 lmoms (Asquith) "
            "on seven samples, R 4.5.3, 2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "samlmu and lmoms give the L-moments of the unbiased "
                "probability-weighted moments, as the spec",
            ),
        ),
    ),
    base={"values": list(_POLANA)},
)


def sample_l_moments(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> SampleLMoments:
    """Return the L-moments and the L-skewness of a sample, spec sample_l_moments.

    Parameters
    ----------
    values : array_like of float
        The sample.

    Returns
    -------
    SampleLMoments
        Its first and second L-moments and its L-skewness.

    Raises
    ------
    InvalidParameterError
        If the sample is refused by the spec: too short, all equal or not finite.
    """
    x = checked_inputs(L_MOMENTS, values=values)
    out = checked_outputs(L_MOMENTS, _l_moments(x.array("values"))._asdict())
    return SampleLMoments(out.real("l1"), out.real("l2"), out.real("t3"))


# --- quantiles of return periods ----------------------------------------------------

_KZGW_FITS: Final = Source(
    citation=_KZGW,
    locator="examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the "
    "Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four "
    "estimators give their annual maxima, with the log-normal and Weibull parameters "
    "the examples print (pp. 47-48 and 53-54)",
    url=_KZGW_URL,
)
_DESIGN_PERIODS: Final = Source(
    citation="Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie "
    "warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich "
    "usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values",
    locator="załącznik nr 4: the control flood of a structure of class I at p = "
    "0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years",
    url="https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20070860579",
)
_SCIPY_STATS: Final = Source(
    citation="Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for "
    "scientific computing in Python. Nature Methods 17, 261-272",
    locator="scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the "
    "inverse of the survival function",
    url="https://docs.scipy.org/doc/scipy/reference/stats.html",
)

_RETURN_PERIODS: Final = Variable(
    name="return_periods_years",
    symbol="T",
    unit="years",
    kind="real_array",
    description="Return periods: the quantile of T years is exceeded with the "
    "probability 1/T in a year.",
    physical=Range(
        low=1.0,
        low_inclusive=False,
        test_high=1.0e6,
        test_reason="a million years lies far beyond every design flood (the Polish "
        "rules ask for 5,000 years at most) and tests the far tail of each "
        "distribution",
    ),
    applicability="unstated",
    typical=Range(low=2.0, high=5000.0, source=_DESIGN_PERIODS),
)
_SCALE_RANGE: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=1.0e6,
    test_reason="the formulas are homogeneous in the unit of loc and scale (their "
    "scalings), so any bound tests their arithmetic: a million m3/s exceeds the "
    "discharge of every river",
)


def _parameter(
    name: str,
    symbol: str,
    description: str,
    physical: Range,
    typical: tuple[float, float],
    unit: str = _UNIT,
) -> Variable:
    return Variable(
        name=name,
        symbol=symbol,
        unit=unit,
        description=description,
        physical=physical,
        applicability="unstated",
        typical=Range(low=typical[0], high=typical[1], source=_KZGW_FITS),
    )


def _quantiles_output(text: str) -> Output:
    return Output(
        name="quantiles",
        unit=_UNIT,
        kind="real_array",
        symbol="Q_T",
        description=text,
        physical=Range(),
    )


def _isf(name: str, shape: float, x: Values) -> NDArray[np.float64]:
    """Return the quantiles of distribution ``name`` at the exceedance 1/T."""
    periods = x.array("return_periods_years")
    quantiles = _DISTRIBUTIONS[name].isf(
        1.0 / periods, shape, loc=x.real("loc"), scale=x.real("scale")
    )
    return np.asarray(quantiles, dtype=np.float64)


_SCALED_QUANTILES: Final = Scaling(
    name="unit_of_the_sample",
    inputs={"loc": 1.0, "scale": 1.0},
    outputs={"quantiles": 1.0},
    tolerance=Tolerance(
        abs=1e-300,
        rel=4.5e-16,
        reason="the quantile is loc + scale times that of the standard distribution, "
        "and doubling loc and scale rounds alike",
    ),
)
_SHIFTED_QUANTILES: Final = Symmetry(
    name="location",
    text="a location larger by 1 gives quantiles larger by 1",
    inputs=lambda x: {**x, "loc": x.real("loc") + 1.0},
    outputs=lambda out: {"quantiles": out.array("quantiles") + 1.0},
    tolerance=Tolerance(
        abs=1e-9,
        rel=4.5e-16,
        reason="loc + 1 and the sum round within an ulp of the larger of loc and the "
        "quantile, below 1e-9 within the test bound of a million",
    ),
)
_RETURN_PERIOD_CONVENTION: Final = (
    "the quantile of the return period T at the annual exceedance probability 1/T, "
    "the non-exceedance 1 - 1/T (Polish Q_p% with p = 100/T %, KZGW 2017 eq. 3.7; "
    "WMO-No. 168 sect. 5.6.1), computed as the inverse survival function at 1/T, "
    "which keeps its digits for long return periods"
)
_PERIODS_TRAP: Final = (
    "range case return_periods_years-physical_low_inside: T just above 1 puts the "
    "non-exceedance probability at 2.2e-16, the far lower tail, finite"
)


def _decimal_quantiles(
    run: Callable[..., Values],
    exact: Callable[[Decimal, Decimal], Decimal],
    shapes: tuple[float, ...],
    what: str,
) -> None:
    """Compare the quantiles with a closed form evaluated in decimal arithmetic."""
    periods = [1.0001, 1.5, 2.0, 10.0, 100.0, 1000.0, 1.0e6]
    for shape in shapes:
        out = run(shape=shape, loc=10.0, scale=2.0, return_periods_years=periods)
        with localcontext(prec=50):
            wanted = [
                float(10 + 2 * exact(Decimal(shape), Decimal(period)))
                for period in periods
            ]
        assert_within(
            out.array("quantiles"),
            wanted,
            rel=1e-13,
            abs=1e-12,
            reason=f"{what} at 50 digits; scipy's inverse survival function keeps "
            "about 14 significant digits, and near the median the quantile is near "
            "loc",
        )


def _gev_reduced(shape: Decimal, period: Decimal) -> Decimal:
    """(1 - y^c) / c with y = -ln(1 - 1/T), or -ln y at c = 0, at 50 digits."""
    reduced = -(1 - 1 / period).ln()
    if shape == 0:
        return -reduced.ln()
    return (1 - (shape * reduced.ln()).exp()) / shape


def _gev_closed_form(run: Callable[..., Values]) -> None:
    _decimal_quantiles(
        run, _gev_reduced, (-0.5, -0.1, 0.0, 0.1, 0.5), "the GEV quantile function"
    )


GEV_QUANTILES: Final = FormulaSpec(
    name="gev_quantiles",
    title="Quantiles of the generalized extreme value (GEV) distribution for return "
    "periods",
    function="hydrolog.statistics.frequency.gev_quantiles",
    family="statistic",
    equation=(
        "Q_T = loc + scale (1 - y**c) / c with y = -ln(1 - 1/T); Q_T = loc - scale "
        "ln y for c = 0 (Gumbel); c is scipy's genextreme shape, k of Hosking, -xi "
        "of Coles"
    ),
    latex=(
        r"Q_T = \xi + \alpha\,\frac{1 - y^{c}}{c},\quad y = -\ln\left(1 - "
        r"\frac{1}{T}\right);\qquad Q_T = \xi - \alpha \ln y \ \ (c = 0)"
    ),
    variables=(
        _parameter(
            "shape",
            "c",
            "Shape c: an upper bound for c > 0, a heavy upper tail for c < 0.",
            Range(
                test_low=-1.0,
                test_high=50.0,
                test_reason="the shapes of Hydrolog's estimators: above -1 by the "
                "L-moments (where the GEV has a mean), at most 50, the end of the "
                "brackets of the L-moment and moment solvers",
            ),
            (-0.6, 0.0),
            unit="-",
        ),
        _parameter("loc", r"\xi", "Location.", _ANY_VALUE, (2.0, 22.2)),
        _parameter("scale", r"\alpha", "Scale.", _SCALE_RANGE, (1.0, 19.5)),
        _RETURN_PERIODS,
    ),
    outputs=(_quantiles_output("The flows of the return periods."),),
    sources=(
        Source(
            citation=_WMO_168,
            locator="table II.5.2, p. II.5-5 (the GEV of Stedinger et al. 1993, F(x) = "
            "exp{-[1 - kappa (x - xi) / alpha]^(1/kappa)}); sect. 5.6.1, p. II.5-14",
            url=_WMO_168_URL,
        ),
        Source(
            citation=_WMO_1029,
            locator="sect. 7.5, eq. 7.5, p. 62 (the same GEV, kappa > 0 bounded above)",
            url=_WMO_1029_URL,
        ),
        _SCIPY_STATS,
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"return_periods_years": 1, "loc": 1},
        scalings=(_SCALED_QUANTILES,),
        symmetries=(_SHIFTED_QUANTILES,),
        limits=(
            Limit(
                name="closed_form",
                text="the quantile function of the GEV and, at c = 0, of the Gumbel "
                "distribution, in decimal arithmetic at 50 digits",
                check=_gev_closed_form,
            ),
        ),
    ),
    validation="none: the quantile function of the distribution",
    formula_version=1,
    status="referenced",
    conventions=(
        "the shape c of scipy's genextreme, equal to k of Hosking and kappa of "
        "WMO-No. 168 and WMO-No. 1029, and to -xi of Coles (2001): c > 0 has the "
        "upper bound loc + scale/c, c < 0 a heavy upper tail",
        _RETURN_PERIOD_CONVENTION,
        "loc and scale in the unit of the sample; the formula is homogeneous",
    ),
    traps={
        "singular_at_bound": _PERIODS_TRAP,
        "exp_overflow": "range cases shape-physical_low_test_bound and "
        "shape-physical_high_test_bound with the far tails: y**c of c = 50 at T "
        "just above 1 and of c = -1 at a million years stay finite",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the quantile function in decimal arithmetic at 50 digits",
            test="tests/unit/test_formulas_flood_frequency.py (limit closed_form)",
        ),
        Oracle(
            kind="frozen",
            description="lmom 3.3 quagev at the parameters of pelgev on seven samples, "
            "R 4.5.3, 2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "quagev takes Hosking's (xi, alpha, k), scipy's (loc, scale, c)",
                "the quantile at the non-exceedance 1 - 1/T on both sides",
            ),
        ),
    ),
)


def gev_quantiles(
    shape: float,
    loc: float,
    scale: float,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> NDArray[np.float64]:
    """Return the GEV quantiles of return periods, spec gev_quantiles.

    Parameters
    ----------
    shape, loc, scale : float
        The parameters of the distribution.
    return_periods_years : array_like of float
        Return periods [years].

    Returns
    -------
    numpy.ndarray
        The quantile of each return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        GEV_QUANTILES,
        shape=shape,
        loc=loc,
        scale=scale,
        return_periods_years=return_periods_years,
    )
    quantiles = _isf("gev", x.real("shape"), x)
    return checked_outputs(GEV_QUANTILES, {"quantiles": quantiles}).array("quantiles")


def _normal_quantile(period: float) -> float:
    """Return the standard normal quantile of the exceedance 1/T (Python's own).

    From the tail probability 1/T, which keeps its digits for long return periods
    where 1 - 1/T does not: the normal distribution is symmetric.
    """
    return -NormalDist().inv_cdf(1.0 / period)


def _log_normal_closed_form(run: Callable[..., Values]) -> None:
    periods = [1.0001, 1.5, 2.0, 10.0, 100.0, 1000.0, 1.0e6]
    for shape in (0.2, 0.75, 1.5):
        out = run(shape=shape, loc=0.384, scale=2.0, return_periods_years=periods)
        assert_within(
            out.array("quantiles"),
            [0.384 + 2.0 * math.exp(shape * _normal_quantile(t)) for t in periods],
            rel=1e-12,
            reason="loc + scale exp(s z) with z from Python's statistics.NormalDist "
            "(Wichura's algorithm AS241, another than scipy's ndtri); both keep "
            "about 15 digits of z, s z multiplies its error",
        )


LOG_NORMAL_QUANTILES: Final = FormulaSpec(
    name="log_normal_quantiles",
    title="Quantiles of the log-normal distribution for return periods",
    function="hydrolog.statistics.frequency.log_normal_quantiles",
    family="statistic",
    equation=(
        "Q_T = loc + scale exp(s z) with z the standard normal quantile of the "
        "non-exceedance 1 - 1/T; loc = 0 is the two-parameter distribution"
    ),
    latex=(
        r"Q_T = \epsilon + e^{\mu} \exp\left(\sigma\,\Phi^{-1}\left(1 - "
        r"\frac{1}{T}\right)\right)"
    ),
    variables=(
        _parameter(
            "shape",
            r"\sigma",
            "Standard deviation of the logarithms of x - loc.",
            Range(
                low=0.0,
                low_inclusive=False,
                test_high=5.0,
                test_reason="a shape of 5 spreads the quantiles of T from just above "
                "1 to a million years over a factor of 10**15; the fits of annual "
                "maxima stay below 1",
            ),
            (0.6, 0.9),
            unit="-",
        ),
        _parameter(
            "loc",
            r"\epsilon",
            "Lower bound: 0 for the two-parameter distribution of Hydrolog's fits.",
            _ANY_VALUE,
            (0.0, 0.4),
        ),
        _parameter(
            "scale",
            r"e^{\mu}",
            "exp of the mean of the logarithms.",
            _SCALE_RANGE,
            (2.4, 27.0),
        ),
        _RETURN_PERIODS,
    ),
    outputs=(_quantiles_output("The flows of the return periods."),),
    sources=(
        Source(
            citation=_KZGW,
            locator="eqs. 3.35 and 3.40, p. 46 (Q_p = epsilon + exp(mu + sigma u_p)); "
            "example 3.3, table 3.12, p. 51",
            url=_KZGW_URL,
        ),
        Source(
            citation=_WMO_168,
            locator="table II.5.2, p. II.5-5 and its note a (the three-parameter "
            "log-normal with Y = ln(X - xi))",
            url=_WMO_168_URL,
        ),
        _SCIPY_STATS,
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"return_periods_years": 1, "loc": 1, "scale": 1},
        scalings=(_SCALED_QUANTILES,),
        symmetries=(_SHIFTED_QUANTILES,),
        limits=(
            Limit(
                name="closed_form",
                text="loc + scale exp(s z) with an independent normal quantile",
                check=_log_normal_closed_form,
            ),
        ),
    ),
    validation="none: the quantile function of the distribution",
    formula_version=1,
    status="referenced",
    conventions=(
        "scipy's lognorm(s, loc, scale): s = sigma, loc = epsilon (the lower bound "
        "of KZGW 2017 eq. 3.35), scale = exp(mu)",
        _RETURN_PERIOD_CONVENTION,
        "loc and scale in the unit of the sample; the formula is homogeneous",
    ),
    traps={
        "singular_at_bound": _PERIODS_TRAP,
        "exp_overflow": "range case shape-physical_high_test_bound: exp(5 z) at a "
        "million years is 2e10, finite",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="loc + scale exp(s z) with z from Python's "
            "statistics.NormalDist",
            test="tests/unit/test_formulas_flood_frequency.py (limit closed_form)",
        ),
        Oracle(
            kind="frozen",
            description="lmom 3.3 qualn3 at the parameters of pelln3 with bound 0 on "
            "seven samples, R 4.5.3, 2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "qualn3 takes (zeta, mu, sigma): loc = zeta, scale = exp(mu), shape = "
                "sigma",
            ),
        ),
    ),
)


def log_normal_quantiles(
    shape: float,
    loc: float,
    scale: float,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> NDArray[np.float64]:
    """Return the log-normal quantiles of return periods, spec log_normal_quantiles.

    Parameters
    ----------
    shape, loc, scale : float
        The parameters of the distribution.
    return_periods_years : array_like of float
        Return periods [years].

    Returns
    -------
    numpy.ndarray
        The quantile of each return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        LOG_NORMAL_QUANTILES,
        shape=shape,
        loc=loc,
        scale=scale,
        return_periods_years=return_periods_years,
    )
    quantiles = _isf("log_normal", x.real("shape"), x)
    return checked_outputs(LOG_NORMAL_QUANTILES, {"quantiles": quantiles}).array(
        "quantiles"
    )


def _normal_limit(run: Callable[..., Values]) -> None:
    periods = [1.0001, 2.0, 10.0, 100.0, 1.0e6]
    out = run(skew=0.0, loc=10.0, scale=2.0, return_periods_years=periods)
    assert_within(
        out.array("quantiles"),
        [10.0 + 2.0 * _normal_quantile(t) for t in periods],
        rel=5e-12,
        reason="Pearson III of skewness 0 is the normal distribution; z from Python's "
        "statistics.NormalDist of the tail 1/T, another algorithm than scipy's, which "
        "takes the normal quantile of 1 - 1/T and keeps about 11 digits of the tail "
        "probability at a million years",
    )


PEARSON3_QUANTILES: Final = FormulaSpec(
    name="pearson3_quantiles",
    title="Quantiles of the Pearson type III distribution for return periods",
    function="hydrolog.statistics.frequency.pearson3_quantiles",
    family="statistic",
    equation=(
        "Q_T = loc + K(skew, T) scale, K the frequency factor: the standardised "
        "Pearson III quantile of the non-exceedance 1 - 1/T (a gamma of shape 4 / "
        "skew**2 shifted and scaled to the mean 0 and standard deviation 1)"
    ),
    latex=r"Q_T = \mu + K_{\gamma}\!\left(1 - \frac{1}{T}\right)\sigma",
    variables=(
        _parameter(
            "skew",
            r"\gamma",
            "Skewness of the distribution.",
            Range(
                test_low=-9.0,
                test_high=9.0,
                test_reason="Bulletin 17B appendix 3 tabulates the frequency factor "
                "for skews of -9 to 9",
            ),
            (1.3, 2.7),
            unit="-",
        ),
        _parameter("loc", r"\mu", "Mean of the distribution.", _ANY_VALUE, (3.0, 35.4)),
        _parameter(
            "scale",
            r"\sigma",
            "Standard deviation of the distribution.",
            _SCALE_RANGE,
            (2.0, 29.6),
        ),
        _RETURN_PERIODS,
    ),
    outputs=(_quantiles_output("The flows of the return periods."),),
    sources=(
        Source(
            citation=_B17B,
            locator="eq. 1, p. 9 (log Q = X + K S) and appendix 3, pp. 3-1 to 3-10 "
            "(the frequency factors K of Harter 1969 for skews of -9 to 9)",
            url=_B17B_URL,
        ),
        Source(
            citation=_KZGW,
            locator="eqs. 3.1 and 3.3, p. 28 (Q_p = epsilon + the gamma quantile of "
            "1 - p with lambda and 1/alpha); example 3.2, table 3.9, p. 44",
            url=_KZGW_URL,
        ),
        _SCIPY_STATS,
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"return_periods_years": 1, "loc": 1},
        scalings=(_SCALED_QUANTILES,),
        symmetries=(_SHIFTED_QUANTILES,),
        limits=(
            Limit(
                name="normal",
                text="the skewness 0 gives the normal distribution",
                check=_normal_limit,
            ),
        ),
    ),
    validation="none: the quantile function of the distribution",
    formula_version=1,
    status="referenced",
    conventions=(
        "scipy's pearson3(skew, loc, scale) is parameterised by the mean, standard "
        "deviation and skewness, as Bulletin 17B and lmom's PE3 (mu, sigma, gamma); "
        "KZGW 2017's (epsilon, alpha, lambda) give skew = 2 / sqrt(lambda), loc = "
        "epsilon + lambda / alpha and scale = sqrt(lambda) / alpha",
        "a positive skewness has the lower bound loc - 2 scale / skew, a negative one "
        "the upper bound loc - 2 scale / skew",
        _RETURN_PERIOD_CONVENTION,
        "loc and scale in the unit of the sample; the formula is homogeneous",
    ),
    traps={
        "singular_at_bound": _PERIODS_TRAP,
        "exp_overflow": "range cases skew-physical_low_test_bound and "
        "skew-physical_high_test_bound: a gamma shape of 4/81 in both tails stays "
        "finite",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="frozen",
            description="lmom 3.3 quape3 at the parameters of pelpe3 on seven samples, "
            "R 4.5.3, 2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "quape3 takes (mu, sigma, gamma), scipy's (loc, scale, skew)",
            ),
        ),
        Oracle(
            kind="algorithm",
            description="the normal quantile of Python's statistics.NormalDist at the "
            "skewness 0",
            test="tests/unit/test_formulas_flood_frequency.py (limit normal)",
        ),
    ),
)


def pearson3_quantiles(
    skew: float,
    loc: float,
    scale: float,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> NDArray[np.float64]:
    """Return the Pearson III quantiles of return periods, spec pearson3_quantiles.

    Parameters
    ----------
    skew, loc, scale : float
        The parameters of the distribution: skewness, mean and standard deviation.
    return_periods_years : array_like of float
        Return periods [years].

    Returns
    -------
    numpy.ndarray
        The quantile of each return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        PEARSON3_QUANTILES,
        skew=skew,
        loc=loc,
        scale=scale,
        return_periods_years=return_periods_years,
    )
    quantiles = _isf("pearson3", x.real("skew"), x)
    return checked_outputs(PEARSON3_QUANTILES, {"quantiles": quantiles}).array(
        "quantiles"
    )


def _weibull_reduced(shape: Decimal, period: Decimal) -> Decimal:
    """(ln T)^(1/k) at 50 digits: -ln(1 - F) is ln T at F = 1 - 1/T."""
    return (period.ln().ln() / shape).exp()


def _weibull_closed_form(run: Callable[..., Values]) -> None:
    _decimal_quantiles(
        run, _weibull_reduced, (0.5, 0.947, 1.0, 2.0, 10.0), "loc + scale (ln T)^(1/k)"
    )


_LOG_LARGEST: Final = math.log(float(np.finfo(np.float64).max))
"""The natural logarithm of the largest float64, about 709.78."""


def _finite_weibull(x: Values) -> bool:
    """Whether scale (ln T)^(1/k) stays a float64 for every return period."""
    with np.errstate(divide="ignore", over="ignore"):
        exponents = np.log(np.log(x.array("return_periods_years"))) / x.real("shape")
    return bool(np.all(math.log(x.real("scale")) + exponents < _LOG_LARGEST - 1.0))


WEIBULL_QUANTILES: Final = FormulaSpec(
    name="weibull_quantiles",
    title="Quantiles of the three-parameter Weibull distribution for return periods",
    function="hydrolog.statistics.frequency.weibull_quantiles",
    family="statistic",
    equation=(
        "Q_T = loc + scale (ln T)**(1/k): F(x) = 1 - exp(-((x - loc) / scale)**k) "
        "= 1 - 1/T"
    ),
    latex=r"Q_T = \epsilon + \frac{1}{\alpha_W}\left(\ln T\right)^{1/\beta_W}",
    variables=(
        _parameter(
            "shape",
            r"\beta_W",
            "Shape k of the distribution.",
            Range(
                low=0.0,
                low_inclusive=False,
                test_high=50.0,
                test_reason="shapes above 50 put the quantile of every T up to a "
                "million years within 6 % of loc + scale ((ln 10**6)**(1/50) = 1.054)",
            ),
            (0.7, 1.4),
            unit="-",
        ),
        _parameter("loc", r"\epsilon", "Lower bound.", _ANY_VALUE, (-1.0, 4.9)),
        _parameter("scale", r"1/\alpha_W", "Scale.", _SCALE_RANGE, (1.5, 37.0)),
        _RETURN_PERIODS,
    ),
    outputs=(_quantiles_output("The flows of the return periods."),),
    constraints=(
        Constraint(
            name="finite_quantiles",
            cls="precondition",
            check=_finite_weibull,
            text="ln(scale) + ln(ln T) / k < 708.78 for every T: scale (ln T)**(1/k) "
            "below e**-1 of the largest float64",
            source=Source(
                citation="Harris, C.R. et al. (2020). Array programming with NumPy. "
                "Nature 585, 357-362",
                locator="numpy.finfo(numpy.float64).max, about 1.8e308, the largest "
                "IEEE 754 binary64 number",
                url="https://numpy.org/doc/stable/reference/generated/numpy.finfo.html",
            ),
            satisfied={"shape": 1.0},
            violated={"shape": 0.001},
        ),
    ),
    sources=(
        Source(
            citation=_KZGW,
            locator="eqs. 3.52 and 3.55, pp. 53-54 (P(Q >= x) = exp(-[alpha_W (x - "
            "epsilon)]^beta_W)); example 3.4, table 3.15, p. 60",
            url=_KZGW_URL,
        ),
        Source(
            citation=_WMO_1029,
            locator="sect. 7.5, eq. 7.6, p. 62 (F(x) = 1 - exp[-((x - xi) / "
            "alpha)^kappa]) and eq. 7.13, p. 64",
            url=_WMO_1029_URL,
        ),
        _SCIPY_STATS,
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"return_periods_years": 1, "loc": 1, "scale": 1},
        scalings=(_SCALED_QUANTILES,),
        symmetries=(_SHIFTED_QUANTILES,),
        limits=(
            Limit(
                name="closed_form",
                text="loc + scale (ln T)^(1/k) in decimal arithmetic at 50 digits",
                check=_weibull_closed_form,
            ),
        ),
    ),
    validation="none: the quantile function of the distribution",
    formula_version=1,
    status="referenced",
    conventions=(
        "scipy's weibull_min(k, loc, scale), the lower-bounded Weibull fitted to "
        "maxima as KZGW 2017 eq. 3.52 (epsilon = loc, alpha_W = 1/scale, beta_W = "
        "k) and lmom's (zeta, beta, delta)",
        _RETURN_PERIOD_CONVENTION,
        "loc and scale in the unit of the sample; the formula is homogeneous",
    ),
    traps={
        "singular_at_bound": _PERIODS_TRAP,
        "exp_overflow": "constraint case finite_quantiles-violated: a shape of 0.001 "
        "would raise (ln T)**(1/k) beyond the float64 numbers at T = 5,000 years; it "
        "is refused before the computation",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="loc + scale (ln T)^(1/k) in decimal arithmetic at 50 digits",
            test="tests/unit/test_formulas_flood_frequency.py (limit closed_form)",
        ),
        Oracle(
            kind="frozen",
            description="lmom 3.3 quawei at the parameters of pelwei on seven samples, "
            "R 4.5.3, 2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "quawei takes (zeta, beta, delta): loc, scale and the shape k",
            ),
        ),
    ),
)


def weibull_quantiles(
    shape: float,
    loc: float,
    scale: float,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> NDArray[np.float64]:
    """Return the Weibull quantiles of return periods, spec weibull_quantiles.

    Parameters
    ----------
    shape, loc, scale : float
        The parameters of the distribution.
    return_periods_years : array_like of float
        Return periods [years].

    Returns
    -------
    numpy.ndarray
        The quantile of each return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        WEIBULL_QUANTILES,
        shape=shape,
        loc=loc,
        scale=scale,
        return_periods_years=return_periods_years,
    )
    quantiles = _isf("weibull", x.real("shape"), x)
    return checked_outputs(WEIBULL_QUANTILES, {"quantiles": quantiles}).array(
        "quantiles"
    )


# --- estimators of the parameters ---------------------------------------------------


class FittedParameters(NamedTuple):
    """Parameters of a distribution fitted to a sample (the specs ``fit_*``).

    Those of :mod:`scipy.stats`: ``lognorm`` (location 0), ``genextreme``,
    ``pearson3`` (whose shape is the skewness) or ``weibull_min``.
    """

    shape: float
    loc: float
    scale: float


class _Search(NamedTuple):
    """The end of a search for the parameters ``(shape, loc, scale)`` of a sample.

    ``failure`` is ``""`` with parameters, else ``"unbounded_likelihood"`` (the search
    of the likelihood ends at an end of the shapes of :func:`_limit_distance`, or at
    a vanishing scale) or ``"not_converged"`` (no run settles, or it ends worse than
    it started).
    """

    parameters: tuple[float, float, float] | None
    failure: str


def _shape(
    statistic: Callable[[float], float], value: float, bracket: tuple[float, float]
) -> float:
    """Return the shape in ``bracket`` whose ``statistic`` (decreasing) is ``value``.

    A value at or beyond the statistic of an end of the bracket gives that end: the
    L-skewness of values all equal but one lies within rounding of 1 or -1, beyond
    the shapes the bracket holds, where ``brentq`` finds no change of sign.
    """
    low, high = bracket
    if value >= statistic(low):
        return low
    if value <= statistic(high):
        return high
    return float(brentq(lambda shape: statistic(shape) - value, low, high))


def _gev_skewness(c: float) -> float:
    """Skewness of the GEV with shape ``c``."""
    with np.errstate(all="ignore"):  # scipy computes the kurtosis too; it overflows
        return float(genextreme.stats(c, moments="s"))


def _gev_from_moments(
    mean: float, std: float, skewness: float, bracket: tuple[float, float]
) -> tuple[float, float, float]:
    """GEV ``(c, loc, scale)`` with the given mean, standard deviation and skewness."""
    c = _shape(_gev_skewness, skewness, bracket)
    with np.errstate(all="ignore"):
        mean_1, variance_1 = genextreme.stats(c, moments="mv")
    scale = std / float(np.sqrt(variance_1))
    return c, mean - scale * float(mean_1), scale


def _gev_l_skewness(c: float) -> float:
    """L-skewness τ3 = 2 (1 - 3^-c) / (1 - 2^-c) - 3 of the GEV with shape ``c``."""
    if c == 0.0:
        return _GUMBEL_L_SKEWNESS
    return float(2.0 * np.expm1(-c * np.log(3.0)) / np.expm1(-c * np.log(2.0)) - 3.0)


def _gev_from_l_moments(
    l1: float, l2: float, t3: float, bracket: tuple[float, float]
) -> tuple[float, float, float]:
    """GEV ``(c, loc, scale)`` with the given L-moments (Hosking and Wallis 1997).

    The shape c solves τ3 = 2 (1 - 3^-c) / (1 - 2^-c) - 3; then
    α = λ2 c / ((1 - 2^-c) Γ(1 + c)) and ξ = λ1 - α (1 - Γ(1 + c)) / c, with the
    limits α = λ2 / ln 2 and ξ = λ1 - γ α (Euler's γ) of the Gumbel distribution
    (c = 0).
    """
    c = _shape(_gev_l_skewness, t3, bracket)
    if abs(c) < _GUMBEL_SHAPE:
        scale = l2 / float(np.log(2.0))
        return c, l1 - float(np.euler_gamma) * scale, scale
    gamma_1 = float(gamma(1.0 + c))
    scale = l2 * c / (-float(np.expm1(-c * np.log(2.0))) * gamma_1)
    return c, l1 - scale * (1.0 - gamma_1) / c, scale


def _pearson3_from_l_moments(
    l1: float, l2: float, t3: float
) -> tuple[float, float, float]:
    """Pearson III ``(skew, loc, scale)`` with the given L-moments.

    Hosking and Wallis (1997): α = 4 / γ² from |τ3| by their rational approximations
    (:data:`_PE3_APPROXIMATION`), then γ = 2 sign(τ3) / √α,
    σ = λ2 √(π α) Γ(α) / Γ(α + 1/2) and μ = λ1; at a small |τ3| the normal
    distribution, σ = λ2 √π.
    """
    a = _PE3
    t = abs(t3)
    if t < a["normal_below"]:
        return 0.0, l1, l2 * float(np.sqrt(np.pi))
    if t >= 1.0 / 3.0:
        z = 1.0 - t
        alpha = (z * (a["b1"] + z * (a["b2"] + z * a["b3"]))) / (
            1.0 + z * (a["b4"] + z * (a["b5"] + z * a["b6"]))
        )
    else:
        z = 3.0 * np.pi * t * t
        alpha = (1.0 + a["a1"] * z) / (z * (1.0 + z * (a["a2"] + z * a["a3"])))
    ratio = float(np.exp(gammaln(alpha) - gammaln(alpha + 0.5)))
    scale = l2 * float(np.sqrt(np.pi * alpha)) * ratio
    return float(np.copysign(2.0 / np.sqrt(alpha), t3)), l1, scale


def _weibull_from_reversed_gev(
    c: float, loc: float, scale: float
) -> tuple[float, float, float]:
    """Weibull ``(shape, loc, scale)`` of X when -X is GEV ``(c, loc, scale)``, c > 0.

    -X then has the upper bound loc + scale / c, so X has the lower bound
    -loc - scale / c, the shape 1 / c and the scale scale / c.
    """
    return 1.0 / c, -loc - scale / c, scale / c


def _within_moments(name: str, data: NDArray[np.float64]) -> bool:
    """Whether the sample skewness lies inside the skewnesses ``name`` can take.

    Only the Weibull distribution has a limit: the skewness of the reversed Gumbel
    distribution, which its skewness approaches as its shape grows.
    """
    return name != "weibull" or _moments(data).skewness > -_GUMBEL_SKEWNESS


def _within_l_moments(name: str, data: NDArray[np.float64]) -> bool:
    """Whether the sample L-moments lie inside those ``name`` can take.

    The log-normal of location 0 has λ2 / λ1 = erf(s / 2) below 1; the GEV and
    Pearson III have |τ3| below 1, the Weibull distribution τ3 above that of the
    reversed Gumbel distribution.
    """
    l1, l2, t3 = _l_moments(data)
    if name == "log_normal":
        return l2 < l1
    lowest = -_GUMBEL_L_SKEWNESS if name == "weibull" else -1.0
    return lowest < t3 < 1.0


def _by_moments(name: str, data: NDArray[np.float64]) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name`` by moments.

    The sample meets the preconditions of :data:`FIT_MOMENTS`.
    """
    mean, std, skewness = _moments(data)
    if name == "log_normal":
        # mean = scale exp(s²/2) and Cv² = exp(s²) - 1
        cv2 = (std / mean) ** 2
        return float(np.sqrt(np.log1p(cv2))), 0.0, mean / float(np.sqrt(1.0 + cv2))
    if name == "pearson3":
        return skewness, mean, std  # scipy's parameters are these moments
    if name == "gev":
        return _gev_from_moments(mean, std, skewness, _GEV_SHAPES_BY_SKEWNESS)
    reversed_gev = _gev_from_moments(-mean, std, -skewness, _WEIBULL_SHAPES)
    return _weibull_from_reversed_gev(*reversed_gev)


def _by_l_moments(name: str, data: NDArray[np.float64]) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name`` by L-moments.

    The sample meets the preconditions of :data:`FIT_L_MOMENTS`.
    """
    l1, l2, t3 = _l_moments(data)
    if name == "log_normal":
        # λ1 = scale exp(s²/2) and λ2 = λ1 erf(s/2)
        shape = 2.0 * float(erfinv(l2 / l1))
        return shape, 0.0, l1 * float(np.exp(-0.5 * shape**2))
    if name == "weibull":
        reversed_gev = _gev_from_l_moments(-l1, l2, -t3, _WEIBULL_SHAPES)
        return _weibull_from_reversed_gev(*reversed_gev)
    if name == "gev":
        return _gev_from_l_moments(l1, l2, t3, _GEV_SHAPES_BY_L_SKEWNESS)
    return _pearson3_from_l_moments(l1, l2, t3)


def _settle(
    objective: Callable[[NDArray[np.float64]], float],
    start: NDArray[np.float64],
    step: float | None = None,
    stop: Callable[[NDArray[np.float64]], bool] | None = None,
) -> tuple[Any, bool]:
    """Minimise ``objective`` by Nelder-Mead from ``start`` until a run gains nothing.

    Each run starts where the last ended; the search settles when a run gains no
    more than ``_SEARCH_GAIN``, within ``_SEARCH_RUNS`` runs after the first, or ends
    where ``stop`` holds (a limit where no run would settle). scipy's first simplex
    moves each coordinate by 5 % of itself; with ``step`` by at least ``step``, so
    that a coordinate that starts near 0 (the location of a standardised sample) is
    searched too. Returns the best end (scipy's ``OptimizeResult``) and whether it
    settled.
    """

    def run(point: NDArray[np.float64]) -> Any:
        options: dict[str, object] = dict(_NELDER_MEAD)
        if step is not None:
            moves = np.maximum(0.05 * np.abs(point), step)
            options["initial_simplex"] = np.vstack([point, point + np.diag(moves)])
        return minimize(objective, point, method="Nelder-Mead", options=options)

    found = run(start)
    for _ in range(_SEARCH_RUNS):
        if not np.isfinite(found.fun):
            break
        if stop is not None and stop(found.x):
            return found, True
        again = run(found.x)
        gain = found.fun - again.fun
        if gain > 0.0:
            found = again
        if gain <= _SEARCH_GAIN:
            return found, True
    return found, False


def _standardised(
    data: NDArray[np.float64], centred: bool = True
) -> tuple[NDArray[np.float64], float, float, int]:
    """Return the sample standardised, with its centre, spread and binary exponent.

    The sample is divided by the power of two of :func:`_normalised` (exactly, so
    that its unit changes no digit of the search), then centred on its mean unless
    ``centred`` is false and divided by its standard deviation (divisor n): z = (x /
    2**e - centre) / spread. A location and a scale of z give those of x as
    2**e (centre + spread loc) and 2**e spread scale.
    """
    scaled, exponent = _normalised(data)
    centre = float(np.mean(scaled)) if centred else 0.0
    spread = float(np.std(scaled))
    return (scaled - centre) / spread, centre, spread, exponent


def _support(name: str, shape: float, scale: float) -> tuple[float, float]:
    """Lower and upper bound of distribution ``name`` with location 0 (infinite: none).

    The GEV with scipy's c > 0 has the upper bound scale / c and with c < 0 the lower
    one; Pearson III with the skewness γ > 0 has the lower bound -2 scale / γ and with
    γ < 0 the upper one; Weibull has the lower bound 0.
    """
    if name == "weibull":
        return 0.0, np.inf
    if shape == 0.0:
        return -np.inf, np.inf
    if name == "gev":
        bound = scale / shape
        return (-np.inf, bound) if shape > 0.0 else (bound, np.inf)
    bound = -2.0 * scale / shape
    return (bound, np.inf) if shape > 0.0 else (-np.inf, bound)


def _limit_distance(name: str, shape: float) -> float:
    """How far ``shape`` lies inside the shapes the likelihood is searched over.

    Positive inside them, 0 or less at or beyond an end: the GEV's -1 < c < 1,
    Pearson III's |skewness| < 2 and the Weibull distribution's 1 < shape <
    ``_ML_WEIBULL_SHAPE``.
    """
    if name == "gev":
        return 1.0 - abs(shape)
    if name == "pearson3":
        return 2.0 - abs(shape)
    return min(shape - 1.0, _ML_WEIBULL_SHAPE - shape)


def _ml_start(name: str, sample: NDArray[np.float64]) -> tuple[float, float, float]:
    """Start ``(shape, loc, scale)`` of the maximum-likelihood search on ``sample``.

    ``sample`` is standardised (mean 0, standard deviation 1). The start is the
    L-moments' estimate, else the moments', else the distribution of skewness 0, with
    its shape moved ``_ML_INSIDE`` short of the limit if it is closer and its location
    moved, if needed, so that a bound of the support lies ``_ML_MARGIN`` beyond the
    sample: a value without density leaves no likelihood to improve.
    """
    if _within_l_moments(name, sample):
        shape, loc, scale = _by_l_moments(name, sample)
    elif _within_moments(name, sample):
        shape, loc, scale = _by_moments(name, sample)
    else:  # only Weibull: a sample skewness below that of every Weibull distribution
        shape, loc, scale = _weibull_from_reversed_gev(
            *_gev_from_moments(0.0, 1.0, 0.0, _GEV_SHAPES_BY_SKEWNESS)
        )
    if name == "gev":
        shape = min(max(shape, _ML_INSIDE - 1.0), 1.0 - _ML_INSIDE)
    elif name == "pearson3":
        shape = min(max(shape, _ML_INSIDE - 2.0), 2.0 - _ML_INSIDE)
    else:
        shape = min(max(shape, 1.0 + _ML_INSIDE), _ML_WEIBULL_SHAPE - _ML_INSIDE)
    lower, upper = _support(name, shape, scale)
    lowest = float(sample.max()) - upper + _ML_MARGIN
    highest = float(sample.min()) - lower - _ML_MARGIN
    return shape, min(max(loc, lowest), highest), scale


@lru_cache(maxsize=64)
def _likelihood_search(name: str, sample: bytes) -> _Search:
    """Run the search of :func:`_maximum_likelihood` on a float64 sample's bytes."""
    data = np.frombuffer(sample, dtype=np.float64)
    distribution = _DISTRIBUTIONS[name]
    if name == "gev" and 2 * np.count_nonzero(data == data.min()) > data.size:
        # k values tied at the smallest and m others: as the scale falls to 0 the
        # log-likelihood grows as (k - m / xi) ln(1 / scale), without limit for the
        # xi of m / k to 1 that the search covers, so for k > m
        return _Search(None, "unbounded_likelihood")
    standard, centre, spread, exponent = _standardised(data)

    def minus_log_likelihood(point: NDArray[np.float64]) -> float:
        if _limit_distance(name, point[0]) <= 0.0 or point[2] < _ML_LEAST_LOG_SCALE:
            return np.inf
        with np.errstate(all="ignore"):
            log_densities = distribution.logpdf(
                standard, point[0], loc=point[1], scale=np.exp(point[2])
            )
            total = -float(np.sum(log_densities))
        return np.inf if np.isnan(total) else total

    shape, loc, scale = _ml_start(name, standard)
    start = np.array([shape, loc, np.log(scale)])

    def at_a_limit(point: NDArray[np.float64]) -> bool:
        return bool(
            _limit_distance(name, point[0]) < _ML_EDGE
            or point[2] < _ML_LEAST_LOG_SCALE + _ML_EDGE
        )

    found, settled = _settle(minus_log_likelihood, start, stop=at_a_limit)
    shape = float(found.x[0])
    if at_a_limit(found.x):
        return _Search(None, "unbounded_likelihood")
    if not settled or found.fun > minus_log_likelihood(start):
        return _Search(None, "not_converged")
    loc = math.ldexp(centre + spread * float(found.x[1]), exponent)
    return _Search(
        (shape, loc, math.ldexp(spread * float(np.exp(found.x[2])), exponent)), ""
    )


def _maximum_likelihood(name: str, data: NDArray[np.float64]) -> _Search:
    """Maximum-likelihood ``(shape, loc, scale)`` of a three-parameter distribution.

    ``name`` is ``"gev"``, ``"pearson3"`` or ``"weibull"``; the sample has more values
    than the distribution has parameters, not all equal. The search runs on the
    standardised sample (:func:`_standardised`), whose scale is of the order of 1 in
    any unit of x (scipy's own ``fit`` starts from the scale 1 and may stop far from
    the maximum on annual maxima of hundreds of m³/s): Nelder-Mead on the shape, the
    location and the logarithm of the scale from :func:`_ml_start`, over the shapes
    inside the ends of :func:`_limit_distance`, run again until a run gains nothing
    (:func:`_settle`). A search that ends at an end of the shapes or at a vanishing
    scale finds no maximum (``unbounded_likelihood``), as does a GEV with more than
    half the values tied at the smallest; one that does not settle or ends less
    likely than its start none either (``not_converged``). Cached by the sample's
    bytes: the precondition ``likelihood_has_a_maximum`` and the fit run one search.
    """
    contiguous = np.ascontiguousarray(data, dtype=np.float64)
    return _likelihood_search(name, contiguous.tobytes())


@lru_cache(maxsize=64)
def _squares_search(name: str, sample: bytes) -> _Search:
    """Run the search of :func:`_least_squares` on a float64 sample's bytes."""
    data = np.frombuffer(sample, dtype=np.float64)
    log_normal = name == "log_normal"
    standard, centre, spread, exponent = _standardised(data, centred=not log_normal)
    ascending = np.sort(standard)
    probabilities = np.arange(1, data.size + 1) / (data.size + 1)
    distribution = _DISTRIBUTIONS[name]
    positive_shape = name in ("log_normal", "weibull")

    def parameters(point: NDArray[np.float64]) -> tuple[float, float, float]:
        first = float(np.exp(point[0])) if positive_shape else float(point[0])
        if log_normal:
            return first, 0.0, float(np.exp(point[1]))
        return first, float(point[1]), float(np.exp(point[2]))

    low, high = _LS_SHAPES[name]

    def at_an_end(point: NDArray[np.float64]) -> bool:
        return bool(min(point[0] - low, high - point[0]) < _ML_EDGE)

    def squares(point: NDArray[np.float64]) -> float:
        if not low < point[0] < high:
            return np.inf
        with np.errstate(all="ignore"):
            quantiles = distribution.ppf(probabilities, *parameters(point))
            total = float(np.sum((ascending - quantiles) ** 2))
        return total if np.isfinite(total) else np.inf

    shape, loc, scale = _by_moments(name, ascending)
    first = float(np.log(shape)) if positive_shape else shape
    first = min(max(first, low + _ML_INSIDE), high - _ML_INSIDE)
    start = [first, np.log(scale)] if log_normal else [first, loc, np.log(scale)]
    found, settled = _settle(
        squares, np.array(start, dtype=np.float64), step=0.05, stop=at_an_end
    )
    if not settled or at_an_end(found.x):
        return _Search(None, "not_converged")
    shape, loc, scale = parameters(found.x)
    return _Search(
        (
            shape,
            math.ldexp(centre + spread * loc, exponent),
            math.ldexp(spread * scale, exponent),
        ),
        "",
    )


def _least_squares(name: str, data: NDArray[np.float64]) -> _Search:
    """Least-squares ``(shape, loc, scale)`` of distribution ``name``.

    They minimise Σ (x(j) - Q(j / (n + 1)))² over the ascending sample x(j), Q the
    quantile function of the distribution: the quantiles at the Weibull plotting
    positions of the empirical frequency of
    :class:`~hydrolog.statistics.FloodFrequencyAnalysis`. The search runs on the
    standardised sample (:func:`_standardised`; the log-normal, of location 0, only
    divided by its spread) from the moments' estimate: Nelder-Mead on the logarithm
    of the scale and of the log-normal and Weibull shapes, which stay positive, run
    again until a run gains nothing (:func:`_settle`), over the shapes of
    ``_LS_SHAPES``: a search that ends at one of their ends or does not settle finds
    no minimum (``not_converged``). Cached by the sample's bytes: the precondition
    ``squares_have_a_minimum`` and the fit run one search.
    """
    contiguous = np.ascontiguousarray(data, dtype=np.float64)
    return _squares_search(name, contiguous.tobytes())


def _settled(spec: FormulaSpec, search: _Search) -> tuple[float, float, float]:
    """Return the parameters a search found; ``calculation_error`` if it did not settle.

    The trap ``unbounded_iteration``: the search ran its bounded count of runs.
    """
    if search.parameters is None:
        runs = _SEARCH_RUNS + 1
        raise ERRORS.calculation(
            f"{spec.name}: the search for the parameters did not settle in {runs} "
            "runs of Nelder-Mead",
            {"reason": "not_converged", "formula": spec.name, "runs": runs},
        )
    return search.parameters


def _fitted(
    spec: FormulaSpec, parameters: tuple[float, float, float]
) -> FittedParameters:
    """Check the parameters as the outputs of ``spec`` and return them."""
    shape, loc, scale = parameters
    out = checked_outputs(spec, {"shape": shape, "loc": loc, "scale": scale})
    return FittedParameters(out.real("shape"), out.real("loc"), out.real("scale"))


# --- the specs of the estimators -------------------------------------------------

_HOSKING_WALLIS: Final = Source(
    citation="Hosking, J.R.M. and Wallis, J.R. (1997). Regional Frequency Analysis: "
    "An Approach Based on L-Moments. Cambridge University Press",
    locator="appendix A.5 (GEV), A.8 (log-normal), A.9 (Pearson type III, the "
    "rational approximations of alpha from |t3|)",
    access="author-provided",
)
_LMOM_FORTRAN: Final = Source(
    citation=_LMOM,
    locator="lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson "
    "III: alpha from |t3| by rational approximations, relative accuracy better than "
    "3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the "
    "negated L-moments",
    url=_LMOM_URL,
)
_SMITH_1985: Final = (
    "Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular "
    "cases. Biometrika 72(1), 67-90"
)
_PE3_APPROXIMATION: Final = tuple(
    Constant(name=name, value=value, unit="-", source=_LMOM_FORTRAN, symbol=symbol)
    for name, value, symbol in (
        ("a1", 0.2906, "A_1"),
        ("a2", 0.1882, "A_2"),
        ("a3", 0.0442, "A_3"),
        ("b1", 0.36067, "B_1"),
        ("b2", -0.59567, "B_2"),
        ("b3", 0.25361, "B_3"),
        ("b4", -2.78861, "C_1"),
        ("b5", 2.56096, "C_2"),
        ("b6", -0.77045, "C_3"),
        ("normal_below", 1e-6, r"\tau_{3,0}"),
    )
)
"""Hosking's rational approximations of Pearson III's alpha = 4 / G**2 from |t3|:
z = 3 pi t3**2 below |t3| = 1/3, z = 1 - |t3| above, and the |t3| below which the
distribution is the normal one (PELPE3)."""
_PE3: Final = {constant.name: float(constant.value) for constant in _PE3_APPROXIMATION}

_GUMBEL_CONSTANTS: Final = (
    Constant(
        name="gumbel_skewness",
        value=_GUMBEL_SKEWNESS,
        unit="-",
        symbol=r"\gamma_G",
        source=Source(
            citation=_WMO_168,
            locator="table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of "
            "skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3",
            url=_WMO_168_URL,
        ),
    ),
)
_GUMBEL_L_CONSTANTS: Final = (
    Constant(
        name="gumbel_l_skewness",
        value=_GUMBEL_L_SKEWNESS,
        unit="-",
        symbol=r"\tau_{3,G}",
        source=Source(
            citation=_LMOM,
            locator="pelwei: the GEV of the negated L-moments, which needs -t3 below "
            "the Gumbel's L-skewness 2 ln 3 / ln 2 - 3 = 0.1699",
            url=_LMOM_URL,
        ),
    ),
)

_DISTRIBUTION_CHOICE: Final = Variable(
    name="distribution",
    symbol="F",
    unit="-",
    kind="choice",
    description="The distribution: the log-normal of location 0, the GEV, Pearson "
    "type III or the three-parameter Weibull distribution of scipy.stats.",
    choices=tuple(_DISTRIBUTIONS),
)
_FLOODS11: Final = (
    95.0, 102.0, 110.0, 118.0, 125.0, 133.0, 140.0, 152.0, 170.0, 215.0, 290.0,
)  # fmt: skip
"""Eleven annual maxima [m3/s] of Hydrolog's tests (``floods11`` of the frozen
oracles): Pearson III and Weibull by maximum likelihood have no maximum."""
_NEGATIVE_SKEW: Final = (0.0, 9.0, 10.0, 10.0)
"""A sample whose skewness and L-skewness lie below those of every Weibull
distribution."""


def _maxima_variable() -> Variable:
    return Variable(
        name="annual_maxima",
        symbol="x_i",
        unit=_UNIT,
        kind="real_array",
        description="The sample: annual maxima, or any sample of the distribution.",
        physical=_ANY_VALUE,
        applicability="unstated",
        typical=_MAXIMA,
    )


_FITTED_OUTPUTS: Final = (
    Output(
        name="shape",
        unit="-",
        symbol="k",
        description="Shape: s of the log-normal, c of the GEV (scipy's sign, k of "
        "Hosking, -xi of Coles), the skewness of Pearson III, the Weibull shape.",
        physical=Range(),
    ),
    Output(
        name="loc",
        unit=_UNIT,
        symbol=r"\xi",
        description="Location: 0 for the log-normal, the mean of Pearson III, the "
        "lower bound of Weibull.",
        physical=Range(),
    ),
    Output(
        name="scale",
        unit=_UNIT,
        symbol=r"\alpha",
        description="Scale; one that would underflow is the smallest float64 (its "
        "boundary tolerance).",
        physical=Range(low=0.0, low_inclusive=False),
    ),
)


def _enough(least: int, source: Source) -> Constraint:
    return _count(least, source, "annual_maxima")


def _different(
    source: Source, satisfied: tuple[float, ...] = (5.0, 5.0, 5.0, 6.0)
) -> Constraint:
    return _not_constant(source, "annual_maxima", satisfied)


_POSITIVE_FOR_LOG_NORMAL: Final = Constraint(
    name="positive_values",
    cls="precondition",
    check=lambda x: (
        x.choice("distribution") != "log_normal"
        or bool(np.min(x.array("annual_maxima")) > 0.0)
    ),
    text="min(x) > 0 for the log-normal (location 0)",
    source=Source(
        citation=_LMOM,
        locator="pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0",
        url=_LMOM_URL,
    ),
    satisfied={"distribution": "log_normal", "annual_maxima": [0.81, 2.0, 4.0, 8.0]},
    violated={"distribution": "log_normal", "annual_maxima": [-0.81, 2.0, 4.0, 8.0]},
    boundary={"distribution": "log_normal", "annual_maxima": [0.0, 2.0, 4.0, 8.0]},
    boundary_holds=False,
)


def _scaled_parameters(tolerance: Tolerance) -> Scaling:
    return Scaling(
        name="unit_of_the_sample",
        inputs={"annual_maxima": 1.0},
        outputs={"loc": 1.0, "scale": 1.0},
        tolerance=tolerance,
    )


_EXACT_PARAMETERS: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="the estimators run on the sample divided by a power of two, so doubling "
    "it changes no rounding: the shape is the same and loc and scale double exactly; "
    "a scale below the normal floats keeps fewer bits",
)
_FIT_SAMPLES: Final = (_POLANA, _FLOODS11, (1.0, 2.0, 3.0, 4.0, 10.0))
"""Samples of the oracles of the fits: Polana, eleven maxima and five integers."""
_REVERSED_GUMBEL: Final = tuple(math.log(-math.log1p(-j / 21.0)) for j in range(1, 21))
"""The quantiles of the reversed Gumbel distribution at the 20 plotting positions
j / 21: least squares fits it with the Weibull shape growing without limit."""
_LOG_EXP_PARAMETERS: Final = Tolerance(
    abs=1e-300,
    rel=2e-13,
    reason="the searches run on the sample divided by a power of two, so doubling it "
    "changes no rounding; the log-normal's closed form takes exp of the mean of ln x, "
    "whose rounding of up to an ulp of |ln x| < 745 is a relative error of the scale "
    "of up to 745 ulp",
)


def _distribution_l_moments(quantile: Callable[[float], float]) -> list[float]:
    """λ1, λ2 and τ3 of a distribution from its quantile function, by quadrature."""
    from scipy.integrate import quad

    weights: tuple[Callable[[float], float], ...] = (
        lambda f: 1.0,
        lambda f: 2.0 * f - 1.0,
        lambda f: 6.0 * f * f - 6.0 * f + 1.0,
    )
    lambdas = [
        quad(lambda f, w=w: float(quantile(f)) * w(f), 0.0, 1.0, limit=200)[0]
        for w in weights
    ]
    return [lambdas[0], lambdas[1], lambdas[2] / lambdas[1]]


def _fitted_l_moments(run: Callable[..., Values]) -> None:
    """Assert that the fitted distributions have the sample's L-moments (quadrature)."""
    for name in _DISTRIBUTIONS:
        for sample in _FIT_SAMPLES:
            out = run(annual_maxima=list(sample), distribution=name)
            fitted = _DISTRIBUTIONS[name](
                out.real("shape"), loc=out.real("loc"), scale=out.real("scale")
            )
            count = 2 if name == "log_normal" else 3  # two parameters: l1 and l2
            assert_within(
                _distribution_l_moments(fitted.ppf)[:count],
                list(_l_moments(np.array(sample)))[:count],
                rel=3e-5 if name == "pearson3" else 1e-7,
                abs=1e-9,
                reason="lambda_r = integral of Q(F) P*_{r-1}(F) dF by adaptive "
                "quadrature; Pearson III's alpha comes from Hosking's rational "
                "approximations, within 3e-5 relative",
            )


def _fitted_moments(run: Callable[..., Values]) -> None:
    """Assert that the fitted distributions have the sample's moments (scipy)."""
    for name in _DISTRIBUTIONS:
        for sample in _FIT_SAMPLES:
            out = run(annual_maxima=list(sample), distribution=name)
            with np.errstate(all="ignore"):
                mean, variance, skewness = _DISTRIBUTIONS[name].stats(
                    out.real("shape"),
                    loc=out.real("loc"),
                    scale=out.real("scale"),
                    moments="mvs",
                )
            got = [float(mean), math.sqrt(float(variance)), float(skewness)]
            count = 2 if name == "log_normal" else 3  # two parameters: mean and s
            assert_within(
                got[:count],
                list(_moments(np.array(sample)))[:count],
                rel=1e-9,
                abs=1e-9,
                reason="scipy's mean, variance and skewness of the fitted "
                "distribution; the GEV shape solves its skewness by brentq (xtol "
                "2e-12)",
            )


FIT_L_MOMENTS: Final = FormulaSpec(
    name="fit_l_moments",
    title="Parameters of a distribution of annual maxima by the method of L-moments",
    function="hydrolog.statistics.frequency.fit_l_moments",
    family="statistic",
    equation=(
        "the distribution whose L-moments are the sample's l1, l2 and t3: log-normal "
        "(loc 0) s = 2 erfinv(l2 / l1), scale = l1 exp(-s**2 / 2); GEV: c solves t3 "
        "= 2 (1 - 3**-c) / (1 - 2**-c) - 3, scale = l2 c / ((1 - 2**-c) Gamma(1 + "
        "c)), loc = l1 - scale (1 - Gamma(1 + c)) / c; Pearson III: alpha = 4 / G**2 "
        "from |t3| (rational approximations), G = 2 sign(t3) / sqrt(alpha), scale = "
        "l2 sqrt(pi alpha) Gamma(alpha) / Gamma(alpha + 1/2), loc = l1; Weibull: the "
        "GEV (c, xi, a) of (-l1, l2, -t3), shape = 1/c, loc = -xi - a/c, scale = a/c"
    ),
    latex=(
        r"\tau_3 = \frac{2(1 - 3^{-c})}{1 - 2^{-c}} - 3,\quad \alpha = "
        r"\frac{\lambda_2 c}{(1 - 2^{-c})\Gamma(1 + c)},\quad \xi = \lambda_1 - "
        r"\alpha\frac{1 - \Gamma(1 + c)}{c};\qquad s = 2\,\mathrm{erf}^{-1}"
        r"\frac{\lambda_2}{\lambda_1};\qquad \sigma = \lambda_2\sqrt{\pi a}\,"
        r"\frac{\Gamma(a)}{\Gamma(a + 1/2)},\ G = \frac{2\,\mathrm{sign}\,\tau_3}"
        r"{\sqrt{a}}"
    ),
    variables=(_maxima_variable(), _DISTRIBUTION_CHOICE),
    outputs=_FITTED_OUTPUTS,
    sources=(_LMOM_FORTRAN, _HOSKING_WALLIS, _HOSKING_1990),
    constraints=(
        _enough(
            3,
            Source(citation=_LMOM, locator="samlmu: t3 needs 3 values", url=_LMOM_URL),
        ),
        _different(
            Source(
                citation=_LMOM,
                locator="pelgev, pelpe3: l2 must be positive",
                url=_LMOM_URL,
            )
        ),
        _POSITIVE_FOR_LOG_NORMAL,
        Constraint(
            name="l_moments_within_distribution",
            cls="precondition",
            check=lambda x: _within_l_moments(
                x.choice("distribution"), x.array("annual_maxima")
            ),
            text="l2 < l1 (log-normal); -1 < t3 < 1 (GEV, Pearson III); -0.1699 < t3 "
            "< 1 (Weibull)",
            source=_LMOM_FORTRAN,
            satisfied={"distribution": "weibull"},
            violated={"distribution": "weibull", "annual_maxima": list(_NEGATIVE_SKEW)},
        ),
    ),
    constants=_PE3_APPROXIMATION + _GUMBEL_L_CONSTANTS,
    properties=Properties(
        units="homogeneous",
        scalings=(_scaled_parameters(_EXACT_PARAMETERS),),
        limits=(
            Limit(
                name="l_moments_of_the_fit",
                text="the fitted distribution has the sample's l1, l2 and t3 (l1 "
                "and l2 for the log-normal), by quadrature of its quantile function",
                check=_fitted_l_moments,
            ),
        ),
    ),
    validation="none: the estimator gives the distribution of the sample's "
    "L-moments; Hosking and Wallis (1997) report its efficiency on simulated samples",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the unbiased sample L-moments of sample_l_moments",
        "scipy's parameters: the GEV shape c is Hosking's k and -xi of Coles; Pearson "
        "III (loc, scale, shape) are its mean, standard deviation and skewness; the "
        "log-normal has location 0",
        "the GEV shape solved exactly by brentq in -1 < c <= 50 (lmom's pelgev uses "
        "Donaldson's approximation, within 2e-7 of it); a t3 beyond the L-skewness "
        "of an end of that bracket gives the end",
        "Weibull as the GEV of the negated L-moments, as lmom's pelwei",
    ),
    assumptions=("the annual maxima are independent and identically distributed",),
    traps={
        "singular_at_bound": "constraint case l_moments_within_distribution-violated "
        "and test_l_skewness_near_one_clamps_the_gev_shape: |t3| = 1 is refused, a "
        "t3 within rounding of it gives the end of the bracket",
        "unbounded_iteration": "test_l_skewness_near_one_clamps_the_gev_shape: "
        "brentq runs in a bracket, its ends clamped (at most 100 iterations)",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
        "moment_cancellation": "test_a_large_mean_shifts_the_fits: a mean of 1e9 "
        "with the spread of the Polana maxima over 1000",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="the L-moments of the fitted distribution by quadrature of "
            "its quantile function",
            test="tests/unit/test_formulas_flood_frequency.py (limit "
            "l_moments_of_the_fit)",
        ),
        Oracle(
            kind="frozen",
            description="lmom 3.3 pelgev, pelpe3, pelwei, pelln3 (bound 0) and "
            "lmomco 2.5.8 pargev (useHosking=FALSE) on seven samples, R 4.5.3, "
            "2026-11-18",
            test="tests/oracles/frequency_lmom_r.csv",
            conventions=(
                "GEV (xi, alpha, k) of Hosking is scipy's (loc, scale, c)",
                "Pearson III (mu, sigma, gamma) is scipy's (loc, scale, skew)",
                "LN3 (zeta 0, mu, sigma) is scipy's lognorm(s = sigma, scale = "
                "exp(mu))",
                "Weibull (zeta, beta, delta) is scipy's weibull_min(delta, loc = "
                "zeta, scale = beta)",
            ),
        ),
    ),
    base={"annual_maxima": list(_POLANA), "distribution": "gev"},
)


def fit_l_moments(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
) -> FittedParameters:
    """Return the parameters of a distribution by L-moments, spec fit_l_moments.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.

    Returns
    -------
    FittedParameters
        Its ``(shape, loc, scale)`` of :mod:`scipy.stats`.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec (``precondition_failed`` names the
        condition).
    """
    x = checked_inputs(
        FIT_L_MOMENTS, annual_maxima=annual_maxima, distribution=distribution
    )
    found = _by_l_moments(x.choice("distribution"), x.array("annual_maxima"))
    return _fitted(FIT_L_MOMENTS, found)


FIT_MOMENTS: Final = FormulaSpec(
    name="fit_moments",
    title="Parameters of a distribution of annual maxima by the method of moments",
    function="hydrolog.statistics.frequency.fit_moments",
    family="statistic",
    equation=(
        "the distribution whose mean, standard deviation and skewness are the "
        "sample's mean, s and G: log-normal (loc 0) s_l = sqrt(ln(1 + Cv**2)), scale "
        "= mean / sqrt(1 + Cv**2), Cv = s / mean; Pearson III (G, mean, s); GEV: c "
        "solves G(c) = G, G(c) the skewness of the GEV, scale = s / sd(c), loc = "
        "mean - scale m(c), m(c) and sd(c) the mean and standard deviation of the "
        "GEV(c, 0, 1); Weibull: the GEV (c, xi, a) of (-mean, s, -G), shape = 1/c, "
        "loc = -xi - a/c, scale = a/c"
    ),
    latex=(
        r"\sigma_l = \sqrt{\ln(1 + C_v^2)},\ e^{\mu} = \frac{\bar{x}}{\sqrt{1 + "
        r"C_v^2}};\qquad (\gamma, \mu, \sigma) = (G, \bar{x}, s);\qquad "
        r"\gamma_{GEV}(c) = G,\ \alpha = \frac{s}{\sigma_{GEV}(c)},\ \xi = \bar{x} "
        r"- \alpha\,\mu_{GEV}(c)"
    ),
    variables=(_maxima_variable(), _DISTRIBUTION_CHOICE),
    outputs=_FITTED_OUTPUTS,
    sources=(
        Source(
            citation=_B17B,
            locator="pp. 9-10 and appendix 12, example 1: the log-Pearson type III "
            "distribution of the mean, standard deviation and skewness of the "
            "logarithms (eqs. 2, 3a, 4a)",
            url=_B17B_URL,
        ),
        Source(
            citation=_WMO_168,
            locator="sect. 5.5 and table II.5.2, pp. II.5-5 to II.5-12: the method "
            "of moments and the moments of the GEV, log-normal, Pearson type III and "
            "Weibull distributions",
            url=_WMO_168_URL,
        ),
        _SCIPY_STATS,
    ),
    constraints=(
        _enough(
            3,
            Source(
                citation=_B17B,
                locator="eq. 4a: the skewness divides by (N - 1)(N - 2)",
                url=_B17B_URL,
            ),
        ),
        _different(
            Source(
                citation=_B17B,
                locator="eq. 4a: the skewness divides by S cubed, 0 for equal values",
                url=_B17B_URL,
            )
        ),
        _POSITIVE_FOR_LOG_NORMAL,
        Constraint(
            name="skewness_within_distribution",
            cls="precondition",
            check=lambda x: _within_moments(
                x.choice("distribution"), x.array("annual_maxima")
            ),
            text="G > -1.1395 for the Weibull distribution, the skewness of the "
            "reversed Gumbel distribution",
            source=_GUMBEL_CONSTANTS[0].source,
            satisfied={"distribution": "weibull"},
            violated={"distribution": "weibull", "annual_maxima": list(_NEGATIVE_SKEW)},
        ),
    ),
    constants=_GUMBEL_CONSTANTS,
    properties=Properties(
        units="homogeneous",
        scalings=(_scaled_parameters(_EXACT_PARAMETERS),),
        limits=(
            Limit(
                name="moments_of_the_fit",
                text="the fitted distribution has the sample's mean, standard "
                "deviation and skewness (the mean and s for the log-normal), by "
                "scipy's stats",
                check=_fitted_moments,
            ),
        ),
    ),
    validation="none: the estimator gives the distribution of the sample's moments",
    formula_version=1,
    status="referenced",
    conventions=(
        "the sample moments of sample_moments: s with the divisor n - 1, G the "
        "adjusted Fisher-Pearson coefficient",
        "the log-normal of location 0 from the mean and Cv of the values, not of "
        "their logarithms",
        "scipy's parameters: the GEV shape c is Hosking's k and -xi of Coles; Pearson "
        "III (loc, scale, shape) are its mean, standard deviation and skewness",
        "the GEV shape solved by brentq in -1/3 < c <= 50 (the skewness exists above "
        "-1/3); Weibull as the GEV of the negated moments, its c in 0 < c <= 50",
    ),
    assumptions=("the annual maxima are independent and identically distributed",),
    traps={
        "singular_at_bound": "constraint case skewness_within_distribution-violated: "
        "the Weibull shape 1/c grows without limit as G falls to -1.1395",
        "unbounded_iteration": "test_a_skewness_beyond_the_bracket_clamps: brentq "
        "runs in a bracket, its ends clamped (at most 100 iterations)",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
        "moment_cancellation": "test_a_large_mean_shifts_the_fits: a mean of 1e9 "
        "with the spread of the Polana maxima over 1000",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the mean, variance and skewness of the fitted distribution "
            "by scipy.stats",
            test="tests/unit/test_formulas_flood_frequency.py (limit "
            "moments_of_the_fit)",
            conventions=(
                "scipy's skewness of the distribution is the population skewness, "
                "set equal to the sample's G",
            ),
        ),
    ),
    base={"annual_maxima": list(_POLANA), "distribution": "gev"},
)


def fit_moments(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
) -> FittedParameters:
    """Return the parameters of a distribution by moments, spec fit_moments.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.

    Returns
    -------
    FittedParameters
        Its ``(shape, loc, scale)`` of :mod:`scipy.stats`.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec (``precondition_failed`` names the
        condition).
    """
    x = checked_inputs(
        FIT_MOMENTS, annual_maxima=annual_maxima, distribution=distribution
    )
    found = _by_moments(x.choice("distribution"), x.array("annual_maxima"))
    return _fitted(FIT_MOMENTS, found)


def _likelihood_maximum(run: Callable[..., Values]) -> None:
    """No point near the estimate is more likely (a local maximum)."""
    sample = np.array(_POLANA)
    for name in _DISTRIBUTIONS:
        out = run(annual_maxima=list(_POLANA), distribution=name)
        best = [out.real("shape"), out.real("loc"), out.real("scale")]
        top = math.fsum(_DISTRIBUTIONS[name].logpdf(sample, *best))
        for index in (0, 1, 2) if name != "log_normal" else (0, 2):
            for step in (-1e-4, 1e-4):
                moved = list(best)
                moved[index] += step * max(abs(best[index]), best[2])
                there = math.fsum(_DISTRIBUTIONS[name].logpdf(sample, *moved))
                assert_within(
                    max(there - top, 0.0),
                    0.0,
                    abs=1e-9,
                    reason="the log-likelihood a step of 1e-4 away is not higher, "
                    "within the gain at which the search settles",
                )


FIT_MAXIMUM_LIKELIHOOD: Final = FormulaSpec(
    name="fit_maximum_likelihood",
    title="Parameters of a distribution of annual maxima by maximum likelihood",
    function="hydrolog.statistics.frequency.fit_maximum_likelihood",
    family="statistic",
    equation=(
        "the parameters that maximise the log-likelihood sum_i ln f(x_i; shape, loc, "
        "scale) of the distribution's density f; for the log-normal of location 0 "
        "in closed form: ln scale = mean(ln x), s = sqrt(mean((ln x - ln scale)**2))"
    ),
    latex=(
        r"(\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\max \sum_i \ln f(x_i; k, \xi, "
        r"\alpha);\qquad \hat{\mu} = \frac{1}{n}\sum_i \ln x_i,\ \hat{s}^2 = "
        r"\frac{1}{n}\sum_i (\ln x_i - \hat{\mu})^2"
    ),
    variables=(_maxima_variable(), _DISTRIBUTION_CHOICE),
    outputs=_FITTED_OUTPUTS,
    sources=(
        Source(
            citation="Coles, S. (2001). An Introduction to Statistical Modeling of "
            "Extreme Values. Springer",
            locator="sect. 3.3.2 (the likelihood of the GEV) and 3.4.1 (Port Pirie)",
            access="author-provided",
        ),
        Source(
            citation=_SMITH_1985,
            locator="the likelihood of a three-parameter distribution has no "
            "maximum where its density is infinite at the bound of its support",
            access="author-provided",
        ),
        Source(
            citation=_WMO_168,
            locator="sect. 5.5, p. II.5-11: the method of maximum likelihood; sect. "
            "5.3.2.3: the Weibull density goes to infinity at its bound for k < 1",
            url=_WMO_168_URL,
        ),
    ),
    constraints=(
        Constraint(
            name="enough_values",
            cls="precondition",
            check=lambda x: (
                x.array("annual_maxima").size
                > _PARAMETER_COUNTS[x.choice("distribution")]
            ),
            text="n > p, the number of parameters: n >= 3 for the log-normal, n >= 4 "
            "for the others",
            source=Source(
                citation=_SMITH_1985,
                locator="n values fit n parameters exactly, where the likelihood "
                "has no maximum",
                access="author-provided",
            ),
            satisfied={"annual_maxima": [1.0, 2.0, 4.0, 8.0, 16.0]},
            violated={"annual_maxima": [1.0, 2.0, 4.0]},
            boundary={"annual_maxima": [1.0, 2.0, 4.0, 8.0]},
        ),
        _different(
            Source(
                citation=_WMO_168,
                locator="sect. 5.5: the likelihood of values all equal grows without "
                "limit as the scale falls to 0",
                url=_WMO_168_URL,
            ),
            # three values tied at the smallest have no maximum of the likelihood
            satisfied=(5.0, 6.0, 6.0, 7.0),
        ),
        _POSITIVE_FOR_LOG_NORMAL,
        Constraint(
            name="likelihood_has_a_maximum",
            cls="precondition",
            check=lambda x: (
                x.choice("distribution") == "log_normal"
                or _maximum_likelihood(
                    x.choice("distribution"), x.array("annual_maxima")
                ).parameters
                is not None
            ),
            text="the likelihood has a maximum inside the shapes searched: the "
            "search ends neither within 1e-3 of the shapes whose density is "
            "infinite at a bound of the support (GEV c >= 1, Pearson III |G| >= 2, "
            "Weibull shape <= 1), nor of GEV c = -1 (no mean) or Weibull shape 50, "
            "nor at a scale of a millionth of the standard deviation; a GEV has at "
            "most half the values tied at the smallest; and the search settles",
            source=Source(
                citation=_SMITH_1985,
                locator="the bound placed at the closest value makes the likelihood "
                "grow without limit",
                access="author-provided",
            ),
            satisfied={"distribution": "gev"},
            violated={"distribution": "pearson3", "annual_maxima": list(_FLOODS11)},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(_scaled_parameters(_LOG_EXP_PARAMETERS),),
        limits=(
            Limit(
                name="local_maximum",
                text="no point a step of 1e-4 from the estimate is more likely",
                check=_likelihood_maximum,
            ),
        ),
    ),
    validation="none: the estimator gives the most likely distribution of the sample",
    formula_version=1,
    status="referenced",
    conventions=(
        "scipy's densities and parameters: the GEV shape c is -xi of Coles (evd, "
        "extRemes, ismev)",
        "the search runs on the standardised sample (x / 2**e - mean) / sd, from "
        "the L-moments' estimate; Nelder-Mead (xatol 1e-10, fatol 1e-12) is run "
        "again from its end until a run gains at most 1e-9 of log-likelihood, at "
        "most 21 runs",
        "the log-normal of location 0 in closed form (scipy's lognorm.fit with floc=0)",
    ),
    assumptions=("the annual maxima are independent and identically distributed",),
    traps={
        "singular_at_bound": "constraint case likelihood_has_a_maximum-violated: "
        "the density infinite at a bound placed on a value",
        "unbounded_iteration": "test_a_search_that_does_not_settle_is_refused: a "
        "search that does not settle in its bounded count of runs fails the "
        "precondition likelihood_has_a_maximum",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
        "moment_cancellation": "test_a_large_mean_shifts_the_fits: a mean of 1e9 "
        "with the spread of the Polana maxima over 1000",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="frozen",
            description="evd 2.3.7.1 fgev, extRemes 2.2.1 fevd, ismev 1.43 gev.fit "
            "and lmomco 2.5.8 mle2par on seven samples, R 4.5.3, 2026-11-18: "
            "Hydrolog's log-likelihood is not lower",
            test="tests/oracles/frequency_ml_r.csv (tests/unit/"
            "test_maximum_likelihood.py)",
            conventions=(
                "evd, extRemes and ismev give Coles's xi = -c",
                "lmomco's Pearson III (mu, sigma, gamma) and Weibull (zeta, beta, "
                "delta) are written as scipy's parameters",
            ),
        ),
    ),
    base={"annual_maxima": list(_POLANA), "distribution": "gev"},
)


def fit_maximum_likelihood(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
) -> FittedParameters:
    """Return the maximum-likelihood parameters, spec fit_maximum_likelihood.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.

    Returns
    -------
    FittedParameters
        Its ``(shape, loc, scale)`` of :mod:`scipy.stats`.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec (``precondition_failed`` names the
        condition, ``likelihood_has_a_maximum`` a likelihood without a maximum).
    CalculationError
        If an output is not finite (a defect: the search's preconditions hold).
    """
    x = checked_inputs(
        FIT_MAXIMUM_LIKELIHOOD, annual_maxima=annual_maxima, distribution=distribution
    )
    name = x.choice("distribution")
    data = x.array("annual_maxima")
    if name == "log_normal":
        shape, _, scale = lognorm.fit(data, floc=0)
        return _fitted(FIT_MAXIMUM_LIKELIHOOD, (float(shape), 0.0, float(scale)))
    found = _settled(FIT_MAXIMUM_LIKELIHOOD, _maximum_likelihood(name, data))
    return _fitted(FIT_MAXIMUM_LIKELIHOOD, found)


def _squares_minimum(run: Callable[..., Values]) -> None:
    """No point near the estimate has a smaller sum of squares (a local minimum)."""
    sample = np.sort(np.array(_POLANA))
    probabilities = np.arange(1, sample.size + 1) / (sample.size + 1)
    for name in _DISTRIBUTIONS:
        out = run(annual_maxima=list(_POLANA), distribution=name)
        best = [out.real("shape"), out.real("loc"), out.real("scale")]
        quantiles = _DISTRIBUTIONS[name].ppf(probabilities, *best)
        least = math.fsum((sample - quantiles) ** 2)
        for index in (0, 1, 2) if name != "log_normal" else (0, 2):
            for step in (-1e-4, 1e-4):
                moved = list(best)
                moved[index] += step * max(abs(best[index]), best[2])
                there = _DISTRIBUTIONS[name].ppf(probabilities, *moved)
                assert_within(
                    max(least - math.fsum((sample - there) ** 2), 0.0),
                    0.0,
                    abs=1e-9 * least,
                    reason="the sum of squares a step of 1e-4 away is not smaller, "
                    "within the gain at which the search settles",
                )


FIT_LEAST_SQUARES: Final = FormulaSpec(
    name="fit_least_squares",
    title="Parameters of a distribution of annual maxima by least squares on the "
    "plotting positions",
    function="hydrolog.statistics.frequency.fit_least_squares",
    family="statistic",
    equation=(
        "the parameters that minimise sum_j (x(j) - Q(j / (n + 1)))**2 over the "
        "ascending sample x(1) <= ... <= x(n), Q the quantile function of the "
        "distribution: the quantiles at the Weibull plotting positions"
    ),
    latex=(
        r"(\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\min \sum_{j=1}^{n}\left(x_{(j)} "
        r"- Q\left(\frac{j}{n + 1}; k, \xi, \alpha\right)\right)^2"
    ),
    variables=(_maxima_variable(), _DISTRIBUTION_CHOICE),
    outputs=_FITTED_OUTPUTS,
    sources=(
        Source(
            citation=_WMO_168,
            locator="sect. 5.6.1, p. II.5-14: the Weibull plotting position i / (n + "
            "1) of the graphical fit of a distribution to the ordered sample",
            url=_WMO_168_URL,
        ),
        Source(
            citation=_KZGW,
            locator="eq. 3.7: the empirical probability m / (N + 1) of the ordered "
            "annual maxima",
            url=_KZGW_URL,
        ),
    ),
    constraints=(
        _enough(
            3,
            Source(
                citation=_B17B,
                locator="eq. 4a: the moments of the start divide by (N - 1)(N - 2)",
                url=_B17B_URL,
            ),
        ),
        _different(
            Source(
                citation=_WMO_168,
                locator="sect. 5.6.1: values all equal have no spread to fit",
                url=_WMO_168_URL,
            )
        ),
        _POSITIVE_FOR_LOG_NORMAL,
        Constraint(
            name="skewness_within_distribution",
            cls="precondition",
            check=lambda x: _within_moments(
                x.choice("distribution"), x.array("annual_maxima")
            ),
            text="G > -1.1395 for the Weibull distribution: the search starts from "
            "the moments' estimate",
            source=_GUMBEL_CONSTANTS[0].source,
            satisfied={"distribution": "weibull"},
            violated={"distribution": "weibull", "annual_maxima": list(_NEGATIVE_SKEW)},
        ),
        Constraint(
            name="squares_have_a_minimum",
            cls="precondition",
            check=lambda x: (
                _least_squares(
                    x.choice("distribution"), x.array("annual_maxima")
                ).parameters
                is not None
            ),
            text="the sum of squares has a minimum inside the shapes searched "
            "(log-normal s < 5, GEV -1 < c < 50, Pearson III |G| < 9, Weibull shape "
            "< 50) on which the search settles",
            source=Source(
                citation=_B17B,
                locator="appendix 3: the frequency factors of Pearson type III, "
                "tabulated for skews of -9 to 9",
                url=_B17B_URL,
            ),
            satisfied={"distribution": "weibull"},
            violated={
                "distribution": "weibull",
                "annual_maxima": list(_REVERSED_GUMBEL),
            },
        ),
    ),
    constants=_GUMBEL_CONSTANTS,
    properties=Properties(
        units="homogeneous",
        scalings=(_scaled_parameters(_EXACT_PARAMETERS),),
        limits=(
            Limit(
                name="local_minimum",
                text="no point a step of 1e-4 from the estimate has a smaller sum of "
                "squares",
                check=_squares_minimum,
            ),
        ),
    ),
    validation="none: the estimator gives the distribution closest to the plotted "
    "sample",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the Weibull plotting positions j / (n + 1) of the ascending sample, "
        "unweighted residuals in the unit of the sample",
        "scipy's parameters, as fit_moments",
        "the search runs on the standardised sample (the log-normal, of location 0, "
        "only divided by its standard deviation) from the moments' estimate; "
        "Nelder-Mead (xatol 1e-10, fatol 1e-12) is run again from its end until a "
        "run gains at most 1e-9, at most 21 runs",
    ),
    assumptions=("the annual maxima are independent and identically distributed",),
    traps={
        "singular_at_bound": "constraint case skewness_within_distribution-violated: "
        "the Weibull start of a skewness below the reversed Gumbel's",
        "unbounded_iteration": "test_a_search_that_does_not_settle_is_refused: a "
        "search that does not settle in its bounded count of runs fails the "
        "precondition squares_have_a_minimum",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
        "moment_cancellation": "test_a_large_mean_shifts_the_fits: a mean of 1e9 "
        "with the spread of the Polana maxima over 1000",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="the sum of squares at points a step of 1e-4 from the "
            "estimate, by math.fsum",
            test="tests/unit/test_formulas_flood_frequency.py (limit local_minimum)",
        ),
        Oracle(
            kind="algorithm",
            description="Powell's method from the estimate finds no smaller sum of "
            "squares",
            test="tests/unit/test_formulas_flood_frequency.py "
            "(test_powell_finds_no_smaller_squares)",
        ),
    ),
    base={"annual_maxima": list(_POLANA), "distribution": "gev"},
)


def fit_least_squares(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
) -> FittedParameters:
    """Return the least-squares parameters, spec fit_least_squares.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.

    Returns
    -------
    FittedParameters
        Its ``(shape, loc, scale)`` of :mod:`scipy.stats`.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec (``precondition_failed`` names the
        condition).
    CalculationError
        If an output is not finite (a defect: the search's preconditions hold).
    """
    x = checked_inputs(
        FIT_LEAST_SQUARES, annual_maxima=annual_maxima, distribution=distribution
    )
    search = _least_squares(x.choice("distribution"), x.array("annual_maxima"))
    return _fitted(FIT_LEAST_SQUARES, _settled(FIT_LEAST_SQUARES, search))


# --- goodness of fit -------------------------------------------------------------

_ADR_0048: Final = Source(
    citation="Hydrolog (2026). ADR-0048: Anderson-Darling critical values by a "
    "parametric bootstrap",
    locator="decision 1: A² keeps its form, F clipped to [1e-10, 1 - 1e-10]",
    url="https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/"
    "0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md",
)
_SHAPE_OF_THE_DISTRIBUTION: Final = Constraint(
    name="shape_of_the_distribution",
    cls="physical",
    check=lambda x: (
        x.choice("distribution") not in ("log_normal", "weibull") or x.real("shape") > 0
    ),
    text="shape > 0 for the log-normal (s) and Weibull (k)",
    source=Source(
        citation="Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for "
        "scientific computing in Python. Nature Methods 17, 261-272",
        locator="scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape "
        "c > 0",
        url="https://docs.scipy.org/doc/scipy/reference/stats.html",
    ),
    satisfied={"distribution": "weibull", "shape": 1.2, "loc": 0.0},
    violated={"distribution": "weibull", "shape": -0.01, "loc": 0.0},
    boundary={"distribution": "weibull", "shape": 0.0, "loc": 0.0},
    boundary_holds=False,
)


def _fitted_variables() -> tuple[Variable, ...]:
    """Return the inputs of a statistic of a fitted distribution: sample, parameters."""
    return (
        _maxima_variable(),
        _DISTRIBUTION_CHOICE,
        _parameter(
            "shape",
            "k",
            "Shape: s of the log-normal, c of the GEV (scipy's sign, k of Hosking, -xi "
            "of Coles), the skewness of Pearson III, the Weibull shape.",
            Range(
                test_low=-9.0,
                test_high=50.0,
                test_reason="the shapes of Hydrolog's estimators: a Pearson III "
                "skewness above -9 by least squares, a GEV c and a Weibull shape of "
                "at most 50",
            ),
            (-0.6, 2.7),
            unit="-",
        ),
        _parameter("loc", r"\xi", "Location.", _ANY_VALUE, (-1.0, 35.4)),
        _parameter("scale", r"\alpha", "Scale.", _SCALE_RANGE, (1.0, 37.0)),
    )


_FITTED_BASE: Final = {
    "annual_maxima": list(_POLANA),
    "distribution": "gev",
    "shape": -0.18,
    "loc": 20.9,
    "scale": 16.4,
}
"""The typical point: the Polana maxima and their GEV of the L-moments, rounded."""
_GOODNESS_SAMPLES: Final = (_POLANA, _FLOODS11)
"""The samples of the oracles of the statistics of the fits."""
_OUTSIDE_SUPPORT: Final = ("weibull", (1.2, 5.0, 30.0))
"""A Weibull distribution with its lower bound above the smallest Polana maximum."""


def _distribution(x: Values) -> Any:
    """Return the scipy distribution of the inputs, frozen at their parameters."""
    return _DISTRIBUTIONS[x.choice("distribution")](
        x.real("shape"), loc=x.real("loc"), scale=x.real("scale")
    )


def _a_squared(probabilities: NDArray[np.float64]) -> NDArray[np.float64]:
    """A² of the distribution function's values at ascending samples (the last axis).

    The values are clipped to the spec's ``[cdf_clip, 1 - cdf_clip]``, so a value
    outside the support adds a large finite term.
    """
    clip = ANDERSON_DARLING.constant("cdf_clip")
    n = probabilities.shape[-1]
    clipped = np.clip(probabilities, clip, 1.0 - clip)
    weights = (2.0 * np.arange(1, n + 1) - 1.0) / n
    terms = np.log(clipped) + np.log(1.0 - clipped[..., ::-1])
    result: NDArray[np.float64] = -n - np.sum(weights * terms, axis=-1)
    return result


def _a_squared_integral(probabilities: list[float]) -> Decimal:
    """A² = n ∫ (F_n(u) - u)² / (u (1 - u)) du over [0, 1], at 50 digits.

    Between the ith and the next of the ascending u the empirical distribution
    function is c = i / n, and (c - u)² / (u (1 - u)) = c² / u + (1 - c)² / (1 - u)
    - 1 has a closed integral.
    """
    with localcontext(prec=50):
        ends = [Decimal(0), *sorted(Decimal(p) for p in probabilities), Decimal(1)]
        n = len(probabilities)
        total = Decimal(0)
        for i in range(n + 1):
            low, high, c = ends[i], ends[i + 1], Decimal(i) / n
            total -= high - low
            if i > 0:
                total += c * c * (high / low).ln()
            if i < n:
                total -= (1 - c) ** 2 * ((1 - high) / (1 - low)).ln()
        return n * total


def _a_squared_by_the_integral(run: Callable[..., Values]) -> None:
    """Assert A² of the fits, and of one outside its support, against the integral."""
    clip = ANDERSON_DARLING.constant("cdf_clip")
    fits = [
        (sample, name, _by_l_moments(name, np.array(sample)))
        for sample in _GOODNESS_SAMPLES
        for name in _DISTRIBUTIONS
    ]
    for sample, name, (shape, loc, scale) in [
        *fits,
        (_POLANA, _OUTSIDE_SUPPORT[0], _OUTSIDE_SUPPORT[1]),
    ]:
        out = run(
            annual_maxima=list(sample),
            distribution=name,
            shape=shape,
            loc=loc,
            scale=scale,
        )
        cdf = _DISTRIBUTIONS[name].cdf(np.array(sample), shape, loc=loc, scale=scale)
        exact = _a_squared_integral(list(np.clip(cdf, clip, 1.0 - clip)))
        assert_within(
            out.real("a_squared"),
            float(exact),
            abs=1e-12,
            reason="the integral form of A² in closed pieces at 50 digits; the code "
            "sums n terms of up to 2 |ln 1e-10|, each within an ulp",
        )


ANDERSON_DARLING: Final = FormulaSpec(
    name="anderson_darling",
    title="Anderson-Darling statistic A² of a sample against a fitted distribution",
    function="hydrolog.statistics.frequency.anderson_darling",
    family="statistic",
    equation=(
        "A² = -n - sum_i (2 i - 1) / n [ln F(x_(i)) + ln(1 - F(x_(n+1-i)))] over the "
        "ascending sample x_(1) <= ... <= x_(n), F the distribution function at the "
        "parameters, clipped to [cdf_clip, 1 - cdf_clip]"
    ),
    latex=(
        r"A^2 = -n - \sum_{i=1}^{n} \frac{2i - 1}{n}\left[\ln F(x_{(i)}) + "
        r"\ln\left(1 - F(x_{(n+1-i)})\right)\right]"
    ),
    variables=_fitted_variables(),
    outputs=(
        Output(
            name="a_squared",
            unit="-",
            symbol="A^2",
            description="The statistic: n times the integral of the squared distance "
            "of the empirical and the fitted distribution functions, weighted by "
            "1 / (F (1 - F)).",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        Source(
            citation="NIST/SEMATECH e-Handbook of Statistical Methods (2012)",
            locator="sect. 1.3.5.14, Anderson-Darling test: A² = -N - S, S = sum (2i "
            "- 1) / N [ln F(Y_i) + ln(1 - F(Y_(N+1-i)))] of the ordered data",
            url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm",
        ),
        Source(
            citation="Anderson, T.W. and Darling, D.A. (1954). A test of goodness of "
            "fit. Journal of the American Statistical Association 49(268), 765-769",
            locator="the statistic W_n² and its computing form",
            access="author-provided",
        ),
        Source(
            citation="Stephens, M.A. (1974). EDF statistics for goodness of fit and "
            "some comparisons. Journal of the American Statistical Association "
            "69(347), 730-737",
            locator="the computing form of A²; case 0, a distribution given in advance",
            access="author-provided",
        ),
    ),
    constants=(
        Constant(
            name="cdf_clip", value=1e-10, unit="-", symbol=r"\epsilon", source=_ADR_0048
        ),
    ),
    constraints=(_SHAPE_OF_THE_DISTRIBUTION,),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"annual_maxima": 1.0, "loc": 1.0, "scale": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="(x - loc) / scale of the doubled sample, loc and scale is "
                    "the same float, so F is",
                ),
            ),
        ),
        symmetries=(
            Symmetry(
                name="order",
                text="the sample in the reverse order has the same A²",
                inputs=lambda x: {**x, "annual_maxima": x.array("annual_maxima")[::-1]},
                outputs=dict,
                tolerance=Tolerance(
                    abs=0.0, reason="the statistic sorts the sample first"
                ),
            ),
        ),
        limits=(
            Limit(
                name="integral_form",
                text="n times the integral of (F_n(u) - u)² / (u (1 - u)) over [0, "
                "1], in closed pieces at 50 digits, for the L-moment fits of two "
                "samples and a Weibull distribution that leaves a value outside its "
                "support",
                check=_a_squared_by_the_integral,
            ),
        ),
    ),
    validation="none: a distance between the sample and the fitted distribution",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the statistic of a distribution given in advance (case 0 of Stephens 1974), "
        "here at the parameters estimated from the same sample: its critical values "
        "are not case 0's",
        "the critical values FloodFrequencyAnalysis gives a fit by L-moments are "
        "those of a parametric bootstrap of that fit (ADR-0048): 999 samples of n "
        "values drawn from it with the seed 20261118, each refitted by L-moments; a "
        "fit by another method has none",
        "F clipped to [cdf_clip, 1 - cdf_clip], so a value outside the support of the "
        "distribution adds a large finite term instead of an infinite one",
        "F of scipy.stats at the parameters of its lognorm, genextreme, pearson3 or "
        "weibull_min",
        "the sample in any unit, with loc and scale in it: A² has none",
    ),
    traps={
        "singular_at_bound": "limit integral_form: ln F at a value outside the "
        "support, where F = 0, is ln cdf_clip",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the integral form of the definition, n times the integral of "
            "(F_n(u) - u)² / (u (1 - u)) du, in closed pieces at 50 digits (decimal)",
            test="tests/unit/test_formulas_flood_frequency.py (limit integral_form)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.anderson for the normal distribution (Pearson "
            "III of skewness 0) and the Gumbel distribution (the GEV of c = 0)",
            test="tests/unit/test_formulas_flood_frequency.py "
            "(test_the_a_squared_is_scipys)",
            conventions=(
                "scipy.stats.anderson estimates the parameters itself (the mean and "
                "the standard deviation of ddof 1; the Gumbel's by maximum "
                "likelihood): they are given to the formula",
                "scipy takes ln F and ln(1 - F) as logcdf and logsf, unclipped",
            ),
        ),
    ),
    base=_FITTED_BASE,
)


def anderson_darling(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
    shape: float,
    loc: float,
    scale: float,
) -> float:
    """Return the A² of a sample against a distribution, spec anderson_darling.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.
    shape, loc, scale : float
        Its parameters, those of :mod:`scipy.stats`.

    Returns
    -------
    float
        The statistic A².

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec.
    """
    x = checked_inputs(
        ANDERSON_DARLING,
        annual_maxima=annual_maxima,
        distribution=distribution,
        shape=shape,
        loc=loc,
        scale=scale,
    )
    probabilities = _distribution(x).cdf(np.sort(x.array("annual_maxima")))
    statistic = float(_a_squared(np.asarray(probabilities, dtype=np.float64)))
    return checked_outputs(ANDERSON_DARLING, {"a_squared": statistic}).real("a_squared")


def _log_densities(x: Values) -> NDArray[np.float64]:
    """Return ln f of each value of the sample under the distribution of the inputs."""
    with np.errstate(all="ignore"):
        found = _distribution(x).logpdf(x.array("annual_maxima"))
    return np.asarray(found, dtype=np.float64)


def _within_support(x: Values) -> bool:
    """Whether every ln f, and so the log-likelihood, is finite."""
    log_densities = _log_densities(x)
    return bool(np.isfinite(log_densities).all() and np.isfinite(np.sum(log_densities)))


def _log_density_by_hand(
    name: str, value: float, shape: float, loc: float, scale: float
) -> float:
    """Return ln f of a value inside the support, the density written out by hand."""
    z = (value - loc) / scale
    if name == "log_normal":
        w = math.log(z) / shape
        return (
            -math.log(value - loc)
            - math.log(shape * math.sqrt(2 * math.pi))
            - w * w / 2
        )
    if name == "gev":
        if shape == 0.0:
            return -math.log(scale) - z - math.exp(-z)
        t = 1.0 - shape * z
        return (
            -math.log(scale)
            + (1.0 / shape - 1.0) * math.log(t)
            - math.pow(t, 1.0 / shape)
        )
    if name == "weibull":
        return (
            math.log(shape / scale) + (shape - 1.0) * math.log(z) - math.pow(z, shape)
        )
    alpha = 4.0 / shape**2  # Pearson III: a gamma distribution from its bound
    beta = scale * shape / 2.0
    y = (value - (loc - 2.0 * scale / shape)) / beta
    return -math.log(abs(beta)) + (alpha - 1.0) * math.log(y) - y - math.lgamma(alpha)


def _aic_by_hand(run: Callable[..., Values]) -> None:
    """Assert the AIC of the moment fits against the densities written out."""
    for sample in _GOODNESS_SAMPLES:
        for name in _DISTRIBUTIONS:
            shape, loc, scale = _by_moments(name, np.array(sample))
            out = run(
                annual_maxima=list(sample),
                distribution=name,
                shape=shape,
                loc=loc,
                scale=scale,
            )
            log_likelihood = math.fsum(
                _log_density_by_hand(name, value, shape, loc, scale) for value in sample
            )
            assert_within(
                out.real("aic"),
                2.0 * _PARAMETER_COUNTS[name] - 2.0 * log_likelihood,
                rel=1e-12,
                reason="the densities written out in floating point: each ln f "
                "within a few ulp of its largest term",
            )


def _aic_of_the_doubled_sample(run: Callable[..., Values]) -> None:
    """Assert that doubling the sample, loc and scale adds 2 n ln 2 to the AIC."""
    for sample in _GOODNESS_SAMPLES:
        for name in _DISTRIBUTIONS:
            shape, loc, scale = _by_moments(name, np.array(sample))
            here, there = (
                run(
                    annual_maxima=[factor * value for value in sample],
                    distribution=name,
                    shape=shape,
                    loc=factor * loc,
                    scale=factor * scale,
                ).real("aic")
                for factor in (1.0, 2.0)
            )
            assert_within(
                there,
                here + 2.0 * len(sample) * math.log(2.0),
                rel=1e-13,
                abs=1e-12,
                reason="each density of the doubled sample is half its density: ln f "
                "falls by ln 2 for each value, which rounds within an ulp of ln f",
            )


AKAIKE: Final = FormulaSpec(
    name="akaike_information_criterion",
    title="Akaike information criterion of a distribution fitted to a sample",
    function="hydrolog.statistics.frequency.akaike_information_criterion",
    family="statistic",
    equation=(
        "AIC = 2 k - 2 sum_i ln f(x_i; shape, loc, scale), f the density at the "
        "parameters; k = 2 for the log-normal of location 0, 3 for the others"
    ),
    latex=r"\mathrm{AIC} = 2k - 2\sum_{i=1}^{n} \ln f(x_i; k, \xi, \alpha)",
    variables=_fitted_variables(),
    outputs=(
        Output(
            name="aic",
            unit="-",
            symbol=r"\mathrm{AIC}",
            description="The criterion: the lower, the better the fit for its number "
            "of parameters.",
            physical=Range(),
        ),
    ),
    sources=(
        Source(
            citation=_WMO_168,
            locator="sect. 5.6.3, eq. 5.31, pp. II.5-14 and II.5-15: AIC(f) = -2 log "
            "L(theta, x) + 2k, with L the likelihood function and k the number of "
            "parameters; alone not appropriate for model selection",
            url=_WMO_168_URL,
        ),
        Source(
            citation="Akaike, H. (1974). A new look at the statistical model "
            "identification. IEEE Transactions on Automatic Control 19(6), 716-723",
            locator="the criterion -2 ln (maximum likelihood) + 2 k",
            access="author-provided",
        ),
    ),
    constraints=(
        _SHAPE_OF_THE_DISTRIBUTION,
        Constraint(
            name="values_within_support",
            cls="precondition",
            check=_within_support,
            text="ln f(x_i) is finite for every value, and so is their sum: each value "
            "inside the support of the distribution, where its density is positive "
            "and finite",
            source=Source(
                citation=_WMO_168,
                locator="sect. 5.6.3, eq. 5.31: the logarithm of the likelihood, "
                "-inf where a value has no density",
                url=_WMO_168_URL,
            ),
            satisfied={"distribution": "gev"},
            violated={
                "distribution": "weibull",
                "shape": 1.2,
                "loc": 4.93,
                "scale": 30.0,
            },
            boundary={
                "distribution": "weibull",
                "shape": 1.2,
                "loc": 4.92,
                "scale": 30.0,
            },
            boundary_holds=False,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        symmetries=(
            Symmetry(
                name="order",
                text="the sample in the reverse order has the same AIC",
                inputs=lambda x: {**x, "annual_maxima": x.array("annual_maxima")[::-1]},
                outputs=dict,
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the log-likelihood is summed exactly rounded (math.fsum), "
                    "in any order",
                ),
            ),
        ),
        limits=(
            Limit(
                name="closed_form",
                text="the AIC of the moment fits of two samples, every value inside "
                "their supports, with the densities of the four distributions written "
                "out",
                check=_aic_by_hand,
            ),
            Limit(
                name="unit_of_the_sample",
                text="doubling the sample, loc and scale adds 2 n ln 2: the AIC "
                "depends on the unit of the sample",
                check=_aic_of_the_doubled_sample,
            ),
        ),
    ),
    validation="none: a criterion for comparing fits; WMO-No. 168 finds it alone not "
    "appropriate for choosing one",
    formula_version=1,
    status="referenced",
    conventions=(
        "the likelihood at the parameters of the method that fitted them, the "
        "maximum only for maximum likelihood (ADR-0021, point 7): a ranking by AIC "
        "compares the likelihood of each fit's parameters",
        "k counts the parameters fitted: 2 for the log-normal, whose location is fixed "
        "at 0, 3 for the others",
        "a fit that leaves a value outside its support has no finite AIC: "
        "FloodFrequencyAnalysis gives it an infinite AIC without the formula, with "
        "the notice outside_support, and ranks it last",
        "ln f of scipy.stats at the parameters of its lognorm, genextreme, pearson3 "
        "or weibull_min, summed exactly rounded (math.fsum)",
        "the natural logarithm; the AIC depends on the unit of the sample",
    ),
    traps={
        "singular_at_bound": "constraint case values_within_support-violated: ln f "
        "of a value outside the support is refused before the sum",
        "gap_propagation": "type case annual_maxima-nan_element: a gap is refused",
        "many_small_terms": "symmetry order: the log-likelihood is summed exactly "
        "rounded, in any order",
    },
    reference_cases=("tests/fixtures/formulas/flood-frequency-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the log-likelihood with the densities of the GEV, the "
            "log-normal, Pearson III and Weibull written out (math)",
            test="tests/unit/test_formulas_flood_frequency.py (limit closed_form)",
        ),
    ),
    base=_FITTED_BASE,
)


def akaike_information_criterion(
    annual_maxima: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
    shape: float,
    loc: float,
    scale: float,
) -> float:
    """Return the AIC of a distribution of a sample, spec akaike_information_criterion.

    Parameters
    ----------
    annual_maxima : array_like of float
        The sample.
    distribution : str
        The distribution: ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.
    shape, loc, scale : float
        Its parameters, those of :mod:`scipy.stats`.

    Returns
    -------
    float
        The criterion.

    Raises
    ------
    InvalidParameterError
        If the inputs are refused by the spec (``values_within_support`` for a value
        without a density).
    """
    x = checked_inputs(
        AKAIKE,
        annual_maxima=annual_maxima,
        distribution=distribution,
        shape=shape,
        loc=loc,
        scale=scale,
    )
    parameters = _PARAMETER_COUNTS[x.choice("distribution")]
    aic = 2.0 * parameters - 2.0 * math.fsum(_log_densities(x))
    return checked_outputs(AKAIKE, {"aic": aic}).real("aic")


SPECS: Final = (
    MOMENTS,
    L_MOMENTS,
    GEV_QUANTILES,
    LOG_NORMAL_QUANTILES,
    PEARSON3_QUANTILES,
    WEIBULL_QUANTILES,
    FIT_L_MOMENTS,
    FIT_MOMENTS,
    FIT_MAXIMUM_LIKELIHOOD,
    FIT_LEAST_SQUARES,
    ANDERSON_DARLING,
    AKAIKE,
)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""
