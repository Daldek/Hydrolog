# Research: long-term (continuous) hydrological modelling and flood routing

| | |
|---|---|
| Date | 2026-10-24 |
| Status | Research for the author's decisions. The routing part (section 5, phases R0 to R4) was taken up on 2026-10-24: decisions D1, D9, D10, D13 and D14 are recorded in [ADR-0007](../decisions/0007-flood-routing-enters-the-scope.md) and in the plan [2026-10-24-flood-routing.md](2026-10-24-flood-routing.md). Nothing else in this report is approved; the continuous-modelling part (section 4, phases L0 to L6) is not implemented. A change of a command, option or result schema starts with a plan in `docs/plans/` ([DEV-17.4][dev-std]) and ADRs ([DOC-8.1][doc-std]). |
| Base | branch `chore/nogat-2.1`, commit `d4f7282` (Hydrolog 1.0.0.dev0); this report lives on branch `research/long-term-and-routing` |
| Method | Reading of the repository, the Nogat standard 2.1 and the ecosystem registry; checks of candidate libraries on GitHub and PyPI (all dates below are the state on 2026-10-24); reading of primary sources; small throwaway numerical experiments (Appendix A, not kept in the repository). |
| Location | Moved from `docs/research/` to `docs/plans/` on 2026-10-24 (decision D14): DEV-17.4 says `docs/research/` is not used for new work. The text is otherwise unchanged. |

## 1. Summary

Both directions fit "hydrological calculations" if they stay **lumped and hydrologic** (storage, translation, conceptual stores) and leave hydraulics, water quality and crop management to other tools. Neither is in scope today: [SCOPE.md](../SCOPE.md) §2.2 lists channel flow routing, retention reservoir modelling, snowmelt modelling and groundwater modelling as out of scope, and §2.3 lists parameter calibration and uncertainty analysis as future work. Adding them is a scope change, so decision D1 and an ADR come first.

1. **Routing first.** A `hydrolog.routing` package with lag, linear reservoir and Muskingum (with sub-reaches), a cascade of linear reservoirs (Kalinin–Milyukov/Nash; reuses `NashIUH`), Muskingum–Cunge (constant-coefficient NRCS form first, variable parameters later), level-pool (storage-indication) reservoir routing and a network composer over the existing `StreamNetwork` DAG. The method set is closed, the numerical rules are documented, and public-domain reference data exist (NRCS NEH-630 chapter 17): two worked examples were reproduced to within 0.85 and 0.24 ft³/s in this research (Appendix A). It removes the limit "no routing: hydrograph for the closing cross-section" ([SCOPE.md](../SCOPE.md) §5.1) and lets the SCS-CN method be applied per sub-catchment instead of to a whole catchment under 250 km². Estimated 14–18 working days (R1–R4).
2. **Continuous modelling: lumped conceptual models built in-house, in two steps.** First the parts that are useful alone: evaluation metrics (NSE, KGE and relatives), series alignment and split-sample helpers, baseflow separation, PET (Oudin, Hargreaves–Samani) and degree-day snow (L1–L2, 7–9 days). Then GR4J (GR5J/GR6J optional) and an HBV-class model with DDS calibration (L3–L4, 13–17 days). A SWAT-like daily soil-moisture CN model with aquifer reservoirs (L5) and uncertainty analysis (L6) only after the data decisions D3, D5 and D8.
3. **Do not wrap SWAT+ or the Python libraries; do not clone SWAT+.** SWAT+ is a Fortran model (LGPL-2.1) driven by a text-file project that QGIS tooling builds first; pySWATPlus (GPL-3.0-or-later) only runs it. hydrobricks (MIT) has a C++ core and is at 0.9.x; RRMPG is not on PyPI; SuperflexPy (LGPL-3.0) and GRsuite (GPL-2.0-or-later) depend on Numba. A GR4J run over 30 years of daily data took 34–42 ms in pure Python here, so a 500–2,000-evaluation calibration is feasible with NumPy and SciPy only. Use airGR, GRsuite, hydrobricks and HEC-HMS as development-time cross-checks, not as dependencies.
4. **Boundary.** Hydrolog does hydrologic routing and rainfall–runoff; Hydraulik, HEC-RAS and IMGW HD do hydraulics (water levels, inundation, backwater, structures). Polish practice draws the same line: the flood-risk reduction programme for the Kaczawa catchment (IMGW-PIB with Wody Polskie, 2025) computes hydrographs with an HBV rainfall–runoff model and transforms the wave with a 1-D hydrodynamic model ([PRRP Kaczawa][prrp-kaczawa]). Hydrolog hands hydrographs to Hydraulik as CSV; Hydrograf supplies the network (its `stream_catchments.downstream_segment_idx` is a downstream map) and would have to drop "no routing" from its scope.
5. **The agent-guide budget is the first hard blocker.** `AGENTS.md` is 16,073 of 16,384 bytes and 164 of 200 lines ([DOC-1.7][doc-std]); a command costs about 138 bytes with its group heading, so two more commands fit. The 18 commands proposed here need a generator change, a recorded deviation or a Nogat budget decision (D10). The `core` family holds 9 of its 10 allowed tools ([AGI-5.12][agi-std]).
6. **Data gaps are requests, not code.** Daily synoptic data (wind, humidity, sunshine) for Penman–Monteith are marked unsupported in IMGWTools; no Polish regional channel-geometry relations were found; SoilGrids is a 250 m global product. Oudin and Hargreaves–Samani PET need only temperature and latitude, which IMGW climate stations and `WatershedParameters` (plus one new optional field) can supply.

Effort (focused working days with agent assistance, review by the author not included): R0–R4 15–19 (up to 22 with variable-parameter Muskingum–Cunge), L0–L4 21–27, L5–L6 13–17, guide-budget work 1–2. Section 7 gives the table, the order and the dependencies; section 10 lists the 15 decisions that only the author can take.

## 2. Starting point

### 2.1 What exists and what is missing

| Need | Existing piece | Gap |
|---|---|---|
| Runoff volume | `SCSCN`: event method, AMC I–III by the Chow et al. conversions, configurable λ ([`runoff/scs_cn.py`](../../src/hydrolog/runoff/scs_cn.py)) | no state between days; CN is not driven by soil moisture |
| Transformation | SCS, Nash, Clark and Snyder unit hydrographs, `convolve_discrete`, `HydrographGenerator` ([`runoff/`](../../src/hydrolog/runoff/)) | one outlet; no attenuation along channels; direct runoff only |
| Linear reservoir scheme | `ClarkIUH._route_linear_reservoir`: `O_t = O_(t-1) + C1 (I_t + I_(t-1) - 2 O_(t-1))`, `C1 = dt / (2R + dt)` ([`clark_iuh.py`](../../src/hydrolog/runoff/clark_iuh.py)) | private; identical to Muskingum with X = 0 and K = R (Appendix A4); the docstring calls it "Muskingum-Cunge", which it is not |
| Cascade of linear reservoirs | `NashIUH` (gamma kernel with n and K) | not offered as a routing kernel |
| River network | `StreamNetwork`, `StreamSegment(segment_id, upstream_ids, length_km)`: topological processing, cycle and unknown-id errors, Strahler/Shreve ([`network/stream_order.py`](../../src/hydrolog/network/stream_order.py)), command `network stats` | no flow, no junction sums, no reach parameters; the downstream map is private |
| Catchment attributes | `WatershedParameters` (area, lengths, slopes, CN, `manning_n`, urban and forest percentages) and the hypsometric curve ([`morphometry/`](../../src/hydrolog/morphometry/)) | no latitude (PET), no elevation zones |
| Series input | `load_series`, `read_table`, stations; IMGWTools CSV is read unchanged ([`catalog/inputs.py`](../../src/hydrolog/catalog/inputs.py)) | one value column per call; no join of several files by date; no elapsed-time (minutes) hydrograph table |
| Observed-series statistics | frequency analysis, characteristic flows, low-flow sequences, Mann–Kendall ([`statistics/`](../../src/hydrolog/statistics/)) | no model-versus-observed metrics, no baseflow separation |
| Soil data | `soil hsg` (SoilGrids clay, sand, silt to HSG), `cn weighted`, TR-55 tables | no soil hydraulic properties (field capacity, wilting point, Ksat) |
| Agent interface | one catalog behind CLI, MCP, Python and guides | budgets of section 2.2 |

### 2.2 Constraints a new group must meet

| Constraint | Source | State today | Effect on this work |
|---|---|---|---|
| One command = catalog entry + one keyword-only operation; names `<group> <verb>`; `operation_id` at most 48 characters; summary at most 100 characters; summary + description + rules at most 600 characters | [AGI-2.2, AGI-5.2][agi-std], [DOC-1.7][doc-std], [ADR-0001](../decisions/0001-catalog-english-and-operation-ids.md) | 38 commands in 14 groups | every command below needs a bilingual declaration (the group modules hold 4,994 lines for 38 commands, about 130 per command), an operation, a result schema, examples that the contract test runs, tests and docs |
| `AGENTS.md` at most 200 lines and 16 KiB, generated, byte-compared | [DOC-1.7, DOC-4.1][doc-std], [`test_agent_guide.py`](../../tests/contract/test_agent_guide.py) | 164 lines, 16,073 bytes: 36 lines and 311 bytes free; the command index is 5,250 bytes for 38 commands | about two more commands fit (D10) |
| `core` family at most 10 tools | [AGI-5.12][agi-std], `CORE_FAMILY_MAX` in [`catalog/spec.py`](../../src/hydrolog/catalog/spec.py) | 9 | at most one new core command; none proposed |
| CLI and MCP results at most 20,000 characters per default page | [DOC-1.7][doc-std], [AGI-5.6][agi-std] | event hydrographs (288 points) fit | a 30-year daily series (10,950 values) does not: long series go to `--output` files and the envelope carries summaries |
| Writing commands use `--output`, `--force`, `--check` | [ADR-0003](../decisions/0003-writing-commands-output-force-check.md) | three commands write | routing and simulation commands that write series follow it |
| Options carry the unit; docstrings give units in brackets | [DEV-8.2, DEV-9.2][dev-std] | `area_km2`, `tc_min`, `timestep_min` | `k_min`, `lag_min`, `x1_mm`, `x4_d`, `latitude_deg` |
| Errors are registry codes; precision goes to `details.reason` | [ADR-0005](../decisions/0005-error-registry.md) | 11 codes | stability, alignment and gap problems use `validation_error`, `data_error`, `calculation_error` with reasons |
| Runtime dependencies NumPy, SciPy, platformdirs; Python 3.12+; MIT licence; no network; heavy imports lazy | [`pyproject.toml`](../../pyproject.toml), [AGI-5.11, AGI-7.3][agi-std] | as stated | no Numba, no GPL or LGPL dependency by default (section 4.4) |
| A change of a command or schema needs a plan and ADRs | [`CLAUDE.md`](../../CLAUDE.md), [DEV-17.4][dev-std] | six ADRs | phases R0 and L0 |
| Tests are offline; coverage floor 80 % | [`CLAUDE.md`](../../CLAUDE.md) | gate in `scripts/gate.sh` | reference data are committed fixtures or closed-form checks |

## 3. Shared context

### 3.1 Roles in the ecosystem and the boundary

| Project | What it does today | What this work needs from it or gives it |
|---|---|---|
| [Kartograf](https://github.com/Daldek/Kartograf) | Downloads the digital elevation model (DEM, Polish NMT; 0.15–10 m grids), land cover (BDOT10k, CORINE Land Cover) and SoilGrids rasters (`clay`, `sand`, `silt`, `soc`, `bdod`, `cfvo`, `ocd`, `nitrogen`, `phh2o`) | Terrain, land cover and soil inputs; delivered as files, no package dependency ([registry][nogat-registry]) |
| [IMGWTools](https://github.com/Daldek/IMGWTools) | IMGW-PIB and ČHMÚ series; daily climate data (`Tmax`, `Tmin`, `Tmean`, `P`, snow cover) from 1951, daily precipitation from 1950, daily hydrological data (`H`, `Q`, `T`) from 1951, PMAXTP | Forcing and observed discharge; the `series export` CSV is read by Hydrolog unchanged ([INTEGRATION.md](../INTEGRATION.md)) |
| [Hydrograf](https://github.com/Daldek/Hydrograf) | Web application: watershed delineation, stream network and sub-catchments in PostGIS; the SCS-CN hydrograph at any point; its documented assumptions are "no routing in the channel (instant aggregation)" and "SCS-CN for catchments up to 250 km²" ([SCOPE][hydrograf-scope]) | Supplier of the network: the table `stream_catchments` holds `downstream_segment_idx` ("graph: the segment it drains to") and `stream_network` holds `length_m`, `mean_slope_percent` and `strahler_order` ([data model][hydrograf-data-model]); consumer of routing |
| [Hydraulik](https://github.com/Daldek/Hydraulik) | Research stage: 2-D hydraulic flood screening with Deltares SFINCS (registry summary) | Consumer of hydrographs: SFINCS takes point discharge time series in m³/s as forcing ([manual][sfincs-forcing]), so a Hydrolog hydrograph is a direct input; Hydraulik does not need Hydrolog routing inside its domain |
| Retman | Natural-language command layer over the catalogs | New commands appear through `hydrolog-catalog`; no extra work |

**Boundary rule proposed.** Hydrolog computes quantities that follow from storage and translation: runoff volume and hydrograph, attenuation and delay along a reach, level-pool reservoir outflow, daily conceptual water balance. It does not compute water levels, inundation extents, backwater, the effect of bridges and culverts, dam breaks or 2-D flow. Those belong to Hydraulik, HEC-RAS or IMGW HD. Muskingum–Cunge is a *diffusion-wave* method that Ponce calls "hydraulic in basis" yet suited to "extensive watershed/basin routing" ([Ponce 2020][ponce-mc]); its own accuracy check says when to stop trusting it (section 5.3).

### 3.2 Polish practice

- **Design flows are mostly statistical.** The national methodology of 2017 (Stowarzyszenie Hydrologów Polskich for KZGW; authors Banasik, Wałęga, Węglarczyk, Więzik) prescribes a statistical method at gauged sections, the rainfall formula for natural catchments up to 50 km², an areal regression equation above 50 km², and a rainfall–runoff simulation for urbanised catchments ([KZGW 2017][kzgw-2017], Table 1). Its chapter VI describes the SCS (CN), Snyder and Nash transformations, which are the models Hydrolog already has. It also says that, when the model is used to delimit flood-hazard zones, the decomposition into sub-catchments follows "the needs of building a hydraulic model of flood-wave transformation in the river channel" (rule 2 of chapter VI). Consequence: Hydrolog's new functions support scenario work, hypothetical hydrographs and reservoir effects; they do not replace the statistical design flow.
- **Operations use HBV plus a hydrodynamic model.** The flood-risk reduction programme for the Kaczawa catchment (IMGW-PIB with Wody Polskie, March 2025) used the operational rainfall–runoff model "in the IHMS HBV software", with catchment parameters from the Hydrographic Division Map of Poland (MPHP, Mapa Podziału Hydrograficznego Polski, version 16 of 2021), a topographic map 1:10,000, a DEM and CORINE 2018. The hydrographs entered the 1-D hydrodynamic model IMGW HD as boundary conditions; small tributaries were point inflows; a planned reservoir was represented in the rainfall–runoff stage and dry flood-control reservoirs (suchy zbiornik przeciwpowodziowy) in the hydrodynamic stage ([PRRP Kaczawa][prrp-kaczawa], chapter 5). The same inputs (DEM, CORINE, sub-catchment network) are what Kartograf and Hydrograf supply.
- **SWAT is a research tool in Poland.** It was calibrated for the Gąsawka, Rega and Warta basins ([Ostojski et al. 2014][ostojski-2014]); the sources read for this report show no operational use.

### 3.3 Data supply for both directions

| Input | Needed by | Supplier and status |
|---|---|---|
| Daily areal precipitation | every continuous model | IMGWTools daily precipitation and climate datasets give point series; `precip areal` handles one time step, so an areal *series* needs a new command (L2) |
| Daily mean, minimum, maximum temperature | snow, Oudin and Hargreaves–Samani PET | IMGWTools daily climate dataset; available |
| Solar radiation, humidity, wind | Penman–Monteith | IMGW daily synoptic archives exist (`dane_meteorologiczne/dobowe/synop`) but IMGWTools lists `meteo/dobowe/synop` as unsupported; **request** (D5, D15) |
| Snow depth, fresh snow [cm] | snow validation | IMGWTools precipitation dataset; depth, not water equivalent |
| Observed daily discharge | calibration, metrics | IMGWTools daily hydrological dataset (`Q`, hydrological year November–October); available |
| Observed inflow and outflow of one reach | Muskingum calibration | two gauges in the daily dataset; flood-wave timing needs sub-daily series, which the IMGWTools dataset registry does not list (hydro daily, monthly, semi-annual only) |
| Area, mean elevation, hypsometric curve | all | `WatershedParameters`, `morphometry` ([hypsometry](../../src/hydrolog/morphometry/hypsometry.py)); latitude is missing |
| Land cover, HSG → CN | event and L5 | Kartograf rasters → `soil hsg`, `cn weighted`; available |
| Soil field capacity, wilting point, Ksat | L5 | derivable from SoilGrids sand, clay, organic carbon and bulk density with pedotransfer functions ([Saxton and Rawls 2006][saxton-rawls]); 250 m resolution limits trust |
| Reach length, slope | routing | Hydrograf `stream_network` (`length_m`, `mean_slope_percent`) or Kartograf DEM; DEM slope over short reaches is noisy |
| Channel width, depth, Manning n | Muskingum–Cunge, level-pool | **not in a DEM** (the water surface hides the cross-section). Power laws of drainage area exist for the United States ([Leopold and Maddock 1953][leopold-maddock]; [Bieger et al. 2015][bieger-2015]); no Polish regional relations were found in this research |
| Stage–area of a reservoir site | level-pool | DEM hypsometry gives the dry basin; bathymetry of an existing reservoir is missing |

## 4. Direction A: long-term (continuous) modelling

### 4.1 What it is for

1. **Daily discharge simulation** for a catchment with forcing but no discharge record, and infilling of gaps in a gauged record.
2. **Antecedent moisture for event design.** AMC I–III is a three-class proxy. [Michel et al. (2005)][michel-2005] analysed the continuous soil-moisture accounting implied by the SCS-CN equation, found "a confusion between intrinsic parameter and initial condition" and proposed a change of parameterisation with a more complete assessment of the initial condition; [Garen and Moore (2005)][garen-moore] list uses and abuses of CN in continuous water-quality modelling. A simulated soil-moisture state can select an AMC class or a retention value for the event module.
3. **Low flows and baseflow.** `stats low-flow` analyses observed series only; a model or a recursive filter (Lyne–Hollick, [Eckhardt 2005][eckhardt-2005], [Ladson et al. 2013][ladson-2013]) adds baseflow indices and an initial baseflow for event hydrographs, which `hydrograph generate` does not include (it returns direct runoff).
4. **Evaluation of what Hydrolog already computes.** Metrics on observed events (peak, time-to-peak and volume errors) need no new model and are the cheapest first step.
5. **Climate sensitivity** (temperature and precipitation deltas), later.

### 4.2 Approaches surveyed

| Approach | Structure | Parameters | Forcing | Reference implementation |
|---|---|---|---|---|
| GR4J / GR5J / GR6J | production store, routing store, two unit hydrographs, groundwater exchange; GR6J adds a store for low flows ([Pushpalatha et al. 2011][pushpalatha-2011]); CemaNeige adds snow ([Valéry et al. 2014][valery-2014]) | 4 (GR4J); median 350 mm, 0 mm, 90 mm, 1.7 d with 80 % intervals 100–1200, −5 to 3, 20–300, 1.1–2.9 ([Perrin et al. 2003][perrin-2003], Table 1) | P, PET (a climatological PET is accepted) | airGR (R, GPL-2) |
| HBV family | snow routine (degree-day), soil routine, response routine with two boxes, triangular routing; elevation and vegetation zones ([Seibert and Vis 2012][seibert-vis-2012]) | 13 in the teaching set: `TT`, `CFMAX`, `SCF`, `CWH`, `CFR`, `FC`, `LP`, `BETA`, `CET`, `K1`, `K2`, `PERC`, `MAXBAS` | P, T, monthly long-term PET | HBV-light; IHMS HBV at IMGW-PIB ([PRRP Kaczawa][prrp-kaczawa]) |
| NAM | surface, root-zone and groundwater stores with snow; MIKE 11 ([Madsen 2000][madsen-2000]) | about 10 ([third-party description][nam-holmes]) | P, PET, T | MIKE (DHI, commercial) |
| Sacramento (SAC-SMA) | upper and lower zone tension and free-water stores | 19 basin parameters plus frozen-ground parameters in the NOAA implementation ([NWS description][sacsma-noaa]) | P, PET | [NOAA-OWP/sac-sma][sacsma-repo] (Apache-2.0, Fortran) |
| TOPMODEL | topographic-index classes; root zone, unsaturated zone, saturated deficit ([Beven et al. 2021][beven-2021], [Beven and Kirkby 1979][beven-kirkby]) | 6 in the classical version: `To`, `m`, `Srmax`, `Sro`, `td`, `Cv` | P, PET, topographic index from a DEM | several |
| SWAT+ | HRUs in landscape units; daily water balance, CN runoff, soil layers, aquifers, snow, channel routing, crops, nutrients, sediment ([SWAT+ repository][swatplus-repo]) | many per HRU, calibrated through multipliers | P, Tmax, Tmin, solar radiation, humidity, wind, or a weather generator ([weather inputs][swatplus-weather]) | Fortran, LGPL-2.1 |
| Continuous SCS-CN | CN with a daily retention parameter from soil water (SWAT+), or a re-parameterised CN with an explicit initial state ([Michel et al. 2005][michel-2005]) | `CN2`, shape of the wet condition, baseflow constant | P, PET | SWAT+ code; Michel et al. 2005 |

Observed in a small experiment (Appendix A8): 500 DDS evaluations of GR4J on synthetic data with 5 % noise reached KGE 0.97 but returned parameters unlike the generating ones. Parameter values from such a calibration are a fit, not a measurement.

### 4.3 SWAT+ concepts: what to borrow

| Concept | SWAT+ formulation | Verdict for Hydrolog |
|---|---|---|
| HRU | a landscape unit is a collection of HRUs ([spatial objects][swatplus-spatial]) | Do not implement the overlay. Accept a table of area fractions per unit, or use sub-catchments. [INTEGRATION.md](../INTEGRATION.md) already assigns the HSG × land-cover intersection to Hydrograf. |
| Daily curve number from soil water | `S = Smax (1 - SW / (SW + exp(w1 - w2 SW)))`, `S ≥ 3 mm`; the shape coefficients make `S` equal the `CN1` retention at wilting point, the `CN3` retention at field capacity and 2.54 mm (CN 99) at saturation ([retention parameter][swatplus-cn]) | L5 only. It is the bridge to the event module, but Garen and Moore's warnings apply. `CN1` and `CN3` differ by convention: for `CN2 = 72` Hydrolog's `SCSCN` (Chow et al.) gives 53.0 and 85.8, SWAT+ ([hydrology page][swatplus-hydrology-draft]) gives 53.4 and 86.9 (D12). |
| PET | Penman–Monteith, Priestley–Taylor or Hargreaves; `λE0 = 0.0023 H0 (Tmx - Tmn)^0.5 (Tav + 17.8)` ([Hargreaves][swatplus-hargreaves]) | Hargreaves–Samani ([1985][hargreaves-1985]) and Oudin ([2005][oudin-2005]); Penman–Monteith ([FAO-56][fao-56]) only with the data of section 3.3. |
| Snow | `SNOmlt = b_mlt sno_cov [(T_snow + T_mx)/2 - T_mlt]` with a seasonal melt factor; rural range 1.4–6.9 mm °C⁻¹ d⁻¹ ([snow melt][swatplus-snow]; temperature-index methods: [Hock 2003][hock-2003]) | Degree-day with a threshold temperature and, optionally, a seasonal factor; elevation zones from the hypsometric curve. |
| Groundwater and baseflow | `Q_gw,i = Q_gw,i-1 exp(-α Δt) + w_rchrg (1 - exp(-α Δt))` above a storage threshold; `α` 0.1–0.3 for slow and 0.9–1.0 for fast response ([baseflow][swatplus-baseflow]) | A linear reservoir: the same recursion as the routing kernel of section 5.2. |
| Channel routing | variable storage (default) or Muskingum; Muskingum steps are sub-divided when `Δt > 2K(1 - X)` ([channels][swatplus-channels-draft]) | Direction B. |
| Reservoirs, ponds, wetlands | level-pool style storage | R4. |
| Crop growth, nutrients, sediment, carbon, pesticides, management | most of the SWAT+ source | Out of scope. |

The official theory page lists a second retention method driven by accumulated plant evapotranspiration; the code-verified draft documentation says SWAT+ 62.0.1 has only the soil-water method. The disagreement is one more reason not to track SWAT+ semantics.

### 4.4 Build versus wrap

State on 2026-10-24 (GitHub API and PyPI):

| Candidate | What it is | Licence | Release and activity | Notes | Verdict |
|---|---|---|---|---|---|
| [SWAT+][swatplus-repo] | Fortran model | LGPL-2.1 | 62.0.1 (2026-10-19), pushed 2026-10-21; 85 stars, 77 open issues | a project is a directory of text input files built beforehand with QSWATPlus | do not wrap |
| [pySWATPlus][pyswatplus] | Python driver of SWAT+: edits `calibration.cal`, runs, computes metrics, sensitivity (SALib), calibration (pymoo) | GPL-3.0-or-later | 1.3.0 (2025-11-16), pushed 2026-04-14 | needs an existing SWAT+ project; Python 3.10–3.13 | no: GPL, and it is a driver, not a model |
| [hydrobricks][hydrobricks] | modular framework, C++ core with Python interface; hydro units from a DEM, glaciers, calibration | MIT | 0.9.3 (2026-10-23); 5 stars, 28 open issues | 56 % Python, 41 % C++; wheels for Linux, macOS arm64, Windows; needs `numpy<2.4`, pandas, YAML project files | cross-check for L4; revisit at 1.0 |
| [RRMPG][rrmpg] | Python models (Numba) | MIT | no releases; pushed 2025-12-11 | not on PyPI under `RRMPG` or `rrmpg`; README: "work in progress" | reference only |
| [SuperflexPy][superflexpy] | framework for lumped and semi-distributed conceptual models ([Dal Molin et al. 2021][dalmolin-2021]) | LGPL-3.0 | 1.3.3 on PyPI (2026-07-03) | needs Numba | reference only |
| [GRsuite][grsuite] | unofficial Python port of airGR (GR4J, GR5J, GR6J, CemaNeige…), "validated against airGR 1.7.9" | GPL-2.0-or-later | 1.1.1 (2026-09-05), 3 releases | needs Numba; one maintainer | development-time cross-check |
| [airGR][airgr] | reference R package of INRAE | GPL-2 | 1.7.9 (CRAN, 2026-07-08) | R | source of cross-check fixtures |
| [Raven][raven] / [RavenPy][ravenpy] | C++ framework with many model structures and routing options / Python wrapper | Artistic-2.0 / MIT | 4.12 (2026-03-05) / 0.21.0 (2026-03-16) | the wrapper needs cf-xarray, climpred, pandas and more | out of reach for a light tool |
| [HEC-HMS][hechms] | Java application with SCS-CN, SMA, Muskingum, Muskingum–Cunge, Modified Puls, Lag, kinematic wave | free installers (4.13 on the download page; documentation of 4.14 dated 2026-09) | current | no source repository found among the first 100 repositories of the HEC GitHub organisation | documentation and tutorial data for cross-checks |
| [spotpy][spotpy] | calibration and uncertainty algorithms (SCE-UA, DDS, DREAM, ...), [Houska et al. 2015][houska-2015] | MIT | 1.6.7 (2026-02-16) | requires `numpy>=2.0`, Hydrolog allows `>=1.24` | optional extra for L6 only |
| [pyet][pyet] | PET methods | MIT | 1.5.0 (2026-05-26) | needs xarray and pandas | not needed; two one-line formulas |
| HydroErr, hydrostats, hydroeval | metrics | MIT, MIT, GPLv3 | 2.0.0 (2025-12), 1.0.0 (2025-12), 0.1.0 (2021) | `hydrostats` needs Numba | formulas are short; use HydroErr as a cross-check |
| [t-route][troute], [mizuRoute][mizuroute], [RAPID][rapid] | network routing engines (Muskingum–Cunge and diffusive wave on a tree; river routing of runoff in a catchment-based vector network; flow and volume in river networks of many thousands of reaches) | Apache-2.0, Apache-2.0, BSD 3-Clause (README badge; no licence in the GitHub metadata) | 2.4.0 (2024-10-02), 3.2.0 (2026-10-03), 1.8.0 (2020-04-24) | continental scale; Fortran and Python | design references only: topological order, lateral inflow per node |

**Measured cost of building.** The GR4J equations of [Perrin et al. (2003)][perrin-2003] (Eqs. 1–23) took 34–42 ms for 30 years of daily data in a plain Python loop (two runs, one core), and 6.4–7.1 ms per parameter set when 100 sets were advanced together with NumPy. Five hundred DDS evaluations on 10 years took 8.5 s. A SWAT-like model over many HRUs is a different order of cost: [INFERENCE] 100 HRUs would need seconds per run even when vectorised across HRUs, which makes calibration impractical without Numba or compiled code. This is the performance argument for keeping the continuous scope lumped (D3).

**Licence.** Hydrolog is MIT ([`pyproject.toml`](../../pyproject.toml)). Importing an LGPL or GPL package into a distributed MIT library constrains users, so such packages are used by the author as *external* cross-checks, never imported by `src/hydrolog`.

**Recommendation: build.** Implement the small models in NumPy and SciPy, with closed-form and cross-checked tests (section 4.9); wrap nothing; offer `spotpy` only as an optional extra if ensembles are wanted (L6).

### 4.5 Data needs per model

| Model | Minimum inputs | Optional | Notes |
|---|---|---|---|
| GR4J | daily P, PET, area | observed Q for metrics | `x4` is a unit-hydrograph time base, so the time step is one day; PET from Oudin needs temperature and latitude |
| HBV-class | daily P, T, monthly PET | elevation zones, observed Q, snow depth | snow-dominated Carpathian and Sudeten catchments need zones and a lapse rate |
| Continuous SCS-CN | daily P, PET, `CN2`, soil water capacity | slope adjustment, frozen-soil factor | needs soil properties of section 3.3 |

### 4.6 Calibration and evaluation

- **Metrics.** Nash–Sutcliffe efficiency ([1970][nash-sutcliffe]), Kling–Gupta efficiency ([Gupta et al. 2009][gupta-2009]) and its modified form ([Kling et al. 2012][kling-2012]), NSE of log flows for low flows, percent bias, RMSE, relative volume error, and for events the peak, time-to-peak and volume errors. The result reports the components of KGE (correlation, variability ratio, bias ratio).
- **Benchmarks, not thresholds.** The mean observed flow gives NSE = 0 and KGE = 1 − √2 ≈ −0.41 ([Knoben et al. 2019][knoben-2019]; the arithmetic was reproduced, Appendix A9). [Clark et al. (2021)][clark-2021] caution against abuse of such metrics. The result carries the benchmark value next to the score; ratings from [Moriasi et al. (2015)][moriasi-2015] (for watershed flow, NSE above 0.50 is "satisfactory", above 0.70 "good", above 0.80 "very good") may be offered as an informational field, never as pass or fail.
- **Procedure.** A warm-up period is excluded from the score; calibration and validation periods follow the split-sample idea of [Klemeš (1986)][klemes-1986]; both scores are returned, and a validation score far below the calibration score is a notice.
- **Algorithms.** Dynamically dimensioned search ([Tolson and Shoemaker 2007][dds]) is designed for a limited evaluation budget and has one parameter; implement it first. SCE-UA ([Duan et al. 1992][sceua]) is the long-standing hydrological choice and can follow. `scipy.optimize.differential_evolution` is available now as a cross-check.
- **Equifinality.** The result lists parameters at their bounds, returns the highest-scoring parameter set together with the validation score, and never states that parameters were "recovered" (Appendix A8).
- **Budget.** At 17–42 ms per evaluation, 1,000 evaluations take 17–42 s. MCP calls need progress notifications ([AGI-5.11][agi-std]) and a cap on `max_evaluations`; `workers` ([AGI-3.4][agi-std]) parallelises across processes.
- **Determinism.** A `seed` option, recorded in the result.

### 4.7 Fit with the event-based design

The event module answers "what hydrograph follows from this design rainfall"; a continuous model answers "what flows and states follow from this weather series". They meet in three places: the AMC/retention state before an event, the baseflow added to a direct-runoff hydrograph, and the metrics that compare either with observations. Nothing in the continuous scope changes `hydrograph generate`. In Polish practice (section 3.2) the continuous model is supporting evidence next to the statistical design flow, and the documentation must say so.

### 4.8 Architecture and public API

**Packages** (library classes, class-based like the rest of Hydrolog; operations in `hydrolog.operations` as for every command):

```
src/hydrolog/
├── evaluation/   metrics.py  split.py  baseflow.py        # L1
├── processes/    pet.py  snow.py  forcing.py              # L2  (areal series, lapse rate, elevation zones)
└── simulation/   gr.py  hbv.py  cn_continuous.py          # L3, L4, L5
                  calibration.py                           # DDS, SCE-UA, differential evolution adapter
```

**Commands** (names are proposals; D13):

| Command | Phase | Purpose |
|---|---|---|
| `metrics evaluate` | L1 | NSE, KGE (+ components), KGE′, log-NSE, PBIAS, RMSE, volume error, event peak/time/volume errors for two aligned series or files |
| `baseflow separate` | L1 | Lyne–Hollick or Eckhardt filter; baseflow index |
| `pet oudin`, `pet hargreaves` | L2 | daily PET series from temperature and latitude |
| `snow degree-day` | L2 | snow storage and melt from precipitation and temperature, optionally by elevation zone |
| `precip areal-series` | L2 | daily areal precipitation from several gauge series with Thiessen or IDW weights computed once |
| `simulate gr4j` | L3 | daily simulation with given parameters (GR5J and GR6J as an option) |
| `calibrate run` | L3 | DDS (later SCE-UA) for a chosen model, objective, periods, bounds |
| `simulate hbv` | L4 | snow + soil + response + triangular routing, elevation zones |
| `simulate scs-cn` | L5 | daily soil-moisture CN model with baseflow reservoir |

**Inputs.** Forcing is one file with a date column and named value columns (`precipitation_column`, `temperature_column` or `pet_column`), observed discharge a second file (`observed_file`, `observed_column`), both loaded with the existing readers and joined by date; the catchment comes from `watershed_file` plus `area_km2`; `latitude_deg` becomes an optional field of `WatershedParameters` (additive, so the schema number stays, [AGI-4.1][agi-std]). Dates must be strictly daily and aligned; gaps are a `data_error` with `details.reason = "gaps"` and the first gaps listed (D7 decides whether a fill option is wanted).

**Results.** Series go to `output` (CSV with `date`, `Q_sim_m3s`, state columns), the envelope carries `files[]`, the water balance, the runoff coefficient, the metrics, the warm-up used and notices (`short_warmup`, `parameter_at_bound`, `validation_worse_than_calibration`, `pet_climatology`). Result schema ids follow `hydrolog-<group>-<verb>/1`; the schemas are generated by `scripts/generate_result_schemas.py`.

**Python sketch** (not implemented):

```python
from hydrolog.simulation import GR4J

model = GR4J(x1_mm=350.0, x2_mm_per_d=0.0, x3_mm=90.0, x4_d=1.7)
run = model.run(precipitation_mm=p, pet_mm=e, warmup_days=365)   # NumPy arrays, daily
run.discharge_mm                                                  # mm/d; run.discharge_m3s(area_km2=45.3)
```

**CLI sketch** (flags follow [AGI-3.4][agi-std] and Hydrolog's units-in-names rule):

```bash
hydrolog calibrate run --model gr4j --forcing-file forcing.csv --date-column date \
  --precipitation-column P --temperature-column Tmean --latitude-deg 50.06 --area-km2 45.3 \
  --observed-file q_daily.csv --observed-column Q --objective kge --algorithm dds \
  --max-evaluations 1000 --seed 1 --calibration-start 2005-11-01 --calibration-end 2012-10-31 \
  --validation-start 2012-11-01 --validation-end 2016-10-31 --output calibration.json --json
```

### 4.9 Test strategy for Direction A

| Layer | Checks | Reference |
|---|---|---|
| Closed form | GR4J S-curves `SH1`, `SH2` (Perrin Eqs. 9–15) and unit-hydrograph ordinates; one step of the production store from Eqs. 3–7 by hand; store never above its capacity; mass balance `ΣP − ΣE_actual − ΣQ − ΔS = 0` to 1e-9; constant input gives the analytic steady state | [Perrin et al. 2003][perrin-2003] |
| Metrics | identities: perfect fit = 1; mean-flow predictor gives NSE = 0 and KGE = 1 − √2; scaling and shift behaviour of `α`, `β` | [Knoben et al. 2019][knoben-2019] |
| Cross-check | identical forcing and parameters through airGR (R) and, as a second opinion, GRsuite; compare series to 1e-6 relative; fixtures generated by a script that records package versions and seeds. Whether fixtures derived from GPL code may be committed is D11. | [airGR][airgr], [GRsuite][grsuite] |
| Calibration | determinism for a seed; bounds respected; evaluation budget respected; the calibrated score is not worse than the start; *performance* (not parameter) recovery on synthetic data | Appendix A8 |
| Real data | a three-year IMGW series (precipitation and temperature from a climate station, discharge from a gauge) as a smoke and regression fixture with the IMGW attribution columns kept, as the existing `imgwtools_series_export.csv` does | [`tests/fixtures`](../../tests/fixtures/) |
| Contract | every command's examples run; schemas validate; guide budget; MCP tool names and descriptions | existing contract tests |

## 5. Direction B: flood routing

### 5.1 Scope and boundary

Hydrologic routing is adequate where the flood wave is attenuated and delayed by storage and diffusion, backwater is absent, and the answer wanted is a discharge hydrograph. Hydraulic modelling is needed when levels, inundation extents, backwater, bridges and culverts, dam breaks or flat gradients decide the result. The NRCS handbook says so for its own method: the Muskingum–Cunge warning limit "occurs mostly on long flat reaches"; the recommended actions are to rerun with an unsteady flow model such as HEC-RAS or to treat the reach as a storage reach ([NEH-630 ch. 17][neh17], appendix B). `route muskingum-cunge` therefore reports the same accuracy check as a notice (section 5.3), and the documentation names Hydraulik, HEC-RAS and IMGW HD as the next tools.

### 5.2 Methods

| Method | Recurrence or relation | Parameters | Use and limits | In Hydrolog |
|---|---|---|---|---|
| Lag | `O_t = I_(t-lag)`; no attenuation ([HEC-HMS][hec-lag]) | `lag_min` | short reaches with a predictable travel time | none |
| Linear reservoir | `S = K O`; `O_t = O_(t-1) + C (I_t + I_(t-1) - 2 O_(t-1))`, `C = Δt / (2K + Δt)` | `k_min` | ponds, flat wide floodplains, reaches controlled from downstream ([HEC-HMS Modified Puls][hec-puls]); catchment storage (Clark) | private in `ClarkIUH` |
| Cascade of `n` linear reservoirs | `u(t) = (t/K)^(n-1) exp(-t/K) / (K Γ(n))`; the Kalinin–Milyukov method of the Soviet Union is the same idea with a *characteristic reach length* `Δx_c = q / (S0 c)`, which is Cunge's expression with `X = 0`, and `n = L / Δx_c` ([Ponce][ponce-linear-reservoirs]) | `n`, `k_min` | reach routing with an analytic kernel, so no explicit time-stepping limit [INFERENCE: not tested here] | `NashIUH` |
| Muskingum | `S = K [X I + (1 - X) O]`; `O_t = C0 I_t + C1 I_(t-1) + C2 O_(t-1)` with `C0 = (Δt - 2KX) / D`, `C1 = (Δt + 2KX) / D`, `C2 = (2K(1 - X) - Δt) / D`, `D = 2K(1 - X) + Δt` ([HEC-HMS][hec-musk]) | `k_min`, `x` in [0, 0.5], sub-reaches `N` | `K` and `X` come from inflow–outflow hydrographs; "good for the reach and event used for calibration; poor for any other reach or flood event" ([Ponce 2020][ponce-mc]) | none |
| Muskingum–Cunge, constant coefficients | same recurrence; `K = Δx / c`, `X = ½ (1 - Q / (B S0 c Δx))`, `Δx = ½ (c Δt + Q / (B S0 c))` for the reference discharge `Q` (the inflow peak in NRCS WinTR-20) ([NEH-630 ch. 17][neh17]) | length, slope, Manning `n`, section shape, reference discharge | ungauged reaches; volume-conserving; `X` may be negative; accuracy check `Dg ≤ exp(2.3 Cg)` | none |
| Muskingum–Cunge, variable parameters | coefficients recomputed each step from the current discharge ([Ponce and Yevjevich 1978][ponce-yevjevich]) | as above | "small but perceptible" loss of mass ([Ponce and Chaganti 1994][ponce-vp-revisited]) | none |
| Level-pool (Modified Puls, storage-indication) | `(S_t/Δt + O_t/2) = (I_(t-1) + I_t)/2 + (S_(t-1)/Δt - O_(t-1)/2)` with `S = f(O)` ([HEC-HMS][hec-puls], [NEH-630 ch. 17][neh17]) | storage–outflow table, sub-reaches `N` | reservoirs and ponds; channel reaches with a tabulated storage curve | none |
| Kinematic wave | `∂Q/∂t + c ∂Q/∂x = 0` | geometry | steep reaches and overland flow; "Kinematic waves do not attenuate" ([Ponce 2020][ponce-mc]), apart from numerical diffusion | not proposed now (D2) |
| Diffusive and dynamic wave | Saint-Venant equations | cross-sections | hydraulics | Hydraulik, HEC-RAS, IMGW HD |

SWAT+ uses a variable-storage method by default and Muskingum as an option ([channels][swatplus-channels-draft]); the variable-storage form is a level-pool variant and is not proposed.

### 5.3 Numerical stability rules

| Scheme | Rule | Evidence | Proposed policy |
|---|---|---|---|
| Muskingum | all three coefficients are non-negative exactly when `|2KX| ≤ Δt ≤ 2K(1 - X)`; for `0 ≤ X ≤ 0.5` this reads `2KX ≤ Δt ≤ 2K(1 - X)`. A frequently quoted sufficient form is `K > Δt > 2KX` ([lecture note][nptel-lec45]). | derived from the coefficients; checked for X = 0, 0.15, 0.25, 0.5 and −0.254 (Appendix A6). SWAT+ clips `C1 ≥ 0`, rescales the coefficients to sum to 1 and sub-divides the step when `Δt > 2K(1 - X)` ([channels][swatplus-channels-draft]). | compute the window for `K/N`; with `subreaches` omitted choose `N = max(1, round(K/Δt))` so that the travel time per sub-reach is about `Δt` ([HEC-HMS][hec-musk]) and reduce `N` until the window holds; report `substeps_added` as a notice. An explicit `subreaches` outside the window is a `validation_error` with `details.reason = "unstable_timestep"`. `X = 0.5` requires `K = NΔt` (pure lag). |
| Sub-reaches | for fixed `X`, `N` equal sub-reaches of `K/N` have mean delay `K` and variance `K²(1 - 2X)/N`; more sub-reaches mean less attenuation ([HEC-HMS][hec-musk]) | exact in the discrete scheme to three decimals (Appendix A5) | document `N` as an attenuation parameter for Muskingum; in Muskingum–Cunge `X` is recomputed per sub-reach, which keeps the total variance independent of `N` (Cunge's numerical-diffusion argument, [NEH-630][neh17]) |
| Linear reservoir | the weight on `O_(t-1)` is `(2K - Δt)/(2K + Δt)`, negative for `Δt > 2K` | `ClarkIUH(tc_min=60, r_min=2).generate_iuh(timestep_min=5)` returns a negative ordinate (−0.00031 per minute) | refuse `timestep_min > 2 k_min` or add sub-steps; fix the Clark guard in the same change (finding F1) |
| Level-pool | "negative outflows will occur on the recession side whenever `Δt` is greater than `2 S2/O2`" (equivalently `O/2 > S/Δt`); if any part of the working curve falls left of the line of equal values, discard it and use a smaller `Δt` ([NEH-630][neh17]). For channels: `Tt/Tp ≲ 0.5` and `Δt < Tt`; the number of sub-reaches is `L / (c Δt)` ([HEC-HMS][hec-puls]) | NEH-630 example 17-1 follows these rules (`Tt/Tp = 0.4`, `Δt = 0.5 h < Tt = 0.813 h`) | validate the working curve before the run; if it fails, refine `Δt` internally (WinTR-20 does the same), interpolate back and report `timestep_refined`; storage and outflow must be non-decreasing |
| Muskingum–Cunge | accuracy limit: with the Courant number `Cg = c Δt / Δx` and the grid Reynolds number `Dg = Q / (T S0 c Δx) = 1 - 2X`, results may be inaccurate when `Dg > exp(2.3 Cg)`; typical on long flat reaches ([NEH-630][neh17], appendix B). Rise-time rule: at least 10 steps between 5 % of the peak and the peak, else interpolate to a finer step and back. Ponce: strongly stable and convergent for Courant numbers near 1 ([Ponce 2020][ponce-mc]) | example 17-4: `Cg = 0.595`, `Dg = 1.508`, limit 3.93: within limits (Appendix A2) | notice `accuracy_limit` (never an error); automatic refinement for the rise-time rule; positivity window as for Muskingum with `X` possibly negative |
| Variable-parameter M-C | mass is not conserved exactly | [Ponce and Chaganti 1994][ponce-vp-revisited] | constant coefficients first (R2); variable parameters later report the volume error in the result |
| All | outflow ≥ 0; volume balance `ΣI − ΣO − ΔS` reported; the outflow lasts longer than the inflow, so the series is extended by `extend_min` (default: until below 0.1 % of the peak or a cap) and the extension is reported; initial condition: outflow = inflow (steady state, as in HEC-HMS) unless `initial_outflow_m3s` is given | HEC-HMS initial-condition options ([Muskingum][hec-musk]) | `tail_extended` notice |

### 5.4 Network composition

**Model.** A directed acyclic graph. Node types: `subcatchment` (a source hydrograph), `reach` (any method of 5.2), `junction` (sum), `reservoir` (level-pool) and `outlet`; diversions and bifurcations are a later extension. Every node lists its upstream nodes, which is the convention of `StreamSegment.upstream_ids`; evaluation follows the topological order of the existing `StreamNetwork` code, with its cycle and unknown-id errors. The same upstream-to-downstream rule underlies t-route ("all routing computations strictly obey an upstream-to-downstream ordering", [t-route][troute]) and mizuRoute (runoff or lateral inflow from a hydrologic model routed through rivers, lakes and reservoirs, [mizuRoute][mizuroute]).

**Input** (`hydrolog-network/1`, a JSON file; a sketch is in Appendix B). Source nodes either carry `watershed` parameters (the same fields as `hydrograph generate`, evaluated with the command's rainfall options) or point to a column of an `inflows_file`; rainfall options of `hydrograph generate` apply to all sources.

**Mapping from Hydrograf.** `stream_catchments` rows (area, mean slope, `downstream_segment_idx`) become `subcatchment` nodes feeding the upstream end of their segment; `stream_network` rows (`length_m`, `mean_slope_percent`) become `reach` nodes; the downstream index becomes the `from` lists ([data model][hydrograf-data-model]). Hydrolog never reads PostGIS or rasters for this.

**Time step.** One time step per run; source and file hydrographs must share it (`validation_error`, `details.reason = "timestep_mismatch"`); resampling is a decision (D7).

**Output.** Per node: `peak_m3s`, `time_to_peak_min`, `volume_m3`; the hydrographs of the requested nodes in one CSV (`time_min` plus one column per node, the shape SFINCS point-discharge forcing needs after a unit conversion, [SFINCS manual][sfincs-forcing]).

**Assumptions to state in the documentation.** Uniform rainfall over the whole network (as in [SCOPE.md](../SCOPE.md) §5.1), lumped inflow at the upstream end of a reach, no lateral inflow along the reach, no losses. The 250 km² limit of SCS-CN ([Hydrograf scope][hydrograf-scope]) then applies per sub-catchment, which is a policy decision (D8).

### 5.5 Parameters from the DEM and channel geometry

1. **Reach length and slope** from the Kartograf DEM through Hydrograf (`length_m`, `mean_slope_percent`). Slope over short reaches from a 1 m DEM is noisy; the documentation advises a minimum reach length and smoothing. [INFERENCE: not measured here.]
2. **Cross-section.** A DEM does not see below the water surface, so width, depth and side slopes come from the user, from a hydraulic model or from regional relations. Power laws of drainage area exist for the United States ([Leopold and Maddock 1953][leopold-maddock], [Bieger et al. 2015][bieger-2015]); no Polish regional relations were found. Whatever is used is flagged `approximate` in the result.
3. **Roughness.** `manning_n` is already a field of `WatershedParameters`; reach tables by channel type are the user's input.
4. **Rating and celerity.** Manning's equation on a trapezoid gives `Q(y)`, `A(y)`, `B(y)`; the celerity is `c = dQ/dA` ([HEC-HMS][hec-mc]); NRCS writes it as `c = m Q / A` with `m` the log-log slope of the `Q`–`A` curve (example 17-4: `m = 1.3873`, `c = 4.297 ft/s`).
5. **`K`, `X`, `Δx`** as in 5.2. The reference discharge is the inflow peak (NRCS) or `Q0 = Q_base + ½ (Q_peak − Q_base)` (EM 1110-2-1417, [HEC-HMS][hec-mc]).
6. **Sensitivity** [INFERENCE]: `c` scales with `S0^(1/2) / n`, so a 20 % error in `n` changes `K` by about 20 % and a 20 % error in slope by about 10 %. Parameters estimated from geometry are priors; observed inflow–outflow pairs improve them, and the calibration engine of section 4.6 can fit `K`, `X` and `N` to an observed outflow (a synergy of the two directions: the engine is model-agnostic).

### 5.6 Reservoirs

Level-pool routing needs a storage–outflow relation. Storage comes from a stage–area table (the dry basin from DEM hypsometry; the bathymetry of an existing reservoir is missing) and outflow from outlet ratings: an orifice or bottom outlet and a spillway, summed above their crests; [NEH-630 example 17-2][neh17] shows the construction from a contour map and a spillway rating. Dry flood-control reservoirs are among the measures assessed in the Kaczawa programme ([PRRP Kaczawa][prrp-kaczawa]: for the September 2024 flood the computed outflow of the reservoir "Rzymówka" would not exceed the permitted outflow; the report gives the maximum computed upper level and filling). R4 adds `route outlet-rating` and warnings for stage above the table or above the dam crest. Gate operation, release rules and dam break are not proposed (hydraulics or operations).

### 5.7 Architecture and public API

```
src/hydrolog/routing/
├── _kernels.py     recurrences shared by Clark, Muskingum and the cascade (replaces ClarkIUH._route_linear_reservoir)
├── lag.py  muskingum.py  cunge.py  cascade.py  level_pool.py
├── reach.py        shapes (rectangle, trapezoid, triangle), Manning rating, celerity, K and X
├── structures.py   orifice and weir ratings, stage–storage from a table or the hypsometric curve   (R4)
└── network.py      RoutingNetwork: nodes, links, evaluation order over network.StreamNetwork       (R3)
```

**Commands** (names are proposals; D13):

| Command | Phase | Main options | Result (`hydrolog-route-<verb>/1`) |
|---|---|---|---|
| `route lag` | R1 | hydrograph input, `lag_min` | outflow, shift applied, interpolation notice |
| `route cascade` | R1 | `n` and `k_min`, or `length_km` and `celerity_m_per_s` | weights, outflow, `n`, `k_min` |
| `route muskingum` | R1 | `k_min`, `x`, `subreaches`, `initial_outflow_m3s`, `extend_min` | coefficients, stability window, peaks, attenuation, volumes, balance |
| `route level-pool` | R1 | `storage_m3` and `discharge_m3s` lists or `rating_file`, initial state, `subreaches` | outflow, storage series, maximum storage, working-curve check |
| `route muskingum-cunge` | R2 | geometry (`length_km`, `slope_m_per_m`, `manning_n`, `shape`, widths and depths), `reference_discharge_m3s`, `parameters` (constant or variable) | as Muskingum plus `celerity_m_per_s`, `dx_m`, Courant and grid Reynolds numbers, `within_accuracy_limit` |
| `route reach-params` | R2 | geometry or `watershed_file`, `discharge_m3s`, `timestep_min` | celerity, travel time, `K`, `X`, `Δx`, stability window (no series) |
| `route network` | R3 | `network_file`, rainfall options or `inflows_file`, `nodes`, `output` | per-node summary and `files[]` |
| `route outlet-rating` | R4 | stage–area table, outlet definitions | stage–storage–discharge table |

All time inputs accept an `input_file` with `time_min` and a value column (or a dated series), or inline `times_min` and `discharge_m3s` (`one_of`); results above the page budget require `output` ([ADR-0003](../decisions/0003-writing-commands-output-force-check.md)). `hydrograph generate` gains `output` so that its hydrograph can feed `route *` without pasting arrays. Library classes follow the existing style (`SCOPE.md` §3.3):

```python
from hydrolog.routing import Hydrograph, MuskingumReach, LevelPool

inflow = Hydrograph(times_min=t, discharge_m3s=q)            # regular step required
outflow = MuskingumReach(k_min=138.0, x=0.15).route(inflow)  # N chosen automatically; notices attached
pond = LevelPool(storage_m3=[0, 5e4, 2e5], discharge_m3s=[0, 1.5, 9.0]).route(inflow)
```

### 5.8 Test strategy for Direction B

| Layer | Checks | Reference |
|---|---|---|
| Public-domain worked examples | NEH-630 example 17-1 (storage-indication; reproduced to 0.85 ft³/s), example 17-4 (constant-coefficient Muskingum–Cunge, `K = 605.07 s`, `X = −0.254`; reproduced to 0.24 ft³/s; peak 645.7 ft³/s at 13.1 h against 647 ft³/s from HEC-RAS in the same chapter), example 17-5 for R2b | [NEH-630 ch. 17][neh17]; works of the US federal government are not copyrighted in the United States ([17 U.S.C. § 105][us-copyright]) |
| Handout example | Muskingum, `K = 20 h`, `X = 0.25`, `Δt = 12 h` (reproduced to 0.05 cfs) | [University of Iowa][iowa-musk] |
| Identities | Muskingum with `X = 0.5` and `K = Δt` is a lag of one step ([HEC-HMS Lag][hec-lag]); with `X = 0` it is the Clark linear-reservoir scheme (exact, Appendix A4); `N` sub-reaches in series equal a network of `N` reaches; the cascade kernel equals `NashIUH` | Appendix A |
| Moments | mean delay `K`, variance `K²(1 − 2X)/N` for a pulse | Appendix A5 |
| Analytic | linear-reservoir step response `1 − exp(−t/K)` with an error bound that falls with `Δt`; grid independence of Muskingum–Cunge (halving `Δt` and `Δx` near `Cg = 1` changes the peak by less than a set tolerance) [tolerance to be fixed in the plan] | [Ponce 2020][ponce-mc] |
| Invariants | non-negative outflow; volume balance (exact for constant coefficients and level-pool; documented tolerance for variable parameters); time-shift invariance; superposition for the linear schemes; steady state preserved | |
| Network | one-reach network equals the single command; node order in the file does not change results; series equivalence; junction sums; cycle, unknown id, two outlets and disconnected node are errors | existing `StreamNetwork` errors |
| Cross-check (development only) | HEC-HMS runs of the tutorials "Applying the Lag / Muskingum / Muskingum–Cunge Routing Method" and a toy network in t-route or mizuRoute; not in the gate | [HEC-HMS][hec-mc], [t-route][troute] |
| Contract | examples run, schemas validate, guide budget, MCP names | existing contract tests |

## 6. Cross-cutting design

### 6.1 Time axes and file formats (D7)

| Format | Columns | Used by |
|---|---|---|
| Hydrograph table, event scale | `time_min` (elapsed, regular step), `discharge_m3s` (one column per node in network output) | `route *`, `hydrograph generate --output`, hand-off to Hydraulik |
| Dated series, daily | `date` plus value columns; IMGWTools names such as `Q [m3/s]` stay | `stats *`, `metrics evaluate`, `simulate *`, `calibrate run` |
| Network | `hydrolog-network/1` JSON | `route network`; written by Hydrograf |
| Forcing | dated CSV with `P`, `T`, optional `Tmin`, `Tmax`, `PET` | `simulate *`, `pet *`, `snow *` |

Time quantities are minutes (`k_min`, `lag_min`, `timestep_min`) for event routing, as everywhere in Hydrolog, and days for the daily models (`x4_d`, `warmup_days`); series of one run must not mix the two conventions.

### 6.2 Agent-guide, MCP and result budgets (D10)

| Item | Today | After the 18 commands of this report |
|---|---|---|
| Commands, groups | 38, 14 | 56, 21 (new groups: `route`, `metrics`, `baseflow`, `pet`, `snow`, `simulate`, `calibrate`) |
| `AGENTS.md` | 164 lines, 16,073 bytes (limit 200 and 16,384) | about 189 lines and 18,460 bytes: the line limit holds, the byte limit is exceeded by about 2.1 KB (18 commands × 116 bytes + 7 headings × 44 bytes, the means of the current index) |
| `core` family | 9 of 10 | unchanged |
| MCP instructions | built from the catalog, limit 4,096 characters | unchanged in structure; the text names groups, not commands |

Options: (a) shorten the summaries and compress the three typical flows (3,613 bytes now) to make room; (b) print one line per group for groups of five or more commands and leave the detail to `commands list` and `commands schema` (this departs from "one line per command", [DOC-4.2][doc-std], and is recorded in `CLAUDE.md` as a deviation); (c) ask Nogat to raise the budget (limits are stated only in DOC-1.7). Recommendation: (a) now; (b) or (c) only if (a) cannot hold after R3. Long operations (`calibrate run`, `route network` on large networks) send progress notifications when the client provides a token ([AGI-5.11][agi-std]); `max_evaluations` is capped.

### 6.3 Compatibility and documentation

All additions are minor-version changes within 1.x: new commands, new optional fields (`latitude_deg` in `WatershedParameters`, `output` in `hydrograph generate`), new result schemas, new `details.reason` values. Each phase updates [COMPUTATION_PATHS.md](../COMPUTATION_PATHS.md) with a computation-paths section (which parameter estimators may feed which model, in the style of its existing warnings), [INTEGRATION.md](../INTEGRATION.md) (Hydrograf network, Hydraulik hand-off), [USAGE.md](../USAGE.md) (examples that the gate runs), the CHANGELOG and, after D1, [SCOPE.md](../SCOPE.md) and [PRD.md](../PRD.md).

## 7. Phased roadmap and effort

Effort is in focused working days with agent assistance and does not include the author's review time. Calibration from the history of this repository: statistics and hydrometrics (v0.7.0: two packages, about 2,600 lines) have plan and specification files dated 2026-03-26, and their scaffold, seven modules, plots, documentation, review fixes and merge are 17 commits dated 2026-03-27 (`git log`). A command of the present catalog costs more than a module of that time: a bilingual declaration (about 130 lines on average), an operation, a result schema, examples that run in the contract tests, tests and documentation. The estimates below assume 0.5–1 day per command plus the shared work of each phase.

### 7.1 Phases

| Phase | Content | Days | Depends on | Exit criterion |
|---|---|---|---|---|
| R0 | ADR for D1; plan in `docs/plans/` with file formats (hydrograph table, network JSON), stability policy (D9), names (D13), guide budget (D10) | 1 | D1, D7, D9, D10, D13 | plan carries `Approved: <date>` |
| R1 | `hydrolog.routing` kernels; `route lag`, `route cascade`, `route muskingum`, `route level-pool`; hydrograph table I/O; `hydrograph generate --output`; `ClarkIUH` moved onto the shared kernel with the `Δt ≤ 2R` guard | 3–4 | R0 | NEH-630 example 17-1 within 1 ft³/s (published values are rounded), Iowa example, identity and moment tests, contract tests, USAGE examples, CHANGELOG |
| R2 | section shapes, Manning rating, celerity, constant-coefficient Muskingum–Cunge with distance steps, accuracy check, rise-time refinement; `route muskingum-cunge`, `route reach-params` | 3–4 | R1 | NEH-630 example 17-4 within 0.5 ft³/s; notices `accuracy_limit`, `timestep_refined` |
| R2b | variable-parameter Muskingum–Cunge, tabular and eight-point sections, floodplain (example 17-5) | 2–3 | R2 | optional |
| R3 | `RoutingNetwork` and `route network`; `hydrolog-network/1`; Hydrograf mapping and Hydraulik hand-off in INTEGRATION.md | 5–7 | R1, R2 | tests of 5.8; sample network fixture |
| R4 | `route outlet-rating`, stage–storage from a table or the hypsometric curve, reservoir node in the network, dry-reservoir example | 3 | R1, R3 | rating checked against hand calculation; mass balance |
| L0 | ADR; plan with D3–D7, D11, D12; forcing and result formats | 1 | D1 | approved plan |
| L1 | `metrics evaluate`, `baseflow separate`, join of dated series from several files, gap errors, warm-up and split helpers, event metrics | 3–4 | L0 | closed-form tests; usable on `hydrograph generate` output |
| L2 | `pet oudin`, `pet hargreaves`, `snow degree-day`, `precip areal-series`, `latitude_deg`, elevation zones from the hypsometric curve | 4–5 | L1, D5 | PET against published example values; snow mass balance |
| L3 | `simulate gr4j` (GR5J, GR6J optional), `calibrate run` with DDS, `workers`, progress, validation period | 7–9 | L2 | closed-form tests; cross-check against airGR or GRsuite; 30-year run under 50 ms |
| L4 | `simulate hbv` with elevation zones; bounds from the HBV-light table | 6–8 | L3 | cross-check against hydrobricks or HBV-light (development only) |
| L5 | `simulate scs-cn`: daily soil-moisture CN, soil properties by pedotransfer, aquifer reservoirs, HRU table, network integration | 8–10 | L4, R3, D3, D8, D12 | decided after L4 with a real use case |
| L6 | ensembles, GLUE, climate deltas; optional `spotpy` extra | 5–7 | L3 | |
| G | guide-budget work and documentation infrastructure | 1–2 | D10 | `AGENTS.md` within budget with the new commands |

Totals: R0–R4 15–19 days (17–22 with R2b), L0–L4 21–27, L5–L6 13–17, G 1–2.

### 7.2 Order and dependencies

Recommended order: **R0, R1, L0, L1, R2, R3, L2, L3, R4, L4**, then R2b, L5 and L6 as needed.

```
R0 ── R1 ── R2 ── R3 ── R4
       │            ╲
L0 ── L1 ── L2 ── L3 ── L4 ── L5 ── L6        R3 + L5 = semi-distributed continuous model
```

Routing comes first because its method set is closed, its numerical rules and reference data are documented, and it has no data gap. L1 follows R1 immediately because metrics validate routing against observed hydrographs and are useful for the event module on their own. L2 and L3 wait for D5 and D7. The guide-budget decision (D10) has to be made before R1 ends, when the first new commands appear.

## 8. Risks

| ID | Risk | Effect | Mitigation |
|---|---|---|---|
| K1 | Scope creep towards a SWAT clone or into hydraulics | years of work, shallow results | D1 states non-goals in an ADR; L5 is a separate decision after L4 |
| K2 | Calibrated parameters read as physical truth (equifinality, Appendix A8) | wrong decisions from "the parameters of the catchment" | result carries the validation score, KGE components, parameters at bounds; wording in COMPUTATION_PATHS.md |
| K3 | Continuous CN misused ([Garen and Moore 2005][garen-moore]) | biased runoff | L5 only, labelled experimental until validated on Polish gauges |
| K4 | Routing instability, negative flows, mass loss | unusable hydrographs | stability policy of 5.3; non-negativity and balance checks in every result; tests of 5.8 |
| K5 | Guide, MCP and result budgets exceeded | contract test fails; clients truncate | D10; long series to files; `--tools` families |
| K6 | Data licences and provenance (IMGW terms, SoilGrids, NRCS, GPL-derived fixtures) | blocked release | attribution columns kept; NRCS data are US federal works; D11 for GPL-derived numbers |
| K7 | Pure-Python speed for HBV zones or HRUs | calibration too slow | vectorise over zones; cap evaluations; optional Numba extra (D6) |
| K8 | Unit and time-step confusion (minutes, hours, days; mm per day against m³/s) | silent errors | units in option names; one time convention per run; explicit `area_km2` conversion; mismatch is an error |
| K9 | Mismatch with Polish practice: design flows are statistical | results misused | documentation states the role (3.2); no claim of compliance with the national methodology |
| K10 | Maintenance burden of many models | stale code | short model list (GR4J family, HBV-class); reference-data tests; no model zoo |
| K11 | Cross-project coordination (Hydrograf scope, IMGWTools requests, Hydraulik format) | work waits | `request` issues after D1 ([DEV-17.5][dev-std]); formats versioned (`/1`) |
| K12 | Long MCP calls time out | failed tool calls | progress notifications, `max_evaluations` cap, `--check` plans |

## 9. Not recommended, and what covers it

| Item | Reason | Covered by |
|---|---|---|
| Wrapping SWAT+ or importing pySWATPlus | Fortran model with a text-file project; GPL-3.0-or-later driver; outside the "files in, numbers out" design | users run SWAT+ themselves; Hydrolog's metrics can score its output |
| HRU overlay, crop growth, nutrients, sediment, carbon, management | the bulk of SWAT+; needs data Hydrolog does not have | SWAT+ |
| Kinematic wave, diffusive and dynamic wave, inundation, dam break | hydraulics | Hydraulik, HEC-RAS, IMGW HD |
| Gate operation and release rules of reservoirs | operations research, not routing | out of scope until a use case exists |
| NAM, Sacramento, TOPMODEL, a model zoo | proprietary (NAM), many parameters (Sacramento), needs a topographic index (TOPMODEL); GR4J and HBV cover the lumped need | cross-check with their open implementations if ever needed |
| Real-time forecasting and data assimilation | different architecture and responsibility | IMGW-PIB operational systems |
| Green–Ampt infiltration | already out of scope in SCOPE.md §2.2; needs sub-daily rainfall | not planned |

## 10. Decisions for the author

| ID | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| D1 | Scope change of [SCOPE.md](../SCOPE.md) §2.2 and §2.3 (routing, reservoir routing, snow and groundwater as conceptual stores, PET, calibration) | yes, limited to lumped hydrologic methods / routing only / neither | yes, with non-goals of section 9, recorded in an ADR | everything |
| D2 | Order and funding | section 7.2 / continuous first | section 7.2 | schedule |
| D3 | Depth of continuous modelling | lumped conceptual only / add a SWAT-like HRU model | lumped; decide L5 after L4 | L5 |
| D4 | First models | GR4J (+GR5J, GR6J) and an HBV-class model; CemaNeige or degree-day for snow | GR4J and HBV-class; degree-day snow; GR5J and GR6J on request | L3, L4 |
| D5 | PET policy | Oudin and Hargreaves–Samani only / add Penman–Monteith after IMGWTools supports daily synoptic data | Oudin and Hargreaves–Samani now; open a low-priority `request` at IMGWTools | L2 |
| D6 | Dependencies | NumPy and SciPy only / optional Numba extra / optional `spotpy` extra | NumPy and SciPy; revisit Numba only if HBV zones or HRUs make calibration slow; `spotpy` only for L6 | L3, L4, L6 |
| D7 | Formats and time axes | hydrograph table `time_min` + `discharge_m3s`, strict daily series with gap errors, minutes for event routing and days for daily models / allow resampling and mixed units | strict, as listed; no resampling in the first release | R0, L0 |
| D8 | Network and HRU ownership | Hydrograf exports `hydrolog-network/1`, Hydrolog reads no GIS data / Hydrolog gains a `[raster]` overlay; SCS-CN area limit per sub-catchment | Hydrograf owns extraction and overlay; limit applies per sub-catchment | R3, L5 |
| D9 | Stability policy | automatic sub-reaches or sub-steps with a notice, explicit user values validated / always strict | automatic with a notice; explicit values validated | R0 |
| D10 | Guide budget | shorten summaries and flows / one line per group for large groups with a recorded deviation / ask Nogat to raise 16 KiB | shorten first; the others only if that fails after R3 | R1 |
| D11 | Reference data licensing | NRCS examples primary, handout data secondary, fixtures derived from airGR or GRsuite (GPL) committed as numbers with provenance / only dev-time cross-checks without committed fixtures | NRCS first; for GPL-derived numbers decide after reading the licence terms; until then keep them out of the repository | R1, L3 |
| D12 | CN conventions in the continuous model | keep `SCSCN` (Chow et al. conversions) / adopt SWAT+ `CN1`, `CN3`; allow λ = 0.05 | keep `SCSCN`; offer the SWAT+ convention as an option of `simulate scs-cn` only | L5 |
| D13 | Names | groups `route`, `metrics`, `baseflow`, `pet`, `snow`, `simulate`, `calibrate`, `core` unchanged / a smaller set of groups (for example a single `model` group) | as listed | R0, L0 |
| D14 | Location of this report | keep `docs/research/` and add a deviation line to `CLAUDE.md` / move to `docs/plans/` | move (a rename) if the standard is to stay without deviations | none |
| D15 | Cross-project requests | open `request` issues: IMGWTools (daily synoptic data), Hydrograf (routing scope text, `hydrolog-network/1` export), Hydraulik (hydrograph CSV contract) | after D1 | R3 |

## 11. Findings in existing code and documents

These came out of the research; none was changed.

- **F1.** `ClarkIUH` produces a negative ordinate when the time step exceeds twice the storage constant (`r_min = 2`, `timestep_min = 5`: −0.00031 per minute; Appendix A10). Its docstring calls the reservoir scheme "Muskingum-Cunge"; it is Muskingum with `X = 0` ([`clark_iuh.py`](../../src/hydrolog/runoff/clark_iuh.py)). R1 fixes both.
- **F2.** The `AGENTS.md` byte budget has 311 bytes left (Appendix A11).
- **F3.** `precip areal` works on one time step; there is no areal series.
- **F4.** [SCOPE.md](../SCOPE.md) §2.2 and §5.1, [PRD.md](../PRD.md) ("No flow routing") and the Hydrograf scope all state "no routing"; they change together after D1.
- **F5.** `WatershedParameters` has a `crs` but no coordinates or latitude.
- **F6.** SCOPE.md §2.3 lists "Rational method" and "Empirical peak flow formulas" as post-1.0 items; they are independent of this report and unaffected.

## Appendix A. Checks made for this report

Throwaway scripts outside the repository; nothing here is committed. Equations are those of the cited sources, so each check can be repeated.

| # | Check | Result |
|---|---|---|
| A1 | [NEH-630 ch. 17][neh17] example 17-1 (Tables 17-5 and 17-7): outflow found by linear interpolation in the working curve `S/Δt + O/2` for `Δt = 0.5 h` | 19 ordinates, largest difference 0.85 ft³/s (published values are rounded) |
| A2 | Example 17-4: `L = 2,600 ft`, `Δt = 0.1 h`, reference discharge 684.18 ft³/s, `T = 44.6 ft`, `S = 0.00091`, `c = 4.297 ft/s`; `K = 605.07 s`, `X = −0.254`, `C = 0.028 / 0.356 / 0.617`, `Cg = 0.595`, `Dg = 1.509` (limit 3.93) | 37 ordinates, largest difference 0.24 ft³/s; peak 645.78 against 645.72 ft³/s published at 13.1 h |
| A3 | [Iowa handout][iowa-musk]: `K = 20 h`, `X = 0.25`, `Δt = 12 h`; `C0 = 0.0476`, `C1 = 0.5238`, `C2 = 0.4286` | 10 ordinates, largest difference 0.05 cfs |
| A4 | Muskingum with `X = 0.5`, `K = Δt`: coefficients 0, 1, 0; outflow equals inflow shifted one step. Muskingum with `X = 0`, `K = R`: identical to the scheme in `ClarkIUH._route_linear_reservoir` | exact |
| A5 | Unit pulse through `N` equal Muskingum sub-reaches (`K = 6`, `X = 0.2`, `Δt = 0.5`): mean delay 6.000 for all `N`; variance 21.6, 10.8, 5.4, 3.6, 1.8 for `N` = 1, 2, 4, 6, 12 against `K²(1 − 2X)/N` | agree to three decimals; volume 1.0000 |
| A6 | Positivity window `\|2KX\| ≤ Δt ≤ 2K(1 − X)` with `K = 20`: `X = 0`: [0, 40]; `0.15`: [6, 34]; `0.25`: [10, 30]; `0.5`: [20, 20]; example 17-4 (`X = −0.254`): [307.9, 1,518.1] s, `Δt = 360 s` inside | as stated |
| A7 | GR4J (Perrin et al. 2003, Eqs. 1–23), synthetic daily forcing, one core, Python 3.13: 30 years | 34 and 42 ms per run (two runs); advancing 100 parameter sets together with NumPy: 6.4 and 7.1 ms per set; scalar and vectorised series agree to 1e-14 |
| A8 | DDS ([Tolson and Shoemaker 2007][dds], `r = 0.2`) calibrating GR4J on 10 years of synthetic data with 5 % multiplicative noise, KGE objective, one year of warm-up, 500 evaluations | 8.5 s; KGE 0.971; found `x1, x2, x3, x4` = 213, −3.3, 299, 1.8 against generating values 420, −0.8, 110, 1.9 (`x3` at its bound): equifinality. One seed; indicative only |
| A9 | Mean-flow predictor on a ten-point series | NSE = 0; KGE = −0.4142 = 1 − √2, as [Knoben et al. (2019)][knoben-2019] state |
| A10 | `ClarkIUH(tc_min=60, r_min=R).generate_iuh(timestep_min=5)` for `R` = 30, 5, 2.5, 2, 1 | minimum ordinate 0 except `R = 2`: −0.00031 per minute (one negative value); each IUH integrates to 1 |
| A11 | Guide budget: `AGENTS.md` 16,073 bytes and 164 lines; command index 5,250 bytes; command line 115.8 bytes on average (38 lines), group heading 43.7 bytes (14 lines) | 18 commands and 7 new groups add about 2,390 bytes: 18,463 in total, 2,079 over the limit |
| A12 | `CN2 = 72`: Chow et al. conversions of `SCSCN` give `CN1 = 52.99`, `CN3 = 85.76`; the SWAT+ equations give 53.41 and 86.93 | the conventions differ by 0.4–1.2 CN units |

## Appendix B. Reference data and sketches

### B1. NEH-630 chapter 17, example 17-1 (storage-indication, `Δt = 0.5 h`)

Storage–outflow relation (Table 17-5, discharge in ft³/s, storage in ft³/s-h):

| `O` | 0 | 50 | 150 | 300 | 800 | 1,500 | 3,500 | 5,000 | 7,000 | 10,000 |
|---|---|---|---|---|---|---|---|---|---|---|
| `S` | 0.0 | 71.8 | 136.9 | 246.9 | 650.7 | 1,300.0 | 3,302.8 | 4,537.5 | 5,611.1 | 7,131.9 |

Inflow and published outflow (Table 17-7, ft³/s), `t` = 0, 0.5, … 9.0 h:

| `I` | 0 | 1,250 | 2,500 | 3,750 | 5,000 | 4,375 | 3,750 | 3,125 | 2,500 | 1,875 | 1,250 | 625 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `O` | 0 | 290 | 1,016 | 1,887 | 2,881 | 3,620 | 3,827 | 3,645 | 3,292 | 2,851 | 2,336 | 1,778 | 1,173 | 661 | 348 | 175 | 80 | 42 | 30 |

### B2. Muskingum example (Iowa handout)

`K = 20 h`, `X = 0.25`, `Δt = 12 h`. Inflow 100, 300, 680, 500, 400, 310, 230, 180, 100, 50 cfs; outflow 100.0, 109.5, 236.5, 481.3, 487.2, 433.1, 358.9, 282.9, 220.3, 149.2 cfs.

### B3. Network file sketch (`hydrolog-network/1`)

```json
{
  "schema": "hydrolog-network/1",
  "name": "Example stream",
  "nodes": [
    {"id": "A", "type": "subcatchment", "watershed": {"area_km2": 18.2, "cn": 74, "tc_min": 95}},
    {"id": "B", "type": "subcatchment", "watershed": {"area_km2": 26.7, "cn": 70, "tc_min": 120}},
    {"id": "R1", "type": "reach", "from": ["A"], "method": "muskingum-cunge",
     "length_km": 8.4, "slope_m_per_m": 0.0042, "manning_n": 0.04,
     "section": {"shape": "trapezoid", "bottom_width_m": 6.0, "side_slope": 2.0, "bankfull_depth_m": 1.6}},
    {"id": "J1", "type": "junction", "from": ["R1", "B"]},
    {"id": "D", "type": "reservoir", "from": ["J1"], "method": "level-pool", "rating_file": "pond_rating.csv"},
    {"id": "OUT", "type": "outlet", "from": ["D"]}
  ]
}
```

### B4. Command and result sketch

```bash
hydrolog route muskingum --input-file inflow.csv --time-column time_min \
  --value-column discharge_m3s --k-min 138 --x 0.15 --output outflow.csv --json
```

For `K = 138 min`, `X = 0.15` and a 60-minute step, the default sub-reach count is `N = round(K/Δt) = 2`; each sub-reach has `K/N = 69 min`, the positivity window is [20.7, 117.3] min, and the coefficients are `C0 = 0.2217`, `C1 = 0.4552`, `C2 = 0.3232`. The result would carry these, the peaks, the attenuation, the volumes and the balance, and `files[]` for `outflow.csv`.
## Sources

State of the web on 2026-10-24. Licences, releases, push dates, stars and languages of repositories come from the GitHub REST API; versions, upload dates, Python requirements and dependencies of packages from the PyPI JSON API; DOIs were resolved through Crossref. Where a document was read as a file (NRCS handbook chapter, Perrin et al. 2003, Moriasi et al. 2015, the Kaczawa programme, the national methodology), the quoted passage was checked in the text.

**Standards and ecosystem.** [AGENT_INTERFACE][agi-std], [DEVELOPMENT_STANDARDS][dev-std], [DOCUMENTATION_STANDARDS][doc-std] and the [ecosystem registry][nogat-registry] of Nogat; the repositories of [Kartograf](https://github.com/Daldek/Kartograf), [IMGWTools](https://github.com/Daldek/IMGWTools), [Hydrograf](https://github.com/Daldek/Hydrograf) ([scope][hydrograf-scope], [data model][hydrograf-data-model]) and [Hydraulik](https://github.com/Daldek/Hydraulik); the dataset registry of IMGWTools and the SoilGrids provider of Kartograf were read on their `chore/nogat-2.1` branches, which are not yet on the default branches; the [SFINCS manual][sfincs-forcing].

**Process models and software.** SWAT+: [repository][swatplus-repo], [retention parameter][swatplus-cn], [baseflow][swatplus-baseflow], [snow melt][swatplus-snow], [Hargreaves][swatplus-hargreaves], [spatial objects][swatplus-spatial], [weather inputs][swatplus-weather], and the code-verified draft pages [hydrology][swatplus-hydrology-draft] and [channels][swatplus-channels-draft]; [pySWATPlus][pyswatplus]; [hydrobricks][hydrobricks]; [RRMPG][rrmpg]; [SuperflexPy][superflexpy] and [its paper][dalmolin-2021]; [GRsuite][grsuite]; [airGR][airgr]; [Raven][raven] and [RavenPy][ravenpy]; [HEC-HMS][hechms]; [spotpy][spotpy] and [its paper][houska-2015]; [pyet][pyet]; [t-route][troute]; [mizuRoute][mizuroute]; [RAPID][rapid]; [NOAA-OWP sac-sma][sacsma-repo].

**Conceptual models and processes.** [Perrin et al. 2003][perrin-2003] (GR4J); [Pushpalatha et al. 2011][pushpalatha-2011] (GR6J); [Valéry et al. 2014][valery-2014] (CemaNeige); [Seibert and Vis 2012][seibert-vis-2012] (HBV-light); [Madsen 2000][madsen-2000] and a [third-party NAM description][nam-holmes]; the [NWS Sacramento description][sacsma-noaa]; [Beven and Kirkby 1979][beven-kirkby] and [Beven et al. 2021][beven-2021] (TOPMODEL); [Michel et al. 2005][michel-2005] and [Garen and Moore 2005][garen-moore] (SCS-CN); [Hargreaves and Samani 1985][hargreaves-1985], [Oudin et al. 2005][oudin-2005] and [FAO-56][fao-56] (PET); [Hock 2003][hock-2003] (temperature-index snow melt); [Eckhardt 2005][eckhardt-2005] and [Ladson et al. 2013][ladson-2013] (baseflow filters); [Saxton and Rawls 2006][saxton-rawls] (pedotransfer).

**Evaluation and calibration.** [Nash and Sutcliffe 1970][nash-sutcliffe]; [Gupta et al. 2009][gupta-2009]; [Kling et al. 2012][kling-2012]; [Knoben et al. 2019][knoben-2019]; [Clark et al. 2021][clark-2021]; [Moriasi et al. 2015][moriasi-2015]; [Klemeš 1986][klemes-1986]; [Duan et al. 1992][sceua]; [Tolson and Shoemaker 2007][dds].

**Routing.** HEC-HMS technical reference: [Muskingum][hec-musk], [Muskingum–Cunge][hec-mc], [Modified Puls][hec-puls], [Lag][hec-lag]; [NRCS NEH-630 chapter 17][neh17] (chapter PDF, Amendment 69, April 2014; the official index is the [NRCS Part 630 page](https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf)) and [17 U.S.C. § 105][us-copyright]; Ponce: [Muskingum–Cunge explained][ponce-mc], [with variable parameters][ponce-yevjevich], [revisited][ponce-vp-revisited], [linear reservoirs and numerical diffusion][ponce-linear-reservoirs]; [lecture note on the Muskingum interval][nptel-lec45]; [University of Iowa worked example][iowa-musk]; [Leopold and Maddock 1953][leopold-maddock]; [Bieger et al. 2015][bieger-2015].

**Polish practice.** [National methodology 2017][kzgw-2017] (Stowarzyszenie Hydrologów Polskich for KZGW); [Flood risk reduction programme for the Kaczawa catchment][prrp-kaczawa] (IMGW-PIB and Wody Polskie, March 2025); [Ostojski et al. 2014][ostojski-2014] (SWAT in Poland).

[agi-std]: https://github.com/Daldek/Nogat/blob/main/standards/AGENT_INTERFACE.md
[dev-std]: https://github.com/Daldek/Nogat/blob/main/standards/DEVELOPMENT_STANDARDS.md
[doc-std]: https://github.com/Daldek/Nogat/blob/main/standards/DOCUMENTATION_STANDARDS.md
[nogat-registry]: https://github.com/Daldek/Nogat/blob/main/ecosystem.yaml
[hydrograf-scope]: https://github.com/Daldek/Hydrograf/blob/main/docs/SCOPE.md
[hydrograf-data-model]: https://github.com/Daldek/Hydrograf/blob/main/docs/DATA_MODEL.md
[sfincs-forcing]: https://sfincs.readthedocs.io/en/latest/input_forcing.html
[swatplus-repo]: https://github.com/swat-model/swatplus
[swatplus-cn]: https://swatplus.gitbook.io/io-docs/theoretical-documentation/section-2-hydrology/chapter-2-1-surface-runoff/2-1.1-runoff-volume-scs-curve-number-procedure/2-1.1.1-scs-curve-number/2-1.1.1.3-retention-parameter
[swatplus-baseflow]: https://swatplus.gitbook.io/io-docs/theoretical-documentation/section-2-hydrology/chapter-2-4-groundwater/2-4.2-shallow-aquifer/2-4.2.3-groundwater-base-flow
[swatplus-snow]: https://swatplus.gitbook.io/io-docs/theoretical-documentation/section-1-climate/chapter-1-2-atmospheric-water/1-2.5-snow-melt/1-2.5.1-snow-pack-temperature/1-2.5.1.1-snow-melt-equation
[swatplus-hargreaves]: https://swatplus.gitbook.io/io-docs/theoretical-documentation/section-2-hydrology/chapter-2-2-evapotranspiration/2-2.2-potential-evapotranspiration/2-2.2.3-hargreaves-method
[swatplus-spatial]: https://swatplus.gitbook.io/io-docs/introduction/basin/spatial-objects
[swatplus-weather]: https://swatplus.gitbook.io/io-docs/introduction-1/climate/weather-sta.cli
[swatplus-hydrology-draft]: https://github.com/swat-model/swatplus-documentation/blob/main/docs/model-theory/hydrology.md
[swatplus-channels-draft]: https://github.com/swat-model/swatplus-documentation/blob/main/docs/model-theory/channels.md
[pyswatplus]: https://github.com/swat-model/pySWATPlus
[hydrobricks]: https://github.com/hydrobricks/hydrobricks
[rrmpg]: https://github.com/kratzert/RRMPG
[superflexpy]: https://github.com/dalmo1991/superflexPy
[dalmolin-2021]: https://doi.org/10.5194/gmd-14-7047-2021
[grsuite]: https://pypi.org/project/grsuite/
[airgr]: https://hydrogr.github.io/airGR
[raven]: https://github.com/CSHS-CWRA/RavenHydroFramework
[ravenpy]: https://github.com/CSHS-CWRA/RavenPy
[hechms]: https://www.hec.usace.army.mil/software/hec-hms/
[spotpy]: https://github.com/thouska/spotpy
[houska-2015]: https://doi.org/10.1371/journal.pone.0145180
[pyet]: https://github.com/pyet-org/pyet
[troute]: https://github.com/NOAA-OWP/t-route
[mizuroute]: https://github.com/ESCOMP/mizuRoute
[rapid]: https://github.com/c-h-david/rapid
[sacsma-repo]: https://github.com/NOAA-OWP/sac-sma
[sacsma-noaa]: https://vlab.noaa.gov/documents/207461/1893018/Sacramento_Soil_Moisture_Accounting.pdf
[perrin-2003]: https://doi.org/10.1016/S0022-1694(03)00225-7
[pushpalatha-2011]: https://doi.org/10.1016/j.jhydrol.2011.09.034
[valery-2014]: https://doi.org/10.1016/j.jhydrol.2014.04.059
[seibert-vis-2012]: https://doi.org/10.5194/hess-16-3315-2012
[madsen-2000]: https://doi.org/10.1016/S0022-1694(00)00279-1
[nam-holmes]: https://antoinelb.github.io/holmes/concepts/hydro/nam
[beven-kirkby]: https://doi.org/10.1080/02626667909491834
[beven-2021]: https://doi.org/10.5194/hess-25-527-2021
[michel-2005]: https://doi.org/10.1029/2004WR003191
[garen-moore]: https://doi.org/10.1111/j.1752-1688.2005.tb03742.x
[hargreaves-1985]: https://doi.org/10.13031/2013.26773
[oudin-2005]: https://doi.org/10.1016/j.jhydrol.2004.08.026
[fao-56]: https://www.fao.org/4/x0490e/x0490e00.htm
[hock-2003]: https://doi.org/10.1016/S0022-1694(03)00257-9
[eckhardt-2005]: https://doi.org/10.1002/hyp.5675
[ladson-2013]: https://doi.org/10.7158/13241583.2013.11465417
[saxton-rawls]: https://doi.org/10.2136/sssaj2005.0117
[nash-sutcliffe]: https://doi.org/10.1016/0022-1694(70)90255-6
[gupta-2009]: https://doi.org/10.1016/j.jhydrol.2009.08.003
[kling-2012]: https://doi.org/10.1016/j.jhydrol.2012.01.011
[knoben-2019]: https://doi.org/10.5194/hess-23-4323-2019
[clark-2021]: https://doi.org/10.1029/2020WR029001
[moriasi-2015]: https://doi.org/10.13031/trans.58.10715
[klemes-1986]: https://doi.org/10.1080/02626668609491024
[sceua]: https://doi.org/10.1029/91WR02985
[dds]: https://doi.org/10.1029/2005WR004723
[hec-musk]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-model
[hec-mc]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-cunge-model
[hec-puls]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/modified-puls-model
[hec-lag]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/lag-model
[neh17]: https://damtoolbox.org/images/a/a6/NEH17.pdf
[us-copyright]: https://www.law.cornell.edu/uscode/text/17/105
[ponce-mc]: https://ponce.sdsu.edu/muskingum_cunge_method_explained.html
[ponce-yevjevich]: https://ponce.sdsu.edu/muskingum_cunge_method_with_variable_parameters.html
[ponce-vp-revisited]: https://ponce.sdsu.edu/variable_parameter_muskingum_cunge_method_revisited.html
[ponce-linear-reservoirs]: https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html
[nptel-lec45]: http://elearn.psgcas.ac.in/nptel/courses/video/105105214/lec45.pdf
[iowa-musk]: https://user.engineering.uiowa.edu/~flood/handouts/EX-L27-Muskingum-soln.pdf
[leopold-maddock]: https://doi.org/10.3133/pp252
[bieger-2015]: https://doi.org/10.1111/jawr.12282
[kzgw-2017]: https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf
[prrp-kaczawa]: https://www.gov.pl/attachment/b39f6f09-7d94-4995-ac4e-ab5980297fac
[ostojski-2014]: https://doi.org/10.2134/jeq2011.0365
