# Hydrolog

> A Python library, CLI and MCP server for watershed hydrology: SCS-CN and curve numbers, design hyetographs, time of concentration, unit and runoff hydrographs, morphometry, flow statistics, hydrologic soil groups (HSG) from rasters, a Markdown report. It computes locally, with no network and no data downloads. <!-- hydrolog:summary -->

<!-- hydrolog:rules -->

- Interfaces: Python (`hydrolog.operations`, keyword arguments = the options of a command), the CLI `hydrolog <group> <command> --option value` (`--json` — the envelope on one line, `--schema` — the option schema) and the MCP server `hydrolog mcp --allow-dir DIRECTORY` (extra `hydrolog[mcp]`; a tool = an `operation_id`, e.g. `tc_kirpich`). Installation: `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`; the commands `soil hsg` and `soil hsg-stats` need the extra `hydrolog[raster]`.
- Result: the `hydrolog-result/1` envelope with the fields `inputs`, `result`, `files` and `notices` (pass the warnings on to the user).
- Error: a `hydrolog-error/1` document (`code`, `title`, `message`, `hint`, `details`; CLI: the last stderr line with `--json`); codes from a closed registry (CLI exit code in brackets): <!-- hydrolog:error_codes -->.
- Input data: CSV (comma or semicolon, a header row) or JSON; name a column with or without its unit (`Q` finds `Q [m3/s]`); a watershed is a `WatershedParameters` JSON.

Command groups (`hydrolog commands list`; options and examples: `hydrolog commands schema --command "<command>"`):

<!-- hydrolog:groups -->

Typical flows (CLI; in MCP call the tool `operation_id` with the arguments = the options; replace the symbols in capitals with your own values):

<!-- hydrolog:flows_short -->

## Documentation

- [AGENTS.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/AGENTS.md): the full guide for agents (in Polish) — rules, envelope and errors, file formats, every command with its options, flows in the CLI and MCP, what not to do
- [README.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/README.md): installation and examples of using the library (in Polish)
- [Scope](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/SCOPE.md): what is in and out of scope (Hydrolog downloads nothing)
- [Computation paths](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/COMPUTATION_PATHS.md): which time-of-concentration methods and parameters suit the unit hydrograph models (SCS, Nash, Clark, Snyder)
- [Integration](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/INTEGRATION.md): exchange of watersheds with Hydrograf (the `WatershedParameters` format)
- [Changes](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/CHANGELOG.md): changes per release

## Optional

- [Design 1.0.0](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/plans/2026-10-19-v1-catalog-mcp-hsg-spec.md): the command catalog, the MCP server, result serialization, HSG
- [Standards](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/DEVELOPMENT_STANDARDS.md): rules for working on the code
- [PRD](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/PRD.md): product requirements
