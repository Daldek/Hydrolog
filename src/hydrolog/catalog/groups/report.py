"""Group ``report``: the Markdown calculation report.

``report generate`` takes the inputs of ``hydrograph generate``
(:data:`hydrolog.catalog.groups.hydrograph.GENERATE_OPTIONS`), computes the design
hydrograph and writes the report. The operation is in
:mod:`hydrolog.operations.report`.
"""

from __future__ import annotations

from hydrolog.catalog.groups._output import CHECK, FORCE
from hydrolog.catalog.groups.hydrograph import GENERATE_ONE_OF, GENERATE_OPTIONS
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"


COMMANDS: tuple[Command, ...] = (
    Command(
        name="report generate",
        operation_id="hydrolog_report_generate",
        summary_pl="Zapisz raport obliczeniowy hydrogramu projektowego w Markdown.",
        summary="Write a Markdown calculation report of a design hydrograph.",
        description_pl=(
            "Liczy hydrogram jak `hydrograph generate` (te same opcje) i zapisuje "
            "polski raport Markdown ze wzorami, tabelami i bilansem wodnym. Do "
            "dokumentacji; same liczby daje `hydrograph generate`. Tabele są skracane "
            "do `max_table_rows`."
        ),
        description=(
            "Compute the hydrograph exactly like `hydrograph generate` (same options) "
            "and write a Polish Markdown report with formulas, tables and the water "
            "balance. Use for documentation; for the numbers only use `hydrograph "
            "generate`. Tables are cut to `max_table_rows`."
        ),
        function="hydrolog.operations.report_generate",
        options=(
            Option(
                name="output",
                type="path",
                description_pl=(
                    "Plik Markdown z raportem do zapisania; brakujące katalogi są "
                    "tworzone, istniejący plik jest zastępowany tylko z `force`."
                ),
                description=(
                    "Markdown file to write the report to; missing directories are "
                    "created, an existing file is replaced only with `force`."
                ),
                required=True,
                path_role="output",
            ),
            Option(
                name="watershed_name",
                type="string",
                description_pl=(
                    "Nazwa zlewni w nagłówku raportu; domyślnie `name` ze zlewni, "
                    "a gdy go brak — `Zlewnia`."
                ),
                description=(
                    "Watershed name in the report header; default: `name` of the "
                    "watershed, else `Zlewnia`."
                ),
            ),
            *GENERATE_OPTIONS,
            Option(
                name="include_formulas",
                type="boolean",
                description_pl="Dołącz wzory w LaTeX z podstawionymi wartościami.",
                description="Include the LaTeX formulas with substituted values.",
                default=True,
            ),
            Option(
                name="include_tables",
                type="boolean",
                description_pl=(
                    "Dołącz tabele szeregów czasowych i wskaźniki kształtu zlewni."
                ),
                description=(
                    "Include the time series tables and the watershed shape indicators."
                ),
                default=True,
            ),
            Option(
                name="max_table_rows",
                type="integer",
                description_pl=(
                    "Liczba wierszy tabeli, powyżej której jest skracana (początek i "
                    "koniec), co najmniej 1."
                ),
                description=(
                    "Number of rows above which a table is abbreviated (head and "
                    "tail), at least 1."
                ),
                default=50,
                minimum=1,
            ),
            FORCE,
            CHECK,
        ),
        one_of=GENERATE_ONE_OF,
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
        result_schema="hydrolog-report-generate/1",
        rules=(
            "Give the options of `hydrograph generate` plus `output`.",
            "Read `notices` for warnings of the computation.",
            "The report text is Polish whatever the interface language.",
        ),
        rules_pl=(
            "Podaj opcje `hydrograph generate` oraz `output`.",
            "Sprawdź `notices` pod kątem ostrzeżeń obliczeń.",
            "Tekst raportu jest po polsku niezależnie od języka interfejsu.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "forbidden",
            "io_error",
            "conflict",
        ),
        example_results=(
            {
                "watershed_name": "Zlewnia Przykładowa",
                "peak_discharge_m3s": 47.0273,
                "time_to_peak_min": 110.0,
                "total_precipitation_mm": 50.0,
                "cn_used": 72,
            },
            {
                "watershed_name": "Zlewnia testowa",
                "peak_discharge_m3s": 26.245,
                "time_to_peak_min": 140.0,
                "total_precipitation_mm": 48.0,
                "cn_used": 72.0,
            },
        ),
    ),
)
