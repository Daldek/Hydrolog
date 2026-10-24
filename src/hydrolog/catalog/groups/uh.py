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
    description_pl="Powierzchnia zlewni [km²]; > 0.",
    description="Catchment area [km2]; > 0.",
    required=True,
    exclusive_minimum=0,
    unit="km2",
)


def _timestep(default: float, note_pl: str, note_en: str) -> Option:
    return Option(
        name="timestep_min",
        type="number",
        description_pl=(
            f"Krok czasowy hydrogramu [min]; > 0; domyślnie {default:g}. {note_pl}"
        ),
        description=(
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
        description_pl=(
            "Czas trwania opadu jednostkowego D, dla którego liczony jest "
            f"hydrogram [min]; > 0. {note_pl}"
        ),
        description=(
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
        description_pl=(f"Całkowita długość wyniku [min]; > 0. {note_pl}"),
        description=(f"Total length of the result [min]; > 0. {note_en}"),
        exclusive_minimum=0,
        unit="min",
    )


_TC = Option(
    name="tc_min",
    type="number",
    description_pl=("Czas koncentracji [min]; > 0 (z dowolnej metody grupy `tc`)."),
    description=(
        "Time of concentration [min]; > 0 (from any method of the `tc` group)."
    ),
    required=True,
    exclusive_minimum=0,
    unit="min",
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="uh scs",
        operation_id="hydrolog_uh_scs",
        summary_pl=(
            "Oblicz hydrogram jednostkowy SCS (NRCS) z powierzchni i czasu "
            "koncentracji."
        ),
        summary=(
            "Compute the SCS (NRCS) unit hydrograph from the area and the time of "
            "concentration."
        ),
        description_pl=(
            "Bezwymiarowy hydrogram jednostkowy SCS (NRCS, TR-55) w m3/s na mm. "
            "Stosuj, gdy znany jest czas koncentracji tc (z komendy `tc`). Nie do "
            "hydrogramu odpływu (`hydrograph generate`). Kształt z tablicy; krok jest "
            "zarazem czasem trwania opadu jednostkowego."
        ),
        description=(
            "Dimensionless SCS (NRCS, TR-55) unit hydrograph in m3/s per mm. Use when "
            "tc is known (from a `tc` command). Not for a runoff hydrograph "
            "(`hydrograph generate`). Fixed table shape; the step is also the unit "
            "rainfall duration."
        ),
        function="hydrolog.operations.uh_scs",
        options=(
            _AREA,
            _TC,
            _timestep(
                5.0,
                "Jest zarazem czasem trwania opadu jednostkowego D.",
                "It is also the unit rainfall duration D.",
            ),
        ),
        result_schema="hydrolog-uh-scs/1",
        cardinality="bounded",
        rules=(
            "Pass tc_min in minutes, taken from a `tc` command.",
            "Read ordinates in m3/s per mm of effective rain.",
            "Check `notices` in the result.",
        ),
        rules_pl=(
            "Podaj tc_min w minutach, z komendy `tc`.",
            "Rzędne odczytuj w m3/s na mm opadu efektywnego.",
            "Sprawdź `notices` w wyniku.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "model": "scs",
                "peak_discharge_m3s_per_mm": 10.0061,
                "time_to_peak_min": 56.5,
                "lag_time_min": 54.0,
                "time_base_min": 282.5,
            },
        ),
        examples=({"area_km2": 45.3, "tc_min": 90.0, "timestep_min": 5.0},),
    ),
    Command(
        name="uh nash",
        operation_id="hydrolog_uh_nash",
        summary_pl=(
            "Oblicz hydrogram jednostkowy Nasha z n i K, metodą Lutza lub regresją "
            "miejską."
        ),
        summary=(
            "Compute the Nash cascade unit hydrograph from n and K, the Lutz method or"
            " urban regression."
        ),
        description_pl=(
            "Kaskada zbiorników liniowych Nasha (1957), hydrogram jednostkowy w m3/s "
            "na mm. Podaj dokładnie jedną grupę parametrów: `n` + `k_min`, Lutz "
            "(zlewnie niekontrolowane) lub regresja miejska. Nie do kształtów opartych"
            " na tc (`uh scs`, `uh clark`)."
        ),
        description=(
            "Nash (1957) cascade of linear reservoirs, unit hydrograph in m3/s per mm."
            " Give exactly one parameter group: `n` + `k_min`, Lutz (ungauged "
            "catchments) or urban regression. Not for tc-based shapes (`uh scs`, `uh "
            "clark`)."
        ),
        function="hydrolog.operations.uh_nash",
        options=(
            _AREA,
            Option(
                name="n",
                type="number",
                description_pl=(
                    "Liczba zbiorników kaskady n (parametr kształtu, może być "
                    "ułamkowa); > 0, typowo 1–10. Razem z `k_min`."
                ),
                description=(
                    "Number of reservoirs n (shape parameter, may be fractional); "
                    "> 0, typically 1-10. Together with `k_min`."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="k_min",
                type="number",
                description_pl=(
                    "Stała magazynowania zbiornika K [min]; > 0, typowo 10–200. "
                    "Razem z `n`."
                ),
                description=(
                    "Storage constant K of a reservoir [min]; > 0, typically "
                    "10-200. Together with `n`."
                ),
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="lutz_length_km",
                type="number",
                description_pl=(
                    "Lutz: długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego L [km]; > 0."
                ),
                description=(
                    "Lutz: length of the main stream from the divide to the "
                    "outlet L [km]; > 0."
                ),
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="lutz_centroid_length_km",
                type="number",
                description_pl=(
                    "Lutz: długość cieku od przekroju zamykającego do punktu "
                    "najbliższego środka ciężkości zlewni Lc [km]; > 0, nie "
                    "większa niż L."
                ),
                description=(
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
                description_pl="Lutz: średni spadek cieku głównego J [m/m]; > 0.",
                description="Lutz: mean slope of the main stream J [m/m]; > 0.",
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="lutz_manning_n",
                type="number",
                description_pl=(
                    "Lutz: współczynnik szorstkości Manninga koryta n_M; > 0, "
                    "typowo 0,025–0,050 dla cieków naturalnych."
                ),
                description=(
                    "Lutz: Manning roughness coefficient of the channel n_M; > 0, "
                    "typically 0.025-0.050 for natural streams."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="lutz_urban_pct",
                type="number",
                description_pl=(
                    "Lutz: udział terenów zurbanizowanych U [%]; 0–100; domyślnie 0."
                ),
                description=("Lutz: share of urbanized area U [%]; 0-100; default 0."),
                minimum=0,
                maximum=100,
                unit="%",
            ),
            Option(
                name="lutz_forest_pct",
                type="number",
                description_pl=(
                    "Lutz: udział terenów leśnych W [%]; 0–100; domyślnie 0."
                ),
                description=("Lutz: share of forested area W [%]; 0-100; default 0."),
                minimum=0,
                maximum=100,
                unit="%",
            ),
            Option(
                name="urban_effective_precip_mm",
                type="number",
                description_pl=(
                    "Regresja miejska: suma opadu efektywnego H [mm]; > 0. Razem "
                    "z `urban_duration_h`."
                ),
                description=(
                    "Urban regression: total effective precipitation H [mm]; > 0. "
                    "Together with `urban_duration_h`."
                ),
                exclusive_minimum=0,
                unit="mm",
            ),
            Option(
                name="urban_duration_h",
                type="number",
                description_pl=(
                    "Regresja miejska: czas trwania opadu efektywnego D [h]; > 0. "
                    "Razem z `urban_effective_precip_mm`."
                ),
                description=(
                    "Urban regression: duration of the effective rainfall D [h]; "
                    "> 0. Together with `urban_effective_precip_mm`."
                ),
                exclusive_minimum=0,
                unit="h",
            ),
            Option(
                name="urban_fraction",
                type="number",
                description_pl=(
                    "Regresja miejska: wskaźnik urbanizacji U [-] (udział "
                    "powierzchni zabudowanej, 0 ≤ U < 1); domyślnie 0."
                ),
                description=(
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
        result_schema="hydrolog-uh-nash/1",
        cardinality="bounded",
        rules=(
            (
                "Give exactly one of the three parameter groups; other options are "
                "rejected."
            ),
            "Lutz needs lutz_centroid_length_km <= lutz_length_km.",
            "Check `notices` in the result.",
        ),
        rules_pl=(
            (
                "Podaj dokładnie jedną z trzech grup parametrów; pozostałe opcje są "
                "odrzucane."
            ),
            "Lutz wymaga lutz_centroid_length_km <= lutz_length_km.",
            "Sprawdź `notices` w wyniku.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "model": "nash",
                "estimation": "direct",
                "lag_time_min": 90.0,
                "time_to_peak_min": 65.0,
                "peak_discharge_m3s_per_mm": 6.79676,
                "parameters": {"n": 3.0, "k_min": 30.0},
            },
            {
                "estimation": "lutz",
                "lag_time_min": 158.712,
                "time_to_peak_min": 120.0,
                "peak_discharge_m3s_per_mm": 4.13768,
                "parameters": {"n": 3.75659, "k_min": 42.2491},
            },
            {
                "estimation": "urban_regression",
                "lag_time_min": 38.3523,
                "time_to_peak_min": 16.0,
                "peak_discharge_m3s_per_mm": 0.408326,
                "parameters": {"n": 1.62133, "k_min": 23.6549},
            },
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
        operation_id="hydrolog_uh_clark",
        summary_pl=(
            "Oblicz hydrogram jednostkowy Clarka z tc oraz stałej retencji R lub "
            "stosunku R/tc."
        ),
        summary=(
            "Compute the Clark unit hydrograph from tc and the storage constant R or "
            "the ratio R/tc."
        ),
        description_pl=(
            "Hydrogram jednostkowy Clarka (1945): translacja czas–powierzchnia i "
            "zbiornik liniowy, w m3/s na mm. Stosuj z tc z komendy `tc` i R. Nie do "
            "kształtów Nasha ani Snydera. Opad D krótszy od kroku działa jak D = krok."
        ),
        description=(
            "Clark (1945) unit hydrograph: time-area translation plus a linear "
            "reservoir, in m3/s per mm. Use with tc from a `tc` command and R. Not for"
            " Nash or Snyder shapes. A rainfall D shorter than the step acts as D = "
            "step."
        ),
        function="hydrolog.operations.uh_clark",
        options=(
            _AREA,
            _TC,
            Option(
                name="r_min",
                type="number",
                description_pl=(
                    "Stała retencji zbiornika liniowego R [min]; > 0 (alternatywa "
                    "dla `r_tc_ratio`)."
                ),
                description=(
                    "Storage constant R of the linear reservoir [min]; > 0 "
                    "(alternative to `r_tc_ratio`)."
                ),
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="r_tc_ratio",
                type="number",
                description_pl=(
                    "Stosunek R/tc [-]; > 0, typowo 0,2–1,5 (alternatywa dla "
                    "`r_min`; R = stosunek · tc)."
                ),
                description=(
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
        result_schema="hydrolog-uh-clark/1",
        cardinality="bounded",
        rules=(
            "Give exactly one of r_min and r_tc_ratio.",
            "Pass tc_min in minutes, taken from a `tc` command.",
            "Keep timestep_min at most 2 R, else it is a validation_error.",
            "Check `notices` in the result.",
        ),
        rules_pl=(
            "Podaj dokładnie jedną z opcji r_min i r_tc_ratio.",
            "Podaj tc_min w minutach, z komendy `tc`.",
            "Krok timestep_min najwyżej 2 R, inaczej validation_error.",
            "Sprawdź `notices` w wyniku.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "model": "clark",
                "lag_time_min": 120.0,
                "time_to_peak_min": 100.0,
                "peak_discharge_m3s_per_mm": 5.83984,
                "parameters": {"tc_min": 120.0, "r_min": 60.0},
            },
            {
                "model": "clark",
                "lag_time_min": 120.0,
                "time_to_peak_min": 100.0,
                "peak_discharge_m3s_per_mm": 5.86008,
                "parameters": {"tc_min": 120.0, "r_min": 60.0, "r_tc_ratio": 0.5},
            },
        ),
        examples=(
            {"area_km2": 45.3, "tc_min": 120.0, "r_min": 60.0, "timestep_min": 10.0},
            {"area_km2": 45.3, "tc_min": 120.0, "r_tc_ratio": 0.5},
        ),
    ),
    Command(
        name="uh snyder",
        operation_id="hydrolog_uh_snyder",
        summary_pl=(
            "Oblicz syntetyczny hydrogram jednostkowy Snydera z L, Lc oraz "
            "współczynników Ct i Cp."
        ),
        summary=(
            "Compute the Snyder synthetic unit hydrograph from L, Lc and the "
            "coefficients Ct and Cp."
        ),
        description_pl=(
            "Syntetyczny hydrogram jednostkowy Snydera (1938) w m3/s na mm, z własnym "
            "równaniem lagu. Stosuj dla zlewni niekontrolowanych ze znanymi "
            "długościami cieku. Nie używa tc: nie łącz z wynikami `tc`; dla kształtów "
            "opartych na tc użyj `uh scs`."
        ),
        description=(
            "Snyder (1938) synthetic unit hydrograph in m3/s per mm with its own lag "
            "equation. Use for ungauged catchments with known stream lengths. Does not"
            " use tc: do not feed it `tc` results; for tc-based shapes use `uh scs`."
        ),
        function="hydrolog.operations.uh_snyder",
        options=(
            _AREA,
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego L [km]; > 0."
                ),
                description=(
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
                description_pl=(
                    "Długość cieku od przekroju zamykającego do punktu najbliższego "
                    "środka ciężkości zlewni Lc [km]; > 0."
                ),
                description=(
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
                description_pl=(
                    "Współczynnik czasowy Ct (SI), > 0; typowo 1,35–1,65; "
                    "domyślnie 1,5."
                ),
                description=(
                    "Time coefficient Ct (SI), > 0; typically 1.35-1.65; default 1.5."
                ),
                exclusive_minimum=0,
                default=1.5,
            ),
            Option(
                name="cp",
                type="number",
                description_pl=(
                    "Współczynnik szczytowy Cp, > 0; typowo 0,4–0,8; domyślnie 0,6."
                ),
                description=(
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
        result_schema="hydrolog-uh-snyder/1",
        cardinality="bounded",
        rules=(
            "Give L and Lc in km and Ct, Cp in SI units.",
            "Do not pass a time of concentration.",
            "Check `notices` in the result.",
        ),
        rules_pl=(
            "Podaj L i Lc w km oraz Ct, Cp w jednostkach SI.",
            "Nie podawaj czasu koncentracji.",
            "Sprawdź `notices` w wyniku.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "model": "snyder",
                "lag_time_min": 378.44,
                "time_to_peak_min": 412.843,
                "peak_discharge_m3s_per_mm": 2.6211,
                "time_base_min": 1275.23,
            },
            {
                "model": "snyder",
                "lag_time_min": 361.538,
                "time_to_peak_min": 394.405,
                "peak_discharge_m3s_per_mm": 1.23639,
                "time_base_min": 1293.74,
            },
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
