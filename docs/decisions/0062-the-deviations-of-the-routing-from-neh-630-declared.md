# 0062. The deviations of the routing from NEH 630 and HEC-HMS, declared in the specs

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0061](0061-the-routing-formulas-by-specs.md) (the routing formulas by specs),
  [ADR-0008](0008-routing-conventions.md) (routing conventions), [ADR-0026](0026-a-reach-without-a-muskingum-cunge-grid.md)
  (a reach without a Muskingum-Cunge grid), Nogat's computation standard (CMP-2.3 conventions, CMP-3.4, CMP-5.2) and the
  literature research of the routing formulas of 2026-11-18 (`ct-research/routing.md`, sections F3, F5, F7 and 12)

## Context

The research found no defect in the routing numerics, but six places where Hydrolog chose otherwise than the source of
the method, each documented in ADR-0008, ADR-0026 or `docs/COMPUTATION_PATHS.md` and none labelled in a spec: NEH 630
accepts negative Muskingum-Cunge weights (example 17-5 has C1 = −0.187), takes a reference discharge per distance step
(WinTR-20), uses a discharge-weighted log-log slope `m` for the celerity of a rating table, re-interpolates a fast rise
to exactly 10 intervals, states the step rule of storage indication on the whole working curve, and lets a flood leave
the table to WinTR-20's own extrapolation; HEC-HMS's lag takes the current inflow before the lag has passed. Two of the
reference cases (NEH examples 17-4 from the section and 17-5) differ by those choices, not by an error. The standard
asks a spec to state its conventions (CMP-2.3), a difference a case shares with a second source to be a recorded
discrepancy (CMP-5.2), and no `calculation_error` for accepted inputs (CMP-3.4).

## Decision

1. **Each deviation is a convention of its spec or a Tier B row, with the source it departs from:**
   - `muskingum_cunge`: only grids whose weights are not negative (precondition `nonnegative_weights`, the window
     `|c dt − D| <= dx <= c dt + D`); one reference discharge for all distance steps; the coefficients constant.
   - `manning_normal_flow`: the celerity is the local `dQ/dA` of the section (HEC-HMS TRM, Muskingum-Cunge eq. 4),
     not NEH's discharge-weighted `m` of a table (eqs. 17-29, 17-30a): 2.0 % lower on example 17-4.
   - `muskingum_cunge_rise` (Tier B): a rise shorter than 10 steps divides each step into `ceil(10 / rise)` whole
     sub-steps and keeps the original ordinates, where NEH re-interpolates to exactly 10 intervals.
   - `level_pool` and `level_pool_substeps` (Tier B): the step rule `dt <= 2 min(ΔS/ΔO) / N` on every segment the run
     reaches, stricter than NEH's `dt <= 2 S/O` on the whole curve (p. 17-11), which lets a step through on a table
     whose slope changes sharply; a flood that leaves the table is a failed precondition of the formula
     (`flood_below_table_top`, `flood_above_table_bottom`, whose checks run the recurrence) and the reach's
     `calculation_error` `table_exceeded` or `table_emptied`, never an extrapolation.
   - `lag`: before the first ordinate the inflow is the initial outflow (the steady state of ADR-0008), where HEC-HMS
     TRM's lag model writes `O_t = I_t` for `t < lag`.
2. **The cases that differ by design are recorded discrepancies,** skipped with their cause and second source: NEH
   example 17-4 from the section (celerity −2.0 %, peak −0.26 %) and example 17-5 (Hydrolog routes 2,600 ft in one
   step of non-negative weights: peak 2,867.6 ft³/s against NEH's 2,828.99 and HEC-RAS's unsteady 2,902). Example 17-4
   with the printed celerity, where the choices coincide, passes.
3. **Nothing changes for now;** the choices that would change results are the author's questions (below).

## Consequences

- `docs/FORMULAS.md` shows each deviation beside the equation it qualifies, and the cards carry them.
- Results stay as they were; a later change of any choice is a new `formula_version` of its spec.

## Alternatives considered

- **Following NEH 630 to the letter** (negative weights, a reference per step, the weighted `m`, exactly 10 intervals,
  the whole-curve rule): negative weights give negative or oscillating outflows (CMP-3.4), a reference per step makes
  the scheme non-linear in the inflow and dependent on the extension of the series, and the whole-curve rule lets the
  outflow overshoot on kinked tables; the weighted `m` needs a rating table that a prismatic section does not have.
- **Warnings instead of conventions:** the choices hold for every input, so a notice on every result would say nothing.

## Open questions (the author's)

1. An applicability notice of the diffusion wave behind Muskingum-Cunge (Ponce: `t_r S0 (g/d0)^(1/2) > 15` for 95 %
   accuracy; EM 1110-2-1417 p. 9-21: a rise under 2 h on slopes under 1 ft/mile) — no notice is issued today.
2. NEH Fig. 17B-3 draws a "lower limit of Cg and Dg" without an equation; it may be the positivity bound `Cg + Dg >= 1`.
3. The lag's storages hold the initial outflow up to the first ordinate while its outflow ramps to the first inflow
   over the step before it: with `O0 != I0` the balance error is about `(I0 − O0) dt / 2`; aligning the storages would
   be `lag` `formula_version` 2.
