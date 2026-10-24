# 0004. Shared settings and `config show`

- Status: accepted
- Date: 2026-10-24

## Context

DEV-18 gives every `tool` one settings file (`nogat.toml`), a fixed precedence and a
command `<tool> config show --json` that reports each key with its value and source,
the credentials and the store root.

## Decision

- Hydrolog has two settings: `lang` (language of human-readable output; default `pl`)
  and `log_level` (verbosity of the CLI log on stderr; default `warning`). Precedence:
  command-line option, `HYDROLOG_<KEY>`, `NOGAT_<KEY>`, `nogat.toml` `[hydrolog]`, then
  `[nogat]`, then the default. An invalid ambient value is ignored, so a broken settings
  file never stops a calculation.
- The file is `platformdirs.user_config_path("nogat")/nogat.toml` or `NOGAT_CONFIG`;
  `platformdirs` is the only new runtime dependency.
- `data_dir` and `cache_dir` are not used: Hydrolog writes no store and no cache.
- `config show` is a catalog command (group `config`), so it is available through the
  CLI, MCP and Python. It reports `settings`, `config_file`, `credentials` (none) and
  `store` (null). Options given on the command line apply to their own call and are not
  reported.

## Consequences

- `nogat doctor` can read Hydrolog's configuration from the tool itself (DEV-18.6).
