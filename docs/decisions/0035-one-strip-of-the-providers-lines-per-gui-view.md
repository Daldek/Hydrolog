# 0035. One strip of the providers' lines per GUI view, the full lines in a dialog and the welcome

- Status: accepted
- Date: 2026-11-13
- Builds on: Nogat DEV-20.5 and ECO-064, Nogat's GUI kit 0.5.1 (`<nogat-sources>`, Nogat `5406e5c`, `cbe9f4e`)
- Amends: [ADR-0028](0028-the-providers-lines-in-every-product.md) (point 7: what the GUI shows on screen) and
  [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (kit 0.5.1; the guide's „Regulamin” opens a new tab)
- Amended by [ADR-0036](0036-link-the-providers-terms-instead-of-restating-them.md) (2026-11-13): kit 0.6.0
- Amended by [ADR-0039](0039-the-regulamin-in-the-rail-and-the-welcome-no-footer.md) (2026-11-14): no footer; the
  welcome's „Regulamin serwisu” stands alone while the page shows no provider data

## Context

ADR-0028 put the full providers' lines and the terms notice, as the part „Źródła danych”, under every result: in the
centre under the charts, at the end of the panel Wyniki, and, in the panel Dane, under a fetched PMAXTP depth and in
the card of a received hand-off. A view of Hydrogram zlewni with a PMAXTP depth carried three copies, 56 lines at
1440 px (27 + 12 + 17, measured in Chromium) and 54 at 390 px. Nogat's DEV-20.5 now asks for one compact strip per
view on screen, showing only the short lines S, P, PS, PP and ČHMÚ's short form CK, with „Źródła i warunki” opening
the full lines and the terms; the same full content in the GUI's own welcome window; files, exports, images, print
views and hand-offs unchanged.

## Decision

1. Each section's view (Hydrogram zlewni, Sieć, Statystyka, Kalkulatory, Wszystkie polecenia) has one
   `<nogat-sources>` under its centre (`ViewLayout`'s `sources`, `ui/sources.js`), fed with the union of the lines of
   its inputs (the PMAXTP depth, a received hand-off, the network's sources) and of its last run, ordered as the
   providers' sets of `GET api/session`. Its `terms` is the session's regulamin (a public GUI only).
2. No full block stands on screen. The existing footers stay in the page for the print view only (`@media screen`
   hides them; `print.css` prints them at the end of the results and under the data they came with, and hides the
   strip), so the print view is as before.
3. The welcome dialog lists the lines of the data the page shows, with the kit's `fillSources`, and nothing while it
   shows none. The alternative, the general lines of every provider Hydrolog may show (IMGW-PIB, its hydrological
   service, PMAXTP, ČHMÚ: 8 attribution lines and 4 terms lines), would double the welcome of every first visit for
   data the person may never load; with the chosen rule a first visit, every section empty, keeps the welcome to its
   sentences.
4. Every link to the regulamin opens a new tab (DEV-15.7): the kit's (0.5.1) and the footer's, also on the guide's
   page.

## Consequences

- At 1440 px a view shows its lines in 2 (IMGW-PIB) to 4 (PMAXTP) lines of 12 px, at 390 px in 4 to 6.
- Files, exports, PNG, the report, the hand-off and the print view keep the full lines; the command option
  `attribution` of a run is unchanged.
- The kit's files are copied byte for byte (DEV-15.6); `nogat-kit.json` names 0.5.1.
