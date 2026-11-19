"""Distributions of annual extremes: sample statistics and parameter estimators.

The formulas of the frequency analyses of annual maxima
(:class:`~hydrolog.statistics.FloodFrequencyAnalysis`) and minima
(:func:`~hydrolog.statistics.fit_fisher_tippett_minima`), declared by their specs
(Nogat's computation standard, ADR-0050): the sample's product moments
(:data:`MOMENTS`, ``sample_moments``) and L-moments (:data:`L_MOMENTS`,
``sample_l_moments``), and the estimators of the parameters of the log-normal, GEV,
Pearson type III and Weibull distributions of :mod:`scipy.stats` by L-moments,
moments, maximum likelihood and least squares. ``docs/FORMULAS.md`` shows their
equations, constants, ranges and sources.

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
from fractions import Fraction
from typing import Any, Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq, minimize
from scipy.special import erfinv, gamma, gammaln, zeta
from scipy.stats import genextreme, lognorm, pearson3, weibull_min

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
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
    "L_MOMENTS",
    "MOMENTS",
    "SPECS",
    "SampleLMoments",
    "SampleMoments",
    "sample_l_moments",
    "sample_moments",
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
# limits (named here for an error message), if there is one.
_UNBOUNDED_LIKELIHOOD: Final = {
    "gev": "the shape c of 1",
    "pearson3": "the skewness of 2 or -2",
    "weibull": "the shape of 1",
}
# The search for the maximum likelihood (Nelder-Mead on the standardised sample) and
# its check: it is run again from the point found until a run gains no more than
# _ML_GAIN of log-likelihood, at most _ML_RUNS times. Its start has a shape at least
# _ML_INSIDE short of the limit and a bound _ML_MARGIN standard deviations beyond the
# sample; an end closer to the limit than _ML_EDGE is the limit, where there is no
# maximum.
_ML_NELDER_MEAD: Final = {
    "xatol": 1e-10,
    "fatol": 1e-12,
    "maxiter": 10_000,
    "maxfev": 20_000,
}
_ML_RUNS: Final = 20
_ML_GAIN: Final = 1e-9
_ML_INSIDE: Final = 0.1
_ML_MARGIN: Final = 0.05
_ML_EDGE: Final = 1e-3
# The skewness and the L-skewness of the Gumbel distribution (the GEV with shape 0):
# the Weibull distribution of the moments and L-moments needs a sample statistic above
# minus these, the limit of its skewness and L-skewness as its shape grows.
_GUMBEL_SKEWNESS: Final = float(12.0 * np.sqrt(6.0) * zeta(3.0) / np.pi**3)  # 1.1395
_GUMBEL_L_SKEWNESS: Final = float(2.0 * np.log(3.0) / np.log(2.0) - 3.0)  # 0.1699
# Brackets of the GEV shape c (scipy's sign; Hosking's k, -ξ of Coles 2001): the
# skewness exists above c = -1/3 and the mean (so the L-moments) above c = -1; the
# gamma functions of the skewness overflow above c of about 56.
_GEV_SHAPES_BY_SKEWNESS: Final = (-1.0 / 3.0 + 1e-6, 50.0)
_GEV_SHAPES_BY_L_SKEWNESS: Final = (-1.0 + 1e-9, 50.0)


class _NoParameters(Exception):
    """A fit method gives no parameters of a distribution for the sample.

    :meth:`~hydrolog.statistics.FloodFrequencyAnalysis._estimate` turns it into a
    :class:`~hydrolog.exceptions.CalculationError` that names the method and the
    distribution.

    Parameters
    ----------
    reason : str
        ``details.reason`` of that error.
    message : str
        Why, in words that follow a colon.
    **details : object
        Further JSON-compatible details.
    """

    def __init__(self, reason: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.reason = reason
        self.details = details


def _require_spread(data: NDArray[np.float64], minimum: int = _MIN_VALUES) -> None:
    """Require ``minimum`` values, not all equal.

    By default the 3 values of the skewness and the L-skewness; maximum likelihood asks
    for one more than the distribution's parameters.
    """
    if data.size < minimum:
        raise _NoParameters(
            "too_few_values",
            f"it needs at least {minimum} values, got {data.size}",
            count=int(data.size),
            minimum=minimum,
        )
    if data.min() == data.max():
        raise _NoParameters("constant_values", "all values are equal")


def _require_range(
    statistic: str, value: float, minimum: float, maximum: float | None = None
) -> None:
    """Require a sample ``statistic`` inside the open range a distribution can take.

    ``statistic`` is ``"skewness"`` or ``"l_skewness"``; ``maximum`` ``None`` is no
    upper limit.
    """
    if minimum < value and (maximum is None or value < maximum):
        return
    name = "L-skewness" if statistic == "l_skewness" else statistic
    limits = (
        f"above {minimum:.4g}"
        if maximum is None
        else f"between {minimum:.4g} and {maximum:.4g}"
    )
    raise _NoParameters(
        "out_of_range",
        f"the sample {name} {value:.4g} is not {limits}",
        statistic=statistic,
        value=value,
        minimum=minimum,
        maximum=maximum,
    )


def _require_positive(data: NDArray[np.float64]) -> None:
    """Require values above 0, the support of the log-normal with location 0."""
    smallest = float(data.min())
    if smallest > 0.0:
        return
    raise _NoParameters(
        "non_positive_values",
        f"it needs values above 0, the smallest is {smallest:.6g}",
        count=int(np.count_nonzero(data <= 0.0)),
        smallest=smallest,
    )


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


def _count(least: int, source: Source) -> Constraint:
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


def _not_constant(source: Source) -> Constraint:
    """Return the precondition of values not all equal."""
    return Constraint(
        name="values_not_all_equal",
        cls="precondition",
        check=lambda x: bool(np.ptp(x.array("values")) > 0.0),
        text="min(x) < max(x)",
        source=source,
        satisfied={"values": [5.0, 5.0, 5.0, 6.0]},
        violated={"values": [5.0, 5.0, 5.0, 5.0]},
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
    spread (the corrected two-pass algorithm).
    """
    scaled, exponent = _normalised(data)
    n = data.size
    centre = float(np.mean(scaled))
    deviations = scaled - centre
    residual = float(np.mean(deviations))
    deviations -= residual
    m2 = float(np.mean(deviations**2))
    m3 = float(np.mean(deviations**3))
    skewness = math.sqrt(n * (n - 1)) / (n - 2) * m3 / m2**1.5
    std = math.sqrt(m2 * n / (n - 1))
    return SampleMoments(
        math.ldexp(centre + residual, exponent), math.ldexp(std, exponent), skewness
    )


def _sample_moments(data: NDArray[np.float64]) -> SampleMoments:
    """Mean, standard deviation and skewness of a sample (:data:`MOMENTS`).

    Raises ``_NoParameters`` for fewer than 3 values or values all equal.
    """
    _require_spread(data)
    return _moments(data)


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


def _sample_l_moments(data: NDArray[np.float64]) -> SampleLMoments:
    """L-moments λ1 and λ2 and L-skewness τ3 of a sample (:data:`L_MOMENTS`).

    Raises ``_NoParameters`` for fewer than 3 values or values all equal.
    """
    _require_spread(data)
    return _l_moments(data)


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


def _shape(
    statistic: Callable[[float], float], value: float, bracket: tuple[float, float]
) -> float:
    """Return the shape in ``bracket`` whose ``statistic`` (decreasing) is ``value``."""
    return float(brentq(lambda shape: statistic(shape) - value, *bracket))


def _gev_skewness(c: float) -> float:
    """Skewness of the GEV with shape ``c``."""
    with np.errstate(all="ignore"):  # scipy computes the kurtosis too; it overflows
        return float(genextreme.stats(c, moments="s"))


def _gev_from_moments(
    mean: float, std: float, skewness: float
) -> tuple[float, float, float]:
    """GEV ``(c, loc, scale)`` with the given mean, standard deviation and skewness."""
    c = _shape(_gev_skewness, skewness, _GEV_SHAPES_BY_SKEWNESS)
    with np.errstate(all="ignore"):
        mean_1, variance_1 = genextreme.stats(c, moments="mv")
    scale = std / float(np.sqrt(variance_1))
    return c, mean - scale * float(mean_1), scale


def _gev_l_skewness(c: float) -> float:
    """L-skewness τ3 = 2 (1 - 3^-c) / (1 - 2^-c) - 3 of the GEV with shape ``c``."""
    if c == 0.0:
        return _GUMBEL_L_SKEWNESS
    return float(2.0 * np.expm1(-c * np.log(3.0)) / np.expm1(-c * np.log(2.0)) - 3.0)


def _gev_from_l_moments(l1: float, l2: float, t3: float) -> tuple[float, float, float]:
    """GEV ``(c, loc, scale)`` with the given L-moments (Hosking and Wallis 1997).

    The shape c solves τ3 = 2 (1 - 3^-c) / (1 - 2^-c) - 3; then
    α = λ2 c / ((1 - 2^-c) Γ(1 + c)) and ξ = λ1 - α (1 - Γ(1 + c)) / c, with the
    limits α = λ2 / ln 2 and ξ = λ1 - 0.5772 α (Euler's constant) of the Gumbel
    distribution (c = 0).
    """
    c = _shape(_gev_l_skewness, t3, _GEV_SHAPES_BY_L_SKEWNESS)
    if abs(c) < 1e-8:
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
    (α within 3e-5, relative, of the exact τ3 = 6 I(1/3; α, 2α) - 3), then
    γ = 2 sign(τ3) / √α, σ = λ2 √(π α) Γ(α) / Γ(α + 1/2) and μ = λ1; below
    |τ3| = 1e-6 the normal distribution, σ = λ2 √π.
    """
    t = abs(t3)
    if t < 1e-6:
        return 0.0, l1, l2 * float(np.sqrt(np.pi))
    if t >= 1.0 / 3.0:
        z = 1.0 - t
        alpha = (z * (0.36067 + z * (-0.59567 + z * 0.25361))) / (
            1.0 + z * (-2.78861 + z * (2.56096 + z * -0.77045))
        )
    else:
        z = 3.0 * np.pi * t * t
        alpha = (1.0 + 0.2906 * z) / (z * (1.0 + z * (0.1882 + z * 0.0442)))
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


def _by_moments(name: str, data: NDArray[np.float64]) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name`` by moments."""
    if name == "log_normal":
        _require_positive(data)
    mean, std, skewness = _sample_moments(data)
    if name == "log_normal":
        # mean = scale exp(s²/2) and Cv² = exp(s²) - 1
        cv2 = (std / mean) ** 2
        return float(np.sqrt(np.log1p(cv2))), 0.0, mean / float(np.sqrt(1.0 + cv2))
    if name == "pearson3":
        return skewness, mean, std  # scipy's parameters are these moments
    if name == "gev":
        return _gev_from_moments(mean, std, skewness)
    _require_range("skewness", skewness, -_GUMBEL_SKEWNESS)
    return _weibull_from_reversed_gev(*_gev_from_moments(-mean, std, -skewness))


def _by_l_moments(name: str, data: NDArray[np.float64]) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name`` by L-moments."""
    if name == "log_normal":
        _require_positive(data)
    l1, l2, t3 = _sample_l_moments(data)
    if name == "log_normal":
        # λ1 = scale exp(s²/2) and λ2 = λ1 erf(s/2)
        shape = 2.0 * float(erfinv(l2 / l1))
        return shape, 0.0, l1 * float(np.exp(-0.5 * shape**2))
    if name == "weibull":
        _require_range("l_skewness", t3, -_GUMBEL_L_SKEWNESS, 1.0)
        return _weibull_from_reversed_gev(*_gev_from_l_moments(-l1, l2, -t3))
    _require_range("l_skewness", t3, -1.0, 1.0)
    if name == "gev":
        return _gev_from_l_moments(l1, l2, t3)
    return _pearson3_from_l_moments(l1, l2, t3)


def _by_least_squares(
    name: str, data: NDArray[np.float64]
) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name`` by least squares.

    They minimise Σ (x(j) - Q(j / (n + 1)))² over the ascending sample x(j), Q the
    quantile function of the distribution: the quantiles at the Weibull plotting
    positions of the empirical frequency of
    :class:`~hydrolog.statistics.FloodFrequencyAnalysis`. Nelder-Mead starts from the
    moments; it searches the logarithm of the scale and of the log-normal and Weibull
    shapes, which stay positive.
    """
    shape, loc, scale = _by_moments(name, data)
    ascending = np.sort(data)
    probabilities = np.arange(1, data.size + 1) / (data.size + 1)
    distribution = _DISTRIBUTIONS[name]
    positive_shape = name in ("log_normal", "weibull")

    def parameters(point: NDArray[np.float64]) -> tuple[float, float, float]:
        first = float(np.exp(point[0])) if positive_shape else float(point[0])
        if name == "log_normal":
            return first, 0.0, float(np.exp(point[1]))
        return first, float(point[1]), float(np.exp(point[2]))

    def squares(point: NDArray[np.float64]) -> float:
        with np.errstate(all="ignore"):
            quantiles = distribution.ppf(probabilities, *parameters(point))
            total = float(np.sum((ascending - quantiles) ** 2))
        return total if np.isfinite(total) else np.inf

    first = float(np.log(shape)) if positive_shape else shape
    start = (
        [first, float(np.log(scale))]
        if name == "log_normal"
        else [first, loc, float(np.log(scale))]
    )
    found = minimize(squares, start, method="Nelder-Mead")
    return parameters(found.x)


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
    """How far ``shape`` lies short of the limit of ``_UNBOUNDED_LIKELIHOOD``.

    Positive where the likelihood of ``name`` can have a maximum, 0 or less where the
    density is infinite at a bound of the support.
    """
    if name == "gev":
        return 1.0 - shape
    if name == "pearson3":
        return 2.0 - abs(shape)
    return shape - 1.0


def _ml_start(name: str, sample: NDArray[np.float64]) -> tuple[float, float, float]:
    """Start ``(shape, loc, scale)`` of the maximum-likelihood search on ``sample``.

    ``sample`` is standardised (mean 0, standard deviation 1). The start is the
    L-moments' estimate, else the moments', else the distribution of skewness 0, with
    its shape moved ``_ML_INSIDE`` short of the limit if it is closer and its location
    moved, if needed, so that a bound of the support lies ``_ML_MARGIN`` beyond the
    sample: a value without density leaves no likelihood to improve.
    """
    for estimate in (_by_l_moments, _by_moments):
        try:
            shape, loc, scale = estimate(name, sample)
            break
        except _NoParameters:
            continue
    else:  # only Weibull: a sample skewness below that of every Weibull distribution
        shape, loc, scale = _weibull_from_reversed_gev(
            *_gev_from_moments(0.0, 1.0, 0.0)
        )
    if name == "gev":
        shape = min(shape, 1.0 - _ML_INSIDE)
    elif name == "pearson3":
        shape = min(max(shape, _ML_INSIDE - 2.0), 2.0 - _ML_INSIDE)
    else:
        shape = max(shape, 1.0 + _ML_INSIDE)
    lower, upper = _support(name, shape, scale)
    lowest = float(sample.max()) - upper + _ML_MARGIN
    highest = float(sample.min()) - lower - _ML_MARGIN
    return shape, min(max(loc, lowest), highest), scale


def _maximum_likelihood(
    name: str, data: NDArray[np.float64]
) -> tuple[float, float, float]:
    """Maximum-likelihood ``(shape, loc, scale)`` of a three-parameter distribution.

    ``name`` is ``"gev"``, ``"pearson3"`` or ``"weibull"``. The search runs on the
    standardised sample z = (x - mean) / sd, whose scale is of the order of 1 in any
    unit of x (scipy's own ``fit`` starts from the scale 1 and may stop far from the
    maximum on annual maxima of hundreds of m³/s): Nelder-Mead on the shape, the
    location and the logarithm of the scale from :func:`_ml_start`, over the shapes
    short of the limit of ``_UNBOUNDED_LIKELIHOOD``, run again from the point it found
    until a run gains no more than ``_ML_GAIN`` of log-likelihood. The parameters of x
    are the shape, mean + sd · loc and sd · scale.

    Raises
    ------
    _NoParameters
        ``too_few_values`` (fewer values than 4), ``constant_values``,
        ``unbounded_likelihood`` (the search ends at the limit: the likelihood has no
        maximum) or ``not_converged`` (no run settles, or the end is less likely than
        the start).
    """
    _require_spread(data, _PARAMETER_COUNTS[name] + 1)
    distribution = _DISTRIBUTIONS[name]
    mean = float(np.mean(data))
    spread = float(np.std(data))
    sample = (data - mean) / spread

    def minus_log_likelihood(point: NDArray[np.float64]) -> float:
        if _limit_distance(name, point[0]) <= 0.0:
            return np.inf
        with np.errstate(all="ignore"):
            log_densities = distribution.logpdf(
                sample, point[0], loc=point[1], scale=np.exp(point[2])
            )
            total = -float(np.sum(log_densities))
        return np.inf if np.isnan(total) else total

    shape, loc, scale = _ml_start(name, sample)
    start = np.array([shape, loc, np.log(scale)])
    found = minimize(
        minus_log_likelihood, start, method="Nelder-Mead", options=_ML_NELDER_MEAD
    )
    settled = False
    for _ in range(_ML_RUNS):
        if not np.isfinite(found.fun):
            break
        again = minimize(
            minus_log_likelihood, found.x, method="Nelder-Mead", options=_ML_NELDER_MEAD
        )
        gain = found.fun - again.fun
        if gain > 0.0:
            found = again
        if gain <= _ML_GAIN:
            settled = True
            break
    shape = float(found.x[0])
    if _limit_distance(name, shape) < _ML_EDGE:
        raise _NoParameters(
            "unbounded_likelihood",
            "its likelihood has no maximum: the search ends at "
            f"{_UNBOUNDED_LIKELIHOOD[name]}, with a bound of the distribution at the "
            "closest value, beyond which the likelihood grows without limit",
            shape=shape,
        )
    if not settled or found.fun > minus_log_likelihood(start):
        raise _NoParameters(
            "not_converged",
            f"the search for the maximum of the likelihood did not settle in {_ML_RUNS}"
            " runs",
        )
    return shape, mean + spread * float(found.x[1]), spread * float(np.exp(found.x[2]))


def _by_maximum_likelihood(
    name: str, data: NDArray[np.float64]
) -> tuple[float, float, float]:
    """Parameters ``(shape, loc, scale)`` of distribution ``name``, maximum likelihood.

    The log-normal with location 0 in closed form (``scipy.stats.lognorm.fit`` with
    ``floc=0``: the mean and the standard deviation, divisor n, of ln x), from 3 values
    above 0, not all equal; the others by :func:`_maximum_likelihood`.
    """
    if name != "log_normal":
        return _maximum_likelihood(name, data)
    _require_positive(data)
    _require_spread(data, _PARAMETER_COUNTS[name] + 1)
    shape, _, scale = lognorm.fit(data, floc=0)
    return float(shape), 0.0, float(scale)


SPECS: Final = (MOMENTS, L_MOMENTS)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""
