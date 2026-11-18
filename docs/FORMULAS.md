# Formulas of Hydrolog

<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); do not edit. -->

## Tier A

| Formula | Function | Status | Version | Mutation score |
|---|---|---|---|---|
| [Potential maximum retention S of the SCS curve number](#scs_cn_retention) | `hydrolog.runoff.scs_cn.potential_retention` | referenced | 1 | not measured |
| [Direct runoff of a storm by the SCS curve number](#scs_cn_runoff) | `hydrolog.runoff.scs_cn.runoff_depths` | referenced | 1 | not measured |
| [Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)](#scs_cn_amc) | `hydrolog.runoff.scs_cn.amc_curve_number` | referenced | 1 | not measured |
| [Time of concentration by Kirpich's formula (Tennessee form)](#kirpich) | `hydrolog.time.concentration.ConcentrationTime.kirpich` | referenced | 1 | not measured |
| [Time of concentration by the NRCS watershed lag equation (Mockus 1961)](#nrcs) | `hydrolog.time.concentration.ConcentrationTime.nrcs` | referenced | 1 | not measured |
| [Time of concentration by Giandotti's formula (1934)](#giandotti) | `hydrolog.time.concentration.ConcentrationTime.giandotti` | referenced | 1 | not measured |
| [Overland flow time by the FAA formula (AC 150/5320-5B, 1970)](#faa) | `hydrolog.time.concentration.ConcentrationTime.faa` | referenced | 1 | not measured |
| [Overland flow time by Kerby's formula (1959)](#kerby) | `hydrolog.time.concentration.ConcentrationTime.kerby` | referenced | 1 | not measured |
| [Time of concentration by the Kerby-Kirpich method (Roussel et al. 2005)](#kerby_kirpich) | `hydrolog.time.concentration.ConcentrationTime.kerby_kirpich` | referenced | 1 | not measured |

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
