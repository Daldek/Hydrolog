# Hydrolog — guide for agents

> A file generated from the command catalog: `hydrolog commands guide --format agents --lang en`.
> Do not edit it by hand. The Polish version is the one in the repository: `hydrolog commands guide --format agents --lang pl --path AGENTS.md`.

## What Hydrolog is

Hydrolog is a Python library, the `hydrolog` CLI and an MCP server for watershed hydrology: SCS-CN effective precipitation and curve numbers (TR-55), design hyetographs, time of concentration, unit hydrographs and the runoff hydrograph, morphometry of watersheds and river networks, flow statistics (characteristic values, flood and low-flow frequency, the Mann–Kendall test), rating curves and water-level zones, hydrologic soil groups (HSG) from soil texture rasters and a calculation report in Markdown. It computes locally: no network, no keys, no data downloads — measurement series come from IMGWTools, rasters (DEM, land cover, soils) from Kartograf. Every interface is generated from one command catalog, so they share option names, validation, the result envelope and the error codes. <!-- hydrolog:summary -->

Abbreviations in option names and results: `tc` — time of concentration [min]; `CN` — Curve Number (1–100); `AMC` — antecedent moisture condition (I, II, III); `Ia` — initial abstraction (`ia_coefficient` times the retention, 0.2 by default); `HSG` — hydrologic soil group (A–D); `UH` — unit hydrograph (the models `scs`, `nash`, `clark`, `snyder`); `WWQ` … `NNQ` — second-degree characteristic values.

## Rules

<!-- hydrolog:rules -->

## Installation and running

- Installation (Python ≥ 3.12; dependencies: NumPy and SciPy): `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`. Extras: `hydrolog[raster]` (rasterio and pyproj; the commands `soil hsg` and `soil hsg-stats`), `hydrolog[mcp]` (the MCP server), `hydrolog[visualization]` (plots in Python, outside the command catalog) and `hydrolog[all]`, e.g. `pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"`.
- CLI: `hydrolog <group> <command> --option value` (also `python -m hydrolog.cli …`). The flag of an option is `--` and its name with `-` instead of `_`; a list of numbers is comma-separated (`--return-periods 10,50,100`), an object or a list of objects is JSON text (`--parts '[{"cn": 55, "area": 27.2}]'`), a boolean is `--flag` or `--no-flag`. General flags: `--json` (the result envelope on one line of stdout), `--schema` (the option schema of the command, nothing is run), `--lang pl|en` (the language of help and messages; the variable `HYDROLOG_LANG`, `pl` by default), `-V` (version).
- MCP: `hydrolog mcp --allow-dir DIRECTORY` (`--allow-dir` can be repeated, `--lang pl|en` selects the language of the tool descriptions). Claude Code: `claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data`; other clients: `{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}}}`. A tool is named like the `operation_id` of the command and its arguments are the options; without `--allow-dir` commands with path options are refused (`forbidden`), commands without files work.

## Interfaces

| Interface | Discovery | Call | Result | Error |
|---|---|---|---|---|
| Python | `data_commands()`, `command_schema()` from `hydrolog.catalog` | a function of `hydrolog.operations` (keyword arguments = options) or `run_command("<group> <command>", {...})` | a result object with `to_dict()` and `to_json()`; `run_command` returns the envelope (`CommandResult`) | a `HydrologError` exception (`code`, `hint`, `details`) |
| CLI | `hydrolog commands list`, `hydrolog commands schema`, `--schema` | `hydrolog <group> <command> --option value` | a text summary; with `--json` the envelope on one line of stdout | text on stderr or, with `--json`, one `hydrolog-error/1` line; the exit code from the registry |
| MCP | `tools/list` | the tool `<operation_id>` with the arguments = the options | `structuredContent` = the envelope (the same JSON as text) | `isError: true` and a `hydrolog-error/1` document |

<!-- hydrolog:call_example -->

Besides the command catalog the library has classes for use in code (`hydrolog.runoff`, `hydrolog.time`, `hydrolog.precipitation`, `hydrolog.morphometry`, `hydrolog.network`, `hydrolog.statistics`, `hydrolog.hydrometrics`, `hydrolog.soil`, `hydrolog.reports`); plots (`hydrolog.visualization`, the extra `hydrolog[visualization]`) exist in Python only. They are described by the README and the docstrings.

## The result envelope and errors

A command returns the `hydrolog-result/1` envelope: `{"schema", "command", "hydrolog_version", "status", "inputs", "result", "files", "notices"}`.

- `inputs` — the options after normalization: defaults filled in, paths absolute. This is what the result was computed with.
- `result` — the values of the command; its shape depends on the command (the command description in `commands schema` gives it), units follow from the field names (`tc_min`, `peak_discharge_m3s`), and `NaN` and infinities are `null`.
- `files` — the files written by a command with an output option: `{"role", "path", "sha256"}`.
- `notices` — non-fatal warnings `{"level", "code", "text"}` (a short series, a value outside the typical range of a formula, skipped gaps): pass them on to the user together with the result.
- `status` is always `ok`: a command that fails ends with an error, not with an envelope holding a partial result — computations are atomic.

An error is a `hydrolog-error/1` document: `{"schema", "code", "title", "message", "hint", "details", "exit_code", "command"}`. The `code` comes from the closed registry below and is the same in Python (`HydrologError.code`), the CLI (the exit code; with `--json` one JSON line on stderr) and MCP (`isError`). `details.option` names the faulty option and `details.reason` the cause (among others `required`, `type`, `minimum`, `maximum`, `choice`, `unknown_option`, `one_of`); `message` and `hint` are in English, `title` is in the language of `--lang`. The CLI also exits with 130 after Ctrl+C.

<!-- hydrolog:errors -->

## Input data

- **Series** (`values` with `dates`, or `input_file` with `value_column` and possibly `date_column`; the exact alternatives are in the "Options" column of the command tables): a CSV file (comma or semicolon, UTF-8, a header row) or JSON (a list of records, an object of columns or a list of numbers). Numbers `12.5` or `12,5`; an empty cell, `NaN`, `NA` and `null` are gaps; dates ISO `YYYY-MM-DD`, strictly increasing. Name a column exactly or without its unit suffix (`Q` finds `Q [m3/s]`). The CSV exported by IMGWTools (`series export`) loads without preprocessing.
- **Watershed** (`watershed_file` or `watershed`): JSON in the `WatershedParameters` format (`to_json()`); `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` and `elevation_max_m` are required, among the optional ones `name`, `elevation_mean_m`, `mean_slope_m_per_m`, `channel_length_km`, `channel_slope_m_per_m` and `cn`. The fields a method needs are listed in the command description; a missing field is a `validation_error` listing what is missing.
- **Rain gauges** (`precip areal`: `stations` or `stations_file`): records `name`, `x`, `y`, `precipitation_mm`, optionally `elevation_m`.
- **River network segments** (`network stats`: `segments` or `segments_file`): the columns `segment_id`, `upstream_ids` (in a CSV the ids are separated by a semicolon, e.g. `3;4`) and `length_km`.
- **Rasters** (`soil hsg`, `soil hsg-stats`; the extra `hydrolog[raster]`): GeoTIFF. The clay, sand and silt rasters must share the coordinate system, the grid and the size (otherwise `data_error`); any units, but consistent ones (SoilGrids: g/kg). The result of `soil hsg` is a `uint8` GeoTIFF: 0 — no data, 1–4 are the groups A–D.

## Commands

The table of each group gives the command, the name of the MCP tool (`operation_id`), the description, the options in catalog order (`*` — required, `=` — default value; the CLI flag is `--` and the option name with `-` instead of `_`) and the effect of a run: `read`; `write (replaces an existing file)` — the command writes the file named by an output option; `read; option: write…` — it writes only when you give that option. No command uses the network. The full option schema (units, bounds, examples): `hydrolog commands schema --command "<command>"`.

<!-- hydrolog:commands -->

## Typical flows

Every step is a CLI line with an MCP call under it (the tool and its arguments); in Python the same options are the keyword arguments of the function in `hydrolog.operations`. The paths `/dane/...` are examples — give your own, absolute and (in MCP) inside an allowed directory. Symbols written in capitals (<!-- hydrolog:flow_symbols -->) stand for values taken from IMGWTools; the `imgw` and `kartograf` lines are separate tools of the ecosystem, not Hydrolog commands.

<!-- hydrolog:flows -->

## What not to do

1. Do not paste long series into arguments — save them to a CSV or JSON file and give the file (`input_file`).
2. Do not guess options, units or values the user did not give; slope is in m/m (not %), precipitation in mm, time in minutes.
3. Do not parse the English `message` or `hint` — decide by `code`, `details.option`, `details.reason` and the exit code; `hint` is for fixing the argument.
4. Do not ignore `notices`: pass the warnings (a short series, a value outside the range of a formula, skipped gaps) on to the user together with the result.
5. Do not silently choose one method (of time of concentration, of the unit hydrograph, of the distribution) when they give different results — show the differences or justify the choice.
6. Do not combine time-of-concentration formulas with every unit hydrograph model: SCS and Clark take `tc`, Nash takes `n` and `K` (the Lutz method, the urban regression or given values), Snyder takes `Ct` and `Cp` and no external `tc` (`docs/COMPUTATION_PATHS.md`).
7. Do not repeat a call without changing it: `validation_error`, `data_error` and `calculation_error` need the options or the data corrected.
8. Do not overwrite input files: the output options (`output`, `output_path`, `path`) replace an existing file without asking, and `report generate` refuses when `output` is an input file.
9. Do not expect a network or data downloads: measurement series come from IMGWTools, rasters (DEM, land cover, soils) from Kartograf.
10. In MCP do not guess paths: give absolute ones inside the `--allow-dir` directories; `forbidden` lists the allowed ones in `details.allowed_dirs`.
11. Do not run `soil hsg` or `soil hsg-stats` without the extra `hydrolog[raster]` (`missing_dependency`).
12. Do not treat the HSG as the CN: the soil group is one of two factors — the CN also needs the land cover (`cn list`, `cn lookup`, `cn weighted`).
13. Do not edit `AGENTS.md` or `llms.txt` by hand — regenerate them with the command from the header.

## Working on the repository code

This file describes how to use Hydrolog. When changing the code, `CLAUDE.md` (environment, branches, conventions), `docs/DEVELOPMENT_STANDARDS.md` (standards), `docs/SCOPE.md` (scope: Hydrolog downloads nothing) and `docs/PROGRESS.md` (the state of the work) apply; changes for users go to `docs/CHANGELOG.md`. The gate: `.venv/bin/python -m pytest tests/`, `.venv/bin/python -m black --check hydrolog/ tests/` and `.venv/bin/python -m mypy hydrolog/`.

**How to add a command** (details: the docstring of `hydrolog/catalog/__init__.py`):

1. The operation: a public, documented (NumPy docstring), fully type-hinted function whose keyword arguments are named like the options, in `hydrolog/operations/<group>.py`; it returns a result with `to_dict()` or an `OperationOutput` (notices, written files); export it in `hydrolog/operations/__init__.py`.
2. The declaration: `Command` and `Option` in `hydrolog/catalog/groups/<group>.py` (the `COMMANDS` tuple): the name `<group> <command>`, `operation_id`, Polish and English descriptions (`summary` up to 120 characters), units, bounds, `one_of`, `writes` and at least one example in `examples`. A new group: append its module to `GROUP_MODULES` in `hydrolog/catalog/groups/__init__.py` (this is the order in the CLI help and in this guide; `commands` stays last) and its title to `_GROUP_TITLES` in `hydrolog/agent_guide.py`.
3. The CLI, the MCP server and the guides follow from the catalog without further changes. The catalog tests run every example through `run_command` and the CLI (`--json`) and compare the envelopes.
4. Regenerate the guides in the same change: `hydrolog commands guide --format agents --lang pl --path AGENTS.md` and `hydrolog commands guide --format llms --lang pl --path llms.txt`. The test `tests/unit/test_agent_guide.py` compares the bytes of both files with the generator; the same applies to a change of the templates in `hydrolog/_data/agents/`, of the error registry and of the flows in `hydrolog/agent_guide.py` (every step of a flow is validated, so a renamed option stops the generator).
