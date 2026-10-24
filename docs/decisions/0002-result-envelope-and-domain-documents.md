# 0002. Result envelope and domain documents

- Status: accepted
- Date: 2026-10-24

## Context

The v1 envelope `hydrolog-result/1` had `hydrolog_version`, `inputs`, top-level `files`
and notices with `text`. The Nogat `result-1` schema (AGI-4.2) names the fields `tool`,
`version`, `check`, `status`, `result`, `items`, `notices`, `page`, and requires `result`
to be a document with its own `schema` (AGI-4.1). DEV-19.19 puts the written files in the
domain result as `{path, size_bytes, sha256, status}`.

## Decision

- The envelope has `schema`, `tool`, `version`, `command`, `check`, `status`, `result`,
  `notices` (`level`, `code`, `message`), `inputs` (a Hydrolog addition: the normalized
  options of the call) and, for collections, `page`. There are no `items`: Hydrolog has
  no batch commands, and `status` is `ok` (a failing command raises).
- `result` is the `to_dict()` of the operation result with `schema` first, taken from the
  catalog (`Command.result_schema`, `hydrolog-<group>-<verb>/1`); the envelope adds it,
  so `to_dict()` of a library result object has no `schema` key (a deviation from
  AGI-4.4, listed in `CLAUDE.md`). A result that is not a mapping is a program error.
- Files written by a command are `result.files[]` with `status` `written` or `replaced`.
- The domain schemas are published in `src/hydrolog/schemas/` and the catalog entry names
  the id of each in `result.schema`.
- A `check` run returns the plan document `hydrolog-plan/1`.

## Consequences

- **Breaking:** `hydrolog_version` is `version`; `files` moved into `result`; notices
  have `message` instead of `text`.
