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
| [Muskingum routing through N equal sub-reaches (McCarthy's storage, trapezoid continuity)](#muskingum) | `hydrolog.routing.formulas.muskingum.muskingum_route` | referenced | 1 | not measured |
| [Cascade of n equal linear reservoirs, exact for an inflow linear between the ordinates (Nash)](#linear_reservoir_cascade) | `hydrolog.routing.formulas.cascade.cascade_route` | oracle only | 1 | not measured |
| [Lag routing: the inflow translated by a fixed time, linear between the ordinates](#lag) | `hydrolog.routing.formulas.lag.lag_route` | oracle only | 1 | not measured |
| [Normal flow of a trapezoidal, rectangular or triangular channel by Manning's equation, with the kinematic celerity dQ/dA](#manning_normal_flow) | `hydrolog.routing.formulas.manning.normal_flow` | referenced | 1 | not measured |
| [Muskingum-Cunge routing with constant coefficients on N equal distance steps (Cunge's K and X)](#muskingum_cunge) | `hydrolog.routing.formulas.cunge.muskingum_cunge_route` | referenced | 1 | not measured |
| [Level-pool routing by storage indication (modified Puls) through N equal pools](#level_pool) | `hydrolog.routing.formulas.level_pool.level_pool_route` | referenced | 1 | not measured |
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
| [Sielianinov's hydrothermal coefficient of a month or a season](#sielianinov_coefficient) | `hydrolog.statistics.meteo_hydrothermal.sielianinov_coefficient` | referenced | 1 | not measured |
| [Class of Sielianinov's hydrothermal coefficient (Skowera and Puła)](#sielianinov_class) | `hydrolog.statistics.meteo_hydrothermal.sielianinov_class` | referenced | 1 | not measured |
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
| [Anderson-Darling statistic A² of a sample against a fitted distribution](#anderson_darling) | `hydrolog.statistics.frequency.anderson_darling` | oracle only | 1 | not measured |
| [Akaike information criterion of a distribution fitted to a sample](#akaike_information_criterion) | `hydrolog.statistics.frequency.akaike_information_criterion` | referenced | 1 | not measured |
| [Plotting positions of annual maxima: exceedance probabilities and return periods](#plotting_positions) | `hydrolog.statistics._types.compute_plotting_positions` | referenced | 1 | not measured |
| [Plotting positions of annual minima: non-exceedance probabilities and return periods](#non_exceedance_positions) | `hydrolog.statistics._types.compute_non_exceedance_positions` | referenced | 1 | not measured |
| [Fisher-Tippett distribution of annual minima by maximum likelihood and its quantiles](#fisher_tippett_minima) | `hydrolog.statistics.low_flows.fisher_tippett_minima` | oracle only | 1 | not measured |
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
| [Walsh and Lawler's seasonality index of twelve monthly totals](#seasonality_index) | `hydrolog.statistics.regime.seasonality_index` | referenced | 1 | not measured |
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

<a id="muskingum"></a>
### Muskingum routing through N equal sub-reaches (McCarthy's storage, trapezoid continuity)

`hydrolog.routing.formulas.muskingum.muskingum_route` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1},\quad c_0 = \frac{\Delta t - 2kX}{D},\ c_1 = \frac{\Delta t + 2kX}{D},\ c_2 = \frac{2k(1-X) - \Delta t}{D},\ D = 2k(1-X) + \Delta t,\ k = \frac{K}{N}
$$

Plain text: `in each of N sub-reaches of k = K / N in series: O[t] = c0 I[t] + c1 I[t-1] + c2 O[t-1], c0 = (dt - 2 k X) / D, c1 = (dt + 2 k X) / D, c2 = (2 k (1 - X) - dt) / D, D = 2 k (1 - X) + dt; O[0] = O0 in every sub-reach; storage S = k sum_j [X I_j + (1 - X) O_j] [m3]`

**Sources**

- US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, equations of the storage and of the weights; X from 0 to 0.5; sub-reaches whose travel time is about the time step (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-model>
- US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, eqs. 9-15 to 9-19, pp. 9-12 to 9-15 (open) <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>
- USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-6 to 17-11 and the Muskingum method, pp. 17-14 to 17-18 (open) <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
- McCarthy, G.T. (1938). The unit hydrograph and flood routing, Conference of the North Atlantic Division, US Army Corps of Engineers, New London, Conn. (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `inflow_m3s` | $I_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a series of daily discharges (IMGW-PIB)) | unstated | [5.0, 720.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d) |
| `k_min` | $K$ | min | real | (0.0, inf), test bound high 12000.0 (ten times the longest K of Hydrolog's routing tests, the Iowa example's 20 h (1,200 min)) | unstated | [10.0, 1200.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), K of 10 to 60 min in the tests of the reach, 2.3 h (NPTEL) and 20 h (Iowa) in the published examples |
| `x` | $X$ | - | real | [0.0, 0.5]: US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, equations of the storage and of the weights; X from 0 to 0.5; sub-reaches whose travel time is about the time step | [0.0, 0.5]: US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, equations of the storage and of the weights; X from 0 to 0.5; sub-reaches whose travel time is about the time step | [0.1, 0.3]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), X of 0.2 in most tests of the reach, 0.15 (NPTEL) and 0.25 (Iowa) in the published examples; 0.1 to 0.3 for natural streams after Fread (1993), as Balaz, Danacova and Szolgay (2010, Slovak Journal of Civil Engineering 18(3)) cite it |
| `subreaches` | $N$ | - | integer | [1.0, inf), test bound high 1000.0 (K / dt of the test bound of K (12,000 min) on a step of 12 min, the rule of thumb of the sub-reaches) | unstated | [1.0, 10.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 to 3 sub-reaches in the tests of the reach and in the published examples; K / dt rounded up to 10 in the network tests |
| `initial_outflow_m3s` | $O_0$ | m3/s | real | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `representable` | precondition | dt, K / N and dt / (K / N) >= 2.2e-308, the smallest normal float64, and 2 K [s] and the water K max(I, O0) [m3] are finite: below, the weights round to fewer digits or those of the inflow underflow and the water that enters is lost; above, the weights are NaN | IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, smallest normal 2.2e-308, the ratio of the step to K / N in the weights, K in seconds in their denominator and the storage K max(I, O0) |
| `nonnegative_weights` | precondition | 2 K X / N <= dt <= 2 K (1 - X) / N, each end to 1e-9 of itself: every weight is non-negative, so a non-negative inflow gives a non-negative outflow | the signs of the numerators of the weights (Hydrolog ADR-0008); Ponce's form \|C - D\| <= 1 <= C + D, c_current >= 0 iff dt >= 2KX/N, c_previous >= 0 iff dt >= -2KX/N, c_outflow >= 0 iff dt <= 2K(1 - X)/N |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `outflow_m3s` | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | 4 ulp of the bound |
| `c_current` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `c_previous` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `c_outflow` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `storage_start_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_end_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_steady_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: discharge in m3/s, time in min, storage in m3 (K in min times a discharge in m3/s times the 60 s of a minute of the units table)
- the weights are named by what they multiply: c_current I[t], c_previous I[t-1], c_outflow O[t-1]; NEH 630 and HEC-HMS call them C2, C1 and C3, the Iowa and NPTEL examples C1, C2 and C3
- continuity by the trapezoid rule, (S[t] - S[t-1]) / dt = (I[t] + I[t-1]) / 2 - (O[t] + O[t-1]) / 2, with S = k [X I + (1 - X) O] in each sub-reach
- N equal sub-reaches of K / N in series with the same X (HEC-HMS); every sub-reach starts at rest with O0, so at the first ordinate all but the first are fed by O0
- within the window's slack a weight that rounding puts below zero is set to zero and the others are divided by their sum (hydrolog.routing._kernels.nonnegative_coefficients)
- only the given ordinates are routed: MuskingumReach chooses N (K / dt rounded) and the sub-steps of a step without a window, interpolates the inflow linearly between them, and extends the time axis (Tier B, ADR-0008)

**Assumptions**

- the storage of the reach is linear in a weighted discharge, S = K [X I + (1 - X) O], with K and X constant over the flood
- no backwater: the outflow does not depend on the water downstream

**Validation:** none: K and X are calibrated on observed floods of a reach (HEC-HMS TRM, Muskingum model; EM 1110-2-1417 ch. 9); the sources report no agreement of the scheme itself with observations

**Notices:** `outside_applicability`

**Numerical traps (CMP-6.6)**

- `difference_denominator`: c_current = (dt - 2KX/N) / D vanishes on the window's lower end: limit lag_of_one_step gives it exactly 0; D = 2K(1 - X)/N + dt >= dt > 0 never vanishes
- `stability_bound`: the window 2KX/N <= dt <= 2K(1 - X)/N: constraint nonnegative_weights with its satisfied, boundary and violated points, and test_a_border_of_the_window_rounds_to_zero_weights
- `gap_propagation`: type cases inflow_m3s-nan_element and inflow_m3s-inf_element: a gap is refused, the recurrence would carry it to every later ordinate
- `many_small_terms`: test_a_long_steady_inflow_stays_steady: 200,000 ordinates of a constant inflow stay constant to 1e-14

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `inflow_m3s` increasing, `initial_outflow_m3s` increasing
- scaling `discharge`: inputs times 2^e (`inflow_m3s` e = 1.0, `initial_outflow_m3s` e = 1.0) give outputs times 2^e (`outflow_m3s` e = 1.0, `storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- scaling `time`: inputs times 2^e (`timestep_min` e = 1.0, `k_min` e = 1.0) give outputs times 2^e (`storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- limit `lag_of_one_step`: X = 0.5 and K = N dt with N = 1: c0 = c2 = 0 and c1 = 1, the outflow is the inflow one step later (HEC-HMS: Muskingum with X = 0.5 and K = dt is the lag of one step)
- limit `steady_state`: an inflow equal to the initial outflow passes unchanged: the weights sum to 1
- limit `exact_recurrence`: every outflow equals the recurrence of the sub-reaches in exact rational arithmetic
- limit `moments`: the impulse response has the mean delay K and the variance K^2 (1 - 2X) / N, whatever dt
- limit `bounded_by_its_inputs`: every outflow lies between the least and the largest of the inflow and the initial outflow
- conservation `volume`: the trapezoid continuity holds in every sub-reach: inflow volume - outflow volume = storage at the end - storage at the start

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/muskingum-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the recurrence of the sub-reaches and its weights in exact rational arithmetic (fractions), loop by loop (`tests/unit/test_formulas_muskingum.py (limit exact_recurrence)`)
- exact: the moments of the impulse response, mean K and variance K^2 (1 - 2X) / N, from the generating function (c0 + c1 s) / (1 - c2 s) of the scheme (`tests/unit/test_formulas_muskingum.py (limit moments)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="linear_reservoir_cascade"></a>
### Cascade of n equal linear reservoirs, exact for an inflow linear between the ordinates (Nash)

`hydrolog.routing.formulas.cascade.cascade_route` · family `scheme` · formula_version 1 · status **oracle only** · mutation score not measured

$$
O(t) = O_0\,Q\!\left(n, \tfrac{t}{K}\right) + \int_0^t u(t-s)\,I(s)\,ds,\quad u(t) = \frac{1}{K\,\Gamma(n)}\left(\frac{t}{K}\right)^{n-1}e^{-t/K},\quad h_m = -\frac{V((m+1)a) - 2V(ma) + V((m-1)a)}{a},\ V(x) = x\,Q(n, x) + n\,P(n+1, x),\ a = \frac{\Delta t}{K}
$$

Plain text: `O(t) = O0 Q(n, t/K) + integral from 0 to t of u(t - s) I(s) ds, u(t) = (t/K)^(n-1) exp(-t/K) / (K Gamma(n)), I linear between the ordinates; at the ordinates O[j] = O0 (1 - P(n, x_j)) + I[0] (P(n, x_j) - (1 - (V(x_j) - V(x_(j-1))) / a)) + sum_(m < j) h_m I[j-m], x_j = j a, a = dt / K, V(x) = x Q(n, x) + n P(n+1, x), h_0 = 1 - V(a) / a, h_m = -(V((m+1)a) - 2 V(m a) + V((m-1)a)) / a; storage at the end K [sum over the segments of the water not yet released + O0 (n - V(x_N))] [m3]`

**Sources**

- Nash, J.E. (1957). The form of the instantaneous unit hydrograph, IAHS Publication 45, 114-121, the cascade of n equal linear reservoirs and its gamma impulse response (author-provided)
- Ponce, V.M. (online). Linear reservoirs and numerical diffusion, San Diego State University, the Nash cascade and the Kalinin-Milyukov method: n reservoirs of S = K O in series, impulse response of mean n K (open) <https://ponce.sdsu.edu/linear_reservoirs_and_numerical_diffusion.html>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `inflow_m3s` | $I_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a series of daily discharges (IMGW-PIB)) | unstated | [5.0, 720.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d) |
| `n` | $n$ | - | real | (0.0, inf), test bound high 1000000.0 (the cascade of a million reservoirs of the tests of the reach, whose delay outlasts the series (test_a_reach_that_holds_the_water_longer_than_the_series_keeps_the_start)) | unstated | [1.0, 8.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), n of 1 to 8 in tests/unit/test_routing_cascade.py and 2.5 in docs/USAGE.md (route cascade) |
| `k_min` | $K$ | min | real | (0.0, inf), test bound high 12000.0 (ten times the longest storage constant of Hydrolog's routing tests, the Iowa example's 20 h (1,200 min)) | unstated | [5.0, 80.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), K of 5 to 40 min in tests/unit/test_routing_cascade.py and 80 min in docs/USAGE.md (route cascade) |
| `initial_outflow_m3s` | $O_0$ | m3/s | real | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `representable` | precondition | n >= 2.2e-308, 0 < dt / K, and the grid of N dt / K, the largest discharge over dt / K and the storage n K max(I, O0) are finite in float64 | IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, smallest normal 2.2e-308; SciPy's scipy.special.gammainc and gammaincc (1.18.1) give P(a, x) = 0 and Q(a, x) <= 0 for a subnormal shape a, x = m dt / K on the grid of the ordinates, the inflow over dt / K, the storage n K I, and n as the shape of P and Q |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `outflow_m3s` | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | 4 ulp of the bound |
| `storage_start_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_end_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_steady_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: discharge in m3/s, time in min, storage in m3 (K in min times a discharge in m3/s times the 60 s of a minute of the units table)
- the inflow is linear between the ordinates and equal to the initial outflow before the first one: every reservoir starts at rest with O0, and the inflow jumps to I[0] at the first ordinate
- the outflow at an ordinate is the exact response to that inflow, not a trapezoid or Euler step; between the ordinates it is not linear, so the trapezoid volume of the outflow differs from its integral
- a weight that rounding puts below zero is set to zero, and so are a remainder n - V and an outflow that rounding puts below zero
- n need not be whole: Gamma(n) and P(n, x) of SciPy's gammainc and gammaincc
- only the given ordinates are routed: CascadeReach takes K or K = L / (n c) from the length and the celerity of a reach, and extends the time axis (Tier B, ADR-0008)

**Assumptions**

- each reservoir is linear, S = K O, with K constant over the flood
- no backwater: the outflow does not depend on the water downstream

**Validation:** none: n and K are calibrated on observed floods or follow from the reach (Kalinin-Milyukov); the sources report no agreement of the cascade itself with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: the weights divide second differences of V by dt / K, which underflows for a step far shorter than K: precondition representable refuses dt / K = 0, an inflow over it that overflows and a subnormal n, for which SciPy's P and Q fail (test_a_step_ratio_beyond_float64_is_refused, test_a_subnormal_number_of_reservoirs_is_refused)
- `gap_propagation`: type cases inflow_m3s-nan_element and inflow_m3s-inf_element: a gap is refused, the convolution would carry it to every later ordinate
- `many_small_terms`: test_a_long_steady_inflow_stays_steady: 200,000 ordinates of a steady inflow, convolved by the FFT, stay steady to 1e-12

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `inflow_m3s` increasing, `initial_outflow_m3s` increasing
- scaling `discharge`: inputs times 2^e (`inflow_m3s` e = 1.0, `initial_outflow_m3s` e = 1.0) give outputs times 2^e (`outflow_m3s` e = 1.0, `storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- scaling `time`: inputs times 2^e (`timestep_min` e = 1.0, `k_min` e = 1.0) give outputs times 2^e (`storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- limit `steady_state`: an inflow equal to the initial outflow passes unchanged: the weights add up to one
- limit `step_response`: a steady inflow into a cascade at rest at another outflow gives O0 + (I - O0) P(n, t / K), the gamma distribution function
- limit `matrix_exponential`: for whole n the outflow and the storage equal the exact solution of the linear ODEs of the chain of reservoirs
- limit `moments`: the response to a unit hat has the mass one and the mean delay n K exactly, and the variance n K^2 + dt^2 / 6
- limit `bounded_by_its_inputs`: every outflow lies between the least and the largest of the inflow and the initial outflow
- conservation `volume`: inflow volume - outflow volume - (storage at the end - storage at the start) lies within the error of the trapezoid rule on the outflow, (|I[0] - O0| / 2 + max |I[t] - I[t-1]| / 4) dt

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- established: the step response P(n, t / K) of SciPy's scipy.special.gammainc (regularised lower incomplete gamma function) (`tests/unit/test_formulas_cascade.py (limit step_response)`)
- algorithm: for whole n, the linear ODEs of the chain solved over each step by the matrix exponential (scipy.linalg.expm), exact for an inflow linear over the step (`tests/unit/test_formulas_cascade.py (limit matrix_exponential)`)
- exact: the moments of the impulse response, mean n K and variance n K^2, of the gamma density (`tests/unit/test_formulas_cascade.py (limit moments)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="lag"></a>
### Lag routing: the inflow translated by a fixed time, linear between the ordinates

`hydrolog.routing.formulas.lag.lag_route` · family `scheme` · formula_version 1 · status **oracle only** · mutation score not measured

$$
O(t) = I(t - \tau),\quad O_j = (1 - f)\,I_{j-w} + f\,I_{j-w-1},\ \frac{\tau}{\Delta t} = w + f,\ 0 \le f < 1,\quad S(t) = \int_{t-\tau}^{t} I(s)\,ds
$$

Plain text: `O(t) = I(t - lag), I = O0 before the first ordinate; with lag / dt = w + f, 0 <= f < 1: O[j] = (1 - f) I[j - w] + f I[j - w - 1]; storage at the start lag O0, at the end the integral of I over the last lag minutes, at rest lag I[-1] [m3]`

**Sources**

- US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Lag Model, eq. 1: O_t = I_(t - lag) for t >= lag and O_t = I_t before; the lag suits short reaches with a predictable travel time (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/lag-model>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `inflow_m3s` | $I_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a series of daily discharges (IMGW-PIB)) | unstated | [5.0, 720.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d) |
| `lag_min` | $\tau$ | min | real | (0.0, inf), test bound high 50000.0 (ten times the longest lag of the tests of the lag, 5,000 min, a lag beyond the cap of the extension) | unstated | [5.0, 60.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), lags of 5 to 30 min in tests/unit/test_routing_core.py and of 10 to 60 min in docs/USAGE.md (route lag, networks) |
| `initial_outflow_m3s` | $O_0$ | m3/s | real | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `representable` | precondition | lag / dt and the water in transit lag max(I, O0) are finite in float64 | IEEE 754 binary64, the float64 of NumPy: largest finite number 1.8e308, the lag over the step, and the water in transit lag max(I, O0) |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `outflow_m3s` | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | 4 ulp of the bound |
| `storage_start_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_end_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_steady_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `lag_steps` | - | real | [0.0, inf) | 4 ulp of the bound |
| `lag_fraction` | - | real | [0.0, 1.0) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: discharge in m3/s, time in min, storage in m3 (a lag in min times a discharge in m3/s times the 60 s of a minute of the units table)
- before the first ordinate the inflow is the initial outflow (the reach at rest, ADR-0008); HEC-HMS TRM Lag model eq. 1 writes O_t = I_t for t < lag instead
- a lag that is not a whole number of steps interpolates the inflow linearly between the two ordinates around t - lag, which flattens sharp peaks; one step before the first ordinate the inflow is O0, so the outflow ordinates follow an inflow that rises linearly from O0 to I[0] over that step, while the storages hold O0 up to the first ordinate
- a lag within 1e-9 steps of a whole number counts as whole (LAG_ROUNDING); the storages keep the lag as given
- only the given ordinates are routed: LagReach extends the time axis by the lag (Tier B, ADR-0008) and adds the notice lag_interpolated for a lag that is not a whole number of steps

**Assumptions**

- the reach translates the wave without attenuation, its travel time constant over the flood
- no backwater: the outflow does not depend on the water downstream

**Validation:** none: the lag is the travel time of a reach, set from its length and the celerity or calibrated (HEC-HMS TRM, Lag model); the source reports no agreement with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `gap_propagation`: type cases inflow_m3s-nan_element and inflow_m3s-inf_element: a gap is refused, the shift would carry it lag minutes later
- `many_small_terms`: test_a_long_transit_volume_sums_exactly: the transit volume of a lag of 100,000 steps against math.fsum of the same trapezoids

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `inflow_m3s` increasing, `initial_outflow_m3s` increasing
- scaling `discharge`: inputs times 2^e (`inflow_m3s` e = 1.0, `initial_outflow_m3s` e = 1.0) give outputs times 2^e (`outflow_m3s` e = 1.0, `storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- scaling `time`: inputs times 2^e (`timestep_min` e = 1.0, `lag_min` e = 1.0) give outputs times 2^e (`storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- limit `whole_step_shift`: a lag of two steps copies each inflow ordinate two ordinates later, the initial outflow before
- limit `half_step_interpolation`: a lag of two and a half steps averages the inflow two and three steps earlier (Hydrolog's catalog example of route lag)
- limit `steady_state`: an inflow equal to the initial outflow passes unchanged
- limit `muskingum_one_step`: a lag of one step equals the Muskingum scheme with X = 0.5 and K = dt in one sub-reach (HEC-HMS)
- limit `convex_shifts`: a lag of w + f steps is (1 - f) times the shift by w steps plus f times the shift by w + 1
- conservation `volume`: inflow volume - outflow volume - (storage at the end - storage at the start) = J (u_end - u_end^2 / (2 dt)) - J (u - u^2 / (2 dt)) - f (1 - f) dt (slope change across the window) / 2, J = I[0] - O0, u = min(lag, dt), u_end = min(lag - T, dt) for a lag beyond the series T: exact for a whole number of steps and I[0] = O0

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the Muskingum scheme with X = 0.5 and K = dt in one sub-reach (hydrolog.routing.formulas.muskingum.muskingum_route, spec muskingum), the lag of one step (`tests/unit/test_formulas_lag.py (limit muskingum_one_step)`)
- exact: the shift by a whole number of steps, and a fractional lag as the convex combination of the two shifts around it (`tests/unit/test_formulas_lag.py (limits whole_step_shift, half_step_interpolation, convex_shifts)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="manning_normal_flow"></a>
### Normal flow of a trapezoidal, rectangular or triangular channel by Manning's equation, with the kinematic celerity dQ/dA

`hydrolog.routing.formulas.manning.normal_flow` · family `empirical` · formula_version 1 · status **referenced** · mutation score not measured

$$
Q = \frac{1}{n} A R^{2/3} S^{1/2},\quad A = (b + z y) y,\ P = b + 2 y \sqrt{1 + z^2},\ R = \frac{A}{P};\quad T = b + 2 z y,\ V = \frac{Q}{A},\ c = \frac{dQ}{dA} = V \left(\frac{5}{3} - \frac{2}{3} \frac{A P'}{T P}\right)
$$

Plain text: `Q = A R^(2/3) S^(1/2) / n, A = (b + z y) y, P = b + 2 y (1 + z^2)^(1/2), R = A / P; T = b + 2 z y; V = Q / A; c = dQ/dA = V (5/3 - 2/3 A P' / (T P)), P' = 2 (1 + z^2)^(1/2); the normal depth y is the root of the first equation`

**Sources**

- Arcement, G.J. and Schneider, V.R. (1989). Guide for selecting Manning's roughness coefficients for natural channels and flood plains, US Geological Survey Water-Supply Paper 2339, Introduction, eqs. 1 and 2 (the first page of the text): V = 1.486/n R^(2/3) Se^(1/2) and the conveyance K = 1.486/n A R^(2/3), in feet (open) <https://pubs.usgs.gov/wsp/2339/report.pdf>
- US Army Corps of Engineers, Hydrologic Engineering Center. Water Surface Profile Calculations with HEC-RAS (training lesson 1.6, PROSPECT course), slides 'Cross Section Subdivision for Conveyance Calculations' (Q = 1.486/n A R^(2/3) Sf^(1/2), in feet) and 'Computational Procedure: Tolerances and trials' (water surface calculation tolerance 0.01 ft by default) (open) <https://www.hec.usace.army.mil/confluence/prospect/files/124452884/124453107/1/1669663021202/1.6+L+-+Water+Surface+Profile+Calculations.pdf>
- US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum-Cunge Model, eq. 4, the flood wave celerity c = dQ/dA; Required Parameters: the reach's Manning's n and a rectangle, trapezoid or triangle by its bottom width and side slope (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-cunge-model>
- USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-24 and 17-25, c = dQ/dA = m Q / A, and 17-29 and 17-30a, the weighted m of a rating table; Table 17-16 and example 17-4, pp. 17-36 to 17-43 (open) <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
- Manning, R. (1891). On the flow of water in open channels and pipes, Transactions of the Institution of Civil Engineers of Ireland 20, 161-207 (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `discharge_m3s` | $Q$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included) | unstated | [1.0, 300.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), reference discharges of 0.95 to 300.05 m3/s in the tests of the reach (tests/unit/test_routing_cunge.py), 12 m3/s in tests/fixtures/network_flood.json; NEH 630 examples 17-4 and 17-5, 684.18 and 3,385.4 ft3/s (19.4 and 95.9 m3/s) |
| `slope_m_per_m` | $S$ | m/m | real | (0.0, inf), test bound high 0.2 (ten times the steepest reach of the project's data, 0.02 in Hydrograf's network tests/fixtures/handoff_hydrograf_network.json) | unstated | [0.0002, 0.02]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.0002 to 0.002778 in the tests of the reach (tests/unit/test_routing_cunge.py), 0.00208 to 0.009859 on the reaches of Hydrograf's Nysa Szalona network from the DEM (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json), 0.02 in tests/fixtures/handoff_hydrograf_network.json; 0.00091 in NEH 630 examples 17-4 and 17-5 |
| `bottom_width_m` | $b$ | m | real | [0.0, inf), test bound high 50000.0 (ten times the widest section of the tests, the 5,000 m rectangle of tests/unit/test_routing_sections.py) | unstated | [0.0, 30.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0 (a triangle) to 30 m in the tests of the section (tests/unit/test_routing_sections.py), 5 to 15 m in the tests of the reach, 8 m in tests/fixtures/network_flood.json; NEH 630 example 17-4, 15 ft (4.57 m) |
| `side_slope_m_per_m` | $z$ | m/m | real | [0.0, inf), test bound high 20.0 (ten times the gentlest banks of the tests, NEH's 2:1) | unstated | [0.0, 2.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0 (a rectangle) to 2 (2:1 banks) in the tests of the section and of the reach, 2 in tests/fixtures/network_flood.json and NEH 630 example 17-4 |
| `manning_n` | $n$ | s/m^(1/3) | real | (0.0, inf), test bound high 1.0 (ten times the roughest channel of the tests, n = 0.1 in tests/unit/test_routing_sections.py) | unstated | [0.03, 0.05]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.03 to 0.05 in the tests of the section and of the reach, 0.035 in docs/USAGE.md and tests/fixtures/network_flood.json; NEH 630 example 17-4, 0.04 |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `has_width` | physical | b + z > 0: a section with a bottom or banks; neither holds no water | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum-Cunge Model, eq. 4, the flood wave celerity c = dQ/dA; Required Parameters: the reach's Manning's n and a rectangle, trapezoid or triangle by its bottom width and side slope |
| `representable_flow` | precondition | 2.2e-308 <= y, A, T, V, c < inf: float64 holds the normal flow to sixteen digits; a section so narrow, flat or rough, or a discharge so large or small, that one of them overflows or falls among the subnormal floats has none | IEEE 754-2019, binary64: normal numbers of magnitude about 2.2e-308 to 1.8e308, with 53 significant bits; below them the subnormal numbers keep fewer, the depth, the area, the top width, the velocity and the celerity of a flow must be normal numbers to hold their sixteen digits |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `radius_exponent` | $2/3$ | 2/3 | - | Arcement, G.J. and Schneider, V.R. (1989). Guide for selecting Manning's roughness coefficients for natural channels and flood plains, US Geological Survey Water-Supply Paper 2339, Introduction, eqs. 1 and 2 (the first page of the text): V = 1.486/n R^(2/3) Se^(1/2) and the conveyance K = 1.486/n A R^(2/3), in feet |
| `slope_exponent` | $1/2$ | 1/2 | - | Arcement, G.J. and Schneider, V.R. (1989). Guide for selecting Manning's roughness coefficients for natural channels and flood plains, US Geological Survey Water-Supply Paper 2339, Introduction, eqs. 1 and 2 (the first page of the text): V = 1.486/n R^(2/3) Se^(1/2) and the conveyance K = 1.486/n A R^(2/3), in feet |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `depth_m` | m | real | (0.0, inf) | 4 ulp of the bound |
| `area_m2` | m2 | real | (0.0, inf) | 4 ulp of the bound |
| `top_width_m` | m | real | (0.0, inf) | 4 ulp of the bound |
| `velocity_m_per_s` | m/s | real | (0.0, inf) | 4 ulp of the bound |
| `celerity_m_per_s` | m/s | real | (0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: Q in m3/s, lengths in m, n in s/m^(1/3); the US customary form multiplies by 1.486, the cube root of the feet in a metre (1.4859) rounded, as HEC-RAS does (USGS WSP 2339 eq. 1)
- the bed slope is the friction slope: the flow is uniform
- the celerity is the local kinematic celerity dQ/dA at the depth (HEC-HMS eq. 4; NEH eq. 17-25 with m = d ln Q / d ln A); NEH's example 17-4 takes a discharge-weighted m of the rating from zero to Q (eqs. 17-29, 17-30a), 2 % above the local one (case mc_neh17_example17_4_from_section)
- one roughness for the whole wetted perimeter; a trapezoid with both banks at z:1, a rectangle at z = 0 and a triangle at b = 0; no floodplain
- the normal depth is found by Brent's method in ln y (scipy.optimize.brentq, delegated, CMP-1.2) in a bracket from the slope of ln K in ln y, between 1 and 10/3, to four units of 1e-16 of max(1, |ln y|)

**Assumptions**

- steady uniform flow: the depth is the normal depth of the discharge
- a prismatic channel whose n does not change with the depth
- the flow stays within the section, which has no top

**Validation:** none: the sources give Manning's equation as the practice of uniform open channel flow and report no agreement of their own with observations; n is chosen from tables or calibrated (USGS WSP 2339)

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: ln b and ln z of a triangle (b = 0) and of a rectangle (z = 0) are minus infinity, which logaddexp takes: range cases bottom_width_m-physical_low and side_slope_m_per_m-physical_low give finite flows; ln Q and S^(1/2) at their open lower ends: range cases discharge_m3s-physical_low_inside and slope_m_per_m-physical_low_inside, a finite flow or the precondition representable_flow
- `exp_overflow`: y = e^u beyond the largest float: the violated point of representable_flow and test_a_depth_beyond_a_float_is_refused; the range cases at the test bounds give finite flows

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `discharge_m3s` increasing, `slope_m_per_m` decreasing, `manning_n` increasing
- scaling `length`: inputs times 2^e (`discharge_m3s` e = 9.0, `bottom_width_m` e = 3.0, `manning_n` e = -1.0) give outputs times 2^e (`depth_m` e = 3.0, `area_m2` e = 6.0, `top_width_m` e = 3.0, `velocity_m_per_s` e = 3.0, `celerity_m_per_s` e = 3.0)
- scaling `time`: inputs times 2^e (`discharge_m3s` e = -1.0, `manning_n` e = 1.0) give outputs times 2^e (`velocity_m_per_s` e = -1.0, `celerity_m_per_s` e = -1.0)
- scaling `slope`: inputs times 2^e (`discharge_m3s` e = 1.0, `slope_m_per_m` e = 2.0) give outputs times 2^e (`velocity_m_per_s` e = 1.0, `celerity_m_per_s` e = 1.0)
- limit `rectangle_by_hand`: b = 2 m, z = 0, n = 0.03, S = 0.001 and Q = 2 (1/2)^(2/3) 0.001^(1/2) / 0.03: A = 2, P = 4, R = 1/2, so y = 1 m
- limit `triangle_closed_form`: a triangle (b = 0) has the closed form y = (Q n P'^(2/3) / (S^(1/2) z^(5/3)))^(3/8) and c = 4/3 V
- limit `kinematic_celerity_bounds`: V <= c <= 5/3 V: the celerity of a trapezoid lies between that of a deep narrow rectangle and that of a wide one
- limit `decimal_oracle`: the depth and dQ/dA equal Manning's equation written as S^(1/2) / n (A^5 / P^2)^(1/3), solved by bisection and differenced at 50 digits

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/muskingum-cunge-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the closed form of a triangle, y = (Q n P'^(2/3) / (S^(1/2) z^(5/3)))^(3/8), and its c = 4/3 V (`tests/unit/test_formulas_muskingum_cunge.py (limit triangle_closed_form)`)
- algorithm: Manning's equation written as S^(1/2) / n (A^5 / P^2)^(1/3) in decimal arithmetic at 50 digits, its depth by bisection and dQ/dA by a central difference (`tests/unit/test_formulas_muskingum_cunge.py (limit decimal_oracle)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="muskingum_cunge"></a>
### Muskingum-Cunge routing with constant coefficients on N equal distance steps (Cunge's K and X)

`hydrolog.routing.formulas.cunge.muskingum_cunge_route` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
D = \frac{Q}{T S_0 c},\ \Delta x = \frac{L}{N},\ K = \frac{\Delta x}{c},\ X = \frac{1}{2}\left(1 - \frac{D}{\Delta x}\right);\quad O_t = c_0 I_t + c_1 I_{t-1} + c_2 O_{t-1};\quad C_g = \frac{c \Delta t}{\Delta x},\ D_g = \frac{D}{\Delta x} = 1 - 2X
$$

Plain text: `D = Q / (T S0 c), dx = L / N, K = dx / c, X = (1 - D / dx) / 2; in each of N distance steps in series O[t] = c0 I[t] + c1 I[t-1] + c2 O[t-1] with the Muskingum weights of K, X and dt; Cg = c dt / dx, Dg = D / dx = 1 - 2X and NEH's accuracy limit exp(2.3 Cg)`

**Sources**

- USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-20 to 17-22 (X, the distance step, K) and 17-31 to 17-36 (Cg, Dg and the accuracy limit, eq. 17-36 on p. 17-33); examples 17-4 and 17-5, pp. 17-36 to 17-51 (open) <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
- US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum-Cunge Model, eqs. 3 to 5 (the convective diffusion equation, c = dQ/dA, mu = Q / (2 B S0)), 6 to 10 (the weights) and 12 and 13 (K = dx / c, X = (1 - Q / (B S0 c dx)) / 2) (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/muskingum-cunge-model>
- US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, eq. 9-22 and the reference flow, p. 9-21 (open) <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>
- Cunge, J.A. (1969). On the subject of a flood propagation computation method (Muskingum method), Journal of Hydraulic Research 7(2), 205-230 (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `inflow_m3s` | $I_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a series of daily discharges (IMGW-PIB)) | unstated | [5.0, 720.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d) |
| `length_km` | $L$ | km | real | (0.0, inf), test bound high 234.0 (ten times the longest reach of the project's data, 23.36 km on Hydrograf's Nysa Szalona network) | unstated | [0.1, 23.4]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.1 to 20 km in the tests of the reach (tests/unit/test_routing_cunge.py), 1.3 to 23.4 km on Hydrograf's Nysa Szalona network besides a 7 m connector (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json); NEH 630 examples 17-4 and 17-5, 2,600 ft (0.79 km) |
| `slope_m_per_m` | $S_0$ | m/m | real | (0.0, inf), test bound high 0.2 (ten times the steepest reach of the project's data, 0.02 in Hydrograf's network tests/fixtures/handoff_hydrograf_network.json) | unstated | [0.0002, 0.02]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.0002 to 0.002778 in the tests of the reach (tests/unit/test_routing_cunge.py), 0.00208 to 0.009859 on the reaches of Hydrograf's Nysa Szalona network from the DEM (tests/fixtures/handoff_hydrograf_network_nysa_szalona.json), 0.02 in tests/fixtures/handoff_hydrograf_network.json; 0.00091 in NEH 630 examples 17-4 and 17-5 |
| `celerity_m_per_s` | $c$ | m/s | real | (0.0, inf), test bound high 50.0 (ten times the fastest wave of the tests, 5 m/s) | unstated | [0.2, 5.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 0.2 to 5 m/s in the tests of the reach (tests/unit/test_routing_cunge.py); NEH 630 examples 17-4 and 17-5, 4.297 and 1.779 ft/s (1.31 and 0.54 m/s) |
| `top_width_m` | $T$ | m | real | (0.0, inf), test bound high 2250.0 (ten times the widest water surface of the tests and examples, 738.3 ft (225 m) in NEH 630 example 17-5) | unstated | [10.0, 225.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 10 to 200 m in the tests of the reach and of the networks (tests/unit/test_routing_cunge.py, tests/unit/test_operations_route_network.py); NEH 630 examples 17-4 and 17-5, 44.6 and 738.3 ft (13.6 and 225 m) |
| `reference_discharge_m3s` | $Q$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included) | unstated | [1.0, 300.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), reference discharges of 0.95 to 300.05 m3/s in the tests of the reach (tests/unit/test_routing_cunge.py), 12 m3/s in tests/fixtures/network_flood.json; NEH 630 examples 17-4 and 17-5, 684.18 and 3,385.4 ft3/s (19.4 and 95.9 m3/s) |
| `subreaches` | $N$ | - | integer | [1.0, inf), test bound high 1000.0 (the test bound of the length, 234 km, in steps of 234 m, half of what the wave of NEH 630 example 17-4 (4.297 ft/s) travels in its step of 0.1 h) | unstated | [1.0, 4.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 to 4 distance steps in the tests of the reach (tests/unit/test_routing_cunge.py); 1 and 2 in NEH 630 examples 17-4 and 17-5 |
| `initial_outflow_m3s` | $O_0$ | m3/s | real | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `nonnegative_weights` | precondition | \|c dt - D\| <= L / N <= c dt + D with D = Q / (T S0 c), each end to 1e-9 of itself: every weight is non-negative, so a non-negative inflow gives a non-negative outflow | the signs of the numerators of the weights (Hydrolog ADR-0008); Ponce's form \|C - D\| <= 1 <= C + D, c_current >= 0 iff dx <= c dt + D, c_previous >= 0 iff dx >= D - c dt, c_outflow >= 0 iff dx >= c dt - D |
| `finite_grid` | precondition | L / c, c dt / dx, D / dx and N K (1 + 2\|X\|) max(I, O0) are finite: float64 holds the grid and the water it can hold; a wave so slow, a step so short or a flood so large that one overflows has none | IEEE 754-2019, binary64: finite numbers of magnitude about 4.9e-324 to 1.8e308, the grid's scalars and the water it holds must be among them; exp(700), about 1.0e304, is one |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `accuracy_factor` | $2.3$ | 2.3 | - | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-20 to 17-22 (X, the distance step, K) and 17-31 to 17-36 (Cg, Dg and the accuracy limit, eq. 17-36 on p. 17-33); examples 17-4 and 17-5, pp. 17-36 to 17-51 |
| `limit_exponent_cap` |  | 700.0 | - | IEEE 754-2019, binary64: finite numbers of magnitude about 4.9e-324 to 1.8e308, the grid's scalars and the water it holds must be among them; exp(700), about 1.0e304, is one |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `outflow_m3s` | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | 4 ulp of the bound |
| `k_min` | min | real | (0.0, inf) | 4 ulp of the bound |
| `x` | - | real | (-inf, 0.5] | 4 ulp of the bound |
| `c_current` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `c_previous` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `c_outflow` | - | real | [0.0, 1.0] | 4 ulp of the bound |
| `dx_m` | m | real | (0.0, inf) | 4 ulp of the bound |
| `courant_number` | - | real | (0.0, inf) | 4 ulp of the bound |
| `grid_reynolds_number` | - | real | (0.0, inf) | 4 ulp of the bound |
| `grid_reynolds_limit` | - | real | [1.0, inf) | 4 ulp of the bound |
| `storage_start_m3` | m3 | real | (-inf, inf) | 4 ulp of the bound |
| `storage_end_m3` | m3 | real | (-inf, inf) | 4 ulp of the bound |
| `storage_steady_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: discharge in m3/s, time in min, the reach in km, the distance step and the diffusion length in m, the celerity in m/s, storage in m3
- the weights are named by what they multiply: c_current I[t], c_previous I[t-1], c_outflow O[t-1]; NEH 630 and HEC-HMS call them C2, C1 and C3
- one reference discharge, celerity and top width for every distance and time step, so the coefficients are constant: NRCS's WinTR-20 takes the peak at the upstream end of each distance step (NEH 630 example 17-5) and HEC-HMS recomputes the coefficients at every time and distance step (a variable-coefficient method, Ponce 1986): case mc_neh17_example17_5_reach
- X may be negative (NEH 630 example 17-4, X = -0.254); a grid with a negative weight, which NEH accepts (example 17-5, C1 = -0.187), is refused by the precondition nonnegative_weights (Hydrolog ADR-0008)
- within the window's slack a weight that rounding puts below zero is set to zero and the others are divided by their sum (hydrolog.routing._kernels.nonnegative_coefficients)
- Dg is computed as D / dx (NEH eq. 17-34), equal to 1 - 2X (eq. 17-35) to rounding; the accuracy limit exp(2.3 Cg) is capped at exp(700), above every Dg <= 1 + Cg of the window
- no lateral inflow: the term C4 q dx of HEC-HMS eq. 7 is zero
- only the given grid is routed: MuskingumCungeReach takes the inflow peak as the reference unless one is given, chooses N and the sub-steps of a step by NEH 630's rules inside the window, interpolates the inflow linearly between them and falls back to linear reservoirs where no grid exists (Tier B, ADR-0008, ADR-0026)

**Assumptions**

- the diffusion wave: the inertia terms of the momentum equation are neglected, and the convective diffusion equation is linearised at the reference discharge with c and mu = Q / (2 T S0) constant (HEC-HMS eqs. 1 to 5)
- a prismatic reach of one slope; no backwater

**Validation:** none: the sources compare the scheme with unsteady flow models, not with observations (NEH 630 examples 17-4 and 17-5 against HEC-RAS: peaks within 0.2 and 2.5 %); NRCS fitted its accuracy limit to 140 test routings (NEH 630 appendix 17B)

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: the window's top L / |c dt - D| divides by a difference: when the wave travels exactly its diffusion length in a step it has no top (test_a_wave_as_long_as_its_diffusion_length_has_no_top); the weights' 1 + Cg + Dg never vanishes
- `stability_bound`: the window |c dt - D| <= dx <= c dt + D: constraint nonnegative_weights with its satisfied, boundary and violated points, and test_a_border_of_the_window_rounds_to_zero_weights
- `gap_propagation`: type cases inflow_m3s-nan_element and inflow_m3s-inf_element: a gap is refused, the recurrence would carry it to every later ordinate
- `many_small_terms`: test_a_long_steady_inflow_stays_steady: 200,000 ordinates of a constant inflow stay constant to 1e-14

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `inflow_m3s` increasing, `initial_outflow_m3s` increasing
- scaling `discharge`: inputs times 2^e (`inflow_m3s` e = 1.0, `initial_outflow_m3s` e = 1.0) give outputs times 2^e (`outflow_m3s` e = 1.0, `storage_start_m3` e = 1.0, `storage_end_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- scaling `time`: inputs times 2^e (`inflow_m3s` e = -1.0, `timestep_min` e = 1.0, `celerity_m_per_s` e = -1.0, `reference_discharge_m3s` e = -1.0, `initial_outflow_m3s` e = -1.0) give outputs times 2^e (`outflow_m3s` e = -1.0, `k_min` e = 1.0)
- scaling `length`: inputs times 2^e (`inflow_m3s` e = 3.0, `length_km` e = 1.0, `celerity_m_per_s` e = 1.0, `top_width_m` e = 1.0, `reference_discharge_m3s` e = 3.0, `initial_outflow_m3s` e = 3.0) give outputs times 2^e (`outflow_m3s` e = 3.0, `dx_m` e = 1.0, `storage_start_m3` e = 3.0, `storage_end_m3` e = 3.0, `storage_steady_m3` e = 3.0)
- scaling `discharge_per_width`: inputs times 2^e (`top_width_m` e = 1.0, `reference_discharge_m3s` e = 1.0) give outputs times 2^e (none)
- limit `steady_state`: an inflow equal to the initial outflow passes unchanged: the weights sum to 1
- limit `exact_recurrence`: the grid and every outflow equal Ponce's form of the weights, (C + D - 1, 1 + C - D, 1 - C + D) / (1 + C + D), and the recurrence in exact rational arithmetic
- limit `moments`: the impulse response has the moments of the diffusion wave, the mean L / c and the variance 2 mu L / c^3 = D L / c^2, whatever dt and N
- limit `bounded_by_its_inputs`: every outflow lies between the least and the largest of the inflow and the initial outflow
- limit `inside_the_accuracy_limit`: on every grid the window accepts Dg <= exp(2.3 Cg), to the window's slack: |Cg - Dg| <= 1 gives Dg <= 1 + Cg <= exp(2.3 Cg)
- conservation `volume`: the trapezoid continuity holds in every distance step: inflow volume - outflow volume = storage at the end - storage at the start

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/muskingum-cunge-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: Ponce's form of the weights, (C + D - 1, 1 + C - D, 1 - C + D) / (1 + C + D), and the recurrence of the distance steps in exact rational arithmetic (fractions) (`tests/unit/test_formulas_muskingum_cunge.py (limit exact_recurrence)`)
- exact: the moments of the impulse response against those of the diffusion wave of HEC-HMS eq. 3, mean L / c and variance 2 mu L / c^3 with mu = Q / (2 T S0), which Cunge's K and X reproduce exactly (`tests/unit/test_formulas_muskingum_cunge.py (limit moments)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

<a id="level_pool"></a>
### Level-pool routing by storage indication (modified Puls) through N equal pools

`hydrolog.routing.formulas.level_pool.level_pool_route` · family `scheme` · formula_version 1 · status **referenced** · mutation score not measured

$$
\frac{s_t}{\Delta t} + \frac{O_t}{2} = \frac{I_{t-1} + I_t}{2} + \frac{s_{t-1}}{\Delta t} - \frac{O_{t-1}}{2},\quad s = \frac{S(O)}{N}
$$

Plain text: `in each of N pools in series, holding s = S(O) / N of the table for the same outflow: s[t] / dt + O[t] / 2 = (I[t-1] + I[t]) / 2 + s[t-1] / dt - O[t-1] / 2, O[t] read from the working curve s / dt + O / 2 of the table, linear between its rows; O[0] = O0 in every pool, at rest at the highest storage the table gives O0`

**Sources**

- USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-1 to 17-3, pp. 17-9 to 17-10 (a working curve of O2 against S2/dt + O2/2 is necessary); examples 17-1 and 17-2, tables 17-5 to 17-12, pp. 17-11 to 17-25 (open) <https://directives.nrcs.usda.gov/sites/default/files2/1712930634/Part%20630%20-%20Hydrology.pdf>
- US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, eq. 3; Required Parameters: the initial outflow, a storage vs. discharge relationship and the number of subreaches (open) <https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/modified-puls-model>
- US Army Corps of Engineers (1994). Engineering and Design: Flood-Runoff Analysis, EM 1110-2-1417, chapter 9, modified Puls, eq. 9-12 (open) <https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1417.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `inflow_m3s` | $I_t$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |
| `timestep_min` | $\Delta t$ | min | real | (0.0, inf), test bound high 1440.0 (a day, the step of a series of daily discharges (IMGW-PIB)) | unstated | [5.0, 720.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), steps of 5 min (Hydrograf's networks, tests/fixtures/handoff_hydrograf_network*.json) to 12 h (the Iowa example and NEH 630 ch. 17 example 17-2, 0.5 d) |
| `table_storage_m3` | $S_i$ | m3 | real_array | [0.0, inf), test bound high 30000000.0 (ten times the largest table of Hydrolog's routing tests (NEH 630 ch. 17 example 17-2, 2.87e6 m3); the scheme is homogeneous in the storage and the discharge (scaling discharge), so any bound tests its arithmetic) | unstated | [0.0, 3000000.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), tables up to 2.87e6 m3: NEH 630 ch. 17 example 17-2, 1,174.5 ft3/s-d; the catalog's pond, 255,000 m3 (tests/fixtures/pond_rating.csv) |
| `table_outflow_m3s` | $O_i$ | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 300.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), tables up to 283.2 m3/s: NEH 630 ch. 17 example 17-1, 10,000 ft3/s; the catalog's pond, 27.17 m3/s |
| `subreaches` | $N$ | - | integer | [1.0, inf), test bound high 1000.0 (HEC-HMS's estimate L / (c dt) for a reach of 100 km, a celerity of 1 m/s and a step of 100 s) | unstated | [1.0, 6.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), 1 (a pond or a reservoir, the default of LevelPoolReach) to 6 pools in the tests of the reach |
| `initial_outflow_m3s` | $O_0$ | m3/s | real | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | unstated | [0.0, 100.0]: Hydrolog's routing tests and examples (tests/unit/test_routing_*.py, tests/unit/_routing_reference.py, docs/USAGE.md section route), floods of 0 to 95.9 m3/s: NEH 630 ch. 17 example 17-5, 3,385.4 cfs; the guide's Kamiennik, 54.2 m3/s |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `table_columns_paired` | physical | the storage and the outflow columns have as many rows | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the storage vs. discharge relationship is a paired data object whose storages cover the entire range met in a simulation; the initial storage is computed from the initial outflow and that relationship |
| `table_not_decreasing` | physical | S[i] <= S[i+1] and O[i] <= O[i+1]: storage and outflow rise together with the water level | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), tables 17-4 and 17-9 to 17-11: storage and discharge accumulated with the elevation, both rising with it |
| `table_rows_distinct` | physical | no row repeats the one before it: the working curve rises from row to row | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-1 to 17-3, pp. 17-9 to 17-10 (a working curve of O2 against S2/dt + O2/2 is necessary); examples 17-1 and 17-2, tables 17-5 to 17-12, pp. 17-11 to 17-25 |
| `initial_outflow_in_table` | precondition | O[0] <= O0 <= O[-1]: the pools start at rest at a state of the table | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the storage vs. discharge relationship is a paired data object whose storages cover the entire range met in a simulation; the initial storage is computed from the initial outflow and that relationship |
| `storage_where_outflow_rises` | precondition | dS > 0 on every segment where the outflow rises, from the state at rest under the lowest flow of the run to the first row that reaches its largest: no step meets the step rule on a segment without storage | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), pp. 17-10 to 17-11: negative outflows whenever dt > 2 S2/O2 (O2/2 > S2/dt); a working curve with any part left of the line of equal values is discarded and computed again with a smaller dt, as WinTR-20 does internally |
| `timestep_within_limit` | precondition | dt <= 2 min(dS/dO) / N over the segments the run can reach (from the state at rest under its lowest flow to the first row that reaches its largest), to 1e-9 of itself: the weight (2K - dt) / (2K + dt) of the previous state is not negative on any of them, so the outflow stays between the lowest and the highest flow of the run | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Stability: a level-pool step of at most twice the shortest dS/dO of the segments between the lowest and the highest flow of the run, over the number of sub-reaches; NEH's rule for the whole curve let the outflow exceed the inflow peak on 201 of 1,499 random tables |
| `working_curve_rises` | precondition | S / (N dt) + O / 2 is finite and rises from row to row in float64: the outflow is read from it | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), eqs. 17-1 to 17-3, pp. 17-9 to 17-10 (a working curve of O2 against S2/dt + O2/2 is necessary); examples 17-1 and 17-2, tables 17-5 to 17-12, pp. 17-11 to 17-25 |
| `flood_below_table_top` | precondition | no pool fills beyond the last row (its working curve above the last row's by more than 1e-9 of it): the table covers the flood, never an extrapolation | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the storage vs. discharge relationship is a paired data object whose storages cover the entire range met in a simulation; the initial storage is computed from the initial outflow and that relationship |
| `flood_above_table_bottom` | precondition | no pool empties below the first row (its working curve below the first row's by more than 1e-9 of the last row's): an inflow below the first outflow of the table must not drain it | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the storage vs. discharge relationship is a paired data object whose storages cover the entire range met in a simulation; the initial storage is computed from the initial outflow and that relationship |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `outflow_m3s` | m3/s | real_array | [0.0, inf), test bound high 1000000.0 (a million m3/s exceeds the discharge of every river, the Amazon's included; the routing formulas are linear in the discharge (their scaling), so any bound tests their arithmetic) | 4 ulp of the bound |
| `storage_m3` | m3 | real_array | [0.0, inf) | 4 ulp of the bound |
| `last_pool_storage_m3` | m3 | real_array | [0.0, inf) | 4 ulp of the bound |
| `storage_peak_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |
| `storage_steady_m3` | m3 | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- SI units: discharge in m3/s, storage in m3, the step in min (S / dt with the 60 s of a minute of the units table)
- the outflow is read from the working curve S / (N dt) + O / 2 by linear interpolation between the rows of the table, as the table is linear between them (NEH 630 interpolates its working table, HEC-HMS solves the same equation by trial and error)
- N pools in series each hold S / N for the same outflow (HEC-HMS subreaches); every pool starts at rest with O0, at the highest storage the table gives that outflow, so a pool with a dead zone below a crest starts full to the crest
- the datum of the storage column is free: only differences of storage enter the outflow, and the storages reported are measured from it
- a state that rounding puts beyond an end of the table by at most 1e-9 of the working curve's top is held at that end; further beyond, the pool has left the table, which the preconditions flood_below_table_top and flood_above_table_bottom refuse
- the storage at rest under the last inflow ordinate is read at the end row of the table for a flow beyond it
- only the given ordinates are routed: LevelPoolReach divides a longer step into sub-steps, the inflow linear between the ordinates, extends the time axis and reads the stage of the last pool (Tier B, ADR-0008)

**Assumptions**

- the storage is a single-valued function of the outflow: a level water surface, or a reach whose storage follows its outflow, without hysteresis (NEH 630: the water surface is level or nearly level)
- for a channel NEH 630 asks for a travel time through the reach of about half the inflow's time of rise or less (not an input: not checked)
- the inflow is linear between its ordinates (the trapezoid rule)

**Validation:** none: the storage-outflow relation of a reach or a reservoir comes from water-surface profiles, the reservoir's topography or observed floods (HEC-HMS TRM, Modified Puls; NEH 630 ch. 17); the sources report no agreement of the scheme itself with observations

**Notices:** none

**Numerical traps (CMP-6.6)**

- `difference_denominator`: the fraction (Y - W[r]) / (W[r+1] - W[r]) of a segment of the working curve: rows whose working curve is equal in float64 are refused by the precondition working_curve_rises (test_rows_the_working_curve_cannot_tell_apart_are_refused); K = dS/dO of the step rule is taken only where the outflow rises
- `stability_bound`: dt <= 2 min(dS/dO) / N on the segments the run reaches: precondition timestep_within_limit with its satisfied, boundary and violated points, limit bounded_by_its_flows (a kinked table on the step of its steep segment) and test_a_step_that_the_rule_for_the_whole_curve_allows_is_refused
- `gap_propagation`: type cases inflow_m3s-nan_element, table_storage_m3-nan_element and table_outflow_m3s-nan_element: a gap is refused, the recurrence would carry it to every later ordinate
- `many_small_terms`: test_a_long_steady_inflow_stays_steady: 200,000 ordinates of a steady inflow stay steady to 1e-12

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `discharge`: inputs times 2^e (`inflow_m3s` e = 1.0, `table_storage_m3` e = 1.0, `table_outflow_m3s` e = 1.0, `initial_outflow_m3s` e = 1.0) give outputs times 2^e (`outflow_m3s` e = 1.0, `storage_m3` e = 1.0, `last_pool_storage_m3` e = 1.0, `storage_peak_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- scaling `time`: inputs times 2^e (`timestep_min` e = 1.0, `table_storage_m3` e = 1.0) give outputs times 2^e (`storage_m3` e = 1.0, `last_pool_storage_m3` e = 1.0, `storage_peak_m3` e = 1.0, `storage_steady_m3` e = 1.0)
- limit `steady_state`: an inflow equal to the initial outflow passes unchanged, and the pools hold what the table gives it at rest
- limit `exact_recurrence`: every outflow equals the recurrence of the pools in exact rational arithmetic
- limit `muskingum_without_weight`: a table S = K O is the linear reservoir: the outflow and the storage of the spec muskingum with X = 0 and the same K, N and step
- limit `bounded_by_its_flows`: every outflow lies between the least and the largest of the inflow and the initial outflow, a kinked table on the step its steep segment allows included; the scheme is non-decreasing in the inflow and the initial outflow to the rounding of its working curve, larger than four units in the last place of the outflow on a short step (test_the_outflow_rises_with_its_inflow_and_initial_outflow)
- limit `datum_free`: a constant added to the storage column changes no outflow and adds itself to the storage
- conservation `volume`: the trapezoid continuity holds in every pool: inflow volume - outflow volume = storage at the end - storage at the start

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/level-pool-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the recurrence of the pools and their state at rest in exact rational arithmetic (fractions), ordinate by ordinate (`tests/unit/test_formulas_level_pool.py (limit exact_recurrence)`)
- algorithm: a table S = K O is the linear reservoir: the spec muskingum with X = 0 and the same K, N and step, its three-point recurrence (scipy.signal.lfilter) (`tests/unit/test_formulas_level_pool.py (limit muskingum_without_weight)`)
- established: scipy.integrate.solve_ivp (RK45, rtol 1e-11) of dS/dt = I(t) - O(S) through a weir's table: the scheme's error falls as the step squared (`tests/unit/test_formulas_level_pool.py::test_the_scheme_converges_to_the_integrated_equation`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6).

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

<a id="anderson_darling"></a>
### Anderson-Darling statistic A² of a sample against a fitted distribution

`hydrolog.statistics.frequency.anderson_darling` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
A^2 = -n - \sum_{i=1}^{n} \frac{2i - 1}{n}\left[\ln F(x_{(i)}) + \ln\left(1 - F(x_{(n+1-i)})\right)\right]
$$

Plain text: `A² = -n - sum_i (2 i - 1) / n [ln F(x_(i)) + ln(1 - F(x_(n+1-i)))] over the ascending sample x_(1) <= ... <= x_(n), F the distribution function at the parameters, clipped to [cdf_clip, 1 - cdf_clip]`

**Sources**

- NIST/SEMATECH e-Handbook of Statistical Methods (2012), sect. 1.3.5.14, Anderson-Darling test: A² = -N - S, S = sum (2i - 1) / N [ln F(Y_i) + ln(1 - F(Y_(N+1-i)))] of the ordered data (open) <https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm>
- Anderson, T.W. and Darling, D.A. (1954). A test of goodness of fit. Journal of the American Statistical Association 49(268), 765-769, the statistic W_n² and its computing form (author-provided)
- Stephens, M.A. (1974). EDF statistics for goodness of fit and some comparisons. Journal of the American Statistical Association 69(347), 730-737, the computing form of A²; case 0, a distribution given in advance (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |
| `shape` | $k$ | - | real | (-inf, inf), test bound low -9.0 and high 50.0 (the shapes of Hydrolog's estimators: a Pearson III skewness above -9 by least squares, a GEV c and a Weibull shape of at most 50) | unstated | [-0.6, 2.7]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\xi$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [-1.0, 35.4]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $\alpha$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [1.0, 37.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `shape_of_the_distribution` | physical | shape > 0 for the log-normal (s) and Weibull (k) | Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `cdf_clip` | $\epsilon$ | 1e-10 | - | Hydrolog (2026). ADR-0048: Anderson-Darling critical values by a parametric bootstrap, decision 1: A² keeps its form, F clipped to [1e-10, 1 - 1e-10] |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `a_squared` | - | real | [0.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the statistic of a distribution given in advance (case 0 of Stephens 1974), here at the parameters estimated from the same sample: its critical values are not case 0's
- the critical values FloodFrequencyAnalysis gives a fit by L-moments are those of a parametric bootstrap of that fit (ADR-0048): 999 samples of n values drawn from it with the seed 20261118, each refitted by L-moments; a fit by another method has none
- F clipped to [cdf_clip, 1 - cdf_clip], so a value outside the support of the distribution adds a large finite term instead of an infinite one
- F of scipy.stats at the parameters of its lognorm, genextreme, pearson3 or weibull_min
- the sample in any unit, with loc and scale in it: A² has none

**Assumptions**

None stated.

**Validation:** none: a distance between the sample and the fitted distribution

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: limit integral_form: ln F at a value outside the support, where F = 0, is ln cdf_clip
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_sample`: inputs times 2^e (`annual_maxima` e = 1.0, `loc` e = 1.0, `scale` e = 1.0) give outputs times 2^e (none)
- limit `integral_form`: n times the integral of (F_n(u) - u)² / (u (1 - u)) over [0, 1], in closed pieces at 50 digits, for the L-moment fits of two samples and a Weibull distribution that leaves a value outside its support
- symmetry `order`: the sample in the reverse order has the same A²

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the integral form of the definition, n times the integral of (F_n(u) - u)² / (u (1 - u)) du, in closed pieces at 50 digits (decimal) (`tests/unit/test_formulas_flood_frequency.py (limit integral_form)`)
- established: scipy.stats.anderson for the normal distribution (Pearson III of skewness 0) and the Gumbel distribution (the GEV of c = 0) (`tests/unit/test_formulas_flood_frequency.py (test_the_a_squared_is_scipys)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="akaike_information_criterion"></a>
### Akaike information criterion of a distribution fitted to a sample

`hydrolog.statistics.frequency.akaike_information_criterion` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
\mathrm{AIC} = 2k - 2\sum_{i=1}^{n} \ln f(x_i; k, \xi, \alpha)
$$

Plain text: `AIC = 2 k - 2 sum_i ln f(x_i; shape, loc, scale), f the density at the parameters; k = 2 for the log-normal of location 0, 3 for the others`

**Sources**

- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.3, eq. 5.31, pp. II.5-14 and II.5-15: AIC(f) = -2 log L(theta, x) + 2k, with L the likelihood function and k the number of parameters; alone not appropriate for model selection (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- Akaike, H. (1974). A new look at the statistical model identification. IEEE Transactions on Automatic Control 19(6), 716-723, the criterion -2 ln (maximum likelihood) + 2 k (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `annual_maxima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `distribution` | $F$ | - | choice of log_normal, gev, pearson3, weibull | – | – | – |
| `shape` | $k$ | - | real | (-inf, inf), test bound low -9.0 and high 50.0 (the shapes of Hydrolog's estimators: a Pearson III skewness above -9 by least squares, a GEV c and a Weibull shape of at most 50) | unstated | [-0.6, 2.7]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `loc` | $\xi$ | m3/s | real | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [-1.0, 35.4]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |
| `scale` | $\alpha$ | m3/s | real | (0.0, inf), test bound high 1000000.0 (the formulas are homogeneous in the unit of loc and scale (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river) | unstated | [1.0, 37.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4 (the Czarna at Polana, the Rypienica at Rypin, the Świślina at Rzepin, tables 3.5, 3.10 and 3.13): the parameters Hydrolog's four estimators give their annual maxima, with the log-normal and Weibull parameters the examples print (pp. 47-48 and 53-54) |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `shape_of_the_distribution` | physical | shape > 0 for the log-normal (s) and Weibull (k) | Virtanen, P. et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods 17, 261-272, scipy.stats.lognorm, shape s > 0, and scipy.stats.weibull_min, shape c > 0 |
| `values_within_support` | precondition | ln f(x_i) is finite for every value, and so is their sum: each value inside the support of the distribution, where its density is positive and finite | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.3, eq. 5.31: the logarithm of the likelihood, -inf where a value has no density |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `aic` | - | real | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the likelihood at the parameters of the method that fitted them, the maximum only for maximum likelihood (ADR-0021, point 7): a ranking by AIC compares the likelihood of each fit's parameters
- k counts the parameters fitted: 2 for the log-normal, whose location is fixed at 0, 3 for the others
- a fit that leaves a value outside its support has no finite AIC: FloodFrequencyAnalysis gives it an infinite AIC without the formula, with the notice outside_support, and ranks it last
- ln f of scipy.stats at the parameters of its lognorm, genextreme, pearson3 or weibull_min, summed exactly rounded (math.fsum)
- the natural logarithm; the AIC depends on the unit of the sample

**Assumptions**

None stated.

**Validation:** none: a criterion for comparing fits; WMO-No. 168 finds it alone not appropriate for choosing one

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case values_within_support-violated: ln f of a value outside the support is refused before the sum
- `gap_propagation`: type case annual_maxima-nan_element: a gap is refused
- `many_small_terms`: symmetry order: the log-likelihood is summed exactly rounded, in any order

**Properties (CMP-6.5)**

- units: unit_specific
- limit `closed_form`: the AIC of the moment fits of two samples, every value inside their supports, with the densities of the four distributions written out
- limit `unit_of_the_sample`: doubling the sample, loc and scale adds 2 n ln 2: the AIC depends on the unit of the sample
- symmetry `order`: the sample in the reverse order has the same AIC

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the log-likelihood with the densities of the GEV, the log-normal, Pearson III and Weibull written out (math) (`tests/unit/test_formulas_flood_frequency.py (limit closed_form)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="plotting_positions"></a>
### Plotting positions of annual maxima: exceedance probabilities and return periods

`hydrolog.statistics._types.compute_plotting_positions` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
p_i = \frac{i - a}{n + 1 - 2a},\qquad T_i = \frac{1}{p_i}
$$

Plain text: `p_i = (i - a) / (n + 1 - 2a) and T_i = 1 / p_i of the value of rank i = 1 ... n, ranked from the largest (rank 1); a = 0 (Weibull, i / (n + 1)), 1/2 (Hazen, (i - 1/2) / n) or 2/5 (Cunnane, (i - 2/5) / (n + 1/5))`

**Sources**

- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>
- KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), eq. 3.7, p. 29: p_i = i / (N + 1) 100 %, the empirical exceedance probability of the ith largest annual maximum; example 3.4, table 3.13, pp. 54-55 (open) <https://kzgw.gov.pl/files/zam-pub/20170402-przeglad-i-aktualizacja-map/zal-2-do-OPZ-ujednolicony-1.pdf>
- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.3, eq. 7.3, p. 59: P_i = (i - a) / (n + 1 - 2a), the non-exceedance probability of the ith smallest of n events; p. 60: the Weibull formula is a = 0; sect. 7.8, step I, p. 65: the AM(7) values ranked ascending, the smallest rank 1, and the Weibull formula (open) <https://library.wmo.int/idurl/4/32176>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_{(i)}$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.81, 111.0]: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych o określonym prawdopodobieństwie przewyższenia dla zlewni kontrolowanych i niekontrolowanych, załącznik 2 do OPZ (wersja ujednolicona), examples 3.2 to 3.4, tables 3.5, 3.10 and 3.13 (pp. 39-55): annual maxima of 0.81 m3/s (Rypienica at Rypin) to 111 m3/s (Czarna at Polana) |
| `method` | $a$ | - | choice of weibull, hazen, cunnane | – | – | – |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `a_weibull` | $a$ | 0 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |
| `a_hazen` | $a$ | 1/2 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |
| `a_cunnane` | $a$ | 2/5 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `values_sorted` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |
| `exceedance_prob` | - | real_array | (0.0, 1.0) | 4 ulp of the bound |
| `return_periods` | years | real_array | (1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the exceedance probability of the ith largest value, rank 1 the largest (WMO-No. 168 sect. 5.6.1; KZGW 2017 eq. 3.7, Polish p_i = i / (N + 1)); the return period T = 1 / p, as of the quantiles of the maxima
- the general form (i - a) / (n + 1 - 2a) of WMO-No. 1029 eq. 7.3 with the a of WMO-No. 168 sect. 5.6.1; no Gringorten formula
- tied values keep consecutive ranks, each with its own position, as KZGW 2017 table 3.13 ranks its two values of 10.3 and of 7.88 m3/s
- the sample in any unit: the positions depend on the ranks only

**Assumptions**

None stated.

**Validation:** none: an estimate of the probability of each value of the ranked sample

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: limit exact_rational: the return period one over the smallest position, about 1 / n, of up to 10,000 values; the positions never reach 0 or 1
- `gap_propagation`: type case values-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`values_sorted` e = 1.0)
- limit `exact_rational`: the positions and return periods of the definition in exact rational arithmetic, for samples of 1 to 10,000 values
- symmetry `order`: the sample in the reverse order has the same positions
- symmetry `mirror`: the negated sample has the negated values in the reverse order and the same positions

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the positions and return periods in exact rational arithmetic (fractions) (`tests/unit/test_formulas_flood_frequency.py (limit exact_rational)`)
- established: scipy.stats.mstats.plotting_positions with alpha = beta = a (`tests/unit/test_formulas_flood_frequency.py (test_the_plotting_positions_are_scipys)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="non_exceedance_positions"></a>
### Plotting positions of annual minima: non-exceedance probabilities and return periods

`hydrolog.statistics._types.compute_non_exceedance_positions` · family `statistic` · formula_version 1 · status **referenced** · mutation score not measured

$$
p_i = \frac{i - a}{n + 1 - 2a},\qquad T_i = \frac{1}{p_i}
$$

Plain text: `p_i = (i - a) / (n + 1 - 2a) and T_i = 1 / p_i of the value of rank i = 1 ... n, ranked from the smallest (rank 1); a = 0 (Weibull, i / (n + 1)), 1/2 (Hazen, (i - 1/2) / n) or 2/5 (Cunnane, (i - 2/5) / (n + 1/5))`

**Sources**

- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.3, eq. 7.3, p. 59: P_i = (i - a) / (n + 1 - 2a), the non-exceedance probability of the ith smallest of n events; p. 60: the Weibull formula is a = 0; sect. 7.8, step I, p. 65: the AM(7) values ranked ascending, the smallest rank 1, and the Weibull formula (open) <https://library.wmo.int/idurl/4/32176>
- WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n (open) <https://www.hydrology.nl/images/docs/hwrp/WMO_Guide_168_Vol_II_en.pdf>

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `values` | $x_{(i)}$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.0, 78.0]: WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, table 7.1, p. 64: the AM(7) annual minima of stations 223204 and 223207, 0 to 78 in the unit of the table |
| `method` | $a$ | - | choice of weibull, hazen, cunnane | – | – | – |

**Constants**

| Constant | Symbol | Value | Unit | Source |
|---|---|---|---|---|
| `a_weibull` | $a$ | 0 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |
| `a_hazen` | $a$ | 1/2 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |
| `a_cunnane` | $a$ | 2/5 | - | WMO (2009). Guide to Hydrological Practices, 6th ed., Volume II: Management of Water Resources and Application of Hydrological Practices, WMO-No. 168, sect. 5.6.1, p. II.5-14: the exceedance probability p_i of the ith largest flood x(i) by the Weibull formula i / (n + 1), the Cunnane formula (i - 0.40) / (n + 0.2) and the Hazen formula (i - 0.5) / n |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `values_ascending` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |
| `non_exceedance_probabilities` | - | real_array | (0.0, 1.0) | 4 ulp of the bound |
| `return_periods` | years | real_array | (1.0, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- the non-exceedance probability of the ith smallest value, rank 1 the smallest (WMO-No. 1029 eq. 7.3 and sect. 7.8, step I); the return period T = 1 / F of a low flow undercut once in T years (WMO-No. 1029 eq. 7.14), as of the quantiles of fisher_tippett_minima
- the general form (i - a) / (n + 1 - 2a) of WMO-No. 1029 eq. 7.3 with the a of WMO-No. 168 sect. 5.6.1; no Gringorten formula
- tied values keep consecutive ranks, each with its own position, as KZGW 2017 table 3.13 ranks its two values of 10.3 and of 7.88 m3/s
- the sample in any unit: the positions depend on the ranks only

**Assumptions**

None stated.

**Validation:** none: an estimate of the probability of each value of the ranked sample

**Notices:** none

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: limit exact_rational: the return period one over the smallest position, about 1 / n, of up to 10,000 values; the positions never reach 0 or 1
- `gap_propagation`: type case values-nan_element: a gap is refused

**Properties (CMP-6.5)**

- units: homogeneous
- monotonic: `values` increasing
- scaling `unit_of_the_sample`: inputs times 2^e (`values` e = 1.0) give outputs times 2^e (`values_ascending` e = 1.0)
- limit `exact_rational`: the positions and return periods of the definition in exact rational arithmetic, for samples of 1 to 10,000 values
- symmetry `order`: the sample in the reverse order has the same positions
- symmetry `mirror`: the negated sample has the negated values in the reverse order and the same positions

**Reference cases (CMP-6.1)**

- `tests/fixtures/formulas/flood-frequency-cases.json`

**Oracles (CMP-6.2 to CMP-6.4)**

- exact: the positions and return periods in exact rational arithmetic (fractions) (`tests/unit/test_formulas_flood_frequency.py (limit exact_rational)`)
- established: scipy.stats.mstats.plotting_positions with alpha = beta = a (`tests/unit/test_formulas_flood_frequency.py (test_the_plotting_positions_are_scipys)`)

**Tests by class (CMP §6):** reference cases (CMP-6.1); oracles (CMP-6.2); established implementations (CMP-6.3); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

<a id="fisher_tippett_minima"></a>
### Fisher-Tippett distribution of annual minima by maximum likelihood and its quantiles

`hydrolog.statistics.low_flows.fisher_tippett_minima` · family `statistic` · formula_version 1 · status **oracle only** · mutation score not measured

$$
F(x) = 1 - \exp\left\{-\left[1 + c\,\frac{x - \xi}{\alpha}\right]^{1/c}\right\},\quad Q_T = \xi + \frac{\alpha}{c}\left[\left(-\ln\left(1 - \frac{1}{T}\right)\right)^{c} - 1\right]
$$

Plain text: `F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)}, the GEV of -x (scipy's genextreme with shape c and location -loc) fitted to the negated minima by maximum likelihood (fit_maximum_likelihood); Q_T = loc + scale ((-ln(1 - 1/T))**c - 1) / c at the non-exceedance 1/T, loc + scale ln(-ln(1 - 1/T)) for c = 0; a quantile of a discharge below 0 is a gap`

**Sources**

- WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, p. 62: if X is EV III distributed, -X is Weibull distributed; eq. 7.14, p. 64: T of the event X <= x_p (open) <https://library.wmo.int/idurl/4/32176>
- Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values. Springer, sect. 3.1.4: min(X) = -max(-X), the GEV of minima (author-provided)

**Variables**

| Variable | Symbol | Unit | Kind | Physical range | Applicability | Typical range |
|---|---|---|---|---|---|---|
| `minima` | $x_i$ | m3/s | real_array | (-inf, inf), test bound low -1000000.0 and high 1000000.0 (the formulas are homogeneous in the unit of the sample (their scalings), so any bound tests their arithmetic: a million m3/s exceeds the discharge of every river, and a stage may lie below its gauge's zero, so the same bound holds below 0) | unstated | [0.0, 78.0]: WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, table 7.1, p. 64: the AM(7) annual minima of stations 223204 and 223207, 0 to 78 in the unit of the table |
| `return_periods_years` | $T$ | years | real_array | (1.0, inf), test bound high 1000000.0 (a million years tests the far lower tail; droughts are estimated for at most a thousand years) | unstated | [2.0, 1000.0]: Hydrolog (2026). stats low-flow and Obserwator's low_flow.Q, the default return periods, 2 to 1000 years |
| `variable` | $v$ | - | choice of discharge, stage | – | – | – |

**Constraints**

| Constraint | Class | Condition | Source |
|---|---|---|---|
| `enough_values` | precondition | n >= 4 | Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, n values fit n parameters exactly, where the likelihood has no maximum: one value more than the three parameters |
| `values_not_all_equal` | precondition | min(x) < max(x) | WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5: a distribution of the minima needs their spread |
| `discharges_not_negative` | physical | min(x) >= 0 for a discharge | WMO (2008). Manual on Low-flow Estimation and Prediction, Operational Hydrology Report No. 50, WMO-No. 1029, sect. 7.5, p. 62: the lower bound of the minima of a flow is 0 or above |
| `likelihood_has_a_maximum` | precondition | the GEV likelihood of the negated minima has a maximum the search settles on (precondition likelihood_has_a_maximum of fit_maximum_likelihood) | Smith, R.L. (1985). Maximum likelihood estimation in a class of nonregular cases. Biometrika 72(1), 67-90, the bound placed at the closest value makes the likelihood grow without limit |

**Outputs**

| Output | Unit | Kind | Physical range | Boundary tolerance |
|---|---|---|---|---|
| `shape` | - | real | (-inf, inf) | 4 ulp of the bound |
| `loc` | m3/s | real | (-inf, inf) | 4 ulp of the bound |
| `scale` | m3/s | real | (0.0, inf) | 4 ulp of the bound |
| `quantiles` | m3/s | real_array | (-inf, inf) | 4 ulp of the bound |

**Conventions (CMP-2.3)**

- min(x) = -max(-x): the Fisher-Tippett distribution of the minima is the GEV of the negated minima, F(x) = 1 - exp{-[1 + c (x - loc) / scale]^(1/c)} with scipy's genextreme shape c and the location -loc of the negated sample
- the quantile of T years at the non-exceedance probability 1/T (WMO-No. 1029 eq. 7.14), from the inverse survival function of the negated sample
- a discharge quantile below 0 is a gap (NaN, null in JSON) with the notice negative_quantiles; a stage keeps it
- the search of fit_maximum_likelihood: the GEVs with a mean, -1 < c < 1

**Assumptions**

- the annual minima are independent and identically distributed

**Validation:** none: the maximum-likelihood fit of the distribution of minima

**Notices:** `negative_quantiles`

**Numerical traps (CMP-6.6)**

- `singular_at_bound`: constraint case likelihood_has_a_maximum-violated: the density infinite at a bound placed on a value
- `unbounded_iteration`: the search of fit_maximum_likelihood (tests/unit/test_formulas_flood_frequency.py, test_a_search_that_does_not_settle_is_refused)
- `gap_propagation`: type case minima-nan_element: a gap is refused; the gaps of the quantiles are the negative discharges

**Properties (CMP-6.5)**

- units: homogeneous
- scaling `unit_of_the_minima`: inputs times 2^e (`minima` e = 1.0) give outputs times 2^e (`loc` e = 1.0, `scale` e = 1.0, `quantiles` e = 1.0)
- limit `gev_of_the_negated`: the parameters and quantiles are those of the maximum-likelihood GEV of the negated minima, mirrored

**Reference cases (CMP-6.1)**

None.

**Oracles (CMP-6.2 to CMP-6.4)**

- algorithm: the maximum-likelihood GEV of the negated minima and its quantiles, mirrored (`tests/unit/test_formulas_low_flows.py (limit gev_of_the_negated)`)
- frozen: evd 2.3.7.1 fgev and extRemes 2.2.1 fevd on the negated minima of a small stream (the research of 2026-11-18): log-likelihood 54.537, Q10 0.017422 m3/s (`tests/unit/test_maximum_likelihood.py (test_small_stream_low_flows_are_the_maximum_and_never_negative)`)

**Tests by class (CMP §6):** oracles (CMP-6.2); frozen oracles (CMP-6.4); generated ranges and types (CMP-6.5); properties (CMP-6.5); numerical traps (CMP-6.6); statistical procedures (CMP-6.7).

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
| `hydrograph_volume` | `hydrolog.routing.hydrograph.Hydrograph.volume_m3` | the volume under the ordinates by the trapezoid rule: the step times the sum of the ordinates with the first and the last halved, in m3 | – | the discharge is linear between the ordinates; minutes to seconds by the units table | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Hydrograph table, Balance and Stability |
| `hydrograph_refinement` | `hydrolog.routing.hydrograph.Hydrograph.refined` | the hydrograph on a step divided into equal sub-steps, the new ordinates on the straight lines between the old ones | – | the old ordinates are kept exactly and the volume is unchanged; a scheme run on the sub-steps is read back at the original ordinates | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Hydrograph table, Balance and Stability |
| `hydrograph_extension` | `hydrolog.routing.hydrograph.Hydrograph.extended` | the hydrograph with steps added after its last ordinate, each holding the last value (or a given one) | – | the inflow after the record is its last value, as the tail of the routing assumes | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Hydrograph table, Balance and Stability |
| `routing_initial_state` | `hydrolog.routing.reach._initial_outflow` | the outflow at the first ordinate: the given initial outflow, else the first inflow ordinate; every sub-reach, pool or reservoir of the element starts at rest with it | – | a steady state at the start (HEC-HMS initialises a reach by its inflow); a given initial outflow is finite and not negative | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Initial condition |
| `routing_tail` | `hydrolog.routing.reach._settled` | the shortest extension of the time axis, the last inflow held, after which the outflow is within the tolerance of the final inflow (relative to the inflow peak) and the water stored above its steady amount is within the tolerance of the inflow volume (or of the excess the element started with, when larger); at most ten times the inflow duration and at least the minimum of steps | tail_tolerance = 0.001 - (Hydrolog ADR-0008: routing conventions, 0.1 % of the peak); min_extension_steps = 100.0 - (Hydrolog ADR-0008: routing conventions, at least 100 steps) | the inflow after its last ordinate is its last value; an outflow that has not settled at the cap gives the warning tail_truncated | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Tail |
| `routing_volume_balance` | `hydrolog.routing.reach.RoutingResult.balance_error_m3` | the inflow volume over the extended axis (the last inflow held) minus the outflow volume minus the storage at the end plus the storage at the start, each volume by the trapezoid rule | – | zero to rounding for a recurrence on the original step; the sampling error of the trapezoid rule after sub-steps, the quadrature error of an exact kernel (cascade) or of an interpolated lag otherwise | Hydrolog ADR-0008: routing conventions, docs/decisions/0008-routing-conventions.md, Balance |
| `muskingum_subreaches` | `hydrolog.routing.muskingum.subreach_window` | the whole numbers N of equal sub-reaches whose weights are non-negative on a step dt, ceil(2KX/dt) <= N <= floor(2K(1 - X)/dt), each end to 1e-9 of itself; MuskingumReach routes with N = K/dt rounded (a half up, at least 1), which lies in the window whenever a whole number does, and divides a step without a window into the fewest of 2 to 100 equal sub-steps that have one, the inflow linear between the ordinates | – | the travel time of a sub-reach is about one time step (HEC-HMS); a number of sub-reaches the caller gives is never changed: outside the window it is refused (unstable_timestep, ADR-0008) | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Muskingum Model, the number of subreaches: the travel time through a subreach approximately equal to the simulation time step |
| `cascade_time_scale` | `hydrolog.routing.cascade.CascadeReach` | the storage constant of one reservoir from the length L and the flood-wave celerity c of the reach, K = L / (n c): the travel time L / c is the mean delay n K of the cascade; L in km and c in m/s through the units table (1 km = 1000 m, 1 min = 60 s) | – | K is given directly or follows from L and c, never both (details.reason one_of); Kalinin and Milyukov take n as L over the characteristic length Q / (T S0 c) | Ponce, V.M. (online). Linear reservoirs and numerical diffusion, San Diego State University, the Kalinin-Milyukov method: n = L / L_c reservoirs of K = L_c / c in series |
| `muskingum_cunge_rise` | `hydrolog.routing.cunge.rise_steps` | the steps from the ordinate before the first one above 5 % of the inflow peak to the first peak of at least half of it; a rise of 1 to 9 steps divides each step of a grid into ceil(10 / rise) equal sub-steps (at most 100), the inflow linear between the ordinates (notice timestep_refined) | – | NEH 630 re-interpolates the hydrograph to exactly 10 intervals on the rise; Hydrolog divides into whole sub-steps, 10 intervals or more, and keeps the original ordinates; the reservoirs of a reach without a grid are exact at any step and are not refined | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), Muskingum-Cunge method, step 1: at least 10 time intervals from the point of 5 percent of the peak on the rise to the peak, p. 17-32 |
| `muskingum_cunge_grid` | `hydrolog.routing.cunge.MuskingumCungeReach._grid` | the reference discharge is the inflow peak unless one is given; the NRCS distance step dx_c = (c dt + D) / 2 with D = Q / (T S0 c) gives ceil(L / dx_c) steps, changed to the nearest number inside the window of non-negative weights \|c dt - D\| <= L / N <= c dt + D, each end to 1e-9 of itself (hydrolog.routing.formulas.cunge.distance_step_window); a step without a whole number in the window is divided into the fewest of 2 to 100 equal sub-steps that have one, the inflow linear between the ordinates (notices subreaches_adjusted, substeps_added); the notice accuracy_limit reports an NRCS grid whose Dg = D / dx exceeds exp(2.3 Cg) | – | one reference for every distance step, where WinTR-20 takes the peak at the upstream end of each; a grid with a negative weight, which NEH accepts (example 17-5), is replaced (ADR-0008); a grid that needs more than a million ordinates is refused (unstable_timestep) | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), steps 2 to 4 of the Muskingum-Cunge method and eqs. 17-21 and 17-36, pp. 17-32 to 17-33 |
| `muskingum_cunge_fallback` | `hydrolog.routing.cunge._reservoirs` | a reach without a grid within 100 sub-steps is routed as n = L / D linear reservoirs (rounded a half up, at least 1) of K = L / (n c) through the cascade of CascadeReach (notice diffusion_dominated) | – | the n reservoirs, of mean n K and variance n K^2, keep the mean travel time L / c of the diffusion wave and, as nearly as a whole n can, its variance D L / c^2 = 2 mu L / c^3 with mu = Q / (2 T S0) (HEC-HMS TRM, Muskingum-Cunge model, eq. 5) | Hydrolog ADR-0026: a reach without a Muskingum-Cunge grid, linear reservoirs with a warning, not a refusal, Decision, points 1 and 2 (docs/decisions/0026-a-reach-without-a-muskingum-cunge-grid.md) |
| `level_pool_substeps` | `hydrolog.routing.level_pool.timestep_limit_min` | the longest step a storage-outflow table allows a run, 2 min(dS/dO) / N over the segments from the state at rest under the lowest flow of the run to the first row that reaches its largest, in min (the precondition timestep_within_limit of the spec level_pool); LevelPoolReach divides a longer step into the fewest equal sub-steps that meet it, each end to 1e-9 of itself, the inflow linear between the ordinates, and reads the outflow back at the original ordinates (notice timestep_refined) | – | the rule per segment is stricter than NEH 630's for the whole curve, dt <= 2 S/O at every row (the working curve right of the line of equal values), which lets the outflow overshoot the inflow peak on a table whose slope changes sharply (ADR-0008); more than 100 sub-steps or more ordinates than the limit are refused (unstable_timestep), and so is a segment the run reaches without storage (working_curve) | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), pp. 17-10 to 17-11: negative outflows whenever dt > 2 S2/O2; a working curve left of the line of equal values is discarded and computed again with a smaller dt, which WinTR-20 adjusts internally |
| `level_pool_initial_outflow` | `hydrolog.routing.level_pool.LevelPoolReach._initial` | the outflow the pools start at rest with: the run's initial outflow (routing_initial_state), taken at the end of the table when it lies beyond it by at most 1e-9 of the table's largest outflow (at least 1e-9 m3/s); further beyond, it is refused (initial_outflow_m3s, minimum or maximum) | – | the table covers the run, never an extrapolation; the beyond is rounding, not data | US Army Corps of Engineers, Hydrologic Engineering Center. HEC-HMS Technical Reference Manual, Channel Flow: Modified Puls Model, Required Parameters: the initial storage is computed from the initial outflow and the storage vs. discharge relationship |
| `level_pool_stage` | `hydrolog.routing.level_pool._levels` | the stage of the last pool at every ordinate: the table's stage column at the pool's storage, linear between the rows; the peak stage and its time are its largest value and the first ordinate that has it, as the peak storage and its time are of the storage of all pools | – | the stage only reports, it does not enter the routing: for a reservoir (one pool) the level of the pool, for sub-reaches the level of the last | USDA-NRCS (2014). National Engineering Handbook, Part 630 Hydrology, Chapter 17: Flood Routing (210-VI-NEH, Amendment 69, April 2014), example 17-2, p. 17-25: the peak elevation and storage interpolated from the elevation-discharge and elevation-storage data of table 17-11 |
| `junction_sum` | `hydrolog.routing.network._sum` | the hydrograph of a junction: the sum of its inflows ordinate by ordinate on the longest of their axes, a shorter one held at its last value | – | one time step and one start for every source of a network, no resampling; holding a truncated outflow (tail_truncated) at a value above zero adds volume downstream, which the upstream warning names | Hydrolog's computation paths, section 3.9.7, and ADR-0008, docs/COMPUTATION_PATHS.md, Time axes: a junction holds a shorter hydrograph at its last value; one step, nothing resampled |
| `mean_width` | `hydrolog.morphometry.geometric.WatershedGeometry.width_km` | W = A / L, the mean width of the watershed [km] | – | L as length_km of WatershedGeometry (the straight line or the longest flow path); Baścik's B divides by the valley length Lm | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 21: średnia szerokość zlewni B = A / Lm |
| `midpoint_elevation` | `hydrolog.morphometry.terrain.TerrainAnalysis` | H_mean = (Hmin + Hmax) / 2, the mean elevation TerrainAnalysis assumes when none is given [m a.s.l.] | – | an approximation, with the notice mean_elevation_approximated where Hydrolog reports it; the area-weighted mean of the DEM (Baścik 2006, eq. 1.2.8, HypsometricCurve.mean_elevation) is to be preferred | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.5): the mean elevation approximated by the mean of the highest and the lowest |
| `hypsometric_curve` | `hydrolog.morphometry.hypsometry.HypsometricCurve.generate_curve` | relative heights h/H = (t - min) / (max - min) at n equally spaced thresholds t and the relative areas a/A of the cells at or above each | – | exceedance (area above), Strahler's percentage hypsometric curve; the first relative area is 1 | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |
| `area_weighted_mean_elevation` | `hydrolog.morphometry.hypsometry.HypsometricCurve.mean_elevation` | the mean elevation of the cells weighted by their areas [m a.s.l.] | – | numpy.average with the cell areas as weights | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, eq. (1.2.8): the mean elevation weighted by the areas between contours |
| `elevation_above_share` | `hydrolog.morphometry.hypsometry.HypsometricCurve.elevation_at_percentile` | the elevation of the first cell, from the highest down, at which the cumulative share of the area reaches the given percent [m a.s.l.] | – | the median elevation is the one with half of the area above it; no interpolation between cells | Strahler, A.N. (1952). Hypsometric (area-altitude) analysis of erosional topography. Geological Society of America Bulletin 63: 1117-1142, Fig. 3 and 'Integration of the hypsometric function': the integral is the area under the percentage hypsometric curve, relative area a/A above relative height h/H, over the unit square; the stages in the text with Fig. 7 (a copy of the article) |
| `streams_of_each_order` | `hydrolog.network.stream_order.StreamNetwork.get_statistics` | the number of Strahler streams of each order, their total and mean lengths [km] and the total length of the network [km] | – | a segment continues the stream of an upstream segment of its own order and begins one otherwise; the mean length is the total length of the order's segments over the number of its streams | Baścik, M. (2006). Parametry fizjograficzne. In: Pociask-Karteczka, J. (ed.), Zlewnia. Właściwości i procesy. Wydawnictwo Uniwersytetu Jagiellońskiego, Kraków, pp. 21-34, p. 28: Strahler's orders: a source stream is of order 1, two streams of order u form one of order u + 1, and where streams of different orders join, the stream below keeps the higher order |
| `usda_texture_codes` | `hydrolog.soil.texture.classify_usda_texture_array` | the class of spec usda_texture, cell by cell, as its code 1-12 (TEXTURE_CLASSES) | – | a cell without soil data - zero total, a NaN or an infinite amount - gets the code of loam (4) as a placeholder, which classify_hsg masks as no data; a negative amount is refused | Soil Science Division Staff (2017). Soil Survey Manual. USDA Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, Washington, DC, ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 (sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the textural triangle, Fig. 3-7, p. 125 |
| `texture_hsg_codes` | `hydrolog.soil.texture.texture_to_hsg_array` | the group of spec texture_hsg of each texture code, as the raster code 1-4 for A-D | – | texture code 0 (no data) gives 0; a code outside 0-12 is refused | USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical Release 55, 2nd ed. (210-VI-TR-55, June 1986), appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, after Brakensiek and Rawls (1983) |
| `hsg_of_amounts` | `hydrolog.soil.hsg.classify_hsg` | the group of spec texture_hsg of the class of spec usda_texture, cell by cell, as the raster code 1-4 for A-D | – | 0 (no data) for a cell with a NaN or infinite amount, an amount equal to its input's nodata tag, or all three amounts zero (the SoilGrids gap); a negative amount in a cell with data is refused | Kartograf ADR-025 (HSG from SoilGrids clay, sand and silt), ported to Hydrolog 0.8.0, raster codes uint8, 0 no data, 1-4 the groups A-D |
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
| manning_normal_depth | scipy.optimize.brentq | scipy>=1.10 (1.18.1 locked) | the root ln y = 0 of ln K(e^u) - ln K(1) for Manning's conveyance A R^(2/3) of a rectangle 2 m wide on [-1, 1] with xtol 1e-15 is 0 within 1e-14 (spec manning_normal_flow) | `tests/unit/test_formulas_muskingum_cunge.py::test_the_delegated_root_finder_finds_a_known_root` |
| kolmogorov_smirnov_test | scipy.stats.kstest (the K-S statistic and p-value of the flood and low-flow frequency analyses) | scipy>=1.10 (1.18.1 locked) | three values 0.05, 0.1 and 0.2 against the uniform distribution on [0, 1]: D = 0.8, the largest of i / n - u_i and u_i - (i - 1) / n, and the exact p = 2 (1 - D)^3 = 0.016 of D >= 2/3 | `tests/unit/test_formulas_flood_frequency.py::test_the_delegated_ks_test_gives_the_exact_statistic_and_p` |
| distribution_functions | scipy.stats genextreme, lognorm, pearson3 and weibull_min: cdf (the statistics of the fits and the bootstrap of A²) | scipy>=1.10 (1.18.1 locked) | F(1) of the GEV of c = 0.5, exp(-1/4); F(e) of the log-normal of s = 1, Phi(1); F(1) of Pearson III of skewness 2, 1 - exp(-2); F(1) of the Weibull of shape 2, 1 - exp(-1); loc 0 and scale 1 | `tests/unit/test_formulas_flood_frequency.py::test_the_delegated_distribution_functions_are_the_closed_forms` |
| densities | scipy.stats genextreme, lognorm, pearson3 and weibull_min: pdf and logpdf (the AIC, the densities at the quantiles, the likelihood searched) | scipy>=1.10 (1.18.1 locked) | f(1) of the GEV of c = 0.5, exp(-1/4) / 2; f(e) of the log-normal of s = 1, exp(-3/2) / sqrt(2 pi); f(1) of Pearson III of skewness 2, exp(-2); f(1) of the Weibull of shape 2, 2 exp(-1); loc 0 and scale 1, and ln f | `tests/unit/test_formulas_flood_frequency.py::test_the_delegated_densities_are_the_closed_forms` |
| lyne_hollick_recursion | scipy.signal.lfilter | scipy>=1.10 (1.18.1 locked) | lfilter([(1 + a) / 2], [1, -a], diff(Q), zi=[a Q_1]) gives the quickflow q_t = a q_(t-1) + (1 + a)/2 (Q_t - Q_(t-1)) from q_1 = Q_1 of the first pass of Ladson et al. (2013), Table 4 (Bass River, a = 0.98): 155.46 after 96 and 158 (spec lyne_hollick) | `tests/unit/test_formulas_baseflow.py::test_the_delegated_recursion_is_the_first_pass_of_table_4` |
| student_t_quantile | scipy.stats.t.isf | scipy>=1.10 (1.18.1 locked) | the upper quantile of the tail 0.025 with one degree of freedom is tan(0.475 pi) = 12.7062047361747 within 1e-13 relative (spec mean_interval_half_width) | `tests/unit/test_formulas_characteristic.py::test_the_delegated_t_quantile_is_a_known_one` |
| mann_whitney_u | scipy.stats.mannwhitneyu (two-sided, method auto: exact for parts of at most 8 values without ties, else normal with the corrections for ties and continuity) | scipy>=1.10 (1.18.1 locked) | Helsel et al. (2020), Example 5.1: U of the first part 76.5, p = 0.04911 (R's wilcox.test W = 76.5, p = 0.0491099747); the frozen oracle tests/oracles/trend_regime holds R's U and p of three pairs of samples (stats homogeneity) | `tests/unit/test_formulas_trend.py::test_the_delegated_mann_whitney_is_helsels_and_rs` |
| ks_two_sample | scipy.stats.ks_2samp (two-sided, method auto: exact for a continuous distribution) | scipy>=1.10 (1.18.1 locked) | three values all below four others: D = 1, p = 2 / C(7, 3) = 0.0571429; seeded samples without ties against the exact count of spec ks_exact (stats homogeneity without ties) | `tests/unit/test_formulas_trend.py::test_the_delegated_ks_2samp_is_exact_without_ties` |
| rating_curve_least_squares | scipy.optimize.curve_fit (bounds: least_squares, trust region reflective) | scipy>=1.10 (1.18.1 locked) | eight noise-free pairs of Q = 0.012 (H - 32)^1.62 at H = 40 to 270 cm give back a = 0.012, b = 1.62 and H0 = 32 cm within 1e-6 relative (spec rating_curve_fit) | `tests/unit/test_formulas_hydrometrics.py::test_the_delegated_least_squares_recover_a_noise_free_curve` |
| harmonic_least_squares | numpy.linalg.lstsq (LAPACK gelsd) | numpy>=1.24 (2.5.4 locked) | the least squares of an exact signal of two harmonics over five hydrological years recover its mean 10 and amplitudes 5 and 2 within 1e-8 (spec harmonic_fit) | `tests/unit/test_formulas_regime.py::test_the_delegated_least_squares_recover_an_exact_signal` |
