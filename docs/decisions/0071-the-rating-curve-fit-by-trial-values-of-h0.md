# 0071. The rating curve fit by trial values of H₀, and least squares without a minimum

- Status: accepted
- Date: 2026-11-21
- Builds on: [ADR-0063](0063-the-station-statistics-by-specs.md) (spec `rating_curve_fit`, the precondition
  `least_squares_minimum`), [ADR-0055](0055-the-frequency-estimators-refuse-by-preconditions-and-search-within-bounds.md)
  (a search within bounds, an end at a bound is no minimum), [ADR-0041](0041-implausible-rating-curves-flagged-not-refused.md)
  (implausible curves flagged, not refused); Nogat PROGRESS Next 6 and 7 (the fit that does not converge at
  Obserwator's stations, to be examined), the author's decisions of 2026-11-21 (planned fixes go into 0.9.0)

## Context

Obserwator's analyses of 2026-11-17 to 2026-11-19 (Hydrolog 0.8.0 to 0.9.0.dev0) failed with „Optimal parameters not
found: The maximum number of function evaluations is exceeded” in five analyses at four IMGW-PIB stations: 149190350
(`rating_curve`, 2016–2025), 149190390 (`rating_curve.periods`), 150169991 (both, 1981–1990) and 150230070
(`rating_curve.periods`); periods of seven more stations (149190320, 150190010, 151219999, 152180100, 152190070,
152230060, 153220170) and of ČHMÚ 0-203-1-200500 were `fit_failed`. The search was SciPy's trust region method from
one start of H₀. The least squares of Q = a (H − H₀)^b were profiled over H₀ (the best b at each H₀, a in closed form)
for every fit of these stations:

- in 21 of 58 fits the sum of squares falls without a minimum as H₀ goes to −∞ and b to +∞, toward the exponential
  Q = C e^(kH), the limit of the curve: the daily pairs rise faster than any power of the head, as those of two ratings
  in one period do (149190390: the gauge zero moved in 1988 and 2018; 150169991: in 1984) or of a compound control.
  WMO-No. 1044 (sect. 1.5.4) finds e by trying values until the rating is straight on logarithmic paper; these pairs
  stay concave at every trial value. The old search ran out of evaluations on them, or stopped where the valley was
  flat enough and returned that point: 0.9.0.dev4 gave b 50.2, H₀ −765 cm at 149190350 and b 24.5 at 150230070,
  2001–2010, and needed 255 s to refuse 149190390;
- the other fits have a minimum, a few at the bound below the lowest stage (150169991: b 5.07, H₀ 2 cm, the lowest
  stage) or deep (150230070, all pairs: b 25.0, H₀ −1,597 cm; 152230060, 2001–2010: b 60.6), and one next to that
  bound that the old search missed (149190390, 2011–2020: b 0.25, R² 0.06).

## Decision

1. **The search profiles the least squares over trial values of H₀.** Below the lowest level: the bound, `h0_initial`
   and the range of the levels times 2^j for j = −20 to 10; at each the best b, a in closed form (a grid of b, then
   Brent's bounded search); ln of the depth refined between the neighbours of the best trial; then the trust region
   search (SciPy's `curve_fit`, unchanged tolerances) from that end. `h0_initial` stays an option and is one of the
   trials.
2. **The search is bounded and an end at a bound is no minimum.** b from 0 to 100 (25 times the largest plausible
   exponent of ADR-0041, so that minima however implausible are still given and flagged, as ADR-0041 decided) and H₀
   down to 1024 ranges of the levels below the lowest level; an end within 10⁻³ of b's bound, within 10⁻³ relative of
   H₀'s deepest bound, or a trust region search that does not settle fails the precondition `least_squares_minimum`
   (`validation_error`, its name kept), whose text and hint now name the cause.
3. **A period without a minimum says so.** With `years_per_period` such a period has `reason`
   `no_least_squares_minimum`; `fit_failed` stays for the other refusals (levels or discharges all equal).
4. **`formula_version` of `rating_curve_fit` is 2.** Minima that the old search reached are the same within 10⁻⁶ (the
   catalog's examples, R's `nls` oracle); flat ones may end lower (150230070, all pairs: b 25.0 instead of 24.5,
   R² 0.780701).

## Consequences

- Breaking: results of 0.9.0.dev0 to dev4 at the points of a valley are refused; stored `rating_curve*` analyses are
  found by `formula_versions` and recomputed. Of the analyses of the failing stations, the curve of all the pairs of
  149190390, 151219999, 152190070, 152230060 and 153220170 has no minimum, so their `rating_curve.periods` is refused
  as a whole (see the last point); 150230070 and 150169991 now give their curves.
- Obserwator words `hydro.rating.reason.no_least_squares_minimum` and its text of the refusal.
- A fit costs one profile: about 0.1 s for a few thousand pairs, under 2 s for 16,000.
- With `years_per_period`, a curve of all the pairs without a minimum refuses the whole result, although its periods
  have curves. Giving the periods with a null curve of all the pairs and a notice changes the meaning of
  `hydrolog-hydrometrics-rating-curve/1` (its curve fields are required numbers). Decided by the author on 2026-11-21:
  the refusal stays; the periods without the curve of all the pairs go into version 2 of the document (AGI-4.1),
  made once more changes of it are collected (PROGRESS, Next 14).

## Alternatives considered

- **Only a bound of b on the old search:** the search from one start still crawled along the valley (266 s and no
  result at 149190390, 1981–1990) and missed the minimum next to H₀'s bound (149190390, 2011–2020).
- **b at most 20, the test bound of the curve's spec:** refuses the deep minima of b 25 to 61 that ADR-0041 would flag.
- **Comparing with the exponential limit:** exact, but equal sums of squares of a flat valley and of the limit are not
  told apart in floating point; the bounds decide the same fits.
