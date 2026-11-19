# 0066. The soil texture and HSG tables as data: two specs, Kartograf as a frozen oracle, no texture of nothing

- Status: accepted
- Date: 2026-11-19
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (specs, Nogat CMP-2.5: a published table is a data file
  transcribed twice), [ADR-0051](0051-the-tr55-table-as-data-no-invented-fair-rows.md) (the first table as data), the
  audit of the formulas of 2026-11-18 (research `morphometry-soil.md` §7, §8, §11, §14; TRIAGE T17), Nogat's plan of
  the computation standard (step 5, and step 7: Kartograf's and Hydrolog's texture rules proven equal by one shared
  set of cases), Kartograf ADR-025 (the rules and the texture → HSG table, ported to Hydrolog 0.8.0)

## Context

`hydrolog.soil.texture` classified clay, sand and silt amounts into the twelve USDA texture classes with a tuple of
lambdas, one per class, and mapped the classes to the hydrologic soil groups A–D with a dictionary: two published
tables written into code, which CMP-2.5 forbids. The audit found the class limits right since the fix of T17 (clay
< 20 % and < 27 %), and the texture → HSG table described wrongly: „more lenient than the TR-55 table (USDA-NRCS NEH
Part 630, ch. 7)” in `docs/COMPUTATION_PATHS.md` and „deliberately milder” in the module, while sandy loam B is
stricter than TR-55's A and the table is TR-55's appendix A, not NEH's; the catalog and `docs/USAGE.md` did not
disclose the deviation at all. The scalar classifier returned `loam` for three zeros, a class of no soil, and took
strings and booleans (`float("5")`, `float(True)`).

## Decision

1. **The class definitions are data.** `src/hydrolog/_data/tables/usda_texture_classes.csv` holds the definitions of
   the Soil Survey Manual (Soil Science Division Staff 2017, USDA Handbook 18, ch. 3, pp. 122–124): one row per
   crisp inequality `a clay + b sand + c silt <relation> k` percent of the total, with the class, its alternative
   (sandy loam and silt loam have two), the page and the Manual's words; 41 rows. The sand ranges the Manual gives
   in words for sands („more than 85 percent”) and loamy sands („between 70 and 90 percent”) follow from their
   other inequalities and are not rows. The spec `usda_texture` (`classify_usda_texture(clay, sand, silt)`, family
   `classification`) records its SHA-256; the code evaluates the rows as `100 (a clay + b sand + c silt) <relation> k
   (clay + sand + silt)` in `float64` after scaling the three amounts by one power of two: no division, no overflow,
   and exact for integer amounts (the g/kg of SoilGrids, lab percentages). The arguments keep their names: the
   classifier is unit-free (any unit the three share), a convention of the spec and its property `unit_free`.
2. **Two transcriptions.** `tests/oracles/usda_texture_classes_first.csv` (typed from the Manual's text by the
   author of the spec) and `tests/oracles/usda_texture_classes_second.csv` (typed by a second agent given only the
   Manual's pages and the format) are identical, and equal to the data file as sets of rows
   (`tests/unit/test_formulas_texture.py`).
3. **Kartograf is the frozen oracle.** `tests/oracles/kartograf_texture_oracle.py` ran Kartograf 0.8.2's
   `classify_usda_texture_array` (its own copy of the rules) once over all 5,151 integer percent compositions and
   all 501,501 integer g/kg compositions; the percent grid is stored as rows, the g/kg grid run-length encoded along
   sand (2,452 runs). Hydrolog's classifier equals it on every composition, the percent grid ×10 is a subgrid of the
   g/kg grid, and the package table evaluated in exact rationals (`fractions.Fraction`, CMP-6.2) agrees on the
   percent grid and on drawn integer compositions. This is the shared set of cases of the plan's step 7.
4. **A zero total has no texture.** The class is a function of the shares of the total, undefined for a total of
   zero: `classify_usda_texture` and `soil texture` refuse it with the precondition `positive_total`
   (`precondition_failed`; `soil texture` refused it before with the reason `no_data`). The array classifier keeps
   its documented no-data convention as the Tier B `usda_texture_codes`: a cell with a zero total or a NaN or an
   infinite amount gets the code of loam as a placeholder (an infinite amount gave an arbitrary class before), and
   `classify_hsg` (Tier B `hsg_of_amounts`) masks such cells as no data, as it did.
5. **The texture → HSG table is data with a source per row.** `src/hydrolog/_data/tables/texture_hsg.csv`, the spec
   `texture_hsg` (`texture_to_hsg(texture_class)`); `TEXTURE_TO_HSG` is read from it. Eight rows follow TR-55
   (USDA-SCS 1986, appendix A, p. A-1); sandy loam B and clay loam and silty clay loam C follow the textures NEH 630
   ch. 7 (2009, p. 7-2) names as typical of groups B and C; silt, which TR-55 does not list, takes the B of silt loam
   (NEH: well aggregated silt may be B). No letter changes. The comparison transcriptions are TR-55's table read
   from the PDF's text layer (`tests/oracles/transcribe_tr55_hsg.py`), which differs exactly on the three NEH rows,
   and Kartograf 0.8.2's `TEXTURE_TO_HSG`, frozen with its Rawls (1982) Ksat values; the property
   `not_milder_as_ksat_falls` holds along the order of falling Ksat of Rawls et al. (1982).
6. **The descriptions say what the table is.** The module, `docs/COMPUTATION_PATHS.md`, `docs/USAGE.md`, the
   catalog of `soil texture` and the operation's docstring state the hybrid: stricter than TR-55 for sandy loam,
   milder for the two clay loams, silt as silt loam. The docstrings of the two formulas name their specs and hold no
   digit (CMP-2.7); the numeric examples are in the module's docstring.

## Consequences

- `classify_usda_texture(0, 0, 0)` raises where it returned `"loam"`; a string, a `bool`, NaN or an infinity is
  refused with the standard's `details.reason` (`invalid_type`, `outside_physical_range`), a negative amount too
  (with `details.reason` now). `soil texture` with three zeros fails with `precondition_failed` and
  `details.constraint` `positive_total` instead of `no_data`; the web GUI words it and marks the clay field.
- `texture_to_hsg` refuses an unknown class with `invalid_choice` and `details.choices` (was `details.allowed`).
- `classify_usda_texture_array` gives an infinite amount the loam placeholder; `classify_hsg` is unchanged.
- `soil texture` and `soil hsg` results carry `formula_versions` `{"texture_hsg": 1, "usda_texture": 1}`.
- Kartograf keeps its own copy of the rules and the table (its scalar classifier still accepts negative amounts and
  maps an unknown class to B, TRIAGE T20); the frozen oracle proves the copies equal on every integer composition
  until Kartograf calls Hydrolog's.

## Open question

**Q2 (research §14): which texture → HSG table?** The table is a hybrid of TR-55 appendix A (for disturbed urban
profiles) and NEH 630 ch. 7's typical textures. NEH 630 ch. 7, by its typical textures and by its table 7-1 applied
to Rawls' class Ksat, would also put loam and silt loam (the loess soils of southern Poland) and silt in C and
loamy sand in B; returning to TR-55 would make sandy loam A and the two clay loams D. Either change moves the curve
numbers of every consumer (Hydrograf, Kartograf); it is the author's decision and stays open.

## Alternatives considered

- **Keep `loam` for a zero total in the scalar classifier:** a class of no soil, returned silently; `soil texture`
  already refused it, and the raster path keeps its no-data placeholder.
- **The class limits as a table of ranges per fraction:** the Manual's sands and loamy sands are defined by `silt +
  1.5 clay` and `silt + 2 clay`, which a range per fraction cannot express; linear inequalities express every
  definition as worded.
- **A frozen oracle of R `aqp::ssc_to_texcl`:** R is not installed; its NASIS logic was read and agrees on the
  reference cases (their second source), and Kartograf's classifier is the consumer whose equality matters.
