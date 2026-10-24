"""Group ``network``: classification of a river network.

The operation is in :mod:`hydrolog.operations.network`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="network stats",
        operation_id="hydrolog_network_stats",
        summary_pl="Oblicz statystyki rzędów sieci rzecznej (Strahler lub Shreve).",
        summary="Compute the order statistics of a river network (Strahler or Shreve).",
        description_pl=(
            "Nadaje rzędy odcinkom sieci rzecznej (Strahler lub Shreve) i podsumowuje "
            "liczby, długości oraz współczynniki bifurkacji i długości Hortona; z "
            "`area_km2` także gęstość sieci i częstość cieków. Dla listy odcinków; "
            "geometrii nie czyta. Cykle i nieznane id to błędy."
        ),
        description=(
            "Order the segments of a river network (Strahler or Shreve) and summarize "
            "counts, lengths, Horton bifurcation and length ratios; with `area_km2` "
            "also drainage density and stream frequency. Use for a segment list; no "
            "geometry is read. Cycles and unknown ids are errors."
        ),
        function="hydrolog.operations.network_stats",
        options=(
            Option(
                name="segments",
                type="object_list",
                description_pl=(
                    "Odcinki sieci jako lista obiektów: `segment_id` (liczba "
                    "całkowita), `upstream_ids` (lista id odcinków wpływających; "
                    "pusta albo pominięta dla źródła) i `length_km` [km]."
                ),
                description=(
                    "Network segments as a list of objects: `segment_id` (integer), "
                    "`upstream_ids` (list of the ids of the segments flowing in; "
                    "empty or omitted for a headwater) and `length_km` [km]."
                ),
            ),
            Option(
                name="segments_file",
                type="path",
                path_role="input",
                description_pl=(
                    "Plik CSV albo JSON z odcinkami (kolumny `segment_id`, "
                    "`upstream_ids`, `length_km`); w CSV id w `upstream_ids` rozdziela "
                    "średnik, np. `3;4`."
                ),
                description=(
                    "CSV or JSON file with the segments (columns `segment_id`, "
                    "`upstream_ids`, `length_km`); in CSV the ids in `upstream_ids` "
                    "are separated by a semicolon, e.g. `3;4`."
                ),
            ),
            Option(
                name="method",
                type="choice",
                description_pl="Metoda nadawania rzędów.",
                description="Ordering method.",
                choices=("strahler", "shreve"),
                meanings={
                    "strahler": "Order grows when two top-order streams meet.",
                    "shreve": "Order is the number of sources upstream of the segment.",
                },
                meanings_pl={
                    "strahler": "Rząd rośnie, gdy łączą się dwa cieki równego rzędu.",
                    "shreve": "Rząd to liczba źródeł powyżej odcinka.",
                },
                default="strahler",
            ),
            Option(
                name="area_km2",
                type="number",
                description_pl=(
                    "Powierzchnia zlewni; włącza obliczenie gęstości sieci rzecznej i "
                    "częstości cieków."
                ),
                description=(
                    "Watershed area; enables the drainage density and the stream "
                    "frequency."
                ),
                exclusive_minimum=0,
                unit="km2",
            ),
        ),
        one_of=(("segments",), ("segments_file",)),
        examples=(
            {
                "segments": [
                    {"segment_id": 1, "upstream_ids": [], "length_km": 1.2},
                    {"segment_id": 2, "upstream_ids": [], "length_km": 0.8},
                    {"segment_id": 3, "upstream_ids": [1, 2], "length_km": 1.5},
                ],
                "method": "strahler",
                "area_km2": 4.5,
            },
            {
                "segments_file": "tests/fixtures/network_segments.csv",
                "method": "shreve",
                "area_km2": 12.0,
            },
        ),
        result_schema="hydrolog-network-stats/1",
        rules=(
            "Give `segments` or `segments_file`, exactly one.",
            ("Use `upstream_ids` with ids of segments flowing in; empty for a source."),
            "Give `area_km2` in km2 to get drainage density.",
        ),
        rules_pl=(
            "Podaj dokładnie jedno z `segments` lub `segments_file`.",
            "W `upstream_ids` podaj id dopływów; puste dla źródła.",
            "Podaj `area_km2` w km2, by uzyskać gęstość sieci.",
        ),
        errors=("validation_error", "not_found", "data_error", "forbidden"),
        example_results=(
            {
                "method": "strahler",
                "n_segments": 3,
                "stream_frequency_per_km2": 0.666667,
                "statistics": {
                    "max_order": 2,
                    "total_stream_length_km": 3.5,
                    "drainage_density": 0.777778,
                },
            },
            {
                "method": "shreve",
                "n_segments": 9,
                "stream_frequency_per_km2": 0.75,
                "statistics": {
                    "max_order": 5,
                    "total_stream_length_km": 12.7,
                    "drainage_density": 1.05833,
                },
            },
        ),
    ),
)
