# 0048. Anderson-Darling critical values by a parametric bootstrap

- Status: accepted
- Date: 2026-11-18
- Amended by [ADR-0055](0055-the-frequency-estimators-refuse-by-preconditions-and-search-within-bounds.md)
  (2026-11-19): A² is the formula `anderson_darling` with a spec; its critical values are unchanged
- Amended by [ADR-0074](0074-intervals-of-the-quantiles-and-of-the-median-annual-flow-duration-curve.md)
  (2026-11-25): the same 999 refits of an L-moments fit also give the percentile interval of its quantiles
- Builds on: the audit of the computation standard of 2026-11-18 (TRIAGE T30, flood frequency §1.5)
- Amends: [ADR-0021](0021-fit-methods-of-flood-frequency.md) (the goodness of fit of every fit)

## Context

Every fit of `stats flood-frequency` carries its Anderson-Darling statistic A² and `ad_critical_values`, and the GUI
marks the fit ✓ when A² is below the 5 % value. Up to 0.8.x the values were the fixed table 1.610, 1.933, 2.492, 3.070,
3.857 (15 … 1 %), the points of A² for a distribution given in advance (case 0 of Stephens 1974). With the parameters
estimated from the same sample A² is much smaller: by a Monte Carlo of the audit (2000 samples, L-moments fits) the
true 5 % point is 0.54–0.58 for a GEV of 30 or 60 maxima, about 0.8 for a log-normal and about 1.0 for a Pearson III,
and no GEV or log-normal sample reached 2.492. The check never rejected: the ✓ said nothing. The points depend on the
distribution, the method of estimation, the sample size and the shape. Published tables for estimated parameters exist
for single cases (Stephens 1977 for the Gumbel and Chowdhury, Stedinger and Lu 1991 for the GEV, named by the audit and
not opened; Laio 2004, Water Resources Research 40, W09308, for maximum likelihood), none for Hydrolog's four methods
and four distributions together, and the standard of computations keeps a published table in a data file transcribed
twice (CMP-2.5).

## Decision

1. **A parametric bootstrap of each fit.** `ad_critical_values` of a fit are the 85, 90, 95, 97.5 and 99 % quantiles
   of A² over 999 samples of n values drawn from the fitted distribution, each refitted by the same method (Stute,
   González Manteiga and Presedo Quindimil 1993). The seed is fixed (20261118), so a sample always gets the same
   values. A sample the method cannot fit is left out. A² keeps its form (F clipped to [10⁻¹⁰, 1 − 10⁻¹⁰]); the
   samples that fall outside the support of their refit belong to the same distribution of A², which gives Pearson III
   and Weibull large upper points.
2. **For the L-moments only.** Their refits are closed forms: the four distributions take about 0.2 s together. The
   refits of maximum likelihood and least squares are iterative searches (a maximum-likelihood GEV takes about 0.15 s,
   999 of them minutes; the method of moments solves the GEV shape numerically too); their `ad_critical_values` is
   `null`, the GUI shows their A² without ✓ or ✗, and A² remains a distance for comparing fits.
3. **The texts.** The notice `ks_test_approximate` no longer recommends A² without qualification; the GUI shows the
   critical value of each fit in the title of its mark instead of one value in the column head.

## Consequences

- Breaking: `ad_critical_values` changes from the fixed table to numbers of each fit (about 0.4–0.9 at 5 % for the
  log-normal and the GEV) and is `null` for the methods other than `l_moments`. Fits that passed the fixed table
  may now fail (A² = 5.96 of a GEV on a bimodal sample of 40 values against 0.62).
- A fit by L-moments takes about 0.05 s longer per distribution.
- Clients that show a mark (Obserwator, Hydrograf) read `ad_critical_values["5%"]` of each fit and must accept `null`.

## Alternatives considered

- **Published tables per distribution**: none covers the L-moments of all four distributions, and each would be a
  transcribed table with its own conventions of estimation (CMP-2.5).
- **A bootstrap for every method**: minutes for one `stats flood-frequency` with maximum likelihood; a smaller
  number of samples would make the 1 % point a guess.
- **Dropping the mark**: loses a valid test for the default method.
