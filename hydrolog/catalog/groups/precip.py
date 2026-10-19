"""Group ``precip``: design hyetographs and areal precipitation."""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_HIETOGRAM_TYPES = ("block", "triangular", "beta", "euler_ii")
_AREAL_METHODS = ("arithmetic", "thiessen", "idw", "isohyet")

_TYPE_PL = (
    "Typ rozkładu opadu w czasie: block — blokowy (stała intensywność); "
    "triangular — trójkątny z maksimum w `peak_position`; beta — rozkład beta "
    "(parametry `alpha`, `beta`); euler_ii — DVWK Euler typ II (maksimum po ok. "
    "1/3 czasu trwania, naprzemienne układanie bloków)."
)
_TYPE_EN = (
    "Temporal distribution of the rainfall: block - uniform intensity; "
    "triangular - triangular with the peak at `peak_position`; beta - Beta "
    "distribution (parameters `alpha`, `beta`); euler_ii - DVWK Euler type II "
    "(peak at about 1/3 of the duration, alternating blocks)."
)

HIETOGRAM_OPTIONS: tuple[Option, ...] = (
    Option(
        name="hietogram_type",
        type="choice",
        description=_TYPE_PL,
        description_en=_TYPE_EN,
        required=True,
        choices=_HIETOGRAM_TYPES,
    ),
    Option(
        name="total_mm",
        type="number",
        description="Całkowita wysokość opadu [mm]; > 0.",
        description_en="Total precipitation depth [mm]; > 0.",
        required=True,
        exclusive_minimum=0,
        unit="mm",
    ),
    Option(
        name="duration_min",
        type="number",
        description=(
            "Czas trwania opadu [min]; > 0 i nie krótszy niż krok czasowy. "
            "Hietogram ma `int(duration_min / timestep_min)` kroków; gdy czas "
            "trwania nie jest wielokrotnością kroku, końcówka nie jest pokryta "
            "(uwaga w wyniku)."
        ),
        description_en=(
            "Rainfall duration [min]; > 0 and not shorter than the time step. The "
            "hyetograph has `int(duration_min / timestep_min)` steps; when the "
            "duration is not a multiple of the step the tail is not covered (a "
            "notice reports it)."
        ),
        required=True,
        exclusive_minimum=0,
        unit="min",
    ),
    Option(
        name="timestep_min",
        type="number",
        description="Krok czasowy hietogramu [min]; > 0; domyślnie 5.",
        description_en="Time step of the hyetograph [min]; > 0; default 5.",
        exclusive_minimum=0,
        unit="min",
        default=5.0,
    ),
    Option(
        name="alpha",
        type="number",
        description=(
            "Parametr α rozkładu beta (kształt ramienia wznoszącego), > 0; "
            "tylko dla `beta`; domyślnie 2. Para (2; 5) daje wczesne maksimum "
            "(opad konwekcyjny), (2; 2) — symetryczne, (5; 2) — późne."
        ),
        description_en=(
            "Parameter α of the Beta distribution (shape of the rising limb), > 0; "
            "only for `beta`; default 2. The pair (2; 5) gives an early peak "
            "(convective storm), (2; 2) a symmetric one, (5; 2) a late one."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="beta",
        type="number",
        description=(
            "Parametr β rozkładu beta (kształt ramienia opadającego), > 0; "
            "tylko dla `beta`; domyślnie 5."
        ),
        description_en=(
            "Parameter β of the Beta distribution (shape of the falling limb), > "
            "0; only for `beta`; default 5."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="peak_position",
        type="number",
        description=(
            "Względne położenie maksimum w czasie trwania, 0 < p < 1 (bez "
            "końców); tylko dla `triangular` (domyślnie 0,5) i `euler_ii` "
            "(domyślnie 0,33)."
        ),
        description_en=(
            "Relative position of the peak within the duration, 0 < p < 1 "
            "(exclusive); only for `triangular` (default 0.5) and `euler_ii` "
            "(default 0.33)."
        ),
        exclusive_minimum=0,
        maximum=1,
    ),
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="precip hietogram",
        operation_id="precip_hietogram",
        summary="Hietogram opadu projektowego: blokowy, trójkątny, beta lub Euler II.",
        summary_en="Design hyetograph: block, triangular, Beta or Euler type II.",
        description=(
            "Generuje hietogram — rozkład wysokości opadu w czasie — dla zadanej "
            "sumy `total_mm` [mm], czasu trwania `duration_min` [min] i kroku "
            "`timestep_min` [min]. Typy: block (stała intensywność); triangular "
            "(liniowy wzrost do `peak_position` i spadek); beta (gęstość rozkładu "
            "beta o parametrach `alpha`, `beta` w środkach przedziałów); euler_ii "
            "(DVWK Euler II: malejące rangi bloków 1/r^0,7 układane naprzemiennie "
            "wokół maksimum położonego na ok. 1/3 czasu trwania; DVWK 1984, "
            "Regeln 113). Suma bloków zawsze równa się `total_mm`. Wynik: "
            "wysokości opadu w krokach `depths_mm` [mm] (w bibliotece pole "
            "`intensities_mm` — to wysokości, nie natężenia), natężenia "
            "`intensities_mm_per_h` [mm/h], czasy końców przedziałów `times_min` "
            "[min], liczba kroków i maksymalne natężenie. Parametry typu "
            "niewłaściwego dla wybranego rozkładu są odrzucane. Wynik można "
            "wprowadzić do `scs effective` (`values`) lub `hydrograph generate`."
        ),
        description_en=(
            "Generates a hyetograph - the distribution of precipitation depth in "
            "time - for a given total `total_mm` [mm], duration `duration_min` "
            "[min] and step `timestep_min` [min]. Types: block (uniform "
            "intensity); triangular (linear rise to `peak_position` and decay); "
            "beta (Beta density with parameters `alpha`, `beta` at the interval "
            "midpoints); euler_ii (DVWK Euler II: block ranks 1/r^0.7 placed "
            "alternately around a peak at about 1/3 of the duration; DVWK 1984, "
            "Regeln 113). The blocks always sum to `total_mm`. Result: the depths "
            "per step `depths_mm` [mm] (the library field `intensities_mm` - "
            "depths, not rates), the intensities `intensities_mm_per_h` [mm/h], "
            "the interval end times `times_min` [min], the number of steps and the "
            "peak intensity. Parameters of another type than the chosen one are "
            "rejected. The result can be fed into `scs effective` (`values`) or "
            "`hydrograph generate`."
        ),
        function="hydrolog.operations:precip_hietogram",
        options=HIETOGRAM_OPTIONS,
        examples=(
            {
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
                "timestep_min": 5.0,
                "alpha": 2.0,
                "beta": 5.0,
            },
            {"hietogram_type": "euler_ii", "total_mm": 38.4, "duration_min": 120.0},
        ),
    ),
    Command(
        name="precip areal",
        operation_id="precip_areal",
        summary="Opad obszarowy z posterunków: średnia arytmetyczna, Thiessen, IDW lub izohiety.",
        summary_en="Areal precipitation from gauges: arithmetic mean, Thiessen, IDW or isohyets.",
        description=(
            "Opad obszarowy zlewni [mm] z opadów punktowych. `method`: arithmetic "
            "— średnia arytmetyczna posterunków (dla gęstej, równomiernej sieci i "
            "płaskiego terenu); thiessen — średnia ważona powierzchniami "
            "wieloboków Thiessena (1911) w zlewni, P = Σ P_i·A_i / Σ A_i, "
            "powierzchnie `polygon_areas_km2` [km²] podaje użytkownik (posterunki "
            "bez powierzchni są pomijane); idw — ważenie odwrotnością odległości "
            "(Shepard, 1968), w_i = 1/d_i^p: wartość w punkcie `target_x`, "
            "`target_y` (np. w środku ciężkości zlewni) albo średnia z wartości w "
            "punktach siatki `grid_x`, `grid_y`; `power` p domyślnie 2, "
            "`max_distance` ogranicza posterunki do tych w zadanej odległości "
            "(tylko dla punktu); isohyet — metoda izohiet: średnia ważona "
            "udziałami powierzchni stref `area_fractions` (suma 1) ze średnimi "
            "(P_i + P_{i+1})/2 sąsiednich izohiet `isohyet_values_mm`. "
            "Posterunki: `stations` (obiekty `name`, `x`, `y`, "
            "`precipitation_mm`, opcjonalnie `elevation_m`) albo `stations_file` "
            "(CSV/JSON z tymi kolumnami); współrzędne w jednym układzie "
            "metrycznym (np. PL-1992, EPSG:2180) — ich jednostka wyznacza "
            "odległości w IDW i `max_distance`. Wynik: opad obszarowy, wagi i "
            "udziały posterunków (thiessen, idw), użyte parametry."
        ),
        description_en=(
            "Areal precipitation of a watershed [mm] from point measurements. "
            "`method`: arithmetic - the arithmetic mean of the gauges (for a dense, "
            "even network and flat terrain); thiessen - the mean weighted by the "
            "areas of the Thiessen (1911) polygons inside the watershed, P = sum "
            "P_i·A_i / sum A_i, the areas `polygon_areas_km2` [km2] are supplied "
            "by the user (gauges without an area are skipped); idw - inverse "
            "distance weighting (Shepard, 1968), w_i = 1/d_i^p: the value at the "
            "point `target_x`, `target_y` (e.g. the watershed centroid) or the "
            "mean of the values at the grid points `grid_x`, `grid_y`; `power` p "
            "defaults to 2, `max_distance` restricts the gauges to those within "
            "the distance (point only); isohyet - the isohyetal method: the mean "
            "weighted by the area fractions of the zones `area_fractions` (sum 1) "
            "with the means (P_i + P_{i+1})/2 of neighbouring isohyets "
            "`isohyet_values_mm`. Gauges: `stations` (objects `name`, `x`, `y`, "
            "`precipitation_mm`, optionally `elevation_m`) or `stations_file` "
            "(CSV/JSON with those columns); coordinates in one metric system "
            "(e.g. PL-1992, EPSG:2180) - their unit sets the IDW distances and "
            "`max_distance`. Result: the areal precipitation, the weights and "
            "contributions of the gauges (thiessen, idw) and the parameters used."
        ),
        function="hydrolog.operations:precip_areal",
        options=(
            Option(
                name="method",
                type="choice",
                description=(
                    "Metoda: arithmetic, thiessen, idw lub isohyet (wymagane "
                    "opcje każdej metody opisano w opisie komendy)."
                ),
                description_en=(
                    "Method: arithmetic, thiessen, idw or isohyet (the options "
                    "each method needs are listed in the command description)."
                ),
                required=True,
                choices=_AREAL_METHODS,
            ),
            Option(
                name="stations",
                type="object_list",
                description=(
                    'Posterunki opadowe jako obiekty `{"name": ..., "x": ..., '
                    '"y": ..., "precipitation_mm": ...}` (opcjonalnie '
                    "`elevation_m`); dla arithmetic, thiessen i idw."
                ),
                description_en=(
                    'Precipitation gauges as objects `{"name": ..., "x": ..., '
                    '"y": ..., "precipitation_mm": ...}` (optionally '
                    "`elevation_m`); for arithmetic, thiessen and idw."
                ),
            ),
            Option(
                name="stations_file",
                type="path",
                description=(
                    "Plik CSV (nagłówek `name,x,y,precipitation_mm[,elevation_m]`) "
                    "lub JSON z posterunkami; alternatywa dla `stations`."
                ),
                description_en=(
                    "CSV file (header `name,x,y,precipitation_mm[,elevation_m]`) "
                    "or JSON file with the gauges; alternative to `stations`."
                ),
            ),
            Option(
                name="polygon_areas_km2",
                type="object",
                description=(
                    "Dla thiessen: powierzchnie wieloboków Thiessena w zlewni "
                    "[km²] jako obiekt nazwa posterunku → powierzchnia (≥ 0), np. "
                    '`{"Balice": 18.5, "Skawina": 12.6}`.'
                ),
                description_en=(
                    "For thiessen: the areas of the Thiessen polygons inside the "
                    "watershed [km2] as an object gauge name -> area (>= 0), e.g. "
                    '`{"Balice": 18.5, "Skawina": 12.6}`.'
                ),
            ),
            Option(
                name="target_x",
                type="number",
                description=(
                    "Dla idw: współrzędna X punktu docelowego (jednostka jak "
                    "współrzędne posterunków); razem z `target_y`."
                ),
                description_en=(
                    "For idw: X coordinate of the target point (same unit as the "
                    "gauge coordinates); together with `target_y`."
                ),
            ),
            Option(
                name="target_y",
                type="number",
                description=(
                    "Dla idw: współrzędna Y punktu docelowego; razem z " "`target_x`."
                ),
                description_en=(
                    "For idw: Y coordinate of the target point; together with "
                    "`target_x`."
                ),
            ),
            Option(
                name="grid_x",
                type="number_list",
                description=(
                    "Dla idw: współrzędne X punktów siatki w zlewni (średnia z "
                    "wartości IDW w punktach); razem z `grid_y` tej samej "
                    "długości, zamiast `target_x`/`target_y`."
                ),
                description_en=(
                    "For idw: X coordinates of grid points inside the watershed "
                    "(the mean of the IDW values at the points); together with "
                    "`grid_y` of the same length, instead of `target_x`/`target_y`."
                ),
            ),
            Option(
                name="grid_y",
                type="number_list",
                description="Dla idw: współrzędne Y punktów siatki; razem z `grid_x`.",
                description_en=(
                    "For idw: Y coordinates of the grid points; together with "
                    "`grid_x`."
                ),
            ),
            Option(
                name="power",
                type="number",
                description=(
                    "Dla idw: wykładnik odległości p (> 0); domyślnie 2. Większe "
                    "p silniej faworyzuje bliskie posterunki."
                ),
                description_en=(
                    "For idw: distance exponent p (> 0); default 2. A larger p "
                    "favours nearby gauges more strongly."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="max_distance",
                type="number",
                description=(
                    "Dla idw w punkcie: największa odległość posterunku (jednostka "
                    "współrzędnych); domyślnie wszystkie posterunki."
                ),
                description_en=(
                    "For idw at a point: the largest gauge distance (coordinate "
                    "unit); all gauges by default."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="isohyet_values_mm",
                type="number_list",
                description=(
                    "Dla isohyet: wartości kolejnych izohiet [mm] (co najmniej "
                    "2; n izohiet to n−1 stref)."
                ),
                description_en=(
                    "For isohyet: values of the consecutive isohyets [mm] (at "
                    "least 2; n isohyets make n-1 zones)."
                ),
                minimum=0,
                unit="mm",
            ),
            Option(
                name="area_fractions",
                type="number_list",
                description=(
                    "Dla isohyet: udziały powierzchni zlewni między kolejnymi "
                    "izohietami (n−1 wartości z przedziału 0–1, suma 1)."
                ),
                description_en=(
                    "For isohyet: the fractions of the watershed area between "
                    "consecutive isohyets (n-1 values in 0-1, sum 1)."
                ),
                minimum=0,
                maximum=1,
            ),
        ),
        examples=(
            {
                "method": "arithmetic",
                "stations": [
                    {
                        "name": "Balice",
                        "x": 555500,
                        "y": 244300,
                        "precipitation_mm": 31.2,
                    },
                    {
                        "name": "Krzeszowice",
                        "x": 545900,
                        "y": 249700,
                        "precipitation_mm": 36.8,
                    },
                    {
                        "name": "Skawina",
                        "x": 562900,
                        "y": 229400,
                        "precipitation_mm": 28.4,
                    },
                ],
            },
            {
                "method": "thiessen",
                "stations": [
                    {
                        "name": "Balice",
                        "x": 555500,
                        "y": 244300,
                        "precipitation_mm": 31.2,
                    },
                    {
                        "name": "Krzeszowice",
                        "x": 545900,
                        "y": 249700,
                        "precipitation_mm": 36.8,
                    },
                    {
                        "name": "Skawina",
                        "x": 562900,
                        "y": 229400,
                        "precipitation_mm": 28.4,
                    },
                ],
                "polygon_areas_km2": {
                    "Balice": 18.5,
                    "Krzeszowice": 14.2,
                    "Skawina": 12.6,
                },
            },
            {
                "method": "idw",
                "stations": [
                    {
                        "name": "Balice",
                        "x": 555500,
                        "y": 244300,
                        "precipitation_mm": 31.2,
                    },
                    {
                        "name": "Krzeszowice",
                        "x": 545900,
                        "y": 249700,
                        "precipitation_mm": 36.8,
                    },
                    {
                        "name": "Skawina",
                        "x": 562900,
                        "y": 229400,
                        "precipitation_mm": 28.4,
                    },
                ],
                "target_x": 553000,
                "target_y": 240000,
                "power": 2.0,
            },
            {
                "method": "isohyet",
                "isohyet_values_mm": [20.0, 30.0, 40.0, 50.0],
                "area_fractions": [0.3, 0.5, 0.2],
            },
        ),
    ),
)
