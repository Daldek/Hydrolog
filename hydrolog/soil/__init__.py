"""Hydrologic Soil Groups (HSG) from soil texture.

The soil input of the SCS-CN method: classifies the USDA soil texture from clay,
sand and silt contents, maps it to the Hydrologic Soil Groups A-D and summarises
HSG rasters as areas per group.

- :mod:`hydrolog.soil.texture` - USDA texture triangle and texture -> HSG table
  (NumPy only).
- :mod:`hydrolog.soil.hsg` - :func:`classify_hsg` and HSG area statistics on arrays
  (NumPy only).
- :mod:`hydrolog.soil.raster` - GeoTIFF input/output (extra ``hydrolog[raster]``:
  ``rasterio`` and ``pyproj``, imported lazily).

Ported from Kartograf 0.8.0 (``kartograf.hydrology.hsg``, Kartograf ADR-025):
Kartograf downloads the SoilGrids clay, sand and silt rasters, Hydrolog computes
the HSG.

Examples
--------
>>> from hydrolog.soil import classify_hsg, classify_usda_texture
>>> classify_usda_texture(clay=200, sand=400, silt=400)  # g/kg
'loam'
>>> classify_hsg([200], [400], [400]).tolist()  # loam -> B
[2]
"""

from hydrolog.soil.hsg import (
    HSG_CODES,
    HSG_DESCRIPTIONS,
    HsgGroupStatistics,
    HsgStatistics,
    classify_hsg,
    hsg_statistics_array,
)
from hydrolog.soil.raster import HsgRasterResult, hsg_from_rasters, hsg_statistics
from hydrolog.soil.texture import (
    TEXTURE_CLASSES,
    TEXTURE_NAMES,
    TEXTURE_TO_HSG,
    classify_usda_texture,
    classify_usda_texture_array,
    texture_to_hsg,
    texture_to_hsg_array,
)

__all__ = [
    "HSG_CODES",
    "HSG_DESCRIPTIONS",
    "TEXTURE_CLASSES",
    "TEXTURE_NAMES",
    "TEXTURE_TO_HSG",
    "HsgGroupStatistics",
    "HsgRasterResult",
    "HsgStatistics",
    "classify_hsg",
    "classify_usda_texture",
    "classify_usda_texture_array",
    "hsg_from_rasters",
    "hsg_statistics",
    "hsg_statistics_array",
    "texture_to_hsg",
    "texture_to_hsg_array",
]
