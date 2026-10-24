"""Group ``tc``: time of concentration.

One command per empirical formula of :class:`~hydrolog.time.ConcentrationTime`
(``tc kirpich``, ``tc nrcs``, ``tc giandotti``, ``tc faa``, ``tc kerby``,
``tc kerby-kirpich``) and ``tc watershed``, which applies one of the methods to a
:class:`~hydrolog.morphometry.WatershedParameters` file. All results are given in
minutes and hours.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_METHODS = ("kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich")

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
        "Liczba krzywej CN dla AMC II, 1–100 (zalecany zakres metody: 50–95); "
        "może być ułamkowa (np. średnia ważona z `cn weighted`)."
    ),
    description=(
        "Curve Number CN for AMC II, 1-100 (recommended range of the method: "
        "50-95); may be fractional (e.g. a weighted mean from `cn weighted`)."
    ),
    required=True,
    minimum=1,
    maximum=100,
)

_RETARDANCE = Option(
    name="retardance",
    type="number",
    description_pl=(
        "Współczynnik retardacji (szorstkości) Kerby'ego N, > 0; zwykle "
        f"0,02–0,80. {_KERBY_TABLE_PL}"
    ),
    description=(
        "Kerby retardance (roughness) coefficient N, > 0; usually 0.02-0.80. "
        f"{_KERBY_TABLE_EN}"
    ),
    required=True,
    exclusive_minimum=0,
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="tc kirpich",
        operation_id="hydrolog_tc_kirpich",
        summary_pl="Oblicz czas koncentracji wzorem Kirpicha (długość i spadek cieku).",
        summary="Compute time of concentration with the Kirpich formula.",
        description_pl=(
            "Czas koncentracji tc [min, h] wzorem Kirpicha z długości cieku głównego "
            "[km] i spadku [m/m]. Użyj dla małych zlewni rolniczych (0,004–0,45 "
            "km²); dla spływu powierzchniowego z korytem użyj `tc kerby-kirpich`. "
            "Ostrzega poza L ≤ 80 km i S 0,002–0,15."
        ),
        description=(
            "Kirpich tc [min, h] from main channel length [km] and slope [m/m]. "
            "Use for small agricultural watersheds (0.004-0.45 km2); for overland "
            "plus channel flow use `tc kerby-kirpich`. Warns outside L <= 80 km "
            "and S 0.002-0.15."
        ),
        function="hydrolog.operations.tc_kirpich",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość cieku głównego od działu wodnego do przekroju "
                    "zamykającego [km]; > 0 (typowo ≤ 80)."
                ),
                description=(
                    "Main channel length from the watershed divide to the outlet "
                    "[km]; > 0 (typically <= 80)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek cieku głównego [m/m] (nie w procentach); > 0 "
                    "(typowo 0,002–0,15)."
                ),
                description=(
                    "Mean slope of the main channel [m/m] (not percent); > 0 "
                    "(typically 0.002-0.15)."
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
        summary_pl="Oblicz czas koncentracji metodą NRCS (TR-55) z L, spadku i CN.",
        summary="Compute time of concentration with the NRCS (TR-55 lag) method.",
        description_pl=(
            "Czas koncentracji tc [min, h] metodą NRCS (TR-55, czas opóźnienia / "
            "0,6) z długości drogi hydraulicznej [km], spadku zlewni [m/m] i CN. "
            "Użyj, gdy CN jest znane (`cn lookup`, `cn weighted`). Zwraca tc, nie "
            "tlag (tlag = 0,6·tc). Ostrzega poza L 0,03–30 km i S 0,001–0,15."
        ),
        description=(
            "NRCS (TR-55) tc [min, h] from hydraulic length [km], watershed slope "
            "[m/m] and CN. Use when CN is known (`cn lookup`, `cn weighted`). "
            "Returns tc, not lag (lag = 0.6 * tc). Warns outside L 0.03-30 km and "
            "S 0.001-0.15."
        ),
        function="hydrolog.operations.tc_nrcs",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość drogi hydraulicznej zlewni (najdłuższej ścieżki "
                    "spływu) [km]; > 0 (typowo 0,03–30)."
                ),
                description=(
                    "Hydraulic length of the watershed (longest flow path) [km]; "
                    "> 0 (typically 0.03-30)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek zlewni [m/m] (nie w procentach); > 0 (typowo "
                    "0,001–0,15)."
                ),
                description=(
                    "Mean watershed slope [m/m] (not percent); > 0 (typically "
                    "0.001-0.15)."
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
            "długości cieku [km] i różnicy wysokości [m]. Użyj dla większych "
            "zlewni górskich (> 170 km²); dla małych zlewni użyj `tc kirpich`. "
            "Ostrzega poza A 100–10 000 km², L 1–300 km, H 20–3000 m."
        ),
        description=(
            "Giandotti tc [min, h] from area [km2], channel length [km] and "
            "elevation difference [m]. Use for larger mountain watersheds (> 170 "
            "km2); for small watersheds use `tc kirpich`. Warns outside A 100-10,000 "
            "km2, L 1-300 km, H 20-3000 m."
        ),
        function="hydrolog.operations.tc_giandotti",
        options=(
            Option(
                name="area_km2",
                type="number",
                description_pl="Powierzchnia zlewni [km²]; > 0 (typowo 100–10 000).",
                description="Watershed area [km2]; > 0 (typically 100-10,000).",
                required=True,
                exclusive_minimum=0,
                unit="km2",
            ),
            Option(
                name="length_km",
                type="number",
                description_pl="Długość cieku głównego [km]; > 0 (typowo 1–300).",
                description="Main channel length [km]; > 0 (typically 1-300).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="elevation_diff_m",
                type="number",
                description_pl=(
                    "Różnica wysokości między średnią wysokością zlewni a "
                    "przekrojem zamykającym [m]; > 0 (typowo 20–3000)."
                ),
                description=(
                    "Difference between the mean watershed elevation and the "
                    "outlet [m]; > 0 (typically 20-3000)."
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
            "płaskich dróg spływu (L 0,015–3 km); dla zlewni z korytem użyj `tc "
            "kerby-kirpich` lub `tc kirpich`."
        ),
        description=(
            "FAA overland flow tc [min, h] from flow length [km], slope [m/m] and "
            "runoff coefficient C. Use for short, flat flow paths (L 0.015-3 km); "
            "for a watershed with a channel use `tc kerby-kirpich` or `tc "
            "kirpich`."
        ),
        function="hydrolog.operations.tc_faa",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego [km]; > 0 (typowo 0,015–3)."
                ),
                description="Overland flow length [km]; > 0 (typically 0.015-3).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek terenu [m/m] (nie w procentach); > 0 (typowo "
                    "0,005–0,10)."
                ),
                description=(
                    "Mean ground slope [m/m] (not percent); > 0 (typically 0.005-0.10)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="runoff_coeff",
                type="number",
                description_pl=(
                    "Współczynnik odpływu C metody wymiernej, 0 < C ≤ 1 (typowo "
                    "0,10–0,95)."
                ),
                description=(
                    "Rational-method runoff coefficient C, 0 < C <= 1 (typically "
                    "0.10-0.95)."
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
            "spływu (L ≤ 0,366 km); dla zlewni z korytem użyj `tc kerby-kirpich` "
            "lub `tc kirpich`. Dla S < 0,002 stosuje poprawkę spadku."
        ),
        description=(
            "Kerby overland flow tc [min, h] from flow length [km], slope [m/m] and "
            "retardance N. Use for short flow paths (L <= 0.366 km); for a "
            "watershed with a channel use `tc kerby-kirpich` or `tc kirpich`. "
            "Applies a low-slope adjustment for S < 0.002."
        ),
        function="hydrolog.operations.tc_kerby",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego [km]; > 0 (typowo ≤ 0,366)."
                ),
                description="Overland flow length [km]; > 0 (typically <= 0.366).",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek terenu [m/m] (nie w procentach); > 0 (typowo "
                    "0,001–0,01)."
                ),
                description=(
                    "Mean ground slope [m/m] (not percent); > 0 (typically 0.001-0.01)."
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
            "Czas koncentracji tc [min, h] złożoną metodą Kerby–Kirpich: spływ "
            "powierzchniowy (Kerby) plus koryto (Kirpich). Użyj, gdy droga spływu "
            "ma oba odcinki; dla samego koryta użyj `tc kirpich`, dla samego "
            "spływu `tc kerby`. Ostrzega, gdy odcinek wykracza poza zakres wzoru."
        ),
        description=(
            "Kerby-Kirpich tc [min, h]: overland segment (Kerby) plus channel "
            "segment (Kirpich). Use when the flow path has both; for the channel "
            "only use `tc kirpich`, for overland flow only `tc kerby`. Warns when "
            "a segment is outside its formula range."
        ),
        function="hydrolog.operations.tc_kerby_kirpich",
        options=(
            Option(
                name="overland_length_km",
                type="number",
                description_pl=(
                    "Długość spływu powierzchniowego od najdalszego punktu do "
                    "początku wyraźnego cieku [km]; > 0 (typowo ≤ 0,366)."
                ),
                description=(
                    "Overland flow length from the most distant point to the start "
                    "of a defined channel [km]; > 0 (typically <= 0.366)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="overland_slope_m_per_m",
                type="number",
                description_pl=(
                    "Średni spadek spływu powierzchniowego [m/m]; > 0 (typowo "
                    "0,001–0,01)."
                ),
                description=("Mean overland slope [m/m]; > 0 (typically 0.001-0.01)."),
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            _RETARDANCE,
            Option(
                name="channel_length_km",
                type="number",
                description_pl=(
                    "Długość cieku od początku wyraźnego koryta do przekroju "
                    "zamykającego [km]; > 0 (typowo ≤ 80)."
                ),
                description=(
                    "Channel length from the start of the defined channel to the "
                    "outlet [km]; > 0 (typically <= 80)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="channel_slope_m_per_m",
                type="number",
                description_pl=("Średni spadek koryta [m/m]; > 0 (typowo 0,002–0,15)."),
                description="Mean channel slope [m/m]; > 0 (typically 0.002-0.15).",
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
                "channel_length_km": 5.0,
                "channel_slope_m_per_m": 0.005,
            },
        ),
        result_schema="hydrolog-tc-kerby-kirpich/1",
        cardinality="single",
        rules=(
            "Give slopes in m/m and lengths in km.",
            "Do not count the overland length twice in the channel length.",
            "Check `notices` for segments outside the formula range.",
        ),
        rules_pl=(
            "Podaj spadki w m/m, a długości w km.",
            "Nie wliczaj długości spływu powierzchniowego do długości koryta.",
            "Sprawdź `notices` pod kątem odcinków poza zakresem wzoru.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "method": "kerby_kirpich",
                "tc_min": 144.02,
                "tc_h": 2.40034,
                "parameters": {
                    "overland_length_km": 0.25,
                    "overland_slope_m_per_m": 0.008,
                    "retardance": 0.4,
                    "channel_length_km": 5.0,
                    "channel_slope_m_per_m": 0.005,
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
                    "Parametry zlewni jako obiekt WatershedParameters (m.in. "
                    "`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, "
                    "`elevation_max_m`, opcjonalnie `cn`, `mean_slope_m_per_m`, "
                    "`channel_length_km`, `channel_slope_m_per_m`, `runoff_coeff`, "
                    "`retardance`, `overland_length_km`, "
                    "`overland_slope_m_per_m`...)."
                ),
                description=(
                    "Watershed parameters as a WatershedParameters object "
                    "(`area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, "
                    "`elevation_max_m`, optionally `cn`, `mean_slope_m_per_m`, "
                    "`channel_length_km`, `channel_slope_m_per_m`, `runoff_coeff`, "
                    "`retardance`, `overland_length_km`, "
                    "`overland_slope_m_per_m`...)."
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
                    "Metoda obliczenia tc; domyślnie kirpich. Pola zlewni "
                    "wymagane przez metodę podaje komenda `tc <metoda>`."
                ),
                description=(
                    "Method of computing tc; default kirpich. The watershed "
                    "fields a method needs follow the matching `tc <method>` "
                    "command."
                ),
                choices=_METHODS,
                default="kirpich",
                meanings={
                    "kirpich": "Kirpich formula from channel length and slope.",
                    "nrcs": "NRCS (TR-55) lag method; needs `cn`.",
                    "giandotti": "Giandotti formula from area, length and relief.",
                    "faa": "FAA overland flow formula; needs `runoff_coeff`.",
                    "kerby": "Kerby overland flow formula; needs `retardance`.",
                    "kerby_kirpich": "Composite Kerby overland plus Kirpich channel.",
                },
                meanings_pl={
                    "kirpich": "Wzór Kirpicha z długości i spadku cieku.",
                    "nrcs": "Metoda NRCS (TR-55, czas opóźnienia); wymaga `cn`.",
                    "giandotti": "Wzór Giandottiego z powierzchni, długości i relief.",
                    "faa": "Wzór FAA spływu powierzchniowego; wymaga `runoff_coeff`.",
                    "kerby": "Wzór Kerby'ego spływu powierzchniowego; wymaga "
                    "`retardance`.",
                    "kerby_kirpich": "Złożona: spływ Kerby'ego plus koryto Kirpicha.",
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
