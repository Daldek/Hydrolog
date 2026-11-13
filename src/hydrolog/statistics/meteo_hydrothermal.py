"""Sielianinov's hydrothermal coefficient of a meteorological station.

The coefficient relates precipitation to the sum of temperatures, a measure of the
evaporation (Selyaninov, 1928): k = P / (0.1 Σt). For a month (Skowera and Puła,
2004), P is its precipitation sum [mm] and Σt its mean daily temperature times its
days [°C], for a month with a mean above 0 °C; the months of the growing season,
April to September (Radzka, 2014), are given. For the season, P and Σt are summed over
the days of the year with a mean daily temperature above 10 °C (Selyaninov, 1928; Miś,
2026), in a year whose every day has both values. Classes of Skowera and Puła (2004,
p. 172): k <= 0.4 extremely dry, <= 0.7 very dry, <= 1.0 dry, <= 1.3 fairly dry,
<= 1.6 optimal, <= 2.0 fairly wet, <= 2.5 wet, <= 3.0 very wet, above 3.0 extremely
wet. The monthly sums and means follow WMO-No. 1203 (4.4.1 a, c).

References
----------
Selyaninov, G. T. (1928): O sel'skokhozyaystvennoy otsenke klimata (On the
    agricultural evaluation of climate). Trudy po sel'skokhozyaystvennoy meteorologii
    20, 165-177.
Skowera, B. & Puła, J. (2004): Skrajne warunki pluwiotermiczne w okresie wiosennym na
    obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177.
Radzka, E. (2014): Hydrothermal characteristics of vegetation period in central-
    eastern Poland in years 1971-2005. Folia Pomeranae Universitatis Technologiae
    Stetinensis, Agric., Aliment., Pisc., Zootech. 312(31), 133-142.
Miś, F. (2026): Spatiotemporal variability of atmospheric drought during the growing
    season in Poland. Theoretical and Applied Climatology 157, 790 (eq. 4).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._climate import (
    as_days,
    check_daily,
    classify,
    complete_years,
    finite,
    grid_of_values,
    mean_of,
    monthly_means,
    monthly_precipitation,
    years_with_values,
)

__all__ = [
    "HYDROTHERMAL_MONTHS",
    "HydrothermalCoefficient",
    "HydrothermalMonth",
    "HydrothermalMonthSummary",
    "HydrothermalPeriod",
    "HydrothermalYear",
    "SEASON_TEMPERATURE_C",
    "SIELIANINOV_CLASSES",
    "hydrothermal_coefficient",
    "sielianinov_class",
]

HYDROTHERMAL_MONTHS: tuple[int, ...] = (4, 5, 6, 7, 8, 9)
"""The months of the growing season (April to September) whose coefficient is given."""
SEASON_TEMPERATURE_C = 10.0
"""The season sums the days with a mean temperature above this [°C]."""
SIELIANINOV_CLASSES: tuple[str, ...] = (
    "extremely_dry",
    "very_dry",
    "dry",
    "fairly_dry",
    "optimal",
    "fairly_wet",
    "wet",
    "very_wet",
    "extremely_wet",
)
"""The classes of Skowera and Puła (2004), driest first."""
_LIMITS = (0.4, 0.7, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0)


def sielianinov_class(coefficient: float | None) -> str | None:
    """Return the class of a hydrothermal coefficient (Skowera and Puła, 2004)."""
    return classify(coefficient, _LIMITS, SIELIANINOV_CLASSES)


@dataclass
class HydrothermalMonth(JsonResultMixin):
    """The coefficient of one month of a year.

    Attributes
    ----------
    month : int
        Calendar month.
    coefficient : float or None
        k = 10 P / (T n): P the monthly sum [mm], T the monthly mean temperature
        [°C], n the days of the month; ``None`` without both or with T <= 0.
    sielianinov_class : str or None
        Its class (:data:`SIELIANINOV_CLASSES`).
    """

    month: int
    coefficient: float | None
    sielianinov_class: str | None


@dataclass
class HydrothermalYear(JsonResultMixin):
    """The coefficients of one year.

    Attributes
    ----------
    year : int
        The calendar year.
    months : list of HydrothermalMonth
        April to September.
    season_coefficient : float or None
        k of the days with a mean temperature above 10 °C; ``None`` unless every day
        of the year has both values.
    season_class : str or None
        Its class.
    season_days : int or None
        Those days.
    """

    year: int
    months: list[HydrothermalMonth]
    season_coefficient: float | None
    season_class: str | None
    season_days: int | None


@dataclass
class HydrothermalMonthSummary(JsonResultMixin):
    """One month over the period.

    Attributes
    ----------
    month : int
        Calendar month.
    n_years : int
        Years with a coefficient of the month.
    mean_coefficient : float or None
        Their mean.
    class_counts : dict of str to int
        How many of them fall in each class.
    """

    month: int
    n_years: int
    mean_coefficient: float | None
    class_counts: dict[str, int]


@dataclass
class HydrothermalPeriod(JsonResultMixin):
    """The coefficients over the period.

    Attributes
    ----------
    n_years : int
        Years with a season coefficient.
    mean_season_coefficient : float or None
        Their mean.
    mean_season_class : str or None
        Its class.
    months : list of HydrothermalMonthSummary
        April to September.
    """

    n_years: int
    mean_season_coefficient: float | None
    mean_season_class: str | None
    months: list[HydrothermalMonthSummary]


@dataclass
class HydrothermalCoefficient(JsonResultMixin):
    """Sielianinov's hydrothermal coefficient of months and seasons (M14).

    Attributes
    ----------
    first_year, last_year : int
        First and last calendar year with a value.
    period_years : int
        Years with a value.
    years : list of HydrothermalYear
        Every year with a value.
    period : HydrothermalPeriod
        The means and the class counts.
    """

    first_year: int
    last_year: int
    period_years: int
    years: list[HydrothermalYear]
    period: HydrothermalPeriod


def hydrothermal_coefficient(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    tmean_c: NDArray[np.float64] | Sequence[float],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
) -> HydrothermalCoefficient:
    """Sielianinov's hydrothermal coefficient of the months IV-IX and of the season.

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing (days may be absent).
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    accumulated : array_like of bool, optional
        Accumulated totals of precipitation: they stand for the missing days before
        them in the monthly sums and are missing days of the season.

    Returns
    -------
    HydrothermalCoefficient
        The coefficients of each calendar year and their means.

    Raises
    ------
    InvalidParameterError
        If an array is empty or of another length, the dates do not increase, a
        precipitation is negative or no day has a value.
    """
    days = as_days(dates)
    rain = np.asarray(precipitation_mm, dtype=np.float64)
    temperature = np.asarray(tmean_c, dtype=np.float64)
    check_daily(days, rain, temperature)
    flags = (
        np.zeros(rain.size, dtype=bool)
        if accumulated is None
        else np.asarray(accumulated, dtype=bool)
    )
    if flags.size != rain.size:
        raise InvalidParameterError("accumulated must have one flag per value")
    if bool((rain[np.isfinite(rain)] < 0).any()):
        raise InvalidParameterError("precipitation must not be negative")
    grid = grid_of_values(
        days, np.isfinite(rain) | np.isfinite(temperature), "calendar"
    )
    raw = grid.place(days, rain)
    totals = grid.place_flags(days, flags) & np.isfinite(raw)
    daily_rain = np.where(totals, np.nan, raw)
    daily_t = grid.place(days, temperature)
    month_rain = monthly_precipitation(grid, raw, totals)
    month_t = monthly_means(grid, daily_t)
    with np.errstate(invalid="ignore", divide="ignore"):
        monthly = np.where(
            month_t > 0, 10.0 * month_rain / (month_t * grid.days_in_month()), np.nan
        )
    both = np.isfinite(daily_rain) & np.isfinite(daily_t)
    complete = complete_years(grid, both)
    with np.errstate(invalid="ignore"):
        warm = both & (daily_t > SEASON_TEMPERATURE_C)
    starts = grid.year_starts()
    warm_rain = np.add.reduceat(np.where(warm, daily_rain, 0.0), starts)
    warm_t = np.add.reduceat(np.where(warm, daily_t, 0.0), starts)
    warm_days = np.add.reduceat(warm.astype(np.int64), starts)
    with np.errstate(invalid="ignore", divide="ignore"):
        season = np.where(complete & (warm_t > 0), 10.0 * warm_rain / warm_t, np.nan)
    present = years_with_values(grid, np.isfinite(raw) | np.isfinite(daily_t))
    slots = [grid.months.index(month) for month in HYDROTHERMAL_MONTHS]
    rows: list[HydrothermalYear] = []
    for row in np.flatnonzero(present).tolist():
        months = [
            HydrothermalMonth(
                month,
                finite(monthly[row, slot]),
                sielianinov_class(finite(monthly[row, slot])),
            )
            for month, slot in zip(HYDROTHERMAL_MONTHS, slots, strict=True)
        ]
        value = finite(season[row])
        rows.append(
            HydrothermalYear(
                year=grid.first_year + row,
                months=months,
                season_coefficient=value,
                season_class=sielianinov_class(value),
                season_days=int(warm_days[row]) if complete[row] else None,
            )
        )
    summaries: list[HydrothermalMonthSummary] = []
    for month, slot in zip(HYDROTHERMAL_MONTHS, slots, strict=True):
        column = monthly[present, slot]
        values = column[np.isfinite(column)]
        counts = dict.fromkeys(SIELIANINOV_CLASSES, 0)
        for value in values.tolist():
            name = sielianinov_class(value)
            if name is not None:
                counts[name] += 1
        summaries.append(
            HydrothermalMonthSummary(
                month=month,
                n_years=int(values.size),
                mean_coefficient=mean_of(values),
                class_counts=counts,
            )
        )
    seasons = season[present]
    mean_season = mean_of(seasons)
    return HydrothermalCoefficient(
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        years=rows,
        period=HydrothermalPeriod(
            n_years=int(np.isfinite(seasons).sum()),
            mean_season_coefficient=mean_season,
            mean_season_class=sielianinov_class(mean_season),
            months=summaries,
        ),
    )
