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
from dataclasses import dataclass
from typing import Final, Literal, cast, get_args

import numpy as np
from numpy.typing import NDArray
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
from hydrolog.statistics.frequency import (
    _DISTRIBUTIONS,
    _by_l_moments,
    _maximum_likelihood,
    _within_l_moments,
    fit_l_moments,
    fit_least_squares,
    fit_maximum_likelihood,
    fit_moments,
    gev_quantiles,
    log_normal_quantiles,
    pearson3_quantiles,
    weibull_quantiles,
)

_DEFAULT_RETURN_PERIODS = np.array([2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0])
_MIN_RELIABLE_YEARS = 10  # below it the estimates may be unreliable
# KZGW (2017): the minimum record for flood frequency analysis (one table of ranges)
_KZGW_MIN_YEARS = int(cast(float, typical_range("flood_frequency", "years").minimum))

_AD_LEVELS: Final = {"15%": 0.15, "10%": 0.10, "5%": 0.05, "2.5%": 0.025, "1%": 0.01}
"""Significance levels of the critical values of A²."""
_AD_REPLICATES: Final = 999
"""Samples of the parametric bootstrap of the critical values of A²."""
_AD_SEED: Final = 20261118
"""Seed of that bootstrap, so that a sample always gets the same critical values."""

FitMethod = Literal["mle", "moments", "l_moments", "least_squares"]
FIT_METHODS: tuple[str, ...] = get_args(FitMethod)
"""Parameter estimation methods of :class:`FloodFrequencyAnalysis` (``fit_method``)."""

_DISTRIBUTION_NAMES: Final = {
    "log_normal": "log-normal",
    "gev": "GEV",
    "pearson3": "Pearson type III",
    "weibull": "Weibull",
}
_METHOD_NAMES: Final = {
    "mle": "method of maximum likelihood",
    "moments": "method of moments",
    "l_moments": "method of L-moments",
    "least_squares": "method of least squares",
}
_LEFT_OUT: Final = {
    "enough_values": "too_few_values",
    "values_not_all_equal": "constant_values",
    "positive_values": "non_positive_values",
    "l_moments_within_distribution": "out_of_range",
    "skewness_within_distribution": "out_of_range",
    "squares_have_a_minimum": "not_converged",
}
"""``reason`` of :class:`~hydrolog._warnings.DistributionLeftOut` (the codes of
version 0.9.0) by the precondition of the estimator's spec that failed."""


@dataclass
class FrequencyAnalysisResult(JsonResultMixin):
    """Result of fitting a distribution to annual maxima.

    Attributes
    ----------
    distribution_name : str
        Distribution identifier: ``"log_normal"``, ``"gev"``,
        ``"pearson3"``, or ``"weibull"``.
    fit_method : str
        Method that estimated the parameters, one of :data:`FIT_METHODS`.
    parameters : dict[str, float]
        Fitted distribution parameters.
    return_periods : NDArray[np.float64]
        Return periods *T* (years).
    quantiles : NDArray[np.float64]
        Quantile estimates for each return period.
    densities : NDArray[np.float64]
        Probability density of the fitted distribution at each of ``quantiles``
        [1/(m³/s)], in the same order.
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
    ad_critical_values : dict[str, float] or None
        Critical values of ``ad_statistic`` at the levels ``"15%"`` … ``"1%"`` for
        the distribution fitted to this sample, from a parametric bootstrap
        (:func:`_ad_critical_values`); ``None`` for a method other than
        ``"l_moments"``, whose refits are too slow to bootstrap.
    aic : float
        Akaike Information Criterion, from the log-likelihood at the fitted
        parameters; infinite when an annual maximum lies outside the support of
        the fitted distribution.
    """

    distribution_name: str
    fit_method: str
    parameters: dict[str, float]
    return_periods: NDArray[np.float64]
    quantiles: NDArray[np.float64]
    densities: NDArray[np.float64]
    exceedance_probabilities: NDArray[np.float64]
    ks_statistic: float
    ks_p_value: float
    ks_valid: bool
    ad_statistic: float
    ad_critical_values: dict[str, float] | None
    aic: float


def _a_squared(probabilities: NDArray[np.float64]) -> NDArray[np.float64]:
    """Anderson-Darling A² of the fitted CDF values of ascending samples.

    The samples run along the last axis; the values are clipped to [1e-10,
    1 - 1e-10], so that a value outside the support adds a large finite term.
    A² = -n - Σ [(2i − 1)/n · (ln F(x_i) + ln(1 − F(x_{n+1−i})))].
    """
    n = probabilities.shape[-1]
    clipped = np.clip(probabilities, 1e-10, 1 - 1e-10)
    weights = (2.0 * np.arange(1, n + 1) - 1.0) / n
    terms = np.log(clipped) + np.log(1.0 - clipped[..., ::-1])
    result: NDArray[np.float64] = -n - np.sum(weights * terms, axis=-1)
    return result


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
        Anderson-Darling *A*² statistic (:func:`_a_squared`).

    Notes
    -----
    ``scipy.stats.anderson`` only supports a limited set of distributions
    (norm, expon, logistic, gumbel, gumbel_l), with their own estimators.
    """
    probabilities = np.asarray(cdf_func(np.sort(data)), dtype=np.float64)  # type: ignore[operator]
    return float(_a_squared(probabilities))


def _ad_critical_values(
    name: str, parameters: tuple[float, float, float], size: int
) -> dict[str, float] | None:
    """Critical values of A² of an L-moments fit, by a parametric bootstrap.

    With the parameters estimated from the sample, the distribution of A² is much
    narrower than for a distribution given in advance (case 0 of Stephens 1974,
    whose 5 % point 2.492 such a fit almost never reaches) and depends on the
    distribution, the method of estimation, the sample size and the shape. So the
    critical values are those of this fit: ``_AD_REPLICATES`` samples of ``size``
    values drawn from the fitted distribution, each refitted by L-moments, give the
    A² whose upper quantiles 1 - level are the critical values (the parametric
    bootstrap of Stute, González Manteiga and Presedo Quindimil 1993; the seed is
    fixed). A sample that the L-moments cannot fit is left out.
    """
    distribution = _DISTRIBUTIONS[name]
    rng = np.random.default_rng(_AD_SEED)
    samples = np.sort(
        distribution.rvs(*parameters, size=(_AD_REPLICATES, size), random_state=rng),
        axis=1,
    )
    # Drawn from a continuous distribution, the samples have distinct values (and
    # those of the log-normal positive ones): only their L-moments can fail.
    kept = [
        row for row, sample in enumerate(samples) if _within_l_moments(name, sample)
    ]
    if not kept:
        return None
    refits = [_by_l_moments(name, samples[row]) for row in kept]
    columns = zip(*refits, strict=True)
    shape, loc, scale = (np.array(column)[:, None] for column in columns)
    with np.errstate(all="ignore"):
        statistics = _a_squared(distribution.cdf(samples[kept], shape, loc, scale))
    return {
        label: float(np.quantile(statistics, 1.0 - level))
        for label, level in _AD_LEVELS.items()
    }


_ESTIMATORS: Final = {
    "mle": fit_maximum_likelihood,
    "moments": fit_moments,
    "l_moments": fit_l_moments,
    "least_squares": fit_least_squares,
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
        If *annual_maxima* is empty or holds a value that is not finite (NaN or
        infinity).

    Warns
    -----
    UserWarning
        If sample size is below KZGW-recommended 30 years, or below 10.

    Notes
    -----
    Each ``fit_*`` method takes ``fit_method`` (:data:`FIT_METHODS`), by default
    ``"l_moments"``: maximum likelihood is less stable on the short samples of
    annual maxima. :meth:`fit_all` also takes ``"all"``, each distribution by each
    method. Every method gives the parameters of the same scipy distributions
    (``lognorm`` with location 0, ``genextreme``, ``pearson3``, ``weibull_min``),
    from which the quantiles, the goodness of fit and the AIC follow alike:

    - ``"mle"``: maximum likelihood; the log-normal in closed form
      (``scipy.stats.lognorm.fit`` with ``floc=0``), the others by Nelder-Mead on
      the standardised sample (x - mean) / sd from the L-moments' estimate, run
      again from the point found until it gains nothing (scipy's own ``fit`` starts
      from the scale 1 and may stop far from the maximum);
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
    above -0.1699 (the limits of the Gumbel distribution). Every method needs values
    not all equal: 3 for the moments, the L-moments and least squares (which starts
    from the moments and needs what they need), and one more than the distribution
    has parameters for maximum likelihood (3 for the log-normal, 4 for the others).
    Each method is a formula with a spec (``fit_l_moments``, ``fit_moments``,
    ``fit_maximum_likelihood``, ``fit_least_squares`` of
    :mod:`hydrolog.statistics.frequency`): a sample that fails one of its
    preconditions is refused with :class:`InvalidParameterError`, ``details.reason``
    ``precondition_failed`` and ``details.constraint`` the condition:
    ``enough_values``, ``values_not_all_equal``, ``positive_values`` (the log-normal
    with location 0 needs values above 0), ``l_moments_within_distribution`` or
    ``skewness_within_distribution`` (the sample L-skewness or skewness outside the
    range of the distribution) or, by maximum likelihood,
    ``likelihood_has_a_maximum``. The likelihood of a three-parameter distribution
    has no maximum where its density is infinite at a bound of the support, which
    then sits at the closest annual maximum (Smith 1985): the GEV with c >= 1,
    Pearson III with a skewness of 2 or more (or -2 or less), Weibull with a shape of
    1 or less; a search that ends there fails ``likelihood_has_a_maximum``. A search
    of maximum likelihood or least squares that does not settle raises
    :class:`CalculationError` (``details.reason`` ``not_converged``). The other
    methods may give a distribution whose support leaves out an annual maximum, most
    often a lower bound of Pearson III or Weibull above the smallest one: the result
    keeps its quantiles and its AIC is infinite, so it ranks after every fit with a
    finite AIC.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
    >>> data = np.array([120.0, 95.0, 150.0, 200.0, 180.0, 160.0])
    >>> ffa = FloodFrequencyAnalysis(data)  # doctest: +SKIP
    >>> result = ffa.fit_gev()  # doctest: +SKIP
    >>> by_mle = ffa.fit_gev(fit_method="mle")  # doctest: +SKIP
    >>> every_fit = ffa.fit_all(fit_method="all")  # doctest: +SKIP
    """

    def __init__(
        self,
        annual_maxima: NDArray[np.float64],
        return_periods: NDArray[np.float64] | None = None,
    ) -> None:
        if len(annual_maxima) == 0:
            raise InvalidParameterError("annual_maxima must not be empty.")
        if not np.all(np.isfinite(annual_maxima)):
            raise InvalidParameterError(
                "annual_maxima must hold finite numbers only (no NaN or infinity).",
                details={"option": "annual_maxima", "reason": "not_finite"},
            )

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
        self, *, fit_method: FitMethod = "l_moments"
    ) -> FrequencyAnalysisResult:
        """Fit a two-parameter log-normal distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default
            ``"l_moments"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`, or the sample fails a
            precondition of the method (see the class notes).
        CalculationError
            If the search of the method does not settle (see the class notes).

        Notes
        -----
        The location parameter is fixed at zero whatever the method (maximum
        likelihood: ``scipy.stats.lognorm.fit(data, floc=0)``), yielding a
        standard two-parameter log-normal parameterisation (shape *s*, scale).
        """
        shape, loc, scale = self._estimate("log_normal", fit_method)
        params = {"shape": shape, "loc": loc, "scale": scale}
        k = 2  # shape + scale (loc is fixed)

        quantiles = log_normal_quantiles(shape, 0.0, scale, self._return_periods)

        return self._build_result(
            name="log_normal",
            fit_method=fit_method,
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: lognorm.cdf(x, shape, loc=0, scale=scale),
            logpdf_func=lambda x: lognorm.logpdf(x, shape, loc=0, scale=scale),
        )

    def fit_gev(
        self, *, fit_method: FitMethod = "l_moments"
    ) -> FrequencyAnalysisResult:
        """Fit the Generalised Extreme Value distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default
            ``"l_moments"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`, or the sample fails a
            precondition of the method (see the class notes).
        CalculationError
            If the search of the method does not settle (see the class notes).

        Notes
        -----
        SciPy uses the sign convention ``c = -ξ`` for the shape parameter.
        """
        c, loc, scale = self._estimate("gev", fit_method)
        params = {"shape": c, "loc": loc, "scale": scale}
        k = 3

        quantiles = gev_quantiles(c, loc, scale, self._return_periods)

        return self._build_result(
            name="gev",
            fit_method=fit_method,
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: genextreme.cdf(x, c, loc=loc, scale=scale),
            logpdf_func=lambda x: genextreme.logpdf(x, c, loc=loc, scale=scale),
        )

    def fit_pearson3(
        self, *, fit_method: FitMethod = "l_moments"
    ) -> FrequencyAnalysisResult:
        """Fit the Pearson Type III distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default
            ``"l_moments"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`, or the sample fails a
            precondition of the method (see the class notes).
        CalculationError
            If the search of the method does not settle (see the class notes).
        """
        skew, loc, scale = self._estimate("pearson3", fit_method)
        params = {"skew": skew, "loc": loc, "scale": scale}
        k = 3

        quantiles = pearson3_quantiles(skew, loc, scale, self._return_periods)

        return self._build_result(
            name="pearson3",
            fit_method=fit_method,
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: pearson3.cdf(x, skew, loc=loc, scale=scale),
            logpdf_func=lambda x: pearson3.logpdf(x, skew, loc=loc, scale=scale),
        )

    def fit_weibull(
        self, *, fit_method: FitMethod = "l_moments"
    ) -> FrequencyAnalysisResult:
        """Fit the Weibull minimum distribution.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares"}, optional
            Parameter estimation method (see the class notes), by default
            ``"l_moments"``.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is not one of :data:`FIT_METHODS`, or the sample fails a
            precondition of the method (see the class notes).
        CalculationError
            If the search of the method does not settle (see the class notes).
        """
        shape, loc, scale = self._estimate("weibull", fit_method)
        params = {"shape": shape, "loc": loc, "scale": scale}
        k = 3

        quantiles = weibull_quantiles(shape, loc, scale, self._return_periods)

        return self._build_result(
            name="weibull",
            fit_method=fit_method,
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
        self,
        *,
        fit_method: FitMethod | Literal["all"] = "l_moments",
        distribution: str = "all",
    ) -> dict[str, FrequencyAnalysisResult]:
        """Fit the distributions and return results sorted by AIC.

        Parameters
        ----------
        fit_method : {"mle", "moments", "l_moments", "least_squares", "all"}, optional
            Parameter estimation method of every distribution (see the class
            notes), by default ``"l_moments"``; ``"all"`` fits each distribution
            by each of :data:`FIT_METHODS`.
        distribution : {"all", "log_normal", "gev", "pearson3", "weibull"}, optional
            The distribution to fit, by default ``"all"``: the four.

        Returns
        -------
        dict[str, FrequencyAnalysisResult]
            Ordered dictionary sorted by AIC in ascending order (best fit first),
            keyed by the distribution name, with ``"all"`` by
            ``"<distribution>/<fit_method>"`` (``"gev/l_moments"``). Each result
            carries its ``fit_method``.

        Raises
        ------
        InvalidParameterError
            If ``fit_method`` is neither ``"all"`` nor one of :data:`FIT_METHODS`, or
            ``distribution`` is neither ``"all"`` nor one of the four, or the one
            combination asked for fails a precondition of its method (its own error,
            as of ``fit_<distribution>``).
        CalculationError
            If the search of the one combination asked for does not settle, or the
            method gives parameters of none of the distributions (``details.reasons``
            by combination).

        Warns
        -----
        DistributionLeftOut
            For each combination of several asked for whose method gives no
            parameters (see the class notes), maximum likelihood without a maximum
            included; that combination is not in the result, so it is never ranked.
            Its ``reason`` is ``too_few_values``, ``constant_values``,
            ``non_positive_values``, ``out_of_range``, ``unbounded_likelihood`` (the
            failed precondition of the method) or ``not_converged``.
        """
        if distribution != "all" and distribution not in _DISTRIBUTIONS:
            allowed = ", ".join(repr(name) for name in ("all", *_DISTRIBUTIONS))
            raise InvalidParameterError(
                f"Unknown distribution: {distribution!r}. Use {allowed}.",
                details={
                    "option": "distribution",
                    "reason": "choice",
                    "allowed": ["all", *_DISTRIBUTIONS],
                    "value": str(distribution),
                },
            )
        names = tuple(_DISTRIBUTIONS) if distribution == "all" else (distribution,)
        methods = FIT_METHODS if fit_method == "all" else (fit_method,)
        combinations = [(name, method) for name in names for method in methods]
        results: dict[str, FrequencyAnalysisResult] = {}
        reasons: dict[str, str] = {}
        for name, method in combinations:
            key = f"{name}/{method}" if fit_method == "all" else name
            try:
                results[key] = getattr(self, f"fit_{name}")(fit_method=method)
            except (CalculationError, InvalidParameterError) as exc:
                constraint = exc.details.get("constraint")
                if len(combinations) == 1 or (
                    isinstance(exc, InvalidParameterError) and constraint is None
                ):
                    raise
                reasons[key] = _LEFT_OUT.get(str(constraint), str(constraint))
                if constraint == "likelihood_has_a_maximum":  # no maximum, or no end
                    reasons[key] = _maximum_likelihood(name, self._data).failure
                if isinstance(exc, CalculationError):
                    reasons[key] = str(exc.details["reason"])
                warnings.warn(
                    DistributionLeftOut(
                        distribution=name,
                        fit_method=method,
                        reason=reasons[key],
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
            If ``fit_method`` is not one of :data:`FIT_METHODS`, or the sample fails a
            precondition of the method (``details.constraint``; the class notes).
        CalculationError
            If the search of the method does not settle (``not_converged``).
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
        estimate = _ESTIMATORS[fit_method]
        what = (
            f"The {_METHOD_NAMES[fit_method]} cannot fit the "
            f"{_DISTRIBUTION_NAMES[name]} distribution to these annual maxima"
        )
        hint = "Choose another fit method or distribution."
        context = {"distribution": name, "fit_method": fit_method}
        try:
            parameters = estimate(self._data, name)
        except InvalidParameterError as exc:
            if exc.details.get("reason") != "precondition_failed":
                raise
            raise InvalidParameterError(
                f"{what}: its precondition {exc.details['constraint']} fails "
                f"({exc.details['text']})",
                details={**exc.details, **context},
                hint=hint,
            ) from None
        except CalculationError as exc:
            raise CalculationError(
                f"{what}: {exc}", details={**exc.details, **context}, hint=hint
            ) from None
        return parameters

    def _build_result(
        self,
        name: str,
        fit_method: str,
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
        fit_method : str
            Method that estimated ``params``.
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

        # Anderson-Darling: the critical values of this fit by a parametric
        # bootstrap, for the L-moments only (the other refits are too slow)
        ad_stat = _anderson_darling(self._data, cdf_func)
        shape, loc, scale = params.values()  # (shape, loc, scale) of every fit
        ad_critical = (
            _ad_critical_values(name, (shape, loc, scale), self._data.size)
            if fit_method == "l_moments"
            else None
        )

        # AIC
        log_densities = np.asarray(logpdf_func(self._data))  # type: ignore[operator]
        log_likelihood = float(np.sum(log_densities))
        aic = 2.0 * k - 2.0 * log_likelihood
        outside = ~np.isfinite(log_densities)
        if outside.any():
            values = [float(value) for value in np.sort(self._data[outside])]
            warnings.warn(
                OutsideSupport(distribution=name, fit_method=fit_method, values=values),
                stacklevel=3,
            )

        exceedance = 1.0 / self._return_periods
        densities = np.exp(np.asarray(logpdf_func(quantiles)))  # type: ignore[operator]

        return FrequencyAnalysisResult(
            distribution_name=name,
            fit_method=fit_method,
            parameters=params,
            return_periods=self._return_periods.copy(),
            quantiles=np.asarray(quantiles, dtype=np.float64),
            densities=densities,
            exceedance_probabilities=exceedance,
            ks_statistic=float(ks_stat),
            ks_p_value=float(ks_pval),
            ks_valid=False,
            ad_statistic=ad_stat,
            ad_critical_values=ad_critical,
            aic=float(aic),
        )
