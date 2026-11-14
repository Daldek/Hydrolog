# Hydrograf ↔ Hydrolog integration

**Created:** 2026-01-20
**Last updated:** 2026-11-02 (the web GUI: hosting it in Nogat's GUI platform, the hand-off with Hydrograf)
**Status:** In progress (Hydrolog - ready; Hydrograf - to be implemented)

---

## Purpose

Enable easy data exchange between Hydrograf (GIS spatial analysis) and Hydrolog (hydrological calculations), with the option to integrate other systems: the Retman agent platform, MCP clients (e.g. Claude Code), Nogat's GUI platform, which hosts Hydrolog's web GUI, and the Obserwator and Kartograf tools, which supply input data. Hydrolog downloads nothing and does not depend on any of these tools - data is exchanged through files (JSON, CSV, GeoTIFF) - with one exception: `precip pmaxtp` fetches the PMAXTP depth of a point from IMGW-PIB through Obserwator, an optional dependency (extra `pmaxtp`, [ADR-0018](decisions/0018-pmaxtp-through-obserwator.md); see "Obserwator: the PMAXTP depth" below). Hydrolog is a consumer that needs plain files, so it reads the output of Kartograf and Obserwator written in plain-file mode (`--output-dir`, `output_dir=`), not from a versioned store.

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
  "required": ["area_km2"],
  "properties": {
    "name": {"type": "string", "description": "Watershed name"},
    "area_km2": {"type": "number", "minimum": 0, "description": "Area [km²]"},
    "perimeter_km": {"type": "number", "minimum": 0, "description": "Perimeter [km]"},
    "length_km": {"type": "number", "minimum": 0, "description": "Watershed length [km]"},
    "elevation_min_m": {"type": "number", "description": "Minimum elevation [m a.s.l.]"},
    "elevation_max_m": {"type": "number", "description": "Maximum elevation [m a.s.l.]"},
    "elevation_mean_m": {"type": "number", "description": "Mean elevation [m a.s.l.]"},
    "mean_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Mean land slope of the watershed [m/m] (NRCS: Y)"},
    "channel_length_km": {"type": "number", "minimum": 0, "description": "Main channel length [km] (Giandotti)"},
    "channel_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Main channel slope [m/m]"},
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
    "forest_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "Percentage of forested area [%] (Nash)"},

    "__comment_v100": "Optional fields added in v1.0.0 (ADR-0019)",
    "flow_path_length_km": {"type": "number", "exclusiveMinimum": 0, "description": "Length of the longest flow path, from the hydraulically most distant point of the watershed (usually on the divide, possibly on a ridge inside the watershed) to the outlet [km] (Kirpich, NRCS, Kerby-Kirpich)"},
    "flow_path_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Slope of the longest flow path: (elevation of its head - outlet elevation) / its length [m/m] (Kirpich, Kerby-Kirpich)"}
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

# Calculations (Kirpich takes flow_path_length_km and flow_path_slope_m_per_m)
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
    flow_path_length_km: float | None = None       # hydraulic_length_km
    flow_path_slope_m_per_m: float | None = None   # (head - outlet) / length
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

# 4. Compute the time of concentration (Kirpich: the longest flow path,
#    flow_path_length_km and flow_path_slope_m_per_m, ADR-0019)
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
- A `rating_file` named by the document lies beside `network_file`; an inline network (MCP) cannot name files. The document must carry `"schema": "hydrolog-network/1"`, and an `id` must not be a Windows device name (`con`, `nul`, `aux`, `prn`, `com1` to `com9`, `lpt1` to `lpt9`), because it names the file `<id>.csv`.
- **Positions and descriptions** ([ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md)): every node may have `description` (plain text for people, 1 to 500 characters, not blank, no control character but the line feed, never read as HTML or Markdown) and `position` (`{"x": ..., "y": ...}`, whole numbers from −1000 to 1000, the cell of the node in the grid of the schematic: `x` grows downstream, `y` sideways), and the document a `description` at its top. Both are optional, change no computation and keep the version `/1`; the canonical form writes them after the fields of the node's kind, `description` then `position`, and a document without them is written as before. The reader stays strict, so a Hydrolog from before these fields refuses a document that has them (`unknown_field`); every older document reads as before. Hydrograf's `/1` documents without them are unaffected; Retman recognises the file by its exact `schema`, which does not change. `hydrolog.testing.placed(node, description=..., position=(x, y))` and `network_document(..., description=...)` build them.
- **Nash's n and K from the watershed** ([ADR-0024](decisions/0024-nash-by-lutz-from-the-watershed.md)): the `curve-number` runoff of a subcatchment may say `"uh_model": "nash", "nash_estimation": "lutz"` instead of `nash_n` and `nash_k_min`; Hydrolog then estimates them by Lutz from the node's `watershed`: `flow_path_length_km` and `flow_path_slope_m_per_m` (Lutz's L and J, the main stream from the divide: Hydrograf's `hydraulic_length_km` and its slope, not the channel), `Lc_km`, `manning_n`, and `urban_pct` and `forest_pct` (0 when missing). A node without one of the four first fields is `missing_field` with `details.method` `lutz` and its `node_id`. The field is optional and keeps `/1`, but a Hydrolog from before it refuses it (`unknown_field`): a producer may write it only for a consumer that pins a Hydrolog that has it. `hydrograph generate --nash-estimation lutz` gives the node's hydrograph for the same watershed and rainfall.
- **Tests of a consumer:** `hydrolog.testing` builds the network documents (also of subcatchments that make their hydrograph: `watershed`, `curve_number_runoff`, `design_storm`, `rainfall_series`), the tables of `--output-dir`, a complete case (`build_network_fixture`), a network of three subcatchments (`example_network_document`, `example_network`) and the envelope of `precip hietogram` offline, with the real code ([ADR-0011](decisions/0011-public-testing-module.md), [ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)); test against it at the Hydrolog version you pin, not against hand-written copies of the formats (DEV-10.6).
- A network exporter in Hydrograf and a reader of the tables in Hydraulik are `request` issues in their repositories (DEV-17.5); this change opens none.

### Flood routing from Python: the control points of Hydrograf

When Hydrograf calls Hydrolog as a library there is no file: it builds the network pick by pick, in the order the user works, **the outlet first, then points upstream of it** ([ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md); `ControlPointNetwork` in `hydrolog.routing`; the worked workflow is in [USAGE.md](USAGE.md), "Networks of objects, rainfall per subcatchment, control points"). The network is valid, and routes, after every step.

| In Hydrograf | In Hydrolog |
|---|---|
| the outlet pick | `ControlPointNetwork(OutletPoint(id, subcatchment))` |
| a pick on a stream | `add_point(ControlPoint(id, subcatchment), downstream=<the pick or confluence below it>, channel=<Reach or Channel>)` |
| a pick between two picks | the same, with `upstream={<the pick above>: <its channel to the new pick>}` |
| a tributary that joins the stream between two picks | `add_confluence(id, on_channel_of=<the upper pick>, upstream_channel=, downstream_channel=)`, then `add_point(..., downstream=<confluence id>)` |
| the area that is left to a pick | `update_subcatchment(id, subcatchment)` |
| the user removes a pick | `remove_point(id)`, with `channel=` when Hydrograf gives the one channel that replaces the two |
| the discharge at a pick | `route().hydrographs[id]` |

- **Residual areas are Hydrograf's job.** A pick closes its contributing area minus the areas of the picks above it: when a pick is added, Hydrograf gives the pick below it the smaller area (`update_subcatchment`); when one is removed, it gives the area back. Hydrolog does not know areas and checks none, and it makes up no channel: Hydrograf chooses the `Reach` of every stream (the options of `route <method>`: `lag_min`; `k_min` and `x`; a section or a celerity from the length and the slope of the stream segment) and, at a confluence, both parts of the channel that is split. Hydrolog checks the topology (one outlet, no bifurcation, no cycle), the ids and the time axis.
- **The rainfall belongs to each subcatchment.** Hydrograf makes one `Subcatchment(id, watershed=WatershedParameters.from_dict(...), runoff=CurveNumberRunoff(...), rainfall=<source>)` per pick, with the watershed that its morphometry produces. Two picks of one network can have rain from different sources: a design storm (`DesignStorm`: a depth, a duration and a hietogram shape), a record (`RainfallSeries`) or, later, any class that implements `RainfallSource` (areal rainfall from Obserwator, radar, PMAXTP) and is registered in `RAINFALL_KINDS` to be named in a document. `ControlPointNetwork(..., rainfall=)` is only a default for the subcatchments that have none. The network has one time step (`timestep_min=`, else that of the records, else 5 min); a record of another step is refused (`timestep_mismatch`), nothing is resampled.
- **An edit that is refused changes nothing.** It raises `InvalidParameterError` with `details.reason` (`unknown_point`, `duplicate_node`, `no_inflow`, `not_upstream`, `outlet_removal`, `timestep_mismatch`, `missing_field`...) and the id in `details`: Hydrograf shows the message and keeps its own state.
- **Ids.** The ids of the picks, the confluences, the subcatchments and the channels are node ids: letters, digits, `_`, `.` and `-`, at most 64 characters, unique without regard to case. A bare `Reach` is wrapped in a channel named `<id>_channel` after the pick it leaves.
- **What comes back.** `hydrographs[id]` of the result is the discharge at the pick (`times_min`, `discharge_m3s`, peak, time to peak, volume); `nodes[id]` has for every pick, confluence, subcatchment and channel the peak, the time to peak, the volume, the `parameters` that the calculation used (`name`, `value`, `unit`, `source`: `given`, `computed` or `default`) and the `notices`; `rainfall[subcatchment_id]` the rain that was used; `runs[channel_id]` the run of a channel. `kind(id)`, `downstream(id)`, `upstream(id)`, `channels(id)` and `subcatchment(id)` give the structure for a schematic of the network. The state of the picks is Hydrograf's; `points.network().to_document()` is the `hydrolog-network/1` document of the state if a file is wanted (`route network` and `RoutingNetwork.from_document` read it).

```python
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import EulerIIHietogram
from hydrolog.routing import (
    ControlPoint, ControlPointNetwork, CurveNumberRunoff, DesignStorm,
    MuskingumReach, OutletPoint, RainfallSeries, Subcatchment,
)


def residual(point_id, watershed, rain):
    """The residual area of a pick: the watershed dict is Hydrograf's, the rain is its own."""
    return Subcatchment(
        f"{point_id}_area",
        watershed=WatershedParameters.from_dict(watershed),
        runoff=CurveNumberRunoff(tc_method="kirpich"),
        rainfall=rain,
    )


design = DesignStorm(45.0, 60.0, EulerIIHietogram())
record = RainfallSeries([0.0, 2.0, 5.0, 10.0, 12.0, 6.0, 3.0], timestep_min=5.0)
whole = {"area_km2": 30.0, "perimeter_km": 25.0, "length_km": 8.0,
         "elevation_min_m": 210.0, "elevation_max_m": 330.0, "cn": 75,
         "flow_path_length_km": 8.0, "flow_path_slope_m_per_m": 0.015}

points = ControlPointNetwork(OutletPoint("OUT", residual("OUT", whole, design)))   # 1. the outlet
points.add_point(                                                                   # 2. a pick above it
    ControlPoint("P1", residual("P1", {**whole, "area_km2": 18.0}, record)),
    downstream="OUT",
    channel=MuskingumReach(k_min=40.0, x=0.2),
)
points.update_subcatchment("OUT", residual("OUT", {**whole, "area_km2": 12.0}, design))   # 30 - 18
result = points.route()
print(result.hydrographs["P1"].peak_discharge_m3s, result.hydrographs["OUT"].peak_discharge_m3s)
```

### Drawing the network: the schematic for an application

Hydrolog computes the picture of a network once, so that the screen of Hydrograf, a report and `route network --schematic` show the same one ([ADR-0013](decisions/0013-network-schematic.md); JSON Schema `src/hydrolog/schemas/hydrolog-network-schematic-1.schema.json`; the picture of the USAGE example is `docs/images/network-schematic.svg`). An application does not lay the network out: it asks for the document and draws it.

- **Ask.** `RoutingNetwork.schematic(result=None, main_stem=None)` returns the document, JSON-native (`points.network().schematic(points.route())` for control points). Without `main_stem` the stem follows from the outlet the branch with the larger drained area (the areas of the subcatchments that make their hydrograph; a headwater that is given its hydrograph has none, and then the branch with more nodes) and the smaller id on a tie. Hydrograf knows the main river and Hydrolog does not: `main_stem="P2"` (the head of the river) or the ids of points along it (they must lie on one path to the outlet, `unknown_node` and `main_stem_not_a_path` otherwise). Over files or MCP: `route network ... --schematic FILE [--main-stem ID,...] --json` writes the SVG and returns the document as `result.schematic`.
- **Places.** `nodes[].x` and `nodes[].y` are integers in grid units, `x` growing downstream (to the right) and `y` downwards, as on a screen; multiply both by one scale (the lines at 45 degrees stay at 45 degrees). `grid.width` and `grid.height` are the extent of the nodes: leave about one unit around them for the labels.
- **Lines.** `edges[].points` are the corners of the polyline from `from` to `to`; draw it with round joins. `line` groups the edges and the nodes (`lines[]`: index 0 is the main stem, a tributary names the node it flows into, `joins`): colour by line, and draw the lines with the larger index first so that the main stem is on top where a line merges into it (a node with more than two inflows takes its lines at taps and they share their last stretch).
- **Nodes and labels.** A symbol by `type` (`subcatchment`, `reach`, `reservoir`, `junction`, `outlet`; a kind that was added is a plain circle until you know it). `label.text` and `label.side` (a compass point on the screen around the node: `n` above it, centred; `ne` above it, starting at the node; `e` to its right...): the layout leaves every label one unit wide and four tenths of a unit high on that side, clear of the lines.
- **Values.** With a result each node has `peak_m3s`, `time_to_peak_min`, `volume_m3` (the numbers of `NetworkResult.nodes`), `parameters` (`name`, `value`, `unit`, `source`: `given`, `computed` or `default`) and `notices` (`level`, `code`, `message`; a warning deserves a mark). Without one `has_result` is false and `parameters` are what is given. The layout is the same either way, and the same whatever the order of the nodes in the network document.
- **Given positions** ([ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md)). When every node of the network document has a `position` and no two share a cell, the picture is the **given** layout: the nodes stay on their cells, moved together so that the smallest `x` and `y` are 0, the lines and labels are chosen as in the computed layout, and every edge follows rule D from the positions of its two nodes (straight when they share a row or a column; downstream, a sideways leg, one 45 degree step and the row of the lower node; upstream, a 45 degree leg, then straight). A given picture may cross itself or run an edge through a node. `layout` at the top of the schematic says `given` or `computed` (a document without it is computed). Positions on some nodes only (`partial`) or two nodes on one cell (`shared_cell`) give the computed layout and the warning `positions_ignored` (`details.reason`, `node_id`), a Python warning of `schematic()` and a notice of `route network --schematic` and `route schematic`. A node that has a `description` carries it in the schematic, after `label`; the network's own description is not in the schematic. To keep ADR-0013's picture and let a person move nodes from it, store the computed `x` and `y` as the positions: rule D draws the computed edges exactly.
- **The structure alone** ([ADR-0025](decisions/0025-the-structure-alone-in-the-schematic.md)). A draft whose nodes still miss values (a network delineated by Hydrograf before its reaches have Manning's n and a width, a network being drawn) is laid out by `hydrolog.routing.structure_schematic(document, main_stem=None)` or `route schematic --structure-only` (`structure_only: true` over MCP): only `schema`, `name`, `timestep_min`, each node's `id`, `type` and `from` and each headwater's `watershed.area_km2` are read, the structure is checked with the reasons and details of the full reader, and every other field may be missing or wrong. The picture is the computed layout (positions are ignored); for a document that makes a network it is that network's computed picture. Its document has `structure_only` `true`, every node's `parameters` empty, no `description`, and `timestep_min` only when the document gives it: a reader of the schematic that needs the step reads it only from a schematic without `structure_only`. No file the document names is read (`inflows_file` and `time_column` with it are `conflict`).
- **SVG.** `hydrolog.routing.schematic.schematic_svg(document)` draws a document with the standard library, from the document alone (text in ids, symbols and units; ids longer than 16 characters are wrapped; a node's `description` in its tooltip, on the line after `id (type)`, escaped); `route network --schematic` writes it. The schematic keeps its version `/1` when it gains optional fields (AGI-4.1): `layout`, the given layout and a node's `description` came that way ([ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md)), and so did `structure_only` with a `timestep_min` that only its schematic may leave out ([ADR-0025](decisions/0025-the-structure-alone-in-the-schematic.md), the schematic being unreleased), and a reader of `/1` draws a given layout from its `x`, `y` and `points` as it draws a computed one. A change of the computed layout or of the meaning of a field is a change of a documented format and goes with a new version of the schema.

```python
schematic = points.network().schematic(points.route(), main_stem="P2")
for edge in schematic["edges"]:
    draw_polyline([(x * SCALE, y * SCALE) for x, y in edge["points"]], colour(edge["line"]))
for node in schematic["nodes"]:
    draw_symbol(node["type"], node["x"] * SCALE, node["y"] * SCALE)
    draw_label(node["label"]["text"], node["label"]["side"], node.get("peak_m3s"))
```

### Retman (calculation handlers)

Retman calls Hydrolog through the command layer, not through the library classes.

- **Operations layer:** `hydrolog.operations` - one public, typed function per command (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...), arguments named like the command options, NumPy-style docstrings (used by `retman-scaffold`). The function returns a result object with `to_dict()`/`to_json()`, or an `OperationOutput` (`result`, `notices`, `files`) when the command has warnings or writes files.
- **Catalog and envelope:** `hydrolog.catalog.run_command("<group> <command>", {options})` (also `hydrolog.run_command`) validates the options, runs the operation and returns a `hydrolog-result/1` envelope (`schema`, `tool`, `version`, `command`, `check`, `status`, `result`, `notices`, `inputs`; the files written are in `result.files[]` with SHA-256; `to_dict()`, `to_json()`). Option schema (JSON Schema): `command_schema()`, `hydrolog commands schema`. Errors are `HydrologError` exceptions with `code`, `hint` and `details` (registry `ERROR_CODES`; document `hydrolog-error/1`).
- **`catchment_characteristics`:** the proposed format is `WatershedParameters` JSON (`WatershedParameters.to_json()`; only `area_km2` is required, a command that needs a missing field names it in `details.option` with `details.reason` `missing_field`). The file is passed to commands as `watershed_file`, and `WatershedParameters.from_dict()` ignores the extra `schema` key (e.g. `"hydrolog-catchment/1"`) added by the catalog tools.
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

### Web GUI: a module of Nogat's GUI platform

The web GUI (`hydrolog gui serve`, extra `gui`; [USAGE.md](USAGE.md#8-the-web-gui), plan `docs/plans/2026-11-02-hydrolog-gui.md`, D4 and D5) runs alone or as a module that another application hosts, which is how Nogat's GUI platform will show it.

- **Discovery.** The entry point group `nogat.gui` names it: `hydrolog = "hydrolog.gui:gui_module"`. `gui_module()` returns a frozen `GuiModule`: `name` (`"hydrolog"`), `title` (`"Hydrolog"`), `web` (the directory of the page's static files), `index` (`"index.html"`), `sections` (pairs of the address fragment and the Polish title: `hydrogram` „Hydrogram zlewni”, `siec` „Sieć i trasowanie”, `statystyka` „Statystyka przepływów”, `kalkulatory` „Kalkulatory”, `polecenia` „Wszystkie polecenia”; `#siec` opens a section) and `app` (`hydrolog.gui.create_app`). The shape is a proposal to Nogat's platform plan.
- **Mounting.** `app(work_root=..., data_dir=...)` returns an ASGI (Starlette) app that serves the page at its root and its API under `api/`, relative to the page, so the host mounts it at any prefix of its own origin. Its lifespan starts the two worker processes and ends them and the session directories; a host that does not run the lifespan of a mounted app gets the workers at the first run. `data_dir` (default: the setting `data_dir`) holds the reports of „Zgłoś uwagę”, `<data_dir>/hydrolog/feedback.sqlite3`. Alternatively a host serves `web/` itself and answers the same routes from its own bridge to a catalog: they are generic over any `hydrolog-commands/1` catalog.
- **Logs.** A mounted app writes no access log of its own: the host keeps one, outermost (Nogat DEV-12.8). `app(..., log=ServerLog(...))` (`hydrolog.gui.nogat_logging`, Nogat's reference module copied unchanged) adds `AccessLog` as the app's outermost middleware with Hydrolog's static paths (`hydrolog.gui._app.QUIET`, paths at the root of the origin); `hydrolog gui serve` does that and starts and stops the log ([USAGE.md](USAGE.md#logs)).
- **The routes are private.** `GET api/session`, `GET api/commands`, `GET api/commands/{group}/{verb}`, `GET api/schemas/{file}`, `POST api/run/{group}/{verb}?channel=...`, `POST api/format/{group}/{verb}`, `PUT api/files/in/{name}`, `GET` and `DELETE api/files/{in|out}/{name}` and `POST api/feedback` (a report of „Zgłoś uwagę”) serve this page only: not a REST interface of Hydrolog, with no version and no stability promise (agents use the CLI, MCP and Python). A run answers `hydrolog-result/1` or `hydrolog-error/1` with the registry's HTTP status; paths in answers are relative to the session (`in/x.csv`). The admin routes, `GET api/admin/feedback`, `PATCH` and `DELETE api/admin/feedback/{id}`, `GET api/admin/stats` and `GET api/admin/status`, are Nogat's core admin API (DEV-15.13), with the key of `HYDROLOG_ADMIN_API_KEY` or `HYDROLOG_ADMIN_API_KEY_FILE` in `X-Admin-Key` ([USAGE.md](USAGE.md#reports-of-users-zgłoś-uwagę)).
- **Embedded.** `?nogat=1` in the page's address hides Hydrolog's top bar and rail before the first paint, and with them „Zgłoś uwagę”, „Instrukcja” and the welcome dialog: the host's own chrome takes their place. The theme is the `localStorage` key `nogat-theme` (`auto`, `light`, `dark`), shared by the pages of one origin. The handshake with the host (`postMessage`), the host's theme and a hand-off through the host wait for the platform's kit, which replaces `web/src/host.js`.
- **Its guide and admin panel.** The user guide is `instrukcja/` relative to the page (static HTML in Polish); a host may link it. The admin panel, Nogat's kit shell with the reports, the daily totals and the server's status, is `admin/` (`admin` answers `308` to it).
- **The app menu.** „Aplikacje” in the top bar, left of the theme switch, is Nogat's `<nogat-app-menu>` (DEV-15.4, [ADR-0027](decisions/0027-nogats-gui-kit-the-app-menu-and-the-handoff.md)): the GUIs of the deployment's table `gui` of `[nogat]` in `nogat.toml` (`NOGAT_CONFIG` or the user configuration directory), e.g. `gui = { hydrolog = "https://hydrolog.example/", hydrograf = "http://127.0.0.1:8080/", archiwista = "/archiwista/" }`, one key per registry name in lower case, an address absolute or a path on the page's origin. `GET api/session` gives the table as `gui` (`null` without it), read at every request, and the page hands it to the element. An entry opens its GUI in the tab `nogat-<name>`; without another GUI in the table, or inside a host (`?nogat=1` hides the top bar), the menu is not drawn. Nogat's GUI kit lives in `web/nogat/` beside the tokens and marks, copied byte for byte (DEV-15.6): `nogat-app-menu.js`, `nogat-app-menu.css`, `nogat-handoff.js` and their manifest `nogat-kit.json`.

```python
import contextlib
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount

from hydrolog.gui import gui_module

module = gui_module()
gui = module.app(work_root=Path("/var/lib/nogat/hydrolog-gui"))


@contextlib.asynccontextmanager
async def lifespan(app):
    async with gui.router.lifespan_context(gui):  # the workers and the sessions
        yield


host = Starlette(routes=[Mount("/m/hydrolog", app=gui)], lifespan=lifespan)
```

Mounted like this, the page is `/m/hydrolog/` and its API `/m/hydrolog/api/...`; the browser tests of the GUI (`tests/e2e/conftest.py`) run it the same way.

### Web GUI: the hand-off with Hydrograf (`nogat-handoff/1`)

The GUI and Hydrograf exchange a watershed or a network as the envelope `nogat-handoff/1`, which Nogat publishes (`schemas/exchange/handoff-1.schema.json`, unchanged since Nogat `8848c26`) and Hydrolog never defines; Hydrolog keeps an unchanged copy in `schemas/nogat/handoff-1.schema.json` (its SHA-256 in `schemas/nogat/README.md`). The file, the clipboard and the envelope's check are Nogat's kit, `web/nogat/nogat-handoff.js` (DEV-15.5, [ADR-0027](decisions/0027-nogats-gui-kit-the-app-menu-and-the-handoff.md)), the same in every GUI of the ecosystem. The `payload` is `hydrolog-network/1`, whose nodes may have the optional `description` and `position` and whose top may have a `description` ([ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md)). Sieć keeps them: a network opened from a file or a hand-off keeps its positions and descriptions, and the hand-off written from Sieć carries the document as it is, so a reader of such a payload needs a Hydrolog that knows them (an older one refuses them as `unknown_field`). Hydrograf's hand-offs, written without them, are unaffected and open in Hydrolog's computed layout.

- **Writing.** „Przekazanie” at the end of the panel Wyniki: „Plik przekazania” downloads `<subject>.handoff.json` (the kit's name rule: `\/:*?"<>|` and control characters become `-`, runs of white space one space, an empty subject `hydrolog`; 2-space JSON with a final newline) and „Kopiuj do Hydrologa” copies the same text; where the browser gives no clipboard (a plain-HTTP address other than localhost) or refuses it, the text goes selected into a field below the buttons for Ctrl+C. From Hydrogram zlewni it carries one `subcatchment` made from the shown run (its watershed, `runoff` and `rainfall`) and the `outlet`; from Sieć the whole network, with the outlet's result once „Oblicz sieć” has computed the network as it is. `producer` is `{"tool": "hydrolog", "version": ..., "page": "#hydrogram"}` (or `"#siec"`), and `result` holds `command` (`hydrograph generate` or `route network`), `peak_discharge_m3s`, `time_to_peak_min` and `total_volume_m3`.
- **Provenance.** In Hydrogram zlewni `rainfall` is `{"source": "pmaxtp", "probability_percent": ..., "duration_min": ..., "latitude": ..., "longitude": ..., "method": ...}`, the point, probability, duration and method the depth was fetched for by `precip pmaxtp` ([ADR-0018](decisions/0018-pmaxtp-through-obserwator.md)), or `{"source": "user"}`; `watershed` is `{"source": "file", "file": ...}`, `{"source": "user"}` or the received hand-off's own entry, with `changed` listing the fields edited since, if any; Nash by Lutz is no longer written as numbers with a `runoff` entry of `uh nash`: the node's runoff says `nash_estimation` `lutz` ([ADR-0024](decisions/0024-nash-by-lutz-from-the-watershed.md)), and its reader estimates n and K again from the watershed it receives; a hand-off written before, with n and K and `runoff` `{"source": "hydrolog", "command": "uh nash", "method": "lutz"}`, opens with that n and K given. Sieć names its network's file (`network`) or keeps a received hand-off's provenance; once the network's rainfall differs from the one it opened with, `rainfall` is that rainfall's by the rule above. Unchanged data written again keep the received entries, latitude and longitude included. Hydrogram zlewni offers a hand-off only for a full watershed (`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`), although its runs need only the fields the chosen model reads; its `watershed` holds the fields of step 1 and those the chosen model and tc method read.
- **Reading.** „Wczytaj z Hydrografa” in the first step of Hydrogram zlewni and of Sieć reads a hand-off file or the clipboard, with a field to paste into where the browser gives no clipboard. The kit parses it and checks the envelope against the validation keywords of Nogat's schema (`web/src/handoff/envelope.js`, a copy without the annotations, which a browser test compares with the schema; copy it again when Nogat changes the schema); Hydrolog checks the payload against `hydrolog-network-1.schema.json` with its own `web/src/handoff/validate.js`, which reads `\w` of a pattern as Python does (a node id `Ś1`) and names the problem inside the branch of a `oneOf` the node's `type` chooses, where the kit's check reads `\w` as ASCII and names only the `oneOf`. A refused hand-off lists its problems in Polish, in the kit's words, with their paths and changes nothing. Exactly one subcatchment with the outlet below it opens in Hydrogram zlewni, which refuses it with a rainfall series whose step is not the network's; any other network opens in Sieć. Read in Sieć, every network hand-off opens there, one subcatchment with its outlet too. With a network open, „Dodaj zlewnię z Hydrografa” in Sieć adds the hand-off's subcatchments to it, unconnected and in free cells right of the top row: an id the network has takes its stem with the first free number (`Z1` becomes `Z2`), the hand-off's outlet and its other nodes stay out, a node without a description takes the subject, the network keeps its `timestep_min`, and a rainfall at the hand-off's top becomes the node's own when the network's differs; the hand-off's origins go with each node (below). PMAXTP provenance (its probability and duration in the atlas, the duration the payload's) takes its point from `provenance.rainfall`, else from `provenance.watershed` (the outlet that Hydrograf names). The payload's depth is remembered without a fetch only when `provenance.rainfall` carries the point; with a point only in the watershed's provenance, Hydrogram zlewni fetches the depth for it; with no point at all the rainfall opens as a design hyetograph („Hietogram”) of the payload's depth and duration. A subcatchment without rainfall on the node or the network (Hydrograf's watershed alone, handed off before it has a hydrograph) opens with PMAXTP at the point of `provenance.watershed`, p, the duration and the unit hydrograph left to choose (an empty step 2 without a point); the depth is fetched once p and the duration are chosen.
- **The origin of each node** (`node_provenance`, Nogat's plan `2026-11-10-node-provenance-in-handoff`; plan [2026-11-10-network-wizard](plans/2026-11-10-network-wizard.md), D9). Read in Sieć, the origin of input *i* (`watershed`, `runoff`, `rainfall` of a subcatchment, `node` of any node) of node *n* is `node_provenance[n][i]`, else `provenance[i]`; a key that names no node of the payload, matched exactly, is left out and the load's note names it, and the network still opens. Each node keeps its origins and they follow it through a rename and through „Dodaj zlewnię z Hydrografa” under a free id. A subcatchment's panel shows its watershed's origin in step 1 with the fields changed since, and the received origins of its rainfall in step 2 and of its runoff in step 3; a reach, a junction or the outlet shows its `node` origin in „Dane”'s step 3, and a node without one the hand-off's. Hydrograf's origin parameters (its plan `2026-11-10-network-delineation`, D14) are shown in words: `element` (`headwater`, `tributary`, `intermediate`; `reach`; `confluence`, `point`, `outlet`), `point`, `reach`, `at_mouth`, the place (`latitude`, `longitude`), and of a reach `length` (`flow_distance`), `slope` (`nmt`, `minimum`), `upstream_elevation_m`, `downstream_elevation_m`, `vector_length_km` and `vector_source` (`bdot10k`); other keys pass through unshown. Sieć's hand-off writes `node_provenance` under the nodes' current ids, an entry only where `provenance` would not give the node's origin: the received entries while their inputs are unchanged, a watershed or a node's own fields edited since with `changed` (the keys of the fields that differ, after those the entry named), an edited runoff and an own rainfall typed by the person as `{"source": "user"}` (an own PMAXTP rainfall as its record), every origin of a node added or filled from a single-watershed hand-off (that hand-off's `provenance`), and for a node made in Sieć `{"source": "user"}` where `provenance` would claim its input. A subcatchment that takes the network's rainfall writes no rainfall of its own once that rainfall changed. Hydrogram zlewni reads its one subcatchment with `provenance` only.
- **Comparing.** The producer's result is shown beside Hydrolog's own with both versions (`result.computed_with` when another tool computed it, as Hydrograf does with Hydrolog 0.6.3, else `producer`), each differing value marked; once the data differ from those handed over, a note says that the producer's result is of the data handed over.

Field names are Hydrolog's (`channel_length_km`, `flow_path_length_km`; slopes in m/m); mapping Hydrograf's own names is Hydrograf's side (its `hydraulic_length_km` is `flow_path_length_km`, [ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md)). Hydrolog times a handed watershed by `runoff.tc_method` from the fields that method's source defines (Kirpich: `flow_path_length_km`, `flow_path_slope_m_per_m`; NRCS: `flow_path_length_km`, `mean_slope_m_per_m`, `cn`; Giandotti: `channel_length_km`, `elevation_mean_m`, `elevation_min_m`; FAA and Kerby: `overland_length_km`, `overland_slope_m_per_m`, `runoff_coeff` or `retardance`; Kerby-Kirpich: the overland fields, `retardance` and the flow path); a `runoff.tc_min` is a given value. Hydrograf writes the hand-off (`core/handoff.py`, from the release after its v0.5.0) with „Kopiuj do Hydrologa” (the clipboard) and „Plik przekazania” (a file) in its panel „Zlewnia”: the watershed alone after the delineation, then with the runoff, the rainfall and the result once it has a hydrograph; it does not read hand-offs. Values shown in Hydrolog's headers and notes are rounded (tc to 0,1 min), while the run uses those handed over. A hand-off through Nogat's shell, without a file or the clipboard, waits for the platform's kit.

### Web GUI: a station's series from Archiwista (`hydrolog-series/1`)

Archiwista hands a station's series to „Statystyka przepływów” in the same envelope ([ADR-0020](decisions/0020-a-stations-series-through-the-handoff.md)): „Kopiuj do Hydrologa” and „Plik przekazania” beside the chart of its station card, or `archiwista stations handoff CODE --variable Q [--resolution annual] > raba.handoff.json`. The payload is `hydrolog-series/1` (`hydrolog/schemas/hydrolog-series-1.schema.json`): the daily values of the variable (`step` `day`, `dates`, every day of the range with `null` where it has no value), or the annual maxima Archiwista finds in IMGW-PIB's half-year characteristics (`step` `year`, `statistic` `max`, `year_type` `hydrological`, `years`), only of complete years; `provenance.series` names the station, dataset and series version and, for annual maxima, the years left out.

„Wczytaj z Archiwisty” in the first step of Statystyka przepływów reads it from a file or the clipboard, checking the envelope against Nogat's schema and the payload against Hydrolog's. Annual maxima become the pasted values in the order of their years (missing years left out); daily values become the session's file `<subject>.csv` with the columns `date` and the variable, chosen as for a file of the person's, and `stats flood-frequency` takes the annual maxima of complete hydrological years from them. Annual minima are refused with the reason: low flows are `stats low-flow` in „Polecenia”. The section names where the series came from until it is changed.

### Obserwator: series export → `stats` commands

Hydrolog does not download IMGW series. Obserwator exports the daily series (`series export`) to a single CSV file with units in the header (`Q [m3/s]`), a `date` column, value flags and attribution. Export to a file uses `--output FILE` (for example `series export ... --output q_daily.csv`); the versioned-store root option is `--root` and defaults to the user data directory. The file is loaded without preprocessing (comma or semicolon separator, UTF-8; columns are given by name without the unit: `Q` finds `Q [m3/s]`):

```bash
hydrolog stats flood-frequency --input-file q_daily.csv --value-column Q --date-column date \
    --distribution all --return-periods 10,50,100
hydrolog stats low-flow --input-file q_daily.csv --value-column Q --date-column date
hydrolog stats characteristic --input-file q_daily.csv --value-column Q --date-column date
hydrolog stats monthly --input-file q_daily.csv --value-column Q --date-column date
```

Annual maxima and minima (`stats flood-frequency`, `stats low-flow`) are taken from **complete** hydrological years (Nov-Oct; a value for every day of the year): an export covering calendar years loses the first and last hydrological year, and the skipped years are listed in the `incomplete_years` notice and the `incomplete_years` result field. A series shorter than recommended produces a warning in `notices`; a series without 3 complete years fails with `calculation_error`. The same commands are available in Python (`hydrolog.operations.stats_flood_frequency(input_file=..., value_column="Q", date_column="date")`) and over MCP (`hydrolog_stats_flood_frequency`).

### Obserwator: the PMAXTP depth → `precip pmaxtp`

The one thing Hydrolog fetches is the PMAXTP depth of IMGW-PIB ([ADR-0018](decisions/0018-pmaxtp-through-obserwator.md)), and it fetches it through Obserwator's Python API, not by itself: with the extra `pmaxtp` (`obserwator>=3.0.0.dev0,<4`, until Obserwator is tagged the commit of Nogat's release set candidate-1), `precip pmaxtp` calls `obserwator.fetch_pmaxtp(latitude, longitude, method=..., timeout=20)`, which asks the PMAXTP API of IMGW-PIB over HTTPS for the table of the point, and reads the cell of the duration and the probability. Only the coordinates and the method go out; nothing is cached or written. The depth is the `total_mm` of a design storm:

```bash
hydrolog precip pmaxtp --latitude 51.01544 --longitude 15.88984 --duration-min 720 \
    --probability-percent 1 --method POT --json
hydrolog hydrograph generate --watershed-file kamiennik.json --tc-method kirpich \
    --hietogram-type beta --total-mm 101.82 --duration-min 720 --timestep-min 10
```

- A duration (5 min to 72 h, 16 values) or a probability (0.01 % to 99.9 %, 27 values) that the atlas lacks is a `validation_error` before anything is sent; a point outside Poland's box (latitude 49-55, longitude 14-24.5) too. A point inside the box but outside the atlas is `validation_error` on `latitude` with `details.reason` `outside_pmaxtp`; IMGW-PIB unreachable or too slow is `source_unavailable` (exit 5); an unreadable answer is `data_error`; without the extra, `missing_dependency`.
- The envelope's `attribution` (PMAXTP's PS, PP and monograph M) and `terms_notice` (RK, „Regulamin danych PMAXTP: https://klimat.imgw.pl/opady-maksymalne”) are the lines the terms of PMAXTP require on every product of the depth ([ADR-0028](decisions/0028-the-providers-lines-in-every-product.md), [ADR-0036](decisions/0036-link-the-providers-terms-instead-of-restating-them.md), Nogat DEV §20); `result.attribution` is the source line and the notice `pmaxtp_attribution` points to them. Pass them on with the depth as `--attribution '[...]'` of `precip hietogram`, `hydrograph generate`, `report generate` or `route network`, whose results and files then carry them; an Obserwator export's attribution columns and a hand-off's `attribution` and `terms_notice` travel the same way, and lines written before Nogat ECO-065 (H, N, „Regulamin: …”) are read as the current ones.
- IMGW-PIB may update the atlas, so a depth fetched later can differ; a hand-off records the point, probability, duration and method, not a date.
- Obserwator's own `pmaxtp` commands give the whole table of a point; a depth taken from there, or from anywhere else, is still passed as `--total-mm`.

### Flood routing: the hydrograph table between tools

The `route` commands (ADR-0007, ADR-0008) read and write one file format, the hydrograph table: a CSV (or a JSON object of two equal-length columns) with the columns `time_min` (minutes since any origin, strictly increasing at a regular step) and `discharge_m3s` (m3/s, not negative). Other names are given with `--time-column` and `--value-column`; an irregular step, a gap or a negative discharge is refused, nothing is resampled. A table from any source, for example a column of a hydraulic model or a design hydrograph written by another tool, is an input; the file that a `route` command writes with `--output` has the same two columns, so the outflow of one reach is the inflow of the next, or the discharge boundary condition of a hydraulic model:

```bash
hydrolog route lag --lag-min 30 --input-file inflow.csv --output outflow.csv
```

Hydrolog computes discharge only: water levels, inundation and backwater are hydraulics (Hydraulik, HEC-RAS, IMGW HD). Hydrolog writes no other tool's format. A hydrograph contract with Hydraulik and the export of a river network from Hydrograf need `request` issues in those repositories (DEV-17.5); this repository does not make them.

### Hydrograf: migrating HSG from Kartograf to Hydrolog

Until now the hydrologic soil groups were computed by Kartograf (`HSGCalculator`, `calculate_hsg`; in Hydrograf: `backend/core/cn_calculator.py` and `scripts/bootstrap.py`). Since Hydrolog 1.0.0, HSG calculation belongs to Hydrolog (module `hydrolog.soil`; the rules and the texture → HSG mapping were moved from Kartograf 0.8.0, Kartograf ADR-025), and Kartograf is left with raster download only (`download_soil`). Hydrolog does not depend on Kartograf (the former `hydrolog[spatial]` extra was removed).

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
