r"""The Muskingum scheme through equal sub-reaches, declared by the spec ``muskingum``.

:data:`MUSKINGUM` declares the routing of a hydrograph through ``N`` equal Muskingum
sub-reaches of ``K / N`` in series on a given time step (McCarthy's storage
``S = K [X I + (1 - X) O]`` with the trapezoid rule of continuity), and
:func:`muskingum_route` computes it. :class:`~hydrolog.routing.MuskingumReach` chooses
``N`` and the sub-steps of a time step and extends the time axis (ADR-0008), then
routes through it. ``docs/FORMULAS.md`` shows the equation, the ranges and the sources
(ADR-0061).

Examples
--------
The example of the University of Iowa (Lesson 27), ``K`` = 20 h, ``X`` = 0.25 and a step
of 12 h, its flows in cfs (the scheme is linear in the discharge):

>>> run = muskingum_route([100.0, 300.0, 680.0, 500.0], 720.0, 1200.0, 0.25, 1, 100.0)
>>> run.outflow_m3s.round(1).tolist()
[100.0, 109.5, 236.5, 481.3]
>>> [round(c, 4) for c in (run.c_current, run.c_previous, run.c_outflow)]
[0.0476, 0.5238, 0.4286]
"""

from __future__ import annotations

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

__all__ = [
    "MUSKINGUM",
    "SPECS",
    "WINDOW_ROUNDING",
    "MuskingumRoute",
    "muskingum_route",
]

WINDOW_ROUNDING: Final = 1e-9
"""Relative slack of the window's ends: a whole number of sub-reaches on a border is
inside it to rounding (``hydrolog.routing.muskingum.subreach_window`` uses it too)."""


@dataclass(frozen=True)
class MuskingumRoute:
    """A hydrograph routed by the spec ``muskingum``.

    Attributes
    ----------
    outflow_m3s : numpy.ndarray
        Outflow of the last sub-reach at every inflow ordinate [m3/s].
    c_current, c_previous, c_outflow : float
        Weights of ``I[t]``, ``I[t-1]`` and ``O[t-1]`` of one sub-reach.
    storage_start_m3, storage_end_m3 : float
        Water held by all sub-reaches at the first and at the last ordinate [m3].
    storage_steady_m3 : float
        What they would hold at rest under the last inflow ordinate, ``K I`` [m3].
    """

    outflow_m3s: NDArray[np.float64]
    c_current: float
    c_previous: float
    c_outflow: float
    storage_start_m3: float
    storage_end_m3: float
    storage_steady_m3: float


# --- the computation -----------------------------------------------------------------


def _in_window(x: Values) -> bool:
    """Whether ``2 K X / dt <= N <= 2 K (1 - X) / dt``, to the window's rounding."""
    k, weight = x.real("k_min"), x.real("x")
    step, count = x.real("timestep_min"), x.integer("subreaches")
    lowest = 2.0 * k * weight / step * (1.0 - WINDOW_ROUNDING)
    highest = 2.0 * k * (1.0 - weight) / step * (1.0 + WINDOW_ROUNDING)
    return lowest <= count <= highest


_SMALLEST_NORMAL: Final = float(np.finfo(np.float64).smallest_normal)


def _representable(x: Values) -> bool:
    """Whether float64 holds the weights and the water of the scheme.

    ``dt``, ``K / N`` and ``dt / (K / N)`` must be normal numbers, or the terms of the
    weights round to fewer digits and the weights of the inflow underflow to zero, so
    the water that enters is lost; ``2 K`` in seconds and the water ``K max(I, O0)``
    must be finite, or the weights are NaN and the storage infinite.
    """
    k, step = x.real("k_min"), x.real("timestep_min")
    count = x.integer("subreaches")
    peak = max(float(np.max(x.array("inflow_m3s"))), x.real("initial_outflow_m3s"))
    seconds = k * SECONDS_PER_MINUTE
    return (
        min(step, k / count, step * count / k) >= _SMALLEST_NORMAL
        and np.isfinite(2.0 * seconds)
        and np.isfinite(seconds * peak)
    )


def _route(x: Values) -> dict[str, object]:
    count = x.integer("subreaches")
    run = route_muskingum_cascade(
        x.array("inflow_m3s"),
        x.real("k_min") / count,
        x.real("x"),
        x.real("timestep_min"),
        count,
        x.real("initial_outflow_m3s"),
    )
    return {
        "outflow_m3s": run.outflow,
        "c_current": run.weights[0],
        "c_previous": run.weights[1],
        "c_outflow": run.weights[2],
        "storage_start_m3": run.storage_start * SECONDS_PER_MINUTE,
        "storage_end_m3": run.storage_end * SECONDS_PER_MINUTE,
        "storage_steady_m3": run.storage_steady * SECONDS_PER_MINUTE,
    }


def _volume_kept(x: Values, out: Values) -> float:
    """Return inflow volume - outflow volume - storage change over the largest.

    The scale is at least the volume of a hydrograph of the smallest normal float64
    discharge: below it the volumes are subnormal and carry fewer digits.
    """
    step = x.real("timestep_min")
    flows = x.array("inflow_m3s")
    entered = volume_m3(flows, step)
    left = volume_m3(out.array("outflow_m3s"), step)
    start, end = out.real("storage_start_m3"), out.real("storage_end_m3")
    floor = _SMALLEST_NORMAL * step * SECONDS_PER_MINUTE * flows.size
    scale = max(entered, left, start, end, floor)
    return (entered - left - (end - start)) / scale


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_EXACT_POINTS: Final = (
    # inflow, step, K, X, N, initial outflow
    ((100.0, 300.0, 680.0, 500.0, 400.0, 310.0, 230.0), 720.0, 1200.0, 0.25, 1, 100.0),
    ((0.0, 4.5, 37.0, 81.25, 40.0, 12.0, 3.0, 0.0), 10.0, 45.0, 0.3, 3, 0.0),
    ((2.0, 2.0, 9.0, 1.0, 0.5, 2.0, 7.0, 6.0, 1.0), 5.0, 17.0, 0.0, 2, 3.5),
)
"""Inputs of the exact oracle: the Iowa example and two made-up floods."""


def _exact_outflow(
    inflow_m3s: Sequence[float],
    step: float,
    k_min: float,
    weight: float,
    count: int,
    initial: float,
) -> list[Fraction]:
    """Return the recurrence of the sub-reaches in exact rational arithmetic."""
    k = Fraction(k_min) / count
    x = Fraction(weight)
    dt = Fraction(step)
    total = 2 * k * (1 - x) + dt
    c0, c1, c2 = (dt - 2 * k * x) / total, (dt + 2 * k * x) / total, 1 - 2 * dt / total
    series = [Fraction(value) for value in inflow_m3s]
    for _ in range(count):
        out = [Fraction(initial)]
        for t in range(1, len(series)):
            out.append(c0 * series[t] + c1 * series[t - 1] + c2 * out[t - 1])
        series = out
    return series


def _exact_recurrence(run: Callable[..., Values]) -> None:
    for values, step, k_min, weight, count, initial in _EXACT_POINTS:
        out = run(
            inflow_m3s=list(values),
            timestep_min=step,
            k_min=k_min,
            x=weight,
            subreaches=count,
            initial_outflow_m3s=initial,
        )
        exact = _exact_outflow(values, step, k_min, weight, count, initial)
        assert_within(
            out.array("outflow_m3s"),
            [float(value) for value in exact],
            rel=1e-13,
            abs=1e-12,
            reason="the recurrence of lfilter in float64 against the same recurrence "
            "in exact rational arithmetic: a few roundings per step, damped by "
            "c_outflow < 1, over at most nine steps and three sub-reaches",
        )


_MOMENT_POINTS: Final = ((3.0, 0.2, 1.5, 1), (1.0, 0.0, 1.9, 1), (12.0, 0.3, 2.0, 4))
"""(K, X, dt, N) of the impulse responses whose moments are checked."""


def _moments(run: Callable[..., Values]) -> None:
    for k_min, weight, step, count in _MOMENT_POINTS:
        impulse = np.zeros(600)
        impulse[1] = 1.0
        out = run(
            inflow_m3s=impulse,
            timestep_min=step,
            k_min=k_min,
            x=weight,
            subreaches=count,
            initial_outflow_m3s=0.0,
        ).array("outflow_m3s")
        times = step * np.arange(out.size, dtype=np.float64)
        mass = float(np.sum(out))
        mean = float(np.sum(times * out)) / mass
        variance = float(np.sum((times - mean) ** 2 * out)) / mass
        assert_within(
            [mean - step, variance],
            [k_min, k_min**2 * (1.0 - 2.0 * weight) / count],
            rel=1e-12,
            reason="the impulse response of the scheme has the mean delay K and the "
            "variance K^2 (1 - 2X) / N exactly (generating function); its tail beyond "
            "600 ordinates is below 1e-30 of its mass, the sums round at 1e-15",
        )


def _bounded(run: Callable[..., Values]) -> None:
    for values, step, k_min, weight, count, initial in _EXACT_POINTS:
        out = run(
            inflow_m3s=list(values),
            timestep_min=step,
            k_min=k_min,
            x=weight,
            subreaches=count,
            initial_outflow_m3s=initial,
        ).array("outflow_m3s")
        low = min(*values, initial)
        high = max(*values, initial)
        slack = 4 * np.spacing(high)
        if not ((out >= low - slack).all() and (out <= high + slack).all()):
            raise AssertionError(
                f"muskingum: outflow {out} leaves [{low}, {high}], the range of the "
                "inflow and the initial outflow, though non-negative weights that sum "
                "to 1 make every ordinate a weighted mean of them"
            )


# --- the spec ------------------------------------------------------------------------

_HEC_HMS = hec_hms(
    "Muskingum Model",
    "muskingum-model",
    "equations of the storage and of the weights; X from 0 to 0.5; sub-reaches whose "
    "travel time is about the time step",
)
_EM = em_1110_2_1417("chapter 9, eqs. 9-15 to 9-19, pp. 9-12 to 9-15")
_NEH = neh630_17("eqs. 17-6 to 17-11 and the Muskingum method, pp. 17-14 to 17-18")
_MCCARTHY = Source(
    citation="McCarthy, G.T. (1938). The unit hydrograph and flood routing, "
    "Conference of the North Atlantic Division, US Army Corps of Engineers, New "
    "London, Conn.",
    access="author-provided",
)
_POSITIVITY = Source(
    citation="the signs of the numerators of the weights (Hydrolog ADR-0008); "
    "Ponce's form |C - D| <= 1 <= C + D",
    locator="c_current >= 0 iff dt >= 2KX/N, c_previous >= 0 iff dt >= -2KX/N, "
    "c_outflow >= 0 iff dt <= 2K(1 - X)/N",
)
_EXACT_SCALING = Tolerance(
    rel=0.0,
    abs=1e-300,
    reason="a power of two scales every product and sum of the recurrence exactly in "
    "binary, but for subnormal discharges, which round to fewer digits",
)

MUSKINGUM: Final = FormulaSpec(
    name="muskingum",
    title="Muskingum routing through N equal sub-reaches (McCarthy's storage, "
    "trapezoid continuity)",
    function="hydrolog.routing.formulas.muskingum.muskingum_route",
    family="scheme",
    equation=(
        "in each of N sub-reaches of k = K / N in series: O[t] = c0 I[t] + c1 I[t-1] "
        "+ c2 O[t-1], c0 = (dt - 2 k X) / D, c1 = (dt + 2 k X) / D, c2 = (2 k (1 - X) "
        "- dt) / D, D = 2 k (1 - X) + dt; O[0] = O0 in every sub-reach; storage "
        "S = k sum_j [X I_j + (1 - X) O_j] [m3]"
    ),
    latex=(
        r"O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1},\quad "
        r"c_0 = \frac{\Delta t - 2kX}{D},\ c_1 = \frac{\Delta t + 2kX}{D},\ "
        r"c_2 = \frac{2k(1-X) - \Delta t}{D},\ D = 2k(1-X) + \Delta t,\ "
        r"k = \frac{K}{N}"
    ),
    variables=(
        inflow(),
        timestep(),
        Variable(
            name="k_min",
            symbol="K",
            unit="min",
            description="Travel time of the whole reach, the storage constant K.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=12000.0,
                test_reason="ten times the longest K of Hydrolog's routing tests, the "
                "Iowa example's 20 h (1,200 min)",
            ),
            applicability="unstated",
            typical=Range(
                low=10.0,
                high=1200.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="K of 10 to 60 min in the tests of the reach, 2.3 h "
                    "(NPTEL) and 20 h (Iowa) in the published examples",
                ),
            ),
        ),
        Variable(
            name="x",
            symbol="X",
            unit="-",
            description="Weight of the inflow in the storage: 0 a linear reservoir, "
            "0.5 a wave that does not attenuate.",
            physical=Range(low=0.0, high=0.5, source=_HEC_HMS),
            applicability=Range(low=0.0, high=0.5, source=_HEC_HMS),
            typical=Range(
                low=0.1,
                high=0.3,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="X of 0.2 in most tests of the reach, 0.15 (NPTEL) and "
                    "0.25 (Iowa) in the published examples; 0.1 to 0.3 for natural "
                    "streams after Fread (1993), as Balaz, Danacova and Szolgay "
                    "(2010, Slovak Journal of Civil Engineering 18(3)) cite it",
                ),
            ),
        ),
        Variable(
            name="subreaches",
            symbol="N",
            unit="-",
            kind="integer",
            description="Number of equal sub-reaches of K / N in series.",
            physical=Range(
                low=1.0,
                test_high=1000.0,
                test_reason="K / dt of the test bound of K (12,000 min) on a step of "
                "12 min, the rule of thumb of the sub-reaches",
            ),
            applicability="unstated",
            typical=Range(
                low=1.0,
                high=10.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="1 to 3 sub-reaches in the tests of the reach and in the "
                    "published examples; K / dt rounded up to 10 in the network tests",
                ),
            ),
        ),
        initial_outflow(),
    ),
    outputs=(
        outflow(),
        Output(
            name="c_current",
            unit="-",
            symbol="c_0",
            description="Weight of I[t] in one sub-reach.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="c_previous",
            unit="-",
            symbol="c_1",
            description="Weight of I[t-1] in one sub-reach.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="c_outflow",
            unit="-",
            symbol="c_2",
            description="Weight of O[t-1] in one sub-reach.",
            physical=Range(low=0.0, high=1.0),
        ),
        storage(
            "storage_start_m3", "Water held by the sub-reaches at the first ordinate."
        ),
        storage(
            "storage_end_m3", "Water held by the sub-reaches at the last ordinate."
        ),
        storage(
            "storage_steady_m3",
            "Water they would hold at rest under the last inflow, K I[-1].",
        ),
    ),
    sources=(_HEC_HMS, _EM, _NEH, _MCCARTHY),
    constraints=(
        Constraint(
            name="representable",
            cls="precondition",
            check=_representable,
            text="dt, K / N and dt / (K / N) >= 2.2e-308, the smallest normal "
            "float64, and 2 K [s] and the water K max(I, O0) [m3] are finite: below, "
            "the weights round to fewer digits or those of the inflow underflow and "
            "the water that enters is lost; above, the weights are NaN",
            source=Source(
                citation="IEEE 754 binary64, the float64 of NumPy: largest finite "
                "number 1.8e308, smallest normal 2.2e-308",
                locator="the ratio of the step to K / N in the weights, K in seconds "
                "in their denominator and the storage K max(I, O0)",
            ),
            satisfied={"timestep_min": 60.0},
            violated={"timestep_min": 5e-324, "x": 0.0},
        ),
        Constraint(
            name="nonnegative_weights",
            cls="precondition",
            check=_in_window,
            text="2 K X / N <= dt <= 2 K (1 - X) / N, each end to 1e-9 of itself: "
            "every weight is non-negative, so a non-negative inflow gives a "
            "non-negative outflow",
            source=_POSITIVITY,
            satisfied={"timestep_min": 60.0},
            boundary={"k_min": 120.0, "x": 0.5, "subreaches": 2},
            violated={"timestep_min": 97.0},
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
                inputs={"timestep_min": 1, "k_min": 1},
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
                text="the trapezoid continuity holds in every sub-reach: inflow volume "
                "- outflow volume = storage at the end - storage at the start",
                residual=_volume_kept,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="relative to the largest volume or storage: the recurrence "
                    "rounds at 1e-16 per step; a weight that rounding put below zero "
                    "on a border of the window is set to zero, which moves the others "
                    "by at most the window's slack of 1e-9",
                ),
            ),
        ),
        limits=(
            Limit(
                name="lag_of_one_step",
                text="X = 0.5 and K = N dt with N = 1: c0 = c2 = 0 and c1 = 1, the "
                "outflow is the inflow one step later (HEC-HMS: Muskingum with X = 0.5 "
                "and K = dt is the lag of one step)",
                inputs={
                    "inflow_m3s": [0.0, 10.0, 40.0, 20.0, 5.0],
                    "timestep_min": 30.0,
                    "k_min": 30.0,
                    "x": 0.5,
                    "subreaches": 1,
                    "initial_outflow_m3s": 0.0,
                },
                expected={"outflow_m3s": [0.0, 0.0, 10.0, 40.0, 20.0]},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="c0 = 0, c1 = 1 and c2 = 0 exactly: the products and sums "
                    "are exact",
                ),
            ),
            Limit(
                name="steady_state",
                text="an inflow equal to the initial outflow passes unchanged: the "
                "weights sum to 1",
                inputs={
                    "inflow_m3s": [7.5] * 12,
                    "timestep_min": 10.0,
                    "k_min": 45.0,
                    "x": 0.2,
                    "subreaches": 3,
                    "initial_outflow_m3s": 7.5,
                },
                expected={"outflow_m3s": [7.5] * 12},
                tolerance=Tolerance(
                    rel=1e-15,
                    reason="the weights sum to 1 to rounding; each step rounds a "
                    "product and a sum, damped by c_outflow < 1",
                ),
            ),
            Limit(
                name="exact_recurrence",
                text="every outflow equals the recurrence of the sub-reaches in exact "
                "rational arithmetic",
                check=_exact_recurrence,
            ),
            Limit(
                name="moments",
                text="the impulse response has the mean delay K and the variance "
                "K^2 (1 - 2X) / N, whatever dt",
                check=_moments,
            ),
            Limit(
                name="bounded_by_its_inputs",
                text="every outflow lies between the least and the largest of the "
                "inflow and the initial outflow",
                check=_bounded,
            ),
        ),
    ),
    validation=(
        "none: K and X are calibrated on observed floods of a reach (HEC-HMS TRM, "
        "Muskingum model; EM 1110-2-1417 ch. 9); the sources report no agreement of "
        "the scheme itself with observations"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "SI units: discharge in m3/s, time in min, storage in m3 (K in min times a "
        "discharge in m3/s times the 60 s of a minute of the units table)",
        (
            "the weights are named by what they multiply: c_current I[t], "
            "c_previous I[t-1], c_outflow O[t-1]; NEH 630 and HEC-HMS call them C2, "
            "C1 and C3, the Iowa and NPTEL examples C1, C2 and C3"
        ),
        (
            "continuity by the trapezoid rule, (S[t] - S[t-1]) / dt = (I[t] + I[t-1]) "
            "/ 2 - (O[t] + O[t-1]) / 2, with S = k [X I + (1 - X) O] in each sub-reach"
        ),
        (
            "N equal sub-reaches of K / N in series with the same X (HEC-HMS); every "
            "sub-reach starts at rest with O0, so at the first ordinate all but the "
            "first are fed by O0"
        ),
        (
            "within the window's slack a weight that rounding puts below zero is set "
            "to zero and the others are divided by their sum "
            "(hydrolog.routing._kernels.nonnegative_coefficients)"
        ),
        (
            "only the given ordinates are routed: MuskingumReach chooses N (K / dt "
            "rounded) and the sub-steps of a step without a window, interpolates the "
            "inflow linearly between them, and extends the time axis (Tier B, ADR-0008)"
        ),
    ),
    assumptions=(
        (
            "the storage of the reach is linear in a weighted discharge, "
            "S = K [X I + (1 - X) O], with K and X constant over the flood"
        ),
        "no backwater: the outflow does not depend on the water downstream",
    ),
    traps={
        "difference_denominator": "c_current = (dt - 2KX/N) / D vanishes on the "
        "window's lower end: limit lag_of_one_step gives it exactly 0; "
        "D = 2K(1 - X)/N + dt >= dt > 0 never vanishes",
        "stability_bound": "the window 2KX/N <= dt <= 2K(1 - X)/N: constraint "
        "nonnegative_weights with its satisfied, boundary and violated points, and "
        "test_a_border_of_the_window_rounds_to_zero_weights",
        "gap_propagation": "type cases inflow_m3s-nan_element and "
        "inflow_m3s-inf_element: a gap is refused, the recurrence would carry it to "
        "every later ordinate",
        "many_small_terms": "test_a_long_steady_inflow_stays_steady: 200,000 "
        "ordinates of a constant inflow stay constant to 1e-14",
    },
    reference_cases=("tests/fixtures/formulas/muskingum-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the recurrence of the sub-reaches and its weights in exact "
            "rational arithmetic (fractions), loop by loop",
            test="tests/unit/test_formulas_muskingum.py (limit exact_recurrence)",
        ),
        Oracle(
            kind="exact",
            description="the moments of the impulse response, mean K and variance "
            "K^2 (1 - 2X) / N, from the generating function "
            "(c0 + c1 s) / (1 - c2 s) of the scheme",
            test="tests/unit/test_formulas_muskingum.py (limit moments)",
        ),
    ),
    base={
        "timestep_min": 60.0,
        "k_min": 120.0,
        "x": 0.2,
        "subreaches": 2,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (MUSKINGUM,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def muskingum_route(
    inflow_m3s: NDArray[np.float64] | Sequence[float],
    timestep_min: float,
    k_min: float,
    x: float,
    subreaches: int,
    initial_outflow_m3s: float,
) -> MuskingumRoute:
    """Route a hydrograph through equal Muskingum sub-reaches, spec muskingum.

    The first input is the inflow at every ordinate and the last the outflow at the
    first one, both in cubic metres per second.

    Parameters
    ----------
    timestep_min : float
        Time step of the ordinates [min].
    k_min : float
        Travel time ``K`` of the whole reach [min].
    x : float
        Weighting factor ``X``.
    subreaches : int
        Number ``N`` of equal sub-reaches of ``K / N``.

    Returns
    -------
    MuskingumRoute
        The outflow at every ordinate, the weights of a sub-reach and the water held
        at the first and the last ordinate and at rest.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a gap, or a time step outside the window of non-negative
        weights of the sub-reaches (``precondition_failed``, constraint
        ``nonnegative_weights``).
    """
    values = checked_inputs(
        MUSKINGUM,
        inflow_m3s=inflow_m3s,
        timestep_min=timestep_min,
        k_min=k_min,
        x=x,
        subreaches=subreaches,
        initial_outflow_m3s=initial_outflow_m3s,
    )
    out = checked_outputs(MUSKINGUM, _route(values))
    return MuskingumRoute(
        outflow_m3s=out.array("outflow_m3s"),
        c_current=out.real("c_current"),
        c_previous=out.real("c_previous"),
        c_outflow=out.real("c_outflow"),
        storage_start_m3=out.real("storage_start_m3"),
        storage_end_m3=out.real("storage_end_m3"),
        storage_steady_m3=out.real("storage_steady_m3"),
    )
