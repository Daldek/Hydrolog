# 0038. Nogat's admin panel: the kit shell at `admin/`, `api/admin/stats` and `api/admin/status`

- Status: accepted
- Date: 2026-11-14
- Builds on: Nogat DEV-15.13 and ECO-067, kit 0.7.0 (Nogat `develop` `229ade3`), Nogat's plan
  `docs/plans/2026-11-13-admin-panel.md` (step 2)
- Amends: [ADR-0016](0016-gui-feedback-and-data-dir.md) (the admin page and the answer of `PATCH`) and
  [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (the daily totals leave out the admin panel)

## Context

ADR-0016 gave the GUI an admin page of its own at `admin/`, Preact on Nogat's tokens, which read, marked and deleted the
reports of „Zgłoś uwagę” with the key of `HYDROLOG_ADMIN_API_KEY` or `HYDROLOG_ADMIN_API_KEY_FILE`; `/admin` answered
`307` (Starlette's directory redirect) and the page's files were cached like the app's (`no-cache`). Each GUI of the
ecosystem had such a page of its own. ECO-067 gives every GUI one panel: the kit's `<nogat-admin>` with „Zgłoszenia”,
„Statystyki” and „Stan” on one core API of five routes, at `/admin/` and `/api/admin/` only, so a deployment protects
exactly `/admin`, `/admin/*` and `/api/admin/*`.

## Decision

1. **The kit.** Kit 0.7.0 is copied byte for byte into `web/nogat/` from Nogat `229ade3`, with its new files
   `nogat-admin.js` and `nogat-admin.css` and its manifest `nogat-kit.json`.
2. **The page.** `web/admin/index.html` is the kit shell alone, `<nogat-admin app="Hydrolog" project="hydrolog"
   back="../" marks="../nogat/marks/">`, with the tokens, the kit's stylesheet and script, the stored theme
   (`theme-init.js`) and `<meta name="robots" content="noindex">`; Hydrolog has no section of its own. The Preact page
   (`admin.js`, `admin.css`, `src/labels/admin.js`) and the error texts only it used are removed. The key is kept in
   `sessionStorage` under `hydrolog/admin-key/1` (was `hydrolog-gui/admin-key/1`).
3. **`admin` answers `308`** to `admin/`, a relative address, so it holds under a host's prefix.
4. **No admin answer is stored.** `Cache-Control: no-store` for `admin`, `admin/…` and `api/admin/…`, as for the rest of
   `api/`; the app's own files keep `no-cache`.
5. **`PATCH api/admin/feedback/{id}` answers the report** (`UPDATE … RETURNING`), as DEV-15.13 says, instead of
   `{"status": "ok"}`.
6. **`GET api/admin/stats?from=&to=`** answers `{days, totals}`: the lines of `<data_dir>/hydrolog/stats.jsonl` between
   the two UTC days `YYYY-MM-DD`, both included, by default the 30 days up to today, today's line replaced by the day
   as counted so far in a public GUI (`DailyStats.snapshot`); each day has the keys of DEV-15.11 (a missing or unusable
   total is 0), lines that are not a day are left out, and `totals` sums every key but `visitors`. A day that is not
   `YYYY-MM-DD` is `validation_error` (`format`), `from` after `to` too (`maximum`). A GUI that is not public counts
   nothing and still gives the lines a public run left.
7. **`GET api/admin/status`** answers `{app: "Hydrolog", version, started_at, uptime_s, data_dir, disk: {free_bytes,
   total_bytes}, checks}` (`hydrolog.gui._admin`): `started_at` when the app was built, `data_dir` the directory
   `<data_dir>/hydrolog`, the disk of it or of its nearest existing parent, and two checks with a Polish `detail`:
   `data_dir` (a probe file made and removed in the directory, or, before the first report, a writable directory above
   it; else `failed`) and `feedback_db` (the reports' file read for its counts; no file is `ok`; an unreadable one
   `failed`).
8. **The operator is no visitor.** In a public GUI the requests of `/admin`, `/admin/…` and `/api/admin/…`
   (`_public.is_admin`) count in no daily total (DEV-15.11), and stay under the request limit (DEV-15.9).
9. **The sign-in is unchanged**: every admin route, `stats` and `status` included, checks `X-Admin-Key` in constant
   time against the key read at every request; refusals are `401 unauthorized` with `admin_key_not_configured`,
   `admin_key_missing` or `admin_key_invalid`; no key is generated or logged.

## Consequences

- The deployment protects `/admin`, `/admin/*` and `/api/admin/*` (Cloudflare Access on the test deployment) and sets
  the key file named by `HYDROLOG_ADMIN_API_KEY_FILE` in the unit, as before.
- A key kept by the old page under `hydrolog-gui/admin-key/1` is not read: the operator signs in once more.
- A script that read `{"status": "ok"}` from `PATCH` gets the report; its status code is still 200.
- Rejected: an `X-Robots-Tag` header on the admin answers (the page's `noindex` is what DEV-15.13 asks), and a
  `warning` for unread reports in `feedback_db` (the count is in its `detail`).
