# 0068. A station's series as an `input_file`: `hydrolog-series/1`, alone or in Archiwista's hand-off

- Status: accepted
- Date: 2026-11-21
- Builds on: [ADR-0020](0020-a-stations-series-through-the-handoff.md) (the payload `hydrolog-series/1` and the GUI's
  reading); the finding E3-07 of the scenario test of 2026-11-15/16 (F1, decision B6) and the author's decision of
  2026-11-21 („`--input-file` accepts `hydrolog-series/1`”)

## Context

ADR-0020 made `hydrolog-series/1` the payload of Archiwista's hand-off and taught only the GUI to read it. The CLI, the
MCP server and the Python API read a series from `input_file` as CSV or as JSON tables (records, columns, a list of
numbers); a `hydrolog-series/1` or a `nogat-handoff/1` around it ended with exit 7, `data_error`, „unsupported JSON
structure” (`details.reason` `shape`). The scenario test took the earlier „GUI only” for a defect (E3-07) and the author
decided on 2026-11-21 that `--input-file` accepts `hydrolog-series/1`, leaving open whether the envelope is read too.

What Archiwista gives a person or an agent outside a browser is the envelope, never the bare payload: its CLI
`archiwista stations handoff CODE --variable Q [--resolution annual]` prints the whole `nogat-handoff/1` („the document
itself on standard output; save it as `NAZWA.handoff.json`”, Archiwista's `docs/AGENT_API.md`), and its route
`GET /stations/{code}/handoff` answers the same document (A-ADR-052). The providers' lines of the series (`attribution`,
`terms_notice`, Nogat DEV-20.6) are fields of the envelope, not of the payload. Accepting the payload alone would make
every user cut the file by hand and lose the lines the provider's terms require.

## Decision

1. **`read_table` reads a `hydrolog-series/1` as a table of two columns**: `date` (`step` `day`) or `year` (`step`
   `year`) and the series' `variable` (`Q`, `H`, `P`), its `null` values missing. Every command whose series comes
   through `read_table` takes it (`stats`, `meteo`, `hydrometrics water-level-zones`, `scs effective`, `stats
   flood-frequency` and the others; `hydrometrics rating-curve` needs pairs of two variables, which no series carries).
2. **A `nogat-handoff/1` whose `payload` is a `hydrolog-series/1` is read the same way**, its `attribution` and
   `terms_notice` the lines of the run (cited into the envelope like a CSV's attribution columns). A hand-off of any
   other payload (a `hydrolog-network/1`) is refused with `details.reason` `handoff_payload`; the envelope's other
   fields are not checked (`producer`, `created_at`: nothing in a computation reads them, and Nogat's schema allows
   unknown fields).
3. **The series' columns are the defaults of a series**: with neither `date_column` nor `year_column`, the key column
   is `date` (daily values) or `year` (annual values), so daily values keep their dates and annual maxima their years
   (the annual maxima of `stats flood-frequency` come from the hydrological years of daily values instead of every
   day taken for a maximum; the split year of `stats homogeneity`, Sen's slope per year of `stats mann-kendall`).
   `value_column` is the variable where a command leaves it optional (`scs effective`, `load_series`); the catalog's
   `one_of` groups are unchanged, so a command that requires `value_column` (and `date_column`) takes `Q` (and
   `date`), a column option naming one of the two columns as in any file. Annual values where a command needs dates
   are refused with `annual_series`.
4. **The payload is checked as its schema checks it** (unknown and missing fields, `step`, `statistic`, `year_type`, the
   variable's pattern, the types of the lists, as many keys as values), with `data_error` and the field in `details`.
   Hydrolog does not depend on `jsonschema`; the check is in `hydrolog.catalog.inputs`, beside the other readers.
5. The option `input_file` of the series says so in the catalog (`commands schema`), the rule „Other sources” of the
   guides names Archiwista.

## Consequences

`hydrolog stats flood-frequency --input-file raba.handoff.json --value-column Q` runs on Archiwista's file as saved; the
GUI's reading (ADR-0020) is unchanged. A JSON table whose top `schema` is `hydrolog-series/1` or `nogat-handoff/1` was
refused before, so no file that loaded loads differently. Annual minima (`statistic` `min`) are read like maxima: the
GUI refuses them in Statystyka przepływów, which computes flood quantiles, while the commands leave the choice to the
caller (`stats low-flow` takes daily values). Tests: `tests/unit/test_catalog_inputs.py` (`TestSeriesDocuments`) and
`tests/unit/test_cli.py` (the CLI with a hand-off of daily values and with annual values).
