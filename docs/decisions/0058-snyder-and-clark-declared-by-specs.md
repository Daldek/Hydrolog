# 0058. Snyder's and Clark's unit hydrographs declared by specs: two Snyder formulas, Clark's step a precondition, the ranges to be verified

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (specs, Nogat CMP),
  [ADR-0057](0057-the-unit-hydrographs-declared-by-specs.md) (the SCS unit hydrograph and the convolution),
  [ADR-0008](0008-routing-conventions.md) (the window of non-negative weights of the Muskingum scheme), the literature
  research of the unit hydrographs of 2026-11-18 (`unit-hydrographs.md`, its reference cases and verdicts)

## Context

Snyder's unit hydrograph kept its constants as literals: 0.275 and 0.556 in `runoff/snyder_uh.py`, again in
`reports/generator.py` and the report's section, and the widths' coefficients rounded to 0.1783 and 0.1019. Its area
range of 26–26,000 km² was credited to Snyder (1938) through Chow et al. (1988), neither open, and the range of Cp to
an unverified „0.56–0.69” of Snyder. The curve of its ordinates, the gamma curve of 1 mm through the peak (Hydrolog's
since 0.8.0), comes from no source of Snyder's method, which gives the peak, the widths and the time base.

Clark's unit hydrograph refused a time step above 2R with `unstable_timestep`, a reason of the routing commands, and
its typical R/tc of 0.2–1.5 with three classes was credited to the HEC-HMS Technical Reference Manual and „engineering
practice”: the manual gives no R/tc, and the Polish calibrations of the Stobnica (Wałęga and Cupak 2013) give
1.7–2.3. The hydrograph generator applied the 0.25 tp of NEH 630, a rule for the SCS unit hydrograph, to every model.

## Decision

1. **Two specs for Snyder.** `snyder` (`snyder_parameters`) declares what the sources give: tL, tD, tLR, tpR, qp, qpR,
   tb and the widths W50 and W75, in minutes, with 5.5 and 1/4 (HEC-HMS 2000 eqs. 30–31; KZGW 2017 eqs. 6.6, 6.8) and
   0.275 and 0.556 per mm (KZGW eqs. 6.7, 6.11; Chow's 2.75 and 5.56 per cm). `snyder_shape` (`snyder_shape`) declares
   the gamma curve of 1 mm through (tpR, qpR), K found by Brent's method in a bracket of 1e−12 to 1e12. The parameters
   have sources and a reference case; the curve has none and is `oracle only` (its volume identity of Asquith and
   Roussel 2007 and SciPy's gamma density): two formulas, two statuses and two `formula_version`s.
2. **The widths from 770 and 440, converted exactly.** W = Cw (qpR/A)^−1.08 from qpR, as Chow et al. (1988, after
   Rajagopalan's notes, p. 78) give it, with Snyder's 770 and 440 in ft³/s per mi² and in converted by the units table
   (1 / 2323.2 m³/s per km² and mm): 0.17829 and 0.10188, not Chow's SI values rounded to 2.14 and 1.22 per cm (0.2 and
   0.4 % lower) nor Hydrolog's four digits. `SnyderUH.width_at_percent` keeps the standard duration, where qpR = qp.
3. **Snyder's ranges from the sources one can open.** The area is 30–30,000 km², Snyder's 10–10,000 mi² as the open
   notes after Chow give them (p. 76), instead of 26–26,000 km² converted from the closed book; Ct 1.35–1.65 and Cp
   0.4–0.8 are KZGW 2017's (pp. 90–91; HEC-HMS 2000, p. 54, gives the same Cp). The unverified 0.56–0.69 is dropped.
4. **KZGW 2017 example 6.1 is the reference case of `snyder`, and its two slips are discrepancies.** Its printed tpR
   7.0 h and tb 23.0 h do not follow from its own printed terms (7.10 and 23.54 h); its design peak, 73.24 m³/s from a
   unit hydrograph of straight lines, is 6.9 % below the gamma curve's. Both are recorded as discrepancies of the
   cases, and the formulas follow the equations of both sources.
5. **Clark is one spec, `clark`, `oracle only`.** No source publishes a worked Clark example; the evidence is
   HEC-HMS's recursion with the mean of two outflows on the same grid (to 1e−12), HEC-HMS's own end at 0.995 of the
   volume (the peak within 0.5 %, the research case `clark-hec-hms-trm-oracle`), the volume of 1 mm and the scalings.
   The inputs are `(tc_min, r_min, area_km2, timestep_min, duration_min, total_duration_min)`: the step comes before
   the duration, so that the refusal of the instantaneous unit hydrograph (D = Δt) names the step.
6. **Clark's step is a precondition of the scheme.** Δt ≤ 2R keeps the weight (2R − Δt)/(2R + Δt) of the previous
   outflow non-negative (ADR-0008 with X = 0): `step_stable`, refused with `precondition_failed` instead of
   `unstable_timestep`, with 1e−9 of 2R allowed for rounding and the weights then taken at 2R. A precondition about one
   input names it in `details.option` through `hydrolog._formulas.CONSTRAINT_OPTIONS` (`clark.step_stable` →
   `timestep_min`, `snyder_shape.root_bracketed` → `peak_discharge_m3s`), so that the commands and the GUI keep the
   field: `uh snyder` and `hydrograph generate` map the latter to `cp` and `snyder_cp`.
7. **Ranges without a source are kept to be verified, not dropped.** Clark's R/tc of 0.2–1.5 and the 0.25 tp step of
   `nash`, `clark` and `snyder` stay as ranges with `verified` false and the notice `outside_unverified_range`, their
   source saying that none is published (for R/tc, that the Polish calibrations give 1.7–2.3); `scs` keeps NEH 630's
   step. They still warn of values far from practice and no longer claim a source; the classes of R/tc are gone.
8. **The wrappers check nothing and fill the defaults**, as `SCSUnitHydrograph` (ADR-0057): `SnyderUH` takes D = tD
   and ends the curve at 99.99 % of its volume, `ClarkIUH` takes T = tc + 5R (+ D) and warns of R/tc after the spec
   accepted R and tc. The report reads Snyder's numbers from the spec.

## Consequences

- Breaking: the refusals carry the standard's reasons (`outside_physical_range`, `precondition_failed` with
  `step_stable`, `root_bracketed`, `representable`, `length_bounded`); the constructors no longer refuse; Snyder's
  area notice comes outside 30–30,000 km², and R/tc and the step of three models give `outside_unverified_range`.
- The numbers stay those of 0.8.1 but the widths (−0.008 % and −0.02 %) and the last digits of Clark's sums; Clark's
  S-curve of a D much shorter than the step keeps its digits.
- `formula_versions` gain `snyder`, `snyder_shape` and `clark`, each 1.
- Open: a published source for R/tc and for the step of the Nash, Clark and Snyder unit hydrographs; Snyder's L taken
  from the channel in the GUI rather than the flow path to the divide (research #16); whether a discrepancy case may
  name an output its spec lacks (KZGW's design peak on `snyder_shape`).
