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

_LAND_COVER_PL = (
    "Klasa pokrycia terenu wg TR-55: fallow — ugór (gleba odkryta); row_crops — "
    "uprawy rzędowe; small_grain — zboża drobnoziarniste; pasture — pastwisko, "
    "użytek zielony; meadow — łąka kośna; brush — zarośla, krzewy; forest — las; "
    "herbaceous — roślinność zielna (zbiorowiska trawiasto-zielne); farmstead — "
    "zabudowa zagrodowa; residential_low — zabudowa mieszkaniowa luźna (działki "
    "1–2 akry, 12–20% uszczelnienia); residential_medium — zabudowa średnia "
    "(działki 1/4–1/2 akra, 25–38%); residential_high — zabudowa gęsta (działki "
    "≤ 1/8 akra, 65%); commercial — tereny handlowo-usługowe (85%); industrial "
    "— tereny przemysłowe (72%); open_space — tereny zielone (parki, trawniki, "
    "pola golfowe); paved — nawierzchnie utwardzone; gravel — nawierzchnie "
    "żwirowe; dirt — drogi gruntowe; water — wody (CN = 100)."
)
_LAND_COVER_EN = (
    "TR-55 land cover class: fallow - bare soil; row_crops - row crops; "
    "small_grain - small grain; pasture - pasture, grassland; meadow - meadow; "
    "brush - brush; forest - woods; herbaceous - herbaceous vegetation; "
    "farmstead - farmsteads; residential_low - low-density residential (1-2 acre "
    "lots, 12-20% impervious); residential_medium - medium density (1/4-1/2 acre "
    "lots, 25-38%); residential_high - high density (<= 1/8 acre lots, 65%); "
    "commercial - commercial and business (85%); industrial (72%); open_space - "
    "parks, lawns, golf courses; paved - paved surfaces; gravel - gravel roads; "
    "dirt - dirt roads; water - water bodies (CN = 100)."
)

_CONDITION_PL = (
    "Stan hydrologiczny pokrycia: poor (słaby: rzadka roślinność, intensywny "
    "wypas), fair (średni), good (dobry: zwarta roślinność). Dotyczy pokryć "
    "zależnych od stanu (row_crops, small_grain, pasture, brush, forest, "
    "herbaceous, open_space); gdy go pominięto, przyjmowany jest fair; dla "
    "pozostałych pokryć jest ignorowany."
)
_CONDITION_EN = (
    "Hydrologic condition of the cover: poor (sparse vegetation, heavy "
    "grazing), fair (moderate), good (dense vegetation). It applies to "
    "condition-dependent covers (row_crops, small_grain, pasture, brush, forest, "
    "herbaceous, open_space); fair is assumed when omitted; for the other covers "
    "it is ignored."
)

_LAND_COVER = Option(
    name="land_cover",
    type="choice",
    description=_LAND_COVER_PL,
    description_en=_LAND_COVER_EN,
    required=True,
    choices=_LAND_COVERS,
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="cn lookup",
        operation_id="cn_lookup",
        summary="Liczba CN z tablic TR-55 dla grupy hydrologicznej gleby i pokrycia terenu.",
        summary_en="Curve Number from the TR-55 tables for a soil group and a land cover.",
        description=(
            "Odczytuje liczbę krzywej CN (AMC II) z tablic USDA-NRCS TR-55 (National "
            "Engineering Handbook, Part 630, rozdz. 9) dla hydrologicznej grupy "
            "gleby HSG (A–D) i klasy pokrycia terenu. Dla pokryć zależnych od stanu "
            "hydrologicznego podaje się `condition` (poor/fair/good); bez niego "
            "przyjmowane jest fair, a dla pokryć o jednej wartości (paved, water, "
            "residential_*...) `condition` jest ignorowane — wynik mówi, jaki stan "
            "faktycznie zastosowano (`condition_applied`) i zgłasza to w "
            "informacji. CN odnosi się do warunków wilgotności AMC II i "
            "standardowego stosunku strat początkowych 0,2 (korekta AMC: `scs "
            "effective`); średnią ważoną z kilku pokryć daje `cn weighted`. Wynik: "
            "cn, hsg, land_cover, condition, condition_applied. Źródło: USDA-NRCS "
            "(1986), Urban Hydrology for Small Watersheds, TR-55."
        ),
        description_en=(
            "Reads the Curve Number (AMC II) from the USDA-NRCS TR-55 tables "
            "(National Engineering Handbook, Part 630, chapter 9) for a hydrologic "
            "soil group HSG (A-D) and a land cover class. Condition-dependent "
            "covers take a `condition` (poor/fair/good); fair is assumed without "
            "it, and for single-value covers (paved, water, residential_*...) "
            "`condition` is ignored - the result states which condition was "
            "actually applied (`condition_applied`) and reports it as a notice. "
            "The CN refers to AMC II and the standard initial abstraction ratio "
            "0.2 (AMC adjustment: `scs effective`); `cn weighted` averages the CN "
            "of several covers. Result: cn, hsg, land_cover, condition, "
            "condition_applied. Source: USDA-NRCS (1986), Urban Hydrology for "
            "Small Watersheds, TR-55."
        ),
        function="hydrolog.operations:cn_lookup",
        options=(
            Option(
                name="hsg",
                type="choice",
                description=(
                    "Hydrologiczna grupa gleby (HSG) wg USDA: A — mały potencjał "
                    "odpływu (piaski), B — umiarkowanie mały (gliny piaszczyste), "
                    "C — umiarkowanie duży (gliny ilaste), D — duży (iły). HSG z "
                    "danych glebowych liczą komendy grupy `soil`."
                ),
                description_en=(
                    "USDA hydrologic soil group (HSG): A - low runoff potential "
                    "(sands), B - moderately low (sandy loams), C - moderately "
                    "high (clay loams), D - high (clays). The `soil` commands "
                    "derive HSG from soil data."
                ),
                required=True,
                choices=_HSG,
            ),
            _LAND_COVER,
            Option(
                name="condition",
                type="choice",
                description=_CONDITION_PL,
                description_en=_CONDITION_EN,
                choices=_CONDITIONS,
            ),
        ),
        examples=(
            {"hsg": "B", "land_cover": "forest", "condition": "good"},
            {"hsg": "C", "land_cover": "paved"},
        ),
    ),
    Command(
        name="cn list",
        operation_id="cn_list",
        summary="Pełna tablica CN TR-55: pokrycia terenu, stany hydrologiczne i CN dla grup A–D.",
        summary_en="The whole TR-55 CN table: land covers, hydrologic conditions, CN for groups A-D.",
        description=(
            "Zwraca całą tablicę CN (AMC II) z USDA-NRCS TR-55 używaną przez "
            "`cn lookup`: dla każdego pokrycia terenu (`land_cover`) jeden wiersz "
            "na stan hydrologiczny (`condition` = poor/fair/good) albo jeden "
            "wiersz z `condition` = null dla pokryć o jednej wartości, każdy z CN "
            "dla grup gleby A, B, C i D. Służy do poznania dopuszczalnych wartości "
            "`land_cover` i `condition` oraz do przeglądu całej tablicy w jednym "
            "wywołaniu. Komenda nie ma opcji."
        ),
        description_en=(
            "Returns the whole CN table (AMC II) of USDA-NRCS TR-55 used by `cn "
            "lookup`: for each land cover (`land_cover`) one row per hydrologic "
            "condition (`condition` = poor/fair/good) or a single row with "
            "`condition` = null for single-value covers, each with the CN of soil "
            "groups A, B, C and D. Use it to learn the allowed `land_cover` and "
            "`condition` values or to review the table in one call. The command "
            "has no options."
        ),
        function="hydrolog.operations:cn_list",
        options=(),
        examples=({},),
    ),
    Command(
        name="cn range",
        operation_id="cn_range",
        summary="Zakres CN (min–max po stanach hydrologicznych) pokrycia terenu dla grup A–D.",
        summary_en="CN range (min-max over hydrologic conditions) of a land cover for groups A-D.",
        description=(
            "Dla wybranego pokrycia terenu zwraca przedział CN (AMC II, TR-55) "
            "w każdej hydrologicznej grupie gleby A–D: minimum i maksimum po "
            "stanach hydrologicznych pokrycia (poor/fair/good). Dla pokryć o "
            "jednej wartości minimum = maksimum. Wynik zawiera też listę stanów, "
            "które przedział obejmuje. Służy do oceny wrażliwości CN na stan "
            "pokrycia; konkretną wartość daje `cn lookup`."
        ),
        description_en=(
            "For the chosen land cover returns the CN interval (AMC II, TR-55) in "
            "each hydrologic soil group A-D: the minimum and maximum over the "
            "hydrologic conditions of the cover (poor/fair/good). For single-value "
            "covers minimum = maximum. The result also lists the conditions the "
            "interval spans. Use it to judge how sensitive the CN is to the "
            "condition of the cover; `cn lookup` gives a concrete value."
        ),
        function="hydrolog.operations:cn_range",
        options=(_LAND_COVER,),
        examples=({"land_cover": "forest"},),
    ),
    Command(
        name="cn weighted",
        operation_id="cn_weighted",
        summary="Średnia ważona powierzchnią liczba CN zlewni złożonej z kilku pokryć/gleb.",
        summary_en="Area-weighted Curve Number of a watershed made of several covers/soils.",
        description=(
            "Liczy średnią ważoną liczbę CN zlewni: CN = Σ(CN_i · w_i) / Σ w_i, "
            "gdzie w_i to powierzchnia (lub udział) części o wartości CN_i, "
            "1 ≤ CN_i ≤ 100. Części podaje się jako (a) listę obiektów `parts`, "
            "każdy z kluczami `cn` oraz `area` (powierzchnia w dowolnej, "
            "jednolitej jednostce: km², ha, % — nieujemna) albo `fraction` "
            "(udział 0–1), (b) równoległe listy `cn_values` i `areas`, albo (c) "
            "równoległe listy `cn_values` i `fractions`. Udziały muszą dawać w "
            "sumie 1 (tolerancja 0,001), inaczej błąd walidacji; powierzchnie "
            "nie mogą się sumować do zera. Wynik: ważone CN (ułamkowe; "
            "`scs effective`, `tc nrcs` i `hydrograph generate` przyjmują "
            "ułamkowe CN), liczba części, suma powierzchni (null przy udziałach) "
            "i udział każdej części w sumie. Wartości CN poszczególnych części "
            "daje `cn lookup`; powierzchnie klas gleby — komendy grupy `soil`."
        ),
        description_en=(
            "Computes the area-weighted Curve Number of a watershed: CN = "
            "sum(CN_i · w_i) / sum(w_i), where w_i is the area (or share) of the "
            "part with CN_i, 1 <= CN_i <= 100. Give the parts as (a) a list of "
            "objects `parts`, each with the keys `cn` and either `area` (area in "
            "any consistent unit: km2, ha, % - non-negative) or `fraction` (share "
            "0-1), (b) parallel lists `cn_values` and `areas`, or (c) parallel "
            "lists `cn_values` and `fractions`. Fractions must sum to 1 "
            "(tolerance 0.001), otherwise a validation error is raised; areas "
            "must not sum to zero. Result: the weighted CN (fractional; `scs "
            "effective`, `tc nrcs` and `hydrograph generate` accept fractional "
            "CN), the number of parts, the total area (null for fractions) and the "
            "share of each part. Use `cn lookup` for the CN of single parts and "
            "the `soil` commands for soil class areas."
        ),
        function="hydrolog.operations:cn_weighted",
        options=(
            Option(
                name="parts",
                type="object_list",
                description=(
                    'Części zlewni jako obiekty `{"cn": liczba 1–100, "area": '
                    'powierzchnia ≥ 0}` albo `{"cn": ..., "fraction": udział '
                    "0–1}`; w jednej liście wszystkie części mają ten sam rodzaj "
                    "wagi (`area` albo `fraction`)."
                ),
                description_en=(
                    'Watershed parts as objects `{"cn": number 1-100, "area": '
                    'area >= 0}` or `{"cn": ..., "fraction": share 0-1}`; all '
                    "parts of one list use the same kind of weight (`area` or "
                    "`fraction`)."
                ),
            ),
            Option(
                name="cn_values",
                type="number_list",
                description=(
                    "Wartości CN części zlewni (1–100); równolegle do `areas` "
                    "albo `fractions`."
                ),
                description_en=(
                    "CN values of the watershed parts (1-100); parallel to "
                    "`areas` or `fractions`."
                ),
                minimum=1,
                maximum=100,
            ),
            Option(
                name="areas",
                type="number_list",
                description=(
                    "Powierzchnie części (≥ 0, jednolita jednostka dowolna); "
                    "tyle elementów, ile `cn_values`."
                ),
                description_en=(
                    "Areas of the parts (>= 0, any consistent unit); as many "
                    "items as `cn_values`."
                ),
                minimum=0,
            ),
            Option(
                name="fractions",
                type="number_list",
                description=(
                    "Udziały części w zlewni (0–1), sumujące się do 1; tyle "
                    "elementów, ile `cn_values`."
                ),
                description_en=(
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
    ),
)
