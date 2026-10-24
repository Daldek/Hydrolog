"""Group ``route``: lumped hydrologic flood routing of a discharge hydrograph.

Every command takes a hydrograph at a regular time step (``times_min`` with
``discharge_m3s``, or ``input_file``), routes it through one element of
:mod:`hydrolog.routing` and returns the outflow with its summary; ``output`` writes the
outflow as a hydrograph table that every ``route`` command reads again (ADR-0007,
ADR-0008). The operations are in :mod:`hydrolog.operations.route`.

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
)
