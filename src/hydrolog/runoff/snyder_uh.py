"""Snyder's synthetic unit hydrograph (Snyder 1938; KZGW 2017, annex 2, section 6.2).

Two formulas, each declared by its spec (Nogat's computation standard, ADR-0050,
ADR-0058) beside its function; ``docs/FORMULAS.md`` shows their equations, constants,
ranges and sources:

* :data:`SNYDER` (``snyder``), :func:`snyder_parameters`: the lag, the standard
  duration, the adjusted lag, time to peak and peak of a rainfall duration, the time
  base and the widths at 50 % and 75 % of the peak;
* :data:`SNYDER_SHAPE` (``snyder_shape``), :func:`snyder_shape`: the gamma curve of
  1 mm through that peak (Asquith and Roussel 2007), sampled at the time step.

:class:`SnyderUH` keeps the interface of earlier versions and computes through the
specs: it fills their defaults, the standard duration tD and the length of the curve
to the end of its recession, when 99.99 % of its volume has run off.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Final, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq
from scipy.special import gammaincinv, gammaln
from scipy.stats import gamma

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
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
from hydrolog.runoff._uh_specs import (
    AREA,
    AREA_TYPICAL,
    HEC_TRM_2000,
    INNOVYZE_SNYDER,
    KZGW,
    MAX_ORDINATES,
    ORDINATES_SOURCE,
    TIMESTEP,
    TIMESTEP_TYPICAL,
    chow_notes,
    handoffs,
    hec_trm_2000,
    hec_trm_online,
    kzgw,
)

__all__ = [
    "SNYDER",
    "SNYDER_SHAPE",
    "SPECS",
    "SnyderParameters",
    "SnyderShape",
    "SnyderUH",
    "SnyderUHResult",
    "snyder_parameters",
    "snyder_shape",
]

_SMALLEST: Final = float(np.finfo(np.float64).tiny)
"""The smallest normal float64: an output below it would lose digits to underflow."""

_EXPONENTS: Final = (1.0e-12, 1.0e12)
"""The bracket of the exponent K of the curve, the bounds of its root finding."""

_TAIL_VOLUME: Final = 1.0e-4
"""Share of the 1 mm beyond the default end of the curve: it runs to 99.99 %."""

_WIDTHS: Final = {50.0: "width_50_min", 75.0: "width_75_min"}
"""The widths of the method by their percentage of the peak."""


@dataclass(frozen=True)
class SnyderParameters(JsonResultMixin):
    """The parameters of Snyder's unit hydrograph for a rainfall duration (``snyder``).

    Attributes
    ----------
    lag_time_min : float
        Basin lag tL [min].
    standard_duration_min : float
        Standard rainfall duration tD = tL / 5.5 [min].
    adjusted_lag_time_min : float
        Lag tLR of the duration D [min] (tL for D = tD).
    time_to_peak_min : float
        Time to peak tpR = tLR + D / 2 from the beginning of the rainfall [min].
    standard_peak_discharge_m3s : float
        Peak qp of the standard duration [m³/s per mm].
    peak_discharge_m3s : float
        Peak qpR of the duration D [m³/s per mm].
    time_base_min : float
        Base tb of the triangle of the peak qpR that holds 1 mm [min].
    width_50_min, width_75_min : float
        Widths W50 and W75 at 50 % and 75 % of the peak qpR [min].
    """

    lag_time_min: float
    standard_duration_min: float
    adjusted_lag_time_min: float
    time_to_peak_min: float
    standard_peak_discharge_m3s: float
    peak_discharge_m3s: float
    time_base_min: float
    width_50_min: float
    width_75_min: float


@dataclass(frozen=True)
class SnyderShape(JsonResultMixin):
    """The curve of Snyder's unit hydrograph on the time step (``snyder_shape``).

    Attributes
    ----------
    shape_exponent : float
        Exponent K of the curve [-].
    times_min : NDArray[np.float64]
        Times of the ordinates, from the beginning of the rainfall [min].
    ordinates_m3s : NDArray[np.float64]
        Ordinates [m³/s per mm], holding 1 mm over the watershed.
    """

    shape_exponent: float
    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]


@dataclass
class SnyderUHResult(JsonResultMixin):
    """
    Result of Snyder Unit Hydrograph generation.

    Attributes
    ----------
    times_min : NDArray[np.float64]
        Time values [min].
    ordinates_m3s : NDArray[np.float64]
        Unit hydrograph ordinates [m³/s per mm].
    area_km2 : float
        Watershed area [km²].
    length_km : float
        Length L of the main stream from the outlet to the divide [km].
    centroid_length_km : float
        Length Lc along the main stream to the point nearest the centroid [km].
    lag_time_min : float
        Basin lag time tL [min] (original, unadjusted).
    adjusted_lag_time_min : float
        Adjusted lag time tLR [min] of the rainfall duration.
    time_to_peak_min : float
        Time to peak tpR [min] of the rainfall duration (tp for tD).
    peak_discharge_m3s : float
        Largest ordinate [m³/s per mm]: qpR up to the sampling of the curve at the
        time step.
    time_base_min : float
        Time base tb [min] of the triangle with the peak qpR and the volume of
        1 mm (a Snyder parameter; the ordinates follow the recession of the
        curve beyond it).
    duration_min : float
        Rainfall duration D used for generation [min].
    standard_duration_min : float
        Standard rainfall duration tD = tL/5.5 [min].
    ct : float
        Time coefficient Ct.
    cp : float
        Peak coefficient Cp.
    """

    times_min: NDArray[np.float64]
    ordinates_m3s: NDArray[np.float64]
    area_km2: float
    length_km: float
    centroid_length_km: float
    lag_time_min: float
    adjusted_lag_time_min: float
    time_to_peak_min: float
    peak_discharge_m3s: float
    time_base_min: float
    duration_min: float
    standard_duration_min: float
    ct: float
    cp: float

    @property
    def n_steps(self) -> int:
        """Number of time steps."""
        return len(self.times_min)


# --- the parameters (spec snyder) -----------------------------------------------------


def _width_factor() -> float:
    """Return 1 ft³/s per mi² and in, in m³/s per km² and mm (exact, 1 / 2323.2)."""
    return (
        convert(1.0, "ft3_per_s", "m3_per_s")
        / convert(1.0, "mi", "km") ** 2
        / convert(1.0, "in", "mm")
    )


def _parameters(x: Values) -> dict[str, float]:
    """Return the outputs of the spec snyder for checked inputs, in its order.

    Raises
    ------
    ArithmeticError
        Where float64 cannot hold a step: the precondition representable.
    """
    area, cp = x.real("area_km2"), x.real("cp")
    lag = x.real("ct") * (x.real("length_km") * x.real("centroid_length_km")) ** (
        SNYDER.constant("lag_exponent")
    )
    standard = lag / SNYDER.constant("standard_ratio")
    duration = convert(x.real("duration_min"), "min", "h")
    adjusted = lag + SNYDER.constant("adjustment") * (duration - standard)
    peak = SNYDER.constant("peak_factor") * cp * area / lag
    adjusted_peak = SNYDER.constant("peak_factor") * cp * area / adjusted
    base = SNYDER.constant("base_factor") * area / adjusted_peak
    per_area = (adjusted_peak / area / _width_factor()) ** SNYDER.constant(
        "width_exponent"
    )
    return {
        "lag_time_min": convert(lag, "h", "min"),
        "standard_duration_min": convert(standard, "h", "min"),
        "adjusted_lag_time_min": convert(adjusted, "h", "min"),
        "time_to_peak_min": convert(adjusted + duration / 2.0, "h", "min"),
        "standard_peak_discharge_m3s": peak,
        "peak_discharge_m3s": adjusted_peak,
        "time_base_min": convert(base, "h", "min"),
        "width_50_min": convert(SNYDER.constant("width_50") / per_area, "h", "min"),
        "width_75_min": convert(SNYDER.constant("width_75") / per_area, "h", "min"),
    }


def _representable(x: Values) -> bool:
    """Return whether float64 holds every output as a normal number."""
    try:
        outputs = _parameters(x)
    except ArithmeticError:  # a power or a quotient beyond float64
        return False
    return all(math.isfinite(v) and v >= _SMALLEST for v in outputs.values())


def _standard_duration_min(
    length_km: object, centroid_length_km: object, ct: object
) -> float:
    """Return tD of the spec snyder, the default duration, or NaN for refused inputs.

    The spec checks its inputs before the duration, so a NaN of inputs it refuses
    never reaches the computation.
    """
    try:
        lag = float(cast(float, ct)) * math.pow(
            float(cast(float, length_km)) * float(cast(float, centroid_length_km)),
            SNYDER.constant("lag_exponent"),
        )
    except (TypeError, ValueError, ArithmeticError):
        return math.nan
    return convert(lag / SNYDER.constant("standard_ratio"), "h", "min")


def _triangle_volume(x: Values, out: Values) -> float:
    """Return the depth of the triangle of qpR and tb, less 1 mm."""
    seconds = convert(out.real("time_base_min"), "min", "s")
    volume_m3 = out.real("peak_discharge_m3s") * seconds / 2.0
    per_mm_m3 = convert(x.real("area_km2"), "km2", "m2") * convert(1.0, "mm", "m")
    return volume_m3 / per_mm_m3 - 1.0


def _standard_duration(run: Callable[..., Values]) -> None:
    for point in (
        {},
        {"length_km": 14.9, "centroid_length_km": 7.0, "ct": 1.65, "cp": 0.565},
    ):
        out = run(**point)
        tl, td = out.real("lag_time_min"), out.real("standard_duration_min")
        at = run(**point, duration_min=td)
        reason = (
            "D = tD gives tLR = tL, tpR = tL + tD / 2 and qpR = qp (KZGW 2017 eqs. 6.4 "
            "and 6.8 to 6.10): tD in h and back in min rounds by a unit in the last "
            "place"
        )
        assert_within(at.real("adjusted_lag_time_min"), tl, rel=1e-14, reason=reason)
        assert_within(
            at.real("time_to_peak_min"), tl + td / 2.0, rel=1e-14, reason=reason
        )
        assert_within(
            at.real("peak_discharge_m3s"),
            out.real("standard_peak_discharge_m3s"),
            rel=1e-14,
            reason=reason,
        )


def _decimal_parameters(inputs: dict[str, float]) -> dict[str, float]:
    """Return the outputs in decimal arithmetic of fifty digits, widths in feet."""
    with localcontext() as context:
        context.prec = 50
        area, cp = Decimal(inputs["area_km2"]), Decimal(inputs["cp"])
        lengths = Decimal(inputs["length_km"]) * Decimal(inputs["centroid_length_km"])
        lag = Decimal(inputs["ct"]) * lengths ** Decimal("0.3")
        standard = lag / Decimal("5.5")
        duration = Decimal(inputs["duration_min"]) / 60
        adjusted = lag + (duration - standard) / 4
        peak = Decimal("0.275") * cp * area / lag
        adjusted_peak = Decimal("0.275") * cp * area / adjusted
        foot = Decimal("0.3048")
        mile_km = 5280 * foot / 1000
        per_area = adjusted_peak / area * mile_km**2 * Decimal("25.4") / foot**3
        widths = per_area ** Decimal("-1.08")
        hours = {
            "lag_time_min": lag,
            "standard_duration_min": standard,
            "adjusted_lag_time_min": adjusted,
            "time_to_peak_min": adjusted + duration / 2,
            "time_base_min": Decimal("0.556") * area / adjusted_peak,
            "width_50_min": 770 * widths,
            "width_75_min": 440 * widths,
        }
        found = {name: float(value * 60) for name, value in hours.items()}
        found["standard_peak_discharge_m3s"] = float(peak)
        found["peak_discharge_m3s"] = float(adjusted_peak)
    return found


_DECIMAL_POINTS: Final = (
    # KZGW 2017 example 6.1, the Jasienica at the Międzyrzecze dam, D = 1 h
    {
        "area_km2": 45.3,
        "length_km": 14.9,
        "centroid_length_km": 7.0,
        "ct": 1.65,
        "cp": 0.565,
        "duration_min": 60.0,
    },
    # the catalog's first example, a 30 min rainfall
    {
        "area_km2": 100.0,
        "length_km": 15.0,
        "centroid_length_km": 8.0,
        "ct": 1.5,
        "cp": 0.6,
        "duration_min": 30.0,
    },
    # a small watershed of the hand-offs at a 5 min step
    {
        "area_km2": 0.35,
        "length_km": 0.9,
        "centroid_length_km": 0.4,
        "ct": 1.35,
        "cp": 0.8,
        "duration_min": 5.0,
    },
)
"""Inputs of the decimal oracle."""


def _decimal_oracle(run: Callable[..., Values]) -> None:
    for point in _DECIMAL_POINTS:
        out = run(**point)
        for name, expected in _decimal_parameters(point).items():
            assert_within(
                out.real(name),
                expected,
                rel=1e-13,
                reason="float64 against fifty decimal digits, the widths from "
                "Snyder's 770 and 440 in foot-pound units: a few units in the last "
                "place of each product, quotient and power",
            )


# --- the spec snyder ------------------------------------------------------------------

_LENGTH: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=2000.0,
    test_reason="twice the length of the Vistula (1,047 km), the longest river of "
    "Poland",
)
_LENGTH_TYPICAL: Final = Range(
    low=0.05,
    high=29.0,
    source=handoffs(
        "the longest flow paths of the 27 watersheds that have one, 0.057 to 28.9 km "
        "(flow_path_length_km): Snyder's L runs from the outlet to the divide, and Lc "
        "along it to the point nearest the centroid"
    ),
)
_KZGW_SNYDER: Final = "eqs. 6.4 to 6.11, pp. 90-92; example 6.1, pp. 92-95"

SNYDER: Final = FormulaSpec(
    name="snyder",
    title="Snyder's synthetic unit hydrograph: lag, peak, time base and widths",
    function="hydrolog.runoff.snyder_uh.snyder_parameters",
    family="empirical",
    equation=(
        "tL = Ct (L Lc)^0.3 [h, L and Lc in km, Ct in SI units]; tD = tL / 5.5; tLR = "
        "tL + (D - tD) / 4; tpR = tLR + D / 2; qp = 0.275 Cp A / tL, qpR = 0.275 Cp A "
        "/ tLR [m3/s per mm, A in km2, times in h]; tb = 0.556 A / qpR [h]; W50 = 770 "
        "(qpR / A)^-1.08 and W75 = 440 (qpR / A)^-1.08 [h, qpR / A in ft3/s per mi2 "
        "and in], 0.17829 and 0.10188 with qpR / A in m3/s per km2 and mm; times "
        "given in min"
    ),
    latex=(
        r"t_L = C_t\,(L\,L_c)^{0.3},\quad t_D = \frac{t_L}{5.5},\quad t_{LR} = t_L + "
        r"\frac{D - t_D}{4},\quad t_{pR} = t_{LR} + \frac{D}{2},\quad q_{pR} = "
        r"\frac{0.275\,C_p\,A}{t_{LR}},\quad t_b = \frac{0.556\,A}{q_{pR}},\quad "
        r"W_{50} = 770 \left(\frac{q_{pR}}{A}\right)^{-1.08}"
    ),
    variables=(
        Variable(
            name="area_km2",
            symbol="A",
            unit="km2",
            description="Area of the watershed.",
            physical=AREA,
            applicability=Range(
                low=30.0,
                high=30000.0,
                source=chow_notes(
                    "p. 76: Snyder's watersheds in the Appalachian Highlands, of 30 to "
                    "30,000 km2 (10 to 10,000 mi2)"
                ),
            ),
            typical=AREA_TYPICAL,
        ),
        Variable(
            name="length_km",
            symbol="L",
            unit="km",
            description="Length of the main stream from the outlet to the divide.",
            physical=_LENGTH,
            applicability="unstated",
            typical=_LENGTH_TYPICAL,
        ),
        Variable(
            name="centroid_length_km",
            symbol="L_c",
            unit="km",
            description="Length along the main stream from the outlet to the point "
            "nearest the centroid of the watershed.",
            physical=_LENGTH,
            applicability="unstated",
            typical=_LENGTH_TYPICAL,
        ),
        Variable(
            name="ct",
            symbol="C_t",
            unit="-",
            description="Time coefficient in SI units.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=60.0,
                test_reason="ten times the largest Ct HEC-HMS reports, 8.0 in "
                "foot-pound units (6.0 in SI) near the Gulf of Mexico",
            ),
            applicability=Range(
                low=1.35,
                high=1.65,
                source=kzgw(
                    "p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units, 0.75 times "
                    "Snyder's 1.8 to 2.2"
                ),
            ),
            typical=Range(
                low=1.35,
                high=1.65,
                source=kzgw("p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units"),
            ),
        ),
        Variable(
            name="cp",
            symbol="C_p",
            unit="-",
            description="Peak coefficient.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=8.0,
                test_reason="ten times the largest Cp of the sources, 0.8",
            ),
            applicability=Range(
                low=0.4,
                high=0.8,
                source=Source(
                    citation=f"{KZGW}; and {HEC_TRM_2000}",
                    locator="KZGW 2017, annex 2, p. 91, eq. 6.7: Cp from 0.4 to 0.8; "
                    "HEC-HMS 2000, Snyder's unit hydrograph model, p. 54: 0.4 to 0.8",
                    url="https://kzgw.gov.pl/files/zam-pub/"
                    "20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf",
                ),
            ),
            typical=Range(
                low=0.4,
                high=0.8,
                source=kzgw("p. 91, eq. 6.7: Cp from 0.4 to 0.8"),
            ),
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
    ),
    outputs=(
        Output(
            name="lag_time_min",
            unit="min",
            symbol="t_L",
            description="Basin lag, from the centre of the rainfall of tD to the peak.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="standard_duration_min",
            unit="min",
            symbol="t_D",
            description="Standard rainfall duration.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="adjusted_lag_time_min",
            unit="min",
            symbol="t_{LR}",
            description="Lag of the duration D.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="time_to_peak_min",
            unit="min",
            symbol="t_{pR}",
            description="Time to peak of the duration D from the beginning of the "
            "rainfall.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="standard_peak_discharge_m3s",
            unit="m3/s per mm",
            symbol="q_p",
            description="Peak of the standard duration.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="peak_discharge_m3s",
            unit="m3/s per mm",
            symbol="q_{pR}",
            description="Peak of the duration D.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="time_base_min",
            unit="min",
            symbol="t_b",
            description="Base of the triangle of the peak qpR that holds 1 mm.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="width_50_min",
            unit="min",
            symbol="W_{50}",
            description="Width of the unit hydrograph at 50 % of the peak qpR.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="width_75_min",
            unit="min",
            symbol="W_{75}",
            description="Width of the unit hydrograph at 75 % of the peak qpR.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(
        kzgw(_KZGW_SNYDER),
        hec_trm_2000("Snyder's unit hydrograph model, eqs. 30-32, pp. 54-55"),
        hec_trm_online(
            "snyder-unit-hydrograph-model",
            "Snyder Unit Hydrograph Model, eqs. 1 to 5: tp = C Ct (L Lc)^0.3, C = 0.75 "
            "in SI and 1.00 in foot-pound units",
        ),
        chow_notes("Snyder's synthetic unit hydrograph, pp. 76-78, eqs. 7.7.2-7.7.6"),
        INNOVYZE_SNYDER,
    ),
    constants=(
        Constant(
            name="lag_exponent",
            value=0.3,
            unit="-",
            symbol="0.3",
            source=kzgw(
                "eq. 6.5, p. 90: tL = Ct (L Lc)^0.3; HEC-HMS (online), Snyder Unit "
                "Hydrograph Model, eq. 5; Chow et al. 1988 after Rajagopalan's notes, "
                "eq. 7.7.2, p. 76"
            ),
        ),
        Constant(
            name="standard_ratio",
            value=5.5,
            unit="-",
            symbol="5.5",
            source=hec_trm_2000(
                "eq. 30: tp = 5.5 tr; KZGW 2017, annex 2, eq. 6.6, p. 91: tD = tL / 5.5"
            ),
        ),
        Constant(
            name="adjustment",
            value=0.25,
            unit="-",
            symbol="1/4",
            source=hec_trm_2000(
                "eq. 31: tpR = tp - (tr - tR) / 4; KZGW 2017, annex 2, eq. 6.8, p. 91: "
                "tLR = tL + 0.25 (D - tD)"
            ),
        ),
        Constant(
            name="peak_factor",
            value=0.275,
            unit="m3 s^-1 km^-2 mm^-1 h",
            symbol="0.275",
            source=kzgw(
                "eq. 6.7, p. 91: qp = 0.275 Cp A / tL in m3/s per mm; HEC-HMS 2000, "
                "eq. 32, and Chow et al. 1988 after Rajagopalan's notes, eq. 7.7.3, "
                "p. 77: C2 = 2.75 per cm"
            ),
        ),
        Constant(
            name="base_factor",
            value=0.556,
            unit="h m3 s^-1 km^-2 mm^-1",
            symbol="0.556",
            source=kzgw(
                "eq. 6.11, p. 92: tb = 0.556 A / qpR; Chow et al. 1988 after "
                "Rajagopalan's notes, p. 78: C3 = 5.56 per cm"
            ),
        ),
        Constant(
            name="width_50",
            value=770.0,
            unit="h (ft3 s^-1 mi^-2 in^-1)^1.08",
            symbol="770",
            source=chow_notes(
                "p. 78: W = Cw qpR^-1.08 with Cw = 770 at 50 % of the peak in English "
                "units (2.14 in SI per cm); Innovyze, Snyder Unit Hydrograph Method: "
                "C50 = 770"
            ),
        ),
        Constant(
            name="width_75",
            value=440.0,
            unit="h (ft3 s^-1 mi^-2 in^-1)^1.08",
            symbol="440",
            source=chow_notes(
                "p. 78: Cw = 440 at 75 % of the peak in English units (1.22 in SI per "
                "cm); Innovyze, Snyder Unit Hydrograph Method: C75 = 440"
            ),
        ),
        Constant(
            name="width_exponent",
            value=1.08,
            unit="-",
            symbol="1.08",
            source=chow_notes("p. 78: W = Cw qpR^-1.08, qpR per unit area"),
        ),
    ),
    constraints=(
        Constraint(
            name="representable",
            cls="precondition",
            check=_representable,
            text="float64 holds the lag, the peaks, the time base and the widths as "
            "normal numbers",
            source=Source(
                citation="IEEE 754 double precision (float64)",
                locator="normal numbers from 2.2e-308 to 1.8e308",
            ),
            satisfied={"area_km2": 45.3},
            violated={"area_km2": 1.0e-310},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"length_km": 1, "centroid_length_km": 1, "ct": 1},
        conservation=(
            Conservation(
                name="triangle_volume",
                text="the triangle of the peak qpR and the base tb holds 1 mm over the "
                "watershed, qpR tb / 2 = A x 1 mm, within the rounding of 0.556",
                residual=_triangle_volume,
                tolerance=Tolerance(
                    abs=1e-3,
                    reason="0.556 rounds 2 x 1000 / 3600 = 0.5556 (KZGW 2017 eq. "
                    "6.11): the triangle holds 0.556 x 1.8 = 1.0008 mm",
                ),
            ),
        ),
        limits=(
            Limit(
                name="standard_duration",
                text="the rainfall of the standard duration D = tD keeps the lag tL "
                "and the peak qp, with tpR = tL + tD / 2 (KZGW 2017 eqs. 6.4 and 6.8 "
                "to 6.10)",
                check=_standard_duration,
                source=kzgw("eqs. 6.4 and 6.8 to 6.10, pp. 90-91"),
            ),
            Limit(
                name="decimal_oracle",
                text="every output equals the equations in decimal arithmetic of "
                "fifty digits, the widths from 770 and 440 in foot-pound units",
                check=_decimal_oracle,
            ),
        ),
    ),
    validation=(
        "Snyder (1938) derived the relations from watersheds of the Appalachian "
        "Highlands of 10 to 10,000 square miles (Chow et al. 1988 after Rajagopalan's "
        "notes, p. 76); Ct and Cp are regional and best found by calibration "
        "(HEC-HMS); the sources give no error statistic"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "SI units: A in km2, L and Lc in km; Ct in SI units holds Snyder's 0.75 "
            "(HEC-HMS: tp = C Ct (L Lc)^0.3, C = 0.75 in SI), so that its 1.35 to 1.65 "
            "is 0.75 times Snyder's 1.8 to 2.2 (KZGW 2017 p. 90)"
        ),
        (
            "peaks in m3/s per mm of runoff: 0.275 and 0.556 per mm are Chow's 2.75 "
            "and 5.56 per cm (KZGW 2017 eqs. 6.7 and 6.11)"
        ),
        (
            "times from the beginning of the unit rainfall, given in min: the lag tL "
            "is Snyder's tp of HEC-HMS and Chow, the time to peak is KZGW's tp = tL + "
            "tD / 2 for D = tD and tpR = tLR + D / 2 for another D"
        ),
        (
            "tb is the base of the triangle of the peak qpR that holds 1 mm (KZGW 2017 "
            "eq. 6.11, Chow's C3 / qpR), not the end of the curve of snyder_shape"
        ),
        (
            "the widths are those of Chow et al. (1988), from qpR per unit area, with "
            "Snyder's 770 and 440 converted exactly from ft3/s per mi2 and in (1 / "
            "2323.2 m3/s per km2 and mm, the units table): 0.17829 and 0.10188; "
            "Chow's SI 2.14 and 1.22 per cm round them (0.17800 and 0.10148 per mm, "
            "0.2 % and 0.4 % lower)"
        ),
        (
            "L is the length of the main stream from the outlet to the divide, Lc the "
            "length along it to the point nearest the centroid (KZGW 2017 p. 90)"
        ),
    ),
    assumptions=(
        (
            "the coefficients Ct and Cp are those of the region, best calibrated on "
            "gauged watersheds of it (HEC-HMS); KZGW 2017 gives 1.35 to 1.65 and 0.4 "
            "to 0.8"
        ),
        (
            "most watersheds of the ecosystem (the hand-offs' areas up to 250 km2) are "
            "smaller than Snyder's, 30 to 30,000 km2: they get the notice "
            "outside_applicability of snyder.area_km2"
        ),
    ),
    traps={
        "singular_at_bound": "the powers (L Lc)^0.3 and (qpR / A)^-1.08 at the bounds "
        "0 of the inputs: range cases *-physical_low_inside, refused by the "
        "precondition representable where an output leaves the normal numbers",
    },
    reference_cases=("tests/fixtures/formulas/unit-hydrographs-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="every output in decimal arithmetic of fifty digits, the "
            "widths from Snyder's 770 and 440 in foot-pound units and the exact "
            "conversion of ft3/s per mi2 and in",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit decimal_oracle)",
        ),
    ),
    base={
        "area_km2": 45.3,
        "length_km": 14.9,
        "centroid_length_km": 7.0,
        "ct": 1.65,
        "cp": 0.565,
        "duration_min": 60.0,
    },
)


def snyder_parameters(
    area_km2: float,
    length_km: float,
    centroid_length_km: float,
    ct: float,
    cp: float,
    duration_min: float,
) -> SnyderParameters:
    """Return the parameters of Snyder's unit hydrograph for a duration, spec snyder.

    The first input is the area of the watershed in square kilometres (its name
    carries the unit, so the standard's check of this docstring, which allows no
    digit, keeps it out of the list below).

    Parameters
    ----------
    length_km : float
        Length of the main stream from the outlet to the divide [km].
    centroid_length_km : float
        Length along the main stream to the point nearest the centroid [km].
    ct : float
        Time coefficient in SI units.
    cp : float
        Peak coefficient.
    duration_min : float
        Duration of the unit of excess rainfall [min].

    Returns
    -------
    SnyderParameters
        The lag, the standard duration, the lag, time to peak and peak of the
        duration, the peak of the standard duration, the time base and the widths.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, or outputs a double cannot hold (precondition
        ``representable``).

    Warns
    -----
    OutsideApplicability
        For the area, ``ct`` or ``cp`` outside the range of the method.
    """
    x = checked_inputs(
        SNYDER,
        area_km2=area_km2,
        length_km=length_km,
        centroid_length_km=centroid_length_km,
        ct=ct,
        cp=cp,
        duration_min=duration_min,
    )
    out = checked_outputs(SNYDER, _parameters(x))
    return SnyderParameters(**{o.name: out.real(o.name) for o in SNYDER.outputs})


# --- the curve (spec snyder_shape) ----------------------------------------------------


def _volume_log(exponent: float) -> float:
    """Return ln(Γ(K) (e / K)^K), the volume of the curve over qpR tpR."""
    return float(gammaln(exponent)) + exponent * (1.0 - math.log(exponent))


def _target(area_km2: float, time_to_peak_min: float, peak_m3s: float) -> float:
    """Return -ln(qpR tpR / (A x 1 mm)), the value of the volume's logarithm for K.

    One quotient, so that scaling the area and the peak, or the times and the peak,
    by a power of two leaves it, and K, unchanged to the last bit.

    Raises
    ------
    ArithmeticError, ValueError
        Where float64 cannot hold the quotient: far outside the bracket of K.
    """
    volume_m3 = convert(area_km2, "km2", "m2") * convert(1.0, "mm", "m")
    seconds = convert(time_to_peak_min, "min", "s")
    return math.log(volume_m3 / (peak_m3s * seconds))


def _bracketed(area_km2: float, time_to_peak_min: float, peak_m3s: float) -> bool:
    """Return whether the root K of the volume lies in the bracket of its search."""
    try:
        target = _target(area_km2, time_to_peak_min, peak_m3s)
    except (ArithmeticError, ValueError):  # a quotient float64 cannot hold
        return False
    lowest, highest = _EXPONENTS
    return _volume_log(highest) <= target <= _volume_log(lowest)


def _exponent(area_km2: float, time_to_peak_min: float, peak_m3s: float) -> float:
    """Return the exponent K of the curve that holds 1 mm, of bracketed inputs.

    The logarithm of Γ(K) (e / K)^K falls from +∞ to -∞ as K grows (its derivative
    is ψ(K) - ln K < 0), so a bracketed volume has one root; Brent's method finds it
    in ln K.
    """
    target = _target(area_km2, time_to_peak_min, peak_m3s)
    lowest, highest = (math.log(e) for e in _EXPONENTS)
    found = brentq(
        lambda log_k: _volume_log(math.exp(log_k)) - target,
        lowest,
        highest,
        xtol=1e-12,
    )
    return math.exp(float(found))


def _root_bracketed(x: Values) -> bool:
    """Return whether the precondition root_bracketed holds."""
    return _bracketed(
        x.real("area_km2"), x.real("time_to_peak_min"), x.real("peak_discharge_m3s")
    )


def _count(x: Values) -> int | None:
    """Return the number of ordinates, or None where float64 cannot hold the grid."""
    step, total = x.real("timestep_min"), x.real("total_duration_min")
    try:
        count = max(math.ceil(total / step), 1) + 1
    except OverflowError:  # a quotient of inf
        return None
    seconds = convert(step, "min", "s")
    volume = convert(x.real("area_km2"), "km2", "m2") * convert(1.0, "mm", "m")
    extent = (total + step) / x.real("time_to_peak_min")
    if count > MAX_ORDINATES or not math.isfinite(extent):
        return None
    if not (seconds >= _SMALLEST and _SMALLEST <= volume / seconds < math.inf):
        return None
    return count


def _grid_representable(x: Values) -> bool:
    """Return whether the precondition grid_representable holds."""
    return _count(x) is not None


def _shape(x: Values) -> dict[str, object]:
    """Return the outputs of the spec snyder_shape for checked inputs.

    The curve is evaluated as exp(K (ln x + 1 - x)), x = t / tpR, less its largest
    value on the grid: the rescaling to 1 mm removes the factor, which keeps a peak
    narrower than the step from vanishing in underflow.
    """
    area, step = x.real("area_km2"), x.real("timestep_min")
    tp, peak = x.real("time_to_peak_min"), x.real("peak_discharge_m3s")
    exponent = _exponent(area, tp, peak)
    times = np.arange(cast(int, _count(x)), dtype=np.float64) * step
    ratio = times[1:] / tp
    log_shape = exponent * (np.log(ratio) + 1.0 - ratio)
    weights = np.zeros_like(times)
    weights[1:] = np.exp(log_shape - log_shape.max())
    volume_m3 = convert(area, "km2", "m2") * convert(1.0, "mm", "m")
    scale = volume_m3 / (convert(step, "min", "s") * math.fsum(weights))
    return {
        "shape_exponent": exponent,
        "times_min": times,
        "ordinates_m3s": weights * scale,
    }


def _shape_volume(x: Values, out: Values) -> float:
    """Return the depth the ordinates hold over the watershed, less 1 mm."""
    seconds = convert(x.real("timestep_min"), "min", "s")
    volume_m3 = math.fsum(out.array("ordinates_m3s")) * seconds
    per_mm_m3 = convert(x.real("area_km2"), "km2", "m2") * convert(1.0, "mm", "m")
    return volume_m3 / per_mm_m3 - 1.0


_KZGW_SHAPE: Final = {
    "area_km2": 45.3,
    "time_to_peak_min": 425.99309176111075,
    "peak_discharge_m3s": 1.0664561043776108,
    "timestep_min": 60.0,
    "total_duration_min": 2640.0,
}
"""The peak of KZGW 2017 example 6.1 by the spec snyder, its curve on hours."""


def _volume_identity(run: Callable[..., Values]) -> None:
    for point in ({}, _KZGW_SHAPE, {"peak_discharge_m3s": 0.1}):
        out = run(**point)
        exponent = out.real("shape_exponent")
        inputs = {**SNYDER_SHAPE.base_point(), **point}
        seconds = convert(cast(float, inputs["time_to_peak_min"]), "min", "s")
        volume = (
            cast(float, inputs["peak_discharge_m3s"])
            * seconds
            * math.gamma(exponent)
            * (math.e / exponent) ** exponent
        )
        assert_within(
            volume,
            convert(cast(float, inputs["area_km2"]), "km2", "m2") / 1000.0,
            rel=1e-9,
            reason="Asquith and Roussel (2007) eq. 4 in math.gamma and a power, not "
            "the logarithms of the code: K is found to 1e-12 in ln K",
        )


def _gamma_density(run: Callable[..., Values]) -> None:
    for point in ({}, _KZGW_SHAPE, {"timestep_min": 5.0}):
        out = run(**point)
        exponent = out.real("shape_exponent")
        inputs = {**SNYDER_SHAPE.base_point(), **point}
        tp = cast(float, inputs["time_to_peak_min"])
        times, ordinates = out.array("times_min"), out.array("ordinates_m3s")
        density = gamma(a=exponent + 1.0, scale=tp / exponent).pdf(times)
        assert_within(
            ordinates / ordinates.max(),
            density / density.max(),
            rel=1e-9,
            abs=1e-14,
            reason="the curve in t / tpR is x^K exp(-K x) times a constant, SciPy's "
            "gamma density of the shape K + 1 and the scale tpR / K: both in float64, "
            "the density through its own logarithms",
        )


def _peak_at_its_time(run: Callable[..., Values]) -> None:
    out = run(time_to_peak_min=420.0, timestep_min=30.0)
    ordinates = out.array("ordinates_m3s")
    assert out.array("times_min")[int(np.argmax(ordinates))] == 420.0


_SHAPE_TYPICAL: Final = (
    "the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, "
    "L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 "
    "to 60 min give"
)


def _shape_source(what: str) -> Source:
    return Source(
        citation="Hydrolog: the spec snyder over the typical ranges of its inputs",
        locator=f"{_SHAPE_TYPICAL} {what}",
    )


SNYDER_SHAPE: Final = FormulaSpec(
    name="snyder_shape",
    title="Snyder's unit hydrograph as the gamma curve of 1 mm through its peak",
    function="hydrolog.runoff.snyder_uh.snyder_shape",
    family="scheme",
    equation=(
        "q(t) = qpR [(t / tpR) exp(1 - t / tpR)]^K with K > 0 the root of qpR tpR "
        "Gamma(K) (e / K)^K = A x 1 mm, the curve that holds 1 mm over A; the "
        "ordinates are q(k dt) for k = 0 to max(1, ceil(T / dt)), rescaled so that the "
        "sum of q_k dt is A x 1 mm"
    ),
    latex=(
        r"q(t) = q_{pR}\left[\frac{t}{t_{pR}}\,e^{1 - t/t_{pR}}\right]^K,\quad "
        r"q_{pR}\,t_{pR}\,\Gamma(K)\left(\frac{e}{K}\right)^K = A \cdot "
        r"1\,\mathrm{mm},\quad \sum_k q_k\,\Delta t = A \cdot 1\,\mathrm{mm}"
    ),
    variables=(
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
            name="time_to_peak_min",
            symbol="t_{pR}",
            unit="min",
            description="Time to peak from the beginning of the rainfall (the spec "
            "snyder).",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=7600.0,
                test_reason="ten times the longest of the typical range",
            ),
            applicability="unstated",
            typical=Range(
                low=16.0, high=760.0, source=_shape_source("tpR of 16.6 to 758 min")
            ),
        ),
        Variable(
            name="peak_discharge_m3s",
            symbol="q_{pR}",
            unit="m3/s per mm",
            description="Peak of the unit hydrograph (the spec snyder).",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=2350.0,
                test_reason="ten times the largest of the typical range",
            ),
            applicability="unstated",
            typical=Range(
                low=2.7e-6,
                high=235.0,
                source=_shape_source("qpR of 2.7e-6 to 235 m3/s per mm"),
            ),
        ),
        Variable(
            name="timestep_min",
            symbol=r"\Delta t",
            unit="min",
            description="Time step of the ordinates.",
            physical=TIMESTEP,
            applicability="unstated",
            typical=TIMESTEP_TYPICAL,
        ),
        Variable(
            name="total_duration_min",
            symbol="T",
            unit="min",
            description="Length of the hydrograph: the curve beyond it is cut off.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=76000.0,
                test_reason="ten times the longest of the typical range",
            ),
            applicability="unstated",
            typical=Range(
                low=60.0,
                high=7610.0,
                source=_shape_source(
                    "the ends of the curves at 99.99 % of their volume, the default "
                    "of SnyderUH, of 61 to 7,605 min (K of 1.14 to 17.2)"
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="shape_exponent",
            unit="-",
            symbol="K",
            description="Exponent of the curve.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="times_min",
            unit="min",
            kind="real_array",
            symbol="k \\Delta t",
            description="Times of the ordinates, from the beginning of the rainfall.",
            physical=Range(low=0.0),
        ),
        Output(
            name="ordinates_m3s",
            unit="m3/s per mm",
            kind="real_array",
            symbol="q_k",
            description="Ordinates of the unit hydrograph.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        Source(
            citation="Asquith, W.H. and Roussel, M.C. (2007). An initial-abstraction, "
            "constant-loss model for unit hydrograph modeling for applicable "
            "watersheds in Texas. U.S. Geological Survey Scientific Investigations "
            "Report 2007-5243",
            locator="eq. 2, the gamma unit hydrograph through its peak, and eq. 4, "
            "its volume qp tp Gamma(K) (e / K)^K",
            url="https://pubs.usgs.gov/sir/2007/5243/",
        ),
        kzgw(
            "fig. 6.1, p. 90: the unit hydrograph through (tpR, qpR), its shape not "
            "prescribed"
        ),
    ),
    constraints=(
        Constraint(
            name="root_bracketed",
            cls="precondition",
            check=_root_bracketed,
            text="the exponent K of the curve of 1 mm lies between 1e-12 and 1e12: "
            "qpR tpR / (A x 1 mm) between about 1e-12 and 4e5",
            source=Source(
                citation="Hydrolog's bracket of the root of the volume of the curve",
                locator="Brent's method on ln K from 1e-12 to 1e12",
            ),
            satisfied={"peak_discharge_m3s": 1.0664561043776108},
            violated={"peak_discharge_m3s": 1.0e-12},
        ),
        Constraint(
            name="grid_representable",
            cls="precondition",
            check=_grid_representable,
            text="the grid has at most a million ordinates, and float64 holds (T + "
            "dt) / tpR and, as a normal number, the ordinate of 1 mm on one step, A x "
            "1 mm / dt",
            source=ORDINATES_SOURCE,
            satisfied={"timestep_min": 60.0},
            violated={"timestep_min": 1.0e-3},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="time",
                inputs={
                    "time_to_peak_min": 1,
                    "peak_discharge_m3s": -1,
                    "timestep_min": 1,
                    "total_duration_min": 1,
                },
                outputs={"times_min": 1, "ordinates_m3s": -1},
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling every time and halving the peak keeps qpR tpR, "
                    "K and the grid in units of tpR exactly in binary, but for "
                    "subnormal ordinates",
                ),
            ),
            Scaling(
                name="area",
                inputs={"area_km2": 1, "peak_discharge_m3s": 1},
                outputs={"ordinates_m3s": 1},
                tolerance=Tolerance(
                    rel=1e-14,
                    abs=1e-300,
                    reason="doubling the area and the peak keeps K and doubles every "
                    "ordinate exactly in binary, but for subnormal ordinates",
                ),
            ),
        ),
        conservation=(
            Conservation(
                name="unit_volume",
                text="the ordinates hold 1 mm over the watershed, sum(q_k) dt = A x 1 "
                "mm",
                residual=_shape_volume,
                tolerance=Tolerance(
                    abs=1e-12,
                    reason="the ordinates are rescaled to 1 mm by a sum of math.fsum; "
                    "the products round by a few units in the last place",
                ),
            ),
        ),
        limits=(
            Limit(
                name="volume_identity",
                text="K solves qpR tpR Gamma(K) (e / K)^K = A x 1 mm (Asquith and "
                "Roussel 2007 eq. 4)",
                check=_volume_identity,
            ),
            Limit(
                name="gamma_density",
                text="the ordinates are proportional to SciPy's gamma density of the "
                "shape K + 1 and the scale tpR / K",
                check=_gamma_density,
            ),
            Limit(
                name="peak_at_its_time",
                text="a step that divides tpR puts the largest ordinate at tpR",
                check=_peak_at_its_time,
            ),
        ),
    ),
    validation=(
        "none: Snyder's method gives the peak, the widths and the time base, not a "
        "curve (KZGW 2017 fig. 6.1; HEC-HMS fits a Clark unit hydrograph instead); "
        "Asquith and Roussel (2007) give the curve and its volume"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        "times from the beginning of the rainfall, in min; ordinates in m3/s per mm",
        (
            "the ordinates are the curve at the step times, rescaled to hold exactly 1 "
            "mm: the sampling and the part beyond T would change the volume"
        ),
        (
            "SnyderUH takes tpR and qpR of the spec snyder for the duration, and T, "
            "unless given, at 99.99 % of the curve's volume, T = tpR P^-1(K + 1, "
            "0.9999) / K with P the regularized lower incomplete gamma function"
        ),
    ),
    assumptions=(
        (
            "the shape of the unit hydrograph between its points of Snyder's method is "
            "the gamma curve; KZGW 2017 example 6.1 draws straight lines (its table "
            "6.1, a peak 6.9 % lower)"
        ),
    ),
    traps={
        "unbounded_iteration": "Brent's method on ln K in a bracket with at most a "
        "hundred iterations; outside it the precondition root_bracketed refuses: "
        "test_snyder_shape_refuses_an_exponent_outside_its_bracket",
        "many_small_terms": "the volume of up to a million ordinates by math.fsum: "
        "test_snyder_shape_a_million_ordinates_hold_their_volume",
    },
    reference_cases=("tests/fixtures/formulas/unit-hydrographs-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the volume of the curve, qpR tpR Gamma(K) (e / K)^K = A x 1 "
            "mm (Asquith and Roussel 2007 eq. 4), in math.gamma and a power",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit volume_identity)",
        ),
        Oracle(
            kind="established",
            description="SciPy's gamma distribution (scipy.stats.gamma, SciPy of "
            "Nogat's release set): its density of the shape K + 1 and the scale tpR / "
            "K is proportional to the curve",
            test="tests/unit/test_formulas_unit_hydrographs.py (limit gamma_density)",
            conventions=(
                "Hydrolog: x^K exp(K (1 - x)) with x = t / tpR",
                (
                    "SciPy: t^a-1 exp(-t / scale) / (Gamma(a) scale^a) with a = K + 1 "
                    "and scale = tpR / K"
                ),
            ),
        ),
    ),
    base=_KZGW_SHAPE,
)


def snyder_shape(
    area_km2: float,
    time_to_peak_min: float,
    peak_discharge_m3s: float,
    timestep_min: float,
    total_duration_min: float,
) -> SnyderShape:
    """Return the curve of Snyder's unit hydrograph on the time step, spec snyder_shape.

    The first input is the area of the watershed in square kilometres and the third
    the peak of the spec ``snyder`` in cubic metres per second and millimetre (their
    names carry the units, so the standard's check of this docstring, which allows
    no digit, keeps them out of the list below).

    Parameters
    ----------
    time_to_peak_min : float
        Time to peak from the beginning of the rainfall [min].
    timestep_min : float
        Time step of the ordinates [min].
    total_duration_min : float
        Length of the hydrograph [min].

    Returns
    -------
    SnyderShape
        The exponent of the curve, the times and the ordinates.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a peak no curve of one millimetre has (precondition
        ``root_bracketed``) or a grid a double cannot hold (precondition
        ``grid_representable``).
    """
    x = checked_inputs(
        SNYDER_SHAPE,
        area_km2=area_km2,
        time_to_peak_min=time_to_peak_min,
        peak_discharge_m3s=peak_discharge_m3s,
        timestep_min=timestep_min,
        total_duration_min=total_duration_min,
    )
    out = checked_outputs(SNYDER_SHAPE, _shape(x))
    return SnyderShape(
        shape_exponent=out.real("shape_exponent"),
        times_min=out.array("times_min"),
        ordinates_m3s=out.array("ordinates_m3s"),
    )


SPECS: Final = (SNYDER, SNYDER_SHAPE)
"""The Tier A formulas of the module."""


# --- the interface of earlier versions ------------------------------------------------


class SnyderUH:
    """
    Snyder Synthetic Unit Hydrograph (specs ``snyder`` and ``snyder_shape``).

    Keeps the watershed and the coefficients and computes with
    :func:`snyder_parameters` and :func:`snyder_shape` when a method is called, so
    that the specs check every input then (the constructor checks nothing): a
    refusal is an :class:`~hydrolog.exceptions.InvalidParameterError` with the
    standard's ``details.reason``, and a value outside the method's range warns
    with :class:`~hydrolog._warnings.OutsideApplicability` at each call.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    L_km : float
        Length of the main stream from the outlet to the divide [km].
    Lc_km : float
        Length along the main stream from the outlet to the point nearest the
        centroid of the watershed [km].
    ct : float, optional
        Time coefficient in SI units, by default 1.5.
    cp : float, optional
        Peak coefficient, by default 0.6.

    Notes
    -----
    ``docs/FORMULAS.md`` gives the equations, constants, ranges and sources of the
    specs. A method that takes a rainfall duration computes for the standard
    duration tD when it is not given; :meth:`generate` samples the curve of
    ``snyder_shape`` through the peak (tpR, qpR) of the duration at the time step,
    by default until 99.99 % of its volume has run off.

    Examples
    --------
    >>> uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
    >>> result = uh.generate(timestep_min=30.0)
    >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
    Peak: 2.62 m³/s per mm
    """

    def __init__(
        self,
        area_km2: float,
        L_km: float,
        Lc_km: float,
        ct: float = 1.5,
        cp: float = 0.6,
    ) -> None:
        """
        Keep the watershed and the coefficients of Snyder's unit hydrograph.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        L_km : float
            Length of the main stream [km].
        Lc_km : float
            Length to the point nearest the centroid [km].
        ct : float, optional
            Time coefficient (SI), by default 1.5.
        cp : float, optional
            Peak coefficient, by default 0.6.
        """
        self.area_km2 = area_km2
        self.L_km = L_km
        self.Lc_km = Lc_km
        self.ct = ct
        self.cp = cp

    def parameters(self, duration_min: float | None = None) -> SnyderParameters:
        """
        Return the parameters of the spec ``snyder`` for a rainfall duration.

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration D [min]; by default the standard duration tD.

        Returns
        -------
        SnyderParameters
            tL, tD, tLR, tpR, qp, qpR, tb, W50 and W75.

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``).
        """
        duration = (
            _standard_duration_min(self.L_km, self.Lc_km, self.ct)
            if duration_min is None
            else duration_min
        )
        return snyder_parameters(
            self.area_km2, self.L_km, self.Lc_km, self.ct, self.cp, duration
        )

    @property
    def lag_time_hours(self) -> float:
        """Basin lag time tL [hours]."""
        return convert(self.parameters().lag_time_min, "min", "h")

    @property
    def lag_time_min(self) -> float:
        """Basin lag time tL [min]."""
        return self.parameters().lag_time_min

    @property
    def standard_duration_hours(self) -> float:
        """Standard rainfall duration tD [hours], for which tp and qp apply."""
        return convert(self.parameters().standard_duration_min, "min", "h")

    @property
    def standard_duration_min(self) -> float:
        """Standard rainfall duration tD [min]."""
        return self.parameters().standard_duration_min

    def time_to_peak_hours(self, duration_hours: float | None = None) -> float:
        """
        Calculate time to peak [hours].

        Parameters
        ----------
        duration_hours : float, optional
            Rainfall duration D [hours]; by default the standard duration tD.

        Returns
        -------
        float
            Time to peak tp, or tpR of another duration [hours].
        """
        minutes = (
            None if duration_hours is None else convert(duration_hours, "h", "min")
        )
        return convert(self.parameters(minutes).time_to_peak_min, "min", "h")

    def time_to_peak_min(self, duration_min: float | None = None) -> float:
        """
        Calculate time to peak [min].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration D [min]; by default the standard duration tD.

        Returns
        -------
        float
            Time to peak tp, or tpR of another duration [min].
        """
        return self.parameters(duration_min).time_to_peak_min

    def adjusted_lag_time_hours(self, duration_hours: float | None = None) -> float:
        """
        Calculate adjusted lag time tLR [hours].

        Parameters
        ----------
        duration_hours : float, optional
            Rainfall duration D [hours]; by default the standard duration tD, for
            which tLR is tL.

        Returns
        -------
        float
            Adjusted lag time tLR [hours].
        """
        minutes = (
            None if duration_hours is None else convert(duration_hours, "h", "min")
        )
        return convert(self.parameters(minutes).adjusted_lag_time_min, "min", "h")

    def peak_discharge(self, duration_min: float | None = None) -> float:
        """
        Calculate peak discharge [m³/s per mm].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration D [min]; by default the standard duration tD.

        Returns
        -------
        float
            Peak qp, or qpR of another duration [m³/s per mm].
        """
        return self.parameters(duration_min).peak_discharge_m3s

    def time_base_hours(self, duration_min: float | None = None) -> float:
        """
        Calculate time base tb [hours].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration D [min]; by default the standard duration tD.

        Returns
        -------
        float
            Time base tb of the triangle of the peak that holds 1 mm [hours]: a
            parameter of the method, not the end of the hydrograph of
            :meth:`generate`, which follows the recession of its curve.
        """
        return convert(self.parameters(duration_min).time_base_min, "min", "h")

    def time_base_min(self, duration_min: float | None = None) -> float:
        """
        Calculate time base tb [min].

        Parameters
        ----------
        duration_min : float, optional
            Rainfall duration D [min]; by default the standard duration tD.

        Returns
        -------
        float
            Time base tb [min].
        """
        return self.parameters(duration_min).time_base_min

    def width_at_percent(self, percent: float) -> float:
        """
        Calculate the hydrograph width at 50 % or 75 % of the peak [hours].

        Parameters
        ----------
        percent : float
            Percentage of the peak discharge: 50 or 75, the two widths that
            Snyder's method defines.

        Returns
        -------
        float
            Width W50 or W75 of the unit hydrograph of the standard duration
            [hours].

        Raises
        ------
        InvalidParameterError
            If ``percent`` is neither 50 nor 75 (``details``: ``option="percent"``,
            ``reason="choice"``, ``allowed=[50, 75]``, ``value``), or the spec
            refuses an input.

        Notes
        -----
        Snyder's method (Chow, Maidment and Mays 1988, sec. 7.7) gives no width
        at any other percentage of the peak, and none is extrapolated from these
        two.
        """
        output = _WIDTHS.get(percent)
        if output is None:
            raise InvalidParameterError(
                f"percent must be 50 or 75 (Snyder's widths W50 and W75), "
                f"got {percent}",
                details={
                    "option": "percent",
                    "reason": "choice",
                    "allowed": [50, 75],
                    "value": str(percent),
                },
                hint="Snyder's method defines the widths at 50 % and 75 % of the "
                "peak only.",
            )
        width = cast(float, getattr(self.parameters(), output))
        return convert(width, "min", "h")

    def generate(
        self,
        timestep_min: float = 30.0,
        duration_min: float | None = None,
        total_duration_min: float | None = None,
    ) -> SnyderUHResult:
        """
        Generate Snyder Unit Hydrograph.

        Parameters
        ----------
        timestep_min : float, optional
            Time step for discretization [min], by default 30.0.
        duration_min : float, optional
            Rainfall duration D [min]. If not specified, uses the standard
            duration tD.
        total_duration_min : float, optional
            Total duration of output UH [min]. If not specified, the
            hydrograph runs to the end of its recession, when 99.99 % of its
            volume has passed. A shorter duration cuts the recession off.

        Returns
        -------
        SnyderUHResult
            Generated unit hydrograph with times and ordinates.

        Raises
        ------
        InvalidParameterError
            If a spec refuses an input (``details.reason``), or no unit hydrograph
            of 1 mm has the peak qpR at tpR (precondition ``root_bracketed`` of
            ``snyder_shape``, ``details.option`` ``peak_discharge_m3s``).

        Examples
        --------
        >>> uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        >>> result = uh.generate(timestep_min=30.0)
        >>> print(f"Peak: {result.peak_discharge_m3s:.2f} m³/s per mm")
        Peak: 2.62 m³/s per mm
        """
        found = self.parameters(duration_min)
        tp, qp = found.time_to_peak_min, found.peak_discharge_m3s
        if total_duration_min is None:
            # In x = t / tpR the curve is proportional to x^K exp(-K x), the density
            # of the gamma distribution of the shape K + 1 and the rate K: the share
            # of the volume before x is P(K + 1, K x)
            total_duration_min = tp
            if _bracketed(self.area_km2, tp, qp):
                exponent = _exponent(self.area_km2, tp, qp)
                quantile = gammaincinv(exponent + 1.0, 1.0 - _TAIL_VOLUME)
                total_duration_min = tp * float(quantile) / exponent
        shape = snyder_shape(self.area_km2, tp, qp, timestep_min, total_duration_min)
        duration = found.standard_duration_min if duration_min is None else duration_min
        return SnyderUHResult(
            times_min=shape.times_min,
            ordinates_m3s=shape.ordinates_m3s,
            area_km2=self.area_km2,
            length_km=self.L_km,
            centroid_length_km=self.Lc_km,
            lag_time_min=found.lag_time_min,
            adjusted_lag_time_min=found.adjusted_lag_time_min,
            time_to_peak_min=tp,
            peak_discharge_m3s=float(np.max(shape.ordinates_m3s)),
            time_base_min=found.time_base_min,
            duration_min=duration,
            standard_duration_min=found.standard_duration_min,
            ct=self.ct,
            cp=self.cp,
        )
