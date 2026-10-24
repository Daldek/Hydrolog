"""Group ``cn``: Curve Number tables (TR-55) and area-weighted CN.

``cn lookup`` reads one CN from the USDA-NRCS TR-55 tables, ``cn list`` returns the
whole table, ``cn range`` the CN range of one land cover, and ``cn weighted``
averages the CN of the parts of a watershed.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

# Values of ``hydrolog.runoff.LandCover`` (kept literal so that importing the catalog
# does not import SciPy; a test checks them against the enum).
_LAND_COVERS = (
    "fallow",
    "row_crops",
    "small_grain",
    "pasture",
    "meadow",
    "brush",
    "forest",
    "herbaceous",
    "farmstead",
    "residential_low",
    "residential_medium",
    "residential_high",
    "commercial",
    "industrial",
    "open_space",
    "paved",
    "gravel",
    "dirt",
    "water",
)
_CONDITIONS = ("poor", "fair", "good")
_HSG = ("A", "B", "C", "D")

_LAND_COVER_MEANINGS = {
    "fallow": "Bare soil kept without crop.",
    "row_crops": "Row crops.",
    "small_grain": "Small grain.",
    "pasture": "Pasture and grassland.",
    "meadow": "Meadow, cut for hay.",
    "brush": "Brush and shrubs.",
    "forest": "Woods.",
    "herbaceous": "Herbaceous vegetation.",
    "farmstead": "Farmsteads.",
    "residential_low": "Low-density residential (1-2 acre lots, 12-20% impervious).",
    "residential_medium": "Medium-density residential (1/4-1/2 acre lots, 25-38%).",
    "residential_high": "High-density residential (<= 1/8 acre lots, 65%).",
    "commercial": "Commercial and business areas (85% impervious).",
    "industrial": "Industrial areas (72% impervious).",
    "open_space": "Parks, lawns, golf courses.",
    "paved": "Paved surfaces.",
    "gravel": "Gravel roads.",
    "dirt": "Dirt roads.",
    "water": "Water bodies (CN = 100).",
}
_LAND_COVER_MEANINGS_PL = {
    "fallow": "Ugór (gleba odkryta bez uprawy).",
    "row_crops": "Uprawy rzędowe.",
    "small_grain": "Zboża drobnoziarniste.",
    "pasture": "Pastwisko, użytek zielony.",
    "meadow": "Łąka kośna.",
    "brush": "Zarośla, krzewy.",
    "forest": "Las.",
    "herbaceous": "Roślinność zielna.",
    "farmstead": "Zabudowa zagrodowa.",
    "residential_low": "Zabudowa mieszkaniowa luźna (działki 1–2 akry, 12–20%).",
    "residential_medium": "Zabudowa średnia (działki 1/4–1/2 akra, 25–38%).",
    "residential_high": "Zabudowa mieszkaniowa gęsta (działki ≤ 1/8 akra, 65%).",
    "commercial": "Tereny handlowo-usługowe (85% uszczelnienia).",
    "industrial": "Tereny przemysłowe (72% uszczelnienia).",
    "open_space": "Parki, trawniki, pola golfowe.",
    "paved": "Nawierzchnie utwardzone.",
    "gravel": "Drogi żwirowe.",
    "dirt": "Drogi gruntowe.",
    "water": "Wody (CN = 100).",
}

_CONDITION_MEANINGS = {
    "poor": "Sparse vegetation, heavy grazing.",
    "fair": "Moderate vegetation cover.",
    "good": "Dense vegetation.",
}
_CONDITION_MEANINGS_PL = {
    "poor": "Rzadka roślinność, intensywny wypas.",
    "fair": "Średnie pokrycie roślinnością.",
    "good": "Zwarta roślinność.",
}

_LAND_COVER = Option(
    name="land_cover",
    type="choice",
    description_pl="Klasa pokrycia terenu wg TR-55.",
    description="TR-55 land cover class.",
    required=True,
    choices=_LAND_COVERS,
    meanings=_LAND_COVER_MEANINGS,
    meanings_pl=_LAND_COVER_MEANINGS_PL,
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="cn lookup",
        operation_id="hydrolog_cn_lookup",
        summary_pl="Odczytaj CN z tablic TR-55 dla grupy gleby i pokrycia terenu.",
        summary="Look up the TR-55 Curve Number for a soil group and a land cover.",
        description_pl=(
            "Liczba CN (AMC II) z tablic USDA-NRCS TR-55 dla grupy gleby HSG i "
            "pokrycia terenu; `condition` dotyczy tylko pokryć zależnych od stanu "
            "(domyślnie fair), a wynik podaje `condition_applied`. Użyj dla "
            "jednego pokrycia; dla zlewni z wielu pokryć użyj `cn weighted`, "
            "korektę AMC robi `scs effective`."
        ),
        description=(
            "Curve Number (AMC II) from the USDA-NRCS TR-55 tables for a soil "
            "group HSG and a land cover; `condition` matters only for "
            "condition-dependent covers (fair by default), and the result reports "
            "`condition_applied`. Use for one cover; for several covers use `cn "
            "weighted`, for AMC adjustment `scs effective`."
        ),
        function="hydrolog.operations.cn_lookup",
        options=(
            Option(
                name="hsg",
                type="choice",
                description_pl=(
                    "Hydrologiczna grupa gleby (HSG) wg USDA; HSG z danych "
                    "glebowych liczą komendy grupy `soil`."
                ),
                description=(
                    "USDA hydrologic soil group (HSG); the `soil` commands derive "
                    "HSG from soil data."
                ),
                required=True,
                choices=_HSG,
                meanings={
                    "A": "Low runoff potential (sands).",
                    "B": "Moderately low runoff potential (sandy loams).",
                    "C": "Moderately high runoff potential (clay loams).",
                    "D": "High runoff potential (clays).",
                },
                meanings_pl={
                    "A": "Mały potencjał odpływu (piaski).",
                    "B": "Umiarkowanie mały potencjał odpływu (gliny piaszczyste).",
                    "C": "Umiarkowanie duży potencjał odpływu (gliny ilaste).",
                    "D": "Duży potencjał odpływu (iły).",
                },
            ),
            _LAND_COVER,
            Option(
                name="condition",
                type="choice",
                description_pl=(
                    "Stan hydrologiczny pokrycia; dotyczy pokryć zależnych od "
                    "stanu (row_crops, small_grain, pasture, brush, forest, "
                    "herbaceous, open_space), domyślnie fair; dla pozostałych "
                    "jest ignorowany."
                ),
                description=(
                    "Hydrologic condition of the cover; applies to "
                    "condition-dependent covers (row_crops, small_grain, pasture, "
                    "brush, forest, herbaceous, open_space), fair when omitted; "
                    "ignored for the other covers."
                ),
                choices=_CONDITIONS,
                meanings=_CONDITION_MEANINGS,
                meanings_pl=_CONDITION_MEANINGS_PL,
            ),
        ),
        examples=(
            {"hsg": "B", "land_cover": "forest", "condition": "good"},
            {"hsg": "C", "land_cover": "paved"},
        ),
        result_schema="hydrolog-cn-lookup/1",
        cardinality="single",
        rules=(
            "Check `condition_applied` and `notices` to see which condition was used.",
            "The CN is for AMC II; adjust it with `scs effective`.",
        ),
        rules_pl=(
            "Sprawdź `condition_applied` i `notices`, aby poznać użyty stan.",
            "CN dotyczy AMC II; korektę wykonaj w `scs effective`.",
        ),
        errors=("validation_error",),
        core=True,
        example_results=(
            {
                "cn": 55,
                "hsg": "B",
                "land_cover": "forest",
                "condition": "good",
                "condition_applied": "good",
            },
            {"cn": 98, "hsg": "C", "land_cover": "paved", "condition_applied": None},
        ),
    ),
    Command(
        name="cn list",
        operation_id="hydrolog_cn_list",
        summary_pl="Zwróć pełną tablicę CN TR-55 (pokrycia, stany, grupy A–D).",
        summary="Return the whole TR-55 CN table (covers, conditions, groups A-D).",
        description_pl=(
            "Cała tablica CN (AMC II) z USDA-NRCS TR-55: wiersze `land_cover` i "
            "`condition` z CN dla grup A–D. Użyj, aby poznać dopuszczalne "
            "wartości `land_cover` i `condition`; konkretny CN daje `cn lookup`, "
            "zakres jednego pokrycia `cn range`. Bez opcji."
        ),
        description=(
            "The whole CN table (AMC II) of USDA-NRCS TR-55: rows `land_cover` and "
            "`condition` with the CN of groups A-D. Use it to learn the allowed "
            "`land_cover` and `condition` values; for one CN use `cn lookup`, for "
            "the range of one cover `cn range`. No options."
        ),
        function="hydrolog.operations.cn_list",
        options=(),
        examples=({},),
        result_schema="hydrolog-cn-list/1",
        cardinality="bounded",
        rules=(
            "Call without options.",
            "A null `condition` marks a single-value cover.",
        ),
        rules_pl=(
            "Wywołaj bez opcji.",
            "`condition` równe null oznacza pokrycie o jednej wartości.",
        ),
        errors=("validation_error",),
        example_results=({"hsg": ["A", "B", "C", "D"]},),
    ),
    Command(
        name="cn range",
        operation_id="hydrolog_cn_range",
        summary_pl="Zwróć zakres CN pokrycia terenu po stanach hydrologicznych.",
        summary="Return the CN range of a land cover over hydrologic conditions.",
        description_pl=(
            "Zakres CN (min–max po stanach poor/fair/good, AMC II, TR-55) wybranego "
            "pokrycia w każdej grupie gleby A–D. Użyj do oceny wrażliwości CN na "
            "stan pokrycia; konkretną wartość daje `cn lookup`. Pokrycia o jednej "
            "wartości mają min = max."
        ),
        description=(
            "CN range (min-max over poor/fair/good, AMC II, TR-55) of one land "
            "cover in each soil group A-D. Use it to judge how sensitive CN is to "
            "the cover condition; a concrete value comes from `cn lookup`. "
            "Single-value covers have min = max."
        ),
        function="hydrolog.operations.cn_range",
        options=(_LAND_COVER,),
        examples=({"land_cover": "forest"},),
        result_schema="hydrolog-cn-range/1",
        cardinality="single",
        rules=(
            "Read `by_hsg` for minimum and maximum per soil group.",
            "Use `cn lookup` for a single CN.",
        ),
        rules_pl=(
            "Odczytaj `by_hsg`, aby poznać minimum i maksimum dla grupy gleby.",
            "Pojedyncze CN uzyskasz z `cn lookup`.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "land_cover": "forest",
                "conditions": ["poor", "fair", "good"],
                "by_hsg": {
                    "A": {"minimum": 30, "maximum": 45},
                    "B": {"minimum": 55, "maximum": 66},
                    "C": {"minimum": 70, "maximum": 77},
                    "D": {"minimum": 77, "maximum": 83},
                },
            },
        ),
    ),
    Command(
        name="cn weighted",
        operation_id="hydrolog_cn_weighted",
        summary_pl="Oblicz średnią ważoną CN zlewni złożonej z kilku pokryć lub gleb.",
        summary="Compute the area-weighted CN of a watershed made of several parts.",
        description_pl=(
            "Średnia ważona CN zlewni z części o znanym CN i powierzchni lub "
            "udziale: `parts`, albo równoległe `cn_values` z `areas` lub "
            "`fractions` (suma udziałów = 1). Użyj po `cn lookup` dla każdej "
            "części; wynik jest ułamkowy i nadaje się do `scs effective`."
        ),
        description=(
            "Area-weighted CN of a watershed from parts with a known CN and area "
            "or share: `parts`, or parallel `cn_values` with `areas` or "
            "`fractions` (shares sum to 1). Use after `cn lookup` for each part; "
            "the result is fractional and fits `scs effective`."
        ),
        function="hydrolog.operations.cn_weighted",
        options=(
            Option(
                name="parts",
                type="object_list",
                description_pl=(
                    'Części zlewni jako obiekty `{"cn": liczba 1–100, "area": '
                    'powierzchnia ≥ 0}` albo `{"cn": ..., "fraction": udział '
                    "0–1}`; w jednej liście wszystkie części mają ten sam rodzaj "
                    "wagi (`area` albo `fraction`)."
                ),
                description=(
                    'Watershed parts as objects `{"cn": number 1-100, "area": '
                    'area >= 0}` or `{"cn": ..., "fraction": share 0-1}`; all '
                    "parts of one list use the same kind of weight (`area` or "
                    "`fraction`)."
                ),
            ),
            Option(
                name="cn_values",
                type="number_list",
                description_pl=(
                    "Wartości CN części zlewni (1–100); równolegle do `areas` "
                    "albo `fractions`."
                ),
                description=(
                    "CN values of the watershed parts (1-100); parallel to "
                    "`areas` or `fractions`."
                ),
                minimum=1,
                maximum=100,
            ),
            Option(
                name="areas",
                type="number_list",
                description_pl=(
                    "Powierzchnie części (≥ 0, jednolita jednostka dowolna); "
                    "tyle elementów, ile `cn_values`."
                ),
                description=(
                    "Areas of the parts (>= 0, any consistent unit); as many "
                    "items as `cn_values`."
                ),
                minimum=0,
            ),
            Option(
                name="fractions",
                type="number_list",
                description_pl=(
                    "Udziały części w zlewni (0–1), sumujące się do 1; tyle "
                    "elementów, ile `cn_values`."
                ),
                description=(
                    "Shares of the parts in the watershed (0-1) summing to 1; as "
                    "many items as `cn_values`."
                ),
                minimum=0,
                maximum=1,
            ),
        ),
        one_of=(("parts",), ("cn_values", "areas"), ("cn_values", "fractions")),
        examples=(
            {
                "parts": [
                    {"cn": 55, "area": 27.2},
                    {"cn": 69, "area": 13.6},
                    {"cn": 65, "area": 4.5},
                ]
            },
            {"cn_values": [55, 79, 98], "fractions": [0.6, 0.3, 0.1]},
            {"cn_values": [58, 71, 78], "areas": [12.4, 25.1, 7.8]},
        ),
        result_schema="hydrolog-cn-weighted/1",
        cardinality="single",
        rules=(
            "Use one weight kind per call; fractions must sum to 1.",
            "Use one area unit for all parts.",
            "Pass the fractional CN on without rounding.",
        ),
        rules_pl=(
            "Użyj jednego rodzaju wag; udziały muszą sumować się do 1.",
            "Użyj jednej jednostki powierzchni dla wszystkich części.",
            "Przekaż dalej ułamkowe CN bez zaokrąglania.",
        ),
        errors=("validation_error",),
        core=True,
        example_results=(
            {
                "cn": 60.1965,
                "n_parts": 3,
                "total_area": 45.3,
                "shares": [0.600442, 0.300221, 0.0993377],
            },
            {"cn": 66.5, "n_parts": 3, "total_area": None, "shares": [0.6, 0.3, 0.1]},
            {
                "cn": 68.6468,
                "n_parts": 3,
                "total_area": 45.3,
                "shares": [0.273731, 0.554084, 0.172185],
            },
        ),
    ),
)
