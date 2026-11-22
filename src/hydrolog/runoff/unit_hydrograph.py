"""SCS (NRCS) dimensionless unit hydrograph (NEH 630 chapter 16).

The formula is declared by its spec :data:`SCS` (``scs``, Nogat's computation standard,
ADR-0050, ADR-0057) beside :func:`scs_unit_hydrograph`; ``docs/FORMULAS.md`` shows its
equation, constants, ranges and sources. The ratios of the dimensionless unit
hydrograph, table 16-1 of NEH 630 chapter 16, are the data file
``src/hydrolog/_data/tables/neh630_duh.csv`` (CMP-2.5). :class:`SCSUnitHydrograph`
keeps the interface of earlier versions and computes through the spec.
"""

from __future__ import annotations

import csv
import itertools
import math
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Final, NamedTuple, cast

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._ranges import typical_range
from hydrolog._serialization import JsonResultMixin
from hydrolog._warnings import UhSubsteps
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
    Table,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)
from hydrolog.runoff._uh_specs import (
    AREA,
    AREA_TYPICAL,
    CHOW_NOTES,
    MAX_ORDINATES,
    NEH4_16,
    ORDINATES_SOURCE,
    TC,
    TC_TYPICAL,
    TIMESTEP,
    TIMESTEP_TYPICAL,
    hec_trm_2000,
    neh630_16,
)

__all__ = [
    "SCS",
    "SCS_DIMENSIONLESS_UH",
    "SPECS",
    "SCSUnitHydrograph",
    "UnitHydrographResult",
    "scs_unit_hydrograph",
]

# --- the table (CMP-2.5) --------------------------------------------------------------

_TABLE_PATH: Final = (
    Path(__file__).resolve().parents[1] / "_data" / "tables" / "neh630_duh.csv"
)


def _read_table() -> NDArray[np.float64]:
    with _TABLE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = [
            (float(row["t_over_tp"]), float(row["q_over_qp"]))
            for row in csv.DictReader(handle)
        ]
    table = np.array(rows, dtype=np.float64)
    table.setflags(write=False)
    return table


SCS_DIMENSIONLESS_UH: Final = _read_table()
"""Table 16-1 of NEH 630 chapter 16: t/Tp (column 0) and q/qp (column 1), read-only."""

_STEP_SHARE: Final = cast(float, typical_range("scs", "timestep_min").maximum)
"""The longest unit duration, a share of Tp (NEH 630 p. 16A-3), the range of the time
step that ``hydrograph generate`` checks: a longer step is computed on sub-steps."""

_SMALLEST: Final = np.finfo(np.float64).tiny
"""The smallest normal float64: a peak below it would lose digits to underflow."""


@dataclass
class UnitHydrographResult(JsonResultMixin):
    """
    Result of unit hydrograph generation (spec ``scs``).

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    time_to_peak_min : float
        Time to peak discharge tp [min].
    peak_discharge_m3s : float
        Peak discharge qp of the formula for the duration of the step [m³/s per
        mm]: the largest ordinate when the step is a whole fraction of tp, else a
        little above it, and well above it when the step was computed on sub-steps.
    time_base_min : float
        Time base of the hydrograph tb [min].
    lag_time_min : float
        Lag time tlag [min].
    timestep_min : float
        Time step [min].
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    time_to_peak_min: float
    peak_discharge_m3s: float
    time_base_min: float
    lag_time_min: float
    timestep_min: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


# --- the steps of the formula ---------------------------------------------------------


class _Plan(NamedTuple):
    """The lag, the peak of the step and the grid the ordinates are computed on."""

    lag_min: float
    time_to_peak_min: float
    peak: float
    time_base_min: float
    substeps: int
    substep_min: float


def _peak(area_km2: float, time_to_peak_min: float) -> float:
    """Return qp = C A / Tp per cm of runoff as m³/s per mm."""
    per_cm = (
        SCS.constant("peak_factor") * area_km2 / convert(time_to_peak_min, "min", "h")
    )
    return per_cm * convert(1.0, "mm", "cm")


def _count(time_to_peak_min: float, step_min: float) -> int:
    """Return the number of ordinates of a step's grid, to the end of the table."""
    return math.ceil(_END * time_to_peak_min / step_min) + 1


def _plan(area_km2: float, tc_min: float, timestep_min: float) -> _Plan | None:
    """Return the plan of the computation, or None where float64 cannot hold it.

    Without sub-steps the grid is that of the step. A step longer than its share of
    Tp is divided into n equal sub-steps d = D / n, the fewest with d at most the
    share of Tp(d) = d / 2 + tlag: d <= share tlag / (1 - share / 2). The count n is
    a closed form, corrected for the rounding of the bound at most twice; beyond
    2**53 sub-steps a whole count is no longer a float64, and the plan is refused.
    """
    try:
        lag = SCS.constant("lag_ratio") * tc_min
        tp = timestep_min / 2.0 + lag
        peak = _peak(area_km2, tp)
        substeps, step = 1, timestep_min
        if timestep_min > _STEP_SHARE * tp:
            longest = _STEP_SHARE * lag / (1.0 - _STEP_SHARE / 2.0)
            if not longest >= _SMALLEST or timestep_min / longest > 2.0**53:
                return None
            substeps = max(2, math.ceil(timestep_min / longest))
            for _ in range(2):
                step = timestep_min / substeps
                if step <= _STEP_SHARE * (step / 2.0 + lag):
                    break
                substeps += 1
            step = timestep_min / substeps
            if step > _STEP_SHARE * (step / 2.0 + lag):
                return None
        sub_tp = step / 2.0 + lag
        sub_peak = _peak(area_km2, sub_tp)
        numbers = (lag, tp, peak, step, sub_tp, sub_peak)
        if not all(math.isfinite(n) for n in numbers):
            return None
        counts = (_count(sub_tp, step), _count(tp, timestep_min))
    except ArithmeticError:  # a quotient by an underflown time, or a count of inf
        return None
    if min(peak, sub_peak) < _SMALLEST or max(counts) > MAX_ORDINATES:
        return None
    return _Plan(lag, tp, peak, _END * tp, substeps, step)


def _steps_representable(x: Values) -> bool:
    """Return whether the precondition steps_representable holds."""
    return (
        _plan(x.real("area_km2"), x.real("tc_min"), x.real("timestep_min")) is not None
    )


def _sampled(
    area_km2: float, lag_min: float, step_min: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the dimensionless hydrograph of a step sampled at its multiples."""
    tp = step_min / 2.0 + lag_min
    times = np.arange(_count(tp, step_min), dtype=np.float64) * step_min
    ratios = np.interp(
        times / tp,
        SCS_DIMENSIONLESS_UH[:, 0],
        SCS_DIMENSIONLESS_UH[:, 1],
        left=0.0,
        right=0.0,
    )
    return times, ratios * _peak(area_km2, tp)


def _spread(
    area_km2: float, lag_min: float, timestep_min: float, substeps: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the response to 1 mm spread over the sub-steps, at the step times.

    With u the unit hydrograph of a sub-step d on the sub-steps and n of them in a
    step, the step's 1 mm is 1/n mm in each, so the ordinate at the step time k n d
    is the mean of u over the n sub-steps up to it, (u[(k - 1) n + 1] + ... +
    u[k n]) / n: the discrete convolution on the sub-steps read at every n-th of
    them, from cumulative sums, so that a large n costs nothing. The ordinates sum to
    the sub-steps' ordinates divided by n, hence the same volume. The last one is 0.
    """
    _, fine = _sampled(area_km2, lag_min, timestep_min / substeps)
    last = fine.size - 1  # u[last] is 0: t / tp beyond the table
    cumulative = np.concatenate(([0.0], np.cumsum(fine)))
    steps = -(-last // substeps) + 1
    sums = [
        cumulative[min(k * substeps, last) + 1]
        - cumulative[min(max((k - 1) * substeps + 1, 0), last + 1)]
        for k in range(steps + 1)
    ]
    times = np.arange(steps + 1, dtype=np.float64) * timestep_min
    return times, np.asarray(sums, dtype=np.float64) / substeps


def _hydrograph(x: Values) -> tuple[dict[str, object], _Plan]:
    """Return the outputs of checked inputs and the plan they were computed by."""
    area, step = x.real("area_km2"), x.real("timestep_min")
    plan = cast(_Plan, _plan(area, x.real("tc_min"), step))
    if plan.substeps == 1:
        times, ordinates = _sampled(area, plan.lag_min, step)
    else:
        times, ordinates = _spread(area, plan.lag_min, step, plan.substeps)
    outputs: dict[str, object] = {
        "peak_discharge_m3s": plan.peak,
        "time_to_peak_min": plan.time_to_peak_min,
        "lag_time_min": plan.lag_min,
        "time_base_min": plan.time_base_min,
        "times_min": times,
        "ordinates_m3s": ordinates,
    }
    return outputs, plan


# --- properties and oracles (CMP-6.2, CMP-6.5) ----------------------------------------


def _volume_mm(x: Values, out: Values) -> float:
    """Return the depth the ordinates hold over the watershed [mm]."""
    seconds = convert(x.real("timestep_min"), "min", "s")
    depth_m = (
        math.fsum(out.array("ordinates_m3s"))
        * seconds
        / convert(x.real("area_km2"), "km2", "m2")
    )
    return convert(depth_m, "m", "mm")


def _unit_volume(x: Values, out: Values) -> float:
    return _volume_mm(x, out) - 1.0


def _ratio(t_over_tp: Fraction) -> Fraction:
    """Return the linear interpolation of table 16-1 in exact rational arithmetic."""
    rows = [(Fraction(t), Fraction(q)) for t, q in SCS_DIMENSIONLESS_UH.tolist()]
    if t_over_tp >= rows[-1][0]:
        return Fraction(0)
    for (t0, q0), (t1, q1) in itertools.pairwise(rows):
        if t0 <= t_over_tp <= t1:
            return q0 + (q1 - q0) * (t_over_tp - t0) / (t1 - t0)
    return Fraction(0)


def _exact_ordinates(
    area: float, tc: float, step: float, substeps: int, count: int
) -> list[float]:
    """Return the first ``count`` ordinates of the equation in exact arithmetic."""
    lag = Fraction(3, 5) * Fraction(tc)
    sub = Fraction(step) / substeps
    sub_tp = sub / 2 + lag
    peak = Fraction(208, 100) * Fraction(area) / (sub_tp / 60) / 10

    def fine(k: int) -> Fraction:
        return peak * _ratio(k * sub / sub_tp)

    if substeps == 1:
        return [float(fine(k)) for k in range(count)]
    return [
        float(
            sum(fine(i) for i in range((j - 1) * substeps + 1, j * substeps + 1))
            / substeps
        )
        if j > 0
        else 0.0
        for j in range(count)
    ]


_EXACT_POINTS: Final = (
    (37.22, 187.39, 30.0, 1),  # Kamiennik at Świerzawa, its Kirpich tc, a 30 min step
    (11.9139453075456, 138.0, 18.0, 1),  # NEH 630 example 16-1, area A
    (45.3, 70.0, 12.0, 1),  # the step on the bound 0.25 Tp itself
    (45.3, 69.9, 12.0, 2),  # just beyond it: two sub-steps of 6 min
    (10.0, 90.7, 60.0, 4),  # E5b-07's watershed at an hour's step
)
"""Inputs of the exact oracle and the sub-steps the formula takes for them."""


def _exact_table(run: Callable[..., Values]) -> None:
    for area, tc, step, substeps in _EXACT_POINTS:
        out = run(area_km2=area, tc_min=tc, timestep_min=step)
        ordinates = out.array("ordinates_m3s")
        assert ordinates[-1] == 0.0
        assert_within(
            ordinates,
            _exact_ordinates(area, tc, step, substeps, ordinates.size),
            rel=1e-12,
            abs=1e-15,
            reason="the ordinates of float64 against Tp, qp, the linear interpolation "
            "of table 16-1 and the means over the sub-steps in exact rational "
            "arithmetic: a few units in the last place of each product and sum",
        )


def _recommended_duration(run: Callable[..., Values]) -> None:
    for tc in (60.0, 187.39, 450.0):
        step = 2.0 * tc / 15.0
        out = run(tc_min=tc, timestep_min=step)
        assert_within(
            step / out.real("time_to_peak_min"),
            0.2,
            rel=1e-15,
            reason="D = 2 tc / 15 (NEH 630 eq. 16A-13, 0.133 tc) is D = 0.2 Tp "
            "exactly; float64 rounds D / 2 + 0.6 tc and the quotient",
        )
        assert_within(
            float(out.array("ordinates_m3s")[5]),
            out.real("peak_discharge_m3s"),
            rel=1e-14,
            reason="at D = 0.2 Tp the fifth ordinate falls at Tp, where table 16-1 "
            "gives q / qp = 1: the rounding of 5 D / Tp moves it by a few units in "
            "the last place",
        )


# --- the spec -------------------------------------------------------------------------

_TABLE_SOURCE: Final = neh630_16(
    "table 16-1, p. 16-4: time ratios t/Tp and discharge ratios q/qp (the same "
    "ratios in NEH-4 (1972), table 16.1)"
)

SCS: Final = FormulaSpec(
    name="scs",
    title="SCS (NRCS) dimensionless unit hydrograph of a unit duration",
    function="hydrolog.runoff.unit_hydrograph.scs_unit_hydrograph",
    family="scheme",
    equation=(
        "tlag = 0.6 * tc; Tp = D / 2 + tlag; qp = C * A / Tp [m3/s per cm of runoff, "
        "A in km2, Tp in h], C = 2.08, per mm qp / 10; q(t) = qp * f(t / Tp), f table "
        "16-1 of NEH 630 ch. 16 interpolated linearly, 0 beyond t / Tp = 5, so Tb = 5 "
        "Tp; the ordinates are q(k D). For D > 0.25 Tp the ordinate at k D is the "
        "mean of the ordinates q_d(j d) of the sub-step d = D / n over the n "
        "sub-steps ending at k D, d the longest with d <= 0.25 Tp(d)"
    ),
    latex=(
        r"t_{lag} = 0.6\,t_c,\quad T_p = \frac{D}{2} + t_{lag},\quad q_p = "
        r"\frac{C\,A}{T_p},\quad q_k = q_p\,f\!\left(\frac{k\,D}{T_p}\right),\quad "
        r"T_b = 5\,T_p"
    ),
    variables=(
        Variable(
            name="area_km2",
            symbol="A",
            unit="km2",
            description="Area of the watershed.",
            physical=AREA,
            applicability=Range(
                low=0.0,
                high=51.8,
                source=neh630_16(
                    "p. 16-4: no subarea to exceed 20 square miles (51.8 km2), the "
                    "largest no more than 10 times the smallest"
                ),
            ),
            typical=AREA_TYPICAL,
        ),
        Variable(
            name="tc_min",
            symbol="t_c",
            unit="min",
            description="Time of concentration of the watershed.",
            physical=TC,
            applicability="unstated",
            typical=TC_TYPICAL,
        ),
        Variable(
            name="timestep_min",
            symbol="D",
            unit="min",
            description="Time step of the hydrograph and duration of its unit of "
            "excess rainfall.",
            physical=TIMESTEP,
            applicability="unstated",
            typical=TIMESTEP_TYPICAL,
        ),
    ),
    outputs=(
        Output(
            name="peak_discharge_m3s",
            unit="m3/s per mm",
            symbol="q_p",
            description="Peak discharge of the formula for the duration D.",
            physical=Range(low=0.0),
        ),
        Output(
            name="time_to_peak_min",
            unit="min",
            symbol="T_p",
            description="Time to peak from the beginning of the unit excess.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="lag_time_min",
            unit="min",
            symbol="t_{lag}",
            description="Watershed lag, from the centre of the unit excess to Tp.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="time_base_min",
            unit="min",
            symbol="T_b",
            description="Time base: the end of table 16-1.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="times_min",
            unit="min",
            kind="real_array",
            symbol="k D",
            description="Times of the ordinates, from the beginning of the excess.",
            physical=Range(low=0.0),
        ),
        Output(
            name="ordinates_m3s",
            unit="m3/s per mm",
            kind="real_array",
            symbol="q_k",
            description="Ordinates of the unit hydrograph of the duration D.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        neh630_16(
            "table 16-1, p. 16-4; appendix 16A, eqs. 16A-6 to 16A-9 and 16A-13, pp. "
            "16A-2 to 16A-3; example 16-1, pp. 16-7 to 16-13"
        ),
        hec_trm_2000("SCS unit hydrograph model, eqs. 36-38, pp. 55-56"),
        CHOW_NOTES,
    ),
    constants=(
        Constant(
            name="lag_ratio",
            value=0.6,
            unit="-",
            symbol="0.6",
            source=neh630_16(
                "eq. 16A-9, p. 16A-2: L = 0.6 Tc (after NEH 630 ch. 15); HEC-HMS "
                "2000, eq. 38, p. 56"
            ),
        ),
        Constant(
            name="peak_factor",
            value=2.08,
            unit="m3 s^-1 km^-2 cm^-1 h",
            symbol="C",
            source=hec_trm_2000(
                "eq. 36, p. 55: C = 2.08 in SI and 484 in foot-pound units; Chow et "
                "al. 1988, after Rajagopalan's notes, p. 79: C = 2.08 (483.4 in "
                "English units)"
            ),
        ),
        Constant(
            name="step_share",
            value=_STEP_SHARE,
            unit="-",
            symbol="0.25",
            source=neh630_16(
                "p. 16A-3: the unit duration D is 0.2 Tp and no greater than 0.25 Tp; "
                "HEC-HMS 2000, p. 55: less than 29 % of tlag"
            ),
        ),
    ),
    constraints=(
        Constraint(
            name="steps_representable",
            cls="precondition",
            check=_steps_representable,
            text="float64 holds tlag, Tp, the sub-step and the peaks as normal "
            "numbers, at most 2**53 sub-steps, and the grid of the step and of the "
            "sub-step have at most a million ordinates each",
            source=ORDINATES_SOURCE,
            satisfied={"timestep_min": 30.0},
            violated={"timestep_min": 1.0e-6},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": 1, "tc_min": -1, "timestep_min": -1},
        scalings=(
            Scaling(
                name="area",
                inputs={"area_km2": 1},
                outputs={"peak_discharge_m3s": 1, "ordinates_m3s": 1},
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling the area doubles every ordinate exactly in "
                    "binary, but for values below 1e-300 that float64's subnormal "
                    "numbers round on a fixed absolute step",
                ),
            ),
            Scaling(
                name="time",
                inputs={"tc_min": 1, "timestep_min": 1},
                outputs={
                    "peak_discharge_m3s": -1,
                    "time_to_peak_min": 1,
                    "lag_time_min": 1,
                    "time_base_min": 1,
                    "times_min": 1,
                    "ordinates_m3s": -1,
                },
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling every time keeps t / Tp and the sub-steps and "
                    "halves qp exactly in binary, but for subnormal values",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="unit_volume",
                text="the ordinates hold 1 mm over the watershed, sum(q_k) D = A * 1 "
                "mm, within the sampling of the table",
                residual=_unit_volume,
                tolerance=Tolerance(
                    abs=0.003,
                    reason="the continuous table holds 1.00036 mm at C = 2.08 (area "
                    "1.33595 Tp qp); sampled at D or d of at most 0.25 Tp it holds "
                    "0.99772 to 1.00138 mm over 20,001 ratios D / Tp of (0, 0.25]",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_table",
                text="the ordinates equal the equation in exact rational arithmetic, "
                "with and without sub-steps",
                check=_exact_table,
            ),
            Limit(
                name="recommended_duration",
                text="D = 2 tc / 15 gives D = 0.2 Tp and the peak ordinate qp at Tp "
                "(NEH 630 eqs. 16A-10 to 16A-13)",
                check=_recommended_duration,
                source=neh630_16("eqs. 16A-10 to 16A-13, p. 16A-3"),
            ),
        ),
    ),
    validation=(
        "Mockus (1957) derived the dimensionless unit hydrograph from many natural "
        "unit hydrographs of watersheds varying widely in size and geographical "
        "location (NEH 630-16, p. 16-2; HEC-HMS 2000, p. 55: small agricultural "
        "watersheds); the sources give no error statistic of its shape or peak"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "SI units: A in km2, times in min, ordinates in m3/s per mm of runoff; C "
            "= 2.08 is per cm (HEC-HMS 2000 eq. 36), per mm by the exact 10 mm/cm"
        ),
        (
            "C = 2.08 is NEH's peak rate factor 483.2 in foot-pound units, not 484: "
            "NEH 630 (p. 16A-2) gives table 16-1 the factor 483.4 from the rounding "
            "of its ratios; with 2.08 the continuous table holds 1.00036 mm"
        ),
        "times from the beginning of the unit excess; D is the time step",
        (
            "table 16-1 interpolated linearly between its rows, as NEH 630 table 16-2 "
            "does (t/Tp 2.1 gives 0.2435), and 0 from t/Tp = 5 on"
        ),
        (
            "the ordinates are the curve sampled at the step times (NEH 630 example "
            "16-1, step 2)"
        ),
        (
            "a step longer than 0.25 Tp is divided into sub-steps and the rain of the "
            "step spread evenly over them (notice uh_substeps): the volume stays 1 mm, "
            "while qp, Tp and Tb stay the formula's values for D, so qp then exceeds "
            "the largest ordinate (by 21 % for tc 90.7 min at a step of 60 min)"
        ),
    ),
    assumptions=(
        (
            "excess rainfall uniform over the watershed and in time over D; subareas "
            "of at most 20 square miles, the largest at most 10 times the smallest "
            "(NEH 630 p. 16-4), larger watersheds divided and their hydrographs routed"
        ),
        "tlag = 0.6 tc, the average relation of NEH 630 ch. 15",
        (
            "D = 0.2 Tp (D = 0.133 tc), at most 0.25 Tp (NEH 630 p. 16A-3); hydrograph "
            "generate warns outside_applicability of scs.timestep_min beyond it"
        ),
    ),
    notices=("uh_substeps",),
    traps={
        "stability_bound": "test_scs_steps_at_and_beyond_the_neh_bound: the step "
        "0.25 Tp itself is sampled as it is, the next one is computed on sub-steps "
        "and keeps its volume",
        "unbounded_iteration": "the count of sub-steps is a closed form corrected at "
        "most twice for rounding; range case tc_min-physical_low_inside: a sub-step "
        "float64 cannot hold is refused by the precondition steps_representable",
        "many_small_terms": "test_scs_a_day_step_keeps_its_volume: E5b-07, 93 "
        "sub-steps of a step of 1440 min summed by cumulative sums",
    },
    reference_cases=("tests/fixtures/formulas/unit-hydrographs-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the ordinates in exact rational arithmetic (fractions): Tp, "
            "qp, the linear interpolation of table 16-1 and the means over the "
            "sub-steps",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit exact_table)",
        ),
    ),
    tables=(
        Table(
            path="src/hydrolog/_data/tables/neh630_duh.csv",
            sha256="b465694f902953d282e964c34c7a535adc4cb8c833948ffca7c2a5080d871709",
            source=_TABLE_SOURCE,
            comparison=(
                "tests/oracles/neh630_duh_text_layer.csv (transcribed from the PDF's "
                "text layer by tests/oracles/transcribe_neh630_duh.py) against "
                "tests/oracles/neh630_duh_hydrolog_0_8_1.csv (typed for Hydrolog "
                f"0.8.1), compared by tests/unit/test_formulas_unit_hydrographs.py; "
                f"{NEH4_16}, table 16.1, prints the same ratios"
            ),
        ),
    ),
    base={"area_km2": 37.22},
)

_END: Final = float(SCS_DIMENSIONLESS_UH[-1, 0])
"""The end of table 16-1, t / Tp = 5: the time base in units of Tp."""


def scs_unit_hydrograph(
    area_km2: float, tc_min: float, timestep_min: float
) -> UnitHydrographResult:
    """Return the SCS dimensionless unit hydrograph of a unit duration, spec scs.

    The first input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    tc_min : float
        Time of concentration [min].
    timestep_min : float
        Time step of the hydrograph and duration of its unit of excess rainfall
        [min].

    Returns
    -------
    UnitHydrographResult
        The ordinates at the step times and the lag, time to peak, peak and time
        base of the formula.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, or steps a double cannot hold (precondition
        ``steps_representable``).

    Warns
    -----
    OutsideApplicability
        If the area is larger than the subareas of the method.
    UhSubsteps
        When the step was computed on sub-steps (notice ``uh_substeps``, info).
    """
    x = checked_inputs(SCS, area_km2=area_km2, tc_min=tc_min, timestep_min=timestep_min)
    raw, plan = _hydrograph(x)
    out = checked_outputs(SCS, raw)
    if plan.substeps > 1:
        warnings.warn(
            UhSubsteps(
                timestep_min=x.real("timestep_min"),
                maximum_min=_STEP_SHARE * plan.time_to_peak_min,
                substeps=plan.substeps,
                substep_min=plan.substep_min,
            ),
            stacklevel=2,
        )
    return UnitHydrographResult(
        times_min=out.array("times_min"),
        ordinates_m3s=out.array("ordinates_m3s"),
        time_to_peak_min=out.real("time_to_peak_min"),
        peak_discharge_m3s=out.real("peak_discharge_m3s"),
        time_base_min=out.real("time_base_min"),
        lag_time_min=out.real("lag_time_min"),
        timestep_min=x.real("timestep_min"),
    )


SPECS: Final = (SCS,)
"""The Tier A formula of the module."""


# --- the interface of earlier versions ------------------------------------------------


class SCSUnitHydrograph:
    """
    SCS (NRCS) dimensionless unit hydrograph of a watershed (spec ``scs``).

    Keeps the area and the time of concentration and computes with
    :func:`scs_unit_hydrograph` for the time step a method is given, so that the spec
    checks them there; the constructor checks nothing. ``docs/FORMULAS.md`` shows the
    equation, its constants and ranges, and table 16-1 of NEH 630 ch. 16.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    tc_min : float
        Time of concentration [min].

    Notes
    -----
    The time base of the curvilinear hydrograph is 5 tp, the end of table 16-1; its
    equivalent triangle (NEH 630, appendix 16A) ends at 2.67 tp. The unit hydrograph
    is the response to 1 mm of effective precipitation uniformly distributed over the
    watershed during one time step.

    References
    ----------
    USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology,
    Chapter 16: Hydrographs.

    Examples
    --------
    >>> uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
    >>> result = uh.generate(timestep_min=5.0)
    >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
    Peak: 9.94 m³/s per mm
    >>> print(f"Steps: {result.n_steps}, tp = {result.time_to_peak_min:.1f} min")
    Steps: 58, tp = 56.5 min
    """

    def __init__(self, area_km2: float, tc_min: float) -> None:
        """
        Keep the area and the time of concentration.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        tc_min : float
            Time of concentration [min].
        """
        self.area_km2 = area_km2
        self.tc_min = tc_min

    @property
    def lag_time_min(self) -> float:
        """
        Lag time tlag [min] of spec ``scs``: the share of tc of the spec.

        The lag does not depend on the step; it is computed without the checks of
        the spec, which :meth:`generate` and the methods taking a step make.
        """
        return SCS.constant("lag_ratio") * self.tc_min

    def time_to_peak(self, timestep_min: float) -> float:
        """
        Calculate time to peak tp (spec ``scs``).

        Parameters
        ----------
        timestep_min : float
            Rainfall duration / time step [min].

        Returns
        -------
        float
            Time to peak tp [min].
        """
        return self.generate(timestep_min).time_to_peak_min

    def peak_discharge(self, timestep_min: float) -> float:
        """
        Calculate peak discharge of unit hydrograph (spec ``scs``).

        Parameters
        ----------
        timestep_min : float
            Time step [min].

        Returns
        -------
        float
            Peak discharge qp [m³/s per mm of effective rainfall].
        """
        return self.generate(timestep_min).peak_discharge_m3s

    def time_base(self, timestep_min: float) -> float:
        """
        Calculate time base of unit hydrograph (spec ``scs``): 5 tp.

        Parameters
        ----------
        timestep_min : float
            Time step [min].

        Returns
        -------
        float
            Time base tb [min], the end of table 16-1 (the equivalent triangle of
            NEH 630 ends at 2.67 tp).
        """
        return self.generate(timestep_min).time_base_min

    def generate(self, timestep_min: float = 5.0) -> UnitHydrographResult:
        """
        Generate SCS unit hydrograph (:func:`scs_unit_hydrograph`, spec ``scs``).

        The ordinates are the dimensionless unit hydrograph of the duration D =
        ``timestep_min`` sampled at the step times. A step longer than 0.25 tp leaves
        too few ordinates, and their sum would lose volume (0.52 mm instead of 1 mm
        for tc = 90.7 min at a step of 1440 min): it is divided into the fewest equal
        sub-steps inside that share, the unit hydrograph of a sub-step takes the 1 mm
        of the step spread evenly over them, and the result is read at the step
        times. It keeps the volume, while ``tp``, ``qp`` and ``tb`` stay the
        formula's values for D = ``timestep_min``.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 5.0.

        Returns
        -------
        UnitHydrographResult
            Generated unit hydrograph with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If the spec refuses the area, the time of concentration or the step.

        Warns
        -----
        OutsideApplicability
            If the area is larger than the subareas of the method.
        UhSubsteps
            When the step was computed on sub-steps (notice ``uh_substeps``, info).
        """
        return scs_unit_hydrograph(self.area_km2, self.tc_min, timestep_min)
