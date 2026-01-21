"""Morphometric parameters module for watershed analysis."""

from hydrolog.morphometry.geometric import (
    GeometricParameters,
    ShapeIndicators,
    WatershedGeometry,
)
from hydrolog.morphometry.hypsometry import (
    HypsometricCurve,
    HypsometricResult,
)
from hydrolog.morphometry.terrain import (
    ElevationParameters,
    SlopeParameters,
    TerrainAnalysis,
)
from hydrolog.morphometry.watershed_params import WatershedParameters

__all__ = [
    # Integration interface
    "WatershedParameters",
    # Geometric
    "WatershedGeometry",
    "GeometricParameters",
    "ShapeIndicators",
    # Terrain
    "TerrainAnalysis",
    "ElevationParameters",
    "SlopeParameters",
    # Hypsometry
    "HypsometricCurve",
    "HypsometricResult",
]
