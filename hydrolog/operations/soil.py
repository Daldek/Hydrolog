"""Operations of the group ``soil``: soil texture and Hydrologic Soil Groups (HSG).

The USDA texture class and HSG of one soil sample, HSG GeoTIFFs from clay, sand and
silt rasters, and area statistics of HSG rasters (:mod:`hydrolog.soil`). The raster
operations need the extra ``hydrolog[raster]``. The functions are re-exported by
:mod:`hydrolog.operations`.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.exceptions import InvalidParameterError
from hydrolog.soil import (
    HSG_CODES,
    TEXTURE_CLASSES,
    HsgRasterResult,
    HsgStatistics,
    classify_usda_texture,
    hsg_from_rasters,
    hsg_statistics,
    texture_to_hsg,
)

__all__ = ["SoilTextureResult", "soil_hsg", "soil_hsg_stats", "soil_texture"]


@dataclass
class SoilTextureResult(JsonResultMixin):
    """USDA texture class and Hydrologic Soil Group of a soil sample.

    Attributes
    ----------
    texture_class : str
        USDA texture class (``"sand"``, ``"loamy_sand"``, ``"sandy_loam"``,
        ``"loam"``, ``"silt_loam"``, ``"silt"``, ``"sandy_clay_loam"``,
        ``"clay_loam"``, ``"silty_clay_loam"``, ``"sandy_clay"``, ``"silty_clay"``
        or ``"clay"``).
    texture_code : int
        Code of the class, 1-12 (the order above).
    hsg : str
        Hydrologic Soil Group ``"A"``, ``"B"``, ``"C"`` or ``"D"``.
    hsg_code : int
        Raster code of the group: 1 for A ... 4 for D.
    """

    texture_class: str
    texture_code: int
    hsg: str
    hsg_code: int


def soil_texture(*, clay: float, sand: float, silt: float) -> SoilTextureResult:
    """USDA texture class and Hydrologic Soil Group (``soil texture``).

    Classifies the sample with the USDA texture triangle
    (:func:`hydrolog.soil.classify_usda_texture`) and maps the class to its
    Hydrologic Soil Group (:func:`hydrolog.soil.texture_to_hsg`; the table of
    Kartograf ADR-025, milder than TR-55 for ``sandy_loam``, ``clay_loam`` and
    ``silty_clay_loam``).

    Parameters
    ----------
    clay, sand, silt : float
        Amounts of the three fractions, not negative, in any unit shared by the three
        (percent, g/kg...); they are compared with their total and need not sum to
        100.

    Returns
    -------
    SoilTextureResult
        Texture class and code, HSG letter and code.

    Raises
    ------
    InvalidParameterError
        If an amount is not a finite number, is negative, or all three are zero (no
        soil data).
    """
    name = classify_usda_texture(clay=clay, sand=sand, silt=silt)
    if clay + sand + silt <= 0:
        raise InvalidParameterError(
            "clay, sand and silt must not all be zero (no soil data)",
            details={"option": "clay", "reason": "no_data"},
            hint="Give the contents of the three fractions.",
        )
    group = texture_to_hsg(name)
    return SoilTextureResult(
        texture_class=name,
        texture_code=TEXTURE_CLASSES[name],
        hsg=group,
        hsg_code=HSG_CODES[group],
    )


def soil_hsg(
    *,
    clay_path: str | os.PathLike[str],
    sand_path: str | os.PathLike[str],
    silt_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
) -> OperationOutput:
    """HSG GeoTIFF from clay, sand and silt rasters (``soil hsg``).

    Classifies every cell with the USDA texture triangle and the texture to HSG table
    and writes a single-band ``uint8`` GeoTIFF (Deflate, nodata 0; 1-4 are the groups
    A-D) on the grid of the inputs (:func:`hydrolog.soil.hsg_from_rasters`). Needs the
    extra ``hydrolog[raster]``.

    Parameters
    ----------
    clay_path, sand_path, silt_path : str or os.PathLike
        Rasters of the clay, sand and silt amounts (any unit shared by the three, e.g.
        the g/kg of SoilGrids) on one grid (same CRS, transform and shape).
    output_path : str or os.PathLike
        HSG GeoTIFF to write; missing directories are created and an existing file is
        replaced.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.soil.HsgRasterResult`; the written file is
        listed in ``files``.

    Raises
    ------
    MissingDependencyError
        If ``rasterio`` or ``pyproj`` is not installed.
    NotFoundError
        If an input raster does not exist.
    InputDataError
        If an input cannot be read, has no CRS, the grids differ or an amount is
        invalid.
    InvalidParameterError
        If ``output_path`` is one of the inputs.
    OutputError
        If the output cannot be written.
    """
    result: HsgRasterResult = hsg_from_rasters(
        Path(os.fspath(clay_path)),
        Path(os.fspath(sand_path)),
        Path(os.fspath(silt_path)),
        Path(os.fspath(output_path)),
    )
    return OperationOutput(result, files=(result.output_path,))


def soil_hsg_stats(
    *,
    hsg_path: str | os.PathLike[str],
    bbox: Sequence[float] | None = None,
    bbox_crs: str | None = None,
) -> OperationOutput:
    """Area statistics of an HSG raster (``soil hsg-stats``).

    Count, area [m2, ha] and percent of every group A-D and of the no-data class
    (:func:`hydrolog.soil.hsg_statistics`), optionally inside a bounding box (cells cut
    by its edges count with their share). Needs the extra ``hydrolog[raster]``.

    Parameters
    ----------
    hsg_path : str or os.PathLike
        HSG GeoTIFF: codes 1-4 for A-D, 0 for no data.
    bbox : sequence of float, optional
        Area of interest ``(min_x, min_y, max_x, max_y)``; x is easting or longitude,
        y is northing or latitude. Default: the whole raster.
    bbox_crs : str, optional
        CRS of ``bbox`` (e.g. ``"EPSG:2180"``); default: the CRS of the raster.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.soil.HsgStatistics`; a notice reports a
        ``bbox`` that does not overlap the raster (all areas are then zero).

    Raises
    ------
    MissingDependencyError
        If ``rasterio`` or ``pyproj`` is not installed.
    NotFoundError
        If ``hsg_path`` does not exist.
    InputDataError
        If the file cannot be read, has no CRS or is not an HSG raster.
    InvalidParameterError
        If ``bbox`` or ``bbox_crs`` is invalid, or ``bbox_crs`` is given without
        ``bbox``.
    """
    result: HsgStatistics = hsg_statistics(
        Path(os.fspath(hsg_path)), bbox=bbox, bbox_crs=bbox_crs
    )
    notices: list[Notice] = []
    if bbox is not None and result.total_area_m2 == 0:
        notices.append(
            Notice(
                "warning",
                "empty_area",
                "bbox does not overlap the raster: all counts and areas are zero",
            )
        )
    return OperationOutput(result, notices)
