# PRD.md - Product Requirements Document

## Hydrolog - Hydrological Toolkit Library

**Version:** 1.0.0 (in preparation)
**Date:** 2026-10-19
**Status:** v1.0.0 in preparation

---

## 1. Product Overview

### 1.1 Vision

Hydrolog is a Python library, a CLI and an MCP server that provide a set of tools for hydrological calculations - from generating runoff hydrographs to analysing catchment morphometric parameters, flow statistics and determining hydrologic soil groups. All interfaces are built from a single command catalog, so the same command works in code, in the terminal and in AI agent tools.

### 1.2 Business Goals

1. **Modularity:** Individual modules can be used without installing the whole package
2. **Reusability:** An external dependency for the Hydrograf project and others
3. **Extensibility:** New calculation methods are easy to add
4. **Quality:** Test coverage > 80%, complete documentation

### 1.3 Target Users

| User | Need | How Hydrolog helps |
|------|------|--------------------|
| **Hydrograf developer** | Hydrological calculations in the API | Importing modules as a dependency |
| **Hydrologist/researcher** | Quick calculations in Jupyter | Simple API, examples |
| **Automation** | Batch processing | CLI generated from the command catalog, `--json` output |
| **Retman (agent platform)** | Calculation handlers and catchment data as files | `hydrolog.operations` layer, `WatershedParameters` JSON, `hydrolog-result/1` envelope |
| **AI agent (Claude Code and other MCP clients)** | Calling calculations without guessing options | MCP server `hydrolog mcp`, `AGENTS.md`, `llms.txt` |

---

## 2. User Stories

### 2.1 Module runoff (v0.1.0)

#### US-R01: Generating an SCS-CN hydrograph
**As** a developer of a hydrological application
**I want** to generate a runoff hydrograph with the SCS-CN method
**So that** I can determine the peak discharge for a given rainfall scenario

**Acceptance criteria:**
- [ ] Accepts: catchment area [km²], CN, time of concentration [min]
- [ ] Accepts: a hyetograph (intensity array) or a Hietogram object
- [ ] Returns: a HydrographResult object with Qmax, time to peak and volume
- [ ] Returns: a time series (time, discharge) as numpy arrays
- [ ] Supports AMC-I, AMC-II and AMC-III conditions
- [ ] Raises an exception for invalid input (CN<0, CN>100, area<=0)

**Usage example:**
```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

hietogram = BetaHietogram(alpha=2.0, beta=5.0).generate(
    total_mm=38.5, duration_min=60, timestep_min=5
)
generator = HydrographGenerator(area_km2=45.3, cn=72, tc_min=68.5)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Time to peak: {result.time_to_peak_min} min")
print(f"Volume: {result.total_volume_m3:.0f} m³")
```

---

#### US-R02: Computing effective precipitation
**As** a developer
**I want** to compute effective precipitation with the SCS-CN method
**So that** I can determine how much of the rainfall becomes runoff

**Acceptance criteria:**
- [ ] Accepts: total precipitation [mm], CN
- [ ] Returns: effective precipitation [mm]
- [ ] Handles the case P < Ia (returns 0)
- [ ] Method of the `SCSCN` class (class-based API)

**Example:**
```python
from hydrolog.runoff import SCSCN

result = SCSCN(cn=72).effective_precipitation(precipitation_mm=38.5)
print(f"Effective precipitation: {result.total_effective_mm:.2f} mm")
```

---

### 2.2 Module precipitation (v0.1.0)

#### US-P01: Generating a Beta hyetograph
**As** a developer
**I want** to generate a hyetograph with a Beta distribution
**So that** I get a realistic temporal distribution of rainfall

**Acceptance criteria:**
- [ ] Accepts: total precipitation [mm], duration [min], time step [min]
- [ ] Optionally: alpha, beta parameters (default α=2, β=5)
- [ ] Returns: an object with arrays of intensities and times
- [ ] Sum of intensity × dt = total precipitation (±0.01 mm)

**Example:**
```python
from hydrolog.precipitation import BetaHietogram

hietogram = BetaHietogram(alpha=2.0, beta=5.0)
result = hietogram.generate(total_mm=38.5, duration_min=60, timestep_min=5)

print(f"Intensities: {result.intensities_mm}")
print(f"Times: {result.times_min}")
print(f"Peak intensity: {result.intensity_mm_per_h.max():.2f} mm/h")
```

---

#### US-P02: Generating a block hyetograph
**As** a developer
**I want** to generate a block hyetograph (constant intensity)
**So that** I can perform simplified calculations

**Acceptance criteria:**
- [ ] Accepts: total precipitation [mm], duration [min], time step [min]
- [ ] Returns: an object with an array of constant intensity
- [ ] Intensity = total_mm / duration_min

---

### 2.3 Module time (v0.1.0)

#### US-T01: Computing time of concentration - Kirpich
**As** a developer
**I want** to compute the time of concentration with the Kirpich formula
**So that** I can determine the catchment response time

**Acceptance criteria:**
- [ ] Accepts: stream length [km], slope [m/m]
- [ ] Returns: time of concentration [min]
- [ ] Formula: tc = 0.0195 × L^0.77 × S^(-0.385)

**Example:**
```python
from hydrolog.time import ConcentrationTime

tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
print(f"tc = {tc:.1f} min")
```

---

#### US-T02: Computing time of concentration - NRCS (formerly SCS Lag)
**As** a developer
**I want** to compute the time of concentration with the NRCS method
**So that** I can take CN into account in the calculations

**Acceptance criteria:**
- [ ] Accepts: stream length [km], CN, slope [m/m]
- [ ] Returns: time of concentration [min]
- [ ] Formula: Lag = L^0.8 × (S+1)^0.7 / (1900 × Y^0.5), tc = Lag / 0.6

> **Note:** The method was renamed from `scs_lag` to `nrcs` in v0.3.0. The `slope_percent` parameter was changed to `slope_m_per_m`.

---

### 2.4 Module morphometry (v0.2.0)

#### US-M01: Computing geometric parameters
**As** a developer
**I want** to compute the basic geometric parameters of a catchment
**So that** I can characterise its shape

**Acceptance criteria:**
- [ ] Accepts: an elevation array (2D array), cell size [m]
- [ ] Computes: area, perimeter, length, width
- [ ] Returns: a dictionary or an object with the parameters

---

#### US-M02: Computing shape indices
**As** a developer
**I want** to compute catchment shape indices
**So that** I can compare it with other catchments

**Acceptance criteria:**
- [ ] Computes: Cf, Cz, Ck, Cw, Cl
- [ ] Requires the geometric parameters to be computed beforehand

---

### 2.5 Module network (v0.3.0)

#### US-N01: Strahler classification
**As** a developer
**I want** to classify a river network with the Strahler method
**So that** I can determine the order of the main stream

**Acceptance criteria:**
- [ ] Accepts: a network structure (adjacency list or similar)
- [ ] Returns: the order of each segment

---

### 2.6 CLI (v0.4.0, rebuilt in v1.0.0)

#### US-C01: Generating a hydrograph through the CLI
**As** a user
**I want** to generate a hydrograph from the command line
**So that** I can automate calculations

**Acceptance criteria:**
- [x] Command: `hydrolog hydrograph generate`
- [x] Parameters: `--area-km2`, `--cn`, `--tc-min`, `--hietogram-type`, `--total-mm`, `--duration-min` or `--watershed-file` (WatershedParameters JSON)
- [x] Output: a text summary or, with `--json`, the `hydrolog-result/1` envelope
- [x] Markdown report: `hydrolog report generate --output raport.md ...`

---

### 2.7 Additional hyetograph types (v0.1.0-v0.5.0)

#### US-P03: Triangular hyetograph
**As** a developer
**I want** to generate a triangular hyetograph with a configurable peak position
**So that** I get a simplified rainfall distribution with a distinct peak

#### US-P04: Euler Type II hyetograph
**As** a developer
**I want** to generate an Euler Type II (DVWK) hyetograph
**So that** I can apply the standard design rainfall used in German-speaking countries

---

### 2.8 Additional time of concentration methods (v0.1.0-v0.6.3)

#### US-T03: Time of concentration - Giandotti
**As** a developer
**I want** to compute the time of concentration with the Giandotti formula
**So that** I can take catchment area and elevations into account

#### US-T04: Time of concentration - FAA
**As** a developer
**I want** to compute the time of concentration with the FAA method
**So that** I can determine the response time for overland flow

#### US-T05: Time of concentration - Kerby
**As** a developer
**I want** to compute the time of concentration with the Kerby method
**So that** I can take surface roughness into account in overland flow calculations

#### US-T06: Time of concentration - Kerby-Kirpich (composite method)
**As** a developer
**I want** to compute the time of concentration with the composite Kerby-Kirpich method
**So that** I can treat the overland flow and channel segments separately

---

### 2.9 Additional unit hydrograph models (v0.4.0-v0.5.0)

#### US-R03: Nash IUH
**As** a developer
**I want** to generate an instantaneous unit hydrograph with the Nash model
**So that** I can model runoff with a cascade of linear reservoirs

#### US-R04: Clark IUH
**As** a developer
**I want** to generate an instantaneous unit hydrograph with the Clark model
**So that** I can account for translation (time-area histogram) and storage (linear routing)

#### US-R05: Snyder UH
**As** a developer
**I want** to generate a Snyder synthetic unit hydrograph
**So that** I can use empirical relationships based on L and Lc

---

### 2.10 CN tables (v0.4.0)

#### US-R06: CN lookup from TR-55 tables
**As** a developer
**I want** to read a CN value from the TR-55 tables
**So that** I do not have to look up CN manually for a hydrologic soil group and land cover

---

### 2.11 Spatial precipitation interpolation (v0.3.0)

#### US-P05: Spatial interpolation
**As** a developer
**I want** to compute the mean catchment rainfall from station data
**So that** I can account for the spatial distribution of precipitation (IDW, Thiessen, isohyets)

---

### 2.12 Visualization module (v0.5.0)

#### US-V01: Plots of calculation results
**As** a developer
**I want** to generate plots of hyetographs, hydrographs and the water balance
**So that** I can present calculation results graphically

---

### 2.13 Reports module (v0.6.0)

#### US-RP01: Generating calculation reports
**As** a developer
**I want** to generate a report with the full calculation procedure in Markdown format
**So that** I can document the whole hydrological calculation process with formulas and results

---

### 2.14 Command catalog, MCP server and HSG (v1.0.0)

#### US-K01: One command definition for all interfaces
**As** a Hydrolog developer
**I want** to declare a command once (operation + `Command`/`Option`)
**So that** the library, CLI, MCP server and agent guides share the same option names, units, ranges and validation

**Acceptance criteria:**
- [x] 43 commands in 15 groups, list: `hydrolog commands list`
- [x] Option schema (JSON Schema) for the whole catalog or a single command: `commands schema`, `--schema`
- [x] Result envelope `hydrolog-result/1` and error document `hydrolog-error/1` with a closed `ERROR_CODES` registry
- [x] All result classes have `to_dict()` and `to_json()`
- [x] Consistency test of CLI, MCP and Python, and a byte-for-byte check of `AGENTS.md`/`llms.txt` against the generator

#### US-K02: Calculations from files
**As** an agent or script
**I want** to supply series, stations, network segments and catchments as a CSV/JSON file
**So that** I do not paste long lists of numbers into arguments

**Acceptance criteria:**
- [x] CSV (comma or semicolon, UTF-8, header) and JSON
- [x] An IMGWTools series export (`export_series`) is read without conversion
- [x] Catchment: `WatershedParameters` JSON (the `catchment_characteristics` format in Retman)

#### US-M01: MCP server
**As** a user of an MCP client (e.g. Claude Code)
**I want** to call Hydrolog commands as tools
**So that** the agent computes hydrology locally, without network access or keys

**Acceptance criteria:**
- [x] `hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]` (extra `hydrolog[mcp]`); the server output is always English
- [x] One tool per command (name = `operation_id`), `structuredContent` = result envelope, error as `isError` with `hydrolog-error/1`
- [x] File access only within `--allow-dir` directories (otherwise `forbidden`)

#### US-S01: Hydrologic soil group (HSG)
**As** a hydrologist
**I want** to determine an HSG raster from clay, sand and silt rasters (e.g. SoilGrids) and the areas of groups A-D
**So that** I can compute the area-weighted catchment CN

**Acceptance criteria:**
- [x] `hydrolog.soil`: USDA texture class and HSG (NumPy only), `hsg_from_rasters`, `hsg_statistics` (extra `hydrolog[raster]`)
- [x] Commands `soil texture`, `soil hsg`, `soil hsg-stats`
- [x] Rules consistent with Kartograf 0.8.0 (ADR-025); Hydrolog does not depend on Kartograf

### 2.15 Flood routing (ADR-0007)

#### US-F01: Route a hydrograph through a reach
**As** a hydrologist
**I want** to route a discharge hydrograph through a reach, a reservoir or a river network
**So that** I get the delayed and attenuated hydrograph at the downstream end without a hydraulic model

**Acceptance criteria:**
- [x] `hydrolog.routing`: `Hydrograph` (regular-step discharge table) and `Reach`, the template of a routing element (steady-state or given initial outflow, extension of the time axis until the outflow has settled, volume balance with the storage of the reach)
- [x] Hydrograph in and out as a table `time_min`, `discharge_m3s` (inline lists or a file; `--output` writes the outflow, with `--check` and `--force`)
- [x] Lag: `LagReach`, command `route lag`
- [x] Muskingum with sub-reaches inside the positivity window: `MuskingumReach`, command `route muskingum`
- [x] Muskingum-Cunge with constant coefficients (the NRCS form, section or celerity, accuracy and rise-time rules): `MuskingumCungeReach`, command `route muskingum-cunge`
- [x] Cascade of linear reservoirs with the exact kernel for any time step: `CascadeReach`, command `route cascade`
- [x] Level-pool reservoir by storage indication from a storage-outflow table (inline or `rating_file`, optional stage, steps kept inside the limit of the table): `LevelPoolReach`, command `route level-pool`
- [ ] River network: `route network`
- [x] Hydraulics (levels, inundation, backwater, structures) stays out of scope; the documentation names Hydraulik, HEC-RAS and IMGW HD

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Operation | Target |
|-----------|--------|
| Hydrograph generation (typical data) | < 100 ms |
| Hyetograph generation | < 10 ms |
| tc calculation | < 1 ms |
| Morphometric parameters (100x100 grid) | < 1 s |

### 3.2 Code Quality

- **Test coverage:** > 80%
- **Type hints:** 100% of public functions
- **Docstrings:** 100% of public classes/methods
- **Linting:** `scripts/gate.sh` passes (lint, mypy, tests) without errors

### 3.3 Documentation

- README with a quick start
- NumPy-style docstrings
- Usage examples for each module
- API reference (Sphinx or MkDocs)

### 3.4 Compatibility

- Python >= 3.12
- NumPy >= 1.24
- SciPy >= 1.10 (required since v0.7.0; statistical distributions, gamma function, optimization)
- Matplotlib >= 3.7 (optional, visualization module)
- Seaborn >= 0.12 (optional, visualization module)
- rasterio >= 1.3, pyproj >= 3.6 (optional, extra `[raster]`: HSG from rasters)
- mcp >= 2.3, < 3 (optional, extra `[mcp]`: MCP server)
- No dependency on GeoPandas/Shapely in the core

---

## 4. Constraints and Assumptions

### 4.1 Methodological Constraints

- SCS-CN for catchments < 250 km²
- Uniform rainfall over the whole catchment
- AMC-II antecedent moisture conditions as the default
- Routing is lumped hydrologic routing; no hydraulics (levels, inundation, backwater)

### 4.2 Technical Assumptions

- Input data: NumPy arrays, basic Python types
- Thread-safe (no global state)
- Input/output operations (CSV/JSON files, GeoTIFF, report writing) only in the operations/catalog layer and in the CLI/MCP; calculation classes do not read files
- No network access or data downloading (data is supplied by IMGWTools and Kartograf)

---

## 5. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | > 80% | pytest-cov |
| Hydrograph generation time | < 100 ms | benchmark |
| Calculation accuracy | ±1% vs literature | validation tests |
| Documentation | 100% of public API | sphinx-apidoc |

---

## 6. Roadmap

### v0.1.0 - SCS-CN hydrograph *(completed)*
- [x] `runoff.scs_cn` - SCS-CN calculations (`SCSCN` class)
- [x] `runoff.unit_hydrograph` - SCS UH
- [x] `runoff.convolution` - convolution
- [x] `precipitation.hietogram` - Beta, block, triangular
- [x] `time.concentration` - Kirpich, NRCS (formerly SCS Lag), Giandotti
- [x] Tests: > 80% coverage (103 tests)
- [x] Documentation: README, docstrings

### v0.2.0 - Morphometric parameters *(completed)*
- [x] `morphometry.geometric` - area, perimeter, shape indices
- [x] `morphometry.terrain` - elevations, slopes
- [x] `morphometry.hypsometry` - hypsometric curve
- [x] Tests and documentation (150 tests)

### v0.3.0 - Interpolation and network *(completed)*
- [x] `precipitation.interpolation` - IDW, Thiessen, isohyets, arithmetic mean
- [x] `network.classification` - Strahler, Shreve
- [x] `network.parameters` - network indices (drainage density, bifurcation ratio)
- [ ] `precipitation.scenarios` - PMAXTP integration
- [x] Tests and documentation (210 tests)

### v0.4.0 - CLI + advanced UH models *(completed)*
- [x] `cli` - command-line interface (tc, cn, scs, uh)
- [x] `runoff.nash_iuh` - Nash IUH (cascade model)
- [x] `runoff.clark_iuh` - Clark IUH (time-area histogram + routing)
- [x] `runoff.snyder_uh` - Snyder UH (synthetic unit hydrograph)
- [x] `runoff.cn_lookup` - CN tables per TR-55 (20 land cover types)
- [x] Tests and documentation (412 tests)

### v0.5.0 - Visualization *(completed)*
- [x] `visualization` - plotting module (matplotlib/seaborn)
  - [x] Hyetographs, hydrographs, UH comparisons
  - [x] Water balance, CN curve, hypsometric curve
  - [x] River network statistics, rain gauge station map
  - [x] Dashboard with full calculation results
- [x] `precipitation.hietogram` - Euler Type II (DVWK)
- [x] `runoff.nash_iuh` - Lutz method (estimating n, K from catchment characteristics)
- [x] Tests and documentation (538 tests)

### v0.5.1/v0.5.2 - Fixes *(completed)*
- [x] Correction of the SCS peak discharge constant (2.08 -> 0.208)
- [x] `morphometry.WatershedParameters` - GIS integration interface
- [x] Removal of the unused imgwtools dependency

### v0.6.0 - Reports *(completed)*
- [x] `reports` - Markdown report generation module
  - [x] Full calculation procedure with LaTeX formulas
  - [x] Support for all UH models (SCS, Nash, Clark, Snyder)
  - [x] Configurable sections (formulas, tables, water balance)
- [x] Tests and documentation (610 tests)

### v0.6.1-v0.6.3 - Extensions and quality *(completed)*
- [x] `runoff.nash_iuh` - urban regression method (Rao, Delleur, Sarma 1972)
- [x] Full calculation formulas in reports for all UH models
- [x] `time.concentration` - FAA, Kerby, Kerby-Kirpich methods
- [x] Metric corrections (Snyder W50/W75, Clark histogram, SCS Lag)
- [x] `WatershedParameters` extended with 8 new fields
- [x] Tests and documentation (754 tests)

### v0.7.0 - Hydrological statistics + Hydrometry *(completed)*
- [x] `statistics.characteristic` - characteristic values (NNQ-WWQ), daily/monthly statistics
- [x] `statistics.high_flows` - frequency analysis: LogNormal, GEV, Pearson III, Weibull
- [x] `statistics.low_flows` - Fisher-Tippett, low-flow detection
- [x] `statistics.stationarity` - Mann-Kendall test
- [x] `hydrometrics.rating_curve` - rating curve, Rybczyński zones
- [x] `visualization.statistics` - 10 visualization functions
- [x] Tests and documentation

### v1.0.0 - Stable API, command catalog, MCP, HSG *(in preparation)*
- [x] `catalog`, `operations` - a catalog of 43 commands and the operations layer
- [x] `cli` - CLI generated from the catalog (breaking change: the former syntax was removed)
- [x] `mcp` - MCP server (`hydrolog mcp`, extra `[mcp]`)
- [x] `agent_guide` - `AGENTS.md` and `llms.txt` generated from the catalog
- [x] `soil` - HSG from texture rasters (extra `[raster]`), removal of the Kartograf dependency
- [x] Result serialization (`JsonResultMixin`), `ERROR_CODES` error registry
- [x] Calculation fixes: Fisher-Tippett for minima, Clark UH for D that is not a multiple of the step, calculation report, StreamNetwork, RatingCurve (details: CHANGELOG)
- [ ] Empirical peak flow formulas (Punzet, Bogdanowicz-Stachy) - after v1.0.0
- [ ] Complete API documentation (MkDocs/Sphinx)
- [ ] Publication on PyPI

### After v1.0.0 - Flood routing *(branches `feature/routing-*`, ADR-0007)*
- [x] `routing` and the command group `route`: `Hydrograph`, `Reach`, lag (`route lag`), Muskingum (`route muskingum`), Muskingum-Cunge (`route muskingum-cunge`), cascade of linear reservoirs (`route cascade`), level-pool reservoir (`route level-pool`) (plan: `docs/plans/2026-10-24-flood-routing.md`)
- [ ] River network

---

**Document version:** 1.0.0 (in preparation)
**Last updated:** 2026-10-24
