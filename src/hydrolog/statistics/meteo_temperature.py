"""Air temperature statistics of a daily series of a meteorological station.

Four indices of the daily mean, maximum and minimum air temperature (Tmean, Tmax, Tmin
[°C]) of a period of years, each a function of this module:

* :func:`temperature_means` -- monthly and annual means of Tmean, Tmax and Tmin, the
  normal of Tmean and the anomaly from it, and the absolute extremes with their dates;
* :func:`temperature_days` -- frost days (Tmin < 0 °C), ice days (Tmax < 0 °C), summer
  days (Tmax > 25 °C), hot days (Tmax > 30 °C) and tropical nights (Tmin > 20 °C): FD,
  ID, SU and TR of the ETCCDI (Zhang et al., 2011) and the hot day of Polish practice;
* :func:`degree_days` -- growing degree days above 5 °C, Σ max(Tmean - 5, 0), and
  heating degree days by Eurostat's rule, Σ (18 - Tmean) over the days with Tmean
  <= 15 °C (Eurostat, 2024);
* :func:`temperature_range` -- the mean daily range Tmax - Tmin, DTR of the ETCCDI.

Missing days follow WMO-No. 1203 (:mod:`hydrolog.statistics._climate`): a monthly mean
or count needs fewer than 11 missing days and fewer than 5 in a row (a count is scaled
to the days of the month), a monthly degree-day sum needs every day, a monthly extreme
takes whatever days there are; an annual value needs its twelve months.

The normals of :func:`temperature_means` come from a reference period
(``reference_first_year`` to ``reference_last_year``, by default the analysed years),
the means and the anomalies of each analysed year from its own days: normals are the
benchmark of anomalies (WMO-No. 1203, chapter 2), the climatological standard normal
1991-2020 for monitoring and the reference normal 1961-1990 for climate change
(chapters 2 and 3, section 5.1), and need values in 80 % of the years of the
reference period (4.4.2).

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203.
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Eurostat (2024): Energy statistics - cooling and heating degree days (nrg_chdd),
    reference metadata, section 3.4: HDD = Σ (18 °C - Tm) when Tm <= 15 °C.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._climate import (
    DailyGrid,
    as_days,
    block_extreme,
    check_daily,
    check_year_type,
    finite,
    grid_of_values,
    mean_of,
    monthly_counts,
    monthly_means,
    monthly_totals,
    normal,
    period_days,
    reference_period,
    years_with_values,
)

__all__ = [
    "DegreeDays",
    "DegreeDaysMonth",
    "DegreeDaysPeriod",
    "DegreeDaysYear",
    "TemperatureDays",
    "TemperatureDaysMonth",
    "TemperatureDaysPeriod",
    "TemperatureDaysYear",
    "TemperatureMeans",
    "TemperatureMeansMonth",
    "TemperatureMeansPeriod",
    "TemperatureMeansYear",
    "TemperatureMonthSummary",
    "TemperatureRange",
    "TemperatureRangeMonth",
    "TemperatureRangePeriod",
    "TemperatureRangeYear",
    "degree_days",
    "temperature_days",
    "temperature_means",
    "temperature_range",
    "TEMPERATURE_INDICES",
]

TEMPERATURE_INDICES: tuple[str, ...] = ("means", "days", "degree_days", "range")
"""The indices of ``meteo temperature``, one function of this module each."""


class _Series(NamedTuple):
    """The temperature series laid on the whole years of their values."""

    grid: DailyGrid
    tmean: NDArray[np.float64] | None
    tmax: NDArray[np.float64] | None
    tmin: NDArray[np.float64] | None
    present: NDArray[np.bool_]


class _Record(NamedTuple):
    """The checked temperature series, before they are laid on years."""

    days: NDArray[np.datetime64]
    series: dict[str, NDArray[np.float64]]  # the given series by argument name
    known: NDArray[np.bool_]  # a day with a value of any series
    year_type: str

    def on_grid(self, keep: NDArray[np.bool_] | None = None) -> _Series:
        """Lay the days of ``keep`` (every day by default) on the years of values."""
        days, series, known = self.days, self.series, self.known
        if keep is not None:
            days, known = days[keep], known[keep]
            series = {name: values[keep] for name, values in series.items()}
        grid = grid_of_values(days, known, self.year_type)
        placed = {name: grid.place(days, values) for name, values in series.items()}
        return _Series(
            grid,
            placed.get("tmean_c"),
            placed.get("tmax_c"),
            placed.get("tmin_c"),
            years_with_values(grid, grid.place_flags(days, known)),
        )


def _record(
    dates: NDArray[np.datetime64] | Sequence[object],
    year_type: str,
    **series: NDArray[np.float64] | Sequence[float] | None,
) -> _Record:
    check_year_type(year_type)
    days = as_days(dates)
    given = {
        name: np.asarray(values, dtype=np.float64)
        for name, values in series.items()
        if values is not None
    }
    if not given:
        raise InvalidParameterError("give at least one temperature series")
    check_daily(days, *given.values())
    known = np.zeros(days.size, dtype=bool)
    for values in given.values():
        known |= np.isfinite(values)
    return _Record(days, given, known, year_type)


def _series(
    dates: NDArray[np.datetime64] | Sequence[object],
    year_type: str,
    **series: NDArray[np.float64] | Sequence[float] | None,
) -> _Series:
    return _record(dates, year_type, **series).on_grid()


def _require(values: NDArray[np.float64] | None, name: str) -> NDArray[np.float64]:
    if values is None:
        raise InvalidParameterError(f"{name} is required")
    return values


def _annual_mean(table: NDArray[np.float64]) -> NDArray[np.float64]:
    """Average the twelve monthly values of each year; ``NaN`` without all."""
    means: NDArray[np.float64] = np.where(
        np.isfinite(table).all(axis=1), table.mean(axis=1), np.nan
    )
    return means


def _first_extreme(
    values: NDArray[np.float64], positions: NDArray[np.int64], largest: bool
) -> tuple[float | None, int]:
    """Return the first largest (smallest) finite value and its position or -1."""
    if not np.isfinite(values).any():
        return None, -1
    at = int(np.nanargmax(values) if largest else np.nanargmin(values))
    return float(values[at]), int(positions[at])


# --- means, normal, anomaly and extremes ----------------------------------------------


@dataclass
class TemperatureMeansMonth(JsonResultMixin):
    """One month of a year.

    Attributes
    ----------
    month : int
        Calendar month.
    tmean_c, tmax_c, tmin_c : float or None
        Monthly means of Tmean, Tmax and Tmin [°C] (WMO-No. 1203, 4.4.1 a).
    anomaly_c : float or None
        ``tmean_c`` minus the normal of the month (of the reference period) [°C].
    max_c, min_c : float or None
        The highest Tmax and the lowest Tmin of the month [°C] (any days).
    max_date, min_date : str or None
        Their (first) days.
    """

    month: int
    tmean_c: float | None
    anomaly_c: float | None
    tmax_c: float | None
    tmin_c: float | None
    max_c: float | None
    max_date: str | None
    min_c: float | None
    min_date: str | None


@dataclass
class TemperatureMeansYear(JsonResultMixin):
    """One analysed year.

    Attributes
    ----------
    year : int
        The year.
    tmean_c, tmax_c, tmin_c : float or None
        Annual means: the mean of the twelve monthly means [°C].
    anomaly_c : float or None
        ``tmean_c`` minus the annual normal (of the reference period) [°C].
    max_c, min_c : float or None
        The highest Tmax and the lowest Tmin of the year [°C].
    max_date, min_date : str or None
        Their (first) days.
    months : list of TemperatureMeansMonth
        The twelve months in the order of the year.
    """

    year: int
    tmean_c: float | None
    anomaly_c: float | None
    tmax_c: float | None
    tmin_c: float | None
    max_c: float | None
    max_date: str | None
    min_c: float | None
    min_date: str | None
    months: list[TemperatureMeansMonth]


@dataclass
class TemperatureMonthSummary(JsonResultMixin):
    """One calendar month: its normal and its means over the analysed years.

    Attributes
    ----------
    month : int
        Calendar month.
    normal_c : float or None
        Normal of Tmean of the reference period (at least 80 % of its years,
        WMO-No. 1203, 4.4.2) [°C].
    n_years : int
        Analysed years with a monthly mean of Tmean.
    tmean_c, tmax_c, tmin_c : float or None
        Means of the monthly means of the analysed years [°C].
    max_c, min_c : float or None
        The highest Tmax and the lowest Tmin of the month in the period [°C].
    max_date, min_date : str or None
        Their (first) days.
    """

    month: int
    normal_c: float | None
    n_years: int
    tmean_c: float | None
    tmax_c: float | None
    tmin_c: float | None
    max_c: float | None
    max_date: str | None
    min_c: float | None
    min_date: str | None


@dataclass
class TemperatureMeansPeriod(JsonResultMixin):
    """The normal of the reference period, the means and records of the analysed years.

    Attributes
    ----------
    normal_c : float or None
        Annual normal of Tmean of the reference period [°C].
    normal_years : int
        Years of the reference period with an annual mean of Tmean.
    tmean_c, tmax_c, tmin_c : float or None
        Means of the annual means of the analysed years [°C].
    max_c, min_c : float or None
        The highest Tmax and the lowest Tmin of the period [°C].
    max_date, min_date : str or None
        Their (first) days.
    months : list of TemperatureMonthSummary
        The twelve months in the order of the year.
    """

    normal_c: float | None
    normal_years: int
    tmean_c: float | None
    tmax_c: float | None
    tmin_c: float | None
    max_c: float | None
    max_date: str | None
    min_c: float | None
    min_date: str | None
    months: list[TemperatureMonthSummary]


@dataclass
class TemperatureMeans(JsonResultMixin):
    """Monthly and annual means, the normal, the anomaly and the extremes.

    Attributes
    ----------
    index : str
        ``"means"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The analysed years: first and last year with a value, years with a value.
    reference_first_year, reference_last_year : int
        The reference period of the normals, as given or by default the analysed
        years.
    reference_period_years : int
        Its years with a value.
    years : list of TemperatureMeansYear
        Every analysed year with a value.
    period : TemperatureMeansPeriod
        The normal, the means and the records.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    reference_first_year: int
    reference_last_year: int
    reference_period_years: int
    years: list[TemperatureMeansYear]
    period: TemperatureMeansPeriod


def temperature_means(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    tmean_c: NDArray[np.float64] | Sequence[float],
    tmax_c: NDArray[np.float64] | Sequence[float] | None = None,
    tmin_c: NDArray[np.float64] | Sequence[float] | None = None,
    year_type: str = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> TemperatureMeans:
    """Monthly and annual means, the normal and anomaly of Tmean, and the extremes.

    The means of each analysed year come from its own days, the normals of Tmean
    from the reference period: the mean of its years with a value when they are at
    least 80 % of its years, those without data too (WMO-No. 1203, 4.4.2).

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing (days may be absent).
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    tmax_c, tmin_c : array_like of float, optional
        Daily maximum and minimum temperature [°C]: their means and the extremes.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.
    first_year, last_year : int, optional
        The analysed years (of ``year_type``), by default those of the record.
    reference_first_year, reference_last_year : int, optional
        The reference period of the normals, each by default that of the analysed
        years as resolved; each period keeps the days of its own years only.

    Returns
    -------
    TemperatureMeans
        The means of each month and year, the anomalies and the normals.

    Raises
    ------
    InvalidParameterError
        If an array is empty or of another length, the dates do not increase, no day
        has a value, ``year_type`` is unknown or a period starts after its last year
        (``details.reason`` ``range``).
    CalculationError
        If a period has no value (``details.reason`` ``no_values_in_period``).
    """
    record = _record(dates, year_type, tmean_c=tmean_c, tmax_c=tmax_c, tmin_c=tmin_c)
    data = record.on_grid(
        period_days(record.days, record.known, year_type, first_year, last_year)
    )
    reference = reference_period(
        record.days,
        record.known,
        year_type,
        data.grid,
        reference_first_year,
        reference_last_year,
    )
    base = data if reference.is_period_of(data.grid) else record.on_grid(reference.keep)
    grid = data.grid
    tmean = _require(data.tmean, "tmean_c")
    shape = (grid.n_years, 12)
    empty = np.full(shape, np.nan)
    no_position = np.full(shape, -1, dtype=np.int64)
    means = {
        name: monthly_means(grid, values) if values is not None else empty
        for name, values in (("tmean", tmean), ("tmax", data.tmax), ("tmin", data.tmin))
    }
    annual = {name: _annual_mean(table) for name, table in means.items()}
    base_means = (
        means["tmean"]
        if base is data
        else monthly_means(base.grid, _require(base.tmean, "tmean_c"))
    )
    base_annual = annual["tmean"] if base is data else _annual_mean(base_means)
    normal_c, normal_years = normal(base_annual, reference.n_years)
    month_normals = [
        normal(base_means[:, slot], reference.n_years)[0] for slot in range(12)
    ]
    starts = grid.month_starts()
    if data.tmax is not None:
        high, high_at = block_extreme(data.tmax, starts, largest=True)
        high, high_at = high.reshape(shape), high_at.reshape(shape)
    else:
        high, high_at = empty, no_position
    if data.tmin is not None:
        low, low_at = block_extreme(data.tmin, starts, largest=False)
        low, low_at = low.reshape(shape), low_at.reshape(shape)
    else:
        low, low_at = empty, no_position
    months = grid.months

    def anomaly(value: float, reference: float | None) -> float | None:
        return (
            value - reference
            if reference is not None and math.isfinite(value)
            else None
        )

    rows: list[TemperatureMeansYear] = []
    for row in np.flatnonzero(data.present).tolist():
        top, top_at = _first_extreme(high[row], high_at[row], True)
        bottom, bottom_at = _first_extreme(low[row], low_at[row], False)
        rows.append(
            TemperatureMeansYear(
                year=grid.first_year + row,
                tmean_c=finite(annual["tmean"][row]),
                anomaly_c=anomaly(annual["tmean"][row], normal_c),
                tmax_c=finite(annual["tmax"][row]),
                tmin_c=finite(annual["tmin"][row]),
                max_c=top,
                max_date=grid.iso(top_at),
                min_c=bottom,
                min_date=grid.iso(bottom_at),
                months=[
                    TemperatureMeansMonth(
                        month=month,
                        tmean_c=finite(means["tmean"][row, slot]),
                        anomaly_c=anomaly(
                            means["tmean"][row, slot], month_normals[slot]
                        ),
                        tmax_c=finite(means["tmax"][row, slot]),
                        tmin_c=finite(means["tmin"][row, slot]),
                        max_c=finite(high[row, slot]),
                        max_date=grid.iso(int(high_at[row, slot])),
                        min_c=finite(low[row, slot]),
                        min_date=grid.iso(int(low_at[row, slot])),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    summaries: list[TemperatureMonthSummary] = []
    for slot, month in enumerate(months):
        top, top_at = _first_extreme(high[:, slot], high_at[:, slot], True)
        bottom, bottom_at = _first_extreme(low[:, slot], low_at[:, slot], False)
        summaries.append(
            TemperatureMonthSummary(
                month=month,
                normal_c=month_normals[slot],
                n_years=int(np.isfinite(means["tmean"][:, slot]).sum()),
                tmean_c=mean_of(means["tmean"][:, slot]),
                tmax_c=mean_of(means["tmax"][:, slot]),
                tmin_c=mean_of(means["tmin"][:, slot]),
                max_c=top,
                max_date=grid.iso(top_at),
                min_c=bottom,
                min_date=grid.iso(bottom_at),
            )
        )
    record_high, record_high_at = _first_extreme(
        high.reshape(-1), high_at.reshape(-1), True
    )
    record_low, record_low_at = _first_extreme(
        low.reshape(-1), low_at.reshape(-1), False
    )
    return TemperatureMeans(
        index="means",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        reference_first_year=reference.first_year,
        reference_last_year=reference.last_year,
        reference_period_years=int(base.present.sum()),
        years=rows,
        period=TemperatureMeansPeriod(
            normal_c=normal_c,
            normal_years=normal_years,
            tmean_c=mean_of(annual["tmean"]),
            tmax_c=mean_of(annual["tmax"]),
            tmin_c=mean_of(annual["tmin"]),
            max_c=record_high,
            max_date=grid.iso(record_high_at),
            min_c=record_low,
            min_date=grid.iso(record_low_at),
            months=summaries,
        ),
    )


# --- characteristic days --------------------------------------------------------------


@dataclass
class TemperatureDaysMonth(JsonResultMixin):
    """The characteristic days of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    frost_days, ice_days, summer_days, hot_days, tropical_nights : float or None
        Days with Tmin < ``frost_tmin_c``, Tmax < ``ice_tmax_c``, Tmax >
        ``summer_tmax_c``, Tmax > ``hot_tmax_c`` and Tmin > ``tropical_tmin_c``,
        scaled to the days of the month when some are missing (WMO-No. 1203,
        4.4.1 d); ``None`` without enough days or without the series. In
        ``period.months`` the means over the years.
    """

    month: int
    frost_days: float | None
    ice_days: float | None
    summer_days: float | None
    hot_days: float | None
    tropical_nights: float | None


@dataclass
class TemperatureDaysYear(JsonResultMixin):
    """The characteristic days of one year.

    Attributes
    ----------
    year : int
        The year.
    frost_days, ice_days, summer_days, hot_days, tropical_nights : float or None
        The sums of the twelve monthly counts (FD, ID, SU, TR of the ETCCDI and the
        hot days); ``None`` without all of them.
    months : list of TemperatureDaysMonth
        The twelve months in the order of the year.
    """

    year: int
    frost_days: float | None
    ice_days: float | None
    summer_days: float | None
    hot_days: float | None
    tropical_nights: float | None
    months: list[TemperatureDaysMonth]


@dataclass
class TemperatureDaysPeriod(JsonResultMixin):
    """Mean characteristic days of the period.

    Attributes
    ----------
    frost_days, ice_days, summer_days, hot_days, tropical_nights : float or None
        Mean annual counts of the years with one.
    months : list of TemperatureDaysMonth
        Mean monthly counts, in the order of the year.
    """

    frost_days: float | None
    ice_days: float | None
    summer_days: float | None
    hot_days: float | None
    tropical_nights: float | None
    months: list[TemperatureDaysMonth]


@dataclass
class TemperatureDays(JsonResultMixin):
    """Frost, ice, summer and hot days and tropical nights.

    Attributes
    ----------
    index : str
        ``"days"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    frost_tmin_c, ice_tmax_c, summer_tmax_c, hot_tmax_c, tropical_tmin_c : float
        The thresholds [°C].
    years : list of TemperatureDaysYear
        Every year with a value.
    period : TemperatureDaysPeriod
        The mean counts.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    frost_tmin_c: float
    ice_tmax_c: float
    summer_tmax_c: float
    hot_tmax_c: float
    tropical_tmin_c: float
    years: list[TemperatureDaysYear]
    period: TemperatureDaysPeriod


_DAY_KINDS = ("frost_days", "ice_days", "summer_days", "hot_days", "tropical_nights")


def _finite_threshold(name: str, value: float) -> float:
    if not math.isfinite(value):
        raise InvalidParameterError(f"{name} must be a finite number, got {value!r}")
    return float(value)


def temperature_days(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    tmax_c: NDArray[np.float64] | Sequence[float] | None = None,
    tmin_c: NDArray[np.float64] | Sequence[float] | None = None,
    frost_tmin_c: float = 0.0,
    ice_tmax_c: float = 0.0,
    summer_tmax_c: float = 25.0,
    hot_tmax_c: float = 30.0,
    tropical_tmin_c: float = 20.0,
    year_type: str = "calendar",
) -> TemperatureDays:
    """Count the frost, ice, summer and hot days and the tropical nights.

    A frost day has Tmin < 0 °C (FD of the ETCCDI), an ice day Tmax < 0 °C (ID), a
    summer day Tmax > 25 °C (SU), a hot day Tmax > 30 °C and a tropical night Tmin >
    20 °C (TR), with the thresholds as defaults (Zhang et al., 2011).

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing.
    tmax_c, tmin_c : array_like of float, optional
        Daily maximum and minimum temperature [°C]; at least one is needed.
    frost_tmin_c, ice_tmax_c, summer_tmax_c, hot_tmax_c, tropical_tmin_c : float
        The thresholds [°C], by default 0, 0, 25, 30 and 20.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    TemperatureDays
        The counts of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If neither series is given, the arrays are invalid, a threshold is not finite
        or ``year_type`` is unknown.
    """
    limits = {
        name: _finite_threshold(name, value)
        for name, value in (
            ("frost_tmin_c", frost_tmin_c),
            ("ice_tmax_c", ice_tmax_c),
            ("summer_tmax_c", summer_tmax_c),
            ("hot_tmax_c", hot_tmax_c),
            ("tropical_tmin_c", tropical_tmin_c),
        )
    }
    data = _series(dates, year_type, tmax_c=tmax_c, tmin_c=tmin_c)
    grid = data.grid
    empty = np.full((grid.n_years, 12), np.nan)

    def count(
        values: NDArray[np.float64] | None, event: str, limit: float
    ) -> NDArray[np.float64]:
        if values is None:
            return empty
        with np.errstate(invalid="ignore"):
            hit = values < limit if event == "below" else values > limit
        return monthly_counts(grid, values, hit)

    tables = {
        "frost_days": count(data.tmin, "below", limits["frost_tmin_c"]),
        "ice_days": count(data.tmax, "below", limits["ice_tmax_c"]),
        "summer_days": count(data.tmax, "above", limits["summer_tmax_c"]),
        "hot_days": count(data.tmax, "above", limits["hot_tmax_c"]),
        "tropical_nights": count(data.tmin, "above", limits["tropical_tmin_c"]),
    }
    annual = {name: table.sum(axis=1) for name, table in tables.items()}
    months = grid.months

    def month_counts(month: int, values: list[float | None]) -> TemperatureDaysMonth:
        frost, ice, summer, hot, tropical = values
        return TemperatureDaysMonth(month, frost, ice, summer, hot, tropical)

    rows: list[TemperatureDaysYear] = []
    for row in np.flatnonzero(data.present).tolist():
        frost, ice, summer, hot, tropical = (
            finite(annual[name][row]) for name in _DAY_KINDS
        )
        rows.append(
            TemperatureDaysYear(
                grid.first_year + row,
                frost,
                ice,
                summer,
                hot,
                tropical,
                [
                    month_counts(
                        month, [finite(tables[name][row, slot]) for name in _DAY_KINDS]
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    frost, ice, summer, hot, tropical = (mean_of(annual[name]) for name in _DAY_KINDS)
    return TemperatureDays(
        index="days",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        **limits,
        years=rows,
        period=TemperatureDaysPeriod(
            frost,
            ice,
            summer,
            hot,
            tropical,
            [
                month_counts(
                    month, [mean_of(tables[name][:, slot]) for name in _DAY_KINDS]
                )
                for slot, month in enumerate(months)
            ],
        ),
    )


# --- degree days ----------------------------------------------------------------------


@dataclass
class DegreeDaysMonth(JsonResultMixin):
    """The degree days of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    growing_degree_days : float or None
        Σ max(Tmean - ``growing_base_c``, 0) [°C·d]; ``None`` when a day is missing.
    heating_degree_days : float or None
        Σ (``heating_base_c`` - Tmean) over the days with Tmean <= ``heating_limit_c``
        [°C·d]. In ``period.months`` the means over the years.
    """

    month: int
    growing_degree_days: float | None
    heating_degree_days: float | None


@dataclass
class DegreeDaysYear(JsonResultMixin):
    """The degree days of one year.

    Attributes
    ----------
    year : int
        The year.
    growing_degree_days, heating_degree_days : float or None
        The sums of the twelve months [°C·d]; ``None`` without all of them.
    months : list of DegreeDaysMonth
        The twelve months in the order of the year.
    """

    year: int
    growing_degree_days: float | None
    heating_degree_days: float | None
    months: list[DegreeDaysMonth]


@dataclass
class DegreeDaysPeriod(JsonResultMixin):
    """Mean degree days of the period.

    Attributes
    ----------
    n_years : int
        Years with annual sums.
    growing_degree_days, heating_degree_days : float or None
        Mean annual sums [°C·d].
    months : list of DegreeDaysMonth
        Mean monthly sums, in the order of the year.
    """

    n_years: int
    growing_degree_days: float | None
    heating_degree_days: float | None
    months: list[DegreeDaysMonth]


@dataclass
class DegreeDays(JsonResultMixin):
    """Growing and heating degree days.

    Attributes
    ----------
    index : str
        ``"degree_days"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    growing_base_c, heating_base_c, heating_limit_c : float
        The bases and the limit [°C].
    years : list of DegreeDaysYear
        Every year with a value.
    period : DegreeDaysPeriod
        The means.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    growing_base_c: float
    heating_base_c: float
    heating_limit_c: float
    years: list[DegreeDaysYear]
    period: DegreeDaysPeriod


def degree_days(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    tmean_c: NDArray[np.float64] | Sequence[float],
    growing_base_c: float = 5.0,
    heating_base_c: float = 18.0,
    heating_limit_c: float = 15.0,
    year_type: str = "calendar",
) -> DegreeDays:
    """Growing degree days and heating degree days by Eurostat's rule.

    GDD = Σ max(Tmean - 5, 0); HDD = Σ (18 - Tmean) over the days with Tmean <= 15 °C
    (Eurostat), with the bases and the limit as defaults.

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing.
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    growing_base_c : float, optional
        Base of the growing degree days [°C], by default 5.
    heating_base_c : float, optional
        Base of the heating degree days [°C], by default 18.
    heating_limit_c : float, optional
        A day counts in the heating degree days when Tmean <= this [°C], by default
        15.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    DegreeDays
        The degree days of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, a base is not finite or ``year_type`` is unknown.
    """
    bases = {
        name: _finite_threshold(name, value)
        for name, value in (
            ("growing_base_c", growing_base_c),
            ("heating_base_c", heating_base_c),
            ("heating_limit_c", heating_limit_c),
        )
    }
    data = _series(dates, year_type, tmean_c=tmean_c)
    grid = data.grid
    tmean = _require(data.tmean, "tmean_c")
    known = np.isfinite(tmean)
    with np.errstate(invalid="ignore"):
        growing = np.where(
            known, np.maximum(tmean - bases["growing_base_c"], 0.0), np.nan
        )
        heating = np.where(
            known,
            np.where(
                tmean <= bases["heating_limit_c"], bases["heating_base_c"] - tmean, 0.0
            ),
            np.nan,
        )
    tables = {
        "growing": monthly_totals(grid, growing),
        "heating": monthly_totals(grid, heating),
    }
    annual = {name: table.sum(axis=1) for name, table in tables.items()}
    months = grid.months
    rows = [
        DegreeDaysYear(
            grid.first_year + row,
            finite(annual["growing"][row]),
            finite(annual["heating"][row]),
            [
                DegreeDaysMonth(
                    month,
                    finite(tables["growing"][row, slot]),
                    finite(tables["heating"][row, slot]),
                )
                for slot, month in enumerate(months)
            ],
        )
        for row in np.flatnonzero(data.present).tolist()
    ]
    return DegreeDays(
        index="degree_days",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        **bases,
        years=rows,
        period=DegreeDaysPeriod(
            n_years=int(np.isfinite(annual["growing"]).sum()),
            growing_degree_days=mean_of(annual["growing"]),
            heating_degree_days=mean_of(annual["heating"]),
            months=[
                DegreeDaysMonth(
                    month,
                    mean_of(tables["growing"][:, slot]),
                    mean_of(tables["heating"][:, slot]),
                )
                for slot, month in enumerate(months)
            ],
        ),
    )


# --- daily range ----------------------------------------------------------------------


@dataclass
class TemperatureRangeMonth(JsonResultMixin):
    """The mean daily range of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    dtr_c : float or None
        Mean of Tmax - Tmin over the days with both (WMO-No. 1203, 4.4.1 a) [°C]; in
        ``period.months`` the mean over the years.
    """

    month: int
    dtr_c: float | None


@dataclass
class TemperatureRangeYear(JsonResultMixin):
    """The mean daily range of one year.

    Attributes
    ----------
    year : int
        The year.
    dtr_c : float or None
        The mean of the twelve monthly ranges (DTR of the ETCCDI) [°C].
    months : list of TemperatureRangeMonth
        The twelve months in the order of the year.
    """

    year: int
    dtr_c: float | None
    months: list[TemperatureRangeMonth]


@dataclass
class TemperatureRangePeriod(JsonResultMixin):
    """The mean daily range of the period.

    Attributes
    ----------
    n_years : int
        Years with an annual range.
    dtr_c : float or None
        Mean of the annual ranges [°C].
    months : list of TemperatureRangeMonth
        Mean monthly ranges, in the order of the year.
    """

    n_years: int
    dtr_c: float | None
    months: list[TemperatureRangeMonth]


@dataclass
class TemperatureRange(JsonResultMixin):
    """The mean daily temperature range.

    Attributes
    ----------
    index : str
        ``"range"``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period.
    years : list of TemperatureRangeYear
        Every year with a value.
    period : TemperatureRangePeriod
        The means.
    """

    index: str
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    years: list[TemperatureRangeYear]
    period: TemperatureRangePeriod


def temperature_range(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    tmax_c: NDArray[np.float64] | Sequence[float],
    tmin_c: NDArray[np.float64] | Sequence[float],
    year_type: str = "calendar",
) -> TemperatureRange:
    """Compute the mean daily temperature range Tmax - Tmin (DTR of the ETCCDI).

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing.
    tmax_c, tmin_c : array_like of float
        Daily maximum and minimum temperature [°C]; ``NaN`` on a missing day.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    TemperatureRange
        The mean range of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid or ``year_type`` is unknown.
    """
    data = _series(dates, year_type, tmax_c=tmax_c, tmin_c=tmin_c)
    grid = data.grid
    daily = _require(data.tmax, "tmax_c") - _require(data.tmin, "tmin_c")
    table = monthly_means(grid, daily)
    annual = _annual_mean(table)
    months = grid.months
    rows = [
        TemperatureRangeYear(
            grid.first_year + row,
            finite(annual[row]),
            [
                TemperatureRangeMonth(month, finite(table[row, slot]))
                for slot, month in enumerate(months)
            ],
        )
        for row in np.flatnonzero(data.present).tolist()
    ]
    return TemperatureRange(
        index="range",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        years=rows,
        period=TemperatureRangePeriod(
            n_years=int(np.isfinite(annual).sum()),
            dtr_c=mean_of(annual),
            months=[
                TemperatureRangeMonth(month, mean_of(table[:, slot]))
                for slot, month in enumerate(months)
            ],
        ),
    )
