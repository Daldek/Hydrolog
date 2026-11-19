# 0067. The precipitation formulas by specs: design hyetographs and areal precipitation

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs),
  [ADR-0042](0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md) (the Euler type II storm from a curve) and
  [ADR-0046](0046-design-hyetographs-of-whole-steps-and-exact-blocks.md) (whole steps, exact blocks); the research of
  the audit of 2026-11-18 (Nogat, `hyetographs.md`, `hyetographs-cases.json`)

## Context

The precipitation family was the last of Hydrolog without specs (Nogat CMP-2.1): the four hyetograph generators
(`BlockHietogram`, `TriangularHietogram`, `BetaHietogram`, `EulerIIHietogram`), the areal precipitation of gauges and
isohyets (`arithmetic_mean`, `thiessen_polygons`, `inverse_distance_weighting`, `areal_precipitation_idw`,
`isohyet_method`) and the PMAXTP depth of `hydrolog._pmaxtp`. ADR-0042 and ADR-0046 had fixed what the audit found
wrong in the storms (the Euler type II storm, the sampled triangle and Beta, the steps); their checks stayed in the
classes, with reasons of their own (`not_multiple`, `total_mismatch`, `not_covered`, `decreasing`, `type`,
`not_finite`, `exclusive_minimum`), which the GUI words and the network documents carry. The areal functions accepted
a negative depth, area or isohyet, a NaN depth (a NaN result), and raised `OverflowError` or `ZeroDivisionError` for a
large exponent of IDW; nothing bounded the number of steps of a storm.

## Decision

1. **Eight specs, `formula_version` 1, with the names the handbook cites.** In `hydrolog.precipitation.hietogram`:
   `block_hyetograph`, `triangular_hyetograph`, `beta_hyetograph` and `euler_ii_hyetograph` (functions of the same
   names: a total, a duration and a step, with r or α and β; the Euler storm takes the curve as two arrays,
   `durations_min` and `depths_mm`, and returns `peak_start_min` and its total h(Td)). In
   `hydrolog.precipitation.interpolation`: `areal_mean_precipitation`, `thiessen_precipitation`
   (`polygon_areas_km2`), `idw_precipitation` (coordinates in metres, a target point and `power`) and
   `isohyet_precipitation` (`zone_areas_km2`, divided by their sum, KZGW 2017 eq. 2.2). Both modules join
   `FORMULA_MODULES` before the runoff formulas. No input states an applicability range in its sources, so none
   gives a notice; the Euler spec says why in its assumptions.
2. **Tier B and delegated.** `depth_duration_interpolation` (linear in ln D, `EulerIIHietogram.depth_mm`, ADR-0042),
   `pmaxtp_depth` (the PMAXTP lookup of `hydrolog._pmaxtp.fetch_depth`: nothing is computed; the row is declared in
   the hyetograph module because `_pmaxtp` imports no numerical library and the catalog reads it at its cold start)
   and `idw_grid_mean` (the mean of IDW over a grid). SciPy's `betainc`, the integral of the Beta density, is the
   delegated computation `regularised_incomplete_beta`.
3. **Preconditions for what the code could not compute.** Every storm is made of at most a million whole steps
   (`step_within_duration`, `steps_representable`, `whole_steps`); the triangle's peak intensity must be a finite
   number (`peak_intensity_finite`); a curve has one depth per duration, increasing durations and depths that never
   decrease (a physical constraint), and reaches from the step to the duration (`curve_covers`); gauges, polygons
   and zones agree in number and cover some area.
4. **IDW without overflow, gauges at the point averaged.** The weights are `exp(-p (ln d - ln d_min))` normalised,
   the same `d^-p` without overflowing or underflowing to a zero sum; several gauges within 1e-10 m of the point share
   it equally (the first one took it before, so the result depended on the order of the gauges).
5. **The classes and functions of earlier versions keep their refusals** and compute through the specs: the GUI and
   the network documents read their reasons. They move to the standard's reasons with the release that renames
   `outside_typical_range` (ADR-0050, point 3); until then a value the classes take and the spec refuses (a storm of
   more than a million steps, a negative depth of a gauge) is refused with the standard's reason.
6. **Evidence.** Reference cases in `tests/fixtures/formulas/hyetographs-cases.json` and
   `areal-precipitation-cases.json`: Chow et al. (1988) Example 14.3.1 (the triangle's peak and its time), the itwh
   KOSTRA-DWD printouts of Göllheim (30, 60 and 90 min, the depths from the rain rates of p. 7) and Aurich (the peak
   of 9 h at 160 min), DWD's storms of Malitz (2009), the storms of 75 and 150 min of Kaźmierczak and Kotowski (2012,
   Tab. 4.6), Chow Fig. 3.4.3 (a)–(c) and Example 3.7 of NPTEL's Hydrology (IIT Roorkee). The 15-min storm of itwh and
   the 180-min storm of the Wrocław monograph place the peak a step later than A 118 as quoted: they are recorded as
   discrepancies (CMP-5.2). The block and Beta storms have no published worked example with their parameters (KZGW
   2017 does not print the r and s of its Table 6.1): their status is `oracle only`, the exact integrals in rational
   arithmetic (and in closed form at 50 digits for α = 1/2) and their properties.

## Consequences

- The library refuses, with `validation_error` and the standard's reasons, what it accepted before: a negative depth
  of a gauge, a negative polygon or isohyet, a NaN depth, a storm of more than a million steps; IDW gives a finite
  estimate for every exponent.
- Results change only where the old code was not the formula: fractions of isohyets that miss one (within the 1e-3
  the function takes) are weighted by their sum (up to 0.1 %), and several gauges at the IDW point give their mean.
- Every result of a hyetograph or an areal precipitation records the `formula_version` of its spec in the envelope.
- `docs/FORMULAS.md` and `formulas/*.toml` list the eight specs; the handbook includes their blocks by name.

## Alternatives considered

- **The standard's reasons in the classes now:** the GUI's sentences and the network documents' errors of
  `not_multiple`, `total_mismatch`, `decreasing` and `not_covered` would change in this commit, apart from the
  renamed notice they belong with.
- **The PMAXTP lookup in `hydrolog._pmaxtp`'s own table:** it would import NumPy into the catalog's cold start.
- **The Beta case of KZGW (2017, Table 6.1) as a reference:** its r and s are not printed, and its shares at the ends
  of the hours do not follow its own eq. 2.20 (the last hour is not 0).
