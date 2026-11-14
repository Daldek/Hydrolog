# 0040. CP without the detail of processing

- Status: accepted
- Date: 2026-11-14
- Builds on: Nogat ECO-071 („Processing lines never name the processing”, the author's decision of 2026-11-14),
  DEV §20 (DEV-20.3, DEV-20.4) and Nogat's GUI kit 0.7.1 with the regulamin template 1.1 (Nogat `develop`,
  `05bf583`)
- Amends: [ADR-0028](0028-the-providers-lines-in-every-product.md) (point 1: Hydrolog's own CP and a producer's CP
  kept before it)

## Context

ADR-0028 gave Hydrolog its own CP, „Dane ČHMÚ zostały przetworzone (obliczenia hydrologiczne programem Hydrolog)”,
and kept a producer's CP beside it, so a series of ČHMÚ that Obserwator exported reached a result with two lines:
Obserwator's „(normalizacja i zmiana formatu)” and Hydrolog's. Nogat ECO-071 makes CP one fixed line, „Dane ČHMÚ
zostały przetworzone”, written once on a product with modified ČHMÚ data, and asks every reader of an older file to
take any „Dane ČHMÚ zostały przetworzone (…)” as CP and deduplicate it.

## Decision

1. **The line.** `hydrolog._attribution.CHMI_PROCESSED` is „Dane ČHMÚ zostały przetworzone”: every product with
   ČHMÚ's data (the envelope, the CSV columns, `ATTRIBUTION.txt`, the schematic, the report, the GUI's exports)
   carries C and this CP, once.
2. **The readers.** `Attribution.from_lines` takes a line „Dane ČHMÚ zostały przetworzone (…)”, whatever the words
   in parentheses (a final full stop and blanks ignored, as for every known line), as CP: it names ČHMÚ and is not
   kept, so an older input, hand-off or `ATTRIBUTION.txt` gives C and the one CP. A line that only begins like CP,
   without the parentheses, is another producer's line and stays verbatim.
3. **The page.** `orderLines` (`web/src/attribution.js`), through which the page shows and hands on lines it did not
   get from a run (a received hand-off, the lines of a Sieć hand-off made without a fresh run), passes them through
   the kit's `lines`, which gives the canonical CP for an older one.
4. **The kit.** Kit 0.7.1 is copied byte for byte into `web/nogat/` from Nogat `05bf583`: `LINES.CP` and the
   normalising `lines` of `nogat-sources.js`, and the regulamin template 1.1, whose ČHMÚ block quotes the new CP. A
   public GUI publishing 1.1 needs its own `terms_effective` in `[nogat.operator]`.

## Consequences

- A result from an Obserwator export of ČHMÚ has two lines (C, CP) instead of three.
- Old files are not rewritten: they are read as today's lines, as ADR-0036 did for the lines Nogat retired.
- Rejected: keeping a producer's parenthetical CP beside the canonical one (ECO-071 wants one line), and a fixed list of
  old CP lines in `retired_lines` (any words in parentheses are CP, so the page matches the form, as the kit does).
