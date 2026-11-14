# PRD.md - Product Requirements Document

## Hydrolog - Hydrological Toolkit Library

**Version:** 1.0.0 (in preparation)
**Date:** 2026-10-19
**Status:** v1.0.0 in preparation

---

## 1. Product Overview

### 1.1 Vision

Hydrolog is a Python library, a CLI, an MCP server and a web GUI that provide a set of tools for hydrological calculations - from generating runoff hydrographs to analysing catchment morphometric parameters, flow statistics and determining hydrologic soil groups. All interfaces are built from a single command catalog, so the same command works in code, in the terminal, in AI agent tools and in the browser.

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
- [ ] Accepts: a hyetograph (precipitation depths per time step [mm]) or a `HietogramResult`
- [ ] Returns: a `HydrographGeneratorResult` object with Qmax, time to peak and volume
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
- [ ] Accepts: area [km²], perimeter [km], length [km] (`WatershedGeometry`)
- [ ] Computes: area, perimeter, length, width
- [ ] Returns: an object with the parameters (`GeometricParameters`)

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
- [x] 62 commands in 17 groups, list: `hydrolog commands list`
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
- [x] An Obserwator series export (`export_series`) is read without conversion
- [x] Catchment: `WatershedParameters` JSON (the `catchment_characteristics` format in Retman)

#### US-M01: MCP server
**As** a user of an MCP client (e.g. Claude Code)
**I want** to call Hydrolog commands as tools
**So that** the agent computes hydrology locally, without keys and without network access except for `precip pmaxtp`, whose tool fetches the PMAXTP depth of IMGW-PIB through Obserwator and says so (`openWorldHint`, ADR-0018)

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
- [x] Rules consistent with Kartograf 0.8.0 (Kartograf ADR-025); Hydrolog does not depend on Kartograf

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
- [x] River network of subcatchments, reaches, reservoirs and junctions: `RoutingNetwork`, command `route network` (the document `hydrolog-network/1`, a hydrograph table per node in `--output-dir`)
- [x] Subcatchments that make their own hydrograph from their own rainfall (`RainfallSource`: `DesignStorm`, `RainfallSeries`; `RunoffModel`: `CurveNumberRunoff` over `HydrographGenerator`), nodes, rainfall kinds, runoff models and reach methods as registered classes, `describe()` of every part, and the network written as a document, `RoutingNetwork.to_document()` (ADR-0012)
- [x] Control points for an application that picks points on the streams: `ControlPointNetwork` (outlet first; `add_point`, `update_subcatchment`, `add_confluence`, `remove_point`; residual areas and channels given by the application) (ADR-0012)
- [x] Hydraulics (levels, inundation, backwater, structures) stays out of scope; the documentation names Hydraulik, HEC-RAS and IMGW HD

### 2.16 Web GUI (ADR-0014)

#### US-G01: Hydrograph of one watershed that follows every change
**As** a hydrologist without code or an agent
**I want** to enter a watershed, a design rainfall, the losses and a unit hydrograph in a browser form and see the hydrograph at once
**So that** I can try parameters and see their effect without a compute button

**Acceptance criteria:**
- [ ] Section „Hydrogram zlewni” in three steps (Zlewnia: the watershed with CN, also read from a `WatershedParameters` JSON; Hietogram: the rainfall; Hydrogram: the UH model with the tc method it needs, then the SCS-CN losses); a valid change recomputes after 250 ms through `hydrograph generate`, and only the newest response is shown
- [ ] The section starts empty; the guide's worked example (Kamiennik at Świerzawa: Hydrograf's outlet 51,01544 / 15,88984, p 1 %, 12 h, POT) fetched 101,82 mm on 2026-11-04 and shows 56,39 m³/s at 6:20 and 976 759 m³; switching the tc method, the AMC and the UH model gives the runs of the mockup (ADR-0018)
- [ ] Under PMAXTP the depth comes from `precip pmaxtp` for the point, p, the duration and the method, read-only and kept with the inputs, so a reload does not fetch again; no hydrograph is computed until it is known (ADR-0018)
- [ ] Charts: the hydrograph with the hyetograph, the cumulative P, F and Pe, and the unit hydrograph of the run (`uh_times_min`, `uh_discharge_m3s_per_mm`); a table, the balance, the parameters and the notices in Polish
- [ ] An invalid value (e.g. CN 150) shows on its field and keeps the last result, marked; ten fast edits send at most two runs and show the last
- [ ] The CLI line shown under the result, run by the CLI, gives the same peak

#### US-G02: A river network drawn and routed
**As** a hydrologist
**I want** to open a network document or build one, see its schematic, change the settings of a node and route it
**So that** I get the hydrograph of every node without editing JSON by hand

**Acceptance criteria:**
- [ ] Section „Sieć i trasowanie”: the schematic drawn vertically with the outlet at the bottom by the page from its own inputs, also for an incomplete network and before the first run; a document with a `position` for every node opens as placed, one without takes Hydrolog's layout of its structure (`route schematic --structure-only`) as soon as the structure has no problem, whatever values the nodes miss (ADR-0023, ADR-0025)
- [ ] The network's time step and rainfall come first, in step 1 „Sieć” (Hydrogram zlewni's step 2: PMAXTP fetched for a point and kept, a design hyetograph or a series); a subcatchment takes it („Jak w sieci”) unless it has its own, and one with neither is the problem „Brak opadu” of its node (plan `docs/plans/2026-11-10-network-wizard.md`, A2)
- [ ] A node is chosen by a click, the arrow keys and Enter or Space, in the node list or in the node table (with „Opis” and „Odpływa do”), and opens its settings in „Dane”: a reach or a reservoir the form of its type and method (from `hydrolog-network-1.schema.json`), with a rating table editor; a subcatchment made from rainfall its panel beside „Dane”, Hydrogram zlewni's three steps with the same fields, order, checks and (i) explanations, mapped to the node by the one mapping of Hydrogram zlewni's hand-off (A1, A3)
- [ ] „Oblicz sieć” runs `route network`; the example's outlet values equal those of `route network`; a changed reach method shows its options and marks the results stale, and so do a link and a rename, while a move and a description do not
- [ ] Results per node (chart and parameters); the SVG schematic draws the picture of the canvas, and the exported network document keeps the positions and descriptions

#### US-G03: Flow statistics
**As** a hydrologist
**I want** to compute the flood frequency of a series of annual maxima in the browser
**So that** I can read design discharges and compare them with a design hydrograph

**Acceptance criteria:**
- [ ] Section „Statystyka przepływów”: a file (columns from its header, `date_column` for daily series) or pasted values; distributions and return periods; the probability plot and tables
- [ ] The guide's annual maxima 1998–2023, pasted, give GEV by maximum likelihood „Q 1% = 307,3 m³/s” (the default fit is the L-moments, ADR-0021) and the KZGW notice in Polish (from the notice code `short_record`)
- [ ] „Do porównania” draws a chosen quantile on the hydrograph of „Hydrogram zlewni”

#### US-G04: Calculators
**As** an engineer
**I want** single calculations (time of concentration, CN, effective rainfall, unit hydrographs...) prefilled from my watershed
**So that** I can check one step without building the whole hydrograph

**Acceptance criteria:**
- [ ] Section „Kalkulatory”: 16 calculators, catalog forms prefilled from the watershed of „Hydrogram zlewni”
- [ ] The tc comparison lists six methods with the words of their applicability notices (`outside_typical_range`)
- [ ] A calculator's CLI line and result match the CLI's

#### US-G05: Every command as a generated form
**As** a user of Hydrolog
**I want** a form for every catalog command
**So that** I can run any calculation in the browser, also a command added after the GUI

**Acceptance criteria:**
- [ ] Section „Wszystkie polecenia” lists the 58 commands of the GUI (all but `gui serve`, `config show`, `commands guide` and `commands batch`) under Polish group titles, with search
- [ ] Fields from `commands-1`: units, bounds, allowed values with their meanings, `one_of` groups, series, files; the `scs effective` and `uh nash` forms reproduce the mockup's validation and run
- [ ] Errors placed on their field by `details.option` and worded in Polish from `code` and `reason`; an error without an option stands above the form
- [ ] Input files upload into the session and outputs download

#### US-G06: Exports and the hand-off with Hydrograf
**As** a hydrologist who works with Hydrograf
**I want** to take a result out of the GUI and to pass a watershed or a network between Hydrograf and Hydrolog
**So that** I can document it and continue in the other tool without retyping

**Acceptance criteria:**
- [ ] CSV (the hydrograph table that every `route` command and Hydraulik read), JSON (the envelope), the Markdown report (`report generate`), a print view on A4 (PDF from the browser), PNG of the chart shown and the CLI line (`format_command`)
- [ ] A hand-off from „Hydrogram zlewni” is `nogat-handoff/1` carrying `hydrolog-network/1`, validates against Nogat's schema and reopens with the same values; its payload through `route network` gives the same outlet peak
- [ ] A hand-off with two subcatchments opens in „Sieć i trasowanie”; the producer's version and result are shown beside Hydrolog's

#### US-G07: Running the GUI standalone and as a Nogat module
**As** the user of one computer, or the operator of Nogat's GUI platform
**I want** to start the GUI with one command, or have the platform host it
**So that** I get the same GUI on my own machine and inside Nogat

**Acceptance criteria:**
- [ ] `hydrolog gui serve` (extra `hydrolog[gui]`) answers on 127.0.0.1:8070, `--no-browser` does not open a browser, and Ctrl+C or SIGTERM stops it with exit 0; without the extra it ends with `missing_dependency` and the hint `pip install "hydrolog[gui]"`
- [x] `hydrolog gui serve --check` returns the plan (`hydrolog-plan/1` with `targets: []`, `url`, `port_free`) without serving; a host other than loopback adds the notice `exposed_without_auth`
- [ ] The entry point `nogat.gui` loads `gui_module()`; the app mounted at `/m/hydrolog/` serves the page and the API
- [ ] Every response carries the CSP and security headers of ADR-0014; cross-site writes are refused; files stay in the session's work directory within its limits
- [ ] Both themes and the phone layout (390 px) work without console errors or CSP violations

#### US-G08: The catalog behind the GUI
**As** the GUI, or any other client of the catalog
**I want** the CLI line of a call, stable notice codes with their values, the layout of a network and the unit hydrograph of a run
**So that** I show and word everything from the catalog and compute nothing myself (ADR-0015)

**Acceptance criteria:**
- [x] `format_command` and `parse_command` (in `hydrolog` and `hydrolog.catalog`): every catalog example survives `format_command(parse_command(call))` and runs
- [x] Every notice code in the registry `NOTICES` with its level, English template and `details` keys; no notice of any catalog example is `user_warning`
- [x] `route schematic` returns `hydrolog-network-schematic/1` without values, equal to `RoutingNetwork.schematic()`
- [x] `hydrograph generate` returns `uh_times_min` and `uh_discharge_m3s_per_mm`; the UH ordinates convolved with Pe give Q
- [x] `gui serve` is in `commands list` and `commands schema`, absent from MCP `tools/list` and from the index of `AGENTS.md`, which stays within 16 KiB

#### US-G09: Building a network as in HEC-HMS
**As** a hydrologist who knows the basin model editor of HEC-HMS
**I want** to place the elements of a network, connect each to the one below it, name and describe them and give their parameters in the browser
**So that** I build a network for `route network` without writing `hydrolog-network/1` by hand (plan `docs/plans/2026-11-10-network-editor.md`, ADR-0023)

**Acceptance criteria:**
- [ ] „Nowa sieć” opens step 1 with the time step and „Opad sieci” first and an empty canvas that asks for the rainfall before the elements; its palette adds „Zlewnia”, „Odcinek”, „Zbiornik”, „Złącze” and „Wylot” (Hydrolog's five node types; HEC-HMS's source is a subcatchment given its hydrograph, its diversion has no counterpart)
- [ ] The guide's three-subcatchment network built from empty by the mouse, by the keyboard alone and without any drag, each subcatchment in its panel, gives the outlet values of the guide's file; „Uporządkuj” lays its structure out before any value is given (ADR-0025)
- [ ] After every edit the structure is checked with the library's reasons (`cycle`, `upstream_count`, `no_outlet`, `disconnected_node`...), every problem at once, marked on its node and listed in „Problemy sieci”; a refused link says its reason, a second inflow into a reach, a reservoir or the outlet offers „Wstaw złącze”, and Hydrolog confirms every complete network (`route schematic`)
- [ ] Ids are checked as the library checks them and every `from` follows a rename; a description is plain text of up to 500 characters; „Usuń i połącz” bridges a removed node; „Cofnij” and „Ponów” go through 100 steps
- [ ] „Zapisz sieć” (or „Zapisz szkic” for a network with problems) downloads `hydrolog-network/1` with the positions and descriptions; it reopens as placed and `route network --schematic` draws the same picture
- [ ] „Dodaj zlewnię z Hydrografa” adds the subcatchments of a hand-off to the open network (`Z1` becomes `Z2`); the hand-off written from Sieć validates against Nogat's schema and `/1` and reopens with its positions
- [ ] WCAG 2.2 AA: every action by the keyboard and by a single pointer without dragging, the keys listed by „Skróty”; a 390 px phone, on which the subcatchment's panel and „Dane” alternate, and both themes without console errors

#### US-G10: A network delineated by Hydrograf opens ready
**As** a hydrologist who delineates a network at control points in Hydrograf
**I want** it to open in Sieć laid out, with the origin of each node, and to keep those origins when I hand it on
**So that** I give only what Hydrograf leaves to Hydrolog (the network's rainfall, the section of each reach) and still know where every value came from (plan `docs/plans/2026-11-10-network-wizard.md`, A6; Nogat's `node_provenance`)

**Acceptance criteria:**
- [ ] A hand-off of a network opens in Sieć at the structure's layout, its subcatchments through the mapping of Hydrogram zlewni's inputs, every node with its origin by Nogat's precedence (the node's own `node_provenance` entry, else the hand-off's `provenance`); a key that names no node is left out, named in the load's note, and the network still opens
- [ ] A subcatchment's panel names its watershed's element in Hydrograf's words (a tributary, the headwater too, at a point or at its mouth; the reach of an intermediate subcatchment) with its outlet's place and the fields changed since, and the origins of its rainfall and runoff; a reach, a junction and the outlet show theirs in „Dane” (how the length and the slope were measured, the check length of the vector line)
- [ ] A reach handed over without its section is marked until Manning's n and the width are given; then the network computes
- [ ] The hand-off written from Sieć carries `node_provenance` under the current ids, with `changed` for edited fields and `{"source": "user"}` for an edited rainfall or runoff and for nodes made in Sieć; it validates against Nogat's schema and reopens with the same origins
- [ ] Hydrograf's own hand-off of a network, as its `POST /api/delineate-network` writes it (`tests/fixtures/handoff_hydrograf_network.json`), opens so

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
- starlette >= 1.10, < 2, uvicorn >= 0.54, < 1 (optional, extra `[gui]`: web GUI)
- obserwator >= 3.0.0.dev0, < 4 (optional, extras `[pmaxtp]` and `[gui]`: the PMAXTP depth of `precip pmaxtp`)
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
- Input/output operations (CSV/JSON files) only in the operations/catalog layer and in the CLI, MCP server and GUI, apart from GeoTIFF in `hydrolog.soil.raster` and a report's file in `HydrologyReportGenerator`; calculation classes do not read files
- No data downloading and no network access, except `precip pmaxtp`, which fetches the PMAXTP depth of a point from IMGW-PIB through Obserwator (extra `pmaxtp`, ADR-0018); other data is supplied as files by Obserwator and Kartograf

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
- [ ] `precipitation.scenarios` - PMAXTP integration (since v1.0.0 the PMAXTP depth of a point is `precip pmaxtp`, fetched through Obserwator, ADR-0018)
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
- [x] `catalog`, `operations` - a catalog of 62 commands in 17 groups and the operations layer
- [x] `cli` - CLI generated from the catalog (breaking change: the former syntax was removed)
- [x] `mcp` - MCP server (`hydrolog mcp`, extra `[mcp]`)
- [x] `agent_guide` - `AGENTS.md` and `llms.txt` generated from the catalog
- [x] `soil` - HSG from texture rasters (extra `[raster]`), removal of the Kartograf dependency
- [x] Result serialization (`JsonResultMixin`), `ERROR_CODES` error registry
- [x] Calculation fixes: Fisher-Tippett for minima, Clark UH for D that is not a multiple of the step, calculation report, StreamNetwork, RatingCurve (details: CHANGELOG)
- [x] Station analyses for Obserwator's series: the groups `stats`, `hydrometrics` and `meteo` (ADR-0029 to ADR-0033)
- [x] `gui` - the web GUI (`hydrolog gui serve`, extra `[gui]`, ADR-0014; section 2.16)
- [ ] Empirical peak flow formulas (Punzet, Bogdanowicz-Stachy) - after v1.0.0
- [ ] Complete API documentation (MkDocs/Sphinx)
- [ ] Publication on PyPI

### v1.0.0 - Flood routing *(merged into `develop`, ADR-0007)*
- [x] `routing` and the command group `route`: `Hydrograph`, `Reach`, lag (`route lag`), Muskingum (`route muskingum`), Muskingum-Cunge (`route muskingum-cunge`), cascade of linear reservoirs (`route cascade`), level-pool reservoir (`route level-pool`), river network (`route network`) (plan: `docs/plans/2026-10-24-flood-routing.md`)

---

**Document version:** 1.0.0 (in preparation)
**Last updated:** 2026-11-14
