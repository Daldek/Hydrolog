# Hydrolog: watershed hydrology calculations for engineers, researchers and AI agents

Hydrolog is a watershed hydrology calculator: SCS-CN curve numbers and effective rainfall (TR-55), design hyetographs, time of concentration, unit hydrographs and design runoff hydrographs, flood routing of a discharge hydrograph, morphometry, flow statistics, rating curves and hydrologic soil groups. Python library, CLI and MCP server; it runs offline on numbers or local CSV, JSON and GeoTIFF files.

## When to use

Hydrolog computes the standard quantities of watershed hydrology:

- design direct-runoff hydrograph (peak discharge, time to peak, volume): a block, triangular, Beta or Euler type II design hyetograph (Polish hietogram), SCS-CN effective rainfall and an SCS, Nash, Clark or Snyder unit hydrograph;
- lumped flood routing of a discharge hydrograph at a regular time step: lag (`route lag`); the outflow is returned or written to a CSV file that the next `route` command reads;
- time of concentration (Kirpich, NRCS, Giandotti, FAA, Kerby, Kerby-Kirpich), TR-55 curve numbers (CN) and the area-weighted CN of a watershed;
- hydrologic soil groups (HSG) from clay, sand and silt rasters such as SoilGrids;
- watershed shape and relief indicators, river network order (Strahler, Shreve), areal precipitation (Thiessen, IDW, isohyets);
- flow statistics of daily series: characteristic flows (Polish WWQ to NNQ), flood and low-flow frequency, Mann-Kendall trend, rating curves, water level zones;
- a Markdown calculation report of a design hydrograph.

The same commands run from Python, from a shell or a CI job, and from an AI agent over MCP; results are JSON documents.

## When not to use

- Downloading or preparing spatial data (digital elevation model (DEM, Polish NMT), land cover, the topographic database BDOT10k, soil rasters): use [Kartograf](https://github.com/Daldek/Kartograf). Hydrolog only reads the files it is given.
- Measurement series and stations of IMGW-PIB (Polish Institute of Meteorology and Water Management) and CHMU (Czech Hydrometeorological Institute): use [IMGWTools](https://github.com/Daldek/IMGWTools); `imgw series export` writes the CSV that the `stats` commands read.
- Watershed delineation from a DEM: use [Hydrograf](https://github.com/Daldek/Hydrograf) or a GIS; Hydrolog takes the resulting area, lengths and elevations.
- Hydraulics (water levels, inundation mapping, backwater) and channel routing by the Saint-Venant equations: use [Hydraulik](https://github.com/Daldek/Hydraulik) (2D flood screening, research stage) or an external tool such as HEC-RAS. Hydrolog routes discharge only, with lumped hydrologic methods.
- Reservoirs, water quality, groundwater, snowmelt, erosion, Green-Ampt infiltration: not covered ([docs/SCOPE.md](https://github.com/Daldek/Hydrolog/blob/main/docs/SCOPE.md)); use a specialised external model.

## Install

Python 3.12 or newer. Hydrolog is not on PyPI yet, so the lines below install from Git with [uv](https://docs.astral.sh/uv/); with pip: `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`.

```sh
uv tool install "git+https://github.com/Daldek/Hydrolog.git"                           # CLI: hydrolog
uv add "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"                         # Python library
uvx --from "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git" hydrolog-mcp  # MCP server
```

Optional dependencies are extras; add them in brackets, for example `"hydrolog[raster,mcp] @ git+https://github.com/Daldek/Hydrolog.git"`. Without extras, the library, the CLI and every command except the two raster commands run on NumPy, SciPy and platformdirs.

| Extra | Brings | Needed for |
|---|---|---|
| `raster` | rasterio, pyproj | `soil hsg` and `soil hsg-stats` (GeoTIFF rasters) |
| `mcp` | mcp >= 2.3, < 3 | the MCP server |
| `viz` | matplotlib, seaborn | plots in `hydrolog.visualization` (Python only, outside the command catalog) |
| `all` | all of the above | everything |

## Quick start

Option names carry the unit (`length_km`, `slope_m_per_m`, `tc_min`); a CLI flag is the option name with `-` for `_`. `hydrolog --help` and `hydrolog <group> <command> --help` list the options. The examples use inline values only.

**CLI.** `--json` prints one `hydrolog-result/1` document on stdout and nothing else; without it the CLI prints a summary, in Polish by default (`--lang en` for English).

```bash
hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json
```

```json output
{
  "schema": "hydrolog-result/1",
  "tool": "hydrolog",
  "version": "...",
  "command": "tc kirpich",
  "check": false,
  "status": "ok",
  "result": {
    "schema": "hydrolog-tc-kirpich/1",
    "method": "kirpich",
    "tc_min": 85.97330594494066,
    "tc_h": 1.4328884324156776,
    "parameters": {"length_km": 8.2, "slope_m_per_m": 0.023}
  },
  "notices": [],
  "inputs": {"length_km": 8.2, "slope_m_per_m": 0.023}
}
```

`result` is the document of the command (its own `schema`; units are in the field names), `notices` holds non-fatal warnings and `inputs` the options after normalization. A second call computes the design hydrograph of a 45.3 km2 watershed (CN 72, time of concentration 86 min, 38.5 mm of Beta-distributed rain in 60 min):

```bash
hydrolog hydrograph generate --area-km2 45.3 --cn 72 --tc-min 86 --hietogram-type beta --total-mm 38.5 --duration-min 60 --json
```

```json output
{
  "command": "hydrograph generate",
  "result": {
    "schema": "hydrolog-hydrograph-generate/1",
    "peak_discharge_m3s": 30.326278160165238,
    "time_to_peak_min": 80.0,
    "total_volume_m3": 135467.47576859492,
    "times_min": [0.0, 5.0, 10.0, "..."],
    "discharge_m3s": [0.0, 0.0, 0.0, "..."]
  }
}
```

**Python.** `run_command` takes the command name (or its `operation_id`) and the options as keyword arguments and returns the same envelope; an error raises a `hydrolog.HydrologError` subclass.

```python
import hydrolog

envelope = hydrolog.run_command("tc kirpich", length_km=8.2, slope_m_per_m=0.023)
print(envelope.to_json())
```

```json output
{"command": "tc kirpich", "status": "ok", "result": {"tc_min": 85.97330594494066}}
```

`list_commands`, `command_schema`, `validate_command` and `check_command` complete the catalog API. The typed function of each command is in `hydrolog.operations`; the calculation classes (`SCSCN`, `HydrographGenerator`, `NashIUH`, `ConcentrationTime` and others) are described in [docs/USAGE.md](https://github.com/Daldek/Hydrolog/blob/main/docs/USAGE.md).

**MCP.** A client calls the tool named like the `operation_id` with the options as arguments and receives the same envelope as `structuredContent`. This call runs the server in memory with the MCP SDK (extra `mcp`); the MCP server section below configures real clients.

```python
import json

import anyio
from mcp import Client

from hydrolog.mcp import create_server


async def call_tool() -> None:
    async with Client(create_server()) as client:
        arguments = {"length_km": 8.2, "slope_m_per_m": 0.023}
        result = await client.call_tool("hydrolog_tc_kirpich", arguments)
        print(json.dumps(result.structured_content))


anyio.run(call_tool)
```

```json output
{"command": "tc kirpich", "status": "ok", "result": {"tc_min": 85.97330594494066}}
```

## Capabilities

39 commands in 15 groups, all computed offline: no command opens a network connection or downloads data. The MCP tool is `hydrolog_` plus the command name with `_`; every command is also available as `hydrolog.run_command("<command>", **options)`.

| Group | Task | CLI command | MCP tool | Python (`hydrolog.operations`) |
|---|---|---|---|---|
| Time of concentration | Overland flow time (FAA) | `tc faa` | `hydrolog_tc_faa` | `tc_faa` |
| | Time of concentration (Giandotti) | `tc giandotti` | `hydrolog_tc_giandotti` | `tc_giandotti` |
| | Overland flow time (Kerby) | `tc kerby` | `hydrolog_tc_kerby` | `tc_kerby` |
| | Overland plus channel time (Kerby-Kirpich) | `tc kerby-kirpich` | `hydrolog_tc_kerby_kirpich` | `tc_kerby_kirpich` |
| | Time of concentration (Kirpich) | `tc kirpich` | `hydrolog_tc_kirpich` | `tc_kirpich` |
| | Time of concentration (NRCS lag, TR-55) | `tc nrcs` | `hydrolog_tc_nrcs` | `tc_nrcs` |
| | Time of concentration of a watershed by any method | `tc watershed` | `hydrolog_tc_watershed` | `tc_watershed` |
| Curve numbers | The whole TR-55 curve number table | `cn list` | `hydrolog_cn_list` | `cn_list` |
| | Curve number of a soil group and land cover | `cn lookup` | `hydrolog_cn_lookup` | `cn_lookup` |
| | Curve number range of a land cover | `cn range` | `hydrolog_cn_range` | `cn_range` |
| | Area-weighted curve number of a watershed | `cn weighted` | `hydrolog_cn_weighted` | `cn_weighted` |
| Effective rainfall | Effective precipitation by SCS-CN | `scs effective` | `hydrolog_scs_effective` | `scs_effective` |
| Precipitation | Areal precipitation (arithmetic, Thiessen, IDW, isohyets) | `precip areal` | `hydrolog_precip_areal` | `precip_areal` |
| | Design hyetograph (block, triangular, Beta, Euler II) | `precip hietogram` | `hydrolog_precip_hietogram` | `precip_hietogram` |
| Unit hydrographs | Clark unit hydrograph | `uh clark` | `hydrolog_uh_clark` | `uh_clark` |
| | Nash cascade unit hydrograph (n and K, Lutz, urban regression) | `uh nash` | `hydrolog_uh_nash` | `uh_nash` |
| | SCS (NRCS) unit hydrograph | `uh scs` | `hydrolog_uh_scs` | `uh_scs` |
| | Snyder synthetic unit hydrograph | `uh snyder` | `hydrolog_uh_snyder` | `uh_snyder` |
| Runoff hydrograph | Design direct-runoff hydrograph | `hydrograph generate` | `hydrolog_hydrograph_generate` | `hydrograph_generate` |
| Flood routing | Lag routing of a hydrograph (writes a file if an output is given) | `route lag` | `hydrolog_route_lag` | `route_lag` |
| Morphometry | Geometric, shape and relief indicators | `morphometry watershed` | `hydrolog_morphometry_watershed` | `morphometry_watershed` |
| River network | River network order statistics (Strahler, Shreve) | `network stats` | `hydrolog_network_stats` | `network_stats` |
| Flow statistics | Characteristic values WWQ to NNQ of a daily series | `stats characteristic` | `hydrolog_stats_characteristic` | `stats_characteristic` |
| | Day-of-year statistics | `stats daily` | `hydrolog_stats_daily` | `stats_daily` |
| | Flood quantiles from annual maxima | `stats flood-frequency` | `hydrolog_stats_flood_frequency` | `stats_flood_frequency` |
| | Low-flow quantiles from annual minima | `stats low-flow` | `hydrolog_stats_low_flow` | `stats_low_flow` |
| | Low-flow (drought) sequences below a threshold | `stats low-flow-sequences` | `hydrolog_stats_low_flow_sequences` | `stats_low_flow_sequences` |
| | Monotonic trend test (Mann-Kendall) | `stats mann-kendall` | `hydrolog_stats_mann_kendall` | `stats_mann_kendall` |
| | Monthly statistics with confidence interval | `stats monthly` | `hydrolog_stats_monthly` | `stats_monthly` |
| Hydrometry | Rating curve Q = a(H - H0)^b | `hydrometrics rating-curve` | `hydrolog_hydrometrics_rating_curve` | `hydrometrics_rating_curve` |
| | Water level zones NTW, STW, WTW (Rybczyński) | `hydrometrics water-level-zones` | `hydrolog_hydrometrics_water_level_zones` | `hydrometrics_water_level_zones` |
| Soil | HSG GeoTIFF from clay, sand and silt rasters (writes a file) | `soil hsg` | `hydrolog_soil_hsg` | `soil_hsg` |
| | Area and share of HSG A-D in an HSG raster | `soil hsg-stats` | `hydrolog_soil_hsg_stats` | `soil_hsg_stats` |
| | USDA texture class and HSG of one sample | `soil texture` | `hydrolog_soil_texture` | `soil_texture` |
| Report | Markdown calculation report (writes a file) | `report generate` | `hydrolog_report_generate` | `report_generate` |
| Settings | Effective settings and their sources | `config show` | `hydrolog_config_show` | `config_show` |
| Catalog and guides | Render AGENTS.md, llms.txt or a block (writes a file) | `commands guide` | `hydrolog_commands_guide` | `commands_guide` |
| | List the commands | `commands list` | `hydrolog_commands_list` | `commands_list` |
| | Options, units, rules and examples of a command | `commands schema` | `hydrolog_commands_schema` | `commands_schema` |

## For AI agents

- [llms.txt](https://github.com/Daldek/Hydrolog/blob/main/llms.txt) and [AGENTS.md](https://github.com/Daldek/Hydrolog/blob/main/AGENTS.md) state the scope, the workflow, the error codes and typical flows (design hydrograph of a watershed file, flood frequency from an IMGWTools export, HSG from SoilGrids rasters); both are generated from the command catalog. `hydrolog commands guide --format agents` (or `llms`) prints them; `--format agents-md-block --inject AGENTS.md` puts a compact block into another repository's AGENTS.md.
- The catalog is served by the tool: `hydrolog commands list` (names, operation ids, summaries) and `hydrolog commands schema --command "tc kirpich"` (options with units, bounds and allowed values, result schema, rules, examples, errors). In MCP these are the tools `hydrolog_commands_list` and `hydrolog_commands_schema`; `--schema` after any command prints its description instead of running it.
- Work in four steps: discover, check, run, read. A result is a `hydrolog-result/1` envelope (`status` is `ok`; a failing command ends with an error instead), an error a `hydrolog-error/1` document.
- Calculations are read-only. Four commands write one file (`report generate`, `soil hsg`, `commands guide` and `route lag`, whose `--output` is optional) and take `--output`, `--check` and `--force`: `--check` writes nothing and returns the plan, `result.targets[]` with `option`, `path` and `action` (`write`, `replace` or `conflict`); an existing file is replaced only with `--force`. A `route` command without `--output` has no file to plan: it returns the routed hydrograph, also with `--check`.

```bash
hydrolog commands schema --command "tc kirpich" --json
hydrolog commands guide --format llms --output guide.txt --check --json
```

```json output
{
  "command": "commands guide", "check": true,
  "result": {"schema": "hydrolog-plan/1", "targets": [{"option": "output", "path": "...", "action": "write"}]}
}
```

## MCP server

`hydrolog mcp` (console script `hydrolog-mcp`) serves the catalog over stdio: one tool per command, named by its `operation_id`, with annotations, an input schema and the result envelope as output schema. It targets MCP specification 2026-07-28 with the SDK pinned as `mcp>=2.3,<3`, and offers tools only (no resources or prompts). The configurations start it with the uvx line of the Install section; replace `/path/to/data` with the directory that holds your input files.

Claude Code:

```sh
claude mcp add hydrolog -- uvx --from "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git" hydrolog-mcp --allow-dir /path/to/data
```

Cursor, `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "hydrolog": {
      "command": "uvx",
      "args": [
        "--from", "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git",
        "hydrolog-mcp", "--allow-dir", "/path/to/data"
      ]
    }
  }
}
```

Codex:

```sh
codex mcp add hydrolog -- uvx --from "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git" hydrolog-mcp --allow-dir /path/to/data
```

VS Code, `.vscode/mcp.json` (key `servers`):

```json
{
  "servers": {
    "hydrolog": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git",
        "hydrolog-mcp", "--allow-dir", "/path/to/data"
      ]
    }
  }
}
```

- `--allow-dir DIR` (repeatable): the only directories in which tools read files; without it every path option is refused (`forbidden`), while commands that take values still work.
- `--allow-writes`: lets `report generate`, `soil hsg`, `commands guide` and `route lag` (with `output`) write inside the allowed directories; without it they run as `check` and return the plan, while `route lag` without `output` still returns the routed hydrograph.
- `--tools FAMILIES`: comma-separated tool families, a command group (`tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `route`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `config`, `commands`) or `core`, the main tasks (`tc watershed`, `cn lookup`, `cn weighted`, `scs effective`, `hydrograph generate`, `morphometry watershed`, `stats flood-frequency`, `commands list`, `commands schema`).
- The server speaks English only (`hydrolog mcp --lang en` is rejected). Instructions are at most 4,096 characters, each tool description at most 600; an execution error is an `isError` result that holds the `hydrolog-error/1` document.

## Related tools

- [Kartograf](https://github.com/Daldek/Kartograf) downloads Polish and Czech geodata (elevation, land cover, soils); the `files[].path` values in the `--json` result of `kartograf soil download --output-dir DIR` are the clay, sand and silt rasters of `soil hsg`.
- [IMGWTools](https://github.com/Daldek/IMGWTools) provides IMGW-PIB and CHMU series: `imgw series export --output FILE` writes the CSV that `--input-file` of the `stats` and `hydrometrics` commands reads, and its PMAXTP design precipitation can supply `--total-mm`.
- [Hydrograf](https://github.com/Daldek/Hydrograf) is a web app for watershed delineation and design hydrographs built on Hydrolog; watersheds travel as `WatershedParameters` JSON ([docs/INTEGRATION.md](https://github.com/Daldek/Hydrolog/blob/main/docs/INTEGRATION.md)).
- [Retman](https://github.com/Daldek/Retman) is a Polish natural-language command layer over the ecosystem tools; it is designed to drive Hydrolog through the command layer (`hydrolog.operations`).
- [Hydraulik](https://github.com/Daldek/Hydraulik) screens 2D floods (research stage) and uses the Beta and Euler type II hyetograph classes of Hydrolog; [Nogat](https://github.com/Daldek/Nogat) holds the shared standards and the registry of these tools.
- External alternatives: HEC-HMS when a study needs several sub-basins, channel routing, reservoirs or calibration; HEC-RAS for hydraulics and inundation; EPA SWMM for urban drainage networks; WhiteboxTools or pysheds for watershed delineation and flow routing on a DEM.

## Errors and exit codes

An error exits with a registry code and, in both CLI modes, ends stderr with a `hydrolog-error/1` JSON line (`code`, `title`, `message`, `hint`, `details`, `exit_code`); Python raises `hydrolog.HydrologError` subclasses with the same `code`, `details` and `hint`, and MCP returns the document in an `isError` result. The shared registry: [ERROR_REGISTRY.md](https://github.com/Daldek/Nogat/blob/main/standards/ERROR_REGISTRY.md).

| Code | Exit | Typical cause | Hint |
|---|---|---|---|
| `validation_error` | 2 | missing, unknown or out-of-range option | fix the option in `details.option`, see `commands schema` |
| `not_found` | 3 | unknown command or missing input file | check the name (`details.suggestions`) or the path |
| `conflict` | 4 | the output file exists | give another `--output` or add `--force` |
| `missing_dependency` | 6 | an optional extra is not installed | add the extra the error names (`raster`, `mcp` or `viz`), see Install |
| `data_error` | 7 | malformed CSV, JSON or GeoTIFF | see `details.path` and `details.reason` |

Also `io_error` (9, output not writable), `forbidden` (12, path outside `--allow-dir`), `calculation_error` (13, valid input without a result), `internal_error` (1), `cancelled` (130) and `terminated` (143).

```python
import json

import hydrolog

try:
    hydrolog.run_command("tc kirpich", length_km=-1, slope_m_per_m=0.023)
except hydrolog.HydrologError as error:
    print(json.dumps({"code": error.code, "exit_code": error.exit_code, "details": error.details}))
```

```json output
{"code": "validation_error", "exit_code": 2, "details": {"option": "length_km", "reason": "exclusive_minimum"}}
```

## Data and licensing

Hydrolog downloads nothing, opens no network connection and needs no account or key. Input is numbers or local files: CSV series (an IMGWTools export loads unchanged), JSON (watershed, stations, network segments) and GeoTIFF rasters (extra `raster`). It ships no dataset except the TR-55 curve number table of USDA NRCS. The data you pass keep the licence of their source (IMGW-PIB terms of reuse, SoilGrids CC BY 4.0); Hydrolog does not copy the attribution columns of an IMGWTools export into results, so name the source when you publish a result.

A command writes only to the file named by `--output` (exactly one plain file, written atomically; `commands guide --inject PATH` edits the AGENTS.md you name) and replaces an existing file only with `--force`. There is no store, cache or credential.

Settings (`lang`, `log_level`) come from, in order: the command-line option, `HYDROLOG_<KEY>`, `NOGAT_<KEY>`, `nogat.toml` (section `[hydrolog]`, then `[nogat]`) in the user config directory or at `NOGAT_CONFIG`, then the default; an invalid environment or file value is ignored. [.env.example](https://github.com/Daldek/Hydrolog/blob/main/.env.example) lists every variable: `HYDROLOG_LANG`, `NOGAT_LANG` (`pl` or `en`, default `pl`), `HYDROLOG_LOG_LEVEL`, `NOGAT_LOG_LEVEL` (`debug`, `info`, `warning` or `error`, default `warning`) and `NOGAT_CONFIG`. `hydrolog config show` prints the effective values and where each comes from:

```bash
hydrolog config show --json
```

```json output
{
  "command": "config show",
  "result": {
    "schema": "hydrolog-config/1",
    "settings": [
      {"key": "lang", "value": "pl", "source": "default"},
      {"key": "log_level", "value": "warning", "source": "default"}
    ],
    "credentials": [],
    "store": null
  }
}
```

## Documentation

- [Usage guide](https://github.com/Daldek/Hydrolog/blob/main/docs/USAGE.md): tasks per interface, the library classes
- [Changelog](https://github.com/Daldek/Hydrolog/blob/main/docs/CHANGELOG.md): changes per release, breaking changes with migration notes
- [Decisions](https://github.com/Daldek/Hydrolog/blob/main/docs/DECISIONS.md): architecture decision records
- [Scope](https://github.com/Daldek/Hydrolog/blob/main/docs/SCOPE.md): what is in and out of scope
- [Computation paths](https://github.com/Daldek/Hydrolog/blob/main/docs/COMPUTATION_PATHS.md): methods, formulas and which parameters combine
- [Integration](https://github.com/Daldek/Hydrolog/blob/main/docs/INTEGRATION.md): files exchanged with Hydrograf, Retman, Kartograf and IMGWTools

## Development

[CLAUDE.md](https://github.com/Daldek/Hydrolog/blob/main/CLAUDE.md) holds the instructions for working on the repository (rules, code map, documentation map); set up with `uv sync --locked --all-extras` and run `scripts/gate.sh` before every commit: ruff format and check, mypy, the tests with coverage and the commit checks. See also [CONTRIBUTING.md](https://github.com/Daldek/Hydrolog/blob/main/CONTRIBUTING.md) and [SECURITY.md](https://github.com/Daldek/Hydrolog/blob/main/SECURITY.md).

## Status, licence, author

Alpha: version 1.0.0 is not released yet (the repository carries `1.0.0.dev0`), and semantic versioning applies from 1.0.0. Licence: MIT. Author: Piotr de Bever ([Daldek](https://github.com/Daldek)). Hydrolog is part of the [Nogat](https://github.com/Daldek/Nogat) ecosystem and follows its standard 2.1.
