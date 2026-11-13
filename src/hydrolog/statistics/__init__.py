"""Statistical analysis module for hydrological data.

Provides:
- Characteristic values of the first and second degree (Polish system: NNQ–WWQ),
  from a daily series or IMGW-PIB's half-year characteristics
- Events and days beyond a level (threshold level method)
- Duration curves and class frequencies
- Runoff volumes
- The flow regime (Pardé's coefficients, Dynowska's types), the seasonality of annual
  extremes (circular statistics of their dates) and the harmonics of the annual cycle
- Baseflow (Lyne and Hollick's filter) and the recession constant
- Flood frequency analysis (GEV, Log-Normal, Pearson III, Weibull)
- Low-flow frequency analysis (Fisher-Tippett, drought sequences)
- Mann-Kendall trend test for series stationarity, with Sen's slope
- Homogeneity tests of a split series (Mann-Whitney U, Kolmogorov-Smirnov, Pettitt)
"""

from hydrolog.statistics._types import EmpiricalFrequency, LowFlowEmpiricalFrequency
from hydrolog.statistics.baseflow import (
    BaseflowSeparation,
    BaseflowYear,
    RecessionConstant,
    baseflow_separation,
    lyne_hollick_filter,
    recession_constant,
)
from hydrolog.statistics.characteristic import (
    CHARACTERISTIC_KEYS,
    CharacteristicValues,
    DailyStatistics,
    FirstDegreeValues,
    HalfYearExtremes,
    HalfYearPart,
    HalfYearValues,
    MonthlyStatistics,
    PeriodValues,
    SecondDegreeValues,
    annual_extremes_from_half_years,
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
from hydrolog.statistics.harmonics import (
    AnnualCycle,
    Harmonic,
    HarmonicFit,
    HarmonicYear,
    annual_cycle,
    harmonic_fit,
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
    fit_fisher_tippett_minima,
)
from hydrolog.statistics.regime import (
    FlowRegime,
    RegimeCriteria,
    RegimeType,
    dynowska_regime_type,
    flow_regime,
    seasonality_index,
)
from hydrolog.statistics.seasonality import (
    CircularMean,
    DatedExtreme,
    ExtremeSeasonality,
    circular_mean_date,
    daily_extremes,
    extreme_seasonality,
    half_year_extremes,
)
from hydrolog.statistics.stationarity import (
    MannKendallResult,
    SenSlope,
    mann_kendall_test,
    sen_slope,
)
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
    "HalfYearExtremes",
    "HalfYearPart",
    "HalfYearValues",
    "PeriodValues",
    "SecondDegreeValues",
    "annual_extremes_from_half_years",
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
    # Regime
    "FlowRegime",
    "RegimeCriteria",
    "RegimeType",
    "dynowska_regime_type",
    "flow_regime",
    "seasonality_index",
    # Seasonality of annual extremes
    "CircularMean",
    "DatedExtreme",
    "ExtremeSeasonality",
    "circular_mean_date",
    "daily_extremes",
    "extreme_seasonality",
    "half_year_extremes",
    # Harmonics of the annual cycle
    "AnnualCycle",
    "Harmonic",
    "HarmonicFit",
    "HarmonicYear",
    "annual_cycle",
    "harmonic_fit",
    # Baseflow
    "BaseflowSeparation",
    "BaseflowYear",
    "RecessionConstant",
    "baseflow_separation",
    "lyne_hollick_filter",
    "recession_constant",
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
    "fit_fisher_tippett_minima",
    # Stationarity
    "mann_kendall_test",
    "MannKendallResult",
    "SenSlope",
    "sen_slope",
    # Homogeneity
    "homogeneity_tests",
    "HomogeneityResult",
    "TwoSampleTestResult",
    "PettittResult",
]
