# A. Oznaczenia i jednostki

## Zasady zapisu

- Liczby mają przecinek dziesiętny; tysiące liczb o co najmniej pięciu cyfrach oddziela
  spacja, a potęgi dziesięciu zapisano jako `1·10⁻⁹`.
- Przedział `[a; b]` zawiera swoje krańce, `(a; b)` ich nie zawiera, a `∞` oznacza brak
  ograniczenia. Średnik oddziela krańce, bo przecinek jest dziesiętny.
- Wielkości mają jednostki układu SI z jednostkami dopuszczonymi do stosowania razem z nim
  (minuta, godzina, doba, rok). Wzory wyprowadzone w jednostkach anglosaskich Hydrolog liczy w
  jednostkach ich źródła, przeliczając dane dokładnymi przelicznikami tabeli jednostek
  standardu Nogat (CMP-4.3; BIPM 2019); stąd złożone jednostki niektórych stałych.
- Nazwa argumentu w Hydrologu zawiera jednostkę: `area_km2` (km²), `slope_m_per_m` (m/m),
  `duration_min` (min); opcja wiersza poleceń to ta sama nazwa z łącznikiem zamiast
  podkreślenia (`--area-km2`).
- Symbole pochodzą z równań specyfikacji wzorów. Ten sam symbol bywa w różnych wzorach inną
  wielkością (na przykład $S$ to retencja maksymalna w metodzie SCS-CN, a spadek we wzorze
  Kirpicha), dlatego wykaz symboli podaje znaczenie osobno dla każdego wzoru.

Oba wykazy poniżej są generowane z ramek wzorów, które pokazuje podręcznik (dodatek D, D.7):
obejmują jednostki i symbole tych wzorów i odsyłają do ramek.

## A.1. Jednostki

<!-- generated:units -->

| Jednostka | Zapis w Hydrologu | Nazwa |
|---|---|---|
| % | `%` | procent |
| % na m/m | `% per m/m` | procent na metr na metr (przeliczenie spadku na procenty) |
| – | `-` | wielkość bezwymiarowa |
| 1/% | `1/%` | odwrotność procentu |
| 1/h | `1/h` | odwrotność godziny |
| 1/km² | `1/km2` | odwrotność kilometra kwadratowego |
| 1/min | `1/min` | odwrotność minuty |
| a | `a` | rok |
| cm | `cm` | centymetr |
| d | `d` | doba |
| d/rok | `d/yr` | doba na rok (liczba dni w roku) |
| d | `day` | doba |
| °C | `degC` | stopień Celsjusza |
| $\mathrm{ft^{0{,}8}\,in^{0{,}7}\,h^{-1}\,\%^{0{,}5}}$ | `ft^0.8 in^0.7 h^-1 %^0.5` | jednostka stałej wzoru w stopach, calach, godzinach i procentach |
| h | `h` | godzina |
| $\mathrm{h\,(ft^{3}\,s^{-1}\,mi^{-2}\,in^{-1})^{1{,}08}}$ | `h (ft3 s^-1 mi^-2 in^-1)^1.08` | jednostka stałej wzoru w jednostkach anglosaskich: godziny, stopy sześcienne na sekundę, mile kwadratowe i cale |
| $\mathrm{h\,km^{-0{,}52}}$ | `h km^-0.52` | jednostka parametru empirycznego w godzinach i kilometrach |
| $\mathrm{h\,km^{-0{,}52}\,s^{-1}\,m^{1/3}}$ | `h km^-0.52 s^-1 m^1/3` | jednostka współczynnika empirycznego w godzinach, kilometrach, sekundach i metrach |
| $\mathrm{h\,km^{-0{,}78}\,mm^{0{,}11}\,h^{-0{,}22}}$ | `h km^-0.78 mm^0.11 h^-0.22` | jednostka współczynnika empirycznego w godzinach, kilometrach i milimetrach |
| $\mathrm{h\,km^{-0{,}92}\,mm^{0{,}27}\,h^{-0{,}37}}$ | `h km^-0.92 mm^0.27 h^-0.37` | jednostka współczynnika empirycznego w godzinach, kilometrach i milimetrach |
| $\mathrm{h\,km^{-1}\,m^{0{,}5}}$ | `h km^-1 m^0.5` | jednostka współczynnika empirycznego w godzinach, kilometrach i metrach |
| $\mathrm{h\,m^{3}\,s^{-1}\,km^{-2}\,mm^{-1}}$ | `h m3 s^-1 km^-2 mm^-1` | godzina razy metr sześcienny na sekundę na kilometr kwadratowy i milimetr opadu |
| $\mathrm{h^{0{,}04}}$ | `h^0.04` | jednostka współczynnika empirycznego w godzinach |
| in | `in` | cal |
| km | `km` | kilometr |
| km/km² | `km/km2` | kilometr na kilometr kwadratowy |
| km² | `km2` | kilometr kwadratowy |
| m | `m` | metr |
| m/m | `m/m` | metr na metr (spadek) |
| m/s | `m/s` | metr na sekundę |
| m² | `m2` | metr kwadratowy |
| m³ | `m3` | metr sześcienny |
| $\mathrm{m^{3}\,s^{-1}\,km^{-2}\,cm^{-1}\,h}$ | `m3 s^-1 km^-2 cm^-1 h` | metr sześcienny na sekundę na kilometr kwadratowy i centymetr opadu, razy godzina |
| $\mathrm{m^{3}\,s^{-1}\,km^{-2}\,mm^{-1}\,h}$ | `m3 s^-1 km^-2 mm^-1 h` | metr sześcienny na sekundę na kilometr kwadratowy i milimetr opadu, razy godzina |
| m³/s | `m3/s` | metr sześcienny na sekundę |
| $\mathrm{m^{3}/s\text{ na }cm^{b}}$ | `m3/s per cm^b` | metr sześcienny na sekundę na centymetr podniesiony do wykładnika b krzywej |
| m³/s na mm | `m3/s per mm` | metr sześcienny na sekundę na milimetr opadu efektywnego |
| m³/s/a | `m3/s/a` | metr sześcienny na sekundę na rok |
| min | `min` | minuta |
| $\mathrm{min\,ft^{-0{,}5}\,\%^{1/3}}$ | `min ft^-0.5 %^(1/3)` | jednostka stałej wzoru w minutach, stopach i procentach |
| $\mathrm{min\,ft^{-0{,}77}}$ | `min ft^-0.77` | jednostka stałej wzoru w minutach i stopach |
| $\mathrm{min^{1/0{,}467}\,ft^{-1}}$ | `min^(1/0.467) ft^-1` | jednostka stałej wzoru w minutach i stopach |
| mm | `mm` | milimetr |
| mm/(°C·d) | `mm/(°C·d)` | milimetr na stopień Celsjusza i dobę |
| mm/h | `mm/h` | milimetr na godzinę |
| mies. | `month` | miesiąc kalendarzowy (jego numer) |
| $\mathrm{s\,m^{-1/3}}$ | `s m^-1/3` | sekunda na metr do potęgi jednej trzeciej (jednostka współczynnika Manninga) |
| s/d | `s/d` | sekundy na dobę |
| $\mathrm{s/m^{1/3}}$ | `s/m^(1/3)` | sekunda na metr do potęgi jednej trzeciej (jednostka współczynnika Manninga) |
| wspólna | `shared unit` | jednostka wspólna trzech frakcji (procent albo g/kg) |
| wartości | `values` | liczba wartości |
| lata | `years` | lata |
| °C | `°C` | stopień Celsjusza |
| °C·d | `°C·d` | stopniodzień (stopień Celsjusza razy doba) |

<!-- /generated:units -->

## A.2. Symbole

<!-- generated:symbols -->

| Symbol | Znaczenie | Jednostka | Wzory |
|---|---|---|---|
| $1/\alpha_W$ | Parametr skali | m³/s | [`weibull_quantiles`](07-przeplywy-maksymalne.md#spec-weibull_quantiles) |
| $a$ | Formuła pozycji wykreślnej: Weibulla, Hazena lub Cunnane'a | – | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions), [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $a$ | Parametr a formuły pozycji wykreślnej Cunnane'a | – | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions), [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $a$ | Parametr a formuły pozycji wykreślnej Hazena | – | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions), [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $a$ | Parametr a formuły pozycji wykreślnej Weibulla | – | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions), [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $A$ | Pole przekroju przepływu przy głębokości normalnej | m² | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $A$ | Powierzchnia zlewni | km² | [`giandotti`](04-czas-koncentracji.md#spec-giandotti), [`scs`](05-hydrogram-jednostkowy.md#spec-scs), [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder), [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape), [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression), [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $A$ | Powierzchnia zlewni w rzucie poziomym | km² | [`form_factor`](01-zlewnia.md#spec-form_factor), [`compactness_coefficient`](01-zlewnia.md#spec-compactness_coefficient), [`circularity_ratio`](01-zlewnia.md#spec-circularity_ratio), [`elongation_ratio`](01-zlewnia.md#spec-elongation_ratio), [`lemniscate_ratio`](01-zlewnia.md#spec-lemniscate_ratio), [`drainage_density`](01-zlewnia.md#spec-drainage_density), [`stream_frequency`](01-zlewnia.md#spec-stream_frequency) |
| $a$ | Przepływ przy wysokości H - H0 równej jednej jednostce H (C według WMO) | $\mathrm{m^{3}/s\text{ na }cm^{b}}$ | [`rating_curve`](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| $a$ | Przepływ przy wysokości równej jednej jednostce H | $\mathrm{m^{3}/s\text{ na }cm^{b}}$ | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $a$ | Wyraz wolny Conovera: wartość prostej w czasie 0 (w roku 0 przy latach) | m³/s | [`sen_slope`](10-jednorodnosc-i-trend.md#spec-sen_slope) |
| $A_0$ | Średnia dopasowanego cyklu, w jednostce wartości | °C | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $A_1$ | Współczynnik liniowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $A^2$ | Statystyka: n razy całka z kwadratu różnicy dystrybuanty empirycznej i dopasowanej, ważona przez 1 / (F (1 - F)) | – | [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling) |
| $A_2$ | Współczynnik kwadratowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $A_3$ | Współczynnik sześcienny mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy małej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $A_i$ | Powierzchnia każdego pasa między dwiema kolejnymi izohietami | km² | [`isohyet_precipitation`](02-opad.md#spec-isohyet_precipitation) |
| $A_i$ | Powierzchnia wieloboku każdego posterunku w granicach zlewni | km² | [`thiessen_precipitation`](02-opad.md#spec-thiessen_precipitation) |
| $A_j$ | Powierzchnia każdej komórki w dowolnej jednej jednostce (liczą się tylko udziały) | – | [`hypsometric_integral`](01-zlewnia.md#spec-hypsometric_integral) |
| $\alpha$ | Parametr filtru | – | [`lyne_hollick`](08-przeplywy-charakterystyczne-nizowki.md#spec-lyne_hollick) |
| $\alpha$ | Parametr kształtu rozkładu gamma (`spi_gamma_fit`) | – | [`spi`](11-wskazniki-meteorologiczne.md#spec-spi) |
| $\alpha$ | Parametr skali | m³/s | [`gev_quantiles`](07-przeplywy-maksymalne.md#spec-gev_quantiles), [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling), [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion), [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta), [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $\alpha$ | Parametr skali; wartość, która uległaby niedomiarowi, zastępuje się najmniejszą liczbą float64 (tolerancja brzegowa) | m³/s | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments), [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_maximum_likelihood`](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares) |
| $\alpha$ | Pierwszy parametr kształtu (r w KZGW): narastanie deszczu | – | [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph) |
| $\alpha$ | Poziom istotności: przedział ufności obejmuje 1 - alpha | – | [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $ARC$ | Warunki wilgotnościowe poprzedzające, na które przelicza się CN: I suche, III wilgotne | – | [`scs_cn_amc`](03-opad-efektywny.md#spec-scs_cn_amc) |
| $B$ | Liczba prób bootstrapu | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap) |
| $b$ | Nachylenie Sena: mediana nachyleń par o różnych czasach, w jednostce wartości na jednostkę czasu | m³/s/a | [`sen_slope`](10-jednorodnosc-i-trend.md#spec-sen_slope) |
| $b$ | Szerokość dna przekroju; zero dla trójkąta | m | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $b$ | Wykładnik krzywej | – | [`rating_curve_plausibility`](09-rezim-i-zmiennosc.md#spec-rating_curve_plausibility) |
| $b$ | Wykładnik wysokości nad stanem przepływu zerowego | – | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $b$ | Wykładnik wysokości nad stanem przepływu zerowego (beta według WMO) | – | [`rating_curve`](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| $B_1$ | Współczynnik liniowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $B_2$ | Współczynnik kwadratowy licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $B_3$ | Współczynnik sześcienny licznika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $\bar L_u$ | Średnia długość cieków rzędu u według Strahlera | km | [`length_ratio`](01-zlewnia.md#spec-length_ratio) |
| $\bar L_{u+1}$ | Średnia długość cieków rzędu u + 1 według Strahlera | km | [`length_ratio`](01-zlewnia.md#spec-length_ratio) |
| $\bar{P}$ | Średni opad w zlewni | mm | [`areal_mean_precipitation`](02-opad.md#spec-areal_mean_precipitation), [`thiessen_precipitation`](02-opad.md#spec-thiessen_precipitation), [`isohyet_precipitation`](02-opad.md#spec-isohyet_precipitation) |
| $\bar{Q}$ | Średni przepływ ze wszystkich dni z wartością | m³/s | [`parde_coefficients`](09-rezim-i-zmiennosc.md#spec-parde_coefficients) |
| $\bar{Q}_m$ | Średni przepływ każdego miesiąca, od listopada do października | m³/s | [`parde_coefficients`](09-rezim-i-zmiennosc.md#spec-parde_coefficients), [`spring_share`](09-rezim-i-zmiennosc.md#spec-spring_share) |
| $\bar{x}$ | Średnia arytmetyczna | m³/s | [`sample_moments`](07-przeplywy-maksymalne.md#spec-sample_moments) |
| $\beta$ | Drugi parametr kształtu (s w KZGW): zanikanie deszczu | – | [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph) |
| $\beta$ | Parametr skali rozkładu gamma (`spi_gamma_fit`) | mm | [`spi`](11-wskazniki-meteorologiczne.md#spec-spi) |
| $\beta_W$ | Parametr kształtu k rozkładu | – | [`weibull_quantiles`](07-przeplywy-maksymalne.md#spec-weibull_quantiles) |
| $BFI$ | Udział przepływu podstawowego w objętości przepływu | – | [`baseflow_index`](08-przeplywy-charakterystyczne-nizowki.md#spec-baseflow_index) |
| $b_L$ | Dolna granica przedziału nachylenia | m³/s/a | [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $b_t$ | Przepływ podstawowy każdego dnia, w jednostce szeregu | m³/s | [`lyne_hollick`](08-przeplywy-charakterystyczne-nizowki.md#spec-lyne_hollick) |
| $b_t$ | Przepływ podstawowy tych samych dni; luka oznacza dzień bez wartości | m³/s | [`baseflow_index`](08-przeplywy-charakterystyczne-nizowki.md#spec-baseflow_index) |
| $b_U$ | Górna granica przedziału nachylenia | m³/s/a | [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $c$ | Parametr kształtu c funkcji genextreme biblioteki scipy dla zanegowanych minimów: dolne ograniczenie minimów loc - scale / c dla c > 0 | – | [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $c$ | Parametr kształtu c: górne ograniczenie dla c > 0, ciężki górny ogon dla c < 0 | – | [`gev_quantiles`](07-przeplywy-maksymalne.md#spec-gev_quantiles) |
| $c$ | Poziomy ufności, różne: każdy przedział jest dwustronny i centralny, każdy ogon (1 - c) / 2 | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $c$ | Poziomy ufności, różne: każdy przedział jest dwustronny i centralny, każdy ogon najwyżej (1 - c) / 2 | – | [`duration_curve_annual_median_interval`](08-przeplywy-charakterystyczne-nizowki.md#spec-duration_curve_annual_median_interval) |
| $c$ | Prędkość fali wezbraniowej przy przepływie odniesienia | m/s | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $c$ | Prędkość kinematycznej fali wezbraniowej, dQ/dA przy stałym spadku | m/s | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $C$ | Stosunek odpływu bezpośredniego do opadu | – | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $C$ | Współczynnik przepływu kulminacyjnego (współczynnik szczytu) | $\mathrm{m^{3}\,s^{-1}\,km^{-2}\,cm^{-1}\,h}$ | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $C$ | Współczynnik spływu metody racjonalnej | – | [`faa`](04-czas-koncentracji.md#spec-faa) |
| $c_0$ | Waga I[t] w jednym kroku przestrzennego | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $c_0$ | Waga I[t] w jednym pododcinku | – | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $c_1$ | Waga I[t-1] w jednym kroku przestrzennego | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $c_1$ | Waga I[t-1] w jednym pododcinku | – | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $C_1$ | Współczynnik liniowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $c_2$ | Waga O[t-1] w jednym kroku przestrzennego | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $c_2$ | Waga O[t-1] w jednym pododcinku | – | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $C_2$ | Współczynnik kwadratowy mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $C_3$ | Współczynnik sześcienny mianownika aproksymacji wymiernej parametru alfa rozkładu Pearsona III przy dużej L-skośności | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $C_e$ | Wskaźnik wydłużenia: średnica koła o tej samej powierzchni podzielona przez długość zlewni; 1 dla koła o średnicy L | – | [`elongation_ratio`](01-zlewnia.md#spec-elongation_ratio) |
| $C_f$ | Wskaźnik formy: powierzchnia podzielona przez kwadrat długości; pi/4 dla koła o średnicy L | – | [`form_factor`](01-zlewnia.md#spec-form_factor) |
| $C_g$ | Liczba Couranta siatki, c dt / dx | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $C_k$ | Amplituda każdej harmoniki, w jednostce wartości | °C | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $C_k$ | Wskaźnik kolistości: powierzchnia zlewni podzielona przez powierzchnię koła o tym samym obwodzie; 1 dla koła | – | [`circularity_ratio`](01-zlewnia.md#spec-circularity_ratio) |
| $CN$ | Liczba CN dla AMC II, zastępująca współczynnik oporu cn' | – | [`nrcs`](04-czas-koncentracji.md#spec-nrcs) |
| $CN$ | Liczba CN dla ARC II i Ia = 0,2 S | – | [`tr55_cn`](03-opad-efektywny.md#spec-tr55_cn) |
| $CN$ | Liczba CN dla warunków wilgotnościowych poprzedzających przyjętych we wzorze | – | [`scs_cn_retention`](03-opad-efektywny.md#spec-scs_cn_retention), [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff), [`scs_cn_amc`](03-opad-efektywny.md#spec-scs_cn_amc) |
| $CN_x$ | Liczba CN dla tych warunków | – | [`scs_cn_amc`](03-opad-efektywny.md#spec-scs_cn_amc) |
| $C_p$ | Współczynnik kulminacji | – | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $C_t$ | Współczynnik czasowy w jednostkach SI | – | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $C_z$ | Wskaźnik zwartości: obwód zlewni podzielony przez obwód koła o tej samej powierzchni; 1 dla koła | – | [`compactness_coefficient`](01-zlewnia.md#spec-compactness_coefficient) |
| $D$ | Czas trwania jednostkowego opadu efektywnego | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder), [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $D$ | Czas trwania opadu efektywnego | h | [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $d$ | Dzień roku hydrologicznego każdej wartości, 1 = 1 listopada | d | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $d$ | Dzień roku, licząc od 1, w którym przepływ zsumowany od pierwszego dnia po raz pierwszy przekracza połowę sumy roku | d | [`half_flow_date`](08-przeplywy-charakterystyczne-nizowki.md#spec-half_flow_date) |
| $D$ | Krok czasowy hydrogramu i czas trwania jego jednostkowego opadu efektywnego | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $D$ | Liczba dni powyżej progu | d | [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $D$ | Największa odległość między dystrybuantami prób | – | [`ks_exact`](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| $D_d$ | Gęstość sieci rzecznej | km/km² | [`drainage_density`](01-zlewnia.md#spec-drainage_density) |
| $\Delta P_i$ | Wysokość opadu w każdym kroku czasowym (suma to jeden krok) | mm | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $\Delta t$ | Krok czasowy dopływu i odpływu | min | [`lag`](06-transformacja-fali.md#spec-lag), [`muskingum`](06-transformacja-fali.md#spec-muskingum), [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge), [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade), [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $\Delta t$ | Krok czasowy opadu i hydrogramu jednostkowego | min | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $\Delta t$ | Krok czasowy rzędnych | min | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape), [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $\Delta t$ | Krok czasowy rzędnych i zbiornika | min | [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $\Delta t$ | Krok czasowy: długość każdego bloku deszczu | min | [`block_hyetograph`](02-opad.md#spec-block_hyetograph), [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph), [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph), [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $\Delta x$ | Krok przestrzenny L / N | m | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $D_g$ | Siatkowa liczba Reynoldsa D / dx = 1 - 2X | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $D_h$ | Średnia długość ciągów takich dni, 0 bez żadnego | d | [`high_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-high_flow_days) |
| $D_i$ | Czasy trwania punktów krzywej wysokość–czas trwania, rosnące | min | [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $d_{II}$ | Liczba dni lutego w roku średnim | d | [`spring_share`](09-rezim-i-zmiennosc.md#spec-spring_share) |
| $d_k$ | Dzień roku hydrologicznego pierwszego maksimum każdej harmoniki | d | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $D_l$ | Średnia długość ciągów takich dni, 0 bez żadnego | d | [`low_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-low_flow_days) |
| $e$ | Granice klas stanów, rosnące | cm | [`rybczynski_zones`](09-rezim-i-zmiennosc.md#spec-rybczynski_zones) |
| $e$ | Maksima albo minima dopasowane jako rozkład GEV zanegowanych minimów (fisher_tippett_minima: jego parametr położenia odnosi się do minimów) | – | [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $e^{2{,}3 C_g}$ | Granica dokładności siatkowej liczby Reynoldsa według NEH, exp(2,3 Cg), ograniczona do exp(700) | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $\ell$ | Długość spływu: najdłuższa droga, którą woda spływa od działu wodnego do przekroju | km | [`nrcs`](04-czas-koncentracji.md#spec-nrcs) |
| $e^{\mu}$ | Funkcja wykładnicza (exp) średniej logarytmów | m³/s | [`log_normal_quantiles`](07-przeplywy-maksymalne.md#spec-log_normal_quantiles) |
| $\epsilon$ | Dolne ograniczenie | m³/s | [`weibull_quantiles`](07-przeplywy-maksymalne.md#spec-weibull_quantiles) |
| $\epsilon$ | Dolne ograniczenie: 0 dla rozkładu dwuparametrowego dopasowywanego w Hydrologu | m³/s | [`log_normal_quantiles`](07-przeplywy-maksymalne.md#spec-log_normal_quantiles) |
| $\epsilon$ | Margines obcięcia dystrybuanty F od zera i od jedności | – | [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling) |
| $f$ | Kierunek średniego wektora jako ułamek roku | – | [`circular_mean`](09-rezim-i-zmiennosc.md#spec-circular_mean) |
| $F$ | Rozkład: logarytmiczno-normalny o parametrze położenia 0, GEV, Pearsona typu III lub trójparametrowy rozkład Weibulla z scipy.stats | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments), [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_maximum_likelihood`](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares), [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling), [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion), [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $f$ | Waga wcześniejszej rzędnej: część kroku, o którą przesunięcie odbiega od całkowitej liczby kroków | – | [`lag`](06-transformacja-fali.md#spec-lag) |
| $f_0$ | Udział dni bez przepływu wśród dni z wartością | – | [`zero_flow_fraction`](08-przeplywy-charakterystyczne-nizowki.md#spec-zero_flow_fraction) |
| $F_h$ | Liczba dni poza progiem na rok dni z wartością | d/rok | [`high_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-high_flow_days) |
| $F_i$ | Prawdopodobieństwo nieprzewyższenia każdej wartości | – | [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $F_l$ | Liczba dni poza progiem na rok dni z wartością | d/rok | [`low_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-low_flow_days) |
| $F_s$ | Wskaźnik częstości cieków | 1/km² | [`stream_frequency`](01-zlewnia.md#spec-stream_frequency) |
| $G$ | Skorygowany współczynnik skośności Fishera–Pearsona | – | [`sample_moments`](07-przeplywy-maksymalne.md#spec-sample_moments) |
| $\gamma$ | Skośność rozkładu | – | [`pearson3_quantiles`](07-przeplywy-maksymalne.md#spec-pearson3_quantiles) |
| $\Gamma'(2)$ | Wartość pochodnej funkcji gamma w punkcie dwa | – | [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $\gamma_G$ | Skośność rozkładu Gumbela | – | [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares) |
| $h$ | Natężenie w szczycie trójkąta | mm/h | [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph) |
| $H$ | Stan wody H każdego pomiaru przepływu, w jednej jednostce stanów | cm | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $H$ | Stany par, do których dopasowano krzywą | cm | [`rating_curve_plausibility`](09-rezim-i-zmiennosc.md#spec-rating_curve_plausibility) |
| $H$ | Stany wody H, przy których odczytuje się przepływ, w jednostce stanów krzywej | cm | [`rating_curve`](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| $H$ | Wysokość opadu efektywnego danego deszczu | mm | [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $H$ | Średnia wysokość zlewni ponad przekrojem | m | [`giandotti`](04-czas-koncentracji.md#spec-giandotti) |
| $h(T_d)$ | Całkowita wysokość deszczu, wysokość krzywej dla Td | mm | [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $H_0$ | Stan przepływu zerowego albo efektywnego przepływu zerowego (e według WMO) | cm | [`rating_curve`](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| $H_0$ | Stan przepływu zerowego krzywej | cm | [`rating_curve_plausibility`](09-rezim-i-zmiennosc.md#spec-rating_curve_plausibility) |
| $H_0$ | Stan przepływu zerowego, poniżej każdego stanu | cm | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $H_{0,start}$ | Punkt startowy poszukiwania H0, poniżej każdego stanu | cm | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $\hat{\alpha}$ | Parametr kształtu rozkładu gamma sum dodatnich | – | [`spi_gamma_fit`](11-wskazniki-meteorologiczne.md#spec-spi_gamma_fit) |
| $\hat{\beta}$ | Parametr skali tego rozkładu | mm | [`spi_gamma_fit`](11-wskazniki-meteorologiczne.md#spec-spi_gamma_fit) |
| $HI$ | Pole pod procentową krzywą hipsometryczną w kwadracie jednostkowym | – | [`hypsometric_integral`](01-zlewnia.md#spec-hypsometric_integral) |
| $h_i$ | Wysokości krzywej dla tych czasów trwania, jednego prawdopodobieństwa | mm | [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $H_{max}$ | Najwyższa wysokość zlewni [m n.p.m.] | m | [`relief_ratio`](01-zlewnia.md#spec-relief_ratio) |
| $H_{min}$ | Najniższa wysokość zlewni, czyli wysokość jej ujścia [m n.p.m.] | m | [`relief_ratio`](01-zlewnia.md#spec-relief_ratio) |
| $H_{NTW}$ | Górna granica niskiego tła wodnego (NTW) | cm | [`rybczynski_zones`](09-rezim-i-zmiennosc.md#spec-rybczynski_zones) |
| $H_{STW}$ | Górna granica średniego tła wodnego (STW) | cm | [`rybczynski_zones`](09-rezim-i-zmiennosc.md#spec-rybczynski_zones) |
| $I_a$ | Straty początkowe Ia | mm | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $i \Delta t$ | Chwile rzędnych liczone od początku opadu | min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $I_t$ | Dopływ w chwilach t = 0, dt, 2 dt, ...: hydrogram wpływający do odcinka, liniowy między rzędnymi | m³/s | [`lag`](06-transformacja-fali.md#spec-lag), [`muskingum`](06-transformacja-fali.md#spec-muskingum), [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge), [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade), [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $Jg$ | Spadek profilu podłużnego cieku głównego uśredniony metodą równych pól (specyfikacja `equal_area_slope`), a nie spadek między jego końcami | m/m | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $K$ | Czas przepływu L / c przez cały odcinek | min | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $K$ | Czas przepływu przez cały odcinek, stała retencji K | min | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $k$ | Dobowa stała recesji przepływu całkowitego | – | [`recession_constant`](08-przeplywy-charakterystyczne-nizowki.md#spec-recession_constant) |
| $K$ | Liczba dopasowywanych harmonik | – | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $k$ | Parametr kształtu: s rozkładu logarytmiczno-normalnego, c rozkładu GEV (znak jak w scipy, k Hoskinga, -xi Colesa), skośność rozkładu Pearsona III, parametr kształtu rozkładu Weibulla | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments), [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_maximum_likelihood`](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares), [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling), [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion), [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $K$ | Statystyka Pettitta, największe \|U_t\| | – | [`pettitt`](10-jednorodnosc-i-trend.md#spec-pettitt) |
| $K$ | Stała retencji jednego zbiornika | min | [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| $K$ | Stała retencji każdego zbiornika | min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`nash_iuh_peak`](05-hydrogram-jednostkowy.md#spec-nash_iuh_peak), [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $k$ | Stała retencji każdego zbiornika | min | [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $k$ | Wskaźnik lemniskaty: powierzchnia koła o średnicy L podzielona przez powierzchnię zlewni; 1 dla tego koła, większy dla zlewni bardziej wydłużonych | – | [`lemniscate_ratio`](01-zlewnia.md#spec-lemniscate_ratio) |
| $k$ | Współczynnik hydrotermiczny | – | [`sielianinov_coefficient`](11-wskazniki-meteorologiczne.md#spec-sielianinov_coefficient), [`sielianinov_class`](11-wskazniki-meteorologiczne.md#spec-sielianinov_class) |
| $K$ | Wykładnik krzywej | – | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $K$ | Zachowane próby bootstrapu: dopasowane ponownie metodą L-momentów | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap) |
| $k\,\Delta t$ | Początek przedziału szczytu liczony od początku deszczu | min | [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $k D$ | Chwile rzędnych liczone od początku opadu efektywnego | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $k \Delta t$ | Chwile rzędnych liczone od początku opadu | min | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $k_{I}$ | Stosunek retencji maksymalnej w warunkach I do retencji w warunkach II | – | [`scs_cn_amc`](03-opad-efektywny.md#spec-scs_cn_amc) |
| $k_{III}$ | Stosunek retencji maksymalnej w warunkach III do retencji w warunkach II | – | [`scs_cn_amc`](03-opad-efektywny.md#spec-scs_cn_amc) |
| $K_m$ | Współczynnik Pardégo każdego miesiąca, od listopada do października | – | [`parde_coefficients`](09-rezim-i-zmiennosc.md#spec-parde_coefficients) |
| $K_m$ | Współczynniki Pardégo miesięcy od listopada do października | – | [`dynowska_regime_type`](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| $K_{min}$ | Najmniejsza liczba zachowanych prób, przy której przedział jest wyznaczany | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap) |
| $L$ | Dolna granica dla każdego poziomu (wiersz na poziom, w podanej kolejności) i okresu powtarzalności; luka tam, gdzie granica przepływu byłaby poniżej 0 | m³/s | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $L$ | Długość cieku głównego | km | [`giandotti`](04-czas-koncentracji.md#spec-giandotti) |
| $L$ | Długość cieku głównego od przekroju zamykającego do działu wodnego | km | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $L$ | Długość najdłuższej drogi spływu, od przekroju do punktu zlewni najdalszego hydraulicznie | km | [`kirpich`](04-czas-koncentracji.md#spec-kirpich) |
| $L$ | Długość odcinka | km | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $L$ | Długość spływu po stoku (warstwą), od najdalszego punktu do wyraźnego koryta lub wpustu | km | [`faa`](04-czas-koncentracji.md#spec-faa), [`kerby`](04-czas-koncentracji.md#spec-kerby) |
| $L$ | Długość wzdłuż cieku głównego od przekroju zamykającego do działu wodnego: najdłuższa droga spływu | km | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $L$ | Długość zlewni: odcinek prosty od ujścia do najdalszego punktu działu wodnego albo najdłuższa droga spływu przekazana przez Hydrograf | km | [`form_factor`](01-zlewnia.md#spec-form_factor), [`elongation_ratio`](01-zlewnia.md#spec-elongation_ratio), [`lemniscate_ratio`](01-zlewnia.md#spec-lemniscate_ratio), [`relief_ratio`](01-zlewnia.md#spec-relief_ratio) |
| $L_1$ | Najmniejszy współczynnik miesiąca letniego w reżimie niwalno-pluwialnym | – | [`dynowska_regime_type`](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| $LAG$ | Czas opóźnienia hydrogramu jednostkowego chwilowego, N K | h | [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $\lambda$ | Współczynnik strat początkowych Ia / S | – | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $\lambda_1$ | Pierwszy L-moment, średnia | m³/s | [`sample_l_moments`](07-przeplywy-maksymalne.md#spec-sample_l_moments) |
| $\lambda_2$ | Drugi L-moment, połowa średniej różnicy dwóch wartości | m³/s | [`sample_l_moments`](07-przeplywy-maksymalne.md#spec-sample_l_moments) |
| $Lc$ | Długość wzdłuż cieku głównego od przekroju zamykającego do jego punktu najbliższego środkowi ciężkości zlewni | km | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $L_c$ | Długość wzdłuż cieku głównego od przekroju zamykającego do punktu najbliższego środkowi ciężkości zlewni | km | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $L_{fp}$ | Długość cieku głównego w rozumieniu metody: najdłuższa droga spływu od działu wodnego do przekroju, łącznie z odcinkiem po stoku | km | [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $L_i$ | Długość roku każdej daty, w jednostce terminów | d | [`circular_mean`](09-rezim-i-zmiennosc.md#spec-circular_mean) |
| $L_{ov}$ | Długość spływu po stoku (warstwą), od najdalszego punktu do wyraźnego koryta lub wpustu | km | [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $L_t$ | Liczba dni ciągu kończącego się w danym dniu, 0 w każdym innym dniu | d | [`spell_lengths`](11-wskazniki-meteorologiczne.md#spec-spell_lengths) |
| $M$ | Magnituda odcinka poniżej węzła według Shreve'a, czyli liczba źródeł powyżej niego | – | [`shreve_magnitude`](01-zlewnia.md#spec-shreve_magnitude) |
| $m$ | Najkrótszy odcinek recesji: liczba spadków z rzędu | d | [`recession_constant`](08-przeplywy-charakterystyczne-nizowki.md#spec-recession_constant) |
| $\mathrm{AIC}$ | Kryterium: im mniejsze, tym lepsze dopasowanie przy danej liczbie parametrów | – | [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion) |
| $\mathrm{class}$ | Klasa uziarnienia USDA (specyfikacja `usda_texture`) | – | [`texture_hsg`](03-opad-efektywny.md#spec-texture_hsg) |
| $\mathrm{class}$ | Klasa uziarnienia USDA, jedna z dwunastu klas Soil Survey Manual | – | [`usda_texture`](03-opad-efektywny.md#spec-usda_texture) |
| $\mathrm{GDD}$ | Stopniodni wzrostu każdej doby | °C·d | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $\mathrm{HDD}$ | Stopniodni grzania każdej doby | °C·d | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $\mathrm{HSG}$ | Grupa hydrologiczna gleby, od A (mały potencjał odpływu) do D (duży) | – | [`texture_hsg`](03-opad-efektywny.md#spec-texture_hsg) |
| $\mathrm{PCI}$ | Wskaźnik koncentracji opadów | – | [`pci_class`](11-wskazniki-meteorologiczne.md#spec-pci_class) |
| $\mathrm{PCI}$ | Wskaźnik: 100/12 przy równych miesiącach, 100 przy jednym miesiącu z opadem | – | [`precipitation_concentration_index`](11-wskazniki-meteorologiczne.md#spec-precipitation_concentration_index) |
| $\mathrm{PRCPTOT}$ | Suma opadu dni z opadem | mm | [`sdii`](11-wskazniki-meteorologiczne.md#spec-sdii), [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $\mathrm{SDII}$ | Średni opad dnia z opadem | mm | [`sdii`](11-wskazniki-meteorologiczne.md#spec-sdii) |
| $\mathrm{SI}$ | Wskaźnik sezonowości | – | [`si_class`](11-wskazniki-meteorologiczne.md#spec-si_class) |
| $\mathrm{SI}$ | Wskaźnik: 0 dla równych miesięcy, 11/6 dla jednego miesiąca z opadem | – | [`seasonality_index`](09-rezim-i-zmiennosc.md#spec-seasonality_index) |
| $\mathrm{SPI}$ | SPI każdej sumy | – | [`spi`](11-wskazniki-meteorologiczne.md#spec-spi) |
| $m_d$ | Miesiąc kalendarzowy każdego dnia, styczeń = 1 | – | [`parde_coefficients`](09-rezim-i-zmiennosc.md#spec-parde_coefficients) |
| $M_i$ | Magnitudy według Shreve'a odcinków wpadających do danego odcinka; lista pusta dla odcinka źródłowego | – | [`shreve_magnitude`](01-zlewnia.md#spec-shreve_magnitude) |
| $m_\mathrm{clay}$ | Zawartość iłu (< 0,002 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [`usda_texture`](03-opad-efektywny.md#spec-usda_texture) |
| $m_\mathrm{sand}$ | Zawartość piasku (0,05 do 2 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [`usda_texture`](03-opad-efektywny.md#spec-usda_texture) |
| $m_\mathrm{silt}$ | Zawartość pyłu (0,002 do 0,05 mm) w częściach ziemistych, w dowolnej jednostce wspólnej dla trzech zawartości (procent, g/kg); nie muszą one sumować się do 100 | wspólna | [`usda_texture`](03-opad-efektywny.md#spec-usda_texture) |
| $m n$ | Graniczny iloczyn liczebności prób dla testu dokładnego | – | [`ks_exact`](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| $\mu$ | Średnia rozkładu | m³/s | [`pearson3_quantiles`](07-przeplywy-maksymalne.md#spec-pearson3_quantiles) |
| $N$ | Liczba jednakowych kroków przestrzennych dx = L / N | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $N$ | Liczba jednakowych pododcinków o stałej K / N połączonych szeregowo | – | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $n$ | Liczba jednakowych zbiorników połączonych szeregowo; nie musi być całkowita | – | [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| $n$ | Liczba równo rozmieszczonych wysokości względnych krzywej | – | [`hypsometric_integral`](01-zlewnia.md#spec-hypsometric_integral) |
| $n$ | Liczba stanów w każdej klasie | – | [`rybczynski_zones`](09-rezim-i-zmiennosc.md#spec-rybczynski_zones) |
| $n$ | Liczba wartości próby, do której dopasowano rozkład | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap) |
| $N$ | Liczba zbiorników kaskady Nasha | – | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz), [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $n$ | Liczba zbiorników kaskady, parametr kształtu; nie musi być całkowita | – | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`nash_iuh_peak`](05-hydrogram-jednostkowy.md#spec-nash_iuh_peak) |
| $N$ | Liczba zbiorników połączonych szeregowo, z których każdy mieści S / N z tabeli przy tym samym odpływie | – | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $N$ | Przejścia filtru, na przemian naprzód i wstecz | – | [`lyne_hollick`](08-przeplywy-charakterystyczne-nizowki.md#spec-lyne_hollick) |
| $N$ | Współczynnik oporu (retardacji) Kerby'ego dla powierzchni stoku, nie współczynnik Manninga n | – | [`kerby`](04-czas-koncentracji.md#spec-kerby), [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $n$ | Współczynnik szorstkości Manninga dla całego obwodu zwilżonego | $\mathrm{s/m^{1/3}}$ | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $N'$ | Liczba par o różnych czasach | – | [`sen_slope`](10-jednorodnosc-i-trend.md#spec-sen_slope) |
| $n_0$ | Liczba wartości, od której wartość p wyznacza się z przybliżenia normalnego | wartości | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $nM$ | Współczynnik szorstkości Manninga koryta głównego | $\mathrm{s\,m^{-1/3}}$ | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $N_u$ | Liczba cieków rzędu u według Strahlera | – | [`bifurcation_ratio`](01-zlewnia.md#spec-bifurcation_ratio) |
| $N_{u+1}$ | Liczba cieków rzędu u + 1 według Strahlera | – | [`bifurcation_ratio`](01-zlewnia.md#spec-bifurcation_ratio) |
| $O_0$ | Odpływ w pierwszej rzędnej; odcinek startuje z nim w stanie ustalonym | m³/s | [`lag`](06-transformacja-fali.md#spec-lag), [`muskingum`](06-transformacja-fali.md#spec-muskingum), [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge), [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade), [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $O_i$ | Odpływ w każdym wierszu tabeli, niemalejący; zero poniżej korony przelewu | m³/s | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $\operatorname{Var}(S)$ | Wariancja S przy braku trendu, z poprawką na grupy wartości równych; 0 dla szeregu wartości równych | – | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $\operatorname{Var}(S)$ | Wariancja statystyki S Kendalla, na której opiera się przedział: wariancja z testu Manna–Kendalla tych wartości, z poprawką na wiązania (wzór 16.3 Gilberta albo wzór 16.5 przy kilku wartościach z jednego czasu) | – | [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $O_t$ | Odpływ w rzędnych dopływu | m³/s | [`lag`](06-transformacja-fali.md#spec-lag), [`muskingum`](06-transformacja-fali.md#spec-muskingum), [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge), [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade), [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $P$ | Całkowita wysokość deszczu | mm | [`block_hyetograph`](02-opad.md#spec-block_hyetograph), [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph), [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph) |
| $p$ | Dokładna dwustronna wartość p hipotezy, że obie próby pochodzą z jednego rozkładu | – | [`ks_exact`](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| $p$ | Dwustronna wartość p hipotezy braku trendu; wartość mniejszą od najmniejszej dodatniej liczby zmiennoprzecinkowej zastępuje się tą liczbą | – | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $P$ | Obwód zlewni, czyli długość jej działu wodnego | km | [`compactness_coefficient`](01-zlewnia.md#spec-compactness_coefficient), [`circularity_ratio`](01-zlewnia.md#spec-circularity_ratio) |
| $P$ | Okres cyklu rocznego, długość roku średniego | d | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $P$ | Opad miesiąca lub sezonu | mm | [`sielianinov_coefficient`](11-wskazniki-meteorologiczne.md#spec-sielianinov_coefficient) |
| $P$ | Opad w punkcie | mm | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $p$ | Percentyl | % | [`wet_day_percentile`](11-wskazniki-meteorologiczne.md#spec-wet_day_percentile) |
| $p$ | Procenty dni, w których wartość jest osiągana lub przekraczana | % | [`exceedance_values`](08-przeplywy-charakterystyczne-nizowki.md#spec-exceedance_values) |
| $p$ | Przybliżona dwustronna wartość p hipotezy braku zmiany; wartość mniejszą od najmniejszej dodatniej liczby zmiennoprzecinkowej zastępuje się tą liczbą | – | [`pettitt`](10-jednorodnosc-i-trend.md#spec-pettitt) |
| $p$ | Wykładnik potęgi odległości | – | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $P/N$ | Opad w % normy | % | [`kaczorowska_class`](11-wskazniki-meteorologiczne.md#spec-kaczorowska_class), [`month_precipitation_class`](11-wskazniki-meteorologiczne.md#spec-month_precipitation_class) |
| $P_0$ | Najmniejszy opad dnia z opadem | mm | [`spell_lengths`](11-wskazniki-meteorologiczne.md#spec-spell_lengths) |
| $P1$ | Parametr szorstkościowy Lutza w zależności na tp | $\mathrm{h\,km^{-0{,}52}}$ | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $p_1$ | Procent przewyższenia pierwszego, wyższego punktu krzywej | % | [`fdc_slope`](08-przeplywy-charakterystyczne-nizowki.md#spec-fdc_slope) |
| $p_2$ | Procent przewyższenia drugiego, niższego punktu krzywej | % | [`fdc_slope`](08-przeplywy-charakterystyczne-nizowki.md#spec-fdc_slope) |
| $P_{e,m}$ | Opad efektywny w każdym kroku | mm | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $p_i$ | Dwanaście sum miesięcznych roku albo dwanaście norm miesięcznych, w dowolnej kolejności | mm | [`precipitation_concentration_index`](11-wskazniki-meteorologiczne.md#spec-precipitation_concentration_index) |
| $P_i$ | Opad dobowy dni okresu; NaN w dniu z brakiem danych, który jest pomijany | mm | [`sdii`](11-wskazniki-meteorologiczne.md#spec-sdii), [`wet_day_percentile`](11-wskazniki-meteorologiczne.md#spec-wet_day_percentile), [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $p_i$ | Prawdopodobieństwo przewyższenia każdej wartości | – | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions) |
| $P_i$ | Wysokość opadu na każdym posterunku | mm | [`areal_mean_precipitation`](02-opad.md#spec-areal_mean_precipitation), [`thiessen_precipitation`](02-opad.md#spec-thiessen_precipitation), [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $P_j$ | Wysokość opadu w każdym kroku (pole zachowuje nazwę z wcześniejszych wersji; natężenie podaje pole wyniku intensity_mm_per_h) | mm | [`block_hyetograph`](02-opad.md#spec-block_hyetograph), [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph), [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph), [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $P_t$ | Dobowy opad z kolejnych dni; NaN w dniu z brakiem danych | mm | [`spell_lengths`](11-wskazniki-meteorologiczne.md#spec-spell_lengths) |
| $P_t$ | Próg: percentyl opadu dni z opadem okresu odniesienia | mm | [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $P_w$ | Najmniejszy opad dnia z opadem | mm | [`sdii`](11-wskazniki-meteorologiczne.md#spec-sdii), [`wet_day_percentile`](11-wskazniki-meteorologiczne.md#spec-wet_day_percentile), [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $Q$ | Odpływ bezpośredni z całego opadu | mm | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $Q$ | Percentyl opadu dni z opadem | mm | [`wet_day_percentile`](11-wskazniki-meteorologiczne.md#spec-wet_day_percentile) |
| $q$ | Prawdopodobieństwo sumy zerowej (`spi_gamma_fit`) | – | [`spi`](11-wskazniki-meteorologiczne.md#spec-spi) |
| $Q$ | Przepływ odniesienia, przy którym przyjmuje się prędkość fali i szerokość zwierciadła, wspólny dla całego obliczenia | m³/s | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $Q$ | Przepływ przy każdym stanie | m³/s | [`rating_curve`](09-rezim-i-zmiennosc.md#spec-rating_curve) |
| $Q$ | Przepływ zmierzony przy każdym stanie | m³/s | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $Q$ | Przepływ, dla którego wyznacza się przepływ normalny | m³/s | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $q$ | Udział sum zerowych | – | [`spi_gamma_fit`](11-wskazniki-meteorologiczne.md#spec-spi_gamma_fit) |
| $q$ | Wartości dobowe szeregu, w dowolnej kolejności; NaN w dniu bez wartości, który jest pomijany | m³/s | [`exceedance_values`](08-przeplywy-charakterystyczne-nizowki.md#spec-exceedance_values) |
| $Q_d$ | Średni przepływ dobowy, w m³/s lub dowolnej jednostce; NaN oznacza dzień bez wartości | m³/s | [`parde_coefficients`](09-rezim-i-zmiennosc.md#spec-parde_coefficients) |
| $q_i$ | Odpływ bezpośredni w każdym kroku | mm | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $q_i$ | Rzędne hydrogramu jednostkowego dla czasu trwania D | m³/s na mm | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh), [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $q_k$ | Rzędne hydrogramu jednostkowego | m³/s na mm | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $q_k$ | Rzędne hydrogramu jednostkowego dla czasu trwania D | m³/s na mm | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $Q_{max}$ | Największa rzędna hydrogramu | m³/s | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $Q_n$ | Odpływ bezpośredni w chwili t_n | m³/s | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $q_p$ | Kulminacja dla standardowego czasu trwania | m³/s na mm | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $q_p$ | Największa rzędna | m³/s na mm | [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $q_p$ | Największa rzędna hydrogramu jednostkowego | m³/s na mm | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $q_p$ | Przepływ kulminacyjny ze wzoru dla czasu trwania D | m³/s na mm | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $Q_p$ | Wartość osiągana lub przekraczana w każdym z podanych procentów dni, w jednostce szeregu | m³/s | [`exceedance_values`](08-przeplywy-charakterystyczne-nizowki.md#spec-exceedance_values) |
| $Q_p(i)$ | Wartości krzywych rocznych: wiersz na każdy pełny rok hydrologiczny i, w dowolnej kolejności, kolumna na każdy procent przewyższenia p (Q_p(i) Vogela i Fennesseya, każda z dni swojego roku) | m³/s | [`duration_curve_annual_median_interval`](08-przeplywy-charakterystyczne-nizowki.md#spec-duration_curve_annual_median_interval) |
| $Q_{p,(k)}$ | Dolna granica każdej mediany, wiersz na poziom w podanej kolejności: k-ta najmniejsza wartość roczna; luka tam, gdzie N lat nie osiąga poziomu | m³/s | [`duration_curve_annual_median_interval`](08-przeplywy-charakterystyczne-nizowki.md#spec-duration_curve_annual_median_interval) |
| $Q_{p,(N+1-k)}$ | Górna granica: k-ta największa wartość roczna; luka jak w dolnej | m³/s | [`duration_curve_annual_median_interval`](08-przeplywy-charakterystyczne-nizowki.md#spec-duration_curve_annual_median_interval) |
| $Q_{p,0{,}5}$ | Medianowa krzywa roczna: dla każdego procentu mediana N wartości rocznych, w jednostce szeregu | m³/s | [`duration_curve_annual_median_interval`](08-przeplywy-charakterystyczne-nizowki.md#spec-duration_curve_annual_median_interval) |
| $q_{pR}$ | Kulminacja dla czasu trwania D | m³/s na mm | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $q_{pR}$ | Kulminacja hydrogramu jednostkowego (specyfikacja `snyder`) | m³/s na mm | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $Q_T$ | Minima o danych okresach powtarzalności; luka tam, gdzie przepływ byłby ujemny | m³/s | [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $Q_t$ | Przepływ dobowy jednego roku od jego pierwszego dnia; NaN w dniu bez wartości | m³/s | [`half_flow_date`](08-przeplywy-charakterystyczne-nizowki.md#spec-half_flow_date) |
| $Q_t$ | Przepływ dobowy w kolejnych dniach; luka (NaN) oznacza dzień bez wartości | m³/s | [`recession_constant`](08-przeplywy-charakterystyczne-nizowki.md#spec-recession_constant) |
| $Q_t$ | Przepływ dobowy w porządku czasowym; NaN w dniu bez wartości | m³/s | [`high_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-high_flow_days), [`low_flow_days`](08-przeplywy-charakterystyczne-nizowki.md#spec-low_flow_days) |
| $Q_t$ | Przepływ dobowy, znany dla każdego dnia, w porządku czasowym | m³/s | [`lyne_hollick`](08-przeplywy-charakterystyczne-nizowki.md#spec-lyne_hollick) |
| $Q_t$ | Przepływ dobowy; NaN w dniu bez wartości | m³/s | [`zero_flow_fraction`](08-przeplywy-charakterystyczne-nizowki.md#spec-zero_flow_fraction) |
| $Q_t$ | Przepływ dobowy; luka (NaN) oznacza dzień bez wartości | m³/s | [`baseflow_index`](08-przeplywy-charakterystyczne-nizowki.md#spec-baseflow_index) |
| $Q_T$ | Przepływy o danych okresach powtarzalności | m³/s | [`gev_quantiles`](07-przeplywy-maksymalne.md#spec-gev_quantiles), [`log_normal_quantiles`](07-przeplywy-maksymalne.md#spec-log_normal_quantiles), [`pearson3_quantiles`](07-przeplywy-maksymalne.md#spec-pearson3_quantiles), [`weibull_quantiles`](07-przeplywy-maksymalne.md#spec-weibull_quantiles) |
| $Q_t$ | Wartości dobowe szeregu, w dowolnej kolejności; NaN w dniu bez wartości, który jest pomijany | m³/s | [`fdc_slope`](08-przeplywy-charakterystyczne-nizowki.md#spec-fdc_slope) |
| $r$ | Długość średniego wektora: 1 dla jednego terminu, bliska 0, gdy terminy rozkładają się na cały rok | – | [`circular_mean`](09-rezim-i-zmiennosc.md#spec-circular_mean) |
| $r$ | Najmniejszy stosunek współczynnika miesiąca letniego do wiosennego uznawany za „prawie równy” | – | [`dynowska_regime_type`](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| $R$ | Opad dni powyżej progu (R95p) | mm | [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $R$ | Stała retencji zbiornika liniowego, S = R O | min | [`clark`](05-hydrogram-jednostkowy.md#spec-clark), [`clark_lag`](05-hydrogram-jednostkowy.md#spec-clark_lag) |
| $r$ | Współczynnik wyprzedzenia burzy: czas do szczytu jako ułamek czasu trwania | – | [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph) |
| $R^2$ | Udział wariancji wyjaśnionej przez całe dopasowanie | – | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $R^2$ | Współczynnik determinacji krzywej na Q | – | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $R_b$ | Wskaźnik bifurkacji rzędów u i u + 1 | – | [`bifurcation_ratio`](01-zlewnia.md#spec-bifurcation_ratio) |
| $R_h$ | Wskaźnik rzeźby: deniwelacja podzielona przez długość zlewni | m/m | [`relief_ratio`](01-zlewnia.md#spec-relief_ratio) |
| $R_l$ | Wskaźnik długości cieków rzędów u i u + 1 | – | [`length_ratio`](01-zlewnia.md#spec-length_ratio) |
| $S$ | Największa objętość wody we wszystkich zbiornikach | m³ | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $S$ | Objętość wody w drodze przez odcinek w ostatniej rzędnej, dopływ z ostatnich lag minut | m³ | [`lag`](06-transformacja-fali.md#spec-lag) |
| $S$ | Objętość wody w drodze przez odcinek w pierwszej rzędnej, lag O0 | m³ | [`lag`](06-transformacja-fali.md#spec-lag) |
| $S$ | Objętość wody w drodze przez odcinek w stanie ustalonym przy ostatnim dopływie, lag I[-1] | m³ | [`lag`](06-transformacja-fali.md#spec-lag) |
| $S$ | Objętość wody w pododcinkach w ostatniej rzędnej | m³ | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $S$ | Objętość wody w pododcinkach w pierwszej rzędnej | m³ | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $S$ | Objętość wody w pododcinkach w stanie ustalonym przy ostatnim dopływie, K I[-1] | m³ | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $S$ | Objętość wody w schemacie w ostatniej rzędnej | m³ | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $S$ | Objętość wody w schemacie w pierwszej rzędnej, suma K/N [X I + (1 - X) O] po krokach przestrzennych; ujemna, gdy X < 0, a dopływ dostatecznie przewyższa odpływ początkowy | m³ | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $S$ | Objętość wody w schemacie w stanie ustalonym przy ostatnim dopływie, K I[-1] | m³ | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $S$ | Objętość wody w zbiornikach w ostatniej rzędnej | m³ | [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| $S$ | Objętość wody w zbiornikach w pierwszej rzędnej | m³ | [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| $S$ | Objętość wody w zbiornikach w stanie ustalonym przy ostatnim dopływie, n K I[-1] | m³ | [`linear_reservoir_cascade`](06-transformacja-fali.md#spec-linear_reservoir_cascade) |
| $S$ | Objętość wody, jaką zbiorniki mieściłyby w stanie ustalonym przy ostatniej rzędnej dopływu | m³ | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $s$ | Odchylenie standardowe reszt Q - Q(H) | m³/s | [`rating_curve_fit`](09-rezim-i-zmiennosc.md#spec-rating_curve_fit) |
| $s$ | Odchylenie standardowe z dzielnikiem n - 1 | m³/s | [`sample_moments`](07-przeplywy-maksymalne.md#spec-sample_moments) |
| $s$ | R w % PRCPTOT (R95pTOT według ClimPACT) | % | [`heavy_precipitation_share`](11-wskazniki-meteorologiczne.md#spec-heavy_precipitation_share) |
| $S$ | Retencja maksymalna S | mm | [`scs_cn_runoff`](03-opad-efektywny.md#spec-scs_cn_runoff) |
| $S$ | Retencja maksymalna po rozpoczęciu odpływu | mm | [`scs_cn_retention`](03-opad-efektywny.md#spec-scs_cn_retention) |
| $S$ | Spadek dna, równy spadkowi linii energii przy przepływie jednostajnym | m/m | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $S$ | Spadek krzywej w skali logarytmicznej na jednostkę prawdopodobieństwa przewyższenia | – | [`fdc_slope`](08-przeplywy-charakterystyczne-nizowki.md#spec-fdc_slope) |
| $S$ | Spadek najdłuższej drogi spływu: wysokość jej początku minus wysokość przekroju, podzielona przez jej długość | m/m | [`kirpich`](04-czas-koncentracji.md#spec-kirpich) |
| $S$ | Spadek powierzchni, po której spływa woda | m/m | [`faa`](04-czas-koncentracji.md#spec-faa), [`kerby`](04-czas-koncentracji.md#spec-kerby) |
| $S$ | Spadek prostej przez przekrój, przy którym pola profilu nad nią i pod nią są równe | m/m | [`equal_area_slope`](01-zlewnia.md#spec-equal_area_slope) |
| $S$ | Statystyka S Kendalla: liczba par rosnących pomniejszona o liczbę par malejących | – | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $s$ | Udział marca i kwietnia w objętości rocznej, od 0 do 1 | – | [`spring_share`](09-rezim-i-zmiennosc.md#spec-spring_share) |
| $s$ | Ziarno generatora liczb losowych | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap) |
| $S_0$ | Spadek dna odcinka | m/m | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $S_1$ | Górna granica współczynnika miesiąca wiosennego w reżimie niwalnym słabo wykształconym | – | [`dynowska_regime_type`](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| $S_2$ | Górna granica współczynnika miesiąca wiosennego w reżimie niwalnym średnio wykształconym | – | [`dynowska_regime_type`](09-rezim-i-zmiennosc.md#spec-dynowska_regime_type) |
| $S_{fp}$ | Spadek tej drogi: wysokość jej początku minus wysokość przekroju, podzielona przez jej długość | m/m | [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $S_i$ | Retencja w każdym wierszu tabeli retencja–odpływ, niemalejąca; do odpływu wchodzą tylko jej różnice, więc jej poziom odniesienia jest dowolny | m³ | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $\sigma$ | Odchylenie standardowe logarytmów x - loc | – | [`log_normal_quantiles`](07-przeplywy-maksymalne.md#spec-log_normal_quantiles) |
| $\sigma$ | Odchylenie standardowe rozkładu | m³/s | [`pearson3_quantiles`](07-przeplywy-maksymalne.md#spec-pearson3_quantiles) |
| $S_{ov}$ | Spadek powierzchni, po której spływa woda | m/m | [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $s_t$ | Objętość wody w ostatnim zbiorniku w każdej rzędnej, cała objętość przy N = 1 | m³ | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $S_t$ | Objętość wody we wszystkich zbiornikach w każdej rzędnej | m³ | [`level_pool`](06-transformacja-fali.md#spec-level_pool) |
| $\sum L$ | Łączna długość cieków zlewni | km | [`drainage_density`](01-zlewnia.md#spec-drainage_density) |
| $\sum N_u$ | Liczba cieków wszystkich rzędów według Strahlera | – | [`stream_frequency`](01-zlewnia.md#spec-stream_frequency) |
| $\sum t$ | Suma średnich dobowych temperatur z tych samych dni: średnia miesięczna pomnożona przez liczbę dni miesiąca albo suma z dni sezonu | °C·d | [`sielianinov_coefficient`](11-wskazniki-meteorologiczne.md#spec-sielianinov_coefficient) |
| $T$ | Długość hydrogramu: krzywa poza nią jest odcinana | min | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $T$ | Długość hydrogramu; `ClarkIUH` przyjmuje tc + 5 R + D | min | [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $T$ | Długość hydrogramu; `NashIUH` przyjmuje 5 n K + D | min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $T$ | Okresy powtarzalności: kwantyl T-letni jest przewyższany z prawdopodobieństwem 1/T w roku | lata | [`gev_quantiles`](07-przeplywy-maksymalne.md#spec-gev_quantiles), [`log_normal_quantiles`](07-przeplywy-maksymalne.md#spec-log_normal_quantiles), [`pearson3_quantiles`](07-przeplywy-maksymalne.md#spec-pearson3_quantiles), [`weibull_quantiles`](07-przeplywy-maksymalne.md#spec-weibull_quantiles), [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $T$ | Okresy powtarzalności: wartość niższa od kwantyla T-letniego występuje z prawdopodobieństwem 1/T w roku | lata | [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $t$ | Podział t, przy którym występuje K: liczba wartości przed zmianą | – | [`pettitt`](10-jednorodnosc-i-trend.md#spec-pettitt) |
| $T$ | Szerokość zwierciadła wody przy głębokości normalnej | m | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $T$ | Szerokość zwierciadła wody przy przepływie odniesienia | m | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $T_{1/2}$ | Liczba dni, w ciągu których taka recesja zmniejsza przepływ o połowę | d | [`recession_constant`](08-przeplywy-charakterystyczne-nizowki.md#spec-recession_constant) |
| $t_a$ | Chwila szczytu liczona od początku deszczu | min | [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph) |
| $\tau$ | Przesunięcie, czas przepływu przez odcinek | min | [`lag`](06-transformacja-fali.md#spec-lag) |
| $\tau_3$ | L-skośność; 1 (lub -1), gdy wszystkie wartości poza największą (najmniejszą) są równe | – | [`sample_l_moments`](07-przeplywy-maksymalne.md#spec-sample_l_moments) |
| $\tau_{3,0}$ | Wartość bezwzględna L-skośności, poniżej której rozkład Pearsona III przyjmuje się za normalny | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $\tau_{3,G}$ | L-skośność rozkładu Gumbela, granica zanegowanej L-skośności przy dopasowaniu rozkładu Weibulla | – | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments) |
| $T_b$ | Czas podstawy hydrogramu: koniec tab. 16-1 | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $t_b$ | Podstawa trójkąta o wierzchołku qpR i objętości 1 mm | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $T_b$ | Temperatura bazowa stopniodni wzrostu | °C | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $t_c$ | Czas koncentracji | min | [`kirpich`](04-czas-koncentracji.md#spec-kirpich), [`nrcs`](04-czas-koncentracji.md#spec-nrcs), [`giandotti`](04-czas-koncentracji.md#spec-giandotti), [`faa`](04-czas-koncentracji.md#spec-faa), [`kerby`](04-czas-koncentracji.md#spec-kerby), [`kerby_kirpich`](04-czas-koncentracji.md#spec-kerby_kirpich) |
| $t_c$ | Czas koncentracji zlewni | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $t_c$ | Czas koncentracji, czyli czas translacji zlewni | min | [`clark`](05-hydrogram-jednostkowy.md#spec-clark), [`clark_lag`](05-hydrogram-jednostkowy.md#spec-clark_lag) |
| $T_d$ | Czas trwania deszczu, całkowita liczba kroków | min | [`block_hyetograph`](02-opad.md#spec-block_hyetograph), [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph), [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph), [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $t_D$ | Standardowy czas trwania opadu | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $\text{stan hydrologiczny}$ | Stan hydrologiczny; brak dla pokrycia o jednym wierszu | – | [`tr55_cn`](03-opad-efektywny.md#spec-tr55_cn) |
| $\text{pokrycie terenu}$ | Klasa pokrycia terenu w Hydrologu | – | [`tr55_cn`](03-opad-efektywny.md#spec-tr55_cn) |
| $\text{HSG}$ | Hydrologiczna grupa gleby | – | [`tr55_cn`](03-opad-efektywny.md#spec-tr55_cn) |
| $\text{rodzaj}$ | Ciągi dni bezopadowych (poniżej progu) albo ciągi dni z opadem (na progu lub powyżej) | – | [`spell_lengths`](11-wskazniki-meteorologiczne.md#spec-spell_lengths) |
| $T_f$ | Próg: dzień FD ma Tmin poniżej tej wartości | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $T_h$ | Próg: dzień upalny ma Tmax powyżej tej wartości | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $t_i$ | Czas każdej daty od początku jej roku: dzień roku minus połowa, czyli środek dnia | d | [`circular_mean`](09-rezim-i-zmiennosc.md#spec-circular_mean) |
| $t_i$ | Czas każdej kolejnej wartości: jej rok albo krok 0, 1, 2 … szeregu; kilka wartości może mieć ten sam czas. Nachylenie jest wyrażone na jednostkę tych czasów | a | [`sen_slope`](10-jednorodnosc-i-trend.md#spec-sen_slope), [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $T_i$ | Okres powtarzalności każdej wartości, od której wartość niższa występuje raz na T lat | lata | [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $T_i$ | Okres powtarzalności każdej wartości, przewyższanej raz na T lat | lata | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions) |
| $T_i$ | Próg: dzień mroźny ma Tmax poniżej tej wartości, a dzień przymrozkowy powyżej niej | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $t_j$ | Koniec każdego kroku liczony od początku deszczu | min | [`block_hyetograph`](02-opad.md#spec-block_hyetograph), [`triangular_hyetograph`](02-opad.md#spec-triangular_hyetograph), [`beta_hyetograph`](02-opad.md#spec-beta_hyetograph), [`euler_ii_hyetograph`](02-opad.md#spec-euler_ii_hyetograph) |
| $t_L$ | Czas opóźnienia zlewni, od środka opadu o czasie trwania tD do kulminacji | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $T_l$ | Próg grzania: doba jest dniem grzewczym, gdy Tm nie przekracza tej wartości (angielska „base temperature” Eurostatu, polska „temperatura graniczna”) | °C | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $t_{lag}$ | Czas opóźnienia zlewni, od środka jednostkowego opadu efektywnego do Tp | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $t_{lag}$ | Czas opóźnienia, pierwszy moment hydrogramu jednostkowego chwilowego | min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $t_{lag}$ | Czas opóźnienia, pierwszy moment hydrogramu jednostkowego chwilowego Clarka liczony od chwili opadu | min | [`clark_lag`](05-hydrogram-jednostkowy.md#spec-clark_lag) |
| $t_{LR}$ | Czas opóźnienia dla czasu trwania D | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $T_m$ | Średnia dobowa temperatura powietrza; NaN w dniu z brakiem danych | °C | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $t_{max}$ | Chwila pierwszej największej rzędnej | min | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $t_n$ | Chwile rzędnych | min | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $T_n$ | Minimalna dobowa temperatura powietrza z tych samych dni; NaN w dniu z brakiem danych | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $t_p$ | Chwila największej rzędnej | min | [`clark`](05-hydrogram-jednostkowy.md#spec-clark) |
| $t_p$ | Chwila największej rzędnej hydrogramu jednostkowego | min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $t_p$ | Chwila szczytu hydrogramu jednostkowego chwilowego, czyli jego dominanta | min | [`nash_iuh_peak`](05-hydrogram-jednostkowy.md#spec-nash_iuh_peak) |
| $tp$ | Czas do kulminacji chwilowego hydrogramu jednostkowego | h | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $T_p$ | Czas do kulminacji od początku jednostkowego opadu efektywnego | min | [`scs`](05-hydrogram-jednostkowy.md#spec-scs) |
| $t_{pR}$ | Czas do kulminacji dla czasu trwania D liczony od początku opadu | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $t_{pR}$ | Czas do kulminacji od początku opadu (specyfikacja `snyder`) | min | [`snyder_shape`](05-hydrogram-jednostkowy.md#spec-snyder_shape) |
| $T_r$ | Temperatura odniesienia stopniodni grzania (polska „temperatura bazowa”) | °C | [`degree_days`](11-wskazniki-meteorologiczne.md#spec-degree_days) |
| $T_s$ | Próg: dzień gorący ma Tmax powyżej tej wartości | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $T_t$ | Próg: noc tropikalna ma Tmin powyżej tej wartości | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $T_x$ | Maksymalna dobowa temperatura powietrza; NaN w dniu z brakiem danych | °C | [`threshold_days`](11-wskazniki-meteorologiczne.md#spec-threshold_days) |
| $U$ | Górna granica, jak dolna | m³/s | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $u$ | Rząd cieku poniżej węzła według Strahlera | – | [`strahler_order`](01-zlewnia.md#spec-strahler_order) |
| $U$ | Udział powierzchni nieprzepuszczalnych w powierzchni zlewni | – | [`nash_urban_regression`](05-hydrogram-jednostkowy.md#spec-nash_urban_regression) |
| $U$ | Udział terenów zurbanizowanych w powierzchni zlewni | % | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $u(i \Delta t)$ | Rzędne hydrogramu jednostkowego chwilowego w tych chwilach | 1/min | [`nash_iuh`](05-hydrogram-jednostkowy.md#spec-nash_iuh) |
| $u_i$ | Rzędy według Strahlera cieków wpadających do danego cieku; lista pusta dla cieku źródłowego | – | [`strahler_order`](01-zlewnia.md#spec-strahler_order) |
| $U_k$ | Rzędne hydrogramu jednostkowego dla czasu trwania równego krokowi, pierwsza w t = 0 | m³/s na mm | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $up$ | Rzędna kulminacyjna chwilowego hydrogramu jednostkowego (dt -> 0) | 1/h | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $u_p$ | Rzędna szczytowa hydrogramu jednostkowego chwilowego | 1/min | [`nash_iuh_peak`](05-hydrogram-jednostkowy.md#spec-nash_iuh_peak) |
| $V$ | Objętość hydrogramu, sum(Q_n) dt | m³ | [`uh_convolution`](05-hydrogram-jednostkowy.md#spec-uh_convolution) |
| $V$ | Prędkość średnia Q / A | m/s | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $v$ | Rodzaj ekstremów: przepływ albo inna wielkość nigdy poniżej 0, np. wysokość opadu, albo stan wody, którego 0 jest zerem wodowskazu | – | [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $v$ | Rodzaj minimów: przepływ, nigdy poniżej 0, lub stan wody, którego 0 jest zerem wodowskazu | – | [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $v_i$ | Wartości kolejnych izohiet ograniczających pasy | mm | [`isohyet_precipitation`](02-opad.md#spec-isohyet_precipitation) |
| $W$ | Liczba dni z opadem | d | [`sdii`](11-wskazniki-meteorologiczne.md#spec-sdii) |
| $W$ | Udział lasów w powierzchni zlewni | % | [`lutz`](05-hydrogram-jednostkowy.md#spec-lutz) |
| $w + f$ | Przesunięcie podzielone przez krok czasowy | – | [`lag`](06-transformacja-fali.md#spec-lag) |
| $W_{50}$ | Szerokość hydrogramu jednostkowego na wysokości 50 % kulminacji qpR | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $W_{75}$ | Szerokość hydrogramu jednostkowego na wysokości 75 % kulminacji qpR | min | [`snyder`](05-hydrogram-jednostkowy.md#spec-snyder) |
| $w_i$ | Waga każdego posterunku; wagi sumują się do jedności | – | [`thiessen_precipitation`](02-opad.md#spec-thiessen_precipitation), [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $x$ | Odległość wzdłuż profilu od przekroju (pierwszego punktu) w górę do każdego punktu; początek dowolny, bo liczą się tylko różnice | m | [`equal_area_slope`](01-zlewnia.md#spec-equal_area_slope) |
| $x$ | Pierwsza próba, np. wartości przed podziałem | m³/s | [`ks_exact`](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| $x$ | Sumy opadu z miesiąca kalendarzowego i skali czasowej rozkładu; NaN pozostaje NaN | mm | [`spi`](11-wskazniki-meteorologiczne.md#spec-spi) |
| $X$ | Waga dopływu w retencji: 0 — zbiornik liniowy, 0,5 — fala nietłumiona | – | [`muskingum`](06-transformacja-fali.md#spec-muskingum) |
| $x$ | Wartości dobowe w dowolnej jednostce, najczęściej temperatura wody lub powietrza; NaN oznacza dzień bez wartości | °C | [`harmonic_fit`](09-rezim-i-zmiennosc.md#spec-harmonic_fit) |
| $X$ | Współczynnik wagowy każdego kroku przestrzennego, (1 - Dg) / 2 | – | [`muskingum_cunge`](06-transformacja-fali.md#spec-muskingum_cunge) |
| $x$ | Współrzędna wschodnia punktu | m | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $x_{(i)}$ | Próba: maksima roczne przepływu lub stanu wody | m³/s | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions) |
| $x_{(i)}$ | Próba: minima roczne przepływu lub stanu wody | m³/s | [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $x_{(i)}$ | Wartości uporządkowane malejąco | m³/s | [`plotting_positions`](07-przeplywy-maksymalne.md#spec-plotting_positions) |
| $x_{(i)}$ | Wartości uporządkowane rosnąco | m³/s | [`non_exceedance_positions`](08-przeplywy-charakterystyczne-nizowki.md#spec-non_exceedance_positions) |
| $x_i$ | Minima roczne przepływu lub stanu wody | m³/s | [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $\xi$ | Parametr położenia | m³/s | [`gev_quantiles`](07-przeplywy-maksymalne.md#spec-gev_quantiles), [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling), [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion), [`quantile_interval_bootstrap`](07-przeplywy-maksymalne.md#spec-quantile_interval_bootstrap), [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta), [`fisher_tippett_minima`](08-przeplywy-charakterystyczne-nizowki.md#spec-fisher_tippett_minima) |
| $\xi$ | Parametr położenia: 0 dla rozkładu logarytmiczno-normalnego, średnia rozkładu Pearsona III, dolne ograniczenie rozkładu Weibulla | m³/s | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments), [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_maximum_likelihood`](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares) |
| $x_i$ | Próba, do której dopasowano rozkład metodą największej wiarygodności: maksima roczne albo minima roczne (extremes minima) | m³/s | [`quantile_interval_delta`](07-przeplywy-maksymalne.md#spec-quantile_interval_delta) |
| $x_i$ | Próba: maksima lub minima roczne | m³/s | [`sample_moments`](07-przeplywy-maksymalne.md#spec-sample_moments), [`sample_l_moments`](07-przeplywy-maksymalne.md#spec-sample_l_moments) |
| $x_i$ | Próba: maksima roczne lub dowolna próba z danego rozkładu | m³/s | [`fit_l_moments`](07-przeplywy-maksymalne.md#spec-fit_l_moments), [`fit_moments`](07-przeplywy-maksymalne.md#spec-fit_moments), [`fit_maximum_likelihood`](07-przeplywy-maksymalne.md#spec-fit_maximum_likelihood), [`fit_least_squares`](07-przeplywy-maksymalne.md#spec-fit_least_squares), [`anderson_darling`](07-przeplywy-maksymalne.md#spec-anderson_darling), [`akaike_information_criterion`](07-przeplywy-maksymalne.md#spec-akaike_information_criterion) |
| $x_i$ | Sumy opadu jednego miesiąca kalendarzowego i jednej skali czasowej, po jednej na każdy rok okresu odniesienia | mm | [`spi_gamma_fit`](11-wskazniki-meteorologiczne.md#spec-spi_gamma_fit) |
| $x_i$ | Szereg uporządkowany w czasie, np. maksima roczne, w dowolnej jednostce | m³/s | [`pettitt`](10-jednorodnosc-i-trend.md#spec-pettitt) |
| $x_i$ | Szereg uporządkowany w czasie, po jednej wartości na krok czasowy: maksima, średnie lub minima roczne, sumy lub liczebności, w dowolnej jednostce | m³/s | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $x_i$ | Szereg, po jednej wartości na każdy czas z times, w dowolnej jednostce | m³/s | [`sen_interval`](10-jednorodnosc-i-trend.md#spec-sen_interval) |
| $x_i$ | Szereg, po jednej wartości na każdy czas z times, w dowolnej jednostce; nachylenie ma jednostkę szeregu na jednostkę czasu | m³/s | [`sen_slope`](10-jednorodnosc-i-trend.md#spec-sen_slope) |
| $x_i$ | Współrzędna wschodnia (easting) każdego posterunku | m | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $x_n$ | Dwanaście sum miesięcznych w dowolnej kolejności: opadu lub objętości odpływu w dowolnej jednostce (wskaźnik jest bezwymiarowy) | mm | [`seasonality_index`](09-rezim-i-zmiennosc.md#spec-seasonality_index) |
| $y$ | Druga próba, w jednostce pierwszej | m³/s | [`ks_exact`](10-jednorodnosc-i-trend.md#spec-ks_exact) |
| $y$ | Głębokość normalna | m | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $y$ | Współrzędna północna punktu | m | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $Y$ | Średni spadek terenu zlewni, nie spadek drogi spływu | m/m | [`nrcs`](04-czas-koncentracji.md#spec-nrcs) |
| $y_i$ | Współrzędna północna (northing) każdego posterunku | m | [`idw_precipitation`](02-opad.md#spec-idw_precipitation) |
| $z$ | Odległość pozioma w metrach na metr wysokości obu skarp; zero dla prostokąta | m/m | [`manning_normal_flow`](06-transformacja-fali.md#spec-manning_normal_flow) |
| $Z$ | Standaryzowana statystyka z poprawką na ciągłość równą jeden | – | [`mann_kendall`](10-jednorodnosc-i-trend.md#spec-mann_kendall) |
| $z$ | Wysokość każdego punktu profilu, dna lub wypełnionego NMT wzdłuż drogi spływu; pierwsza to wysokość przekroju | m | [`equal_area_slope`](01-zlewnia.md#spec-equal_area_slope) |
| $z$ | Wysokość każdej komórki NMT zlewni [m n.p.m.] | m | [`hypsometric_integral`](01-zlewnia.md#spec-hypsometric_integral) |

<!-- /generated:symbols -->

## A.3. Skróty

| Skrót | Znaczenie |
|---|---|
| AMC, ARC | warunki wilgotnościowe poprzedzające (*antecedent moisture condition*, *antecedent runoff condition*) metody SCS-CN, klasy I, II i III |
| BFI | wskaźnik odpływu podziemnego (*baseflow index*) |
| CN | parametr krzywej odpływu metody SCS (*curve number*) |
| ETCCDI | zespół ekspertów WMO do spraw wykrywania zmian klimatu i ich wskaźników (*Expert Team on Climate Change Detection and Indices*) |
| GEV | uogólniony rozkład wartości ekstremalnych (*generalized extreme value*) |
| HSG | grupa hydrologiczna gleby (*hydrologic soil group*), A do D |
| IDW | interpolacja ważona odwrotnością odległości (*inverse distance weighting*) |
| IMGW-PIB | Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy |
| KZGW | Krajowy Zarząd Gospodarki Wodnej |
| NEH | *National Engineering Handbook* (USDA-NRCS), część 630 *Hydrology* |
| NRCS | *Natural Resources Conservation Service* (USDA), dawniej SCS |
| PMAXTP | maksymalne opady o określonym czasie trwania i prawdopodobieństwie przewyższenia (IMGW-PIB) |
| PMP | opad maksymalny prawdopodobny (*probable maximum precipitation*); nie mylić z PMAXTP |
| SCS | *Soil Conservation Service* (USDA), dziś NRCS |
| SPI | standaryzowany wskaźnik opadu (*standardized precipitation index*) |
| TR-55 | *Technical Release 55: Urban Hydrology for Small Watersheds* (USDA-SCS 1986) |
| WMO | Światowa Organizacja Meteorologiczna (*World Meteorological Organization*) |

## Źródła

- BIPM (2019). *The International System of Units (SI)*, 9th edition.
  <https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf>.
- Nogat (2026). Standard 1.1, *Computations: formulas, their limits and their verification*
  (`standards/COMPUTATIONS.md`, wymaganie CMP-4.3). <https://github.com/Daldek/Nogat>.
