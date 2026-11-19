"""Characteristic values of the first and second degree (Polish hydrological system).

Computes the characteristic values of a discharge (Q), stage (H) or water temperature
(T) series: the first degree, the minimum, mean and maximum of each hydrological year
(1 November - 31 October) and of its half-years (winter XI-IV, summer V-X), and the
second degree, the highest, mean, median and lowest of those values over the years of
a period (NNQ-WWQ, NNW-WWW). The first degree comes from a daily series
(:func:`calculate_characteristic_values`) or from IMGW-PIB's published half-year
characteristics (:func:`characteristic_values_from_half_years`).

Only the half-year mode gives IMGW-PIB's characteristic values. IMGW-PIB takes the
extremes of a month, half-year and year from all observations (Rocznik Hydrologiczny
2022, p. 7) and publishes no characteristic of a period with a break in observations;
the daily mode takes the extremes of the daily values (one value a day, e.g. a daily
mean) and keeps a year with missing days. Its maxima are as a rule lower and its
minima higher than IMGW-PIB's (Kłodzko 150160180, hydrological year 2010: WQ 96.0
against the published 145 m³/s, NQ 4.93 against 4.17 m³/s; the mean 19.14 against 19.1).

Daily and monthly statistics of a series: per day of the hydrological year
(:func:`calculate_daily_statistics`) and per calendar month
(:func:`calculate_monthly_statistics`), the latter with the standard deviation,
coefficient of variation and skewness of the month's values and the confidence
interval of its long-term mean. These four estimators are the Tier A formulas of the
module, each declared by its spec (:data:`SPECS`, Nogat's computation standard); the
characteristic values and the calendar aggregations are its Tier B formulas
(:data:`TIER_B`). ``docs/FORMULAS.md`` shows their equations, ranges and sources.

References
----------
Second degree from the first-degree values of each year:
- WWQ = max of annual maxima
- SWQ = mean of annual maxima (NOT mean of half-year maxima)
- ZWQ = median of annual maxima
- NWQ = min of annual maxima
- (same pattern for means and minima)
Byczkowski, A. (1996): Hydrologia, t. 1. Wydawnictwo SGGW, Warszawa (characteristic
values of the first and second degree).
IMGW-PIB: Rocznik Hydrologiczny 2022, pp. 5-8 (definitions of the published
characteristic values).

Examples
--------
NIST's certified standard deviation of its data set NumAcc1, the largest coefficient
of variation and Fisher-Pearson skewness of four non-negative values, √4 and
2/√3, and the half-width of the 95 % interval of the mean of two values two apart,
the Student quantile of one degree of freedom:

>>> sample_standard_deviation([10000001.0, 10000003.0, 10000002.0])
1.0
>>> coefficient_of_variation([4.0, 0.0, 0.0, 0.0])
2.0
>>> round(fisher_pearson_skewness([4.0, 0.0, 0.0, 0.0]), 12)
1.154700538379
>>> round(mean_interval_half_width([100.0, 102.0], 0.95), 6)
12.706205
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Final, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.stats import t as t_dist

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
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
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._hydrological_year import (
    FIRST_MONTH,
    SUMMER_FIRST_MONTH,
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
        Day numbers of the hydrological year (1 = 1 November, up to 366), those
        with a value. From 1 March a leap year's days are one higher than a common
        year's, so a day after 28 February pools two calendar dates (day 121 is 29
        February of a leap year and 1 March of a common one) and day 366 holds the
        31 October of leap years only (TIER_B ``daily_statistics``).
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

    An entry a spec refuses for the month's values is ``NaN`` (``null`` in JSON):
    every spread and the interval of a month with a single value, the interval of a
    month observed in one year, the coefficient of variation of a month with a value
    below zero or with values all zero, the skewness of a month of equal values.

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
        Standard deviation per month (spec ``sample_standard_deviation``).
    cv_values : NDArray[np.float64]
        Coefficient of variation per month (spec ``coefficient_of_variation``):
        defined for a quantity with a true zero, such as discharge.
    skewness_values : NDArray[np.float64]
        Fisher-Pearson coefficient of skewness g1 per month (spec
        ``fisher_pearson_skewness``).
    ci_lower : NDArray[np.float64]
        Lower bound of the confidence interval of the long-term mean of the month:
        the mean of the month less the half-width of spec
        ``mean_interval_half_width`` on the means of the month in the separate years
        (see :func:`calculate_monthly_statistics`); below zero where the interval
        reaches there.
    ci_upper : NDArray[np.float64]
        Upper bound of that interval.
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

    These are not IMGW-PIB's characteristic values. IMGW-PIB takes the extremes of
    a half-year and year from all observations (Rocznik Hydrologiczny 2022, p. 7)
    and publishes none for a period with a break in observations; here the extremes
    are those of the daily values and a year with missing days stays. The maxima
    are as a rule lower and the minima higher than IMGW-PIB's (Kłodzko 150160180,
    hydrological year 2010: WQ 96.0 against 145 m³/s, winter WQ 62.6 against 77.4
    m³/s, NQ 4.93 against 4.17 m³/s), while the means agree (19.14 against 19.1
    m³/s). IMGW-PIB's values come from its half-year file
    (:func:`characteristic_values_from_half_years`).
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
    in_summer = (months >= SUMMER_FIRST_MONTH) & (months < FIRST_MONTH)
    rows: list[FirstDegreeValues] = []
    incomplete: list[int] = []
    for year in np.unique(hydro_years).tolist():
        start = hydrological_year_start(year)
        middle = np.datetime64(f"{year:04d}-{SUMMER_FIRST_MONTH:02d}-01", "D")
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


class HalfYearExtremes(NamedTuple):
    """Annual maxima or minima of the years that have both half-year values.

    Attributes
    ----------
    years : NDArray[np.int64]
        Hydrological years with the winter and the summer value, ascending.
    values : NDArray[np.float64]
        The larger of the half-year maxima (the smaller of the minima) of each year.
    dates : tuple of str or None
        ISO date of each value, from the half-year it comes from; ``None`` where the
        file gives none.
    incomplete_years : list of int
        Years with the value of one half-year only, left out.
    """

    years: NDArray[np.int64]
    values: NDArray[np.float64]
    dates: tuple[str | None, ...]
    incomplete_years: list[int]


def annual_extremes_from_half_years(
    half_years: HalfYearValues, kind: Literal["max", "min"]
) -> HalfYearExtremes:
    """Annual extremes of IMGW-PIB's half-year characteristics.

    The annual maximum is the larger of the winter (XI-IV) and the summer (V-X)
    maximum, the winter one when they are equal; the annual minimum the smaller of
    the minima. A year needs both half-year values: with one only, its annual
    extreme is unknown (the other half-year may hold it), so the year is left out and
    named in ``incomplete_years``. These are the annual values of
    :func:`characteristic_values_from_half_years`.

    Parameters
    ----------
    half_years : HalfYearValues
        The published values of one variable.
    kind : {"max", "min"}
        Annual maxima or minima.

    Returns
    -------
    HalfYearExtremes
        The years with both half-years, their extremes and dates, and the years
        with one half-year only.

    Raises
    ------
    InvalidParameterError
        If ``kind`` is not ``"max"`` or ``"min"``.
    """
    if kind not in ("max", "min"):
        raise InvalidParameterError(
            f"kind must be 'max' or 'min', got {kind!r}",
            details={"option": "kind", "reason": "choice", "value": str(kind)},
        )
    winter, summer = half_years.winter, half_years.summer
    if kind == "max":
        first, second = winter.max, summer.max
        first_dates, second_dates = winter.max_dates, summer.max_dates
        pick_first = first >= second
    else:
        first, second = winter.min, summer.min
        first_dates, second_dates = winter.min_dates, summer.min_dates
        pick_first = first <= second
    known_first, known_second = np.isfinite(first), np.isfinite(second)
    both = known_first & known_second
    rows = np.flatnonzero(both).tolist()
    return HalfYearExtremes(
        years=half_years.years[both].astype(np.int64),
        values=np.where(pick_first, first, second)[both].astype(np.float64),
        dates=tuple(
            first_dates[row] if pick_first[row] else second_dates[row] for row in rows
        ),
        incomplete_years=[
            int(year) for year in half_years.years[known_first ^ known_second]
        ],
    )


def calculate_daily_statistics(
    daily_values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
) -> DailyStatistics:
    """Compute statistics for each day of the hydrological year over the years.

    Groups the values by their day of the hydrological year
    (:func:`~hydrolog.statistics._hydrological_year.hydrological_day_of_year`: 1 = 1
    November) and takes the maximum, mean, median, minimum and number of the values
    of each day. The days are counted, not dated: from 1 March a leap year's days
    are one higher than a common year's, so the statistics of a day after 28
    February pool two adjacent calendar dates (day 121: 29 February of the leap
    years and 1 March of the common ones; day 365: 30 October and 31 October) and
    day 366 holds the 31 October of the leap years only, as its ``count`` shows.

    Parameters
    ----------
    daily_values : NDArray[np.float64]
        Daily flow or stage values; every value counts (a ``NaN`` makes the
        statistics of its day ``NaN``: remove missing values first).
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


# --- the estimators of the monthly statistics (Tier A) --------------------------------

_UNIT: Final = "m3/s"
"""The unit of the samples in the documents: the formulas are homogeneous (their
scalings), so a sample in any unit gives its statistics in that unit."""

_NIST: Final = (
    "NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of "
    "Standards and Technology"
)
_NIST_SCALE: Final = Source(
    citation=_NIST,
    locator="sect. 1.3.5.6, Measures of Scale: the standard deviation "
    "s = sqrt(sum((Y - mean)**2) / (N - 1))",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm",
)
_NIST_STRD: Final = Source(
    citation="NIST Statistical Reference Datasets, Univariate Summary Statistics: "
    "NumAcc1 to NumAcc4 (Simon and Lesage 1989), certified values",
    locator="sample standard deviation (denom. = n-1), exact",
    url="https://www.itl.nist.gov/div898/strd/univ/homepage.html",
)
_NIST_SKEWNESS: Final = Source(
    citation=_NIST,
    locator="sect. 1.3.5.11, Measures of Skewness and Kurtosis: the Fisher-Pearson "
    "coefficient of skewness g1 = sum((Y - mean)**3) / N / s**3, s with the "
    "divisor N",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm",
)
_NIST_LIMITS: Final = Source(
    citation=_NIST,
    locator="sect. 1.3.5.2, Confidence Limits for the Mean: mean +- "
    "t(1 - alpha/2, N - 1) s / sqrt(N); the example of ZARR13.DAT",
    url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm",
)
_DATAPLOT_CV: Final = Source(
    citation="NIST, Dataplot Reference Manual, vol. 2, Let Subcommands: COEFFICIENT "
    "OF VARIATION",
    locator="cv = s / mean; 'should typically only be used for data measured on a "
    "ratio scale'; 'if the mean value is near zero, the coefficient of variation is "
    "sensitive to small changes in the mean'",
    url="https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/"
    "coefvari.htm",
)
_SCIPY_SKEW: Final = Source(
    citation="Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for "
    "scientific computing in Python. Nature Methods 17, 261-272",
    locator="scipy.stats.skew with bias=True, its default: the Fisher-Pearson "
    "coefficient g1 = m3 / m2**1.5",
    url="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html",
)
_STUDENT: Final = Source(
    citation="Student (1908). The probable error of a mean. Biometrika 6(1), 1-25",
    locator="the distribution of the deviation of a sample's mean in units of its "
    "standard deviation",
    access="author-provided",
)
_YEARLY_MEANS: Final = Source(
    citation="Hydrolog, ADR-0049: exact small-sample p-values and intervals on "
    "independent values",
    locator="docs/decisions/0049-exact-small-sample-p-values-and-intervals-of-"
    "independent-values.md, decision 5: the interval on the means of the month in "
    "the separate years",
)
_KLODZKO: Final = Source(
    citation="IMGW-PIB, public hydrological data: codz_2010_01..12.csv, station "
    "150160180 Kłodzko (Nysa Kłodzka)",
    locator="the daily discharges of the hydrological year 2010, 4.93 to 96.0 m3/s "
    "(tests/oracles/characteristic/imgw_150160180_codz_2010.csv)",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/",
)
_CATALOG: Final = Source(
    citation="Hydrolog, catalog command stats monthly",
    locator="src/hydrolog/catalog/groups/stats.py: confidence_level 0.95 by default, "
    "0.9 in its example",
)

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
_RATIO_SCALE: Final = Range(
    low=0.0,
    test_high=1.0e6,
    test_reason=(
        "a million m3/s exceeds the discharge of every river; the formula is "
        "homogeneous (its scaling), so the bound tests its arithmetic"
    ),
)
_DAILY_FLOWS: Final = Range(low=4.93, high=96.0, source=_KLODZKO)
"""The daily discharges of Kłodzko in the hydrological year 2010."""

_EXACT: Final = Tolerance(
    abs=1e-300,
    rel=4.5e-16,
    reason="the statistics run on the sample scaled by a power of two, so doubling "
    "or negating it changes no rounding; a result below the normal floats keeps fewer "
    "bits",
)


def _values(description: str, physical: Range) -> Variable:
    return Variable(
        name="values",
        symbol="x_i",
        unit=_UNIT,
        kind="real_array",
        description=description,
        physical=physical,
        applicability="unstated",
        typical=_DAILY_FLOWS,
    )


def _enough(least: int, source: Source, name: str = "values") -> Constraint:
    """Return the precondition of at least ``least`` values of input ``name``."""
    sample = [1.0, 2.0, 4.0, 8.0]
    return Constraint(
        name="enough_values",
        cls="precondition",
        check=lambda x: x.array(name).size >= least,
        text=f"n >= {least}",
        source=source,
        satisfied={name: sample[: least + 1]},
        violated={name: sample[: least - 1]},
        boundary={name: sample[:least]},
    )


def _deviations(data: NDArray[np.float64]) -> tuple[NDArray[np.float64], float, int]:
    """Return the deviations of a sample from its mean, both scaled, and the scale.

    The sample is divided by the power of two that brings its largest magnitude into
    [½, 1): the division is exact, so the sums neither underflow nor overflow and
    the power multiplies them back. The deviations are taken from the mean twice,
    the second pass removing the rounding of the first mean, which a large mean
    makes large next to a small spread (the corrected two-pass algorithm).
    """
    largest = float(np.max(np.abs(data)))
    exponent = math.frexp(largest)[1] if largest > 0.0 else 0
    scaled = np.ldexp(data, -exponent)
    centre = float(np.mean(scaled))
    deviations = scaled - centre
    residual = float(np.mean(deviations))
    return deviations - residual, centre + residual, exponent


def _scaled_std(deviations: NDArray[np.float64]) -> float:
    """Return the standard deviation, divisor n - 1, of deviations from the mean."""
    return math.sqrt(float(np.sum(deviations**2)) / (deviations.size - 1))


def _exact_moments(values: Sequence[float]) -> tuple[Fraction, Fraction, Fraction]:
    """Return the mean and the central moments m2 and m3 of a sample, rationally."""
    exact = [Fraction(value) for value in values]
    n = len(exact)
    mean = sum(exact, Fraction(0)) / n
    m2 = sum(((v - mean) ** 2 for v in exact), Fraction(0)) / n
    m3 = sum(((v - mean) ** 3 for v in exact), Fraction(0)) / n
    return mean, m2, m3


def _exact_variance(values: Sequence[float]) -> Fraction:
    """Return the variance of a sample with the divisor n - 1, rationally."""
    n = len(values)
    return _exact_moments(values)[1] * n / (n - 1)


_RATIONAL_SAMPLES: Final = (
    (1.0, 2.0, 3.0, 4.0, 10.0),
    (0.1, 0.2, 0.3, 0.3, 0.7, 0.6),
    (8.25, 7.86, 7.72, 7.75, 7.6, 7.47, 7.35, 7.35, 7.12, 6.99),
    tuple(1.0e9 + value for value in (0.001, 0.002, 0.004, 0.0085, 0.016, 0.031)),
)
"""Samples of the exact oracles: integers, decimals with a tie, daily discharges of
Kłodzko and a large mean with a small spread (the trap of cancellation)."""


def _mirrored(x: Values) -> dict[str, object]:
    return {"values": -x.array("values")}


def _rational_std(run: Callable[..., Values]) -> None:
    for sample in _RATIONAL_SAMPLES:
        assert_within(
            run(values=list(sample)).real("std"),
            math.sqrt(_exact_variance(sample)),
            rel=1e-14,
            reason="the exact rational variance, rounded once to a float and once by "
            "its square root; the code's pairwise sums of ten values round within a "
            "few ulp",
        )


STANDARD_DEVIATION: Final = FormulaSpec(
    name="sample_standard_deviation",
    title="Standard deviation of a sample, with the divisor n - 1",
    function="hydrolog.statistics.characteristic.sample_standard_deviation",
    family="statistic",
    equation="s = sqrt(sum((x - mean)**2) / (n - 1)) with mean = sum(x) / n",
    latex=(
        r"s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}{n - 1}},\quad "
        r"\bar{x} = \frac{1}{n}\sum_i x_i"
    ),
    variables=(
        _values(
            "The sample: the values of a calendar month over the years.", _ANY_VALUE
        ),
    ),
    outputs=(
        Output(
            name="std",
            unit=_UNIT,
            symbol="s",
            description="Standard deviation with the divisor n - 1.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_NIST_SCALE, _NIST_STRD),
    constraints=(
        _enough(
            2,
            Source(
                citation=_NIST,
                locator="sect. 1.3.5.6: the divisor N - 1 needs two values",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm",
            ),
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0},
                outputs={"std": 1.0},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated sample has the same standard deviation",
                inputs=_mirrored,
                outputs=lambda out: {"std": out.real("std")},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the standard deviation of the definition in exact rational "
                "arithmetic",
                check=_rational_std,
            ),
            Limit(
                name="equal_values",
                text="equal values have no spread",
                inputs={"values": [7.25, 7.25, 7.25]},
                expected={"std": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the deviations of equal values from their mean are "
                    "exactly zero",
                ),
            ),
        ),
    ),
    validation="none: the definition of a sample statistic",
    formula_version=1,
    status="referenced",
    conventions=(
        "the divisor n - 1 (NIST sect. 1.3.5.6; numpy.std with ddof=1)",
        "the sample in any unit; the standard deviation in its unit",
        "the deviations from the mean, centred twice, on the sample divided by a "
        "power of two; never the sums of powers E[x**2] - E[x]**2",
    ),
    traps={
        "singular_at_bound": "limit equal_values: the square root at a variance of "
        "0 is exactly 0",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "many_small_terms": "reference cases nist_strd_numacc2 to "
        "nist_strd_numacc4: 1001 values against the certified s",
        "moment_cancellation": "reference case nist_strd_numacc4: a mean of 1e7 "
        "with s = 0.1; limit exact_rational: a mean of 1e9 with a spread of 0.03",
    },
    reference_cases=("tests/fixtures/formulas/characteristic-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the variance in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_characteristic.py (limit exact_rational)",
        ),
        Oracle(
            kind="established",
            description="numpy.std with ddof=1",
            test="tests/unit/test_formulas_characteristic.py "
            "(test_the_estimators_are_numpys_and_scipys)",
            conventions=("numpy.std(ddof=1) has the divisor n - 1 of the spec",),
        ),
    ),
)


def sample_standard_deviation(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> float:
    """Return the standard deviation of a sample, spec sample_standard_deviation.

    Parameters
    ----------
    values : array_like of float
        The sample.

    Returns
    -------
    float
        Its standard deviation.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the sample: too short or not finite.
    """
    x = checked_inputs(STANDARD_DEVIATION, values=values)
    deviations, _, exponent = _deviations(x.array("values"))
    std = math.ldexp(_scaled_std(deviations), exponent)
    return checked_outputs(STANDARD_DEVIATION, {"std": std}).real("std")


def _rational_cv(run: Callable[..., Values]) -> None:
    for sample in _RATIONAL_SAMPLES:
        mean = _exact_moments(sample)[0]
        assert_within(
            run(values=list(sample)).real("cv"),
            math.sqrt(_exact_variance(sample) / mean**2),
            rel=1e-14,
            reason="the exact rational square of the coefficient, rounded once to a "
            "float and once by its square root; the code's pairwise sums round "
            "within a few ulp",
        )


COEFFICIENT_OF_VARIATION: Final = FormulaSpec(
    name="coefficient_of_variation",
    title="Coefficient of variation of a sample of a quantity with a true zero",
    function="hydrolog.statistics.characteristic.coefficient_of_variation",
    family="statistic",
    equation="Cv = s / mean with s = sqrt(sum((x - mean)**2) / (n - 1)) and "
    "mean = sum(x) / n",
    latex=(
        r"C_v = \frac{s}{\bar{x}},\quad s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}"
        r"{n - 1}},\quad \bar{x} = \frac{1}{n}\sum_i x_i"
    ),
    variables=(
        _values(
            "The sample of a quantity with a true zero (a ratio scale), such as "
            "discharge: the values of a calendar month over the years.",
            _RATIO_SCALE,
        ),
    ),
    outputs=(
        Output(
            name="cv",
            unit="-",
            symbol="C_v",
            description="Coefficient of variation, a ratio (not in per cent).",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_DATAPLOT_CV, _NIST_SCALE),
    constraints=(
        _enough(
            2,
            Source(
                citation=_NIST,
                locator="sect. 1.3.5.6: the divisor N - 1 of s needs two values",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm",
            ),
        ),
        Constraint(
            name="positive_mean",
            cls="precondition",
            check=lambda x: bool(np.any(x.array("values") > 0.0)),
            text="max(x) > 0, so that mean > 0",
            source=_DATAPLOT_CV,
            satisfied={"values": [0.0, 0.0, 1.0]},
            violated={"values": [0.0, 0.0, 0.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0},
                outputs={},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the coefficient of the definition in exact rational arithmetic",
                check=_rational_cv,
            ),
            Limit(
                name="one_positive_value",
                text="one positive value among n - 1 zeros has the largest "
                "coefficient of n values not below zero, sqrt(n)",
                inputs={"values": [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
                expected={"cv": 3.0},
                tolerance=Tolerance(
                    rel=4.5e-16,
                    reason="one rounding of the square root of the exact 9 of the "
                    "scaled sums",
                ),
            ),
            Limit(
                name="equal_values",
                text="equal positive values have no relative spread",
                inputs={"values": [7.25, 7.25, 7.25]},
                expected={"cv": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the deviations of equal values from their mean are "
                    "exactly zero",
                ),
            ),
        ),
    ),
    validation="none: the definition of a sample statistic",
    formula_version=1,
    status="oracle only",
    conventions=(
        "a ratio scale: values not below zero, of a quantity with a true zero such "
        "as discharge (Dataplot); the coefficient of a stage above an arbitrary gauge "
        "zero or of a temperature in degrees Celsius changes with the datum and is "
        "not defined here for values below zero",
        "the divisor n - 1 of the standard deviation; the coefficient as a ratio",
        "the deviations from the mean, centred twice, on the sample divided by a "
        "power of two",
    ),
    traps={
        "singular_at_bound": "constraint case positive_mean-violated: the mean 0 "
        "of zeros is refused before the division",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "moment_cancellation": "limit exact_rational: a mean of 1e9 with a spread "
        "of 0.03",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the square of the coefficient in exact rational arithmetic "
            "(fractions)",
            test="tests/unit/test_formulas_characteristic.py (limit exact_rational)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.variation with ddof=1",
            test="tests/unit/test_formulas_characteristic.py "
            "(test_the_estimators_are_numpys_and_scipys)",
            conventions=(
                "scipy.stats.variation(ddof=1) is std(ddof=1) / mean, the spec's",
            ),
        ),
    ),
)


def coefficient_of_variation(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> float:
    """Return the coefficient of variation of a sample, spec coefficient_of_variation.

    Parameters
    ----------
    values : array_like of float
        The sample, of a quantity with a true zero.

    Returns
    -------
    float
        Its coefficient of variation, a ratio.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the sample: too short, all zero, with a value below
        zero or not finite.
    """
    x = checked_inputs(COEFFICIENT_OF_VARIATION, values=values)
    deviations, centre, _ = _deviations(x.array("values"))
    cv = _scaled_std(deviations) / centre
    return checked_outputs(COEFFICIENT_OF_VARIATION, {"cv": cv}).real("cv")


def _rational_skewness(run: Callable[..., Values]) -> None:
    for sample in _RATIONAL_SAMPLES:
        _, m2, m3 = _exact_moments(sample)
        assert_within(
            run(values=list(sample)).real("skewness"),
            math.copysign(math.sqrt(m3**2 / m2**3), m3),
            abs=1e-12,
            reason="the exact rational skewness, its square rounded once; the third "
            "moment of deviations of both signs loses digits to cancellation, by at "
            "most n ulp of the sum of their absolute cubes over m2**1.5",
        )


SKEWNESS: Final = FormulaSpec(
    name="fisher_pearson_skewness",
    title="Fisher-Pearson coefficient of skewness g1 of a sample",
    function="hydrolog.statistics.characteristic.fisher_pearson_skewness",
    family="statistic",
    equation="g1 = m3 / m2**1.5 with m_k = sum((x - mean)**k) / n",
    latex=(
        r"g_1 = \frac{m_3}{m_2^{3/2}},\quad m_k = \frac{1}{n}\sum_i (x_i - "
        r"\bar{x})^k"
    ),
    variables=(
        _values(
            "The sample: the values of a calendar month over the years.", _ANY_VALUE
        ),
    ),
    outputs=(
        Output(
            name="skewness",
            unit="-",
            symbol="g_1",
            description="Fisher-Pearson coefficient of skewness.",
            physical=Range(),
        ),
    ),
    sources=(_NIST_SKEWNESS, _SCIPY_SKEW),
    constraints=(
        _enough(
            2,
            Source(
                citation=_NIST,
                locator="sect. 1.3.5.11: a sample of one value has no s",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm",
            ),
        ),
        Constraint(
            name="values_not_all_equal",
            cls="precondition",
            check=lambda x: bool(np.ptp(x.array("values")) > 0.0),
            text="min(x) < max(x)",
            source=Source(
                citation=_NIST,
                locator="sect. 1.3.5.11: g1 divides by s**3, 0 for equal values",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm",
            ),
            satisfied={"values": [5.0, 5.0, 5.0, 6.0]},
            violated={"values": [5.0, 5.0, 5.0, 5.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"values": 1.0},
                outputs={},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated sample has the negated skewness",
                inputs=_mirrored,
                outputs=lambda out: {"skewness": -out.real("skewness")},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the skewness of the definition in exact rational arithmetic",
                check=_rational_skewness,
            ),
            Limit(
                name="symmetric_sample",
                text="a sample symmetric about its mean has no skewness",
                inputs={"values": [1.0, 2.0, 3.0, 4.0, 5.0]},
                expected={"skewness": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the cubes of the opposite deviations -2, -1, 1, 2 cancel "
                    "exactly",
                ),
            ),
            Limit(
                name="one_positive_value",
                text="one value apart from n - 1 equal ones has the largest skewness "
                "of n values, (n - 2) / sqrt(n - 1)",
                inputs={"values": [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
                expected={"skewness": 8.0 / 3.0},
                tolerance=Tolerance(
                    rel=2e-15,
                    reason="the moments of the scaled sample are sums of a few exact "
                    "binary fractions; m2**1.5 and the division round a few times",
                ),
            ),
        ),
    ),
    validation="none: the definition of a sample statistic",
    formula_version=1,
    status="oracle only",
    conventions=(
        "the Fisher-Pearson coefficient g1 of NIST sect. 1.3.5.11, the moments with "
        "the divisor n (scipy.stats.skew with bias=True), not the adjusted "
        "G1 = sqrt(n (n - 1)) / (n - 2) g1 of flood frequency analysis (Bulletin 17B)",
        "the sample in any unit; the skewness without one",
        "the deviations from the mean, centred twice, on the sample divided by a "
        "power of two",
    ),
    traps={
        "singular_at_bound": "constraint case values_not_all_equal-violated: m2 = 0 "
        "of equal values is refused before the division by m2**1.5",
        "gap_propagation": "type case values-nan_element: a gap is refused",
        "moment_cancellation": "limit exact_rational: a mean of 1e9 with a spread "
        "of 0.03",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the skewness in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_characteristic.py (limit exact_rational)",
        ),
        Oracle(
            kind="established",
            description="scipy.stats.skew with bias=True",
            test="tests/unit/test_formulas_characteristic.py "
            "(test_the_estimators_are_numpys_and_scipys)",
            conventions=("scipy.stats.skew(bias=True) is the spec's g1",),
        ),
    ),
)


def fisher_pearson_skewness(
    values: NDArray[np.float64] | list[float] | tuple[float, ...],
) -> float:
    """Return the skewness coefficient of a sample, spec fisher_pearson_skewness.

    Parameters
    ----------
    values : array_like of float
        The sample.

    Returns
    -------
    float
        Its Fisher-Pearson coefficient of skewness.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the sample: too short, all equal or not finite.
    """
    x = checked_inputs(SKEWNESS, values=values)
    deviations, _, _ = _deviations(x.array("values"))
    m2 = float(np.mean(deviations**2))
    m3 = float(np.mean(deviations**3))
    skewness = m3 / m2**1.5
    return checked_outputs(SKEWNESS, {"skewness": skewness}).real("skewness")


def _rational_half_width(run: Callable[..., Values]) -> None:
    """Assert the half-width of three means against its rational closed form.

    Two degrees of freedom: F(t) = 1/2 + t / (2 sqrt(2 + t**2)), so the upper
    quantile of the tail (1 - c) / 2 is t with t**2 = 2 c**2 / (1 - c**2).
    """
    samples = ((9.0, 10.0, 11.0), (0.1, 0.2, 0.7), _RATIONAL_SAMPLES[3][:3])
    for sample in samples:
        for level in (0.5, 0.9, 0.95, 0.99):
            exact = Fraction(level)
            square = 2 * exact**2 / (1 - exact**2) * _exact_variance(sample) / 3
            assert_within(
                run(yearly_means=list(sample), confidence_level=level).real(
                    "half_width"
                ),
                math.sqrt(square),
                rel=1e-13,
                reason="the closed form of the t quantile of two degrees of freedom "
                "and the variance in exact rational arithmetic; scipy's quantile, an "
                "inversion of the incomplete beta function, is good to about 1e-14",
            )


def _closed_forms(run: Callable[..., Values]) -> None:
    """Assert the quantiles of one and four degrees of freedom in closed form.

    One degree: t = tan(pi c / 2); four: the trigonometric form of Hill (1970),
    t = 2 sqrt(cos(acos(sqrt(a)) / 3) / sqrt(a) - 1) with a = 1 - c**2.
    """
    for level in (0.5, 0.9, 0.95, 0.99, 0.999):
        one = math.tan(math.pi * level / 2)
        alpha = (1 + level) * (1 - level)
        four = 2 * math.sqrt(math.cos(math.acos(math.sqrt(alpha)) / 3) / alpha**0.5 - 1)
        for sample, quantile in (
            ((100.0, 102.0), one),
            ((1.0, 2.0, 3.0, 4.0, 5.0), four),
        ):
            k = len(sample)
            spread = math.sqrt(_exact_variance(sample))
            assert_within(
                run(yearly_means=list(sample), confidence_level=level).real(
                    "half_width"
                ),
                quantile * spread / math.sqrt(k),
                rel=1e-12,
                reason="the closed forms in floating point: tan and the cosine of a "
                "third of an arc cosine round a few ulp, magnified near a level of 1 "
                "by their slopes",
            )


MEAN_INTERVAL: Final = FormulaSpec(
    name="mean_interval_half_width",
    title="Half-width of the Student t confidence interval of a mean of yearly means",
    function="hydrolog.statistics.characteristic.mean_interval_half_width",
    family="statistic",
    equation="h = t(1 - alpha/2, k - 1) s / sqrt(k) with alpha = 1 - c and "
    "s = sqrt(sum((m - mean(m))**2) / (k - 1)) of the k yearly means m",
    latex=(
        r"h = t_{1 - \alpha/2,\,k - 1}\,\frac{s}{\sqrt{k}},\quad \alpha = 1 - c,"
        r"\quad s = \sqrt{\frac{\sum_j (m_j - \bar{m})^2}{k - 1}}"
    ),
    variables=(
        Variable(
            name="yearly_means",
            symbol="m_j",
            unit=_UNIT,
            kind="real_array",
            description="Independent values: the means of a calendar month in the "
            "separate years.",
            physical=_ANY_VALUE,
            applicability="unstated",
            typical=_DAILY_FLOWS,
        ),
        Variable(
            name="confidence_level",
            symbol="c",
            unit="-",
            description="Confidence level of the two-sided interval.",
            physical=Range(
                low=0.0, high=1.0, low_inclusive=False, high_inclusive=False
            ),
            applicability="unstated",
            typical=Range(low=0.9, high=0.95, source=_CATALOG),
        ),
    ),
    outputs=(
        Output(
            name="half_width",
            unit=_UNIT,
            symbol="h",
            description="Half-width of the interval around the long-term mean.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_NIST_LIMITS, _STUDENT, _YEARLY_MEANS),
    constraints=(
        _enough(
            2,
            Source(
                citation=_NIST,
                locator="sect. 1.3.5.2: N - 1 degrees of freedom need two values",
                url="https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm",
            ),
            "yearly_means",
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"confidence_level": 1},
        scalings=(
            Scaling(
                name="unit_of_the_sample",
                inputs={"yearly_means": 1.0},
                outputs={"half_width": 1.0},
                tolerance=_EXACT,
            ),
        ),
        symmetries=(
            Symmetry(
                name="mirror",
                text="the negated means have the same half-width",
                inputs=lambda x: {
                    "yearly_means": -x.array("yearly_means"),
                    "confidence_level": x.real("confidence_level"),
                },
                outputs=lambda out: {"half_width": out.real("half_width")},
                tolerance=_EXACT,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="three means, two degrees of freedom: the closed-form quantile "
                "and the variance in exact rational arithmetic",
                check=_rational_half_width,
            ),
            Limit(
                name="closed_forms",
                text="one and four degrees of freedom: the quantiles tan(pi c / 2) "
                "and the trigonometric form of Hill (1970)",
                check=_closed_forms,
            ),
            Limit(
                name="equal_means",
                text="equal yearly means give an interval of no width",
                inputs={"yearly_means": [12.5, 12.5, 12.5]},
                expected={"half_width": 0.0},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="the deviations of equal values from their mean are "
                    "exactly zero",
                ),
            ),
        ),
    ),
    validation="none: an interval estimate; the coverage holds for independent, about "
    "normal yearly means (Student 1908)",
    formula_version=1,
    status="referenced",
    conventions=(
        "two-sided, the upper quantile of the tail (1 - c) / 2 by scipy.stats.t.isf, "
        "the tail kept exact up to the largest level below 1",
        "s with the divisor k - 1, of the yearly means centred twice on their values "
        "divided by a power of two",
        "the interval of the long-term mean of a month is its mean of all values "
        "+- h (calculate_monthly_statistics, ADR-0049), not clipped at zero",
    ),
    assumptions=(
        "the yearly means of a month are independent and about normal; its daily "
        "values are not independent (ADR-0049)",
    ),
    traps={
        "singular_at_bound": "test_a_level_next_to_one_has_a_finite_half_width: the "
        "quantile grows without bound as c nears 1; at the largest float below 1 "
        "the tail 1 - c is exact and the half-width finite",
        "gap_propagation": "type case yearly_means-nan_element: a gap is refused",
        "moment_cancellation": "limit exact_rational: yearly means of 1e9 with a "
        "spread of 0.003",
    },
    reference_cases=("tests/fixtures/formulas/characteristic-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the closed-form quantile of two degrees of freedom and the "
            "variance in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_characteristic.py (limit exact_rational)",
        ),
        Oracle(
            kind="algorithm",
            description="the closed-form quantiles of one and four degrees of "
            "freedom against scipy's inversion of the incomplete beta function",
            test="tests/unit/test_formulas_characteristic.py (limit closed_forms)",
            conventions=(
                "both the upper quantile of the tail (1 - c) / 2 of Student's t",
            ),
        ),
    ),
)


def mean_interval_half_width(
    yearly_means: NDArray[np.float64] | list[float] | tuple[float, ...],
    confidence_level: float,
) -> float:
    """Return the half-width of the interval of a mean, spec mean_interval_half_width.

    Parameters
    ----------
    yearly_means : array_like of float
        Independent values: the means of a month in the separate years.
    confidence_level : float
        Confidence level of the two-sided interval.

    Returns
    -------
    float
        The half-width of the confidence interval of their mean.

    Raises
    ------
    InvalidParameterError
        If the spec refuses the inputs: too few means, a level outside its range or
        a value not finite.
    """
    x = checked_inputs(
        MEAN_INTERVAL, yearly_means=yearly_means, confidence_level=confidence_level
    )
    means = x.array("yearly_means")
    deviations, _, exponent = _deviations(means)
    tail = (1.0 - x.real("confidence_level")) / 2.0
    quantile = float(t_dist.isf(tail, means.size - 1))
    half_width = math.ldexp(
        quantile * _scaled_std(deviations) / math.sqrt(means.size), exponent
    )
    return checked_outputs(MEAN_INTERVAL, {"half_width": half_width}).real("half_width")


_UNDEFINED: Final = frozenset({"precondition_failed", "outside_physical_range"})
"""The refusals that leave a month's estimate undefined (``NaN``)."""
_LEVEL_PROBE: Final = (0.0, 1.0)
"""Yearly means the spec of the interval accepts, to check a level by it alone."""


def _defined(function: Callable[..., float], **inputs: object) -> float:
    """Return the estimate, ``NaN`` where its spec refuses the month's values."""
    try:
        return function(**inputs)
    except InvalidParameterError as refused:
        if (refused.details or {}).get("reason") in _UNDEFINED:
            return math.nan
        raise


def calculate_monthly_statistics(
    daily_values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    confidence_level: float = 0.95,
) -> MonthlyStatistics:
    """Compute monthly statistics with t-Student confidence intervals.

    All values of a calendar month (over all years) form one sample of the maximum,
    mean, median and minimum, of the standard deviation (spec
    ``sample_standard_deviation``), the coefficient of variation (spec
    ``coefficient_of_variation``) and the skewness (spec ``fisher_pearson_skewness``).
    The confidence interval of the long-term mean of the month is the mean of all
    its values ± the half-width of spec ``mean_interval_half_width`` on the means of
    the month in the separate calendar years, one value per year, since the daily
    values of a month are strongly autocorrelated and not independent (the method
    of batch means, ADR-0049). The interval is not clipped: a stage below its
    gauge's zero, or a mean poorly known, has a lower limit below zero.

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
        If spec ``mean_interval_half_width`` refuses confidence_level (outside the
        open interval (0, 1), not finite or not a number), or if some calendar month
        has no value (``details["missing_months"]`` lists them). Both errors are
        also ``ValueError``.

    Notes
    -----
    An entry a spec refuses for the values of a month is ``NaN`` (no warning is
    issued), while the maximum, mean, median and minimum are computed: a month with
    a single value has no standard deviation, coefficient of variation or skewness;
    a month observed in a single year has no confidence interval (it needs the means
    of at least two years); a month with a value below zero or with values all zero
    has no coefficient of variation (it is defined for a quantity with a true zero);
    a month of equal values has no skewness. Before 0.8.0 the interval of a month
    with one value was reported as the zero-width interval ``[mean, mean]``. Before
    0.9.0 the interval was built on the n daily values, as if they were independent,
    3 to 25 times too narrow; its lower limit was raised to zero, above the mean of
    a month of stages below the gauge's zero; the coefficient of variation of a mean
    of zero was 0 and that of values below zero a number; and the largest level
    below 1 gave an infinite upper limit.

    References
    ----------
    Student (1908): The probable error of a mean. Biometrika 6(1), 1-25.
    """
    level = checked_inputs(
        MEAN_INTERVAL, yearly_means=_LEVEL_PROBE, confidence_level=confidence_level
    ).real("confidence_level")
    values = np.asarray(daily_values, dtype=np.float64)
    months = dates.astype("datetime64[M]").astype(int) % 12 + 1
    years = dates.astype("datetime64[Y]").astype(int)

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
    std_vals = np.empty(12, dtype=np.float64)
    cv_vals = np.empty(12, dtype=np.float64)
    skew_vals = np.empty(12, dtype=np.float64)
    ci_lo = np.empty(12, dtype=np.float64)
    ci_hi = np.empty(12, dtype=np.float64)

    for i, m in enumerate(range(1, 13)):
        mask = months == m
        month_vals = values[mask]
        max_vals[i] = np.max(month_vals)
        mean_vals[i] = np.mean(month_vals)
        median_vals[i] = np.median(month_vals)
        min_vals[i] = np.min(month_vals)
        std_vals[i] = _defined(sample_standard_deviation, values=month_vals)
        cv_vals[i] = _defined(coefficient_of_variation, values=month_vals)
        skew_vals[i] = _defined(fisher_pearson_skewness, values=month_vals)

        # the interval from the means of the month in the separate years
        month_years = years[mask]
        yearly = np.array(
            [np.mean(month_vals[month_years == y]) for y in np.unique(month_years)]
        )
        half_width = _defined(
            mean_interval_half_width, yearly_means=yearly, confidence_level=level
        )
        ci_lo[i] = mean_vals[i] - half_width
        ci_hi[i] = mean_vals[i] + half_width

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
        confidence_level=level,
    )


SPECS: Final = (STANDARD_DEVIATION, COEFFICIENT_OF_VARIATION, SKEWNESS, MEAN_INTERVAL)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""

_ROCZNIK: Final = Source(
    citation="IMGW-PIB (2023). Rocznik Hydrologiczny 2022",
    locator="pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of "
    "the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, "
    "SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie "
    "wszystkich dostępnych pomiarów i obserwacji' (p. 7)",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/"
    "Rocznik%20hydrologiczny/Rocznik%20Hydrologiczny%202022.pdf",
)
_POLR: Final = Source(
    citation="IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of "
    "2026-04-29)",
    locator="PLWSKP 13 winter half-year XI-IV, 14 summer half-year V-X, 15 year; "
    "PLWSKEX 1 minimum, 2 mean, 3 maximum; a value 99999.999 or NULL is a break in "
    "observations",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/polroczne_i_roczne/POLR_publiczne_format.txt",
)
_SUMMER_FIRST_MONTH: Final = Constant(
    name="summer_first_month",
    value=Fraction(SUMMER_FIRST_MONTH),
    unit="month",
    source=_ROCZNIK,
)

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="characteristic_first_degree",
        function="hydrolog.statistics.characteristic.calculate_characteristic_values",
        definition="The first degree of each hydrological year and of its half-years "
        "from a daily series: the minimum, mean and maximum of the days with a value, "
        "each extreme dated by the first day it occurs.",
        convention="Winter XI-IV, summer V-X, year XI-X. The extremes are those of the "
        "daily values, as a rule milder than IMGW-PIB's extremes of all observations "
        "(Kłodzko 2010: WQ 96.0 against 145 m3/s); a year with days without a value "
        "stays, with the days it has, and is listed in incomplete_years, where "
        "IMGW-PIB publishes no characteristic.",
        source=_ROCZNIK,
        constants=(_SUMMER_FIRST_MONTH,),
    ),
    TierBSpec(
        name="characteristic_second_degree",
        function="hydrolog.statistics.characteristic.calculate_characteristic_values",
        definition="The second degree of the year and of each half-year: the highest "
        "(W), mean (S), median (Z) and lowest (N) over the years of the first-degree "
        "maxima, means and minima (WWQ ... NNQ), each of the years that have it.",
        convention="SWQ is the mean of the annual maxima, never of the pooled "
        "half-year maxima; the medians (ZWQ, ZSQ, ZNQ) and WSQ, NSQ, WNQ, NWQ follow "
        "the pattern of Byczkowski (1996, author-provided); W, S, N of a stage are "
        "WWW ... NNW and of water temperature WWT ... NNT.",
        source=_ROCZNIK,
    ),
    TierBSpec(
        name="characteristic_from_half_years",
        function="hydrolog.statistics.characteristic."
        "characteristic_values_from_half_years",
        definition="The first degree from IMGW-PIB's published half-year "
        "characteristics: the half-years keep their minimum, mean and maximum with "
        "dates; the annual maximum is the larger of the half-year maxima and the "
        "annual minimum the smaller of the minima, with that half-year's date; the "
        "annual mean is the published one.",
        convention="The winter value on a tie; an annual extreme with a half-year "
        "missing (a break in observations) is unknown; a year without any value is "
        "left out; the second degree as from a daily series.",
        source=_POLR,
    ),
    TierBSpec(
        name="half_year_annual_extremes",
        function="hydrolog.statistics.characteristic.annual_extremes_from_half_years",
        definition="The annual maxima (minima) of IMGW-PIB's half-year "
        "characteristics: the larger (smaller) of the winter and the summer value of "
        "each year that has both.",
        convention="The winter value on a tie, dated from its half-year; a year with "
        "one half-year only is left out and named in incomplete_years.",
        source=_POLR,
    ),
    TierBSpec(
        name="daily_statistics",
        function="hydrolog.statistics.characteristic.calculate_daily_statistics",
        definition="The maximum, mean, median, minimum and number of the values of "
        "each day of the hydrological year over the years.",
        convention="Days counted from 1 November (TIER_B hydrological_day_of_year): "
        "after 28 February a day pools two adjacent calendar dates of leap and common "
        "years (day 121: 29 February and 1 March) and day 366 holds leap years only; "
        "every value counts, a NaN makes its day's statistics NaN.",
        source=_ROCZNIK,
    ),
    TierBSpec(
        name="monthly_statistics",
        function="hydrolog.statistics.characteristic.calculate_monthly_statistics",
        definition="The maximum, mean, median and minimum of all values of each "
        "calendar month; their standard deviation, coefficient of variation and "
        "skewness by the specs; the interval of the month's long-term mean, its mean "
        "+- the half-width of spec mean_interval_half_width on its yearly means.",
        convention="Calendar months and years; an estimate whose spec refuses the "
        "month's values is NaN; the interval is centred on the mean of all values "
        "of the month (ADR-0049) and not clipped.",
        source=_YEARLY_MEANS,
    ),
)
"""The characteristic values and the calendar aggregations of the module (CMP-2.2)."""
