# Hydrolog: watershed hydrology calculations for engineers, researchers and AI agents

Hydrolog is a watershed hydrology calculator: SCS-CN curve numbers and effective rainfall (TR-55), design hyetographs, time of concentration, unit hydrographs and design runoff hydrographs, flood routing of a discharge hydrograph, morphometry, flow statistics, rating curves, the meteorological statistics of a weather station and hydrologic soil groups. Python library, CLI, MCP server and a web GUI in Polish; it runs offline on numbers or local CSV, JSON and GeoTIFF files, except `precip pmaxtp`, which fetches the PMAXTP design rainfall depth of IMGW-PIB through Obserwator.


## When to use

Hydrolog computes the standard quantities of watershed hydrology:

- design direct-runoff hydrograph (peak discharge, time to peak, volume): a block, triangular, Beta or Euler type II design hyetograph (Polish hietogram), SCS-CN effective rainfall and an SCS, Nash, Clark or Snyder unit hydrograph;
- lumped flood routing of a discharge hydrograph at a regular time step: lag (`route lag`), Muskingum with sub-reaches (`route muskingum`), Muskingum-Cunge from the slope and the channel section or celerity of the reach (`route muskingum-cunge`), a cascade of linear reservoirs with an exact kernel for any time step (`route cascade`) and a reservoir or a reach with a storage-outflow table, by storage indication (`route level-pool`), and down a river network of subcatchments, reaches, reservoirs and junctions described in a JSON document (`route network`); in Python the network is made of objects, a subcatchment given its hydrograph or making it from a watershed and a rainfall of its own (a design storm or a record, SCS-CN and a unit hydrograph), and `ControlPointNetwork` builds it as an application picks points on the streams, outlet first; the outflow is returned or written to a CSV file that the next `route` command reads, a network writes one file per node;
- time of concentration (Kirpich, NRCS, Giandotti, FAA, Kerby, Kerby-Kirpich), TR-55 curve numbers (CN) and the area-weighted CN of a watershed;
- hydrologic soil groups (HSG) from clay, sand and silt rasters such as SoilGrids;
- watershed shape and relief indicators, river network order (Strahler, Shreve), areal precipitation (Thiessen, IDW, isohyets);
- flow statistics of daily series: characteristic flows (Polish WWQ to NNQ), flood and low-flow frequency, Mann-Kendall trend with Sen's slope, the flow regime, the season of floods and low flows, the annual cycle, baseflow, rating curves, water level zones;
- meteorological statistics of a weather station's daily series: precipitation sums and normals (of the analysed years or of a reference period such as 1991-2020, `--reference-first-year`, `--reference-last-year`), maxima, wet days, intensity, heavy precipitation, dry and wet spells (`--min-duration-days` shortens their list), SPI, air temperature indices and degree days, snow cover, Sielianinov's hydrothermal coefficient;

- a Markdown calculation report of a design hydrograph.

The same commands run from Python, from a shell or a CI job, from an AI agent over MCP and, for a person, in the web GUI; results are JSON documents.

## When not to use

- Downloading or preparing spatial data (digital elevation model (DEM, Polish NMT), land cover, the topographic database BDOT10k, soil rasters): use [Kartograf](https://github.com/Daldek/Kartograf). Hydrolog only reads the files it is given.
- Measurement series and stations of IMGW-PIB (Polish Institute of Meteorology and Water Management) and CHMU (Czech Hydrometeorological Institute): use [Obserwator](https://github.com/Daldek/Obserwator); `obserwator series export` writes the CSV that the `stats` and `meteo` commands read.

- Watershed delineation from a DEM: use [Hydrograf](https://github.com/Daldek/Hydrograf) or a GIS; Hydrolog takes the resulting area, lengths and elevations.
- Hydraulics (water levels, inundation mapping, backwater) and channel routing by the Saint-Venant equations: use [Hydraulik](https://github.com/Daldek/Hydraulik) (2D flood screening, research stage) or an external tool such as HEC-RAS. Hydrolog routes discharge only, with lumped hydrologic methods.
- Reservoirs, water quality, groundwater, snowmelt, erosion, Green-Ampt infiltration: not covered ([docs/SCOPE.md](https://github.com/Daldek/Hydrolog/blob/main/docs/SCOPE.md)); use a specialised external model.

## Install

Python 3.12 or newer. Hydrolog is not on PyPI yet, so the lines below install from Git with [uv](https://docs.astral.sh/uv/); with pip: `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`.

```sh
uv tool install "git+https://github.com/Daldek/Hydrolog.git"                           # CLI: hydrolog
uv add "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"                         # Python library
uvx --from "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git" hydrolog-mcp  # MCP server
uv tool install "hydrolog[gui] @ git+https://github.com/Daldek/Hydrolog.git"           # CLI with the web GUI
```

Optional dependencies are extras; add them in brackets, for example `"hydrolog[raster,mcp] @ git+https://github.com/Daldek/Hydrolog.git"`. Without extras, the library, the CLI and every command except the two raster commands, `precip pmaxtp` and `gui serve` run on NumPy, SciPy and platformdirs.

| Extra | Brings | Needed for |
|---|---|---|
| `raster` | rasterio, pyproj | `soil hsg` and `soil hsg-stats` (GeoTIFF rasters) |
| `mcp` | mcp >= 2.3, < 3 | the MCP server |
| `pmaxtp` | obserwator >= 3.0.0.dev0, < 4 | `precip pmaxtp` (the PMAXTP depth of IMGW-PIB, over the network) |
| `gui` | starlette, uvicorn, obserwator | the web GUI (`hydrolog gui serve`) |
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
  "notices": [
    {
      "level": "warning",
      "code": "outside_typical_range",
      "message": "kirpich: slope_m_per_m=0.023 is outside typical range [0.03, 0.1]. Results may be unreliable.",
      "details": {"method": "kirpich", "parameter": "slope_m_per_m", "field": "slope_m_per_m", "value": 0.023, "minimum": 0.03, "maximum": 0.1}
    }
  ],
  "inputs": {"length_km": 8.2, "slope_m_per_m": 0.023}
}
```

`result` is the document of the command (its own `schema`; units are in the field names), `notices` holds non-fatal warnings (here: a slope below the 3–10 % of the watersheds Kirpich's formula comes from; `hydrolog tc kirpich --schema` lists the typical ranges a command checks, with their sources) and `inputs` the options after normalization. A second call computes the design hydrograph of a 45.3 km2 watershed (CN 72, time of concentration 86 min, 38.5 mm of Beta-distributed rain in 60 min):

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

62 commands in 17 groups, all computed offline except `precip pmaxtp`, the only one that opens a network connection: it fetches the PMAXTP depth of IMGW-PIB through Obserwator (extra `pmaxtp`). The MCP tool is `hydrolog_` plus the command name with `_`; every command is also available as `hydrolog.run_command("<command>", **options)`.


| Group | Task | CLI command | MCP tool | Python (`hydrolog.operations`) |
|---|---|---|---|---|
| Time of concentration | Overland flow time (FAA) | `tc faa` | `hydrolog_tc_faa` | `tc_faa` |
| | Time of concentration (Giandotti) | `tc giandotti` | `hydrolog_tc_giandotti` | `tc_giandotti` |
| | Overland flow time (Kerby) | `tc kerby` | `hydrolog_tc_kerby` | `tc_kerby` |
| | Overland plus channel time (Kerby-Kirpich) | `tc kerby-kirpich` | `hydrolog_tc_kerby_kirpich` | `tc_kerby_kirpich` |
| | Time of concentration (Kirpich) | `tc kirpich` | `hydrolog_tc_kirpich` | `tc_kirpich` |
| | Time of concentration (NRCS lag, NEH 630) | `tc nrcs` | `hydrolog_tc_nrcs` | `tc_nrcs` |
| | Time of concentration of a watershed by any method | `tc watershed` | `hydrolog_tc_watershed` | `tc_watershed` |
| Curve numbers | The whole TR-55 curve number table | `cn list` | `hydrolog_cn_list` | `cn_list` |
| | Curve number of a soil group and land cover | `cn lookup` | `hydrolog_cn_lookup` | `cn_lookup` |
| | Curve number range of a land cover | `cn range` | `hydrolog_cn_range` | `cn_range` |
| | Area-weighted curve number of a watershed | `cn weighted` | `hydrolog_cn_weighted` | `cn_weighted` |
| Effective rainfall | Effective precipitation by SCS-CN | `scs effective` | `hydrolog_scs_effective` | `scs_effective` |
| Precipitation | Areal precipitation (arithmetic, Thiessen, IDW, isohyets) | `precip areal` | `hydrolog_precip_areal` | `precip_areal` |
| | Design hyetograph (block, triangular, Beta, Euler II) | `precip hietogram` | `hydrolog_precip_hietogram` | `precip_hietogram` |
| | PMAXTP design rainfall depth of IMGW-PIB at a point, fetched through Obserwator | `precip pmaxtp` | `hydrolog_precip_pmaxtp` | `precip_pmaxtp` |
| Unit hydrographs | Clark unit hydrograph | `uh clark` | `hydrolog_uh_clark` | `uh_clark` |
| | Nash cascade unit hydrograph (n and K, Lutz, urban regression) | `uh nash` | `hydrolog_uh_nash` | `uh_nash` |
| | SCS (NRCS) unit hydrograph | `uh scs` | `hydrolog_uh_scs` | `uh_scs` |
| | Snyder synthetic unit hydrograph | `uh snyder` | `hydrolog_uh_snyder` | `uh_snyder` |
| Runoff hydrograph | Design direct-runoff hydrograph | `hydrograph generate` | `hydrolog_hydrograph_generate` | `hydrograph_generate` |
| Flood routing | Cascade of linear reservoirs routing of a hydrograph, exact for any time step (writes a file if an output is given) | `route cascade` | `hydrolog_route_cascade` | `route_cascade` |
| | Lag routing of a hydrograph (writes a file if an output is given) | `route lag` | `hydrolog_route_lag` | `route_lag` |
| | Level-pool (storage indication) routing of a hydrograph through a reservoir with a storage-outflow table (writes a file if an output is given) | `route level-pool` | `hydrolog_route_level_pool` | `route_level_pool` |
| | Muskingum routing of a hydrograph over sub-reaches (writes a file if an output is given) | `route muskingum` | `hydrolog_route_muskingum` | `route_muskingum` |
| | Muskingum-Cunge routing of a hydrograph over a reach with its section or celerity (writes a file if an output is given) | `route muskingum-cunge` | `hydrolog_route_muskingum_cunge` | `route_muskingum_cunge` |
| | Hydrographs routed down a river network of catchments, reaches, reservoirs and junctions (writes a table per node if an output directory is given) | `route network` | `hydrolog_route_network` | `route_network` |
| | The schematic of a river network, laid out without routing it | `route schematic` | `hydrolog_route_schematic` | `route_schematic` |
| Morphometry | Geometric, shape and relief indicators | `morphometry watershed` | `hydrolog_morphometry_watershed` | `morphometry_watershed` |
| River network | River network order statistics (Strahler, Shreve) | `network stats` | `hydrolog_network_stats` | `network_stats` |
| Flow statistics | Baseflow by the Lyne-Hollick filter, the baseflow index and the recession constant | `stats baseflow` | `hydrolog_stats_baseflow` | `stats_baseflow` |
| | Characteristic values of the first and second degree (WQ to NQ, WWQ to NNQ, WWW to NNW) of a daily series or IMGW-PIB's half-years | `stats characteristic` | `hydrolog_stats_characteristic` | `stats_characteristic` |
| | Day-of-year statistics | `stats daily` | `hydrolog_stats_daily` | `stats_daily` |
| | Duration curve with class frequencies and the modal class | `stats duration-curve` | `hydrolog_stats_duration_curve` | `stats_duration_curve` |
| | Flood quantiles from annual maxima, a daily series or IMGW-PIB's half-years | `stats flood-frequency` | `hydrolog_stats_flood_frequency` | `stats_flood_frequency` |
| | Harmonics of the annual cycle of a daily series (mean, amplitude, day of maximum) | `stats harmonics` | `hydrolog_stats_harmonics` | `stats_harmonics` |
| | Homogeneity tests of annual maxima (Mann-Whitney U, Kolmogorov-Smirnov, Pettitt) | `stats homogeneity` | `hydrolog_stats_homogeneity` | `stats_homogeneity` |
| | Low-flow quantiles from annual minima of a daily series or IMGW-PIB's half-years | `stats low-flow` | `hydrolog_stats_low_flow` | `stats_low_flow` |
| | Low-flow (drought) sequences below a threshold, across gaps, with yearly summaries | `stats low-flow-sequences` | `hydrolog_stats_low_flow_sequences` | `stats_low_flow_sequences` |
| | Monotonic trend test (Mann-Kendall) with Sen's slope and its confidence interval | `stats mann-kendall` | `hydrolog_stats_mann_kendall` | `stats_mann_kendall` |
| | Monthly statistics with confidence interval | `stats monthly` | `hydrolog_stats_monthly` | `stats_monthly` |
| | Flow regime: Pardé coefficients, Dynowska's regime type, seasonality index | `stats regime` | `hydrolog_stats_regime` | `stats_regime` |
| | Annual and monthly runoff volumes, the cumulative volume of a year | `stats runoff-volume` | `hydrolog_stats_runoff_volume` | `stats_runoff_volume` |
| | Mean date and concentration of the annual maxima or minima | `stats seasonality` | `hydrolog_stats_seasonality` | `stats_seasonality` |
| | Events and days above or below a threshold | `stats threshold-events` | `hydrolog_stats_threshold_events` | `stats_threshold_events` |
| Hydrometry | Rating curve Q = a(H - H0)^b, also of dated pairs by range of years and period | `hydrometrics rating-curve` | `hydrolog_hydrometrics_rating_curve` | `hydrometrics_rating_curve` |
| | Water level zones NTW, STW, WTW (Rybczyński) | `hydrometrics water-level-zones` | `hydrolog_hydrometrics_water_level_zones` | `hydrometrics_water_level_zones` |
| Meteorological statistics | Sielianinov's hydrothermal coefficient of the months April to September and of the warm season | `meteo hydrothermal` | `hydrolog_meteo_hydrothermal` | `meteo_hydrothermal` |
| | Precipitation statistics: sums and normals, maxima, days, intensity, heavy precipitation, regime | `meteo precipitation` | `hydrolog_meteo_precipitation` | `meteo_precipitation` |
| | Snow cover of each winter: days, largest depth, first and last day, fresh snow | `meteo snow` | `hydrolog_meteo_snow` | `meteo_snow` |
| | Dry or wet spells of daily precipitation | `meteo spells` | `hydrolog_meteo_spells` | `meteo_spells` |
| | Standardized precipitation index (SPI) of several scales, relative precipitation of months and years | `meteo spi` | `hydrolog_meteo_spi` | `meteo_spi` |
| | Air temperature statistics: means and normals, characteristic days, degree days, daily range | `meteo temperature` | `hydrolog_meteo_temperature` | `meteo_temperature` |

| Soil | HSG GeoTIFF from clay, sand and silt rasters (writes a file) | `soil hsg` | `hydrolog_soil_hsg` | `soil_hsg` |
| | Area and share of HSG A-D in an HSG raster | `soil hsg-stats` | `hydrolog_soil_hsg_stats` | `soil_hsg_stats` |
| | USDA texture class and HSG of one sample | `soil texture` | `hydrolog_soil_texture` | `soil_texture` |
| Report | Markdown calculation report (writes a file) | `report generate` | `hydrolog_report_generate` | `report_generate` |
| Settings | Effective settings and their sources | `config show` | `hydrolog_config_show` | `config_show` |
| Web GUI | The web GUI, served on this computer until it is stopped (for a person, so no MCP tool) | `gui serve` | none (`hydrolog_gui_serve` is not a tool) | `gui_serve` |
| Catalog and guides | Run the catalog calls of a JSON Lines file in one process (writes a file) | `commands batch` | `hydrolog_commands_batch` | `commands_batch` |
| | Render AGENTS.md, llms.txt or a block (writes a file) | `commands guide` | `hydrolog_commands_guide` | `commands_guide` |
| | List the commands | `commands list` | `hydrolog_commands_list` | `commands_list` |
| | Options, units, rules and examples of a command | `commands schema` | `hydrolog_commands_schema` | `commands_schema` |

## For AI agents

- [llms.txt](https://github.com/Daldek/Hydrolog/blob/main/llms.txt) and [AGENTS.md](https://github.com/Daldek/Hydrolog/blob/main/AGENTS.md) state the scope, the workflow, the error codes and typical flows (design hydrograph of a watershed file, flood frequency from an Obserwator export, HSG from SoilGrids rasters); both are generated from the command catalog. `hydrolog commands guide --format agents` (or `llms`) prints them; `--format agents-md-block --inject AGENTS.md` puts a compact block into another repository's AGENTS.md.
- The catalog is served by the tool: `hydrolog commands list` (names, operation ids, summaries) and `hydrolog commands schema --command "tc kirpich"` (options with units, bounds and allowed values, result schema, rules, examples, errors, and the typical ranges the command checks with their sources, `typical_ranges`, which only the document of one command carries). In MCP these are the tools `hydrolog_commands_list` and `hydrolog_commands_schema`; `--schema` after any command prints its description instead of running it.
- Work in four steps: discover, check, run, read. A result is a `hydrolog-result/1` envelope (`status` is `ok`; a failing command ends with an error instead, and `commands batch` with failed calls is `partial` or `failed` with an `items` entry per call, exit 10 or 11), an error a `hydrolog-error/1` document.
- Calculations are read-only. Four commands write one file (`report generate`, `soil hsg`, `commands guide`, `commands batch`), and so does every `route` command that is given `--output`; they take `--output`, `--check` and `--force`: `--check` writes nothing and returns the plan, `result.targets[]` with `option`, `path` and `action` (`write`, `replace` or `conflict`); an existing file is replaced only with `--force`. `route network` writes one table per node into the directory of `--output-dir` (`-o`) the same way: its plan lists every table, and a directory that is, or lies in, the store of another Nogat tool is refused (`conflict`, `details.reason` `output_in_store`). A `route` command without `--output`, and `route network` without `--output-dir`, has no file to plan: it returns the routed hydrographs, also with `--check`.

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
- `--allow-writes`: lets `report generate`, `soil hsg`, `commands guide`, `commands batch` (whose calls keep the server's `--allow-dir`) and the `route` commands (with `output`, `route network` with `output_dir`) write inside the allowed directories; without it they run as `check` and return the plan, while a `route` command without an output still returns the routed hydrographs.
- `--tools FAMILIES`: comma-separated tool families, a command group (`tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `route`, `morphometry`, `network`, `stats`, `hydrometrics`, `meteo`, `soil`, `report`, `config`, `commands`) or `core`, the main tasks (`tc watershed`, `cn lookup`, `cn weighted`, `scs effective`, `hydrograph generate`, `morphometry watershed`, `stats flood-frequency`, `commands list`, `commands schema`).

- The server speaks English only (`hydrolog mcp --lang en` is rejected). Instructions are at most 4,096 characters, each tool description at most 600; an execution error is an `isError` result that holds the `hydrolog-error/1` document.

## Web GUI

The web GUI is Hydrolog in a browser, in Polish, for people who would rather not use a command line: open a section, enter or load the data (the guide has a worked example for each section) and read the result. **Hydrogram zlewni** gives the runoff hydrograph of one watershed after a design storm and recomputes it after every change; under PMAXTP the storm's depth is not typed but fetched read-only by `precip pmaxtp` for the point, probability, duration and method given; **Sieć i trasowanie** builds a river network of subcatchments, reaches, reservoirs, junctions and an outlet on a canvas, as in HEC-HMS's basin model editor (or opens one from a file or a hand-off), in the order a hydrologist thinks of it: the network's time step and rainfall first (PMAXTP, a design hyetograph or a series), then the elements, then each subcatchment in a panel beside the data with Hydrogram zlewni's own three steps; it checks the structure while it is edited, lays it out before any value is given, keeps the place and the description of every node in the network document and routes it, and a network that Hydrograf delineates at control points opens laid out with the origin of each node, which the network keeps when it is handed on; **Statystyka przepływów** fits every flood frequency distribution by every fit method to annual maxima, shows the combinations chosen, tests the homogeneity of the series and recomputes after every change; **Kalkulatory** compares the time of concentration of six methods and holds fifteen single calculators; **Wszystkie polecenia** has a form for every command of the catalog. Every number comes from the same catalog as the CLI, and every result shows the command line that gives it. Results leave the page as CSV, JSON or PNG, a Markdown report, a print view (a PDF by the browser) or a hand-off `nogat-handoff/1`, the format in which the GUI exchanges watersheds and networks with Hydrograf. The results are estimates of simplified methods, not a forecast or a flood hazard map. A guide for users, in Polish and starting in plain words, opens from „Instrukcja” in the top bar.

```sh
hydrolog gui serve                          # http://127.0.0.1:8070/, opened in the browser; Ctrl+C stops it
hydrolog gui serve --no-browser --port 8071
```

`--check` only reports the address and whether the port is free. The server has no sign-in: anyone who reaches it can compute and upload files (each open page gets a work directory of its own, with limits, deleted when the page is closed or reloaded and at the latest after an hour idle; the page keeps its id in its memory, no cookie). It listens on 127.0.0.1, this computer only. To share it, keep it there and put an authenticating reverse proxy in front of it, for example Cloudflare Access on a Cloudflare Tunnel to `127.0.0.1:8070`, or open it to everyone as a public GUI (below); `--host` with another address exposes it without a sign-in and adds the warning `exposed_without_auth`. Running it as a service, your data in the GUI and the limits: [docs/USAGE.md](https://github.com/Daldek/Hydrolog/blob/main/docs/USAGE.md#8-the-web-gui); hosting it in another app: [docs/INTEGRATION.md](https://github.com/Daldek/Hydrolog/blob/main/docs/INTEGRATION.md#web-gui-a-module-of-nogats-gui-platform).

**Logs** (Nogat DEV-12.4 to DEV-12.9, [ADR-0037](https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/0037-nogats-logs-in-gui-serve.md)). `hydrolog gui serve` keeps three logs as JSON Lines of `nogat-log/1` (`schemas/nogat/record-1.schema.json`) in `<state_dir>/hydrolog/logs/`, one file per kind and UTC day (`access-YYYY-MM-DD.jsonl`, `app-…`, `lifecycle-…`), `~/.local/state/nogat/hydrolog/logs/` by default (`state_dir` is `HYDROLOG_STATE_DIR`, `NOGAT_STATE_DIR`, `nogat.toml`, else the user state directory of `nogat`), and deletes each file itself 14 days after its date, at the start and at every midnight UTC. The access log has one record per request, public or not, but the page's files and the catalog documents answered below 400: `method`, `path` with its query (the values of free text, names, e-mail addresses and keys dropped: `?q=`), `status`, `bytes`, `duration_ms`, the kind of client in `agent` (`browser`, `bot`, `script`, `none`) and a random `request_id` never sent back; no log holds an IP address, a cookie or the `User-Agent` itself. Standard error, and with it the journal of a service, gets only the records of the start (with the address, `url`, and `public`), the stop and the deletion of old files, and errors reduced to their type. Read the last 14 days without the successful requests with [jq](https://jqlang.org/):

```sh
jq -cs 'sort_by(.time)[] | select(.kind != "access" or .status >= 500)' ~/.local/state/nogat/hydrolog/logs/*.jsonl
```

Usage is counted only in the daily totals of a public GUI (below), never from the logs.

**A public GUI** (Nogat DEV-15.7 to DEV-15.12, [ADR-0034](https://github.com/Daldek/Hydrolog/blob/main/docs/decisions/0034-a-public-gui-regulamin-limit-logs-totals.md)). With the table `operator` of `[nogat]` in `nogat.toml` (`name`, `email`, `terms_effective`, `processor`, `processor_transfer`, `processor_cookie`, `mail_provider`, `mail_transfer`) and Hydrolog's own address in `[nogat] gui` (`hydrolog = "https://…/"`), the GUI is open to anyone without signing in and keeps Nogat's rules for that:

- **Regulamin.** It fills the regulamin of Nogat's GUI kit at the start, with the blocks of its sources (PMAXTP, IMGW-PIB and ČHMÚ station series), serves it at `regulamin.html` beside its page and links it, with the statement „Serwis jest niekomercyjny i bezpłatny…”, at the foot of every view and in the menu „Aplikacje”; a field missing or empty leaves no page and no link, and a warning in the log.
- **Request limit.** At most `request_limit` requests (default 300) of one client address in `request_window` seconds (default 60), the address held in memory for its window only; static files and the catalog documents (`api/commands…`, `api/schemas/…`) are not counted. Over it the answer is `429` with `Retry-After`: an API route the error `rate_limited`, a page „Zbyt wiele żądań. Spróbuj ponownie za <n> s.”. Behind a proxy on the same machine (`cloudflared`) the address is the one in `X-Forwarded-For`, trusted only from `127.0.0.1` (uvicorn's `FORWARDED_ALLOW_IPS`).
- **Daily totals** in `<data_dir>/hydrolog/stats.jsonl`, one JSON line per UTC day (`date`, `visitors`, `page_views`, `stations_opened`, `analyses_run`, `downloads`), rewritten every five minutes, at midnight UTC and at the stop: `visitors` are the day's distinct HMAC-SHA-256 of the address and the `User-Agent` under a random salt drawn at the start and every midnight, never written; `page_views` the app, its guide and the regulamin served (not the admin page); `stations_opened` the stations' series from a hand-off opened in Statystyka przepływów; `analyses_run` the computations the server ran (not the plans of `--check`); `downloads` the files the page saved (exports, reports, hand-off files, outputs). A restart adds to the day's line with a new salt.
- **The admin panel is the operator's.** Put `/admin`, `/admin/*` and `/api/admin/*` behind a sign-in (Cloudflare Access); the key of `HYDROLOG_ADMIN_API_KEY` still guards the API. Its requests count in no daily total and stay under the request limit.

**Zgłoś uwagę** (report a problem) in the top bar sends a report to whoever runs the server: a text of up to 5,000 characters and the context the page adds itself, the open view, the station of a station's series, the view's inputs and the version; nothing else (Nogat DEV-15.12). There is no contact field: under the text the dialog says „Nie wpisuj danych osobowych”, in a public GUI with the operator's address to write to for an answer, and the server refuses any other field (`validation_error`, `unknown_field`), so a report holds no contact, no address of the page, no browser and no IP address. The reports are kept in one SQLite file, `<data_dir>/hydrolog/feedback.sqlite3`, which the first report makes (`data_dir` is `HYDROLOG_DATA_DIR`, `NOGAT_DATA_DIR`, `data_dir` of `nogat.toml` or the user data directory, `~/.local/share/nogat` on Linux; `hydrolog config show` prints it); a deleted report is overwritten in the file. A file of the earlier form (with contacts, the page's addresses, browsers and diagnostics) is first copied whole to `feedback-v1-<UTC time>.sqlite3` beside it, then its reports keep their text and get the context their address and diagnostics give; the copy is the operator's to delete once its reports are handled. Read them in the admin panel (below), or with `sqlite3`, and back the file up with SQLite's `.backup`, which is safe while the server runs:

```sh
openssl rand -hex 32 > ~/.config/hydrolog-admin.key && chmod 600 ~/.config/hydrolog-admin.key
HYDROLOG_ADMIN_API_KEY_FILE=~/.config/hydrolog-admin.key hydrolog gui serve --no-browser
sqlite3 ~/.local/share/nogat/hydrolog/feedback.sqlite3 \
  "SELECT id, created_at, is_read, message, context FROM feedback ORDER BY created_at DESC"
sqlite3 ~/.local/share/nogat/hydrolog/feedback.sqlite3 ".backup feedback-backup.sqlite3"
```

**The admin panel** (Nogat DEV-15.13, ECO-067; kit 0.7.0) is `admin/` under the GUI's address (`http://127.0.0.1:8070/admin/`; `admin` answers `308` to it), Nogat's `<nogat-admin>` with three sections: „Zgłoszenia” lists the reports newest first with the count of unread ones, shows each one's context, marks it read or unread and deletes it after a question; „Statystyki” shows the daily totals of `stats.jsonl` for 7, 30 or 90 days or the whole record, and saves them as CSV; „Stan” shows the version, the start, the uptime, the data directory `<data_dir>/hydrolog`, the free disk and two checks:

- `data_dir`: the data directory can be written (a probe file, made and removed at once), or, before the first report, the directory above it, where the first write makes it; `failed` otherwise.
- `feedback_db`: the reports' file can be read, with its counts of reports and unread ones; without a file, `ok` until the first report; `failed` when it is not a readable database.

The panel asks for the key in `HYDROLOG_ADMIN_API_KEY`, or in the file that `HYDROLOG_ADMIN_API_KEY_FILE` names, read at every request, and keeps it in the browser tab (`sessionStorage`, `hydrolog/admin-key/1`) until „Wyloguj”. Without either the server refuses every admin request (`401 unauthorized`, `admin_key_not_configured`); no key is generated or logged. Its API, `GET api/admin/feedback`, `PATCH` and `DELETE api/admin/feedback/{id}`, `GET api/admin/stats?from=&to=` and `GET api/admin/status`, is Nogat's core admin API ([docs/USAGE.md](https://github.com/Daldek/Hydrolog/blob/main/docs/USAGE.md#reports-of-users-zgłoś-uwagę)); no answer of the panel is stored (`Cache-Control: no-store`) and the page is not indexed (`noindex`).

## Related tools

- [Kartograf](https://github.com/Daldek/Kartograf) downloads Polish and Czech geodata (elevation, land cover, soils); the `files[].path` values in the `--json` result of `kartograf soil download --output-dir DIR` are the clay, sand and silt rasters of `soil hsg`.
- [Obserwator](https://github.com/Daldek/Obserwator) provides IMGW-PIB and CHMU series: `obserwator series export --output FILE` writes the CSV that `--input-file` of the `stats`, `hydrometrics` and `meteo` commands reads; `precip pmaxtp` (extra `pmaxtp`) fetches the PMAXTP design precipitation of a point through it, the `--total-mm` of a design storm.
- [Hydrograf](https://github.com/Daldek/Hydrograf) is a web app for watershed delineation and design hydrographs built on Hydrolog; watersheds travel as `WatershedParameters` JSON, and watersheds and the networks it delineates at control points as hand-offs `nogat-handoff/1` with the origin of each node ([docs/INTEGRATION.md](https://github.com/Daldek/Hydrolog/blob/main/docs/INTEGRATION.md)).
- [Retman](https://github.com/Daldek/Retman) is a Polish natural-language command layer over the ecosystem tools; it is designed to drive Hydrolog through the command layer (`hydrolog.operations`).
- [Hydraulik](https://github.com/Daldek/Hydraulik) screens 2D floods (research stage) and uses the Beta and Euler type II hyetograph classes of Hydrolog; [Nogat](https://github.com/Daldek/Nogat) holds the shared standards and the registry of these tools.
- External alternatives: HEC-HMS when a study needs several sub-basins, channel routing, reservoirs or calibration; HEC-RAS for hydraulics and inundation; EPA SWMM for urban drainage networks; WhiteboxTools or pysheds for watershed delineation and flow routing on a DEM.

## Errors and exit codes

An error exits with a registry code and, in both CLI modes, ends stderr with a `hydrolog-error/1` JSON line (`code`, `title`, `message`, `hint`, `details`, `exit_code`); Python raises `hydrolog.HydrologError` subclasses with the same `code`, `details` and `hint`, and MCP returns the document in an `isError` result. The shared registry: [ERROR_REGISTRY.md](https://github.com/Daldek/Nogat/blob/main/standards/ERROR_REGISTRY.md).

| Code | Exit | Typical cause | Hint |
|---|---|---|---|
| `validation_error` | 2 | missing, unknown or out-of-range option | fix the option in `details.option`, see `commands schema` |
| `not_found` | 3 | unknown command or missing input file | check the name (`details.suggestions`) or the path |
| `conflict` | 4 | an output file exists, or the output directory lies in the store of another Nogat tool | give another `--output` or `--output-dir`, or add `--force` |
| `missing_dependency` | 6 | an optional extra is not installed | add the extra the error names (`raster`, `mcp`, `pmaxtp`, `gui` or `viz`), see Install |
| `data_error` | 7 | malformed CSV, JSON or GeoTIFF | see `details.path` and `details.reason` |

Also `source_unavailable` (5, `precip pmaxtp` only: IMGW-PIB did not answer), `io_error` (9, output not writable), `forbidden` (12, path outside `--allow-dir`), `calculation_error` (13, valid input without a result), `internal_error` (1), `cancelled` (130) and `terminated` (143).

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

Hydrolog downloads nothing and needs no account, except the PMAXTP depth of `precip pmaxtp`: the only network connection it opens, to the PMAXTP service of IMGW-PIB, through Obserwator (extra `pmaxtp`), sending only the point's coordinates and the method. Its only key is one you choose for the web GUI's admin page. Input is numbers or local files: CSV series (an Obserwator export loads unchanged), JSON (watershed, stations, network segments, the network of `route network`) and GeoTIFF rasters (extra `raster`). It ships no dataset except the TR-55 curve number table of USDA NRCS. The data you pass keep the licence of their source (IMGW-PIB terms of reuse, SoilGrids CC BY 4.0); Hydrolog does not copy the attribution columns of an Obserwator export into results, so name the source when you publish a result. A PMAXTP depth carries the attribution IMGW-PIB prescribes (`attribution` and the notice `pmaxtp_attribution`).

A command writes only to the file named by `--output` (exactly one plain file, written atomically; `commands guide --inject PATH` edits the AGENTS.md you name) or, for `route network`, into the directory named by `--output-dir` (one table per node, each moved into place from a `.hydrolog-incoming/` staging directory that is removed afterwards), and replaces an existing file only with `--force`. There is no store or cache; only the web GUI writes files of its own, the reports of „Zgłoś uwagę” in `<data_dir>/hydrolog/feedback.sqlite3`, public, its daily totals in `<data_dir>/hydrolog/stats.jsonl`, and the logs of `gui serve` in `<state_dir>/hydrolog/logs/`.

Settings (`lang`, `log_level`, `data_dir`, `state_dir`, `request_limit`, `request_window`) come from, in order: the command-line option, `HYDROLOG_<KEY>`, `NOGAT_<KEY>`, `nogat.toml` (section `[hydrolog]`, then `[nogat]`) in the user config directory or at `NOGAT_CONFIG`, then the default; an invalid environment or file value is ignored. [.env.example](https://github.com/Daldek/Hydrolog/blob/main/.env.example) lists every variable: `HYDROLOG_LANG`, `NOGAT_LANG` (`pl` or `en`, default `pl`), `HYDROLOG_LOG_LEVEL`, `NOGAT_LOG_LEVEL` (`debug`, `info`, `warning` or `error`, default `warning`), `HYDROLOG_DATA_DIR`, `NOGAT_DATA_DIR` (the data directory, default the user data directory of `nogat`), `HYDROLOG_STATE_DIR`, `NOGAT_STATE_DIR` (the state directory, where `gui serve` keeps its logs, default the user state directory of `nogat`), `HYDROLOG_REQUEST_LIMIT`, `NOGAT_REQUEST_LIMIT` (the requests a public web GUI answers per client address in a window, default 300), `HYDROLOG_REQUEST_WINDOW`, `NOGAT_REQUEST_WINDOW` (that window in seconds, default 60), `NOGAT_CONFIG`, and the credential, which is read from the environment only, never from `nogat.toml`: `HYDROLOG_ADMIN_API_KEY` or `HYDROLOG_ADMIN_API_KEY_FILE` (the key of the web GUI's admin page, or a file that holds it). `hydrolog config show` prints the effective values, where each comes from and whether each credential variable is set, never its value:

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
      {"key": "log_level", "value": "warning", "source": "default"},
      {"key": "data_dir", "value": "...", "source": "default"},
      {"key": "state_dir", "value": "...", "source": "default"},
      {"key": "request_limit", "value": "300", "source": "default"},
      {"key": "request_window", "value": "60", "source": "default"}
    ],
    "credentials": [
      {"name": "HYDROLOG_ADMIN_API_KEY", "present": false},
      {"name": "HYDROLOG_ADMIN_API_KEY_FILE", "present": false}
    ],
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
- [Integration](https://github.com/Daldek/Hydrolog/blob/main/docs/INTEGRATION.md): files exchanged with Hydrograf, Retman, Kartograf and Obserwator; hosting the web GUI

## Development

[CLAUDE.md](https://github.com/Daldek/Hydrolog/blob/main/CLAUDE.md) holds the instructions for working on the repository (rules, code map, documentation map); set up with `uv sync --locked --all-extras` and run `scripts/gate.sh` before every commit: ruff format and check, mypy, the tests with coverage and the commit checks. See also [CONTRIBUTING.md](https://github.com/Daldek/Hydrolog/blob/main/CONTRIBUTING.md) and [SECURITY.md](https://github.com/Daldek/Hydrolog/blob/main/SECURITY.md).

## Status, licence, author

Alpha: version 1.0.0 is not released yet (the repository carries `1.0.0.dev0`), and semantic versioning applies from 1.0.0. Licence: MIT. Author: Piotr de Bever ([Daldek](https://github.com/Daldek)). Hydrolog is part of the [Nogat](https://github.com/Daldek/Nogat) ecosystem and follows its standard 2.1.
