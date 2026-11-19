# 0055. The frequency estimators refuse by preconditions and search within bounds

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs) and Nogat's computation
  standard (CMP-3.2, CMP-3.4, CMP-6.6, CMP-9.1); the literature research of the flood frequency formulas of 2026-11-18
- Amends: [ADR-0021](0021-fit-methods-of-flood-frequency.md) (what a fit method refuses, how maximum likelihood and
  least squares search, the AIC of a fit outside its support) and
  [ADR-0048](0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md) (A² as a formula with a spec; its
  critical values unchanged)

## Context

The estimators of the flood frequency analysis (L-moments, moments, maximum likelihood and least squares, each for the
log-normal of location 0, the GEV, Pearson III and Weibull), the Fisher-Tippett distribution of the annual minima, the
plotting positions and the goodness of fit (A², AIC) get specs (`hydrolog.statistics.frequency`, `low_flows`,
`_types`). Up to 0.9.0 each fit checked its sample by hand and raised `calculation_error` with reasons of its own
(`too_few_values`, `constant_values`, `out_of_range`, `non_positive_values`, `unbounded_likelihood`, `not_converged`);
maximum likelihood checked nothing (four equal maxima gave a GEV ranked best with AIC −428, a Weibull Q1% of 7·10³⁰
m³/s), and on degenerate samples its search ran 21 × 20,000 evaluations, 60–100 s, before it failed. Least squares
ran Nelder-Mead once with SciPy's default tolerances, 10⁻⁴ absolute in the unit of the sample: it stopped before the
minimum, and the result depended on the unit (the Weibull of the Polana maxima, KZGW 2017 example 3.2: a sum of
squares of 515.9 instead of 429.3, Q1% −4.7 %, Q0.1% −8.2 %; a gross defect, CMP-9.1(1)).

The standard refuses a failed precondition with `validation_error`, `details.reason` `precondition_failed`, before
any computation (CMP-3.2); a formula never returns a value that is not finite (CMP-3.4); an iteration has a bounded
count, and the failure it may end in is named by a precondition where one can foresee it (CMP-6.6). Whether a
likelihood has a maximum, or a sum of squares a minimum, is known only by searching for it.

## Decision

1. **A sample the method cannot fit fails a precondition of its spec.** `enough_values` (3; maximum likelihood one
   value more than the parameters, 4 for the minima), `values_not_all_equal`, `positive_values` (the log-normal of
   location 0), `l_moments_within_distribution`, `skewness_within_distribution`, `likelihood_has_a_maximum` and
   `squares_have_a_minimum`. One fit asked for (`FloodFrequencyAnalysis.fit_*`, `fit_all` of one combination, `stats
   flood-frequency`, the Fisher-Tippett fit of `stats low-flow`) is refused with `validation_error`,
   `precondition_failed` and `details.constraint`, with `details.distribution` and `details.fit_method`.
2. **The notice of a combination left out keeps its reasons.** Of several combinations, the one whose method cannot
   fit is left out with `distribution_left_out` and the reason of 0.9.0 that its failed precondition maps to
   (`too_few_values`, `constant_values`, `non_positive_values`, `out_of_range`, `unbounded_likelihood`,
   `not_converged`), so a consumer that reads the notice sees no change; `fit_all` with nothing left still fails
   with `calculation_error` and `details.reasons`.
3. **A search is a precondition, run once.** `likelihood_has_a_maximum` and `squares_have_a_minimum` run the search,
   and the fit takes its end: one search per distribution and sample, cached by the sample's bytes (`lru_cache` of
   64). A search that does not settle within its bounded count of runs fails the precondition; `calculation_error`
   (`not_converged`) is left for a result that the preconditions should have prevented, a defect of the spec
   (CMP-3.4).
4. **The shapes searched are bounded.** Maximum likelihood searches the GEV with −1 < c < 1 (scipy's c: from c = 1
   on the density is infinite at the upper bound, where the likelihood has no maximum, Smith 1985; at c ≤ −1 the GEV
   has no mean), Pearson III with |G| < 2 and Weibull with 1 < k < 50 (beyond 50 Weibull is the reversed Gumbel within
   a few per cent); a search that ends within 10⁻³ of one of these ends, or at a scale below 10⁻⁶ standard deviations,
   finds no maximum. Least squares searches the log-normal with s < 5, the GEV with −1 < c < 50, Pearson III with
   |G| < 9 and Weibull with k < 50, the test bounds of the quantile functions; an end at one of them is no minimum.
5. **A GEV with more than half the sample tied at its smallest value has no maximum.** With k values tied at the
   smallest and m others, the log-likelihood grows as (k − m/ξ) ln(1/σ) as the scale σ falls to 0, without limit for
   k > m over the shapes searched; such a sample fails `likelihood_has_a_maximum` before the search.
6. **Least squares reaches the least squares.** The search runs on the standardised sample, (x/2ᵉ − mean)/sd, with
   the tolerances 10⁻¹⁰ and 10⁻¹² of Nelder-Mead, a first simplex that moves each coordinate by at least 0.05, and
   restarts from its end until a run gains at most 10⁻⁹, at most 21 runs. The fix of the gross defect changes the
   least-squares quantiles (the Polana Weibull Q1% +4.9 %, Q0.1% +9.0 %; the other distributions by about 10⁻⁵); its
   release waits for the author's decision (CMP-9.2).
7. **The goodness of fit by specs.** A² (`anderson_darling`) and the AIC (`akaike_information_criterion`) are
   formulas with specs; the critical values of A² stay those of the parametric bootstrap of ADR-0048. A fit that
   leaves an annual maximum without a finite density fails the AIC's precondition `values_within_support`: it keeps
   an infinite AIC (`null`), given without the formula, with the notice `outside_support`, and ranks last. SciPy's
   `kstest` and the `cdf`, `pdf` and `logpdf` of the four distributions are delegated computations (CMP-1.2), each
   with a smoke case and its test in `docs/FORMULAS.md`.

## Consequences

- Breaking: a single fit that fails a precondition raises `validation_error` (exit code 2) where it raised
  `calculation_error` (exit code 13); a negative discharge minimum and a return period of 1 year or less are refused
  with `outside_physical_range`. Obserwator stores the error code of a failed analysis and has a fixture of the old
  code (`low_flow_negative_quantiles.json`, `calculation_error` `constant_values`, now `validation_error`
  `values_not_all_equal`).
- Some combinations of `fit_method` `mle`, `least_squares` or `all` are newly left out: a GEV by maximum likelihood
  whose c would reach 1 or −1, a Weibull shape beyond 50, tied minima, a least-squares minimum at an end of its
  shapes. The default `l_moments` keeps its quantiles.
- A degenerate sample ends in under a second instead of a minute; a fit followed by its precondition costs one search.
- Results computed by `least_squares` or `all` before the fix differ; they are found by their `formula_versions`,
  which lack `fit_least_squares`.

## Alternatives considered

- **Keep `calculation_error` for the fits:** the failure is foreseeable from the sample, which is what the standard
  calls a precondition, and the GUIs word the standard's `precondition_failed` already.
- **New reasons in `distribution_left_out`:** every consumer that reads the notice would change for no gain; the
  constraint is in the error of a single fit.
- **Search twice, once for the precondition and once for the fit:** a maximum-likelihood search takes about 0.15 s;
  `fit_all` with `all` would double it.
- **Unbounded searches with scipy's `fit`:** it stopped far from the maximum of the likelihood and ran for a minute on
  degenerate samples (ADR-0021, amendment of 2026-11-18).
- **Least squares by one run with tighter tolerances in the unit of the sample:** a tolerance in m³/s is a different
  tolerance in L/s; the standardised sample makes the search the same in every unit.
