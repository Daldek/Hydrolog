# Copies of the Nogat standard

Verbatim copies (ERR-3, AGI-4.1, DEV-15.6) of the files below, from the
[Nogat](https://github.com/Daldek/Nogat) repository at commit `7786271` (2026-11-12). The
standard is numbered 1.0 since Nogat `55a191a` (the drafts called 2.0 and 2.1 became 1.0); it
is not tagged yet, so replace the copies by the tag when it is. Nogat's `scripts/ecosystem.py
drift` reports each copy as current, behind or modified.

- `error_registry.json` (Nogat `standards/error_registry.json`): error codes, exit
  codes and HTTP statuses. `src/hydrolog/_errors.py` is generated from it with
  `uv run scripts/generate_errors.py`.
- `result-1.schema.json`, `error-1.schema.json`, `commands-1.schema.json` (Nogat
  `schemas/agent/`): the schemas of the result envelope, the error document and the
  command catalog. `tests/contract/` validates Hydrolog's documents against them.
- `handoff-1.schema.json` (Nogat `schemas/exchange/handoff-1.schema.json` at `b29eada` of Nogat's
  `develop`, whose ECO-065 made `terms_notice` the links to the providers' terms only, RD, RH
  and RK, in its description and examples; `edd559b` had added the optional `attribution` and
  `terms_notice`, the providers' lines of DEV §20, and `8848c26` `node_provenance`, the origin
  of each node of a network; SHA-256
  `c26ce043b292284fa7e8f995589fee09fd5ffa046efb61c4b3736619b8b71d08`): the envelope
  `nogat-handoff/1` of data handed between the GUIs of the ecosystem. The GUI writes and reads
  it with the payload `hydrolog-network/1` and the origin of each of its nodes
  (`src/hydrolog/gui/web/src/handoff/`, through Nogat's kit `web/nogat/nogat-handoff.js`).
  `tests/contract/test_gui_handoff.py` validates hand-offs against this copy; the browser
  checks the envelope against its validation keywords (`handoff/envelope.js`, which
  `tests/e2e/test_exports.py` compares with the copy).
- `record-1.schema.json` (Nogat `schemas/log/record-1.schema.json` at `a41d971` of Nogat's
  `develop`, ECO-066; SHA-256
  `cac452bd338054916d7837820053b0a5ed8f5a076a33f95ed0448ded170984d0`): `nogat-log/1`, one record
  of the logs of `hydrolog gui serve` (DEV-12.4 to DEV-12.9), written by Nogat's reference module
  `standards/reference/nogat_logging.py`, which is copied from the same commit, unchanged, to
  `src/hydrolog/gui/nogat_logging.py` (SHA-256
  `66964a5167ab8edd40f5bcae4462bf685bbe2e34456e8bead6722fe8cf0d32b7`).
  `tests/integration/gui/test_serve.py` and `test_public.py` validate the records against this copy.

Do not edit these files; copy them again when the standard changes.
