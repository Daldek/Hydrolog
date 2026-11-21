# 0072. The admin panel says what each daily total counts

- Status: accepted
- Date: 2026-11-21
- Builds on: Nogat DEV-15.11 (the daily totals), DEV-15.13 (the admin panel and the app's own scripts and sections in
  `<nogat-admin>`), DEV-15.14 (info texts); the finding G08-4 of the scenario test of 2026-11-15/16
- Amends: [ADR-0038](0038-nogats-admin-panel.md) (decision 2: the page is no longer the kit shell alone)

## Context

On 2026-11-16 at 00:27 UTC the admin panel of the scenario's public GUI showed for that day 2 visitors, 0 page views and
14 computations, and the tester could not tell whether the page views were miscounted. The access log of that instance
shows how the totals came about, and they follow DEV-15.11:

- `visitors` count every request the request limit counts, the API's too, not only pages. The day's two visitors were
  a browser that computed in Sieć at 00:01, with no page that day (the log's last page of a browser is `GET /` 304
  at 23:58 UTC the day before, counted on 2026-11-15), and a headless browser whose page called `GET api/session`
  and six runs at 00:07 and 00:18 without any `GET /`.
- `page_views` count the HTML pages the server answers (200 or 304). A page the browser shows from its own cache does
  not reach the server: a tab restored when the browser starts loads the app from the cache, runs its scripts and asks
  the API, and the server sees no page. A persistent Chromium profile with `--restore-last-session` does exactly that
  (checked on 2026-11-21: the restored tab sent `GET api/session` and no `GET /`). Switching sections of an open page
  (`#hydrogram`, `#siec`) loads no page either.
- `analyses_run` count every run answered `ok`; each page load runs about six (every section computes its stored
  inputs), so 14 is two page loads and two runs of Sieć.

So no total was miscounted; the panel just did not say what its columns count. The kit's view `<nogat-admin-stats>`
has fixed headings and no place for an app's words, and a copied kit file is never edited (ADR-0027); the kit lets the
app add its own scripts to the admin page (Nogat `design/README.md`, admin panel).

## Decision

1. **`web/admin/admin.js`**, a module loaded after the kit's, adds under the table of „Statystyki” a fold „Co liczą
   kolumny”, with the kit's classes of a report's „Kontekst” (`nogat-admin-context`): one line on the UTC day and the
   admin panel's requests, then each column's heading (the kit's `STATS_COLUMNS`) and what it counts.
2. **The texts are Hydrolog's**, in `web/src/labels/admin.js`, worded as info texts (DEV-15.14): what each total counts
   and why a visitor may have no page view (a tab opened the day before, a tab the browser restored from its cache),
   why the computations outnumber the page views (each section computes when the page opens and at every change), and
   that the totals are daily sums of UTC days.
3. **The counting is unchanged.** Counting the page loads from the browser's cache would need the page to report itself
   (a request DEV-15.11 does not name) or `no-store` on the pages, which would make every reload and history step
   download the page again; neither is taken.

## Consequences

- The admin page loads one script of the app; the contract test of the page names it.
- A change of what a total counts updates its text in `labels/admin.js` together with USAGE („Daily totals”).
