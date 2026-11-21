# 0064. Notices of applicability constraints and of unreferenced formulas

- Status: accepted
- Date: 2026-11-19
- Amended by [ADR-0070](0070-the-notice-outside-applicability.md) (2026-11-21): point 4, the notice's code is `outside_applicability`
- Builds on: [ADR-0050](0050-formulas-declared-by-specs.md) (formulas declared by specs) and Nogat's computation
  standard (CMP-3.3, the notice of a violated applicability constraint; CMP-5.1, the notice of a formula without
  evidence)
- Amends: [ADR-0050](0050-formulas-declared-by-specs.md), point 3 (the notice `outside_typical_range` also carries a
  violated applicability constraint, with three more details)

## Context

ADR-0050 issues the standard's notice `outside_applicability` as Hydrolog's warning `OutsideTypicalRange`, code
`outside_typical_range`, for an input outside its applicability range, so that no consumer sees a new code before the
coordinated rename (plan of the computation standard, step 5). Two notices of the standard had no warning in the library
and `hydrolog._formulas` refused them with a `TypeError`:

- **A violated applicability constraint** (CMP-3.3): a condition between inputs, or on their number, under which a
  formula was derived. The station statistics have the first one: WMO-No. 1044 (2010, Vol. II, sect. 1.5.1,
  p. II.1-3) wants at least 12 to 15 gaugings for a rating curve, while Hydrolog fits one from 3 pairs.
- **An unreferenced formula** (CMP-5.1): a formula with neither a reference case nor an oracle gives the notice
  `unreferenced_formula` at level `info` on every result. The station statistics have two: Rybczyński's water-level
  zones, whose source (Rybczyński 1923, 1932) the audit could not open, and the plausibility rule of a rating curve
  ([ADR-0041](0041-implausible-rating-curves-flagged-not-refused.md)), Hydrolog's own.

## Decision

1. **A violated applicability constraint is `outside_typical_range` of the quantity it bounds.** The formula module
   declares, beside the spec, the quantity, its value from the checked inputs and its range
   (`hydrolog._formulas.constraint_range(spec, constraint, parameter=…, value=…, minimum=…, maximum=…)`); the notice
   names it in `parameter`, with `value`, `minimum` and `maximum` as for an input. The rating curve's fit declares
   `gaugings`, the number of pairs, with the minimum 12 and no maximum (constraint `enough_gaugings`).
2. **Three more details on `outside_typical_range`.** `constraint`, `condition` and `source` give the name, the text
   and the source of the violated constraint; they are `null` for an input outside its own range. A range with one end
   (`minimum` or `maximum` `null`) is worded by that end („… is below its typical minimum 12”). Every notice of the
   code carries the three keys, because the warnings of the library have fixed details. The message stays a function
   of the code's registry entry and the details (plan D16 of the GUI): `NoticeSpec.message(details)` fills the
   template, or, for a code made from a library warning (`NoticeSpec.warning`), words it by the class
   (`HydrologWarning.message_of(details)`), which is how a range with one end gets its own sentence.
3. **The notice `unreferenced_formula`.** `hydrolog._warnings.UnreferencedFormula`, level `info`, details `formula`,
   `title` and `formula_version`, is issued on every result of a spec with the status `unreferenced`
   (`rating_curve_plausibility` and `rybczynski_zones` from this release). The catalog lists it, and the web GUI words
   it in Polish.
4. **No new code before the rename.** Both notices keep the codes of the standard that consumers will see after the
   rename: `unreferenced_formula` is the standard's own code, and `outside_applicability` stays issued as
   `outside_typical_range` until Hydrograf, Obserwator and the GUIs change together.
5. **A contract test** checks that every applicability constraint of every spec has its declared range, so a new one
   cannot reach `_issue` without its warning.

## Consequences

- `hydrometrics rating-curve` gives `outside_typical_range` with `parameter` `gaugings` below 12 pairs and
  `unreferenced_formula` on every result; `hydrometrics water-level-zones` gives `unreferenced_formula`.
- Additive for every consumer of `outside_typical_range`: the three keys are new and `null` for the notices of the
  existing formulas (tc, SCS-CN, Lutz, the unit hydrographs). A consumer that compares the details of the notice as a
  whole (Hydrograf's and Obserwator's tests) must expect them; a consumer that words the notice must accept a `null`
  `maximum`.
- Obserwator's GUI needs a text for `unreferenced_formula`, which its stored `rating_curve` and `water_level_zones.H`
  analyses now carry.

## Alternatives considered

- **A new code for a violated constraint** (`outside_applicability` now, or `outside_typical_conditions`): a code
  that consumers do not know, one release before the rename that changes it anyway.
- **The keys only on a constraint's notice:** the warnings of the library have fixed details; optional keys would need
  another mechanism for one notice.
- **The number of gaugings as an input of the fit:** it is the length of the arrays, not a value the caller chooses.
