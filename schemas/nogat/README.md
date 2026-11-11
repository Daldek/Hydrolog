# Copies of the Nogat standard

Verbatim copies (ERR-3, AGI-4.1) of the files below, from the standard 2.1 of the
[Nogat](https://github.com/Daldek/Nogat) repository at commit `cc656e7` (the tag
`std-2.1` does not exist yet; replace the copies by the tag when it does):

- `error_registry.json` (Nogat `standards/error_registry.json`): error codes, exit
  codes and HTTP statuses. `src/hydrolog/_errors.py` is generated from it with
  `uv run scripts/generate_errors.py`.
- `result-1.schema.json`, `error-1.schema.json`, `commands-1.schema.json` (Nogat
  `schemas/agent/`): the schemas of the result envelope, the error document and the
  command catalog. `tests/contract/` validates Hydrolog's documents against them.

And, outside the standard, from commit `8848c26` on Nogat's `develop` (the optional
`node_provenance`, the origin of each node of a network, and a second example that
carries it; Nogat's `docs/plans/2026-11-10-node-provenance-in-handoff.md`; SHA-256
`84c6856d1148acdc08bf79600c8cdab03674e81fe1f30eb7abeb66629b5742ed`):

- `handoff-1.schema.json` (Nogat `schemas/exchange/handoff-1.schema.json`): the
  envelope `nogat-handoff/1` of data handed between the GUIs of the ecosystem. The GUI
  writes and reads it with the payload `hydrolog-network/1` and the origin of each of
  its nodes (`src/hydrolog/gui/web/src/handoff/`). `tests/contract/test_gui_handoff.py`
  validates hand-offs against this copy; the browser checks them against its validation
  keywords (`handoff/envelope.js`, which `tests/e2e/test_exports.py` compares with the
  copy).

Do not edit these files; copy them again when the standard changes.
