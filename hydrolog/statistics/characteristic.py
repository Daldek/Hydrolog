"""Second-degree characteristic values for Polish hydrological system.

Computes characteristic flow (Q) or stage (H) values from daily time series,
following the Polish hydrological convention (NNQ–WWQ / NNH–WWH).

Additionally provides daily and monthly statistics with confidence intervals.

References
----------
IMGW-PIB methodology for characteristic values:
- WWQ = max of annual maxima
- SWQ = mean of annual maxima (NOT mean of half-year maxima)
- ZWQ = median of annual maxima
- NWQ = min of annual maxima
- (same pattern for means and minima)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import skew as scipy_skew
from scipy.stats import t as t_dist

from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    hydrological_day_of_year,
    hydrological_year,
)


@dataclass
class CharacteristicValues:
    """Second-degree characteristic flow/stage values (Polish system).

    Attributes
    ----------
    wwx : float
        Maximum of annual maxima (highest observed).
    swx : float
        Mean of annual maxima.
    zwx : float
        Median of annual maxima.
    nwx : float
        Minimum of annual maxima.
    wsx : float
        Maximum of annual means.
    ssx : float
        Mean of annual means.
    zsx : float
        Median of annual means.
    nsx : float
        Minimum of annual means.
    wnx : float
        Maximum of annual minima.
    snx : float
        Mean of annual minima.
    znx : float
        Median of annual minima.
    nnx : float
        Minimum of annual minima (lowest observed).
    period_years : int
        Number of hydrological years in the record.
    parameter : str
        Parameter type: ``"Q"`` (flow) or ``"H"`` (stage).
    """

    wwx: float
    swx: float
    zwx: float
    nwx: float
    wsx: float
    ssx: float
    zsx: float
    nsx: float
    wnx: float
    snx: float
    znx: float
    nnx: float
    period_years: int
    parameter: str


@dataclass
class DailyStatistics:
    """Statistics per hydrological day-of-year.

    Attributes
    ----------
    day_of_year : NDArray[np.float64]
        Day numbers (1..366).
    max_values : NDArray[np.float64]
        Maximum value for each day across all years.
    mean_values : NDArray[np.float64]
        Mean value for each day across all years.
    median_values : NDArray[np.float64]
        Median value for each day across all years.
    min_values : NDArray[np.float64]
        Minimum value for each day across all years.
    count : NDArray[np.float64]
        Number of observations for each day.
    """

    day_of_year: NDArray[np.float64]
    max_values: NDArray[np.float64]
    mean_values: NDArray[np.float64]
    median_values: NDArray[np.float64]
    min_values: NDArray[np.float64]
    count: NDArray[np.float64]


@dataclass
class MonthlyStatistics:
    """Monthly statistics with confidence intervals.

    Attributes
    ----------
    months : NDArray[np.float64]
        Month numbers (1..12).
    max_values : NDArray[np.float64]
        Maximum value per month.
    mean_values : NDArray[np.float64]
        Mean value per month.
    median_values : NDArray[np.float64]
        Median value per month.
    min_values : NDArray[np.float64]
        Minimum value per month.
    std_values : NDArray[np.float64]
        Standard deviation per month.
    cv_values : NDArray[np.float64]
        Coefficient of variation (std / mean) per month.
    skewness_values : NDArray[np.float64]
        Fisher-Pearson skewness coefficient per month.
    ci_lower : NDArray[np.float64]
        Lower bound of confidence interval for the mean.
    ci_upper : NDArray[np.float64]
        Upper bound of confidence interval for the mean.
    confidence_level : float
        Confidence level used (e.g. 0.95).
    """

    months: NDArray[np.float64]
    max_values: NDArray[np.float64]
    mean_values: NDArray[np.float64]
    median_values: NDArray[np.float64]
    min_values: NDArray[np.float64]
    std_values: NDArray[np.float64]
    cv_values: NDArray[np.float64]
    skewness_values: NDArray[np.float64]
    ci_lower: NDArray[np.float64]
    ci_upper: NDArray[np.float64]
    confidence_level: float


def calculate_characteristic_values(
    daily_values: NDArray[np.float64],
    dates: NDArray,
    parameter: str = "Q",
) -> CharacteristicValues:
    """Calculate second-degree characteristic values from daily data.

    Groups daily values by hydrological year (Nov 1 – Oct 31), computes
    annual maxima, means, and minima, then derives the characteristic
    statistics (WW, SW, ZW, NW for each series).

    Parameters
    ----------
    daily_values : NDArray[np.float64]
        Daily flow or stage values.
    dates : NDArray
        Corresponding dates (dtype datetime64[D]).
    parameter : str, optional
        Parameter identifier, by default ``"Q"``.

    Returns
    -------
    CharacteristicValues
        Computed characteristic values.

    Raises
    ------
    InvalidParameterError
        If arrays are empty or have mismatched lengths.

    Notes
    -----
    SWQ is the mean of annual maxima, NOT the mean of half-year maxima.
    This follows the correct IMGW-PIB methodology.
    """
    if len(daily_values) == 0 or len(dates) == 0:
        raise InvalidParameterError("Input arrays must not be empty.")
    if len(daily_values) != len(dates):
        raise InvalidParameterError(
            f"Arrays must have the same length: "
            f"daily_values has {len(daily_values)}, "
            f"dates has {len(dates)}."
        )

    hydro_years = hydrological_year(dates)
    unique_years = np.unique(hydro_years)

    annual_maxima = np.empty(len(unique_years), dtype=np.float64)
    annual_means = np.empty(len(unique_years), dtype=np.float64)
    annual_minima = np.empty(len(unique_years), dtype=np.float64)

    for i, yr in enumerate(unique_years):
        mask = hydro_years == yr
        year_vals = daily_values[mask]
        annual_maxima[i] = np.max(year_vals)
        annual_means[i] = np.mean(year_vals)
        annual_minima[i] = np.min(year_vals)

    return CharacteristicValues(
        wwx=float(np.max(annual_maxima)),
        swx=float(np.mean(annual_maxima)),
        zwx=float(np.median(annual_maxima)),
        nwx=float(np.min(annual_maxima)),
        wsx=float(np.max(annual_means)),
        ssx=float(np.mean(annual_means)),
        zsx=float(np.median(annual_means)),
        nsx=float(np.min(annual_means)),
        wnx=float(np.max(annual_minima)),
        snx=float(np.mean(annual_minima)),
        znx=float(np.median(annual_minima)),
        nnx=float(np.min(annual_minima)),
        period_years=len(unique_years),
        parameter=parameter,
    )


def calculate_daily_statistics(
    daily_values: NDArray[np.float64],
    dates: NDArray,
) -> DailyStatistics:
    """Compute statistics for each hydrological day-of-year.

    Groups values by hydrological day number (1 = Nov 1) and computes
    max, mean, median, min, and count across all years.

    Parameters
    ----------
    daily_values : NDArray[np.float64]
        Daily flow or stage values.
    dates : NDArray
        Corresponding dates (dtype datetime64[D]).

    Returns
    -------
    DailyStatistics
        Per-day statistics across all observed years.
    """
    day_numbers = hydrological_day_of_year(dates)
    unique_days = np.unique(day_numbers)

    max_vals = np.empty(len(unique_days), dtype=np.float64)
    mean_vals = np.empty(len(unique_days), dtype=np.float64)
    median_vals = np.empty(len(unique_days), dtype=np.float64)
    min_vals = np.empty(len(unique_days), dtype=np.float64)
    count_vals = np.empty(len(unique_days), dtype=np.float64)

    for i, day in enumerate(unique_days):
        mask = day_numbers == day
        day_vals = daily_values[mask]
        max_vals[i] = np.max(day_vals)
        mean_vals[i] = np.mean(day_vals)
        median_vals[i] = np.median(day_vals)
        min_vals[i] = np.min(day_vals)
        count_vals[i] = float(len(day_vals))

    return DailyStatistics(
        day_of_year=unique_days.astype(np.float64),
        max_values=max_vals,
        mean_values=mean_vals,
        median_values=median_vals,
        min_values=min_vals,
        count=count_vals,
    )


def calculate_monthly_statistics(
    daily_values: NDArray[np.float64],
    dates: NDArray,
    confidence_level: float = 0.95,
) -> MonthlyStatistics:
    """Compute monthly statistics with t-Student confidence intervals.

    Parameters
    ----------
    daily_values : NDArray[np.float64]
        Daily flow or stage values.
    dates : NDArray
        Corresponding dates (dtype datetime64[D]).
    confidence_level : float, optional
        Confidence level for CI, by default 0.95. Must be in (0, 1).

    Returns
    -------
    MonthlyStatistics
        Monthly statistics including CV, skewness, and CI.

    Raises
    ------
    InvalidParameterError
        If confidence_level is not in the open interval (0, 1).
    """
    if not (0.0 < confidence_level < 1.0):
        raise InvalidParameterError(
            f"confidence_level must be in (0, 1), got {confidence_level}."
        )

    months = dates.astype("datetime64[M]").astype(int) % 12 + 1

    max_vals = np.empty(12, dtype=np.float64)
    mean_vals = np.empty(12, dtype=np.float64)
    median_vals = np.empty(12, dtype=np.float64)
    min_vals = np.empty(12, dtype=np.float64)
    std_vals = np.empty(12, dtype=np.float64)
    cv_vals = np.empty(12, dtype=np.float64)
    skew_vals = np.empty(12, dtype=np.float64)
    ci_lo = np.empty(12, dtype=np.float64)
    ci_hi = np.empty(12, dtype=np.float64)

    alpha = 1.0 - confidence_level

    for i, m in enumerate(range(1, 13)):
        mask = months == m
        month_vals = daily_values[mask]

        n = len(month_vals)
        max_vals[i] = np.max(month_vals)
        mean_vals[i] = np.mean(month_vals)
        median_vals[i] = np.median(month_vals)
        min_vals[i] = np.min(month_vals)
        std_vals[i] = np.std(month_vals, ddof=1)
        cv_vals[i] = std_vals[i] / mean_vals[i] if mean_vals[i] != 0.0 else 0.0
        skew_vals[i] = float(scipy_skew(month_vals))

        # t-Student confidence interval for the mean
        if n > 1:
            t_val = t_dist.ppf(1.0 - alpha / 2.0, df=n - 1)
            margin = t_val * std_vals[i] / np.sqrt(n)
            ci_lo[i] = max(0.0, mean_vals[i] - margin)
            ci_hi[i] = mean_vals[i] + margin
        else:
            ci_lo[i] = mean_vals[i]
            ci_hi[i] = mean_vals[i]

    return MonthlyStatistics(
        months=np.arange(1, 13, dtype=np.float64),
        max_values=max_vals,
        mean_values=mean_vals,
        median_values=median_vals,
        min_values=min_vals,
        std_values=std_vals,
        cv_values=cv_vals,
        skewness_values=skew_vals,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        confidence_level=confidence_level,
    )
