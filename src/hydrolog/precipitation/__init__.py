"""Precipitation module for hyetograms and interpolation."""

from hydrolog.precipitation.hietogram import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    Hietogram,
    HietogramResult,
    TriangularHietogram,
)
from hydrolog.precipitation.interpolation import (
    IDWResult,
    IsohyetResult,
    Station,
    ThiessenResult,
    areal_precipitation_idw,
    arithmetic_mean,
    inverse_distance_weighting,
    isohyet_method,
    thiessen_polygons,
)

__all__ = [
    # Hietograms
    "HietogramResult",
    "Hietogram",
    "BlockHietogram",
    "TriangularHietogram",
    "BetaHietogram",
    "EulerIIHietogram",
    # Interpolation
    "Station",
    "ThiessenResult",
    "IDWResult",
    "IsohyetResult",
    "thiessen_polygons",
    "inverse_distance_weighting",
    "areal_precipitation_idw",
    "isohyet_method",
    "arithmetic_mean",
]
