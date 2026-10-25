# 0011. `hydrolog.testing`: builders of the files other projects read

- Status: accepted
- Date: 2026-10-25

## Context

DEV-10.6 asks every producer to ship a public `<package>.testing` module, in the installed wheel, that builds
small valid instances of every format another project reads from its files; consumers test against it, with the
producer at the version they pin, instead of against formats written by hand. Hydrolog had no such module
because no project read its files (PROGRESS, open question "`hydrolog.testing` module"). One does now:
Hydraulik reads the hydrograph tables of `route network --output-dir` as the inflow of a sewer
(`swmm run --inflow`, `model couple --inflow`) and the envelope of `precip hietogram` (`rainfall build
--hietogram`), and Hydrograf is to write `hydrolog-network/1` documents ([ADR-0010](0010-route-network-document-and-output-directory.md)).

## Decision

- **One module, `hydrolog/testing.py`,** shipped with the package (it is under `src/hydrolog`, not under `tests/`).
  It builds: network documents (`subcatchment`, `reach`, `junction`, `outlet`, `network_document`,
  `write_network_document`), hydrograph tables (`hydrograph_table`, `network_tables`, `write_network_tables`), a
  complete small case of files (`build_network_fixture`: `network.json`, `inflows.csv` and the tables of
  `out/`) and the envelope of `precip hietogram` (`hietogram_envelope`, `write_hietogram_envelope`).
- **The real code makes every instance.** A table is `Hydrograph.to_table()`, a network document is read by
  `load_network` before it is returned (a column source is checked as an inline one), the tables of a network are
  routed by `RoutingNetwork`, an envelope is `run_command("precip hietogram", ...).to_json()`. A builder is never a
  second copy of a format, so it cannot drift from it.
- **No clock, no network, no random numbers.** Two calls with the same arguments give the same bytes; an envelope
  carries the `version` of the installed Hydrolog.
- **Only what a consumer reads or writes.** The formats of the `route` commands that no other tool touches (the
  result of `route lag`, the plan) have no builder; add one with the first consumer (DEV-10.6).
- **Contract test** `tests/contract/test_testing_module.py` runs the real `hydrolog` program and compares: the
  tables of `build_network_fixture` and of `write_network_tables` with the files of `route network
  --output-dir`, `hydrograph_table` with the file of `route lag --output`, the envelope with the line that
  `precip hietogram --json` prints, the documents with the shipped JSON Schema and the command that reads them.
- **The module is public API** from 1.0.0: a name or a signature of `hydrolog.testing` changes only with a major
  version, like the documents it builds.

## Consequences

- Hydraulik's tests build their Hydrolog inputs with `hydrolog.testing`; its recorded real outputs
  (`tests/fixtures/hydrolog`, `tests/fixtures/rain/hietogram_euler_ii.json`) stay, because they prove the
  recorded behaviour of a given commit, not the format.
- The Nogat registry lists `hydrolog-testing` in the `exchange` of the Hydrolog edges that carry files (a Nogat
  change, not made here).
- `hydrolog.testing` imports NumPy (the routing code); `import hydrolog` still imports none.
- Hydrolog's own tests keep their private builders of broken documents (`tests/unit/_network_documents.py`): they
  build documents that the loader must refuse, which a builder of valid instances never does.
