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
        operation_id="hydrometrics_rating_curve",
        summary=(
            "Krzywa przepływu Q = a·(H − H₀)^b dopasowana do par stan–przepływ, z "
            "opcjonalnym usuwaniem odstających."
        ),
        summary_en=(
            "Rating curve Q = a·(H − H₀)^b fitted to stage–discharge pairs, with "
            "optional outlier removal."
        ),
        description=(
            "Dopasowuje potęgową krzywą przepływu Q = a·(H − H₀)^b do par pomiarów "
            "stanu wody H (cm albo m) i przepływu Q [m³/s] nieliniową metodą "
            "najmniejszych kwadratów (`scipy.optimize.curve_fit`; więzy a ≥ 0, b ≥ 0, "
            "H₀ poniżej najniższego stanu z pomiarów; punkt startowy a = 1, b = 1,5, "
            "H₀ = `h0_initial`, domyślnie dobierany z danych: najniższy stan minus "
            "10 % rozstępu stanów, co najmniej jedna jednostka, więc działa także dla "
            "stanów poniżej zera wodowskazu). Z `remove_outliers=true` po pierwszym "
            "dopasowaniu "
            "odrzucane są pary, których reszta przekracza `outlier_std` odchyleń "
            "standardowych, i krzywa jest dopasowywana ponownie (o ile zostaną co "
            "najmniej 3 pary). Wymaga co najmniej 3 par; pary z brakującą wartością "
            "(NaN) są pomijane i zgłaszane w `notices`; brak zbieżności to "
            "`calculation_error`. Pary podaje się inline (`water_levels` i "
            "`discharges`) albo w pliku (`input_file` z `level_column` i "
            "`discharge_column`). Wynik: `a`, `b`, `h0` (w jednostce stanów H), "
            "`r_squared`, `std_residuals` [m³/s], `n_points` (pary użyte w "
            "ostatecznym dopasowaniu) i `n_outliers_removed`."
        ),
        description_en=(
            "Fits the power-law rating curve Q = a·(H − H₀)^b to pairs of water "
            "level H (cm or m) and discharge Q [m³/s] by non-linear least squares "
            "(`scipy.optimize.curve_fit`; constraints a ≥ 0, b ≥ 0, H₀ below the "
            "lowest observed level; starting point a = 1, b = 1.5, H₀ = "
            "`h0_initial`, by default chosen from the data: the lowest level minus "
            "10 % of the range of the levels, at least one unit, so it works for "
            "levels below the gauge zero too). With `remove_outliers=true` the pairs "
            "whose residual exceeds `outlier_std` standard deviations are dropped "
            "after the first "
            "fit and the curve is fitted again (when at least 3 pairs remain). At "
            "least 3 pairs are required; pairs with a missing value (NaN) are "
            "skipped and reported in `notices`; failure to converge is "
            "`calculation_error`. Pairs are given inline (`water_levels` and "
            "`discharges`) or in a file (`input_file` with `level_column` and "
            "`discharge_column`). Result: `a`, `b`, `h0` (in the unit of the "
            "levels H), `r_squared`, `std_residuals` [m³/s], `n_points` (pairs used "
            "in the final fit) and `n_outliers_removed`."
        ),
        function="hydrolog.operations:hydrometrics_rating_curve",
        options=(
            Option(
                name="water_levels",
                type="number_list",
                description=(
                    "Stany wody H z kolejnych pomiarów przepływu (cm albo m, tak samo "
                    "jak `h0_initial`); tyle samo co `discharges`."
                ),
                description_en=(
                    "Water levels H of the successive discharge measurements (cm or "
                    "m, as for `h0_initial`); as many as `discharges`."
                ),
            ),
            Option(
                name="discharges",
                type="number_list",
                description="Przepływy Q zmierzone przy stanach `water_levels`.",
                description_en="Discharges Q measured at the levels `water_levels`.",
                unit="m3/s",
            ),
            replace(
                INPUT_FILE,
                description=(
                    "Plik CSV albo JSON z parami stan–przepływ (zamiast list "
                    "`water_levels` i `discharges`); kolumny wskazują `level_column` "
                    "i `discharge_column`."
                ),
                description_en=(
                    "CSV or JSON file with stage–discharge pairs (instead of the "
                    "lists `water_levels` and `discharges`); the columns are named by "
                    "`level_column` and `discharge_column`."
                ),
            ),
            Option(
                name="level_column",
                type="string",
                description=(
                    "Nazwa kolumny ze stanami wody w `input_file` (np. `H`; "
                    "wystarczy nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description_en=(
                    "Name of the water level column in `input_file` (e.g. `H`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="discharge_column",
                type="string",
                description=(
                    "Nazwa kolumny z przepływami w `input_file` (np. `Q`; wystarczy "
                    "nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description_en=(
                    "Name of the discharge column in `input_file` (e.g. `Q`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="h0_initial",
                type="number",
                description=(
                    "Początkowe przybliżenie H₀, stanu zerowego przepływu, w "
                    "jednostce stanów; musi być niższe niż najniższy stan z pomiarów. "
                    "Bez tej opcji dobierane z danych (najniższy stan minus 10 % "
                    "rozstępu stanów, co najmniej jedna jednostka), także dla stanów "
                    "ujemnych."
                ),
                description_en=(
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
                description=(
                    "Odrzuć pary o resztach większych niż `outlier_std` odchyleń "
                    "standardowych i dopasuj krzywą ponownie."
                ),
                description_en=(
                    "Drop the pairs whose residual exceeds `outlier_std` standard "
                    "deviations and fit the curve again."
                ),
                default=False,
            ),
            Option(
                name="outlier_std",
                type="number",
                description=(
                    "Próg odstających obserwacji w odchyleniach standardowych reszt "
                    "(dodatni); działa z `remove_outliers`."
                ),
                description_en=(
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
        operation_id="hydrometrics_water_level_zones",
        summary=(
            "Strefy stanów wody wg Rybczyńskiego (NTW, STW, WTW) z histogramu i "
            "krzywej czasu trwania stanów."
        ),
        summary_en=(
            "Rybczyński water level zones (NTW, STW, WTW) from the histogram and the "
            "duration curve of water levels."
        ),
        description=(
            "Wyznacza strefy stanów wody metodą Rybczyńskiego z histogramu stanów "
            "(klasy o szerokości `bin_width`, od najniższego stanu zaokrąglonego w "
            "dół do liczby całkowitej): NTW (niskie tło wodne) – stany poniżej klasy "
            "modalnej, STW (średnie tło wodne) – od klasy modalnej do klasy, w której "
            "krzywa czasu trwania spada poniżej 50 %, WTW (wysokie tło wodne) – stany "
            "wyższe. Granica NTW/STW (`ntw_upper`) to środek klasy o największej "
            "częstości, a granica STW/WTW (`stw_upper`) to środek pierwszej klasy, "
            "dla której czas trwania stanów nie niższych niż jej dolna granica jest "
            "krótszy niż 50 % czasu; granice mają jednostkę stanów (cm albo m). "
            "Wynik: `n_observations`, `bin_width`, `zones` (`ntw_upper`, "
            "`stw_upper`, `ntw_range`, `stw_range`, `wtw_range`) i `frequency` "
            "(`bin_edges`, `bin_centers`, `counts`, `frequency_pct`, "
            "`cumulative_frequency_pct`, `duration_pct`). Braki danych (NaN) są "
            "pomijane i zgłaszane w `notices`."
        ),
        description_en=(
            "Delimits water level zones with the Rybczyński method from the "
            "histogram of the levels (classes of `bin_width`, starting at the lowest "
            "level rounded down to an integer): NTW (low background water) – levels "
            "below the modal class, STW (medium background water) – from the modal "
            "class to the class where the duration curve falls below 50 %, WTW (high "
            "background water) – higher levels. The NTW/STW limit (`ntw_upper`) is "
            "the centre of the most frequent class and the STW/WTW limit "
            "(`stw_upper`) is the centre of the first class for which the duration "
            "of levels not lower than its lower edge is shorter than 50 % of the "
            "time; the limits are in the unit of the levels (cm or m). Result: "
            "`n_observations`, `bin_width`, `zones` (`ntw_upper`, `stw_upper`, "
            "`ntw_range`, `stw_range`, `wtw_range`) and `frequency` (`bin_edges`, "
            "`bin_centers`, `counts`, `frequency_pct`, `cumulative_frequency_pct`, "
            "`duration_pct`). Missing values (NaN) are skipped and reported in "
            "`notices`."
        ),
        function="hydrolog.operations:hydrometrics_water_level_zones",
        options=(
            replace(
                VALUES,
                description=(
                    "Stany wody (cm albo m), np. dobowe z wielolecia. Długie szeregi "
                    "podawaj w pliku (`input_file`)."
                ),
                description_en=(
                    "Water levels (cm or m), e.g. daily values of many years. Give "
                    "long series in a file (`input_file`)."
                ),
            ),
            replace(
                INPUT_FILE,
                description=(
                    "Plik CSV albo JSON ze stanami wody, np. eksport szeregu z "
                    "IMGWTools; kolumnę wskazuje `value_column`."
                ),
                description_en=(
                    "CSV or JSON file with water levels, e.g. an IMGWTools series "
                    "export; the column is named by `value_column`."
                ),
            ),
            replace(
                VALUE_COLUMN,
                description=(
                    "Nazwa kolumny ze stanami wody w `input_file` (np. `H`; "
                    "wystarczy nazwa bez jednostki w nawiasie kwadratowym)."
                ),
                description_en=(
                    "Name of the water level column in `input_file` (e.g. `H`; the "
                    "name without the unit in square brackets is enough)."
                ),
            ),
            Option(
                name="bin_width",
                type="number",
                description=(
                    "Szerokość klasy histogramu stanów, w jednostce stanów (cm albo "
                    "m), dodatnia."
                ),
                description_en=(
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
