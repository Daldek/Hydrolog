# 0005. Adopt the shared error registry

- Status: accepted
- Date: 2026-10-24

## Context

ERR-3 requires a vendored copy of the registry and an error module generated from it;
ERR §4 maps the Hydrolog codes: `calculation_error` 4 to 13, `forbidden` 8 to 12 and an
unwritable output to `io_error` with reason `output_unwritable`.

## Decision

- `schemas/nogat/` holds verbatim copies of `error_registry.json` and the three agent
  schemas (Nogat commit `cc656e7`); `scripts/generate_errors.py` writes
  `src/hydrolog/_errors.py`; a contract test compares the module with the generator
  and validates error documents against `error-1`.
- `ERROR_CODES` lists the registry codes Hydrolog ends a call with: `internal_error`,
  `validation_error`, `not_found`, `conflict`, `missing_dependency`, `data_error`,
  `io_error`, `forbidden`, `calculation_error`, `cancelled` and `terminated`. Hydrolog
  adds no code of its own; finer precision is `details.reason`.
- The error document omits `hint` and `command` when empty and has an English `title`
  unless Polish is requested. On any error the last line of stderr is that document as
  compact JSON, in both CLI modes; Ctrl-C (130) is an outcome and prints no document;
  SIGTERM ends with `terminated` (143).

## Consequences

- **Breaking:** exit codes 4 and 8 become 13 and 12; exit code 4 now means `conflict`.
