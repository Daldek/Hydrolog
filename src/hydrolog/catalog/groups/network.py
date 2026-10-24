"""Group ``network``: classification of a river network.

The operation is in :mod:`hydrolog.operations.network`.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

COMMANDS: tuple[Command, ...] = (
    Command(
        name="network stats",
        operation_id="network_stats",
        summary=(
            "Klasyfikacja sieci rzecznej (Strahler, Shreve): rzędy, długości, "
            "wskaźniki Hortona, gęstość sieci."
        ),
        summary_en=(
            "River network classification (Strahler, Shreve): orders, lengths, Horton "
            "ratios, drainage density."
        ),
        description=(
            "Nadaje rzędy odcinkom sieci rzecznej metodą Strahlera (rząd rośnie, gdy "
            "łączą się dwa cieki tego samego, najwyższego rzędu) albo Shreve'a (rząd "
            "to suma rzędów dopływów, czyli liczba źródeł powyżej odcinka) i "
            "podsumowuje sieć: liczbę oraz łączną i średnią długość odcinków każdego "
            "rzędu, współczynnik bifurkacji Rb = N_i/N_(i+1) i współczynnik długości "
            "Rl = średnia długość rzędu i+1 / średnia długość rzędu i (prawa Hortona; "
            "sens mają dla rzędów Strahlera, dla Shreve'a to formalne ilorazy "
            "kolejnych rzędów), łączną długość cieków [km] oraz, po podaniu "
            "`area_km2`, gęstość sieci rzecznej Dd = ΣL/A [km/km²] i częstość cieków "
            "Fs = liczba odcinków/A [1/km²]. Odcinki podaje się inline (`segments`) "
            "albo w pliku CSV/JSON (`segments_file`) z kolumnami `segment_id`, "
            "`upstream_ids` (id odcinków wpływających; w CSV rozdzielone średnikiem, "
            "np. `3;4`, pusta komórka = źródło) i `length_km` [km]. Dane są "
            "sprawdzane: powtórzone id, nieznany odcinek powyżej i cykl dają błąd. "
            "Wynik: `method`, `n_segments`, `stream_frequency_per_km2`, `statistics` "
            "(`max_order`, `segment_counts`, `total_lengths_km`, `mean_lengths_km`, "
            "`bifurcation_ratios`, `length_ratios`, `total_stream_length_km`, "
            "`drainage_density`); słowniki mają jako klucze numery rzędów (w JSON "
            "tekstowe)."
        ),
        description_en=(
            "Orders the segments of a river network with the Strahler method (the "
            "order increases when two streams of the same, highest order meet) or the "
            "Shreve method (the order is the sum of the orders of the tributaries, "
            "i.e. the number of sources upstream of the segment) and summarizes the "
            "network: the number and the total and mean length of the segments of "
            "each order, the bifurcation ratio Rb = N_i/N_(i+1) and the length ratio "
            "Rl = mean length of order i+1 / mean length of order i (Horton's laws; "
            "meaningful for Strahler orders, formal quotients of consecutive orders "
            "for Shreve), the total stream length [km] and, with `area_km2`, the "
            "drainage density Dd = ΣL/A [km/km²] and the stream frequency Fs = "
            "number of segments/A [1/km²]. Segments are given inline (`segments`) or "
            "in a CSV/JSON file (`segments_file`) with the columns `segment_id`, "
            "`upstream_ids` (ids of the segments flowing in; in CSV separated by a "
            "semicolon, e.g. `3;4`, an empty cell = headwater) and `length_km` [km]. "
            "The data are checked: a repeated id, an unknown upstream segment and a "
            "cycle are errors. Result: `method`, `n_segments`, "
            "`stream_frequency_per_km2`, `statistics` (`max_order`, "
            "`segment_counts`, `total_lengths_km`, `mean_lengths_km`, "
            "`bifurcation_ratios`, `length_ratios`, `total_stream_length_km`, "
            "`drainage_density`); the dictionaries are keyed by the order numbers "
            "(strings in JSON)."
        ),
        function="hydrolog.operations:network_stats",
        options=(
            Option(
                name="segments",
                type="object_list",
                description=(
                    "Odcinki sieci jako lista obiektów: `segment_id` (liczba "
                    "całkowita), `upstream_ids` (lista id odcinków wpływających; "
                    "pusta albo pominięta dla źródła) i `length_km` [km]."
                ),
                description_en=(
                    "Network segments as a list of objects: `segment_id` (integer), "
                    "`upstream_ids` (list of the ids of the segments flowing in; "
                    "empty or omitted for a headwater) and `length_km` [km]."
                ),
            ),
            Option(
                name="segments_file",
                type="path",
                description=(
                    "Plik CSV albo JSON z odcinkami (kolumny `segment_id`, "
                    "`upstream_ids`, `length_km`); w CSV id w `upstream_ids` rozdziela "
                    "średnik, np. `3;4`."
                ),
                description_en=(
                    "CSV or JSON file with the segments (columns `segment_id`, "
                    "`upstream_ids`, `length_km`); in CSV the ids in `upstream_ids` "
                    "are separated by a semicolon, e.g. `3;4`."
                ),
            ),
            Option(
                name="method",
                type="choice",
                description=(
                    "Metoda nadawania rzędów: `strahler` (Strahler 1957) albo "
                    "`shreve` (Shreve 1966)."
                ),
                description_en=(
                    "Ordering method: `strahler` (Strahler 1957) or `shreve` (Shreve "
                    "1966)."
                ),
                choices=("strahler", "shreve"),
                default="strahler",
            ),
            Option(
                name="area_km2",
                type="number",
                description=(
                    "Powierzchnia zlewni; włącza obliczenie gęstości sieci rzecznej i "
                    "częstości cieków."
                ),
                description_en=(
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
    ),
)
