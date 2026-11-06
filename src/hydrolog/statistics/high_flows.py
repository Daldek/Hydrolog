"""Flood frequency analysis using parametric distributions.

Fits annual maximum series to GEV, Log-Normal, Pearson Type III, and Weibull
distributions by maximum likelihood, the method of moments, the method of
L-moments or least squares (:data:`FIT_METHODS`).  Provides goodness-of-fit
diagnostics (K-S, Anderson-Darling, AIC) and quantile estimates for user-defined
return periods.

References
----------
KZGW (2017): Metodyka opracowywania charakterystyk wezbrań i powodzi
    w zlewniach kontrolowanych — minimum 30 years of data recommended.
Coles S. (2001): An Introduction to Statistical Modeling of Extreme Values.
Hosking J.R.M., Wallis J.R. (1997): Regional Frequency Analysis: An Approach
    Based on L-Moments. Cambridge University Press.
"""

from __future__ import annotations

import warnings
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, Literal, cast, get_args

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq, minimize
from scipy.special import erfinv, gamma, gammaln, zeta
from scipy.stats import genextreme, kstest, lognorm, pearson3, weibull_min

from hydrolog._ranges import typical_range
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import (
    DistributionLeftOut,
    KsTestApproximate,
    OutsideSupport,
    ShortRecord,
    SmallSample,
)
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics._types import EmpiricalFrequency, compute_plotting_positions

_DEFAULT_RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])
_MIN_RELIABLE_YEARS = 10  # below it the estimates may be unreliable
# KZGW (2017): the minimum record for flood frequency analysis (one table of ranges)
_KZGW_MIN_YEARS = int(cast(float, typical_range("flood_frequency", "years").minimum))

_AD_CRITICAL_VALUES: dict[str, float] = {
    "15%": 1.610,
    "10%": 1.933,
    "5%": 2.492,
    "2.5%": 3.070,
    "1%": 3.857,
}

FitMethod = Literal["mle", "moments", "l_moments", "least_squares"]
FIT_METHODS: tuple[str, ...] = get_args(FitMethod)
"""Parameter estimation methods of :class:`FloodFrequencyAnalysis` (``fit_method``)."""

_DISTRIBUTIONS: Final[dict[str, Any]] = {
    "log_normal": lognorm,
    "gev": genextreme,
    "pearson3": pearson3,
    "weibull": weibull_min,
}
_DISTRIBUTION_NAMES: Final = {
    "log_normal": "log-normal",
    "gev": "GEV",
    "pearson3": "Pearson type III",
    "weibull": "Weibull",
}
_METHOD_NAMES: Final = {
    "moments": "method of moments",
    "l_moments": "method of L-moments",
    "least_squares": "method of least squares",
}
_MIN_VALUES: Final = 3  # the skewness and the L-skewness need three values
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


@dataclass
class FrequencyAnalysisResult(JsonResultMixin):
    """Result of fitting a distribution to annual maxima.

    Attributes
    ----------
    distribution_name : str
        Distribution identifier: ``"log_normal"``, ``"gev"``,
        ``"pearson3"``, or ``"weibull"``.
    parameters : dict[str, float]
        Fitted distribution parameters.
    return_periods : NDArray[np.float64]
        Return periods *T* (years).
    quantiles : NDArray[np.float64]
        Quantile estimates for each return period.
    exceedance_probabilities : NDArray[np.float64]
        Exceedance probability 1/*T* for each return period.
    ks_statistic : float
        Kolmogorov-Smirnov test statistic.
    ks_p_value : float
        Kolmogorov-Smirnov *p*-value.
    ks_valid : bool
        Always ``False`` — parameters were estimated from the data.
    ad_statistic : float
        Anderson-Darling test statistic.
    ad_critical_values : dict[str, float]
        Approximate critical values (case 0: fully specified distribution).
    aic : float
        Akaike Information Criterion, from the log-likelihood at the fitted
        parameters; infinite when an annual maximum lies outside the support of
        the fitted distribution.
    """

    distribution_name: str
    parameters: dict[str, float]
    return_periods: NDArray[np.float64]
    quantiles: NDArray[np.float64]
    exceedance_probabilities: NDArray[np.float64]
    ks_statistic: float
    ks_p_value: float
    ks_valid: bool
    ad_statistic: float
    ad_critical_values: dict[str, float]
    aic: float


def _anderson_darling(
    data: NDArray[np.float64],
    cdf_func: object,
) -> float:
    """Compute Anderson-Darling statistic for any continuous distribution.

    Parameters
    ----------
    data : NDArray[np.float64]
        Observed sample.
    cdf_func : callable
        CDF function that accepts an array and returns probabilities.

    Returns
    -------
    float
        Anderson-Darling *A*² statistic.

    Notes
    -----
    ``scipy.stats.anderson`` only supports a limited set of distributions
    (norm, expon, logistic, gumbel, gumbel_l).  This function implements the
    general formula:

    A² = -n - Σ [(2i − 1)/n · (ln F(x_i) + ln(1 − F(x_{n+1−i})))]
    """
    n = len(data)
    sorted_data = np.sort(data)
    F = cdf_func(sorted_data)  # type: ignore[operator]
    F = np.clip(F, 1e-10, 1 - 1e-10)  # avoid log(0)
    i = np.arange(1, n + 1)
    S = np.sum((2 * i - 1) / n * (np.log(F) + np.log(1 - F[::-1])))
    A2: float = float(-n - S)
    return A2


class _NoParameters(Exception):
    """A fit method gives no parameters of a distribution for the sample.

    :meth:`FloodFrequencyAnalysis._estimate` turns it into a
    :class:`CalculationError` that names the method and the distribution.

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


def _require_spread(data: NDArray[np.float64]) -> None:
    """Require the 3 values of the skewness and the L-skewness, not all equal."""
    if data.size < _MIN_VALUES:
        raise _NoParameters(
            "too_few_values",
            f"it needs at least {_MIN_VALUES} values, got {data.size}",
            count=int(data.size),
            minimum=_MIN_VALUES,
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
    positions of :meth:`FloodFrequencyAnalysis.empirical_frequency`. Nelder-Mead
    starts from the moments; it searches the logarithm of the scale and of the
    log-normal and Weibull shapes, which stay positive.
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


_ESTIMATORS: Final = {
    "moments": _by_moments,
    "l_moments": _by_l_moments,
    "least_squares": _by_least_squares,
}


class FloodFrequencyAnalysis:
    """Flood frequency analysis for annual maximum series.

    Fits GEV, Log-Normal, Pearson Type III, and Weibull distributions
    and computes quantile estimates for specified return periods.

    Parameters
    ----------
    annual_maxima : NDArray[np.float64]
        Annual maximum flow values.
    return_periods : NDArray[np.float64] or None, optional
        Return periods *T* (years).  Defaults to
        ``[2, 5, 10, 20, 50, 100, 500, 1000]``.

    Raises
    ------
    InvalidParameterError
        If *annual_maxima* is empty or contains NaN values.

    Warns
    -----
    UserWarning
        If sample size is below KZGW-recommended 30 years, or below 10.

    Notes
    -----
    Each ``fit_*`` method takes ``fit_method`` (:data:`FIT_METHODS`). Every method
    gives the parameters of the same scipy distributions (``lognorm`` with location
    0, ``genextreme``, ``pearson3``, ``weibull_min``), from which the quantiles, the
    goodness of fit and the AIC follow alike:

    - ``"mle"``: maximum likelihood, ``scipy.stats.<distribution>.fit``;
    - ``"moments"``: the distribution's mean, standard deviation and (three
      parameters) skewness equal the sample's, with the divisor n - 1 and the
      adjusted skewness G1 = √(n (n - 1)) / (n - 2) · m3 / m2^(3/2);
    - ``"l_moments"``: its L-moments λ1, λ2 and (three parameters) L-skewness τ3
      equal the sample's, from the unbiased probability-weighted moments (Hosking
      and Wallis 1997): the log-normal by s = 2 erf⁻¹(λ2 / λ1), the GEV by the
      shape whose τ3 is the sample's, Pearson III by the approximations of Hosking
      and Wallis;
    - ``"least_squares"``: the parameters minimising the sum of squared
      differences between the ascending sample and the distribution's quantiles
      at the Weibull plotting positions j / (n + 1), searched by Nelder-Mead from
      the moments.

    For the moments and the L-moments the Weibull distribution is the GEV of the
    negated sample, which needs a sample skewness above -1.1395 or an L-skewness
    above -0.1699 (the limits of the Gumbel distribution). The methods other than
    maximum likelihood need 3 values, not all equal (least squares starts from the
    moments and needs what they need), and raise :class:`CalculationError` when
    they give no parameters, with ``details.reason``: ``too_few_values``,
    ``constant_values``, ``out_of_range`` (the sample skewness or L-skewness
    outside the range of the distribution) or ``non_positive_values`` (the
    log-normal with location 0 needs values above 0). They may give a distribution
    whose support leaves out an annual maximum, most often a lower bound of Pearson
    III or Weibull above the smallest one (maximum likelihood rarely does): the
    result keeps its quantiles and its AIC is infinite, so it ranks after every fit
    with a finite AIC.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
    >>> data = np.array([120.0, 95.0, 150.0, 200.0, 180.0, 160.0])
    >>> ffa = FloodFrequencyAnalysis(data)  # doctest: +SKIP
    >>> result = ffa.fit_gev()  # doctest: +SKIP
    >>> by_l_moments = ffa.fit_gev(fit_method="l_moments")  # doctest: +SKIP
    """

    def __init__(
        self,
        annual_maxima: NDArray[np.float64],
        return_periods: NDArray[np.float64] | None = None,
    ) -> None:
        if len(annual_maxima) == 0:
            raise InvalidParameterError("annual_maxima must not be empty.")
        if np.any(np.isnan(annual_maxima)):
            raise InvalidParameterError("annual_maxima must not contain NaN values.")

        years = len(annual_maxima)
        if years < _MIN_RELIABLE_YEARS:
            warnings.warn(
                SmallSample(years=years, minimum=_MIN_RELIABLE_YEARS), stacklevel=2
            )
        elif years < _KZGW_MIN_YEARS:
            warnings.warn(
                ShortRecord(years=years, minimum=_KZGW_MIN_YEARS), stacklevel=2
            )

        self._data = np.asarray(annual_maxima, dtype=np.float64)
        self._return_periods = (
            np.asarray(return_periods, dtype=np.float64)
            if return_periods is not None
            else _DEFAULT_RETURN_PERIODS.copy()
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fit_log_normal(
        self, *, fit_method: FitMethod = "mle"
    ) -> FrequencyAnalysisResult:
        """Fit a two-parameter log-normal distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default ``"mle"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If a method other than ``"mle"`` gives no parameters.

        Notes
        -----
        The location parameter is fixed at zero whatever the method (maximum
        likelihood: ``scipy.stats.lognorm.fit(data, floc=0)``), yielding a
        standard two-parameter log-normal parameterisation (shape *s*, scale).
        """
        shape, loc, scale = self._estimate("log_normal", fit_method)
        params = {"shape": shape, "loc": loc, "scale": scale}
        k = 2  # shape + scale (loc is fixed)

        exceedance = 1.0 / self._return_periods
        quantiles = lognorm.ppf(1 - exceedance, shape, loc=0, scale=scale)

        return self._build_result(
            name="log_normal",
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: lognorm.cdf(x, shape, loc=0, scale=scale),
            logpdf_func=lambda x: lognorm.logpdf(x, shape, loc=0, scale=scale),
        )

    def fit_gev(self, *, fit_method: FitMethod = "mle") -> FrequencyAnalysisResult:
        """Fit the Generalised Extreme Value distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default ``"mle"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If a method other than ``"mle"`` gives no parameters.

        Notes
        -----
        SciPy uses the sign convention ``c = -ξ`` for the shape parameter.
        """
        c, loc, scale = self._estimate("gev", fit_method)
        params = {"shape": c, "loc": loc, "scale": scale}
        k = 3

        exceedance = 1.0 / self._return_periods
        quantiles = genextreme.ppf(1 - exceedance, c, loc=loc, scale=scale)

        return self._build_result(
            name="gev",
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: genextreme.cdf(x, c, loc=loc, scale=scale),
            logpdf_func=lambda x: genextreme.logpdf(x, c, loc=loc, scale=scale),
        )

    def fit_pearson3(self, *, fit_method: FitMethod = "mle") -> FrequencyAnalysisResult:
        """Fit the Pearson Type III distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default ``"mle"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If a method other than ``"mle"`` gives no parameters.
        """
        skew, loc, scale = self._estimate("pearson3", fit_method)
        params = {"skew": skew, "loc": loc, "scale": scale}
        k = 3

        exceedance = 1.0 / self._return_periods
        quantiles = pearson3.ppf(1 - exceedance, skew, loc=loc, scale=scale)

        return self._build_result(
            name="pearson3",
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: pearson3.cdf(x, skew, loc=loc, scale=scale),
            logpdf_func=lambda x: pearson3.logpdf(x, skew, loc=loc, scale=scale),
        )

    def fit_weibull(self, *, fit_method: FitMethod = "mle") -> FrequencyAnalysisResult:
        """Fit the Weibull minimum distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default ``"mle"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If a method other than ``"mle"`` gives no parameters.
        """
        shape, loc, scale = self._estimate("weibull", fit_method)
        params = {"shape": shape, "loc": loc, "scale": scale}
        k = 3

        exceedance = 1.0 / self._return_periods
        quantiles = weibull_min.ppf(1 - exceedance, shape, loc=loc, scale=scale)

        return self._build_result(
            name="weibull",
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: weibull_min.cdf(x, shape, loc=loc, scale=scale),
            logpdf_func=lambda x: weibull_min.logpdf(x, shape, loc=loc, scale=scale),
        )

    def empirical_frequency(self, method: str = "weibull") -> EmpiricalFrequency:
        """Compute empirical plotting positions.

        Parameters
        ----------
        method : str, optional
            Plotting position method, by default ``"weibull"``.
            Options: ``"weibull"``, ``"hazen"``, ``"cunnane"``.

        Returns
        -------
        EmpiricalFrequency
            Sorted values with exceedance probabilities and return periods.
        """
        return compute_plotting_positions(self._data, method=method)

    def fit_all(
        self, *, fit_method: FitMethod = "mle"
    ) -> dict[str, FrequencyAnalysisResult]:
        """Fit all four distributions and return results sorted by AIC.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method of every distribution (see the class
            notes), by default ``"mle"``.

        Returns
        -------
        dict[str, FrequencyAnalysisResult]
            Ordered dictionary keyed by distribution name, sorted by AIC
            in ascending order (best fit first).

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If the method gives parameters of none of the distributions.

        Warns
        -----
        DistributionLeftOut
            For each distribution a method other than ``"mle"`` gives no parameters
            of (see the class notes); it is not in the result.
        """
        results: dict[str, FrequencyAnalysisResult] = {}
        reasons: dict[str, str] = {}
        for name in ("log_normal", "gev", "pearson3", "weibull"):
            try:
                results[name] = getattr(self, f"fit_{name}")(fit_method=fit_method)
            except CalculationError as exc:
                reasons[name] = exc.details["reason"]
                warnings.warn(
                    DistributionLeftOut(
                        distribution=name,
                        fit_method=fit_method,
                        reason=reasons[name],
                        cause=str(exc),
                    ),
                    stacklevel=2,
                )
        if not results:
            raise CalculationError(
                f"The {_METHOD_NAMES[fit_method]} fits none of the four distributions "
                "to these annual maxima",
                details={"fit_method": fit_method, "reasons": reasons},
                hint="Choose another fit method.",
            )

        sorted_items = sorted(results.items(), key=lambda item: item[1].aic)
        return OrderedDict(sorted_items)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _estimate(self, name: str, fit_method: str) -> tuple[float, float, float]:
        """Parameters ``(shape, loc, scale)`` of distribution ``name``.

        Parameters
        ----------
        name : str
            Distribution identifier.
        fit_method : str
            Parameter estimation method, one of :data:`FIT_METHODS`.

        Returns
        -------
        tuple of float
            The parameters of the scipy distribution (``lognorm`` with location 0).

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`.
        CalculationError
            If a method other than ``"mle"`` gives no parameters (see the class
            notes for ``details.reason``).
        """
        if fit_method not in FIT_METHODS:
            allowed = ", ".join(repr(method) for method in FIT_METHODS)
            raise InvalidParameterError(
                f"Unknown fit method: {fit_method!r}. Use {allowed}.",
                details={
                    "option": "fit_method",
                    "reason": "choice",
                    "allowed": list(FIT_METHODS),
                    "value": str(fit_method),
                },
            )
        distribution = _DISTRIBUTIONS[name]
        if fit_method == "mle":
            fitted = (
                lognorm.fit(self._data, floc=0)
                if name == "log_normal"
                else distribution.fit(self._data)
            )
            return cast(tuple[float, float, float], fitted)
        estimate = _ESTIMATORS[fit_method]
        try:
            parameters = estimate(name, self._data)
        except _NoParameters as exc:
            raise CalculationError(
                f"The {_METHOD_NAMES[fit_method]} cannot fit the "
                f"{_DISTRIBUTION_NAMES[name]} distribution to these annual maxima: "
                f"{exc}",
                details={
                    "distribution": name,
                    "fit_method": fit_method,
                    "reason": exc.reason,
                    **exc.details,
                },
                hint="Choose another fit method or distribution.",
            ) from None
        return parameters

    def _build_result(
        self,
        name: str,
        params: dict[str, float],
        k: int,
        quantiles: NDArray[np.float64],
        cdf_func: object,
        logpdf_func: object,
    ) -> FrequencyAnalysisResult:
        """Build a :class:`FrequencyAnalysisResult` with GOF diagnostics.

        Parameters
        ----------
        name : str
            Distribution identifier.
        params : dict[str, float]
            Fitted parameter dictionary.
        k : int
            Number of estimated parameters (for AIC).
        quantiles : NDArray[np.float64]
            Quantile estimates at ``self._return_periods``.
        cdf_func : callable
            CDF evaluated with fitted parameters.
        logpdf_func : callable
            Log-PDF evaluated with fitted parameters.

        Returns
        -------
        FrequencyAnalysisResult
        """
        # K-S test
        ks_stat, ks_pval = kstest(self._data, cdf_func)
        warnings.warn(KsTestApproximate(), stacklevel=3)

        # Anderson-Darling (manual)
        ad_stat = _anderson_darling(self._data, cdf_func)

        # AIC
        log_densities = np.asarray(logpdf_func(self._data))  # type: ignore[operator]
        log_likelihood = float(np.sum(log_densities))
        aic = 2.0 * k - 2.0 * log_likelihood
        outside = ~np.isfinite(log_densities)
        if outside.any():
            values = [float(value) for value in np.sort(self._data[outside])]
            warnings.warn(
                OutsideSupport(distribution=name, values=values), stacklevel=3
            )

        exceedance = 1.0 / self._return_periods

        return FrequencyAnalysisResult(
            distribution_name=name,
            parameters=params,
            return_periods=self._return_periods.copy(),
            quantiles=np.asarray(quantiles, dtype=np.float64),
            exceedance_probabilities=exceedance,
            ks_statistic=float(ks_stat),
            ks_p_value=float(ks_pval),
            ks_valid=False,
            ad_statistic=ad_stat,
            ad_critical_values=_AD_CRITICAL_VALUES.copy(),
            aic=float(aic),
        )
