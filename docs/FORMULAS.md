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
| [Mann-Kendall test of a monotonic trend: S, Var(S) with ties, Z and the two-sided p](#mann_kendall) | `hydrolog.statistics.stationarity.mann_kendall` | referenced | 1 | not measured |
| [Sen's slope of a series with Conover's intercept](#sen_slope) | `hydrolog.statistics.stationarity.sen_line` | referenced | 1 | not measured |
| [Gilbert's confidence interval of Sen's slope](#sen_interval) | `hydrolog.statistics.stationarity.sen_interval` | referenced | 1 | not measured |
| [Pettitt's change-point test: K, the change point and the approximate p](#pettitt) | `hydrolog.statistics.homogeneity.pettitt` | referenced | 1 | not measured |
| [Exact two-sided p-value of the two-sample Kolmogorov-Smirnov D, ties respected](#ks_exact) | `hydrolog.statistics.homogeneity.ks_exact` | referenced | 1 | not measured |
| [Values of the duration curve equalled or exceeded on p % of the days (Weibull positions, linear interpolation)](#exceedance_values) | `hydrolog.statistics.duration.exceedance_values` | referenced | 1 | not measured |
| [Baseflow of a daily series by the Lyne and Hollick filter (standard approach of Ladson et al. 2013)](#lyne_hollick) | `hydrolog.statistics.baseflow.lyne_hollick_filter` | referenced | 1 | not measured |
| [Baseflow index: the volume of baseflow over the volume of flow](#baseflow_index) | `hydrolog.statistics.baseflow.baseflow_index` | referenced | 1 | not measured |
| [Recession constant of the total flow: the median daily ratio of runs of falling flow](#recession_constant) | `hydrolog.statistics.baseflow.recession_ratio` | oracle only | 1 | not measured |
| [Pardé's coefficients: the mean discharge of each month over the mean annual discharge](#parde_coefficients) | `hydrolog.statistics.regime.parde_coefficients` | referenced | 1 | not measured |
| [The March-April share of the annual volume of the mean monthly flows](#spring_share) | `hydrolog.statistics.regime.spring_share` | oracle only | 1 | not measured |
| [Dynowska's type of a Polish river regime from Pardé's coefficients](#dynowska_regime_type) | `hydrolog.statistics.regime.dynowska_regime_type` | referenced | 1 | not measured |
| [Mean direction and concentration of times on the circles of their years (Bayliss and Jones)](#circular_mean) | `hydrolog.statistics.seasonality.circular_mean` | oracle only | 1 | not measured |
| [Least squares fit of the mean and the harmonics of the annual cycle](#harmonic_fit) | `hydrolog.statistics.harmonics.harmonic_fit` | oracle only | 1 | not measured |
| [Standard deviation of a sample, with the divisor n - 1](#sample_standard_deviation) | `hydrolog.statistics.characteristic.sample_standard_deviation` | referenced | 1 | not measured |
| [Coefficient of variation of a sample of a quantity with a true zero](#coefficient_of_variation) | `hydrolog.statistics.characteristic.coefficient_of_variation` | oracle only | 1 | not measured |
| [Fisher-Pearson coefficient of skewness g1 of a sample](#fisher_pearson_skewness) | `hydrolog.statistics.characteristic.fisher_pearson_skewness` | oracle only | 1 | not measured |
| [Half-width of the Student t confidence interval of a mean of yearly means](#mean_interval_half_width) | `hydrolog.statistics.characteristic.mean_interval_half_width` | referenced | 1 | not measured |
| [Discharge at a water level by the power-law rating curve](#rating_curve) | `hydrolog.hydrometrics.rating_curve.rating_discharge` | oracle only | 1 | not measured |
| [Rating curve Q = a (H - H0)^b fitted to stage-discharge pairs by least squares on Q](#rating_curve_fit) | `hydrolog.hydrometrics.rating_curve.fit_rating_curve` | oracle only | 1 | not measured |
| [Plausibility of a rating curve as the curve of one stage-discharge relation (Hydrolog's rule of ADR-0041)](#rating_curve_plausibility) | `hydrolog.hydrometrics.rating_curve.rating_curve_plausibility` | unreferenced | 1 | not measured |
| [Rybczyński's zones of low, medium and high background water levels (NTW, STW, WTW)](#rybczynski_zones) | `hydrolog.hydrometrics.rating_curve.rybczynski_zones` | unreferenced | 1 | not measured |

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

<a id="mann_kendall"></a>
### Mann-Kendall test of a monotonic trend: S, Var(S) with ties, Z and the two-sided p

`hydrolog.statistics.stationarity.mann_kendall` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
S = \sum_{i<j} \operatorname{sgn}(x_j - x_i),\quad \operatorname{Var}(S) = \frac{n(n-1)(2n+5) - \sum_p t_p(t_p-1)(2t_p+5)}{18},\quad Z = \frac{S - \operatorname{sgn} S}{\sqrt{\operatorname{Var}(S)}},\quad p = \begin{cases} P(|S'| \ge |S|) & n < n_0 \\ 2\,P(Z' > |Z|) & n \ge n_0 \end{cases}
$$

Plain text: `S = sum_{i<j} sgn(x_j - x_i); Var(S) = [n (n - 1) (2n + 5) - sum_p t_p (t_p - 1) (2 t_p + 5)] / 18 over the groups of t_p equal values; Z = (S - 1) / sqrt(Var(S)) for S > 0, 0 for S = 0, (S + 1) / sqrt(Var(S)) for S < 0; p = P(|S'| >= |S|) of the exact distribution of S below n0 values, else 2 P(Z' > |Z|) of the standard normal`

**Sources**

- Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, eqs. 16.1 to 16.4, pp. 209-211: S, Var(S) corrected for ties, Z with a continuity correction of one; section 16.4.1 and table A18: the exact probabilities of S below n = 10 (open) <https://digital.library.unt.edu/ark:/67531/metadc1197046/m2/1/high_res_d/7037501.pdf>
- Hirsch, R.M., Slack, J.R., Smith, R.A. (1981). Techniques of trend analysis for monthly water quality data. U.S. Geological Survey Open-File Report 81-488 (Water Resources Research 18(1), 107-121, 1982), eqs. 1, 2, 3b and 4, PDF pp. 6-7: S, its variance with ties after Kendall (1975) and Z; 'even for n = 10 the normal approximation is excellent, provided one uses a continuity correction of one unit' (open) <https://pubs.usgs.gov/of/1981/0488/report.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 1.1 to 1.4, pp. 10-11: S with sgn(0) = 0, its variance without the correction for ties, u = (S - sgn S) / sigma, the normal approximation 'już dla N >= 10' (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point Detection, R package version 1.1.10, CRAN, R/mk.test.R: at least 3 values ('x' must have at least 3 elements), S, varS corrected for ties, z = sgn(S) (|S| - 1) / sigma, the two-sided p 2 min(0.5, P(Z > |z|)) (open) <https://cran.r-project.org/package=trend>
- Mann, H.B. (1945). Nonparametric tests against trend. Econometrica 13, 245-259 (author-provided)
- Kendall, M.G. (1975). Rank Correlation Methods, 4th ed. Griffin, London, p. 55: the normal approximation of S from n = 10 (quoted by Gilbert 1987, p. 211) (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the test counts the signs of differences and Sen's slope scales with the unit of the series, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage or a temperature may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point Detection, R package version 1.1.10, CRAN, R/mk.test.R: at least 3 values ('x' must have at least 3 elements), S, varS corrected for ties, z = sgn(S) (\|S\| - 1) / sigma, the two-sided p 2 min(0.5, P(Z > \|z\|)) |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `exact_below` | $n_0$ | 10 | values | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.4.2, p. 211: the normal approximation from n = 10 after Kendall (1975, p. 55), as KZGW (2017, p. 11) and Hirsch et al. (1981, PDF p. 7) state it; section 16.4.1 and table A18: the exact probabilities below |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `s` | - | integer | (-inf, inf) | 4 ulp of the bound |
| `var_s` | - | real | [0.0, inf) | 4 ulp of the bound |
| `z` | - | real | (-inf, inf) | 4 ulp of the bound |
| `p_value` | - | real | (0.0, 1.0] | 4 ulp of the bound |
| `p_value_method` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- values tie when exactly equal (round a series computed in floating point to its precision first); sgn(0) = 0, as KZGW (2017) eq. 1.2 defines it, though its worked examples count a tied pair as -1
- Var(S) corrected for the groups of ties (Gilbert eq. 16.3, Hirsch et al. eq. 3b, R's trend); KZGW (2017, p. 11) leaves the correction out
- Z with a continuity correction of one toward 0 and Z = 0 for S = 0 (Gilbert eq. 16.4, KZGW eq. 1.4)
- the p-value is two-sided: below n0 values the exact P(|S'| >= |S|) over every distinct ordering of the values, equally likely under no trend, ties respected (the q-multinomial coefficients, MacMahon 1916); from n0 values 2 P(Z' > |Z|) from the upper tail of the normal distribution (scipy's norm.sf, as R's trend), which keeps its digits for a strong trend
- a p-value below the smallest positive float (|Z| above about 38.5) is set to it, the end of the physical range (0, 1]
- the series in any unit: the statistics have none

**Assumptions**

- the values are independent and identically distributed under no trend (Gilbert 1987, p. 213; KZGW 2017, p. 10): serial correlation, as of daily or monthly flows, makes the test reject too often
- the values are in time order, one per time step; gaps of the record do not enter the test

**Validation:** none: a test of the hypothesis of no trend; its sources compare it with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: sqrt(Var(S)) at Var(S) = 0, a series of equal values: Z = 0 by S = 0, limit equal_values
- `exp_overflow`: the normal tail exp(-z^2/2) of a strong trend: 50 increasing values keep p = 1.3e-24 and 10,000 give the smallest positive float, not 0 (test_a_strong_trend_keeps_a_p_value_above_zero)
- `gap_propagation`: type case values-nan_element: a gap is refused
- `many_small_terms`: S sums n(n - 1)/2 signs in integers and Var(S) is one division of integers (test_s_of_a_long_series_is_exact)

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (none)
- limit `equal_values`: a series of equal values: S = 0, Var(S) = 0, Z = 0 (Gilbert's eq. 16.4 for S = 0) and p = 1, every ordering being the same
- limit `monotone_series_exact`: a strictly monotone series below n0 values has the exact p 2/n!
- limit `normal_tail`: from n0 values p equals erfc(|Z| / sqrt(2)), the normal tail of another algorithm
- symmetry `negated_series`: the negated series has the negated S and Z, the same Var(S) and p
- symmetry `reversed_series`: the series in reverse order has the negated S and Z, the same Var(S) and p

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/trend-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the null distribution of S by every ordering of the series (the permutation test's definition), with Fraction probabilities: p and the variance of the distribution, which is Var(S) with ties (`tests/unit/test_formulas_trend.py (test_the_exact_p_and_var_s_are_those_of_every_ordering)`)
- exact: the Mahonian numbers of the inversions of the permutations of n by the recurrence M(n, k) = M(n, k - 1) + M(n - 1, k) - M(n - 1, k - n), not the product of the q-factorial (`tests/unit/test_formulas_trend.py (test_the_exact_p_without_ties_is_that_of_the_mahonian_numbers)`)
- established: scipy.stats.kendalltau of the series against its times (SciPy 1.18.1): S from tau-b and, without ties below n0 values, the exact p (`tests/unit/test_formulas_trend.py (test_s_and_the_exact_p_are_scipys_kendalltau)`)
- frozen: R 4.4.3 trend 1.1.10 mk.test, modifiedmk 1.6 mkttest and Kendall 2.2.2 MannKendall on 13 series (`tests/oracles/trend_regime/r_oracle_outputs_headed.csv (tests/unit/test_formulas_trend.py, test_mann_kendall_is_rs)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="sen_slope"></a>
### Sen's slope of a series with Conover's intercept

`hydrolog.statistics.stationarity.sen_line` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
b = \operatorname*{median}_{t_i < t_j} \frac{x_j - x_i}{t_j - t_i},\quad a = \operatorname{median}(x) - b \operatorname{median}(t)
$$

Plain text: `b = median of the N' slopes (x_j - x_i) / (t_j - t_i) over the pairs with t_i < t_j; a = median(x) - b median(t)`

**Sources**

- Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 (open) <https://digital.library.unt.edu/ark:/67531/metadc1197046/m2/1/high_res_d/7037501.pdf>
- Helsel, D.R., Hirsch, R.M., Ryberg, K.R., Archfield, S.A., Gilroy, E.J. (2020). Statistical Methods in Water Resources. U.S. Geological Survey Techniques and Methods 4-A3, section 10.1.1, eqs. 10.1 to 10.3, pp. 266-268: the Theil-Sen slope, the median of all pairwise slopes, and the intercept b0 = y_med - b1 x_med (Conover 1999) (open) <https://pubs.usgs.gov/tm/04/a03/tm4a3.pdf>
- Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau. Journal of the American Statistical Association 63, 1379-1389 (author-provided)
- Conover, W.J. (1980). Practical Nonparametric Statistics, 2nd ed. Wiley, New York, the intercept median(x) - slope median(t) (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the test counts the signs of differences and Sen's slope scales with the unit of the series, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage or a temperature may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |
| `times` | $t_i$ | a | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (years of the Common Era or steps of a series of at most 5,000 values: a million exceeds both) | unstated | [1965.0, 2005.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: the years 1965 to 2005 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one time per value | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 |
| `times_in_order` | physical | t[i+1] >= t[i]: the values in time order, several of one time allowed | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 |
| `two_times` | precondition | t[-1] > t[0]: two values of different times make a slope | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 |
| `slopes_in_float64` | precondition | 2 (max x - min x) / (least step of t) and the line (max x - min x) / (least step of t) max\|t\| + max\|x\| are finite in float64: every slope, the difference of two slopes and the intercept are | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `slope` | m3/s/a | real | (-inf, inf) | 4 ulp of the bound |
| `intercept` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `n_slopes` | - | integer | [1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the slopes of the pairs of different times only: several values of one time (Gilbert's eq. 16.5 case) give no slope among themselves
- per unit of the times given: per year with years, per step with the steps 0, 1, 2 … of the series; R's trend and modifiedmk take the slopes per step of the index, the same where the years follow each other
- the median of an even number of slopes is the mean of the middle two
- Conover's intercept median(x) - b median(t) (Helsel et al. 2020, eq. 10.3), the line at t = 0; the trend vignette's alternative is the median of the residuals
- at most 5,000 values: every slope is held in memory, eight bytes each, 100 MB at 5,000 values; the estimator is meant for independent values, annual or monthly, whose longest records have a few hundred years

**Assumptions**

- a linear trend of the values in time; the estimator is robust to outliers, not to serial correlation of the values (as the Mann-Kendall test)

**Validation:** none: an estimator of the slope of a monotonic trend; its sources compare it with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: 1 / (t_j - t_i): pairs of one time give no slope and series of one time are refused by the precondition two_times; slopes beyond float64 by slopes_in_float64 (test_a_series_of_one_time_and_slopes_beyond_float64_are_refused)
- `gap_propagation`: type cases values-nan_element and times-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_values`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`slope` e = 1.0, `intercept` e = 1.0)
- scaling `unit_of_the_times`: inputs times 2^e (`times` e = 1.0) give outputs times 2^e (`slope` e = -1.0)
- limit `straight_line`: the values of a straight line give its slope
- limit `exact_median`: the slope is the median of the slopes in exact rational arithmetic, rounded once
- symmetry `negated_values`: the negated values have the negated slope and intercept

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/trend-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the median of the slopes in exact rational arithmetic (fractions) (`tests/unit/test_formulas_trend.py (limit exact_median)`)
- established: scipy.stats.theilslopes with method='separate': the median of the slopes of the pairs with x_j > x_i and the intercept median(y) - slope median(x) (SciPy 1.18.1) (`tests/unit/test_formulas_trend.py (test_the_line_is_scipys_theilslopes)`)
- frozen: R 4.4.3 trend 1.1.10 sens.slope and modifiedmk 1.6 mkttest on 13 series (`tests/oracles/trend_regime/r_oracle_outputs_headed.csv (tests/unit/test_formulas_trend.py, test_sens_slope_is_rs)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="sen_interval"></a>
### Gilbert's confidence interval of Sen's slope

`hydrolog.statistics.stationarity.sen_interval` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
C = z_{1-\alpha/2}\sqrt{\operatorname{Var}(S)},\quad M_1 = \frac{N' - C}{2},\quad M_2 = \frac{N' + C}{2},\quad b_L = Q_{(M_1)},\quad b_U = Q_{(M_2+1)}
$$

Plain text: `C = z(1 - alpha/2) sqrt(Var(S)); M1 = (N' - C) / 2, M2 = (N' + C) / 2; lower = the M1-th and upper = the (M2 + 1)-th of the N' ordered slopes, interpolated linearly between ranks`

**Sources**

- Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 (open) <https://digital.library.unt.edu/ark:/67531/metadc1197046/m2/1/high_res_d/7037501.pdf>
- Helsel, D.R., Hirsch, R.M., Ryberg, K.R., Archfield, S.A., Gilroy, E.J. (2020). Statistical Methods in Water Resources. U.S. Geological Survey Techniques and Methods 4-A3, section 10.1.1, eqs. 10.1 to 10.3, pp. 266-268: the Theil-Sen slope, the median of all pairwise slopes, and the intercept b0 = y_med - b1 x_med (Conover 1999) (open) <https://pubs.usgs.gov/tm/04/a03/tm4a3.pdf>
- Sen, P.K. (1968). Estimates of the regression coefficient based on Kendall's tau. Journal of the American Statistical Association 63, 1379-1389 (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the test counts the signs of differences and Sen's slope scales with the unit of the series, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage or a temperature may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |
| `times` | $t_i$ | a | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (years of the Common Era or steps of a series of at most 5,000 values: a million exceeds both) | unstated | [1965.0, 2005.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: the years 1965 to 2005 |
| `var_s` | $\operatorname{Var}(S)$ | - | real | [0.0, inf), test bound high 14000000000.0 (Var(S) of 5,000 values without ties, the most the spec takes, is 1.389e10) | unstated | [3139.0, 7921.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1 (pp. 11-12), 1.2 (pp. 13-14), 3.10 (p. 48) and 3.13 (pp. 55-56): the Mann-Kendall test of the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: n = 30 to 41 with ties, Var(S) 3,139.7 to 7,920.7 |
| `alpha` | $\alpha$ | - | real | (0.0, 1.0) | unstated | [0.05, 0.05]: Obserwator 3.1.0.dev0, analysis registry (src/obserwator/store/analysis_registry.py), the stored analyses mann_kendall.* of stats mann-kendall; KZGW (2017), p. 11, options alpha = 0.05; the significance level 0.05 of KZGW's test |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one time per value | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 |
| `times_in_order` | physical | t[i+1] >= t[i]: the values in time order, several of one time allowed | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 |
| `two_times` | precondition | t[-1] > t[0]: two values of different times make a slope | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 |
| `slopes_in_float64` | precondition | 2 (max x - min x) / (least step of t) and the line (max x - min x) / (least step of t) max\|t\| + max\|x\| are finite in float64: every slope, the difference of two slopes and the intercept are | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 |
| `ranks_within_slopes` | precondition | 1 <= M1 and M2 + 1 <= N': both ranks lie among the N' ordered slopes (C <= N' - 2) | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, steps 1 to 4, p. 218: C = Z(1 - alpha/2) [Var(S)]^(1/2), M1 = (N' - C)/2, M2 = (N' + C)/2, the limits the M1-th and the (M2 + 1)-th of the ordered slopes, 'for n as small as 10 unless there are many ties'; Example 16.5, p. 219, interpolates between ranks, as subroutine CONINT, appendix B, p. 289 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `lower` | m3/s/a | real | (-inf, inf) | 4 ulp of the bound |
| `upper` | m3/s/a | real | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Gilbert's linear interpolation between ranks (his Example 16.5 and subroutine CONINT, appendix B); R's trend rounds the ranks (round(), half to even) and Helsel et al. (2020, eqs. 10.6-10.7) take whole ranks, which move the limits by up to 5 % of a limit at n <= 34 (frozen oracle, ADR-0063)
- the Var(S) of the test of the same values, given by the caller; Gilbert's Exercise 16.3 builds it without the correction for ties on purpose
- z(1 - alpha/2) of the standard normal distribution (scipy's norm.ppf); an alpha whose 1 - alpha/2 rounds to 1 has no interval
- stats mann-kendall gives the interval from ten values (Gilbert 1987, p. 218: the normal approximation of S it rests on), null below
- at most 5,000 values, as Sen's slope

**Assumptions**

- S approximately normal under no trend, from about ten values unless there are many ties (Gilbert 1987, p. 218)

**Validation:** none: a non-parametric confidence interval of the slope (Gilbert 1987, section 16.5); its sources compare it with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: sqrt(Var(S)) at Var(S) = 0: the middle slopes, limit holds_the_slope; ranks outside the slopes are refused by the precondition ranks_within_slopes
- `gap_propagation`: type cases values-nan_element and times-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `var_s` decreasing, `alpha` increasing
- scaling `unit_of_the_values`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`lower` e = 1.0, `upper` e = 1.0)
- scaling `unit_of_the_times`: inputs times 2^e (`times` e = 1.0) give outputs times 2^e (`lower` e = -1.0, `upper` e = -1.0)
- limit `holds_the_slope`: the interval holds Sen's slope, and at Var(S) = 0 it is the middle slopes

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/trend-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the ordered slopes sorted in full (numpy.sort) and the ranks interpolated on the whole ladder of ranks (numpy.interp), as Hydrolog 0.9.0.dev2 computed them (`tests/unit/test_formulas_trend.py (test_the_interval_is_the_interpolation_of_the_sorted_slopes)`)
- frozen: R 4.4.3 trend 1.1.10 sens.slope at 90 and 95 % on 13 series (`tests/oracles/trend_regime/r_oracle_outputs_headed.csv (tests/unit/test_formulas_trend.py, test_sens_interval_rounds_as_rs)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="pettitt"></a>
### Pettitt's change-point test: K, the change point and the approximate p

`hydrolog.statistics.homogeneity.pettitt` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
U_t = 2\sum_{i \le t} r_i - t(n + 1),\quad K = \max_{1 \le t < n} |U_t|,\quad p = \min\left(1,\ 2 e^{-6K^2/(n^3 + n^2)}\right)
$$

Plain text: `U_t = 2 sum_{i<=t} r_i - t (n + 1) = sum_{i<=t} sum_{j>t} sgn(x_i - x_j) for t = 1 … n - 1 with the mid-ranks r_i; K = max_t |U_t|, the change point the first t of K; p = min(1, 2 exp(-6 K^2 / (n^3 + n^2)))`

**Sources**

- Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point Detection, R package version 1.1.10, CRAN, R/pettitt.test.R and its help page: U_k = 2 sum_{i<=k} r_i - k (n + 1) of the ranks, U* = max |U_k|, the change point where |U_k| is largest, p = min(1, 2 exp(-6 U*^2 / (n^3 + n^2))), 'good for p <= 0.5' (after Verstraeten et al. 2006) (open) <https://cran.r-project.org/package=trend>
- Hussain, M.M. pyHomogeneity: a Python package for homogeneity tests of time series data, version 1.1, GitHub mmhs013/pyHomogeneity, pyhomogeneity.py, __pettitt and pettitt_test: U = 2 cumsum(r) - k (n + 1) over k = 1 … n - 1, the first k of max |U|, p = 2 exp(-6 U^2 / (n^3 + n^2)) (open) <https://github.com/mmhs013/pyHomogeneity>
- Pettitt, A.N. (1979). A non-parametric approach to the change-point problem. Journal of the Royal Statistical Society, Series C (Applied Statistics) 28(2), 126-135 (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the tests rank the values, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1, 1.2, 3.10 and 3.13 (pp. 11-56): the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 2: a split t of 1 … n - 1 | Hussain, M.M. pyHomogeneity: a Python package for homogeneity tests of time series data, version 1.1, GitHub mmhs013/pyHomogeneity, pyhomogeneity.py, __pettitt and pettitt_test: U = 2 cumsum(r) - k (n + 1) over k = 1 … n - 1, the first k of max \|U\|, p = 2 exp(-6 U^2 / (n^3 + n^2)) |
| `values_not_all_equal` | precondition | min(x) < max(x): equal values give U_t = 0 for every t, no change point | Pohlert, T. trend: Non-Parametric Trend Tests and Change-Point Detection, R package version 1.1.10, CRAN, R/pettitt.test.R and its help page: U_k = 2 sum_{i<=k} r_i - k (n + 1) of the ranks, U* = max \|U_k\|, the change point where \|U_k\| is largest, p = min(1, 2 exp(-6 U*^2 / (n^3 + n^2))), 'good for p <= 0.5' (after Verstraeten et al. 2006) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `k` | - | integer | [0.0, inf) | 4 ulp of the bound |
| `p_value` | - | real | (0.0, 1.0] | 4 ulp of the bound |
| `change_point_index` | - | integer | [1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the mid-ranks of tied values (scipy's rankdata, R's rank)
- K over t = 1 … n - 1 (R's trend also takes t = n, where U_n = 0); the change point is the first t of K (R's trend returns every t of K), the number of values before the change, which names the year of the first value after it in homogeneity_tests
- p is Pettitt's approximation 2 exp(-6 K^2 / (n^3 + n^2)), capped at 1, good for p <= 0.5 (R's trend); it is conservative for short series: ten increasing values give 0.066 where the exact permutation p is 2 / C(10, 5) = 0.0079
- a p-value below the smallest positive float is set to it, the end of the physical range (0, 1]

**Assumptions**

- independent values with one change of location at most

**Validation:** none: a test of the hypothesis of no change; its sources compare it with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `exp_overflow`: exp(-6 K^2 / (n^3 + n^2)) of a long series with a step underflows: p is the smallest positive float, not 0 (test_a_long_step_keeps_a_p_value_above_zero)
- `gap_propagation`: type case values-nan_element: a gap is refused
- `many_small_terms`: the cumulative sums of the mid-ranks are whole numbers and half-numbers, exact in float64 (limit pairwise_definition, test_k_of_a_long_series_is_exact)

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_series`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (none)
- limit `complete_separation`: ten increasing values: K = n^2/4 = 25 at t = 5 and p = 2 exp(-6 625 / 1100)
- limit `pairwise_definition`: K and its t from the ranks equal those of the double sum of signs
- symmetry `negated_series`: the negated series has the same K, change point and p

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/trend-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: U_t by its double sum of signs of the pairs on either side of t, not the ranks (`tests/unit/test_formulas_trend.py (limit pairwise_definition)`)
- frozen: R 4.4.3 trend 1.1.10 pettitt.test on 13 series (`tests/oracles/trend_regime/r_oracle_outputs_headed.csv (tests/unit/test_formulas_trend.py, test_pettitt_is_rs)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="ks_exact"></a>
### Exact two-sided p-value of the two-sample Kolmogorov-Smirnov D, ties respected

`hydrolog.statistics.homogeneity.ks_exact` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
D = \max_x |F_1(x) - F_2(x)|,\quad p = 1 - \frac{\#\{\text{paths with } |i n - j m| < m n D \text{ at the ends of the ties}\}}{\binom{m + n}{m}}
$$

Plain text: `D = max_x |F1(x) - F2(x)| of the empirical distribution functions; p = P(D' >= D) over the C(m + n, m) equally likely splits of the pooled values into samples of m and n, ties respected: 1 - (the lattice paths from (0, 0) to (m, n) that keep |i n - j m| < m n D wherever a group of equal values ends) / C(m + n, m)`

**Sources**

- R Core Team. R: A Language and Environment for Statistical Computing, version 4.4.3, package stats, function ks.test, help page ks.test, Details: in the two-sample case an exact p-value is computed if the product of the sample sizes is less than 10000, with or without ties (the algorithm of Schröer and Trenkler 1995); Examples: with ties, D = 3/7, p = 8/33 (open) <https://stat.ethz.ch/R-manual/R-devel/library/stats/html/ks.test.html>
- Schröer, G., Trenkler, D. (1995). Exact and randomization distributions of Kolmogorov-Smirnov tests two or three samples. Computational Statistics & Data Analysis 20(2), 185-202 (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `first` | $x$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the tests rank the values, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1, 1.2, 3.10 and 3.13 (pp. 11-56): the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |
| `second` | $y$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the tests rank the values, so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below 0, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 1.1, 1.2, 3.3 and 3.4, tables 1.1, 1.2, 3.10 and 3.13 (pp. 11-56): the annual maxima of the Bóbr at Bukówka, the Czarna at Polana, the Rypienica at Rypin and the Świślina at Rzepin: annual maxima of 0.81 to 111 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `exact_size` | precondition | m n < 10000, R's bound of its exact test: the paths are counted on the lattice of the m n points | R Core Team. R: A Language and Environment for Statistical Computing, version 4.4.3, package stats, function ks.test, help page ks.test, Details: in the two-sample case an exact p-value is computed if the product of the sample sizes is less than 10000, with or without ties (the algorithm of Schröer and Trenkler 1995); Examples: with ties, D = 3/7, p = 8/33 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `exact_product` | $m n$ | 10000 | - | R Core Team. R: A Language and Environment for Statistical Computing, version 4.4.3, package stats, function ks.test, help page ks.test, Details: in the two-sample case an exact p-value is computed if the product of the sample sizes is less than 10000, with or without ties (the algorithm of Schröer and Trenkler 1995); Examples: with ties, D = 3/7, p = 8/33 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `d` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `p_value` | - | real | (0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- two-sided; D taken only where a group of equal values ends, as the empirical distribution functions are steps there
- homogeneity_tests takes it for samples with ties and m n < 10000; scipy's ks_2samp, exact for a continuous distribution, without ties and beyond (conservative with ties: Helsel et al. 2020, Example 5.1, 0.0524 against 0.0478)
- the samples in any unit: D and p have none

**Assumptions**

- independent values; under homogeneity every split of the pooled values is equally likely

**Validation:** none: the exact null distribution of a test statistic; its sources compare it with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type cases first-nan_element and second-nan_element: a gap is refused
- `many_small_terms`: the paths are counted in Python integers, exact however many (C(198, 99) is about 2e58), and p is one quotient (limit every_split)

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_samples`: inputs times 2^e (`first` e = 1.0, `second` e = 1.0) give outputs times 2^e (none)
- limit `complete_separation`: three values all below four others: D = 1 and p = 2 / C(7, 3)
- limit `every_split`: p equals P(D' >= D) counted over every split of the pooled values in rational arithmetic
- symmetry `swapped_samples`: the samples swapped give the same D and p
- symmetry `negated_samples`: the negated samples give the same D and p

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/trend-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: P(D' >= D) over every split of the pooled values, counted one by one in rational arithmetic (`tests/unit/test_formulas_trend.py (limit every_split)`)
- established: scipy.stats.ks_2samp with method='exact' (SciPy 1.18.1) on samples without ties (`tests/unit/test_formulas_trend.py (test_the_delegated_ks_2samp_is_exact_without_ties)`)
- frozen: R 4.4.3 stats::ks.test, exact, on three pairs of samples with ties (`tests/oracles/trend_regime/r_oracle_outputs_headed.csv (tests/unit/test_formulas_trend.py, test_ks_exact_is_rs)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

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

<a id="parde_coefficients"></a>
### Pardé's coefficients: the mean discharge of each month over the mean annual discharge

`hydrolog.statistics.regime.parde_coefficients` · family `index` · formula_version 1 · status **referenced** · mutation score not measured

$$
K_m = \frac{\bar{Q}_m}{\bar{Q}},\quad \bar{Q}_m = \frac{1}{n_m}\sum_{d \in m} Q_d,\quad \bar{Q} = \frac{1}{N}\sum_{d} Q_d
$$

Plain text: `K_m = Qbar_m / Qbar, Qbar_m the mean of the days with a value of calendar month m over the period, Qbar the mean of all days with a value`

**Sources**

- Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff (open) <http://wiki.baw.de/en/index.php/Parde_coefficient>
- Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 254: Dynowska's (1997) types read from the monthly flow coefficients W (miesięczne współczynniki przepływu); Table 1, p. 260, in % of the mean annual flow (open) <https://repozytorium.amu.edu.pl/server/api/core/bitstreams/2a303457-aae6-4476-a766-985a3a4ac0b6/content>
- Pardé, M. (1933). Fleuves et rivières. Armand Colin, Paris, the monthly coefficient of discharge; not opened (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $Q_d$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s, about five times the mean discharge of the Amazon (about 2.1e5 m3/s), the largest of any river) | unstated | [1.24, 522.0]: IMGW-PIB, public hydrological data: the monthly characteristics of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997 (tests/fixtures/imgw_klodzko/imgw_150160180_mies_1971_2015.csv), the smallest monthly minimum 1.24 m3/s and the largest monthly maximum 522 m3/s of discharge, which bound its daily means |
| `month` | $m_d$ | - | real_array | [1.0, 12.0] | unstated | [1.0, 12.0]: IMGW-PIB, MIES_publiczne_format.txt, the format of the public monthly files, the calendar month of a row, 1 to 12 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one month per day | Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff |
| `whole_months` | physical | each month is a whole number, a calendar month 1 to 12 | Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff |
| `every_month_has_a_value` | precondition | every calendar month has a day with a value: twelve means exist | Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff |
| `positive_mean` | precondition | 0 < Qbar < inf: some day has a positive discharge, and float64 holds the mean and its sum | Bundesanstalt für Wasserbau, BAWiki glossary: Parde coefficient, the quotient of the long-term mean monthly discharge and the long-term mean annual runoff |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `monthly_mean` | m3/s | real_array | [0.0, inf) | 4 ulp of the bound |
| `annual_mean` | m3/s | real | (0.0, inf) | 4 ulp of the bound |
| `parde` | - | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- Qbar_m the mean of the days with a value of calendar month m over the whole period (the month's days of every year together), Qbar the mean of all days with a value, as IMGW-PIB's monthly and annual means of a year: the twelve coefficients weighted by the days of their months average one and sum to 12 only when every month has as many days (a gapless year: about 11.96 for a strong spring flood); the mean of the twelve monthly means would make them sum to 12
- a day without a value (NaN) counts in neither mean; with gaps gathered in some months Qbar leans towards the better observed ones
- the input months are calendar months (January = 1), the outputs run from November to October, the months of the hydrological year
- discharge in m3/s or any unit (the coefficients have none); Wrzesiński's tables print them in % of the mean annual flow

**Assumptions**

- the period's days represent its months: a period of a few years describes those years, not the climate (the regime of Polish rivers is read from 30 to 40 years, Wrzesiński 2017)

**Validation:** none: Pardé's coefficients describe the mean annual cycle of discharge; their sources compare them with no observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: Qbar -> 0 divides every coefficient: the precondition positive_mean refuses a series without a positive day and a mean that underflows (test_a_tiny_or_vanishing_mean)
- `gap_propagation`: type case values-nan_element and test_gaps_are_left_out_of_both_means: a NaN day is left out, never propagated
- `many_small_terms`: test_a_century_of_days_keeps_the_exact_means: 36,525 days of math.fsum against exact fractions

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing
- scaling `discharge_in_another_unit`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`monthly_mean` e = 1.0, `annual_mean` e = 1.0)
- limit `constant_discharge`: a constant discharge gives every coefficient one
- limit `exact_rational`: the means and coefficients of the float inputs in exact rational arithmetic
- conservation `day_weighted_mean_of_one`: the coefficients weighted by the days with a value of their months average one, sum(n_m K_m) = N; they sum to twelve only when every month has as many days

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/regime-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the monthly and annual means and the coefficients of the float inputs in exact rational arithmetic (fractions) (`tests/unit/test_formulas_regime.py (limit exact_rational, trap many_small_terms)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="spring_share"></a>
### The March-April share of the annual volume of the mean monthly flows

`hydrolog.statistics.regime.spring_share` · family `index` · formula_version 1 · status **oracle only** · mutation score not measured

$$
s = \frac{V_{III} + V_{IV}}{\sum_{m} V_m},\quad V_m = \bar{Q}_m\,d_m
$$

Plain text: `s = (V_III + V_IV) / sum(V_m) with V_m = Qbar_m * d_m, d_m the days of month m, February 28.25`

**Sources**

- Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: spring_share, the March-April share of the annual volume, the monthly means times the days of the month (open)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `monthly_mean` | $\bar{Q}_m$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s, about five times the mean discharge of the Amazon (about 2.1e5 m3/s), the largest of any river) | unstated | [2.67, 58.9]: IMGW-PIB, public hydrological data: the monthly characteristics of station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997 (tests/fixtures/imgw_klodzko/imgw_150160180_mies_1971_2015.csv), the monthly means of discharge, 2.67 to 58.9 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `positive_volume` | precondition | 0 < sum(V_m) < inf: some month has a positive mean, and float64 holds the volumes | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: spring_share, the March-April share of the annual volume, the monthly means times the days of the month |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `february_days` | $d_{II}$ | 113/4 | day | Hydrolog, ADR-0031 (2026), restated in ADR-0063, February of the mean year of 1901-2099, in which every fourth year is a leap year: 28 + 1/4 days, so the twelve months make 365.25 days; the other months have their days of a common year |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `spring_share` | - | real | [0.0, 1.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the volumes are the long-term monthly means times the days of the month, February 28.25 days (the mean year of 365.25 days), not the days of the period's years
- the inputs run from November to October, as the outputs of parde_coefficients; March and April are the fifth and sixth
- the volumes in m3/s times days, a unit that cancels in the share

**Assumptions**

None stated.

**Validation:** none: Hydrolog's descriptive index of the regime (ADR-0031)

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: sum(V_m) -> 0 divides the share: the precondition positive_volume refuses twelve zero means (constraint case positive_volume-violated); a single month of 1e-300 m3/s gives a finite share (limit exact_rational)
- `gap_propagation`: type case monthly_mean-nan_element: a gap is refused, the twelve means need values

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `discharge_in_another_unit`: inputs times 2^e (`monthly_mean` e = 1.0) give outputs times 2^e (none)
- limit `equal_months`: equal monthly means give the 61 days of March and April in the 365.25 of the mean year
- limit `all_in_spring`: flow in March and April only gives a share of one
- limit `exact_rational`: the share of the float inputs in exact rational arithmetic

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the share of the float inputs in exact rational arithmetic (fractions), February 113/4 days (`tests/unit/test_formulas_regime.py (limit exact_rational)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="dynowska_regime_type"></a>
### Dynowska's type of a Polish river regime from Pardé's coefficients

`hydrolog.statistics.regime.dynowska_regime_type` · family `classification` · formula_version 1 · status **referenced** · mutation score not measured

$$
S = \max(K_{III}, K_{IV}),\ L = \max(K_{VI}, K_{VII}, K_{VIII});\ \text{type} = \begin{cases} 5 & L \ge 0.95\,S \\ 4 & L \ge 1.00 \\ 1 & S \le 1.30 \\ 2 & S \le 1.80 \\ 3 & \text{otherwise} \end{cases}
$$

Plain text: `S = max(K_III, K_IV), L = max(K_VI, K_VII, K_VIII); type 5 if L >= 0.95 S, else 4 if L >= 1.00, else 1 if S <= 1.30, 2 if S <= 1.80, 3 otherwise`

**Sources**

- Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 255: Dynowska's (1997) five types: the spring month's mean flow at most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a rule 130-180 % with a summer rise of at least 100 % (4); the summer month's mean flow higher than or nearly equal to the spring month's (5) (open) <https://repozytorium.amu.edu.pl/server/api/core/bitstreams/2a303457-aae6-4476-a766-985a3a4ac0b6/content>
- Wrzesiński, D. (2018). Typologia reżimu odpływu rzek w Polsce w różnych fazach oscylacji północnoatlantyckiej. Badania Fizjograficzne, Seria A, 9 (A69), 249-261. doi:10.14746/bfg.2018.9.19, p. 250: the five types in the words of Wrzesiński (2017, p. 255); Table 1, pp. 253-254: the mean coefficients of each type, 516 gauges, 1971-2010 (open) <https://pressto.amu.edu.pl/index.php/bfg/article/download/24472/22684/50308>
- Perz, A. (2019). Cechy reżimu odpływu rzek Kotliny Kłodzkiej. Badania Fizjograficzne, Seria A, 10 (A70), 65-83. doi:10.14746/bfg.2019.10.6, p. 79: Dynowska's criteria, 130-180 % and at least 100 % of the mean annual flow, the spring month March or April (marzec-kwiecień) (open) <https://pressto.amu.edu.pl/index.php/bfg/article/download/23873/22299/>
- Dynowska, I. (1997). Reżim odpływu rzecznego. In: Atlas Rzeczypospolitej Polskiej. Główny Geodeta Kraju, Warszawa, the five types of the river regime; not opened: as Wrzesiński (2017, 2018) and Perz (2019) quote them (author-provided)
- Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: where the sources name no month and no number, the spring month is the larger of March and April, the summer month the largest of June to August and 'nearly equal' at least 0.95 of the spring coefficient (the mockup's REGIME_RULE) (open)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `parde` | $K_m$ | - | real_array | [0.0, inf), test bound high 30.0 (ten times the largest monthly coefficient of Polish rivers in Wrzesiński's (2017) Table 1, 2.819 (March, type 3), rounded up; a coefficient grows without a bound only through gaps) | unstated | [0.224, 2.819]: Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, Table 1, p. 260: the smallest coefficient 22.4 % (February, type 5) and the largest 281.9 % (March, type 3) of 516 gauges, 1971-2010 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `weakly_nival` | $S_1$ | 13/10 | - | Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 255: Dynowska's (1997) five types: the spring month's mean flow at most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a rule 130-180 % with a summer rise of at least 100 % (4); the summer month's mean flow higher than or nearly equal to the spring month's (5) |
| `moderately_nival` | $S_2$ | 9/5 | - | Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 255: Dynowska's (1997) five types: the spring month's mean flow at most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a rule 130-180 % with a summer rise of at least 100 % (4); the summer month's mean flow higher than or nearly equal to the spring month's (5) |
| `summer_rise` | $L_1$ | 1 | - | Wrzesiński, D. (2017). Typologia reżimu odpływu rzek w Polsce w podejściu nadzorowanym i nienadzorowanym. Badania Fizjograficzne, Seria A, R. VIII (A68), 253-264. doi:10.14746/bfg.2017.8.19, p. 255: Dynowska's (1997) five types: the spring month's mean flow at most 130 % of the mean annual flow (1), 130-180 % (2), above 180 % (3); as a rule 130-180 % with a summer rise of at least 100 % (4); the summer month's mean flow higher than or nearly equal to the spring month's (5) |
| `nearly_equal` | $r$ | 19/20 | - | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 1: where the sources name no month and no number, the spring month is the larger of March and April, the summer month the largest of June to August and 'nearly equal' at least 0.95 of the spring coefficient (the mockup's REGIME_RULE) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `code` | - | integer | [1.0, 5.0] | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the coefficients are Pardé's of the months November to October, as 1.30 for 130 % of the mean annual flow
- the spring month is the larger of March and April (Perz 2019, p. 79), the summer month the largest of June to August (Hydrolog's reading); of equal coefficients the earlier month
- the types are tested in the order 5, 4, then 1 to 3: 'higher than or nearly equal' reads as at least 0.95 of the spring coefficient (Hydrolog's reading, no source gives a number); the sources' 'as a rule 130-180 %' of types 4 and 5 is not tested
- inclusive limits as the sources word them: 'at most 130 %' is type 1, 'above 180 %' type 3, so 180 % is type 2, 'at least 100 %' type 4; the limits are compared as the floats 1.3, 1.8 and 1.0, and summer with the float 0.95 times spring, which keeps every printed three-decimal tie inside its class

**Assumptions**

- the coefficients describe a long period, 30 to 40 years in the sources; the type of a few years or of coefficients near a limit is not robust: Kłodzko's June of 1971-2015 lies 0.05 % above 100 % (Perz's case)
- Wrzesiński's two classifications of the same 516 gauges of 1971-2010 count 24 (2017) and 33 (2018) pluvio-nival rivers: the reading of 'nearly equal' is not settled in the sources either

**Validation:** none: a typology; Wrzesiński (2017, 2018) classified 516 gauges of 1971-2010 and Perz (2019) the rivers of the Kłodzko basin by it, without a measure of agreement

**Notices:** none

**Numerical traps (CMP-6.6)**

- `class_limit`: limit class_limits: 1.30, 1.80, 1.00 and 0.95 of spring, each exactly and just beyond (math.nextafter, or the next printed thousandth)
- `gap_propagation`: type case parde-nan_element: a gap is refused, the twelve coefficients need values

**Properties (CMP-6.5)**

- units: unit_specific
- limit `class_limits`: a coefficient exactly at a limit of a class and just beyond it gives the class of the criteria's inclusive limit and the next one
- limit `decision_table`: the type of three-decimal coefficients is that of the criteria applied to their printed decimals in exact fractions
- symmetry `months_that_do_not_decide`: the coefficients of the months other than March, April and June to August leave the type as it is

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/regime-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the criteria applied to the printed decimals of the coefficients in exact fractions, 'nearly equal' as 20 L >= 19 S (`tests/unit/test_formulas_regime.py (limit decision_table)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="circular_mean"></a>
### Mean direction and concentration of times on the circles of their years (Bayliss and Jones)

`hydrolog.statistics.seasonality.circular_mean` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
\theta_i = \frac{2\pi t_i}{L_i},\quad \bar{x} = \frac{1}{n}\sum_i \cos\theta_i,\quad \bar{y} = \frac{1}{n}\sum_i \sin\theta_i,\quad f = \frac{\operatorname{atan2}(\bar{y}, \bar{x}) \bmod 2\pi}{2\pi},\quad r = \sqrt{\bar{x}^2 + \bar{y}^2}
$$

Plain text: `theta_i = 2 pi t_i / L_i; xbar = sum(cos theta_i) / n, ybar = sum(sin theta_i) / n; f = (atan2(ybar, xbar) mod 2 pi) / (2 pi); r = sqrt(xbar^2 + ybar^2)`

**Sources**

- Bayliss, A.C. and Jones, R.C. (1992). The peaks-over-threshold database at the Institute of Hydrology. Report to MAFF, Institute of Hydrology, Wallingford, March 1992 (published as IH Report No. 121, 1993), section 3.2, pp. 18-19: theta_i = day 2 pi / LENYR - ADJUST with ADJUST = (1/2)(2 pi / 365) for the middle of the day, LENYR 365 or 366; xbar, ybar the means of cos and sin; tan(thetabar) = ybar / xbar with pi or 2 pi added by their signs; MPD = thetabar 365 / (2 pi) + 0.5; section 3.3, p. 21: r = sqrt(xbar^2 + ybar^2), MPD less meaningful when r is close to zero (open) <https://nora.nerc.ac.uk/id/eprint/14407/>
- Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1, pp. 177-179: theta = (day no. - 0.5) 2 pi / LENYR, LENYR 365 or 366, the 0.5 for the middle of the day; XFLOOD and YFLOOD the means of cos theta and sin theta; thetabar by their quadrant, r their length; when r is small the direction is less meaningful (open) <https://www.ceh.ac.uk/sites/default/files/2021-11/Flood-Estimation-Handbook-3-Statistical-Procedures-For-Flood-Frequency-Estimation_Alice-Robson_Duncan-Reed.pdf>
- Hall, J. and Blöschl, G. (2018). Spatial patterns and characteristics of flood seasonality in Europe. Hydrology and Earth System Sciences 22, 3883-3901, eqs. 1-5: theta_i = D_i 2 pi / m_i (D_i = 1 on 1 January, m_i 365 or 366); the mean date by the quadrant rules times m / (2 pi), m the mean number of days per year, undefined for xbar = ybar = 0; R = sqrt(xbar^2 + ybar^2) (open) <https://hess.copernicus.org/articles/22/3883/2018/hess-22-3883-2018.pdf>
- Burn, D.H. (1997). Catchment similarity for regional flood frequency analysis using seasonality measures. Journal of Hydrology 202, 212-230, the seasonality measures of flood dates; not opened (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `elapsed_days` | $t_i$ | day | real_array | [0.0, inf), test bound high 1000000000.0 (a year in seconds is about 3.2e7: the bound leaves room for times in any unit down to the second) | unstated | [2.5, 336.5]: IMGW-PIB, public hydrological data: the half-year characteristics of discharge at station 150160180 Kłodzko on the Nysa Kłodzka, hydrological years 1971-2015 but 1997, the dates of the 44 annual maxima, the larger of the half-year maxima: days 3 to 337 of their calendar years |
| `year_days` | $L_i$ | day | real_array | (0.0, inf), test bound high 1000000000.0 (a year in seconds is about 3.2e7: the bound leaves room for times in any unit down to the second) | unstated | [365.0, 366.0]: Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1: LENYR, 365 or 366 days |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one year length per time | Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1, pp. 177-179: theta = (day no. - 0.5) 2 pi / LENYR, LENYR 365 or 366, the 0.5 for the middle of the day; XFLOOD and YFLOOD the means of cos theta and sin theta; thetabar by their quadrant, r their length; when r is small the direction is less meaningful |
| `within_its_year` | physical | 0 <= t_i < L_i: each time lies in its year | Robson, A. and Reed, D. (1999). Flood Estimation Handbook, Volume 3: Statistical procedures for flood frequency estimation. Institute of Hydrology, Wallingford, Additional Note 16.1, pp. 177-179: theta = (day no. - 0.5) 2 pi / LENYR, LENYR 365 or 366, the 0.5 for the middle of the day; XFLOOD and YFLOOD the means of cos theta and sin theta; thetabar by their quadrant, r their length; when r is small the direction is less meaningful |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `mean_fraction` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `concentration` | - | real | [0.0, 1.0] | 1e-13 |

**Conventions (CMP-2.3)**

- the times and the lengths of their years in one unit of time, days for dates; the angle 2 pi t / L of a time t from the start of its year of L
- for dates t is the day of the year minus a half, the middle of the day, and L 365 or 366 (Bayliss and Jones's ADJUST, FEH's day no. - 0.5); Hall and Blöschl (2018) take the day itself, D 2 pi / m_i
- the mean direction atan2(ybar, xbar) taken into [0, 2 pi): Bayliss and Jones and the FEH add pi or 2 pi to arctan(ybar / xbar) by the signs, the same angle; at xbar = ybar = 0 the direction is undefined (Hall and Blöschl) and the formula gives 0, as scipy.stats.circmean does
- near r = 0 the direction is ill-conditioned: a rounding moves it; read the mean with r (Bayliss and Jones, section 3.3; the FEH)

**Assumptions**

- the times are the dates of independent events, one annual extreme per year; Hall and Blöschl keep the stations where a Rayleigh test rejects uniform dates, which Hydrolog does not compute

**Validation:** none: a description of the timing of floods; Bayliss and Jones (1992) and the FEH map it for British rivers, Hall and Blöschl (2018) for Europe

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: atan2 at xbar = ybar = 0 has no direction: limit opposite_times and test_no_direction_gives_the_start_of_the_year
- `gap_propagation`: type cases elapsed_days-nan_element and year_days-nan_element: a gap is refused
- `many_small_terms`: test_many_dates_keep_their_sums: 100,000 dates against math.fsum of the cosines and sines

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `time_in_another_unit`: inputs times 2^e (`elapsed_days` e = 1.0, `year_days` e = 1.0) give outputs times 2^e (none)
- limit `one_time`: a single time is its own mean, with r = 1
- limit `opposite_times`: two times half a year apart have no direction: r = 0
- limit `quadrant_rules`: the direction and length equal Bayliss and Jones's arctan with the quadrant rules and their r, of sums by math.fsum
- symmetry `reversed_order`: the times in reverse order give the same concentration

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: Bayliss and Jones's (1992) and the FEH's arctan(ybar / xbar) with pi or 2 pi added by the signs, and r, of sums by math.fsum (`tests/unit/test_formulas_regime.py (limit quadrant_rules)`)
- established: scipy.stats.circmean of the angles (SciPy 1.18) (`tests/unit/test_formulas_regime.py (test_the_mean_direction_is_scipys)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="harmonic_fit"></a>
### Least squares fit of the mean and the harmonics of the annual cycle

`hydrolog.statistics.harmonics.harmonic_fit` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
x(t) = A_0 + \sum_{k=1}^{K}\left(a_k \cos\frac{2\pi k t}{P} + b_k \sin\frac{2\pi k t}{P}\right),\quad C_k = \sqrt{a_k^2 + b_k^2},\quad d_k = \frac{(\operatorname{atan2}(b_k, a_k) \bmod 2\pi)\,P}{2\pi k} + 1
$$

Plain text: `x(t) = A0 + sum_k (a_k cos(2 pi k t / P) + b_k sin(2 pi k t / P)), k = 1 ... K, by least squares with t = day - 1; C_k = sqrt(a_k^2 + b_k^2); phase day = (atan2(b_k, a_k) mod 2 pi) P / (2 pi k) + 1; share_k = R2(1..k) - R2(1..k-1) of the nested fits`

**Sources**

- Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd ed. Academic Press, Oxford, section 9.4: the harmonic functions of a periodic series, their amplitude, phase and share of the variance, fitted by regression; not opened (author-provided)
- Feichtinger, H.G., Gröchenig, K. and Strohmer, T. (1995). Efficient numerical methods in non-uniform sampling theory. Numerische Mathematik 69, 423-440, section 4, Propositions 1 and 2, pp. 429-430: a trigonometric polynomial of degree M on a period of 1 sampled with a largest gap delta < 1/(2M) (on the circle) is a stable sampling set, its condition number at most ((1 + 2 delta M) / (1 - 2 delta M))^2; for larger gaps no estimate is known (after Gröchenig 1992, Math. Comp. 59, 181-194) (open) <http://www.math.ucdavis.edu/~strohmer/papers/1995/fgs0195.ps.gz>
- Draper, N.R. and Smith, H. (1998). Applied Regression Analysis, 3rd ed. Wiley, New York, section 6.1: the extra sum of squares of terms added to a fitted model, which never increases the residual sum of squares; not opened (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `day_of_year` | $d$ | day | real_array | [1.0, 366.0] | unstated | [1.0, 366.0]: IMGW-PIB, hydrologia_info_ogolne.txt of the public hydrological data, the hydrological year from 1 November to 31 October: days 1 to 365, or 366 when it ends in a leap year |
| `values` | $x$ | degC | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (a million in the series' unit: a thousand times the largest water and air temperatures and Polish discharges, and above any river stage in cm) | unstated | [-22.2, 29.3]: IMGW-PIB, synoptic station Warszawa-Okęcie (352200375), daily data 1991-2020 (tests/fixtures/warszawa_okecie_1991_2020.csv.gz), the daily mean air temperature, -22.2 to 29.3 degC |
| `n_harmonics` | $K$ | - | integer | [1.0, 4.0] | unstated | [1.0, 4.0]: Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: harmonics 1 to 4 (default 2: the annual and the half-year one), as the option of stats harmonics |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one day per value | Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd ed. Academic Press, Oxford, section 9.4: the harmonic functions of a periodic series, their amplitude, phase and share of the variance, fitted by regression; not opened |
| `enough_values` | precondition | at least 4 K + 2 values: twice the 2 K + 1 coefficients (Hydrolog's rule) | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: too_few_values |
| `year_covered` | precondition | the longest gap between days with a value, on the circle of the year, is shorter than P / (2 K): the harmonics are resolved | Feichtinger, H.G., Gröchenig, K. and Strohmer, T. (1995). Efficient numerical methods in non-uniform sampling theory. Numerische Mathematik 69, 423-440, section 4, Propositions 1 and 2, pp. 429-430: a trigonometric polynomial of degree M on a period of 1 sampled with a largest gap delta < 1/(2M) (on the circle) is a stable sampling set, its condition number at most ((1 + 2 delta M) / (1 - 2 delta M))^2; for larger gaps no estimate is known (after Gröchenig 1992, Math. Comp. 59, 181-194) |
| `values_not_all_equal` | precondition | 0 < sum((x - mean)^2) < inf: the values are not all equal and float64 holds their variance, so R2 and the phases exist | Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd ed. Academic Press, Oxford, section 9.4: the harmonic functions of a periodic series, their amplitude, phase and share of the variance, fitted by regression; not opened |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `period_days` | $P$ | 1461/4 | day | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: the period P = 365.25 d, the mean year of 1901-2099, in which every fourth year is a leap year (the Julian year) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `mean` | degC | real | (-inf, inf) | 4 ulp of the bound |
| `amplitudes` | degC | real_array | [0.0, inf) | 4 ulp of the bound |
| `phase_days` | day | real_array | [1.0, 366.25] | 4 ulp of the bound |
| `explained_variances` | - | real_array | [0.0, 1.0] | 1e-12 |
| `r_squared` | - | real | [0.0, 1.0] | 1e-12 |

**Conventions (CMP-2.3)**

- t is the day of the hydrological year minus one (1 November = 0), P = 365.25 days: a leap year's 31 October is t = 365, so t jumps by 1.25 days at the turn of the year
- the phase day is the day of the hydrological year whose value the harmonic peaks at: a day's value sits at t = day - 1 and the phase day is t + 1
- a harmonic's share of the variance is the increase of R2 when it joins the least squares fit of the harmonics before it (nested fits, the extra sum of squares of Draper and Smith); for a whole number of years of equally spaced days the harmonics are orthogonal and the share is Wilks's (n/2) C_k^2 / ((n - 1) s^2); Hydrolog 0.8 cut the coefficients of the whole fit instead, which gave negative shares on years with gaps
- R2 = 1 - SSR / SST with SST the sum of squared deviations from the mean of the values
- the values in any unit (degC in the documents): the mean and the amplitudes come in that unit

**Assumptions**

- the annual cycle is periodic with the mean year; a trend or a change of regime over the period is spread over the harmonics
- a harmonic of no amplitude has no phase: its phase day is then noise of the rounding, read it only with its amplitude

**Validation:** none: a description of the mean annual cycle; Wilks (2011) gives no measure of its agreement with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: atan2 of a harmonic without amplitude: the precondition values_not_all_equal refuses a constant series (test_a_constant_series_is_refused); a harmonic missing from the signal keeps a finite phase in range (test_a_missing_harmonic_has_a_finite_phase)
- `unbounded_iteration`: the least squares are LAPACK's divide and conquer singular value decomposition (numpy.linalg.lstsq, delegated), bounded by its own count; the precondition year_covered keeps the design well conditioned (test_a_season_of_values_is_refused)
- `gap_propagation`: a NaN day is left out of the fit: type case values-nan_element and test_gaps_are_left_out_of_the_fit
- `many_small_terms`: test_thirty_years_of_temperature_match_the_normal_equations: 10,958 days of Warszawa-Okęcie
- `moment_cancellation`: the fit runs on the deviations from the mean and SST is taken from them, not as E[x^2] - E[x]^2: test_a_large_offset_keeps_the_amplitudes, a signal on top of 1e6, and the pinned example of test_properties_of_annual_cycles, a cycle of 1e-14 on 2.0

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `values_in_another_unit`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`mean` e = 1.0, `amplitudes` e = 1.0)
- limit `two_harmonics`: an exact signal of two harmonics is recovered: mean 10, amplitudes 5 and 2, days 101 and 31, R2 = 1
- limit `normal_equations`: the mean and the amplitudes equal those of the normal equations of the same design solved in exact fractions
- conservation `shares_add_up_to_r_squared`: the shares of the harmonics add up to R2 of the whole fit

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: exact signals of one or two harmonics recovered: their mean, amplitudes, phase days and R2 = 1 (`tests/unit/test_formulas_regime.py (limit two_harmonics)`)
- algorithm: the normal equations of the same design, summed by math.fsum and solved in exact fractions (`tests/unit/test_formulas_regime.py (limit normal_equations, trap many_small_terms)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="sample_standard_deviation"></a>
### Standard deviation of a sample, with the divisor n - 1

`hydrolog.statistics.characteristic.sample_standard_deviation` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}{n - 1}},\quad \bar{x} = \frac{1}{n}\sum_i x_i
$$

Plain text: `s = sqrt(sum((x - mean)**2) / (n - 1)) with mean = sum(x) / n`

**Sources**

- NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.6, Measures of Scale: the standard deviation s = sqrt(sum((Y - mean)**2) / (N - 1)) (open) <https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm>
- NIST Statistical Reference Datasets, Univariate Summary Statistics: NumAcc1 to NumAcc4 (Simon and Lesage 1989), certified values, sample standard deviation (denom. = n-1), exact (open) <https://www.itl.nist.gov/div898/strd/univ/homepage.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [4.93, 96.0]: IMGW-PIB, public hydrological data: codz_2010_01..12.csv, station 150160180 Kłodzko (Nysa Kłodzka), the daily discharges of the hydrological year 2010, 4.93 to 96.0 m3/s (tests/oracles/characteristic/imgw_150160180_codz_2010.csv) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 2 | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.6: the divisor N - 1 needs two values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `std` | m3/s | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the divisor n - 1 (NIST sect. 1.3.5.6; numpy.std with ddof=1)
- the sample in any unit; the standard deviation in its unit
- the deviations from the mean, centred twice, on the sample divided by a power of two; never the sums of powers E[x**2] - E[x]**2

**Assumptions**

None stated.

**Validation:** none: the definition of a sample statistic

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: limit equal_values: the square root at a variance of 0 is exactly 0
- `gap_propagation`: type case values-nan_element: a gap is refused
- `many_small_terms`: reference cases nist_strd_numacc2 to nist_strd_numacc4: 1001 values against the certified s
- `moment_cancellation`: reference case nist_strd_numacc4: a mean of 1e7 with s = 0.1; limit exact_rational: a mean of 1e9 with a spread of 0.03

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`std` e = 1.0)
- limit `exact_rational`: the standard deviation of the definition in exact rational arithmetic
- limit `equal_values`: equal values have no spread
- symmetry `mirror`: the negated sample has the same standard deviation

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/characteristic-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the variance in exact rational arithmetic (fractions) (`tests/unit/test_formulas_characteristic.py (limit exact_rational)`)
- established: numpy.std with ddof=1 (`tests/unit/test_formulas_characteristic.py (test_the_estimators_are_numpys_and_scipys)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="coefficient_of_variation"></a>
### Coefficient of variation of a sample of a quantity with a true zero

`hydrolog.statistics.characteristic.coefficient_of_variation` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
C_v = \frac{s}{\bar{x}},\quad s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}{n - 1}},\quad \bar{x} = \frac{1}{n}\sum_i x_i
$$

Plain text: `Cv = s / mean with s = sqrt(sum((x - mean)**2) / (n - 1)) and mean = sum(x) / n`

**Sources**

- NIST, Dataplot Reference Manual, vol. 2, Let Subcommands: COEFFICIENT OF VARIATION, cv = s / mean; 'should typically only be used for data measured on a ratio scale'; 'if the mean value is near zero, the coefficient of variation is sensitive to small changes in the mean' (open) <https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/coefvari.htm>
- NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.6, Measures of Scale: the standard deviation s = sqrt(sum((Y - mean)**2) / (N - 1)) (open) <https://www.itl.nist.gov/div898/handbook/eda/section3/eda356.htm>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river; the formula is homogeneous (its scaling), so the bound tests its arithmetic) | unstated | [4.93, 96.0]: IMGW-PIB, public hydrological data: codz_2010_01..12.csv, station 150160180 Kłodzko (Nysa Kłodzka), the daily discharges of the hydrological year 2010, 4.93 to 96.0 m3/s (tests/oracles/characteristic/imgw_150160180_codz_2010.csv) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 2 | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.6: the divisor N - 1 of s needs two values |
| `positive_mean` | precondition | max(x) > 0, so that mean > 0 | NIST, Dataplot Reference Manual, vol. 2, Let Subcommands: COEFFICIENT OF VARIATION, cv = s / mean; 'should typically only be used for data measured on a ratio scale'; 'if the mean value is near zero, the coefficient of variation is sensitive to small changes in the mean' |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `cv` | - | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- a ratio scale: values not below zero, of a quantity with a true zero such as discharge (Dataplot); the coefficient of a stage above an arbitrary gauge zero or of a temperature in degrees Celsius changes with the datum and is not defined here for values below zero
- the divisor n - 1 of the standard deviation; the coefficient as a ratio
- the deviations from the mean, centred twice, on the sample divided by a power of two

**Assumptions**

None stated.

**Validation:** none: the definition of a sample statistic

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case positive_mean-violated: the mean 0 of zeros is refused before the division
- `gap_propagation`: type case values-nan_element: a gap is refused
- `moment_cancellation`: limit exact_rational: a mean of 1e9 with a spread of 0.03

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: the coefficient of the definition in exact rational arithmetic
- limit `one_positive_value`: one positive value among n - 1 zeros has the largest coefficient of n values not below zero, sqrt(n)
- limit `equal_values`: equal positive values have no relative spread

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the square of the coefficient in exact rational arithmetic (fractions) (`tests/unit/test_formulas_characteristic.py (limit exact_rational)`)
- established: scipy.stats.variation with ddof=1 (`tests/unit/test_formulas_characteristic.py (test_the_estimators_are_numpys_and_scipys)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fisher_pearson_skewness"></a>
### Fisher-Pearson coefficient of skewness g1 of a sample

`hydrolog.statistics.characteristic.fisher_pearson_skewness` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
g_1 = \frac{m_3}{m_2^{3/2}},\quad m_k = \frac{1}{n}\sum_i (x_i - \bar{x})^k
$$

Plain text: `g1 = m3 / m2**1.5 with m_k = sum((x - mean)**k) / n`

**Sources**

- NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.11, Measures of Skewness and Kurtosis: the Fisher-Pearson coefficient of skewness g1 = sum((Y - mean)**3) / N / s**3, s with the divisor N (open) <https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.skew with bias=True, its default: the Fisher-Pearson coefficient g1 = m3 / m2**1.5 (open) <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [4.93, 96.0]: IMGW-PIB, public hydrological data: codz_2010_01..12.csv, station 150160180 Kłodzko (Nysa Kłodzka), the daily discharges of the hydrological year 2010, 4.93 to 96.0 m3/s (tests/oracles/characteristic/imgw_150160180_codz_2010.csv) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 2 | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.11: a sample of one value has no s |
| `values_not_all_equal` | precondition | min(x) < max(x) | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.11: g1 divides by s**3, 0 for equal values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `skewness` | - | real | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the Fisher-Pearson coefficient g1 of NIST sect. 1.3.5.11, the moments with the divisor n (scipy.stats.skew with bias=True), not the adjusted G1 = sqrt(n (n - 1)) / (n - 2) g1 of flood frequency analysis (Bulletin 17B)
- the sample in any unit; the skewness without one
- the deviations from the mean, centred twice, on the sample divided by a power of two

**Assumptions**

None stated.

**Validation:** none: the definition of a sample statistic

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case values_not_all_equal-violated: m2 = 0 of equal values is refused before the division by m2**1.5
- `gap_propagation`: type case values-nan_element: a gap is refused
- `moment_cancellation`: limit exact_rational: a mean of 1e9 with a spread of 0.03

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (none)
- limit `exact_rational`: the skewness of the definition in exact rational arithmetic
- limit `symmetric_sample`: a sample symmetric about its mean has no skewness
- limit `one_positive_value`: one value apart from n - 1 equal ones has the largest skewness of n values, (n - 2) / sqrt(n - 1)
- symmetry `mirror`: the negated sample has the negated skewness

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the skewness in exact rational arithmetic (fractions) (`tests/unit/test_formulas_characteristic.py (limit exact_rational)`)
- established: scipy.stats.skew with bias=True (`tests/unit/test_formulas_characteristic.py (test_the_estimators_are_numpys_and_scipys)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="mean_interval_half_width"></a>
### Half-width of the Student t confidence interval of a mean of yearly means

`hydrolog.statistics.characteristic.mean_interval_half_width` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
h = t_{1 - \alpha/2,\,k - 1}\,\frac{s}{\sqrt{k}},\quad \alpha = 1 - c,\quad s = \sqrt{\frac{\sum_j (m_j - \bar{m})^2}{k - 1}}
$$

Plain text: `h = t(1 - alpha/2, k - 1) s / sqrt(k) with alpha = 1 - c and s = sqrt(sum((m - mean(m))**2) / (k - 1)) of the k yearly means m`

**Sources**

- NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.2, Confidence Limits for the Mean: mean +- t(1 - alpha/2, N - 1) s / sqrt(N); the example of ZARR13.DAT (open) <https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm>
- Student (1908). The probable error of a mean. Biometrika 6(1), 1-25, the distribution of the deviation of a sample's mean in units of its standard deviation (author-provided)
- Hydrolog, ADR-0049: exact small-sample p-values and intervals on independent values, docs/decisions/0049-exact-small-sample-p-values-and-intervals-of-independent-values.md, decision 5: the interval on the means of the month in the separate years (open)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `yearly_means` | $m_j$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [4.93, 96.0]: IMGW-PIB, public hydrological data: codz_2010_01..12.csv, station 150160180 Kłodzko (Nysa Kłodzka), the daily discharges of the hydrological year 2010, 4.93 to 96.0 m3/s (tests/oracles/characteristic/imgw_150160180_codz_2010.csv) |
| `confidence_level` | $c$ | - | real | (0.0, 1.0) | unstated | [0.9, 0.95]: Hydrolog, catalog command stats monthly, src/hydrolog/catalog/groups/stats.py: confidence_level 0.95 by default, 0.9 in its example |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 2 | NIST/SEMATECH (2012). e-Handbook of Statistical Methods, National Institute of Standards and Technology, sect. 1.3.5.2: N - 1 degrees of freedom need two values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `half_width` | m3/s | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- two-sided, the upper quantile of the tail (1 - c) / 2 by scipy.stats.t.isf, the tail kept exact up to the largest level below 1
- s with the divisor k - 1, of the yearly means centred twice on their values divided by a power of two
- the interval of the long-term mean of a month is its mean of all values +- h (calculate_monthly_statistics, ADR-0049), not clipped at zero

**Assumptions**

- the yearly means of a month are independent and about normal; its daily values are not independent (ADR-0049)

**Validation:** none: an interval estimate; the coverage holds for independent, about normal yearly means (Student 1908)

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: test_a_level_next_to_one_has_a_finite_half_width: the quantile grows without bound as c nears 1; at the largest float below 1 the tail 1 - c is exact and the half-width finite
- `gap_propagation`: type case yearly_means-nan_element: a gap is refused
- `moment_cancellation`: limit exact_rational: yearly means of 1e9 with a spread of 0.003

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `confidence_level` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`yearly_means` e = 1.0) give outputs times 2^e (`half_width` e = 1.0)
- limit `exact_rational`: three means, two degrees of freedom: the closed-form quantile and the variance in exact rational arithmetic
- limit `closed_forms`: one and four degrees of freedom: the quantiles tan(pi c / 2) and the trigonometric form of Hill (1970)
- limit `equal_means`: equal yearly means give an interval of no width
- symmetry `mirror`: the negated means have the same half-width

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/characteristic-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the closed-form quantile of two degrees of freedom and the variance in exact rational arithmetic (fractions) (`tests/unit/test_formulas_characteristic.py (limit exact_rational)`)
- algorithm: the closed-form quantiles of one and four degrees of freedom against scipy's inversion of the incomplete beta function (`tests/unit/test_formulas_characteristic.py (limit closed_forms)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="rating_curve"></a>
### Discharge at a water level by the power-law rating curve

`hydrolog.hydrometrics.rating_curve.rating_discharge` · family `empirical` · formula_version 1 · status **oracle only** · mutation score not measured

$$
Q = \begin{cases} a\,(H - H_0)^{b} & H > H_0 \\ 0 & H \le H_0 \end{cases}
$$

Plain text: `Q = a * (H - H0)**b for H > H0; Q = 0 for H <= H0`

**Sources**

- WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper (open) <https://library.wmo.int/idurl/4/32726>
- ISO 1100-2:2010. Hydrometry - Measurement of liquid flow in open channels - Part 2: Determination of the stage-discharge relationship, the power-law rating equation and its fit to gaugings (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `water_levels` | $H$ | cm | real_array | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-10.0, 330.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070 |
| `a` | $a$ | m3/s per cm^b | real | [0.0, inf), test bound high 1000000.0 (the discharge at a head of one cm cannot exceed the largest discharge of any river, below a million m3/s) | unstated | [0.003, 0.04]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm |
| `b` | $b$ | - | real | [0.0, inf), test bound high 20.0 (five times the largest exponent of a plausible curve (4, ADR-0041), three times the exponent of the curve of two relations at IMGW-PIB 150170070 (6.6)) | unstated | [1.2, 3.1]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm |
| `h0` | $H_0$ | cm | real | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-30.0, 55.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `finite_discharge` | precondition | a (max(H) - H0)**b < 1.8e308: the discharge at every level is a float64 number | NumPy documentation, numpy.finfo, float64: the largest number 1.7976931348623157e+308 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `discharge_m3s` | m3/s | real_array | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- H and H0 in one unit of the levels, cm as IMGW-PIB gives them or m; a in m3/s per (unit of H)^b, so the same curve with the levels in m has a 100^b times larger and H0 100 times smaller (symmetry levels_in_another_unit); Q in m3/s
- Q = 0 at and below H0, the gauge height of zero flow (WMO's e): no flow over the control, whatever b
- H0 is the stage of zero flow, not the gauge zero (the datum of the staff gauge)

**Assumptions**

- one stage-discharge relation of one control (a section or a channel control) over the levels: no shift, hysteresis or variable backwater

**Validation:** none: WMO-No. 1044 presents the equation as the rating of section and channel controls (sects. 1.3 and 1.5.4 to 1.5.6) and reports no statistic of its agreement with gaugings; a curve's fit to its gaugings is that of spec rating_curve_fit

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: the fractional power of the head at its bound 0: test_the_power_at_the_stage_of_zero_flow_is_finite
- `exp_overflow`: the power of a head with a large b: test_a_power_that_overflows_is_refused (the precondition finite_discharge)

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `water_levels` increasing, `a` increasing, `h0` decreasing
- scaling `discharge`: inputs times 2^e (`a` e = 1.0) give outputs times 2^e (`discharge_m3s` e = 1.0)
- limit `unit_head`: the discharge at a head of one unit is a (WMO's C)
- limit `no_flow_at_or_below_zero_flow`: no discharge at and below H0, also for b = 0
- limit `exact_decimal`: Q equals the curve evaluated at 50 decimal digits
- symmetry `levels_in_another_unit`: levels and H0 in a unit twice as small with a times 2^-b give the same discharges: the curve in cm and in m is one curve

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the curve evaluated with Python's decimal at 50 digits, rounded once (`tests/unit/test_formulas_hydrometrics.py (limit exact_decimal)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="rating_curve_fit"></a>
### Rating curve Q = a (H - H0)^b fitted to stage-discharge pairs by least squares on Q

`hydrolog.hydrometrics.rating_curve.fit_rating_curve` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
(\hat a, \hat b, \hat H_0) = \arg\min_{a \ge 0,\, b \ge 0,\, H_0 < \min H} \sum_{i=1}^{n} \left(Q_i - a\,(H_i - H_0)^{b}\right)^2,\quad R^2 = 1 - \frac{SS_{res}}{SS_{tot}}
$$

Plain text: `(a, b, H0) minimise sum((Q_i - a * (H_i - H0)**b)**2) over a >= 0, b >= 0, H0 < min(H); R2 = 1 - SS_res / SS_tot with SS_tot = sum((Q_i - mean(Q))**2); s = sqrt(sum((r_i - mean(r))**2) / (n - 1)) of the residuals r_i`

**Sources**

- WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper (open) <https://library.wmo.int/idurl/4/32726>
- WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.12.2, p. II.1-20: the equation of the relation may be computed by the method of least squares, which assumes that the relation plots as a straight line on logarithmic paper (open) <https://library.wmo.int/idurl/4/32726>
- ISO 1100-2:2010. Hydrometry - Measurement of liquid flow in open channels - Part 2: Determination of the stage-discharge relationship, the power-law rating equation and its fit to gaugings (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `water_levels` | $H$ | cm | real_array | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-10.0, 330.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070 |
| `discharges_m3s` | $Q$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s, above the largest flood discharge of any river (the Amazon's, a few hundred thousand m3/s)) | unstated | [0.5, 125.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, discharges of 0.5 (the catalog's example) to 122.3 m3/s (station_daily.csv) |
| `h0_initial` | $H_{0,start}$ | cm | real | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-30.0, 60.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the starts of their fits: -23 (the catalog's example of stages below the gauge zero), 40 and 41.2 cm |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `same_length` | physical | one discharge per level | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.1, p. II.1-3: at a minimum the list of discharge measurements should include at least 12 to 15 measurements, all made during the period of analysis |
| `enough_pairs` | precondition | n >= 3: three pairs or more for the three parameters a, b and H0 | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper |
| `levels_not_all_equal` | precondition | min(H) < max(H): levels all equal determine neither b nor H0 | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper |
| `discharges_not_all_equal` | precondition | min(Q) < max(Q): a discharge that does not change with the level fits b = 0 at any H0 | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper |
| `start_below_levels` | precondition | h0_initial < min(H): the search starts inside its bound, H0 below every level | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.4, eq. 1.4, pp. II.1-6 to II.1-7: Q = C (h - e)^beta, h the gauge height, e the gauge height of zero flow for a control of regular shape, or of effective zero flow for a control of irregular shape, C the discharge when the head h - e equals 1, beta the slope of the rating on logarithmic paper |
| `least_squares_minimum` | precondition | the sum of squares has a minimum that the search reaches in 10,000 evaluations, at which the curve is a float64 number at every level | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.12.2, p. II.1-20: the equation of the relation may be computed by the method of least squares, which assumes that the relation plots as a straight line on logarithmic paper |
| `enough_gaugings` | applicability | n >= 12: at least 12 to 15 gaugings of the period of analysis | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.1, p. II.1-3: at a minimum the list of discharge measurements should include at least 12 to 15 measurements, all made during the period of analysis |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `least_gaugings` |  | 12.0 | - | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.1, p. II.1-3: at a minimum the list of discharge measurements should include at least 12 to 15 measurements, all made during the period of analysis |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `a` | m3/s per cm^b | real | [0.0, inf) | 4 ulp of the bound |
| `b` | - | real | [0.0, inf) | 4 ulp of the bound |
| `h0` | cm | real | (-inf, inf) | 4 ulp of the bound |
| `r_squared` | - | real | (-inf, 1.0] | 4 ulp of the bound |
| `std_residuals` | m3/s | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- least squares on Q, the arithmetic residuals of every pair weighted equally; WMO-No. 1044 (sect. 1.12.2) fits the straight line on logarithmic paper, log Q on log(H - H0), which gives another curve (the catalog's six gaugings: b = 1.640 on Q, 1.820 in logarithms)
- bounds a >= 0, b >= 0 and H0 below the lowest level by 2^-30 of the levels' scale (the power of two that brings the largest |H| into [1/2, 1)), about 5e-7 cm for stages of a few metres
- the search: SciPy's curve_fit, the trust region reflective method with ftol, xtol and gtol of 1e-12 and at most 10,000 evaluations, from a = 1, b = 1.5 and H0 = h0_initial, on the levels and discharges divided exactly by the powers of two that bring their largest magnitudes into [1/2, 1); the curve is scaled back, so levels in cm or m and discharges scaled by a power of two give the same curve
- R2 = 1 - SS_res / SS_tot on Q; s the standard deviation of the residuals with n - 1 (numpy.std, ddof 1)
- H, H0 and h0_initial in one unit of the levels (cm or m); a in m3/s per (unit of H)^b; Q in m3/s

**Assumptions**

- the pairs follow one stage-discharge relation of one control over the period (no shift, hysteresis or variable backwater); the check of spec rating_curve_plausibility flags curves that do not
- errors in Q only, independent and of equal variance

**Validation:** none: the least squares give the curve closest to the gaugings on Q; WMO-No. 1044 (sect. 1.12.2) reports no statistic of the agreement of such a fit, and the research found no open worked example with gaugings and fitted parameters (WMO-No. 1044, Rantz 1982, Kennedy 1984)

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: the fractional power of a head at H0's bound below the lowest level: test_a_curve_at_its_bound_is_finite
- `exp_overflow`: the power of the head at the levels' test bounds: test_levels_at_their_test_bounds_fit_or_are_refused
- `unbounded_iteration`: the search's bounded count of 10,000 evaluations: test_a_search_that_does_not_settle_is_refused (precondition least_squares_minimum)
- `gap_propagation`: type cases water_levels-nan_element and discharges_m3s-nan_element: a gap is refused
- `many_small_terms`: test_many_pairs_keep_their_sums: 20,000 pairs against math.fsum
- `moment_cancellation`: test_a_large_mean_discharge_keeps_r_squared: SS_tot of discharges near 1e6 against exact fractions

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `discharges`: inputs times 2^e (`discharges_m3s` e = 1.0) give outputs times 2^e (`a` e = 1.0, `std_residuals` e = 1.0)
- limit `noise_free_power_law`: pairs of an exact power law give back its a, b and H0, with levels in cm and in m
- limit `local_minimum`: no point a step of 1e-4 from the estimate has a smaller sum of squares
- limit `zero_flow_below_the_levels`: H0 lies below every level of the pairs
- symmetry `levels_in_another_unit`: levels and the start in a unit twice as small give the same curve: a times 2^-b, H0 doubled, b, R2 and s unchanged

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- frozen: R 4.4.3 stats::nls(algorithm = 'port') from a = 1, b = 1.5 and H0 = min(H) - max(1, 0.1 range), bounds a, b >= 0, H0 <= min(H) - 1e-6: tests/oracles/rating_curve/r_rating_outputs.csv (`tests/unit/test_formulas_hydrometrics.py (test_the_fit_equals_r_nls_port; the cases of tests/fixtures/formulas/hydrometrics-cases.json)`)
- exact: pairs of the exact power law Q = 0.012 (H - 32)^1.62 give back a, b and H0, with levels in cm and in m (`tests/unit/test_formulas_hydrometrics.py (limit noise_free_power_law; case rating_curve_exact_power_law_and_units)`)
- algorithm: the sum of squares at points a step of 1e-4 from the estimate, by math.fsum (`tests/unit/test_formulas_hydrometrics.py (limit local_minimum)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="rating_curve_plausibility"></a>
### Plausibility of a rating curve as the curve of one stage-discharge relation (Hydrolog's rule of ADR-0041)

`hydrolog.hydrometrics.rating_curve.rating_curve_plausibility` · family `classification` · formula_version 1 · status **unreferenced** · mutation score not measured

$$
b \notin [1, 4] \Rightarrow \text{b\_out\_of\_range},\quad \min H - H_0 > \max H - \min H \Rightarrow \text{h0\_too\_low}
$$

Plain text: `b_out_of_range unless 1 <= b <= 4; h0_too_low if min(H) - H0 > max(H) - min(H)`

**Sources**

- Hydrolog ADR-0041 (2026). Implausible rating curves: flagged, not refused, docs/decisions/0041-implausible-rating-curves-flagged-not-refused.md, decision 1: b from 1 to 4, H0 below the lowest stage by at most the range of the stages; Hydrolog's own rule, published by no source (open)
- WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.3, eq. 1.1, p. II.1-2: beta = 1.5 for a rectangular and 2.5 for a V-shaped section control; sect. 1.5.6, p. II.1-8: logarithmic ratings of section controls in natural channels almost always have a slope of 2 or greater, those of channel controls usually less than 2 (open) <https://library.wmo.int/idurl/4/32726>
- WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.5.6, fig. II.1.5, p. II.1-9: the rating of a real stream with section control throughout, e = 0.6 m, has a slope of about 4.3 below 1.4 m and 2.8 above 1.5 m (open) <https://library.wmo.int/idurl/4/32726>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `water_levels` | $H$ | cm | real_array | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-10.0, 330.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070 |
| `b` | $b$ | - | real | [0.0, inf), test bound high 20.0 (five times the largest exponent of a plausible curve (4, ADR-0041), three times the exponent of the curve of two relations at IMGW-PIB 150170070 (6.6)) | unstated | [1.2, 3.1]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm |
| `h0` | $H_0$ | cm | real | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-30.0, 55.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, the curves fitted to them with levels in cm: a 0.0049 to 0.035, b 1.28 to 3.02 (all the pairs of 150170070), H0 -25.2 to 52.6 cm |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `lowest_exponent` |  | 1.0 | - | Hydrolog ADR-0041 (2026). Implausible rating curves: flagged, not refused, docs/decisions/0041-implausible-rating-curves-flagged-not-refused.md, decision 1: b from 1 to 4, H0 below the lowest stage by at most the range of the stages; Hydrolog's own rule, published by no source |
| `highest_exponent` |  | 4.0 | - | Hydrolog ADR-0041 (2026). Implausible rating curves: flagged, not refused, docs/decisions/0041-implausible-rating-curves-flagged-not-refused.md, decision 1: b from 1 to 4, H0 below the lowest stage by at most the range of the stages; Hydrolog's own rule, published by no source |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `exponent` | - | choice | – | 4 ulp of the bound |
| `zero_flow_stage` | - | choice | – | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- b from 1 to 4, bounds included: section controls 1.5 to 2.5 and 2 or more in natural channels, channel controls usually below 2 (WMO-No. 1044, pp. II.1-2 and II.1-8), compound sections and overbank flow left in; a real section control of slope 4.3 (fig. II.1.5) is flagged
- H0 at most the range of the levels below the lowest level, bound included: Hydrolog's own bound; the levels are those of the pairs given to the fit, before outliers are removed
- a verdict, not a refusal: the curve is still given (ADR-0041)

**Assumptions**

- a curve fitted to the pairs of two relations (a gauge zero moved, a channel changed within the period) has a steep b and an H0 far below every level

**Validation:** none: a heuristic of Hydrolog (ADR-0041), checked against no observations; WMO-No. 1044 shows a real section control whose rating has a slope of about 4.3 below 1.4 m (fig. II.1.5, p. II.1-9), which the rule flags b_out_of_range

**Notices:** `unreferenced_formula`

**Numerical traps (CMP-6.6)**

- `class_limit`: limit class_limits: b = 1, b = 4 and H0 at the range below the lowest level, and the next values beyond them
- `gap_propagation`: type case water_levels-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `levels`: inputs times 2^e (`water_levels` e = 1.0, `h0` e = 1.0) give outputs times 2^e (none)
- limit `class_limits`: b = 1 and b = 4 are plausible, the next floats beyond are not; H0 exactly the range below the lowest level is plausible, a little deeper is not
- limit `two_relations`: the curve of two relations at IMGW-PIB 150170070, 1981-1990 (b = 6.5, H0 = -88 cm under stages of 45 to 161 cm), fails both
- limit `levels_in_metres`: the verdicts of levels in cm and in m are the same

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="rybczynski_zones"></a>
### Rybczyński's zones of low, medium and high background water levels (NTW, STW, WTW)

`hydrolog.hydrometrics.rating_curve.rybczynski_zones` · family `classification` · formula_version 1 · status **unreferenced** · mutation score not measured

$$
H_{NTW} = c_{\arg\max_i f_i},\quad H_{STW} = c_{\min\{i:\, D_i < 50\%\}},\quad D_i = 100 - \sum_{j<i} f_j,\quad f_j = \frac{100\,n_j}{\sum n}
$$

Plain text: `NTW ends at the centre of the most frequent class; STW at the centre of the first class i with D_i < 50 %, D_i = 100 - sum(f_j, j < i), f_j = 100 n_j / sum(n)`

**Sources**

- Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `bin_edges` | $e$ | cm | real_array | (-inf, inf), test bound low -10000.0 and high 10000.0 (100 m above or below a gauge's zero in cm: the stages of the largest rivers in flood range over a few tens of metres, so every stage of a gauge lies within) | unstated | [-10.0, 340.0]: Hydrolog's stage-discharge data: tests/fixtures/rating_curve_pairs.csv, tests/fixtures/station_daily.csv, the catalog's examples of hydrometrics rating-curve and IMGW-PIB 150170070 in ADR-0041, stages of -10 cm (below the gauge zero, the catalog's example) to 329 cm (station_daily.csv); 6 to 161 cm at 150170070 |
| `counts` | $n$ | - | real_array | [0.0, inf), test bound high 1000000.0 (a million levels in a class, the hourly stages of more than a century) | unstated | [0.0, 820.0]: Hydrolog's water level data: tests/fixtures/station_daily.csv and the classes of 5 to 20 cm of the catalog's and the tests' examples, 1,811 daily stages of 45 to 329 cm: classes of 10 cm hold up to 483 levels, of 20 cm up to 815 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `one_count_per_class` | physical | one count per class between two edges | Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) |
| `edges_increasing` | physical | e[i+1] > e[i]: classes of positive width, from the lowest level up | Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) |
| `some_levels` | precondition | sum(n) > 0: the frequencies need levels | Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `duration_limit_pct` |  | 50.0 | % | Rybczyński, M. (1932). Kilka uwag o charakterystyce przepływów. Biuletyn Towarzystwa Geofizyków w Warszawie 4-5; and his lecture notes of 1923, not opened: the names NTW, STW and WTW and the limits of the zones are not confirmed from the source (research of 2026-11-18, trend-regime sect. 3.12) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `ntw_upper` | cm | real | (-inf, inf) | 4 ulp of the bound |
| `stw_upper` | cm | real | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the limits are class centres: NTW ends at the centre of the most frequent class (the first of equal ones), STW at the centre of the first class at whose lower edge the duration (the share of levels at or above it) is below 50 %
- when no class has a duration below 50 %, or STW would not lie above NTW, STW ends at the centre of the class above the most frequent one; when that is the last class, one class width above NTW, beyond the highest edge (WTW then runs backwards)
- the classes and counts of spec water_level_frequency (Tier B), levels in cm or m

**Assumptions**

- the levels of a long series, daily or more often, of one gauge zero

**Validation:** none: Rybczyński's source was not opened

**Notices:** `unreferenced_formula`

**Numerical traps (CMP-6.6)**

- `class_limit`: limit half_duration: a duration of exactly 50 %; limit fallbacks: equal most frequent classes
- `gap_propagation`: type cases bin_edges-nan_element and counts-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `levels`: inputs times 2^e (`bin_edges` e = 1.0) give outputs times 2^e (`ntw_upper` e = 1.0, `stw_upper` e = 1.0)
- scaling `counts`: inputs times 2^e (`counts` e = 1.0) give outputs times 2^e (none)
- limit `worked_example`: the most frequent class and the duration below 50 %
- limit `fallbacks`: STW when no duration falls below 50 % and when the most frequent class is the last; of equal classes, the first
- limit `half_duration`: a duration of exactly 50 % is not below it

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

None.

**Tests by class (CMP §6):** generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
| `trend_decision` | `hydrolog.statistics.stationarity.mann_kendall_test` | trend_detected is p < alpha; trend_direction is increasing for S > 0 and decreasing for S < 0 when a trend is detected, else none; Sen's interval is given from ten values and is null below them or when a rank falls outside the slopes | – | a two-sided test at the caller's alpha, the interval at 1 - alpha; the times must increase strictly (one value a time step) | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, eqs. 16.1 to 16.4, pp. 209-211: S, Var(S) corrected for ties, Z with a continuity correction of one; section 16.4.1 and table A18: the exact probabilities of S below n = 10 |
| `trend_times` | `hydrolog.operations.stats_mann_kendall` | the times of the values: their years (years, year_column) or, without them, the steps 0, 1, 2 … of the series; a missing value is left out and keeps its step | – | Sen's slope per year with years, per step without them | Gilbert, R.O. (1987). Statistical Methods for Environmental Pollution Monitoring. Van Nostrand Reinhold, New York, section 16.5, eqs. 16.8 and 16.9, p. 218: the N' slopes (x_i' - x_i) / (i' - i) of the pairs of data i' > i of different times (several values of one time give no slope among themselves), their median; Example 16.5, p. 219 |
| `homogeneity_split` | `hydrolog.statistics.homogeneity.homogeneity_tests` | the first part is the first n // 2 values, or the values of the years before split_year; the second part the rest | – | split_year and Pettitt's change_point_year name the year of the first value of the second part (ADR-0022) | Hydrolog, ADR-0022 (2026-11-06): homogeneity tests of annual maxima, decisions 2 and 5 |
| `homogeneity_decision` | `hydrolog.statistics.homogeneity.homogeneity_tests` | a test is homogeneous when its p-value is at least alpha; Mann-Whitney's U is scipy's mannwhitneyu, the Kolmogorov-Smirnov p scipy's ks_2samp without ties or with m n >= 10000, else the spec ks_exact | – | two-sided tests at the caller's alpha | Hydrolog, ADR-0022 (2026-11-06): homogeneity tests of annual maxima, decision 6 |
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
| `flow_regime_of_a_daily_series` | `hydrolog.statistics.regime.flow_regime` | The calendar month of each date; Pardé's coefficients, the spring share and Dynowska's type of the series (the specs parde_coefficients, spring_share, dynowska_regime_type), Walsh and Lawler's index of the monthly volumes (the means times the days of the month, February 28.25 days) and the first, last and number of the hydrological years with a value | february_days = 113/4 day (Hydrolog, ADR-0031 (2026), restated in ADR-0063, February of the mean year of 1901-2099, in which every fourth year is a leap year: 28 + 1/4 days, so the twelve months make 365.25 days; the other months have their days of a common year) | months of the Gregorian calendar; the lists from November to October; a day without a value (NaN) is left out; a hydrological year runs from November to October and is named after the year of its end (IMGW-PIB) | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), point 1: the result of stats regime |
| `circular_mean_of_dates` | `hydrolog.statistics.seasonality.circular_mean_date` | The time of each date, its day of the calendar year (1 = 1 January) minus a half, and the length of its year, 365 or 366 days; their circular_mean; the mean day 365.25 f + 0.5 and its MM-DD in the common year 2001 | mean_year_days = 1461/4 day (Hall, J. and Blöschl, G. (2018). Spatial patterns and characteristics of flood seasonality in Europe. Hydrology and Earth System Sciences 22, 3883-3901, eq. 2: m, the mean number of days per year, taken as 365.25, the mean of 1901-2099; Bayliss and Jones (1992, p. 19) take 365) | leap years by the Gregorian rule; the direction back to a day on the mean year of 365.25 days (Hall and Blöschl's m; Bayliss and Jones take 365, up to a quarter of a day earlier at the end of the year); the date of the mean day rounded by Python's round (a half to the even day), a day beyond 365 on 31 December | Bayliss, A.C. and Jones, R.C. (1992). The peaks-over-threshold database at the Institute of Hydrology. Report to MAFF, Institute of Hydrology, Wallingford, March 1992 (published as IH Report No. 121, 1993), section 3.2, pp. 18-19: theta_i = day 2 pi / LENYR - ADJUST with ADJUST = (1/2)(2 pi / 365) for the middle of the day, LENYR 365 or 366; xbar, ybar the means of cos and sin; tan(thetabar) = ybar / xbar with pi or 2 pi added by their signs; MPD = thetabar 365 / (2 pi) + 0.5; section 3.3, p. 21: r = sqrt(xbar^2 + ybar^2), MPD less meaningful when r is close to zero |
| `extremes_of_complete_years` | `hydrolog.statistics.seasonality.daily_extremes` | The maximum or minimum of each complete hydrological year of a daily series, dated by the first day it occurs | – | a year counts only with a value for every day, as IMGW-PIB gives no characteristic for a period with a break; the extremes are of daily values, not of all observations | IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of the public data, the winter half-year 1 November to 30 April, the summer one 1 May to 31 October; the hydrological year named after the year of its end; no characteristic for a period with a break in the observations |
| `extremes_of_half_years` | `hydrolog.statistics.seasonality.half_year_extremes` | IMGW-PIB's annual maximum, the larger of the half-year maxima (the winter one when they are equal), or minimum, the smaller of the minima, with the date of that half-year's extreme | – | a year without both half-years has no extreme; one whose extreme has no date is left out and named | IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of the public data, the winter half-year 1 November to 30 April, the summer one 1 May to 31 October; the hydrological year named after the year of its end; no characteristic for a period with a break in the observations |
| `seasonality_of_extremes` | `hydrolog.statistics.seasonality.extreme_seasonality` | The circular mean date and concentration of the dated annual extremes and their shares in the winter (November to April) and the summer (May to October) half-year | – | IMGW-PIB's half-years by the calendar month of each date | IMGW-PIB, Rocznik Hydrologiczny 2022 and hydrologia_info_ogolne.txt of the public data, the winter half-year 1 November to 30 April, the summer one 1 May to 31 October; the hydrological year named after the year of its end; no characteristic for a period with a break in the observations |
| `annual_cycle_of_a_daily_series` | `hydrolog.statistics.harmonics.annual_cycle` | The day of the hydrological year of each date (1 = 1 November); the harmonic_fit of every day of the period, the mean annual cycle, and of each hydrological year with at least 300 days with a value that meet its preconditions | min_year_values = 300 day (Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: each hydrological year with at least 300 values has a fit of its own) | a hydrological year runs from November to October and is named after the year of its end (IMGW-PIB); a year whose values the fit refuses (all equal, or a gap too long for the harmonics) has no fit of its own | Hydrolog, ADR-0031 (2026): regime, seasonality, harmonics, Sen's slope and baseflow (docs/decisions/), restated in ADR-0063, point 3: the result of stats harmonics |
| `characteristic_first_degree` | `hydrolog.statistics.characteristic.calculate_characteristic_values` | The first degree of each hydrological year and of its half-years from a daily series: the minimum, mean and maximum of the days with a value, each extreme dated by the first day it occurs. | summer_first_month = 5 month (IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7)) | Winter XI-IV, summer V-X, year XI-X. The extremes are those of the daily values, as a rule milder than IMGW-PIB's extremes of all observations (Kłodzko 2010: WQ 96.0 against 145 m3/s); a year with days without a value stays, with the days it has, and is listed in incomplete_years, where IMGW-PIB publishes no characteristic. | IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7) |
| `characteristic_second_degree` | `hydrolog.statistics.characteristic.calculate_characteristic_values` | The second degree of the year and of each half-year: the highest (W), mean (S), median (Z) and lowest (N) over the years of the first-degree maxima, means and minima (WWQ ... NNQ), each of the years that have it. | – | SWQ is the mean of the annual maxima, never of the pooled half-year maxima; the medians (ZWQ, ZSQ, ZNQ) and WSQ, NSQ, WNQ, NWQ follow the pattern of Byczkowski (1996, author-provided); W, S, N of a stage are WWW ... NNW and of water temperature WWT ... NNT. | IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7) |
| `characteristic_from_half_years` | `hydrolog.statistics.characteristic.characteristic_values_from_half_years` | The first degree from IMGW-PIB's published half-year characteristics: the half-years keep their minimum, mean and maximum with dates; the annual maximum is the larger of the half-year maxima and the annual minimum the smaller of the minima, with that half-year's date; the annual mean is the published one. | – | The winter value on a tie; an annual extreme with a half-year missing (a break in observations) is unknown; a year without any value is left out; the second degree as from a daily series. | IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), PLWSKP 13 winter half-year XI-IV, 14 summer half-year V-X, 15 year; PLWSKEX 1 minimum, 2 mean, 3 maximum; a value 99999.999 or NULL is a break in observations |
| `half_year_annual_extremes` | `hydrolog.statistics.characteristic.annual_extremes_from_half_years` | The annual maxima (minima) of IMGW-PIB's half-year characteristics: the larger (smaller) of the winter and the summer value of each year that has both. | – | The winter value on a tie, dated from its half-year; a year with one half-year only is left out and named in incomplete_years. | IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), PLWSKP 13 winter half-year XI-IV, 14 summer half-year V-X, 15 year; PLWSKEX 1 minimum, 2 mean, 3 maximum; a value 99999.999 or NULL is a break in observations |
| `daily_statistics` | `hydrolog.statistics.characteristic.calculate_daily_statistics` | The maximum, mean, median, minimum and number of the values of each day of the hydrological year over the years. | – | Days counted from 1 November (TIER_B hydrological_day_of_year): after 28 February a day pools two adjacent calendar dates of leap and common years (day 121: 29 February and 1 March) and day 366 holds leap years only; every value counts, a NaN makes its day's statistics NaN. | IMGW-PIB (2023). Rocznik Hydrologiczny 2022, pp. 5-8: WQ, SQ, NQ the largest, mean and smallest value of a month, of the half-years Zima XI-IV and Lato V-X and of the year Rok XI-X; WWQ, SWQ, SSQ, SNQ, NNQ of a period; 'Wartości ekstremalne opracowane zostały na podstawie wszystkich dostępnych pomiarów i obserwacji' (p. 7) |
| `monthly_statistics` | `hydrolog.statistics.characteristic.calculate_monthly_statistics` | The maximum, mean, median and minimum of all values of each calendar month; their standard deviation, coefficient of variation and skewness by the specs; the interval of the month's long-term mean, its mean +- the half-width of spec mean_interval_half_width on its yearly means. | – | Calendar months and years; an estimate whose spec refuses the month's values is NaN; the interval is centred on the mean of all values of the month (ADR-0049) and not clipped. | Hydrolog, ADR-0049: exact small-sample p-values and intervals on independent values, docs/decisions/0049-exact-small-sample-p-values-and-intervals-of-independent-values.md, decision 5: the interval on the means of the month in the separate years |
| `hydrological_year` | `hydrolog.statistics._hydrological_year.hydrological_year` | The hydrological year of a date: its calendar year, one more for November and December. | first_month = 11 month (IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016') | IMGW-PIB's year 1 November - 31 October, named after the calendar year in which it ends (2016 = 1.11.2015 - 31.10.2016); ČHMÚ's the same (Hydrologická ročenka České republiky 2010, introduction). | IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' |
| `hydrological_day_of_year` | `hydrolog.statistics._hydrological_year.hydrological_day_of_year` | The day of a date in its hydrological year: the days since 1 November, plus one. | first_month = 11 month (IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016') | 1 November is day 1 and 29 February day 121; from 1 March a leap year's days are one higher than a common year's (1 March is day 122 or 121, 31 October day 366 or 365): a day number names no calendar date. | IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' |
| `days_in_hydrological_year` | `hydrolog.statistics._hydrological_year.days_in_hydrological_year` | The calendar days of a hydrological year: 366 when its name is a leap year, else 365. | – | A year holds 29 February of the calendar year it is named after; leap years of the Gregorian calendar, a multiple of 4 but not of 100 unless of 400 (2000 leap, 2100 common). | IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' |
| `hydrological_year_start` | `hydrolog.statistics._hydrological_year.hydrological_year_start` | The first day of a hydrological year: 1 November of the calendar year before its name. | first_month = 11 month (IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016') | The year named after the calendar year in which it ends. | IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of 2020-06-23), 'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; 'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze letnie - okresowi 1.05.2016-31.10.2016' |
| `daily_calendar` | `hydrolog.statistics._hydrological_year.on_daily_calendar` | Every day from the first to the last date of a series, with its value. | – | A day whose date is absent or whose value is NaN has no value (NaN); no value is filled in. | Hydrolog, ADR-0029: station analyses for Obserwator, docs/decisions/0029-station-analyses-for-obserwator.md: a day whose date is absent or whose value is empty has no value |
| `complete_year_extremes` | `hydrolog.statistics._hydrological_year.annual_extremes` | The maximum or the minimum of each complete hydrological year, one with a value on each of its 365 or 366 days. | – | A year with a day without a value is skipped and reported (its extreme may fall on that day); a date given twice counts once. | IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of 2026-04-29), 'Wartość stanu wody/przepływu/temperatury wody równa 99999.999 albo NULL oznacza przerwy w obserwacjach': no characteristic of a period with a break |
| `water_level_frequency` | `hydrolog.hydrometrics.rating_curve.WaterLevelFrequency.frequency_distribution` | classes of bin_width from the lowest level rounded down to a whole unit up to the first edge above the highest level rounded up; the count of each class, its frequency 100 n_i / n %, the cumulative frequency from the lowest class and the duration D_i = 100 - the cumulative frequency below class i, the share of levels at or above its lower edge | – | classes [lower, upper) of numpy.histogram, the last one closed; the first edge a whole unit of the levels (cm or m), so the classes depend on the unit; duration as the share equalled or exceeded | Searcy, J.K. (1959). Flow-duration curves. Manual of Hydrology: Part 2, Low-flow techniques. U.S. Geological Survey Water-Supply Paper 1542-A, p. 2: the percent of time a value was equalled or exceeded; p. 6: class intervals barely including the extremes of the record |
| `rating_curve_start` | `hydrolog.hydrometrics.rating_curve.RatingCurve.fit` | without h0_initial the search starts at H0 = min(H) - max(1, 0.1 (max(H) - min(H))), below every level whatever their sign | start_fraction = 0.1 - (Hydrolog, docs/COMPUTATION_PATHS.md, sect. 3.8, the H0 starting point) | one unit of the levels at least (1 cm or 1 m), so the start depends on the unit; starts 0.1 to 1 range below the lowest level reached the same least squares in Hydrolog's benchmark of synthetic curves | Hydrolog, docs/COMPUTATION_PATHS.md, sect. 3.8, the H0 starting point (0.8.0); the R oracle of the research starts there too (tests/oracles/rating_curve/r_rating_oracle.R) |
| `rating_curve_outlier_screening` | `hydrolog.hydrometrics.rating_curve.RatingCurve.fit` | with remove_outliers, the pairs whose residual from the first fit exceeds outlier_std standard deviations of the residuals (n - 1) are left out and the curve is fitted again to the rest, once, when at least 3 remain | – | one pass, \|r\| > k s left out and \|r\| = k s kept; the start of the second fit is that of the first; Hydrolog's own rule, while WMO-No. 1044 (sect. 1.12.1) checks a gauging that departs from the curve by more than 5 per cent by a check measurement | WMO (2010). Manual on Stream Gauging, Volume II: Computation of Discharge, WMO-No. 1044, Geneva, sect. 1.12.1, pp. II.1-19 to II.1-20: a measurement that does not check the rating by 5 per cent is repeated |

## Delegated computations (CMP-1.2)

| Computation | Library | Versions | Smoke case | Test |
|---|---|---|---|---|
| nash_shape_root | scipy.optimize.brentq | scipy>=1.10 (1.18.1 locked) | the root N of f(N) = (N-1)^N e^-(N-1) / Gamma(N) = f(2.55) on [1.1, 20] with xtol 1e-6 is 2.55 within 1e-6 (spec lutz) | `tests/unit/test_formulas_lutz.py::test_the_delegated_root_finder_finds_a_known_root` |
| lyne_hollick_recursion | scipy.signal.lfilter | scipy>=1.10 (1.18.1 locked) | lfilter([(1 + a) / 2], [1, -a], diff(Q), zi=[a Q_1]) gives the quickflow q_t = a q_(t-1) + (1 + a)/2 (Q_t - Q_(t-1)) from q_1 = Q_1 of the first pass of Ladson et al. (2013), Table 4 (Bass River, a = 0.98): 155.46 after 96 and 158 (spec lyne_hollick) | `tests/unit/test_formulas_baseflow.py::test_the_delegated_recursion_is_the_first_pass_of_table_4` |
| student_t_quantile | scipy.stats.t.isf | scipy>=1.10 (1.18.1 locked) | the upper quantile of the tail 0.025 with one degree of freedom is tan(0.475 pi) = 12.7062047361747 within 1e-13 relative (spec mean_interval_half_width) | `tests/unit/test_formulas_characteristic.py::test_the_delegated_t_quantile_is_a_known_one` |
| mann_whitney_u | scipy.stats.mannwhitneyu (two-sided, method auto: exact for parts of at most 8 values without ties, else normal with the corrections for ties and continuity) | scipy>=1.10 (1.18.1 locked) | Helsel et al. (2020), Example 5.1: U of the first part 76.5, p = 0.04911 (R's wilcox.test W = 76.5, p = 0.0491099747); the frozen oracle tests/oracles/trend_regime holds R's U and p of three pairs of samples (stats homogeneity) | `tests/unit/test_formulas_trend.py::test_the_delegated_mann_whitney_is_helsels_and_rs` |
| ks_two_sample | scipy.stats.ks_2samp (two-sided, method auto: exact for a continuous distribution) | scipy>=1.10 (1.18.1 locked) | three values all below four others: D = 1, p = 2 / C(7, 3) = 0.0571429; seeded samples without ties against the exact count of spec ks_exact (stats homogeneity without ties) | `tests/unit/test_formulas_trend.py::test_the_delegated_ks_2samp_is_exact_without_ties` |
| rating_curve_least_squares | scipy.optimize.curve_fit (bounds: least_squares, trust region reflective) | scipy>=1.10 (1.18.1 locked) | eight noise-free pairs of Q = 0.012 (H - 32)^1.62 at H = 40 to 270 cm give back a = 0.012, b = 1.62 and H0 = 32 cm within 1e-6 relative (spec rating_curve_fit) | `tests/unit/test_formulas_hydrometrics.py::test_the_delegated_least_squares_recover_a_noise_free_curve` |
| harmonic_least_squares | numpy.linalg.lstsq (LAPACK gelsd) | numpy>=1.24 (2.5.4 locked) | the least squares of an exact signal of two harmonics over five hydrological years recover its mean 10 and amplitudes 5 and 2 within 1e-8 (spec harmonic_fit) | `tests/unit/test_formulas_regime.py::test_the_delegated_least_squares_recover_an_exact_signal` |
