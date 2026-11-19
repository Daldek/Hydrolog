# 0061. The routing formulas by specs: the schemes on a given grid, the reaches plan the grid

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs),
  [ADR-0008](0008-routing-conventions.md) (routing conventions), [ADR-0012](0012-network-objects-rainfall-and-runoff.md)
  (network objects), [ADR-0026](0026-a-reach-without-a-muskingum-cunge-grid.md) (a reach without a Muskingum-Cunge grid),
  Nogat's computation standard (CMP-2.1, CMP-2.2, CMP-3.4, CMP-3.5, CMP-6.5) and the literature research of the routing
  formulas of 2026-11-18 (`ct-research/routing.md`: no gross defect, the code's rules sourced)

## Context

The routing family is the next to get specs (Nogat's plan of the computation standard, step 5). Its schemes are
recurrences or kernels over a hydrograph: Muskingum through equal sub-reaches, Muskingum-Cunge with constant
coefficients, the cascade of linear reservoirs, storage indication of a level pool and the lag, with Manning's normal
flow of a prismatic section for the celerity of Muskingum-Cunge. Around each scheme the reach classes do what is not the
formula: they check their options when a network document is read (each refusal with its `node_id`, ADR-0012), choose
the grid (the sub-reaches of Muskingum by HEC-HMS's rule, the distance steps of Muskingum-Cunge by NEH 630's rules, the
sub-steps of a step without a window, the fallback of ADR-0026), extend the time axis until the outflow settles and
report the volume balance (ADR-0008). Their refusals of a grid that cannot exist (`unstable_timestep`) and of a flood
beyond a table (`table_exceeded`, `table_emptied`) carry details that the web GUI's Sieć words and offers changes for.

The standard wants one spec per formula beside a function that takes exactly its inputs, checks made only by the
reference module (CMP-3.5), and no `calculation_error` for accepted inputs (CMP-3.4).

## Decision

1. **The formulas are the schemes on a given grid,** in the package `hydrolog.routing.formulas`, one module per scheme,
   each with its spec and its function; `hydrolog.routing.formulas._shared` holds what they share (the inflow, the step
   and the initial outflow as inputs, the sources, the volume by the trapezoid rule). The first is `muskingum`
   (`muskingum_route(inflow_m3s, timestep_min, k_min, x, subreaches, initial_outflow_m3s)`): the window of non-negative
   weights, 2KX/N ≤ Δt ≤ 2K(1 − X)/N to the planner's slack of 10⁻⁹, is its precondition `nonnegative_weights`.
2. **The reaches keep their options, their plans and their refusals.** `MuskingumReach` and the other reaches check
   their options with the catalog's vocabulary when they are made, choose the grid, extend the time axis and compute
   through the formulas, so that a network document is still refused node by node when it is read and Sieć keeps its
   words for `unstable_timestep`; the rules of the grids are their modules' Tier B formulas (`muskingum_subreaches`).
   The formula modules hold no check of their own; a caller of a formula gets the standard's refusals.
3. **Rounding never gives a negative outflow.** The three-point recurrence starts after the first ordinate, from
   `c_previous I[0] + c_outflow O[0]`, so `O[0]` is the initial outflow itself and no difference of inputs is taken; a
   weight that rounding puts below zero on a border of the window is set to zero and the others are divided by their
   sum (`_kernels.nonnegative_coefficients`). With non-negative weights every outflow is then a sum of non-negative
   terms, non-decreasing in every input, as the spec's monotonicity asserts.
4. **Evidence.** The published cases with their roundings in `tests/fixtures/formulas/<family>-cases.json` (the
   University of Iowa's and NPTEL's Muskingum examples), oracles in exact rational arithmetic and the moments of the
   impulse response, limits and the volume balance as a conservation law, and the generated tests, with a strategy of
   points inside the window for the properties (`tests/unit/test_formulas_muskingum.py`).

## Consequences

- `route muskingum` and a network with a Muskingum reach carry `"formula_versions": {"muskingum": 1}`; their outflows
  change by rounding only (at most 1.4·10⁻¹² relative over 20,000 random runs).
- A reach's refusal and a formula's refusal of the same value differ in vocabulary: `MuskingumReach(k_min=-1)` is
  `exclusive_minimum` (catalog), `muskingum_route(..., k_min=-1, ...)` `outside_physical_range` (standard).

## Alternatives considered

- **The reach classes as the spec's functions:** their arguments are a `Hydrograph` and options of a plan, not the
  inputs of a formula; the grid they choose is not an input of the scheme.
- **Dropping the reaches' own checks** (as the unit hydrographs did): a network document would be accepted when read
  and refused only when routed, and Sieć would lose its words for `unstable_timestep`.
- **The window as an applicability warning:** outside it the outflow can be negative, a result the standard forbids;
  it is a precondition.
