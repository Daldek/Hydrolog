# 0016. Reports of the GUI's users: „Zgłoś uwagę”, `data_dir` and the admin key

- Status: accepted
- Date: 2026-11-04
- Amends: [ADR-0004](0004-settings-and-config-show.md) (`data_dir` is used; one credential),
  [ADR-0014](0014-web-gui-enters-the-scope.md) (the private API gains the report routes and an admin page)

## Context

Nogat's plan `docs/plans/2026-11-03-feedback-in-archiwista-and-hydrolog.md` (approved 2026-11-03) gives Hydrolog
Hydrograf's feedback mechanism (D1: the same behaviour, limits, texts and answers): a button of the top bar, a dialog
with diagnostics, reports stored by the app and an admin who reads, marks and deletes them (D3 to D6). Hydrolog had no
database, no administrator, no data directory and no credential.

## Decision

- **Storage.** One SQLite file, `<data_dir>/hydrolog/feedback.sqlite3` (DEV-18.2), made with its directory (0700, the
  file 0600) by the first report; reading makes nothing. The table `feedback` is Hydrograf's (`id`, `created_at` in UTC,
  `message`, `contact`, `page_url`, `user_agent`, `diagnostics` as JSON text, `is_read`) with its limits as checks;
  `PRAGMA user_version` is 1. WAL, a busy timeout and one call at a time per process make concurrent requests and
  several processes safe. A failure is `io_error` with `details.reason` (`feedback_store_failed`...) and no path.
- **`data_dir` is a setting** with the precedence of DEV-18.1 (`HYDROLOG_DATA_DIR`, `NOGAT_DATA_DIR`, `nogat.toml`,
  default `platformdirs.user_data_path("nogat")`), reported by `config show`; `create_app(data_dir=...)` lets a host
  place the file. Only the web GUI writes there.
- **The admin key is the one credential** (DEV-18.4): `HYDROLOG_ADMIN_API_KEY`, else the text of the file named by
  `HYDROLOG_ADMIN_API_KEY_FILE`, read at every request and compared in constant time with the bytes of `X-Admin-Key`.
  Without a key every admin request is `401 unauthorized` (`admin_key_not_configured`); unlike Hydrograf, no key is
  generated. `config show` reports both variables as present or missing, never their values.
- **Routes** (private, as D5 of the GUI plan): `POST api/feedback` for a GUI session (it opens one, as the other
  routes do; JSON only, at most 256 KiB), `GET api/admin/feedback`, `PATCH` and `DELETE api/admin/feedback/{id}`, with
  Hydrograf's answers and limits; errors are registry codes (`validation_error`, `unauthorized`, `not_found`,
  `io_error`) worded in Polish by the page.
- **The page.** The dialog and the diagnostics of D4 (events, the open section and its inputs, the environment; never
  file contents, request bodies, cookies or keys; at most 100,000 bytes; the preview is what is sent) and an admin page
  `admin/` whose key stays in the tab's `sessionStorage`; every text of a report is a text node.

## Consequences

- Hydrolog writes a file it was not asked to name, but only the web GUI and only for a report; the README and USAGE
  say where it is and how to read and back it up (`sqlite3 ... ".backup ..."`).
- `nogat doctor` sees `data_dir` and the two credential variables through `config show`.
- Rejected: a generated key logged at the start (Hydrograf's), because D3 refuses without a key; a JSON-lines file,
  which cannot change the read flag in place; the session directories, which are removed after 12 hours.
