"""Group ``route``: lumped hydrologic flood routing of a discharge hydrograph.

Every command takes a hydrograph at a regular time step (``times_min`` with
``discharge_m3s``, or ``input_file``), routes it through one element of
:mod:`hydrolog.routing` and returns the outflow with its summary; ``output`` writes the
outflow as a hydrograph table that every ``route`` command reads again (ADR-0007,
ADR-0008). ``route network`` routes the hydrographs of many subcatchments down a river
network, a document ``hydrolog-network/1`` whose reaches and reservoirs take the options
of the other commands (:func:`model_options`), and writes one such table per node into
``output_dir`` (ADR-0010). The operations are in :mod:`hydrolog.operations.route`.

The options that all commands share are public constants (:data:`INFLOW_OPTIONS`,
:data:`INFLOW_ONE_OF`, :data:`RUN_OPTIONS`, :data:`OUTPUT_OPTIONS`) so that a command
declares its model parameters and adds them.
"""

from __future__ import annotations

from hydrolog.catalog.groups._output import FORCE
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"

TIMES_MIN = Option(
    name="times_min",
    type="number_list",
    description_pl=(
        "Czasy rzędnych dopływu [min], ściśle rosnące w stałym kroku (co najmniej "
        "dwie). Długie hydrogramy podawaj w `input_file`. Razem z `discharge_m3s`."
    ),
    description=(
        "Times of the inflow ordinates [min], strictly increasing at a regular step "
        "(at least two). Give long hydrographs in `input_file`. Use with "
        "`discharge_m3s`."
    ),
    unit="min",
)
DISCHARGE_M3S = Option(
    name="discharge_m3s",
    type="number_list",
    description_pl=(
        "Przepływ dopływający w każdej chwili [m3/s], nieujemny; tyle wartości co "
        "`times_min`."
    ),
    description=(
        "Inflow discharge at each time [m3/s], not negative; as many values as "
        "`times_min`."
    ),
    minimum=0,
    unit="m3/s",
)
INPUT_FILE = Option(
    name="input_file",
    type="path",
    path_role="input",
    description_pl=(
        "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON z hydrogramem "
        "dopływu: `output` komendy `route` albo dowolna tabela z kolumną czasu i "
        "przepływu. Kolumny wskazują `time_column` i `value_column`."
    ),
    description=(
        "CSV file (comma or semicolon, header row) or JSON file with the inflow "
        "hydrograph: the `output` of a `route` command, or any table with a time and a "
        "discharge column. The columns are named by `time_column` and `value_column`."
    ),
)
TIME_COLUMN = Option(
    name="time_column",
    type="string",
    description_pl="Nazwa kolumny z czasem [min] w `input_file`; domyślnie `time_min`.",
    description="Name of the time column [min] in `input_file`; default `time_min`.",
)
VALUE_COLUMN = Option(
    name="value_column",
    type="string",
    description_pl=(
        "Nazwa kolumny z przepływem [m3/s] w `input_file`; domyślnie `discharge_m3s`."
    ),
    description=(
        "Name of the discharge column [m3/s] in `input_file`; default `discharge_m3s`."
    ),
)
INITIAL_OUTFLOW_M3S = Option(
    name="initial_outflow_m3s",
    type="number",
    description_pl=(
        "Odpływ w pierwszej rzędnej [m3/s], nieujemny; domyślnie pierwsza rzędna "
        "dopływu (stan ustalony)."
    ),
    description=(
        "Outflow at the first ordinate [m3/s], not negative; default the first inflow "
        "ordinate (steady state)."
    ),
    minimum=0,
    unit="m3/s",
)
EXTEND_MIN = Option(
    name="extend_min",
    type="number",
    description_pl=(
        "Czas dodany po ostatniej rzędnej dopływu, której wartość jest utrzymywana "
        "[min], nieujemny; 0 nie dodaje nic. Domyślnie: do ustabilizowania odpływu "
        "(w granicach 0,1 % szczytu dopływu), co najwyżej dziesięciokrotność czasu "
        "trwania dopływu."
    ),
    description=(
        "Time added after the last inflow ordinate, whose value is held [min], not "
        "negative; 0 adds nothing. Default: until the outflow has settled (within "
        "0.1 % of the inflow peak), at most ten times the inflow duration."
    ),
    minimum=0,
    unit="min",
)
OUTPUT = Option(
    name="output",
    type="path",
    path_role="output",
    description_pl=(
        "Plik CSV z hydrogramem odpływu (`time_min`, `discharge_m3s`), który czyta "
        "każda komenda `route`; bez niego szereg jest w wyniku. Istniejący plik jest "
        "zastępowany tylko z `force`; nie może być `input_file`."
    ),
    description=(
        "CSV file to write with the outflow hydrograph (`time_min`, `discharge_m3s`), "
        "which every `route` command reads; without it the series is in the result. "
        "An existing file is replaced only with `force`; it must not be `input_file`."
    ),
)
CHECK = Option(
    name="check",
    type="boolean",
    description_pl=(
        "Z `output`: plan bez skutków, zwróć plik docelowy i jego akcję (`write`, "
        "`replace` lub `conflict`), niczego nie zapisując. Bez `output` nie ma czego "
        "planować i wynik jest liczony jak zwykle."
    ),
    description=(
        "With `output`: plan without effects, return the target file and its action "
        "(`write`, `replace` or `conflict`) and write nothing. Without `output` there "
        "is nothing to plan and the result is computed as usual."
    ),
    default=False,
)

INFLOW_OPTIONS: tuple[Option, ...] = (
    TIMES_MIN,
    DISCHARGE_M3S,
    INPUT_FILE,
    TIME_COLUMN,
    VALUE_COLUMN,
)
"""The inflow hydrograph: inline lists, or a file with its two columns."""

INFLOW_ONE_OF: tuple[tuple[str, ...], ...] = (
    ("times_min", "discharge_m3s"),
    ("input_file",),
)
"""Exactly one of: the two inline lists, or ``input_file``."""

RUN_OPTIONS: tuple[Option, ...] = (INITIAL_OUTFLOW_M3S, EXTEND_MIN)
"""The initial condition and the extension of the time axis (ADR-0008)."""

OUTPUT_OPTIONS: tuple[Option, ...] = (OUTPUT, FORCE, CHECK)
"""The optional outflow file and its ``force`` and ``check``."""

NETWORK = Option(
    name="network",
    type="object",
    description_pl=(
        "Sieć w treści, jako obiekt JSON `hydrolog-network/1`: `schema`, `name` i "
        "`nodes`, lista węzłów z `id` (nazwa pliku `<id>.csv`; nie con, prn, aux, nul, "
        "com1-9, lpt1-9), `type` (subcatchment, reach, reservoir, junction, outlet) i "
        "`from` (id węzłów powyżej). Zlewnia (subcatchment) ma `times_min` z "
        "`discharge_m3s` albo `value_column` z `inflows_file` (domyślnie jej `id`); "
        "odcinek (reach) ma `method` (lag, muskingum, muskingum-cunge, cascade, "
        "level-pool) i opcje `route <method>`, zbiornik (reservoir) opcje `route "
        "level-pool`, oba także `initial_outflow_m3s` i `extend_min`; złącze "
        "(junction) dodaje dopływające węzły; jest dokładnie jeden outlet. Sieć w "
        "treści nie wskazuje plików: `rating_file` wymaga `network_file`."
    ),
    description=(
        "The network inline, as a JSON object `hydrolog-network/1`: `schema`, `name` "
        "and `nodes`, a list of nodes with `id` (names the file `<id>.csv`; not con, "
        "prn, aux, nul, com1-9, lpt1-9), `type` (subcatchment, reach, reservoir, "
        "junction, outlet) and `from` (the ids of the nodes upstream). A "
        "subcatchment has "
        "`times_min` with `discharge_m3s`, or a `value_column` of `inflows_file` "
        "(default its `id`); a reach has `method` (lag, muskingum, muskingum-cunge, "
        "cascade, level-pool) and the options of `route <method>`, a reservoir those "
        "of `route level-pool`, both also `initial_outflow_m3s` and `extend_min`; a "
        "junction adds the nodes that flow into it; there is exactly one outlet. An "
        "inline network names no files: a `rating_file` needs `network_file`."
    ),
)
NETWORK_FILE = Option(
    name="network_file",
    type="path",
    path_role="input",
    description_pl=(
        "Plik JSON z siecią `hydrolog-network/1`, zamiast `network`. `rating_file` "
        "węzła jest podany względem katalogu tego pliku i musi w nim leżeć."
    ),
    description=(
        "JSON file with the network `hydrolog-network/1`, instead of `network`. The "
        "`rating_file` of a node is relative to the directory of this file and must "
        "lie inside it."
    ),
)
INFLOWS_FILE = Option(
    name="inflows_file",
    type="path",
    path_role="input",
    description_pl=(
        "Plik CSV albo JSON z przepływami zlewni, które nie mają ich w treści: "
        "kolumna czasu (`time_column`) i kolumna [m3/s] każdej zlewni, nazwana jej "
        "`value_column` albo, bez niej, jej `id`."
    ),
    description=(
        "CSV or JSON file with the discharges of the subcatchments that have none "
        "inline: the time column (`time_column`) and a column [m3/s] for each "
        "subcatchment, named by its `value_column` or else by its `id`."
    ),
)
NETWORK_TIME_COLUMN = Option(
    name="time_column",
    type="string",
    description_pl=(
        "Nazwa kolumny z czasem [min] w `inflows_file`; domyślnie `time_min`."
    ),
    description="Name of the time column [min] in `inflows_file`; default `time_min`.",
)
NODES = Option(
    name="nodes",
    type="string_list",
    description_pl=(
        "Id węzłów, których hydrogramy są zwracane: zapisywane jako `<id>.csv` w "
        "`output_dir` albo, bez niego, umieszczane w wyniku; domyślnie wszystkie."
    ),
    description=(
        "Ids of the nodes whose hydrographs are returned: written as `<id>.csv` into "
        "`output_dir` or, without it, put in the result; default all of them."
    ),
)
OUTPUT_DIR = Option(
    name="output_dir",
    type="path",
    path_role="output",
    description_pl=(
        "Katalog na hydrogram każdego wybranego węzła, `<id>.csv` (`time_min`, "
        "`discharge_m3s`), który czyta każda komenda `route`; tworzony, jeśli go "
        "brak. Bez niego hydrogramy są w wyniku. Istniejący plik jest zastępowany "
        "tylko z `force`; żaden plik nie może być plikiem wejściowym, a katalog nie "
        "może leżeć w magazynie innego narzędzia Nogat."
    ),
    description=(
        "Directory for the hydrograph of each selected node, `<id>.csv` (`time_min`, "
        "`discharge_m3s`), which every `route` command reads; created if missing. "
        "Without it the hydrographs are in the result. An existing file is replaced "
        "only with `force`; no file may be an input file and the directory must not "
        "lie in the store of another Nogat tool."
    ),
)
NETWORK_FORCE = Option(
    name="force",
    type="boolean",
    description_pl=(
        "Zastąp pliki `<id>.csv`, które istnieją w `output_dir`; bez tej opcji nic "
        "nie jest nadpisywane."
    ),
    description=(
        "Replace the `<id>.csv` files that exist in `output_dir`; without it nothing "
        "is overwritten."
    ),
    default=False,
)
NETWORK_CHECK = Option(
    name="check",
    type="boolean",
    description_pl=(
        "Z `output_dir`: plan bez skutków, zwróć każdy plik z jego działaniem "
        "(`write`, `replace` lub `conflict`), niczego nie zapisując. Bez `output_dir` "
        "nie ma czego planować i wynik jest liczony jak zwykle."
    ),
    description=(
        "With `output_dir`: plan without effects, return each file with its action "
        "(`write`, `replace` or `conflict`) and write nothing. Without `output_dir` "
        "there is nothing to plan and the result is computed as usual."
    ),
    default=False,
)

MODEL_METHODS: tuple[str, ...] = (
    "lag",
    "muskingum",
    "muskingum-cunge",
    "cascade",
    "level-pool",
)
"""The routing methods, ``route <method>``: the values of ``method`` of a reach."""

_ERRORS = (
    "validation_error",
    "not_found",
    "data_error",
    "forbidden",
    "io_error",
    "conflict",
)

COMMANDS: tuple[Command, ...] = (
    Command(
        name="route lag",
        operation_id="hydrolog_route_lag",
        summary_pl=(
            "Przeprowadź hydrogram metodą lagu: odpływ to dopływ przesunięty w czasie."
        ),
        summary=(
            "Route a hydrograph by lag: the outflow is the inflow, shifted in time."
        ),
        description_pl=(
            "Metoda lagu (jak w HEC-HMS): odpływ to dopływ po `lag_min`, bez "
            "tłumienia; dla krótkich odcinków o znanym czasie przepływu. Dopływ to "
            "hydrogram w stałym kroku; oś czasu jest wydłużana, aż odpływ się "
            "ustabilizuje. Zwraca szczyty, objętości, bilans i szereg."
        ),
        description=(
            "Lag routing (as in HEC-HMS): the outflow is the inflow `lag_min` later, "
            "without attenuation; for short reaches with a known travel time. The "
            "inflow is a regular-step hydrograph; the time axis is extended until the "
            "outflow has settled. Returns peaks, volumes, balance and the series."
        ),
        function="hydrolog.operations.route_lag",
        options=(
            Option(
                name="lag_min",
                type="number",
                description_pl=(
                    "Lag [min]: o ile później odpływ powtarza dopływ; > 0. Lag, który "
                    "nie jest całkowitą liczbą kroków, jest interpolowany "
                    "(`lag_interpolated`)."
                ),
                description=(
                    "Lag [min]: how much later the outflow repeats the inflow; > 0. A "
                    "lag that is not a whole number of time steps is interpolated "
                    "(`lag_interpolated`)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="min",
            ),
            *INFLOW_OPTIONS,
            *RUN_OPTIONS,
            *OUTPUT_OPTIONS,
        ),
        one_of=INFLOW_ONE_OF,
        examples=(
            {
                "lag_min": 30.0,
                "input_file": f"{_FIXTURES}/flood_inflow.csv",
                "output": "outflow.csv",
            },
            {
                "lag_min": 25.0,
                "times_min": [0, 10, 20, 30, 40, 50, 60, 70],
                "discharge_m3s": [0, 10, 40, 90, 60, 30, 10, 0],
            },
        ),
        result_schema="hydrolog-route-lag/1",
        cardinality="bounded",
        rules=(
            "Give the hydrograph inline or as `input_file`, at a regular step.",
            "Add `output` to write the outflow as a CSV that every `route` command "
            "reads.",
            "Read `notices`: `tail_extended` is the time added after the inflow.",
        ),
        rules_pl=(
            "Podaj hydrogram w treści albo jako `input_file`, w stałym kroku.",
            "Dodaj `output`, by zapisać odpływ jako CSV czytany przez każdą komendę "
            "`route`.",
            "Czytaj `notices`: `tail_extended` to czas dodany po dopływie.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "model": "lag",
                "parameters": {"lag_min": 30.0, "lag_steps": 3.0},
                "timestep_min": 10.0,
                "extension_min": 10.0,
                "outflow_peak_m3s": 40.0,
                "outflow_time_to_peak_min": 90.0,
                "peak_delay_min": 30.0,
            },
            {
                "model": "lag",
                "parameters": {"lag_min": 25.0, "lag_steps": 2.5},
                "extension_min": 30.0,
                "inflow_peak_m3s": 90.0,
                "outflow_peak_m3s": 75.0,
                "outflow_time_to_peak_min": 60.0,
                "peak_attenuation_pct": 16.6667,
                "outflow_m3s": [0.0, 0.0, 0.0, 5.0, 25.0, 65.0, 75.0, 45.0, 20.0],
            },
        ),
    ),
    Command(
        name="route muskingum",
        operation_id="hydrolog_route_muskingum",
        summary_pl=(
            "Przeprowadź hydrogram metodą Muskingum: retencja K[XI + (1-X)O] na "
            "pododcinkach."
        ),
        summary=(
            "Route a hydrograph by Muskingum: storage K[XI + (1-X)O] over sub-reaches."
        ),
        description_pl=(
            "Metoda Muskingum (jak w HEC-HMS): S = K[X I + (1-X) O] na `subreaches` "
            "równych pododcinkach o K/N. Domyślnie N = K/krok; wagi muszą być "
            "nieujemne: |2KX| <= krok <= 2K(1-X), inaczej krok jest dzielony "
            "(`substeps_added`). Zwraca szczyty, objętości, bilans i szereg."
        ),
        description=(
            "Muskingum routing (as in HEC-HMS): S = K[X I + (1-X) O] over `subreaches` "
            "equal sub-reaches of K/N. Default N = K/step; the weights must stay "
            "non-negative, |2KX| <= step <= 2K(1-X), else the step is divided "
            "(`substeps_added`). Returns peaks, volumes, balance and the series."
        ),
        function="hydrolog.operations.route_muskingum",
        options=(
            Option(
                name="k_min",
                type="number",
                description_pl=(
                    "Czas przepływu fali K na odcinku [min]; > 0 (w przybliżeniu "
                    "długość odcinka przez prędkość fali powodziowej)."
                ),
                description=(
                    "Travel time K of the reach [min]; > 0 (about the reach length "
                    "divided by the flood-wave celerity)."
                ),
                required=True,
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="x",
                type="number",
                description_pl=(
                    "Współczynnik wagowy X, od 0 do 0,5: 0 to zbiornik liniowy "
                    "(największe tłumienie), 0,5 przenosi falę bez tłumienia."
                ),
                description=(
                    "Weighting factor X, 0 to 0.5: 0 is a linear reservoir (maximum "
                    "attenuation), 0.5 passes the wave on without attenuation."
                ),
                required=True,
                minimum=0,
                maximum=0.5,
            ),
            Option(
                name="subreaches",
                type="integer",
                description_pl=(
                    "Liczba równych pododcinków o K/N, co najmniej 1; domyślnie "
                    "K/krok zaokrąglone. Wagi muszą pozostać nieujemne: "
                    "2KX/krok <= N <= 2K(1-X)/krok."
                ),
                description=(
                    "Number of equal sub-reaches of K/N, at least 1; default K/step "
                    "rounded. Each keeps the weights non-negative for "
                    "2KX/step <= N <= 2K(1-X)/step."
                ),
                minimum=1,
            ),
            *INFLOW_OPTIONS,
            *RUN_OPTIONS,
            *OUTPUT_OPTIONS,
        ),
        one_of=INFLOW_ONE_OF,
        examples=(
            {
                "k_min": 40.0,
                "x": 0.2,
                "input_file": f"{_FIXTURES}/flood_inflow.csv",
                "output": "outflow.csv",
            },
            {
                # the University of Iowa example: K = 20 h, X = 0.25, step 12 h
                "k_min": 1200.0,
                "x": 0.25,
                "subreaches": 1,
                "times_min": [
                    720,
                    1440,
                    2160,
                    2880,
                    3600,
                    4320,
                    5040,
                    5760,
                    6480,
                    7200,
                ],
                "discharge_m3s": [100, 300, 680, 500, 400, 310, 230, 180, 100, 50],
                "extend_min": 0,
            },
        ),
        result_schema="hydrolog-route-muskingum/1",
        cardinality="bounded",
        rules=(
            "Give the hydrograph inline or as `input_file`, at a regular step.",
            "`x` is 0 (linear reservoir) to 0.5 (no attenuation); more `subreaches` "
            "attenuate less.",
            "A `subreaches` outside the window is `unstable_timestep`; the error gives "
            "the window.",
        ),
        rules_pl=(
            "Podaj hydrogram w treści albo jako `input_file`, w stałym kroku.",
            "`x` od 0 (zbiornik liniowy) do 0,5 (bez tłumienia); więcej `subreaches` "
            "tłumi mniej.",
            "`subreaches` poza oknem to `unstable_timestep`; błąd podaje okno.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "model": "muskingum",
                "parameters": {"k_min": 40.0, "x": 0.2, "subreaches": 4},
                "timestep_min": 10.0,
                "extension_min": 30.0,
                "outflow_peak_m3s": 36.437015,
                "outflow_time_to_peak_min": 100.0,
                "peak_delay_min": 40.0,
            },
            {
                "model": "muskingum",
                "parameters": {
                    "k_min": 1200.0,
                    "x": 0.25,
                    "subreaches": 1,
                    "c_current": 0.047619,
                    "c_previous": 0.52381,
                    "c_outflow": 0.428571,
                },
                "outflow_peak_m3s": 487.241427,
                "outflow_time_to_peak_min": 3600.0,
                "peak_attenuation_pct": 28.346849,
                "outflow_m3s": [
                    100.0,
                    109.52381,
                    236.462585,
                    481.341108,
                    487.241427,
                    433.103469,
                    358.949106,
                    282.88295,
                    220.283169,
                    149.168977,
                ],
            },
        ),
    ),
    Command(
        name="route muskingum-cunge",
        operation_id="hydrolog_route_muskingum_cunge",
        summary_pl=(
            "Przeprowadź hydrogram metodą Muskingum-Cunge: K i X z prędkości fali, "
            "szerokości i spadku odcinka."
        ),
        summary=(
            "Route a hydrograph by Muskingum-Cunge: K and X from the celerity, width "
            "and slope of the reach."
        ),
        description_pl=(
            "Muskingum-Cunge o stałych współczynnikach (NRCS NEH-630 rozdz. 17): "
            "K = dx/c, X = (1 - Q/(T S0 c dx))/2 na ceil(L/dx_c) krokach, X może być "
            "ujemne. Q to szczyt dopływu, chyba że podano `reference_discharge_m3s`."
        ),
        description=(
            "Muskingum-Cunge with constant coefficients (NRCS NEH-630 ch. 17): "
            "K = dx/c, X = (1 - Q/(T S0 c dx))/2 over ceil(L/dx_c) steps, X may be "
            "negative. Q is the inflow peak unless `reference_discharge_m3s` is given."
        ),
        function="hydrolog.operations.route_muskingum_cunge",
        options=(
            Option(
                name="length_km",
                type="number",
                description_pl="Długość odcinka [km]; > 0.",
                description="Length of the reach [km]; > 0.",
                required=True,
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="slope_m_per_m",
                type="number",
                description_pl="Spadek dna (spadek tarcia) odcinka [m/m]; > 0.",
                description="Friction (bed) slope of the reach [m/m]; > 0.",
                required=True,
                exclusive_minimum=0,
                unit="m/m",
            ),
            Option(
                name="manning_n",
                type="number",
                description_pl=(
                    "Współczynnik szorstkości Manninga [s/m^(1/3)]; > 0. Razem z "
                    "`bottom_width_m` opisuje przekrój, zamiast `celerity_m_per_s` i "
                    "`top_width_m`."
                ),
                description=(
                    "Manning's roughness [s/m^(1/3)]; > 0. With `bottom_width_m` it "
                    "describes the section, instead of `celerity_m_per_s` and "
                    "`top_width_m`."
                ),
                exclusive_minimum=0,
                unit="s/m^(1/3)",
            ),
            Option(
                name="bottom_width_m",
                type="number",
                description_pl=(
                    "Szerokość dna przekroju [m]; >= 0 (0: trójkąt). Razem z "
                    "`manning_n`."
                ),
                description=(
                    "Bottom width of the section [m]; >= 0 (0: a triangle). With "
                    "`manning_n`."
                ),
                minimum=0,
                unit="m",
            ),
            Option(
                name="side_slope_m_per_m",
                type="number",
                description_pl=(
                    "Nachylenie skarp [m/m]: metry w poziomie na metr w pionie; "
                    ">= 0 (0: prostokąt); domyślnie 0. Część przekroju, pomijane z "
                    "`celerity_m_per_s`."
                ),
                description=(
                    "Bank slope [m/m]: horizontal metres per vertical metre; >= 0 "
                    "(0: a rectangle); default 0. Part of the section, ignored with "
                    "`celerity_m_per_s`."
                ),
                minimum=0,
                unit="m/m",
            ),
            Option(
                name="celerity_m_per_s",
                type="number",
                description_pl=(
                    "Prędkość fali powodziowej (celerity) przy przepływie "
                    "odniesienia [m/s]; > 0. Razem z `top_width_m`, zamiast przekroju."
                ),
                description=(
                    "Flood-wave celerity at the reference discharge [m/s]; > 0. With "
                    "`top_width_m`, instead of the section."
                ),
                exclusive_minimum=0,
                unit="m/s",
            ),
            Option(
                name="top_width_m",
                type="number",
                description_pl=(
                    "Szerokość zwierciadła wody przy przepływie odniesienia [m]; "
                    "> 0. Razem z `celerity_m_per_s`."
                ),
                description=(
                    "Width of the water surface at the reference discharge [m]; > 0. "
                    "With `celerity_m_per_s`."
                ),
                exclusive_minimum=0,
                unit="m",
            ),
            Option(
                name="reference_discharge_m3s",
                type="number",
                description_pl=(
                    "Przepływ odniesienia [m3/s], przy którym liczone są prędkość "
                    "fali i szerokość; > 0; domyślnie szczyt dopływu."
                ),
                description=(
                    "Reference discharge [m3/s] at which the celerity and the width "
                    "are taken; > 0; default the inflow peak."
                ),
                exclusive_minimum=0,
                unit="m3/s",
            ),
            *INFLOW_OPTIONS,
            *RUN_OPTIONS,
            *OUTPUT_OPTIONS,
        ),
        one_of=INFLOW_ONE_OF,
        examples=(
            {
                "length_km": 8.0,
                "slope_m_per_m": 0.001,
                "manning_n": 0.035,
                "bottom_width_m": 12.0,
                "side_slope_m_per_m": 2.0,
                "input_file": f"{_FIXTURES}/flood_inflow.csv",
                "output": "outflow.csv",
            },
            {
                "length_km": 15.0,
                "slope_m_per_m": 0.0008,
                "celerity_m_per_s": 1.0,
                "top_width_m": 30.0,
                "times_min": [
                    0,
                    15,
                    30,
                    45,
                    60,
                    75,
                    90,
                    105,
                    120,
                    135,
                    150,
                    165,
                    180,
                    195,
                    210,
                    225,
                    240,
                    255,
                    270,
                    285,
                    300,
                    315,
                    330,
                    345,
                    360,
                ],
                "discharge_m3s": [
                    4.0,
                    4.61,
                    6.41,
                    9.27,
                    13.0,
                    17.34,
                    22.0,
                    26.66,
                    31.0,
                    34.73,
                    37.59,
                    39.39,
                    40.0,
                    39.39,
                    37.59,
                    34.73,
                    31.0,
                    26.66,
                    22.0,
                    17.34,
                    13.0,
                    9.27,
                    6.41,
                    4.61,
                    4.0,
                ],
            },
        ),
        result_schema="hydrolog-route-muskingum-cunge/1",
        cardinality="bounded",
        rules=(
            "Give one group: `manning_n` with `bottom_width_m`, or `celerity_m_per_s` "
            "with `top_width_m`.",
            "Read `notices`: `subreaches_adjusted`, `substeps_added`, "
            "`timestep_refined`, `accuracy_limit`.",
        ),
        rules_pl=(
            "Podaj jedną grupę: `manning_n` z `bottom_width_m` albo "
            "`celerity_m_per_s` z `top_width_m`.",
            "Czytaj `notices`: `subreaches_adjusted`, `substeps_added`, "
            "`timestep_refined`, `accuracy_limit`.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "model": "muskingum-cunge",
                "parameters": {
                    "reference_discharge_m3s": 40.0,
                    "celerity_m_per_s": 1.74409,
                    "top_width_m": 20.188973,
                    "k_min": 76.448665,
                    "x": -0.209998,
                    "subreaches": 10,
                    "substeps": 2,
                },
                "extension_min": 80.0,
                "outflow_peak_m3s": 30.863841,
                "outflow_time_to_peak_min": 140.0,
                "peak_delay_min": 80.0,
            },
            {
                "model": "muskingum-cunge",
                "parameters": {
                    "celerity_m_per_s": 1.0,
                    "top_width_m": 30.0,
                    "k_min": 250.0,
                    "x": -0.166667,
                    "subreaches": 12,
                    "substeps": 1,
                },
                "extension_min": 510.0,
                "outflow_peak_m3s": 28.487838,
                "outflow_time_to_peak_min": 420.0,
                "peak_attenuation_pct": 28.780406,
                "peak_delay_min": 240.0,
                "outflow_m3s": [
                    4.0,
                    4.000002,
                    4.000025,
                    4.00019,
                    4.000964,
                    4.00374,
                    4.011883,
                    4.032238,
                ],
            },
        ),
    ),
    Command(
        name="route cascade",
        operation_id="hydrolog_route_cascade",
        summary_pl=(
            "Przeprowadź hydrogram przez kaskadę n zbiorników liniowych (Nash, "
            "Kalinin-Miljukow)."
        ),
        summary=(
            "Route a hydrograph through a cascade of n linear reservoirs (Nash, "
            "Kalinin-Milyukov)."
        ),
        description_pl=(
            "Kaskada n równych zbiorników liniowych S = K O. Odpływ jest dokładną "
            "odpowiedzią na dopływ liniowy między rzędnymi, dla każdego kroku, bez "
            "podkroków; n nie musi być całkowite. Skala czasu: `k_min` albo "
            "`length_km` z `celerity_m_per_s` (K = L/(n c)). Zwraca szczyty, "
            "objętości, bilans i szereg."
        ),
        description=(
            "Cascade of n equal linear reservoirs S = K O. The outflow is the exact "
            "response to the inflow, linear between ordinates, for any time step and "
            "without sub-steps; n need not be whole. Time scale: `k_min`, or "
            "`length_km` with `celerity_m_per_s` (K = L/(n c)). Returns peaks, "
            "volumes, balance and the series."
        ),
        function="hydrolog.operations.route_cascade",
        options=(
            Option(
                name="n",
                type="number",
                description_pl=(
                    "Liczba zbiorników w szeregu; > 0, nie musi być całkowita. n = 1 "
                    "to jeden zbiornik (największe tłumienie), duże n to samo "
                    "opóźnienie fali."
                ),
                description=(
                    "Number of reservoirs in series; > 0, need not be whole. n = 1 "
                    "is one reservoir (the most attenuation), a large n is a pure "
                    "delay of the wave."
                ),
                required=True,
                exclusive_minimum=0,
            ),
            Option(
                name="k_min",
                type="number",
                description_pl=(
                    "Stała retencji K jednego zbiornika [min]; > 0; odcinek opóźnia "
                    "falę o n K. Zamiast `length_km` i `celerity_m_per_s`."
                ),
                description=(
                    "Storage constant K of one reservoir [min]; > 0; the reach delays "
                    "the wave by n K. Instead of `length_km` and `celerity_m_per_s`."
                ),
                exclusive_minimum=0,
                unit="min",
            ),
            Option(
                name="length_km",
                type="number",
                description_pl=(
                    "Długość odcinka [km]; > 0. Razem z `celerity_m_per_s`, zamiast "
                    "`k_min`: K = L/(n c)."
                ),
                description=(
                    "Length of the reach [km]; > 0. With `celerity_m_per_s`, instead "
                    "of `k_min`: K = L/(n c)."
                ),
                exclusive_minimum=0,
                unit="km",
            ),
            Option(
                name="celerity_m_per_s",
                type="number",
                description_pl=(
                    "Prędkość fali powodziowej (celerity) [m/s]; > 0. Razem z "
                    "`length_km`."
                ),
                description=("Flood-wave celerity [m/s]; > 0. With `length_km`."),
                exclusive_minimum=0,
                unit="m/s",
            ),
            *INFLOW_OPTIONS,
            *RUN_OPTIONS,
            *OUTPUT_OPTIONS,
        ),
        one_of=INFLOW_ONE_OF,
        examples=(
            {
                "n": 3.0,
                "k_min": 20.0,
                "input_file": f"{_FIXTURES}/flood_inflow.csv",
                "output": "outflow.csv",
            },
            {
                # 18 km at 1.5 m/s is 200 min of travel: 2.5 reservoirs of 80 min
                "n": 2.5,
                "length_km": 18.0,
                "celerity_m_per_s": 1.5,
                "times_min": [0, 60, 120, 180, 240, 300, 360],
                "discharge_m3s": [5.0, 20.0, 60.0, 35.0, 15.0, 8.0, 5.0],
            },
        ),
        result_schema="hydrolog-route-cascade/1",
        cardinality="bounded",
        rules=(
            "Give `n` and one time scale: `k_min`, or `length_km` with "
            "`celerity_m_per_s`.",
            "No time step is too long: nothing is divided or refused.",
            "Read `notices`: `tail_extended` is the time added after the inflow.",
        ),
        rules_pl=(
            "Podaj `n` i jedną skalę czasu: `k_min` albo `length_km` z "
            "`celerity_m_per_s`.",
            "Żaden krok nie jest za długi: nic nie jest dzielone ani odrzucane.",
            "Czytaj `notices`: `tail_extended` to czas dodany po dopływie.",
        ),
        errors=_ERRORS,
        example_results=(
            {
                "model": "cascade",
                "parameters": {
                    "n": 3.0,
                    "k_min": 20.0,
                    "lag_min": 60.0,
                    "timestep_over_k": 0.5,
                },
                "timestep_min": 10.0,
                "extension_min": 90.0,
                "outflow_peak_m3s": 29.15152,
                "outflow_time_to_peak_min": 120.0,
                "peak_delay_min": 60.0,
            },
            {
                "model": "cascade",
                "parameters": {
                    "n": 2.5,
                    "k_min": 80.0,
                    "lag_min": 200.0,
                    "timestep_over_k": 0.75,
                    "length_km": 18.0,
                    "celerity_m_per_s": 1.5,
                },
                "extension_min": 660.0,
                "outflow_peak_m3s": 26.544046,
                "outflow_time_to_peak_min": 300.0,
                "peak_attenuation_pct": 55.759923,
                "peak_delay_min": 180.0,
                "outflow_m3s": [
                    5.0,
                    5.419436,
                    8.949596,
                    18.041115,
                    25.403668,
                    26.544046,
                    23.205285,
                    18.328584,
                ],
            },
        ),
    ),
    Command(
        name="route level-pool",
        operation_id="hydrolog_route_level_pool",
        summary_pl=(
            "Przeprowadź hydrogram przez zbiornik z tabelą pojemność-odpływ (level "
            "pool)."
        ),
        summary=(
            "Route a hydrograph through a reservoir with a storage-outflow table "
            "(level pool)."
        ),
        description_pl=(
            "Metoda zbiornika (zmodyfikowana metoda Pulsa, NEH-630 rozdz. 17) dla "
            "zbiornika lub odcinka z tabelą pojemność-odpływ: w treści (`storage_m3`, "
            "`outflow_m3s`, `stage_m`) albo `rating_file`; `subreaches` to "
            "pododcinki. "
            "Krok dłuższy niż 2 min dS/dO jest dzielony. Zwraca szczyty, objętości, "
            "bilans i szereg."
        ),
        description=(
            "Level-pool routing (modified Puls, NEH-630 ch. 17) through a reservoir or "
            "reach given by a storage-outflow table, inline (`storage_m3`, "
            "`outflow_m3s`, `stage_m`) or `rating_file`; `subreaches` sets "
            "sub-reaches. "
            "A step above twice the shortest dS/dO is divided. Returns peaks, volumes, "
            "balance and the series."
        ),
        function="hydrolog.operations.route_level_pool",
        options=(
            Option(
                name="storage_m3",
                type="number_list",
                description_pl=(
                    "Pojemność (woda w zbiorniku) w kolejnych wierszach tabeli [m3], "
                    "niemalejąca, nieujemna; od stanu pustego. Razem z `outflow_m3s`, "
                    "zamiast `rating_file`."
                ),
                description=(
                    "Storage of each row of the table [m3], not decreasing, not "
                    "negative; from the empty state. With `outflow_m3s`, instead of "
                    "`rating_file`."
                ),
                minimum=0,
                unit="m3",
            ),
            Option(
                name="outflow_m3s",
                type="number_list",
                description_pl=(
                    "Odpływ w kolejnych wierszach tabeli [m3/s], niemalejący, "
                    "nieujemny; 0 poniżej korony. Tyle wartości co `storage_m3`."
                ),
                description=(
                    "Outflow of each row of the table [m3/s], not decreasing, not "
                    "negative; 0 below a crest. As many values as `storage_m3`."
                ),
                minimum=0,
                unit="m3/s",
            ),
            Option(
                name="stage_m",
                type="number_list",
                description_pl=(
                    "Rzędna wody w kolejnych wierszach tabeli [m], niemalejąca "
                    "(rzędna albo głębokość); tylko z tabelą w treści, podawana w "
                    "szczycie. Tyle wartości co `storage_m3`."
                ),
                description=(
                    "Water level of each row of the table [m], not decreasing (an "
                    "elevation or a depth); only with the inline table, reported at "
                    "the peak. As many values as `storage_m3`."
                ),
                unit="m",
            ),
            Option(
                name="rating_file",
                type="path",
                path_role="input",
                description_pl=(
                    "Plik CSV albo JSON z tabelą pojemność-odpływ: kolumny "
                    "`storage_m3`, `outflow_m3s` i opcjonalnie `stage_m`, wiersze od "
                    "stanu pustego do pełnego. Zamiast tabeli w treści."
                ),
                description=(
                    "CSV or JSON file with the storage-outflow table: columns "
                    "`storage_m3`, `outflow_m3s` and optionally `stage_m`, rows from "
                    "the empty to the full state. Instead of the inline table."
                ),
            ),
            Option(
                name="subreaches",
                type="integer",
                description_pl=(
                    "Liczba pododcinków w szeregu, co najmniej 1; każdy trzyma S/N "
                    "pojemności przy tym samym odpływie, więcej pododcinków tłumi "
                    "mniej. 1 to zbiornik."
                ),
                description=(
                    "Number of sub-reaches in series, at least 1; each holds S/N of "
                    "the storage for the same outflow, so more of them attenuate "
                    "less. 1 is a reservoir."
                ),
                default=1,
                minimum=1,
            ),
            *INFLOW_OPTIONS,
            *RUN_OPTIONS,
            *OUTPUT_OPTIONS,
        ),
        one_of=INFLOW_ONE_OF,
        examples=(
            {
                "rating_file": f"{_FIXTURES}/pond_rating.csv",
                "input_file": f"{_FIXTURES}/flood_inflow.csv",
                "output": "outflow.csv",
            },
            {
                "storage_m3": [0, 30000, 90000, 180000],
                "outflow_m3s": [0, 10, 40, 100],
                "stage_m": [0, 0.8, 1.9, 3.4],
                "times_min": [0, 10, 20, 30, 40, 50, 60, 70],
                "discharge_m3s": [0, 10, 40, 90, 60, 30, 10, 0],
            },
        ),
        result_schema="hydrolog-route-level-pool/1",
        cardinality="bounded",
        rules=(
            "Give the table inline or as `rating_file`, rows rising from empty to "
            "full.",
            "A flood beyond the table is `table_exceeded`, never an extrapolation.",
            "Read `notices`: `timestep_refined` is a divided time step.",
        ),
        rules_pl=(
            "Podaj tabelę w treści albo jako `rating_file`, wiersze rosnące od stanu "
            "pustego do pełnego.",
            "Wezbranie poza tabelą to `table_exceeded`, nigdy ekstrapolacja.",
            "Czytaj `notices`: `timestep_refined` to podzielony krok czasu.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
            "io_error",
            "conflict",
        ),
        example_results=(
            {
                "model": "level-pool",
                "parameters": {
                    "subreaches": 1,
                    "substeps": 1,
                    "timestep_limit_min": 175.862069,
                    "storage_peak_m3": 211556.627674,
                    "storage_peak_time_min": 120.0,
                    "stage_peak_m": 102.64507,
                    "stage_peak_time_min": 120.0,
                },
                "timestep_min": 10.0,
                "extension_min": 770.0,
                "inflow_peak_m3s": 40.0,
                "outflow_peak_m3s": 18.935635,
                "outflow_time_to_peak_min": 120.0,
                "peak_attenuation_pct": 52.660912,
                "peak_delay_min": 60.0,
            },
            {
                "model": "level-pool",
                "parameters": {
                    "subreaches": 1,
                    "substeps": 1,
                    "timestep_limit_min": 50.0,
                    "storage_peak_m3": 82961.628358,
                    "storage_peak_time_min": 50.0,
                    "stage_peak_m": 1.770963,
                    "stage_peak_time_min": 50.0,
                },
                "extension_min": 300.0,
                "inflow_peak_m3s": 90.0,
                "outflow_peak_m3s": 36.480814,
                "outflow_time_to_peak_min": 50.0,
                "peak_attenuation_pct": 59.465762,
                "peak_delay_min": 20.0,
                "outflow_m3s": [
                    0.0,
                    0.909091,
                    5.289256,
                    18.817822,
                    33.474043,
                    36.480814,
                    32.181471,
                    25.090653,
                ],
            },
        ),
    ),
    Command(
        name="route network",
        operation_id="hydrolog_route_network",
        summary_pl=(
            "Przeprowadź hydrogramy przez sieć rzeczną: zlewnie, odcinki, zbiorniki, "
            "złącza."
        ),
        summary=(
            "Route hydrographs down a river network: catchments, reaches, reservoirs, "
            "junctions."
        ),
        description_pl=(
            "Przeprowadza przepływy zlewni w dół sieci odcinków (lag, Muskingum, "
            "Muskingum-Cunge, kaskada, zbiornik), zbiorników i złączy do jednego "
            "wylotu. Sieć to dokument `hydrolog-network/1`; przepływy są w treści lub "
            "w `inflows_file`. Jeden krok czasu dla wszystkich węzłów. Zwraca szczyty "
            "i objętości każdego węzła."
        ),
        description=(
            "Routes the discharges of subcatchments down a network of reaches (lag, "
            "Muskingum, Muskingum-Cunge, cascade, level pool), reservoirs and "
            "junctions to one outlet. The network is a document `hydrolog-network/1`; "
            "discharges are inline or in `inflows_file`. Returns peaks and volumes per "
            "node."
        ),
        function="hydrolog.operations.route_network",
        options=(
            NETWORK,
            NETWORK_FILE,
            INFLOWS_FILE,
            NETWORK_TIME_COLUMN,
            NODES,
            OUTPUT_DIR,
            NETWORK_FORCE,
            NETWORK_CHECK,
        ),
        one_of=(("network",), ("network_file",)),
        examples=(
            {
                "network_file": f"{_FIXTURES}/network_flood.json",
                "inflows_file": f"{_FIXTURES}/network_inflows.csv",
                "output_dir": "network_out",
            },
            {
                "network": {
                    "schema": "hydrolog-network/1",
                    "nodes": [
                        {
                            "id": "A",
                            "type": "subcatchment",
                            "times_min": [0, 10, 20, 30, 40, 50, 60, 70],
                            "discharge_m3s": [0, 10, 40, 90, 60, 30, 10, 0],
                        },
                        {
                            "id": "B",
                            "type": "subcatchment",
                            "times_min": [0, 10, 20, 30, 40, 50, 60, 70],
                            "discharge_m3s": [0, 4, 12, 8, 3, 0, 0, 0],
                        },
                        {
                            "id": "R1",
                            "type": "reach",
                            "from": ["A"],
                            "method": "lag",
                            "lag_min": 25.0,
                        },
                        {"id": "J1", "type": "junction", "from": ["R1", "B"]},
                        {"id": "OUT", "type": "outlet", "from": ["J1"]},
                    ],
                },
                "nodes": ["OUT"],
            },
        ),
        result_schema="hydrolog-route-network/1",
        cardinality="bounded",
        rules=(
            "Give `network` or `network_file`; a `rating_file` lies beside the file.",
            "`output_dir` writes `<id>.csv` per node (`nodes` selects); `check` "
            "plans it.",
            "Notices begin with the node id.",
        ),
        rules_pl=(
            "Podaj `network` albo `network_file`; `rating_file` leży obok pliku.",
            "`output_dir` zapisuje `<id>.csv` każdego węzła (`nodes` wybiera); `check` "
            "to planuje.",
            "Uwagi zaczynają się od id węzła.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
            "io_error",
            "conflict",
        ),
        example_results=(
            {
                "name": "Pond catchment",
                "timestep_min": 10.0,
                "outlet": "OUT",
                "order": ["A", "B", "R1", "J1", "D", "OUT"],
                "nodes": [
                    {"id": "A", "peak_m3s": 24.0, "time_to_peak_min": 60.0},
                    {"id": "B", "peak_m3s": 6.8, "time_to_peak_min": 40.0},
                    {
                        "id": "R1",
                        "type": "reach",
                        "from": ["A"],
                        "peak_m3s": 22.231889,
                        "time_to_peak_min": 120.0,
                        "model": "muskingum-cunge",
                        "peak_attenuation_pct": 7.367128,
                        "peak_delay_min": 60.0,
                    },
                    {"id": "J1", "peak_m3s": 25.471889, "time_to_peak_min": 120.0},
                    {
                        "id": "D",
                        "type": "reservoir",
                        "from": ["J1"],
                        "peak_m3s": 13.86388,
                        "time_to_peak_min": 170.0,
                        "model": "level-pool",
                        "peak_attenuation_pct": 45.571842,
                        "peak_delay_min": 50.0,
                    },
                ],
            },
            {
                "timestep_min": 10.0,
                "outlet": "OUT",
                "order": ["A", "B", "R1", "J1", "OUT"],
                "nodes": [
                    {"id": "A", "peak_m3s": 90.0, "time_to_peak_min": 30.0},
                    {"id": "B", "peak_m3s": 12.0, "time_to_peak_min": 20.0},
                    {
                        "id": "R1",
                        "model": "lag",
                        "peak_m3s": 75.0,
                        "peak_attenuation_pct": 16.666667,
                        "peak_delay_min": 30.0,
                    },
                    {"id": "J1", "peak_m3s": 75.0, "volume_m3": 160200.0},
                    {
                        "id": "OUT",
                        "type": "outlet",
                        "peak_m3s": 75.0,
                        "time_to_peak_min": 60.0,
                        "times_min": [0.0, 10.0, 20.0],
                        "discharge_m3s": [0.0, 4.0, 12.0],
                    },
                ],
            },
        ),
    ),
)


def model_options(method: str) -> tuple[Option, ...]:
    """Return the options of ``route <method>`` that describe the element.

    These are the options a reach of a network takes next to ``method``
    (``hydrolog-network/1``): the options of the command without the inflow, the run
    (``initial_outflow_m3s`` and ``extend_min``, which every reach and reservoir of a
    network takes) and the output, which the network supplies itself.

    Parameters
    ----------
    method : str
        One of :data:`MODEL_METHODS`.

    Returns
    -------
    tuple of Option
        The declarations, in catalog order.

    Raises
    ------
    KeyError
        If ``method`` is not one of :data:`MODEL_METHODS`.
    """
    if method not in MODEL_METHODS:
        raise KeyError(method)
    shared = {
        option.name for option in (*INFLOW_OPTIONS, *RUN_OPTIONS, *OUTPUT_OPTIONS)
    }
    command = next(item for item in COMMANDS if item.name == f"route {method}")
    return tuple(option for option in command.options if option.name not in shared)
