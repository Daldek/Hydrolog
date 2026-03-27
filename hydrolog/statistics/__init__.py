"""Statistical analysis module for hydrological data.

Provides:
- Characteristic flow values (Polish system: NNQ–WWQ)
- Flood frequency analysis (GEV, Log-Normal, Pearson III, Weibull)
- Low-flow frequency analysis (Fisher-Tippett, drought sequences)
- Mann-Kendall trend test for series stationarity
"""

from hydrolog.statistics._types import EmpiricalFrequency
from hydrolog.statistics.characteristic import (
    CharacteristicValues,
    DailyStatistics,
    MonthlyStatistics,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
)
from hydrolog.statistics.high_flows import (
    FloodFrequencyAnalysis,
    FrequencyAnalysisResult,
)
from hydrolog.statistics.low_flows import (
    LowFlowAnalysis,
    LowFlowAnalysisResult,
    LowFlowFrequencyResult,
    LowFlowSequence,
)
from hydrolog.statistics.stationarity import MannKendallResult, mann_kendall_test

__all__ = [
    # Characteristic values
    "CharacteristicValues",
    "calculate_characteristic_values",
    "DailyStatistics",
    "MonthlyStatistics",
    "calculate_daily_statistics",
    "calculate_monthly_statistics",
    # Flood frequency
    "FloodFrequencyAnalysis",
    "FrequencyAnalysisResult",
    "EmpiricalFrequency",
    # Low-flow
    "LowFlowAnalysis",
    "LowFlowFrequencyResult",
    "LowFlowSequence",
    "LowFlowAnalysisResult",
    # Stationarity
    "mann_kendall_test",
    "MannKendallResult",
]
