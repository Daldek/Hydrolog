# 0039. The regulamin linked from the rail, the welcome and the guide's contents; no footer

- Status: accepted
- Date: 2026-11-14
- Builds on: the author's decision of 2026-11-14 for every public GUI of Nogat (the footer statement of DEV-15.8
  goes away; the statement stays as the opening of § 3 of the regulamin 1.0, unchanged)
- Amends: [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (where the regulamin is linked) and
  [ADR-0035](0035-one-strip-of-the-providers-lines-per-gui-view.md) (point 4: the footer's link)

## Context

ADR-0034 gave every view of a public GUI a status bar at its foot: the statement of DEV-15.8 („Serwis jest
niekomercyjny i bezpłatny…”) and „Regulamin”, and the guide's page the same footer. The row took space under every
view, on a phone above the bottom bar, while the regulamin was already one click away in the app menu „Aplikacje”. The
author dropped the footer for every GUI of the ecosystem: the statement is the opening of § 3 of the regulamin, and a
public GUI links the regulamin in exactly three places: the kit's app menu, the bottom of the GUI's left navigation as
a small quiet link, and the welcome window where the GUI has one. The providers' strip `<nogat-sources>` and its dialog
„Źródła i warunki” (with „Regulamin serwisu”) stay as they are: IMGW-PIB's terms (§ 5) require the providers' lines on
screen.

## Decision

1. **No footer.** The status bar of every view (`src/ui/footer.js`, `.app-footer`, the shell's extra grid row) and the
   guide's footer are removed, and with them the statement's text in the page (`shell.footer`).
2. **The rail.** On a public GUI the rail of the sections ends with the small link „Regulamin” at its bottom
   (`src/ui/terms.js` `TermsLink`, class `rail-terms`; 10 px, the rail's ink, dimmed). The phone's bottom bar of
   sections leaves it out: five sections fill it, and the app menu and the welcome dialog give the link there.
3. **The welcome dialog.** While the page shows provider data, the welcome's part „Źródła danych” (the kit's
   `fillSources`) ends with „Regulamin serwisu”, and that is the welcome's link; without provider data, as on a first
   visit, the part is that link alone (`welcome-terms`), so the dialog never shows the regulamin twice.
4. **The guide.** Its left navigation, the contents, ends with „Regulamin” from `GET api/terms` (was: the footer under
   the page).
5. **The app menu** keeps its last entry „Regulamin” (kit, unchanged). Every link opens a new tab
   (`target="_blank" rel="noopener"`), and a GUI that is not public draws none of them.

## Consequences

- A view of a public GUI is as tall as a local one: the layout no longer depends on `[nogat.operator]`.
- The statement is read only in the regulamin; the page carries no text of its own about the service's character.
- `GET api/terms` serves the guide's contents instead of its footer; its answer is unchanged.
- Rejected: a sixth item of the phone's bottom bar (the five sections would shrink below their touch size).
