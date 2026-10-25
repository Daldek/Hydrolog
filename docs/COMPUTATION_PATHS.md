# Computation Paths for Unit Hydrograph Models (plus HSG and the Fisher–Tippett Distribution)

**Document version:** 1.3
**Date:** 2026-10-19
**Applies to:** Hydrolog >= 1.0.0 (sections 3.3.6, 3.4.6, 3.5, 3.6, 3.7 and 3.8 describe behaviour from v1.0.0; the rest: >= 0.6.0)

---

## 1. Introduction

### 1.1 Purpose of the Document

Hydrolog implements 4 unit hydrograph models: **SCS**, **Nash**, **Clark** and **Snyder**. Each model has different input parameters and different methods for estimating them.

**An incorrect combination of methods** (e.g. using the time of concentration from the Kirpich formula in the Nash model through `from_tc()`) can lead to wrong results without scientific justification.

This document serves as a guide that:
- States clearly the **correct computation paths** for each model
- **Warns** against incorrect use of methods
- Gives the **literature justification** for each path

### 1.2 Compatibility Matrix

| Model | Kirpich | NRCS | Giandotti | FAA | Kerby | Kerby-Kirpich | from_lutz() | from_urban_regression() | Directly | Own method |
|-------|:-------:|:-------:|:---------:|:---:|:-----:|:-------------:|:-----------:|:-----------------------:|:------------:|:-------------:|
| **SCS UH** | ✅ | ✅ | ✅ | ✅¹ | ✅¹ | ✅ | - | - | - | - |
| **Nash IUH** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | - |
| **Clark IUH** | ✅ | ✅ | ✅ | ✅¹ | ✅¹ | ✅ | - | - | ✅ | - |
| **Snyder UH** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | - | ✅ | ✅ |

**Legend:**
- ✅ **OK** - correct use, confirmed by the literature
- ⚠️ **DEPRECATED** - works, but has no scientific justification (will be removed in v1.0.0)
- ❌ **NOT APPLICABLE** - the model does not use an external Tc
- ✅¹ **OK with a limitation** - FAA and Kerby compute the overland flow time (flow paths of the order of hundreds of metres), so as a catchment Tc they are suitable only for small catchments without a distinct channel; for a catchment with a channel, Tc is given by Kerby-Kirpich (overland flow + channel) or by Kirpich (section 3.7)

---

## 2. Hydrograph Models - Overview

### 2.1 SCS Unit Hydrograph

| Feature | Value |
|---------|-------|
| **Type** | Synthetic, empirical |
| **Input parameters** | `area_km2`, `tc_min` |
| **Source** | USDA-NRCS TR-55 (1986) |
| **Characteristics** | NRCS dimensionless curve (33 points) |

**Key relation:** `tlag = 0.6 × Tc` (part of the SCS method)

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
| **Input parameters** | `L_km`, `Lc_km`, `Ct`, `Cp` |
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
    │ tc=3.981×L^0.77 │ │ tc=f(L,S,CN)│ │ tc=f(A,L,H) │
    │  ×S^(-0.385)    │ │             │ │             │
    │    [min]        │ │             │ │             │
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
    └───────┬───────┘                   │ (TR-55, 1986) │
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

> **Note on the Kirpich constant:** The literature contains two equivalent forms:
> - `tc[min] = 3.981 × L[km]^0.77 × S^(-0.385)` (result in minutes -- used in the code)
> - `tc[h] = 0.0663 × L[km]^0.77 × S^(-0.385)` (result in hours)
>
> Both forms are identical: `3.981 / 60 ≈ 0.0663`. The Hydrolog implementation uses the constant **3.981** and returns the result in **minutes**.

#### 3.1.2 Correct Tc Estimation Methods

| Method | Status | Justification |
|--------|--------|---------------|
| Kirpich | ✅ OK | Tc is an input parameter of the SCS method |
| NRCS | ✅ OK | Method developed together with the SCS UH (TR-55) |
| Giandotti | ✅ OK | Tc is an input parameter of the SCS method |
| FAA | ✅ OK¹ | Tc is an input parameter of the SCS method (overland flow time) |
| Kerby | ✅ OK¹ | Tc is an input parameter of the SCS method (sheet flow time, path up to 366 m) |
| Kerby-Kirpich | ✅ OK | Composite Tc (overland + channel flow) is an input parameter of SCS |

**Literature justification:**
- The relation `tlag = 0.6 × Tc` comes from USDA TR-55 (1986)
- It was developed **specifically** for the SCS Dimensionless Unit Hydrograph
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
    │  3. up = 0.66/tp^1.04    │ │ 2. k = 0.56×A^0.39   │    │
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

#### 3.2.2 WARNING: from_tc() is DEPRECATED

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ⚠️  DEPRECATED PATH  ⚠️                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  The NashIUH.from_tc() method uses the relation: tlag = 0.6 × Tc   │
│                                                                     │
│  This relation comes from the SCS method (TR-55, 1986) and has NO  │
│  scientific justification for the Nash model!                      │
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
│  CONSEQUENCES OF INCORRECT USE:                                     │
│  - Parameter K is computed from an invalid relationship            │
│  - The IUH shape may not match the catchment characteristics       │
│  - It cannot be verified against observed data                     │
│                                                                     │
│  SOLUTION:                                                          │
│  Use NashIUH.from_lutz() or supply n and K directly                │
└─────────────────────────────────────────────────────────────────────┘
```

**Status:** `from_tc()` will be removed in version 1.0.0

#### 3.2.3 Correct Estimation Methods

| Method | Status | Justification |
|--------|--------|---------------|
| `from_lutz()` | ✅ RECOMMENDED | Developed specifically for Nash (Lutz, 1984) |
| `from_urban_regression()` | ✅ OK | Regression for urbanised catchments (Rao, Delleur, Sarma 1972) |
| Directly `n`, `K` | ✅ OK | When you have calibrated values |
| ~~Method of moments~~ | REMOVED in v0.5.1 | Requires data from an observed hydrograph |
| `from_tc()` | ⚠️ DEPRECATED | No scientific justification |

#### 3.2.4 Lutz Method Formulas

```
1. P₁ = 3.989 × n_manning + 0.028

2. tp = P₁ × (L × Lc / Jg^1.5)^0.26 × e^(-0.016U) × e^(0.004W)   [h]

3. up = 0.66 / tp^1.04                                            [1/h]

4. f(N) = tp × up → solve numerically for N
   (where f(N) = (N-1)^N × e^(-(N-1)) / Γ(N))

5. K = tp / (N-1)                                                 [h]
```

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

#### 3.2.7 Code Example - INCORRECT USE (DO NOT DO THIS!)

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import NashIUH

# ⚠️ INCORRECT - THIS WILL EMIT A DeprecationWarning!
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
nash = NashIUH.from_tc(tc_min=tc, n=3.0)  # DEPRECATED!

# Use from_lutz() instead:
nash_correct = NashIUH.from_lutz(
    L_km=8.2, Lc_km=4.5, slope=0.023, manning_n=0.035
)
```

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
| R/Tc ratio | ✅ OK | Typical values: 0.2-1.5 |

**Literature justification:**
- In the Clark model, Tc represents the **translation time** - the time water takes to travel from the farthest point of the catchment to the outlet
- This is **consistent** with the physical interpretation of the time of concentration
- Source: Clark (1945), HEC-HMS Technical Reference Manual
- ¹ FAA and Kerby: only small catchments without a channel (as in section 3.1.2); for a catchment with a channel use Kerby-Kirpich

#### 3.3.3 Choosing the R Coefficient

| Catchment type | R/Tc ratio | Description |
|----------------|------------|-------------|
| Steep, urban | 0.2-0.4 | Little storage, fast runoff |
| Natural, average | 0.4-0.8 | Typical conditions |
| Flat, swampy | 0.8-1.5 | Large storage, slow runoff |

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
`details.reason = "unstable_timestep"`.

#### 3.3.5 Code Example

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import ClarkIUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Step 1: Compute Tc
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Step 2: Determine the storage coefficient R
r_min = 0.5 * tc  # R/Tc = 0.5 (typical value)

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

> **Change in v1.0.0 (bug fix).** Versions < 1.0.0 shifted the S-curve by `round(D/dt)` steps but divided by D. For D that is not a multiple of the step, the volume was `round(D/dt)·dt/D` mm: **1.333 mm for D = 1.5·dt** and 0.8 mm for D = 2.5·dt (discharges 33% too large or 20% too small), and for D < dt/2 `to_unit_hydrograph` raised `ValueError` (`s_curve[:-0]`). Since v1.0.0 the volume is 1.000 mm for every D, and a non-positive or infinite D or step raises `InvalidParameterError`.

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
    │              (gamma-like shape)                       │
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
    L_km=15.0,      # Stream length
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

#### 3.4.6 Snyder in `HydrographGenerator`: Unit Hydrograph for D = Time Step (since v1.0.0)

Discrete convolution treats the unit hydrograph as the response to 1 mm of effective precipitation in a single step `dt`. Therefore `HydrographGenerator` builds the Snyder hydrograph for a duration **D = dt** (the tLR, tpR and qpR correction from section 3.4.3), and not for the standard tD = tL/5.5 (Snyder 1938; USACE HEC-HMS, Technical Reference Manual, "Snyder Unit Hydrograph Model"; Chow, Maidment, Mays 1988):

```python
uh = snyder.generate(timestep_min=dt, duration_min=dt)   # this is how the generator computes it
```

Versions < 1.0.0 called `snyder.generate(timestep_min=dt)`, i.e. the hydrograph for tD, and convolved it in steps of `dt`: for a step shorter than tD the peak was too low and too late (tpR = tLR + D/2, tLR = tL + 0.25 (D − tD)), for a longer one too high and too early. `uh_time_to_peak_min` in the `hydrograph generate` result is tpR, and the report documents Δt equal to the step.

| Catchment 45 km², L = 12 km, Lc = 6 km, Ct = 1.5, Cp = 0.6, CN 72, beta rainfall 50 mm/120 min, step 5 min | before v1.0.0 (D = tD = 59.0 min) | since v1.0.0 (D = 5 min) |
|------|------:|------:|
| Unit hydrograph: time to peak tp [min] | 354.2 | 313.7 |
| Unit hydrograph: peak qp [m³/s/mm] | 1.379 | 1.542 |
| Runoff hydrograph: Qmax [m³/s] (time [min]) | 9.76 (405) | 10.90 (365) |

For a step equal to tD the correction vanishes (tLR = tL) and the result is the same as before.

---

### 3.5 Hydrologic Soil Groups (HSG) and Area-Weighted CN (`hydrolog.soil`, since v1.0.0)

HSG (A-D) is one of the two factors of the CN number (the other is land cover). The `hydrolog.soil` module determines HSG from clay, sand and silt content; the rules and mapping were transferred from Kartograf 0.8.0 (`kartograf.hydrology.hsg`, ADR-025), and Kartograf remains responsible for downloading rasters (`download_soil`).

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

Rules (c - clay, s - sand, si - silt, in % of the sum of the three fractions), the first one satisfied wins:

| # | Class | Condition |
|---|-------|-----------|
| 1 | `sand` | si + 1.5·c < 15 |
| 2 | `loamy_sand` | si + 1.5·c ≥ 15 and si + 2·c < 30 |
| 3 | `sandy_loam` | (7 ≤ c ≤ 20, s > 52, si + 2·c ≥ 30) or (c < 7, si < 50, si + 2·c ≥ 30) |
| 4 | `silt` | si ≥ 80, c < 12 |
| 5 | `silt_loam` | (si ≥ 50, 12 ≤ c < 27) or (50 ≤ si < 80, c < 12) |
| 6 | `loam` | 7 ≤ c ≤ 27, 28 ≤ si < 50, s ≤ 52 |
| 7 | `sandy_clay_loam` | 20 ≤ c < 35, si < 28, s > 45 |
| 8 | `clay_loam` | 27 ≤ c < 40, 20 < s ≤ 45 |
| 9 | `silty_clay_loam` | 27 ≤ c < 40, s ≤ 20 |
| 10 | `sandy_clay` | c ≥ 35, s > 45 |
| 11 | `silty_clay` | c ≥ 40, si ≥ 40 |
| 12 | `clay` | c ≥ 40, s ≤ 45, si < 40 |

- The rules compare the **amounts** of the fractions with their sum (without division, in `float64`), so the result does not depend on the unit (%, g/kg) as long as it is common to the three rasters, and values on the triangle boundaries are classified exactly.
- A sum equal to zero gives `loam` in the texture classifier; in `classify_hsg` such a cell (all three fractions equal to 0, the SoilGrids convention for gaps) is no data.
- No data (code 0) is also NaN/±Inf and a value equal to the `nodata` marker of any of the three rasters. A negative amount in a cell with data is an error.

#### 3.5.3 Texture → HSG

| HSG | Texture classes |
|-----|-----------------|
| A | `sand`, `loamy_sand` |
| B | `sandy_loam`, `loam`, `silt_loam`, `silt` |
| C | `sandy_clay_loam`, `clay_loam`, `silty_clay_loam` |
| D | `sandy_clay`, `silty_clay`, `clay` |

The mapping is **more lenient than the TR-55 table** (USDA-NRCS NEH Part 630, ch. 7) for three transitional classes: `sandy_loam` = B (TR-55: A), `clay_loam` and `silty_clay_loam` = C (TR-55: D). Their actual group also depends on soil structure, and the middle group is conservative for the SCS-CN method (Kartograf ADR-025, decision b). Changing the `TEXTURE_TO_HSG` table changes CN for every user.

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

### 3.6 Minimum Flows: the Fisher–Tippett Distribution for Minima (`LowFlowAnalysis`, fix in v1.0.0)

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

Because the sample minimum is the negated sample maximum with the sign changed, `min(x) = -max(-x)`, the parameters are estimated by maximum likelihood from the **negated** minima (`scipy.stats.genextreme`), and the quantile is `Q_T = -genextreme.isf(p, c, loc=-loc, scale=scale)`. The reported `shape` is the `c` parameter from `scipy.stats.genextreme` (i.e. minus the shape parameter ξ in the usual GEV notation).

> **Change in v1.0.0 (bug fix).** Versions < 1.0.0 fitted the distribution of **maxima** directly to the minima and read its quantile at the point p. That is the mirror-image distribution: it approximates the centre of the sample correctly, but its left tail is not the tail of the distribution of smallest values, so the quantiles of rare low flows were biased, increasingly so with T, and could be negative. For a synthetic sample of 1000 annual minima from the Gumbel distribution for minima (loc = 50, scale = 8), the quantile for T = 100 years was **−3821**, and since v1.0.0 it is **13.26** (theoretical value 13.20). For the Weibull distribution (k = 2, loc = 1, scale = 5) for T = 100 years: 1.24 → 1.51 (theory 1.50), for T = 1000 years: 0.33 → 1.18 (theory 1.16).

#### 3.6.2 Limitations

- The distribution is not restricted to positive flows: for `shape ≤ 0` the minima have no lower bound, and quantiles for very long return periods can be negative.
- Three parameters from a few decades of data are uncertain, especially the shape, and with it the quantiles of rare low flows (with fewer than 10 years of data the result carries a warning).
- The Kolmogorov-Smirnov test is informational (`ks_valid = False`: the parameters were estimated from the same data).

#### 3.6.3 Annual Minima (and Maxima): Complete Hydrological Years Only (fix in v1.0.0)

The annual minima of `LowFlowAnalysis` and the annual maxima of `stats flood-frequency` (from a daily series) are extremes of **whole years of observation** (KZGW 2017; WMO No. 1029, 2009): a hydrological year (1 November – 31 October) enters the sample only if the series has a value for **every** day of the year — 365 days, or 366 for a year containing 29 February (a so-called leap year: 1 November 2019 – 31 October 2020 has 366 days). A missing date or `NaN` excludes the whole year, because the year's maximum or minimum could have occurred on the day without a value. Omitted years (with the number of days with data) are reported by the notice `incomplete_years` and the result field `incomplete_years`; the library (`LowFlowAnalysis.annual_minima()`) warns with `UserWarning`, and a series without a complete year is a `CalculationError`. Practical consequence: an export covering calendar years (1 January – 31 December) loses the first hydrological year (without November and December) and the last one (only November and December).

> **Change in v1.0.0 (bug fix).** Versions < 1.0.0 took the extreme from every year present in the dates, including an incomplete one. For a synthetic calendar series 1991–2020 (a flood on 15 March and a low flow on 15 September every year), the sample had 31 "years", including 2021 with only November and December 2020 (maximum and minimum equal to the base level 5.0, with the median of complete years 13.0 and 2.2). Since v1.0.0 the sample has 29 years (1992–2020): GEV for T = 100 years **16.08 → 16.35**, Fisher–Tippett for T = 100 years **2.002 → 1.968**. For a series with gaps: fill in the data or (for maxima) supply the annual maxima directly, without dates.

#### 3.6.4 Empirical Frequency of Minima: the Non-Exceedance Convention (fix in v1.0.0)

In low-flow analysis, the return period *T* belongs to the **non-exceedance** probability *F = 1/T* (a flow equal or lower once in *T* years; WMO No. 1029, 2009; Tallaksen and van Lanen, 2004) — this is how the `fisher_tippett` quantiles are computed. The empirical positions of `LowFlowAnalysis.empirical_non_exceedance()` (result `LowFlowEmpiricalFrequency`, the `empirical` block of the `stats low-flow` command) follow the same convention: annual minima in ascending order (`values_ascending`), the *m*-th smallest has

```
Weibull (default):  F_m = m / (n + 1)          Hazen: (m − 0.5) / n          Cunnane: (m − 0.4) / (n + 0.2)
T_m = 1 / F_m                                  (the deepest low flow in n years: T = n + 1)
```

The points (F, value) therefore lie on the same plot as the `fisher_tippett` quantiles (`non_exceedance_probabilities = 1/T`). `LowFlowAnalysis.empirical_frequency()` still returns *exceedance* positions (values descending, `P = i/(n+1)`), i.e. the opposite side of the same sample (`F = 1 − P`).

> **Change in v1.0.0 (bug fix).** The `empirical` block in `stats low-flow` was the result of `empirical_frequency()`, so next to `fisher_tippett.return_periods` using the non-exceedance convention it placed `return_periods` using the exceedance convention. For `tests/fixtures/daily_flows_3y.csv` (minima 1.79; 1.88; 1.66) the deepest low flow 1.66 had T = **1.33** (P = 0.75), and since v1.0.0 it has F = 0.25 and T = **4**.

```python
from hydrolog.statistics import LowFlowAnalysis

analysis = LowFlowAnalysis(daily_flows, dates, return_periods=[10, 50, 100])
ft = analysis.fit_fisher_tippett()
print(ft.parameters)   # {"shape": ..., "loc": ..., "scale": ...}
print(ft.quantiles)    # flow [m³/s] once in 10, 50, 100 years
```

The same analysis in the CLI: `hydrolog stats low-flow --input-file q_dobowe.csv --value-column Q --date-column date --return-periods 10,50,100`.

### 3.7 Time of Concentration from a Catchment (`WatershedParameters.calculate_tc`, `tc watershed`; fixes in v1.0.0)

`WatershedParameters.calculate_tc(method)` and the `tc watershed` command compute tc with the chosen method from the catchment fields. The formula arguments are derived from the fields by `WatershedParameters.tc_parameters(method)`; the same numbers appear in the command's `result.parameters` and in the time of concentration section of the report.

| Method | Length | Slope | Required fields beyond the basic ones |
|--------|--------|-------|---------------------------------------|
| Kirpich | `channel_length_km`, otherwise `length_km` | `channel_slope_m_per_m`, then `mean_slope_m_per_m`, then H/(L·1000) | - |
| NRCS | same as Kirpich | **`mean_slope_m_per_m`** (mean catchment terrain slope Y), then `channel_slope_m_per_m`, then H/(L·1000) | `cn` |
| Giandotti | same as Kirpich | - (H = `elevation_mean_m` − `elevation_min_m`; without a mean: the midpoint of the range) | - |
| FAA | **`overland_length_km`** | **`overland_slope_m_per_m`** | `runoff_coeff`, `overland_length_km`, `overland_slope_m_per_m` |
| Kerby | **`overland_length_km`** | **`overland_slope_m_per_m`** | `retardance`, `overland_length_km`, `overland_slope_m_per_m` |
| Kerby-Kirpich | `overland_length_km` and `channel_length_km` | `overland_slope_m_per_m` and `channel_slope_m_per_m` | `retardance`, `overland_length_km`, `overland_slope_m_per_m`, `channel_length_km`, `channel_slope_m_per_m` |

- **FAA and Kerby are formulas for overland flow time** (FAA 1966, 2013; Kerby 1959). Kerby derived his formula for flow paths up to 366 m (1200 ft; Roussel et al. 2005; TxDOT Hydraulic Design Manual, ch. 4, section 11), and the library warns for FAA outside 0.015–3 km. The channel length and slope therefore gave a result outside the range of the formula for every catchment with a channel. Since v1.0.0 FAA and Kerby take only `overland_length_km` and `overland_slope_m_per_m` and require them: missing fields are an `InvalidParameterError` (`details.missing`), with no silent substitution of the channel. The result is the overland flow time; **the tc of a catchment with a channel is given by the composite Kerby-Kirpich method**, and FAA and Kerby make sense as a catchment Tc only for small catchments without a distinct channel.
- **NRCS**: in the TR-55 lag equation (ch. 3; NEH Part 630, ch. 15) Y is the mean terrain slope of the catchment [%], not the slope of the flow path, so `mean_slope_m_per_m` takes precedence over the channel slope (before v1.0.0 it was the other way round).

Example (catchment: L = 12 km, channel 10 km with slope 0.02, terrain slope 0.025, CN 72, overland flow 0.2 km with slope 0.01, C = 0.5, N = 0.4):

| Method | tc before v1.0.0 [min] | tc since v1.0.0 [min] | Reason |
|--------|-----------------------:|----------------------:|--------|
| FAA | 155.3 (warning: L = 10 km outside 0.015–3 km) | 27.7 | overland flow 0.2 km, S = 0.01 |
| Kerby | 173.2 (two warnings) | 32.8 | as FAA |
| NRCS | 463.9 | 414.9 | Y = 2.5% (terrain) instead of 2.0% (channel) |
| Kirpich | 105.7 | 105.7 | unchanged |
| Kerby-Kirpich | 138.5 | 138.5 | unchanged |

#### 3.7.1 `cn` Alongside a Catchment in `hydrograph generate` and `report generate`

The `cn` option given alongside a catchment is the CN of the whole calculation: it overrides the catchment's `cn` both in SCS-CN and in the time of concentration by the `nrcs` method, in which the retention S = 25400/CN − 254 (TR-55, ch. 3) comes from the same CN. A catchment without `cn` also works when `cn` is given. Formerly the NRCS time of concentration took CN from the file and the effective precipitation took CN from the option. Example (CN 60 in the file, `cn` = 85, L = 12 km, Y = 2.5%, beta rainfall 50 mm/120 min): tc 657.7 → 322.1 min, Qmax 27.64 → 55.62 m³/s, time to peak 440 → 240 min.

### 3.8 Rating Curve Q = a·(H − H₀)^b: the H₀ Starting Point (`RatingCurve`, fix in v1.0.0)

`RatingCurve.fit()` (`hydrometrics rating-curve`) fits `Q = a·(H − H₀)^b` by least squares (`scipy.optimize.curve_fit`, bounds a ≥ 0, b ≥ 0, H₀ < min(H)) with the starting point a = 1, b = 1.5, H₀ = `h0_initial`. Without `h0_initial` the H₀ start lies below the lowest stage by one tenth of the stage range, by at least one stage unit:

```
H₀,start = min(H) − max(1, 0.1·(max(H) − min(H)))
```

Such a start is admissible for any sign of the stages (stages below the gauge zero, e.g. −10 cm, are normal). An explicitly supplied value must be finite and lower than the lowest stage (`validation_error`).

> **Change in v1.0.0 (bug fix).** A fixed start of 0 was not lower than the lowest stage of a gauge with a reading ≤ 0, so `hydrolog hydrometrics rating-curve --water-levels=-10,5,20,40,80,120 --discharges 0.5,1.2,2.5,4.8,10.1,17.3` ended with an error ("h0_initial must be … below the lowest water level (−10), got 0.0"). Since v1.0.0 the start is −23 and the fit gives a = 0.004917, b = 1.640, H₀ = −25.17 (R² = 0.9998). On 60 synthetic curves (stages in cm and m, positive and negative, noise 1–8 %, 6–30 measurements) starts from 0.1 to 1 of the range below the lowest stage always gave the best least-squares solution.

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

**Hydraulics and reference.** `c` and `T` are given, or follow from a prismatic section (`TrapezoidalSection`: rectangle, trapezoid, triangle) and Manning's equation at the reference discharge: `c = dQ/dA` (HEC-HMS), which is NRCS `c = m Q / A` with the local slope of the rating instead of the weighted log-log slope `m` of the whole table (2 % lower for example 17-4). The reference is the inflow peak, or `reference_discharge_m3s` (EM 1110-2-1417: base flow plus half of the rise). WinTR-20 takes the peak at the upstream end of each distance step; here every step has the reference of the reach (HEC-HMS), which is the same for one step and keeps the scheme linear and independent of the extension of the series.

**Rules of NEH-630.** (1) The hydrograph must rise from 5 % of its peak to the peak in at least 10 time steps (`rise_steps`); otherwise each step is divided into `ceil(10 / steps)` sub-steps, the inflow interpolated linearly and the outflow read at the original ordinates (notice `timestep_refined`; the balance has a sampling error). (2) Accuracy: with `Cg = c dt / dx` and `Dg = 1 - 2X` the routing is within the limits when `Dg <= exp(2.3 Cg)` (appendix B). Every grid inside the window above meets it: for `Dg <= 1` the limit is at least 1 and holds at once; for `Dg > 1` the window `|Cg - Dg| <= 1` gives `Cg >= Dg - 1`, and `exp(2.3 (Dg - 1)) >= 1 + 2.3 (Dg - 1) >= Dg` (checked on 73,804 random grids as well, the closest margin is 0.0017). A grid beyond the limit is therefore one that the planner replaced: it keeps the NRCS number of steps when the window allows it, otherwise takes the largest number of steps inside the window (`subreaches_adjusted`), or divides the time step further (`substeps_added`), and reports the grid of the NRCS rule when it was beyond the limit (`accuracy_limit`, ADR-0008). If no division of the reach into 1 to 100 sub-steps has a window (a short, flat reach: the weights are negative) the reach is refused (`validation_error`, `details.reason` `unstable_timestep`, `details.option` `times_min`), and NEH-630 advises storage routing (`route level-pool`).

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

---

## 4. Literature Verification

### 4.1 Table of Sources for Each Computation Path

| Computation path | Source | Status |
|------------------|--------|:------:|
| SCS UH + Kirpich → Tc | USDA TR-55 (1986), Kirpich (1940) | ✅ |
| SCS UH + NRCS → Tc | USDA TR-55 (1986) | ✅ |
| SCS UH + Giandotti → Tc | Giandotti (1934), TR-55 | ✅ |
| SCS UH + FAA → Tc | FAA AC 150/5320-5D (2013), TR-55 | ✅ (small catchments without a channel) |
| SCS UH + Kerby → Tc | Kerby (1959), TR-55 | ✅ (small catchments without a channel) |
| Clark IUH + FAA → Tc | FAA AC 150/5320-5D (2013), Clark (1945) | ✅ (small catchments without a channel) |
| Clark IUH + Kerby → Tc | Kerby (1959), Clark (1945) | ✅ (small catchments without a channel) |
| SCS UH + Kerby-Kirpich → Tc | Roussel et al. (2005), TR-55 | ✅ |
| Clark IUH + Kerby-Kirpich → Tc | Roussel et al. (2005), Clark (1945) | ✅ |
| Nash IUH + from_lutz() | Lutz (1984), KZGW (2017) | ✅ |
| Nash IUH + from_urban_regression() | Rao, Delleur, Sarma (1972), Banasik (2009) | ✅ |
| Nash IUH + directly n, K | Nash (1957) | ✅ |
| Nash IUH + from_tc() | **NO JUSTIFICATION** | ⚠️ |
| Clark IUH + Tc (any method) | Clark (1945), HEC-HMS | ✅ |
| Clark IUH + R/Tc ratio | HEC-HMS, engineering practice | ✅ |
| Snyder UH + L, Lc, Ct, Cp | Snyder (1938) | ✅ |
| Snyder UH in `HydrographGenerator` (D = time step: tLR, tpR, qpR) | Snyder (1938), HEC-HMS Technical Reference Manual, Chow, Maidment, Mays (1988) | ✅ |
| NRCS from a catchment (Y = mean terrain slope of the catchment) | TR-55 (1986) ch. 3, NEH Part 630 ch. 15 (2010) | ✅ |
| FAA, Kerby from a catchment (overland flow time from `overland_*`) | FAA AC 150/5320-5A/5D, Kerby (1959), Roussel et al. (2005), TxDOT Hydraulic Design Manual ch. 4 section 11 | ✅ |
| D-minute Clark UH (S-curve, any D > 0) | Clark (1945), S-curve method (e.g. Chow, Maidment, Mays 1988) | ✅ |
| HSG from USDA texture (class mapping) | USDA Soil Survey Manual (Handbook 18), NEH Part 630 ch. 7 (TR-55), Kartograf ADR-025 | ✅ (with a deviation for 3 classes) |
| Distribution of annual minima (GEV for minima) | Fisher and Tippett (1928), Gumbel (1958), Coles (2001) | ✅ |
| Annual extremes from a daily series: complete hydrological years only | KZGW (2017), WMO No. 1029 (2009) | ✅ |
| Empirical frequency of minima (non-exceedance positions) | Weibull (1939), Hazen (1930), Cunnane (1978); WMO No. 1029 (2009), Tallaksen and van Lanen (2004) | ✅ |
| Lag routing (`route lag`, `LagReach`) | HEC-HMS Technical Reference Manual (Lag routing model) | ✅ |
| Muskingum routing with sub-reaches (`route muskingum`, `MuskingumReach`) | McCarthy (1938), Chow, Maidment, Mays (1988), HEC-HMS Technical Reference Manual (Muskingum model), University of Iowa Lesson 27 (worked example) | ✅ |
| Muskingum-Cunge, constant coefficients (`route muskingum-cunge`, `MuskingumCungeReach`) | Cunge (1969), NRCS NEH Part 630 ch. 17 (2014) eq. 17-20 to 17-22, example 17-4 and appendix B, HEC-HMS Technical Reference Manual (Muskingum-Cunge model) | ✅ |
| Cascade of linear reservoirs, exact kernel (`route cascade`, `CascadeReach`) | Nash (1957) (the IUH of `NashIUH`), Kalinin and Milyukov (1957) as presented by Ponce (linear reservoirs and numerical diffusion), Chow, Maidment, Mays (1988); weights checked against the numerical integral of the gamma density and the exact solution of the chain | ✅ |
| Level-pool routing, storage indication (`route level-pool`, `LevelPoolReach`) | NRCS NEH Part 630 ch. 17 (2014) eq. 17-3 and example 17-1, HEC-HMS Technical Reference Manual (Modified Puls model); the step rule per segment checked on random tables and against the exact solution of a tank with a weir | ✅ |

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
| FAA | 2013 | Tc formula for overland flow (AC 150/5320-5D) |
| Kerby, W.S. | 1959 | Tc formula for sheet flow (retardance coefficient) |
| Giandotti, M. | 1934 | Tc formula for Italian catchments |
| Roussel, M.C. et al. | 2005 | Composite Kerby-Kirpich method (TxDOT 0-4696-2) |
| Rao, Delleur, Sarma | 1972 | Regression of Nash parameters for urbanised catchments |
| Lutz, W. | 1984 | Estimation of Nash parameters from physiographic characteristics |
| USDA TR-55 | 1986 | SCS-CN method, the relation tlag = 0.6×Tc |
| KZGW | 2017 | Polish methodology, f(N) table for Lutz |
| Fisher, R.A. and Tippett, L.H.C. | 1928 | Limiting distributions of the smallest and largest sample value |
| Gumbel, E.J. | 1958 | Statistics of extreme values (distribution for minima) |
| Coles, S. | 2001 | GEV estimation by maximum likelihood (ch. 3) |
| USDA Soil Survey Manual | 1993 | Texture triangle, texture classes |

---

## 5. Common Mistakes and How to Avoid Them

### 5.1 Mistake: Nash IUH + Kirpich without from_lutz()

```
┌─────────────────────────────────────────────────────────────────────┐
│  MISTAKE: Using ConcentrationTime.kirpich() → NashIUH.from_tc()    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  from_tc() assumes: tlag = 0.6 × Tc                                │
│  This relation is specific to the SCS method and has NO scientific │
│  justification for the Nash model.                                  │
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

9. **FAA** (2013). Airport Drainage Design. Advisory Circular AC 150/5320-5D. Federal Aviation Administration, U.S. Department of Transportation.

10. **Kerby, W.S.** (1959). Time of concentration for overland flow. *Civil Engineering*, 29(3), 174.

11. **Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., & Garcia, C.A.** (2005). Time-parameter estimation for applicable Texas watersheds. *TxDOT Research Report 0-4696-2*. Texas Department of Transportation.

12. **KZGW** (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych (Update of the methodology for computing maximum flows and precipitation; National Water Management Authority, Poland). Annex 2, Table C.2.

13. **USACE HEC-HMS** (2024). Technical Reference Manual. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/

14. **USDA-NRCS** (1986). Urban Hydrology for Small Watersheds. Technical Release 55 (TR-55).

### Textbooks

15. **Banasik, K.** (2009). Wyznaczanie wezbrań powodziowych w małych zlewniach zurbanizowanych (Determining flood waves in small urbanised catchments). *Wyd. SGGW, Warszawa*.

16. **Bedient, P.B. & Huber, W.C.** (1992). *Hydrology and Floodplain Analysis*. Addison-Wesley.

17. **Fisher, R.A. & Tippett, L.H.C.** (1928). Limiting forms of the frequency distribution of the largest or smallest member of a sample. *Proceedings of the Cambridge Philosophical Society*, 24(2), 180-190.

18. **Gumbel, E.J.** (1958). *Statistics of Extremes*. Columbia University Press, New York.

19. **Coles, S.** (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer, London.

20. **USDA** (1993). Soil Survey Manual. Handbook No. 18. Soil Survey Division Staff, USDA.

21. **USDA-NRCS** (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 7: Hydrologic Soil Groups.

22. **Chow, V.T., Maidment, D.R. & Mays, L.W.** (1988). *Applied Hydrology*. McGraw-Hill (S-curve method for unit hydrographs, synthetic hydrographs including Snyder's).

23. **USDA-NRCS** (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (lag equation: Y is the mean terrain slope of the catchment).

24. **TxDOT**. Hydraulic Design Manual, Chapter 4 Hydrology, Section 11: Time of Concentration (the 1200 ft = 366 m limit for the Kerby formula; the Kerby-Kirpich method).

### Flood Routing

25. **McCarthy, G.T.** (1938). The unit hydrograph and flood routing. Unpublished manuscript presented at the conference of the North Atlantic Division, U.S. Army Corps of Engineers, New London, Connecticut, 24 June 1938.

26. **University of Iowa**. Lesson 27: Hydrologic Routing, Muskingum Method (course handout EX-L27-Muskingum-soln). https://user.engineering.uiowa.edu/~flood/handouts/EX-L27-Muskingum-soln.pdf

27. **Cunge, J.A.** (1969). On the subject of a flood propagation computation method (Muskingum method). *Journal of Hydraulic Research*, 7(2), 205-230.

28. **USDA-NRCS** (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (Amendment 69): example 17-4, appendices B and C. https://damtoolbox.org/images/a/a6/NEH17.pdf

29. **Kalinin, G.P. and Milyukov, P.I.** (1957). O raschete neustanovivshegosya dvizheniya vody v otkrytykh ruslakh (On the computation of unsteady flow in open channels). *Meteorologiya i Gidrologiya*, 10, 10-18 (Leningrad); cited after Szilagyi, J. et al. (2005), *Journal of Hydrology*, 311, 219-229.

30. **Ponce, V.M.** (1980, online version 2016). Linear reservoirs and numerical diffusion. https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html (the gamma response of Nash, the SSARR equation as Muskingum with `X = 0`, the Kalinin-Milyukov characteristic reach length).

---

**Document version:** 1.3
**Last updated:** 2026-10-19
