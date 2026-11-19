"""Clark Instantaneous Unit Hydrograph (IUH) and its unit hydrograph of a duration.

The Clark method models watershed runoff by the translation of a time-area curve and
the attenuation of a linear reservoir (Clark 1945). The formula is declared by its
spec :data:`CLARK` (``clark``, Nogat's computation standard, ADR-0050, ADR-0058)
beside :func:`clark_unit_hydrograph`, and the model's lag by :data:`CLARK_LAG`
(``clark_lag``) beside :func:`clark_lag_time`; ``docs/FORMULAS.md`` shows their
equations, constants, ranges and sources. :class:`ClarkIUH` keeps the interface of
earlier versions and computes through the specs.

Reference:
    Clark, C.O. (1945). Storage and the Unit Hydrograph.
    Transactions of the American Society of Civil Engineers, 110, 1419-1446.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, cast

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._ranges import warn_if_outside
from hydrolog._serialization import JsonResultMixin
from hydrolog.nogat_formulas import (
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
from hydrolog.routing._kernels import route_linear_reservoir
from hydrolog.runoff._uh_specs import (
    AREA,
    AREA_TYPICAL,
    MAX_ORDINATES,
    ORDINATES_SOURCE,
    TC,
    TC_TYPICAL,
    TIMESTEP,
    TIMESTEP_TYPICAL,
    hec_trm_2000,
    hec_trm_online,
)

__all__ = [
    "CLARK",
    "CLARK_LAG",
    "SPECS",
    "ClarkIUH",
    "ClarkIUHResult",
    "ClarkUHResult",
    "clark_lag_time",
    "clark_unit_hydrograph",
]

_STEP_TOLERANCE: Final = 1e-9
"""Relative excess of the time step over ``2 R`` that is still accepted (rounding)."""

_SMALLEST: Final = float(np.finfo(np.float64).tiny)
"""The smallest normal float64."""

_UNIT_AREA_KM2: Final = 1.0
"""The area the instantaneous unit hydrograph is computed for, then divided out."""


@dataclass
class ClarkIUHResult(JsonResultMixin):
    """
    Result of Clark Instantaneous Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_per_min : NDArray[np.float64]
        Ordinates [1/min]: the unit hydrograph of a rainfall of one time step,
        holding one unit of volume (the mean of the reservoir's outflow over the
        step, HEC-HMS's averaged outflow).
    tc_min : float
        Time of concentration [min].
    r_min : float
        Storage coefficient [min].
    time_to_peak_min : float
        Time to peak discharge [min].
    peak_ordinate_per_min : float
        Peak IUH ordinate [1/min].
    """

    times_min: NDArray[np.float64]
    ordinates_per_min: NDArray[np.float64]
    tc_min: float
    r_min: float
    time_to_peak_min: float
    peak_ordinate_per_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


@dataclass
class ClarkUHResult(JsonResultMixin):
    """
    Result of Clark Unit Hydrograph (finite duration D, spec ``clark``).

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    duration_min : float
        Rainfall duration D [min].
    area_km2 : float
        Watershed area [km²].
    tc_min : float
        Time of concentration [min].
    r_min : float
        Storage coefficient [min].
    time_to_peak_min : float
        Time of the largest ordinate [min].
    peak_discharge_m3s : float
        Largest ordinate [m³/s per mm].
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    duration_min: float
    area_km2: float
    tc_min: float
    r_min: float
    time_to_peak_min: float
    peak_discharge_m3s: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


# --- the steps of the formula ---------------------------------------------------------


def _time_area(ratio: NDArray[np.float64]) -> NDArray[np.float64]:
    """Return the cumulative share A(t) / A of the elliptical watershed at t / tc."""
    factor = CLARK.constant("time_area_factor")
    exponent = CLARK.constant("time_area_exponent")
    tau = np.clip(ratio, 0.0, 1.0)
    rising = factor * tau**exponent
    falling = 1.0 - factor * (1.0 - tau) ** exponent
    return np.where(tau <= 0.5, rising, falling)


def _count(x: Values) -> int | None:
    """Return the number of ordinates, or None beyond a million or float64."""
    try:
        count = max(math.ceil(x.real("total_duration_min") / x.real("timestep_min")), 1)
    except OverflowError:  # a quotient of inf
        return None
    return count + 1 if count < MAX_ORDINATES else None


def _step_stable(x: Values) -> bool:
    """Return whether the precondition step_stable holds: dt <= 2 R."""
    limit = 2.0 * x.real("r_min") * (1.0 + _STEP_TOLERANCE)
    return x.real("timestep_min") <= limit


def _length_bounded(x: Values) -> bool:
    """Return whether the precondition length_bounded holds."""
    return _count(x) is not None


def _volume_m3(area_km2: float) -> float:
    """Return the volume of 1 mm over the watershed [m³]."""
    return convert(area_km2, "km2", "m2") * convert(1.0, "mm", "m")


def _representable(x: Values) -> bool:
    """Return whether float64 holds the first outflow and 1 mm over D per second."""
    step, r = x.real("timestep_min"), x.real("r_min")
    first = float(_time_area(np.array([step / x.real("tc_min")]))[0])
    weight = step / (2.0 * r + step)
    seconds = convert(x.real("duration_min"), "min", "s")
    if not (first * weight >= _SMALLEST and seconds >= _SMALLEST):
        return False
    return math.isfinite(_volume_m3(x.real("area_km2")) / seconds)


def _iuh(x: Values) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the times and the ordinates of one unit routed from the time-area curve.

    The translation hydrograph is the increment of the time-area curve over each step,
    routed through the linear reservoir on the trapezoid rule and divided by its
    volume: the response to one unit of rainfall in one step [1/min].
    """
    step = x.real("timestep_min")
    times = np.arange(cast(int, _count(x)), dtype=np.float64) * step
    inflow = np.diff(_time_area(times / x.real("tc_min")), prepend=0.0)
    # a step accepted within 1e-9 above 2 R weighs the reservoir as 2 R: no negative
    # weight of the previous outflow from the rounding of 2 R
    r = x.real("r_min")
    outflow = route_linear_reservoir(inflow, r, min(step, 2.0 * r))
    return times, outflow / (np.sum(outflow) * step)


def _hydrograph(x: Values) -> dict[str, object]:
    """Return the outputs of checked inputs.

    With c the cumulative sums of the ordinates u of one step, S(t_i) = dt c_i+1 the
    S-curve and D = m dt + rem (m whole, 0 <= rem < dt), the S-curve lagged by D is
    read linearly between the grid points, so that

        S(t_i) - S(t_i - D) = dt (c_i+1 - c_i-m+1) + rem u_i-m,

    with c and u 0 before the grid: the D-hour unit hydrograph is that over D, in
    m³/s per mm. Written so, a D much shorter than the step loses no digits.
    """
    times, units = _iuh(x)
    step, duration = x.real("timestep_min"), x.real("duration_min")
    count = times.size
    ratio = duration / step
    whole = count if not ratio < count else math.floor(ratio)
    remainder = duration - whole * step if whole < count else 0.0
    cumulative = np.concatenate(([0.0], np.cumsum(units)))
    index = np.arange(count)
    lagged = index - whole
    window = cumulative[index + 1] - cumulative[np.clip(lagged + 1, 0, count)]
    tail = np.where(lagged >= 0, units[np.clip(lagged, 0, count - 1)], 0.0)
    rise = step * window + remainder * tail
    per_second = _volume_m3(x.real("area_km2")) / convert(duration, "min", "s")
    ordinates = rise * per_second
    peak = int(np.argmax(ordinates))
    return {
        "times_min": times,
        "ordinates_m3s": ordinates,
        "time_to_peak_min": float(times[peak]),
        "peak_discharge_m3s": float(ordinates[peak]),
    }


# --- properties and oracles (CMP-6.2, CMP-6.5) ----------------------------------------


def _hec_recursion(tc: float, r: float, step: float, count: int) -> NDArray[np.float64]:
    """Return the unit ordinates of HEC-HMS's form of the scheme [1/min].

    O_t = CA I_t + CB O_t-1 with CA = dt / (R + dt / 2) and CB = 1 - CA, its unit
    hydrograph the mean of two outflows (HEC-HMS 2000 eqs. 47 to 49), on the grid and
    time-area curve of the formula, divided by its volume.
    """
    times = np.arange(count, dtype=np.float64) * step
    share = []
    for t in times:
        tau = min(max(t / tc, 0.0), 1.0)
        share.append(
            1.414 * tau**1.5 if tau <= 0.5 else 1.0 - 1.414 * (1.0 - tau) ** 1.5
        )
    inflow = np.diff(np.array(share), prepend=0.0)
    ca = step / (r + 0.5 * step)
    outflow, previous, averaged = 0.0, 0.0, []
    for current in inflow:
        outflow = ca * current + (1.0 - ca) * previous
        averaged.append((previous + outflow) / 2.0)
        previous = outflow
    mean = np.array(averaged)
    return mean / (math.fsum(mean) * step)


_HEC_POINTS: Final = (
    {"tc_min": 120.0, "r_min": 60.0, "timestep_min": 10.0},
    {"tc_min": 60.0, "r_min": 30.0, "timestep_min": 5.0},
    {"tc_min": 90.0, "r_min": 10.0, "timestep_min": 20.0},  # dt = 2 R
)
"""Inputs of the oracle of HEC-HMS's recursion."""


def _hec_form(run: Callable[..., Values]) -> None:
    for point in _HEC_POINTS:
        step = point["timestep_min"]
        total = point["tc_min"] + 5.0 * point["r_min"] + step
        out = run(**point, duration_min=step, total_duration_min=total, area_km2=1.0)
        ordinates = out.array("ordinates_m3s")
        units = ordinates / (_volume_m3(1.0) / convert(1.0, "min", "s"))
        expected = _hec_recursion(point["tc_min"], point["r_min"], step, ordinates.size)
        assert_within(
            units,
            expected,
            rel=1e-12,
            abs=1e-15,
            reason="HEC-HMS's recursion with the averaged outflow is the formula's "
            "trapezoid rule on the inflow for a reservoir at rest: the same numbers "
            "summed in another order, to a few units in the last place",
        )


def _hec_truncation(run: Callable[..., Values]) -> None:
    """HEC-HMS's own end, at 0.995 of the volume, rescaled to one unit."""
    out = run(
        tc_min=120.0,
        r_min=60.0,
        area_km2=45.3,
        duration_min=10.0,
        timestep_min=10.0,
        total_duration_min=430.0,
    )
    units = _hec_recursion(120.0, 60.0, 10.0, 2000)
    shares = np.cumsum(units) * 10.0
    end = int(np.searchsorted(shares, 0.995)) + 1
    kept = units[:end] / (math.fsum(units[:end]) * 10.0)
    peak = int(np.argmax(kept))
    expected = kept[peak] * _volume_m3(45.3) / convert(1.0, "min", "s")
    assert out.real("time_to_peak_min") == peak * 10.0
    assert_within(
        out.real("peak_discharge_m3s"),
        expected,
        rel=5e-3,
        reason="the research case clark-hec-hms-trm-oracle: HEC-HMS ends the "
        "hydrograph at 0.995 of its volume, the formula at tc + 5 R + D, and both "
        "rescale to one unit (5.8398 against 5.8528 m3/s per mm, -0.22 %)",
    )


def _volume_of_the_default_length(run: Callable[..., Values]) -> None:
    for duration in (10.0, 2.5, 15.0, 30.0, 47.0):
        total = 120.0 + 5.0 * 60.0 + duration
        out = run(duration_min=duration, total_duration_min=total, area_km2=45.3)
        seconds = convert(10.0, "min", "s")
        depth = math.fsum(out.array("ordinates_m3s")) * seconds / _volume_m3(45.3)
        assert_within(
            depth,
            1.0,
            abs=2e-3,
            reason="the grid to tc + 5 R + D: the ordinates of one step hold 1 mm, "
            "and the S-curve's last D, short of 1 by the reservoir's tail beyond tc "
            "+ 5 R, keeps 0.9985 mm or more",
        )


# --- the spec -------------------------------------------------------------------------

_TIME_AREA: Final = hec_trm_2000(
    "Clark's unit hydrograph model, eq. 50, p. 59: At / A = 1.414 (t / tc)^1.5 for t "
    "<= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for t >= tc / 2"
)

CLARK: Final = FormulaSpec(
    name="clark",
    title="Clark's unit hydrograph of a duration: time-area curve and linear reservoir",
    function="hydrolog.runoff.clark_iuh.clark_unit_hydrograph",
    family="scheme",
    equation=(
        "A(t) / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 "
        "for tc / 2 < t < tc, 1 from tc; I_i = A(i dt) / A - A((i - 1) dt) / A; O_i = "
        "O_i-1 + C (I_i + I_i-1 - 2 O_i-1), C = dt / (2 R + dt), O and I 0 before the "
        "grid; u_i = O_i / (dt sum O); S(t) the S-curve of u, U_D(t) = (S(t) - S(t - "
        "D)) / D with S between grid points linear; q_i = U_D(i dt) A x 1 mm per s; i "
        "= 0 to max(1, ceil(T / dt))"
    ),
    latex=(
        r"\frac{A_t}{A} = 1.414\left(\frac{t}{t_c}\right)^{1.5},\ t \le "
        r"\frac{t_c}{2};\quad O_i = O_{i-1} + \frac{\Delta t}{2R + \Delta t}\,(I_i + "
        r"I_{i-1} - 2\,O_{i-1});\quad U_D(t) = \frac{S(t) - S(t - D)}{D}"
    ),
    variables=(
        Variable(
            name="tc_min",
            symbol="t_c",
            unit="min",
            description="Time of concentration, the translation time of the watershed.",
            physical=TC,
            applicability="unstated",
            typical=TC_TYPICAL,
        ),
        Variable(
            name="r_min",
            symbol="R",
            unit="min",
            description="Storage constant of the linear reservoir, S = R O.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=10440.0,
                test_reason="ten times the longest R of the Polish calibrations, "
                "17.4 h (Wałęga and Cupak 2013)",
            ),
            applicability="unstated",
            typical=Range(
                low=0.2,
                high=1050.0,
                source=Source(
                    citation="Wałęga, A. and Cupak, A. (2013). In Węglarczyk, S. "
                    "(ed.), Problemy obliczania przepływów ekstremalnych, Monografie "
                    "Komitetu Gospodarki Wodnej PAN 35, pp. 145-151",
                    locator="table 2, p. 148: R of 12.14 and 17.4 h calibrated for "
                    "the Stobnica (335.84 km2); and Hydrolog's R/tc of 0.2 to 1.5 "
                    "times the typical tc of 1 to 450 min, R from 0.2 min",
                    url="https://kgw.pan.pl/files/"
                    "35_Praca_zbiorowa_red_Stanisaw_Wglarczyk.pdf",
                ),
            ),
        ),
        Variable(
            name="area_km2",
            symbol="A",
            unit="km2",
            description="Area of the watershed.",
            physical=AREA,
            applicability="unstated",
            typical=AREA_TYPICAL,
        ),
        Variable(
            name="timestep_min",
            symbol=r"\Delta t",
            unit="min",
            description="Time step of the ordinates and of the reservoir.",
            physical=TIMESTEP,
            applicability="unstated",
            typical=TIMESTEP_TYPICAL,
        ),
        Variable(
            name="duration_min",
            symbol="D",
            unit="min",
            description="Duration of the unit of excess rainfall.",
            physical=TIMESTEP,
            applicability="unstated",
            typical=TIMESTEP_TYPICAL,
        ),
        Variable(
            name="total_duration_min",
            symbol="T",
            unit="min",
            description="Length of the hydrograph; ClarkIUH takes tc + 5 R + D.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=57600.0,
                test_reason="ten times the longest default length of the typical "
                "ranges",
            ),
            applicability="unstated",
            typical=Range(
                low=7.0,
                high=5760.0,
                source=Source(
                    citation="Hydrolog: the default length tc + 5 R + D over the "
                    "typical ranges of tc, R and D",
                    locator="1 + 5 x 0.2 + 5 = 7 to 450 + 5 x 1050 + 60 = 5,760 min",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="times_min",
            unit="min",
            kind="real_array",
            symbol="i \\Delta t",
            description="Times of the ordinates, from the beginning of the rainfall.",
            physical=Range(low=0.0),
        ),
        Output(
            name="ordinates_m3s",
            unit="m3/s per mm",
            kind="real_array",
            symbol="q_i",
            description="Ordinates of the unit hydrograph of the duration D.",
            physical=Range(low=0.0),
        ),
        Output(
            name="time_to_peak_min",
            unit="min",
            symbol="t_p",
            description="Time of the largest ordinate.",
            physical=Range(low=0.0),
        ),
        Output(
            name="peak_discharge_m3s",
            unit="m3/s per mm",
            symbol="q_p",
            description="Largest ordinate.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        hec_trm_2000("Clark's unit hydrograph model, eqs. 47-50, pp. 58-59"),
        hec_trm_online(
            "clark-unit-hydrograph-model",
            "Clark Unit Hydrograph Model: the time-area curve of an elliptical "
            "watershed, O_t = CA I_t + CB O_t-1, CA = dt / (R + 0.5 dt), the unit "
            "hydrograph the mean of two outflows",
        ),
    ),
    constants=(
        Constant(
            name="time_area_factor",
            value=1.414,
            unit="-",
            symbol="1.414",
            source=_TIME_AREA,
        ),
        Constant(
            name="time_area_exponent",
            value=1.5,
            unit="-",
            symbol="1.5",
            source=_TIME_AREA,
        ),
    ),
    constraints=(
        Constraint(
            name="step_stable",
            cls="precondition",
            check=_step_stable,
            text="the time step is at most twice the storage constant, dt <= 2 R (to "
            "1e-9 of 2 R for its rounding): beyond it the previous outflow has the "
            "negative weight (2 R - dt) / (2 R + dt) and the ordinates oscillate "
            "below 0",
            source=Source(
                citation="Hydrolog ADR-0008, the conventions of routing: the window of "
                "non-negative weights of the Muskingum scheme",
                locator="dt <= 2 K (1 - X), here X = 0 and K = R",
            ),
            satisfied={"timestep_min": 10.0},
            violated={"timestep_min": 130.0},
            boundary={"timestep_min": 120.0},
        ),
        Constraint(
            name="length_bounded",
            cls="precondition",
            check=_length_bounded,
            text="the grid has at most a million ordinates",
            source=ORDINATES_SOURCE,
            satisfied={"timestep_min": 10.0},
            violated={"timestep_min": 1.0e-4},
        ),
        Constraint(
            name="representable",
            cls="precondition",
            check=_representable,
            text="float64 holds the first outflow of the reservoir, C A(dt) / A, as a "
            "normal number and 1 mm over the watershed per second of D, A x 1 mm / D",
            source=Source(
                citation="IEEE 754 double precision (float64)",
                locator="normal numbers from 2.2e-308 to 1.8e308",
            ),
            satisfied={"duration_min": 10.0},
            violated={"duration_min": 1.0e-310},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="time",
                inputs={
                    "tc_min": 1,
                    "r_min": 1,
                    "duration_min": 1,
                    "timestep_min": 1,
                    "total_duration_min": 1,
                },
                outputs={
                    "times_min": 1,
                    "ordinates_m3s": -1,
                    "time_to_peak_min": 1,
                    "peak_discharge_m3s": -1,
                },
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling every time keeps t / tc, the weights of the "
                    "reservoir and D / dt and halves the ordinates exactly in binary, "
                    "but for subnormal ordinates",
                ),
            ),
            Scaling(
                name="area",
                inputs={"area_km2": 1},
                outputs={"ordinates_m3s": 1, "peak_discharge_m3s": 1},
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling the area doubles every ordinate exactly in "
                    "binary, but for subnormal ordinates",
                ),
            ),
        ),
        limits=(
            Limit(
                name="hec_form",
                text="the ordinates of D = dt are HEC-HMS's recursion of the "
                "reservoir with the mean of two outflows, on the same grid",
                check=_hec_form,
                source=hec_trm_2000("eqs. 47-49, p. 58"),
            ),
            Limit(
                name="hec_truncation",
                text="HEC-HMS's end of the hydrograph at 0.995 of its volume gives the "
                "same time to peak and the peak within 0.5 %",
                check=_hec_truncation,
            ),
            Limit(
                name="unit_volume",
                text="to the default length tc + 5 R + D the ordinates hold 1 mm "
                "over the watershed",
                check=_volume_of_the_default_length,
            ),
        ),
    ),
    validation=(
        "none: Clark (1945) and HEC-HMS give the model; its parameters tc and R are "
        "calibrated on gauged floods (HEC-HMS), and the sources give no error "
        "statistic"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "times in min from the beginning of the rainfall; ordinates in m3/s per mm",
        (
            "the time-area curve of HEC-HMS's elliptical watershed, 1.414 for the "
            "square root of 2 (the halves meet at 0.49992 and 0.50008, a step of "
            "1.6e-4)"
        ),
        (
            "the reservoir on the trapezoid rule, O_i = O_i-1 + C (I_i + I_i-1 - 2 "
            "O_i-1) with C = dt / (2 R + dt): HEC-HMS's O_t = CA I_t + CB O_t-1 and "
            "its mean of two outflows, the averaging moved from the outflow to the "
            "inflow, the same for a reservoir at rest"
        ),
        (
            "the grid ends at T (ClarkIUH: tc + 5 R + D), where HEC-HMS stops at 0.995 "
            "of the volume; both divide the routed ordinates by their volume, one unit"
        ),
        (
            "the unit hydrograph of D from the S-curve, S(t - D) read linearly between "
            "the grid points: D need not be a whole number of steps, and a D shorter "
            "than dt gives the hydrograph of D = dt"
        ),
        (
            "R/tc outside 0.2 to 1.5 gives the notice outside_unverified_range of "
            "ClarkIUH (clark.r_tc_ratio): no source publishes that range, and the "
            "Polish calibrations of the Stobnica give 1.7 to 2.3 (Wałęga and Cupak "
            "2013)"
        ),
    ),
    assumptions=(
        (
            "tc is the translation time from the farthest point of the watershed; the "
            "time-area curve is that of an elliptical watershed unless one is known"
        ),
        "excess rainfall uniform over the watershed and in time over D",
    ),
    traps={
        "stability_bound": "test_clark_steps_at_and_beyond_the_stability_bound: dt = "
        "2 R computes without a negative ordinate, dt beyond 2 R (1 + 1e-9) is "
        "refused by the precondition step_stable",
        "many_small_terms": "test_clark_a_million_ordinates_hold_their_volume: the "
        "volume of up to a million ordinates by NumPy's pairwise sum and cumulative "
        "sums",
    },
    oracles=(
        Oracle(
            kind="algorithm",
            description="HEC-HMS's recursion of the reservoir, O_t = CA I_t + CB "
            "O_t-1 with the mean of two outflows (HEC-HMS 2000 eqs. 47-49), on the "
            "formula's grid and time-area curve",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit hec_form)",
        ),
        Oracle(
            kind="algorithm",
            description="the same recursion ended at 0.995 of the volume as HEC-HMS "
            "ends it and rescaled to one unit: the research case "
            "clark-hec-hms-trm-oracle (tc 120 min, R 60 min, dt 10 min, A 45.3 km2), "
            "the peak within 0.5 %",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit hec_truncation)",
        ),
    ),
    base={
        "tc_min": 120.0,
        "r_min": 60.0,
        "area_km2": 45.3,
        "duration_min": 10.0,
        "timestep_min": 10.0,
        "total_duration_min": 430.0,
    },
)


def clark_unit_hydrograph(
    tc_min: float,
    r_min: float,
    area_km2: float,
    timestep_min: float,
    duration_min: float,
    total_duration_min: float,
) -> ClarkUHResult:
    """Return Clark's unit hydrograph of a rainfall duration, spec clark.

    The third input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    tc_min : float
        Time of concentration, the translation time [min].
    r_min : float
        Storage constant of the linear reservoir [min].
    timestep_min : float
        Time step of the ordinates [min].
    duration_min : float
        Duration of the unit of excess rainfall [min].
    total_duration_min : float
        Length of the hydrograph [min].

    Returns
    -------
    ClarkUHResult
        The ordinates at the step times, the largest and its time.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a step longer than twice the storage constant (precondition
        ``step_stable``, ``details.option`` ``timestep_min``), a grid of too many
        ordinates (``length_bounded``) or one a double cannot hold
        (``representable``).
    """
    x = checked_inputs(
        CLARK,
        tc_min=tc_min,
        r_min=r_min,
        area_km2=area_km2,
        duration_min=duration_min,
        timestep_min=timestep_min,
        total_duration_min=total_duration_min,
    )
    out = checked_outputs(CLARK, _hydrograph(x))
    return ClarkUHResult(
        times_min=out.array("times_min"),
        ordinates_m3s=out.array("ordinates_m3s"),
        duration_min=x.real("duration_min"),
        area_km2=x.real("area_km2"),
        tc_min=x.real("tc_min"),
        r_min=x.real("r_min"),
        time_to_peak_min=out.real("time_to_peak_min"),
        peak_discharge_m3s=out.real("peak_discharge_m3s"),
    )


# --- the lag of Clark's model: the spec clark_lag -------------------------------------


def _time_area_centroid(run: Callable[..., Values]) -> None:
    from scipy.integrate import quad

    def outside(ratio: float) -> float:
        return 1.0 - float(_time_area(np.array([ratio]))[0])

    share = quad(outside, 0.0, 1.0, points=[0.5], epsabs=1e-15, epsrel=1e-14)[0]
    for tc, r in ((120.0, 60.0), (60.0, 30.0), (90.0, 10.0), (450.0, 1050.0)):
        assert_within(
            run(tc_min=tc, r_min=r).real("lag_time_min"),
            share * tc + r,
            rel=1e-14,
            reason="the centroid of the time-area curve, the integral of 1 - A(t) / A "
            "over t / tc from 0 to 1, by adaptive quadrature: 1/2 within 1e-15",
        )


def _unit_hydrograph_centroid(run: Callable[..., Values]) -> None:
    step = 0.25
    for tc, r in ((120.0, 60.0), (90.0, 10.0), (30.0, 45.0), (450.0, 1050.0)):
        shape = clark_unit_hydrograph(tc, r, 1.0, step, step, tc + 40.0 * r)
        times, ordinates = shape.times_min, shape.ordinates_m3s
        centroid = math.fsum((times * ordinates).tolist()) / math.fsum(
            ordinates.tolist()
        )
        assert_within(
            run(tc_min=tc, r_min=r).real("lag_time_min"),
            centroid - step / 2.0,
            abs=1e-4,
            reason="the first moment of the unit hydrograph of D = dt = 0.25 min of "
            "the spec clark to tc + 40 R, less the rainfall's centroid D / 2: the "
            "grid's time-area increments move it by 7.6e-5 dt, 1.9e-5 min, and the "
            "reservoir's tail beyond tc + 40 R holds e^-40 of the unit",
        )


CLARK_LAG: Final = FormulaSpec(
    name="clark_lag",
    title="Lag of Clark's model: the centroid of the time-area curve plus R",
    function="hydrolog.runoff.clark_iuh.clark_lag_time",
    family="scheme",
    equation="t_lag = tc / 2 + R",
    latex=r"t_{lag} = \frac{t_c}{2} + R",
    variables=(CLARK.variable("tc_min"), CLARK.variable("r_min")),
    outputs=(
        Output(
            name="lag_time_min",
            unit="min",
            symbol=r"t_{lag}",
            description="Lag time, the first moment of Clark's instantaneous unit "
            "hydrograph from the instant of the rainfall.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(
        hec_trm_2000(
            "Clark's unit hydrograph model, eq. 50, p. 59: the time-area curve of an "
            "elliptical watershed, whose centroid is at tc / 2; eqs. 47-49, p. 58: "
            "the linear reservoir S = R O, whose response has the first moment R"
        ),
        Source(
            citation="Nash, J.E. (1959). Systematic determination of unit hydrograph "
            "parameters. Journal of Geophysical Research 64(1): 111-115",
            locator="the theorem of moments: the first moment of a linear system's "
            "response to an input is the input's first moment plus the IUH's, so "
            "translation and reservoir add their lags (not opened)",
            url="https://doi.org/10.1029/JZ064i001p00111",
        ),
    ),
    constants=(
        Constant(
            name="centroid_share",
            value=0.5,
            unit="-",
            symbol="1/2",
            source=_TIME_AREA,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"tc_min": 1, "r_min": 1},
        scalings=(
            Scaling(
                name="time",
                inputs={"tc_min": 1, "r_min": 1},
                outputs={"lag_time_min": 1},
                tolerance=Tolerance(
                    rel=0.0,
                    abs=1e-300,
                    reason="halving and adding doubled numbers is exact in binary, "
                    "but for subnormal times",
                ),
            ),
        ),
        limits=(
            Limit(
                name="time_area_centroid",
                text="tc / 2 is the centroid of the time-area curve: the integral of "
                "1 - A(t) / A over the curve, its two halves cancelling the factor "
                "1.414",
                check=_time_area_centroid,
            ),
            Limit(
                name="unit_hydrograph_centroid",
                text="the first moment of the spec clark's unit hydrograph on a fine "
                "grid, less D / 2, is tc / 2 + R",
                check=_unit_hydrograph_centroid,
            ),
        ),
    ),
    validation=(
        "none: an exact property of the model; Clark's tc and R are calibrated on "
        "gauged floods (HEC-HMS), and the sources give no error statistic"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "the lag from the instant of a unit of rainfall to the centroid of the "
        "response, in min; the unit hydrograph of D lags a further D / 2 after the "
        "rainfall's beginning",
        (
            "the centroid of HEC-HMS's elliptical time-area curve is tc / 2 whatever "
            "its factor (1.414): the areas its two halves cut off from the line A = "
            "1 are equal"
        ),
    ),
    assumptions=(
        "the time-area curve of an elliptical watershed (spec clark); another curve "
        "has another centroid",
    ),
    no_traps_reason=(
        "half of one input plus another: no denominator, iteration, gap or long sum"
    ),
    oracles=(
        Oracle(
            kind="algorithm",
            description="the centroid of the time-area curve by adaptive quadrature "
            "(scipy.integrate.quad, SciPy 1.18.1)",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit "
            "time_area_centroid)",
        ),
        Oracle(
            kind="algorithm",
            description="the first moment of the unit hydrograph of the spec clark on "
            "a grid of 0.25 min, less D / 2",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit "
            "unit_hydrograph_centroid)",
        ),
    ),
    base={"tc_min": 120.0, "r_min": 60.0},
)


def clark_lag_time(tc_min: float, r_min: float) -> float:
    """Return the lag of Clark's model, spec clark_lag.

    Parameters
    ----------
    tc_min : float
        Time of concentration, the translation time [min].
    r_min : float
        Storage constant of the linear reservoir [min].

    Returns
    -------
    float
        Lag time from the instant of the rainfall to the centroid of the response
        [min].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``).
    """
    x = checked_inputs(CLARK_LAG, tc_min=tc_min, r_min=r_min)
    lag = CLARK_LAG.constant("centroid_share") * x.real("tc_min") + x.real("r_min")
    return checked_outputs(CLARK_LAG, {"lag_time_min": lag}).real("lag_time_min")


SPECS: Final = (CLARK, CLARK_LAG)
"""The Tier A formulas of the module."""


# --- the interface of earlier versions ------------------------------------------------


def _default_length(tc_min: float, r_min: float, duration_min: float = 0.0) -> float:
    """Return tc + 5 R (+ D), the default length, or NaN of values the spec refuses."""
    try:
        return float(tc_min + 5.0 * r_min + duration_min)
    except TypeError:
        return math.nan


class ClarkIUH:
    r"""
    Clark Instantaneous Unit Hydrograph (IUH), spec ``clark``.

    The Clark model represents watershed response through two processes:
    1. Translation: Excess rainfall is routed through the watershed using
       a time-area histogram that represents the fraction of area
       contributing to runoff at each time.
    2. Attenuation: The translation hydrograph is routed through a
       linear reservoir to account for storage effects.

    Keeps the parameters and computes with :func:`clark_unit_hydrograph` when a
    method is called, so that the spec checks every input then (the constructor
    checks nothing): a refusal is an :class:`~hydrolog.exceptions.InvalidParameterError`
    with the standard's ``details.reason``.

    Parameters
    ----------
    tc_min : float
        Time of concentration [min]. The time for water to travel from
        the most remote point in the watershed to the outlet.
    r_min : float
        Storage coefficient [min]. Represents the linear reservoir
        storage-discharge relationship (S = R * O).
    area_km2 : float, optional
        Watershed area [km²]. If provided, generate() returns the
        dimensional unit hydrograph [m³/s per mm].

    Notes
    -----
    ``docs/FORMULAS.md`` gives the equations, constants, ranges and sources of the
    spec. The time step must not exceed 2R: the weight of the previous outflow of
    the reservoir, (2R - dt) / (2R + dt), is negative beyond it and the scheme
    oscillates. An R/tc outside its range, which no source publishes, warns with
    :class:`~hydrolog._warnings.OutsideUnverifiedRange` at each computation.

    Key properties:
    - Lag time: the centroid of the time-area curve plus R, Tc/2 + R
    - Larger R values produce broader, flatter hydrographs
    - Larger Tc values shift the peak later

    References
    ----------
    Clark, C.O. (1945). Storage and the Unit Hydrograph.
    US Army Corps of Engineers, HEC-HMS Technical Reference Manual.

    Examples
    --------
    >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
    >>> result = iuh.generate(timestep_min=5.0)
    >>> print(f"Peak at {result.time_to_peak_min:.1f} min")
    Peak at 50.0 min
    """

    def __init__(
        self, tc_min: float, r_min: float, area_km2: float | None = None
    ) -> None:
        """
        Keep the parameters of the Clark model.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        r_min : float
            Storage coefficient [min].
        area_km2 : float, optional
            Watershed area [km²]. If provided, generate() returns
            dimensional unit hydrograph [m³/s per mm].
        """
        self.tc_min = tc_min
        self.r_min = r_min
        self.area_km2 = area_km2

    @property
    def lag_time_min(self) -> float:
        """
        Lag time [min], spec ``clark_lag``.

        Notes
        -----
        The centroid of the time-area curve of the elliptical watershed is at
        Tc/2; the linear reservoir adds R (:func:`clark_lag_time`).
        """
        return clark_lag_time(self.tc_min, self.r_min)

    def cumulative_time_area(self, t_min: float) -> float:
        """
        Calculate cumulative time-area fraction at time t.

        Uses the time-area curve of the elliptical watershed of HEC-HMS (spec
        ``clark``): 0 before the rainfall, 1 from Tc on, the two halves meeting
        at Tc/2.

        Parameters
        ----------
        t_min : float
            Time since start of rainfall [min].

        Returns
        -------
        float
            Cumulative fraction of watershed area contributing (0 to 1).
        """
        return float(_time_area(np.array([t_min / self.tc_min]))[0])

    def incremental_time_area(
        self, times_min: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """
        Calculate incremental time-area histogram.

        Parameters
        ----------
        times_min : NDArray[np.float64]
            Array of time values [min].

        Returns
        -------
        NDArray[np.float64]
            Incremental area fractions for each time interval.
        """
        times = np.asarray(times_min, dtype=np.float64)
        return np.diff(_time_area(times / self.tc_min), prepend=0.0)

    def _warn_ratio(self) -> None:
        """Warn of an R/tc outside its range, of parameters the spec accepted."""
        warn_if_outside("clark", "r_tc_ratio", self.r_min / self.tc_min, stacklevel=3)

    def generate(
        self,
        timestep_min: float = 5.0,
        duration_min: float | None = None,
    ) -> ClarkIUHResult | ClarkUHResult:
        """
        Generate Clark Unit Hydrograph.

        If area_km2 was provided in constructor, returns dimensional
        unit hydrograph [m³/s per mm]. Otherwise returns IUH [1/min].

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        duration_min : float, optional
            Total duration [min]. If not specified, uses Tc + 5*R.

        Returns
        -------
        ClarkIUHResult or ClarkUHResult
            ClarkIUHResult if area_km2 not provided (ordinates in 1/min).
            ClarkUHResult if area_km2 provided (ordinates in m³/s per mm).

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``), among them a
            ``timestep_min`` above ``2 * r_min`` (precondition ``step_stable``).

        Examples
        --------
        >>> # Without area - returns IUH
        >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        >>> result = iuh.generate(timestep_min=5.0)
        >>> print(f"Steps: {result.n_steps}")
        Steps: 43

        >>> # With area - returns dimensional UH
        >>> clark = ClarkIUH(tc_min=60.0, r_min=30.0, area_km2=45.0)
        >>> result = clark.generate(timestep_min=5.0)
        >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
        Peak: 11.60 m³/s per mm
        """
        if self.area_km2 is not None:
            # Return dimensional unit hydrograph
            return self.to_unit_hydrograph(
                area_km2=self.area_km2,
                duration_min=timestep_min,  # D = timestep for UH
                timestep_min=timestep_min,
                total_duration_min=duration_min,
            )
        return self.generate_iuh(timestep_min=timestep_min, duration_min=duration_min)

    def generate_iuh(
        self,
        timestep_min: float = 5.0,
        duration_min: float | None = None,
    ) -> ClarkIUHResult:
        """
        Generate Clark Instantaneous Unit Hydrograph.

        Always returns IUH regardless of area_km2 setting: the unit hydrograph of
        the spec ``clark`` for a rainfall of one step, per unit of volume.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        duration_min : float, optional
            Total duration of IUH [min]. If not specified, uses Tc + 5*R.

        Returns
        -------
        ClarkIUHResult
            Generated IUH with times and ordinates [1/min].

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``), among them a
            ``timestep_min`` above twice the storage coefficient (precondition
            ``step_stable``, ``details.option`` ``timestep_min``): the linear
            reservoir scheme would give negative ordinates.

        Examples
        --------
        >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        >>> result = iuh.generate_iuh(timestep_min=5.0)
        >>> print(f"Steps: {result.n_steps}")
        Steps: 43
        """
        total = (
            _default_length(self.tc_min, self.r_min)
            if duration_min is None
            else duration_min
        )
        shape = clark_unit_hydrograph(
            self.tc_min, self.r_min, _UNIT_AREA_KM2, timestep_min, timestep_min, total
        )
        self._warn_ratio()
        per_unit = _volume_m3(_UNIT_AREA_KM2) / convert(1.0, "min", "s")
        ordinates = shape.ordinates_m3s / per_unit
        return ClarkIUHResult(
            times_min=shape.times_min,
            ordinates_per_min=ordinates,
            tc_min=shape.tc_min,
            r_min=shape.r_min,
            time_to_peak_min=shape.time_to_peak_min,
            peak_ordinate_per_min=shape.peak_discharge_m3s / per_unit,
        )

    def to_unit_hydrograph(
        self,
        area_km2: float,
        duration_min: float,
        timestep_min: float = 5.0,
        total_duration_min: float | None = None,
    ) -> ClarkUHResult:
        r"""
        Convert IUH to D-minute Unit Hydrograph (spec ``clark``).

        Generates the unit hydrograph of an effective rainfall of duration D by
        the S-curve method: the S-curve of the IUH minus the same curve lagged
        by D, divided by D.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        duration_min : float
            Rainfall duration D [min]. Need not be a multiple of
            ``timestep_min``.
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.
        total_duration_min : float, optional
            Total duration of output UH [min]. If not specified,
            uses Tc + 5*R + duration.

        Returns
        -------
        ClarkUHResult
            Unit hydrograph with ordinates in m³/s per mm.

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``), among them a
            ``timestep_min`` above ``2 * r_min`` (``precondition_failed``,
            ``details.constraint`` ``step_stable``).

        Notes
        -----
        With S(t) the S-curve (the cumulative sum of the IUH ordinates, i.e.
        the response to a continuous unit-rate input), the D-minute unit
        hydrograph is

        .. math::
            U_D(t) = \frac{S(t) - S(t - D)}{D}

        S is known at the grid points ``t_i = i * dt`` only (``dt`` is
        ``timestep_min``). The lagged curve S(t_i - D) is read from S by linear
        interpolation (S = 0 before t = 0), so D need not be a whole multiple of
        the time step; for D = k * dt it is exactly S(t_{i-k}). With
        ``m = floor(D / dt)`` and ``f = D / dt - m`` the ordinates are a
        weighted moving average of the IUH ordinates ``u_j``:

        .. math::
            U_D(t_i) = \frac{dt}{D}\left(\sum_{j=i-m+1}^{i} u_j
            + f \, u_{i-m}\right)

        Volume: the volume of the result is
        :math:`\frac{dt}{D} \sum_i [S(t_i) - S(t_i - D)]`. For the
        piecewise-linear S this sum is :math:`\frac{dt}{D}\left(f \, S_{n-m-1}
        + \sum_{j=n-m}^{n-1} S_j\right)`, which equals 1 (mm) whenever S has
        reached 1 at the last ``m + 1`` grid points, for any D > 0. Only the
        part of the response that lies beyond ``total_duration_min`` is missing.
        Shifting S by the rounded number of steps instead, while dividing by D,
        gives the volume ``round(D / dt) * dt / D`` (1.33 mm for D = 1.5 dt).

        The S-curve is resolved to one time step: a D shorter than ``dt``
        gives the hydrograph of D = ``dt``. Use ``timestep_min <= duration_min``
        to resolve a short rainfall.

        Examples
        --------
        >>> iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        >>> uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)
        >>> print(f"Peak: {uh.peak_discharge_m3s:.2f} m³/s per mm")
        Peak: 10.87 m³/s per mm

        D need not be a multiple of the time step (volume is still 1 mm):

        >>> uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=7.5)
        >>> print(f"Depth: {uh.ordinates_m3s.sum() * 5.0 * 60.0 / 45000.0:.3f} mm")
        Depth: 1.000 mm
        """
        total = (
            _default_length(self.tc_min, self.r_min, duration_min)
            if total_duration_min is None
            else total_duration_min
        )
        result = clark_unit_hydrograph(
            self.tc_min, self.r_min, area_km2, timestep_min, duration_min, total
        )
        self._warn_ratio()
        return result

    @classmethod
    def from_tc_r_ratio(
        cls,
        tc_min: float,
        r_tc_ratio: float = 0.5,
    ) -> ClarkIUH:
        """
        Create ClarkIUH from time of concentration and R/Tc ratio.

        Parameters
        ----------
        tc_min : float
            Time of concentration [min].
        r_tc_ratio : float, optional
            Ratio of R to Tc, by default 0.5.

        Returns
        -------
        ClarkIUH
            Configured Clark IUH generator, R = r_tc_ratio * tc_min; the spec
            checks R and tc when it computes.

        Notes
        -----
        The R/Tc ratio characterizes watershed storage: a larger one gives a lower
        and later peak. Outside 0.2-1.5 the computation warns
        (``outside_unverified_range``): no source publishes that range; HEC-HMS
        gives none, and the Polish calibrations of the Stobnica give 1.7-2.3
        (Wałęga and Cupak 2013).

        Examples
        --------
        >>> iuh = ClarkIUH.from_tc_r_ratio(tc_min=90.0, r_tc_ratio=0.5)
        >>> print(f"R = {iuh.r_min:.1f} min")
        R = 45.0 min
        """
        return cls(tc_min=tc_min, r_min=r_tc_ratio * tc_min)
