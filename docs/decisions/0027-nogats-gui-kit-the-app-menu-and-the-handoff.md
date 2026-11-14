# 0027. Nogat's GUI kit: the app menu and the shared hand-off

- Status: accepted
- Date: 2026-11-12
- Builds on: Nogat ECO-058 and its plan `docs/plans/2026-11-12-gui-links-and-handoff.md` (approved 2026-11-12, stage 1
  of the GUI platform; this is its step 4), DEV-15.4 to DEV-15.6 and DEV-18.1 of the Nogat standard
- Amends: [ADR-0014](0014-web-gui-enters-the-scope.md) (the private API's `GET api/session` gains `gui`)
- Amended by [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (2026-11-13): kit 0.4.0

## Context

The author asked on 2026-11-12 for one way from any GUI of the ecosystem to the others and one hand-off between them.
Nogat answered with a kit (`design/kit/`, version 0.1.0 at Nogat `7786271`): the element `<nogat-app-menu>` with its
stylesheet, and `nogat-handoff.js`, which names the file, writes the text, copies with a fallback, downloads, reads a
file or the clipboard and checks a document against a JSON Schema with Polish messages. Every GUI copies the files byte
for byte and never edits them (DEV-15.6). Hydrolog had its own hand-off code: the file named after the section's file
base (`handoffFileName`), the text and the download in `handoff-panel.js`, a clipboard copy that fails outside a secure
context (`ui/export-panel.js` `copyText`), and a keyword validator of its own (`handoff/validate.js`) for the envelope
and the payload. Its menu had no address of another GUI.

## Decision

1. **The kit in `web/nogat/`**, beside the tokens and the marks: `nogat-app-menu.js`, `nogat-app-menu.css`,
   `nogat-handoff.js` and `nogat-kit.json`, copied byte for byte from Nogat `7786271`, and the mark of Obserwator,
   so every GUI the menu knows has its mark. `nogat/nogat.json` stays the record of the identity's copies (tokens and
   marks: source, commit, SHA-256); the kit's own manifest `nogat-kit.json` holds the SHA-256 of its files. A contract
   test checks both and that every file of `web/nogat/` is one of them; Nogat's `drift` reports the same copies as
   current, behind or modified.
2. **The addresses** come from the table `gui` of `[nogat]` in `nogat.toml` (DEV-18.1; `NOGAT_CONFIG` or the user
   configuration directory), read by `hydrolog._settings.gui_addresses` at every `GET api/session`, which answers them
   as `gui` (`null` without the table). Only `[nogat]` gives it: the table describes the deployment, not the tool, so
   there is no `[hydrolog]` table, no environment variable and no default. Rejected: a value written into `index.html`
   (the page is static package data and a host serves it unchanged) and a route of its own (the page reads the
   session at its start anyway). Read at every request, a new address applies at the next page load without a
   restart, as the admin key does (ADR-0016).
3. **The menu** is `<nogat-app-menu current="hydrolog" marks="nogat/marks/">` in the top bar (`ui/top-bar.js`), left
   of the theme switch; the page sets its `apps` from the session. With no other GUI in the table it is not drawn, and
   inside a host (`?nogat=1`) the top bar with it is hidden. The module loads under the GUI's CSP (`script-src
   'self'`); an entry opens its GUI in the tab `nogat-<name>`, which with Hydrolog's `Cross-Origin-Opener-Policy`
   costs one more tab per click (Nogat's plan, D3).
4. **Writing a hand-off** goes through the kit: „Plik przekazania” downloads `<subject>.handoff.json`
   (`downloadHandoff`, the name rule of D6), „Kopiuj do Hydrologa” (`TEXTS.copyTo`, formerly „Do schowka”) copies with
   `copyHandoff`, whose fallback puts the text selected into a field below the buttons for Ctrl+C where the browser
   gives no clipboard or refuses it. The consumer of Hydrolog's own hand-off is Hydrolog, so no „Otwórz …” link follows
   a copy. `handoffFileName` is gone; `copyText` and `downloadBlob` of `export-panel.js` stay for the other exports.
5. **Reading** goes through the kit for the file, the clipboard (`readFile`, `readClipboard`) and the envelope:
   `readHandoff(text, ENVELOPE_SCHEMA)` with the keywords of `handoff/envelope.js` (the page cannot load the copy of
   the schema, which lies outside the package; a browser test compares the two). Hydrolog keeps its own check of the
   payload, `handoff/validate.js`, since the kit's `validate` reads `\w` of a pattern as ASCII, while Python's
   `jsonschema` takes a node id such as `Ś1`, and names only the `oneOf` of a node instead of the problem inside the
   branch its `type` chooses; its problems now use the kit's keywords and parameters and are worded by the kit's
   `TEXTS`, with Polish numbers. Hydrolog's domain checks (a series' length, minima, the rainfall's step) and the
   hints for a text that is not a hand-off (a network file, a watershed file) stay its own.
6. **The labels** the GUIs share come from the kit's `TEXTS`: „Wczytaj z Hydrografa”, „Wczytaj z Archiwisty”, „Plik
   przekazania…”, „Wklej ze schowka”, „Plik przekazania”, „Kopiuj do Hydrologa” and the messages after a copy or a
   download.
7. **The copies of the standard** in `schemas/nogat/` are Nogat's at `7786271`: `error_registry.json` (the standard
   numbered 1.0 since Nogat `55a191a`; `_errors.py` regenerated), the agent schemas and `handoff-1.schema.json`
   unchanged.

## Consequences

- A refused envelope reads in the kit's words („producer.tool: niezgodne ze wzorem ^[a-z][a-z0-9]*$”, „To nie jest
  przekazanie nogat-handoff/1.”); a payload's problems keep their paths with the node's id.
- The kit lacked what Hydrolog's payload check needs (Unicode `\w`, problems inside a `oneOf`) and drops no leading
  byte order mark (Hydrolog drops it before the kit parses); these are reported to Nogat rather than patched here.
- `tests/e2e/test_shell.py` checks the menu at the root, under a host's prefix and on a phone; `tests/e2e/test_exports.py`
  the file name, the copy's fallback field and the kit's messages; `tests/integration/gui/test_app.py` the session's
  `gui`; `tests/contract/test_gui_web.py` the copies.
