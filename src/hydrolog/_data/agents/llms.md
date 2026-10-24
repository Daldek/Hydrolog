# Hydrolog

> A Python library, CLI and MCP server for watershed hydrology: SCS-CN and curve numbers, design hyetographs, time of concentration, unit and runoff hydrographs, morphometry, flow statistics, hydrologic soil groups (HSG) from rasters, a Markdown report. It computes locally, with no network and no data downloads.

Hydrolog is not for spatial data (DEM, land cover, SoilGrids rasters), which Kartograf provides, or for IMGW/CHMU measurement series, which IMGWTools exports to CSV.

Interfaces: Python (<!-- hydrolog:python_example -->), the CLI (`hydrolog <group> <verb> --option value --json`) and the MCP server (`hydrolog mcp --allow-dir DIR`; a tool is an `operation_id`). Install with `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`; the extras are `raster`, `mcp`, `viz` and `all`.

Work in four steps: discover (`hydrolog commands list`, `hydrolog commands schema --command NAME`), check (`--check` for commands that write a file), run, read (`result`, `notices`, `result.files`). A result is a `hydrolog-result/1` envelope; an error is a `hydrolog-error/1` document whose `code` is one of: <!-- hydrolog:error_codes -->.

Command groups: <!-- hydrolog:group_names -->.

## Documentation

- [AGENTS.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/AGENTS.md): the full guide for agents: interfaces, envelope, error codes, command index, typical flows
- [README.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/README.md): what Hydrolog is for, installation, quick start and MCP client configuration
- [Usage](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/USAGE.md): task-oriented guide to the CLI, the Python interface and the MCP server
- [Computation paths](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/COMPUTATION_PATHS.md): which time-of-concentration methods and parameters suit the unit hydrograph models
- [Scope](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/SCOPE.md): what is in and out of scope
- [Integration](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/INTEGRATION.md): exchange of watersheds with Hydrograf (the `WatershedParameters` format)
- [Changelog](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/CHANGELOG.md): changes per release

## Optional

- [Design 1.0.0](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/plans/2026-10-19-v1-catalog-mcp-hsg-spec.md): the command catalog, the MCP server, result serialization, HSG
- [PRD](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/PRD.md): product requirements
- [Decisions](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/DECISIONS.md): architecture decision records
