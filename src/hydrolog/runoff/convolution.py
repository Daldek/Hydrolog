"""Discrete convolution of effective rainfall with a unit hydrograph.

The formula is declared by its spec :data:`CONVOLUTION` (``uh_convolution``, Nogat's
computation standard, ADR-0050, ADR-0057) beside :func:`convolve_discrete`;
``docs/FORMULAS.md`` shows its equation, ranges and sources.

Examples
--------
>>> pe = [0.0, 5.0, 10.0, 8.0, 3.0]  # mm
>>> uh = [0.0, 0.5, 1.0, 0.8, 0.4, 0.1]  # m³/s per mm
>>> result = convolve_discrete(pe, uh, timestep_min=5.0)
>>> print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
Qmax = 19.50 m³/s
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
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
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)
from hydrolog.runoff._uh_specs import (
    MAX_ORDINATES,
    ORDINATES_SOURCE,
    TIMESTEP,
    TIMESTEP_TYPICAL,
    kzgw,
    neh630_16,
)

__all__ = ["CONVOLUTION", "SPECS", "HydrographResult", "convolve_discrete"]


@dataclass
class HydrographResult(JsonResultMixin):
    """
    Result of hydrograph generation (spec ``uh_convolution``).

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    discharge_m3s : NDArray[np.float64]
        Discharge values [m³/s].
    peak_discharge_m3s : float
        Peak discharge [m³/s].
    time_to_peak_min : float
        Time to peak discharge [min].
    total_volume_m3 : float
        Total runoff volume [m³].
    timestep_min : float
        Time step [min].
    """

    times_min: NDArray[np.float64]
    discharge_m3s: NDArray[np.float64]
    peak_discharge_m3s: float
    time_to_peak_min: float
    total_volume_m3: float
    timestep_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)

    @property
    def duration_min(self) -> float:
        """Total duration [min]."""
        if len(self.times_min) > 0:
            return float(self.times_min[-1])
        return 0.0


def _length_bounded(x: Values) -> bool:
    """Return whether the hydrograph has at most a million ordinates."""
    count = x.array("effective_precip_mm").size + x.array("unit_hydrograph_m3s").size
    return count - 1 <= MAX_ORDINATES


def _convolution(x: Values) -> dict[str, object]:
    discharge = np.convolve(
        x.array("effective_precip_mm"), x.array("unit_hydrograph_m3s"), mode="full"
    )
    step = x.real("timestep_min")
    times = np.arange(discharge.size, dtype=np.float64) * step
    peak = int(np.argmax(discharge))
    seconds = convert(step, "min", "s")
    return {
        "peak_discharge_m3s": float(discharge[peak]),
        "time_to_peak_min": float(times[peak]),
        "total_volume_m3": math.fsum(discharge) * seconds,
        "discharge_m3s": discharge,
        "times_min": times,
    }


def _volume_kept(x: Values, out: Values) -> float:
    """Return the relative difference of the volume from sum(Pe) sum(UH) dt."""
    expected = (
        math.fsum(x.array("effective_precip_mm"))
        * math.fsum(x.array("unit_hydrograph_m3s"))
        * convert(x.real("timestep_min"), "min", "s")
    )
    volume = out.real("total_volume_m3")
    return (volume - expected) / expected if expected > 0.0 else volume


_EXACT_POINTS: Final = (
    ([0.0, 1.4, 1.6, 2.1], [0.0, 0.57, 1.371, 1.772, 1.911, 1.887, 1.769], 30.0),
    ([2.0, 0.0, 5.5, 0.25, 12.0], [0.0, 0.5, 1.0, 0.8, 0.4, 0.1], 5.0),
    ([0.001] * 200, [0.0, 3.0e3, 7.0e3, 1.0e3], 60.0),
)
"""Inputs of the exact oracle: KZGW (2017) example 6.4 and two made-up storms."""


def _exact_sums(run: Callable[..., Values]) -> None:
    for pe, uh, step in _EXACT_POINTS:
        out = run(effective_precip_mm=pe, unit_hydrograph_m3s=uh, timestep_min=step)
        exact = [
            float(
                sum(
                    (
                        Fraction(pe[m]) * Fraction(uh[n - m])
                        for m in range(len(pe))
                        if 0 <= n - m < len(uh)
                    ),
                    Fraction(0),
                )
            )
            for n in range(len(pe) + len(uh) - 1)
        ]
        assert_within(
            out.array("discharge_m3s"),
            exact,
            rel=1e-14,
            abs=1e-300,
            reason="the sums of float64 products against the same sums in exact "
            "rational arithmetic: a few units in the last place per term",
        )


CONVOLUTION: Final = FormulaSpec(
    name="uh_convolution",
    title="Direct runoff of excess rainfall by discrete convolution with a unit "
    "hydrograph",
    function="hydrolog.runoff.convolution.convolve_discrete",
    family="scheme",
    equation=(
        "Q_n = sum over m of Pe_m * U_(n - m), n = 0 .. M + K - 2, Pe_m the excess of "
        "the interval starting at m dt, U_k the unit hydrograph's ordinate at k dt; "
        "t_n = n dt; V = sum(Q_n) dt"
    ),
    latex=r"Q_n = \sum_{m} P_{e,m}\,U_{n-m},\quad t_n = n\,\Delta t,\quad "
    r"V = \Delta t \sum_n Q_n",
    variables=(
        Variable(
            name="effective_precip_mm",
            symbol=r"P_{e,m}",
            unit="mm",
            kind="real_array",
            description="Effective rainfall of each step.",
            physical=Range(
                low=0.0,
                test_high=1825.0,
                test_reason="the world's largest daily rainfall, 1,825 mm at Foc-Foc, "
                "La Réunion, 7-8 January 1966 (WMO)",
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=20.0,
                source=kzgw(
                    "examples 6.1, 6.2 and 6.4, tables 6.1, 6.3 and 6.4, pp. 94-110: "
                    "effective rainfall of 0 to 15.3 mm per step"
                ),
            ),
        ),
        Variable(
            name="unit_hydrograph_m3s",
            symbol="U_k",
            unit="m3/s per mm",
            kind="real_array",
            description="Ordinates of the unit hydrograph of the step's duration, "
            "the first at t = 0.",
            physical=Range(
                low=0.0,
                test_high=1.0e5,
                test_reason="the SCS peak of a million km2 at a time to peak of 2 h "
                "(1.04e5 m3/s per mm)",
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=15.0,
                source=kzgw(
                    "examples 6.2 and 6.4, tables 6.2 and 6.3, pp. 100-110: ordinates "
                    "up to 1.911 m3/s per mm; NEH 630 example 16-1 (11.9 km2): 1.62"
                ),
            ),
        ),
        Variable(
            name="timestep_min",
            symbol=r"\Delta t",
            unit="min",
            description="Time step of the rainfall and of the unit hydrograph.",
            physical=TIMESTEP,
            applicability="unstated",
            typical=TIMESTEP_TYPICAL,
        ),
    ),
    outputs=(
        Output(
            name="peak_discharge_m3s",
            unit="m3/s",
            symbol="Q_{max}",
            description="Largest ordinate of the hydrograph.",
            physical=Range(low=0.0),
        ),
        Output(
            name="time_to_peak_min",
            unit="min",
            symbol="t_{max}",
            description="Time of the first largest ordinate.",
            physical=Range(low=0.0),
        ),
        Output(
            name="total_volume_m3",
            unit="m3",
            symbol="V",
            description="Volume of the hydrograph, sum(Q_n) dt.",
            physical=Range(low=0.0),
        ),
        Output(
            name="discharge_m3s",
            unit="m3/s",
            kind="real_array",
            symbol="Q_n",
            description="Direct runoff at t_n.",
            physical=Range(low=0.0),
        ),
        Output(
            name="times_min",
            unit="min",
            kind="real_array",
            symbol="t_n",
            description="Times of the ordinates.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        kzgw("eq. 6.12, p. 92; examples 6.2 and 6.4, pp. 100-110"),
        neh630_16("example 16-1, steps 4-10 and table 16-4, pp. 16-10 to 16-13"),
    ),
    constraints=(
        Constraint(
            name="length_bounded",
            cls="precondition",
            check=_length_bounded,
            text="the hydrograph has at most a million ordinates, M + K - 1",
            source=ORDINATES_SOURCE,
            satisfied={"effective_precip_mm": [1.0, 2.0]},
            violated={"effective_precip_mm": [0.0] * MAX_ORDINATES},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"effective_precip_mm": 1, "unit_hydrograph_m3s": 1},
        scalings=(
            Scaling(
                name="rainfall",
                inputs={"effective_precip_mm": 1},
                outputs={
                    "peak_discharge_m3s": 1,
                    "total_volume_m3": 1,
                    "discharge_m3s": 1,
                },
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling every depth doubles every product and sum "
                    "exactly in binary, but for subnormal values",
                ),
            ),
            Scaling(
                name="unit_hydrograph",
                inputs={"unit_hydrograph_m3s": 1},
                outputs={
                    "peak_discharge_m3s": 1,
                    "total_volume_m3": 1,
                    "discharge_m3s": 1,
                },
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling every ordinate doubles every product and sum "
                    "exactly in binary, but for subnormal values",
                ),
            ),
            Scaling(
                name="time",
                inputs={"timestep_min": 1},
                outputs={"time_to_peak_min": 1, "total_volume_m3": 1, "times_min": 1},
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling the step doubles the times and the volume "
                    "exactly in binary and leaves the discharges as they are",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="volume",
                text="the volume is the excess times the unit hydrograph's volume, "
                "sum(Q) dt = sum(Pe) sum(U) dt",
                residual=_volume_kept,
                tolerance=Tolerance(
                    abs=1e-12,
                    reason="np.convolve's float64 products and pairwise sums against "
                    "two fsum totals: a few units in the last place per term, "
                    "relative",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_sums",
                text="every ordinate equals its sum of products in exact rational "
                "arithmetic",
                check=_exact_sums,
            ),
        ),
    ),
    validation="none: the convolution is the superposition that the unit hydrograph "
    "assumes; its sources report no agreement of their own with observations",
    formula_version=1,
    status="referenced",
    conventions=(
        "SI units: depths in mm, ordinates in m3/s per mm, discharges in m3/s",
        (
            "Pe_m is the excess of the interval from m dt to (m + 1) dt and U_0 the "
            "ordinate at t = 0: Q_n at t = n dt is the response at the end of interval "
            "n, as KZGW eq. 6.12 and NEH example 16-1 align them (Q(0.6 h) = 0.12 in x "
            "UH(0.3 h))"
        ),
        "the unit hydrograph is that of the duration dt, the step of the rainfall",
        "V = dt sum(Q_n), the sum taken exactly (math.fsum)",
    ),
    assumptions=(
        (
            "linearity and time invariance of the watershed's response to excess "
            "rainfall, uniform over the watershed"
        ),
    ),
    traps={
        "many_small_terms": "limit exact_sums: 200 steps of 0.001 mm against the "
        "sums in exact rational arithmetic",
        "gap_propagation": "type cases effective_precip_mm-nan_element and "
        "unit_hydrograph_m3s-nan_element: a gap is refused before it spreads",
    },
    reference_cases=("tests/fixtures/formulas/unit-hydrographs-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the ordinates as sums of products in exact rational "
            "arithmetic (fractions)",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit exact_sums)",
        ),
    ),
)


def convolve_discrete(
    effective_precip_mm: NDArray[np.float64] | list[float],
    unit_hydrograph_m3s: NDArray[np.float64] | list[float],
    timestep_min: float,
) -> HydrographResult:
    """
    Return the direct runoff hydrograph of excess rainfall, spec uh_convolution.

    The second input is the unit hydrograph of the step's duration in cubic metres
    per second per millimetre, its first ordinate at the beginning of the excess
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    effective_precip_mm : array_like of float
        Effective precipitation of each time step [mm].
    timestep_min : float
        Time step [min].

    Returns
    -------
    HydrographResult
        The hydrograph, its peak, the time of the peak and the volume.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): an empty series, a gap,
        a negative value, or a hydrograph longer than the bound of the spec.
    """
    x = checked_inputs(
        CONVOLUTION,
        effective_precip_mm=effective_precip_mm,
        unit_hydrograph_m3s=unit_hydrograph_m3s,
        timestep_min=timestep_min,
    )
    out = checked_outputs(CONVOLUTION, _convolution(x))
    return HydrographResult(
        times_min=out.array("times_min"),
        discharge_m3s=out.array("discharge_m3s"),
        peak_discharge_m3s=out.real("peak_discharge_m3s"),
        time_to_peak_min=out.real("time_to_peak_min"),
        total_volume_m3=out.real("total_volume_m3"),
        timestep_min=x.real("timestep_min"),
    )


SPECS: Final = (CONVOLUTION,)
"""The Tier A formula of the module."""
