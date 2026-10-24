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
)
