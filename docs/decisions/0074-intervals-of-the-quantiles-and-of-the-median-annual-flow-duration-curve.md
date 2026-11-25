# 0074. Intervals of the quantiles and of the median annual flow-duration curve

- Status: accepted
- Date: 2026-11-25
- Amends: [ADR-0048](0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md) (its refits also give the
  interval of the quantiles of an L-moments fit)
- Builds on: Nogat plan `2026-11-24-interval-estimation`, step H1 (approved by the author on 2026-11-24: „Przedziały
  ufności: 1. liczymy oba; 2, 3, 4, 5, 6 – ok.”), Nogat ECO-091 (intervals beside point estimates, computed by Hydrolog,
  shown by Obserwator), CMP-2.3 and CMP-6.11 of Nogat's computation standard, ECO-090 (one chart module in the kit),
  [ADR-0050](0050-formulas-declared-by-specs.md)

## Context

`stats flood-frequency`, `stats low-flow` and `stats duration-curve` gave point estimates only: the flood and
precipitation quantiles Q_p and P_max,p of four distributions by four methods, the low-flow quantiles NQ_T of the GEV of
the negated annual minima, and the period-of-record flow-duration curve, whose spec said its confidence intervals were
not computed. A design value at T of 100 to 1000 years from 30 to 60 maxima is an extrapolation, the regulation (Dz.U.
2026 poz. 692, annex 3, note 3) adds to the check flood its error at the confidence 0.84, and KZGW (2017) computes it as
the upper bound of a one-sided interval; the handbook said „Hydrolog tej poprawki ani przedziału ufności nie liczy”. The
author's feedback #13 to Obserwator asked for interval estimates beside the point estimates, Hydrolog computing them and
Obserwator showing them (ECO-059); ECO-091 fixed their shape for the ecosystem: two-sided, central, at each
`confidence_level` asked, Obserwator storing 0.95 and 0.68. The cost has to fit Obserwator's on-request computation of
30 s and its build of every station: the L-moments fits already run 999 parametric bootstrap refits (ADR-0048), a
maximum-likelihood refit takes about 0.15 s.

## Decision

1. **An L-moments fit: the percentile interval of a parametric bootstrap** (spec `quantile_interval_bootstrap`,
   `formula_version` 1, status oracle only). The 999 samples of n values drawn from the fit with the seed 20261118 and
   refitted by L-moments, which already give `ad_critical_values` (ADR-0048, same samples, same refits), give per return
   period the quantiles of the K refits kept; the bounds are their empirical quantiles at (1 − c)/2 and (1 + c)/2 by
   type 6 of Hyndman and Fan (positions i/(K + 1); numpy's `weibull`, R's type 6), with K = 999 the 25th refit from each
   end at 0.95 and the 160th at 0.68 (Efron and Tibshirani 1993, ch. 13; Hosking and Wallis 1997; Kyselý 2008 for the
   parametric before the nonparametric bootstrap). A sample the L-moments cannot fit is left out, not drawn again, and
   counted: `ci_samples` is K; fewer than 990 kept give no interval (`bootstrap_failures`). Verified against the frozen
   oracle of R `lmomco` 2.5.8, `qua2ci.simple` on the 34 Polana maxima of KZGW ex. 3.2 with 20,000 simulations
   (`tests/oracles/interval_lmomco_r.*`), within a Monte Carlo tolerance, and by its generated properties.
2. **A maximum-likelihood fit: the delta method as KZGW (2017) applies it** (spec `quantile_interval_delta`,
   `formula_version` 1, status referenced). Q_T ∓ zσ_T with z = Φ⁻¹((1 + c)/2); the bound of the support held at its
   estimate and the expected information of the two other parameters in closed form: the log-normal on ln Q (eq. 3.41
   and 2.9), Pearson III by eq. 3.26–3.27, rearranged without its cancellation of order λ = 4/G² as G → 0 so that G = 0
   gives the normal interval, the Weibull by eq. 3.57 applied to Q_T − loc, the two-parameter quantile it is derived
   for; the GEV by its observed information, the negative Hessian of the log-likelihood by central differences, only
   where scipy's c < 0.5 (ξ > −0.5) and the information is positive definite, else no interval (`nonregular_fit`; Smith
   1985). `stats low-flow` uses the GEV row on the negated minima, its bounds negated and swapped. KZGW's u_β = 0.994 at
   β = 84 % is z at c = 0.68, so the upper bound at 0.68 is KZGW's one-sided 84 % bound. Reference cases: KZGW ex. 3.2
   (table 3.9, Pearson III, the Czarna at Polana), ex. 3.3 (table 3.12, log-normal, the Rypienica at Rypin) and table 2.3
   (log-normal, precipitation), 15 cases (`tests/fixtures/formulas/flood-interval-cases.json`), each taking KZGW's own
   parameters and naming its rounding steps (CMP-6.1); the frozen oracle of R `extRemes` 2.2.1, `ci.fevd` (method
   `normal`) for the GEV (`tests/oracles/interval_extremes_r.*`); exact oracles in mpmath at 50 digits (CMP-6.2). KZGW
   ex. 3.4 (Weibull, the Świślina at Rzepin) is no reference case: KZGW applies eq. 3.57 to Q_T instead of Q_T − ε
   (5.24 against 4.88 m³/s at p = 10 %), and its source, Heo, Salas and Kim (2001), is closed access (CMP-5.2).
3. **No interval for the method of moments and least squares.** Their refits are iterative searches; a bootstrap would
   take minutes per call (ADR-0048, decision 2), over Obserwator's 30 s. Their entries keep the level and have method,
   bounds and samples `null`, with one notice `interval_not_computed` (`fit_method`) per fit.
4. **The median annual flow-duration curve and its interval by order statistics** (spec
   `duration_curve_annual_median_interval`, `formula_version` 1, status referenced). One curve per complete
   hydrological year from its own days; per exceedance percentage the median of the N annual values, the median annual
   curve, the curve of a typical year of Vogel and Fennessey (1994, annual interpretation, p. 494); as its interval the
   narrowest symmetric pair of order statistics Q(k), Q(N + 1 − k) whose binomial coverage 1 − 2F(k − 1) is at least c,
   compared exactly in integers, the years taken as independent (Helsel and Hirsch 2002, sect. 3.3.1, eqs. 3.2–3.3).
   It needs 6 complete years at 0.95, 5 at 0.90 and 3 at 0.68; fewer give no interval at that level
   (`too_few_complete_years`). The source is Helsel and Hirsch, not eq. (10) of Vogel and Fennessey (p. 497) that the
   plan named: its bounds, the α/2 and 1 − α/2 quantiles of the n annual values, are the central range of the annual
   values, which brackets one year's value rather than the median and does not narrow as n grows. Reference case:
   Helsel and Hirsch's example 2 (25 arsenic concentrations, 4.8 ≤ C_0.5 ≤ 110 at α = 0.044); oracle: SciPy's
   `quantile_test` and the binomial coverage in exact rational arithmetic. The period-of-record curve
   (`exceedance_values`) is unchanged beside it and has no interval.
5. **The result and the option.** Each fit of `stats flood-frequency` (`distributions[i]`), the `fisher_tippett` block
   of `stats low-flow` and the top level of `stats duration-curve` carry `intervals`, one entry per level in the order
   asked: `confidence_level`, `ci_method` (`parametric_bootstrap`, `delta`, `order_statistics` or `null`), `ci_lower`
   and `ci_upper` aligned with `quantiles` (or with `curve_exceedance_percents`), an element `null` where undefined, and
   `ci_samples`; `stats duration-curve` adds `annual_median_values`. The three commands take `confidence_level`: one
   number or a list of distinct numbers in (0, 1), default 0.95 (catalog type `number_or_list`, CLI
   `--confidence-level 0.95,0.68`); the library takes `confidence_level=` in `FloodFrequencyAnalysis` (with
   `discharge=`, False for a stage), `LowFlowAnalysis`, `fit_fisher_tippett_minima` and `duration_curve`. Every level
   of a call comes from one computation. Optional fields only: `hydrolog-result/1` and the three domain documents stay
   `/1` (AGI-4.1, ECO-085); the point specs keep their versions, and `formula_versions` names the interval specs used.
6. **The notice `interval_not_computed`** (level `warning`), with `details.reason` `fit_method`, `bootstrap_failures`,
   `nonregular_fit`, `too_few_complete_years` or `below_physical_range` and the details `confidence_levels`,
   `distribution`, `fit_method`, `return_periods`, `complete_years` and `required_years` (`null` where not concerned).
   A bound of a discharge or a precipitation below 0 is `null` (CMP-3.4), the rest kept, with `below_physical_range`
   naming its return periods and levels; a stage (`discharge=False`, the half-year file of parameter H) keeps it.
7. **The coverage, simulated nightly** (CMP-6.11). Tests marked `nightly`, excluded from the default run and the gate
   and run by a CI job at 02:00 UTC (and by hand before each release), simulate each interval at 30 and 60 values and
   at 0.95 and 0.68, with at least 1,000 samples per setting and the seed 20261125, fixed once: an exact method (order
   statistics) is asserted within 3√(c(1 − c)/m) of its exact coverage per element, an approximate one (bootstrap,
   delta) above a stated bound with its reason (CMP-6.8). Their records are kept in
   `tests/fixtures/formulas/interval-coverage.json` and shown under each formula in `docs/FORMULAS.md`, through
   `assert_coverage` and `formulas_markdown` of Nogat's reference module, copied again from Nogat `6920f91`.
8. **The GUI.** The chart module draws a `band` series (`[x, lo, hi]`, filled between its ends, broken where an end is
   missing, read as „label: lo–hi”) with the interface and look of the kit's chart module (ECO-090), so the kit's can
   replace it. Statystyka przepływów draws the band of the active combination on its probability plot, writes
   „[dolna–górna]” in its quantile tiles and the ends of each level in its CSV; the notice is worded in Polish by its
   reason; Wszystkie polecenia shows the bounds of `stats low-flow` and `stats duration-curve` in its table, CSV and
   chart.

## Consequences

- A fit by L-moments costs one quantile function over the 999 refits more; a maximum-likelihood fit microseconds, the
  GEV about 20 log-likelihood evaluations; the duration curve N sorts of a year. Obserwator's stored results grow by two
  arrays per level and fit, not by a second result.
- Minima with a lower bound of c ≥ 0.5 get no interval: every low-flow example of the handbook (the Kaczawa at
  Świerzawa, the Czarna Woda at Bukowna, by daily values and by IMGW-PIB's half-years) gets `nonregular_fit`.
- The coverage of the delta method at 30 values is the method's: in the records of 2026-11-25 below c at long return
  periods for the GEV; it is reported, not forced to c.
- Clients that read the results (Obserwator in step O1, Hydrolog's GUI) must accept `null` methods and bound
  elements; Archiwista and Hydrograf read none of these results.
- `mpmath` is a development dependency (the exact oracles).

## Alternatives considered

- **The profile likelihood** (Coles 2001, sect. 3.3.3): better than the delta method at long T, but one constrained
  search per return period, 25 per fit.
- **A bootstrap for every method:** minutes per call for maximum likelihood, moments and least squares (ADR-0048).
- **A nonparametric bootstrap of the annual extremes:** too narrow for 30 to 60 values (Kyselý 2008).
- **KZGW's tables A.3 and A.4 in code:** Hydrolog computes the information itself; the printed σ of the examples serve
  as reference values only, so no published table enters the code (CMP-2.5).
- **The observed information of all three parameters of Pearson III and Weibull:** with the bound estimated the
  likelihood is not regular below a shape of 2 (Smith 1985), where Hydrolog's search reaches and Polish maxima lie
  (a Pearson III skewness of 1.6 to 1.9 from the L-moments of KZGW's examples), and it reproduces none of KZGW's
  examples.
- **Eq. (10) of Vogel and Fennessey (1994) as the duration curve's interval:** the central range of the annual values,
  an interval of one year's value, not of the median annual curve, and as wide at 60 years as at 10.
