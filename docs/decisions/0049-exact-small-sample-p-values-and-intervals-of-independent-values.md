# 0049. Exact small-sample p-values and intervals on independent values

- Status: accepted
- Date: 2026-11-18
- Builds on: the audit of the computation standard of 2026-11-18 (TRIAGE T22, trend and regime findings 2, 3, 4, 6)
- Amends: [ADR-0022](0022-homogeneity-tests.md) (the K-S p-value), [ADR-0031](0031-regime-seasonality-harmonics-sens-slope-and-baseflow.md)
  (Sen's interval), [ADR-0033](0033-review-of-the-station-analyses.md) (the Mann-Kendall p-value)

## Context

The audit found four places where a p-value or an interval rested on an approximation outside its validity:

- `stats mann-kendall` took p = 2 (1 − Φ(|z|)), which is exactly 0 for |z| above about 8.3 (50 increasing values:
  0 instead of 1.3·10⁻²⁴), and used the normal approximation of S from 3 values, while it holds from about 10
  (Kendall 1975, p. 55, after Gilbert 1987, p. 211; KZGW 2017; Hirsch, Slack and Smith 1981): 7 values of Helsel et
  al. (2020, Example 10.3) gave 0.0069 against the exact 0.0028. Gilbert gives Sen's interval "for n as small as 10"
  (p. 218).
- `stats homogeneity` took scipy's `ks_2samp`, documented as exact; scipy's exact distribution assumes no ties, and
  annual maxima published to three significant digits tie: on Helsel's Example 5.1 data scipy gives 0.0524, the exact
  value with ties (R's `ks.test`) 0.0478, and the decision at 0.05 flips.
- `stats monthly` built the interval of a month's mean as mean ± t·s/√n over all its daily values; daily flows are
  autocorrelated (lag-1 0.71–0.89 at Kłodzko in 2010), which makes the interval 3 to 25 times too narrow.

## Decision

1. **Mann-Kendall p from the upper tail.** From 10 values p = 2 P(Z > |z|) by `norm.sf`, as R's `trend`.
2. **The exact Mann-Kendall p below 10 values.** P(|S| ≥ |s|) of the exact permutation distribution of S (Gilbert
   1987, section 16.4.1, Table A18): every distinct ordering of the values equally likely, the numbers of orderings by
   their inversions the q-multinomial coefficients (MacMahon 1916), so ties are exact too. From 10 values the normal
   approximation stays, the procedure of KZGW (2017) and of R's `trend`. The result gains `p_value_method`
   (`exact` or `normal`), an optional field of `hydrolog-stats-mann-kendall/1`.
3. **No Sen interval below 10 values.** `sen_slope_lower` and `sen_slope_upper` are `null` there: the normal
   approximation of S that C = z √Var(S) needs does not apply. `sen_slope()` itself still builds the interval from the
   `var_s` it is given (Gilbert's Example 16.5 has 8 values).
4. **The exact K-S p with ties.** With tied values and m·n < 10 000 (R's bound for its exact test) the p-value is
   P(D ≥ d) over all splits of the pooled values, ties respected, counted in integers on the lattice of the two
   samples, D taken where a group of equal values ends (Schröer and Trenkler 1995; R's `ks.test`). Without ties, and
   with ties beyond that size, it stays scipy's.
5. **The monthly interval on yearly means.** The interval is mean ± t·s_y/√k with s_y the standard deviation of the
   k means of the month in the separate years and k − 1 degrees of freedom, around the mean of all values of the
   month. A month with values of one year has no interval (`null`), with the new notice `single_year_month`.

## Consequences

- Breaking: Mann-Kendall p-values below 10 values change (Gilbert's n = 4, S = 4: 0.308 → 0.333; Helsel's 7 values:
  0.0069 → 0.0028), Sen's interval below 10 values is `null`, strong trends get a p above 0; K-S p-values of samples
  with ties are smaller (Helsel 5.1: 0.0524 → 0.0478); monthly intervals are wider, and a one-year series has none.
- Obserwator (trends, regime tables) and other clients that print these numbers must accept `null` intervals.

## Alternatives considered

- **A notice below 10 values instead of the exact p**: the exact p is cheap (n < 10) and removes the approximation.
- **The exact Mann-Kendall p up to 40 values** (Gilbert 1987, section 16.4.1): it would change the p-values of the
  typical series of 30–41 annual maxima away from the normal procedure of KZGW (2017).
- **An AR(1) effective sample size for the monthly interval**: needs a model of the autocorrelation; the yearly means
  need none and are independent as far as the years are.
