"""Runs of days beyond a threshold: the threshold level method on a daily calendar.

A daily series is laid on the calendar of its days (:func:`on_daily_calendar`): a day
whose date is absent or whose value is ``NaN`` has no value. A day is *beyond* the
threshold when it has a value at or above it (``direction="above"``) or below it
(``"below"``); consecutive days beyond the threshold form a run, runs parted by fewer
than ``max_gap_days`` days (without a value or not beyond) merge into one event, and
events shorter than ``min_duration_days`` are dropped (:func:`threshold_runs`). The
same rule finds the low-flow sequences of
:meth:`hydrolog.statistics.LowFlowAnalysis.detect_sequences`.

These are Tier B of Nogat's computation standard (CMP-1.1; ADR-0063): the method
counts days, sums the daily deficits and picks extremes by a calendar definition and
the conventions of its days and gaps (which day is beyond, how runs pool, how long an
event lasts, the year it counts in); it estimates, fits or tests nothing. :data:`TIER_B`
declares them with their sources, the low-flow sequences and their deficit volumes
too; ``docs/FORMULAS.md`` shows them.

Examples
--------
Two runs parted by two days merge when fewer than three days part them:

>>> beyond = np.array([True, True, False, False, True, True, False])
>>> [run.tolist() for run in threshold_runs(beyond, max_gap_days=3)]
[[0], [5]]
>>> [run.tolist() for run in threshold_runs(beyond, max_gap_days=2)]
[[0, 4], [1, 5]]

An event above 5 with its peak, and the days beyond the threshold of its hydrological
year:

>>> days = np.arange(np.datetime64("2021-03-01"), np.datetime64("2021-03-06"))
>>> found = threshold_events([4.0, 6.0, 7.5, 5.0, 2.0], days, threshold=5.0)
>>> event = found.events[0]
>>> (event.start_date, event.duration_days, event.peak, event.peak_date)
('2021-03-02', 3, 7.5, '2021-03-03')
>>> (found.years[0].year, found.years[0].days_beyond)
(2021, 3)

References
----------
Tallaksen, L. M. & van Lanen, H. A. J. (Eds., 2004): Hydrological Drought — Processes
    and Estimation Methods for Streamflow and Groundwater. Elsevier, ch. 5 (the
    threshold level method).
WMO (2008): Manual on Low-flow Estimation and Prediction, WMO-No. 1029, sect. 8.2.
Fleig, A. K., Tallaksen, L. M., Hisdal, H. & Demuth, S. (2006): A global evaluation
    of streamflow drought characteristics. Hydrology and Earth System Sciences 10,
    535-552.
Tokarczyk, T. (2010): Niżówka jako wskaźnik suszy hydrologicznej. Monografie IMGW-PIB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import UNITS, Constant, FormulaSpec, Source, TierBSpec
from hydrolog.statistics._hydrological_year import (
    days_in_hydrological_year,
    hydrological_year,
    on_daily_calendar,
)

__all__ = [
    "SPECS",
    "TIER_B",
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
    """Find the runs of days beyond a threshold, merged across short gaps.

    Parameters
    ----------
    beyond : NDArray[np.bool_]
        One flag per calendar day: the day has a value beyond the threshold.
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
    """One event: a run of days beyond the threshold.

    Attributes
    ----------
    start_date, end_date : str
        First and last day of the event (ISO ``YYYY-MM-DD``, inclusive).
    duration_days : int
        Calendar days from the first to the last, bridged gap days included.
    days_beyond : int
        Days of the event with a value beyond the threshold.
    missing_days : int
        Days of the event without a value (bridged by ``max_gap_days``).
    peak : float
        The extreme of the event: the largest value above the threshold, the
        smallest below it.
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
    """Days beyond the threshold in one hydrological year.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    days_beyond : int
        Days of the year with a value beyond the threshold.
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
    """Events and days beyond a threshold in a daily series.

    Attributes
    ----------
    threshold : float
        The threshold, in the unit of the series.
    direction : {"above", "below"}
        ``"above"``: a day is beyond the threshold when its value is at least
        ``threshold``; ``"below"``: when its value is below it.
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
        Days with a value beyond the threshold.
    n_events : int
        Number of events.
    max_duration_days : int
        Duration of the longest event; 0 without events.
    events : list of ThresholdEvent
        The events in time order.
    years : list of ThresholdEventYear
        Every hydrological year with a value, in order.
    """

    threshold: float
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
    threshold: float,
    direction: Direction = "above",
    min_duration_days: int = 1,
    max_gap_days: int = 0,
) -> ThresholdEvents:
    """Find the events and count the days beyond a threshold in a daily series.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    threshold : float
        The threshold, in the unit of the series.
    direction : {"above", "below"}, optional
        Count the days at or above the threshold (``"above"``, default) or below it.
    min_duration_days : int, optional
        Shortest event kept [days], at least 1, by default 1.
    max_gap_days : int, optional
        Events parted by fewer days merge, at least 0, by default 0.

    Returns
    -------
    ThresholdEvents
        The events, the days beyond the threshold per hydrological year and totals.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase
        strictly, ``threshold`` is not finite, ``direction`` is unknown,
        ``min_duration_days`` is below 1 or ``max_gap_days`` below 0, or no day has a
        value.
    """
    values = np.asarray(values, dtype=np.float64)
    dates = np.asarray(dates).astype("datetime64[D]")
    if values.size == 0 or values.size != dates.size:
        raise InvalidParameterError(
            "values and dates must be non-empty and of the same length"
        )
    if np.any(dates[1:] <= dates[:-1]):
        raise InvalidParameterError("the dates must increase strictly")
    if not np.isfinite(threshold):
        raise InvalidParameterError(
            f"threshold must be a finite number, got {threshold}"
        )
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
        beyond = (daily >= threshold) if direction == "above" else (daily < threshold)
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
        threshold=float(threshold),
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


# --- the Tier B formulas of the threshold level method --------------------------------

_WMO_1029 = (
    "WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, "
    "Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.)"
)
_WMO_1029_URL = "https://library.wmo.int/idurl/4/32176"
_THRESHOLD_LEVEL = Source(
    citation=_WMO_1029,
    locator="sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the "
    "threshold and ends as soon as it returns above it, with its duration, volume, "
    "minimum flow and time of occurrence; the IT method pools deficits that occur "
    "less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 "
    "(eqs. 8.1)",
    url=_WMO_1029_URL,
)
_FLEIG = Source(
    citation="Fleig, A.K., Tallaksen, L.M., Hisdal, H. and Demuth, S. (2006). A global "
    "evaluation of streamflow drought characteristics. Hydrology and Earth System "
    "Sciences 10, 535-552",
    locator="sect. 2.1, p. 539, eqs. (1) and (2): the full duration of a pooled "
    "drought runs from the first day of the first event to the last day of the last, "
    "the excess periods included, and its deficit volume is the sum of the pooled "
    "deficits",
    url="https://hess.copernicus.org/articles/10/535/2006/hess-10-535-2006.pdf",
)
_DAY = Constant(
    name="day",
    value=UNITS["d"].factor,
    unit="s/d",
    symbol=r"\Delta t",
    source=UNITS["d"].source,
)

SPECS: Final[tuple[FormulaSpec, ...]] = ()
"""The module has no Tier A formula (CMP-1.1): see :data:`TIER_B`."""

TIER_B: Final = (
    TierBSpec(
        name="threshold_runs",
        function="hydrolog.statistics.events.threshold_runs",
        definition="the runs of consecutive days flagged beyond a threshold; two runs "
        "parted by fewer than max_gap_days days (without a value or not beyond) merge "
        "into one, with the days between them; runs shorter than min_duration_days, "
        "counted with the days merged in, are dropped; each run is the positions of "
        "its first and last day, inclusive, in time order",
        convention="the pooling of the inter-event time method: runs pool when the "
        "gap is less than t_min = max_gap_days days (WMO-No. 1029, p. 72; lfstat's "
        "pool_it, 'inter-event time is less than tmin'), where Fleig et al. (2006) "
        "write tau_i <= t_c in their formula against 'less than' in their text; "
        "max_gap_days 4 pools gaps of 1 to 3 days, as the program NIŻÓWKA pools low "
        "flows parted by 3 days (Tokarczyk 2010, p. 34) and Tomaszewski (2012, pp. "
        "68-69) breaks of at most 3 days; the duration of a pooled run includes the "
        "gap, the full drought duration of Fleig et al. (2006, eq. 1) and lfstat's "
        "duration, while WMO-No. 1029 (eq. 8.1(a)), NIŻÓWKA (Tokarczyk 2010, p. 34) "
        "and Tomaszewski (2012, fig. 14) add the durations of the runs without the gap "
        "(the real duration, days_beyond of threshold_events); the minimum duration "
        "applies to the full duration after pooling (Fleig et al. apply d_min to the "
        "real one); 0 pools nothing",
        source=_THRESHOLD_LEVEL,
    ),
    TierBSpec(
        name="threshold_events",
        function="hydrolog.statistics.events.threshold_events",
        definition="the series laid on the calendar of its days; a day is beyond the "
        "threshold when its value is >= threshold (above) or < threshold (below); the "
        "events are the threshold_runs of those days; per event its first and last "
        "day, duration in calendar days (the days merged in included), days beyond, "
        "days without a value, peak (the largest value above, the smallest below, "
        "dated by its first day), the hydrological year of its first day and whether "
        "the day before (after) it has no value; per hydrological year with a value "
        "its days beyond, events starting in it, days with a value and calendar days "
        "(365 or 366); the totals of the period",
        convention="a day at the threshold is beyond it above it and not below it; a "
        "day whose date is absent or whose value is NaN or not finite has no value and "
        "is never beyond; an event counts in the hydrological year (1 November - 31 "
        "October, named after the year of its end) in which it starts; the dates "
        "increase strictly",
        source=_THRESHOLD_LEVEL,
    ),
    TierBSpec(
        name="low_flow_sequences",
        function="hydrolog.statistics.low_flows.LowFlowAnalysis.detect_sequences",
        definition="the flows laid on the calendar of their dates; the runs of days "
        "with a value below the threshold T, Q < T (threshold_runs, by default "
        "min_duration_days 5 and max_gap_days 4); per sequence its duration in "
        "calendar days (gap days included), the minimum and the mean of its days with "
        "a value, the deficit sum(max(T - Q, 0)) over its days with a value in the "
        "unit of the series times a day, its days without a value and whether the day "
        "before (after) it has no value; the sum of the deficits, the longest "
        "duration and the number of sequences",
        convention="below is Q < T, as WMO-No. 1029 (p. 71) and the IMGW-PIB glossary "
        "(29, 'niższe od') say, not Q <= T of Yevjevich in Tokarczyk (2010, p. 33) "
        "or of lfstat; the deficit of a pooled sequence is the sum of the deficits of "
        "its runs, the excess of the days between them not subtracted (Fleig et al. "
        "2006, eq. 2; WMO-No. 1029, eq. 8.1(b); lfstat's vbt, while lfstat's volume "
        "subtracts it); a day without a value adds no deficit and is a gap day; the "
        "defaults are NIŻÓWKA's minimum of 5 days and pooling across 3 days "
        "(Tokarczyk 2010, p. 34); any finite threshold, so a stage below its gauge's "
        "zero too",
        source=_FLEIG,
    ),
    TierBSpec(
        name="low_flow_deficit_volumes",
        function="hydrolog.operations.stats.stats_low_flow_sequences",
        definition="the deficit of a discharge series in m3/s as a volume, "
        "deficit_volume_m3 = deficit x 86,400 s/d [m3], of each sequence, of each "
        "hydrological year and of the period; None for a stage (parameter H); a "
        "sequence counts in the hydrological year of its first day, with its whole "
        "duration and deficit",
        convention="the day of 86,400 s (the SI's non-SI day, BIPM 2019, table 8, "
        "from the units table of nogat_formulas): the daily deficits [m3/s] times the "
        "days give m3, the deficit volume of WMO-No. 1029 (sect. 8.3 (c)(iii), 'the "
        "sum of the daily deficit flows multiplied by the duration in days'); "
        "Tokarczyk (2010, p. 34, eq. 1) sums (Q0 - Q_t) Δt with Δt a day",
        source=_THRESHOLD_LEVEL,
        constants=(_DAY,),
    ),
)
"""The Tier B formulas of the module (CMP-2.2), with the low-flow sequences of
:meth:`~hydrolog.statistics.LowFlowAnalysis.detect_sequences` and their volumes in
``stats low-flow-sequences``, which run :func:`threshold_runs`."""
