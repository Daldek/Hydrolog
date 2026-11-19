"""Dry and wet spells of a daily precipitation series.

A *dry* day has precipitation below a threshold, a *wet* day at least the threshold
(1 mm by default: CDD and CWD of the ETCCDI, Zhang et al., 2011). A spell is a run of
consecutive dry (wet) days found by the run logic of ``stats threshold-events``
(:func:`hydrolog.statistics.threshold_runs`; the threshold level method, Tallaksen and
van Lanen, 2004) on the calendar of the series: a day without a value is neither dry
nor wet and ends a spell, which is then *open* (it may have been longer). The length
of the spell ending on each day is the formula :data:`SPELL_LENGTHS` (spec
``spell_lengths``, Nogat's computation standard, ADR-0050 and ADR-0059), which refuses
a negative precipitation; the year a spell counts in and the yearly summaries are its
Tier B (:data:`TIER_B`); ``docs/FORMULAS.md`` shows them.

A spell that crosses the start of a year is not cut there: it counts, whole, in the
year in which it ends, the convention of the ETCCDI's software (fclimdex, and
climdex.pcic with its default ``spells.can.span.years = TRUE``) and of ECA&D (ATBD
version 11, p. 20: "a spell can continue into the next year and is counted against
the year in which the spell ends"). A year that lies wholly inside a spell ending
later has no longest spell (``None``, as in climdex.pcic). The yearly summaries take
the years whose every day has a value, and the distribution of durations the spells
of those years that are not open.

``min_duration_days`` shortens the list of spells only: the yearly and the period
summaries take every spell whatever its duration, since CDD and CWD of the ETCCDI
(Zhang et al., 2011; Klein Tank et al., 2009) are the yearly largest numbers of
consecutive dry (wet) days with no minimum, and a distribution of durations counts
every spell. The default 1 lists every spell.

References
----------
Zhang, X. et al. (2011): Indices for monitoring changes in extremes based on daily
    temperature and precipitation data. WIREs Climate Change 2(6), 851-870.
Klein Tank, A. M. G., Zwiers, F. W. & Zhang, X. (2009): Guidelines on Analysis of
    extremes in a changing climate in support of informed decisions for adaptation.
    WMO-TD No. 1500 (WCDMP-No. 72), WMO, Geneva.
ECA&D (2021): European Climate Assessment & Dataset, Algorithm Theoretical Basis
    Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20.
Bronaugh, D. (2020): climdex.pcic 1.1-11, the ETCCDI indices in R (Pacific Climate
    Impacts Consortium), ``spell.length.max`` and ``climdex.cdd``.
Tallaksen, L. M. & van Lanen, H. A. J. (Eds., 2004): Hydrological Drought. Elsevier,
    ch. 5.

Examples
--------
>>> spell_lengths([0.0, 0.2, 3.1, np.nan, 0.0, 0.0], 1.0, "dry")
array([0., 2., 0., 0., 0., 2.])
>>> days = np.arange(np.datetime64("2001-12-30"), np.datetime64("2002-01-04"))
>>> found = precipitation_spells([0.0, 0.0, 0.0, 5.0, 0.0], days)
>>> [(spell.start_date, spell.duration_days, spell.year) for spell in found.spells]
[('2001-12-30', 3, 2002), ('2002-01-03', 1, 2002)]
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from numbers import Integral
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Conservation,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.statistics._climate import complete_years, precipitation_record
from hydrolog.statistics.events import threshold_runs

__all__ = [
    "DEFAULT_SPELL_THRESHOLD_MM",
    "PrecipitationSpell",
    "PrecipitationSpells",
    "SPECS",
    "SPELL_CLASSES",
    "SPELL_COUNT_DAYS",
    "SPELL_LENGTHS",
    "SpellClass",
    "SpellPeriod",
    "SpellYear",
    "TIER_B",
    "precipitation_spells",
    "spell_lengths",
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
"""The classes of the distribution of durations [days], ``None``: no upper limit."""


# --- the spell ending on each day (spec spell_lengths) --------------------------------

_ETCCDI = Source(
    citation="ETCCDI (2009). Climate Change Indices: definitions of the 27 core "
    "indices. Expert Team on Climate Change Detection and Indices",
    locator="CDD: the largest number of consecutive days with RR < 1 mm; CWD: the "
    "largest number of consecutive days with RR >= 1 mm (RR the daily precipitation)",
    url="https://etccdi.pacificclimate.org/list_27_indices.shtml",
)
_ECAD = Source(
    citation="ECA&D (2021). European Climate Assessment & Dataset, Algorithm "
    "Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt",
    locator="section 5.1, p. 20: a spell can continue into the next year and is "
    "counted against the year in which the spell ends",
    url="https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf",
)
_DAILY_RECORD = (
    "the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January "
    "1966 (WMO Archive of Weather and Climate Extremes)"
)
_WARSZAWA_P = Source(
    citation="Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: "
    "the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020",
    locator="the daily precipitation: 0 to 75.8 mm",
)


def _of_kind(x: Values) -> NDArray[np.bool_]:
    """Return the days of the kind: dry below the threshold, wet at or above it."""
    values = x.array("precipitation_mm")
    threshold = x.real("threshold_mm")
    with np.errstate(invalid="ignore"):
        if x.choice("kind") == "dry":
            return values < threshold
        return values >= threshold


def _spell_lengths(x: Values) -> NDArray[np.float64]:
    starts, ends = threshold_runs(_of_kind(x))
    lengths = np.zeros(x.array("precipitation_mm").size)
    lengths[ends] = ends - starts + 1
    return lengths


def _counted(values: Sequence[float], threshold: float, dry: bool) -> list[float]:
    """Count the spell of each day in a loop over the days: the oracle of the spec."""
    lengths = [0.0] * len(values)
    run = 0
    for day, value in enumerate([*values, math.nan]):
        if not math.isnan(value) and (value < threshold) == dry:
            run += 1
            continue
        if run:
            lengths[day - 1] = float(run)
        run = 0
    return lengths


def _counting_oracle(run: Callable[..., Values]) -> None:
    seeded = np.random.default_rng(20261119).choice(
        [0.0, 0.3, 1.0, 4.2, 17.0, math.nan], size=400
    )
    series = (
        [0.0, 0.0, 2.5, 1.0, 0.0, math.nan, 0.0, 0.9, 1.0, 0.0],
        [math.nan, 1.0, 1.0, math.nan, math.nan, 0.0],
        seeded.tolist(),
    )
    for values in series:
        for kind in ("dry", "wet"):
            for threshold in (0.1, 1.0, 5.0):
                out = run(precipitation_mm=values, threshold_mm=threshold, kind=kind)
                assert_within(
                    out.array("spell_days"),
                    _counted(values, threshold, kind == "dry"),
                    abs=0.0,
                    reason="whole numbers of days, counted exactly both ways",
                )


def _uncounted_days(x: Values, out: Values) -> float:
    """Return the days in the spells less the days of the kind."""
    return float(np.sum(out.array("spell_days"))) - np.count_nonzero(_of_kind(x))


SPELL_LENGTHS: Final = FormulaSpec(
    name="spell_lengths",
    title="The length of the dry or wet spell ending on each day",
    function="hydrolog.statistics.meteo_spells.spell_lengths",
    family="index",
    equation=(
        "a day is dry when P < P0 and wet when P >= P0, a missing day neither; L(t) "
        "= the number of consecutive days of the kind ending on day t when day t is "
        "of the kind and day t + 1 is not, else 0"
    ),
    latex=(
        r"L_t = \begin{cases} t - s + 1 & d_s = \dots = d_t = 1,\ d_{s-1} = d_{t+1} = "
        r"0 \\ 0 & \text{otherwise} \end{cases},\quad d_t = [P_t < P_0]\ "
        r"(\text{dry}),\ [P_t \ge P_0]\ (\text{wet})"
    ),
    variables=(
        Variable(
            name="precipitation_mm",
            symbol="P_t",
            unit="mm",
            kind="real_array",
            description="Daily precipitation of consecutive days; NaN on a missing "
            "day.",
            physical=Range(low=0.0, test_high=1825.0, test_reason=_DAILY_RECORD),
            applicability="unstated",
            typical=Range(low=0.0, high=75.8, source=_WARSZAWA_P),
            gaps_allowed=True,
        ),
        Variable(
            name="threshold_mm",
            symbol="P_0",
            unit="mm",
            description="The least precipitation of a wet day.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1825.0,
                test_reason=_DAILY_RECORD,
            ),
            applicability="unstated",
            typical=Range(low=1.0, high=1.0, source=_ETCCDI),
        ),
        Variable(
            name="kind",
            symbol=r"\text{kind}",
            unit="-",
            kind="choice",
            description="Dry spells (below the threshold) or wet spells (at or above "
            "it).",
            choices=("dry", "wet"),
        ),
    ),
    outputs=(
        Output(
            name="spell_days",
            unit="d",
            kind="real_array",
            symbol="L_t",
            description="The days of the spell ending on each day, 0 on any other day.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(_ETCCDI, _ECAD),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="precipitation_in_another_unit",
                inputs={"precipitation_mm": 1.0, "threshold_mm": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="doubling a float is exact and keeps every comparison with "
                    "the doubled threshold",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="every_day_of_the_kind_once",
                text="the spells hold each day of the kind once: the sum of L is the "
                "number of dry (wet) days",
                residual=_uncounted_days,
                tolerance=Tolerance(
                    abs=0.0, reason="sums of whole numbers below 2**53 are exact"
                ),
            ),
        ),
        limits=(
            Limit(
                name="counting_oracle",
                text="L equals the spells counted day by day in a loop, on hand-made "
                "and seeded series with gaps, both kinds and three thresholds",
                check=_counting_oracle,
            ),
            Limit(
                name="one_spell_of_every_day",
                text="a series of dry days is one spell, its length on its last day",
                inputs={
                    "precipitation_mm": [0.0, 0.0, 0.0],
                    "threshold_mm": 1.0,
                    "kind": "dry",
                },
                expected={"spell_days": [0.0, 0.0, 3.0]},
                tolerance=Tolerance(abs=0.0, reason="whole numbers of days"),
            ),
            Limit(
                name="a_day_at_the_threshold_is_wet",
                text="P = P0 is a wet day, P just below it a dry one",
                inputs={
                    "precipitation_mm": [1.0, 0.99],
                    "threshold_mm": 1.0,
                    "kind": "wet",
                },
                expected={"spell_days": [1.0, 0.0]},
                tolerance=Tolerance(abs=0.0, reason="whole numbers of days"),
                source=_ETCCDI,
            ),
        ),
    ),
    validation="none: a count of days",
    formula_version=1,
    status="oracle only",
    conventions=(
        "a dry day has P < P0 and a wet day P >= P0 (RR < 1 mm and RR >= 1 mm of the "
        "ETCCDI): a day at the threshold is wet",
        "a missing day (NaN) is neither dry nor wet: it ends a spell and has L = 0; "
        "the series function marks such a spell open",
        "the length of a spell stands on its last day, so that the series function "
        "credits each spell whole to the year of its end (Tier B spell_year)",
    ),
    traps={
        "gap_propagation": "type case precipitation_mm-nan_element and limit "
        "counting_oracle: a missing day ends a spell and has 0, never NaN",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="the spells counted day by day in a Python loop (math.isnan "
            "and a running count), not by the edges of runs",
            test="tests/unit/test_formulas_meteo_spells.py (limit counting_oracle)",
        ),
    ),
)


def spell_lengths(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    threshold_mm: float,
    kind: str,
) -> NDArray[np.float64]:
    """Return the length of the dry or wet spell ending on each day, spec spell_lengths.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation of consecutive days [mm]; ``NaN`` on a missing day.
    threshold_mm : float
        The least precipitation of a wet day [mm].
    kind : {"dry", "wet"}
        Dry spells (below the threshold) or wet spells (at or above it).

    Returns
    -------
    numpy.ndarray
        The days of the spell ending on each day [d], zero on any other day.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec, a negative precipitation among them
        (``outside_physical_range``).
    """
    x = checked_inputs(
        SPELL_LENGTHS,
        precipitation_mm=precipitation_mm,
        threshold_mm=threshold_mm,
        kind=kind,
    )
    return checked_outputs(
        SPELL_LENGTHS, {"spell_days": _spell_lengths(x)}, inputs=x
    ).array("spell_days")


@dataclass
class PrecipitationSpell(JsonResultMixin):
    """One spell.

    Attributes
    ----------
    start_date, end_date : str
        Its first and last day (ISO, inclusive).
    duration_days : int
        Its days.
    year : int
        The year in which it counts: the year of its last day.
    open_start, open_end : bool
        The day before the first (after the last) has no value: the spell may have
        begun earlier (lasted longer).
    """

    start_date: str
    end_date: str
    duration_days: int
    year: int
    open_start: bool
    open_end: bool


@dataclass
class SpellYear(JsonResultMixin):
    """The spells that end in one year.

    Attributes
    ----------
    year : int
        The year.
    complete : bool
        Every day of the year has a value; the counts need it.
    n_spells : int or None
        Spells that end in the year.
    max_duration_days : int or None
        The longest of them [days] (0 without one; ``None`` when the year lies wholly
        inside a spell that ends later).
    max_start_date, max_end_date : str or None
        Its first and last day (the first longest).
    spells_10_days, spells_15_days, spells_20_days : int or None
        Spells of at least 10, 15 and 20 days.
    """

    year: int
    complete: bool
    n_spells: int | None
    max_duration_days: int | None
    max_start_date: str | None
    max_end_date: str | None
    spells_10_days: int | None
    spells_15_days: int | None
    spells_20_days: int | None


@dataclass
class SpellClass(JsonResultMixin):
    """One class of the distribution of durations.

    Attributes
    ----------
    min_days : int
        Shortest duration of the class [days].
    max_days : int or None
        Longest duration; ``None``: no limit.
    count : int
        Spells of the complete years, not open, with a duration in the class.
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
    n_years : int
        Years with a value on every day.
    mean_max_duration_days : float or None
        Mean of the yearly longest spell [days].
    mean_spells_10_days, mean_spells_15_days, mean_spells_20_days : float or None
        Mean yearly counts of spells of at least 10, 15 and 20 days.
    mean_n_spells : float or None
        Mean yearly number of spells.
    classes : list of SpellClass
        The distribution of durations (:data:`SPELL_CLASSES`).
    """

    n_years: int
    mean_max_duration_days: float | None
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
    min_duration_days : int
        The shortest spell listed in ``spells`` [days].
    year_type : str
        ``"calendar"`` or ``"hydrological"``.
    first_year, last_year, period_years : int
        The period: first and last year with a value, years with a value.
    n_spells : int
        Spells of the period, of every duration.
    max_duration_days : int
        The longest of them [days] (0 without one).
    spells : list of PrecipitationSpell
        The spells of at least ``min_duration_days``, in time order.
    years : list of SpellYear
        Every year with a value.
    period : SpellPeriod
        Means and the distribution of durations of the complete years.
    """

    kind: str
    threshold_mm: float
    min_duration_days: int
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    n_spells: int
    max_duration_days: int
    spells: list[PrecipitationSpell]
    years: list[SpellYear]
    period: SpellPeriod


def precipitation_spells(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    kind: str = "dry",
    threshold_mm: float = DEFAULT_SPELL_THRESHOLD_MM,
    min_duration_days: int = 1,
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
    min_duration_days : int, optional
        The shortest spell listed in ``spells`` [days], at least 1, by default 1
        (every spell). The yearly and period summaries take every spell.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them: missing days here.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year.

    Returns
    -------
    PrecipitationSpells
        The spells, the yearly summaries and the distribution of durations.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, the dates do not increase, no
        day has a value, a value is negative, ``year_type`` is unknown or
        ``min_duration_days`` is not an integer of at least 1, or the spec
        ``spell_lengths`` refuses ``kind`` or ``threshold_mm``.
    """
    if (
        isinstance(min_duration_days, bool)
        or not isinstance(min_duration_days, Integral)
        or min_duration_days < 1
    ):
        raise InvalidParameterError(
            f"min_duration_days must be an integer of at least 1, "
            f"got {min_duration_days!r}"
        )
    data = precipitation_record(
        precipitation_mm, dates, accumulated, year_type
    ).on_grid()
    grid, daily = data.grid, data.daily
    lengths = spell_lengths(daily, threshold_mm, kind)
    ends = np.flatnonzero(lengths)
    starts = ends - lengths[ends].astype(np.intp) + 1
    present_days = np.isfinite(daily)
    last = daily.size - 1
    spells = [
        PrecipitationSpell(
            start_date=str(grid.dates[start]),
            end_date=str(grid.dates[end]),
            duration_days=end - start + 1,
            year=int(grid.year[end]),
            open_start=start == 0 or not bool(present_days[start - 1]),
            open_end=end == last or not bool(present_days[end + 1]),
        )
        for start, end in zip(starts.tolist(), ends.tolist(), strict=True)
    ]
    durations = np.array([spell.duration_days for spell in spells], dtype=np.int64)
    spell_years = np.array([spell.year for spell in spells], dtype=np.int64)
    closed = np.array(
        [not (spell.open_start or spell.open_end) for spell in spells], dtype=bool
    )
    present = data.present
    complete = complete_years(grid, present_days)
    edges = np.zeros(daily.size + 1, dtype=np.int64)
    edges[starts] += 1
    edges[ends + 1] -= 1
    of_kind = np.cumsum(edges[:-1])
    inside = np.minimum.reduceat(of_kind, grid.year_starts()) > 0
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
        mine_durations = durations[mine]
        if mine.size:
            longest = spells[int(mine[int(np.argmax(mine_durations))])]
            max_days: int | None = longest.duration_days
            max_start: str | None = longest.start_date
            max_end: str | None = longest.end_date
        else:
            max_days, max_start, max_end = (None if inside[row] else 0), None, None
        counts = [int((mine_durations >= limit).sum()) for limit in SPELL_COUNT_DAYS]
        rows.append(
            SpellYear(
                year=year,
                complete=True,
                n_spells=int(mine.size),
                max_duration_days=max_days,
                max_start_date=max_start,
                max_end_date=max_end,
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
        hit = full & (durations >= low)
        if high is not None:
            hit &= durations <= high
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
        min_duration_days=int(min_duration_days),
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        n_spells=len(spells),
        max_duration_days=int(durations.max()) if durations.size else 0,
        spells=[spell for spell in spells if spell.duration_days >= min_duration_days],
        years=rows,
        period=SpellPeriod(
            n_years=n_complete,
            mean_max_duration_days=mean([row.max_duration_days for row in counted]),
            mean_spells_10_days=mean([row.spells_10_days for row in counted]),
            mean_spells_15_days=mean([row.spells_15_days for row in counted]),
            mean_spells_20_days=mean([row.spells_20_days for row in counted]),
            mean_n_spells=mean([row.n_spells for row in counted]),
            classes=classes,
        ),
    )


SPECS: Final = (SPELL_LENGTHS,)
"""The Tier A formulas of the module."""

TIER_B: Final = (
    TierBSpec(
        name="spell_year",
        function="hydrolog.statistics.meteo_spells.precipitation_spells",
        definition="a spell (spell_lengths) counts, whole, in the year of its last "
        "day: a spell over the start of a year is not cut, and a year wholly inside a "
        "spell that ends later has no longest spell",
        convention="the year of the spell's end, as climdex.pcic 1.1-11 (its default "
        "spells.can.span.years = TRUE) and ECA&D; the ETCCDI's definition read "
        "literally cuts a spell at the start of the year (ADR-0044)",
        source=_ECAD,
    ),
    TierBSpec(
        name="spell_summaries",
        function="hydrolog.statistics.meteo_spells.precipitation_spells",
        definition="per year with a value on every day: the spells that end in it, the "
        "longest of them (CDD, CWD) with its days, and the spells of at least 10, 15 "
        "and 20 days; per period: their means over those years and the distribution "
        "of the durations of their spells that are not open, per year",
        convention="a year needs every day (climdex.pcic accepts up to 15 missing "
        "days); an open spell, beside a missing day or an end of the series, is left "
        "out of the distribution of durations only; min_duration_days shortens the "
        "list of spells, not the summaries",
        source=_ETCCDI,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
