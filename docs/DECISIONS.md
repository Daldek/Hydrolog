# Decisions

Architecture decision records (DOC-8.1). One file per decision in
[decisions/](decisions/); new records get the next number. Decisions taken before
the Nogat standard 2.1 adoption are in the plans of [plans/](plans/).

| ID | Title | Status | Date |
|---|---|---|---|
| [0001](decisions/0001-catalog-english-and-operation-ids.md) | English catalog, Polish in `i18n.pl`, `hydrolog_` operation ids | accepted | 2026-10-24 |
| [0002](decisions/0002-result-envelope-and-domain-documents.md) | Result envelope and domain documents | accepted | 2026-10-24 |
| [0003](decisions/0003-writing-commands-output-force-check.md) | Writing commands: `--output`, `--force`, `--check` | accepted | 2026-10-24 |
| [0004](decisions/0004-settings-and-config-show.md) | Shared settings and `config show` | accepted | 2026-10-24 |
| [0005](decisions/0005-error-registry.md) | Adopt the shared error registry | accepted | 2026-10-24 |
| [0006](decisions/0006-mcp-server-conformance.md) | MCP server conformance with AGI section 5 | accepted | 2026-10-24 |
| [0007](decisions/0007-flood-routing-enters-the-scope.md) | Lumped hydrologic flood routing enters the scope | accepted | 2026-10-24 |
| [0008](decisions/0008-routing-conventions.md) | Routing conventions: hydrograph table, initial condition, tail, stability | accepted | 2026-10-24 |
| [0009](decisions/0009-compact-index-line-for-large-groups.md) | One index line for a command group that would not fit the guide | accepted | 2026-10-24 |
| [0010](decisions/0010-route-network-document-and-output-directory.md) | `route network`: the network document, one table per node, `--output-dir` | accepted | 2026-10-25 |
| [0011](decisions/0011-public-testing-module.md) | `hydrolog.testing`: builders of the files other projects read | accepted | 2026-10-25 |
| [0012](decisions/0012-network-objects-rainfall-and-runoff.md) | Network objects, rainfall and runoff per subcatchment, and control points | accepted | 2026-10-25 |
| [0013](decisions/0013-network-schematic.md) | The schematic of a network: a metro-style map that Hydrolog computes | accepted | 2026-10-25 |
| [0014](decisions/0014-web-gui-enters-the-scope.md) | The web GUI enters the scope: `hydrolog.gui`, `gui serve`, hosting in Nogat, a private server API | accepted | 2026-11-02 |
| [0015](decisions/0015-catalog-additions-for-the-gui.md) | Catalog additions for the GUI: `format_command`/`parse_command`, `NOTICES`, `route schematic`, UH ordinates, `gui serve` | accepted | 2026-11-02 |
| [0016](decisions/0016-gui-feedback-and-data-dir.md) | Reports of the GUI's users: „Zgłoś uwagę”, `data_dir` and the admin key | accepted | 2026-11-04 |
| [0017](decisions/0017-typical-ranges-in-the-catalog.md) | Typical ranges: one table in Hydrolog, served in the document of one command (`typical_ranges`) | accepted | 2026-11-04 |
| [0018](decisions/0018-pmaxtp-through-obserwator.md) | PMAXTP through Obserwator: `precip pmaxtp`, the one command that uses the network | accepted | 2026-11-04 |
| [0019](decisions/0019-tc-from-the-inputs-its-source-defines.md) | Time of concentration from the inputs its source defines: the longest flow path, no substitutes | accepted | 2026-11-05 |
| [0020](decisions/0020-a-stations-series-through-the-handoff.md) | A station's series through the hand-off: `hydrolog-series/1` into Statystyka przepływów | accepted | 2026-11-05 |
| [0021](decisions/0021-fit-methods-of-flood-frequency.md) | Fit methods of flood frequency: maximum likelihood, moments, L-moments and least squares | accepted | 2026-11-06 |
| [0022](decisions/0022-homogeneity-tests.md) | Homogeneity tests of annual maxima: Mann-Whitney U, two-sample Kolmogorov-Smirnov and Pettitt | accepted | 2026-11-06 |
