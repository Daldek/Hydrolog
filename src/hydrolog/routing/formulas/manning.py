r"""Manning's normal flow in a prismatic channel, the spec ``manning_normal_flow``.

:data:`MANNING_NORMAL_FLOW` declares the normal flow of a discharge in a trapezoid of
bottom width ``b`` with banks of ``z`` horizontal to one vertical (``z = 0`` a
rectangle, ``b = 0`` a triangle): the depth ``y`` at which Manning's equation in SI
units, ``Q = A R^(2/3) S^(1/2) / n`` with ``A = (b + z y) y``,
``P = b + 2 y (1 + z^2)^(1/2)`` and ``R = A / P``, carries the discharge ``Q`` down the
slope ``S``, with the area, the top width ``T = b + 2 z y``, the mean velocity
``V = Q / A`` and the celerity of a kinematic flood wave at that depth,
``c = dQ/dA = V (5/3 - 2/3 A P' / (T P))`` with ``P' = dP/dy``; :func:`normal_flow`
computes it. :class:`~hydrolog.routing.TrapezoidalSection` takes its flow from it, and
:class:`~hydrolog.routing.MuskingumCungeReach` the celerity and the top width at its
reference discharge (ADR-0061).

The conveyance ``K = A R^(2/3)`` grows with the depth at ``d ln K / d ln y`` between 1
and 10/3 in every trapezoid, so a first guess ``u0`` of ``ln y`` and its misfit
``g0 = ln K - ln(Q n / S^(1/2))`` bracket the root within ``|g0|`` of ``u0`` without a
search. Brent's method (``scipy.optimize.brentq``, a computation delegated by CMP-1.2)
finds ``ln y`` in that bracket to a few units of 1e-16, for every depth a float holds;
a flow whose depth, area, top width, velocity or celerity is not a normal float (one
that overflows, or underflows to fewer digits) is refused by the precondition
``representable_flow``.

Examples
--------
A trapezoid of 4 m with 2:1 banks and ``n`` = 0.035 on a slope of 0.001, at 10 m3/s:

>>> flow = normal_flow(10.0, 0.001, 4.0, 2.0, 0.035)
>>> round(flow.depth_m, 3), round(flow.top_width_m, 3)
(1.551, 10.204)
>>> round(flow.velocity_m_per_s, 3), round(flow.celerity_m_per_s, 3)
(0.908, 1.246)
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Final

import numpy as np
from scipy.optimize import brentq

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
    Scaling,
    Source,
    Tolerance,
    Values,
    Variable,
    assert_within,
)
from hydrolog.routing.formulas._shared import ROUTING_TESTS, hec_hms, neh630_17

__all__ = [
    "BED_SLOPE",
    "BED_SLOPE_TYPICAL",
    "MANNING_NORMAL_FLOW",
    "REFERENCE_DISCHARGE",
    "REFERENCE_DISCHARGE_TYPICAL",
    "SPECS",
    "NormalFlow",
    "normal_flow",
]

_RADIUS_EXPONENT: Final = Fraction(2, 3)
"""Exponent of the hydraulic radius in Manning's equation."""

_SLOPE_EXPONENT: Final = Fraction(1, 2)
"""Exponent of the slope in Manning's equation."""

_RADIUS: Final = float(_RADIUS_EXPONENT)
_SLOPE: Final = float(_SLOPE_EXPONENT)

_TOLERANCE: Final = 4.0 * float(np.finfo(np.float64).eps)
"""Brent's tolerance on ``ln y``, absolute and relative: the least scipy allows."""

_MAX_ITERATIONS: Final = 200
"""Brent's bound on its iterations: a bracket of any finite width shrinks to the
tolerance in fewer than a hundred bisections."""

_MARGIN: Final = 1e-9
"""Widening of the bracket per unit of the logarithms, far above their rounding."""

BED_SLOPE: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=0.2,
    test_reason="ten times the steepest reach of the project's data, 0.02 in "
    "Hydrograf's network tests/fixtures/handoff_hydrograf_network.json",
)
"""Physical range of the bed slope of a reach [m/m]: normal flow needs a fall."""

BED_SLOPE_TYPICAL: Final = Range(
    low=0.0002,
    high=0.02,
    source=Source(
        citation=ROUTING_TESTS,
        locator="0.0002 to 0.002778 in the tests of the reach "
        "(tests/unit/test_routing_cunge.py), 0.00208 to 0.009859 on the reaches of "
        "Hydrograf's Nysa Szalona network from the DEM "
        "(tests/fixtures/handoff_hydrograf_network_nysa_szalona.json), 0.02 in "
        "tests/fixtures/handoff_hydrograf_network.json; 0.00091 in NEH 630 examples "
        "17-4 and 17-5",
    ),
)
"""Typical range of the bed slope of a reach [m/m]."""

REFERENCE_DISCHARGE: Final = Range(
    low=0.0,
    low_inclusive=False,
    test_high=1.0e6,
    test_reason="a million m3/s exceeds the discharge of every river, the Amazon's "
    "included",
)
"""Physical range of a discharge that flows: above zero [m3/s]."""

REFERENCE_DISCHARGE_TYPICAL: Final = Range(
    low=1.0,
    high=300.0,
    source=Source(
        citation=ROUTING_TESTS,
        locator="reference discharges of 0.95 to 300.05 m3/s in the tests of the "
        "reach (tests/unit/test_routing_cunge.py), 12 m3/s in "
        "tests/fixtures/network_flood.json; NEH 630 examples 17-4 and 17-5, 684.18 "
        "and 3,385.4 ft3/s (19.4 and 95.9 m3/s)",
    ),
)
"""Typical range of the reference discharge of a reach [m3/s]."""


@dataclass(frozen=True)
class NormalFlow:
    """The normal flow of a discharge, by the spec ``manning_normal_flow``.

    Attributes
    ----------
    depth_m : float
        Normal depth [m].
    area_m2 : float
        Flow area [m2].
    top_width_m : float
        Width of the water surface [m].
    velocity_m_per_s : float
        Mean velocity ``Q / A`` [m/s].
    celerity_m_per_s : float
        Celerity of a kinematic flood wave, ``dQ/dA`` at a constant slope [m/s].
    """

    depth_m: float
    area_m2: float
    top_width_m: float
    velocity_m_per_s: float
    celerity_m_per_s: float


# --- the computation -----------------------------------------------------------------


@dataclass(frozen=True)
class _Section:
    """A section in logarithms, with the conveyance ``Q n / S^(1/2)`` it must carry.

    ``log_width`` and ``log_side`` are minus infinity for a triangle and a rectangle;
    ``log_wall`` is the logarithm of ``P' = 2 (1 + z^2)^(1/2)``, the wetted perimeter
    per metre of depth beyond the bottom.
    """

    log_width: float
    log_side: float
    log_wall: float
    log_target: float

    def misfit(self, log_depth: float) -> float:
        """Return ``ln K(y) - ln(Q n / S^(1/2))`` at ``y = e^u``, without overflow."""
        log_area = float(np.logaddexp(self.log_width, self.log_side + log_depth))
        log_area += log_depth
        log_perimeter = float(np.logaddexp(self.log_width, self.log_wall + log_depth))
        return log_area + _RADIUS * (log_area - log_perimeter) - self.log_target

    def guess(self) -> float:
        """Return the shallower ``ln y`` of the bottom and of the banks alone.

        The wide rectangle of the bottom has ``K = b y^(5/3)``, the triangle of the
        banks ``K = z^(5/3) y^(8/3) / P'^(2/3)``.
        """
        guesses = []
        if self.log_width > -math.inf:
            guesses.append((self.log_target - self.log_width) / (1.0 + _RADIUS))
        if self.log_side > -math.inf:
            side = (1.0 + _RADIUS) * self.log_side - _RADIUS * self.log_wall
            guesses.append((self.log_target - side) / (2.0 + _RADIUS))
        return min(guesses)


def _log_depth(section: _Section) -> float:
    """Return ``ln y`` of the normal depth, NaN where the logarithms overflow.

    The misfit grows with ``ln y`` at a rate of at least 1, so the root lies within
    ``|g0|`` of the guess: the bracket of twice that, widened beyond the rounding of
    the logarithms, holds it with a change of sign at its ends.
    """
    start = section.guess()
    misfit = section.misfit(start)
    if not (math.isfinite(start) and math.isfinite(misfit)):
        return math.nan
    if misfit == 0.0:
        return start
    half = 2.0 * abs(misfit)
    half += _MARGIN * (1.0 + abs(start) + abs(section.log_target))
    low, high = start - half, start + half
    if not section.misfit(low) < 0.0 < section.misfit(high):
        return math.nan
    return float(
        brentq(
            section.misfit,
            low,
            high,
            xtol=_TOLERANCE,
            rtol=_TOLERANCE,
            maxiter=_MAX_ITERATIONS,
        )
    )


def _flow(x: Values) -> dict[str, float]:
    """Return the normal flow; a value a float cannot hold is NaN or infinite."""
    discharge, slope = x.real("discharge_m3s"), x.real("slope_m_per_m")
    width, side = x.real("bottom_width_m"), x.real("side_slope_m_per_m")
    roughness = x.real("manning_n")
    wall = 2.0 * math.hypot(1.0, side)
    section = _Section(
        log_width=math.log(width) if width > 0.0 else -math.inf,
        log_side=math.log(side) if side > 0.0 else -math.inf,
        log_wall=math.log(wall),
        log_target=math.log(discharge) + math.log(roughness) - _SLOPE * math.log(slope),
    )
    with np.errstate(all="ignore"):
        depth = np.exp(np.float64(_log_depth(section)))
        area = (width + side * depth) * depth
        top = width + 2.0 * side * depth
        perimeter = width + wall * depth
        velocity = discharge / area
        # d ln Q / dy = (5/3) T / A - (2/3) P' / P, and c = dQ/dA = (dQ/dy) / T
        shape = (area / top) * (wall / perimeter)
        celerity = velocity * ((1.0 + _RADIUS) - _RADIUS * shape)
    return {
        "depth_m": float(depth),
        "area_m2": float(area),
        "top_width_m": float(top),
        "velocity_m_per_s": float(velocity),
        "celerity_m_per_s": float(celerity),
    }


def _representable(x: Values) -> bool:
    """Whether the depth, area, top width, velocity and celerity are normal floats."""
    return all(sys.float_info.min <= value < math.inf for value in _flow(x).values())


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_DECIMAL_POINTS: Final = (
    # discharge, slope, bottom width, side slope, n
    (10.0, 0.001, 4.0, 2.0, 0.035),
    (19.37375, 0.00091, 4.572, 2.0, 0.04),
    (5.0, 0.002, 3.0, 0.0, 0.03),
    (7.0, 0.003, 0.0, 2.0, 0.03),
    (2000.0, 0.0005, 5000.0, 0.0, 0.03),
    (1.0e4, 1.0e-4, 1.0, 0.0, 0.05),
    (1.0e-6, 0.01, 2.0, 1.0, 0.04),
    (300.0, 0.02, 30.0, 0.5, 0.05),
)
"""Points of the decimal oracle: the doctest, NEH's 684.18 ft3/s, a rectangle, a
triangle, a wide, a deep narrow and a nearly dry channel, a steep one."""


def _decimal_flow(
    discharge: float, slope: float, width: float, side: float, roughness: float
) -> tuple[Decimal, Decimal]:
    """Return the normal depth and ``dQ/dA`` at it, to fifty digits.

    Manning's equation is written ``Q = S^(1/2) / n (A^5 / P^2)^(1/3)``, the depth found
    by bisection and the celerity by a central difference of ``Q`` over ``A``.
    """
    with localcontext() as context:
        context.prec = 50
        q, s, b, z, n = (Decimal(v) for v in (discharge, slope, width, side, roughness))
        wall = 2 * (1 + z * z).sqrt()
        factor = s.sqrt() / n
        third = Decimal(1) / 3

        def area(y: Decimal) -> Decimal:
            return (b + z * y) * y

        def manning(y: Decimal) -> Decimal:
            return factor * (area(y) ** 5 / (b + wall * y) ** 2) ** third

        low, high = Decimal(0), Decimal(1)
        while manning(high) < q:
            low, high = high, 2 * high
        for _ in range(200):
            middle = (low + high) / 2
            if manning(middle) < q:
                low = middle
            else:
                high = middle
        depth = (low + high) / 2
        step = depth * Decimal("1e-20")
        rise = manning(depth + step) - manning(depth - step)
        celerity = rise / (area(depth + step) - area(depth - step))
        return +depth, +celerity


def _decimal_oracle(run: Callable[..., Values]) -> None:
    for discharge, slope, width, side, roughness in _DECIMAL_POINTS:
        out = run(
            discharge_m3s=discharge,
            slope_m_per_m=slope,
            bottom_width_m=width,
            side_slope_m_per_m=side,
            manning_n=roughness,
        )
        depth, celerity = _decimal_flow(discharge, slope, width, side, roughness)
        assert_within(
            out.real("depth_m"),
            float(depth),
            rel=1e-14,
            reason="brentq stops within four units of 1e-16 of ln y and the misfit "
            "rounds at a few of them; the decimal bisection is exact to 1e-45",
        )
        assert_within(
            out.real("celerity_m_per_s"),
            float(celerity),
            rel=1e-13,
            reason="the depth's 1e-14 and a few roundings of the area, the velocity "
            "and the shape factor; the central difference at 50 digits with a step "
            "of 1e-20 y is exact to 1e-30",
        )


_TRIANGLES: Final = (
    (7.0, 0.003, 2.0, 0.03),
    (0.4, 0.05, 0.5, 0.06),
    (900.0, 2e-4, 6.0, 0.035),
)
"""(Q, S, z, n) of the triangles of the closed form."""


def _triangle(run: Callable[..., Values]) -> None:
    for discharge, slope, side, roughness in _TRIANGLES:
        out = run(
            discharge_m3s=discharge,
            slope_m_per_m=slope,
            bottom_width_m=0.0,
            side_slope_m_per_m=side,
            manning_n=roughness,
        )
        wall = 2.0 * math.sqrt(1.0 + side * side)
        conveyance = discharge * roughness / math.sqrt(slope)
        depth = (conveyance * wall ** (2.0 / 3.0) / side ** (5.0 / 3.0)) ** (3.0 / 8.0)
        velocity = discharge / (side * depth * depth)
        assert_within(
            [
                out.real("depth_m"),
                out.real("top_width_m"),
                out.real("velocity_m_per_s"),
            ],
            [depth, 2.0 * side * depth, velocity],
            rel=1e-13,
            reason="a triangle has the closed form y = (Q n P'^(2/3) / (S^(1/2) "
            "z^(5/3)))^(3/8); its powers and the root finder each round at a few "
            "units of 1e-16",
        )
        assert_within(
            out.real("celerity_m_per_s"),
            4.0 / 3.0 * out.real("velocity_m_per_s"),
            rel=1e-14,
            reason="in a triangle Q grows as A^(4/3), so c = dQ/dA = 4/3 V exactly; "
            "the shape factor A P' / (T P) = 1/2 rounds at 1e-16",
        )


_KINEMATIC_POINTS: Final = (
    (10.0, 0.001, 4.0, 2.0, 0.035),
    (2000.0, 0.0005, 5000.0, 0.0, 0.03),
    (1.0e4, 1.0e-4, 1.0, 0.0, 0.05),
    (1.0e-6, 0.01, 2.0, 1.0, 0.04),
    (50.0, 0.004, 0.0, 20.0, 0.1),
)


def _kinematic(run: Callable[..., Values]) -> None:
    for discharge, slope, width, side, roughness in _KINEMATIC_POINTS:
        out = run(
            discharge_m3s=discharge,
            slope_m_per_m=slope,
            bottom_width_m=width,
            side_slope_m_per_m=side,
            manning_n=roughness,
        )
        ratio = out.real("celerity_m_per_s") / out.real("velocity_m_per_s")
        if not 1.0 <= ratio <= 5.0 / 3.0 * (1.0 + 1e-15):
            raise AssertionError(
                f"manning_normal_flow: c / V = {ratio} at {out}; a trapezoid has "
                "c / V = 5/3 - 2/3 A P' / (T P) with 0 <= A P' / (T P) <= 1"
            )


# --- the spec ------------------------------------------------------------------------

_USGS = Source(
    citation="Arcement, G.J. and Schneider, V.R. (1989). Guide for selecting Manning's "
    "roughness coefficients for natural channels and flood plains, US Geological "
    "Survey Water-Supply Paper 2339",
    locator="Introduction, eqs. 1 and 2 (the first page of the text): V = 1.486/n "
    "R^(2/3) Se^(1/2) and the conveyance K = 1.486/n A R^(2/3), in feet",
    url="https://pubs.usgs.gov/wsp/2339/report.pdf",
)
_HEC = Source(
    citation="US Army Corps of Engineers, Hydrologic Engineering Center. Water Surface "
    "Profile Calculations with HEC-RAS (training lesson 1.6, PROSPECT course)",
    locator="slides 'Cross Section Subdivision for Conveyance Calculations' (Q = "
    "1.486/n A R^(2/3) Sf^(1/2), in feet) and 'Computational Procedure: Tolerances "
    "and trials' (water surface calculation tolerance 0.01 ft by default)",
    url="https://www.hec.usace.army.mil/confluence/prospect/files/124452884/"
    "124453107/1/1669663021202/1.6+L+-+Water+Surface+Profile+Calculations.pdf",
)
_MANNING = Source(
    citation="Manning, R. (1891). On the flow of water in open channels and pipes, "
    "Transactions of the Institution of Civil Engineers of Ireland 20, 161-207",
    access="author-provided",
)
_HMS = hec_hms(
    "Muskingum-Cunge Model",
    "muskingum-cunge-model",
    "eq. 4, the flood wave celerity c = dQ/dA; Required Parameters: the reach's "
    "Manning's n and a rectangle, trapezoid or triangle by its bottom width and side "
    "slope",
)
_NEH = neh630_17(
    "eqs. 17-24 and 17-25, c = dQ/dA = m Q / A, and 17-29 and 17-30a, the weighted m "
    "of a rating table; Table 17-16 and example 17-4, pp. 17-36 to 17-43"
)
_FLOAT64 = Source(
    citation="IEEE 754-2019, binary64: normal numbers of magnitude about 2.2e-308 to "
    "1.8e308, with 53 significant bits; below them the subnormal numbers keep fewer",
    locator="the depth, the area, the top width, the velocity and the celerity of a "
    "flow must be normal numbers to hold their sixteen digits",
)
_MANNING_SCALING = Tolerance(
    rel=1e-12,
    reason="the root finder solves the scaled point afresh: ln y to a few units of "
    "1e-16 of max(1, |ln y|), up to 1e-13 for depths near the ends of the floats",
)

MANNING_NORMAL_FLOW: Final = FormulaSpec(
    name="manning_normal_flow",
    title="Normal flow of a trapezoidal, rectangular or triangular channel by "
    "Manning's equation, with the kinematic celerity dQ/dA",
    function="hydrolog.routing.formulas.manning.normal_flow",
    family="empirical",
    equation=(
        "Q = A R^(2/3) S^(1/2) / n, A = (b + z y) y, P = b + 2 y (1 + z^2)^(1/2), "
        "R = A / P; T = b + 2 z y; V = Q / A; c = dQ/dA = V (5/3 - 2/3 A P' / (T P)), "
        "P' = 2 (1 + z^2)^(1/2); the normal depth y is the root of the first equation"
    ),
    latex=(
        r"Q = \frac{1}{n} A R^{2/3} S^{1/2},\quad A = (b + z y) y,\ "
        r"P = b + 2 y \sqrt{1 + z^2},\ R = \frac{A}{P};\quad T = b + 2 z y,\ "
        r"V = \frac{Q}{A},\ c = \frac{dQ}{dA} = V \left(\frac{5}{3} - \frac{2}{3} "
        r"\frac{A P'}{T P}\right)"
    ),
    variables=(
        Variable(
            name="discharge_m3s",
            symbol="Q",
            unit="m3/s",
            description="Discharge whose normal flow is sought.",
            physical=REFERENCE_DISCHARGE,
            applicability="unstated",
            typical=REFERENCE_DISCHARGE_TYPICAL,
        ),
        Variable(
            name="slope_m_per_m",
            symbol="S",
            unit="m/m",
            description="Bed slope, the friction slope of a uniform flow.",
            physical=BED_SLOPE,
            applicability="unstated",
            typical=BED_SLOPE_TYPICAL,
        ),
        Variable(
            name="bottom_width_m",
            symbol="b",
            unit="m",
            description="Bottom width of the section; zero for a triangle.",
            physical=Range(
                low=0.0,
                test_high=5.0e4,
                test_reason="ten times the widest section of the tests, the 5,000 m "
                "rectangle of tests/unit/test_routing_sections.py",
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=30.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="0 (a triangle) to 30 m in the tests of the section "
                    "(tests/unit/test_routing_sections.py), 5 to 15 m in the tests "
                    "of the reach, 8 m in tests/fixtures/network_flood.json; NEH 630 "
                    "example 17-4, 15 ft (4.57 m)",
                ),
            ),
        ),
        Variable(
            name="side_slope_m_per_m",
            symbol="z",
            unit="m/m",
            description="Horizontal metres per vertical metre of both banks; zero for "
            "a rectangle.",
            physical=Range(
                low=0.0,
                test_high=20.0,
                test_reason="ten times the gentlest banks of the tests, NEH's 2:1",
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=2.0,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="0 (a rectangle) to 2 (2:1 banks) in the tests of the "
                    "section and of the reach, 2 in tests/fixtures/network_flood.json "
                    "and NEH 630 example 17-4",
                ),
            ),
        ),
        Variable(
            name="manning_n",
            symbol="n",
            unit="s/m^(1/3)",
            description="Manning's roughness of the whole wetted perimeter.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.0,
                test_reason="ten times the roughest channel of the tests, n = 0.1 in "
                "tests/unit/test_routing_sections.py",
            ),
            applicability="unstated",
            typical=Range(
                low=0.03,
                high=0.05,
                source=Source(
                    citation=ROUTING_TESTS,
                    locator="0.03 to 0.05 in the tests of the section and of the "
                    "reach, 0.035 in docs/USAGE.md and "
                    "tests/fixtures/network_flood.json; NEH 630 example 17-4, 0.04",
                ),
            ),
        ),
    ),
    outputs=(
        Output(
            name="depth_m",
            unit="m",
            symbol="y",
            description="Normal depth.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="area_m2",
            unit="m2",
            symbol="A",
            description="Flow area at the normal depth.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="top_width_m",
            unit="m",
            symbol="T",
            description="Width of the water surface at the normal depth.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="velocity_m_per_s",
            unit="m/s",
            symbol="V",
            description="Mean velocity Q / A.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
        Output(
            name="celerity_m_per_s",
            unit="m/s",
            symbol="c",
            description="Celerity of a kinematic flood wave, dQ/dA at a fixed slope.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(_USGS, _HEC, _HMS, _NEH, _MANNING),
    constants=(
        Constant(
            name="radius_exponent",
            value=_RADIUS_EXPONENT,
            unit="-",
            symbol="2/3",
            source=_USGS,
        ),
        Constant(
            name="slope_exponent",
            value=_SLOPE_EXPONENT,
            unit="-",
            symbol="1/2",
            source=_USGS,
        ),
    ),
    constraints=(
        Constraint(
            name="has_width",
            cls="physical",
            check=lambda x: x.real("bottom_width_m") + x.real("side_slope_m_per_m") > 0,
            text="b + z > 0: a section with a bottom or banks; neither holds no water",
            source=_HMS,
            satisfied={"bottom_width_m": 0.0},
            violated={"bottom_width_m": 0.0, "side_slope_m_per_m": 0.0},
        ),
        Constraint(
            name="representable_flow",
            cls="precondition",
            check=_representable,
            text="2.2e-308 <= y, A, T, V, c < inf: float64 holds the normal flow to "
            "sixteen digits; a section so narrow, flat or rough, or a discharge so "
            "large or small, that one of them overflows or falls among the subnormal "
            "floats has none",
            source=_FLOAT64,
            satisfied={"discharge_m3s": 1.0e6},
            violated={
                "discharge_m3s": 1.0e6,
                "bottom_width_m": 1.0e-300,
                "side_slope_m_per_m": 0.0,
            },
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"discharge_m3s": 1, "slope_m_per_m": -1, "manning_n": 1},
        scalings=(
            Scaling(
                name="length",
                inputs={"discharge_m3s": 9, "bottom_width_m": 3, "manning_n": -1},
                outputs={
                    "depth_m": 3,
                    "area_m2": 6,
                    "top_width_m": 3,
                    "velocity_m_per_s": 3,
                    "celerity_m_per_s": 3,
                },
                tolerance=_MANNING_SCALING,
            ),
            Scaling(
                name="time",
                inputs={"discharge_m3s": -1, "manning_n": 1},
                outputs={"velocity_m_per_s": -1, "celerity_m_per_s": -1},
                tolerance=_MANNING_SCALING,
            ),
            Scaling(
                name="slope",
                inputs={"discharge_m3s": 1, "slope_m_per_m": 2},
                outputs={"velocity_m_per_s": 1, "celerity_m_per_s": 1},
                tolerance=_MANNING_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="rectangle_by_hand",
                text="b = 2 m, z = 0, n = 0.03, S = 0.001 and Q = 2 (1/2)^(2/3) "
                "0.001^(1/2) / 0.03: A = 2, P = 4, R = 1/2, so y = 1 m",
                inputs={
                    "discharge_m3s": 2.0 * 0.5 ** (2.0 / 3.0) * math.sqrt(0.001) / 0.03,
                    "slope_m_per_m": 0.001,
                    "bottom_width_m": 2.0,
                    "side_slope_m_per_m": 0.0,
                    "manning_n": 0.03,
                },
                expected={"depth_m": 1.0, "area_m2": 2.0, "top_width_m": 2.0},
                tolerance=Tolerance(
                    rel=1e-14,
                    reason="the discharge is rounded once and the root found to a "
                    "few units of 1e-16",
                ),
            ),
            Limit(
                name="triangle_closed_form",
                text="a triangle (b = 0) has the closed form y = (Q n P'^(2/3) / "
                "(S^(1/2) z^(5/3)))^(3/8) and c = 4/3 V",
                check=_triangle,
            ),
            Limit(
                name="kinematic_celerity_bounds",
                text="V <= c <= 5/3 V: the celerity of a trapezoid lies between that "
                "of a deep narrow rectangle and that of a wide one",
                check=_kinematic,
            ),
            Limit(
                name="decimal_oracle",
                text="the depth and dQ/dA equal Manning's equation written as "
                "S^(1/2) / n (A^5 / P^2)^(1/3), solved by bisection and differenced at "
                "50 digits",
                check=_decimal_oracle,
            ),
        ),
    ),
    validation=(
        "none: the sources give Manning's equation as the practice of uniform open "
        "channel flow and report no agreement of their own with observations; n is "
        "chosen from tables or calibrated (USGS WSP 2339)"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "SI units: Q in m3/s, lengths in m, n in s/m^(1/3); the US customary form "
            "multiplies by 1.486, the cube root of the feet in a metre (1.4859) "
            "rounded, as HEC-RAS does (USGS WSP 2339 eq. 1)"
        ),
        "the bed slope is the friction slope: the flow is uniform",
        (
            "the celerity is the local kinematic celerity dQ/dA at the depth "
            "(HEC-HMS eq. 4; NEH eq. 17-25 with m = d ln Q / d ln A); NEH's example "
            "17-4 takes a discharge-weighted m of the rating from zero to Q (eqs. "
            "17-29, 17-30a), 2 % above the local one (case "
            "mc_neh17_example17_4_from_section)"
        ),
        (
            "one roughness for the whole wetted perimeter; a trapezoid with both banks "
            "at z:1, a rectangle at z = 0 and a triangle at b = 0; no floodplain"
        ),
        (
            "the normal depth is found by Brent's method in ln y (scipy.optimize."
            "brentq, delegated, CMP-1.2) in a bracket from the slope of ln K in ln y, "
            "between 1 and 10/3, to four units of 1e-16 of max(1, |ln y|)"
        ),
    ),
    assumptions=(
        "steady uniform flow: the depth is the normal depth of the discharge",
        "a prismatic channel whose n does not change with the depth",
        "the flow stays within the section, which has no top",
    ),
    traps={
        "singular_at_bound": "ln b and ln z of a triangle (b = 0) and of a rectangle "
        "(z = 0) are minus infinity, which logaddexp takes: range cases "
        "bottom_width_m-physical_low and side_slope_m_per_m-physical_low give finite "
        "flows; ln Q and S^(1/2) at their open lower ends: range cases "
        "discharge_m3s-physical_low_inside and slope_m_per_m-physical_low_inside, a "
        "finite flow or the precondition representable_flow",
        "exp_overflow": "y = e^u beyond the largest float: the violated point of "
        "representable_flow and test_a_depth_beyond_a_float_is_refused; the range "
        "cases at the test bounds give finite flows",
    },
    reference_cases=("tests/fixtures/formulas/muskingum-cunge-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the closed form of a triangle, y = (Q n P'^(2/3) / (S^(1/2) "
            "z^(5/3)))^(3/8), and its c = 4/3 V",
            test="tests/unit/test_formulas_muskingum_cunge.py (limit "
            "triangle_closed_form)",
        ),
        Oracle(
            kind="algorithm",
            description="Manning's equation written as S^(1/2) / n (A^5 / P^2)^(1/3) "
            "in decimal arithmetic at 50 digits, its depth by bisection and dQ/dA by a "
            "central difference",
            test="tests/unit/test_formulas_muskingum_cunge.py (limit decimal_oracle)",
        ),
    ),
    base={
        "discharge_m3s": 10.0,
        "slope_m_per_m": 0.001,
        "bottom_width_m": 4.0,
        "side_slope_m_per_m": 2.0,
        "manning_n": 0.035,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (MANNING_NORMAL_FLOW,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def normal_flow(
    discharge_m3s: float,
    slope_m_per_m: float,
    bottom_width_m: float,
    side_slope_m_per_m: float,
    manning_n: float,
) -> NormalFlow:
    """Return the normal flow of a discharge in a channel, spec manning_normal_flow.

    The first input is the discharge in cubic metres per second.

    Parameters
    ----------
    slope_m_per_m : float
        Bed slope, the friction slope of the uniform flow [m/m].
    bottom_width_m : float
        Width of the bottom [m]; zero for a triangle.
    side_slope_m_per_m : float
        Horizontal metres per vertical metre of both banks; zero for a rectangle.
    manning_n : float
        Manning's roughness coefficient, in seconds per cube root of a metre.

    Returns
    -------
    NormalFlow
        The normal depth, the flow area, the top width, the mean velocity and the
        celerity of a kinematic flood wave.

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``): a value outside its
        physical range, a section with neither a bottom nor banks (constraint
        ``has_width``), or a flow that a float cannot hold to its digits
        (``precondition_failed``, constraint ``representable_flow``).
    """
    values = checked_inputs(
        MANNING_NORMAL_FLOW,
        discharge_m3s=discharge_m3s,
        slope_m_per_m=slope_m_per_m,
        bottom_width_m=bottom_width_m,
        side_slope_m_per_m=side_slope_m_per_m,
        manning_n=manning_n,
    )
    out = checked_outputs(MANNING_NORMAL_FLOW, _flow(values))
    return NormalFlow(
        depth_m=out.real("depth_m"),
        area_m2=out.real("area_m2"),
        top_width_m=out.real("top_width_m"),
        velocity_m_per_s=out.real("velocity_m_per_s"),
        celerity_m_per_s=out.real("celerity_m_per_s"),
    )
