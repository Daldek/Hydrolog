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

- Python: `hydrolog.run_command("tc kirpich", length_km=8.2, slope_m_per_m=0.023)` (keyword arguments are the options). Also `check_command`, `validate_command`, `list_commands`, `command_schema` of `hydrolog`. `run_command` returns the envelope (`to_dict()`, `to_json()`); errors raise `HydrologError` subclasses (`code`, `hint`, `details`).
- CLI: `hydrolog <group> <verb> --option value --json`, e.g. `hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json`. A flag is `--` and the option name with `-` for `_`; lists are comma-separated (`--return-periods 10,50,100`), objects JSON text, booleans `--flag` or `--no-flag`. `--json` prints the envelope on one line of stdout; `--lang pl|en` only changes human output.
- MCP: `hydrolog mcp --allow-dir DIR [--allow-writes] [--tools FAMILIES]` (console script `hydrolog-mcp`). `--allow-dir` can be repeated; `--tools` selects families (a command group or `core`). A tool is named like the `operation_id`, its arguments are the options; writing needs `--allow-writes`; the path rule is below.
- Settings: `hydrolog config show` prints the effective `lang` and `log_level` and their sources.

## Workflow rules

Discover (`hydrolog commands list`, then `hydrolog commands schema --command "<name>"`), check (`--check` first for a command that writes a file: `report generate`, `soil hsg`, `commands guide`, `route` with `output`), run, read `result`, `notices` and `result.files`.

Rules:

1. **Discover, do not guess:** `commands list` lists the commands, `commands schema` (option `command`) gives options, units, bounds and examples; in MCP use `tools/list`.
2. **Files, not arrays:** give series, stations, segments and watersheds as a CSV/JSON file (`input_file`, `watershed_file`...), not long lists.
3. **Units:** option descriptions give them (km, km2, m/m, mm, min, m3/s; slope in m/m, not %); do not convert silently or guess values the user did not give.
4. **Check, then write:** a command that writes takes `output`, `check` and `force`; run `check` first, an existing file is replaced only with `force`, written files are listed in `result.files`.
5. **Errors by code:** decide by `code`, `details.option` and `details.reason` (or the exit code), fix the argument as `hint` says and call again; never present an error as a result.
6. **Absolute paths in allowed directories:** MCP refuses (`forbidden`) files outside `--allow-dir`, and every path option without it.
7. **Read `notices`:** non-fatal warnings (a short series, a value outside a formula's range); pass them on with the result.
8. **No data downloads:** Hydrolog uses no network; series come from IMGWTools, soil rasters from Kartograf.

## Result envelope

A command returns `hydrolog-result/1`: `schema`, `tool` (`hydrolog`), `version`, `command`, `check` (true for a `--check` plan: `result.targets[]` with `option`, `path`, `action`), `status` (always `ok`: a failing command raises an error and leaves nothing half done), `result`, `notices`, `inputs`, `page` (paged lists).

- `result`: the values of the command with its own `schema`; units follow from field names (`tc_min`); `NaN` and infinities are `null`.
- `result.files`: files the command wrote, each `{path, size_bytes, sha256, status}` with `status` `written` or `replaced`.
- `notices`: non-fatal `{level, code, message}` entries.
- `inputs`: the options after normalization (defaults filled in, paths absolute).

## Error codes

Errors are `hydrolog-error/1` documents (`schema`, `code`, `title`, `message`, `hint`, `details`, `exit_code`, `command`; with `--json` the last line of stderr). The code is the same in Python, the CLI exit code and MCP. Registry: https://github.com/Daldek/Nogat/blob/main/standards/ERROR_REGISTRY.md

| Code | Exit | What to do |
|---|---|---|
| `internal_error` | 1 | bug in Hydrolog: report command, options, version |
| `validation_error` | 2 | wrong or missing option: fix `details.option` (`hint`) |
| `not_found` | 3 | unknown command (`details.suggestions`) or input file |
| `conflict` | 4 | output file exists: another `output` or `force` |
| `missing_dependency` | 6 | optional extra missing: install it (`hint`) |
| `data_error` | 7 | malformed input file: see `details.path`, `details.reason` |
| `io_error` | 9 | output cannot be written: check `details.path` |
| `forbidden` | 12 | path outside allowed directories (`details.allowed_dirs`) |
| `calculation_error` | 13 | valid input, no result: change the data |
| `cancelled` | 130 | interrupted (Ctrl+C): nothing half written; run again |
| `terminated` | 143 | ended by SIGTERM: nothing half written; run again |

## Command index

One line per command: name, `operation_id`, summary. Options, units, bounds and examples: `hydrolog commands schema --command "<name>"`.

### [tc: Time of concentration][paths]
- `tc faa` (`hydrolog_tc_faa`): Compute overland flow time with the FAA method.
- `tc giandotti` (`hydrolog_tc_giandotti`): Compute time of concentration with the Giandotti formula.
- `tc kerby` (`hydrolog_tc_kerby`): Compute overland flow time with the Kerby formula.
- `tc kerby-kirpich` (`hydrolog_tc_kerby_kirpich`): Compute time of concentration with the Kerby-Kirpich method.
- `tc kirpich` (`hydrolog_tc_kirpich`): Compute time of concentration with the Kirpich formula.
- `tc nrcs` (`hydrolog_tc_nrcs`): Compute time of concentration with the NRCS (TR-55 lag) method.
- `tc watershed` (`hydrolog_tc_watershed`): Compute time of concentration by a chosen method from a watershed.
### [cn: Curve Number (TR-55)][paths]
- `cn list` (`hydrolog_cn_list`): Return the whole TR-55 CN table (covers, conditions, groups A-D).
- `cn lookup` (`hydrolog_cn_lookup`): Look up the TR-55 Curve Number for a soil group and a land cover.
- `cn range` (`hydrolog_cn_range`): Return the CN range of a land cover over hydrologic conditions.
- `cn weighted` (`hydrolog_cn_weighted`): Compute the area-weighted CN of a watershed made of several parts.
### [scs: SCS-CN effective precipitation][paths]
- `scs effective` (`hydrolog_scs_effective`): Compute effective precipitation by the SCS-CN method from a total or a hyetograph.
### [precip: Hyetographs and areal precipitation][paths]
- `precip areal` (`hydrolog_precip_areal`): Compute areal precipitation from gauges: arithmetic mean, Thiessen, IDW or isohyets.
- `precip hietogram` (`hydrolog_precip_hietogram`): Compute a design hyetograph: block, triangular, Beta or Euler type II.
### [uh: Unit hydrographs][paths]
- `uh clark` (`hydrolog_uh_clark`): Compute the Clark unit hydrograph from tc and the storage constant R or the ratio R/tc.
- `uh nash` (`hydrolog_uh_nash`): Compute the Nash cascade unit hydrograph from n and K, the Lutz method or urban regression.
- `uh scs` (`hydrolog_uh_scs`): Compute the SCS (NRCS) unit hydrograph from the area and the time of concentration.
- `uh snyder` (`hydrolog_uh_snyder`): Compute the Snyder synthetic unit hydrograph from L, Lc and the coefficients Ct and Cp.
### [hydrograph: Runoff hydrograph][paths]
- `hydrograph generate` (`hydrolog_hydrograph_generate`): Compute the design direct-runoff hydrograph: rainfall, SCS-CN, unit hydrograph, convolution.
### [route: Flood routing][paths]
- `route cascade`, `route lag`, `route muskingum`, `route muskingum-cunge` (tools `hydrolog_route_<verb>`, `-` as `_`): route a hydrograph (`time_min`, `discharge_m3s`) through a reach, a reservoir or a river network; summaries: `commands list`.
### [morphometry: Watershed morphometry][paths]
- `morphometry watershed` (`hydrolog_morphometry_watershed`): Compute geometric, shape and relief indicators of a watershed.
### [network: River network][paths]
- `network stats` (`hydrolog_network_stats`): Compute the order statistics of a river network (Strahler or Shreve).
### [stats: Flow statistics][paths]
- `stats characteristic` (`hydrolog_stats_characteristic`): Compute second-degree characteristic values (WWQ…NNQ) of a daily series
- `stats daily` (`hydrolog_stats_daily`): Compute day-of-year statistics over all years of a daily series
- `stats flood-frequency` (`hydrolog_stats_flood_frequency`): Compute flood quantiles for return periods from annual maxima
- `stats low-flow` (`hydrolog_stats_low_flow`): Compute low-flow quantiles for return periods from annual minima
- `stats low-flow-sequences` (`hydrolog_stats_low_flow_sequences`): Detect low-flow (drought) sequences below a threshold
- `stats mann-kendall` (`hydrolog_stats_mann_kendall`): Test a series for a monotonic trend with the Mann–Kendall test
- `stats monthly` (`hydrolog_stats_monthly`): Compute monthly statistics with a t-Student confidence interval of the mean
### [hydrometrics: Hydrometry][paths]
- `hydrometrics rating-curve` (`hydrolog_hydrometrics_rating_curve`): Fit a rating curve Q = a·(H − H₀)^b to stage–discharge pairs
- `hydrometrics water-level-zones` (`hydrolog_hydrometrics_water_level_zones`): Delimit Rybczyński water level zones (NTW, STW, WTW) from level series
### [soil: Texture and HSG][paths]
- `soil hsg` (`hydrolog_soil_hsg`): Write an HSG GeoTIFF classified from clay, sand and silt rasters.
- `soil hsg-stats` (`hydrolog_soil_hsg_stats`): Compute areas and shares of the HSG groups A-D from an HSG raster.
- `soil texture` (`hydrolog_soil_texture`): Compute the USDA soil texture class and Hydrologic Soil Group A-D of one soil sample.
### [report: Calculation report][paths]
- `report generate` (`hydrolog_report_generate`): Write a Markdown calculation report of a design hydrograph.
### [config: Effective settings][paths]
- `config show` (`hydrolog_config_show`): Show the effective settings of Hydrolog and the source of each.
### [commands: The command catalog and this guide][paths]
- `commands guide` (`hydrolog_commands_guide`): Render the agent guide (AGENTS.md, llms.txt, block) from the catalog.
- `commands list` (`hydrolog_commands_list`): List the catalog commands: name, operation id and summary.
- `commands schema` (`hydrolog_commands_schema`): Return options, result and rules of one command or a catalog page.

[paths]: https://github.com/Daldek/Hydrolog/blob/main/docs/COMPUTATION_PATHS.md

## Typical flows

CLI lines; in MCP call the tool `operation_id` with the same options as arguments. Paths under `/data/` are examples: give your own (absolute, inside an allowed directory). `imgw` and `kartograf` lines are other tools.

### 1. Design hydrograph of a watershed described by a JSON file
The watershed file has the `WatershedParameters` format: `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` and `elevation_max_m` are required; `cn`, `channel_length_km`, `channel_slope_m_per_m` are optional.
1. `hydrolog morphometry watershed --watershed-file /data/hydrolog/watershed.json` - geometric, shape and relief indicators; a bad file is a `data_error` with `details.path`.
2. `hydrolog tc watershed --watershed-file /data/hydrolog/watershed.json --method kirpich` - time of concentration (`result.tc_min`); a field the method needs but the file lacks is a `validation_error` that lists it.
3. `hydrolog hydrograph generate --watershed-file /data/hydrolog/watershed.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60` - direct runoff (Beta hyetograph, SCS-CN with `cn` from the file, SCS unit hydrograph): `peak_discharge_m3s`, `time_to_peak_min`, `total_volume_m3`.
4. `hydrolog report generate --output /data/hydrolog/report.md --watershed-file /data/hydrolog/watershed.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60 --check` - plan of the Markdown report (action `write`, `replace` or `conflict`, nothing written); run it without `check` to write it (`result.files`).
### 2. Flood frequency from an IMGWTools CSV export
IMGWTools exports the daily discharge series to a CSV file (`Q [m3/s]`, `date`) that Hydrolog loads without preprocessing.
1. `imgw series export --dataset pl.imgw.hydro_daily --station CODE --variables Q --format csv --output /data/hydrolog/q_daily.csv` - IMGWTools: export one station (`CODE` from `imgw stations find`); reliable quantiles need at least 30 years.
2. `hydrolog stats flood-frequency --input-file /data/hydrolog/q_daily.csv --value-column Q --date-column date --distribution all --return-periods 10,50,100` - annual maxima of hydrological years (Nov-Oct); `Q` finds the column `Q [m3/s]`; result: `best_distribution`, `distributions[].quantiles`; under 30 years adds a notice.
### 3. Hydrologic soil groups (HSG) from SoilGrids rasters and the weighted CN
Kartograf downloads clay, sand and silt (g/kg); Hydrolog computes the HSG (extra `raster`).
1. `kartograf soil download --property clay --depth 0-5cm --stat mean --bbox 626000,480000,628000,482000 --bbox-crs EPSG:2180 --output-dir /data/kartograf --json` - Kartograf: repeat with `--property sand` and `--property silt`; the `files[].path` values of its `--json` result are the raster inputs of the next step.
2. `hydrolog soil hsg --clay-path /data/kartograf/soil/clay.tif --sand-path /data/kartograf/soil/sand.tif --silt-path /data/kartograf/soil/silt.tif --output /data/hydrolog/hsg.tif` - HSG raster (GeoTIFF `uint8`: 0 no data, 1-4 are A-D) from three rasters with the same coordinate system, grid and size.
3. `hydrolog soil hsg-stats --hsg-path /data/hydrolog/hsg.tif` - area (`area_ha`) and share of each group (`groups.A` ... `groups.D`) and the `nodata` cells.
4. `hydrolog cn weighted --parts '[{"cn":30,"area":75.0},{"cn":58,"area":75.0},{"cn":71,"area":75.0},{"cn":78,"area":68.75}]'` - area-weighted CN (`result.cn`): a part is a CN (`cn list`, `cn lookup`) and the `area_ha` of a group from `soil hsg-stats`; intersecting rasters with land cover happens outside Hydrolog.

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
