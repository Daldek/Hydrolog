"""Spatial interpolation methods for precipitation data.

The areal precipitation of gauges and isohyets is declared by specs (Nogat's
computation standard, ADR-0050, ADR-0067): :data:`AREAL_MEAN`
(``areal_mean_precipitation``), :data:`THIESSEN` (``thiessen_precipitation``),
:data:`IDW` (``idw_precipitation``) and :data:`ISOHYET` (``isohyet_precipitation``),
with the mean of the IDW values of a grid in the Tier B table (``idw_grid_mean``);
``docs/FORMULAS.md`` shows their equations, ranges and sources. The functions of
earlier versions, :func:`arithmetic_mean`, :func:`thiessen_polygons`,
:func:`inverse_distance_weighting`, :func:`areal_precipitation_idw` and
:func:`isohyet_method`, keep their interface and refusals and compute through them.

Chow, Maidment and Mays (1988, Fig. 3.4.3c) and the inverse squares of distance of
Example 3.7 of NPTEL's Hydrology (IIT Roorkee):

>>> zones_km2 = [0.88, 1.59, 2.24, 3.01, 1.22, 0.20]
>>> round(isohyet_precipitation([0, 10, 20, 30, 40, 50, 56], zones_km2), 1)
27.9
>>> gauges = ([28.0, 17.7, 42.5], [0, 0, 0], [98.9, 120.5, 110.0])
>>> at_a = idw_precipitation(*gauges, 0, 0, 2)
>>> round(at_a.point_precipitation_mm, 1)
113.9
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
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
    Source,
    Symmetry,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
)

ArrayLike = NDArray[np.float64] | Sequence[float]
"""An array of real numbers: a NumPy array, a list or a tuple."""


@dataclass
class Station(JsonResultMixin):
    """
    Precipitation measurement station.

    Attributes
    ----------
    station_id : str
        Unique identifier for the station.
    x : float
        X coordinate (easting) of the station. Must be in a consistent
        coordinate system with other stations. The unit (e.g., meters
        or kilometers) directly affects distance calculations in IDW
        interpolation.
    y : float
        Y coordinate (northing) of the station. Must use the same
        coordinate system and unit as ``x``.
    precipitation_mm : float
        Measured precipitation [mm].
    elevation_m : float, optional
        Station elevation [m a.s.l.].
    """

    station_id: str
    x: float
    y: float
    precipitation_mm: float
    elevation_m: float | None = None


@dataclass
class ThiessenResult(JsonResultMixin):
    """
    Result of Thiessen polygon interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Weighted average precipitation [mm].
    station_weights : dict[str, float]
        Weight (fraction of area) for each station.
    station_contributions_mm : dict[str, float]
        Precipitation contribution from each station [mm].
    """

    areal_precipitation_mm: float
    station_weights: dict[str, float]
    station_contributions_mm: dict[str, float]


@dataclass
class IDWResult(JsonResultMixin):
    """
    Result of IDW interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Interpolated precipitation value [mm].
    station_weights : dict[str, float]
        Weight assigned to each station.
    power : float
        Power parameter used for interpolation.
    """

    areal_precipitation_mm: float
    station_weights: dict[str, float]
    power: float


@dataclass
class IsohyetResult(JsonResultMixin):
    """
    Result of isohyet method interpolation.

    Attributes
    ----------
    areal_precipitation_mm : float
        Weighted average precipitation [mm].
    isohyet_values_mm : NDArray[np.float64]
        Isohyet contour values [mm].
    area_fractions : NDArray[np.float64]
        Fraction of area between isohyets.
    """

    areal_precipitation_mm: float
    isohyet_values_mm: NDArray[np.float64]
    area_fractions: NDArray[np.float64]


@dataclass(frozen=True)
class GaugeWeights(JsonResultMixin):
    """Areal precipitation of the gauges' polygons (spec ``thiessen_precipitation``).

    Attributes
    ----------
    areal_precipitation_mm : float
        Areal precipitation [mm].
    weights : numpy.ndarray
        Weight of each gauge, in the order of the gauges.
    """

    areal_precipitation_mm: float
    weights: NDArray[np.float64]


@dataclass(frozen=True)
class PointEstimate(JsonResultMixin):
    """Precipitation at a point by inverse distances (spec ``idw_precipitation``).

    Attributes
    ----------
    point_precipitation_mm : float
        Precipitation at the target point [mm].
    weights : numpy.ndarray
        Weight of each gauge, in the order of the gauges.
    """

    point_precipitation_mm: float
    weights: NDArray[np.float64]


# --- the specs (Nogat's computation standard, ADR-0050, ADR-0067) ---------------------

_CHOW = (
    "Chow, V.T., Maidment, D.R. and Mays, L.W. (1988). Applied Hydrology. McGraw-Hill, "
    "New York"
)
_CHOW_URL = "https://ponce.sdsu.edu/Applied_Hydrology_Chow_1988.pdf"
_KZGW = (
    "KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych "
    "o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i "
    "niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona)"
)
_KZGW_URL = (
    "https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/"
    "zal-2-do-OPZ-ujednolicony-1.pdf"
)
_WORLD_RECORD = (
    "the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January "
    "1966 (WMO Archive of Weather and Climate Extremes)"
)
_LAND = "the land area of the Earth, about 149 million km2"
_DEPTHS_IN_USE = Source(
    citation="Hydrograf's areal PMAXTP depth (Thiessen cells of the PMAXTP grid points "
    "of a catchment) over the depths of Hydrolog's PMAXTP fixtures for Kamiennik and "
    "Warsaw (POT, recorded in November 2026)",
    locator="tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: "
    "6.96 to 341.27 mm",
)
_GAUGE_DEPTHS: Final = Variable(
    name="precipitation_mm",
    symbol="P_i",
    unit="mm",
    kind="real_array",
    description="Depth at each gauge.",
    physical=Range(low=0.0, test_high=1825.0, test_reason=_WORLD_RECORD),
    applicability="unstated",
    typical=Range(low=6.96, high=341.27, source=_DEPTHS_IN_USE),
)
_AREAL: Final = Output(
    name="areal_precipitation_mm",
    unit="mm",
    symbol=r"\bar{P}",
    description="Mean precipitation over the watershed.",
    physical=Range(low=0.0),
)
_WEIGHTS: Final = Output(
    name="weights",
    unit="-",
    kind="real_array",
    symbol="w_i",
    description="Weight of each gauge, summing to one.",
    physical=Range(low=0.0, high=1.0),
)
_DOUBLED: Final = Tolerance(
    rel=1e-15,
    abs=1e-300,
    reason="doubling the depths doubles every product exactly in binary; the sums "
    "round once, but for subnormal values",
)
_SAME_SUM: Final = Tolerance(
    rel=1e-12,
    abs=1e-12,
    reason="the same terms summed in another order: correctly rounded sums of "
    "products that each round once",
)
_WEIGHTS_ADD_UP: Final = Conservation(
    name="weights_add_up",
    text="the weights sum to one",
    residual=lambda x, out: math.fsum(out.array("weights")) - 1.0,
    tolerance=Tolerance(
        abs=1e-12,
        reason="each weight is a quotient rounded once; a few units in the last place "
        "of one per weight, for up to a few hundred gauges",
    ),
)


def _reversed(names: tuple[str, ...]) -> Callable[[Values], dict[str, object]]:
    """Return the inputs with the arrays ``names`` in reverse order."""

    def turned(x: Values) -> dict[str, object]:
        return {**x, **{name: x.array(name)[::-1] for name in names}}

    return turned


def _same(name: str) -> Callable[[Values], dict[str, object]]:
    """Return the output ``name`` unchanged, as a symmetry expects it."""
    return lambda out: {name: out.real(name)}


# --- arithmetic mean -----------------------------------------------------------------


def _mean(x: Values) -> dict[str, object]:
    depths = x.array("precipitation_mm")
    return {"areal_precipitation_mm": math.fsum(depths) / len(depths)}


def _mean_exact(run: Callable[..., Values]) -> None:
    for depths in ([20.0, 30.0, 40.0, 50.0], [31.2, 36.8, 28.4], [0.1] * 7):
        exact = sum((Fraction(d) for d in depths), Fraction(0)) / len(depths)
        assert_within(
            run(precipitation_mm=depths).real("areal_precipitation_mm"),
            float(exact),
            rel=1.2e-16,
            reason="the mean in exact rational arithmetic, rounded once to float64: "
            "math.fsum rounds the sum once and the quotient once more",
        )


_CHOW_GAUGES = Source(
    citation=_CHOW,
    locator="sec. 3.4 Areal rainfall, Fig. 3.4.3, pp. 78-80: the gauges of the "
    "example, 10 to 50 mm",
    url=_CHOW_URL,
)

AREAL_MEAN: Final = FormulaSpec(
    name="areal_mean_precipitation",
    title="Areal precipitation by the arithmetic mean of the gauges",
    function="hydrolog.precipitation.interpolation.areal_mean_precipitation",
    family="statistic",
    equation="P = (P_1 + ... + P_n) / n over the gauges in the watershed",
    latex=r"\bar{P} = \frac{1}{n}\sum_{i=1}^{n} P_i",
    variables=(_GAUGE_DEPTHS,),
    outputs=(_AREAL,),
    sources=(
        Source(
            citation=_CHOW,
            locator="sec. 3.4, Fig. 3.4.3(a), p. 78: the arithmetic mean of the gauges "
            "within the watershed",
            url=_CHOW_URL,
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"precipitation_mm": 1},
        scalings=(
            Scaling(
                name="depth",
                inputs={"precipitation_mm": 1},
                outputs={"areal_precipitation_mm": 1},
                tolerance=_DOUBLED,
            ),
        ),
        symmetries=(
            Symmetry(
                name="order",
                text="the order of the gauges does not matter",
                inputs=_reversed(("precipitation_mm",)),
                outputs=_same("areal_precipitation_mm"),
                tolerance=_SAME_SUM,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the mean equals the mean in exact rational arithmetic",
                check=_mean_exact,
            ),
        ),
    ),
    validation=(
        "Chow et al. (1988, p. 78) find the method satisfactory where the gauges are "
        "uniformly spread over flat terrain; no error statistic"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "depths in mm; only the gauges within the watershed are given (Chow et al. "
        "1988 leave out the gauges outside it)",
        "the sum by math.fsum, correctly rounded",
    ),
    traps={
        "gap_propagation": "type case precipitation_mm-nan_element: a gap is refused",
        "many_small_terms": "limit exact_rational: seven depths of 0.1 mm against "
        "the exact rational mean",
    },
    reference_cases=("tests/fixtures/formulas/areal-precipitation-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the mean in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_areal_precipitation.py (limit "
            "exact_rational)",
        ),
    ),
)


def areal_mean_precipitation(precipitation_mm: ArrayLike) -> float:
    """Return the arithmetic mean of the gauges, spec areal_mean_precipitation.

    Parameters
    ----------
    precipitation_mm : array_like of float
        Depth at each gauge within the watershed [mm].

    Returns
    -------
    float
        Areal precipitation [mm].

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(AREAL_MEAN, precipitation_mm=precipitation_mm)
    return checked_outputs(AREAL_MEAN, _mean(x)).real("areal_precipitation_mm")


# --- Thiessen polygons ---------------------------------------------------------------


def _thiessen(x: Values) -> dict[str, object]:
    areas = x.array("polygon_areas_km2")
    weights = areas / math.fsum(areas)
    return {
        "areal_precipitation_mm": math.fsum(weights * x.array("precipitation_mm")),
        "weights": weights,
    }


def _weighted_exact(depths: list[float], areas: list[float]) -> float:
    total = sum((Fraction(a) for a in areas), Fraction(0))
    weighted = sum(
        (Fraction(d) * Fraction(a) for d, a in zip(depths, areas, strict=True)),
        Fraction(0),
    )
    return float(weighted / total)


def _thiessen_exact(run: Callable[..., Values]) -> None:
    for depths, areas in (
        ([10.0, 20.0, 30.0, 40.0, 50.0], [0.22, 4.02, 1.35, 1.6, 1.95]),
        ([31.2, 36.8, 28.4], [18.5, 14.2, 12.6]),
        ([12.0, 0.0, 7.5], [0.0, 3.0, 1.0]),
    ):
        assert_within(
            run(precipitation_mm=depths, polygon_areas_km2=areas).real(
                "areal_precipitation_mm"
            ),
            _weighted_exact(depths, areas),
            rel=1e-15,
            reason="the weighted mean in exact rational arithmetic; float64 rounds "
            "each weight and product once and math.fsum the sums",
        )


def _equal_areas(run: Callable[..., Values]) -> None:
    depths = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert_within(
        run(precipitation_mm=depths, polygon_areas_km2=[2.0] * 5).real(
            "areal_precipitation_mm"
        ),
        30.0,
        rel=1e-15,
        reason="equal polygons give the arithmetic mean; a weight of 0.2 rounds once",
    )


def _gauge_count(x: Values) -> bool:
    return len(x.array("precipitation_mm")) == len(x.array("polygon_areas_km2"))


def _area_positive(name: str) -> Callable[[Values], bool]:
    return lambda x: math.fsum(x.array(name)) > 0.0


_CHOW_B = Source(
    citation=_CHOW,
    locator="sec. 3.4, eq. 3.4.1 and Fig. 3.4.3(b), pp. 78-79: the polygons of the "
    "example, 0.22 to 4.02 km2",
    url=_CHOW_URL,
)
_CHOW_DEPTHS = (10.0, 20.0, 30.0, 40.0, 50.0)
_CHOW_AREAS = (0.22, 4.02, 1.35, 1.6, 1.95)

THIESSEN: Final = FormulaSpec(
    name="thiessen_precipitation",
    title="Areal precipitation by the Thiessen polygons of the gauges",
    function="hydrolog.precipitation.interpolation.thiessen_precipitation",
    family="statistic",
    equation="P = sum(A_i P_i) / sum(A_i); w_i = A_i / sum(A_i)",
    latex=r"\bar{P} = \frac{\sum_i A_i P_i}{\sum_i A_i},\quad w_i = "
    r"\frac{A_i}{\sum_j A_j}",
    variables=(
        _GAUGE_DEPTHS,
        Variable(
            name="polygon_areas_km2",
            symbol="A_i",
            unit="km2",
            kind="real_array",
            description="Area of each gauge's polygon within the watershed.",
            physical=Range(low=0.0, test_high=1.49e8, test_reason=_LAND),
            applicability="unstated",
            typical=Range(low=0.22, high=4.02, source=_CHOW_B),
        ),
    ),
    outputs=(_AREAL, _WEIGHTS),
    sources=(
        _CHOW_B,
        Source(
            citation=_KZGW,
            locator="ch. II.1, eq. 2.1, pp. 15-16: metoda wieloboków równego opadu "
            "(after Byczkowski 1996)",
            url=_KZGW_URL,
        ),
        Source(
            citation="Thiessen, A.H. (1911). Precipitation averages for large areas. "
            "Monthly Weather Review 39(7), 1082-1084",
            access="author-provided",
        ),
    ),
    constraints=(
        Constraint(
            name="gauge_count",
            cls="precondition",
            check=_gauge_count,
            text="one polygon area for each gauge",
            source=_CHOW_B,
            satisfied={"polygon_areas_km2": list(_CHOW_AREAS)},
            violated={"polygon_areas_km2": [0.22, 4.02]},
        ),
        Constraint(
            name="area_positive",
            cls="precondition",
            check=_area_positive("polygon_areas_km2"),
            text="sum(A_i) > 0: the polygons cover some of the watershed",
            source=_CHOW_B,
            satisfied={"polygon_areas_km2": list(_CHOW_AREAS)},
            violated={"polygon_areas_km2": [0.0] * 5},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"precipitation_mm": 1},
        scalings=(
            Scaling(
                name="depth",
                inputs={"precipitation_mm": 1},
                outputs={"areal_precipitation_mm": 1},
                tolerance=_DOUBLED,
            ),
            Scaling(
                name="area",
                inputs={"polygon_areas_km2": 1},
                outputs={},
                tolerance=_DOUBLED,
            ),
        ),
        conservation=(_WEIGHTS_ADD_UP,),
        symmetries=(
            Symmetry(
                name="order",
                text="the order of the gauges does not matter",
                inputs=_reversed(("precipitation_mm", "polygon_areas_km2")),
                outputs=_same("areal_precipitation_mm"),
                tolerance=_SAME_SUM,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the weighted mean equals it in exact rational arithmetic",
                check=_thiessen_exact,
            ),
            Limit(
                name="equal_areas",
                text="equal polygons give the arithmetic mean",
                check=_equal_areas,
            ),
        ),
    ),
    validation=(
        "none: Chow et al. (1988, p. 78) describe the method as more accurate than the "
        "arithmetic mean where the gauges are unevenly spread, without an error "
        "statistic"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "depths in mm, areas in km2 (any one unit gives the same mean)",
        (
            "the weights are the areas over their sum: KZGW (2017, eq. 2.1) divides by "
            "the area of the watershed, the same when the polygons tile it"
        ),
        "the polygons are given; drawing them is not part of the formula",
    ),
    traps={
        "gap_propagation": "type cases precipitation_mm-nan_element and "
        "polygon_areas_km2-nan_element: a gap is refused",
        "many_small_terms": "the sums by math.fsum; limit exact_rational",
    },
    reference_cases=("tests/fixtures/formulas/areal-precipitation-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the weighted mean in exact rational arithmetic (fractions)",
            test="tests/unit/test_formulas_areal_precipitation.py (limit "
            "exact_rational)",
        ),
    ),
    base={
        "precipitation_mm": list(_CHOW_DEPTHS),
        "polygon_areas_km2": list(_CHOW_AREAS),
    },
)


def thiessen_precipitation(
    precipitation_mm: ArrayLike, polygon_areas_km2: ArrayLike
) -> GaugeWeights:
    """Return the areal precipitation of Thiessen polygons, spec thiessen_precipitation.

    The second input gives the area of each gauge's polygon within the watershed in
    square kilometres, in the order of the gauges (its name carries the unit, so the
    standard's check of this docstring, which allows no digit, keeps it out of the
    list below).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Depth at each gauge [mm].

    Returns
    -------
    GaugeWeights
        The areal precipitation and the weight of each gauge.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        THIESSEN, precipitation_mm=precipitation_mm, polygon_areas_km2=polygon_areas_km2
    )
    out = checked_outputs(THIESSEN, _thiessen(x))
    return GaugeWeights(
        areal_precipitation_mm=out.real("areal_precipitation_mm"),
        weights=out.array("weights"),
    )


# --- inverse distance weighting -------------------------------------------------------

_COINCIDENT_M: Final = 1e-10
"""A target closer to a gauge than this [m] takes the gauge's depth."""


def _idw(x: Values) -> dict[str, object]:
    distances = np.hypot(
        x.array("station_x_m") - x.real("target_x_m"),
        x.array("station_y_m") - x.real("target_y_m"),
    )
    close = distances < _COINCIDENT_M
    if close.any():
        weights = close / np.count_nonzero(close)
    else:
        # d^-p relative to the nearest gauge, so no power overflows or underflows all
        logs = np.log(distances)
        weights = np.exp(-x.real("power") * (logs - logs.min()))
        weights /= math.fsum(weights)
    return {
        "point_precipitation_mm": math.fsum(weights * x.array("precipitation_mm")),
        "weights": weights,
    }


_KRAKOW_GAUGES: Final = (
    (555500.0, 244300.0, 31.2),
    (545900.0, 249700.0, 36.8),
    (562900.0, 229400.0, 28.4),
)
"""Hydrolog's catalog example of ``precip areal``: three gauges near Kraków (x, y in m
of EPSG:2180, depth in mm), the point (553,000, 240,000)."""

_KRAKOW: Final = {
    "station_x_m": [gauge[0] for gauge in _KRAKOW_GAUGES],
    "station_y_m": [gauge[1] for gauge in _KRAKOW_GAUGES],
    "precipitation_mm": [gauge[2] for gauge in _KRAKOW_GAUGES],
    "target_x_m": 553000.0,
    "target_y_m": 240000.0,
    "power": 2.0,
}


def _idw_decimal(power: float) -> float:
    """Return the estimate of the Kraków example at 50 digits: distances by roots."""
    with localcontext() as context:
        context.prec = 50
        tx, ty = Decimal(553000), Decimal(240000)
        exponent = -Decimal(repr(power)) / 2
        weights, weighted = [], []
        for xs, ys, depth in _KRAKOW_GAUGES:
            squared = (Decimal(repr(xs)) - tx) ** 2 + (Decimal(repr(ys)) - ty) ** 2
            weight = (squared.ln() * exponent).exp()
            weights.append(weight)
            weighted.append(weight * Decimal(repr(depth)))
        return float(sum(weighted) / sum(weights))


def _idw_exact(run: Callable[..., Values]) -> None:
    for power in (1.0, 2.0, 3.0, 0.5):
        assert_within(
            run(**{**_KRAKOW, "power": power}).real("point_precipitation_mm"),
            _idw_decimal(power),
            rel=1e-14,
            reason="the weights d^-p from logarithms at 50 digits (decimal); float64 "
            "rounds the distances, the logarithms and the sums",
        )


def _at_a_gauge(run: Callable[..., Values]) -> None:
    out = run(**{**_KRAKOW, "target_x_m": 545900.0, "target_y_m": 249700.0})
    assert out.real("point_precipitation_mm") == 36.8
    assert out.array("weights").tolist() == [0.0, 1.0, 0.0]


def _station_count(x: Values) -> bool:
    count = len(x.array("precipitation_mm"))
    return len(x.array("station_x_m")) == count == len(x.array("station_y_m"))


_IDW_POWER_SOURCE = Source(
    citation=_CHOW,
    locator="p. 79: the reciprocal-distance-squared method (Wei and McGuinness 1973); "
    "HEC-HMS's inverse distance gage weighting and Hydrolog's default use p = 2",
    url=_CHOW_URL,
)
_NPTEL = Source(
    citation="Indian Institute of Technology Roorkee, NPTEL course Hydrology "
    "(105107129), "
    "module 3, lecture 4, 3.6 Estimation of missing data",
    locator="eq. 3.12 (the distance power method, weights 1/D^2) and Example 3.7",
    url="https://archive.nptel.ac.in/content/storage2/courses/105107129/module3/"
    "lecture4/lecture4.pdf",
)
_CATALOG_EXAMPLE = Source(
    citation="Hydrolog's catalog example of precip areal: three gauges near Kraków in "
    "EPSG:2180",
    locator="src/hydrolog/catalog/groups/precip.py, the examples of precip areal: x "
    "545,900 to 562,900 m, y 229,400 to 249,700 m",
)
_COORDINATE = Range(
    low=-math.inf,
    test_low=-1.0e7,
    test_high=1.0e7,
    test_reason="the coordinates of a projected system lie within half the "
    "circumference of the Earth, 2e7 m, of its origin; 1e7 m tests it",
)


def _coordinate(
    name: str, symbol: str, description: str, low: float, high: float
) -> Variable:
    return Variable(
        name=name,
        symbol=symbol,
        unit="m",
        kind="real_array" if name.startswith("station") else "real",
        description=description,
        physical=_COORDINATE,
        applicability="unstated",
        typical=Range(low=low, high=high, source=_CATALOG_EXAMPLE),
    )


IDW: Final = FormulaSpec(
    name="idw_precipitation",
    title="Precipitation at a point by inverse distance weighting of the gauges",
    function="hydrolog.precipitation.interpolation.idw_precipitation",
    family="statistic",
    equation=(
        "P = sum(w_i P_i), w_i = d_i**-p / sum(d_j**-p), d_i the distance of gauge i "
        "from the point; at the point of a gauge (d_i < 1e-10 m) P is the mean of the "
        "gauges there"
    ),
    latex=r"P = \sum_i w_i P_i,\quad w_i = \frac{d_i^{-p}}{\sum_j d_j^{-p}},\quad d_i "
    r"= \sqrt{(x_i - x)^2 + (y_i - y)^2}",
    variables=(
        _coordinate("station_x_m", "x_i", "Easting of each gauge.", 545900.0, 562900.0),
        _coordinate(
            "station_y_m", "y_i", "Northing of each gauge.", 229400.0, 249700.0
        ),
        _GAUGE_DEPTHS,
        _coordinate("target_x_m", "x", "Easting of the point.", 545900.0, 562900.0),
        _coordinate("target_y_m", "y", "Northing of the point.", 229400.0, 249700.0),
        Variable(
            name="power",
            symbol="p",
            unit="-",
            description="Exponent of the distance.",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=100.0,
                test_reason="p = 100 already gives the nearest gauge; fifty times "
                "the usual p = 2",
            ),
            applicability="unstated",
            typical=Range(low=2.0, high=2.0, source=_IDW_POWER_SOURCE),
        ),
    ),
    outputs=(
        Output(
            name="point_precipitation_mm",
            unit="mm",
            symbol="P",
            description="Precipitation at the point.",
            physical=Range(low=0.0),
        ),
        _WEIGHTS,
    ),
    sources=(
        _NPTEL,
        Source(
            citation="US Army Corps of Engineers, Hydrologic Engineering Center. "
            "HEC-HMS "
            "Technical Reference Manual: Inverse distance gage weighting",
            locator="the weight of a gage, 1/d^2 over the sum of 1/d^2 of the gages",
            url="https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/meteorology/"
            "precipitation/inverse-distance-gage-weighting",
        ),
        _IDW_POWER_SOURCE,
        Source(
            citation="Shepard, D. (1968). A two-dimensional interpolation function for "
            "irregularly-spaced data. Proceedings of the 1968 23rd ACM National "
            "Conference, 517-524",
            access="author-provided",
        ),
    ),
    constraints=(
        Constraint(
            name="station_count",
            cls="precondition",
            check=_station_count,
            text="two coordinates and a depth for each gauge",
            source=_NPTEL,
            satisfied={"precipitation_mm": [31.2, 36.8, 28.4]},
            violated={"precipitation_mm": [31.2, 36.8]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"precipitation_mm": 1},
        scalings=(
            Scaling(
                name="depth",
                inputs={"precipitation_mm": 1},
                outputs={"point_precipitation_mm": 1},
                tolerance=_DOUBLED,
            ),
            Scaling(
                name="coordinates",
                inputs={
                    "station_x_m": 1,
                    "station_y_m": 1,
                    "target_x_m": 1,
                    "target_y_m": 1,
                },
                outputs={},
                tolerance=Tolerance(
                    rel=1e-12,
                    abs=1e-12,
                    reason="doubling every coordinate doubles the distances exactly; "
                    "the logarithms of the doubled distances round differently",
                ),
            ),
        ),
        conservation=(_WEIGHTS_ADD_UP,),
        symmetries=(
            Symmetry(
                name="order",
                text="the order of the gauges does not matter",
                inputs=_reversed(("station_x_m", "station_y_m", "precipitation_mm")),
                outputs=_same("point_precipitation_mm"),
                tolerance=_SAME_SUM,
            ),
        ),
        limits=(
            Limit(
                name="exact_decimal",
                text="the estimate equals the weights d^-p computed at 50 digits",
                check=_idw_exact,
            ),
            Limit(
                name="at_a_gauge",
                text="at a gauge the estimate is the gauge's depth (Shepard 1968)",
                check=_at_a_gauge,
            ),
        ),
    ),
    validation=(
        "none: the sources give the method without an error statistic; HEC-HMS uses "
        "it for real-time forecasting"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "coordinates in metres of one projected system (EPSG:2180 in Poland); the "
        "weights depend only on ratios of distances, so any one unit gives the same "
        "estimate but for the threshold of a gauge at the point, 1e-10 of the unit",
        "every gauge given is used: HEC-HMS's nearest gauge per quadrant and a "
        "largest distance are choices of the caller; gauges at the point share it "
        "equally",
        (
            "the weights from ln d relative to the nearest gauge, so d**-p neither "
            "overflows nor underflows to a zero sum"
        ),
    ),
    traps={
        "singular_at_bound": "limit at_a_gauge: a distance of 0 gives the gauge's "
        "depth, not 1/0",
        "exp_overflow": "range case power-physical_high_test_bound: p = 100 over "
        "distances of kilometres stays finite",
        "gap_propagation": "type cases of every array, nan_element: a gap is refused",
        "many_small_terms": "the sums by math.fsum",
    },
    reference_cases=("tests/fixtures/formulas/areal-precipitation-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the weights d^-p from square roots and logarithms at 50 "
            "digits (decimal)",
            test="tests/unit/test_formulas_areal_precipitation.py (limit "
            "exact_decimal)",
        ),
    ),
    base=_KRAKOW,
)


def idw_precipitation(
    station_x_m: ArrayLike,
    station_y_m: ArrayLike,
    precipitation_mm: ArrayLike,
    target_x_m: float,
    target_y_m: float,
    power: float,
) -> PointEstimate:
    """Return the precipitation at a point by inverse distances, spec idw_precipitation.

    Parameters
    ----------
    station_x_m, station_y_m : array_like of float
        Coordinates of the gauges [m].
    precipitation_mm : array_like of float
        Depth at each gauge [mm].
    target_x_m, target_y_m : float
        Coordinates of the point [m].
    power : float
        Exponent of the distance.

    Returns
    -------
    PointEstimate
        The precipitation at the point and the weight of each gauge.

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        IDW,
        station_x_m=station_x_m,
        station_y_m=station_y_m,
        precipitation_mm=precipitation_mm,
        target_x_m=target_x_m,
        target_y_m=target_y_m,
        power=power,
    )
    out = checked_outputs(IDW, _idw(x))
    return PointEstimate(
        point_precipitation_mm=out.real("point_precipitation_mm"),
        weights=out.array("weights"),
    )


# --- isohyets -------------------------------------------------------------------------


def _isohyets(x: Values) -> dict[str, object]:
    values, areas = x.array("isohyet_values_mm"), x.array("zone_areas_km2")
    means = (values[:-1] + values[1:]) / 2.0
    return {"areal_precipitation_mm": math.fsum(means * (areas / math.fsum(areas)))}


def _isohyet_exact(run: Callable[..., Values]) -> None:
    for values, areas in (
        (
            [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 56.0],
            [0.88, 1.59, 2.24, 3.01, 1.22, 0.2],
        ),
        ([20.0, 30.0, 40.0, 50.0], [0.3, 0.5, 0.2]),
        ([12.5, 12.5], [7.0]),
    ):
        means = [(Fraction(a) + Fraction(b)) / 2 for a, b in itertools.pairwise(values)]
        assert_within(
            run(isohyet_values_mm=values, zone_areas_km2=areas).real(
                "areal_precipitation_mm"
            ),
            _weighted_exact([float(m) for m in means], areas),
            rel=1e-15,
            reason="the area-weighted mean of the zones in exact rational arithmetic; "
            "float64 rounds each share and product once and math.fsum the sums",
        )


def _zone_count(x: Values) -> bool:
    return len(x.array("zone_areas_km2")) == len(x.array("isohyet_values_mm")) - 1


_CHOW_C = Source(
    citation=_CHOW,
    locator="sec. 3.4, Fig. 3.4.3(c), p. 80: the isohyets 10 to 50 mm and the zones "
    "of 0.20 to 3.01 km2 of the example",
    url=_CHOW_URL,
)
_CHOW_ISOHYETS = (0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 56.0)
_CHOW_ZONES = (0.88, 1.59, 2.24, 3.01, 1.22, 0.2)

ISOHYET: Final = FormulaSpec(
    name="isohyet_precipitation",
    title="Areal precipitation by the isohyet method",
    function="hydrolog.precipitation.interpolation.isohyet_precipitation",
    family="statistic",
    equation=(
        "P = sum(A_i (v_i + v_(i+1)) / 2) / sum(A_i), zone i between the isohyets v_i "
        "and v_(i+1)"
    ),
    latex=r"\bar{P} = \frac{\sum_i A_i \frac{v_i + v_{i+1}}{2}}{\sum_i A_i}",
    variables=(
        Variable(
            name="isohyet_values_mm",
            symbol="v_i",
            unit="mm",
            kind="real_array",
            description="Values of the consecutive isohyets that bound the zones.",
            physical=Range(low=0.0, test_high=1825.0, test_reason=_WORLD_RECORD),
            applicability="unstated",
            typical=Range(low=10.0, high=50.0, source=_CHOW_C),
            min_length=2,
        ),
        Variable(
            name="zone_areas_km2",
            symbol="A_i",
            unit="km2",
            kind="real_array",
            description="Area of each zone between two consecutive isohyets.",
            physical=Range(low=0.0, test_high=1.49e8, test_reason=_LAND),
            applicability="unstated",
            typical=Range(low=0.2, high=3.01, source=_CHOW_C),
        ),
    ),
    outputs=(_AREAL,),
    sources=(
        _CHOW_C,
        Source(
            citation=_KZGW,
            locator="ch. II.1, eq. 2.2, pp. 16-17: metoda izohiet, the mean between "
            "neighbouring isohyets times the area between them (after Byczkowski "
            "1996)",
            url=_KZGW_URL,
        ),
    ),
    constraints=(
        Constraint(
            name="zone_count",
            cls="precondition",
            check=_zone_count,
            text="n isohyets bound n - 1 zones",
            source=_CHOW_C,
            satisfied={"zone_areas_km2": list(_CHOW_ZONES)},
            violated={"zone_areas_km2": [0.88, 1.59]},
        ),
        Constraint(
            name="area_positive",
            cls="precondition",
            check=_area_positive("zone_areas_km2"),
            text="sum(A_i) > 0: the zones cover some of the watershed",
            source=_CHOW_C,
            satisfied={"zone_areas_km2": list(_CHOW_ZONES)},
            violated={"zone_areas_km2": [0.0] * 6},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"isohyet_values_mm": 1},
        scalings=(
            Scaling(
                name="depth",
                inputs={"isohyet_values_mm": 1},
                outputs={"areal_precipitation_mm": 1},
                tolerance=_DOUBLED,
            ),
            Scaling(
                name="area",
                inputs={"zone_areas_km2": 1},
                outputs={},
                tolerance=_DOUBLED,
            ),
        ),
        symmetries=(
            Symmetry(
                name="order",
                text="the isohyets and zones read from the other end give the same "
                "mean",
                inputs=_reversed(("isohyet_values_mm", "zone_areas_km2")),
                outputs=_same("areal_precipitation_mm"),
                tolerance=_SAME_SUM,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="the mean equals it in exact rational arithmetic",
                check=_isohyet_exact,
            ),
        ),
    ),
    validation=(
        "none: Chow et al. (1988, p. 80) call the method the most accurate of the "
        "three "
        "where the isohyets are drawn with the topography; no error statistic"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "depths in mm, areas in km2 (any one unit gives the same mean, so shares of "
        "the watershed do too)",
        (
            "the mean of a zone is the mean of its two isohyets (KZGW 2017, eq. 2.2); "
            "an "
            "edge zone takes a notional bound that makes that mean the depth estimated "
            "for it (Chow et al. 1988, Fig. 3.4.3c: bounds 0 and 56 mm for 5 and 53 mm)"
        ),
        "the areas are divided by their sum, the watershed's area when the zones tile "
        "it",
    ),
    traps={
        "gap_propagation": "type cases of both arrays, nan_element: a gap is refused",
        "many_small_terms": "the sums by math.fsum; limit exact_rational",
    },
    reference_cases=("tests/fixtures/formulas/areal-precipitation-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="the area-weighted mean of the zones in exact rational "
            "arithmetic (fractions)",
            test="tests/unit/test_formulas_areal_precipitation.py (limit "
            "exact_rational)",
        ),
    ),
    base={
        "isohyet_values_mm": list(_CHOW_ISOHYETS),
        "zone_areas_km2": list(_CHOW_ZONES),
    },
)


def isohyet_precipitation(
    isohyet_values_mm: ArrayLike, zone_areas_km2: ArrayLike
) -> float:
    """Return the areal precipitation of isohyets, spec isohyet_precipitation.

    The second input gives the area of each zone between two consecutive isohyets in
    square kilometres, or its share of the watershed (its name carries the unit, so
    the standard's check of this docstring, which allows no digit, keeps it out of the
    list below).

    Parameters
    ----------
    isohyet_values_mm : array_like of float
        Values of the consecutive isohyets [mm].

    Returns
    -------
    float
        Areal precipitation [mm].

    Raises
    ------
    InvalidParameterError
        If an input is refused by the spec.
    """
    x = checked_inputs(
        ISOHYET, isohyet_values_mm=isohyet_values_mm, zone_areas_km2=zone_areas_km2
    )
    return checked_outputs(ISOHYET, _isohyets(x)).real("areal_precipitation_mm")


SPECS: Final = (AREAL_MEAN, THIESSEN, IDW, ISOHYET)
"""The Tier A formulas of the module, in the order of ``docs/FORMULAS.md``."""

TIER_B: Final = (
    TierBSpec(
        name="idw_grid_mean",
        function="hydrolog.precipitation.interpolation.areal_precipitation_idw",
        definition="the areal precipitation of a watershed as the arithmetic mean of "
        "the IDW estimates (idw_precipitation) at the points of a grid",
        convention="the mean of the points is the mean over the watershed only for a "
        "regular grid of points inside it; every gauge is used at every point",
        source=Source(
            citation=_CHOW,
            locator="sec. 3.4, p. 79: an areal mean from values interpolated at grid "
            "points by the reciprocal-distance-squared method",
            url=_CHOW_URL,
        ),
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


def thiessen_polygons(
    stations: list[Station],
    polygon_areas_km2: dict[str, float],
) -> ThiessenResult:
    """
    Calculate areal precipitation using Thiessen polygon method.

    The Thiessen method assigns weights to each station based on the area of its
    Voronoi polygon within the watershed (spec ``thiessen_precipitation``); a station
    without an area is not used.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations with measurements.
    polygon_areas_km2 : dict[str, float]
        Area of each station's Thiessen polygon [km²].
        Keys are station IDs.

    Returns
    -------
    ThiessenResult
        Interpolation results with weights and contributions.

    Raises
    ------
    InvalidParameterError
        If stations list is empty or areas don't match stations.

    Notes
    -----
    The Thiessen polygon (Voronoi diagram) for each station includes all points
    closer to that station than any other; ``docs/FORMULAS.md`` shows the equation,
    ranges and sources of the spec.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, precipitation_mm=25.0),
    ...     Station("S2", 10, 0, precipitation_mm=35.0),
    ...     Station("S3", 5, 8, precipitation_mm=30.0),
    ... ]
    >>> areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}
    >>> result = thiessen_polygons(stations, areas)
    >>> print(f"Areal P: {result.areal_precipitation_mm:.1f} mm")
    Areal P: 30.6 mm
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    # Validate polygon areas
    station_ids = {s.station_id for s in stations}
    area_ids = set(polygon_areas_km2.keys())

    if not area_ids.issubset(station_ids):
        missing = area_ids - station_ids
        raise InvalidParameterError(
            f"polygon_areas_km2 contains unknown station IDs: {missing}"
        )

    # Calculate total area and weights
    total_area = sum(polygon_areas_km2.values())

    if total_area <= 0:
        raise InvalidParameterError("Total polygon area must be positive")

    used = [station for station in stations if station.station_id in polygon_areas_km2]
    polygons = thiessen_precipitation(
        [station.precipitation_mm for station in used],
        [polygon_areas_km2[station.station_id] for station in used],
    )
    weights = {
        station.station_id: float(weight)
        for station, weight in zip(used, polygons.weights, strict=True)
    }
    return ThiessenResult(
        areal_precipitation_mm=polygons.areal_precipitation_mm,
        station_weights=weights,
        station_contributions_mm={
            station.station_id: station.precipitation_mm * weights[station.station_id]
            for station in used
        },
    )


def inverse_distance_weighting(
    stations: list[Station],
    target_x: float,
    target_y: float,
    power: float = 2.0,
    max_distance: float | None = None,
) -> IDWResult:
    """
    Interpolate precipitation using Inverse Distance Weighting (IDW).

    IDW assigns weights inversely proportional to the distance
    raised to a power.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.
    target_x : float
        X coordinate of target point.
    target_y : float
        Y coordinate of target point.
    power : float, optional
        Distance power parameter, by default 2.0.
        Higher values give more weight to nearby stations.
    max_distance : float, optional
        Maximum distance to include stations. If None, all
        stations are used.

    Returns
    -------
    IDWResult
        Interpolation result with weights.

    Raises
    ------
    InvalidParameterError
        If stations list is empty or power is non-positive.

    Notes
    -----
    Spec ``idw_precipitation``: the weights fall with a power of the distance, and a
    target point at a station takes that station's value; ``docs/FORMULAS.md`` shows
    the equation, ranges and sources. Stations beyond ``max_distance`` are left out
    first.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, precipitation_mm=25.0),
    ...     Station("S2", 10, 0, precipitation_mm=35.0),
    ... ]
    >>> result = inverse_distance_weighting(stations, 3, 0, power=2)
    >>> print(f"P at (3,0): {result.areal_precipitation_mm:.1f} mm")
    P at (3,0): 26.6 mm
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    if power <= 0:
        raise InvalidParameterError(f"power must be positive, got {power}")

    valid_stations = stations
    if max_distance is not None:
        valid_stations = [
            s
            for s in stations
            if math.hypot(s.x - target_x, s.y - target_y) <= max_distance
        ]
        if not valid_stations:
            raise InvalidParameterError(
                f"No stations within max_distance={max_distance}"
            )

    estimate = idw_precipitation(
        [s.x for s in valid_stations],
        [s.y for s in valid_stations],
        [s.precipitation_mm for s in valid_stations],
        target_x,
        target_y,
        power,
    )
    used = list(zip(valid_stations, estimate.weights.tolist(), strict=True))
    if np.count_nonzero(estimate.weights) == 1:
        # the target at a station, or one station left: that station alone
        used = [(station, weight) for station, weight in used if weight > 0.0]
    return IDWResult(
        areal_precipitation_mm=estimate.point_precipitation_mm,
        station_weights={station.station_id: weight for station, weight in used},
        power=power,
    )


def areal_precipitation_idw(
    stations: list[Station],
    grid_x: NDArray[np.float64],
    grid_y: NDArray[np.float64],
    power: float = 2.0,
) -> float:
    """
    Calculate areal precipitation by averaging IDW over a grid.

    This function interpolates precipitation to each grid point
    and returns the arithmetic mean.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.
    grid_x : NDArray[np.float64]
        X coordinates of grid points.
    grid_y : NDArray[np.float64]
        Y coordinates of grid points (same shape as grid_x).
    power : float, optional
        IDW power parameter, by default 2.0.

    Returns
    -------
    float
        Mean areal precipitation [mm].

    Examples
    --------
    >>> import numpy as np
    >>> stations = [Station("S1", 0, 0, 25.0), Station("S2", 10, 10, 35.0)]
    >>> x = np.linspace(0, 10, 11)
    >>> y = np.linspace(0, 10, 11)
    >>> xx, yy = np.meshgrid(x, y)
    >>> P_areal = areal_precipitation_idw(stations, xx.flatten(), yy.flatten())
    """
    if len(grid_x) != len(grid_y):
        raise InvalidParameterError(
            f"grid_x and grid_y must have same length, "
            f"got {len(grid_x)} and {len(grid_y)}"
        )

    if len(grid_x) == 0:
        raise InvalidParameterError("Grid cannot be empty")

    interpolated = []
    for x, y in zip(grid_x, grid_y, strict=False):
        result = inverse_distance_weighting(stations, float(x), float(y), power)
        interpolated.append(result.areal_precipitation_mm)

    return float(np.mean(interpolated))


def isohyet_method(
    isohyet_values_mm: NDArray[np.float64],
    area_fractions: NDArray[np.float64],
) -> IsohyetResult:
    """
    Calculate areal precipitation using the isohyet method.

    The isohyet method uses contour lines of equal precipitation
    (isohyets) and the areas between them to calculate weighted
    average precipitation.

    Parameters
    ----------
    isohyet_values_mm : NDArray[np.float64]
        Precipitation values at isohyet boundaries [mm].
        Array of length n representing n-1 zones.
    area_fractions : NDArray[np.float64]
        Fraction of watershed area between consecutive isohyets.
        Array of length n-1, must sum to 1.0.

    Returns
    -------
    IsohyetResult
        Interpolation results.

    Raises
    ------
    InvalidParameterError
        If arrays have incompatible lengths or fractions don't sum to 1.

    Notes
    -----
    For each zone between isohyets i and i+1, the average precipitation is the mean
    of the two (spec ``isohyet_precipitation``, KZGW 2017, eq. 2.2; Chow et al. 1988,
    Fig. 3.4.3c), weighted by the fraction of the watershed between them;
    ``docs/FORMULAS.md`` shows the equation, ranges and sources.

    Every zone lies between two values, so the zones at the edges of the watershed
    (beyond its highest or below its lowest isohyet) need a bounding value of their
    own: the value that makes the mid-value of the zone the mean precipitation
    estimated for it. Chow et al. (1988) estimate 5 mm for the zone below the 10-mm
    isohyet and 53 mm for the one above the 50-mm isohyet; the bounds 0 and 56 mm give
    those means and their 27.9 mm.

    Examples
    --------
    Chow, Maidment and Mays (1988), Fig. 3.4.3(c), p. 80: zone areas 0.88, 1.59, 2.24,
    3.01, 1.22 and 0.20 km² between the isohyets 10 to 50 mm, with edge bounds 0 and
    56 mm:

    >>> import numpy as np
    >>> isohyets = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 56.0])
    >>> areas_km2 = np.array([0.88, 1.59, 2.24, 3.01, 1.22, 0.20])
    >>> result = isohyet_method(isohyets, areas_km2 / areas_km2.sum())
    >>> print(f"Areal P: {result.areal_precipitation_mm:.1f} mm")
    Areal P: 27.9 mm
    """
    isohyet_values_mm = np.asarray(isohyet_values_mm, dtype=np.float64)
    area_fractions = np.asarray(area_fractions, dtype=np.float64)

    if len(isohyet_values_mm) < 2:
        raise InvalidParameterError(
            f"Need at least 2 isohyet values, got {len(isohyet_values_mm)}"
        )

    expected_zones = len(isohyet_values_mm) - 1
    if len(area_fractions) != expected_zones:
        raise InvalidParameterError(
            f"Expected {expected_zones} area fractions for "
            f"{len(isohyet_values_mm)} isohyets, got {len(area_fractions)}"
        )

    fraction_sum = np.sum(area_fractions)
    if not np.isclose(fraction_sum, 1.0, rtol=1e-3):
        raise InvalidParameterError(
            f"area_fractions must sum to 1.0, got {fraction_sum:.4f}"
        )

    if np.any(area_fractions < 0):
        raise InvalidParameterError("area_fractions must be non-negative")

    return IsohyetResult(
        areal_precipitation_mm=isohyet_precipitation(isohyet_values_mm, area_fractions),
        isohyet_values_mm=isohyet_values_mm,
        area_fractions=area_fractions,
    )


def arithmetic_mean(stations: list[Station]) -> float:
    """
    Calculate simple arithmetic mean of station precipitation.

    This is the simplest method (spec ``areal_mean_precipitation``), appropriate when
    stations are uniformly distributed and topography is relatively flat.

    Parameters
    ----------
    stations : list[Station]
        List of precipitation stations.

    Returns
    -------
    float
        Arithmetic mean precipitation [mm].

    Raises
    ------
    InvalidParameterError
        If stations list is empty.

    Examples
    --------
    >>> stations = [
    ...     Station("S1", 0, 0, 25.0),
    ...     Station("S2", 10, 0, 35.0),
    ...     Station("S3", 5, 8, 30.0),
    ... ]
    >>> P_mean = arithmetic_mean(stations)
    >>> print(f"Mean P: {P_mean:.1f} mm")
    Mean P: 30.0 mm
    """
    if not stations:
        raise InvalidParameterError("stations list cannot be empty")

    return areal_mean_precipitation([s.precipitation_mm for s in stations])
