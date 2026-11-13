"""Precipitation statistics of a daily series of a meteorological station.

Six indices of the daily precipitation P [mm] of a period of years (calendar years, or
hydrological years November - October), each a function of this module:

* :func:`precipitation_sums` -- sums of the months, half-years (XI-IV, V-X), seasons
  (DJF, MAM, JJA, SON) and years, the normals of the period and the sums in % of
  them (M1 of Nogat's plan);
* :func:`precipitation_maxima` -- the largest daily sum of each year and month and the
  largest sums of n consecutive days, with their dates (M2);
* :func:`precipitation_days` -- days with P at or above thresholds, per month and year
  (M5; R10mm and R20mm of the ETCCDI for 10 and 20 mm);
* :func:`precipitation_intensity` -- the mean annual sum and the mean precipitation of
  a wet day, SDII (M4);
* :func:`heavy_precipitation` -- the sums on the days above percentiles of the wet days
  of the period and their share in the total of the wet days, R95pTOT and R99pTOT
  (M7);
* :func:`precipitation_seasonality` -- the monthly regime of the normals, Oliver's
  precipitation concentration index and Walsh and Lawler's seasonality index (M9).

Missing days follow WMO-No. 1203 (:mod:`hydrolog.statistics._climate`): a monthly sum
needs every day, a multi-day total flagged as accumulated (``accumulated``) stands for
the missing days it covers in the sums and is a missing day for every daily statistic;
a monthly count of days is scaled to the days of the month when fewer than 11 days,
and fewer than 5 in a row, are missing; an annual value needs its twelve months, and
the annual maxima, the percentile sums and the spells need every day of the year. A
normal is the mean of the years of the period with a value when they are at least
80 % of its years.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203.
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Oliver, J. E. (1980): Monthly precipitation distribution: a comparative index.
    Professional Geographer 32(3), 300-309.
Walsh, R. P. D. & Lawler, D. M. (1981): Rainfall seasonality: description, spatial
    patterns and change through time. Weather 36(7), 201-208.
Hyndman, R. J. & Fan, Y. (1996): Sample quantiles in statistical packages. The
    American Statistician 50(4), 361-365 (quantile type 8).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics._climate import (
    DailyGrid,
    as_days,
    block_extreme,
    check_daily,
    check_year_type,
    classify,
    complete_years,
    finite,
    grid_of_values,
    mean_of,
    month_quality,
    monthly_counts,
    monthly_precipitation,
    monthly_totals,
    normal,
    rolling_sum,
    years_with_values,
)
from hydrolog.statistics.regime import seasonality_index

__all__ = [
    "DEFAULT_DURATIONS_DAYS",
    "DEFAULT_PERCENTILES",
    "DEFAULT_THRESHOLDS_MM",
    "DEFAULT_WET_DAY_MM",
    "HeavyPrecipitation",
    "HeavyPrecipitationPeriod",
    "HeavyPrecipitationYear",
    "MIN_WET_DAYS",
    "PCI_CLASSES",
    "PrecipitationDays",
    "PrecipitationDaysMonth",
    "PrecipitationDaysPeriod",
    "PrecipitationDaysYear",
    "PrecipitationDuration",
    "PrecipitationDurationSummary",
    "PrecipitationIntensity",
    "PrecipitationIntensityMonth",
    "PrecipitationIntensityPeriod",
    "PrecipitationIntensityYear",
    "PrecipitationMaxima",
    "PrecipitationMaximaPeriod",
    "PrecipitationMaximaYear",
    "PrecipitationMonthMaximum",
    "PrecipitationMonthMaximumSummary",
    "PrecipitationMonthStatistics",
    "PrecipitationMonthSum",
    "PrecipitationRegimeMonth",
    "PrecipitationSeasonality",
    "PrecipitationSeasonalityPeriod",
    "PrecipitationSeasonalityYear",
    "PrecipitationSumPeriod",
    "PrecipitationSumYear",
    "PrecipitationSums",
    "SI_CLASSES",
    "heavy_precipitation",
    "precipitation_concentration_index",
    "precipitation_days",
    "precipitation_intensity",
    "precipitation_maxima",
    "precipitation_seasonality",
    "precipitation_sums",
    "pci_class",
    "si_class",
    "PRECIPITATION_INDICES",
]

PRECIPITATION_INDICES: tuple[str, ...] = (
    "sums",
    "maxima",
    "days",
    "intensity",
    "heavy",
    "seasonality",
)
"""The indices of ``meteo precipitation``, one function of this module each."""
DEFAULT_DURATIONS_DAYS: tuple[int, ...] = (2, 3, 5, 10)
"""Durations [days] of the largest multi-day sums (Nogat's plan, M2; Rx5day of the
ETCCDI for 5)."""
DEFAULT_THRESHOLDS_MM: tuple[float, ...] = (0.1, 1.0, 10.0, 20.0)
"""Thresholds [mm] of the days with precipitation: a day with precipitation (0.1 mm),
a wet day, R10mm and R20mm of the ETCCDI."""
DEFAULT_WET_DAY_MM = 1.0
"""A wet day has at least this precipitation [mm] (ETCCDI, Zhang et al., 2011)."""
DEFAULT_PERCENTILES: tuple[float, ...] = (95.0, 99.0)
"""Percentiles of the wet days of R95pTOT and R99pTOT (ETCCDI)."""
MIN_WET_DAYS = 100
"""Fewest wet days of the period the percentiles of :func:`heavy_precipitation` are
estimated from."""

PCI_CLASSES: tuple[str, ...] = (
    "uniform",
    "moderate",
    "irregular",
    "strongly_irregular",
)
"""Classes of the precipitation concentration index (Oliver, 1980): up to 10, 15, 20
and above 20."""
_PCI_LIMITS = (10.0, 15.0, 20.0)
SI_CLASSES: tuple[str, ...] = (
    "very_equable",
    "equable_wetter_season",
    "rather_seasonal",
    "seasonal",
    "markedly_seasonal",
    "most_in_three_months",
    "extreme",
)
"""Classes of the seasonality index (Walsh and Lawler, 1981): below 0.20, 0.40, 0.60,
0.80, 1.00, 1.20, and from 1.20."""
_SI_LIMITS = (0.2, 0.4, 0.6, 0.8, 1.0, 1.2)


# --- the series on its years ----------------------------------------------------------


class _Daily(NamedTuple):
    """Daily precipitation laid on the whole years of its values."""

    grid: DailyGrid
    raw: NDArray[np.float64]  # the values, accumulated totals included
    daily: NDArray[np.float64]  # daily values: an accumulated total is missing
    accumulated: NDArray[np.bool_]
    present: NDArray[np.bool_]  # (years,) the year has a value


def _daily(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None,
    year_type: str,
) -> _Daily:
    check_year_type(year_type)
    values = np.asarray(precipitation_mm, dtype=np.float64)
    days = as_days(dates)
    check_daily(days, values)
    flags = (
        np.zeros(values.size, dtype=bool)
        if accumulated is None
        else np.asarray(accumulated, dtype=bool)
    )
    if flags.size != values.size:
        raise InvalidParameterError("accumulated must have one flag per value")
    if bool((values[np.isfinite(values)] < 0).any()):
        raise InvalidParameterError("precipitation must not be negative")
    known = np.isfinite(values)
    grid = grid_of_values(days, known, year_type)
    raw = grid.place(days, values)
    totals = grid.place_flags(days, flags) & np.isfinite(raw)
    return _Daily(
        grid,
        raw,
        np.where(totals, np.nan, raw),
        totals,
        years_with_values(grid, np.isfinite(raw)),
    )


def _first_at(values: NDArray[np.float64], largest: bool) -> int:
    """Position of the first largest (smallest) finite value."""
    return int(np.nanargmax(values) if largest else np.nanargmin(values))


# --- M1: sums, normals and % of the normal --------------------------------------------


@dataclass
class PrecipitationMonthSum(JsonResultMixin):
    """The precipitation of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month (1 = January).
    total_mm : float or None
        Monthly sum [mm]; ``None`` when a day is missing (WMO-No. 1203, 4.4.1 c).
    percent_of_normal : float or None
        ``total_mm`` in % of the normal of the month.
    """

    month: int
    total_mm: float | None
    percent_of_normal: float | None


@dataclass
class PrecipitationSumYear(JsonResultMixin):
    """The precipitation sums of one year.

    Attributes
    ----------
    year : int
        The year (a hydrological year is named after the year in which it ends).
    total_mm : float or None
        Annual sum [mm]; ``None`` without all twelve monthly sums.
    percent_of_normal : float or None
        ``total_mm`` in % of the annual normal.
    winter_mm, summer_mm : float or None
        Sums of the half-years XI-IV and V-X of the hydrological year that ends in
        ``year`` [mm].
    djf_mm, mam_mm, jja_mm, son_mm : float or None
        Sums of the seasons December (of the year before) to February, March to May,
        June to August and September to November [mm].
    months : list of PrecipitationMonthSum
        The twelve months in the order of the year.
    """

    year: int
    total_mm: float | None
    percent_of_normal: float | None
    winter_mm: float | None
    summer_mm: float | None
    djf_mm: float | None
    mam_mm: float | None
    jja_mm: float | None
    son_mm: float | None
    months: list[PrecipitationMonthSum]


@dataclass
class PrecipitationMonthStatistics(JsonResultMixin):
    """The monthly sums of one calendar month over the period.

    Attributes
    ----------
    month : int
        Calendar month.
    normal_mm : float or None
        Mean of the monthly sums when at least 80 % of the years have one [mm].
    n_years : int
        Years with a sum of the month.
    mean_mm, min_mm, max_mm : float or None
        Mean, smallest and largest sum of the month [mm].
    min_year, max_year : int or None
        The first year with the smallest and the largest sum.
    """

    month: int
    normal_mm: float | None
    n_years: int
    mean_mm: float | None
    min_mm: float | None
    min_year: int | None
    max_mm: float | None
    max_year: int | None


@dataclass
class PrecipitationSumPeriod(JsonResultMixin):
    """The normals and the statistics of the annual sums of the period.

    Attributes
    ----------
    normal_mm : float or None
        Annual normal: the mean annual sum when at least 80 % of the years of the
        period have one [mm] (WMO-No. 1203, 4.4.2).
    normal_years : int
        Years of the period with an annual sum.
    winter_normal_mm, summer_normal_mm : float or None
        Normals of the half-years [mm].
    djf_normal_mm, mam_normal_mm, jja_normal_mm, son_normal_mm : float or None
        Normals of the seasons [mm].
    mean_mm : float or None
        Mean annual sum of the years with one [mm].
    std_mm : float or None
        Its standard deviation (n - 1) [mm].
    cv : float or None
        Coefficient of variation, ``std_mm / mean_mm``.
    min_mm, max_mm : float or None
        Smallest and largest annual sum [mm].
    min_year, max_year : int or None
        Their (first) years.
    months : list of PrecipitationMonthStatistics
        The twelve months in the order of the year.
    """

    normal_mm: float | None
    normal_years: int
    winter_normal_mm: float | None
    summer_normal_mm: float | None
    djf_normal_mm: float | None
    mam_normal_mm: float | None
    jja_normal_mm: float | None
    son_normal_mm: float | None
    mean_mm: float | None
    std_mm: float | None
    cv: float | None
    min_mm: float | None
    min_year: int | None
    max_mm: float | None
    max_year: int | None
    months: list[PrecipitationMonthStatistics]


@dataclass
class PrecipitationSums(JsonResultMixin):
    """Precipitation sums of the months, half-years, seasons and years (M1).

    Attributes
    ----------
    index : str
        ``"sums"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year : int
        First and last year with a value.
    period_years : int
        Years with a value.
    years : list of PrecipitationSumYear
        Every year with a value, in order.
    period : PrecipitationSumPeriod
        Normals and the statistics of the annual sums.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    years: list[PrecipitationSumYear]
    period: PrecipitationSumPeriod


def _percent(value: float, reference: float | None) -> float | None:
    if reference is None or reference == 0 or not math.isfinite(value):
        return None
    return 100.0 * value / reference


def _spans(
    grid: DailyGrid, flat: NDArray[np.float64]
) -> dict[str, NDArray[np.float64]]:
    """Sum the half-years and seasons named after each year of the grid."""

    def span(year: int, month: int, count: int) -> float:
        start = grid.flat_index(year, month)
        if start is None or start + count > flat.size:
            return math.nan
        return float(flat[start : start + count].sum())

    parts = {
        "winter": (-1, 11, 6),
        "summer": (0, 5, 6),
        "djf": (-1, 12, 3),
        "mam": (0, 3, 3),
        "jja": (0, 6, 3),
        "son": (0, 9, 3),
    }
    return {
        name: np.array([span(int(y) + shift, month, count) for y in grid.years])
        for name, (shift, month, count) in parts.items()
    }


def precipitation_sums(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationSums:
    """Sum the months, half-years, seasons and years and their normals (M1).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing (days may be absent).
    accumulated : array_like of bool, optional
        The values that are accumulated totals of the missing days before them.
    year_type : {"calendar", "hydrological"}, optional
        Calendar years (default) or hydrological years (November - October).

    Returns
    -------
    PrecipitationSums
        The sums of each year with a value, in % of the normals of the period.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase, a
        value is negative, no day has a value or ``year_type`` is unknown.
    """
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    table = monthly_precipitation(grid, data.raw, data.accumulated)
    annual = table.sum(axis=1)
    normal_mm, normal_years = normal(annual)
    month_normals = [normal(table[:, slot])[0] for slot in range(12)]
    spans = _spans(grid, table.reshape(-1))
    span_normals = {name: normal(values)[0] for name, values in spans.items()}
    months = grid.months
    rows: list[PrecipitationSumYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationSumYear(
                year=grid.first_year + row,
                total_mm=finite(annual[row]),
                percent_of_normal=_percent(annual[row], normal_mm),
                winter_mm=finite(spans["winter"][row]),
                summer_mm=finite(spans["summer"][row]),
                djf_mm=finite(spans["djf"][row]),
                mam_mm=finite(spans["mam"][row]),
                jja_mm=finite(spans["jja"][row]),
                son_mm=finite(spans["son"][row]),
                months=[
                    PrecipitationMonthSum(
                        month=month,
                        total_mm=finite(table[row, slot]),
                        percent_of_normal=_percent(
                            table[row, slot], month_normals[slot]
                        ),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    statistics: list[PrecipitationMonthStatistics] = []
    for slot, month in enumerate(months):
        column = table[:, slot]
        have = np.isfinite(column)
        statistics.append(
            PrecipitationMonthStatistics(
                month=month,
                normal_mm=month_normals[slot],
                n_years=int(have.sum()),
                mean_mm=mean_of(column),
                min_mm=finite(column[_first_at(column, False)]) if have.any() else None,
                min_year=grid.first_year + _first_at(column, False)
                if have.any()
                else None,
                max_mm=finite(column[_first_at(column, True)]) if have.any() else None,
                max_year=grid.first_year + _first_at(column, True)
                if have.any()
                else None,
            )
        )
    valid = np.isfinite(annual)
    sums = annual[valid]
    labels = grid.years[valid]
    mean_mm = float(sums.mean()) if sums.size else None
    std_mm = float(sums.std(ddof=1)) if sums.size > 1 else None
    period = PrecipitationSumPeriod(
        normal_mm=normal_mm,
        normal_years=normal_years,
        winter_normal_mm=span_normals["winter"],
        summer_normal_mm=span_normals["summer"],
        djf_normal_mm=span_normals["djf"],
        mam_normal_mm=span_normals["mam"],
        jja_normal_mm=span_normals["jja"],
        son_normal_mm=span_normals["son"],
        mean_mm=mean_mm,
        std_mm=std_mm,
        cv=std_mm / mean_mm if std_mm is not None and mean_mm else None,
        min_mm=float(sums.min()) if sums.size else None,
        min_year=int(labels[int(np.argmin(sums))]) if sums.size else None,
        max_mm=float(sums.max()) if sums.size else None,
        max_year=int(labels[int(np.argmax(sums))]) if sums.size else None,
        months=statistics,
    )
    return PrecipitationSums(
        index="sums",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        years=rows,
        period=period,
    )


# --- M2: the largest daily and multi-day sums -----------------------------------------


@dataclass
class PrecipitationDuration(JsonResultMixin):
    """The largest sum of n consecutive days of a year.

    Attributes
    ----------
    days : int
        n, the number of consecutive days.
    sum_mm : float or None
        The largest sum of n days whose last day lies in the year [mm]; ``None`` for
        a year with a missing day.
    start_date, end_date : str or None
        Its first and last day (the first such window of the year).
    """

    days: int
    sum_mm: float | None
    start_date: str | None
    end_date: str | None


@dataclass
class PrecipitationMonthMaximum(JsonResultMixin):
    """The largest daily precipitation of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month.
    max_mm : float or None
        The largest daily sum of the days with a value [mm] (WMO-No. 1203, 4.4.1 b).
    date : str or None
        Its (first) day.
    """

    month: int
    max_mm: float | None
    date: str | None


@dataclass
class PrecipitationMaximaYear(JsonResultMixin):
    """The maxima of one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a daily value; the annual maxima need it.
    durations : list of PrecipitationDuration
        The largest sums of 1 day and of each of ``durations_days``.
    months : list of PrecipitationMonthMaximum
        The largest daily sum of each month, in the order of the year.
    """

    year: int
    complete: bool
    durations: list[PrecipitationDuration]
    months: list[PrecipitationMonthMaximum]


@dataclass
class PrecipitationDurationSummary(JsonResultMixin):
    """The annual maxima of one duration over the complete years.

    Attributes
    ----------
    days : int
        The duration [days].
    n_years : int
        Complete years.
    mean_mm, median_mm, min_mm, max_mm : float or None
        Statistics of the annual maxima [mm].
    max_start_date, max_end_date : str or None
        First and last day of the largest one.
    """

    days: int
    n_years: int
    mean_mm: float | None
    median_mm: float | None
    min_mm: float | None
    max_mm: float | None
    max_start_date: str | None
    max_end_date: str | None


@dataclass
class PrecipitationMonthMaximumSummary(JsonResultMixin):
    """The monthly maxima of one calendar month over the period.

    Attributes
    ----------
    month : int
        Calendar month.
    max_mm : float or None
        The largest daily precipitation of the month in the period [mm].
    date : str or None
        Its (first) day.
    mean_max_mm : float or None
        Mean of the monthly maxima of the months with enough days (WMO-No. 1203,
        4.4.2) [mm].
    n_months : int
        Those months.
    annual_maxima : int
        Complete years whose largest daily sum fell in this month.
    """

    month: int
    max_mm: float | None
    date: str | None
    mean_max_mm: float | None
    n_months: int
    annual_maxima: int


@dataclass
class PrecipitationMaximaPeriod(JsonResultMixin):
    """The maxima over the period.

    Attributes
    ----------
    n_years : int
        Complete years.
    incomplete_years : list of int
        Years with a value but a missing day: no annual maxima.
    durations : list of PrecipitationDurationSummary
        One per duration, 1 day first.
    months : list of PrecipitationMonthMaximumSummary
        The twelve months in the order of the year.
    """

    n_years: int
    incomplete_years: list[int]
    durations: list[PrecipitationDurationSummary]
    months: list[PrecipitationMonthMaximumSummary]


@dataclass
class PrecipitationMaxima(JsonResultMixin):
    """The largest daily and multi-day precipitation of each year and month (M2).

    Attributes
    ----------
    index : str
        ``"maxima"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period: first and last year with a value, years with a value.
    durations_days : list of int
        The durations of ``years[].durations``: 1 and the durations asked for.
    years : list of PrecipitationMaximaYear
        Every year with a value.
    period : PrecipitationMaximaPeriod
        The maxima over the complete years.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    durations_days: list[int]
    years: list[PrecipitationMaximaYear]
    period: PrecipitationMaximaPeriod


def _durations(durations_days: Sequence[int]) -> list[int]:
    chosen: set[int] = {1}
    for item in durations_days:
        if isinstance(item, bool) or int(item) != item or item < 1:
            raise InvalidParameterError(
                f"durations_days must be whole numbers of at least 1, got {item!r}"
            )
        chosen.add(int(item))
    return sorted(chosen)


def precipitation_maxima(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    durations_days: Sequence[int] = DEFAULT_DURATIONS_DAYS,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationMaxima:
    """Find the largest daily and n-day precipitation of each year and month (M2).

    The n-day sum of a day is the sum of the n days that end on it; it belongs to the
    year of its last day and needs all n days. An annual maximum needs every day of
    the year; a monthly maximum takes whatever days the month has.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    durations_days : sequence of int, optional
        Durations of the multi-day sums [days], each at least 1, by default 2, 3, 5
        and 10; the 1-day maximum is always given.
    accumulated : array_like of bool, optional
        Accumulated totals: missing days for the maxima.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationMaxima
        The maxima of each year and month and their summary over the period.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid (see :func:`precipitation_sums`) or a duration is
        not a whole number of at least 1.
    """
    durations = _durations(durations_days)
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    known = np.isfinite(data.daily)
    complete = complete_years(grid, known)
    starts = grid.year_starts()
    found = {
        days: block_extreme(rolling_sum(data.daily, days), starts) for days in durations
    }
    month_best, month_at = block_extreme(data.daily, grid.month_starts())
    month_best = month_best.reshape(grid.n_years, 12)
    month_at = month_at.reshape(grid.n_years, 12)
    enough = month_quality(grid, known).enough
    months = grid.months

    def duration(days: int, row: int) -> PrecipitationDuration:
        best, end = found[days]
        if not complete[row] or not math.isfinite(best[row]):
            return PrecipitationDuration(days, None, None, None)
        last = int(end[row])
        return PrecipitationDuration(
            days, float(best[row]), grid.iso(last - days + 1), grid.iso(last)
        )

    rows: list[PrecipitationMaximaYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationMaximaYear(
                year=grid.first_year + row,
                complete=bool(complete[row]),
                durations=[duration(days, row) for days in durations],
                months=[
                    PrecipitationMonthMaximum(
                        month,
                        finite(month_best[row, slot]),
                        grid.iso(int(month_at[row, slot])),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    chosen = data.present & complete
    summaries: list[PrecipitationDurationSummary] = []
    for days in durations:
        best, end = found[days]
        use = chosen & np.isfinite(best)
        values = best[use]
        if values.size == 0:
            summaries.append(
                PrecipitationDurationSummary(
                    days, 0, None, None, None, None, None, None
                )
            )
            continue
        top = int(end[use][int(np.argmax(values))])
        summaries.append(
            PrecipitationDurationSummary(
                days=days,
                n_years=int(values.size),
                mean_mm=float(values.mean()),
                median_mm=float(np.median(values)),
                min_mm=float(values.min()),
                max_mm=float(values.max()),
                max_start_date=grid.iso(top - days + 1),
                max_end_date=grid.iso(top),
            )
        )
    one_day_best, one_day_end = found[1]
    annual_month = grid.month[one_day_end[chosen & np.isfinite(one_day_best)]]
    month_summaries: list[PrecipitationMonthMaximumSummary] = []
    for slot, month in enumerate(months):
        column = month_best[:, slot]
        usable = column[enough[:, slot] & np.isfinite(column)]
        if np.isfinite(column).any():
            at = _first_at(column, True)
            top_mm: float | None = float(column[at])
            top_date = grid.iso(int(month_at[at, slot]))
        else:
            top_mm, top_date = None, None
        month_summaries.append(
            PrecipitationMonthMaximumSummary(
                month=month,
                max_mm=top_mm,
                date=top_date,
                mean_max_mm=float(usable.mean()) if usable.size else None,
                n_months=int(usable.size),
                annual_maxima=int((annual_month == month).sum()),
            )
        )
    return PrecipitationMaxima(
        index="maxima",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        durations_days=durations,
        years=rows,
        period=PrecipitationMaximaPeriod(
            n_years=int(chosen.sum()),
            incomplete_years=[
                int(year) for year in grid.years[data.present & ~complete]
            ],
            durations=summaries,
            months=month_summaries,
        ),
    )


# --- M5: days with precipitation ------------------------------------------------------


@dataclass
class PrecipitationDaysMonth(JsonResultMixin):
    """Days with precipitation of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    days : list of float or None
        Days with P at or above each of ``thresholds_mm``, scaled to the days of the
        month when some are missing; ``None`` without enough days (WMO-No. 1203,
        4.4.1 d). In ``period.months`` the mean over the years.
    """

    month: int
    days: list[float | None]


@dataclass
class PrecipitationDaysYear(JsonResultMixin):
    """Days with precipitation of one year.

    Attributes
    ----------
    year : int
        The year.
    days : list of float or None
        Days with P at or above each of ``thresholds_mm``: the sum of the twelve
        monthly counts; ``None`` without all of them.
    months : list of PrecipitationDaysMonth
        The twelve months in the order of the year.
    """

    year: int
    days: list[float | None]
    months: list[PrecipitationDaysMonth]


@dataclass
class PrecipitationDaysPeriod(JsonResultMixin):
    """Mean days with precipitation over the period.

    Attributes
    ----------
    n_years : int
        Years with annual counts.
    days : list of float or None
        Mean annual days at or above each threshold.
    months : list of PrecipitationDaysMonth
        Mean monthly days, in the order of the year.
    """

    n_years: int
    days: list[float | None]
    months: list[PrecipitationDaysMonth]


@dataclass
class PrecipitationDays(JsonResultMixin):
    """Days with precipitation at or above thresholds (M5).

    Attributes
    ----------
    index : str
        ``"days"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    thresholds_mm : list of float
        The thresholds [mm] of every ``days`` list.
    years : list of PrecipitationDaysYear
        Every year with a value.
    period : PrecipitationDaysPeriod
        The means of the period.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    thresholds_mm: list[float]
    years: list[PrecipitationDaysYear]
    period: PrecipitationDaysPeriod


def _positive_list(option: str, values: Sequence[float]) -> list[float]:
    chosen = [float(item) for item in values]
    if not chosen or not all(math.isfinite(item) and item > 0 for item in chosen):
        raise InvalidParameterError(
            f"{option} must be a non-empty list of positive numbers, got {values!r}"
        )
    return chosen


def precipitation_days(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    thresholds_mm: Sequence[float] = DEFAULT_THRESHOLDS_MM,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationDays:
    """Days with precipitation at or above each threshold, per month and year (M5).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    thresholds_mm : sequence of float, optional
        Thresholds [mm], each positive, by default 0.1, 1, 10 and 20 (R10mm and
        R20mm of the ETCCDI for 10 and 20).
    accumulated : array_like of bool, optional
        Accumulated totals: missing days for the counts.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationDays
        The days of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or a threshold is not a positive number.
    """
    thresholds = _positive_list("thresholds_mm", thresholds_mm)
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    with np.errstate(invalid="ignore"):
        tables = [
            monthly_counts(grid, data.daily, data.daily >= threshold)
            for threshold in thresholds
        ]
    annual = [table.sum(axis=1) for table in tables]
    months = grid.months
    rows: list[PrecipitationDaysYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationDaysYear(
                year=grid.first_year + row,
                days=[finite(values[row]) for values in annual],
                months=[
                    PrecipitationDaysMonth(
                        month, [finite(table[row, slot]) for table in tables]
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    valid = np.isfinite(annual[0])
    return PrecipitationDays(
        index="days",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        thresholds_mm=thresholds,
        years=rows,
        period=PrecipitationDaysPeriod(
            n_years=int(valid.sum()),
            days=[mean_of(values[valid]) for values in annual],
            months=[
                PrecipitationDaysMonth(
                    month, [mean_of(table[:, slot]) for table in tables]
                )
                for slot, month in enumerate(months)
            ],
        ),
    )


# --- M4: mean annual sum and intensity of a wet day -----------------------------------


@dataclass
class PrecipitationIntensityMonth(JsonResultMixin):
    """Wet days of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    wet_days : int or None
        Days with P >= ``wet_day_mm``; ``None`` when a day of the month is missing.
    wet_day_total_mm : float or None
        Their precipitation [mm].
    sdii_mm : float or None
        Mean precipitation of a wet day [mm]; in ``period.months`` pooled over the
        complete months of the period.
    """

    month: int
    wet_days: int | None
    wet_day_total_mm: float | None
    sdii_mm: float | None


@dataclass
class PrecipitationIntensityYear(JsonResultMixin):
    """The annual sum and the intensity of the wet days of one year.

    Attributes
    ----------
    year : int
        The year.
    total_mm : float or None
        Annual sum [mm] (as ``years[].total_mm`` of ``sums``).
    wet_days : int or None
        Wet days; ``None`` unless every month is complete.
    wet_day_total_mm : float or None
        Precipitation of the wet days, PRCPTOT of the ETCCDI [mm].
    sdii_mm : float or None
        Simple daily intensity index SDII: ``wet_day_total_mm / wet_days`` [mm].
    months : list of PrecipitationIntensityMonth
        The twelve months in the order of the year.
    """

    year: int
    total_mm: float | None
    wet_days: int | None
    wet_day_total_mm: float | None
    sdii_mm: float | None
    months: list[PrecipitationIntensityMonth]


@dataclass
class PrecipitationIntensityPeriod(JsonResultMixin):
    """Mean annual sum and mean intensity over the period.

    Attributes
    ----------
    mean_total_mm : float or None
        Mean annual sum of the years with one [mm].
    n_years : int
        Those years.
    mean_sdii_mm : float or None
        Mean of the annual SDII [mm].
    sdii_years : int
        Years with an SDII.
    months : list of PrecipitationIntensityMonth
        Wet days of each month pooled over its complete months (``wet_days`` and
        ``wet_day_total_mm`` are their sums), in the order of the year.
    """

    mean_total_mm: float | None
    n_years: int
    mean_sdii_mm: float | None
    sdii_years: int
    months: list[PrecipitationIntensityMonth]


@dataclass
class PrecipitationIntensity(JsonResultMixin):
    """The mean annual sum and the precipitation intensity of a wet day (M4).

    Attributes
    ----------
    index : str
        ``"intensity"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    wet_day_mm : float
        A wet day has at least this precipitation [mm].
    years : list of PrecipitationIntensityYear
        Every year with a value.
    period : PrecipitationIntensityPeriod
        The means of the period.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    wet_day_mm: float
    years: list[PrecipitationIntensityYear]
    period: PrecipitationIntensityPeriod


def _wet_day(wet_day_mm: float) -> float:
    if not (math.isfinite(wet_day_mm) and wet_day_mm > 0):
        raise InvalidParameterError(
            f"wet_day_mm must be a positive number, got {wet_day_mm!r}"
        )
    return float(wet_day_mm)


def _whole(value: float) -> int | None:
    return int(round(value)) if math.isfinite(value) else None


def precipitation_intensity(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    wet_day_mm: float = DEFAULT_WET_DAY_MM,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationIntensity:
    """Compute the mean annual sum and the mean precipitation of a wet day (M4).

    SDII = the precipitation of the wet days (P >= ``wet_day_mm``) of a year over
    their number (ETCCDI, Zhang et al., 2011); a year needs every day of every month.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    wet_day_mm : float, optional
        A wet day has at least this precipitation [mm], by default 1.
    accumulated : array_like of bool, optional
        Accumulated totals: they count in the annual sums, not in the wet days.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationIntensity
        The annual sums and the intensity of each year and month.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or ``wet_day_mm`` is not positive.
    """
    threshold = _wet_day(wet_day_mm)
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    known = np.isfinite(data.daily)
    with np.errstate(invalid="ignore"):
        wet = known & (data.daily >= threshold)
    month_totals = monthly_totals(
        grid, np.where(wet, data.daily, np.where(known, 0.0, np.nan))
    )
    month_days = monthly_totals(grid, np.where(known, wet.astype(np.float64), np.nan))
    year_totals = month_totals.sum(axis=1)
    year_days = month_days.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        year_sdii = np.where(year_days > 0, year_totals / year_days, np.nan)
        month_sdii = np.where(month_days > 0, month_totals / month_days, np.nan)
    annual = monthly_precipitation(grid, data.raw, data.accumulated).sum(axis=1)
    months = grid.months
    rows: list[PrecipitationIntensityYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            PrecipitationIntensityYear(
                year=grid.first_year + row,
                total_mm=finite(annual[row]),
                wet_days=_whole(year_days[row]),
                wet_day_total_mm=finite(year_totals[row]),
                sdii_mm=finite(year_sdii[row]),
                months=[
                    PrecipitationIntensityMonth(
                        month,
                        _whole(month_days[row, slot]),
                        finite(month_totals[row, slot]),
                        finite(month_sdii[row, slot]),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    pooled: list[PrecipitationIntensityMonth] = []
    for slot, month in enumerate(months):
        both = np.isfinite(month_totals[:, slot]) & np.isfinite(month_days[:, slot])
        days = float(month_days[both, slot].sum())
        total = float(month_totals[both, slot].sum())
        pooled.append(
            PrecipitationIntensityMonth(
                month,
                int(round(days)) if both.any() else None,
                total if both.any() else None,
                total / days if days > 0 else None,
            )
        )
    have_total = np.isfinite(annual)
    have_sdii = np.isfinite(year_sdii)
    return PrecipitationIntensity(
        index="intensity",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        wet_day_mm=threshold,
        years=rows,
        period=PrecipitationIntensityPeriod(
            mean_total_mm=mean_of(annual),
            n_years=int(have_total.sum()),
            mean_sdii_mm=mean_of(year_sdii),
            sdii_years=int(have_sdii.sum()),
            months=pooled,
        ),
    )


# --- M7: heavy precipitation ----------------------------------------------------------


@dataclass
class HeavyPrecipitationYear(JsonResultMixin):
    """Heavy precipitation of one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a daily value; the sums need it.
    wet_day_total_mm : float or None
        Precipitation of the wet days, PRCPTOT [mm].
    sums_mm : list of float or None
        For each percentile: the precipitation of the days with P above its
        threshold (R95p, R99p) [mm].
    shares_percent : list of float or None
        Those sums in % of ``wet_day_total_mm`` (R95pTOT, R99pTOT).
    days : list of int or None
        The days above each threshold.
    """

    year: int
    complete: bool
    wet_day_total_mm: float | None
    sums_mm: list[float | None]
    shares_percent: list[float | None]
    days: list[int | None]


@dataclass
class HeavyPrecipitationPeriod(JsonResultMixin):
    """The thresholds of the period and the mean shares.

    Attributes
    ----------
    wet_days : int
        Wet days of the period the percentiles are taken of.
    thresholds_mm : list of float
        The percentiles of their precipitation [mm] (quantile type 8, Hyndman and
        Fan, 1996).
    n_years : int
        Complete years.
    mean_shares_percent : list of float or None
        Mean annual share of each percentile [%].
    """

    wet_days: int
    thresholds_mm: list[float]
    n_years: int
    mean_shares_percent: list[float | None]


@dataclass
class HeavyPrecipitation(JsonResultMixin):
    """Precipitation on the days above percentiles of the wet days (M7).

    Attributes
    ----------
    index : str
        ``"heavy"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    wet_day_mm : float
        A wet day has at least this precipitation [mm].
    percentiles : list of float
        The percentiles of the wet days [%].
    years : list of HeavyPrecipitationYear
        Every year with a value.
    period : HeavyPrecipitationPeriod
        The thresholds and the mean shares.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    wet_day_mm: float
    percentiles: list[float]
    years: list[HeavyPrecipitationYear]
    period: HeavyPrecipitationPeriod


def heavy_precipitation(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    wet_day_mm: float = DEFAULT_WET_DAY_MM,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> HeavyPrecipitation:
    """Sum the days above percentiles of the wet days and give their shares (M7).

    The thresholds are percentiles of the precipitation of the wet days (P >=
    ``wet_day_mm``) of the whole period, quantile type 8 (Hyndman and Fan, 1996, as
    climdex.pcic of the ETCCDI); a year sums the precipitation of its days above each
    threshold (R95p, R99p) and gives it in % of the precipitation of its wet days
    (R95pTOT, R99pTOT; Zhang et al., 2011). A year needs every day.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    wet_day_mm : float, optional
        A wet day has at least this precipitation [mm], by default 1.
    percentiles : sequence of float, optional
        Percentiles in (0, 100), by default 95 and 99.
    accumulated : array_like of bool, optional
        Accumulated totals: missing days.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    HeavyPrecipitation
        The thresholds and the heavy precipitation of each year.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, ``wet_day_mm`` is not positive or a percentile
        is outside (0, 100).
    CalculationError
        If the period has fewer than 100 wet days (``details.reason``
        ``too_few_wet_days``).
    """
    threshold = _wet_day(wet_day_mm)
    levels = [float(item) for item in percentiles]
    if not levels or not all(math.isfinite(item) and 0 < item < 100 for item in levels):
        raise InvalidParameterError(
            f"percentiles must be numbers in (0, 100), got {percentiles!r}"
        )
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    known = np.isfinite(data.daily)
    with np.errstate(invalid="ignore"):
        wet = known & (data.daily >= threshold)
    sample = data.daily[wet]
    if sample.size < MIN_WET_DAYS:
        raise CalculationError(
            f"The percentiles need at least {MIN_WET_DAYS} wet days (P >= "
            f"{threshold:g} mm) in the period, got {sample.size}",
            details={
                "reason": "too_few_wet_days",
                "count": int(sample.size),
                "minimum": MIN_WET_DAYS,
            },
            hint="Choose a longer period.",
        )
    limits = np.percentile(sample, levels, method="median_unbiased")
    complete = complete_years(grid, known)
    filled = np.nan_to_num(data.daily)
    starts = grid.year_starts()
    totals = np.add.reduceat(np.where(filled >= threshold, filled, 0.0), starts)
    sums = [
        np.add.reduceat(np.where(filled > limit, filled, 0.0), starts)
        for limit in limits
    ]
    days = [
        np.add.reduceat((filled > limit).astype(np.int64), starts) for limit in limits
    ]
    rows: list[HeavyPrecipitationYear] = []
    shares: list[list[float]] = [[] for _ in levels]
    for row in np.flatnonzero(data.present).tolist():
        if not complete[row]:
            rows.append(
                HeavyPrecipitationYear(
                    grid.first_year + row,
                    False,
                    None,
                    [None] * len(levels),
                    [None] * len(levels),
                    [None] * len(levels),
                )
            )
            continue
        total = float(totals[row])
        year_shares: list[float | None] = []
        for number, values in enumerate(sums):
            share = 100.0 * float(values[row]) / total if total > 0 else None
            year_shares.append(share)
            if share is not None:
                shares[number].append(share)
        rows.append(
            HeavyPrecipitationYear(
                year=grid.first_year + row,
                complete=True,
                wet_day_total_mm=total,
                sums_mm=[float(values[row]) for values in sums],
                shares_percent=year_shares,
                days=[int(values[row]) for values in days],
            )
        )
    return HeavyPrecipitation(
        index="heavy",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        wet_day_mm=threshold,
        percentiles=levels,
        years=rows,
        period=HeavyPrecipitationPeriod(
            wet_days=int(sample.size),
            thresholds_mm=[float(limit) for limit in limits],
            n_years=int((data.present & complete).sum()),
            mean_shares_percent=[
                float(np.mean(values)) if values else None for values in shares
            ],
        ),
    )


# --- M9: regime and seasonality -------------------------------------------------------


def precipitation_concentration_index(monthly_mm: Sequence[float]) -> float | None:
    """Oliver's (1980) precipitation concentration index of twelve monthly sums.

    PCI = 100 Σp² / (Σp)²: 8.3 for twelve equal months, 100 for one wet month.

    Parameters
    ----------
    monthly_mm : sequence of float
        The twelve monthly sums [mm].

    Returns
    -------
    float or None
        The index; ``None`` when a sum is missing or the total is not positive.
    """
    values = np.asarray(monthly_mm, dtype=np.float64)
    total = float(values.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    return 100.0 * float(np.sum(values**2)) / total**2


def _seasonality_index(monthly_mm: Sequence[float]) -> float | None:
    """Return :func:`~hydrolog.statistics.seasonality_index` of twelve monthly sums.

    Parameters
    ----------
    monthly_mm : sequence of float
        The twelve monthly sums [mm].

    Returns
    -------
    float or None
        The index; ``None`` when a sum is missing or the total is not positive.
    """
    total = float(np.sum(np.asarray(monthly_mm, dtype=np.float64)))
    if not math.isfinite(total) or total <= 0:
        return None
    return seasonality_index(monthly_mm)


@dataclass
class PrecipitationRegimeMonth(JsonResultMixin):
    """One month of the regime of the normals.

    Attributes
    ----------
    month : int
        Calendar month.
    normal_mm : float or None
        Normal of the month [mm].
    share_percent : float or None
        Its share in the sum of the twelve normals [%].
    coefficient : float or None
        The normal over the mean of the twelve normals.
    """

    month: int
    normal_mm: float | None
    share_percent: float | None
    coefficient: float | None


@dataclass
class PrecipitationSeasonalityYear(JsonResultMixin):
    """Concentration and seasonality of the monthly sums of one year.

    Attributes
    ----------
    year : int
        The year.
    pci : float or None
        Precipitation concentration index (Oliver, 1980).
    pci_class : str or None
        Its class (:data:`PCI_CLASSES`).
    si : float or None
        Seasonality index (Walsh and Lawler, 1981).
    si_class : str or None
        Its class (:data:`SI_CLASSES`).
    """

    year: int
    pci: float | None
    pci_class: str | None
    si: float | None
    si_class: str | None


@dataclass
class PrecipitationSeasonalityPeriod(JsonResultMixin):
    """The regime of the normals and the mean indices of the years.

    Attributes
    ----------
    months : list of PrecipitationRegimeMonth
        The twelve months in the order of the year.
    pci, si : float or None
        The indices of the twelve monthly normals.
    pci_class, si_class : str or None
        Their classes.
    mean_pci, mean_si : float or None
        The means of the indices of the years.
    mean_pci_class, mean_si_class : str or None
        Their classes.
    n_years : int
        Years with all twelve monthly sums.
    """

    months: list[PrecipitationRegimeMonth]
    pci: float | None
    pci_class: str | None
    si: float | None
    si_class: str | None
    mean_pci: float | None
    mean_pci_class: str | None
    mean_si: float | None
    mean_si_class: str | None
    n_years: int


@dataclass
class PrecipitationSeasonality(JsonResultMixin):
    """The monthly regime, the concentration and the seasonality of precipitation (M9).

    Attributes
    ----------
    index : str
        ``"seasonality"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    years : list of PrecipitationSeasonalityYear
        Every year with a value.
    period : PrecipitationSeasonalityPeriod
        The regime of the normals and the mean indices.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    years: list[PrecipitationSeasonalityYear]
    period: PrecipitationSeasonalityPeriod


def pci_class(value: float | None) -> str | None:
    """Class of a precipitation concentration index (Oliver, 1980)."""
    return classify(value, _PCI_LIMITS, PCI_CLASSES)


def si_class(value: float | None) -> str | None:
    """Class of a seasonality index (Walsh and Lawler, 1981)."""
    return classify(value, _SI_LIMITS, SI_CLASSES, inclusive=False)


def precipitation_seasonality(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationSeasonality:
    """Compute the monthly regime, PCI and SI of the normals and of each year (M9).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationSeasonality
        The regime of the normals and the indices of each year.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid.
    """
    data = _daily(precipitation_mm, dates, accumulated, year_type)
    grid = data.grid
    table = monthly_precipitation(grid, data.raw, data.accumulated)
    normals = [normal(table[:, slot])[0] for slot in range(12)]
    months = grid.months
    regime: list[PrecipitationRegimeMonth]
    if all(value is not None for value in normals):
        values = [float(value) for value in normals if value is not None]
        total = sum(values)
        regime = [
            PrecipitationRegimeMonth(
                month,
                value,
                100.0 * value / total if total > 0 else None,
                value / (total / 12.0) if total > 0 else None,
            )
            for month, value in zip(months, values, strict=True)
        ]
        pci = precipitation_concentration_index(values)
        si = _seasonality_index(values)
    else:
        regime = [
            PrecipitationRegimeMonth(month, value, None, None)
            for month, value in zip(months, normals, strict=True)
        ]
        pci = si = None
    rows: list[PrecipitationSeasonalityYear] = []
    year_pci: list[float] = []
    year_si: list[float] = []
    for row in np.flatnonzero(data.present).tolist():
        year_values = table[row]
        complete = bool(np.isfinite(year_values).all())
        value_pci = precipitation_concentration_index(year_values) if complete else None
        value_si = _seasonality_index(year_values) if complete else None
        if value_pci is not None:
            year_pci.append(value_pci)
        if value_si is not None:
            year_si.append(value_si)
        rows.append(
            PrecipitationSeasonalityYear(
                grid.first_year + row,
                value_pci,
                pci_class(value_pci),
                value_si,
                si_class(value_si),
            )
        )
    mean_pci = float(np.mean(year_pci)) if year_pci else None
    mean_si = float(np.mean(year_si)) if year_si else None
    return PrecipitationSeasonality(
        index="seasonality",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        years=rows,
        period=PrecipitationSeasonalityPeriod(
            months=regime,
            pci=pci,
            pci_class=pci_class(pci),
            si=si,
            si_class=si_class(si),
            mean_pci=mean_pci,
            mean_pci_class=pci_class(mean_pci),
            mean_si=mean_si,
            mean_si_class=si_class(mean_si),
            n_years=len(year_pci),
        ),
    )
