"""What the specs of the unit hydrographs share: sources, ranges and bounds (CMP-2.1).

The specs ``scs`` (:mod:`hydrolog.runoff.unit_hydrograph`), ``snyder`` and
``snyder_shape`` (:mod:`hydrolog.runoff.snyder_uh`), ``clark``
(:mod:`hydrolog.runoff.clark_iuh`) and ``uh_convolution``
(:mod:`hydrolog.runoff.convolution`) cite the same handbooks, take their typical ranges
from the watersheds Hydrograf hands to Hydrolog and bound the length of a hydrograph
alike. Each name here is declared once and imported by the specs.
"""

from __future__ import annotations

from typing import Final

from hydrolog.nogat_formulas import Range, Source

__all__ = [
    "AREA",
    "AREA_TYPICAL",
    "CHOW_NOTES",
    "HEC_TRM_2000",
    "HEC_TRM_ONLINE",
    "INNOVYZE_SNYDER",
    "KZGW",
    "MAX_ORDINATES",
    "NEH4_16",
    "NEH630_16",
    "ORDINATES_SOURCE",
    "TC",
    "TC_TYPICAL",
    "TIMESTEP",
    "TIMESTEP_TYPICAL",
    "chow_notes",
    "handoffs",
    "hec_trm_2000",
    "hec_trm_online",
    "kzgw",
    "neh630_16",
]

# --- sources -----------------------------------------------------------------------

NEH630_16: Final = (
    "USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: "
    "Hydrographs (210-VI-NEH, March 2007)"
)
_NEH630_16_URL: Final = (
    "https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf"
)
NEH4_16: Final = (
    "USDA-SCS (1972). National Engineering Handbook, Section 4 Hydrology, Chapter 16: "
    "Hydrographs (NEH Notice 4-102, August 1972; amendment 6, March 1985)"
)
HEC_TRM_2000: Final = (
    "USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference "
    "Manual (CPD-74B, March 2000)"
)
_HEC_TRM_2000_URL: Final = (
    "https://www.hec.usace.army.mil/software/hec-hms/documentation/"
    "HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf"
)
HEC_TRM_ONLINE: Final = (
    "USACE-HEC. HEC-HMS Technical Reference Manual (online, read 2026-11-19), "
    "chapter Transform"
)
_HEC_TRM_ONLINE_URL: Final = (
    "https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/"
)
KZGW: Final = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL: Final = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
CHOW_NOTES: Final = Source(
    citation="Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, "
    "V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, "
    "University of Colorado Boulder",
    locator="Snyder's synthetic UHG, pp. 76-78 (eqs. 7.7.2-7.7.4, C1 0.75, C2 2.75, "
    "C3 5.56, Cw 2.14 and 1.22 in SI, 770 and 440 in English units, areas of 30 to "
    "30,000 km2); SCS dimensionless hydrograph, p. 79 (C = 2.08, 483.4 in English "
    "units)",
    url="https://civil.colorado.edu/~balajir/CVEN5333/Lectures/"
    "Unit-Hydrographs-Chow-Chap7.pdf",
)
INNOVYZE_SNYDER: Final = Source(
    citation="Innovyze. InfoSWMM help, Snyder Unit Hydrograph Method (online, read "
    "2026-11-19)",
    locator="the widths W50 and W75 of the unit hydrograph: C50 = 770 and C75 = 440 "
    "in U.S. customary units, 2.14 and 1.22 in S.I. units; C2 = 640 and 2.75 of the "
    "peak",
    url="https://help.innovyze.com/space/infoswmm/17598671/"
    "Snyder+Unit+Hydrograph+Method",
)
_HANDOFFS: Final = (
    "Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November "
    "2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa "
    "(134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, "
    "and the guide's Kamiennik to Świerzawa (37.22 km2)"
)
_HANDOFF_FILES: Final = (
    "tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json"
)


def neh630_16(locator: str) -> Source:
    """Return NEH 630 chapter 16 at ``locator``."""
    return Source(citation=NEH630_16, locator=locator, url=_NEH630_16_URL)


def hec_trm_2000(locator: str) -> Source:
    """Return the HEC-HMS Technical Reference Manual of 2000 at ``locator``."""
    return Source(citation=HEC_TRM_2000, locator=locator, url=_HEC_TRM_2000_URL)


def hec_trm_online(page: str, locator: str) -> Source:
    """Return the ``page`` of the online HEC-HMS Technical Reference Manual."""
    return Source(
        citation=HEC_TRM_ONLINE, locator=locator, url=f"{_HEC_TRM_ONLINE_URL}{page}"
    )


def chow_notes(locator: str) -> Source:
    """Return Rajagopalan's notes after Chow et al. (1988) at ``locator``."""
    return Source(citation=CHOW_NOTES.citation, locator=locator, url=CHOW_NOTES.url)


def kzgw(locator: str) -> Source:
    """Return KZGW (2017), annex 2, at ``locator``."""
    return Source(citation=KZGW, locator=locator, url=_KZGW_URL)


def handoffs(what: str) -> Source:
    """Return the hand-offs of Hydrograf recorded in the tests, for ``what``."""
    return Source(citation=_HANDOFFS, locator=f"{_HANDOFF_FILES}: {what}")


# --- ranges and bounds ----------------------------------------------------------------

AREA: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=1.0e6,
    test_reason="a million km2, five times the basin of the Vistula (194,000 km2) "
    "and four thousand times the largest watershed Hydrograf hands over",
)
"""Physical range of a watershed's area [km2]."""

AREA_TYPICAL: Final = Range(
    low=0.0003,
    high=250.0,
    source=Source(
        citation=_HANDOFFS,
        locator=f"{_HANDOFF_FILES}: areas of 0.00035 to 135 km2; Hydrograf computes "
        "hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py)",
    ),
)
"""Typical range of a watershed's area [km2]."""

TC: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=4500.0,
    test_reason="ten times the longest time of concentration of the hand-offs (450 "
    "min)",
)
"""Physical range of a time of concentration [min]."""

TC_TYPICAL: Final = Range(
    low=1.0,
    high=450.0,
    source=handoffs(
        "Kirpich's tc of the flow paths of the 27 watersheds, the default method of "
        "hydrograph generate, 1.04 to 450 min"
    ),
)
"""Typical range of a time of concentration [min]."""

TIMESTEP: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=1440.0,
    test_reason="a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a "
    "step of 1440 min)",
)
"""Physical range of a time step or a unit duration [min]."""

TIMESTEP_TYPICAL: Final = Range(
    low=5.0,
    high=60.0,
    source=Source(
        citation=f"{_HANDOFFS}; and {KZGW}",
        locator=f"{_HANDOFF_FILES}: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 "
        "(1 h) and 6.4 (0.5 h), pp. 92-110",
        url=_KZGW_URL,
    ),
)
"""Typical range of a time step or a unit duration [min]."""

MAX_ORDINATES: Final = 1_000_000
"""Largest number of ordinates of a unit hydrograph on its grid, as of a routed one."""

ORDINATES_SOURCE: Final = Source(
    citation="Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach."
    "MAX_ORDINATES)",
    locator="a million ordinates: the routing of a hydrograph refuses a longer one",
)
"""Where the bound of a hydrograph's length comes from."""
