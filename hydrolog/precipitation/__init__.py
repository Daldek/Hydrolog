"""Precipitation module for hyetograms and interpolation."""

from hydrolog.precipitation.hietogram import (
    HietogramResult,
    Hietogram,
    BlockHietogram,
    TriangularHietogram,
    BetaHietogram,
    EulerIIHietogram,
)

from hydrolog.precipitation.interpolation import (
    Station,
    ThiessenResult,
    IDWResult,
    IsohyetResult,
    thiessen_polygons,
    inverse_distance_weighting,
    areal_precipitation_idw,
    isohyet_method,
    arithmetic_mean,
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
