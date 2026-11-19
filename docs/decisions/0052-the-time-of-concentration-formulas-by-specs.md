# 0052. The time of concentration formulas by specs: the sources' units, Kirpich's 0.0078 with the exact foot

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs), Nogat's computation standard
  (CMP-2.4 confirmation of a constant, CMP-4.3 conversions by the units table, CMP-1.4 applicability ranges) and the
  literature research of the formulas of 2026-11-18 (TRIAGE T8, T10)
- Amends: [ADR-0019](0019-tc-from-the-inputs-its-source-defines.md) (Kerby-Kirpich's flow path not longer than its
  overland segment is refused as a violated physical constraint, no longer as `exclusive_minimum`)

## Context

The time of concentration family is the second to get specs (Nogat's plan of the computation standard, step 5). Its six
formulas were computed with metric constants that the code had converted itself:

- **Kirpich** took 3.981 for L in km, which is 0.0195 · 1000^0.77. The sources disagree on the metric constant: TxDOT
  (Roussel et al. 2005, Hydraulic Design Manual 2019) prints 0.0195 for L in m, WR-D-71-1 (2023) 0.01947; both round
  0.0078 · (1/0.3048)^0.77 = 0.019472, the formula in feet. The form in feet, 0.0078 L^0.77 S^−0.385 [min], is the one
  that Fang et al. (2005, eq. 3.14, p. 22), Roussel et al. (2005, eq. 7 and the supplement, p. 29), Mota and Kobiyama
  (2015, pp. 56–58) and FDOT (2024, eq. 2.2-9) print. Kirpich (1940) published curves; the formula is Rowe and
  Thomas's (1942), after Mota and Kobiyama.
- **NRCS** took 0.01416 in SI units. NEH 630-15 eq. 15-4b is tc = l^0.8 (S + 1)^0.7 / (1140 Y^0.5) [h] with l in ft,
  S in inches and Y in percent; in SI it is 100 l[m]^0.8 (S[mm] + 25.4)^0.7 / (7068.86 Y^0.5) with
  7068.86 = 1900 · 0.3048^0.8 · 25.4^0.7, so the constant is 100/7068.86 = 0.0141466 (TRIAGE T8).
- **Kirpich's range** was Roussel et al.'s rounded slopes 3–10 %, which leave out Kirpich's own basin of S = 0.0274.
  Mota and Kobiyama (2015, p. 58) give the interval of the data of Kirpich (1940, table 1): L 350–4,000 ft and S
  0.025–0.1.
- **Kerby-Kirpich** offsets a slope below 0.002 by 0.0005 (Cleveland et al. 2012, eqs. 1–2) for each segment by its own
  slope, while Cleveland et al. (pp. 1–2) decide by the main-channel slope for both segments (below 0.002 both are
  offset, above 0.003 neither, 0.002–0.003 left to the engineer) (TRIAGE T10).

The standard confirms a constant by its primary source or two independent secondary ones (CMP-2.4), and a formula
module contains no conversion literal: every conversion is an entry of the units table (CMP-4.3).

## Decision

1. **Six specs, `formula_version` 1, status `referenced`.** `KIRPICH`, `NRCS`, `GIANDOTTI`, `FAA`, `KERBY` and
   `KERBY_KIRPICH` of `hydrolog.time.concentration` (spec names `kirpich` … `kerby_kirpich`) beside
   `ConcentrationTime.<method>`, whose arguments do not change; `hydrolog.time.concentration` joins `FORMULA_MODULES`.
   Each formula is evaluated in the units of its source with the exact foot, inch and percent of the units table:
   Kirpich, Kerby and FAA with lengths in feet (FAA's slope in percent), NRCS in feet, inches and percent with the
   result in hours, Giandotti in hours; every result is in minutes.
2. **Kirpich's constant is 0.0078 for L in ft**, confirmed by Fang et al. (2005) and three further independent prints.
   The metric 0.0195 and 0.01947 are roundings of its conversion that two sources print differently, and 3.981 folds a
   conversion into a constant: neither is a constant of the source. Every Kirpich result is 0.136 % shorter (3.981 /
   3.975604 = 1.001357).
3. **The NRCS lag equation is eq. 15-4b in its own units,** which is the exact metric 0.0141466 instead of 0.01416:
   every NRCS result is 0.095 % shorter (1.000950).
4. **Kirpich's applicability is Mota and Kobiyama's data interval,** L 0.10668–1.2192 km and S 0.025–0.1, each with its
   locator; a value outside gives the notice (ADR-0050, point 3). The area 0.005–0.45 km², not an input of the formula,
   stays in `hydrolog._ranges`, checked by `WatershedParameters.calculate_tc`. The other methods keep their ranges, now
   written in their specs with source and locator, or `unstated` where no source gives one.
5. **Kerby-Kirpich keeps the offset per segment, declared as a deviation** from Cleveland et al. (2012) in its spec's
   conventions: the two agree when both slopes lie on the same side of 0.002 and differ for a flat main channel under a
   steeper overland segment, a steep channel under a flat overland segment and the band 0.002–0.003. At 0.002 the
   offset is dropped, so Kerby's time steps up by 5.35 % and the channel part of Kerby-Kirpich by 8.97 %; the limits
   of the spec assert both steps.
6. **Ranges.** Every input has a physical range with a test bound and its reason (a flow path of 1,000 km, about the
   Vistula; a slope of 1 m/m; Kerby's N of 8), an applicability range with its source or `unstated`, and a typical
   range from Hydrograf's recorded hand-offs (`tests/fixtures/handoff_hydrograf*.json`, `kamiennik.json`), Hydrograf's
   ADR-0075 for CN and the tables of N and C the catalog quotes.
7. **Refusals of the standard.** `ConcentrationTime.*` refuse NaN, infinities, booleans, strings and values outside the
   physical range with `details.reason` `outside_physical_range` or `invalid_type`, `details.formula` and
   `details.option`; Kerby-Kirpich's flow path not longer than its overland segment is `outside_physical_range` with
   `details.constraint` `flow_path_longer_than_overland` (ADR-0019 had `exclusive_minimum`).
8. **Evidence.** 41 published cases with their roundings in `tests/fixtures/formulas/tc-cases.json` and one recorded
   discrepancy (INDOT example 29-7.8, an error of the source), oracles in decimal arithmetic at 50 digits of the SI forms
   with unrounded constants, the power laws of each formula and the steps of the low-slope offset
   (`tests/unit/test_formulas_tc.py`).

## Consequences

- **Results change:** Kirpich −0.136 % and every hydrograph timed by it (the default `tc_method`), the channel part of
  Kerby-Kirpich the same, NRCS −0.095 %; FAA and Kerby by less than 0.003 %, Giandotti not at all. A stored Kirpich tc
  is divided by 1.001357 and an NRCS one by 1.000950 to recompute it; the envelope carries `formula_versions`
  (`{"kirpich": 1}`) from this release on. The guide's Kamiennik: Kirpich 187.4 → 187.1 min, NRCS 399.8 → 399.4 min,
  Kerby-Kirpich 208.9 → 208.6 min, its hydrograph 54.20 → 54.23 m³/s.
- Kirpich warns on almost every watershed of Hydrograf: their flow paths are longer than 1.22 km.
- Nogat's hand-off example D15 was computed with 3.981; with the exact Beta storm of ADR-0046 Hydrolog now gives
  57.9 m³/s and 1 046 737.6 m³ instead of the printed 57.8773 m³/s and 1 046 712.9 m³. Hydrolog's copy of
  `handoff-1.schema.json` records them, and Nogat's file takes the same change.
- Docstrings of the six methods name their specs and hold no number (CMP-2.7); the reports take their constants from
  the specs, and `docs/FORMULAS.md` shows equations, constants, ranges and sources.

## Alternatives considered

- **Keep 3.981:** a constant that folds a unit conversion (CMP-4.3) into a rounding of a rounding.
- **0.0195 with L in m (TxDOT):** a two-digit rounding of the converted constant, which WR-D-71-1 rounds differently
  (0.01947); no source confirms either digit as the formula's.
- **The exact metric 0.019472 as the constant:** it is 0.0078 multiplied by a conversion, which belongs to the units
  table, not to the formula.
- **Roussel et al.'s 3–10 %:** a rounding that leaves out one of Kirpich's own basins.
- **Cleveland et al.'s rule for Kerby-Kirpich** (the offset decided by the main-channel slope, with the band
  0.002–0.003 to the engineer): it changes results of watersheds with slopes on both sides of 0.002 and needs a
  decision on the band; it is the author's question.
