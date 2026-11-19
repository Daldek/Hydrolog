# Formulas of Hydrolog

<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); do not edit. -->

## Tier A

| Formula | Function | Status | Version | Mutation score |
|---|---|---|---|---|
| [Potential maximum retention S of the SCS curve number](#scs_cn_retention) | `hydrolog.runoff.scs_cn.potential_retention` | referenced | 1 | not measured |
| [Direct runoff of a storm by the SCS curve number](#scs_cn_runoff) | `hydrolog.runoff.scs_cn.runoff_depths` | referenced | 1 | not measured |
| [Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)](#scs_cn_amc) | `hydrolog.runoff.scs_cn.amc_curve_number` | referenced | 1 | not measured |
| [Curve number of a soil-cover complex from the TR-55 tables](#tr55_cn) | `hydrolog.runoff.cn_lookup.table_curve_number` | referenced | 1 | not measured |
| [Time of concentration by Kirpich's formula (Tennessee form)](#kirpich) | `hydrolog.time.concentration.ConcentrationTime.kirpich` | referenced | 1 | not measured |
| [Time of concentration by the NRCS watershed lag equation (Mockus 1961)](#nrcs) | `hydrolog.time.concentration.ConcentrationTime.nrcs` | referenced | 1 | not measured |
| [Time of concentration by Giandotti's formula (1934)](#giandotti) | `hydrolog.time.concentration.ConcentrationTime.giandotti` | referenced | 1 | not measured |
| [Overland flow time by the FAA formula (AC 150/5320-5B, 1970)](#faa) | `hydrolog.time.concentration.ConcentrationTime.faa` | referenced | 1 | not measured |
| [Overland flow time by Kerby's formula (1959)](#kerby) | `hydrolog.time.concentration.ConcentrationTime.kerby` | referenced | 1 | not measured |
| [Time of concentration by the Kerby-Kirpich method (Roussel et al. 2005)](#kerby_kirpich) | `hydrolog.time.concentration.ConcentrationTime.kerby_kirpich` | referenced | 1 | not measured |
| [Equal-area slope of a longitudinal profile (the line through the outlet with equal areas above and below it)](#equal_area_slope) | `hydrolog.morphometry.profile.equal_area_slope` | oracle only | 1 | not measured |
| [Nash's n and K of an ungauged watershed by Lutz's method (KZGW 2017)](#lutz) | `hydrolog.runoff.nash_iuh.lutz_parameters` | referenced | 1 | not measured |
| [SCS (NRCS) dimensionless unit hydrograph of a unit duration](#scs) | `hydrolog.runoff.unit_hydrograph.scs_unit_hydrograph` | referenced | 1 | not measured |
| [Snyder's synthetic unit hydrograph: lag, peak, time base and widths](#snyder) | `hydrolog.runoff.snyder_uh.snyder_parameters` | referenced | 1 | not measured |
| [Snyder's unit hydrograph as the gamma curve of 1 mm through its peak](#snyder_shape) | `hydrolog.runoff.snyder_uh.snyder_shape` | oracle only | 1 | not measured |
| [Clark's unit hydrograph of a duration: time-area curve and linear reservoir](#clark) | `hydrolog.runoff.clark_iuh.clark_unit_hydrograph` | oracle only | 1 | not measured |
| [Direct runoff of excess rainfall by discrete convolution with a unit hydrograph](#uh_convolution) | `hydrolog.runoff.convolution.convolve_discrete` | referenced | 1 | not measured |
| [Horton's form factor of a watershed](#form_factor) | `hydrolog.morphometry.geometric.form_factor` | oracle only | 1 | not measured |
| [Gravelius's compactness coefficient of a watershed](#compactness_coefficient) | `hydrolog.morphometry.geometric.compactness_coefficient` | oracle only | 1 | not measured |
| [Miller's circularity ratio of a watershed](#circularity_ratio) | `hydrolog.morphometry.geometric.circularity_ratio` | oracle only | 1 | not measured |
| [Schumm's elongation ratio of a watershed](#elongation_ratio) | `hydrolog.morphometry.geometric.elongation_ratio` | oracle only | 1 | not measured |
| [Chorley's lemniscate ratio k of a watershed](#lemniscate_ratio) | `hydrolog.morphometry.geometric.lemniscate_ratio` | oracle only | 1 | not measured |
| [Relief ratio: the relief of a watershed over a length (Schumm)](#relief_ratio) | `hydrolog.morphometry.terrain.relief_ratio` | referenced | 1 | not measured |
| [Hypsometric integral of a watershed by the trapezoid of its curve (Strahler)](#hypsometric_integral) | `hydrolog.morphometry.hypsometry.hypsometric_integral` | oracle only | 1 | not measured |
| [Strahler's order of a stream below a junction](#strahler_order) | `hydrolog.network.stream_order.strahler_order` | referenced | 1 | not measured |
| [Horton's bifurcation ratio of the streams of two consecutive orders](#bifurcation_ratio) | `hydrolog.network.stream_order.bifurcation_ratio` | oracle only | 1 | not measured |
| [Horton's length ratio of the streams of two consecutive orders](#length_ratio) | `hydrolog.network.stream_order.length_ratio` | oracle only | 1 | not measured |
| [Drainage density: the length of the streams over the watershed's area](#drainage_density) | `hydrolog.network.stream_order.drainage_density` | oracle only | 1 | not measured |
| [Stream frequency: the number of streams over the watershed's area](#stream_frequency) | `hydrolog.network.stream_order.stream_frequency` | oracle only | 1 | not measured |
| [USDA soil texture class of clay, sand and silt amounts](#usda_texture) | `hydrolog.soil.texture.classify_usda_texture` | referenced | 1 | not measured |
| [Hydrologic soil group of a USDA texture class](#texture_hsg) | `hydrolog.soil.texture.texture_to_hsg` | referenced | 1 | not measured |

<a id="scs_cn_retention"></a>
### Potential maximum retention S of the SCS curve number

`hydrolog.runoff.scs_cn.potential_retention` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
S = 25.4\left(\frac{1000}{CN} - 10\right)
$$

Plain text: `S = 25.4 * (1000 / CN - 10) [mm]`

**Sources**

- USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-12, p. 10-4 (S = 1000/CN - 10, in); eq. 10-13 (the same in mm) (open) <https://www.hydrocad.net/neh/630ch10.pdf>
- USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), eq. 2-4, p. 2-1 (open) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.1, p. 88 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `cn` | $CN$ | - | real | [1.0, 100.0] | unstated | [30.0, 98.0]: Hydrolog's table of TR-55 curve numbers (cn list), the CN its users take for soil-cover complexes, its least and largest CN, 30 (woods and brush, good, A) and 98 (impervious and water) |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `s_scale` | $1000$ | 1000.0 | in | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-12, p. 10-4 |
| `s_offset` | $10$ | 10.0 | in | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-12, p. 10-4 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `retention_mm` | mm | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- S in mm from the inch form of NEH 630-10 eq. 10-12 by the exact 25.4 mm/in of the units table, which is eq. 10-13 (S = 25400/CN - 254)
- the CN of the antecedent runoff condition of the computation: ARC (AMC) II unless converted by scs_cn_amc

**Assumptions**

None stated.

**Validation:** none: S is the definition of the curve number (NEH 630-10, eq. 10-12)

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range case cn-physical_low: CN = 1 gives S = 25,146 mm, finite; a CN below 1 is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `cn` decreasing
- limit `no_retention`: CN = 100 gives S = 0
- limit `exact_rational`: S equals 25.4 (1000/CN - 10) mm in exact rational arithmetic for whole CN

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/scs-cn-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: S = 25.4 (1000/CN - 10) in exact rational arithmetic (fractions) for whole CN (`tests/unit/test_formulas_scs_cn.py (limit exact_rational)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="scs_cn_runoff"></a>
### Direct runoff of a storm by the SCS curve number

`hydrolog.runoff.scs_cn.runoff_depths` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q(P) = \begin{cases} \dfrac{(P - I_a)^2}{P - I_a + S} & P > I_a \\ 0 & P \le I_a \end{cases},\quad I_a = \lambda S,\quad q_i = Q(P_i) - Q(P_{i-1}),\quad C = \frac{Q}{P}
$$

Plain text: `Q(P) = (P - Ia)**2 / (P - Ia + S) for P > Ia, else 0; Ia = lambda * S; S of scs_cn_retention; P the cumulative depth after each step, the runoff of a step the difference of Q; C = Q / P of the storm`

**Sources**

- USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eqs. 10-9 to 10-11, pp. 10-2 to 10-4; example 10-6 and table 10-2, pp. 10-17 to 10-18 (cumulative rainfall of a storm) (open) <https://www.hydrocad.net/neh/630ch10.pdf>
- USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), eqs. 2-1 to 2-4, p. 2-1 (open) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.2, p. 88 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $\Delta P_i$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 350.0]: Hydrolog's test fixtures: the PMAXTP depths of IMGW-PIB for Kamiennik (51.015 N, 15.890 E) and Warsaw (52.23 N, 21.01 E), POT, recorded in November 2026, tests/fixtures/pmaxtp_kamiennik_pot.json and pmaxtp_warszawa_pot.json: 6.96 to 341.27 mm over durations of 5 min to 72 h and probabilities of 0.01 to 99.9 % |
| `cn` | $CN$ | - | real | [1.0, 100.0] | [40.0, 100.0]: USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), chapter 2, limitations, p. 2-11: when the weighted CN is less than 40, use another procedure | [30.0, 98.0]: Hydrolog's table of TR-55 curve numbers (cn list), the CN its users take for soil-cover complexes, its least and largest CN, 30 (woods and brush, good, A) and 98 (impervious and water) |
| `ia_coefficient` | $\lambda$ | - | real | (0.0, 1.0] | unstated | [0.05, 0.2]: Hydrolog's command scs effective: the ratio 0.2 of the CN tables and 0.05 of Woodward et al. (2003), the two its catalog and GUI name, catalog option ia_coefficient |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `total_effective_mm` | mm | real | [0.0, inf) | 4 ulp of the bound |
| `effective_mm` | mm | real_array | [0.0, inf) | 1e-09 |
| `runoff_coefficient` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `retention_mm` | mm | real | [0.0, inf) | 4 ulp of the bound |
| `initial_abstraction_mm` | mm | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: depths in mm
- the equation on the cumulative rainfall of the storm, the runoff of each step the difference of the cumulative runoff (NEH 630-10 example 10-6; KZGW 2017 eq. 6.2); a total is a storm of one step
- Ia = lambda S with lambda given; S from the CN by scs_cn_retention
- the CN of ARC (AMC) II unless converted by scs_cn_amc
- C = Q / P of the storm, 0 without rainfall

**Assumptions**

- the CN of the NRCS tables assume lambda = 0.2; another lambda needs CN fitted for it (NEH 630-10 p. 10-4; Woodward et al. 2003), and the command scs effective then gives the notice ia_coefficient_nonstandard
- direct runoff of one storm, not an infiltration model or a continuous simulation (NEH 630-10 p. 10-19); not for snowmelt or rain on frozen ground (TR-55 p. 2-11)
- TR-55 (p. 2-11) finds the method less accurate for runoff below 0.5 in (12.7 mm); this limit of the output gives no notice

**Validation:** NEH 630-9 (p. 9-1) derives the curve numbers of its tables from annual floods of small agricultural watersheds, generally under 1 square mile, and storms of one day or less; the sources give no error statistic of the equation

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `difference_denominator`: limit cn_100: P - Ia + S is P itself at CN 100 and a step of no rainfall gives no runoff
- `gap_propagation`: type case precipitation_mm-nan_element: a gap is refused before the cumulative sum
- `many_small_terms`: test_a_long_storm_matches_its_total_summed_exactly

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `precipitation_mm` increasing, `cn` increasing, `ia_coefficient` decreasing
- limit `no_runoff_below_ia`: no runoff while the rainfall does not exceed Ia (NEH 630-10, eq. 10-9)
- limit `cn_100`: CN = 100 gives S = Ia = 0 and the rainfall of every step as runoff
- limit `ultimate_loss`: P - Q tends to S + Ia as P grows (NEH 630-10, eq. 10-16)
- limit `exact_rational`: Q equals the equation in exact rational arithmetic
- conservation `steps_add_up`: the runoff of the steps adds up to the runoff of the storm

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/scs-cn-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: Q in exact rational arithmetic (fractions) (`tests/unit/test_formulas_scs_cn.py (limit exact_rational)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="scs_cn_amc"></a>
### Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)

`hydrolog.runoff.scs_cn.amc_curve_number` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
CN_x = \operatorname{round}\frac{CN}{k_x + (1 - k_x)\,CN/100},\quad k_{I} = 2.281,\ k_{III} = 0.427
$$

Plain text: `CN_x = CN / (k_x + (1 - k_x) * CN / 100), k_I = 2.281, k_III = 0.427 (S_x = k_x * S_II), rounded to the nearest integer, at least 1`

**Sources**

- Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eqs. 13-16, p. 15 (S_I = 2.281 S_II, S_III = 0.427 S_II) (open) <https://www.uvm.edu/~bwemple/HydroModel/ponce1996.pdf>
- Banasik, K., Rutkowska, A. and Kohnová, S. (2014). Retention and curve number variability in a small agricultural catchment: the probabilistic approach. Water 6(5), 1118-1133, doi:10.3390/w6051118, eqs. 12-13, p. 1124 (eq. 12 misprints 0.01381 for 0.01281) (open) <https://mdpi-res.com/d_attachment/water/water-06-01118/article_deploy/water-06-01118.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `cn` | $CN$ | - | real | [1.0, 100.0] | [55.0, 95.0]: Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, p. 15: eqs. 15-16 applicable in the range 55 <= CN <= 95 | [51.8, 81.4]: Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the 223 catchments of the Hydroni run h07 (2,941 km2), Consequences: CN of AMC II 51.8 to 81.4, median 70.8 |
| `amc` | $ARC$ | - | choice of I, III | – | – | – |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `ratio_i` | $k_{I}$ | 2.281 | - | Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eq. 13, p. 15 (r2 = 0.999); Banasik et al. (2014) eq. 12 |
| `ratio_iii` | $k_{III}$ | 0.427 | - | Ponce, V.M. and Hawkins, R.H. (1996). Runoff curve number: has it reached maturity? Journal of Hydrologic Engineering 1(1), 11-19, reporting Hawkins, R.H., Hjelmfelt, A.T. and Zevenbergen, A.W. (1985), Journal of Irrigation and Drainage Engineering 111(4), 330-340, eq. 14, p. 15 (r2 = 0.994); Banasik et al. (2014) eq. 13 |
| `cn_scale` | $100$ | 100.0 | - | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10: Estimation of Direct Runoff from Storm Rainfall (210-VI-NEH, July 2004), eq. 10-11, p. 10-4: CN = 1000/(10 + S), 100 at S = 0 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `cn_adjusted` | - | integer | [1.0, 100.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the fit of Hawkins et al. (1985) to the curves of NRCS, not NEH 630-10 table 10-1 itself (NEH 630-10 p. 10-6; it gives the table) nor Chow et al. (1988) eqs. 5.5.7-5.5.8, another fit
- rounded to the nearest integer as table 10-1 prints them, a half to the even integer; at least 1
- ARC II is the CN as given: no formula

**Assumptions**

- NEH 630-10 (pp. 10-5, 10-7) found no relation between the rainfall of the five preceding days and the CN: the condition is chosen by the engineer

**Validation:** Ponce and Hawkins (1996, p. 15) report the fits S_I = 2.281 S_II (r2 0.999, standard error 0.206 in) and S_III = 0.427 S_II (r2 0.994, 0.088 in) to NEH table 10-1, and standard errors of 1.0 CN (eq. 15) and 0.7 CN (eq. 16); against that table at CN 55 to 95 the rounded conversion differs by up to 2 CN for ARC I and 1 CN for ARC III (unrounded at most 2.45 CN for ARC I at CN 92 and 1.19 CN for ARC III at CN 79)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

None applies: the denominators k + (1 - k) CN / 100 lie between 0.43 and 2.28 for CN of 1 to 100; no logarithm, root or exponential

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `cn` increasing
- limit `no_retention`: CN 100 stays 100 in either condition (S = 0)
- limit `ratio_of_retention`: the converted CN is the CN of k_x S_II, rounded, in exact rational arithmetic

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/scs-cn-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the CN of S_x = k_x S_II in exact rational arithmetic (fractions), rounded (`tests/unit/test_formulas_scs_cn.py (limit ratio_of_retention)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5).

<a id="tr55_cn"></a>
### Curve number of a soil-cover complex from the TR-55 tables

`hydrolog.runoff.cn_lookup.table_curve_number` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
CN = T(\text{cover}, \text{condition}, \text{HSG})
$$

Plain text: `CN = T(land cover, condition, hydrologic soil group), T the TR-55 table`

**Sources**

- USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, p. 2-8 (open) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
- USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 9: Hydrologic Soil-Cover Complexes, p. 9-1: impervious and water surfaces are always assigned a CN of 98 (open) <https://www.hydrocad.net/neh/630ch9.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `hsg` | $\text{HSG}$ | - | choice of A, B, C, D | – | – | – |
| `land_cover` | $\text{cover}$ | - | choice of fallow, row_crops, small_grain, pasture, meadow, brush, forest, herbaceous, woods_grass, farmstead, residential_low, residential_medium, residential_quarter_acre, residential_high, commercial, industrial, open_space, paved, paved_road_open_ditches, gravel, dirt, water | – | – | – |
| `condition` | $\text{condition}$ | - | choice of poor, fair, good, none | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `row_in_table` | precondition | the table has a row of the land cover in the condition | USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, p. 2-8 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `cn` | - | integer | [1.0, 100.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- ARC (AMC) II and Ia = 0.2 S (TR-55 tables 2-2a to 2-2c, footnote 1)
- herbaceous is the pasture, grassland or range row of table 2-2c, as footnote 1 of table 2-2d directs for range in humid regions; table 2-2d itself (arid and semiarid rangelands) is not used
- row crops and small grain are the straight-row rows of table 2-2b, poor and good only: TR-55 has no fair condition for them
- water is CN 98 (NEH 630-9 p. 9-1), not the 100 of some texts

**Assumptions**

None stated.

**Validation:** NEH 630-9 (p. 9-1) derives the CN of its complexes from annual floods of small agricultural watersheds of one soil group and one cover; the table gives no error statistic

**Notices:** none

**Numerical traps (CMP-6.6)**

None applies: a lookup of categorical keys: no numeric class limit and no series

**Properties (CMP-6.5)**

- units: unit_specific
- limit `groups_in_order`: CN does not fall from group A to D in any row

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/cn-table-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tables (CMP-2.5)**

- `src/hydrolog/_data/tables/tr55_cn.csv` sha256 `781fdd02b39aa868571ec09cb92516716a79c0d74a77640fe810e794cfd3a6e8`: USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, p. 2-8; transcriptions compared in `tests/oracles/tr55_cn_text_layer.csv (transcribed from the PDF's text layer by tests/oracles/transcribe_tr55_cn.py) against tests/oracles/tr55_cn_hydrolog_0_8_1.csv (typed for Hydrolog 0.8.1), compared by tests/unit/test_formulas_cn_table.py`

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5).

<a id="kirpich"></a>
### Time of concentration by Kirpich's formula (Tennessee form)

`hydrolog.time.concentration.ConcentrationTime.kirpich` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_c = 0.0078\,L^{0.77}\,S^{-0.385},\quad L\ \mathrm{[ft]}
$$

Plain text: `tc = 0.0078 * L**0.77 * S**-0.385 [min], L in ft (L[km] by the exact foot), S in m/m`

**Sources**

- Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22 (L the channel length to the most remote point, S its drop over L) (open) <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
- Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, eq. 7, p. 7; supplement, p. 29 (K = 0.0078 for feet) (open) <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
- Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, pp. 56-58: Kirpich's curves and data of 1940, table 1; the formula published by Rowe and Thomas (1942) (open) <https://revistas.abrhidro.org.br/article.php?Article=5027>
- Florida Department of Transportation (2024). Drainage Design Guide, chapter 2, eq. 2.2-9 (open) <https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/roadway/drainage/files/drainagedesignguide/chapter2.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | [0.10668, 1.2192]: Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, p. 58: the data of Kirpich (1940), table 1, give the range of the formula, L between 350 and 4,000 ft | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km |
| `slope_m_per_m` | $S$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | [0.025, 0.1]: Mota, A.A. and Kobiyama, M. (2015). Reconsiderações sobre a fórmula de Kirpich para o cálculo de tempo de concentração. Revista Brasileira de Recursos Hídricos 20(1), 55-59, p. 58: the data of Kirpich (1940), table 1, give the range of the formula, S from 0.025 to 0.1 | [0.002, 0.11]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow path slopes of 0.00244 to 0.1055 m/m |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `kirpich_coefficient` | $0.0078$ | 0.0078 | min ft^-0.77 | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; the same in Roussel et al. (2005) eq. 7, Mota and Kobiyama (2015) and FDOT (2024) eq. 2.2-9 |
| `kirpich_length_exponent` | $0.77$ | 0.77 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) |
| `kirpich_slope_exponent` | $-0.385$ | -0.385 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the Tennessee form in its source units: L in feet by the exact 0.3048 m/ft of the units table, tc in minutes; the SI constants 0.0195 (L in m; Roussel et al. 2005, TxDOT 2019) and 0.01947 (WR-D-71-1, 2023) round 0.0078 (1/0.3048)^0.77 = 0.019472, and Hydrolog's 3.981 (L in km) up to 0.8.1 was 0.136 % above the exact 3.97560
- L along the watercourse from the outlet to the most remote point of the watershed, the longest flow path, and S the drop between its two ends over L (Fang et al. 2005, eq. 3.14), neither the channel to its head nor the mean slope of the watershed; Kirpich (1940) measured L to the highest point of the basin (Mota and Kobiyama 2015, p. 56)
- S in m/m (ft/ft), not in percent
- no low-slope offset in the formula alone; Kerby-Kirpich offsets its channel part (Cleveland et al. 2012)

**Assumptions**

- small rural basins with defined channels, 1.25-112 acres (0.005-0.45 km2, checked by WatershedParameters.calculate_tc), so mostly channel flow; Kirpich applied it up to about 200 acres (Roussel et al. 2005, p. 5); the factors 0.4 for overland flow on concrete or asphalt and 0.2 for concrete channels of US practice (Fang et al. 2005, p. 22) are not applied
- Hydrograf's watersheds (flow paths of 0.05-30 km) lie mostly outside Kirpich's data (0.107-1.22 km): their results are extrapolations, with the notice

**Validation:** Kirpich (1940) published curves of six basins of Ramser (1927) near Jackson, Tennessee (basin 2 of seven excluded), not the formula; Mota and Kobiyama (2015, pp. 57-58) find their own fit to those data 2 to 9 % from the formula within L of 350-4,000 ft and S of 0.025-0.1, up to 30 % outside

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases slope_m_per_m-physical_low_*: tc grows without bound as S tends to 0 (S^-0.385) and stays finite down to the smallest positive float; a slope of 0 is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `slope_m_per_m` decreasing
- limit `source_units`: tc equals the SI form 0.0078 (1/0.3048)^0.77 L[m]^0.77 S^-0.385 evaluated in decimal arithmetic at 50 digits
- limit `power_law`: doubling L multiplies tc by 2^0.77, doubling S by 2^-0.385

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the SI form with the unrounded constant 0.0078 (1/0.3048)^0.77, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit source_units)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="nrcs"></a>
### Time of concentration by the NRCS watershed lag equation (Mockus 1961)

`hydrolog.time.concentration.ConcentrationTime.nrcs` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
T_c = \frac{\ell^{0.8}\,(S + 1)^{0.7}}{1140\,Y^{0.5}},\quad S = \frac{1000}{CN} - 10,\quad \ell\ \mathrm{[ft]},\ S\ \mathrm{[in]},\ Y\ [\%]
$$

Plain text: `tc = l**0.8 * (S + 1)**0.7 / (1140 * Y**0.5) [h], l in ft, S = 1000 / CN - 10 in, Y = 100 * slope in percent; the lag is 0.6 tc`

**Sources**

- USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-3, 15-4a and 15-4b and their variables, pp. 15-3 to 15-6; the example of the lag method, p. 15-12 (open) <https://directives.nrcs.usda.gov/sites/default/files2/1712930617/14081.pdf>
- USDA-NRCS (2025). 210 NEH Part 630 Hydrology, Subpart F: Time of Concentration (amended June 2025), eqs. 630.15-3, 630.15-4a and 630.15-4b, the same equations and limits (open) <https://directives.nrcs.usda.gov/sites/default/files2/1749749287/Subpart%20F%20%E2%80%93%20Time%20of%20Concentration.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `length_km` | $\ell$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km |
| `slope_m_per_m` | $Y$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | unstated | [0.04, 0.19]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: mean land slopes of 0.0500 to 0.1831 m/m |
| `cn` | $CN$ | - | real | [1.0, 100.0] | [50.0, 95.0]: USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), p. 15-6: a CN of less than 50, or greater than 95 should not be used in the solution of equations 15-4a and 15-4b (Mockus 1961) | [51.8, 81.4]: Hydrograf ADR-0075 (2026-11-08), the CN of soil-cover complexes of the 223 catchments of the Hydroni run h07 (2,941 km2), Consequences: CN of AMC II 51.8 to 81.4, median 70.8 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `tc_denominator` | $1140$ | 1140.0 | ft^0.8 in^0.7 h^-1 %^0.5 | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eq. 15-4b, p. 15-5: eq. 15-4a (1,900) with L = 0.6 Tc |
| `length_exponent` | $0.8$ | 0.8 | - | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-4a and 15-4b, p. 15-5 |
| `retention_exponent` | $0.7$ | 0.7 | - | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-4a and 15-4b, p. 15-5 |
| `retention_shift` | $1$ | 1.0 | in | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), eqs. 15-4a and 15-4b, p. 15-5: S + 1 |
| `s_scale` | $1000$ | 1000.0 | in | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), p. 15-5: S = 1,000 / cn' - 10 |
| `s_offset` | $10$ | 10.0 | in | USDA-NRCS (2010). National Engineering Handbook, Part 630 Hydrology, Chapter 15: Time of Concentration (210-VI-NEH, May 2010), p. 15-5: S = 1,000 / cn' - 10 |
| `percent` | $100$ | 100.0 | % per m/m | BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- eq. 15-4b in its source units: l in feet and S in inches by the exact 0.3048 m/ft and 25.4 mm/in of the units table, Y in percent (100 per m/m), Tc in hours, converted to minutes; in SI it is 100 l[m]^0.8 (S[mm] + 25.4)^0.7 / (7068.86 Y^0.5) with 100/7068.86 = 0.0141466, where Hydrolog up to 0.8.1 used 0.01416 (+0.095 %, TRIAGE T8)
- Tc = lag / 0.6 (eq. 15-3, Mockus 1957; Simas 1996); a unit hydrograph takes tp = D/2 + 0.6 Tc (USACE HEC-HMS Technical Reference Manual, SCS unit hydrograph, eqs. 1 and 3); TR-55 (1986) has no lag relation
- l the longest flow path from the divide to the outlet (p. 15-5); Y the average land slope of the watershed, 'not to be confused with the slope of the flow path' (p. 15-5)
- the retardance factor cn' is the CN of AMC II (p. 15-6: CN is used as a surrogate for cn'); S = 0 at CN 100; a fractional CN, a weighted mean, is used as given

**Assumptions**

- average natural watershed conditions with an approximately uniform distribution of runoff (eq. 15-3); the area of the 24 watersheds, 0.005-24 km2, is checked by WatershedParameters.calculate_tc
- Hydrograf's flow paths (0.05-30 km) and the CN of its catchments (51.8-81.4) lie inside the equation's CN range; a CN below 50 or above 95 gives the notice

**Validation:** NEH 630-15 (p. 15-6) reports the equation's data, 24 watersheds of 1.3 acres to 9.2 square miles, mostly under 2,000 acres (Mockus 1961), and that Folmar and Miller (2000) found a reasonable upper limit of up to 19 square miles; table 15-4 shows the lag of one watershed varying from storm to storm (Jones Falls, Maryland: 4.16 to 6.91 h)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases slope_m_per_m-physical_low_*: tc grows as Y^-0.5 when Y tends to 0 and stays finite down to the smallest positive float; cn-physical_low: CN = 1 gives S = 990 in, finite

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `slope_m_per_m` decreasing, `cn` decreasing
- limit `exact_metric_constant`: tc equals 100 l[m]^0.8 (S[mm] + 25.4)^0.7 / (7068.86 Y^0.5) with 7068.86 = 1900 0.3048^0.8 25.4^0.7 unrounded, in decimal arithmetic at 50 digits (TRIAGE T8)
- limit `power_law`: doubling l multiplies tc by 2^0.8, doubling Y by 2^-0.5

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the SI form with S in mm and the unrounded 1900 0.3048^0.8 25.4^0.7, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit exact_metric_constant)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="giandotti"></a>
### Time of concentration by Giandotti's formula (1934)

`hydrolog.time.concentration.ConcentrationTime.giandotti` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_c = \frac{4\sqrt{A} + 1.5\,L}{0.8\sqrt{H}}
$$

Plain text: `tc = (4 * A**0.5 + 1.5 * L) / (0.8 * H**0.5) [h]`

**Sources**

- Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto idrogeologico (PAI), Direttiva sulla piena di progetto, §6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937) (open) <https://www.adbpo.it/PAI/7%20-%20Norme%20di%20attuazione/7.2%20-%20Direttive%20di%20Piano/Direttiva2/DIRETTIVA/DIRETTIVA.PDF>
- Michailidi, E.M., Antoniadi, S., Koukouvinos, A., Bacchi, B. and Efstratiadis, A. (2018). Timing the time of concentration: shedding light on a paradox. Hydrological Sciences Journal 63(5), 721-740, doi:10.1080/02626667.2018.1450985, table 2 (the formula), table 3 (30 basins) (open) <https://www.itia.ntua.gr/en/getfile/1777/2/documents/Timing_the_time_of_concentration_shedding_light_on_a_paradox_nNWG5Fq.pdf>
- Almeida, I.K., Almeida, A.K., Anache, J.A.A., Steffen, J.L. and Alves Sobrinho, T. (2014). Estimation on time of concentration of overland flow in watersheds: a review. Geociências 33(4), 661-671, table 1, Giandotti: basins of central and northern Italy, 170-70,000 km2 (after Giandotti 1940, Preti et al. 2011, Radice et al. 2012) (open) <https://www.revistageociencias.com.br/geociencias-arquivos/33/volume33_4_files/33-4-artigo-9.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 1000000.0 (a million km2, more than ten times the largest basin of the formula's data (70,000 km2)) | [170.0, 70000.0]: Almeida, I.K., Almeida, A.K., Anache, J.A.A., Steffen, J.L. and Alves Sobrinho, T. (2014). Estimation on time of concentration of overland flow in watersheds: a review. Geociências 33(4), 661-671, table 1, Giandotti: basins of central and northern Italy, 170-70,000 km2 (after Giandotti 1940, Preti et al. 2011, Radice et al. 2012) | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | unstated | [0.007, 27.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: main channels of 0.0071 to 26.18 km |
| `elevation_diff_m` | $H$ | m | real | (0.0, inf), test bound high 8849.0 (the height of Mount Everest above sea level: no mean elevation lies higher above its outlet) | unstated | [2.5, 210.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: mean elevations of 2.89 to 204 m above the outlet |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `area_factor` | $4$ | 4.0 | h km^-1 m^0.5 | Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto idrogeologico (PAI), Direttiva sulla piena di progetto, §6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937) |
| `length_factor` | $1.5$ | 1.5 | h km^-1 m^0.5 | Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto idrogeologico (PAI), Direttiva sulla piena di progetto, §6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937) |
| `height_factor` | $0.8$ | 0.8 | - | Autorità di bacino del fiume Po (2001). Piano stralcio per l'assetto idrogeologico (PAI), Direttiva sulla piena di progetto, §6.1, p. 9: tempo di corrivazione di Giandotti (1934, 1937) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- A in km2, L in km and H in m as the sources print it, tc in hours converted to minutes
- H the mean elevation of the watershed minus the elevation of the outlet, neither the relief (maximum minus minimum) nor the mean elevation itself
- L the main channel, the field channel_length_km, after Grimaldi et al. (2012, eq. 5); the Autorità di bacino del Po (2001, §6.1: 'percorso idraulicamente più lungo') and Michailidi et al. (2018) take the longest flow path, longer by the overland segment (Kamiennik: 14.78 against 15.88 km, +3.5 % in tc)

**Assumptions**

- basins of central and northern Italy of 170-70,000 km2 (Almeida et al. 2014, table 1); Hydrograf's watersheds, up to 250 km2, lie mostly below that range: their results are extrapolations, with the notice

**Validation:** none reported by the open sources (Giandotti 1934 is not open)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases elevation_diff_m-physical_low_*: tc grows as H^-0.5 when H tends to 0 (a flat watershed) and stays finite; H = 0 is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `area_km2` increasing, `length_km` increasing, `elevation_diff_m` decreasing
- limit `decimal`: tc equals 75 (4 A^0.5 + 1.5 L) / H^0.5 minutes evaluated in decimal arithmetic at 50 digits
- limit `height`: four times H halves tc

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the formula in minutes, 75 (4 A^0.5 + 1.5 L) / H^0.5, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit decimal)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="faa"></a>
### Overland flow time by the FAA formula (AC 150/5320-5B, 1970)

`hydrolog.time.concentration.ConcentrationTime.faa` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
T = \frac{1.8\,(1.1 - C)\,\sqrt{D}}{\sqrt[3]{S}},\quad D\ \mathrm{[ft]},\ S\ [\%]
$$

Plain text: `T = 1.8 * (1.1 - C) * D**0.5 / S**(1/3) [min], D in ft, S in percent (100 * slope)`

**Sources**

- Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, chapter 3, §6, figure 7 'Surface flow time curves', p. 11; table I, p. 10 (open) <https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_150_5320-5B.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | unstated | [0.04, 0.7]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km |
| `slope_m_per_m` | $S$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | unstated | [0.005, 0.19]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m |
| `runoff_coeff` | $C$ | - | real | (0.0, 1.0] | [0.0, 0.95]: Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, table I, p. 10: the values of factor C, 0.00 to 0.95 | [0.05, 0.95]: Hydrolog's catalog: the coefficients of table I of AC 150/5320-5B, which the option runoff_coeff of tc faa quotes, without its 0.00, table I, p. 10: moderately pervious soils 0.05-0.20 to watertight roofs 0.75-0.95 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `faa_coefficient` | $1.8$ | 1.8 | min ft^-0.5 %^(1/3) | Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, figure 7, p. 11 |
| `c_offset` | $1.1$ | 1.1 | - | Federal Aviation Agency (1970). Airport Drainage. Advisory Circular AC 150/5320-5B, figure 7, p. 11 |
| `percent` | $100$ | 100.0 | % per m/m | BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- figure 7 in its source units: D in feet by the exact 0.3048 m/ft of the units table, S in percent (100 per m/m; the curves are labelled in percent), T in minutes; Hydrolog's 22.213 for L in km and S in m/m up to 0.8.1 rounded 22.2125
- the inlet time: overland flow 'from the most remote point in the drainage subarea to the inlet' (§6b), not the time of concentration of a watershed with a channel
- C of table I in (0, 1]: C = 0, which the table lists for moderately pervious soils with turf (0.00-0.10), is refused

**Assumptions**

- 'Use the formula for distances in excess of 800 feet' (figure 7): the curves end at 800 ft and the formula serves longer paths; the later circulars AC 150/5320-5C (2006) and 5D (2013) time the flow with the NRCS segment method instead

**Validation:** none reported by the source

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases slope_m_per_m-physical_low_*: T grows as S^(-1/3) when S tends to 0 and stays finite; S = 0 is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `slope_m_per_m` decreasing, `runoff_coeff` decreasing
- limit `decimal`: T equals 1.8 (1000/0.3048)^0.5 / 100^(1/3) (1.1 - C) L[km]^0.5 S[m/m]^(-1/3) evaluated in decimal arithmetic at 50 digits
- limit `runoff_coefficient`: T is proportional to 1.1 - C

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the SI form with the unrounded constant 1.8 (1000/0.3048)^0.5 / 100^(1/3), evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit decimal)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="kerby"></a>
### Overland flow time by Kerby's formula (1959)

`hydrolog.time.concentration.ConcentrationTime.kerby` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_c = \left(\frac{0.67\,N\,L}{\sqrt{S}}\right)^{0.467},\quad L\ \mathrm{[ft]},\quad S \to S + 0.0005\ \text{for}\ S < 0.002
$$

Plain text: `tc = (0.67 * N * L / S**0.5)**0.467 [min], L in ft; S + 0.0005 for S below 0.002`

**Sources**

- Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12 and table 3.3, p. 22 (open) <https://rosap.ntl.bts.gov/view/dot/88539/dot_88539_DS1.pdf>
- Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, eq. 3, p. 5; supplement, p. 29 (the form K (L N)^0.467 S^-0.235) (open) <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
- Indiana Department of Transportation. Indiana Design Manual (metric, archived), Part IV, chapter 29: Hydrology, eq. 29-7.14, Kerby's formula in SI units with K = 1.44 (open) <https://www.in.gov/dot/div/contracts/standards/dm-Archived/07%20Metric/Part%204%20Vol.%201/Ch%2029/Ch29.pdf>
- Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures and eq. 2, pp. 1-2 (open) <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | [0.0, 0.366]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: in the development of Kerby's equation the length of overland flow was as much as about 1,200 feet (366 meters), an upper limit | [0.04, 0.7]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km |
| `slope_m_per_m` | $S$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | [0.0, 0.01]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, p. 5: the watersheds of Kerby (1959) have dimensionless slopes less than 0.01 | [0.005, 0.19]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m |
| `retardance` | $N$ | - | real | (0.0, inf), test bound high 8.0 (ten times the largest N of Kerby's table (0.80)) | [0.02, 0.8]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: Kerby's table of the retardance N, pavement 0.02 to dense grass, coniferous forest or deciduous forest with deep litter 0.80 | [0.02, 0.8]: Hydrolog's catalog and GUI: Kerby's table of N (Roussel et al. 2005, supplement, p. 29), from which their users take N, option retardance of tc kerby and tc kerby-kirpich: 0.02 (pavement) to 0.80 (dense grass, coniferous forest) |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `kerby_coefficient` | $0.67$ | 0.67 | min^(1/0.467) ft^-1 | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22, (0.67 N L / S^0.5)^0.467 with L in ft; the same in Roussel et al. (2005) eq. 3 |
| `kerby_exponent` | $0.467$ | 0.467 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22; INDOT eq. 29-7.14 and TxDOT (2019) take the same exponent of L N |
| `low_slope_threshold` | $0.002$ | 0.002 | m/m | Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, step 2(c), p. 2: a main channel slope less than 0.002 is low slope; TxDOT (2019), section 11 |
| `low_slope_offset` | $0.0005$ | 0.0005 | m/m | Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, step 3 and eq. 1, p. 2: S_low slope = S0 + 0.0005; TxDOT (2019), section 11 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Kerby's form in its source units: L in feet by the exact 0.3048 m/ft of the units table, tc in minutes; the forms K (L N)^0.467 S^-0.235 of TxDOT (K 0.828 for ft, 1.44 for m) round 0.67^0.467 and the exponent 0.467/2 = 0.2335; Hydrolog's 36.37 for L in km up to 0.8.1 rounded 36.3699
- N Kerby's retardance of the overland surface (Roussel et al. 2005, supplement, p. 29), not Manning's n; NEH 630-15 appendix 15A eq. 15A-2 prints (2.2 n l / S^0.5)^0.324, a misprint of this formula
- the low-slope offset of Cleveland et al. (2012, eqs. 1-2): a slope below 0.002 is taken as S + 0.0005; the formula alone decides it by its own slope, where Cleveland et al. decide by the main-channel slope, which overland flow alone does not have; at 0.002 the offset is dropped, so tc rises by 5.35 % as S reaches 0.002 from below and is monotonic in S only on each side of 0.002

**Assumptions**

- Kerby's data: watersheds below 10 acres (0.04 km2, checked by WatershedParameters.calculate_tc), overland flow up to 1,200 ft, slopes below 1 %, N up to 0.8 (Roussel et al. 2005, p. 5); overland (sheet) flow only
- N from Kerby's table (Roussel et al. 2005, supplement, p. 29): pavement 0.02; smooth, bare, packed soil 0.10; poor grass, cultivated row crops or moderately rough packed surfaces 0.20; pasture, average grass 0.40; deciduous forest 0.60; dense grass, coniferous forest or deciduous forest with deep litter 0.80
- Hydrograf's overland segments (0.04-0.7 km at 0.005-0.19 m/m) are mostly steeper than Kerby's data: their results are extrapolations, with the notice

**Validation:** none reported by the open sources (Kerby 1959 is not open)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases slope_m_per_m-physical_low_*: the offset keeps tc finite as S tends to 0 (S + 0.0005); a slope of 0 is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `retardance` increasing
- limit `decimal`: tc equals (0.67/0.3048)^0.467 (L[m] N)^0.467 S^(-0.467/2) with the offset, evaluated in decimal arithmetic at 50 digits
- limit `low_slope_step`: tc rises by 1.25^0.2335 - 1 = 5.35 % as S reaches 0.002 from below and the offset is dropped: not monotonic in S
- limit `power_law`: doubling L or N multiplies tc by 2^0.467

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the SI form (0.67/0.3048)^0.467 (L[m] N)^0.467 S^(-0.467/2) with the offset, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit decimal)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="kerby_kirpich"></a>
### Time of concentration by the Kerby-Kirpich method (Roussel et al. 2005)

`hydrolog.time.concentration.ConcentrationTime.kerby_kirpich` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_c = \left(\frac{0.67\,N\,L_{ov}}{\sqrt{S_{ov}}}\right)^{0.467} + 0.0078\,(L_{fp} - L_{ov})^{0.77}\,S_{fp}^{-0.385},\quad L\ \mathrm{[ft]}
$$

Plain text: `tc = kerby(L_ov, S_ov, N) + kirpich(L_fp - L_ov, S_fp) [min], each slope below 0.002 taken as S + 0.0005`

**Sources**

- Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement 'Guidance for estimation of time of concentration in Texas', pp. 29-30, and its example (open) <https://rosap.ntl.bts.gov/view/dot/88540/dot_88540_DS1.pdf>
- Texas Department of Transportation (2019). Hydraulic Design Manual, chapter 4, section 11: Time of Concentration, eqs. 4-13 to 4-15 (open) <https://www.txdot.gov/manuals/des/hyd/chapter-4--hydrology/section-11--time-of-concentration.html>
- Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, eqs. 1-3, pp. 1-3, and its example (open) <https://rosap.ntl.bts.gov/view/dot/66537/dot_66537_DS1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `overland_length_km` | $L_{ov}$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | [0.0, 0.366]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: in the development of Kerby's equation the length of overland flow was as much as about 1,200 feet (366 meters), an upper limit | [0.04, 0.7]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland segments of 0.0495 to 0.693 km |
| `overland_slope_m_per_m` | $S_{ov}$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | unstated | [0.005, 0.19]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: overland slopes of 0.00594 to 0.1804 m/m |
| `retardance` | $N$ | - | real | (0.0, inf), test bound high 8.0 (ten times the largest N of Kerby's table (0.80)) | [0.02, 0.8]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: Kerby's table of the retardance N, pavement 0.02 to dense grass, coniferous forest or deciduous forest with deep litter 0.80 | [0.02, 0.8]: Hydrolog's catalog and GUI: Kerby's table of N (Roussel et al. 2005, supplement, p. 29), from which their users take N, option retardance of tc kerby and tc kerby-kirpich: 0.02 (pavement) to 0.80 (dense grass, coniferous forest) |
| `flow_path_length_km` | $L_{fp}$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | [1.6, 80.0]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: main channel lengths of the 92 Texas watersheds approximately 1 to 50 miles, from the outlet to the divide | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km |
| `flow_path_slope_m_per_m` | $S_{fp}$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any flow path or land surface of a watershed on average) | [0.002, 0.02]: Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 29: dimensionless main channel slopes approximately 0.002 to 0.02, from the divide to the outlet | [0.002, 0.11]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow path slopes of 0.00244 to 0.1055 m/m |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `flow_path_longer_than_overland` | physical | flow_path_length_km > overland_length_km | Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G. and Garcia, C.A. (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT Research Report 0-4696-2, Lamar University, supplement, p. 30: the subtraction of the overland flow length from the overall main-channel length (watershed divide to outlet) is necessary |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `kerby_coefficient` | $0.67$ | 0.67 | min^(1/0.467) ft^-1 | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22, (0.67 N L / S^0.5)^0.467 with L in ft; the same in Roussel et al. (2005) eq. 3 |
| `kerby_exponent` | $0.467$ | 0.467 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.12, p. 22; INDOT eq. 29-7.14 and TxDOT (2019) take the same exponent of L N |
| `low_slope_threshold` | $0.002$ | 0.002 | m/m | Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, low slope procedures, step 2(c), p. 2: a main channel slope less than 0.002 is low slope; TxDOT (2019), section 11 |
| `low_slope_offset` | $0.0005$ | 0.0005 | m/m | Cleveland, T.G., Thompson, D.B., Fang, X. and Li, M.-H. (2012). Guidance for estimation of time of concentration in Texas for low-slope conditions. TxDOT Product 0-6382-P1, Texas Tech University, step 3 and eq. 1, p. 2: S_low slope = S0 + 0.0005; TxDOT (2019), section 11 |
| `kirpich_coefficient` | $0.0078$ | 0.0078 | min ft^-0.77 | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; the same in Roussel et al. (2005) eq. 7, Mota and Kobiyama (2015) and FDOT (2024) eq. 2.2-9 |
| `kirpich_length_exponent` | $0.77$ | 0.77 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) |
| `kirpich_slope_exponent` | $-0.385$ | -0.385 | - | Fang, X., Cleveland, T.G., Garcia, C.A., Thompson, D.B. and Malla, R. (2005). Literature review on timing parameters for hydrographs. TxDOT Research Report 0-4696-1, Lamar University, eq. 3.14, p. 22; Mota and Kobiyama (2015); FDOT (2024) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `tc_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- tc = t_overland + t_channel: kerby on the overland segment, kirpich on the channel segment, the flow path minus the overland segment, at the slope of the whole path from the divide to the outlet (Roussel et al. 2005, supplement, pp. 29-30), in the units and with the constants of those specs
- a deviation from Cleveland et al. (2012, pp. 1-2): the low-slope offset (S + 0.0005 below 0.002) is decided for each segment by its own slope, the overland slope for Kerby and the flow path slope for Kirpich, while Cleveland et al. decide it by the main-channel slope for both segments (below 0.002 both offset, above 0.003 neither) and leave 0.002-0.003 to the engineer ('if flow direction ambiguity is present, treat as low slope'); the two agree when both slopes lie on the same side of 0.002 and differ for a flat main channel under a steeper overland segment (Cleveland et al. offset it too), for a steep main channel under a flat overland segment (Hydrolog offsets it) and in the transitional band (Hydrolog never offsets the channel there)
- at a flow path slope of 0.002 the channel part rises by 8.97 %, at an overland slope of 0.002 the overland part by 5.35 %, as the offset is dropped: tc is not monotonic in either slope

**Assumptions**

- the 92 Texas watersheds of Roussel et al. (2005): 0.25-150 square miles (0.65-388 km2, checked by WatershedParameters.calculate_tc), main channels of 1-50 miles at 0.002-0.02; 'no watersheds with low topographic slopes are available in the underlying database' (supplement, p. 29)
- the overland segment up to 1,200 ft, Kerby's upper limit (supplement, p. 29); the method states no range of the overland slope, and its own example takes 2 %

**Validation:** Roussel et al. (2005, supplement, p. 29) find the Kerby-Kirpich estimates 'consistent with watershed time values independently derived from real-world storms and runoff hydrographs' of their 92 Texas watersheds

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `difference_denominator`: constraint flow_path_longer_than_overland: the channel segment L_fp - L_ov vanishes at the boundary point, which is refused, so Kirpich never takes a length of 0
- `singular_at_bound`: range cases *_slope_m_per_m-physical_low_*: the offset keeps both parts finite as a slope tends to 0

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `retardance` increasing, `flow_path_length_km` increasing
- limit `decimal`: tc equals Kerby on the overland segment plus Kirpich on the rest of the flow path, each with its own offset, evaluated in decimal arithmetic at 50 digits
- limit `low_slope_step`: the channel part rises by 1.25^0.385 - 1 = 8.97 % as the flow path slope reaches 0.002 and the offset is dropped

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/tc-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the two SI forms with unrounded constants and the offset per segment, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_tc.py (limit decimal)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="equal_area_slope"></a>
### Equal-area slope of a longitudinal profile (the line through the outlet with equal areas above and below it)

`hydrolog.morphometry.profile.equal_area_slope` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
S = \frac{2A}{L^2},\quad A = \sum_{i} \frac{(x_{i+1} - x_i)\,(h_i + h_{i+1})}{2},\quad h_i = z_i - z_0,\quad L = x_n - x_0
$$

Plain text: `S = 2 A / L**2 with A = sum((x[i+1] - x[i]) * (h[i] + h[i+1]) / 2), h = z - z[0], L = x[-1] - x[0] [m/m]`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the legend of eq. 6.17: Jg, the averaged slope of the main stream, is the slope of the line from the lowest point of the longitudinal profile for which the areas between it and the profile, below and above it, are equal (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- Ministry of Works and Development, Water and Soil Division (1980). A method for estimating design peak discharge, Technical Memorandum No. 61, Wellington, appendix A, pp. 12-13: the equal-area method, line AC through the outlet A with equal areas X and Y; the area under the profile Ad equals the triangle ABC, so Sa = 2Ad/L^2 (open) <https://web.archive.org/web/20170228021947/http://docs.niwa.co.nz/library/public/TM61_1980.pdf>
- Barbosa Jr., A.R. (2004). Hidrologia Aplicada CIV 226, Bacia Hidrográfica, Universidade Federal de Ouro Preto, lecture notes, section 3.4.4, eqs. 17-18, p. 14: the area under the profile Ap as a sum of trapezoids and S2 = 2Ap/L^2 - 2z_foz/L (open) <https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/17403/material/Cap2%20-%20Bacia%20Hidrografica_UFOP.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `distance_m` | $x$ | m | real_array | [0.0, inf), test bound high 1000000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no flow path of a Polish watershed is longer) | unstated | [0.0, 30000.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km |
| `elevation_m` | $z$ | m | real_array | (-inf, inf), test bound low -431.0 and high 8849.0 (the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of Jordan and Nepal)) | unstated | [100.0, 750.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one elevation per distance | Barbosa Jr., A.R. (2004). Hidrologia Aplicada CIV 226, Bacia Hidrográfica, Universidade Federal de Ouro Preto, lecture notes, section 3.4.4, eqs. 17-18, p. 14: the area under the profile Ap as a sum of trapezoids and S2 = 2Ap/L^2 - 2z_foz/L |
| `distance_not_decreasing` | physical | x[i+1] >= x[i]: the profile runs from the outlet upstream; a repeated distance is a vertical step | Barbosa Jr., A.R. (2004). Hidrologia Aplicada CIV 226, Bacia Hidrográfica, Universidade Federal de Ouro Preto, lecture notes, section 3.4.4, eqs. 17-18, p. 14: the area under the profile Ap as a sum of trapezoids and S2 = 2Ap/L^2 - 2z_foz/L |
| `positive_area` | precondition | 0 < 2 A / L**2 < inf: the profile lies above its outlet on the whole (A > 0) over a length L > 0, and float64 holds both | Ministry of Works and Development, Water and Soil Division (1980). A method for estimating design peak discharge, Technical Memorandum No. 61, Wellington, appendix A, pp. 12-13: the equal-area method, line AC through the outlet A with equal areas X and Y; the area under the profile Ad equals the triangle ABC, so Sa = 2Ad/L^2 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `slope_m_per_m` | m/m | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the profile is ordered from the outlet upstream: x the distance along the flow path in m from any origin, as only differences count, z the elevation in m; L is the last distance minus the first
- the line passes through the first point, the outlet, at its elevation: TM61 draws it through the outlet A, KZGW (2017, p. 97) from the lowest point of the profile, which the outlet of a flow path on a filled DEM is; a stretch below the outlet counts as area below the line, so A is the signed area of z - z[0]
- A by the trapezoid rule, the profile straight between its points (Barbosa Jr., eq. 17); the triangle under the line, L (S L) / 2, equals A, so the areas of the profile above and below the line are equal (TM61, Sa = 2Ad/L^2)
- S in m/m, not in percent or per mille
- Lutz's Jg (KZGW 2017, p. 97) is this slope of the longitudinal profile of the main stream from the divide to the outlet, the longest flow path (WatershedParameters.flow_path_equal_area_slope_m_per_m); the slope between the ends of that path (flow_path_slope_m_per_m), Kirpich's S, is larger on a concave profile and no substitute for it

**Assumptions**

- the points are those of one flow path where the elevation is known: the cells of a D8 path on a filled DEM or surveyed points; a run of points of equal elevation may be thinned to its ends without changing A
- a profile from a filled DEM has no point below its outlet; a surveyed bed may have pools below it, which reduce A

**Validation:** none: the equal-area slope defines the mean slope of a profile (TM61, appendix A; KZGW 2017, p. 97); its sources compare it with no observations, and TM61 (p. 12) notes that in practice it gives results largely independent of the user

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: L = x[-1] - x[0]: a profile of equal distances has L = 0 and is refused by the precondition positive_area (test_a_profile_without_length_is_refused)
- `singular_at_bound`: S grows as 1/L^2: a profile of 1 mm is finite, one whose L^2 underflows is refused by the precondition positive_area (test_a_tiny_profile_is_finite_or_refused)
- `gap_propagation`: type cases distance_m-nan_element and elevation_m-nan_element: a gap is refused, the spec allows none
- `many_small_terms`: test_a_profile_of_many_points_matches_its_exact_sum: 100,001 points against the exact rational sum

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `both_axes`: inputs times 2^e (`distance_m` e = 1.0, `elevation_m` e = 1.0) give outputs times 2^e (none)
- scaling `elevation`: inputs times 2^e (`elevation_m` e = 1.0) give outputs times 2^e (`slope_m_per_m` e = 1.0)
- scaling `distance`: inputs times 2^e (`distance_m` e = 1.0) give outputs times 2^e (`slope_m_per_m` e = -1.0)
- limit `straight_profile`: a straight profile gives its own slope
- limit `two_points`: a profile of two points gives the drop over the length
- limit `exact_rational`: S equals 2A/L^2 of the float inputs in exact rational arithmetic
- limit `equal_areas`: the line through the outlet at slope S leaves equal areas of the profile above and below it, found by bisection

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: 2A/L^2 of the float inputs in exact rational arithmetic (fractions), rounded once (`tests/unit/test_formulas_equal_area_slope.py (limit exact_rational, the Kamiennik profile, trap many_small_terms)`)
- algorithm: the sources' construction: the line through the outlet whose slope bisection moves until the profile's areas above and below it, summed apart over the segments cut where they cross it, are equal (`tests/unit/test_formulas_equal_area_slope.py (limit equal_areas, the Kamiennik profile)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="lutz"></a>
### Nash's n and K of an ungauged watershed by Lutz's method (KZGW 2017)

`hydrolog.runoff.nash_iuh.lutz_parameters` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_p = P_1 \left(\frac{L\,L_c}{J_g^{1.5}}\right)^{0.26} e^{-0.016\,U} e^{0.004\,W},\quad P_1 = 3.989\,n_M + 0.028,\quad u_p = \frac{0.66}{t_p^{1.04}},\quad \frac{(N-1)^N e^{-(N-1)}}{\Gamma(N)} = t_p\,u_p,\quad K = \frac{t_p}{N-1}
$$

Plain text: `tp = P1 * (L * Lc / Jg**1.5)**0.26 * exp(-0.016 * U) * exp(0.004 * W) [h], P1 = 3.989 * nM + 0.028; up = 0.66 / tp**1.04 [1/h] (dt -> 0); N solves (N - 1)**N * exp(-(N - 1)) / Gamma(N) = tp * up; K = tp / (N - 1)`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), annex 2, section 3.1.2, pp. 97-98: eqs. 6.17-6.21, Fig. 6.3 and the definitions of L, Lc, Jg, U and W; Ex. 6.2, pp. 99-100; Table C.2, pp. 132-133 (N against f(N)) (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- Sikorska, A.E., Scheidegger, A., Banasik, K., Rieckermann, J. (2012). Bayesian uncertainty assessment of flood predictions in ungauged urban basins for conceptual rainfall-runoff models. Hydrology and Earth System Sciences 16, 1221-1236, Table 1, p. 1226: Lutz's tp with the exponent 0.26 and up = P2 / tp**P3, P2 = 0.64 and P3 = 1.04, 'dependent on the interval of estimation' (open) <https://hess.copernicus.org/articles/16/1221/2012/hess-16-1221-2012.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no main stream of a Polish watershed is longer) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: flow paths of 0.0566 to 28.88 km |
| `centroid_length_km` | $Lc$ | km | real | (0.0, inf), test bound high 1000.0 (1,000 km, about the length of the Vistula, the longest river of Poland: no main stream of a Polish watershed is longer) | unstated | [0.004, 15.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Lc of 0.0042 to 14.49 km |
| `slope_m_per_m` | $Jg$ | m/m | real | (0.0, inf), test bound high 1.0 (a mean slope of 1 m/m (45 degrees), steeper than any main stream on average) | unstated | [0.002, 0.11]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: slopes between the ends of the flow paths, 0.00244 to 0.1055 m/m, which bound their equal-area slopes on concave profiles (Kamiennik: 0.00848 against 0.0114) |
| `manning_n` | $nM$ | s m^-1/3 | real | (0.0, inf), test bound high 0.8 (0.80, the roughness of overland flow through woods with dense underbrush, rougher than any channel (USDA-NRCS 1986, TR-55, table 3-1)) | unstated | [0.025, 0.035]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); and Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), KZGW Ex. 6.2, p. 99: n = 0.025 for the Niedźwiadka; tests/fixtures/kamiennik.json: n = 0.035 |
| `urban_pct` | $U$ | % | real | [0.0, 100.0] | unstated | [0.0, 10.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: urbanized shares of 0 to 9 % |
| `forest_pct` | $W$ | % | real | [0.0, 100.0] | unstated | [0.0, 100.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: forest shares of 0 to 100 % |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `centroid_within_length` | physical | Lc <= L: both run along the main stream from the outlet, Lc to its point nearest the centroid, L to the divide | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the definitions of L and Lc under eq. 6.17 |
| `shares_within_catchment` | physical | U + W <= 100: the urbanized and the forest land are shares of the same watershed's area that do not overlap | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 97, the definitions of U and W under eq. 6.17 |
| `root_in_bracket` | precondition | f(1.1) <= tp up <= f(20), tp from about 3.4e-11 to 3.4e23 h: the root N of f(N) = tp up lies in the bracket searched, from the first row of Table C.2, and float64 holds every step | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.20, p. 98, and Table C.2, pp. 132-133, from N = 1.10 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `p1_slope` | $3.989$ | 3.989 | h km^-0.52 s^-1 m^1/3 | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.18, p. 97; Fig. 6.3, p. 98: P1 = 3.9886 n + 0.0284 (R2 = 0.9974), after Lutz (1984) |
| `p1_intercept` | $0.028$ | 0.028 | h km^-0.52 | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), Fig. 6.3, p. 98 (+0.0284) and Ex. 6.2, p. 99 (P1 = 0.128 for n = 0.025); eq. 6.18, p. 97, prints '- 0,028', a misprint |
| `slope_exponent` | $1.5$ | 1.5 | - | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1 |
| `geometric_exponent` | $0.26$ | 0.26 | - | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1 |
| `urban_coefficient` | $-0.016$ | -0.016 | 1/% | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1 |
| `forest_coefficient` | $0.004$ | 0.004 | 1/% | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.17, p. 97; the same in Sikorska et al. 2012, Table 1 |
| `peak_coefficient` | $0.66$ | 0.66 | h^0.04 | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.19, p. 98, for dt -> 0; Sikorska et al. 2012, Table 1, give P2 = 0.64 |
| `peak_exponent` | $1.04$ | 1.04 | - | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.19, p. 98; the same in Sikorska et al. 2012, Table 1 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `time_to_peak_h` | h | real | (0.0, inf) | 4 ulp of the bound |
| `peak_ordinate_per_h` | 1/h | real | (0.0, inf) | 4 ulp of the bound |
| `n` | - | real | (1.0, inf) | 4 ulp of the bound |
| `k_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `p1` | h km^-0.52 | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- up = 0.66 / tp**1.04 is Lutz's relation for dt -> 0 (KZGW 2017, eq. 6.19, p. 98), the peak of the instantaneous unit hydrograph; the unit hydrograph of a step dt averages that IUH exactly over dt (NashIUH.to_unit_hydrograph). KZGW's Ex. 6.2 (p. 100) takes instead the relation of dt = 1 h, up = 0.464 / tp**0.824, and Sikorska et al. (2012, Table 1) state that P2 and P3 depend on the interval: that route gives N 2.55 and k 0.70 h where this one gives N 3.88 and K 0.377 h (case kzgw2017-ex6-2-n-k, a discrepancy)
- P1 = 3.989 nM + 0.028: eq. 6.18 (KZGW 2017, p. 97) prints '- 0,028', a misprint, as Fig. 6.3 (P1 = 3.9886 n + 0.0284) and Ex. 6.2 (P1 = 0.128 for n = 0.025) show
- 0.66 of KZGW eq. 6.19, not the 0.64 of Sikorska et al. (2012, Table 1), who cite the same Lutz (1984)
- L and Lc in km, Jg in m/m, the equal-area slope of the main stream's profile (KZGW 2017, p. 97; spec equal_area_slope), nM in s m^-1/3, U and W in percent of the watershed's area; tp in h, up in 1/h, K returned in min by the exact 60 min/h
- N solves f(N) = tp up on [1.1, 20] by Brent's method (scipy.optimize.brentq, xtol 1e-6) where KZGW reads it from Table C.2 (pp. 132-133); f increases strictly there, from 0.0755 to 1.731, and matches the table's 13 rows from N = 1.10 to 7.99 within half its printed digit

**Assumptions**

- watersheds of up to 236 km2 with development spread fairly evenly (KZGW 2017, p. 97); NashIUH.from_lutz warns of a larger area; Lutz's data were 75 watersheds of up to 250 km2 (Sikorska et al. 2012, p. 1225)
- a near-natural watershed: KZGW (2017, p. 96) uses Nash's model with Lutz's parameters for imperviousness below 5 %

**Validation:** Lutz (1984) fitted the relations to 75 watersheds of south-west Germany of up to 250 km2 (Sikorska et al. 2012, p. 1225); KZGW (2017, Fig. 6.3) gives R2 = 0.9974 for P1 against Manning's n; no source open to Hydrolog reports the errors of tp, up or the peak flows against observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases slope_m_per_m-physical_low_*: tp grows without bound as Jg tends to 0 (Jg^-0.39), and as tp tends to 0 the target tp up = 0.66 tp^-0.04 grows; beyond the bracket of N the precondition root_in_bracket refuses, as for the smallest positive Jg, whose Jg^1.5 underflows
- `exp_overflow`: range cases urban_pct-physical_high and forest_pct-physical_high: exp(-0.016 U) and exp(0.004 W) at 100 % are 0.2019 and 1.4918

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `centroid_length_km` increasing, `slope_m_per_m` decreasing, `manning_n` increasing, `urban_pct` decreasing, `forest_pct` increasing
- limit `decimal_steps`: tp and up equal eqs. 6.17-6.19 evaluated in decimal arithmetic at 50 digits
- limit `cascade_peak`: the gamma density of shape N and scale K, Nash's IUH, peaks at (N - 1) K = tp with the ordinate up (scipy.stats.gamma)
- limit `power_law`: doubling L or Lc multiplies tp by 2^0.26, doubling Jg by 2^-0.39; adding 10 to U or W multiplies it by exp(-0.16) or exp(0.04)

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/lutz-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: tp and up of eqs. 6.17-6.19 with the decimal constants, evaluated with the decimal module at 50 digits (`tests/unit/test_formulas_lutz.py (limit decimal_steps)`)
- established: scipy.stats.gamma (SciPy 1.18.1): the density of shape N and scale K, Nash's IUH, at its mode (N - 1) K (`tests/unit/test_formulas_lutz.py (limit cascade_peak)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="scs"></a>
### SCS (NRCS) dimensionless unit hydrograph of a unit duration

`hydrolog.runoff.unit_hydrograph.scs_unit_hydrograph` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_{lag} = 0.6\,t_c,\quad T_p = \frac{D}{2} + t_{lag},\quad q_p = \frac{C\,A}{T_p},\quad q_k = q_p\,f\!\left(\frac{k\,D}{T_p}\right),\quad T_b = 5\,T_p
$$

Plain text: `tlag = 0.6 * tc; Tp = D / 2 + tlag; qp = C * A / Tp [m3/s per cm of runoff, A in km2, Tp in h], C = 2.08, per mm qp / 10; q(t) = qp * f(t / Tp), f table 16-1 of NEH 630 ch. 16 interpolated linearly, 0 beyond t / Tp = 5, so Tb = 5 Tp; the ordinates are q(k D). For D > 0.25 Tp the ordinate at k D is the mean of the ordinates q_d(j d) of the sub-step d = D / n over the n sub-steps ending at k D, d the longest with d <= 0.25 Tp(d)`

**Sources**

- USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), table 16-1, p. 16-4; appendix 16A, eqs. 16A-6 to 16A-9 and 16A-13, pp. 16A-2 to 16A-3; example 16-1, pp. 16-7 to 16-13 (open) <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>
- USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), SCS unit hydrograph model, eqs. 36-38, pp. 55-56 (open) <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
- Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, Snyder's synthetic UHG, pp. 76-78 (eqs. 7.7.2-7.7.4, C1 0.75, C2 2.75, C3 5.56, Cw 2.14 and 1.22 in SI, 770 and 440 in English units, areas of 30 to 30,000 km2); SCS dimensionless hydrograph, p. 79 (C = 2.08, 483.4 in English units) (open) <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 1000000.0 (a million km2, five times the basin of the Vistula (194,000 km2) and four thousand times the largest watershed Hydrograf hands over) | [0.0, 51.8]: USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), p. 16-4: no subarea to exceed 20 square miles (51.8 km2), the largest no more than 10 times the smallest | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `tc_min` | $t_c$ | min | real | (0.0, inf), test bound high 4500.0 (ten times the longest time of concentration of the hand-offs (450 min)) | unstated | [1.0, 450.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Kirpich's tc of the flow paths of the 27 watersheds, the default method of hydrograph generate, 1.04 to 450 min |
| `timestep_min` | $D$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `steps_representable` | precondition | float64 holds tlag, Tp, the sub-step and the peaks as normal numbers, at most 2**53 sub-steps, and the grid of the step and of the sub-step have at most a million ordinates each | Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `lag_ratio` | $0.6$ | 0.6 | - | USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), eq. 16A-9, p. 16A-2: L = 0.6 Tc (after NEH 630 ch. 15); HEC-HMS 2000, eq. 38, p. 56 |
| `peak_factor` | $C$ | 2.08 | m3 s^-1 km^-2 cm^-1 h | USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 36, p. 55: C = 2.08 in SI and 484 in foot-pound units; Chow et al. 1988, after Rajagopalan's notes, p. 79: C = 2.08 (483.4 in English units) |
| `step_share` | $0.25$ | 0.25 | - | USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), p. 16A-3: the unit duration D is 0.2 Tp and no greater than 0.25 Tp; HEC-HMS 2000, p. 55: less than 29 % of tlag |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `peak_discharge_m3s` | m3/s per mm | real | [0.0, inf) | 4 ulp of the bound |
| `time_to_peak_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `lag_time_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `time_base_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `times_min` | min | real_array | [0.0, inf) | 4 ulp of the bound |
| `ordinates_m3s` | m3/s per mm | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: A in km2, times in min, ordinates in m3/s per mm of runoff; C = 2.08 is per cm (HEC-HMS 2000 eq. 36), per mm by the exact 10 mm/cm
- C = 2.08 is NEH's peak rate factor 483.2 in foot-pound units, not 484: NEH 630 (p. 16A-2) gives table 16-1 the factor 483.4 from the rounding of its ratios; with 2.08 the continuous table holds 1.00036 mm
- times from the beginning of the unit excess; D is the time step
- table 16-1 interpolated linearly between its rows, as NEH 630 table 16-2 does (t/Tp 2.1 gives 0.2435), and 0 from t/Tp = 5 on
- the ordinates are the curve sampled at the step times (NEH 630 example 16-1, step 2)
- a step longer than 0.25 Tp is divided into sub-steps and the rain of the step spread evenly over them (notice uh_substeps): the volume stays 1 mm, while qp, Tp and Tb stay the formula's values for D, so qp then exceeds the largest ordinate (by 21 % for tc 90.7 min at a step of 60 min)

**Assumptions**

- excess rainfall uniform over the watershed and in time over D; subareas of at most 20 square miles, the largest at most 10 times the smallest (NEH 630 p. 16-4), larger watersheds divided and their hydrographs routed
- tlag = 0.6 tc, the average relation of NEH 630 ch. 15
- D = 0.2 Tp (D = 0.133 tc), at most 0.25 Tp (NEH 630 p. 16A-3); hydrograph generate warns outside_typical_range of scs.timestep_min beyond it

**Validation:** Mockus (1957) derived the dimensionless unit hydrograph from many natural unit hydrographs of watersheds varying widely in size and geographical location (NEH 630-16, p. 16-2; HEC-HMS 2000, p. 55: small agricultural watersheds); the sources give no error statistic of its shape or peak

**Notices:** `outside_applicability`, `uh_substeps`

**Numerical traps (CMP-6.6)**

- `stability_bound`: test_scs_steps_at_and_beyond_the_neh_bound: the step 0.25 Tp itself is sampled as it is, the next one is computed on sub-steps and keeps its volume
- `unbounded_iteration`: the count of sub-steps is a closed form corrected at most twice for rounding; range case tc_min-physical_low_inside: a sub-step float64 cannot hold is refused by the precondition steps_representable
- `many_small_terms`: test_scs_a_day_step_keeps_its_volume: E5b-07, 93 sub-steps of a step of 1440 min summed by cumulative sums

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` increasing, `tc_min` decreasing, `timestep_min` decreasing
- scaling `area`: inputs times 2^e (`area_km2` e = 1.0) give outputs times 2^e (`peak_discharge_m3s` e = 1.0, `ordinates_m3s` e = 1.0)
- scaling `time`: inputs times 2^e (`tc_min` e = 1.0, `timestep_min` e = 1.0) give outputs times 2^e (`peak_discharge_m3s` e = -1.0, `time_to_peak_min` e = 1.0, `lag_time_min` e = 1.0, `time_base_min` e = 1.0, `times_min` e = 1.0, `ordinates_m3s` e = -1.0)
- limit `exact_table`: the ordinates equal the equation in exact rational arithmetic, with and without sub-steps
- limit `recommended_duration`: D = 2 tc / 15 gives D = 0.2 Tp and the peak ordinate qp at Tp (NEH 630 eqs. 16A-10 to 16A-13)
- conservation `unit_volume`: the ordinates hold 1 mm over the watershed, sum(q_k) D = A * 1 mm, within the sampling of the table

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/unit-hydrographs-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the ordinates in exact rational arithmetic (fractions): Tp, qp, the linear interpolation of table 16-1 and the means over the sub-steps (`tests/unit/test_formulas_unit_hydrographs.py (limit exact_table)`)

**Tables (CMP-2.5)**

- `src/hydrolog/_data/tables/neh630_duh.csv` sha256 `b465694f902953d282e964c34c7a535adc4cb8c833948ffca7c2a5080d871709`: USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), table 16-1, p. 16-4: time ratios t/Tp and discharge ratios q/qp (the same ratios in NEH-4 (1972), table 16.1); transcriptions compared in `tests/oracles/neh630_duh_text_layer.csv (transcribed from the PDF's text layer by tests/oracles/transcribe_neh630_duh.py) against tests/oracles/neh630_duh_hydrolog_0_8_1.csv (typed for Hydrolog 0.8.1), compared by tests/unit/test_formulas_unit_hydrographs.py; USDA-SCS (1972). National Engineering Handbook, Section 4 Hydrology, Chapter 16: Hydrographs (NEH Notice 4-102, August 1972; amendment 6, March 1985), table 16.1, prints the same ratios`

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="snyder"></a>
### Snyder's synthetic unit hydrograph: lag, peak, time base and widths

`hydrolog.runoff.snyder_uh.snyder_parameters` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
t_L = C_t\,(L\,L_c)^{0.3},\quad t_D = \frac{t_L}{5.5},\quad t_{LR} = t_L + \frac{D - t_D}{4},\quad t_{pR} = t_{LR} + \frac{D}{2},\quad q_{pR} = \frac{0.275\,C_p\,A}{t_{LR}},\quad t_b = \frac{0.556\,A}{q_{pR}},\quad W_{50} = 770 \left(\frac{q_{pR}}{A}\right)^{-1.08}
$$

Plain text: `tL = Ct (L Lc)^0.3 [h, L and Lc in km, Ct in SI units]; tD = tL / 5.5; tLR = tL + (D - tD) / 4; tpR = tLR + D / 2; qp = 0.275 Cp A / tL, qpR = 0.275 Cp A / tLR [m3/s per mm, A in km2, times in h]; tb = 0.556 A / qpR [h]; W50 = 770 (qpR / A)^-1.08 and W75 = 440 (qpR / A)^-1.08 [h, qpR / A in ft3/s per mi2 and in], 0.17829 and 0.10188 with qpR / A in m3/s per km2 and mm; times given in min`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 6.4 to 6.11, pp. 90-92; example 6.1, pp. 92-95 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Snyder's unit hydrograph model, eqs. 30-32, pp. 54-55 (open) <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
- USACE-HEC. HEC-HMS Technical Reference Manual (online, read 2026-11-19), chapter Transform, Snyder Unit Hydrograph Model, eqs. 1 to 5: tp = C Ct (L Lc)^0.3, C = 0.75 in SI and 1.00 in foot-pound units (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/snyder-unit-hydrograph-model>
- Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, Snyder's synthetic unit hydrograph, pp. 76-78, eqs. 7.7.2-7.7.6 (open) <https://civil.colorado.edu/~balajir/CVEN5333/Lectures/Unit-Hydrographs-Chow-Chap7.pdf>
- Innovyze. InfoSWMM help, Snyder Unit Hydrograph Method (online, read 2026-11-19), the widths W50 and W75 of the unit hydrograph: C50 = 770 and C75 = 440 in U.S. customary units, 2.14 and 1.22 in S.I. units; C2 = 640 and 2.75 of the peak (open) <https://help.innovyze.com/space/infoswmm/17598671/Snyder+Unit+Hydrograph+Method>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 1000000.0 (a million km2, five times the basin of the Vistula (194,000 km2) and four thousand times the largest watershed Hydrograf hands over) | [30.0, 30000.0]: Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 76: Snyder's watersheds in the Appalachian Highlands, of 30 to 30,000 km2 (10 to 10,000 mi2) | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 2000.0 (twice the length of the Vistula (1,047 km), the longest river of Poland) | unstated | [0.05, 29.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: the longest flow paths of the 27 watersheds that have one, 0.057 to 28.9 km (flow_path_length_km): Snyder's L runs from the outlet to the divide, and Lc along it to the point nearest the centroid |
| `centroid_length_km` | $L_c$ | km | real | (0.0, inf), test bound high 2000.0 (twice the length of the Vistula (1,047 km), the longest river of Poland) | unstated | [0.05, 29.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: the longest flow paths of the 27 watersheds that have one, 0.057 to 28.9 km (flow_path_length_km): Snyder's L runs from the outlet to the divide, and Lc along it to the point nearest the centroid |
| `ct` | $C_t$ | - | real | (0.0, inf), test bound high 60.0 (ten times the largest Ct HEC-HMS reports, 8.0 in foot-pound units (6.0 in SI) near the Gulf of Mexico) | [1.35, 1.65]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units, 0.75 times Snyder's 1.8 to 2.2 | [1.35, 1.65]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 90, eq. 6.5: Ct from 1.35 to 1.65 in SI units |
| `cp` | $C_p$ | - | real | (0.0, inf), test bound high 8.0 (ten times the largest Cp of the sources, 0.8) | [0.4, 0.8]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona); and USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), KZGW 2017, annex 2, p. 91, eq. 6.7: Cp from 0.4 to 0.8; HEC-HMS 2000, Snyder's unit hydrograph model, p. 54: 0.4 to 0.8 | [0.4, 0.8]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), p. 91, eq. 6.7: Cp from 0.4 to 0.8 |
| `duration_min` | $D$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `representable` | precondition | float64 holds the lag, the peaks, the time base and the widths as normal numbers | IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `lag_exponent` | $0.3$ | 0.3 | - | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.5, p. 90: tL = Ct (L Lc)^0.3; HEC-HMS (online), Snyder Unit Hydrograph Model, eq. 5; Chow et al. 1988 after Rajagopalan's notes, eq. 7.7.2, p. 76 |
| `standard_ratio` | $5.5$ | 5.5 | - | USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 30: tp = 5.5 tr; KZGW 2017, annex 2, eq. 6.6, p. 91: tD = tL / 5.5 |
| `adjustment` | $1/4$ | 0.25 | - | USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), eq. 31: tpR = tp - (tr - tR) / 4; KZGW 2017, annex 2, eq. 6.8, p. 91: tLR = tL + 0.25 (D - tD) |
| `peak_factor` | $0.275$ | 0.275 | m3 s^-1 km^-2 mm^-1 h | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.7, p. 91: qp = 0.275 Cp A / tL in m3/s per mm; HEC-HMS 2000, eq. 32, and Chow et al. 1988 after Rajagopalan's notes, eq. 7.7.3, p. 77: C2 = 2.75 per cm |
| `base_factor` | $0.556$ | 0.556 | h m3 s^-1 km^-2 mm^-1 | KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.11, p. 92: tb = 0.556 A / qpR; Chow et al. 1988 after Rajagopalan's notes, p. 78: C3 = 5.56 per cm |
| `width_50` | $770$ | 770.0 | h (ft3 s^-1 mi^-2 in^-1)^1.08 | Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: W = Cw qpR^-1.08 with Cw = 770 at 50 % of the peak in English units (2.14 in SI per cm); Innovyze, Snyder Unit Hydrograph Method: C50 = 770 |
| `width_75` | $440$ | 440.0 | h (ft3 s^-1 mi^-2 in^-1)^1.08 | Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: Cw = 440 at 75 % of the peak in English units (1.22 in SI per cm); Innovyze, Snyder Unit Hydrograph Method: C75 = 440 |
| `width_exponent` | $1.08$ | 1.08 | - | Rajagopalan, B. CVEN 5333 lecture notes, Unit Hydrographs, after Chow, V.T., Maidment, D.R. and Mays, L.W. (1988), Applied Hydrology, chapter 7, University of Colorado Boulder, p. 78: W = Cw qpR^-1.08, qpR per unit area |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `lag_time_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `standard_duration_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `adjusted_lag_time_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `time_to_peak_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `standard_peak_discharge_m3s` | m3/s per mm | real | (0.0, inf) | 4 ulp of the bound |
| `peak_discharge_m3s` | m3/s per mm | real | (0.0, inf) | 4 ulp of the bound |
| `time_base_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `width_50_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `width_75_min` | min | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: A in km2, L and Lc in km; Ct in SI units holds Snyder's 0.75 (HEC-HMS: tp = C Ct (L Lc)^0.3, C = 0.75 in SI), so that its 1.35 to 1.65 is 0.75 times Snyder's 1.8 to 2.2 (KZGW 2017 p. 90)
- peaks in m3/s per mm of runoff: 0.275 and 0.556 per mm are Chow's 2.75 and 5.56 per cm (KZGW 2017 eqs. 6.7 and 6.11)
- times from the beginning of the unit rainfall, given in min: the lag tL is Snyder's tp of HEC-HMS and Chow, the time to peak is KZGW's tp = tL + tD / 2 for D = tD and tpR = tLR + D / 2 for another D
- tb is the base of the triangle of the peak qpR that holds 1 mm (KZGW 2017 eq. 6.11, Chow's C3 / qpR), not the end of the curve of snyder_shape
- the widths are those of Chow et al. (1988), from qpR per unit area, with Snyder's 770 and 440 converted exactly from ft3/s per mi2 and in (1 / 2323.2 m3/s per km2 and mm, the units table): 0.17829 and 0.10188; Chow's SI 2.14 and 1.22 per cm round them (0.17800 and 0.10148 per mm, 0.2 % and 0.4 % lower)
- L is the length of the main stream from the outlet to the divide, Lc the length along it to the point nearest the centroid (KZGW 2017 p. 90)

**Assumptions**

- the coefficients Ct and Cp are those of the region, best calibrated on gauged watersheds of it (HEC-HMS); KZGW 2017 gives 1.35 to 1.65 and 0.4 to 0.8
- most watersheds of the ecosystem (the hand-offs' areas up to 250 km2) are smaller than Snyder's, 30 to 30,000 km2: they get the notice outside_typical_range of snyder.area_km2

**Validation:** Snyder (1938) derived the relations from watersheds of the Appalachian Highlands of 10 to 10,000 square miles (Chow et al. 1988 after Rajagopalan's notes, p. 76); Ct and Cp are regional and best found by calibration (HEC-HMS); the sources give no error statistic

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: the powers (L Lc)^0.3 and (qpR / A)^-1.08 at the bounds 0 of the inputs: range cases *-physical_low_inside, refused by the precondition representable where an output leaves the normal numbers

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `length_km` increasing, `centroid_length_km` increasing, `ct` increasing
- limit `standard_duration`: the rainfall of the standard duration D = tD keeps the lag tL and the peak qp, with tpR = tL + tD / 2 (KZGW 2017 eqs. 6.4 and 6.8 to 6.10)
- limit `decimal_oracle`: every output equals the equations in decimal arithmetic of fifty digits, the widths from 770 and 440 in foot-pound units
- conservation `triangle_volume`: the triangle of the peak qpR and the base tb holds 1 mm over the watershed, qpR tb / 2 = A x 1 mm, within the rounding of 0.556

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/unit-hydrographs-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: every output in decimal arithmetic of fifty digits, the widths from Snyder's 770 and 440 in foot-pound units and the exact conversion of ft3/s per mi2 and in (`tests/unit/test_formulas_unit_hydrographs.py (limit decimal_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="snyder_shape"></a>
### Snyder's unit hydrograph as the gamma curve of 1 mm through its peak

`hydrolog.runoff.snyder_uh.snyder_shape` · family `scheme` · formula_version 1 · status **oracle only** · mutation score not measured

$$
q(t) = q_{pR}\left[\frac{t}{t_{pR}}\,e^{1 - t/t_{pR}}\right]^K,\quad q_{pR}\,t_{pR}\,\Gamma(K)\left(\frac{e}{K}\right)^K = A \cdot 1\,\mathrm{mm},\quad \sum_k q_k\,\Delta t = A \cdot 1\,\mathrm{mm}
$$

Plain text: `q(t) = qpR [(t / tpR) exp(1 - t / tpR)]^K with K > 0 the root of qpR tpR Gamma(K) (e / K)^K = A x 1 mm, the curve that holds 1 mm over A; the ordinates are q(k dt) for k = 0 to max(1, ceil(T / dt)), rescaled so that the sum of q_k dt is A x 1 mm`

**Sources**

- Asquith, W.H. and Roussel, M.C. (2007). An initial-abstraction, constant-loss model for unit hydrograph modeling for applicable watersheds in Texas. U.S. Geological Survey Scientific Investigations Report 2007-5243, eq. 2, the gamma unit hydrograph through its peak, and eq. 4, its volume qp tp Gamma(K) (e / K)^K (open) <https://pubs.usgs.gov/sir/2007/5243/>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), fig. 6.1, p. 90: the unit hydrograph through (tpR, qpR), its shape not prescribed (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 1000000.0 (a million km2, five times the basin of the Vistula (194,000 km2) and four thousand times the largest watershed Hydrograf hands over) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `time_to_peak_min` | $t_{pR}$ | min | real | (0.0, inf), test bound high 7600.0 (ten times the longest of the typical range) | unstated | [16.0, 760.0]: Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give tpR of 16.6 to 758 min |
| `peak_discharge_m3s` | $q_{pR}$ | m3/s per mm | real | (0.0, inf), test bound high 2350.0 (ten times the largest of the typical range) | unstated | [2.7e-06, 235.0]: Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give qpR of 2.7e-6 to 235 m3/s per mm |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |
| `total_duration_min` | $T$ | min | real | (0.0, inf), test bound high 76000.0 (ten times the longest of the typical range) | unstated | [60.0, 7610.0]: Hydrolog: the spec snyder over the typical ranges of its inputs, the corners of the typical ranges of the spec snyder: areas of 0.0003 to 250 km2, L and Lc of 0.05 to 29 km (Lc <= L), Ct 1.35 to 1.65, Cp 0.4 to 0.8 and D of 5 to 60 min give the ends of the curves at 99.99 % of their volume, the default of SnyderUH, of 61 to 7,605 min (K of 1.14 to 17.2) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `root_bracketed` | precondition | the exponent K of the curve of 1 mm lies between 1e-12 and 1e12: qpR tpR / (A x 1 mm) between about 1e-12 and 4e5 | Hydrolog's bracket of the root of the volume of the curve, Brent's method on ln K from 1e-12 to 1e12 |
| `grid_representable` | precondition | the grid has at most a million ordinates, and float64 holds (T + dt) / tpR and the ordinate of 1 mm on one step, A x 1 mm / dt | Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape_exponent` | - | real | (0.0, inf) | 4 ulp of the bound |
| `times_min` | min | real_array | [0.0, inf) | 4 ulp of the bound |
| `ordinates_m3s` | m3/s per mm | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- times from the beginning of the rainfall, in min; ordinates in m3/s per mm
- the ordinates are the curve at the step times, rescaled to hold exactly 1 mm: the sampling and the part beyond T would change the volume
- SnyderUH takes tpR and qpR of the spec snyder for the duration, and T, unless given, at 99.99 % of the curve's volume, T = tpR P^-1(K + 1, 0.9999) / K with P the regularized lower incomplete gamma function

**Assumptions**

- the shape of the unit hydrograph between its points of Snyder's method is the gamma curve; KZGW 2017 example 6.1 draws straight lines (its table 6.1, a peak 6.9 % lower)

**Validation:** none: Snyder's method gives the peak, the widths and the time base, not a curve (KZGW 2017 fig. 6.1; HEC-HMS fits a Clark unit hydrograph instead); Asquith and Roussel (2007) give the curve and its volume

**Notices:** none

**Numerical traps (CMP-6.6)**

- `unbounded_iteration`: Brent's method on ln K in a bracket with at most a hundred iterations; outside it the precondition root_bracketed refuses: test_snyder_shape_refuses_an_exponent_outside_its_bracket
- `many_small_terms`: the volume of up to a million ordinates by math.fsum: test_snyder_shape_a_million_ordinates_hold_their_volume

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `time`: inputs times 2^e (`time_to_peak_min` e = 1.0, `peak_discharge_m3s` e = -1.0, `timestep_min` e = 1.0, `total_duration_min` e = 1.0) give outputs times 2^e (`times_min` e = 1.0, `ordinates_m3s` e = -1.0)
- scaling `area`: inputs times 2^e (`area_km2` e = 1.0, `peak_discharge_m3s` e = 1.0) give outputs times 2^e (`ordinates_m3s` e = 1.0)
- limit `volume_identity`: K solves qpR tpR Gamma(K) (e / K)^K = A x 1 mm (Asquith and Roussel 2007 eq. 4)
- limit `gamma_density`: the ordinates are proportional to SciPy's gamma density of the shape K + 1 and the scale tpR / K
- limit `peak_at_its_time`: a step that divides tpR puts the largest ordinate at tpR
- conservation `unit_volume`: the ordinates hold 1 mm over the watershed, sum(q_k) dt = A x 1 mm

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/unit-hydrographs-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the volume of the curve, qpR tpR Gamma(K) (e / K)^K = A x 1 mm (Asquith and Roussel 2007 eq. 4), in math.gamma and a power (`tests/unit/test_formulas_unit_hydrographs.py (limit volume_identity)`)
- established: SciPy's gamma distribution (scipy.stats.gamma, SciPy of Nogat's release set): its density of the shape K + 1 and the scale tpR / K is proportional to the curve (`tests/unit/test_formulas_unit_hydrographs.py (limit gamma_density)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="clark"></a>
### Clark's unit hydrograph of a duration: time-area curve and linear reservoir

`hydrolog.runoff.clark_iuh.clark_unit_hydrograph` · family `scheme` · formula_version 1 · status **oracle only** · mutation score not measured

$$
\frac{A_t}{A} = 1.414\left(\frac{t}{t_c}\right)^{1.5},\ t \le \frac{t_c}{2};\quad O_i = O_{i-1} + \frac{\Delta t}{2R + \Delta t}\,(I_i + I_{i-1} - 2\,O_{i-1});\quad U_D(t) = \frac{S(t) - S(t - D)}{D}
$$

Plain text: `A(t) / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for tc / 2 < t < tc, 1 from tc; I_i = A(i dt) / A - A((i - 1) dt) / A; O_i = O_i-1 + C (I_i + I_i-1 - 2 O_i-1), C = dt / (2 R + dt), O and I 0 before the grid; u_i = O_i / (dt sum O); S(t) the S-curve of u, U_D(t) = (S(t) - S(t - D)) / D with S between grid points linear; q_i = U_D(i dt) A x 1 mm per s; i = 0 to max(1, ceil(T / dt))`

**Sources**

- USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eqs. 47-50, pp. 58-59 (open) <https://www.hec.usace.army.mil/software/hec-hms/documentation/HEC-HMS_Technical%20Reference%20Manual_%28CPD-74B%29.pdf>
- USACE-HEC. HEC-HMS Technical Reference Manual (online, read 2026-11-19), chapter Transform, Clark Unit Hydrograph Model: the time-area curve of an elliptical watershed, O_t = CA I_t + CB O_t-1, CA = dt / (R + 0.5 dt), the unit hydrograph the mean of two outflows (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/clark-unit-hydrograph-model>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `tc_min` | $t_c$ | min | real | (0.0, inf), test bound high 4500.0 (ten times the longest time of concentration of the hand-offs (450 min)) | unstated | [1.0, 450.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: Kirpich's tc of the flow paths of the 27 watersheds, the default method of hydrograph generate, 1.04 to 450 min |
| `r_min` | $R$ | min | real | (0.0, inf), test bound high 10440.0 (ten times the longest R of the Polish calibrations, 17.4 h (Wałęga and Cupak 2013)) | unstated | [0.2, 1050.0]: Wałęga, A. and Cupak, A. (2013). In Węglarczyk, S. (ed.), Problemy obliczania przepływów ekstremalnych, Monografie Komitetu Gospodarki Wodnej PAN 35, pp. 145-151, table 2, p. 148: R of 12.14 and 17.4 h calibrated for the Stobnica (335.84 km2); and Hydrolog's R/tc of 0.2 to 1.5 times the typical tc of 1 to 450 min, R from 0.2 min |
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 1000000.0 (a million km2, five times the basin of the Vistula (194,000 km2) and four thousand times the largest watershed Hydrograf hands over) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 135 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |
| `duration_min` | $D$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |
| `total_duration_min` | $T$ | min | real | (0.0, inf), test bound high 57600.0 (ten times the longest default length of the typical ranges) | unstated | [7.0, 5760.0]: Hydrolog: the default length tc + 5 R + D over the typical ranges of tc, R and D, 1 + 5 x 0.2 + 5 = 7 to 450 + 5 x 1050 + 60 = 5,760 min |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `step_stable` | precondition | the time step is at most twice the storage constant, dt <= 2 R (to 1e-9 of 2 R for its rounding): beyond it the previous outflow has the negative weight (2 R - dt) / (2 R + dt) and the ordinates oscillate below 0 | Hydrolog ADR-0008, the conventions of routing: the window of non-negative weights of the Muskingum scheme, dt <= 2 K (1 - X), here X = 0 and K = R |
| `length_bounded` | precondition | the grid has at most a million ordinates | Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one |
| `representable` | precondition | float64 holds the first outflow of the reservoir, C A(dt) / A, as a normal number and 1 mm over the watershed per second of D, A x 1 mm / D | IEEE 754 double precision (float64), normal numbers from 2.2e-308 to 1.8e308 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `time_area_factor` | $1.414$ | 1.414 | - | USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eq. 50, p. 59: At / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for t >= tc / 2 |
| `time_area_exponent` | $1.5$ | 1.5 | - | USACE-HEC (2000). Hydrologic Modeling System HEC-HMS, Technical Reference Manual (CPD-74B, March 2000), Clark's unit hydrograph model, eq. 50, p. 59: At / A = 1.414 (t / tc)^1.5 for t <= tc / 2 and 1 - 1.414 (1 - t / tc)^1.5 for t >= tc / 2 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `times_min` | min | real_array | [0.0, inf) | 4 ulp of the bound |
| `ordinates_m3s` | m3/s per mm | real_array | [0.0, inf) | 4 ulp of the bound |
| `time_to_peak_min` | min | real | [0.0, inf) | 4 ulp of the bound |
| `peak_discharge_m3s` | m3/s per mm | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- times in min from the beginning of the rainfall; ordinates in m3/s per mm
- the time-area curve of HEC-HMS's elliptical watershed, 1.414 for the square root of 2 (the halves meet at 0.49992 and 0.50008, a step of 1.6e-4)
- the reservoir on the trapezoid rule, O_i = O_i-1 + C (I_i + I_i-1 - 2 O_i-1) with C = dt / (2 R + dt): HEC-HMS's O_t = CA I_t + CB O_t-1 and its mean of two outflows, the averaging moved from the outflow to the inflow, the same for a reservoir at rest
- the grid ends at T (ClarkIUH: tc + 5 R + D), where HEC-HMS stops at 0.995 of the volume; both divide the routed ordinates by their volume, one unit
- the unit hydrograph of D from the S-curve, S(t - D) read linearly between the grid points: D need not be a whole number of steps, and a D shorter than dt gives the hydrograph of D = dt
- R/tc outside 0.2 to 1.5 gives the notice outside_unverified_range of ClarkIUH (clark.r_tc_ratio): no source publishes that range, and the Polish calibrations of the Stobnica give 1.7 to 2.3 (Wałęga and Cupak 2013)

**Assumptions**

- tc is the translation time from the farthest point of the watershed; the time-area curve is that of an elliptical watershed unless one is known
- excess rainfall uniform over the watershed and in time over D

**Validation:** none: Clark (1945) and HEC-HMS give the model; its parameters tc and R are calibrated on gauged floods (HEC-HMS), and the sources give no error statistic

**Notices:** none

**Numerical traps (CMP-6.6)**

- `stability_bound`: test_clark_steps_at_and_beyond_the_stability_bound: dt = 2 R computes without a negative ordinate, dt beyond 2 R (1 + 1e-9) is refused by the precondition step_stable
- `many_small_terms`: test_clark_a_million_ordinates_hold_their_volume: the volume of up to a million ordinates by NumPy's pairwise sum and cumulative sums

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `time`: inputs times 2^e (`tc_min` e = 1.0, `r_min` e = 1.0, `duration_min` e = 1.0, `timestep_min` e = 1.0, `total_duration_min` e = 1.0) give outputs times 2^e (`times_min` e = 1.0, `ordinates_m3s` e = -1.0, `time_to_peak_min` e = 1.0, `peak_discharge_m3s` e = -1.0)
- scaling `area`: inputs times 2^e (`area_km2` e = 1.0) give outputs times 2^e (`ordinates_m3s` e = 1.0, `peak_discharge_m3s` e = 1.0)
- limit `hec_form`: the ordinates of D = dt are HEC-HMS's recursion of the reservoir with the mean of two outflows, on the same grid
- limit `hec_truncation`: HEC-HMS's end of the hydrograph at 0.995 of its volume gives the same time to peak and the peak within 0.5 %
- limit `unit_volume`: to the default length tc + 5 R + D the ordinates hold 1 mm over the watershed

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: HEC-HMS's recursion of the reservoir, O_t = CA I_t + CB O_t-1 with the mean of two outflows (HEC-HMS 2000 eqs. 47-49), on the formula's grid and time-area curve (`tests/unit/test_formulas_unit_hydrographs.py (limit hec_form)`)
- algorithm: the same recursion ended at 0.995 of the volume as HEC-HMS ends it and rescaled to one unit: the research case clark-hec-hms-trm-oracle (tc 120 min, R 60 min, dt 10 min, A 45.3 km2), the peak within 0.5 % (`tests/unit/test_formulas_unit_hydrographs.py (limit hec_truncation)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="uh_convolution"></a>
### Direct runoff of excess rainfall by discrete convolution with a unit hydrograph

`hydrolog.runoff.convolution.convolve_discrete` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_n = \sum_{m} P_{e,m}\,U_{n-m},\quad t_n = n\,\Delta t,\quad V = \Delta t \sum_n Q_n
$$

Plain text: `Q_n = sum over m of Pe_m * U_(n - m), n = 0 .. M + K - 2, Pe_m the excess of the interval starting at m dt, U_k the unit hydrograph's ordinate at k dt; t_n = n dt; V = sum(Q_n) dt`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 6.12, p. 92; examples 6.2 and 6.4, pp. 100-110 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- USDA-NRCS (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 16: Hydrographs (210-VI-NEH, March 2007), example 16-1, steps 4-10 and table 16-4, pp. 16-10 to 16-13 (open) <https://irrigationtoolbox.com/NEH/Part630_Hydrology/H_210_630_16.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `effective_precip_mm` | $P_{e,m}$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO)) | unstated | [0.0, 20.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 6.1, 6.2 and 6.4, tables 6.1, 6.3 and 6.4, pp. 94-110: effective rainfall of 0 to 15.3 mm per step |
| `unit_hydrograph_m3s` | $U_k$ | m3/s per mm | real_array | [0.0, inf), test bound high 100000.0 (the SCS peak of a million km2 at a time to peak of 2 h (1.04e5 m3/s per mm)) | unstated | [0.0, 15.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 6.2 and 6.4, tables 6.2 and 6.3, pp. 100-110: ordinates up to 1.911 m3/s per mm; NEH 630 example 16-1 (11.9 km2): 1.62 |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a daily rainfall series (E5b-07: tc 90.7 min at a step of 1440 min)) | unstated | [5.0, 60.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2); and KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: 5 min; KZGW 2017, annex 2, ex. 6.1 and 6.2 (1 h) and 6.4 (0.5 h), pp. 92-110 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `length_bounded` | precondition | the hydrograph has at most a million ordinates, M + K - 1 | Hydrolog's bound of a hydrograph's length (hydrolog.routing.reach.MAX_ORDINATES), a million ordinates: the routing of a hydrograph refuses a longer one |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `peak_discharge_m3s` | m3/s | real | [0.0, inf) | 4 ulp of the bound |
| `time_to_peak_min` | min | real | [0.0, inf) | 4 ulp of the bound |
| `total_volume_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `discharge_m3s` | m3/s | real_array | [0.0, inf) | 4 ulp of the bound |
| `times_min` | min | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: depths in mm, ordinates in m3/s per mm, discharges in m3/s
- Pe_m is the excess of the interval from m dt to (m + 1) dt and U_0 the ordinate at t = 0: Q_n at t = n dt is the response at the end of interval n, as KZGW eq. 6.12 and NEH example 16-1 align them (Q(0.6 h) = 0.12 in x UH(0.3 h))
- the unit hydrograph is that of the duration dt, the step of the rainfall
- V = dt sum(Q_n), the sum taken exactly (math.fsum)

**Assumptions**

- linearity and time invariance of the watershed's response to excess rainfall, uniform over the watershed

**Validation:** none: the convolution is the superposition that the unit hydrograph assumes; its sources report no agreement of their own with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `many_small_terms`: limit exact_sums: 200 steps of 0.001 mm against the sums in exact rational arithmetic
- `gap_propagation`: type cases effective_precip_mm-nan_element and unit_hydrograph_m3s-nan_element: a gap is refused before it spreads

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `effective_precip_mm` increasing, `unit_hydrograph_m3s` increasing
- scaling `rainfall`: inputs times 2^e (`effective_precip_mm` e = 1.0) give outputs times 2^e (`peak_discharge_m3s` e = 1.0, `total_volume_m3` e = 1.0, `discharge_m3s` e = 1.0)
- scaling `unit_hydrograph`: inputs times 2^e (`unit_hydrograph_m3s` e = 1.0) give outputs times 2^e (`peak_discharge_m3s` e = 1.0, `total_volume_m3` e = 1.0, `discharge_m3s` e = 1.0)
- scaling `time`: inputs times 2^e (`timestep_min` e = 1.0) give outputs times 2^e (`time_to_peak_min` e = 1.0, `total_volume_m3` e = 1.0, `times_min` e = 1.0)
- limit `exact_sums`: every ordinate equals its sum of products in exact rational arithmetic
- conservation `volume`: the volume is the excess times the unit hydrograph's volume, sum(Q) dt = sum(Pe) sum(U) dt

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/unit-hydrographs-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the ordinates as sums of products in exact rational arithmetic (fractions) (`tests/unit/test_formulas_unit_hydrographs.py (limit exact_sums)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="form_factor"></a>
### Horton's form factor of a watershed

`hydrolog.morphometry.geometric.form_factor` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
C_f = \frac{A}{L^2}
$$

Plain text: `Cf = A / L**2`

**Sources**

- Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, p. 929: Horton's (1932) form factor, the area of the basin over the square of its length (open) <https://doi.org/10.1080/02626660209493000>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik formy Cf = A / L^2 = B / L (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 20000.0 (20,000 km, half the circumference of the Earth (40,075 km at the equator): no two points of a watershed lie farther apart) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_reach` | physical | A <= pi L^2: the watershed lies within the circle of radius L about its outlet, L being the straight line to the farthest point of the divide or the longest flow path, which is not shorter | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `form_factor` | - | real | [0.0, 3.141592653589793] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- L the straight line from the outlet to the farthest point of the divide (Baścik 2006, p. 21), as WatershedGeometry describes length_km; Hydrograf hands over the longest flow path, which is not shorter, so with it the index of elongation is smaller (k larger) than with the straight line; Schumm's (1956) L, the longest dimension parallel to the main drainage line, and Baścik's Lm, the valley length, are other conventions
- A within the circle of radius L about the outlet bounds Cf by pi; with L the longest dimension of the watershed (the isodiametric inequality) by pi/4, the circle's value

**Assumptions**

None stated.

**Validation:** none: a geometric index, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases length_km-physical_low_*: Cf grows as L^-2, which the constraint within_reach bounds by pi; a length too short for the area is refused
- `gap_propagation`: type cases area_km2-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` increasing, `length_km` decreasing
- scaling `units_of_length`: inputs times 2^e (`area_km2` e = 2.0, `length_km` e = 1.0) give outputs times 2^e (none)
- scaling `area`: inputs times 2^e (`area_km2` e = 1.0) give outputs times 2^e (`form_factor` e = 1.0)
- limit `decimal`: Cf equals A / L^2 evaluated in decimal arithmetic at 50 digits
- limit `shapes`: a circle with L its diameter gives pi/4, a square with L its diagonal 1/2, a semicircle with L its radius pi/2

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: A / L^2 of the float inputs in decimal arithmetic at 50 digits, and the exact values of a circle, a square and a semicircle with pi summed by the decimal module's series (`tests/unit/test_formulas_shape.py (limits decimal and shapes)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="compactness_coefficient"></a>
### Gravelius's compactness coefficient of a watershed

`hydrolog.morphometry.geometric.compactness_coefficient` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
C_z = \frac{P}{2\sqrt{\pi A}}
$$

Plain text: `Cz = P / (2 * sqrt(pi * A))`

**Sources**

- Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (1), p. 922: K = P / (2 sqrt(pi A)) = 0.28 P / sqrt(A) (open) <https://doi.org/10.1080/02626660209493000>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik zwartości (Graveliusa) K = Oz / (2 sqrt(pi A)) (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `perimeter_km` | $P$ | km | real | (0.0, inf), test bound high 1000000.0 (a million km, 25 times the circumference of the Earth (40,075 km at the equator): no divide traced on a map is longer) | unstated | [0.17, 90.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: perimeters of 0.1756 to 84.46 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `isoperimetric` | physical | P^2 >= 4 pi A: no perimeter is shorter than the circle's of the same area (the isoperimetric inequality); a shorter one means A and P measured on different outlines | Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, pp. 921-922: the perimeter of any basin exceeds that of the circle of the same area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle |
| `within_float64` | precondition | P / (2 sqrt(pi A)) lies within float64: no watershed has a divide 10^150 times its width | Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, pp. 921-922: the perimeter of any basin exceeds that of the circle of the same area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `compactness_coefficient` | - | real | [1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- P the length of the divide as traced: it grows with the resolution of the map or DEM, as a divide is irregular at every scale, so the index does too (Bendjoudi and Hubert 2002, pp. 924-928)
- A and P of the same outline: Hydrograf takes A from the cells and P from the smoothed boundary, so a value near 1 is to be read with care

**Assumptions**

None stated.

**Validation:** none: a geometric index, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases area_km2-physical_low_*: the root of A in the denominator tends to 0 with A; the index stays finite down to the smallest positive float, or a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases area_km2-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` decreasing, `perimeter_km` increasing
- scaling `units_of_length`: inputs times 2^e (`area_km2` e = 2.0, `perimeter_km` e = 1.0) give outputs times 2^e (none)
- scaling `perimeter`: inputs times 2^e (`perimeter_km` e = 1.0) give outputs times 2^e (`compactness_coefficient` e = 1.0)
- limit `decimal`: Cz equals P / (2 sqrt(pi A)) evaluated in decimal arithmetic at 50 digits
- limit `shapes`: a circle gives 1, a square 2/sqrt(pi), a semicircle (pi + 2) / (pi sqrt(2))

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: P / (2 sqrt(pi A)) of the float inputs in decimal arithmetic at 50 digits, and the exact values of a circle, a square and a semicircle (`tests/unit/test_formulas_shape.py (limits decimal and shapes)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="circularity_ratio"></a>
### Miller's circularity ratio of a watershed

`hydrolog.morphometry.geometric.circularity_ratio` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
C_k = \frac{4\pi A}{P^2}
$$

Plain text: `Ck = 4 * pi * A / P**2`

**Sources**

- Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (2), p. 922: Miller's (1953) C = 4 pi A / P^2 (open) <https://doi.org/10.1080/02626660209493000>
- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.3): Ck = A / Ak = 4 pi A / P^2 (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik kolistości Ck = 4 pi A / Oz^2 (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `perimeter_km` | $P$ | km | real | (0.0, inf), test bound high 1000000.0 (a million km, 25 times the circumference of the Earth (40,075 km at the equator): no divide traced on a map is longer) | unstated | [0.17, 90.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: perimeters of 0.1756 to 84.46 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `isoperimetric` | physical | P^2 >= 4 pi A: no perimeter is shorter than the circle's of the same area (the isoperimetric inequality); a shorter one means A and P measured on different outlines | Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, pp. 921-922: the perimeter of any basin exceeds that of the circle of the same area, so K = P / (2 sqrt(pi A)) is at least 1, 1 for a circle |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `circularity_ratio` | - | real | [0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- P the length of the divide as traced: it grows with the resolution of the map or DEM, as a divide is irregular at every scale, so the index does too (Bendjoudi and Hubert 2002, pp. 924-928)

**Assumptions**

None stated.

**Validation:** none: a geometric index, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type cases area_km2-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` increasing, `perimeter_km` decreasing
- scaling `units_of_length`: inputs times 2^e (`area_km2` e = 2.0, `perimeter_km` e = 1.0) give outputs times 2^e (none)
- limit `decimal`: Ck equals 4 pi A / P^2 evaluated in decimal arithmetic at 50 digits
- limit `shapes`: a circle gives 1, a square pi/4, a semicircle 2 pi^2 / (pi + 2)^2
- limit `gravelius`: Ck Cz^2 = 1: Miller's ratio is Gravelius's coefficient to the power -2

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: 4 pi A / P^2 of the float inputs in decimal arithmetic at 50 digits, and the exact values of a circle, a square and a semicircle (`tests/unit/test_formulas_shape.py (limits decimal and shapes)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="elongation_ratio"></a>
### Schumm's elongation ratio of a watershed

`hydrolog.morphometry.geometric.elongation_ratio` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
C_e = \frac{2}{L}\sqrt{\frac{A}{\pi}}
$$

Plain text: `Ce = (2 / L) * sqrt(A / pi)`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.2): Cw = (2 / Lm) sqrt(A / pi), after Schumm (1956) (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik wydłużenia Cw = (2 / L) (A / pi)^0.5 (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 20000.0 (20,000 km, half the circumference of the Earth (40,075 km at the equator): no two points of a watershed lie farther apart) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_reach` | physical | A <= pi L^2: the watershed lies within the circle of radius L about its outlet, L being the straight line to the farthest point of the divide or the longest flow path, which is not shorter | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `elongation_ratio` | - | real | [0.0, 2.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- L the straight line from the outlet to the farthest point of the divide (Baścik 2006, p. 21), as WatershedGeometry describes length_km; Hydrograf hands over the longest flow path, which is not shorter, so with it the index of elongation is smaller (k larger) than with the straight line; Schumm's (1956) L, the longest dimension parallel to the main drainage line, and Baścik's Lm, the valley length, are other conventions
- A within the circle of radius L about the outlet bounds Ce by 2; with L the longest dimension of the watershed by 1, the circle's value

**Assumptions**

None stated.

**Validation:** none: a geometric index, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type cases area_km2-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` increasing, `length_km` decreasing
- scaling `units_of_length`: inputs times 2^e (`area_km2` e = 2.0, `length_km` e = 1.0) give outputs times 2^e (none)
- scaling `length`: inputs times 2^e (`length_km` e = 1.0) give outputs times 2^e (`elongation_ratio` e = -1.0)
- limit `decimal`: Ce equals (2 / L) sqrt(A / pi) evaluated in decimal arithmetic at 50 digits
- limit `shapes`: a circle with L its diameter gives 1, a square with L its diagonal sqrt(2/pi), a semicircle with L its radius sqrt(2)
- limit `form_factor`: Cf = pi Ce^2 / 4 for the same A and L

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: (2 / L) sqrt(A / pi) of the float inputs in decimal arithmetic at 50 digits, and the exact values of a circle, a square and a semicircle (`tests/unit/test_formulas_shape.py (limits decimal and shapes)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="lemniscate_ratio"></a>
### Chorley's lemniscate ratio k of a watershed

`hydrolog.morphometry.geometric.lemniscate_ratio` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
k = \frac{\pi L^2}{4A}
$$

Plain text: `k = pi * L**2 / (4 * A)`

**Sources**

- Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eqs. (3)-(5), pp. 922-923: Chorley et al. (1957) compare the basin with one loop of the lemniscate rho = l cos(k theta), of area pi l^2 / (4k), so k = pi l^2 / (4A) (open) <https://doi.org/10.1080/02626660209493000>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2: wskaźnik lemniskaty Cl = pi L^2 / (4A) (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 20000.0 (20,000 km, half the circumference of the Earth (40,075 km at the equator): no two points of a watershed lie farther apart) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_reach` | physical | A <= pi L^2: the watershed lies within the circle of radius L about its outlet, L being the straight line to the farthest point of the divide or the longest flow path, which is not shorter | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: the length of the watershed L is the straight line from the outlet to the farthest point of the divide; the maximum length Lm runs along the valley of the main river |
| `within_float64` | precondition | pi L^2 / (4A) lies within float64: no watershed is 10^150 times longer than wide | Bendjoudi, H. & Hubert, P. (2002). Le coefficient de compacité de Gravelius : analyse critique d'un indice de forme des bassins versants. Hydrological Sciences Journal 47(6): 921-930, eq. (5), p. 923 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `lemniscate_ratio` | - | real | [0.25, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- L the straight line from the outlet to the farthest point of the divide (Baścik 2006, p. 21), as WatershedGeometry describes length_km; Hydrograf hands over the longest flow path, which is not shorter, so with it the index of elongation is smaller (k larger) than with the straight line; Schumm's (1956) L, the longest dimension parallel to the main drainage line, and Baścik's Lm, the valley length, are other conventions
- Chorley's k with pi (the loop of the lemniscate), not the variant L^2 / (4A) of some secondary texts, which Hydrolog computed up to 0.8.1
- A within the circle of radius L about the outlet bounds k below by 1/4; with L the longest dimension of the watershed by 1, the circle's value

**Assumptions**

None stated.

**Validation:** none: a geometric index, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases area_km2-physical_low_*: k grows as 1/A; a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases area_km2-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `area_km2` decreasing, `length_km` increasing
- scaling `units_of_length`: inputs times 2^e (`area_km2` e = 2.0, `length_km` e = 1.0) give outputs times 2^e (none)
- scaling `length`: inputs times 2^e (`length_km` e = 1.0) give outputs times 2^e (`lemniscate_ratio` e = 2.0)
- limit `decimal`: k equals pi L^2 / (4A) evaluated in decimal arithmetic at 50 digits
- limit `shapes`: a circle with L its diameter gives 1, a square with L its diagonal pi/2, a semicircle with L its radius 1/2
- limit `form_factor`: k Cf = pi/4 for the same A and L
- limit `elongation_ratio`: k Ce^2 = 1 for the same A and L

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: pi L^2 / (4A) of the float inputs in decimal arithmetic at 50 digits, the exact values of a circle, a square and a semicircle, and the identities with Cf and Ce (`tests/unit/test_formulas_shape.py (limits decimal, shapes, form_factor and elongation_ratio)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="relief_ratio"></a>
### Relief ratio: the relief of a watershed over a length (Schumm)

`hydrolog.morphometry.terrain.relief_ratio` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
R_h = \frac{H_{max} - H_{min}}{L}
$$

Plain text: `Rh = (Hmax - Hmin) / L, L in m [m/m]`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.12): wskaźnik rzeźby Cs = (Hmax - Hmin) / Lm; eq. (1.2.15): the slope of a river, the drop from its source to its mouth over its length (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Wartalska, K. Hydrologia i ochrona wód, ćwiczenia, cz. 2: Podstawowe wskaźniki charakteryzujące zlewnię. Politechnika Wrocławska, course material, section 2.3: wskaźnik rzeźby zlewni Strahlera Jd = dH / L (open) <https://wis.pwr.edu.pl/download/IjJmY2BjNFWCQpYzskenQnH0gkIw4dLS8zLjlyTXULMRckZjYEKH0FdSl6CBQoKGAveTAPHAAqEWwVBThNdwtoXm5kPQ4,dGJn01DTQ1HGYZeTIYPzM9NWQ0IggOPCpufFZwKnZ7LB0lZjoJNX4YdRRgeAsnbyB0Iml_XkA/hydrologia_i_ochrona_wod_-_cz_2_10.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `elevation_min_m` | $H_{min}$ | m | real | (-inf, inf), test bound low -431.0 and high 8849.0 (the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of Jordan and Nepal)) | unstated | [100.0, 750.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m |
| `elevation_max_m` | $H_{max}$ | m | real | (-inf, inf), test bound low -431.0 and high 8849.0 (the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of Jordan and Nepal)) | unstated | [100.0, 750.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 20000.0 (20,000 km, half the circumference of the Earth (40,075 km at the equator): no two points of a watershed lie farther apart) | unstated | [0.05, 30.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: lengths (longest flow paths) of 0.0566 to 28.88 km |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `rises_above_outlet` | physical | Hmax > Hmin: a watershed drains to its outlet, so it rises above it | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.12): wskaźnik rzeźby Cs = (Hmax - Hmin) / Lm; eq. (1.2.15): the slope of a river, the drop from its source to its mouth over its length |
| `within_float64` | precondition | (Hmax - Hmin) / L lies within float64: no relief is 10^300 times its length | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.12): wskaźnik rzeźby Cs = (Hmax - Hmin) / Lm; eq. (1.2.15): the slope of a river, the drop from its source to its mouth over its length |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `percent` | $100$ | 100.0 | % per m/m | BIPM (2019). The International System of Units (SI), 9th edition, version 4.01, section 5.4.7: the symbol % (percent) is the number 0.01; the slopes of TerrainAnalysis in percent |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `relief_ratio` | m/m | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Rh in m/m (dimensionless), the relief in m over L converted from km to m by the units table; Baścik (2006) and Wartalska print it in m/km (per mille)
- the relief of the whole watershed, its highest point minus its outlet; Baścik (2006, p. 23) notes that hydrological practice may take the water level at the outlet
- L the length_km of the watershed for the relief ratio (Schumm's L is the longest dimension parallel to the main drainage line, Baścik's Lm the valley length); TerrainAnalysis gives the same ratio as the watershed slope, which is not the mean slope of the land, and over the channel length as the slope of the main channel, whose drop is then the watershed's relief, not the channel's head minus its mouth

**Assumptions**

None stated.

**Validation:** none: a ratio of measured quantities, which its sources compare with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: the relief Hmax - Hmin is a difference of inputs in the numerator: equal elevations are refused by the constraint rises_above_outlet (its boundary case)
- `singular_at_bound`: range cases length_km-physical_low_*: Rh grows as 1/L; a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases elevation_min_m-nan and the other inputs': a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `elevation_min_m` decreasing, `elevation_max_m` increasing, `length_km` decreasing
- scaling `units_of_length`: inputs times 2^e (`elevation_min_m` e = 1.0, `elevation_max_m` e = 1.0, `length_km` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: Rh equals (Hmax - Hmin) / (1000 L) of the float inputs in exact rational arithmetic

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/morphometry-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: (Hmax - Hmin) / (1000 L) of the float inputs in exact rational arithmetic (fractions), rounded once (`tests/unit/test_formulas_relief.py (limit exact_rational)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="hypsometric_integral"></a>
### Hypsometric integral of a watershed by the trapezoid of its curve (Strahler)

`hydrolog.morphometry.hypsometry.hypsometric_integral` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
HI = \sum_{i=0}^{n-2} \frac{a_i + a_{i+1}}{2\,(n-1)},\quad a_i = \frac{\sum_{z_j \ge t_i} A_j}{\sum_j A_j},\quad t_i = z_{min} + \frac{i}{n-1}(z_{max} - z_{min})
$$

Plain text: `HI = sum((a[i] + a[i+1]) / 2) / (n - 1), a[i] the share of the area at or above z_min + i (z_max - z_min) / (n - 1), i = 0 .. n-1`

**Sources**

- Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) (open) <https://pdfcoffee.com/strahler-1952-hypsometry-pdf-pdf-free.html>
- Pike, R.J. & Wilson, S.E. (1971). Elevation-relief ratio, hypsometric integral, and geomorphic area-altitude analysis. Geological Society of America Bulletin 82: 1079-1084, the elevation-relief ratio E = (mean - min) / (max - min) equals the hypsometric integral (not opened; the identity of the exceedance integral, integral of P(h >= x) dx over [0, 1] = E[h], is exact) (open)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `elevations_m` | $z$ | m | real_array | (-inf, inf), test bound low -431.0 and high 8849.0 (the lowest and the highest land on Earth: the shore of the Dead Sea at -431 m and Mount Everest at 8,849 m (CIA, The World Factbook, 2025, field Elevation of Jordan and Nepal)) | unstated | [100.0, 750.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: elevations of 100.0 to 722.68 m |
| `cell_areas` | $A_j$ | - | real_array | (0.0, inf), test bound high 149000000.0 (the land area of the Earth in km2 (CIA, The World Factbook, 2025, field Area: land): no cell is larger) | unstated | [1.0, 1.0]: Hydrolog's HypsometricCurve: cells of equal area unless cell_areas is given, as in every example and test of the project, src/hydrolog/morphometry/hypsometry.py; examples/04_morfometria.ipynb |
| `n_points` | $n$ | - | integer | [2.0, inf), test bound high 10001.0 (a hundred times the default 101: the trapezoid's bound 1/(2(n-1)) is then 5e-5) | unstated | [101.0, 101.0]: Hydrolog's HypsometricCurve: cells of equal area unless cell_areas is given, as in every example and test of the project, src/hydrolog/morphometry/hypsometry.py; examples/04_morfometria.ipynb |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one area per elevation | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |
| `positive_relief` | precondition | max(z) > min(z): the relative height h/H divides by the relief | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `hypsometric_integral` | - | real | [0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the curve of the relative area a/A at or above the relative height h/H (exceedance), Strahler's percentage hypsometric curve, sampled at n equally spaced heights from the lowest to the highest cell, h/H = 0 to 1
- HI by the trapezoid rule over the n points of the curve, n = 101 by default; the exact integral of the step curve of the cells is (mean - min) / (max - min) (Pike and Wilson 1971), from which the trapezoid departs by at most (a(0) - a(1)) / (2 (n - 1)), 0.005 for n = 101, most where much of the area lies at the outlet's elevation
- Strahler's stages (1952, text with Fig. 7): about 0.60 and above the inequilibrium (youthful) stage, 0.35 to 0.60 the equilibrium (mature) stage, below 0.35 the monadnock phase; Strahler gives them as rough limits and replaces old age by the monadnock phase
- cell areas in any one unit: only their shares count

**Assumptions**

None stated.

**Validation:** none: the integral describes a surface; Strahler (1952) relates its values to stages of erosion, not to observations of a quantity

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: the relief max - min divides the heights: equal elevations are refused by the precondition positive_relief (its boundary case and test_a_flat_surface_is_refused)
- `gap_propagation`: type cases elevations_m-nan_element and cell_areas-nan_element: a gap is refused, the spec allows none
- `many_small_terms`: test_many_cells_match_their_exact_sums: the shares of 200,001 cells against math.fsum

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `elevations`: inputs times 2^e (`elevations_m` e = 1.0) give outputs times 2^e (none)
- scaling `cell_areas`: inputs times 2^e (`cell_areas` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: HI equals the trapezoid of the curve in exact rational arithmetic
- limit `mean_based`: HI lies within (a(0) - a(1)) / (2 (n - 1)) of the exact integral (mean - min) / (max - min)
- limit `two_points`: with two thresholds HI is (1 + the highest cells' share) / 2

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the trapezoid of the curve in exact rational arithmetic (fractions), with exact thresholds (`tests/unit/test_formulas_hypsometry.py (limit exact_rational)`)
- exact: the exact integral (mean - min) / (max - min) in rational arithmetic, with the trapezoid's error bound (`tests/unit/test_formulas_hypsometry.py (limit mean_based)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="strahler_order"></a>
### Strahler's order of a stream below a junction

`hydrolog.network.stream_order.strahler_order` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
u = \begin{cases} 1 & \text{no upstream stream} \\ \max u_i + 1 & \text{two or more } u_i = \max u_i \\ \max u_i & \text{otherwise} \end{cases}
$$

Plain text: `u = 1 for a source; else u = max(upstream) + 1 if two or more upstream streams have the highest order, max(upstream) otherwise`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) (open) <https://doi.org/10.1029/TR038i006p00913>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `upstream_orders` | $u_i$ | - | real_array | [1.0, inf), test bound high 64.0 (an order of 64 needs 2^63 sources, more than the cells of any DEM) | unstated | [1.0, 3.0]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, orders 1 to 3 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `whole_orders` | physical | orders are whole numbers | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `order` | - | integer | [1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- a junction of three or more streams raises the order when at least two of them have the highest order
- Shreve's magnitude, the sum of the upstream magnitudes, is another ordering

**Assumptions**

None stated.

**Validation:** none: a classification of the streams of a network

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases strahler-* at the junctions of equal and unequal orders
- `gap_propagation`: type case upstream_orders-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `upstream_orders` increasing
- limit `source`: a stream without upstream streams is of order 1
- limit `pass_through`: a single upstream stream keeps its order
- limit `three_highest`: three upstream streams of the highest order raise it by one, as two do

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/morphometry-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the streams of a network counted as the connected runs of links of one order (union-find) (`tests/unit/test_formulas_network.py (test_streams_are_the_runs_of_links_of_one_order)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="bifurcation_ratio"></a>
### Horton's bifurcation ratio of the streams of two consecutive orders

`hydrolog.network.stream_order.bifurcation_ratio` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
R_b = \frac{N_u}{N_{u+1}}
$$

Plain text: `Rb = N_u / N_(u+1)`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) (open) <https://doi.org/10.1029/TR038i006p00913>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `n_lower` | $N_u$ | - | real | [2.0, inf), test bound high 10000000.0 (ten million streams: a D8 network on 10^8 cells, a 10 m DEM of 10,000 km2, has fewer sources than cells) | unstated | [2.0, 5.0]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 5 and 2 streams of orders 1 and 2 |
| `n_higher` | $N_{u+1}$ | - | real | [1.0, inf), test bound high 10000000.0 (ten million streams: a D8 network on 10^8 cells, a 10 m DEM of 10,000 km2, has fewer sources than cells) | unstated | [1.0, 2.0]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 2 and 1 streams of orders 2 and 3 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `whole_numbers` | physical | N_u and N_(u+1) are numbers of streams, whole numbers | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A |
| `two_streams_per_junction` | physical | N_u >= 2 N_(u+1): every stream of order u + 1 begins where at least two streams of order u end, and a stream ends once, so Rb >= 2 | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `bifurcation_ratio` | - | real | [2.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- N_u counts Strahler streams, a stream of order u running from where the order begins to its junction with a stream of an equal or higher order, not the links between junctions (StreamNetwork.get_statistics)
- Horton's ratios are defined on Strahler orders only: Shreve magnitudes get none

**Assumptions**

None stated.

**Validation:** none: Horton's law of stream numbers makes Rb nearly constant across orders; its sources report ranges of Rb, not its agreement with a quantity

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: none of the denominator is a difference: N_(u+1) >= 1 by its physical range, so no division by zero
- `gap_propagation`: type cases of every input with nan: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `n_lower` increasing, `n_higher` decreasing
- scaling `counts`: inputs times 2^e (`n_lower` e = 1.0, `n_higher` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: Rb is the exact quotient of the counts, rounded once

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: N_u / N_(u+1) in exact rational arithmetic (fractions) (`tests/unit/test_formulas_network.py (limit exact_rational)`)
- algorithm: the streams of a network counted as the connected runs of links of one order (union-find), another algorithm than the code's rule (`tests/unit/test_formulas_network.py (test_streams_are_the_runs_of_links_of_one_order)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="length_ratio"></a>
### Horton's length ratio of the streams of two consecutive orders

`hydrolog.network.stream_order.length_ratio` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
R_l = \frac{\bar L_{u+1}}{\bar L_u}
$$

Plain text: `Rl = mean L_(u+1) / mean L_u`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) (open) <https://doi.org/10.1029/TR038i006p00913>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `mean_length_lower_km` | $\bar L_u$ | km | real | (0.0, inf), test bound high 10000000.0 (ten million km: a drainage density of 10 km/km2 over a million km2, beyond any network a DEM of Poland gives) | unstated | [0.9, 5.2]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, mean lengths of 0.92, 1.45 and 5.2 km of orders 1-3 |
| `mean_length_higher_km` | $\bar L_{u+1}$ | km | real | [0.0, inf), test bound high 10000000.0 (ten million km: a drainage density of 10 km/km2 over a million km2, beyond any network a DEM of Poland gives) | unstated | [0.9, 5.2]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, mean lengths of 0.92, 1.45 and 5.2 km of orders 1-3 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_float64` | precondition | mean L_(u+1) / mean L_u lies within float64 | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `length_ratio` | - | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- mean lengths of Strahler streams: the total length of the segments of an order over the number of its streams (StreamNetwork.get_statistics), km
- Rl of the mean lengths, Horton's ratio; not the ratio of total lengths

**Assumptions**

None stated.

**Validation:** none: Horton's law of stream lengths makes Rl nearly constant across orders; its sources report no agreement with a quantity

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases mean_length_lower_km-physical_low_*: Rl grows as 1/mean L_u; a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases of every input with nan: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `mean_length_lower_km` decreasing, `mean_length_higher_km` increasing
- scaling `units_of_length`: inputs times 2^e (`mean_length_lower_km` e = 1.0, `mean_length_higher_km` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: Rl is the exact quotient of the mean lengths, rounded once

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: mean L_(u+1) / mean L_u in exact rational arithmetic (`tests/unit/test_formulas_network.py (limit exact_rational)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="drainage_density"></a>
### Drainage density: the length of the streams over the watershed's area

`hydrolog.network.stream_order.drainage_density` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
D_d = \frac{\sum L}{A}
$$

Plain text: `Dd = sum(L) / A [km/km2]`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) (open) <https://doi.org/10.1029/TR038i006p00913>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `total_length_km` | $\sum L$ | km | real | [0.0, inf), test bound high 10000000.0 (ten million km: a drainage density of 10 km/km2 over a million km2, beyond any network a DEM of Poland gives) | unstated | [0.7, 12.7]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, segments of 0.7 to 3.0 km, 12.7 km in all |
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_float64` | precondition | sum(L) / A lies within float64 | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `drainage_density` | km/km2 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the length of every stream of the network over the area of the watershed, km/km2; a network from a DEM depends on the threshold area of a stream, one from a map on its scale, so values compare only by one method

**Assumptions**

None stated.

**Validation:** none: a ratio of measured quantities; Baścik (2006) notes that it depends strongly on the map's scale and the threshold that defines a stream

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases area_km2-physical_low_*: Dd grows as 1/A; a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases of every input with nan: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `total_length_km` increasing, `area_km2` decreasing
- scaling `units_of_length`: inputs times 2^e (`total_length_km` e = 1.0, `area_km2` e = 2.0) give outputs times 2^e (`drainage_density` e = -1.0)
- limit `exact_rational`: Dd is the exact quotient of the length and the area, rounded once

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: sum(L) / A in exact rational arithmetic (`tests/unit/test_formulas_network.py (limit exact_rational)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="stream_frequency"></a>
### Stream frequency: the number of streams over the watershed's area

`hydrolog.network.stream_order.stream_frequency` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
F_s = \frac{\sum_u N_u}{A}
$$

Plain text: `Fs = sum(N_u) / A [1/km2]`

**Sources**

- Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A (open) <https://ruj.uj.edu.pl/server/api/core/bitstreams/c5c7e7e9-5f46-4b35-8758-05c7c8201f48/content>
- Strahler, A.N. (1957). Quantitative analysis of watershed geomorphology. Transactions, American Geophysical Union 38(6): 913-920, stream orders, the numbers and mean lengths of the streams of each order and Horton's laws (not opened; the definitions as Baścik 2006 gives them) (open) <https://doi.org/10.1029/TR038i006p00913>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `n_streams` | $\sum N_u$ | - | integer | [0.0, inf), test bound high 10000000.0 (ten million streams: a D8 network on 10^8 cells, a 10 m DEM of 10,000 km2, has fewer sources than cells) | unstated | [1.0, 8.0]: Hydrolog's example network tests/fixtures/network_segments.csv, the example of network stats in the catalog and docs/USAGE.md: 9 segments over 12 km2, 8 streams of orders 1-3 |
| `area_km2` | $A$ | km2 | real | (0.0, inf), test bound high 149000000.0 (the land area of the Earth, 148.94 million km2 (CIA, The World Factbook, 2025, field Area: land): no watershed is larger) | unstated | [0.0003, 250.0]: Hydrograf's watersheds handed to Hydrolog (Hydrograf 0.5.0.dev0, November 2026): the hand-offs recorded in Hydrolog's tests, Kamiennik to Świerzawa (134.97 km2), a network of 8 subcatchments and the Nysa Szalona network of 18, and the guide's Kamiennik to Świerzawa (37.22 km2), tests/fixtures/handoff_hydrograf*.json and tests/fixtures/kamiennik.json: areas of 0.00035 to 134.97 km2; Hydrograf computes hydrographs of watersheds up to 250 km2 (backend/api/endpoints/hydrograph.py) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `within_float64` | precondition | sum(N_u) / A lies within float64 | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eqs. (1.2.18)-(1.2.22): the density of the river network sum(L) / A, the bifurcation ratio N_u / N_(u+1), N_u the number of streams of order u, the ratio of the mean lengths of the streams of consecutive orders and the frequency of streams, the number of streams of all orders over A |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `stream_frequency` | 1/km2 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Strahler streams of all orders (StreamNetwork.n_streams), not the links between junctions; Hydrograf's stream frequency counts links of the BDOT10k network and says so

**Assumptions**

None stated.

**Validation:** none: a ratio of counted and measured quantities

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range cases area_km2-physical_low_*: Fs grows as 1/A; a value beyond float64 is refused by the precondition within_float64
- `gap_propagation`: type cases of every input with nan: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `n_streams` increasing, `area_km2` decreasing
- scaling `area`: inputs times 2^e (`area_km2` e = 1.0) give outputs times 2^e (`stream_frequency` e = -1.0)
- limit `exact_rational`: Fs is the exact quotient of the count and the area, rounded once

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: sum(N_u) / A in exact rational arithmetic (`tests/unit/test_formulas_network.py (limit exact_rational)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="usda_texture"></a>
### USDA soil texture class of clay, sand and silt amounts

`hydrolog.soil.texture.classify_usda_texture` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{class} = C \iff \exists j\ \forall (a, b, c, \sim, k) \in T_{C,j}:\ 100\,(a\,m_\mathrm{clay} + b\,m_\mathrm{sand} + c\,m_\mathrm{silt}) \sim k\,(m_\mathrm{clay} + m_\mathrm{sand} + m_\mathrm{silt})
$$

Plain text: `class = the class C of the table usda_texture_classes.csv for which every row (a, b, c, relation, k) of one alternative holds: 100 (a clay + b sand + c silt) relation k (clay + sand + silt)`

**Sources**

- Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 (open) <https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/GOVPUB-A-PURL-gpo113168.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `clay` | $m_\mathrm{clay}$ | shared unit | real | [0.0, inf), test bound high 10000.0 (ten times the largest amount of the ecosystem's data, 1000 g/kg of SoilGrids; the class depends on the shares only) | unstated | [0.0, 1000.0]: ISRIC - World Soil Information (2026). SoilGrids FAQ, 'Which soil properties are predicted': clay, sand and silt of the fine earth in g/kg, the data Kartograf downloads for Hydrolog's soil hsg: integers 0 to 1000 g/kg; soil texture takes percent (0 to 100) or g/kg |
| `sand` | $m_\mathrm{sand}$ | shared unit | real | [0.0, inf), test bound high 10000.0 (ten times the largest amount of the ecosystem's data, 1000 g/kg of SoilGrids; the class depends on the shares only) | unstated | [0.0, 1000.0]: ISRIC - World Soil Information (2026). SoilGrids FAQ, 'Which soil properties are predicted': clay, sand and silt of the fine earth in g/kg, the data Kartograf downloads for Hydrolog's soil hsg: integers 0 to 1000 g/kg; soil texture takes percent (0 to 100) or g/kg |
| `silt` | $m_\mathrm{silt}$ | shared unit | real | [0.0, inf), test bound high 10000.0 (ten times the largest amount of the ecosystem's data, 1000 g/kg of SoilGrids; the class depends on the shares only) | unstated | [0.0, 1000.0]: ISRIC - World Soil Information (2026). SoilGrids FAQ, 'Which soil properties are predicted': clay, sand and silt of the fine earth in g/kg, the data Kartograf downloads for Hydrolog's soil hsg: integers 0 to 1000 g/kg; soil texture takes percent (0 to 100) or g/kg |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `positive_total` | precondition | clay + sand + silt > 0 | Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `texture_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- amounts in any unit the three share (percent, g/kg), compared with their total: the class depends on the shares of clay + sand + silt only, which need not be 100 % (organic matter and gravel are outside the fine earth)
- USDA separates: sand 0.05 to 2 mm, silt 0.002 to 0.05 mm, clay below 0.002 mm (the PTG 2008 Polish classes use the same limits); the twelve classes cover every composition of the triangle, so no amount has an applicability range (unstated)
- 'X to less than Y percent' is X <= share < Y, 'more than X' is > X, 'X or more' is >= X, 'X or less' is <= X, 'more than 20 to 45 percent sand' (clay loam) is 20 < sand <= 45, as the Manual words each class
- the sand ranges the Manual also gives in words, sands 'more than 85 percent sand' and loamy sands 'between 70 and 90 percent sand', are implied by their other inequalities (silt + 1.5 clay < 15 gives sand > 85; silt + 1.5 clay >= 15 and silt + 2 clay < 30 give 70 < sand <= 90) and are not rows of the table
- float64 throughout, the amounts scaled by one power of two first; exact for integer amounts (total below 10**13); other amounts within a few units in the last place of a class limit may fall on either side of it, and where rounding lets two classes hold the first in the table's order is taken
- a zero total has no texture and is refused (precondition positive_total); the array variant pins it to loam as no data (Tier B usda_texture_codes)

**Assumptions**

- the amounts are of the fine earth (< 2 mm) of a mineral soil; the Manual's subclasses by sand size (coarse sand, fine sandy loam, ...) are not given

**Validation:** none: the classes are defined by the Manual, not fitted to observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: tests/unit/test_formulas_texture.py::test_every_row_of_the_table_at_its_limit_and_just_beyond: each row's limit on the integer percent and g/kg grids and one g/kg beyond, against the Manual's inclusive or exclusive wording; clay 20 and 27 % moved by math.nextafter
- `gap_propagation`: tests/unit/test_formulas_texture.py::test_a_gap_is_refused_or_kept_as_no_data: NaN is refused (outside_physical_range); a NaN or infinite amount of the array variant gives its cell the loam placeholder and classify_hsg masks it as no data

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `shared_unit`: inputs times 2^e (`clay` e = 1.0, `sand` e = 1.0, `silt` e = 1.0) give outputs times 2^e (none)
- limit `unit_free`: multiplying the three amounts by one positive factor (10 from percent to g/kg, 1000, 3, a power of two) leaves the class unchanged, also on the limits of the classes

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/texture-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- frozen: Kartograf 0.8.2, kartograf.hydrology.hsg.classify_usda_texture_array (its own copy of the rules), on all 5,151 integer percent and 501,501 integer g/kg compositions (`tests/oracles/kartograf_0_8_2_texture_percent.csv and tests/oracles/kartograf_0_8_2_texture_gkg.csv (written once by tests/oracles/kartograf_texture_oracle.py), compared by tests/unit/test_formulas_texture.py`)
- exact: the package table evaluated in exact rationals (fractions.Fraction) on both integer grids and on drawn integer compositions (`tests/unit/test_formulas_texture.py::test_the_table_in_rationals_agrees`)

**Tables (CMP-2.5)**

- `src/hydrolog/_data/tables/usda_texture_classes.csv` sha256 `b957a339f36ec7c0ee82ec1f25e286e401f26afeffa85dcccca24f9a4e61c381`: Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125; transcriptions compared in `tests/oracles/usda_texture_classes_first.csv (typed from the Manual's text by the author of the spec) against tests/oracles/usda_texture_classes_second.csv (typed independently by a second agent from the same pages), compared with the data file by tests/unit/test_formulas_texture.py`

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="texture_hsg"></a>
### Hydrologic soil group of a USDA texture class

`hydrolog.soil.texture.texture_to_hsg` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{HSG} = G(\mathrm{class})
$$

Plain text: `HSG = G(texture class), G the table texture_hsg.csv: TR-55 appendix A, with sandy loam B and clay loam and silty clay loam C as NEH 630 ch. 7's typical textures and silt B as silt loam`

**Sources**

- USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) (open) <https://www.hydrocad.net/pdf/TR-55%20Manual.pdf>
- USDA-NRCS (2009). National Engineering Handbook, Part 630 Hydrology, Chapter 7: Hydrologic Soil Groups (210-VI-NEH, January 2009), p. 7-2: the textures groups A to D 'typically' have; group B 'loamy sand or sandy loam', group C 'loam, silt loam, sandy clay loam, clay loam, and silty clay loam', well aggregated silt may be B (open) <https://www.hydrocad.net/neh/630ch7.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `texture_class` | $\mathrm{class}$ | - | choice of sand, loamy_sand, sandy_loam, loam, silt_loam, silt, sandy_clay_loam, clay_loam, silty_clay_loam, sandy_clay, silty_clay, clay | – | – | – |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `hsg` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- TR-55 appendix A gives the groups of disturbed soil profiles (urban areas, no significant compaction); the table applies them to every soil
- documented deviations from TR-55 appendix A: sandy loam B (TR-55 A), clay loam and silty clay loam C (TR-55 D), as NEH 630 ch. 7 p. 7-2 names the typical textures of groups B and C (Kartograf ADR-025, decision b): stricter than TR-55 for sandy loam, milder for the two clay loams
- silt, which TR-55 does not list, takes the group of silt loam, B; NEH 630 ch. 7 p. 7-2 puts well aggregated silt in group B
- NEH 630 ch. 7 would put loam and silt loam (and, by Ksat, silt) in C and loamy sand in B; the table keeps TR-55's groups for them (open question of ADR-0066)

**Assumptions**

- the group of a texture alone: no water table, impermeable layer, rock fragments, bulk density or structure (NEH 630 ch. 7, table 7-1)

**Validation:** none stated: TR-55 derives its texture groups from Brakensiek and Rawls (1983) for disturbed profiles; NEH 630 ch. 7 gives typical textures, not a fit

**Notices:** none

**Numerical traps (CMP-6.6)**

None applies: a lookup of a categorical key: no numeric class limit and no series

**Properties (CMP-6.5)**

- units: unit_specific
- limit `not_milder_as_ksat_falls`: along the classes in the order of falling saturated hydraulic conductivity of Rawls et al. (1982), sand, loamy sand, sandy loam, loam, silt loam, sandy clay loam, clay loam, silty clay loam, sandy clay, silty clay, clay, the group never gets milder (NEH 630 ch. 7 assigns the groups by falling Ksat; silt has no value)

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/hsg-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- frozen: Kartograf 0.8.2, kartograf.hydrology.hsg.TEXTURE_TO_HSG (its own copy of the table, ADR-025) (`tests/oracles/kartograf_0_8_2_texture_hsg.csv (written once by tests/oracles/kartograf_texture_oracle.py), compared by tests/unit/test_formulas_texture_hsg.py`)

**Tables (CMP-2.5)**

- `src/hydrolog/_data/tables/texture_hsg.csv` sha256 `f8e1d4b427ae6bb4c0abf7afbbbf9a70f3c32c42de0b5fe5a0ee2157daebef4a`: USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983); transcriptions compared in `tests/oracles/tr55_hsg_text_layer.csv (read from the PDF's text layer by tests/oracles/transcribe_tr55_hsg.py) and tests/oracles/kartograf_0_8_2_texture_hsg.csv (Kartograf 0.8.2's table), compared with the data file by tests/unit/test_formulas_texture_hsg.py`

**Tests by class (CMP §6):** reference cases (CMP-6.1); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5).

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
| `mean_width` | `hydrolog.morphometry.geometric.WatershedGeometry.width_km` | W = A / L, the mean width of the watershed [km] | – | L as length_km of WatershedGeometry (the straight line or the longest flow path); Baścik's B divides by the valley length Lm | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: średnia szerokość zlewni B = A / Lm |
| `midpoint_elevation` | `hydrolog.morphometry.terrain.TerrainAnalysis` | H_mean = (Hmin + Hmax) / 2, the mean elevation TerrainAnalysis assumes when none is given [m a.s.l.] | – | an approximation, with the notice mean_elevation_approximated where Hydrolog reports it; the area-weighted mean of the DEM (Baścik 2006, eq. 1.2.8, HypsometricCurve.mean_elevation) is to be preferred | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.5): the mean elevation approximated by the mean of the highest and the lowest |
| `hypsometric_curve` | `hydrolog.morphometry.hypsometry.HypsometricCurve.generate_curve` | relative heights h/H = (t - min) / (max - min) at n equally spaced thresholds t and the relative areas a/A of the cells at or above each | – | exceedance (area above), Strahler's percentage hypsometric curve; the first relative area is 1 | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |
| `area_weighted_mean_elevation` | `hydrolog.morphometry.hypsometry.HypsometricCurve.mean_elevation` | the mean elevation of the cells weighted by their areas [m a.s.l.] | – | numpy.average with the cell areas as weights | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.8): the mean elevation weighted by the areas between contours |
| `elevation_above_share` | `hydrolog.morphometry.hypsometry.HypsometricCurve.elevation_at_percentile` | the elevation of the first cell, from the highest down, at which the cumulative share of the area reaches the given percent [m a.s.l.] | – | the median elevation is the one with half of the area above it; no interpolation between cells | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |
| `streams_of_each_order` | `hydrolog.network.stream_order.StreamNetwork.get_statistics` | the number of Strahler streams of each order, their total and mean lengths [km] and the total length of the network [km] | – | a segment continues the stream of an upstream segment of its own order and begins one otherwise; the mean length is the total length of the order's segments over the number of its streams | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order |
| `usda_texture_codes` | `hydrolog.soil.texture.classify_usda_texture_array` | the class of spec usda_texture, cell by cell, as its code 1-12 (TEXTURE_CLASSES) | – | a cell without soil data - zero total, a NaN or an infinite amount - gets the code of loam (4) as a placeholder, which classify_hsg masks as no data; a negative amount is refused | Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 |
| `texture_hsg_codes` | `hydrolog.soil.texture.texture_to_hsg_array` | the group of spec texture_hsg of each texture code, as the raster code 1-4 for A-D | – | texture code 0 (no data) gives 0; a code outside 0-12 is refused | USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) |
| `hsg_of_amounts` | `hydrolog.soil.hsg.classify_hsg` | the group of spec texture_hsg of the class of spec usda_texture, cell by cell, as the raster code 1-4 for A-D | – | 0 (no data) for a cell with a NaN or infinite amount, an amount equal to its input's nodata tag, or all three amounts zero (the SoilGrids gap); a negative amount in a cell with data is refused | Kartograf ADR-025 (HSG from SoilGrids clay, sand and silt), ported to Hydrolog 0.8.0, raster codes uint8, 0 no data, 1-4 the groups A-D |

## Delegated computations (CMP-1.2)

| Computation | Library | Versions | Smoke case | Test |
|---|---|---|---|---|
| nash_shape_root | scipy.optimize.brentq | scipy>=1.10 (1.18.1 locked) | the root N of f(N) = (N-1)^N e^-(N-1) / Gamma(N) = f(2.55) on [1.1, 20] with xtol 1e-6 is 2.55 within 1e-6 (spec lutz) | `tests/unit/test_formulas_lutz.py::test_the_delegated_root_finder_finds_a_known_root` |
