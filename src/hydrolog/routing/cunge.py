"""Muskingum-Cunge routing with constant coefficients (the NRCS form).

Cunge (1969) chose the parameters of the Muskingum scheme so that its numerical
diffusion equals the physical diffusion of the flood wave. For a routing distance step
``dx`` and the reference discharge ``Q`` (NEH-630 chapter 17, eq. 17-20 to 17-22)::

    K = dx / c        X = (1 - Q / (T S0 c dx)) / 2

with ``c`` the celerity of the flood wave, ``T`` the top width and ``S0`` the slope.
The coefficients are constant for the whole run. The reach is divided into equal
distance steps of at most ``dx_c = (c dt + Q / (T S0 c)) / 2`` (eq. 17-21), each
routed as a Muskingum sub-reach (``route_muskingum_cascade``), so the volume is
conserved. ``X`` may be negative.

Two rules of NEH-630 are applied. The hydrograph must rise from 5 % of its peak to the
peak in at least 10 time steps, otherwise the step is divided (``timestep_refined``).
The grid Reynolds number ``Dg = 1 - 2X`` and the Courant number ``Cg = c dt / dx`` give
the accuracy limit ``Dg <= exp(2.3 Cg)``. Every distance step whose weights are
non-negative meets it (there ``|Cg - Dg| <= 1``), so the routing is never beyond it; the
notice ``accuracy_limit`` says that the step of the NRCS rule would have been beyond the
limit and was replaced (ADR-0008). It is not an error.

A reach for which no division of the reach and of the time step (into at most 100
parts) keeps the weights non-negative is not refused (ADR-0026). Typically its
diffusion length ``D = Q / (T S0 c)`` is long against the distance ``c dt`` that the
wave travels in a step (a flat reach, a large discharge, a narrow channel), and no
whole number of distance steps matches it. It is routed as ``n`` equal linear
reservoirs of ``K = L / (n c)`` with the exact kernel of the cascade
(:class:`~hydrolog.routing.cascade.CascadeReach`), the Muskingum scheme with ``X = 0``:
the diffusion wave of the reach travels ``L / c`` on average with the variance
``D L / c^2``, and ``n = L / D`` rounded (at least 1) matches both moments as nearly as
a whole number of reservoirs can. The warning ``diffusion_dominated`` says so; the
attenuation is approximate.

Unlike NRCS WinTR-20, which takes the peak at the upstream end of each distance step
as its reference, every step has the one reference of the reach (the inflow peak, or
the discharge that the caller gives), as in HEC-HMS; for a reach of one step the two
are the same.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import one_complete_group, positive
from hydrolog.routing._kernels import route_muskingum_cascade
from hydrolog.routing.cascade import CascadeReach
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.muskingum import MAX_SUBSTEPS
from hydrolog.routing.reach import (
    MAX_ORDINATES,
    REACH_METHODS,
    Reach,
    ReachRun,
    RoutingNotice,
)
from hydrolog.routing.sections import TrapezoidalSection

__all__ = ["MIN_RISE_STEPS", "MuskingumCungeReach", "rise_steps"]

MIN_RISE_STEPS = 10
"""NRCS: at least this many time steps from 5 % of the peak to the peak."""

_RISE_THRESHOLD = 0.05
_MAIN_PEAK = 0.5
_ROUNDING = 1e-9
_SECONDS_PER_MINUTE = 60.0
_METRES_PER_KM = 1000.0
_MAX_EXPONENT = 700.0  # exp() overflows a float above about 709

_SECTION = ("manning_n", "bottom_width_m")
_WAVE = ("celerity_m_per_s", "top_width_m")


def rise_steps(discharge_m3s: NDArray[np.float64]) -> int:
    """Return the number of time steps from 5 % of the peak to the peak.

    NEH-630 chapter 17, step 1 of the Muskingum-Cunge method: the start is the ordinate
    before the first one above 5 % of the peak discharge, the end the first peak that
    reaches half of the highest peak (the time to peak of a single-peak hydrograph).

    Parameters
    ----------
    discharge_m3s : numpy.ndarray
        The hydrograph ordinates, not negative.

    Returns
    -------
    int
        The number of steps; 0 for a hydrograph without a positive ordinate or one that
        starts at its peak.
    """
    values = np.asarray(discharge_m3s, dtype=np.float64)
    peak = float(values.max())
    if peak <= 0.0:
        return 0
    start = max(int(np.argmax(values > _RISE_THRESHOLD * peak)) - 1, 0)
    # the highest ordinate is always such a peak, so the search ends
    top = next(
        int(index)
        for index in np.flatnonzero(values >= _MAIN_PEAK * peak)
        if _is_peak(values, int(index))
    )
    return top - start


def _is_peak(values: NDArray[np.float64], index: int) -> bool:
    """Whether the ordinate is not below its predecessor and falls after any plateau."""
    level = values[index]
    if index > 0 and level < values[index - 1]:
        return False
    after = index + 1
    while after < len(values) and values[after] == level:
        after += 1
    return bool(after == len(values) or values[after] < level)


def _nrcs_steps(length: float, wave: float, diffusion: float) -> int:
    """Return the number of distance steps of the NRCS rule, ``ceil(L / dx_c)``.

    ``dx_c = (c dt + D) / 2`` (NEH-630 eq. 17-21) with ``wave = c dt`` and
    ``diffusion = D = Q / (T S0 c)`` in metres.
    """
    return max(1, math.ceil(length / (0.5 * (wave + diffusion)) * (1.0 - _ROUNDING)))


@dataclass(frozen=True)
class _Plan:
    """How the reach is routed: reference, distance steps and time sub-steps."""

    reference_m3s: float
    celerity_m_per_s: float
    top_width_m: float
    diffusion_length_m: float
    reference_step_m: float
    steps: int
    substeps: int
    notices: tuple[RoutingNotice, ...]


@dataclass(frozen=True)
class _Reservoirs:
    """How a reach without a grid is routed: ``count`` linear reservoirs (ADR-0026)."""

    reference_m3s: float
    celerity_m_per_s: float
    top_width_m: float
    diffusion_length_m: float
    count: int
    k_min: float
    notice: RoutingNotice


def _reservoirs(
    reference: float,
    celerity: float,
    top_width: float,
    diffusion: float,
    length: float,
    step_min: float,
) -> _Reservoirs:
    """Plan a reach for which no grid has non-negative weights (ADR-0026).

    The diffusion wave of the reach (celerity ``c``, diffusion length ``D`` [m]) has
    the mean travel time ``L / c`` and the variance ``D L / c^2``; ``n`` linear
    reservoirs of ``K`` have ``n K`` and ``n K^2``. ``K = L / (n c)`` keeps the travel
    time, and ``n = L / D`` rounded (a half up, at least 1) the variance as nearly as a
    whole number does.
    """
    count = max(1, math.floor(length / diffusion + 0.5))
    k_min = length / (count * celerity) / _SECONDS_PER_MINUTE
    longer = (
        f", longer than the reach: X = (1 - D / L) / 2 = "
        f"{0.5 * (1.0 - diffusion / length):.3g} would be negative"
        if diffusion > length
        else ""
    )
    message = (
        f"No division of the {length:g} m reach or of the {step_min:g} min step (into "
        f"at most {MAX_SUBSTEPS} parts) keeps the Muskingum-Cunge weights non-negative "
        f"(celerity {celerity:.3g} m/s, diffusion length D = {diffusion:.4g} m"
        f"{longer}). The reach was routed as {count} linear reservoir(s) of "
        f"K = L / (n c) = {k_min:.4g} min (Muskingum with X = 0, n = L / D rounded), "
        "which keep the travel time of the diffusion wave and, as nearly as a whole "
        "n can, its spread: the attenuation is approximate."
    )
    return _Reservoirs(
        reference,
        celerity,
        top_width,
        diffusion,
        count,
        k_min,
        RoutingNotice("diffusion_dominated", message, "warning"),
    )


@REACH_METHODS.register
class MuskingumCungeReach(Reach):
    """Route a hydrograph through a reach with constant-coefficient Muskingum-Cunge.

    The hydraulics of the reach are given either by a prismatic section and Manning's
    roughness (``manning_n`` and ``bottom_width_m``, with ``side_slope_m_per_m``), from
    which the normal depth, top width and celerity at the reference discharge follow
    (:class:`~hydrolog.routing.sections.TrapezoidalSection`), or directly by the
    ``celerity_m_per_s`` and the ``top_width_m`` of the flood wave at that discharge
    (for example from a hydraulic model or from NEH-630 ``c = m Q / A``).

    The reference discharge is the peak of the inflow unless
    ``reference_discharge_m3s`` is given (EM 1110-2-1417 takes the base flow plus half
    of the rise). The routing distance step is the NRCS one,
    ``dx_c = (c dt + Q / (T S0 c)) / 2``, and the reach is divided into
    ``ceil(L / dx_c)`` equal steps. Where the weights of that scheme would not all be
    non-negative, that is unless ``|c dt - D| <= dx <= c dt + D`` with
    ``D = Q / (T S0 c)``, the number of steps is changed (notice
    ``subreaches_adjusted``) or the time step is divided (``substeps_added``). When no
    such combination exists, the reach is routed as ``n = L / D`` (rounded, at least 1)
    linear reservoirs of ``K = L / (n c)`` with the exact kernel of the cascade, and
    the warning ``diffusion_dominated`` says that the attenuation is approximate; the
    ``parameters`` of the run then hold ``scheme`` ``linear_reservoir``, ``n``,
    ``k_min`` (of one reservoir), ``lag_min`` (``L / c``) and ``diffusion_length_m``
    instead of those of the grid (ADR-0026). A rise of fewer than 10 steps from 5 % of
    the peak to the peak divides the time step of a grid (``timestep_refined``). The
    notice ``accuracy_limit`` reports an NRCS grid that was beyond the accuracy limit of
    NEH-630 and was replaced; the routing itself is always inside the limit.

    Parameters
    ----------
    length_km : float
        Length of the reach [km], > 0.
    slope_m_per_m : float
        Friction (bed) slope [m/m], > 0.
    manning_n : float, optional
        Manning's roughness [s/m^(1/3)], > 0; with ``bottom_width_m``.
    bottom_width_m : float, optional
        Bottom width of the section [m], >= 0 (0: a triangle); with ``manning_n``.
    side_slope_m_per_m : float, optional
        Horizontal metres per vertical metre of the banks, >= 0 (0: a rectangle), by
        default 0.
    celerity_m_per_s : float, optional
        Celerity of the flood wave at the reference discharge [m/s], > 0; with
        ``top_width_m``, instead of the section.
    top_width_m : float, optional
        Width of the water surface at the reference discharge [m], > 0; with
        ``celerity_m_per_s``.
    reference_discharge_m3s : float, optional
        Reference discharge [m3/s], > 0; default the inflow peak.

    Raises
    ------
    InvalidParameterError
        If a value is not valid, or not exactly one of the two groups of hydraulics
        options is given (``details.reason`` ``one_of``). Routing raises it, with
        ``details.reason`` ``unstable_timestep``, when the grid needs so many sub-steps
        that the hydrograph would have more than a million ordinates.
    """

    model = "muskingum-cunge"

    def __init__(
        self,
        length_km: float,
        slope_m_per_m: float,
        *,
        manning_n: float | None = None,
        bottom_width_m: float | None = None,
        side_slope_m_per_m: float = 0.0,
        celerity_m_per_s: float | None = None,
        top_width_m: float | None = None,
        reference_discharge_m3s: float | None = None,
    ) -> None:
        """Create the element."""
        self.length_km = positive(length_km, "length_km")
        self.slope_m_per_m = positive(slope_m_per_m, "slope_m_per_m")
        values = {
            "manning_n": manning_n,
            "bottom_width_m": bottom_width_m,
            "celerity_m_per_s": celerity_m_per_s,
            "top_width_m": top_width_m,
        }
        given = [name for name, value in values.items() if value is not None]
        group = one_complete_group(given, (_SECTION, _WAVE), "The reach")
        # the group check has shown which options are given: the casts only tell mypy
        self._source: TrapezoidalSection | tuple[float, float]
        if group == 0:
            self._source = TrapezoidalSection(
                cast(float, bottom_width_m), side_slope_m_per_m, cast(float, manning_n)
            )
        else:
            self._source = (
                positive(cast(float, celerity_m_per_s), "celerity_m_per_s"),
                positive(cast(float, top_width_m), "top_width_m"),
            )
        self.reference_discharge_m3s = (
            None
            if reference_discharge_m3s is None
            else positive(reference_discharge_m3s, "reference_discharge_m3s")
        )

    def options(self) -> dict[str, Any]:
        """Return the arguments that rebuild the element.

        The two groups of hydraulics options are exclusive: the section (``manning_n``,
        ``bottom_width_m``, ``side_slope_m_per_m``) or the wave (``celerity_m_per_s``,
        ``top_width_m``); ``reference_discharge_m3s`` is in it when it was given.
        """
        options: dict[str, Any] = {
            "length_km": self.length_km,
            "slope_m_per_m": self.slope_m_per_m,
        }
        if isinstance(self._source, TrapezoidalSection):
            options["manning_n"] = self._source.manning_n
            options["bottom_width_m"] = self._source.bottom_width_m
            options["side_slope_m_per_m"] = self._source.side_slope_m_per_m
        else:
            options["celerity_m_per_s"], options["top_width_m"] = self._source
        if self.reference_discharge_m3s is not None:
            options["reference_discharge_m3s"] = self.reference_discharge_m3s
        return options

    def _hydraulics(self, reference: float) -> tuple[float, float]:
        """Return the celerity [m/s] and the top width [m] at the reference."""
        if isinstance(self._source, TrapezoidalSection):
            state = self._source.flow(reference, self.slope_m_per_m)
            return state.celerity_m_per_s, state.top_width_m
        return self._source

    def _plan(self, inflow: Hydrograph) -> _Plan | _Reservoirs:
        step_min = inflow.timestep_min
        reference = self.reference_discharge_m3s or inflow.peak_discharge_m3s
        if reference <= 0.0:
            raise InvalidParameterError(
                "Option 'reference_discharge_m3s': the inflow is zero everywhere, so "
                "there is no discharge to take the reference from",
                details={
                    "option": "reference_discharge_m3s",
                    "reason": "required",
                    "value": 0.0,
                },
                hint="Give reference_discharge_m3s, a discharge above zero.",
            )
        celerity, top_width = self._hydraulics(reference)
        diffusion = reference / (top_width * self.slope_m_per_m * celerity)
        length = self.length_km * _METRES_PER_KM
        step_s = step_min * _SECONDS_PER_MINUTE
        notices: list[RoutingNotice] = []

        rise = rise_steps(inflow.discharge_m3s)
        first = 1
        if 0 < rise < MIN_RISE_STEPS:
            first = min(math.ceil(MIN_RISE_STEPS / rise), MAX_SUBSTEPS)
            notices.append(
                RoutingNotice(
                    "timestep_refined",
                    f"The inflow rises from 5 % of its peak to the peak in {rise} "
                    f"time step(s), NRCS asks for at least {MIN_RISE_STEPS}: each "
                    f"{step_min:g} min step was divided into {first} sub-steps of "
                    f"{step_min / first:g} min (the inflow is interpolated linearly, "
                    "the outflow is read at the original ordinates, so the volume "
                    "balance has a sampling error).",
                )
            )
        grid = self._grid(length, celerity, diffusion, step_s, first)
        if grid is None:
            return _reservoirs(
                reference, celerity, top_width, diffusion, length, step_min
            )
        steps, substeps, preferred = grid
        refined = (len(inflow) - 1) * substeps + 1
        if refined > MAX_ORDINATES:
            raise InvalidParameterError(
                f"Option 'times_min': the time step of {step_min:g} min has to be "
                f"divided into {substeps} parts for this reach, which gives {refined} "
                f"ordinates (at most {MAX_ORDINATES})",
                details={
                    "option": "times_min",
                    "reason": "unstable_timestep",
                    "timestep_min": step_min,
                    "substeps": substeps,
                    "maximum": MAX_ORDINATES,
                },
                hint="Use a shorter hydrograph or a coarser time step.",
            )
        # NEH-630 appendix B: Dg <= exp(2.3 Cg) on the grid of the NRCS rule. A grid
        # with non-negative weights always meets it, so a grid beyond the limit is one
        # that this planner has replaced.
        nrcs_step = length / _nrcs_steps(length, celerity * step_s / first, diffusion)
        nrcs_courant = celerity * step_s / first / nrcs_step
        nrcs_limit = math.exp(min(2.3 * nrcs_courant, _MAX_EXPONENT))
        if diffusion / nrcs_step > nrcs_limit:
            notices.append(
                RoutingNotice(
                    "accuracy_limit",
                    f"On the NRCS grid ({nrcs_step:g} m steps) the grid Reynolds "
                    f"number {diffusion / nrcs_step:g} is above exp(2.3 Cg) = "
                    f"{nrcs_limit:g} for the Courant number Cg = {nrcs_courant:g}: "
                    "NEH-630 warns that such a routing may be inaccurate (a long, "
                    "flat reach). The reach was routed on a grid inside the limit.",
                )
            )
        if substeps > first:
            notices.append(
                RoutingNotice(
                    "substeps_added",
                    f"No number of distance steps keeps the weights non-negative "
                    f"on a {step_min / first:g} min step for this reach: each step "
                    f"was divided into {substeps} sub-steps of "
                    f"{step_min / substeps:g} min (the inflow is interpolated "
                    "linearly, the outflow is read at the original ordinates, so "
                    "the volume balance has a sampling error).",
                )
            )
        reference_step = 0.5 * (celerity * step_s / substeps + diffusion)
        if steps != preferred:
            notices.append(
                RoutingNotice(
                    "subreaches_adjusted",
                    f"The NRCS distance step of {reference_step:g} m gives "
                    f"{preferred} step(s) for the {length:g} m reach; {steps} "
                    f"(of {length / steps:g} m) keep the weights non-negative.",
                )
            )
        return _Plan(
            reference,
            celerity,
            top_width,
            diffusion,
            reference_step,
            steps,
            substeps,
            tuple(notices),
        )

    def _grid(
        self,
        length: float,
        celerity: float,
        diffusion: float,
        step_s: float,
        first: int,
    ) -> tuple[int, int, int] | None:
        """Choose the distance steps and the sub-steps; also the NRCS number.

        The weights of a distance step ``dx`` on a step ``dt`` are non-negative when
        ``|c dt - D| <= dx <= c dt + D``, ``D = Q / (T S0 c)``. The NRCS rule gives
        ``ceil(L / dx_c)`` steps; it is kept unless it breaks the lower bound, then
        the largest number that does not is taken. If there is none the step is
        divided further; ``None`` when no division into at most ``MAX_SUBSTEPS``
        parts gives one.
        """
        for substeps in range(first, MAX_SUBSTEPS + 1):
            wave = celerity * step_s / substeps
            most = length / (wave + diffusion)
            fewest = max(1, math.ceil(most * (1.0 - _ROUNDING)))
            gap = abs(wave - diffusion)
            largest = (
                math.inf if gap == 0.0 else math.floor(length / gap * (1.0 + _ROUNDING))
            )
            if fewest > largest:
                continue
            preferred = _nrcs_steps(length, wave, diffusion)
            return int(min(max(preferred, fewest), largest)), substeps, preferred
        return None

    def _run(self, inflow: Hydrograph, initial_outflow_m3s: float) -> ReachRun:
        plan = self._plan(inflow)
        if isinstance(plan, _Reservoirs):
            return self._run_reservoirs(plan, inflow, initial_outflow_m3s)
        fine = inflow.refined(plan.substeps)
        step_min = fine.timestep_min
        length = self.length_km * _METRES_PER_KM
        step_m = length / plan.steps
        k_step = step_m / plan.celerity_m_per_s / _SECONDS_PER_MINUTE
        x = 0.5 * (1.0 - plan.diffusion_length_m / step_m)
        run = route_muskingum_cascade(
            fine.discharge_m3s, k_step, x, step_min, plan.steps, initial_outflow_m3s
        )
        courant = plan.celerity_m_per_s * step_min * _SECONDS_PER_MINUTE / step_m
        reynolds = 1.0 - 2.0 * x
        limit = math.exp(min(2.3 * courant, _MAX_EXPONENT))
        return ReachRun(
            outflow_m3s=run.outflow[:: plan.substeps],
            storage_start_m3=run.storage_start * _SECONDS_PER_MINUTE,
            storage_end_m3=run.storage_end * _SECONDS_PER_MINUTE,
            storage_steady_m3=run.storage_steady * _SECONDS_PER_MINUTE,
            parameters={
                "length_km": self.length_km,
                "slope_m_per_m": self.slope_m_per_m,
                "reference_discharge_m3s": plan.reference_m3s,
                "celerity_m_per_s": plan.celerity_m_per_s,
                "top_width_m": plan.top_width_m,
                "k_min": k_step * plan.steps,
                "x": x,
                "subreaches": plan.steps,
                "substeps": plan.substeps,
                "dx_m": step_m,
                "dx_reference_m": plan.reference_step_m,
                "c_current": run.weights[0],
                "c_previous": run.weights[1],
                "c_outflow": run.weights[2],
                "courant_number": courant,
                "grid_reynolds_number": reynolds,
                "grid_reynolds_limit": limit,
            },
            notices=plan.notices,
        )

    def _run_reservoirs(
        self, plan: _Reservoirs, inflow: Hydrograph, initial_outflow_m3s: float
    ) -> ReachRun:
        """Route the reach as the linear reservoirs of the plan (ADR-0026).

        The run is the one of the cascade method with ``n`` and ``k_min``, so its
        ``parameters`` are those of the cascade with the hydraulics of the reach.
        """
        cascade = CascadeReach(plan.count, k_min=plan.k_min)
        run = cascade._run(inflow, initial_outflow_m3s)
        return replace(
            run,
            parameters={
                "length_km": self.length_km,
                "slope_m_per_m": self.slope_m_per_m,
                "reference_discharge_m3s": plan.reference_m3s,
                "celerity_m_per_s": plan.celerity_m_per_s,
                "top_width_m": plan.top_width_m,
                "diffusion_length_m": plan.diffusion_length_m,
                "scheme": "linear_reservoir",
                "n": plan.count,
                "k_min": plan.k_min,
                "lag_min": plan.count * plan.k_min,
            },
            notices=(plan.notice,),
        )
