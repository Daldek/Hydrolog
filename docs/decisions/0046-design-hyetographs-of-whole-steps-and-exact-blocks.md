# 0046. Design hyetographs of whole steps and exact blocks

- Status: accepted
- Date: 2026-11-18
- Builds on: the audit of the formulas of 2026-11-18 (Nogat CMP-7, research `hyetographs.md` sections 1, 4, 5, 6
  and 9; TRIAGE T35, T6 and the Hydrolog part of T26) and [ADR-0042](0042-the-euler-type-ii-storm-from-a-depth-duration-curve.md),
  whose Euler type II storm already refused a duration that is not a whole number of steps
- Amends: [ADR-0012](0012-network-objects-rainfall-and-runoff.md) (a design storm of a network is cut into whole
  steps of the network, and the notice `duration_not_covered` of a node is gone), [ADR-0015](0015-catalog-additions-for-the-gui.md)
  (the list of routing notices without `duration_not_covered`)

## Context

Every hyetograph generator cut the storm into `n = int(D / Δt)` steps and put the whole total into them. When the
duration D was not a multiple of the step Δt the storm was shorter than D and its mean intensity higher by
D/(nΔt): the PMAXTP depth of Warsaw for 45 min (36.58 mm) in steps of 10 min fell in 40 min, 12.5 % above the mean
intensity of that probability (`DesignStorm` of a network: 30 mm of 50 min in steps of 20 min, +25 %). A notice
(`duration_not_covered`) said what was covered, but the storm was no longer the design storm of its duration and
probability, and `int()` of a binary-inexact ratio lost a step (`int(0.3 / 0.1) = 2`). The Euler type II storm of
ADR-0042 already refused such a duration (`not_multiple`).

The triangular hyetograph weighted the steps by the triangle sampled at their ends, with zeros at t = 0 and
t = (n+1)Δt and the peak step clipped to 2..n; for 3 steps the weights were 1/2, 1, 1/2 whatever the peak position.
Chow, Maidment and Mays (1988, sec. 14.3, eqs. 14.3.1–14.3.3, after Yen and Chow 1980) define the continuous
triangle of base D, height 2P/D and peak at r·D; its Example 14.3.1 (Urbana, 15 min, 27.178 mm, r = 0.38) in steps of
5 min holds 7.947, 14.361 and 4.871 mm, where the code gave 6.79, 13.59 and 6.79 mm.

The Beta hyetograph weighted the steps by the Beta density at their midpoints and fell back silently to a uniform
storm when every weight was zero or not finite (NaN or infinite α, β; α = β ≥ ~535). The midpoint rule
under-integrates a density that is infinite at an end: for α = 0.5, β = 5 and 12 steps the first step held 0.5445 of
the total against 0.6372 of the exact block integral (the case `beta-kzgw2017-eq2.20-a0.5-b5-n12-oracle`). The Polish
source of the shape, KZGW (2017, ch. II.3, eqs. 2.20–2.22, after Węglarczyk 1993), evaluates the density at the ends
of the intervals, which shifts the storm by half a step (33 % of the peak for (2, 5) and 12 steps).

NaN and infinite totals, durations, steps and shape parameters passed the checks of the library (`NaN <= 0` is
False) and gave NaN depths or a uniform storm through the Python API; the CLI refused them (CMP-3).

## Decision

1. **A hyetograph is made of whole steps.** Every generator (`BlockHietogram`, `TriangularHietogram`,
   `BetaHietogram`, `EulerIIHietogram`) takes `n = round(D / Δt)` and refuses a duration that differs from n·Δt by
   more than 1e-9 of D: `validation_error`, `details.option` `duration_min`, `details.reason` `not_multiple`,
   `details.timestep_min`, as Euler II did. The storm then lasts D and holds the total. The notice
   `duration_not_covered` is removed from the registry, `precip hietogram`, `hydrograph generate`, `report
   generate`, `route network` and the GUI. `DesignStorm` cut at the step of a network follows the same rule; the
   refusal carries the node (`details.node_id`).
2. **The triangular hyetograph is the block integral of the triangle of Yen and Chow.** The cumulative share is
   `F(u) = u²/r` for `u ≤ r` and `1 − (1 − u)²/(1 − r)` for `u > r` (u = t/D, r = `peak_position`), and step j holds
   `P [F(j/n) − F((j−1)/n)]`. `peak_position` keeps its name and range (0 < r < 1): it is the time of the peak, no
   longer the step of the peak.
3. **The Beta hyetograph is the block integral of the Beta density.** Step i holds
   `P [I_(i/n)(α, β) − I_((i−1)/n)(α, β)]`, with I the regularised incomplete Beta function (`scipy.special.betainc`).
   The steps hold P for every finite α, β > 0, so there is no fallback.
4. **Values that are not finite are refused where they enter.** The generators refuse a total, duration, step,
   α, β or `peak_position` that is not a finite number (`details.reason` `not_finite`, or `type` for a bool or a
   text) with `details.option` naming it; `peak_position` outside (0, 1) is `exclusive_minimum` or
   `exclusive_maximum`, and the catalog declares `exclusive_maximum` 1. In a network document such an error of a
   shape's argument keeps the shape's reason and adds `details.field` (it was `invalid_value`).
5. **Texts follow the sources.** IMGW-PIB recommends POT for p ≥ 50 % and treats AMP and POT as equivalent below
   (Ozga-Zieliński (Ed.) 2022, p. 23), not "POT, the recommended method"; PMAXTP is not PMP. The Beta hyetograph cites
   KZGW (2017) after Węglarczyk (1993), not Chow et al. (1988) or Wachulec et al. (2016), and drops the unsourced
   "convective storm"; the triangle cites Yen and Chow (1980) through Chow et al. (1988). The isohyet method states
   how the edge zones are represented (Chow et al. 1988, Fig. 3.4.3c: bounds 0 and 56 mm for the estimated means 5 and
   53 mm, 27.9 mm).

## Consequences

- Breaking: a duration that is not a whole number of steps is refused instead of being answered with a shorter,
  more intense storm and a notice; a network whose design storm is not a whole number of its steps is refused with
  the node. The migration is to choose a step that divides the duration (10 min for 12 h).
- Results change. The triangle: 12 steps with r = 0.5, the peak −0.7 % and the steps by up to 14 % of the peak;
  6 steps up to 23 %; 3 steps with r = 0.38, the peak +5.7 %. Beta (2, 5): 12 steps, the steps by up to 2.0 % of the
  peak (the peak +0.003 %), 6 steps 5.5 %, 144 steps 0.02 %; α < 1 or β < 1 by more (α = 0.5, β = 5, 12 steps: the first
  step +17 %). The hand-off example of Nogat (Beta (2, 5), 105 mm in 720 min) peaks at 57.8773 m³/s instead of
  57.8786 m³/s; Hydrolog's copy of `handoff-1.schema.json` records the new value until Nogat's own does.
- `Hietogram._validate_params` keeps its signature and returns the number of steps: a shape added to `HIETOGRAMS`
  that calls it gets the new checks.
- Other projects: Hydrograf (`hietogram_type` beta, triangular, block, and its durations and steps), Hydraulik
  (`rainfall build`, `generate_hyetograph`, whose docstring promises the shortened duration, and its recorded rain
  fixtures of these shapes) and Retman, if it builds design storms through Hydrolog, must give durations that are
  whole numbers of steps and expect the new depths; that is a `request` issue in each repository (DEV-17.5).

## Alternatives considered

- **A partial last step** (n = ceil(D/Δt) with a short last step): a hyetograph has one time step
  (`HietogramResult.timestep_min`, `intensity_mm_per_h` = depth·60/Δt), the unit hydrograph is convolved at that step,
  and Hydraulik's rain tables require regular times; a short step breaks all of them.
- **Keep the whole steps and the notice**: the storm is not the design storm of its duration and probability
  (+12.5 % mean intensity in the audit's case), and the notice does not make it one.
- **Stretch the depth over n·Δt or pad to ceil(D/Δt) with zeros**: the first changes the duration, the second the
  intensity of the last step; neither is a source's rule.
- **The end-point rule of KZGW (2017) for Beta**, the one Polish source: it shifts the storm by half a step and
  its first step is 0 for α > 1; the block integrals are exact for every step and agree with the density as the
  step shrinks.
- **The midpoint rule kept as a documented deviation**: exact integrals cost nothing and remove the dependence
  on where in the step the density is read.
