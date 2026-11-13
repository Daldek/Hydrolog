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
  consecutive-years criterion (4.4.2).

An annual value needs all twelve monthly values; annual extremes of daily values,
spells and percentile sums need every day of the year.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203,
    Geneva, section 4.4.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError

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
        """Lay values at their dates on the grid, ``NaN`` on the other days."""
        out = np.full(self.dates.size, np.nan)
        out[(dates - self.dates[0]).astype(np.int64)] = values
        return out

    def place_flags(
        self, dates: NDArray[np.datetime64], flags: NDArray[np.bool_]
    ) -> NDArray[np.bool_]:
        """Lay boolean flags at their dates on the grid, ``False`` on the other days."""
        out = np.zeros(self.dates.size, dtype=bool)
        out[(dates - self.dates[0]).astype(np.int64)] = flags
        return out

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
    fewer than 11 of its days.

    Returns
    -------
    NDArray[np.float64]
        ``(years, 12)`` sums [mm], ``NaN`` where missing.
    """
    sums, covered = sums_with_accumulated(raw, accumulated)
    lost = grid.per_month(covered.astype(np.float64)) >= WMO_MISSING_DAYS
    known = np.isfinite(sums)
    quality = month_quality(grid, known)
    totals = grid.per_month(np.where(known, sums, 0.0))
    monthly: NDArray[np.float64] = np.where(quality.complete & ~lost, totals, np.nan)
    return monthly


def normal(values: NDArray[np.float64]) -> tuple[float | None, int]:
    """Average the values of the years of a period, if enough years have one.

    Parameters
    ----------
    values : NDArray[np.float64]
        One value per year of the period (``NaN`` where the year has none).

    Returns
    -------
    tuple of (float or None, int)
        The normal, ``None`` when fewer than 80 % of the years have a value
        (WMO-No. 1203, 4.4.2), and the number of years with a value.
    """
    have = np.isfinite(values)
    count = int(have.sum())
    if count == 0 or count < WMO_NORMAL_SHARE * values.size:
        return None, count
    return float(values[have].mean()), count


_SUM_DECIMALS = 6
"""Decimals the window sums are rounded to: decimal data summed in binary carry errors
that depend on the order of the additions, and windows with equal sums must tie (the
first one is then taken)."""


def rolling_sum(values: NDArray[np.float64], days: int) -> NDArray[np.float64]:
    """Sum the ``days`` values that end at each position.

    Each window is summed on its own and rounded to 1e-6, so that equal sums tie; the
    sum is ``NaN`` unless all its values are known (and for the first ``days - 1``
    positions).
    """
    out = np.full(values.size, np.nan)
    if days > values.size:
        return out
    windows = np.lib.stride_tricks.sliding_window_view(values, days)
    out[days - 1 :] = np.round(windows.sum(axis=1), _SUM_DECIMALS)
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
