"""Private machinery of the meteorological statistics: whole years, months, WMO rules.

A daily series of a station is laid on every day of the whole years that hold its
values (:func:`daily_grid`): calendar years (1 January - 31 December) or Polish
hydrological years (1 November - 31 October, named after the calendar year in which
they end). Each day has its year, its calendar month and a month *key*, the number of
the month counted from the first month of the grid, so that a month of a year is one
cell of a ``(years, 12)`` table whose columns run in the order of the year (January
to December, or November to October) and whose flattened cells run in time order.

Missing data follow the WMO Guidelines on the Calculation of Climate Normals
(WMO-No. 1203, 2017, section 4.4):

* a monthly mean or a monthly count of days is missing when 11 or more days of the
  month, or 5 or more consecutive days, are missing (4.4.1 a, d); a count is the share
  of the observed days with the event times the days of the month;
* a monthly sum needs every day; an accumulated total that follows missing days
  stands for them when it represents fewer than 5 consecutive days and fewer than 11
  days of the month (4.4.1 c);
* monthly extremes use whatever days there are (4.4.1 b);
* a normal needs values in at least 80 % of the years of its period, with no
  consecutive-years criterion (4.4.2);
* a normal of several months (a year, a half-year, a season) is the sum of the monthly
  normals of its months for a sum or a count, their mean for a mean, and is missing
  when one of them is (4.3.3), not the mean of the multi-month values of the years.

An annual value needs all twelve monthly values; annual extremes of daily values,
spells and percentile sums need every day of the year.

A period keeps the days of its own years only (plan 2026-11-13, D1): the analysed
years (:func:`period_days`) and the reference period of the baselines
(:func:`reference_period`; by default the analysed years) each lie on a grid of
their own. The normals that serve as the benchmark of anomalies (WMO-No. 1203,
chapter 2), the percentiles of the wet days and the fits of the SPI come from the
reference period, the values of the analysed years from their own days; the 80 % of
a normal count every year of the reference period, those without data too.

Every sum of daily precipitation is rounded to 1e-6 (:func:`round_sums`): 0.1-mm
data summed in binary carry errors that depend on the order of the additions, and
sums equal in decimal must be equal numbers (a tie of the Mann-Kendall test, the
first of equal windows).

These rules are Tier B of Nogat's computation standard (ADR-0059): the module has no
formula of its own (``SPECS`` is empty) and declares them in :data:`TIER_B`, which
``docs/FORMULAS.md`` shows.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203,
    Geneva, chapters 2, 3 and 5, sections 4.3 and 4.4.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from typing import Final, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import Constant, FormulaSpec, Source, TierBSpec

YearType = Literal["calendar", "hydrological"]
YEAR_TYPES: tuple[str, ...] = ("calendar", "hydrological")
"""Kinds of year: calendar (January - December) or hydrological (November - October)."""
SNOW_SEASON = "snow_season"
"""The kind of year of the snow cover: 1 August - 31 July, named after the year in
which it ends (the hydrological year of its winter)."""
_START_MONTHS = {"calendar": 1, "hydrological": 11, SNOW_SEASON: 8}

WMO_MISSING_DAYS = 11
"""WMO-No. 1203, 4.4.1: a monthly mean or count is missing from this many missing
days ..."""
WMO_MISSING_RUN = 5
"""... or from this many consecutive missing days."""
WMO_NORMAL_SHARE = 0.8
"""WMO-No. 1203, 4.4.2: a normal needs values in this share of the years of its
period."""


def check_year_type(year_type: str) -> None:
    """Require ``"calendar"`` or ``"hydrological"``.

    Raises
    ------
    InvalidParameterError
        If ``year_type`` is another value.
    """
    if year_type not in YEAR_TYPES:
        raise InvalidParameterError(
            f"year_type must be 'calendar' or 'hydrological', got {year_type!r}"
        )


def months_of(year_type: str) -> tuple[int, ...]:
    """Return the calendar months in the order of a year.

    I-XII for calendar years, XI-X for hydrological years, VIII-VII for snow seasons.
    """
    start = _START_MONTHS[year_type]
    return tuple((start - 1 + shift) % 12 + 1 for shift in range(12))


def as_days(dates: NDArray[np.datetime64] | Sequence[object]) -> NDArray[np.datetime64]:
    """Dates as ``datetime64[D]``."""
    return np.asarray(dates).astype("datetime64[D]")


def calendar_year(dates: NDArray[np.datetime64]) -> NDArray[np.int64]:
    """Calendar year of each date."""
    years: NDArray[np.int64] = dates.astype("datetime64[Y]").astype(np.int64) + 1970
    return years


def calendar_month(dates: NDArray[np.datetime64]) -> NDArray[np.int64]:
    """Calendar month (1-12) of each date."""
    months: NDArray[np.int64] = dates.astype("datetime64[M]").astype(np.int64) % 12 + 1
    return months


def year_of(dates: NDArray[np.datetime64], year_type: str) -> NDArray[np.int64]:
    """Return the year of each date.

    Calendar, hydrological (November and December count in the year that follows) or
    snow season (August to December do).
    """
    years = calendar_year(dates)
    start = _START_MONTHS[year_type]
    if start == 1:
        return years
    shifted: NDArray[np.int64] = np.where(
        calendar_month(dates) >= start, years + 1, years
    )
    return shifted


def year_start(year: int, year_type: str) -> np.datetime64:
    """Return the first day of a year: 1 January, or 1 November or 1 August before."""
    start = _START_MONTHS[year_type]
    if start == 1:
        return np.datetime64(f"{year:04d}-01-01", "D")
    return np.datetime64(f"{year - 1:04d}-{start:02d}-01", "D")


class DailyGrid(NamedTuple):
    """Every day of the whole years ``first_year`` to ``first_year + n_years - 1``.

    Attributes
    ----------
    dates : NDArray[np.datetime64]
        Every day of the years, in order (``datetime64[D]``).
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year : int
        The first year (its name).
    n_years : int
        Number of years.
    year : NDArray[np.int64]
        The year of each day.
    month : NDArray[np.int64]
        The calendar month of each day.
    key : NDArray[np.int64]
        ``(year - first_year) * 12 + position of the month in the year``: the month of
        each day, counted from the first month of the grid, in time order.
    """

    dates: NDArray[np.datetime64]
    year_type: str
    first_year: int
    n_years: int
    year: NDArray[np.int64]
    month: NDArray[np.int64]
    key: NDArray[np.int64]

    @property
    def years(self) -> NDArray[np.int64]:
        """The names of the years of the grid."""
        names: NDArray[np.int64] = self.first_year + np.arange(
            self.n_years, dtype=np.int64
        )
        return names

    @property
    def last_year(self) -> int:
        """The last year of the grid."""
        return self.first_year + self.n_years - 1

    @property
    def months(self) -> tuple[int, ...]:
        """The calendar months of the columns of a ``(years, 12)`` table."""
        return months_of(self.year_type)

    def place(
        self, dates: NDArray[np.datetime64], values: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Lay values at their dates on the grid, ``NaN`` on the other days.

        Days outside the grid's years are left out: a series may begin or end with
        whole years of missing days, before the first or after the last year with a
        value (:func:`grid_of_values`).
        """
        out = np.full(self.dates.size, np.nan)
        positions, inside = self._positions(dates)
        out[positions] = values[inside]
        return out

    def place_flags(
        self, dates: NDArray[np.datetime64], flags: NDArray[np.bool_]
    ) -> NDArray[np.bool_]:
        """Lay boolean flags at their dates on the grid, ``False`` on the other days.

        Days outside the grid's years are left out, as in :meth:`place`.
        """
        out = np.zeros(self.dates.size, dtype=bool)
        positions, inside = self._positions(dates)
        out[positions] = flags[inside]
        return out

    def _positions(
        self, dates: NDArray[np.datetime64]
    ) -> tuple[NDArray[np.int64], NDArray[np.bool_]]:
        """Return where the days of ``dates`` lie on the grid, and which of them do."""
        offsets = (dates - self.dates[0]).astype(np.int64)
        inside = (offsets >= 0) & (offsets < self.dates.size)
        positions: NDArray[np.int64] = offsets[inside]
        return positions, inside

    def per_month(self, weights: NDArray[np.float64]) -> NDArray[np.float64]:
        """Sum ``weights`` in each month, as a ``(years, 12)`` table."""
        totals = np.bincount(self.key, weights=weights, minlength=self.n_years * 12)
        table: NDArray[np.float64] = totals.reshape(self.n_years, 12)
        return table

    def month_starts(self) -> NDArray[np.intp]:
        """Return the position of the first day of every month, in time order."""
        starts: NDArray[np.intp] = np.flatnonzero(
            np.concatenate(([True], self.key[1:] != self.key[:-1]))
        )
        return starts

    def year_starts(self) -> NDArray[np.intp]:
        """Return the position of the first day of every year, in order."""
        starts: NDArray[np.intp] = np.flatnonzero(
            np.concatenate(([True], self.year[1:] != self.year[:-1]))
        )
        return starts

    def days_in_month(self) -> NDArray[np.float64]:
        """Count the calendar days of each month, as a ``(years, 12)`` table."""
        return self.per_month(np.ones(self.dates.size))

    def iso(self, position: int) -> str | None:
        """Return the ISO date of a day of the grid, ``None`` before the grid."""
        return None if position < 0 else str(self.dates[position])

    def flat_index(self, year: int, month: int) -> int | None:
        """Return the cell of a calendar month in the flattened ``(years, 12)`` table.

        Parameters
        ----------
        year : int
            Calendar year of the month.
        month : int
            Calendar month (1-12).

        Returns
        -------
        int or None
            The position of the month in time order, ``None`` outside the grid.
        """
        start = _START_MONTHS[self.year_type]
        label = year + (1 if start > 1 and month >= start else 0)
        slot = (month - start) % 12
        row = label - self.first_year
        if not 0 <= row < self.n_years:
            return None
        return row * 12 + slot


def daily_grid(first: np.datetime64, last: np.datetime64, year_type: str) -> DailyGrid:
    """Build the grid of the whole years from the year of ``first`` to that of ``last``.

    Parameters
    ----------
    first, last : numpy.datetime64
        The first and the last day that must lie on the grid.
    year_type : {"calendar", "hydrological"}
        The kind of year.

    Returns
    -------
    DailyGrid
        Every day of those years.
    """
    first_year = int(year_of(np.array([first], dtype="datetime64[D]"), year_type)[0])
    last_year = int(year_of(np.array([last], dtype="datetime64[D]"), year_type)[0])
    start = year_start(first_year, year_type)
    stop = year_start(last_year + 1, year_type)
    dates = np.arange(start, stop, dtype="datetime64[D]")
    year = year_of(dates, year_type)
    month = calendar_month(dates)
    slot = (month - _START_MONTHS[year_type]) % 12
    key: NDArray[np.int64] = (year - first_year) * 12 + slot
    return DailyGrid(
        dates, year_type, first_year, last_year - first_year + 1, year, month, key
    )


def grid_of_values(
    dates: NDArray[np.datetime64],
    known: NDArray[np.bool_],
    year_type: str,
) -> DailyGrid:
    """Build the grid of the years from the first to the last day with a value.

    Raises
    ------
    InvalidParameterError
        If no day has a value.
    """
    if not known.any():
        raise InvalidParameterError("the series has no value")
    where = np.flatnonzero(known)
    return daily_grid(dates[where[0]], dates[where[-1]], year_type)


def check_daily(dates: NDArray[np.datetime64], *arrays: NDArray[np.float64]) -> None:
    """Require non-empty, equally long arrays and strictly increasing dates.

    Raises
    ------
    InvalidParameterError
        If they are empty, differ in length or the dates do not increase.
    """
    if dates.size == 0 or any(array.size != dates.size for array in arrays):
        raise InvalidParameterError(
            "values and dates must be non-empty and of the same length"
        )
    if dates.size > 1 and not bool(np.all(dates[1:] > dates[:-1])):
        raise InvalidParameterError("dates must be strictly increasing")


# --- the analysed years and the reference period (plan 2026-11-13, D1) ---------------


def in_years(
    dates: NDArray[np.datetime64],
    year_type: str,
    first_year: int | None,
    last_year: int | None,
) -> NDArray[np.bool_]:
    """Tell the days of the years ``first_year`` to ``last_year`` (``None``: open)."""
    years = year_of(dates, year_type)
    keep = np.ones(dates.size, dtype=bool)
    if first_year is not None:
        keep &= years >= first_year
    if last_year is not None:
        keep &= years <= last_year
    return keep


def _available(
    dates: NDArray[np.datetime64], known: NDArray[np.bool_], year_type: str
) -> list[int]:
    """Return the first and the last year with a value."""
    years = year_of(dates[known], year_type)
    return [int(years.min()), int(years.max())]


def period_days(
    dates: NDArray[np.datetime64],
    known: NDArray[np.bool_],
    year_type: str,
    first_year: int | None = None,
    last_year: int | None = None,
) -> NDArray[np.bool_]:
    """Pick the days of the analysed years ``first_year`` to ``last_year``.

    Parameters
    ----------
    dates : NDArray[np.datetime64]
        The days of the record (``datetime64[D]``).
    known : NDArray[np.bool_]
        The days with a value.
    year_type : str
        The kind of year of the bounds.
    first_year, last_year : int, optional
        The first and the last year; by default those of the record.

    Returns
    -------
    NDArray[np.bool_]
        The days of those years.

    Raises
    ------
    InvalidParameterError
        If ``first_year`` is after ``last_year`` (``details``: ``option``
        ``first_year``, ``reason`` ``range``, ``first_year``, ``last_year``).
    CalculationError
        If a day of the record has a value but none of those years
        (``details.reason`` ``no_values_in_period``, ``first_year``, ``last_year`` and
        ``available``, the first and the last year with a value).
    """
    if first_year is not None and last_year is not None and first_year > last_year:
        raise InvalidParameterError(
            f"Option 'first_year' ({first_year}) is after 'last_year' ({last_year})",
            details={
                "option": "first_year",
                "reason": "range",
                "first_year": first_year,
                "last_year": last_year,
            },
            hint="Give the first year of the period, then the last.",
        )
    keep = in_years(dates, year_type, first_year, last_year)
    if known.any() and not (keep & known).any():
        raise CalculationError(
            f"No value in the years {first_year} to {last_year}",
            details={
                "reason": "no_values_in_period",
                "first_year": first_year,
                "last_year": last_year,
                "available": _available(dates, known, year_type),
            },
            hint="Choose years that the series covers.",
        )
    return keep


class ReferencePeriod(NamedTuple):
    """The reference period of the baselines: the normals, percentiles and SPI fits.

    Normals are the benchmark against which observations are compared (WMO-No. 1203,
    chapter 2): the climatological standard normal, the latest 30 years ending in a
    year ending in 0 (now 1991-2020), for monitoring and anomalies, and the reference
    normal of 1961-1990 for long-term climate change (chapters 2 and 3, section 5.1).

    Attributes
    ----------
    first_year, last_year : int
        Its first and last year, as given or by default those of the analysed years.
    keep : NDArray[np.bool_]
        The days of the record in its years.
    """

    first_year: int
    last_year: int
    keep: NDArray[np.bool_]

    @property
    def n_years(self) -> int:
        """Count its years, those without data too: the base of the 80 % rule."""
        return self.last_year - self.first_year + 1

    def is_period_of(self, grid: DailyGrid) -> bool:
        """Tell whether its years are those of ``grid`` (as by default)."""
        return (self.first_year, self.last_year) == (grid.first_year, grid.last_year)


def reference_period(
    dates: NDArray[np.datetime64],
    known: NDArray[np.bool_],
    year_type: str,
    analysed: DailyGrid,
    first_year: int | None = None,
    last_year: int | None = None,
) -> ReferencePeriod:
    """Resolve the reference period of the baselines and pick its days.

    Parameters
    ----------
    dates, known, year_type
        The whole record, as for :func:`period_days`.
    analysed : DailyGrid
        The analysed years: the default first and last year.
    first_year, last_year : int, optional
        ``reference_first_year`` and ``reference_last_year`` (years of
        ``year_type``); each by default that of ``analysed``.

    Returns
    -------
    ReferencePeriod
        Its years and the days of the record in them.

    Raises
    ------
    InvalidParameterError
        If its first year is after its last (``details``: ``option``
        ``reference_first_year``, ``reason`` ``range``, ``first_year``,
        ``last_year``).
    CalculationError
        If no day of its years has a value (``details.reason``
        ``no_values_in_period``, ``option`` ``reference_first_year``, ``first_year``,
        ``last_year`` and ``available``).
    """
    first = analysed.first_year if first_year is None else int(first_year)
    last = analysed.last_year if last_year is None else int(last_year)
    if first > last:
        defaulted = (
            ""
            if first_year is not None and last_year is not None
            else " (a bound not given is that of the analysed years)"
        )
        raise InvalidParameterError(
            f"The reference period starts in {first}, after its last year {last}"
            f"{defaulted}",
            details={
                "option": "reference_first_year",
                "reason": "range",
                "first_year": first,
                "last_year": last,
            },
            hint="Give reference_first_year not after reference_last_year.",
        )
    keep = in_years(dates, year_type, first, last)
    if not (keep & known).any():
        raise CalculationError(
            f"No value in the reference period {first} to {last}",
            details={
                "reason": "no_values_in_period",
                "option": "reference_first_year",
                "first_year": first,
                "last_year": last,
                "available": _available(dates, known, year_type),
            },
            hint="Choose a reference period that the series covers.",
        )
    return ReferencePeriod(first, last, keep)


class MonthQuality(NamedTuple):
    """How complete each month of a daily series is (WMO-No. 1203, 4.4.1).

    Attributes
    ----------
    known : NDArray[np.float64]
        Days with a value, ``(years, 12)``.
    days : NDArray[np.float64]
        Calendar days of the month, ``(years, 12)``.
    run : NDArray[np.int64]
        The longest run of missing days inside the month, ``(years, 12)``.
    """

    known: NDArray[np.float64]
    days: NDArray[np.float64]
    run: NDArray[np.int64]

    @property
    def complete(self) -> NDArray[np.bool_]:
        """Every day of the month has a value."""
        full: NDArray[np.bool_] = self.known == self.days
        return full

    @property
    def enough(self) -> NDArray[np.bool_]:
        """Tell the months with enough days for a mean or a count.

        Fewer than 11 missing, fewer than 5 in a row, and at least one with a value.
        """
        good: NDArray[np.bool_] = (
            (self.days - self.known < WMO_MISSING_DAYS)
            & (self.run < WMO_MISSING_RUN)
            & (self.known > 0)
        )
        return good


def month_quality(grid: DailyGrid, known: NDArray[np.bool_]) -> MonthQuality:
    """Days with a value and the longest run of missing days of each month."""
    missing = ~known
    key = grid.key
    new_month = np.concatenate(([True], key[1:] != key[:-1]))
    first = missing & (new_month | np.concatenate(([True], ~missing[:-1])))
    index = np.arange(known.size)
    run_start = np.maximum.accumulate(np.where(first, index, -1))
    length = np.where(missing, index - run_start + 1, 0)
    run: NDArray[np.int64] = (
        np.maximum.reduceat(length, grid.month_starts())
        .astype(np.int64)
        .reshape(grid.n_years, 12)
    )
    return MonthQuality(
        grid.per_month(known.astype(np.float64)), grid.days_in_month(), run
    )


def monthly_means(grid: DailyGrid, values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Monthly means where the month has enough days (WMO-No. 1203, 4.4.1 a)."""
    known = np.isfinite(values)
    quality = month_quality(grid, known)
    total = grid.per_month(np.where(known, values, 0.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = total / quality.known
    means: NDArray[np.float64] = np.where(quality.enough, mean, np.nan)
    return means


def monthly_counts(
    grid: DailyGrid, values: NDArray[np.float64], event: NDArray[np.bool_]
) -> NDArray[np.float64]:
    """Days with ``event`` in each month, scaled to the days of the month.

    The share of the days with a value on which the event happened times the days of
    the month (WMO-No. 1203, 4.3 and 4.4.1 d); missing for a month without enough days.
    """
    known = np.isfinite(values)
    quality = month_quality(grid, known)
    count = grid.per_month((event & known).astype(np.float64))
    with np.errstate(invalid="ignore", divide="ignore"):
        scaled = count / quality.known * quality.days
    counts: NDArray[np.float64] = np.where(quality.enough, scaled, np.nan)
    return counts


def monthly_totals(grid: DailyGrid, values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Monthly sums of a daily quantity where every day of the month has a value."""
    known = np.isfinite(values)
    quality = month_quality(grid, known)
    totals: NDArray[np.float64] = np.where(
        quality.complete, grid.per_month(np.where(known, values, 0.0)), np.nan
    )
    return totals


_SUM_DECIMALS = 6
"""Decimals every sum of daily precipitation is rounded to (:func:`round_sums`)."""


def round_sums(sums: NDArray[np.float64]) -> NDArray[np.float64]:
    """Round sums of daily precipitation to 1e-6 [mm].

    Decimal data summed in binary carry errors that depend on the order of the
    additions (0.1 + 0.2 gives 0.30000000000000004). Rounded, a sum of 0.1-mm values
    is the number nearest its decimal value, so sums equal in decimal are equal
    numbers: a tie of the Mann-Kendall test, the first of equal windows. ``NaN``
    stays ``NaN``.
    """
    rounded: NDArray[np.float64] = np.round(sums, _SUM_DECIMALS)
    return rounded


def round_sum(value: float) -> float:
    """Round one sum of daily precipitation as :func:`round_sums` does [mm]."""
    return float(np.round(value, _SUM_DECIMALS))


def sums_with_accumulated(
    raw: NDArray[np.float64], accumulated: NDArray[np.bool_]
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Daily precipitation for sums: accumulated totals stand for the days they cover.

    A total flagged as accumulated (IMGW-PIB marks a reading that follows days
    without one) stands for the missing days just before it when, with its own day,
    they are fewer than 5 (WMO-No. 1203, 4.4.1 c): its day gets the total, the days it
    covers get 0. A total that follows 4 or more missing days covers nothing and its
    day stays missing.

    Parameters
    ----------
    raw : NDArray[np.float64]
        Daily precipitation on a grid, totals included; ``NaN`` on a missing day.
    accumulated : NDArray[np.bool_]
        The days whose value is an accumulated total.

    Returns
    -------
    tuple of NDArray
        The precipitation for sums (``NaN`` where unknown) and the days that an
        accumulated total represents (the total's day and the days it covers).
    """
    sums = np.where(accumulated, np.nan, raw)
    covered = np.zeros(raw.size, dtype=bool)
    missing = ~np.isfinite(raw)
    for total in np.flatnonzero(accumulated & ~missing).tolist():
        first = total
        while first > 0 and missing[first - 1]:
            first -= 1
        if total - first + 1 < WMO_MISSING_RUN:
            sums[first:total] = 0.0
            sums[total] = raw[total]
            covered[first : total + 1] = True
    return sums, covered


def monthly_precipitation(
    grid: DailyGrid,
    raw: NDArray[np.float64],
    accumulated: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Monthly precipitation sums by WMO-No. 1203, 4.4.1 c.

    A month has a sum when every day is known after the accumulated totals stand for
    the days they cover (:func:`sums_with_accumulated`) and the totals represent
    fewer than 11 of its days. The sums are rounded to 1e-6 (:func:`round_sums`).

    Returns
    -------
    NDArray[np.float64]
        ``(years, 12)`` sums [mm], ``NaN`` where missing.
    """
    sums, covered = sums_with_accumulated(raw, accumulated)
    lost = grid.per_month(covered.astype(np.float64)) >= WMO_MISSING_DAYS
    known = np.isfinite(sums)
    quality = month_quality(grid, known)
    totals = round_sums(grid.per_month(np.where(known, sums, 0.0)))
    monthly: NDArray[np.float64] = np.where(quality.complete & ~lost, totals, np.nan)
    return monthly


def normal(
    values: NDArray[np.float64], years: int | None = None
) -> tuple[float | None, int]:
    """Average the values of the years of a period, if enough years have one.

    Parameters
    ----------
    values : NDArray[np.float64]
        One value per year with data (``NaN`` where the year has none).
    years : int, optional
        The years of the period, those without data too; by default ``values.size``.

    Returns
    -------
    tuple of (float or None, int)
        The normal, ``None`` when fewer than 80 % of the years have a value
        (WMO-No. 1203, 4.4.2), and the number of years with a value.
    """
    have = np.isfinite(values)
    count = int(have.sum())
    span = values.size if years is None else years
    if count == 0 or count < WMO_NORMAL_SHARE * span:
        return None, count
    return float(values[have].mean()), count


def monthly_normals(
    table: NDArray[np.float64], years: int | None = None
) -> tuple[list[float | None], int]:
    """Return the normal of each month of a ``(years, 12)`` table (:func:`normal`).

    Returns
    -------
    tuple of (list of float or None, int)
        The normals in the order of the columns and the fewest years with a value
        among the months: every monthly normal exists when that number reaches 80 %
        of the years (WMO-No. 1203, 4.4.2).
    """
    pairs = [normal(table[:, slot], years) for slot in range(table.shape[1])]
    return [value for value, _ in pairs], min(count for _, count in pairs)


def multimonth_normal(
    normals: Sequence[float | None], *, mean: bool = False
) -> float | None:
    """Combine the normals of the months of a year, half-year or season.

    WMO-No. 1203, 4.3.3: the normal of several months is the sum of their monthly
    normals for a sum or a count, their (unweighted) mean for a mean, and missing when
    one of them is; it is not computed from the multi-month values of the years.

    Parameters
    ----------
    normals : sequence of float or None
        The normals of the months concerned.
    mean : bool, optional
        Average them (a mean parameter) instead of summing them.

    Returns
    -------
    float or None
        The normal, ``None`` when a monthly normal is.
    """
    values = [value for value in normals if value is not None]
    if not values or len(values) < len(normals):
        return None
    total = math.fsum(values)
    return total / len(values) if mean else total


def rolling_sum(values: NDArray[np.float64], days: int) -> NDArray[np.float64]:
    """Sum the ``days`` values that end at each position.

    Each window is summed on its own and rounded to 1e-6 (:func:`round_sums`), so
    that equal sums tie; the sum is ``NaN`` unless all its values are known (and for
    the first ``days - 1`` positions).
    """
    out = np.full(values.size, np.nan)
    if days > values.size:
        return out
    windows = np.lib.stride_tricks.sliding_window_view(values, days)
    out[days - 1 :] = round_sums(windows.sum(axis=1))
    return out


def block_extreme(
    values: NDArray[np.float64], starts: NDArray[np.intp], *, largest: bool = True
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Find the largest (or smallest) value of each block and its first position.

    Parameters
    ----------
    values : NDArray[np.float64]
        Values; ``NaN`` where unknown.
    starts : NDArray[np.intp]
        The first position of each block (blocks run to the next start).
    largest : bool, optional
        The largest (default) or the smallest value.

    Returns
    -------
    tuple of NDArray
        The extreme of each block (``NaN`` for a block without a value) and the
        position of its first occurrence (``-1`` without a value).
    """
    count = values.size
    finite = np.isfinite(values)
    filled = np.where(finite, values, -np.inf if largest else np.inf)
    best = (np.maximum if largest else np.minimum).reduceat(filled, starts)
    lengths = np.diff(np.concatenate((starts, [count])))
    hit = finite & (filled == np.repeat(best, lengths))
    first = np.minimum.reduceat(np.where(hit, np.arange(count), count), starts)
    found = first < count
    extremes: NDArray[np.float64] = np.where(found, best, np.nan)
    positions: NDArray[np.int64] = np.where(found, first, -1).astype(np.int64)
    return extremes, positions


def finite(value: float) -> float | None:
    """Return a finite number, or ``None``."""
    number = float(value)
    return number if math.isfinite(number) else None


def mean_of(values: NDArray[np.float64]) -> float | None:
    """Return the mean of the finite values, ``None`` without one."""
    have = values[np.isfinite(values)]
    return float(have.mean()) if have.size else None


def years_with_values(grid: DailyGrid, known: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Tell, for each year of the grid, whether it has a day with a value."""
    counts = np.bincount(
        grid.year - grid.first_year,
        weights=known.astype(np.float64),
        minlength=grid.n_years,
    )
    present: NDArray[np.bool_] = counts > 0
    return present


def complete_years(grid: DailyGrid, known: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Tell, for each year of the grid, whether every day has a value."""
    starts = grid.year_starts()
    have = np.add.reduceat(known.astype(np.int64), starts)
    lengths = np.diff(np.concatenate((starts, [known.size])))
    complete: NDArray[np.bool_] = have == lengths
    return complete


def classify(
    value: float | None,
    limits: Sequence[float],
    names: Sequence[str],
    *,
    inclusive: bool = True,
) -> str | None:
    """Return the class of a value between ascending upper limits.

    Parameters
    ----------
    value : float or None
        The value; ``None`` or ``NaN`` has no class.
    limits : sequence of float
        Upper limits of the classes but the last, ascending.
    names : sequence of str
        One name more than ``limits``.
    inclusive : bool, optional
        A value equal to a limit belongs to the class below it (``<=``, default) or
        to the class above it (``<``).

    Returns
    -------
    str or None
        The name of the class.
    """
    if value is None or not math.isfinite(value):
        return None
    for limit, name in zip(limits, names, strict=False):
        if value <= limit if inclusive else value < limit:
            return name
    return names[-1]


# --- daily precipitation on its years -------------------------------------------------


class DailyPrecipitation(NamedTuple):
    """Daily precipitation laid on the whole years of its values.

    Attributes
    ----------
    grid : DailyGrid
        The years.
    raw : NDArray[np.float64]
        The values, accumulated totals included [mm]; ``NaN`` on a missing day.
    daily : NDArray[np.float64]
        The daily values [mm]: an accumulated total is a missing day.
    accumulated : NDArray[np.bool_]
        The days of the accumulated totals.
    present : NDArray[np.bool_]
        For each year of the grid, whether a day has a value.
    """

    grid: DailyGrid
    raw: NDArray[np.float64]
    daily: NDArray[np.float64]
    accumulated: NDArray[np.bool_]
    present: NDArray[np.bool_]

    def monthly(self) -> NDArray[np.float64]:
        """Return the monthly sums [mm], ``(years, 12)`` (WMO-No. 1203, 4.4.1 c)."""
        return monthly_precipitation(self.grid, self.raw, self.accumulated)


class PrecipitationRecord(NamedTuple):
    """A checked daily precipitation series, before it is laid on years.

    Attributes
    ----------
    days : NDArray[np.datetime64]
        The dates, strictly increasing (``datetime64[D]``).
    values : NDArray[np.float64]
        Daily precipitation [mm]; ``NaN`` on a missing day.
    accumulated : NDArray[np.bool_]
        The values that are accumulated totals of the missing days before them.
    year_type : str
        The kind of year.
    """

    days: NDArray[np.datetime64]
    values: NDArray[np.float64]
    accumulated: NDArray[np.bool_]
    year_type: str

    def on_grid(self, keep: NDArray[np.bool_] | None = None) -> DailyPrecipitation:
        """Lay the days of ``keep`` (every day by default) on the years of their values.

        Raises
        ------
        InvalidParameterError
            If no day of ``keep`` has a value.
        """
        days, values, flags = self.days, self.values, self.accumulated
        if keep is not None:
            days, values, flags = days[keep], values[keep], flags[keep]
        grid = grid_of_values(days, np.isfinite(values), self.year_type)
        raw = grid.place(days, values)
        totals = grid.place_flags(days, flags) & np.isfinite(raw)
        return DailyPrecipitation(
            grid,
            raw,
            np.where(totals, np.nan, raw),
            totals,
            years_with_values(grid, np.isfinite(raw)),
        )


def precipitation_record(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None,
    year_type: str,
) -> PrecipitationRecord:
    """Check a daily precipitation series.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase, a
        value is negative or ``year_type`` is unknown.
    """
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
    negative = np.flatnonzero(values < 0)
    if negative.size:
        at = int(negative[0])
        raise InvalidParameterError(
            f"precipitation must not be negative; precipitation_mm[{at}] = "
            f"{values[at]:g} mm is outside its physical range [0, inf)",
            details={
                "reason": "outside_physical_range",
                "option": "precipitation_mm",
                "variable": "precipitation_mm",
                "value": float(values[at]),
                "index": [at],
            },
        )
    return PrecipitationRecord(days, values, flags, year_type)


class PrecipitationPeriods(NamedTuple):
    """Daily precipitation of the analysed years and of the reference period.

    Attributes
    ----------
    data : DailyPrecipitation
        The analysed years: their values.
    reference : DailyPrecipitation
        The years of the reference period: the baselines; ``data`` itself when they
        are the analysed years.
    period : ReferencePeriod
        The reference period.
    """

    data: DailyPrecipitation
    reference: DailyPrecipitation
    period: ReferencePeriod

    @property
    def reference_period_years(self) -> int:
        """Count the years of the reference period with a value."""
        return int(self.reference.present.sum())


def precipitation_periods(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    accumulated: NDArray[np.bool_] | Sequence[bool] | None,
    year_type: str,
    *,
    first_year: int | None = None,
    last_year: int | None = None,
    reference_first_year: int | None = None,
    reference_last_year: int | None = None,
) -> PrecipitationPeriods:
    """Check a daily precipitation series and lay its two periods on their years.

    Each period keeps the days of its own years only (plan 2026-11-13, D1).

    Raises
    ------
    InvalidParameterError
        If the series is invalid (:func:`precipitation_record`), has no value, or a
        period's first year is after its last.
    CalculationError
        If a period has no value (``no_values_in_period``).
    """
    record = precipitation_record(precipitation_mm, dates, accumulated, year_type)
    known = np.isfinite(record.values)
    data = record.on_grid(
        period_days(record.days, known, year_type, first_year, last_year)
    )
    period = reference_period(
        record.days,
        known,
        year_type,
        data.grid,
        reference_first_year,
        reference_last_year,
    )
    reference = data if period.is_period_of(data.grid) else record.on_grid(period.keep)
    return PrecipitationPeriods(data, reference, period)


SPECS: Final[tuple[FormulaSpec, ...]] = ()
"""The Tier A formulas of the module: none, its rules are Tier B."""

_WMO_1203 = (
    "WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, "
    "Geneva"
)
_WMO_1203_URL = "https://library.wmo.int/idurl/4/55797"


def _wmo(locator: str) -> Source:
    return Source(citation=_WMO_1203, locator=locator, url=_WMO_1203_URL)


_MISSING = _wmo(
    "section 4.4.1 (a) and footnote 4, p. 7: a mean is not calculated when 11 or more "
    "days are missing or 5 or more consecutive days"
)

TIER_B: Final = (
    TierBSpec(
        name="wmo_monthly_mean",
        function="hydrolog.statistics._climate.monthly_means",
        definition="the mean of the daily values of a month with fewer than 11 missing "
        "days and fewer than 5 missing in a row, and at least one value",
        convention="a day of the grid without a date counts as missing",
        source=_MISSING,
        constants=(
            Constant(
                name="missing_days", value=11.0, unit="d", symbol="11", source=_MISSING
            ),
            Constant(
                name="missing_run", value=5.0, unit="d", symbol="5", source=_MISSING
            ),
        ),
    ),
    TierBSpec(
        name="wmo_monthly_count",
        function="hydrolog.statistics._climate.monthly_counts",
        definition="the days of an event in a month whose mean could be calculated, "
        "scaled to the days of the month: the events over the days with a value times "
        "the days of the month",
        convention="the scaling of every such month (WMO-No. 1203 gives the ratio for "
        "normals); a count is then not a whole number",
        source=_wmo("sections 4.3.1 (d) and 4.4.1 (d), pp. 5-8"),
    ),
    TierBSpec(
        name="wmo_monthly_sum",
        function="hydrolog.statistics._climate.monthly_totals",
        definition="the sum of the daily values of a month with every day",
        convention="no sum of a month with a missing day",
        source=_wmo("sections 4.3.1 (c) and 4.4.1 (c), pp. 5-8"),
    ),
    TierBSpec(
        name="accumulated_totals",
        function="hydrolog.statistics._climate.monthly_precipitation",
        definition="a total flagged as accumulated stands for the missing days just "
        "before it when, with its own day, they are fewer than 5; a month's sum takes "
        "such totals when fewer than 11 of its days are covered by them",
        convention="a block over the start of a month is judged on its whole length; "
        "the total counts in the month of its own day",
        source=_wmo(
            "section 4.4.1 (c), pp. 7-8: accumulated observations that cover the full "
            "period of missing data, not 11 or more days nor 5 or more in a row"
        ),
    ),
    TierBSpec(
        name="wmo_normal",
        function="hydrolog.statistics._climate.normal",
        definition="the normal of a calendar month: the mean of its values in the "
        "years of the reference period with one, when they are at least 80 % of its "
        "years",
        convention="every year of the reference period counts, those without data too; "
        "no consecutive-years criterion",
        source=_wmo("section 4.4.2, pp. 8-9"),
        constants=(
            Constant(
                name="normal_share",
                value=Fraction(4, 5),
                unit="-",
                symbol="80 %",
                source=_wmo("section 4.4.2, pp. 8-9: 24 or more of 30 years"),
            ),
        ),
    ),
    TierBSpec(
        name="multimonth_normal",
        function="hydrolog.statistics._climate.multimonth_normal",
        definition="the normal of a year, half-year or season: the sum of the normals "
        "of its months for a sum or a count, their mean for a mean",
        convention="from the monthly normals, not from the annual values (WMO-No. "
        "1203, 4.3.3: identical without missing months)",
        source=_wmo("section 4.3.3, p. 6"),
    ),
    TierBSpec(
        name="block_extreme",
        function="hydrolog.statistics._climate.block_extreme",
        definition="the extreme of a month from the days that have a value, with the "
        "first date it occurs",
        convention="an annual extreme of a statistic that needs every day is taken by "
        "its series function from complete years only",
        source=_wmo("section 4.4.1 (b), p. 7: extremes regardless of missing data"),
    ),
    TierBSpec(
        name="rounded_sums",
        function="hydrolog.statistics._climate.round_sums",
        definition="every sum of daily precipitation rounded to 1e-6 mm",
        convention="0.1-mm data summed in binary depend on the order of the additions; "
        "rounded, sums equal in decimal are equal numbers (ties of the Mann-Kendall "
        "test, the first of equal windows); at most 5e-7 mm per sum",
        source=Source(
            citation="Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a "
            "station, the group meteo",
            locator="the sums of daily precipitation",
            url="https://github.com/Daldek/Hydrolog/blob/develop/docs/decisions/"
            "0032-meteorological-statistics-of-a-station-the-group-meteo.md",
        ),
    ),
    TierBSpec(
        name="years_of_a_series",
        function="hydrolog.statistics._climate.year_of",
        definition="the calendar year (January - December), the Polish hydrological "
        "year (November - October) named after the year it ends, or the snow season "
        "(August - July) named after the year it ends",
        convention="a year is laid on the grid whole, its days without a value missing",
        source=_wmo("chapter 2: normals of calendar months"),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
