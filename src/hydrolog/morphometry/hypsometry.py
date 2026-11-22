"""Hypsometric curve and hypsometric integral of a watershed (Strahler 1952).

The hypsometric integral is declared by its spec :data:`HYPSOMETRIC_INTEGRAL`
(``hypsometric_integral``, Nogat CMP-2.1) beside its function
:func:`hypsometric_integral`; ``docs/FORMULAS.md`` shows its equation, ranges,
sources and Strahler's stages. The curve, the area-weighted mean and the elevation
with a given share of the area above it are the Tier B rows of :data:`TIER_B`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

import numpy as np
from numpy.typing import NDArray

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry._sources import ELEVATION_REASON, from_handoffs
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
    Variable,
    assert_within,
)

__all__ = [
    "HYPSOMETRIC_INTEGRAL",
    "SPECS",
    "TIER_B",
    "HypsometricCurve",
    "HypsometricResult",
    "hypsometric_integral",
]

_STRAHLER = Source(
    citation="Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional "
    "topography. Geological Society of America Bulletin 63: 1117-1142",
    locator="Fig. 3 and 'Integration of the hypsometric function': the integral is the "
    "area under the percentage hypsometric curve, relative area a/A above relative "
    "height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of "
    "the article)",
    url="https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html",
)
_PIKE_WILSON = Source(
    citation="Pike, R.J. & Wilson, S.E. (1971). Elevation-relief ratio, hypsometric "
    "integral, and geomorphic area-altitude analysis. Geological Society of America "
    "Bulletin 82: 1079-1084",
    locator="the elevation-relief ratio E = (mean - min) / (max - min) equals the "
    "hypsometric integral (not opened; the identity of the exceedance integral, "
    "integral of P(h >= x) dx over [0, 1] = E[h], is exact)",
)
_EQUAL_CELLS = Source(
    citation="Hydrolog's HypsometricCurve: cells of equal area unless cell_areas is "
    "given, as in every example and test of the project",
    locator="src/hydrolog/morphometry/hypsometry.py; examples/04_morfometria.ipynb",
)

# --- the computation -----------------------------------------------------------------


def _curve(
    elevations: NDArray[np.float64], areas: NDArray[np.float64], n_points: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Relative heights h/H and relative areas a/A above them, at n thresholds.

    The thresholds are equally spaced from the lowest to the highest elevation; the
    area above a threshold counts the cells at or above it, so the first relative
    area is 1 and the last the share of the highest cells. Elevations must differ.
    """
    lowest = float(np.min(elevations))
    highest = float(np.max(elevations))
    thresholds = np.linspace(lowest, highest, n_points)
    total = float(np.sum(areas))
    above = np.array(
        [float(np.sum(areas[elevations >= threshold])) for threshold in thresholds],
        dtype=np.float64,
    )
    return (thresholds - lowest) / (highest - lowest), above / total


def _integral(x: Values) -> float:
    """Return the trapezoid of the curve of checked inputs."""
    heights, areas = _curve(
        x.array("elevations_m"), x.array("cell_areas"), x.integer("n_points")
    )
    return float(np.trapezoid(areas, heights))


# --- oracles and limits (CMP-6.2, CMP-6.5) -------------------------------------------

_ORACLE_SURFACES: Final[tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]] = (
    # the docstring's seven equally spaced elevations, equal cells
    ((100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0), (1.0,) * 7),
    # nine cells at the outlet's elevation and one above (a flat valley floor)
    ((100.0,) * 9 + (200.0,), (1.0,) * 10),
    # a convex (young) surface with unequal cells
    ((210.0, 395.5, 402.25, 410.0, 380.125, 399.0), (2.0, 1.0, 0.5, 3.0, 1.5, 1.0)),
    # a concave surface with a residual mass (monadnock)
    ((258.72, 260.1, 261.0, 263.4, 270.0, 440.16), (4.0, 3.5, 3.0, 2.0, 1.0, 0.25)),
)
"""Surfaces of the oracles: elevations [m] and cell areas."""


def _exact_trapezoid(
    elevations: Sequence[float], areas: Sequence[float], n_points: int
) -> Fraction:
    """Return the trapezoid of the curve in exact rational arithmetic.

    The thresholds are the exact points min + i (max - min) / (n - 1); a cell lies
    above one when its exact elevation does. The oracles' elevations lie away from
    the float rounding of every threshold, so both sides compare alike.
    """
    z = [Fraction(value) for value in elevations]
    a = [Fraction(value) for value in areas]
    lowest, highest = min(z), max(z)
    total = sum(a, Fraction(0))
    shares = []
    for i in range(n_points):
        threshold = lowest + (highest - lowest) * i / (n_points - 1)
        shares.append(
            sum(
                (ai for zi, ai in zip(z, a, strict=True) if zi >= threshold),
                Fraction(0),
            )
            / total
        )
    step = Fraction(1, n_points - 1)
    return sum(
        ((shares[i] + shares[i + 1]) * step / 2 for i in range(n_points - 1)),
        Fraction(0),
    )


def _exact_rational(run: Callable[..., Values]) -> None:
    for elevations, areas in _ORACLE_SURFACES:
        for n_points in (2, 11, 101):
            assert_within(
                run(
                    elevations_m=list(elevations),
                    cell_areas=list(areas),
                    n_points=n_points,
                ).real("hypsometric_integral"),
                float(_exact_trapezoid(elevations, areas, n_points)),
                abs=2e-15,
                reason="the trapezoid of the float curve against its exact rational "
                "value: each relative area and height rounds once or twice and the "
                "trapezoid sums at most a hundred such terms of at most 1/100",
            )


def _mean_based(elevations: Sequence[float], areas: Sequence[float]) -> Fraction:
    """(mean - min) / (max - min), the area-weighted mean, in rational arithmetic."""
    z = [Fraction(value) for value in elevations]
    a = [Fraction(value) for value in areas]
    mean = sum((zi * ai for zi, ai in zip(z, a, strict=True)), Fraction(0)) / sum(
        a, Fraction(0)
    )
    return (mean - min(z)) / (max(z) - min(z))


def _within_trapezoid_bound(run: Callable[..., Values]) -> None:
    for elevations, areas in _ORACLE_SURFACES:
        z = np.asarray(elevations)
        top_share = float(np.sum(np.asarray(areas)[z == z.max()]) / np.sum(areas))
        for n_points in (2, 11, 101):
            bound = (1.0 - top_share) / (2 * (n_points - 1))
            assert_within(
                run(
                    elevations_m=list(elevations),
                    cell_areas=list(areas),
                    n_points=n_points,
                ).real("hypsometric_integral"),
                float(_mean_based(elevations, areas)),
                abs=bound + 1e-15,
                reason="the exact integral is (mean - min) / (max - min) (Pike and "
                "Wilson 1971); the trapezoid of n points on the non-increasing step "
                "curve departs from it by at most (a(0) - a(1)) / (2 (n - 1)), and "
                "float64 adds a few units in the last place",
            )


def _two_points(run: Callable[..., Values]) -> None:
    for elevations, areas in _ORACLE_SURFACES:
        z = np.asarray(elevations)
        top_share = float(np.sum(np.asarray(areas)[z == z.max()]) / np.sum(areas))
        assert_within(
            run(elevations_m=list(elevations), cell_areas=list(areas), n_points=2).real(
                "hypsometric_integral"
            ),
            (1.0 + top_share) / 2.0,
            rel=4.5e-16,
            reason="two thresholds, the lowest and the highest elevation: one "
            "trapezoid of the whole area and the highest cells' share, a sum and a "
            "halving",
        )


# --- the spec ------------------------------------------------------------------------

_EXACT_SCALING = Tolerance(
    abs=0.0,
    reason="elevations or cell areas scaled by 2 are exact in binary and scale the "
    "thresholds and sums exactly, so every relative height and area is the same",
)

HYPSOMETRIC_INTEGRAL: Final = FormulaSpec(
    name="hypsometric_integral",
    title="Hypsometric integral of a watershed by the trapezoid of its curve "
    "(Strahler)",
    function="hydrolog.morphometry.hypsometry.hypsometric_integral",
    family="index",
    equation=(
        "HI = sum((a[i] + a[i+1]) / 2) / (n - 1), a[i] the share of the area at or "
        "above z_min + i (z_max - z_min) / (n - 1), i = 0 .. n-1"
    ),
    latex=(
        r"HI = \sum_{i=0}^{n-2} \frac{a_i + a_{i+1}}{2\,(n-1)},\quad "
        r"a_i = \frac{\sum_{z_j \ge t_i} A_j}{\sum_j A_j},\quad "
        r"t_i = z_{min} + \frac{i}{n-1}(z_{max} - z_{min})"
    ),
    variables=(
        Variable(
            name="elevations_m",
            symbol="z",
            unit="m",
            kind="real_array",
            description="Elevation of each cell of the watershed's DEM [m a.s.l.].",
            physical=Range(
                test_low=-431.0, test_high=8849.0, test_reason=ELEVATION_REASON
            ),
            applicability="unstated",
            typical=Range(
                low=100.0,
                high=750.0,
                source=from_handoffs("elevations of 100.0 to 722.68 m"),
            ),
        ),
        Variable(
            name="cell_areas",
            symbol="A_j",
            unit="-",
            kind="real_array",
            description="Area of each cell, in any one unit (only the shares count).",
            physical=Range(
                low=0.0,
                low_inclusive=False,
                test_high=1.49e8,
                test_reason="the land area of the Earth in km2 (CIA, The World "
                "Factbook, 2025, field Area: land): no cell is larger",
            ),
            applicability="unstated",
            typical=Range(low=1.0, high=1.0, source=_EQUAL_CELLS),
        ),
        Variable(
            name="n_points",
            symbol="n",
            unit="-",
            kind="integer",
            description="Number of equally spaced relative heights of the curve.",
            physical=Range(
                low=2.0,
                test_high=10001.0,
                test_reason="a hundred times the default 101: the trapezoid's bound "
                "1/(2(n-1)) is then 5e-5",
            ),
            applicability="unstated",
            typical=Range(low=101.0, high=101.0, source=_EQUAL_CELLS),
        ),
    ),
    outputs=(
        Output(
            name="hypsometric_integral",
            unit="-",
            symbol="HI",
            description="Area under the percentage hypsometric curve in the unit "
            "square.",
            physical=Range(low=0.0, high=1.0),
        ),
    ),
    sources=(_STRAHLER, _PIKE_WILSON),
    constraints=(
        Constraint(
            name="same_length",
            cls="physical",
            check=lambda x: (
                x.array("elevations_m").shape == x.array("cell_areas").shape
            ),
            text="one area per elevation",
            source=_STRAHLER,
            satisfied={"elevations_m": [100.0, 200.0], "cell_areas": [1.0, 1.0]},
            violated={"elevations_m": [100.0, 200.0, 300.0], "cell_areas": [1.0, 1.0]},
        ),
        Constraint(
            name="positive_relief",
            cls="precondition",
            check=lambda x: (
                float(np.max(x.array("elevations_m")))
                > float(np.min(x.array("elevations_m")))
            ),
            text="max(z) > min(z): the relative height h/H divides by the relief",
            source=_STRAHLER,
            satisfied={"elevations_m": [100.0, 200.0], "cell_areas": [1.0, 1.0]},
            boundary={"elevations_m": [250.0, 250.0], "cell_areas": [1.0, 1.0]},
            boundary_holds=False,
            violated={"elevations_m": [250.0], "cell_areas": [1.0]},
        ),
    ),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="elevations",
                inputs={"elevations_m": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
            Scaling(
                name="cell_areas",
                inputs={"cell_areas": 1},
                outputs={},
                tolerance=_EXACT_SCALING,
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="HI equals the trapezoid of the curve in exact rational "
                "arithmetic",
                check=_exact_rational,
            ),
            Limit(
                name="mean_based",
                text="HI lies within (a(0) - a(1)) / (2 (n - 1)) of the exact "
                "integral (mean - min) / (max - min)",
                check=_within_trapezoid_bound,
            ),
            Limit(
                name="two_points",
                text="with two thresholds HI is (1 + the highest cells' share) / 2",
                check=_two_points,
            ),
        ),
    ),
    validation=(
        "none: the integral describes a surface; Strahler (1952) relates its values to "
        "stages of erosion, not to observations of a quantity"
    ),
    formula_version=1,
    status="oracle only",
    conventions=(
        (
            "the curve of the relative area a/A at or above the relative height h/H "
            "(exceedance), Strahler's percentage hypsometric curve, sampled at n "
            "equally spaced heights from the lowest to the highest cell, h/H = 0 to 1"
        ),
        (
            "HI by the trapezoid rule over the n points of the curve, n = 101 by "
            "default; the exact integral of the step curve of the cells is (mean - "
            "min) / (max - min) (Pike and Wilson 1971), from which the trapezoid "
            "departs by at most (a(0) - a(1)) / (2 (n - 1)), 0.005 for n = 101, most "
            "where much of the area lies at the outlet's elevation"
        ),
        (
            "Strahler's stages (1952, text with Fig. 7): about 0.60 and above the "
            "inequilibrium (youthful) stage, 0.35 to 0.60 the equilibrium (mature) "
            "stage, below 0.35 the monadnock phase; Strahler gives them as rough "
            "limits and replaces old age by the monadnock phase"
        ),
        "cell areas in any one unit: only their shares count",
    ),
    traps={
        "difference_denominator": "the relief max - min divides the heights: equal "
        "elevations are refused by the precondition positive_relief (its boundary "
        "case and test_a_flat_surface_is_refused)",
        "gap_propagation": "type cases elevations_m-nan_element and "
        "cell_areas-nan_element: a gap is refused, the spec allows none",
        "many_small_terms": "test_many_cells_match_their_exact_sums: the shares of "
        "200,001 cells against math.fsum",
    },
    oracles=(
        Oracle(
            kind="exact",
            description="the trapezoid of the curve in exact rational arithmetic "
            "(fractions), with exact thresholds",
            test="tests/unit/test_formulas_hypsometry.py (limit exact_rational)",
        ),
        Oracle(
            kind="exact",
            description="the exact integral (mean - min) / (max - min) in rational "
            "arithmetic, with the trapezoid's error bound",
            test="tests/unit/test_formulas_hypsometry.py (limit mean_based)",
        ),
    ),
    base={
        "elevations_m": [100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0],
        "cell_areas": [1.0] * 7,
        "n_points": 101,
    },
)

SPECS: Final[tuple[FormulaSpec, ...]] = (HYPSOMETRIC_INTEGRAL,)
"""The spec of the module."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="hypsometric_curve",
        function="hydrolog.morphometry.hypsometry.HypsometricCurve.generate_curve",
        definition="relative heights h/H = (t - min) / (max - min) at n equally spaced "
        "thresholds t and the relative areas a/A of the cells at or above each",
        convention="exceedance (area above), Strahler's percentage hypsometric curve; "
        "the first relative area is 1",
        source=_STRAHLER,
    ),
    TierBSpec(
        name="area_weighted_mean_elevation",
        function="hydrolog.morphometry.hypsometry.HypsometricCurve.mean_elevation",
        definition="the mean elevation of the cells weighted by their areas [m a.s.l.]",
        convention="numpy.average with the cell areas as weights",
        source=Source(
            citation="Baścik, M. (2006). Parametry fizjograficzne. In: "
            "Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. "
            "Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34",
            locator="eq. (1.2.8): the mean elevation weighted by the areas between "
            "contours",
            url="https://ruj.uj.edu.pl/server/api/core/bitstreams/"
            "c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content",
        ),
    ),
    TierBSpec(
        name="elevation_above_share",
        function="hydrolog.morphometry.hypsometry.HypsometricCurve."
        "elevation_at_percentile",
        definition="the elevation of the first cell, from the highest down, at which "
        "the cumulative share of the area reaches the given percent [m a.s.l.]",
        convention="the median elevation is the one with half of the area above it; "
        "no interpolation between cells",
        source=_STRAHLER,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""


def hypsometric_integral(
    elevations_m: NDArray[np.float64] | Sequence[float],
    cell_areas: NDArray[np.float64] | Sequence[float],
    n_points: int,
) -> float:
    """Return the hypsometric integral of a watershed, spec hypsometric_integral.

    Parameters
    ----------
    elevations_m : array_like
        Elevation of each cell [m a.s.l.].
    cell_areas : array_like
        Area of each cell, in any one unit.
    n_points : int
        Number of equally spaced relative heights of the curve.

    Returns
    -------
    float
        Hypsometric integral [-].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``), the
        arrays differ in length or all elevations are equal (``details.constraint``).
    """
    x = checked_inputs(
        HYPSOMETRIC_INTEGRAL,
        elevations_m=elevations_m,
        cell_areas=cell_areas,
        n_points=n_points,
    )
    return checked_outputs(
        HYPSOMETRIC_INTEGRAL, {"hypsometric_integral": _integral(x)}
    ).real("hypsometric_integral")


@dataclass
class HypsometricResult(JsonResultMixin):
    """
    Result of hypsometric curve analysis.

    Attributes
    ----------
    relative_heights : NDArray[np.float64]
        Relative heights h/H (0 to 1), where h is height above
        minimum and H is total relief.
    relative_areas : NDArray[np.float64]
        Relative cumulative areas a/A (0 to 1), where a is area
        above a given elevation and A is total area.
    hypsometric_integral : float
        Hypsometric integral [-], spec ``hypsometric_integral``.
    elevation_mean_m : float
        Area-weighted mean elevation [m a.s.l.].
    elevation_median_m : float
        Median elevation (50% area above) [m a.s.l.].
    """

    relative_heights: NDArray[np.float64]
    relative_areas: NDArray[np.float64]
    hypsometric_integral: float
    elevation_mean_m: float
    elevation_median_m: float

    @property
    def n_points(self) -> int:
        """Number of points in the hypsometric curve."""
        return len(self.relative_heights)


class HypsometricCurve:
    """
    Generate and analyze hypsometric curves.

    The hypsometric curve shows the relationship between elevation
    and the cumulative area above that elevation. It characterizes
    the distribution of landmass with elevation.

    Parameters
    ----------
    elevations : NDArray[np.float64]
        Array of elevation values from DEM [m a.s.l.].
    cell_areas : NDArray[np.float64], optional
        Area of each DEM cell [km²]. If not provided, assumes
        uniform cell sizes.

    Notes
    -----
    The hypsometric integral (spec ``hypsometric_integral``) indicates the stage of
    the landscape: Strahler (1952, GSA Bulletin 63: 1117-1142, text with Fig. 7)
    puts the inequilibrium (youthful) stage at about 0.60 and above, the equilibrium
    (mature) stage between 0.35 and 0.60 and the monadnock phase below 0.35.

    Examples
    --------
    >>> elevations = np.array([100, 150, 200, 250, 300, 350, 400])
    >>> hypso = HypsometricCurve(elevations)
    >>> result = hypso.analyze()
    >>> print(f"Hypsometric integral: {result.hypsometric_integral:.3f}")
    Hypsometric integral: 0.501
    """

    def __init__(
        self,
        elevations: NDArray[np.float64],
        cell_areas: NDArray[np.float64] | None = None,
    ) -> None:
        """
        Initialize hypsometric curve analysis.

        Parameters
        ----------
        elevations : NDArray[np.float64]
            Array of elevation values from DEM [m a.s.l.].
        cell_areas : NDArray[np.float64], optional
            Area of each DEM cell [km²].

        Raises
        ------
        InvalidParameterError
            If elevations array is empty or holds non-finite values, or if
            cell_areas holds non-finite or non-positive values.
        """
        self.elevations = np.asarray(elevations, dtype=np.float64).flatten()

        if len(self.elevations) == 0:
            raise InvalidParameterError("elevations array cannot be empty")

        if not np.all(np.isfinite(self.elevations)):
            raise InvalidParameterError("elevations must be finite (no NaN or inf)")
        if cell_areas is not None:
            self.cell_areas = np.asarray(cell_areas, dtype=np.float64).flatten()
            if len(self.cell_areas) != len(self.elevations):
                raise InvalidParameterError(
                    f"cell_areas length ({len(self.cell_areas)}) must match "
                    f"elevations length ({len(self.elevations)})"
                )
            if not np.all(np.isfinite(self.cell_areas)) or np.any(self.cell_areas <= 0):
                raise InvalidParameterError(
                    "all cell_areas must be finite and positive"
                )
        else:
            # Uniform cell areas
            self.cell_areas = np.ones_like(self.elevations)

        self._total_area = float(np.sum(self.cell_areas))

    @property
    def elevation_min(self) -> float:
        """Minimum elevation [m a.s.l.]."""
        return float(np.min(self.elevations))

    @property
    def elevation_max(self) -> float:
        """Maximum elevation [m a.s.l.]."""
        return float(np.max(self.elevations))

    @property
    def relief(self) -> float:
        """Total relief H = max - min [m]."""
        return self.elevation_max - self.elevation_min

    @property
    def total_area(self) -> float:
        """Total watershed area [km²]."""
        return self._total_area

    def generate_curve(
        self, n_points: int = 101
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Generate hypsometric curve data (the Tier B row ``hypsometric_curve``).

        Parameters
        ----------
        n_points : int, optional
            Number of points for the curve, by default 101.

        Returns
        -------
        tuple[NDArray[np.float64], NDArray[np.float64]]
            (relative_heights, relative_areas) both in range [0, 1].

        Raises
        ------
        InvalidParameterError
            If ``n_points`` is below 2 or all elevations are equal, as the spec
            ``hypsometric_integral`` refuses them.

        Notes
        -----
        relative_height = (elevation - min) / relief
        relative_area = cumulative_area_above / total_area
        """
        x = checked_inputs(
            HYPSOMETRIC_INTEGRAL,
            elevations_m=self.elevations,
            cell_areas=self.cell_areas,
            n_points=n_points,
        )
        return _curve(
            x.array("elevations_m"), x.array("cell_areas"), x.integer("n_points")
        )

    def hypsometric_integral(self, n_points: int = 101) -> float:
        """
        Calculate the hypsometric integral (:func:`hypsometric_integral`).

        Parameters
        ----------
        n_points : int, optional
            Number of points for integration, by default 101.

        Returns
        -------
        float
            Hypsometric integral (0 to 1).

        Raises
        ------
        InvalidParameterError
            If the relief is zero (all elevations equal): the curve and its
            integral are undefined.
        """
        return hypsometric_integral(self.elevations, self.cell_areas, n_points)

    def elevation_at_percentile(self, percentile: float) -> float:
        """
        Find elevation at a given area percentile.

        Parameters
        ----------
        percentile : float
            Percentile of area (0-100). E.g., 50 means the elevation
            where 50% of the area is above.

        Returns
        -------
        float
            Elevation at the given percentile [m a.s.l.].

        Examples
        --------
        >>> hypso = HypsometricCurve(np.array([100, 150, 200, 250, 300, 350, 400]))
        >>> hypso.elevation_at_percentile(50)
        250.0
        """
        if not 0 <= percentile <= 100:
            raise InvalidParameterError(
                f"percentile must be in range 0-100, got {percentile}"
            )

        # Sort elevations in descending order with their areas
        sorted_indices = np.argsort(self.elevations)[::-1]
        sorted_elevations = self.elevations[sorted_indices]
        sorted_areas = self.cell_areas[sorted_indices]

        # Calculate cumulative area percentage
        cumulative_area = np.cumsum(sorted_areas)
        cumulative_percent = (cumulative_area / self.total_area) * 100.0

        # Find elevation where cumulative percentage reaches target
        target = percentile
        idx = np.searchsorted(cumulative_percent, target)

        if idx >= len(sorted_elevations):
            return float(sorted_elevations[-1])

        return float(sorted_elevations[idx])

    def mean_elevation(self) -> float:
        """
        Calculate area-weighted mean elevation.

        Returns
        -------
        float
            Mean elevation [m a.s.l.].
        """
        mean_elev: float = float(np.average(self.elevations, weights=self.cell_areas))
        return mean_elev

    def analyze(self, n_points: int = 101) -> HypsometricResult:
        """
        Perform complete hypsometric analysis.

        Parameters
        ----------
        n_points : int, optional
            Number of points for the curve, by default 101.

        Returns
        -------
        HypsometricResult
            Complete analysis results.

        Examples
        --------
        >>> elevations = np.linspace(100, 500, 1000)
        >>> hypso = HypsometricCurve(elevations)
        >>> result = hypso.analyze()
        >>> print(f"HI: {result.hypsometric_integral:.3f}")
        HI: 0.500
        >>> print(f"Mean elev: {result.elevation_mean_m:.1f} m")
        Mean elev: 300.0 m
        """
        rel_heights, rel_areas = self.generate_curve(n_points)
        hi = self.hypsometric_integral(n_points)
        mean_elev = self.mean_elevation()
        median_elev = self.elevation_at_percentile(50)

        return HypsometricResult(
            relative_heights=rel_heights,
            relative_areas=rel_areas,
            hypsometric_integral=hi,
            elevation_mean_m=mean_elev,
            elevation_median_m=median_elev,
        )
