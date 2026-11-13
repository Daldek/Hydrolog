"""Runs of days beyond a level: the threshold level method on a daily calendar.

A daily series is laid on the calendar of its days (:func:`on_daily_calendar`): a day
whose date is absent or whose value is ``NaN`` has no value. A day is *beyond* a level
when it has a value at or above the level (``direction="above"``) or below it
(``"below"``); consecutive days beyond the level form a run, runs parted by fewer
than ``max_gap_days`` days (without a value or not beyond) merge into one event, and
events shorter than ``min_duration_days`` are dropped (:func:`threshold_runs`). The
same rule finds the low-flow sequences of
:meth:`hydrolog.statistics.LowFlowAnalysis.detect_sequences`.

References
----------
Tallaksen, L. M. & van Lanen, H. A. J. (Eds., 2004): Hydrological Drought — Processes
    and Estimation Methods for Streamflow and Groundwater. Elsevier, ch. 5 (the
    threshold level method).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    days_in_hydrological_year,
    hydrological_year,
    on_daily_calendar,
)

__all__ = [
    "ThresholdEvent",
    "ThresholdEventYear",
    "ThresholdEvents",
    "threshold_events",
    "threshold_runs",
]

Direction = Literal["above", "below"]


def threshold_runs(
    beyond: NDArray[np.bool_],
    *,
    min_duration_days: int = 1,
    max_gap_days: int = 0,
) -> tuple[NDArray[np.intp], NDArray[np.intp]]:
    """Find the runs of days beyond a level, merged across short gaps.

    Parameters
    ----------
    beyond : NDArray[np.bool_]
        One flag per calendar day: the day has a value beyond the level.
    min_duration_days : int, optional
        Shortest run kept, in days (gap days inside it included), by default 1.
    max_gap_days : int, optional
        Two runs parted by fewer than this many days merge into one, by default 0
        (no merging).

    Returns
    -------
    tuple of NDArray[np.intp]
        The first and the last day (inclusive) of each run, as positions in
        ``beyond``, in time order.
    """
    flags = np.asarray(beyond, dtype=bool)
    padded = np.concatenate(([False], flags, [False]))
    edges = np.diff(padded.astype(np.int8))
    starts: NDArray[np.intp] = np.flatnonzero(edges == 1)
    ends: NDArray[np.intp] = np.flatnonzero(edges == -1) - 1
    if starts.size > 1 and max_gap_days > 0:
        # A run opens a new event unless the gap before it is shorter than the limit.
        opens = np.concatenate(([True], starts[1:] - ends[:-1] - 1 >= max_gap_days))
        closes = np.concatenate((opens[1:], [True]))
        starts, ends = starts[opens], ends[closes]
    keep = ends - starts + 1 >= min_duration_days
    return starts[keep], ends[keep]


@dataclass
class ThresholdEvent(JsonResultMixin):
    """One event: a run of days beyond the level.

    Attributes
    ----------
    start_date, end_date : str
        First and last day of the event (ISO ``YYYY-MM-DD``, inclusive).
    duration_days : int
        Calendar days from the first to the last, bridged gap days included.
    days_beyond : int
        Days of the event with a value beyond the level.
    missing_days : int
        Days of the event without a value (bridged by ``max_gap_days``).
    peak : float
        The extreme of the event: the largest value above a level, the smallest
        below one.
    peak_date : str
        The first day with the peak value.
    hydrological_year : int
        Hydrological year of the first day.
    open_start, open_end : bool
        The day before the first (after the last) has no value in the series: the
        event may have begun earlier (lasted longer).
    """

    start_date: str
    end_date: str
    duration_days: int
    days_beyond: int
    missing_days: int
    peak: float
    peak_date: str
    hydrological_year: int
    open_start: bool
    open_end: bool


@dataclass
class ThresholdEventYear(JsonResultMixin):
    """Days beyond the level in one hydrological year.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    days_beyond : int
        Days of the year with a value beyond the level.
    n_events : int
        Events that start in the year.
    days_with_data : int
        Days of the year with a value.
    days : int
        Calendar days of the year (365 or 366).
    """

    year: int
    days_beyond: int
    n_events: int
    days_with_data: int
    days: int


@dataclass
class ThresholdEvents(JsonResultMixin):
    """Events and days beyond a level in a daily series.

    Attributes
    ----------
    level : float
        The level, in the unit of the series.
    direction : {"above", "below"}
        ``"above"``: a day is beyond the level when its value is at least ``level``;
        ``"below"``: when its value is below it.
    min_duration_days, max_gap_days : int
        The rules of the events (see :func:`threshold_runs`).
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    n_days : int
        Calendar days from the first to the last date of the series.
    n_missing_days : int
        Days of ``n_days`` without a value.
    days_beyond : int
        Days with a value beyond the level.
    n_events : int
        Number of events.
    max_duration_days : int
        Duration of the longest event; 0 without events.
    events : list of ThresholdEvent
        The events in time order.
    years : list of ThresholdEventYear
        Every hydrological year with a value, in order.
    """

    level: float
    direction: str
    min_duration_days: int
    max_gap_days: int
    first_year: int
    last_year: int
    period_years: int
    n_days: int
    n_missing_days: int
    days_beyond: int
    n_events: int
    max_duration_days: int
    events: list[ThresholdEvent] = field(default_factory=list)
    years: list[ThresholdEventYear] = field(default_factory=list)


def threshold_events(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    level: float,
    direction: Direction = "above",
    min_duration_days: int = 1,
    max_gap_days: int = 0,
) -> ThresholdEvents:
    """Find the events and count the days beyond a level in a daily series.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    level : float
        The level, in the unit of the series.
    direction : {"above", "below"}, optional
        Count the days at or above the level (``"above"``, default) or below it.
    min_duration_days : int, optional
        Shortest event kept [days], at least 1, by default 1.
    max_gap_days : int, optional
        Events parted by fewer days merge, at least 0, by default 0.

    Returns
    -------
    ThresholdEvents
        The events, the days beyond the level per hydrological year and totals.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, ``level`` is not finite,
        ``direction`` is unknown, ``min_duration_days`` is below 1 or
        ``max_gap_days`` below 0, or no day has a value.
    """
    values = np.asarray(values, dtype=np.float64)
    dates = np.asarray(dates).astype("datetime64[D]")
    if values.size == 0 or values.size != dates.size:
        raise InvalidParameterError(
            "values and dates must be non-empty and of the same length"
        )
    if not np.isfinite(level):
        raise InvalidParameterError(f"level must be a finite number, got {level}")
    if direction not in ("above", "below"):
        raise InvalidParameterError(
            f"direction must be 'above' or 'below', got {direction!r}"
        )
    if min_duration_days < 1 or max_gap_days < 0:
        raise InvalidParameterError(
            "min_duration_days must be at least 1 and max_gap_days at least 0"
        )
    calendar, daily = on_daily_calendar(values, dates)
    present = np.isfinite(daily)
    if not present.any():
        raise InvalidParameterError("the series has no value")
    with np.errstate(invalid="ignore"):
        beyond = (daily >= level) if direction == "above" else (daily < level)
    beyond &= present
    starts, ends = threshold_runs(
        beyond, min_duration_days=min_duration_days, max_gap_days=max_gap_days
    )
    years = hydrological_year(calendar)
    last = daily.size - 1
    events: list[ThresholdEvent] = []
    for start, end in zip(starts.tolist(), ends.tolist(), strict=True):
        window = daily[start : end + 1]
        if direction == "above":
            at = int(np.nanargmax(window))
        else:
            at = int(np.nanargmin(window))
        events.append(
            ThresholdEvent(
                start_date=str(calendar[start]),
                end_date=str(calendar[end]),
                duration_days=end - start + 1,
                days_beyond=int(beyond[start : end + 1].sum()),
                missing_days=int((~present[start : end + 1]).sum()),
                peak=float(window[at]),
                peak_date=str(calendar[start + at]),
                hydrological_year=int(years[start]),
                open_start=start == 0 or not bool(present[start - 1]),
                open_end=end == last or not bool(present[end + 1]),
            )
        )
    event_years = years[starts]
    rows: list[ThresholdEventYear] = []
    for year in np.unique(years[present]).tolist():
        mine = years == year
        rows.append(
            ThresholdEventYear(
                year=int(year),
                days_beyond=int(beyond[mine].sum()),
                n_events=int((event_years == year).sum()),
                days_with_data=int(present[mine].sum()),
                days=int(days_in_hydrological_year(np.array([year]))[0]),
            )
        )
    return ThresholdEvents(
        level=float(level),
        direction=direction,
        min_duration_days=int(min_duration_days),
        max_gap_days=int(max_gap_days),
        first_year=rows[0].year,
        last_year=rows[-1].year,
        period_years=len(rows),
        n_days=int(daily.size),
        n_missing_days=int((~present).sum()),
        days_beyond=int(beyond.sum()),
        n_events=len(events),
        max_duration_days=max((event.duration_days for event in events), default=0),
        events=events,
        years=rows,
    )
