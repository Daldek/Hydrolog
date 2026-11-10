# 0014. The web GUI enters the scope

- Status: accepted
- Date: 2026-11-02
- Amended by [ADR-0016](0016-gui-feedback-and-data-dir.md) (2026-11-04): the private API gains the report routes and
  an admin page; by [ADR-0018](0018-pmaxtp-through-obserwator.md) (2026-11-04): Hydrogram zlewni fetches the PMAXTP
  depth instead of asking for it
- Builds on: [ADR-0002](0002-result-envelope-and-domain-documents.md) (the envelope that every run of the GUI returns),
  [ADR-0013](0013-network-schematic.md) (the schematic that the GUI draws)

## Context

Hydrolog's interfaces were the Python library, the CLI and the MCP server, and [SCOPE.md](../SCOPE.md) listed a REST
API as out of scope. People who compute with Hydrolog without writing code or calling an agent had no way in, and
Nogat's GUI platform (Nogat's plan `docs/plans/2026-11-01-nogat-gui-platform.md`) hosts the GUIs of the ecosystem's
tools as modules. The author approved a mockup of a Polish browser GUI in Nogat's visual identity (Nogat
`design/mockups/hydrolog/`, `ed3473c`) and decided its open points on 2026-11-01. The plan
[2026-11-02-hydrolog-gui.md](../plans/2026-11-02-hydrolog-gui.md), approved on 2026-11-02, fixes the design; its
decisions D2 to D8 are the ones that change what Hydrolog is and are recorded here. The catalog additions they need
(decisions D3, D5, D11, D14 and D16 of the plan) are in [ADR-0015](0015-catalog-additions-for-the-gui.md).

Facts that shaped the decision (checked in the plan): a warm in-process `hydrograph generate` takes about 1 ms and the
CLI 1.4 s per call; `capture_warnings` serialises computations with a process-wide lock; Starlette and uvicorn are
already in `uv.lock` through `mcp`; Archiwista runs a Preact and htm frontend without a build under a `'self'` CSP and
tests it with Playwright.

## Decision

- **A browser GUI is in scope**, standalone and as a hosted module of Nogat's GUI platform: five sections (Hydrogram
  zlewni, Sieć i trasowanie, Statystyka przepływów, Kalkulatory, Wszystkie polecenia), Nogat's identity (copied
  tokens and marks, the light and the dark theme, the phone layout), exports (CSV, JSON, the Markdown report, a print
  view, PNG, the CLI line) and the hand-off with Hydrograf as `nogat-handoff/1` carrying `hydrolog-network/1`.
- **The GUI computes nothing.** Every hydrological value comes from the catalog (`run_command`); the browser formats,
  sums series for display and draws.
- **Package and extra (D2).** `src/hydrolog/gui/` holds the server and `src/hydrolog/gui/web/` the static files
  (package data `gui/web/**`). The extra `gui = ["starlette>=1.10,<2", "uvicorn>=0.54,<1"]` is repeated in `all`; the
  dev group gains `httpx` (Starlette's `TestClient`) and `playwright`. The base install stays numpy, scipy and
  platformdirs.
- **`hydrolog gui serve` through the catalog (D3).** A group `gui` with the command `gui serve`
  (`hydrolog.operations.gui_serve`; options `host`, default `127.0.0.1`, `port`, default `8070`, `no_browser`,
  `check`). It is a catalog command like every other, but not an MCP tool and not a line of the agent guide's index;
  the catalog side is in [ADR-0015](0015-catalog-additions-for-the-gui.md).
- **Hosting by the entry point group `nogat.gui` (D4).** `hydrolog = "hydrolog.gui:gui_module"`; `gui_module()`
  returns a frozen `GuiModule` (`name`, `title`, `web`, `index`, `sections`, `app=create_app`). A host mounts
  `app(work_root=...)` at a prefix of its own origin, or serves `web/` and answers the same routes from its catalog
  bridge. The page uses relative URLs only, so it works at `/` and under any prefix; `?nogat=1` hides the top bar and
  the rail before the first paint. The shape of `GuiModule` is a proposal to Nogat's platform plan.
- **A private, generic server API relative to the page (D5).** `GET api/session`, `GET api/commands`,
  `GET api/commands/{group}/{verb}`, `GET api/schemas/{file}`, `POST api/run/{group}/{verb}?channel=...&check=...`,
  `POST api/format/{group}/{verb}`, `PUT api/files/in/{name}`, `GET` and `DELETE api/files/{in|out}/{name}`. The
  routes serve this GUI only: they are not a REST interface of Hydrolog (no `/api/v1`, no OpenAPI, no stability
  promise; agents use the CLI, MCP and Python). This is a deviation from AGI section 6, listed in `CLAUDE.md`. They are
  generic over any `commands-1` catalog, so Nogat's bridge can answer them for a hosted module. `gui serve`,
  `config show` and `commands guide` are excluded (`404 not_found`). A run's outcome is the envelope: an error is
  `hydrolog-error/1` with the registry's HTTP status and the Polish `title`; a run replaced or stopped is the status
  `cancelled` (AGI-4.2). The server rewrites every absolute path of the work directory relative to it, so no server
  path reaches the browser.
- **Warm worker processes, the newest run wins (D6).** Two spawned worker processes import numpy, scipy and
  `hydrolog.operations` once (BLAS threads at 1) and run `run_command(name, options, allowed_dirs=[session
  directory])`. A run names its `channel`; a newer run of the same session and channel cancels an older one that is
  still queued (notice `superseded`), and the client ignores one that already runs. A run longer than 30 s kills its
  worker, which is replaced, and ends `cancelled` with the notice `timeout`; on POSIX each worker has `RLIMIT_AS` of
  2 GiB.
- **One work directory per browser session (D7).** A random id in the cookie `hydrolog_gui` (HttpOnly,
  SameSite=Strict) names `<tmp>/hydrolog-gui-<pid>/<id>/` (mode 0700) with `in/` and `out/`. A path option takes only
  `in/<name>` or `out/<name>` (an output only `out/`), anything else is `403 forbidden` before the run and
  `allowed_dirs` checks again inside it. Limits: 20 MiB per file, 100 MiB and 200 files per session, 5 MiB of JSON per
  request, 64 sessions (the least recently used idle one goes first), idle sessions removed after 12 h and all at
  shutdown. No arbitrary paths, no file browser, no store.
- **Security of the standalone server (D8).** It binds `127.0.0.1` by default and has no sign-in. Reachable beyond
  loopback, anyone who reaches it can use it, so it is exposed only behind an authenticating proxy: the author's
  tunnel to 127.0.0.1:8070 will be behind Cloudflare Access, which the author sets up, and the platform has its own
  front door. `gui serve` with another address adds the notice `exposed_without_auth`. Every response carries a strict
  Content-Security-Policy (`default-src 'self'`, no inline scripts or styles, `frame-ancestors 'none'`),
  `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, COOP and CORP
  `same-origin` and a `Permissions-Policy`; static files are `no-cache`, `api/` is `no-store`. `POST`, `PUT` and
  `DELETE` are refused (`403 forbidden`) when `Sec-Fetch-Site` is `cross-site` or `same-site`, and `run` and `format`
  require `Content-Type: application/json`, which a cross-site page cannot send without a preflight that fails. DNS
  rebinding gives an attacker only a session of its own, so there is no Host allow-list.
- **Polish only.** The UI texts are modules keyed by English ids (DEV-2.3); an English UI comes later. This is a
  deviation from DEV-2.2, listed in `CLAUDE.md`. Numbers follow `pl-PL`. Notices and errors are worded in Polish from
  their stable codes and `details` ([ADR-0015](0015-catalog-additions-for-the-gui.md)); an unknown code shows the
  English message marked „(EN)”.
- **A print view instead of a PDF output.** „Drukuj” lays a section out on A4 and the browser saves it as PDF;
  Hydrolog adds no PDF output.
- **No variants.** The GUI keeps each section's inputs in the browser's storage, without saved variants or projects.
  Hydrogram zlewni recomputes live after every valid change; the other sections compute on their button and mark
  their results stale after a change.

## Consequences

- [SCOPE.md](../SCOPE.md) no longer excludes a web interface in general: it excludes a public REST API, lists the GUI
  among the interfaces and the `gui` extra among the dependencies; [PRD.md](../PRD.md) section 2.16 holds the user
  stories.
- The GUI is a client of the catalog like the CLI and the MCP server: a value it shows can be reproduced with the CLI
  line it exports, and a new command appears in Wszystkie polecenia as a generated form without GUI code.
- The base install and the library are unchanged; without the extra `gui serve` ends with `missing_dependency` and
  the hint `pip install "hydrolog[gui]"`.
- The private routes may change with the GUI. A host other than Hydrolog's own server that answers them (Nogat's
  bridge) follows the version of the GUI it hosts.
- The gate gains Playwright tests with Chromium (locally and on the three CI systems), so `CLAUDE.md` names the
  browser install.
- Until Cloudflare Access is in place, the page behind the tunnel is open to anyone with the address, within the
  session limits above; the deployment through the tunnel is done only when Access is in place.

## Alternatives considered

- **FastAPI:** the private routes need neither OpenAPI nor pydantic.
- **`http.server`:** no maintained HTTP parser in front of a tunnel, no client disconnects, no `StaticFiles` or
  `TestClient`.
- **Threads instead of worker processes:** `capture_warnings` serialises computations anyway, and a thread cannot be
  stopped.
- **The CLI per call:** 1.4 s per run makes live recompute impossible.
- **A public REST API (`/api/v1`, OpenAPI):** a second public interface to keep stable next to the CLI, MCP and Python,
  with nothing an agent needs that those do not give.
- **A sign-in in Hydrolog:** the platform has its own front door and the author's tunnel gets Cloudflare Access; a
  second account system would only duplicate them.
- **Chart.js:** a canvas (PNG and print want SVG), no probability paper, re-styling on every theme change and about
  200 kB to vendor; the GUI draws inline SVG with its own module.
- **The mockup's classic script, or a build toolchain:** the generated forms and node editors need components and
  state; Preact and htm as ES modules without a build (DEV-15.1), vendored as in Archiwista, give them.
