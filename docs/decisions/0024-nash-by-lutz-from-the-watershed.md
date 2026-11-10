# 0024. Nash's n and K estimated from the watershed: `nash_estimation` (Lutz) in the command, the report and the network

- Status: accepted
- Date: 2026-11-10
- Amends: [ADR-0012](0012-network-objects-rainfall-and-runoff.md) (the `curve-number` runoff of `hydrolog-network/1`
  gains the optional field `nash_estimation`; its watershed then supplies the inputs of the estimation)
- Builds on: the plan [2026-11-10-network-wizard.md](../plans/2026-11-10-network-wizard.md) (approved 2026-11-10;
  the author's decision A5, the plan's D5 and D6, and the coordinator's answer to its question Q1 of 2026-11-10) and
  [ADR-0019](0019-tc-from-the-inputs-its-source-defines.md) (each method takes the inputs its source defines)

## Context

The author decided on 2026-11-10 (A5) that the `curve-number` runoff of a network can say „Lutz”: an optional field,
like `tc_method`, selects Lutz's estimation of Nash's n and K from the watershed, and the library computes them, as
`uh nash` already does. Until now:

- `NashIUH.from_lutz` served `uh nash` only. `hydrograph generate`, `report generate` and the `curve-number` runoff
  took Nash's n and K as numbers, so a network document could not say how they were obtained.
- Hydrogram zlewni ran `uh nash` first and then `hydrograph generate` with the n and K it estimated (the GUI plan's
  D13: „because `hydrograph generate` has no `nash_estimation`”). The command line it exported carried two numbers
  without naming their source, and its hand-off carried them with a `provenance.runoff` of `uh nash`.
- The report had the steps of Lutz's method, but no operation asked for them.
- The GUI and Kalkulatory fed Lutz's L and J with the channel (`channel_length_km`, `channel_slope_m_per_m`). Lutz
  (1984, after KZGW 2017, annex 2, table C.2), and the options of `uh nash` itself, define L as the length of the main
  stream from the divide to the section and J as its mean slope. Hydrograf's channel ends at the channel head, short
  of the divide (ADR-0019): its length is not Lutz's L.

## Decision

1. **One option and one field, `nash_estimation`.** A string with the one value `lutz`, optional, without a default:
   an option of `hydrograph generate` and, as it takes the same options, of `report generate`, after `nash_k_min`
   (`--nash-estimation lutz`; Polish „Estymacja n i K”), and a field of the `curve-number` runoff of
   `hydrolog-network/1`, after `nash_k_min` in its canonical form (`CurveNumberRunoff(nash_estimation="lutz")`,
   property `nash_estimation`). The constants are `NASH_ESTIMATIONS` of `hydrolog.routing`,
   `hydrolog.morphometry.watershed_params` and `hydrolog.operations.hydrograph` (`NashEstimation`), pinned to the
   catalog's choices by a test.
2. **The inputs are the fields the method defines** (the coordinator's answer to Q1). `hydrolog._ranges.NASH_INPUTS`,
   beside `TC_INPUTS`, names them: L `flow_path_length_km`, Lc `Lc_km`, J `flow_path_slope_m_per_m`, n_M
   `manning_n`, U `urban_pct` and W `forest_pct` (0 when the watershed has none, as in `uh nash`), and `area_km2`,
   which scales the unit hydrograph and is checked against Lutz's range. Lutz's main stream from the divide is the
   longest flow path that ADR-0019 introduced, the field Kirpich reads; the channel is not a substitute.
   `WatershedParameters.nash_parameters("lutz")` returns the keyword arguments of `NashIUH.from_lutz`, and
   `compute_hydrograph` (so `hydrograph generate` and `report generate`) and `CurveNumberRunoff` both estimate with
   `NashIUH.from_lutz(**watershed.nash_parameters(method))`: one path for the command, the report and the network.
3. **The reasons are those of `tc_method`** (`validation_error`, decided by `details`):
   - `nash_estimation` with another `uh_model`: `not_applicable` on `nash_estimation`;
   - with `nash_n` or `nash_k_min`: `conflict` on `nash_estimation`;
   - Nash with neither n and K nor an estimation: `required` on `nash_n`, whose hint names `nash_estimation`;
   - another value: `choice`;
   - `hydrograph generate` given `area_km2` and `cn` instead of a watershed: `not_applicable` on `nash_estimation`
     (nothing to estimate from);
   - a field Lutz needs and the watershed lacks: `missing_field` with `details.option` the first of
     `flow_path_length_km`, `Lc_km`, `flow_path_slope_m_per_m`, `manning_n` that is missing, `details.missing` all of
     them and `details.method` `lutz`; in a network also `details.node_id`, and `details.option` names the field
     inside the node's watershed (`watershed.flow_path_length_km`), as a missing field of a `tc_method` does;
   - `Lc_km` longer than `flow_path_length_km`: `maximum` on `Lc_km` (`details.maximum` the flow path's length);
     a flow path of slope 0: `exclusive_minimum` on `flow_path_slope_m_per_m` (Lutz divides by J).
4. **What a run says.** The result `hydrolog-hydrograph-generate/1` gains `nash_estimation` (after `uh_model`; `null`
   for given n and K or another model), and its `uh_parameters` hold the estimated `n` and `k_min`.
   `HydrographRun` keeps `nash_estimation` and `lutz` (the `LutzCalculationResult`), from which `report generate`
   prints Lutz's inputs and steps in its unit hydrograph section. `describe()` of the runoff lists `nash_estimation`
   (`given`) and, with a watershed, `nash_n` and `nash_k_min` (`computed`), so `route network` and the schematic show
   them. `hydrograph generate` and `report generate` serve Lutz's area range in `typical_ranges` (method `lutz`,
   parameter `area_km2`), and a larger watershed gives the notice `outside_typical_range` with that method.
5. **An estimate is not checked against the ranges of given n and K.** Those ranges are of given values and have no
   published source (`outside_unverified_range`); an estimating constructor never checked them. The generator takes
   the estimate as such (`HydrographGenerator(uh_params={..., "estimated": True})`), so one run warns exactly as
   `uh nash` did, and less than the two runs it replaces, whose second run checked the numbers as given ones.
6. **The version stays `/1`** (AGI-4.1): the field is optional, and the document and the result are unreleased. A
   document without the field is read and written byte for byte as before.
7. **Hydrogram zlewni takes the same path** (D6): Nash by Lutz sends `nash_estimation` with the watershed in one
   `hydrograph generate`, never `uh nash`; its command line says `--nash-estimation lutz` and reproduces the run; its
   hand-off carries `nash_estimation` instead of n and K. A hand-off written before, with n and K and the
   `provenance.runoff` of `uh nash`, opens with that n and K given. Kalkulatory fills `uh nash`'s L and J from the
   flow path.

## Consequences

- **Results change** where Lutz was fed with the channel. The guide's Kamiennik at Świerzawa (PMAXTP 101.82 mm,
  12 h, Beta, Δt 10 min, AMC II; L 14.78 → 15.88 km, J 0.0142 → 0.0114): n 3.631 → 3.610, K 82.35 → 92.13 min, peak
  37.66 → 35.03 m³/s at 8:50 → 9:10 h; the volume (977,067 m³) does not change. `uh nash` itself takes the L and J it
  is given, as before.
- One run equals the two it replaces, to the last ordinate, when `uh nash` is given the flow path; a network node
  with the field equals the command. The tests hold both.
- An older Hydrolog refuses a document with the field (`unknown_field`), as it refused ADR-0012's and ADR-0023's: the
  release sets move the pins together (Retman, Hydrograf). Hydrograf may write the field, but need not.
- `hydrolog.testing.curve_number_runoff` takes the field (its `**options` go through the real reader).
- PROGRESS's open question on the ranges of given n and K no longer concerns Lutz.

## Alternatives considered

- **Keep the channel for L and J** (the plan's first draft, no number would change): the channel ends at the channel
  head, so its length and slope are not those of Lutz's stream; ADR-0019 refused the same substitute for Kirpich.
- **A new field for the stream to the divide:** the longest flow path is that stream, Hydrograf measures it already
  and Kirpich reads it.
- **Keep `uh nash` before `hydrograph generate` in the GUI:** two runs, a command line whose numbers do not say where
  they come from, and a hand-off whose reader cannot estimate again from its own watershed.
- **Run Hydrogram zlewni through `route network` of a one-node document:** the section shows what
  `hydrograph generate` gives (the rainfall, the losses, the balance, the unit hydrograph's ordinates).
- **Urban regression as a value of `nash_estimation`:** its inputs, the effective rainfall and its duration, belong to
  the storm, not to the watershed.
