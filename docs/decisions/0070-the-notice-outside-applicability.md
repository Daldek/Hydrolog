# 0070. The notice `outside_applicability`: the standard's code for an input outside its applicability

- Status: accepted
- Date: 2026-11-21
- Amends: [ADR-0015](0015-catalog-additions-for-the-gui.md) (the warning `OutsideTypicalRange` and its code),
  [ADR-0017](0017-typical-ranges-in-the-catalog.md) (the `notice` of a typical range),
  [ADR-0050](0050-formulas-declared-by-specs.md), point 3 (the notice kept its code until the rename) and
  [ADR-0064](0064-notices-of-applicability-constraints-and-unreferenced-formulas.md), point 4 (no new code before the
  rename)
- Builds on: Nogat's computation standard (`standards/COMPUTATIONS.md`, CMP-3.3) and its plans
  `2026-11-18-computation-standard.md` (step 5) and `2026-11-19-hydrolog-0.9.0-consumers.md` (step 1)

## Context

CMP-3.3 gives an input inside its physical range but outside its applicability range, and a violated applicability
constraint, a notice of level `warning` with the code `outside_applicability`. Hydrolog issued it as
`outside_typical_range` (warning `OutsideTypicalRange`), its code since ADR-0015, so that no consumer saw a new code
before one release renamed it for all of them (ADR-0050, point 3; ADR-0064, point 4). That release is 0.9.0, a minor
with other breaking changes, whose consumers (Hydrograf, Retman, Obserwator) move to it together (the plan of the
consumers, step 1).

## Decision

1. **The code is `outside_applicability`.** The warning is `hydrolog._warnings.OutsideApplicability` (its code is its
   class's name in snake_case), issued by `warn_outside_applicability`; `OutsideTypicalRange` and
   `warn_outside_typical_range` are gone, with no alias (a clean cut in a minor release, REL-1.1). The level and the
   `details` keys are unchanged: `method`, `parameter`, `field`, `value`, `minimum`, `maximum`, `constraint`,
   `condition`, `source`.
2. **Its words say applicability.** English: „is outside its applicability range [a, b]”, „is below its
   applicability range, from a”, „is above its applicability range, up to b”; the GUI's Polish: „poza zakresem
   stosowania” (the term of the GUI's confirmations „w zakresie stosowania”), a field's warning „Poza zakresem
   stosowania od … do …”, the summary of Hydrogram's step 3 „Poza zakresem:”.
3. **`outside_unverified_range` is unchanged.** A range without a published source keeps its code, details and
   words; `OutsideUnverifiedRange` subclasses `OutsideApplicability`, so a filter on the latter catches both, as it
   did on `OutsideTypicalRange`.
4. **The catalog keeps `typical_ranges`.** `typical_ranges[].notice` of `hydrolog-commands/1` names
   `outside_applicability`; the field and `hydrolog._ranges.TYPICAL_RANGES` keep their names (Hydrolog's typical
   range is the standard's applicability range, ADR-0050), since renaming the field is another interface change.

## Consequences

- Breaking for every client that reads the code or the class: Hydrograf (its map of notice codes to Polish text,
  tests and docs) and Retman (its translations keyed by code) change in the same release; Obserwator's GUI has no
  label of the code.
- The released CHANGELOG sections, the ADRs before this one and the plans keep the old code as history.

## Alternatives considered

- **An alias `OutsideTypicalRange = OutsideApplicability`:** a deprecated path the standard's clean cut-over avoids;
  a filter on the old name would keep working while the code it sees changed anyway.
- **Rename the catalog field `typical_ranges` too:** a second breaking change of `hydrolog-commands/1` that CMP-3.3
  does not ask for.
