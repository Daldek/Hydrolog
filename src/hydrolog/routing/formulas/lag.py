r"""The translation of a hydrograph by a lag, declared by the spec ``lag``.

:data:`LAG` declares ``O(t) = I(t - lag)`` (HEC-HMS Lag model) on the ordinates of the
inflow, and :func:`lag_route` computes it. :class:`~hydrolog.routing.LagReach` extends
the time axis (ADR-0008) and says when a lag is not a whole number of steps (notice
``lag_interpolated``), then routes through it. ``docs/FORMULAS.md`` shows the
equation, the ranges and the sources (ADR-0061).

A lag of ``w + f`` steps (``w`` whole, ``0 <= f < 1``) gives
``O[j] = (1 - f) I[j - w] + f I[j - w - 1]``, the inflow interpolated linearly between
the ordinates; before the first ordinate the inflow is the initial outflow. The water
in transit at the end is the inflow of the last ``lag`` minutes, ``lag O0`` at the
start and ``lag I`` at rest.

Examples
--------
A lag of 25 min on a step of 10 min, two and a half steps:

>>> run = lag_route([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0, 25.0, 0.0)
>>> run.outflow_m3s.tolist()
[0.0, 0.0, 0.0, 5.0, 25.0, 65.0, 75.0, 45.0]
>>> run.lag_steps, run.lag_fraction
(2.5, 0.5)
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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
)
from hydrolog.routing.formulas._shared import (
    ROUTING_TESTS,
    SECONDS_PER_MINUTE,
    hec_hms,
    inflow,
    initial_outflow,
    outflow,
    storage,
    timestep,
    volume_m3,
)
from hydrolog.routing.formulas.muskingum import muskingum_route

__all__ = ["LAG", "LAG_ROUNDING", "SPECS", "LagRoute", "lag_route"]

LAG_ROUNDING: Final = 1e-9
"""Steps by which a lag may miss a whole number of steps and still count as whole."""

_SMALLEST_NORMAL: Final = float(np.finfo(np.float64).tiny)
"""The smallest normal float64, the least scale of a volume in the conservation law."""


@dataclass(frozen=True)
class LagRoute:
    """A hydrograph routed by the spec ``lag``.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow at every inflow ordinate [m3/s].
    storage_start_m3, storage_end_m3 : float
        Water in transit at the first and at the last ordinate [m3].
    storage_steady_m3 : float
        Water in transit at rest under the last inflow ordinate, ``lag I`` [m3].
    lag_steps : float
        The lag over the time step.
    lag_fraction : float
        The part of a step by which the lag misses a whole number of steps, the weight
        of the earlier ordinate; zero for a whole number.
    """

    outflow_m3s: NDArray[np.float64]
    storage_start_m3: float
    storage_end_m3: float
    storage_steady_m3: float
    lag_steps: float
    lag_fraction: float


# --- the computation -----------------------------------------------------------------


def _representable(x: Values) -> bool:
    """Whether the lag in steps and the water in transit are finite float64."""
    lag = x.real("lag_min")
    largest = max(float(x.array("inflow_m3s").max()), x.real("initial_outflow_m3s"))
    return (
        lag / x.real("timestep_min") < math.inf
        and lag * largest * SECONDS_PER_MINUTE < math.inf
    )


def _transit_volume(
    times: NDArray[np.float64],
    values: NDArray[np.float64],
    initial: float,
    lag: float,
) -> float:
    """Volume of the inflow over the last ``lag`` minutes of the series [m3].

    The inflow is piecewise linear between the ordinates and equals ``initial`` before
    the first one (the water that was in transit at the start).
    """
    end = float(times[-1])
    begin = end - lag
    first = float(times[0])
    before = initial * max(0.0, first - begin)
    lower = max(begin, first)
    knots = np.concatenate([[lower], times[(times > lower) & (times < end)], [end]])
    levels = np.interp(knots, times, values)
    area = float(np.sum(0.5 * (levels[1:] + levels[:-1]) * np.diff(knots)))
    return (before + area) * SECONDS_PER_MINUTE


def _route(x: Values) -> dict[str, object]:
    values = x.array("inflow_m3s")
    count = len(values)
    step, lag = x.real("timestep_min"), x.real("lag_min")
    start = x.real("initial_outflow_m3s")
    steps = lag / step
    whole = math.floor(steps + LAG_ROUNDING)
    fraction = steps - whole
    if fraction < LAG_ROUNDING:
        fraction = 0.0
    elif fraction > 1.0 - LAG_ROUNDING:
        whole, fraction = whole + 1, 0.0
    # padded[j + 1] is the inflow ``whole`` steps before ordinate j, padded[j] one
    # step earlier; before the first ordinate the inflow is the initial outflow.
    head = min(whole + 1, count + 1)
    padded = np.concatenate([np.full(head, start), values])[: count + 1]
    times = step * np.arange(count, dtype=np.float64)
    return {
        "outflow_m3s": (1.0 - fraction) * padded[1:] + fraction * padded[:-1],
        "storage_start_m3": start * lag * SECONDS_PER_MINUTE,
        "storage_end_m3": _transit_volume(times, values, start, lag),
        "storage_steady_m3": float(values[-1]) * lag * SECONDS_PER_MINUTE,
        "lag_steps": steps,
        "lag_fraction": fraction,
    }


def _transit_kept(x: Values, out: Values) -> float:
    """Return the imbalance less its two known parts, over the largest volume.

    The outflow ordinates are exact samples of ``I(t - lag)`` for an inflow that rises
    linearly from ``O0`` one step before the first ordinate to ``I[0]``, while the
    storages hold ``O0`` up to the first ordinate: the ramp adds
    ``J (u - u^2 / (2 dt))`` over the last ``u = min(lag, dt)`` minutes before it,
    ``J = I[0] - O0``, at the start and, for a lag longer than the series, at the
    end. The trapezoid on the
    outflow errs by ``f (1 - f) dt^2 / 2`` times each change of the inflow's slope that
    falls between two outflow ordinates; these telescope to the change of slope across
    the window.
    """
    values = x.array("inflow_m3s")
    step, lag = x.real("timestep_min"), x.real("lag_min")
    start = x.real("initial_outflow_m3s")
    count = values.size
    fraction = out.real("lag_fraction")
    whole = round(out.real("lag_steps") - fraction)
    jump = float(values[0]) - start

    def ramp(length: float) -> float:
        # u (1 - u / (2 dt)) and not u - u^2 / (2 dt): u^2 underflows for tiny steps
        return jump * length * (1.0 - length / (2.0 * step))

    def level(index: int) -> float:
        return float(values[index]) if index >= 0 else start

    span = (count - 1) * step
    tail = ramp(min(lag - span, step)) if lag > span else 0.0
    kinks = 0.0
    first, last = -whole, count - 2 - whole
    if fraction > 0.0 and first <= last:
        change = (level(last + 1) - level(last)) - (level(first) - level(first - 1))
        kinks = 0.5 * fraction * (1.0 - fraction) * step * change
    known = (tail - ramp(min(lag, step)) - kinks) * SECONDS_PER_MINUTE
    entered = volume_m3(values, step)
    left = volume_m3(out.array("outflow_m3s"), step)
    begin, end = out.real("storage_start_m3"), out.real("storage_end_m3")
    scale = max(entered, left, begin, end, abs(known), _SMALLEST_NORMAL)
    return (entered - left - (end - begin) - known) / scale


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_FLOODS: Final = (
    # inflow, step, initial outflow
    ((0.0, 4.5, 37.0, 81.25, 40.0, 12.0, 3.0, 0.0), 10.0, 0.0),
    ((2.0, 2.0, 9.0, 1.0, 0.5, 2.0, 7.0, 6.0, 1.0), 5.0, 3.5),
    ((100.0, 300.0, 680.0, 500.0, 400.0, 310.0, 230.0), 720.0, 100.0),
)
"""Made-up floods and the Iowa inflow of the Muskingum spec."""


def _muskingum_one_step(run: Callable[..., Values]) -> None:
    for values, step, start in _FLOODS:
        out = run(
            inflow_m3s=list(values),
            timestep_min=step,
            lag_min=step,
            initial_outflow_m3s=start,
        ).array("outflow_m3s")
        scheme = muskingum_route(list(values), step, step, 0.5, 1, start)
        assert_within(
            out,
            scheme.outflow_m3s,
            abs=0.0,
            reason="Muskingum with X = 0.5 and K = dt has c_current = c_outflow = 0 "
            "and c_previous = 1 exactly, the lag of one step (HEC-HMS): both copy "
            "the earlier ordinate",
        )


def _shifted(
    run: Callable[..., Values],
    flood: tuple[Sequence[float], float, float],
    steps: float,
) -> NDArray[np.float64]:
    values, step, start = flood
    return run(
        inflow_m3s=list(values),
        timestep_min=step,
        lag_min=steps * step,
        initial_outflow_m3s=start,
    ).array("outflow_m3s")


def _convex_shifts(run: Callable[..., Values]) -> None:
    for flood in _FLOODS:
        for whole, fraction in ((1, 0.25), (2, 0.5), (3, 0.375), (12, 0.75)):
            assert_within(
                _shifted(run, flood, whole + fraction),
                (1.0 - fraction) * _shifted(run, flood, whole)
                + fraction * _shifted(run, flood, whole + 1),
                rel=1e-15,
                abs=1e-300,
                reason="dt and the binary fractions make (w + f) dt / dt exact, so "
                "the fractional lag takes the same two products and one sum as the "
                "convex combination of the shifts by w and w + 1 steps",
            )


# --- the spec ------------------------------------------------------------------------

_HEC_HMS = hec_hms(
    "Lag Model",
    "lag-model",
    "eq. 1: O_t = I_(t - lag) for t >= lag and O_t = I_t before; the lag suits "
    "short reaches with a predictable travel time",
)
_FLOAT64 = Source(
    citation="IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308",
    locator="the lag over the step, and the water in transit lag max(I, O0)",
)
_EXACT_SCALING = Tolerance(
    rel=0.0,
    abs=1e-300,
    reason="a power of two scales every product and sum of the shift and the transit "
    "volume exactly in binary, and leaves lag / dt unchanged, but for subnormal "
    "discharges, which round to fewer digits",
)

LAG: Final = FormulaSpec(
    name="lag",
    title="Lag routing: the inflow translated by a fixed time, linear between the "
    "ordinates",
    function="hydrolog.routing.formulas.lag.lag_route",
    family="scheme",
    equation=(
        "O(t) = I(t - lag), I = O0 before the first ordinate; with lag / dt = w + f, "
        "0 <= f < 1: O[j] = (1 - f) I[j - w] + f I[j - w - 1]; storage at the start "
        "lag O0, at the end the integral of I over the last lag minutes, at rest "
        "lag I[-1] [m3]"
    ),
    latex=(
        r"O(t) = I(t - \tau),\quad "
        r"O_j = (1 - f)\,I_{j-w} + f\,I_{j-w-1},\ "
        r"\frac{\tau}{\Delta t} = w + f,\ 0 \le f < 1,\quad "
        r"S(t) = \int_{t-\tau}^{t} I(s)\,ds"
    ),
    variables=(
        inflow(),
        timestep(),
        Variable(
            name="lag_min",
            symbol=r"\tau",
            unit="min",
            description="Lag, the travel time of the reach.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=50000.0,
                test_reason="ten times the longest lag of the tests of the lag, "
                "5,000 min, a lag beyond the cap of the extension",
            ),
            applicability="unstated",
            typical=Range(
                low=5.0,
                high=60.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="lags of 5 to 30 min in tests/unit/test_routing_core.py "
                    "and of 10 to 60 min in docs/USAGE.md (route lag, networks)",
                ),
            ),
        ),
        initial_outflow(),
    ),
    outputs=(
        outflow(),
        storage("storage_start_m3", "Water in transit at the first ordinate, lag O0."),
        storage(
            "storage_end_m3",
            "Water in transit at the last ordinate, the inflow of the last lag "
            "minutes.",
        ),
        storage(
            "storage_steady_m3",
            "Water in transit at rest under the last inflow, lag I[-1].",
        ),
        Output(
            name="lag_steps",
            unit="-",
            symbol="w + f",
            description="The lag over the time step.",
            physical=Range(low=0.0),
        ),
        Output(
            name="lag_fraction",
            unit="-",
            symbol="f",
            description="The weight of the earlier ordinate: the part of a step by "
            "which the lag misses a whole number of steps.",
            physical=Range(low=0.0, high=1.0, high_inclusive=False),
        ),
    ),
    sources=(_HEC_HMS,),
    constraints=(
        Constraint(
            name="representable",
            cls="precondition",
            check=_representable,
            text="lag / dt and the water in transit lag max(I, O0) are finite in "
            "float64",
            source=_FLOAT64,
            satisfied={"timestep_min": 10.0},
            violated={"timestep_min": 5e-324},
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
                inputs={"timestep_min": 1, "lag_min": 1},
                outputs={
                    "storage_start_m3": 1,
                    "storage_end_m3": 1,
                    "storage_steady_m3": 1,
                },
                tolerance=_EXACT_SCALING,
            ),
        ),
        conservation=(
            Conservation(
                name="volume",
                text="inflow volume - outflow volume - (storage at the end - storage "
                "at the start) = J (u_end - u_end^2 / (2 dt)) - J (u - u^2 / (2 dt)) "
                "- f (1 - f) dt (slope change across the window) / 2, J = I[0] - O0, "
                "u = min(lag, dt), u_end = min(lag - T, dt) for a lag beyond the "
                "series T: exact for a whole number of steps and I[0] = O0",
                residual=_transit_kept,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="relative to the largest volume or storage: the volumes "
                    "and the transit volume are sums of exact trapezoids, rounding at "
                    "1e-16 each; the shift takes the lag a rounding of 1e-9 steps "
                    "from a whole number as whole, while the storages keep the lag",
                ),
            ),
        ),
        limits=(
            Limit(
                name="whole_step_shift",
                text="a lag of two steps copies each inflow ordinate two ordinates "
                "later, the initial outflow before",
                inputs={
                    "inflow_m3s": [0.0, 10.0, 40.0, 20.0, 0.0, 0.0],
                    "timestep_min": 30.0,
                    "lag_min": 60.0,
                    "initial_outflow_m3s": 2.0,
                },
                expected={
                    "outflow_m3s": [2.0, 2.0, 0.0, 10.0, 40.0, 20.0],
                    "storage_start_m3": 2.0 * 60.0 * SECONDS_PER_MINUTE,
                    "storage_end_m3": (20.0 / 2.0) * 30.0 * SECONDS_PER_MINUTE,
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="f = 0: the ordinates are copied, and the transit volume "
                    "of the last two steps is a sum of exact halves",
                ),
            ),
            Limit(
                name="half_step_interpolation",
                text="a lag of two and a half steps averages the inflow two and three "
                "steps earlier (Hydrolog's catalog example of route lag)",
                inputs={
                    "inflow_m3s": [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0],
                    "timestep_min": 10.0,
                    "lag_min": 25.0,
                    "initial_outflow_m3s": 0.0,
                },
                expected={
                    "outflow_m3s": [0.0, 0.0, 0.0, 5.0, 25.0, 65.0, 75.0, 45.0],
                    "lag_fraction": 0.5,
                },
                tolerance=Tolerance(
                    abs=0.0,
                    reason="halves of whole numbers are exact in binary",
                ),
                source=_HEC_HMS,
            ),
            Limit(
                name="steady_state",
                text="an inflow equal to the initial outflow passes unchanged",
                inputs={
                    "inflow_m3s": [7.5] * 12,
                    "timestep_min": 10.0,
                    "lag_min": 37.0,
                    "initial_outflow_m3s": 7.5,
                },
                expected={"outflow_m3s": [7.5] * 12},
                tolerance=Tolerance(
                    rel=1e-15,
                    reason="(1 - f) 7.5 + f 7.5 rounds once in each product and in "
                    "the sum",
                ),
            ),
            Limit(
                name="muskingum_one_step",
                text="a lag of one step equals the Muskingum scheme with X = 0.5 and "
                "K = dt in one sub-reach (HEC-HMS)",
                check=_muskingum_one_step,
            ),
            Limit(
                name="convex_shifts",
                text="a lag of w + f steps is (1 - f) times the shift by w steps plus "
                "f times the shift by w + 1",
                check=_convex_shifts,
            ),
        ),
    ),
    validation=(
        "none: the lag is the travel time of a reach, set from its length and the "
        "celerity or calibrated (HEC-HMS TRM, Lag model); the source reports no "
        "agreement with observations"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "SI units: discharge in m3/s, time in min, storage in m3 (a lag in min times a "
        "discharge in m3/s times the 60 s of a minute of the units table)",
        (
            "before the first ordinate the inflow is the initial outflow (the reach at "
            "rest, ADR-0008); HEC-HMS TRM Lag model eq. 1 writes O_t = I_t for "
            "t < lag instead"
        ),
        (
            "a lag that is not a whole number of steps interpolates the inflow "
            "linearly between the two ordinates around t - lag, which flattens sharp "
            "peaks; one step before the first ordinate the inflow is O0, so the "
            "outflow ordinates follow an inflow that rises linearly from O0 to I[0] "
            "over that step, while the storages hold O0 up to the first ordinate"
        ),
        (
            "a lag within 1e-9 steps of a whole number counts as whole "
            "(LAG_ROUNDING); the storages keep the lag as given"
        ),
        (
            "only the given ordinates are routed: LagReach extends the time axis by "
            "the lag (Tier B, ADR-0008) and adds the notice lag_interpolated for a "
            "lag that is not a whole number of steps"
        ),
    ),
    assumptions=(
        "the reach translates the wave without attenuation, its travel time constant "
        "over the flood",
        "no backwater: the outflow does not depend on the water downstream",
    ),
    traps={
        "gap_propagation": "type cases inflow_m3s-nan_element and "
        "inflow_m3s-inf_element: a gap is refused, the shift would carry it lag "
        "minutes later",
        "many_small_terms": "test_a_long_transit_volume_sums_exactly: the transit "
        "volume of a lag of 100,000 steps against math.fsum of the same trapezoids",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="the Muskingum scheme with X = 0.5 and K = dt in one "
            "sub-reach (hydrolog.routing.formulas.muskingum.muskingum_route, spec "
            "muskingum), the lag of one step",
            test="tests/unit/test_formulas_lag.py (limit muskingum_one_step)",
        ),
        Oracle(
            kind="exact",
            description="the shift by a whole number of steps, and a fractional lag "
            "as the convex combination of the two shifts around it",
            test="tests/unit/test_formulas_lag.py (limits whole_step_shift, "
            "half_step_interpolation, convex_shifts)",
        ),
    ),
)

SPECS: Final[tuple[FormulaSpec, ...]] = (LAG,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def lag_route(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    lag_min: float,
    initial_outflow_m3s: float,
) -> LagRoute:
    """Translate a hydrograph by a lag, spec lag.

    The first input is the inflow at every ordinate and the last the outflow at the
    first one, both in cubic metres per second.

    Parameters
    ----------
    timestep_min : float
        Time step of the ordinates [min].
    lag_min : float
        Lag [min].

    Returns
    -------
    LagRoute
        The outflow at every ordinate, the water in transit at the first and the last
        ordinate and at rest, and the lag in steps with its fraction.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a gap, or a lag in steps or water in transit beyond float
        (``precondition_failed``, constraint ``representable``).
    """
    values = checked_inputs(
        LAG,
        inflow_m3s=inflow_m3s,
        timestep_min=timestep_min,
        lag_min=lag_min,
        initial_outflow_m3s=initial_outflow_m3s,
    )
    out = checked_outputs(LAG, _route(values))
    return LagRoute(
        outflow_m3s=out.array("outflow_m3s"),
        storage_start_m3=out.real("storage_start_m3"),
        storage_end_m3=out.real("storage_end_m3"),
        storage_steady_m3=out.real("storage_steady_m3"),
        lag_steps=out.real("lag_steps"),
        lag_fraction=out.real("lag_fraction"),
    )
