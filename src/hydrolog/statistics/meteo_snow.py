"""Snow cover of each winter of a daily series of a meteorological station.

A winter is a snow season, 1 August - 31 July, named after the year in which it ends:
the hydrological year (November - October) of its winter months, with the whole cold
season kept together, so that snow of late October (or of September in the
mountains) starts the winter it belongs to. A day with snow cover has a depth of at
least 1 cm. The days with snow cover of a month are scaled to its days when fewer
than 11 days, and fewer than 5 in a row, are missing (WMO-No. 1203, 4.3 and 4.4.1 d);
a month with more missing days adds the days observed. A winter is counted when every
month from October to May has enough days; the largest depth with its day, the first
and the last day with snow cover and the sum of the depths of fresh snow take
whatever days the winter has.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203,
    sections 4.3 and 4.4.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._climate import (
    SNOW_SEASON,
    as_days,
    block_extreme,
    check_daily,
    finite,
    grid_of_values,
    mean_of,
    month_quality,
    monthly_counts,
    years_with_values,
)

__all__ = [
    "SNOW_COVER_CM",
    "SNOW_SEASON_MONTHS",
    "SnowCover",
    "SnowMonth",
    "SnowPeriod",
    "SnowYear",
    "snow_cover",
]

SNOW_COVER_CM = 1.0
"""A day with snow cover has a depth of at least this [cm]."""
SNOW_SEASON_MONTHS: tuple[int, ...] = (10, 11, 12, 1, 2, 3, 4, 5)
"""The months whose data a winter needs: October to May."""
_REFERENCE_START = np.datetime64("2001-08-01", "D")
"""The first day of a snow season without 29 February (2001/02), for the median
first and last day."""


@dataclass
class SnowYear(JsonResultMixin):
    """The snow cover of one winter.

    Attributes
    ----------
    year : int
        The winter: the snow season August - July named after the year in which it
        ends (the hydrological year of its winter).
    complete : bool
        Every month from October to May has enough days (WMO-No. 1203, 4.4.1 d).
    cover_days : float or None
        Days with snow cover (depth >= 1 cm), scaled per month; ``None`` for a
        winter that is not complete.
    max_depth_cm : float or None
        The largest depth [cm].
    max_date : str or None
        Its (first) day; ``None`` without snow cover.
    first_date, last_date : str or None
        The first and the last day with snow cover.
    fresh_snow_cm : float or None
        Sum of the depths of fresh snow [cm]; ``None`` without its series.
    fresh_snow_days : int or None
        Days with fresh snow.
    """

    year: int
    complete: bool
    cover_days: float | None
    max_depth_cm: float | None
    max_date: str | None
    first_date: str | None
    last_date: str | None
    fresh_snow_cm: float | None
    fresh_snow_days: int | None


@dataclass
class SnowMonth(JsonResultMixin):
    """The mean days with snow cover of one month.

    Attributes
    ----------
    month : int
        Calendar month.
    cover_days : float or None
        Mean of the monthly days with snow cover over the months with enough days.
    """

    month: int
    cover_days: float | None


@dataclass
class SnowPeriod(JsonResultMixin):
    """The snow cover of the complete winters of the period.

    Attributes
    ----------
    n_years : int
        Complete winters.
    skipped_years : list of int
        Winters with a value that are not complete.
    mean_cover_days : float or None
        Mean days with snow cover.
    mean_max_depth_cm : float or None
        Mean of the largest depths [cm].
    max_depth_cm : float or None
        The largest depth [cm].
    max_date : str or None
        Its day.
    median_first_day, median_last_day : str or None
        Median first and last day with snow cover, ``MM-DD``.
    earliest_first_date, latest_last_date : str or None
        The earliest first and the latest last day with snow cover.
    years_without_cover : int
        Winters without a day with snow cover.
    mean_fresh_snow_cm : float or None
        Mean sum of fresh snow [cm].
    mean_fresh_snow_days : float or None
        Mean days with fresh snow.
    months : list of SnowMonth
        The twelve months from August.
    """

    n_years: int
    skipped_years: list[int]
    mean_cover_days: float | None
    mean_max_depth_cm: float | None
    max_depth_cm: float | None
    max_date: str | None
    median_first_day: str | None
    median_last_day: str | None
    earliest_first_date: str | None
    latest_last_date: str | None
    years_without_cover: int
    mean_fresh_snow_cm: float | None
    mean_fresh_snow_days: float | None
    months: list[SnowMonth]


@dataclass
class SnowCover(JsonResultMixin):
    """Snow cover of each winter (M10).

    Attributes
    ----------
    first_year, last_year : int
        First and last winter (snow season named after the year it ends in) with a
        value.
    period_years : int
        Winters with a value.
    years : list of SnowYear
        Every winter with a value.
    period : SnowPeriod
        The means over the complete winters.
    """

    first_year: int
    last_year: int
    period_years: int
    years: list[SnowYear]
    period: SnowPeriod


def _day_of_season(offset: float) -> str:
    """``MM-DD`` of the day ``offset`` days after 1 August (2001-08-01)."""
    day = _REFERENCE_START + np.timedelta64(round(offset), "D")
    return str(day)[5:]


def snow_cover(
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    snow_cover_cm: NDArray[np.float64] | Sequence[float],
    fresh_snow_cm: NDArray[np.float64] | Sequence[float] | None = None,
) -> SnowCover:
    """Days with snow cover, the largest depth, the first and last day of each winter.

    Parameters
    ----------
    dates : array_like of datetime64
        The days, strictly increasing (days may be absent).
    snow_cover_cm : array_like of float
        Depth of the snow cover [cm], 0 without cover; ``NaN`` on a missing day.
    fresh_snow_cm : array_like of float, optional
        Depth of fresh snow [cm].

    Returns
    -------
    SnowCover
        The snow cover of each winter and the means of the complete ones.

    Raises
    ------
    InvalidParameterError
        If an array is empty or of another length, the dates do not increase, a
        depth is negative or no day has a value.
    """
    depth_values = np.asarray(snow_cover_cm, dtype=np.float64)
    days = as_days(dates)
    fresh_values = (
        None if fresh_snow_cm is None else np.asarray(fresh_snow_cm, dtype=np.float64)
    )
    check_daily(days, depth_values, *(() if fresh_values is None else (fresh_values,)))
    for values in (depth_values, fresh_values):
        if values is not None and bool((values[np.isfinite(values)] < 0).any()):
            raise InvalidParameterError("snow depths must not be negative")
    grid = grid_of_values(days, np.isfinite(depth_values), SNOW_SEASON)
    depth = grid.place(days, depth_values)
    fresh = None if fresh_values is None else grid.place(days, fresh_values)
    known = np.isfinite(depth)
    with np.errstate(invalid="ignore"):
        cover_flags = known & (depth >= SNOW_COVER_CM)
    enough = month_quality(grid, known).enough
    scaled = monthly_counts(grid, depth, cover_flags)
    observed = grid.per_month(cover_flags.astype(np.float64))
    present = years_with_values(grid, known)
    season = [grid.months.index(month) for month in SNOW_SEASON_MONTHS]
    starts = grid.year_starts()
    top, top_at = block_extreme(depth, starts)
    rows: list[SnowYear] = []
    offsets: dict[int, tuple[int, int]] = {}
    for row in np.flatnonzero(present).tolist():
        start = int(starts[row])
        stop = int(starts[row + 1]) if row + 1 < starts.size else depth.size
        on = np.flatnonzero(cover_flags[start:stop])
        complete = bool(enough[row, season].all())
        cover_days = (
            float(np.where(enough[row], scaled[row], observed[row]).sum())
            if complete
            else None
        )
        largest = finite(top[row])
        fresh_cm: float | None = None
        fresh_days: int | None = None
        if fresh is not None:
            block = fresh[start:stop]
            have = np.isfinite(block)
            if have.any():
                fresh_cm = float(block[have].sum())
                fresh_days = int((block[have] > 0).sum())
        rows.append(
            SnowYear(
                year=grid.first_year + row,
                complete=complete,
                cover_days=cover_days,
                max_depth_cm=largest,
                max_date=grid.iso(int(top_at[row]))
                if largest is not None and largest > 0
                else None,
                first_date=grid.iso(start + int(on[0])) if on.size else None,
                last_date=grid.iso(start + int(on[-1])) if on.size else None,
                fresh_snow_cm=fresh_cm,
                fresh_snow_days=fresh_days,
            )
        )
        if complete and on.size:
            offsets[grid.first_year + row] = (int(on[0]), int(on[-1]))
    counted = [row for row in rows if row.complete]

    def mean(values: Sequence[float | int | None]) -> float | None:
        numbers = [float(value) for value in values if value is not None]
        return float(np.mean(numbers)) if numbers else None

    record = max(counted, key=lambda row: row.max_depth_cm or 0.0, default=None)
    firsts = [first for first, _ in offsets.values()]
    lasts = [last for _, last in offsets.values()]
    earliest = min(offsets, key=lambda year: offsets[year][0], default=None)
    latest = max(offsets, key=lambda year: offsets[year][1], default=None)
    by_year = {row.year: row for row in rows}
    return SnowCover(
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        years=rows,
        period=SnowPeriod(
            n_years=len(counted),
            skipped_years=[row.year for row in rows if not row.complete],
            mean_cover_days=mean([row.cover_days for row in counted]),
            mean_max_depth_cm=mean([row.max_depth_cm for row in counted]),
            max_depth_cm=record.max_depth_cm if record else None,
            max_date=record.max_date if record else None,
            median_first_day=_day_of_season(float(np.median(firsts)))
            if firsts
            else None,
            median_last_day=_day_of_season(float(np.median(lasts))) if lasts else None,
            earliest_first_date=by_year[earliest].first_date if earliest else None,
            latest_last_date=by_year[latest].last_date if latest else None,
            years_without_cover=sum(1 for row in counted if not row.cover_days),
            mean_fresh_snow_cm=mean([row.fresh_snow_cm for row in counted]),
            mean_fresh_snow_days=mean([row.fresh_snow_days for row in counted]),
            months=[
                SnowMonth(month, mean_of(scaled[:, slot]))
                for slot, month in enumerate(grid.months)
            ],
        ),
    )
