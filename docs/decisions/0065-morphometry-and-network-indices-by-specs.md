# 0065. The morphometric and river-network indices declared by specs: shape, relief, hypsometry, Strahler and Horton

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs), the literature research of
  the formulas of 2026-11-18 (`morphometry-soil`, TRIAGE T15, T16, T18) and Nogat's plan of the computation standard,
  step 5

## Context

The research of 2026-11-18 found the lemniscate ratio without its π (T15), Horton's ratios counted over links instead
of Strahler streams (T16) and a hypsometric integral that returned NaN for a flat or gapped surface (T18); `develop`
fixed all three. The formulas still checked their inputs by hand or not at all: `WatershedGeometry` refused only
non-positive values (a NaN computed NaN), the helpers of `network.stream_order` raised messages without the standard's
`details.reason`, the relief ratio converted kilometres by a literal and no formula of the family recorded a
`formula_version`. No open source prints a worked example of the shape indices or of Horton's ratios with its inputs
(the Polish journals were out of reach; Baścik 2006 prints the slopes of two rivers and Strahler's rule).

## Decision

1. **Specs, `formula_version` 1.** Shape indicators in `hydrolog.morphometry.geometric` (new module functions of the
   names of the specs; `WatershedGeometry` and its methods compute through them): `form_factor` A/L²,
   `compactness_coefficient` P/(2√(πA)), `circularity_ratio` 4πA/P², `elongation_ratio` (2/L)√(A/π) and
   `lemniscate_ratio` πL²/(4A). `relief_ratio` (H_max − H_min)/L in m/m (`hydrolog.morphometry.terrain`), through
   which `TerrainAnalysis` gives the relief ratio, the watershed slope and the channel slope. `hypsometric_integral`
   (`hydrolog.morphometry.hypsometry.hypsometric_integral(elevations_m, cell_areas, n_points)`), through which
   `HypsometricCurve` computes. `strahler_order`, `bifurcation_ratio`, `length_ratio` (new),
   `drainage_density` and `stream_frequency` (`hydrolog.network.stream_order`), through which
   `StreamNetwork.get_statistics` computes. Tier B rows: the mean width A/L, the midpoint elevation (H_min + H_max)/2,
   the hypsometric curve, the area-weighted mean elevation, the elevation above a share of the area and the
   streams of each order with their lengths.
2. **Physical constraints the geometry implies.** A watershed lies within the circle of radius L about its outlet
   whether L is the straight line to the farthest point of the divide or the longest flow path, which is not shorter:
   A ≤ πL² (`within_reach`), so Cf ≤ π, Ce ≤ 2 and k ≥ 1/4. No perimeter is shorter than the circle's of the same
   area: P² ≥ 4πA (`isoperimetric`), so Cz ≥ 1 and Ck ≤ 1. A watershed rises above its outlet: H_max > H_min
   (`rises_above_outlet`). Every stream of order u + 1 begins where at least two streams of order u end, and a stream
   ends once, so N_u ≥ 2N_(u+1) and Rb ≥ 2 (`two_streams_per_junction`, Baścik 2006, p. 28): the counts of links that
   T16 found give Rb below 2 and are refused. An index whose value lies beyond float64 is `precondition_failed`
   (`within_float64`). Each is refused with the standard's `details`.
3. **Evidence.** `relief_ratio` and `strahler_order` are `referenced` (Baścik 2006: the Racławka, 9.1 ‰, and the Raba,
   4.6 ‰; Strahler's rule, p. 28, with Rai et al. 2014 as the second source). The others are `oracle only`: the
   equations in decimal arithmetic at 50 digits with π summed by the decimal module's series, the exact values of a
   circle, a square and a semicircle, the identities Ck·Cz² = 1, Cf = πCe²/4, k·Cf = π/4 and k·Ce² = 1, exact rational
   quotients, the exact rational trapezoid of the hypsometric curve, and for the counts of streams another algorithm
   (connected runs of links of one order) on random networks. Reference cases are
   `tests/fixtures/formulas/morphometry-cases.json`; the tests are `tests/unit/test_formulas_{shape,relief,hypsometry,
   network}.py`.
4. **The trapezoid stays.** The hypsometric integral remains the trapezoid of the curve at n points (101 by default),
   as Hydrolog computed it. Its departure from the exact integral of the cells' step curve, (mean − min)/(max − min)
   (Pike and Wilson 1971), is at most (a(0) − a(1))/(2(n − 1)) ≤ 0.005 at 101 points, most where much of the area lies
   at the outlet's elevation (nine cells at 100 m and one at 200 m: 0.1045 instead of 0.1). Whether to compute the
   exact value instead is the author's question (below); the spec states both, and the oracle checks the bound.
5. **Strahler's stages** (about 0.60 and above inequilibrium, 0.35–0.60 equilibrium, below 0.35 the monadnock phase;
   Strahler 1952, text with Fig. 7) are a convention of the spec, not a classification Hydrolog returns.

## Consequences

- **Breaking:** inputs the specs refuse are refused with `validation_error` and the standard's `details.reason`,
  `details.formula`, `details.option` or `details.constraint`, also by `WatershedGeometry(...)`,
  `TerrainAnalysis(...)`, `morphometry watershed` and `network stats`: NaN and infinities (computed into NaN before),
  booleans and strings, A > πL², P² < 4πA, N_u < 2N_(u+1), non-whole counts. `drainage_density` accepts a length of 0.
  Values inside the ranges compute as before within a few units in the last place: each index now divides in an order
  that cannot overflow or underflow where its result does not (A/L/L, 2√A/√π/L, 4π(A/P)/P, (π/4)(L/A)L).
- Results of these commands carry `formula_versions` (CMP-2.8).
- Hydrograf hands its longest flow path as `length_km` and takes A from cells and P from a smoothed boundary: its
  watersheds satisfy both constraints by geometry and by the margins of real shapes (Cz ≥ 1.43 in the recorded
  hand-offs); a hand-off that does not is refused rather than given Cz < 1.

## Open questions

- The exact hypsometric integral (mean − min)/(max − min) instead of the trapezoid (changes HI by up to 0.005 at 101
  points).
- The convention of L across the ecosystem: the straight line (Schumm, Baścik), the valley length L_m (Baścik) or the
  longest flow path (Hydrograf's hand-off).

## Alternatives considered

- **Output ranges without the geometric constraints** (Cf, Ce, k unbounded; Cz, Ck any positive): every impossible
  watershed would compute, and CMP-3.4 needs a constraint that prevents an index outside its range.
- **Counts of streams as integer inputs of `bifurcation_ratio`:** the reference module scales real inputs only, so the
  homogeneity of the ratio could not be tested; whole numbers are a physical constraint of a real input instead.
