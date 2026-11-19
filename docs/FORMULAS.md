# Formulas of Hydrolog

<!-- Generated from the formula specs by nogat_formulas (CMP-2.6); do not edit. -->

## Tier A

| Formula | Function | Status | Version | Mutation score |
|---|---|---|---|---|
| [Potential maximum retention S of the SCS curve number](#scs_cn_retention) | `hydrolog.runoff.scs_cn.potential_retention` | referenced | 1 | not measured |
| [Direct runoff of a storm by the SCS curve number](#scs_cn_runoff) | `hydrolog.runoff.scs_cn.runoff_depths` | referenced | 1 | not measured |
| [Curve number of antecedent runoff condition I or III (Hawkins et al. 1985)](#scs_cn_amc) | `hydrolog.runoff.scs_cn.amc_curve_number` | referenced | 1 | not measured |
| [Curve number of a soil-cover complex from the TR-55 tables](#tr55_cn) | `hydrolog.runoff.cn_lookup.table_curve_number` | referenced | 1 | not measured |
| [SCS (NRCS) dimensionless unit hydrograph of a unit duration](#scs) | `hydrolog.runoff.unit_hydrograph.scs_unit_hydrograph` | referenced | 1 | not measured |
| [Snyder's synthetic unit hydrograph: lag, peak, time base and widths](#snyder) | `hydrolog.runoff.snyder_uh.snyder_parameters` | referenced | 1 | not measured |
| [Snyder's unit hydrograph as the gamma curve of 1 mm through its peak](#snyder_shape) | `hydrolog.runoff.snyder_uh.snyder_shape` | oracle only | 1 | not measured |
| [Direct runoff of excess rainfall by discrete convolution with a unit hydrograph](#uh_convolution) | `hydrolog.runoff.convolution.convolve_discrete` | referenced | 1 | not measured |

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

## Tier B

| Formula | Function | Definition | Constants | Convention | Source |
|---|---|---|---|---|---|
| `weighted_cn` | `hydrolog.runoff.cn_lookup.calculate_weighted_cn` | CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the parts | – | areas or shares in any one unit; a part of zero area counts nothing | USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, Chapter 10, example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3) |
