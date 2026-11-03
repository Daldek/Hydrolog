"""Group ``hydrometrics``: rating curves and water level zones.

The operations are in :mod:`hydrolog.operations.hydrometrics`.
"""

from __future__ import annotations

from dataclasses import replace

from hydrolog.catalog.groups._series import INPUT_FILE, VALUE_COLUMN, VALUES
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"

COMMANDS: tuple[Command, ...] = (
    Command(
        name="hydrometrics rating-curve",
        operation_id="hydrolog_hydrometrics_rating_curve",
        summary_pl=("Dopasuj krzywą przepływu Q = a·(H − H₀)^b do par stan–przepływ"),
        summary=("Fit a rating curve Q = a·(H − H₀)^b to stage–discharge pairs"),
        description_pl=(
            "Potęgowa krzywa przepływu nieliniową metodą najmniejszych kwadratów ze"
            " stanów H (cm albo m) i przepływów Q [m³/s], z opcjonalnym usuwaniem "
            "odstających. Do budowy zależności stan–przepływ; strefy stanów: "
            "`hydrometrics water-level-zones`. Wymaga co najmniej 3 par; pary z NaN"
            " są pomijane."
        ),
        description=(
            "Power-law rating curve by non-linear least squares from water level H "
            "(cm or m) and discharge Q [m³/s], with optional outlier removal. Use "
            "to build a stage–discharge relation; for level zones use `hydrometrics"
            " water-level-zones`. Needs 3 or more pairs; NaN pairs are skipped."
        ),
        result_schema="hydrolog-hydrometrics-rating-curve/1",
        rules=(
            (
                "Pass levels and discharges as equal-length lists, or a file with two "
                "columns."
            ),
            (
                "Check `r_squared`, `n_outliers_removed` and `notices` before using the"
                " curve."
            ),
            "`h0` is in the unit of the levels; discharge is in m³/s.",
        ),
        rules_pl=(
            (
                "Podaj stany i przepływy jako listy równej długości albo plik z dwiema "
                "kolumnami."
            ),
            (
                "Sprawdź `r_squared`, `n_outliers_removed` i `notices` przed użyciem "
                "krzywej."
            ),
            "`h0` jest w jednostce stanów; przepływ w m³/s.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "a": 0.00932083,
                "b": 1.51276,
                "h0": 39.1108,
                "r_squared": 0.999093,
                "n_points": 14,
                "n_outliers_removed": 1,
            },
            {
                "a": 0.0152929,
                "b": 1.42498,
                "h0": 43.7989,
                "r_squared": 0.998986,
                "n_points": 8,
                "n_outliers_removed": 0,
            },
            {
                "a": 0.00491733,
                "b": 1.64014,
                "h0": -25.1698,
                "r_squared": 0.999754,
                "n_points": 6,
                "n_outliers_removed": 0,
            },
        ),
        function="hydrolog.operations.hydrometrics_rating_curve",
        options=(
            Option(
                name="water_levels",
                type="number_list",
                description_pl=(
                    "Stany wody H z kolejnych pomiarów przepływu (cm albo m, tak samo "
                    "jak `h0_initial`); tyle samo co `discharges`."
                ),
                description=(
                    "Water levels H of the successive discharge measurements (cm or "
                    "m, as for `h0_initial`); as many as `discharges`."
                ),
            ),
            Option(
                name="discharges",
                type="number_list",
                description_pl="Przepływy Q zmierzone przy stanach `water_levels`.",
                description="Discharges Q measured at the levels `water_levels`.",
                unit="m3/s",
            ),
            replace(
                INPUT_FILE,
                description_pl=(
                    "Plik CSV albo JSON z parami stan–przepływ (zamiast list "
                    "`water_levels` i `discharges`); kolumny wskazują `level_column` "
                    "i `discharge_column`."
                ),
                description=(
                    "CSV or JSON file with stage–discharge pairs (instead of the "
                    "lists `water_levels` and `discharges`); the columns are named by "
                    "`level_column` and `discharge_column`."
                ),
            ),
            Option(
                name="level_column",
                type="string",
                description_pl=(
                    "Nazwa kolumny ze stanami wody w `input_file` (np. `H`; "
                    "wystarczy nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description=(
                    "Name of the water level column in `input_file` (e.g. `H`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="discharge_column",
                type="string",
                description_pl=(
                    "Nazwa kolumny z przepływami w `input_file` (np. `Q`; wystarczy "
                    "nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description=(
                    "Name of the discharge column in `input_file` (e.g. `Q`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="h0_initial",
                type="number",
                description_pl=(
                    "Początkowe przybliżenie H₀, stanu zerowego przepływu, w "
                    "jednostce stanów; musi być niższe niż najniższy stan z pomiarów. "
                    "Bez tej opcji dobierane z danych (najniższy stan minus 10 % "
                    "rozstępu stanów, co najmniej jedna jednostka), także dla stanów "
                    "ujemnych."
                ),
                description=(
                    "Initial guess of H₀, the level of zero flow, in the unit of the "
                    "levels; must be below the lowest observed level. Without this "
                    "option it is chosen from the data (the lowest level minus 10 % "
                    "of the range of the levels, at least one unit), also for "
                    "negative levels."
                ),
            ),
            Option(
                name="remove_outliers",
                type="boolean",
                description_pl=(
                    "Odrzuć pary o resztach większych niż `outlier_std` odchyleń "
                    "standardowych i dopasuj krzywą ponownie."
                ),
                description=(
                    "Drop the pairs whose residual exceeds `outlier_std` standard "
                    "deviations and fit the curve again."
                ),
                default=False,
            ),
            Option(
                name="outlier_std",
                type="number",
                description_pl=(
                    "Próg odstających obserwacji w odchyleniach standardowych reszt "
                    "(dodatni); działa z `remove_outliers`."
                ),
                description=(
                    "Outlier threshold in standard deviations of the residuals "
                    "(positive); used with `remove_outliers`."
                ),
                default=2.0,
                exclusive_minimum=0,
            ),
        ),
        one_of=(
            ("water_levels", "discharges"),
            ("input_file", "level_column", "discharge_column"),
        ),
        examples=(
            {
                "input_file": f"{_FIXTURES}/rating_curve_pairs.csv",
                "level_column": "H",
                "discharge_column": "Q",
                "h0_initial": 40.0,
                "remove_outliers": True,
            },
            {
                "water_levels": [62, 88, 115, 142, 170, 200, 235, 270],
                "discharges": [1.05, 3.4, 6.32, 10.48, 15.7, 20.5, 26.63, 34.92],
                "h0_initial": 40.0,
            },
            {
                "water_levels": [-10, 5, 20, 40, 80, 120],
                "discharges": [0.5, 1.2, 2.5, 4.8, 10.1, 17.3],
            },
        ),
    ),
    Command(
        name="hydrometrics water-level-zones",
        operation_id="hydrolog_hydrometrics_water_level_zones",
        summary_pl=(
            "Wyznacz strefy stanów wody wg Rybczyńskiego (NTW, STW, WTW) ze szeregu"
            " stanów"
        ),
        summary=(
            "Delimit Rybczyński water level zones (NTW, STW, WTW) from level series"
        ),
        description_pl=(
            "Granice stref z histogramu i krzywej czasu trwania stanów wody (klasy "
            "o szerokości `bin_width`): NTW niskie, STW średnie, WTW wysokie tło "
            "wodne. Do stref stanów wodowskazu; zależność stan–przepływ: "
            "`hydrometrics rating-curve`. Granice mają jednostkę stanów."
        ),
        description=(
            "Zone limits from the histogram and the duration curve of water levels "
            "(classes of `bin_width`): NTW low, STW medium, WTW high background "
            "water. Use for level zones of a gauge; for a stage–discharge relation "
            "use `hydrometrics rating-curve`. Limits are in the unit of the levels."
        ),
        result_schema="hydrolog-hydrometrics-water-level-zones/1",
        cardinality="bounded",
        rules=(
            (
                "Give water levels in one unit (cm or m) and set `bin_width` in the "
                "same unit."
            ),
            "Check `notices` for skipped missing values.",
            "Limits are `zones.ntw_upper` and `zones.stw_upper`.",
        ),
        rules_pl=(
            ("Podaj stany w jednej jednostce (cm albo m), `bin_width` w tej samej."),
            "Sprawdź `notices` pod kątem pominiętych braków danych.",
            "Granice to `zones.ntw_upper` i `zones.stw_upper`.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        example_results=(
            {
                "n_observations": 12,
                "bin_width": 10.0,
                "zones": {"ntw_upper": 155.0, "stw_upper": 175.0},
            },
        ),
        function="hydrolog.operations.hydrometrics_water_level_zones",
        options=(
            replace(
                VALUES,
                description_pl=(
                    "Stany wody (cm albo m), np. dobowe z wielolecia. Długie szeregi "
                    "podawaj w pliku (`input_file`)."
                ),
                description=(
                    "Water levels (cm or m), e.g. daily values of many years. Give "
                    "long series in a file (`input_file`)."
                ),
            ),
            replace(
                INPUT_FILE,
                description_pl=(
                    "Plik CSV albo JSON ze stanami wody, np. eksport szeregu z "
                    "IMGWTools; kolumnę wskazuje `value_column`."
                ),
                description=(
                    "CSV or JSON file with water levels, e.g. an IMGWTools series "
                    "export; the column is named by `value_column`."
                ),
            ),
            replace(
                VALUE_COLUMN,
                description_pl=(
                    "Nazwa kolumny ze stanami wody w `input_file` (np. `H`; "
                    "wystarczy nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description=(
                    "Name of the water level column in `input_file` (e.g. `H`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="bin_width",
                type="number",
                description_pl=(
                    "Szerokość klasy histogramu stanów, w jednostce stanów (cm albo "
                    "m), dodatnia."
                ),
                description=(
                    "Width of the histogram class of the levels, in the unit of the "
                    "levels (cm or m), positive."
                ),
                default=10.0,
                exclusive_minimum=0,
            ),
        ),
        one_of=(("values",), ("input_file", "value_column")),
        examples=(
            {
                "input_file": f"{_FIXTURES}/imgwtools_series_export.csv",
                "value_column": "H",
                "bin_width": 10,
            },
        ),
    ),
)
