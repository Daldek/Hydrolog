# Hydrolog - guide for agents

> Generated from the command catalog: `hydrolog commands guide --format agents`. Do not edit it by hand.

## Purpose and scope

Hydrolog is a Python library, the `hydrolog` CLI and an MCP server for watershed hydrology: SCS-CN and curve numbers (TR-55), design hyetographs, time of concentration, unit and runoff hydrographs, lumped flood routing, morphometry, flow statistics, rating curves, hydrologic soil groups (HSG) from soil rasters and a calculation report. All interfaces come from one command catalog.

Use it to compute these quantities from numbers or from local CSV/JSON/GeoTIFF files. It runs locally: no network, no keys, no downloads. Not for:

- spatial data (DEM, land cover, SoilGrids rasters): use Kartograf (`kartograf soil download`);
- IMGW/CHMU measurement series: use IMGWTools (`imgw series export`);
- hydraulics (water levels, inundation, backwater): use Hydraulik or HEC-RAS; reservoir operation, water quality, groundwater (`docs/SCOPE.md`).

## Install

Python 3.12 or newer: `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`. Extras: `raster` (rasterio, pyproj; `soil hsg`, `soil hsg-stats`), `mcp` (the MCP server), `viz` (plots in Python, outside the catalog), `all`.

## Interfaces

- Python: <!-- hydrolog:python_example --> (keyword arguments are the options). Also `check_command`, `validate_command`, `list_commands`, `command_schema` of `hydrolog`. `run_command` returns the envelope (`to_dict()`, `to_json()`); errors raise `HydrologError` subclasses (`code`, `hint`, `details`).
- CLI: `hydrolog <group> <verb> --option value --json`, e.g. <!-- hydrolog:cli_example -->. A flag is `--` and the option name with `-` for `_`; lists are comma-separated (`--return-periods 10,50,100`), objects JSON text, booleans `--flag` or `--no-flag`. `--json` prints the envelope on one line of stdout; `--lang pl|en` only changes human output.
- MCP: `hydrolog mcp --allow-dir DIR [--allow-writes] [--tools FAMILIES]` (console script `hydrolog-mcp`). `--allow-dir` can be repeated; `--tools` selects families (a command group or `core`). A tool is named like the `operation_id`, its arguments are the options; writing needs `--allow-writes`; the path rule is below.
- Settings: `hydrolog config show` prints the effective `lang` and `log_level` and their sources.

## Workflow rules

Discover (`hydrolog commands list`, then `hydrolog commands schema --command "<name>"`), check (`--check` first for a command that writes a file: `report generate`, `soil hsg`, `commands guide`, `route` with `output`), run, read `result`, `notices` and `result.files`.

Rules:

<!-- hydrolog:rules -->

## Result envelope

A command returns `hydrolog-result/1`: `schema`, `tool` (`hydrolog`), `version`, `command`, `check` (true for a `--check` plan: `result.targets[]` with `option`, `path`, `action`), `status` (always `ok`: a failing command raises an error and leaves nothing half done), `result`, `notices`, `inputs`, `page` (paged lists).

- `result`: the values of the command with its own `schema`; units follow from field names (`tc_min`); `NaN` and infinities are `null`.
- `result.files`: files the command wrote, each `{path, size_bytes, sha256, status}` with `status` `written` or `replaced`.
- `notices`: non-fatal `{level, code, message}` entries.
- `inputs`: the options after normalization (defaults filled in, paths absolute).

## Error codes

Errors are `hydrolog-error/1` documents (`schema`, `code`, `title`, `message`, `hint`, `details`, `exit_code`, `command`; with `--json` the last line of stderr). The code is the same in Python, the CLI exit code and MCP. Registry: https://github.com/Daldek/Nogat/blob/main/standards/ERROR_REGISTRY.md

<!-- hydrolog:errors -->

## Command index

One line per command: name, `operation_id`, summary. Options, units, bounds and examples: `hydrolog commands schema --command "<name>"`.

<!-- hydrolog:index -->

## Typical flows

CLI lines; in MCP call the tool `operation_id` with the same options as arguments. Paths under `/data/` are examples: give your own (absolute, inside an allowed directory). `imgw` and `kartograf` lines are other tools.

<!-- hydrolog:flows -->

## Things not to do

- Do not pick one method silently when methods (time of concentration, unit hydrograph) disagree, and do not combine every formula with every model: `docs/COMPUTATION_PATHS.md`.
- Do not repeat a call unchanged after `validation_error`, `data_error` or `calculation_error`, and do not parse `message` or `hint`: decide by `code`, `details.option`, `details.reason` or the exit code.
- Do not treat the HSG as the CN: the CN also needs the land cover (`cn list`, `cn lookup`, `cn weighted`).

## Working on this repository

Gate: `scripts/gate.sh`. To add a command (details in `src/hydrolog/catalog/__init__.py`):

1. Write the operation in `src/hydrolog/operations/<group>.py` and export it in `src/hydrolog/operations/__init__.py`.
2. Declare `Command` and `Option` in `src/hydrolog/catalog/groups/<group>.py`; a new group goes into `GROUP_MODULES` in `src/hydrolog/catalog/groups/__init__.py` and its title into `_GROUP_TITLES` in `src/hydrolog/agent_guide.py`.
3. Regenerate the guides (the CLI, MCP server and guides follow from the catalog): `hydrolog commands guide --format agents --output AGENTS.md --force` and `hydrolog commands guide --format llms --output llms.txt --force`.

Developing this repository? Read CLAUDE.md.
