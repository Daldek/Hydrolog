# 0021. Fit methods of flood frequency: maximum likelihood, moments, L-moments and least squares

- Status: accepted
- Date: 2026-11-06
- Builds on: plan `docs/plans/2026-11-06-flow-statistics-feedback.md` (decision D1), the reports 4 and 12 of „Zgłoś
  uwagę”
- Amended: 2026-11-06 (below), `fit_method` `all` and the default `l_moments` (the plan's erratum, decision D6);
  2026-11-18 (below), maximum likelihood by Hydrolog's own search, no parameters without a maximum, its
  preconditions and no negative low flows (the fix of a gross defect, Nogat CMP-9.2)

## Context

Two reports of „Zgłoś uwagę” on Statystyka przepływów asked for a choice of the method that estimates the parameters
of the distributions („Brakuje wyboru metody dopasowania parametrów rozkładu; poza MLE dodać MoM, L-momenty i
najmniejsze kwadraty”). `stats flood-frequency` fitted the log-normal, GEV, Pearson III and Weibull distributions to the
annual maxima by maximum likelihood only: `FloodFrequencyAnalysis` calls scipy's `fit` (`lognorm` with the location
fixed at 0, so two parameters; `genextreme`, `pearson3` and `weibull_min` with three), computes the quantiles, K-S, A²
and AIC from the parameters and ranks the distributions by AIC.

## Decision

1. **The option `fit_method` of `stats flood-frequency`** (`--fit-method`): `mle` (the default; the results do not
   change), `moments`, `l_moments`, `least_squares`. The result carries `fit_method`; `hydrolog-stats-flood-frequency/1`
   gains the field (additive). The library takes the keyword `fit_method` (default `mle`) on
   `FloodFrequencyAnalysis.fit_log_normal`, `fit_gev`, `fit_pearson3`, `fit_weibull` and `fit_all`;
   `hydrolog.statistics.FIT_METHODS` lists the values.
2. **One parametrisation for every method**, today's: `lognorm` with location 0, `genextreme` (scipy's shape c = −ξ),
   `pearson3` (its parameters are the skewness, the mean and the standard deviation), `weibull_min`. The quantiles, K-S,
   A² and the ranking take the parameters whatever method gave them.
3. **`moments`**: the distribution's mean, standard deviation and, for three parameters, skewness equal the sample's:
   the mean, the standard deviation with the divisor n − 1 and the adjusted skewness G1 = √(n(n − 1)) / (n − 2) ·
   m3 / m2^(3/2) (m2, m3 the central moments of the sample). Log-normal: s² = ln(1 + Cv²) and scale = mean / √(1 + Cv²);
   Pearson III: the skew G1, the location the mean, the scale the standard deviation; GEV: the shape c whose skewness
   is G1 (Brent's method on scipy's `genextreme.stats`), then the scale and the location from the variance and the mean.
4. **`l_moments`**: the distribution's λ1, λ2 and, for three parameters, τ3 equal the sample's, from the unbiased
   probability-weighted moments b0, b1, b2 of the sorted sample: λ1 = b0, λ2 = 2b1 − b0, τ3 = (6b2 − 6b1 + b0) / λ2
   (Hosking and Wallis 1997). Log-normal with location 0: λ2 / λ1 = erf(s/2), so s = 2 erf⁻¹(λ2 / λ1) and scale =
   λ1 exp(−s²/2); GEV: the shape c solving τ3 = 2(1 − 3^−c) / (1 − 2^−c) − 3 (Brent's method), then α = λ2 c /
   ((1 − 2^−c) Γ(1 + c)) and ξ = λ1 − α (1 − Γ(1 + c)) / c (scipy's c is Hosking's k); Pearson III: α = 4/γ² from |τ3|
   by the rational approximations of Hosking and Wallis, then γ = 2 sign(τ3) / √α, σ = λ2 √(πα) Γ(α) / Γ(α + ½) and
   μ = λ1.
5. **The Weibull distribution of the moments and the L-moments is the GEV of the negated sample**: −X ~ GEV(c, ξ, α)
   with c > 0 is X ~ Weibull with the shape 1/c, the scale α/c and the location −ξ − α/c. It therefore needs a sample
   skewness above −1.1395 or an L-skewness above −0.1699, the values of the Gumbel distribution (c = 0).
6. **`least_squares`**: the parameters minimising Σ (x₍ᵢ₎ − Q(pᵢ))² over the sorted sample and the quantiles at the
   plotting positions of the result's `empirical` (Weibull's, exceedance i / (n + 1)), started from the `moments`
   estimate.
7. **AIC stays the ranking**, from the log-likelihood at the estimated parameters with the same number of parameters (2
   for the log-normal, 3 for the others); a method other than `mle` ranks the distributions it fitted.
8. **No parameters: the distribution is left out.** The moments and the L-moments need 3 values, not all equal, a
   sample skewness or L-skewness inside the distribution's range and, for the log-normal, values above 0. Otherwise the
   library raises `CalculationError` (`calculation_error`) for that distribution with `details.reason`
   `too_few_values`, `constant_values`, `out_of_range` or `non_positive_values`, `details.distribution` and
   `details.fit_method`. The operation leaves the distribution out with a notice when it fits all four, and ends with
   the error when none remains or the one requested cannot be fitted.
9. **A fit whose support leaves out an annual maximum stays.** The moments and the L-moments may give a distribution
   under which an annual maximum has no density, most often a lower bound of Pearson III or Weibull above the smallest
   annual maximum (scipy's maximum likelihood may too: its Weibull of `tests/fixtures/maksima_roczne.csv` has the
   location 94.2, above the maxima 81.6 and 87.2). Its quantiles, K-S and A² are kept; its log-likelihood is −∞, so its
   AIC is infinite (`null` in JSON) and it ranks after every fit with a finite AIC; a notice names the values outside
   the support.
10. **GUI**: a choice field „Metoda estymacji parametrów” in Dane of Statystyka; both runs (the table's and the
    curves') use it.

## Consequences

- An additive change of `stats flood-frequency`: the option and the field `fit_method`. An `aic` of `null` was already
  possible (the Weibull above; the schema leaves the items of `distributions` open and the GUI shows „—” with „brak AIC
  w wyniku”) and becomes frequent with the new methods. The default results are those of before.
- With the moments and the L-moments, Pearson III and Weibull often rank last. In trials of 300 samples of 30 and of
  60 years drawn from GEV, log-normal, Pearson III and Weibull distributions, the fitted lower bound lay above the
  smallest annual maximum in 9-81 % of the Pearson III fits and 16-91 % of the Weibull fits (the most with the GEV
  samples of a heavy tail); the notice says why.
- `FloodFrequencyAnalysis` can compare the methods on one sample.
- The unit tests recover known parameters from large synthetic samples for every distribution and method, check the
  sample L-moments against a case computed by hand and the moments against the sample's mean, variance and G1.
- COMPUTATION_PATHS, USAGE, the CHANGELOG, the guide `instrukcja/`, `AGENTS.md` and `llms.txt` describe the methods.

## Alternatives considered

- **Leave out a fit whose support leaves out an annual maximum** (the plan's first wording): Pearson III and Weibull
  would be missing from most results of the moments and the L-moments, though the user asked to compare their
  quantiles of floods; in the trials above the bound that excluded a value was always the lower one.
- **Another ranking for the new methods** (A², the correlation of the probability plot): the ranking of a method would
  not be comparable with that of `mle`.
- **The moments of the logarithms for the log-normal**: with the divisor n they are the maximum likelihood estimate;
  the method of moments matches the moments of the flows.
- **The approximation of the GEV shape k ≈ 7.8590z + 2.9554z², z = 2 / (3 + τ3) − ln 2 / ln 3** (Hosking, Wallis and
  Wood 1985): it errs by less than 10⁻³ only for shapes between −0.5 and 0.5 (τ3 from about −0.1 to 0.5) and by 0.08 at
  τ3 = −0.5; the exact relation is solved instead. The rational approximation of Pearson III stays: its α is within
  3·10⁻⁵ (relative) of the exact relation τ3 = 6 I₁/₃(α, 2α) − 3 over the whole range.
- **The three-parameter log-normal for the L-moments** (the generalised normal of Hosking and Wallis): each method
  would compare other distributions.

## Amendment (2026-11-06, every combination and the default L-moments)

The author's review of the deployed Statystyka (the plan's erratum of 2026-11-06, decision D6) changes points 1, 7 and
8:

- **`fit_method` gains `all`**: each distribution fitted by each of the four methods, as `distribution` has `all`. In
  the library `FloodFrequencyAnalysis.fit_all(fit_method="all")` gives up to 16 results keyed
  `"<distribution>/<fit_method>"` (`"gev/l_moments"`); with one method the keys stay the distribution names. The
  `fit_*` of one distribution take one method, and `FIT_METHODS` still lists the four methods; `fit_all` takes
  `distribution` too, so `stats flood-frequency --distribution gev --fit-method all` is the GEV by each method (one
  combination asked for raises its own error, as `fit_gev` does).
- **Every item carries its `fit_method`**: `FrequencyAnalysisResult.fit_method` is the method that gave its
  parameters, so the items of `distributions` say which combination they are; the result's `fit_method` stays the
  value asked for (`all` included). Both are additive in `hydrolog-stats-flood-frequency/1`.
- **One ranking by AIC over all the items** (point 7). The AICs of the methods compare: each is the log-likelihood at
  the method's parameters with the distribution's number of parameters. Maximum likelihood should give the lowest AIC
  of its distribution, but scipy's `fit` is a numerical search that may stop short of the maximum: on the sample of
  the unit tests (`_FLOODS`, 11 values) its GEV has the AIC 129.1 and the L-moments' GEV 118.6.
- **A combination without parameters is left out** with `distribution_left_out`, whose `fit_method` names the method
  (point 8). With `all` maximum likelihood fits each distribution, so `all` never ends with the error of none
  remaining.
- **The default becomes `l_moments`** in the library, the CLI, MCP and the GUI, instead of `mle` (point 1): maximum
  likelihood is less stable on the short samples of annual maxima (the KZGW minimum is 30 years), where scipy's
  three-parameter searches depend on their start and may end in a local optimum (above); the L-moments are linear in
  the ordered sample, so the largest floods weigh less, and they exist whenever the mean does (Hosking and Wallis
  1997). The default results change; the numbers the guide quotes follow.

## Amendment (2026-11-18, maximum likelihood that reaches the maximum or reports that there is none)

The literature research of the formulas of 2026-11-18 found scipy's `fit` far from the maximum of the likelihood (two
gross defects, Nogat CMP-9.1) and maximum likelihood run at its singularity and without preconditions. The fix,
released at once (CMP-9.2), changes points 1, 7, 8 and 9 and the first amendment:

- **Maximum likelihood is Hydrolog's own search** (point 1). scipy's `fit` starts the GEV from c = −0.5 and the scale
  1 and, on annual maxima of hundreds of m³/s, often stopped at a degenerate point: on the sample of the unit tests
  (`_FLOODS`) at c = −6.26 with the log-likelihood −61.55 against the maximum −56.13 of R's `evd`, `extRemes` and
  `ismev`, and Q100 = 2.5·10¹² m³/s instead of 505. The GEV, Pearson III and Weibull are now fitted by Nelder-Mead on
  the standardised sample (x − mean) / sd from the L-moments' estimate, moved inside the support, run again from the
  point found until a run gains at most 10⁻⁹ of log-likelihood and checked to be no less likely than its start; the
  log-normal keeps its closed form. The Fisher-Tippett fit of annual minima (`stats low-flow`,
  `fit_fisher_tippett_minima`), the GEV of the negated minima, takes the same search.
- **No maximum, no parameters** (points 7 and 8, the first amendment). The likelihood of a three-parameter
  distribution grows without limit where its density is infinite at a bound placed at the closest value (Smith
  1985): the GEV with c ≥ 1, Pearson III with |skewness| ≥ 2 and Weibull with a shape ≤ 1. The search keeps the
  shapes short of these limits, and one that ends within 10⁻³ of a limit is a `calculation_error` with
  `details.reason` `unbounded_likelihood` (`not_converged` when no run settles). Among several combinations such a
  fit is left out with `distribution_left_out` and never ranked: scipy's fits at the singularity led the AIC ranking
  (`_FLOODS`: Pearson III with AIC 102.3 ahead of every regular fit, 118.6 to 121.6). Maximum likelihood therefore no
  longer fits each distribution, and `all` can end with the error of none remaining (values all equal).
- **Preconditions** (point 8). Maximum likelihood needs one value more than the distribution has parameters (3 for
  the log-normal, 4 for the others), values not all equal and, for the log-normal, above 0 (`too_few_values`,
  `constant_values`, `non_positive_values`). `FloodFrequencyAnalysis` and `fit_fisher_tippett_minima` refuse a value
  that is not a finite number (`validation_error`, `details.reason` `not_finite`), and `stats low-flow` needs 4
  complete hydrological years instead of 3.
- **No negative discharge** (the low-flow fit). A quantile of annual minima below 0 comes from a fitted support that
  reaches below zero flow, which WMO-No. 1029 (2009, sec. 7.5) excludes (a lower bound at 0 or above). It is NaN
  (`null` in JSON) with the new warning `negative_quantiles` (`details.return_periods` of the quantiles left out,
  `details.zero_return_period` = 1 / F(0), the years at which the fitted distribution reaches 0), never a negative
  number; the quantiles of the other return periods stay. A stage (`parameter` H of `half_year_file`;
  `discharge=False` of `fit_fisher_tippett_minima`), whose zero is the gauge's, keeps its quantiles.
- **Point 9 holds for the other methods only**: a fit by maximum likelihood gives a density to every value.

The default (`l_moments`) results do not change; those of `mle` and `all` change where scipy stopped short of the
maximum (on samples whose spread is far from 1) or at a singularity. The CHANGELOG says which stored results to
recompute. Alternatives considered: refusing a low-flow fit with a negative quantile (its valid quantiles of the other
return periods would be lost: Obserwator stores 25 of them, up to 1000 years); keeping scipy's `fit` on a rescaled
sample or checked against the L-moments' likelihood (both still return a point at the singularity); a lower bound of
Pearson III or Weibull fixed below the smallest value, as KZGW 2017 (p. 36) does by hand (another estimator than
maximum likelihood, for another decision).
