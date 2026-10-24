# 0003. Writing commands: `--output`, `--force`, `--check`

- Status: accepted
- Date: 2026-10-24

## Context

DEV §19 (data output) binds a tool without a versioned store only through the names of
AGI-3.4: `--output` for the one file a command writes, `--output-dir` for plain files,
`--force` and `--check`. Hydrolog writes one file per command (`report generate`,
`soil hsg`, `commands guide`) and silently replaced an existing file before.

## Decision

- The output option is named `output` (`path_role: output`) in the three commands
  (`soil hsg` had `output_path`, `commands guide` had `path`). Hydrolog has no
  `--output-dir`, no `--root` and no store.
- An existing output file is replaced only with `--force`; otherwise the run fails with
  `conflict`, `details.reason = output_exists` and every offending path in
  `details.paths`, before anything is computed or written (DEV-19.6, DEV-19.9).
- `--check` returns the plan without effects: each target with `write`, `replace`
  (with `--force`) or `conflict`; a plan that lists a conflict is a successful result
  (DEV-19.10). Planning is shared by the operations in `operations/_outputs.py`.
- A command still writes through a temporary file beside the target and `os.replace`
  (`_atomic.py`); the staging directory `.hydrolog-incoming/` of DEV-19.7 is not used,
  because a single file written beside its target needs no cross-file verification.
  Listed as a deviation in `CLAUDE.md`.
- `commands guide --inject PATH` replaces the Hydrolog block in a consumer's AGENTS.md
  (AGI-8.2) and is idempotent; it edits an existing file, so it needs no `--force`.

## Consequences

- **Breaking:** an existing output is no longer replaced silently.
