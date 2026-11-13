"""Seasonality of annual extremes: the circular statistics of their dates.

The date of each annual maximum (or minimum) is an angle on the circle of its calendar
year, θ = 2π (d − 0.5) / L, d the day of the year (1 = 1 January) and L its length (365
or 366 days): the middle of the day. The mean of the unit vectors of the n dates,
x̄ = Σ cos θ / n and ȳ = Σ sin θ / n, points to the mean date, atan2(ȳ, x̄), a day of a
year of 365.25 days, and its length r = √(x̄² + ȳ²) is the concentration of the dates:
1 when they all fall on one day, near 0 when they spread over the year (Bayliss and
Jones, 1993; Burn, 1997). The annual extremes are those of the complete hydrological
years of a daily series (:func:`daily_extremes`) or IMGW-PIB's published ones
(:func:`half_year_extremes`, the larger of the half-year maxima, the smaller of the
minima, as :func:`~hydrolog.statistics.characteristic_values_from_half_years`).

References
----------
Bayliss, A. C. & Jones, R. C. (1993): Peaks-over-threshold flood database: summary
    statistics and seasonality. Report No. 121, Institute of Hydrology, Wallingford.
Burn, D. H. (1997): Catchment similarity for regional flood frequency analysis using
    seasonality measures. Journal of Hydrology, 202(1–4), 212–230.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    AnnualExtremes,
    annual_extremes,
    hydrological_year,
)
from hydrolog.statistics.characteristic import (
    HalfYearValues,
    characteristic_values_from_half_years,
)

__all__ = [
    "CircularMean",
    "DatedExtreme",
    "ExtremeSeasonality",
    "circular_mean_date",
    "daily_extremes",
    "extreme_seasonality",
    "half_year_extremes",
]

Statistic = Literal["max", "min"]

_YEAR_DAYS = 365.25


class CircularMean(NamedTuple):
    """The mean date and the concentration of dates over the year.

    Attributes
    ----------
    mean_day : float
        Day of the year of the mean date (1 = 1 January, 0.5 to 365.75). With a
        concentration near 0 the dates have no clear mean and it says little.
    mean_date : str
        The month and day of ``mean_day`` rounded, in a common year (``MM-DD``).
    concentration : float
        Length of the mean vector, 0 to 1.
    """

    mean_day: float
    mean_date: str
    concentration: float


@dataclass
class DatedExtreme(JsonResultMixin):
    """The extreme of one hydrological year with its date.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    value : float
        The annual maximum or minimum, in the unit of the series.
    date : str
        Its date (ISO ``YYYY-MM-DD``), the first day it occurs.
    """

    year: int
    value: float
    date: str


@dataclass
class ExtremeSeasonality(JsonResultMixin):
    """The seasonality of the annual maxima or minima of a station.

    Attributes
    ----------
    statistic : {"max", "min"}
        Annual maxima or minima.
    parameter : str
        The variable: ``"Q"``, ``"H"`` or ``"T"``.
    source : {"daily", "half_years"}
        The complete years of a daily series, or IMGW-PIB's half-year file.
    first_year, last_year : int
        First and last hydrological year of ``years``.
    period_years : int
        Number of ``years``.
    years : list of DatedExtreme
        The dated annual extreme of each year, in order.
    mean_day : float
        Day of the year of the mean date (1 = 1 January), see :class:`CircularMean`.
    mean_date : str
        The mean date as ``MM-DD``.
    concentration : float
        Concentration r of the dates, 0 (spread) to 1 (one day).
    winter_share, summer_share : float
        Shares of the extremes dated in the winter (November to April) and the
        summer (May to October) half-year.
    """

    statistic: str
    parameter: str
    source: str
    first_year: int
    last_year: int
    period_years: int
    years: list[DatedExtreme]
    mean_day: float
    mean_date: str
    concentration: float
    winter_share: float
    summer_share: float


def _calendar(days: NDArray[np.datetime64]) -> tuple[NDArray[np.int64], ...]:
    """Calendar year, month and day of the year (1 = 1 January) of each date."""
    years = days.astype("datetime64[Y]")
    day_of_year = (days - years.astype("datetime64[D]")).astype(np.int64) + 1
    months = days.astype("datetime64[M]").astype(np.int64) % 12 + 1
    return years.astype(np.int64) + 1970, months, day_of_year


def circular_mean_date(
    dates: Sequence[str] | NDArray[np.datetime64],
) -> CircularMean:
    """Return the mean date and the concentration of dates over the year.

    Parameters
    ----------
    dates : sequence of str or NDArray[np.datetime64]
        ISO dates; at least one.

    Returns
    -------
    CircularMean
        The mean day of the year, its ``MM-DD`` and the concentration r.

    Raises
    ------
    InvalidParameterError
        If there is no date.
    """
    days = np.asarray(dates, dtype="datetime64[D]")
    if days.size == 0:
        raise InvalidParameterError("circular_mean_date needs at least one date")
    years, _, day_of_year = _calendar(days)
    leap = (years % 4 == 0) & ((years % 100 != 0) | (years % 400 == 0))
    angles = 2.0 * np.pi * (day_of_year - 0.5) / (365 + leap)
    x = float(np.mean(np.cos(angles)))
    y = float(np.mean(np.sin(angles)))
    concentration = math.hypot(x, y)
    direction = math.atan2(y, x) % (2.0 * math.pi)
    mean_day = direction / (2.0 * math.pi) * _YEAR_DAYS + 0.5
    whole = min(max(round(mean_day), 1), 365)
    moment = np.datetime64("2001-01-01", "D") + np.timedelta64(whole - 1, "D")
    return CircularMean(mean_day, str(moment)[5:], concentration)


def daily_extremes(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    statistic: Statistic,
) -> tuple[list[DatedExtreme], AnnualExtremes]:
    """Return the dated extremes of the complete hydrological years of a daily series.

    A hydrological year is complete when every one of its days has a value
    (:func:`~hydrolog.statistics._hydrological_year.annual_extremes`); the date of its
    extreme is the first day with that value.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    statistic : {"max", "min"}
        The annual maximum or minimum.

    Returns
    -------
    list of DatedExtreme
        The extreme of each complete year, in order.
    AnnualExtremes
        The complete years and those skipped as incomplete.
    """
    flows = np.asarray(values, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    extremes = annual_extremes(flows, days, statistic)
    year_of_day = hydrological_year(days)
    known = np.isfinite(flows)
    out: list[DatedExtreme] = []
    for year in extremes.years.tolist():
        mine = np.flatnonzero((year_of_day == year) & known)
        pick = np.argmax if statistic == "max" else np.argmin
        at = int(mine[pick(flows[mine])])
        out.append(DatedExtreme(int(year), float(flows[at]), str(days[at])))
    return out, extremes


def half_year_extremes(
    half_years: HalfYearValues, statistic: Statistic
) -> tuple[list[DatedExtreme], list[int]]:
    """Return IMGW-PIB's dated annual extremes from its half-year values.

    The annual maximum is the larger of the two half-year maxima (the winter one when
    they are equal), the annual minimum the smaller of the minima, each with the date
    of that half-year's extreme; a year without both half-years has none
    (:func:`~hydrolog.statistics.characteristic_values_from_half_years`).

    Parameters
    ----------
    half_years : HalfYearValues
        The published values of one variable.
    statistic : {"max", "min"}
        The annual maximum or minimum.

    Returns
    -------
    list of DatedExtreme
        The dated annual extremes, in order.
    list of int
        The years whose extreme has no date in the file (left out).
    """
    rows = characteristic_values_from_half_years(half_years).years
    out: list[DatedExtreme] = []
    undated: list[int] = []
    for row in rows:
        annual = row.annual
        value = annual.max if statistic == "max" else annual.min
        date = annual.max_date if statistic == "max" else annual.min_date
        if value is None:
            continue
        if date is None:
            undated.append(row.year)
            continue
        out.append(DatedExtreme(row.year, value, date))
    return out, undated


def extreme_seasonality(
    extremes: Sequence[DatedExtreme],
    *,
    statistic: Statistic,
    parameter: str,
    source: str,
) -> ExtremeSeasonality:
    """Compute the seasonality of dated annual extremes.

    Parameters
    ----------
    extremes : sequence of DatedExtreme
        The dated annual extremes of the years of the period; at least one.
    statistic : {"max", "min"}
        Whether they are maxima or minima.
    parameter : str
        The variable (``"Q"``, ``"H"``, ``"T"``).
    source : {"daily", "half_years"}
        Where they come from.

    Returns
    -------
    ExtremeSeasonality
        The mean date, the concentration and the half-year shares of the extremes.

    Raises
    ------
    InvalidParameterError
        If there is no extreme.
    """
    if not extremes:
        raise InvalidParameterError("extreme_seasonality needs at least one extreme")
    rows = list(extremes)
    days = np.array([row.date for row in rows], dtype="datetime64[D]")
    mean = circular_mean_date(days)
    _, months, _ = _calendar(days)
    in_winter = (months >= 11) | (months <= 4)
    return ExtremeSeasonality(
        statistic=statistic,
        parameter=parameter,
        source=source,
        first_year=rows[0].year,
        last_year=rows[-1].year,
        period_years=len(rows),
        years=rows,
        mean_day=mean.mean_day,
        mean_date=mean.mean_date,
        concentration=mean.concentration,
        winter_share=float(np.mean(in_winter)),
        summer_share=float(np.mean(~in_winter)),
    )
