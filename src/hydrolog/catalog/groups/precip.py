"""Group ``precip``: design hyetographs and areal precipitation."""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_HIETOGRAM_TYPES = ("block", "triangular", "beta", "euler_ii")
_AREAL_METHODS = ("arithmetic", "thiessen", "idw", "isohyet")

_TYPE_PL = (
    "Typ rozkładu opadu w czasie; `alpha`, `beta` dotyczą typu beta, "
    "`peak_position` typów triangular i euler_ii."
)
_TYPE_EN = (
    "Temporal distribution of the rainfall; `alpha`, `beta` apply to beta, "
    "`peak_position` to triangular and euler_ii."
)

_TYPE_MEANINGS = {
    "block": "Uniform intensity over the whole duration.",
    "triangular": "Linear rise to the peak at `peak_position`, then linear fall.",
    "beta": "Shape of a Beta density with parameters `alpha` and `beta`.",
    "euler_ii": "DVWK Euler type II: peak at about 1/3 of the duration.",
}
_TYPE_MEANINGS_PL = {
    "block": "Stała intensywność w całym czasie trwania.",
    "triangular": "Liniowy wzrost do maksimum w `peak_position`, potem spadek.",
    "beta": "Kształt gęstości rozkładu beta o parametrach `alpha` i `beta`.",
    "euler_ii": "DVWK Euler typ II: maksimum po ok. 1/3 czasu trwania.",
}

HIETOGRAM_OPTIONS: tuple[Option, ...] = (
    Option(
        name="hietogram_type",
        type="choice",
        description_pl=_TYPE_PL,
        description=_TYPE_EN,
        required=True,
        choices=_HIETOGRAM_TYPES,
        meanings=_TYPE_MEANINGS,
        meanings_pl=_TYPE_MEANINGS_PL,
    ),
    Option(
        name="total_mm",
        type="number",
        description_pl="Całkowita wysokość opadu [mm]; > 0.",
        description="Total precipitation depth [mm]; > 0.",
        required=True,
        exclusive_minimum=0,
        unit="mm",
    ),
    Option(
        name="duration_min",
        type="number",
        description_pl=(
            "Czas trwania opadu [min]; > 0 i nie krótszy niż krok czasowy. "
            "Hietogram ma `int(duration_min / timestep_min)` kroków; gdy czas "
            "trwania nie jest wielokrotnością kroku, końcówka nie jest pokryta "
            "(uwaga w wyniku)."
        ),
        description=(
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
        description_pl="Krok czasowy hietogramu [min]; > 0; domyślnie 5.",
        description="Time step of the hyetograph [min]; > 0; default 5.",
        exclusive_minimum=0,
        unit="min",
        default=5.0,
    ),
    Option(
        name="alpha",
        type="number",
        description_pl=(
            "Parametr α rozkładu beta (kształt ramienia wznoszącego), > 0; "
            "tylko dla `beta`; domyślnie 2. Para (2; 5) daje wczesne maksimum "
            "(opad konwekcyjny), (2; 2) — symetryczne, (5; 2) — późne."
        ),
        description=(
            "Parameter α of the Beta distribution (shape of the rising limb), > 0; "
            "only for `beta`; default 2. The pair (2; 5) gives an early peak "
            "(convective storm), (2; 2) a symmetric one, (5; 2) a late one."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="beta",
        type="number",
        description_pl=(
            "Parametr β rozkładu beta (kształt ramienia opadającego), > 0; "
            "tylko dla `beta`; domyślnie 5."
        ),
        description=(
            "Parameter β of the Beta distribution (shape of the falling limb), > "
            "0; only for `beta`; default 5."
        ),
        exclusive_minimum=0,
    ),
    Option(
        name="peak_position",
        type="number",
        description_pl=(
            "Względne położenie maksimum w czasie trwania, 0 < p < 1 (bez "
            "końców); tylko dla `triangular` (domyślnie 0,5) i `euler_ii` "
            "(domyślnie 0,33)."
        ),
        description=(
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
        operation_id="hydrolog_precip_hietogram",
        summary_pl=(
            "Oblicz hietogram opadu projektowego: blokowy, trójkątny, beta lub Euler "
            "II."
        ),
        summary=(
            "Compute a design hyetograph: block, triangular, Beta or Euler type II."
        ),
        description_pl=(
            "Hietogram o zadanej sumie, czasie trwania i kroku: wysokości i natężenia "
            "w krokach. Stosuj jako opad projektowy dla `scs effective` lub "
            "`hydrograph generate`. Nie do średnich obszarowych (`precip areal`). "
            "Parametry innego typu są odrzucane."
        ),
        description=(
            "Hyetograph of a given total, duration and step: depths and intensities "
            "per step. Use as the design rainfall for `scs effective` or `hydrograph "
            "generate`. Not for areal averages (`precip areal`). Parameters of another"
            " type are rejected."
        ),
        function="hydrolog.operations.precip_hietogram",
        options=HIETOGRAM_OPTIONS,
        result_schema="hydrolog-precip-hietogram/1",
        cardinality="bounded",
        rules=(
            "Pass duration_min >= timestep_min.",
            (
                "Use alpha and beta only for beta, peak_position for triangular and "
                "euler_ii."
            ),
            "Read depths_mm in mm per step; check `notices`.",
        ),
        rules_pl=(
            "Podaj duration_min >= timestep_min.",
            "alpha i beta tylko dla beta, peak_position dla triangular i euler_ii.",
            "depths_mm to mm na krok; sprawdź `notices`.",
        ),
        errors=("validation_error",),
        example_results=(
            {
                "hietogram_type": "beta",
                "n_steps": 12,
                "peak_intensity_mm_per_h": 121.701,
                "parameters": {"alpha": 2.0, "beta": 5.0},
            },
            {
                "hietogram_type": "euler_ii",
                "n_steps": 24,
                "peak_intensity_mm_per_h": 77.7862,
                "parameters": {"peak_position": 0.33},
            },
        ),
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
        operation_id="hydrolog_precip_areal",
        summary_pl=(
            "Oblicz opad obszarowy z posterunków: średnia arytmetyczna, Thiessen, IDW "
            "lub izohiety."
        ),
        summary=(
            "Compute areal precipitation from gauges: arithmetic mean, Thiessen, IDW "
            "or isohyets."
        ),
        description_pl=(
            "Opad obszarowy [mm] z posterunków punktowych wg `method`: arithmetic, "
            "thiessen (wymaga powierzchni wieloboków), idw (punkt lub siatka) lub "
            "isohyet. Nie do pobierania danych z posterunków (IMGWTools) ani opadu "
            "projektowego (`precip hietogram`)."
        ),
        description=(
            "Areal precipitation [mm] from point gauges by `method`: arithmetic, "
            "thiessen (needs polygon areas), idw (point or grid) or isohyet. Not for "
            "downloading gauge data (IMGWTools) or design rainfall (`precip "
            "hietogram`)."
        ),
        function="hydrolog.operations.precip_areal",
        options=(
            Option(
                name="method",
                type="choice",
                description_pl=(
                    "Metoda opadu obszarowego; opcje wymagane przez każdą metodę "
                    "wskazują opisy pozostałych opcji (`Dla ...`)."
                ),
                description=(
                    "Areal precipitation method; the options each method needs "
                    "are marked in the other option descriptions (`For ...`)."
                ),
                required=True,
                choices=_AREAL_METHODS,
                meanings={
                    "arithmetic": "Arithmetic mean of the gauges.",
                    "thiessen": "Mean weighted by the Thiessen polygon areas.",
                    "idw": "Inverse distance weighted value at a point or grid.",
                    "isohyet": "Mean weighted by the area fractions of isohyet zones.",
                },
                meanings_pl={
                    "arithmetic": "Średnia arytmetyczna posterunków.",
                    "thiessen": "Średnia ważona powierzchniami wieloboków Thiessena.",
                    "idw": "Wartość ważona odwrotnością odległości (punkt lub siatka).",
                    "isohyet": "Średnia ważona udziałami powierzchni stref izohiet.",
                },
            ),
            Option(
                name="stations",
                type="object_list",
                description_pl=(
                    'Posterunki opadowe jako obiekty `{"name": ..., "x": ..., '
                    '"y": ..., "precipitation_mm": ...}` (opcjonalnie '
                    "`elevation_m`); dla arithmetic, thiessen i idw."
                ),
                description=(
                    'Precipitation gauges as objects `{"name": ..., "x": ..., '
                    '"y": ..., "precipitation_mm": ...}` (optionally '
                    "`elevation_m`); for arithmetic, thiessen and idw."
                ),
            ),
            Option(
                name="stations_file",
                type="path",
                path_role="input",
                description_pl=(
                    "Plik CSV (nagłówek `name,x,y,precipitation_mm[,elevation_m]`) "
                    "lub JSON z posterunkami; alternatywa dla `stations`."
                ),
                description=(
                    "CSV file (header `name,x,y,precipitation_mm[,elevation_m]`) "
                    "or JSON file with the gauges; alternative to `stations`."
                ),
            ),
            Option(
                name="polygon_areas_km2",
                type="object",
                description_pl=(
                    "Dla thiessen: powierzchnie wieloboków Thiessena w zlewni "
                    "[km²] jako obiekt nazwa posterunku → powierzchnia (≥ 0), np. "
                    '`{"Balice": 18.5, "Skawina": 12.6}`.'
                ),
                description=(
                    "For thiessen: the areas of the Thiessen polygons inside the "
                    "watershed [km2] as an object gauge name -> area (>= 0), e.g. "
                    '`{"Balice": 18.5, "Skawina": 12.6}`.'
                ),
            ),
            Option(
                name="target_x",
                type="number",
                description_pl=(
                    "Dla idw: współrzędna X punktu docelowego (jednostka jak "
                    "współrzędne posterunków); razem z `target_y`."
                ),
                description=(
                    "For idw: X coordinate of the target point (same unit as the "
                    "gauge coordinates); together with `target_y`."
                ),
            ),
            Option(
                name="target_y",
                type="number",
                description_pl=(
                    "Dla idw: współrzędna Y punktu docelowego; razem z `target_x`."
                ),
                description=(
                    "For idw: Y coordinate of the target point; together with "
                    "`target_x`."
                ),
            ),
            Option(
                name="grid_x",
                type="number_list",
                description_pl=(
                    "Dla idw: współrzędne X punktów siatki w zlewni (średnia z "
                    "wartości IDW w punktach); razem z `grid_y` tej samej "
                    "długości, zamiast `target_x`/`target_y`."
                ),
                description=(
                    "For idw: X coordinates of grid points inside the watershed "
                    "(the mean of the IDW values at the points); together with "
                    "`grid_y` of the same length, instead of `target_x`/`target_y`."
                ),
            ),
            Option(
                name="grid_y",
                type="number_list",
                description_pl=(
                    "Dla idw: współrzędne Y punktów siatki; razem z `grid_x`."
                ),
                description=(
                    "For idw: Y coordinates of the grid points; together with `grid_x`."
                ),
            ),
            Option(
                name="power",
                type="number",
                description_pl=(
                    "Dla idw: wykładnik odległości p (> 0); domyślnie 2. Większe "
                    "p silniej faworyzuje bliskie posterunki."
                ),
                description=(
                    "For idw: distance exponent p (> 0); default 2. A larger p "
                    "favours nearby gauges more strongly."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="max_distance",
                type="number",
                description_pl=(
                    "Dla idw w punkcie: największa odległość posterunku (jednostka "
                    "współrzędnych); domyślnie wszystkie posterunki."
                ),
                description=(
                    "For idw at a point: the largest gauge distance (coordinate "
                    "unit); all gauges by default."
                ),
                exclusive_minimum=0,
            ),
            Option(
                name="isohyet_values_mm",
                type="number_list",
                description_pl=(
                    "Dla isohyet: wartości kolejnych izohiet [mm] (co najmniej "
                    "2; n izohiet to n−1 stref)."
                ),
                description=(
                    "For isohyet: values of the consecutive isohyets [mm] (at "
                    "least 2; n isohyets make n-1 zones)."
                ),
                minimum=0,
                unit="mm",
            ),
            Option(
                name="area_fractions",
                type="number_list",
                description_pl=(
                    "Dla isohyet: udziały powierzchni zlewni między kolejnymi "
                    "izohietami (n−1 wartości z przedziału 0–1, suma 1)."
                ),
                description=(
                    "For isohyet: the fractions of the watershed area between "
                    "consecutive isohyets (n-1 values in 0-1, sum 1)."
                ),
                minimum=0,
                maximum=1,
            ),
        ),
        result_schema="hydrolog-precip-areal/1",
        cardinality="single",
        rules=(
            "Give the options each method needs; see the option descriptions.",
            "Give coordinates in one metric system (e.g. EPSG:2180).",
            "Check `notices` in the result.",
        ),
        rules_pl=(
            "Podaj opcje wymagane przez metodę; zob. opisy opcji.",
            "Podaj współrzędne w jednym układzie metrycznym (np. EPSG:2180).",
            "Sprawdź `notices` w wyniku.",
        ),
        errors=("validation_error", "not_found", "data_error", "forbidden"),
        example_results=(
            {
                "method": "arithmetic",
                "areal_precipitation_mm": 32.1333,
                "n_stations": 3,
            },
            {
                "method": "thiessen",
                "areal_precipitation_mm": 32.1766,
                "station_weights": {
                    "Balice": 0.408389,
                    "Krzeszowice": 0.313466,
                    "Skawina": 0.278146,
                },
            },
            {"method": "idw", "areal_precipitation_mm": 31.6884, "power": 2.0},
            {
                "method": "isohyet",
                "areal_precipitation_mm": 34.0,
                "area_fractions": [0.3, 0.5, 0.2],
            },
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
