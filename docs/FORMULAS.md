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
| [Growing and heating degree days of each day](#degree_days) | `hydrolog.statistics.meteo_temperature.daily_degree_days` | referenced | 1 | not measured |
| [The length of the dry or wet spell ending on each day](#spell_lengths) | `hydrolog.statistics.meteo_spells.spell_lengths` | oracle only | 1 | not measured |

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
- symmetry `shifted_temperatures`: the temperature and the three thresholds shifted by 1 °C give the same degree days

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

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
| `spi_k_month_sums` | `hydrolog.statistics.meteo_spi.standardized_precipitation_index` | the k-month sum of a month is the sum of the monthly sums of the k months that end in it, missing unless all k are known; the sums of each calendar month over the reference period are fitted (spi_gamma_fit) when they are known in at least 80 % of its years, those without data counted | normal_share = 4/5 - (WMO (2017). WMO Guidelines on the Calculation of Climate Normals. WMO-No. 1203, Geneva, section 4.4.2, pp. 8-9: values in at least 80 % of the years of the period; section 4.3.3, p. 6: the normal of several months from the monthly normals) | the k-month sums of the reference period stay within its years (climate_indices 3.2.0 lets those of its first k - 1 months reach before it); every analysed month gets the SPI of its own sum under the fit of its calendar month; a month whose sums the fit refuses has no SPI (notice spi_not_fitted) | WMO (2012). Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva, chapter 2 and section 6.1: the gamma distribution of the sums of each calendar month transformed to the standard normal (McKee et al. 1993) |
| `relative_precipitation` | `hydrolog.statistics.meteo_spi.standardized_precipitation_index` | 100 P / N: a month's sum in % of the normal of its calendar month, a year's in % of the sum of the twelve monthly normals (classed by month_precipitation_class and kaczorowska_class) | – | the normals of the reference period; no percentage without a normal or with a normal of 0 | Gąsiorek, E. and Musiał, E. (2011). Porównanie i klasyfikacja warunków opadowych na podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu. Woda-Środowisko-Obszary Wiejskie 11, 4(36), 107-119 (after Tomaszewska 1994), eq. 1, p. 109: RPI = P / P-bar 100 % |
| `spell_year` | `hydrolog.statistics.meteo_spells.precipitation_spells` | a spell (spell_lengths) counts, whole, in the year of its last day: a spell over the start of a year is not cut, and a year wholly inside a spell that ends later has no longest spell | – | the year of the spell's end, as climdex.pcic 1.1-11 (its default spells.can.span.years = TRUE) and ECA&D; the ETCCDI's definition read literally cuts a spell at the start of the year (ADR-0044) | ECA&D (2021). European Climate Assessment & Dataset, Algorithm Theoretical Basis Document (ATBD), version 11. KNMI, De Bilt, section 5.1, p. 20: a spell can continue into the next year and is counted against the year in which the spell ends |
| `spell_summaries` | `hydrolog.statistics.meteo_spells.precipitation_spells` | per year with a value on every day: the spells that end in it, the longest of them (CDD, CWD) with its days, and the spells of at least 10, 15 and 20 days; per period: their means over those years and the distribution of the durations of their spells that are not open, per year | – | a year needs every day (climdex.pcic accepts up to 15 missing days); an open spell, beside a missing day or an end of the series, is left out of the distribution of durations only; min_duration_days shortens the list of spells, not the summaries | ETCCDI (2009). Climate Change Indices: definitions of the 27 core indices. Expert Team on Climate Change Detection and Indices, CDD: the largest number of consecutive days with RR < 1 mm; CWD: the largest number of consecutive days with RR >= 1 mm (RR the daily precipitation) |
