# 0041. Implausible rating curves: flagged, not refused

- Status: accepted
- Date: 2026-11-17
- Builds on: the author's decision of 2026-11-17 (an item of the patch release 0.8.1)
- Amends: [ADR-0029](0029-station-analyses-for-obserwator.md) (point 4: the result of `hydrometrics rating-curve`)

## Context

`hydrometrics rating-curve` fits Q = a·(H − H₀)^b to stage–discharge pairs, and with `years_per_period` the curve of
each block of years too (ADR-0029). Obserwator stores these curves and shows them in „Kolejne okresy”. At IMGW-PIB
150170070, with periods of 10 years, the curves of 1981–1990 (b = 6.50, H₀ = −88 cm under stages of 45 to 161 cm) and
2001–2010 (b = 6.62, H₀ = −179 cm under stages of 6 to 131 cm) came out as any other, though no single control gives
them: the daily pairs of a period follow the rating that IMGW-PIB applied in each year, and a period that spans a change
of that rating (a moved gauge zero, an eroded or silted channel) holds pairs of two relations. The least squares then
bend one curve through both clouds with a steep exponent and an H₀ far below every stage. The neighbouring periods
(1991–2000, 2011–2020, 2021–2024: b from 1.90 to 2.37) and the curve of all the pairs (b = 3.02, H₀ = −34 cm) are
ordinary.

## Decision

1. **The criteria.** A curve is plausible for one stage–discharge relation when its exponent b lies from 1 to 4,
   bounds included, and its H₀ lies below the lowest stage of its pairs by at most the range of their stages:
   H_min − H₀ ≤ H_max − H_min. The stages are those of the pairs given to the fit (all the pairs of the range, or of
   the period), before outliers are removed. A section control gives b of about 1.5 (a rectangular section) to 2.5 (a
   triangular one), a channel control by Manning's equation 5/3 in a wide rectangular channel; 1 to 4 leaves compound
   sections and overbank flow in. The zero-flow level lies at or somewhat below the lowest stage; an H₀ deeper than the
   whole observed range has no physical meaning for one control.
2. **The fields.** `RatingCurveAnalysis` (the curve of all the pairs) and `RatingPeriod` (each period's curve) gain
   `plausible` (bool) and `implausibility_reasons` (list): `b_out_of_range` and `h0_too_low`, in that order, empty
   for a plausible curve. A period without a curve (`reason` `too_few_pairs` or `fit_failed`) has both null. The fields
   are optional in `hydrolog-hydrometrics-rating-curve/1` (`_ADDED_FIELDS`), whose version stays 1, and the
   dataclasses gain them last, so positional construction is unchanged.
3. **The notice.** `implausible_rating_curve` (warning), one per result when any curve fails: `details.curves` names
   the curves, `"all pairs"` for the curve of all the pairs and `"1981-1990"` for a period (the form of
   `reference_level_not_computed`), and `details.b` and `details.h0` give their b and H₀ in the same order, rounded to
   six significant digits as the message writes them (the result keeps the exact numbers). The GUI words each curve
   with its b and H₀ in Polish (`each` of `web/src/labels/notices.js`).
4. **What does not change.** The fits, the splitting into periods, the reference level and discharge and their
   values: an implausible curve is still given and is not an error.

## Consequences

- Obserwator and other clients read `plausible` to mark or hide a curve; a client that words notices by code (Obserwator
  shows each code once) gets every implausible curve in one notice.
- A curve of one relation with an unusual section (b just above 4) is flagged too; the reasons say which bound it
  passes, and the number is the result's `b`.
- Results of earlier versions lack the fields and still validate.

## Alternatives considered

- **Refusing the curve** (`calculation_error`): the curve, its fit and the periods beside it are still worth showing;
  the flag keeps them.
- **Splitting a period at the change of the rating**: finding the year of the change is another analysis
  (`stats homogeneity` finds change points of annual series); the periods stay the blocks of ADR-0029.
- **R² as the criterion**: a low R² also comes from the scatter of one relation (hysteresis, ice, weeds); it does not
  single out a mixture of two relations, whose fit may reach R² 0.84 (150170070, 1981–1990).
- **One notice per curve**: clean details, but a long series in years would give dozens of notices, and a client that
  shows one notice per code would name one curve only.
