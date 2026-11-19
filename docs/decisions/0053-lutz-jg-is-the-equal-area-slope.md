# 0053. Lutz's Jg is the equal-area slope of the main stream's profile: `flow_path_equal_area_slope_m_per_m` and `equal_area_slope`

- Status: accepted
- Date: 2026-11-19
- Amends: [ADR-0024](0024-nash-by-lutz-from-the-watershed.md) (point 2: Lutz's J is no longer
  `flow_path_slope_m_per_m`; point 3: the missing field and the refusal of a zero slope)
- Builds on: TRIAGE T3 of the literature research of the formulas of 2026-11-18,
  [ADR-0019](0019-tc-from-the-inputs-its-source-defines.md) (each method takes the inputs its source defines, no
  substitutes) and [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs)

## Context

ADR-0024 fed Lutz's J with `flow_path_slope_m_per_m`, the elevation of the head of the longest flow path minus the
outlet's, over its length, and called it "the mean slope". KZGW (2017, annex 2, p. 97, the legend of eq. 6.17) defines
Lutz's Jg otherwise: "uśredniony spadek cieku głównego, wyznaczony jako spadek prostej, wychodzącej z najniższego punktu
profilu podłużnego cieku, przy którym powierzchnie ograniczone tą prostą i linią terenu, położone poniżej i powyżej tej
prostej, są sobie równe" — the equal-area slope of the main stream's longitudinal profile, Lutz's "gewogenes Gefälle".
New Zealand's TM61 (Ministry of Works and Development 1980, appendix A, pp. 12–13) draws the same line AC through the
outlet and gives Sa = 2Ad/L², Ad the area under the profile above the outlet; Barbosa Jr. (UFOP notes, eqs. 17–18)
sums that area by trapezoids. On a concave profile, as streams are, the slope between the ends is larger: Kamiennik
at Świerzawa, Hydrograf's flow path of 2026-11-05 (15.88 km, 440.16 → 258.72 m, 1,593 points of the filled DEM in
`tests/fixtures/kamiennik_flow_path_profile.json`), has 0.0114 between its ends and 0.0084766 by equal areas (0.742 of
it), and tp ∝ Jg^−0.39 grows by 12 %. Hydrolog had neither the field nor a function for it, and Hydrograf measures the
path but not the area of its profile.

## Decision

1. **The formula `equal_area_slope`** (`hydrolog.morphometry.equal_area_slope(distance_m, elevation_m)`, spec
   `EQUAL_AREA_SLOPE` of `hydrolog.morphometry.profile`, `formula_version` 1, status `oracle only`): S = 2A/L² of a
   profile ordered from the outlet upstream, A the trapezoid sum of z − z[0], L the last distance minus the first. The
   line passes through the first point, the outlet (TM61; KZGW's lowest point, which the outlet of a flow path on a
   filled DEM is), so a stretch below the outlet counts as area below the line. Refused: arrays of different lengths
   and a distance that steps back (`outside_physical_range`), and a profile without positive area or length, or beyond
   float64 (`precondition_failed`, constraint `positive_area`). The profile is divided by powers of two before it is
   summed, so the declared homogeneity in the units of both axes holds exactly. No open source publishes a profile with
   its slope, so the evidence is two oracles: the exact rational 2A/L² and the sources' construction by bisection, both
   also on the Kamiennik profile, besides the generated range, type and property tests.
2. **The field `flow_path_equal_area_slope_m_per_m`** of `WatershedParameters` (optional, appended, > 0 with
   `exclusive_minimum`), of the `watershed` of `hydrolog-network/1` (the schema regenerated; `/1` kept, the field being
   optional, AGI-4.1), of the report's watershed table and of `hydrolog.testing.watershed` (left out by default: Lutz
   also needs `Lc_km` and `manning_n`, which the builder does not give).
3. **Lutz reads it** (`hydrolog._ranges.NASH_INPUTS["lutz"]["slope"]`): a watershed without it is `missing_field`
   (`details.option` the field in the order L, Lc, Jg, n_M; `details.method` `lutz`; the hint names
   `equal_area_slope`), **also when it has the end-point slope**. The end-point slope is another quantity (ADR-0019's
   rule) whose error depends on the shape of the profile: on a concave profile it overestimates Jg and so the peak, on a
   convex one it underestimates them, so a notice could not state the error and the result would not be Lutz's.
   Kirpich and Kerby-Kirpich keep `flow_path_slope_m_per_m`, which their sources define (Fang et al. 2005, eq. 3.14).
4. **What Hydrograf computes and passes:** on the D8 path of the filled DEM that it reports as `flow_path_length_km`
   (from the basin cell of greatest flow distance down to the path's end cell, whose flow distance is the baseline of
   `hydraulic_length_km`), the profile from that end cell upstream: x the flow distance minus the end cell's [m], z the
   filled-DEM elevation [m]; `equal_area_slope(x, z)` or the same trapezoid sum, sent as
   `flow_path_equal_area_slope_m_per_m`. Over a graph of catchments the trapezoid integrals of z and the lengths add
   over consecutive pieces of the path, so S = 2(Σ∫z dx − z_outlet L)/L². A profile without positive area gets no
   value. Kamiennik's hand-off would carry 0.00848.
5. **`uh nash`** computes as before from the J it is given; its option `lutz_slope_m_per_m` now says that J is the
   equal-area slope.

## Consequences

- **Breaking:** Nash by Lutz from a watershed without the field (`hydrograph generate` and `report generate` with
  `nash_estimation` `lutz`, the `curve-number` runoff of `route network`) is refused with `missing_field`, every
  Hydrograf hand-off included until Hydrograf sends it; a zero slope is refused when the watershed is read
  (`exclusive_minimum` on the field) instead of by `nash_parameters`.
- **Results change where the profile is not straight:** the guide's Kamiennik (PMAXTP 101.82 mm, 12 h, Beta, Δt 10 min,
  AMC II; Jg 0.0114 → 0.00848): n 3.610 → 3.587, K 92.13 → 104.30 min, peak 35.03 → 32.17 m³/s at 9:10 → 9:40 h; the
  volume (977 067 m³) does not change. The catalog's example of `hydrograph generate` with Lutz takes 0.0185 for its
  flow path of 0.025 between its ends: 22.171 → 19.638 m³/s.
- An older Hydrolog refuses a watershed with the field (`unknown_field`).

## Alternatives considered

- **Accept the end-point slope with a notice:** a substitute whose error has no stated size or sign (above).
- **Profiles in the watershed, Jg computed by Hydrolog:** arrays of thousands of points in every document; Hydrograf
  has the rasters and can call `equal_area_slope`.
- **The line from the lowest point of the profile** (KZGW's words) instead of the outlet: the same on a filled DEM;
  the outlet keeps the slope defined for a surveyed bed with pools below its outlet, as TM61 draws it.
- **Another mean slope** (85–10, Taylor–Schwarz): not Lutz's definition.
