"""Flood frequency analysis using parametric distributions.

Fits annual maximum series to GEV, Log-Normal, Pearson Type III, and Weibull
distributions.  Provides goodness-of-fit diagnostics (K-S, Anderson-Darling,
AIC) and quantile estimates for user-defined return periods.

References
----------
KZGW (2017): Metodyka opracowywania charakterystyk wezbrań i powodzi
    w zlewniach kontrolowanych — minimum 30 years of data recommended.
Coles S. (2001): An Introduction to Statistical Modeling of Extreme Values.
"""

from __future__ import annotations

import warnings
from collections import OrderedDict
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import genextreme, kstest, lognorm, pearson3, weibull_min

from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._types import EmpiricalFrequency, compute_plotting_positions

_DEFAULT_RETURN_PERIODS = np.array(
    [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0, 1000.0]
)

_AD_CRITICAL_VALUES: dict[str, float] = {
    "15%": 1.610,
    "10%": 1.933,
    "5%": 2.492,
    "2.5%": 3.070,
    "1%": 3.857,
}


@dataclass
class FrequencyAnalysisResult:
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
        Akaike Information Criterion.
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

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.high_flows import FloodFrequencyAnalysis
    >>> data = np.array([120.0, 95.0, 150.0, 200.0, 180.0, 160.0])
    >>> ffa = FloodFrequencyAnalysis(data)  # doctest: +SKIP
    >>> result = ffa.fit_gev()  # doctest: +SKIP
    """

    def __init__(
        self,
        annual_maxima: NDArray[np.float64],
        return_periods: NDArray[np.float64] | None = None,
    ) -> None:
        if len(annual_maxima) == 0:
            raise InvalidParameterError(
                "annual_maxima must not be empty."
            )
        if np.any(np.isnan(annual_maxima)):
            raise InvalidParameterError(
                "annual_maxima must not contain NaN values."
            )

        if len(annual_maxima) < 10:
            warnings.warn(
                "Sample size < 10: results may be unreliable",
                UserWarning,
                stacklevel=2,
            )
        elif len(annual_maxima) < 30:
            warnings.warn(
                "KZGW (2017) requires minimum 30 years of data "
                "for flood frequency analysis",
                UserWarning,
                stacklevel=2,
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

    def fit_log_normal(self) -> FrequencyAnalysisResult:
        """Fit a two-parameter log-normal distribution.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Notes
        -----
        Uses ``scipy.stats.lognorm.fit(data, floc=0)`` which fixes the
        location parameter at zero, yielding a standard two-parameter
        log-normal parameterisation (shape *s*, scale).
        """
        shape, loc, scale = lognorm.fit(self._data, floc=0)
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

    def fit_gev(self) -> FrequencyAnalysisResult:
        """Fit the Generalised Extreme Value distribution.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.

        Notes
        -----
        SciPy uses the sign convention ``c = -ξ`` for the shape parameter.
        """
        c, loc, scale = genextreme.fit(self._data)
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

    def fit_pearson3(self) -> FrequencyAnalysisResult:
        """Fit the Pearson Type III distribution.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.
        """
        skew, loc, scale = pearson3.fit(self._data)
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

    def fit_weibull(self) -> FrequencyAnalysisResult:
        """Fit the Weibull minimum distribution.

        Returns
        -------
        FrequencyAnalysisResult
            Fitted result with quantile estimates.
        """
        shape, loc, scale = weibull_min.fit(self._data)
        params = {"shape": shape, "loc": loc, "scale": scale}
        k = 3

        exceedance = 1.0 / self._return_periods
        quantiles = weibull_min.ppf(
            1 - exceedance, shape, loc=loc, scale=scale
        )

        return self._build_result(
            name="weibull",
            params=params,
            k=k,
            quantiles=quantiles,
            cdf_func=lambda x: weibull_min.cdf(x, shape, loc=loc, scale=scale),
            logpdf_func=lambda x: weibull_min.logpdf(
                x, shape, loc=loc, scale=scale
            ),
        )

    def empirical_frequency(
        self, method: str = "weibull"
    ) -> EmpiricalFrequency:
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

    def fit_all(self) -> dict[str, FrequencyAnalysisResult]:
        """Fit all four distributions and return results sorted by AIC.

        Returns
        -------
        dict[str, FrequencyAnalysisResult]
            Ordered dictionary keyed by distribution name, sorted by AIC
            in ascending order (best fit first).
        """
        results: dict[str, FrequencyAnalysisResult] = {
            "log_normal": self.fit_log_normal(),
            "gev": self.fit_gev(),
            "pearson3": self.fit_pearson3(),
            "weibull": self.fit_weibull(),
        }

        sorted_items = sorted(results.items(), key=lambda item: item[1].aic)
        return OrderedDict(sorted_items)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
        ks_stat, ks_pval = kstest(self._data, cdf_func)  # type: ignore[arg-type]
        warnings.warn(
            "Kolmogorov-Smirnov test critical values are invalid when "
            "parameters are estimated from the same data. Use Anderson-"
            "Darling or AIC for model selection.",
            UserWarning,
            stacklevel=3,
        )

        # Anderson-Darling (manual)
        ad_stat = _anderson_darling(self._data, cdf_func)

        # AIC
        log_likelihood = float(np.sum(logpdf_func(self._data)))  # type: ignore[operator]
        aic = 2.0 * k - 2.0 * log_likelihood

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
