"""Routing elements: the base class, the result and the notices of a run.

A :class:`Reach` turns an inflow :class:`~hydrolog.routing.hydrograph.Hydrograph` into
an outflow hydrograph. A subclass implements one thing, ``_run``: its recurrence on a
given time axis. :meth:`Reach.route` does what every model shares (ADR-0008): the
initial condition, the extension of the time axis until the outflow has settled, the
non-negativity check and the notices, and returns a :class:`RoutingResult` with the
volume balance.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing.hydrograph import Hydrograph

__all__ = [
    "MAX_ORDINATES",
    "MIN_EXTENSION_STEPS",
    "TAIL_TOLERANCE",
    "Reach",
    "ReachRun",
    "RoutingNotice",
    "RoutingResult",
]

TAIL_TOLERANCE = 1e-3
"""The outflow has settled when it stays this close to the final inflow, relative to
the inflow peak."""
MIN_EXTENSION_STEPS = 100
"""The automatic extension is at most ten times the inflow duration, and at least this
many steps."""
MAX_ORDINATES = 1_000_000
"""Largest number of ordinates of a routed hydrograph."""

_ROUNDING = 1e-9
"""Relative slack for whole numbers of steps and for the sign of the outflow."""
_SECONDS_PER_MINUTE = 60.0

NoticeLevel = Literal["info", "warning"]


@dataclass(frozen=True)
class RoutingNotice:
    """A non-fatal observation of a routing run.

    Attributes
    ----------
    code : str
        Stable ``snake_case`` identifier (``tail_extended``, ``substeps_added``...).
    message : str
        English description.
    level : {"info", "warning"}
        ``"warning"`` when the result may not be what the caller wants.
    """

    code: str
    message: str
    level: NoticeLevel = "info"


@dataclass(frozen=True)
class ReachRun:
    """What a model computes on one time axis.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow ordinates [m3/s], one per ordinate of the inflow it was given.
    storage_start_m3, storage_end_m3 : float
        Water stored in the element at the first and at the last ordinate [m3].
    storage_steady_m3 : float
        Water the element would hold at rest under the final inflow ordinate [m3]; the
        run has released its inflow when the end storage has come back to it.
    parameters : dict of str to float
        The parameters the run used, including the ones the model derived (the number
        of sub-reaches, the coefficients...).
    notices : tuple of RoutingNotice
        Observations of the model (an interpolated lag, added sub-reaches...).
    """

    outflow_m3s: NDArray[np.float64]
    storage_start_m3: float
    storage_end_m3: float
    storage_steady_m3: float
    parameters: dict[str, float]
    notices: tuple[RoutingNotice, ...] = ()


@dataclass
class RoutingResult(JsonResultMixin):
    """The outcome of routing one hydrograph through one element.

    Attributes
    ----------
    model : str
        Name of the model (``"lag"``, ``"muskingum"``...).
    parameters : dict of str to float
        The parameters used, including the derived ones.
    inflow : Hydrograph
        The inflow as given.
    outflow : Hydrograph
        The outflow on the time axis of the inflow, extended after its last ordinate
        when the outflow had not settled by then.
    storage_start_m3, storage_end_m3 : float
        Water stored in the element at the first and at the last ordinate [m3].
    notices : list of RoutingNotice
        Observations of the run.
    """

    model: str
    parameters: dict[str, float]
    inflow: Hydrograph
    outflow: Hydrograph
    storage_start_m3: float
    storage_end_m3: float
    notices: list[RoutingNotice] = field(default_factory=list)

    @property
    def extension_min(self) -> float:
        """float: time added after the last inflow ordinate [min]."""
        return (len(self.outflow) - len(self.inflow)) * self.inflow.timestep_min

    @property
    def volume_in_m3(self) -> float:
        """float: volume of the inflow as given [m3]."""
        return self.inflow.volume_m3

    @property
    def volume_out_m3(self) -> float:
        """float: volume of the outflow, extension included [m3]."""
        return self.outflow.volume_m3

    @property
    def storage_change_m3(self) -> float:
        """float: storage at the last ordinate minus storage at the first [m3]."""
        return self.storage_end_m3 - self.storage_start_m3

    @property
    def balance_error_m3(self) -> float:
        """float: inflow volume - outflow volume - change of storage [m3].

        The inflow is held at its last value over the extension, as the model saw it.
        It is zero to rounding, except that a run on a refined time step
        (``timestep_refined`` or ``substeps_added``) samples the outflow back at the
        original ordinates, which leaves the sampling error of the trapezoid rule.
        """
        held = self.inflow.extended(len(self.outflow) - len(self.inflow))
        return held.volume_m3 - self.outflow.volume_m3 - self.storage_change_m3

    @property
    def peak_attenuation_pct(self) -> float:
        """float: reduction of the peak, in percent of the inflow peak."""
        peak = self.inflow.peak_discharge_m3s
        if peak <= 0.0:
            return 0.0
        return 100.0 * (1.0 - self.outflow.peak_discharge_m3s / peak)

    @property
    def peak_delay_min(self) -> float:
        """float: time of the outflow peak minus time of the inflow peak [min]."""
        return self.outflow.time_to_peak_min - self.inflow.time_to_peak_min


def _initial_outflow(inflow: Hydrograph, given: float | None) -> float:
    """Return the given outflow at the first ordinate, else the inflow there."""
    if given is None:
        return float(inflow.discharge_m3s[0])
    if not math.isfinite(given):
        raise InvalidParameterError(
            f"Option 'initial_outflow_m3s': must be a finite number, got {given}",
            details={
                "option": "initial_outflow_m3s",
                "reason": "not_finite",
                "value": str(given),
            },
        )
    if given < 0.0:
        raise InvalidParameterError(
            f"Option 'initial_outflow_m3s': must be >= 0, got {given}",
            details={
                "option": "initial_outflow_m3s",
                "reason": "minimum",
                "minimum": 0.0,
                "value": given,
            },
        )
    return float(given)


def _explicit_extension(inflow: Hydrograph, extend_min: float) -> int:
    """Return the number of steps in an extension of ``extend_min`` (rounded up)."""
    if not math.isfinite(extend_min) or extend_min < 0.0:
        raise InvalidParameterError(
            f"Option 'extend_min': must be a finite number >= 0, got {extend_min}",
            details={
                "option": "extend_min",
                "reason": "minimum" if math.isfinite(extend_min) else "not_finite",
                "minimum": 0.0,
                "value": extend_min if math.isfinite(extend_min) else str(extend_min),
            },
        )
    steps = math.ceil(extend_min / inflow.timestep_min - _ROUNDING)
    steps = max(steps, 0)
    if len(inflow) + steps > MAX_ORDINATES:
        longest = (MAX_ORDINATES - len(inflow)) * inflow.timestep_min
        raise InvalidParameterError(
            f"Option 'extend_min': {extend_min:g} min would give more than "
            f"{MAX_ORDINATES} ordinates",
            details={
                "option": "extend_min",
                "reason": "maximum",
                "maximum": longest,
                "value": extend_min,
            },
            hint=f"Give at most {longest:g} min or use a longer time step.",
        )
    return steps


def _settled(inflow: Hydrograph, run: ReachRun) -> bool:
    """Whether the run has released the inflow: outflow and storage are at rest.

    The last outflow is within :data:`TAIL_TOLERANCE` of the final inflow, relative to
    the inflow peak, and the water still stored above its steady-state amount is below
    :data:`TAIL_TOLERANCE` of what had to be released (the inflow volume, or the
    excess the element started with when that is larger).
    """
    peak = inflow.peak_discharge_m3s
    if abs(run.outflow_m3s[-1] - inflow.discharge_m3s[-1]) > TAIL_TOLERANCE * peak:
        return False
    to_release = max(
        inflow.volume_m3, abs(run.storage_start_m3 - run.storage_steady_m3)
    )
    return (
        abs(run.storage_end_m3 - run.storage_steady_m3) <= TAIL_TOLERANCE * to_release
    )


class Reach(ABC):
    """A routing element: a hydrograph in, a hydrograph out.

    Subclasses set :attr:`model` and implement :meth:`_run`; :meth:`route` is the public
    entry point.

    Attributes
    ----------
    model : str
        Name of the model, the ``model`` of its results.
    """

    model: ClassVar[str]

    @abstractmethod
    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        """Route ``inflow`` on its own time axis.

        Parameters
        ----------
        inflow : Hydrograph
            The inflow, already extended by the caller when needed; the outflow of
            ordinate ``t`` must depend only on ordinates up to ``t`` (causality), so
            that a longer run extends a shorter one.
        initial_outflow_m3s : float
            Outflow at the first ordinate [m3/s].

        Returns
        -------
        ReachRun
            The outflow at every ordinate of ``inflow`` and the storage at both ends.
        """

    def route(
        self,
        inflow: Hydrograph,
        *,
        initial_outflow_m3s: float | None = None,
        extend_min: float | None = None,
    ) -> RoutingResult:
        """Route a hydrograph through the element.

        Parameters
        ----------
        inflow : Hydrograph
            The inflow.
        initial_outflow_m3s : float, optional
            Outflow at the first ordinate [m3/s], >= 0; default the first inflow
            ordinate (steady state).
        extend_min : float, optional
            Time to add after the last inflow ordinate, where the last inflow value is
            held [min], >= 0; ``0`` adds nothing. Default: as much as the element needs
            to release the inflow, that is until the outflow is within 0.1 % of the
            final inflow (relative to the inflow peak) and the water still stored above
            its steady amount is below 0.1 % of the inflow volume; at most ten times
            the inflow duration (and at least 100 steps).

        Returns
        -------
        RoutingResult
            The outflow, the storage at both ends, the balance and the notices
            (``tail_extended`` when time was added, ``tail_truncated`` when the outflow
            had still not settled at the end).

        Raises
        ------
        InvalidParameterError
            If ``initial_outflow_m3s`` or ``extend_min`` is not valid.
        CalculationError
            If the scheme gave a negative outflow (a model bug, not a user input).
        """
        initial = _initial_outflow(inflow, initial_outflow_m3s)
        if extend_min is None:
            steps, run, truncated = self._settle(inflow, initial)
        else:
            steps = _explicit_extension(inflow, extend_min)
            run = self._run(inflow.extended(steps), initial)
            truncated = not _settled(inflow, run)
        extended = inflow.extended(steps)
        outflow = self._outflow(extended, run)
        notices = list(run.notices)
        step = inflow.timestep_min
        if steps > 0:
            notices.append(
                RoutingNotice(
                    "tail_extended",
                    f"The time axis was extended by {steps * step:g} min after the "
                    "last inflow ordinate, which is held, for the outflow to settle.",
                )
            )
        if truncated:
            notices.append(
                RoutingNotice(
                    "tail_truncated",
                    "The outflow had not settled to within 0.1 % of the inflow peak "
                    f"at the end of the series ({extended.duration_min:g} min).",
                    "warning",
                )
            )
        return RoutingResult(
            model=self.model,
            parameters=run.parameters,
            inflow=inflow,
            outflow=outflow,
            storage_start_m3=run.storage_start_m3,
            storage_end_m3=run.storage_end_m3,
            notices=notices,
        )

    def _settle(self, inflow: Hydrograph, initial: float) -> tuple[int, ReachRun, bool]:
        """Find the shortest extension after which the inflow has been released.

        Returns the number of steps added, the run on that axis and whether the cap was
        reached before the outflow settled.
        """
        given = len(inflow)
        run = self._run(inflow, initial)
        if _settled(inflow, run):
            return 0, run, False
        cap = min(max(10 * (given - 1), MIN_EXTENSION_STEPS), MAX_ORDINATES - given)
        if cap <= 0:
            return 0, run, True
        # Grow the extension until the run has settled, then bisect for the shortest
        # one; ``short`` has not settled, ``long`` has (a settled run stays settled).
        short, long = 0, min(cap, max(given // 2, 10))
        while True:
            best = self._run(inflow.extended(long), initial)
            if _settled(inflow, best):
                break
            if long >= cap:
                return long, best, True
            short, long = long, min(cap, 2 * long)
        while long - short > 1:
            middle = (short + long) // 2
            trial = self._run(inflow.extended(middle), initial)
            if _settled(inflow, trial):
                long, best = middle, trial
            else:
                short = middle
        return long, best, False

    @staticmethod
    def _outflow(extended: Hydrograph, run: ReachRun) -> Hydrograph:
        """Return the outflow as a hydrograph; rounding below zero is removed."""
        values = run.outflow_m3s
        floor = -_ROUNDING * max(extended.peak_discharge_m3s, 1.0)
        if values.min() < floor:
            raise CalculationError(
                f"The scheme gave a negative outflow ({values.min():g} m3/s)",
                details={"reason": "negative_outflow", "value": float(values.min())},
                hint="Report the parameters: a routing scheme must not do this.",
            )
        return Hydrograph(extended.times_min, np.maximum(values, 0.0))
