# 0028. The providers' lines in every product: `attribution` and `terms_notice`

- Status: accepted
- Date: 2026-11-13
- Builds on: Nogat DEV §20 (DEV-20.1 to DEV-20.8) and ECO-060 (Nogat `fix/provider-attribution`, `bbb58a8`,
  `edd559b`, `6f75180`), the author's order of 2026-11-13, plan
  [2026-11-13-provider-attribution](../plans/2026-11-13-provider-attribution.md)
- Amends: [ADR-0002](0002-result-envelope-and-domain-documents.md) (the envelope gains `attribution` and
  `terms_notice`) and [ADR-0018](0018-pmaxtp-through-obserwator.md) (PMAXTP's own lines replace the attribution of
  the general terms of IMGW-PIB)
- Amended by [ADR-0035](0035-one-strip-of-the-providers-lines-per-gui-view.md) (2026-11-13): point 7, what the GUI
  shows on screen
- Amended by [ADR-0036](0036-link-the-providers-terms-instead-of-restating-them.md) (2026-11-13): points 1 and 7, the
  lines and the terms notice
- Amended by [ADR-0040](0040-cp-without-the-detail-of-processing.md) (2026-11-14): point 1, CP is „Dane ČHMÚ
  zostały przetworzone”, once, and an older CP with its detail is read as it

## Context

The terms of IMGW-PIB (<https://danepubliczne.imgw.pl/regulations>, §5 ust. 3 and 4), of the PMAXTP project (a dialog
on <https://klimat.imgw.pl/opady-maksymalne>, ust. 1 and 2), of IMGW-PIB's hydrological service
(<https://hydro.imgw.pl/#/regulamin>) and ČHMÚ's licence (CC BY 4.0, §3(a)(1)) bind every product made with their
data: a source line, a line that the data were processed, PMAXTP's monograph, the licence with its link. Nogat fixed
the lines byte for byte and where they go (DEV §20); its table is quoted in
`src/hydrolog/_attribution.py`.

Hydrolog computes with such data in two ways. It fetches one itself, the PMAXTP depth of `precip pmaxtp`, whose
result named IMGW-PIB in the wording of the general terms only (ADR-0018), which PMAXTP's own terms replace. And it is
given the others: the station series of an Obserwator export (whose CSV has the columns `attribution_source` and
`attribution_processed`, which Hydrolog ignored), a series handed off by Archiwista, a PMAXTP depth passed on as
`total_mm` by the person, the GUI or an agent. A number given inline carries no sign of its source, and no product of
Hydrolog carried any line but the PMAXTP result's.

## Decision

1. **One source of the lines**: `hydrolog._attribution` holds S, P, H, PS, PP, M, C and the notice N with RD, RH, RK
   verbatim, and Hydrolog's own CP, „Dane ČHMÚ zostały przetworzone (obliczenia hydrologiczne programem Hydrolog)”.
   `Attribution` turns the providers found (`imgw`, `imgw_hydro`, `pmaxtp`, `chmi`) into their complete lines:
   Hydrolog processes everything it computes with, so a product always has the processed line, and the terms notice
   follows from the providers (N with RD, RH or RK; none for ČHMÚ). Lines it knows are recognised with a final full
   stop or blanks around them; a ČHMÚ credit by its beginning (an earlier wording without the licence's link becomes C);
   a producer's CP is kept before Hydrolog's; any other line is carried verbatim after the known ones. Lines merge
   in the order of DEV-20.4 and DEV-20.7, each once.
2. **The envelope** `hydrolog-result/1` gains `attribution` and `terms_notice` after `result`, arrays of strings,
   present only when the run met a provider's data (AGI-4.1: optional fields keep `/1`; Nogat's `result-1` allows
   them). The domain documents keep their schemas; `precip pmaxtp` keeps its string `result.attribution`, now PS.
3. **The run collects the lines** (`hydrolog._attribution.collecting`, opened by `run_command`): the readers of input
   files cite what a file carries (the CSV columns `attribution` and `terms_notice`, one line per cell, and
   Obserwator's `attribution_source` and `attribution_processed`, which are left out of the table's data; the fields
   `attribution` and `terms_notice` of a JSON object), an operation cites its option `attribution` and the lines of
   the data it fetches (`precip pmaxtp`: PMAXTP), and the envelope gets what was collected.
4. **The option `attribution`** (`string_list`, a JSON array on the command line) on the commands that take a
   provider's data inline: `precip hietogram`, `precip areal`, `scs effective`, `hydrograph generate`, `report
   generate`, the six `route` commands that route, every `stats` command and both `hydrometrics` commands. It takes
   the lines of the data's source, attribution and terms mixed (the `attribution` and `terms_notice` of the
   `precip pmaxtp` result, of a hand-off); the command completes them. Rejected: an option naming the provider
   (`pmaxtp`, `imgw`), which needs a vocabulary beside Nogat's lines and cannot carry a line Hydrolog does not know;
   a global flag outside the catalog, which the catalog's contract (one declaration, every interface) does not allow.
5. **Files**: the hydrograph tables of `route * --output` and `route network --output-dir` have the trailing columns
   `attribution` and `terms_notice` (DEV-20.5: one line per cell from the first data row down, a short table joins
   the rest into its last cell), still read by every `route` command; `route network --output-dir` also writes
   `ATTRIBUTION.txt` at the directory's root (DEV-20.5; merged with one already there, listed in `result.files`);
   the SVG of `--schematic` draws the lines under its legend; the Markdown of `report generate` ends with the section
   „Źródła danych”. A network document `hydrolog-network/1` may carry `attribution` and `terms_notice` at its top,
   which change no calculation and are carried into the result and files.
6. **Interfaces**: the CLI prints „Źródła danych” / „Data sources” with the lines before the notices; MCP passes the
   envelope's fields and its instructions say to show them and pass them on; the notice `pmaxtp_attribution` says the
   same and names PMAXTP's terms; `GET api/session` answers `attribution`, the complete lines of each provider, for a
   page that names the provider of a hand-off that has no lines of its own.
7. **The GUI** shows the lines and the terms notice under every result with a provider's data and in every export
   (CSV columns, the envelope's JSON, a footer drawn into PNG charts, the print view, the report, the hand-off's
   `attribution` and `terms_notice`, copied with Nogat's schema at `edd559b`), passes the lines of its sources (the
   PMAXTP fetch, a hand-off) as `attribution` to every run, and names the provider of an older hand-off from its
   `provenance`.

## Consequences

- An agent that passes a PMAXTP depth on gives its lines too, or the product of the next command lacks them; the
  notice, the catalog rule of `precip pmaxtp` and the MCP instructions say so.
- A number typed by a person without a source carries nothing: Hydrolog cannot know it came from a provider.
- The command line the GUI shows for a run with lines has `--attribution '[...]'`; it reproduces the run.
- Output tables of runs with provider data have two more columns; a reader that takes columns by name, as every
  reader in the ecosystem does, is unchanged.
