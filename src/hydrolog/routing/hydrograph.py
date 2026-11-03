"""The hydrograph table: a discharge series at a regular time step.

:class:`Hydrograph` is what every routing model takes and gives (ADR-0008): ordinates
``discharge_m3s`` [m3/s] at ``times_min`` [min], at a strictly regular step, never
negative. It is immutable. The step is the one place where a routing scheme meets the
data, so an irregular table is rejected instead of being resampled silently.

:func:`check_table` finds the first problem of two arrays without raising, so that the
file loader can report it as a data error and the class as a validation error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import as_array

__all__ = ["STEP_TOLERANCE", "Hydrograph", "TableProblem", "check_table"]

STEP_TOLERANCE = 1e-6
"""Largest deviation of a step from the mean step of a regular table, relative to it."""

_SECONDS_PER_MINUTE = 60.0


@dataclass(frozen=True)
class TableProblem:
    """The first problem of a hydrograph table.

    Attributes
    ----------
    option : str
        The option the problem belongs to: ``"times_min"`` or ``"discharge_m3s"``.
    reason : str
        ``type``, ``length_mismatch``, ``too_short``, ``not_finite``,
        ``not_increasing``, ``irregular_step`` or ``negative``.
    message : str
        English description.
    details : dict
        JSON-compatible facts (``index`` of the first offending ordinate, ...).
    """

    option: str
    reason: str
    message: str
    details: dict[str, Any]


def check_table(
    times_min: NDArray[np.float64], discharge_m3s: NDArray[np.float64]
) -> TableProblem | None:
    """Find the first problem of a hydrograph table.

    Parameters
    ----------
    times_min : numpy.ndarray
        Times [min].
    discharge_m3s : numpy.ndarray
        Discharges [m3/s].

    Returns
    -------
    TableProblem or None
        The first violated rule in the order: one-dimensional arrays, equal lengths, at
        least two ordinates, finite values, strictly increasing times, a regular step
        (every step within :data:`STEP_TOLERANCE` of the mean step), discharges not
        negative; ``None`` when the table is valid.
    """
    if times_min.ndim != 1:
        return TableProblem(
            "times_min", "type", "times_min must be a flat list of numbers", {}
        )
    if discharge_m3s.ndim != 1:
        return TableProblem(
            "discharge_m3s", "type", "discharge_m3s must be a flat list of numbers", {}
        )
    n_times, n_values = len(times_min), len(discharge_m3s)
    if n_times != n_values:
        return TableProblem(
            "discharge_m3s",
            "length_mismatch",
            f"{n_values} discharges for {n_times} times",
            {"times": n_times, "discharges": n_values},
        )
    if n_times < 2:
        return TableProblem(
            "times_min",
            "too_short",
            "a hydrograph needs at least two ordinates to have a time step",
            {"ordinates": n_times},
        )
    for name, values in (("times_min", times_min), ("discharge_m3s", discharge_m3s)):
        broken = ~np.isfinite(values)
        if broken.any():
            index = int(np.argmax(broken))
            return TableProblem(
                name,
                "not_finite",
                f"{name}[{index}] is not a finite number",
                {"index": index},
            )
    steps = np.diff(times_min)
    backwards = steps <= 0.0
    if backwards.any():
        index = int(np.argmax(backwards)) + 1
        return TableProblem(
            "times_min",
            "not_increasing",
            f"times_min must increase strictly; times_min[{index}] = "
            f"{times_min[index]:g} does not follow {times_min[index - 1]:g}",
            {"index": index},
        )
    mean_step = float(times_min[-1] - times_min[0]) / (n_times - 1)
    irregular = np.abs(steps - mean_step) > STEP_TOLERANCE * mean_step
    if irregular.any():
        index = int(np.argmax(irregular)) + 1
        return TableProblem(
            "times_min",
            "irregular_step",
            f"the time step must be regular: the mean step is {mean_step:g} min but "
            f"times_min[{index}] follows its predecessor after "
            f"{steps[index - 1]:g} min",
            {
                "index": index,
                "expected_step_min": mean_step,
                "found_step_min": float(steps[index - 1]),
            },
        )
    negative = discharge_m3s < 0.0
    if negative.any():
        index = int(np.argmax(negative))
        return TableProblem(
            "discharge_m3s",
            "negative",
            f"discharge_m3s must not be negative; discharge_m3s[{index}] = "
            f"{discharge_m3s[index]:g}",
            {"index": index, "value": float(discharge_m3s[index])},
        )
    return None


@dataclass(frozen=True, eq=False, init=False)
class Hydrograph(JsonResultMixin):
    """A discharge hydrograph at a regular time step.

    Parameters
    ----------
    times_min : array_like
        Times of the ordinates [min], strictly increasing at a regular step (every
        step within :data:`STEP_TOLERANCE` of the mean step); at least two.
    discharge_m3s : array_like
        Discharge at each time [m3/s]; finite and not negative.

    Attributes
    ----------
    times_min : numpy.ndarray
        The times (a read-only copy).
    discharge_m3s : numpy.ndarray
        The discharges (a read-only copy).

    Raises
    ------
    InvalidParameterError
        If the table breaks a rule of :func:`check_table`; ``details.option`` is
        ``times_min`` or ``discharge_m3s`` and ``details.reason`` the rule.

    Examples
    --------
    >>> hydrograph = Hydrograph([0.0, 30.0, 60.0], [0.0, 12.0, 4.0])
    >>> hydrograph.peak_discharge_m3s, hydrograph.time_to_peak_min
    (12.0, 30.0)
    >>> hydrograph.volume_m3
    25200.0
    """

    times_min: NDArray[np.float64]
    discharge_m3s: NDArray[np.float64]

    def __init__(self, times_min: ArrayLike, discharge_m3s: ArrayLike) -> None:
        """Validate the table and keep read-only copies of the arrays."""
        times = as_array(times_min, "times_min")
        discharge = as_array(discharge_m3s, "discharge_m3s")
        problem = check_table(times, discharge)
        if problem is not None:
            raise InvalidParameterError(
                f"Option {problem.option!r}: {problem.message}",
                details={
                    "option": problem.option,
                    "reason": problem.reason,
                    **problem.details,
                },
            )
        times.flags.writeable = False
        discharge.flags.writeable = False
        object.__setattr__(self, "times_min", times)
        object.__setattr__(self, "discharge_m3s", discharge)

    @classmethod
    def from_step(
        cls, discharge_m3s: ArrayLike, timestep_min: float, start_min: float = 0.0
    ) -> Hydrograph:
        """Build a hydrograph from its ordinates and a step.

        Parameters
        ----------
        discharge_m3s : array_like
            Discharges [m3/s].
        timestep_min : float
            Time step [min], > 0.
        start_min : float, optional
            Time of the first ordinate [min], by default 0.

        Returns
        -------
        Hydrograph
            ``times_min = start_min + timestep_min * [0, 1, ...]``.
        """
        discharge = as_array(discharge_m3s, "discharge_m3s")
        return cls(start_min + timestep_min * np.arange(len(discharge)), discharge)

    def __len__(self) -> int:
        """Return the number of ordinates."""
        return len(self.times_min)

    @property
    def timestep_min(self) -> float:
        """float: the time step [min] (the mean step of the table)."""
        return float(self.times_min[-1] - self.times_min[0]) / (len(self) - 1)

    @property
    def start_min(self) -> float:
        """float: time of the first ordinate [min]."""
        return float(self.times_min[0])

    @property
    def duration_min(self) -> float:
        """float: time from the first to the last ordinate [min]."""
        return float(self.times_min[-1] - self.times_min[0])

    @property
    def peak_discharge_m3s(self) -> float:
        """float: the largest ordinate [m3/s]."""
        return float(self.discharge_m3s.max())

    @property
    def time_to_peak_min(self) -> float:
        """float: time of the first largest ordinate [min]."""
        return float(self.times_min[int(np.argmax(self.discharge_m3s))])

    @property
    def volume_m3(self) -> float:
        """float: volume under the hydrograph by the trapezoid rule [m3]."""
        values = self.discharge_m3s
        area = 0.5 * (values[0] + values[-1]) + values[1:-1].sum()
        return float(area) * self.timestep_min * _SECONDS_PER_MINUTE

    def extended(self, steps: int, value: float | None = None) -> Hydrograph:
        """Return the hydrograph with ordinates added after the last one.

        Parameters
        ----------
        steps : int
            Number of ordinates to add; zero or less returns this hydrograph.
        value : float, optional
            Discharge of the added ordinates [m3/s]; default the last ordinate (the
            inflow is held).

        Returns
        -------
        Hydrograph
            The same times followed by ``steps`` more at the same step.
        """
        if steps <= 0:
            return self
        level = float(self.discharge_m3s[-1]) if value is None else value
        added = self.times_min[-1] + self.timestep_min * np.arange(1, steps + 1)
        return Hydrograph(
            np.concatenate([self.times_min, added]),
            np.concatenate([self.discharge_m3s, np.full(steps, level)]),
        )

    def refined(self, factor: int) -> Hydrograph:
        """Return the hydrograph on a step ``factor`` times shorter.

        The new ordinates lie on the straight lines between the old ones, so the volume
        is unchanged and the old ordinates are reproduced exactly.

        Parameters
        ----------
        factor : int
            Number of new steps per old step, at least 1.

        Returns
        -------
        Hydrograph
            ``(n - 1) * factor + 1`` ordinates.
        """
        if factor <= 1:
            return self
        values = self.discharge_m3s
        weights = np.tile(np.arange(factor) / factor, len(values) - 1)
        fine = np.repeat(values[:-1], factor) + np.repeat(np.diff(values), factor) * (
            weights
        )
        step = self.timestep_min / factor
        count = (len(values) - 1) * factor + 1
        return Hydrograph(
            self.start_min + step * np.arange(count), np.append(fine, values[-1])
        )

    def coarsened(self, factor: int) -> Hydrograph:
        """Return every ``factor``-th ordinate (the inverse of :meth:`refined`).

        Parameters
        ----------
        factor : int
            Take every ``factor``-th ordinate; ``n - 1`` must be a multiple of it.

        Returns
        -------
        Hydrograph
            ``(n - 1) / factor + 1`` ordinates.

        Raises
        ------
        InvalidParameterError
            If ``n - 1`` is not a multiple of ``factor``.
        """
        if factor <= 1:
            return self
        if (len(self) - 1) % factor:
            raise InvalidParameterError(
                f"{len(self) - 1} steps cannot be divided into groups of {factor}",
                details={"option": "factor", "reason": "indivisible"},
            )
        return Hydrograph(self.times_min[::factor], self.discharge_m3s[::factor])

    def to_table(self) -> str:
        r"""Return the table as CSV text, a row per ordinate.

        Returns
        -------
        str
            ``time_min,discharge_m3s`` and the rows; UTF-8, ``"\n"`` line ends, every
            number in its shortest exact form (it reads back unchanged), the format of
            the hydrograph tables that the ``route`` commands read and write.
        """
        rows = [
            f"{time!r},{value!r}"
            for time, value in zip(
                self.times_min.tolist(), self.discharge_m3s.tolist(), strict=True
            )
        ]
        return "\n".join(["time_min,discharge_m3s", *rows]) + "\n"
