"""Hydrometrics module for water level and discharge measurements.

Provides:
- Rating curve fitting Q = a × (H - H₀)^b
- Water level frequency and duration analysis
- Rybczyński method for water level zone delimitation
"""

from hydrolog.hydrometrics.rating_curve import (
    FrequencyDistributionResult,
    RatingCurve,
    RatingCurveResult,
    WaterLevelFrequency,
    WaterLevelZones,
)

__all__: list[str] = [
    "RatingCurve",
    "RatingCurveResult",
    "WaterLevelFrequency",
    "WaterLevelZones",
    "FrequencyDistributionResult",
]
