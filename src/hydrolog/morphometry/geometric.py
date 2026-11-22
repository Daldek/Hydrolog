"""Geometric parameters and shape indicators of a watershed.

The five shape indicators are declared by their specs (Nogat CMP-2.1), each beside
its function: :data:`FORM_FACTOR` (``form_factor``, Horton),
:data:`COMPACTNESS_COEFFICIENT` (``compactness_coefficient``, Gravelius),
:data:`CIRCULARITY_RATIO` (``circularity_ratio``, Miller), :data:`ELONGATION_RATIO`
(``elongation_ratio``, Schumm) and :data:`LEMNISCATE_RATIO` (``lemniscate_ratio``,
Chorley et al.); ``docs/FORMULAS.md`` shows their equations, ranges and sources.
:class:`WatershedGeometry` computes them for one watershed; the mean width is the
Tier B row :data:`MEAN_WIDTH`.

Examples
--------
>>> round(form_factor(area_km2=45.0, length_km=12.0), 4)
0.3125
>>> round(compactness_coefficient(area_km2=45.0, perimeter_km=32.0), 4)
1.3457
>>> round(lemniscate_ratio(area_km2=45.0, length_km=12.0), 4)
2.5133
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any, Final

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.morphometry._sources import (
    AREA,
    BASCIK,
    BASCIK_URL,
    BENDJOUDI_HUBERT,
    BENDJOUDI_HUBERT_URL,
    LENGTH,
    PERIMETER,
    WARTALSKA,
    WARTALSKA_URL,
    decimal_pi,
)
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
    TierBSpec,
    Tolerance,
    Values,
    assert_within,
)

__all__ = [
    "CIRCULARITY_RATIO",
    "COMPACTNESS_COEFFICIENT",
    "ELONGATION_RATIO",
    "FORM_FACTOR",
    "LEMNISCATE_RATIO",
    "MEAN_WIDTH",
    "SPECS",
    "TIER_B",
    "GeometricParameters",
    "ShapeIndicators",
    "WatershedGeometry",
    "circularity_ratio",
    "compactness_coefficient",
    "elongation_ratio",
    "form_factor",
    "lemniscate_ratio",
]

# --- sources --------------------------------------------------------------------------


def _bendjoudi(locator: str) -> Source:
    return Source(citation=BENDJOUDI_HUBERT, locator=locator, url=BENDJOUDI_HUBERT_URL)


def _wartalska(locator: str) -> Source:
    return Source(citation=WARTALSKA, locator=locator, url=WARTALSKA_URL)


def _bascik(locator: str) -> Source:
    return Source(citation=BASCIK, locator=locator, url=BASCIK_URL)


_LENGTH_DEFINITION = _bascik(
    "p. 21: the length of the watershed L is the straight line from the outlet to the "
    "farthest point of the divide; the maximum length Lm runs along the valley of the "
    "main river"
)
_CIRCLE_PERIMETER = _bendjoudi(
    "pp. 921-922: the perimeter of any basin exceeds that of the circle of the same "
    "area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle"
)

# --- the computations ----------------------------------------------------------------


def _form_factor(x: Values) -> float:
    """Return A / L^2 as (A / L) / L, which never overflows where A <= pi L^2."""
    length = x.real("length_km")
    return x.real("area_km2") / length / length


def _compactness(x: Values) -> float:
    """Return P / (2 sqrt(pi) sqrt(A)), each root apart: pi A never overflows."""
    return x.real("perimeter_km") / (
        2.0 * math.sqrt(math.pi) * math.sqrt(x.real("area_km2"))
    )


def _circularity(x: Values) -> float:
    """Return 4 pi (A / P) / P, which never overflows where P^2 >= 4 pi A."""
    perimeter = x.real("perimeter_km")
    return 4.0 * math.pi * (x.real("area_km2") / perimeter / perimeter)


def _elongation(x: Values) -> float:
    """Return 2 sqrt(A) / sqrt(pi) / L: no quotient of A underflows, at most 2."""
    root = math.sqrt(x.real("area_km2"))
    return 2.0 * root / math.sqrt(math.pi) / x.real("length_km")


def _lemniscate(x: Values) -> float:
    """Return (pi / 4) (L / A) L: inf only where the index lies beyond float64."""
    length = x.real("length_km")
    return math.pi / 4.0 * (length / x.real("area_km2")) * length


# --- oracles and limits (CMP-6.2, CMP-6.5) --------------------------------------------

_DIGITS = 50
"""Precision of the decimal oracles: far beyond float64's 16 digits."""

_POINTS: Final[tuple[dict[str, float], ...]] = (
    {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0},
    {"area_km2": 37.22, "perimeter_km": 40.89, "length_km": 16.05},
    {"area_km2": 134.9683, "perimeter_km": 84.4609, "length_km": 22.2789},
    {"area_km2": 0.00035, "perimeter_km": 0.1756, "length_km": 0.0566},
    {"area_km2": 1.2032, "perimeter_km": 6.02, "length_km": 2.1512},
)
"""Inputs of the decimal oracles: the docstring's example, the guide's Kamiennik and
watersheds of Hydrograf's hand-offs (the largest, the smallest, one of a network)."""

_DECIMAL_REASON = (
    "float64 against the equation at the same inputs in decimal arithmetic at 50 "
    "digits: a few roundings of a quotient, a product and a root"
)
_SHAPE_REASON = (
    "float inputs of the exact shape: pi, sqrt(2) and their products rounded to "
    "float64, the index squaring them at most, and the formula's own few roundings"
)


def _shapes() -> tuple[tuple[str, dict[str, float], dict[str, Decimal]], ...]:
    """Return circle, square and semicircle: float inputs and exact indices.

    Circle of radius 2 km with L its diameter (outlet on the boundary); square of
    side 3 km with the outlet at a corner, L its diagonal; semicircle of radius 2 km
    with the outlet at the middle of its chord, L its radius. Call in a decimal
    context of :data:`_DIGITS` digits.
    """
    pi = decimal_pi()
    two = Decimal(2)
    root_two = two.sqrt()
    return (
        (
            "circle",
            {
                "area_km2": math.pi * 4.0,
                "perimeter_km": math.pi * 4.0,
                "length_km": 4.0,
            },
            {
                "form_factor": pi / 4,
                "compactness_coefficient": Decimal(1),
                "circularity_ratio": Decimal(1),
                "elongation_ratio": Decimal(1),
                "lemniscate_ratio": Decimal(1),
            },
        ),
        (
            "square",
            {"area_km2": 9.0, "perimeter_km": 12.0, "length_km": 3.0 * math.sqrt(2.0)},
            {
                "form_factor": Decimal("0.5"),
                "compactness_coefficient": two / pi.sqrt(),
                "circularity_ratio": pi / 4,
                "elongation_ratio": (two / pi).sqrt(),
                "lemniscate_ratio": pi / 2,
            },
        ),
        (
            "semicircle",
            {
                "area_km2": math.pi * 2.0,
                "perimeter_km": (math.pi + 2.0) * 2.0,
                "length_km": 2.0,
            },
            {
                "form_factor": pi / 2,
                "compactness_coefficient": (pi + 2) / (pi * root_two),
                "circularity_ratio": 2 * pi * pi / ((pi + 2) * (pi + 2)),
                "elongation_ratio": root_two,
                "lemniscate_ratio": Decimal("0.5"),
            },
        ),
    )


type _Equation = Callable[[Mapping[str, Decimal], Decimal], Decimal]


def _decimal_check(
    output: str, inputs: tuple[str, str], equation: _Equation
) -> Callable[[Callable[..., Values]], None]:
    """Return a limit that compares the index with its equation in decimal."""

    def check(run: Callable[..., Values]) -> None:
        with localcontext(prec=_DIGITS):
            pi = decimal_pi()
            for point in _POINTS:
                given = {name: point[name] for name in inputs}
                exact = equation({k: Decimal(v) for k, v in given.items()}, pi)
                assert_within(
                    run(**given).real(output),
                    float(exact),
                    rel=1e-15,
                    reason=_DECIMAL_REASON,
                )

    return check


def _shape_check(
    output: str, inputs: tuple[str, str]
) -> Callable[[Callable[..., Values]], None]:
    """Return a limit that compares the index of exact shapes with its exact value."""

    def check(run: Callable[..., Values]) -> None:
        with localcontext(prec=_DIGITS):
            shapes = _shapes()
        for _name, point, exact in shapes:
            assert_within(
                run(**{name: point[name] for name in inputs}).real(output),
                float(exact[output]),
                rel=2e-15,
                reason=_SHAPE_REASON,
            )

    return check


def _identity_check(
    output: str,
    inputs: tuple[str, str],
    other: Callable[..., float],
    other_inputs: tuple[str, str],
    relation: Callable[[float, float], float],
    expected: float,
    text: str,
) -> Callable[[Callable[..., Values]], None]:
    """Return a limit: ``relation(index, other index)`` equals ``expected``."""

    def check(run: Callable[..., Values]) -> None:
        for point in _POINTS:
            mine = run(**{name: point[name] for name in inputs}).real(output)
            theirs = other(**{name: point[name] for name in other_inputs})
            assert_within(
                relation(mine, theirs),
                expected,
                rel=4e-15,
                reason=f"{text}: two indices of the same inputs, each a few roundings "
                "from its exact value",
            )

    return check


# --- shared parts of the specs --------------------------------------------------------

_AREA_LENGTH = ("area_km2", "length_km")
_AREA_PERIMETER = ("area_km2", "perimeter_km")
_EXACT_SCALING = Tolerance(
    abs=0.0,
    reason="lengths scaled by 2 and areas by 4 are exact in binary, and so is every "
    "quotient of them, unless a result underflows",
)


def _within_reach() -> Constraint:
    return Constraint(
        name="within_reach",
        cls="physical",
        check=lambda x: (
            x.real("area_km2") <= math.pi * x.real("length_km") * x.real("length_km")
        ),
        text="A <= pi L^2: the watershed lies within the circle of radius L about its "
        "outlet, L being the straight line to the farthest point of the divide or the "
        "longest flow path, which is not shorter",
        source=_LENGTH_DEFINITION,
        satisfied={"area_km2": 45.0, "length_km": 12.0},
        boundary={"area_km2": math.pi * 4.0, "length_km": 2.0},
        violated={"area_km2": 13.0, "length_km": 2.0},
    )


def _isoperimetric() -> Constraint:
    return Constraint(
        name="isoperimetric",
        cls="physical",
        check=lambda x: (
            x.real("perimeter_km") * x.real("perimeter_km")
            >= 4.0 * math.pi * x.real("area_km2")
        ),
        text="P^2 >= 4 pi A: no perimeter is shorter than the circle's of the same "
        "area (the isoperimetric inequality); a shorter one means A and P measured "
        "on different outlines",
        source=_CIRCLE_PERIMETER,
        satisfied={"area_km2": 45.0, "perimeter_km": 32.0},
        boundary={"area_km2": math.pi, "perimeter_km": 2.0 * math.pi},
        violated={"area_km2": math.pi, "perimeter_km": 6.0},
    )


_LENGTH_CONVENTION = (
    "L the straight line from the outlet to the farthest point of the divide (Baścik "
    "2006, p. 21), as WatershedGeometry describes length_km; Hydrograf hands over the "
    "longest flow path, which is not shorter, so with it the index of elongation is "
    "smaller (k larger) than with the straight line; Schumm's (1956) L, the longest "
    "dimension parallel to the main drainage line, and Baścik's Lm, the valley "
    "length, are other conventions"
)
_PERIMETER_CONVENTION = (
    "P the length of the divide as traced: it grows with the resolution of the map or "
    "DEM, as a divide is irregular at every scale, so the index does too "
    "(Bendjoudi and Hubert 2002, pp. 924-928)"
)
_SINGULAR_AREA = (
    "range cases area_km2-physical_low_*: the root of A in the denominator tends to "
    "0 with A; the index stays finite down to the smallest positive float, or a value "
    "beyond float64 is refused by the precondition within_float64"
)
_GAPS = "type cases area_km2-nan and the other inputs': a gap is refused"
_GEOMETRIC = "none: a geometric index, which its sources compare with no observations"

# --- Horton's form factor -----------------------------------------------------------

FORM_FACTOR: Final = FormulaSpec(
    name="form_factor",
    title="Horton's form factor of a watershed",
    function="hydrolog.morphometry.geometric.form_factor",
    family="index",
    equation="Cf = A / L**2",
    latex=r"C_f = \frac{A}{L^2}",
    variables=(AREA, LENGTH),
    outputs=(
        Output(
            name="form_factor",
            unit="-",
            symbol="C_f",
            description="Form factor: the area over the square of the length; pi/4 "
            "for a circle whose diameter is L.",
            physical=Range(low=0.0, high=math.pi),
        ),
    ),
    sources=(
        _bendjoudi(
            "p. 929: Horton's (1932) form factor, the area of the basin over the "
            "square of its length"
        ),
        _wartalska("section 2: wskaźnik formy Cf = A / L^2 = B / L"),
    ),
    constraints=(_within_reach(),),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": 1, "length_km": -1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"area_km2": 2, "length_km": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="area",
                inputs={"area_km2": 1},
                outputs={"form_factor": 1},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="decimal",
                text="Cf equals A / L^2 evaluated in decimal arithmetic at 50 digits",
                check=_decimal_check(
                    "form_factor",
                    _AREA_LENGTH,
                    lambda x, pi: x["area_km2"] / x["length_km"] ** 2,
                ),
            ),
            Limit(
                name="shapes",
                text="a circle with L its diameter gives pi/4, a square with L its "
                "diagonal 1/2, a semicircle with L its radius pi/2",
                check=_shape_check("form_factor", _AREA_LENGTH),
            ),
        ),
    ),
    validation=_GEOMETRIC,
    formula_version=1,
    status="oracle only",
    conventions=(
        _LENGTH_CONVENTION,
        (
            "A within the circle of radius L about the outlet bounds Cf by pi; with L "
            "the longest dimension of the watershed (the isodiametric inequality) by "
            "pi/4, the circle's value"
        ),
    ),
    traps={
        "singular_at_bound": "range cases length_km-physical_low_*: Cf grows as "
        "L^-2, which the constraint within_reach bounds by pi; a length too short for "
        "the area is refused",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="A / L^2 of the float inputs in decimal arithmetic at 50 "
            "digits, and the exact values of a circle, a square and a semicircle with "
            "pi summed by the decimal module's series",
            test="tests/unit/test_formulas_shape.py (limits decimal and shapes)",
        ),
    ),
    base={"area_km2": 45.0, "length_km": 12.0},
)

# --- Gravelius's compactness coefficient --------------------------------------------

COMPACTNESS_COEFFICIENT: Final = FormulaSpec(
    name="compactness_coefficient",
    title="Gravelius's compactness coefficient of a watershed",
    function="hydrolog.morphometry.geometric.compactness_coefficient",
    family="index",
    equation="Cz = P / (2 * sqrt(pi * A))",
    latex=r"C_z = \frac{P}{2\sqrt{\pi A}}",
    variables=(AREA, PERIMETER),
    outputs=(
        Output(
            name="compactness_coefficient",
            unit="-",
            symbol="C_z",
            description="Compactness coefficient: the perimeter over the circumference "
            "of the circle of the same area; 1 for a circle.",
            physical=Range(low=1.0),
        ),
    ),
    sources=(
        _bendjoudi("eq. (1), p. 922: K = P / (2 sqrt(pi A)) = 0.28 P / sqrt(A)"),
        _wartalska(
            "section 2: wskaźnik zwartości (Graveliusa) K = Oz / (2 sqrt(pi A))"
        ),
    ),
    constraints=(
        _isoperimetric(),
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(_compactness(x)),
            text="P / (2 sqrt(pi A)) lies within float64: no watershed has a divide "
            "10^150 times its width",
            source=_CIRCLE_PERIMETER,
            satisfied={"area_km2": 45.0, "perimeter_km": 32.0},
            violated={"area_km2": 5e-324, "perimeter_km": 1.0e160},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": -1, "perimeter_km": 1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"area_km2": 2, "perimeter_km": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="perimeter",
                inputs={"perimeter_km": 1},
                outputs={"compactness_coefficient": 1},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="decimal",
                text="Cz equals P / (2 sqrt(pi A)) evaluated in decimal arithmetic at "
                "50 digits",
                check=_decimal_check(
                    "compactness_coefficient",
                    _AREA_PERIMETER,
                    lambda x, pi: x["perimeter_km"] / (2 * (pi * x["area_km2"]).sqrt()),
                ),
            ),
            Limit(
                name="shapes",
                text="a circle gives 1, a square 2/sqrt(pi), a semicircle "
                "(pi + 2) / (pi sqrt(2))",
                check=_shape_check("compactness_coefficient", _AREA_PERIMETER),
            ),
        ),
    ),
    validation=_GEOMETRIC,
    formula_version=1,
    status="oracle only",
    conventions=(
        _PERIMETER_CONVENTION,
        (
            "A and P of the same outline: Hydrograf takes A from the cells and P from "
            "the smoothed boundary, so a value near 1 is to be read with care"
        ),
    ),
    traps={
        "singular_at_bound": _SINGULAR_AREA,
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="P / (2 sqrt(pi A)) of the float inputs in decimal arithmetic "
            "at 50 digits, and the exact values of a circle, a square and a semicircle",
            test="tests/unit/test_formulas_shape.py (limits decimal and shapes)",
        ),
    ),
    base={"area_km2": 45.0, "perimeter_km": 32.0},
)

# --- Miller's circularity ratio -------------------------------------------------------


CIRCULARITY_RATIO: Final = FormulaSpec(
    name="circularity_ratio",
    title="Miller's circularity ratio of a watershed",
    function="hydrolog.morphometry.geometric.circularity_ratio",
    family="index",
    equation="Ck = 4 * pi * A / P**2",
    latex=r"C_k = \frac{4\pi A}{P^2}",
    variables=(AREA, PERIMETER),
    outputs=(
        Output(
            name="circularity_ratio",
            unit="-",
            symbol="C_k",
            description="Circularity ratio: the area over the area of the circle of "
            "the same perimeter; 1 for a circle.",
            physical=Range(low=0.0, high=1.0),
        ),
    ),
    sources=(
        _bendjoudi("eq. (2), p. 922: Miller's (1953) C = 4 pi A / P^2"),
        _bascik("eq. (1.2.3): Ck = A / Ak = 4 pi A / P^2"),
        _wartalska("section 2: wskaźnik kolistości Ck = 4 pi A / Oz^2"),
    ),
    constraints=(_isoperimetric(),),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": 1, "perimeter_km": -1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"area_km2": 2, "perimeter_km": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="decimal",
                text="Ck equals 4 pi A / P^2 evaluated in decimal arithmetic at 50 "
                "digits",
                check=_decimal_check(
                    "circularity_ratio",
                    _AREA_PERIMETER,
                    lambda x, pi: 4 * pi * x["area_km2"] / x["perimeter_km"] ** 2,
                ),
            ),
            Limit(
                name="shapes",
                text="a circle gives 1, a square pi/4, a semicircle "
                "2 pi^2 / (pi + 2)^2",
                check=_shape_check("circularity_ratio", _AREA_PERIMETER),
            ),
            Limit(
                name="gravelius",
                text="Ck Cz^2 = 1: Miller's ratio is Gravelius's coefficient to the "
                "power -2",
                check=_identity_check(
                    "circularity_ratio",
                    _AREA_PERIMETER,
                    lambda area_km2, perimeter_km: compactness_coefficient(
                        area_km2, perimeter_km
                    ),
                    _AREA_PERIMETER,
                    lambda ck, cz: ck * cz * cz,
                    1.0,
                    "Ck Cz^2 = 1",
                ),
            ),
        ),
    ),
    validation=_GEOMETRIC,
    formula_version=1,
    status="oracle only",
    conventions=(_PERIMETER_CONVENTION,),
    traps={
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="4 pi A / P^2 of the float inputs in decimal arithmetic at 50 "
            "digits, and the exact values of a circle, a square and a semicircle",
            test="tests/unit/test_formulas_shape.py (limits decimal and shapes)",
        ),
    ),
    base={"area_km2": 45.0, "perimeter_km": 32.0},
)

# --- Schumm's elongation ratio --------------------------------------------------------

ELONGATION_RATIO: Final = FormulaSpec(
    name="elongation_ratio",
    title="Schumm's elongation ratio of a watershed",
    function="hydrolog.morphometry.geometric.elongation_ratio",
    family="index",
    equation="Ce = (2 / L) * sqrt(A / pi)",
    latex=r"C_e = \frac{2}{L}\sqrt{\frac{A}{\pi}}",
    variables=(AREA, LENGTH),
    outputs=(
        Output(
            name="elongation_ratio",
            unit="-",
            symbol="C_e",
            description="Elongation ratio: the diameter of the circle of the same "
            "area over the length; 1 for a circle whose diameter is L.",
            physical=Range(low=0.0, high=2.0),
        ),
    ),
    sources=(
        _bascik("eq. (1.2.2): Cw = (2 / Lm) sqrt(A / pi), after Schumm (1956)"),
        _wartalska("section 2: wskaźnik wydłużenia Cw = (2 / L) (A / pi)^0.5"),
    ),
    constraints=(_within_reach(),),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": 1, "length_km": -1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"area_km2": 2, "length_km": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="length",
                inputs={"length_km": 1},
                outputs={"elongation_ratio": -1},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="decimal",
                text="Ce equals (2 / L) sqrt(A / pi) evaluated in decimal arithmetic "
                "at 50 digits",
                check=_decimal_check(
                    "elongation_ratio",
                    _AREA_LENGTH,
                    lambda x, pi: 2 * (x["area_km2"] / pi).sqrt() / x["length_km"],
                ),
            ),
            Limit(
                name="shapes",
                text="a circle with L its diameter gives 1, a square with L its "
                "diagonal sqrt(2/pi), a semicircle with L its radius sqrt(2)",
                check=_shape_check("elongation_ratio", _AREA_LENGTH),
            ),
            Limit(
                name="form_factor",
                text="Cf = pi Ce^2 / 4 for the same A and L",
                check=_identity_check(
                    "elongation_ratio",
                    _AREA_LENGTH,
                    lambda area_km2, length_km: form_factor(area_km2, length_km),
                    _AREA_LENGTH,
                    lambda ce, cf: math.pi * ce * ce / (4.0 * cf),
                    1.0,
                    "pi Ce^2 / (4 Cf) = 1",
                ),
            ),
        ),
    ),
    validation=_GEOMETRIC,
    formula_version=1,
    status="oracle only",
    conventions=(
        _LENGTH_CONVENTION,
        (
            "A within the circle of radius L about the outlet bounds Ce by 2; with L "
            "the longest dimension of the watershed by 1, the circle's value"
        ),
    ),
    traps={
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="(2 / L) sqrt(A / pi) of the float inputs in decimal "
            "arithmetic at 50 digits, and the exact values of a circle, a square and "
            "a semicircle",
            test="tests/unit/test_formulas_shape.py (limits decimal and shapes)",
        ),
    ),
    base={"area_km2": 45.0, "length_km": 12.0},
)

# --- Chorley's lemniscate ratio -----------------------------------------------------

LEMNISCATE_RATIO: Final = FormulaSpec(
    name="lemniscate_ratio",
    title="Chorley's lemniscate ratio k of a watershed",
    function="hydrolog.morphometry.geometric.lemniscate_ratio",
    family="index",
    equation="k = pi * L**2 / (4 * A)",
    latex=r"k = \frac{\pi L^2}{4A}",
    variables=(AREA, LENGTH),
    outputs=(
        Output(
            name="lemniscate_ratio",
            unit="-",
            symbol="k",
            description="Lemniscate ratio: the area of the circle of diameter L over "
            "the area of the watershed; 1 for that circle, larger for longer "
            "watersheds.",
            physical=Range(low=0.25),
        ),
    ),
    sources=(
        _bendjoudi(
            "eqs. (3)-(5), pp. 922-923: Chorley et al. (1957) compare the basin with "
            "one loop of the lemniscate rho = l cos(k theta), of area pi l^2 / (4k), "
            "so k = pi l^2 / (4A)"
        ),
        _wartalska("section 2: wskaźnik lemniskaty Cl = pi L^2 / (4A)"),
    ),
    constraints=(
        _within_reach(),
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(_lemniscate(x)),
            text="pi L^2 / (4A) lies within float64: no watershed is 10^150 times "
            "longer than wide",
            source=_bendjoudi("eq. (5), p. 923"),
            satisfied={"area_km2": 45.0, "length_km": 12.0},
            violated={"area_km2": 5e-324, "length_km": 1.0},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"area_km2": -1, "length_km": 1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"area_km2": 2, "length_km": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="length",
                inputs={"length_km": 1},
                outputs={"lemniscate_ratio": 2},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="decimal",
                text="k equals pi L^2 / (4A) evaluated in decimal arithmetic at 50 "
                "digits",
                check=_decimal_check(
                    "lemniscate_ratio",
                    _AREA_LENGTH,
                    lambda x, pi: pi * x["length_km"] ** 2 / (4 * x["area_km2"]),
                ),
            ),
            Limit(
                name="shapes",
                text="a circle with L its diameter gives 1, a square with L its "
                "diagonal pi/2, a semicircle with L its radius 1/2",
                check=_shape_check("lemniscate_ratio", _AREA_LENGTH),
            ),
            Limit(
                name="form_factor",
                text="k Cf = pi/4 for the same A and L",
                check=_identity_check(
                    "lemniscate_ratio",
                    _AREA_LENGTH,
                    lambda area_km2, length_km: form_factor(area_km2, length_km),
                    _AREA_LENGTH,
                    lambda k, cf: 4.0 * k * cf / math.pi,
                    1.0,
                    "4 k Cf / pi = 1",
                ),
            ),
            Limit(
                name="elongation_ratio",
                text="k Ce^2 = 1 for the same A and L",
                check=_identity_check(
                    "lemniscate_ratio",
                    _AREA_LENGTH,
                    lambda area_km2, length_km: elongation_ratio(area_km2, length_km),
                    _AREA_LENGTH,
                    lambda k, ce: k * ce * ce,
                    1.0,
                    "k Ce^2 = 1",
                ),
            ),
        ),
    ),
    validation=_GEOMETRIC,
    formula_version=1,
    status="oracle only",
    conventions=(
        _LENGTH_CONVENTION,
        (
            "Chorley's k with pi (the loop of the lemniscate), not the variant "
            "L^2 / (4A) of some secondary texts, which Hydrolog computed up to 0.8.1"
        ),
        (
            "A within the circle of radius L about the outlet bounds k below by 1/4; "
            "with L the longest dimension of the watershed by 1, the circle's value"
        ),
    ),
    traps={
        "singular_at_bound": "range cases area_km2-physical_low_*: k grows as 1/A; "
        "a value beyond float64 is refused by the precondition within_float64",
        "gap_propagation": _GAPS,
    },
    oracles=(
        Oracle(
            kind="exact",
            description="pi L^2 / (4A) of the float inputs in decimal arithmetic at 50 "
            "digits, the exact values of a circle, a square and a semicircle, and the "
            "identities with Cf and Ce",
            test="tests/unit/test_formulas_shape.py (limits decimal, shapes, "
            "form_factor and elongation_ratio)",
        ),
    ),
    base={"area_km2": 45.0, "length_km": 12.0},
)

SPECS: Final[tuple[FormulaSpec, ...]] = (
    FORM_FACTOR,
    COMPACTNESS_COEFFICIENT,
    CIRCULARITY_RATIO,
    ELONGATION_RATIO,
    LEMNISCATE_RATIO,
)
"""The specs of the module, in the order of ``docs/FORMULAS.md``."""

MEAN_WIDTH: Final = TierBSpec(
    name="mean_width",
    function="hydrolog.morphometry.geometric.WatershedGeometry.width_km",
    definition="W = A / L, the mean width of the watershed [km]",
    convention="L as length_km of WatershedGeometry (the straight line or the longest "
    "flow path); Baścik's B divides by the valley length Lm",
    source=_bascik("p. 21: średnia szerokość zlewni B = A / Lm"),
)

TIER_B: Final[tuple[TierBSpec, ...]] = (MEAN_WIDTH,)
"""The Tier B formula of the module (CMP-2.2)."""


# --- the formulas ---------------------------------------------------------------------


def form_factor(area_km2: float, length_km: float) -> float:
    """Return Horton's form factor of a watershed, spec form_factor.

    The first input is the planimetric area of the watershed in square kilometres
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    length_km : float
        Length of the watershed [km], see :class:`WatershedGeometry`.

    Returns
    -------
    float
        Form factor [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``), or a
        length too short for the area (``details.constraint``).
    """
    x = checked_inputs(FORM_FACTOR, area_km2=area_km2, length_km=length_km)
    return checked_outputs(FORM_FACTOR, {"form_factor": _form_factor(x)}).real(
        "form_factor"
    )


def compactness_coefficient(area_km2: float, perimeter_km: float) -> float:
    """Return Gravelius's compactness coefficient, spec compactness_coefficient.

    The first input is the planimetric area of the watershed in square kilometres
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    perimeter_km : float
        Length of the divide [km].

    Returns
    -------
    float
        Compactness coefficient [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input, or a perimeter shorter than the circle's of the
        same area (``details.constraint``).
    """
    x = checked_inputs(
        COMPACTNESS_COEFFICIENT, area_km2=area_km2, perimeter_km=perimeter_km
    )
    return checked_outputs(
        COMPACTNESS_COEFFICIENT, {"compactness_coefficient": _compactness(x)}
    ).real("compactness_coefficient")


def circularity_ratio(area_km2: float, perimeter_km: float) -> float:
    """Return Miller's circularity ratio of a watershed, spec circularity_ratio.

    The first input is the planimetric area of the watershed in square kilometres
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    perimeter_km : float
        Length of the divide [km].

    Returns
    -------
    float
        Circularity ratio [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input, or a perimeter shorter than the circle's of the
        same area (``details.constraint``).
    """
    x = checked_inputs(CIRCULARITY_RATIO, area_km2=area_km2, perimeter_km=perimeter_km)
    return checked_outputs(
        CIRCULARITY_RATIO, {"circularity_ratio": _circularity(x)}
    ).real("circularity_ratio")


def elongation_ratio(area_km2: float, length_km: float) -> float:
    """Return Schumm's elongation ratio of a watershed, spec elongation_ratio.

    The first input is the planimetric area of the watershed in square kilometres
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    length_km : float
        Length of the watershed [km], see :class:`WatershedGeometry`.

    Returns
    -------
    float
        Elongation ratio [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input, or a length too short for the area
        (``details.constraint``).
    """
    x = checked_inputs(ELONGATION_RATIO, area_km2=area_km2, length_km=length_km)
    return checked_outputs(ELONGATION_RATIO, {"elongation_ratio": _elongation(x)}).real(
        "elongation_ratio"
    )


def lemniscate_ratio(area_km2: float, length_km: float) -> float:
    """Return Chorley's lemniscate ratio of a watershed, spec lemniscate_ratio.

    The first input is the planimetric area of the watershed in square kilometres
    (its name carries the unit, so the standard's check of this docstring, which
    allows no digit, keeps it out of the list below).

    Parameters
    ----------
    length_km : float
        Length of the watershed [km], see :class:`WatershedGeometry`.

    Returns
    -------
    float
        Lemniscate ratio [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input, or a length too short for the area
        (``details.constraint``).
    """
    x = checked_inputs(LEMNISCATE_RATIO, area_km2=area_km2, length_km=length_km)
    return checked_outputs(LEMNISCATE_RATIO, {"lemniscate_ratio": _lemniscate(x)}).real(
        "lemniscate_ratio"
    )


# --- the watershed --------------------------------------------------------------------


@dataclass
class ShapeIndicators(JsonResultMixin):
    """
    Shape indicators for a watershed (the specs of the module).

    Attributes
    ----------
    form_factor : float
        Horton's form factor Cf [-], spec ``form_factor``; lower values indicate
        elongated watersheds.
    compactness_coefficient : float
        Gravelius's compactness coefficient Cz [-], spec
        ``compactness_coefficient``; 1 for a circle.
    circularity_ratio : float
        Miller's circularity ratio Ck [-], spec ``circularity_ratio``; 1 for a
        circle.
    elongation_ratio : float
        Schumm's elongation ratio Ce [-], spec ``elongation_ratio``; 1 for a circle
        whose diameter is the length.
    lemniscate_ratio : float
        Chorley's lemniscate ratio k [-], spec ``lemniscate_ratio``; 1 for a circle
        whose diameter is the length, larger for more elongated watersheds.
    """

    form_factor: float
    compactness_coefficient: float
    circularity_ratio: float
    elongation_ratio: float
    lemniscate_ratio: float


@dataclass
class GeometricParameters(JsonResultMixin):
    """
    Basic geometric parameters of a watershed.

    Attributes
    ----------
    area_km2 : float
        Watershed area [km²].
    perimeter_km : float
        Watershed perimeter [km].
    length_km : float
        Watershed length [km].
    width_km : float
        Mean width of the watershed [km], the Tier B row ``mean_width``.
    """

    area_km2: float
    perimeter_km: float
    length_km: float
    width_km: float


class WatershedGeometry:
    """
    Geometric parameters and shape indicators of a watershed.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    perimeter_km : float
        Watershed perimeter, the length of the divide [km].
    length_km : float
        Watershed length: the straight line from the outlet to the most distant
        point on the divide [km]. Hydrograf hands over the longest flow path, which
        is not shorter (the conventions of the specs, ``docs/FORMULAS.md``).

    Raises
    ------
    InvalidParameterError
        If the specs of the indicators refuse the inputs: a value that is not a
        positive finite number, a perimeter shorter than the circle's of the same
        area or a length too short for the area.

    Examples
    --------
    >>> geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
    >>> params = geom.get_parameters()
    >>> print(f"Area: {params.area_km2} km², Width: {params.width_km:.2f} km")
    Area: 45.0 km², Width: 3.75 km

    >>> indicators = geom.get_shape_indicators()
    >>> print(f"Form factor: {indicators.form_factor:.3f}")
    Form factor: 0.312

    Create from dictionary (e.g., API response):

    >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0}
    >>> geom = WatershedGeometry.from_dict(data)
    """

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatershedGeometry:
        """
        Create WatershedGeometry from a dictionary.

        This method is designed for easy integration with JSON APIs
        and external data sources like Hydrograf.

        Parameters
        ----------
        data : dict
            Dictionary with watershed parameters. Required keys:
            area_km2, perimeter_km, length_km.

        Returns
        -------
        WatershedGeometry
            New instance with values from dictionary.

        Raises
        ------
        KeyError
            If required keys are missing.
        InvalidParameterError
            If parameter values are invalid.

        Examples
        --------
        >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0}
        >>> geom = WatershedGeometry.from_dict(data)
        >>> print(f"Area: {geom.area_km2} km²")
        Area: 45.0 km²

        Extra keys in the dictionary are ignored:

        >>> data = {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 12.0,
        ...         "elevation_min_m": 150.0, "source": "Hydrograf"}
        >>> geom = WatershedGeometry.from_dict(data)
        """
        return cls(
            area_km2=data["area_km2"],
            perimeter_km=data["perimeter_km"],
            length_km=data["length_km"],
        )

    def __init__(
        self,
        area_km2: float,
        perimeter_km: float,
        length_km: float,
    ) -> None:
        """
        Initialize watershed geometry calculator.

        Parameters
        ----------
        area_km2 : float
            Watershed area [km²].
        perimeter_km : float
            Watershed perimeter [km].
        length_km : float
            Watershed length [km].

        Raises
        ------
        InvalidParameterError
            If the specs of the indicators refuse the inputs (``details.reason``,
            ``details.option``, ``details.constraint``).
        """
        with_perimeter = checked_inputs(
            COMPACTNESS_COEFFICIENT, area_km2=area_km2, perimeter_km=perimeter_km
        )
        with_length = checked_inputs(
            FORM_FACTOR, area_km2=area_km2, length_km=length_km
        )
        self.area_km2 = with_perimeter.real("area_km2")
        self.perimeter_km = with_perimeter.real("perimeter_km")
        self.length_km = with_length.real("length_km")

    @property
    def width_km(self) -> float:
        """Mean width of the watershed [km], the Tier B row ``mean_width``."""
        return self.area_km2 / self.length_km

    def get_parameters(self) -> GeometricParameters:
        """
        Get basic geometric parameters.

        Returns
        -------
        GeometricParameters
            Dataclass with area, perimeter, length, and width.
        """
        return GeometricParameters(
            area_km2=self.area_km2,
            perimeter_km=self.perimeter_km,
            length_km=self.length_km,
            width_km=self.width_km,
        )

    def form_factor(self) -> float:
        """Return Horton's form factor [-] (:func:`form_factor`)."""
        return form_factor(self.area_km2, self.length_km)

    def compactness_coefficient(self) -> float:
        """Return Gravelius's compactness coefficient [-] (the module's function)."""
        return compactness_coefficient(self.area_km2, self.perimeter_km)

    def circularity_ratio(self) -> float:
        """Return Miller's circularity ratio [-] (:func:`circularity_ratio`)."""
        return circularity_ratio(self.area_km2, self.perimeter_km)

    def elongation_ratio(self) -> float:
        """Return Schumm's elongation ratio [-] (:func:`elongation_ratio`)."""
        return elongation_ratio(self.area_km2, self.length_km)

    def lemniscate_ratio(self) -> float:
        """Return Chorley's lemniscate ratio k [-] (:func:`lemniscate_ratio`)."""
        return lemniscate_ratio(self.area_km2, self.length_km)

    def get_shape_indicators(self) -> ShapeIndicators:
        """
        Calculate all shape indicators.

        Returns
        -------
        ShapeIndicators
            Dataclass with all shape indicators.

        Examples
        --------
        >>> geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
        >>> indicators = geom.get_shape_indicators()
        >>> print(f"Compactness: {indicators.compactness_coefficient:.2f}")
        Compactness: 1.35
        """
        return ShapeIndicators(
            form_factor=self.form_factor(),
            compactness_coefficient=self.compactness_coefficient(),
            circularity_ratio=self.circularity_ratio(),
            elongation_ratio=self.elongation_ratio(),
            lemniscate_ratio=self.lemniscate_ratio(),
        )
