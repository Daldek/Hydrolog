# 0020. A station's series through the hand-off: `hydrolog-series/1` into Statystyka przepływów

- Status: accepted
- Date: 2026-11-05
- Builds on: Nogat plan `docs/plans/2026-11-05-archiwista-series-to-hydrolog.md` (decisions D2, D3), the GUI plan's D15
  (the hand-off `nogat-handoff/1` with Hydrograf) and [ADR-0014](0014-web-gui-enters-the-scope.md)

## Context

The author asked on 2026-11-05 for a way to pass a station's series from Archiwista to Hydrolog's statistics like the
one between Hydrograf and Hydrolog („Hydrolog ma możliwość liczenia statystyk z szeregów rocznych maksimów lub dobowych.
Trzeba zrobić mechanizm przekazywania danych z Archiwisty do Hydrologa analogiczny do tego, który jest pomiędzy
Hydrografem a Hydrologiem”). Until now a series reached „Statystyka przepływów” only as a CSV file the person exported
(`obserwator series export`) and uploaded, or as pasted values. The hand-off `nogat-handoff/1` carries any payload a
consumer validates against its owner's schema; the GUI took `hydrolog-network/1` only and refused any other kind.

## Decision

1. **The payload `hydrolog-series/1`** (`src/hydrolog/schemas/hydrolog-series-1.schema.json`, written by
   `scripts/generate_result_schemas.py` beside `hydrolog-network/1`): `name`, `variable`, `unit` and either `step`
   `day` with `dates` (ISO days) or `step` `year` with `statistic` (`max`, `min`), `year_type` (`hydrological`,
   `calendar`) and `years`; `values` the same length, `null` for a missing value. Unknown fields are refused. Hydrolog owns
   it as it owns the network document; Nogat's envelope is unchanged.
2. **Reading** (`web/src/handoff/handoff.js` `readHandoff`, `handoff-panel.js` `openHandoff`): a hand-off whose payload is
   `hydrolog-series/1` is checked against that schema and against what the section needs beyond it (as many values as
   dates or years, at least one value), and opens in „Statystyka przepływów”. Annual maxima become the pasted values in
   the order of their years, missing years left out; daily values become a file of the session `<subject>.csv`
   (`date` and the variable), written as an upload would write it, whose columns the section finds as it finds those of
   a person's file. The section keeps where the series came from (`HandoffOrigin`) until its series is changed.
3. **Annual minima are refused** with the reason: the section computes flood quantiles; low flows are `stats low-flow`
   in „Polecenia”. The schema keeps `min` for a later consumer.
4. **The button** „Wczytaj z Archiwisty” in the first step of Statystyka przepływów is the same reading as „Wczytaj z
   Hydrografa” with texts that name Archiwista; any hand-off opens where it belongs. Archiwista's mark is copied from
   Nogat at the commit of the other marks (`nogat/nogat.json`).

## Consequences

Archiwista writes the document („Kopiuj do Hydrologa”, „Plik przekazania” on the station card; its A-ADR-052).
`tests/e2e/test_statystyka.py` opens annual maxima (the mockup's GEV „Q 1% 307,3 m³/s” from the same values with a
missing year), a daily series (its columns and complete hydrological years) and refused minima;
`tests/contract/test_result_schemas.py` checks the schema. The section's file box no longer shows „undefined” for a
session file: its missing text (`file.session`) is added.
