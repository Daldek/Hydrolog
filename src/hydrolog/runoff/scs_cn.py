"""SCS Curve Number method: retention, direct runoff and antecedent runoff condition.

The formulas are declared by their specs (Nogat's computation standard, ADR-0050):
:data:`RETENTION` (``scs_cn_retention``), :data:`RUNOFF` (``scs_cn_runoff``) and
:data:`AMC_CONVERSION` (``scs_cn_amc``); ``docs/FORMULAS.md`` shows their equations,
constants, ranges and sources. :class:`SCSCN` keeps the interface of earlier versions
and computes through them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Conservation,
    Constant,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)

__all__ = [
    "AMC",
    "AMC_CONVERSION",
    "RETENTION",
    "RUNOFF",
    "SCSCN",
    "SPECS",
    "EffectivePrecipitationResult",
    "RunoffDepths",
    "amc_curve_number",
    "potential_retention",
    "runoff_depths",
]

# --- sources -----------------------------------------------------------------------

_NEH630_10 = (
    "USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: "
    "Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004)"
)
_NEH630_10_URL = "https://www.hydrocad.net/neh/630ch10.pdf"
_NEH630_9 = Source(
    citation="USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, "
    "Chapter 9: Hydrologic Soil-Cover Complexes (210-VI-NEH, July 2004)",
    locator="p. 9-1: curve numbers derived from annual floods of watersheds generally "
    "under 1 square mile and storms of one day or less",
    url="https://www.hydrocad.net/neh/630ch9.pdf",
)
_TR55 = (
    "USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, "
    "2nd ed. (210-VI-TR-55, June 1986)"
)
_TR55_URL = "https://www.hydrocad.net/pdf/TR-55%20Manual.pdf"
_KZGW = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_PONCE_HAWKINS = (
    "Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached "
    "maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, "
    "R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and "
    "Drainage Engineering 111(4), 330-340"
)
_PONCE_HAWKINS_URL = "https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf"
_BANASIK = Source(
    citation="Banasik, K., Rutkowska, A. and Kohnová, S. (2014). Retention and curve "
    "number variability in a small agricultural catchment: the probabilistic "
    "approach. Water 6(5), 1118-1133, doi:10.3390/w6051118",
    locator="eqs. 12-13, p. 1124 (eq. 12 misprints 0.01381 for 0.01281)",
    url="https://mdpi-res.com/d_attachment/water/water-06-01118/article_deploy/"
    "water-06-01118.pdf",
)
_HYDROLOG_CN_TABLE = Source(
    citation="Hydrolog's table of TR-55 curve numbers (cn list), the CN its users "
    "take for soil-cover complexes",
    locator="its least and largest CN, 30 (woods and brush, good, A) and 98 "
    "(impervious and water)",
)
_HYDROGRAF_CATCHMENTS = Source(
    citation="Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the "
    "223 catchments of the Hydroni run h07 (2,941 km2)",
    locator="Consequences: CN of AMC II 51.8 to 81.4, median 70.8",
    url="https://github.com/Daldek/Hydrograf/blob/develop/docs/decisions/"
    "0075-cn-of-soil-cover-complexes.md",
)
_PMAXTP_FIXTURES = Source(
    citation="Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik "
    "(51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in "
    "November 2026",
    locator="tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: "
    "6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 "
    "to 99.9 %",
)
_LAMBDA_USE = Source(
    citation="Hydrolog's command scs effective: the ratio 0.2 of the CN tables and "
    "0.05 of Woodward et al. (2003), the two its catalog and GUI name",
    locator="catalog option ia_coefficient",
)

_WORLD_RECORD = (
    "the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January "
    "1966 (WMO Archive of Weather and Climate Extremes)"
)

_CN = Range(low=1.0, high=100.0)
"""The CN Hydrolog accepts: 100 is no retention; below 1 the retention would exceed
25 m of water, more than a soil holds (Hydrolog's bound since its first release)."""


def _cn_variable(applicability: Range | None, typical: Range) -> Variable:
    return Variable(
        name="cn",
        symbol="CN",
        unit="-",
        description="Curve number of the antecedent runoff condition of the formula.",
        physical=_CN,
        applicability=applicability if applicability is not None else "unstated",
        typical=typical,
    )


# --- retention -------------------------------------------------------------------


def _retention_mm(x: Values) -> float:
    cn = x.real("cn")
    retention_in = RETENTION.constant("s_scale") / cn - RETENTION.constant("s_offset")
    return convert(retention_in, "in", "mm")


def _retention_oracle(run: Callable[..., Values]) -> None:
    for cn in (30, 55, 72, 81, 98):
        exact = Fraction(254, 10) * (Fraction(1000, cn) - 10)
        assert_within(
            run(cn=float(cn)).real("retention_mm"),
            float(exact),
            rel=1e-13,
            reason="exact rational S = 25.4 (1000/CN - 10) mm; 1000/CN carries half "
            "an ulp of a number near 10, and the difference near CN 100 is small",
        )


RETENTION: Final = FormulaSpec(
    name="scs_cn_retention",
    title="Potential maximum retention S of the SCS curve number",
    function="hydrolog.runoff.scs_cn.potential_retention",
    family="empirical",
    equation="S = 25.4 * (1000 / CN - 10) [mm]",
    latex=r"S = 25.4\left(\frac{1000}{CN} - 10\right)",
    variables=(
        _cn_variable(None, Range(low=30.0, high=98.0, source=_HYDROLOG_CN_TABLE)),
    ),
    outputs=(
        Output(
            name="retention_mm",
            unit="mm",
            symbol="S",
            description="Potential maximum retention after runoff begins.",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        Source(
            citation=_NEH630_10,
            locator="eq. 10-12, p. 10-4 (S = 1000/CN - 10, in); eq. 10-13 (the "
            "same in mm)",
            url=_NEH630_10_URL,
        ),
        Source(citation=_TR55, locator="eq. 2-4, p. 2-1", url=_TR55_URL),
        Source(citation=_KZGW, locator="eq. 6.1, p. 88", url=_KZGW_URL),
    ),
    constants=(
        Constant(
            name="s_scale",
            value=1000.0,
            unit="in",
            symbol="1000",
            source=Source(
                citation=_NEH630_10, locator="eq. 10-12, p. 10-4", url=_NEH630_10_URL
            ),
        ),
        Constant(
            name="s_offset",
            value=10.0,
            unit="in",
            symbol="10",
            source=Source(
                citation=_NEH630_10, locator="eq. 10-12, p. 10-4", url=_NEH630_10_URL
            ),
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"cn": -1},
        limits=(
            Limit(
                name="no_retention",
                text="CN = 100 gives S = 0",
                inputs={"cn": 100.0},
                expected={"retention_mm": 0.0},
                tolerance=Tolerance(abs=0.0, reason="1000/100 - 10 is exactly 0"),
            ),
            Limit(
                name="exact_rational",
                text="S equals 25.4 (1000/CN - 10) mm in exact rational arithmetic "
                "for whole CN",
                check=_retention_oracle,
            ),
        ),
    ),
    validation="none: S is the definition of the curve number (NEH 630-10, eq. 10-12)",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "S in mm from the inch form of NEH 630-10 eq. 10-12 by the exact 25.4 "
            "mm/in of the units table, which is eq. 10-13 (S = 25400/CN - 254)"
        ),
        (
            "the CN of the antecedent runoff condition of the computation: ARC (AMC) "
            "II unless converted by scs_cn_amc"
        ),
    ),
    traps={
        "singular_at_bound": "range case cn-physical_low: CN = 1 gives S = 25,146 mm, "
        "finite; a CN below 1 is refused",
    },
    reference_cases=("tests/fixtures/formulas/scs-cn-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="S = 25.4 (1000/CN - 10) in exact rational arithmetic "
            "(fractions) for whole CN",
            test="tests/unit/test_formulas_scs_cn.py (limit exact_rational)",
        ),
    ),
)


def potential_retention(cn: float) -> float:
    """Return the potential maximum retention of a curve number, spec scs_cn_retention.

    Parameters
    ----------
    cn : float
        Curve number.

    Returns
    -------
    float
        Potential maximum retention [mm].

    Raises
    ------
    InvalidParameterError
        If the curve number is refused by the spec.
    """
    x = checked_inputs(RETENTION, cn=cn)
    return checked_outputs(RETENTION, {"retention_mm": _retention_mm(x)}).real(
        "retention_mm"
    )


# --- direct runoff ----------------------------------------------------------------


@dataclass(frozen=True)
class RunoffDepths(JsonResultMixin):
    """Direct runoff of a storm by the SCS curve number (spec ``scs_cn_runoff``).

    Attributes
    ----------
    total_effective_mm : float
        Direct runoff of the whole storm [mm].
    effective_mm : numpy.ndarray
        Direct runoff of each step [mm].
    runoff_coefficient : float
        Direct runoff over rainfall of the storm (0 without rainfall).
    retention_mm : float
        Potential maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    """

    total_effective_mm: float
    effective_mm: NDArray[np.float64]
    runoff_coefficient: float
    retention_mm: float
    initial_abstraction_mm: float


def _runoff(x: Values) -> dict[str, object]:
    depths = x.array("precipitation_mm")
    retention = potential_retention(x.real("cn"))
    abstraction = x.real("ia_coefficient") * retention
    cumulative = np.cumsum(depths)
    excess = np.maximum(cumulative - abstraction, 0.0)
    runoff = np.zeros_like(cumulative)
    wet = excess > 0.0
    runoff[wet] = excess[wet] ** 2 / (excess[wet] + retention)
    total = float(runoff[-1])
    rainfall = float(cumulative[-1])
    return {
        "total_effective_mm": total,
        "effective_mm": np.diff(runoff, prepend=0.0),
        "runoff_coefficient": total / rainfall if rainfall > 0.0 else 0.0,
        "retention_mm": retention,
        "initial_abstraction_mm": abstraction,
    }


def _increments_add_up(x: Values, out: Values) -> float:
    return float(np.sum(out.array("effective_mm")) - out.real("total_effective_mm"))


def _no_runoff_below_abstraction(run: Callable[..., Values]) -> None:
    out = run(precipitation_mm=[10.0, 20.0, 20.0], cn=50.0, ia_coefficient=0.2)
    assert_within(
        out.real("total_effective_mm"),
        0.0,
        abs=0.0,
        reason="P = 50 mm does not exceed Ia = 0.2 S = 50.8 mm at CN 50: Q is 0",
    )


def _all_runoff_without_retention(run: Callable[..., Values]) -> None:
    out = run(precipitation_mm=[12.5, 37.5], cn=100.0, ia_coefficient=0.2)
    assert_within(
        out.array("effective_mm"),
        [12.5, 37.5],
        rel=4e-16,
        reason="CN 100: S = Ia = 0, so Q = P of every step but for rounding",
    )


def _asymptote(run: Callable[..., Values]) -> None:
    out = run(precipitation_mm=[5.0e4], cn=72.0, ia_coefficient=0.2)
    retention = out.real("retention_mm")
    loss = 5.0e4 - out.real("total_effective_mm")
    # P - Q = Ia + S - S**2 / (P - Ia + S): within S**2 / P of Ia + S
    assert_within(
        loss,
        1.2 * retention,
        abs=retention**2 / 4.0e4,
        reason="NEH 630-10 eq. 10-16: P - Q tends to S + Ia; the gap is below S**2/P",
    )


def _exact_rational(run: Callable[..., Values]) -> None:
    for rainfall, cn in ((109.22, 74), (152.4, 70), (50.0, 72)):
        retention = Fraction(254, 10) * (Fraction(1000, cn) - 10)
        abstraction = Fraction(1, 5) * retention
        excess = Fraction(rainfall) - abstraction
        exact = excess**2 / (excess + retention)
        out = run(precipitation_mm=[rainfall], cn=float(cn), ia_coefficient=0.2)
        assert_within(
            out.real("total_effective_mm"),
            float(exact),
            rel=1e-14,
            reason="exact rational Q = (P - Ia)**2 / (P - Ia + S); float64 rounding",
        )


RUNOFF: Final = FormulaSpec(
    name="scs_cn_runoff",
    title="Direct runoff of a storm by the SCS curve number",
    function="hydrolog.runoff.scs_cn.runoff_depths",
    family="scheme",
    equation=(
        "Q(P) = (P - Ia)**2 / (P - Ia + S) for P > Ia, else 0; Ia = lambda * S; S of "
        "scs_cn_retention; P the cumulative depth after each step, the runoff of a "
        "step the difference of Q; C = Q / P of the storm"
    ),
    latex=(
        r"Q(P) = \begin{cases} \dfrac{(P - I_a)^2}{P - I_a + S} & P > I_a \\ 0 & "
        r"P \le I_a \end{cases},\quad I_a = \lambda S,\quad q_i = Q(P_i) - "
        r"Q(P_{i-1}),\quad C = \frac{Q}{P}"
    ),
    variables=(
        Variable(
            name="precipitation_mm",
            symbol=r"\Delta P_i",
            unit="mm",
            kind="real_array",
            description="Rainfall depth of each step of the storm (a total is one "
            "step).",
            physical=Range(low=0.0, test_high=1825.0, test_reason=_WORLD_RECORD),
            applicability="unstated",
            typical=Range(low=0.0, high=350.0, source=_PMAXTP_FIXTURES),
        ),
        _cn_variable(
            Range(
                low=40.0,
                high=100.0,
                source=Source(
                    citation=_TR55,
                    locator="chapter 2, limitations, p. 2-11: when the weighted CN is "
                    "less than 40, use another procedure",
                    url=_TR55_URL,
                ),
            ),
            Range(low=30.0, high=98.0, source=_HYDROLOG_CN_TABLE),
        ),
        Variable(
            name="ia_coefficient",
            symbol=r"\lambda",
            unit="-",
            description="Initial abstraction ratio Ia / S.",
            physical=Range(low=0.0, low_inclusive=False, high=1.0),
            applicability="unstated",
            typical=Range(low=0.05, high=0.2, source=_LAMBDA_USE),
        ),
    ),
    outputs=(
        Output(
            name="total_effective_mm",
            unit="mm",
            symbol="Q",
            description="Direct runoff of the storm.",
            physical=Range(low=0.0),
        ),
        Output(
            name="effective_mm",
            unit="mm",
            kind="real_array",
            symbol="q_i",
            description="Direct runoff of each step.",
            physical=Range(low=0.0),
            boundary_tolerance=1e-9,
        ),
        Output(
            name="runoff_coefficient",
            unit="-",
            symbol="C",
            description="Direct runoff over the rainfall of the storm.",
            physical=Range(low=0.0, high=1.0),
        ),
        Output(
            name="retention_mm",
            unit="mm",
            symbol="S",
            physical=Range(low=0.0),
        ),
        Output(
            name="initial_abstraction_mm",
            unit="mm",
            symbol="I_a",
            physical=Range(low=0.0),
        ),
    ),
    sources=(
        Source(
            citation=_NEH630_10,
            locator="eqs. 10-9 to 10-11, pp. 10-2 to 10-4; example 10-6 and table "
            "10-2, pp. 10-17 to 10-18 (cumulative rainfall of a storm)",
            url=_NEH630_10_URL,
        ),
        Source(citation=_TR55, locator="eqs. 2-1 to 2-4, p. 2-1", url=_TR55_URL),
        Source(citation=_KZGW, locator="eq. 6.2, p. 88", url=_KZGW_URL),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"precipitation_mm": 1, "cn": 1, "ia_coefficient": -1},
        conservation=(
            Conservation(
                name="steps_add_up",
                text="the runoff of the steps adds up to the runoff of the storm",
                residual=_increments_add_up,
                tolerance=Tolerance(
                    abs=1e-9,
                    reason="differences of the cumulative runoff, each within a few "
                    "units in the last place of a depth below 10 m",
                ),
            ),
        ),
        limits=(
            Limit(
                name="no_runoff_below_ia",
                text="no runoff while the rainfall does not exceed Ia (NEH 630-10, "
                "eq. 10-9)",
                check=_no_runoff_below_abstraction,
            ),
            Limit(
                name="cn_100",
                text="CN = 100 gives S = Ia = 0 and the rainfall of every step as "
                "runoff",
                check=_all_runoff_without_retention,
            ),
            Limit(
                name="ultimate_loss",
                text="P - Q tends to S + Ia as P grows (NEH 630-10, eq. 10-16)",
                check=_asymptote,
            ),
            Limit(
                name="exact_rational",
                text="Q equals the equation in exact rational arithmetic",
                check=_exact_rational,
            ),
        ),
    ),
    validation=(
        "NEH 630-9 (p. 9-1) derives the curve numbers of its tables from annual floods "
        "of small agricultural watersheds, generally under 1 square mile, and storms "
        "of one day or less; the sources give no error statistic of the equation"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "SI units: depths in mm",
        (
            "the equation on the cumulative rainfall of the storm, the runoff of each "
            "step the difference of the cumulative runoff (NEH 630-10 example 10-6; "
            "KZGW 2017 eq. 6.2); a total is a storm of one step"
        ),
        "Ia = lambda S with lambda given; S from the CN by scs_cn_retention",
        "the CN of ARC (AMC) II unless converted by scs_cn_amc",
        "C = Q / P of the storm, 0 without rainfall",
    ),
    assumptions=(
        (
            "the CN of the NRCS tables assume lambda = 0.2; another lambda needs CN "
            "fitted for it (NEH 630-10 p. 10-4; Woodward et al. 2003), and the command "
            "scs effective then gives the notice ia_coefficient_nonstandard"
        ),
        (
            "direct runoff of one storm, not an infiltration model or a continuous "
            "simulation (NEH 630-10 p. 10-19); not for snowmelt or rain on frozen "
            "ground (TR-55 p. 2-11)"
        ),
        (
            "TR-55 (p. 2-11) finds the method less accurate for runoff below 0.5 in "
            "(12.7 mm); this limit of the output gives no notice"
        ),
    ),
    traps={
        "difference_denominator": "limit cn_100: P - Ia + S is P itself at CN 100 "
        "and a step of no rainfall gives no runoff",
        "gap_propagation": "type case precipitation_mm-nan_element: a gap is refused "
        "before the cumulative sum",
        "many_small_terms": "test_a_long_storm_matches_its_total_summed_exactly",
    },
    reference_cases=("tests/fixtures/formulas/scs-cn-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="Q in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_scs_cn.py (limit exact_rational)",
        ),
    ),
)


def runoff_depths(
    precipitation_mm: NDArray[np.float64] | list[float] | tuple[float, ...],
    cn: float,
    ia_coefficient: float,
) -> RunoffDepths:
    """Return the direct runoff of a storm, spec scs_cn_runoff.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Rainfall depth of each step of the storm [mm]; a total is a storm of one
        step.
    cn : float
        Curve number of the antecedent runoff condition of the storm.
    ia_coefficient : float
        Initial abstraction ratio.

    Returns
    -------
    RunoffDepths
        The runoff of the storm and of each step, the runoff coefficient, the
        retention and the initial abstraction.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec: a negative or missing depth among them.

    Warns
    -----
    OutsideApplicability
        If the curve number is outside the applicability of the method.
    """
    x = checked_inputs(
        RUNOFF, precipitation_mm=precipitation_mm, cn=cn, ia_coefficient=ia_coefficient
    )
    out = checked_outputs(RUNOFF, _runoff(x))
    return RunoffDepths(
        total_effective_mm=out.real("total_effective_mm"),
        effective_mm=out.array("effective_mm"),
        runoff_coefficient=out.real("runoff_coefficient"),
        retention_mm=out.real("retention_mm"),
        initial_abstraction_mm=out.real("initial_abstraction_mm"),
    )


# --- antecedent runoff condition ----------------------------------------------------

_ARC = ("I", "III")


def _converted(cn: float, ratio: float) -> int:
    scale = AMC_CONVERSION.constant("cn_scale")
    converted = cn / (ratio + (1.0 - ratio) * cn / scale)
    return max(1, min(round(scale), round(converted)))


def _conversion(x: Values) -> int:
    ratio = AMC_CONVERSION.constant(f"ratio_{x.choice('amc').lower()}")
    return _converted(x.real("cn"), ratio)


def _ratio_identity(run: Callable[..., Values]) -> None:
    for amc, ratio in (("I", Fraction(2281, 1000)), ("III", Fraction(427, 1000))):
        for cn in (55, 60, 72, 85, 95):
            s_ii = Fraction(1000, cn) - 10
            exact = Fraction(1000) / (10 + ratio * s_ii)
            assert run(cn=float(cn), amc=amc).integer("cn_adjusted") == round(exact)


AMC_CONVERSION: Final = FormulaSpec(
    name="scs_cn_amc",
    title="Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)",
    function="hydrolog.runoff.scs_cn.amc_curve_number",
    family="empirical",
    equation=(
        "CN_x = CN / (k_x + (1 - k_x) * CN / 100), k_I = 2.281, k_III = 0.427 "
        "(S_x = k_x * S_II), rounded to the nearest integer, at least 1"
    ),
    latex=(
        r"CN_x = \operatorname{round}\frac{CN}{k_x + (1 - k_x)\,CN/100},\quad "
        r"k_{I} = 2.281,\ k_{III} = 0.427"
    ),
    variables=(
        _cn_variable(
            Range(
                low=55.0,
                high=95.0,
                source=Source(
                    citation=_PONCE_HAWKINS,
                    locator="p. 15: eqs. 15-16 applicable in the range 55 <= CN <= 95",
                    url=_PONCE_HAWKINS_URL,
                ),
            ),
            Range(low=51.8, high=81.4, source=_HYDROGRAF_CATCHMENTS),
        ),
        Variable(
            name="amc",
            symbol="ARC",
            unit="-",
            kind="choice",
            description="Antecedent runoff condition to convert to: I dry, III wet.",
            choices=_ARC,
        ),
    ),
    outputs=(
        Output(
            name="cn_adjusted",
            unit="-",
            kind="integer",
            symbol="CN_x",
            description="Curve number of the condition.",
            physical=Range(low=1.0, high=100.0),
        ),
    ),
    sources=(
        Source(
            citation=_PONCE_HAWKINS,
            locator="eqs. 13-16, p. 15 (S_I = 2.281 S_II, S_III = 0.427 S_II)",
            url=_PONCE_HAWKINS_URL,
        ),
        _BANASIK,
    ),
    constants=(
        Constant(
            name="ratio_i",
            value=2.281,
            unit="-",
            symbol="k_{I}",
            source=Source(
                citation=_PONCE_HAWKINS,
                locator="eq. 13, p. 15 (r2 = 0.999); Banasik et al. (2014) eq. 12",
                url=_PONCE_HAWKINS_URL,
            ),
        ),
        Constant(
            name="ratio_iii",
            value=0.427,
            unit="-",
            symbol="k_{III}",
            source=Source(
                citation=_PONCE_HAWKINS,
                locator="eq. 14, p. 15 (r2 = 0.994); Banasik et al. (2014) eq. 13",
                url=_PONCE_HAWKINS_URL,
            ),
        ),
        Constant(
            name="cn_scale",
            value=100.0,
            unit="-",
            symbol="100",
            source=Source(
                citation=_NEH630_10,
                locator="eq. 10-11, p. 10-4: CN = 1000/(10 + S), 100 at S = 0",
                url=_NEH630_10_URL,
            ),
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"cn": 1},
        limits=(
            Limit(
                name="no_retention",
                text="CN 100 stays 100 in either condition (S = 0)",
                inputs={"cn": 100.0, "amc": "III"},
                expected={"cn_adjusted": 100},
                tolerance=Tolerance(abs=0.0, reason="an integer"),
            ),
            Limit(
                name="ratio_of_retention",
                text="the converted CN is the CN of k_x S_II, rounded, in exact "
                "rational arithmetic",
                check=_ratio_identity,
            ),
        ),
    ),
    validation=(
        "Ponce and Hawkins (1996, p. 15) report the fits S_I = 2.281 S_II (r2 0.999, "
        "standard error 0.206 in) and S_III = 0.427 S_II (r2 0.994, 0.088 in) to NEH "
        "table 10-1, and standard errors of 1.0 CN (eq. 15) and 0.7 CN (eq. 16); "
        "against that table at CN 55 to 95 the rounded conversion differs by up to "
        "2 CN for ARC I and 1 CN for ARC III (unrounded at most 2.45 CN for ARC I at "
        "CN 92 and 1.19 CN for ARC III at CN 79)"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "the fit of Hawkins et al. (1985) to the curves of NRCS, not NEH 630-10 "
            "table 10-1 itself (NEH 630-10 p. 10-6; it gives the table) nor Chow et "
            "al. (1988) eqs. 5.5.7-5.5.8, another fit"
        ),
        (
            "rounded to the nearest integer as table 10-1 prints them, a half to the "
            "even integer; at least 1"
        ),
        "ARC II is the CN as given: no formula",
    ),
    assumptions=(
        (
            "NEH 630-10 (pp. 10-5, 10-7) found no relation between the rainfall of the "
            "five preceding days and the CN: the condition is chosen by the engineer"
        ),
    ),
    no_traps_reason=(
        "the denominators k + (1 - k) CN / 100 lie between 0.43 and 2.28 for CN of 1 "
        "to 100; no logarithm, root or exponential"
    ),
    reference_cases=("tests/fixtures/formulas/scs-cn-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the CN of S_x = k_x S_II in exact rational arithmetic "
            "(fractions), rounded",
            test="tests/unit/test_formulas_scs_cn.py (limit ratio_of_retention)",
        ),
    ),
)


def amc_curve_number(cn: float, amc: str) -> int:
    """Return the curve number of another antecedent condition, spec scs_cn_amc.

    Parameters
    ----------
    cn : float
        Curve number of the average condition (II).
    amc : {"I", "III"}
        Condition to convert to.

    Returns
    -------
    int
        Curve number of the condition.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.

    Warns
    -----
    OutsideApplicability
        If the curve number is outside the range of the conversion.
    """
    x = checked_inputs(AMC_CONVERSION, cn=cn, amc=amc)
    return checked_outputs(AMC_CONVERSION, {"cn_adjusted": _conversion(x)}).integer(
        "cn_adjusted"
    )


SPECS: Final = (RETENTION, RUNOFF, AMC_CONVERSION)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""


# --- the interface of earlier versions ------------------------------------------------


class AMC(Enum):
    """
    Antecedent Moisture Condition (AMC).

    AMC represents the soil moisture condition before a storm event,
    which affects the runoff potential.

    Attributes
    ----------
    I : str
        Dry conditions - lowest runoff potential.
    II : str
        Average/normal conditions (default).
    III : str
        Wet conditions - highest runoff potential.
    """

    I = "dry"  # noqa: E741  # AMC class I is the SCS name
    II = "normal"
    III = "wet"


@dataclass
class EffectivePrecipitationResult(JsonResultMixin):
    """
    Result of effective precipitation calculation.

    Attributes
    ----------
    effective_mm : NDArray[np.float64] | float
        Effective precipitation (runoff depth) [mm].
    total_effective_mm : float
        Total effective precipitation [mm].
    retention_mm : float
        Maximum retention S [mm].
    initial_abstraction_mm : float
        Initial abstraction Ia [mm].
    cn_adjusted : float
        CN used: the CN given for AMC II, the converted integer for AMC I and III.
    """

    effective_mm: NDArray[np.float64] | float
    total_effective_mm: float
    retention_mm: float
    initial_abstraction_mm: float
    cn_adjusted: float


def _storm(
    precipitation_mm: NDArray[np.float64] | float | list[float],
) -> tuple[NDArray[np.float64] | list[float], bool]:
    """Return the steps of a storm and whether a total was given (one step).

    A value that is not a sequence becomes one step as it is, so the spec refuses
    a string, ``None`` or a ``bool`` given as the total.
    """
    if isinstance(precipitation_mm, np.ndarray | list | tuple):
        return precipitation_mm, False
    return [precipitation_mm], True


class SCSCN:
    """
    SCS Curve Number method for rainfall-runoff calculation.

    Computes with the formulas of the specs ``scs_cn_retention``, ``scs_cn_runoff``
    and ``scs_cn_amc`` (``docs/FORMULAS.md``), which refuse an invalid CN or initial
    abstraction ratio when a method uses it.

    Parameters
    ----------
    cn : float
        Curve Number for AMC-II conditions (1-100).
        CN=100 means all precipitation becomes runoff.
    ia_coefficient : float, optional
        Initial abstraction coefficient (λ), by default 0.2.
        Ia = λ · S

    Notes
    -----
    The standard initial abstraction ratio is λ = 0.2 (USDA-NRCS,
    NEH Part 630, Chapter 10). An alternative value of λ ≈ 0.05 was
    proposed based on analysis of several hundred watershed datasets:

        Woodward, D.E.; Hawkins, R.H.; Jiang, R.; Hjelmfelt Jr., A.T.;
        Van Mullem, J.A.; Quan, Q.D. (2003). Runoff Curve Number Method:
        Examination of the Initial Abstraction Ratio. World Water and
        Environmental Resources Congress, Philadelphia, PA. ASCE.
        DOI: 10.1061/40685(2003)308

    See also: Hawkins, R.H.; Ward, T.J.; Woodward, D.E.; Van Mullem,
    J.A. (2009). Curve Number Hydrology: State of the Practice.
    ASCE/EWRI.

    **Caution:** When using λ = 0.05, the standard CN lookup tables
    (TR-55, calibrated with λ = 0.2) are not directly applicable —
    CN values require recalibration. As of 2026, NRCS has not
    officially adopted λ = 0.05 in its directives.

    Examples
    --------
    >>> scs = SCSCN(cn=72)
    >>> result = scs.effective_precipitation(precipitation_mm=50.0)
    >>> print(f"Effective: {result.total_effective_mm:.2f} mm")
    Effective: 7.09 mm
    >>> print(f"C = {scs.runoff_coefficient(50.0):.3f}")
    C = 0.142
    """

    def __init__(self, cn: float, ia_coefficient: float = 0.2) -> None:
        """
        Keep the curve number and the initial abstraction ratio.

        Parameters
        ----------
        cn : float
            Curve Number for AMC-II (1-100).
        ia_coefficient : float, optional
            Initial abstraction coefficient, by default 0.2.
        """
        self.cn = cn
        self.ia_coefficient = ia_coefficient

    def adjust_cn_for_amc(self, amc: AMC) -> float:
        """
        Adjust CN for Antecedent Moisture Condition.

        AMC II keeps the CN as given; AMC I and III convert it by the formulas of
        Hawkins et al. (1985) (spec ``scs_cn_amc``, rounded to an integer), which
        approximate the table of NEH 630 ch. 10 (table 10-1) within 2 CN.

        Parameters
        ----------
        amc : AMC
            Antecedent Moisture Condition (I, II, or III).

        Returns
        -------
        float
            Adjusted CN: the CN given for AMC II, an integer for AMC I and III.

        Raises
        ------
        InvalidParameterError
            If ``amc`` is not an :class:`AMC`, or the spec refuses the CN.

        Warns
        -----
        OutsideApplicability
            For AMC I or III, if the CN is outside the CN of the conversion
            (method ``scs_cn_amc``, parameter ``cn``).
        """
        if amc == AMC.II:
            return self.cn
        if amc in (AMC.I, AMC.III):
            return amc_curve_number(self.cn, amc.name)
        raise InvalidParameterError(f"Unknown AMC: {amc}")

    def retention(self, cn: float) -> float:
        """
        Calculate maximum retention S (spec ``scs_cn_retention``).

        Parameters
        ----------
        cn : float
            Curve Number (1-100).

        Returns
        -------
        float
            Maximum retention S [mm]; 0 for CN = 100.
        """
        return potential_retention(cn)

    def initial_abstraction(self, retention_mm: float) -> float:
        """
        Calculate initial abstraction Ia = λ·S (spec ``scs_cn_runoff``).

        Initial abstraction represents interception, depression storage,
        evaporation and infiltration before runoff begins (TR-55, p. 2-1).

        Parameters
        ----------
        retention_mm : float
            Maximum retention S [mm].

        Returns
        -------
        float
            Initial abstraction Ia [mm].
        """
        return self.ia_coefficient * retention_mm

    def effective_precipitation(
        self,
        precipitation_mm: NDArray[np.float64] | float | list[float],
        amc: AMC = AMC.II,
    ) -> EffectivePrecipitationResult:
        """
        Calculate effective precipitation (runoff depth).

        The runoff of spec ``scs_cn_runoff`` with the CN of the moisture condition.

        Parameters
        ----------
        precipitation_mm : NDArray[np.float64] | float | list
            Precipitation depth(s) [mm]. Can be:
            - Single value (total precipitation)
            - Array of values (hyetograph intervals)
        amc : AMC, optional
            Antecedent Moisture Condition, by default AMC.II.

        Returns
        -------
        EffectivePrecipitationResult
            Result containing effective precipitation and parameters.

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input: a negative depth, a missing value (NaN)
            or a CN outside 1-100 among them.

        Examples
        --------
        >>> scs = SCSCN(cn=72)
        >>> result = scs.effective_precipitation(50.0)
        >>> print(f"Pe = {result.total_effective_mm:.2f} mm")
        Pe = 7.09 mm
        """
        cn_adjusted = self.adjust_cn_for_amc(amc)
        storm, scalar = _storm(precipitation_mm)
        runoff = runoff_depths(storm, cn_adjusted, self.ia_coefficient)
        effective: NDArray[np.float64] | float
        effective = float(runoff.effective_mm[0]) if scalar else runoff.effective_mm
        return EffectivePrecipitationResult(
            effective_mm=effective,
            total_effective_mm=runoff.total_effective_mm,
            retention_mm=runoff.retention_mm,
            initial_abstraction_mm=runoff.initial_abstraction_mm,
            cn_adjusted=cn_adjusted,
        )

    def runoff_coefficient(
        self,
        precipitation_mm: float,
        amc: AMC = AMC.II,
    ) -> float:
        """
        Calculate runoff coefficient C = Pe / P (spec ``scs_cn_runoff``).

        Parameters
        ----------
        precipitation_mm : float
            Total precipitation depth [mm].
        amc : AMC, optional
            Antecedent Moisture Condition, by default AMC.II.

        Returns
        -------
        float
            Runoff coefficient C = Pe / P (0 to 1; 0 without precipitation).

        Examples
        --------
        >>> scs = SCSCN(cn=72)
        >>> c = scs.runoff_coefficient(50.0)
        >>> print(f"C = {c:.3f}")
        C = 0.142
        """
        cn_adjusted = self.adjust_cn_for_amc(amc)
        storm, _ = _storm(precipitation_mm)
        runoff = runoff_depths(storm, cn_adjusted, self.ia_coefficient)
        return runoff.runoff_coefficient
