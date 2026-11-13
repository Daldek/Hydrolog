"""Characteristic values of the first and second degree (Polish hydrological system).

Computes the characteristic values of a discharge (Q), stage (H) or water temperature
(T) series: the first degree, the minimum, mean and maximum of each hydrological year
(1 November - 31 October) and of its half-years (winter XI-IV, summer V-X), and the
second degree, the highest, mean, median and lowest of those values over the years of
a period (NNQ-WWQ, NNW-WWW). The first degree comes from a daily series
(:func:`calculate_characteristic_values`) or from IMGW-PIB's published half-year
characteristics (:func:`characteristic_values_from_half_years`).

Additionally provides daily and monthly statistics with confidence intervals.

References
----------
IMGW-PIB methodology for characteristic values:
- WWQ = max of annual maxima
- SWQ = mean of annual maxima (NOT mean of half-year maxima)
- ZWQ = median of annual maxima
- NWQ = min of annual maxima
- (same pattern for means and minima)
Byczkowski, A. (1996): Hydrologia, t. 1. Wydawnictwo SGGW, Warszawa (characteristic
values of the first and second degree).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.stats import skew as scipy_skew
from scipy.stats import t as t_dist

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    hydrological_day_of_year,
    hydrological_year,
    hydrological_year_start,
)

CHARACTERISTIC_KEYS: tuple[str, ...] = (
    "wwx",
    "swx",
    "zwx",
    "nwx",
    "wsx",
    "ssx",
    "zsx",
    "nsx",
    "wnx",
    "snx",
    "znx",
    "nnx",
)
"""Keys of the second-degree values: statistic over the years, then annual value."""


def characteristic_labels(parameter: str) -> dict[str, str]:
    """Return the Polish names of the second-degree values of a variable.

    Parameters
    ----------
    parameter : str
        ``"Q"`` (discharge), ``"H"`` (stage) or ``"T"`` (water temperature).

    Returns
    -------
    dict
        Each key of :data:`CHARACTERISTIC_KEYS` with its name: the statistic over the
        years (W highest, S mean, Z median, N lowest), the annual value it is taken
        of (W maximum, S mean, N minimum) and the variable, W for the stage
        („wodowskaz”): ``wwx`` is WWQ, WWW or WWT.
    """
    suffix = "W" if parameter == "H" else parameter
    return {
        key: f"{key[0].upper()}{key[1].upper()}{suffix}" for key in CHARACTERISTIC_KEYS
    }


def first_degree_labels(parameter: str) -> dict[str, str]:
    """Return the Polish names of the first-degree values of a variable.

    Parameters
    ----------
    parameter : str
        ``"Q"``, ``"H"`` or ``"T"``.

    Returns
    -------
    dict
        ``max``, ``mean`` and ``min`` with their names: WQ, SQ, NQ for discharge, WW,
        SW, NW for the stage, WT, ST, NT for water temperature.
    """
    suffix = "W" if parameter == "H" else parameter
    return {"max": f"W{suffix}", "mean": f"S{suffix}", "min": f"N{suffix}"}


@dataclass
class PeriodValues(JsonResultMixin):
    """First-degree values of one hydrological year or half-year.

    Attributes
    ----------
    min, mean, max : float or None
        The lowest, mean and highest value (``None`` when unknown).
    min_date, max_date : str or None
        ISO date of the lowest and highest value (its first day).
    days_with_data : int or None
        Days with a value (``None`` for published values).
    days : int or None
        Calendar days of the period (``None`` for published values).
    """

    min: float | None
    mean: float | None
    max: float | None
    min_date: str | None
    max_date: str | None
    days_with_data: int | None
    days: int | None


@dataclass
class FirstDegreeValues(JsonResultMixin):
    """First-degree values of one hydrological year and of its half-years.

    Attributes
    ----------
    year : int
        Hydrological year, named after the calendar year in which it ends.
    winter, summer, annual : PeriodValues
        The winter half-year (XI-IV), the summer half-year (V-X) and the year.
    """

    year: int
    winter: PeriodValues
    summer: PeriodValues
    annual: PeriodValues


@dataclass
class SecondDegreeValues(JsonResultMixin):
    """Second-degree values of one part of the hydrological year over the years.

    Each value is ``None`` (``NaN``) when no year has the first-degree value it is
    taken of. The keys are those of :class:`CharacteristicValues`.
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


@dataclass(frozen=True)
class HalfYearPart(JsonResultMixin):
    """Published values of one half-year, one item per year of :class:`HalfYearValues`.

    Attributes
    ----------
    min, mean, max : NDArray[np.float64]
        The half-year's lowest, mean and highest value; ``NaN`` where missing.
    min_dates, max_dates : tuple of str or None
        ISO dates of the lowest and highest value; ``None`` where missing.
    """

    min: NDArray[np.float64]
    mean: NDArray[np.float64]
    max: NDArray[np.float64]
    min_dates: tuple[str | None, ...]
    max_dates: tuple[str | None, ...]


@dataclass(frozen=True)
class HalfYearValues(JsonResultMixin):
    """IMGW-PIB's half-year and annual characteristics of one variable.

    Attributes
    ----------
    years : NDArray[np.int64]
        Hydrological years, ascending.
    winter, summer : HalfYearPart
        The values of the winter (XI-IV) and the summer (V-X) half-year.
    annual_mean : NDArray[np.float64]
        The published annual mean of each year; ``NaN`` where missing.
    """

    years: NDArray[np.int64]
    winter: HalfYearPart
    summer: HalfYearPart
    annual_mean: NDArray[np.float64]

    def select(self, first_year: int | None, last_year: int | None) -> HalfYearValues:
        """Return the years from ``first_year`` to ``last_year`` (bounds optional)."""
        keep = np.ones(self.years.size, dtype=bool)
        if first_year is not None:
            keep &= self.years >= first_year
        if last_year is not None:
            keep &= self.years <= last_year
        rows = np.flatnonzero(keep).tolist()

        def part(values: HalfYearPart) -> HalfYearPart:
            return HalfYearPart(
                values.min[keep],
                values.mean[keep],
                values.max[keep],
                tuple(values.min_dates[row] for row in rows),
                tuple(values.max_dates[row] for row in rows),
            )

        return HalfYearValues(
            self.years[keep],
            part(self.winter),
            part(self.summer),
            self.annual_mean[keep],
        )


@dataclass
class CharacteristicValues(JsonResultMixin):
    """Characteristic values of the first and second degree (Polish system).

    The second-degree values of the year are the twelve top-level keys.

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
        Number of hydrological years with a value.
    parameter : str
        Parameter type: ``"Q"`` (flow), ``"H"`` (stage) or ``"T"`` (water
        temperature).
    labels : dict
        Polish name of each second-degree key (:func:`characteristic_labels`).
    first_degree_labels : dict
        Polish names of the first-degree ``max``, ``mean`` and ``min``.
    source : {"daily", "half_years"}
        A daily series, or IMGW-PIB's published half-year characteristics.
    first_year, last_year : int or None
        First and last hydrological year with a value.
    winter, summer : SecondDegreeValues or None
        Second-degree values of the winter (XI-IV) and summer (V-X) half-years.
    years : list of FirstDegreeValues
        First-degree values of every hydrological year with a value, in order.
    incomplete_years : list of int
        Years of a daily series with a day without a value; their extremes are in
        the values above and may be milder than the true ones.
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
    labels: dict[str, str] = field(default_factory=dict)
    first_degree_labels: dict[str, str] = field(default_factory=dict)
    source: str = "daily"
    first_year: int | None = None
    last_year: int | None = None
    winter: SecondDegreeValues | None = None
    summer: SecondDegreeValues | None = None
    years: list[FirstDegreeValues] = field(default_factory=list)
    incomplete_years: list[int] = field(default_factory=list)


@dataclass
class DailyStatistics(JsonResultMixin):
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
class MonthlyStatistics(JsonResultMixin):
    """Monthly statistics with confidence intervals.

    Entries that are undefined for a month with a single value (``std_values``,
    ``cv_values``, ``skewness_values``, ``ci_lower``, ``ci_upper``) are ``NaN``
    (``null`` in JSON).

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
        Sample standard deviation (``ddof=1``) per month.
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


def _period_values(
    values: NDArray[np.float64], dates: NDArray[np.datetime64], days: int
) -> PeriodValues:
    """First-degree values of the days of one period (all with a value)."""
    if values.size == 0:
        return PeriodValues(None, None, None, None, None, 0, days)
    low = int(np.argmin(values))
    high = int(np.argmax(values))
    return PeriodValues(
        min=float(values[low]),
        mean=float(np.mean(values)),
        max=float(values[high]),
        min_date=str(dates[low]),
        max_date=str(dates[high]),
        days_with_data=int(values.size),
        days=days,
    )


def _statistics(known: Sequence[float | None]) -> tuple[float, float, float, float]:
    """Highest, mean, median and lowest of the known values; NaN without one."""
    numbers = np.array([value for value in known if value is not None], dtype=float)
    if numbers.size == 0:
        return (np.nan, np.nan, np.nan, np.nan)
    return (
        float(numbers.max()),
        float(numbers.mean()),
        float(np.median(numbers)),
        float(numbers.min()),
    )


def _second_degree(periods: Sequence[PeriodValues]) -> dict[str, float]:
    """Return the twelve second-degree values of the first-degree values."""
    out: dict[str, float] = {}
    for letter, name in (("w", "max"), ("s", "mean"), ("n", "min")):
        high, mean, median, low = _statistics([getattr(item, name) for item in periods])
        out[f"w{letter}x"] = high
        out[f"s{letter}x"] = mean
        out[f"z{letter}x"] = median
        out[f"n{letter}x"] = low
    return out


def _half_year_degree(periods: Sequence[PeriodValues]) -> SecondDegreeValues:
    known = sum(
        1
        for item in periods
        if item.min is not None or item.mean is not None or item.max is not None
    )
    return SecondDegreeValues(**_second_degree(periods), period_years=known)


def _characteristic_result(
    rows: list[FirstDegreeValues],
    parameter: str,
    source: str,
    incomplete_years: list[int],
) -> CharacteristicValues:
    return CharacteristicValues(
        **_second_degree([row.annual for row in rows]),
        period_years=len(rows),
        parameter=parameter,
        labels=characteristic_labels(parameter),
        first_degree_labels=first_degree_labels(parameter),
        source=source,
        first_year=rows[0].year,
        last_year=rows[-1].year,
        winter=_half_year_degree([row.winter for row in rows]),
        summer=_half_year_degree([row.summer for row in rows]),
        years=rows,
        incomplete_years=incomplete_years,
    )


def calculate_characteristic_values(
    daily_values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    parameter: str = "Q",
) -> CharacteristicValues:
    """Calculate the characteristic values of the first and second degree.

    Groups the days with a value by hydrological year (1 November - 31 October) and
    half-year (winter XI-IV, summer V-X) and takes the minimum, mean and maximum of
    each (the first degree, with the first day of each extreme); the second degree
    is the highest, mean, median and lowest of the annual maxima, means and minima
    (WW, SW, ZW, NW ...) and likewise of each half-year's. A year with days without a
    value takes part with the days it has and is listed in ``incomplete_years``.

    Parameters
    ----------
    daily_values : NDArray[np.float64]
        Daily flow, stage or water temperature values; ``NaN`` is a missing value.
    dates : NDArray
        Corresponding dates (dtype datetime64[D]).
    parameter : str, optional
        Parameter identifier, ``"Q"``, ``"H"`` or ``"T"``, by default ``"Q"``; it
        names the labels.

    Returns
    -------
    CharacteristicValues
        Computed characteristic values.

    Raises
    ------
    InvalidParameterError
        If arrays are empty, have mismatched lengths or hold no value.

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
    values = np.asarray(daily_values, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    known = np.isfinite(values)
    if not known.any():
        raise InvalidParameterError("The series has no value.")
    values, days = values[known], days[known]

    hydro_years = hydrological_year(days)
    months = days.astype("datetime64[M]").astype(np.int64) % 12 + 1
    in_summer = (months >= 5) & (months <= 10)
    rows: list[FirstDegreeValues] = []
    incomplete: list[int] = []
    for year in np.unique(hydro_years).tolist():
        start = hydrological_year_start(year)
        middle = np.datetime64(f"{year:04d}-05-01", "D")
        winter_days = int((middle - start).astype(np.int64))
        summer_days = int((hydrological_year_start(year + 1) - middle).astype(np.int64))
        mine = hydro_years == year
        winter = mine & ~in_summer
        summer = mine & in_summer
        row = FirstDegreeValues(
            year=int(year),
            winter=_period_values(values[winter], days[winter], winter_days),
            summer=_period_values(values[summer], days[summer], summer_days),
            annual=_period_values(values[mine], days[mine], winter_days + summer_days),
        )
        if int(mine.sum()) < winter_days + summer_days:
            incomplete.append(int(year))
        rows.append(row)
    return _characteristic_result(rows, parameter, "daily", incomplete)


def _published(part: HalfYearPart, at: int) -> PeriodValues:
    def number(value: float) -> float | None:
        return float(value) if np.isfinite(value) else None

    return PeriodValues(
        min=number(part.min[at]),
        mean=number(part.mean[at]),
        max=number(part.max[at]),
        min_date=part.min_dates[at],
        max_date=part.max_dates[at],
        days_with_data=None,
        days=None,
    )


def characteristic_values_from_half_years(
    half_years: HalfYearValues, parameter: str = "Q"
) -> CharacteristicValues:
    """Characteristic values from IMGW-PIB's published half-year characteristics.

    The half-years keep their published minimum, mean and maximum with their dates.
    The annual maximum is the larger of the two half-year maxima (the winter one when
    they are equal), the annual minimum the smaller of the minima, both with their
    date and unknown when a half-year is missing; the annual mean is the published
    one. The second degree is taken of these values as for a daily series (each from
    the years that have the value). Years without any value are left out.

    Parameters
    ----------
    half_years : HalfYearValues
        The published values of one variable.
    parameter : str, optional
        ``"Q"``, ``"H"`` or ``"T"``, by default ``"Q"``; it names the labels.

    Returns
    -------
    CharacteristicValues
        The characteristic values, ``source="half_years"``; the first-degree
        ``days_with_data`` and ``days`` are ``None``.

    Raises
    ------
    InvalidParameterError
        If no year has a value.
    """
    rows: list[FirstDegreeValues] = []
    for at, year in enumerate(half_years.years.tolist()):
        winter = _published(half_years.winter, at)
        summer = _published(half_years.summer, at)
        high: tuple[float | None, str | None] = (None, None)
        low: tuple[float | None, str | None] = (None, None)
        if winter.max is not None and summer.max is not None:
            pick = winter if winter.max >= summer.max else summer
            high = (pick.max, pick.max_date)
        if winter.min is not None and summer.min is not None:
            pick = winter if winter.min <= summer.min else summer
            low = (pick.min, pick.min_date)
        mean = half_years.annual_mean[at]
        annual = PeriodValues(
            min=low[0],
            mean=float(mean) if np.isfinite(mean) else None,
            max=high[0],
            min_date=low[1],
            max_date=high[1],
            days_with_data=None,
            days=None,
        )
        parts = (winter, summer, annual)
        if all(
            item.min is None and item.mean is None and item.max is None
            for item in parts
        ):
            continue
        rows.append(FirstDegreeValues(int(year), winter, summer, annual))
    if not rows:
        raise InvalidParameterError("The half-year characteristics hold no value.")
    return _characteristic_result(rows, parameter, "half_years", [])


def calculate_daily_statistics(
    daily_values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
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
    dates: NDArray[np.datetime64],
    confidence_level: float = 0.95,
) -> MonthlyStatistics:
    """Compute monthly statistics with t-Student confidence intervals.

    All values of a calendar month (over all years) form one sample. The
    confidence interval of the mean is ``mean ± t * s / sqrt(n)`` with the
    two-sided Student quantile ``t`` for ``n - 1`` degrees of freedom; its lower
    limit is not allowed below zero (the values are flows or stages).

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
        If confidence_level is not in the open interval (0, 1), or if some
        calendar month has no value (``details["missing_months"]`` lists them).
        Both errors are also ``ValueError``.

    Notes
    -----
    A month with a single value has no sample standard deviation (``ddof=1``),
    hence no coefficient of variation, no skewness and no t-based confidence
    interval (it needs ``n - 1 >= 1`` degrees of freedom): for such a month
    ``std_values``, ``cv_values``, ``skewness_values``, ``ci_lower`` and
    ``ci_upper`` are ``NaN`` (no warning is issued), while the maximum, mean,
    median and minimum are the value itself. Before 1.0.0 the interval of such a
    month was reported as the zero-width interval ``[mean, mean]``, which claims an
    exactly known mean, and NumPy warned about the undefined deviation.

    References
    ----------
    Student (1908): The probable error of a mean. Biometrika 6(1), 1-25.
    """
    if not (0.0 < confidence_level < 1.0):
        raise InvalidParameterError(
            f"confidence_level must be in (0, 1), got {confidence_level}."
        )

    months = dates.astype("datetime64[M]").astype(int) % 12 + 1

    counts = np.bincount(months, minlength=13)[1:]  # observations of month 1..12
    missing = [month for month in range(1, 13) if counts[month - 1] == 0]
    if missing:
        raise InvalidParameterError(
            "Monthly statistics need values in every calendar month; "
            f"no values in month(s): {', '.join(str(month) for month in missing)}",
            details={"missing_months": missing},
            hint="Provide a series that covers at least one full year.",
        )

    max_vals = np.empty(12, dtype=np.float64)
    mean_vals = np.empty(12, dtype=np.float64)
    median_vals = np.empty(12, dtype=np.float64)
    min_vals = np.empty(12, dtype=np.float64)
    std_vals = np.full(12, np.nan, dtype=np.float64)
    cv_vals = np.full(12, np.nan, dtype=np.float64)
    skew_vals = np.full(12, np.nan, dtype=np.float64)
    ci_lo = np.full(12, np.nan, dtype=np.float64)
    ci_hi = np.full(12, np.nan, dtype=np.float64)

    alpha = 1.0 - confidence_level

    for i, m in enumerate(range(1, 13)):
        mask = months == m
        month_vals = daily_values[mask]

        n = len(month_vals)
        max_vals[i] = np.max(month_vals)
        mean_vals[i] = np.mean(month_vals)
        median_vals[i] = np.median(month_vals)
        min_vals[i] = np.min(month_vals)
        if n < 2:
            continue  # deviation, CV, skewness and CI stay NaN (see Notes)

        std_vals[i] = np.std(month_vals, ddof=1)
        cv_vals[i] = std_vals[i] / mean_vals[i] if mean_vals[i] != 0.0 else 0.0
        skew_vals[i] = float(scipy_skew(month_vals))

        # t-Student confidence interval for the mean
        t_val = t_dist.ppf(1.0 - alpha / 2.0, df=n - 1)
        margin = t_val * std_vals[i] / np.sqrt(n)
        ci_lo[i] = max(0.0, mean_vals[i] - margin)
        ci_hi[i] = mean_vals[i] + margin

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
