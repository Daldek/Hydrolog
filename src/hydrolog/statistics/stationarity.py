"""Mann-Kendall trend test and Sen's slope for hydrological time series.

Implements the non-parametric Mann-Kendall test used to detect monotonic
trends in hydrological records, as required by KZGW (Polish Water Authority)
for stationarity assessment before frequency analysis, and Sen's estimate of the
slope of the trend with its confidence interval (:func:`sen_slope`).

References
----------
Mann, H.B. (1945). Nonparametric tests against trend.
    Econometrica, 13, 245–259.
Kendall, M.G. (1975). Rank Correlation Methods.
    Griffin, London.
Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau.
    Journal of the American Statistical Association, 63, 1379–1389.
Conover, W.J. (1980). Practical Nonparametric Statistics, 2nd ed. Wiley, New York
    (the intercept median(x) − slope · median(t)).
Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring.
    Van Nostrand Reinhold, New York, section 16.5 (the confidence interval).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError


@dataclass
class SenSlope(JsonResultMixin):
    """Sen's slope of a series with its intercept and confidence interval.

    Attributes
    ----------
    slope : float
        The median of the slopes (xⱼ − xᵢ) / (tⱼ − tᵢ) of all pairs tᵢ < tⱼ, in the
        unit of the values per unit of time.
    intercept : float
        median(x) − slope · median(t) (Conover, 1980): the line at t = 0.
    lower, upper : float or None
        The limits of the 100 (1 − alpha) % confidence interval of the slope;
        ``None`` when the series is too short for it.
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
        Mann-Kendall S statistic (sum of sign differences).
    var_s : float
        Variance of S under the null hypothesis of no trend.
    z_score : float
        Standardised test statistic (approximately N(0,1)).
    p_value : float
        Two-sided p-value for the null hypothesis of no trend.
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
        (Gilbert, 1987); ``None`` when the series is too short for it.
    """

    s_statistic: float
    var_s: float
    z_score: float
    p_value: float
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

    The slope is the median of the N' slopes (xⱼ − xᵢ) / (tⱼ − tᵢ) of the pairs with
    tᵢ < tⱼ (two values of the same time give no slope). The interval follows
    Gilbert (1987, section 16.5): C = z₁₋α/₂ √Var(S), M₁ = (N' − C)/2 and
    M₂ = (N' + C)/2; its limits are the M₁-th and the (M₂ + 1)-th of the ordered
    slopes, interpolated linearly between ranks (Gilbert's Example 16.5), ``None``
    when that rank is outside 1 … N'.

    Parameters
    ----------
    values : NDArray[np.floating]
        The values.
    times : NDArray[np.floating]
        Their times (years, or the steps of the series), in order.
    var_s : float
        The variance of Kendall's S that the interval is built on (that of the
        Mann-Kendall test of the values).
    alpha : float, optional
        The interval covers 1 − alpha, by default 0.05 (95 %).

    Returns
    -------
    SenSlope
        The slope, the intercept and the interval.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in length, hold a value that is not finite, the times
        decrease or no pair has two different times.

    Examples
    --------
    Gilbert (1987), Example 16.5: eight values of five time periods.

    >>> import numpy as np
    >>> from hydrolog.statistics.stationarity import sen_slope
    >>> times = np.array([1, 1, 1, 2, 3, 3, 4, 5], dtype=float)
    >>> data = np.array([10, 22, 21, 30, 22, 30, 40, 40], dtype=float)
    >>> estimate = sen_slope(data, times, var_s=58.1, alpha=0.10)
    >>> estimate.slope, round(estimate.lower, 1), round(estimate.upper, 1)
    (5.5, 2.6, 9.3)
    """
    x = np.asarray(values, dtype=np.float64)
    t = np.asarray(times, dtype=np.float64)
    if x.shape != t.shape or x.ndim != 1:
        raise InvalidParameterError("values and times must have the same length")
    if not (np.isfinite(x).all() and np.isfinite(t).all()):
        raise InvalidParameterError("values and times must be finite")
    if np.any(np.diff(t) < 0):
        raise InvalidParameterError("times must not decrease")
    first, second = np.triu_indices(x.size, 1)
    apart = t[second] > t[first]
    if not apart.any():
        raise InvalidParameterError("Sen's slope needs two values of different times")
    first, second = first[apart], second[apart]
    slopes = np.sort((x[second] - x[first]) / (t[second] - t[first]))
    count = slopes.size
    slope = float(np.median(slopes))
    reach = float(norm.ppf(1.0 - alpha / 2.0)) * math.sqrt(max(var_s, 0.0))
    ranks = np.arange(1, count + 1)

    def limit(rank: float) -> float | None:
        if not 1.0 <= rank <= count:
            return None
        return float(np.interp(rank, ranks, slopes))

    return SenSlope(
        slope=slope,
        intercept=float(np.median(x) - slope * np.median(t)),
        lower=limit((count - reach) / 2.0),
        upper=limit((count + reach) / 2.0 + 1.0),
        n_slopes=int(count),
    )


def mann_kendall_test(
    series: NDArray[np.floating],
    alpha: float = 0.05,
    times: NDArray[np.floating] | None = None,
) -> MannKendallResult:
    """Perform the Mann-Kendall non-parametric trend test.

    Computes the S statistic, its variance, the standardised Z score and the
    two-sided p-value.  The test is appropriate for hydro-meteorological time
    series that may be non-normal and contain ties.  Sen's slope of the series,
    its intercept and its 100 (1 − alpha) % confidence interval, built on the
    variance of S of the test, come with it (:func:`sen_slope`).

    Parameters
    ----------
    series : NDArray[np.floating]
        1-D array of observations ordered in time.  Must contain at least
        3 elements.
    alpha : float, optional
        Significance level for trend detection (default 0.05).
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
        If *series* is empty, contains fewer than 3 observations or a value that is
        not finite, or *times* differ in length from it or do not increase strictly.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.stationarity import mann_kendall_test
    >>> result = mann_kendall_test(np.arange(1.0, 21.0))
    >>> result.trend_detected
    True
    >>> result.trend_direction
    'increasing'
    >>> result.sen_slope
    1.0
    """
    series = np.asarray(series, dtype=float)

    if series.size == 0:
        raise InvalidParameterError(
            "series must not be empty; received an array with 0 elements."
        )
    if series.size < 3:
        raise InvalidParameterError(
            f"series must contain at least 3 observations; received {series.size}."
        )
    if not np.isfinite(series).all():
        raise InvalidParameterError(
            "series must hold finite values only; remove the missing ones first."
        )

    n = series.size
    if times is None:
        steps = np.arange(n, dtype=float)
    else:
        steps = np.asarray(times, dtype=float)
        if steps.shape != series.shape:
            raise InvalidParameterError(
                f"times must have one item per observation; received {steps.size} "
                f"for {n}."
            )
        if not np.all(np.diff(steps) > 0):
            raise InvalidParameterError("times must increase strictly.")

    # S = Σ_{i<j} sgn(x_j - x_i)
    s: float = 0.0
    for i in range(n - 1):
        s += float(np.sum(np.sign(series[i + 1 :] - series[i])))

    # Var(S) = n(n-1)(2n+5) / 18  (no-ties formula)
    # Note: when ties exist, the exact formula includes a correction:
    #   Var(S) = [n(n-1)(2n+5) - sum_g t_g(t_g-1)(2t_g+5)] / 18
    # The no-ties formula slightly overestimates Var(S), making the test
    # conservative. Acceptable for most hydrological annual series.
    var_s: float = n * (n - 1) * (2 * n + 5) / 18.0

    # Continuity-corrected Z statistic
    if s > 0:
        z: float = (s - 1.0) / np.sqrt(var_s)
    elif s == 0:
        z = 0.0
    else:
        z = (s + 1.0) / np.sqrt(var_s)

    # Two-sided p-value
    p_value: float = float(2.0 * (1.0 - norm.cdf(abs(z))))

    trend_detected: bool = p_value < alpha

    if not trend_detected:
        trend_direction = "none"
    elif s > 0:
        trend_direction = "increasing"
    else:
        trend_direction = "decreasing"

    estimate = sen_slope(series, steps, var_s=var_s, alpha=alpha)
    return MannKendallResult(
        s_statistic=s,
        var_s=var_s,
        z_score=z,
        p_value=p_value,
        trend_detected=trend_detected,
        trend_direction=trend_direction,
        significance_level=alpha,
        sen_slope=estimate.slope,
        sen_intercept=estimate.intercept,
        sen_slope_lower=estimate.lower,
        sen_slope_upper=estimate.upper,
    )
