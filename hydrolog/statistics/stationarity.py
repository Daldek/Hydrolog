"""Mann-Kendall trend test for hydrological time series stationarity.

Implements the non-parametric Mann-Kendall test used to detect monotonic
trends in hydrological records, as required by KZGW (Polish Water Authority)
for stationarity assessment before frequency analysis.

References
----------
Mann, H.B. (1945). Nonparametric tests against trend.
    Econometrica, 13, 245–259.
Kendall, M.G. (1975). Rank Correlation Methods.
    Griffin, London.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from hydrolog.exceptions import InvalidParameterError


@dataclass
class MannKendallResult:
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
    """

    s_statistic: float
    var_s: float
    z_score: float
    p_value: float
    trend_detected: bool
    trend_direction: str
    significance_level: float


def mann_kendall_test(
    series: NDArray[np.floating],
    alpha: float = 0.05,
) -> MannKendallResult:
    """Perform the Mann-Kendall non-parametric trend test.

    Computes the S statistic, its variance, the standardised Z score and the
    two-sided p-value.  The test is appropriate for hydro-meteorological time
    series that may be non-normal and contain ties.

    Parameters
    ----------
    series : NDArray[np.floating]
        1-D array of observations ordered in time.  Must contain at least
        3 elements.
    alpha : float, optional
        Significance level for trend detection (default 0.05).

    Returns
    -------
    MannKendallResult
        Dataclass with all test statistics and the trend decision.

    Raises
    ------
    InvalidParameterError
        If *series* is empty or contains fewer than 3 observations.

    Examples
    --------
    >>> import numpy as np
    >>> from hydrolog.statistics.stationarity import mann_kendall_test
    >>> result = mann_kendall_test(np.arange(1.0, 21.0))
    >>> result.trend_detected
    True
    >>> result.trend_direction
    'increasing'
    """
    series = np.asarray(series, dtype=float)

    if series.size == 0:
        raise InvalidParameterError(
            "series must not be empty; received an array with 0 elements."
        )
    if series.size < 3:
        raise InvalidParameterError(
            f"series must contain at least 3 observations; " f"received {series.size}."
        )

    n = series.size

    # S = Σ_{i<j} sgn(x_j - x_i)
    s: float = 0.0
    for i in range(n - 1):
        s += float(np.sum(np.sign(series[i + 1 :] - series[i])))

    # Var(S) = n(n-1)(2n+5) / 18  (no-ties formula)
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

    return MannKendallResult(
        s_statistic=s,
        var_s=var_s,
        z_score=z,
        p_value=p_value,
        trend_detected=trend_detected,
        trend_direction=trend_direction,
        significance_level=alpha,
    )
