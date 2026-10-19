"""Group ``report``: the Markdown calculation report.

``report generate`` takes the inputs of ``hydrograph generate``
(:data:`hydrolog.catalog.groups.hydrograph.GENERATE_OPTIONS`), computes the design
hydrograph and writes the report. The operation is in
:mod:`hydrolog.operations.report`.
"""

from __future__ import annotations

import dataclasses

from hydrolog.catalog.groups.hydrograph import GENERATE_ONE_OF, GENERATE_OPTIONS
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"


def _report_input(option: Option) -> Option:
    """An input of ``hydrograph generate``, as the report takes it."""
    if option.name != "ia_coefficient":
        return option
    return dataclasses.replace(
        option,
        description=(
            "Współczynnik strat początkowych λ (Ia = λ·S). Raport renderuje wzór "
            "z λ = 0,2 (standard), więc inna wartość jest odrzucana; domyślnie 0,2."
        ),
        description_en=(
            "Initial abstraction ratio λ (Ia = λ·S). The report renders the formula "
            "with λ = 0.2 (the standard), so any other value is rejected; default "
            "0.2."
        ),
    )


COMMANDS: tuple[Command, ...] = (
    Command(
        name="report generate",
        operation_id="report_generate",
        summary=(
            "Raport obliczeniowy hydrogramu w Markdown (wzory, tabele, bilans); dane "
            "jak w `hydrograph generate`; zapisuje plik."
        ),
        summary_en=(
            "Markdown report of a design hydrograph (formulas, tables, balance); "
            "inputs of `hydrograph generate`; writes a file."
        ),
        description=(
            "Liczy projektowy hydrogram odpływu dokładnie jak `hydrograph generate` "
            "(te same opcje: zlewnia, CN, tc, opad, model hydrogramu jednostkowego) i "
            "zapisuje do `output` raport obliczeniowy w Markdown (po polsku): "
            "nagłówek (nazwa zlewni, data, wersja Hydrologa), parametry zlewni i "
            "wskaźniki kształtu (gdy podano `watershed` albo `watershed_file`), czas "
            "koncentracji (metoda, wzór), hietogram opadu, opad efektywny metodą "
            "SCS-CN (retencja S, strata początkowa Ia, korekta AMC), hydrogram "
            "jednostkowy wybranego modelu, splot dyskretny, charakterystyki "
            "hydrogramu wynikowego (Qmax, czas do szczytu, objętość) i bilans wodny, "
            "ze wzorami w LaTeX i tabelami szeregów czasowych (skracanymi do "
            "`max_table_rows` wierszy). Ograniczenia generatora raportów: sekcja "
            "hydrogramu jednostkowego pokazuje kształt uproszczony (trójkątny), a nie "
            "rzędne modelu, natomiast sekcje wyników pochodzą z obliczeń; wzór "
            "straty początkowej jest renderowany z λ = 0,2, dlatego `ia_coefficient` "
            "inny niż 0,2 jest odrzucany; parametry wejściowe metod faa, kerby, "
            "kerby_kirpich i powierzchnia w metodzie giandottiego nie trafiają do "
            "sekcji czasu koncentracji. Plik jest zapisywany atomowo, istniejący jest "
            "zastępowany (nie może nim być plik wejściowy). Wynik: `output_path`, "
            "`size_bytes`, `sections` (tytuły sekcji), `watershed_name` oraz "
            "podsumowanie obliczeń (`peak_discharge_m3s`, `time_to_peak_min`, "
            "`total_volume_m3`, `total_precipitation_mm`, `total_effective_mm`, "
            "`runoff_coefficient`, `cn_used`); zapisany plik jest w `files`, "
            "ostrzeżenia obliczeń w `notices`."
        ),
        description_en=(
            "Computes the design runoff hydrograph exactly like `hydrograph "
            "generate` (the same options: watershed, CN, tc, precipitation, unit "
            "hydrograph model) and writes to `output` a calculation report in "
            "Markdown (in Polish): header (watershed name, date, Hydrolog version), "
            "watershed parameters and shape indicators (when `watershed` or "
            "`watershed_file` is given), time of concentration (method, formula), "
            "precipitation hyetograph, SCS-CN effective precipitation (retention S, "
            "initial abstraction Ia, AMC adjustment), the unit hydrograph of the "
            "chosen model, the discrete convolution, the characteristics of the "
            "resulting hydrograph (Qmax, time to peak, volume) and the water "
            "balance, with LaTeX formulas and time series tables (abbreviated to "
            "`max_table_rows` rows). Limits of the report generator: the unit "
            "hydrograph section shows a simplified (triangular) shape, not the "
            "ordinates of the model, while the result sections come from the "
            "computation; the initial abstraction formula is rendered with λ = 0.2, "
            "so an `ia_coefficient` other than 0.2 is rejected; the input "
            "parameters of the faa, kerby and kerby_kirpich methods and the area in "
            "the giandotti method do not reach the time of concentration section. "
            "The file is written atomically and an existing one is replaced (it "
            "must not be an input file). Result: `output_path`, `size_bytes`, "
            "`sections` (section titles), `watershed_name` and the computation "
            "summary (`peak_discharge_m3s`, `time_to_peak_min`, `total_volume_m3`, "
            "`total_precipitation_mm`, `total_effective_mm`, `runoff_coefficient`, "
            "`cn_used`); the written file is listed in `files`, the warnings of the "
            "computation in `notices`."
        ),
        function="hydrolog.operations:report_generate",
        options=(
            Option(
                name="output",
                type="path",
                description=(
                    "Plik Markdown z raportem do zapisania; brakujące katalogi są "
                    "tworzone, istniejący plik jest zastępowany."
                ),
                description_en=(
                    "Markdown file to write the report to; missing directories are "
                    "created, an existing file is replaced."
                ),
                required=True,
                writes=True,
            ),
            Option(
                name="watershed_name",
                type="string",
                description=(
                    "Nazwa zlewni w nagłówku raportu; domyślnie `name` ze zlewni, "
                    "a gdy go brak — `Zlewnia`."
                ),
                description_en=(
                    "Watershed name in the report header; default: `name` of the "
                    "watershed, else `Zlewnia`."
                ),
            ),
            *(_report_input(option) for option in GENERATE_OPTIONS),
            Option(
                name="include_formulas",
                type="boolean",
                description="Dołącz wzory w LaTeX z podstawionymi wartościami.",
                description_en="Include the LaTeX formulas with substituted values.",
                default=True,
            ),
            Option(
                name="include_tables",
                type="boolean",
                description=(
                    "Dołącz tabele szeregów czasowych i wskaźniki kształtu zlewni."
                ),
                description_en=(
                    "Include the time series tables and the watershed shape "
                    "indicators."
                ),
                default=True,
            ),
            Option(
                name="max_table_rows",
                type="integer",
                description=(
                    "Liczba wierszy tabeli, powyżej której jest skracana (początek i "
                    "koniec), co najmniej 1."
                ),
                description_en=(
                    "Number of rows above which a table is abbreviated (head and "
                    "tail), at least 1."
                ),
                default=50,
                minimum=1,
            ),
        ),
        one_of=GENERATE_ONE_OF,
        writes=True,
        examples=(
            {
                "output": "raport.md",
                "watershed_file": f"{_FIXTURES}/watershed_example.json",
                "tc_method": "kirpich",
                "hietogram_type": "beta",
                "total_mm": 50.0,
                "duration_min": 60.0,
                "timestep_min": 5.0,
                "uh_model": "scs",
            },
            {
                "output": "raport.md",
                "watershed_name": "Zlewnia testowa",
                "area_km2": 45.0,
                "cn": 72,
                "values": [5.0, 10.0, 15.0, 10.0, 5.0, 3.0],
                "timestep_min": 10.0,
                "uh_model": "nash",
                "nash_n": 3.0,
                "nash_k_min": 48.0,
                "max_table_rows": 20,
            },
        ),
    ),
)
