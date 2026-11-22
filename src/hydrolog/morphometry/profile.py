"""The longitudinal profile of a watercourse: its equal-area slope, declared by a spec.

:data:`EQUAL_AREA_SLOPE` (``equal_area_slope``) declares the slope of the line through
the outlet that leaves equal areas of the profile above and below it, the mean slope of
a main stream in Lutz's estimation of Nash's n and K (KZGW 2017) and in New Zealand's
TM61; ``docs/FORMULAS.md`` shows its equation, ranges and sources (ADR-0053).
:func:`equal_area_slope` computes it from a profile ordered from the outlet upstream.

Examples
--------
A straight profile gives its own slope, a concave one less than the slope between its
ends:

>>> equal_area_slope([0.0, 250.0, 1000.0, 4000.0], [300.0, 305.0, 320.0, 380.0])
0.02
>>> round(equal_area_slope([0.0, 1000.0, 2000.0], [300.0, 302.0, 340.0]), 4)
0.011
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.nogat_formulas import (
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

__all__ = ["EQUAL_AREA_SLOPE", "SPECS", "equal_area_slope"]

_KZGW = Source(
    citation="KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów "
    "maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni "
    "kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)",
    locator="p. 97, the legend of eq. 6.17: Jg, the averaged slope of the main stream, "
    "is the slope of the line from the lowest point of the longitudinal profile for "
    "which the areas between it and the profile, below and above it, are equal",
    url="https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf",
)
_TM61 = Source(
    citation="Ministry of Works and Development, Water and Soil Division (1980). "
    "A method for estimating design peak discharge, Technical Memorandum No. 61, "
    "Wellington",
    locator="appendix A, pp. 12-13: the equal-area method, line AC through the outlet "
    "A with equal areas X and Y; the area under the profile Ad equals the triangle "
    "ABC, so Sa = 2Ad/L^2",
    url="https://web.archive.org/web/20170228021947/http://docs.niwa.co.nz/library/"
    "public/TM61_1980.pdf",
)
_BARBOSA = Source(
    citation="Barbosa Jr., A.R. (2004). Hidrologia Aplicada CIV 226, Bacia "
    "Hidrográfica, Universidade Federal de Ouro Preto, lecture notes",
    locator="section 3.4.4, eqs. 17-18, p. 14: the area under the profile Ap as a sum "
    "of trapezoids and S2 = 2Ap/L^2 - 2z_foz/L",
    url="https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/17403/"
    "material/Cap2%20-%20Bacia%20Hidrografica_UFOP.pdf",
)
_HANDOFFS = (
    "Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November "
    "2026): the hand-offs recorded in Hydrolog's tests and the guide's Kamiennik to "
    "Świerzawa (37.22 km2)"
)
_HANDOFF_FILES = (
    "tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json"
)

# --- the computation -----------------------------------------------------------------


def _slope(x: Values) -> float:
    """Return 2A/L^2 of checked inputs: 0 for no area, NaN or inf beyond float64.

    The trapezoids give twice the area above the outlet as the sum of
    (x[i+1] - x[i]) (h[i] + h[i+1]) with h = z - z[0], so the twos of 2A cancel. The
    steps are divided by the power of two just above L and the pairs of heights by the
    one just above their largest, which is exact, so every term lies below 1 and the
    result depends on the units of the inputs only through those powers: scaled by a
    power of two, a profile gives its slope scaled exactly. A zero length, an infinity
    or an overflow gives NaN or inf, which the precondition ``positive_area`` refuses
    before the formula computes.
    """
    distance = x.array("distance_m")
    elevation = x.array("elevation_m")
    with np.errstate(all="ignore"):
        steps = np.diff(distance)
        height = elevation - elevation[0]
        pairs = height[:-1] + height[1:]
        length = float(distance[-1] - distance[0])
        largest = float(np.max(np.abs(pairs)))
    if not (math.isfinite(length) and length > 0.0 and math.isfinite(largest)):
        return math.nan
    if largest == 0.0:
        return 0.0
    _, length_exponent = math.frexp(length)
    _, height_exponent = math.frexp(largest)
    with np.errstate(all="ignore"):
        terms = np.ldexp(steps, -length_exponent) * np.ldexp(pairs, -height_exponent)
    unit = math.ldexp(length, -length_exponent)
    ratio = math.fsum(terms.tolist()) / (unit * unit)
    try:
        return math.ldexp(ratio, height_exponent - length_exponent)
    except OverflowError:
        return math.inf


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_ORACLE_PROFILES: Final[tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]] = (
    # concave, as streams are: steeper towards the head
    ((0.0, 1000.0, 2500.0, 4000.0, 6000.0), (210.0, 212.5, 221.0, 248.0, 330.0)),
    # convex: steeper towards the outlet
    ((0.0, 500.0, 2000.0, 3500.0), (150.0, 171.0, 190.0, 196.5)),
    # uneven spacing of points, a reach flatter than the outlet's surroundings
    (
        (0.0, 7.07, 54.49, 60.0, 1311.3, 1312.0, 9000.0),
        (258.72, 258.83, 258.83, 259.4, 261.05, 270.0, 312.6),
    ),
    # a short stretch below the outlet, which counts as area below the line
    ((0.0, 100.0, 300.0, 900.0), (500.0, 499.6, 503.0, 540.0)),
)
"""Profiles of the oracles: distance from the outlet [m] and elevation [m]."""


def _exact_slope(distance: Sequence[float], elevation: Sequence[float]) -> Fraction:
    """2A/L^2 of float inputs in exact rational arithmetic."""
    x = [Fraction(value) for value in distance]
    z = [Fraction(value) for value in elevation]
    twice_area = sum(
        (x[i + 1] - x[i]) * (z[i] + z[i + 1] - 2 * z[0]) for i in range(len(x) - 1)
    )
    return Fraction(twice_area) / (x[-1] - x[0]) ** 2


def _exact_rational(run: Callable[..., Values]) -> None:
    for distance, elevation in _ORACLE_PROFILES:
        assert_within(
            run(distance_m=list(distance), elevation_m=list(elevation)).real(
                "slope_m_per_m"
            ),
            float(_exact_slope(distance, elevation)),
            rel=4e-15,
            reason="the exact rational slope of the float inputs: each term carries "
            "the roundings of a difference, a sum and a product, L^2 two and the "
            "quotient one, a few units of 2^-53 relative; the stretch below the outlet "
            "cancels less than a fifth of the area",
        )


def _signed_areas(
    distance: Sequence[float], height: Sequence[float], slope: float
) -> tuple[float, float]:
    """Return the areas of the profile above and below the line h = slope (x - x0).

    Each segment is cut where it crosses the line, so the two areas are summed apart,
    as the sources' construction draws them (TM61, appendix A: areas X and Y).
    """
    above: list[float] = []
    below: list[float] = []
    for i in range(len(distance) - 1):
        width = distance[i + 1] - distance[i]
        left = height[i] - slope * (distance[i] - distance[0])
        right = height[i + 1] - slope * (distance[i + 1] - distance[0])
        if left >= 0.0 and right >= 0.0:
            above.append(width * (left + right) / 2.0)
        elif left <= 0.0 and right <= 0.0:
            below.append(-width * (left + right) / 2.0)
        else:
            cut = width * left / (left - right)
            first, second = cut * left / 2.0, (width - cut) * right / 2.0
            above.append(max(first, second))
            below.append(-min(first, second))
    return math.fsum(above), math.fsum(below)


def _equal_areas_slope(distance: Sequence[float], elevation: Sequence[float]) -> float:
    """Return the slope whose line through the outlet leaves equal areas (bisection)."""
    height = [value - elevation[0] for value in elevation]
    steepest = max(
        abs(h) / (x - distance[0])
        for x, h in zip(distance[1:], height[1:], strict=True)
    )
    low, high = 0.0, 2.0 * steepest
    for _ in range(200):
        middle = (low + high) / 2.0
        if middle in (low, high):
            break
        above, below = _signed_areas(distance, height, middle)
        if above > below:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _equal_areas(run: Callable[..., Values]) -> None:
    for distance, elevation in _ORACLE_PROFILES:
        assert_within(
            run(distance_m=list(distance), elevation_m=list(elevation)).real(
                "slope_m_per_m"
            ),
            _equal_areas_slope(distance, elevation),
            rel=1e-12,
            reason="the line found by bisection to the last bit of its slope, its "
            "areas above and below summed apart over segments cut at the crossings: "
            "each split area carries a few roundings relative to the whole area",
        )


def _two_points(run: Callable[..., Values]) -> None:
    for distance, elevation in (
        ((0.0, 1500.0), (200.0, 245.0)),
        ((1200.0, 1500.25), (812.5, 813.0)),
        ((0.0, 0.001), (100.0, 100.00001)),
    ):
        drop = elevation[1] - elevation[0]
        length = distance[1] - distance[0]
        assert_within(
            run(distance_m=list(distance), elevation_m=list(elevation)).real(
                "slope_m_per_m"
            ),
            drop / length,
            rel=4e-16,
            reason="a single segment: the line from its outlet ends at its head, so "
            "the slope is the drop over the length; L dz / L^2 against dz / L, two "
            "roundings apart",
        )


# --- the spec ------------------------------------------------------------------------

_DISTANCE_TEST = 1.0e6
_DISTANCE_REASON = (
    "1,000 km, about the length of the Vistula, the longest river of Poland: no flow "
    "path of a Polish watershed is longer"
)
_ELEVATION_REASON = (
    "the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and "
    "Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of "
    "Jordan and Nepal)"
)
_EXACT_SCALING = Tolerance(
    abs=2.2250738585072014e-308,
    reason="the profile is divided by powers of two before it is summed, so a power "
    "of two scales the slope exactly, except a slope below the smallest normal float, "
    "2.2e-308, which rounds to fewer digits",
)

EQUAL_AREA_SLOPE: Final = FormulaSpec(
    name="equal_area_slope",
    title="Equal-area slope of a longitudinal profile (the line through the outlet "
    "with equal areas above and below it)",
    function="hydrolog.morphometry.profile.equal_area_slope",
    family="index",
    equation=(
        "S = 2 A / L**2 with A = sum((x[i+1] - x[i]) * (h[i] + h[i+1]) / 2), "
        "h = z - z[0], L = x[-1] - x[0] [m/m]"
    ),
    latex=(
        r"S = \frac{2A}{L^2},\quad A = \sum_{i} \frac{(x_{i+1} - x_i)\,"
        r"(h_i + h_{i+1})}{2},\quad h_i = z_i - z_0,\quad L = x_n - x_0"
    ),
    variables=(
        Variable(
            name="distance_m",
            symbol="x",
            unit="m",
            kind="real_array",
            description="Distance along the profile from the outlet (the first point) "
            "upstream to each point; any origin, as only differences count.",
            physical=Range(
                low=0.0, test_high=_DISTANCE_TEST, test_reason=_DISTANCE_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=0.0,
                high=30000.0,
                source=Source(
                    citation=_HANDOFFS,
                    locator=f"{_HANDOFF_FILES}: flow paths of 0.0566 to 28.88 km",
                ),
            ),
            min_length=2,
        ),
        Variable(
            name="elevation_m",
            symbol="z",
            unit="m",
            kind="real_array",
            description="Elevation of each point of the profile, the bed or the filled "
            "DEM along the flow path; the first is the outlet's.",
            physical=Range(
                test_low=-431.0, test_high=8849.0, test_reason=_ELEVATION_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=100.0,
                high=750.0,
                source=Source(
                    citation=_HANDOFFS,
                    locator=f"{_HANDOFF_FILES}: elevations of 100.0 to 722.68 m",
                ),
            ),
            min_length=2,
        ),
    ),
    outputs=(
        Output(
            name="slope_m_per_m",
            unit="m/m",
            symbol="S",
            description="Slope of the line through the outlet that leaves equal areas "
            "of the profile above and below it.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(_KZGW, _TM61, _BARBOSA),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: x.array("distance_m").shape == x.array("elevation_m").shape,
            text="one elevation per distance",
            source=_BARBOSA,
            satisfied={"distance_m": [0.0, 1000.0], "elevation_m": [300.0, 320.0]},
            violated={
                "distance_m": [0.0, 1000.0, 2000.0],
                "elevation_m": [300.0, 320.0],
            },
        ),
        Constraint(
            name="distance_not_decreasing",
            cls="physical",
            check=lambda x: bool(np.all(np.diff(x.array("distance_m")) >= 0.0)),
            text="x[i+1] >= x[i]: the profile runs from the outlet upstream; a "
            "repeated distance is a vertical step",
            source=_BARBOSA,
            satisfied={
                "distance_m": [0.0, 1000.0, 2000.0],
                "elevation_m": [300.0, 320.0, 350.0],
            },
            boundary={
                "distance_m": [0.0, 1000.0, 1000.0],
                "elevation_m": [300.0, 320.0, 350.0],
            },
            violated={
                "distance_m": [0.0, 1000.0, 999.0],
                "elevation_m": [300.0, 320.0, 350.0],
            },
        ),
        Constraint(
            name="positive_area",
            cls="precondition",
            check=lambda x: 0.0 < _slope(x) < math.inf,
            text="0 < 2 A / L**2 < inf: the profile lies above its outlet on the whole "
            "(A > 0) over a length L > 0, and float64 holds both",
            source=_TM61,
            satisfied={
                "distance_m": [0.0, 1000.0, 2000.0],
                "elevation_m": [300.0, 300.5, 340.0],
            },
            boundary={
                "distance_m": [0.0, 1000.0, 2000.0],
                "elevation_m": [300.0, 300.0, 300.0],
            },
            boundary_holds=False,
            violated={
                "distance_m": [0.0, 1000.0, 2000.0],
                "elevation_m": [300.0, 299.0, 299.5],
            },
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="both_axes",
                inputs={"distance_m": 1, "elevation_m": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="elevation",
                inputs={"elevation_m": 1},
                outputs={"slope_m_per_m": 1},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="distance",
                inputs={"distance_m": 1},
                outputs={"slope_m_per_m": -1},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="straight_profile",
                text="a straight profile gives its own slope",
                inputs={
                    "distance_m": [0.0, 250.0, 1000.0, 4000.0],
                    "elevation_m": [300.0, 305.0, 320.0, 380.0],
                },
                expected={"slope_m_per_m": 0.02},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="whole numbers: the sum 320,000 and L^2 16,000,000 are "
                    "exact, and their quotient is the float nearest 0.02",
                ),
            ),
            Limit(
                name="two_points",
                text="a profile of two points gives the drop over the length",
                check=_two_points,
            ),
            Limit(
                name="exact_rational",
                text="S equals 2A/L^2 of the float inputs in exact rational arithmetic",
                check=_exact_rational,
            ),
            Limit(
                name="equal_areas",
                text="the line through the outlet at slope S leaves equal areas of the "
                "profile above and below it, found by bisection",
                check=_equal_areas,
            ),
        ),
    ),
    validation=(
        "none: the equal-area slope defines the mean slope of a profile (TM61, "
        "appendix A; KZGW 2017, p. 97); its sources compare it with no observations, "
        "and TM61 (p. 12) notes that in practice it gives results largely independent "
        "of the user"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "the profile is ordered from the outlet upstream: x the distance along the "
            "flow path in m from any origin, as only differences count, z the "
            "elevation in m; L is the last distance minus the first"
        ),
        (
            "the line passes through the first point, the outlet, at its elevation: "
            "TM61 draws it through the outlet A, KZGW (2017, p. 97) from the lowest "
            "point of the profile, which the outlet of a flow path on a filled DEM is; "
            "a stretch below the outlet counts as area below the line, so A is the "
            "signed area of z - z[0]"
        ),
        (
            "A by the trapezoid rule, the profile straight between its points "
            "(Barbosa Jr., eq. 17); the triangle under the line, L (S L) / 2, equals "
            "A, so the areas of the profile above and below the line are equal (TM61, "
            "Sa = 2Ad/L^2)"
        ),
        "S in m/m, not in percent or per mille",
        (
            "Lutz's Jg (KZGW 2017, p. 97) is this slope of the longitudinal profile of "
            "the main stream from the divide to the outlet, the longest flow path "
            "(WatershedParameters.flow_path_equal_area_slope_m_per_m); the slope "
            "between the ends of that path (flow_path_slope_m_per_m), Kirpich's S, is "
            "larger on a concave profile and no substitute for it"
        ),
    ),
    assumptions=(
        (
            "the points are those of one flow path where the elevation is known: the "
            "cells of a D8 path on a filled DEM or surveyed points; a run of points of "
            "equal elevation may be thinned to its ends without changing A"
        ),
        (
            "a profile from a filled DEM has no point below its outlet; a surveyed "
            "bed may have pools below it, which reduce A"
        ),
    ),
    traps={
        "difference_denominator": "L = x[-1] - x[0]: a profile of equal distances "
        "has L = 0 and is refused by the precondition positive_area "
        "(test_a_profile_without_length_is_refused)",
        "singular_at_bound": "S grows as 1/L^2: a profile of 1 mm is finite, one "
        "whose L^2 underflows is refused by the precondition positive_area "
        "(test_a_tiny_profile_is_finite_or_refused)",
        "gap_propagation": "type cases distance_m-nan_element and "
        "elevation_m-nan_element: a gap is refused, the spec allows none",
        "many_small_terms": "test_a_profile_of_many_points_matches_its_exact_sum: "
        "100,001 points against the exact rational sum",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="2A/L^2 of the float inputs in exact rational arithmetic "
            "(fractions), rounded once",
            test="tests/unit/test_formulas_equal_area_slope.py (limit exact_rational, "
            "the Kamiennik profile, trap many_small_terms)",
        ),
        Oracle(
            kind="algorithm",
            description="the sources' construction: the line through the outlet whose "
            "slope bisection moves until the profile's areas above and below it, "
            "summed apart over the segments cut where they cross it, are equal",
            test="tests/unit/test_formulas_equal_area_slope.py (limit equal_areas, the "
            "Kamiennik profile)",
        ),
    ),
)

SPECS: Final[tuple[FormulaSpec, ...]] = (EQUAL_AREA_SLOPE,)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""


def equal_area_slope(
    distance_m: NDArray[np.float64] | Sequence[float],
    elevation_m: NDArray[np.float64] | Sequence[float],
) -> float:
    """Return the equal-area slope of a longitudinal profile, spec equal_area_slope.

    Parameters
    ----------
    distance_m : array_like
        Distance of each point of the profile along the flow path, from the outlet
        upstream [m].
    elevation_m : array_like
        Elevation of each point [m], the outlet's first.

    Returns
    -------
    float
        The slope of the line through the outlet that leaves equal areas of the
        profile above and below it [m/m].

    Raises
    ------
    InvalidParameterError
        If the profile is refused by the spec: a value that is not finite, arrays of
        different lengths, a distance that steps back, or a profile that does not
        rise above its outlet on the whole.
    """
    x = checked_inputs(EQUAL_AREA_SLOPE, distance_m=distance_m, elevation_m=elevation_m)
    return checked_outputs(EQUAL_AREA_SLOPE, {"slope_m_per_m": _slope(x)}).real(
        "slope_m_per_m"
    )
