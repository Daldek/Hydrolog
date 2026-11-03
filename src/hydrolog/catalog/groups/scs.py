"""Group ``scs``: effective precipitation by the SCS-CN method."""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="scs effective",
        operation_id="hydrolog_scs_effective",
        summary_pl="Oblicz opad efektywny metodą SCS-CN z sumy opadu lub hietogramu.",
        summary=(
            "Compute effective precipitation by the SCS-CN method from a total or a "
            "hyetograph."
        ),
        description_pl=(
            "Opad efektywny SCS-CN z `precipitation_mm` lub szeregu (`values`, "
            "`input_file`); CN dla AMC II, `amc` go koryguje. Nie do doboru i ważenia "
            "CN (`cn lookup`, `cn weighted`) ani hydrogramu (`hydrograph generate`). "
            "Standardowo Ia = 0,2·S."
        ),
        description=(
            "SCS-CN effective precipitation from `precipitation_mm` or a series "
            "(`values`, `input_file`); CN is for AMC II, `amc` adjusts it. Not for CN "
            "lookup or weighting (`cn lookup`, `cn weighted`) or the hydrograph "
            "(`hydrograph generate`). Standard Ia = 0.2·S."
        ),
        function="hydrolog.operations.scs_effective",
        options=(
            Option(
                name="cn",
                type="number",
                description_pl=(
                    "Liczba krzywej CN dla AMC II, 1–100 (może być ułamkowa, np. "
                    "średnia ważona z `cn weighted`)."
                ),
                description=(
                    "Curve Number CN for AMC II, 1-100 (may be fractional, e.g. a "
                    "weighted mean from `cn weighted`)."
                ),
                required=True,
                minimum=1,
                maximum=100,
            ),
            Option(
                name="precipitation_mm",
                type="number",
                description_pl="Całkowita wysokość opadu [mm]; ≥ 0.",
                description="Total precipitation depth [mm]; >= 0.",
                minimum=0,
                unit="mm",
            ),
            Option(
                name="values",
                type="number_list",
                description_pl=(
                    "Wysokości opadu w kolejnych krokach czasowych (hietogram) "
                    "[mm]; każda ≥ 0."
                ),
                description=(
                    "Precipitation depths in consecutive time steps (hyetograph) "
                    "[mm]; each >= 0."
                ),
                minimum=0,
                unit="mm",
            ),
            Option(
                name="input_file",
                type="path",
                path_role="input",
                description_pl=(
                    "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON "
                    "z wysokościami opadu w krokach [mm]."
                ),
                description=(
                    "CSV file (comma or semicolon, header row) or JSON file with "
                    "precipitation depths per step [mm]."
                ),
            ),
            Option(
                name="value_column",
                type="string",
                description_pl=(
                    "Kolumna pliku z wysokościami opadu; pomijana, gdy plik ma "
                    "jedną kolumnę (nazwa może być bez jednostki `[mm]`)."
                ),
                description=(
                    "File column holding the precipitation depths; may be omitted "
                    "for a one-column file (the name may omit the `[mm]` unit)."
                ),
            ),
            Option(
                name="amc",
                type="choice",
                description_pl=("Wilgotność poprzedzająca (AMC); domyślnie II."),
                description=("Antecedent moisture condition (AMC); default II."),
                choices=("I", "II", "III"),
                meanings={
                    "I": "Dry antecedent moisture; CN lowered.",
                    "II": "Normal antecedent moisture; CN as given.",
                    "III": "Wet antecedent moisture; CN raised.",
                },
                meanings_pl={
                    "I": "Sucho przed opadem; CN obniżone.",
                    "II": "Przeciętna wilgotność; CN bez zmian.",
                    "III": "Mokro przed opadem; CN podwyższone.",
                },
                default="II",
            ),
            Option(
                name="ia_coefficient",
                type="number",
                description_pl=(
                    "Współczynnik strat początkowych λ (Ia = λ·S), 0 < λ ≤ 1; "
                    "domyślnie 0,2 (wartość standardowa, dla której skalibrowano "
                    "tablice CN)."
                ),
                description=(
                    "Initial abstraction ratio λ (Ia = λ·S), 0 < λ <= 1; default "
                    "0.2 (the standard value the CN tables are calibrated for)."
                ),
                exclusive_minimum=0,
                maximum=1,
                default=0.2,
            ),
        ),
        one_of=(("precipitation_mm",), ("values",), ("input_file",)),
        result_schema="hydrolog-scs-effective/1",
        cardinality="bounded",
        rules=(
            "Give exactly one of precipitation_mm, values, input_file.",
            "Pass CN for AMC II; amc adjusts it.",
            "Check `notices` for a non-standard ia_coefficient.",
        ),
        rules_pl=(
            "Podaj dokładnie jedno z: precipitation_mm, values, input_file.",
            "Podaj CN dla AMC II; amc je koryguje.",
            "Sprawdź `notices` przy niestandardowym ia_coefficient.",
        ),
        errors=("validation_error", "not_found", "data_error", "forbidden"),
        core=True,
        example_results=(
            {
                "cn_adjusted": 72.0,
                "retention_mm": 98.7778,
                "initial_abstraction_mm": 19.7556,
                "total_effective_mm": 7.08968,
                "runoff_coefficient": 0.141794,
            },
            {
                "cn_adjusted": 90,
                "retention_mm": 28.2222,
                "initial_abstraction_mm": 5.64444,
                "total_effective_mm": 49.296,
                "runoff_coefficient": 0.65728,
            },
            {
                "cn_adjusted": 72.0,
                "retention_mm": 98.7778,
                "initial_abstraction_mm": 19.7556,
                "total_effective_mm": 7.08968,
                "runoff_coefficient": 0.141794,
            },
        ),
        examples=(
            {"cn": 72, "precipitation_mm": 50.0},
            {"cn": 80, "precipitation_mm": 75.0, "amc": "III"},
            {"cn": 72, "values": [2.5, 5.0, 12.5, 15.0, 8.0, 4.0, 3.0]},
        ),
    ),
)
