"""Statistical analysis module for hydrological data.

Provides:
- Characteristic values of the first and second degree (Polish system: NNQ–WWQ),
  from a daily series or IMGW-PIB's half-year characteristics
- Events and days beyond a level (threshold level method)
- Duration curves and class frequencies
- Runoff volumes
- Flood frequency analysis (GEV, Log-Normal, Pearson III, Weibull)
- Low-flow frequency analysis (Fisher-Tippett, drought sequences)
- Mann-Kendall trend test for series stationarity
- Homogeneity tests of a split series (Mann-Whitney U, Kolmogorov-Smirnov, Pettitt)
"""

from hydrolog.statistics._types import EmpiricalFrequency, LowFlowEmpiricalFrequency
from hydrolog.statistics.characteristic import (
    CHARACTERISTIC_KEYS,
    CharacteristicValues,
    DailyStatistics,
    FirstDegreeValues,
    HalfYearPart,
    HalfYearValues,
    MonthlyStatistics,
    PeriodValues,
    SecondDegreeValues,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
    characteristic_labels,
    characteristic_values_from_half_years,
    first_degree_labels,
)
from hydrolog.statistics.duration import (
    CURVE_PERCENTS,
    DEFAULT_PERCENTS,
    DurationClass,
    DurationCurve,
    ModalClass,
    duration_curve,
    exceedance_values,
)
from hydrolog.statistics.events import (
    ThresholdEvent,
    ThresholdEvents,
    ThresholdEventYear,
    threshold_events,
    threshold_runs,
)
from hydrolog.statistics.high_flows import (
    FIT_METHODS,
    FitMethod,
    FloodFrequencyAnalysis,
    FrequencyAnalysisResult,
)
from hydrolog.statistics.homogeneity import (
    HomogeneityResult,
    PettittResult,
    TwoSampleTestResult,
    homogeneity_tests,
)
from hydrolog.statistics.low_flows import (
    LowFlowAnalysis,
    LowFlowAnalysisResult,
    LowFlowFrequencyResult,
    LowFlowSequence,
)
from hydrolog.statistics.stationarity import MannKendallResult, mann_kendall_test
from hydrolog.statistics.volumes import (
    DAY_SECONDS,
    MonthVolume,
    RunoffVolumes,
    YearVolume,
    runoff_volumes,
)

__all__ = [
    # Characteristic values
    "CHARACTERISTIC_KEYS",
    "CharacteristicValues",
    "FirstDegreeValues",
    "HalfYearPart",
    "HalfYearValues",
    "PeriodValues",
    "SecondDegreeValues",
    "calculate_characteristic_values",
    "characteristic_labels",
    "characteristic_values_from_half_years",
    "first_degree_labels",
    "DailyStatistics",
    "MonthlyStatistics",
    "calculate_daily_statistics",
    "calculate_monthly_statistics",
    # Events beyond a level
    "ThresholdEvent",
    "ThresholdEventYear",
    "ThresholdEvents",
    "threshold_events",
    "threshold_runs",
    # Duration curves
    "CURVE_PERCENTS",
    "DEFAULT_PERCENTS",
    "DurationClass",
    "DurationCurve",
    "ModalClass",
    "duration_curve",
    "exceedance_values",
    # Runoff volumes
    "DAY_SECONDS",
    "MonthVolume",
    "RunoffVolumes",
    "YearVolume",
    "runoff_volumes",
    # Flood frequency
    "FloodFrequencyAnalysis",
    "FrequencyAnalysisResult",
    "FIT_METHODS",
    "FitMethod",
    "EmpiricalFrequency",
    # Low-flow
    "LowFlowAnalysis",
    "LowFlowFrequencyResult",
    "LowFlowEmpiricalFrequency",
    "LowFlowSequence",
    "LowFlowAnalysisResult",
    # Stationarity
    "mann_kendall_test",
    "MannKendallResult",
    # Homogeneity
    "homogeneity_tests",
    "HomogeneityResult",
    "TwoSampleTestResult",
    "PettittResult",
]
