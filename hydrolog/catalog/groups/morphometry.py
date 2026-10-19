"""Group ``morphometry``: geometric and terrain indicators of a watershed.

The operation is in :mod:`hydrolog.operations.morphometry`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="morphometry watershed",
        operation_id="morphometry_watershed",
        summary=(
            "Wskaźniki geometryczne, kształtu i rzeźby zlewni z jej parametrów "
            "(obiekt albo plik JSON)."
        ),
        summary_en=(
            "Geometric, shape and relief indicators of a watershed from its parameters "
            "(object or JSON file)."
        ),
        description=(
            "Oblicza wskaźniki zlewni z parametrów `WatershedParameters` (obiekt albo "
            "plik JSON, np. z Hydrografu). Geometria: powierzchnia A [km²], obwód P "
            "[km], długość L [km] i średnia szerokość W = A/L [km]. Wskaźniki kształtu "
            "[–]: współczynnik kształtu Hortona Cf = A/L², współczynnik zwartości "
            "Graveliusa Cz = P/(2√(πA)), wskaźnik kolistości Millera Ck = 4πA/P², "
            "wskaźnik wydłużenia Schumma Ce = 2√(A/π)/L i wskaźnik lemniskaty "
            "Chorleya Cl = L²/(4A). Ukształtowanie: wysokości minimalna, maksymalna i "
            "średnia [m n.p.m.], deniwelacja H = max − min [m] i wskaźnik rzeźby "
            "Rh = H/L [–]. Spadki [% i m/m]: spadek zlewni przybliżony wskaźnikiem "
            "rzeźby H/L (to nie jest spadek wyznaczony z NMT) oraz spadek cieku "
            "H/długość cieku. Spadki podane w parametrach zlewni "
            "(`mean_slope_m_per_m`, `channel_slope_m_per_m`) nie są tu używane "
            "(używają ich komendy czasu koncentracji, np. `tc watershed`): gdy "
            "plik je zawiera, `notices` (`slopes_from_relief`) podaje obie "
            "wartości, policzoną i podaną. Gdy brak "
            "`elevation_mean_m`, średnia wysokość to (min + max)/2, a gdy brak "
            "`channel_length_km`, długość cieku przyjmuje się równą długości zlewni; "
            "oba przypadki są zgłaszane w `notices`. Wynik: `name`, `geometry`, "
            "`shape_indicators`, `elevation`, `slopes`."
        ),
        description_en=(
            "Computes watershed indicators from `WatershedParameters` (an object or a "
            "JSON file, e.g. from Hydrograf). Geometry: area A [km²], perimeter P "
            "[km], length L [km] and mean width W = A/L [km]. Shape indicators [–]: "
            "Horton form factor Cf = A/L², Gravelius compactness Cz = P/(2√(πA)), "
            "Miller circularity Ck = 4πA/P², Schumm elongation Ce = 2√(A/π)/L and "
            "Chorley lemniscate ratio Cl = L²/(4A). Relief: minimum, maximum and mean "
            "elevation [m a.s.l.], relief H = max − min [m] and relief ratio Rh = H/L "
            "[–]. Slopes [% and m/m]: the watershed slope approximated by the relief "
            "ratio H/L (it is not a DEM-derived slope) and the channel slope "
            "H/channel length. The slopes given in the watershed parameters "
            "(`mean_slope_m_per_m`, `channel_slope_m_per_m`) are not used here (the "
            "time of concentration commands, e.g. `tc watershed`, use them): when "
            "the file has them, `notices` (`slopes_from_relief`) gives both "
            "values, the computed and the given one. Without "
            "`elevation_mean_m` the mean elevation is (min + max)/2, and without "
            "`channel_length_km` the channel length is taken equal to the watershed "
            "length; both cases are reported in `notices`. Result: `name`, "
            "`geometry`, `shape_indicators`, `elevation`, `slopes`."
        ),
        function="hydrolog.operations:morphometry_watershed",
        options=(
            Option(
                name="watershed",
                type="object",
                description=(
                    "Parametry zlewni jako obiekt JSON (klucze `WatershedParameters`): "
                    "wymagane `area_km2` [km²], `perimeter_km` [km], `length_km` [km], "
                    "`elevation_min_m` i `elevation_max_m` [m n.p.m.]; opcjonalne "
                    "m.in. `elevation_mean_m`, `channel_length_km`, `name`."
                ),
                description_en=(
                    "Watershed parameters as a JSON object (the keys of "
                    "`WatershedParameters`): required `area_km2` [km²], "
                    "`perimeter_km` [km], `length_km` [km], `elevation_min_m` and "
                    "`elevation_max_m` [m a.s.l.]; optional among others "
                    "`elevation_mean_m`, `channel_length_km`, `name`."
                ),
            ),
            Option(
                name="watershed_file",
                type="path",
                description=(
                    "Plik JSON z parametrami zlewni (format `WatershedParameters."
                    "to_json()`, np. z Hydrografu); zamiast `watershed`."
                ),
                description_en=(
                    "JSON file with the watershed parameters (the "
                    "`WatershedParameters.to_json()` format, e.g. from Hydrograf); "
                    "instead of `watershed`."
                ),
            ),
        ),
        one_of=(("watershed",), ("watershed_file",)),
        examples=(
            {
                "watershed": {
                    "name": "Zlewnia testowa",
                    "area_km2": 45.3,
                    "perimeter_km": 32.1,
                    "length_km": 12.5,
                    "elevation_min_m": 150.0,
                    "elevation_max_m": 520.0,
                    "elevation_mean_m": 310.0,
                    "channel_length_km": 14.2,
                }
            },
            {"watershed_file": "tests/fixtures/watershed_example.json"},
        ),
    ),
)
