# Computation Paths for Unit Hydrograph Models (plus HSG and the Fisher–Tippett Distribution)

**Document version:** 1.13
**Date:** 2026-11-18
**Applies to:** Hydrolog >= 0.8.0 (sections 3.2.2, 3.2.7, 3.3.4 (the time step limit), 3.3.6, 3.4.6, 3.4.7 and 3.5 to 3.14 describe behaviour from v0.8.0, the sub-steps of the SCS unit hydrograph (3.1.3) and the plausibility of a rating curve (3.8) from 0.8.1, maximum likelihood (3.6, 3.10) and the Euler type II storm (3.15) from the fixes of 2026-11-18, not yet released; the rest: >= 0.6.0)

---

## 1. Introduction

### 1.1 Purpose of the Document

Hydrolog implements 4 unit hydrograph models: **SCS**, **Nash**, **Clark** and **Snyder**. Each model has different input parameters and different methods for estimating them.

**An incorrect combination of methods** (e.g. turning the time of concentration from the Kirpich formula into the Nash storage constant through the SCS relation `tlag = 0.6 × Tc`) can lead to wrong results without scientific justification.

This document serves as a guide that:
- States clearly the **correct computation paths** for each model
- **Warns** against incorrect use of methods
- Gives the **literature justification** for each path

### 1.2 Compatibility Matrix

| Model | Kirpich | NRCS | Giandotti | FAA | Kerby | Kerby-Kirpich | from_lutz() | from_urban_regression() | Directly | Own method |
|-------|:-------:|:-------:|:---------:|:---:|:-----:|:-------------:|:-----------:|:-----------------------:|:------------:|:-------------:|
| **SCS UH** | ✅ | ✅ | ✅ | ✅¹ | ✅¹ | ✅ | - | - | - | - |
| **Nash IUH** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | - |
| **Clark IUH** | ✅ | ✅ | ✅ | ✅¹ | ✅¹ | ✅ | - | - | ✅ | - |
| **Snyder UH** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | - | ✅ | ✅ |

**Legend:**
- ✅ **OK** - correct use, confirmed by the literature
- ❌ **NOT APPLICABLE** - the model does not use an external Tc
- ✅¹ **OK with a limitation** - FAA and Kerby compute the overland flow time (flow paths of the order of hundreds of metres), so as a catchment Tc they are suitable only for small catchments without a distinct channel; for a catchment with a channel, Tc is given by Kerby-Kirpich (overland flow + channel) or by Kirpich (section 3.7)

---

## 2. Hydrograph Models - Overview

### 2.1 SCS Unit Hydrograph

| Feature | Value |
|---------|-------|
| **Type** | Synthetic, empirical |
| **Input parameters** | `area_km2`, `tc_min` |
| **Source** | USDA-NRCS NEH 630 ch. 16 (2007), table 16-1 and eqs. 16A-6 to 16A-9; HEC-HMS Technical Reference Manual, "SCS Unit Hydrograph Model" |
| **Characteristics** | NRCS dimensionless curve (33 points) |

**Key relation:** `tlag = 0.6 × Tc` (NEH 630 ch. 15, eq. 15-3, after Mockus 1957 and Simas 1996; HEC-HMS Technical Reference Manual, "SCS Unit Hydrograph Model", eq. 3)

### 2.2 Nash IUH

| Feature | Value |
|---------|-------|
| **Type** | Conceptual (cascade of linear reservoirs) |
| **Input parameters** | `n` (number of reservoirs), `k_min` (storage constant) |
| **Source** | Nash (1957), Lutz (1984) |
| **Characteristics** | Gamma distribution, `u(t) = (t/K)^(n-1) × e^(-t/K) / (K×Γ(n))` |

**Key relation:** `tlag = n × K` (a mathematical result, not an assumption!)

### 2.3 Clark IUH

| Feature | Value |
|---------|-------|
| **Type** | Conceptual (translation + linear reservoir) |
| **Input parameters** | `tc_min` (translation time), `r_min` (storage constant) |
| **Source** | Clark (1945), HEC-HMS |
| **Characteristics** | Time-area histogram + routing |

**Key relation:** Tc = translation time through the catchment

### 2.4 Snyder UH

| Feature | Value |
|---------|-------|
| **Type** | Synthetic, empirical |
| **Input parameters** | `area_km2`, `L_km`, `Lc_km`, `ct`, `cp` |
| **Source** | Snyder (1938) |
| **Characteristics** | Built-in estimation: `tL = Ct × (L × Lc)^0.3` |

**Key relation:** The model **does NOT need** an external Tc!

---

## 3. Computation Paths - Details

### 3.1 SCS Unit Hydrograph

#### 3.1.1 Data Flow Diagram

```
                      INPUT DATA
                    ┌─────────────────┐
                    │  L_km, S (m/m)  │
                    │     CN (opt)    │
                    │   A_km², H_m    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │    KIRPICH      │ │    NRCS     │ │  GIANDOTTI  │
    │tc=0.0078×L^0.77 │ │ tc=f(L,S,CN)│ │ tc=f(A,L,H) │
    │  ×S^(-0.385)    │ │             │ │             │
    │ [min], L in ft  │ │             │ │             │
    └────────┬────────┘ └──────┬──────┘ └──────┬──────┘
             │                 │               │
             └─────────────────┼───────────────┘
                               ▼
                         ┌──────────┐
                         │   Tc     │
                         │  [min]   │
                         └────┬─────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 │                 ▼
    ┌───────────────┐         │         ┌───────────────┐
    │  tlag = 0.6×Tc│ ←───────┴─────────│ SCS RELATION  │
    └───────┬───────┘                   │ (NEH 630,     │
            │                           │ eq. 15-3)     │
            │                           └───────────────┘
            ▼
    ┌───────────────────────┐
    │  tp = D/2 + tlag      │ D = time step
    │  qp = 0.208 × A / tp  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │   SCS UNIT HYDROGRAPH │
    │   (table, 33 points)  │
    └───────────────────────┘
```

> **Note on the Kirpich constant:** Kirpich's formula is published as `tc[min] = 0.0078 × L[ft]^0.77 × S^(-0.385)`, S in ft/ft (Fang et al. 2005, eq. 3.14, p. 22; Roussel et al. 2005, eq. 7). Hydrolog takes L in km and converts it to feet exactly (1 ft = 0.3048 m), so it computes the published formula. The metric constants met in the literature are rounded conversions of it: 0.0195 with L in m (Roussel et al. 2005, supplement; exactly 0.019472), 3.981 with L in km and the result in minutes, 0.0663 with L in km and the result in hours. Before 0.9.0 Hydrolog used 3.981, 0.136 % above the exact `0.0078 × (1000/0.3048)^0.77 = 3.97560`. The constants and applicability ranges of every method are in [FORMULAS.md](FORMULAS.md).

The inputs in the diagram are generic; each method takes those its source defines (section 3.7): Kirpich the length and slope of the longest flow path, NRCS that length, the average land slope Y and CN, Giandotti A, the main channel and H = mean elevation − outlet elevation.

#### 3.1.2 Correct Tc Estimation Methods

| Method | Status | Justification |
|--------|--------|---------------|
| Kirpich | ✅ OK | Tc is an input parameter of the SCS method |
| NRCS | ✅ OK | Lag method of the SCS UH (NEH 630, ch. 15: lag equation 15-4a; its tc form, eq. 15-4b, follows from L = 0.6 Tc, eq. 15-3) |
| Giandotti | ✅ OK | Tc is an input parameter of the SCS method |
| FAA | ✅ OK¹ | Tc is an input parameter of the SCS method (overland flow time) |
| Kerby | ✅ OK¹ | Tc is an input parameter of the SCS method (sheet flow time, path up to 366 m) |
| Kerby-Kirpich | ✅ OK | Composite Tc (overland + channel flow) is an input parameter of SCS |

**Literature justification:**
- The relation `tlag = 0.6 × Tc` is NEH 630 ch. 15, eq. 15-3 (Mockus 1957; Simas 1996: "for average natural watershed conditions and an approximately uniform distribution of runoff", p. 15-3); HEC-HMS takes it as `tp = 0.6 × Tc` with `Tp = Δt/2 + tp` (Technical Reference Manual, "SCS Unit Hydrograph Model", eqs. 3 and 1). TR-55 (1986) does not contain it
- The SCS dimensionless unit hydrograph is built on it: `Tp = ΔD/2 + L` and `qp = 484 A Q / (ΔD/2 + 0.6 Tc)` (NEH 630 ch. 16, eqs. 16A-7 and 16A-9)
- All Tc computation methods are suitable as input
- ¹ FAA and Kerby are formulas for overland flow time, not for the time of concentration of a catchment with a channel; for such a catchment use Kerby-Kirpich (section 3.7)

#### 3.1.3 Formulas

```
tlag = 0.6 × Tc                              [min]
tp = D/2 + tlag                              [min]   (D = time step)
qp = 0.208 × A / tp                          [m³/s/mm]   (tp in hours!)
tb = 5.0 × tp                                [min]
```

**Note on the base time (tb):** In the context of the SCS UH there are two values of tb — both are correct for their purposes:
- `tb ≈ 2.67 × tp` — triangular approximation, used to derive the constant 0.208
- `tb = 5.0 × tp` — full range of the NRCS dimensionless table (33 points), used when discretising the UH

**Derivation of the constant 0.208:**
- For the triangular approximation: V = 0.5 × qp × tb
- Volume of 1 mm over A km²: V = A × 1000 m³
- With tb ≈ 2.67 × tp: qp = 2V / (2.67 × tp × 3600) ≈ 0.208 × A / tp

**A time step beyond its range (0.8.1, E5b-07).** The ordinates are the dimensionless curve sampled at the step times k·Δt. A step beyond its typical range, Δt > 0.25·tp with tp = Δt/2 + tlag (the `timestep_min` range of `hydrolog._ranges`, NEH 630 ch. 16), leaves too few ordinates, and their sum loses volume: tc = 90.7 min at Δt = 1440 min gave three ordinates, 0, 0.355·qp and 0.017·qp, and 0.52 mm instead of 1 mm (about 61 % of Pe·A in a network's elements of the scenario test). Such a step is divided into the fewest equal sub-steps d = Δt/n inside the range (d ≤ 0.25·(d/2 + tlag)); the unit hydrograph of D = d, sampled on the sub-steps, takes the 1 mm of the step spread evenly over them, 1/n mm each, and is read at the step times: u(k·Δt) = (u_d(((k − 1)·n + 1)·d) + … + u_d(k·n·d))/n. The ordinates hold the volume of the sub-step's unit hydrograph (0.998 mm in that example, 93 sub-steps of 15.48 min: ordinates 0, 0.01156·A, 0 m³/s per mm), the convolution of the step's effective rain is unchanged, and the notice `uh_substeps` (info: `timestep_min`, `maximum_min`, `substeps`, `substep_min`) says so beside the `outside_applicability` of the step, which stays: the result still has one ordinate per step. tp, qp and tb stay those of the formulas for D = Δt, which the ordinates no longer reach. A step inside the range is sampled as before, to the last bit.

#### 3.1.4 Code Example

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import SCSUnitHydrograph, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Step 1: Compute Tc with any method
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
print(f"Tc (Kirpich) = {tc:.1f} min")

# Step 2: Create the SCS UH
scs_uh = SCSUnitHydrograph(area_km2=45.0, tc_min=tc)
result = scs_uh.generate(timestep_min=5.0)

print(f"tlag = {result.lag_time_min:.1f} min")
print(f"tp = {result.time_to_peak_min:.1f} min")
print(f"qp = {result.peak_discharge_m3s:.2f} m³/s/mm")

# Step 3: Full rainfall → runoff transformation
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=tc)
hydrograph = generator.generate(precip)

print(f"Qmax = {hydrograph.peak_discharge_m3s:.2f} m³/s")
```

---

### 3.2 Nash IUH

#### 3.2.1 Diagram - Correct Paths

```
                              INPUT DATA
    ┌──────────────────────────────────────────────────────────────────────┐
    │   LUTZ METHOD             │  URBAN REGRESSION   │  DIRECT           │
    │  L_km, Lc_km, slope,      │  area_km2,          │  n (no. of res.)  │
    │  manning_n, urban_pct,    │  effective_precip_mm,│  K [min]          │
    │  forest_pct              │  duration_h,         │                   │
    │                          │  urban_fraction      │                   │
    └──────────┬───────────────┴──────────┬───────────┴────────┬──────────┘
               │                          │                    │
               ▼                          ▼                    │
    ┌───────────────────────────┐ ┌───────────────────────┐    │
    │  NashIUH.from_lutz()      │ │ NashIUH               │    │
    │  ─────────────────────── │ │ .from_urban_regression │    │
    │  1. P1 = 3.989×n + 0.028 │ │ ──────────────────── │    │
    │  2. tp = P1×(L×Lc/       │ │ 1. tL = 1.28×A^0.46  │    │
    │     Jg^1.5)^0.26         │ │    ×(1+U)^(-1.66)    │    │
    │    ×e^(-0.016U)          │ │    ×H^(-0.27)        │    │
    │    ×e^(0.004W)           │ │    ×D^0.37           │    │
    │  3. up=0.66/tp^1.04 Δt→0 │ │ 2. k = 0.56×A^0.39   │    │
    │  4. f(N) = tp×up →      │ │    ×(1+U)^(-0.62)    │    │
    │     solve for N          │ │    ×H^(-0.11)        │    │
    │  5. K = tp / (N-1)       │ │    ×D^0.22           │    │
    └──────────┬────────────────┘ │ 3. N = tL / k        │    │
               │                  └──────────┬────────────┘    │
               │                             │                 │
               └─────────────┬───────────────┘                 │
                             └──────────────┬──────────────────┘
                                            ▼
                                    ┌───────────────┐
                                    │   n, K [min]  │
                                    └───────┬───────┘
                                            │
                                            ▼
                             ┌──────────────────────────────┐
                             │         NASH IUH             │
                             │  u(t) = (t/K)^(n-1)×e^(-t/K) │
                             │        / (K × Γ(n))          │
                             └──────────────────────────────┘
```

#### 3.2.2 No Path from Tc

The Nash model takes no time of concentration. `NashIUH.from_tc()` (`tlag = 0.6 × Tc`, `K = tlag / n`),
deprecated since v0.6.2, was removed in v0.8.0:

```
┌─────────────────────────────────────────────────────────────────────┐
│  The relation tlag = 0.6 × Tc comes from the SCS method (NEH 630,   │
│  eq. 15-3) and has NO scientific justification for the Nash model.  │
│                                                                     │
│  In the Nash model: tlag = n × K is a MATHEMATICAL RESULT          │
│  of the reservoir cascade, NOT an input parameter!                 │
│                                                                     │
│  ┌─────────────────────────┐       ┌─────────────────────────┐     │
│  │   SCS Unit Hydrograph   │       │      Nash IUH           │     │
│  ├─────────────────────────┤       ├─────────────────────────┤     │
│  │ tlag = 0.6 × Tc         │       │ tlag = n × K            │     │
│  │ (DESIGN ASSUMPTION)     │       │ (MATHEMATICAL RESULT)   │     │
│  │ Tc is the INPUT         │       │ n, K are the INPUT      │     │
│  └─────────────────────────┘       └─────────────────────────┘     │
│                                                                     │
│  Use NashIUH.from_lutz(), NashIUH.from_urban_regression() or       │
│  supply n and K directly                                           │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.2.3 Correct Estimation Methods

| Method | Status | Justification |
|--------|--------|---------------|
| `from_lutz()` | ✅ RECOMMENDED | Developed specifically for Nash (Lutz, 1984) |
| `from_urban_regression()` | ✅ OK | Regression for urbanised catchments (Rao, Delleur, Sarma 1972) |
| Directly `n`, `K` | ✅ OK | When you have calibrated values |
| ~~Method of moments~~ | REMOVED in v0.5.1 | Requires data from an observed hydrograph |
| ~~`from_tc()`~~ | REMOVED in v0.8.0 | No scientific justification (SCS relation `tlag = 0.6 × Tc`) |

#### 3.2.4 Lutz Method Formulas

The spec `lutz` ([FORMULAS.md](FORMULAS.md#lutz)) declares the equations, their constants,
ranges and sources (KZGW 2017, annex 2, pp. 97–100 and Table C.2;
`hydrolog.runoff.nash_iuh.lutz_parameters`, which `NashIUH.from_lutz` computes with):

```
1. P₁ = 3.989 × n_manning + 0.028     (eq. 6.18 prints "− 0,028", a misprint)

2. tp = P₁ × (L × Lc / Jg^1.5)^0.26 × e^(-0.016U) × e^(0.004W)   [h]

3. up = 0.66 / tp^1.04                for Δt → 0 (eq. 6.19)       [1/h]

4. f(N) = tp × up → solve numerically for N on [1.1, 20]
   (where f(N) = (N-1)^N × e^(-(N-1)) / Γ(N), KZGW's Table C.2)

5. K = tp / (N-1)                                                 [h]
```

Step 3 is Lutz's relation for an infinitesimal step: the unit hydrograph of a step Δt
averages the IUH over Δt exactly. KZGW's Ex. 6.2 takes the relation of Δt = 1 h
(`up = 0.464 / tp^0.824`) and gets N 2.55 and k 0.70 h where Hydrolog gets 3.88 and
0.377 h (a UH peak 28 % higher); the spec records it as a discrepancy. The spec refuses
Lc > L, U + W > 100 % and a tp whose N lies outside the bracket.

**Influence of physiographic parameters:**

| Factor | Effect on runoff |
|--------|------------------|
| ↑ Forest (W) | Slower (↑ tp, ↑ tlag) |
| ↑ Urbanisation (U) | Faster (↓ tp, ↓ tlag) |
| ↑ Slope (Jg) | Faster (↓ tp) |
| ↑ Manning (n) | Slower (↑ tp) |

#### 3.2.5 Formulas of the Regression Method for Urbanised Catchments

The `from_urban_regression()` method uses empirical power-law regression equations
(Rao, Delleur, Sarma 1972) developed for urbanised and partly
urbanised catchments:

```
1. Lag time:
   tL = 1.28 × A^0.46 × (1+U)^(-1.66) × H^(-0.27) × D^0.37        [h]

2. Storage constant:
   k = 0.56 × A^0.39 × (1+U)^(-0.62) × H^(-0.11) × D^0.22         [h]

3. Number of reservoirs:
   N = tL / k                                                        [-]
```

**Input parameters:**

| Symbol | Parameter | Unit |
|--------|-----------|------|
| A | Catchment area | km² |
| U | Urbanisation index (0 = natural, 0.5 = 50% urbanised) | - |
| H | Effective precipitation (total) | mm |
| D | Duration of effective precipitation | h |

**Origin of the metric constants:**
The original regression (Sarma, Delleur, Rao 1969) was developed in imperial
units (mi², in). The metric constants 1.28 and 0.56 incorporate the unit conversion
and appear in the 1972 ASCE publication.

**Effect of the parameters:**

| Factor | Effect on runoff |
|--------|------------------|
| ↑ Area (A) | Slower (↑ tL, ↑ k) |
| ↑ Urbanisation (U) | Faster (↓ tL, ↓ k) |
| ↑ Effective precipitation (H) | Faster (↓ tL, ↓ k) |
| ↑ Duration (D) | Slower (↑ tL, ↑ k) |

#### 3.2.6 Code Example - CORRECT USE

```python
from hydrolog.runoff import NashIUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# METHOD 1: from_lutz() - RECOMMENDED for catchments without measurement data
nash = NashIUH.from_lutz(
    L_km=15.0,          # Main stream length
    Lc_km=8.0,          # Length to the catchment centroid
    slope=0.02,         # Stream slope
    manning_n=0.035,    # Manning coefficient
    forest_pct=40.0,    # Forest share [%]
    urban_pct=5.0,      # Urbanisation share [%]
    area_km2=50.0       # Catchment area
)
print(f"n = {nash.n:.2f}")
print(f"K = {nash.k_min:.1f} min")
print(f"tlag = {nash.lag_time_min:.1f} min")

# METHOD 2: from_urban_regression() - for urbanised catchments
nash_urban = NashIUH.from_urban_regression(
    area_km2=1.3,
    effective_precip_mm=1.305,
    duration_h=0.167,
    urban_fraction=0.05,
)
print(f"n = {nash_urban.n:.3f}")
print(f"K = {nash_urban.k_min:.1f} min")

# METHOD 3: Supplying the parameters directly
# (when you have calibrated values)
nash_direct = NashIUH(n=3.5, k_min=45.0, area_km2=50.0)

# Generating the hydrograph
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(
    area_km2=50.0, cn=72,
    uh_model="nash",
    uh_params={"n": nash.n, "k": nash.k_min / 60.0, "k_unit": "hours"}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

#### 3.2.7 Lutz from a Watershed: `nash_estimation` (ADR-0024)

`hydrograph generate`, `report generate` and the `curve-number` runoff of a network
(`hydrolog-network/1`) estimate n and K by Lutz from the watershed when given
`nash_estimation: "lutz"` instead of `nash_n` and `nash_k_min`, in the same run. Each input
is the watershed field the method defines (`hydrolog._ranges.NASH_INPUTS`,
`WatershedParameters.nash_parameters("lutz")`), with no substitute:

| Symbol | Field | Note |
|--------|-------|------|
| L | `flow_path_length_km` | the main stream from the divide to the outlet: the longest flow path (ADR-0019), not the channel, which ends at the channel head |
| Lc | `Lc_km` | along the stream to the point nearest the centroid; not longer than L (`maximum` on `Lc_km`) |
| Jg | `flow_path_equal_area_slope_m_per_m` | the equal-area slope of that stream's longitudinal profile (KZGW 2017, annex 2, p. 97; spec `equal_area_slope`, `hydrolog.morphometry.equal_area_slope`; ADR-0053), > 0; not `flow_path_slope_m_per_m`, the slope between its ends, which Kirpich takes |
| n_M | `manning_n` | Manning's coefficient of the channel |
| U, W | `urban_pct`, `forest_pct` | 0 when the watershed has none |
| A | `area_km2` | scales the unit hydrograph; above 236 km2 the notice `outside_applicability` (method `lutz`, KZGW 2017) |

The estimate is the one of `NashIUH.from_lutz`, so one run equals `uh nash` with the same L, Lc,
J, n_M, U and W followed by `hydrograph generate` with its n and K, to the last ordinate. Unlike
given n and K, the estimate is not checked against their ranges (`outside_unverified_range`):
those are ranges of given values. The report prints Lutz's inputs and steps in its unit
hydrograph section, and a network node lists `nash_estimation` (given) and `nash_n`,
`nash_k_min` (computed). A missing field is `missing_field` with `details.method` `lutz`.

---

### 3.3 Clark IUH

#### 3.3.1 Data Flow Diagram

```
                      INPUT DATA
                    ┌─────────────────┐
                    │  L_km, S (m/m)  │
                    │  A_km², H_m     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │    KIRPICH      │ │    NRCS     │ │  GIANDOTTI  │
    └────────┬────────┘ └──────┬──────┘ └──────┬──────┘
             │                 │               │
             └─────────────────┼───────────────┘
                               ▼
                         ┌──────────┐
                         │   Tc     │  ← TRANSLATION TIME
                         │  [min]   │
                         └────┬─────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │     Tc        │   │  R [min]      │
            │ (translation) │   │  (storage)    │
            └───────┬───────┘   └───────┬───────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
            ┌──────────────────────────────────┐
            │           CLARK IUH              │
            │  1. Time-area histogram          │
            │  2. Routing through a linear     │
            │     reservoir (S = R × O)        │
            └──────────────────────────────────┘
```

#### 3.3.2 Correct Estimation Methods

| Method | Status | Justification |
|--------|--------|---------------|
| Kirpich → Tc | ✅ OK | Tc = translation time (consistent with the Clark model) |
| NRCS → Tc | ✅ OK | Tc = translation time |
| Giandotti → Tc | ✅ OK | Tc = translation time |
| FAA → Tc | ✅ OK¹ | Tc = translation time (overland flow time) |
| Kerby → Tc | ✅ OK¹ | Tc = translation time (sheet flow time) |
| Kerby-Kirpich → Tc | ✅ OK | Tc = translation time (composite: overland + channel flow) |
| Directly Tc, R | ✅ OK | When you have measured/calibrated values |
| R/Tc ratio | ✅ OK | 0.2-1.5 without a notice; no published source (to be verified) |

**Literature justification:**
- In the Clark model, Tc represents the **translation time** - the time water takes to travel from the farthest point of the catchment to the outlet
- This is **consistent** with the physical interpretation of the time of concentration
- Source: Clark (1945), HEC-HMS Technical Reference Manual
- ¹ FAA and Kerby: only small catchments without a channel (as in section 3.1.2); for a catchment with a channel use Kerby-Kirpich

#### 3.3.3 Choosing the R Coefficient

R is best calibrated on measured floods. Outside R/Tc 0.2–1.5 Hydrolog warns with
`outside_unverified_range` (`clark.r_tc_ratio`), but no source publishes that range: the
HEC-HMS Technical Reference Manual gives no R/Tc, and the Polish calibrations of the
Stobnica (335.84 km², Wałęga and Cupak 2013, table 2) give R/Tc 1.7–2.3. A larger R/Tc
gives a lower and later peak. The classes of earlier versions (0.2–0.4 steep and urban,
0.4–0.8 average, 0.8–1.5 flat and swampy) were credited to HEC-HMS, which does not
contain them.

#### 3.3.4 Formulas

```
Two-stage model:

1. TRANSLATION (time-area histogram):
   HEC-HMS curve for an elliptical catchment (two-part):

   tau = t / Tc

   For tau ≤ 0.5:  A_cum(t) = 1.414 × tau^1.5
   For tau > 0.5:  A_cum(t) = 1.0 - 1.414 × (1.0 - tau)^1.5

   Boundary conditions:
   - A_cum(0)    = 0
   - A_cum(Tc/2) = 1.414 × 0.5^1.5 ≈ 0.5  (symmetric centroid)
   - A_cum(Tc)   = 1.0

2. ATTENUATION (linear reservoir):
   O(t) = O(t-1) + C1 × (I(t) + I(t-1) - 2×O(t-1))
   where C1 = dt / (2R + dt)
```

The scheme is the Muskingum routing with X = 0. The weight of the previous outflow,
(2R - dt) / (2R + dt), is negative for dt > 2R and the hydrograph would oscillate, so
`ClarkIUH` (and `uh clark`, `hydrograph generate` with `uh_model=clark`) accepts a time
step of at most 2R; a longer one is a `validation_error` with
`details.reason = "precondition_failed"` (`details.constraint = "step_stable"`,
`details.option = "timestep_min"`).

#### 3.3.5 Code Example

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import ClarkIUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Step 1: Compute Tc
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Step 2: Determine the storage coefficient R
r_min = 0.5 * tc  # R/Tc = 0.5, assumed: no source publishes a typical R/Tc

# Step 3: Create the Clark IUH
clark = ClarkIUH(tc_min=tc, r_min=r_min, area_km2=45.0)
result = clark.generate(timestep_min=5.0)

print(f"Tc = {tc:.1f} min")
print(f"R = {r_min:.1f} min")
print(f"Qmax UH = {result.peak_discharge_m3s:.2f} m³/s/mm")

# Alternatively: the from_tc_r_ratio method
clark_alt = ClarkIUH.from_tc_r_ratio(tc_min=tc, r_tc_ratio=0.5)

# Full transformation
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(
    area_km2=45.0, cn=72, tc_min=tc,
    uh_model="clark",
    uh_params={"r": r_min}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

#### 3.3.6 D-minute Hydrograph from the S-curve (`to_unit_hydrograph`)

`ClarkIUH.to_unit_hydrograph(area_km2, duration_min, timestep_min)` converts the IUH into a unit hydrograph of effective precipitation of duration D using the S-curve method:

```
S(t)  = ∑ u(t_i) × dt                     (cumulative sum of the IUH ordinates; response to continuous rainfall of unit intensity)
U_D(t) = [ S(t) - S(t - D) ] / D          (unit hydrograph for 1 mm of rainfall over time D)
```

The S-curve is known only at the nodes `t_i = i × dt`, so the lagged curve `S(t_i - D)` is read by linear interpolation (before t = 0 it equals 0). Thanks to this, **D does not have to be a multiple of the step `dt`**:

| D / dt | Behaviour |
|--------|-----------|
| integer k (D = k·dt) | exactly the S-curve shifted by k steps (as before) |
| non-integer (e.g. 1.5) | linear interpolation between two neighbouring nodes; UH volume = 1 mm |
| < 1 | S resolved at best to the step: result as for D = dt; to resolve a short rainfall use `timestep_min <= duration_min` |

The hydrograph volume (sum of ordinates × dt, converted to a water depth over the catchment) is **1 mm** for any D > 0, provided the whole response is covered by `total_duration_min` (by default `tc + 5R + D` loses only a negligible tail).

> **Change in v0.8.0 (bug fix).** Versions < 0.8.0 shifted the S-curve by `round(D/dt)` steps but divided by D. For D that is not a multiple of the step, the volume was `round(D/dt)·dt/D` mm: **1.333 mm for D = 1.5·dt** and 0.8 mm for D = 2.5·dt (discharges 33% too large or 20% too small), and for D < dt/2 `to_unit_hydrograph` raised `ValueError` (`s_curve[:-0]`). Since v0.8.0 the volume is 1.000 mm for every D, and a non-positive or infinite D or step raises `InvalidParameterError`.

```python
iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
# D = 1.5 steps: UH volume = 1 mm (formerly 1.333 mm)
uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=7.5, timestep_min=5.0,
                            total_duration_min=1000.0)
print(f"{uh.ordinates_m3s.sum() * 5.0 * 60.0 / 45000.0:.3f} mm")   # 1.000 mm
```

---

### 3.4 Snyder UH

#### 3.4.1 Data Flow Diagram

```
                      INPUT DATA
    ┌───────────────────────────────────────────────────────┐
    │  A_km²  - catchment area                              │
    │  L_km   - main stream length                          │
    │  Lc_km  - length to the catchment centroid            │
    │  Ct     - time coefficient (1.35-1.65)                │
    │  Cp     - peak coefficient (0.4-0.8)                  │
    └───────────────────────┬───────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │              BUILT-IN SNYDER METHOD                   │
    │  ───────────────────────────────────────────────      │
    │  tL = Ct × (L × Lc)^0.3           [h]                │
    │       ↑                                               │
    │       └─── OWN FORMULA (NOT Kirpich!)                 │
    │                                                       │
    │  tD = tL / 5.5                    [h] (standard)      │
    │  tp = tL + tD/2                   [h]                 │
    │  qp = 0.275 × Cp × A / tL         [m³/s/mm]          │
    └───────────────────────┬───────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │                    SNYDER UH                          │
    │  gamma curve through (tpR, qpR), 1 mm (section 3.4.7) │
    └───────────────────────────────────────────────────────┘
```

#### 3.4.2 The Model Does NOT Use an External Tc!

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ⚠️  THE SNYDER MODEL DOES NOT NEED AN EXTERNAL Tc!                  │
│                                                                       │
│  Snyder has its OWN method of estimating the lag time (tL)           │
│  based on L, Lc and the coefficient Ct.                              │
│                                                                       │
│  DO NOT USE with the Snyder model:                                   │
│  ❌ ConcentrationTime.kirpich()                                       │
│  ❌ ConcentrationTime.nrcs()                                          │
│  ❌ ConcentrationTime.giandotti()                                     │
│                                                                       │
│  Using an external Tc would be methodologically unjustified,         │
│  because the Snyder model was developed as a COMPLETE method.        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

#### 3.4.3 Formulas

**For the standard duration (Δt = tD):**
```
tL = Ct × (L × Lc)^0.3                   [h]
tD = tL / 5.5                            [h]
tp = tL + tD/2                           [h]
qp = 0.275 × Cp × A / tL                 [m³/s/mm]
```

**For a non-standard duration (Δt ≠ tD):**
```
tLR = tL + 0.25 × (Δt - tD)              [h]
tpR = tLR + Δt/2                         [h]
qpR = qp × (tL / tLR)                    [m³/s/mm]
tb = 0.556 × A / qpR                     [h]
```

**Shape of the hydrograph (since v0.8.0, section 3.4.7):**
```
q(t) = qpR × [(t/tpR) × exp(1 - t/tpR)]^K          [m³/s/mm]
Γ(K) × (e/K)^K = V / (qpR × tpR),  V = A × 1000 m³   (1 mm over A)
```

tb is the base of the triangle with the peak qpR and the volume of 1 mm: a parameter of the method (`time_base_min`), not the end of the hydrograph.

#### 3.4.4 Choosing the Ct and Cp Coefficients

| Catchment type | Ct (SI) | Cp | Description |
|----------------|---------|-----|-------------|
| Mountainous, steep | 1.35-1.45 | 0.60-0.80 | Fast runoff, little storage |
| Hilly | 1.45-1.55 | 0.50-0.65 | Typical conditions |
| Lowland, flat | 1.55-1.65 | 0.40-0.55 | Slow runoff, large storage |

**Note:** Ct and Cp are **inversely correlated** (larger Ct → smaller Cp)

#### 3.4.5 Code Example

```python
from hydrolog.runoff import SnyderUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Snyder does NOT need an external Tc!
snyder = SnyderUH(
    area_km2=100.0,
    L_km=15.0,      # Main stream length from the divide (longest flow path)
    Lc_km=8.0,      # Length to the centroid
    ct=1.5,         # Time coefficient
    cp=0.6          # Peak coefficient
)

# The parameters are computed automatically
print(f"tL = {snyder.lag_time_min:.1f} min")
print(f"tD = {snyder.standard_duration_min:.1f} min")

# Generating the UH for a specific rainfall duration
delta_t = 60  # min
print(f"tpR = {snyder.time_to_peak_min(delta_t):.1f} min")
print(f"qpR = {snyder.peak_discharge(delta_t):.3f} m³/s/mm")

result = snyder.generate(timestep_min=10.0, duration_min=delta_t)

# With HydrographGenerator
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=10.0)

generator = HydrographGenerator(
    area_km2=100.0, cn=72,
    uh_model="snyder",
    uh_params={"L_km": 15.0, "Lc_km": 8.0, "ct": 1.5, "cp": 0.6}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

#### 3.4.6 Snyder in `HydrographGenerator`: Unit Hydrograph for D = Time Step (since v0.8.0)

Discrete convolution treats the unit hydrograph as the response to 1 mm of effective precipitation in a single step `dt`. Therefore `HydrographGenerator` builds the Snyder hydrograph for a duration **D = dt** (the tLR, tpR and qpR correction from section 3.4.3), and not for the standard tD = tL/5.5 (Snyder 1938; USACE HEC-HMS, Technical Reference Manual, "Snyder Unit Hydrograph Model"; Chow, Maidment, Mays 1988):

```python
uh = snyder.generate(timestep_min=dt, duration_min=dt)   # this is how the generator computes it
```

Versions < 0.8.0 called `snyder.generate(timestep_min=dt)`, i.e. the hydrograph for tD, and convolved it in steps of `dt`: for a step shorter than tD the peak was too low and too late (tpR = tLR + D/2, tLR = tL + 0.25 (D − tD)), for a longer one too high and too early. `uh_time_to_peak_min` in the `hydrograph generate` result is tpR, and the report documents Δt equal to the step.

| Catchment 45 km², L = 12 km, Lc = 6 km, Ct = 1.5, Cp = 0.6, CN 72, beta rainfall 50 mm/120 min, step 5 min | before v0.8.0 (D = tD = 59.0 min) | since v0.8.0 (D = 5 min) |
|------|------:|------:|
| Unit hydrograph: time to peak tp [min] | 354.2 | 313.7 |
| Unit hydrograph: peak qp [m³/s/mm] | 1.379 | 1.432 |
| Runoff hydrograph: Qmax [m³/s] (time [min]) | 9.76 (405) | 10.12 (365) |

The values since v0.8.0 include the shape of section 3.4.7, whose peak is qpR; with that shape the step alone moves Qmax from 9.71 m³/s at 405 min (D = tD) to 10.12 m³/s at 365 min (+4.3%). For a step equal to tD the correction vanishes (tLR = tL): the generator uses the hydrograph of the standard duration.

#### 3.4.7 Shape of the Snyder Hydrograph and the End of Its Recession (since v0.8.0)

Snyder's method gives the peak (tpR, qpR), the widths W50 and W75 and the triangular time base tb, not a curve. Versions < 0.8.0 took a gamma curve of one fixed shape (n = 3.7, `(t/k)^(n-1) × exp(-t/k)` with k = tp/(n-1)), scaled it to qp, cut it at tb and rescaled the ordinates to 1 mm. tb = 0.556 × A / qpR shrinks as Cp grows while that curve does not change, so the cut came at 4.6% of the peak for Cp = 0.6 and at 20% for Cp = 0.8 (Δt = 5 min), and from Cp ≈ 2 on at or before the peak itself. The runoff hydrograph then ended in a near-vertical drop (Hydrograf front-end test of 2026-11-01). The peak of the ordinates was not qpR either: Cp acted only through the cut (Kamiennik, Ct = 1.65: Cp 0.4 → 1.0 moves qpR 0.64 → 1.60 m³/s/mm, but the peak of the ordinates moved 1.02 → 1.22).

Since v0.8.0 the ordinates are the gamma unit hydrograph through the peak (Asquith and Roussel 2007, USGS SIR 2007-5243, eq. 2 and 4):

```
q(t) = qpR × [(t/tpR) × exp(1 - t/tpR)]^K          [m³/s/mm]
V = qpR × tpR × Γ(K) × (e/K)^K                      (volume of the curve)
```

K is the root of `Γ(K) × (e/K)^K = V / (qpR × tpR)` for V = 1 mm over A (`brentq` on ln K; the left side falls monotonically from +∞ to 0, so the root is unique). Ct thus sets the time of the peak and Cp its height: for Δt = tD, K ≈ 2.0, 2.8, 3.8 and 4.9 for Cp = 0.5, 0.6, 0.7 and 0.8 (the former fixed n = 3.7 corresponds to K = 2.7). In t/tpR the curve is proportional to the density of the gamma distribution with the shape K + 1 and the rate K, so by default the ordinates run until 99.99% of the volume has passed, `P(K + 1, K × t/tpR) = 0.9999`, where the curve is below 0.1% of the peak; they are then rescaled to 1 mm (sampling at the step). A shorter `total_duration_min` still cuts the recession. `time_base_min` stays tb. A Cp for which no hydrograph of 1 mm has the peak qpR (K outside 10⁻¹²…10¹², i.e. Cp below about 10⁻¹² or above about 10⁵) raises `InvalidParameterError`.

| Kamiennik catchment (Hydrograf): A = 37.23 km², L = 15.22 km, Lc = 6.92 km, CN 67.9, PMAXTP 1 h p = 1% (46.35 mm, beta), AMC II, step 5 min | Ct 1.65, Cp 0.8: before | after | Ct 1.5, Cp 0.6: before | after |
|------|------:|------:|------:|------:|
| K | 2.7 | 4.16 | 2.7 | 2.41 |
| Unit hydrograph: peak [m³/s/mm] (qpR) | 1.100 (1.282) | 1.282 | 1.140 (1.057) | 1.057 |
| Unit hydrograph: end [min] (ordinate there, % of the peak) | 970 (20.2) | 1680 (0.04) | 1175 (4.6) | 2155 (0.03) |
| Runoff hydrograph: Qmax [m³/s] (time [min]) | 3.852 (410) | 4.487 (410) | 3.990 (375) | 3.701 (375) |
| Runoff hydrograph: below 1% of Qmax from [min] / end [min] | 1015 / 1025 | 1305 / 1735 | 1210 / 1230 | 1570 / 2210 |
| Steepest 5-minute fall [% of Qmax] (time [min]) | 5.7 (995) | 1.2 (600) | 1.3 (1195) | 0.9 (600) |

The volume (130,400 m³) does not change. Before the change the steepest fall was the cut-off at the end of the recession, after it it lies on the falling limb at about 70% of the peak.

---

### 3.5 Hydrologic Soil Groups (HSG) and Area-Weighted CN (`hydrolog.soil`, since v0.8.0)

HSG (A-D) is one of the two factors of the CN number (the other is land cover). The `hydrolog.soil` module determines HSG from clay, sand and silt content; the rules and mapping were transferred from Kartograf 0.8.0 (`kartograf.hydrology.hsg`, Kartograf ADR-025), and Kartograf remains responsible for downloading rasters (`download_soil`).

#### 3.5.1 Data Flow Diagram

```
Kartograf download_soil (property = clay | sand | silt, SoilGrids, g/kg)
        │   three GeoTIFF rasters: same CRS, grid and size
        ▼
hydrolog.soil.hsg_from_rasters(clay, sand, silt, output_path)      [extra hydrolog[raster]]
        │   USDA texture class (12 classes) → HSG; GeoTIFF uint8: 0 = no data, 1-4 = A-D
        ▼
hydrolog.soil.hsg_statistics(hsg_path, bbox=None, bbox_crs=None)
        │   area (m², ha) and share (%) of groups A-D and of no data
        ▼
get_cn(HSG, land cover, condition) × group area  →  calculate_weighted_cn(...)
        ▼
Catchment CN  →  SCSCN / HydrographGenerator
```

The same steps in the CLI: `soil hsg`, `soil hsg-stats`, `cn weighted`; the texture class and HSG of a single sample are given by `soil texture` (`classify_usda_texture`, `texture_to_hsg`).

#### 3.5.2 Texture Classification (USDA Triangle)

Class definitions of the USDA Soil Survey Manual (Soil Science Division Staff, 2017, ch. 3, pp. 122–124), declared by the spec `usda_texture` (`hydrolog.soil.texture.USDA_TEXTURE`, card in [FORMULAS.md](FORMULAS.md#usda_texture), [ADR-0066](decisions/0066-the-soil-texture-and-hsg-tables-as-data.md)). The definitions are the data file `src/hydrolog/_data/tables/usda_texture_classes.csv`: one row per inequality `a·clay + b·sand + c·silt <relation> k` percent of the sum of the three fractions, with the class, its alternative (sandy loam and silt loam have two), the page and the Manual's words; a class holds where every row of one of its alternatives holds. "X to less than Y percent" includes X and excludes Y (sandy loams: "7 to less than 20 percent clay"); the sand ranges the Manual also gives for sands and loamy sands follow from their inequalities. The twelve definitions do not overlap and leave no gap, so every composition belongs to exactly one class: there are no ties on the boundaries, and the order of the rows does not matter.

- The rows compare the **amounts** of the fractions with their sum (without division, in `float64`, after scaling the three by one power of two), so the result does not depend on the unit (%, g/kg) as long as it is common to the three rasters, and integer amounts on the class limits are classified exactly. Kartograf 0.8.2's own copy of the rules gives the same class on all 5,151 integer percent and 501,501 integer g/kg compositions (frozen oracles in `tests/oracles/`).
- A sum equal to zero has no texture: `classify_usda_texture` and `soil texture` refuse it (`precondition_failed`, constraint `positive_total`). The array classifier gives such a cell, and a cell with a NaN or infinite amount, the code of `loam` as a placeholder (Tier B `usda_texture_codes`); in `classify_hsg` such a cell (all three fractions equal to 0 is the SoilGrids convention for gaps) is no data.
- No data (code 0) is also NaN/±Inf and a value equal to the `nodata` marker of any of the three rasters. A negative amount in a cell with data is an error.

#### 3.5.3 Texture → HSG

Declared by the spec `texture_hsg` (`hydrolog.soil.texture.TEXTURE_HSG`, card in [FORMULAS.md](FORMULAS.md#texture_hsg)); the table is the data file `src/hydrolog/_data/tables/texture_hsg.csv`, each row with the source it follows.

| HSG | Texture classes |
|-----|-----------------|
| A | `sand`, `loamy_sand` |
| B | `sandy_loam`, `loam`, `silt_loam`, `silt` |
| C | `sandy_clay_loam`, `clay_loam`, `silty_clay_loam` |
| D | `sandy_clay`, `silty_clay`, `clay` |

The table is TR-55's (USDA-SCS 1986, appendix A, p. A-1, for disturbed soil profiles) for eight classes. Three follow the textures NEH 630 ch. 7 (2009, p. 7-2) names as typical of a group instead: `sandy_loam` = B, **stricter** than TR-55's A (a higher CN), and `clay_loam` and `silty_clay_loam` = C, **milder** than TR-55's D (a lower CN); `silt`, which TR-55 does not list, takes the B of `silt_loam` (Kartograf ADR-025, decision b). NEH 630 ch. 7 would also put `loam` and `silt_loam` in C and `loamy_sand` in B; the table keeps TR-55's groups for them (an open question of ADR-0066). Changing the `TEXTURE_TO_HSG` table changes CN for every user.

#### 3.5.4 Area Statistics

- Cell area: for a **geographic** coordinate system it is computed geodetically for each raster row (it depends on latitude), for a **projected** one from the affine transform.
- The `percent` of groups A-D is the share of the area **with data**, the `percent` of no data is the share of the total area; the sums of the groups and of no data give `total_area_m2`.
- An optional `bbox` rectangle (with `bbox_crs`) clips the statistics, taking into account the share of edge cells.

#### 3.5.5 Code Example

```python
from hydrolog.runoff import calculate_weighted_cn, get_cn
from hydrolog.soil import hsg_from_rasters, hsg_statistics   # requires hydrolog[raster]

hsg_from_rasters("clay.tif", "sand.tif", "silt.tif", output_path="hsg.tif")
stats = hsg_statistics("hsg.tif")

# Area-weighted CN (a single land cover, e.g. meadow in good condition)
parts = [(get_cn(g, "meadow", "good"), s.area_ha)
         for g, s in stats.groups.items() if s.area_ha > 0]
cn = calculate_weighted_cn(parts)
```

> **Note.** HSG is not a CN number. With several land covers, the CN parts are pairs (HSG × land cover), and intersecting the HSG raster with the land cover raster is done outside Hydrolog.

---

### 3.6 Minimum Flows: the Fisher–Tippett Distribution for Minima (`LowFlowAnalysis`, fix in v0.8.0)

`LowFlowAnalysis.fit_fisher_tippett()` fits to the annual minima (hydrological year XI-X, i.e. November-October) a distribution of **smallest** values: the generalised extreme value (GEV) distribution for minima, whose special cases are the Gumbel distribution for minima and the three-parameter Weibull distribution.

#### 3.6.1 Formulas

```
Distribution function of annual minima x:

   F(x) = 1 - exp( -( 1 + c × (x - loc) / scale )^(1/c) ),     1 + c × (x - loc) / scale > 0

   c → 0   Gumbel distribution for minima:  F(x) = 1 - exp( -exp( (x - loc) / scale ) )
   c > 0   minima have a lower bound  loc - scale / c  (Weibull with shape 1/c)

Quantile with non-exceedance probability p = 1/T (the flow that occurs once in T years
as equal or smaller):

   Q_T = loc + scale / c × ( (-ln(1 - p))^c - 1 )
```

Because the sample minimum is the negated sample maximum with the sign changed, `min(x) = -max(-x)`, the parameters are estimated by maximum likelihood from the **negated** minima, by the search of section 3.10 for the GEV (`scipy.stats.genextreme`), and the quantile is `Q_T = -genextreme.isf(p, c, loc=-loc, scale=scale)`. The reported `shape` is the `c` parameter from `scipy.stats.genextreme` (i.e. minus the shape parameter ξ in the usual GEV notation).

> **Change in v0.8.0 (bug fix).** Versions < 0.8.0 fitted the distribution of **maxima** directly to the minima and read its quantile at the point p. That is the mirror-image distribution: it approximates the centre of the sample correctly, but its left tail is not the tail of the distribution of smallest values, so the quantiles of rare low flows were biased, increasingly so with T, and could be negative. For a synthetic sample of 1000 annual minima from the Gumbel distribution for minima (loc = 50, scale = 8), the quantile for T = 100 years was **−3821**, and since v0.8.0 it is **13.26** (theoretical value 13.20). For the Weibull distribution (k = 2, loc = 1, scale = 5) for T = 100 years: 1.24 → 1.51 (theory 1.50), for T = 1000 years: 0.33 → 1.18 (theory 1.16).

> **Change of 2026-11-18 (bug fix).** Up to 0.8.1 the parameters were those of scipy's `genextreme.fit`, which starts from the scale 1 and stopped far from the maximum of the likelihood on the minima of small streams. For 20 annual minima of a small stream (0.0007–0.0678 m³/s, `tests/unit/test_maximum_likelihood.py`) it ended at c = −0.718 with the log-likelihood 48.41 and gave Q10 = **−0.047** and Q100 = **−0.586** m³/s; the maximum, 54.537 as in R's `evd` and `extRemes`, lies at c = 0.176, with Q10 = **0.0175** m³/s and Q100 left out (below 0: the fitted distribution reaches 0 once in 77 years). Of 100 samples of 20 or of 30 minima of a Weibull distribution (shape 1.5, scale 0.05 m³/s) the old fit stopped short of the maximum in 21–23 and missed Q10 or Q100 by more than 5 % in 7–9.

#### 3.6.2 Limitations

- A discharge cannot be negative, but the fitted distribution may reach below 0: for `shape ≤ 0` the minima have no lower bound, and for `shape > 0` the bound `loc − scale / shape` may lie below 0 (WMO No. 1029, 2009, sec. 7.5, wants it at 0 or above). A quantile below 0 is left out, NaN in the library and `null` in JSON, with the warning `negative_quantiles` (`details.return_periods`, those left out, and `details.zero_return_period`, 1 / F(0) [years], at which the fitted distribution reaches 0). A stage keeps its quantiles, since its zero is the gauge's: `stats low-flow` with `half_year_file` and `parameter` H, or `fit_fisher_tippett_minima(..., discharge=False)`.
- Maximum likelihood needs 4 annual minima, more than the three parameters, not all equal: the spec `fisher_tippett_minima` refuses fewer or equal minima with `validation_error`, `details.reason` `precondition_failed` and `details.constraint` `enough_values` or `values_not_all_equal`, and `stats low-flow` needs 4 complete hydrological years (with fewer it fails with `calculation_error`, `details.count` and `details.minimum`). When the search runs to c = 1 the likelihood has no maximum: the lower bound sits at the smallest minimum, where the density of c ≥ 1 is infinite (Smith 1985). The search covers −1 < c < 1 (a GEV of c ≤ −1 has no mean), and minima of which more than half are tied at the largest have no maximum either. A search that ends at an end of these shapes or does not settle fails the precondition `likelihood_has_a_maximum` (`validation_error`, `precondition_failed`), and a negative discharge minimum is refused with `outside_physical_range` (`details.constraint` `discharges_not_negative`) ([ADR-0055](decisions/0055-the-frequency-estimators-refuse-by-preconditions-and-search-within-bounds.md)). Short records meet it often (of 100 samples of 20 and of 30 minima of a Weibull distribution of shape 1.5, 31 and 19).
- Three parameters from a few decades of data are uncertain, especially the shape, and with it the quantiles of rare low flows (with fewer than 10 years of data the result carries a warning).
- The Kolmogorov-Smirnov test is informational (`ks_valid = False`: the parameters were estimated from the same data).

#### 3.6.3 Annual Minima (and Maxima): Complete Hydrological Years Only (fix in v0.8.0)

The annual minima of `LowFlowAnalysis` and the annual maxima of `stats flood-frequency` (from a daily series) are extremes of **whole years of observation** (KZGW 2017; WMO No. 1029, 2009): a hydrological year (1 November – 31 October) enters the sample only if the series has a value for **every** day of the year — 365 days, or 366 for a year containing 29 February (a so-called leap year: 1 November 2019 – 31 October 2020 has 366 days). A missing date or `NaN` excludes the whole year, because the year's maximum or minimum could have occurred on the day without a value. Omitted years (with the number of days with data) are reported by the notice `incomplete_years` and the result field `incomplete_years`; the library (`LowFlowAnalysis.annual_minima()`) warns with `UserWarning`, and a series without a complete year is a `CalculationError`. Practical consequence: an export covering calendar years (1 January – 31 December) loses the first hydrological year (without November and December) and the last one (only November and December).

> **Change in v0.8.0 (bug fix).** Versions < 0.8.0 took the extreme from every year present in the dates, including an incomplete one. For a synthetic calendar series 1991–2020 (a flood on 15 March and a low flow on 15 September every year), the sample had 31 "years", including 2021 with only November and December 2020 (maximum and minimum equal to the base level 5.0, with the median of complete years 13.0 and 2.2). Since v0.8.0 the sample has 29 years (1992–2020): GEV for T = 100 years **16.08 → 16.35**, Fisher–Tippett for T = 100 years **2.002 → 1.968**. For a series with gaps: fill in the data or (for maxima) supply the annual maxima directly, without dates.

#### 3.6.4 Empirical Frequency of Minima: the Non-Exceedance Convention (fix in v0.8.0)

In low-flow analysis, the return period *T* belongs to the **non-exceedance** probability *F = 1/T* (a flow equal or lower once in *T* years; WMO No. 1029, 2009; Tallaksen and van Lanen, 2004) — this is how the `fisher_tippett` quantiles are computed. The empirical positions of `LowFlowAnalysis.empirical_non_exceedance()` (result `LowFlowEmpiricalFrequency`, the `empirical` block of the `stats low-flow` command) follow the same convention: annual minima in ascending order (`values_ascending`), the *m*-th smallest has

```
Weibull (default):  F_m = m / (n + 1)          Hazen: (m − 0.5) / n          Cunnane: (m − 0.4) / (n + 0.2)
T_m = 1 / F_m                                  (the deepest low flow in n years: T = n + 1)
```

The points (F, value) therefore lie on the same plot as the `fisher_tippett` quantiles (`non_exceedance_probabilities = 1/T`). `LowFlowAnalysis.empirical_frequency()` still returns *exceedance* positions (values descending, `P = i/(n+1)`), i.e. the opposite side of the same sample (`F = 1 − P`).

> **Change in v0.8.0 (bug fix).** The `empirical` block in `stats low-flow` was the result of `empirical_frequency()`, so next to `fisher_tippett.return_periods` using the non-exceedance convention it placed `return_periods` using the exceedance convention. For `tests/fixtures/daily_flows_3y.csv` (minima 1.79; 1.88; 1.66) the deepest low flow 1.66 had T = **1.33** (P = 0.75), and since v0.8.0 it has F = 0.25 and T = **4**. Since 2026-11-18 the command needs 4 complete years; of the 15 of `tests/fixtures/daily_flows_15y.csv` the deepest low flow, 0.67, has F = 1/16 and T = 16.

```python
from hydrolog.statistics import LowFlowAnalysis

analysis = LowFlowAnalysis(daily_flows, dates, return_periods=[10, 50, 100])
ft = analysis.fit_fisher_tippett()
print(ft.parameters)   # {"shape": ..., "loc": ..., "scale": ...}
print(ft.quantiles)    # flow [m³/s] once in 10, 50, 100 years; NaN below 0 (negative_quantiles)
```

The same analysis in the CLI: `hydrolog stats low-flow --input-file q_dobowe.csv --value-column Q --date-column date --return-periods 10,50,100`.

### 3.7 Time of Concentration from a Catchment (`WatershedParameters.calculate_tc`, `tc watershed`; fixes in v0.8.0)

`WatershedParameters.calculate_tc(method)` and the `tc watershed` command compute tc with the chosen method from the catchment fields. Each argument of the formula is the field the method's source defines, with no substitute ([ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md), `hydrolog._ranges.TC_INPUTS`): a missing field is `validation_error` with `details.reason` `missing_field` naming it, whatever other fields the catchment has. `WatershedParameters.tc_parameters(method)` returns the arguments; the same numbers appear in the command's `result.parameters` and in the time of concentration section of the report.

| Method | Length | Slope and other inputs | Source |
|--------|--------|------------------------|--------|
| Kirpich | `flow_path_length_km`: the longest flow path, from the outlet to the hydraulically most distant point of the watershed (usually on the divide, possibly on a ridge inside it) | `flow_path_slope_m_per_m`: elevation of that point minus the outlet, over the length | Fang et al. 2005 (TxDOT 0-4696-1), eq. 3.14; Mota and Kobiyama 2015 |
| NRCS | `flow_path_length_km` (the flow length ℓ, most distant point to outlet) | `mean_slope_m_per_m` (average land slope Y, not the slope of the flow path), `cn` | USDA-NRCS 2010, NEH 630 ch. 15, eq. 15-4 |
| Giandotti | `channel_length_km` (main channel) | H = `elevation_mean_m` − `elevation_min_m` | Grimaldi et al. 2012 |
| FAA | **`overland_length_km`** | **`overland_slope_m_per_m`** (slope of the overland surface), `runoff_coeff` (C, table I) | FAA 1970, AC 150/5320-5B, fig. 7 |
| Kerby | **`overland_length_km`** (up to a defined channel) | **`overland_slope_m_per_m`**, `retardance` (N) | Kerby 1959 (Roussel et al. 2005) |
| Kerby-Kirpich | `overland_length_km`; channel = `flow_path_length_km` − `overland_length_km` | `overland_slope_m_per_m`; the channel at `flow_path_slope_m_per_m`, the slope of the whole path; `retardance` | Roussel et al. 2005 (TxDOT 0-4696-2), supplement; TxDOT HDM ch. 4 s. 11; Cleveland et al. 2012 (TxDOT 0-6382-P1) |

- **The longest flow path** (`flow_path_length_km`, `flow_path_slope_m_per_m`) runs from the hydraulically most distant point of the watershed (the cell with the greatest flow distance to the outlet; usually on the divide, but possibly on a ridge inside the watershed) to the outlet; its slope is the elevation of that point minus the outlet elevation, over its length. Hydrograf's hydraulic length is this length. Before v0.8.0 Kirpich and NRCS took the channel length, else the catchment length, and Kirpich the channel slope, else the mean slope, else the relief over the length (which equals Kirpich's S only when the most remote point is also the highest), and Giandotti took the catchment length without a channel and the middle of the elevation range without a mean.
- **FAA and Kerby are formulas for overland flow time** (FAA 1970, AC 150/5320-5B, fig. 7; Kerby 1959). Kerby derived his formula for flow paths up to 366 m (1200 ft; Roussel et al. 2005; TxDOT Hydraulic Design Manual, ch. 4, section 11); the FAA gives no limit of the length (its curves end at 800 ft). Before v0.8.0 the channel length and slope timed the channel with an overland flow formula, far beyond Kerby's paths. The result is the overland flow time; **the tc of a catchment with a channel is given by Kerby-Kirpich (or Kirpich)**. The later circulars AC 150/5320-5C and 5D do not have the FAA formula.
- **NRCS**: in the lag equation (NEH 630, ch. 15, eq. 15-4; TR-55 does not contain it) Y is the mean land slope of the catchment [%], "not to be confused with the slope of the flow path".
- **Kerby-Kirpich** splits the longest flow path: Kerby on the overland segment, Kirpich on the rest of the path at the slope of the whole path, with S + 0.0005 for a slope below 0.002 (Cleveland et al. 2012, pp. 1–2, eqs. 1–3). Hydrolog decides the offset per segment, by the slope of that segment; Cleveland et al. decide it for both segments by the main-channel slope, with a transitional band of 0.002–0.003 left to the engineer's judgement: a deviation declared in the spec `kerby_kirpich` ([FORMULAS.md](FORMULAS.md)). tc is therefore not monotonic in a slope at 0.002: where the offset is dropped, the Kerby part steps up by 1.25^0.2335 − 1 = +5.35 % and the Kirpich part by 1.25^0.385 − 1 = +8.97 %. Hydrolog reproduces the published examples: 24.6 + 31.9 = 56.5 min against "about 57" (Roussel et al. 2005; L 5,280 ft, overland 500 ft at 2%, N 0.40, S 0.0095), and 52.1 + 86.7 = 138.7 min against "about 140" with the low-slope offset (Cleveland et al. 2012). A flow path not longer than the overland segment is `exclusive_minimum` on `flow_path_length_km`.

Example (catchment: L = 12 km, channel 10 km with slope 0.02, longest flow path 10.5 km with slope 0.019, terrain slope 0.025, CN 72, overland flow 0.2 km with slope 0.01, C = 0.5, N = 0.4):

| Method | tc before v0.8.0 [min] | tc since v0.8.0 [min] | Reason |
|--------|-----------------------:|----------------------:|--------|
| FAA | 155.3 (warning: L = 10 km outside 0.015–3 km) | 27.7 | overland flow 0.2 km, S = 0.01 |
| Kerby | 173.2 (two warnings) | 32.8 | as FAA |
| NRCS | 463.9 | 431.0 | the flow path (10.5 km) instead of the channel; Y = 2.5% (terrain) instead of 2.0% (channel) |
| Kirpich | 105.7 | 111.8 | the flow path, 10.5 km at 0.019, instead of the channel, 10 km at 0.02 |
| Kerby-Kirpich | 138.5 | 142.9 | channel = 10.5 − 0.2 km at 0.019 instead of the given channel |

The column since v0.8.0 is computed with the constants of 0.9.0, the sources' own with exact unit conversion (Kirpich 0.0078 with L in ft, NRCS eq. 15-4b in ft, in and %); v0.8.x gave NRCS 431.4, Kirpich 111.9 and Kerby-Kirpich 143.1 min.

#### 3.7.1 `cn` Alongside a Catchment in `hydrograph generate` and `report generate`

The `cn` option given alongside a catchment is the CN of the whole calculation: it overrides the catchment's `cn` both in SCS-CN and in the time of concentration by the `nrcs` method, in which the retention S = 25400/CN − 254 of the lag equation (NEH 630, ch. 15, eq. 15-4) comes from the same CN. A catchment without `cn` also works when `cn` is given. Formerly the NRCS time of concentration took CN from the file and the effective precipitation took CN from the option. Example (CN 60 in the file, `cn` = 85, L = 12 km, Y = 2.5%, beta rainfall 50 mm/120 min; 0.9.0 constants): tc 657.1 → 321.8 min, Qmax 27.66 → 55.68 m³/s, time to peak 440 → 240 min.

### 3.8 Rating Curve Q = a·(H − H₀)^b: the H₀ Starting Point and the Plausibility (`RatingCurve`, fixes in v0.8.0 and 0.8.1)

`RatingCurve.fit()` (`hydrometrics rating-curve`) fits `Q = a·(H − H₀)^b` by least squares (`scipy.optimize.curve_fit`, bounds a ≥ 0, b ≥ 0, H₀ < min(H)) with the starting point a = 1, b = 1.5, H₀ = `h0_initial`. H₀ is the stage of zero flow, the gauge height at which the flow is zero or, for a control of irregular shape, effectively zero (WMO-No. 1044, 2010, Vol. II, eq. 1.4), not the gauge zero (the datum of the staff gauge from which the stages are read). The stages may be in any unit (IMGW-PIB's are in cm): H₀ is in that unit and a, the discharge at a head of one unit, in m³/s per unit^b, so the same curve has a 100^b times larger a with stages in m than in cm (Q = 0.012·(H − 32 cm)^1.62 is Q = 20.85·(H − 0.32 m)^1.62). Without `h0_initial` the H₀ start lies below the lowest stage by one tenth of the stage range, by at least one stage unit:

```
H₀,start = min(H) − max(1, 0.1·(max(H) − min(H)))
```

Such a start is admissible for any sign of the stages (stages below the gauge zero, e.g. −10 cm, are normal). An explicitly supplied value must be finite and lower than the lowest stage (`validation_error`).

> **Change in v0.8.0 (bug fix).** A fixed start of 0 was not lower than the lowest stage of a gauge with a reading ≤ 0, so `hydrolog hydrometrics rating-curve --water-levels=-10,5,20,40,80,120 --discharges 0.5,1.2,2.5,4.8,10.1,17.3` ended with an error ("h0_initial must be … below the lowest water level (−10), got 0.0"). Since v0.8.0 the start is −23 and the fit gives a = 0.004917, b = 1.640, H₀ = −25.17 (R² = 0.9998). On 60 synthetic curves (stages in cm and m, positive and negative, noise 1–8 %, 6–30 measurements) starts from 0.1 to 1 of the range below the lowest stage always gave the best least-squares solution.

**Plausibility (0.8.1, ADR-0041).** Every fitted curve, the curve of all the pairs and the curve of each period, is checked as the curve of one stage–discharge relation: its exponent lies from 1 to 4 (a section control gives about 1.5 for a rectangular and 2.5 for a triangular section, a channel control by Manning's equation 5/3 in a wide rectangular channel) and its H₀ lies below the lowest stage of its pairs by at most the range of their stages, min(H) − H₀ ≤ max(H) − min(H), the stages being those of the pairs given to the fit, before outliers are removed. A curve outside either bound is still given, with `plausible` false and `implausibility_reasons` `b_out_of_range`, `h0_too_low` or both, and the notice `implausible_rating_curve` (warning; `details.curves` `"all pairs"` or a period such as `"1981-1990"`, with their `b` and `h0` to six significant digits) names it. Such a curve comes from pairs of more than one relation: the daily pairs of a period that spans a change of the rating (a moved gauge zero, a changed channel) bend the least squares into a steep curve with an H₀ far below every stage. At IMGW-PIB 150170070 with `years_per_period` 10, the curves of 1981–1990 (b = 6.50, H₀ = −88 cm, stages 45–161 cm) and 2001–2010 (b = 6.62, H₀ = −179 cm, stages 6–131 cm) fail both bounds; those of 1991–2000, 2011–2020 and 2021–2024 (b from 1.90 to 2.37) and of all the pairs (b = 3.02, H₀ = −34 cm) pass. The fits are unchanged.

**Specs (0.9.0, Nogat CMP, ADR-0063).** The curve is spec `rating_curve`, the fit spec `rating_curve_fit`, the plausibility check spec `rating_curve_plausibility` and the zones spec `rybczynski_zones` of `hydrolog.hydrometrics.rating_curve` (`docs/FORMULAS.md`). The fit is least squares on Q, as before, while WMO-No. 1044 (sect. 1.12.2) fits the straight line on logarithmic paper (the six gaugings above: b = 1.640 on Q, 1.820 in logarithms). The search runs on the stages and discharges divided exactly by powers of two, with tolerances of 1e-12, so the curve of stages in cm and in m is one curve; it is checked against R's `nls(port)` (`tests/oracles/rating_curve/`): equal or smaller sums of squares. Least squares without a minimum the search reaches in 10,000 evaluations (discharges rising like an exponential) are refused with `validation_error`, `details.constraint` `least_squares_minimum`; fewer than 12 pairs, the least of WMO-No. 1044 (sect. 1.5.1), give the notice `outside_applicability` of `gaugings`. The plausibility rule is Hydrolog's own (WMO's fig. II.1.5 shows a real section control of slope 4.3) and Rybczyński's source was not opened: both are `unreferenced`, and their results carry the notice `unreferenced_formula`.

### 3.9 Flood Routing (`hydrolog.routing`, `route *`; ADR-0007)

Lumped hydrologic routing turns an inflow hydrograph into the outflow hydrograph of a reach from storage and translation alone. It computes discharge only: water levels, inundation and backwater are hydraulics (Hydraulik, HEC-RAS, IMGW HD). The parameters of a model come from the user, from observed inflow and outflow, or from channel geometry; they are not derived from the catchment fields, and a routing model is not a substitute for a hydraulic model where the flood wave is not attenuated by storage and diffusion alone.

#### 3.9.1 Conventions Shared by All Models (ADR-0008)

| Item | Rule |
|------|------|
| Hydrograph table | `time_min` (minutes since any origin, strictly increasing at a regular step: every step within 1e-6 of the mean step) and `discharge_m3s` (not negative, finite), at least two ordinates. An irregular table is refused, nothing is resampled (`details.reason`: `irregular_step`, `not_increasing`, `negative`, `length_mismatch`, `too_short`, `not_finite`) |
| Initial condition | the outflow at the first ordinate equals the inflow there (steady state) unless `initial_outflow_m3s` is given |
| Tail | the outflow outlasts the inflow: the time axis is extended after the last inflow ordinate, where the inflow is held, until the last outflow differs from the final inflow by at most 0.1 % of the inflow peak and the water still stored above its steady amount is below 0.1 % of the inflow volume; at most ten times the inflow duration (at least 100 steps), otherwise the series ends with the warning `tail_truncated`. `extend_min` fixes the extension (`0` adds none). The notice `tail_extended` reports the added minutes |
| Balance | volumes are trapezoid sums; `balance_error_m3` = inflow volume (on the extended axis) - outflow volume - change of storage: zero to rounding for the recurrences, unless the scheme ran on a refined time step; the quadrature error of the trapezoid rule where the outflow is not a recurrence of the ordinates (the exact cascade, 3.9.5) |
| Non-negativity | a non-negative inflow gives a non-negative outflow; a scheme that returned a negative outflow is a `calculation_error` (a bug, not an input) |
| Notices | accuracy limits are notices of the result, never errors |

#### 3.9.2 Lag (`LagReach`, `route lag`)

```
O(t) = I(t - lag)        before the first ordinate: I = the initial outflow
```

The hydrograph is translated without attenuation, as in HEC-HMS (Lag): for a short reach with a predictable travel time. A lag that is a whole number of time steps shifts the ordinates exactly; otherwise the shifted ordinates are interpolated linearly between ordinates, which flattens sharp peaks (notice `lag_interpolated`). The storage of the reach is the water in transit, `lag` times the inflow. A shift by whole steps is exact (the identity tested in `tests/unit/test_routing_core.py`).

```python
from hydrolog.routing import Hydrograph, LagReach

inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], timestep_min=30.0)
result = LagReach(lag_min=60.0).route(inflow)
print(result.outflow.time_to_peak_min, result.peak_delay_min)   # 120.0 60.0
```

#### 3.9.3 Muskingum (`MuskingumReach`, `route muskingum`)

```
S = K [X I + (1 - X) O]          K travel time [min], X weight, 0 <= X <= 0.5
O_t = c_current I_t + c_previous I_{t-1} + c_outflow O_{t-1}        D = 2K(1 - X) + dt
c_current = (dt - 2KX) / D     c_previous = (dt + 2KX) / D     c_outflow = (2K(1 - X) - dt) / D
```

The storage is a prism (`K O`) plus a wedge (`K X (I - O)`); the continuity equation over a step with the trapezoid rule gives the recurrence (McCarthy 1938; Chow, Maidment and Mays 1988; [HEC-HMS Muskingum model](https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-model)). The weights sum to 1, so a steady state is kept. `X = 0` is a linear reservoir (maximum attenuation, the scheme of `ClarkIUH`), `X = 0.5` a wave that does not attenuate. Whatever the step, the first two moments of the discrete impulse response are those of the continuous model: the mean delay is `K` and the variance `K²(1 - 2X)`.

**Positivity window.** The three weights are non-negative only when `|2KX| <= dt <= 2K(1 - X)`. Below `2KX` the weight of the current inflow is negative, so the first ordinate of a rising limb takes water out of the outflow; above `2K(1 - X)` the weight of the previous outflow is negative and the outflow oscillates. With `K = 20 h`: `X = 0`: `dt` from 0 to 40 h; `0.25`: 10 to 30 h; `0.5`: exactly 20 h.

**Sub-reaches.** The reach is divided into `N` equal sub-reaches of `K/N`, in series, each with the same `X` and each starting with the initial outflow (HEC-HMS). The mean delay stays `K` and the variance becomes `K²(1 - 2X)/N`: more sub-reaches, less attenuation. Every sub-reach has to be inside the window, that is `2KX/dt <= N <= 2K(1 - X)/dt` (`hydrolog.routing.muskingum.subreach_window`). Unless `subreaches` is given, `N` is `K/dt` rounded to the nearest whole number (a half goes up), the HEC-HMS rule that the travel time of a sub-reach is about one time step. The window is symmetric about `K/dt`, so that number is inside it whenever the window holds any whole number. A `subreaches` given by the caller is never changed: outside the window it is a `validation_error` (`details.reason` `unstable_timestep`, `details.minimum` and `details.maximum` the window, `details.timestep_min` the step).

**When no whole number fits** (`K` shorter than the step allows, or `X` near 0.5 with `K/dt` not a whole number) every time step is divided into the fewest equal sub-steps, from 2 to 100, for which a window exists; the inflow is interpolated linearly, the scheme runs on the sub-step and the outflow is read at the original ordinates (notice `substeps_added`). The volume balance then has the sampling error of the trapezoid rule on the original ordinates, which `balance_error_m3` reports. If 100 sub-steps give no window (`K` shorter than `dt / (200 (1 - X))`, or `X = 0.5` with `K/dt` not a ratio of small whole numbers) or the divided series would have more than 1,000,000 ordinates, the reach is refused (`validation_error`, `details.option` `k_min`, `details.reason` `unstable_timestep`); `route lag` has no storage and no such limit.

**Storage and balance.** The storage is the sum over the sub-reaches of `K/N [X I_j + (1 - X) O_j]`, where `I_j` is the inflow of sub-reach `j` (the outflow of `j - 1`); at the first ordinate every sub-reach but the first is fed by the initial outflow. The steady storage is `K` times the final inflow. The balance error is zero to rounding because the trapezoid continuity holds in every sub-reach and the flows at the junctions cancel.

**Reference values.** The [University of Iowa handout](https://user.engineering.uiowa.edu/~flood/handouts/EX-L27-Muskingum-soln.pdf) (Lesson 27) routes ten inflow ordinates at `dt = 12 h` through one reach with `K = 20 h` and `X = 0.25`, starting from the steady outflow of 100 cfs. It prints the weights 0.0476, 0.5238 and 0.4286 and the outflow to 0.1 cfs, so a printed value is right to 0.05 cfs:

| Time (h) | 12 | 24 | 36 | 48 | 60 | 72 | 84 | 96 | 108 | 120 |
|---|---|---|---|---|---|---|---|---|---|---|
| Inflow (cfs) | 100 | 300 | 680 | 500 | 400 | 310 | 230 | 180 | 100 | 50 |
| Published outflow (cfs) | 100.0 | 109.5 | 236.5 | 481.3 | 487.2 | 433.1 | 358.9 | 282.9 | 220.3 | 149.2 |
| `MuskingumReach` (cfs) | 100.0000 | 109.5238 | 236.4626 | 481.3411 | 487.2414 | 433.1035 | 358.9491 | 282.8830 | 220.2832 | 149.1690 |

The largest difference is 0.049 cfs, inside the rounding of the table (`tests/unit/test_routing_muskingum.py`). The same file tests the identities: `X = 0.5` with `K` equal to `N` steps is `LagReach` of `N` steps (exact, and with a fractional number of steps the interpolated lag), `X = 0` is the Clark loop, the mean delay is `K` and the variance `K²(1 - 2X)/N` to 1e-9 for 1 to 4 sub-reaches, and `tests/unit/test_routing_kernels.py` shows second-order convergence of the sinusoidal response to the transfer function `(1 - KXs) / (1 + K(1 - X)s)`.

```python
from hydrolog.routing import Hydrograph, MuskingumReach

inflow = Hydrograph.from_step([100, 300, 680, 500, 400, 310, 230, 180, 100, 50], 720.0)
result = MuskingumReach(k_min=1200.0, x=0.25, subreaches=1).route(inflow, extend_min=0.0)
print(result.outflow.discharge_m3s.round(1).tolist())
# [100.0, 109.5, 236.5, 481.3, 487.2, 433.1, 358.9, 282.9, 220.3, 149.2]
```

#### 3.9.4 Muskingum-Cunge with Constant Coefficients (`MuskingumCungeReach`)

```
K = dx / c        X = (1 - Q / (T S0 c dx)) / 2        dx_c = (c dt + Q / (T S0 c)) / 2
```

Cunge (1969) set the numerical diffusion of the Muskingum scheme equal to the physical diffusion of the flood wave, `mu = Q / (2 T S0)`, which gives `K` and `X` of a routing distance step `dx` from the celerity `c`, the top width `T`, the slope `S0` and a reference discharge `Q` (NEH-630 chapter 17, eq. 17-20 to 17-22). `X` may be negative. The reach of length `L` is divided into `ceil(L / dx_c)` equal steps (eq. 17-21), each routed as a Muskingum sub-reach, so the volume is conserved; with `D = Q / (T S0 c)` the weights of a step are all non-negative exactly when `|c dt - D| <= dx <= c dt + D` (the window of 3.9.3 with `K = dx / c`).

**Hydraulics and reference.** `c` and `T` are given, or follow from a prismatic section (`TrapezoidalSection`: rectangle, trapezoid, triangle) and Manning's equation at the reference discharge: `c = dQ/dA` (HEC-HMS), which is NRCS `c = m Q / A` with the local slope of the rating instead of the weighted log-log slope `m` of the whole table (2 % lower for example 17-4). The reference is the inflow peak, or `reference_discharge_m3s` (EM 1110-2-1417: base flow plus half of the rise). WinTR-20 takes the peak at the upstream end of each distance step; here every step has the one reference of the reach, which is the same for one step and keeps the scheme linear and independent of the extension of the series (HEC-HMS's Muskingum-Cunge is another method: it recomputes its coefficients at every time and distance step).

**Rules of NEH-630.** (1) The hydrograph must rise from 5 % of its peak to the peak in at least 10 time steps (`rise_steps`); otherwise each step is divided into `ceil(10 / steps)` sub-steps, the inflow interpolated linearly and the outflow read at the original ordinates (notice `timestep_refined`; the balance has a sampling error). (2) Accuracy: with `Cg = c dt / dx` and `Dg = 1 - 2X` the routing is within the limits when `Dg <= exp(2.3 Cg)` (appendix B). Every grid inside the window above meets it: for `Dg <= 1` the limit is at least 1 and holds at once; for `Dg > 1` the window `|Cg - Dg| <= 1` gives `Cg >= Dg - 1`, and `exp(2.3 (Dg - 1)) >= 1 + 2.3 (Dg - 1) >= Dg` (checked on 73,804 random grids as well, the closest margin is 0.0017). A grid beyond the limit is therefore one that the planner replaced: it keeps the NRCS number of steps when the window allows it, otherwise takes the largest number of steps inside the window (`subreaches_adjusted`), or divides the time step further (`substeps_added`), and reports the grid of the NRCS rule when it was beyond the limit (`accuracy_limit`, ADR-0008). A grid that needs so many sub-steps that the series would have more than a million ordinates is refused (`validation_error`, `details.reason` `unstable_timestep`, `details.option` `times_min`).

**A reach without a grid ([ADR-0026](decisions/0026-a-reach-without-a-muskingum-cunge-grid.md)).** When no division of the reach and of the step into 1 to 100 sub-steps has a window, the reach is not refused. Typically the diffusion length `D` is long against the distance `c dt` that the wave travels in a step and lies far from every whole fraction `L / n` of the reach (a flat, short or narrow reach at a large discharge): sub-steps only shorten `dt`, and the rise rule refines a long step, so no step that the run can take helps. The reach is routed as `n` equal linear reservoirs of `K = L / (n c)` with the exact kernel of the cascade (3.9.5), the Muskingum scheme with `X = 0` and no window at all. The diffusion wave of the reach has the mean travel time `L / c` and the variance `D L / c²`; `n` reservoirs have `n K` and `n K²`, so `K = L / (n c)` keeps the travel time and `n = L / D` rounded (a half up, at least 1) matches the variance as nearly as a whole number can. The warning `diffusion_dominated` gives `L`, `c`, `D`, `n` and `K` (and `X = (1 - D / L) / 2`, negative, when `D > L`), and `parameters` hold `scheme` `linear_reservoir`, `n`, `k_min` (one reservoir), `lag_min` (`L / c`) and `diffusion_length_m` instead of those of a grid; the rise rule does not apply, the volume is kept to rounding when the series ends at rest, and the outflow is not negative. Against the linear diffusion wave (`dQ/dt + c dQ/dx = (c D / 2) d²Q/dx²` on a semi-infinite channel, the exact Hayami response, checked by Crank-Nicolson to 3e-4 m3/s) on the inflow of Hydrograf's reach R2 (Nysa Szalona, 60 mm in a 120 min block, `n` 0.05 and a 5 m bottom: peak 180.5 m3/s, 5 min step) the peak is 4.9 % low for R2 itself (`L` = 7,701 m, `D` = 6,740 m, one reservoir), 0.6 % high for a 490 m reach with `D` = 9,028 m, and 7.8 % low (5 min late) with three reservoirs for `L / D` = 3.3, where one reservoir would be 21.4 % low and 70 min early; the volume is the same and the time to peak equal otherwise (ADR-0026 has the table).

**Reference values.** NEH-630 example 17-4 (`L` = 2,600 ft, `S0` = 0.00091, `dt` = 0.1 h, reference 684.18 ft3/s, `c` = 4.297 ft/s, `T` = 44.6 ft) gives `dx_c` = 2,735 ft (here 833.63 m), one step, `K` = 605.07 s, `X` = -0.2544 (printed -0.254), the weights 0.0277, 0.3556 and 0.6166 (printed 0.028, 0.355, 0.617), `Cg` = 0.595, `Dg` = 1.509 (printed 1.508) and the limit 3.93. The outflow of Table 17-18 follows from the printed coefficients to 0.0049 ft3/s, half of the printed digit, so the table was computed with the rounded coefficients; the exact weights give it to 0.24 ft3/s (0.04 % of the peak; 645.78 ft3/s at 13.1 h against 645.72 ft3/s), and varying `c`, `T` or `S0` within their printed rounding cannot remove that. Routing the same reach from its section (15 ft bottom, 2:1, `n` = 0.04) gives the table to 2.4 ft3/s (0.4 %), the effect of the 2 % lower celerity. The tests are in `tests/unit/test_routing_cunge.py` and `tests/unit/test_routing_sections.py` (the library) and `tests/unit/test_operations_route.py` (the command `route muskingum-cunge`, in SI).

#### 3.9.5 Cascade of Linear Reservoirs (`CascadeReach`, `route cascade`)

```
u(t) = (t/K)^(n-1) exp(-t/K) / (K Γ(n))        mean delay n K        variance n K²
```

The reach is `n` equal linear reservoirs `S = K O` in series. Nash (1957) showed that the response to a unit impulse is the gamma density above (the kernel of `NashIUH`); `n` need not be whole. The Kalinin-Milyukov method of the Soviet Union is the same model with a characteristic reach length `Δx_c = Q / (T S0 c)` (Cunge's expression with `X = 0`, 3.9.4): `n = L / Δx_c` reservoirs of `K = Δx_c / c` (Ponce, "Linear reservoirs and numerical diffusion"). `CascadeReach` takes `n` with `k_min`, or with `length_km` and `celerity_m_per_s`, which fix the travel time `L / c = n K`. The SSARR routing equation (Muskingum with `X = 0`, the Clark scheme of `route_muskingum_cascade`) is a trapezoid-rule recurrence of this model: its weights are not negative only for `dt <= 2K`, and its numerical diffusion grows with `dt / K`.

**Exact kernel.** The cascade is evaluated with its kernel and not with a recurrence, so every time step is allowed: there is no positivity window, no sub-reach and no sub-step. The inflow is read as the piecewise-linear interpolation of its ordinates and the outflow at an ordinate is the exact response to it. With `x = t / K`, `a = dt / K`, `P(n, x)` the regularised lower incomplete gamma function (`scipy.special.gammainc`) and `Q = 1 - P`, the response to a unit step is `P(n, x)` and to a unit ramp `S2(x) = ∫P = x P(n, x) - n P(n + 1, x)`. A piecewise-linear inflow is a sum of hats, and a hat is the second difference of the ramp over `dt`, so the outflow at ordinate `j` is `Σ h_m I(j - m)` with

```
h_0 = S2(a) / a        h_m = [S2((m + 1) a) - 2 S2(m a) + S2((m - 1) a)] / a
```

(`cascade_weights`). The weights are integrals of the gamma density against a hat, so they are not negative; they add up to 1, and `Σ m h_m a = n`, so the mean delay is exact. The code evaluates them from `V(x) = x - S2(x) = x Q(n, x) + n P(n + 1, x)`, which tends to `n` and so loses no digits at large `x`; the weights lose accuracy as `a` falls, relative to the largest weight about 1e-14 at `a = 1`, 1e-12 at `a = 0.1`, 1e-10 at `a = 0.01` and 2e-8 at `a = 0.001`.

**Start, storage and balance.** All `n` reservoirs start with the initial outflow `O_0` (the first inflow ordinate unless `initial_outflow_m3s` is given), and the inflow follows its ordinates from `I_0`, which may differ: `O_j = O_0 [1 - P(n, ja)] + I_0 [P(n, ja) - D_j] + Σ_{i>=1} I_i h_{j-i}`, where `D_j` is the mean of `P` over the step before ordinate `j`. The storage is the water of the inflow that has not yet left, `∫ I(t - τ) Q(n, τ/K) dτ`, in closed form from `V` and `∫ x Q`; at rest it is `n K I`. The outflow between the ordinates is not a straight line, so its trapezoid volume differs from its integral: `balance_error_m3` is that quadrature error, `(dt² / 12) [O'(end) - O'(start)]` to leading order, second order in `dt` and negligible when the series starts and ends at rest.

```python
from hydrolog.routing import CascadeReach, Hydrograph

inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], timestep_min=30.0)
result = CascadeReach(n=3, k_min=30.0).route(inflow)
print(result.outflow.time_to_peak_min, round(result.outflow.peak_discharge_m3s, 2))   # 120.0 16.02
```

**Reference values.** There is no published table for the cascade; the references are its definition and computations that share nothing with the code (`tests/unit/test_routing_cascade.py`). For whole `n`, the exact solution of the chain of reservoirs by the matrix exponential (outflow and storage to 1e-10, also with an initial outflow that differs from the first inflow). For any `n`, the convolution integral of the gamma density of `NashIUH` with the interpolated inflow (1e-8). The weights as the integral of `NashIUH.ordinate` against a hat (1e-11) and against 60-digit arithmetic. A unit-volume pulse of width `dt` reproduces the IUH with an error that falls with `dt²`. One reservoir by hand (`h_0 = 1/e` for `dt = K`). The trapezoid recurrence of the Clark scheme converges to the kernel with second order.

**Command.** `route cascade` takes `n` and exactly one time scale, `k_min` or `length_km` with `celerity_m_per_s` (anything else is a `validation_error`, `details.reason` `one_of`), next to the hydrograph, run and output options of `route lag`. It has no `unstable_timestep`: `parameters` hold `n`, `k_min`, the delay `lag_min = n K`, `timestep_over_k = dt / K` and the length and celerity when they were given, and the only notices are `tail_extended` and `tail_truncated`.

#### 3.9.6 Level-Pool Routing, Storage Indication (`LevelPoolReach`, `route level-pool`)

```
S2/dt + O2/2 = (I1 + I2)/2 + (S1/dt - O1/2)        working curve  Y(O) = S(O)/dt + O/2
```

A reservoir, a pond or a reach holds one storage for each outflow, and the table of rows `(S, O)` (with an optional stage) is its only parameter (NEH-630 chapter 17; [HEC-HMS Modified Puls](https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/modified-puls-model)). Continuity over a step with the trapezoid rule puts the unknown storage and outflow on one side; the outflow is read from the working curve by linear interpolation of the table, so the volume is conserved exactly (the balance error is zero to rounding unless the step was divided). The table is a polyline with both columns not decreasing; a stretch with no outflow below a crest or an invert (a dead zone) is allowed, and the pool then rests at its highest storage, full to the crest. Only differences of storage enter, so its datum is free. With `subreaches = N` the reach is `N` pools in series, each holding `S/N` for the same outflow (HEC-HMS: more of them, less attenuation).

**Step rule.** Where the storage constant `K = dS/dO` of a segment is shorter than `dt/2`, the weight of the previous outflow of the linear reservoir of that `K`, `(2K - dt)/(2K + dt)`, is negative (3.9.3 with `X = 0`): the outflow overshoots, and can go negative. NEH-630 states the rule for the whole curve, `dt <= 2 S/O` (the working curve to the right of the line of equal values), and `S/O` is a mean of the `K` below it, so a table with a sharp change of slope passes it while the outflow still overshoots the inflow peak: on 1,499 random tables (a dead zone, 3 to 10 rows) a step at 0.99 of that limit gave a peak outflow above the inflow peak in 201 of them, by up to 24 %, and in none when `dt <= 2K` is applied to each segment. The library applies it per segment (`timestep_limit_min`), from the state at rest under the lowest flow of the run up to the first row that reaches the largest, so a row for overtopping far above the flood does not shorten the step; the scheme is then monotone, which is the discrete maximum principle: the outflow stays between those flows. A longer step is divided into the fewest equal sub-steps (the inflow interpolated linearly, the outflow read at the original ordinates, notice `timestep_refined`, a sampling error in the balance); more than 100 parts are `unstable_timestep`.

**Initial state and range.** Every pool starts at rest with the initial outflow (the first inflow ordinate unless given), at the storage the table gives for it. An initial outflow outside the table is a `validation_error`; a flood that fills the reservoir beyond the last row or empties it below the first is a `calculation_error` (`table_exceeded`, `table_emptied`): the table is never extrapolated.

```python
from hydrolog.routing import Hydrograph, LevelPoolReach

pond = LevelPoolReach(storage_m3=[0, 360000], outflow_m3s=[0, 100])   # 3,600 m3 per m3/s
flood = Hydrograph.from_step([0.0, 5.0, 10.0, 5.0, 0.0], timestep_min=60.0)
print(round(pond.route(flood).outflow.peak_discharge_m3s, 3))          # 6.852
```

**Reference values.** NEH-630 example 17-1 (the channel reach of Table 17-4, `dt` = 0.5 h, 19 ordinates) is reproduced to 0.85 ft3/s (0.02 % of the 3,827 ft3/s peak), inside the 1 ft3/s of the plan but above the half unit of the print. Table 17-7 prints each average inflow rounded (4,687.5 as 4,688, and so on): those averages belong to ordinates 1 ft3/s higher at 2.5, 3.5, 4.5 and 5.5 h, and with them all 19 printed values are reproduced to 0.49 ft3/s. The storage at the peak follows from the printed 9,056 and 3,827 ft3/s. The shortest `K` of the table up to the 5,000 ft3/s peak is 0.651 h (50 to 150 ft3/s), so the limit is 78.12 min (60.83 min for the whole table) and the published step of 30 min is not divided. The other references share nothing with the code (`tests/unit/test_routing_level_pool.py`): a table of constant `K` is the linear reservoir, equal to Muskingum with `X = 0` and `N` sub-reaches to 1e-12; a tank draining through a weir has the exact solution `h = (h0^(-1/2) + C t / (2A))^(-2)`, and a tank filled by a flood is integrated with an ODE solver, both converging with second order in `dt` (the error falls by 4.0 when the step is halved); and random tables with a dead zone keep the outflow between the lowest and the highest flow of the run with the volume balance closed to 1e-9.

**Command.** `route level-pool` takes the table inline (`storage_m3` with `outflow_m3s`, and optionally `stage_m`) or as a `rating_file` with those columns, exactly one of the two (anything else is a `validation_error`, `details.reason` `one_of`; a `stage_m` next to a `rating_file` is a `conflict`, the file brings its own column), and `subreaches` (default 1), next to the hydrograph, run and output options of `route lag`. The file is read after the output has been planned; `output` must not be the `rating_file`. A bad inline table is a `validation_error` and a bad file a `data_error` with the row and the column. `parameters` hold the sub-reaches and sub-steps, the longest step of the table, the peak storage and its time and, with a stage, the peak stage and its time; the notice `timestep_refined` says that the step was divided, and a flood beyond the table is a `calculation_error`.

#### 3.9.7 Routing over a River Network (`RoutingNetwork`, `route network`)

A network is a directed acyclic graph of node objects that link by reference: a node holds the nodes that flow into it (`inflows`; in a document `from`, their ids, the convention of `StreamSegment.upstream_ids`). The classes are `Subcatchment` (type `subcatchment`, a source hydrograph), `Channel` (`reach`: any element above, routing the hydrograph of its upstream node), `Reservoir` (`reservoir`: a `LevelPoolReach`), `Junction` (`junction`: the sum of the hydrographs that flow into it) and one `Outlet` (`outlet`); `RoutingNetwork(outlet)` is the network that ends there, everything upstream of the outlet being in it. The nodes are evaluated headwaters first and, among those that are ready, the smallest id first, so neither the order of the nodes in a list or a file nor anything but the links decides the result. A node flows into one node (a bifurcation would count its water twice) and every node reaches the outlet; two outlets or none and a node that flows nowhere are errors with a `details.reason`, and in a document so are a cycle and an unknown id (objects can form neither).

**Time axes.** One step and one first time for all sources; nothing is resampled (ADR-0008). Their lengths may differ, and so do those of the outflows, which each reach extends until it has settled; a junction holds a shorter hydrograph at its last value, as a reach holds its inflow over the extension.

```python
from hydrolog.routing import (
    Channel, Hydrograph, Junction, LagReach, Outlet, RoutingNetwork, Subcatchment
)

small = Hydrograph.from_step([1.0, 4.0, 1.0], timestep_min=10.0)
large = Hydrograph.from_step([2.0, 8.0, 2.0], timestep_min=10.0)
a, b = Subcatchment("A", small), Subcatchment("B", large)
reach = Channel("R", LagReach(lag_min=10.0), inflow=Junction("J", inflows=[a, b]))
network = RoutingNetwork(Outlet("OUT", inflow=reach))
print(network.route().hydrographs["OUT"].peak_discharge_m3s)           # 12.0
```

**Reference values.** No published table exists for a network, so the tests are the identities of the plan. A one-reach network equals the single command: the table it writes is the same file, byte for byte, for each of the five methods. A junction adds; the sum of the routed parts is the routed sum for a linear reach; the order of the nodes changes nothing. `N` reaches of `K / N` in series equal one `MuskingumReach` with `N` sub-reaches: exactly (1e-12) when `extend_min` fixes the extension, and to the size of the settling tolerance when the extension is automatic, because each reach cuts its tail at 0.1 % of its inflow peak (0.099 m3/s of a 90 m3/s peak over three reaches).

**Command.** `route network` reads the document `hydrolog-network/1` ([ADR-0010](decisions/0010-route-network-document-and-output-directory.md)) inline or from `network_file`. A subcatchment has its discharges inline or in a column of `inflows_file`; a reach has a `method` and the options of `route <method>`, validated by their catalog declaration; a reservoir has those of `route level-pool`; a `rating_file` lies in the directory of the network file. A wrong document is a `data_error` for a file and a `validation_error` for the inline option, with the node and the field in `details`. `result.nodes[]` gives the peak, its time and the volume of every node and, for a reach or a reservoir, the figures of `route <method>`; the notices begin with the node id. `output_dir` writes `<id>.csv` for each selected node, which every `route` command reads again; without it the hydrographs of the selected nodes are in the result.

**Subcatchments that make their hydrograph** ([ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)). A `Subcatchment` is one lumped, homogeneous area, with no flow paths inside. It is given its hydrograph, or makes it from a `WatershedParameters`, a `RunoffModel` and a `RainfallSource`; the path of a made one is the path of `hydrograph generate`, fed with the rain of that subcatchment:

```
rainfall.hyetograph(step)  ->  SCS-CN effective rainfall (CN of the watershed, AMC, Ia)
                           ->  unit hydrograph (SCS, Nash, Clark or Snyder; tc given or from the watershed)
                           ->  discharge [m3/s] at the time step of the network, from time 0
```

`DesignStorm` is a design storm (a depth over a duration in the shape of a `Hietogram`) cut at the step of the network; `RainfallSeries` is a record, never resampled (a network of another step refuses it, `timestep_mismatch`); `CurveNumberRunoff` is `HydrographGenerator` as a `RunoffModel`, with the options of the command, and its hydrograph is the generator's to the last ordinate (`assert_array_equal`, for the four unit hydrograph models). The **rainfall belongs to the subcatchment**: two of them take it from different sources, and `RoutingNetwork(..., rainfall=)` is only a default for those that have none (`missing_field` when neither exists). A network has one time step: the one given, else that of the given hydrographs and series (they must agree), else 5 min. A warning of the library on the way (a time-of-concentration formula outside its range) is a notice of the node that caused it.

**Control points** ([ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)). An application that lets its user pick points on the streams builds the network with `ControlPointNetwork`: the outlet first, then points upstream of it. A point closes its *residual* area, the contributing area minus the areas of the points picked above it (the application computes it; Hydrolog does not know areas), and the stream between two points is a channel. Every point is a junction that adds its own residual subcatchment and the outflow of the channel of each point that flows into it:

```
Q(P) = Q_residual(P) + sum over the points U that flow into P of  route(channel U->P, Q(U))
```

so `hydrographs[P]` of the result is the discharge at the point. Where another stream joins a channel `U->D`, `add_confluence` splits it into `U->C` and `C->D` (both given, never made up) and the tributary `T` flows into `C`: `Q(C) = route(U->C, Q(U)) + route(T->C, Q(T))` and `D` receives `route(C->D, Q(C))`. The stream below the confluence is routed once, for the water of both. For a **linear** reach that is the same as routing each stream through its own copy of `C->D`, because routing is linear and a sum of routed parts is the routed sum; for a **nonlinear** one it is not. In the test (`tests/unit/test_routing_points.py`: two streams of 4 and 9 m3/s peaks, each through a 10 min lag, joining above one reach) the peak below the confluence is 7.62 m3/s with a Muskingum reach whichever way it is built, 3.91 m3/s with a Muskingum-Cunge reach (the coefficients follow the inflow peak: 6 km, 1 m/s, 25 m, slope 0.001) against 5.06 m3/s when each stream is routed through its own copy, and 3.21 against 3.03 m3/s with a pond. Removing a point keeps the points above it: they flow into the point below through the two channels in series (what the stream was), or through the one that the application gives for both; two streams that meet in the removed point keep a confluence there; a confluence that is left with one stream is dropped.

### 3.10 Flood Frequency: Fit Methods (`FloodFrequencyAnalysis`, `stats flood-frequency`; ADR-0021)

`stats flood-frequency` fits the log-normal (location 0, two parameters), GEV, Pearson III and Weibull distributions to the annual maxima and ranks them by AIC. `fit_method` (default `l_moments`) chooses how the parameters are estimated ([ADR-0021](decisions/0021-fit-methods-of-flood-frequency.md)); `all` fits each distribution by each of the four methods. Every method gives the parameters of the same scipy distributions (`lognorm` with `loc = 0`, `genextreme`, `pearson3`, `weibull_min`), and the quantiles, K-S, A² and AIC follow from them alike. Every item of `distributions` carries its `fit_method`; the result's `fit_method` is the value asked for.

Each distribution of the result also carries `densities` [1/(m³/s)]: the fitted probability density at each of its `quantiles`, in the same order (the exponential of scipy's log-density there). A quantile of T > 1 lies inside the support, where the four densities are positive. The GUI draws the density and the distribution function F = 1 − p against Q from these fields and computes nothing else.

| `fit_method` | Estimator |
|---|---|
| `mle` | Maximum likelihood. The log-normal in closed form (`scipy.stats.lognorm.fit` with `floc=0`: the mean and the standard deviation, divisor n, of ln x). GEV, Pearson III and Weibull: Nelder-Mead over (shape, location, ln scale) on the standardised sample z = (x − mean) / sd (sd with the divisor n), from the `l_moments` estimate (else the `moments` one, else the distribution of skewness 0) with its shape at least 0.1 short of the limit below and its location moved so that a bound of the support lies 0.05 beyond the sample, run again from the point found until a run gains at most 10⁻⁹ of log-likelihood (20 runs at most) and checked to be no less likely than its start; the parameters of x are the shape, mean + sd · loc and sd · scale |
| `moments` | The distribution's mean, standard deviation and (three parameters) skewness equal the sample's: the mean, the standard deviation with the divisor n − 1 and the adjusted skewness G1 = √(n(n − 1)) / (n − 2) · m3 / m2^(3/2). Log-normal: s² = ln(1 + Cv²), scale = mean / √(1 + Cv²); Pearson III: (G1, mean, standard deviation), scipy's own parameters; GEV: the shape c whose skewness is G1 (Brent's method), then the scale and the location from the variance and the mean |
| `l_moments` | The distribution's λ1, λ2 and (three parameters) τ3 equal the sample's, from the unbiased probability-weighted moments of the ascending sample: λ1 = b0, λ2 = 2b1 − b0, τ3 = (6b2 − 6b1 + b0) / λ2. Log-normal: s = 2 erf⁻¹(λ2 / λ1), scale = λ1 exp(−s²/2); GEV: c solving τ3 = 2(1 − 3^−c) / (1 − 2^−c) − 3 (Brent's method), α = λ2 c / ((1 − 2^−c) Γ(1 + c)), ξ = λ1 − α (1 − Γ(1 + c)) / c; Pearson III: α = 4/γ² from \|τ3\| by the rational approximations of Hosking and Wallis (1997), γ = 2 sign(τ3) / √α, σ = λ2 √(πα) Γ(α) / Γ(α + ½), μ = λ1 |
| `least_squares` | The minimum of Σ (x₍ⱼ₎ − Q(j / (n + 1)))² over the ascending sample and the quantiles at the Weibull plotting positions of `empirical`, by Nelder-Mead from the `moments` estimate (the scale and the log-normal and Weibull shapes searched as logarithms) |

For the moments and the L-moments (and so the start of least squares) the **Weibull distribution is the GEV of the negated sample**: −X ~ GEV(c, ξ, α) with c > 0 is X ~ `weibull_min`(1/c, −ξ − α/c, α/c). It needs a sample skewness above −1.1395 or an L-skewness between −0.1699 and 1, the values of the Gumbel distribution (c = 0).

**No parameters.** Every method needs values not all equal, and the log-normal values above 0. The moments, the L-moments and least squares need 3 values and a sample skewness or L-skewness inside the distribution's range; maximum likelihood needs one value more than the distribution has parameters (3 for the log-normal, 4 for the others). The likelihood of a three-parameter distribution has no maximum where its density is infinite at a bound of the support: placed at the closest annual maximum, the bound makes the likelihood grow without limit (Smith 1985). That happens for the GEV with c ≥ 1 (ξ ≤ −1), Pearson III with |skewness| ≥ 2 and Weibull with a shape ≤ 1, so maximum likelihood searches the shapes short of these limits (and the GEVs with a mean, c > −1, and Weibull shapes up to 50), and a search that ends within 10⁻³ of one, or at a scale of a millionth of the standard deviation (values tied at the smallest), has no maximum to give; a GEV with more than half its values tied at the smallest has none either. Each method is a formula with a spec (`fit_l_moments`, `fit_moments`, `fit_maximum_likelihood`, `fit_least_squares` of `hydrolog.statistics.frequency`), so a sample that fails one of these conditions is refused with `validation_error`, `details.reason` `precondition_failed` and `details.constraint` `enough_values`, `values_not_all_equal`, `positive_values`, `l_moments_within_distribution`, `skewness_within_distribution` or `likelihood_has_a_maximum` (up to 0.9.0 a `calculation_error` with `details.reason` `too_few_values`, `constant_values`, `non_positive_values`, `out_of_range` or `unbounded_likelihood`); a search of maximum likelihood or least squares that does not settle is a `calculation_error` with `details.reason` `not_converged`. When several combinations are fitted (`distribution = "all"` or `fit_method = "all"`) that combination is left out with the notice `distribution_left_out`, which names its distribution, its method and the reason (`too_few_values`, `constant_values`, `non_positive_values`, `out_of_range`, `unbounded_likelihood` or `not_converged`), so it is never ranked; the call fails only when none remains (all values equal, for example).

**Every method at once.** With `fit_method = "all"` one AIC ranking covers all the combinations, up to 16 (`FloodFrequencyAnalysis.fit_all` keys them `"<distribution>/<fit_method>"`). Each AIC is the log-likelihood at that method's parameters with the distribution's number of parameters, so maximum likelihood normally gives its distribution the lowest AIC of the methods: on the 11 values of the unit tests (`_FLOODS`) its GEV has the AIC 118.27 and the L-moments' GEV 118.60. The default is `l_moments` because maximum likelihood is less stable on the short samples of annual maxima.

> **Change of 2026-11-18 (bug fix).** Up to 0.8.1 `mle` was scipy's `fit`, which starts the GEV from c = −0.5 and the scale 1 and, on annual maxima of hundreds of m³/s, often stopped at a degenerate point (c of −6 to −10, the lower bound at the smallest maximum). On `_FLOODS` (95–290 m³/s) it ended at c = −6.26 with the log-likelihood −61.55 instead of −56.13 (AIC 129.1), with Q100 = **2.5·10¹²** m³/s instead of **505**; of 100 samples of 30 and of 50 maxima of a GEV (c −0.1, location 1000, scale 400 m³/s) it stopped short of the maximum in 72 and 62 (Q100 up to 10¹⁹–10²⁰ m³/s), of Pearson III and log-normal maxima fitted by the GEV in 44–55. Samples of a spread near 1 (sea levels in m, the KZGW examples of 0.8–111 m³/s) were fitted right. Pearson III and Weibull came out at their singularity, with the lower bound at the smallest maximum, and led the AIC ranking: Pearson III with AIC 102.3 on `_FLOODS`, and on KZGW 2017's Świślina at Rzepin with Q 1% = 40.5 m³/s against 51.9–58.7 from the regular fits. Four equal maxima gave a GEV of scale 0 and a Weibull Q 1% of 7·10³⁰ m³/s, three maxima a GEV Q 1% of 1.7·10²¹ m³/s.

**Outside the support: AIC null.** A fitted distribution may give no density to an annual maximum, most often a lower bound of Pearson III or Weibull above the smallest one. Its log-likelihood is −∞, so its AIC is infinite (`null` in JSON), given without the formula `akaike_information_criterion` (whose precondition `values_within_support` such a fit fails), and it ranks after the fits with a finite AIC; its quantiles, K-S and A² stay, and the notice `outside_support` names the values. With the moments and the L-moments this is frequent: in trials of 300 samples of 30 and 60 years it happened in 9–81 % of the Pearson III fits and 16–91 % of the Weibull fits. Maximum likelihood never does: such a fit is the least likely there is (up to 0.8.1 scipy's `fit` could stop at one: its Weibull of `tests/fixtures/maksima_roczne.csv` had the location 94.2, above the maxima 81.6 and 87.2; the maximum lies at 80.2).

**A² against the critical values of its fit ([ADR-0048](decisions/0048-anderson-darling-critical-values-by-a-parametric-bootstrap.md)).** A² (the spec `anderson_darling` in `docs/FORMULAS.md`) = −n − Σ (2i − 1)/n [ln F(x₍ᵢ₎) + ln(1 − F(x₍ₙ₊₁₋ᵢ₎))] over the ascending maxima (Stephens, 1974; F clipped to [10⁻¹⁰, 1 − 10⁻¹⁰], so a maximum outside the support adds a large finite term). Its critical values for a distribution given in advance (case 0: 1.610, 1.933, 2.492, 3.070, 3.857 at 15 … 1 %) do not apply to parameters estimated from the same sample, whose A² is far smaller: a GEV fitted by L-moments to 30 or 60 maxima has its 5 % point at 0.54–0.58, a log-normal at about 0.8, and the case-0 check, used until 0.9.0, almost never rejected (the audit of 2026-11-18, 2000 Monte Carlo samples). They depend on the distribution, the method, n and the shape, so each fit by L-moments gets its own `ad_critical_values` from a parametric bootstrap (Stute, González Manteiga and Presedo Quindimil, 1993): 999 samples of n values drawn from the fitted distribution (seed 20261118, so a sample always gets the same values), each refitted by L-moments, give the A² whose 85, 90, 95, 97.5 and 99 % quantiles are the critical values; a sample the L-moments cannot fit is left out. The samples outside the support of their refit are part of that distribution, which makes the upper points of Pearson III and Weibull large. The other methods refit by iterative searches (a maximum-likelihood GEV takes about 0.15 s, 999 of them minutes), so their `ad_critical_values` is `null` and A² stays a distance for comparing fits. On a bimodal sample of 40 values (20 about 100 and 20 about 200 m³/s) the GEV fit has A² = 5.96 against the 5 % point 0.62.

**Least squares follows the largest values.** Its residuals are in m³/s, and the largest annual maxima lie farthest apart, so they weigh most. On the 26 annual maxima of `tests/fixtures/maksima_roczne.csv` the GEV Q 1% is 307.3 m³/s by `mle`, 309.8 by `moments`, 324.9 by `l_moments` and 517.3 by `least_squares`.

**Verification** (`tests/unit/test_high_flows.py`). Every method recovers known parameters of every distribution to 1 % from a synthetic sample of 20,000 values (the quantiles at (i − 0.5)/n); the sample L-moments of 1, 2, 3, 4, 10 are λ1 = 4, λ2 = 2, τ3 = 0.5, computed by hand from the 10 pairs and 10 triples; the moments fit reproduces the sample's mean, variance (n − 1) and G1; least squares brings the quantiles closer to the sample than its start. The Pearson III approximation was checked against the exact τ3 = 6 I₁/₃(α, 2α) − 3: α within 3·10⁻⁵ (relative) over the whole range. For every distribution and method that fits `_FLOODS` (all but Pearson III and Weibull by maximum likelihood, which have no maximum there), the densities equal scipy's pdf at the quantiles (relative 10⁻¹²) and are above 0, from T = 1.01 to 1000 years. With `all`, those 14 combinations are each equal to their own fit, sorted by AIC, each method's in the order of its own ranking, and a left-skewed sample leaves out the Weibull fits of the moments, the L-moments and least squares and the GEV and Pearson III by maximum likelihood (`unbounded_likelihood`: their upper bound runs to the largest value).

**Verification of maximum likelihood** (`tests/unit/test_maximum_likelihood.py`). The GEV reaches the maximum log-likelihood of R's `evd`, `extRemes` and `ismev` on the seven samples of the frozen oracle in `tests/oracles` (`_FLOODS`, Coles' Port Pirie sea levels, R's ozone and four seeded samples of GEV, Pearson III, log-normal and Weibull maxima): Hydrolog's is never lower by more than 10⁻⁶, and its quantiles lie within 0.5 % of those of the most likely R fit. Pearson III and Weibull reach that of `lmomco` where its maximum is regular and are refused (`unbounded_likelihood`) where `lmomco` stops at the singularity (`_FLOODS`: skewness 2.62, Weibull shape 0.87). Coles' (2001) Port Pirie fit is reproduced (μ 3.875, σ 0.198, ξ −0.050 within half a unit of the last digit, log-likelihood 4.33906, the 10- and 100-year levels 4.29617 and 4.68814 m), and so are the GEV of `_FLOODS` (ξ 0.428, log-likelihood −56.13304, `extRemes`' quantiles within 1 %) and the small stream of section 3.6; one test asserts scipy's sign, c = −ξ, against Coles' distribution function written out. Of 30 seeded samples of 30 GEV maxima and 30 of 20 small-stream minima, each fit is at least as likely as the maximum Powell's method finds on the raw values, and each refusal is a sample on which that search, too, runs to the limit.

### 3.11 Homogeneity of Annual Maxima (`homogeneity_tests`, `stats homogeneity`; ADR-0022)

A flood frequency analysis takes the annual maxima as a sample of one distribution; a change of the catchment or of the gauge (a reservoir, a regulated reach, a moved station) breaks that. `stats homogeneity` (`hydrolog.statistics.homogeneity_tests`) checks the series with three non-parametric tests ([ADR-0022](decisions/0022-homogeneity-tests.md)). Its series is that of `stats flood-frequency`: the annual maxima of the complete hydrological years of a daily series (section 3.6.3; their hydrological years are the years), or annual maxima as values with optional years (`years` inline, `year_column` in a file: whole numbers, strictly increasing, gaps allowed).

**The split.** The first part holds the values of the years before `split_year`, the second those from `split_year` on; without `split_year` the first part is the first ⌊n/2⌋ values (an odd n puts the middle value in the second part). `split_year` need not be a year of the series (a skipped incomplete year splits between its neighbours) but must leave a value in each part: from the first year + 1 to the last year. The result gives `split_index`, the number of values of the first part (the 0-based index of the first value of the second part), and `split_year`, the year of that value (`null` without years).

| Test | Statistic | p-value (two-sided) |
|---|---|---|
| Mann-Whitney U (the two parts) | U of the first part: the pairs (x from the first part, y from the second) with x > y, a tie counting ½; about n₁n₂/2 without a difference, 0 when every value of the first part is smaller | `scipy.stats.mannwhitneyu`: exact when a part has at most 8 values and there are no ties, otherwise the normal approximation with the corrections for ties and continuity |
| Kolmogorov-Smirnov, two samples (the two parts) | D = max \|F₁(x) − F₂(x)\|, the largest distance between the empirical distribution functions of the parts | `scipy.stats.ks_2samp`, exact without tied values; with ties (m·n < 10 000) the exact P(D ≥ d) over the splits of the pooled values, ties respected, as R's `ks.test` (Schröer and Trenkler, 1995; spec `ks_exact`): scipy's p assumes no ties and is then too large (Helsel et al., 2020, Example 5.1: 0.0524 instead of 0.0478; until 0.9.0); with ties and m·n ≥ 10 000, scipy's p, conservative |
| Pettitt (the whole series) | U_t = Σ_{i≤t} Σ_{j>t} sgn(x_i − x_j) = 2 Σ_{i≤t} r_i − t(n + 1) for t = 1, …, n − 1 (r_i the ranks, mid-ranks for ties); K = max_t \|U_t\| | p ≈ 2 exp(−6K² / (n³ + n²)), capped at 1 (good for p ≤ 0.5) |

**The change point** of Pettitt's test is the t of K (the first t if several give K), named like the split: `change_point_index` = t, the number of values before the change, and `change_point_year`, the year of the first value after the change. So `split_year = change_point_year` makes the two-sample tests compare the parts that Pettitt's test found. Pettitt (1979) and R's `trend` name the position t of the last value before the change; it is the same number as `change_point_index`, but the year given here is the next one.

**The decision.** `homogeneous` is `p_value ≥ alpha` (default 0.05), as `trend_detected` of the Mann-Kendall test is `p_value < alpha`; the command adds the notice `homogeneity_rejected`, whose `details.tests` lists the tests that reject. A short series rarely rejects: split into halves, Mann-Whitney and Kolmogorov-Smirnov can reject at α = 0.05 from 8 values (4 + 4), Pettitt's test from 11, so `homogeneous` says that a test found no difference, not that there is none. The tests take the values as independent. Fewer than 3 values and all values equal are a `calculation_error` (`too_few_values`, `constant_values`: Mann-Whitney's U has no variance and Pettitt's test no change point).

**Verification** (`tests/unit/test_homogeneity.py`, `tests/unit/test_operations_analysis.py`). A step in the middle of a deterministic series (golden-ratio steps) is rejected by all three tests and the same values without the step by none; Pettitt's K of 1, 3, 2, 5, 4 is 6 (U_t = −4, −4, −6, −2, counted pair by pair) with p = 2 exp(−1.44) = 0.474 and the change point after the third value, and of 2, 1, 2, 3 is 3 with mid-ranks and p capped at 1; the change point of a two-level step of 12 and 18 years is the first year of the second level, with K = 12 · 18, and as the split year it separates the levels exactly (U = 0, D = 1); U of the first part (not the smaller U), the split year, a year missing from the series, the errors and the series of a daily file are checked.

### 3.12 Regime, Seasonality, Harmonics, Trends and Baseflow of a Station (`stats regime`, `stats seasonality`, `stats harmonics`, `stats mann-kendall`, `stats baseflow`; plan 2026-11-13, D11; ADR-0031, ADR-0033)

These commands describe a station's daily series over a reference period: the hydrological years `first_year` to `last_year` (November to October, the whole record by default). A result that characterises the period names it (`first_year`, `last_year`, `period_years`) and carries the notice `short_reference_period` when it has fewer than 30 years (plan D1). They give the numbers of the prototypes of Obserwator's GUI mockup (`_hydro_proto.py`) on the same series, except where a step below names a difference.

**Regime (`stats regime`, `flow_regime`).** The mean flow Q̄ₘ of each calendar month is the mean of its days with a value over the period, the mean annual flow Q̄ the mean of all days with a value; Pardé's coefficient is Kₘ = Q̄ₘ / Q̄ (Pardé, 1933; spec `parde_coefficients`, [FORMULAS.md](FORMULAS.md#parde_coefficients)). Weighted by the days of their months the coefficients average one, so the twelve sum to 12 only when the months have as many days (Kłodzko 2010: 12.0003); IMGW-PIB's monthly means and annual mean of Kłodzko in 2010 are those of its daily values. The lists `monthly_mean` and `parde` run from November to October. A negative or infinite discharge is refused (`outside_physical_range`). The monthly volumes Vₘ = Q̄ₘ dₘ (dₘ the days of the month, 28.25 for February, the mean year of 1901–2099) give `spring_share` = (V_III + V_IV) / Σ V (spec `spring_share`) and Walsh and Lawler's (1981) seasonality index SI = Σ \|Vₘ − R/12\| / R, R = Σ V: 0 for equal months, 11/6 ≈ 1.83 when one month holds the whole volume. Dynowska's (1997) type (spec `dynowska_regime_type`) is read from the coefficients of the spring month, the larger of March and April, and of the summer month, the largest of June to August, with the criteria as Wrzesiński (2018, p. 250; the same words in Wrzesiński, 2017, p. 255) states them:

| `code` | Type | Criterion (Wrzesiński, 2018) | Test |
|---|---|---|---|
| 5 | pluvio-nival | the summer month's mean flow is higher than or nearly equal to the spring month's (both as a rule 130–180 % of the annual mean) | summer ≥ 0.95 · spring, tested first |
| 4 | nival-pluvial | the spring month as a rule 130–180 %, a clear summer rise to at least 100 % of the annual mean | summer ≥ 1.00 |
| 1 | nival, weakly developed | the spring month at most 130 % | spring ≤ 1.30 |
| 2 | nival, moderately developed | the spring month 130–180 % | spring ≤ 1.80 |
| 3 | nival, strongly developed | the spring month above 180 % | spring > 1.80 |

The sources name neither the months nor a number for "nearly equal": the spring month as March or April follows Perz (2019, p. 79), who applies Dynowska's criteria to the rivers of the Kłodzko basin; June to August and 0.95 are Hydrolog's reading (the mockup's `REGIME_RULE`), and the "as a rule 130–180 %" of types 4 and 5 is not tested. Dynowska's (1997) Atlas sheet itself was not available; the criteria were checked against Wrzesiński (2017, 2018) and Perz (2019). Wrzesiński's two classifications of the same 516 gauges of 1971–2010 count 24 (2017) and 33 (2018) pluvio-nival rivers, so the reading of "nearly equal" is not settled in the sources either. The limits are compared as the floats 1.3, 1.8 and 1.0 and summer with 0.95 times spring, which keeps every printed three-decimal tie in its class. `regime_type.criteria` gives the two months, their coefficients and the limits. The mean coefficients of each type in Wrzesiński's 2017 and 2018 Tables 1 give that type, and Kłodzko's discharge of 1971–2015 gives type 4, as Perz (2019) found for the same years; its June coefficient 1.0005 lies within the rounding of IMGW-PIB's monthly means above the limit of type 4.

**Seasonality of annual extremes (`stats seasonality`).** The annual maxima (`statistic` `max`) or minima of the complete hydrological years of a daily series, dated by the first day of the extreme (a year with a day without a value is skipped, notice `incomplete_years`), or IMGW-PIB's from `half_year_file`: the larger of the two half-year maxima (the winter one on a tie), the smaller of the minima, with that half-year's date, as `stats characteristic` takes them (a year without both half-years has none; an extreme without a date is left out, notice `undated_extremes`). Each date is an angle on the circle of its calendar year, θ = 2π (d − 0.5) / L, d the day of the year (1 = 1 January) and L = 365 or 366, the middle of the day (Bayliss and Jones, 1992, section 3.2; FEH vol. 3, Additional Note 16.1); the mean of the unit vectors, x̄ = Σ cos θ / n, ȳ = Σ sin θ / n, points to the mean date, `mean_day` = atan2(ȳ, x̄) / 2π · 365.25 + 0.5 (`mean_date` its `MM-DD` in a common year), and its length r = √(x̄² + ȳ²), `concentration`, is 1 when every extreme falls on one day and near 0 when they spread over the year (spec `circular_mean`, [FORMULAS.md](FORMULAS.md#circular_mean)). Bayliss and Jones turn the direction back into a day on 365 days, up to a quarter of a day earlier at the end of the year; Hall and Blöschl (2018) take the mean number of days per year, as Hydrolog's 365.25, and the day itself without the half. With a concentration near 0 the mean date says little: at r = 0 it has no direction and the formula gives 1 January, as `scipy.stats.circmean`. `winter_share` and `summer_share` are the shares of the extremes dated in November–April and May–October.

**Harmonics of the annual cycle (`stats harmonics`, `annual_cycle`).** Least squares fit of x(t) = A₀ + Σₖ [aₖ cos(2πkt/P) + bₖ sin(2πkt/P)], k = 1 … K (`harmonics`, 1 to 4, default 2), with t the day of the hydrological year counted from 0 on 1 November and P = 365.25 d, the mean year of 1901–2099 (Wilks, 2011, section 9.4; spec `harmonic_fit`, [FORMULAS.md](FORMULAS.md#harmonic_fit)). Each harmonic gives its `amplitude` Cₖ = √(aₖ² + bₖ²), its `phase_day` = φₖ P / (2πk) + 1 with φₖ = atan2(bₖ, aₖ), the day of the hydrological year of its first maximum, and its `explained_variance`, what it adds to the R² of the least squares fit of the harmonics before it (nested fits; for whole years, whose harmonics are orthogonal, Wilks's (n/2) Cₖ² / ((n − 1) s²)); `r_squared` is the R² of all K. The days with a value must leave no gap of P/(2K) days or more between them (182.6, 91.3, 60.9 and 45.7 days for 1 to 4 harmonics; Feichtinger, Gröchenig and Strohmer, 1995): a period with a longer gap, a summer of water temperature, or values all equal is refused (`precondition_failed`, `details.constraint` `year_covered` or `values_not_all_equal`). `period` fits every day of the period (the mean annual cycle), `years` each hydrological year with at least 300 days with a value that the fit accepts (a shorter year is named in the notice `short_years_left_out`, one that the fit refuses in `years_without_fit`). The command serves any daily variable: water temperature (H14), air temperature (M12), discharge. The mockup's meteorological prototype (`_meteo_proto.harmonic_fit`) puts t at the middle of the day as a fraction of its own calendar year and reads the peaks on 365 days; on the water temperature of Słupsk (1984–2025) the difference is 0.0002 °C in the amplitudes, 0.11 day in the day of the first maximum and 3·10⁻⁵ in the explained variance.

**Trends with Sen's slope (`stats mann-kendall`, `mann_kendall_test`, `sen_slope`; the specs `mann_kendall`, `sen_slope` and `sen_interval` of `docs/FORMULAS.md`, ADR-0063).** The Mann-Kendall test (Mann, 1945; Kendall, 1975) takes S = Σᵢ<ⱼ sgn(xⱼ − xᵢ) and its variance under no trend corrected for tied values, Var(S) = [n(n − 1)(2n + 5) − Σₚ tₚ(tₚ − 1)(2tₚ + 5)] / 18, the sum over the groups of tₚ equal values (Kendall, 1975; Hirsch, Slack and Smith, 1982; Gilbert, 1987, Eq. 16.3); without ties it is n(n − 1)(2n + 5)/18 as before (ADR-0033: until then a series with ties had the larger variance without the correction). Values tie when they are exactly equal: a series computed in floating point should be rounded to its precision first (the `meteo` sums are, to 1e-6 mm). Z = (S − 1)/√Var(S) for S > 0, (S + 1)/√Var(S) for S < 0, 0 for S = 0 (Gilbert's Eq. 16.4). The p-value is two-sided: from 10 values 2 P(Z > |z|), taken from the upper tail of the normal distribution (`norm.sf`, as R's `trend`; until 0.9.0 it was 2 (1 − Φ(|z|)), which is exactly 0 for |z| above about 8.3: 50 increasing values gave 0 instead of 1.3·10⁻²⁴; a p below the smallest positive float, |z| above about 38.5, is given as that float, 4.9·10⁻³²⁴); below 10 values, where the normal approximation does not apply (Kendall, 1975, p. 55, after Gilbert, 1987, p. 211), P(|S| ≥ |s|) of the exact distribution of S (Gilbert, 1987, section 16.4.1, Table A18): every distinct ordering of the values is equally likely under no trend, and the numbers of orderings with k pairs in descending order, S = N − 2k (N the pairs of unequal values), are the coefficients of the q-multinomial [n]! / Π [tₚ]! (MacMahon, 1916), so ties are exact too (`p_value_method` `exact` or `normal`; until 0.9.0 the normal approximation was used from 3 values: 7 values of Helsel et al., 2020, Example 10.3, gave 0.0069 instead of the exact 0.0028). A series of equal values has Var(S) = 0, Z = 0, p = 1. Sen's (1968) slope is the median of the N' slopes (xⱼ − xᵢ) / (tⱼ − tᵢ) of the pairs tᵢ < tⱼ, with t the `years` (`year_column` in a file) or, without them, the steps 0, 1, 2 … of the series, a missing value keeping its step. The intercept is Conover's (1980) median(x) − slope · median(t), the value of the line at t = 0 (year 0 with years). The 100 (1 − alpha) % confidence interval, given from 10 values (Gilbert, 1987, p. 218: the normal approximation it rests on holds “for n as small as 10”; `null` below), follows Gilbert (1987, section 16.5): C = z₁₋α/₂ √Var(S) with the test's tie-corrected Var(S), M₁ = (N' − C)/2, M₂ = (N' + C)/2, the limits are the M₁-th and the (M₂ + 1)-th of the ordered slopes, interpolated linearly between ranks as in Gilbert's Example 16.5 and his program (appendix B), and `null` when such a rank is outside 1 … N': for `sen_slope` itself 5 or fewer values without ties at alpha 0.05 (5 values: M₁ = (10 − 1.95996 √16.667)/2 = 0.9992), in `stats mann-kendall`, from 10 values, only an alpha below about 1.2·10⁻⁴ (until 0.9.0 this text said fewer than 5 values). Sen's slope and its interval hold every slope in memory, eight bytes each, so they take at most 5,000 values (12.5 million slopes, 100 MB); a longer series, such as a daily one, is refused (`invalid_shape`): the test and the slope assume independent values, which daily values are not, so aggregate them first (ADR-0063). The mockup's `_hydro_proto.sen_slope` differs, as the plan's sources do not: its intercept is median(x − slope · t), its limits are truncated ranks and its interval is always 95 %; `_meteo_proto.sen_slope` gives Hydrolog's numbers.

**Baseflow (`stats baseflow`, `baseflow_separation`).** The recursive digital filter of Lyne and Hollick (1979), qₜ = α qₜ₋₁ + (1 + α)/2 (Qₜ − Qₜ₋₁) and bₜ = Qₜ − qₜ when qₜ > 0, else Qₜ, with `alpha` 0.925 and `passes` 3 (forward, backward, forward, each on the baseflow of the pass before; Nathan and McMahon, 1990), in the standard of Ladson et al. (2013) and their published code: each span is reflected by 30 days at both ends (Q₃₀ … Q₁ before it, Qₙ₋₂ … Qₙ₋₃₁ after it), each pass starts its quickflow at the first value of its input and keeps it unclipped, negative too, as the state of the next day, and a baseflow below 0 becomes 0 after the last pass. A series with gaps is filtered on each gapless span of at least 60 days (`n_spans` spans, `n_values` days). `bfi` = Σ b / Σ Q over the days filtered, of the period and of each year with at least 300 of them (`years`); `series_baseflow` gives every day of `series_year`, by default the last complete year of the period (as `cumulative_year` of `stats runoff-volume`). The recession constant k is the median of the ratios Q(t+1) / Q(t) over the recession segments (`recession.n_segments`), runs of at least 5 daily falls (a missing day ends one), and `half_life_days` = ln 2 / (−ln k). It is the recession of the total flow: k is the daily constant of Qₜ = Q₀ kᵗ (WMO No. 1029, 2009, sec. 5.3, Eq. 5.1–5.3), but the segments are Hydrolog's own rule and start at any fall, the quickflow after a peak included, while WMO's baseflow recession analysis (the master recession curve) takes 7-day segments below Q70 without the days right after a peak; Hydrolog's k is therefore smaller (a faster recession): on WMO's Ngaruroro example (1963–1989, the data of R's `lfstat`) 0.932 against WMO's 0.9602 (the audit of 2026-11-18). Until 0.9.0 the method was attributed to Tallaksen (1995), an attribution that could not be verified (the review is not open) and that described a baseflow recession constant. The mockup's `_hydro_proto.lyne_hollick` clips the quickflow to 0 … Q at every step and starts each pass at 0: on Ladson's Bass River example (α = 0.98) it gives a BFI of 0.094 instead of the published 0.197, and on Kłodzko's record (1951–2025) 0.585 instead of 0.663; with that filter swapped in, Hydrolog's command gives the mockup's numbers to the last digit.

**The baseflow formulas by specs (Nogat's computation standard; ADR-0050, ADR-0063).** The filter (`lyne_hollick_filter`, spec `lyne_hollick`), the index (`baseflow_index`, spec `baseflow_index`, BFI = Σ b / Σ Q over the days with both values) and the recession constant (`recession_ratio`, spec `recession_constant`, which `recession_constant` wraps with k `null` for a series without a segment) are declared with their ranges, conventions and sources in `docs/FORMULAS.md`; the spans, the years and the series without a recession are its Tier B rows. `alpha` outside 0.9–0.98, the values its sources validated (Nathan and McMahon, 1990, 0.9 to 0.95 against manual separation, and 0.98 of Ladson et al., 2013, against chemical tracers; their sect. 2.5 and 3.1), gives the notice `outside_applicability`. A negative discharge is refused (`validation_error`, `outside_physical_range`), as is a period without flow on its days with a baseflow (`precondition_failed`, constraint `positive_flow_volume`); a year without flow on its days has `bfi` `null`. Until 0.9.0 a negative discharge was filtered as if it were one and a year or a period without flow had the index NaN (0 / 0), `null` in the JSON without a notice. Verification (`tests/unit/test_formulas_baseflow.py`): the daily baseflow of Ladson's worked spreadsheet (α = 0.98, to 17 digits) and of their Table 3, the BFI of the spreadsheet (0.19657587147728861), of their sect. 3 (0.20) and of their Table 5 (α 0.9 to 0.987); the recursion, the index and the median in exact rational arithmetic; Ladson's own R function `BFI()` run once on the Bass River and a seeded two-year series for α 0.9 to 0.987 and 3, 5 and 9 passes (`tests/oracles/baseflow/`).

**Water temperature (H15)** needs no command of its own: the days at or above 15, 20 and 25 °C and below 1 °C are `stats threshold-events` on the series of T (one call per level), the yearly maximum with its date the first degree of `stats characteristic` with `parameter` T, the annual cycle `stats harmonics`.

**Verification** (`tests/unit/test_station_regime.py`, `tests/unit/test_stationarity.py`; the mockup's numbers by a check outside the repository, plan 2026-11-13, Results). Sen's slope, interval and S reproduce Gilbert's (1987) Example 16.5 (5.5, 2.6 to 9.3 with two values in one time period) and Exercises 16.1–16.3: S = 12, Var(S) = 43.3 and Z = 1.67 with the two non-detects (ND) as one group of 2 ties (16.1), slope 0.33 and 0.23 (16.2), and the interval 0 to 0.94 built, as Gilbert does on purpose, on the uncorrected Var(S) = 44.3 (16.3); Eq. 16.3 with Example 16.2's tie groups (n = 22; 6 × 20, 2 × 23, 2 × 30) gives Var(S) = 1227.33 and, with S = +108, Z = 3.1; the mean Pardé coefficients of Wrzesiński's (2018) Table 1 give types 1 to 5; the filter reproduces the BFIs that Ladson et al. (2013) publish with their code for the Bass River at Loch (0.1965759) and for its two spans parted by missing days (0.1411197); an exact two-harmonic sinusoid is recovered (amplitudes, days of the maxima, R² = 1); the seasonality index takes its bounds 0 and 11/6; Pardé's coefficients, the spring share, the circular mean of dates and the recession constant of an exponential recession are checked against hand computations.

**The specs (ADR-0063).** `mann_kendall`, `sen_slope`, `sen_interval` (`hydrolog.statistics.stationarity`), `pettitt` and `ks_exact` (`hydrolog.statistics.homogeneity`) declare these formulas for Nogat's computation standard; `docs/FORMULAS.md` shows their equations, ranges, conventions and evidence. `tests/unit/test_formulas_trend.py` checks them against the reference cases of `tests/fixtures/formulas/trend-cases.json` (Gilbert, 1987; Helsel et al., 2020; KZGW, 2017, whose printed S counts a tied pair as −1, recorded as a discrepancy of the source; the `trend` vignette; Pettitt's Page data; Schröer and Trenkler's tied samples), the exact null distributions counted over every ordering and every split, SciPy (`kendalltau`, `theilslopes`, `ks_2samp`, `mannwhitneyu`) and R's `trend`, `modifiedmk`, `Kendall` and `stats` frozen in `tests/oracles/trend_regime/` (R 4.4.3, 2026-11-18). Mann-Whitney's U and the K-S test without ties stay SciPy's, delegated computations (CMP-1.2).

### 3.13 Meteorological Statistics of a Station (`meteo` group; plan 2026-11-13, D12; ADR-0032, ADR-0033)

The six commands read a station's daily series: Obserwator's export (`date`, `P [mm]`, `P_flag`, `Tmax [degC]`, `Tmin [degC]`, `Tmean [degC]`, `snow_cover [cm]`, `fresh_snow [cm]`; each column by its `*_column` option, the export's name by default) or inline lists with `dates`. The library functions are in `hydrolog.statistics` (`meteo_precipitation`, `meteo_spells`, `meteo_spi`, `meteo_temperature`, `meteo_snow`, `meteo_hydrothermal`, the shared rules in `_climate`). Years are calendar years, or hydrological years (XI–X, named after their end) with `year_type` `hydrological`; `first_year` and `last_year` keep the days of those years only (D1), and a result carries `first_year`, `last_year`, `period_years` and, under 30 years, the notice `short_reference_period`. The normals, the wet-day percentiles and the SPI's fits come from a reference period, by default the same years (below).

**Missing days (WMO-No. 1203, 2017, section 4.4).** A monthly mean or count needs fewer than 11 missing days and fewer than 5 in a row (4.4.1 a, d); a count is the share of the observed days with the event times the days of the month (4.3). A monthly sum needs every day (4.4.1 c), except that a value flagged `accumulated` (IMGW-PIB's reading after unread days, `P_flag` of the export; `precipitation_flag_column`) stands for the missing days just before it when, with its own day, they are fewer than 5 and the totals represent fewer than 11 days of the month; for every daily statistic such a value is a missing day (notice `accumulated_totals`). Monthly extremes take any days (4.4.1 b). An annual value needs its 12 months; annual maxima, percentile sums and spells need every day of the year, the hydrothermal season every day of April–September. A monthly normal is the mean of the years of the reference period with a value when they are at least 80 % of its years, counted from `reference_first_year` to `reference_last_year`, years outside the record included (4.4.2, no consecutive-years rule). The normal of a year, a half-year or a season is the sum of the normals of its months (precipitation; the mean of them for Tmean) and is missing when one of them is (4.3.3: "annual normals should be calculated from the monthly normals, and not from the individual annual values"), so a few years each lacking one month leave it; `normal_years` is the fewest years with a value among the twelve months (notice `normal_not_computed` with the reference's bounds). Hydrolog uses the monthly normals unrounded, where WMO recommends rounding them to 0.1 first (4.7); the difference is below the printed unit.

**Reference period of the baselines (ADR-0033).** `meteo precipitation` (`index` `sums`, `heavy`, `seasonality`), `meteo spi` and `meteo temperature` (`index` `means`) take `reference_first_year` and `reference_last_year` (years of `year_type`; another index refuses them, `not_applicable`). Each defaults to the analysed period as resolved (the result's `first_year`, `last_year`), so a call without them gives the numbers it gave before; the result names `reference_first_year`, `reference_last_year` and `reference_period_years` (its years with a value) after `period_years`. Each period keeps the days of its own years only (D1): the analysed years and the reference period are laid on separate grids, so a k-month SPI sum ending in the reference's first months needs days before the reference and is missing there even when the record has them (the normals of a winter half-year or DJF are sums of monthly normals and need no such days). The analysed years' own days give, unchanged by the reference, the sums, means and monthly and annual values, the SPI's k-month sums, the R95p and R99p sums, PRCPTOT, each year's PCI and SI and every other statistic of `period` (means, standard deviation, CV, extremes, `n_years`, `mean_pci`, `mean_si`, `mean_shares_percent`). The reference period alone gives the baselines: the normals (annual, monthly, half-year and season; the annual and monthly normals of Tmean) and with them `percent_of_normal`, `anomaly_c` and the classes of relative precipitation of `meteo spi`; the wet-day percentiles of `heavy` (`period.thresholds_mm`, `period.wet_days` and the check of at least 100 wet days); the regime of `seasonality` (the monthly normals' shares and coefficients, the PCI and SI of the normals); the SPI's gamma fits of each scale and calendar month (`period.scales[].fits`, whose `n_values` are sums of the reference) and `period.normal_mm`, `normal_years`, `months_normal_mm`. Normals are the benchmark against which observations are compared and anomalies formed, over 30 years; the climatological standard normal is the latest 30-year period ending in a year ending in 0, now 1991–2020, and 1961–1990 is kept as the reference period for long-term climate change assessment (WMO-No. 1203, chapters 2 and 3); the standard normal serves monitoring and anomaly products, the reference normal climate change (5.1), and periods longer than 30 years suit higher-order statistics such as percentiles (5.2.2). The SPI compares a k-month total with the totals of the same months in the years on record, with at least 20 to 30 years of monthly values, 50 to 60 preferred (WMO-No. 1090, 2012, chapter 2 and sections 5.1.1 to 5.1.2; McKee et al., 1993); the Copernicus European and Global Drought Observatories fit the gamma distribution on the baseline 1991–2020 (EDO and GDO SPI factsheet, 2025). The ETCCDI takes the wet-day percentiles of R95p and R99p from a base period, 1961–1990 (Zhang et al., 2011; Klein Tank, Zwiers and Zhang, 2009); its in-base bootstrap serves the temperature exceedance indices, not R95pTOT, so none is applied. A reference period under 30 years with values has its own `short_reference_period` when it differs from the analysed one; `reference_first_year` after `reference_last_year` (a bound not given takes the analysed one) is `validation_error` `range`, a reference period without a value `calculation_error` `no_values_in_period`.

**Exact sums (ADR-0033).** Every sum of daily precipitation is rounded to 1e-6 mm where it is formed, as the n-day windows of `maxima` were: the monthly totals, the half-year and season spans, the annual totals, the SPI's k-month sums and its monthly and annual totals, the yearly wet-day totals and the R95p and R99p sums of `heavy`, the wet-day totals of `intensity` and the precipitation of the hydrothermal season. A sum of 0.1-mm data is then the number nearest its decimal value (the fixture's 2020: 736.7, was 736.6999999999999; Kraków's 1990: 622.0, was 621.9999999999999), and sums equal in decimal are equal numbers, so that Mann–Kendall's S counts them as ties (section 3.12). Means (the normals, means, SDII, shares) are not rounded.

| Command, index | Method |
|---|---|
| `meteo precipitation` `sums` (M1) | Sums of months, half-years XI–IV and V–X (named after the hydrological year), seasons DJF (December of the year before), MAM, JJA, SON, years; monthly normals of the reference period, and the normals of the year, half-years and seasons as sums of the monthly ones (WMO-No. 1203, 4.3.3); each sum in % of its normal; annual mean, standard deviation (n − 1), CV, extremes |
| `maxima` (M2) | The n-day sum of a day is the sum of the n days ending on it (each window summed alone, to 1e-6 mm, so that equal sums tie), counted in the year of its last day; the yearly largest of 1 day and of `durations_days` (2, 3, 5, 10; Rx5day of the ETCCDI) with dates, the first window on a tie; monthly largest daily sums; quantiles: `stats flood-frequency` on the values |
| `days` (M5) | Days with P ≥ `thresholds_mm` (0.1, 1, 10, 20; R10mm, R20mm of the ETCCDI) per month (scaled) and year |
| `intensity` (M4) | Mean annual sum; SDII = PRCPTOT / wet days, a wet day P ≥ `wet_day_mm` (1 mm; Zhang et al., 2011) |
| `heavy` (M7) | Thresholds: the `percentiles` (95, 99) of the wet days of the reference period, quantile type 8 (Hyndman and Fan, 1996; as climdex.pcic), from at least 100 wet days; per year Σ P over P > threshold (R95p, R99p) in % of PRCPTOT (R95pTOT, R99pTOT) |
| `seasonality` (M9) | Regime of the 12 monthly normals of the reference period (share, normal / mean normal); PCI = 100 Σp² / (Σp)² (Oliver, 1980; ≤ 10 uniform, ≤ 15 moderate, ≤ 20 irregular, above strongly irregular); SI = Σ\|x − R/12\| / R (Walsh and Lawler, 1981; < 0.2 … ≥ 1.2, seven classes) of the normals and of each year |
| `meteo spells` (M6) | Runs of days with P < `threshold_mm` (`dry`) or ≥ it (`wet`), 1 mm by default (CDD, CWD of the ETCCDI), by `threshold_runs` of `stats threshold-events` (D4): a missing day ends a run (`open_start`, `open_end`); a spell over the start of a year is not cut and counts whole in the year it ends (`year`), the convention of the ETCCDI's software (fclimdex; climdex.pcic 1.1-11, `spells.can.span.years = TRUE`, "the default for fclimdex") and of ECA&D (ATBD v11, 2021, p. 20: "counted against the year in which the spell ends"), and a year wholly inside a longer spell has no longest spell (`null`, as climdex.pcic); per complete year the longest (`max_duration_days`, `max_start_date`, `max_end_date`), the spells of ≥ 10, 15, 20 days and their number; durations in the classes 1, 2, 3, 4–5, 6–10, 11–15, 16–20, 21–30, ≥ 31 of the closed spells. `spells` lists the spells of at least `min_duration_days` (1 by default: every spell); the yearly and period summaries take every spell, because CDD and CWD are yearly maxima with no minimum duration (Zhang et al., 2011; Klein Tank, Zwiers and Zhang, 2009) and a distribution of durations needs every spell |
| `meteo spi` (M8) | SPI of `scales_months` (1, 3, 6, 12): per calendar month a gamma distribution by Thom's (1958) approximation fitted to the positive k-month sums of the reference period (in at least 80 % of its years, 3 positive, not all equal), H(x) = q + (1 − q) G(x), SPI = Φ⁻¹(H) within ±3.09 (McKee et al., 1993; Edwards and McKee, 1997; WMO-No. 1090, 2012; notice `spi_not_fitted`), for each month of the analysed years (`year` of `year_type`, `month` 1–12); each month and year in % of its normal: years in Kaczorowska's (1962) classes < 50, 50–74, 75–89, 90–110, 111–125, 126–150, > 150 % (the percentage rounded to a whole percent, a half up: 74.5 % is dry; ADR-0059), months in the monthly limits < 25, < 50, < 75, ≤ 125, ≤ 150, ≤ 200, > 200 % (Tomaszewska, 1994, after Kosiba, 1948; Gąsiorek and Musiał, 2011, Table 1: Kaczorowska gave no monthly classes). The specs `spi_gamma_fit`, `spi`, `kaczorowska_class` and `month_precipitation_class` (`docs/FORMULAS.md`) |
| `meteo temperature` `means` (M11) | Monthly means of Tmean, Tmax, Tmin, annual = mean of 12; monthly normals of Tmean of the reference period and the annual normal as their mean (WMO-No. 1203, 4.3.3), the anomaly against them; extremes of Tmax and Tmin with dates |
| `days` | Frost Tmin < 0, ice Tmax < 0, summer Tmax > 25, hot Tmax > 30 °C, tropical nights Tmin > 20 °C (FD, ID, SU, TR of Zhang et al., 2011; thresholds are options), and freeze-thaw days Tmin < `frost_tmin_c` and Tmax > `ice_tmax_c` (0 °C): the „dzień przymrozkowy” of the *Słownik meteorologiczny* (2003, as quoted by Kossowska-Cezak, 2014, Prace Geograficzne 136, p. 14), of IMGW-PIB's normals 1991–2020 (product PRZYMROZKI, „TMAX>0 & TMIN<0”) and of IMGW-PIB Agrometeo. FD is in Polish „dni z przymrozkiem”: the *Atlas klimatu Polski* (2005) and KLIMADA 2.0 call it „dni przymrozkowe”, the *Słownik* and IMGW-PIB the freeze-thaw days; at Warszawa-Okęcie 1991–2020 FD is 97.9 and freeze-thaw 64.0 days a year (IMGW-PIB's TMIN_0 and PRZYMROZKI). The signs are strict as in the ETCCDI; IMGW-PIB's yearbooks count Tmin ≤ 0 and Tmax ≥ 25 or 30 °C, a few days more (Warszawa 2022: 92 against 87 frost days) |
| `degree_days` | GDD = Σ max(Tmean − 5, 0) (Wypych et al., 2017, eq. 1, with the bases 0, 5 and 10 °C); HDD = Σ (18 − Tmean) over the days with Tmean ≤ 15 °C (Eurostat, nrg_chdd metadata, 3.4; Commission Directive (EU) 2015/1127): 18 °C is the reference temperature (`heating_base_c`, Polish „temperatura bazowa”), 15 °C the heating threshold (`heating_limit_c`, Eurostat's English "base temperature", Polish „temperatura graniczna”); both sums over every day of complete months and the 12 months of the year (no growing or heating season), as both sources do. The Directive's daily mean is (Tmin + Tmax) / 2; Hydrolog takes Tmean as given (IMGW-PIB's daily mean): at Warszawa-Okęcie 1991–2020 HDD is 3407 °C·d with it and 3365 °C·d with (Tmin + Tmax) / 2 (−1.25 %), so give that mean as Tmean to reproduce Eurostat |
| `range` | DTR: monthly mean of Tmax − Tmin, annual = mean of 12 (ETCCDI) |
| `meteo snow` (M10) | Winter = the snow season 1 August – 31 July named after the hydrological year it ends in (D12's "per winter (hydrological year)", read so that late-October snow starts its own winter; on Kraków a literal XI–X year moved 6 of 64 winters); days with cover ≥ 1 cm (scaled months), largest depth and its date, first and last day with cover, fresh snow; a winter needs enough days in X–V, and the winters with a value that do not are `incomplete_years`, left out of the period's statistics; the period's median first and last day (`MM-DD`) take each date as its day of the season on a calendar without 29 February (29 February counts as 28 February), so that a date is the same day in every winter, and of an even number of winters the mean of the two middle days, rounded half to even |
| `meteo hydrothermal` (M14) | k = P / (0.1 Σt) (Selyaninov, 1928): months IV–IX with Σt = monthly mean × days for a mean above 0 °C (Skowera and Puła, 2004; Radzka, 2014), and the season: the days of April–September of each year with Tmean > 10 °C (Miś, 2026, eq. 4, "calculated for the April–September period"; Chmist-Sikorska, Kępińska-Kasprzak and Struzik, 2022, Italian Journal of Agrometeorology 1, p. 5), with both values on every day of April–September. This is not the classical season of Russian practice, every day between the stable spring and autumn transitions through 10 °C (Национальный атлас России, vol. 2), whose transition rule Hydrolog does not implement (Selyaninov's own papers are not open); at Warszawa-Okęcie 1991–2020 the mean k is 1.154, with a 5-day running mean approximating the stable period 1.196 [audit, research `meteo-indices`]. Classes ≤ 0.4, 0.7, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0, above (Skowera and Puła, 2004, p. 172; Miś and Chmist-Sikorska et al. use 0.4, 0.8, 1.1, 1.4, 1.7, 2.1, 2.6, 3.0) |

**Verification** (`tests/unit/test_meteo.py`, `tests/unit/test_meteo_reference.py`, `tests/unit/test_meteo_spells.py`): hand-computed sequences of each index (accumulated totals, scaled counts, the 80 % rule, maxima with dates, SDII, the type-8 percentile by hand, PCI 100/12 and SI 11/6 of the extreme regimes, spells cut by a missing day, Thom's estimates, the class limits, Eurostat's HDD, October snow, Sielianinov's k) and the ETCCDI counts of the fixture year 2021 (FD, ID, SU, TR, R10mm, R20mm, CDD, CWD, PRCPTOT, SDII, R95pTOT) counted from the rows of `tests/fixtures/meteo_daily.csv`; the baselines of a reference period by hand on the fixture (the sums in % of its normals, the anomalies of Tmean, the SPI's fits from its sums only, the percentiles of its wet days, the regime of its normals) with the analysed years' values unchanged, the 80 % rule of a reference reaching beyond the record, the default reference equal to the analysed period in every catalog example, the errors and the variant options; sums equal in decimal equal as numbers (0.1 + 0.2 and 0.3 mm); the list of spells by `min_duration_days` with the summaries unchanged. The mockup's prototypes (Obserwator, `_meteo_proto.py`) were reproduced on Kraków (250190390) and Praha-Klementinum (0-203-0-11514) to their rounding, with the differences of D1 (the period's days only) and the monthly classes above.

**Formulas by specs** (ADR-0059; `tests/unit/test_formulas_meteo_*.py`, generated from the specs of `docs/FORMULAS.md`): the range, type and property tests of each spec (CMP-6.5) and the reference cases of `tests/fixtures/formulas/meteo-indices-cases.json`; the SPI against Thom's equations in 50-digit decimals and the frozen output of climate_indices 3.2.0 on Warszawa-Okęcie 1991–2020 (`tests/oracles/spi_climate_indices_warszawa.csv`); the degree days against Eurostat's examples; the length of the spell ending on each day (`spell_lengths`) against the spells counted day by day in a loop, the days of each kind held once by the spells, and a negative precipitation refused (`outside_physical_range`); SDII, the type-8 percentile of the wet days, R95p and R95pTOT, PCI and SI against their equations in exact fractions, the percentiles 95.65 and 99.6633 mm and R95p 490 mm of the wet days 1 to 100 mm, PCI 8.3 and 100 (de Luis et al., 2011) and SI 0 and 1.83 (Sumner et al., 2001), and the classes of PCI and SI at and beside each limit; the frost, freeze-thaw, ice, summer and hot days and tropical nights of each day (`threshold_days`) at each threshold of the ETCCDI, of the hot day and of the freeze-thaw day and 0.1 °C beyond it, against the flags compared day by day in a loop; Sielianinov's k against Kulik et al. (2016, Sosnowica 2003: 0.67) and Trawczyński (2021, Jadwisin 2018, six months) and in exact fractions, and its classes at and just above each limit of Skowera and Puła (2004). The calendar rules of `_climate` and `meteo_snow` (WMO-No. 1203, the years, the rounding, the snow season) are their Tier B tables in `docs/FORMULAS.md`, verified by the tests above.

**Reference cases of the audit of 2026-11-18** (research `meteo-indices`; `tests/unit/test_meteo_warszawa.py` on the daily series of IMGW-PIB's Warszawa-Okęcie 1991–2020, `tests/fixtures/warszawa_okecie_1991_2020.csv.gz`, and `tests/unit/test_meteo_reference.py`): IMGW-PIB's normals 1991–2020 of WARSZAWA 12375 to their printed 0.1 (precipitation, months and the year 549.7 mm; Tmean, months and the year 9.0 °C; TMIN_0 97.9 days as FD; PRZYMROZKI 64.0 days as the freeze-thaw days); the dry spell of 1996-12-15 to 1997-02-11 (59 days) in 1997, CDD 25 in 1996, and the mean CDD 25.77 days, as an independent recount by the year of the spell's end; the mean season coefficient 1.154277 of the days above 10 °C in April–September (independent recount; the all-year days gave 1.144); and WMO-No. 1203, 4.3.3 on a seeded series with one missing day in seven years, where the annual normal is the sum of the monthly ones, 767.950 mm, instead of missing.

### 3.14 Station Analyses of a Daily Series (`stats characteristic`, `stats threshold-events`, `stats low-flow-sequences`, `stats duration-curve`, `stats runoff-volume`, `hydrometrics rating-curve`, half-years in `stats flood-frequency`, `stats low-flow`, `stats homogeneity`; plan 2026-11-13, D1, D3 to D9; ADR-0029, ADR-0030, ADR-0033)

These commands reduce a station's daily series (Obserwator's export or inline values with `dates`; a day whose date is absent or whose value is empty has no value) over the reference period of D1: the hydrological years `first_year` to `last_year` (1 November – 31 October, named after the year in which they end; by default the first and the last year with a value), from the days of those years only. A result names the period (`first_year`, `last_year`, `period_years`, its years with a value); a result that characterises the period as a whole (the second degree of `stats characteristic`, a threshold of `stats low-flow-sequences` taken from the series, `stats duration-curve`, the means of `stats runoff-volume`) carries the notice `short_reference_period` under 30 years, the length of a climatological standard normal (WMO-No. 1203, 2017); lists of events and fits of chosen years do not. A period without a value is `calculation_error` `no_values_in_period`.

**Characteristic values of both degrees (`stats characteristic`, `calculate_characteristic_values`, `characteristic_values_from_half_years`).** The first degree of a hydrological year and of its half-years (winter XI–IV, summer V–X) is the minimum, the mean and the maximum of its days with a value (`years`: `winter`, `summer`, `annual`, each with the dates of its extremes, the first day on which each occurs, `days_with_data` and the calendar `days`). The second degree of the year and of each half-year (`winter`, `summer`) is the highest (W), the mean (S), the median (Z) and the lowest (N) of the first-degree maxima, means and minima of the years that have them: WWQ … NNQ for Q, WWW … NNW for the stage, WWT … NNT for T by analogy (`labels`, `first_degree_labels`); SWQ is the mean of the *annual* maxima, never of the pooled half-year maxima (IMGW-PIB's definition; Byczkowski, 1996). A year with missing days stays in the values (its extremes may be milder than the true ones) and is named in `incomplete_years` and the notice `years_with_missing_days`. From a daily series the result is therefore not IMGW-PIB's characteristic values: IMGW-PIB takes the extremes of a month, half-year and year from all observations ("Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji", Rocznik Hydrologiczny 2022, p. 7) and publishes no characteristic of a period with a break in observations, while the daily mode takes the extremes of the daily values (one a day, e.g. the daily mean), so its maxima are as a rule lower and its minima higher (Kłodzko 150160180, hydrological year 2010: WQ 96.0 against IMGW-PIB's 145 m³/s, winter WQ 62.6 against 77.4 m³/s, NQ 4.93 against 4.17 m³/s; the annual mean 19.14 against 19.1 m³/s). IMGW-PIB's characteristic values come from its half-year file. From IMGW-PIB's published half-year characteristics (`half_year_file`, Obserwator's export of `pl.imgw.hydro_semiannual`) the half-years keep their published values and dates, the annual maximum is the larger of the two half-year maxima (the winter one on a tie), the annual minimum the smaller of the minima, both unknown when a half-year is missing, and the annual mean is the published one (`days_with_data` and `days` are `null`).

**Threshold events (`stats threshold-events`, `threshold_events`, `threshold_runs`).** The threshold level method (Tallaksen and van Lanen, 2004, ch. 5) on the calendar of the series: a day is beyond `threshold` when its value is at or above it (`direction` `above`) or below it (`below`), and a day without a value never is; consecutive days beyond form a run, runs parted by fewer than `max_gap_days` days (without a value or not beyond; 0 merges none) merge into one event, and events shorter than `min_duration_days` (gap days inside included) are dropped. Each event has its start, end, duration, the days beyond, the missing days, the peak (the largest value above the threshold, the smallest below it, dated by its first day) and `open_start`, `open_end` when the day before or after it has no value, so that the event may be longer; an event counts in the hydrological year in which it starts, and `years` gives per year the days beyond, the events and the days with data. With the defaults it gives the mockup's days and events beyond SWW, SSW, SNW, SWQ, SSQ and SNQ; the water temperature days of H15 are this command on T. The runs, the events, the low-flow sequences below and their volumes in m³ are Tier B formulas of `docs/FORMULAS.md` (`threshold_runs`, `threshold_events`, `low_flow_sequences`, `low_flow_deficit_volumes`; ADR-0063) with their sources: runs pool when fewer days than `max_gap_days` part them (WMO-No. 1029, sect. 8.2), the duration of a pooled event includes those days (the full duration of Fleig et al., 2006, eq. 1), while `days_beyond` counts the days of its runs (the pooled duration of WMO-No. 1029, eq. 8.1(a)), and the deficit of a pooled low-flow sequence is the sum of the deficits of its runs, the excess of the days between them not subtracted (eq. 8.1(b)). The dates of the library's `threshold_events`, `runoff_volumes` and `duration_curve` must increase strictly, as the commands require: before 0.9.0 a repeated date let the later value overwrite the earlier one, or counted a day twice in the duration curve.

**Low-flow sequences across gaps (`stats low-flow-sequences`, `LowFlowAnalysis.detect_sequences`).** The same runs below a threshold, with `min_duration_days` 5 and `max_gap_days` 4 by default (the author's 5 days and gaps under 4 days, the mockup's `merge_low_flow_events`), on the calendar of the series, so that missing values and absent dates are gap days (before ADR-0029 they were refused, `missing_values`, `date_gap`). The threshold is given (`threshold_method` `value`), SNQ or SNW of the period (`mean_annual_minimum`, the `snx` of `stats characteristic`) or the value of the duration curve below exceeded on `exceedance_percent` % of the days (`exceedance`, 70 by default: Q70, Q90); `threshold` or `exceedance_percent` given with another method is `not_applicable` (ADR-0033). The deficit of a sequence is Σ (threshold − Q) over its days with a value below the threshold, in the unit of the series times days, and with `parameter` Q also a volume, times 86,400 s (`deficit_volume_m3`, m³); `mean_flow` is the mean of its days with a value. `years` counts a sequence in the hydrological year in which it starts (the mockup's summary).

**Duration curve (`stats duration-curve`, `duration_curve`, `exceedance_values`).** The value equalled or exceeded on p % of the days: the n values of the period (of one calendar month with `month`) ranked from the highest have the Weibull plotting positions p = m / (n + 1), and a percentage between two positions is interpolated linearly between their values, held at the end values beyond them (Vogel and Fennessey, 1994, eq. 3; method R6 of Hyndman and Fan, NIST/SEMATECH e-Handbook, 7.2.6.2; the spec `exceedance_values`, `formula_version` 1, in `docs/FORMULAS.md`, which refuses a percentage outside (0, 100), an infinite value and a series without a value; Searcy, 1959, and WMO-No. 1029, sect. 6.1, give a class the share i/N of the days instead); `values` are read at `exceedance_percents` (1, 5, 10, 30, 50, 70, 90, 95, 99 by default), `curve_values` at the 105 percentages 0.1 … 99.9 of `curve_exceedance_percents`. The classes (`bin_method`) are of equal `bin_width` (10 by default; 10 cm for H), [k·w, (k + 1)·w) from the multiple of the width at or below the smallest value (the author's 10 cm table), counted in decimal arithmetic on the shortest decimal form of the values and the width, so a value on a bound is in the class it starts (until 0.9.0 the edges were k·w in binary floating point and 0.3 with the width 0.1 fell into [0.2, 0.3), since 0.3 / 0.1 = 2.9999999999999996), or `bin_count` (40 by default) logarithmic classes between the smallest positive and the largest value, which are their end edges (the mockup's `log_classes`: equal classes would put the mode of a skewed flow series in its lowest class); `bin_width` with `log` and `bin_count` with `width` are `not_applicable` (ADR-0033). Each class, from the highest down, has its `days`, `share_percent`, the cumulative `days_with_higher` and `days_with_lower` („including higher”, „including lower”; Searcy, 1959, the total-period method; Byczkowski, 1996) and its days in each hydrological month XI–X; the modal class is the most frequent, the lowest one on a tie. The classes and the days the curve takes are Tier B (`duration_classes`, `duration_curve_days`).

**Monthly statistics (`stats monthly`, `calculate_monthly_statistics`).** For each calendar month the maximum, mean, median and minimum of all its daily values and their standard deviation (spec `sample_standard_deviation`, the divisor n − 1), coefficient of variation (spec `coefficient_of_variation`) and skewness (spec `fisher_pearson_skewness`, the Fisher-Pearson g₁ of NIST's e-Handbook, sect. 1.3.5.11, scipy's `skew` with `bias=True`); `docs/FORMULAS.md` gives their equations and sources. The confidence interval of the long-term mean of the month is the mean of all its values ± the half-width of spec `mean_interval_half_width`, Student's interval on the k means of the month in the separate calendar years with k − 1 degrees of freedom: the daily values of a month are not independent (lag-1 correlation of daily flows 0.71–0.89 at Kłodzko in 2010, the audit of 2026-11-18), one value a year is. The interval is not clipped: a month of stages below the gauge's zero, or a mean poorly known, has a lower limit below 0. Until 0.9.0 the interval was mean ± t·s/√n over the n daily values, 3 to 25 times too narrow, and its lower limit was raised to 0, above the mean of a month of stages below the gauge's zero. A month with values of one year has no interval (`null`, notice `single_year_month`); a month with one value has no spread either (`single_value_month`). The coefficient of variation is defined for a quantity with a true zero, such as discharge (NIST, Dataplot): a month with a value below 0 or with values all 0 has none (`null`; until 0.9.0 the 0/0 of a dry month was 0 and a month below 0 had a number that depends on the gauge's zero), and a month of equal values has no skewness.

**Daily statistics (`stats daily`, `calculate_daily_statistics`).** The maximum, mean, median, minimum and number of the values of each day of the hydrological year over the years, the days counted from 1 November (day 1). The days are counted, not dated: from 1 March a leap year's days are one higher than a common year's, so a day after 28 February pools two adjacent calendar dates (day 121 is 29 February of the leap years and 1 March of the common ones) and day 366 holds the 31 October of the leap years only, as its `count` shows (the audit of 2026-11-18, finding 9).

**Runoff volumes (`stats runoff-volume`, `runoff_volumes`).** V = Σ Q · 86,400 s over the days with a value of a month or a hydrological year [m³] (the author's daily volumes, the mockup's `runoff`). A month or a year is complete when each of its days has a value, and the means (`mean_annual_volume_m3`, `monthly_mean_volume_m3` XI–X) take the complete ones only. The cumulative volume of `cumulative_year` (by default the last complete year of the period) adds the days in order, a missing day adding nothing; `mean_cumulative_volume_m3` is the mean of the complete years' curves over their first 365 days.

**Rating curves by period (`hydrometrics rating-curve`).** With the dates of the pairs (`dates`, `date_column`) the pairs are the days with both values; `first_year`, `last_year` limit them to those hydrological years, and the curve of the range is the fit of section 3.8. With `years_per_period` n the curve of each block of n years is fitted too, with the same `h0_initial`, `remove_outliers` and `outlier_std`: the blocks start at the years y with (y − 1) mod n = 0 (1951–1960, 1961–1970 for 10), the first and the last cut to the years of the pairs; a block with fewer than 30 pairs has no curve (`reason` `too_few_pairs`), one whose fit fails `fit_failed`. Each period's curve is read at the medians of the level and of the discharge of all the pairs (`reference_level`, `reference_discharge_m3s`), so that the shift of the curve between periods is a number (`discharge_at_reference_m3s`, `level_at_reference_discharge`). A value the curve does not give is null: the discharge at a reference level at or below the period's H₀, and the level at the reference discharge when it is not a finite number, as for a flat curve (b near 0, the fit of a period whose discharge does not rise with the stage) whose plateau a lies below that discharge, where H₀ + (Q / a)^(1/b) is beyond any number. The periods without that level are named in the notice `reference_level_not_computed` (before 0.8.1 the overflow of the power ended the command with `internal_error`). Each period's curve is checked for plausibility against the stages of its own pairs (section 3.8: its `plausible` and `implausibility_reasons`, null for a period without a curve, and the notice `implausible_rating_curve`). Without dates nothing changes; `first_year`, `last_year` and `years_per_period` need dates.

**IMGW-PIB's half-years in the frequency commands (`stats flood-frequency`, `stats low-flow`, `stats homogeneity`; `annual_extremes_from_half_years`).** With `half_year_file` and `parameter` Q or H (the columns of the file) the annual maximum is the larger of the winter and the summer maximum of a year that has both (the winter one on a tie), the annual minimum the smaller of the minima: the annual values of the first degree of `stats characteristic`. A year with one half-year only is left out and named in `incomplete_years`, because its other half-year may hold the extreme; `first_year`, `last_year` choose the years of the file, and `source` says where the values come from (`daily`, `values`, `half_years`). `stats low-flow` fits the minima directly (`fit_fisher_tippett_minima`), as it fits the annual minima of a daily series.

**Verification** (`tests/unit/test_station_analyses.py`, `tests/unit/test_station_batch.py`, `tests/unit/test_formulas_daily.py`; the mockup's numbers by a check outside the repository, plan 2026-11-13, Results). Hand-computed series: runs merged across gaps shorter than the limit and none with 0, a missing day that ends an event, dated peaks, days below a threshold across gaps; the first and second degree of years and half-years and the larger half-year maximum of a file; Weibull positions interpolated between ranks and classes from a multiple of the width with their cumulative days; the volumes of complete and incomplete years; low-flow sequences across missing days with their yearly summary; the periods of a rating curve without enough pairs. The formula tests check the values of the duration curve against their spec (generated ranges, types and properties; NIST's example of the 90th percentile and Vogel and Fennessey's positions; eq. 3 in exact rational arithmetic and NumPy's `weibull` quantile), the runs, events, low-flow sequences and deficit volumes in m³ against runs found day by day and sums in exact rational arithmetic on seeded series with gaps, small samples, ties at the threshold, zeros and constant series, lfstat's pooling tests and NIŻÓWKA's pooling across 3 days (Tokarczyk, 2010), and the runoff volumes against exact sums. On Kłodzko's exports (150160180, 1951–2025 without hydrological year 1997) the commands give the mockup's numbers to the last digit (largest relative difference 1.2e-16): the characteristic values of both degrees from the daily series and from IMGW-PIB's half-years, the days and events beyond SWW … SNQ, the low-flow periods with SNQ, Q90, H70 and 4 m³/s in 1991–2020, the duration curves of H and Q with their classes by month, the runoff volumes and the rating curves of 2016–2025, of 2000–2020 without outliers and of the decades; the annual maxima of the half-years in `stats flood-frequency` equal the mockup's (74 years of 1951–2025, 29 of 1991–2020) with the same best distribution and quantiles. One difference, by D7: the January curve of H in 1991–2020 has its classes from 80 cm (a multiple of 10), the mockup's from its lowest value, so the modal class differs.

### 3.15 Design Hyetographs: the Euler Type II Storm (`EulerIIHietogram`, `euler_ii` of `precip hietogram`, `hydrograph generate`, `report generate` and `route network`; hotfix of 2026-11-18, ADR-0042)

The Euler type II storm is the model rain of ATV-DVWK-A 118 for the design of urban drainage, used in Germany with KOSTRA-DWD and in Poland with the PMAXTP atlas of IMGW-PIB or a local formula. It is made from the depth-duration curve h(D) of **one** probability (one return period), so that the blocks around its peak hold, for every duration, the depth that the curve gives for that duration: the storm is critical for any catchment whose response time it contains.

**Inputs.** `depth_duration_mm`, the depths h [mm] of one probability by duration D [min] (a mapping; in JSON an object whose keys are the durations, `"5"`), not decreasing (`decreasing`, naming the two durations), finite and not negative, each duration once; the duration D (`duration_min`), a whole number of time steps (`not_multiple`); the step Δt (`timestep_min`), at most D. The curve must reach from Δt to D (`not_covered`): nothing is extrapolated, so with PMAXTP (5 min to 72 h) Δt ≥ 5 min. `precip pmaxtp` gives the PMAXTP curve of a point (`result.depth_duration_mm`: the 16 durations at the asked probability and method). `precip hietogram`, `hydrograph generate` and `report generate` take the curve as `depth_duration_mm` or read it from `depth_duration_file`: a CSV `duration_min,depth_mm` (`,` or `;`, a decimal comma allowed) or JSON (such an object, a table of records or of columns, or the envelope or the result of `precip pmaxtp --json`, whose `attribution` and `terms_notice` the result then carries). A design rainfall of `hydrolog-network/1` holds the curve as `depth_duration_mm` (the schema keeps its version `/1`: the field is added, and a curve-less `euler_ii` is refused, `missing_field` `rainfall.depth_duration_mm`).

**The blocks.** With `n = D / Δt`, the depths of the curve at the ends of the steps and their increments

```
h_j = h(j Δt), j = 1..n (h_0 = 0)        Δh_j = h_j - h_(j-1)
k = floor(0.3 n)                          the peak block, counted from 0
P_k = Δh_1        P_(k-i) = Δh_(i+1), i = 1..k        P_(k+i) = Δh_(k+i+1), i = 1..n-k-1
```

The peak interval starts at 0.3·D rounded down to a multiple of Δt (the result's `parameters.peak_start_min` = k·Δt), the increments of the next durations fill the time before it back to t = 0 and the rest follow it. The m blocks that end with the peak (k−m+1..k while m ≤ k+1, else the first m blocks) therefore hold `h(m Δt)` whatever the curve, and the whole storm holds h(D). For a curve whose increments decrease (intensities that fall with the duration, an IDF curve) this is the arrangement that A 118 and DWD describe: the largest increment at the peak, the next k larger ones before it in ascending order, the rest after it in descending order ("Der höchste 5-min-Wert steht an Position 4. Die drei nächsthöheren Werte sind links vom Spitzenwert angeordnet. Die restlichen Werte folgen (mit abnehmender Größe) rechts vom Spitzenwert", Malitz 2009, slide 17). Where the interpolation between the coarse points of a table makes an increment grow (the PMAXTP depths of Kamiennik at p = 50 % between 30 and 45 min), the increments keep their order by duration and are not sorted: sorted, the 30 min that end with the peak would hold 15.14 mm instead of h(30) = 15.01 mm, and the itwh software also leaves each increment at the block of its duration (its KOSTRA-DWD 2020 printout of Aurich keeps the negative increments of its surcharge at the blocks of the KOSTRA steps 90, 180, 240 and 360 min).

**The total.** The depth of the storm is h(D). The commands take `total_mm` as optional for `euler_ii` (it is h(D)) and refuse a total that differs from h(D) by more than 0.005 mm, half of the 0.01 mm that the PMAXTP tables print (`total_mismatch`, `details.depth_mm` h(D)); `EulerIIHietogram.generate(total_mm, duration_min, timestep_min)` keeps the signature of every hyetograph and refuses another total in the same way, and `depth_mm(D)` gives h(D). In a network document `total_mm` stays required and must be h(D): another total is refused when the network is routed, with the id of the node.

**Between the points of the curve.** Depths are interpolated linearly in ln D. That reproduces the itwh KOSTRA-DWD 2010R printouts of Göllheim from their 0.1-mm depths to 0.07 mm, where linear interpolation in D misses by 0.16 mm; the DWA's KOSTRA tool interpolates linearly in D, HEC-HMS's frequency storm in log–log, and PMAXTP smooths each station with a power law (Ozga-Zieliński 2022, pp. 32–35); no Polish rule for the gaps of PMAXTP was found. The peak block and every window whose duration is a point of the curve do not depend on the choice.

**The peak rule.** ATV-DVWK-A 118, Kap. 5.2.2.1, as quoted by Thewes (2005, p. 10): "Beginn des Regenintervalls mit der höchsten Niederschlagsintensität beim 0,3-fachen der Modellregendauer … auf ein Vielfaches von 5 Minuten abgerundet. Daran schließen sich auf der Zeitachse nach links die nächst niedrigeren Intervalle an, bis der Zeitpunkt t = 0 erreicht ist"; Kaźmierczak and Kotowski (2012, pp. 31–32) give the same rule. Hydrolog rounds down to a multiple of the step, the same for Δt = 5 min (Δt = 10 min and D = 60 min: 18 min becomes 10 min, the second block). The position is not a parameter: `peak_position` is refused for `euler_ii`. Two published storms place the peak one block elsewhere: the itwh software puts the peak of a 15-min storm in the second block (the rule: 0.3·15 = 4.5 min, the first), and the Wrocław monograph's Tab. 4.6 ends the peak at D/3 for 165 and 180 min (55–60 min for 180 min, where the rule that its p. 31 states gives 50–55 min).

**Applicability.** The storm is a design rain of urban drainage; A 118 asks for D of at least twice the longest flow time (Thewes 2005, p. 11; Kaźmierczak and Kotowski 2012, p. 31). Every depth of the curve must be of the same probability, as for HEC-HMS's frequency storm ("All depth-duration precipitation values must be for the same annual exceedance probability"). PMAXTP's short durations make a peaked storm (h(5)/h(60) = 0.557 at Warsaw, POT, p = 1 %, against 0.26–0.39 in the KOSTRA examples); whether IMGW-PIB's 5- and 10-min depths suit model rains is an open question (Open questions of `docs/PROGRESS.md`). In the GUI, Hydrogram zlewni and Sieć offer Euler II with PMAXTP: the curve is the table of the chosen probability and method, sent with the depth.

```python
from hydrolog.precipitation import EulerIIHietogram

kostra = {5: 9.5, 10: 13.9, 15: 16.9, 20: 19.2, 30: 22.4, 45: 25.6, 60: 27.9}   # Göllheim, T = 5 a [min: mm]
euler = EulerIIHietogram(kostra)
storm = euler.generate(total_mm=euler.depth_mm(60.0), duration_min=60.0, timestep_min=5.0)
print(storm.intensities_mm.round(2).tolist())
# [2.3, 3.0, 4.4, 9.5, 1.76, 1.44, 1.22, 1.05, 0.93, 0.84, 0.76, 0.7]: itwh prints 2.23, 3.00, 4.44, 9.51 ...
print(round(float(storm.intensities_mm[1:4].sum()), 2))   # 16.9: the 15 min that end with the peak hold h(15)
```

**Up to 0.8.1** the class took the total only. It weighted the blocks by rank, `w_r = r^-0.7 / Σ k^-0.7`, and placed them alternately left and right of the block `max(2, floor(n p) + 1)` with p = 0.33 (`peak_position`): the same shares for every place, probability and duration (for n = 12 the peak was 23.08 % of the total and h(60)/h(5) = 4.33 always), neither the local curve nor the Euler arrangement. Its peak block was 23 to 66 % below every published Euler type II storm and an Euler type II of PMAXTP (the cases below: DWD 10.4 mm → 6.138 mm; Göllheim 9.51 mm → 7.303, 6.438 and 5.746 mm at 30, 60 and 90 min; Aurich 11.00 mm → 3.771 mm in block 36; Wrocław 101.71 mm/h → 65.51 mm/h; PMAXTP at Warsaw and Kamiennik, 60 min, 49 to 59 % below h(5)), and its 15 min around the peak short of h(15) (Warsaw, p = 1 %: 18.79 mm against 28.22 mm). It even missed its own premise: an IDF curve `i ~ D^-0.7` gives `h ~ D^0.3` and a peak share of 0.4745 for n = 12, not 0.2308. The peak of a hydrograph moves less than the peak block, and only where the catchment answers within the storm: for the PMAXTP storm of Warsaw (p = 1 %, 60 min, 39.16 mm) on 5 km² of CN 80 with the SCS unit hydrograph the new peak is 120, 47 and 15 % above the old for tc 10, 20 and 30 min and within 3 % of it for tc 60 to 180 min (the volume of one total is the same). Every result made with `euler_ii` up to 0.8.1 (`precip hietogram`, `hydrograph generate`, `report generate`, `route network`, `RoutingNetwork`, the GUI) is to be computed again with the curve of its probability.

**Verification** (`tests/unit/test_euler_ii.py`; the tolerance of each case is half a unit of its last printed digit plus the rounding of the printed inputs it is built from). DWD (Malitz 2009, slides 18 and 19, 60 min, the curve from the sums of the largest printed values): every block to 0.05 mm, the peak at position 4. itwh KOSTRA-DWD 2010R, Göllheim, T = 5 a (the printed 0.1-mm KOSTRA depths, storms of 30, 60 and 90 min to 0.01 mm): every block to 0.105 mm (the largest difference is 0.07 mm), the peaks in blocks 2, 4 and 6. itwh KOSTRA-DWD 2020, Aurich, 9 h: the peak interval 160–165 min (block 33) with 11.00 and 14.99 mm (T = 3 and 10 a) to 0.005 mm. Kaźmierczak and Kotowski (2012), Wrocław, formula (2.6), C = 3 years: the peak 101.71 mm/h to 0.005 mm/h at 60 min (15–20 min) and at 180 min (50–55 min by the rule). Wdowikowski et al. (2025), PMAXTP at Wrocław, C = 5 years, 60 min: the peak 146.18 mm/h (12.18 mm) to 0.2 mm, the paper's own 5-min depth coming from a fitted curve, at 15–20 min. The recorded PMAXTP tables of Warsaw and Kamiennik (POT, p = 1, 10 and 50 %, 60 min): the peak in block 4 holds h(5), and the largest 15 and 30 min hold h(15) and h(30), to 0.005 mm. The power law h = D^0.3: peak shares 0.5842, 0.4745 and 0.3854 for n = 6, 12 and 24. Properties: every window around the peak holds h(m Δt) to 1e-12 for every m (Kamiennik p = 50 % and 2 %, Warsaw p = 1 %; D from 15 to 720 min, Δt 5 and 15 min); the total is h(D); the peak interval starts at floor(0.3 n) Δt for n = 1 to 120, and at 10 min for Δt = 10 min and D = 60 min; growing increments keep their order; keys given as text; three blocks for 0.3 min in steps of 0.1 min. The refusals: a decreasing curve, a curve that does not cover the step or the duration, a duration that is not a whole number of steps, a step over the duration, a depth that is not finite or negative, a duration that is not a number above 0 or is given twice, an empty curve or one that is not a mapping, a total 0.006 mm off h(D) (and one within the rounding taken as h(D)), a total that is not finite or not above 0. The commands, the network document and the GUI are tested in `tests/unit/test_operations_runoff.py`, `tests/unit/test_routing_rainfall.py`, `tests/unit/test_route_network_made.py` and `tests/e2e/test_hydrogram.py`.

### 3.16 Design Hyetographs: Whole Steps, the Triangle and the Beta Storm (`BlockHietogram`, `TriangularHietogram`, `BetaHietogram`, `DesignStorm`; ADR-0046)

**Whole steps.** Every generator cuts the storm into `n = D / Δt` steps of the time step Δt (`times_min` = the ends of the steps, Δt..nΔt) and puts the whole total into them. The duration D must be a whole number of steps, to 1e-9 of D (`0.3 / 0.1` is 3 steps): another duration is refused (`validation_error`, `details.option` `duration_min`, `details.reason` `not_multiple`, `details.timestep_min`). The storm then lasts D and its mean intensity is the total over D. **Up to 0.8.1** the generators took `int(D / Δt)` steps and put the whole total into them, so a duration that was not a whole number of steps gave a shorter storm of a higher intensity (the PMAXTP depth of Warsaw for 45 min, 36.58 mm, in 40 min with steps of 10 min: +12.5 %; a network's `DesignStorm` of 50 min with steps of 20 min: +25 %) and the notice `duration_not_covered`, now removed. A design storm of a network follows the rule at the network's step and its refusal names the node.

**Inputs.** The total, the duration, the step and the shape parameters must be finite numbers above zero (`not_finite`, `exclusive_minimum`, `type` for a bool), `peak_position` a finite number in (0, 1) (`exclusive_minimum`, `exclusive_maximum`); the library refuses them, as the CLI does, with `details.option` naming the value.

**Block.** `P_i = P / n`.

**Triangle** (Yen and Chow 1980, as given by Chow, Maidment and Mays 1988, sec. 14.3, eqs. 14.3.1–14.3.3). The intensity rises linearly from 0 at t = 0 to `h = 2P/D` at `t_a = r D` and falls linearly to 0 at t = D (r = `peak_position`, the storm advancement coefficient; Chow et al. 1988, Table 14.3.2: 0.294 to 0.480). Each step holds the depth that falls in it:

```
F(u) = u² / r                      for u <= r        (u = t / D)
F(u) = 1 - (1 - u)² / (1 - r)      for u > r
P_j  = P [F(j/n) - F((j-1)/n)],    j = 1..n
```

With r = 0.5 and an even n the two middle steps are equal. **Up to 0.8.1** the steps had the triangle sampled at their ends (`w_j = j/j_p` up to the step `j_p = max(2, floor(n r) + 1)`, then `(n-j+1)/(n-j_p+1)`, normalised): for 3 steps 1/2, 1, 1/2 of the peak whatever r; for 12 steps and r = 0.5 the steps differed from the integrals by up to 14 % of the peak.

**Beta** (KZGW 2017, ch. II.3, eqs. 2.20–2.22, after Węglarczyk 1993). The intensity over u = t/D has the shape of the Beta density with α and β; each step holds the difference of the Beta distribution function, the regularised incomplete Beta function `I_u(α, β)` (`scipy.special.betainc`):

```
P_i = P [I_(i/n)(α, β) - I_((i-1)/n)(α, β)],    i = 1..n
```

The steps hold P for every α, β > 0, also where the density is infinite (α < 1 or β < 1). KZGW reads the density at the ends of the intervals, which shifts the storm by half a step (33 % of the peak for (2, 5) and 12 steps). **Up to 0.8.1** the steps had the density at their midpoints, normalised, and a uniform storm when every weight was 0 or not finite (NaN or infinite α, β; α = β ≥ ~535): for (2, 5) and 12 steps within 2.0 % of the peak, but for α = 0.5, β = 5 the first step held 0.5445 of the total instead of 0.6372.

```python
from hydrolog.precipitation import BetaHietogram, TriangularHietogram

urbana = TriangularHietogram(peak_position=0.38).generate(27.178, duration_min=15.0, timestep_min=5.0)
print(urbana.intensities_mm.round(3).tolist())   # [7.947, 14.361, 4.871]: Chow et al. 1988, Ex. 14.3.1
beta = BetaHietogram(alpha=0.5, beta=5.0).generate(1.0, duration_min=12.0, timestep_min=1.0)
print(round(float(beta.intensities_mm[0]), 4))   # 0.6372 = I_(1/12)(0.5, 5)
```

**Verification** (`tests/unit/test_hietogram.py`). Chow et al. (1988), Example 14.3.1 (Urbana, 15 min, 1.07 in, r = 0.38): the block integrals of the published triangle in steps of 1 and 5 min to 0.0005 mm. Beta (2, 5) with 6 and 12 steps and (0.5, 5) with 12 steps: every step equals the difference of `scipy.stats.beta.cdf` to 1e-12. Every type: the steps hold the total and the last ends at D; a duration that is not a whole number of steps and a value that is not finite are refused.

**Areal precipitation by isohyets** (`isohyet_method`, `precip areal` `isohyet`; KZGW 2017, eq. 2.2; Chow et al. 1988, Fig. 3.4.3c). A zone's precipitation is the mean of its two bounding isohyets, so a zone at the edge of the watershed (beyond its highest or below its lowest isohyet) takes a notional bound that makes that mean the precipitation estimated for it: Chow's edge zones of 5 and 53 mm are the bounds 0 and 56 mm, and the example gives 27.9 mm.

---

## 4. Literature Verification

### 4.1 Table of Sources for Each Computation Path

| Computation path | Source | Status |
|------------------|--------|:------:|
| SCS UH + Kirpich → Tc | Kirpich (1940), NEH Part 630 ch. 15 eq. 15-3 (tlag = 0.6 × Tc) | ✅ |
| SCS UH + NRCS → Tc | USDA-NRCS (2010), NEH Part 630 ch. 15 | ✅ |
| SCS UH + Giandotti → Tc | Giandotti (1934), NEH Part 630 ch. 15 eq. 15-3 | ✅ |
| SCS UH + FAA → Tc | FAA AC 150/5320-5B (1970), NEH Part 630 ch. 15 eq. 15-3 | ✅ (small catchments without a channel) |
| SCS UH + Kerby → Tc | Kerby (1959), NEH Part 630 ch. 15 eq. 15-3 | ✅ (small catchments without a channel) |
| Clark IUH + FAA → Tc | FAA AC 150/5320-5B (1970), Clark (1945) | ✅ (small catchments without a channel) |
| Clark IUH + Kerby → Tc | Kerby (1959), Clark (1945) | ✅ (small catchments without a channel) |
| SCS UH + Kerby-Kirpich → Tc | Roussel et al. (2005), NEH Part 630 ch. 15 eq. 15-3 | ✅ |
| Clark IUH + Kerby-Kirpich → Tc | Roussel et al. (2005), Clark (1945) | ✅ |
| Nash IUH + from_lutz() | Lutz (1984), KZGW (2017) | ✅ |
| Nash IUH + from_urban_regression() | Rao, Delleur, Sarma (1972), Banasik (2009) | ✅ |
| Nash IUH + directly n, K | Nash (1957) | ✅ |
| Clark IUH + Tc (any method) | Clark (1945), HEC-HMS | ✅ |
| Clark IUH + R/Tc ratio | Clark (1945), HEC-HMS; the range of R/Tc has no published source (to be verified) | ✅ |
| Snyder UH + L, Lc, Ct, Cp | Snyder (1938) | ✅ |
| Snyder UH in `HydrographGenerator` (D = time step: tLR, tpR, qpR) | Snyder (1938), HEC-HMS Technical Reference Manual, Chow, Maidment, Mays (1988) | ✅ |
| Kirpich from a catchment (the longest flow path, `flow_path_length_km`, `flow_path_slope_m_per_m`) | Fang et al. (2005) eq. 3.14, Mota and Kobiyama (2015) | ✅ |
| NRCS from a catchment (the longest flow path; Y = mean terrain slope of the catchment) | NEH Part 630 ch. 15 (2010), eq. 15-4 | ✅ |
| Giandotti from a catchment (main channel; mean elevation − outlet) | Grimaldi et al. (2012) | ✅ |
| Kerby-Kirpich from a catchment (channel = flow path − overland, at the slope of the flow path) | Roussel et al. (2005) supplement, TxDOT Hydraulic Design Manual ch. 4 section 11, Cleveland et al. (2012); both published examples reproduced | ✅ |
| FAA, Kerby from a catchment (overland flow time from `overland_*`) | FAA AC 150/5320-5B (1970), Kerby (1959), Roussel et al. (2005), TxDOT Hydraulic Design Manual ch. 4 section 11 | ✅ |
| D-minute Clark UH (S-curve, any D > 0) | Clark (1945), S-curve method (e.g. Chow, Maidment, Mays 1988) | ✅ |
| HSG from USDA texture (class mapping) | USDA Soil Survey Manual (Handbook 18, 2017, ch. 3), NEH Part 630 ch. 7 (TR-55), Kartograf ADR-025 | ✅ (with a deviation for 3 classes) |
| Distribution of annual minima (GEV for minima) | Fisher and Tippett (1928), Gumbel (1958), Coles (2001); maximum likelihood as `evd` and `extRemes` (a small stream's minima), the limit c < 1 of Smith (1985); no negative discharge: WMO No. 1029 (2009), sec. 7.5 | ✅ |
| Annual extremes from a daily series: complete hydrological years only | KZGW (2017), WMO No. 1029 (2009) | ✅ |
| Empirical frequency of minima (non-exceedance positions) | Weibull (1939), Hazen (1930), Cunnane (1978); WMO No. 1029 (2009), Tallaksen and van Lanen (2004) | ✅ |
| Lag routing (`route lag`, `LagReach`) | HEC-HMS Technical Reference Manual (Lag routing model) | ✅ |
| Muskingum routing with sub-reaches (`route muskingum`, `MuskingumReach`) | McCarthy (1938), Chow, Maidment, Mays (1988), HEC-HMS Technical Reference Manual (Muskingum model), University of Iowa Lesson 27 (worked example) | ✅ |
| Muskingum-Cunge, constant coefficients (`route muskingum-cunge`, `MuskingumCungeReach`) | Cunge (1969), NRCS NEH Part 630 ch. 17 (2014) eq. 17-20 to 17-22, example 17-4 and appendix B, HEC-HMS Technical Reference Manual (Muskingum-Cunge model) | ✅ |
| Cascade of linear reservoirs, exact kernel (`route cascade`, `CascadeReach`) | Nash (1957) (the IUH of `NashIUH`), Kalinin and Milyukov (1957) as presented by Ponce (linear reservoirs and numerical diffusion), Chow, Maidment, Mays (1988); weights checked against the numerical integral of the gamma density and the exact solution of the chain | ✅ |
| Level-pool routing, storage indication (`route level-pool`, `LevelPoolReach`) | NRCS NEH Part 630 ch. 17 (2014) eq. 17-3 and example 17-1, HEC-HMS Technical Reference Manual (Modified Puls model); the step rule per segment checked on random tables and against the exact solution of a tank with a weir | ✅ |
| River network of reaches, reservoirs and junctions (`route network`, `RoutingNetwork`) | Composition of the elements above in the order of the stream (the convention of `StreamSegment.upstream_ids`); no published table, the identities of the plan instead: a one-reach network equals the command, series equivalence with the sub-reaches of `MuskingumReach`, junction sums, order independence | ✅ |
| Subcatchment that makes its hydrograph from its rain (`Subcatchment(watershed=, runoff=, rainfall=)`, `CurveNumberRunoff`, `DesignStorm`, `RainfallSeries`) | The SCS-CN and unit hydrograph paths above (`HydrographGenerator`): the hydrograph of the node equals the generator's to the last ordinate for the four unit hydrograph models, and a network of such nodes routes as the network of their hydrographs | ✅ |
| Control points (`ControlPointNetwork`) | Expansion into the nodes above, no formula of its own: the network of points equals the same nodes built by hand (document and hydrographs); a linear reach routes the same with and without a confluence, a nonlinear one (Muskingum-Cunge with the inflow peak, a pond) does not | ✅ |
| Flood frequency fit methods (`fit_method`) | Hosking and Wallis (1997): sample L-moments, GEV and Pearson III from L-moments; moments and least squares on the same scipy distributions (ADR-0021); maximum likelihood: R's `evd`, `extRemes`, `ismev` and `lmomco` (a frozen oracle), Coles' (2001) Port Pirie fit, the limits of Smith (1985) | ✅ |
| Homogeneity of annual maxima (`stats homogeneity`, `homogeneity_tests`): Mann-Whitney U, two-sample Kolmogorov-Smirnov, Pettitt | Mann and Whitney (1947), Smirnov (1939), Pettitt (1979); `scipy.stats.mannwhitneyu` and `ks_2samp`, the K-S p of tied values exact (Schröer and Trenkler, 1995; Helsel et al., 2020, Example 5.1 against R's `ks.test`, 0.0478036); Pettitt's K checked by hand on small series (ADR-0022) | ✅ |
| Flow regime (`stats regime`): Pardé's coefficients, Dynowska's types, the seasonality index | Pardé (1933); Dynowska (1997) with the criteria of Wrzesiński (2017, 2018) and the spring months of Perz (2019); Walsh and Lawler (1981); IMGW-PIB's means of Kłodzko 2010, the types of Wrzesiński's 2017 and 2018 Tables 1 and Perz's Kłodzko reproduced (specs `parde_coefficients`, `spring_share`, `dynowska_regime_type`) | ✅ (the summer months and "nearly equal" = 0.95 are Hydrolog's reading) |
| Seasonality of annual extremes (`stats seasonality`): circular mean date and concentration | Bayliss and Jones (1992), FEH vol. 3 (1999), Hall and Blöschl (2018), Burn (1997); `scipy.stats.circmean` and Bayliss and Jones's quadrant rules (spec `circular_mean`) | ✅ |
| Harmonics of the annual cycle (`stats harmonics`) | Wilks (2011), section 9.4; Feichtinger, Gröchenig and Strohmer (1995) for the gaps; exact signals and the normal equations in fractions (spec `harmonic_fit`) | ✅ |
| Mann-Kendall test with the variance corrected for ties, Sen's slope, Conover's intercept, Gilbert's interval (`stats mann-kendall`) | Mann (1945), Kendall (1975), Hirsch, Slack and Smith (1982), Sen (1968), Conover (1980), Gilbert (1987) Eq. 16.3, sections 16.4–16.5 and Table A18 (the exact p below 10 values); Examples 16.2, 16.5, Exercises 16.1–16.3 and Helsel et al. (2020) Example 10.3 reproduced | ✅ |
| Baseflow by the Lyne and Hollick filter, recession constant (`stats baseflow`) | Lyne and Hollick (1979), Nathan and McMahon (1990), Ladson et al. (2013) (their published BFIs reproduced); the recession constant of the total flow, Hydrolog's own segments (WMO No. 1029, 2009, sec. 5.3, for k) | ✅ |
| Meteorological statistics (`meteo` group) | WMO-No. 1203 (2017) 4.3–4.4; Zhang et al. (2011, ETCCDI), climdex.pcic and ECA&D ATBD v11 (spells over the year's start); Hyndman and Fan (1996); Oliver (1980); Walsh and Lawler (1981); McKee et al. (1993), Thom (1958), WMO-No. 1090 (2012); Kaczorowska (1962), Gąsiorek and Musiał (2011); Słownik meteorologiczny (2003, via Kossowska-Cezak 2014) and IMGW-PIB's normals 1991–2020 (freeze-thaw days); Wypych et al. (2017); Eurostat nrg_chdd, Directive (EU) 2015/1127; Selyaninov (1928), Skowera and Puła (2004), Radzka (2014), Miś (2026); IMGW-PIB's normals 1991–2020 of Warszawa reproduced; the prototypes of Obserwator's mockup reproduced on two stations | ✅ |
| The reference period of normals, percentiles and the SPI's fits (`reference_first_year`, `reference_last_year` of `meteo precipitation`, `meteo spi`, `meteo temperature`) | WMO-No. 1203 (2017) chapters 2, 3, sections 4.4.2, 5.1, 5.2.2; WMO-No. 1090 (2012); McKee et al. (1993); Zhang et al. (2011), Klein Tank, Zwiers and Zhang (2009); the Copernicus EDO's SPI factsheet (2025) | ✅ |
| Characteristic values of the first and second degree from a daily series or IMGW-PIB's half-years (`stats characteristic`; the half-years in the frequency commands) | IMGW-PIB's definitions (Byczkowski, 1996; Rocznik Hydrologiczny 2022, pp. 5–8); the mockup's Kłodzko numbers reproduced; from a daily series the extremes are those of the daily values, milder than IMGW-PIB's published ones (section 3.14) | ✅ |
| Threshold events and low-flow sequences across gaps (`stats threshold-events`, `stats low-flow-sequences`) | Tallaksen and van Lanen (2004), chapter 5 (the threshold level method); hand-computed runs | ✅ |
| Duration curve and the frequencies of its classes (`stats duration-curve`) | Searcy (1959), Vogel and Fennessey (1994), Byczkowski (1996); the mockup's Kłodzko numbers reproduced | ✅ |
| Runoff volumes (`stats runoff-volume`), rating curves by period (`hydrometrics rating-curve`) | V = Σ Q · 86,400 s; the power-law fit of section 3.8 per block of years; the mockup's Kłodzko numbers reproduced | ✅ |
| Euler type II design storm from a depth-duration curve (`EulerIIHietogram`, `euler_ii`; section 3.15) | ATV-DVWK-A 118 (2001) Kap. 5.2.2.1 as quoted by Thewes (2005), Malitz (2009), Kaźmierczak and Kotowski (2012); the storms printed by DWD (Malitz 2009), itwh (KOSTRA-DWD 2010R and 2020), Kaźmierczak and Kotowski (2012) and Wdowikowski et al. (2025) and the recorded PMAXTP tables reproduced | ✅ (the peak from 0.3·D also beyond 150 min, where the Wrocław monograph ends it at D/3; depths between the points of the curve linear in ln D) |
| Design hyetographs: whole steps, the triangle, the Beta storm (`BlockHietogram`, `TriangularHietogram`, `BetaHietogram`; section 3.16) | Chow, Maidment and Mays (1988) sec. 14.3 after Yen and Chow (1980), Example 14.3.1 reproduced; KZGW (2017) eqs. 2.20–2.22 after Węglarczyk (1993), the steps checked against `scipy.stats.beta.cdf` | ✅ (block integrals instead of KZGW's density at the ends of the intervals) |

### 4.2 Key Publications

| Source | Year | Significance for Hydrolog |
|--------|------|---------------------------|
| Nash, J.E. | 1957 | Theoretical basis of the Nash IUH model |
| Snyder, F.F. | 1938 | Definition of the Snyder synthetic UH |
| Kirpich, Z.P. | 1940 | Time of concentration formula |
| Clark, C.O. | 1945 | Translation + reservoir model |
| McCarthy, G.T. | 1938 | Muskingum method: wedge storage `S = K [X I + (1 - X) O]` |
| Cunge, J.A. | 1969 | Muskingum parameters from the diffusion of the flood wave: `K = dx / c`, `X = (1 - Q / (T S0 c dx)) / 2` |
| Kalinin, G.P. and Milyukov, P.I. | 1957 | Cascade of reservoirs for channel routing with a characteristic reach length `Δx_c = Q / (T S0 c)` |
| FAA | 1970 | Tc formula for overland flow (AC 150/5320-5B, fig. 7) |
| Kerby, W.S. | 1959 | Tc formula for sheet flow (retardance coefficient) |
| Giandotti, M. | 1934 | Tc formula for Italian catchments |
| Roussel, M.C. et al. | 2005 | Composite Kerby-Kirpich method (TxDOT 0-4696-2) |
| Fang, X. et al. | 2005 | Kirpich's L and S: the length to the most remote point and its drop (TxDOT 0-4696-1) |
| USDA-NRCS, NEH 630 ch. 15 | 2010 | NRCS lag equation: flow length ℓ and land slope Y; the relation tlag = 0.6×Tc (eq. 15-3, after Mockus 1957) |
| Cleveland, T.G. et al. | 2012 | Low-slope offset of Kerby-Kirpich (TxDOT 0-6382-P1) |
| Rao, Delleur, Sarma | 1972 | Regression of Nash parameters for urbanised catchments |
| Lutz, W. | 1984 | Estimation of Nash parameters from physiographic characteristics |
| USDA TR-55 | 1986 | SCS-CN method (it contains neither the relation tlag = 0.6×Tc nor the dimensionless unit hydrograph) |
| KZGW | 2017 | Polish methodology, f(N) table for Lutz |
| Fisher, R.A. and Tippett, L.H.C. | 1928 | Limiting distributions of the smallest and largest sample value |
| Gumbel, E.J. | 1958 | Statistics of extreme values (distribution for minima) |
| Coles, S. | 2001 | GEV estimation by maximum likelihood (ch. 3) |
| Smith, R.L. | 1985 | Maximum likelihood in nonregular cases: no maximum of the likelihood where the density is infinite at a bound of the support (GEV ξ ≤ −1, Pearson III \|γ\| ≥ 2, Weibull shape ≤ 1) |
| Hosking, J.R.M. and Wallis, J.R. | 1997 | L-moments; parameters of the GEV and Pearson III from them (`fit_method` `l_moments`) |
| Mann, H.B. and Whitney, D.R. | 1947 | The U test of two samples (`stats homogeneity`) |
| Smirnov, N.V. | 1939 | The two-sample Kolmogorov-Smirnov test (`stats homogeneity`) |
| Pettitt, A.N. | 1979 | The non-parametric change-point test and its approximate p-value (`stats homogeneity`) |
| USDA Soil Survey Manual | 2017 | Texture triangle, definitions of the 12 texture classes (ch. 3, pp. 122–124) |
| ATV-DVWK (A 118) | 2001 | The Euler type II model rain: the increments of one depth-duration curve, the peak interval from 0.3·D (as quoted by Thewes, 2005) |
| Malitz, G. (DWD) | 2009 | DWD's description of the Euler type II storm and its printed 60-min storms |
| Kaźmierczak, B. and Kotowski, A. | 2012 | The Euler type II storm in Polish practice; the Wrocław depth-duration formula (2.6) |
| Ozga-Zieliński, B. (Ed.), IMGW-PIB | 2022 | PMAXTP: the depth-duration curves that `precip pmaxtp` fetches |

---

## 5. Common Mistakes and How to Avoid Them

### 5.1 Mistake: Nash IUH + Kirpich without from_lutz()

```
┌─────────────────────────────────────────────────────────────────────┐
│  MISTAKE: Deriving the Nash K from ConcentrationTime.kirpich()     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  K = 0.6 × Tc / n assumes the SCS relation tlag = 0.6 × Tc.        │
│  This relation is specific to the SCS method and has NO scientific │
│  justification for the Nash model (NashIUH.from_tc() was removed   │
│  in v0.8.0 for this reason).                                       │
│                                                                     │
│  CONSEQUENCES:                                                      │
│  - Parameter K is computed from an invalid relationship            │
│  - The IUH shape may not match the catchment characteristics       │
│  - Results may differ significantly from calibrated methods        │
│                                                                     │
│  SOLUTION:                                                          │
│  Use NashIUH.from_lutz() with physiographic parameters:            │
│  - L_km (stream length)                                            │
│  - Lc_km (distance to the centroid)                                │
│  - slope (slope)                                                    │
│  - manning_n (Manning coefficient)                                 │
│  - forest_pct, urban_pct (land cover)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Mistake: Snyder UH + an External Tc

```
┌─────────────────────────────────────────────────────────────────────┐
│  MISTAKE: Computing Tc with Kirpich and passing it to Snyder       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  The Snyder model has a BUILT-IN lag time estimation formula:      │
│  tL = Ct × (L × Lc)^0.3                                            │
│                                                                     │
│  There is NO "tc" parameter in the SnyderUH constructor!           │
│                                                                     │
│  SOLUTION:                                                          │
│  Supply L_km and Lc_km directly:                                   │
│                                                                     │
│  snyder = SnyderUH(                                                │
│      area_km2=100,                                                 │
│      L_km=15,      # stream length                                 │
│      Lc_km=8,      # to the centroid                               │
│      ct=1.5,                                                       │
│      cp=0.6                                                        │
│  )                                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Mistake: Mixing K Units in the Nash Model

```
┌─────────────────────────────────────────────────────────────────────┐
│  MISTAKE: Supplying K in hours when minutes are expected (or vice  │
│  versa)                                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  - NashIUH(k_min=...) expects K in MINUTES                         │
│  - HydrographGenerator(uh_params={"k": ...}) defaults to HOURS     │
│                                                                     │
│  SOLUTION:                                                          │
│  Always state the unit explicitly:                                 │
│                                                                     │
│  # Directly (always minutes)                                       │
│  nash = NashIUH(n=3, k_min=45.0)                                   │
│                                                                     │
│  # Through HydrographGenerator (hours by default)                  │
│  gen = HydrographGenerator(                                        │
│      uh_model="nash",                                              │
│      uh_params={"n": 3, "k": 0.75, "k_unit": "hours"}  # 45 min    │
│  )                                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. References

### Original Publications

1. **Clark, C.O.** (1945). Storage and the Unit Hydrograph. *Transactions of the American Society of Civil Engineers*, 110, 1419-1446.

2. **Giandotti, M.** (1934). Previsione delle piene e delle magre dei corsi d'acqua. *Memorie e Studi Idrografici*, Vol. 8. Ministero dei Lavori Pubblici, Roma.

3. **Kirpich, Z.P.** (1940). Time of concentration of small agricultural watersheds. *Civil Engineering*, 10(6), 362.

4. **Lutz, W.** (1984). Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen. *Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft*, H. 24, Universität Karlsruhe.

5. **Nash, J.E.** (1957). The form of the instantaneous unit hydrograph. *International Association of Scientific Hydrology*, 45(3), 114-121.

6. **Rao, R.A., Delleur, J.W., & Sarma, B.S.P.** (1972). Conceptual Hydrologic Models for Urbanizing Basins. *Journal of the Hydraulics Division, ASCE*, 98(HY7), 1205-1220.

7. **Sarma, P.B.S., Delleur, J.W., & Rao, A.R.** (1969). A Program in Urban Hydrology, Part II. *Purdue University Water Resources Research Center, Technical Report No. 9*. https://docs.lib.purdue.edu/watertech/8/

8. **Snyder, F.F.** (1938). Synthetic unit-graphs. *Transactions of the American Geophysical Union*, 19, 447-454.

### Technical Documentation

9. **FAA** (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, fig. 7 and table I. Federal Aviation Administration, U.S. Department of Transportation.

10. **Kerby, W.S.** (1959). Time of concentration for overland flow. *Civil Engineering*, 29(3), 174.

11. **Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., & Garcia, C.A.** (2005). Time-parameter estimation for applicable Texas watersheds. *TxDOT Research Report 0-4696-2*. Texas Department of Transportation.

12. **KZGW** (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych (Update of the methodology for computing maximum flows and precipitation; National Water Management Authority, Poland). Annex 2, Table C.2.

13. **USACE HEC-HMS** (2024). Technical Reference Manual. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/

14. **USDA-NRCS** (1986). Urban Hydrology for Small Watersheds. Technical Release 55 (TR-55).

15. **Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B., & Malla, R.** (2005). Literature review on timing parameters for hydrographs. *TxDOT Research Report 0-4696-1*.

16. **Cleveland, T.G., Thompson, D.B., Fang, X., & Li, M.-H.** (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. *TxDOT Product 0-6382-P1*, Texas Tech University.

17. **Mota, A.A. & Kobiyama, M.** (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. *Revista Brasileira de Recursos Hídricos*, 20(1), 55-59.

### Textbooks

18. **Banasik, K.** (2009). Wyznaczanie wezbrań powodziowych w małych zlewniach zurbanizowanych (Determining flood waves in small urbanised catchments). *Wyd. SGGW, Warszawa*.

19. **Bedient, P.B. & Huber, W.C.** (1992). *Hydrology and Floodplain Analysis*. Addison-Wesley.

20. **Fisher, R.A. & Tippett, L.H.C.** (1928). Limiting forms of the frequency distribution of the largest or smallest member of a sample. *Proceedings of the Cambridge Philosophical Society*, 24(2), 180-190.

21. **Gumbel, E.J.** (1958). *Statistics of Extremes*. Columbia University Press, New York.

22. **Coles, S.** (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer, London.

23. **USDA** (2017). Soil Survey Manual. Handbook No. 18. Soil Science Division Staff, USDA-NRCS (ch. 3, "Definitions of Soil Texture Classes and Subclasses", pp. 122-124; textural triangle Fig. 3-7, p. 125).

24. **USDA-NRCS** (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 7: Hydrologic Soil Groups.

25. **Chow, V.T., Maidment, D.R. & Mays, L.W.** (1988). *Applied Hydrology*. McGraw-Hill (S-curve method for unit hydrographs, synthetic hydrographs including Snyder's).

26. **USDA-NRCS** (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (eq. 15-3: lag L = 0.6 Tc, after Mockus 1957 and Simas 1996; lag equation 15-4: ℓ is the longest flow path from the hydraulically most distant point of the watershed to the outlet, Y the mean terrain slope of the catchment).

27. **TxDOT**. Hydraulic Design Manual, Chapter 4 Hydrology, Section 11: Time of Concentration (the 1200 ft = 366 m limit for the Kerby formula; the Kerby-Kirpich method).

### Flood Routing

28. **McCarthy, G.T.** (1938). The unit hydrograph and flood routing. Unpublished manuscript presented at the conference of the North Atlantic Division, U.S. Army Corps of Engineers, New London, Connecticut, 24 June 1938.

29. **University of Iowa**. Lesson 27: Hydrologic Routing, Muskingum Method (course handout EX-L27-Muskingum-soln). https://user.engineering.uiowa.edu/~flood/handouts/EX-L27-Muskingum-soln.pdf

30. **Cunge, J.A.** (1969). On the subject of a flood propagation computation method (Muskingum method). *Journal of Hydraulic Research*, 7(2), 205-230.

31. **USDA-NRCS** (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (Amendment 69): example 17-4, appendices B and C. https://damtoolbox.org/images/a/a6/NEH17.pdf

32. **Kalinin, G.P. and Milyukov, P.I.** (1957). O raschete neustanovivshegosya dvizheniya vody v otkrytykh ruslakh (On the computation of unsteady flow in open channels). *Meteorologiya i Gidrologiya*, 10, 10-18 (Leningrad); cited after Szilagyi, J. et al. (2005), *Journal of Hydrology*, 311, 219-229.

33. **Ponce, V.M.** (1980, online version 2016). Linear reservoirs and numerical diffusion. https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html (the gamma response of Nash, the SSARR equation as Muskingum with `X = 0`, the Kalinin-Milyukov characteristic reach length).

### Synthetic Unit Hydrographs

34. **Asquith, W.H. & Roussel, M.C.** (2007). An initial-abstraction, constant-loss model for unit hydrograph modeling for applicable watersheds in Texas. *U.S. Geological Survey Scientific Investigations Report 2007-5243* (the gamma unit hydrograph from its peak and time to peak, eq. 2 and 4). https://pubs.usgs.gov/sir/2007/5243/

### Flood Frequency

35. **Hosking, J.R.M. & Wallis, J.R.** (1997). *Regional Frequency Analysis: An Approach Based on L-Moments*. Cambridge University Press (sample L-moments; the GEV, Pearson III and lognormal L-moments and the estimators of their parameters).

### Homogeneity

36. **Mann, H.B. & Whitney, D.R.** (1947). On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics*, 18(1), 50-60.

37. **Smirnov, N.V.** (1939). On the estimation of the discrepancy between empirical curves of distribution for two independent samples. *Bulletin Mathématique de l'Université de Moscou*, 2(2).

38. **Pettitt, A.N.** (1979). A non-parametric approach to the change-point problem. *Journal of the Royal Statistical Society, Series C (Applied Statistics)*, 28(2), 126-135.

### Regime, Seasonality, Trends and Baseflow

39. **Pardé, M.** (1933). *Fleuves et rivières*. Armand Colin, Paris.

40. **Dynowska, I.** (1997). Reżim odpływu rzecznego (River runoff regime). In: *Atlas Rzeczypospolitej Polskiej*. Główny Geodeta Kraju, Warszawa.

41. **Wrzesiński, D.** (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym (A typology of the river regime in Poland in supervised and unsupervised approaches). *Badania Fizjograficzne, Seria A – Geografia Fizyczna*, 8 (A68), 253-264. doi:10.14746/bfg.2017.8.19

42. **Wrzesiński, D.** (2018). Typologia reżimu odpływu rzek w Polsce w różnych fazach oscylacji północnoatlantyckiej (A typology of the river regime in Poland in the phases of the North Atlantic Oscillation). *Badania Fizjograficzne, Seria A – Geografia Fizyczna*, 9 (A69), 249-261 (the criteria of Dynowska's types on p. 250, Table 1 on pp. 253-254). doi:10.14746/bfg.2018.9.19

43. **Perz, A.** (2019). Cechy reżimu odpływu rzek Kotliny Kłodzkiej (Features of the runoff regime of the rivers of the Kłodzko Basin). *Badania Fizjograficzne, Seria A – Geografia Fizyczna*, 10 (A70), 65-83 (the spring month, March or April, p. 79). doi:10.14746/bfg.2019.10.6

44. **Walsh, R.P.D. & Lawler, D.M.** (1981). Rainfall seasonality: description, spatial patterns and change through time. *Weather*, 36(7), 201-208.

45. **Bayliss, A.C. & Jones, R.C.** (1993). Peaks-over-threshold flood database: summary statistics and seasonality. *Report No. 121*, Institute of Hydrology, Wallingford. The same work as a report to MAFF (March 1992), section 3 on the seasonality, is open: <https://nora.nerc.ac.uk/id/eprint/14407/>.

46. **Burn, D.H.** (1997). Catchment similarity for regional flood frequency analysis using seasonality measures. *Journal of Hydrology*, 202(1-4), 212-230.

47. **Wilks, D.S.** (2011). *Statistical Methods in the Atmospheric Sciences*, 3rd ed. Academic Press, Oxford (section 9.4, harmonic analysis). With **Feichtinger, H.G., Gröchenig, K. & Strohmer, T.** (1995). Efficient numerical methods in non-uniform sampling theory. *Numerische Mathematik*, 69, 423-440 (Propositions 1-2: the largest gap a fit of K harmonics allows), and **Robson, A. & Reed, D.** (1999). *Flood Estimation Handbook*, Vol. 3, Institute of Hydrology (Additional Note 16.1: the seasonality of floods).

48. **Mann, H.B.** (1945). Nonparametric tests against trend. *Econometrica*, 13(3), 245-259.

49. **Kendall, M.G.** (1975). *Rank Correlation Methods*, 4th ed. Charles Griffin, London.

50. **Hirsch, R.M., Slack, J.R. & Smith, R.A.** (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research*, 18(1), 107-121.

51. **Sen, P.K.** (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63(324), 1379-1389.

52. **Conover, W.J.** (1980). *Practical Nonparametric Statistics*, 2nd ed. Wiley, New York.

53. **Gilbert, R.O.** (1987). *Statistical Methods for Environmental Pollution Monitoring*. Van Nostrand Reinhold, New York (chapter 16: Eq. 16.3, Example 16.2, section 16.5, Example 16.5, Exercises 16.1-16.3 and their answers on p. 224, the program of appendix B).

54. **Lyne, V. & Hollick, M.** (1979). Stochastic time-variable rainfall-runoff modelling. *Hydrology and Water Resources Symposium*, Institution of Engineers Australia, Perth.

55. **Nathan, R.J. & McMahon, T.A.** (1990). Evaluation of automated techniques for base flow and recession analyses. *Water Resources Research*, 26(7), 1465-1473.

56. **Ladson, A.R., Brown, R., Neal, B. & Nathan, R.** (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. *Australasian Journal of Water Resources*, 17(1), 25-34. doi:10.7158/13241583.2013.11465417; the authors' code and example: https://github.com/TonyLadson/BaseflowSeparation_LyneHollick

57. **Tallaksen, L.M.** (1995). A review of baseflow recession analysis. *Journal of Hydrology*, 165(1-4), 349-370.

### Meteorological Statistics

58. **Copernicus European and Global Drought Observatories (EDO, GDO)** (2025). *EDO and GDO Indicator Factsheet: Standardized Precipitation Index (SPI)*. European Union, https://drought.emergency.copernicus.eu/ (the gamma fits on the baseline January 1991 – December 2020).

59. **Edwards, D.C. & McKee, T.B.** (1997). Characteristics of 20th century drought in the United States at multiple time scales. *Climatology Report* 97-2, Colorado State University, Fort Collins.

60. **Eurostat** (2024). Energy statistics – cooling and heating degree days (nrg_chdd), reference metadata, section 3.4.

61. **Gąsiorek, E. & Musiał, E.** (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. *Woda-Środowisko-Obszary Wiejskie*, 11(4), 107-119 (Kaczorowska's classes on p. 108; the monthly limits of Tomaszewska, 1994, after Kosiba, 1948, in Table 1).

62. **Hyndman, R.J. & Fan, Y.** (1996). Sample quantiles in statistical packages. *The American Statistician*, 50(4), 361-365.

63. **Kaczorowska, Z.** (1962). Opady w Polsce w przekroju wieloletnim. *Prace Geograficzne IG PAN*, 33.

64. **Klein Tank, A.M.G., Zwiers, F.W. & Zhang, X.** (2009). *Guidelines on Analysis of Extremes in a Changing Climate in Support of Informed Decisions for Adaptation*. WMO-TD No. 1500 (WCDMP-No. 72), World Meteorological Organization, Geneva (the ETCCDI indices, CDD and CWD, and the base period of the percentile indices).

65. **McKee, T.B., Doesken, N.J., & Kleist, J.** (1993). The relationship of drought frequency and duration to time scales. *8th Conference on Applied Climatology*, Anaheim, 179-184.

66. **Miś, F.** (2026). Spatiotemporal variability of atmospheric drought during the growing season in Poland: a multi-index analysis based on SPEI, VPD, and HTC (1980–2024). *Theoretical and Applied Climatology*, 157(12), 790 (eq. 4).

67. **Oliver, J.E.** (1980). Monthly precipitation distribution: a comparative index. *Professional Geographer*, 32(3), 300-309.

68. **Radzka, E.** (2014). Hydrothermal characteristics of vegetation period in central-eastern Poland in years 1971–2005. *Folia Pomeranae Universitatis Technologiae Stetinensis*, 312(31), 133-142.

69. **Selyaninov, G.T.** (1928). On the agricultural estimation of climate. *Trudy po sel'skokhozyaystvennoy meteorologii*, 20, 165-177.

70. **Skowera, B. & Puła, J.** (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971–2000. *Acta Agrophysica*, 3(1), 171-177 (the classes of k on p. 172).

71. **Thom, H.C.S.** (1958). A note on the gamma distribution. *Monthly Weather Review*, 86, 117-122.

72. **WMO** (2012). *Standardized Precipitation Index User Guide*. WMO-No. 1090, World Meteorological Organization, Geneva (chapter 2, the length of the record; sections 5.1.1 and 5.1.2, the SPI against the totals of the years on record, at least 30 years).

73. **WMO** (2017). *WMO Guidelines on the Calculation of Climate Normals*. WMO-No. 1203, World Meteorological Organization, Geneva (chapter 2, normals as the benchmark of anomalies; chapter 3 and section 5.1, the climatological standard normal 1991–2020 and the reference normal 1961–1990; section 4.4, missing data, 4.4.2 a normal from 80 % of the years; section 5.2.2, longer periods for percentiles).

74. **Wypych, A., Sulikowska, A., Ustrnul, Z., & Czekierda, D.** (2017). Variability of growing degree days in Poland. *International Journal of Biometeorology*, 61(1), 49-59.

75. **Zhang, X. et al.** (2011). Indices for monitoring changes in extremes based on daily temperature and precipitation data. *WIREs Climate Change*, 2(6), 851-870.

### Station Analyses

76. **Byczkowski, A.** (1996). *Hydrologia*, t. 1. Wydawnictwo SGGW, Warszawa (characteristic values of the first and second degree; the classes of the stages with the days including higher and lower).

77. **Searcy, J.K.** (1959). Flow-duration curves. *Manual of Hydrology, Part 2*. USGS Water-Supply Paper 1542-A.

78. **Tallaksen, L.M. & van Lanen, H.A.J.** (Eds.) (2004). *Hydrological Drought: Processes and Estimation Methods for Streamflow and Groundwater*. Elsevier, Amsterdam (chapter 5, the threshold level method).

79. **Vogel, R.M. & Fennessey, N.M.** (1994). Flow-duration curves. I: New interpretation and confidence intervals. *Journal of Water Resources Planning and Management*, 120(4), 485-504.

### Maximum Likelihood of the Frequency Analyses

80. **Smith, R.L.** (1985). Maximum likelihood estimation in a class of nonregular cases. *Biometrika*, 72(1), 67-90.

### Design Storms

81. **ATV-DVWK** (2001). Arbeitsblatt ATV-DVWK-A 118, Kap. 5.2.2.1 (the Euler type II model rain), as quoted by Thewes (2005); the Arbeitsblatt itself was not read.

82. **Thewes, K.** (2005). Diplomarbeit, Fachhochschule Trier (p. 10: the peak rule and the arrangement of ATV-DVWK-A 118; p. 11: the duration of a model rain).

83. **Malitz, G.** (2009). Stark- und Extremniederschlag im Kurzzeitbereich. Deutscher Wetterdienst, slides of the 2. Trierer Workshop (slide 17, the Euler type II storm; slides 18 and 19, two storms of 60 min).

84. **Kaźmierczak, B. & Kotowski, A.** (2012). *Weryfikacja przepustowości kanalizacji deszczowej w modelowaniu hydrodynamicznym* (Verifying the capacity of storm sewers in hydrodynamic modelling). Oficyna Wydawnicza Politechniki Wrocławskiej, Wrocław (formula 2.6 on p. 19; the Euler type II storm on pp. 31–32; Tab. 4.6).

85. **Wdowikowski, M., Kaźmierczak, B., Wartalska, K., Kotowski, A., Szymczewski, S., Przestrzelska, K. & Domalewska, W.** (2025). The impact of climate change on the functioning of drainage systems in industrial areas—a case study. *Atmosphere*, 16(3), 347. doi:10.3390/atmos16030347 (Tab. 2: the PMAXTP depths of Wrocław, C = 5 years, and a 60-min Euler type II storm).

86. **Ozga-Zieliński, B. (Ed.)** (2022). *Modele probabilistyczne opadów maksymalnych o określonym czasie trwania i prawdopodobieństwie przewyższenia – projekt PMAXTP*. IMGW-PIB, Warszawa (pp. 32–35: the power law over the durations of a station).

87. **Yen, B.C. & Chow, V.T.** (1980). Design hyetographs for small drainage structures. *Journal of the Hydraulics Division, ASCE*, 106(HY6), 1055–1076 (the triangular hyetograph, as given by Chow, Maidment and Mays 1988, sec. 14.3, pp. 462–465; the paper itself was not read).

88. **Węglarczyk, S.** (1993), as cited by KZGW (2017), ch. II.3, eqs. 2.20–2.22, p. 25 (the Beta hyetograph of a daily design total; the paper itself was not read).

### Statistical Tests

89. **Stephens, M.A.** (1974). EDF statistics for goodness of fit and some comparisons. *Journal of the American Statistical Association*, 69(347), 730-737 (A² and the case-0 critical values).

90. **Stute, W., González Manteiga, W. & Presedo Quindimil, M.** (1993). Bootstrap based goodness-of-fit-tests. *Metrika*, 40, 243-256. doi:10.1007/BF02613687 (the parametric bootstrap of EDF statistics with estimated parameters).

91. **Schröer, G. & Trenkler, D.** (1995). Exact and randomization distributions of Kolmogorov-Smirnov tests two or three samples. *Computational Statistics & Data Analysis*, 20(2), 185-202 (the exact two-sample distribution with tied values, R's `ks.test`).

92. **MacMahon, P.A.** (1916). *Combinatory Analysis*, Vol. 1. Cambridge University Press (the numbers of inversions of the orderings of a multiset, the q-multinomial coefficients).

93. **Helsel, D.R., Hirsch, R.M., Ryberg, K.R., Archfield, S.A. & Gilroy, E.J.** (2020). *Statistical Methods in Water Resources*. USGS Techniques and Methods 4-A3. doi:10.3133/tm4a3 (Example 5.1, the rank-sum data; Example 10.3, the exact Mann-Kendall p-value of 7 values).

94. **WMO** (2009). *Manual on Low-flow Estimation and Prediction*. WMO No. 1029, Operational Hydrology Report No. 50, World Meteorological Organization, Geneva (section 5.3, Eq. 5.1-5.3: the recession constant).

---

**Document version:** 1.14
**Last updated:** 2026-11-18
