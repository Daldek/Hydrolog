# Formulas of Hydrolog

<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); do not edit. -->

## Tier A

| Formula | Function | Status | Version | Mutation score |
|---|---|---|---|---|
| [Potential maximum retention S of the SCS curve number](#scs_cn_retention) | `hydrolog.runoff.scs_cn.potential_retention` | referenced | 1 | not measured |
| [Direct runoff of a storm by the SCS curve number](#scs_cn_runoff) | `hydrolog.runoff.scs_cn.runoff_depths` | referenced | 1 | not measured |
| [Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)](#scs_cn_amc) | `hydrolog.runoff.scs_cn.amc_curve_number` | referenced | 1 | not measured |
| [Curve number of a soil-cover complex from the TR-55 tables](#tr55_cn) | `hydrolog.runoff.cn_lookup.table_curve_number` | referenced | 1 | not measured |
| [Gamma distribution of precipitation sums by Thom's approximation](#spi_gamma_fit) | `hydrolog.statistics.meteo_spi.fit_gamma` | referenced | 1 | not measured |
| [Standardized precipitation index of precipitation sums](#spi) | `hydrolog.statistics.meteo_spi.spi_values` | referenced | 1 | not measured |
| [Kaczorowska's class of a year's precipitation in % of its normal](#kaczorowska_class) | `hydrolog.statistics.meteo_spi.year_precipitation_class` | referenced | 1 | not measured |
| [Class of a month's precipitation in % of its normal](#month_precipitation_class) | `hydrolog.statistics.meteo_spi.month_precipitation_class` | referenced | 1 | not measured |
| [Frost, freeze-thaw, ice, summer and hot days and tropical nights of a day](#threshold_days) | `hydrolog.statistics.meteo_temperature.threshold_days` | referenced | 1 | not measured |
| [Growing and heating degree days of each day](#degree_days) | `hydrolog.statistics.meteo_temperature.daily_degree_days` | referenced | 1 | not measured |
| [The length of the dry or wet spell ending on each day](#spell_lengths) | `hydrolog.statistics.meteo_spells.spell_lengths` | oracle only | 1 | not measured |
| [Simple daily intensity index: the mean precipitation of a wet day](#sdii) | `hydrolog.statistics.meteo_precipitation.wet_day_intensity` | oracle only | 1 | not measured |
| [Percentile of the precipitation of the wet days (quantile type 8)](#wet_day_percentile) | `hydrolog.statistics.meteo_precipitation.wet_day_percentile` | referenced | 1 | not measured |
| [Precipitation of the days above a threshold and its share of the wet days'](#heavy_precipitation_share) | `hydrolog.statistics.meteo_precipitation.heavy_precipitation_share` | referenced | 1 | not measured |
| [Oliver's precipitation concentration index of twelve monthly totals](#precipitation_concentration_index) | `hydrolog.statistics.meteo_precipitation.precipitation_concentration_index` | referenced | 1 | not measured |
| [Oliver's class of a precipitation concentration index](#pci_class) | `hydrolog.statistics.meteo_precipitation.pci_class` | referenced | 1 | not measured |
| [Walsh and Lawler's class of a seasonality index](#si_class) | `hydrolog.statistics.meteo_precipitation.si_class` | referenced | 1 | not measured |
| [Walsh and Lawler's seasonality index of twelve monthly totals](#seasonality_index) | `hydrolog.statistics.regime.seasonality_index` | referenced | 1 | not measured |
| [Sielianinov's hydrothermal coefficient of a month or a season](#sielianinov_coefficient) | `hydrolog.statistics.meteo_hydrothermal.sielianinov_coefficient` | referenced | 1 | not measured |
| [Class of Sielianinov's hydrothermal coefficient (Skowera and Puła)](#sielianinov_class) | `hydrolog.statistics.meteo_hydrothermal.sielianinov_class` | referenced | 1 | not measured |

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

<a id="spi_gamma_fit"></a>
### Gamma distribution of precipitation sums by Thom's approximation

`hydrolog.statistics.meteo_spi.fit_gamma` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
A = \ln\bar{x} - \overline{\ln x},\quad \hat{\alpha} = \frac{1 + \sqrt{1 + 4A/3}}{4A},\quad \hat{\beta} = \frac{\bar{x}}{\hat{\alpha}},\quad q = \frac{m}{n}
$$

Plain text: `A = ln(mean x) - mean(ln x) over the positive sums x; alpha = (1 + sqrt(1 + 4A/3)) / (4A); beta = mean x / alpha; q = m / n, m sums of zero among n`

**Sources**

- Thom, H. C. S. (1958). A note on the gamma distribution. Monthly Weather Review 86(4), 117, the approximation of the maximum likelihood estimate of the shape; not opened here: its equations as McSweeney (2007) and Naresh Kumar et al. (2009) print them (author-provided)
- McSweeney, C. F. (2007). Daily rainfall variability at point and areal scales: evaluating simulations of present and future climate. PhD thesis, University of East Anglia, Norwich, chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum likelihood estimate of the shape (open) <https://crudata.uea.ac.uk/cru/pubs/thesis/2007-mcsweeney/4.Gamma.pdf>
- Naresh Kumar, M., Murthy, C. S., Sesha Sai, M. V. R. and Roy, P. S. (2009). On the use of Standardized Precipitation Index (SPI) for drought intensity assessment. Meteorological Applications 16(3), 381-389; open preprint arXiv:1509.04808, appendix, eqs. A4-A8 (Thom's estimates) and A9 (q = m / n) (open) <https://arxiv.org/pdf/1509.04808>
- WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) (open) <https://library.wmo.int/idurl/4/39629>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `sums_mm` | $x_i$ | mm | real_array | [0.0, inf), test bound high 105880.0 (four times the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes): a sum of the longest scale, 48 months) | unstated | [0.0, 872.3]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the k-month sums of the default scales 1, 3, 6 and 12: 0.4 to 872.3 mm (a month without precipitation gives 0) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `three_positive_sums` | precondition | at least three of the sums are positive | Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a station, the group meteo, point 5: a calendar month is fitted when 3 of its sums are positive |
| `positive_sums_differ` | precondition | the positive sums are not all equal (A > 0) | McSweeney, C. F. (2007). Daily rainfall variability at point and areal scales: evaluating simulations of present and future climate. PhD thesis, University of East Anglia, Norwich, chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum likelihood estimate of the shape |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `thom_ratio` | $4/3$ | 4/3 | - | McSweeney, C. F. (2007). Daily rainfall variability at point and areal scales: evaluating simulations of present and future climate. PhD thesis, University of East Anglia, Norwich, chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum likelihood estimate of the shape |
| `thom_denominator` | $4$ | 4.0 | - | McSweeney, C. F. (2007). Daily rainfall variability at point and areal scales: evaluating simulations of present and future climate. PhD thesis, University of East Anglia, Norwich, chapter 4, p. 93, eqs. 4-3 and 4-4: Thom's approximation of the maximum likelihood estimate of the shape |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `alpha` | - | real | (0.0, inf) | 4 ulp of the bound |
| `beta_mm` | mm | real | (0.0, inf) | 4 ulp of the bound |
| `zero_probability` | - | real | [0.0, 1.0) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the sums of one calendar month and scale over the years of the reference period; the caller leaves out the years without a sum
- q = m / n, the zero sums among all n sums (Edwards and McKee 1997, as Naresh Kumar et al. 2009 eq. A9 restate it); the shape and scale from the positive sums only
- Thom's approximation, not the exact maximum likelihood estimate, as climate_indices 3.2.0 and xclim 1.0.0 (method APP)
- A computed as the mean of d - ln(1 + d), d = x / mean x - 1, which equals ln(mean x) - mean(ln x) without its cancellation (ln x - ln(mean x) for a sum below half the mean)

**Assumptions**

None stated.

**Validation:** Thom's estimate approximates the maximum likelihood shape: its relative error is 1e-4 at A = 0.1 (alpha near 5), 2e-3 at A = 0.3 and 2.7 % at A = 1 (alpha 0.62), against ln(alpha) - digamma(alpha) = A solved exactly (the audit of 2026-11-18); the sources give no test of the fit against observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: preconditions three_positive_sums and positive_sums_differ: A = 0 for equal sums would divide by zero; a zero sum never reaches a logarithm
- `moment_cancellation`: limit nearly_equal_sums: A, a difference of nearly equal logarithms, is the mean of d - ln(1 + d)
- `many_small_terms`: the mean and A are pairwise sums of at most one term per year; limit decimal_oracle checks them to 1e-13
- `gap_propagation`: type case sums_mm-nan_element: a gap is refused; the caller passes the known sums only

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `sums_in_another_unit`: inputs times 2^e (`sums_mm` e = 1.0) give outputs times 2^e (`beta_mm` e = 1.0)
- limit `decimal_oracle`: alpha, beta and q equal Thom's equations evaluated from ln(mean) - mean(ln x) in 50-digit decimal arithmetic
- limit `nearly_equal_sums`: sums equal to two parts in a billion keep their estimates (A as the mean of d - ln(1 + d))
- limit `share_of_zeros`: q is the share of zero sums

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: Thom's equations from ln(mean) - mean(ln x) in 50-digit decimal arithmetic (decimal) (`tests/unit/test_formulas_meteo_spi.py (limit decimal_oracle)`)
- frozen: climate_indices 3.2.0 indices.spi on the monthly sums of Warszawa-Okęcie 1991-2020, scales 1, 3, 6 and 12 (`tests/oracles/spi_climate_indices_warszawa.csv, compared by tests/unit/test_formulas_meteo_spi.py`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="spi"></a>
### Standardized precipitation index of precipitation sums

`hydrolog.statistics.meteo_spi.spi_values` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
H(x) = q + (1 - q)\,P\!\left(\alpha, \frac{x}{\beta}\right),\quad H(0) = q,\quad \mathrm{SPI} = \max\!\left(-3.09, \min\!\left(3.09, \Phi^{-1}(H(x))\right)\right)
$$

Plain text: `H(x) = q + (1 - q) G(x; alpha, beta) for x > 0, H(0) = q, G the gamma distribution function; SPI = Phi^-1(H(x)) held within -3.09 and 3.09`

**Sources**

- WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) (open) <https://library.wmo.int/idurl/4/39629>
- Naresh Kumar, M., Murthy, C. S., Sesha Sai, M. V. R. and Roy, P. S. (2009). On the use of Standardized Precipitation Index (SPI) for drought intensity assessment. Meteorological Applications 16(3), 381-389; open preprint arXiv:1509.04808, appendix, eq. A9 (H(x) = q + (1 - q) G(x), after Edwards and McKee 1997) and eqs. A10-A12 (the normal quantile) (open) <https://arxiv.org/pdf/1509.04808>
- climate_indices 3.2.0 (J. Adams), Python package of climate indices, indices.spi: Thom's estimates, zero_handling 'classic' (H(0) = q), the SPI held within the valid range of a fitted index, -3.09 to 3.09 (open) <https://pypi.org/project/climate-indices/3.2.0/>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `sums_mm` | $x$ | mm | real_array | [0.0, inf), test bound high 105880.0 (four times the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes): a sum of the longest scale, 48 months) | unstated | [0.0, 872.3]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the k-month sums of the default scales 1, 3, 6 and 12: 0.4 to 872.3 mm (a month without precipitation gives 0) |
| `alpha` | $\alpha$ | - | real | (0.0, inf), test bound high 10000.0 (a shape of 1e4 is a coefficient of variation of 1 % of the sums, beyond the 213.6 of 48-month sums at Warszawa-Okęcie) | unstated | [1.7, 42.6]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the fits of the default scales 1, 3, 6 and 12: shapes 1.72 to 42.60 |
| `beta_mm` | $\beta$ | mm | real | (0.0, inf), test bound high 105880.0 (four times the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes): a sum of the longest scale, 48 months) | unstated | [5.8, 31.7]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the fits of the default scales 1, 3, 6 and 12: scales 5.81 to 31.71 mm |
| `zero_probability` | $q$ | - | real | [0.0, 1.0) | unstated | [0.0, 0.0]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, no month without precipitation in 1991-2020: q = 0 in every fit of the default scales |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `spi_limit` | $3.09$ | 3.09 | - | climate_indices 3.2.0 (J. Adams), Python package of climate indices, indices.spi: Thom's estimates, zero_handling 'classic' (H(0) = q), the SPI held within the valid range of a fitted index, -3.09 to 3.09 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `spi` | - | real_array | [-3.09, 3.09] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- classic zero handling, H(0) = q (Edwards and McKee 1997; climate_indices zero_handling 'classic'); the centre of the zero mass, Phi^-1(q / 2), is not used
- held within -3.09 and 3.09, the quantiles of 0.001 and 0.999, as climate_indices; WMO-No. 1090 and xclim set no limit
- the upper tail from 1 - H = (1 - q) Q(alpha, x / beta), Q the regularized upper incomplete gamma function, where H > 0.5
- the SPI is not classed (WMO-No. 1090 table 1 gives classes from -2 to 2)

**Assumptions**

None stated.

**Validation:** none: the SPI is a transformation of the fitted distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: limit held_within_limits: Phi^-1(0) and Phi^-1(1) are infinite and held at the limits; at a subnormal shape scipy's gammainc gives 0 and its gammaincc may go negative: both are held in [0, 1] and the tail is chosen by gammaincc (the pinned examples of test_spi_properties)
- `gap_propagation`: type case sums_mm-nan_element: a missing sum gives a missing SPI and no other

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `sums_mm` increasing, `alpha` decreasing, `beta_mm` decreasing, `zero_probability` increasing
- scaling `sums_and_scale_in_another_unit`: inputs times 2^e (`sums_mm` e = 1.0, `beta_mm` e = 1.0) give outputs times 2^e (none)
- limit `zero_sum`: a zero sum has H = q (the classic zero handling)
- limit `held_within_limits`: H = 0 and H = 1 give -3.09 and 3.09
- limit `series_oracle`: the SPI equals the normal quantile of H from the power series of the incomplete gamma function in decimal arithmetic

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: P(alpha, x / beta) by its power series in 40-digit decimals (decimal) and the normal quantile of statistics.NormalDist (AS241) (`tests/unit/test_formulas_meteo_spi.py (limit series_oracle)`)
- frozen: climate_indices 3.2.0 indices.spi on the monthly sums of Warszawa-Okęcie 1991-2020, scales 1, 3, 6 and 12 (`tests/oracles/spi_climate_indices_warszawa.csv, compared by tests/unit/test_formulas_meteo_spi.py`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="kaczorowska_class"></a>
### Kaczorowska's class of a year's precipitation in % of its normal

`hydrolog.statistics.meteo_spi.year_precipitation_class` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
r = \left\lfloor \frac{100\,P}{N} + \frac{1}{2} \right\rfloor:\ r < 50,\ 50 \le r \le 74,\ 75 \le r \le 89,\ 90 \le r \le 110,\ 111 \le r \le 125,\ 126 \le r \le 150,\ r > 150
$$

Plain text: `P/N rounded to a whole percent, a half up: below 50 extremely dry, 50-74 very dry, 75-89 dry, 90-110 normal, 111-125 wet, 126-150 very wet, above 150 extremely wet`

**Sources**

- Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the classes of a year (or a season) in % of the normal (open) <https://rcin.org.pl/Content/16869/PDF/WA51_22011_r1962_nr33_Prace-Geogr.pdf>
- IMGW-PIB (2023). Rocznik Meteorologiczny 2022, Tab. 5, p. 14 (the same classes, „normalny” for „przeciętny”) and Tab. 9, p. 22 (annual sums in % of the normal 1991-2020, whole percents) (open) <https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/Roczniki/Rocznik%20meteorologiczny/Rocznik%20Meteorologiczny%202022.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `percent_of_normal` | $P/N$ | % | real | [0.0, inf), test bound high 1452.0 (ten times the largest percentage of the project's data (145.2 % at Warszawa-Okęcie)) | unstated | [71.0, 145.2]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the annual sums of 1991-2020 in % of their normal: 71.0 to 145.2 % |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `very_dry_from` | $50$ | 50.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class very_dry |
| `dry_from` | $75$ | 75.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class dry |
| `normal_from` | $90$ | 90.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class normal |
| `wet_from` | $111$ | 111.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class wet |
| `very_wet_from` | $126$ | 126.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class very_wet |
| `extremely_wet_from` | $151$ | 151.0 | % | Kaczorowska, Z. (1962). Opady w Polsce w przekroju wieloletnim. Prace Geograficzne IG PAN 33, p. 72: the least whole percent of the class extremely_wet |
| `rounding_half` | $1/2$ | 0.5 | % | Hydrolog ADR-0059 (2026-11-19): the meteorological indices declared by specs, the classes are ranges of whole percents: a percentage counts in the class of its rounding, a half up |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `precipitation_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- a percentage counts in the class of its whole-number rounding, a half rounded up: 74.5 % is dry, 110.5 % wet, 150.5 % extremely wet (Python's rounding of a half to even, used up to 0.8.1, made them very dry, normal and very wet)
- Łabędzki and Bąk (2004, Acta Agrophysica 3(1), Tab. 2) read the classes with decimal bounds (75.0-89.9 dry): 89.6 % is normal here and dry there
- the normal of the reference period, by default the analysed years

**Assumptions**

None stated.

**Validation:** none: a classification

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases kaczorowska-boundary-*: each limit, a half below it and above it
- `gap_propagation`: type case percent_of_normal-nan: NaN is refused; a year without a percentage has no class

**Properties (CMP-6.5)**

- units: unit_specific
- limit `ordered_classes`: a larger percentage never gives a drier class

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="month_precipitation_class"></a>
### Class of a month's precipitation in % of its normal

`hydrolog.statistics.meteo_spi.month_precipitation_class` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\frac{100\,P}{N} < 25,\ [25, 50),\ [50, 75),\ [75, 125],\ (125, 150],\ (150, 200],\ > 200
$$

Plain text: `P/N below 25 extremely dry, [25, 50) very dry, [50, 75) dry, [75, 125] normal, (125, 150] wet, (150, 200] very wet, above 200 extremely wet`

**Sources**

- Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the classes of the relative precipitation index of a month (source line: Tomaszewska 1994); eq. 1, p. 109 (RPI = 100 P / N) (open) <https://www.itp.edu.pl/old/wydawnictwo/woda/zeszyt_36_2011/artykuly/Gasiorek%20Musial.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `percent_of_normal` | $P/N$ | % | real | [0.0, inf), test bound high 3589.0 (ten times the largest percentage of the project's data (358.9 % at Warszawa-Okęcie)) | unstated | [1.1, 358.9]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020 in % of their normals: 1.1 to 358.9 % |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `extremely_dry_below` | $25$ | 25.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class extremely_dry |
| `very_dry_below` | $50$ | 50.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class very_dry |
| `dry_below` | $75$ | 75.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the open upper limit of the class dry |
| `normal_to` | $125$ | 125.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class normal |
| `wet_to` | $150$ | 150.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class wet |
| `very_wet_to` | $200$ | 200.0 | % | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), Table 1, p. 109: the upper limit of the class very_wet |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `precipitation_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the interval closures of Table 1 as printed: the lower three classes closed below, the upper ones closed above
- Kaczorowska (1962) classes years and seasons only; IMGW-PIB's monitoring labels this monthly table after her, which the source line of Gąsiorek and Musiał (2011) does not

**Assumptions**

None stated.

**Validation:** none: a classification

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases month-class-boundary-*: each limit and just beyond it
- `gap_propagation`: type case percent_of_normal-nan: NaN is refused; a month without a percentage has no class

**Properties (CMP-6.5)**

- units: unit_specific
- limit `ordered_classes`: a larger percentage never gives a drier class

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="threshold_days"></a>
### Frost, freeze-thaw, ice, summer and hot days and tropical nights of a day

`hydrolog.statistics.meteo_temperature.threshold_days` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{FD} = [T_{n} < T_f],\ \mathrm{FT} = [T_{n} < T_f][T_{x} > T_i],\ \mathrm{ID} = [T_{x} < T_i],\ \mathrm{SU} = [T_{x} > T_s],\ \mathrm{HD} = [T_{x} > T_h],\ \mathrm{TR} = [T_{n} > T_t]
$$

Plain text: `frost: Tmin < Tf; freeze-thaw: Tmin < Tf and Tmax > Ti; ice: Tmax < Ti; summer: Tmax > Ts; hot: Tmax > Th; tropical night: Tmin > Tt; 1 when it holds, else 0 (the ETCCDI: Tf = Ti = 0, Ts = 25, Tt = 20 °C; Th = 30 °C)`

**Sources**

- ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN (open) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
- Kossowska-Cezak, U. (2014). Zmiany wieloletnie liczby termicznych dni charakterystycznych w Warszawie (1951-2010). Prace Geograficzne 136, 9-30, p. 14, after the Słownik meteorologiczny (2003): a hot day („upalny”) has tmax > 30 °C, a freeze-thaw day („przymrozkowy”) tmin < 0 °C and tmax > 0 °C (open)
- IMGW-PIB: Normy klimatyczne 1991-2020, product PRZYMROZKI, „Liczba dni przymrozkowych (TMAX>0 & TMIN<0)” (open) <https://klimat.imgw.pl>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `tmax_c` | $T_x$ | °C | real_array | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [-16.7, 37.0]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily maximum temperature: -16.7 to 37.0 °C |
| `tmin_c` | $T_n$ | °C | real_array | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [-27.1, 22.8]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily minimum temperature: -27.1 to 22.8 °C |
| `frost_tmin_c` | $T_f$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 0.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |
| `ice_tmax_c` | $T_i$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 0.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |
| `summer_tmax_c` | $T_s$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [25.0, 25.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |
| `hot_tmax_c` | $T_h$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [30.0, 30.0]: Kossowska-Cezak, U. (2014). Zmiany wieloletnie liczby termicznych dni charakterystycznych w Warszawie (1951-2010). Prace Geograficzne 136, 9-30, p. 14, after the Słownik meteorologiczny (2003): a hot day („upalny”) has tmax > 30 °C, a freeze-thaw day („przymrozkowy”) tmin < 0 °C and tmax > 0 °C |
| `tropical_tmin_c` | $T_t$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [20.0, 20.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `the_same_days` | precondition | tmax_c and tmin_c hold the same days, one value of each a day | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `frost` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |
| `freeze_thaw` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |
| `ice` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |
| `summer` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |
| `hot` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |
| `tropical` | - | real_array | [0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- strict signs as the ETCCDI: a day exactly at a threshold is none of these days; IMGW-PIB's yearbooks count Tmin <= 0 and Tmax >= 25 or 30 °C
- the freeze-thaw day is the „dzień przymrozkowy” of the Słownik meteorologiczny and of IMGW-PIB's normals (PRZYMROZKI); the frost day is FD
- a flag is missing (NaN) where a temperature it needs is; the series function gives an all-missing series for one it lacks

**Assumptions**

None stated.

**Validation:** none: a classification of a day

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases etccdi-*-boundary: each threshold and 0.1 °C beyond it
- `gap_propagation`: type cases tmax_c-nan_element and tmin_c-nan_element: a missing temperature leaves only its own flags missing

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `tmin_c` decreasing, `frost_tmin_c` increasing
- limit `counting_oracle`: every flag equals the comparison made day by day in a loop, at the ETCCDI's thresholds and beside them, with gaps
- conservation `a_freeze_thaw_day_is_a_frost_day`: no freeze-thaw day without a frost day

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the flags compared day by day in a Python loop on a seeded series with gaps and on the thresholds themselves (`tests/unit/test_formulas_meteo_temperature.py (limit counting_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="degree_days"></a>
### Growing and heating degree days of each day

`hydrolog.statistics.meteo_temperature.daily_degree_days` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{GDD} = \max(T_m - T_b, 0),\quad \mathrm{HDD} = \begin{cases} T_r - T_m & T_m \le T_l \\ 0 & T_m > T_l \end{cases},\quad T_l \le T_r
$$

Plain text: `GDD = max(Tm - Tb, 0); HDD = Tr - Tm if Tm <= Tl, else 0 (Eurostat: Tr = 18 °C, Tl = 15 °C); Tl <= Tr`

**Sources**

- Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) (open) <https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm>
- Wypych, A., Sulikowska, A., Ustrnul, Z. and Czekierda, D. (2017). Variability of growing degree days in Poland in response to ongoing climate changes in Europe. International Journal of Biometeorology 61, 49-59, eq. 1, p. 50: GDD = sum of (T - Tbase) over the days with T > Tbase; the bases 0, 5 and 10 °C (open)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `tmean_c` | $T_m$ | °C | real_array | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [-22.2, 29.3]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily mean temperature: -22.2 to 29.3 °C |
| `growing_base_c` | $T_b$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 10.0]: Wypych, A., Sulikowska, A., Ustrnul, Z. and Czekierda, D. (2017). Variability of growing degree days in Poland in response to ongoing climate changes in Europe. International Journal of Biometeorology 61, 49-59, eq. 1, p. 50: GDD = sum of (T - Tbase) over the days with T > Tbase; the bases 0, 5 and 10 °C |
| `heating_base_c` | $T_r$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [18.0, 18.0]: Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) |
| `heating_limit_c` | $T_l$ | °C | real | [-273.15, inf), test bound high 56.7 (the highest air temperature on record, 56.7 °C at Furnace Creek, 10 July 1913 (WMO Archive of Weather and Climate Extremes)) | unstated | [15.0, 15.0]: Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `heating_limit_not_above_base` | precondition | heating_limit_c <= heating_base_c: a heating day lies below the reference temperature, so its degree days are not negative | Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `growing_degree_days` | °C·d | real_array | [0.0, inf) | 4 ulp of the bound |
| `heating_degree_days` | °C·d | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Tm is the daily mean given; Eurostat's Directive takes Tm = (Tmin + Tmax) / 2 (at Warszawa-Okęcie 1991-2020 HDD 3407 against 3365 °C·d)
- a day heats at Tm <= Tl (inclusive) and grows at Tm > Tb
- the series function sums the days of complete months and the twelve months of the year: no growing or heating season is cut out

**Assumptions**

None stated.

**Validation:** none: an index of the daily mean

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type case tmean_c-nan_element: a missing day gives missing degree days and no other
- `difference_denominator`: none divides; precondition heating_limit_not_above_base keeps Tr - Tm of a heating day >= 0

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `tmean_c` increasing, `growing_base_c` decreasing
- symmetry `shifted_temperatures`: the temperature and the three thresholds shifted by 1 °C, where the shift is exact in binary, give the same degree days

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="spell_lengths"></a>
### The length of the dry or wet spell ending on each day

`hydrolog.statistics.meteo_spells.spell_lengths` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
L_t = \begin{cases} t - s + 1 & d_s = \dots = d_t = 1,\ d_{s-1} = d_{t+1} = 0 \\ 0 & \text{otherwise} \end{cases},\quad d_t = [P_t < P_0]\ (\text{dry}),\ [P_t \ge P_0]\ (\text{wet})
$$

Plain text: `a day is dry when P < P0 and wet when P >= P0, a missing day neither; L(t) = the number of consecutive days of the kind ending on day t when day t is of the kind and day t + 1 is not, else 0`

**Sources**

- ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) (open) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
- ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20: a spell can continue into the next year and is counted against the year in which the spell ends (open) <https://knmi-ecad-assets-prd.s3.amazonaws.com/documents/atbd.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $P_t$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 75.8]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm |
| `threshold_mm` | $P_0$ | mm | real | (0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [1.0, 1.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) |
| `kind` | $\text{kind}$ | - | choice of dry, wet | – | – | – |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `spell_days` | d | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- a dry day has P < P0 and a wet day P >= P0 (RR < 1 mm and RR >= 1 mm of the ETCCDI): a day at the threshold is wet
- a missing day (NaN) is neither dry nor wet: it ends a spell and has L = 0; the series function marks such a spell open
- the length of a spell stands on its last day, so that the series function credits each spell whole to the year of its end (Tier B spell_year)

**Assumptions**

None stated.

**Validation:** none: a count of days

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type case precipitation_mm-nan_element and limit counting_oracle: a missing day ends a spell and has 0, never NaN

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `precipitation_in_another_unit`: inputs times 2^e (`precipitation_mm` e = 1.0, `threshold_mm` e = 1.0) give outputs times 2^e (none)
- limit `counting_oracle`: L equals the spells counted day by day in a loop, on hand-made and seeded series with gaps, both kinds and three thresholds
- limit `one_spell_of_every_day`: a series of dry days is one spell, its length on its last day
- limit `a_day_at_the_threshold_is_wet`: P = P0 is a wet day, P just below it a dry one
- conservation `every_day_of_the_kind_once`: the spells hold each day of the kind once: the sum of L is the number of dry (wet) days

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the spells counted day by day in a Python loop (math.isnan and a running count), not by the edges of runs (`tests/unit/test_formulas_meteo_spells.py (limit counting_oracle)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="sdii"></a>
### Simple daily intensity index: the mean precipitation of a wet day

`hydrolog.statistics.meteo_precipitation.wet_day_intensity` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
W = \#\{i : P_i \ge P_w\},\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,\quad \mathrm{SDII} = \frac{\mathrm{PRCPTOT}}{W}
$$

Plain text: `W = the number of days with P >= Pw; PRCPTOT = the sum of their P; SDII = PRCPTOT / W`

**Sources**

- ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 (open) <https://etccdi.pacificclimate.org/list_27_indices.shtml>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $P_i$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 75.8]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm |
| `wet_day_mm` | $P_w$ | mm | real | (0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [1.0, 1.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_wet_day` | precondition | at least one day has P >= P_w | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `sdii_mm` | mm | real | (0.0, inf) | 4 ulp of the bound |
| `wet_days` | d | integer | [1.0, inf) | 4 ulp of the bound |
| `wet_day_total_mm` | mm | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- a wet day has P >= Pw (RR >= 1 mm of the ETCCDI); a missing day (NaN) is left out
- the series function takes the days of a complete month or year, or of a calendar month's complete months pooled, and rounds PRCPTOT to 1e-6 mm; a span without a wet day has no SDII (climdex.pcic gives 0)

**Assumptions**

None stated.

**Validation:** none: an index of the daily precipitation

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type case precipitation_mm-nan_element: a missing day is left out, never NaN in the outputs
- `many_small_terms`: limit exact_oracle: PRCPTOT of 365 days against exact fractions to 1e-14

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `precipitation_in_another_unit`: inputs times 2^e (`precipitation_mm` e = 1.0, `wet_day_mm` e = 1.0) give outputs times 2^e (`sdii_mm` e = 1.0, `wet_day_total_mm` e = 1.0)
- limit `exact_oracle`: W, PRCPTOT and SDII equal their values in exact fractions
- limit `a_day_at_the_threshold_is_wet`: P = Pw counts as a wet day
- conservation `intensity_times_days_is_the_total`: SDII W = PRCPTOT

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: W, PRCPTOT and SDII in exact fractions (fractions.Fraction) of hand-made and seeded series with gaps (`tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="wet_day_percentile"></a>
### Percentile of the precipitation of the wet days (quantile type 8)

`hydrolog.statistics.meteo_precipitation.wet_day_percentile` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
h = \left(n + \tfrac{1}{3}\right)\frac{p}{100} + \tfrac{1}{3},\quad Q = x_{(k)} + (h - k)\left(x_{(k+1)} - x_{(k)}\right),\quad k = \lfloor h \rfloor
$$

Plain text: `x(1) <= ... <= x(n) the precipitation of the days with P >= Pw; h = (n + 1/3) p / 100 + 1/3, k its whole part; Q = x(1) for h <= 1, x(n) for h >= n, else x(k) + (h - k) (x(k + 1) - x(k))`

**Sources**

- Hyndman, R. J. and Fan, Y. (1996). Sample quantiles in statistical packages. The American Statistician 50(4), 361-365, definition 8: Q(p) = x(k) + (h - k) (x(k + 1) - x(k)), h = (n + 1/3) p + 1/3 and k its whole part, x(k) the k-th smallest of n values (author-provided)
- NumPy 2 documentation, numpy.percentile, method 'median_unbiased': definition 8 of Hyndman and Fan (1996), virtual index n p + 1/3 + p / 3 - 1 counted from 0 (open) <https://numpy.org/doc/stable/reference/generated/numpy.percentile.html>
- Bronaugh, D. (2020). climdex.pcic 1.1-11: PCIC implementation of Climdex routines, R package, R/climdex.r: the percentiles of the wet days (not NA, at least 1 mm) of the base period by quantile type 8 (open) <https://cran.r-project.org/src/contrib/Archive/climdex.pcic/>
- ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 (open) <https://etccdi.pacificclimate.org/list_27_indices.shtml>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $P_i$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 75.8]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm |
| `wet_day_mm` | $P_w$ | mm | real | (0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [1.0, 1.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |
| `percentile` | $p$ | % | real | (0.0, 100.0) | unstated | [95.0, 99.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_wet_day` | precondition | at least one day has P >= P_w | Hyndman, R. J. and Fan, Y. (1996). Sample quantiles in statistical packages. The American Statistician 50(4), 361-365, definition 8: Q(p) = x(k) + (h - k) (x(k + 1) - x(k)), h = (n + 1/3) p + 1/3 and k its whole part, x(k) the k-th smallest of n values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `percentile_mm` | mm | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- quantile type 8 of Hyndman and Fan (1996), median-unbiased, as climdex.pcic 1.1-11 (quantile type 8) and NumPy's method median_unbiased
- the wet days (P >= Pw) of the period given; a missing day (NaN) is left out
- the series function gives the wet days of the reference period and needs at least 100 of them (too_few_wet_days, Hydrolog's minimum, ADR-0032)

**Assumptions**

None stated.

**Validation:** none: a sample quantile

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type case precipitation_mm-nan_element: a missing day is left out
- `singular_at_bound`: the percentile is in (0, 100): h is clipped to [1, n] by definition 8, limit exact_oracle at 0.5 and 99.9

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `percentile` increasing
- scaling `precipitation_in_another_unit`: inputs times 2^e (`precipitation_mm` e = 1.0, `wet_day_mm` e = 1.0) give outputs times 2^e (`percentile_mm` e = 1.0)
- limit `exact_oracle`: Q equals definition 8 of Hyndman and Fan in exact fractions

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: definition 8 of Hyndman and Fan in exact fractions (fractions.Fraction), written from the paper's equation (`tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="heavy_precipitation_share"></a>
### Precipitation of the days above a threshold and its share of the wet days'

`hydrolog.statistics.meteo_precipitation.heavy_precipitation_share` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
R = \sum_{P_i > P_t} P_i,\quad \mathrm{PRCPTOT} = \sum_{P_i \ge P_w} P_i,\quad s = \frac{100\,R}{\mathrm{PRCPTOT}},\quad P_t \ge P_w
$$

Plain text: `R = the sum of P over the days with P > Pt (R95p for the 95th percentile of the wet days), D their number, PRCPTOT the sum of P over the days with P >= Pw; share = 100 R / PRCPTOT (R95pTOT); Pt >= Pw`

**Sources**

- ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 (open) <https://etccdi.pacificclimate.org/list_27_indices.shtml>
- ClimPACT2, the indices of the Expert Team on Sector-specific Climate Indices (ET-SCI), climate.indices.csv: R95p, the annual sum of the precipitation of the days above the 95th percentile of the wet days; R95pTOT = 100 R95p / PRCPTOT (open) <https://github.com/ARCCSS-extremes/climpact>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $P_i$ | mm | real_array | [0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.0, 75.8]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the daily precipitation: 0 to 75.8 mm |
| `wet_day_mm` | $P_w$ | mm | real | (0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [1.0, 1.0]: ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |
| `threshold_mm` | $P_t$ | mm | real | (0.0, inf), test bound high 1825.0 (the world's largest daily rainfall, 1,825 mm at Foc-Foc, La Réunion, 7-8 January 1966 (WMO Archive of Weather and Climate Extremes)) | unstated | [16.8, 29.43]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the 95th and 99th percentiles of the wet days of 1991-2020: 16.8 and 29.43 mm |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_wet_day` | precondition | at least one day has P >= P_w | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |
| `threshold_of_a_wet_day` | precondition | Pt >= Pw: a day above the threshold is a wet day | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `heavy_mm` | mm | real | [0.0, inf) | 4 ulp of the bound |
| `heavy_days` | d | integer | [0.0, inf) | 4 ulp of the bound |
| `wet_day_total_mm` | mm | real | (0.0, inf) | 4 ulp of the bound |
| `share_percent` | % | real | [0.0, 100.0] | 1e-09 |

**Conventions (CMP-2.3)**

- a day counts above the threshold when P > Pt (strictly), a wet day when P >= Pw; a missing day (NaN) is left out
- R is R95p of ClimPACT and of the ETCCDI's list (a sum in mm), the share R95pTOT of ClimPACT (100 R / PRCPTOT); ECA&D's R95pTOT divides by the precipitation of every day
- the series function takes the days of a complete year, the threshold of wet_day_percentile, and rounds R and PRCPTOT to 1e-6 mm; a year without a wet day has no share

**Assumptions**

None stated.

**Validation:** none: an index of the daily precipitation

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: precondition a_wet_day: PRCPTOT > 0, the sum of values of at least Pw > 0
- `gap_propagation`: type case precipitation_mm-nan_element: a missing day is left out
- `many_small_terms`: limit exact_oracle: the sums of 365 days against exact fractions to 1e-14

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `precipitation_mm` increasing, `threshold_mm` decreasing
- scaling `precipitation_in_another_unit`: inputs times 2^e (`precipitation_mm` e = 1.0, `wet_day_mm` e = 1.0, `threshold_mm` e = 1.0) give outputs times 2^e (`heavy_mm` e = 1.0, `wet_day_total_mm` e = 1.0)
- limit `exact_oracle`: R, D and the share equal their values in exact fractions

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: R, D and the share in exact fractions (fractions.Fraction) of the wet days 1 to 100 mm and of seeded series with gaps (`tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="precipitation_concentration_index"></a>
### Oliver's precipitation concentration index of twelve monthly totals

`hydrolog.statistics.meteo_precipitation.precipitation_concentration_index` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{PCI} = 100\,\frac{\sum_{i=1}^{12} p_i^2}{\left(\sum_{i=1}^{12} p_i\right)^2}
$$

Plain text: `PCI = 100 sum(p_i^2) / (sum p_i)^2 over the twelve monthly totals p_i`

**Sources**

- de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, eq. 1, p. 1260: PCI = 100 sum p_i^2 / (sum p_i)^2 of the twelve monthly totals; 8.3 for equal months, 100 for all in one month (open) <https://nhess.copernicus.org/articles/11/1259/2011/>
- Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300-309, the index and its classes; not opened here: as de Luis et al. (2011) print them (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `monthly_mm` | $p_i$ | mm | real_array | [0.0, inf), test bound high 26470.0 (a month holds less than the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.4, 295.0]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020: 0.4 to 295.0 mm |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_positive_total` | precondition | the total of the twelve months is positive | Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300-309, the index and its classes; not opened here: as de Luis et al. (2011) print them |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `pci` | - | real | [8.333333333333334, 100.0] | 1e-12 |

**Conventions (CMP-2.3)**

- computed from the shares p_i / sum p, which equals the equation without squaring a sum (no overflow or underflow of the squares)
- the series function gives the twelve normals of the reference period or the twelve monthly sums of a year with all of them; a total of 0 has no index

**Assumptions**

None stated.

**Validation:** none: an index of the monthly totals

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: precondition a_positive_total: the total divides
- `singular_at_bound`: limit exact_oracle: a single month of 1e-300 mm, whose square underflows, gives 100

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `totals_in_another_unit`: inputs times 2^e (`monthly_mm` e = 1.0) give outputs times 2^e (none)
- limit `exact_oracle`: PCI equals 100 sum p^2 / (sum p)^2 in exact fractions
- limit `equal_months`: twelve equal months give 100/12
- symmetry `months_in_another_order`: the months in reverse order give the same index

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the equation in exact fractions (fractions.Fraction) of the normals of Warszawa and of seeded monthly totals (`tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="pci_class"></a>
### Oliver's class of a precipitation concentration index

`hydrolog.statistics.meteo_precipitation.pci_class` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{PCI} \le 10,\ (10, 15],\ (15, 20],\ > 20
$$

Plain text: `PCI <= 10 uniform, (10, 15] moderate, (15, 20] irregular, above 20 strongly irregular`

**Sources**

- de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate concentration, 16-20 irregular, above 20 strong irregularity (open) <https://nhess.copernicus.org/articles/11/1259/2011/>
- Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. Professional Geographer 32(3), 300-309, the index and its classes; not opened here: as de Luis et al. (2011) print them (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `pci` | $\mathrm{PCI}$ | - | real | [8.333333333333334, 100.0] | unstated | [9.4, 27.3]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the yearly PCI of 1991-2020: 9.4 to 27.3 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `uniform_to` | $10$ | 10.0 | - | de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate concentration, 16-20 irregular, above 20 strong irregularity |
| `moderate_to` | $15$ | 15.0 | - | de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate concentration, 16-20 irregular, above 20 strong irregularity |
| `irregular_to` | $20$ | 20.0 | - | de Luis, M., González-Hidalgo, J. C., Brunetti, M. and Longares, L. A. (2011). Precipitation concentration changes in Spain 1946-2005. Natural Hazards and Earth System Sciences 11, 1259-1265, p. 1260, Oliver's classes: below 10 uniform, 11-15 moderate concentration, 16-20 irregular, above 20 strong irregularity |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `index_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the source's classes are of whole numbers (below 10, 11-15, 16-20, above 20); the gaps between them go to the class above: 10 is uniform, 10.5 moderate, 15 moderate and 15.5 irregular

**Assumptions**

None stated.

**Validation:** none: a classification

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases pci-class-*: each limit and just beyond it
- `gap_propagation`: type case pci-nan: NaN is refused; a year without an index has no class

**Properties (CMP-6.5)**

- units: unit_specific
- limit `ordered_classes`: a larger index never gives a more uniform class

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="si_class"></a>
### Walsh and Lawler's class of a seasonality index

`hydrolog.statistics.meteo_precipitation.si_class` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{SI} < 0.2,\ [0.2, 0.4),\ [0.4, 0.6),\ [0.6, 0.8),\ [0.8, 1.0),\ [1.0, 1.2),\ \ge 1.2
$$

Plain text: `SI < 0.2 very equable, [0.2, 0.4) equable with a wetter season, [0.4, 0.6) rather seasonal, [0.6, 0.8) seasonal, [0.8, 1.0) markedly seasonal, [1.0, 1.2) most in three months, from 1.2 extreme`

**Sources**

- Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme (open)
- Zambrano-Bigiarini, M. hydroTSM: time series management and analysis for hydrological modelling, R package (CRAN), si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83, and its seven classes (open) <https://cran.r-project.org/package=hydroTSM>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `si` | $\mathrm{SI}$ | - | real | [0.0, 1.8333333333333333] | unstated | [0.31, 0.85]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the yearly SI of 1991-2020: 0.31 to 0.85 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `very_equable_below` | $0.2$ | 0.2 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |
| `equable_wetter_season_below` | $0.4$ | 0.4 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |
| `rather_seasonal_below` | $0.6$ | 0.6 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |
| `seasonal_below` | $0.8$ | 0.8 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |
| `markedly_seasonal_below` | $1$ | 1.0 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |
| `most_in_three_months_below` | $1.2$ | 1.2 | - | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, Table II, p. 226, after Walsh and Lawler (1981): <= 0.19 very equable, 0.20-0.39 equable but with a definite wetter season, 0.40-0.59 rather seasonal with a short drier season, 0.60-0.79 seasonal, 0.80-0.99 markedly seasonal with a long drier season, 1.00-1.19 most rain in 3 months or less, >= 1.20 extreme |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `index_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the table's classes are of two decimals (<= 0.19, 0.20-0.39 ... >= 1.20); each class runs up to the next limit: 0.199 is very equable, 0.2 equable with a wetter season, 1.2 extreme

**Assumptions**

None stated.

**Validation:** none: a classification

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases si-class-*: each limit and just below it
- `gap_propagation`: type case si-nan: NaN is refused; a year without an index has no class

**Properties (CMP-6.5)**

- units: unit_specific
- limit `ordered_classes`: a larger index never gives a more equable class

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="seasonality_index"></a>
### Walsh and Lawler's seasonality index of twelve monthly totals

`hydrolog.statistics.regime.seasonality_index` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{SI} = \frac{1}{R}\sum_{n=1}^{12}\left|x_n - \frac{R}{12}\right|,\quad R = \sum_{n=1}^{12} x_n
$$

Plain text: `SI = (1/R) sum |x_n - R/12| over the twelve monthly totals x_n, R = sum x_n`

**Sources**

- Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, eq. 1, p. 225: SI = (1/R) sum |x_n - R/12|, R the annual total; 0 when every month has the same total, 1.83 when one month has all of it (open)
- Zambrano-Bigiarini, M. hydroTSM: time series management and analysis for hydrological modelling, R package (CRAN), si(): the seasonality index of Walsh and Lawler (1981), from 0 to 1.83 (open) <https://cran.r-project.org/package=hydroTSM>
- Walsh, R. P. D. and Lawler, D. M. (1981). Rainfall seasonality: description, spatial patterns and change through time. Weather 36(7), 201-208, the index; not opened here: as Sumner et al. (2001) and hydroTSM print it (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `monthly_mm` | $x_n$ | mm | real_array | [0.0, inf), test bound high 26470.0 (a month holds less than the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes)) | unstated | [0.4, 295.0]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the monthly sums of 1991-2020: 0.4 to 295.0 mm |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_positive_total` | precondition | the total of the twelve months is positive | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, eq. 1, p. 225: SI = (1/R) sum \|x_n - R/12\|, R the annual total; 0 when every month has the same total, 1.83 when one month has all of it |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `si` | - | real | [0.0, 1.8333333333333333] | 1e-12 |

**Conventions (CMP-2.3)**

- computed as the sum of |x_n / R - 1/12|, which equals the equation without R/12, which underflows for a subnormal R
- precipitation_seasonality gives the twelve normals of a reference period or the twelve monthly sums of a year with all of them, flow_regime the monthly volumes of a discharge series; a total of 0 has no index

**Assumptions**

None stated.

**Validation:** none: an index of the monthly totals

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: precondition a_positive_total: R divides
- `singular_at_bound`: limit exact_oracle: a single month of 1e-300 mm gives 11/6

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `totals_in_another_unit`: inputs times 2^e (`monthly_mm` e = 1.0) give outputs times 2^e (none)
- limit `exact_oracle`: SI equals the equation in exact fractions
- limit `one_wet_month`: one month with all the precipitation gives 11/6
- symmetry `months_in_another_order`: the months in reverse order give the same index

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the equation in exact fractions (fractions.Fraction) of the normals of Warszawa and of seeded monthly totals (`tests/unit/test_formulas_meteo_precipitation.py (limit exact_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="sielianinov_coefficient"></a>
### Sielianinov's hydrothermal coefficient of a month or a season

`hydrolog.statistics.meteo_hydrothermal.sielianinov_coefficient` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
k = \frac{P}{0.1\,\sum t}
$$

Plain text: `k = P / (0.1 sum t): P the precipitation [mm] and sum t the sum of the daily mean temperatures [°C·d] of the same days`

**Sources**

- Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the monthly sum of the air temperatures above 0 °C, the monthly mean times the days (open) <http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf>
- Kulik, M., Baryła, R., Czarnecki, Z. and Bochniak, A. (2016). Warunki hydrotermiczne w centralnej części rejonu kanału Wieprz-Krzna w 50-leciu (1966-2015). Agronomy Science 71(3), 1-12, p. 2: the coefficient; Table 1, pp. 5-6: P, the mean temperature and k of April-September at Sosnowica (open) <https://doi.org/10.24326/as.2016.3.1>
- Selyaninov, G. T. (1928). O sel'skokhozyaystvennoy otsenke klimata. Trudy po sel'skokhozyaystvennoy meteorologii 20, 165-177, the coefficient; not opened here: as Skowera and Puła (2004) print it (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `precipitation_mm` | $P$ | mm | real | [0.0, inf), test bound high 26470.0 (a season holds less than the world's greatest 12-month rainfall, 26,470 mm at Cherrapunji, 1 August 1860 - 31 July 1861 (WMO Archive of Weather and Climate Extremes)) | unstated | [3.2, 535.2]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the precipitation of the months April to September and of the seasons of 1991-2020: 3.2 to 535.2 mm |
| `temperature_sum_c_days` | $\sum t$ | °C·d | real | (-inf, inf), test bound low -99700.0 and high 20700.0 (a year of daily means at absolute zero (-273.15 °C times 365) or at the highest temperature on record (56.7 °C times 365)) | unstated | [150.8, 3297.0]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the sums of the months April to September and of the seasons of 1991-2020: 150.8 to 3297.0 °C·d |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `a_positive_temperature_sum` | precondition | sum t > 0: a month with a mean above 0 °C, a season with a warm day | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the monthly sum of the air temperatures above 0 °C, the monthly mean times the days |
| `a_finite_coefficient` | precondition | P / (0.1 sum t) is a finite number: sum t is not vanishingly small against P | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the monthly sum of the air temperatures above 0 °C, the monthly mean times the days |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `tenth` | $0.1$ | 1/10 | mm/(°C·d) | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k = P / (0.1 sum t), P the monthly precipitation [mm], sum t the monthly sum of the air temperatures above 0 °C, the monthly mean times the days |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `coefficient` | - | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- computed as 10 P / sum t, the factor 1 / 0.1 exact
- the series function gives a month's sum and mean times its days (April to September, a mean above 0 °C) or the sums over the days of April to September above 10 °C (Miś 2026; Tier B hydrothermal_season)

**Assumptions**

None stated.

**Validation:** none: an index of precipitation and temperature

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: preconditions a_positive_temperature_sum and a_finite_coefficient: sum t at 0 and vanishingly small is refused

**Properties (CMP-6.5)**

- units: unit_specific
- monotonic: `precipitation_mm` increasing, `temperature_sum_c_days` decreasing
- limit `exact_oracle`: k equals P / (0.1 sum t) in exact fractions
- limit `no_precipitation`: no precipitation gives k = 0

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: P / (0.1 sum t) in exact fractions (fractions.Fraction) (`tests/unit/test_formulas_meteo_hydrothermal.py (limit exact_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="sielianinov_class"></a>
### Class of Sielianinov's hydrothermal coefficient (Skowera and Puła)

`hydrolog.statistics.meteo_hydrothermal.sielianinov_class` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
k \le 0.4,\ (0.4, 0.7],\ (0.7, 1.0],\ (1.0, 1.3],\ (1.3, 1.6],\ (1.6, 2.0],\ (2.0, 2.5],\ (2.5, 3.0],\ > 3.0
$$

Plain text: `k <= 0.4 extremely dry, (0.4, 0.7] very dry, (0.7, 1.0] dry, (1.0, 1.3] fairly dry, (1.3, 1.6] optimal, (1.6, 2.0] fairly wet, (2.0, 2.5] wet, (2.5, 3.0] very wet, above 3.0 extremely wet`

**Sources**

- Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet (open) <http://www.acta-agrophysica.org/pdf-108195-38985?filename=38985.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `coefficient` | $k$ | - | real | [0.0, inf), test bound high 52.7 (ten times the largest monthly coefficient of the project's data (5.27 at Warszawa-Okęcie)) | unstated | [0.1, 5.27]: Hydrolog's test fixture tests/fixtures/warszawa_okecie_1991_2020.csv.gz: the daily data of IMGW-PIB's synop station Warszawa-Okęcie (352200375), 1991-2020, the coefficients of the months April to September of 1991-2020: 0.10 to 5.27 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `extremely_dry_to` | $0.4$ | 0.4 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `very_dry_to` | $0.7$ | 0.7 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `dry_to` | $1$ | 1.0 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `fairly_dry_to` | $1.3$ | 1.3 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `optimal_to` | $1.6$ | 1.6 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `fairly_wet_to` | $2$ | 2.0 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `wet_to` | $2.5$ | 2.5 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `very_wet_to` | $3$ | 3.0 | - | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `sielianinov_class` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- each limit belongs to the class below it, as the source prints (k <= 0.4 extremely dry); the source's text speaks of ten classes and lists nine
- Miś (2026) and Chmist-Sikorska et al. (2022) use other limits

**Assumptions**

None stated.

**Validation:** none: a classification

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: reference cases skowera-pula-*: each limit and just above it
- `gap_propagation`: type case coefficient-nan: NaN is refused; a month without a coefficient has no class

**Properties (CMP-6.5)**

- units: unit_specific
- limit `ordered_classes`: a larger coefficient never gives a drier class

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/meteo-indices-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** reference cases (CMP-6.1); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
| `spi_k_month_sums` | `hydrolog.statistics.meteo_spi.standardized_precipitation_index` | the k-month sum of a month is the sum of the monthly sums of the k months that end in it, missing unless all k are known; the sums of each calendar month over the reference period are fitted (spi_gamma_fit) when they are known in at least 80 % of its years, those without data counted | normal_share = 4/5 - (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: values in at least 80 % of the years of the period; section 4.3.3, p. 6: the normal of several months from the monthly normals) | the k-month sums of the reference period stay within its years (climate_indices 3.2.0 lets those of its first k - 1 months reach before it); every analysed month gets the SPI of its own sum under the fit of its calendar month; a month whose sums the fit refuses has no SPI (notice spi_not_fitted) | WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) |
| `relative_precipitation` | `hydrolog.statistics.meteo_spi.standardized_precipitation_index` | 100 P / N: a month's sum in % of the normal of its calendar month, a year's in % of the sum of the twelve monthly normals (classed by month_precipitation_class and kaczorowska_class) | – | the normals of the reference period; no percentage without a normal or with a normal of 0 | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), eq. 1, p. 109: RPI = P / P-bar 100 % |
| `temperature_monthly_means` | `hydrolog.statistics.meteo_temperature.temperature_means` | the mean of the daily Tmean, Tmax and Tmin of a month with fewer than 11 missing days and fewer than 5 in a row; of a year, the mean of its twelve monthly means, needing each | – | the twelve months weigh the same (WMO-No. 1203, 4.3.3 a, footnote 1: weighting by days not recommended) | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (a) and 4.4.1 (a), pp. 5-7; 4.3.3 (a), p. 6 |
| `temperature_normals_and_anomalies` | `hydrolog.statistics.meteo_temperature.temperature_means` | the normal of Tmean of a calendar month: the mean of its monthly means in the years of the reference period that have one, when they are at least 80 % of its years; the annual normal, the mean of the twelve monthly normals; an anomaly, a mean less its normal | – | the reference period is by default the analysed years; its years without data count among its years | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9; section 4.3.3 (a), p. 6 |
| `temperature_extremes` | `hydrolog.statistics.meteo_temperature.temperature_means` | the highest Tmax and the lowest Tmin of a month, a year and the period, with their dates, from the days that have a value | – | an extreme takes whatever days there are (WMO-No. 1203, 4.4.1 b); the first of equal extremes and its date | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b), p. 7 |
| `temperature_day_counts` | `hydrolog.statistics.meteo_temperature.temperature_days` | the days of each kind of threshold_days in a month with fewer than 11 missing days and fewer than 5 in a row, scaled to the days of the month; of a year, the sum of its twelve months, needing each | – | with gaps a month's count is not a whole number (climdex.pcic counts the days it has) | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.1 (d) and 4.4.1 (d), pp. 5-8 |
| `degree_day_sums` | `hydrolog.statistics.meteo_temperature.degree_days` | the sum of the degree_days of each day of a month, needing every day; of a year, the sum of its twelve months, needing each | – | no growing or heating season is cut out (Eurostat: computed daily and summed to the year) | Eurostat (2024). Energy statistics - cooling and heating degree days (nrg_chdd), reference metadata, updated 25 October 2024, section 3.4: HDD = 18 °C - Tm if Tm <= 15 °C, else 0; examples 12 °C gives 6, 16 °C gives 0 (Commission Directive (EU) 2015/1127, Annex) |
| `daily_temperature_range` | `hydrolog.statistics.meteo_temperature.temperature_range` | DTR: Tmax - Tmin of each day with both, its mean in a month with fewer than 11 missing days and fewer than 5 in a row, and of a year the mean of its twelve monthly means | – | a day with Tmax below Tmin is taken as it is (no check; an open question of the audit of 2026-11-18) | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, FD: days with TN < 0 °C; SU: TX > 25 °C; ID: TX < 0 °C; TR: TN > 20 °C; DTR: the monthly mean of TX - TN |
| `spell_year` | `hydrolog.statistics.meteo_spells.precipitation_spells` | a spell (spell_lengths) counts, whole, in the year of its last day: a spell over the start of a year is not cut, and a year wholly inside a spell that ends later has no longest spell | – | the year of the spell's end, as climdex.pcic 1.1-11 (its default spells.can.span.years = TRUE) and ECA&D; the ETCCDI's definition read literally cuts a spell at the start of the year (ADR-0044) | ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20: a spell can continue into the next year and is counted against the year in which the spell ends |
| `spell_summaries` | `hydrolog.statistics.meteo_spells.precipitation_spells` | per year with a value on every day: the spells that end in it, the longest of them (CDD, CWD) with its days, and the spells of at least 10, 15 and 20 days; per period: their means over those years and the distribution of the durations of their spells that are not open, per year | – | a year needs every day (climdex.pcic accepts up to 15 missing days); an open spell, beside a missing day or an end of the series, is left out of the distribution of durations only; min_duration_days shortens the list of spells, not the summaries | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) |
| `precipitation_sums` | `hydrolog.statistics.meteo_precipitation.precipitation_sums` | the sum of the daily precipitation of a month, needing every day or accumulated totals that cover the missing days; of a half-year (XI-IV, V-X), a season (DJF with the December before, MAM, JJA, SON) and a year, the sum of its months, needing each; a sum in % of its normal, 100 P / N | – | every sum of daily precipitation rounded to 1e-6 mm (round_sums); no percentage without a normal or with a normal of 0 | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.1 (c) and 4.4.1 (c), pp. 5-8: a sum needs complete data or accumulated observations covering the missing days |
| `precipitation_normals` | `hydrolog.statistics.meteo_precipitation.precipitation_sums` | the normal of a calendar month: the mean of its sums in the years of the reference period that have one, when they are at least 80 % of its years; of a half-year, a season or the year: the sum of the normals of its months | normal_share = 4/5 - (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2) | the reference period is by default the analysed years; its years without data count among its years | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: values in at least 80 % of the years; section 4.3.3, p. 6: the normal of several months from the monthly normals |
| `precipitation_maxima` | `hydrolog.statistics.meteo_precipitation.precipitation_maxima` | Rx1day and the largest n-day sums (Rx5day for 5): the n-day sum of a day is the sum of the n days ending on it, credited to the year of its last day and missing unless all n are known; a month's maximum takes the days it has, a year's needs every day of the year | – | the first of equal maxima, with its dates; climdex.pcic 1.1-11 credits a 5-day window to its middle day and takes a missing day as 0 | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, Rx1day, the largest daily precipitation of a period; Rx5day, the largest precipitation of 5 consecutive days (the interval ending on a day) |
| `precipitation_days` | `hydrolog.statistics.meteo_precipitation.precipitation_days` | the days with P at or above each threshold (R10mm and R20mm for 10 and 20 mm); a month's count scaled to its days when fewer than 11 days, and fewer than 5 in a row, are missing; a year's the sum of its twelve months | – | P >= threshold; with gaps a month's count is not a whole number (climdex.pcic counts the days it has) | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, R10mm and R20mm: the annual count of days with RR >= 10 mm and >= 20 mm |
| `precipitation_intensity` | `hydrolog.statistics.meteo_precipitation.precipitation_intensity` | sdii of each month and year with every day, and of each calendar month over those months of the period together; the mean annual sum and the mean SDII of the years with one | – | an accumulated total is a missing day for sdii and counts in the annual sum; PRCPTOT rounded to 1e-6 mm; a month or year without a wet day has W = 0 and no SDII | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, SDII: the precipitation of the wet days (RR >= 1 mm) of a period over their number; PRCPTOT: the precipitation of the wet days of the year; R95pTOT: the annual total of the days with RR > RRwn95, the 95th percentile of the precipitation of the wet days of the base period 1961-1990 |
| `heavy_precipitation_thresholds` | `hydrolog.statistics.meteo_precipitation.heavy_precipitation` | the thresholds: wet_day_percentile of the wet days of the reference period at each percentile, from at least 100 wet days; each year with every day: heavy_precipitation_share at each threshold, and the mean share of those years | – | the reference period is by default the analysed years (the ETCCDI's base is 1961-1990); the minimum of 100 wet days is Hydrolog's (ADR-0032), no source gives one | Bronaugh, D. (2020). climdex.pcic 1.1-11: PCIC implementation of Climdex routines, R package, R/climdex.r: the percentiles of the wet days (not NA, at least 1 mm) of the base period by quantile type 8 |
| `precipitation_regime` | `hydrolog.statistics.meteo_precipitation.precipitation_seasonality` | each monthly normal of the reference period in % of their sum and over their mean; precipitation_concentration_index and seasonality_index, with their classes, of the twelve normals and of each year with its twelve monthly sums, and the means of the yearly indices | – | the indices of the normals and the means of the yearly indices differ and both are given (Sumner et al. 2001); a total of 0 has no index | Sumner, G., Homar, V. and Ramis, C. (2001). Precipitation seasonality in eastern and southern coastal Spain. International Journal of Climatology 21, 219-247, p. 225: the SI of the mean monthly totals and the mean of the yearly SI |
| `hydrothermal_months` | `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient` | sielianinov_coefficient of each month April to September: P its precipitation sum, sum t its mean daily temperature times its days, for a month with both and a mean above 0 °C | – | the months April to September (Radzka 2014); the sums of precipitation rounded to 1e-6 mm | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and (c), pp. 7-8: a monthly mean needs fewer than 11 missing days and fewer than 5 in a row, a monthly sum every day or accumulated totals covering the missing days |
| `hydrothermal_season` | `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient` | sielianinov_coefficient of the days of April to September with a mean temperature above 10 °C: P and sum t summed over them, in a year whose every day of April to September has both values | – | the day filter of Polish practice (Miś 2026), not the period between the stable transitions through 10 °C of Russian practice; an accumulated total is a missing day of the season | Miś, F. (2026). Spatiotemporal variability of atmospheric drought during the growing season in Poland: a multi-index analysis based on SPEI, VPD, and HTC (1980-2024). Theoretical and Applied Climatology 157(12), 790, section 2, eq. 4: the days with a mean temperature above 10 °C, calculated for the April-September period |
| `hydrothermal_period` | `hydrolog.statistics.meteo_hydrothermal.hydrothermal_coefficient` | per month April to September: the mean coefficient of the years with one and the count of each class; the mean season coefficient and its class | – | the class of the mean, not the most frequent class | Skowera, B. and Puła, J. (2004). Skrajne warunki pluwiotermiczne w okresie wiosennym na obszarze Polski w latach 1971-2000. Acta Agrophysica 3(1), 171-177, p. 172: k <= 0.4 extremely dry, 0.4 < k <= 0.7 very dry, 0.7 < k <= 1.0 dry, 1.0 < k <= 1.3 fairly dry, 1.3 < k <= 1.6 optimal, 1.6 < k <= 2.0 fairly wet, 2.0 < k <= 2.5 wet, 2.5 < k <= 3.0 very wet, k > 3.0 extremely wet |
| `snow_cover_day` | `hydrolog.statistics.meteo_snow.snow_cover` | a day with snow cover has a depth of at least 1 cm; the days of a month are scaled to its days when fewer than 11 days, and fewer than 5 in a row, are missing; a winter's days are the sum of its months | snow_cover_cm = 1.0 cm (ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.3.9: SD1, snow days (SD >= 1 cm)) | at least 1 cm, as IMGW-PIB's yearbooks and ECA&D's SD1; IMGW-PIB's normals count > 0 cm (SNIEG_0, the same with whole centimetres) and > 1 cm (SNIEG_1) | IMGW-PIB (2023). Rocznik Meteorologiczny 2022, p. 5: snow cover, a layer of at least 1 cm covering more than half of the terrain around the station, measured at 06 UTC |
| `snow_season` | `hydrolog.statistics.meteo_snow.snow_cover` | a winter is the snow season 1 August - 31 July named after the year it ends; it is complete when every month October to May has enough days | – | the whole cold season together: snow of late October starts its winter (Polish studies also use X-V, XI-III or XII-II) | Urban, G. (2015). Przegląd Geograficzny 87(3), pp. 498-499: the snow season from 1 August to 31 July, after Falarz |
| `snow_season_extremes` | `hydrolog.statistics.meteo_snow.snow_cover` | the largest depth with its day, the first and the last day with snow cover and the sum of the depths of fresh snow of a winter, from whatever days it has | – | the first of equal largest depths | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b) and (d), pp. 7-8: extremes from whatever days, counts of months whose mean could be calculated |
| `snow_season_medians` | `hydrolog.statistics.meteo_snow.snow_cover` | the median first and last day with snow cover of the complete winters: each date a day of the season on a calendar without 29 February, the median of those days turned back into a date | – | 29 February counts as 28 February, so a date is the same day in every winter; a median between two days is rounded half to even | Urban, G. (2015). Przegląd Geograficzny 87(3), pp. 498-499: the snow season from 1 August to 31 July, after Falarz |
| `wmo_monthly_mean` | `hydrolog.statistics._climate.monthly_means` | the mean of the daily values of a month with fewer than 11 missing days and fewer than 5 missing in a row, and at least one value | missing_days = 11.0 d (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and footnote 4, p. 7: a mean is not calculated when 11 or more days are missing or 5 or more consecutive days); missing_run = 5.0 d (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and footnote 4, p. 7: a mean is not calculated when 11 or more days are missing or 5 or more consecutive days) | a day of the grid without a date counts as missing | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (a) and footnote 4, p. 7: a mean is not calculated when 11 or more days are missing or 5 or more consecutive days |
| `wmo_monthly_count` | `hydrolog.statistics._climate.monthly_counts` | the days of an event in a month whose mean could be calculated, scaled to the days of the month: the events over the days with a value times the days of the month | – | the scaling of every such month (WMO-No. 1203 gives the ratio for normals); a count is then not a whole number | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (d) and 4.4.1 (d), pp. 5-8 |
| `wmo_monthly_sum` | `hydrolog.statistics._climate.monthly_totals` | the sum of the daily values of a month with every day | – | no sum of a month with a missing day | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, sections 4.3.1 (c) and 4.4.1 (c), pp. 5-8 |
| `accumulated_totals` | `hydrolog.statistics._climate.monthly_precipitation` | a total flagged as accumulated stands for the missing days just before it when, with its own day, they are fewer than 5; a month's sum takes such totals when fewer than 11 of its days are covered by them | – | a block over the start of a month is judged on its whole length; the total counts in the month of its own day | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (c), pp. 7-8: accumulated observations that cover the full period of missing data, not 11 or more days nor 5 or more in a row |
| `wmo_normal` | `hydrolog.statistics._climate.normal` | the normal of a calendar month: the mean of its values in the years of the reference period with one, when they are at least 80 % of its years | normal_share = 4/5 - (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: 24 or more of 30 years) | every year of the reference period counts, those without data too; no consecutive-years criterion | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9 |
| `multimonth_normal` | `hydrolog.statistics._climate.multimonth_normal` | the normal of a year, half-year or season: the sum of the normals of its months for a sum or a count, their mean for a mean | – | from the monthly normals, not from the annual values (WMO-No. 1203, 4.3.3: identical without missing months) | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.3.3, p. 6 |
| `block_extreme` | `hydrolog.statistics._climate.block_extreme` | the extreme of a month from the days that have a value, with the first date it occurs | – | an annual extreme of a statistic that needs every day is taken by its series function from complete years only | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.1 (b), p. 7: extremes regardless of missing data |
| `rounded_sums` | `hydrolog.statistics._climate.round_sums` | every sum of daily precipitation rounded to 1e-6 mm | – | 0.1-mm data summed in binary depend on the order of the additions; rounded, sums equal in decimal are equal numbers (ties of the Mann-Kendall test, the first of equal windows); at most 5e-7 mm per sum | Hydrolog ADR-0032 (2026-11-13): meteorological statistics of a station, the group meteo, the sums of daily precipitation |
| `years_of_a_series` | `hydrolog.statistics._climate.year_of` | the calendar year (January - December), the Polish hydrological year (November - October) named after the year it ends, or the snow season (August - July) named after the year it ends | – | a year is laid on the grid whole, its days without a value missing | WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, chapter 2: normals of calendar months |
