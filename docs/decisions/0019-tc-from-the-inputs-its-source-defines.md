# 0019. Time of concentration from the inputs its source defines: the longest flow path, no substitutes

- Status: accepted
- Date: 2026-11-05
- Amends: [ADR-0017](0017-typical-ranges-in-the-catalog.md) (the inputs of a range checked on a watershed are the one
  field the method's source defines, no longer a first choice with substitutes; the two channel ranges of
  Kerby-Kirpich are the ranges of the flow path)
- Builds on: Nogat plan `docs/plans/2026-11-05-official-tc-inputs.md` (decisions D1-D4, D6), the research behind it
  (sources quoted below) and Hydrograf's ADR-068, whose reason for handing tc over as a value this removes

## Context

The author asked on 2026-11-05 that every calculation follow what is official in its method („Chciałbym, żeby wszystkie
obliczenia były oparte na tym, co jest oficjalne w danej metodzie”). `WatershedParameters.calculate_tc` fed the formulas
with whatever field it found, first choice first:

- Kirpich and NRCS took the length of the main channel, else the length of the watershed; Kirpich the channel slope,
  else the mean slope of the watershed, else the relief over the length; NRCS the mean slope, else the channel slope,
  else the relief over the length;
- Giandotti took the channel, else the watershed length, and the mean elevation, else the middle of the elevation range;
- Kerby-Kirpich took the channel length and slope as given, and checked the ranges of the main channel "from the outlet
  to the divide" on the channel segment.

The sources define other inputs:

- **NRCS lag** (USDA-NRCS 2010, NEH 630 ch. 15, p. 15-5, eq. 15-4): ℓ, "the longest path along which water flows from
  the watershed divide to the outlet", and Y, "the average land slope of the watershed ... not to be confused with the
  slope of the flow path". TR-55 (1986), cited until now, does not contain the equation.
- **Kirpich** (Fang et al. 2005, TxDOT 0-4696-1, eq. 3.14; Mota and Kobiyama 2015 on Kirpich's 1940 graph): L along
  the watercourse from the outlet to the most remote point on the divide, and S the elevation of that point above the
  outlet over L.
- **Kerby-Kirpich** (Roussel et al. 2005, TxDOT 0-4696-2, supplement; TxDOT Hydraulic Design Manual, ch. 4, section 11):
  the main channel is the primary flow path from the divide to the outlet, its slope the drop from the divide to the
  outlet over that whole length, and the channel segment is the main channel minus the overland segment. With these
  inputs Hydrolog reproduces both published examples: 24.6 + 32.0 = 56.5 min against "about 57" (Roussel et al. 2005),
  and with the low-slope offset 52.1 + 86.8 = 138.9 min against "about 140" (Cleveland et al. 2012, TxDOT 0-6382-P1,
  the source of the offset; the cited "0-6544-1" report does not exist).
- **Giandotti** (Grimaldi et al. 2012): the main channel and the mean elevation of the basin above the outlet.
- **FAA** (FAA 1970, AC 150/5320-5B, fig. 7; not the later 5C and 5D, which lack the formula) and **Kerby** (Kerby
  1959 through Roussel et al. 2005): the overland length and the slope of the overland surface, with C from the
  circular's table I and N from Kerby's table.

Hydrolog had no field for the longest flow path, although Hydrograf measures it, so a hand-off from Hydrograf could not
be timed in Hydrolog with Hydrograf's inputs: Hydrograf's ADR-068 hands tc over as a value for that reason.

## Decision

- **Two fields of `WatershedParameters`** (optional, appended to the dataclass; in `from_dict`, the checks and the
  `watershed` of `hydrolog-network/1`): `flow_path_length_km`, the length of the longest flow path from the hydraulically
  most distant point of the watershed (the cell with the greatest flow distance to the outlet; usually on the divide, but
  possibly on a ridge between two valleys inside the watershed; NEH 630 ch. 15 p. 15-5, Fang et al. 2005 eq. 3.14) to the
  outlet along the flow [km], > 0; and `flow_path_slope_m_per_m`, the elevation of that point
  minus the outlet elevation, over that length [m/m], ≥ 0. A slope, not the elevation of the head: it is what the
  formulas take, like the other `*_slope_m_per_m` fields. The names say what the field is; Hydrograf's
  `hydraulic_length_km` is mapped to the first.
- **Each method takes the fields its source defines, with no substitute** (`hydrolog._ranges.TC_INPUTS`, one table
  read by `calculate_tc`, `tc_parameters` and the catalog): Kirpich `flow_path_length_km` and
  `flow_path_slope_m_per_m`; NRCS `flow_path_length_km`, `mean_slope_m_per_m` and `cn`; Giandotti `channel_length_km`
  and `elevation_mean_m` - `elevation_min_m`; FAA and Kerby `overland_length_km`, `overland_slope_m_per_m` and
  `runoff_coeff` or `retardance`; Kerby-Kirpich the overland fields, `retardance` and the flow path. A missing field is
  `validation_error` with `details.reason` `missing_field` naming it, whatever other fields the watershed has; the hint
  of a missing flow path says how it is measured. Giandotti's L is the main channel, as the sources say; whether it
  runs to the channel head or to the divide is the producer's (Hydrograf's is the channel head).
- **Kerby-Kirpich takes the flow path, a clean cut-over:** `ConcentrationTime.kerby_kirpich(overland_length_km,
  overland_slope_m_per_m, retardance, flow_path_length_km, flow_path_slope_m_per_m)`, the options of `tc kerby-kirpich`,
  `generate_tc_section` and `FormulaRenderer.kerby_kirpich_tc` (`fp_length_km`, `fp_slope_m_per_m`) replace the
  channel length and slope. The channel segment is `flow_path_length_km - overland_length_km`, timed by Kirpich at the
  slope of the whole path (with the low-slope offset below 0.002); a flow path not longer than the overland segment is
  `exclusive_minimum` on `flow_path_length_km`. The ranges 1.6-80 km and 0.002-0.02 are those of
  `flow_path_length_km` and `flow_path_slope_m_per_m`.
- **FAA's C and Kerby's N are inputs.** Nothing derives them: no table from land cover to C or N with a source is at
  hand.
- **Citations follow the sources above** in the docstrings, the catalog, the report and the GUI; the defaults are
  unchanged (`tc_method` `kirpich`, which now needs the flow path).

## Consequences

- **Breaking:** a watershed without `flow_path_length_km` and `flow_path_slope_m_per_m` is no longer timed by Kirpich,
  NRCS (which also needs `mean_slope_m_per_m`) or Kerby-Kirpich, and one without `channel_length_km` or
  `elevation_mean_m` by Giandotti: `tc watershed`, `hydrograph generate`, `report generate` and the `curve-number`
  runoff of `route network` end with `missing_field`, also by default (Kirpich). `tc kerby-kirpich` and its function,
  `generate_tc_section` and `FormulaRenderer.kerby_kirpich_tc` take the flow path. The CHANGELOG gives the migration.
- **Results change** where the old inputs were substitutes: Kirpich and NRCS from the channel to the longest flow path
  (the guide's Kamiennik: Kirpich 162.9 → 187.4 min, NRCS 377.5 → 399.8 min, Kerby-Kirpich 187.2 → 208.9 min, so the
  example's hydrograph changes), Giandotti without a mean elevation is refused instead of using the middle of the range.
  A watershed whose given fields were the official ones keeps its numbers.
- Hydrograf can send the fields it measures and Hydrolog computes the same method from them (Nogat plan, step 2): the
  hand-off can carry `tc_method` instead of `tc_min`.
- `hydrolog.testing.watershed()` gives a flow path by default (6 km at 0.02, the length and relief of its default
  catchment), so the default subcatchment is still timed by Kirpich.

## Alternatives considered

- **Keep the relief over the length for Kirpich's S, with a notice:** it equals the official S only when the most
  remote point is also the highest; on Kamiennik the head of the flow path is at 440 m, the summit at 475 m.
- **A field of the head's elevation** (with `elevation_min_m`): the raw measurement, but every formula would derive
  the slope, and an outlet elevation from another source would silently change it.
- **Keep the channel arguments of Kerby-Kirpich and derive them in `WatershedParameters`:** a "channel slope" option
  whose official meaning is the slope from the divide to the outlet is easy to misuse, and `TC_INPUTS` cannot express a
  difference of two fields.
- **Giandotti's L to the divide (the flow path):** the accessible sources say only "main channel"; Hydrolog takes the
  field of that name.
- **C and N from land cover:** no sourced class table; a default would be an assumption shown as a result.
