"""Group ``uh``: unit hydrographs (SCS, Nash, Clark, Snyder).

Every command returns the unit hydrograph of a catchment in m3/s per mm of effective
precipitation. Nash and Clark offer more than one way to obtain their parameters; the
alternatives are separate ``one_of`` groups of options (decision: no ``estimation``
option, the group that is given selects the method). ``NashIUH.from_tc`` is not
offered: it is deprecated and has no scientific basis for the Nash model.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_AREA = Option(
    name="area_km2",
    type="number",
    description="Powierzchnia zlewni [km²]; > 0.",
    description_en="Catchment area [km2]; > 0.",
    required=True,
    exclusive_minimum=0,
    unit="km2",
)


def _timestep(default: float, note_pl: str, note_en: str) -> Option:
    return Option(
        name="timestep_min",
        type="number",
        description=(
            f"Krok czasowy hydrogramu [min]; > 0; domyślnie {default:g}. {note_pl}"
        ),
        description_en=(
            f"Time step of the hydrograph [min]; > 0; default {default:g}. {note_en}"
        ),
        exclusive_minimum=0,
        unit="min",
        default=default,
    )


def _rainfall_duration(note_pl: str, note_en: str) -> Option:
    return Option(
        name="rainfall_duration_min",
        type="number",
        description=(
            "Czas trwania opadu jednostkowego D, dla którego liczony jest "
            f"hydrogram [min]; > 0. {note_pl}"
        ),
        description_en=(
            "Duration D of the unit rainfall the hydrograph is computed for "
            f"[min]; > 0. {note_en}"
        ),
        exclusive_minimum=0,
        unit="min",
    )


def _total_duration(note_pl: str, note_en: str) -> Option:
    return Option(
        name="total_duration_min",
        type="number",
        description=(f"Całkowita długość wyniku [min]; > 0. {note_pl}"),
        description_en=(f"Total length of the result [min]; > 0. {note_en}"),
        exclusive_minimum=0,
        unit="min",
    )


_TC = Option(
    name="tc_min",
    type="number",
    description=("Czas koncentracji [min]; > 0 (z dowolnej metody grupy `tc`)."),
    description_en=(
        "Time of concentration [min]; > 0 (from any method of the `tc` group)."
    ),
    required=True,
    exclusive_minimum=0,
    unit="min",
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="uh scs",
        operation_id="uh_scs",
        summary="Hydrogram jednostkowy SCS (NRCS, TR-55) z powierzchni i czasu koncentracji.",
        summary_en="SCS (NRCS, TR-55) unit hydrograph from the area and the time of concentration.",
        description=(
            "Bezwymiarowy hydrogram jednostkowy SCS (NRCS, TR-55) dla zlewni o "
            "powierzchni A i czasie koncentracji tc: czas opóźnienia tlag = 0,6·tc; "
            "czas do szczytu tp = D/2 + tlag, gdzie D to krok czasowy "
            "`timestep_min` (czas trwania opadu jednostkowego); szczyt qp = 0,208·"
            "A/tp [m³/s na mm] (A w km², tp w godzinach); podstawa tb = 5·tp. "
            "Kształt wyznacza tablica bezwymiarowa NRCS (33 punkty t/tp–q/qp, "
            "interpolacja liniowa). Hydrogram odpowiada 1 mm opadu efektywnego "
            "rozłożonego równomiernie w czasie D. tc podaje się z dowolnej metody "
            "grupy `tc` (Kirpich, NRCS, Giandotti, FAA, Kerby, Kerby–Kirpich). "
            "Wynik: tp, qp, tlag, tb oraz rzędne hydrogramu `ordinates_m3s_per_mm` "
            "i czasy `times_min`. Literatura: USDA-NRCS (1986), Urban Hydrology for "
            "Small Watersheds, TR-55, rozdz. 3."
        ),
        description_en=(
            "The dimensionless SCS (NRCS, TR-55) unit hydrograph of a catchment "
            "with area A and time of concentration tc: lag time tlag = 0.6·tc; "
            "time to peak tp = D/2 + tlag, where D is the time step "
            "`timestep_min` (the unit rainfall duration); peak qp = 0.208·A/tp "
            "[m3/s per mm] (A in km2, tp in hours); time base tb = 5·tp. The shape "
            "is the NRCS dimensionless table (33 points t/tp-q/qp, linear "
            "interpolation). The hydrograph corresponds to 1 mm of effective "
            "precipitation spread evenly over the time D. tc comes from any "
            "method of the `tc` group (Kirpich, NRCS, Giandotti, FAA, Kerby, "
            "Kerby-Kirpich). Result: tp, qp, tlag, tb and the hydrograph "
            "ordinates `ordinates_m3s_per_mm` with the times `times_min`. "
            "Reference: USDA-NRCS (1986), Urban Hydrology for Small Watersheds, "
            "TR-55, chapter 3."
        ),
        function="hydrolog.operations:uh_scs",
        options=(
            _AREA,
            _TC,
            _timestep(
                5.0,
                "Jest zarazem czasem trwania opadu jednostkowego D.",
                "It is also the unit rainfall duration D.",
            ),
        ),
        examples=({"area_km2": 45.3, "tc_min": 90.0, "timestep_min": 5.0},),
    ),
    Command(
        name="uh nash",
        operation_id="uh_nash",
        summary="Hydrogram jednostkowy Nasha (kaskada zbiorników): n i K, metoda Lutza lub regresja miejska.",
        summary_en="Nash cascade unit hydrograph: direct n and K, Lutz method or urban regression.",
        description=(
            "Hydrogram jednostkowy Nasha (1957): kaskada n jednakowych zbiorników "
            "liniowych o stałej magazynowania K [min]; IUH u(t) = (t/K)^(n−1)·"
            "exp(−t/K) / (K·Γ(n)), lag tlag = n·K, czas do szczytu IUH (n−1)·K. "
            "Hydrogram D-minutowy to różnica krzywych S (niepełna funkcja gamma) "
            "przesuniętych o D, podzielona przez D i przeskalowana objętością "
            "1 mm × A [m³/s na mm]. Parametry n i K podaje się jedną z trzech "
            "dróg (dokładnie jedna grupa opcji): (a) wprost `n` i `k_min` "
            "(wartości skalibrowane lub oszacowane); (b) metodą Lutza (1984; KZGW "
            "2017), zalecaną dla zlewni bez pomiarów: tp = P₁·(L·Lc/J^1,5)^0,26·"
            "exp(−0,016·U)·exp(0,004·W) [h], P₁ = 3,989·n_M + 0,028, następnie N z "
            "równania f(N) = tp·up = (N−1)^N·exp(−(N−1))/Γ(N), up = 0,66/tp^1,04, "
            "oraz K = tp/(N−1); wymaga `lutz_length_km` (L), "
            "`lutz_centroid_length_km` (Lc ≤ L), `lutz_slope_m_per_m` (J), "
            "`lutz_manning_n` (n_M), opcjonalnie `lutz_urban_pct` (U) i "
            "`lutz_forest_pct` (W) w procentach; (c) regresją dla zlewni "
            "zurbanizowanych (Rao, Delleur, Sarma, 1972): tL = 1,28·A^0,46·"
            "(1+U)^−1,66·H^−0,27·D^0,37 [h], k = 0,56·A^0,39·(1+U)^−0,62·H^−0,11·"
            "D^0,22 [h], N = tL/k; wymaga `urban_effective_precip_mm` (H) i "
            "`urban_duration_h` (D), opcjonalnie `urban_fraction` (U ∈ [0, 1)). "
            "Opcje spoza wybranej grupy są odrzucane. Metoda from_tc (tlag = "
            "0,6·tc) jest przestarzała i bez uzasadnienia dla modelu Nasha, więc "
            "nie jest dostępna. Wynik: n, K, lag, czas do szczytu, szczyt "
            "[m³/s na mm], rzędne i (dla Lutza) wyniki pośrednie obliczeń."
        ),
        description_en=(
            "The Nash (1957) unit hydrograph: a cascade of n identical linear "
            "reservoirs with storage constant K [min]; IUH u(t) = (t/K)^(n-1)·"
            "exp(-t/K) / (K·Γ(n)), lag time tlag = n·K, IUH time to peak "
            "(n-1)·K. The D-minute hydrograph is the difference of S-curves "
            "(incomplete gamma function) shifted by D, divided by D and scaled by "
            "the volume 1 mm × A [m3/s per mm]. The parameters n and K come from "
            "one of three routes (exactly one group of options): (a) directly "
            "`n` and `k_min` (calibrated or estimated values); (b) the Lutz "
            "method (1984; KZGW 2017), recommended for ungauged catchments: tp = "
            "P1·(L·Lc/J^1.5)^0.26·exp(-0.016·U)·exp(0.004·W) [h], P1 = 3.989·n_M + "
            "0.028, then N from f(N) = tp·up = (N-1)^N·exp(-(N-1))/Γ(N), up = "
            "0.66/tp^1.04, and K = tp/(N-1); needs `lutz_length_km` (L), "
            "`lutz_centroid_length_km` (Lc <= L), `lutz_slope_m_per_m` (J), "
            "`lutz_manning_n` (n_M), optionally `lutz_urban_pct` (U) and "
            "`lutz_forest_pct` (W) in percent; (c) the regression for urbanized "
            "catchments (Rao, Delleur, Sarma, 1972): tL = 1.28·A^0.46·"
            "(1+U)^-1.66·H^-0.27·D^0.37 [h], k = 0.56·A^0.39·(1+U)^-0.62·H^-0.11·"
            "D^0.22 [h], N = tL/k; needs `urban_effective_precip_mm` (H) and "
            "`urban_duration_h` (D), optionally `urban_fraction` (U in [0, 1)). "
            "Options outside the chosen group are rejected. The from_tc method "
            "(tlag = 0.6·tc) is deprecated and has no basis for the Nash model, "
            "so it is not offered. Result: n, K, lag, time to peak, peak [m3/s "
            "per mm], the ordinates and (for Lutz) the intermediate results."
        ),
        function="hydrolog.operations:uh_nash",
        options=(
            _AREA,
            Option(
                name="n",
                type="number",
                description=(
                    "Liczba zbiorników kaskady n (parametr kształtu, może być "
                    "ułamkowa); > 0, typowo 1–10. Razem z `k_min`."
                ),
                description_en=(
                    "Number of reservoirs n (shape parameter, may be fractional); "
                    "> 0, typically 1-10. Together with `k_min`."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="k_min",
                type="number",
                description=(
                    "Stała magazynowania zbiornika K [min]; > 0, typowo 10–200. "
                    "Razem z `n`."
                ),
                description_en=(
                    "Storage constant K of a reservoir [min]; > 0, typically "
                    "10-200. Together with `n`."
                ),
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="lutz_length_km",
                type="number",
                description=(
                    "Lutz: długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego L [km]; > 0."
                ),
                description_en=(
                    "Lutz: length of the main stream from the divide to the "
                    "outlet L [km]; > 0."
                ),
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="lutz_centroid_length_km",
                type="number",
                description=(
                    "Lutz: długość cieku od przekroju zamykającego do punktu "
                    "najbliższego środka ciężkości zlewni Lc [km]; > 0, nie "
                    "większa niż L."
                ),
                description_en=(
                    "Lutz: length along the main stream from the outlet to the "
                    "point nearest to the catchment centroid Lc [km]; > 0, not "
                    "larger than L."
                ),
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="lutz_slope_m_per_m",
                type="number",
                description="Lutz: średni spadek cieku głównego J [m/m]; > 0.",
                description_en="Lutz: mean slope of the main stream J [m/m]; > 0.",
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="lutz_manning_n",
                type="number",
                description=(
                    "Lutz: współczynnik szorstkości Manninga koryta n_M; > 0, "
                    "typowo 0,025–0,050 dla cieków naturalnych."
                ),
                description_en=(
                    "Lutz: Manning roughness coefficient of the channel n_M; > 0, "
                    "typically 0.025-0.050 for natural streams."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="lutz_urban_pct",
                type="number",
                description=(
                    "Lutz: udział terenów zurbanizowanych U [%]; 0–100; " "domyślnie 0."
                ),
                description_en=(
                    "Lutz: share of urbanized area U [%]; 0-100; default 0."
                ),
                minimum=0,
                maximum=100,
                unit="%",
            ),
            Option(
                name="lutz_forest_pct",
                type="number",
                description=("Lutz: udział terenów leśnych W [%]; 0–100; domyślnie 0."),
                description_en=(
                    "Lutz: share of forested area W [%]; 0-100; default 0."
                ),
                minimum=0,
                maximum=100,
                unit="%",
            ),
            Option(
                name="urban_effective_precip_mm",
                type="number",
                description=(
                    "Regresja miejska: suma opadu efektywnego H [mm]; > 0. Razem "
                    "z `urban_duration_h`."
                ),
                description_en=(
                    "Urban regression: total effective precipitation H [mm]; > 0. "
                    "Together with `urban_duration_h`."
                ),
                exclusive_minimum=0,
                unit="mm",
            ),
            Option(
                name="urban_duration_h",
                type="number",
                description=(
                    "Regresja miejska: czas trwania opadu efektywnego D [h]; > 0. "
                    "Razem z `urban_effective_precip_mm`."
                ),
                description_en=(
                    "Urban regression: duration of the effective rainfall D [h]; "
                    "> 0. Together with `urban_effective_precip_mm`."
                ),
                exclusive_minimum=0,
                unit="h",
            ),
            Option(
                name="urban_fraction",
                type="number",
                description=(
                    "Regresja miejska: wskaźnik urbanizacji U [-] (udział "
                    "powierzchni zabudowanej, 0 ≤ U < 1); domyślnie 0."
                ),
                description_en=(
                    "Urban regression: urbanization index U [-] (built-up share "
                    "of the area, 0 <= U < 1); default 0."
                ),
                minimum=0,
                maximum=1,
            ),
            _timestep(
                5.0,
                "Przy domyślnym D jest zarazem czasem trwania opadu jednostkowego.",
                "With the default D it is also the unit rainfall duration.",
            ),
            _rainfall_duration(
                "Domyślnie równy krokowi czasowemu.",
                "Defaults to the time step.",
            ),
            _total_duration(
                "Domyślnie 5·n·K + D.",
                "Defaults to 5·n·K + D.",
            ),
        ),
        one_of=(
            ("n", "k_min"),
            (
                "lutz_length_km",
                "lutz_centroid_length_km",
                "lutz_slope_m_per_m",
                "lutz_manning_n",
            ),
            ("urban_effective_precip_mm", "urban_duration_h"),
        ),
        examples=(
            {"area_km2": 45.3, "n": 3.0, "k_min": 30.0, "timestep_min": 5.0},
            {
                "area_km2": 45.0,
                "lutz_length_km": 8.2,
                "lutz_centroid_length_km": 4.5,
                "lutz_slope_m_per_m": 0.023,
                "lutz_manning_n": 0.035,
                "lutz_forest_pct": 30.0,
                "lutz_urban_pct": 5.0,
            },
            {
                "area_km2": 1.3,
                "urban_effective_precip_mm": 1.305,
                "urban_duration_h": 0.167,
                "urban_fraction": 0.05,
                "timestep_min": 2.0,
            },
        ),
    ),
    Command(
        name="uh clark",
        operation_id="uh_clark",
        summary="Hydrogram jednostkowy Clarka (translacja + zbiornik liniowy) z tc oraz R lub R/tc.",
        summary_en="Clark unit hydrograph (translation + linear reservoir) from tc and R or R/tc.",
        description=(
            "Hydrogram jednostkowy Clarka (1945) w dwóch krokach: (1) translacja "
            "histogramem czas–powierzchnia o krzywej eliptycznej HEC-HMS, "
            "A_cum = 1,414·τ^1,5 dla τ ≤ 0,5 i 1 − 1,414·(1−τ)^1,5 dla τ > 0,5 "
            "(τ = t/tc); (2) tłumienie w zbiorniku liniowym S = R·O, O_t = O_{t−1} "
            "+ C1·(I_t + I_{t−1} − 2·O_{t−1}), C1 = dt/(2R + dt). IUH jest "
            "normalizowany do 1, a hydrogram D-minutowy to różnica krzywej S i jej "
            "kopii opóźnionej o D, podzielona przez D i przeskalowana "
            "objętością 1 mm × A [m³/s na mm]. tc [min] jest czasem translacji "
            "(z dowolnej metody grupy `tc`). Stałą retencji R podaje się wprost "
            "(`r_min` [min]) albo przez stosunek `r_tc_ratio` = R/tc (typowo "
            "0,2–0,4 zlewnie strome i miejskie, 0,4–0,8 przeciętne, 0,8–1,5 "
            "płaskie i bagienne) — dokładnie jedna z tych opcji. Czas trwania "
            "opadu D może być dowolny (> 0), nie musi być wielokrotnością kroku: "
            "krzywa S jest interpolowana liniowo między krokami, a objętość "
            "hydrogramu to 1 mm (bez ogona odpowiedzi dłuższego niż "
            "`total_duration_min`); krzywa S ma rozdzielczość jednego kroku, "
            "więc D krótszy od kroku daje hydrogram dla D = krok (aby go "
            "rozróżnić, zmniejsz krok). Przybliżony lag: tc/2 + "
            "R. Wynik: tc, R, lag, czas do szczytu, szczyt [m³/s na mm] i rzędne. "
            "Literatura: Clark, C.O. (1945), Storage and the unit hydrograph, "
            "Transactions ASCE 110, 1419–1446; USACE, HEC-HMS Technical Reference "
            "Manual."
        ),
        description_en=(
            "The Clark (1945) unit hydrograph in two steps: (1) translation with a "
            "time-area histogram of the HEC-HMS elliptical curve, A_cum = "
            "1.414·τ^1.5 for τ <= 0.5 and 1 - 1.414·(1-τ)^1.5 for τ > 0.5 (τ = "
            "t/tc); (2) attenuation in a linear reservoir S = R·O, O_t = O_{t-1} + "
            "C1·(I_t + I_{t-1} - 2·O_{t-1}), C1 = dt/(2R + dt). The IUH is "
            "normalized to 1 and the D-minute hydrograph is the difference of the "
            "S-curve and its copy lagged by D, divided by D and scaled by the "
            "volume 1 mm × A [m3/s per mm]. tc [min] is the translation time (from "
            "any method of the `tc` group). The storage constant R is given "
            "directly (`r_min` [min]) or through the ratio `r_tc_ratio` = R/tc "
            "(typically 0.2-0.4 steep and urban catchments, 0.4-0.8 average, "
            "0.8-1.5 flat and swampy) - exactly one of the two. The rainfall "
            "duration D may be any value > 0, not necessarily a multiple of the "
            "time step: the S-curve is interpolated linearly between the steps and "
            "the volume of the hydrograph is 1 mm (without a response tail beyond "
            "`total_duration_min`); the S-curve is resolved "
            "to one step, so a D shorter than the step gives the hydrograph of "
            "D = step (reduce the step to resolve it). Approximate lag: tc/2 + R. "
            "Result: tc, R, lag, time to peak, peak [m3/s per mm] and the "
            "ordinates. References: Clark, C.O. (1945), Storage and the unit "
            "hydrograph, Transactions ASCE 110, 1419-1446; USACE, HEC-HMS "
            "Technical Reference Manual."
        ),
        function="hydrolog.operations:uh_clark",
        options=(
            _AREA,
            _TC,
            Option(
                name="r_min",
                type="number",
                description=(
                    "Stała retencji zbiornika liniowego R [min]; > 0 (alternatywa "
                    "dla `r_tc_ratio`)."
                ),
                description_en=(
                    "Storage constant R of the linear reservoir [min]; > 0 "
                    "(alternative to `r_tc_ratio`)."
                ),
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="r_tc_ratio",
                type="number",
                description=(
                    "Stosunek R/tc [-]; > 0, typowo 0,2–1,5 (alternatywa dla "
                    "`r_min`; R = stosunek · tc)."
                ),
                description_en=(
                    "Ratio R/tc [-]; > 0, typically 0.2-1.5 (alternative to "
                    "`r_min`; R = ratio · tc)."
                ),
                exclusive_minimum=0,
            ),
            _timestep(
                5.0,
                "Przy domyślnym D jest zarazem czasem trwania opadu jednostkowego.",
                "With the default D it is also the unit rainfall duration.",
            ),
            _rainfall_duration(
                "Dowolny D > 0; krótszy od kroku daje hydrogram dla D = krok; "
                "domyślnie równy krokowi.",
                "Any D > 0; one shorter than the step gives the hydrograph of D = "
                "step; defaults to the step.",
            ),
            _total_duration(
                "Domyślnie tc + 5·R + D.",
                "Defaults to tc + 5·R + D.",
            ),
        ),
        one_of=(("r_min",), ("r_tc_ratio",)),
        examples=(
            {"area_km2": 45.3, "tc_min": 120.0, "r_min": 60.0, "timestep_min": 10.0},
            {"area_km2": 45.3, "tc_min": 120.0, "r_tc_ratio": 0.5},
        ),
    ),
    Command(
        name="uh snyder",
        operation_id="uh_snyder",
        summary="Syntetyczny hydrogram jednostkowy Snydera z L, Lc oraz współczynników Ct i Cp.",
        summary_en="Snyder synthetic unit hydrograph from L, Lc and the coefficients Ct and Cp.",
        description=(
            "Syntetyczny hydrogram jednostkowy Snydera (1938) w wersji metrycznej. "
            "Lag zlewni tL = Ct·(L·Lc)^0,3 [h], gdzie L to długość cieku "
            "głównego, a Lc — długość od przekroju zamykającego do punktu "
            "najbliższego środka ciężkości zlewni [km]; standardowy czas opadu tD "
            "= tL/5,5. Dla D = tD: tp = tL + tD/2, qp = 0,275·Cp·A/tL [m³/s na mm]. "
            "Dla D ≠ tD: tLR = tL + 0,25·(D − tD) (nie mniej niż 0,1·tL), tpR = "
            "tLR + D/2, qpR = 0,275·Cp·A/tLR; podstawa tb = 0,556·A/qpR [h]. "
            "Kształt to rozkład gamma (n = 3,7) dopasowany do tp i qp, normowany "
            "do objętości 1 mm × A. Model ma własne równanie lagu i NIE używa "
            "zewnętrznego czasu koncentracji — nie łączyć z wynikami `tc ...`. "
            "Współczynniki (SI): Ct 1,35–1,65 (mniejsze dla zlewni górskich), Cp "
            "0,4–0,8 (Ct i Cp są ujemnie skorelowane). Wynik: tL, tD, tLR, tp, qp, "
            "tb i rzędne. Literatura: Snyder, F.F. (1938), Synthetic unit-graphs, "
            "Transactions AGU 19, 447–454; Bedient, P.B., Huber, W.C. (1992), "
            "Hydrology and Floodplain Analysis."
        ),
        description_en=(
            "The Snyder (1938) synthetic unit hydrograph in metric form. Basin lag "
            "tL = Ct·(L·Lc)^0.3 [h], where L is the main stream length and Lc the "
            "length from the outlet to the point nearest to the catchment "
            "centroid [km]; standard rainfall duration tD = tL/5.5. For D = tD: "
            "tp = tL + tD/2, qp = 0.275·Cp·A/tL [m3/s per mm]. For D != tD: tLR = "
            "tL + 0.25·(D - tD) (at least 0.1·tL), tpR = tLR + D/2, qpR = "
            "0.275·Cp·A/tLR; time base tb = 0.556·A/qpR [h]. The shape is a gamma "
            "distribution (n = 3.7) fitted to tp and qp, normalized to the volume "
            "1 mm × A. The model has its own lag equation and does NOT use an "
            "external time of concentration - do not combine it with `tc ...` "
            "results. Coefficients (SI): Ct 1.35-1.65 (lower for mountain "
            "catchments), Cp 0.4-0.8 (Ct and Cp are negatively correlated). "
            "Result: tL, tD, tLR, tp, qp, tb and the ordinates. References: "
            "Snyder, F.F. (1938), Synthetic unit-graphs, Transactions AGU 19, "
            "447-454; Bedient, P.B., Huber, W.C. (1992), Hydrology and Floodplain "
            "Analysis."
        ),
        function="hydrolog.operations:uh_snyder",
        options=(
            _AREA,
            Option(
                name="length_km",
                type="number",
                description=(
                    "Długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego L [km]; > 0."
                ),
                description_en=(
                    "Length of the main stream from the divide to the outlet L "
                    "[km]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="centroid_length_km",
                type="number",
                description=(
                    "Długość cieku od przekroju zamykającego do punktu najbliższego "
                    "środka ciężkości zlewni Lc [km]; > 0."
                ),
                description_en=(
                    "Length along the main stream from the outlet to the point "
                    "nearest to the catchment centroid Lc [km]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="ct",
                type="number",
                description=(
                    "Współczynnik czasowy Ct (SI), > 0; typowo 1,35–1,65; "
                    "domyślnie 1,5."
                ),
                description_en=(
                    "Time coefficient Ct (SI), > 0; typically 1.35-1.65; "
                    "default 1.5."
                ),
                exclusive_minimum=0,
                default=1.5,
            ),
            Option(
                name="cp",
                type="number",
                description=(
                    "Współczynnik szczytowy Cp, > 0; typowo 0,4–0,8; domyślnie " "0,6."
                ),
                description_en=(
                    "Peak coefficient Cp, > 0; typically 0.4-0.8; default 0.6."
                ),
                exclusive_minimum=0,
                default=0.6,
            ),
            _timestep(
                30.0,
                "Typowe lagi zlewni rzędu godzin dopuszczają krok 30 min.",
                "Typical basin lags of hours allow a 30 min step.",
            ),
            _rainfall_duration(
                "Domyślnie standardowy czas opadu tD = tL/5,5.",
                "Defaults to the standard duration tD = tL/5.5.",
            ),
            _total_duration(
                "Domyślnie podstawa hydrogramu tb.",
                "Defaults to the time base tb.",
            ),
        ),
        examples=(
            {"area_km2": 100.0, "length_km": 15.0, "centroid_length_km": 8.0},
            {
                "area_km2": 45.3,
                "length_km": 12.5,
                "centroid_length_km": 6.0,
                "ct": 1.65,
                "cp": 0.565,
                "timestep_min": 10.0,
            },
        ),
    ),
)
