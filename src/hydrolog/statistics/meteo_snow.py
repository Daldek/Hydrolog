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
whatever days the winter has. The median first and last day count each date as a
day of the season on a calendar without 29 February (29 February counts as
28 February), so that a date is the same day in every winter. These conventions are
Tier B of Nogat's computation standard (ADR-0059), declared in :data:`TIER_B`
(``SPECS`` is empty) and shown in ``docs/FORMULAS.md``.

References
----------
WMO (2017): WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203,
    sections 4.3 and 4.4.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import Constant, FormulaSpec, Source, TierBSpec
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
    "SPECS",
    "SnowCover",
    "SnowMonth",
    "SnowPeriod",
    "SnowYear",
    "TIER_B",
    "snow_cover",
]

SNOW_COVER_CM = 1.0
"""A day with snow cover has a depth of at least this [cm]."""
SNOW_SEASON_MONTHS: tuple[int, ...] = (10, 11, 12, 1, 2, 3, 4, 5)
"""The months whose data a winter needs: October to May."""
_REFERENCE_START = np.datetime64("2001-08-01", "D")
"""1 August of the snow season 2001/02, which has no 29 February: the calendar on
which the days of the season of the median first and last day are counted."""


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
    incomplete_years : list of int
        Winters with a value that are not complete, left out of these statistics.
    mean_cover_days : float or None
        Mean days with snow cover.
    mean_max_depth_cm : float or None
        Mean of the largest depths [cm].
    max_depth_cm : float or None
        The largest depth [cm].
    max_date : str or None
        Its day.
    median_first_day, median_last_day : str or None
        Median first and last day with snow cover, ``MM-DD``: each date is a day of
        the season counted from 1 August on a calendar without 29 February, which
        counts as 28 February, so a date is the same day in every winter; of an even
        number of winters the mean of the two middle days, rounded half to even.
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
    incomplete_years: list[int]
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


def _season_day(date: str) -> int:
    """Day of the season of an ISO date, 0 on 1 August, on the season 2001/02.

    A month and day is the same day of the season in every year; 29 February counts
    as 28 February.
    """
    month, day = int(date[5:7]), int(date[8:10])
    if (month, day) == (2, 29):
        day = 28
    year = 2001 if month >= 8 else 2002
    return int(
        (np.datetime64(f"{year}-{month:02d}-{day:02d}") - _REFERENCE_START).astype(int)
    )


def _date_of_season(day: float) -> str:
    """``MM-DD`` of day ``day`` of the season 2001/02, rounded half to even."""
    return str(_REFERENCE_START + np.timedelta64(round(day), "D"))[5:]


def _season_order(date: str) -> tuple[int, int]:
    """Months since August and day of an ISO date: its place in any season."""
    return (int(date[5:7]) - 8) % 12, int(date[8:10])


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
    counted = [row for row in rows if row.complete]

    def mean(values: Sequence[float | int | None]) -> float | None:
        numbers = [float(value) for value in values if value is not None]
        return float(np.mean(numbers)) if numbers else None

    record = max(counted, key=lambda row: row.max_depth_cm or 0.0, default=None)
    covered = [
        (row.first_date, row.last_date)
        for row in counted
        if row.first_date is not None and row.last_date is not None
    ]
    firsts = [_season_day(first) for first, _ in covered]
    lasts = [_season_day(last) for _, last in covered]
    earliest = min((first for first, _ in covered), key=_season_order, default=None)
    latest = max((last for _, last in covered), key=_season_order, default=None)
    return SnowCover(
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        years=rows,
        period=SnowPeriod(
            n_years=len(counted),
            incomplete_years=[row.year for row in rows if not row.complete],
            mean_cover_days=mean([row.cover_days for row in counted]),
            mean_max_depth_cm=mean([row.max_depth_cm for row in counted]),
            max_depth_cm=record.max_depth_cm if record else None,
            max_date=record.max_date if record else None,
            median_first_day=_date_of_season(float(np.median(firsts)))
            if firsts
            else None,
            median_last_day=_date_of_season(float(np.median(lasts))) if lasts else None,
            earliest_first_date=earliest,
            latest_last_date=latest,
            years_without_cover=sum(1 for row in counted if not row.cover_days),
            mean_fresh_snow_cm=mean([row.fresh_snow_cm for row in counted]),
            mean_fresh_snow_days=mean([row.fresh_snow_days for row in counted]),
            months=[
                SnowMonth(month, mean_of(scaled[:, slot]))
                for slot, month in enumerate(grid.months)
            ],
        ),
    )


SPECS: Final[tuple[FormulaSpec, ...]] = ()
"""The Tier A formulas of the module: none, its conventions are Tier B."""

_ROCZNIK = Source(
    citation="IMGW-PIB (2023). Rocznik Meteorologiczny 2022",
    locator="p. 5: snow cover, a layer of at least 1 cm covering more than half of the "
    "terrain around the station, measured at 06 UTC",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/"
    "Rocznik%20meteorologiczny/Rocznik%20Meteorologiczny%202022.pdf",
)
_ECAD_SNOW = Source(
    citation="ECA&D (2021). European Climate Assessment & Dataset, Algorithm "
    "Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt",
    locator="section 5.3.9: SD1, snow days (SD >= 1 cm)",
    url="https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf",
)
_URBAN = Source(
    citation="Urban, G. (2015). Przegląd Geograficzny 87(3)",
    locator="pp. 498-499: the snow season from 1 August to 31 July, after Falarz",
    access="author-provided",
)
_WMO_EXTREMES = Source(
    citation="WMO (2017). WMO Guidelines on the Calculation of Climate Normals. "
    "WMO-No. 1203, Geneva",
    locator="section 4.4.1 (b) and (d), pp. 7-8: extremes from whatever days, counts "
    "of months whose mean could be calculated",
    url="https://library.wmo.int/idurl/4/55797",
)

TIER_B: Final = (
    TierBSpec(
        name="snow_cover_day",
        function="hydrolog.statistics.meteo_snow.snow_cover",
        definition="a day with snow cover has a depth of at least 1 cm; the days of a "
        "month are scaled to its days when fewer than 11 days, and fewer than 5 in a "
        "row, are missing; a winter's days are the sum of its months",
        convention="at least 1 cm, as IMGW-PIB's yearbooks and ECA&D's SD1; IMGW-PIB's "
        "normals count > 0 cm (SNIEG_0, the same with whole centimetres) and > 1 cm "
        "(SNIEG_1)",
        source=_ROCZNIK,
        constants=(
            Constant(
                name="snow_cover_cm",
                value=SNOW_COVER_CM,
                unit="cm",
                symbol="1 cm",
                source=_ECAD_SNOW,
            ),
        ),
    ),
    TierBSpec(
        name="snow_season",
        function="hydrolog.statistics.meteo_snow.snow_cover",
        definition="a winter is the snow season 1 August - 31 July named after the "
        "year it ends; it is complete when every month October to May has enough days",
        convention="the whole cold season together: snow of late October starts its "
        "winter (Polish studies also use X-V, XI-III or XII-II)",
        source=_URBAN,
    ),
    TierBSpec(
        name="snow_season_extremes",
        function="hydrolog.statistics.meteo_snow.snow_cover",
        definition="the largest depth with its day, the first and the last day with "
        "snow cover and the sum of the depths of fresh snow of a winter, from whatever "
        "days it has",
        convention="the first of equal largest depths",
        source=_WMO_EXTREMES,
    ),
    TierBSpec(
        name="snow_season_medians",
        function="hydrolog.statistics.meteo_snow.snow_cover",
        definition="the median first and last day with snow cover of the complete "
        "winters: each date a day of the season on a calendar without 29 February, "
        "the median of those days turned back into a date",
        convention="29 February counts as 28 February, so a date is the same day in "
        "every winter; a median between two days is rounded half to even",
        source=_URBAN,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
