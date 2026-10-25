# SCOPE.md - Hydrolog Project Scope

## Hydrological Toolkit Library

**Version:** 1.6
**Date:** 2026-10-24
**Status:** v1.0.0 in preparation

---

## 1. Introduction

### 1.1 Project Purpose

**Hydrolog** is a Python library, a CLI (`hydrolog`) and an MCP server that provide tools for hydrological calculations. It is designed as an external dependency for the Hydrograf project and for other systems that need hydrological functions (including Retman and AI agents).

### 1.2 Main Goals

- Generating runoff hydrographs (SCS-CN)
- Computing catchment morphometric parameters
- Generating hyetographs (temporal distribution of rainfall)
- Interpolating precipitation data
- Classifying the river network
- Determining hydrologic soil groups (HSG) from soil texture rasters
- Flow statistics and hydrometry
- Lumped hydrologic flood routing: lag, Muskingum, Muskingum-Cunge, cascade of linear reservoirs, level-pool reservoir, river network (ADR-0007)
- A single command catalog as the source of truth for the library, the CLI, the MCP server and the agent guides

### 1.3 Analogy

Hydrolog is analogous to **Kartograf** (spatial data download) and **IMGWTools** (IMGW data download) - a modular Python library with a clean API that can be used as a dependency in other projects. Since v1.0.0, like them, it exposes a single command catalog (CLI + MCP + AGENTS.md/llms.txt), but it does not depend on either of those libraries: Hydrolog downloads nothing, and data files are supplied by external tools.

---

## 2. FUNCTIONAL SCOPE

### 2.1 ✅ IN SCOPE - Functionality

#### 2.1.1 Module `runoff` - Rainfall-Runoff (v0.1.0)

**SCS Curve Number method:**
- Computing maximum retention: `S = 25400/CN - 254`
- Computing initial abstraction: `Ia = 0.2 × S`
- Computing effective precipitation: `Pe = (P - Ia)² / (P - Ia + S)` when P > Ia, otherwise Pe = 0
  - The simplified form `(P - 0.2S)² / (P + 0.8S)` is valid only when Ia = 0.2S
- Antecedent moisture conditions: AMC-I, AMC-II (default), AMC-III

**SCS unit hydrograph:**
- Time to peak: `tp = 0.6 × tc`
- Peak discharge: `qp = 0.208 × A / tp` (A in km², tp in hours)
- Base time: `tb = 5.0 × tp` (full range of the dimensionless UH; the triangular approximation is 2.67 × tp)
- Dimensionless time distribution

**Rainfall → runoff transformation:**
- Discrete convolution: `Q(t) = Pe(t) ⊗ UH(t)`
- Time step: configurable (default 5 min)

**Results:**
- Qmax - peak discharge [m³/s]
- Time to peak [min]
- Runoff volume [m³]
- Runoff coefficient [-]
- Time series: time vs discharge

**Hydrologic soil groups (HSG) - module `soil` (v1.0.0):**
- USDA texture class from clay, sand and silt content (12 classes) and its assignment to HSG A-D (rules from Kartograf 0.8.0, ADR-025)
- HSG raster (GeoTIFF `uint8`: 0 - no data, 1-4 are A-D) from clay, sand and silt rasters (e.g. SoilGrids in g/kg) and group areas over the whole catchment or within a bbox rectangle (extra `hydrolog[raster]`)
- USDA-NRCS CN tables for HSG + land cover combinations (`runoff.cn_lookup`) and area-weighted CN (`cn weighted`)
- Downloading soil rasters remains out of scope (Kartograf `download_soil`)

---

#### 2.1.2 Module `precipitation` - Precipitation (v0.1.0 / v0.3.0)

**Hyetographs (v0.1.0):**
- Beta distribution (configurable α, β; default α=2, β=5)
- Block distribution (constant intensity)
- Triangular distribution
- DVWK Euler Type II distribution (`EulerIIHietogram`)

**Interpolation (v0.3.0):**
- IDW (Inverse Distance Weighting)
- Thiessen (Voronoi polygons)
- Isohyetal method (`isohyet_method`)
- Arithmetic mean (`arithmetic_mean`)
- Kriging (optional - not implemented)

**Rainfall scenarios (future):**
- ❌ Not implemented
- PMAXTP data (IMGW maximum probable precipitation) is downloaded by the parent application (e.g. Hydrograf via IMGWTools)
- Hydrolog receives ready-made precipitation values

---

#### 2.1.3 Module `time` - Characteristic Times (v0.1.0)

**Time of concentration (tc) - 6 methods:**
- Kirpich formula: `tc = 0.0195 × L^0.77 × S^(-0.385)`
- NRCS formula: `tc = 0.01416 × L^0.8 × (S+25.4)^0.7 × Y^-0.5`
- Giandotti formula: `tc = (4√A + 1.5L) / (0.8 × √Hmean)`
- FAA formula: `tc = 22.213 × (1.1 - C) × L^0.5 / S^(1/3)`
- Kerby formula: `tc = 36.37 × (L × N)^0.467 × S^(-0.2335)`
- Kerby-Kirpich method: `tc = t_overland(Kerby) + t_channel(Kirpich)`

**Input parameters:**
- Main stream length [km or m]
- Stream slope [% or m/m]
- CN (for the NRCS method)

---

#### 2.1.4 Module `morphometry` - Physiographic Parameters (v0.2.0)

**Geometric parameters:**
- Catchment area [km²]
- Perimeter [km]
- Catchment length [km]
- Catchment width [km]

**Shape indices:**
- Form factor Cf = A / L²
- Compactness coefficient Cz = P / √A
- Circularity ratio Ck
- Elongation ratio Cw
- Lemniscate ratio Cl

**Morphometric parameters:**
- Elevation: max, min, mean [m a.s.l.]
- Relief [m]
- Catchment slope [%]
- Main stream slope [%]

**Hypsometric curve:**
- Elevation distribution
- Weighted mean elevation

**WatershedParameters - additional optional fields (v0.6.3):**
- `runoff_coeff` - runoff coefficient for the FAA method
- `retardance` - Kerby roughness coefficient (0.02-0.80)
- `overland_length_km` - overland flow length [km] (FAA, Kerby, Kerby-Kirpich)
- `overland_slope_m_per_m` - overland slope [m/m] (FAA, Kerby, Kerby-Kirpich)
- `Lc_km` - distance to the catchment centroid [km] (Nash/Snyder)
- `manning_n` - Manning coefficient (Nash)
- `urban_pct` - percentage of built-up area [%] (Nash)
- `forest_pct` - percentage of forest cover [%] (Nash)

---

#### 2.1.5 Module `network` - River Network (v0.3.0)

**Classification:**
- Strahler method
- Shreve method

**Indices:**
- Bifurcation ratio (`bifurcation_ratio`)
- Drainage density (`drainage_density`)
- Stream frequency (`stream_frequency`)

**Network statistics (`NetworkStatistics`):**
- Number of streams by order
- Mean stream length by order
- Maximum stream order

---

#### 2.1.6 Module `cli` - CLI (v0.4.0, rebuilt in v1.0.0) ✅

Since v1.0.0 the CLI is generated from the command catalog (`hydrolog.catalog`): 42 commands in 15 groups (list: `hydrolog commands list`). Syntax: `hydrolog <group> <command> --option value`; global flags `--json`, `--schema`, `--lang pl|en`, `-V`. The former CLI syntax (v0.4.0-v0.7.0) was removed without aliases.

```bash
# Time of concentration
hydrolog tc kirpich --length-km 2.5 --slope-m-per-m 0.02
hydrolog tc nrcs --length-km 5.0 --slope-m-per-m 0.01 --cn 72
hydrolog tc giandotti --area-km2 100 --length-km 15 --elevation-diff-m 500
hydrolog tc faa --length-km 0.15 --slope-m-per-m 0.02 --runoff-coeff 0.6
hydrolog tc kerby --length-km 0.10 --slope-m-per-m 0.008 --retardance 0.40
hydrolog tc kerby-kirpich --overland-length-km 0.25 --overland-slope-m-per-m 0.008 \
    --retardance 0.40 --channel-length-km 5.0 --channel-slope-m-per-m 0.005

# CN lookup (TR-55 tables)
hydrolog cn lookup --hsg B --land-cover forest --condition good
hydrolog cn list
hydrolog cn range --land-cover pasture

# SCS-CN calculations
hydrolog scs effective --cn 72 --precipitation-mm 50
hydrolog scs effective --cn 72 --precipitation-mm 50 --amc III

# Unit hydrographs (SCS, Nash, Clark, Snyder)
hydrolog uh scs --area-km2 45 --tc-min 90 --timestep-min 10
hydrolog uh nash --area-km2 45 --n 3 --k-min 30 --timestep-min 10
hydrolog uh clark --area-km2 45 --tc-min 60 --r-min 30 --timestep-min 10
hydrolog uh snyder --area-km2 100 --length-km 15 --centroid-length-km 8 --timestep-min 30

# JSON output (hydrolog-result/1 envelope)
hydrolog uh scs --area-km2 45 --tc-min 90 --json
```

Other groups: `precip`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `config`, `commands`.

---

#### 2.1.6a Operations Layer, Command Catalog and Agent Interfaces (v1.0.0)

- **Command catalog** (`hydrolog.catalog`) - a single source of truth: `Command` and `Option` declarations (English texts with Polish translations, units, ranges, `one_of` groups, examples), `data_commands()`, `command_schema()`, `validate_command()`, `run_command()`
- **Operations layer** (`hydrolog.operations`) - one public, typed function per command; it composes existing classes and contains no new hydrology
- **Result envelope** `hydrolog-result/1` and error document `hydrolog-error/1` with a closed `ERROR_CODES` registry (CLI exit codes: 1, 2, 3, 4, 6, 7, 9, 12, 13)
- **Serialization** - all result classes have `to_dict()` and `to_json()` (`JsonResultMixin`)
- **Data from files** - series, stations, network segments and catchments as CSV/JSON (including the IMGWTools `export_series` export, read without conversion); `WatershedParameters` JSON is the `catchment_characteristics` format in Retman
- **MCP server** (`hydrolog mcp`, extra `hydrolog[mcp]`) - every catalog command is a tool; file access is restricted to `--allow-dir` directories and writing needs `--allow-writes`
- **Agent guides** - `AGENTS.md` and `llms.txt` generated from the catalog (`hydrolog commands guide`), enforced by a byte-for-byte consistency test
- Plots (`hydrolog.visualization`) remain Python-only, outside the command catalog

---

#### 2.1.7 Module `reports` - Calculation Reports (v0.6.0)

**Generating Markdown reports with LaTeX formulas:**
- `HydrologyReportGenerator` - main report generator class
- `ReportConfig` - configuration (tc method, UH model, table/formula options)
- `FormulaRenderer` - rendering formulas with substituted values
- `TableGenerator` - generating Markdown tables (parameters, time series)

**Report sections:**
- Catchment parameters (geometry, terrain, shape indices)
- Time of concentration (formulas with substituted values)
- Hyetograph (parameters, temporal distribution)
- SCS-CN effective precipitation (S, Ia, Pe with values)
- Unit hydrograph (SCS, Nash, Clark, Snyder - model-specific formulas)
- Discrete convolution (procedure, formulas)
- Water balance (summary table)

**Templates (`templates.py`):**
- Polish headings and labels
- Descriptions of methods and AMC conditions
- Literature references, glossary of terms

---

#### 2.1.8 Module `visualization` - Plots (v0.5.0)

The module requires optional dependencies: `pip install hydrolog[viz]`

**Hyetographs:**
- `plot_hietogram()` - rainfall intensity plot with an optional cumulative line
- `plot_hietogram_comparison()` - comparison of total and effective precipitation

**Hydrographs:**
- `plot_hydrograph()` - runoff hydrograph Q(t) with a peak annotation
- `plot_unit_hydrograph()` - unit hydrograph (any model)

**Combined plots:**
- `plot_rainfall_runoff()` - classic rainfall-runoff plot

**UH comparison:**
- `plot_uh_comparison()` - comparison of several UH models on one plot

**Water balance:**
- `plot_water_balance()` - SCS-CN balance visualization (bar or pie)
- `plot_cn_curve()` - P → Pe relation with AMC variants

**Morphometry:**
- `plot_hypsometric_curve()` - hypsometric curve with the HI integral
- `plot_elevation_histogram()` - elevation distribution histogram

**River network:**
- `plot_stream_order_stats()` - network statistics in 3 panels
- `plot_bifurcation_ratios()` - bifurcation ratios by order

**Interpolation:**
- `plot_stations_map()` - map of rain gauge stations with weights

---

#### 2.1.9 Module `statistics` - Hydrological Statistics (v0.7.0)

- Characteristic flow values (Polish system: NNQ-WWQ)
- Frequency analysis of maximum flows (LogNormal, GEV, Pearson III, Weibull)
- Frequency analysis of minimum flows (Fisher-Tippett)
- Detection of low-flow sequences (threshold method)
- Mann-Kendall trend test (stationarity check)
- Goodness-of-fit tests: Kolmogorov-Smirnov, Anderson-Darling
- Akaike information criterion (AIC)

---

#### 2.1.10 Module `hydrometrics` - Hydrometry (v0.7.0)

- Rating curve Q = a × (H − H₀)^b
- Frequency and duration analysis of water levels
- Rybczyński method (gauge zones NTW/STW/WTW: low/medium/high water level zones)

---

#### 2.1.11 Module `routing` - Flood Routing (after v1.0.0, ADR-0007)

Lumped hydrologic routing of discharge hydrographs (storage and translation); water levels,
inundation, backwater and structures stay with Hydraulik, HEC-RAS and IMGW HD.

- `Hydrograph`: a discharge table at a regular time step (`time_min`, `discharge_m3s`), checked
  as in ADR-0008 (no resampling), with the volume under it; read from inline lists or a CSV/JSON
  file (`load_hydrograph`)
- `Reach`: the template of a routing element (initial condition, extension of the time axis until
  the outflow has settled, non-negativity, volume balance, notices) and `RoutingResult`
- Lag: `LagReach`, command `route lag` (the outflow is the inflow, shifted in time)
- Muskingum: `MuskingumReach` (sub-reaches inside the positivity window, steps divided when no
  whole number fits), command `route muskingum`
- Muskingum-Cunge: `MuskingumCungeReach` with constant coefficients (the NRCS form: `K = dx / c`,
  `X` from the diffusion of the wave, distance steps inside the positivity window, the rise-time
  rule), `TrapezoidalSection` (Manning's rating), command `route muskingum-cunge`
- Cascade of linear reservoirs: `CascadeReach` (Nash, Kalinin-Milyukov; the exact response to the
  piecewise-linear inflow from the incomplete gamma function, so no window of stable steps and no
  sub-steps), command `route cascade`
- The outflow written by `--output` is a hydrograph table that every `route` command reads
- Not in scope: variable-parameter Muskingum-Cunge and compound sections, kinematic and dynamic
  waves, reservoir operation (plan `docs/plans/2026-10-24-flood-routing.md`)

---

### 2.2 ❌ OUT OF SCOPE

**Functionality:**
- ❌ Hydraulic flood routing (Saint-Venant solvers, water levels, backwater, bridges and culverts, dam breaks) → Hydraulik, HEC-RAS, IMGW HD; lumped hydrologic routing is in scope (module `routing`)
- ❌ Reservoir operation (gates, release rules); level-pool routing with a given storage-outflow relation is in scope
- ❌ Flood simulations (inundation maps)
- ❌ Water quality modeling
- ❌ Erosion modeling
- ❌ Groundwater modeling
- ❌ Snowmelt modeling
- ❌ Detailed infiltration (Green-Ampt)

**Data download:**
- ❌ Downloading the digital elevation model (DEM, Polish NMT) (→ Kartograf)
- ❌ Downloading land cover (→ Kartograf)
- ❌ Downloading soil rasters (→ Kartograf `download_soil`); computing HSG from already downloaded texture rasters is in scope (module `soil`, since v1.0.0)
- ❌ Downloading IMGW data (→ IMGWTools); Hydrolog reads a ready-made CSV/JSON file from the export
- ❌ REST API (interfaces: Python library, CLI and MCP server)
- ❌ Database operations

**Visualizations and reports:**
- ✅ Static plots (matplotlib) - module `visualization` (since v0.5.0)
- ✅ Markdown/LaTeX reports - module `reports` (since v0.6.0)
- ❌ PDF export (→ external tools, e.g. Pandoc)
- ❌ Interactive maps (→ client application)

---

### 2.3 ⏳ FUTURE SCOPE - Planned for the Future

**Post v1.0:**
- Empirical peak flow formulas (Punzet, Bogdanowicz-Stachy) - project owner decision of 2026-10-19: in scope, but after v1.0.0
- Rational method (Q = CIA) for small catchments
- Parameter calibration
- Uncertainty analysis (Monte Carlo)

**Implemented (since v0.3+):**
- ✅ Nash Cascade (IUH) - `hydrolog.runoff.NashIUH`
- ✅ Clark Unit Hydrograph - `hydrolog.runoff.ClarkIUH`
- ✅ Snyder Unit Hydrograph - `hydrolog.runoff.SnyderUH`
- ✅ CN Lookup (TR-55) - `hydrolog.runoff.cn_lookup`

---

## 3. ARCHITECTURE

### 3.1 Module Structure

```
hydrolog/
├── __init__.py              # Version, main imports
├── exceptions.py            # Shared exceptions (InvalidParameterError)
├── runoff/                  # Rainfall-runoff module
│   ├── __init__.py
│   ├── scs_cn.py           # SCS Curve Number calculations
│   ├── unit_hydrograph.py  # SCS Unit Hydrograph
│   ├── convolution.py      # Discrete convolution
│   ├── generator.py        # HydrographGenerator (rainfall→runoff)
│   ├── nash_iuh.py         # Nash Cascade IUH
│   ├── clark_iuh.py        # Clark IUH
│   ├── snyder_uh.py        # Snyder Synthetic UH
│   └── cn_lookup.py        # CN Lookup Tables (TR-55)
├── morphometry/             # Physiographic parameters
│   ├── __init__.py
│   ├── geometric.py        # Area, perimeter, length
│   ├── terrain.py          # Elevation, slope
│   ├── hypsometry.py       # Hypsometric curve
│   └── watershed_params.py # WatershedParameters (GIS integration)
├── precipitation/           # Precipitation
│   ├── __init__.py
│   ├── hietogram.py        # Temporal distributions
│   └── interpolation.py    # IDW, Thiessen, isohyet, arithmetic mean
├── network/                 # River network
│   ├── __init__.py
│   └── stream_order.py     # Strahler, Shreve, network indices
├── time/                    # Characteristic times
│   ├── __init__.py
│   └── concentration.py    # tc calculations (6 methods)
├── routing/                 # Flood routing (after v1.0.0, ADR-0007)
│   ├── __init__.py
│   ├── hydrograph.py       # Hydrograph (regular-step table), check_table
│   ├── reach.py            # Reach (template), RoutingResult, RoutingNotice
│   ├── lag.py              # LagReach
│   ├── muskingum.py        # MuskingumReach, subreach_window
│   ├── cunge.py            # MuskingumCungeReach, rise_steps
│   ├── sections.py         # TrapezoidalSection (Manning's rating), FlowState
│   ├── cascade.py          # CascadeReach (exact gamma kernel), cascade_weights
│   ├── level_pool.py       # LevelPoolReach (storage indication), timestep_limit_min
│   └── _kernels.py         # Three-point recurrences, shared with ClarkIUH
├── _serialization.py        # to_jsonable(), JsonResultMixin (to_dict/to_json) (v1.0.0)
├── agent_guide.py           # AGENTS.md / llms.txt generator from the catalog (v1.0.0)
├── _data/agents/            # Agent guide templates (English)
├── catalog/                 # Command catalog (v1.0.0)
│   ├── spec.py              # Command, Option
│   ├── envelope.py          # hydrolog-result/1 envelope, Notice
│   ├── inputs.py            # Series, hydrographs, stations, catchments from JSON or CSV/JSON files
│   ├── dispatch.py          # validate_command, run_command, path policy
│   └── groups/              # One module per command group (COMMANDS)
├── operations/              # One public function per catalog command (v1.0.0)
├── mcp/                     # MCP server (v1.0.0, [mcp] extra)
├── soil/                    # HSG from soil texture (v1.0.0)
│   ├── texture.py           # USDA texture triangle, texture → HSG (NumPy only)
│   ├── hsg.py               # classify_hsg(), hsg_statistics_array()
│   └── raster.py            # GeoTIFF input/output ([raster] extra)
├── cli/                     # CLI generated from the catalog (v1.0.0)
│   ├── main.py              # Entry point (hydrolog.cli.main:main)
│   ├── parser.py            # argparse parser from catalog declarations
│   ├── args.py, values.py   # Handling of command-line options and values
│   ├── render.py, texts.py  # Text summary and PL/EN messages
│   └── __main__.py          # python -m hydrolog.cli
├── reports/                 # Report generation (v0.6.0)
│   ├── __init__.py
│   ├── generator.py        # HydrologyReportGenerator
│   ├── formatters.py       # FormulaRenderer, TableGenerator
│   ├── templates.py        # Polish templates and headings
│   └── sections/            # Report sections
│       ├── __init__.py
│       ├── watershed.py     # Catchment parameters
│       ├── concentration.py # Time of concentration
│       ├── hietogram.py     # Hietogram
│       ├── scs_cn.py        # SCS-CN effective precipitation
│       ├── unit_hydrograph.py # Unit hydrograph
│       ├── convolution.py   # Discrete convolution
│       └── water_balance.py # Water balance
├── statistics/              # Hydrological statistics (v0.7.0)
│   ├── __init__.py
│   ├── _types.py            # Shared data types
│   ├── _hydrological_year.py # Hydrological year
│   ├── characteristic.py   # Characteristic values (NNQ-WWQ)
│   ├── high_flows.py       # Frequency analysis of maximum flows
│   ├── low_flows.py        # Fisher-Tippett, low flows
│   └── stationarity.py     # Mann-Kendall test
├── hydrometrics/            # Hydrometry (v0.7.0)
│   ├── __init__.py
│   └── rating_curve.py     # Rating curve, Rybczyński zones
└── visualization/           # Plots (v0.5.0, requires matplotlib)
    ├── __init__.py
    ├── styles.py            # Styles, colors, PL labels
    ├── hietogram.py         # Hyetograph plots
    ├── hydrograph.py        # Hydrograph plots
    ├── combined.py          # Rainfall-runoff plots
    ├── unit_hydrograph.py   # UH comparison
    ├── water_balance.py     # Water balance, krzywa CN
    ├── morphometry.py       # Hypsometric curve, histogram
    ├── network.py           # River network statistics
    ├── interpolation.py     # Rain gauge station map
    └── statistics.py        # Hydrological statistics (v0.7.0)
```

### 3.2 Dependencies

**Required:**
- Python >= 3.12
- NumPy >= 1.24
- SciPy >= 1.10 (statistical distributions, gamma function, optimization - required since v0.7.0)

**Optional (extras `pip install hydrolog[...]`):**
- `raster`: rasterio >= 1.3 + pyproj >= 3.6 (commands `soil hsg` and `soil hsg-stats`, `hydrolog.soil.raster`)
- `mcp`: mcp >= 2.3, < 3 (MCP server `hydrolog mcp`)
- `viz`: matplotlib >= 3.7 + seaborn >= 0.12 (module `visualization`)
- `all`: all of the above

Hydrolog does not depend on Kartograf or IMGWTools; the former `spatial` extra (Kartograf) was removed in v1.0.0.

### 3.3 API Design

**Style:** Object-oriented, class-based

```python
# Usage example
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram
from hydrolog.time import ConcentrationTime

# Time of concentration
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Hyetograph
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(
    total_mm=38.5,
    duration_min=60,
    timestep_min=5
)

# Hydrograph
generator = HydrographGenerator(
    area_km2=45.3,
    cn=72,
    tc_min=tc
)
result = generator.generate(precip)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Time to peak: {result.time_to_peak_min} min")
```

---

## 4. VERSION ROADMAP

| Version | Scope | Modules | Status |
|--------|--------|--------|--------|
| **v0.1.0** | SCS-CN hydrograph | `runoff`, `precipitation.hietogram`, `time` | ✅ Released |
| **v0.2.0** | Morphometric parameters | `morphometry` | ✅ Released |
| **v0.3.0** | Interpolation + network | `precipitation.interpolation`, `network` | ✅ Released |
| **v0.4.0** | CLI + Clark + Snyder + CN Lookup | `cli`, `runoff.clark_iuh`, `runoff.snyder_uh`, `runoff.cn_lookup` | ✅ Released |
| **v0.5.0** | Visualization + Lutz method | `visualization`, `runoff.nash_iuh.from_lutz` | ✅ Released |
| **v0.5.1** | SCS peak discharge correction | `runoff.unit_hydrograph`, `morphometry.watershed_params` | ✅ Released |
| **v0.5.2** | Dependency cleanup | `pyproject.toml` | ✅ Released |
| **v0.6.0** | Calculation reports | `reports` | ✅ Released |
| **v0.6.1** | Nash urban regression | `runoff.nash_iuh.from_urban_regression` | ✅ Released |
| **v0.6.2** | UH formulas in reports + metric corrections | `reports`, `runoff.snyder_uh`, `runoff.clark_iuh` | ✅ Released |
| **v0.6.3** | FAA + Kerby + Kerby-Kirpich tc, API audit, WatershedParameters extension | `time.concentration`, `morphometry.watershed_params`, `reports` | ✅ Released |
| **v0.6.4** | WatershedParams extension + UH ordinates + docs audit | `morphometry.watershed_params`, `runoff.generator`, `reports`, `docs` | ✅ Released |
| **v0.7.0** | Hydrological statistics + Hydrometry | `statistics`, `hydrometrics`, `visualization.statistics` | ✅ Released |
| **v1.0.0** | Stable API, command catalog, catalog-based CLI, MCP server, HSG, result serialization, calculation fixes | `catalog`, `operations`, `mcp`, `soil`, `cli`, `agent_guide` | 🔄 In preparation |
| **after v1.0.0** | Flood routing | `routing` | 🔄 Branches `feature/routing-*` (ADR-0007) |

---

## 5. LIMITATIONS

### 5.1 Methodological limitations

- **SCS-CN:** For catchments < 250 km² (a limitation of the USDA method)
- **Uniform rainfall:** An assumption for small catchments
- **AMC-II conditions:** Default (average)
- **Routing is lumped:** uniform rainfall over the network, inflow at the upstream end of a reach, no lateral inflow, no losses; hydraulic effects are not computed

### 5.2 Technical limitations

- **Pure Python + NumPy:** No dependency on GeoPandas/Shapely in the core
- **Input data:** NumPy arrays, lists, dictionaries; in the CLI/MCP, CSV/JSON files and GeoTIFF rasters (not Shapefile)
- **Thread-safe:** Classes are thread-safe (no global state)

---

## 6. EXTERNAL DEPENDENCIES

| Library | Purpose | Required |
|------------|-----|----------|
| NumPy | Numerical computation | Yes |
| SciPy | Gamma function (Nash IUH), statistical distributions (`statistics`) | Yes (since v0.7.0) |
| IMGWTools | IMGW data (measurement series) | No (Hydrolog reads its CSV export) |
| rasterio, pyproj | GeoTIFF rasters for HSG | No (extra `[raster]`) |
| mcp | MCP server | No (extra `[mcp]`) |

**Hydrolog does NOT contain data download functions:**
- PMAXTP rainfall data → downloaded by the parent application (e.g. Hydrograf via IMGWTools)
- Measurement series → IMGWTools (`series export` to CSV)
- Rasters (DEM, land cover, soil) → Kartograf; Hydrolog does not depend on Kartograf

---

## 7. SUCCESS CRITERIA

### 7.1 Quality

- ✅ Test coverage > 80%
- ✅ Type hints for all public functions
- ✅ Docstrings (NumPy style) for all public classes/methods
- ✅ API documentation (Sphinx/MkDocs)

### 7.2 Functional

- ✅ Results consistent with hand calculations (±1%)
- ✅ Validation against literature examples (USDA TR-55)
- ✅ Edge case handling (CN=100, tc=0, etc.)

### 7.3 Performance

- ✅ Hydrograph generation < 100 ms for typical data
- ✅ No memory leaks for large datasets

---

## 8. LICENSE

**MIT License** - permissive, compatible with use in open-source and commercial projects.

---

**Document version:** 1.6
**Last updated:** 2026-10-24
**Status:** v1.0.0 in preparation
