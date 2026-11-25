"""Interval estimates beside point estimates (Nogat ECO-091).

A result with intervals carries the list ``intervals``, one :class:`ConfidenceInterval`
per confidence level asked, in the order asked: two-sided and central at the level,
its bounds aligned with the estimates (the quantiles of a fit, the percentages of a
duration curve), a bound ``NaN`` (``null`` in JSON) where it is undefined. An
interval that is not computed keeps its level and has its method, bounds and samples
``None``, and the warning :class:`~hydrolog._warnings.IntervalNotComputed` says why.

The intervals of the quantiles of a fitted distribution are formulas declared by their
specs (Nogat's computation standard, ADR-0074): a fit by L-moments by a parametric
bootstrap (:data:`QUANTILE_INTERVAL_BOOTSTRAP`, :func:`quantile_interval_bootstrap`),
a fit by maximum likelihood by the delta method of KZGW (2017)
(:data:`QUANTILE_INTERVAL_DELTA`, :func:`quantile_interval_delta`).
``docs/FORMULAS.md`` shows their equations, constants, ranges, sources and the
simulated coverage of their intervals (CMP-6.11).
"""

from __future__ import annotations

import math
import numbers
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.special import ndtri, polygamma
from scipy.stats import genextreme, pearson3

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import IntervalNotComputed
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
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics.frequency import (
    _ANY_VALUE,
    _DISTRIBUTIONS,
    _HOSKING_WALLIS,
    _KZGW,
    _KZGW_URL,
    _MAXIMA,
    _ML_WEIBULL_SHAPE,
    _PARAMETER_COUNTS,
    _POLANA,
    _RETURN_PERIODS,
    _SHAPE_OF_THE_DISTRIBUTION,
    _SMITH_1985,
    _UNIT,
    _WMO_168,
    _WMO_168_URL,
    _by_l_moments,
    _fitted_variables,
    _not_constant,
    _standardised,
    _within_l_moments,
)

__all__ = [
    "CI_METHODS",
    "QUANTILE_INTERVAL_BOOTSTRAP",
    "QUANTILE_INTERVAL_DELTA",
    "SPECS",
    "BootstrapInterval",
    "ConfidenceInterval",
    "DeltaInterval",
    "confidence_levels",
    "interval_entries",
    "intervals_not_computed",
    "quantile_interval_bootstrap",
    "quantile_interval_delta",
]

CI_METHODS: tuple[str, ...] = ("parametric_bootstrap", "delta", "order_statistics")
"""Values of :attr:`ConfidenceInterval.ci_method` for a computed interval."""


@dataclass
class ConfidenceInterval(JsonResultMixin):
    """The interval of a set of estimates at one confidence level.

    Attributes
    ----------
    confidence_level : float
        The level c in (0, 1) asked: the interval is two-sided and central, each
        tail (1 - c) / 2.
    ci_method : str or None
        ``"parametric_bootstrap"``, ``"delta"`` or ``"order_statistics"`` (the spec
        of the estimate names its formula); ``None`` when not computed.
    ci_lower, ci_upper : NDArray[np.float64] or None
        The bounds, one per estimate in its order; an element is NaN (``null``)
        where the bound is undefined. ``None`` when not computed.
    ci_samples : int or None
        The bootstrap samples kept of those drawn, the same for every level of a
        fit; ``None`` for another method or when not computed.
    """

    confidence_level: float
    ci_method: str | None
    ci_lower: NDArray[np.float64] | None
    ci_upper: NDArray[np.float64] | None
    ci_samples: int | None


def confidence_levels(
    confidence_level: float | Sequence[float] | NDArray[np.float64],
    option: str = "confidence_level",
) -> tuple[float, ...]:
    """Return the levels asked as a tuple: one number or distinct numbers in (0, 1).

    Parameters
    ----------
    confidence_level : float or sequence of float
        One level, or a non-empty list of distinct levels, each in the open
        interval (0, 1).
    option : str, optional
        The name of the option, for ``details.option`` of an error.

    Returns
    -------
    tuple of float
        The levels in the order given.

    Raises
    ------
    InvalidParameterError
        ``details.reason`` ``type`` (neither a number nor a list of numbers, or a
        bool), ``empty`` (an empty list), ``range`` (a level not finite or outside
        (0, 1)) or ``duplicate_level`` (a level given twice).
    """
    asked: list[object]
    if isinstance(confidence_level, numbers.Real):
        asked = [confidence_level]
    elif isinstance(confidence_level, Sequence | np.ndarray) and not isinstance(
        confidence_level, str | bytes
    ):
        asked = list(np.asarray(confidence_level, dtype=object).ravel())
    else:
        raise InvalidParameterError(
            f"Option {option!r}: a number in (0, 1) or a list of such numbers, got "
            f"{confidence_level!r}",
            details={
                "option": option,
                "reason": "type",
                "value": str(confidence_level),
            },
        )
    if not asked:
        raise InvalidParameterError(
            f"Option {option!r}: give at least one confidence level",
            details={"option": option, "reason": "empty", "value": "[]"},
        )
    levels: list[float] = []
    for value in asked:
        if isinstance(value, bool | np.bool_) or not isinstance(value, numbers.Real):
            raise InvalidParameterError(
                f"Option {option!r}: a confidence level is a number, got {value!r}",
                details={"option": option, "reason": "type", "value": str(value)},
            )
        number = float(value)
        if not (math.isfinite(number) and 0.0 < number < 1.0):
            raise InvalidParameterError(
                f"Option {option!r}: a confidence level is a number in the open "
                f"interval (0, 1), got {value!r}",
                details={"option": option, "reason": "range", "value": str(value)},
            )
        if number in levels:
            raise InvalidParameterError(
                f"Option {option!r}: the confidence level {number!r} is given twice",
                details={
                    "option": option,
                    "reason": "duplicate_level",
                    "value": str(number),
                },
            )
        levels.append(number)
    return tuple(levels)


def interval_entries(
    levels: Sequence[float],
    method: str,
    lower: NDArray[np.float64],
    upper: NDArray[np.float64],
    samples: int | None = None,
) -> list[ConfidenceInterval]:
    """Return the computed intervals, one per level, from bounds of shape (levels, n).

    Parameters
    ----------
    levels : sequence of float
        The levels, in the order of the rows of ``lower`` and ``upper``.
    method : str
        One of :data:`CI_METHODS`.
    lower, upper : NDArray[np.float64]
        The bounds, a row per level; NaN where a bound is undefined.
    samples : int or None, optional
        The bootstrap samples kept (``"parametric_bootstrap"`` only).

    Returns
    -------
    list of ConfidenceInterval
    """
    if method not in CI_METHODS:
        raise ValueError(f"{method!r} is not one of {CI_METHODS}")
    lows = np.asarray(lower, dtype=np.float64)
    highs = np.asarray(upper, dtype=np.float64)
    return [
        ConfidenceInterval(
            confidence_level=float(level),
            ci_method=method,
            ci_lower=lows[row].copy(),
            ci_upper=highs[row].copy(),
            ci_samples=samples,
        )
        for row, level in enumerate(levels)
    ]


def intervals_not_computed(levels: Sequence[float]) -> list[ConfidenceInterval]:
    """Return the intervals of levels that are not computed: all but the level null.

    Parameters
    ----------
    levels : sequence of float
        The levels asked, in their order.

    Returns
    -------
    list of ConfidenceInterval
    """
    return [
        ConfidenceInterval(
            confidence_level=float(level),
            ci_method=None,
            ci_lower=None,
            ci_upper=None,
            ci_samples=None,
        )
        for level in levels
    ]


# --- sources and shared declarations ---------------------------------------------

_ADR_0048: Final = Source(
    citation="Hydrolog (2026). ADR-0048: Anderson-Darling critical values by a "
    "parametric bootstrap",
    locator="decision 1: 999 samples of n values drawn from the fitted distribution, "
    "each refitted by the same method, seed 20261118; a sample the method cannot fit "
    "is left out",
    url="https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/"
    "0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md",
)
_ADR_0074: Final = Source(
    citation="Hydrolog (2026). ADR-0074: Intervals of the quantiles and of the median "
    "annual flow-duration curve",
    locator="decisions 1 and 2: the refits of ADR-0048 give the percentile interval, "
    "fewer than 990 kept give none; the delta method of KZGW for maximum likelihood",
    url="https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/"
    "0074-intervals-of-the-quantiles-and-of-the-median-annual-flow-duration-curve.md",
)
_ECO_091: Final = Source(
    citation="Nogat (2026). Decisions of the ecosystem, ECO-091: Intervals beside "
    "point estimates, computed by Hydrolog, shown by Obserwator",
    locator="two-sided and central at each confidence_level asked; Obserwator stores "
    "0.95 and 0.68",
    url="https://github.com/Daldek/Nogat/blob/main/standards/DECISIONS.md",
)
_CMP_SIZES: Final = Source(
    citation="Nogat (2026). Computations: formulas, their limits and their "
    "verification, standard 1.3",
    locator="CMP-6.11: the sample sizes of the ecosystem's use, 30 and 60 values for "
    "annual series",
    url="https://github.com/Daldek/Nogat/blob/main/standards/COMPUTATIONS.md",
)
_EFRON_TIBSHIRANI: Final = Source(
    citation="Efron, B. and Tibshirani, R.J. (1993). An Introduction to the Bootstrap. "
    "Chapman and Hall",
    locator="ch. 6 (the parametric bootstrap), ch. 13 (the percentile interval, the "
    "empirical (B + 1) alpha-th value of the B replications)",
    access="author-provided",
)
_KYSELY: Final = Source(
    citation="Kyselý, J. (2008). A cautionary note on the use of nonparametric "
    "bootstrap for estimating uncertainties in extreme-value models. Journal of "
    "Applied Meteorology and Climatology 47, 3236-3251",
    locator="the parametric bootstrap before the nonparametric one for short samples "
    "of extremes",
    url="https://doi.org/10.1175/2008JAMC1763.1",
    access="author-provided",
)
_R_QUANTILE: Final = Source(
    citation="R Core Team. R: A Language and Environment for Statistical Computing, "
    "stats::quantile, Sample Quantiles (Hyndman and Fan 1996, types 1 to 9)",
    locator="type 6: m = p, p_k = k / (n + 1), the plotting position of Weibull",
    url="https://stat.ethz.ch/R-manual/R-devel/library/stats/html/quantile.html",
)
_KZGW_DELTA: Final = Source(
    citation=_KZGW,
    locator="eq. 3.26-3.27 and ex. 3.2 (Pearson III), eq. 3.41 and ex. 3.3, eq. 2.9 "
    "and table 2.3 (log-normal), eq. 3.56-3.57 and ex. 3.4 (Weibull), pp. 21-55; the "
    "upper bound at beta = 84 % with u_beta = 0.994 (eq. 3.12)",
    url=_KZGW_URL,
)
_STEDINGER: Final = Source(
    citation="Stedinger, J.R., Vogel, R.M. and Foufoula-Georgiou, E. (1993). "
    "Frequency analysis of extreme events. In: Maidment, D.R. (ed.), Handbook of "
    "Hydrology, ch. 18. McGraw-Hill",
    locator="sect. 18.4.2, eqs. 18.4.7-18.4.8, p. 18.30: the variance of the "
    "log-normal quantile by maximum likelihood (the source of KZGW's eq. 2.9)",
    url="https://efi.eng.uci.edu/papers/efg_FA.pdf",
)
_COLES: Final = Source(
    citation="Coles, S. (2001). An Introduction to Statistical Modeling of Extreme "
    "Values. Springer",
    locator="sect. 3.3.2-3.3.3: the observed information of the GEV's maximum "
    "likelihood, the delta method for return levels, regular for xi > -0.5",
    access="author-provided",
)
_HEO: Final = Source(
    citation="Heo, J.-H., Salas, J.D. and Kim, K.-D. (2001). Estimation of "
    "confidence intervals of quantiles for the Weibull distribution. Stochastic "
    "Environmental Research and Risk Assessment 15(4), 284-309",
    locator="the variance of the Weibull quantile by maximum likelihood (KZGW's "
    "eq. 3.57)",
    access="author-provided",
)

_LEVELS: Final = Variable(
    name="confidence_levels",
    symbol="c",
    unit="-",
    kind="real_array",
    description="Confidence levels, distinct: each interval is two-sided and "
    "central, each tail (1 - c) / 2.",
    physical=Range(low=0.0, high=1.0, low_inclusive=False, high_inclusive=False),
    applicability="unstated",
    typical=Range(low=0.68, high=0.95, source=_ECO_091),
)
_VARIABLE_CHOICE: Final = Variable(
    name="variable",
    symbol="v",
    unit="-",
    kind="choice",
    description="What the extremes are: a discharge or another quantity never below "
    "0, such as a precipitation depth, or a stage, whose 0 is the gauge's.",
    choices=("discharge", "stage"),
)


def _bound_output(name: str, symbol: str, text: str) -> Output:
    return Output(
        name=name,
        unit=_UNIT,
        kind="real_array",
        symbol=symbol,
        description=text,
        physical=Range(),
        gaps_allowed=True,
    )


_BOUNDS: Final = (
    _bound_output(
        "lower",
        "L",
        "The lower bound of each level (a row per level in the order given) and "
        "return period; a gap where a bound of a discharge would lie below 0.",
    ),
    _bound_output(
        "upper",
        "U",
        "The upper bound, as the lower.",
    ),
)
_DISTINCT_LEVELS: Final = Constraint(
    name="distinct_levels",
    cls="precondition",
    check=lambda x: (
        np.unique(x.array("confidence_levels")).size
        == x.array("confidence_levels").size
    ),
    text="the confidence levels are distinct",
    source=_ECO_091,
    satisfied={"confidence_levels": [0.95, 0.68]},
    violated={"confidence_levels": [0.95, 0.95]},
)
_INTERVAL_CONVENTION: Final = (
    "two-sided and central at each confidence level c, each tail (1 - c) / 2; the "
    "upper bound at c = 0.68 is KZGW's one-sided upper bound at beta = 84 % (c = 2 "
    "beta - 1); every level of one call from one computation"
)
_SIGN_CONVENTION: Final = (
    "variable discharge (a discharge or another quantity never below 0, such as a "
    "precipitation depth): a bound below 0 is a gap, with the notice "
    "interval_not_computed (below_physical_range) naming its return periods and "
    "levels; stage: no such rule"
)
_SCALED_BOUNDS: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="the samples, the L-moments and the quantiles are loc + scale times those "
    "of the standard distribution, and doubling loc and scale rounds alike",
)


def _nesting(run: Callable[..., Values]) -> None:
    """Assert lower <= upper and the interval of a smaller level inside a larger."""
    levels = [0.5, 0.68, 0.9, 0.95, 0.99]
    out = run(confidence_levels=levels)
    lower, upper = out.array("lower"), out.array("upper")
    zero = np.zeros(lower.shape[1:])  # a gap (NaN) is no bound: np.fmax drops it
    for row in range(len(levels)):
        assert_within(
            np.fmax(lower[row] - upper[row], 0.0),
            zero,
            abs=0.0,
            reason="a lower bound is never above its upper bound",
        )
    for inner, outer in zip(range(len(levels)), range(1, len(levels)), strict=False):
        assert_within(
            np.fmax(lower[outer] - lower[inner], 0.0)
            + np.fmax(upper[inner] - upper[outer], 0.0),
            zero,
            abs=0.0,
            reason="the interval of a smaller level lies inside that of a larger one",
        )


def _level_order(run: Callable[..., Values]) -> None:
    """Assert that the rows follow the levels in the order given."""
    forward = run(confidence_levels=[0.95, 0.68])
    backward = run(confidence_levels=[0.68, 0.95])
    for name in ("lower", "upper"):
        assert_within(
            backward.array(name)[::-1],
            forward.array(name),
            abs=0.0,
            reason="one computation gives every level; the order of the rows is that "
            "of the levels given",
        )


def _signed(
    lower: NDArray[np.float64],
    upper: NDArray[np.float64],
    *,
    discharge: bool,
    levels: NDArray[np.float64],
    periods: NDArray[np.float64],
    distribution: str,
    fit_method: str,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Leave out the bounds of a discharge below 0, with the notice that says so."""
    if not discharge:
        return lower, upper
    below = (lower < 0.0) | (upper < 0.0)
    if not below.any():
        return lower, upper
    rows, columns = np.nonzero(below)
    warnings.warn(
        IntervalNotComputed(
            reason="below_physical_range",
            confidence_levels=[float(levels[row]) for row in sorted(set(rows))],
            distribution=distribution,
            fit_method=fit_method,
            return_periods=[float(periods[col]) for col in sorted(set(columns))],
            complete_years=None,
            required_years=None,
        ),
        stacklevel=3,
    )
    return np.where(lower < 0.0, np.nan, lower), np.where(upper < 0.0, np.nan, upper)


# --- the parametric bootstrap of an L-moments fit ----------------------------------

_BOOTSTRAP_CONSTANTS: Final = (
    Constant(
        name="samples",
        value=999.0,
        unit="-",
        source=_ADR_0048,
        symbol="B",
    ),
    Constant(
        name="seed",
        value=20261118.0,
        unit="-",
        source=_ADR_0048,
        symbol="s",
    ),
    Constant(
        name="least_kept",
        value=990.0,
        unit="-",
        source=_ADR_0074,
        symbol="K_{min}",
    ),
)
_SAMPLES: Final = int(_BOOTSTRAP_CONSTANTS[0].value)
_SEED: Final = int(_BOOTSTRAP_CONSTANTS[1].value)
_LEAST_KEPT: Final = int(_BOOTSTRAP_CONSTANTS[2].value)


class _Refits(NamedTuple):
    """The bootstrap samples of a fit and the parameters of those refitted.

    ``samples`` holds the drawn samples sorted ascending, a row each; ``kept`` the
    rows the L-moments could fit; ``parameters`` their ``(shape, loc, scale)``, a row
    per kept sample. The arrays are read-only: the cache shares them.
    """

    samples: NDArray[np.float64]
    kept: NDArray[np.intp]
    parameters: NDArray[np.float64]


@lru_cache(maxsize=8)
def _bootstrap_refits(
    name: str, shape: float, loc: float, scale: float, size: int
) -> _Refits:
    """Draw the bootstrap samples of a fit and refit each by L-moments (cached).

    The samples of the critical values of A² of an L-moments fit (ADR-0048) and of
    the interval of its quantiles (spec ``quantile_interval_bootstrap``): ``samples``
    samples of ``size`` values drawn from the fitted distribution with the seed
    ``seed``, sorted; a sample the L-moments cannot fit is left out. Drawn from a
    continuous distribution, the samples have distinct values (and those of the
    log-normal positive ones), so only their L-moments can fail; a sample whose
    values the floats cannot tell apart (a scale near the smallest float) or that
    overflows is left out too.
    """
    rng = np.random.default_rng(_SEED)
    with np.errstate(all="ignore"):  # a sample that overflows is left out below
        draws = _DISTRIBUTIONS[name].rvs(
            shape, loc, scale, size=(_SAMPLES, size), random_state=rng
        )
    samples = np.sort(np.asarray(draws, dtype=np.float64), axis=1)
    usable = np.isfinite(samples).all(axis=1) & (samples[:, -1] > samples[:, 0])
    kept = np.array(
        [
            row
            for row in np.flatnonzero(usable)
            if _within_l_moments(name, samples[row])
        ],
        dtype=np.intp,
    )
    parameters = np.array(
        [_by_l_moments(name, samples[row]) for row in kept], dtype=np.float64
    ).reshape(-1, 3)
    for array in (samples, kept, parameters):
        array.flags.writeable = False
    return _Refits(samples, kept, parameters)


def _kept(x: Values) -> int:
    """Return the number of samples the L-moments refit, for the precondition."""
    refits = _bootstrap_refits(
        x.choice("distribution"),
        x.real("shape"),
        x.real("loc"),
        x.real("scale"),
        x.integer("size"),
    )
    return int(refits.kept.size)


QUANTILE_INTERVAL_BOOTSTRAP: Final = FormulaSpec(
    name="quantile_interval_bootstrap",
    title="Interval of the quantiles of an L-moments fit by a parametric bootstrap "
    "(percentile interval)",
    function="hydrolog.statistics.intervals.quantile_interval_bootstrap",
    family="statistic",
    equation=(
        "B samples of n values drawn from the fitted distribution F(shape, loc, "
        "scale) with numpy's default_rng(seed), each sorted and refitted by "
        "L-moments (fit_l_moments), a sample whose L-moments the distribution cannot "
        "take left out; the K kept refits give per return period T the quantiles "
        "Q*_b(T) = F^-1(1 - 1/T; refit b); lower = q6((1 - c) / 2), upper = q6((1 + "
        "c) / 2), q6(P) the empirical quantile of type 6: h = (K + 1) P, Q*(j) + (h "
        "- j) (Q*(j + 1) - Q*(j)) with j = floor(h) of the ascending Q*, Q*(1) for h "
        "< 1 and Q*(K) for h >= K; K < K_min is refused"
    ),
    latex=(
        r"\hat{Q}^{*}_{b}(T) = F^{-1}\left(1 - \tfrac{1}{T};\ \hat\theta^{*}_{b}"
        r"\right),\ b = 1 \dots K;\qquad [L, U] = \left[\hat{Q}^{*}_{((K + 1)"
        r"(1 - c)/2)},\ \hat{Q}^{*}_{((K + 1)(1 + c)/2)}\right]"
    ),
    variables=(
        *_fitted_variables()[1:],
        Variable(
            name="size",
            symbol="n",
            unit="-",
            kind="integer",
            description="Values in the sample the distribution was fitted to.",
            physical=Range(
                low=1.0,
                test_high=200.0,
                test_reason="two hundred values exceed the longest records of "
                "annual extremes the ecosystem reads (IMGW-PIB's daily series begin "
                "in 1951); the cost of the bootstrap grows with n",
            ),
            applicability="unstated",
            typical=Range(low=30.0, high=60.0, source=_CMP_SIZES),
        ),
        _RETURN_PERIODS,
        _LEVELS,
        _VARIABLE_CHOICE,
    ),
    outputs=(
        *_BOUNDS,
        Output(
            name="samples",
            unit="-",
            kind="integer",
            symbol="K",
            description="The bootstrap samples kept: refitted by L-moments.",
            physical=Range(low=float(_LEAST_KEPT), high=float(_SAMPLES)),
        ),
    ),
    sources=(_EFRON_TIBSHIRANI, _HOSKING_WALLIS, _KYSELY, _R_QUANTILE, _ADR_0048),
    constraints=(
        _SHAPE_OF_THE_DISTRIBUTION,
        Constraint(
            name="enough_values",
            cls="precondition",
            check=lambda x: x.integer("size") >= 3,
            text="n >= 3: the L-skewness of a sample needs 3 values",
            source=_HOSKING_WALLIS,
            satisfied={"size": 3},
            violated={"size": 2},
        ),
        _DISTINCT_LEVELS,
        Constraint(
            name="enough_refits",
            cls="precondition",
            check=lambda x: _kept(x) >= _LEAST_KEPT,
            text="at least K_min = 990 of the B = 999 samples are refitted by "
            "L-moments",
            source=_ADR_0074,
            satisfied={"distribution": "weibull", "shape": 3.0, "loc": 0.0, "size": 30},
            violated={"distribution": "weibull", "shape": 5.0, "loc": 0.0, "size": 30},
        ),
    ),
    constants=_BOOTSTRAP_CONSTANTS,
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"loc": 1.0, "scale": 1.0},
                outputs={"lower": 1.0, "upper": 1.0},
                tolerance=_SCALED_BOUNDS,
            ),
        ),
        limits=(
            Limit(
                name="nested_levels",
                text="lower <= upper, and the interval of a smaller level lies "
                "inside that of a larger one",
                check=_nesting,
            ),
            Limit(
                name="order_of_the_levels",
                text="the rows follow the levels in the order given, from the same "
                "refits",
                check=_level_order,
            ),
        ),
    ),
    validation="none: an interval of an estimator; its coverage, simulated from the "
    "distributions it fits at 30 and 60 values, is reported under the formula "
    "(CMP-6.11)",
    formula_version=1,
    status="oracle only",
    conventions=(
        _INTERVAL_CONVENTION,
        "a parametric bootstrap, the percentile interval of Efron and Tibshirani "
        "(1993, ch. 13): B = 999 samples of n values from the fitted distribution, "
        "numpy's default_rng with the seed 20261118, the same samples and refits as "
        "the critical values of A² of the fit (ADR-0048)",
        "the empirical quantile of type 6 of Hyndman and Fan (1996), positions i / "
        "(K + 1): numpy's method 'weibull', R's quantile type 6 (lmomco's empirical "
        "limits); with K = 999 the bounds at c = 0.95 are the 25th refit from each "
        "end and at 0.68 the 160th, Efron and Tibshirani's ((B + 1) alpha)th value; "
        "a level beyond the reach of K refits, (K + 1)(1 - c) / 2 < 1, takes the "
        "smallest and the largest",
        "a sample whose L-moments the distribution cannot take is left out, not "
        "drawn again (lmomco's qua2ci.simple draws again), and counted: samples is "
        "the K kept; fewer than 990 is refused (enough_refits)",
        "the refits of fit_l_moments, the quantiles by scipy's isf at the exceedance "
        "1/T as the quantile specs; scipy's parameters (the GEV c is -xi of Coles)",
        _SIGN_CONVENTION,
    ),
    assumptions=(
        "the fitted distribution stands for the parent: the interval is the spread "
        "of the L-moments estimator over samples of n values from it",
        "the annual extremes are independent and identically distributed",
    ),
    traps={
        "singular_at_bound": "range case return_periods_years-physical_low_inside: T "
        "just above 1 puts the quantiles of the refits in the far lower tail, finite",
        "exp_overflow": "range case shape-physical_high_test_bound is refused by "
        "enough_refits or gives finite quantiles: the refits keep the shapes of "
        "fit_l_moments",
    },
    oracles=(
        Oracle(
            kind="frozen",
            description="R lmomco 2.5.8 qua2ci.simple (called by genci.simple per "
            "probability): the empirical limits of 20000 samples of 34 values drawn "
            "from the L-moments fits of the Polana maxima and refitted by L-moments, T "
            "= 2 to 1000 years, c = 0.95 and 0.68; R 4.5.3, 2026-11-25",
            test="tests/oracles/interval_lmomco_r.csv (tests/unit/"
            "test_interval_oracles.py)",
            conventions=(
                "lmomco's empdist limits are the empirical quantiles (1 -+ c)/2 of its "
                "simulated quantiles by R's quantile type 6, Hydrolog's numpy method "
                "weibull; its lwr/upr, of a generalized normal fitted to them by "
                "L-moments (edist gno), are another convention, within 2.9 % of them",
                "lmomco redraws a sample it cannot fit, Hydrolog leaves it out (none "
                "of either here)",
                "different generators: lmomco's limit lies within Hydrolog's quantiles "
                "at the tail probabilities q -+ 4 sqrt(q (1 - q) (1/B + 1/nsim))",
                "lmomco's gev (xi, alpha, kappa), pe3 (mu, sigma, gamma), ln3 (0, "
                "mulog, sigmalog) and wei (zeta, beta, delta) are scipy's "
                "genextreme(kappa, xi, alpha), pearson3(gamma, mu, sigma), "
                "lognorm(sigmalog, 0, exp(mulog)) and weibull_min(delta, -zeta, beta)",
            ),
        ),
    ),
    base={
        "distribution": "gev",
        "shape": -0.18,
        "loc": 20.9,
        "scale": 16.4,
        "size": 34,
        "return_periods_years": [2.0, 10.0, 100.0],
        "confidence_levels": [0.95, 0.68],
        "variable": "discharge",
    },
)


class BootstrapInterval(NamedTuple):
    """Interval of the quantiles of an L-moments fit (spec quantile_interval_bootstrap).

    ``lower`` and ``upper`` have a row per level and a column per return period;
    ``samples`` is the number of bootstrap samples kept.
    """

    lower: NDArray[np.float64]
    upper: NDArray[np.float64]
    samples: int


def quantile_interval_bootstrap(
    distribution: str,
    shape: float,
    loc: float,
    scale: float,
    size: int,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
    confidence_levels: NDArray[np.float64] | list[float] | tuple[float, ...],
    variable: str,
) -> BootstrapInterval:
    """Return the bootstrap interval of quantiles, spec quantile_interval_bootstrap.

    Parameters
    ----------
    distribution : str
        ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.
    shape, loc, scale : float
        The parameters of the fit by L-moments (scipy's).
    size : int
        Values in the sample fitted.
    return_periods_years : array_like of float
        Return periods [years].
    confidence_levels : array_like of float
        Distinct confidence levels.
    variable : str
        ``"discharge"`` or ``"stage"``.

    Returns
    -------
    BootstrapInterval
        The bounds per level and return period and the samples kept.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec (``enough_refits`` among its
        preconditions).

    Warns
    -----
    IntervalNotComputed
        If bounds of a discharge are left out as negative.
    """
    x = checked_inputs(
        QUANTILE_INTERVAL_BOOTSTRAP,
        distribution=distribution,
        shape=shape,
        loc=loc,
        scale=scale,
        size=size,
        return_periods_years=return_periods_years,
        confidence_levels=confidence_levels,
        variable=variable,
    )
    name = x.choice("distribution")
    refits = _bootstrap_refits(
        name, x.real("shape"), x.real("loc"), x.real("scale"), x.integer("size")
    )
    periods = x.array("return_periods_years")
    levels = x.array("confidence_levels")
    shapes, locs, scales = (refits.parameters[:, k, None] for k in range(3))
    with np.errstate(all="ignore"):
        quantiles = np.asarray(
            _DISTRIBUTIONS[name].isf(1.0 / periods[None, :], shapes, locs, scales),
            dtype=np.float64,
        )
    lower = np.quantile(quantiles, (1.0 - levels) / 2.0, axis=0, method="weibull")
    upper = np.quantile(quantiles, (1.0 + levels) / 2.0, axis=0, method="weibull")
    lower, upper = _signed(
        lower,
        upper,
        discharge=x.choice("variable") == "discharge",
        levels=levels,
        periods=periods,
        distribution=name,
        fit_method="l_moments",
    )
    out = checked_outputs(
        QUANTILE_INTERVAL_BOOTSTRAP,
        {"lower": lower, "upper": upper, "samples": int(refits.kept.size)},
    )
    return BootstrapInterval(
        out.array("lower"), out.array("upper"), out.integer("samples")
    )


# --- the delta method of a maximum-likelihood fit ----------------------------------

_SMALL_SKEW: Final = 0.01
"""Below this |skewness| Pearson III's frequency factor is its Cornish-Fisher series."""
_SKEW_STEP: Final = 1e-3
"""The step of the central differences of the frequency factor in the skewness."""
_LARGE_SHAPE: Final = 10.0
"""Above this gamma shape lambda (lambda psi'(lambda) - 1) is its asymptotic series."""
_HESSIAN_STEP: Final = 1e-4
"""The step of the central differences of the GEV log-likelihood (standardised)."""
_REGULAR_GEV: Final = 0.5
"""scipy's GEV c below which its maximum likelihood is regular (xi > -0.5)."""


def _z(levels: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return z = Phi^-1((1 + c) / 2) from the tail (1 - c) / 2, which keeps digits."""
    return np.asarray(-ndtri((1.0 - levels) / 2.0), dtype=np.float64)


def _upper_normal(periods: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return u_p = Phi^-1(1 - 1/T) from the exceedance 1/T."""
    return np.asarray(-ndtri(1.0 / periods), dtype=np.float64)


def _lambda_d(skew: float) -> float:
    """Return lambda (lambda psi'(lambda) - 1) of the gamma shape lambda = 4 / G**2.

    For lambda > 10 its asymptotic series in t = 1 / lambda (from that of the
    trigamma function, Abramowitz and Stegun 6.4.12), 1/2 + t/6 - t**3/30 +
    t**5/42 - t**7/30 + 5 t**9/66, whose limit 1/2 at G = 0 is the normal one;
    below, directly.
    """
    t = skew * skew / 4.0
    if t < 1.0 / _LARGE_SHAPE:
        return (
            0.5 + t / 6.0 - t**3 / 30.0 + t**5 / 42.0 - t**7 / 30.0 + 5.0 * t**9 / 66.0
        )
    shape = 1.0 / t
    return shape * (shape * float(polygamma(1, shape)) - 1.0)


def _frequency_factor(
    skew: float, periods: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return Pearson III's frequency factor K(G, 1/T) and its derivative dK/dG.

    K is the quantile of the standardised distribution at the exceedance 1/T. Below
    |G| = 0.01 both come from the Cornish-Fisher expansion of the gamma quantile to
    G**3 (its cumulants G, 1.5 G**2 and 3 G**3); above, K is scipy's and dK/dG its
    central differences of steps h and h/2 combined by Richardson's extrapolation.
    """
    if abs(skew) < _SMALL_SKEW:
        u = _upper_normal(periods)
        u2 = u * u
        c1 = (u2 - 1.0) / 6.0
        c2 = (u2 * u - 3.0 * u) / 16.0 - (2.0 * u2 * u - 5.0 * u) / 36.0
        c3 = (
            (u2 * u2 - 6.0 * u2 + 3.0) / 40.0
            - (u2 * u2 - 5.0 * u2 + 2.0) / 16.0
            + (12.0 * u2 * u2 - 53.0 * u2 + 17.0) / 324.0
        )
        factor = u + skew * (c1 + skew * (c2 + skew * c3))
        return factor, c1 + skew * (2.0 * c2 + 3.0 * skew * c3)
    exceedance = 1.0 / periods

    def k(g: float) -> NDArray[np.float64]:
        return np.asarray(pearson3.isf(exceedance, g), dtype=np.float64)

    def central(h: float) -> NDArray[np.float64]:
        return (k(skew + h) - k(skew - h)) / (2.0 * h)

    wide, narrow = central(_SKEW_STEP), central(_SKEW_STEP / 2.0)
    return k(skew), (4.0 * narrow - wide) / 3.0


def _pearson3_sigma(
    skew: float, scale: float, size: int, periods: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return sigma(Q_T) of Pearson III with its bound held (KZGW eq. 3.27).

    phi**2 / (alpha**2 N) with lambda = 4 / G**2 and alpha = 2 / (scale |G|) equals
    scale**2 / N [(1 + G K / 2)**2 + (K + G dK/dG)**2 / (4 lambda (lambda psi' - 1))],
    without the cancellation of order lambda of eq. 3.27's numerator as G -> 0.
    """
    factor, slope = _frequency_factor(skew, periods)
    variance = (1.0 + skew * factor / 2.0) ** 2 + (factor + skew * slope) ** 2 / (
        4.0 * _lambda_d(skew)
    )
    return np.asarray(scale * np.sqrt(variance / size), dtype=np.float64)


_GAMMA_PRIME_2: Final = 1.0 - float(np.euler_gamma)
"""Gamma'(2) = 1 - Euler's gamma, the mean of the standard Gumbel distribution of
minima taken with the sign of eq. 3.57."""


def _weibull_sigma(
    shape: float, excess: NDArray[np.float64], size: int, periods: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return sigma(Q_T) of the Weibull distribution with its bound held (eq. 3.57)."""
    reduced = np.log(np.log(periods))  # ln(-ln p) at the exceedance p = 1/T
    gumbel = np.sqrt(1.0 + (_GAMMA_PRIME_2 - reduced) ** 2 / (math.pi**2 / 6.0))
    return np.asarray(excess / (shape * math.sqrt(size)) * gumbel, dtype=np.float64)


def _small_series(a: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return (1 + (a - 1) e**a) / a**2, 1/2 + a/3 + a**2/8 + a**3/30 near a = 0."""
    small = np.abs(a) < 1e-3
    safe = np.where(small, 1.0, a)
    em1 = np.expm1(safe)
    direct = (safe * em1 - (em1 - safe)) / (safe * safe)
    series = 0.5 + a / 3.0 + a * a / 8.0 + a**3 / 30.0
    return np.asarray(np.where(small, series, direct), dtype=np.float64)


def _expm1_ratio(a: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return expm1(a) / a, 1 at a = 0."""
    small = np.abs(a) < 1e-8
    safe = np.where(small, 1.0, a)
    return np.asarray(np.where(small, 1.0 + a / 2.0, np.expm1(safe) / safe))


class _Information(NamedTuple):
    """The covariance of the GEV's parameters of a standardised sample, its scale."""

    covariance: NDArray[np.float64]
    standard: tuple[float, float, float]
    spread: float


def _gev_log_likelihood(
    sample: NDArray[np.float64], point: NDArray[np.float64]
) -> float:
    """Return the GEV log-likelihood of a sample at (c, loc, scale); -inf off it."""
    with np.errstate(all="ignore"):
        log_densities = genextreme.logpdf(
            sample, point[0], loc=point[1], scale=point[2]
        )
    total = float(np.sum(log_densities))
    return total if math.isfinite(total) else -math.inf


@lru_cache(maxsize=32)
def _gev_information(
    sample: bytes, shape: float, loc: float, scale: float
) -> _Information | None:
    """Return the inverse observed information of a GEV fit, or None (not regular).

    On the standardised sample z = (x / 2**e - centre) / spread of
    :func:`~hydrolog.statistics.frequency._standardised`, whose parameters are (c,
    (loc / 2**e - centre) / spread, scale / (2**e spread)): the Hessian of the
    log-likelihood by central differences (19 evaluations), its negative the
    observed information, inverted. None where c >= 0.5, a log-likelihood near the
    point is not finite, or the information is not positive definite.
    """
    data = np.frombuffer(sample, dtype=np.float64)
    if not shape < _REGULAR_GEV:
        return None
    standard, centre, spread, exponent = _standardised(data)
    unit = math.ldexp(spread, exponent)
    theta = np.array(
        [shape, (math.ldexp(loc, -exponent) - centre) / spread, scale / unit]
    )
    steps = _HESSIAN_STEP * np.array([1.0, 1.0, max(theta[2], 1e-12)])
    centre_value = _gev_log_likelihood(standard, theta)
    hessian = np.empty((3, 3))
    for i in range(3):
        up, down = theta.copy(), theta.copy()
        up[i] += steps[i]
        down[i] -= steps[i]
        hessian[i, i] = (
            _gev_log_likelihood(standard, up)
            - 2.0 * centre_value
            + _gev_log_likelihood(standard, down)
        ) / steps[i] ** 2
        for j in range(i):
            corners = []
            for si, sj in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                moved = theta.copy()
                moved[i] += si * steps[i]
                moved[j] += sj * steps[j]
                corners.append(_gev_log_likelihood(standard, moved))
            value = (corners[0] - corners[1] - corners[2] + corners[3]) / (
                4.0 * steps[i] * steps[j]
            )
            hessian[i, j] = hessian[j, i] = value
    if not np.all(np.isfinite(hessian)):
        return None
    try:
        factor = np.linalg.cholesky(-hessian)
    except np.linalg.LinAlgError:
        return None
    inverse = np.linalg.inv(factor)
    covariance = inverse.T @ inverse
    return _Information(covariance, (theta[0], theta[1], theta[2]), unit)


def _gev_negated(x: Values) -> tuple[NDArray[np.float64], float]:
    """Return the sample and the location of the GEV fitted to it (maxima or minima)."""
    values = x.array("values")
    if x.choice("extremes") == "minima":
        return 0.0 - values, 0.0 - x.real("loc")
    return values, x.real("loc")


def _information(x: Values) -> _Information | None:
    """Return the information of the GEV of the inputs (None: not regular)."""
    sample, loc = _gev_negated(x)
    contiguous = np.ascontiguousarray(sample, dtype=np.float64)
    return _gev_information(contiguous.tobytes(), x.real("shape"), loc, x.real("scale"))


def _gev_sigma(
    information: _Information, periods: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return sigma(Q_T) = sqrt(g' V g) of the GEV, in the unit of the sample."""
    shape, _, scale = information.standard
    reduced = np.log(-np.log1p(-1.0 / periods))  # L = ln y, y = -ln(1 - 1/T)
    a = shape * reduced
    gradient = np.stack(
        [
            -scale * reduced**2 * _small_series(a),
            np.ones_like(reduced),
            -reduced * _expm1_ratio(a),
        ]
    )
    variance = np.einsum("ip,ij,jp->p", gradient, information.covariance, gradient)
    return np.asarray(information.spread * np.sqrt(variance), dtype=np.float64)


def _regular(x: Values) -> bool:
    """Whether the delta method holds: a GEV regular at the point, any other."""
    return x.choice("distribution") != "gev" or _information(x) is not None


def _likelihood_shape(x: Values) -> bool:
    """Whether the shape is one maximum likelihood finds (frequency._limit_distance)."""
    name, shape = x.choice("distribution"), x.real("shape")
    if name == "gev":
        return -1.0 < shape < 1.0
    if name == "pearson3":
        return abs(shape) < 2.0
    if name == "weibull":
        return 1.0 < shape < _ML_WEIBULL_SHAPE
    return True


_POLANA_GEV_ML: Final = {"shape": -0.4061, "loc": 19.528, "scale": 13.6944}
"""The Polana maxima's GEV by maximum likelihood, rounded: the typical point."""


def _pearson3_normal_limit(run: Callable[..., Values]) -> None:
    """Assert that Pearson III at a skewness of 0 is the normal interval."""
    periods = np.array([1.5, 2.0, 10.0, 100.0, 1000.0])
    out = run(
        distribution="pearson3",
        shape=0.0,
        loc=30.0,
        scale=10.0,
        return_periods_years=list(periods),
        confidence_levels=[0.95],
        variable="stage",
    )
    u = _upper_normal(periods)
    size = len(_POLANA)
    half = float(_z(np.array([0.95]))[0]) * 10.0 * np.sqrt((1.0 + u * u / 2.0) / size)
    assert_within(
        out.array("upper")[0],
        30.0 + 10.0 * u + half,
        rel=1e-13,
        abs=1e-12,
        reason="the normal distribution's mean and standard deviation by maximum "
        "likelihood: var Q_T = sigma**2 / N (1 + u_p**2 / 2) (Stedinger et al. "
        "1993); scipy's normal quantile keeps about 15 digits",
    )
    near = run(
        distribution="pearson3",
        shape=1e-9,
        loc=30.0,
        scale=10.0,
        return_periods_years=list(periods),
        confidence_levels=[0.95],
        variable="stage",
    )
    assert_within(
        near.array("upper")[0],
        out.array("upper")[0],
        rel=1e-8,
        abs=1e-12,
        reason="a skewness of 1e-9 moves the quantile and its sigma by about 1e-9 "
        "times u_p**2 / 6",
    )


QUANTILE_INTERVAL_DELTA: Final = FormulaSpec(
    name="quantile_interval_delta",
    title="Interval of the quantiles of a maximum-likelihood fit by the delta method "
    "(KZGW 2017)",
    function="hydrolog.statistics.intervals.quantile_interval_delta",
    family="statistic",
    equation=(
        "z = Phi^-1((1 + c) / 2), p = 1/T, N values; log-normal: loc + (Q_T - loc) "
        "exp(-+ z s / sqrt(N) sqrt(1 + u_p**2 / 2)), u_p = Phi^-1(1 - p) (eq. 3.41, "
        "2.9); Pearson III: Q_T -+ z sigma_T, sigma_T**2 = phi**2 / (alpha**2 N), "
        "phi**2 = (lambda t'**2 - 2 t' t + psi'(lambda) t**2) / (lambda psi'(lambda) "
        "- 1) with lambda = 4 / G**2, alpha = 2 / (scale |G|), t the standard gamma "
        "quantile and t' its derivative in lambda (eq. 3.26-3.27), evaluated as "
        "sigma_T**2 = scale**2 / N [(1 + G K / 2)**2 + (K + G dK/dG)**2 / (4 lambda "
        "(lambda psi'(lambda) - 1))], K = (Q_T - loc) / scale, at G = 0 scale**2 / N "
        "(1 + u_p**2 / 2); Weibull: Q_T -+ z (Q_T - loc) / (k sqrt(N)) sqrt(1 + "
        "(Gamma'(2) - ln(-ln p))**2 / (pi**2 / 6)) (eq. 3.56-3.57); GEV: Q_T -+ z "
        "sqrt(g' V g), V the inverse of the observed information of (c, loc, "
        "scale), the negative Hessian of the log-likelihood by central differences, "
        "g the gradient of Q_T; minima: the GEV of the negated minima, its bounds "
        "negated and swapped; a bound of a discharge below 0 is a gap"
    ),
    latex=(
        r"Q_T \mp z\,\sigma_T,\quad z = \Phi^{-1}\left(\tfrac{1 + c}{2}\right);\quad"
        r"\sigma_T^2 = \frac{\varphi^2(p, \lambda)}{\alpha^2 N},\ \varphi^2 = "
        r"\frac{\lambda t'^2 - 2 t' t + \psi'(\lambda) t^2}{\lambda\psi'(\lambda) - "
        r"1};\quad \sigma_T = \frac{Q_T - \varepsilon}{k\sqrt{N}}\sqrt{1 + "
        r"\frac{(\Gamma'(2) - \ln(-\ln p))^2}{\pi^2/6}};\quad \varepsilon + (Q_T - "
        r"\varepsilon)\,e^{\mp z \frac{s}{\sqrt{N}}\sqrt{1 + u_p^2/2}};\quad "
        r"\sigma_T^2 = \nabla Q_T^{\top} "
        r"I_o^{-1} \nabla Q_T"
    ),
    variables=(
        Variable(
            name="values",
            symbol="x_i",
            unit=_UNIT,
            kind="real_array",
            description="The sample the distribution was fitted to by maximum "
            "likelihood: annual maxima, or annual minima (extremes minima).",
            physical=_ANY_VALUE,
            applicability="unstated",
            typical=_MAXIMA,
        ),
        *_fitted_variables()[1:],
        _RETURN_PERIODS,
        _LEVELS,
        _VARIABLE_CHOICE,
        Variable(
            name="extremes",
            symbol="e",
            unit="-",
            kind="choice",
            description="Maxima, or minima fitted as the GEV of the negated minima "
            "(fisher_tippett_minima: its location is the minima's).",
            choices=("maxima", "minima"),
        ),
    ),
    outputs=_BOUNDS,
    sources=(_KZGW_DELTA, _STEDINGER, _COLES, _HEO),
    constraints=(
        _SHAPE_OF_THE_DISTRIBUTION,
        Constraint(
            name="enough_values",
            cls="precondition",
            check=lambda x: (
                x.array("values").size > _PARAMETER_COUNTS[x.choice("distribution")]
            ),
            text="N > p, the parameters of the fit: N >= 3 for the log-normal, N >= 4 "
            "for the others",
            source=Source(
                citation=_SMITH_1985,
                locator="n values fit n parameters exactly, where the likelihood has "
                "no maximum",
                access="author-provided",
            ),
            satisfied={"values": [1.0, 2.0, 4.0, 8.0, 16.0]},
            violated={"values": [1.0, 2.0, 4.0]},
            boundary={"values": [1.0, 2.0, 4.0, 8.0]},
        ),
        _not_constant(
            Source(
                citation=_WMO_168,
                locator="sect. 5.5: the likelihood of values all equal grows without "
                "limit as the scale falls to 0",
                url=_WMO_168_URL,
            ),
            # three values tied at the smallest leave a sample the GEV's information
            # is regular at
            satisfied=(5.0, 6.0, 6.0, 7.0),
        ),
        Constraint(
            name="shape_of_a_likelihood_maximum",
            cls="precondition",
            check=_likelihood_shape,
            text="the shapes where the search of fit_maximum_likelihood finds a "
            "maximum: GEV -1 < c < 1, Pearson III |G| < 2, Weibull 1 < k < 50",
            source=Source(
                citation=_SMITH_1985,
                locator="the density infinite at the bound of the support (GEV c >= "
                "1, Pearson III |G| >= 2, Weibull k <= 1) leaves the likelihood "
                "without a maximum",
                access="author-provided",
            ),
            satisfied={"distribution": "pearson3", "shape": 1.8, "loc": 34.0},
            violated={"distribution": "pearson3", "shape": 2.0, "loc": 34.0},
            boundary={"distribution": "pearson3", "shape": 2.0, "loc": 34.0},
            boundary_holds=False,
        ),
        Constraint(
            name="minima_of_the_gev",
            cls="precondition",
            check=lambda x: (
                x.choice("extremes") == "maxima" or x.choice("distribution") == "gev"
            ),
            text="minima only by the GEV of the negated minima",
            source=Source(
                citation="WMO (2008). Manual on Low-flow Estimation and Prediction, "
                "Operational Hydrology Report No. 50, WMO-No. 1029",
                locator="sect. 7.5: the GEV of minima, min(x) = -max(-x)",
                url="https://library.wmo.int/idurl/4/32176",
            ),
            satisfied={"extremes": "minima"},
            violated={"extremes": "minima", "distribution": "weibull", "shape": 1.2},
        ),
        _DISTINCT_LEVELS,
        Constraint(
            name="regular_likelihood",
            cls="precondition",
            check=_regular,
            text="a GEV regular at the point: c < 0.5 (xi > -0.5) and its observed "
            "information positive definite",
            source=Source(
                citation=_SMITH_1985,
                locator="the maximum-likelihood estimators of the GEV are regular, "
                "with the usual asymptotic normality, for xi > -0.5",
                access="author-provided",
            ),
            satisfied={"shape": -0.4},
            violated={"shape": 0.5},
            boundary={"shape": 0.5},
            boundary_holds=False,
        ),
    ),
    constants=(
        Constant(
            name="gamma_prime_2",
            value=_GAMMA_PRIME_2,
            unit="-",
            source=_KZGW_DELTA,
            symbol=r"\Gamma'(2)",
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0, "loc": 1.0, "scale": 1.0},
                outputs={"lower": 1.0, "upper": 1.0},
                tolerance=Tolerance(
                    abs=1e-300,
                    rel=4.5e-15,
                    reason="the closed forms scale with loc and scale, and the GEV's "
                    "information is that of the sample divided by a power of two; "
                    "the quantile and sigma round alike within a few ulp",
                ),
            ),
        ),
        limits=(
            Limit(
                name="nested_levels",
                text="lower <= upper, and the interval of a smaller level lies "
                "inside that of a larger one",
                check=_nesting,
            ),
            Limit(
                name="order_of_the_levels",
                text="the rows follow the levels in the order given, from one sigma",
                check=_level_order,
            ),
            Limit(
                name="normal_limit",
                text="Pearson III at G = 0 (and 1e-9) is the normal distribution's "
                "interval, sigma**2 / N (1 + u_p**2 / 2)",
                check=_pearson3_normal_limit,
            ),
        ),
    ),
    validation="none: an interval of an estimator; its coverage, simulated from the "
    "distributions it fits at 30 and 60 values, is reported under the formula "
    "(CMP-6.11)",
    formula_version=1,
    status="referenced",
    conventions=(
        _INTERVAL_CONVENTION,
        "the delta method as KZGW (2017) applies it: the bound of the support held at "
        "its estimate (Pearson III's loc - 2 scale / G, the Weibull's loc, the "
        "log-normal's loc, 0 in Hydrolog's fits) and the expected information of "
        "the two other parameters in closed form: Pearson III of the gamma's lambda "
        "and alpha, the Weibull of ln(x - loc) as the Gumbel distribution of minima, "
        "the log-normal of the normal mean and standard deviation of ln(x - loc), "
        "the interval taken on that scale; the GEV by the observed information of "
        "its three parameters",
        "the parameters of fit_maximum_likelihood: the log-normal's s with the divisor "
        "N (KZGW's eq. 2.6 divides by N - 1); N the number of values",
        "KZGW's u_beta = 0.994 at beta = 84 % is z at c = 0.68, 0.99446 unrounded",
        "Pearson III's eq. 3.27 rearranged without its cancellation of order lambda "
        "as G -> 0: dK/dG by central differences of scipy's pearson3.isf in G, steps "
        "1e-3 and 5e-4 combined by Richardson's extrapolation, for |G| >= 0.01, "
        "below by the Cornish-Fisher expansion of the gamma quantile to G**3; "
        "lambda (lambda psi'(lambda) - 1) by its asymptotic series above lambda = "
        "10; a negative G by the mirror distribution, the same expression",
        "the Weibull's eq. 3.57 applied to the quantile above the bound, Q_T - loc "
        "(the two-parameter quantile it is derived for); KZGW's ex. 3.4 applies it "
        "to Q_T (5.24 against 4.88 m3/s at p = 10 %), so ex. 3.4 is no reference case "
        "until Heo et al. (2001), the source of eq. 3.57, are read (CMP-5.2; closed "
        "access on 2026-11-25)",
        "the GEV's observed information by central differences of the "
        "log-likelihood of the standardised sample (the search's of "
        "fit_maximum_likelihood), steps 1e-4 of c and loc and 1e-4 of the scale "
        "times the scale, 19 evaluations; scipy's genextreme with c = -xi; regular "
        "where c < 0.5 and the information is positive definite (Smith 1985), else "
        "refused (regular_likelihood)",
        "where KZGW reads the bound from a graph (ex. 3.2, 3.4) or from its quantile "
        "formula (eq. 3.36), Hydrolog holds its own estimate; KZGW's eqs. 2.9 and 3.41 "
        "multiply the whole quantile of its three-parameter log-normal (its bound "
        "19.6 mm in table 2.3, 0.384 m3/s in ex. 3.3), Hydrolog's log-normal has the "
        "bound 0, where both agree (the reference cases take loc 0 and the scale of "
        "the printed quantile)",
        "minima (stats low-flow): the GEV of the negated minima with the location of "
        "fisher_tippett_minima, the quantile of the minima at the non-exceedance 1/T",
        _SIGN_CONVENTION,
    ),
    assumptions=(
        "the estimator is near normal with the variance of the asymptotic theory: an "
        "approximation for 30 to 60 values whose coverage is simulated (CMP-6.11)",
        "the annual extremes are independent and identically distributed",
    ),
    traps={
        "moment_cancellation": "limit normal_limit: Pearson III's eq. 3.27 cancels "
        "terms of order lambda = 4 / G**2 as G -> 0; the rearranged form at G = 1e-9 "
        "and 0 gives the normal interval",
        "singular_at_bound": "constraint cases regular_likelihood and "
        "shape_of_a_likelihood_maximum at their bounds: c = 0.5 and |G| = 2 are "
        "refused",
        "gap_propagation": "type case values-nan_element: a gap is refused",
    },
    reference_cases=("tests/fixtures/formulas/flood-interval-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="Pearson III: KZGW's eq. 3.27, phi(p, lambda) / (alpha "
            "sqrt(N)) with phi**2 = (lambda t'**2 - 2 t' t + psi'(lambda) t**2) / "
            "(lambda psi'(lambda) - 1), t by Newton's method on mpmath's regularized "
            "incomplete gamma and t' = -(dP/dlambda) / (dP/dt) by mpmath.diff, at 50 "
            "digits, G = +-0.009 to +-1.9",
            test="tests/unit/test_interval_oracles.py::"
            "test_pearson3_sigma_is_kzgw_phi_in_mpmath",
            conventions=(
                "lambda = 4 / G**2, alpha = 2 / (scale |G|), the bound loc - 2 scale / "
                "G held; a negative G mirrored, t at the gamma's non-exceedance 1/T",
            ),
        ),
        Oracle(
            kind="exact",
            description="Weibull: the delta method of the two-parameter Weibull "
            "above its bound with the inverse of its expected information, the "
            "moments of the unit exponential as derivatives of Gamma by mpmath.diff, "
            "at 50 digits (eq. 3.57 is its closed form), k = 1.05 to 20",
            test="tests/unit/test_interval_oracles.py::"
            "test_weibull_sigma_is_the_delta_method_of_its_expected_information",
            conventions=("the bound loc held, (beta, k) estimated; p = 1/T",),
        ),
        Oracle(
            kind="exact",
            description="log-normal: exp(mu + s u_p -+ z sqrt(g' V g)), V the inverse "
            "expected information of the normal (mu, s) with the divisor N, u_p and z "
            "by mpmath's erfinv at 50 digits, s = 0.1 to 1.5",
            test="tests/unit/test_interval_oracles.py::"
            "test_log_normal_interval_is_eq_3_41_in_mpmath",
        ),
        Oracle(
            kind="exact",
            description="GEV: the observed information as the Hessian of Coles's "
            "log-likelihood (eq. 3.7) and the gradient of the return level by "
            "mpmath.diff at 50 digits, at extRemes's estimates of floods11, portpirie "
            "and the negated minima of station 223207 (xi 0.43, -0.05, -0.45)",
            test="tests/unit/test_interval_oracles.py::"
            "test_the_gev_observed_information_is_mpmaths",
            conventions=("Coles's xi is -c of scipy's genextreme",),
        ),
        Oracle(
            kind="frozen",
            description="R extRemes 2.2.1 fevd (GEV, MLE) and ci.fevd (return.level, "
            "method normal) on the seven samples of frequency_ml_samples.csv and the "
            "negated annual minima of station 223207 (WMO-No. 1029, table 7.1), T = 2 "
            "to 1000 years, c = 0.95 and 0.68; R 4.5.3, 2026-11-25",
            test="tests/oracles/interval_extremes_r.csv (tests/unit/"
            "test_interval_oracles.py)",
            conventions=(
                "extRemes's (location, scale, shape) is Coles's (mu, sigma, xi), "
                "scipy's genextreme(-xi, mu, sigma); minima: extRemes fits the negated "
                "minima, fisher_tippett_minima's loc is -mu and the T-year minimum's "
                "bounds are -upper and -lower",
                "both the delta method with the observed information, extRemes's from "
                "optimHess (step 1e-3) of its analytic gradient, Hydrolog's from "
                "central differences (steps 1e-4) of the log-likelihood; compared at "
                "extRemes's estimates, the points within 1e-12 and the half-widths "
                "within 5e-4",
            ),
        ),
    ),
    base={
        "values": list(_POLANA),
        "distribution": "gev",
        **_POLANA_GEV_ML,
        "return_periods_years": [2.0, 10.0, 100.0],
        "confidence_levels": [0.95, 0.68],
        "variable": "discharge",
        "extremes": "maxima",
    },
)


class DeltaInterval(NamedTuple):
    """Interval of the quantiles of a maximum-likelihood fit (quantile_interval_delta).

    ``lower`` and ``upper`` have a row per level and a column per return period.
    """

    lower: NDArray[np.float64]
    upper: NDArray[np.float64]


def _quantiles(x: Values) -> NDArray[np.float64]:
    """Return the quantiles of the fit at the return periods (minima: undercut)."""
    name = x.choice("distribution")
    exceedance = 1.0 / x.array("return_periods_years")
    if x.choice("extremes") == "minima":
        quantiles = 0.0 - genextreme.isf(
            exceedance, x.real("shape"), loc=0.0 - x.real("loc"), scale=x.real("scale")
        )
    else:
        quantiles = _DISTRIBUTIONS[name].isf(
            exceedance, x.real("shape"), loc=x.real("loc"), scale=x.real("scale")
        )
    return np.asarray(quantiles, dtype=np.float64)


def quantile_interval_delta(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
    distribution: str,
    shape: float,
    loc: float,
    scale: float,
    return_periods_years: NDArray[np.float64] | list[float] | tuple[float, ...],
    confidence_levels: NDArray[np.float64] | list[float] | tuple[float, ...],
    variable: str,
    extremes: str,
) -> DeltaInterval:
    """Return the delta-method interval of quantiles, spec quantile_interval_delta.

    Parameters
    ----------
    values : array_like of float
        The sample fitted.
    distribution : str
        ``"log_normal"``, ``"gev"``, Pearson III or ``"weibull"``.
    shape, loc, scale : float
        The parameters of the fit by maximum likelihood (scipy's; of
        ``fisher_tippett_minima`` for minima).
    return_periods_years : array_like of float
        Return periods [years].
    confidence_levels : array_like of float
        Distinct confidence levels.
    variable : str
        ``"discharge"`` or ``"stage"``.
    extremes : str
        ``"maxima"`` or ``"minima"``.

    Returns
    -------
    DeltaInterval
        The bounds per level and return period.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec (``regular_likelihood`` among its
        preconditions).

    Warns
    -----
    IntervalNotComputed
        If bounds of a discharge are left out as negative.
    """
    x = checked_inputs(
        QUANTILE_INTERVAL_DELTA,
        values=values,
        distribution=distribution,
        shape=shape,
        loc=loc,
        scale=scale,
        return_periods_years=return_periods_years,
        confidence_levels=confidence_levels,
        variable=variable,
        extremes=extremes,
    )
    name = x.choice("distribution")
    periods = x.array("return_periods_years")
    levels = x.array("confidence_levels")
    size = int(x.array("values").size)
    z = _z(levels)[:, None]
    quantiles = _quantiles(x)
    bound = x.real("loc")
    if name == "log_normal":
        u = _upper_normal(periods)
        half = z * x.real("shape") / math.sqrt(size) * np.sqrt(1.0 + u * u / 2.0)
        excess = quantiles - bound
        lower = bound + excess * np.exp(-half)
        upper = bound + excess * np.exp(half)
    else:
        if name == "pearson3":
            sigma = _pearson3_sigma(x.real("shape"), x.real("scale"), size, periods)
        elif name == "weibull":
            sigma = _weibull_sigma(x.real("shape"), quantiles - bound, size, periods)
        else:
            information = _information(x)
            if information is None:  # the precondition regular_likelihood holds
                raise ValueError("quantile_interval_delta: no information of the GEV")
            sigma = _gev_sigma(information, periods)
        lower = quantiles - z * sigma
        upper = quantiles + z * sigma
    lower, upper = _signed(
        lower,
        upper,
        discharge=x.choice("variable") == "discharge",
        levels=levels,
        periods=periods,
        distribution=name if x.choice("extremes") == "maxima" else "fisher_tippett",
        fit_method="mle",
    )
    out = checked_outputs(QUANTILE_INTERVAL_DELTA, {"lower": lower, "upper": upper})
    return DeltaInterval(out.array("lower"), out.array("upper"))


SPECS: Final = (QUANTILE_INTERVAL_BOOTSTRAP, QUANTILE_INTERVAL_DELTA)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""
