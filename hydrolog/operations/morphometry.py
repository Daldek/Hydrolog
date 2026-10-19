"""Operations of the group ``morphometry``: indicators of a watershed.

Geometric, shape and terrain indicators computed from
:class:`~hydrolog.morphometry.WatershedParameters` (an inline object or the JSON file
of the integration format). The function is re-exported by :mod:`hydrolog.operations`.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import load_watershed
from hydrolog.exceptions import CalculationError
from hydrolog.morphometry import (
    ElevationParameters,
    GeometricParameters,
    ShapeIndicators,
    SlopeParameters,
    WatershedParameters,
)

__all__ = ["WatershedMorphometry", "morphometry_watershed"]


@dataclass
class WatershedMorphometry(JsonResultMixin):
    """Morphometric indicators of one watershed.

    Attributes
    ----------
    name : str or None
        Name of the watershed, when the parameters carry one.
    geometry : GeometricParameters
        Area [km2], perimeter [km], length [km] and mean width W = A / L [km].
    shape_indicators : ShapeIndicators
        Horton form factor, Gravelius compactness, Miller circularity, Schumm
        elongation and Chorley lemniscate ratio [-].
    elevation : ElevationParameters
        Minimum, maximum and mean elevation [m a.s.l.], relief [m] and relief ratio
        Rh = H / L [-].
    slopes : SlopeParameters
        Watershed slope approximated by the relief ratio and main channel slope, in
        percent and m/m.
    """

    name: str | None
    geometry: GeometricParameters
    shape_indicators: ShapeIndicators
    elevation: ElevationParameters
    slopes: SlopeParameters


def _slopes_from_relief_notice(
    parameters: WatershedParameters, slopes: SlopeParameters
) -> Notice | None:
    """Notice that slopes given in the file are not the slopes of the result.

    ``TerrainAnalysis`` derives both slopes from the relief, so ``mean_slope_m_per_m``
    and ``channel_slope_m_per_m`` of the watershed parameters are not used here,
    while ``tc watershed`` and ``hydrograph generate`` use them. The notice gives
    both values of every slope that the file also supplies.
    """
    clauses: list[str] = []
    if parameters.mean_slope_m_per_m is not None:
        clauses.append(
            f"watershed slope {slopes.watershed_slope_m_per_m:.4g} m/m (relief ratio "
            f"H/L) instead of mean_slope_m_per_m = {parameters.mean_slope_m_per_m:g} m/m"
        )
    if parameters.channel_slope_m_per_m is not None:
        clauses.append(
            f"channel slope {slopes.channel_slope_m_per_m:.4g} m/m (H / channel "
            f"length) instead of channel_slope_m_per_m = "
            f"{parameters.channel_slope_m_per_m:g} m/m"
        )
    if not clauses:
        return None
    return Notice(
        "info",
        "slopes_from_relief",
        "The slopes are computed from the relief and the slopes of the watershed "
        "parameters are not used here: " + "; ".join(clauses) + ". The commands for "
        "the time of concentration use the given slopes.",
    )


def morphometry_watershed(
    *,
    watershed: Mapping[str, Any] | None = None,
    watershed_file: str | os.PathLike[str] | None = None,
) -> OperationOutput:
    """Geometric and terrain indicators of a watershed (``morphometry watershed``).

    Builds :class:`~hydrolog.morphometry.WatershedGeometry` and
    :class:`~hydrolog.morphometry.TerrainAnalysis` from the watershed parameters
    (``WatershedParameters.to_geometry()`` and ``to_terrain()``) and collects their
    indicators. The watershed slope is the relief ratio H / L (not a DEM-derived
    slope); the main channel slope is H divided by the channel length. The slopes
    ``mean_slope_m_per_m`` and ``channel_slope_m_per_m`` that the parameters may
    carry are not used here (the time of concentration commands do use them): a
    notice gives both values.

    Parameters
    ----------
    watershed : Mapping, optional
        Inline watershed parameters (the keys of ``WatershedParameters``: required
        ``area_km2``, ``perimeter_km``, ``length_km``, ``elevation_min_m``,
        ``elevation_max_m``).
    watershed_file : str or os.PathLike, optional
        JSON file with such an object (the ``WatershedParameters.to_json()`` format).

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`WatershedMorphometry`. The notices say when the mean
        elevation was approximated by ``(min + max) / 2`` (no ``elevation_mean_m``),
        the channel length was taken equal to the watershed length (no
        ``channel_length_km``), or the parameters carry a slope that is not used
        (``slopes_from_relief``: the computed value and the given one).

    Raises
    ------
    InvalidParameterError
        If both or neither of ``watershed`` and ``watershed_file`` is given, or a
        parameter is invalid (for instance ``elevation_mean_m`` outside the elevation
        range).
    NotFoundError
        If ``watershed_file`` does not exist.
    InputDataError
        If the file is not a JSON object or holds missing or invalid parameters.
    CalculationError
        If the parameters are so extreme that an indicator overflows or divides by
        zero.
    """
    parameters = load_watershed(watershed=watershed, watershed_file=watershed_file)
    geometry = parameters.to_geometry()
    terrain = parameters.to_terrain()
    notices: list[Notice] = []
    if parameters.elevation_mean_m is None:
        notices.append(
            Notice(
                "info",
                "mean_elevation_approximated",
                "elevation_mean_m is not given: the mean elevation is approximated "
                "by (elevation_min_m + elevation_max_m) / 2",
            )
        )
    if parameters.channel_length_km is None:
        notices.append(
            Notice(
                "info",
                "channel_length_defaulted",
                "channel_length_km is not given: the channel slope is computed with "
                "the watershed length",
            )
        )
    try:
        result = WatershedMorphometry(
            name=parameters.name,
            geometry=geometry.get_parameters(),
            shape_indicators=geometry.get_shape_indicators(),
            elevation=terrain.get_elevation_parameters(),
            slopes=terrain.get_slope_parameters(),
        )
    except ArithmeticError as exc:
        raise CalculationError(
            f"The indicators cannot be computed for these parameters: {exc}",
            details={"reason": "arithmetic"},
            hint="Check the units: lengths in km, area in km2, elevations in m.",
        ) from exc
    slopes_notice = _slopes_from_relief_notice(parameters, result.slopes)
    if slopes_notice is not None:
        notices.append(slopes_notice)
    return OperationOutput(result, notices)
