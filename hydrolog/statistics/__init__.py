"""Statistical analysis module for hydrological data.

Provides:
- Characteristic flow values (Polish system: NNQ–WWQ)
- Flood frequency analysis (GEV, Log-Normal, Pearson III, Weibull)
- Low-flow frequency analysis (Fisher-Tippett, drought sequences)
- Mann-Kendall trend test for series stationarity
"""

from hydrolog.statistics.low_flows import (
    LowFlowAnalysis,
    LowFlowAnalysisResult,
    LowFlowFrequencyResult,
    LowFlowSequence,
)
from hydrolog.statistics.stationarity import MannKendallResult, mann_kendall_test

__all__: list[str] = [
    "LowFlowAnalysis",
    "LowFlowAnalysisResult",
    "LowFlowFrequencyResult",
    "LowFlowSequence",
    "MannKendallResult",
    "mann_kendall_test",
]
