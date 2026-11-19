"""Precipitation module for hyetograms and interpolation."""

from hydrolog.precipitation.hietogram import (
    BetaHietogram,
    BlockHietogram,
    EulerIIHietogram,
    EulerIIStorm,
    Hietogram,
    HietogramResult,
    TriangularHietogram,
    TriangularStorm,
    beta_hyetograph,
    block_hyetograph,
    euler_ii_hyetograph,
    triangular_hyetograph,
)
from hydrolog.precipitation.interpolation import (
    GaugeWeights,
    IDWResult,
    IsohyetResult,
    PointEstimate,
    Station,
    ThiessenResult,
    areal_mean_precipitation,
    areal_precipitation_idw,
    arithmetic_mean,
    idw_precipitation,
    inverse_distance_weighting,
    isohyet_method,
    isohyet_precipitation,
    thiessen_polygons,
    thiessen_precipitation,
)

__all__ = [
    # Hietograms
    "HietogramResult",
    "Hietogram",
    "BlockHietogram",
    "TriangularHietogram",
    "BetaHietogram",
    "EulerIIHietogram",
    # Hietograms by their specs
    "TriangularStorm",
    "EulerIIStorm",
    "block_hyetograph",
    "triangular_hyetograph",
    "beta_hyetograph",
    "euler_ii_hyetograph",
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
    # Areal precipitation by its specs
    "GaugeWeights",
    "PointEstimate",
    "areal_mean_precipitation",
    "thiessen_precipitation",
    "idw_precipitation",
    "isohyet_precipitation",
]
