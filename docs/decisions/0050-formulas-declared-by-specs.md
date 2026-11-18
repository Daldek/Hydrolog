# 0050. Formulas declared by specs: Nogat's reference module, `formula_versions` in the envelope

- Status: accepted
- Date: 2026-11-18
- Builds on: Nogat's computation standard (standard 1.1, `standards/COMPUTATIONS.md`, CMP §1–§9, ECO-078) and its
  plan `docs/plans/2026-11-18-computation-standard.md` (step 5: Hydrolog, the SCS-CN and time of concentration
  families first)
- Amends: [ADR-0002](0002-result-envelope-and-domain-documents.md) (the envelope gains the optional
  `formula_versions`), [ADR-0017](0017-typical-ranges-in-the-catalog.md) (the ranges of a formula with a spec come
  from its spec)

## Context

Nogat's computation standard asks every project that computes to declare each Tier A formula once, in code, by a
`FormulaSpec` of the reference module `nogat_formulas.py` copied byte for byte (CMP-2.1, CMP-8.1); to leave every check
of its inputs and outputs to the module's `validate` and `check_outputs` (CMP-3.5), which refuse impossible input and
failed preconditions with `validation_error` and give a notice outside the applicability of the formula (CMP-3.1 to
CMP-3.4); to generate range, type and property tests from the spec, test reference cases of the sources and keep
oracles (CMP §6); to generate `docs/FORMULAS.md` and a card per formula (CMP-2.6); and to put on every result it exports
the `formula_version` of each formula the result depends on (CMP-2.8). Hydrolog checked its formulas by hand in each
module and kept the ranges of their data in `hydrolog._ranges` with the notice `outside_typical_range` (ADR-0017), whose
„typical range” is what the standard calls the applicability range. The catalog serves those ranges and quotes them in
the option descriptions without importing NumPy (the cold start of the MCP server, AGI-5.11), while the reference module
imports NumPy.

## Decision

1. **The copy and the adapter.** `src/hydrolog/nogat_formulas.py` is the reference module and
   `schemas/nogat/card-1.schema.json` the card schema (Nogat `c3423da`); neither is edited. `hydrolog._formulas` is
   Hydrolog's side: `ERRORS` turns a refusal into `InvalidParameterError` (code `validation_error`, `details.reason` of
   the standard, `details.option` the input) and a failed result into `CalculationError` (`calculation_error`);
   `checked_inputs(spec, **inputs)` and `checked_outputs(spec, outputs)` are the only checks a formula makes.
2. **Specs beside their functions.** A formula module declares its specs (`SPECS`) and its Tier B formulas (`TIER_B`)
   next to the functions; `hydrolog._formulas.FORMULA_MODULES` lists the modules with specs. A spec's function takes
   exactly its inputs, named with their units, and its docstring names the spec and holds no digit (CMP-2.7): the
   equation, constants, units and ranges are the spec's, and `docs/FORMULAS.md` shows them.
3. **The notice keeps its code.** `outside_applicability` of the standard is issued as Hydrolog's warning
   `OutsideTypicalRange`, code `outside_typical_range`, `method` the spec's name and `parameter` the input, so a
   consumer sees no change of code. The rename to `outside_applicability` changes the code for Hydrograf, Obserwator
   and the GUIs at once and is scheduled by the coordinator for one release (plan, step 5); until then the tests of
   the formulas read `outside_typical_range` as the standard's notice (`tests/unit/_formula_checks.py`).
4. **The catalog reads generated ranges.** `scripts/generate_formulas.py` writes, from the specs, `docs/FORMULAS.md`,
   the cards `formulas/<name>.toml` and `hydrolog._applicability`, the applicability ranges as plain data;
   `hydrolog._ranges` serves those ranges of the formulas with a spec (with their Polish source texts) and keeps the
   ranges of the formulas without one, so a range is written once. `tests/contract/test_formulas.py` checks the files
   fresh, the cards against Nogat's schema, each spec and its function (`spec_problems`) and the tolerances of the
   formula tests (`tolerance_problems`).
5. **`formula_versions` on the envelope.** Each formula with a spec records its `formula_version` when it returns
   (`hydrolog._formula_versions`); `run_command` records around the operation and the envelope `hydrolog-result/1`
   carries `formula_versions`, the spec name to its version, sorted, when such a formula gave the result (an optional
   field: AGI-4.1 keeps the version). Hydrolog keeps no store; the envelope is what it exports, and the stores of its
   consumers keep it with Hydrolog's `version`. A library caller reads the version from the spec
   (`hydrolog.time.concentration.KIRPICH.formula_version`).
6. **Tests.** `tests/conftest.py` loads the Hypothesis profiles of CMP-6.9 (`gate` by default, `HYPOTHESIS_PROFILE`
   selects `ci` or `nightly`); the tests of a formula family are `tests/unit/test_formulas_<family>.py`, marked
   `formula`, with the reference cases in `tests/fixtures/formulas/<family>-cases.json` (the format of
   `load_cases`) and the records of two transcriptions of a published table in `tests/oracles/`. Hypothesis and mutmut
   are development dependencies (CMP-8.3); mutation testing runs outside the gate (CMP-7.1).

## Consequences

- A formula with a spec refuses a NaN, an infinity, a `bool`, a string or a value outside its physical range in the
  library as well as in the commands, with the standard's `details.reason`, before it computes.
- Families get their specs one at a time (plan, step 5); until then their checks and `hydrolog._ranges` stay as they
  were, and `docs/FORMULAS.md` lists the formulas with a spec only.
- Code, docstrings and documents of a formula with a spec state its numbers through the spec: a docstring example
  with numbers moves to the class or the module.

## Alternatives considered

- **The ranges written in `hydrolog._ranges` and checked against the specs by a test:** the range would be written
  twice; generating the plain data keeps one declaration and the catalog without NumPy.
- **Importing the specs in the catalog:** NumPy at the cold start of the MCP server and of `hydrolog --help`.
- **Renaming the notice now:** Hydrograf, Obserwator and the GUIs read `outside_typical_range`; the rename belongs to
  one release of all of them.
- **`formula_version` in each domain document:** a command that uses several formulas (`hydrograph generate`) would
  need a field per formula; one map on the envelope covers every command and each formula family as it gets specs.
