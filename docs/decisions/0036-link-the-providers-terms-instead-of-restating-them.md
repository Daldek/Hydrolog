# 0036. Link the providers' terms instead of restating them

- Status: accepted
- Date: 2026-11-13
- Builds on: Nogat ECO-065 („Tam, gdzie się da, odsyłamy do regulaminu dostawcy danych; treści w naszych produktach
  ograniczone do minimum”), DEV §20 (DEV-20.1, DEV-20.4, DEV-20.5, DEV-20.7) and Nogat's GUI kit 0.6.0 (Nogat
  `develop`, `b29eada`)
- Amends: [ADR-0028](0028-the-providers-lines-in-every-product.md) (points 1 and 7: the lines and the terms notice),
  [ADR-0034](0034-a-public-gui-regulamin-limit-logs-totals.md) (the regulamin's blocks) and
  [ADR-0035](0035-one-strip-of-the-providers-lines-per-gui-view.md) (kit 0.6.0)

## Context

ADR-0028 gave every product with IMGW-PIB data the line H („Dane pochodzą z serwisu hydrologicznego IMGW-PIB …”) for
data of hydro.imgw.pl and the notice N („Dane IMGW-PIB można wykorzystywać nieodpłatnie …”), a summary of IMGW-PIB's
terms, before the addresses of the terms, „Regulamin: <address>”. ECO-065 drops H, which no terms require, and N,
since only the providers' own terms bind and a summary can mis-state them. The addresses stay, each naming whose terms
it links: RD „Regulamin danych IMGW-PIB: …”, RH „Regulamin serwisu hydrologicznego IMGW-PIB: …”, RK „Regulamin danych
PMAXTP: …”; ČHMÚ still has none. The kit's regulamin lost its block `imgw-terms`.

## Decision

1. `hydrolog._attribution` holds S, P, PS, PP, M, C, CP and RD, RH, RK, in the order S, P, PS, PP, M, C, CP, then RD,
   RH, RK; `IMGW_HYDRO` and `IMGW_TERMS` are gone. Each provider brings one terms line (`imgw` RD, `imgw_hydro` RH,
   `pmaxtp` RK, `chmi` none); `imgw_hydro` brings S and P like `imgw`.
2. A line Hydrolog does not know is a terms line when it is given in `terms_notice` or has the form „Regulamin <whose
   terms>: <address>” (was: begins with „Regulamin:”).
3. Lines written before ECO-065 are read as what they stood for, so no old line reaches a new product: H names the
   provider `imgw_hydro`, the old „Regulamin: <address>” of RD, RH or RK becomes the new line, and N and any other
   „Regulamin: …” line are dropped. This holds for every reader (input CSV columns, a JSON document's fields, the
   option `attribution`) and for `ATTRIBUTION.txt`, which a later write merges, so an old run directory or hand-off
   needs no rebuild.
4. The GUI keeps lines in the browser (a fetched PMAXTP depth's), reads them from hand-offs and shows them before and
   beside a run's. `GET api/session` gains `retired_lines`, each retired line with its current line or `null`
   (`hydrolog._attribution.retired_lines`), and the page orders and shows every set of lines through it (the view's
   strip and dialog, the welcome, the printed lines under the data, the lines of a Sieć hand-off made without a fresh
   run), so no kept or received retired line is shown or handed on. Rejected: rewriting the depths the browser kept,
   which the page would have to do for every key it ever stored.
5. The regulamin is filled without `imgw-terms`: the listed blocks (`imgw`, `pmaxtp`, `chmi`) stay, nothing follows
   from them. The kit (0.6.0) and `handoff-1.schema.json` are copied byte for byte from Nogat `b29eada`.

## Consequences

- A product with IMGW-PIB data carries one terms line per provider instead of two; the GUI's dialog „Źródła i
  warunki” lists RD, RH or RK after the attribution lines.
- The private API's `hydrolog-gui-session/1` has one more field.
- Files written before and handed out (CSV columns, a report, an SVG, a hand-off) keep their old lines; Hydrolog does
  not rewrite them, and reads them as point 3 says when they come back as input.
