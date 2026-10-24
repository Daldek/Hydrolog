# 0006. MCP server conformance with AGI section 5

- Status: accepted
- Date: 2026-10-24

## Decision

- Tool names are the catalog `operation_id`s; descriptions are summary + description +
  rules in English (at most 600 characters, enforced by the catalog); `inputSchema` is
  JSON Schema 2020-12 without the top-level `oneOf` that clients reject (the alternatives
  are named in the property descriptions); `outputSchema` is the result envelope;
  results carry `structuredContent` and the same JSON as text; execution errors are
  `isError` results holding the `hydrolog-error/1` document.
- The server starts read-only: without `--allow-writes` the writing tools run in `check`
  mode and report `readOnlyHint: true`; with it they write inside `--allow-dir`
  directories only. Every path option is checked against `--allow-dir` (`forbidden`).
  Hydrolog has no default store root, so DEV-19.3 reduces to this rule.
- `--tools` selects families (the groups and `core`, at most ten tools). The two catalog
  tools `hydrolog_commands_list` and `hydrolog_commands_schema` carry
  `anthropic/alwaysLoad`.
- Instructions are English and at most 4096 characters. Start and `tools/list` import no
  numerical library (a test measures it). The console script `hydrolog-mcp` starts the
  same server as `hydrolog mcp`; the SDK is pinned `mcp>=2.3,<3`.
- No MCP resources or prompts (AGI-5.9 makes them optional).

## Consequences

- **Breaking:** tool names gain the prefix; `--lang` is removed from the server.

## Errata

- 2026-10-24: an explicit `--lang` when the server starts is refused, not ignored: `hydrolog mcp --lang en`,
  `hydrolog --lang en mcp` and `hydrolog-mcp --lang en` end with `validation_error` (exit code 2,
  `details.reason = ineffective_option`), because the server output is always English. `--lang`
  still selects the language of `hydrolog mcp --help`.
