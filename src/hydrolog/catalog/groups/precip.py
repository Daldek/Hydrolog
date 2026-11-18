"""Group ``precip``: design hyetographs, PMAXTP depths and areal precipitation."""

from __future__ import annotations

from collections.abc import Iterable

from hydrolog._pmaxtp import (
    DURATIONS_MIN,
    LATITUDE_RANGE,
    LONGITUDE_RANGE,
    METHODS,
    PROBABILITIES_PERCENT,
)
from hydrolog.catalog.groups._attribution import ATTRIBUTION
from hydrolog.catalog.spec import Command, Option

_HIETOGRAM_TYPES = ("block", "triangular", "beta", "euler_ii")
_AREAL_METHODS = ("arithmetic", "thiessen", "idw", "isohyet")

_TYPE_PL = (
    "Typ rozkładu opadu w czasie; `alpha`, `beta` dotyczą typu beta, "
    "`peak_position` typu triangular, krzywa `depth_duration_mm` (lub "
    "`depth_duration_file`) typu euler_ii."
)
_TYPE_EN = (
    "Temporal distribution of the rainfall; `alpha`, `beta` apply to beta, "
    "`peak_position` to triangular, the curve `depth_duration_mm` (or "
    "`depth_duration_file`) to euler_ii."
)

_TYPE_MEANINGS = {
    "block": "Uniform intensity over the whole duration.",
    "triangular": (
        "Triangle of Yen and Chow: linear rise to the peak at `peak_position` of "
        "the duration, linear fall; each step holds its integral."
    ),
    "beta": (
        "Beta density with parameters `alpha` and `beta`; each step holds its "
        "integral (differences of the Beta distribution function)."
    ),
    "euler_ii": (
        "Euler type II of ATV-DVWK-A 118, built from a depth-duration curve: peak "
        "from 0.3 of the duration (rounded down to the step)."
    ),
}
_TYPE_MEANINGS_PL = {
    "block": "Stała intensywność w całym czasie trwania.",
    "triangular": (
        "Trójkąt Yena i Chowa: liniowy wzrost do maksimum w `peak_position` czasu "
        "trwania, potem spadek; krok ma całkę trójkąta w swoim przedziale."
    ),
    "beta": (
        "Gęstość rozkładu beta o parametrach `alpha` i `beta`; krok ma jej całkę "
        "(różnicę dystrybuanty) w swoim przedziale."
    ),
    "euler_ii": (
        "Euler typu II wg ATV-DVWK-A 118, z krzywej wysokość–czas trwania: "
        "maksimum od 0,3 czasu trwania (w dół do wielokrotności kroku)."
    ),
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
        description_pl=(
            "Całkowita wysokość opadu [mm]; > 0. Wymagana poza `euler_ii`, którego "
            "suma to wysokość krzywej dla `duration_min` (podana musi być jej równa "
            "z dokładnością 0,005 mm)."
        ),
        description=(
            "Total precipitation depth [mm]; > 0. Required except for `euler_ii`, "
            "whose total is the depth of its curve at `duration_min` (a total given "
            "must equal it to 0.005 mm)."
        ),
        exclusive_minimum=0,
        unit="mm",
    ),
    Option(
        name="duration_min",
        type="number",
        description_pl=(
            "Czas trwania opadu [min]; > 0, nie krótszy niż krok czasowy i jego "
            "całkowita wielokrotność: hietogram ma `duration_min / timestep_min` "
            "kroków i trwa cały czas trwania."
        ),
        description=(
            "Rainfall duration [min]; > 0, not shorter than the time step and a "
            "whole number of steps: the hyetograph has `duration_min / timestep_min` "
            "steps and lasts the whole duration."
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
            "tylko dla `beta`; domyślnie 2. Para (2; 5) daje maksimum w 0,2 "
            "czasu trwania, (2; 2) — w środku, (5; 2) — w 0,8."
        ),
        description=(
            "Parameter α of the Beta distribution (shape of the rising limb), > 0; "
            "only for `beta`; default 2. The pair (2; 5) puts the peak at 0.2 of "
            "the duration, (2; 2) at the centre, (5; 2) at 0.8."
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
            "Względne położenie maksimum trójkąta w czasie trwania (współczynnik "
            "r Yena i Chowa), 0 < r < 1 (bez końców); tylko dla `triangular`; "
            "domyślnie 0,5."
        ),
        description=(
            "Relative time of the peak of the triangle within the duration (Yen "
            "and Chow's storm advancement coefficient r), 0 < r < 1 (exclusive); "
            "only for `triangular`; default 0.5."
        ),
        exclusive_minimum=0,
        exclusive_maximum=1,
    ),
    Option(
        name="depth_duration_mm",
        type="object",
        description_pl=(
            "Krzywa wysokość–czas trwania jednego prawdopodobieństwa dla `euler_ii`: "
            'obiekt czas trwania [min] → wysokość [mm], np. `{"5": 8.48, "10": '
            "12.16, ...}` albo `depth_duration_mm` z `precip pmaxtp`; niemalejąca, "
            "od kroku czasowego do `duration_min`. Czasy między jej punktami są "
            "interpolowane liniowo względem ln D. Bloki to jej przyrosty w kolejności "
            "czasów trwania: pierwszy w przedziale szczytu, kolejne przed nim do "
            "t = 0, reszta po nim (jak itwh; dla krzywej IDF to przyrosty "
            "uporządkowane malejąco)."
        ),
        description=(
            "Depth-duration curve of one probability for `euler_ii`: an object of "
            'duration [min] to depth [mm], e.g. `{"5": 8.48, "10": 12.16, ...}` or '
            "the `depth_duration_mm` of `precip pmaxtp`; not decreasing, from the "
            "time step to `duration_min`. Durations between its points are "
            "interpolated linearly in ln D. The blocks are its increments in the "
            "order of the durations: the first in the peak interval, the next "
            "before it back to t = 0, the rest after it (as itwh does; for an IDF "
            "curve the increments sorted from the largest)."
        ),
    ),
    Option(
        name="depth_duration_file",
        type="path",
        path_role="input",
        description_pl=(
            "Plik z krzywą dla `euler_ii` zamiast `depth_duration_mm`: CSV "
            "`duration_min,depth_mm` albo JSON (taki obiekt, tabela lub to, co "
            "wypisuje `precip pmaxtp --json`; jego atrybucja przechodzi do wyniku)."
        ),
        description=(
            "File with the curve for `euler_ii` instead of `depth_duration_mm`: CSV "
            "`duration_min,depth_mm` or JSON (such an object, a table, or what "
            "`precip pmaxtp --json` prints, whose attribution the result carries)."
        ),
    ),
)


def _listed(values: Iterable[float], comma: bool = False) -> str:
    """Write the values as text: "0.01, 0.02", or "0,01; 0,02" with ``comma``."""
    texts = [f"{value:g}" for value in values]
    return "; ".join(t.replace(".", ",") for t in texts) if comma else ", ".join(texts)


PMAXTP_OPTIONS: tuple[Option, ...] = (
    Option(
        name="latitude",
        type="number",
        description_pl=(
            "Szerokość geograficzna punktu (WGS84, stopnie dziesiętne); PMAXTP "
            "obejmuje Polskę."
        ),
        description=(
            "Latitude of the point (WGS84, decimal degrees); PMAXTP covers Poland."
        ),
        required=True,
        minimum=LATITUDE_RANGE[0],
        maximum=LATITUDE_RANGE[1],
        unit="deg",
    ),
    Option(
        name="longitude",
        type="number",
        description_pl="Długość geograficzna punktu (WGS84, stopnie dziesiętne).",
        description="Longitude of the point (WGS84, decimal degrees).",
        required=True,
        minimum=LONGITUDE_RANGE[0],
        maximum=LONGITUDE_RANGE[1],
        unit="deg",
    ),
    Option(
        name="duration_min",
        type="number",
        description_pl=(
            "Czas trwania opadu [min], jedna z wartości tablic PMAXTP: "
            f"{_listed(DURATIONS_MIN, comma=True)}."
        ),
        description=(
            "Rainfall duration [min], one of the values of the PMAXTP tables: "
            f"{_listed(DURATIONS_MIN)}."
        ),
        required=True,
        minimum=DURATIONS_MIN[0],
        maximum=DURATIONS_MIN[-1],
        unit="min",
    ),
    Option(
        name="probability_percent",
        type="number",
        description_pl=(
            "Prawdopodobieństwo przewyższenia [%], jedna z wartości tablic PMAXTP: "
            f"{_listed(PROBABILITIES_PERCENT, comma=True)}."
        ),
        description=(
            "Probability of exceedance [%], one of the values of the PMAXTP tables: "
            f"{_listed(PROBABILITIES_PERCENT)}."
        ),
        required=True,
        minimum=PROBABILITIES_PERCENT[0],
        maximum=PROBABILITIES_PERCENT[-1],
        unit="%",
    ),
    Option(
        name="method",
        type="choice",
        description_pl="Metoda oszacowania PMAXTP; domyślnie POT.",
        description="Estimation method of PMAXTP; default POT.",
        choices=METHODS,
        default="POT",
        meanings={
            "POT": (
                "Peaks over a threshold; IMGW-PIB recommends it for p >= 50 % and "
                "treats AMP and POT as equivalent below."
            ),
            "AMP": "Annual maximum precipitation.",
        },
        meanings_pl={
            "POT": (
                "Szczyty ponad progiem; IMGW-PIB zaleca ją dla p >= 50 %, a poniżej "
                "uznaje AMP i POT za równorzędne."
            ),
            "AMP": "Maksima roczne opadu.",
        },
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
            "Hietogram o zadanym czasie trwania i kroku: wysokości i natężenia w "
            "krokach. Blokowy, trójkątny i beta rozkładają `total_mm`; Euler II "
            "(ATV-DVWK-A 118) powstaje z krzywej wysokość–czas trwania "
            "jednego prawdopodobieństwa, np. z `precip pmaxtp`. Opad projektowy dla "
            "`scs effective` lub `hydrograph generate`. Parametry innego typu są "
            "odrzucane."
        ),
        description=(
            "Hyetograph of a duration and step: depth and intensity per step. "
            "Block, triangular and Beta spread `total_mm`; Euler II (ATV-DVWK-A 118) "
            "is built from the depth-duration curve of one probability (e.g. "
            "`precip pmaxtp`). Design rainfall for `scs effective` or `hydrograph "
            "generate`. Parameters of another type are rejected."
        ),
        function="hydrolog.operations.precip_hietogram",
        options=(*HIETOGRAM_OPTIONS, ATTRIBUTION),
        result_schema="hydrolog-precip-hietogram/1",
        cardinality="bounded",
        rules=(
            "Pass duration_min as a whole multiple of timestep_min.",
            (
                "Use alpha and beta only for beta, peak_position for triangular, "
                "depth_duration_mm or depth_duration_file for euler_ii."
            ),
            "Read depths_mm in mm per step.",
        ),
        rules_pl=(
            "Podaj duration_min jako całkowitą wielokrotność timestep_min.",
            (
                "alpha i beta tylko dla beta, peak_position dla triangular, "
                "depth_duration_mm lub depth_duration_file dla euler_ii."
            ),
            "depths_mm to mm na krok.",
        ),
        errors=("validation_error", "not_found", "data_error"),
        example_results=(
            {
                "hietogram_type": "beta",
                "n_steps": 12,
                "peak_intensity_mm_per_h": 121.704,
                "parameters": {"alpha": 2.0, "beta": 5.0},
            },
            {
                "hietogram_type": "euler_ii",
                "total_mm": 23.66,
                "n_steps": 12,
                "peak_intensity_mm_per_h": 101.76,
                "parameters": {"peak_start_min": 15.0},
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
            {
                "hietogram_type": "euler_ii",
                "duration_min": 60.0,
                "depth_duration_mm": {
                    "5": 8.48,
                    "10": 12.16,
                    "15": 14.49,
                    "30": 18.82,
                    "45": 21.58,
                    "60": 23.66,
                },
            },
        ),
    ),
    Command(
        name="precip pmaxtp",
        operation_id="hydrolog_precip_pmaxtp",
        summary_pl=(
            "Pobierz z IMGW-PIB wysokość opadu PMAXTP dla punktu, czasu trwania i "
            "prawdopodobieństwa."
        ),
        summary=(
            "Fetch the PMAXTP depth of IMGW-PIB for a point, a duration and a "
            "probability."
        ),
        description_pl=(
            "Wysokość opadu maksymalnego [mm] o czasie `duration_min` i "
            "prawdopodobieństwie przewyższenia `probability_percent` z atlasu PMAXTP "
            "IMGW-PIB (POT albo AMP) oraz wysokości wszystkich czasów trwania "
            "(`depth_duration_mm`). Korzysta z sieci (Obserwator, dodatek `pmaxtp`). "
            "Podaj wysokość jako `total_mm`, a krzywą jako `depth_duration_mm` "
            "(euler_ii)."
        ),
        description=(
            "Maximum rainfall depth [mm] of `duration_min` at exceedance probability "
            "`probability_percent` from the PMAXTP atlas of IMGW-PIB (POT or AMP), "
            "with the depths of all its durations. Uses the network (Obserwator, "
            "extra `pmaxtp`). Give the depth as `total_mm`, the depths as the curve "
            "`depth_duration_mm` of euler_ii."
        ),
        function="hydrolog.operations.precip_pmaxtp",
        options=PMAXTP_OPTIONS,
        result_schema="hydrolog-precip-pmaxtp/1",
        cardinality="single",
        network=True,
        rules=(
            "Give a point in Poland (WGS84).",
            "Pick duration_min and probability_percent from their descriptions.",
            "Show attribution and terms_notice with the depth; give them as "
            "attribution to the command that takes it.",
        ),
        rules_pl=(
            "Podaj punkt w Polsce (WGS84).",
            "duration_min i probability_percent wybierz z ich opisów.",
            "Pokaż attribution i terms_notice z wysokością; podaj je jako attribution "
            "poleceniu, które ją przyjmie.",
        ),
        errors=(
            "validation_error",
            "missing_dependency",
            "source_unavailable",
            "data_error",
        ),
        example_results=({"depth_mm": 39.16, "method": "POT"},),
        examples=(
            {
                "latitude": 52.23,
                "longitude": 21.01,
                "duration_min": 60.0,
                "probability_percent": 1.0,
            },
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
            "isohyet. Nie do pobierania danych z posterunków (Obserwator) ani opadu "
            "projektowego (`precip hietogram`)."
        ),
        description=(
            "Areal precipitation [mm] from point gauges by `method`: arithmetic, "
            "thiessen (needs polygon areas), idw (point or grid) or isohyet. Not for "
            "downloading gauge data (Obserwator) or design rainfall (`precip "
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
                    "2; n izohiet to n−1 stref, średnia strefy to średnia jej "
                    "granic). Strefa brzegowa zlewni dostaje granicę umowną, "
                    "dla której ta średnia równa się opadowi oszacowanemu dla "
                    "strefy (Chow i in. 1988: 0 i 56 mm dla 5 i 53 mm)."
                ),
                description=(
                    "For isohyet: values of the consecutive isohyets [mm] (at "
                    "least 2; n isohyets make n-1 zones, a zone's mean is the "
                    "mean of its bounds). An edge zone of the watershed takes a "
                    "notional bound that makes that mean the precipitation "
                    "estimated for the zone (Chow et al. 1988: 0 and 56 mm for "
                    "5 and 53 mm)."
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
            ATTRIBUTION,
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
