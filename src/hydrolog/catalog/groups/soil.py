"""Group ``soil``: soil texture and Hydrologic Soil Groups (HSG).

The operations are in :mod:`hydrolog.operations.soil`; the raster commands need the
extra ``hydrolog[raster]``.
"""

from __future__ import annotations

from hydrolog.catalog.groups._output import CHECK, FORCE
from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"


def _amount(name: str, pl: str, en: str) -> Option:
    """One soil fraction of ``soil texture``."""
    return Option(
        name=name,
        type="number",
        description_pl=(
            f"Zawartość {pl}, nieujemna, w dowolnej jednostce wspólnej dla `clay`, "
            "`sand` i `silt` (%, g/kg); nie musi sumować się do 100."
        ),
        description=(
            f"Amount of {en}, not negative, in any unit shared by `clay`, `sand` and "
            "`silt` (%, g/kg); the three need not sum to 100."
        ),
        required=True,
        minimum=0,
    )


COMMANDS: tuple[Command, ...] = (
    Command(
        name="soil texture",
        operation_id="hydrolog_soil_texture",
        summary_pl=(
            "Oblicz klasę uziarnienia USDA i grupę hydrologiczną gleby A-D dla jednej "
            "próbki gleby."
        ),
        summary=(
            "Compute the USDA soil texture class and Hydrologic Soil Group A-D of one "
            "soil sample."
        ),
        description_pl=(
            "Klasyfikuje zawartości iłu, piasku i pyłu trójkątem uziarnienia USDA (12 "
            "klas), po czym przypisuje klasie grupę HSG metody SCS-CN. Dla jednej "
            "próbki; dla rastrów użyj `soil hsg`. Zawartości mogą być w dowolnej "
            "wspólnej jednostce; same zera to błąd."
        ),
        description=(
            "Classify clay, sand and silt contents with the USDA texture triangle (12 "
            "classes), then map the class to the SCS-CN group HSG. Use for one sample; "
            "for rasters use `soil hsg`. Amounts may be in any shared unit; all zeros "
            "is an error."
        ),
        function="hydrolog.operations.soil_texture",
        options=(
            _amount("clay", "iłu (frakcja < 0,002 mm)", "clay (fraction < 0.002 mm)"),
            _amount("sand", "piasku (0,05–2 mm)", "sand (0.05–2 mm)"),
            _amount("silt", "pyłu (0,002–0,05 mm)", "silt (0.002–0.05 mm)"),
        ),
        examples=(
            {"clay": 200, "sand": 400, "silt": 400},
            {"clay": 45, "sand": 20, "silt": 35},
        ),
        result_schema="hydrolog-soil-texture/1",
        rules=(
            "Give clay, sand and silt in one shared unit; they need not sum to 100.",
            "Pass the resulting `hsg` to `cn lookup` or `cn weighted`.",
        ),
        rules_pl=(
            (
                "Podaj ił, piasek i pył w jednej jednostce; nie muszą sumować się "
                "do 100."
            ),
            "Przekaż wynikowe `hsg` do `cn lookup` lub `cn weighted`.",
        ),
        errors=("validation_error",),
        example_results=(
            {"texture_class": "loam", "texture_code": 4, "hsg": "B", "hsg_code": 2},
            {"texture_class": "clay", "texture_code": 12, "hsg": "D", "hsg_code": 4},
        ),
    ),
    Command(
        name="soil hsg",
        operation_id="hydrolog_soil_hsg",
        summary_pl=(
            "Zapisz GeoTIFF z grupami HSG sklasyfikowanymi z rastrów iłu, piasku i "
            "pyłu."
        ),
        summary="Write an HSG GeoTIFF classified from clay, sand and silt rasters.",
        description_pl=(
            "Klasyfikuje każdą komórkę trójkątem uziarnienia USDA do kodów HSG 1-4 = "
            "A-D, 0 = brak danych. Dla rastrów typu SoilGrids; dla jednej próbki użyj "
            "`soil texture`. Wejścia muszą mieć tę samą siatkę (bez przepróbkowania). "
            "Wymaga [raster]; pobieranie danych to Kartograf."
        ),
        description=(
            "Classify each cell with the USDA texture triangle into HSG codes 1-4 = "
            "A-D, 0 = no data. Use for SoilGrids-like rasters; for one sample use `soil"
            " texture`. Inputs must share one grid (no resampling). Needs [raster]; "
            "data download is Kartograf."
        ),
        function="hydrolog.operations.soil_hsg",
        options=(
            Option(
                name="clay_path",
                type="path",
                path_role="input",
                description_pl=(
                    "Raster zawartości iłu (pierwsze pasmo), np. z SoilGrids."
                ),
                description="Clay amount raster (first band), e.g. from SoilGrids.",
                required=True,
            ),
            Option(
                name="sand_path",
                type="path",
                path_role="input",
                description_pl=(
                    "Raster zawartości piasku (pierwsze pasmo), ta sama siatka co "
                    "`clay_path`."
                ),
                description=(
                    "Sand amount raster (first band), on the same grid as `clay_path`."
                ),
                required=True,
            ),
            Option(
                name="silt_path",
                type="path",
                path_role="input",
                description_pl=(
                    "Raster zawartości pyłu (pierwsze pasmo), ta sama siatka co "
                    "`clay_path`."
                ),
                description=(
                    "Silt amount raster (first band), on the same grid as `clay_path`."
                ),
                required=True,
            ),
            Option(
                name="output",
                type="path",
                description_pl=(
                    "Plik GeoTIFF z wynikiem (kody HSG 1–4, 0 = brak danych); "
                    "istniejący plik jest zastępowany tylko z `force`, nie może być "
                    "jednym z wejść."
                ),
                description=(
                    "GeoTIFF file to write (HSG codes 1–4, 0 = no data); an existing "
                    "file is replaced only with `force`, it must not be one of the "
                    "inputs."
                ),
                required=True,
                path_role="output",
            ),
            FORCE,
            CHECK,
        ),
        examples=(
            {
                "clay_path": f"{_FIXTURES}/hsg_clay.tif",
                "sand_path": f"{_FIXTURES}/hsg_sand.tif",
                "silt_path": f"{_FIXTURES}/hsg_silt.tif",
                "output": "hsg.tif",
            },
        ),
        result_schema="hydrolog-soil-hsg/1",
        rules=(
            "Give three rasters on one grid and in one unit.",
            "Choose a new `output`; it must not be an input.",
            "Check `counts` for nodata cells; follow with `soil hsg-stats`.",
        ),
        rules_pl=(
            "Podaj trzy rastry na jednej siatce i w jednej jednostce.",
            "Wybierz nowy `output`; nie może być wejściem.",
            "Sprawdź `counts` pod kątem komórek bez danych; dalej `soil hsg-stats`.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "forbidden",
            "missing_dependency",
            "io_error",
            "conflict",
        ),
        example_results=(
            {
                "shape": [6, 8],
                "crs": "EPSG:2180",
                "counts": {"A": 12, "B": 12, "C": 12, "D": 11, "nodata": 1},
            },
        ),
    ),
    Command(
        name="soil hsg-stats",
        operation_id="hydrolog_soil_hsg_stats",
        summary_pl=(
            "Oblicz powierzchnie i udziały grup HSG A-D z rastra HSG, opcjonalnie w "
            "prostokącie bbox."
        ),
        summary="Compute areas and shares of the HSG groups A-D from an HSG raster.",
        description_pl=(
            "Liczy komórki, powierzchnię [m2, ha] i udział [%] każdej grupy rastra HSG "
            "(`soil hsg` lub Kartograf), opcjonalnie w `bbox`. Powierzchnie grup to "
            "wagi dla `cn weighted`. Wymaga [raster]; prostokąt poza rastrem dodaje "
            "ostrzeżenie w `notices`."
        ),
        description=(
            "Count cells, area [m2, ha] and share [%] of each group in an HSG raster "
            "(`soil hsg` or Kartograf), optionally inside `bbox`. The group areas are "
            "the weights of `cn weighted`. Needs [raster]; a box outside the raster "
            "adds a warning to `notices`."
        ),
        function="hydrolog.operations.soil_hsg_stats",
        options=(
            Option(
                name="hsg_path",
                type="path",
                path_role="input",
                description_pl=(
                    "Raster HSG (GeoTIFF): kody 1–4 = A–D, 0 = brak danych; np. wynik "
                    "`soil hsg`."
                ),
                description=(
                    "HSG raster (GeoTIFF): codes 1–4 = A–D, 0 = no data; e.g. the "
                    "result of `soil hsg`."
                ),
                required=True,
            ),
            Option(
                name="bbox",
                type="number_list",
                description_pl=(
                    "Obszar zainteresowania: cztery liczby min_x, min_y, max_x, max_y "
                    "(x = easting lub długość, y = northing lub szerokość); domyślnie "
                    "cały raster."
                ),
                description=(
                    "Area of interest: four numbers min_x, min_y, max_x, max_y (x = "
                    "easting or longitude, y = northing or latitude); default: the "
                    "whole raster."
                ),
            ),
            Option(
                name="bbox_crs",
                type="string",
                description_pl=(
                    "Układ współrzędnych `bbox`, np. `EPSG:2180`; domyślnie układ "
                    "rastra. Wymaga `bbox`."
                ),
                description=(
                    "CRS of `bbox`, e.g. `EPSG:2180`; default: the CRS of the "
                    "raster. Needs `bbox`."
                ),
            ),
        ),
        examples=(
            {"hsg_path": f"{_FIXTURES}/hsg_result.tif"},
            {
                "hsg_path": f"{_FIXTURES}/hsg_result.tif",
                "bbox": [500250.0, 598750.0, 501250.0, 600000.0],
                "bbox_crs": "EPSG:2180",
            },
        ),
        result_schema="hydrolog-soil-hsg-stats/1",
        rules=(
            "Give `bbox_crs` when `bbox` is not in the raster CRS.",
            "Read `notices` for a box outside the raster.",
            "Use `groups` areas as weights in `cn weighted`.",
        ),
        rules_pl=(
            "Podaj `bbox_crs`, gdy `bbox` nie jest w układzie rastra.",
            "Sprawdź `notices` pod kątem prostokąta poza rastrem.",
            "Użyj powierzchni z `groups` jako wag w `cn weighted`.",
        ),
        errors=(
            "validation_error",
            "not_found",
            "data_error",
            "forbidden",
            "missing_dependency",
        ),
        example_results=(
            {
                "nodata": {
                    "count": 1,
                    "area_m2": 62500.0,
                    "area_ha": 6.25,
                    "percent": 2.08333,
                },
                "total_area_m2": 3000000.0,
                "valid_area_m2": 2937500.0,
            },
            {
                "nodata": {"count": 0, "area_m2": 0.0, "area_ha": 0.0, "percent": 0.0},
                "total_area_m2": 1250000.0,
                "valid_area_m2": 1250000.0,
            },
        ),
    ),
)
