r"""Level-pool routing: storage indication, the modified Puls method.

A reservoir, a pond, or a reach with a tabulated storage curve holds one storage ``S``
for each outflow ``O``. The continuity equation over a time step ``dt`` with the
trapezoid rule is

.. math::
    \frac{I_1 + I_2}{2} - \frac{O_1 + O_2}{2} = \frac{S_2 - S_1}{dt},

which puts everything unknown on the left,

.. math::
    \frac{S_2}{dt} + \frac{O_2}{2}
    = \frac{I_1 + I_2}{2} + \frac{S_1}{dt} - \frac{O_1}{2}.

The *working curve* ``Y(O) = S(O) / dt + O / 2`` is tabulated from the storage-outflow
table, and the outflow of the new step is read from it by linear interpolation
(NEH-630 chapter 17, example 17-1; HEC-HMS "Modified Puls"). The table is a polyline:
its rows ``(S_i, O_i)`` are given in increasing order of both, so ``Y`` rises along it
and a dead zone, a stretch of storage with no outflow below a crest or an invert, is
allowed. The optional stage column rides along the same polyline and only reports the
water level. Only differences of storage enter the method, so the datum of the storage
column is free; row 0 is the lowest state of the table.

**Step rule.** Where the storage constant of the table, ``K = dS / dO``, is shorter
than half the time step, the weight of the previous outflow of the linear reservoir of
that ``K``, ``(2K - dt) / (2K + dt)``, is negative: the outflow overshoots, and can go
negative (NEH-630: negative outflows whenever ``dt > 2 S / O``; the working curve must
lie to the right of the line of equal values ``Y = O``). With ``dt <= 2K`` on every
segment the scheme is monotone: the outflow stays between the lowest and the highest
flow of the run and is not negative (:func:`timestep_limit_min`). NEH-630 states the
rule for the whole curve, ``S / O``, which is a mean of the ``K`` below it and lets a
step through on a table whose slope changes sharply. Only the segments the run can use
count: from the state at rest under the lowest flow (a flat stretch of the table rests
at its highest storage, the pool full to the crest) up to the largest flow (the
largest inflow, or the initial outflow), so a row for overtopping far above the flood
does not shorten the step. When the step of the hydrograph is longer, it is divided
into the fewest equal sub-steps that meet the rule, the inflow is interpolated
linearly, the outflow is read at the original ordinates and the notice
``timestep_refined`` says so (WinTR-20 does the same); the volume balance then has the
sampling error of the trapezoid rule. More than 100 sub-steps are refused
(``details.reason`` ``unstable_timestep``).

**Sub-reaches.** ``subreaches = N`` routes through ``N`` reaches in series, each with
the storage ``S / N`` for the same outflow (HEC-HMS): more of them, less attenuation,
for a channel whose travel time is about ``N`` steps. One is a pond or a reservoir.

**Initial state and range.** Every sub-reach starts at rest with the initial outflow
(the first inflow ordinate unless given), whose storage is read from the table (the
highest storage of a flat stretch of the outflow: a reservoir sits at its crest). A
table must cover the run: an initial outflow outside it is a validation error, and a
flood that fills the reservoir beyond its last row (``table_exceeded``) or empties it
below its first (``table_emptied``) is a calculation error, never an extrapolation.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing._checks import as_array, whole_number
from hydrolog.routing.hydrograph import Hydrograph, TableProblem
from hydrolog.routing.muskingum import MAX_SUBSTEPS
from hydrolog.routing.reach import MAX_ORDINATES, Reach, ReachRun, RoutingNotice

__all__ = ["LevelPoolReach", "check_rating", "rating_arrays", "timestep_limit_min"]

_SECONDS_PER_MINUTE = 60.0
_TOLERANCE = 1e-9
"""Relative slack of the table ends and of the step rule: rounding, not data."""


def check_rating(
    storage_m3: NDArray[np.float64],
    outflow_m3s: NDArray[np.float64],
    stage_m: NDArray[np.float64] | None = None,
) -> TableProblem | None:
    """Find the first problem of a storage-outflow table.

    Parameters
    ----------
    storage_m3 : numpy.ndarray
        Storage of each row [m3].
    outflow_m3s : numpy.ndarray
        Outflow of each row [m3/s].
    stage_m : numpy.ndarray, optional
        Water level of each row [m].

    Returns
    -------
    TableProblem or None
        The first violated rule in the order: one-dimensional arrays, equal lengths, at
        least two rows, finite values, storage and outflow not negative, no column
        decreasing (``decreasing``) and no row repeating its predecessor
        (``repeated_row``: the working curve could not be inverted); ``None`` when the
        table is valid. ``details.index`` is the first offending row.
    """
    columns = [("storage_m3", storage_m3), ("outflow_m3s", outflow_m3s)]
    if stage_m is not None:
        columns.append(("stage_m", stage_m))
    for name, values in columns:
        if values.ndim != 1:
            return TableProblem(
                name, "type", f"{name} must be a flat list of numbers", {}
            )
    rows = len(storage_m3)
    for name, values in columns[1:]:
        if len(values) != rows:
            return TableProblem(
                name,
                "length_mismatch",
                f"{len(values)} values for {rows} rows of storage_m3",
                {"rows": rows, "values": len(values)},
            )
    if rows < 2:
        return TableProblem(
            "storage_m3",
            "too_short",
            "a storage-outflow table needs at least two rows",
            {"rows": rows},
        )
    for name, values in columns:
        broken = ~np.isfinite(values)
        if broken.any():
            index = int(np.argmax(broken))
            return TableProblem(
                name,
                "not_finite",
                f"{name}[{index}] is not a finite number",
                {"index": index},
            )
    for name, values in columns[:2]:
        negative = values < 0.0
        if negative.any():
            index = int(np.argmax(negative))
            return TableProblem(
                name,
                "negative",
                f"{name} must not be negative; {name}[{index}] = {values[index]:g}",
                {"index": index, "value": float(values[index])},
            )
    for name, values in columns:
        falling = np.diff(values) < 0.0
        if falling.any():
            index = int(np.argmax(falling)) + 1
            return TableProblem(
                name,
                "decreasing",
                f"{name} must not decrease; {name}[{index}] = {values[index]:g} is "
                f"below {name}[{index - 1}] = {values[index - 1]:g}",
                {"index": index},
            )
    repeated = (np.diff(storage_m3) == 0.0) & (np.diff(outflow_m3s) == 0.0)
    if repeated.any():
        index = int(np.argmax(repeated)) + 1
        return TableProblem(
            "outflow_m3s",
            "repeated_row",
            f"row {index} repeats row {index - 1} (the same storage and outflow); "
            "the working curve S/dt + O/2 must rise from row to row",
            {"index": index},
        )
    return None


def rating_arrays(
    storage_m3: ArrayLike, outflow_m3s: ArrayLike, stage_m: ArrayLike | None = None
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64] | None]:
    """Return a storage-outflow table as arrays, after checking it.

    Parameters
    ----------
    storage_m3, outflow_m3s : array_like
        Storage [m3] and outflow [m3/s] of each row.
    stage_m : array_like, optional
        Water level [m] of each row.

    Returns
    -------
    tuple
        The three columns as new ``float64`` arrays (the stage ``None`` when not given).

    Raises
    ------
    InvalidParameterError
        With ``details.option`` the column (``storage_m3``, ``outflow_m3s`` or
        ``stage_m``) and ``details.reason`` ``type`` when it holds no numbers, or the
        rule of :func:`check_rating` that the table breaks.
    """
    storage = as_array(storage_m3, "storage_m3")
    outflow = as_array(outflow_m3s, "outflow_m3s")
    stage = None if stage_m is None else as_array(stage_m, "stage_m")
    problem = check_rating(storage, outflow, stage)
    if problem is not None:
        raise InvalidParameterError(
            f"Option {problem.option!r}: {problem.message}",
            details={
                "option": problem.option,
                "reason": problem.reason,
                **problem.details,
            },
        )
    return storage, outflow, stage


def timestep_limit_min(
    storage_m3: ArrayLike,
    outflow_m3s: ArrayLike,
    *,
    subreaches: int = 1,
    outflow_floor_m3s: float | None = None,
    outflow_cap_m3s: float | None = None,
) -> float:
    """Return the longest time step that keeps the working curve valid.

    The local storage constant of every segment of the table, ``K = dS / dO`` (the
    slope of the working curve), must be at least ``dt / 2``: then the weight of the
    previous outflow of the linear reservoir of that ``K``, ``(2K - dt) / (2K + dt)``,
    is not negative, as in the Muskingum window for ``X = 0``. The outflow of the run
    then stays between its lowest and its highest flow, and is not negative. With ``N``
    sub-reaches each holds ``S / N``, so the limit is ``2 min(K) / N``.

    NEH-630 chapter 17 states the rule for the whole curve, ``S / dt >= O / 2`` at
    every row (a working curve to the right of the line of equal values), which is the
    same rule for ``S / O``, a mean of the ``K`` of the segments below the row. It does
    not suffice on a table with a sharp change of slope, where a step longer than the
    ``K`` of one segment lets the outflow overshoot the inflow peak.

    Only the segments the run can use count: from the state at rest under the lowest
    flow (a flat stretch of the table rests at its highest storage, the pool full to
    the crest) up to the first row that reaches the largest flow.

    Parameters
    ----------
    storage_m3, outflow_m3s : array_like
        The table, a valid one (:func:`check_rating`): both columns not decreasing.
    subreaches : int, optional
        Number of sub-reaches ``N``, by default 1.
    outflow_floor_m3s : float, optional
        The lowest outflow of the run [m3/s]; the segments below the state at rest
        under it do not count. Default (and when it is lower than the first outflow of
        the table): the first row.
    outflow_cap_m3s : float, optional
        The largest outflow of the run [m3/s]; the segments above the first row that
        reaches it do not count. Default: the whole table.

    Returns
    -------
    float
        The limit [min]; ``math.inf`` when no segment counts (the outflow does not
        rise within the flows of the run); ``0`` when a counted segment holds no
        storage.
    """
    storage = np.asarray(storage_m3, dtype=np.float64)
    outflow = np.asarray(outflow_m3s, dtype=np.float64)
    floor = outflow[0] if outflow_floor_m3s is None else outflow_floor_m3s
    first = int(_position(outflow.tolist(), max(float(floor), float(outflow[0]))))
    last = len(outflow) - 1
    if outflow_cap_m3s is not None:
        last = min(int(np.searchsorted(outflow, outflow_cap_m3s, side="left")), last)
    rise = np.diff(outflow)[first:last]
    held = np.diff(storage)[first:last]
    counted = rise > 0.0
    if not counted.any():
        return math.inf
    seconds = 2.0 * float((held[counted] / rise[counted]).min()) / subreaches
    return seconds / _SECONDS_PER_MINUTE


@dataclass(frozen=True)
class _Plan:
    """The time step of a run: its sub-steps, and the limit it was chosen from."""

    substeps: int
    limit_min: float
    notices: tuple[RoutingNotice, ...] = ()


class _TableExit(Exception):
    """The state of a run left the working curve (internal; ends the run)."""

    def __init__(self, above: bool, index: int, working: float) -> None:
        super().__init__()
        self.above = above
        self.index = index
        self.working = working


def _position(outflow: list[float], value: float) -> float:
    """Return the row coordinate of the highest-storage point with this outflow.

    The coordinate is ``i + f``: row ``i`` and the fraction ``f`` of the way to row
    ``i + 1``. ``value`` is clamped to the outflows of the table; a flat stretch of the
    outflow rests at its last row.
    """
    index = bisect_right(outflow, value)
    if index == 0:
        return 0.0
    if index >= len(outflow):
        return float(len(outflow) - 1)
    low, high = outflow[index - 1], outflow[index]
    if low == value:
        return float(index - 1)
    return (index - 1) + (value - low) / (high - low)


def _route_pool(
    inflow: list[float],
    working: list[float],
    outflow: list[float],
    start: tuple[float, float, float],
    slack: float,
) -> tuple[list[float], list[float]]:
    """Route one pool: the recurrence of the working curve, ordinate by ordinate.

    Parameters
    ----------
    inflow : list of float
        Inflow ordinates [m3/s].
    working, outflow : list of float
        The working curve ``S/dt + O/2`` of each row (strictly rising) and the outflow.
    start : tuple of float
        Row coordinate, working-curve value and outflow of the first ordinate.
    slack : float
        How far beyond the first or last row the working curve may stray (rounding)
        before the run is ended; the value is then held at the end.

    Returns
    -------
    tuple of list
        The outflow and the row coordinate of every ordinate.

    Raises
    ------
    _TableExit
        When the working curve falls below the first row or rises above the last.
    """
    last = len(working) - 1
    bottom, top = working[0], working[last]
    position, state, discharge = start
    count = len(inflow)
    routed = [0.0] * count
    where = [0.0] * count
    routed[0], where[0] = discharge, position
    previous = inflow[0]
    for k in range(1, count):
        current = inflow[k]
        state += 0.5 * (previous + current) - discharge
        previous = current
        if state >= top:
            if state > top + slack:
                raise _TableExit(True, k, state)
            state, row = top, last - 1
        elif state <= bottom:
            if state < bottom - slack:
                raise _TableExit(False, k, state)
            state, row = bottom, 0
        else:
            row = bisect_right(working, state) - 1
        low = working[row]
        fraction = (state - low) / (working[row + 1] - low)
        discharge = outflow[row] + fraction * (outflow[row + 1] - outflow[row])
        routed[k], where[k] = discharge, row + fraction
    return routed, where


class LevelPoolReach(Reach):
    """Route a hydrograph through a reservoir or a reach by storage indication.

    The element is given by its storage-outflow table (and optionally the stage), which
    is how the stage-storage-discharge table of a pond, or the storage curve of a reach
    from a hydraulic model, arrives; see the module docstring for the method, the step
    rule and the range of the table. ``route`` returns the outflow and the storage at
    both ends; ``parameters`` of the result hold the numbers of sub-reaches and
    sub-steps, the longest step that meets the rule of NEH-630, the peak storage and
    its time and, with a stage, the peak stage and its time (the stage of the last
    sub-reach: the pool of a reservoir).

    Parameters
    ----------
    storage_m3 : array_like
        Storage [m3] of each row of the table, not decreasing, not negative; measured
        from the first row, which is the empty state.
    outflow_m3s : array_like
        Outflow [m3/s] of each row, not decreasing, not negative; ``0`` below a crest.
    stage_m : array_like, optional
        Water level [m] of each row, not decreasing (an elevation or a depth).
    subreaches : int, optional
        Number of sub-reaches in series, each holding ``S / N``; at least 1, by default
        1 (a pond or a reservoir).

    Raises
    ------
    InvalidParameterError
        If the table breaks a rule of :func:`check_rating` (``details.option``
        ``storage_m3``, ``outflow_m3s`` or ``stage_m``, ``details.reason`` the rule) or
        ``subreaches`` is not a whole number of at least 1. Routing raises it, with
        ``details.reason`` ``unstable_timestep``, when more than 100 sub-steps would be
        needed, and with ``details.option`` ``initial_outflow_m3s`` when the initial
        outflow is outside the table.
    CalculationError
        When routing fills the reservoir beyond the last row of the table
        (``details.reason`` ``table_exceeded``) or empties it below the first
        (``table_emptied``).

    Examples
    --------
    A pond that stores 3,600 m3 for each m3/s of outflow (a storage constant of one
    hour) and a flood of 10 m3/s at its peak:

    >>> from hydrolog.routing import Hydrograph, LevelPoolReach
    >>> pond = LevelPoolReach(storage_m3=[0, 360000], outflow_m3s=[0, 100])
    >>> flood = Hydrograph.from_step([0.0, 5.0, 10.0, 5.0, 0.0], timestep_min=60.0)
    >>> result = pond.route(flood)
    >>> round(result.outflow.peak_discharge_m3s, 3), result.outflow.time_to_peak_min
    (6.852, 180.0)
    """

    model = "level-pool"

    def __init__(
        self,
        storage_m3: ArrayLike,
        outflow_m3s: ArrayLike,
        stage_m: ArrayLike | None = None,
        subreaches: int = 1,
    ) -> None:
        """Create the element."""
        storage, outflow, stage = rating_arrays(storage_m3, outflow_m3s, stage_m)
        self.subreaches = whole_number(subreaches, "subreaches")
        self.storage_m3 = storage
        self.outflow_m3s = outflow
        self.stage_m = stage
        for table in (storage, outflow, stage):
            if table is not None:
                table.flags.writeable = False
        self._outflow_values = outflow.tolist()
        self._rows = np.arange(len(outflow), dtype=np.float64)

    def _start(self, initial_outflow_m3s: float) -> float:
        """Return the row coordinate of the state at rest with this outflow."""
        lowest, highest = self._outflow_values[0], self._outflow_values[-1]
        slack = _TOLERANCE * max(highest, 1.0)
        given = (
            f"The initial outflow of {initial_outflow_m3s:g} m3/s (the first inflow "
            "ordinate unless initial_outflow_m3s is given)"
        )
        if initial_outflow_m3s < lowest - slack:
            raise InvalidParameterError(
                f"Option 'initial_outflow_m3s': {given} is below the first outflow of "
                f"the table ({lowest:g} m3/s)",
                details={
                    "option": "initial_outflow_m3s",
                    "reason": "minimum",
                    "minimum": lowest,
                    "value": initial_outflow_m3s,
                },
                hint="Give an initial outflow inside the table, or start the table "
                "lower.",
            )
        if initial_outflow_m3s > highest + slack:
            raise InvalidParameterError(
                f"Option 'initial_outflow_m3s': {given} is above the last outflow of "
                f"the table ({highest:g} m3/s)",
                details={
                    "option": "initial_outflow_m3s",
                    "reason": "maximum",
                    "maximum": highest,
                    "value": initial_outflow_m3s,
                },
                hint="Give an initial outflow inside the table, or extend the table.",
            )
        clamped = min(max(initial_outflow_m3s, lowest), highest)
        return _position(self._outflow_values, clamped)

    def _plan(self, inflow: Hydrograph, initial_outflow_m3s: float) -> _Plan:
        """Divide the step when the table has a storage constant shorter than it."""
        step_min = inflow.timestep_min
        cap = max(inflow.peak_discharge_m3s, initial_outflow_m3s)
        floor = min(float(inflow.discharge_m3s.min()), initial_outflow_m3s)
        limit = timestep_limit_min(
            self.storage_m3,
            self.outflow_m3s,
            subreaches=self.subreaches,
            outflow_floor_m3s=floor,
            outflow_cap_m3s=cap,
        )
        if limit <= 0.0:
            raise InvalidParameterError(
                "Option 'storage_m3': a segment of the table between the lowest and "
                f"the highest flow of the run ({floor:g} to {cap:g} m3/s) holds no "
                "storage, so no time step keeps the working curve S/dt + O/2 valid",
                details={
                    "option": "storage_m3",
                    "reason": "working_curve",
                    "minimum_outflow_m3s": floor,
                    "maximum_outflow_m3s": cap,
                },
                hint="Give the table some storage where the outflow rises.",
            )
        if step_min <= limit * (1.0 + _TOLERANCE):
            return _Plan(1, limit)
        substeps = math.ceil(step_min / limit * (1.0 - _TOLERANCE))
        reaches = (
            f"each of {self.subreaches} sub-reaches"
            if self.subreaches > 1
            else "the pool"
        )
        if substeps > MAX_SUBSTEPS:
            raise InvalidParameterError(
                f"Option 'times_min': the time step of {step_min:g} min is too long "
                f"for the table: the storage constant dS/dO of {reaches} is as short "
                f"as {limit / 2:g} min, so the step may be at most {limit:g} min (for "
                f"flows from {floor:g} to {cap:g} m3/s), which would need {substeps} "
                f"sub-steps (at most {MAX_SUBSTEPS})",
                details={
                    "option": "times_min",
                    "reason": "unstable_timestep",
                    "timestep_min": step_min,
                    "maximum_timestep_min": limit,
                    "substeps": substeps,
                    "maximum_substeps": MAX_SUBSTEPS,
                },
                hint=f"Use a time step of at most {limit:g} min, fewer subreaches, or "
                "a table with a gentler slope.",
            )
        refined = (len(inflow) - 1) * substeps + 1
        if refined > MAX_ORDINATES:
            raise InvalidParameterError(
                f"Option 'times_min': the time step of {step_min:g} min has to be "
                f"divided into {substeps} parts for this table, which gives {refined} "
                f"ordinates (at most {MAX_ORDINATES})",
                details={
                    "option": "times_min",
                    "reason": "unstable_timestep",
                    "timestep_min": step_min,
                    "maximum_timestep_min": limit,
                    "substeps": substeps,
                    "maximum": MAX_ORDINATES,
                },
                hint="Use a shorter hydrograph or a time step of at most "
                f"{limit:g} min.",
            )
        notice = RoutingNotice(
            "timestep_refined",
            f"The storage constant dS/dO of {reaches} is as short as {limit / 2:g} min "
            f"for flows from {floor:g} to {cap:g} m3/s, so a time step above "
            f"{limit:g} min makes the working curve S/dt + O/2 lie left of the line of "
            "equal values (NEH-630 chapter 17: negative or overshooting outflows). "
            f"Each {step_min:g} min step was divided into {substeps} sub-steps of "
            f"{step_min / substeps:g} min (the inflow is interpolated linearly, the "
            "outflow is read at the original ordinates, so the volume balance has a "
            "sampling error).",
        )
        return _Plan(substeps, limit, (notice,))

    def _exit_error(
        self, leave: _TableExit, fine: Hydrograph, reach: int
    ) -> CalculationError:
        """Describe a run that left the table."""
        time = float(fine.times_min[leave.index])
        where = (
            f" in sub-reach {reach} of {self.subreaches}" if self.subreaches > 1 else ""
        )
        if leave.above:
            row = len(self._outflow_values) - 1
            return CalculationError(
                f"The flood fills the reservoir beyond the last row of its table at "
                f"t = {time:g} min{where} (storage {self.storage_m3[row]:g} m3, "
                f"outflow {self._outflow_values[row]:g} m3/s)",
                details={
                    "reason": "table_exceeded",
                    "time_min": time,
                    "maximum_storage_m3": float(self.storage_m3[row]),
                    "maximum_outflow_m3s": self._outflow_values[row],
                },
                hint="Extend the table above the highest storage the flood reaches "
                "(up to overtopping), or route a smaller flood.",
            )
        return CalculationError(
            f"The outflow empties the reservoir below the first row of its table at "
            f"t = {time:g} min{where} (storage {self.storage_m3[0]:g} m3, outflow "
            f"{self._outflow_values[0]:g} m3/s)",
            details={
                "reason": "table_emptied",
                "time_min": time,
                "minimum_storage_m3": float(self.storage_m3[0]),
                "minimum_outflow_m3s": self._outflow_values[0],
            },
            hint="Start the table at the empty state (zero outflow), or give an "
            "inflow that stays above the first outflow of the table.",
        )

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        reaches = self.subreaches
        start = self._start(initial_outflow_m3s)
        plan = self._plan(inflow, initial_outflow_m3s)
        fine = inflow.refined(plan.substeps)
        step_s = fine.timestep_min * _SECONDS_PER_MINUTE

        # the working curve of one sub-reach, which holds S / N
        held = self.storage_m3 / reaches
        working = held / step_s + 0.5 * self.outflow_m3s
        if not (np.diff(working) > 0.0).all():
            raise InvalidParameterError(
                "Option 'storage_m3': two rows of the table give the same working "
                f"curve at a step of {fine.timestep_min:g} min (rows too close to tell "
                "apart)",
                details={"option": "storage_m3", "reason": "repeated_row"},
                hint="Remove the near-duplicate row.",
            )
        first = (
            start,
            float(np.interp(start, self._rows, working)),
            initial_outflow_m3s,
        )
        slack = _TOLERANCE * max(float(working[-1]), 1.0)

        series = fine.discharge_m3s.tolist()
        stored = np.zeros(len(fine))
        where: list[float] = []
        for reach in range(1, reaches + 1):
            try:
                series, where = _route_pool(
                    series, working.tolist(), self._outflow_values, first, slack
                )
            except _TableExit as leave:
                raise self._exit_error(leave, fine, reach) from None
            stored += np.interp(where, self._rows, held)
        outflow = np.array(series)

        steady = _position(self._outflow_values, float(fine.discharge_m3s[-1]))
        parameters: dict[str, float] = {
            "subreaches": reaches,
            "substeps": plan.substeps,
        }
        if math.isfinite(plan.limit_min):
            parameters["timestep_limit_min"] = plan.limit_min
        peak = int(np.argmax(stored))
        parameters["storage_peak_m3"] = float(stored[peak])
        parameters["storage_peak_time_min"] = float(fine.times_min[peak])
        if self.stage_m is not None:
            levels = np.interp(where, self._rows, self.stage_m)
            top = int(np.argmax(levels))
            parameters["stage_peak_m"] = float(levels[top])
            parameters["stage_peak_time_min"] = float(fine.times_min[top])
        return ReachRun(
            outflow_m3s=outflow[:: plan.substeps],
            storage_start_m3=reaches * float(np.interp(start, self._rows, held)),
            storage_end_m3=float(stored[-1]),
            storage_steady_m3=reaches * float(np.interp(steady, self._rows, held)),
            parameters=parameters,
            notices=plan.notices,
        )
