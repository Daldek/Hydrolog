# 0001. English catalog, Polish in `i18n.pl`, `hydrolog_` operation ids

- Status: accepted
- Date: 2026-10-24

## Context

The v1 catalog was authored in Polish with English translations (`summary`,
`summary_en`), and its `operation_id` was `<group>_<verb>` (`tc_kirpich`). Nogat
standard 2.1 requires English authored texts with Polish next to them (AGI-9.1),
operation ids `<tool>_<group>_<verb>` that are unique in the ecosystem (AGI-2.2),
MCP descriptions within 600 characters (DOC-1.7) and the fields `effects`, `check`,
`families`, `rules`, `examples` with a result, `errors` and `result`.

## Options considered

1. Keep Polish primary and add the missing fields (violates AGI-9.1).
2. English primary; Polish as `*_pl` fields serialized under `i18n.pl`.
3. Translations in separate resource files keyed by id.

## Decision

Option 2. `Command` and `Option` carry English `summary`, `description`, `rules` and
`description`, plus `summary_pl`, `description_pl`, `rules_pl`; the catalog document
(`hydrolog-commands/1`, the Nogat `commands-1` schema) puts the Polish texts under
`i18n.pl`. `operation_id` is `hydrolog_` plus the command name with underscores (at most
48 characters), also the MCP tool name; `function` is a dotted path. `effects`, `check`
and `families` are derived from the declaration (a command writes when an option has
`path_role="output"`; its `check` is the command itself; the family is the group, plus
`core` for the main commands, at most ten). Choice options declare a meaning per value. Hydrolog
adds `one_of` (the alternative option groups) to the command entry and gives every option
of such a group `one_of: "alternatives"`, because the standard's per-option identifier
cannot express groups of several options. The declaration checks itself at import:
summary at most 100 characters, summary + description + rules at most 600 characters.
Method details and literature moved out of the descriptions into
`docs/COMPUTATION_PATHS.md`.

## Consequences

- **Breaking:** operation ids and MCP tool names gain the prefix; `commands schema`
  returns the new document; the `lang` option of the `commands` group is gone.
- Machine output (JSON, MCP, guides) is always English; the CLI's human output follows
  `--lang`.
- Adding a command means filling all fields; the catalog contract test runs every example.
