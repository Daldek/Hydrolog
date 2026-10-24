# 0008. Routing conventions: hydrograph table, initial condition, tail, stability

- Status: accepted
- Date: 2026-10-24

## Context

Every routing model takes a discharge hydrograph and gives one, and the models differ
in how they can fail numerically (a Muskingum step outside its positivity window gives
negative flows, a level-pool step that is too long gives negative outflows). The report
[2026-10-24-long-term-and-routing.md](../plans/2026-10-24-long-term-and-routing.md)
(sections 5.3 and 6.1, decisions D7 and D9) proposes common rules; this record fixes
them for all `route` commands and the `hydrolog.routing` classes, so that the commands
are interchangeable and a result can feed the next command or a hydraulic model.

## Decision

- **Hydrograph table (D7):** two columns, `time_min` (minutes since an origin, strictly
  increasing at a regular step) and `discharge_m3s`. At least two ordinates; times and
  discharges are finite and discharges are not negative. The step is regular when every
  step differs from the mean step by at most 1e-6 of it. There is no resampling: an
  irregular table is rejected (`validation_error` for inline lists, `data_error` for a
  file; `details.reason` is `irregular_step`, `not_increasing`, `negative`,
  `length_mismatch`, `too_short` or `not_finite`). Units: minutes, m3/s, m3 and km.
- **Initial condition:** the outflow at the first ordinate equals the inflow there
  (steady state, as in HEC-HMS) unless `initial_outflow_m3s` is given. Every sub-reach
  starts with that outflow.
- **Tail:** the outflow outlasts the inflow. The time axis is extended after the last
  inflow ordinate, the last inflow value being held, until the outflow stays within
  0.1 % of the inflow peak of that value; the extension is at most ten times the
  duration of the inflow (and at least 100 steps), otherwise the series ends with the
  notice `tail_truncated`. `extend_min` fixes the extension instead (0 gives none). The
  notice `tail_extended` reports the added minutes.
- **Balance:** volumes are trapezoid sums. A result lists the storage of the reach at
  both ends and `balance_error_m3` = inflow volume (on the extended axis) - outflow
  volume - change of storage; it is zero to rounding for the recurrences unless the
  scheme ran on a refined grid (below). The exact kernel of the cascade evaluates the
  outflow at the ordinates of a curve, not of a straight line, so its balance error is
  the quadrature error of the trapezoid rule: second order in the step and negligible
  when the series starts and ends at rest.
- **Stability (D9):** the library chooses automatically and says so with a notice: the
  number of sub-reaches stays inside the positivity window of the scheme
  (`|2KX| <= dt <= 2K(1-X)` for a Muskingum step; `|c dt - D| <= dx <= c dt + D` with
  `D = Q / (T S0 c)` for a Muskingum-Cunge distance step `dx`; `subreaches_adjusted`
  when the rule of thumb or the NRCS number of steps had to move), and when no number
  of sub-reaches fits, the step is refined by an integer factor (the inflow is
  interpolated linearly, the outflow sampled back at the original ordinates;
  `substeps_added`, and `timestep_refined` where NEH-630 asks for at least 10 steps from
  5 % of the peak to the peak). A value the caller gave explicitly (`subreaches`) is
  never changed: outside the window it is a `validation_error` with
  `details.reason = "unstable_timestep"` and the window. A reach for which no division
  of the step into at most 100 parts gives a window (a short, flat reach, which is
  storage) is refused with the same reason. A scheme with an exact kernel (the cascade)
  has no window: no time step is too long for it, and it adds neither sub-reaches nor
  sub-steps.
- **Non-negativity:** inside the window all weights are non-negative, so a
  non-negative inflow gives a non-negative outflow.
- **Accuracy notices are not errors:** the Muskingum-Cunge accuracy limit of NEH-630 is
  `Dg <= exp(2.3 Cg)` with the grid Reynolds number `Dg = D / dx = 1 - 2X` and the
  Courant number `Cg = c dt / dx`. Every distance step inside the window above meets
  it: for `Dg <= 1` the limit is at least 1; for `Dg > 1` the window `|Cg - Dg| <= 1`
  gives `Cg >= Dg - 1`, and `exp(2.3 (Dg - 1)) >= Dg`. The library therefore never
  routes beyond the limit, and the notice `accuracy_limit` (level `info`) reports a
  replacement, not an inaccurate result: the step of the NRCS rule
  would have been beyond the limit and the reach was routed on a step inside it
  (`subreaches_adjusted`, or `substeps_added`). It is a notice, never an error.
- **Files:** `output` writes the outflow as a hydrograph table (`time_min`,
  `discharge_m3s`) with `force` and `check` as in
  [ADR-0003](0003-writing-commands-output-force-check.md). Without `output` the command
  has no file to plan, so `check` computes as usual; this keeps a read-only MCP server,
  which turns every call of a writing tool into a plan, able to route.

## Consequences

- One loader (`load_hydrograph`) and one result document shape serve all commands; the
  files that `route` commands write are valid inputs of every `route` command and the
  hand-off format to Hydraulik.
- A hydrograph with a missing value or an irregular step has to be repaired before
  routing; dated daily series are not a routing input in this version.
- `ClarkIUH` refuses a time step above twice its storage constant instead of returning
  a negative ordinate (finding F1 of the report); it uses the same linear-reservoir kernel.
