"""Dry and wet spells of a daily precipitation series.

A *dry* day has precipitation below a threshold, a *wet* day at least the threshold
(1 mm by default: CDD and CWD of the ETCCDI, Zhang et al., 2011). A spell is a run of
consecutive dry (wet) days found by the run logic of ``stats threshold-events``
(:func:`hydrolog.statistics.threshold_runs`; the threshold level method, Tallaksen and
van Lanen, 2004) on the calendar of the series: a day without a value is neither dry
nor wet and ends a spell, which is then *open* (it may have been longer). A spell
counts in the year in which it starts; the yearly summaries take the years whose
every day has a value, and the distribution of lengths the spells of those years
that are not open.

References
----------
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Tallaksen, L. M. & van Lanen, H. A. J. (Eds., 2004): Hydrological Drought. Elsevier,
    ch. 5.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._climate import (
    as_days,
    check_daily,
    check_year_type,
    complete_years,
    grid_of_values,
    years_with_values,
)
from hydrolog.statistics.events import threshold_runs

__all__ = [
    "DEFAULT_SPELL_THRESHOLD_MM",
    "PrecipitationSpell",
    "PrecipitationSpells",
    "SPELL_CLASSES",
    "SPELL_COUNT_DAYS",
    "SpellClass",
    "SpellPeriod",
    "SpellYear",
    "precipitation_spells",
]

DEFAULT_SPELL_THRESHOLD_MM = 1.0
"""Dry days have less, wet days at least this precipitation [mm] (ETCCDI)."""
SPELL_COUNT_DAYS: tuple[int, ...] = (10, 15, 20)
"""The yearly counts of spells of at least this many days (Nogat's plan, M6)."""
SPELL_CLASSES: tuple[tuple[int, int | None], ...] = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 5),
    (6, 10),
    (11, 15),
    (16, 20),
    (21, 30),
    (31, None),
)
"""The classes of the distribution of lengths [days], ``None``: no upper limit."""


@dataclass
class PrecipitationSpell(JsonResultMixin):
    """One spell.

    Attributes
    ----------
    start_date, end_date : str
        Its first and last day (ISO, inclusive).
    length_days : int
        Its days.
    year : int
        The year of its first day.
    open_start, open_end : bool
        The day before the first (after the last) has no value: the spell may have
        begun earlier (lasted longer).
    """

    start_date: str
    end_date: str
    length_days: int
    year: int
    open_start: bool
    open_end: bool


@dataclass
class SpellYear(JsonResultMixin):
    """The spells that start in one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a value; the counts need it.
    n_spells : int or None
        Spells that start in the year.
    longest_days : int or None
        The longest of them (0 without one).
    longest_start_date, longest_end_date : str or None
        Its first and last day (the first longest).
    spells_10_days, spells_15_days, spells_20_days : int or None
        Spells of at least 10, 15 and 20 days.
    """

    year: int
    complete: bool
    n_spells: int | None
    longest_days: int | None
    longest_start_date: str | None
    longest_end_date: str | None
    spells_10_days: int | None
    spells_15_days: int | None
    spells_20_days: int | None


@dataclass
class SpellClass(JsonResultMixin):
    """One class of the distribution of lengths.

    Attributes
    ----------
    min_days : int
        Shortest length of the class [days].
    max_days : int or None
        Longest length; ``None``: no limit.
    count : int
        Spells of the complete years, not open, with a length in the class.
    per_year : float or None
        ``count`` over the complete years.
    """

    min_days: int
    max_days: int | None
    count: int
    per_year: float | None


@dataclass
class SpellPeriod(JsonResultMixin):
    """The spells of the complete years of the period.

    Attributes
    ----------
    complete_years : int
        Years with a value on every day.
    mean_longest_days : float or None
        Mean of the yearly longest spell [days].
    mean_spells_10_days, mean_spells_15_days, mean_spells_20_days : float or None
        Mean yearly counts of spells of at least 10, 15 and 20 days.
    mean_n_spells : float or None
        Mean yearly number of spells.
    classes : list of SpellClass
        The distribution of lengths (:data:`SPELL_CLASSES`).
    """

    complete_years: int
    mean_longest_days: float | None
    mean_spells_10_days: float | None
    mean_spells_15_days: float | None
    mean_spells_20_days: float | None
    mean_n_spells: float | None
    classes: list[SpellClass]


@dataclass
class PrecipitationSpells(JsonResultMixin):
    """Dry or wet spells of a daily precipitation series (M6).

    Attributes
    ----------
    kind : str
        ``"dry"`` (P below the threshold) or ``"wet"`` (P at or above it).
    threshold_mm : float
        The threshold [mm].
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period: first and last year with a value, years with a value.
    n_spells : int
        Spells of the period.
    max_length_days : int
        The longest of them (0 without one).
    spells : list of PrecipitationSpell
        Every spell, in time order.
    years : list of SpellYear
        Every year with a value.
    period : SpellPeriod
        Means and the distribution of lengths of the complete years.
    """

    kind: str
    threshold_mm: float
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    n_spells: int
    max_length_days: int
    spells: list[PrecipitationSpell]
    years: list[SpellYear]
    period: SpellPeriod


def precipitation_spells(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    kind: str = "dry",
    threshold_mm: float = DEFAULT_SPELL_THRESHOLD_MM,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> PrecipitationSpells:
    """Find the dry or wet spells of a daily precipitation series (M6).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    kind : {"dry", "wet"}, optional
        Dry spells (P < ``threshold_mm``, default) or wet spells (P >= it).
    threshold_mm : float, optional
        The threshold [mm], positive, by default 1.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them: missing days here.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationSpells
        The spells, the yearly summaries and the distribution of lengths.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase, no
        day has a value, ``kind`` or ``year_type`` is unknown or ``threshold_mm`` is
        not positive.
    """
    if kind not in ("dry", "wet"):
        raise InvalidParameterError(f"kind must be 'dry' or 'wet', got {kind!r}")
    if not (math.isfinite(threshold_mm) and threshold_mm > 0):
        raise InvalidParameterError(
            f"threshold_mm must be a positive number, got {threshold_mm!r}"
        )
    check_year_type(year_type)
    values = np.asarray(precipitation_mm, dtype=np.float64)
    days = as_days(dates)
    check_daily(days, values)
    if accumulated is not None:
        flags = np.asarray(accumulated, dtype=bool)
        if flags.size != values.size:
            raise InvalidParameterError("accumulated must have one flag per value")
        values = np.where(flags, np.nan, values)
    grid = grid_of_values(
        days, np.isfinite(np.asarray(precipitation_mm, float)), year_type
    )
    daily = grid.place(days, values)
    present_days = np.isfinite(daily)
    with np.errstate(invalid="ignore"):
        condition = daily < threshold_mm if kind == "dry" else daily >= threshold_mm
    starts, ends = threshold_runs(condition & present_days)
    last = daily.size - 1
    spells = [
        PrecipitationSpell(
            start_date=str(grid.dates[start]),
            end_date=str(grid.dates[end]),
            length_days=end - start + 1,
            year=int(grid.year[start]),
            open_start=start == 0 or not bool(present_days[start - 1]),
            open_end=end == last or not bool(present_days[end + 1]),
        )
        for start, end in zip(starts.tolist(), ends.tolist(), strict=True)
    ]
    lengths = np.array([spell.length_days for spell in spells], dtype=np.int64)
    spell_years = np.array([spell.year for spell in spells], dtype=np.int64)
    closed = np.array(
        [not (spell.open_start or spell.open_end) for spell in spells], dtype=bool
    )
    present = years_with_values(
        grid, np.isfinite(grid.place(days, np.asarray(precipitation_mm, float)))
    )
    complete = complete_years(grid, present_days)
    rows: list[SpellYear] = []
    complete_labels: list[int] = []
    for row in np.flatnonzero(present).tolist():
        year = grid.first_year + row
        if not complete[row]:
            rows.append(
                SpellYear(year, False, None, None, None, None, None, None, None)
            )
            continue
        complete_labels.append(year)
        mine = np.flatnonzero(spell_years == year)
        mine_lengths = lengths[mine]
        if mine.size:
            first_longest = int(mine[int(np.argmax(mine_lengths))])
            longest = spells[first_longest]
            longest_days = longest.length_days
            longest_start: str | None = longest.start_date
            longest_end: str | None = longest.end_date
        else:
            longest_days, longest_start, longest_end = 0, None, None
        counts = [int((mine_lengths >= limit).sum()) for limit in SPELL_COUNT_DAYS]
        rows.append(
            SpellYear(
                year=year,
                complete=True,
                n_spells=int(mine.size),
                longest_days=longest_days,
                longest_start_date=longest_start,
                longest_end_date=longest_end,
                spells_10_days=counts[0],
                spells_15_days=counts[1],
                spells_20_days=counts[2],
            )
        )
    in_complete = np.isin(spell_years, complete_labels)
    full = in_complete & closed
    n_complete = len(complete_labels)
    classes = []
    for low, high in SPELL_CLASSES:
        hit = full & (lengths >= low)
        if high is not None:
            hit &= lengths <= high
        count = int(hit.sum())
        classes.append(
            SpellClass(low, high, count, count / n_complete if n_complete else None)
        )
    counted = [row for row in rows if row.complete]

    def mean(values: list[int | None]) -> float | None:
        numbers = [value for value in values if value is not None]
        return float(np.mean(numbers)) if numbers else None

    return PrecipitationSpells(
        kind=kind,
        threshold_mm=float(threshold_mm),
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        n_spells=len(spells),
        max_length_days=int(lengths.max()) if lengths.size else 0,
        spells=spells,
        years=rows,
        period=SpellPeriod(
            complete_years=n_complete,
            mean_longest_days=mean([row.longest_days for row in counted]),
            mean_spells_10_days=mean([row.spells_10_days for row in counted]),
            mean_spells_15_days=mean([row.spells_15_days for row in counted]),
            mean_spells_20_days=mean([row.spells_20_days for row in counted]),
            mean_n_spells=mean([row.n_spells for row in counted]),
            classes=classes,
        ),
    )
