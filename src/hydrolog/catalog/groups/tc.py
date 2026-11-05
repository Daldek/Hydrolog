"""Group ``tc``: time of concentration.

One command per empirical formula of :class:`~hydrolog.time.ConcentrationTime`
(``tc kirpich``, ``tc nrcs``, ``tc giandotti``, ``tc faa``, ``tc kerby``,
``tc kerby-kirpich``) and ``tc watershed``, which applies one of the methods to a
:class:`~hydrolog.morphometry.WatershedParameters` file. All results are given in
minutes and hours. Each command serves the typical ranges it checks
(``typical_ranges``, :mod:`hydrolog.catalog.groups._typical`).
"""

from __future__ import annotations

from hydrolog.catalog.groups._typical import (
    TC_METHODS,
    WATERSHED_TC_RANGES,
    formula_ranges,
    typically,
)
from hydrolog.catalog.spec import Command, Option

_KERBY_TABLE_PL = (
    "Typowe wartości N: 0,02 gładka nawierzchnia nieprzepuszczalna; 0,10 gładka "
    "twarda gleba; 0,20 słaba trawa, uprawy rzędowe; 0,40 pastwisko, przeciętna "
    "trawa; 0,60 las liściasty; 0,80 gęsta trawa, las iglasty."
)
_KERBY_TABLE_EN = (
    "Typical N: 0.02 smooth impervious surface; 0.10 smooth bare packed soil; "
    "0.20 poor grass, row crops; 0.40 pasture, average grass; 0.60 deciduous "
    "forest; 0.80 dense grass, coniferous forest."
)

_CN = Option(
    name="cn",
    type="number",
    description_pl=(
        "Liczba krzywej CN dla AMC II, 1–100 (w równaniu metody "
        f"{typically('nrcs', 'cn', 'pl')}); może być ułamkowa (np. średnia ważona "
        "z `cn weighted`)."
    ),
    description=(
        "Curve Number CN for AMC II, 1-100 (in the equation of the method "
        f"{typically('nrcs', 'cn')}); may be fractional (e.g. a weighted mean from "
        "`cn weighted`)."
    ),
    required=True,
    minimum=1,
    maximum=100,
)

_RETARDANCE = Option(
    name="retardance",
    type="number",
    description_pl=(
        "Współczynnik retardacji (szorstkości) Kerby'ego N, > 0; "
        f"{typically('kerby', 'retardance', 'pl')}. {_KERBY_TABLE_PL}"
    ),
    description=(
        "Kerby retardance (roughness) coefficient N, > 0; "
        f"{typically('kerby', 'retardance')}. {_KERBY_TABLE_EN}"
    ),
    required=True,
    exclusive_minimum=0,
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="tc kirpich",
        operation_id="hydrolog_tc_kirpich",
        summary_pl=(
            "Oblicz czas koncentracji wzorem Kirpicha (długość i spadek drogi spływu)."
        ),
        summary="Compute time of concentration with the Kirpich formula.",
        description_pl=(
            "Czas koncentracji tc [min, h] wzorem Kirpicha z długości [km] i spadku "
            "[m/m] najdłuższej drogi spływu, od działu wodnego do przekroju. Użyj dla "
            "małych zlewni rolniczych jak te z jego danych; dla spływu "
            "powierzchniowego z korytem użyj `tc kerby-kirpich`. Spadek spoza danych "
            "daje uwagę (`typical_ranges`)."
        ),
        description=(
            "Kirpich tc [min, h] from the length [km] and slope [m/m] of the longest "
            "flow path, divide to outlet. Use for small agricultural watersheds "
            "like those of his data; for overland plus channel flow use "
            "`tc kerby-kirpich`. A slope outside the data is a notice "
            "(`typical_ranges`)."
        ),
        function="hydrolog.operations.tc_kirpich",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość najdłuższej drogi spływu, wzdłuż cieku od przekroju "
                    "zamykającego do najdalszego punktu na dziale wodnym [km]; > 0."
                ),
                description=(
                    "Length of the longest flow path, along the watercourse from the "
                    "outlet to the most remote point on the divide [km]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Spadek tej drogi: wysokość jej początku na dziale wodnym minus "
                    "wysokość przekroju, przez jej długość [m/m] (nie w procentach); "
                    f"> 0 ({typically('kirpich', 'slope_m_per_m', 'pl')})."
                ),
                description=(
                    "Slope of that path: the elevation of its head on the divide "
                    "minus the outlet elevation, over its length [m/m] (not percent); "
                    f"> 0 ({typically('kirpich', 'slope_m_per_m')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
        ),
        examples=({"length_km": 8.2, "slope_m_per_m": 0.023},),
        result_schema="hydrolog-tc-kirpich/1",
        cardinality="single",
        rules=(
            "Give the slope in m/m, not percent.",
            "Read tc_min or tc_h from the result.",
            "Check `notices` for out-of-range warnings.",
        ),
        rules_pl=(
            "Podaj spadek w m/m, nie w procentach.",
            "Odczytaj tc_min lub tc_h z wyniku.",
            "Sprawdź `notices` pod kątem ostrzeżeń o zakresie.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges("kirpich", ("length_km", "slope_m_per_m")),
        example_results=(
            {
                "method": "kirpich",
                "tc_min": 85.9733,
                "tc_h": 1.43289,
                "parameters": {"length_km": 8.2, "slope_m_per_m": 0.023},
            },
        ),
    ),
    Command(
        name="tc nrcs",
        operation_id="hydrolog_tc_nrcs",
        summary_pl=(
            "Oblicz czas koncentracji metodą opóźnienia NRCS (NEH 630) z L, Y i CN."
        ),
        summary="Compute time of concentration with the NRCS lag method (NEH 630).",
        description_pl=(
            "Czas koncentracji tc [min, h] równaniem opóźnienia NRCS (NEH 630, rozdz. "
            "15; tc = opóźnienie / 0,6) z długości najdłuższej drogi spływu [km], "
            "średniego spadku terenu zlewni [m/m] i CN. Użyj, gdy CN jest znane "
            "(`cn lookup`, `cn weighted`). Zwraca tc, nie tlag (tlag = 0,6·tc). CN "
            "spoza równania daje uwagę (`typical_ranges`)."
        ),
        description=(
            "NRCS lag tc [min, h] (NEH 630 ch. 15; tc = lag / 0.6) from the longest "
            "flow path [km], the average land slope of the watershed [m/m] and CN. "
            "Use when CN is known (`cn lookup`, `cn weighted`). Returns tc, not lag "
            "(lag = 0.6 * tc). A CN outside the equation is a notice "
            "(`typical_ranges`)."
        ),
        function="hydrolog.operations.tc_nrcs",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość spływu: najdłuższa droga spływu od działu wodnego do "
                    "przekroju zamykającego [km]; > 0."
                ),
                description=(
                    "Flow length: the longest flow path from the watershed divide to "
                    "the outlet [km]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek terenu zlewni Y [m/m] (nie w procentach, nie spadek "
                    "drogi spływu); > 0."
                ),
                description=(
                    "Average land slope of the watershed Y [m/m] (not percent, not "
                    "the slope of the flow path); > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _CN,
        ),
        examples=({"length_km": 8.2, "slope_m_per_m": 0.023, "cn": 72},),
        result_schema="hydrolog-tc-nrcs/1",
        cardinality="single",
        rules=(
            "Give the slope in m/m, not percent.",
            "Pass CN for AMC II; a fractional CN is accepted.",
            "The result is tc, not lag time.",
        ),
        rules_pl=(
            "Podaj spadek w m/m, nie w procentach.",
            "Podaj CN dla AMC II; ułamkowe CN jest dopuszczalne.",
            "Wynik to tc, nie czas opóźnienia.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges("nrcs", ("length_km", "slope_m_per_m", "cn")),
        example_results=(
            {
                "method": "nrcs",
                "tc_min": 369.047,
                "tc_h": 6.15078,
                "parameters": {"length_km": 8.2, "slope_m_per_m": 0.023, "cn": 72.0},
            },
        ),
    ),
    Command(
        name="tc giandotti",
        operation_id="hydrolog_tc_giandotti",
        summary_pl="Oblicz czas koncentracji wzorem Giandottiego (A, L, H).",
        summary="Compute time of concentration with the Giandotti formula.",
        description_pl=(
            "Czas koncentracji tc [min, h] wzorem Giandottiego z powierzchni [km²], "
            "długości cieku [km] i różnicy wysokości [m]. Użyj dla dużych zlewni jak "
            "jego zlewnie włoskie; dla małych zlewni użyj `tc kirpich`. Powierzchnia "
            "spoza nich daje uwagę (`typical_ranges`)."
        ),
        description=(
            "Giandotti tc [min, h] from area [km2], channel length [km] and "
            "elevation difference [m]. Use for large watersheds like his Italian "
            "basins; for small watersheds use `tc kirpich`. An area outside them is "
            "a notice (`typical_ranges`)."
        ),
        function="hydrolog.operations.tc_giandotti",
        options=(
            Option(
                name="area_km2",
                type="number",
                description_pl=(
                    "Powierzchnia zlewni [km²]; > 0 "
                    f"({typically('giandotti', 'area_km2', 'pl')})."
                ),
                description=(
                    f"Watershed area [km2]; > 0 ({typically('giandotti', 'area_km2')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km2",
            ),
            Option(
                name="length_km",
                type="number",
                description_pl="Długość cieku głównego [km]; > 0.",
                description="Main channel length [km]; > 0.",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="elevation_diff_m",
                type="number",
                description_pl=(
                    "Różnica wysokości między średnią wysokością zlewni a "
                    "przekrojem zamykającym [m]; > 0."
                ),
                description=(
                    "Difference between the mean watershed elevation and the "
                    "outlet [m]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m",
            ),
        ),
        examples=({"area_km2": 145.0, "length_km": 21.5, "elevation_diff_m": 320.0},),
        result_schema="hydrolog-tc-giandotti/1",
        cardinality="single",
        rules=(
            "Give the area in km2, not hectares.",
            "Give the elevation difference from the mean elevation, not the maximum.",
            "Check `notices` for out-of-range warnings.",
        ),
        rules_pl=(
            "Podaj powierzchnię w km², nie w hektarach.",
            "Podaj różnicę względem średniej wysokości zlewni, nie maksimum.",
            "Sprawdź `notices` pod kątem ostrzeżeń o zakresie.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges(
            "giandotti", ("area_km2", "length_km", "elevation_diff_m")
        ),
        example_results=(
            {
                "method": "giandotti",
                "tc_min": 337.156,
                "tc_h": 5.61927,
                "parameters": {
                    "area_km2": 145.0,
                    "length_km": 21.5,
                    "elevation_diff_m": 320.0,
                },
            },
        ),
    ),
    Command(
        name="tc faa",
        operation_id="hydrolog_tc_faa",
        summary_pl="Oblicz czas spływu powierzchniowego metodą FAA (L, spadek, C).",
        summary="Compute overland flow time with the FAA method.",
        description_pl=(
            "Czas spływu powierzchniowego tc [min, h] metodą FAA z długości spływu "
            "[km], spadku [m/m] i współczynnika odpływu C. Użyj dla krótkich, "
            "płaskich dróg spływu; dla zlewni z korytem użyj `tc kerby-kirpich` lub "
            "`tc kirpich`."
        ),
        description=(
            "FAA overland flow tc [min, h] from flow length [km], slope [m/m] and "
            "runoff coefficient C. Use for short, flat flow paths; for a watershed "
            "with a channel use `tc kerby-kirpich` or `tc kirpich`."
        ),
        function="hydrolog.operations.tc_faa",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego od najdalszego punktu do wlotu "
                    "[km]; > 0."
                ),
                description=(
                    "Overland flow length from the most remote point to the inlet "
                    "[km]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Spadek powierzchni spływu powierzchniowego [m/m] (nie w "
                    "procentach); > 0."
                ),
                description=(
                    "Slope of the overland flow surface [m/m] (not percent); > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="runoff_coeff",
                type="number",
                description_pl=(
                    "Współczynnik odpływu C metody wymiernej, 0 < C ≤ 1 "
                    f"({typically('faa', 'runoff_coeff', 'pl')})."
                ),
                description=(
                    "Rational-method runoff coefficient C, 0 < C <= 1 "
                    f"({typically('faa', 'runoff_coeff')})."
                ),
                required=True,
                exclusive_minimum=0,
                maximum=1,
            ),
        ),
        examples=({"length_km": 0.15, "slope_m_per_m": 0.02, "runoff_coeff": 0.6},),
        result_schema="hydrolog-tc-faa/1",
        cardinality="single",
        rules=(
            "Give the slope in m/m, not percent.",
            "Treat the result as overland flow time, not watershed tc.",
            "Check `notices` for out-of-range warnings.",
        ),
        rules_pl=(
            "Podaj spadek w m/m, nie w procentach.",
            "Traktuj wynik jako czas spływu powierzchniowego, nie tc zlewni.",
            "Sprawdź `notices` pod kątem ostrzeżeń o zakresie.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges(
            "faa", ("length_km", "slope_m_per_m", "runoff_coeff")
        ),
        example_results=(
            {
                "method": "faa",
                "tc_min": 15.847,
                "tc_h": 0.264116,
                "parameters": {
                    "length_km": 0.15,
                    "slope_m_per_m": 0.02,
                    "runoff_coeff": 0.6,
                },
            },
        ),
    ),
    Command(
        name="tc kerby",
        operation_id="hydrolog_tc_kerby",
        summary_pl="Oblicz czas spływu powierzchniowego wzorem Kerby'ego.",
        summary="Compute overland flow time with the Kerby formula.",
        description_pl=(
            "Czas spływu powierzchniowego tc [min, h] wzorem Kerby'ego z długości "
            "spływu [km], spadku [m/m] i retardancji N. Użyj dla krótkich dróg "
            "spływu; dla zlewni z korytem użyj `tc kerby-kirpich` lub `tc kirpich`. "
            "Dla S < 0,002 stosuje poprawkę spadku."
        ),
        description=(
            "Kerby overland flow tc [min, h] from flow length [km], slope [m/m] and "
            "retardance N. Use for short flow paths; for a watershed with a channel "
            "use `tc kerby-kirpich` or `tc kirpich`. Applies a low-slope adjustment "
            "for S < 0.002."
        ),
        function="hydrolog.operations.tc_kerby",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego do początku wyraźnego koryta "
                    f"[km]; > 0 ({typically('kerby', 'length_km', 'pl')})."
                ),
                description=(
                    "Overland flow length up to a defined channel [km]; > 0 "
                    f"({typically('kerby', 'length_km')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Spadek terenu, po którym spływa woda [m/m] (nie w procentach); "
                    f"> 0 ({typically('kerby', 'slope_m_per_m', 'pl')})."
                ),
                description=(
                    "Slope of the terrain the overland flow runs on [m/m] (not "
                    f"percent); > 0 ({typically('kerby', 'slope_m_per_m')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _RETARDANCE,
        ),
        examples=({"length_km": 0.10, "slope_m_per_m": 0.008, "retardance": 0.4},),
        result_schema="hydrolog-tc-kerby/1",
        cardinality="single",
        rules=(
            "Give the slope in m/m, not percent.",
            "Pick retardance N from the typical values in the option description.",
            "Treat the result as overland flow time, not watershed tc.",
        ),
        rules_pl=(
            "Podaj spadek w m/m, nie w procentach.",
            "Wybierz retardancję N z typowych wartości w opisie opcji.",
            "Traktuj wynik jako czas spływu powierzchniowego, nie tc zlewni.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges(
            "kerby", ("length_km", "slope_m_per_m", "retardance")
        ),
        example_results=(
            {
                "method": "kerby",
                "tc_min": 24.9766,
                "tc_h": 0.416277,
                "parameters": {
                    "length_km": 0.1,
                    "slope_m_per_m": 0.008,
                    "retardance": 0.4,
                },
            },
        ),
    ),
    Command(
        name="tc kerby-kirpich",
        operation_id="hydrolog_tc_kerby_kirpich",
        summary_pl="Oblicz czas koncentracji metodą Kerby–Kirpich (spływ + koryto).",
        summary="Compute time of concentration with the Kerby-Kirpich method.",
        description_pl=(
            "Czas koncentracji tc [min, h] złożoną metodą Kerby–Kirpich na "
            "najdłuższej drodze spływu: spływ powierzchniowy (Kerby) plus reszta "
            "drogi jako koryto (Kirpich, ze spadkiem całej drogi). Użyj, gdy droga "
            "spływu ma oba odcinki; dla samego spływu użyj `tc kerby`. Wartość spoza "
            "danych metody daje uwagę (`typical_ranges`)."
        ),
        description=(
            "Kerby-Kirpich tc [min, h] on the longest flow path: overland segment "
            "(Kerby) plus the rest of the path as channel (Kirpich, at the slope of "
            "the whole path). Use when the flow path has both; for overland flow "
            "only use `tc kerby`. A value outside the data of the method is a "
            "notice (`typical_ranges`)."
        ),
        function="hydrolog.operations.tc_kerby_kirpich",
        options=(
            Option(
                name="overland_length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego od najdalszego punktu do "
                    "początku wyraźnego cieku [km]; > 0 "
                    f"({typically('kerby_kirpich', 'overland_length_km', 'pl')})."
                ),
                description=(
                    "Overland flow length from the most distant point to the start "
                    "of a defined channel [km]; > 0 "
                    f"({typically('kerby_kirpich', 'overland_length_km')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="overland_slope_m_per_m",
                type="number",
                description_pl=(
                    "Spadek terenu, po którym spływa woda po stoku [m/m]; > 0."
                ),
                description=(
                    "Slope of the terrain the overland flow runs on [m/m]; > 0."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _RETARDANCE,
            Option(
                name="flow_path_length_km",
                type="number",
                description_pl=(
                    "Długość najdłuższej drogi spływu od działu wodnego do przekroju "
                    "zamykającego, z odcinkiem spływu po stoku [km]; większa niż "
                    "`overland_length_km` "
                    f"({typically('kerby_kirpich', 'flow_path_length_km', 'pl')})."
                ),
                description=(
                    "Length of the longest flow path from the watershed divide to "
                    "the outlet, the overland segment included [km]; greater than "
                    "`overland_length_km` "
                    f"({typically('kerby_kirpich', 'flow_path_length_km')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="flow_path_slope_m_per_m",
                type="number",
                description_pl=(
                    "Spadek najdłuższej drogi spływu: wysokość jej początku na "
                    "dziale wodnym minus wysokość przekroju, przez jej długość "
                    "[m/m]; > 0 "
                    f"({typically('kerby_kirpich', 'flow_path_slope_m_per_m', 'pl')})."
                ),
                description=(
                    "Slope of the longest flow path: the elevation of its head on "
                    "the divide minus the outlet elevation, over its length [m/m]; "
                    f"> 0 ({typically('kerby_kirpich', 'flow_path_slope_m_per_m')})."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
        ),
        examples=(
            {
                "overland_length_km": 0.25,
                "overland_slope_m_per_m": 0.008,
                "retardance": 0.4,
                "flow_path_length_km": 5.25,
                "flow_path_slope_m_per_m": 0.005,
            },
        ),
        result_schema="hydrolog-tc-kerby-kirpich/1",
        cardinality="single",
        rules=(
            "Give slopes in m/m and lengths in km.",
            "Give the whole flow path: its channel segment is it minus the overland.",
            "Check `notices` for segments outside the formula range.",
        ),
        rules_pl=(
            "Podaj spadki w m/m, a długości w km.",
            "Podaj całą drogę spływu: odcinek koryta to ona minus spływ po stoku.",
            "Sprawdź `notices` pod kątem odcinków poza zakresem wzoru.",
        ),
        errors=("validation_error",),
        typical_ranges=formula_ranges(
            "kerby_kirpich",
            (
                "overland_length_km",
                "overland_slope_m_per_m",
                "retardance",
                "flow_path_length_km",
                "flow_path_slope_m_per_m",
            ),
        ),
        example_results=(
            {
                "method": "kerby_kirpich",
                "tc_min": 144.02,
                "tc_h": 2.40034,
                "parameters": {
                    "overland_length_km": 0.25,
                    "overland_slope_m_per_m": 0.008,
                    "retardance": 0.4,
                    "flow_path_length_km": 5.25,
                    "flow_path_slope_m_per_m": 0.005,
                },
            },
        ),
    ),
    Command(
        name="tc watershed",
        operation_id="hydrolog_tc_watershed",
        summary_pl="Oblicz czas koncentracji wybraną metodą z parametrów zlewni.",
        summary="Compute time of concentration by a chosen method from a watershed.",
        description_pl=(
            "Czas koncentracji tc [min, h] wybraną metodą z parametrów zlewni "
            "(WatershedParameters: obiekt `watershed` lub plik `watershed_file`). "
            "Użyj, gdy zlewnia jest już opisana; wymagane pola zależą od metody, "
            "braki dają błąd walidacji. Dla pojedynczych liczb użyj `tc <metoda>`."
        ),
        description=(
            "tc [min, h] by a chosen method from WatershedParameters (`watershed` "
            "object or `watershed_file`). Use when the watershed is already "
            "described; required fields depend on the method and missing ones "
            "raise a validation error. For plain numbers use `tc <method>`."
        ),
        function="hydrolog.operations.tc_watershed",
        options=(
            Option(
                name="watershed",
                type="object",
                description_pl=(
                    "Parametry zlewni jako obiekt WatershedParameters (wymagane "
                    "tylko `area_km2`; metoda bierze pola, które definiuje jej "
                    "źródło: Kirpich `flow_path_length_km` i "
                    "`flow_path_slope_m_per_m`, NRCS `flow_path_length_km`, "
                    "`mean_slope_m_per_m` i `cn`, Giandotti `channel_length_km`, "
                    "`elevation_mean_m` i `elevation_min_m`, FAA i Kerby "
                    "`overland_length_km`, `overland_slope_m_per_m` i "
                    "`runoff_coeff` albo `retardance`)."
                ),
                description=(
                    "Watershed parameters as a WatershedParameters object (only "
                    "`area_km2` is required; a method takes the fields its source "
                    "defines: Kirpich `flow_path_length_km` and "
                    "`flow_path_slope_m_per_m`, NRCS `flow_path_length_km`, "
                    "`mean_slope_m_per_m` and `cn`, Giandotti `channel_length_km`, "
                    "`elevation_mean_m` and `elevation_min_m`, FAA and Kerby "
                    "`overland_length_km`, `overland_slope_m_per_m` and "
                    "`runoff_coeff` or `retardance`)."
                ),
            ),
            Option(
                name="watershed_file",
                type="path",
                path_role="input",
                description_pl=(
                    "Plik JSON z parametrami zlewni (format "
                    "`WatershedParameters.to_json()`)."
                ),
                description=(
                    "JSON file with the watershed parameters (the "
                    "`WatershedParameters.to_json()` format)."
                ),
            ),
            Option(
                name="method",
                type="choice",
                description_pl=(
                    "Metoda obliczenia tc; domyślnie kirpich. Każda bierze pola "
                    "zlewni, które definiuje jej źródło, bez zastępników; brak pola "
                    "to błąd `missing_field`."
                ),
                description=(
                    "Method of computing tc; default kirpich. Each takes the "
                    "watershed fields its source defines, with no substitute; a "
                    "missing one is `missing_field`."
                ),
                choices=TC_METHODS,
                default="kirpich",
                meanings={
                    "kirpich": (
                        "Kirpich from the longest flow path: `flow_path_length_km`, "
                        "`flow_path_slope_m_per_m`."
                    ),
                    "nrcs": (
                        "NRCS lag method (NEH 630): `flow_path_length_km`, "
                        "`mean_slope_m_per_m`, `cn`."
                    ),
                    "giandotti": (
                        "Giandotti: `channel_length_km`, `elevation_mean_m`, "
                        "`elevation_min_m`."
                    ),
                    "faa": (
                        "FAA overland flow: `overland_length_km`, "
                        "`overland_slope_m_per_m`, `runoff_coeff`."
                    ),
                    "kerby": (
                        "Kerby overland flow: `overland_length_km`, "
                        "`overland_slope_m_per_m`, `retardance`."
                    ),
                    "kerby_kirpich": (
                        "Kerby overland plus Kirpich channel: the Kerby fields and "
                        "`flow_path_length_km`, `flow_path_slope_m_per_m`."
                    ),
                },
                meanings_pl={
                    "kirpich": (
                        "Kirpich z najdłuższej drogi spływu: `flow_path_length_km`, "
                        "`flow_path_slope_m_per_m`."
                    ),
                    "nrcs": (
                        "Metoda opóźnienia NRCS (NEH 630): `flow_path_length_km`, "
                        "`mean_slope_m_per_m`, `cn`."
                    ),
                    "giandotti": (
                        "Giandotti: `channel_length_km`, `elevation_mean_m`, "
                        "`elevation_min_m`."
                    ),
                    "faa": (
                        "Spływ powierzchniowy FAA: `overland_length_km`, "
                        "`overland_slope_m_per_m`, `runoff_coeff`."
                    ),
                    "kerby": (
                        "Spływ powierzchniowy Kerby'ego: `overland_length_km`, "
                        "`overland_slope_m_per_m`, `retardance`."
                    ),
                    "kerby_kirpich": (
                        "Spływ Kerby'ego plus koryto Kirpicha: pola Kerby'ego oraz "
                        "`flow_path_length_km`, `flow_path_slope_m_per_m`."
                    ),
                },
            ),
        ),
        one_of=(("watershed",), ("watershed_file",)),
        examples=(
            {
                "watershed": {
                    "name": "Potok Młynówka",
                    "area_km2": 45.3,
                    "perimeter_km": 32.1,
                    "length_km": 12.5,
                    "elevation_min_m": 150.0,
                    "elevation_max_m": 520.0,
                    "mean_slope_m_per_m": 0.025,
                    "cn": 72,
                    "flow_path_length_km": 12.5,
                    "flow_path_slope_m_per_m": 0.025,
                },
                "method": "nrcs",
            },
        ),
        result_schema="hydrolog-tc-watershed/1",
        cardinality="single",
        rules=(
            "Pass `watershed` or `watershed_file`, not both.",
            "Fill the watershed fields the chosen method needs.",
            "Read `parameters` to see which values were used.",
        ),
        rules_pl=(
            "Podaj `watershed` albo `watershed_file`, nie oba.",
            "Wypełnij pola zlewni potrzebne wybranej metodzie.",
            "Odczytaj `parameters`, aby zobaczyć użyte wartości.",
        ),
        errors=("validation_error", "not_found", "data_error", "forbidden"),
        core=True,
        typical_ranges=WATERSHED_TC_RANGES,
        example_results=(
            {
                "method": "nrcs",
                "tc_min": 495.966,
                "tc_h": 8.2661,
                "watershed_name": "Potok Młynówka",
                "parameters": {"length_km": 12.5, "slope_m_per_m": 0.025, "cn": 72.0},
            },
        ),
    ),
)
