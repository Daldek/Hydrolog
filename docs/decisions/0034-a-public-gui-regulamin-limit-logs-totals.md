# 0034. A public GUI: the regulamin, the request limit, the access log, daily totals, „Zgłoś uwagę” without contact, sessions without a cookie

- Status: accepted
- Date: 2026-11-13
- Amends: [ADR-0004](0004-settings-and-config-show.md) (two settings), [ADR-0014](0014-web-gui-enters-the-scope.md)
  (the session of the private API), [ADR-0016](0016-gui-feedback-and-data-dir.md) (the report and its file),
  [ADR-0027](0027-nogats-gui-kit-the-app-menu-and-the-handoff.md) (kit 0.4.0)
- Amended by [ADR-0035](0035-one-strip-of-the-providers-lines-per-gui-view.md) (2026-11-13): kit 0.5.1; the guide's
  „Regulamin” opens a new tab
- Amended by [ADR-0036](0036-link-the-providers-terms-instead-of-restating-them.md) (2026-11-13): the regulamin's
  blocks
- Amended by [ADR-0037](0037-nogats-logs-in-gui-serve.md) (2026-11-13): the access log is Nogat's, in every run of
  `gui serve`, in files under `<state_dir>/hydrolog/logs`; no `X-Request-Id`
- Amended by [ADR-0038](0038-nogats-admin-panel.md) (2026-11-14): the daily totals leave out the admin panel

## Context

Nogat's plan `docs/plans/2026-11-13-gui-terms.md` (approved 2026-11-13, step 4) and its standard DEV-15.7 to DEV-15.12
and DEV-18.1 give every public GUI, one that a deployment opens to anyone without signing in, one regulamin (kit 0.4.0,
regulamin 1.0) and the rules its text describes: a request limit per address held in memory only, no IP address in
any log, logs deleted after 14 days, anonymous daily totals, and „Zgłoś uwagę” with no contact field. Hydrolog's GUI
had none of them: uvicorn's access log was off, but the page kept a session in the cookie `hydrolog_gui` with the
person's files for 12 hours idle, and a report held a contact, the page's address, the `User-Agent` and diagnostics. §
8 ust. 7 of the regulamin says the service sets no cookie of its own and uses the files given for computations only to
run them.

## Decision

- **Public is `[nogat.operator]`.** `create_app` reads `nogat.toml` at the start (`config=` gives it parsed): with the
  table `operator` of `[nogat]` the GUI is public and does all of the below; without it (a local run) it does none of
  it: no regulamin, no link, no limit, no access log, no totals.
- **The regulamin.** Kit 0.4.0 (Nogat `2b513d0`) is copied byte for byte into `web/nogat/` (`nogat-terms.md`, `.html`,
  `.css` with the app menu's `terms` attribute). At the start the server fills `nogat-terms.html` as Nogat's
  `design/README.md` says: the blocks of Hydrolog's sources, `imgw` and `chmi` (the station series that Archiwista
  hands off and Obserwator exports) and `pmaxtp` (the depth Hydrogram zlewni fetches), with `imgw-terms`; no basemap
  block, since the GUI draws no map; the fields from `[nogat.operator]`, `[nogat] gui.hydrolog` and Hydrolog's own
  (`Hydrolog`, `MIT`, its repository, `nogat/tokens.css`, `nogat/`), HTML-escaped. It serves the page at
  `regulamin.html` beside `index.html`; a field missing or empty leaves no page and no link, with a warning in the
  log. Every view of the app shows a status bar at its foot with the statement of DEV-15.8 and „Regulamin” (a new tab),
  the app menu gets `terms`, and the guide's page shows the same footer from `GET api/terms`.
- **The request limit** (DEV-15.9). Per client address, the ASGI `client`, which uvicorn takes from `X-Forwarded-For`
  only for a connection from `FORWARDED_ALLOW_IPS` (`127.0.0.1` by default: `cloudflared` on the same machine): at
  most `request_limit` requests in a window of `request_window` seconds from the address's first counted request (new
  settings, default 300 and 60, DEV-18.1 order). Static files are not counted, nor the reads of the catalog documents
  (`api/commands…`, `api/schemas/…`): they are the same for everyone while the server runs, the page caches them, and
  one page load reads about fifty, which would make 300 requests six page loads a minute for a class behind one
  address. Over the limit: `429` with `Retry-After`, an API route the `hydrolog-error/1` of `rate_limited`, a page
  „Zbyt wiele żądań. Spróbuj ponownie za <n> s.”. An address is forgotten when its window ends.
- **The access log** (DEV-15.10). One JSON line per request on the logger `hydrolog.gui.access`: `time`, a random
  `request_id` (also the answer's `X-Request-Id`), `method`, `path` with its query, `status`, `size`, `duration_ms`,
  `user_agent`; never the client's address. `hydrolog gui serve` writes it to standard error, which the service
  manager keeps; uvicorn's own access log stays off and no logger of the app writes the client or the request scope.
  The 14 days are the service manager's (journald's retention), set by the deployment.
- **Daily totals** (DEV-15.11) in `<data_dir>/hydrolog/stats.jsonl`: per counted request the HMAC-SHA-256 of the
  address and the `User-Agent` under a 32-byte salt drawn at the start and at 00:00 UTC, in memory only, for the day's
  distinct `visitors`; `page_views` (the app, its guide and the regulamin served, not the admin page), `analyses_run`
  (runs of `api/run` answered `ok`, not the plans of `check`), `stations_opened` and `downloads`, which only the page
  sees: it sends `POST api/stats/station` when a station's series from a hand-off opens in Statystyka przepływów and
  `POST api/stats/download` for each file it saves (exports, reports, hand-off files, outputs of the server). The day's
  line is rewritten every five minutes while it changes, at the end of the day and at the stop, and a restart adds to
  it.
- **„Zgłoś uwagę”** (DEV-15.12). One text field and „Nie wpisuj danych osobowych. Jeśli chcesz odpowiedzi, napisz na
  <`[nogat.operator] email`>”; `POST api/feedback` takes `{message, context}` and refuses any other field
  (`validation_error`, `unknown_field`), so a contact cannot be sent; the context is `view`, `station`, `parameters`
  and `app_version` (the server's), at most 100,000 bytes. The file goes to version 2 (`id`, `created_at`, `message`,
  `context`, `is_read`; `secure_delete`); a file of version 1 is first copied whole to `feedback-v1-<UTC time>.sqlite3`
  beside it, for the operator to decide on, then its reports keep their text and get the context their page's address
  and diagnostics give, and the file is vacuumed. No session is needed to send a report.
- **Sessions without a cookie.** The page keeps the session's id in its memory and sends it in `X-Hydrolog-Session`;
  an answer that started a session names it in the same header. The page ends its session when it is closed or
  reloaded (`DELETE api/session` on `pagehide`); an idle session goes after one hour (was 12) and all at the stop, so
  the person's files are on the server only while they compute with them. Downloads of the session's files go through
  `fetch` and a `Blob`, since a plain link cannot carry the header.
- **The admin page stays the operator's**: `admin/` and `api/admin/feedback[/{id}]`, with `X-Admin-Key`, behind
  Cloudflare Access in a public deployment (`docs/USAGE.md`).

## Consequences

- A reload or a second tab starts a new session: files given before must be given again; inputs, kept in
  `localStorage`, stay. Links that leave the app (the regulamin, the guide) open a new tab.
- `config show` reports five settings; `nogat doctor` sees the limit.
- The access log and the other logs live in the journal of the service; the deployment keeps them 14 days.
- The totals are informative: anyone can send `api/stats/*`; they count no person.
- Rejected: the session id in `sessionStorage` (it would survive a reload, but the regulamin names only
  `localStorage`); runs that carry their files and answer their outputs, keeping nothing (every section's file model
  rewritten); counting the catalog documents (above); a log file of the app's own (a second retention to keep beside
  the journal's).
