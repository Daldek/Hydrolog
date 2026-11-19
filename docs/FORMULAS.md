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
| [Values of the duration curve equalled or exceeded on p % of the days (Weibull positions, linear interpolation)](#exceedance_values) | `hydrolog.statistics.duration.exceedance_values` | referenced | 1 | not measured |
| [Baseflow of a daily series by the Lyne and Hollick filter (standard approach of Ladson et al. 2013)](#lyne_hollick) | `hydrolog.statistics.baseflow.lyne_hollick_filter` | referenced | 1 | not measured |
| [Baseflow index: the volume of baseflow over the volume of flow](#baseflow_index) | `hydrolog.statistics.baseflow.baseflow_index` | referenced | 1 | not measured |
| [Recession constant of the total flow: the median daily ratio of runs of falling flow](#recession_constant) | `hydrolog.statistics.baseflow.recession_ratio` | oracle only | 1 | not measured |

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

<a id="exceedance_values"></a>
### Values of the duration curve equalled or exceeded on p % of the days (Weibull positions, linear interpolation)

`hydrolog.statistics.duration.exceedance_values` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_p = q_{(i)} + \theta\,\bigl(q_{(i+1)} - q_{(i)}\bigr),\quad i = \left\lfloor \tfrac{(n+1)\,p}{100} \right\rfloor,\quad \theta = \tfrac{(n+1)\,p}{100} - i,\quad q_{(1)} \ge \dots \ge q_{(n)}
$$

Plain text: `q(1) >= ... >= q(n) the n values with a value; h = (n + 1) p / 100, i = floor(h), theta = h - i; Q_p = q(i) + theta (q(i+1) - q(i)) for 1 <= i < n, q(1) for i < 1 and q(n) for i >= n`

**Sources**

- Vogel, R.M. and Fennessey, N.M. (1994). Flow-duration curves. I: New interpretation and confidence intervals. Journal of Water Resources Planning and Management 120(4), 485-504 (the authors' copy), pp. 488-489, eqs. (2a) and (3): Q_p,2 = (1 - theta) q(i) + theta q(i+1) with i = [(n + 1) p] and theta = (n + 1) p - i, the ordered observations q(i) plotted at the Weibull position p_i = i / (n + 1) (open) <https://sites.tufts.edu/richardvogel/files/2019/04/flowDuration1.pdf>
- NIST/SEMATECH (2012). e-Handbook of Statistical Methods, section 7.2.6.2, Percentiles, p (N + 1) = k + d: Y(p) = Y[k] + d (Y[k+1] - Y[k]) for 0 < k < N, Y[1] for k = 0 and Y[N] for k >= N, method R6 of Hyndman and Fan (1996); the example of twelve resistivities, 90th percentile 95.1981 ohm.cm (open) <https://www.itl.nist.gov/div898/handbook/prc/section2/prc262.htm>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $q$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the curve is homogeneous in the unit of the series (its scaling), so any bound tests its arithmetic: a million m3/s exceeds the discharge of every river, and a stage below its gauge's zero or a temperature may be negative, so the same bound holds below 0) | unstated | [1.24, 522.0]: IMGW-PIB, public hydrological data: the half-yearly characteristic flows (polr_Q) of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 (1997 absent), the lowest flow NNQ 1.24 m3/s (2015) and the highest WWQ 522 m3/s (2006), between which its daily mean flows lie |
| `exceedance_percent` | $p$ | % | real_array | (0.0, 100.0) | unstated | [0.1, 99.9]: Hydrolog's duration curve: CURVE_PERCENTS of hydrolog.statistics.duration, the percentages of every drawn curve, and the table's DEFAULT_PERCENTS; the thresholds Q70, Q90 and Q95 of Polish low-flow studies (Tokarczyk 2010, p. 32; Tomaszewski 2012, p. 68) lie between, 0.1 to 99.9 % |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `has_values` | precondition | n >= 1: at least one day with a value | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, section 7.2.6.2, Percentiles, p (N + 1) = k + d: Y(p) = Y[k] + d (Y[k+1] - Y[k]) for 0 < k < N, Y[1] for k = 0 and Y[N] for k >= N, method R6 of Hyndman and Fan (1996); the example of twelve resistivities, 90th percentile 95.1981 ohm.cm |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `exceedance_values` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- p is the exceedance percentage: the share of the days with a value on which the value is equalled or exceeded (krzywa sum czasów trwania wraz z wyższymi); Q_p is the (100 - p)-th percentile of the values
- the Weibull plotting position m / (n + 1) of the value of rank m from the highest, linear interpolation between positions: Q_p,2 of Vogel and Fennessey (1994, eq. 3), method R6 of Hyndman and Fan (NIST e-Handbook 7.2.6.2), numpy's method 'weibull' and R's quantile type 6
- beyond the extreme positions 100 / (n + 1) and 100 n / (n + 1) % the end values hold, as R6 sets k = 0 to the minimum and k >= N to the maximum; Vogel and Fennessey leave Q_p,2 undefined before the first position and recommend interpolating to q(n+1) = 0 after the last, which Hydrolog does not
- not the class method of Searcy (1959) and WMO-No. 1029 (sect. 6.1), whose share of a class is i / N, nor lfstat's Qxx (R's quantile type 7)
- equal values (ties) keep a position each and zeros are values; a day without a value (NaN) is left out, n counts the days with a value
- the series in any unit: the values of the curve in that unit (m3/s in the documents, cm for stages)
- the interpolation runs on the values divided by a power of two, so a difference of two values near the largest float does not overflow

**Assumptions**

- the values are those of one station over one period: the curve describes that period (the period-of-record curve of Vogel and Fennessey), not a climate
- no independence of the days is needed: the curve is descriptive, and its confidence intervals (Vogel and Fennessey, sect. 5) are not computed

**Validation:** none: a nonparametric estimate from the observed series itself; Vogel and Fennessey (1994) compare its sampling properties, not its agreement with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type case values-nan_element, limit constant_series and test_gaps_are_left_out: a day without a value is left out, never a NaN of the curve

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing, `exceedance_percent` decreasing
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`exceedance_values` e = 1.0)
- limit `plotting_positions`: at its position m / (n + 1) the curve gives the m-th largest value, halfway between two positions their mean
- limit `end_values_held`: before the first position the curve holds the largest value, after the last the smallest (NIST's k = 0 and k >= N)
- limit `constant_series`: a series of equal values (ties) gives that value at every percentage, and a day without a value changes nothing
- limit `exact_rational`: the values equal eq. (3) of Vogel and Fennessey in exact rational arithmetic, on whole numbers, decimal flows with zeros and ties, negative stages, gaps, one and two values and 400 seeded flows
- symmetry `mirror`: the negated series at 100 - p gives the negated value at p: the positions m / (n + 1) are symmetric

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/daily-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: eq. (3) of Vogel and Fennessey (1994), (1 - theta) q(i) + theta q(i+1), in exact rational arithmetic (fractions) (`tests/unit/test_formulas_daily.py (limit exact_rational)`)
- established: numpy.quantile with method='weibull' (NumPy 2.5) at the non-exceedance probability 1 - p / 100 (`tests/unit/test_formulas_daily.py (test_the_values_are_numpys_weibull_quantiles)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="lyne_hollick"></a>
### Baseflow of a daily series by the Lyne and Hollick filter (standard approach of Ladson et al. 2013)

`hydrolog.statistics.baseflow.lyne_hollick_filter` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
q_t = \alpha\,q_{t-1} + \frac{1 + \alpha}{2}\,(Q_t - Q_{t-1}),\quad b_t = \begin{cases} Q_t - q_t & q_t > 0 \\ Q_t & q_t \le 0 \end{cases}
$$

Plain text: `q_t = alpha q_(t-1) + (1 + alpha)/2 (Q_t - Q_(t-1)); b_t = Q_t - q_t if q_t > 0 else Q_t; passes alternately forward and backward, each on the baseflow of the pass before, over Q_31, ..., Q_2, Q_1, ..., Q_n, Q_(n-1), ..., Q_(n-30); q of each pass starts at the first value of its input; the baseflow of days 1 to n after the last pass, below 0 set to 0`

**Sources**

- Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, eqs. 1 and 2 (the filter); sect. 2.1 to 2.3 (reflection, initial values, passes); sect. 3, Tables 3 and 4 (the worked example) (open) <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
- Ladson, A.R. (2013). BFI.R and BFI_example.R, the code of Ladson et al. (2013), github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646 (2014-02-12), copied into tests/oracles/baseflow/, BFI.R: FirstPass, BackwardPass, ForwardPass and BFI.calc (open) <https://github.com/TonyLadson/BaseflowSeparation_LyneHollick>
- Nathan, R.J. and McMahon, T.A. (1990). Evaluation of automated techniques for base flow and recession analyses. Water Resources Research 26(7), 1465-1473, the filter with three passes and alpha 0.925 for daily flows, as quoted by Ladson et al. (2013), sect. 1.1 and 2.5, and by Murphy et al. (2009), p. 16 (author-provided) <https://doi.org/10.1029/WR026i007p01465>
- Murphy, R., Graszkiewicz, Z., Hill, P., Neal, B., Nathan, R. and Ladson, T. (2009). Australian Rainfall and Runoff Revision Project 7: Baseflow for Catchment Simulation, Stage 1 report, P7/S1/004, Engineers Australia, p. 15, eq. 7 (the filter); p. 16 (three passes, forward, backward and forward; alpha 0.925 of Nathan and McMahon 1990 for daily data) (open) <https://www.arr-software.org/pdfs/ARR_Project07_Stage1_Final%20Report.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $Q_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of the series (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river (the Amazon's floods reach about 300,000 m3/s)) | unstated | [0.5, 125.0]: IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s |
| `alpha` | $\alpha$ | - | real | (0.0, 1.0) | [0.9, 0.98]: Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.5, pp. 9-10: Nathan and McMahon (1990) found 0.9, 0.925 and 0.95 satisfactory against manual separation, and 0.98 matched chemical tracers better than 0.925 in 9 catchments; sect. 3.1, p. 16: alpha 'anywhere in the range 0.9 to 0.98' | [0.925, 0.98]: Hydrolog's catalog and tests: the defaults of stats baseflow (alpha 0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification, src/hydrolog/catalog/groups/stats.py (stats baseflow); tests/unit/test_station_regime.py (TestBaseflow) |
| `passes` | $N$ | - | integer | [1.0, inf), test bound high 99.0 (99 passes far exceed the 9 that Ladson et al. (2013, sect. 2.3) recommend for hourly data, and only cost time) | unstated | [3.0, 3.0]: Hydrolog's catalog and tests: the defaults of stats baseflow (alpha 0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification, src/hydrolog/catalog/groups/stats.py (stats baseflow); tests/unit/test_station_regime.py (TestBaseflow) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `longer_than_reflection` | precondition | n > 30 | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.1, p. 7: 'the data set must be longer than the amount of reflection'; BFI.R, l. 297 |
| `odd_passes` | precondition | passes odd and passes >= 3 | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.2 and 2.3, pp. 8-9: three passes for daily data, in order forward, backward, forward; BFI.R, l. 290: 'passes must be odd and greater than 2' |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `reflected_values` | $30$ | 30.0 | d | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.1, pp. 6-7; BFI.R, n.reflect = 30 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `baseflow` | m3/s | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the standard approach as Ladson et al. worked it in their spreadsheet, Table 4 and BFI.R: the quickflow is kept unclipped, negative too, as the state of the next day (Table 4, notes d to f), not set to 0 as the printed eq. 1 ('q_f = 0 otherwise') and Murphy et al. (2009) eq. 7 ('subject to q_f(i) >= 0') read
- 30 values reflected at each end without repeating the end value: Q_31, ..., Q_2 before the series and Q_(n-1), ..., Q_(n-30) after it (sect. 2.1)
- the quickflow of each pass starts at the first value of its input: Q_31 for the first pass, the last baseflow of the pass before for a backward pass and its first for a forward one (sect. 2.2)
- an odd number of passes, alternately forward and backward, so that the last runs forward (sect. 2.3: three for daily data, nine for hourly)
- the baseflow below 0 is set to 0 after the last pass, and the reflected values are dropped (BFI.R, BFI.calc)
- the series in any unit, the baseflow in the same (sect. 2: 'In general the units of flow are not important')
- daily data without a gap: a gap is refused; baseflow_separation filters each gapless span of a series with gaps (Tier B baseflow_spans)

**Assumptions**

- the quickflow is the high-frequency part of the hydrograph and the baseflow the low-frequency rest; the filter has no physical basis (Ladson et al., sect. 1)
- the start of each pass is an end effect that the reflection damps but does not remove: a constant series of 10 gets the baseflow 6.78 on its first day and the BFI 0.983 over 400 days; Ladson et al. (sect. 2.1) found the effect of the reflection on the BFI negligible from about 300 days

**Validation:** Ladson et al. (2013, sect. 2.5, Table 2, Fig. 2): on 9 Australian catchments the BFI with alpha 0.98 matched chemical-tracer estimates better than with 0.925, with large scatter; Nathan and McMahon (1990) found alpha 0.9 to 0.95 satisfactory against manual separation on 122 catchments of 4.2 to 210 km2 (as quoted by Ladson et al.)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `stability_bound`: test_alpha_next_to_one_keeps_the_baseflow_within_the_flow: alpha just below 1, where the quickflow hardly decays, against the exact recursion; alpha = 1 is refused (range case alpha-physical_high)
- `gap_propagation`: type case values-nan_element: a gap is refused; test_a_gap_parts_the_spans: baseflow_separation filters around it
- `many_small_terms`: test_a_long_series_matches_the_exact_recursion: the quickflow sums alpha-weighted differences over 3,000 days, against Fraction arithmetic

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`baseflow` e = 1.0)
- limit `no_flow`: a series without flow has no baseflow
- conservation `baseflow_within_flow`: 0 <= b_t <= Q_t on every day: each pass takes a positive quickflow away from its input (eq. 2) and the last sets b < 0 to 0

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/baseflow-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the recursion of Ladson et al. (sect. 2.1 to 2.3) in exact rational arithmetic (fractions), written as loops over the padded series (`tests/unit/test_formulas_baseflow.py::test_the_filter_is_the_exact_recursion`)
- frozen: Ladson's BFI() of BFI.R (ReturnQbase = TRUE) run by R 4.5.3 on the Bass River and a seeded 730-day series, alpha 0.9 to 0.987, 3, 5 and 9 passes (`tests/oracles/baseflow/lyne_hollick_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="baseflow_index"></a>
### Baseflow index: the volume of baseflow over the volume of flow

`hydrolog.statistics.baseflow.baseflow_index` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{BFI} = \frac{\sum_t b_t}{\sum_t Q_t}
$$

Plain text: `BFI = sum(b_t) / sum(Q_t) over the days with both values`

**Sources**

- Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, p. 5: 'the ratio of the baseflow volume (calculated from q_b) to the volume of streamflow (q) over a specified period'; sect. 2.4, p. 9: 'the sum of baseflow divided by the sum of total flow over the period of available raw data segments' (open) <https://tonyladson.wordpress.com/2013/10/01/a-standard-approach-to-baseflow-separation-using-the-lyne-and-hollick-filter/>
- Ladson, A.R. (2013). BFI.R and BFI_example.R, the code of Ladson et al. (2013), github.com/TonyLadson/BaseflowSeparation_LyneHollick, commit 8d09646 (2014-02-12), copied into tests/oracles/baseflow/, BFI.R, BFI.calc: BFI.value <- sum(Qbase)/sum(Qin) (open) <https://github.com/TonyLadson/BaseflowSeparation_LyneHollick>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.2, pp. 43-44: 'BFI = V_baseflow/V_total'; annual BFI from the volumes of each year (open) <https://library.wmo.int/idurl/4/32176>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $Q_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of the series (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river (the Amazon's floods reach about 300,000 m3/s)) | unstated | [0.5, 125.0]: IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s |
| `baseflow` | $b_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of the series (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river (the Amazon's floods reach about 300,000 m3/s)) | unstated | [0.5, 125.0]: IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `baseflow_not_above_flow` | physical | b_t <= Q_t on every day with both values | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, eq. 2: q_b = q - q_f with q_f >= 0 |
| `same_days` | precondition | len(b) = len(Q) | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.4, p. 9: baseflow statistics 'only from time steps in which raw data were available' |
| `positive_flow_volume` | precondition | sum(Q_t) > 0 | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 1.1, p. 5: a ratio to the volume of streamflow, undefined without flow |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `bfi` | - | real | [0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the volumes are the sums of the daily values (each day the same length), summed exactly once rounded (math.fsum)
- a day counts when it has both a discharge and a baseflow; with gaps the index is the ratio of the sums over the days with values (Ladson et al., sect. 2.4), not the mean of the spans' indices weighted by their lengths that BFI.R computes
- the series in any unit: the index has none

**Assumptions**

None stated.

**Validation:** none: the definition of the index

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case positive_flow_volume-violated: no flow is refused before the division; test_a_trickle_has_a_finite_index: the smallest flows divide without underflow
- `gap_propagation`: test_a_day_without_a_value_is_left_out: a gap in either series leaves the day out of both sums
- `many_small_terms`: test_a_long_series_sums_exactly: 50,000 days against the exact rational sums

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `baseflow` increasing, `values` decreasing
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0, `baseflow` e = 1.0) give outputs times 2^e (`bfi` e = 0.0)
- limit `all_baseflow`: a flow that is all baseflow has BFI = 1
- limit `no_baseflow`: a flow without baseflow has BFI = 0

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/baseflow-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the ratio of the sums in exact rational arithmetic (fractions) (`tests/unit/test_formulas_baseflow.py::test_the_index_is_the_exact_ratio`)
- frozen: the BFI that Ladson's BFI() of BFI.R reports, run by R 4.5.3, of the filter's baseflow (`tests/oracles/baseflow/lyne_hollick_bfi_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="recession_constant"></a>
### Recession constant of the total flow: the median daily ratio of runs of falling flow

`hydrolog.statistics.baseflow.recession_ratio` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
k = \operatorname{median}\left\{\frac{Q_{t+1}}{Q_t}\right\},\quad T_{1/2} = \frac{\ln 2}{-\ln k}
$$

Plain text: `k = median of Q_(t+1) / Q_t over the runs of at least min_days consecutive days with Q_t > 0 and Q_(t+1) < Q_t; half-life = ln 2 / (-ln k) (0 for k = 0)`

**Sources**

- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45, eqs. 5.1 to 5.3: Q_t = Q_0 exp(-t/C), k = Q_t/Q_(t-1), C = -dt/ln(k); 'A minimum length in the order of five to seven days is, however, commonly used' (open) <https://library.wmo.int/idurl/4/32176>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $Q_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of the series (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river (the Amazon's floods reach about 300,000 m3/s)) | unstated | [0.5, 125.0]: IMGW-PIB, public hydrological data: daily discharge of the Nysa Kłodzka at Kłodzko (station 150160180) in 2010, files codz_2010_01 to codz_2010_12; and Hydrolog's synthetic station of the GUI guide, tests/fixtures/station_daily.csv, Kłodzko 2010: 4.93 to 96.0 m3/s; station_daily.csv, 2018-11 to 2023-10: 0.52 to 122.34 m3/s |
| `min_days` | $m$ | d | integer | [1.0, inf), test bound high 365.0 (a segment of a year of falling daily flow; longer ones only test the count) | unstated | [5.0, 5.0]: Hydrolog's catalog and tests: the defaults of stats baseflow (alpha 0.925, passes 3, recession segments of 5 days), with which Obserwator calls it, and alpha 0.98 of the worked example of Ladson et al. (2013) in its verification, src/hydrolog/catalog/groups/stats.py (stats baseflow); tests/unit/test_station_regime.py (TestBaseflow) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `recession_segment` | precondition | a run of at least min_days days with 0 < Q_(t+1) / Q_t < 1 | WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45: the recession is analysed on segments of a minimum length |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `k` | - | real | [0.0, 1.0) | 4 ulp of the bound |
| `half_life_days` | d | real | [0.0, inf) | 4 ulp of the bound |
| `n_segments` | - | integer | [1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- k is the daily ratio Q_(t+1) / Q_t of WMO-No. 1029 eq. 5.2, and the half-life ln 2 / (-ln k) is C ln 2 of its eq. 5.3
- segments of Hydrolog's own rule: every run of at least min_days falls, from the first day after a peak, no threshold (WMO starts below Q70 and two days after a peak, on segments of seven days, and fits them by regression)
- the median of all the ratios of all the segments pooled, not a regression through the origin (WMO's master recession curve) nor the mean of the segments' constants (WMO's individual recession segments)
- a fall is strict: a day of equal flow (a tie) ends a run, as a rise does
- a day without a value or a day without flow (Q_t = 0) ends a run; a fall to 0 is the last ratio of its run, so k = 0 and a half-life of 0 only when min_days is 1

**Assumptions**

- the recession is exponential within each segment (WMO-No. 1029 eq. 5.1)
- the series is daily: k is per day and the half-life in days

**Validation:** none: the median ratio of the total flow is Hydrolog's own estimator; on WMO-No. 1029's Ngaruroro example (1963-1989) it gives k = 0.932 where WMO's master recession curve gives 0.9602 and lfstat's MRC 0.954 (the research of 2026-11-18): its segments include the quickflow after a peak

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: test_a_ratio_next_to_one_has_a_finite_half_life and test_a_fall_to_no_flow_has_a_half_life_of_zero: ln k at both ends of (0, 1)
- `gap_propagation`: test_a_gap_ends_a_segment: a day without a value ends a run and is never a ratio

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`k` e = 0.0, `half_life_days` e = 0.0)
- limit `exponential_recession`: two recessions Q_t = Q_0 0.95^t parted by a rise: k = 0.95 and the half-life ln 2 / (-ln 0.95), from both segments

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the runs found by a scan of the days and the median of their ratios in exact rational arithmetic (fractions, statistics.median) (`tests/unit/test_formulas_baseflow.py::test_the_recession_constant_is_the_exact_median`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
| `duration_curve_days` | `hydrolog.statistics.duration.duration_curve` | the days the curve and the classes take: every day with a value, or only those of one calendar month (month); their count n_values, minimum, maximum, mean and median, the curve at CURVE_PERCENTS and the table at exceedance_percents (spec exceedance_values), and the hydrological years (1 November - 31 October, named after the year of their end) of those days: first_year, last_year and period_years | – | the total-period curve of all the days of the record (Searcy 1959, p. 3; WMO-No. 1029, sect. 6.1); a day whose value is NaN or not finite has no value and is left out, not filled; a month's curve takes that calendar month of every year; the dates increase strictly, one value a day | Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology, Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 3: the total-period method, the days of each class cumulated from the highest class; figs. 4-5 (form 9-217c), p. 9: the days equal to or greater than a class limit and less than the next |
| `duration_classes` | `hydrolog.statistics.duration.duration_curve` | classes of equal width w, [k w, (k + 1) w) from the multiple of w at or below the smallest value to the class of the largest, or bin_count classes of equal steps of log10 between the smallest positive and the largest value, whose end edges are those values and which count the positive values only; a value v is in the class with lower <= v < upper, the highest class also holding its upper edge; per class from the highest down: its days, their share of the days counted [%], the days of the class and every higher one (including higher) and of the class and every lower one (including lower), and its days by hydrological month, November to October; the modal class has the most days, the lowest one of equal counts | – | the days counted from the highest class down, a class holding the days equal to or greater than its lower limit and less than the next (Searcy 1959, figs. 4-5); the edges of equal widths are computed in decimal arithmetic on the shortest decimal forms of the values and the width, so a value written on a class bound starts its class (0.3 with the width 0.1 is in [0.3, 0.4); ADR-0048); the edges are the floats nearest those bounds | Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology, Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 3: the total-period method, the days of each class cumulated from the highest class; figs. 4-5 (form 9-217c), p. 9: the days equal to or greater than a class limit and less than the next |
| `threshold_runs` | `hydrolog.statistics.events.threshold_runs` | the runs of consecutive days flagged beyond a threshold; two runs parted by fewer than max_gap_days days (without a value or not beyond) merge into one, with the days between them; runs shorter than min_duration_days, counted with the days merged in, are dropped; each run is the positions of its first and last day, inclusive, in time order | – | the pooling of the inter-event time method: runs pool when the gap is less than t_min = max_gap_days days (WMO-No. 1029, p. 72; lfstat's pool_it, 'inter-event time is less than tmin'), where Fleig et al. (2006) write tau_i <= t_c in their formula against 'less than' in their text; max_gap_days 4 pools gaps of 1 to 3 days, as the program NIŻÓWKA pools low flows parted by 3 days (Tokarczyk 2010, p. 34) and Tomaszewski (2012, pp. 68-69) breaks of at most 3 days; the duration of a pooled run includes the gap, the full drought duration of Fleig et al. (2006, eq. 1) and lfstat's duration, while WMO-No. 1029 (eq. 8.1(a)), NIŻÓWKA (Tokarczyk 2010, p. 34) and Tomaszewski (2012, fig. 14) add the durations of the runs without the gap (the real duration, days_beyond of threshold_events); the minimum duration applies to the full duration after pooling (Fleig et al. apply d_min to the real one); 0 pools nothing | WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.), sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the threshold and ends as soon as it returns above it, with its duration, volume, minimum flow and time of occurrence; the IT method pools deficits that occur less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 (eqs. 8.1) |
| `threshold_events` | `hydrolog.statistics.events.threshold_events` | the series laid on the calendar of its days; a day is beyond the threshold when its value is >= threshold (above) or < threshold (below); the events are the threshold_runs of those days; per event its first and last day, duration in calendar days (the days merged in included), days beyond, days without a value, peak (the largest value above, the smallest below, dated by its first day), the hydrological year of its first day and whether the day before (after) it has no value; per hydrological year with a value its days beyond, events starting in it, days with a value and calendar days (365 or 366); the totals of the period | – | a day at the threshold is beyond it above it and not below it; a day whose date is absent or whose value is NaN or not finite has no value and is never beyond; an event counts in the hydrological year (1 November - 31 October, named after the year of its end) in which it starts; the dates increase strictly | WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.), sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the threshold and ends as soon as it returns above it, with its duration, volume, minimum flow and time of occurrence; the IT method pools deficits that occur less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 (eqs. 8.1) |
| `low_flow_sequences` | `hydrolog.statistics.low_flows.LowFlowAnalysis.detect_sequences` | the flows laid on the calendar of their dates; the runs of days with a value below the threshold T, Q < T (threshold_runs, by default min_duration_days 5 and max_gap_days 4); per sequence its duration in calendar days (gap days included), the minimum and the mean of its days with a value, the deficit sum(max(T - Q, 0)) over its days with a value in the unit of the series times a day, its days without a value and whether the day before (after) it has no value; the sum of the deficits, the longest duration and the number of sequences | – | below is Q < T, as WMO-No. 1029 (p. 71) and the IMGW-PIB glossary (29, 'niższe od') say, not Q <= T of Yevjevich in Tokarczyk (2010, p. 33) or of lfstat; the deficit of a pooled sequence is the sum of the deficits of its runs, the excess of the days between them not subtracted (Fleig et al. 2006, eq. 2; WMO-No. 1029, eq. 8.1(b); lfstat's vbt, while lfstat's volume subtracts it); a day without a value adds no deficit and is a gap day; the defaults are NIŻÓWKA's minimum of 5 days and pooling across 3 days (Tokarczyk 2010, p. 34); any finite threshold, so a stage below its gauge's zero too | Fleig, A.K., Tallaksen, L.M., Hisdal, H. and Demuth, S. (2006). A global evaluation of streamflow drought characteristics. Hydrology and Earth System Sciences 10, 535-552, sect. 2.1, p. 539, eqs. (1) and (2): the full duration of a pooled drought runs from the first day of the first event to the last day of the last, the excess periods included, and its deficit volume is the sum of the pooled deficits |
| `low_flow_deficit_volumes` | `hydrolog.operations.stats.stats_low_flow_sequences` | the deficit of a discharge series in m3/s as a volume, deficit_volume_m3 = deficit x 86,400 s/d [m3], of each sequence, of each hydrological year and of the period; None for a stage (parameter H); a sequence counts in the hydrological year of its first day, with its whole duration and deficit | day = 86400 s/d (BIPM (2019), The International System of Units (SI), 9th edition, version 4.01, Table 8, non-SI units accepted for use with the SI) | the day of 86,400 s (the SI's non-SI day, BIPM 2019, table 8, from the units table of nogat_formulas): the daily deficits [m3/s] times the days give m3, the deficit volume of WMO-No. 1029 (sect. 8.3 (c)(iii), 'the sum of the daily deficit flows multiplied by the duration in days'); Tokarczyk (2010, p. 34, eq. 1) sums (Q0 - Q_t) Δt with Δt a day | WMO (2008). Manual on Low-flow Estimation and Prediction, WMO-No. 1029, Operational Hydrology Report No. 50 (Gustard, A. and Demuth, S., eds.), sect. 8.2, pp. 71-72: a deficit starts when the flow goes below the threshold and ends as soon as it returns above it, with its duration, volume, minimum flow and time of occurrence; the IT method pools deficits that occur less than t_min days apart, d_pool = d_i + d_i+1 and v_pool = v_i + v_i+1 (eqs. 8.1) |
| `runoff_volumes` | `hydrolog.statistics.volumes.runoff_volumes` | the volume of a day V = Q x 86,400 s [m3] for its mean discharge Q [m3/s]; the volume of a month and of a hydrological year: the sum of the volumes of its days with a value; complete: every day of it has a value; the mean annual volume over the complete years and the mean volume of each month (November to October) over its complete months; the cumulative volume of a year at the end of each of its days, and the mean of the cumulative volumes of the complete years over their first 365 days | day = 86400 s/d (BIPM (2019), The International System of Units (SI), 9th edition, version 4.01, Table 8, non-SI units accepted for use with the SI) | the day of 86,400 s (BIPM 2019, table 8, from the units table of nogat_formulas); the hydrological year 1 November - 31 October, named after the year of its end, 366 days when it holds 29 February; a day whose value is NaN or not finite, or whose date is absent, adds nothing and makes its month and year incomplete; the 366th day of a leap year is not in the mean cumulative volume; the dates increase strictly | IMGW-PIB, Słownik hydrologiczny (glossary of terms used in hydrological forecasts), entry 54 (rok hydrologiczny); BIPM (2019), The International System of Units (SI), 9th edition, table 8 (the day, d = 86 400 s), the hydrological year in Poland from 1 November (00:00 UTC) to 31 October (23:59 UTC); 1 d = 24 h = 86 400 s |
| `baseflow_spans` | `hydrolog.statistics.baseflow.baseflow_separation` | the daily series is laid on a calendar of consecutive days (an absent date is a day without a value); each gapless span of at least 60 days is filtered on its own (spec lyne_hollick), reflected at both of its ends; a day of a shorter span has no baseflow; series_baseflow is the baseflow of each day of series_year, by default the last complete hydrological year | min_span_days = 60.0 d (Hydrolog's own rules, ADR-0031: Regime, seasonality, harmonics, Sen's slope and baseflow of a station, point 5: the filter on each gapless span of at least 60 days, a year's index from 300 days with a baseflow (no published source; Ladson et al. 2013 filter every segment longer than the 30 reflected values, sect. 2.1 and 2.4)) | spans of at least 60 days are Hydrolog's own rule; Ladson et al. (2013, sect. 2.4) filter every segment of non-missing values and their BFI.R every one longer than the 30 reflected values | Ladson, A.R., Brown, R., Neal, B. and Nathan, R. (2013). A standard approach to baseflow separation using the Lyne and Hollick filter. Australasian Journal of Water Resources 17(1), 25-34 (the authors' accepted manuscript), sect. 2.4, p. 9: 'Flow data should be divided into segments of non-missing values ... data should be reflected at each end of each segment' |
| `baseflow_index_by_year` | `hydrolog.statistics.baseflow.baseflow_separation` | the baseflow index of the period and of each hydrological year (1 November - 31 October, named after its end) is the index (spec baseflow_index) of their days with a baseflow; a year needs 300 such days for an index of its own, and a year without flow on them has none (null); a period without flow on them is refused | min_year_days = 300.0 d (Hydrolog's own rules, ADR-0031: Regime, seasonality, harmonics, Sen's slope and baseflow of a station, point 5: the filter on each gapless span of at least 60 days, a year's index from 300 days with a baseflow (no published source; Ladson et al. 2013 filter every segment longer than the 30 reflected values, sect. 2.1 and 2.4)) | the ratio of the volumes over the days with a baseflow (Ladson et al., sect. 2.4; WMO-No. 1029, sect. 5.2), not BFI.R's mean of the spans' indices weighted by their lengths; 300 days a year is Hydrolog's own rule | WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.2, p. 44: 'Annual BFI values can be determined by summing up the base-flow and total-flow volume separately for each year' |
| `recession_without_segment` | `hydrolog.statistics.baseflow.recession_constant` | the recession constant of a series (spec recession_constant) with k and the half-life null and no segments when the series has no recession segment | – | the recession of baseflow_separation is that of the whole daily calendar of the series, gaps included as ends of segments | WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 5.3, p. 45 |

## Delegated computations (CMP-1.2)

| Computation | Library | Versions | Smoke case | Test |
|---|---|---|---|---|
| nash_shape_root | scipy.optimize.brentq | scipy>=1.10 (1.18.1 locked) | the root N of f(N) = (N-1)^N e^-(N-1) / Gamma(N) = f(2.55) on [1.1, 20] with xtol 1e-6 is 2.55 within 1e-6 (spec lutz) | `tests/unit/test_formulas_lutz.py::test_the_delegated_root_finder_finds_a_known_root` |
| lyne_hollick_recursion | scipy.signal.lfilter | scipy>=1.10 (1.18.1 locked) | lfilter([(1 + a) / 2], [1, -a], diff(Q), zi=[a Q_1]) gives the quickflow q_t = a q_(t-1) + (1 + a)/2 (Q_t - Q_(t-1)) from q_1 = Q_1 of the first pass of Ladson et al. (2013), Table 4 (Bass River, a = 0.98): 155.46 after 96 and 158 (spec lyne_hollick) | `tests/unit/test_formulas_baseflow.py::test_the_delegated_recursion_is_the_first_pass_of_table_4` |
