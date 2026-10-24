"""Group ``scs``: effective precipitation by the SCS-CN method."""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="scs effective",
        operation_id="scs_effective",
        summary=(
            "Opad efektywny metodą SCS-CN z sumy opadu lub hietogramu (CN, AMC, Ia)."
        ),
        summary_en=(
            "Effective precipitation by the SCS-CN method from a total or a hyetograph."
        ),
        description=(
            "Opad efektywny (odpływ bezpośredni) metodą SCS-CN (USDA-NRCS): Pe = "
            "(P − Ia)² / (P − Ia + S) dla P > Ia, w przeciwnym razie Pe = 0, gdzie "
            "S = 25400/CN − 254 [mm] to maksymalna retencja, a Ia = λ · S straty "
            "początkowe (λ = `ia_coefficient`, standardowo 0,2; CN = 100 daje "
            "S = 0). Wejście: suma opadu `precipitation_mm` [mm] albo szereg "
            "wysokości opadu w kolejnych krokach czasowych (`values` lub "
            "`input_file` + `value_column`, każda wartość ≥ 0, bez braków); dla "
            "szeregu Pe liczone jest od sumy narastającej opadu, a różnice Pe "
            "dają opad efektywny w poszczególnych krokach. CN podaje się dla "
            "AMC II; `amc` I (sucho) i III (mokro) przelicza CN wzorami Chow i in. "
            "(1988): CN_I = CN_II/(2,281 − 0,01281·CN_II), CN_III = CN_II/(0,427 + "
            "0,00573·CN_II) (wynik zaokrąglony do liczby całkowitej, 1–100). "
            "Tablice CN z TR-55 są skalibrowane dla λ = 0,2; λ = 0,05 "
            "(Woodward i in., 2003) wymaga przekalibrowania CN, o czym informuje "
            "uwaga w wyniku. Wynik: skorygowane CN, S, Ia, suma opadu, suma opadu "
            "efektywnego, współczynnik odpływu C = Pe/P oraz opad efektywny w "
            "krokach (dla szeregu). Literatura: USDA-NRCS (2004), National "
            "Engineering Handbook, Part 630, rozdz. 10; Chow, V.T., Maidment, "
            "D.R., Mays, L.W. (1988), Applied Hydrology."
        ),
        description_en=(
            "Effective precipitation (direct runoff) by the SCS-CN method "
            "(USDA-NRCS): Pe = (P - Ia)^2 / (P - Ia + S) for P > Ia, otherwise Pe "
            "= 0, where S = 25400/CN - 254 [mm] is the maximum retention and Ia = "
            "λ · S the initial abstraction (λ = `ia_coefficient`, 0.2 as "
            "standard; CN = 100 gives S = 0). Input: the total precipitation "
            "`precipitation_mm` [mm] or a series of precipitation depths in "
            "consecutive time steps (`values` or `input_file` + `value_column`, "
            "each value >= 0, no gaps); for a series Pe is computed from the "
            "cumulative precipitation and the differences of Pe give the "
            "effective precipitation of each step. CN is given for AMC II; `amc` I "
            "(dry) and III (wet) convert it with the formulas of Chow et al. "
            "(1988): CN_I = CN_II/(2.281 - 0.01281·CN_II), CN_III = CN_II/(0.427 + "
            "0.00573·CN_II) (rounded to an integer, 1-100). The TR-55 CN tables "
            "are calibrated for λ = 0.2; λ = 0.05 (Woodward et al., 2003) needs "
            "recalibrated CN, which a notice in the result points out. Result: the "
            "adjusted CN, S, Ia, the total precipitation, the total effective "
            "precipitation, the runoff coefficient C = Pe/P and the effective "
            "precipitation per step (for a series). References: USDA-NRCS (2004), "
            "National Engineering Handbook, Part 630, chapter 10; Chow, V.T., "
            "Maidment, D.R., Mays, L.W. (1988), Applied Hydrology."
        ),
        function="hydrolog.operations:scs_effective",
        options=(
            Option(
                name="cn",
                type="number",
                description=(
                    "Liczba krzywej CN dla AMC II, 1–100 (może być ułamkowa, np. "
                    "średnia ważona z `cn weighted`)."
                ),
                description_en=(
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
                description="Całkowita wysokość opadu [mm]; ≥ 0.",
                description_en="Total precipitation depth [mm]; >= 0.",
                minimum=0,
                unit="mm",
            ),
            Option(
                name="values",
                type="number_list",
                description=(
                    "Wysokości opadu w kolejnych krokach czasowych (hietogram) "
                    "[mm]; każda ≥ 0."
                ),
                description_en=(
                    "Precipitation depths in consecutive time steps (hyetograph) "
                    "[mm]; each >= 0."
                ),
                minimum=0,
                unit="mm",
            ),
            Option(
                name="input_file",
                type="path",
                description=(
                    "Plik CSV (przecinek lub średnik, wiersz nagłówka) albo JSON "
                    "z wysokościami opadu w krokach [mm]."
                ),
                description_en=(
                    "CSV file (comma or semicolon, header row) or JSON file with "
                    "precipitation depths per step [mm]."
                ),
            ),
            Option(
                name="value_column",
                type="string",
                description=(
                    "Kolumna pliku z wysokościami opadu; pomijana, gdy plik ma "
                    "jedną kolumnę (nazwa może być bez jednostki `[mm]`)."
                ),
                description_en=(
                    "File column holding the precipitation depths; may be omitted "
                    "for a one-column file (the name may omit the `[mm]` unit)."
                ),
            ),
            Option(
                name="amc",
                type="choice",
                description=(
                    "Wilgotność poprzedzająca (AMC): I — sucho, II — przeciętnie, "
                    "III — mokro; domyślnie II."
                ),
                description_en=(
                    "Antecedent moisture condition (AMC): I - dry, II - normal, "
                    "III - wet; default II."
                ),
                choices=("I", "II", "III"),
                default="II",
            ),
            Option(
                name="ia_coefficient",
                type="number",
                description=(
                    "Współczynnik strat początkowych λ (Ia = λ·S), 0 < λ ≤ 1; "
                    "domyślnie 0,2 (wartość standardowa, dla której skalibrowano "
                    "tablice CN)."
                ),
                description_en=(
                    "Initial abstraction ratio λ (Ia = λ·S), 0 < λ <= 1; default "
                    "0.2 (the standard value the CN tables are calibrated for)."
                ),
                exclusive_minimum=0,
                maximum=1,
                default=0.2,
            ),
        ),
        one_of=(("precipitation_mm",), ("values",), ("input_file",)),
        examples=(
            {"cn": 72, "precipitation_mm": 50.0},
            {"cn": 80, "precipitation_mm": 75.0, "amc": "III"},
            {"cn": 72, "values": [2.5, 5.0, 12.5, 15.0, 8.0, 4.0, 3.0]},
        ),
    ),
)
