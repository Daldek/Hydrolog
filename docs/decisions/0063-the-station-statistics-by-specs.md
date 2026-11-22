# 0063. The station statistics by specs: the tiers, one sample per spec, the defects of the audit

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs), Nogat's computation standard
  (CMP-1.1 tiers, CMP-1.2 delegated computations, CMP-2.2 Tier B tables, CMP-3.1 to CMP-3.5, CMP-5.1, CMP-6) and the
  literature research of the formulas of 2026-11-18 (trend and regime; flood frequency, sections on the duration curve,
  the threshold level method, the baseflow and the volumes; observation conventions; TRIAGE T21, T22, T30)
- Amends: [ADR-0022](0022-homogeneity-tests.md) (Pettitt's test and the exact K-S p are specs),
  [ADR-0031](0031-regime-seasonality-harmonics-sens-slope-and-baseflow.md) (the shares of the harmonics, the coverage of
  a year, the baseflow index of a year without flow, Sen's bound), [ADR-0041](0041-implausible-rating-curves-flagged-not-refused.md)
  (the plausibility rule is a declared, unreferenced classification), [ADR-0049](0049-exact-small-sample-p-values-and-intervals-of-independent-values.md)
  (its exact p-values and the interval of a monthly mean are computed by specs)

## Context

The station statistics are the analyses that Obserwator stores for every gauge (`mann_kendall.*`, `homogeneity.Q`,
`duration_curve.*`, `baseflow.Q`, `regime.Q`, `seasonality.*`, `harmonics.*`, `characteristic.*`,
`low_flow_sequences.*`, `threshold_events.*`, `runoff_volume.Q`, `rating_curve*`, `water_level_zones.H`): tests,
estimators, indices, classifications and a model fit, and, around them, calendars, counts of days and sums by
definition. They are the third family to get specs (plan of the computation standard, step 5). Their functions took
whole daily series with dates and mixed the formula with the calendar, checked their inputs by hand, and several
returned what the standard forbids: a baseflow index NaN for a year without flow, shares of variance of −0.63 and 1.47
from the harmonics of a summer, an infinite interval at the largest level below 1, a p-value of 0, catalog ranges that
offered 1 or 100 where the commands refuse them.

## Decision

1. **The tiers (CMP-1.1).** Tier A, by `FormulaSpec`, `formula_version` 1: the Mann-Kendall test (`mann_kendall`), Sen's
   slope and Conover's intercept (`sen_slope`), Gilbert's interval (`sen_interval`), Pettitt's test (`pettitt`), the
   exact K-S p with ties (`ks_exact`), the values of the duration curve (`exceedance_values`), the Lyne and Hollick
   filter (`lyne_hollick`), the baseflow index (`baseflow_index`), the recession constant (`recession_constant`),
   Pardé's coefficients (`parde_coefficients`), the spring share (`spring_share`), Dynowska's type
   (`dynowska_regime_type`), the circular mean (`circular_mean`), the harmonics of the annual cycle (`harmonic_fit`),
   the standard deviation, the coefficient of variation, the skewness g1 and the half-width of the interval of a mean
   (`sample_standard_deviation`, `coefficient_of_variation`, `fisher_pearson_skewness`, `mean_interval_half_width`), the
   rating equation, its fit, its plausibility and Rybczyński's zones (`rating_curve`, `rating_curve_fit`,
   `rating_curve_plausibility`, `rybczynski_zones`). Tier B, by `TIER_B` of each module: the hydrological year and its
   days, half-years and complete years; the characteristic values of the first and second degree from a daily series
   and from IMGW-PIB's half-year values; the daily and monthly statistics as aggregations; the duration classes and the
   days of the duration curve; the runs of the threshold level method, the threshold events, the low-flow sequences of
   `LowFlowAnalysis.detect_sequences` and their deficit volumes; the runoff volumes; the spans and years of the
   baseflow; the regime, the dates of extremes and the yearly fits of a daily series; the histogram of water levels,
   the start of the rating fit and its outlier screening. Delegated (CMP-1.2): SciPy's `lfilter`, `t.isf`,
   `mannwhitneyu`, `ks_2samp` and `curve_fit`, NumPy's `lstsq`, each with a smoke case and its test.
2. **One sample per spec, the series around it.** A spec's function takes the sample of its formula (`values` with
   the unit of the documents and declared scalings, the formulas being homogeneous; times as numbers, levels and
   discharges, a histogram), never a calendar: the public functions and the commands keep their signatures, lay the
   series on the calendar (Tier B) and compute through the specs, so every result records the `formula_version` of
   each formula it used. New public functions: `mann_kendall`, `sen_line`, `sen_interval`, `pettitt`, `ks_exact`,
   `baseflow_index`, `recession_ratio`, `parde_coefficients`, `spring_share`, `circular_mean`,
   `sample_standard_deviation`, `coefficient_of_variation`, `fisher_pearson_skewness`, `mean_interval_half_width`,
   `rating_discharge`, `fit_rating_curve`, `rating_curve_plausibility`, `rybczynski_zones`. `exceedance_values` takes
   `exceedance_percent` (was `percents`) and `lyne_hollick_filter` `values` (was `discharge`). Classes no longer check
   in their constructors (`RatingCurve`); their methods refuse through the specs.
3. **Evidence.** A published case is a reference case; an R run, an analytic signal or a re-implementation is an
   oracle (CMP-1.7), so the rating fit, whose only numbers are R's `nls`, is `oracle only`. The R outputs of the
   research are copied byte for byte into `tests/oracles/` (`trend_regime`, `baseflow`, `rating_curve`) with a copy in
   the reader's commented-header format beside them, never regenerated; IMGW-PIB's files are kept with their
   attribution (`tests/oracles/characteristic`, `tests/fixtures/imgw_klodzko`). Hydrolog's own rules without a source
   are said so: the recession constant and the spring share are `oracle only`, the plausibility rule and Rybczyński's
   zones `unreferenced`, with the notice `unreferenced_formula` ([ADR-0064](0064-notices-of-applicability-constraints-and-unreferenced-formulas.md)).
4. **Conventions stated where sources differ** (each spec lists its own): Mann-Kendall's continuity correction and the
   exact p below 10 values; Gilbert's interval interpolated between ranks (R's `trend` rounds them); Pettitt's first
   change point; the K-S p exact with ties for m·n < 10,000 (R's bound); the duration curve on Weibull positions with
   the end values held (R type 6, not Searcy's i/N); a day below the threshold is Q < T, two runs are pooled when fewer
   than `max_gap_days` days part them and the pooled duration includes those days; Ladson et al.'s (2013) standard
   approach of the filter with the quickflow unclipped; BFI = Σb/ΣQ; the skewness of the monthly statistics is the
   biased g1 (NIST 1.3.5.11) while the frequency analyses keep the adjusted G1; the coefficient of variation only of
   a quantity with a true zero; Pardé's annual mean weighted by days, as IMGW-PIB's; Dynowska's limits 130/180/100 %
   of Wrzesiński (2017, 2018) and Perz (2019) with Hydrolog's reading (spring max(III, IV), summer max(VI–VIII), 0.95,
   the order 5 → 4 → 1–3); the circular mean with Bayliss and Jones's half-day offset and 365.25 days; the rating curve
   homogeneous in the unit of H.
5. **The defects of the audit, fixed.** A baseflow index of a year without flow is `null` and a period without flow is
   refused (it was NaN, CMP-3.4); the shares of the harmonics come from nested fits on the deviations from the mean,
   and a year whose gaps leave the cycle undetermined (Feichtinger, Gröchenig and Strohmer 1995) or a constant series
   is refused, the years left out named by the notice `years_without_fit`; the interval of a monthly mean takes the
   tail by `t.isf` (no infinite limit), is not clipped at 0 (stages below the gauge zero) and the coefficient of
   variation is `null` where the mean is 0 or values are negative; a p-value never underflows to 0; the catalog
   declares `alpha` of `stats mann-kendall`, `stats homogeneity` and `stats baseflow` and the exceedance percentages
   as open intervals; library functions refuse negative or infinite discharges, unordered dates, `var_s` below 0 and
   `alpha` outside (0, 1); the rating fit searches on pairs normalised by powers of two, so it does not depend on the
   unit of H, and a search without a minimum is the precondition `least_squares_minimum` (`validation_error`) instead
   of `calculation_error`.
6. **Sen's slope takes at most 5,000 values.** It holds the slope of every pair (8 bytes each now, 100 MB at 5,000
   values; a daily series of a century needed about 27 GB); the test assumes independent values, so a daily series is
   aggregated first. The Mann-Kendall statistic alone is not capped.

## Consequences

- Breaking (CHANGELOG): new refusals with the standard's `details.reason`, the `null` CV and baseflow index, the
  unclipped interval, the harmonics' shares and coverage, the rating fit's error code and its numbers within 4·10⁻⁶,
  the two renamed parameters, the cap of Sen's slope, the duration curve within 2·10⁻¹⁵ of the range.
- Obserwator's stored analyses carry `formula_versions`; `harmonics.*` of years with gaps or several harmonics and
  `rating_curve*` are recomputed; its texts need `unreferenced_formula` and `years_without_fit`. The other stored values
  do not change.
- Open: whether the runs of the threshold level method are Tier B (here: nothing is estimated) or Tier A like the
  ETCCDI spells of the meteorological statistics (ADR-0059); the recession constant of WMO-No. 1029; the sources of
  Rybczyński, Byczkowski (second-degree medians) and Dynowska (1997), which the author provides (plan, step 9).

## Alternatives considered

- **Specs on the functions of whole daily series:** a spec cannot type dates, and the calendar would be checked as
  part of every formula; the series stay Tier B around one-sample formulas.
- **R's results as reference cases:** they are an implementation, not a source; the statuses would claim more than
  the evidence.
- **A precondition of n on Sen's slope instead of a cap and a smaller array:** the memory of the pairs, not the size
  of the sample, was the defect; both are needed.
- **Refusing a constant series in the Mann-Kendall test** (CMP-1.6's example): Gilbert's eq. 16.4 gives Z = 0 for
  S = 0, and Obserwator's yearly counts of days may all be 0; it gives p = 1.
