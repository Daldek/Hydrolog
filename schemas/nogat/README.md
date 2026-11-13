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
- `handoff-1.schema.json` (Nogat `schemas/exchange/handoff-1.schema.json` at `edd559b` of Nogat's
  branch `fix/provider-attribution`, which added the optional `attribution` and `terms_notice`,
  the providers' lines of DEV §20, to the envelope and its examples; `8848c26` had added
  `node_provenance`, the origin of each node of a network; SHA-256
  `7d69384bafe92c02c2008b4e822b9d7b80f5b382817dc3dbce213c6726ecd958`): the envelope
  `nogat-handoff/1` of data handed between the GUIs of the ecosystem. The GUI writes and reads
  it with the payload `hydrolog-network/1` and the origin of each of its nodes
  (`src/hydrolog/gui/web/src/handoff/`, through Nogat's kit `web/nogat/nogat-handoff.js`).
  `tests/contract/test_gui_handoff.py` validates hand-offs against this copy; the browser
  checks the envelope against its validation keywords (`handoff/envelope.js`, which
  `tests/e2e/test_exports.py` compares with the copy).

Do not edit these files; copy them again when the standard changes.
