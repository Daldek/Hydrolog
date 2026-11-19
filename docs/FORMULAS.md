# Formulas of Hydrolog

<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); do not edit. -->

## Tier A

| Formula | Function | Status | Version | Mutation score |
|---|---|---|---|---|
| [Potential maximum retention S of the SCS curve number](#scs_cn_retention) | `hydrolog.runoff.scs_cn.potential_retention` | referenced | 1 | not measured |
| [Direct runoff of a storm by the SCS curve number](#scs_cn_runoff) | `hydrolog.runoff.scs_cn.runoff_depths` | referenced | 1 | not measured |
| [Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)](#scs_cn_amc) | `hydrolog.runoff.scs_cn.amc_curve_number` | referenced | 1 | not measured |
| [Curve number of a soil-cover complex from the TR-55 tables](#tr55_cn) | `hydrolog.runoff.cn_lookup.table_curve_number` | referenced | 1 | not measured |
| [Mean, standard deviation and skewness of a sample (product moments)](#sample_moments) | `hydrolog.statistics.frequency.sample_moments` | referenced | 1 | not measured |
| [L-moments and L-skewness of a sample (unbiased probability-weighted moments)](#sample_l_moments) | `hydrolog.statistics.frequency.sample_l_moments` | referenced | 1 | not measured |
| [Quantiles of the generalized extreme value (GEV) distribution for return periods](#gev_quantiles) | `hydrolog.statistics.frequency.gev_quantiles` | referenced | 1 | not measured |
| [Quantiles of the log-normal distribution for return periods](#log_normal_quantiles) | `hydrolog.statistics.frequency.log_normal_quantiles` | referenced | 1 | not measured |
| [Quantiles of the Pearson type III distribution for return periods](#pearson3_quantiles) | `hydrolog.statistics.frequency.pearson3_quantiles` | referenced | 1 | not measured |
| [Quantiles of the three-parameter Weibull distribution for return periods](#weibull_quantiles) | `hydrolog.statistics.frequency.weibull_quantiles` | referenced | 1 | not measured |
| [Parameters of a distribution of annual maxima by the method of L-moments](#fit_l_moments) | `hydrolog.statistics.frequency.fit_l_moments` | oracle only | 1 | not measured |
| [Parameters of a distribution of annual maxima by the method of moments](#fit_moments) | `hydrolog.statistics.frequency.fit_moments` | referenced | 1 | not measured |
| [Parameters of a distribution of annual maxima by maximum likelihood](#fit_maximum_likelihood) | `hydrolog.statistics.frequency.fit_maximum_likelihood` | referenced | 1 | not measured |
| [Parameters of a distribution of annual maxima by least squares on the plotting positions](#fit_least_squares) | `hydrolog.statistics.frequency.fit_least_squares` | oracle only | 1 | not measured |

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

<a id="sample_moments"></a>
### Mean, standard deviation and skewness of a sample (product moments)

`hydrolog.statistics.frequency.sample_moments` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
\bar{x} = \frac{1}{n}\sum_i x_i,\quad s = \sqrt{\frac{\sum_i (x_i - \bar{x})^2}{n - 1}},\quad G = \frac{\sqrt{n(n - 1)}}{n - 2}\,\frac{m_3}{m_2^{3/2}},\quad m_k = \frac{1}{n}\sum_i (x_i - \bar{x})^k
$$

Plain text: `mean = sum(x) / n; s = sqrt(sum((x - mean)**2) / (n - 1)); G = sqrt(n (n - 1)) / (n - 2) * m3 / m2**1.5 with m_k = sum((x - mean)**k) / n`

**Sources**

- Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eqs. 2, 3a and 4a (equal to 3b and 4b), pp. 9-10; appendix 12, example 1, table 12-2 and eqs. 12-1 to 12-3 (open) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.6.1, eqs. 7.7 and 7.8, p. 63 (its eq. 7.9 is the biased skewness m3 / m2**1.5); table 7.1, p. 64 (open) <https://library.wmo.int/idurl/4/32176>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.skew with bias=False: the adjusted Fisher-Pearson standardized moment coefficient G1 = sqrt(n (n - 1)) / (n - 2) m3 / m2**1.5 (open) <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by (N - 1)(N - 2) |
| `values_not_all_equal` | precondition | min(x) < max(x) | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by S cubed, 0 for equal values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `mean` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `std` | m3/s | real | [0.0, inf) | 4 ulp of the bound |
| `skewness` | - | real | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the standard deviation with the divisor n - 1 (Bulletin 17B eq. 3a; WMO-No. 1029 eq. 7.8)
- the skewness G of Bulletin 17B eq. 4a, N sum((X - mean)**3) / ((N - 1)(N - 2) S**3), which is the adjusted Fisher-Pearson coefficient G1 of scipy.stats.skew with bias=False; WMO-No. 1029 eq. 7.9 is the biased m3 / m2**1.5, G (n - 2) / sqrt(n (n - 1))
- the sample in any unit: the mean and the standard deviation in its unit, the skewness without one
- the moments of the deviations from the mean (eqs. 3a and 4a, which Bulletin 17B p. 10 finds less sensitive to the digits carried than the sums of powers of eqs. 3b and 4b), centred twice, on the sample divided by a power of two

**Assumptions**

None stated.

**Validation:** none: the definitions of the sample statistics

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case values_not_all_equal-violated: m2 = 0 of equal values is refused before the division by m2**1.5
- `gap_propagation`: type case values-nan_element: a gap is refused
- `many_small_terms`: test_long_samples_keep_their_moments
- `moment_cancellation`: limit exact_rational: a mean of 1e9 with a spread of 0.03 against rational arithmetic

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`mean` e = 1.0, `std` e = 1.0)
- limit `exact_rational`: the statistics of the definition in exact rational arithmetic
- symmetry `mirror`: the negated sample has the negated mean and skewness and the same standard deviation

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the mean, the standard deviation and the skewness in exact rational arithmetic (fractions) (`tests/unit/test_formulas_flood_frequency.py (limit exact_rational)`)
- established: numpy.mean, numpy.std with ddof=1 and scipy.stats.skew with bias=False (`tests/unit/test_formulas_flood_frequency.py (test_the_moments_are_numpys_and_scipys)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="sample_l_moments"></a>
### L-moments and L-skewness of a sample (unbiased probability-weighted moments)

`hydrolog.statistics.frequency.sample_l_moments` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
b_r = \frac{1}{n}\binom{n - 1}{r}^{-1}\sum_{j=1}^{n}\binom{j - 1}{r}x_{(j)},\quad \lambda_1 = b_0,\quad \lambda_2 = 2b_1 - b_0,\quad \tau_3 = \frac{6b_2 - 6b_1 + b_0}{\lambda_2}
$$

Plain text: `b_r = n^-1 C(n - 1, r)^-1 sum_j C(j - 1, r) x(j) over the ascending sample x(1) <= ... <= x(n); l1 = b0; l2 = 2 b1 - b0; t3 = (6 b2 - 6 b1 + b0) / l2`

**Sources**

- Hosking, J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of order statistics. Journal of the Royal Statistical Society, Series B 52(1), 105-124, sect. 2: probability-weighted moments and the sample L-moments of their unbiased estimators (author-provided)
- Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), samlmu: the sample L-moments of Hosking (1990) from the unbiased probability-weighted moments (open) <https://cran.r-project.org/package=lmom>
- Asquith, W.H. lmomco: L-moments, censored L-moments, trimmed L-moments, L-comoments, and many distributions, R package version 2.5.8, CRAN, pwm.ub: beta_r = n^-1 C(n - 1, r)^-1 sum C(j - 1, r) x(j:n); lmoms (open) <https://cran.r-project.org/package=lmomco>
- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5.1, eqs. 5.25 to 5.27 and table II.5.4, pp. II.5-11 to II.5-12 (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.6.2, eqs. 7.11 and 7.12, p. 64; table 7.1, p. 64 (open) <https://library.wmo.int/idurl/4/32176>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Asquith, W.H. lmomco: L-moments, censored L-moments, trimmed L-moments, L-comoments, and many distributions, R package version 2.5.8, CRAN, pwm.ub: b2 divides by C(n - 1, 2), 0 for n < 3 |
| `values_not_all_equal` | precondition | min(x) < max(x) | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.4: the L-skewness is lambda3 / lambda2, and lambda2 is 0 for equal values |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `l1` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `l2` | m3/s | real | [0.0, inf) | 4 ulp of the bound |
| `t3` | - | real | [-1.0, 1.0] | 1e-09 |

**Conventions (CMP-2.3)**

- the unbiased probability-weighted moments b_r of the ascending sample (Hosking 1990; lmom samlmu; lmomco pwm.ub), not the biased estimators of plotting positions
- the L-skewness t3 = lambda3 / lambda2 (WMO-No. 168 table II.5.4)
- the sample in any unit: l1 and l2 in its unit, t3 without one
- lambda2 and lambda3 as the weighted sums of the ordered deviations from the mean that the b_r make (their weights summed first), on the sample divided by a power of two; l1 the mean centred twice
- |t3| = 1 for values all equal but the largest or the smallest; the weighted sums of n values round by up to n ulp, so a t3 within 1e-9 beyond 1 or -1 is set to the bound (its boundary tolerance)

**Assumptions**

None stated.

**Validation:** none: the definitions of the sample statistics

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case values_not_all_equal-violated: l2 = 0 of equal values is refused before the division by l2
- `gap_propagation`: type case values-nan_element: a gap is refused
- `many_small_terms`: test_long_samples_keep_their_moments
- `moment_cancellation`: limit exact_rational: a mean of 1e9 with a spread of 0.03 against rational arithmetic

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`l1` e = 1.0, `l2` e = 1.0)
- limit `exact_rational`: the L-moments of the definition in exact rational arithmetic
- symmetry `mirror`: the negated sample has the negated l1 and t3 and the same l2

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the L-moments of the unbiased probability-weighted moments in exact rational arithmetic (fractions) (`tests/unit/test_formulas_flood_frequency.py (limit exact_rational)`)
- frozen: lmom 3.3 samlmu (Hosking) and lmomco 2.5.8 lmoms (Asquith) on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="gev_quantiles"></a>
### Quantiles of the generalized extreme value (GEV) distribution for return periods

`hydrolog.statistics.frequency.gev_quantiles` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_T = \xi + \alpha\,\frac{1 - y^{c}}{c},\quad y = -\ln\left(1 - \frac{1}{T}\right);\qquad Q_T = \xi - \alpha \ln y \ \ (c = 0)
$$

Plain text: `Q_T = loc + scale (1 - y**c) / c with y = -ln(1 - 1/T); Q_T = loc - scale ln y for c = 0 (Gumbel); c is scipy's genextreme shape, k of Hosking, -xi of Coles`

**Sources**

- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5 (the GEV of Stedinger et al. 1993, F(x) = exp{-[1 - kappa (x - xi) / alpha]^(1/kappa)}); sect. 5.6.1, p. II.5-14 (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, eq. 7.5, p. 62 (the same GEV, kappa > 0 bounded above) (open) <https://library.wmo.int/idurl/4/32176>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function (open) <https://docs.scipy.org/doc/scipy/reference/stats.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `shape` | $c$ | - | real | (-inf, inf), test bound low -1.0 and high 50.0 (the shapes of Hydrolog's estimators: above -1 by the L-moments (where the GEV has a mean), at most 50, the end of the brackets of the L-moment and moment solvers) | unstated | [-0.6, 0.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\xi$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [2.0, 22.2]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $\alpha$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [1.0, 19.5]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `return_periods_years` | $T$ | years | real_array | (1.0, inf), test bound high 1000000.0 (a million years lies far beyond every design flood (the Polish rules ask for 5,000 years at most) and tests the far tail of each distribution) | unstated | [2.0, 5000.0]: Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `quantiles` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the shape c of scipy's genextreme, equal to k of Hosking and kappa of WMO-No. 168 and WMO-No. 1029, and to -xi of Coles (2001): c > 0 has the upper bound loc + scale/c, c < 0 a heavy upper tail
- the quantile of the return period T at the annual exceedance probability 1/T, the non-exceedance 1 - 1/T (Polish Q_p% with p = 100/T %, KZGW 2017 eq. 3.7; WMO-No. 168 sect. 5.6.1), computed as the inverse survival function at 1/T, which keeps its digits for long return periods
- loc and scale in the unit of the sample; the formula is homogeneous

**Assumptions**

None stated.

**Validation:** none: the quantile function of the distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range case return_periods_years-physical_low_inside: T just above 1 puts the non-exceedance probability at 2.2e-16, the far lower tail, finite
- `exp_overflow`: range cases shape-physical_low_test_bound and shape-physical_high_test_bound with the far tails: y**c of c = 50 at T just above 1 and of c = -1 at a million years stay finite

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `return_periods_years` increasing, `loc` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`loc` e = 1.0, `scale` e = 1.0) give outputs times 2^e (`quantiles` e = 1.0)
- limit `closed_form`: the quantile function of the GEV and, at c = 0, of the Gumbel distribution, in decimal arithmetic at 50 digits
- symmetry `location`: a location larger by 1 gives quantiles larger by 1

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the quantile function in decimal arithmetic at 50 digits (`tests/unit/test_formulas_flood_frequency.py (limit closed_form)`)
- frozen: lmom 3.3 quagev at the parameters of pelgev on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="log_normal_quantiles"></a>
### Quantiles of the log-normal distribution for return periods

`hydrolog.statistics.frequency.log_normal_quantiles` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_T = \epsilon + e^{\mu} \exp\left(\sigma\,\Phi^{-1}\left(1 - \frac{1}{T}\right)\right)
$$

Plain text: `Q_T = loc + scale exp(s z) with z the standard normal quantile of the non-exceedance 1 - 1/T; loc = 0 is the two-parameter distribution`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.35 and 3.40, p. 46 (Q_p = epsilon + exp(mu + sigma u_p)); example 3.3, table 3.12, p. 51 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5 and its note a (the three-parameter log-normal with Y = ln(X - xi)) (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function (open) <https://docs.scipy.org/doc/scipy/reference/stats.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `shape` | $\sigma$ | - | real | (0.0, inf), test bound high 5.0 (a shape of 5 spreads the quantiles of T from just above 1 to a million years over a factor of 10**15; the fits of annual maxima stay below 1) | unstated | [0.6, 0.9]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\epsilon$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.0, 0.4]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $e^{\mu}$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [2.4, 27.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `return_periods_years` | $T$ | years | real_array | (1.0, inf), test bound high 1000000.0 (a million years lies far beyond every design flood (the Polish rules ask for 5,000 years at most) and tests the far tail of each distribution) | unstated | [2.0, 5000.0]: Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `quantiles` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- scipy's lognorm(s, loc, scale): s = sigma, loc = epsilon (the lower bound of KZGW 2017 eq. 3.35), scale = exp(mu)
- the quantile of the return period T at the annual exceedance probability 1/T, the non-exceedance 1 - 1/T (Polish Q_p% with p = 100/T %, KZGW 2017 eq. 3.7; WMO-No. 168 sect. 5.6.1), computed as the inverse survival function at 1/T, which keeps its digits for long return periods
- loc and scale in the unit of the sample; the formula is homogeneous

**Assumptions**

None stated.

**Validation:** none: the quantile function of the distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range case return_periods_years-physical_low_inside: T just above 1 puts the non-exceedance probability at 2.2e-16, the far lower tail, finite
- `exp_overflow`: range case shape-physical_high_test_bound: exp(5 z) at a million years is 2e10, finite

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `return_periods_years` increasing, `loc` increasing, `scale` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`loc` e = 1.0, `scale` e = 1.0) give outputs times 2^e (`quantiles` e = 1.0)
- limit `closed_form`: loc + scale exp(s z) with an independent normal quantile
- symmetry `location`: a location larger by 1 gives quantiles larger by 1

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: loc + scale exp(s z) with z from Python's statistics.NormalDist (`tests/unit/test_formulas_flood_frequency.py (limit closed_form)`)
- frozen: lmom 3.3 qualn3 at the parameters of pelln3 with bound 0 on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="pearson3_quantiles"></a>
### Quantiles of the Pearson type III distribution for return periods

`hydrolog.statistics.frequency.pearson3_quantiles` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_T = \mu + K_{\gamma}\!\left(1 - \frac{1}{T}\right)\sigma
$$

Plain text: `Q_T = loc + K(skew, T) scale, K the frequency factor: the standardised Pearson III quantile of the non-exceedance 1 - 1/T (a gamma of shape 4 / skew**2 shifted and scaled to the mean 0 and standard deviation 1)`

**Sources**

- Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 1, p. 9 (log Q = X + K S) and appendix 3, pp. 3-1 to 3-10 (the frequency factors K of Harter 1969 for skews of -9 to 9) (open) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.1 and 3.3, p. 28 (Q_p = epsilon + the gamma quantile of 1 - p with lambda and 1/alpha); example 3.2, table 3.9, p. 44 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function (open) <https://docs.scipy.org/doc/scipy/reference/stats.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `skew` | $\gamma$ | - | real | (-inf, inf), test bound low -9.0 and high 9.0 (Bulletin 17B appendix 3 tabulates the frequency factor for skews of -9 to 9) | unstated | [1.3, 2.7]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\mu$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [3.0, 35.4]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $\sigma$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [2.0, 29.6]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `return_periods_years` | $T$ | years | real_array | (1.0, inf), test bound high 1000000.0 (a million years lies far beyond every design flood (the Polish rules ask for 5,000 years at most) and tests the far tail of each distribution) | unstated | [2.0, 5000.0]: Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `quantiles` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- scipy's pearson3(skew, loc, scale) is parameterised by the mean, standard deviation and skewness, as Bulletin 17B and lmom's PE3 (mu, sigma, gamma); KZGW 2017's (epsilon, alpha, lambda) give skew = 2 / sqrt(lambda), loc = epsilon + lambda / alpha and scale = sqrt(lambda) / alpha
- a positive skewness has the lower bound loc - 2 scale / skew, a negative one the upper bound loc - 2 scale / skew
- the quantile of the return period T at the annual exceedance probability 1/T, the non-exceedance 1 - 1/T (Polish Q_p% with p = 100/T %, KZGW 2017 eq. 3.7; WMO-No. 168 sect. 5.6.1), computed as the inverse survival function at 1/T, which keeps its digits for long return periods
- loc and scale in the unit of the sample; the formula is homogeneous

**Assumptions**

None stated.

**Validation:** none: the quantile function of the distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range case return_periods_years-physical_low_inside: T just above 1 puts the non-exceedance probability at 2.2e-16, the far lower tail, finite
- `exp_overflow`: range cases skew-physical_low_test_bound and skew-physical_high_test_bound: a gamma shape of 4/81 in both tails stays finite

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `return_periods_years` increasing, `loc` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`loc` e = 1.0, `scale` e = 1.0) give outputs times 2^e (`quantiles` e = 1.0)
- limit `normal`: the skewness 0 gives the normal distribution
- symmetry `location`: a location larger by 1 gives quantiles larger by 1

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- frozen: lmom 3.3 quape3 at the parameters of pelpe3 on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)
- algorithm: the normal quantile of Python's statistics.NormalDist at the skewness 0 (`tests/unit/test_formulas_flood_frequency.py (limit normal)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="weibull_quantiles"></a>
### Quantiles of the three-parameter Weibull distribution for return periods

`hydrolog.statistics.frequency.weibull_quantiles` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q_T = \epsilon + \frac{1}{\alpha_W}\left(\ln T\right)^{1/\beta_W}
$$

Plain text: `Q_T = loc + scale (ln T)**(1/k): F(x) = 1 - exp(-((x - loc) / scale)**k) = 1 - 1/T`

**Sources**

- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eqs. 3.52 and 3.55, pp. 53-54 (P(Q >= x) = exp(-[alpha_W (x - epsilon)]^beta_W)); example 3.4, table 3.15, p. 60 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, eq. 7.6, p. 62 (F(x) = 1 - exp[-((x - xi) / alpha)^kappa]) and eq. 7.13, p. 64 (open) <https://library.wmo.int/idurl/4/32176>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function (open) <https://docs.scipy.org/doc/scipy/reference/stats.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `shape` | $\beta_W$ | - | real | (0.0, inf), test bound high 50.0 (shapes above 50 put the quantile of every T up to a million years within 6 % of loc + scale ((ln 10**6)**(1/50) = 1.054)) | unstated | [0.7, 1.4]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\epsilon$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [-1.0, 4.9]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $1/\alpha_W$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [1.5, 37.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `return_periods_years` | $T$ | years | real_array | (1.0, inf), test bound high 1000000.0 (a million years lies far beyond every design flood (the Polish rules ask for 5,000 years at most) and tests the far tail of each distribution) | unstated | [2.0, 5000.0]: Rozporządzenie Ministra Środowiska z dnia 20 kwietnia 2007 r. w sprawie warunków technicznych, jakim powinny odpowiadać budowle hydrotechniczne i ich usytuowanie (Dz.U. 2007 nr 86 poz. 579); Dz.U. 2026 poz. 692 repeats its values, załącznik nr 4: the control flood of a structure of class I at p = 0.02 %, 5,000 years; Hydrolog's default return periods start at 2 years |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `finite_quantiles` | precondition | ln(scale) + ln(ln T) / k < 708.78 for every T: scale (ln T)**(1/k) below e**-1 of the largest float64 | Harris, C.R. et al. (2020). Array programming with NumPy. Nature 585, 357-362, numpy.finfo(numpy.float64).max, about 1.8e308, the largest IEEE 754 binary64 number |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `quantiles` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- scipy's weibull_min(k, loc, scale), the lower-bounded Weibull fitted to maxima as KZGW 2017 eq. 3.52 (epsilon = loc, alpha_W = 1/scale, beta_W = k) and lmom's (zeta, beta, delta)
- the quantile of the return period T at the annual exceedance probability 1/T, the non-exceedance 1 - 1/T (Polish Q_p% with p = 100/T %, KZGW 2017 eq. 3.7; WMO-No. 168 sect. 5.6.1), computed as the inverse survival function at 1/T, which keeps its digits for long return periods
- loc and scale in the unit of the sample; the formula is homogeneous

**Assumptions**

None stated.

**Validation:** none: the quantile function of the distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: range case return_periods_years-physical_low_inside: T just above 1 puts the non-exceedance probability at 2.2e-16, the far lower tail, finite
- `exp_overflow`: constraint case finite_quantiles-violated: a shape of 0.001 would raise (ln T)**(1/k) beyond the float64 numbers at T = 5,000 years; it is refused before the computation

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `return_periods_years` increasing, `loc` increasing, `scale` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`loc` e = 1.0, `scale` e = 1.0) give outputs times 2^e (`quantiles` e = 1.0)
- limit `closed_form`: loc + scale (ln T)^(1/k) in decimal arithmetic at 50 digits
- symmetry `location`: a location larger by 1 gives quantiles larger by 1

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: loc + scale (ln T)^(1/k) in decimal arithmetic at 50 digits (`tests/unit/test_formulas_flood_frequency.py (limit closed_form)`)
- frozen: lmom 3.3 quawei at the parameters of pelwei on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fit_l_moments"></a>
### Parameters of a distribution of annual maxima by the method of L-moments

`hydrolog.statistics.frequency.fit_l_moments` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
\tau_3 = \frac{2(1 - 3^{-c})}{1 - 2^{-c}} - 3,\quad \alpha = \frac{\lambda_2 c}{(1 - 2^{-c})\Gamma(1 + c)},\quad \xi = \lambda_1 - \alpha\frac{1 - \Gamma(1 + c)}{c};\qquad s = 2\,\mathrm{erf}^{-1}\frac{\lambda_2}{\lambda_1};\qquad \sigma = \lambda_2\sqrt{\pi a}\,\frac{\Gamma(a)}{\Gamma(a + 1/2)},\ G = \frac{2\,\mathrm{sign}\,\tau_3}{\sqrt{a}}
$$

Plain text: `the distribution whose L-moments are the sample's l1, l2 and t3: log-normal (loc 0) s = 2 erfinv(l2 / l1), scale = l1 exp(-s**2 / 2); GEV: c solves t3 = 2 (1 - 3**-c) / (1 - 2**-c) - 3, scale = l2 c / ((1 - 2**-c) Gamma(1 + c)), loc = l1 - scale (1 - Gamma(1 + c)) / c; Pearson III: alpha = 4 / G**2 from |t3| (rational approximations), G = 2 sign(t3) / sqrt(alpha), scale = l2 sqrt(pi alpha) Gamma(alpha) / Gamma(alpha + 1/2), loc = l1; Weibull: the GEV (c, xi, a) of (-l1, l2, -t3), shape = 1/c, loc = -xi - a/c, scale = a/c`

**Sources**

- Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from |t3| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments (open) <https://cran.r-project.org/package=lmom>
- Hosking, J.R.M. and Wallis, J.R. (1997). Regional Frequency Analysis: An Approach Based on L-Moments. Cambridge University Press, appendix A.5 (GEV), A.8 (log-normal), A.9 (Pearson type III, the rational approximations of alpha from |t3|) (author-provided)
- Hosking, J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of order statistics. Journal of the Royal Statistical Society, Series B 52(1), 105-124, sect. 2: probability-weighted moments and the sample L-moments of their unbiased estimators (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), samlmu: t3 needs 3 values |
| `values_not_all_equal` | precondition | min(x) < max(x) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelgev, pelpe3: l2 must be positive |
| `positive_values` | precondition | min(x) > 0 for the log-normal (location 0) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 |
| `l_moments_within_distribution` | precondition | l2 < l1 (log-normal); -1 < t3 < 1 (GEV, Pearson III); -0.1699 < t3 < 1 (Weibull) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `a1` | $A_1$ | 0.2906 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `a2` | $A_2$ | 0.1882 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `a3` | $A_3$ | 0.0442 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b1` | $B_1$ | 0.36067 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b2` | $B_2$ | -0.59567 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b3` | $B_3$ | 0.25361 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b4` | $C_1$ | -2.78861 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b5` | $C_2$ | 2.56096 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `b6` | $C_3$ | -0.77045 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `normal_below` | $\tau_{3,0}$ | 1e-06 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), lmoments.f, routines PELGEV (the GEV of the L-moments), PELPE3 (Pearson III: alpha from \|t3\| by rational approximations, relative accuracy better than 3e-5) and PELLN3 (the log-normal of a given bound); R pelwei, the GEV of the negated L-moments |
| `gumbel_l_skewness` | $\tau_{3,G}$ | 0.1699250014423126 | - | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelwei: the GEV of the negated L-moments, which needs -t3 below the Gumbel's L-skewness 2 ln 3 / ln 2 - 3 = 0.1699 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape` | - | real | (-inf, inf) | 4 ulp of the bound |
| `loc` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `scale` | m3/s | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the unbiased sample L-moments of sample_l_moments
- scipy's parameters: the GEV shape c is Hosking's k and -xi of Coles; Pearson III (loc, scale, shape) are its mean, standard deviation and skewness; the log-normal has location 0
- the GEV shape solved exactly by brentq in -1 < c <= 50 (lmom's pelgev uses Donaldson's approximation, within 2e-7 of it); a t3 beyond the L-skewness of an end of that bracket gives the end
- Weibull as the GEV of the negated L-moments, as lmom's pelwei

**Assumptions**

- the annual maxima are independent and identically distributed

**Validation:** none: the estimator gives the distribution of the sample's L-moments; Hosking and Wallis (1997) report its efficiency on simulated samples

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case l_moments_within_distribution-violated and test_l_skewness_near_one_clamps_the_gev_shape: |t3| = 1 is refused, a t3 within rounding of it gives the end of the bracket
- `unbounded_iteration`: test_l_skewness_near_one_clamps_the_gev_shape: brentq runs in a bracket, its ends clamped (at most 100 iterations)
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused
- `moment_cancellation`: test_a_large_mean_shifts_the_fits: a mean of 1e9 with the spread of the Polana maxima over 1000

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`annual_maxima` e = 1.0) give outputs times 2^e (`loc` e = 1.0, `scale` e = 1.0)
- limit `l_moments_of_the_fit`: the fitted distribution has the sample's l1, l2 and t3 (l1 and l2 for the log-normal), by quadrature of its quantile function

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the L-moments of the fitted distribution by quadrature of its quantile function (`tests/unit/test_formulas_flood_frequency.py (limit l_moments_of_the_fit)`)
- frozen: lmom 3.3 pelgev, pelpe3, pelwei, pelln3 (bound 0) and lmomco 2.5.8 pargev (useHosking=FALSE) on seven samples, R 4.5.3, 2026-11-18 (`tests/oracles/frequency_lmom_r.csv`)

**Tests by class (CMP §6):** oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fit_moments"></a>
### Parameters of a distribution of annual maxima by the method of moments

`hydrolog.statistics.frequency.fit_moments` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
\sigma_l = \sqrt{\ln(1 + C_v^2)},\ e^{\mu} = \frac{\bar{x}}{\sqrt{1 + C_v^2}};\qquad (\gamma, \mu, \sigma) = (G, \bar{x}, s);\qquad \gamma_{GEV}(c) = G,\ \alpha = \frac{s}{\sigma_{GEV}(c)},\ \xi = \bar{x} - \alpha\,\mu_{GEV}(c)
$$

Plain text: `the distribution whose mean, standard deviation and skewness are the sample's mean, s and G: log-normal (loc 0) s_l = sqrt(ln(1 + Cv**2)), scale = mean / sqrt(1 + Cv**2), Cv = s / mean; Pearson III (G, mean, s); GEV: c solves G(c) = G, G(c) the skewness of the GEV, scale = s / sd(c), loc = mean - scale m(c), m(c) and sd(c) the mean and standard deviation of the GEV(c, 0, 1); Weibull: the GEV (c, xi, a) of (-mean, s, -G), shape = 1/c, loc = -xi - a/c, scale = a/c`

**Sources**

- Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, pp. 9-10 and appendix 12, example 1: the log-Pearson type III distribution of the mean, standard deviation and skewness of the logarithms (eqs. 2, 3a, 4a) (open) <https://pubs.usgs.gov/unnumbered/70275162/report.pdf>
- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5 and table II.5.2, pp. II.5-5 to II.5-12: the method of moments and the moments of the GEV, log-normal, Pearson type III and Weibull distributions (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.genextreme, lognorm, pearson3 and weibull_min: isf, the inverse of the survival function (open) <https://docs.scipy.org/doc/scipy/reference/stats.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by (N - 1)(N - 2) |
| `values_not_all_equal` | precondition | min(x) < max(x) | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the skewness divides by S cubed, 0 for equal values |
| `positive_values` | precondition | min(x) > 0 for the log-normal (location 0) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 |
| `skewness_within_distribution` | precondition | G > -1.1395 for the Weibull distribution, the skewness of the reversed Gumbel distribution | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `gumbel_skewness` | $\gamma_G$ | 1.1395470994046488 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape` | - | real | (-inf, inf) | 4 ulp of the bound |
| `loc` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `scale` | m3/s | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the sample moments of sample_moments: s with the divisor n - 1, G the adjusted Fisher-Pearson coefficient
- the log-normal of location 0 from the mean and Cv of the values, not of their logarithms
- scipy's parameters: the GEV shape c is Hosking's k and -xi of Coles; Pearson III (loc, scale, shape) are its mean, standard deviation and skewness
- the GEV shape solved by brentq in -1/3 < c <= 50 (the skewness exists above -1/3); Weibull as the GEV of the negated moments, its c in 0 < c <= 50

**Assumptions**

- the annual maxima are independent and identically distributed

**Validation:** none: the estimator gives the distribution of the sample's moments

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case skewness_within_distribution-violated: the Weibull shape 1/c grows without limit as G falls to -1.1395
- `unbounded_iteration`: test_a_skewness_beyond_the_bracket_clamps: brentq runs in a bracket, its ends clamped (at most 100 iterations)
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused
- `moment_cancellation`: test_a_large_mean_shifts_the_fits: a mean of 1e9 with the spread of the Polana maxima over 1000

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`annual_maxima` e = 1.0) give outputs times 2^e (`loc` e = 1.0, `scale` e = 1.0)
- limit `moments_of_the_fit`: the fitted distribution has the sample's mean, standard deviation and skewness (the mean and s for the log-normal), by scipy's stats

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the mean, variance and skewness of the fitted distribution by scipy.stats (`tests/unit/test_formulas_flood_frequency.py (limit moments_of_the_fit)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fit_maximum_likelihood"></a>
### Parameters of a distribution of annual maxima by maximum likelihood

`hydrolog.statistics.frequency.fit_maximum_likelihood` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
(\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\max \sum_i \ln f(x_i; k, \xi, \alpha);\qquad \hat{\mu} = \frac{1}{n}\sum_i \ln x_i,\ \hat{s}^2 = \frac{1}{n}\sum_i (\ln x_i - \hat{\mu})^2
$$

Plain text: `the parameters that maximise the log-likelihood sum_i ln f(x_i; shape, loc, scale) of the distribution's density f; for the log-normal of location 0 in closed form: ln scale = mean(ln x), s = sqrt(mean((ln x - ln scale)**2))`

**Sources**

- Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer, sect. 3.3.2 (the likelihood of the GEV) and 3.4.1 (Port Pirie) (author-provided)
- Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the likelihood of a three-parameter distribution has no maximum where its density is infinite at the bound of its support (author-provided)
- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5, p. II.5-11: the method of maximum likelihood; sect. 5.3.2.3: the Weibull density goes to infinity at its bound for k < 1 (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n > p, the number of parameters: n >= 3 for the log-normal, n >= 4 for the others | Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, n values fit n parameters exactly, where the likelihood has no maximum |
| `values_not_all_equal` | precondition | min(x) < max(x) | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.5: the likelihood of values all equal grows without limit as the scale falls to 0 |
| `positive_values` | precondition | min(x) > 0 for the log-normal (location 0) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 |
| `likelihood_has_a_maximum` | precondition | the likelihood has a maximum inside the shapes searched: the search ends neither within 1e-3 of the shapes whose density is infinite at a bound of the support (GEV c >= 1, Pearson III \|G\| >= 2, Weibull shape <= 1), nor of GEV c = -1 (no mean) or Weibull shape 50, nor at a scale of a millionth of the standard deviation; a GEV has at most half the values tied at the smallest; and the search settles | Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the bound placed at the closest value makes the likelihood grow without limit |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape` | - | real | (-inf, inf) | 4 ulp of the bound |
| `loc` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `scale` | m3/s | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- scipy's densities and parameters: the GEV shape c is -xi of Coles (evd, extRemes, ismev)
- the search runs on the standardised sample (x / 2**e - mean) / sd, from the L-moments' estimate; Nelder-Mead (xatol 1e-10, fatol 1e-12) is run again from its end until a run gains at most 1e-9 of log-likelihood, at most 21 runs
- the log-normal of location 0 in closed form (scipy's lognorm.fit with floc=0)

**Assumptions**

- the annual maxima are independent and identically distributed

**Validation:** none: the estimator gives the most likely distribution of the sample

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case likelihood_has_a_maximum-violated: the density infinite at a bound placed on a value
- `unbounded_iteration`: test_a_search_that_does_not_settle_is_refused: a search that does not settle in its bounded count of runs fails the precondition likelihood_has_a_maximum
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused
- `moment_cancellation`: test_a_large_mean_shifts_the_fits: a mean of 1e9 with the spread of the Polana maxima over 1000

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`annual_maxima` e = 1.0) give outputs times 2^e (`loc` e = 1.0, `scale` e = 1.0)
- limit `local_maximum`: no point a step of 1e-4 from the estimate is more likely

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- frozen: evd 2.3.7.1 fgev, extRemes 2.2.1 fevd, ismev 1.43 gev.fit and lmomco 2.5.8 mle2par on seven samples, R 4.5.3, 2026-11-18: Hydrolog's log-likelihood is not lower (`tests/oracles/frequency_ml_r.csv (tests/unit/test_maximum_likelihood.py)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fit_least_squares"></a>
### Parameters of a distribution of annual maxima by least squares on the plotting positions

`hydrolog.statistics.frequency.fit_least_squares` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
(\hat{k}, \hat{\xi}, \hat{\alpha}) = \arg\min \sum_{j=1}^{n}\left(x_{(j)} - Q\left(\frac{j}{n + 1}; k, \xi, \alpha\right)\right)^2
$$

Plain text: `the parameters that minimise sum_j (x(j) - Q(j / (n + 1)))**2 over the ascending sample x(1) <= ... <= x(n), Q the quantile function of the distribution: the quantiles at the Weibull plotting positions`

**Sources**

- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the Weibull plotting position i / (n + 1) of the graphical fit of a distribution to the ordered sample (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 3.7: the empirical probability m / (N + 1) of the ordered annual maxima (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 3 | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, eq. 4a: the moments of the start divide by (N - 1)(N - 2) |
| `values_not_all_equal` | precondition | min(x) < max(x) | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1: values all equal have no spread to fit |
| `positive_values` | precondition | min(x) > 0 for the log-normal (location 0) | Hosking, J.R.M. lmom: L-moments, R package version 3.3, CRAN (the Fortran routines of Hosking and Wallis 1997), pelln3 with bound 0: the distribution of ln(x - 0), defined for x > 0 |
| `skewness_within_distribution` | precondition | G > -1.1395 for the Weibull distribution: the search starts from the moments' estimate | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 |
| `squares_have_a_minimum` | precondition | the sum of squares has a minimum inside the shapes searched (log-normal s < 5, GEV -1 < c < 50, Pearson III \|G\| < 9, Weibull shape < 50) on which the search settles | Interagency Advisory Committee on Water Data (1982). Guidelines for Determining Flood Flow Frequency, Bulletin 17B of the Hydrology Subcommittee, U.S. Geological Survey, Reston, Virginia, appendix 3: the frequency factors of Pearson type III, tabulated for skews of -9 to 9 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `gumbel_skewness` | $\gamma_G$ | 1.1395470994046488 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, table II.5.2, p. II.5-5: the Gumbel (EV1) distribution, of skewness 1.1396, 12 sqrt(6) zeta(3) / pi**3 |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape` | - | real | (-inf, inf) | 4 ulp of the bound |
| `loc` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `scale` | m3/s | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the Weibull plotting positions j / (n + 1) of the ascending sample, unweighted residuals in the unit of the sample
- scipy's parameters, as fit_moments
- the search runs on the standardised sample (the log-normal, of location 0, only divided by its standard deviation) from the moments' estimate; Nelder-Mead (xatol 1e-10, fatol 1e-12) is run again from its end until a run gains at most 1e-9, at most 21 runs

**Assumptions**

- the annual maxima are independent and identically distributed

**Validation:** none: the estimator gives the distribution closest to the plotted sample

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case skewness_within_distribution-violated: the Weibull start of a skewness below the reversed Gumbel's
- `unbounded_iteration`: test_a_search_that_does_not_settle_is_refused: a search that does not settle in its bounded count of runs fails the precondition squares_have_a_minimum
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused
- `moment_cancellation`: test_a_large_mean_shifts_the_fits: a mean of 1e9 with the spread of the Polana maxima over 1000

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`annual_maxima` e = 1.0) give outputs times 2^e (`loc` e = 1.0, `scale` e = 1.0)
- limit `local_minimum`: no point a step of 1e-4 from the estimate has a smaller sum of squares

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the sum of squares at points a step of 1e-4 from the estimate, by math.fsum (`tests/unit/test_formulas_flood_frequency.py (limit local_minimum)`)
- algorithm: Powell's method from the estimate finds no smaller sum of squares (`tests/unit/test_formulas_flood_frequency.py (test_powell_finds_no_smaller_squares)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
