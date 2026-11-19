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

## Delegated computations (CMP-1.2)

| Computation | Library | Versions | Smoke case | Test |
|---|---|---|---|---|
| nash_shape_root | scipy.optimize.brentq | scipy>=1.10 (1.18.1 locked) | the root N of f(N) = (N-1)^N e^-(N-1) / Gamma(N) = f(2.55) on [1.1, 20] with xtol 1e-6 is 2.55 within 1e-6 (spec lutz) | `tests/unit/test_formulas_lutz.py::test_the_delegated_root_finder_finds_a_known_root` |
