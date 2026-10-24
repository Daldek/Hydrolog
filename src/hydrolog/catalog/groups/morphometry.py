"""Group ``morphometry``: geometric and terrain indicators of a watershed.

The operation is in :mod:`hydrolog.operations.morphometry`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="morphometry watershed",
        operation_id="hydrolog_morphometry_watershed",
        summary_pl="Oblicz wskaźniki geometryczne, kształtu i rzeźby zlewni.",
        summary="Compute geometric, shape and relief indicators of a watershed.",
        description_pl=(
            "Oblicza geometrię, wskaźniki kształtu (Horton, Gravelius, Miller, Schumm, "
            "Chorley), wysokości, rzeźbę i spadki z `WatershedParameters` (obiekt lub "
            "plik JSON). Spadki wynikają ze wskaźnika rzeźby H/L, nie z NMT; dane "
            "terenowe z NMT daje Hydrograf."
        ),
        description=(
            "Compute area, shape indicators (Horton, Gravelius, Miller, Schumm, "
            "Chorley), elevations, relief and slopes from `WatershedParameters` (object"
            " or JSON file). Slopes come from the relief ratio H/L, not from a DEM; use"
            " Hydrograf for DEM terrain data."
        ),
        function="hydrolog.operations.morphometry_watershed",
        options=(
            Option(
                name="watershed",
                type="object",
                description_pl=(
                    "Parametry zlewni jako obiekt JSON (klucze `WatershedParameters`): "
                    "wymagane `area_km2` [km²], `perimeter_km` [km], `length_km` [km], "
                    "`elevation_min_m` i `elevation_max_m` [m n.p.m.]; opcjonalne "
                    "m.in. `elevation_mean_m`, `channel_length_km`, `name`."
                ),
                description=(
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
                path_role="input",
                description_pl=(
                    "Plik JSON z parametrami zlewni (format `WatershedParameters."
                    "to_json()`, np. z Hydrografu); zamiast `watershed`."
                ),
                description=(
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
        result_schema="hydrolog-morphometry-watershed/1",
        rules=(
            "Give `watershed` or `watershed_file`, exactly one.",
            "Read `notices` for assumed mean elevation or channel length.",
            "Areas are in km2, lengths in km, elevations in m.",
        ),
        rules_pl=(
            "Podaj dokładnie jedno z `watershed` lub `watershed_file`.",
            (
                "Sprawdź `notices` pod kątem założonej średniej wysokości lub długości "
                "cieku."
            ),
            "Powierzchnie w km2, długości w km, wysokości w m.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "calculation_error",
            "forbidden",
        ),
        core=True,
        example_results=(
            {
                "name": "Zlewnia testowa",
                "geometry": {
                    "area_km2": 45.3,
                    "perimeter_km": 32.1,
                    "length_km": 12.5,
                    "width_km": 3.624,
                },
                "elevation": {
                    "elevation_min_m": 150.0,
                    "elevation_max_m": 520.0,
                    "elevation_mean_m": 310.0,
                    "relief_m": 370.0,
                    "relief_ratio": 0.0296,
                },
            },
            {
                "name": "Zlewnia Przykładowa",
                "geometry": {
                    "area_km2": 45.3,
                    "perimeter_km": 32.1,
                    "length_km": 12.5,
                    "width_km": 3.624,
                },
                "elevation": {
                    "elevation_min_m": 150.0,
                    "elevation_max_m": 520.0,
                    "elevation_mean_m": 310.0,
                    "relief_m": 370.0,
                    "relief_ratio": 0.0296,
                },
            },
        ),
    ),
)
