# Plan: Hydrolog's web GUI, standalone and as a Nogat module

Approved: 2026-11-02

Approved by the author on 2026-11-02 ([ADR-0014](../decisions/0014-web-gui-enters-the-scope.md), [ADR-0015](../decisions/0015-catalog-additions-for-the-gui.md)), together with the choices on the mockup's open questions and the deviations: the (i) texts in the GUI now; stable notice codes now, option names in library errors later; slope in m/m with a % hint; no variants; a print view instead of a PDF output; a Polish-only UI (a deviation from DEV-2.2); the private GUI API outside AGI section 6. Nogat's N1 (the `nogat-handoff/1` schema) is approved ahead of the rest of the platform plan, and the public tunnel (to 127.0.0.1:8070) will be behind Cloudflare Access, which the author sets up; this answers the open questions 1 and 2.

Requirements: DEV-17.4, DEV-15.1 to DEV-15.3, DEV-2.2, DEV-2.3, AGI-1.1, AGI-2.1, AGI-2.3, AGI-4.1 to AGI-4.3, ECO-055, HUB-1.2. Inputs: the approved mockup (Nogat `design/mockups/hydrolog/`, branch `feature/hydrolog-gui-mockup`, `ed3473c`); the author's decisions of 2026-11-01; Nogat's platform plan `docs/plans/2026-11-01-nogat-gui-platform.md` (pending; items 2, 3 and 5 to 8, steps 11 and 15); Nogat's pointer to this plan, `docs/plans/2026-11-02-hydrolog-gui.md` on Nogat's branch `plan/hydrolog-gui` (HUB-5.2, the order of the projects). No code before `Approved:`.

## Goal

A browser GUI, in Polish and in Nogat's visual identity, for people who compute with Hydrolog, built from the approved mockup:

- five sections: **Hydrogram zlewni** (one watershed; the result follows every change, no variants, no compute button), **Sieć i trasowanie** (the network drawn vertically with the outlet at the bottom; a click on a node opens its settings in „Dane”; an explicit „Oblicz sieć”), **Statystyka przepływów**, **Kalkulatory** and **Wszystkie polecenia** (forms generated from the catalog);
- the layout Dane | Wykresy | Wyniki, the light and the dark theme, the phone layout and the (i) explanations;
- export as CSV, JSON, the Markdown report and a print view (PDF from the browser), PNG and the CLI line; hand-off with Hydrograf as `nogat-handoff/1` carrying `hydrolog-network/1`;
- it runs alone (`hydrolog gui serve`, 127.0.0.1:8070 by default) and is a hosted module of Nogat's GUI platform, found through the entry point group `nogat.gui`;
- every hydrological value comes from the catalog (`run_command`); the browser formats, sums series for display and draws, and computes nothing else.

## Where it starts

Checked on 2026-11-01 in the `Hydrolog-routing` worktree (`feature/routing-schematic`, `2a5ba1a`) unless stated otherwise.

| Fact | Consequence |
|---|---|
| Routing is a linear stack of eight branches on `chore/nogat-2.1`, ending in `feature/routing-schematic`; nothing is merged ([PROGRESS](../PROGRESS.md), Next 1 and 8 to 10) | Sieć needs `route network`, so the GUI starts from that head |
| 44 commands in 15 groups. `hydrolog.catalog.run_command(name, options, *, allowed_dirs=None)` (`catalog/dispatch.py:436`) returns the `hydrolog-result/1` envelope. Measured: a warm in-process `hydrograph generate` takes about 1 ms (the first call 1.1 s, importing numpy and scipy), the CLI 1.4 s per call; `route network` on `hydrolog.testing.example_network_document()` 27 ms | live recompute calls the library in process, never the CLI |
| commands-1 entries carry `type`, `unit`, `required`, `default`, `enum` with meanings, `min`, `max`, `exclusive_minimum`, `items`, `path_role`, `examples`, Polish `i18n.pl` (summary, description, rules, option descriptions, enum meanings) and a command-level `one_of`; no `requires`, `excludes`, `section` or short labels | the form generator reads these fields; labels and group titles come from the GUI's texts |
| Catalog validation errors carry `details.option` and `reason` (`catalog/dispatch.py:12-34`); errors raised inside library classes often do not (`uh nash` with Lc > L: `"Lc_km (16.0) cannot exceed L_km (14.78)"`, `details: {}`); `message` and `hint` are English, only `title` follows `lang` (`exceptions.py:300-323`) | the GUI words errors in Polish from `code`, `reason` and `details`; the rest stands above the form |
| Library warnings become notices with the generic code `user_warning` and English text (10 `warnings.warn` calls in 6 files; `catalog/envelope.py:187-239`); routing and some operations already use their own codes (`tail_extended`, `tc_not_used`, `incomplete_years`) | stable codes come before Polish notices |
| `capture_warnings` serialises computations with a process-wide lock (`catalog/envelope.py:204,226`) | threads give no concurrency, and only a process can be stopped |
| No public `format_command` or `parse_command` (`cli/parser.py:683` is internal; AGI-2.1) | the CLI line needs them |
| `route network` returns `hydrolog-network-schematic/1` only when it writes the SVG (`operations/route.py:196-207`); no command lays a network out without routing it | Sieć cannot draw a network before „Oblicz sieć” |
| `hydrograph generate` returns P, Pe and Q and the UH's time to peak and peak, not its ordinates; `uh snyder` alone differs from the UH used inside (D equal to the step) | the UH chart needs the convolved UH in the result |
| `AGENTS.md` has 16,277 of its 16,384 bytes (`tests/contract/test_agent_guide.py:132`) | a new command must not add an index line |
| Starlette 1.10.0 and uvicorn 0.54.0 are already in `uv.lock` through `mcp`; httpx and Playwright are not | the `gui` extra adds no package to the lock |
| SCOPE: "❌ REST API" (`docs/SCOPE.md:354`); no web code in `src/` | the GUI needs a scope ADR |
| Nogat has no kit yet (`design/kit/`, platform step 2) and no `handoff-1` schema (step 1). `tokens.css` last changed at `29e7e1c`, the commit Hydrograf copied. The mockup, Hydrograf and the specimen store the theme as `nogat-theme` (`design/README.md` still says `theme`) | Hydrolog copies the tokens and marks with hashes; the hand-off schema is Nogat's step first |
| Archiwista vendors Preact 10.29.8 and htm 3.1.1 with SHA-256 per file (`src/archiwista/web/vendor/vendor.json`), imports them by relative paths under CSP `'self'`, and runs Playwright tests (`tests/e2e/`) in its gate and CI (`playwright install --with-deps chromium firefox`) | the frontend reuses that stack and test model |
| Hydrograf in production computes with Hydrolog 0.6.3 (`backend/requirements.txt`: `hydrolog @ git+…@v0.6.3`); its `feature/producer-heads` pins `2a5ba1a` | a hand-off from Hydrograf may carry numbers of another Hydrolog version |

## Decisions

### D1. Branch: `feature/gui` from `feature/routing-schematic`

`feature/gui` starts at `2a5ba1a` (worktree `Hydrolog-gui`); this plan is its first commit. Merging routing first needs the author's review (DEV-3.3; PROGRESS, Next 8 to 10) and the GUI need not wait for it: the stack is linear, so `feature/gui` is the next link and merges after `feature/routing-schematic` without a rebase if the routing branches merge unchanged. If the review changes them, `feature/gui` is rebased onto the new head; S0 limits its edits of routing code to `catalog/groups/route.py` and `operations/route.py` to keep that cheap. Hydrograf is not affected: production pins the tag `v0.6.3`, and `feature/producer-heads` pins `2a5ba1a`, the GUI's base.

### D2. Package and extra

`src/hydrolog/gui/` holds the server, `src/hydrolog/gui/web/` the static files (package data `gui/web/**`). Extra `gui = ["starlette>=1.10,<2", "uvicorn>=0.54,<1"]`, repeated in `all`; the dev group gains `httpx>=0.28,<1` (Starlette's `TestClient`) and `playwright>=1.64,<2`. The base install stays numpy, scipy and platformdirs. Starlette rather than FastAPI: the private routes of D5 need neither OpenAPI nor pydantic. Starlette rather than `http.server`: a maintained HTTP parser in front of a tunnel, client disconnects, `StaticFiles` and `TestClient`.

### D3. `hydrolog gui serve` through the catalog

A new group `gui` (`catalog/groups/gui.py`) with the command `gui serve` (`hydrolog.operations.gui_serve`); options `host` (default `127.0.0.1`), `port` (integer 1 to 65535, default `8070`), `no_browser` (boolean) and `check` (boolean). `--check` returns `hydrolog-plan/1` with `targets: []`, `url` and `port_free` without serving, so the catalog example runs in the contract tests. Two words, because catalog names are `<group> <command>` (`catalog/spec.py:101`, AGI-3.1); `hydrolog gui` alone prints the group's help, like `hydrolog route`. The command is in `commands list` and `commands schema` (Nogat's routes require it, HUB-2.9) but is neither an MCP tool nor a line of the command index in `AGENTS.md`: a new `Command` field `agent_tool: bool = True` is `False` for it, because it blocks and because the guide has 107 bytes left. Without the extra it raises `missing_dependency` with the hint `pip install "hydrolog[gui]"`. An address other than loopback adds the notice `exposed_without_auth`. Ctrl+C or SIGTERM stops it with exit 0 and the result `hydrolog-gui-serve/1` (`url`, `started_at`, `stopped_at`).

### D4. Hosting: the entry point `nogat.gui`, minimal

```toml
[project.entry-points."nogat.gui"]
hydrolog = "hydrolog.gui:gui_module"
```

`gui_module()` returns a frozen `GuiModule(name="hydrolog", title="Hydrolog", web=<path of gui/web>, index="index.html", sections=(("hydrogram", "Hydrogram zlewni"), ("siec", "Sieć i trasowanie"), ("statystyka", "Statystyka przepływów"), ("kalkulatory", "Kalkulatory"), ("polecenia", "Wszystkie polecenia")), app=create_app)`. A host mounts `app(work_root=…)` at a prefix of its own origin, or serves `web/` and answers the same routes from its catalog bridge. The page uses relative URLs only (`src/main.js`; `api/run/…` resolved against `document.baseURI`), so it works at `/` and under any prefix; the absolute paths of Archiwista and Hydrograf are what the platform plan found blocking. `?nogat=1` hides the top bar and the rail before the first paint (the platform's first-paint flag). The `postMessage` handshake, the host's theme and the shell's hand-off wait for the kit's `embed.js` (platform steps 1 to 3) and replace `src/host.js`, which knows the standalone mode only. The shape of `GuiModule` is a proposal to Nogat's steps 1 and 8.

### D5. Server API: private, generic, relative to the page

The routes serve this GUI only. They are not a REST interface of Hydrolog (no `/api/v1`, OpenAPI or stability promise; agents use the CLI, MCP and Python), a deviation from AGI §6 recorded in `CLAUDE.md`. They are generic over any commands-1 catalog, so Nogat's bridge can answer them for a hosted module; nothing in them is specific to Hydrolog's methods.

| Route | Request | Response |
|---|---|---|
| `GET api/session` | – | `hydrolog-gui-session/1`: version, limits, the session's files |
| `GET api/commands` | – | `hydrolog-command-list/1` from `list_commands()` without the excluded commands |
| `GET api/commands/{group}/{verb}` | – | `hydrolog-commands/1` from `command_schema` |
| `GET api/schemas/{file}` | – | a JSON Schema of `src/hydrolog/schemas/`, e.g. `hydrolog-network-1.schema.json` |
| `POST api/run/{group}/{verb}?channel=…&check=true` | the options as JSON; paths are `in/<name>` or `out/<name>` | `hydrolog-result/1`, or `hydrolog-error/1` with the registry's HTTP status and the Polish `title` |
| `POST api/format/{group}/{verb}` | the options | `hydrolog-gui-line/1` `{"line": …}` from `format_command` |
| `PUT api/files/in/{name}` | the file's bytes | `201` `hydrolog-gui-file/1` `{"path", "size_bytes", "sha256"}` |
| `GET`, `DELETE api/files/{in\|out}/{name}` | – | the bytes as an attachment; `204` |

`{group}/{verb}` rather than `{name}`: names contain a space, and the path mirrors the CLI and AGI-6.1. Excluded, answering `404 not_found`: `gui serve` (a server inside the server), `config show` (it shows the server's settings and paths) and `commands guide` (it writes agent guides).

```http
POST api/run/hydrograph/generate?channel=hydrogram
Content-Type: application/json

{"watershed": {"name": "Kamiennik — Świerzawa", "area_km2": 37.22, "perimeter_km": 40.89,
  "length_km": 16.05, "elevation_min_m": 257.3, "elevation_max_m": 475.1, "elevation_mean_m": 363.2,
  "mean_slope_m_per_m": 0.082, "channel_length_km": 14.78, "channel_slope_m_per_m": 0.0142, "cn": 65},
 "tc_method": "kirpich", "amc": "II", "hietogram_type": "beta", "total_mm": 105, "duration_min": 720,
 "alpha": 2, "beta": 5, "timestep_min": 10, "uh_model": "scs"}
```

```json
{"schema": "hydrolog-result/1", "tool": "hydrolog", "version": "1.0.0.dev0", "command": "hydrograph generate",
 "check": false, "status": "ok", "notices": [], "inputs": {"…": "…"},
 "result": {"schema": "hydrolog-hydrograph-generate/1", "peak_discharge_m3s": 60.2148, "time_to_peak_min": 380.0,
            "total_volume_m3": 1046213.2, "runoff_coefficient": 0.2678, "times_min": [0.0, 10.0, "…"], "…": "…"}}
```

An error, with the HTTP status 400 of `validation_error`:

```json
{"schema": "hydrolog-error/1", "code": "validation_error", "title": "Nieprawidłowe dane wejściowe",
 "message": "Option 'cn': must be <= 100, got 150",
 "details": {"option": "cn", "reason": "maximum", "maximum": 100, "value": 150.0},
 "exit_code": 2, "command": "hydrograph generate"}
```

A run replaced by a newer one, or stopped by the timeout, is the outcome `cancelled` of the envelope (AGI-4.2), not an error:

```json
{"schema": "hydrolog-result/1", "tool": "hydrolog", "version": "1.0.0.dev0", "command": "hydrograph generate",
 "check": false, "status": "cancelled", "result": null,
 "notices": [{"level": "info", "code": "superseded", "message": "A newer run of the same channel replaced this one."}]}
```

The server rewrites every absolute path of the work directory in the envelope (`inputs`, `result.files`, result fields) relative to it, so no server path reaches the browser.

### D6. Execution: warm worker processes, the newest run wins

- Two worker processes (spawn) start with the server and import numpy, scipy and `hydrolog.operations` once, with `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS` and `MKL_NUM_THREADS` at 1. A run is `run_command(name, options, allowed_dirs=[session directory])` in a worker; a failure becomes `error_document(exc, name, "pl")`.
- A run names its `channel` (`hydrogram`, `hydrogram-cli`, `siec`, …). A newer run of the same session and channel cancels an older one that is still queued (`superseded`); one already running finishes (milliseconds) and the client ignores it. The client also debounces (D13) and aborts its older `fetch`.
- A run longer than 30 s kills its worker, which is replaced; the run is `cancelled` with the notice `timeout`. On POSIX each worker has `RLIMIT_AS` of 2 GiB.
- Rejected: threads, which `capture_warnings` serialises anyway and which cannot be stopped; the CLI per call (1.4 s) for live recompute.

### D7. Files: one work directory per browser session

- A random session id lives in the cookie `hydrolog_gui` (HttpOnly, SameSite=Strict, the page's path); its directory `<tmp>/hydrolog-gui-<pid>/<id>/` (mode 0700) holds `in/` (uploads and the documents the GUI writes) and `out/` (outputs of commands).
- A path option takes only `in/<name>` or `out/<name>`, `<name>` matching `[A-Za-z0-9][A-Za-z0-9._ -]{0,127}`; an option with `path_role: output` takes only `out/`. Anything else is `403 forbidden` before the run, and `allowed_dirs` checks again inside it.
- Limits: 20 MiB per file; 100 MiB and 200 files per session; 5 MiB of JSON per request; 64 sessions, the least recently used idle one removed first; idle sessions removed after 12 h, all of them at shutdown.
- No arbitrary paths, no file browser, no store: what a command reads is uploaded.

### D8. Security of the standalone server

- It binds `127.0.0.1` by default and has no sign-in. Reachable beyond loopback (a LAN, a tunnel), anyone who reaches it can use it: expose it only behind an authenticating proxy (Cloudflare Access, the platform's front door), as the notice of D3 and `docs/USAGE.md` say. Session directories keep users' files apart; the limits of D7 bound the cost.
- Headers of every response: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy: same-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`; `Cache-Control: no-cache` on static files (revalidated, as in Archiwista) and `no-store` under `api/`.
- `POST`, `PUT` and `DELETE` are refused (`403 forbidden`) when `Sec-Fetch-Site` is `cross-site` or `same-site`; `run` and `format` require `Content-Type: application/json`, which a cross-site page cannot send without a preflight that fails (no CORS headers).
- DNS rebinding gives an attacker only a session of its own (cookies are per host), so no Host allow-list is needed.
- Framing the standalone server from a shell origin (A1's `shell_origin`) is not needed by a hosted module and is left out.

### D9. Frontend stack and structure

Preact 10.29.8, htm 3.1.1 and `preact/hooks` as ES modules without a build (DEV-15.1), vendored byte-identical with Archiwista's files and in the same `vendor.json` format (source tarball, integrity, SHA-256 per file, the one rewritten import of `hooks.mjs`), licence files kept. No reason was found to depart from it: the generated forms and node editors need components and state that the mockup's classic script does not give. UI texts are modules under `src/labels/` keyed by English ids (DEV-2.3, Archiwista's layout). Polish only; an English UI comes later (a deviation from DEV-2.2 recorded in `CLAUDE.md`). Numbers through `Intl.NumberFormat("pl-PL")`: decimal comma, a non-breaking space between thousands from five digits; inputs accept a comma or a dot.

```
src/hydrolog/gui/web/
  index.html theme-init.js              # theme and ?nogat=1 before the first paint (key nogat-theme)
  nogat/     tokens.css marks/*.svg nogat.json      # copies of Nogat 29e7e1c with SHA-256 (D10)
  vendor/    preact/ htm/ vendor.json
  css/       app.css charts.css print.css           # tokens only
  examples/  kamiennik.json siec.json maksima_roczne.csv
  instrukcja/                                       # the guide (S7)
  src/
    main.js app.js router.js host.js store.js api.js format.js persist.js
    labels/  common.js shell.js errors.js notices.js options.js units.js groups.js exports.js
             hydrogram.js siec.js statystyka.js kalkulatory.js polecenia.js
             info/{tc,losses,uh,rain,routing,stats}.js        # (i) texts (D16)
    ui/      top-bar.js rail.js view-layout.js sheet.js status.js info.js menu.js toast.js seg.js
             table.js export-panel.js
    controls/ number-field.js choice-field.js series-field.js file-field.js json-field.js
    forms/   model.js command-form.js result-view.js
    charts/  scale.js axes.js series.js chart.js png.js
    handoff/ handoff.js mapping.js handoff-panel.js
    sections/ index.js hydrogram/ siec/ statystyka/ kalkulatory/ polecenia/
```

The parts the platform's kit will take over (`forms/model.js`, `charts/scale.js`, the layout transform in `sections/siec/schematic.js`, `ui/info.js`) are pure modules without Preact, so that a kit component can wrap them; Hydrolog switches to the kit's copies when they exist (platform steps 2, 3 and 7). A section directory holds `index.js` (its `ViewLayout`), `state.js` (inputs, defaults, persistence and `toOptions`), `data-panel.js`, `charts.js` (chart specs), `results-panel.js` and `export.js` (its export spec). Each section keeps its inputs in `localStorage` (`hydrolog-gui/<section>/1`, no results), with „Wyczyść” to start again; a first visit opens the shipped examples.

### D10. Nogat's identity

`tokens.css` is copied from Nogat `29e7e1c` with the commit in its header comment (DEV-15.3), with `marks/hydrolog.svg` (favicon and top bar), `marks/hydrograf.svg` (hand-off buttons) and `marks/nogat.svg`; `nogat/nogat.json` records the source, the commit and the SHA-256 of each file, and a contract test refuses a modified copy. The shell follows the mockup and `design/README.md`: the top bar (mark, „Hydrolog”, breadcrumbs, the status badge, „Instrukcja”, the theme switch Auto, Jasny, Ciemny), a 64 px rail with five items (a 58 px bottom bar on phones), `.view-layout` with resizable left (260 to 560 px, 300 by default) and right (340 to 720 px, 400) panels that keys also resize, and bottom sheets at 860 px and below. The theme key is `nogat-theme`, as in the mockup, Hydrograf and the specimen; a hosted module then shares the host's choice through the origin's storage.

### D11. The catalog form generator

`forms/model.js` turns one `hydrolog-commands/1` entry into fields:

| commands-1 | Control and rule |
|---|---|
| `number`, `integer` with `unit`, `min`, `max`, `exclusive_minimum`, `default` | a number with its unit (`km2` shown as km²), decimal comma or dot, the default as placeholder and „domyślnie 0,2”; Polish messages for the bounds |
| `string` with `enum` (meanings from `i18n.pl.enum`) | up to four values a segmented control, more a select; the meaning of the chosen value below |
| `boolean` | a checkbox (`force` as „Zastąp istniejące”, `check` as „Tylko plan”) |
| `array` of `number` | a series: pasted from a spreadsheet or text, or a CSV file read in the browser; the count and the bounds of each value |
| `array` of `string` | chips |
| `object` | a JSON editor with parse errors (sections use editors of their own) |
| `path_role: input` | one of the session's uploaded files, or a new upload (`in/<name>`) |
| `path_role: output` | a file name in `out/`, by default the basename of the first catalog example's value; the result lists the downloads |
| command-level `one_of` | a segmented „Sposób podania” with one pane per group; only the chosen group is sent, and all its options are required |
| `required` | a mark and „Wymagane” |
| `requires`, `excludes`, `section`, `format` (the optional fields the platform plan adds to commands-1) | honoured when present; Hydrolog has none, a fixture command tests them |

Labels come from `labels/options.js` by option name, otherwise the option name in monospace; the Polish description is the help text, as the mockup shows label and key together. Server errors are placed by `details.option` and worded from `reason` (`labels/errors.js`); without `option` they stand above the form. The CLI line under the form is formatted by the server, debounced. Polecenia runs on its button; the generic `forms/result-view.js` shows notices, scalars with units from their name suffixes (`_km2`, `_min`, `_m3s`, `_mm`, `_pct`, `_m_per_m`), series as a chart and a table, the targets of a plan, files to download and the JSON.

### D12. Charts: an own SVG module

Inline SVG drawn by `charts/`, styled by CSS classes on the tokens: the mockup's look, and a theme switch without redrawing. Chart.js was rejected: a canvas (PNG and print want SVG), no probability paper, re-styling on every theme change, about 200 kB to vendor. The module has linear and log axes, a Gumbel probability axis for the flood frequency plot, rounded ticks in Polish numbers, lines, steps, bars (the hyetograph hanging from the top on a second axis), areas, points, peak and reference marks, a legend, a readout by pointer and keys, and `toPng(svg, {scale: 2})` (computed styles inlined, an Image from a `blob:` URL, a canvas).

### D13. Live recompute, in Hydrogram zlewni only

Each change validates its field against the catalog's bounds (for the fields inside the `watershed` object, those of `watershed` in `hydrolog-network-1.schema.json`). When the data are valid, a run on channel `hydrogram` is scheduled 250 ms later, and every further change restarts the delay. The badge says „Liczenie…” after 150 ms (`aria-busy`, results dimmed), „Wynik aktualny” when the newest response is in, „Dane niepełne” with the field when the data are invalid (no run; the last result stays, marked), „Błąd danych” with the message after a server error. Only the response of the newest run is applied (a sequence number). Nash by Lutz runs `uh nash` first and passes `nash_n` and `nash_k_min` on, because `hydrograph generate` has no `nash_estimation`. Sieć, Statystyka, Kalkulatory and Polecenia compute on their button and mark their results stale after a change („Dane zmienione: oblicz ponownie”).

### D14. Exports

| Export | How |
|---|---|
| CSV | written in the browser: the hydrograph as `time_min,discharge_m3s,precipitation_mm,effective_precipitation_mm` (comma separator, decimal dot, UTF-8), a valid input of every `route` command and of Hydraulik (`hydrolog-hydrograph-csv`); Sieć one node or all nodes as columns; Statystyka the quantiles |
| JSON | the envelope as received (`<subject>.result.json`); Sieć also the network document |
| Markdown report | `report generate` with the section's options and `output: out/<subject>.md`, then the download |
| Print, PDF | „Drukuj”: `print.css` puts the section's charts, parameters, notices, provenance and CLI line on A4; PDF is the browser's „Zapisz jako PDF”. Hydrolog adds no PDF output |
| PNG | `toPng` of the chart shown; in Sieć the schematic as drawn |
| SVG | Sieć: Hydrolog's own schematic (`route network` with `schematic: out/<subject>.svg`) |
| CLI line | `format_command` with the options as the user gave them (`in/x.csv` shown as `x.csv`), wrapped at ` --` with `\` for display and copied as shown |

### D15. Hand-off

`nogat-handoff/1` exactly as Nogat publishes it (the platform plan's item 6, Nogat's step N1 in the pointer plan, before S6), copied to `schemas/nogat/handoff-1.schema.json` like the agent schemas (ECO-050); Hydrolog never defines it. The payload is `hydrolog-network/1`: Hydrogram writes one `subcatchment` from rainfall and the `outlet`, Sieć its whole network. `provenance` names the source of the rainfall (the PMAXTP probability and duration as typed, or the hyetograph) and of the watershed; `result` carries the peak, the time to peak and the volume. Standalone: „Plik przekazania” (a download), „Do schowka” and „Wczytaj z Hydrografa” (a file or the clipboard); embedded, through the shell once it exists (D4). A hand-off with one subcatchment opens in Hydrogram, with more in Sieć; the producer's version and result are shown beside Hydrolog's own (Hydrograf computes with Hydrolog 0.6.3). Field names are Hydrolog's (`channel_length_km`; slope in m/m with a % hint); mapping Hydrograf's names (`Lc_km`, %) is Hydrograf's side (platform step 12).

```json
{"schema": "nogat-handoff/1", "created_at": "2026-11-02T10:15:00Z",
 "producer": {"tool": "hydrolog", "version": "1.0.0.dev0", "page": "#hydrogram"},
 "subject": "Kamiennik — Świerzawa",
 "provenance": {"rainfall": {"source": "pmaxtp", "probability_percent": 1, "duration_min": 720},
                "watershed": {"source": "hydrograf", "latitude": 51.0154, "longitude": 15.89}},
 "payload": {"schema": "hydrolog-network/1", "name": "Kamiennik — Świerzawa", "timestep_min": 10,
   "nodes": [{"id": "Z1", "type": "subcatchment",
              "watershed": {"area_km2": 37.22, "perimeter_km": 40.89, "length_km": 16.05, "…": "…", "cn": 65},
              "runoff": {"model": "curve-number", "tc_method": "kirpich", "amc": "II", "uh_model": "scs"},
              "rainfall": {"kind": "design", "hietogram_type": "beta", "total_mm": 105.0,
                           "duration_min": 720.0, "alpha": 2.0, "beta": 5.0}},
             {"id": "OUT", "type": "outlet", "from": ["Z1"]}]},
 "result": {"command": "hydrograph generate", "peak_discharge_m3s": 60.2148, "time_to_peak_min": 380.0,
            "total_volume_m3": 1046213.2}}
```

The envelope's fields follow Nogat's schema when it lands. The mapping between Hydrogram's options and the node lives in `handoff/mapping.js` and is tested by routing the payload: its outlet peak equals that of `hydrograph generate`.

### D16. Texts: (i), notices, errors

- The (i) explanations are Polish HTML fragments in `src/labels/info/*.js`: title, what it is, the formula in MathML, the variables with units, applicability ranges as data (`{option, min, max, source}`, marked ok or warn against the current value in the popover) and sources. They are written now in the GUI, adapted from Hydrograf's sourced texts where the topic matches; they move to the kit's `info.js` later, and the ranges to Hydrolog notices in a later plan. The fragments are trusted repository files rendered as HTML; a test refuses scripts, inline styles, event attributes and remote URLs in them.
- Notices: S0 gives every notice Hydrolog emits a stable code and, where its text holds values, `details` (an optional field; result-1 leaves notice objects open), listed in an enumerable registry `NOTICES`. `labels/notices.js` words each code in Polish, and a test fails for a code without Polish text; an unknown code shows the English message marked „(EN)”.
- Errors: Polish from `code`, `reason`, `option`, `allowed`, the bounds and `groups`, under the registry's Polish `title`; the English `message` is the fallback. A library error without `details.option` (Lc > L) stands above the form; giving such errors an `option` is a later change, not a prerequisite.

### D17. Tests

- Python, in the gate, offline, with no new marker: unit tests of the sessions, paths and runner (supersede, timeout, kill, respawn); integration tests through Starlette's `TestClient` of every route, limit, header and error status, and of the app mounted under a prefix; contract tests of the hashes of the vendored and copied files, of no remote URL and no inline script or style in `web/`, of the examples (`siec.json` equals `hydrolog.testing.example_network_document()`), of the hand-off schema, and of `NOTICES` against the Polish texts.
- Browser: Playwright for Python with Chromium in `tests/e2e/` (Archiwista's model): a live server on a free port, a page that fails a test on any console error or `securitypolicyviolation`, widths 1440 and 390, both themes. Pure JavaScript modules (numbers, the form model, scales, the hand-off mapping) are tested through `page.evaluate(import(…))`, so there is no Node toolchain. CI installs Chromium on all three systems (`uv run --no-sync playwright install --with-deps chromium`); the gate needs it locally too (`CLAUDE.md`).
- Each slice's acceptance below is proved by its own tests; the coverage floor of 80 % holds.

### D18. Deviations from the mockup

- PMAXTP's „Pobierz” and the series „Z Archiwisty” are left out: Hydrolog downloads nothing; the depth is typed or comes with a hand-off, and fetching through IMGWTools or Archiwista belongs to the platform's modules.
- „Instrukcja” in the top bar (Hydrograf's pattern) opens the guide.
- A cross-field error without `details.option` stands above the form, not on its field.
- „Raport do druku” is the print view of D14, not a rendered Markdown file.
- The network's structure (adding, removing or reconnecting nodes) is not edited; it comes from a file, a hand-off or the example.
- The switch „Makieta: Samodzielnie | W Nogacie” was a mockup control; the mode comes from D4.

## Interfaces fixed by this plan

Python (S0, S1):

```python
# hydrolog.catalog, public (AGI-2.1); the two functions also in hydrolog.__all__
def format_command(command: str, options: Mapping[str, Any] | None = None,
                   run: Mapping[str, Any] | None = None) -> str: ...
def parse_command(line: str) -> ParsedCommand: ...       # .command, .options, .run
NOTICES: Mapping[str, NoticeSpec]                       # code -> level, English template, details keys
# hydrolog.operations
def route_schematic(*, network=None, network_file=None, main_stem=None) -> RouteSchematicResult: ...
def gui_serve(*, host="127.0.0.1", port=8070, no_browser=False, check=False) -> OperationOutput: ...
# hydrolog.gui
def gui_module() -> GuiModule: ...
def create_app(*, work_root: Path | None = None, workers: int = 2, run_timeout_s: float = 30.0) -> Starlette: ...
def serve(*, host: str, port: int, open_browser: bool) -> dict[str, Any]: ...  # blocks; url, started_at, stopped_at
```

- `route schematic` (read-only; `network` or `network_file`, `main_stem`) returns `hydrolog-network-schematic/1` without values and without writing a file.
- The result of `hydrograph generate` gains `uh_times_min` and `uh_discharge_m3s_per_mm`, the unit hydrograph used in the convolution (optional fields; schema regenerated).

JavaScript (S2, S2b, S6), every exported function with JSDoc:

```js
// src/api.js
api.session(); api.commands(); api.command("uh nash"); api.schema("hydrolog-network-1.schema.json");
api.run("hydrograph generate", options, {channel, check, signal}); // envelope; throws ApiError {status, doc}
api.format("uh nash", options);        // the CLI line
api.upload(file, name);                // {path, size_bytes, sha256}
api.fileUrl("out/x.md"); api.remove("in/x.csv");
// src/store.js: state shared by sections
useStore("watershed"); // Hydrogram's watershed, the `watershed` of hydrolog-network/1; Kalkulatory reads it
useStore("reference"); // {label, peak_m3s, source}: a Statystyka quantile drawn on the hydrograph
useStore("status");    // the active section's badge: ok | busy | stale | invalid | error, with its text
// src/ui/view-layout.js
html`<${ViewLayout} left=${{title, sub, body, foot}} center=${{bar, body}} right=${{title, body}} />`
// src/forms/model.js, src/forms/command-form.js
fieldModel(commandDoc, {labels, hide, values}); // {fields, groups, oneOf}
validate(model, values);                        // {option: message}
toOptions(model, values);                       // the options to send
html`<${CommandForm} command=${doc} values=${values} onChange=${set} errors=${errors} hide=${[]} />`
// src/ui/export-panel.js
html`<${ExportPanel} spec=${{subject, csv: () => text, json: () => obj, chart: () => svg,
                             cli: {command, options}, report: {command, options}, files}} />`
// src/charts/chart.js, src/charts/png.js
html`<${Chart} spec=${{x: {label, scale}, y: {label}, y2, series: [{id, kind, data, axis, cls, label}],
                       marks, legend, readout}} />`
toPng(svgElement, {scale: 2}); // Promise<Blob>
// src/handoff/handoff.js
buildHandoff({subject, provenance, payload, result, page}); // the document
readHandoff(text);  // {doc, target: "hydrogram" | "siec", problems}
// src/sections/<id>/index.js, registered by one line in src/sections/index.js
export default function Section() {}
```

## Steps

Producers before consumers: Nogat's hand-off schema (N1), then the catalog (S0), the server (S1), the foundation (S2, S2b), the sections (S3 to S5), the hand-off and print (S6), the guide, docs and the final smoke (S7). Each slice is one agent on its own branch `feature/gui-<slice>` and worktree, started from `feature/gui`, with the gate green before every commit. A slice edits only the files it owns and its own `docs/CHANGELOG.md` entry. The coordinating session lands slices by rebasing them onto `feature/gui` and fast-forwarding it (no merge commits, nothing pushed; DEV-3.3), resolves the CHANGELOG conflicts, runs the gate and updates `docs/PROGRESS.md`. Sizes are in sessions.

| Slice | Owns | Provides | Acceptance | Size | After |
|---|---|---|---|---|---|
| **S0** catalog additions | `catalog/groups/{gui,route}.py`, `catalog/groups/__init__.py`, `catalog/{spec,envelope,lines,notices}.py`, `catalog/__init__.py`, `__init__.py`, `cli/parser.py`, `operations/{gui,route,hydrograph}.py`, the files with `warnings.warn`, `mcp/_tools.py`, `agent_guide.py`, the regenerated schemas, `AGENTS.md`, `llms.txt`, ADR-0014 (the GUI enters the scope: D2 to D8), ADR-0015 (the catalog additions), `docs/DECISIONS.md`, `docs/SCOPE.md`, `docs/PRD.md` (section 2.16), their tests | `format_command`, `parse_command`, `NOTICES`, `route schematic`, the UH ordinates, `gui serve` (its check path; serving calls `hydrolog.gui.server.serve`) | every catalog example survives `format_command(parse_command(call))` and runs; no notice of any example is `user_warning`; `route schematic` equals `RoutingNetwork.schematic()`; the UH ordinates convolved with Pe give Q; `gui serve --check` plans; `AGENTS.md` within 16 KiB; `gui serve` absent from MCP `tools/list` | 1.5-2 | the plan |
| **S1** server | `src/hydrolog/gui/*.py`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `CLAUDE.md`, `tests/unit/gui/`, `tests/integration/gui/`, `tests/e2e/conftest.py` | the API of D5 to D8, `gui_module`, `serve`, the e2e fixtures | `TestClient` tests of every route, limit, header, refused path, error status, supersede, and timeout with respawn; the app mounted at `/m/hydrolog/` serves the page and the API; `hydrolog gui serve --no-browser` answers on 8070 and stops with exit 0; the `nogat.gui` entry point loads | 2-2.5 | the plan (S0 for the CLI) |
| **S2** foundation | `web/{index.html,theme-init.js}`, `web/nogat/`, `web/vendor/`, `web/css/app.css`, `web/src/*.js`, `web/src/{labels,ui,controls,forms}/` (not the section files of `labels/`), `web/src/sections/{index.js,polecenia/}`, `tests/e2e/test_{shell,polecenia,js_units}.py`, `tests/contract/test_gui_web.py` | the shell, theme, router, API client, store, controls, form generator, result view, export panel (CSV, JSON, CLI line, files), the (i) popover and its registry, Polecenia | Polecenia lists 43 commands (46 after S0, less the 3 excluded) under Polish group titles, with search; the `scs effective` and `uh nash` forms reproduce the mockup's validation (allowed values with meanings, `one_of` groups, bounds) and run; upload and download; both themes at 1440, 1180 and 390 px without horizontal scrolling; no console error or CSP violation; the copies' hashes match | 3-3.5 | S1 for the e2e tests |
| **S2b** charts | `web/src/charts/`, `web/css/charts.css`, `tests/e2e/test_charts.py` | `Chart`, `toPng` | scales, ticks and the probability axis tested as pure functions; a hydrograph with hyetograph and peak, a UH and a probability plot render in both themes; the readout works by keys; `toPng` returns a PNG twice the drawn size | 1.5-2 | the plan |
| **S3** Hydrogram zlewni | `web/src/sections/hydrogram/`, `web/src/labels/hydrogram.js`, `web/src/labels/info/{tc,losses,uh,rain}.js`, `web/examples/kamiennik.json`, `tests/e2e/test_hydrogram.py` | the five steps (watershed, also read from a WatershedParameters JSON in the browser; tc; rainfall; losses; UH), live recompute, the charts (hydrograph with hyetograph, cumulative P, F and Pe, UH), the table, balance, parameters, notices, the export spec, the CLI line, `store.watershed` | the Kamiennik example shows „60,21 m³/s” at „6:20” and „1 046 213 m³”; switching the tc method, AMC and UH model reproduces the mockup's runs; an invalid CN shows on its field and keeps the last result; ten fast edits send at most two runs and show the last; the CLI line run by the CLI gives the same peak | 2.5-3 | wave A |
| **S4** Sieć i trasowanie | `web/src/sections/siec/`, `web/src/labels/siec.js`, `web/src/labels/info/routing.js`, `web/examples/siec.json`, `tests/e2e/test_siec.py`, `tests/contract/test_gui_example_network.py` | loading a network (with its referenced files) or the example; the vertical schematic from `route schematic` (grid transposed so the outlet is at the bottom, labels on the side without a tributary); selection by click, Enter or Space and in the node table; node forms per type and reach method from `hydrolog-network-1.schema.json`, with a rating table editor; „Oblicz sieć” (`route network` on the document written to `in/`); results per node (chart and parameters); the stale badge | the schematic is drawn before the first run; the example's outlet values equal `route network`'s; every node type opens its form; a changed reach method shows its options and marks results stale; the SVG and the network document export | 3 | wave A |
| **S5** Statystyka, Kalkulatory | `web/src/sections/{statystyka,kalkulatory}/`, `web/src/labels/{statystyka,kalkulatory}.js`, `web/src/labels/info/stats.js`, `web/examples/maksima_roczne.csv` (the years 1998 to 2023 of `tests/fixtures/annual_maxima.csv`, as in the mockup), `tests/e2e/test_{statystyka,kalkulatory}.py` | flood frequency from a file (columns from its header, `date_column` for daily series) or pasted values; distributions and return periods; the probability plot and tables; „Do porównania” (`store.reference`); 16 calculators: the tc comparison (six `tc watershed` runs, bars coloured and worded by their notices) and single calculators as catalog forms prefilled from `store.watershed` | the sample gives the mockup's GEV „Q1% 307,3 m³/s” and the KZGW notice in Polish; the tc comparison lists six methods with their range words; a calculator's CLI line and result match the CLI's | 2 | wave A (S3 for the tc texts) |
| **S6** hand-off, report, print | `web/src/handoff/`, `web/css/print.css`, `schemas/nogat/handoff-1.schema.json`, the mount lines in the results panels of Hydrogram and Sieć, `tests/e2e/test_exports.py`, `tests/contract/test_gui_handoff.py` | D14's report and print, D15 | a hand-off from Hydrogram validates against Nogat's schema and reopens with the same values, and its payload through `route network` gives the same outlet peak; a two-subcatchment hand-off opens in Sieć; the Markdown report downloads; the print view fits A4 | 1.5-2 | wave B, N1 |
| **S7** guide, docs, smoke | `web/instrukcja/`, the „Instrukcja” item of the top bar, `docs/USAGE.md`, `docs/INTEGRATION.md`, `README.md`, `tests/e2e/test_smoke.py` | the guide in Polish, starting in plain words (what the GUI is, that the results are estimates, a glossary, a first result in three steps), then each section; a „GUI” section in USAGE in English, also starting in plain words, with running it as a service behind an authenticating proxy; the hand-off and hosting in INTEGRATION | every section opens without console errors in both themes and on a phone; the guide's examples are the shipped examples | 1.5-2 | wave B (S6 for its pages) |

Waves: **A** = S0, S1, S2, S2b in parallel (landing order S0, S1, S2b, S2; S2 and S2b rebase on S1 before their e2e tests); **B** = S3, S4, S5 (landing order S3, S4, S5; each adds its line to `sections/index.js`); **C** = S6, S7. In total about 18.5 to 22.5 sessions, about 8 to 9 on the critical path. Nogat: N1 (the hand-off schema, 0.5) before S6; N2 (the registry: Hydrolog's `gui` interface and a route „Open Hydrolog's GUI in the browser”, then `agents`) after S0 lands.

## Deployment for the author

The service runs the integration worktree `Hydrolog-gui` with `uv sync --locked --all-extras`, so `soil hsg` works as well.

1. After wave A, the omp service `hydrolog-gui` (persistent) replaces `hydrolog-placeholder`, which is stopped first because both bind 8070: `uv run --no-sync hydrolog gui serve --no-browser` in `Hydrolog-gui`, ready on port 8070 and the log line `Hydrolog GUI: http://127.0.0.1:8070/`. It is restarted after each landing.
2. Smoke through the tunnel's public address after each wave: the page loads with Hydrolog's mark; `curl -sI` shows the CSP of D8; the theme switch works; in Polecenia `uh nash` with Lc > L shows the error and a valid run its result; a CSV uploads and downloads. After wave B: Hydrogram shows „60,21 m³/s” and recomputes after a CN change; Sieć's example computes; Statystyka's sample and the tc comparison work. After wave C: the hand-off file round trip, the Markdown report, the print preview and the PNG. Every time: a phone at 390 px and no console errors.
3. Until the public address has Cloudflare Access (question 1), the page is open to anyone who has the address.

## Risks

| Risk | Effect | Mitigation |
|---|---|---|
| The routing review changes the routing branches | `feature/gui` must be rebased | S0 touches two routing files; the rest of the GUI adds files |
| The platform plan changes the kit, the hand-off or hosting | rework of `host.js`, `handoff/` and `nogat/` | those parts are small and isolated; the pure cores of D9 move into the kit |
| Exposure through the tunnel without Access | anyone computes and uploads | Access (question 1); limits, per-session directories, no server paths, excluded commands |
| A runaway computation | a stuck worker | timeout with kill and respawn, a memory limit, two workers |
| Playwright on three CI systems | slow or flaky CI | Chromium only; Archiwista's fixtures as the model |
| New notice codes without Polish text | English notices in the GUI | the `NOTICES` contract test |
| Own SVG charts and the probability axis | effort | a slice of their own (S2b), pure-function tests |
| Parallel slices of one branch | conflicts | owned files, one integration owner, a rebase and the gate per landing |
| Hydrograf's Hydrolog 0.6.3 against 1.0.0.dev0 | different numbers for the same inputs | the hand-off shows the producer's version and result beside Hydrolog's |

## Open questions for the author

1. Is the tunnel's public address (it points at 127.0.0.1:8070) behind Cloudflare Access? The GUI has no sign-in by design (D8); without Access anyone with the address can use it within the limits. Needed before the deployment through the tunnel is called done.
2. Nogat's N1 (the `handoff-1` schema of the platform plan's item 6) ahead of the rest of the platform plan: approved with this plan? Without it S6 waits; everything else proceeds.

Decided here, open to the author's veto: the mockup's open questions 2 to 6 (the (i) texts in the GUI now; notice codes now and option names in library errors later; m/m with a % hint; no variants; print instead of a PDF output). Its question 1, where Hydrolog's sections sit inside Nogat, is the shell's to answer; `GuiModule` lists them.

## Results

Done on 2026-11-02. Every slice landed on `feature/gui` as a fast-forward (rebased where needed; no merge commits, nothing merged into another branch or pushed) in the order of the table, and the gate passed after each wave. From wave B on, each slice's own tests and the whole `tests/e2e` passed in its worktree before it landed; wave A's browser tests were completed on the landed slices.

| Slice | Commits | Notes |
|---|---|---|
| Plan | `fba6ff0` | |
| S1 server | `4b1560f` | |
| S0 catalog additions | `49b0d18` | ADR-0014 and ADR-0015 |
| S2 foundation | `c47baca` | |
| S2b charts | `c7b92ae` | |
| Glue of wave A | `ac244ef`, `3850757`, `848b73a`, `a98a957`, `e004a5d` | the direct imports once S0 and S1 were both in, the web and chart tests against the landed slices, defects of the page found by its browser tests, the browser tests of the shell, Polecenia and the modules, `--no-browser` |
| S3 Hydrogram zlewni | `8fed313`, `e4ee1d6` | |
| S4 Sieć i trasowanie | `6b23ac0`, `6779ee6`, `6369278` | |
| S5 Statystyka, Kalkulatory | `a59d3be` | |
| Glue of wave B | `d137e17`, `83ddb40` | the labels of the tc tile in hours and of a file over the limit; every section mounts at start, and Kalkulatory relies on it |
| S6 hand-off, report, print | `03604d5`, `d2b704b` | `d2b704b` makes S5's Kalkulatory test wait for Hydrogram's first result (a race once S6 loaded more modules) |
| S7 guide, docs, smoke | `6d93e6a`, `5a131f1` | |
| Glue of wave C | `ff5be68`, `f2d9b04` | the guide, INTEGRATION, USAGE and the README describe the hand-off, the report and the print view as shipped (S7 was written before S6), with a picture of the exports; the received hand-off's comparison fits the panel Wyniki (it was 358 px wide in 343 px at 1440 px and in 283 px at 1240 px) |

`docs/PROGRESS.md` followed each wave (`9d2f0e2`, `9b9a8cf` and the commit of these Results). Nogat's steps are on Nogat's branches for the author's review: N1 `a01097c` (`feature/handoff-1`), the envelope `nogat-handoff/1` (`schemas/exchange/handoff-1.schema.json`), which S6 copied unchanged; N2 `33920ec` (`feature/hydrolog-gui-registry`, after N1), the registry's optional `gui` interface with `hydrolog gui serve` and the route „Open Hydrolog's GUI in the browser”. Question 2 is answered by N1 done ahead of the rest of the platform plan; question 1 stays open.

Verification. `scripts/gate.sh` on `f2d9b04`: ruff format and check, mypy, pytest 6593 passed and 18 skipped with the browser tests, coverage 95.09 %, the commit check. The omp service `hydrolog-gui` (persistent; `uv run --no-sync hydrolog gui serve --no-browser --host 127.0.0.1 --port 8070` in `Hydrolog-gui`, `TMPDIR` on the data disk) was restarted after every wave; only it listens on 127.0.0.1:8070, and `curl -I` shows the headers of D8. The smoke after wave C ran in clean Chromium contexts against 127.0.0.1:8070, the tunnel's origin:

- the welcome dialog on a first visit, „Otwórz instrukcję” opening the guide at „Na start” in a new tab, „Przejdź do aplikacji”;
- Hydrogram zlewni 60,21 m³/s at 6:20 h, 1 046 213 m³, and AMC III recomputed by one run without a button: 115,23 m³/s; Sieć's schematic of 8 nodes before the run, a node's form, „Oblicz sieć” 19,1 m³/s at 2:25 h; Statystyka GEV, Q 1% = 307,3 m³/s; Kalkulatory's six tc methods (Kirpich 162,9 min); Polecenia's `uh nash`;
- the PNG of the chart, the Markdown report, a hand-off written in one browser (AMC III) and read in another with the same result and „Wynik producenta zgodny z wynikiem Hydrologa.”, then written again equal but for `created_at`; „Raport do druku” printing in the light theme with every part open, on 4 A4 pages;
- a 390 px phone in the dark theme: every section and the guide, nothing scrolling sideways;
- 22 documents without a console error or warning, a page error, a CSP violation, a failed request or an HTTP status of 400 or more (the capture was checked with a deliberate CSP violation, console error and exception).

Departure from the text above: the print button of D14 is „Raport do druku” (format PDF), beside „MD Raport”, not „Drukuj”.

Left for the author: the review and merge of the routing branches and then of `feature/gui` (DEV-3.3; PROGRESS, Next 8 to 11), with Nogat's N1 and N2; Cloudflare Access on the tunnel's public address (question 1), until which anyone with the address can use the GUI within the limits of D7; Hydrograf's „Wczytaj z Hydrologa” and „Przenieś do Hydrologa” come with the platform's step 12 and its own plan, and the hand-off through Nogat's shell with the kit. Small follow-ups are listed in PROGRESS, Next 12.

## Erratum 2026-11-04: Hydrogram zlewni in three steps, without the example

The author's decision of 2026-11-04 (on the review of the hydrograph flow) supersedes the parts of D13 and S3 below; the rest of D13 (validation as the field is typed, the 250 ms debounce, „Liczenie…”, the newest response only, Nash by Lutz first) stands.

- **Steps.** The panel Dane of Hydrogram zlewni has three steps instead of the mockup's five: 1 Zlewnia (the watershed's basic fields, CN included), 2 Hietogram (the former „Opad”), 3 Hydrogram (the unit hydrograph model, none chosen at first; only the chosen model's block, with tc and the tc method's own fields for SCS and Clark and the watershed fields the model reads, then „Straty SCS-CN”, AMC and λ, common to every model). Other models' fields are not in the page and are never sent.
- **Checks.** Nothing is required before a model is chosen; a value that is not a number or leaves a bound is an error at once. Once a model is chosen an empty field it, its tc method or its rainfall needs is an error (red, no run), a value outside its typical range a warning (amber, the run goes on) from Hydrolog's `outside_typical_range` notice and its `details.field` (Hydrolog owns the typical ranges); step 3 sums them up with a link to each field. Live recompute stays once the inputs are valid.
- **Example.** No example prefill: a first visit and „Wyczyść” show empty steps; `web/examples/kamiennik.json` moved to `tests/fixtures/`, and the guide (`web/instrukcja/`) carries Kamiennik at Świerzawa as a worked example. The stored inputs moved to `hydrolog-gui/hydrogram/2`. The hand-off still carries a full watershed: „Przekazanie” is offered once step 1 has one.
- **Library.** Only `area_km2` is required in a watershed (`WatershedParameters`, `hydrolog-network-1.schema.json`); a method or model that needs a missing field names it in `details.option` (branch `feature/partial-watershed`).

S3's acceptance „the Kamiennik example shows 60,21 m³/s” now holds for the worked example typed as the guide says. The guide's pictures of Hydrogram zlewni (`instrukcja/img/ekran.png`, `hydrogram.png`, `telefon.png`, `eksport.png`, `kalkulatory.png`) still show the five steps; no tool in the repository takes them again.

## Erratum 2026-11-04: one set of typical ranges, Hydrolog's

- **Ranges (the author's decision of 2026-11-04, supersedes D16's GUI-owned ranges).** Hydrolog is the single source of the typical ranges: one range per method and parameter, each with its literature source, in `hydrolog._ranges.TYPICAL_RANGES` (thresholds without a published source are gone, a GUI range with a source moved into the library and warns `outside_typical_range` with `details.field`); the catalog serves them as `typical_ranges` of the commands that check them, in the document of one command (`commands schema --command`, `hydrolog <group> <command> --schema` and `command_schema`, which `api/commands/{group}/{verb}` serves; not in the pages, [ADR-0017](../decisions/0017-typical-ranges-in-the-catalog.md)), so CLI and MCP users get them too, and the GUI's explanations (i) and notes read them from there instead of keeping numbers in `labels/info/*.js` (branch `feature/ranges-from-hydrolog`).

## Not in this plan

Editing the network's structure; framing the standalone server from a shell origin; the `postMessage` handshake and the hand-off through the shell (with the kit); an English UI; PMAXTP through IMGWTools and series from Archiwista; a PDF output of `report generate`; Hydrolog notices for the applicability ranges of the (i) texts; option names in library validation errors; saved variants or projects (Archiwista's, ECO-054); Hydrograf's „Wczytaj z Hydrologa” and „Przenieś do Hydrologa” (platform step 12, its own plan); Nogat's host (platform steps 8 and 9).
