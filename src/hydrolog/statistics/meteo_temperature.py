"""Air temperature statistics of a daily series of a meteorological station.

Four indices of the daily mean, maximum and minimum air temperature (Tmean, Tmax, Tmin
[°C]) of a period of years, each a function of this module:

* :func:`temperature_means` -- monthly and annual means of Tmean, Tmax and Tmin, the
  normal of Tmean and the anomaly from it, and the absolute extremes with their dates;
* :func:`temperature_days` -- frost days (Tmin < 0 °C), ice days (Tmax < 0 °C), summer
  days (Tmax > 25 °C), hot days (Tmax > 30 °C) and tropical nights (Tmin > 20 °C): FD,
  ID, SU and TR of the ETCCDI (Zhang et al., 2011) and the hot day of Polish practice;
  and the freeze-thaw days (Tmin < 0 °C and Tmax > 0 °C), the Polish "dni
  przymrozkowe" of the Słownik meteorologiczny and of IMGW-PIB's normals;
* :func:`degree_days` -- growing degree days above 5 °C, Σ max(Tmean - 5, 0)
  (Wypych et al., 2017, eq. 1), and heating degree days by Eurostat's rule, Σ (18 -
  Tm) over the days with Tm <= 15 °C (Eurostat, 2024; Commission Directive (EU)
  2015/1127), both summed over every day of the year (no growing or heating season is
  cut out); Tm is the daily mean given, Tmean, where the Directive takes (Tmin +
  Tmax) / 2;
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
reference period (4.4.2); the annual normal is the mean of the twelve monthly normals
(4.3.3).

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203.
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Eurostat (2024): Energy statistics - cooling and heating degree days (nrg_chdd),
    reference metadata, section 3.4: HDD = Σ (18 °C - Tm) when Tm <= 15 °C.
Commission Directive (EU) 2015/1127 of 10 July 2015, Annex (as corrected, OJ L 297,
    13.11.2015, p. 9): Tm = (Tmin + Tmax) / 2, computed daily and summed to the year.
Dopke, J. (2010): Obliczanie liczby stopniodni grzania według metody Eurostat
    (cire.pl), eq. 2: „temperatura bazowa” 18 °C, „temperatura graniczna” 15 °C.
Wypych, A., Sulikowska, A., Ustrnul, Z. & Czekierda, D. (2017): Variability of
    growing degree days in Poland in response to ongoing climate changes in Europe.
    International Journal of Biometeorology 61, 49-59 (eq. 1; bases 0, 5, 10 °C).
Kossowska-Cezak, U. (2014): Zmiany wieloletnie liczby termicznych dni
    charakterystycznych w Warszawie (1951-2010). Prace Geograficzne 136, 9-30 (p. 14:
    the Słownik meteorologiczny, 2003, "dzień przymrozkowy", Tmin < 0 °C and Tmax >
    0 °C; the Atlas klimatu Polski, 2005, Tmin < 0 °C).
IMGW-PIB: Normy klimatyczne 1991-2020 (klimat.imgw.pl), product PRZYMROZKI, "Liczba
    dni przymrozkowych (TMAX>0 & TMIN<0)".

The formulas of a day are declared by specs (Nogat's computation standard, ADR-0050
and ADR-0059): :data:`THRESHOLD_DAYS` (``threshold_days``, the characteristic days)
and :data:`DEGREE_DAYS` (``degree_days``); the monthly and annual means, normals,
anomalies, extremes, counts, sums and the daily range around them are the module's
:data:`TIER_B`, and ``docs/FORMULAS.md`` shows both.

Examples
--------
>>> found = threshold_days([25.0, 25.1, -0.1], [-0.1, 20.1, -3.0], 0.0, 0.0, 25.0,
...                        30.0, 20.0)
>>> found.summer, found.freeze_thaw
(array([0., 1., 0.]), array([1., 0., 0.]))
>>> daily_degree_days([12.0, 16.0], 5.0, 18.0, 15.0).heating_degree_days
array([6., 0.])
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Conservation,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Source,
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
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
    monthly_normals,
    monthly_totals,
    multimonth_normal,
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
    "DEGREE_DAYS",
    "DailyDegreeDays",
    "SPECS",
    "THRESHOLD_DAYS",
    "TIER_B",
    "ThresholdDays",
    "daily_degree_days",
    "threshold_days",
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
        Annual normal of Tmean of the reference period: the mean of the twelve
        monthly normals, ``None`` when one is missing (WMO-No. 1203, 4.3.3) [°C].
    normal_years : int
        The fewest years of the reference period with a monthly mean of Tmean among
        the twelve months; every monthly normal needs 80 % of its years (4.4.2).
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
    from the reference period: the normal of a month is the mean of its years with a
    value when they are at least 80 % of its years, those without data too (WMO-No.
    1203, 4.4.2), the annual normal the mean of the twelve monthly normals (4.3.3).

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
    month_normals, normal_years = monthly_normals(base_means, reference.n_years)
    normal_c = multimonth_normal(month_normals, mean=True)
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
    freeze_thaw_days : float or None
        Days with Tmin < ``frost_tmin_c`` and Tmax > ``ice_tmax_c`` (both on the
        day), scaled likewise; ``None`` without both series.
    """

    month: int
    frost_days: float | None
    freeze_thaw_days: float | None
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
    frost_days, freeze_thaw_days, ice_days, summer_days, hot_days, tropical_nights :
        float or None
        The sums of the twelve monthly counts (FD, ID, SU, TR of the ETCCDI, the
        freeze-thaw days and the hot days); ``None`` without all of them.
    months : list of TemperatureDaysMonth
        The twelve months in the order of the year.
    """

    year: int
    frost_days: float | None
    freeze_thaw_days: float | None
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
    frost_days, freeze_thaw_days, ice_days, summer_days, hot_days, tropical_nights :
        float or None
        Mean annual counts of the years with one.
    months : list of TemperatureDaysMonth
        Mean monthly counts, in the order of the year.
    """

    frost_days: float | None
    freeze_thaw_days: float | None
    ice_days: float | None
    summer_days: float | None
    hot_days: float | None
    tropical_nights: float | None
    months: list[TemperatureDaysMonth]


@dataclass
class TemperatureDays(JsonResultMixin):
    """Frost, freeze-thaw, ice, summer and hot days and tropical nights.

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


_DAY_KINDS = (
    "frost_days",
    "freeze_thaw_days",
    "ice_days",
    "summer_days",
    "hot_days",
    "tropical_nights",
)


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
    """Count the frost, freeze-thaw, ice, summer and hot days and the tropical nights.

    A frost day has Tmin < 0 °C (FD of the ETCCDI), an ice day Tmax < 0 °C (ID), a
    summer day Tmax > 25 °C (SU), a hot day Tmax > 30 °C and a tropical night Tmin >
    20 °C (TR), with the thresholds as defaults (Zhang et al., 2011). A freeze-thaw
    day has Tmin below ``frost_tmin_c`` and Tmax above ``ice_tmax_c``, by default
    Tmin < 0 °C and Tmax > 0 °C: the "dzień przymrozkowy" of the Słownik
    meteorologiczny (2003, after Kossowska-Cezak, 2014, p. 14), of IMGW-PIB's normals
    1991-2020 (PRZYMROZKI) and of IMGW-PIB Agrometeo. Polish usage is not uniform: the
    Atlas klimatu Polski (2005) and KLIMADA 2.0 call FD "dni przymrozkowe", so FD is
    named here the days with frost ("dni z przymrozkiem", Tmin < 0 °C), of which the
    freeze-thaw days are those that also thaw. Note the strict signs: IMGW-PIB's
    yearbooks count Tmin <= 0 and Tmax >= 25 or 30 °C.

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
    data = _series(dates, year_type, tmax_c=tmax_c, tmin_c=tmin_c)
    grid = data.grid
    known = data.tmax if data.tmax is not None else _require(data.tmin, "tmin_c")
    missing = np.full(known.size, np.nan)
    days = threshold_days(
        data.tmax if data.tmax is not None else missing,
        data.tmin if data.tmin is not None else missing,
        frost_tmin_c,
        ice_tmax_c,
        summer_tmax_c,
        hot_tmax_c,
        tropical_tmin_c,
    )
    limits = {
        "frost_tmin_c": float(frost_tmin_c),
        "ice_tmax_c": float(ice_tmax_c),
        "summer_tmax_c": float(summer_tmax_c),
        "hot_tmax_c": float(hot_tmax_c),
        "tropical_tmin_c": float(tropical_tmin_c),
    }
    tables = {
        name: monthly_counts(grid, flags, flags == 1.0)
        for name, flags in zip(_DAY_KINDS, days, strict=True)
    }
    annual = {name: table.sum(axis=1) for name, table in tables.items()}
    months = grid.months

    def counts(values: list[float | None]) -> dict[str, float | None]:
        return dict(zip(_DAY_KINDS, values, strict=True))

    rows: list[TemperatureDaysYear] = []
    for row in np.flatnonzero(data.present).tolist():
        rows.append(
            TemperatureDaysYear(
                year=grid.first_year + row,
                **counts([finite(annual[name][row]) for name in _DAY_KINDS]),
                months=[
                    TemperatureDaysMonth(
                        month=month,
                        **counts(
                            [finite(tables[name][row, slot]) for name in _DAY_KINDS]
                        ),
                    )
                    for slot, month in enumerate(months)
                ],
            )
        )
    return TemperatureDays(
        index="days",
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(data.present.sum()),
        **limits,
        years=rows,
        period=TemperatureDaysPeriod(
            **counts([mean_of(annual[name]) for name in _DAY_KINDS]),
            months=[
                TemperatureDaysMonth(
                    month=month,
                    **counts([mean_of(tables[name][:, slot]) for name in _DAY_KINDS]),
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
        The base of the growing degree days, the reference temperature and the
        heating threshold of the heating degree days [°C].
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


_EUROSTAT = Source(
    citation="Eurostat (2024). Energy statistics - cooling and heating degree days "
    "(nrg_chdd), reference metadata, updated 25 October 2024",
    locator="section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C "
    "gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex)",
    url="https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm",
)
_WYPYCH = Source(
    citation="Wypych, A., Sulikowska, A., Ustrnul, Z. and Czekierda, D. (2017). "
    "Variability of growing degree days in Poland in response to ongoing climate "
    "changes in Europe. International Journal of Biometeorology 61, 49-59",
    locator="eq. 1, p. 50: GDD = sum of (T - Tbase) over the days with T > Tbase; "
    "the bases 0, 5 and 10 °C",
)
_WARSZAWA_T = Source(
    citation="Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: "
    "the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020",
    locator="the daily mean temperature: -22.2 to 29.3 °C",
)
_RECORD_HEAT = (
    "the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 "
    "(WMO Archive of Weather and Climate Extremes)"
)


def _air(name: str, symbol: str, description: str, typical: Range) -> Variable:
    return Variable(
        name=name,
        symbol=symbol,
        unit="°C",
        description=description,
        physical=Range(low=-273.15, test_high=56.7, test_reason=_RECORD_HEAT),
        applicability="unstated",
        typical=typical,
    )


class DailyDegreeDays(NamedTuple):
    """The degree days of each day (spec ``degree_days``).

    Attributes
    ----------
    growing_degree_days, heating_degree_days : numpy.ndarray
        GDD and HDD of each day [°C·d]; ``NaN`` where Tmean is.
    """

    growing_degree_days: NDArray[np.float64]
    heating_degree_days: NDArray[np.float64]


def _degree_days(x: Values) -> dict[str, NDArray[np.float64]]:
    tmean = x.array("tmean_c")
    known = ~np.isnan(tmean)
    with np.errstate(invalid="ignore"):
        growing = np.where(
            known, np.maximum(tmean - x.real("growing_base_c"), 0.0), np.nan
        )
        heating = np.where(
            known,
            np.where(
                tmean <= x.real("heating_limit_c"),
                x.real("heating_base_c") - tmean,
                0.0,
            ),
            np.nan,
        )
    return {"growing_degree_days": growing, "heating_degree_days": heating}


def _shifted(x: Values) -> dict[str, object]:
    """Shift the temperature and the three thresholds by 1 °C where that is exact.

    Adding 1 °C rounds away the digits of a value below its last place (3e-165 °C
    becomes 1 °C) and can move it onto a threshold, so such inputs stay as they
    are (the counterexample of the Hypothesis profile ci, pinned in the tests).
    """
    values = {name: np.asarray(x[name], dtype=np.float64) for name in x}
    moved = {name: value + 1.0 for name, value in values.items()}
    if not all(
        np.array_equal(moved[name] - 1.0, value, equal_nan=True)
        for name, value in values.items()
    ):
        moved = values
    return {
        name: value if value.ndim else float(value) for name, value in moved.items()
    }


DEGREE_DAYS: Final = FormulaSpec(
    name="degree_days",
    title="Growing and heating degree days of each day",
    function="hydrolog.statistics.meteo_temperature.daily_degree_days",
    family="index",
    equation=(
        "GDD = max(Tm - Tb, 0); HDD = Tr - Tm if Tm <= Tl, else 0 (Eurostat: Tr = 18 "
        "°C, Tl = 15 °C); Tl <= Tr"
    ),
    latex=(
        r"\mathrm{GDD} = \max(T_m - T_b, 0),\quad \mathrm{HDD} = \begin{cases} T_r - "
        r"T_m & T_m \le T_l \\ 0 & T_m > T_l \end{cases},\quad T_l \le T_r"
    ),
    variables=(
        Variable(
            name="tmean_c",
            symbol="T_m",
            unit="°C",
            kind="real_array",
            description="Daily mean air temperature; NaN on a missing day.",
            physical=Range(low=-273.15, test_high=56.7, test_reason=_RECORD_HEAT),
            applicability="unstated",
            typical=Range(low=-22.2, high=29.3, source=_WARSZAWA_T),
            gaps_allowed=True,
        ),
        _air(
            "growing_base_c",
            "T_b",
            "Base of the growing degree days.",
            Range(low=0.0, high=10.0, source=_WYPYCH),
        ),
        _air(
            "heating_base_c",
            "T_r",
            "Reference temperature of the heating degree days (Polish „temperatura "
            "bazowa”).",
            Range(low=18.0, high=18.0, source=_EUROSTAT),
        ),
        _air(
            "heating_limit_c",
            "T_l",
            "Heating threshold: a day heats when Tm is at most this (Eurostat's "
            "English base temperature, Polish „temperatura graniczna”).",
            Range(low=15.0, high=15.0, source=_EUROSTAT),
        ),
    ),
    outputs=(
        Output(
            name="growing_degree_days",
            unit="°C·d",
            kind="real_array",
            symbol=r"\mathrm{GDD}",
            description="Growing degree days of each day.",
            physical=Range(low=0.0),
            gaps_allowed=True,
            gaps_from="tmean_c",
        ),
        Output(
            name="heating_degree_days",
            unit="°C·d",
            kind="real_array",
            symbol=r"\mathrm{HDD}",
            description="Heating degree days of each day.",
            physical=Range(low=0.0),
            gaps_allowed=True,
            gaps_from="tmean_c",
        ),
    ),
    sources=(_EUROSTAT, _WYPYCH),
    constraints=(
        Constraint(
            name="heating_limit_not_above_base",
            cls="precondition",
            check=lambda x: x.real("heating_limit_c") <= x.real("heating_base_c"),
            text="heating_limit_c <= heating_base_c: a heating day lies below the "
            "reference temperature, so its degree days are not negative",
            source=_EUROSTAT,
            satisfied={"heating_base_c": 18.0, "heating_limit_c": 15.0},
            violated={"heating_base_c": 18.0, "heating_limit_c": 18.5},
            boundary={"heating_base_c": 18.0, "heating_limit_c": 18.0},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"tmean_c": 1, "growing_base_c": -1},
        symmetries=(
            Symmetry(
                name="shifted_temperatures",
                text="the temperature and the three thresholds shifted by 1 °C, where "
                "the shift is exact in binary, give the same degree days",
                inputs=_shifted,
                outputs=lambda out: {
                    "growing_degree_days": out.array("growing_degree_days"),
                    "heating_degree_days": out.array("heating_degree_days"),
                },
                tolerance=Tolerance(
                    abs=1e-12,
                    reason="each sum of a temperature and 1 °C rounds by half a unit "
                    "in the last place of values below 330 °C",
                ),
            ),
        ),
    ),
    validation="none: an index of the daily mean",
    formula_version=1,
    status="referenced",
    conventions=(
        "Tm is the daily mean given; Eurostat's Directive takes Tm = (Tmin + Tmax) / "
        "2 (at Warszawa-Okęcie 1991-2020 HDD 3407 against 3365 °C·d)",
        "a day heats at Tm <= Tl (inclusive) and grows at Tm > Tb",
        "the series function sums the days of complete months and the twelve months "
        "of the year: no growing or heating season is cut out",
    ),
    traps={
        "gap_propagation": "type case tmean_c-nan_element: a missing day gives missing "
        "degree days and no other",
        "difference_denominator": "none divides; precondition "
        "heating_limit_not_above_base keeps Tr - Tm of a heating day >= 0",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
)


def daily_degree_days(
    tmean_c: NDArray[np.float64] | Sequence[float],
    growing_base_c: float,
    heating_base_c: float,
    heating_limit_c: float,
) -> DailyDegreeDays:
    """Return the growing and heating degree days of each day, spec degree_days.

    Parameters
    ----------
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    growing_base_c, heating_base_c, heating_limit_c : float
        The base of the growing degree days, the reference temperature and the
        heating threshold of the heating degree days [°C].

    Returns
    -------
    DailyDegreeDays
        The degree days of each day [°C·d].

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a heating threshold above the reference
        temperature among them (``precondition_failed``).
    """
    x = checked_inputs(
        DEGREE_DAYS,
        tmean_c=tmean_c,
        growing_base_c=growing_base_c,
        heating_base_c=heating_base_c,
        heating_limit_c=heating_limit_c,
    )
    out = checked_outputs(DEGREE_DAYS, _degree_days(x), inputs=x)
    return DailyDegreeDays(
        out.array("growing_degree_days"), out.array("heating_degree_days")
    )


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

    GDD = Σ max(Tmean - 5, 0), the thermal resources above the base of the growing
    season (Wypych et al., 2017, eq. 1, who also use 0 and 10 °C); HDD = Σ (18 -
    Tmean) over the days with Tmean <= 15 °C (Eurostat, nrg_chdd, 3.4; Commission
    Directive (EU) 2015/1127), with the bases and the threshold as defaults. Both are
    summed over every day of each month and the months of the year of ``year_type``
    (Wypych et al.: "for the whole year"; the Directive: computed daily and summed to
    the year); no growing or heating season is cut out. Eurostat's daily mean Tm is
    (Tmin + Tmax) / 2 (the Directive), whereas this function takes the daily mean
    given: with IMGW-PIB's daily mean, which is about 0.1 °C lower, HDD at
    Warszawa-Okęcie 1991-2020 is 1.3 % above the value of (Tmin + Tmax) / 2; pass that
    mean as ``tmean_c`` to reproduce Eurostat's definition.

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing.
    tmean_c : array_like of float
        Daily mean temperature [°C]; ``NaN`` on a missing day.
    growing_base_c : float, optional
        Base of the growing degree days [°C], by default 5.
    heating_base_c : float, optional
        Reference temperature of the heating degree days, from which Tmean is
        subtracted [°C], by default 18 (Polish „temperatura bazowa”, Dopke 2010).
    heating_limit_c : float, optional
        Heating threshold: a day counts in the heating degree days when Tmean <= this
        [°C], by default 15 (Eurostat's English "base temperature", Polish
        „temperatura graniczna”).
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    DegreeDays
        The degree days of each month and year and their means.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, a base is not finite or ``year_type`` is unknown,
        or the heating threshold lies above the reference temperature (the spec
        ``degree_days``, ``precondition_failed``).
    """
    data = _series(dates, year_type, tmean_c=tmean_c)
    grid = data.grid
    days = daily_degree_days(
        _require(data.tmean, "tmean_c"), growing_base_c, heating_base_c, heating_limit_c
    )
    bases = {
        "growing_base_c": float(growing_base_c),
        "heating_base_c": float(heating_base_c),
        "heating_limit_c": float(heating_limit_c),
    }
    growing, heating = days.growing_degree_days, days.heating_degree_days
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


_ETCCDI_T = Source(
    citation="ETCCDI (2009). Climate Change Indices: definitions of the 27 core "
    "indices. Expert Team on Climate Change Detection and Indices",
    locator="FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; "
    "DTR: the monthly mean of TX - TN",
    url="https://etccdi.pacificclimate.org/list_27_indices.shtml",
)
_KOSSOWSKA = Source(
    citation="Kossowska-Cezak, U. (2014). Zmiany wieloletnie liczby termicznych dni "
    "charakterystycznych w Warszawie (1951-2010). Prace Geograficzne 136, 9-30",
    locator="p. 14, after the Słownik meteorologiczny (2003): a hot day („upalny”) "
    "has tmax > 30 °C, a freeze-thaw day („przymrozkowy”) tmin < 0 °C and tmax > 0 °C",
)
_IMGW_NORMALS = Source(
    citation="IMGW-PIB: Normy klimatyczne 1991-2020",
    locator="product PRZYMROZKI, „Liczba dni przymrozkowych (TMAX>0 & TMIN<0)”",
    url="https://klimat.imgw.pl",
)
_WARSZAWA_TX = Source(
    citation=_WARSZAWA_T.citation,
    locator="the daily maximum temperature: -16.7 to 37.0 °C",
)
_WARSZAWA_TN = Source(
    citation=_WARSZAWA_T.citation,
    locator="the daily minimum temperature: -27.1 to 22.8 °C",
)


class ThresholdDays(NamedTuple):
    """The characteristic days of each day (spec ``threshold_days``).

    Attributes
    ----------
    frost, freeze_thaw, ice, summer, hot, tropical : numpy.ndarray
        1 on a frost (freeze-thaw, ice, summer, hot) day or a tropical night, 0 on
        any other day, ``NaN`` where a temperature it needs is missing.
    """

    frost: NDArray[np.float64]
    freeze_thaw: NDArray[np.float64]
    ice: NDArray[np.float64]
    summer: NDArray[np.float64]
    hot: NDArray[np.float64]
    tropical: NDArray[np.float64]


def _flags(values: NDArray[np.float64], hit: NDArray[np.bool_]) -> NDArray[np.float64]:
    return np.where(np.isnan(values), np.nan, hit.astype(np.float64))


def _threshold_days(x: Values) -> dict[str, NDArray[np.float64]]:
    tmax, tmin = x.array("tmax_c"), x.array("tmin_c")
    with np.errstate(invalid="ignore"):
        frost = tmin < x.real("frost_tmin_c")
        thaw = tmax > x.real("ice_tmax_c")
        return {
            "frost": _flags(tmin, frost),
            "freeze_thaw": _flags(tmin + tmax, frost & thaw),
            "ice": _flags(tmax, tmax < x.real("ice_tmax_c")),
            "summer": _flags(tmax, tmax > x.real("summer_tmax_c")),
            "hot": _flags(tmax, tmax > x.real("hot_tmax_c")),
            "tropical": _flags(tmin, tmin > x.real("tropical_tmin_c")),
        }


_LIMITS = {
    "frost_tmin_c": 0.0,
    "ice_tmax_c": 0.0,
    "summer_tmax_c": 25.0,
    "hot_tmax_c": 30.0,
    "tropical_tmin_c": 20.0,
}


def _counted_days(run: Callable[..., Values]) -> None:
    rng = np.random.default_rng(20261119)
    tmax = np.round(rng.normal(12.0, 12.0, 400), 1)
    tmin = np.round(tmax - rng.gamma(4.0, 2.0, 400), 1)
    tmax[rng.random(400) < 0.05] = np.nan
    tmin[rng.random(400) < 0.05] = np.nan
    tmax[:8] = [0.0, -0.1, 25.0, 25.1, 30.0, 30.1, 0.1, 0.0]
    tmin[:8] = [0.0, -0.1, 20.0, 20.1, -0.1, -0.1, -0.1, -0.1]
    out = run(tmax_c=tmax.tolist(), tmin_c=tmin.tolist(), **_LIMITS)
    expected: dict[str, list[float]] = {name: [] for name in ThresholdDays._fields}
    for high, low in zip(tmax.tolist(), tmin.tolist(), strict=True):
        no_high, no_low = math.isnan(high), math.isnan(low)
        expected["frost"].append(math.nan if no_low else float(low < 0.0))
        expected["freeze_thaw"].append(
            math.nan if no_low or no_high else float(low < 0.0 and high > 0.0)
        )
        expected["ice"].append(math.nan if no_high else float(high < 0.0))
        expected["summer"].append(math.nan if no_high else float(high > 25.0))
        expected["hot"].append(math.nan if no_high else float(high > 30.0))
        expected["tropical"].append(math.nan if no_low else float(low > 20.0))
    for name, values in expected.items():
        assert_within(
            out.array(name), values, abs=0.0, reason="0 or 1 a day, NaN where missing"
        )


def _thaw_without_frost(x: Values, out: Values) -> float:
    """Return the freeze-thaw days that are not frost days: none."""
    excess = out.array("freeze_thaw") - out.array("frost")
    return float(np.nansum(np.clip(excess, 0.0, None)))


THRESHOLD_DAYS: Final = FormulaSpec(
    name="threshold_days",
    title="Frost, freeze-thaw, ice, summer and hot days and tropical nights of a day",
    function="hydrolog.statistics.meteo_temperature.threshold_days",
    family="classification",
    equation=(
        "frost: Tmin < Tf; freeze-thaw: Tmin < Tf and Tmax > Ti; ice: Tmax < Ti; "
        "summer: Tmax > Ts; hot: Tmax > Th; tropical night: Tmin > Tt; 1 when it "
        "holds, else 0 (the ETCCDI: Tf = Ti = 0, Ts = 25, Tt = 20 °C; Th = 30 °C)"
    ),
    latex=(
        r"\mathrm{FD} = [T_{n} < T_f],\ \mathrm{FT} = [T_{n} < T_f][T_{x} > T_i],\ "
        r"\mathrm{ID} = [T_{x} < T_i],\ \mathrm{SU} = [T_{x} > T_s],\ \mathrm{HD} = "
        r"[T_{x} > T_h],\ \mathrm{TR} = [T_{n} > T_t]"
    ),
    variables=(
        Variable(
            name="tmax_c",
            symbol="T_x",
            unit="°C",
            kind="real_array",
            description="Daily maximum air temperature; NaN on a missing day.",
            physical=Range(low=-273.15, test_high=56.7, test_reason=_RECORD_HEAT),
            applicability="unstated",
            typical=Range(low=-16.7, high=37.0, source=_WARSZAWA_TX),
            gaps_allowed=True,
        ),
        Variable(
            name="tmin_c",
            symbol="T_n",
            unit="°C",
            kind="real_array",
            description="Daily minimum air temperature of the same days; NaN on a "
            "missing day.",
            physical=Range(low=-273.15, test_high=56.7, test_reason=_RECORD_HEAT),
            applicability="unstated",
            typical=Range(low=-27.1, high=22.8, source=_WARSZAWA_TN),
            gaps_allowed=True,
        ),
        _air(
            "frost_tmin_c",
            "T_f",
            "A frost day has Tmin below this.",
            Range(low=0.0, high=0.0, source=_ETCCDI_T),
        ),
        _air(
            "ice_tmax_c",
            "T_i",
            "An ice day has Tmax below this, a freeze-thaw day above it.",
            Range(low=0.0, high=0.0, source=_ETCCDI_T),
        ),
        _air(
            "summer_tmax_c",
            "T_s",
            "A summer day has Tmax above this.",
            Range(low=25.0, high=25.0, source=_ETCCDI_T),
        ),
        _air(
            "hot_tmax_c",
            "T_h",
            "A hot day has Tmax above this.",
            Range(low=30.0, high=30.0, source=_KOSSOWSKA),
        ),
        _air(
            "tropical_tmin_c",
            "T_t",
            "A tropical night has Tmin above this.",
            Range(low=20.0, high=20.0, source=_ETCCDI_T),
        ),
    ),
    outputs=tuple(
        Output(
            name=name,
            unit="-",
            kind="real_array",
            description=description,
            physical=Range(low=0.0, high=1.0),
            gaps_allowed=True,
            gaps_from=source,
        )
        for name, description, source in (
            ("frost", "1 on a frost day.", "tmin_c"),
            ("freeze_thaw", "1 on a freeze-thaw day; NaN without both.", None),
            ("ice", "1 on an ice day.", "tmax_c"),
            ("summer", "1 on a summer day.", "tmax_c"),
            ("hot", "1 on a hot day.", "tmax_c"),
            ("tropical", "1 on a tropical night.", "tmin_c"),
        )
    ),
    sources=(_ETCCDI_T, _KOSSOWSKA, _IMGW_NORMALS),
    constraints=(
        Constraint(
            name="the_same_days",
            cls="precondition",
            check=lambda x: x.array("tmax_c").shape == x.array("tmin_c").shape,
            text="tmax_c and tmin_c hold the same days, one value of each a day",
            source=_ETCCDI_T,
            satisfied={"tmax_c": [5.0, 6.0], "tmin_c": [-1.0, 0.5]},
            violated={"tmax_c": [5.0, 6.0], "tmin_c": [-1.0]},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"tmin_c": -1, "frost_tmin_c": 1},
        conservation=(
            Conservation(
                name="a_freeze_thaw_day_is_a_frost_day",
                text="no freeze-thaw day without a frost day",
                residual=_thaw_without_frost,
                tolerance=Tolerance(abs=0.0, reason="counts of 0 and 1"),
            ),
        ),
        limits=(
            Limit(
                name="counting_oracle",
                text="every flag equals the comparison made day by day in a loop, at "
                "the ETCCDI's thresholds and beside them, with gaps",
                check=_counted_days,
            ),
        ),
    ),
    validation="none: a classification of a day",
    formula_version=1,
    status="referenced",
    conventions=(
        "strict signs as the ETCCDI: a day exactly at a threshold is none of these "
        "days; IMGW-PIB's yearbooks count Tmin <= 0 and Tmax >= 25 or 30 °C",
        "the freeze-thaw day is the „dzień przymrozkowy” of the Słownik "
        "meteorologiczny and of IMGW-PIB's normals (PRZYMROZKI); the frost day is FD",
        "a flag is missing (NaN) where a temperature it needs is; the series function "
        "gives an all-missing series for one it lacks",
    ),
    traps={
        "class_limit": "reference cases etccdi-*-boundary: each threshold and 0.1 °C "
        "beyond it",
        "gap_propagation": "type cases tmax_c-nan_element and tmin_c-nan_element: a "
        "missing temperature leaves only its own flags missing",
    },
    reference_cases=("tests/fixtures/formulas/meteo-indices-cases.json",),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the flags compared day by day in a Python loop on a seeded "
            "series with gaps and on the thresholds themselves",
            test="tests/unit/test_formulas_meteo_temperature.py (limit "
            "counting_oracle)",
        ),
    ),
)


def threshold_days(
    tmax_c: NDArray[np.float64] | Sequence[float],
    tmin_c: NDArray[np.float64] | Sequence[float],
    frost_tmin_c: float,
    ice_tmax_c: float,
    summer_tmax_c: float,
    hot_tmax_c: float,
    tropical_tmin_c: float,
) -> ThresholdDays:
    """Mark the characteristic days of each day, spec threshold_days.

    Parameters
    ----------
    tmax_c, tmin_c : array_like of float
        Daily maximum and minimum temperature of the same days [°C]; ``NaN`` on a
        missing day.
    frost_tmin_c, ice_tmax_c, summer_tmax_c, hot_tmax_c, tropical_tmin_c : float
        The thresholds [°C].

    Returns
    -------
    ThresholdDays
        The flags of each day.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, series of different days among them
        (``precondition_failed``).
    """
    x = checked_inputs(
        THRESHOLD_DAYS,
        tmax_c=tmax_c,
        tmin_c=tmin_c,
        frost_tmin_c=frost_tmin_c,
        ice_tmax_c=ice_tmax_c,
        summer_tmax_c=summer_tmax_c,
        hot_tmax_c=hot_tmax_c,
        tropical_tmin_c=tropical_tmin_c,
    )
    out = checked_outputs(THRESHOLD_DAYS, _threshold_days(x), inputs=x)
    return ThresholdDays(*(out.array(name) for name in ThresholdDays._fields))


SPECS: Final = (THRESHOLD_DAYS, DEGREE_DAYS)
"""The Tier A formulas of the module."""

_WMO_1203_T = (
    "WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, "
    "Geneva"
)
_WMO_1203_URL = "https://library.wmo.int/idurl/4/55797"

TIER_B: Final = (
    TierBSpec(
        name="temperature_monthly_means",
        function="hydrolog.statistics.meteo_temperature.temperature_means",
        definition="the mean of the daily Tmean, Tmax and Tmin of a month with fewer "
        "than 11 missing days and fewer than 5 in a row; of a year, the mean of its "
        "twelve monthly means, needing each",
        convention="the twelve months weigh the same (WMO-No. 1203, 4.3.3 a, footnote "
        "1: weighting by days not recommended)",
        source=Source(
            citation=_WMO_1203_T,
            locator="sections 4.3.1 (a) and 4.4.1 (a), pp. 5-7; 4.3.3 (a), p. 6",
            url=_WMO_1203_URL,
        ),
    ),
    TierBSpec(
        name="temperature_normals_and_anomalies",
        function="hydrolog.statistics.meteo_temperature.temperature_means",
        definition="the normal of Tmean of a calendar month: the mean of its monthly "
        "means in the years of the reference period that have one, when they are at "
        "least 80 % of its years; the annual normal, the mean of the twelve monthly "
        "normals; an anomaly, a mean less its normal",
        convention="the reference period is by default the analysed years; its years "
        "without data count among its years",
        source=Source(
            citation=_WMO_1203_T,
            locator="section 4.4.2, pp. 8-9; section 4.3.3 (a), p. 6",
            url=_WMO_1203_URL,
        ),
    ),
    TierBSpec(
        name="temperature_extremes",
        function="hydrolog.statistics.meteo_temperature.temperature_means",
        definition="the highest Tmax and the lowest Tmin of a month, a year and the "
        "period, with their dates, from the days that have a value",
        convention="an extreme takes whatever days there are (WMO-No. 1203, 4.4.1 b); "
        "the first of equal extremes and its date",
        source=Source(
            citation=_WMO_1203_T, locator="section 4.4.1 (b), p. 7", url=_WMO_1203_URL
        ),
    ),
    TierBSpec(
        name="temperature_day_counts",
        function="hydrolog.statistics.meteo_temperature.temperature_days",
        definition="the days of each kind of threshold_days in a month with fewer than "
        "11 missing days and fewer than 5 in a row, scaled to the days of the month; "
        "of a year, the sum of its twelve months, needing each",
        convention="with gaps a month's count is not a whole number (climdex.pcic "
        "counts the days it has)",
        source=Source(
            citation=_WMO_1203_T,
            locator="section 4.3.1 (d) and 4.4.1 (d), pp. 5-8",
            url=_WMO_1203_URL,
        ),
    ),
    TierBSpec(
        name="degree_day_sums",
        function="hydrolog.statistics.meteo_temperature.degree_days",
        definition="the sum of the degree_days of each day of a month, needing every "
        "day; of a year, the sum of its twelve months, needing each",
        convention="no growing or heating season is cut out (Eurostat: computed daily "
        "and summed to the year)",
        source=_EUROSTAT,
    ),
    TierBSpec(
        name="daily_temperature_range",
        function="hydrolog.statistics.meteo_temperature.temperature_range",
        definition="DTR: Tmax - Tmin of each day with both, its mean in a month with "
        "fewer than 11 missing days and fewer than 5 in a row, and of a year the mean "
        "of its twelve monthly means",
        convention="a day with Tmax below Tmin is taken as it is (no check; an open "
        "question of the audit of 2026-11-18)",
        source=_ETCCDI_T,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


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
