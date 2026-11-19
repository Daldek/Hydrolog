"""Hydrometrics module for water level and discharge measurements.

Provides:
- Rating curve fitting Q = a × (H - H₀)^b (specs ``rating_curve``,
  ``rating_curve_fit`` and ``rating_curve_plausibility``)
- Water level frequency and duration analysis
- Rybczyński method for water level zone delimitation (spec ``rybczynski_zones``)
"""

from hydrolog.hydrometrics.rating_curve import (
    FrequencyDistributionResult,
    RatingCurve,
    RatingCurveResult,
    RatingPlausibility,
    WaterLevelFrequency,
    WaterLevelZones,
    fit_rating_curve,
    rating_curve_plausibility,
    rating_discharge,
    rybczynski_zones,
)

__all__: list[str] = [
    "RatingCurve",
    "RatingCurveResult",
    "RatingPlausibility",
    "WaterLevelFrequency",
    "WaterLevelZones",
    "FrequencyDistributionResult",
    "fit_rating_curve",
    "rating_curve_plausibility",
    "rating_discharge",
    "rybczynski_zones",
]
