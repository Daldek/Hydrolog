"""Baseflow separation by the Lyne and Hollick filter and the recession constant.

The one-parameter recursive digital filter of Lyne and Hollick (1979) splits the
daily flow Q into quickflow and baseflow:

    qₜ = α qₜ₋₁ + (1 + α)/2 (Qₜ − Qₜ₋₁),   bₜ = Qₜ − qₜ when qₜ > 0, else Qₜ,

passed forward, backward and forward over the series (Nathan and McMahon, 1990), each
pass filtering the baseflow of the one before. The filter follows the standard
approach of Ladson et al. (2013) and their published code: α = 0.925, three passes,
the series reflected by 30 days at each end so that the passes start outside it, the
quickflow of each pass starting at the first value of its input and kept as it is
(negative too) for the next step, and the baseflow below 0 set to 0 at the end. A
daily series with gaps is filtered on each gapless span of at least 60 days; the
baseflow index is BFI = Σ b / Σ Q over the days filtered.

The recession constant k is the median of the daily ratios Qₜ₊₁ / Qₜ on the recession
segments of the series, runs of at least 5 consecutive days of falling flow (Tallaksen,
1995); the half-life of a recession is ln 2 / (−ln k) days.

References
----------
Lyne, V. & Hollick, M. (1979): Stochastic time-variable rainfall-runoff modelling.
    Hydrology and Water Resources Symposium, Institution of Engineers Australia, Perth.
Nathan, R. J. & McMahon, T. A. (1990): Evaluation of automated techniques for base
    flow and recession analyses. Water Resources Research, 26(7), 1465–1473.
Ladson, A. R., Brown, R., Neal, B. & Nathan, R. (2013): A standard approach to baseflow
    separation using the Lyne and Hollick filter. Australasian Journal of Water
    Resources, 17(1), 25–34; code: github.com/TonyLadson/BaseflowSeparation_LyneHollick.
Tallaksen, L. M. (1995): A review of baseflow recession analysis. Journal of
    Hydrology, 165, 349–370.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.signal import lfilter

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    days_in_hydrological_year,
    hydrological_year,
    hydrological_year_start,
    on_daily_calendar,
)

__all__ = [
    "BASEFLOW_ALPHA",
    "BASEFLOW_PASSES",
    "MIN_RECESSION_DAYS",
    "MIN_SPAN_DAYS",
    "MIN_YEAR_DAYS",
    "REFLECTED_DAYS",
    "BaseflowSeparation",
    "BaseflowYear",
    "RecessionConstant",
    "baseflow_separation",
    "lyne_hollick_filter",
    "recession_constant",
]

BASEFLOW_ALPHA = 0.925
"""Filter parameter α of Nathan and McMahon (1990) for daily flows."""
BASEFLOW_PASSES = 3
"""Passes of the filter: forward, backward, forward."""
REFLECTED_DAYS = 30
"""Days reflected at each end of a span (Ladson et al., 2013)."""
MIN_SPAN_DAYS = 60
"""Shortest gapless span of days that is filtered."""
MIN_YEAR_DAYS = 300
"""Days with a baseflow that a hydrological year needs for an index of its own."""
MIN_RECESSION_DAYS = 5
"""Shortest recession segment: days of falling flow in a row."""


@dataclass
class BaseflowYear(JsonResultMixin):
    """The baseflow of one hydrological year.

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    bfi : float
        Baseflow index Σ b / Σ Q of its days with a baseflow.
    days : int
        Days with a baseflow.
    baseflow_mean, discharge_mean : float
        Mean baseflow and mean discharge of those days [m³/s].
    """

    year: int
    bfi: float
    days: int
    baseflow_mean: float
    discharge_mean: float


@dataclass
class RecessionConstant(JsonResultMixin):
    """The recession constant of a daily series.

    Attributes
    ----------
    k : float or None
        Median ratio Qₜ₊₁ / Qₜ over the recession segments; ``None`` without one.
    half_life_days : float or None
        ln 2 / (−ln k): the days in which a recession halves the flow.
    segments : int
        Recession segments found.
    """

    k: float | None
    half_life_days: float | None
    segments: int


@dataclass
class BaseflowSeparation(JsonResultMixin):
    """Baseflow of a daily discharge series by the Lyne and Hollick filter.

    Attributes
    ----------
    alpha : float
        The filter parameter.
    passes : int
        Passes of the filter.
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    bfi : float
        Baseflow index Σ b / Σ Q over the days with a baseflow.
    days : int
        Days with a baseflow: those of the gapless spans of at least 60 days.
    spans : int
        Gapless spans filtered.
    years : list of BaseflowYear
        Each year with at least :data:`MIN_YEAR_DAYS` days with a baseflow.
    recession : RecessionConstant
        The recession constant of the period.
    series_year : int
        Hydrological year of ``series_dates`` and ``series_baseflow``.
    series_dates : list of str
        Every day of ``series_year`` (ISO dates).
    series_baseflow : list of float or None
        The baseflow of each of those days [m³/s]; ``None`` without one.
    """

    alpha: float
    passes: int
    first_year: int
    last_year: int
    period_years: int
    bfi: float
    days: int
    spans: int
    years: list[BaseflowYear]
    recession: RecessionConstant
    series_year: int
    series_dates: list[str] = field(default_factory=list)
    series_baseflow: list[float | None] = field(default_factory=list)


def _check_filter(alpha: float, passes: int) -> None:
    if not (math.isfinite(alpha) and 0.0 < alpha < 1.0):
        raise InvalidParameterError(f"alpha must be in (0, 1), got {alpha!r}")
    if isinstance(passes, bool) or passes < 3 or passes % 2 == 0:
        raise InvalidParameterError(
            f"passes must be an odd number of at least 3, got {passes!r}"
        )


def _pass(series: NDArray[np.float64], alpha: float) -> NDArray[np.float64]:
    """One forward pass: the baseflow of ``series`` (Ladson et al., 2013)."""
    # q₀ = Q₀; qₜ = α qₜ₋₁ + (1 + α)/2 (Qₜ − Qₜ₋₁): a linear recursion, unclamped.
    quick = np.empty_like(series)
    quick[0] = series[0]
    quick[1:] = lfilter(
        [(1.0 + alpha) / 2.0], [1.0, -alpha], np.diff(series), zi=[alpha * series[0]]
    )[0]
    base: NDArray[np.float64] = np.where(quick > 0, series - quick, series)
    return base


def lyne_hollick_filter(
    discharge: NDArray[np.float64],
    *,
    alpha: float = BASEFLOW_ALPHA,
    passes: int = BASEFLOW_PASSES,
) -> NDArray[np.float64]:
    """Filter the baseflow of a gapless daily discharge series.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily discharge [m³/s], every value known; more than
        :data:`REFLECTED_DAYS` days.
    alpha : float, optional
        Filter parameter in (0, 1), by default 0.925.
    passes : int, optional
        Odd number of passes, at least 3, by default 3.

    Returns
    -------
    NDArray[np.float64]
        The baseflow of each day [m³/s], at least 0.

    Raises
    ------
    InvalidParameterError
        If a value is not finite, the series is too short, ``alpha`` is outside
        (0, 1) or ``passes`` is not an odd number of at least 3.
    """
    _check_filter(alpha, passes)
    flows = np.asarray(discharge, dtype=np.float64)
    n = flows.size
    if n <= REFLECTED_DAYS or not np.isfinite(flows).all():
        raise InvalidParameterError(
            f"the filter needs more than {REFLECTED_DAYS} known values in a row"
        )
    # Q₃₀ … Q₁, Q₀ … Qₙ₋₁, Qₙ₋₂ … Qₙ₋₃₁: the reflection leaves out the end values.
    head = flows[np.arange(REFLECTED_DAYS, 0, -1)]
    tail = flows[np.arange(n - 2, n - 2 - REFLECTED_DAYS, -1)]
    base = _pass(np.concatenate((head, flows, tail)), alpha)
    for _ in range((passes - 1) // 2):
        base = _pass(base[::-1], alpha)[::-1]
        base = _pass(base, alpha)
    out: NDArray[np.float64] = np.maximum(
        base[REFLECTED_DAYS : REFLECTED_DAYS + n], 0.0
    )
    return out


def recession_constant(
    discharge: NDArray[np.float64], *, min_days: int = MIN_RECESSION_DAYS
) -> RecessionConstant:
    """Compute the recession constant of a daily discharge series.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily discharge on a calendar of consecutive days; ``NaN`` marks a day
        without a value, which ends a segment.
    min_days : int, optional
        Shortest segment: days of falling flow in a row, by default 5.

    Returns
    -------
    RecessionConstant
        The median ratio Qₜ₊₁ / Qₜ of the segments, the half-life and the number of
        segments.
    """
    flows = np.asarray(discharge, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = flows[1:] / flows[:-1]
        falling = np.isfinite(ratio) & (ratio < 1.0) & (flows[:-1] > 0)
    padded = np.concatenate(([False], falling, [False]))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    picked = [
        ratio[s:e] for s, e in zip(starts, ends, strict=True) if e - s >= min_days
    ]
    if not picked:
        return RecessionConstant(k=None, half_life_days=None, segments=0)
    k = float(np.median(np.concatenate(picked)))
    half_life = math.log(2.0) / -math.log(k) if 0.0 < k < 1.0 else None
    return RecessionConstant(k=k, half_life_days=half_life, segments=len(picked))


def baseflow_separation(
    discharge: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    alpha: float = BASEFLOW_ALPHA,
    passes: int = BASEFLOW_PASSES,
    series_year: int | None = None,
) -> BaseflowSeparation:
    """Separate the baseflow of a daily discharge series.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily discharge [m³/s]; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    alpha : float, optional
        Filter parameter in (0, 1), by default 0.925.
    passes : int, optional
        Odd number of passes, at least 3, by default 3.
    series_year : int, optional
        Hydrological year of the daily baseflow in the result; by default the last
        complete year (every day with a value), or the last year with a baseflow.

    Returns
    -------
    BaseflowSeparation
        The baseflow index of the period and of its years, the recession constant
        and the daily baseflow of ``series_year``.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, ``alpha`` or ``passes`` is out
        of range, no gapless span has :data:`MIN_SPAN_DAYS` days or ``series_year``
        has no value.
    """
    _check_filter(alpha, passes)
    flows = np.asarray(discharge, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    if flows.size == 0 or flows.size != days.size:
        raise InvalidParameterError(
            "discharge and dates must be non-empty and of the same length"
        )
    calendar, daily = on_daily_calendar(flows, days)
    known = np.isfinite(daily)
    padded = np.concatenate(([False], known, [False]))
    edges = np.diff(padded.astype(np.int8))
    base = np.full(daily.shape, np.nan)
    spans = 0
    for start, end in zip(
        np.flatnonzero(edges == 1), np.flatnonzero(edges == -1), strict=True
    ):
        if end - start >= MIN_SPAN_DAYS:
            base[start:end] = lyne_hollick_filter(
                daily[start:end], alpha=alpha, passes=passes
            )
            spans += 1
    if spans == 0:
        raise InvalidParameterError(
            f"No gapless span of at least {MIN_SPAN_DAYS} days to filter"
        )
    filtered = np.isfinite(base)
    year_of_day = hydrological_year(calendar)
    present = np.unique(year_of_day[known])
    rows: list[BaseflowYear] = []
    complete: list[int] = []
    for year in present.tolist():
        in_year = year_of_day == year
        mine = in_year & filtered
        count = int(mine.sum())
        length = int(days_in_hydrological_year(np.array([year]))[0])
        if int((in_year & known).sum()) == length:
            complete.append(int(year))
        if count < MIN_YEAR_DAYS:
            continue
        rows.append(
            BaseflowYear(
                year=int(year),
                bfi=float(base[mine].sum() / daily[mine].sum()),
                days=count,
                baseflow_mean=float(base[mine].mean()),
                discharge_mean=float(daily[mine].mean()),
            )
        )
    if series_year is None:
        with_base = np.unique(year_of_day[filtered])
        series_year = complete[-1] if complete else int(with_base[-1])
    elif series_year not in set(present.tolist()):
        raise InvalidParameterError(
            f"series_year {series_year} has no value in the series"
        )
    first_day = hydrological_year_start(series_year)
    length = int(days_in_hydrological_year(np.array([series_year]))[0])
    year_days = first_day + np.arange(length)
    year_base = np.full(length, np.nan)
    inside = (calendar >= year_days[0]) & (calendar <= year_days[-1])
    year_base[(calendar[inside] - first_day).astype(np.int64)] = base[inside]
    return BaseflowSeparation(
        alpha=float(alpha),
        passes=int(passes),
        first_year=int(present[0]),
        last_year=int(present[-1]),
        period_years=int(present.size),
        bfi=float(base[filtered].sum() / daily[filtered].sum()),
        days=int(filtered.sum()),
        spans=spans,
        years=rows,
        recession=recession_constant(daily),
        series_year=int(series_year),
        series_dates=[str(day) for day in year_days],
        series_baseflow=[
            float(value) if np.isfinite(value) else None for value in year_base
        ],
    )
