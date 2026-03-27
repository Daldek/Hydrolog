# Design: Statistics & Hydrometrics Modules for Hydrolog

**Date:** 2026-03-26
**Version:** 0.7.0 (planned)
**Status:** Approved
**Origin:** Migration from IMGWTools `code/hydro_stats.py` (removed in commit `3c571c8`, 2026-01-10)

---

## 1. Background

### 1.1 What was removed from IMGWTools

Commit `3c571c8` ("Remove legacy code") deleted `code/hydro_stats.py` (1756 lines) containing:
- Hydrological characteristic values (Polish system: NNQ–WWQ)
- Flood frequency analysis (LogNormal, GEV, Pearson III exceedance curves)
- Low-flow frequency analysis (Fisher-Tippett non-exceedance curves)
- Kolmogorov-Smirnov goodness-of-fit tests
- Low-flow drought sequence detection
- Rating curve fitting (power-law Q=f(H))
- Water level frequency/duration curves with Rybczyński zone delimitation
- 8 visualization methods (rating curves, hydrographs, histograms, CI plots, frequency curves)

### 1.2 What we're migrating

- **Layers A+B+C**: Statistical analysis, frequency analysis, visualizations
- **NOT migrating**: CSV parsing, pandas data model, meteo stats, spatial/GIS, IMGW-specific I/O

### 1.3 Approach

**Full rewrite** (Approach A) — rewrite from scratch following Hydrolog standards:
- NumPy arrays (no pandas dependency)
- Type hints, dataclass results, NumPy-style docstrings
- Every formula verified against scientific literature
- All bugs from old code fixed

---

## 2. Architecture

### 2.1 New modules

```
hydrolog/
├── statistics/                    # NEW MODULE
│   ├── __init__.py
│   ├── _hydrological_year.py      # private: year/season utilities
│   ├── _types.py                  # private: shared dataclasses (EmpiricalFrequency)
│   ├── characteristic.py          # characteristic values, daily/monthly stats, FDC
│   ├── high_flows.py              # flood frequency: LogNormal, GEV, Pearson III, Weibull
│   ├── low_flows.py               # low-flow frequency: Fisher-Tippett, drought sequences
│   └── stationarity.py            # Mann-Kendall trend test, series homogeneity
├── hydrometrics/                  # NEW MODULE
│   ├── __init__.py
│   └── rating_curve.py            # rating curve Q=f(H), Rybczyński zones
└── visualization/
    └── statistics.py              # NEW FILE: plots for statistics & hydrometrics
```

### 2.2 Dependencies

SciPy promoted from optional to required:

```toml
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",   # was optional; needed by statistics, hydrometrics, nash_iuh
]
```

### 2.3 New convention: private underscore modules

The `_hydrological_year.py` and `_types.py` files introduce a new pattern: underscore-prefixed private modules. Currently, the codebase uses underscore-prefixed private **functions** within public modules, but no private modules. This is standard Python convention and is introduced here because hydrological year utilities are shared across multiple files within `statistics/`.

### 2.4 Data model

All inputs are NumPy arrays. No pandas dependency. Data preparation (CSV → NumPy) is the responsibility of the calling application (e.g., IMGWTools).

---

## 3. Module: `hydrolog/statistics/`

### 3.1 `_hydrological_year.py` (private utilities)

```python
def hydrological_year(dates: NDArray) -> NDArray:
    """Assign hydrological year (Nov 1 – Oct 31) to each date.
    Months XI–XII → next calendar year. Months I–X → same year."""

def hydrological_day_of_year(dates: NDArray) -> NDArray:
    """Day-of-year within hydrological year (1 = Nov 1, 366 = Oct 31)."""

def split_half_years(values: NDArray, dates: NDArray) -> tuple[NDArray, NDArray]:
    """Split into winter (XI–IV) and summer (V–X) half-years."""
```

**Reference:** Polish hydrological year starts November 1 (IMGW standard).
- Winter half-year: XI–IV (November–April)
- Summer half-year: V–X (May–October)
- Source: https://pl.wikipedia.org/wiki/Rok_hydrologiczny, IMGW-PIB

### 3.2 `characteristic.py`

#### Data structures

```python
@dataclass
class CharacteristicValues:
    """Second-degree characteristic flow/stage values (Polish system)."""
    wwx: float   # max of annual maxima (highest observed)
    swx: float   # mean of annual maxima
    zwx: float   # median of annual maxima
    nwx: float   # min of annual maxima
    wsx: float   # max of annual means
    ssx: float   # mean of annual means
    zsx: float   # median of annual means
    nsx: float   # min of annual means
    wnx: float   # max of annual minima
    snx: float   # mean of annual minima
    znx: float   # median of annual minima
    nnx: float   # min of annual minima
    period_years: int
    parameter: str  # "Q" or "H"

@dataclass
class DailyStatistics:
    """Statistics per hydrological day-of-year."""
    day_of_year: NDArray        # 1..366
    max_values: NDArray
    mean_values: NDArray
    median_values: NDArray
    min_values: NDArray
    count: NDArray

@dataclass
class MonthlyStatistics:
    """Monthly statistics with confidence intervals."""
    months: NDArray             # 1..12
    max_values: NDArray
    mean_values: NDArray
    median_values: NDArray
    min_values: NDArray
    std_values: NDArray
    cv_values: NDArray          # coefficient of variation = std / mean
    skewness_values: NDArray    # Fisher-Pearson skewness coefficient
    ci_lower: NDArray
    ci_upper: NDArray
    confidence_level: float     # configurable, default 0.95
```

#### Functions

```python
def calculate_characteristic_values(
    daily_values: NDArray,
    dates: NDArray,
    parameter: str = "Q",
) -> CharacteristicValues:
    """Compute second-degree characteristic values from daily data.

    Groups by hydrological year, computes annual max/mean/min,
    then computes max/mean/median/min of each annual series.
    """

def calculate_daily_statistics(
    daily_values: NDArray,
    dates: NDArray,
) -> DailyStatistics:
    """Statistics per hydrological day-of-year across all years."""

def calculate_monthly_statistics(
    daily_values: NDArray,
    dates: NDArray,
    confidence_level: float = 0.95,
) -> MonthlyStatistics:
    """Monthly statistics with configurable confidence interval.

    CI = mean ± t × std / sqrt(n), clipped at 0.
    Uses t-Student distribution with n-1 degrees of freedom
    (correct for small samples typical in hydrology, n=20-50 years).
    """
```

#### Bugs fixed from old code

| Bug | Old behavior | New behavior |
|-----|-------------|--------------|
| SWQ computation | `mean(concat(winter_max, summer_max))` — double-weights half-years | `mean(annual_maxima)` — correct |
| ZWQ/ZNQ computation | `median(median(w), median(s))` = mean of 2 values | `median(annual_maxima/minima)` — correct |
| Hydrological year | `groupby("year").cumcount()` — calendar year | Proper Nov 1 – Oct 31 grouping |
| CI confidence level | Hardcoded 0.95 | Configurable parameter |
| CI distribution | z (normal) — incorrect for small samples | t-Student with n-1 df (7% wider at n=20) |

#### References

- Characteristic values: Polish hydrological standard (IMGW-PIB)
  - Source: https://pl.wikipedia.org/wiki/Przepływ_rzeki
  - WWQ = max of annual maxima, SWQ = mean of annual maxima, SSQ = mean of annual means, SNQ = mean of annual minima, NNQ = min of annual minima
- CI formula: t = scipy.stats.t.ppf(1 - α/2, df=n-1), CI = mean ± t × std / √n
  (t-Student with n-1 df; correct for small samples. For n=20 at 95%: t=2.093 vs z=1.960)

### 3.3 `stationarity.py` — Series homogeneity tests

Required by KZGW (2017) as a prerequisite before frequency analysis.

```python
@dataclass
class MannKendallResult:
    """Result of Mann-Kendall trend test."""
    s_statistic: float                # Mann-Kendall S statistic
    var_s: float                      # variance of S
    z_score: float                    # normalized test statistic (U ~ N(0,1))
    p_value: float                    # two-sided p-value
    trend_detected: bool              # True if |z| > z_alpha at given significance
    trend_direction: str              # "increasing", "decreasing", or "none"
    significance_level: float         # alpha used for detection

def mann_kendall_test(
    series: NDArray[np.float64],
    alpha: float = 0.05,
) -> MannKendallResult:
    """Non-parametric Mann-Kendall test for monotonic trend.

    Tests H0: no trend vs H1: monotonic trend in the series.
    KZGW (2017) requires stationarity verification before frequency analysis.

    Formula:
        S = Σ_{i=1}^{n-1} Σ_{j=i+1}^{n} sgn(x_j - x_i)
        Var(S) = n(n-1)(2n+5) / 18
        U = (S-1)/√Var(S)  if S > 0
        U = 0               if S = 0
        U = (S+1)/√Var(S)  if S < 0

    References:
        Mann (1945), Kendall (1975), KZGW (2017).
    """
```

### 3.4 `high_flows.py`

#### Data structures

```python
@dataclass
class FrequencyAnalysisResult:
    distribution_name: str           # "log_normal", "gev", "pearson3"
    parameters: dict[str, float]     # fitted parameters
    return_periods: NDArray           # e.g. [2, 5, 10, 20, 50, 100, 500, 1000]
    quantiles: NDArray                # Q_T for each return period
    exceedance_probabilities: NDArray # 1/T
    ks_statistic: float
    ks_p_value: float
    ks_valid: bool                   # False when params estimated from data
    ad_statistic: float              # Anderson-Darling (better for tails)
    ad_critical_values: dict[str, float]  # critical values at significance levels
    aic: float                       # Akaike Information Criterion (lower = better)

@dataclass
class EmpiricalFrequency:
    values_sorted: NDArray           # sorted descending
    exceedance_prob: NDArray         # plotting position
    return_periods: NDArray          # 1/P
```

#### Class

```python
class FloodFrequencyAnalysis:
    def __init__(self, annual_maxima: NDArray) -> None: ...
    def fit_log_normal(self) -> FrequencyAnalysisResult: ...
    def fit_gev(self) -> FrequencyAnalysisResult: ...
    def fit_pearson3(self) -> FrequencyAnalysisResult: ...
    def fit_weibull(self) -> FrequencyAnalysisResult: ...
    def empirical_frequency(self, method: str = "weibull") -> EmpiricalFrequency: ...
    def fit_all(self) -> dict[str, FrequencyAnalysisResult]:
        """Fit all distributions, rank by AIC, return results."""
```

#### Formulas (verified)

**Log-Normal:**
- Fit: `shape, loc, scale = scipy.stats.lognorm.fit(data, floc=0)`
- Quantile: `Q_T = lognorm.ppf(1 - 1/T, shape, loc=0, scale)`

**GEV (Generalized Extreme Value):**
- CDF: `G(x) = exp(−(1 + ξz)^(−1/ξ))` where `z = (x−μ)/σ`
- Quantile: `Q_T = μ + (σ/ξ) × ((−log(1−1/T))^(−ξ) − 1)` for ξ≠0
- Gumbel (ξ=0): `Q_T = μ − σ × log(−log(1−1/T))`
- SciPy convention: `c = −ξ` (opposite sign!)
- Fit: `shape, loc, scale = scipy.stats.genextreme.fit(data)`
- Quantile: `genextreme.ppf(1 - 1/T, shape, loc, scale)`
- Source: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html
- Source: https://blogs.sas.com/content/iml/2025/08/25/gev-sas.html

**Pearson Type III:**
- Fit: `skew, loc, scale = scipy.stats.pearson3.fit(data)`
- Quantile: `pearson3.ppf(1 - 1/T, skew, loc, scale)`
- Bulletin 17C (USGS) recommends Log-Pearson III with method of moments
- Source: https://pubs.usgs.gov/publication/tm4B5

**Weibull (3-parameter):**
- PDF: `f(x) = (ξ/σ) × ((x−μ)/σ)^(ξ−1) × exp(−((x−μ)/σ)^ξ)` for x > μ
- E(X) = μ + σ × Γ(1 + 1/ξ)
- Fit: `shape, loc, scale = scipy.stats.weibull_min.fit(data)`
- Quantile: `weibull_min.ppf(1 - 1/T, shape, loc, scale)`
- Required by KZGW (2017) methodology alongside Pearson III and Log-Normal
- Source: KZGW (2017), "Metodyka obliczania przepływów i opadów maksymalnych"

**Anderson-Darling goodness-of-fit test:**
- More sensitive than K-S in distribution tails — critical for extreme value analysis
- Implementation: `scipy.stats.anderson(data, dist_name)`
- Returns test statistic and critical values at [15%, 10%, 5%, 2.5%, 1%] significance levels
- Recommended by KZGW (2017) and PANDA (IMGW-PIB 2020)
- Source: Anderson & Darling (1954); KZGW (2017)

**Akaike Information Criterion (AIC):**
- Formula: `AIC = 2k − 2ln(L)` where k = number of parameters, L = maximum likelihood
- Used by `fit_all()` to rank competing distributions — lower AIC = better fit
- Source: Akaike (1974); referenced in PANDA (IMGW-PIB 2020)

**Plotting positions:**
- Weibull: `P_i = i / (n+1)` (default, recommended by Gumbel 1958)
- Hazen: `P_i = (i - 0.5) / n`
- Cunnane: `P_i = (i - 0.4) / (n + 0.2)`
- General: `P_i = (i - a) / (n + 1 - 2a)` (Bulletin 17C)

**Kolmogorov-Smirnov test:**
- Formula: `D = max|F_empirical(x) - F_theoretical(x)|`
- Implementation: `scipy.stats.kstest(data, distribution.cdf)`
- **CRITICAL LIMITATION:** When parameters are estimated from data, K-S critical values are invalid (p-values biased upward). The test becomes overly conservative.
- Source: https://www.itl.nist.gov/div898/handbook/eda/section3/eda35g.htm
- New code sets `ks_valid = False` and emits `UserWarning` when params estimated from data.

#### Bugs fixed from old code

| Bug | Old behavior | New behavior |
|-----|-------------|--------------|
| LogNormal fit input | `lognorm.fit(DataFrame)` | `lognorm.fit(ndarray)` |
| Hardcoded probabilities | Fixed list, not configurable | `return_periods` parameter |
| K-S validity | No warning about limitation | `ks_valid=False` + `UserWarning` |
| Code duplication | K-S test copy-pasted in 2 base classes | Single implementation |

### 3.4 `low_flows.py`

#### Data structures

```python
@dataclass
class LowFlowFrequencyResult:
    distribution_name: str            # "fisher_tippett"
    parameters: dict[str, float]
    return_periods: NDArray
    quantiles: NDArray
    non_exceedance_probabilities: NDArray  # 1/T
    ks_statistic: float
    ks_p_value: float
    ks_valid: bool

@dataclass
class LowFlowSequence:
    start_index: int
    end_index: int
    duration_days: int
    min_flow: float
    mean_flow: float
    deficit_volume: float             # sum of (threshold - Q) for Q < threshold

@dataclass
class LowFlowAnalysisResult:
    threshold: float
    sequences: list[LowFlowSequence]
    total_deficit: float
    max_duration_days: int
    n_events: int
```

#### Class

```python
class LowFlowAnalysis:
    def __init__(self, daily_flows: NDArray, dates: NDArray) -> None: ...
    def annual_minima(self) -> NDArray: ...
    def fit_fisher_tippett(self) -> LowFlowFrequencyResult: ...
    def empirical_frequency(self, method: str = "weibull") -> EmpiricalFrequency: ...
    def detect_sequences(
        self, threshold: float,
        min_duration_days: int = 5, max_gap_days: int = 4,
    ) -> LowFlowAnalysisResult: ...
```

#### Formulas (verified)

**Fisher-Tippett (GEV on minima):**
- Fit: `shape, loc, scale = scipy.stats.genextreme.fit(annual_minima)`
- Quantile: `Q_T = genextreme.ppf(p, shape, loc, scale)` — note: `p` directly (non-exceedance), NOT `1-p`

**Drought sequence detection:**
- Threshold level method (Yevjevich 1967)
- Sequences: Q < threshold for ≥ min_duration_days consecutive days
- Merging: sequences separated by < max_gap_days are merged
- Deficit volume: `V = Σ(threshold - Q_i)` for each day where `Q_i < threshold`
- Reference: Tallaksen & Van Lanen (2004), "Hydrological Drought"

#### Improvements over old code

| Issue | Old behavior | New behavior |
|-------|-------------|--------------|
| Sequence detection | `iterrows()` — extremely slow | Vectorized NumPy operations |
| Deficit volume | Not computed | Computed per sequence |
| Annual minima | Manual extraction from DataFrame | `annual_minima()` method using hydrological year |

---

## 4. Module: `hydrolog/hydrometrics/`

### 4.1 `rating_curve.py`

#### Data structures

```python
@dataclass
class RatingCurveResult:
    a: float                          # coefficient
    b: float                          # exponent
    h0: float                         # zero-flow stage
    r_squared: float
    std_residuals: float
    n_points: int
    n_outliers_removed: int

@dataclass
class WaterLevelZones:
    ntw_upper: float                  # upper boundary of low-water zone
    stw_upper: float                  # upper boundary of mean-water zone
    ntw_range: tuple[float, float]
    stw_range: tuple[float, float]
    wtw_range: tuple[float, float]
```

#### Classes

```python
@dataclass
class FrequencyDistributionResult:
    """Water level frequency and duration analysis result."""
    bin_edges: NDArray                # bin boundaries [cm or m]
    bin_centers: NDArray              # midpoints of bins
    counts: NDArray                   # observations per bin
    frequency_pct: NDArray            # percentage per bin
    cumulative_frequency_pct: NDArray # cumulative from lowest
    duration_pct: NDArray             # cumulative from highest (exceedance duration)

class RatingCurve:
    def __init__(self, water_levels: NDArray, discharges: NDArray) -> None: ...
    def fit(self, h0_initial: float = 0.0, remove_outliers: bool = False,
            outlier_std: float = 2.0) -> RatingCurveResult: ...
    def predict(self, water_levels: NDArray) -> NDArray: ...

class WaterLevelFrequency:
    def __init__(self, water_levels: NDArray, bin_width: float = 10.0) -> None: ...
    def frequency_distribution(self) -> FrequencyDistributionResult: ...
    def rybczynski_zones(self) -> WaterLevelZones: ...
```

#### Formulas (verified)

**Rating curve:**
- Formula: `Q = a × (H − H₀)^b`
- Fitting: `scipy.optimize.curve_fit` with 3 parameters (a, b, H₀)
- Outlier removal: `|residual| > k × std(residuals)`, configurable k (default 2.0)
- Source: Standard hydrological practice, e.g. WMO Guide to Hydrological Practices

**Rybczyński method:**
- NTW upper boundary: H at peak of frequency density curve
- STW/WTW boundary: graphical method on cumulative duration curve
- No hardcoded offsets
- Source: Polish hydrological practice (Rybczyński method for water level zone delimitation)

#### Bugs fixed from old code

| Bug | Old behavior | New behavior |
|-----|-------------|--------------|
| Formula convention | `H = a × Q^c` (inverted) | `Q = a × (H − H₀)^b` (standard) |
| Zero-flow stage | Not estimated | `H₀` as fitted parameter |
| Fit diagnostics | None returned | R², std of residuals |
| Bin width | Hardcoded 10 cm | Configurable parameter |
| Rybczyński offset | Hardcoded 10 cm, unexplained | Removed; computed from data |

---

## 5. Visualization: `hydrolog/visualization/statistics.py`

10 plotting functions following existing Hydrolog patterns:

| Function | Purpose | Old equivalent |
|----------|---------|---------------|
| `plot_frequency_curve()` | Exceedance probability curve | `ExceedanceAnalysis.plot()` |
| `plot_frequency_comparison()` | Compare multiple distributions | — (new) |
| `plot_non_exceedance_curve()` | Non-exceedance for low flows | `NonExceedanceAnalysis.plot()` |
| `plot_daily_characteristics()` | Max/Mean/Median/Min by day | `plt_daily_characteristics()` |
| `plot_monthly_statistics()` | Monthly stats with CI | `plt_confidence_interval()` |
| `plot_annual_hydrographs()` | Stacked annual Q(t) | `plt_daily_flows()` |
| `plot_flow_histogram()` | Histogram of values | `plt_histogram()` |
| `plot_low_flow_sequences()` | Drought sequences shaded | `plot_low_sequences()` |
| `plot_rating_curve()` | Q vs H with fitted curve | `plt_rating_curve()` |
| `plot_water_level_frequency()` | Frequency/duration + zones | `plt_water_level_frequency()` |

All functions follow existing Hydrolog visualization patterns:
- Accept optional `ax: Axes | None` parameter
- Accept optional `figsize: tuple = (10, 6)` parameter
- Accept optional `title: str | None = None` parameter
- Return `plt.Figure` (NOT `Axes` — consistent with all existing viz functions)
- Use `styles.py` colors and Polish labels
- Accept dataclass results (not raw data)

---

## 6. Testing

### 6.1 Test files

```
tests/unit/
├── test_characteristic.py           # ~30 tests
├── test_high_flows.py               # ~30 tests (+Weibull, Anderson-Darling, AIC)
├── test_low_flows.py                # ~20 tests
├── test_stationarity.py             # ~10 tests (Mann-Kendall)
├── test_rating_curve.py             # ~15 tests
└── test_visualization_statistics.py # ~15 tests (smoke tests)
```

### 6.2 Coverage target

> 80% for all new modules (consistent with project standard).

### 6.3 Key test scenarios

- Characteristic values: known dataset → verify all 12 values
- Hydrological year: dates spanning Nov–Oct → correct grouping
- Monthly stats: verify CV, skewness computed; CI uses t-Student (wider than z)
- Flood frequency: synthetic GEV data → fitted params match input
- Weibull fit: synthetic Weibull data → params recovered
- Anderson-Darling: verify statistic and critical values returned
- AIC: verify lower AIC for correct distribution on synthetic data
- K-S test: verify `ks_valid=False` warning emitted
- Mann-Kendall: series with known trend → trend_detected=True; random series → False
- Mann-Kendall: verify KZGW 30-year warning when n < 30
- Low-flow sequences: known pattern → correct detection and merging
- Rating curve: synthetic power-law data → params recovered ±1%
- Plotting: smoke tests (no crash, returns Figure)

---

## 7. Integration

### 7.1 No breaking changes

Existing modules, tests, and public API are unaffected.

### 7.2 Public exports

```python
# hydrolog/statistics/__init__.py
from hydrolog.statistics.characteristic import (
    CharacteristicValues, calculate_characteristic_values,
    DailyStatistics, MonthlyStatistics,
    calculate_daily_statistics, calculate_monthly_statistics,
)
from hydrolog.statistics.high_flows import (
    FloodFrequencyAnalysis, FrequencyAnalysisResult, EmpiricalFrequency,
)
from hydrolog.statistics.low_flows import (
    LowFlowAnalysis, LowFlowFrequencyResult,
    LowFlowSequence, LowFlowAnalysisResult,
)
from hydrolog.statistics.stationarity import (
    mann_kendall_test, MannKendallResult,
)

# hydrolog/hydrometrics/__init__.py
from hydrolog.hydrometrics.rating_curve import (
    RatingCurve, RatingCurveResult,
    WaterLevelFrequency, WaterLevelZones,
    FrequencyDistributionResult,
)
```

### 7.3 Shared types

`EmpiricalFrequency` is used by both `high_flows.py` and `low_flows.py`. It lives in a private shared module:

```python
# hydrolog/statistics/_types.py
@dataclass
class EmpiricalFrequency:
    values_sorted: NDArray[np.float64]
    exceedance_prob: NDArray[np.float64]
    return_periods: NDArray[np.float64]
```

Both `high_flows.py` and `low_flows.py` import from `_types.py`. The `__init__.py` re-exports it.

### 7.4 `__all__` lists

Both new `__init__.py` files must include `__all__` lists following the pattern in `hydrolog/runoff/__init__.py`:

```python
# hydrolog/statistics/__init__.py
__all__ = [
    "CharacteristicValues", "calculate_characteristic_values",
    "DailyStatistics", "MonthlyStatistics",
    "calculate_daily_statistics", "calculate_monthly_statistics",
    "FloodFrequencyAnalysis", "FrequencyAnalysisResult", "EmpiricalFrequency",
    "LowFlowAnalysis", "LowFlowFrequencyResult",
    "LowFlowSequence", "LowFlowAnalysisResult",
    "mann_kendall_test", "MannKendallResult",
]

# hydrolog/hydrometrics/__init__.py
__all__ = [
    "RatingCurve", "RatingCurveResult",
    "WaterLevelFrequency", "WaterLevelZones", "FrequencyDistributionResult",
]
```

### 7.5 Top-level `hydrolog/__init__.py`

No changes to top-level exports. Users import from submodules:
```python
from hydrolog.statistics import FloodFrequencyAnalysis
from hydrolog.hydrometrics import RatingCurve
```

### 7.6 Version

Target: v0.7.0

### 7.7 CLI and reports

**CLI commands:** Deferred to v0.7.1 or later. Statistics workflows are less suited to single CLI invocations (require multi-step data preparation). May add `hydrolog stats` subcommand later.

**Report sections:** Deferred to v0.7.1 or later. The existing `reports` module covers rainfall-runoff workflow. Statistics reports have a different structure (frequency curves, characteristic value tables) that warrants separate design.

### 7.8 Breaking change: SciPy promotion

SciPy moves from optional to required dependency. This is a **breaking change** for users who installed Hydrolog without SciPy and only used modules that don't need it (e.g., `time.concentration`, `morphometry`).

**Rationale:** Nash IUH already requires SciPy in practice. Statistics and hydrometrics modules are unusable without it. Formalizes the de facto requirement.

**Required doc updates:** `SCOPE.md` Section 6 (dependency table), `PRD.md` Section 3.4 (compatibility).

---

## 8. Error Handling

### 8.1 Input validation

All public functions and constructors validate inputs using `InvalidParameterError` from `hydrolog/exceptions.py`:

| Function/Class | Validation |
|---------------|------------|
| `calculate_characteristic_values()` | `len(daily_values) != len(dates)` → error; empty arrays → error |
| `FloodFrequencyAnalysis.__init__()` | `len(annual_maxima) < 5` → `UserWarning`; empty → error; NaN check |
| `LowFlowAnalysis.__init__()` | `len(daily_flows) != len(dates)` → error; empty → error |
| `LowFlowAnalysis.detect_sequences()` | `threshold <= 0` → error; `min_duration_days < 1` → error |
| `RatingCurve.__init__()` | `len(water_levels) != len(discharges)` → error; `< 3 points` → error |
| `WaterLevelFrequency.__init__()` | `bin_width <= 0` → error; empty → error |
| `calculate_monthly_statistics()` | `confidence_level` not in (0, 1) → error |

### 8.2 Warnings

Use `warnings.warn(..., UserWarning, stacklevel=2)` for:
- K-S test with estimated parameters (`ks_valid = False`)
- Sample size < 30 years: `UserWarning` noting KZGW (2017) requires 30+ years
- Sample size < 10 years: stronger `UserWarning` — results may be unreliable
- `curve_fit` convergence issues in `RatingCurve.fit()`
- Negative fitted parameters where physically impossible

---

## 9. Documentation Updates Required

The following project documents must be updated as part of v0.7.0:

| Document | Changes needed |
|----------|---------------|
| `docs/SCOPE.md` | Add statistics/hydrometrics to Section 2.1, module structure (3.1), roadmap (4), dependency table (6) |
| `docs/PRD.md` | Add user stories US-S01..S03, US-H01..H02; add v0.7.0 to roadmap |
| `docs/CHANGELOG.md` | v0.7.0 entry with all new classes/functions |
| `docs/PROGRESS.md` | New session, checkpoints for statistics/hydrometrics |
| `docs/IMPLEMENTATION_PROMPT.md` | Add statistics/hydrometrics to module structure |
| `pyproject.toml` | Move scipy to core dependencies |

---

## 10. NDArray Type Convention

All `NDArray` annotations use the parameterized form `NDArray[np.float64]` consistent with existing codebase (e.g., `scs_cn.py`, `unit_hydrograph.py`).

---

## 11. Literature References

| # | Reference | Used for |
|---|-----------|----------|
| 1 | USGS Bulletin 17C (2019). Guidelines for Determining Flood Flow Frequency. | LP-III, plotting positions |
| 2 | SciPy docs: `scipy.stats.genextreme` | GEV implementation, sign convention |
| 3 | SciPy docs: `scipy.stats.lognorm`, `scipy.stats.pearson3` | Distribution fitting |
| 4 | NIST Engineering Statistics Handbook, §1.3.5.16 | K-S test formula and limitations |
| 5 | Gumbel, E.J. (1958). Statistics of Extremes. | Weibull plotting position |
| 6 | Yevjevich, V. (1967). An objective approach to definitions and investigations of continental hydrologic droughts. | Threshold level method |
| 7 | Tallaksen, L.M. & Van Lanen, H.A.J. (2004). Hydrological Drought. | Low-flow analysis, deficit volume |
| 8 | IMGW-PIB. Rok hydrologiczny. | Hydrological year definition |
| 9 | Polish Wikipedia: Przepływ rzeki. | Characteristic values definitions |
| 10 | WMO Guide to Hydrological Practices. | Rating curve methodology |
| 11 | KZGW (2017). Metodyka obliczania przepływów i opadów maksymalnych. | Polish national standard: required distributions (Pearson III, Log-Normal, Weibull), 30-year minimum, stationarity requirement |
| 12 | PANDA — IMGW-PIB (2020). Metodyka Opracowania Polskiego Atlasu Natężeń Deszczów. | Polish precipitation frequency standard; Anderson-Darling, AIC |
| 13 | Mann, H.B. (1945). Non-parametric tests against trend. Econometrica 13. | Mann-Kendall test |
| 14 | Anderson, T.W. & Darling, D.A. (1954). A test of goodness of fit. JASA 49. | Anderson-Darling test |
| 15 | Akaike, H. (1974). A new look at the statistical model identification. IEEE Trans. | AIC |
| 16 | Rutkowska, A. & Młocek, W. (2024/25). Zastosowanie metod statystycznych w hydrologii i meteorologii. UR Kraków. | Textbook: formulas, KZGW/PANDA methodology overview |
