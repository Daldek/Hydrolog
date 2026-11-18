# 0043. Snyder's L in the web GUI is the longest flow path, not the channel

- Status: accepted
- Date: 2026-11-18
- Builds on: [ADR-0024](0024-nash-by-lutz-from-the-watershed.md) (Lutz's L from the longest flow path, for the same
  reason) and [ADR-0019](0019-tc-from-the-inputs-its-source-defines.md) (each method takes the inputs its source
  defines); finding T4 of the formula audit of 2026-11-18 (`ct-research/TRIAGE.md`, `unit-hydrographs.md` §16)

## Context

Snyder's lag is tL = Ct·(L·Lc)^0.3 with L the length of the main stream from the outlet to the divide (Snyder 1938;
HEC-HMS Technical Reference, Snyder eq. 5; KZGW 2017, p. 90: „od działu wodnego do przekroju zamykającego”). The
options of `uh snyder` and `hydrograph generate` say the same („from the divide to the outlet”).

Hydrogram zlewni, Sieć and Kalkulatory took L from the watershed's `channel_length_km`, „Długość cieku głównego”.
Hydrograf, which fills that field, measures it along the DEM stream network from the outlet to the channel head at its
accumulation threshold (Hydrograf `backend/models/schemas.py`), short of the divide. Lutz's L had the same defect,
which ADR-0024 fixed by reading the longest flow path, `flow_path_length_km`, „from the hydraulically most distant
point (usually on the divide) to the outlet”; Snyder kept the channel.

## Decision

1. The GUI takes Snyder's L from `flow_path_length_km` (`SNYDER_LENGTHS` of Hydrogram's state, the `uh snyder` copy
   of Kalkulatory). Snyder then requires the flow path, not the channel, in step 1; Lc stays `Lc_km`.
2. Snyder's L of an earlier visit or of a `hydrolog-network/1` runoff (`snyder_length_km`) fills the watershed's
   empty `flow_path_length_km`, as it filled `channel_length_km`.
3. The labels say „do działu wodnego”; the guide states the definition and the change.
4. The library is unchanged: `SnyderUH`, `uh snyder` and `hydrograph generate` take the L they are given.

## Consequences

- Results of the GUI change wherever the channel and the flow path differ. The guide's Kamiennik at Świerzawa
  (PMAXTP 101.82 mm, 12 h, Beta, Δt 10 min, AMC II, Lc 6.76 km, Ct 1.5, Cp 0.6): L 14.78 → 15.88 km, tL × 1.022,
  peak 27.46 → 26.98 m³/s.
- A watershed with a channel and no flow path cannot run Snyder in the GUI until the flow path is given.
- Hydrograf's own Snyder (`backend/api/endpoints/hydrograph.py`, `L_km = channel_length_km`) and its Lutz estimation
  (`L_km = channel_length_km`, `slope = channel_slope_m_per_m`) must follow and read `flow_path_length_km` (and
  `flow_path_slope_m_per_m` for Lutz).

## Alternatives considered

- **Keep the channel and document it:** the channel is not Snyder's L; the lag is too short by (L_channel/L)^0.3
  (−2 % on the guide's watershed, −3 to −10 % for a channel 70–90 % of the flow path).
- **A new field for the stream to the divide:** the longest flow path is that stream, Hydrograf measures it already,
  and Kirpich and Lutz read it.
