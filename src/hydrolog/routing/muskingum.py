"""Muskingum routing: wedge storage, with sub-reaches inside the positivity window.

The storage of a reach is ``S = K [X I + (1 - X) O]`` (``K`` the travel time, ``X`` the
weight of the inflow, 0 for a linear reservoir and 0.5 for a wave that does not
attenuate). With the trapezoid rule for the continuity equation it gives the
three-point recurrence of :func:`~hydrolog.routing._kernels.muskingum_coefficients`.
The weights are all non-negative only when ``|2KX| <= dt <= 2K(1 - X)``; outside that
window a non-negative inflow can give a negative outflow (ADR-0008).

A reach is split into ``N`` equal sub-reaches of ``K / N`` in series, each with the
same ``X`` (HEC-HMS). The splitting keeps the weights inside the window, and by the
rule of thumb ``N = K / dt`` the travel time of a sub-reach is one time step. When no
whole ``N`` fits the window the time step is divided into equal sub-steps instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import in_range, positive, whole_number
from hydrolog.routing._kernels import route_muskingum_cascade
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.reach import MAX_ORDINATES, Reach, ReachRun, RoutingNotice

__all__ = ["MAX_SUBSTEPS", "MuskingumReach", "subreach_window"]

MAX_SUBSTEPS = 100
"""Largest number of sub-steps a time step is divided into to find a window."""

_ROUNDING = 1e-9
_SECONDS_PER_MINUTE = 60.0


def subreach_window(k_min: float, x: float, step_min: float) -> tuple[int, int]:
    """Return the numbers of sub-reaches that keep every weight non-negative.

    A sub-reach of ``K / N`` has non-negative weights when
    ``|2 (K / N) X| <= dt <= 2 (K / N) (1 - X)``, that is for
    ``2KX / dt <= N <= 2K(1 - X) / dt``. The window is symmetric about ``K / dt`` (the
    rule-of-thumb number of sub-reaches), and a whole number on its border is inside
    it to rounding.

    Parameters
    ----------
    k_min : float
        Travel time ``K`` of the whole reach [min], > 0.
    x : float
        Weighting factor ``X``, 0 to 0.5.
    step_min : float
        Time step [min], > 0.

    Returns
    -------
    tuple of int
        The smallest (at least 1) and the largest number of sub-reaches; the window is
        empty, and no whole number fits, when the first exceeds the second.
    """
    lowest = max(1, math.ceil(2.0 * k_min * x / step_min * (1.0 - _ROUNDING)))
    highest = math.floor(2.0 * k_min * (1.0 - x) / step_min * (1.0 + _ROUNDING))
    return lowest, highest


def _rule_of_thumb(k_min: float, step_min: float) -> int:
    """Return the number of sub-reaches whose travel time is nearest to one step."""
    return max(1, math.floor(k_min / step_min + 0.5))


def _reaches(lowest: int, highest: int | None = None) -> str:
    """Return the number or range of sub-reaches in words: ``3 to 9 sub-reaches``."""
    if highest is not None and highest != lowest:
        return f"{lowest} to {highest} sub-reaches"
    return "1 sub-reach" if lowest == 1 else f"{lowest} sub-reaches"


@dataclass(frozen=True)
class _Plan:
    """How the scheme runs on a time axis: sub-reaches and sub-steps per step."""

    subreaches: int
    substeps: int
    notices: tuple[RoutingNotice, ...] = ()


class MuskingumReach(Reach):
    """Route a hydrograph through a reach with the Muskingum method.

    The outflow follows from ``S = K [X I + (1 - X) O]`` and continuity, solved with
    the trapezoid rule over ``N`` equal sub-reaches of ``K / N`` (more sub-reaches mean
    less attenuation). Every sub-reach starts with the initial outflow.

    Unless ``subreaches`` is given, ``N`` is the rule of thumb ``K / dt``, the nearest
    whole number, which always lies inside the window of non-negative weights when the
    window holds any whole number (:func:`subreach_window`). When it holds none (``K``
    short for the step, or ``X`` close to 0.5 with ``K / dt`` not a whole number) every
    time step is divided into the fewest equal sub-steps that give a window, the
    inflow is interpolated linearly, the outflow is read at the original ordinates, and
    the notice ``substeps_added`` says so; the volume balance then has a sampling
    error. A ``subreaches`` that the caller gives is never changed.

    Parameters
    ----------
    k_min : float
        Travel time of the reach ``K`` [min], > 0 and finite.
    x : float
        Weighting factor ``X``, 0 (linear reservoir, maximum attenuation) to 0.5
        (no attenuation).
    subreaches : int, optional
        Number of equal sub-reaches, at least 1; default ``K / dt``.

    Raises
    ------
    InvalidParameterError
        If ``k_min``, ``x`` or ``subreaches`` is not valid. Routing raises it, with
        ``details.reason`` ``unstable_timestep``, when ``subreaches`` is outside the
        window of the time step of the hydrograph or when ``K`` is so short that
        :data:`MAX_SUBSTEPS` sub-steps do not give a window.

    Examples
    --------
    The example of the University of Iowa (``K`` = 20 h, ``X`` = 0.25, ``dt`` = 12 h):

    >>> from hydrolog.routing import Hydrograph, MuskingumReach
    >>> inflow = Hydrograph.from_step([100.0, 300.0, 680.0, 500.0], 720.0)
    >>> reach = MuskingumReach(k_min=1200.0, x=0.25, subreaches=1)
    >>> reach.route(inflow, extend_min=0.0).outflow.discharge_m3s.round(1).tolist()
    [100.0, 109.5, 236.5, 481.3]
    """

    model = "muskingum"

    def __init__(self, k_min: float, x: float, subreaches: int | None = None) -> None:
        """Create the element."""
        self.k_min = positive(k_min, "k_min")
        self.x = in_range(x, "x", minimum=0.0, maximum=0.5)
        self.subreaches = (
            None if subreaches is None else whole_number(subreaches, "subreaches")
        )

    def _explicit_plan(self, count: int, step_min: float) -> _Plan:
        """Check the given number of sub-reaches against the window of the step."""
        lowest, highest = subreach_window(self.k_min, self.x, step_min)
        if lowest <= count <= highest:
            return _Plan(count, 1)
        if lowest <= highest:
            problem = (
                f"the weights stay non-negative only for {_reaches(lowest, highest)}"
            )
            hint = f"Give {_reaches(lowest, highest)}, or leave subreaches out."
        else:
            problem = "no whole number of sub-reaches keeps the weights non-negative"
            hint = (
                "Leave subreaches out and the step is divided, or use a shorter step."
            )
        raise InvalidParameterError(
            f"Option 'subreaches': {count} sub-reaches of K / N = "
            f"{self.k_min / count:g} min are outside the window of a {step_min:g} min "
            f"step (K = {self.k_min:g} min, X = {self.x:g}): {problem}",
            details={
                "option": "subreaches",
                "reason": "unstable_timestep",
                "value": count,
                "minimum": lowest,
                "maximum": highest,
                "timestep_min": step_min,
            },
            hint=hint,
        )

    def _plan(self, step_min: float, ordinates: int) -> _Plan:
        """Choose the sub-reaches, and the sub-steps when no whole number fits."""
        if self.subreaches is not None:
            return self._explicit_plan(self.subreaches, step_min)
        lowest, highest = subreach_window(self.k_min, self.x, step_min)
        if lowest <= highest:
            return _Plan(_rule_of_thumb(self.k_min, step_min), 1)
        for substeps in range(2, MAX_SUBSTEPS + 1):
            lowest, highest = subreach_window(self.k_min, self.x, step_min / substeps)
            if lowest <= highest:
                break
        else:
            raise InvalidParameterError(
                f"Option 'k_min': {self.k_min:g} min is too short for a time step of "
                f"{step_min:g} min with X = {self.x:g}: no whole number of sub-reaches "
                f"keeps the weights non-negative even on a step divided into "
                f"{MAX_SUBSTEPS} parts",
                details={
                    "option": "k_min",
                    "reason": "unstable_timestep",
                    "value": self.k_min,
                    "timestep_min": step_min,
                    "maximum_substeps": MAX_SUBSTEPS,
                },
                hint="Use a shorter time step or a longer K (for X = 0.5, K must be "
                "a whole number of steps); route lag has no storage.",
            )
        refined = (ordinates - 1) * substeps + 1
        if refined > MAX_ORDINATES:
            raise InvalidParameterError(
                f"Option 'k_min': {self.k_min:g} min is short for a time step of "
                f"{step_min:g} min with X = {self.x:g}: the step has to be divided "
                f"into {substeps} parts, which gives {refined} ordinates (at most "
                f"{MAX_ORDINATES})",
                details={
                    "option": "k_min",
                    "reason": "unstable_timestep",
                    "value": self.k_min,
                    "timestep_min": step_min,
                    "substeps": substeps,
                    "maximum": MAX_ORDINATES,
                },
                hint="Use a shorter hydrograph, a shorter time step or a longer K.",
            )
        count = _rule_of_thumb(self.k_min, step_min / substeps)
        reaches = _reaches(count)
        notice = RoutingNotice(
            "substeps_added",
            f"No whole number of sub-reaches keeps the weights of K = "
            f"{self.k_min:g} min and X = {self.x:g} non-negative on a "
            f"{step_min:g} min step. Each step was divided into {substeps} sub-steps "
            f"of {step_min / substeps:g} min, with {reaches} of K / N: the inflow is "
            "interpolated linearly and the outflow is read at the original ordinates, "
            "so the volume balance has a sampling error.",
        )
        return _Plan(count, substeps, (notice,))

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        plan = self._plan(inflow.timestep_min, len(inflow))
        fine = inflow.refined(plan.substeps)
        step = fine.timestep_min
        run = route_muskingum_cascade(
            fine.discharge_m3s,
            self.k_min / plan.subreaches,
            self.x,
            step,
            plan.subreaches,
            initial_outflow_m3s,
        )
        lowest, highest = subreach_window(self.k_min, self.x, step)
        return ReachRun(
            outflow_m3s=run.outflow[:: plan.substeps],
            storage_start_m3=run.storage_start * _SECONDS_PER_MINUTE,
            storage_end_m3=run.storage_end * _SECONDS_PER_MINUTE,
            storage_steady_m3=run.storage_steady * _SECONDS_PER_MINUTE,
            parameters={
                "k_min": self.k_min,
                "x": self.x,
                "subreaches": plan.subreaches,
                "substeps": plan.substeps,
                "c_current": run.weights[0],
                "c_previous": run.weights[1],
                "c_outflow": run.weights[2],
                "subreaches_min": lowest,
                "subreaches_max": highest,
            },
            notices=plan.notices,
        )
