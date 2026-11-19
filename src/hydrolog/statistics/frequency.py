"""Distributions of annual extremes: sample statistics and parameter estimators.

The estimators of the frequency analyses of annual maxima
(:class:`~hydrolog.statistics.FloodFrequencyAnalysis`) and minima
(:func:`~hydrolog.statistics.fit_fisher_tippett_minima`): the sample's product
moments and L-moments, and the parameters of the log-normal, GEV, Pearson type III
and Weibull distributions of :mod:`scipy.stats` by L-moments, moments, maximum
likelihood and least squares.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq, minimize
from scipy.special import erfinv, gamma, gammaln, zeta
from scipy.stats import genextreme, lognorm, pearson3, weibull_min

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


def _sample_moments(data: NDArray[np.float64]) -> tuple[float, float, float]:
    """Mean, standard deviation and skewness of a sample, bias-corrected.

    The standard deviation has the divisor n - 1 and the skewness is the adjusted
    Fisher-Pearson coefficient G1 = √(n (n - 1)) / (n - 2) · m3 / m2^(3/2), where m2
    and m3 are the central moments of the sample (divisor n).
    """
    _require_spread(data)
    n = data.size
    mean = float(np.mean(data))
    deviations = data - mean
    m2 = float(np.mean(deviations**2))
    m3 = float(np.mean(deviations**3))
    skewness = np.sqrt(n * (n - 1)) / (n - 2) * m3 / m2**1.5
    return mean, float(np.sqrt(m2 * n / (n - 1))), float(skewness)


def _sample_l_moments(data: NDArray[np.float64]) -> tuple[float, float, float]:
    """L-moments λ1 and λ2 and L-skewness τ3 of a sample.

    From the unbiased probability-weighted moments of the ascending sample
    x(1) ≤ ... ≤ x(n) (Hosking and Wallis 1997): b0 = Σ x(j) / n,
    b1 = Σ (j - 1) x(j) / (n (n - 1)), b2 = Σ (j - 1)(j - 2) x(j) / (n (n - 1)(n - 2));
    λ1 = b0, λ2 = 2 b1 - b0 and τ3 = (6 b2 - 6 b1 + b0) / λ2.
    """
    _require_spread(data)
    n = data.size
    ascending = np.sort(data)
    rank = np.arange(n, dtype=np.float64)  # j - 1
    b0 = float(np.mean(ascending))
    b1 = float(rank @ ascending) / (n * (n - 1))
    b2 = float((rank * (rank - 1.0)) @ ascending) / (n * (n - 1) * (n - 2))
    l2 = 2.0 * b1 - b0
    return b0, l2, (6.0 * b2 - 6.0 * b1 + b0) / l2


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
