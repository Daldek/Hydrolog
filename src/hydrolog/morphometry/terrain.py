"""Terrain parameters of a watershed: elevations, relief and the relief ratio.

The relief ratio, the relief over a length, is declared by its spec
:data:`RELIEF_RATIO` (``relief_ratio``, Nogat CMP-2.1) beside its function
:func:`relief_ratio`; ``docs/FORMULAS.md`` shows its equation, ranges and sources.
:class:`TerrainAnalysis` gives it over the watershed's length and, as the slope of
the main channel, over the channel's length; the mean elevation it assumes when none
is given is the Tier B row :data:`MIDPOINT_ELEVATION`.

Examples
--------
>>> relief_ratio(elevation_min_m=150.0, elevation_max_m=520.0, length_km=12.5)
0.0296
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Final

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry._sources import (
    BASCIK,
    BASCIK_URL,
    ELEVATION_REASON,
    LENGTH,
    WARTALSKA,
    WARTALSKA_URL,
    from_handoffs,
)
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
    TierBSpec,
    Tolerance,
    Values,
    Variable,
    assert_within,
    convert,
)

__all__ = [
    "MIDPOINT_ELEVATION",
    "RELIEF_RATIO",
    "SPECS",
    "TIER_B",
    "ElevationParameters",
    "SlopeParameters",
    "TerrainAnalysis",
    "relief_ratio",
]

_BASCIK_DROP = Source(
    citation=BASCIK,
    locator="eq. (1.2.12): wskaźnik rzeźby Cs = (Hmax - Hmin) / Lm; eq. (1.2.15): the "
    "slope of a river, the drop from its source to its mouth over its length",
    url=BASCIK_URL,
)
_WARTALSKA_DROP = Source(
    citation=WARTALSKA,
    locator="section 2.3: wskaźnik rzeźby zlewni Strahlera Jd = dH / L",
    url=WARTALSKA_URL,
)


def _elevation(name: str, symbol: str, description: str) -> Variable:
    return Variable(
        name=name,
        symbol=symbol,
        unit="m",
        description=description,
        physical=Range(test_low=-431.0, test_high=8849.0, test_reason=ELEVATION_REASON),
        applicability="unstated",
        typical=Range(
            low=100.0,
            high=750.0,
            source=from_handoffs("elevations of 100.0 to 722.68 m"),
        ),
    )


def _ratio(x: Values) -> float:
    """(Hmax - Hmin) / L[m]: inf only where the ratio lies beyond float64."""
    length_m = convert(x.real("length_km"), "km", "m")
    return (x.real("elevation_max_m") - x.real("elevation_min_m")) / length_m


def _exact_ratio(minimum: float, maximum: float, length_km: float) -> Fraction:
    """Return the ratio of the float inputs in exact rational arithmetic."""
    return (Fraction(maximum) - Fraction(minimum)) / (Fraction(length_km) * 1000)


def _exact(run: Callable[..., Values]) -> None:
    for minimum, maximum, length_km in (
        (150.0, 520.0, 12.5),
        (242.0, 390.0, 16.3),
        (298.33, 397.17, 21.5),
        (258.72, 440.16, 15.88),
        (-12.5, 0.75, 0.0566),
    ):
        assert_within(
            run(
                elevation_min_m=minimum, elevation_max_m=maximum, length_km=length_km
            ).real("relief_ratio"),
            float(_exact_ratio(minimum, maximum, length_km)),
            rel=4.5e-16,
            reason="the exact rational ratio of the float inputs: the difference, the "
            "conversion of km to m and the quotient round once each",
        )


RELIEF_RATIO: Final = FormulaSpec(
    name="relief_ratio",
    title="Relief ratio: the relief of a watershed over a length (Schumm)",
    function="hydrolog.morphometry.terrain.relief_ratio",
    family="index",
    equation="Rh = (Hmax - Hmin) / L, L in m [m/m]",
    latex=r"R_h = \frac{H_{max} - H_{min}}{L}",
    variables=(
        _elevation(
            "elevation_min_m",
            r"H_{min}",
            "Lowest elevation of the watershed, its outlet's [m a.s.l.].",
        ),
        _elevation(
            "elevation_max_m",
            r"H_{max}",
            "Highest elevation of the watershed [m a.s.l.].",
        ),
        LENGTH,
    ),
    outputs=(
        Output(
            name="relief_ratio",
            unit="m/m",
            symbol="R_h",
            description="Relief ratio: the relief over the length.",
            physical=Range(low=0.0, low_inclusive=False),
        ),
    ),
    sources=(_BASCIK_DROP, _WARTALSKA_DROP),
    constraints=(
        Constraint(
            name="rises_above_outlet",
            cls="physical",
            check=lambda x: x.real("elevation_max_m") > x.real("elevation_min_m"),
            text="Hmax > Hmin: a watershed drains to its outlet, so it rises above it",
            source=_BASCIK_DROP,
            satisfied={"elevation_min_m": 150.0, "elevation_max_m": 520.0},
            boundary={"elevation_min_m": 300.0, "elevation_max_m": 300.0},
            boundary_holds=False,
            violated={"elevation_min_m": 300.0, "elevation_max_m": 299.0},
        ),
        Constraint(
            name="within_float64",
            cls="precondition",
            check=lambda x: math.isfinite(_ratio(x)),
            text="(Hmax - Hmin) / L lies within float64: no relief is 10^300 times its "
            "length",
            source=_BASCIK_DROP,
            satisfied={"elevation_min_m": 150.0, "length_km": 12.5},
            violated={
                "elevation_min_m": 150.0,
                "elevation_max_m": 520.0,
                "length_km": 5e-324,
            },
        ),
    ),
    constants=(
        Constant(
            name="percent",
            value=100.0,
            unit="% per m/m",
            symbol="100",
            source=Source(
                citation="BIPM (2019). The International System of Units (SI), 9th "
                "edition, version 4.01",
                locator="section 5.4.7: the symbol % (percent) is the number 0.01; "
                "the slopes of TerrainAnalysis in percent",
                url="https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf",
            ),
        ),
    ),
    properties=Properties(
        units="homogeneous",
        monotonic={"elevation_min_m": -1, "elevation_max_m": 1, "length_km": -1},
        scalings=(
            Scaling(
                name="units_of_length",
                inputs={"elevation_min_m": 1, "elevation_max_m": 1, "length_km": 1},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="elevations and length scaled by 2 are exact in binary, and "
                    "so are their difference, the conversion and the quotient",
                ),
            ),
        ),
        limits=(
            Limit(
                name="exact_rational",
                text="Rh equals (Hmax - Hmin) / (1000 L) of the float inputs in exact "
                "rational arithmetic",
                check=_exact,
            ),
        ),
    ),
    validation="none: a ratio of measured quantities, which its sources compare with "
    "no observations",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "Rh in m/m (dimensionless), the relief in m over L converted from km to m "
            "by the units table; Baścik (2006) and Wartalska print it in m/km (per "
            "mille)"
        ),
        (
            "the relief of the whole watershed, its highest point minus its outlet; "
            "Baścik (2006, p. 23) notes that hydrological practice may take the water "
            "level at the outlet"
        ),
        (
            "L the length_km of the watershed for the relief ratio (Schumm's L is the "
            "longest dimension parallel to the main drainage line, Baścik's Lm the "
            "valley length); TerrainAnalysis gives the same ratio as the watershed "
            "slope, which is not the mean slope of the land, and over the channel "
            "length as the slope of the main channel, whose drop is then the "
            "watershed's relief, not the channel's head minus its mouth"
        ),
    ),
    traps={
        "difference_denominator": "the relief Hmax - Hmin is a difference of inputs in "
        "the numerator: equal elevations are refused by the constraint "
        "rises_above_outlet (its boundary case)",
        "singular_at_bound": "range cases length_km-physical_low_*: Rh grows as 1/L; a "
        "value beyond float64 is refused by the precondition within_float64",
        "gap_propagation": "type cases elevation_min_m-nan and the other inputs': a "
        "gap is refused",
    },
    reference_cases=("tests/fixtures/formulas/morphometry-cases.json",),
    oracles=(
        Oracle(
            kind="exact",
            description="(Hmax - Hmin) / (1000 L) of the float inputs in exact "
            "rational arithmetic (fractions), rounded once",
            test="tests/unit/test_formulas_relief.py (limit exact_rational)",
        ),
    ),
    base={"elevation_min_m": 150.0, "elevation_max_m": 520.0, "length_km": 12.5},
)

SPECS: Final[tuple[FormulaSpec, ...]] = (RELIEF_RATIO,)
"""The spec of the module."""

MIDPOINT_ELEVATION: Final = TierBSpec(
    name="midpoint_elevation",
    function="hydrolog.morphometry.terrain.TerrainAnalysis",
    definition="H_mean = (Hmin + Hmax) / 2, the mean elevation TerrainAnalysis assumes "
    "when none is given [m a.s.l.]",
    convention="an approximation, with the notice mean_elevation_approximated where "
    "Hydrolog reports it; the area-weighted mean of the DEM (Baścik 2006, eq. 1.2.8, "
    "HypsometricCurve.mean_elevation) is to be preferred",
    source=Source(
        citation=BASCIK,
        locator="eq. (1.2.5): the mean elevation approximated by the mean of the "
        "highest and the lowest",
        url=BASCIK_URL,
    ),
)

TIER_B: Final[tuple[TierBSpec, ...]] = (MIDPOINT_ELEVATION,)
"""The Tier B formula of the module (CMP-2.2)."""


def relief_ratio(
    elevation_min_m: float, elevation_max_m: float, length_km: float
) -> float:
    """Return the relief over a length, spec relief_ratio.

    Parameters
    ----------
    elevation_min_m : float
        Lowest elevation, the outlet's [m a.s.l.].
    elevation_max_m : float
        Highest elevation [m a.s.l.].
    length_km : float
        Length over which the relief is taken [km]: the watershed's for the relief
        ratio, the main channel's for its slope.

    Returns
    -------
    float
        Relief ratio [m/m].

    Raises
    ------
    InvalidParameterError
        If the spec refuses an input (``details.reason``, ``details.option``) or the
        highest elevation is not above the lowest (``details.constraint``).
    """
    x = checked_inputs(
        RELIEF_RATIO,
        elevation_min_m=elevation_min_m,
        elevation_max_m=elevation_max_m,
        length_km=length_km,
    )
    return checked_outputs(RELIEF_RATIO, {"relief_ratio": _ratio(x)}).real(
        "relief_ratio"
    )


@dataclass
class ElevationParameters(JsonResultMixin):
    """
    Elevation parameters of a watershed.

    Attributes
    ----------
    elevation_min_m : float
        Minimum elevation (outlet) [m a.s.l.].
    elevation_max_m : float
        Maximum elevation [m a.s.l.].
    elevation_mean_m : float
        Mean elevation [m a.s.l.].
    relief_m : float
        Relief (elevation difference) H = max - min [m].
    relief_ratio : float
        Relief ratio [m/m], spec ``relief_ratio``.
    """

    elevation_min_m: float
    elevation_max_m: float
    elevation_mean_m: float
    relief_m: float
    relief_ratio: float


@dataclass
class SlopeParameters(JsonResultMixin):
    """
    Slope parameters of a watershed, from the relief ratio (spec ``relief_ratio``).

    Attributes
    ----------
    watershed_slope_percent : float
        Watershed slope: the relief ratio over the watershed length [%].
    watershed_slope_m_per_m : float
        The same [m/m].
    channel_slope_percent : float
        Main channel slope: the relief over the channel length [%].
    channel_slope_m_per_m : float
        The same [m/m].
    """

    watershed_slope_percent: float
    watershed_slope_m_per_m: float
    channel_slope_percent: float
    channel_slope_m_per_m: float


class TerrainAnalysis:
    """
    Analyze terrain parameters of a watershed.

    Provides methods to calculate elevation statistics and slope
    parameters from watershed data.

    Parameters
    ----------
    elevation_min_m : float
        Minimum elevation at outlet [m a.s.l.].
    elevation_max_m : float
        Maximum elevation in watershed [m a.s.l.].
    elevation_mean_m : float, optional
        Mean elevation [m a.s.l.]. If not provided, the midpoint of the minimum and
        the maximum (the Tier B row ``midpoint_elevation``).
    length_km : float
        Watershed length [km]. Used for relief ratio.
    channel_length_km : float, optional
        Main channel length [km]. If not provided, uses watershed length.

    Examples
    --------
    >>> terrain = TerrainAnalysis(
    ...     elevation_min_m=150.0,
    ...     elevation_max_m=520.0,
    ...     elevation_mean_m=340.0,
    ...     length_km=12.0,
    ...     channel_length_km=15.0
    ... )
    >>> elev = terrain.get_elevation_parameters()
    >>> print(f"Relief: {elev.relief_m} m")
    Relief: 370.0 m

    Create from dictionary (e.g., API response):

    >>> data = {"elevation_min_m": 150.0, "elevation_max_m": 520.0,
    ...         "length_km": 12.0, "elevation_mean_m": 340.0}
    >>> terrain = TerrainAnalysis.from_dict(data)
    """

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TerrainAnalysis:
        """
        Create TerrainAnalysis from a dictionary.

        This method is designed for easy integration with JSON APIs
        and external data sources like Hydrograf.

        Parameters
        ----------
        data : dict
            Dictionary with terrain parameters. Required keys:
            elevation_min_m, elevation_max_m, length_km.
            Optional keys: elevation_mean_m, channel_length_km.

        Returns
        -------
        TerrainAnalysis
            New instance with values from dictionary.

        Raises
        ------
        KeyError
            If required keys are missing.
        InvalidParameterError
            If parameter values are invalid.

        Examples
        --------
        >>> data = {"elevation_min_m": 150.0, "elevation_max_m": 520.0,
        ...         "length_km": 12.0}
        >>> terrain = TerrainAnalysis.from_dict(data)
        >>> print(f"Relief: {terrain.relief_m} m")
        Relief: 370.0 m

        With optional parameters:

        >>> data = {"elevation_min_m": 150.0, "elevation_max_m": 520.0,
        ...         "length_km": 12.0, "elevation_mean_m": 340.0,
        ...         "channel_length_km": 15.0}
        >>> terrain = TerrainAnalysis.from_dict(data)
        """
        return cls(
            elevation_min_m=data["elevation_min_m"],
            elevation_max_m=data["elevation_max_m"],
            length_km=data["length_km"],
            elevation_mean_m=data.get("elevation_mean_m"),
            channel_length_km=data.get("channel_length_km"),
        )

    def __init__(
        self,
        elevation_min_m: float,
        elevation_max_m: float,
        length_km: float,
        elevation_mean_m: float | None = None,
        channel_length_km: float | None = None,
    ) -> None:
        """
        Initialize terrain analysis.

        Parameters
        ----------
        elevation_min_m : float
            Minimum elevation at outlet [m a.s.l.].
        elevation_max_m : float
            Maximum elevation in watershed [m a.s.l.].
        length_km : float
            Watershed length [km].
        elevation_mean_m : float, optional
            Mean elevation [m a.s.l.].
        channel_length_km : float, optional
            Main channel length [km].

        Raises
        ------
        InvalidParameterError
            If the spec ``relief_ratio`` refuses the elevations with the watershed
            length or with the channel length, or the mean elevation lies outside
            the minimum and the maximum.
        """
        x = checked_inputs(
            RELIEF_RATIO,
            elevation_min_m=elevation_min_m,
            elevation_max_m=elevation_max_m,
            length_km=length_km,
        )
        self.elevation_min_m = x.real("elevation_min_m")
        self.elevation_max_m = x.real("elevation_max_m")
        self.length_km = x.real("length_km")

        # Default mean elevation as midpoint if not provided
        if elevation_mean_m is None:
            self.elevation_mean_m = (self.elevation_min_m + self.elevation_max_m) / 2.0
        else:
            if not self.elevation_min_m <= elevation_mean_m <= self.elevation_max_m:
                raise InvalidParameterError(
                    f"elevation_mean_m ({elevation_mean_m}) must be between "
                    f"min ({elevation_min_m}) and max ({elevation_max_m})"
                )
            self.elevation_mean_m = elevation_mean_m

        # Default channel length to watershed length if not provided
        if channel_length_km is None:
            self.channel_length_km = self.length_km
        else:
            self.channel_length_km = checked_inputs(
                RELIEF_RATIO,
                elevation_min_m=elevation_min_m,
                elevation_max_m=elevation_max_m,
                length_km=channel_length_km,
            ).real("length_km")

    @property
    def relief_m(self) -> float:
        """Relief (elevation difference) [m]."""
        return self.elevation_max_m - self.elevation_min_m

    @property
    def relief_ratio(self) -> float:
        """Relief ratio over the watershed length [m/m] (:func:`relief_ratio`)."""
        return relief_ratio(self.elevation_min_m, self.elevation_max_m, self.length_km)

    def watershed_slope(self) -> tuple[float, float]:
        """
        Calculate average watershed slope.

        Uses the relief ratio as an approximation of average slope.

        Returns
        -------
        tuple[float, float]
            (slope_percent, slope_m_per_m)

        Notes
        -----
        This is a simplified calculation. For more accurate slope,
        use DEM-based analysis with actual slope distribution.
        """
        slope_m_per_m = self.relief_ratio
        slope_percent = slope_m_per_m * RELIEF_RATIO.constant("percent")
        return slope_percent, slope_m_per_m

    def channel_slope(self) -> tuple[float, float]:
        """
        Calculate main channel slope.

        The relief of the watershed over the channel length (:func:`relief_ratio`).

        Returns
        -------
        tuple[float, float]
            (slope_percent, slope_m_per_m)
        """
        slope_m_per_m = relief_ratio(
            self.elevation_min_m, self.elevation_max_m, self.channel_length_km
        )
        slope_percent = slope_m_per_m * RELIEF_RATIO.constant("percent")
        return slope_percent, slope_m_per_m

    def get_elevation_parameters(self) -> ElevationParameters:
        """
        Get all elevation parameters.

        Returns
        -------
        ElevationParameters
            Dataclass with elevation statistics.
        """
        return ElevationParameters(
            elevation_min_m=self.elevation_min_m,
            elevation_max_m=self.elevation_max_m,
            elevation_mean_m=self.elevation_mean_m,
            relief_m=self.relief_m,
            relief_ratio=self.relief_ratio,
        )

    def get_slope_parameters(self) -> SlopeParameters:
        """
        Get all slope parameters.

        Returns
        -------
        SlopeParameters
            Dataclass with slope statistics.
        """
        ws_pct, ws_m = self.watershed_slope()
        ch_pct, ch_m = self.channel_slope()

        return SlopeParameters(
            watershed_slope_percent=ws_pct,
            watershed_slope_m_per_m=ws_m,
            channel_slope_percent=ch_pct,
            channel_slope_m_per_m=ch_m,
        )
