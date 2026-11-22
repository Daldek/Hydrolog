# 0042. The Euler type II storm from a depth-duration curve

- Status: accepted
- Date: 2026-11-18
- Builds on: the audit of the formulas of 2026-11-18 (Nogat CMP-9.1; the gross defect T34, fixed at once under
  CMP-9.2) and the author's decisions of 2026-11-18: the increments in the order of their durations, linear in ln D
  between the points of the curve, no `peak_position`, `hydrolog-network/1` kept, `beta` as the default of
  `hydrolog.testing`, no release now
- Amends: [ADR-0011](0011-public-testing-module.md) (the default shape of `design_storm`, `hietogram_envelope` and
  `write_hietogram_envelope` is `beta`), [ADR-0012](0012-network-objects-rainfall-and-runoff.md) (a design rainfall
  reads the arguments its shape requires; an old `euler_ii` rainfall without a curve is refused although the schema
  stays `/1`), [ADR-0018](0018-pmaxtp-through-obserwator.md) (`precip pmaxtp` also returns the depths of every
  duration at the probability, and the GUI keeps them with its fetch)

## Context

`EulerIIHietogram`, the `euler_ii` of `precip hietogram`, `hydrograph generate`, `report generate`, `DesignStorm` and
`route network`, presented itself as the DVWK Euler type II storm. It took the total only and gave the block of rank
r the share `r^-0.7 / Σ k^-0.7`, placed alternately left and right of the block `max(2, floor(n p) + 1)` with
`peak_position` p = 0.33. The shares were the same for every place, probability and duration (for 12 blocks the peak
was always 23.08 % of the total), so the storm ignored the local depth-duration curve, the one input that makes an
Euler type II storm.

The audit of 2026-11-18 (Nogat, research `hyetographs.md`, section 2) found the peak 23 to 66 % below every published
Euler type II storm: DWD's 60-min storms (Malitz 2009, 10.4 mm in the peak block, the code 6.138 mm), the itwh
printouts of KOSTRA-DWD (Göllheim, 9.51 mm, the code 7.303, 6.438 and 5.746 mm at 30, 60 and 90 min; Aurich, 9 h,
11.00 mm against 3.771 mm, in block 36 instead of 33), the Wrocław monograph (Kaźmierczak and Kotowski 2012,
101.71 mm/h against 65.51 mm/h) and an Euler type II of PMAXTP (Warsaw and Kamiennik, 60 min, 49 to 59 % below
h(5)). The 15 min around the peak were short of the 15-min design depth (Warsaw, p = 1 %: 18.79 mm against 28.22 mm).

The storm is defined by ATV-DVWK-A 118 (Kap. 5.2.2.1 as quoted by Thewes 2005, p. 10; DWD, Malitz 2009, slide 17;
Kaźmierczak and Kotowski 2012, pp. 31–32): from the depth-duration curve h(D) of one probability take the increments
of the steps Δt; the largest goes to the interval that starts at 0.3·D rounded down to a multiple of 5 min, the next
larger ones fill the time before it back to t = 0 and the rest follow it. Every duration around the peak then holds
its design depth. The audit left the open points to the author: the order of the increments where a coarse table,
interpolated, makes them grow; the interpolation between the points of a table (PMAXTP has 5, 10, 15, 30, 45, 60, 90,
120 ... min); what becomes of `peak_position`, of the network documents that hold `euler_ii`, and of the default
shape of `hydrolog.testing`.

## Decision

1. **The storm is built from a depth-duration curve.** `EulerIIHietogram(depth_duration_mm)` takes the depths [mm]
   of one probability by duration [min] (a mapping; a key may be the text of a number, as in a JSON object). With
   `n = D / Δt`, `Δh_j = h(jΔt) − h((j−1)Δt)` and the peak block `k = floor(0.3 n)` (counted from 0: the interval
   from 0.3·D rounded down to a multiple of the step), the peak holds Δh_1, the blocks before it Δh_2 .. Δh_(k+1)
   back to t = 0 and the blocks after it the rest, **in the order of their durations**. For a curve whose increments
   decrease this is the arrangement of A 118 and DWD (the largest at the peak, the next ones before it, the rest after
   it). Where interpolation makes an increment grow they are not sorted, so that the m blocks that end with the peak
   always hold h(mΔt): sorted, the PMAXTP storm of Kamiennik at p = 50 % would put 15.14 mm into the 30 min that end
   with the peak instead of h(30) = 15.01 mm; the itwh software places its increments by duration too (Aurich, 2020).
2. **Linear in ln D between the points, nothing extrapolated.** It reproduces the itwh KOSTRA-DWD 2010R printouts of
   Göllheim to 0.07 mm, where linear interpolation in D misses by 0.16 mm. The curve must reach from the step to the
   duration (`not_covered`), so with PMAXTP the step is at least 5 min.
3. **The total is h(D).** `precip hietogram`, `hydrograph generate` and `report generate` take `total_mm` as optional
   for `euler_ii`; a total given must equal h(D) to 0.005 mm, half of the 0.01 mm the PMAXTP tables print
   (`validation_error`, `details.reason` `total_mismatch` with `depth_mm`). `generate(total_mm, duration_min,
   timestep_min)` keeps the signature of every hyetograph and refuses another total in the same way; `depth_mm(D)`
   gives h(D). A network document still requires `total_mm` and must give h(D); another total is refused when the
   network is routed, with the node.
4. **The peak is not a parameter.** `peak_position` is removed from `EulerIIHietogram` and refused with `euler_ii`
   (`not_applicable` in the commands, `unknown_field` in a network document); it remains the parameter of
   `triangular`. The result's `parameters` of `euler_ii` is `{"peak_start_min"}`. The rule rounds down to a multiple
   of the step (for Δt = 5 min A 118's "Vielfaches von 5 Minuten"); D must be a whole number of steps (`not_multiple`),
   since an Euler storm is made of whole blocks.
5. **The commands take the curve.** `precip hietogram`, `hydrograph generate` and `report generate` gain
   `depth_duration_mm` (an object) and `depth_duration_file` (a CSV `duration_min,depth_mm`, or JSON: such an object,
   a table, or the envelope or result of `precip pmaxtp --json`, whose `attribution` and `terms_notice` the result
   carries); exactly one is required for `euler_ii` and neither applies to another shape. `precip hietogram` can now
   also end with `not_found` and `data_error` (the file). A curve that cannot be used is a `validation_error` on
   `depth_duration_mm` (or `depth_duration_file`) with `details.reason` `type`, `empty`, `invalid_duration`,
   `duplicate_duration`, `not_finite`, `minimum`, `decreasing` (the two `durations_min` and their `depths_mm`) or
   `not_covered`.
6. **PMAXTP gives the curve.** The result of `precip pmaxtp` gains `depth_duration_mm`, the depths of its 16
   durations at the asked probability and method, an optional field of `hydrolog-precip-pmaxtp/1` (its version
   stays). No other command fetches anything: `precip pmaxtp` stays the only one that uses the network (ADR-0018).
7. **`hydrolog-network/1` stays `/1`.** A design rainfall gains `depth_duration_mm`, the curve of `euler_ii`, and
   reads every argument its shape requires (`missing_field`, `details.field` `rainfall.depth_duration_mm`). This is
   an exception to ADR-0012's "an old document is read and answered as before": an old `euler_ii` rainfall, without a
   curve, is refused instead of being answered with the wrong storm, and the refusal names the field to add. The
   schema's other documents are unchanged.
8. **`hydrolog.testing` defaults to `beta`.** `design_storm`, `hietogram_envelope` and `write_hietogram_envelope`
   default to `hietogram_type` `beta` (α 2, β 5), since an Euler II needs a curve the caller must choose; they accept
   `depth_duration_mm`, and an envelope's `total_mm` may be `None` (an Euler II's total is h(D)).
   `example_network_document()` gives node A Beta (2; 5), 45 mm in 60 min, and the guide's network of the GUI
   (`przyklady/siec.json`, made from it) follows.
9. **The GUI.** In Hydrogram zlewni and Sieć Euler II comes with PMAXTP: the fetch keeps the curve of its
   probability and method with the depth, and a run sends both, without `peak_position`; a fetch kept without the
   curve (an older session or hand-off) is fetched again when Euler II is chosen. Under „Hietogram” (a total typed by
   hand) Euler II is not offered, and a kept one is refused with the reason and „Przełącz na PMAXTP”; a document or
   hand-off that carries a curve keeps it. The info text, the guide and the report („Deszcz Eulera typu II
   (ATV-DVWK-A 118)”) describe the storm as built.
10. **No release now.** The author decided not to release with this fix: the CHANGELOG entries are under
    `[Unreleased]` and the version is not changed.

## Consequences

- Breaking for every caller of `euler_ii`: `EulerIIHietogram()` and `EulerIIHietogram(peak_position=...)` fail
  (`TypeError`), `--hietogram-type euler_ii` without a curve is a `validation_error` (`required`), `peak_position`
  with it is refused, and a network document whose `euler_ii` has no curve is refused. The migration is to give the
  curve of the storm's probability: `depth_duration_mm` (in Python the mapping), `depth_duration_file`, or the
  `depth_duration_mm` (or the whole `--json` output) of `precip pmaxtp`.
- Results change: the peak block of a storm is 1.3 to 2.9 times the old one in the published cases (the old was 23 to
  66 % below them), 2.0 to 2.4 times for PMAXTP at 60 min (h(5)). The peak of a hydrograph made from it rises where
  the catchment answers within the storm and hardly changes where it does not: for the PMAXTP storm of Warsaw (p = 1 %,
  60 min, 39.16 mm; SCS, CN 80, 5 km²) by 120, 47 and 15 % for tc 10, 20 and 30 min and by less than 3 % (down) for
  tc 60 to 180 min; the volume of the same total is unchanged. Every hydrograph, report and network result made with
  `euler_ii` up to 0.8.1 is to be computed again with the curve of its probability.
- Other projects call the class or the commands: Hydrograf (`hietogram_type=euler_ii`, "DVWK (Euler II)") and
  Hydraulik (`rainfall build --hietogram-type euler_ii`, its recorded `hietogram_euler_ii.json`, the default of
  `hietogram_envelope()`). Each needs the curve or another shape; that is a `request` issue in its repository
  (DEV-17.5), not a change made here.
- The peak position follows A 118 also where a source differs by a block (the itwh software's 15-min storm, the
  Wrocław monograph's D/3 beyond 150 min); the interpolation between PMAXTP's points and the use of its 5- and 10-min
  depths in model rains remain open questions (`docs/PROGRESS.md`).

## Alternatives considered

- **Sort the increments**, the wording of most descriptions: equal to the decision whenever the increments decrease,
  but where interpolation makes them grow the windows around the peak lose their design depths (the Kamiennik case
  above), and itwh does not sort either.
- **Interpolate linearly in D** (the DWA's KOSTRA tool), **in log–log** (HEC-HMS's frequency storm) **or by a power
  law** (PMAXTP's own smoothing): linear in D misses the itwh printouts by 0.16 mm; no Polish rule for the gaps of
  PMAXTP was found, and ln D reproduces the one printout that shows its inputs.
- **Keep the old shape under another name** (an alternating-block storm with `r^-0.7` weights): no source defines
  it, and `euler_ii` promises the storm of A 118.
- **Keep `peak_position`**: A 118 fixes the peak; a storm with the peak elsewhere is not an Euler type II storm.
- **Scale the curve to a total that differs from h(D)**: the storm of one probability holds h(D); another total is
  another probability, so the curve is to be scaled by whoever chose that total.
- **`hydrolog-network/2`**: the new field is additive and the only documents refused are those whose storm was wrong;
  a new version would make every reader and writer of the network move for one shape.
- **The alternating-block method** (Chow, Maidment and Mays 1988, §14.4; HEC-HMS's frequency storm) under
  `euler_ii`: a different arrangement, not Euler type II; it could come later as a shape of its own.
