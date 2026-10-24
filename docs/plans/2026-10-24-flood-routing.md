# Plan: lumped hydrologic flood routing (phases R0 to R4)

Approved: 2026-10-24

The approval is the author's delegation of decisions D1, D9, D10, D13 and D14 to the coordinating session on 2026-10-24 ([ADR-0007](../decisions/0007-flood-routing-enters-the-scope.md)); the author reviews the branches before anything is merged, tagged or pushed.

## Goal

Add flood routing to Hydrolog as a closed set of lumped hydrologic methods, each with a library class, a catalog command in the group `route`, reference tests against published values, documentation and a result envelope that follows the existing conventions (ADR-0002, ADR-0003, ADR-0005). The research is [2026-10-24-long-term-and-routing.md](2026-10-24-long-term-and-routing.md) (section 5, appendices A and B); this plan fixes what it left open for routing. Continuous (long-term) modelling is not part of this plan.

## Decisions

| ID | Decision |
|---|---|
| D1 | Lumped hydrologic routing is in scope; hydraulics stays with Hydraulik, HEC-RAS and IMGW HD ([ADR-0007](../decisions/0007-flood-routing-enters-the-scope.md)). |
| D7 | Hydrograph table `time_min` (elapsed, strictly regular step) and `discharge_m3s`; time in minutes, discharge in m3/s, storage in m3, length in km; no resampling ([ADR-0008](../decisions/0008-routing-conventions.md)). |
| D9 | Automatic sub-reaches or sub-steps with a notice; an explicit value outside the stability window is a `validation_error` with `details.reason = "unstable_timestep"` ([ADR-0008](../decisions/0008-routing-conventions.md)). |
| D10 | `AGENTS.md` stays within 16 KiB: a group declared compact prints one index line instead of one per command ([ADR-0009](../decisions/0009-compact-index-line-for-large-groups.md)); no information is dropped, `commands list` and `commands schema` still give each command. |
| D13 | Group `route`; commands `route lag`, `route muskingum`, `route muskingum-cunge`, `route cascade`, `route level-pool`, `route network`; package `hydrolog.routing`. |
| D14 | The research report moves to `docs/plans/` (DEV-17.4). |

## Interfaces fixed by this plan

- **Hydrograph input** of every single-reach command: either `times_min` with `discharge_m3s` (inline lists) or `input_file` with `time_column` (default `time_min`) and `value_column` (default `discharge_m3s`); the step is regular, discharge is not negative.
- **Result**: `hydrolog-route-<verb>/1` with the model, the effective parameters, peaks, volumes, the storage at both ends, the balance error and the extension of the time axis; the outflow series is inline (`times_min`, `outflow_m3s`) unless `output` is given.
- **File**: `output` writes the outflow as a hydrograph table (`time_min`, `discharge_m3s`), which is again a valid input of every `route` command and the hand-off to Hydraulik; `force` and `check` as in ADR-0003. Without `output`, `check` has nothing to plan and the command computes as usual, so a read-only MCP server can still route.
- **Initial condition**: the outflow at the first ordinate equals the inflow (steady state) unless `initial_outflow_m3s` is given.
- **Tail**: the outflow outlasts the inflow, so the time axis is extended after the last inflow ordinate (the last inflow value is held) until the outflow is within 0.1 % of the inflow peak of that value, unless `extend_min` fixes the extension; the extension is reported (`tail_extended`, `tail_truncated`).

## Steps

Each model has its own branch, started from the previous one; the gate (`scripts/gate.sh`) is green before every commit.

| Branch | Content | Reference tests |
|---|---|---|
| `feature/routing-core` | this plan and ADR-0007 to ADR-0009; `hydrolog.routing` (`Hydrograph`, `Reach`, shared kernels); `route lag`; `ClarkIUH` on the shared kernel with the step guard (finding F1) and its docstring fixed; the compact index line of the guide (D10) | identities (a shift by whole steps is exact), balance, superposition |
| `feature/routing-muskingum` | `route muskingum` with automatic sub-reaches inside the positivity window | University of Iowa example (K = 20 h, X = 0.25); X = 0.5 with K equal to the step is a lag; X = 0 equals the Clark scheme; mean delay K and variance K^2 (1 - 2X) / N |
| `feature/routing-muskingum-cunge` | `route muskingum-cunge`: constant coefficients (NRCS form), channel sections, accuracy check, rise-time rule | NEH-630 chapter 17, example 17-4 |
| `feature/routing-cascade` | `route cascade`: Kalinin-Milyukov / Nash cascade with an exact kernel | exact response to piecewise-linear inflow; equals `NashIUH` |
| `feature/routing-level-pool` | `route level-pool`: storage-indication (modified Puls) | NEH-630 chapter 17, example 17-1 |
| `feature/routing-network` | `route network` over a `StreamNetwork`-style DAG; hydrograph CSV hand-off | one-reach network equals the single command; order independence; junction sums |

## Results

Filled in at the end of each branch (maximum difference from the published values).

| Branch | Reference | Maximum difference |
|---|---|---|
| `feature/routing-core` | (identities only) | exact |

## Not in this plan

Variable-parameter Muskingum-Cunge and compound sections (R2b), `route reach-params` and `route outlet-rating` (R4 beyond the level-pool command), kinematic and dynamic waves, Hydrograf and Hydraulik `request` issues (DEV-17.5), and the whole of the continuous-modelling direction.
