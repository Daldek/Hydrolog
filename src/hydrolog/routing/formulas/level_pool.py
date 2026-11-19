r"""Level-pool routing by storage indication, declared by the spec ``level_pool``.

:data:`LEVEL_POOL` declares the routing of a hydrograph through ``N`` equal pools in
series on a given time step, each holding ``S / N`` of a storage-outflow table for the
same outflow (the modified Puls method): continuity by the trapezoid rule,

.. math::
    \frac{s_2}{\Delta t} + \frac{O_2}{2}
    = \frac{I_1 + I_2}{2} + \frac{s_1}{\Delta t} - \frac{O_1}{2},
    \qquad s = \frac{S(O)}{N},

and the outflow of the new step read from the *working curve* ``s / dt + O / 2`` of the
table, linear between its rows (NEH 630 chapter 17, eq. 17-3; HEC-HMS "Modified Puls",
eq. 3; EM 1110-2-1417, eq. 9-12). :func:`level_pool_route` computes it.
:class:`~hydrolog.routing.LevelPoolReach` chooses the sub-steps of a time step, extends
the time axis and reads the stage (ADR-0008), then routes through it.
``docs/FORMULAS.md`` shows the equation, the ranges and the sources (ADR-0061).

The table is a polyline whose rows rise in storage and in outflow; a dead zone,
storage without outflow below a crest, is allowed, and a pool at rest with an outflow
sits at the highest storage the table gives it (full to the crest). Only differences
of storage enter the outflow, so the datum of the storage column is free; the storages
the run reports are measured from it. The spec refuses what it cannot route: a time
step longer than ``2 min(dS/dO) / N`` on the segments of the table the run can reach
(the outflow would overshoot, :func:`step_limit_s`), an initial outflow outside the
table, and a flood that fills a pool beyond the last row or empties it below the first
(:func:`table_exit`), never an extrapolation.

Examples
--------
NEH 630 chapter 17, example 17-1: a channel reach whose storage is given in ft3/s-h,
routed at a step of 0.5 h, its flows in ft3/s (the scheme is homogeneous in the
discharge and the storage, so the outflow comes out in ft3/s):

>>> from hydrolog.nogat_formulas import convert
>>> rating = [0, 50, 150, 300, 800, 1500, 3500, 5000, 7000, 10000]
>>> held = [0.0, 71.8, 136.9, 246.9, 650.7, 1300.0, 3302.8, 4537.5, 5611.1, 7131.9]
>>> storage = [convert(volume, "h", "s") for volume in held]
>>> run = level_pool_route([0, 1250, 2500, 3750, 5000], 30.0, storage, rating, 1, 0.0)
>>> run.outflow_m3s.round().tolist()
[0.0, 290.0, 1016.0, 1887.0, 2881.0]
"""

from __future__ import annotations

import math
import weakref
from bisect import bisect_right
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
    Conservation,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)
from hydrolog.routing.formulas._shared import (
    DISCHARGE,
    ROUTING_TESTS,
    SECONDS_PER_MINUTE,
    STORAGE,
    em_1110_2_1417,
    hec_hms,
    inflow,
    initial_outflow,
    neh630_17,
    outflow,
    storage,
    timestep,
    volume_m3,
)
from hydrolog.routing.formulas.muskingum import muskingum_route

__all__ = [
    "LEVEL_POOL",
    "ROUNDING",
    "SPECS",
    "LevelPoolRoute",
    "TableExit",
    "level_pool_route",
    "step_limit_s",
    "table_exit",
]

ROUNDING: Final = 1e-9
"""Relative slack of the step rule and of the ends of the table: rounding, not data
(:class:`~hydrolog.routing.LevelPoolReach` plans its sub-steps and checks its initial
outflow with it too)."""

_SMALLEST_NORMAL: Final = float(np.finfo(np.float64).smallest_normal)
"""The smallest float64 with all its digits: the balance holds to it (_volume_kept)."""


@dataclass(frozen=True)
class LevelPoolRoute:
    """A hydrograph routed by the spec ``level_pool``.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow of the last pool at every inflow ordinate [m3/s].
    storage_m3 : numpy.ndarray
        Water held by all pools at every ordinate [m3].
    last_pool_storage_m3 : numpy.ndarray
        Water held by the last pool at every ordinate [m3]: all of it when ``N = 1``.
    storage_peak_m3 : float
        The largest water held by all pools [m3].
    storage_steady_m3 : float
        What they would hold at rest under the last inflow ordinate [m3].
    """

    outflow_m3s: NDArray[np.float64]
    storage_m3: NDArray[np.float64]
    last_pool_storage_m3: NDArray[np.float64]
    storage_peak_m3: float
    storage_steady_m3: float


@dataclass(frozen=True)
class TableExit:
    """Where a run of the spec ``level_pool`` leaves its table.

    Attributes
    ----------
    pool : int
        The pool that leaves it, from 1 (the first downstream of the inflow).
    index : int
        The ordinate at which it does.
    above : bool
        Whether the pool fills beyond the last row (else it empties below the first).
    """

    pool: int
    index: int
    above: bool


# --- the computation -----------------------------------------------------------------


def _rest(rating: list[float], value: float) -> float:
    """Return the row coordinate of the state at rest with an outflow.

    The coordinate is ``i + f``: row ``i`` and the fraction ``f`` of the way to row
    ``i + 1``. The outflow is clamped to the table; a flat stretch of the outflow rests
    at its last row, the highest storage that gives it.
    """
    index = bisect_right(rating, value)
    if index == 0:
        return 0.0
    if index >= len(rating):
        return float(len(rating) - 1)
    low, high = rating[index - 1], rating[index]
    if low == value:
        return float(index - 1)
    return (index - 1) + (value - low) / (high - low)


def step_limit_s(
    table_storage_m3: NDArray[np.float64],
    table_outflow_m3s: NDArray[np.float64],
    subreaches: int,
    lowest_m3s: float,
    highest_m3s: float,
) -> float:
    """Return the longest step that a run between two flows may take [s].

    Twice the shortest storage constant ``K = dS/dO`` of the segments of a valid table
    (both columns not decreasing) that a run between the lowest and the highest flow
    can reach, over the number of pools: from the state at rest under the lowest flow
    (a flat stretch of the outflow rests at its highest storage) up to the first row
    that reaches the highest flow. A segment whose outflow does not rise does not count.

    Parameters
    ----------
    table_storage_m3, table_outflow_m3s : numpy.ndarray
        Storage [m3] and outflow [m3/s] of each row.
    subreaches : int
        Number of pools in series.
    lowest_m3s, highest_m3s : float
        The lowest and the highest flow of the run [m3/s].

    Returns
    -------
    float
        The limit [s]: ``math.inf`` when no segment counts, ``0`` when a counted
        segment holds no storage.
    """
    rating = table_outflow_m3s
    first = int(_rest(rating.tolist(), max(lowest_m3s, float(rating[0]))))
    last = min(int(np.searchsorted(rating, highest_m3s, side="left")), len(rating) - 1)
    rise = np.diff(rating)[first:last]
    held = np.diff(table_storage_m3)[first:last]
    counted = rise > 0.0
    if not counted.any():
        return math.inf
    with np.errstate(over="ignore"):  # a rise near zero is a K beyond float64: inf
        shortest = float((held[counted] / rise[counted]).min())
    return 2.0 * shortest / subreaches


class _Exit(Exception):
    """A pool left its table (internal; ends the run)."""

    def __init__(self, index: int, above: bool) -> None:
        super().__init__()
        self.index = index
        self.above = above


def _route_pool(
    inflow_m3s: list[float],
    working: list[float],
    rating: list[float],
    start: tuple[float, float, float],
    slack: float,
) -> tuple[list[float], list[float]]:
    """Route one pool: the recurrence of the working curve, ordinate by ordinate.

    Parameters
    ----------
    inflow_m3s : list of float
        Inflow ordinates [m3/s].
    working, rating : list of float
        The working curve ``s/dt + O/2`` of each row (rising) and the outflow.
    start : tuple of float
        Row coordinate, working-curve value and outflow of the first ordinate.
    slack : float
        How far beyond the first or the last row the working curve may stray
        (rounding) before the pool has left the table; the value is then held at the
        end.

    Returns
    -------
    tuple of list
        The outflow and the row coordinate of every ordinate.

    Raises
    ------
    _Exit
        When the working curve falls below the first row or rises above the last.
    """
    last = len(working) - 1
    bottom, top = working[0], working[last]
    position, state, discharge = start
    count = len(inflow_m3s)
    routed = [0.0] * count
    where = [0.0] * count
    routed[0], where[0] = discharge, position
    previous = inflow_m3s[0]
    for k in range(1, count):
        current = inflow_m3s[k]
        state += 0.5 * (previous + current) - discharge
        previous = current
        if state >= top:
            if state > top + slack:
                raise _Exit(k, above=True)
            state, row = top, last - 1
        elif state <= bottom:
            if state < bottom - slack:
                raise _Exit(k, above=False)
            state, row = bottom, 0
        else:
            row = bisect_right(working, state) - 1
        low = working[row]
        fraction = (state - low) / (working[row + 1] - low)
        discharge = rating[row] + fraction * (rating[row + 1] - rating[row])
        routed[k], where[k] = discharge, row + fraction
    return routed, where


@dataclass(frozen=True)
class _Run:
    """The pools' outflow and storage, or where the run left the table."""

    outflow: list[float]
    storage: NDArray[np.float64]
    last_pool: NDArray[np.float64]
    steady: float
    exit: TableExit | None


def _working(
    volumes: NDArray[np.float64],
    rating: NDArray[np.float64],
    step_min: float,
    count: int,
) -> NDArray[np.float64]:
    """Return the working curve ``S/(N dt) + O/2`` of each row [m3/s]."""
    return volumes / count / (step_min * SECONDS_PER_MINUTE) + 0.5 * rating


def _cascade(
    inflow_m3s: NDArray[np.float64],
    step_min: float,
    volumes: NDArray[np.float64],
    rating: NDArray[np.float64],
    count: int,
    initial_m3s: float,
) -> _Run:
    """Route through the pools in series, each at rest with the initial outflow."""
    held = volumes / count
    working = _working(volumes, rating, step_min, count)
    rows = np.arange(len(rating), dtype=np.float64)
    flows = rating.tolist()
    start = _rest(flows, initial_m3s)
    first = (start, float(np.interp(start, rows, working)), initial_m3s)
    slack = ROUNDING * float(working[-1])
    series = inflow_m3s.tolist()
    stored = np.zeros(len(series))
    last = stored
    for pool in range(1, count + 1):
        try:
            series, where = _route_pool(series, working.tolist(), flows, first, slack)
        except _Exit as leave:
            return _Run(
                [], stored, last, 0.0, TableExit(pool, leave.index, leave.above)
            )
        last = np.interp(where, rows, held)
        stored = stored + last
    steady = _rest(flows, float(inflow_m3s[-1]))
    return _Run(
        series, stored, last, count * float(np.interp(steady, rows, held)), None
    )


_SHARED: list[tuple[weakref.ref[Values], _Run]] = []
"""The run of the checked inputs alive last, while they live (:func:`_run_of`)."""


def _forget(gone: weakref.ref[Values]) -> None:
    """Release the run of checked inputs that no longer exist."""
    if _SHARED and _SHARED[0][0] is gone:
        _SHARED.clear()


def _run_of(x: Values) -> _Run:
    """Return the run through the pools of checked inputs, computed once for them.

    ``validate`` checks the preconditions ``flood_below_table_top`` and
    ``flood_above_table_bottom`` on one :class:`Values`, which the formula then routes:
    the three share the recurrence, kept until the inputs are released (another
    thread's inputs only make it compute again).
    """
    for kept, run in _SHARED[:1]:
        if kept() is x:
            return run
    run = _cascade(
        x.array("inflow_m3s"),
        x.real("timestep_min"),
        x.array("table_storage_m3"),
        x.array("table_outflow_m3s"),
        x.integer("subreaches"),
        x.real("initial_outflow_m3s"),
    )
    _SHARED[:] = [(weakref.ref(x, _forget), run)]
    return run


def _route(x: Values) -> dict[str, object]:
    run = _run_of(x)
    if run.exit is not None:  # pragma: no cover - the preconditions refuse it first
        raise RuntimeError(f"level_pool: the run left its table at {run.exit}")
    return {
        "outflow_m3s": run.outflow,
        "storage_m3": run.storage,
        "last_pool_storage_m3": run.last_pool,
        "storage_peak_m3": float(run.storage.max()),
        "storage_steady_m3": run.steady,
    }


def table_exit(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    table_storage_m3: NDArray[np.float64] | Sequence[float],
    table_outflow_m3s: NDArray[np.float64] | Sequence[float],
    subreaches: int,
    initial_outflow_m3s: float,
) -> TableExit | None:
    """Return where a run of the spec level_pool leaves its table, or ``None``.

    The run of the preconditions ``flood_below_table_top`` and
    ``flood_above_table_bottom``, for inputs that meet the spec's other constraints:
    the first pool and ordinate at which the working curve leaves the table, through
    which end.
    """
    return _cascade(
        np.asarray(inflow_m3s, dtype=np.float64),
        float(timestep_min),
        np.asarray(table_storage_m3, dtype=np.float64),
        np.asarray(table_outflow_m3s, dtype=np.float64),
        int(subreaches),
        float(initial_outflow_m3s),
    ).exit


def _volume_kept(x: Values, out: Values) -> float:
    """Return inflow volume - outflow volume - storage change over the largest.

    The largest is at least the volume of the smallest normal discharge over the run:
    below it float64 holds fewer digits, and a subnormal flood keeps its balance only
    to its own precision.
    """
    step = x.real("timestep_min")
    entered = volume_m3(x.array("inflow_m3s"), step)
    left = volume_m3(out.array("outflow_m3s"), step)
    stored = out.array("storage_m3")
    start, end = float(stored[0]), float(stored[-1])
    floor = _SMALLEST_NORMAL * step * SECONDS_PER_MINUTE * len(stored)
    scale = max(entered, left, start, end, floor)
    return (entered - left - (end - start)) / scale if scale > 0.0 else 0.0


# --- the constraints -----------------------------------------------------------------


def _columns(x: Values) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    return x.array("table_storage_m3"), x.array("table_outflow_m3s")


def _paired(x: Values) -> bool:
    volumes, rating = _columns(x)
    return len(volumes) == len(rating)


def _not_decreasing(x: Values) -> bool:
    volumes, rating = _columns(x)
    return bool((np.diff(volumes) >= 0.0).all() and (np.diff(rating) >= 0.0).all())


def _rows_distinct(x: Values) -> bool:
    volumes, rating = _columns(x)
    rows = min(len(volumes), len(rating))
    flat = (np.diff(volumes[:rows]) == 0.0) & (np.diff(rating[:rows]) == 0.0)
    return not flat.any()


def _initial_in_table(x: Values) -> bool:
    rating = x.array("table_outflow_m3s")
    return bool(rating[0] <= x.real("initial_outflow_m3s") <= rating[-1])


def _limit_s(x: Values) -> float:
    """Return the step limit of the run's flows [s] (:func:`step_limit_s`)."""
    values = x.array("inflow_m3s")
    initial = x.real("initial_outflow_m3s")
    return step_limit_s(
        x.array("table_storage_m3"),
        x.array("table_outflow_m3s"),
        x.integer("subreaches"),
        min(float(values.min()), initial),
        max(float(values.max()), initial),
    )


def _within_limit(x: Values) -> bool:
    step_s = x.real("timestep_min") * SECONDS_PER_MINUTE
    return step_s <= _limit_s(x) * (1.0 + ROUNDING)


def _working_rises(x: Values) -> bool:
    with np.errstate(over="ignore", invalid="ignore"):  # refused when not finite
        working = _working(
            x.array("table_storage_m3"),
            x.array("table_outflow_m3s"),
            x.real("timestep_min"),
            x.integer("subreaches"),
        )
        return bool(np.isfinite(working).all() and (np.diff(working) > 0.0).all())


def _stays_below_top(x: Values) -> bool:
    leave = _run_of(x).exit
    return leave is None or not leave.above


def _stays_above_bottom(x: Values) -> bool:
    leave = _run_of(x).exit
    return leave is None or leave.above


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_EXACT_POINTS: Final = (
    # inflow [m3/s], step [min], storage [m3], outflow [m3/s], pools, initial outflow
    (
        (0.0, 5.0, 15.0, 12.0, 6.0, 2.0, 0.0, 0.0),
        20.0,
        (0.0, 2.0e5, 3.0e5, 5.0e5),
        (0.0, 0.0, 10.0, 40.0),
        1,
        0.0,
    ),
    (
        (2.0, 12.0, 30.0, 18.0, 8.0, 3.0, 2.0),
        30.0,
        (0.0, 1.8e4, 9.0e4),
        (0.0, 10.0, 40.0),
        2,
        2.0,
    ),
    (
        (10.0, 30.0, 60.0, 65.0, 50.0, 30.0, 20.0, 10.0),
        0.05,
        (0.0, 2000.0, 2250.0, 4000.0),
        (0.0, 20.0, 70.0, 100.0),
        3,
        10.0,
    ),
)
"""Inputs of the exact oracle: a pond with a crest that starts full to it, two pools on
a step at their limit, and three pools of a kinked table."""

_KINK: Final = (
    (40.0, 40.0, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0, 60.0),
    convert(10.0, "s", "min"),
    (0.0, 2000.0, 2250.0),
    (0.0, 20.0, 70.0),
    1,
    40.0,
)
"""A rise from 40 to 60 m3/s through a table whose K = dS/dO falls from 100 s to 5 s at
20 m3/s, on the step of 10 s that the steep segment allows: NEH's rule for the whole
curve, dt <= 2 S/O, would allow 64 s, on which the outflow overshoots 60 m3/s."""


def _exact_outflow(
    inflow_m3s: Sequence[float],
    step_min: float,
    volumes: Sequence[float],
    rating: Sequence[float],
    count: int,
    initial: float,
) -> list[Fraction]:
    """Return the recurrence of the pools in exact rational arithmetic."""
    step_s = Fraction(step_min) * Fraction(SECONDS_PER_MINUTE)
    flows = [Fraction(value) for value in rating]
    working = [
        Fraction(volume) / count / step_s + flow / 2
        for volume, flow in zip(volumes, flows, strict=True)
    ]
    top = len(flows) - 1
    start = Fraction(initial)
    index = bisect_right(flows, start)
    if index == 0:
        rest = working[0]
    elif index > top:
        rest = working[top]
    else:
        low, high = flows[index - 1], flows[index]
        part = (start - low) / (high - low)
        rest = working[index - 1] + part * (working[index] - working[index - 1])
    series = [Fraction(value) for value in inflow_m3s]
    for _ in range(count):
        state, discharge = rest, start
        out = [start]
        for t in range(1, len(series)):
            state += (series[t - 1] + series[t]) / 2 - discharge
            row = min(max(bisect_right(working, state) - 1, 0), top - 1)
            part = (state - working[row]) / (working[row + 1] - working[row])
            discharge = flows[row] + part * (flows[row + 1] - flows[row])
            out.append(discharge)
        series = out
    return series


def _inputs(
    values: Sequence[float],
    step: float,
    volumes: Sequence[float],
    rating: Sequence[float],
    count: int,
    initial: float,
) -> dict[str, object]:
    return {
        "inflow_m3s": list(values),
        "timestep_min": step,
        "table_storage_m3": list(volumes),
        "table_outflow_m3s": list(rating),
        "subreaches": count,
        "initial_outflow_m3s": initial,
    }


def _exact_recurrence(run: Callable[..., Values]) -> None:
    for point in _EXACT_POINTS:
        out = run(**_inputs(*point))
        exact = _exact_outflow(*point)
        assert_within(
            out.array("outflow_m3s"),
            [float(value) for value in exact],
            rel=1e-12,
            abs=1e-12,
            reason="the recurrence in float64 against the same recurrence in exact "
            "rational arithmetic: a few roundings of the working curve and of the "
            "state per step, at 1e-16 of the working curve, damped by the weight "
            "(2K - dt) / (2K + dt) < 1 over at most eight steps and three pools",
        )


_LINEAR_POINTS: Final = (
    # K [min], pools, step [min], inflow [m3/s], initial outflow, top of the table
    (40.0, 1, 10.0, (5.0, 12.0, 30.0, 45.0, 38.0, 20.0, 9.0, 6.0, 5.0), 5.0, 50.0),
    (40.0, 3, 10.0, (5.0, 12.0, 30.0, 45.0, 38.0, 20.0, 9.0, 6.0, 5.0), 8.0, 50.0),
    (90.0, 2, 90.0, (0.0, 4.5, 37.0, 81.25, 40.0, 12.0, 3.0, 0.0), 0.0, 100.0),
)
"""Linear tables ``S = K O``; the last on the step ``2K / N``, where the weight of the
previous outflow is zero."""


def _muskingum_without_weight(run: Callable[..., Values]) -> None:
    for k_min, count, step, values, initial, top in _LINEAR_POINTS:
        volumes = (0.0, k_min * SECONDS_PER_MINUTE * top)
        out = run(**_inputs(values, step, volumes, (0.0, top), count, initial))
        reservoir = muskingum_route(values, step, k_min, 0.0, count, initial)
        stored = out.array("storage_m3")
        assert_within(
            [*out.array("outflow_m3s"), stored[0], stored[-1]],
            [
                *reservoir.outflow_m3s,
                reservoir.storage_start_m3,
                reservoir.storage_end_m3,
            ],
            rel=1e-12,
            abs=1e-9,
            reason="the working curve of S = K O is (K/(N dt) + 1/2) O, so storage "
            "indication is the trapezoid rule of the linear reservoir, Muskingum's "
            "scheme with X = 0, exactly; the two codes round apart at 1e-16 per step, "
            "damped by c_outflow < 1 (abs: storages of 1e5 m3 to 1e-14)",
        )


def _bounded(run: Callable[..., Values]) -> None:
    for point in (*_EXACT_POINTS, _KINK):
        values, step, volumes, rating, count, initial = point
        out = run(**_inputs(*point)).array("outflow_m3s")
        low = min(*values, initial)
        high = max(*values, initial)
        top = float(_working(np.array(volumes), np.array(rating), step, count)[-1])
        slack = 1e-13 * top
        if not ((out >= low - slack).all() and (out <= high + slack).all()):
            raise AssertionError(
                f"level_pool: outflow {out} leaves [{low}, {high}], the range of the "
                "inflow and the initial outflow, though a step within the limit of "
                "every segment the run reaches makes the scheme monotone (the slack "
                "is the rounding of the working curve, 1e-16 of its top per step)"
            )


def _datum_free(run: Callable[..., Values]) -> None:
    for point in _EXACT_POINTS:
        values, step, volumes, rating, count, initial = point
        here = run(**_inputs(*point))
        raised = [volume + 5.0e6 for volume in volumes]
        moved = run(**_inputs(values, step, raised, rating, count, initial))
        assert_within(
            [*moved.array("outflow_m3s"), moved.real("storage_peak_m3") - 5.0e6],
            [*here.array("outflow_m3s"), here.real("storage_peak_m3")],
            rel=1e-9,
            abs=1e-9,
            reason="only differences of storage enter the working curve; a datum of "
            "5e6 m3 above tables of 4e3 to 5e5 m3 rounds their working curve at 1e-16 "
            "of the datum's, up to 1e-10 of the outflow",
        )


# --- the spec ------------------------------------------------------------------------

_NEH = neh630_17(
    "eqs. 17-1 to 17-3, pp. 17-9 to 17-10 (a working curve of O2 against S2/dt + "
    "O2/2 is necessary); examples 17-1 and 17-2, tables 17-5 to 17-12, pp. 17-11 to "
    "17-25"
)
_NEH_STEP = neh630_17(
    "pp. 17-10 to 17-11: negative outflows whenever dt > 2 S2/O2 (O2/2 > S2/dt); a "
    "working curve with any part left of the line of equal values is discarded and "
    "computed again with a smaller dt, as WinTR-20 does internally"
)
_NEH_TABLES = neh630_17(
    "tables 17-4 and 17-9 to 17-11: storage and discharge accumulated with the "
    "elevation, both rising with it"
)
_HEC_HMS = hec_hms(
    "Modified Puls Model",
    "modified-puls-model",
    "eq. 3; Required Parameters: the initial outflow, a storage vs. discharge "
    "relationship and the number of subreaches",
)
_HEC_HMS_TABLE = hec_hms(
    "Modified Puls Model",
    "modified-puls-model",
    "Required Parameters: the storage vs. discharge relationship is a paired data "
    "object whose storages cover the entire range met in a simulation; the initial "
    "storage is computed from the initial outflow and that relationship",
)
_EM = em_1110_2_1417("chapter 9, modified Puls, eq. 9-12")
_ADR_0008 = Source(
    citation="Hydrolog ADR-0008: routing conventions",
    locator="docs/decisions/0008-routing-conventions.md, Stability: a level-pool step "
    "of at most twice the shortest dS/dO of the segments between the lowest and the "
    "highest flow of the run, over the number of sub-reaches; NEH's rule for the "
    "whole curve let the outflow exceed the inflow peak on 201 of 1,499 random tables",
)
_EXACT_SCALING = Tolerance(
    rel=0.0,
    abs=1e-300,
    reason="a power of two scales every value of the working curve, of the state and "
    "of the interpolation exactly in binary, but for subnormal values, which round to "
    "fewer digits",
)
_BASE_INFLOW: Final = (5.0, 20.0, 60.0, 90.0, 70.0, 40.0, 20.0, 10.0, 5.0, 5.0)
_BASE_STORAGE: Final = (0.0, 1.8e5, 5.4e5, 1.08e6, 1.8e6)
_BASE_OUTFLOW: Final = (0.0, 10.0, 40.0, 100.0, 200.0)
_RAISED_OUTFLOW: Final = (5.0, 10.0, 40.0, 100.0, 200.0)

LEVEL_POOL: Final = FormulaSpec(
    name="level_pool",
    title="Level-pool routing by storage indication (modified Puls) through N equal "
    "pools",
    function="hydrolog.routing.formulas.level_pool.level_pool_route",
    family="scheme",
    equation=(
        "in each of N pools in series, holding s = S(O) / N of the table for the "
        "same outflow: s[t] / dt + O[t] / 2 = (I[t-1] + I[t]) / 2 + s[t-1] / dt - "
        "O[t-1] / 2, O[t] read from the working curve s / dt + O / 2 of the table, "
        "linear between its rows; O[0] = O0 in every pool, at rest at the highest "
        "storage the table gives O0"
    ),
    latex=(
        r"\frac{s_t}{\Delta t} + \frac{O_t}{2} = \frac{I_{t-1} + I_t}{2} + "
        r"\frac{s_{t-1}}{\Delta t} - \frac{O_{t-1}}{2},\quad s = \frac{S(O)}{N}"
    ),
    variables=(
        inflow(),
        timestep(),
        Variable(
            name="table_storage_m3",
            symbol="S_i",
            unit="m3",
            kind="real_array",
            description="Storage of each row of the storage-outflow table, not "
            "decreasing; only its differences enter the outflow, so its datum is free.",
            physical=Range(
                low=0.0,
                test_high=3.0e7,
                test_reason="ten times the largest table of Hydrolog's routing "
                "tests (NEH 630 ch. 17 example 17-2, 2.87e6 m3); the scheme is "
                "homogeneous in the storage and the discharge (scaling discharge), so "
                "any bound tests its arithmetic",
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=3.0e6,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="tables up to 2.87e6 m3: NEH 630 ch. 17 example 17-2, "
                    "1,174.5 ft3/s-d; the catalog's pond, 255,000 m3 "
                    "(tests/fixtures/pond_rating.csv)",
                ),
            ),
            min_length=2,
        ),
        Variable(
            name="table_outflow_m3s",
            symbol="O_i",
            unit="m3/s",
            kind="real_array",
            description="Outflow of each row of the table, not decreasing; zero below "
            "a crest.",
            physical=DISCHARGE,
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=300.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="tables up to 283.2 m3/s: NEH 630 ch. 17 example 17-1, "
                    "10,000 ft3/s; the catalog's pond, 27.17 m3/s",
                ),
            ),
            min_length=2,
        ),
        Variable(
            name="subreaches",
            symbol="N",
            unit="-",
            kind="integer",
            description="Number of pools in series, each holding S / N of the table "
            "for the same outflow.",
            physical=Range(
                low=1.0,
                test_high=1000.0,
                test_reason="HEC-HMS's estimate L / (c dt) for a reach of 100 km, a "
                "celerity of 1 m/s and a step of 100 s",
            ),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=6.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="1 (a pond or a reservoir, the default of LevelPoolReach) "
                    "to 6 pools in the tests of the reach",
                ),
            ),
        ),
        initial_outflow(),
    ),
    outputs=(
        outflow(),
        Output(
            name="storage_m3",
            unit="m3",
            kind="real_array",
            symbol="S_t",
            description="Water held by all pools at every ordinate.",
            physical=STORAGE,
        ),
        Output(
            name="last_pool_storage_m3",
            unit="m3",
            kind="real_array",
            symbol="s_t",
            description="Water held by the last pool at every ordinate, all of it when "
            "N = 1.",
            physical=STORAGE,
        ),
        storage("storage_peak_m3", "The largest water held by all pools."),
        storage(
            "storage_steady_m3",
            "Water the pools would hold at rest under the last inflow ordinate.",
        ),
    ),
    sources=(_NEH, _HEC_HMS, _EM),
    constraints=(
        Constraint(
            name="table_columns_paired",
            cls="physical",
            check=_paired,
            text="the storage and the outflow columns have as many rows",
            source=_HEC_HMS_TABLE,
            satisfied={"table_outflow_m3s": _BASE_OUTFLOW},
            violated={"table_outflow_m3s": _BASE_OUTFLOW[:-1]},
        ),
        Constraint(
            name="table_not_decreasing",
            cls="physical",
            check=_not_decreasing,
            text="S[i] <= S[i+1] and O[i] <= O[i+1]: storage and outflow rise together "
            "with the water level",
            source=_NEH_TABLES,
            satisfied={"table_storage_m3": _BASE_STORAGE},
            boundary={"table_outflow_m3s": (0.0, 0.0, 40.0, 100.0, 200.0)},
            violated={"table_storage_m3": (0.0, 1.8e5, 1.7e5, 1.08e6, 1.8e6)},
        ),
        Constraint(
            name="table_rows_distinct",
            cls="physical",
            check=_rows_distinct,
            text="no row repeats the one before it: the working curve rises from row "
            "to row",
            source=_NEH,
            satisfied={"table_storage_m3": _BASE_STORAGE},
            boundary={"table_storage_m3": (0.0, 0.0, 5.4e5, 1.08e6, 1.8e6)},
            violated={
                "table_storage_m3": (0.0, 0.0, 5.4e5, 1.08e6, 1.8e6),
                "table_outflow_m3s": (0.0, 0.0, 40.0, 100.0, 200.0),
            },
        ),
        Constraint(
            name="initial_outflow_in_table",
            cls="precondition",
            check=_initial_in_table,
            text="O[0] <= O0 <= O[-1]: the pools start at rest at a state of the table",
            source=_HEC_HMS_TABLE,
            satisfied={"initial_outflow_m3s": 5.0},
            boundary={"initial_outflow_m3s": 200.0},
            violated={"initial_outflow_m3s": 201.0},
        ),
        Constraint(
            name="storage_where_outflow_rises",
            cls="precondition",
            check=lambda x: _limit_s(x) > 0.0,
            text="dS > 0 on every segment where the outflow rises, from the state at "
            "rest under the lowest flow of the run to the first row that reaches its "
            "largest: no step meets the step rule on a segment without storage",
            source=_NEH_STEP,
            satisfied={"table_storage_m3": _BASE_STORAGE},
            boundary={
                "inflow_m3s": (5.0, 20.0, 60.0, 100.0, 70.0, 40.0, 20.0, 10.0, 5.0),
                "table_storage_m3": (0.0, 1.8e5, 5.4e5, 1.08e6, 1.08e6),
            },
            violated={"table_storage_m3": (0.0, 1.8e5, 1.8e5, 1.08e6, 1.8e6)},
        ),
        Constraint(
            name="timestep_within_limit",
            cls="precondition",
            check=_within_limit,
            text="dt <= 2 min(dS/dO) / N over the segments the run can reach (from the "
            "state at rest under its lowest flow to the first row that reaches its "
            "largest), to 1e-9 of itself: the weight (2K - dt) / (2K + dt) of the "
            "previous state is not negative on any of them, so the outflow stays "
            "between the lowest and the highest flow of the run",
            source=_ADR_0008,
            satisfied={"timestep_min": 30.0},
            boundary={"timestep_min": 150.0},
            violated={"timestep_min": 151.0},
        ),
        Constraint(
            name="working_curve_rises",
            cls="precondition",
            check=_working_rises,
            text="S / (N dt) + O / 2 is finite and rises from row to row in float64: "
            "the outflow is read from it",
            source=_NEH,
            satisfied={"table_storage_m3": _BASE_STORAGE},
            violated={
                "table_storage_m3": (0.0, 1.0e-30, 5.4e5, 1.08e6, 1.8e6),
                "table_outflow_m3s": (1.0, 1.0, 40.0, 100.0, 200.0),
            },
        ),
        Constraint(
            name="flood_below_table_top",
            cls="precondition",
            check=_stays_below_top,
            text="no pool fills beyond the last row (its working curve above the last "
            "row's by more than 1e-9 of it): the table covers the flood, never an "
            "extrapolation",
            source=_HEC_HMS_TABLE,
            satisfied={"inflow_m3s": _BASE_INFLOW},
            boundary={"inflow_m3s": (200.0,) * 10, "initial_outflow_m3s": 200.0},
            violated={
                "inflow_m3s": (5.0, 60.0, 200.0, 300.0, 300.0, 300.0, 200.0, 100.0)
            },
        ),
        Constraint(
            name="flood_above_table_bottom",
            cls="precondition",
            check=_stays_above_bottom,
            text="no pool empties below the first row (its working curve below the "
            "first row's by more than 1e-9 of the last row's): an inflow below the "
            "first outflow of the table must not drain it",
            source=_HEC_HMS_TABLE,
            satisfied={"table_outflow_m3s": _RAISED_OUTFLOW},
            boundary={
                "inflow_m3s": (5.0,) * 10,
                "table_outflow_m3s": _RAISED_OUTFLOW,
            },
            violated={
                "inflow_m3s": (5.0, 20.0, 60.0, 90.0, 70.0, 40.0) + (0.0,) * 14,
                "table_outflow_m3s": _RAISED_OUTFLOW,
            },
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="discharge",
                inputs={
                    "inflow_m3s": 1,
                    "table_storage_m3": 1,
                    "table_outflow_m3s": 1,
                    "initial_outflow_m3s": 1,
                },
                outputs={
                    "outflow_m3s": 1,
                    "storage_m3": 1,
                    "last_pool_storage_m3": 1,
                    "storage_peak_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="time",
                inputs={"timestep_min": 1, "table_storage_m3": 1},
                outputs={
                    "storage_m3": 1,
                    "last_pool_storage_m3": 1,
                    "storage_peak_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
        ),
        conservation=(
            Conservation(
                name="volume",
                text="the trapezoid continuity holds in every pool: inflow volume - "
                "outflow volume = storage at the end - storage at the start",
                residual=_volume_kept,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="relative to the largest volume or storage, at least the "
                    "volume of the smallest normal discharge over the run (a subnormal "
                    "flood rounds to its fewer digits): the state rounds at 1e-16 of "
                    "the working curve per step, damped by the weight (2K - dt) / "
                    "(2K + dt) < 1; a state that rounding puts beyond an end of the "
                    "table, within 1e-9 of it, is held at the end",
                ),
            ),
        ),
        limits=(
            Limit(
                name="steady_state",
                text="an inflow equal to the initial outflow passes unchanged, and the "
                "pools hold what the table gives it at rest",
                inputs={"inflow_m3s": (25.0,) * 12, "initial_outflow_m3s": 25.0},
                expected={
                    "outflow_m3s": [25.0] * 12,
                    "storage_m3": [3.6e5] * 12,
                    "storage_steady_m3": 3.6e5,
                },
                tolerance=Tolerance(
                    rel=1e-13,
                    reason="the state does not change but by the rounding of the "
                    "interpolation at 1e-16, which the next step reads back",
                ),
            ),
            Limit(
                name="exact_recurrence",
                text="every outflow equals the recurrence of the pools in exact "
                "rational arithmetic",
                check=_exact_recurrence,
            ),
            Limit(
                name="muskingum_without_weight",
                text="a table S = K O is the linear reservoir: the outflow and the "
                "storage of the spec muskingum with X = 0 and the same K, N and step",
                check=_muskingum_without_weight,
            ),
            Limit(
                name="bounded_by_its_flows",
                text="every outflow lies between the least and the largest of the "
                "inflow and the initial outflow, a kinked table on the step its steep "
                "segment allows included; the scheme is non-decreasing in the inflow "
                "and the initial outflow to the rounding of its working curve, larger "
                "than four units in the last place of the outflow on a short step "
                "(test_the_outflow_rises_with_its_inflow_and_initial_outflow)",
                check=_bounded,
            ),
            Limit(
                name="datum_free",
                text="a constant added to the storage column changes no outflow and "
                "adds itself to the storage",
                check=_datum_free,
            ),
        ),
    ),
    validation=(
        "none: the storage-outflow relation of a reach or a reservoir comes from "
        "water-surface profiles, the reservoir's topography or observed floods "
        "(HEC-HMS TRM, Modified Puls; NEH 630 ch. 17); the sources report no agreement "
        "of the scheme itself with observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "SI units: discharge in m3/s, storage in m3, the step in min (S / dt with the "
        "60 s of a minute of the units table)",
        (
            "the outflow is read from the working curve S / (N dt) + O / 2 by linear "
            "interpolation between the rows of the table, as the table is linear "
            "between them (NEH 630 interpolates its working table, HEC-HMS solves the "
            "same equation by trial and error)"
        ),
        (
            "N pools in series each hold S / N for the same outflow (HEC-HMS "
            "subreaches); every pool starts at rest with O0, at the highest storage "
            "the table gives that outflow, so a pool with a dead zone below a crest "
            "starts full to the crest"
        ),
        (
            "the datum of the storage column is free: only differences of storage "
            "enter the outflow, and the storages reported are measured from it"
        ),
        (
            "a state that rounding puts beyond an end of the table by at most 1e-9 of "
            "the working curve's top is held at that end; further beyond, the pool "
            "has left the table, which the preconditions flood_below_table_top and "
            "flood_above_table_bottom refuse"
        ),
        (
            "the storage at rest under the last inflow ordinate is read at the end row "
            "of the table for a flow beyond it"
        ),
        (
            "only the given ordinates are routed: LevelPoolReach divides a longer step "
            "into sub-steps, the inflow linear between the ordinates, extends the time "
            "axis and reads the stage of the last pool (Tier B, ADR-0008)"
        ),
    ),
    assumptions=(
        (
            "the storage is a single-valued function of the outflow: a level water "
            "surface, or a reach whose storage follows its outflow, without hysteresis "
            "(NEH 630: the water surface is level or nearly level)"
        ),
        (
            "for a channel NEH 630 asks for a travel time through the reach of about "
            "half the inflow's time of rise or less (not an input: not checked)"
        ),
        "the inflow is linear between its ordinates (the trapezoid rule)",
    ),
    traps={
        "difference_denominator": "the fraction (Y - W[r]) / (W[r+1] - W[r]) of a "
        "segment of the working curve: rows whose working curve is equal in float64 "
        "are refused by the precondition working_curve_rises "
        "(test_rows_the_working_curve_cannot_tell_apart_are_refused); K = dS/dO of "
        "the step rule is taken only where the outflow rises",
        "stability_bound": "dt <= 2 min(dS/dO) / N on the segments the run reaches: "
        "precondition timestep_within_limit with its satisfied, boundary and violated "
        "points, limit bounded_by_its_flows (a kinked table on the step of its steep "
        "segment) and test_a_step_that_the_rule_for_the_whole_curve_allows_is_refused",
        "gap_propagation": "type cases inflow_m3s-nan_element, "
        "table_storage_m3-nan_element and table_outflow_m3s-nan_element: a gap is "
        "refused, the recurrence would carry it to every later ordinate",
        "many_small_terms": "test_a_long_steady_inflow_stays_steady: 200,000 ordinates "
        "of a steady inflow stay steady to 1e-12",
    },
    reference_cases=("tests/fixtures/formulas/level-pool-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the recurrence of the pools and their state at rest in exact "
            "rational arithmetic (fractions), ordinate by ordinate",
            test="tests/unit/test_formulas_level_pool.py (limit exact_recurrence)",
        ),
        Oracle(
            kind="algorithm",
            description="a table S = K O is the linear reservoir: the spec muskingum "
            "with X = 0 and the same K, N and step, its three-point recurrence "
            "(scipy.signal.lfilter)",
            test="tests/unit/test_formulas_level_pool.py "
            "(limit muskingum_without_weight)",
        ),
        Oracle(
            kind="established",
            description="scipy.integrate.solve_ivp (RK45, rtol 1e-11) of dS/dt = "
            "I(t) - O(S) through a weir's table: the scheme's error falls as the step "
            "squared",
            test="tests/unit/test_formulas_level_pool.py::"
            "test_the_scheme_converges_to_the_integrated_equation",
            conventions=(
                "both sides read O(S) from the same table, linear between its rows, "
                "and take the inflow linear between its ordinates",
                "the scheme is the trapezoid rule on the step; solve_ivp an adaptive "
                "Runge-Kutta method of order 5(4) in continuous time",
            ),
        ),
    ),
    base={
        "inflow_m3s": _BASE_INFLOW,
        "timestep_min": 30.0,
        "table_storage_m3": _BASE_STORAGE,
        "table_outflow_m3s": _BASE_OUTFLOW,
        "subreaches": 2,
        "initial_outflow_m3s": 5.0,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (LEVEL_POOL,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def level_pool_route(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    table_storage_m3: NDArray[np.float64] | Sequence[float],
    table_outflow_m3s: NDArray[np.float64] | Sequence[float],
    subreaches: int,
    initial_outflow_m3s: float,
) -> LevelPoolRoute:
    """Route a hydrograph through level pools by storage indication, spec level_pool.

    The first input is the inflow at every ordinate and the last the outflow at the
    first one, both in cubic metres per second; the table gives the storage, in cubic
    metres, and the outflow, in cubic metres per second, of each of its rows.

    Parameters
    ----------
    timestep_min : float
        Time step of the ordinates [min].
    subreaches : int
        Number ``N`` of pools in series, each holding its share of the storage.

    Returns
    -------
    LevelPoolRoute
        The outflow, the water held by the pools and by the last of them at every
        ordinate, its peak, and what the pools would hold at rest.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a gap, a table whose columns differ in length, fall or repeat
        a row, or a failed precondition (``precondition_failed``): the initial outflow
        outside the table, a time step beyond the limit of the segments the run
        reaches, or a flood that fills a pool beyond the table or empties it below
        (``flood_below_table_top``, ``flood_above_table_bottom``).
    """
    values = checked_inputs(
        LEVEL_POOL,
        inflow_m3s=inflow_m3s,
        timestep_min=timestep_min,
        table_storage_m3=table_storage_m3,
        table_outflow_m3s=table_outflow_m3s,
        subreaches=subreaches,
        initial_outflow_m3s=initial_outflow_m3s,
    )
    out = checked_outputs(LEVEL_POOL, _route(values))
    return LevelPoolRoute(
        outflow_m3s=out.array("outflow_m3s"),
        storage_m3=out.array("storage_m3"),
        last_pool_storage_m3=out.array("last_pool_storage_m3"),
        storage_peak_m3=out.real("storage_peak_m3"),
        storage_steady_m3=out.real("storage_steady_m3"),
    )
