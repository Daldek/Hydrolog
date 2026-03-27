# Gap Analysis: PDF Textbook vs. Statistics & Hydrometrics Design Spec

**Date:** 2026-03-26
**PDF source:** "Zastosowanie metod statystycznych w hydrologii i meteorologii" (Application of Statistical Methods in Hydrology and Meteorology), Agnieszka Rutkowska & Wojciech Mlocek, Krakow 2024/25, Cracow University of Agriculture, Department of Applied Mathematics.
**Spec:** `docs/superpowers/specs/2026-03-26-statistics-hydrometrics-design.md`

---

## A. Topics Already in the Spec

### A1. Plotting Positions (Empirical Exceedance Probability)

**PDF (p.16):** Lists four formulas:
- Weibull (1939): `p_i = i / (n+1)`
- Cunnane (1978): `p_i = (i - 0.4) / (n + 0.2)`
- Hazen (1930): `p_i = (i - 0.5) / n`
- Gringorten (1963): `p_i = (i - 0.44) / (n + 0.12)`

**Spec (Section 3.3):** Lists Weibull, Hazen, Cunnane, and general formula `P_i = (i - a) / (n + 1 - 2a)` from Bulletin 17C.

**Assessment:** Well covered. The Gringorten formula is technically a special case of the general formula (a = 0.44), but could be worth listing explicitly since the PDF calls it out by name and it is used in Polish practice. Minor addition.

---

### A2. Flow Duration Curve (FDC)

**PDF (p.17):** Describes FDC as the relationship between exceedance probability and flow. Notes daily, monthly, or annual resolution. Recommends logarithmic scale.

**Spec (Section 4.1):** The `WaterLevelFrequency` class computes frequency/duration distributions with `duration_pct` (cumulative from highest = exceedance duration). The visualization function `plot_water_level_frequency()` plots this.

**Assessment:** Covered conceptually, but the spec's implementation is for water levels (H), not flows (Q). The FDC concept for flows is partially present via `EmpiricalFrequency` in `high_flows.py`, but a dedicated FDC function for daily flow series (not just annual maxima) is NOT explicitly in the spec. See B5 below.

---

### A3. Distributions: Log-Normal

**PDF (p.38):** 3-parameter log-normal: `X ~ LN(epsilon, mu, sigma)`. PDF formula with location parameter epsilon. `EX = epsilon + e^(mu + sigma^2/2)`. Examples: slope measurements, annual maximum flow, low-flow duration.

**Spec (Section 3.3):** `scipy.stats.lognorm.fit(data, floc=0)` — uses 2-parameter (location fixed at 0).

**Assessment:** The PDF presents a 3-parameter version with `epsilon` (threshold/location). The spec forces `floc=0` (2-parameter). This is a potential limitation; see C1.

---

### A4. Distributions: Pearson Type III (Gamma)

**PDF (p.37):** 3-parameter gamma (Pearson III): `X ~ P3(epsilon, alpha, beta)`, with `f(x) = (1/(beta^alpha * Gamma(alpha))) * (x - epsilon)^(alpha-1) * e^(-(x-epsilon)/beta)` for `x > epsilon`. `EX = epsilon + alpha*beta`, `D^2 X = alpha*beta^2`. Examples: annual precipitation sum, annual maximum flow.

**Spec (Section 3.3):** Uses `scipy.stats.pearson3.fit(data)`. Notes Bulletin 17C recommends Log-Pearson III with method of moments.

**Assessment:** Well covered. The PDF provides the explicit PDF formula which matches what SciPy implements.

---

### A5. Distributions: GEV (Generalized Extreme Value)

**PDF (p.40-41):** Full GEV definition with 3 cases:
- `xi = 0`: Gumbel (Fisher-Tippett Type I)
- `xi > 0`: Frechet (Fisher-Tippett Type II)
- `xi < 0`: Reversed Weibull (Fisher-Tippett Type III)

Provides explicit PDF, expected value formulas, and Euler constant gamma = 0.5772157.

**Spec (Section 3.3):** GEV with CDF, quantile formula, SciPy sign convention `c = -xi`. Gumbel quantile formula for xi=0.

**Assessment:** Well covered. The PDF confirms the spec's formulas. The spec correctly notes the SciPy sign convention issue.

---

### A6. Distributions: Gumbel

**PDF (p.43):** Gumbel as GEV with shape=0. Quantile formula: `x_p = mu - (1/alpha) * ln(-ln(p))`. Can be used for estimating probable flows or precipitation.

**Spec (Section 3.3):** Gumbel quantile: `Q_T = mu - sigma * log(-log(1-1/T))`.

**Assessment:** Covered. Same formula, different notation (PDF uses alpha = 1/sigma).

---

### A7. Distributions: Weibull

**PDF (p.39):** Full Weibull distribution with 3 parameters (location mu, scale sigma, shape xi). PDF formula, expected value, variance using Gamma function.

**Spec (Section 3.4):** Uses GEV on minima (Fisher-Tippett) for low flows, which can produce Weibull-type behavior. However, there is NO explicit Weibull distribution fitting in `high_flows.py`.

**Assessment:** Partially covered. See B1.

---

### A8. Kolmogorov-Smirnov Test

**PDF (p.65):** Lambda-Kolmogorov test with formula:
- `D_i = max(|i/(n+1) - p_teor|, |(i+1)/(n+1) - p_teor|)`
- `D_max = max(D_i), i = 1,...,n`
- `lambda_K = sqrt(n) * D_max`
- Critical values: lambda_0.01 = 1.628, lambda_0.05 = 1.354, lambda_0.1 = 1.224

**Spec (Section 3.3):** Uses `scipy.stats.kstest()`. Notes critical limitation when parameters estimated from data (`ks_valid=False`).

**Assessment:** Covered, but the spec does not mention the Lilliefors correction (for estimated parameters), which the PDF references on p.63. See C3.

---

### A9. Exceedance Probability / Return Period

**PDF (p.31):** Formal definition: `Q_max,p = F^{-1}(1-p)`, return period `T = 1/p`. Geometric interpretation with PDF area plots.

**Spec (Section 3.3):** `exceedance_probabilities = 1/T`, quantile computation via `distribution.ppf(1 - 1/T)`.

**Assessment:** Fully covered and consistent.

---

### A10. Confidence Intervals

**PDF (p.49-51):** CI for mean using t-Student distribution: `x_bar +/- t_alpha * s / sqrt(n)` with n-1 degrees of freedom. Also mentions CI for FDC for log-normal, Pearson III, and Weibull (from KZGW methodology).

**Spec (Section 3.2):** Uses `CI = mean +/- z * std / sqrt(n)` (normal/z-based).

**Assessment:** The spec uses z (normal) instead of t-Student. See C2.

---

### A11. Low-Flow / Drought Analysis

**PDF (p.45-46):** Types of drought (meteorological, soil moisture, hydrological, agricultural, economic). Low-flow identification using FDC threshold levels: Q70%, Q80%, Q90%, Q95%. Methods: POT (Peak Over Threshold), SEQ (Sequent Peak Algorithm). Duration, deficit volume, intensity.

**Spec (Section 3.4):** Threshold level method (Yevjevich 1967), sequence detection with configurable threshold, min_duration_days, max_gap_days, deficit volume computation.

**Assessment:** Well covered. The PDF confirms the spec's approach. The PDF adds the specific FDC percentile thresholds (Q70%, Q80%, Q90%, Q95%) as standard boundary levels, which could be added as convenience constants.

---

### A12. Pearson Correlation Coefficient

**PDF (p.70-72):** Population: `rho = Cov(X,Y) / (sigma_X * sigma_Y)`. Sample: `r = sum((x_i - x_bar)(y_i - y_bar)) / sqrt(sum((x_i - x_bar)^2) * sum((y_i - y_bar)^2))`.

**Spec:** Not explicitly in the spec's module structure. The rating curve fitting implicitly uses correlation (R-squared), but no standalone correlation function.

**Assessment:** Not directly relevant to the spec's core modules (frequency analysis, characteristic values), but see B7.

---

### A13. Polish Methodology Requirements (KZGW 2017)

**PDF (p.44):** For flood frequency analysis, KZGW (2017) requires:
- Minimum 30-year series
- Homogeneous (stationary) data
- Distributions: Pearson 3, Log-Normal, Weibull
- Previous version also included GEV

**Spec:** Has LogNormal, GEV, Pearson III but NOT Weibull for high flows.

**Assessment:** The spec is missing Weibull for high flows (KZGW requirement). See B1.

---

## B. Topics NOT in the Spec that SHOULD Be Added

### B1. Weibull Distribution for High Flows (CRITICAL)

**What:** The Weibull distribution (`Weibull(mu, sigma, xi)`) is explicitly required by KZGW (2017) methodology for flood frequency analysis, alongside Pearson III and Log-Normal.

**PDF formulas (p.39):**
```
f(x) = (xi/sigma) * ((x-mu)/sigma)^(xi-1) * e^(-((x-mu)/sigma)^xi)   for x > mu
E(X) = mu + sigma * Gamma(1 + 1/xi)
D^2(X) = sigma^2 * [Gamma(1 + 2/xi) - Gamma^2(1 + 1/xi)]
```

**Where in spec:** Add `fit_weibull()` method to `FloodFrequencyAnalysis` class in `high_flows.py`. Use `scipy.stats.weibull_min.fit(data)`.

**Importance:** CRITICAL - Required by Polish national methodology (KZGW 2017).

---

### B2. Mann-Kendall Trend Test (CRITICAL)

**What:** Non-parametric test for detecting trends (non-stationarity) in time series. Essential for validating the stationarity assumption before frequency analysis. KZGW (2017) requires homogeneous (stationary) data.

**PDF formulas (p.59-60):**
```
S = sum_{i=1}^{n-1} sum_{j=i+1}^{n} sgn(x_j - x_i)
Var(S) = n(n-1)(2n+5) / 18
U = (S-1)/sqrt(Var S)  if S > 0
U = 0                  if S = 0
U = (S+1)/sqrt(Var S)  if S < 0
```
U ~ N(0,1). Reject H0 (no trend) if |U| > z_alpha.

**Purpose in hydrology (p.60):** Tests whether a flow/precipitation series is homogeneous (stationary). If H0 rejected, the series contains a trend and frequency analysis results may be unreliable.

**Where in spec:** New file `hydrolog/statistics/stationarity.py` or add to `characteristic.py`. Function: `mann_kendall_test(series: NDArray) -> MannKendallResult` returning S, Var(S), U, p_value, trend_detected.

**Importance:** CRITICAL - Required as a prerequisite check before frequency analysis per KZGW methodology. Without it, users cannot validate the stationarity assumption.

---

### B3. Anderson-Darling Goodness-of-Fit Test (HIGH)

**What:** Goodness-of-fit test that gives more weight to distribution tails than K-S test. Used in KZGW methodology and PANDA (IMGW-PIB 2020).

**PDF (p.63):** Listed as one of 5 popular goodness-of-fit tests. Explicitly mentioned as used in both KZGW and PANDA methodologies.

**Where in spec:** Add to `FrequencyAnalysisResult` dataclass (alongside existing K-S fields) or provide as separate utility. Use `scipy.stats.anderson()` or `scipy.stats.anderson_ksamp()`.

**Importance:** HIGH - Specifically recommended by KZGW and PANDA. More appropriate than K-S for extreme value distributions because it is more sensitive in the tails.

---

### B4. Chi-Squared (Pearson) Goodness-of-Fit Test (MEDIUM)

**What:** Classical goodness-of-fit test based on binned data.

**PDF formula (p.64):**
```
chi^2 = sum_{i=1}^{k} (n_i - n*p_i)^2 / (n*p_i)
```
Degrees of freedom: k - p - 1 (k = number of classes, p = number of estimated parameters). Each class must have at least 5 observations.

**Where in spec:** Add as an alternative goodness-of-fit test in `high_flows.py` and `low_flows.py`. Use `scipy.stats.chisquare()`.

**Importance:** MEDIUM - Mentioned in KZGW. Less powerful than Anderson-Darling for continuous data, but useful for binned data (histograms) and widely understood.

---

### B5. Flow Duration Curve (FDC) as Standalone Function (MEDIUM)

**What:** A dedicated FDC function for daily flow series (not just annual maxima). The FDC is a fundamental tool in hydrology showing the percentage of time a given flow is equaled or exceeded.

**PDF (p.17, p.46, p.51):** FDC used extensively: for visualizing flow regimes, setting low-flow thresholds (Q70%, Q80%, Q90%, Q95%), and computing CI for exceedance curves.

**Where in spec:** Could be added to `characteristic.py` or as a new utility. Function: `flow_duration_curve(daily_flows: NDArray) -> FlowDurationResult` with fields: sorted_flows, exceedance_pct, and methods to extract Qp% values.

**Importance:** MEDIUM - The concept is partially covered (EmpiricalFrequency, WaterLevelFrequency), but a dedicated FDC for daily flows would be a natural complement. Standard low-flow thresholds (Q70%, Q80%, Q90%, Q95%) should be extractable.

---

### B6. Akaike Information Criterion (AIC) for Distribution Selection (MEDIUM)

**What:** When multiple distributions pass goodness-of-fit tests, AIC provides an objective criterion for selecting the best-fitting distribution.

**PDF (p.66):** "If it is necessary to choose one theoretical distribution, one can apply a selection criterion, for example the Akaike criterion (cf. PANDA, p.28)."

**Formula:** `AIC = 2k - 2ln(L)` where k = number of parameters, L = maximum likelihood.

**Where in spec:** Add to `FloodFrequencyAnalysis.fit_all()` method. After fitting all distributions, compute AIC for each and rank. Add `aic` field to `FrequencyAnalysisResult`.

**Importance:** MEDIUM - Useful for automated best-fit selection, referenced in PANDA methodology.

---

### B7. Spearman Rank Correlation Coefficient (LOW-MEDIUM)

**What:** Non-parametric correlation coefficient based on ranks. More robust than Pearson for non-linear monotonic relationships.

**PDF (p.2, course plan topic 7):** Listed in the course outline alongside Pearson correlation and linear regression, but the formula was not included in the PDF pages (possibly covered in exercises).

**Where in spec:** If a correlation/regression utility module is added, include both Pearson and Spearman. Use `scipy.stats.spearmanr()`.

**Importance:** LOW-MEDIUM - Not directly part of frequency analysis, but useful for exploratory analysis of hydrological variables (e.g., flow vs. catchment area).

---

### B8. L-Moments for Parameter Estimation (NICE-TO-HAVE)

**What:** Alternative parameter estimation method using linear combinations of order statistics (L-moments). More robust than conventional moments for small samples.

**PDF (p.62):** Listed as method #3 for parameter estimation: "method of linear moments: comparing linear moments of the sample to corresponding linear moments of the theoretical distribution (linear moments: L-moments)."

**Where in spec:** The spec uses SciPy's `.fit()` which uses MLE. L-moments could be offered as an alternative estimation method, particularly for GEV (recommended by Hosking 1990). Would require `lmoments3` package or custom implementation.

**Importance:** NICE-TO-HAVE for v0.7.0 (could be deferred to v0.7.1). Commonly used in flood frequency analysis internationally. Hosking & Wallis (1997) "Regional Frequency Analysis" is a key reference.

---

### B9. Generalized Pareto Distribution (NICE-TO-HAVE)

**What:** Used for Peak Over Threshold (POT) analysis - modeling exceedances above a high threshold.

**PDF (p.42):** "Occurs in the analysis of values above a certain threshold, e.g. flow above a certain value (estimation of flood flows), precipitation above a certain level (e.g. flash flood), property prices above a certain threshold."

**Where in spec:** Would be relevant for POT-based flood frequency analysis as an alternative to the annual maxima approach. Use `scipy.stats.genpareto`.

**Importance:** NICE-TO-HAVE - POT analysis is an advanced alternative to annual maxima. Could be added in a later version.

---

### B10. Gringorten Plotting Position (LOW)

**What:** Specific plotting position formula `p_i = (i - 0.44) / (n + 0.12)` (Gringorten 1963).

**PDF (p.16):** Listed explicitly alongside Weibull, Cunnane, and Hazen.

**Where in spec:** Already representable via the general formula `P_i = (i - a) / (n + 1 - 2a)` with a=0.44. Could be added as a named option in the `method` parameter of `empirical_frequency()`.

**Importance:** LOW - Already possible through the general formula, but explicit naming would be convenient.

---

## C. Corrections or Improvements to the Spec

### C1. Log-Normal: Consider 3-Parameter Version

**Current spec:** Forces `floc=0` (2-parameter log-normal).

**PDF (p.38):** Presents 3-parameter version with location parameter epsilon: `X ~ LN(epsilon, mu, sigma)`.

**Recommendation:** Allow optional 3-parameter fitting: `lognorm.fit(data)` without `floc=0`. The 2-parameter version should remain the default, but provide a `three_param: bool = False` option. The KZGW methodology does not specify 2 vs 3 parameters, so supporting both is appropriate.

**Impact:** Low risk. The 3-parameter fit may not converge for some datasets, so the 2-parameter default is safer.

---

### C2. Confidence Intervals: Use t-Student Instead of z (Normal)

**Current spec (Section 3.2):** `CI = mean +/- z * std / sqrt(n)` where `z = scipy.stats.norm.ppf(1 - alpha/2)`.

**PDF (p.49):** Uses t-Student distribution: `CI = x_bar +/- t_alpha * s / sqrt(n)` where `t_alpha` is from t-distribution with n-1 degrees of freedom.

**Recommendation:** Replace `norm.ppf` with `scipy.stats.t.ppf(1 - alpha/2, df=n-1)`. The z-approximation is only valid for large samples (n > 30). For typical hydrological records (20-50 years), the t-Student gives wider (more correct) intervals. This is a clear improvement.

**Formula change:**
```python
# Current (spec):
z = scipy.stats.norm.ppf(1 - alpha / 2)
ci = mean +/- z * std / sqrt(n)

# Corrected (from PDF):
t = scipy.stats.t.ppf(1 - alpha / 2, df=n - 1)
ci = mean +/- t * std / sqrt(n)
```

**Impact:** Important correction. For n=20 at 95% confidence, t=2.093 vs z=1.960 (a 7% difference in interval width).

---

### C3. K-S Test: Mention Lilliefors Correction

**Current spec (Section 3.3):** Notes K-S is invalid when parameters estimated from data. Sets `ks_valid=False`.

**PDF (p.63):** Mentions "lambda-Kolmogorov (possibly with Lilliefors correction)" as one of the popular tests.

**Recommendation:** Add a note in the spec about the Lilliefors correction as a known alternative that adjusts K-S critical values for estimated parameters. `scipy.stats.kstest` does not implement Lilliefors, but `statsmodels.stats.diagnostic.lilliefors()` does. Since Hydrolog avoids statsmodels dependency, this should remain a documentation note rather than implementation, but the Anderson-Darling test (B3) is a better solution.

---

### C4. Minimum Sample Size Requirement from KZGW

**Current spec (Section 8.2):** Warns if sample size < 10 years.

**PDF (p.44):** KZGW (2017) requires minimum 30-year series.

**Recommendation:** Add a stronger warning (or configurable threshold) for `len(annual_maxima) < 30`, referencing KZGW 2017. The current 10-year warning is too lenient for Polish methodology compliance. Suggested approach:
- `< 10`: `UserWarning` (current, keep)
- `< 30`: `UserWarning` noting KZGW requires 30+ years
- `>= 30`: no warning

---

### C5. Descriptive Statistics: Add Coefficient of Variation, Skewness, Kurtosis

**Current spec (Section 3.2):** `MonthlyStatistics` includes mean, median, max, min, std, CI. No skewness, kurtosis, or CV.

**PDF (p.14-15, 28-30):** Defines:
- Coefficient of variation: `VX = DX / EX` (p.28)
- Skewness: `gamma = M3X / (DX)^3` (p.29)
- Kurtosis: `KX = M4X / (DX)^4 - 3` (p.30)

**Recommendation:** Add `cv_values`, `skewness_values`, and optionally `kurtosis_values` to `MonthlyStatistics` or provide a separate `descriptive_statistics()` function. These are standard measures used to characterize hydrological variables and select appropriate distributions (e.g., high skewness suggests log-normal or Pearson III).

---

### C6. PANDA Methodology: Additional Distributions for Precipitation

**Current spec:** Focuses on flow distributions (LogNormal, GEV, Pearson III).

**PDF (p.44):** PANDA (IMGW-PIB 2020) for precipitation analysis lists: log-normal, gamma, exponential, Gumbel, Frechet, GEV, Pareto, Weibull for rainfall intensity at durations from 5 min to 4320 min (3 days).

**Recommendation:** If precipitation frequency analysis is in scope for future versions, the distribution set should match PANDA. For v0.7.0, at minimum add a note in the spec that the precipitation use case may need additional distributions.

---

## D. Topics in the PDF that are OUT OF SCOPE

### D1. Discrete Distributions (Bernoulli, Poisson)
**PDF (p.34):** Bernoulli and Poisson distributions for counting events (rainy days, threshold exceedances). Not relevant to Hydrolog's continuous flow/precipitation frequency analysis.

### D2. Uniform and Exponential Distributions
**PDF (p.35):** Mathematical definitions. Not used in Hydrolog's frequency analysis context.

### D3. Cauchy Distribution
**PDF (p.42):** Theoretical distribution with heavy tails. Not used in hydrological practice.

### D4. General Probability Theory Foundations
**PDF (p.5-14, 18-30):** Definitions of random variables, CDF, PDF, expected value, variance, moments, quantiles. These are mathematical background, not implementable features.

### D5. Parametric Tests for Means, Variances, Proportions
**PDF (p.55-58):** t-test for mean, ANOVA, variance tests, proportion tests. These are general statistical tests, not specific to hydrological frequency analysis.

### D6. Bivariate Random Variables (General Theory)
**PDF (p.67-68):** Joint CDF, joint PDF theory. Foundational material, not directly implementable.

### D7. Meteorological-Specific Examples
**PDF:** Some examples deal with temperature, insolation, and other meteorological variables. Hydrolog's statistics module is focused on flow and precipitation.

### D8. Shapiro-Wilk Test
**PDF (p.63):** Listed for testing normality specifically. Less relevant for hydrological data which is typically non-normal (skewed). Out of scope for v0.7.0.

### D9. Cramer-von Mises Test
**PDF (p.63):** Another goodness-of-fit test. Lower priority than Anderson-Darling. Could be a future addition but out of scope for v0.7.0.

---

## Summary Priority Matrix

| Priority | Item | Description | Spec Location |
|----------|------|-------------|---------------|
| **CRITICAL** | B1 | Weibull distribution for high flows | `high_flows.py` |
| **CRITICAL** | B2 | Mann-Kendall trend test | New file or `characteristic.py` |
| **CRITICAL** | C2 | t-Student CI instead of z-based CI | `characteristic.py` |
| **HIGH** | B3 | Anderson-Darling GoF test | `high_flows.py`, `low_flows.py` |
| **HIGH** | C4 | KZGW 30-year minimum warning | `high_flows.py` |
| **MEDIUM** | B4 | Chi-squared GoF test | `high_flows.py`, `low_flows.py` |
| **MEDIUM** | B5 | Standalone FDC function | `characteristic.py` |
| **MEDIUM** | B6 | AIC for distribution selection | `high_flows.py` |
| **MEDIUM** | C1 | 3-parameter Log-Normal option | `high_flows.py` |
| **MEDIUM** | C5 | CV, skewness, kurtosis stats | `characteristic.py` |
| **LOW-MED** | B7 | Spearman correlation | Future utility module |
| **LOW** | B8 | L-moments estimation | Future enhancement |
| **LOW** | B9 | Generalized Pareto (POT) | Future enhancement |
| **LOW** | B10 | Gringorten plotting position | `high_flows.py` |
| **NOTE** | C3 | Lilliefors correction documentation | Spec documentation |
| **NOTE** | C6 | PANDA precipitation distributions | Future scope note |

---

## Key Literature Referenced in PDF (Not in Spec)

| # | Reference | Relevance |
|---|-----------|-----------|
| 1 | KZGW (2017) "Metodyka obliczania przeplywow i opadow maksymalnych" (Methodology for computing maximum flows and precipitation) | Primary Polish national standard for flood frequency. Mandates specific distributions and tests. |
| 2 | PANDA - IMGW-PIB (2020) "Metodyce Opracowania Polskiego Atlasu Natezen Deszczow" (Methodology for Polish Rainfall Intensity Atlas) | Polish standard for precipitation frequency analysis. |
| 3 | Weglarczyk, S. (2010) "Statystyka w inzynierii srodowiska" (Statistics in Environmental Engineering), Cracow University of Technology | Polish textbook on environmental statistics |
| 4 | Byczkowski, A. (1999) "Hydrologia", SGGW Warsaw | Polish hydrology textbook |
| 5 | Ozga-Zielinska, M. & Brzezinski, J. (1997) "Hydrologia stosowana" (Applied Hydrology), PWN Warsaw | Polish applied hydrology reference |

These references, especially KZGW (2017) and PANDA (2020), should be added to the spec's Section 11 (Literature References).
