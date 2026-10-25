# Flood routing: summary for the author

Written: 2026-10-25. Plan: [2026-10-24-flood-routing.md](2026-10-24-flood-routing.md) (approved 2026-10-24, decisions D1, D9, D10, D13 and D14 delegated by the author to the coordinating session). Six branches are finished and each passed `scripts/gate.sh` before every commit. Nothing was pushed, tagged or merged by this work.

## Merge order

`chore/nogat-2.1` comes first: it is 16 commits ahead of `develop` (3069e64), tip d4f7282, and every routing branch continues it. The routing branches are one line of history, each the previous branch plus its own commits (checked with `git merge-base --is-ancestor`), so no merge can conflict.

| Order | Branch | Tip | Adds | Gate at the tip (passed / skipped, coverage) |
|---|---|---|---|---|
| 1 | `chore/nogat-2.1` | d4f7282 | 16 commits on `develop` | (see its own PROGRESS) |
| 2 | `feature/routing-core` | 777e5d6 | 6 commits | 4,030 / 6, 94.25 % |
| 3 | `feature/routing-muskingum` | f8a5fa2 | 2 commits | 4,164 / 6, 94.33 % |
| 4 | `feature/routing-muskingum-cunge` | 093fd44 | 2 commits | 4,280 / 6, 94.41 % |
| 5 | `feature/routing-cascade` | 73fbd13 | 2 commits | 4,435 / 6, 94.45 % |
| 6 | `feature/routing-level-pool` | f45de5f | 2 commits | 4,758 / 17, 94.55 % |
| 7 | `feature/routing-network` | b23c8e0, then the commit of this summary on top | 3 commits, the closing docs commit and two follow-up commits (the rules of schema, ids and large results, and this summary) | 5,095 / 17, 94.81 % at b23c8e0; the summary commit passed the gate too |

```bash
git switch develop
git merge --ff-only chore/nogat-2.1               # develop is an ancestor of it
git merge --ff-only feature/routing-core
git merge --ff-only feature/routing-muskingum
git merge --ff-only feature/routing-muskingum-cunge
git merge --ff-only feature/routing-cascade
git merge --ff-only feature/routing-level-pool
git merge --ff-only feature/routing-network
```

Every merge is a fast-forward in this order. `feature/routing-network` contains the five branches before it, so merging it alone after `chore/nogat-2.1` brings the whole of the work; merge the others first only to keep their names in the history, or use `--no-ff` for a merge commit per branch as `develop` has (3069e64). The skips grow from 6 to 17 at the level-pool branch because one parametrized test skips the 11 sampled tables that allow every step of the test ("the table allows any step of the test"); no test is skipped for a missing extra.

## What each branch holds

| Branch | Content | Reference and its error |
|---|---|---|
| `feature/routing-core` | the research report and the plan, ADR-0007 (scope), ADR-0008 (conventions) and ADR-0009 (one index line for a compact group in the guide); `ClarkIUH` on the shared kernel with the step guard (finding F1); `hydrolog.routing` (`Hydrograph`, `Reach`, `RoutingResult`, `LagReach`); `load_hydrograph`; `route lag` | identities only: exact |
| `feature/routing-muskingum` | `MuskingumReach` with sub-reaches inside the positivity window, `route muskingum` | University of Iowa, Lesson 27 (K = 20 h, X = 0.25): 0.049 cfs, inside the 0.05 cfs of the print; `X` = 0.5 is a lag, `X` = 0 the Clark scheme, mean delay `K`, variance `K²(1 - 2X)/N` to 1e-9 |
| `feature/routing-muskingum-cunge` | `MuskingumCungeReach` (constant coefficients, the NRCS form), `TrapezoidalSection`, accuracy and rise-time rules, `route muskingum-cunge` | NEH-630 example 17-4: 0.24 ft³/s (0.04 % of the peak) with the printed `c` and `T`; the printed three-decimal coefficients give the table to 0.0049 ft³/s, so the 0.24 is their rounding; from the section 2.4 ft³/s (0.4 %) |
| `feature/routing-cascade` | `CascadeReach`, the exact response of a chain of linear reservoirs to a piecewise-linear inflow, any time step, `route cascade` | no published table; 1e-10 of the matrix exponential, 1e-8 of the convolution integral, the weights 1e-13 to 1e-9 of 60-digit arithmetic |
| `feature/routing-level-pool` | `LevelPoolReach` (storage indication, modified Puls) with a step rule per segment of the table, `route level-pool` (inline table or `rating_file`) | NEH-630 example 17-1: 0.85 ft³/s (0.02 % of the peak), 0.49 ft³/s with the ordinates that give the printed averages |
| `feature/routing-network` | the plan of a directory of plain output and `-o` (`plan_directory`, `staging_directory`, `output_in_store`), `RoutingNetwork`, `route network` with the document `hydrolog-network/1` and its JSON Schema, a table per node in `--output-dir`, ADR-0010 | no published reference; the identities of the plan: a one-reach network writes the table of the single command byte for byte, the order of the nodes changes nothing, a junction adds, `N` reaches in series equal `N` sub-reaches (1e-12 with `extend_min` fixed) |

The results table with the figures is in the plan, section Results.

## Decisions to review

- **ADR-0007 to ADR-0010**: scope, conventions (hydrograph table, initial condition, tail, stability, files), one index line for a group of six commands (a documented deviation from DOC-4.2 in `CLAUDE.md`), and the network (document, files beside it, order, `--output-dir`). ADR-0010 amends ADR-0003, which said Hydrolog has no `--output-dir`. Its amendment of 2026-10-25 records three decisions of the coordinating session: `schema` required, device-name ids refused, the `large_result` warning.
- **`-o`** is the short flag of `--output-dir` and of no other option (AGI-3.4); the parser adds it.
- **DEV-19.7 deviation in `CLAUDE.md`**: `--output` replaces one file through a temporary file beside it; `--output-dir` writes through `.hydrolog-incoming/<host>_<pid>_<token>/`.
- **`hydrolog-network/1`**: `schema` is required (AGI-4.1; without it `missing_field`, with another value `unknown_schema`); `from` is always a list; an id names the file `<id>.csv` (letters, digits, `_`, `.`, `-`, at most 64, unique without regard to case, and not a Windows device name: `con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`, any case, any extension, is `reserved_name`); `value_column` names the column of `inflows_file` (default the node id); a `rating_file` must lie in the directory of `network_file` because a server checks the options of a call and not the files a document names; one outlet, no bifurcation.
- **Series in the result**: without `--output-dir`, `route network` puts the hydrograph of every selected node (default all) into the result, so that a read-only MCP server can route. For a large network that is a large result; `nodes` limits it, and a result of more than 20,000 characters (the page of DOC-1.7) carries the warning `large_result` that suggests `nodes` and `--output-dir`. The envelope does not page a command result, so the result is not cut.
- **Defaults that decide numbers**: the outflow starts at the first inflow ordinate; the tail is extended until the outflow is within 0.1 % of the inflow peak, at most ten times the inflow duration; over a chain of reaches each cuts its tail at that tolerance, so a chain differs from one reach with sub-reaches by about 0.1 % of the peak unless `extend_min` is fixed.
- **Guide budget**: `AGENTS.md` is 16,264 of 16,384 bytes. The next command needs another cut (DOC-1.7, D10).

## Skipped or not done

- **Left to the author** (working rules): pushes, tags, merges, history rewrite, GitHub settings, root-owned files, licence and CLA text.
- **Not in the plan** ([2026-10-24-flood-routing.md](2026-10-24-flood-routing.md), section Not in this plan): variable-parameter Muskingum-Cunge and compound sections (R2b), `route reach-params`, `route outlet-rating`, kinematic and dynamic waves, continuous modelling.
- **Requests to other projects** (DEV-17.5): none opened. [INTEGRATION.md](../INTEGRATION.md) describes the mapping that Hydrograf can use (subcatchment to node, `StreamSegment` to reach, confluence to junction) and the hand-off to Hydraulik (`<id>.csv` per node); a network exporter in Hydrograf and a reader in Hydraulik would be `request` issues in their repositories.
- **Not built**: sources computed from a watershed or from rain (a subcatchment brings a hydrograph), bifurcations (refused), channel parameters estimated from geometry inside the document.

## To check it

```bash
git log --oneline chore/nogat-2.1..feature/routing-network      # 17 commits of work, the closing docs commit and two follow-up commits
scripts/gate.sh                                                   # in a checkout of any tip, about 3.5 minutes
hydrolog route network --network-file tests/fixtures/network_flood.json \
  --inflows-file tests/fixtures/network_inflows.csv -o network_out --lang en
hydrolog route network --network-file tests/fixtures/network_flood.json \
  --inflows-file tests/fixtures/network_inflows.csv -o network_out --check --lang en
```

The first run writes `A.csv`, `B.csv`, `R1.csv`, `J1.csv`, `D.csv` and `OUT.csv` and shows the summary of the six nodes; the second lists every file as a conflict.
