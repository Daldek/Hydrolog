# 0037. Nogat's logs in `gui serve`: access, application and lifecycle records in `<state_dir>/hydrolog/logs`

- Status: accepted
- Date: 2026-11-13
- Builds on: Nogat DEV-12.4 to DEV-12.9 and ECO-066 (Nogat `develop` `a41d971`), Nogat's plan
  `docs/plans/2026-11-13-unified-logging.md` (step 3) and plan `docs/plans/2026-11-13-terms-fix.md` (step 4)
- Amends: [ADR-0004](0004-settings-and-config-show.md) (one setting) and
  [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (the access log)

## Context

ADR-0034 gave a public GUI its own access log: one JSON line per request on the logger `hydrolog.gui.access`, written
to standard error by `gui serve` and kept by the journal, with the full `User-Agent` and the request id sent back in
`X-Request-Id`; a local run logged nothing. The 14 days of DEV-15.10 were journald's, which needs root and changes the
whole host. ECO-066 gives every server of the ecosystem one convention, which Nogat checks: three logs (access,
application, lifecycle) in the format `nogat-log/1` (`schemas/log/record-1.schema.json`), in daily files under
`<state_dir>/<project>/logs` that the server deletes itself after 14 days, only lifecycle records and reduced errors on
standard error, the `User-Agent` kept as its class, a request id never sent to the client, and one implementation,
Nogat's `standards/reference/nogat_logging.py`, copied byte for byte (DEV-15.6).

## Decision

1. **The copies.** `standards/reference/nogat_logging.py` is copied unchanged to `src/hydrolog/gui/nogat_logging.py`
   and `schemas/log/record-1.schema.json` to `schemas/nogat/record-1.schema.json`, both from Nogat `a41d971`.
2. **`state_dir`**, a sixth setting with the order of DEV-18.1 (`HYDROLOG_STATE_DIR`, `NOGAT_STATE_DIR`, `[hydrolog]`
   or `[nogat] state_dir`), default `platformdirs.user_state_path("nogat")` (`~/.local/state/nogat` on Linux), a path
   read like `data_dir`; `config show` reports it.
3. **Every run of `gui serve` logs**, public or not. `hydrolog.gui.server.serve` makes a `ServerLog("hydrolog",
   __version__, <state_dir>/hydrolog/logs)` and gives it to `create_app(log=...)`, which adds `AccessLog` as the
   app's outermost middleware, outside `PublicGuard`, so the answers of the request limit are logged too. Static
   content answered below 400 is not logged: `QUIET = r"^/(css|src|vendor|nogat)/|^/theme-init\.js$|^/api/(commands|schemas)(/|$)"`
   (`hydrolog.gui._app`), the page's files and the catalog documents. `create_app` without `log` logs no request: a
   host that mounts the app keeps its own access log, outermost (DEV-12.8).
4. **Start and stop.** `_serving.run` starts the log before uvicorn, with the settings `url` and `public` in the record
   `start`, and stops it after uvicorn has stopped. The socket listens already when the record is written (`_bind`
   calls `listen()`), so the record replaces the line `Hydrolog GUI: <url>` as the sign that the server is ready.
   While it serves, the CLI's own handler of the `hydrolog` logger is set aside, so warnings reach standard error only
   as Nogat's records. uvicorn keeps `log_config=None` and `access_log=False`.
5. **What goes.** `PublicGuard` keeps the request limit and the daily totals only: its access line, `ACCESS_LOGGER`,
   the header `X-Request-Id` (`REQUEST_ID_HEADER`) and `_serving._access_log` are removed.

## Consequences

- The access log of a running service is `~/.local/state/nogat/hydrolog/logs/access-YYYY-MM-DD.jsonl`, read with
  `jq -cs 'sort_by(.time)[] | select(.kind != "access" or .status >= 500)' ~/.local/state/nogat/hydrolog/logs/*.jsonl`;
  `journalctl --user -u hydrolog-gui` shows only starts, stops, deletions and errors by type. The user unit
  `hydrolog-gui` needs no change, and no journald retention needs setting for Hydrolog's sake.
- A record keeps `agent` (`browser`, `bot`, `script`, `none`), not the `User-Agent`; `path` drops the values of the
  parameters of `REDACTED` (`?q=`); fields renamed from ADR-0034's line: `size` is `bytes`.
- The answers carry no `X-Request-Id`; nothing in the page used it.
- The command's own result (human text, or `hydrolog-gui-serve/1` with `--json`) is still printed on standard output
  when the server stops (AGI §3): the address and the two times, no request data.
- Rejected: a regular expression that also covers the guide's and the admin page's files (`instrukcja/img/`,
  `instrukcja.css`…), not in the migration list of Nogat's plan; those requests are logged, as few as the pages.
