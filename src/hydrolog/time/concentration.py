"""Time of concentration: six empirical formulas, each declared by its spec.

The formulas are declared by their specs (Nogat's computation standard, ADR-0050) and
named like the methods: :data:`KIRPICH` (``kirpich``), :data:`NRCS` (``nrcs``),
:data:`GIANDOTTI` (``giandotti``), :data:`FAA` (``faa``), :data:`KERBY` (``kerby``)
and :data:`KERBY_KIRPICH` (``kerby_kirpich``); ``docs/FORMULAS.md`` shows their
equations, constants, ranges and sources (ADR-0052). :class:`ConcentrationTime`
computes them, every result in minutes.

Each formula is evaluated in the units of its source, with the exact conversions of the
units table: Kirpich, Kerby and FAA with lengths in feet, NRCS with feet, inches and
percent and the result in hours, Giandotti with the result in hours. The area of a
watershed, an argument of Giandotti's formula only, is checked against the data of the
other methods by ``WatershedParameters.calculate_tc`` (:mod:`hydrolog._ranges`).

Examples
--------
>>> round(ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023), 4)
85.8568
>>> round(ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72), 3)
368.696
>>> round(ConcentrationTime.giandotti(
...     area_km2=45.0, length_km=12.0, elevation_diff_m=350.0), 2)
179.73
>>> round(ConcentrationTime.faa(
...     length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.6), 3)
15.847
>>> round(ConcentrationTime.kerby(
...     length_km=0.10, slope_m_per_m=0.008, retardance=0.40), 3)
24.977
>>> round(ConcentrationTime.kerby_kirpich(
...     overland_length_km=0.25, overland_slope_m_per_m=0.008, retardance=0.40,
...     flow_path_length_km=5.25, flow_path_slope_m_per_m=0.005), 2)
143.88
"""

from __future__ import annotations

import math
from collections.abc import Callable
from decimal import Decimal, localcontext
from typing import Final

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
    Constant,
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Source,
    Values,
    Variable,
    assert_within,
    convert,
)

__all__ = [
    "FAA",
    "GIANDOTTI",
    "KERBY",
    "KERBY_KIRPICH",
    "KIRPICH",
    "NRCS",
    "SPECS",
    "ConcentrationTime",
]

# --- sources -----------------------------------------------------------------------

_FANG = (
    "Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). "
    "Literature review on timing parameters for hydrographs. TxDOT Research Report "
    "0-4696-1, Lamar University"
)
_FANG_URL = "https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf"
_ROUSSEL = (
    "Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. "
    "(2005). Time-parameter estimation for applicable Texas watersheds. TxDOT "
    "Research Report 0-4696-2, Lamar University"
)
_ROUSSEL_URL = "https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf"
_CLEVELAND = (
    "Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for "
    "estimation of time of concentration in Texas for low-slope conditions. TxDOT "
    "Product 0-6382-P1, Texas Tech University"
)
_CLEVELAND_URL = "https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf"
_TXDOT = (
    "Texas Department of Transportation (2019). Hydraulic Design Manual, chapter 4, "
    "section 11: Time of Concentration"
)
_TXDOT_URL = (
    "https://www.txdot.gov/manuals/des/hyd/chapter-4--hydrology/"
    "section-11--time-of-concentration.html"
)
_MOTA = (
    "Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich "
    "para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos "
    "20(1), 55-59"
)
_MOTA_URL = "https://revistas.abrhidro.org.br/article.php?Article=5027"
_FDOT = "Florida Department of Transportation (2024). Drainage Design Guide, chapter 2"
_FDOT_URL = (
    "https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/roadway/"
    "drainage/files/drainagedesignguide/chapter2.pdf"
)
_NEH630_15 = (
    "USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: "
    "Time of Concentration (210-VI-NEH, May 2010)"
)
_NEH630_15_URL = (
    "https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf"
)
_NEH630_F = Source(
    citation="USDA-NRCS (2025). 210 NEH Part 630 Hydrology, Subpart F: Time of "
    "Concentration (amended June 2025)",
    locator="eqs. 630.15-3, 630.15-4a and 630.15-4b, the same equations and limits",
    url="https://directives.nrcs.usda.gov/sites/default/files2/1749749287/"
    "Subpart%20F%20%E2%80%93%20Time%20of%20Concentration.pdf",
)
_ADBPO = Source(
    citation="Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto "
    "idrogeologico (PAI), Direttiva sulla piena di progetto",
    locator="§6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937)",
    url="https://www.adbpo.it/PAI/7%20-%20Norme%20di%20attuazione/"
    "7.2%20-%20Direttive%20di%20Piano/Direttiva2/DIRETTIVA/DIRETTIVA.PDF",
)
_MICHAILIDI = (
    "Michailidi, E.M., Antoniadi, S., Koukouvinos, A., Bacchi, B. and Efstratiadis, "
    "A. (2018). Timing the time of concentration: shedding light on a paradox. "
    "Hydrological Sciences Journal 63(5), 721-740, doi:10.1080/02626667.2018.1450985"
)
_MICHAILIDI_URL = (
    "https://www.itia.ntua.gr/en/getfile/1777/2/documents/"
    "Timing_the_time_of_concentration_shedding_light_on_a_paradox_nNWG5Fq.pdf"
)
_ALMEIDA = Source(
    citation="Almeida, I.K., Almeida, A.K., Anache, J.A.A., Steffen, J.L. and Alves "
    "Sobrinho, T. (2014). Estimation on time of concentration of overland flow in "
    "watersheds: a review. Geociências 33(4), 661-671",
    locator="table 1, Giandotti: basins of central and northern Italy, 170-70,000 km2 "
    "(after Giandotti 1940, Preti et al. 2011, Radice et al. 2012)",
    url="https://www.revistageociencias.com.br/geociencias-arquivos/33/"
    "volume33_4_files/33-4-artigo-9.pdf",
)
_FAA = (
    "Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B"
)
_FAA_URL = (
    "https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf"
)
_INDOT = Source(
    citation="Indiana Department of Transportation. Indiana Design Manual (metric, "
    "archived), Part IV, chapter 29: Hydrology",
    locator="eq. 29-7.14, Kerby's formula in SI units with K = 1.44",
    url="https://www.in.gov/dot/div/contracts/standards/dm-Archived/07%20Metric/"
    "Part%204%20Vol.%201/Ch%2029/Ch29.pdf",
)
_SI_PERCENT = Source(
    citation="BIPM (2019). The International System of Units (SI), 9th edition, "
    "version 4.01",
    locator="section 5.4.7: the symbol % (percent) is the number 0.01",
    url="https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf",
)

# Typical ranges: the values of the ecosystem's use (CMP-1.5)
_HANDOFFS = (
    "Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November "
    "2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa "
    "(134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, "
    "and the guide's Kamiennik to Świerzawa (37.22 km2)"
)
_HANDOFF_FILES = (
    "tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json"
)


def _from_handoffs(what: str) -> Source:
    return Source(citation=_HANDOFFS, locator=f"{_HANDOFF_FILES}: {what}")


_HYDROGRAF_CATCHMENTS = Source(
    citation="Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the "
    "223 catchments of the Hydroni run h07 (2,941 km2)",
    locator="Consequences: CN of AMC II 51.8 to 81.4, median 70.8",
    url="https://github.com/Daldek/Hydrograf/blob/develop/docs/decisions/"
    "0075-cn-of-soil-cover-complexes.md",
)
_KERBY_TABLE_USE = Source(
    citation="Hydrolog's catalog and GUI: Kerby's table of N (Roussel et al. 2005, "
    "supplement, p. 29), from which their users take N",
    locator="option retardance of tc kerby and tc kerby-kirpich: 0.02 (pavement) to "
    "0.80 (dense grass, coniferous forest)",
)
_FAA_TABLE_USE = Source(
    citation="Hydrolog's catalog: the coefficients of table I of AC 150/5320-5B, "
    "which the option runoff_coeff of tc faa quotes, without its 0.00",
    locator="table I, p. 10: moderately pervious soils 0.05-0.20 to watertight roofs "
    "0.75-0.95",
)

# --- shared variables ---------------------------------------------------------------

_LENGTH_TEST = 1000.0
_LENGTH_REASON = (
    "1,000 km, about the length of the Vistula, the longest river of Poland: no flow "
    "path of a Polish watershed is longer"
)
_SLOPE_TEST = 1.0
_SLOPE_REASON = (
    "a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface "
    "of a watershed on average"
)
_LENGTH = Range(
    low=0.0, low_inclusive=False, test_high=_LENGTH_TEST, test_reason=_LENGTH_REASON
)
_SLOPE = Range(
    low=0.0, low_inclusive=False, test_high=_SLOPE_TEST, test_reason=_SLOPE_REASON
)
_RETARDANCE = Range(
    low=0.0,
    low_inclusive=False,
    test_high=8.0,
    test_reason="ten times the largest N of Kerby's table (0.80)",
)

_FLOW_PATH_TYPICAL = Range(
    low=0.05, high=30.0, source=_from_handoffs("flow paths of 0.0566 to 28.88 km")
)
_FLOW_PATH_SLOPE_TYPICAL = Range(
    low=0.002,
    high=0.11,
    source=_from_handoffs("flow path slopes of 0.00244 to 0.1055 m/m"),
)
_OVERLAND_TYPICAL = Range(
    low=0.04, high=0.7, source=_from_handoffs("overland segments of 0.0495 to 0.693 km")
)
_OVERLAND_SLOPE_TYPICAL = Range(
    low=0.005,
    high=0.19,
    source=_from_handoffs("overland slopes of 0.00594 to 0.1804 m/m"),
)
_KERBY_LENGTH = Range(
    low=0.0,
    high=0.366,
    source=Source(
        citation=_ROUSSEL,
        locator="supplement, p. 29: in the development of Kerby's equation the "
        "length of overland flow was as much as about 1,200 feet (366 meters), an "
        "upper limit",
        url=_ROUSSEL_URL,
    ),
)
_KERBY_N = Range(
    low=0.02,
    high=0.80,
    source=Source(
        citation=_ROUSSEL,
        locator="supplement, p. 29: Kerby's table of the retardance N, pavement 0.02 "
        "to dense grass, coniferous forest or deciduous forest with deep litter 0.80",
        url=_ROUSSEL_URL,
    ),
)
_KERBY_N_TYPICAL = Range(low=0.02, high=0.80, source=_KERBY_TABLE_USE)


def _flow_path_length(applicability: Range | None) -> Variable:
    return Variable(
        name="length_km",
        symbol="L",
        unit="km",
        description="Length of the longest flow path, from the outlet to the "
        "hydraulically most distant point of the watershed.",
        physical=_LENGTH,
        applicability=applicability if applicability is not None else "unstated",
        typical=_FLOW_PATH_TYPICAL,
    )


def _overland_length(name: str, applicability: Range | None) -> Variable:
    return Variable(
        name=name,
        symbol="L_{ov}" if name.startswith("overland") else "L",
        unit="km",
        description="Overland (sheet) flow length, from the most remote point to a "
        "defined channel or the inlet.",
        physical=_LENGTH,
        applicability=applicability if applicability is not None else "unstated",
        typical=_OVERLAND_TYPICAL,
    )


def _overland_slope(name: str, applicability: Range | None) -> Variable:
    return Variable(
        name=name,
        symbol="S_{ov}" if name.startswith("overland") else "S",
        unit="m/m",
        description="Slope of the surface the overland flow runs on.",
        physical=_SLOPE,
        applicability=applicability if applicability is not None else "unstated",
        typical=_OVERLAND_SLOPE_TYPICAL,
    )


def _retardance() -> Variable:
    return Variable(
        name="retardance",
        symbol="N",
        unit="-",
        description="Kerby's retardance coefficient of the overland surface, not "
        "Manning's n.",
        physical=_RETARDANCE,
        applicability=_KERBY_N,
        typical=_KERBY_N_TYPICAL,
    )


def _tc_output() -> Output:
    return Output(
        name="tc_min",
        unit="min",
        symbol="t_c",
        description="Time of concentration.",
        physical=Range(low=0.0, low_inclusive=False),
    )


# --- decimal oracles (CMP-6.2) --------------------------------------------------------

_DIGITS = 50
"""Precision of the decimal oracles: far beyond float64's 16 digits."""
_FOOT_M = Decimal("0.3048")
_INCH_MM = Decimal("25.4")
_ORACLE_REASON = (
    "float64 powers of the converted inputs against the source's equation in decimal "
    "arithmetic at 50 digits: a few units in the last place of each power"
)


def _exact(value: float) -> Decimal:
    """Return the exact value of a float (``Decimal`` of a float is exact)."""
    return Decimal(value)


def _with_offset(slope: Decimal) -> Decimal:
    """Cleveland et al. (2012), eq. 1: S + 0.0005 below S = 0.002."""
    return slope + Decimal("0.0005") if slope < Decimal("0.002") else slope


def _kirpich_decimal(length_km: float, slope: Decimal) -> Decimal:
    # The SI form of WR-D-71-1 eq. 5.4.2.2 (L in m) with its constant unrounded:
    # 0.0078 (1 / 0.3048)^0.77
    per_metre = Decimal("0.0078") * (1 / _FOOT_M) ** Decimal("0.77")
    length_m = _exact(length_km) * 1000
    return per_metre * length_m ** Decimal("0.77") * slope ** Decimal("-0.385")


def _kerby_decimal(length_km: float, slope: Decimal, retardance: float) -> Decimal:
    # INDOT eq. 29-7.14's form, K (L N)^0.467 S^(-0.467/2) with L in m and K unrounded
    k_metric = (Decimal("0.67") / _FOOT_M) ** Decimal("0.467")
    product = _exact(length_km) * 1000 * _exact(retardance)
    return (
        k_metric
        * product ** Decimal("0.467")
        * _with_offset(slope) ** (Decimal("-0.467") / 2)
    )


def _power_law(
    run: Callable[..., Values], name: str, base: dict[str, float], exponent: float
) -> None:
    """Assert that doubling ``name`` multiplies tc by ``2 ** exponent``."""
    once = run(**base).real("tc_min")
    twice = run(**{**base, name: 2.0 * base[name]}).real("tc_min")
    assert_within(
        twice / once,
        2.0**exponent,
        rel=1e-14,
        reason=f"tc is proportional to {name} to the power {exponent}: the ratio of "
        "two float64 evaluations, each within a few units in the last place",
    )


# --- Kirpich --------------------------------------------------------------------------


def _kirpich_min(length_km: float, slope_m_per_m: float) -> float:
    """Kirpich's tc [min] of checked inputs, in the source's feet."""
    length_ft = convert(length_km, "km", "ft")
    return float(
        KIRPICH.constant("kirpich_coefficient")
        * length_ft ** KIRPICH.constant("kirpich_length_exponent")
        * slope_m_per_m ** KIRPICH.constant("kirpich_slope_exponent")
    )


def _kirpich_oracle(run: Callable[..., Values]) -> None:
    points = (
        (0.11, 0.025),  # the shortest path and the flattest slope of the data
        (1.456944, 0.0095),  # Roussel et al. (2005): 4,780 ft of channel
        (1.55, 0.025),  # WR-D-71-1, the worked example
        (8.2, 0.023),
        (15.88, 0.0114),  # the guide's Kamiennik
        (28.88, 0.105),
    )
    with localcontext(prec=_DIGITS):
        for length_km, slope in points:
            exact = _kirpich_decimal(length_km, _exact(slope))
            assert_within(
                run(length_km=length_km, slope_m_per_m=slope).real("tc_min"),
                float(exact),
                rel=1e-13,
                reason=_ORACLE_REASON,
            )


def _kirpich_scaling(run: Callable[..., Values]) -> None:
    base = {"length_km": 3.0, "slope_m_per_m": 0.04}
    _power_law(run, "length_km", base, 0.77)
    _power_law(run, "slope_m_per_m", base, -0.385)


KIRPICH: Final = FormulaSpec(
    name="kirpich",
    title="Time of concentration by Kirpich's formula (Tennessee form)",
    function="hydrolog.time.concentration.ConcentrationTime.kirpich",
    family="empirical",
    equation="tc = 0.0078 * L**0.77 * S**-0.385 [min], L in ft (L[km] by the exact "
    "foot), S in m/m",
    latex=r"t_c = 0.0078\,L^{0.77}\,S^{-0.385},\quad L\ \mathrm{[ft]}",
    variables=(
        _flow_path_length(
            Range(
                low=0.10668,
                high=1.2192,
                source=Source(
                    citation=_MOTA,
                    locator="p. 58: the data of Kirpich (1940), table 1, give the "
                    "range of the formula, L between 350 and 4,000 ft",
                    url=_MOTA_URL,
                ),
            )
        ),
        Variable(
            name="slope_m_per_m",
            symbol="S",
            unit="m/m",
            description="Slope of the longest flow path: the elevation of its head "
            "minus the outlet's, over its length.",
            physical=_SLOPE,
            applicability=Range(
                low=0.025,
                high=0.1,
                source=Source(
                    citation=_MOTA,
                    locator="p. 58: the data of Kirpich (1940), table 1, give the "
                    "range of the formula, S from 0.025 to 0.1",
                    url=_MOTA_URL,
                ),
            ),
            typical=_FLOW_PATH_SLOPE_TYPICAL,
        ),
    ),
    outputs=(_tc_output(),),
    sources=(
        Source(
            citation=_FANG,
            locator="eq. 3.14, p. 22 (L the channel length to the most remote point, "
            "S its drop over L)",
            url=_FANG_URL,
        ),
        Source(
            citation=_ROUSSEL,
            locator="eq. 7, p. 7; supplement, p. 29 (K = 0.0078 for feet)",
            url=_ROUSSEL_URL,
        ),
        Source(
            citation=_MOTA,
            locator="pp. 56-58: Kirpich's curves and data of 1940, table 1; the "
            "formula published by Rowe and Thomas (1942)",
            url=_MOTA_URL,
        ),
        Source(citation=_FDOT, locator="eq. 2.2-9", url=_FDOT_URL),
    ),
    constants=(
        Constant(
            name="kirpich_coefficient",
            value=0.0078,
            unit="min ft^-0.77",
            symbol="0.0078",
            source=Source(
                citation=_FANG,
                locator="eq. 3.14, p. 22; the same in Roussel et al. (2005) eq. 7, "
                "Mota and Kobiyama (2015) and FDOT (2024) eq. 2.2-9",
                url=_FANG_URL,
            ),
        ),
        Constant(
            name="kirpich_length_exponent",
            value=0.77,
            unit="-",
            symbol="0.77",
            source=Source(
                citation=_FANG,
                locator="eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024)",
                url=_FANG_URL,
            ),
        ),
        Constant(
            name="kirpich_slope_exponent",
            value=-0.385,
            unit="-",
            symbol="-0.385",
            source=Source(
                citation=_FANG,
                locator="eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024)",
                url=_FANG_URL,
            ),
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"length_km": 1, "slope_m_per_m": -1},
        limits=(
            Limit(
                name="source_units",
                text="tc equals the SI form 0.0078 (1/0.3048)^0.77 L[m]^0.77 "
                "S^-0.385 evaluated in decimal arithmetic at 50 digits",
                check=_kirpich_oracle,
            ),
            Limit(
                name="power_law",
                text="doubling L multiplies tc by 2^0.77, doubling S by 2^-0.385",
                check=_kirpich_scaling,
            ),
        ),
    ),
    validation=(
        "Kirpich (1940) published curves of six basins of Ramser (1927) near Jackson, "
        "Tennessee (basin 2 of seven excluded), not the formula; Mota and Kobiyama "
        "(2015, pp. 57-58) find their own fit to those data 2 to 9 % from the formula "
        "within L of 350-4,000 ft and S of 0.025-0.1, up to 30 % outside"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "the Tennessee form in its source units: L in feet by the exact 0.3048 "
            "m/ft of the units table, tc in minutes; the SI constants 0.0195 (L in m; "
            "Roussel et al. 2005, TxDOT 2019) and 0.01947 (WR-D-71-1, 2023) round "
            "0.0078 (1/0.3048)^0.77 = 0.019472, and Hydrolog's 3.981 (L in km) up to "
            "0.8.1 was 0.136 % above the exact 3.97560"
        ),
        (
            "L along the watercourse from the outlet to the most remote point of the "
            "watershed, the longest flow path, and S the drop between its two ends "
            "over L (Fang et al. 2005, eq. 3.14), neither the channel to its head nor "
            "the mean slope of the watershed; Kirpich (1940) measured L to the "
            "highest point of the basin (Mota and Kobiyama 2015, p. 56)"
        ),
        "S in m/m (ft/ft), not in percent",
        (
            "no low-slope offset in the formula alone; Kerby-Kirpich offsets its "
            "channel part (Cleveland et al. 2012)"
        ),
    ),
    assumptions=(
        (
            "small rural basins with defined channels, 1.25-112 acres (0.005-0.45 "
            "km2, checked by WatershedParameters.calculate_tc), so mostly channel "
            "flow; Kirpich applied it up to about 200 acres (Roussel et al. 2005, "
            "p. 5); the factors 0.4 for overland flow on concrete or asphalt and 0.2 "
            "for concrete channels of US practice (Fang et al. 2005, p. 22) are not "
            "applied"
        ),
        (
            "Hydrograf's watersheds (flow paths of 0.05-30 km) lie mostly outside "
            "Kirpich's data (0.107-1.22 km): their results are extrapolations, with "
            "the notice"
        ),
    ),
    traps={
        "singular_at_bound": "range cases slope_m_per_m-physical_low_*: tc grows "
        "without bound as S tends to 0 (S^-0.385) and stays finite down to the "
        "smallest positive float; a slope of 0 is refused",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the SI form with the unrounded constant 0.0078 "
            "(1/0.3048)^0.77, evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_tc.py (limit source_units)",
        ),
    ),
)

# --- NRCS watershed lag ---------------------------------------------------------------


def _nrcs_min(length_km: float, slope_m_per_m: float, cn: float) -> float:
    """NEH 630-15 eq. 15-4b [h] in feet, inches and percent, returned in minutes."""
    length_ft = convert(length_km, "km", "ft")
    retention_in = NRCS.constant("s_scale") / cn - NRCS.constant("s_offset")
    slope_pct = NRCS.constant("percent") * slope_m_per_m
    tc_h = float(
        length_ft ** NRCS.constant("length_exponent")
        * (retention_in + NRCS.constant("retention_shift"))
        ** NRCS.constant("retention_exponent")
        / (NRCS.constant("tc_denominator") * math.sqrt(slope_pct))
    )
    return convert(tc_h, "h", "min")


def _nrcs_oracle(run: Callable[..., Values]) -> None:
    points = (
        (1.178052, 0.0479, 63.0),  # NEH 630-15, the example of the lag method
        (8.2, 0.023, 72.0),
        (15.88, 0.082, 65.0),  # the guide's Kamiennik
        (0.05, 0.19, 95.0),
        (28.88, 0.04, 50.0),
        (3.0, 0.1, 100.0),
    )
    with localcontext(prec=_DIGITS):
        # The metric form with S in mm (NEH 630-10 eq. 10-13): 7068.86 unrounded
        denominator = (
            Decimal(1900) * _FOOT_M ** Decimal("0.8") * _INCH_MM ** Decimal("0.7")
        )
        for length_km, slope, cn in points:
            retention_mm = Decimal(25400) / _exact(cn) - 254
            length_m = _exact(length_km) * 1000
            exact = (
                100
                * length_m ** Decimal("0.8")
                * (retention_mm + _INCH_MM) ** Decimal("0.7")
                / (denominator * (100 * _exact(slope)).sqrt())
            )
            assert_within(
                run(length_km=length_km, slope_m_per_m=slope, cn=cn).real("tc_min"),
                float(exact),
                rel=1e-13,
                reason=_ORACLE_REASON,
            )


def _nrcs_scaling(run: Callable[..., Values]) -> None:
    base = {"length_km": 3.0, "slope_m_per_m": 0.05, "cn": 70.0}
    _power_law(run, "length_km", base, 0.8)
    _power_law(run, "slope_m_per_m", base, -0.5)


def _neh(locator: str) -> Source:
    return Source(citation=_NEH630_15, locator=locator, url=_NEH630_15_URL)


NRCS: Final = FormulaSpec(
    name="nrcs",
    title="Time of concentration by the NRCS watershed lag equation (Mockus 1961)",
    function="hydrolog.time.concentration.ConcentrationTime.nrcs",
    family="empirical",
    equation=(
        "tc = l**0.8 * (S + 1)**0.7 / (1140 * Y**0.5) [h], l in ft, S = 1000 / CN - "
        "10 in, Y = 100 * slope in percent; the lag is 0.6 tc"
    ),
    latex=(
        r"T_c = \frac{\ell^{0.8}\,(S + 1)^{0.7}}{1140\,Y^{0.5}},\quad "
        r"S = \frac{1000}{CN} - 10,\quad \ell\ \mathrm{[ft]},\ S\ \mathrm{[in]},\ "
        r"Y\ [\%]"
    ),
    variables=(
        Variable(
            name="length_km",
            symbol=r"\ell",
            unit="km",
            description="Flow length: the longest path along which water flows from "
            "the watershed divide to the outlet.",
            physical=_LENGTH,
            applicability="unstated",
            typical=_FLOW_PATH_TYPICAL,
        ),
        Variable(
            name="slope_m_per_m",
            symbol="Y",
            unit="m/m",
            description="Average land slope of the watershed, not the slope of the "
            "flow path.",
            physical=_SLOPE,
            applicability="unstated",
            typical=Range(
                low=0.04,
                high=0.19,
                source=_from_handoffs("mean land slopes of 0.0500 to 0.1831 m/m"),
            ),
        ),
        Variable(
            name="cn",
            symbol="CN",
            unit="-",
            description="Curve number of AMC II, the surrogate of the retardance "
            "factor cn'.",
            physical=Range(low=1.0, high=100.0),
            applicability=Range(
                low=50.0,
                high=95.0,
                source=_neh(
                    "p. 15-6: a CN of less than 50, or greater than 95 should not be "
                    "used in the solution of equations 15-4a and 15-4b (Mockus 1961)"
                ),
            ),
            typical=Range(low=51.8, high=81.4, source=_HYDROGRAF_CATCHMENTS),
        ),
    ),
    outputs=(_tc_output(),),
    sources=(
        _neh(
            "eqs. 15-3, 15-4a and 15-4b and their variables, pp. 15-3 to 15-6; the "
            "example of the lag method, p. 15-12"
        ),
        _NEH630_F,
    ),
    constants=(
        Constant(
            name="tc_denominator",
            value=1140.0,
            unit="ft^0.8 in^0.7 h^-1 %^0.5",
            symbol="1140",
            source=_neh("eq. 15-4b, p. 15-5: eq. 15-4a (1,900) with L = 0.6 Tc"),
        ),
        Constant(
            name="length_exponent",
            value=0.8,
            unit="-",
            symbol="0.8",
            source=_neh("eqs. 15-4a and 15-4b, p. 15-5"),
        ),
        Constant(
            name="retention_exponent",
            value=0.7,
            unit="-",
            symbol="0.7",
            source=_neh("eqs. 15-4a and 15-4b, p. 15-5"),
        ),
        Constant(
            name="retention_shift",
            value=1.0,
            unit="in",
            symbol="1",
            source=_neh("eqs. 15-4a and 15-4b, p. 15-5: S + 1"),
        ),
        Constant(
            name="s_scale",
            value=1000.0,
            unit="in",
            symbol="1000",
            source=_neh("p. 15-5: S = 1,000 / cn' - 10"),
        ),
        Constant(
            name="s_offset",
            value=10.0,
            unit="in",
            symbol="10",
            source=_neh("p. 15-5: S = 1,000 / cn' - 10"),
        ),
        Constant(
            name="percent",
            value=100.0,
            unit="% per m/m",
            symbol="100",
            source=_SI_PERCENT,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"length_km": 1, "slope_m_per_m": -1, "cn": -1},
        limits=(
            Limit(
                name="exact_metric_constant",
                text="tc equals 100 l[m]^0.8 (S[mm] + 25.4)^0.7 / (7068.86 Y^0.5) "
                "with 7068.86 = 1900 0.3048^0.8 25.4^0.7 unrounded, in decimal "
                "arithmetic at 50 digits (TRIAGE T8)",
                check=_nrcs_oracle,
            ),
            Limit(
                name="power_law",
                text="doubling l multiplies tc by 2^0.8, doubling Y by 2^-0.5",
                check=_nrcs_scaling,
            ),
        ),
    ),
    validation=(
        "NEH 630-15 (p. 15-6) reports the equation's data, 24 watersheds of 1.3 acres "
        "to 9.2 square miles, mostly under 2,000 acres (Mockus 1961), and that "
        "Folmar and Miller (2000) found a reasonable upper limit of up to 19 square "
        "miles; table 15-4 shows the lag of one watershed varying from storm to "
        "storm (Jones Falls, Maryland: 4.16 to 6.91 h)"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "eq. 15-4b in its source units: l in feet and S in inches by the exact "
            "0.3048 m/ft and 25.4 mm/in of the units table, Y in percent (100 per "
            "m/m), Tc in hours, converted to minutes; in SI it is 100 l[m]^0.8 "
            "(S[mm] + 25.4)^0.7 / (7068.86 Y^0.5) with 100/7068.86 = 0.0141466, "
            "where Hydrolog up to 0.8.1 used 0.01416 (+0.095 %, TRIAGE T8)"
        ),
        (
            "Tc = lag / 0.6 (eq. 15-3, Mockus 1957; Simas 1996); a unit hydrograph "
            "takes tp = D/2 + 0.6 Tc (USACE HEC-HMS Technical Reference Manual, SCS "
            "unit hydrograph, eqs. 1 and 3); TR-55 (1986) has no lag relation"
        ),
        (
            "l the longest flow path from the divide to the outlet (p. 15-5); Y the "
            "average land slope of the watershed, 'not to be confused with the slope "
            "of the flow path' (p. 15-5)"
        ),
        (
            "the retardance factor cn' is the CN of AMC II (p. 15-6: CN is used as a "
            "surrogate for cn'); S = 0 at CN 100; a fractional CN, a weighted mean, "
            "is used as given"
        ),
    ),
    assumptions=(
        (
            "average natural watershed conditions with an approximately uniform "
            "distribution of runoff (eq. 15-3); the area of the 24 watersheds, "
            "0.005-24 km2, is checked by WatershedParameters.calculate_tc"
        ),
        (
            "Hydrograf's flow paths (0.05-30 km) and the CN of its catchments "
            "(51.8-81.4) lie inside the equation's CN range; a CN below 50 or above "
            "95 gives the notice"
        ),
    ),
    traps={
        "singular_at_bound": "range cases slope_m_per_m-physical_low_*: tc grows as "
        "Y^-0.5 when Y tends to 0 and stays finite down to the smallest positive "
        "float; cn-physical_low: CN = 1 gives S = 990 in, finite",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the SI form with S in mm and the unrounded 1900 "
            "0.3048^0.8 25.4^0.7, evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_tc.py (limit exact_metric_constant)",
        ),
    ),
)

# --- Giandotti ------------------------------------------------------------------------


def _giandotti_min(area_km2: float, length_km: float, elevation_diff_m: float) -> float:
    tc_h = (
        GIANDOTTI.constant("area_factor") * math.sqrt(area_km2)
        + GIANDOTTI.constant("length_factor") * length_km
    ) / (GIANDOTTI.constant("height_factor") * math.sqrt(elevation_diff_m))
    return convert(tc_h, "h", "min")


def _giandotti_oracle(run: Callable[..., Values]) -> None:
    points = (
        (123.3, 29.6, 226.0),  # Michailidi et al. (2018), table 3, Rafina
        (37.22, 14.78, 105.9),  # the guide's Kamiennik
        (1853.6, 59.4, 381.0),
        (0.00035, 0.0071, 2.89),
    )
    with localcontext(prec=_DIGITS):
        for area, length, height in points:
            # In minutes at once: 60 / 0.8 = 75
            exact = (
                75
                * (4 * _exact(area).sqrt() + Decimal("1.5") * _exact(length))
                / _exact(height).sqrt()
            )
            got = run(area_km2=area, length_km=length, elevation_diff_m=height)
            assert_within(
                got.real("tc_min"), float(exact), rel=1e-14, reason=_ORACLE_REASON
            )


def _giandotti_height(run: Callable[..., Values]) -> None:
    base = {"area_km2": 200.0, "length_km": 20.0, "elevation_diff_m": 300.0}
    once = run(**base).real("tc_min")
    quadrupled = run(**{**base, "elevation_diff_m": 1200.0}).real("tc_min")
    assert_within(
        quadrupled / once,
        0.5,
        rel=1e-15,
        reason="tc is proportional to H^-0.5: four times H halves it, within the "
        "rounding of two square roots",
    )


GIANDOTTI: Final = FormulaSpec(
    name="giandotti",
    title="Time of concentration by Giandotti's formula (1934)",
    function="hydrolog.time.concentration.ConcentrationTime.giandotti",
    family="empirical",
    equation="tc = (4 * A**0.5 + 1.5 * L) / (0.8 * H**0.5) [h]",
    latex=r"t_c = \frac{4\sqrt{A} + 1.5\,L}{0.8\sqrt{H}}",
    variables=(
        Variable(
            name="area_km2",
            symbol="A",
            unit="km2",
            description="Area of the watershed.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0e6,
                test_reason="a million km2, more than ten times the largest basin of "
                "the formula's data (70,000 km2)",
            ),
            applicability=Range(low=170.0, high=70000.0, source=_ALMEIDA),
            typical=Range(
                low=0.0003,
                high=250.0,
                source=Source(
                    citation=_HANDOFFS,
                    locator=f"{_HANDOFF_FILES}: areas of 0.00035 to 135 km2; "
                    "Hydrograf computes hydrographs of watersheds up to 250 km2 "
                    "(backend/api/endpoints/hydrograph.py)",
                ),
            ),
        ),
        Variable(
            name="length_km",
            symbol="L",
            unit="km",
            description="Length of the main channel.",
            physical=_LENGTH,
            applicability="unstated",
            typical=Range(
                low=0.007,
                high=27.0,
                source=_from_handoffs("main channels of 0.0071 to 26.18 km"),
            ),
        ),
        Variable(
            name="elevation_diff_m",
            symbol="H",
            unit="m",
            description="Mean elevation of the watershed above the outlet.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=8849.0,
                test_reason="the height of Mount Everest above sea level: no mean "
                "elevation lies higher above its outlet",
            ),
            applicability="unstated",
            typical=Range(
                low=2.5,
                high=210.0,
                source=_from_handoffs(
                    "mean elevations of 2.89 to 204 m above the outlet"
                ),
            ),
        ),
    ),
    outputs=(_tc_output(),),
    sources=(
        _ADBPO,
        Source(
            citation=_MICHAILIDI,
            locator="table 2 (the formula), table 3 (30 basins)",
            url=_MICHAILIDI_URL,
        ),
        _ALMEIDA,
    ),
    constants=(
        Constant(
            name="area_factor",
            value=4.0,
            unit="h km^-1 m^0.5",
            symbol="4",
            source=_ADBPO,
        ),
        Constant(
            name="length_factor",
            value=1.5,
            unit="h km^-1 m^0.5",
            symbol="1.5",
            source=_ADBPO,
        ),
        Constant(
            name="height_factor",
            value=0.8,
            unit="-",
            symbol="0.8",
            source=_ADBPO,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"area_km2": 1, "length_km": 1, "elevation_diff_m": -1},
        limits=(
            Limit(
                name="decimal",
                text="tc equals 75 (4 A^0.5 + 1.5 L) / H^0.5 minutes evaluated in "
                "decimal arithmetic at 50 digits",
                check=_giandotti_oracle,
            ),
            Limit(
                name="height",
                text="four times H halves tc",
                check=_giandotti_height,
            ),
        ),
    ),
    validation="none reported by the open sources (Giandotti 1934 is not open)",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "A in km2, L in km and H in m as the sources print it, tc in hours "
            "converted to minutes"
        ),
        (
            "H the mean elevation of the watershed minus the elevation of the outlet, "
            "neither the relief (maximum minus minimum) nor the mean elevation itself"
        ),
        (
            "L the main channel, the field channel_length_km, after Grimaldi et al. "
            "(2012, eq. 5); the Autorità di bacino del Po (2001, §6.1: 'percorso "
            "idraulicamente più lungo') and Michailidi et al. (2018) take the longest "
            "flow path, longer by the overland segment (Kamiennik: 14.78 against "
            "15.88 km, +3.5 % in tc)"
        ),
    ),
    assumptions=(
        (
            "basins of central and northern Italy of 170-70,000 km2 (Almeida et al. "
            "2014, table 1); Hydrograf's watersheds, up to 250 km2, lie mostly below "
            "that range: their results are extrapolations, with the notice"
        ),
    ),
    traps={
        "singular_at_bound": "range cases elevation_diff_m-physical_low_*: tc grows "
        "as H^-0.5 when H tends to 0 (a flat watershed) and stays finite; H = 0 is "
        "refused",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the formula in minutes, 75 (4 A^0.5 + 1.5 L) / H^0.5, "
            "evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_tc.py (limit decimal)",
        ),
    ),
)

# --- FAA ------------------------------------------------------------------------------


def _faa_min(length_km: float, slope_m_per_m: float, runoff_coeff: float) -> float:
    """AC 150/5320-5B fig. 7 [min] in feet and percent."""
    length_ft = convert(length_km, "km", "ft")
    slope_pct = FAA.constant("percent") * slope_m_per_m
    return (
        FAA.constant("faa_coefficient")
        * (FAA.constant("c_offset") - runoff_coeff)
        * math.sqrt(length_ft)
        / math.cbrt(slope_pct)
    )


def _faa_oracle(run: Callable[..., Values]) -> None:
    points = (
        (0.045, 0.02, 0.18),  # INDOT, example 29-7.4
        (0.15, 0.02, 0.6),
        (0.3, 0.082, 0.25),  # the guide's Kamiennik
        (0.7, 0.005, 0.95),
        (0.04, 0.19, 1.0),
    )
    with localcontext(prec=_DIGITS):
        # The SI form in minutes with the constant unrounded: 1.8 (1000/0.3048)^0.5
        # / 100^(1/3) for L in km and S in m/m (22.2125)
        constant = (
            Decimal("1.8") * (1000 / _FOOT_M).sqrt() / Decimal(100) ** (Decimal(1) / 3)
        )
        for length, slope, c in points:
            exact = (
                constant
                * (Decimal("1.1") - _exact(c))
                * _exact(length).sqrt()
                / _exact(slope) ** (Decimal(1) / 3)
            )
            got = run(length_km=length, slope_m_per_m=slope, runoff_coeff=c)
            assert_within(
                got.real("tc_min"), float(exact), rel=1e-13, reason=_ORACLE_REASON
            )


def _faa_runoff_coefficient(run: Callable[..., Values]) -> None:
    base = {"length_km": 0.2, "slope_m_per_m": 0.02}
    half = run(**base, runoff_coeff=0.6).real("tc_min")
    whole = run(**base, runoff_coeff=0.1).real("tc_min")
    assert_within(
        whole / half,
        2.0,
        rel=1e-15,
        reason="tc is proportional to 1.1 - C: C = 0.1 gives twice the time of "
        "C = 0.6, within the rounding of 1.1 - C",
    )


FAA: Final = FormulaSpec(
    name="faa",
    title="Overland flow time by the FAA formula (AC 150/5320-5B, 1970)",
    function="hydrolog.time.concentration.ConcentrationTime.faa",
    family="empirical",
    equation=(
        "T = 1.8 * (1.1 - C) * D**0.5 / S**(1/3) [min], D in ft, S in percent "
        "(100 * slope)"
    ),
    latex=r"T = \frac{1.8\,(1.1 - C)\,\sqrt{D}}{\sqrt[3]{S}},\quad D\ \mathrm{[ft]},"
    r"\ S\ [\%]",
    variables=(
        _overland_length("length_km", None),
        _overland_slope("slope_m_per_m", None),
        Variable(
            name="runoff_coeff",
            symbol="C",
            unit="-",
            description="Runoff coefficient of the rational method.",
            physical=Range(low=0.0, low_inclusive=False, high=1.0),
            applicability=Range(
                low=0.0,
                high=0.95,
                source=Source(
                    citation=_FAA,
                    locator="table I, p. 10: the values of factor C, 0.00 to 0.95",
                    url=_FAA_URL,
                ),
            ),
            typical=Range(low=0.05, high=0.95, source=_FAA_TABLE_USE),
        ),
    ),
    outputs=(_tc_output(),),
    sources=(
        Source(
            citation=_FAA,
            locator="chapter 3, §6, figure 7 'Surface flow time curves', p. 11; table "
            "I, p. 10",
            url=_FAA_URL,
        ),
    ),
    constants=(
        Constant(
            name="faa_coefficient",
            value=1.8,
            unit="min ft^-0.5 %^(1/3)",
            symbol="1.8",
            source=Source(citation=_FAA, locator="figure 7, p. 11", url=_FAA_URL),
        ),
        Constant(
            name="c_offset",
            value=1.1,
            unit="-",
            symbol="1.1",
            source=Source(citation=_FAA, locator="figure 7, p. 11", url=_FAA_URL),
        ),
        Constant(
            name="percent",
            value=100.0,
            unit="% per m/m",
            symbol="100",
            source=_SI_PERCENT,
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"length_km": 1, "slope_m_per_m": -1, "runoff_coeff": -1},
        limits=(
            Limit(
                name="decimal",
                text="T equals 1.8 (1000/0.3048)^0.5 / 100^(1/3) (1.1 - C) L[km]^0.5 "
                "S[m/m]^(-1/3) evaluated in decimal arithmetic at 50 digits",
                check=_faa_oracle,
            ),
            Limit(
                name="runoff_coefficient",
                text="T is proportional to 1.1 - C",
                check=_faa_runoff_coefficient,
            ),
        ),
    ),
    validation="none reported by the source",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "figure 7 in its source units: D in feet by the exact 0.3048 m/ft of the "
            "units table, S in percent (100 per m/m; the curves are labelled in "
            "percent), T in minutes; Hydrolog's 22.213 for L in km and S in m/m up "
            "to 0.8.1 rounded 22.2125"
        ),
        (
            "the inlet time: overland flow 'from the most remote point in the "
            "drainage subarea to the inlet' (§6b), not the time of concentration of "
            "a watershed with a channel"
        ),
        (
            "C of table I in (0, 1]: C = 0, which the table lists for moderately "
            "pervious soils with turf (0.00-0.10), is refused"
        ),
    ),
    assumptions=(
        (
            "'Use the formula for distances in excess of 800 feet' (figure 7): the "
            "curves end at 800 ft and the formula serves longer paths; the later "
            "circulars AC 150/5320-5C (2006) and 5D (2013) time the flow with the "
            "NRCS segment method instead"
        ),
    ),
    traps={
        "singular_at_bound": "range cases slope_m_per_m-physical_low_*: T grows as "
        "S^(-1/3) when S tends to 0 and stays finite; S = 0 is refused",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the SI form with the unrounded constant 1.8 "
            "(1000/0.3048)^0.5 / 100^(1/3), evaluated with the decimal module at 50 "
            "digits",
            test="tests/unit/test_formulas_tc.py (limit decimal)",
        ),
    ),
)

# --- Kerby ----------------------------------------------------------------------------


def _offset(slope_m_per_m: float) -> float:
    """Return the slope Kerby and Kirpich take: S + 0.0005 below S = 0.002."""
    if slope_m_per_m < KERBY.constant("low_slope_threshold"):
        return slope_m_per_m + KERBY.constant("low_slope_offset")
    return slope_m_per_m


def _kerby_min(length_km: float, slope_m_per_m: float, retardance: float) -> float:
    """Kerby's tc [min] of checked inputs, in the source's feet, with the offset."""
    length_ft = convert(length_km, "km", "ft")
    return float(
        (
            KERBY.constant("kerby_coefficient")
            * retardance
            * length_ft
            / math.sqrt(_offset(slope_m_per_m))
        )
        ** KERBY.constant("kerby_exponent")
    )


def _kerby_oracle(run: Callable[..., Values]) -> None:
    points = (
        (0.1524, 0.02, 0.4),  # Roussel et al. (2005), supplement
        (0.1524, 0.0003, 0.4),  # Cleveland et al. (2012): 0.0003 + 0.0005
        (0.2, 0.005, 0.4),  # INDOT, example 29-7.7
        (0.3, 0.082, 0.4),  # the guide's Kamiennik
        (0.04, 0.0019999, 0.02),
        (0.7, 0.19, 0.8),
    )
    with localcontext(prec=_DIGITS):
        for length, slope, retardance in points:
            exact = _kerby_decimal(length, _exact(slope), retardance)
            got = run(length_km=length, slope_m_per_m=slope, retardance=retardance)
            assert_within(
                got.real("tc_min"), float(exact), rel=1e-13, reason=_ORACLE_REASON
            )


def _kerby_step(run: Callable[..., Values]) -> None:
    threshold = KERBY.constant("low_slope_threshold")
    below = run(slope_m_per_m=math.nextafter(threshold, 0.0)).real("tc_min")
    at = run(slope_m_per_m=threshold).real("tc_min")
    assert_within(
        at / below,
        1.25 ** (0.467 / 2),
        rel=1e-12,
        reason="the offset dropped at S = 0.002 turns S + 0.0005 = 0.0025 into 0.002: "
        "tc rises by (0.0025/0.002)^0.2335, within the rounding of two evaluations "
        "and of the float just below 0.002",
    )


def _kerby_scaling(run: Callable[..., Values]) -> None:
    base = {"length_km": 0.1, "slope_m_per_m": 0.005, "retardance": 0.4}
    _power_law(run, "length_km", base, 0.467)
    _power_law(run, "retardance", base, 0.467)


def _cleveland(locator: str) -> Source:
    return Source(citation=_CLEVELAND, locator=locator, url=_CLEVELAND_URL)


_KERBY_CONSTANTS = (
    Constant(
        name="kerby_coefficient",
        value=0.67,
        unit="min^(1/0.467) ft^-1",
        symbol="0.67",
        source=Source(
            citation=_FANG,
            locator="eq. 3.12, p. 22, (0.67 N L / S^0.5)^0.467 with L in ft; the same "
            "in Roussel et al. (2005) eq. 3",
            url=_FANG_URL,
        ),
    ),
    Constant(
        name="kerby_exponent",
        value=0.467,
        unit="-",
        symbol="0.467",
        source=Source(
            citation=_FANG,
            locator="eq. 3.12, p. 22; INDOT eq. 29-7.14 and TxDOT (2019) take the "
            "same exponent of L N",
            url=_FANG_URL,
        ),
    ),
    Constant(
        name="low_slope_threshold",
        value=0.002,
        unit="m/m",
        symbol="0.002",
        source=_cleveland(
            "low slope procedures, step 2(c), p. 2: a main channel slope less than "
            "0.002 is low slope; TxDOT (2019), section 11"
        ),
    ),
    Constant(
        name="low_slope_offset",
        value=0.0005,
        unit="m/m",
        symbol="0.0005",
        source=_cleveland(
            "step 3 and eq. 1, p. 2: S_low slope = S0 + 0.0005; TxDOT (2019), section "
            "11"
        ),
    ),
)

KERBY: Final = FormulaSpec(
    name="kerby",
    title="Overland flow time by Kerby's formula (1959)",
    function="hydrolog.time.concentration.ConcentrationTime.kerby",
    family="empirical",
    equation=(
        "tc = (0.67 * N * L / S**0.5)**0.467 [min], L in ft; S + 0.0005 for S below "
        "0.002"
    ),
    latex=(
        r"t_c = \left(\frac{0.67\,N\,L}{\sqrt{S}}\right)^{0.467},\quad L\ "
        r"\mathrm{[ft]},\quad S \to S + 0.0005\ \text{for}\ S < 0.002"
    ),
    variables=(
        _overland_length("length_km", _KERBY_LENGTH),
        _overland_slope(
            "slope_m_per_m",
            Range(
                low=0.0,
                high=0.01,
                source=Source(
                    citation=_ROUSSEL,
                    locator="p. 5: the watersheds of Kerby (1959) have dimensionless "
                    "slopes less than 0.01",
                    url=_ROUSSEL_URL,
                ),
            ),
        ),
        _retardance(),
    ),
    outputs=(_tc_output(),),
    sources=(
        Source(citation=_FANG, locator="eq. 3.12 and table 3.3, p. 22", url=_FANG_URL),
        Source(
            citation=_ROUSSEL,
            locator="eq. 3, p. 5; supplement, p. 29 (the form K (L N)^0.467 S^-0.235)",
            url=_ROUSSEL_URL,
        ),
        _INDOT,
        _cleveland("low slope procedures and eq. 2, pp. 1-2"),
    ),
    constants=_KERBY_CONSTANTS,
    properties=Properties(
        units="unit_specific",
        monotonic={"length_km": 1, "retardance": 1},
        limits=(
            Limit(
                name="decimal",
                text="tc equals (0.67/0.3048)^0.467 (L[m] N)^0.467 S^(-0.467/2) with "
                "the offset, evaluated in decimal arithmetic at 50 digits",
                check=_kerby_oracle,
            ),
            Limit(
                name="low_slope_step",
                text="tc rises by 1.25^0.2335 - 1 = 5.35 % as S reaches 0.002 from "
                "below and the offset is dropped: not monotonic in S",
                check=_kerby_step,
            ),
            Limit(
                name="power_law",
                text="doubling L or N multiplies tc by 2^0.467",
                check=_kerby_scaling,
            ),
        ),
    ),
    validation="none reported by the open sources (Kerby 1959 is not open)",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "Kerby's form in its source units: L in feet by the exact 0.3048 m/ft of "
            "the units table, tc in minutes; the forms K (L N)^0.467 S^-0.235 of "
            "TxDOT (K 0.828 for ft, 1.44 for m) round 0.67^0.467 and the exponent "
            "0.467/2 = 0.2335; Hydrolog's 36.37 for L in km up to 0.8.1 rounded "
            "36.3699"
        ),
        (
            "N Kerby's retardance of the overland surface (Roussel et al. 2005, "
            "supplement, p. 29), not Manning's n; NEH 630-15 appendix 15A eq. 15A-2 "
            "prints (2.2 n l / S^0.5)^0.324, a misprint of this formula"
        ),
        (
            "the low-slope offset of Cleveland et al. (2012, eqs. 1-2): a slope "
            "below 0.002 is taken as S + 0.0005; the formula alone decides it by its "
            "own slope, where Cleveland et al. decide by the main-channel slope, "
            "which overland flow alone does not have; at 0.002 the offset is "
            "dropped, so tc rises by 5.35 % as S reaches 0.002 from below and is "
            "monotonic in S only on each side of 0.002"
        ),
    ),
    assumptions=(
        (
            "Kerby's data: watersheds below 10 acres (0.04 km2, checked by "
            "WatershedParameters.calculate_tc), overland flow up to 1,200 ft, "
            "slopes below 1 %, N up to 0.8 (Roussel et al. 2005, p. 5); overland "
            "(sheet) flow only"
        ),
        (
            "N from Kerby's table (Roussel et al. 2005, supplement, p. 29): pavement "
            "0.02; smooth, bare, packed soil 0.10; poor grass, cultivated row crops "
            "or moderately rough packed surfaces 0.20; pasture, average grass 0.40; "
            "deciduous forest 0.60; dense grass, coniferous forest or deciduous "
            "forest with deep litter 0.80"
        ),
        (
            "Hydrograf's overland segments (0.04-0.7 km at 0.005-0.19 m/m) are "
            "mostly steeper than Kerby's data: their results are extrapolations, "
            "with the notice"
        ),
    ),
    traps={
        "singular_at_bound": "range cases slope_m_per_m-physical_low_*: the offset "
        "keeps tc finite as S tends to 0 (S + 0.0005); a slope of 0 is refused",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the SI form (0.67/0.3048)^0.467 (L[m] N)^0.467 "
            "S^(-0.467/2) with the offset, evaluated with the decimal module at 50 "
            "digits",
            test="tests/unit/test_formulas_tc.py (limit decimal)",
        ),
    ),
)

# --- Kerby-Kirpich --------------------------------------------------------------------


def _kerby_kirpich_oracle(run: Callable[..., Values]) -> None:
    points = (
        # Roussel et al. (2005), supplement: 500 ft at 2 % and one mile at 50 ft
        (0.1524, 0.02, 0.4, 1.609344, 0.0095),
        # Cleveland et al. (2012): both slopes below 0.002, both offset
        (0.1524, 0.0003, 0.4, 1.609344, 0.00021),
        # A flat main channel under a steeper overland segment: Hydrolog offsets the
        # channel only, Cleveland et al. both segments (the stated deviation)
        (0.2, 0.02, 0.4, 5.0, 0.001),
        # A steep main channel under a flat overland segment: Hydrolog offsets the
        # overland part only, Cleveland et al. neither
        (0.2, 0.001, 0.4, 5.0, 0.01),
        (0.3, 0.082, 0.4, 15.88, 0.0114),  # the guide's Kamiennik
    )
    with localcontext(prec=_DIGITS):
        for length_ov, slope_ov, retardance, length_fp, slope_fp in points:
            channel_km = _exact(length_fp) - _exact(length_ov)
            per_metre = Decimal("0.0078") * (1 / _FOOT_M) ** Decimal("0.77")
            channel = (
                per_metre
                * (channel_km * 1000) ** Decimal("0.77")
                * _with_offset(_exact(slope_fp)) ** Decimal("-0.385")
            )
            exact = _kerby_decimal(length_ov, _exact(slope_ov), retardance) + channel
            got = run(
                overland_length_km=length_ov,
                overland_slope_m_per_m=slope_ov,
                retardance=retardance,
                flow_path_length_km=length_fp,
                flow_path_slope_m_per_m=slope_fp,
            )
            assert_within(
                got.real("tc_min"),
                float(exact),
                rel=1e-13,
                reason=_ORACLE_REASON + "; the channel length is the difference of "
                "two exact floats, rounded once",
            )


def _kerby_kirpich_step(run: Callable[..., Values]) -> None:
    threshold = KERBY.constant("low_slope_threshold")
    base = {
        "overland_length_km": 0.3,
        "overland_slope_m_per_m": 0.05,
        "retardance": 0.4,
        "flow_path_length_km": 10.0,
    }
    overland = run(**base, flow_path_slope_m_per_m=threshold).real("tc_min")
    below = run(**base, flow_path_slope_m_per_m=math.nextafter(threshold, 0.0))
    at = run(**base, flow_path_slope_m_per_m=threshold)
    channel_below = below.real("tc_min") - _kerby_min(0.3, 0.05, 0.4)
    channel_at = overland - _kerby_min(0.3, 0.05, 0.4)
    assert_within(
        channel_at / channel_below,
        1.25**0.385,
        rel=1e-12,
        reason="the channel part rises by (0.0025/0.002)^0.385 as the flow path slope "
        "reaches 0.002 and the offset is dropped; a difference of sums of two "
        "evaluations",
    )
    assert at.real("tc_min") > below.real("tc_min")


KERBY_KIRPICH: Final = FormulaSpec(
    name="kerby_kirpich",
    title="Time of concentration by the Kerby-Kirpich method (Roussel et al. 2005)",
    function="hydrolog.time.concentration.ConcentrationTime.kerby_kirpich",
    family="empirical",
    equation=(
        "tc = kerby(L_ov, S_ov, N) + kirpich(L_fp - L_ov, S_fp) [min], each slope "
        "below 0.002 taken as S + 0.0005"
    ),
    latex=(
        r"t_c = \left(\frac{0.67\,N\,L_{ov}}{\sqrt{S_{ov}}}\right)^{0.467} + "
        r"0.0078\,(L_{fp} - L_{ov})^{0.77}\,S_{fp}^{-0.385},\quad L\ \mathrm{[ft]}"
    ),
    variables=(
        _overland_length("overland_length_km", _KERBY_LENGTH),
        _overland_slope("overland_slope_m_per_m", None),
        _retardance(),
        Variable(
            name="flow_path_length_km",
            symbol="L_{fp}",
            unit="km",
            description="Length of the main channel as the method defines it: the "
            "longest flow path from the divide to the outlet, the overland segment "
            "included.",
            physical=_LENGTH,
            applicability=Range(
                low=1.6,
                high=80.0,
                source=Source(
                    citation=_ROUSSEL,
                    locator="supplement, p. 29: main channel lengths of the 92 Texas "
                    "watersheds approximately 1 to 50 miles, from the outlet to the "
                    "divide",
                    url=_ROUSSEL_URL,
                ),
            ),
            typical=_FLOW_PATH_TYPICAL,
        ),
        Variable(
            name="flow_path_slope_m_per_m",
            symbol="S_{fp}",
            unit="m/m",
            description="Slope of that path: the elevation of its head minus the "
            "outlet's, over its length.",
            physical=_SLOPE,
            applicability=Range(
                low=0.002,
                high=0.02,
                source=Source(
                    citation=_ROUSSEL,
                    locator="supplement, p. 29: dimensionless main channel slopes "
                    "approximately 0.002 to 0.02, from the divide to the outlet",
                    url=_ROUSSEL_URL,
                ),
            ),
            typical=_FLOW_PATH_SLOPE_TYPICAL,
        ),
    ),
    outputs=(_tc_output(),),
    sources=(
        Source(
            citation=_ROUSSEL,
            locator="supplement 'Guidance for estimation of time of concentration in "
            "Texas', pp. 29-30, and its example",
            url=_ROUSSEL_URL,
        ),
        Source(citation=_TXDOT, locator="eqs. 4-13 to 4-15", url=_TXDOT_URL),
        _cleveland("low slope procedures, eqs. 1-3, pp. 1-3, and its example"),
    ),
    constants=(*_KERBY_CONSTANTS, *KIRPICH.constants),
    constraints=(
        Constraint(
            name="flow_path_longer_than_overland",
            cls="physical",
            check=lambda x: (
                x.real("flow_path_length_km") > x.real("overland_length_km")
            ),
            text="flow_path_length_km > overland_length_km",
            source=Source(
                citation=_ROUSSEL,
                locator="supplement, p. 30: the subtraction of the overland flow "
                "length from the overall main-channel length (watershed divide to "
                "outlet) is necessary",
                url=_ROUSSEL_URL,
            ),
            satisfied={"overland_length_km": 0.3, "flow_path_length_km": 15.88},
            boundary={"overland_length_km": 0.3, "flow_path_length_km": 0.3},
            boundary_holds=False,
            violated={"overland_length_km": 0.3, "flow_path_length_km": 0.29},
        ),
    ),
    properties=Properties(
        units="unit_specific",
        monotonic={"retardance": 1, "flow_path_length_km": 1},
        limits=(
            Limit(
                name="decimal",
                text="tc equals Kerby on the overland segment plus Kirpich on the "
                "rest of the flow path, each with its own offset, evaluated in "
                "decimal arithmetic at 50 digits",
                check=_kerby_kirpich_oracle,
            ),
            Limit(
                name="low_slope_step",
                text="the channel part rises by 1.25^0.385 - 1 = 8.97 % as the flow "
                "path slope reaches 0.002 and the offset is dropped",
                check=_kerby_kirpich_step,
            ),
        ),
    ),
    validation=(
        "Roussel et al. (2005, supplement, p. 29) find the Kerby-Kirpich estimates "
        "'consistent with watershed time values independently derived from "
        "real-world storms and runoff hydrographs' of their 92 Texas watersheds"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "tc = t_overland + t_channel: kerby on the overland segment, kirpich on "
            "the channel segment, the flow path minus the overland segment, at the "
            "slope of the whole path from the divide to the outlet (Roussel et al. "
            "2005, supplement, pp. 29-30), in the units and with the constants of "
            "those specs"
        ),
        (
            "a deviation from Cleveland et al. (2012, pp. 1-2): the low-slope offset "
            "(S + 0.0005 below 0.002) is decided for each segment by its own slope, "
            "the overland slope for Kerby and the flow path slope for Kirpich, while "
            "Cleveland et al. decide it by the main-channel slope for both segments "
            "(below 0.002 both offset, above 0.003 neither) and leave 0.002-0.003 to "
            "the engineer ('if flow direction ambiguity is present, treat as low "
            "slope'); the two agree when both slopes lie on the same side of 0.002 "
            "and differ for a flat main channel under a steeper overland segment "
            "(Cleveland et al. offset it too), for a steep main channel under a flat "
            "overland segment (Hydrolog offsets it) and in the transitional band "
            "(Hydrolog never offsets the channel there)"
        ),
        (
            "at a flow path slope of 0.002 the channel part rises by 8.97 %, at an "
            "overland slope of 0.002 the overland part by 5.35 %, as the offset is "
            "dropped: tc is not monotonic in either slope"
        ),
    ),
    assumptions=(
        (
            "the 92 Texas watersheds of Roussel et al. (2005): 0.25-150 square miles "
            "(0.65-388 km2, checked by WatershedParameters.calculate_tc), main "
            "channels of 1-50 miles at 0.002-0.02; 'no watersheds with low "
            "topographic slopes are available in the underlying database' "
            "(supplement, p. 29)"
        ),
        (
            "the overland segment up to 1,200 ft, Kerby's upper limit (supplement, p. "
            "29); the method states no range of the overland slope, and its own "
            "example takes 2 %"
        ),
    ),
    traps={
        "difference_denominator": "constraint flow_path_longer_than_overland: the "
        "channel segment L_fp - L_ov vanishes at the boundary point, which is "
        "refused, so Kirpich never takes a length of 0",
        "singular_at_bound": "range cases *_slope_m_per_m-physical_low_*: the offset "
        "keeps both parts finite as a slope tends to 0",
    },
    reference_cases=("tests/fixtures/formulas/tc-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the two SI forms with unrounded constants and the offset "
            "per segment, evaluated with the decimal module at 50 digits",
            test="tests/unit/test_formulas_tc.py (limit decimal)",
        ),
    ),
    base={
        "overland_length_km": 0.3,
        "overland_slope_m_per_m": 0.082,
        "retardance": 0.4,
        "flow_path_length_km": 15.88,
        "flow_path_slope_m_per_m": 0.0114,
    },
)

SPECS: Final = (KIRPICH, NRCS, GIANDOTTI, FAA, KERBY, KERBY_KIRPICH)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""


class ConcentrationTime:
    """
    Time of concentration by six empirical formulas, each declared by its spec.

    Every method takes the inputs its source defines, with lengths in km and slopes
    in m/m, and returns the time in minutes; ``docs/FORMULAS.md`` gives the
    equations, constants, ranges and sources of the specs ``kirpich``, ``nrcs``,
    ``giandotti``, ``faa``, ``kerby`` and ``kerby_kirpich``. An input the spec refuses
    raises ``InvalidParameterError`` with the standard's ``details.reason``; an input
    outside the data of the formula gives the warning ``OutsideTypicalRange``.

    Examples
    --------
    >>> tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
    >>> print(f"{tc:.1f} min")
    85.9 min

    >>> tc = ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72)
    >>> print(f"{tc:.1f} min")
    368.7 min
    """

    @staticmethod
    def kirpich(length_km: float, slope_m_per_m: float) -> float:
        """Return the time of concentration by Kirpich's formula, spec kirpich.

        Parameters
        ----------
        length_km : float
            Length of the longest flow path, along the watercourse from the outlet to
            the hydraulically most distant point of the watershed [km].
        slope_m_per_m : float
            Slope of that path: the elevation of its head minus the outlet's, over its
            length [m/m], not in percent.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``, ``details.option``).

        Warns
        -----
        OutsideTypicalRange
            For an input outside the data of the formula (``method`` the spec's name,
            ``parameter`` the input). The area of the data is checked by
            ``WatershedParameters.calculate_tc``.
        """
        x = checked_inputs(KIRPICH, length_km=length_km, slope_m_per_m=slope_m_per_m)
        tc = _kirpich_min(x.real("length_km"), x.real("slope_m_per_m"))
        return checked_outputs(KIRPICH, {"tc_min": tc}).real("tc_min")

    @staticmethod
    def nrcs(length_km: float, slope_m_per_m: float, cn: float) -> float:
        """Return the time of concentration by the NRCS lag equation, spec nrcs.

        The equation gives the lag; the time of concentration is the lag over the
        ratio of the spec, and a unit hydrograph takes the lag again.

        Parameters
        ----------
        length_km : float
            Flow length: the longest path along which water flows from the divide to
            the outlet [km].
        slope_m_per_m : float
            Average land slope of the watershed Y [m/m], not the slope of the flow
            path and not in percent.
        cn : float
            Curve number of AMC II, the retardance factor of the equation; a weighted
            (fractional) CN is used as given.

        Returns
        -------
        float
            Time of concentration [min], not the lag.

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``, ``details.option``).

        Warns
        -----
        OutsideTypicalRange
            For a CN outside the CN the equation may be used with. The area of its
            watersheds is checked by ``WatershedParameters.calculate_tc``.
        """
        x = checked_inputs(
            NRCS, length_km=length_km, slope_m_per_m=slope_m_per_m, cn=cn
        )
        tc = _nrcs_min(x.real("length_km"), x.real("slope_m_per_m"), x.real("cn"))
        return checked_outputs(NRCS, {"tc_min": tc}).real("tc_min")

    @staticmethod
    def giandotti(area_km2: float, length_km: float, elevation_diff_m: float) -> float:
        """Return the time of concentration by Giandotti's formula, spec giandotti.

        The first input is the area of the watershed in square kilometres (its name
        carries the unit, so the standard's check of this docstring, which allows no
        digit, keeps it out of the list below).

        Parameters
        ----------
        length_km : float
            Length of the main channel [km].
        elevation_diff_m : float
            Mean elevation of the watershed minus the elevation of the outlet [m],
            not the relief.

        Returns
        -------
        float
            Time of concentration [min].

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``, ``details.option``).

        Warns
        -----
        OutsideTypicalRange
            For an area outside the basins of the formula's data.
        """
        x = checked_inputs(
            GIANDOTTI,
            area_km2=area_km2,
            length_km=length_km,
            elevation_diff_m=elevation_diff_m,
        )
        tc = _giandotti_min(
            x.real("area_km2"), x.real("length_km"), x.real("elevation_diff_m")
        )
        return checked_outputs(GIANDOTTI, {"tc_min": tc}).real("tc_min")

    @staticmethod
    def faa(length_km: float, slope_m_per_m: float, runoff_coeff: float) -> float:
        """Return the overland flow time by the FAA formula, spec faa.

        Parameters
        ----------
        length_km : float
            Overland flow length, from the most remote point of the drainage area to
            the inlet [km].
        slope_m_per_m : float
            Slope of the overland flow surface [m/m], not in percent.
        runoff_coeff : float
            Runoff coefficient C of the rational method, from the circular's table.

        Returns
        -------
        float
            Overland flow (inlet) time [min].

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``, ``details.option``).

        Warns
        -----
        OutsideTypicalRange
            For a coefficient above those of the circular's table.
        """
        x = checked_inputs(
            FAA,
            length_km=length_km,
            slope_m_per_m=slope_m_per_m,
            runoff_coeff=runoff_coeff,
        )
        tc = _faa_min(
            x.real("length_km"), x.real("slope_m_per_m"), x.real("runoff_coeff")
        )
        return checked_outputs(FAA, {"tc_min": tc}).real("tc_min")

    @staticmethod
    def kerby(length_km: float, slope_m_per_m: float, retardance: float) -> float:
        """Return the overland flow time by Kerby's formula, spec kerby.

        A low slope is offset as the spec states, which makes the time step up where
        the offset ends.

        Parameters
        ----------
        length_km : float
            Overland flow length, from the most distant point until a defined channel
            is reached [km].
        slope_m_per_m : float
            Slope of the terrain the overland flow runs on [m/m], not in percent.
        retardance : float
            Kerby's retardance coefficient N of the surface (his table is in the
            spec), not Manning's n.

        Returns
        -------
        float
            Overland flow time [min].

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input (``details.reason``, ``details.option``).

        Warns
        -----
        OutsideTypicalRange
            For a length, slope or retardance outside Kerby's data; the slope is
            checked before the offset. The area of the data is checked by
            ``WatershedParameters.calculate_tc``.
        """
        x = checked_inputs(
            KERBY,
            length_km=length_km,
            slope_m_per_m=slope_m_per_m,
            retardance=retardance,
        )
        tc = _kerby_min(
            x.real("length_km"), x.real("slope_m_per_m"), x.real("retardance")
        )
        return checked_outputs(KERBY, {"tc_min": tc}).real("tc_min")

    @staticmethod
    def kerby_kirpich(
        overland_length_km: float,
        overland_slope_m_per_m: float,
        retardance: float,
        flow_path_length_km: float,
        flow_path_slope_m_per_m: float,
    ) -> float:
        """Return the time of concentration by Kerby-Kirpich, spec kerby_kirpich.

        Kerby's formula times the overland segment and Kirpich's the rest of the
        longest flow path as the channel, at the slope of the whole path; each segment
        decides the low-slope offset by its own slope, a deviation the spec states.

        Parameters
        ----------
        overland_length_km : float
            Overland (sheet) flow length from the hydraulically most distant point to
            the start of a defined channel [km].
        overland_slope_m_per_m : float
            Slope of the terrain the overland flow runs on [m/m].
        retardance : float
            Kerby's retardance coefficient N of the overland surface.
        flow_path_length_km : float
            Length of the main channel as the method defines it: the longest flow
            path from the divide to the outlet, the overland segment included [km];
            longer than ``overland_length_km``.
        flow_path_slope_m_per_m : float
            Slope of that path: the elevation of its head minus the outlet's, over
            ``flow_path_length_km`` [m/m].

        Returns
        -------
        float
            Time of concentration [min], the overland time plus the channel time.

        Raises
        ------
        InvalidParameterError
            If the spec refuses an input, or the flow path is not longer than the
            overland segment (``details.reason`` ``outside_physical_range``,
            ``details.constraint`` ``flow_path_longer_than_overland``).

        Warns
        -----
        OutsideTypicalRange
            For the overland length or the retardance outside Kerby's data, and the
            flow path length or slope outside the main channels of the watersheds the
            method was verified on. Their area is checked by
            ``WatershedParameters.calculate_tc``.
        """
        x = checked_inputs(
            KERBY_KIRPICH,
            overland_length_km=overland_length_km,
            overland_slope_m_per_m=overland_slope_m_per_m,
            retardance=retardance,
            flow_path_length_km=flow_path_length_km,
            flow_path_slope_m_per_m=flow_path_slope_m_per_m,
        )
        overland = x.real("overland_length_km")
        t_overland = _kerby_min(
            overland, x.real("overland_slope_m_per_m"), x.real("retardance")
        )
        t_channel = _kirpich_min(
            x.real("flow_path_length_km") - overland,
            _offset(x.real("flow_path_slope_m_per_m")),
        )
        return checked_outputs(KERBY_KIRPICH, {"tc_min": t_overland + t_channel}).real(
            "tc_min"
        )
