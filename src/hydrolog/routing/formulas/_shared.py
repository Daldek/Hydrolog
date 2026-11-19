"""What the specs of the routing formulas share: sources, a hydrograph, its step.

Every routing formula takes the inflow ordinates at a regular step and the outflow at
the first ordinate, and gives the outflow at the same ordinates (ADR-0008): the inputs
:func:`inflow`, :func:`timestep` and :func:`initial_outflow` are declared once here,
with the sources that the specs cite and the volume of a hydrograph by the trapezoid
rule, which the conservation laws of the specs compare.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog.nogat_formulas import Output, Range, Source, Variable, convert
from hydrolog.routing.reach import MAX_ORDINATES

__all__ = [
    "DISCHARGE",
    "DISCHARGE_TYPICAL",
    "MAX_ORDINATES",
    "ROUTING_TESTS",
    "SECONDS_PER_MINUTE",
    "STORAGE",
    "TIMESTEP",
    "TIMESTEP_TYPICAL",
    "em_1110_2_1417",
    "hec_hms",
    "initial_outflow",
    "inflow",
    "neh630_17",
    "outflow",
    "ponce",
    "storage",
    "timestep",
    "volume_m3",
]

SECONDS_PER_MINUTE: Final = convert(1.0, "min", "s")
"""The seconds of a minute, from the units table (CMP-4.3)."""

_NEH630_17_URL = (
    "https://directives.nrcs.usda.gov/sites/default/files2/1712930634/"
    "Part%20630%20-%20Hydrology.pdf"
)
_HEC_HMS_URL = "https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/"
_EM_URL = (
    "https://www.publications.usace.army.mil/Portals/76/Publications/"
    "EngineerManuals/EM_1110-2-1417.pdf"
)
_PONCE_URL = "https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html"

ROUTING_TESTS: Final = (
    "Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, "
    "tests/unit/_routing_reference.py, docs/USAGE.md section route)"
)
"""The project's data the typical ranges of the routing formulas come from."""


def neh630_17(locator: str) -> Source:
    """Return NRCS NEH Part 630, chapter 17 (Flood Routing) at a locator."""
    return Source(
        citation="USDA-NRCS (2014). National Engineering Handbook, Part 630 "
        "Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014)",
        locator=locator,
        url=_NEH630_17_URL,
    )


def hec_hms(model: str, page: str, locator: str) -> Source:
    """Return a page of the HEC-HMS Technical Reference Manual, Channel Flow."""
    return Source(
        citation="US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS "
        f"Technical Reference Manual, Channel Flow: {model}",
        locator=locator,
        url=_HEC_HMS_URL + page,
    )


def em_1110_2_1417(locator: str) -> Source:
    """Return USACE EM 1110-2-1417 (Flood-Runoff Analysis) at a locator."""
    return Source(
        citation="US Army Corps of Engineers (1994). Engineering and Design: "
        "Flood-Runoff Analysis, EM 1110-2-1417",
        locator=locator,
        url=_EM_URL,
    )


def ponce(locator: str) -> Source:
    """Return Ponce's online article on linear reservoirs at a locator."""
    return Source(
        citation="Ponce, V.M. (online). Linear reservoirs and numerical diffusion, "
        "San Diego State University",
        locator=locator,
        url=_PONCE_URL,
    )


DISCHARGE: Final = Range(
    low=0.0,
    test_high=1.0e6,
    test_reason="a million m3/s exceeds the discharge of every river, the Amazon's "
    "included; the routing formulas are linear in the discharge (their scaling), so "
    "any bound tests their arithmetic",
)
"""Physical range of a discharge [m3/s]."""

DISCHARGE_TYPICAL: Final = Range(
    low=0.0,
    high=100.0,
    source=Source(
        citation=ROUTING_TESTS,
        locator="floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 "
        "cfs; the guide's Kamiennik, 54.2 m3/s",
    ),
)
"""Typical range of a discharge of the routing tests [m3/s]."""

TIMESTEP: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=1440.0,
    test_reason="a day, the step of a series of daily discharges (IMGW-PIB)",
)
"""Physical range of a time step [min]."""

TIMESTEP_TYPICAL: Final = Range(
    low=5.0,
    high=720.0,
    source=Source(
        citation=ROUTING_TESTS,
        locator="steps of 5 min (Hydrograf's networks, "
        "tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example "
        "and NEH 630 ch. 17 example 17-2, 0.5 d)",
    ),
)
"""Typical range of a time step [min]."""

STORAGE: Final = Range(low=0.0)
"""Physical range of the water stored in a reach [m3]."""


def inflow() -> Variable:
    """Return the input ``inflow_m3s``: the inflow ordinates at a regular step."""
    return Variable(
        name="inflow_m3s",
        symbol="I_t",
        unit="m3/s",
        kind="real_array",
        description="Inflow at t = 0, dt, 2 dt, ...: the hydrograph that enters the "
        "reach, linear between its ordinates.",
        physical=DISCHARGE,
        applicability="unstated",
        typical=DISCHARGE_TYPICAL,
        min_length=2,
        max_length=MAX_ORDINATES,
    )


def timestep() -> Variable:
    """Return the input ``timestep_min``: the step of the ordinates."""
    return Variable(
        name="timestep_min",
        symbol=r"\Delta t",
        unit="min",
        description="Time step of the inflow and of the outflow.",
        physical=TIMESTEP,
        applicability="unstated",
        typical=TIMESTEP_TYPICAL,
    )


def initial_outflow() -> Variable:
    """Return the input ``initial_outflow_m3s``: the outflow at the first ordinate."""
    return Variable(
        name="initial_outflow_m3s",
        symbol="O_0",
        unit="m3/s",
        description="Outflow at the first ordinate; the reach starts at rest with it.",
        physical=DISCHARGE,
        applicability="unstated",
        typical=DISCHARGE_TYPICAL,
    )


def outflow() -> Output:
    """Return the output ``outflow_m3s``: the outflow at every inflow ordinate."""
    return Output(
        name="outflow_m3s",
        unit="m3/s",
        kind="real_array",
        symbol="O_t",
        description="Outflow at the ordinates of the inflow.",
        physical=DISCHARGE,
    )


def storage(name: str, description: str) -> Output:
    """Return an output of stored water [m3]."""
    return Output(
        name=name, unit="m3", symbol="S", description=description, physical=STORAGE
    )


def volume_m3(values: NDArray[np.float64] | Sequence[float], step_min: float) -> float:
    """Return the volume of a hydrograph by the trapezoid rule [m3], summed exactly."""
    series = np.asarray(values, dtype=np.float64)
    halves = 0.5 * (float(series[0]) + float(series[-1]))
    return (math.fsum(series[1:-1].tolist()) + halves) * step_min * SECONDS_PER_MINUTE
