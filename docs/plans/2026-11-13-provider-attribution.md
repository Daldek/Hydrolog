# Plan: the providers' lines in every product of Hydrolog (2026-11-13)

Requested: 2026-11-13, the author's order (the attribution IMGW-PIB's terms require MUST be in every product that
contains their data; ČHMÚ's terms must be met as well; use is non-commercial)

Step 3 of Nogat's plan `docs/plans/2026-11-13-provider-attribution.md` (Nogat branch `fix/provider-attribution`:
DEV §20, ECO-060, the hand-off's `attribution` and `terms_notice`, `ATTRIBUTION.txt`). Branch
`fix/provider-attribution` from `develop` (`912dbf2`); no merge, tag or release. Requirements: DEV §20, DEV-15.5,
DEV-15.6, DEV-17.4, AGI-1.1, AGI-4.1, DOC-7.2. Decisions: [ADR-0028](../decisions/0028-the-providers-lines-in-every-product.md).

## Audit (before this branch)

| Product | Provider data | Lines before |
|---|---|---|
| `precip pmaxtp` result (CLI, MCP, Python) | PMAXTP | S only (`result.attribution`, notice `pmaxtp_attribution`), not PMAXTP's own wording; no P, M, N |
| `precip hietogram`, `hydrograph generate`, `scs effective` with a PMAXTP depth | PMAXTP | none |
| `report generate` (Markdown) | PMAXTP | none |
| `route *` tables (`--output`), `route network --output-dir` tables, `--schematic` SVG | PMAXTP (a network's rainfall), station series | none |
| `stats *`, `hydrometrics *` on an Obserwator CSV export | IMGW-PIB, ČHMÚ series | none: the columns `attribution_source`, `attribution_processed` were read as data and ignored |
| The same on values a hand-off brought (Statystyka) | IMGW-PIB, ČHMÚ series | none |
| CLI human output | all of the above | none |
| GUI, Hydrogram zlewni | PMAXTP | S under the PMAXTP fields, a client copy of the text; nothing under the result, in CSV, PNG, JSON, the report, the print view or the hand-off |
| GUI, Sieć i trasowanie | PMAXTP | none |
| GUI, Statystyka przepływów | IMGW-PIB, ČHMÚ series | none; the hand-off card named the producer only |
| GUI, Wszystkie polecenia, Kalkulatory | any command's | the notice of `precip pmaxtp` only |
| `nogat-handoff/1` written | PMAXTP | provenance only |

## Decisions

### D1. One source, Nogat's lines verbatim

`hydrolog._attribution` holds every line of DEV §20 and Hydrolog's CP; `_pmaxtp.ATTRIBUTION` and `TERMS_URL` move
there. The GUI holds no copy: it receives the lines in envelopes, hand-offs and `GET api/session`.

### D2. The envelope's `attribution` and `terms_notice`

Top-level, after `result`, only with a provider's data; completed by Hydrolog (processed lines, terms), merged in
Nogat's order (ADR-0028, 1 and 2).

### D3. Where the lines come from

Input files (CSV columns, JSON fields), the data a command fetches, and the new option `attribution` for data given
inline (ADR-0028, 3 and 4).

### D4. Files Hydrolog writes

Table columns, `ATTRIBUTION.txt` in an output directory, lines under the schematic, the report's „Źródła danych”;
`hydrolog-network/1` accepts the two fields (ADR-0028, 5).

### D5. The GUI

A footer of the lines under every result with a provider's data and in every export, the PMAXTP fetch's lines kept
with the depth, the hand-off read and written with `attribution` and `terms_notice`, an older hand-off named by its
`provenance` (ADR-0028, 7).

## Steps

1. The module, the envelope, the readers, the option, the writers, the CLI, MCP and the schemas (Python).
2. The GUI and its guide.
3. Tests: unit and integration for the lines, the readers, the writers and the acceptance cases (a `precip pmaxtp`
   envelope; `stats flood-frequency` on an Obserwator export); browser tests for Statystyka from a hand-off and for
   Hydrogram's exports.
4. Docs: ADR-0028, this plan, CHANGELOG, PROGRESS, USAGE, INTEGRATION; the guides regenerated.

## Results

All four steps done on 2026-11-13 in one commit of `fix/provider-attribution`.

- Python: `src/hydrolog/_attribution.py`; the envelope (`catalog/envelope.py`), the collection in `run_command`
  (`catalog/dispatch.py`), the readers (`catalog/inputs.py`, `operations/_network_input.py`,
  `routing/document.py`), the option (`catalog/groups/_attribution.py` on 21 commands), the writers
  (`operations/route.py`, `routing/_svg.py`, `operations/report.py`), `precip pmaxtp` (`operations/precip.py`,
  notice in `catalog/notices.py`), the CLI (`cli/render.py`), MCP (`mcp/_instructions.py`), `GET api/session`
  (`gui/_app.py`); schemas `hydrolog-network-1` and `hydrolog-precip-pmaxtp-1` regenerated; the guides unchanged.
- GUI: `web/src/attribution.js` (the footer „Źródła danych”, the CSV columns, the image footer, the option), every
  section's results and exports, `charts/png.js` (footer rows), `css/print.css`, the hand-off (`handoff/*.js`,
  `envelope.js` from Nogat `edd559b`), the guide's section „Źródła danych” and three pictures retaken (`ekran.png`,
  `hydrogram.png`, `eksport.png`).
- Tests: `tests/unit/test_attribution.py` (the lines verbatim, recognition, CSV and `ATTRIBUTION.txt`, the
  acceptance runs: `stats flood-frequency` on an Obserwator export, a ČHMÚ export, a PMAXTP depth through
  `hydrograph generate`, the CLI, the report, route tables and the network), `tests/unit/test_operations_pmaxtp.py`
  (the envelope of `precip pmaxtp`), `tests/e2e/test_attribution.py` (Statystyka from an Archiwista hand-off with and
  without lines, Hydrogram's footer and exports, a series without a provider).
- Left: Kalkulatory's tc comparison has no provider data and no footer; a series or watershed file the browser
  reads itself (a CSV pasted into a field, „Plik zlewni…”) sends values inline without the lines such a file may
  hold (none carries provider data today).
