r"""Muskingum-Cunge routing with constant coefficients, spec ``muskingum_cunge``.

:data:`MUSKINGUM_CUNGE` declares the routing of a hydrograph through a reach of length
``L`` on ``N`` equal distance steps ``dx = L / N`` and a given time step ``dt``, each a
Muskingum sub-reach whose ``K`` and ``X`` Cunge (1969) chose so that the numerical
diffusion of the scheme equals the physical diffusion of the flood wave (NEH 630
chapter 17, eqs. 17-20 to 17-22; HEC-HMS TRM, Muskingum-Cunge model, eqs. 12 and 13;
EM 1110-2-1417, eq. 9-22)::

    D = Q / (T S0 c)        K = dx / c        X = (1 - D / dx) / 2

with the reference discharge ``Q``, the top width ``T`` and the celerity ``c`` of the
wave at it and the slope ``S0``, constant for the whole run, and
:func:`muskingum_cunge_route` computes it with the weights of the Muskingum scheme
(:func:`~hydrolog.routing._kernels.route_muskingum_cascade`). The Courant number
``Cg = c dt / dx`` and the grid Reynolds number ``Dg = D / dx = 1 - 2X`` (NEH eqs.
17-32 to 17-35) describe the grid.

The weights are all non-negative when ``|c dt - D| <= dx <= c dt + D``, Ponce's
``|Cg - Dg| <= 1 <= Cg + Dg``: the precondition ``nonnegative_weights``, whose window
:func:`distance_step_window` gives. ``X`` may then be negative. On such a grid NEH's
accuracy limit ``Dg <= exp(2.3 Cg)`` (eq. 17-36) always holds: ``|Cg - Dg| <= 1``
gives ``Dg <= 1 + Cg <= exp(Cg) <= exp(2.3 Cg)``, to the window's slack of 1e-9.

:class:`~hydrolog.routing.MuskingumCungeReach` chooses the reference discharge, ``N``
and the sub-steps of a time step, and falls back to linear reservoirs where no grid
exists (Tier B: NEH 630 chapter 17 steps 1 to 4, ADR-0008, ADR-0026), then routes
through this formula. ``docs/FORMULAS.md`` shows the equation, the ranges and the
sources (ADR-0061).

Examples
--------
NRCS NEH 630 chapter 17, example 17-4: 2,600 ft at a slope of 0.00091, ``c`` = 4.297
ft/s, ``T`` = 44.6 ft and 684.18 ft3/s, one distance step on a step of 0.1 h (NEH
prints ``C2`` = 0.355, computed with ``X`` rounded to -0.254):

>>> from hydrolog.nogat_formulas import convert
>>> run = muskingum_cunge_route(
...     [0.0, 0.021, 0.032, 0.046], 6.0, convert(2600.0, "ft", "km"), 0.00091,
...     convert(4.297, "ft", "m"), convert(44.6, "ft", "m"),
...     convert(684.18, "ft3_per_s", "m3_per_s"), 1, 0.0,
... )
>>> round(convert(run.k_min, "min", "s"), 2), round(run.x, 3)
(605.07, -0.254)
>>> [round(c, 3) for c in (run.c_previous, run.c_current, run.c_outflow)]
[0.028, 0.356, 0.617]
>>> round(run.courant_number, 3), round(run.grid_reynolds_limit, 2)
(0.595, 3.93)
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
    Conservation,
    Constant,
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
from hydrolog.routing._kernels import route_muskingum_cascade
from hydrolog.routing.formulas._shared import (
    ROUTING_TESTS,
    SECONDS_PER_MINUTE,
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
from hydrolog.routing.formulas.manning import (
    BED_SLOPE,
    BED_SLOPE_TYPICAL,
    REFERENCE_DISCHARGE,
    REFERENCE_DISCHARGE_TYPICAL,
)
from hydrolog.routing.formulas.muskingum import WINDOW_ROUNDING

__all__ = [
    "ACCURACY_FACTOR",
    "MUSKINGUM_CUNGE",
    "SPECS",
    "MuskingumCungeRoute",
    "accuracy_limit",
    "distance_step_window",
    "muskingum_cunge_route",
]

ACCURACY_FACTOR: Final = 2.3
"""NEH 630 eq. 17-36: the grid Reynolds number of an accurate routing is at most
``exp(2.3 Cg)``, a limit NRCS fitted to 140 test routings (appendix 17B)."""

_EXPONENT_CAP: Final = 700.0
"""Largest exponent of the accuracy limit: ``exp(700)``, about 1e304, is a float and
above every grid Reynolds number of a grid with non-negative weights (``1 + Cg``)."""


@dataclass(frozen=True)
class MuskingumCungeRoute:
    """A hydrograph routed by the spec ``muskingum_cunge``.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow at the end of the reach at every inflow ordinate [m3/s].
    k_min : float
        Travel time ``K = L / c`` of the whole reach [min].
    x : float
        Weighting factor ``X`` of every distance step; negative where the diffusion
        length is longer than a step.
    c_current, c_previous, c_outflow : float
        Weights of ``I[t]``, ``I[t-1]`` and ``O[t-1]`` of one distance step.
    dx_m : float
        Distance step ``L / N`` [m].
    courant_number, grid_reynolds_number : float
        ``Cg = c dt / dx`` and ``Dg = D / dx = 1 - 2X`` of the grid.
    grid_reynolds_limit : float
        NEH's accuracy limit ``exp(2.3 Cg)`` of ``Dg``.
    storage_start_m3, storage_end_m3 : float
        Water the scheme holds at the first and at the last ordinate [m3]; below zero
        when ``X < 0`` and the inflow is well above the outflow.
    storage_steady_m3 : float
        What it would hold at rest under the last inflow ordinate, ``K I`` [m3].
    """

    outflow_m3s: NDArray[np.float64]
    k_min: float
    x: float
    c_current: float
    c_previous: float
    c_outflow: float
    dx_m: float
    courant_number: float
    grid_reynolds_number: float
    grid_reynolds_limit: float
    storage_start_m3: float
    storage_end_m3: float
    storage_steady_m3: float


# --- the computation -----------------------------------------------------------------


def _diffusion_length(
    slope: float, celerity: float, top_width: float, reference: float
) -> float:
    """Return ``D = Q / (T S0 c)`` [m]; infinite where ``T S0 c`` underflows."""
    denominator = top_width * slope * celerity
    return reference / denominator if denominator > 0.0 else math.inf


def distance_step_window(
    timestep_min: float,
    length_km: float,
    slope_m_per_m: float,
    celerity_m_per_s: float,
    top_width_m: float,
    reference_discharge_m3s: float,
) -> tuple[float, float]:
    """Return the least and the most distance steps whose weights are not negative.

    The weights of a distance step are non-negative when it is at least the
    difference and at most the sum of the distance the wave travels in a time step and
    the diffusion length of the reference discharge; each end is widened by the
    window's rounding. A number of steps between the two meets the precondition
    ``nonnegative_weights`` of the spec muskingum_cunge, and
    :class:`~hydrolog.routing.MuskingumCungeReach` plans its grid with them, so the
    plan and the precondition agree.

    Parameters
    ----------
    timestep_min : float
        Time step of the routing [min].
    length_km : float
        Length of the reach [km].
    slope_m_per_m : float
        Bed slope [m/m].
    celerity_m_per_s : float
        Celerity of the flood wave at the reference discharge [m/s].
    top_width_m : float
        Width of the water surface at the reference discharge [m].
    reference_discharge_m3s : float
        Reference discharge, in cubic metres per second.

    Returns
    -------
    tuple of float
        The least and the most number of distance steps, real numbers: infinite at
        the top when the wave travels exactly its diffusion length in a step; the
        window holds no whole number when the first exceeds the second.
    """
    length = convert(length_km, "km", "m")
    wave = celerity_m_per_s * convert(timestep_min, "min", "s")
    diffusion = _diffusion_length(
        slope_m_per_m, celerity_m_per_s, top_width_m, reference_discharge_m3s
    )
    total, gap = wave + diffusion, abs(wave - diffusion)
    lowest = length / total * (1.0 - WINDOW_ROUNDING) if total > 0.0 else math.inf
    highest = length / gap * (1.0 + WINDOW_ROUNDING) if gap > 0.0 else math.inf
    return lowest, highest


def accuracy_limit(courant_number: float) -> float:
    """Return NEH's limit of the grid Reynolds number at a Courant number.

    The output ``grid_reynolds_limit`` of the spec muskingum_cunge; the exponential is
    capped where it would leave the floats, far above every grid Reynolds number of a
    grid with non-negative weights.
    """
    return math.exp(min(ACCURACY_FACTOR * courant_number, _EXPONENT_CAP))


@dataclass(frozen=True)
class _Grid:
    """The scalars of a grid: dx [m], K of a step [min], X, Cg and Dg."""

    dx_m: float
    k_step_min: float
    x: float
    courant: float
    reynolds: float


def _grid(x: Values) -> _Grid:
    """Return the scalars of the grid; one that overflows is infinite, not an error."""
    count = x.integer("subreaches")
    celerity = x.real("celerity_m_per_s")
    diffusion = _diffusion_length(
        x.real("slope_m_per_m"),
        celerity,
        x.real("top_width_m"),
        x.real("reference_discharge_m3s"),
    )
    with np.errstate(all="ignore"):
        dx = np.float64(convert(x.real("length_km"), "km", "m")) / count
        reynolds = diffusion / dx
        courant = celerity * convert(x.real("timestep_min"), "min", "s") / dx
        travel = dx / celerity
    return _Grid(
        dx_m=float(dx),
        k_step_min=convert(float(travel), "s", "min"),
        x=0.5 * (1.0 - float(reynolds)),
        courant=float(courant),
        reynolds=float(reynolds),
    )


def _in_window(x: Values) -> bool:
    """Whether ``|c dt - D| <= L / N <= c dt + D``, to the window's rounding."""
    lowest, highest = distance_step_window(
        x.real("timestep_min"),
        x.real("length_km"),
        x.real("slope_m_per_m"),
        x.real("celerity_m_per_s"),
        x.real("top_width_m"),
        x.real("reference_discharge_m3s"),
    )
    return lowest <= x.integer("subreaches") <= highest


def _finite_grid(x: Values) -> bool:
    """Whether ``K``, ``Cg``, ``Dg`` and the bound of the water held are floats.

    The storage of a step, ``K [X I + (1 - X) O]``, is at most ``K (1 + 2|X|)`` times
    the largest of the inflow and the initial outflow, which bound the outflow.
    """
    grid = _grid(x)
    count = x.integer("subreaches")
    peak = max(float(np.max(x.array("inflow_m3s"))), x.real("initial_outflow_m3s"))
    spread = count * (1.0 + 2.0 * abs(grid.x)) * peak
    held = convert(grid.k_step_min, "min", "s") * spread
    return all(
        math.isfinite(value)
        for value in (grid.k_step_min * count, grid.courant, grid.reynolds, held)
    )


def _route(x: Values) -> dict[str, object]:
    grid = _grid(x)
    count = x.integer("subreaches")
    run = route_muskingum_cascade(
        x.array("inflow_m3s"),
        grid.k_step_min,
        grid.x,
        x.real("timestep_min"),
        count,
        x.real("initial_outflow_m3s"),
    )
    return {
        "outflow_m3s": run.outflow,
        "k_min": grid.k_step_min * count,
        "x": grid.x,
        "c_current": run.weights[0],
        "c_previous": run.weights[1],
        "c_outflow": run.weights[2],
        "dx_m": grid.dx_m,
        "courant_number": grid.courant,
        "grid_reynolds_number": grid.reynolds,
        "grid_reynolds_limit": accuracy_limit(grid.courant),
        "storage_start_m3": run.storage_start * SECONDS_PER_MINUTE,
        "storage_end_m3": run.storage_end * SECONDS_PER_MINUTE,
        "storage_steady_m3": run.storage_steady * SECONDS_PER_MINUTE,
    }


def _volume_kept(x: Values, out: Values) -> float:
    """Return inflow volume - outflow volume - storage change over the largest.

    The scale is at least the smallest normal float: below it volumes are subnormal
    and round to an absolute unit of 5e-324, not to a relative one.
    """
    step = x.real("timestep_min")
    entered = volume_m3(x.array("inflow_m3s"), step)
    left = volume_m3(out.array("outflow_m3s"), step)
    start, end = out.real("storage_start_m3"), out.real("storage_end_m3")
    scale = max(entered, left, abs(start), abs(end), sys.float_info.min)
    return (entered - left - (end - start)) / scale


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------


@dataclass(frozen=True)
class _Reach:
    """A reach and its grid: the inputs of the formula but the hydrograph."""

    timestep_min: float
    length_km: float
    slope_m_per_m: float
    celerity_m_per_s: float
    top_width_m: float
    reference_discharge_m3s: float
    subreaches: int

    def inputs(self) -> dict[str, object]:
        """Return the inputs by name."""
        return asdict(self)

    def diffusion_length_m(self) -> float:
        """Return ``D = Q / (T S0 c)`` [m]."""
        return _diffusion_length(
            self.slope_m_per_m,
            self.celerity_m_per_s,
            self.top_width_m,
            self.reference_discharge_m3s,
        )


def _reach(
    step: float,
    length: float,
    slope: float,
    celerity: float,
    width: float,
    reference: float,
    count: int,
) -> _Reach:
    """Return the reach of (dt, L, S0, c, T, Q, N)."""
    return _Reach(step, length, slope, celerity, width, reference, count)


_EXACT_POINTS: Final = (
    # inflow, initial outflow, reach: X = 0.115, -0.25 and -0.125
    (
        (0.0, 4.5, 37.0, 81.25, 40.0, 12.0, 3.0, 0.0),
        0.0,
        _reach(6.0, 2.6, 0.001, 1.0, 20.0, 20.0, 2),
    ),
    (
        (2.0, 2.0, 9.0, 1.0, 0.5, 2.0, 7.0, 6.0, 1.0),
        3.5,
        _reach(10.0, 3.0, 0.001, 1.0, 20.0, 30.0, 3),
    ),
    (
        (100.0, 300.0, 680.0, 500.0, 400.0, 310.0, 230.0),
        100.0,
        _reach(10.0, 4.0, 0.002, 5.0, 10.0, 250.0, 2),
    ),
)
"""Inputs of the exact oracle: made-up floods on grids of a positive and negative X."""


def _exact(
    values: Sequence[float], initial: float, reach: _Reach
) -> tuple[list[Fraction], dict[str, Fraction]]:
    """Return the outflow and the grid in exact rational arithmetic, in Ponce's form.

    ``C = c dt / dx`` and ``D = Q / (T S0 c dx)`` give the weights
    ``(C + D - 1) / (1 + C + D)``, ``(1 + C - D) / (1 + C + D)`` and
    ``(1 - C + D) / (1 + C + D)`` of ``I[t]``, ``I[t-1]`` and ``O[t-1]``.
    """
    count = reach.subreaches
    metres, seconds = Fraction(convert(1.0, "km", "m")), Fraction(SECONDS_PER_MINUTE)
    celerity = Fraction(reach.celerity_m_per_s)
    dx = Fraction(reach.length_km) * metres / count
    courant = celerity * Fraction(reach.timestep_min) * seconds / dx
    width_slope = Fraction(reach.top_width_m) * Fraction(reach.slope_m_per_m)
    reynolds = Fraction(reach.reference_discharge_m3s) / (width_slope * celerity * dx)
    total = 1 + courant + reynolds
    current = (courant + reynolds - 1) / total
    previous = (1 + courant - reynolds) / total
    kept = (1 - courant + reynolds) / total
    series = [Fraction(value) for value in values]
    for _ in range(count):
        out = [Fraction(initial)]
        for t in range(1, len(series)):
            out.append(current * series[t] + previous * series[t - 1] + kept * out[-1])
        series = out
    grid = {
        "k_min": count * dx / celerity / seconds,
        "x": (1 - reynolds) / 2,
        "c_current": current,
        "c_previous": previous,
        "c_outflow": kept,
        "courant_number": courant,
        "grid_reynolds_number": reynolds,
    }
    return series, grid


def _exact_recurrence(run: Callable[..., Values]) -> None:
    for values, initial, reach in _EXACT_POINTS:
        out = run(
            inflow_m3s=list(values), initial_outflow_m3s=initial, **reach.inputs()
        )
        series, grid = _exact(values, initial, reach)
        assert_within(
            out.array("outflow_m3s"),
            [float(value) for value in series],
            rel=1e-13,
            abs=1e-12,
            reason="the recurrence of lfilter in float64 against the same recurrence "
            "in exact rational arithmetic: a few roundings of each weight and step, "
            "damped by c_outflow < 1, over at most nine steps and three distance steps",
        )
        assert_within(
            [out.real(name) for name in grid],
            [float(value) for value in grid.values()],
            rel=1e-14,
            abs=1e-15,
            reason="D, dx, K, X, Cg and Dg are a few roundings of the inputs; X near "
            "zero is a difference, within a unit of 1e-16 absolute",
        )


_MOMENT_POINTS: Final = (
    _reach(5.0, 3.0, 0.001, 1.0, 20.0, 20.0, 3),
    _reach(10.0, 3.0, 0.001, 1.0, 20.0, 30.0, 3),
    _reach(10.0, 2.0, 0.001, 2.0, 20.0, 40.0, 1),
)
"""Reaches whose impulse responses are checked: X = 0, -0.25 and 0.25."""


def _moments(run: Callable[..., Values]) -> None:
    for reach in _MOMENT_POINTS:
        impulse = np.zeros(600)
        impulse[1] = 1.0
        out = run(inflow_m3s=impulse, initial_outflow_m3s=0.0, **reach.inputs())
        series = out.array("outflow_m3s")
        step = reach.timestep_min
        times = step * np.arange(series.size, dtype=np.float64)
        mass = float(np.sum(series))
        mean = float(np.sum(times * series)) / mass
        variance = float(np.sum((times - mean) ** 2 * series)) / mass
        celerity = reach.celerity_m_per_s
        travel = convert(convert(reach.length_km, "km", "m") / celerity, "s", "min")
        spread = travel * convert(reach.diffusion_length_m() / celerity, "s", "min")
        assert_within(
            [mean - step, variance],
            [travel, spread],
            rel=1e-12,
            reason="the impulse response of the Muskingum scheme has the mean K and "
            "the variance K^2 (1 - 2X) / N exactly (its generating function), which "
            "Cunge's K and X make L / c and D L / c^2, the moments of the diffusion "
            "wave; the tail beyond 600 ordinates is below 1e-30 of the mass",
        )


def _bounded(run: Callable[..., Values]) -> None:
    for values, initial, reach in _EXACT_POINTS:
        out = run(
            inflow_m3s=list(values), initial_outflow_m3s=initial, **reach.inputs()
        )
        series = out.array("outflow_m3s")
        low, high = min(*values, initial), max(*values, initial)
        slack = 4 * np.spacing(high)
        if not ((series >= low - slack).all() and (series <= high + slack).all()):
            raise AssertionError(
                f"muskingum_cunge: outflow {series} leaves [{low}, {high}], the range "
                "of the inflow and the initial outflow, though non-negative weights "
                "that sum to 1 make every ordinate a weighted mean of them"
            )


_LIMIT_POINTS: Final = (
    _reach(6.0, 2.6, 0.001, 1.0, 20.0, 20.0, 2),
    _reach(5.0, 2.6, 0.001, 1.0, 20.0, 20.0, 2),
    _reach(30.0, 1.0, 0.001, 1.0, 20.0, 16.0, 1),
    _reach(5.0, 1.0, 0.001, 1.0, 20.0, 26.0, 1),
    _reach(10.0, 3.0, 0.001, 1.0, 20.0, 30.0, 3),
    _reach(1.0, 1.0, 0.001, 1.0e-9, 1.0, 1.0000000009e-9, 1),
    _reach(1440.0, 1.0, 0.02, 5.0, 10.0, 432500.0, 1),
)
"""Grids inside the window, on its lower border (dx = c dt + D), on its upper border
from both sides (dx = c dt - D and dx = D - c dt), with X < 0, with a Courant number
of 6e-11 whose Dg exceeds 1 by the window's slack, and with a Courant number of 432
whose limit is capped."""


def _inside_the_limit(run: Callable[..., Values]) -> None:
    for reach in _LIMIT_POINTS:
        out = run(inflow_m3s=[0.0, 1.0, 0.0], initial_outflow_m3s=0.0, **reach.inputs())
        reynolds = out.real("grid_reynolds_number")
        limit = out.real("grid_reynolds_limit")
        if not reynolds <= limit + 2.0 * WINDOW_ROUNDING:
            raise AssertionError(
                f"muskingum_cunge: Dg = {reynolds} exceeds exp(2.3 Cg) = {limit} at "
                f"{reach}, though |Cg - Dg| <= 1 + 1e-9 gives Dg <= 1 + Cg + 1e-9"
            )


# --- the spec ------------------------------------------------------------------------

_NEH = neh630_17(
    "eqs. 17-20 to 17-22 (X, the distance step, K) and 17-31 to 17-36 (Cg, Dg and the "
    "accuracy limit, eq. 17-36 on p. 17-33); examples 17-4 and 17-5, pp. 17-36 to 17-51"
)
_HMS = hec_hms(
    "Muskingum-Cunge Model",
    "muskingum-cunge-model",
    "eqs. 3 to 5 (the convective diffusion equation, c = dQ/dA, mu = Q / (2 B S0)), "
    "6 to 10 (the weights) and 12 and 13 (K = dx / c, X = (1 - Q / (B S0 c dx)) / 2)",
)
_EM = em_1110_2_1417("chapter 9, eq. 9-22 and the reference flow, p. 9-21")
_CUNGE = Source(
    citation="Cunge, J.A. (1969). On the subject of a flood propagation computation "
    "method (Muskingum method), Journal of Hydraulic Research 7(2), 205-230",
    access="author-provided",
)
_POSITIVITY = Source(
    citation="the signs of the numerators of the weights (Hydrolog ADR-0008); "
    "Ponce's form |C - D| <= 1 <= C + D",
    locator="c_current >= 0 iff dx <= c dt + D, c_previous >= 0 iff dx >= D - c dt, "
    "c_outflow >= 0 iff dx >= c dt - D",
)
_FLOAT64 = Source(
    citation="IEEE 754-2019, binary64: finite numbers of magnitude about 4.9e-324 to "
    "1.8e308",
    locator="the grid's scalars and the water it holds must be among them; exp(700), "
    "about 1.0e304, is one",
)
_EXACT_SCALING = Tolerance(
    rel=0.0,
    abs=1e-300,
    reason="a power of two scales every product and quotient of D, dx, K, X, the "
    "weights and the recurrence exactly in binary, but for subnormal discharges, which "
    "round to fewer digits",
)


def _storage_of_the_scheme(name: str, description: str) -> Output:
    """Return an output of the water the scheme holds, negative where X < 0 may be."""
    return Output(
        name=name, unit="m3", symbol="S", description=description, physical=Range()
    )


MUSKINGUM_CUNGE: Final = FormulaSpec(
    name="muskingum_cunge",
    title="Muskingum-Cunge routing with constant coefficients on N equal distance "
    "steps (Cunge's K and X)",
    function="hydrolog.routing.formulas.cunge.muskingum_cunge_route",
    family="scheme",
    equation=(
        "D = Q / (T S0 c), dx = L / N, K = dx / c, X = (1 - D / dx) / 2; in each of N "
        "distance steps in series O[t] = c0 I[t] + c1 I[t-1] + c2 O[t-1] with the "
        "Muskingum weights of K, X and dt; Cg = c dt / dx, Dg = D / dx = 1 - 2X and "
        "NEH's accuracy limit exp(2.3 Cg)"
    ),
    latex=(
        r"D = \frac{Q}{T S_0 c},\ \Delta x = \frac{L}{N},\ K = \frac{\Delta x}{c},\ "
        r"X = \frac{1}{2}\left(1 - \frac{D}{\Delta x}\right);\quad "
        r"O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1};\quad "
        r"C_g = \frac{c \Delta t}{\Delta x},\ D_g = \frac{D}{\Delta x} = 1 - 2X"
    ),
    variables=(
        inflow(),
        timestep(),
        Variable(
            name="length_km",
            symbol="L",
            unit="km",
            description="Length of the reach.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=234.0,
                test_reason="ten times the longest reach of the project's data, 23.36 "
                "km on Hydrograf's Nysa Szalona network",
            ),
            applicability="unstated",
            typical=Range(
                low=0.1,
                high=23.4,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="0.1 to 20 km in the tests of the reach "
                    "(tests/unit/test_routing_cunge.py), 1.3 to 23.4 km on "
                    "Hydrograf's Nysa Szalona network besides a 7 m connector "
                    "(tests/fixtures/handoff_hydrograf_network_nysa_szalona.json); "
                    "NEH 630 examples 17-4 and 17-5, 2,600 ft (0.79 km)",
                ),
            ),
        ),
        Variable(
            name="slope_m_per_m",
            symbol="S_0",
            unit="m/m",
            description="Bed slope of the reach.",
            physical=BED_SLOPE,
            applicability="unstated",
            typical=BED_SLOPE_TYPICAL,
        ),
        Variable(
            name="celerity_m_per_s",
            symbol="c",
            unit="m/s",
            description="Celerity of the flood wave at the reference discharge.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=50.0,
                test_reason="ten times the fastest wave of the tests, 5 m/s",
            ),
            applicability="unstated",
            typical=Range(
                low=0.2,
                high=5.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="0.2 to 5 m/s in the tests of the reach "
                    "(tests/unit/test_routing_cunge.py); NEH 630 examples 17-4 and "
                    "17-5, 4.297 and 1.779 ft/s (1.31 and 0.54 m/s)",
                ),
            ),
        ),
        Variable(
            name="top_width_m",
            symbol="T",
            unit="m",
            description="Width of the water surface at the reference discharge.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=2250.0,
                test_reason="ten times the widest water surface of the tests and "
                "examples, 738.3 ft (225 m) in NEH 630 example 17-5",
            ),
            applicability="unstated",
            typical=Range(
                low=10.0,
                high=225.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="10 to 200 m in the tests of the reach and of the networks "
                    "(tests/unit/test_routing_cunge.py, "
                    "tests/unit/test_operations_route_network.py); NEH 630 examples "
                    "17-4 and 17-5, 44.6 and 738.3 ft (13.6 and 225 m)",
                ),
            ),
        ),
        Variable(
            name="reference_discharge_m3s",
            symbol="Q",
            unit="m3/s",
            description="Reference discharge, at which the celerity and the top width "
            "are taken, for the whole run.",
            physical=REFERENCE_DISCHARGE,
            applicability="unstated",
            typical=REFERENCE_DISCHARGE_TYPICAL,
        ),
        Variable(
            name="subreaches",
            symbol="N",
            unit="-",
            kind="integer",
            description="Number of equal distance steps dx = L / N.",
            physical=Range(
                low=1.0,
                test_high=1000.0,
                test_reason="the test bound of the length, 234 km, in steps of 234 m, "
                "half of what the wave of NEH 630 example 17-4 (4.297 ft/s) travels "
                "in its step of 0.1 h",
            ),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=4.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="1 to 4 distance steps in the tests of the reach "
                    "(tests/unit/test_routing_cunge.py); 1 and 2 in NEH 630 examples "
                    "17-4 and 17-5",
                ),
            ),
        ),
        initial_outflow(),
    ),
    outputs=(
        outflow(),
        Output(
            name="k_min",
            unit="min",
            symbol="K",
            description="Travel time L / c of the whole reach.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="x",
            unit="-",
            symbol="X",
            description="Weighting factor of every distance step, (1 - Dg) / 2.",
            physical=Range(high=0.5),
        ),
        Output(
            name="c_current",
            unit="-",
            symbol="c_0",
            description="Weight of I[t] in one distance step.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="c_previous",
            unit="-",
            symbol="c_1",
            description="Weight of I[t-1] in one distance step.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="c_outflow",
            unit="-",
            symbol="c_2",
            description="Weight of O[t-1] in one distance step.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="dx_m",
            unit="m",
            symbol=r"\Delta x",
            description="Distance step L / N.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="courant_number",
            unit="-",
            symbol="C_g",
            description="Courant number of the grid, c dt / dx.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="grid_reynolds_number",
            unit="-",
            symbol="D_g",
            description="Grid Reynolds number D / dx = 1 - 2X.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="grid_reynolds_limit",
            unit="-",
            symbol=r"e^{2.3 C_g}",
            description="NEH's accuracy limit of the grid Reynolds number, "
            "exp(2.3 Cg), capped at exp(700).",
            physical=Range(low=1.0),
        ),
        _storage_of_the_scheme(
            "storage_start_m3",
            "Water the scheme holds at the first ordinate, sum of K/N [X I + (1 - X) "
            "O] over the steps; below zero where X < 0 and the inflow exceeds the "
            "initial outflow enough.",
        ),
        _storage_of_the_scheme(
            "storage_end_m3", "Water the scheme holds at the last ordinate."
        ),
        storage(
            "storage_steady_m3",
            "Water it would hold at rest under the last inflow, K I[-1].",
        ),
    ),
    sources=(_NEH, _HMS, _EM, _CUNGE),
    constants=(
        Constant(
            name="accuracy_factor",
            value=ACCURACY_FACTOR,
            unit="-",
            symbol="2.3",
            source=_NEH,
        ),
        Constant(
            name="limit_exponent_cap",
            value=_EXPONENT_CAP,
            unit="-",
            source=_FLOAT64,
        ),
    ),
    constraints=(
        Constraint(
            name="nonnegative_weights",
            cls="precondition",
            check=_in_window,
            text="|c dt - D| <= L / N <= c dt + D with D = Q / (T S0 c), each end to "
            "1e-9 of itself: every weight is non-negative, so a non-negative inflow "
            "gives a non-negative outflow",
            source=_POSITIVITY,
            satisfied={"timestep_min": 6.0},
            boundary={"timestep_min": 5.0},
            violated={"timestep_min": 4.9},
        ),
        Constraint(
            name="finite_grid",
            cls="precondition",
            check=_finite_grid,
            text="L / c, c dt / dx, D / dx and N K (1 + 2|X|) max(I, O0) are finite: "
            "float64 holds the grid and the water it can hold; a wave so slow, a "
            "step so short or a flood so large that one overflows has none",
            source=_FLOAT64,
            satisfied={"subreaches": 2},
            violated={
                "celerity_m_per_s": 1.0e-305,
                "reference_discharge_m3s": 2.6e-304,
            },
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"inflow_m3s": 1, "initial_outflow_m3s": 1},
        scalings=(
            Scaling(
                name="discharge",
                inputs={"inflow_m3s": 1, "initial_outflow_m3s": 1},
                outputs={
                    "outflow_m3s": 1,
                    "storage_start_m3": 1,
                    "storage_end_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="time",
                inputs={
                    "inflow_m3s": -1,
                    "timestep_min": 1,
                    "celerity_m_per_s": -1,
                    "reference_discharge_m3s": -1,
                    "initial_outflow_m3s": -1,
                },
                outputs={"outflow_m3s": -1, "k_min": 1},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="length",
                inputs={
                    "inflow_m3s": 3,
                    "length_km": 1,
                    "celerity_m_per_s": 1,
                    "top_width_m": 1,
                    "reference_discharge_m3s": 3,
                    "initial_outflow_m3s": 3,
                },
                outputs={
                    "outflow_m3s": 3,
                    "dx_m": 1,
                    "storage_start_m3": 3,
                    "storage_end_m3": 3,
                    "storage_steady_m3": 3,
                },
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="discharge_per_width",
                inputs={"top_width_m": 1, "reference_discharge_m3s": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
        ),
        conservation=(
            Conservation(
                name="volume",
                text="the trapezoid continuity holds in every distance step: inflow "
                "volume - outflow volume = storage at the end - storage at the start",
                residual=_volume_kept,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="relative to the largest volume or storage, or to the "
                    "smallest normal float below which volumes round absolutely: the "
                    "recurrence rounds at 1e-16 per step; a weight that rounding put "
                    "below zero on a border of the window is set to zero, which moves "
                    "the others by at most the window's slack of 1e-9",
                ),
            ),
        ),
        limits=(
            Limit(
                name="steady_state",
                text="an inflow equal to the initial outflow passes unchanged: the "
                "weights sum to 1",
                inputs={"inflow_m3s": [7.5] * 12, "initial_outflow_m3s": 7.5},
                expected={"outflow_m3s": [7.5] * 12},
                tolerance=Tolerance(
                    rel=1e-15,
                    reason="the weights sum to 1 to rounding; each step rounds a "
                    "product and a sum, damped by c_outflow < 1",
                ),
            ),
            Limit(
                name="exact_recurrence",
                text="the grid and every outflow equal Ponce's form of the weights, "
                "(C + D - 1, 1 + C - D, 1 - C + D) / (1 + C + D), and the recurrence "
                "in exact rational arithmetic",
                check=_exact_recurrence,
            ),
            Limit(
                name="moments",
                text="the impulse response has the moments of the diffusion wave, the "
                "mean L / c and the variance 2 mu L / c^3 = D L / c^2, whatever dt and "
                "N",
                check=_moments,
            ),
            Limit(
                name="bounded_by_its_inputs",
                text="every outflow lies between the least and the largest of the "
                "inflow and the initial outflow",
                check=_bounded,
            ),
            Limit(
                name="inside_the_accuracy_limit",
                text="on every grid the window accepts Dg <= exp(2.3 Cg), to the "
                "window's slack: |Cg - Dg| <= 1 gives Dg <= 1 + Cg <= exp(2.3 Cg)",
                check=_inside_the_limit,
            ),
        ),
    ),
    validation=(
        "none: the sources compare the scheme with unsteady flow models, not with "
        "observations (NEH 630 examples 17-4 and 17-5 against HEC-RAS: peaks within "
        "0.2 and 2.5 %); NRCS fitted its accuracy limit to 140 test routings (NEH 630 "
        "appendix 17B)"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "SI units: discharge in m3/s, time in min, the reach in km, the distance "
            "step and the diffusion length in m, the celerity in m/s, storage in m3"
        ),
        (
            "the weights are named by what they multiply: c_current I[t], c_previous "
            "I[t-1], c_outflow O[t-1]; NEH 630 and HEC-HMS call them C2, C1 and C3"
        ),
        (
            "one reference discharge, celerity and top width for every distance and "
            "time step, so the coefficients are constant: NRCS's WinTR-20 takes the "
            "peak at the upstream end of each distance step (NEH 630 example 17-5) "
            "and HEC-HMS recomputes the coefficients at every time and distance step "
            "(a variable-coefficient method, Ponce 1986): case "
            "mc_neh17_example17_5_reach"
        ),
        (
            "X may be negative (NEH 630 example 17-4, X = -0.254); a grid with a "
            "negative weight, which NEH accepts (example 17-5, C1 = -0.187), is "
            "refused by the precondition nonnegative_weights (Hydrolog ADR-0008)"
        ),
        (
            "within the window's slack a weight that rounding puts below zero is set "
            "to zero and the others are divided by their sum "
            "(hydrolog.routing._kernels.nonnegative_coefficients)"
        ),
        (
            "Dg is computed as D / dx (NEH eq. 17-34), equal to 1 - 2X (eq. 17-35) to "
            "rounding; the accuracy limit exp(2.3 Cg) is capped at exp(700), above "
            "every Dg <= 1 + Cg of the window"
        ),
        "no lateral inflow: the term C4 q dx of HEC-HMS eq. 7 is zero",
        (
            "only the given grid is routed: MuskingumCungeReach takes the inflow peak "
            "as the reference unless one is given, chooses N and the sub-steps of a "
            "step by NEH 630's rules inside the window, interpolates the inflow "
            "linearly between them and falls back to linear reservoirs where no grid "
            "exists (Tier B, ADR-0008, ADR-0026)"
        ),
    ),
    assumptions=(
        (
            "the diffusion wave: the inertia terms of the momentum equation are "
            "neglected, and the convective diffusion equation is linearised at the "
            "reference discharge with c and mu = Q / (2 T S0) constant (HEC-HMS eqs. "
            "1 to 5)"
        ),
        "a prismatic reach of one slope; no backwater",
    ),
    traps={
        "difference_denominator": "the window's top L / |c dt - D| divides by a "
        "difference: when the wave travels exactly its diffusion length in a step it "
        "has no top (test_a_wave_as_long_as_its_diffusion_length_has_no_top); the "
        "weights' 1 + Cg + Dg never vanishes",
        "stability_bound": "the window |c dt - D| <= dx <= c dt + D: constraint "
        "nonnegative_weights with its satisfied, boundary and violated points, and "
        "test_a_border_of_the_window_rounds_to_zero_weights",
        "gap_propagation": "type cases inflow_m3s-nan_element and "
        "inflow_m3s-inf_element: a gap is refused, the recurrence would carry it to "
        "every later ordinate",
        "many_small_terms": "test_a_long_steady_inflow_stays_steady: 200,000 "
        "ordinates of a constant inflow stay constant to 1e-14",
    },
    reference_cases=("tests/fixtures/formulas/muskingum-cunge-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="Ponce's form of the weights, (C + D - 1, 1 + C - D, 1 - C + "
            "D) / (1 + C + D), and the recurrence of the distance steps in exact "
            "rational arithmetic (fractions)",
            test="tests/unit/test_formulas_muskingum_cunge.py (limit exact_recurrence)",
        ),
        Oracle(
            kind="exact",
            description="the moments of the impulse response against those of the "
            "diffusion wave of HEC-HMS eq. 3, mean L / c and variance 2 mu L / c^3 "
            "with mu = Q / (2 T S0), which Cunge's K and X reproduce exactly",
            test="tests/unit/test_formulas_muskingum_cunge.py (limit moments)",
        ),
    ),
    base={
        "timestep_min": 6.0,
        "length_km": 2.6,
        "slope_m_per_m": 0.001,
        "celerity_m_per_s": 1.0,
        "top_width_m": 20.0,
        "reference_discharge_m3s": 20.0,
        "subreaches": 2,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (MUSKINGUM_CUNGE,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def muskingum_cunge_route(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    length_km: float,
    slope_m_per_m: float,
    celerity_m_per_s: float,
    top_width_m: float,
    reference_discharge_m3s: float,
    subreaches: int,
    initial_outflow_m3s: float,
) -> MuskingumCungeRoute:
    """Route a hydrograph by Muskingum-Cunge on a given grid, spec muskingum_cunge.

    The first input is the inflow at every ordinate, the seventh the reference
    discharge and the last the outflow at the first ordinate, all in cubic metres per
    second.

    Parameters
    ----------
    timestep_min : float
        Time step of the ordinates [min].
    length_km : float
        Length of the reach [km].
    slope_m_per_m : float
        Bed slope [m/m].
    celerity_m_per_s : float
        Celerity of the flood wave at the reference discharge [m/s].
    top_width_m : float
        Width of the water surface at the reference discharge [m].
    subreaches : int
        Number ``N`` of equal distance steps.

    Returns
    -------
    MuskingumCungeRoute
        The outflow at every ordinate, the travel time, the weighting factor and the
        weights of a step, the grid's distance step, Courant and grid Reynolds numbers
        and NEH's accuracy limit, and the water held at the first and the last
        ordinate and at rest.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a gap, a grid outside the window of non-negative weights
        (``precondition_failed``, constraint ``nonnegative_weights``) or one a float
        cannot hold (constraint ``finite_grid``).
    """
    values = checked_inputs(
        MUSKINGUM_CUNGE,
        inflow_m3s=inflow_m3s,
        timestep_min=timestep_min,
        length_km=length_km,
        slope_m_per_m=slope_m_per_m,
        celerity_m_per_s=celerity_m_per_s,
        top_width_m=top_width_m,
        reference_discharge_m3s=reference_discharge_m3s,
        subreaches=subreaches,
        initial_outflow_m3s=initial_outflow_m3s,
    )
    out = checked_outputs(MUSKINGUM_CUNGE, _route(values))
    return MuskingumCungeRoute(
        outflow_m3s=out.array("outflow_m3s"),
        k_min=out.real("k_min"),
        x=out.real("x"),
        c_current=out.real("c_current"),
        c_previous=out.real("c_previous"),
        c_outflow=out.real("c_outflow"),
        dx_m=out.real("dx_m"),
        courant_number=out.real("courant_number"),
        grid_reynolds_number=out.real("grid_reynolds_number"),
        grid_reynolds_limit=out.real("grid_reynolds_limit"),
        storage_start_m3=out.real("storage_start_m3"),
        storage_end_m3=out.real("storage_end_m3"),
        storage_steady_m3=out.real("storage_steady_m3"),
    )
