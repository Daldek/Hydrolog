# 0009. One index line for a command group that would not fit the guide

- Status: accepted
- Date: 2026-10-24

## Context

`AGENTS.md` is generated from the catalog and may have 200 lines and 16 KiB (DOC-1.7);
it had 164 lines and 16,073 bytes, 311 bytes below the limit, with one index line per
command (DOC-4.2). The `route` group adds up to six commands, about 700 bytes with its
heading. The report [2026-10-24-long-term-and-routing.md](../plans/2026-10-24-long-term-and-routing.md)
(section 6.2, decision D10) lists three ways out: shorter summaries and flows,
one line per group for large groups, or a larger budget from Nogat (the limit is stated
only in DOC-1.7).

## Decision

- A group named in `_COMPACT_GROUPS` of `hydrolog.agent_guide` prints one index line
  that names every command of the group in catalog order and the rule for the tool
  names, with a sentence about the group; every other group keeps one line per command.
  Only `route` is compact.
- Nothing is dropped from the guide: `commands list` still gives each command with its
  summary, `commands schema` its options, units, examples and rules, and the MCP tools
  are unchanged. The index of the guide is shorter for one group only.
- The departure from "one line per command" (DOC-4.2) is a deviation listed in
  `CLAUDE.md`. The guide text that the templates carry (purpose, scope, "not for") was
  edited to match the new scope instead of being cut.

## Consequences

- `AGENTS.md` stays below 16 KiB when the group has six commands; a command added to a
  compact group costs about 25 bytes instead of 130.
- The contract test of the index checks that every command is named exactly once, in
  catalog order, either on its own line or on the line of its compact group.
- If the guide outgrows the budget again, shortening the summaries or asking Nogat for a
  larger budget are the remaining options of the report.
