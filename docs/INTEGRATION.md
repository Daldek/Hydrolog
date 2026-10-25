# Hydrograf ↔ Hydrolog integration

**Created:** 2026-01-20
**Last updated:** 2026-10-19 (Hydrolog 1.0.0: Retman, MCP clients, HSG migration, IMGWTools export)
**Status:** In progress (Hydrolog - ready; Hydrograf - to be implemented)

---

## Purpose

Enable easy data exchange between Hydrograf (GIS spatial analysis) and Hydrolog (hydrological calculations), with the option to integrate other systems: the Retman agent platform, MCP clients (e.g. Claude Code), and the IMGWTools and Kartograf tools, which supply input data. Hydrolog downloads nothing and does not depend on any of these tools - data is exchanged through files (JSON, CSV, GeoTIFF). Hydrolog is a consumer that needs plain files, so it reads the output of Kartograf and IMGWTools written in plain-file mode (`--output-dir`, `output_dir=`), not from a versioned store.

---

## Division of responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                         HYDROGRAF                               │
│  Responsibility: SPATIAL ANALYSIS (GIS)                          │
│                                                                 │
│  - Watershed delineation from the DEM (flow network)            │
│  - Geometric parameters from boundary/cells                     │
│  - Elevation statistics from the DEM                            │
│  - CN from land cover                                           │
│  - Precipitation interpolation (IDW/Thiessen)                   │
│                                                                 │
│  OUTPUT: JSON conforming to the WatershedParameters schema      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  STANDARDIZED JSON FORMAT     │
              │  (WatershedParameters schema) │
              └───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         HYDROLOG                                │
│  Responsibility: HYDROLOGICAL CALCULATIONS                      │
│                                                                 │
│  - Time of concentration (Kirpich, SCS Lag, Giandotti, FAA,    │
│    Kerby, Kerby-Kirpich)                                        │
│  - Unit hydrographs (SCS, Nash, Clark, Snyder)                  │
│  - Rainfall→runoff transformation (convolution)                 │
│  - Watershed shape indices                                      │
│  - Hypsometric curve                                            │
│                                                                 │
│  INPUT: WatershedParameters.from_dict(json_data)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data exchange format

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WatershedParameters",
  "description": "Standardized watershed parameter format for GIS ↔ Hydrolog integration",
  "type": "object",
  "required": ["area_km2", "perimeter_km", "length_km", "elevation_min_m", "elevation_max_m"],
  "properties": {
    "name": {"type": "string", "description": "Watershed name"},
    "area_km2": {"type": "number", "minimum": 0, "description": "Area [km²]"},
    "perimeter_km": {"type": "number", "minimum": 0, "description": "Perimeter [km]"},
    "length_km": {"type": "number", "minimum": 0, "description": "Watershed length [km]"},
    "elevation_min_m": {"type": "number", "description": "Minimum elevation [m a.s.l.]"},
    "elevation_max_m": {"type": "number", "description": "Maximum elevation [m a.s.l.]"},
    "elevation_mean_m": {"type": "number", "description": "Mean elevation [m a.s.l.]"},
    "mean_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Mean slope [m/m]"},
    "channel_length_km": {"type": "number", "minimum": 0, "description": "Channel length [km]"},
    "channel_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Channel slope [m/m]"},
    "cn": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Curve Number"},
    "source": {"type": "string", "description": "Data source"},
    "crs": {"type": "string", "description": "Coordinate reference system"},

    "__comment_v063": "Optional fields added in v0.6.3+",
    "runoff_coeff": {"type": "number", "exclusiveMinimum": 0, "maximum": 1.0, "description": "Runoff coefficient C for the FAA method"},
    "retardance": {"type": "number", "exclusiveMinimum": 0, "description": "Kerby retardance coefficient (0.02-0.80)"},
    "overland_length_km": {"type": "number", "exclusiveMinimum": 0, "description": "Overland flow length [km] (FAA, Kerby, Kerby-Kirpich)"},
    "overland_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Overland flow slope [m/m] (FAA, Kerby, Kerby-Kirpich)"},
    "Lc_km": {"type": "number", "exclusiveMinimum": 0, "description": "Distance to the watershed centroid along the channel [km] (Nash/Snyder)"},
    "manning_n": {"type": "number", "exclusiveMinimum": 0, "description": "Manning's roughness coefficient (Nash)"},
    "urban_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "Percentage of urbanized area [%] (Nash)"},
    "forest_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "Percentage of forested area [%] (Nash)"}
  }
}
```

### JSON example

```json
{
  "name": "Stream X watershed",
  "area_km2": 45.3,
  "perimeter_km": 32.1,
  "length_km": 12.5,
  "elevation_min_m": 150.0,
  "elevation_max_m": 520.0,
  "elevation_mean_m": 340.0,
  "mean_slope_m_per_m": 0.025,
  "cn": 72,
  "source": "Hydrograf",
  "crs": "EPSG:2180"
}
```

---

## Implementation in Hydrolog

### New class: `WatershedParameters`

**File:** `hydrolog/morphometry/watershed_params.py`

**Status:** ✅ Implemented

```python
from hydrolog.morphometry import WatershedParameters

# Create from a dict (e.g. from an API response)
params = WatershedParameters.from_dict(json_data)

# Create from a JSON string
params = WatershedParameters.from_json(json_string)

# Eksport
d = params.to_dict()
s = params.to_json(indent=2)

# Convert to Hydrolog classes
geom = params.to_geometry()      # WatershedGeometry
terrain = params.to_terrain()    # TerrainAnalysis

# Calculations
tc = params.calculate_tc(method="kirpich")

# Computed properties
width = params.width_km    # A / L
relief = params.relief_m   # max - min
```

### `from_dict()` methods in existing classes

**Status:** ✅ Implemented

**Files:**
- `hydrolog/morphometry/geometric.py` - `WatershedGeometry.from_dict()`
- `hydrolog/morphometry/terrain.py` - `TerrainAnalysis.from_dict()`

> **Related documents:**
> - Mathematical details of the UH models and computation paths: see [COMPUTATION_PATHS.md](COMPUTATION_PATHS.md)
> - Project scope and responsibility boundaries: see [SCOPE.md](SCOPE.md)

---

## Implementation in Hydrograf

> **Note:** These changes will be implemented as part of CP3 (Hydrograph generation).

### New module: `backend/core/morphometry.py`

**Status:** 🔲 To be implemented

```python
"""Morphometric calculations from watershed cells."""

from shapely.geometry import Polygon
from core.watershed import FlowCell
import numpy as np

def calculate_perimeter_km(boundary: Polygon) -> float:
    """Calculate watershed perimeter from boundary polygon."""
    return boundary.length / 1000  # m -> km

def calculate_watershed_length_km(
    cells: list[FlowCell],
    outlet: FlowCell
) -> float:
    """Calculate watershed length (max distance from outlet)."""
    distances = [
        ((c.x - outlet.x)**2 + (c.y - outlet.y)**2)**0.5
        for c in cells
    ]
    return max(distances) / 1000  # m -> km

def calculate_elevation_stats(cells: list[FlowCell]) -> dict:
    """Calculate elevation statistics from cells."""
    elevations = np.array([c.elevation for c in cells])
    areas = np.array([c.cell_area for c in cells])

    return {
        "elevation_min_m": float(np.min(elevations)),
        "elevation_max_m": float(np.max(elevations)),
        "elevation_mean_m": float(np.average(elevations, weights=areas)),
    }

def calculate_mean_slope(cells: list[FlowCell]) -> float:
    """Calculate area-weighted mean slope."""
    valid = [(c.slope, c.cell_area) for c in cells if c.slope is not None]
    if not valid:
        return 0.0
    slopes, areas = zip(*valid)
    return float(np.average(slopes, weights=areas)) / 100  # % -> m/m

def build_morphometric_params(
    cells: list[FlowCell],
    boundary: Polygon,
    outlet: FlowCell,
    cn: int | None = None,
) -> dict:
    """
    Build complete morphometric parameters dictionary.

    Returns dict compatible with Hydrolog's WatershedParameters.from_dict()
    """
    elev_stats = calculate_elevation_stats(cells)

    return {
        "area_km2": sum(c.cell_area for c in cells) / 1_000_000,
        "perimeter_km": calculate_perimeter_km(boundary),
        "length_km": calculate_watershed_length_km(cells, outlet),
        "elevation_min_m": elev_stats["elevation_min_m"],
        "elevation_max_m": elev_stats["elevation_max_m"],
        "elevation_mean_m": elev_stats["elevation_mean_m"],
        "mean_slope_m_per_m": calculate_mean_slope(cells),
        "cn": cn,
        "source": "Hydrograf",
        "crs": "EPSG:2180",
    }
```

### Extending the Pydantic schemas

**File:** `backend/models/schemas.py`

```python
class MorphometricParameters(BaseModel):
    """
    Morphometric parameters compatible with Hydrolog.

    This schema matches Hydrolog's WatershedParameters dataclass.
    """
    # Required
    area_km2: float = Field(..., ge=0)
    perimeter_km: float = Field(..., ge=0)
    length_km: float = Field(..., ge=0)
    elevation_min_m: float
    elevation_max_m: float

    # Optional
    elevation_mean_m: float | None = None
    mean_slope_m_per_m: float | None = None
    channel_length_km: float | None = None
    channel_slope_m_per_m: float | None = None
    cn: int | None = Field(None, ge=0, le=100)
    source: str | None = "Hydrograf"
    crs: str | None = "EPSG:2180"

class WatershedResponse(BaseModel):
    # ... existing fields ...
    morphometry: MorphometricParameters | None = None  # NEW
```

### Extending the endpoint

**File:** `backend/api/endpoints/watershed.py`

```python
from core.morphometry import build_morphometric_params

@router.post("/delineate-watershed")
def delineate_watershed(...):
    # ... existing code ...

    # NEW: Calculate morphometric parameters
    morph_dict = build_morphometric_params(cells, boundary, outlet_cell)

    response = DelineateResponse(
        watershed=WatershedResponse(
            # ... existing fields ...
            morphometry=MorphometricParameters(**morph_dict),  # NEW
        )
    )
```

---

## Full integration example

```python
# === In Hydrograf (or another GIS system) ===
import requests

# 1. Delineate the watershed
response = requests.post(
    "http://localhost:8000/api/delineate-watershed",
    json={"latitude": 52.23, "longitude": 21.01}
)
data = response.json()

# 2. Get the morphometric parameters
morph_json = data["watershed"]["morphometry"]


# === In any application using Hydrolog ===
from hydrolog.morphometry import WatershedParameters
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# 3. Import the parameters into Hydrolog
params = WatershedParameters.from_dict(morph_json)

# 4. Compute the time of concentration
tc = params.calculate_tc(method="kirpich")

# 5. Generate the hydrograph
generator = HydrographGenerator(
    area_km2=params.area_km2,
    cn=params.cn,
    tc_min=tc,
)
hietogram_gen = BetaHietogram()
hietogram = hietogram_gen.generate(total_mm=50, duration_min=60, timestep_min=5)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
```

---

## Hydrolog 1.0.0: operations layer, command catalog and files

Since v1.0.0 Hydrolog has a single command catalog (`hydrolog.catalog`, 44 commands, list: `hydrolog commands list`) from which the following are generated: the Python operations layer (`hydrolog.operations`), the `hydrolog` CLI, the MCP server (`hydrolog mcp`) and the agent guides (`AGENTS.md`, `llms.txt`). The library classes (`HydrographGenerator`, `WatershedParameters`, ...) work as before; the sections below describe the new ways of integrating.

### Flood routing over a network: Hydrograf and Hydraulik

`route network` routes the hydrographs of many subcatchments down a river network. The network is the document `hydrolog-network/1` ([ADR-0010](decisions/0010-route-network-document-and-output-directory.md); JSON Schema `src/hydrolog/schemas/hydrolog-network-1.schema.json`).

- **Hydrograf (a mapping it can use):** a subcatchment of the delineated watershed is a node of type `subcatchment` whose discharge is the hydrograph that `hydrograph generate` gives for it, written to a column of `inflows_file` (named by the `value_column` or else by the `id` of the node; one time step and one first time for all); a stream segment (`StreamSegment`, `upstream_ids`) is a `reach` whose `from` is the node above it and whose `method` and options Hydrograf chooses (`lag_min`; `k_min` and `x`; `length_km` and `slope_m_per_m` with a section or a celerity); a confluence is a `junction` that lists the nodes that join; a reservoir is a `reservoir` with its storage-outflow table; the last node is the `outlet`. A node `id` names a file: letters, digits, `_`, `.` and `-`, at most 64 characters, unique without regard to case. A bifurcation is refused.
- **Hydraulik (hand-off):** `route network --output-dir DIR` writes `<id>.csv` for each node, the hydrograph that leaves the node (`time_min` in minutes at a regular step, `discharge_m3s` in m3/s), which is the inflow of a hydraulic model at that node. The `result.files[]` of the `--json` result lists the paths with their SHA-256. Hydrolog reads no file of Hydraulik.
- A `rating_file` named by the document lies beside `network_file`; an inline network (MCP) cannot name files.
- A network exporter in Hydrograf and a reader of the tables in Hydraulik are `request` issues in their repositories (DEV-17.5); this change opens none.

### Retman (calculation handlers)

Retman calls Hydrolog through the command layer, not through the library classes.

- **Operations layer:** `hydrolog.operations` - one public, typed function per command (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...), arguments named like the command options, NumPy-style docstrings (used by `retman-scaffold`). The function returns a result object with `to_dict()`/`to_json()`, or an `OperationOutput` (`result`, `notices`, `files`) when the command has warnings or writes files.
- **Catalog and envelope:** `hydrolog.catalog.run_command("<group> <command>", {options})` (also `hydrolog.run_command`) validates the options, runs the operation and returns a `hydrolog-result/1` envelope (`schema`, `tool`, `version`, `command`, `check`, `status`, `result`, `notices`, `inputs`; the files written are in `result.files[]` with SHA-256; `to_dict()`, `to_json()`). Option schema (JSON Schema): `command_schema()`, `hydrolog commands schema`. Errors are `HydrologError` exceptions with `code`, `hint` and `details` (registry `ERROR_CODES`; document `hydrolog-error/1`).
- **`catchment_characteristics`:** the proposed format is `WatershedParameters` JSON (`WatershedParameters.to_json()`; required `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`). The file is passed to commands as `watershed_file`, and `WatershedParameters.from_dict()` ignores the extra `schema` key (e.g. `"hydrolog-catchment/1"`) added by the catalog tools.
- **File inputs and outputs:** series (`input_file` + `value_column`/`date_column`), rainfall stations (`stations_file`), network segments (`segments_file`) and the watershed (`watershed_file`) as CSV/JSON; results that write files (`soil hsg` - GeoTIFF, `report generate` - Markdown; one file given by `--output`, an existing file needs `--force`) list them in `result.files[]`. Retman does not need to paste series into arguments.
- **Versions:** the tool manifest in Retman: `supported_versions=">=1.0,<2"` (semantic versioning applies from 1.0.0: options, command names and envelope shapes do not change incompatibly within the 1.x series).

```python
from hydrolog.catalog import run_command

result = run_command(
    "hydrograph generate",
    {
        "watershed_file": "/data/watersheds/stream_x.json",
        "tc_method": "kirpich",
        "hietogram_type": "beta",
        "total_mm": 50,
        "duration_min": 60,
    },
)
print(result.result.peak_discharge_m3s, [n.message for n in result.notices])  # result object
envelope = result.to_dict()  # hydrolog-result/1 envelope as a dict (result.to_json() - text)
```

### MCP clients (Claude Code and others)

The MCP server exposes every catalog command as a tool (name = `operation_id`, e.g. `hydrolog_tc_kirpich`). It requires the `hydrolog[mcp]` extra (`mcp>=2.3,<3`) and runs over stdio.

```bash
pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"

# Claude Code
claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data
```

Other MCP clients (configuration file, e.g. `.mcp.json`):

```json
{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/data/hydrolog-data"]}}}
```

- `--allow-dir DIR` (repeatable) lists the directories in which the tools may read files and, with `--allow-writes`, write them; paths outside them fail with a `forbidden` error. Without `--allow-dir`, commands with path-type options are rejected, while commands without files (e.g. `hydrolog_tc_kirpich`, `hydrolog_cn_lookup`) work.
- `--allow-writes` lets the writing tools (`hydrolog_report_generate`, `hydrolog_soil_hsg`, `hydrolog_commands_guide`) write inside the `--allow-dir` directories; without it they only plan. `--tools FAMILIES` limits the exposed tools to command groups or `core`. The console script `hydrolog-mcp` starts the same server. The server has no `--lang` option: its output is always English.
- Success: `structuredContent` = the `hydrolog-result/1` envelope; error: `isError: true` with a `hydrolog-error/1` document.
- Agent guide: `AGENTS.md` in the repository (generated by `hydrolog commands guide --format agents --output AGENTS.md`).

### IMGWTools: series export → `stats` commands

Hydrolog does not download IMGW data. IMGWTools exports the daily series (`series export`) to a single CSV file with units in the header (`Q [m3/s]`), a `date` column, value flags and attribution. Export to a file uses `--output FILE` (for example `series export ... --output q_daily.csv`); the versioned-store root option is `--root` and defaults to the user data directory. The file is loaded without preprocessing (comma or semicolon separator, UTF-8; columns are given by name without the unit: `Q` finds `Q [m3/s]`):

```bash
hydrolog stats flood-frequency --input-file q_daily.csv --value-column Q --date-column date \
    --distribution all --return-periods 10,50,100
hydrolog stats low-flow --input-file q_daily.csv --value-column Q --date-column date
hydrolog stats characteristic --input-file q_daily.csv --value-column Q --date-column date
hydrolog stats monthly --input-file q_daily.csv --value-column Q --date-column date
```

Annual maxima and minima (`stats flood-frequency`, `stats low-flow`) are taken from **complete** hydrological years (Nov-Oct; a value for every day of the year): an export covering calendar years loses the first and last hydrological year, and the skipped years are listed in the `incomplete_years` notice and the `incomplete_years` result field. A series shorter than recommended produces a warning in `notices`; a series without 3 complete years fails with `calculation_error`. The same commands are available in Python (`hydrolog.operations.stats_flood_frequency(input_file=..., value_column="Q", date_column="date")`) and over MCP (`hydrolog_stats_flood_frequency`).

### Flood routing: the hydrograph table between tools

The `route` commands (ADR-0007, ADR-0008) read and write one file format, the hydrograph table: a CSV (or a JSON object of two equal-length columns) with the columns `time_min` (minutes since any origin, strictly increasing at a regular step) and `discharge_m3s` (m3/s, not negative). Other names are given with `--time-column` and `--value-column`; an irregular step, a gap or a negative discharge is refused, nothing is resampled. A table from any source, for example a column of a hydraulic model or a design hydrograph written by another tool, is an input; the file that a `route` command writes with `--output` has the same two columns, so the outflow of one reach is the inflow of the next, or the discharge boundary condition of a hydraulic model:

```bash
hydrolog route lag --lag-min 30 --input-file inflow.csv --output outflow.csv
```

Hydrolog computes discharge only: water levels, inundation and backwater are hydraulics (Hydraulik, HEC-RAS, IMGW HD). Hydrolog writes no other tool's format. A hydrograph contract with Hydraulik and the export of a river network from Hydrograf need `request` issues in those repositories (DEV-17.5); this repository does not make them.

### Hydrograf: migrating HSG from Kartograf to Hydrolog

Until now the hydrologic soil groups were computed by Kartograf (`HSGCalculator`, `calculate_hsg`; in Hydrograf: `backend/core/cn_calculator.py` and `scripts/bootstrap.py`). Since Hydrolog 1.0.0, HSG calculation belongs to Hydrolog (module `hydrolog.soil`; the rules and the texture → HSG mapping were moved from Kartograf 0.8.0, ADR-025), and Kartograf is left with raster download only (`download_soil`). Hydrolog does not depend on Kartograf (the former `hydrolog[spatial]` extra was removed).

Existing path in Hydrograf:

```python
from kartograf.hydrology import HSGCalculator

hsg_calc = HSGCalculator()
hsg_calc.calculate_hsg_by_bbox(bbox, hsg_path)      # download + HSG calculation
hsg_stats = hsg_calc.get_hsg_statistics(hsg_path)   # group shares
```

Target path (Kartograf `download_soil` → Hydrolog `hsg_from_rasters` → `hsg_statistics` → weighted CN):

```python
from kartograf import BBox, download_soil
from hydrolog.runoff import calculate_weighted_cn, get_cn
from hydrolog.soil import hsg_from_rasters, hsg_statistics   # requires hydrolog[raster]

bbox = BBox(626000, 480000, 628000, 482000, "EPSG:2180")

# 1. Kartograf: three SoilGrids rasters (g/kg) - clay, sand, silt (same layer, depth and statistic).
#    output_dir writes plain files into the directory (a versioned store would use root=...).
paths = {}
for prop in ("clay", "sand", "silt"):
    report = download_soil(
        output_dir="/data/kartograf", bbox=bbox,
        property=prop, depth="0-5cm", stat="mean",
    )
    paths[prop] = report.files[0].path   # files[]: {path, size_bytes, sha256, status}

# 2. Hydrolog: HSG raster (uint8 GeoTIFF: 0 - no data, 1-4 are A-D)
hsg_from_rasters(paths["clay"], paths["sand"], paths["silt"], output_path="/data/hydrolog/hsg.tif")

# 3. Hydrolog: areas of groups A-D (optionally only a rectangle: bbox=..., bbox_crs=...)
stats = hsg_statistics("/data/hydrolog/hsg.tif")

# 4. Area-weighted CN: a part is a (CN, area) pair; CN from the TR-55 tables for the watershed land cover
parts = [
    (get_cn(group, "meadow", "good"), group_stats.area_ha)
    for group, group_stats in stats.groups.items()
    if group_stats.area_ha > 0
]
cn = calculate_weighted_cn(parts)
```

- The clay, sand and silt rasters must share the same coordinate reference system, grid and size (otherwise `InputDataError`, code `data_error`); units are arbitrary but must be consistent.
- The equivalent Kartograf CLI call is `kartograf soil download ... --output-dir DIR` (plain files); `--root` would select a versioned store instead, which Hydrolog does not read directly.
- The same path in the CLI: `hydrolog soil hsg --clay-path ... --sand-path ... --silt-path ... --output hsg.tif`, `hydrolog soil hsg-stats --hsg-path hsg.tif`, `hydrolog cn weighted --parts '[{"cn": 30, "area": 75.0}, ...]'`.
- HSG is only one of the two CN factors: with several land covers the parts are (HSG × cover) pairs, and the intersection of the HSG and land-cover rasters is done by Hydrograf (Hydrolog does not do it).
- Removing HSG from Kartograf and rewiring Hydrograf (`get_hsg_from_soilgrids`, `bootstrap.py`) are separate changes in those repositories; until they are done, Hydrograf (pinned to v0.6.3) works with the old path.

---

## Change list

### Hydrolog (this session)

| File | Change | Status |
|------|--------|--------|
| `hydrolog/morphometry/watershed_params.py` | NEW - WatershedParameters | ✅ |
| `hydrolog/morphometry/geometric.py` | + `from_dict()` | ✅ |
| `hydrolog/morphometry/terrain.py` | + `from_dict()` | ✅ |
| `hydrolog/morphometry/__init__.py` | Export WatershedParameters | ✅ |
| `tests/unit/test_watershed_params.py` | NEW - unit tests | ✅ |
| `tests/integration/test_hydrograf_integration.py` | NEW - integration tests | ✅ |

### Hydrograf (at CP3)

| File | Change | Status |
|------|--------|--------|
| `backend/core/morphometry.py` | NEW - calculation functions | 🔲 |
| `backend/models/schemas.py` | + MorphometricParameters | 🔲 |
| `backend/api/endpoints/watershed.py` | Return morphometry | 🔲 |
| `backend/requirements.txt` | + hydrolog | 🔲 |

---

## Integration status (2026-10-19)

### Hydrolog - READY

| Component | Status | Notes |
|-----------|--------|-------|
| WatershedParameters | ✅ | from_dict(), to_json(), calculate_tc() — w tym pola v0.6.3+ |
| WatershedGeometry.from_dict() | ✅ | Shape indices |
| TerrainAnalysis.from_dict() | ✅ | Terrain parameters |
| HydrographGenerator | ✅ | SCS bug fixed in v0.5.1 (constant 0.208) |
| Unit tests | ✅ | 35 tests |
| Integration tests | ✅ | 15 tests |
| Operations layer, command catalog, CLI, MCP (v1.0.0) | ✅ | 44 commands; `hydrolog.operations`, `hydrolog mcp` |
| `routing` module (after v1.0.0, ADR-0007) | 🔄 | `Hydrograph`, `Reach`, `LagReach`, `MuskingumReach`, `MuskingumCungeReach`, `CascadeReach`, `LevelPoolReach`, `RoutingNetwork`, `route lag`, `route muskingum`, `route muskingum-cunge`, `route cascade`, `route level-pool`, `route network`; complete on `feature/routing-network`, waiting for the author's merge |
| `soil` module (HSG, v1.0.0) | ✅ | `hsg_from_rasters`, `hsg_statistics`, `soil *` commands |
| Result serialization (v1.0.0) | ✅ | `to_dict()`/`to_json()` in all result classes |

**Fixed:** Bug in `SCSUnitHydrograph.peak_discharge()` — constant 2.08 → 0.208 (fixed in v0.5.1).

### Hydrograf - TO BE IMPLEMENTED

| Component | Status | Notes |
|-----------|--------|-------|
| MorphometricParameters schema | 🔲 | Pydantic model |
| build_morphometric_params() | 🔲 | Calculation function |
| API endpoint /morphometry | 🔲 | API extension |
| Hydrolog integration | 🔲 | pip install hydrolog; migracja HSG: section "Hydrograf: migrating HSG from Kartograf to Hydrolog" |

### Tested scenarios

1. ✅ JSON → WatershedParameters (API simulation)
2. ✅ Batch processing of multiple watersheds
3. ✅ Validation of invalid data
4. ✅ Round-trip serialization (from_json → to_json → from_json)
5. ✅ Full workflow with HydrographGenerator (SCS bug fixed in v0.5.1)
6. ✅ Test on real DEM data (sheet N-33-131-D-a-3-1)

---

## Context for future sessions

### If you are working on Hydrolog:
1. Read this file (`docs/INTEGRATION.md`)
2. Check the "Change list" table above
3. Continue from the first unfinished task

### If you are working on Hydrograf:
1. Read `docs/HYDROGRAF_INTEGRATION.md` (the same file copied there)
2. Check the "Implementation in Hydrograf" section
3. Add Hydrolog as a dependency before implementing

### Key files:
- **Data format:** JSON Schema in the "Data exchange format" section
- **Hydrolog entry point:** `hydrolog.morphometry.WatershedParameters`
- **Hydrograf entry point:** `backend.core.morphometry.build_morphometric_params()`

---

**Last updated:** 2026-10-24
