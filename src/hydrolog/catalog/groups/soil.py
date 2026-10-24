"""Group ``soil``: soil texture and Hydrologic Soil Groups (HSG).

The operations are in :mod:`hydrolog.operations.soil`; the raster commands need the
extra ``hydrolog[raster]``.
"""

from __future__ import annotations

from hydrolog.catalog.spec import Command, Option

_FIXTURES = "tests/fixtures"


def _amount(name: str, pl: str, en: str) -> Option:
    """One soil fraction of ``soil texture``."""
    return Option(
        name=name,
        type="number",
        description=(
            f"Zawartość {pl}, nieujemna, w dowolnej jednostce wspólnej dla `clay`, "
            "`sand` i `silt` (%, g/kg); nie musi sumować się do 100."
        ),
        description_en=(
            f"Amount of {en}, not negative, in any unit shared by `clay`, `sand` and "
            "`silt` (%, g/kg); the three need not sum to 100."
        ),
        required=True,
        minimum=0,
    )


COMMANDS: tuple[Command, ...] = (
    Command(
        name="soil texture",
        operation_id="soil_texture",
        summary=(
            "Klasa uziarnienia gleby (trójkąt USDA) i grupa hydrologiczna gleby HSG "
            "A–D z zawartości iłu, piasku i pyłu."
        ),
        summary_en=(
            "USDA soil texture class and Hydrologic Soil Group A–D from the clay, "
            "sand and silt contents."
        ),
        description=(
            "Klasyfikuje glebę z zawartości iłu (`clay`), piasku (`sand`) i pyłu "
            "(`silt`) kanonicznym trójkątem uziarnienia USDA (Soil Survey Manual): 12 "
            "klas (sand, loamy_sand, sandy_loam, loam, silt_loam, silt, "
            "sandy_clay_loam, clay_loam, silty_clay_loam, sandy_clay, silty_clay, "
            "clay), po czym przypisuje klasie grupę hydrologiczną gleby HSG metody "
            "SCS-CN (USDA-NRCS TR-55, NEH część 630 rozdz. 7): A – sand, loamy_sand; "
            "B – sandy_loam, loam, silt_loam, silt; C – sandy_clay_loam, clay_loam, "
            "silty_clay_loam; D – sandy_clay, silty_clay, clay. Tabela jest "
            "łagodniejsza niż TR-55 (sandy_loam → B zamiast A, clay_loam i "
            "silty_clay_loam → C zamiast D; decyzja Kartograf ADR-025), bo to klasy "
            "przejściowe, których "
            "grupa zależy też od struktury gleby. Zawartości są porównywane z ich "
            "sumą, więc mogą być w %, g/kg itp. (nie muszą sumować się do 100); same "
            "zera (brak danych) są błędem. Wynik: `texture_class`, `texture_code` "
            "(1–12), `hsg` (A–D) i `hsg_code` (1–4, kodowanie rastrów HSG). HSG to "
            "wejście glebowe komend `cn lookup` i `cn weighted`."
        ),
        description_en=(
            "Classifies a soil from its clay (`clay`), sand (`sand`) and silt "
            "(`silt`) contents with the canonical USDA texture triangle (Soil Survey "
            "Manual): 12 classes (sand, loamy_sand, sandy_loam, loam, silt_loam, "
            "silt, sandy_clay_loam, clay_loam, silty_clay_loam, sandy_clay, "
            "silty_clay, clay), then assigns the class its SCS-CN Hydrologic Soil "
            "Group HSG (USDA-NRCS TR-55, NEH part 630 chapter 7): A – sand, "
            "loamy_sand; B – sandy_loam, loam, silt_loam, silt; C – sandy_clay_loam, "
            "clay_loam, silty_clay_loam; D – sandy_clay, silty_clay, clay. The table "
            "is milder than TR-55 (sandy_loam → B instead of A, clay_loam and "
            "silty_clay_loam → C instead of D; Kartograf ADR-025 decision) because "
            "these are transitional classes whose group also depends on the soil "
            "structure. The amounts are compared with their total, so they may be in "
            "%, g/kg etc. (they need not sum to 100); all zeros (no data) is an "
            "error. Result: `texture_class`, `texture_code` (1–12), `hsg` (A–D) and "
            "`hsg_code` (1–4, the encoding of HSG rasters). HSG is the soil input of "
            "`cn lookup` and `cn weighted`."
        ),
        function="hydrolog.operations:soil_texture",
        options=(
            _amount("clay", "iłu (frakcja < 0,002 mm)", "clay (fraction < 0.002 mm)"),
            _amount("sand", "piasku (0,05–2 mm)", "sand (0.05–2 mm)"),
            _amount("silt", "pyłu (0,002–0,05 mm)", "silt (0.002–0.05 mm)"),
        ),
        examples=(
            {"clay": 200, "sand": 400, "silt": 400},
            {"clay": 45, "sand": 20, "silt": 35},
        ),
    ),
    Command(
        name="soil hsg",
        operation_id="soil_hsg",
        summary=(
            "Raster HSG (GeoTIFF) z rastrów iłu, piasku i pyłu, np. SoilGrids w "
            "g/kg; zapisuje plik, wymaga [raster]."
        ),
        summary_en=(
            "HSG raster (GeoTIFF) from clay, sand and silt rasters, e.g. SoilGrids "
            "in g/kg; writes a file, needs [raster]."
        ),
        description=(
            "Klasyfikuje każdą komórkę rastrów zawartości iłu, piasku i pyłu do "
            "grupy hydrologicznej gleby (trójkąt uziarnienia USDA → HSG, jak w `soil "
            "texture`) i zapisuje jednowarstwowy GeoTIFF uint8 (kompresja Deflate, "
            "nodata 0): 1 = A, 2 = B, 3 = C, 4 = D, 0 = brak danych (komórki NaN/Inf, "
            "równe tagowi nodata wejścia lub zerowe we wszystkich trzech rastrach). "
            "Kodowanie jest takie jak w Kartografie. Trzy wejścia muszą mieć tę samą "
            "siatkę (CRS, transformację i rozmiar) i dowolną wspólną jednostkę, np. "
            "g/kg z SoilGrids; nie są przepróbkowywane, inna siatka to `data_error` "
            "(przepróbuj je np. gdalwarp). Istniejący plik wyjściowy jest zastępowany, "
            "brakujące katalogi są tworzone. Wymaga opcjonalnych pakietów rasterio i "
            "pyproj (`pip install hydrolog[raster]`), inaczej `missing_dependency`. "
            "Wynik: `output_path`, `shape` (wiersze, kolumny), `crs` i `counts` "
            "(liczba komórek A, B, C, D i nodata); zapisany plik jest w `files`. "
            "Dalszy krok: `soil hsg-stats`."
        ),
        description_en=(
            "Classifies every cell of the clay, sand and silt rasters into a "
            "Hydrologic Soil Group (USDA texture triangle → HSG, as in `soil "
            "texture`) and writes a single-band uint8 GeoTIFF (Deflate compression, "
            "nodata 0): 1 = A, 2 = B, 3 = C, 4 = D, 0 = no data (NaN/Inf cells, "
            "cells equal to the nodata tag of an input, or zero in all three "
            "rasters). The encoding is the same as in Kartograf. The three inputs "
            "must share one grid (CRS, transform and size) and any common unit, e.g. "
            "the g/kg of SoilGrids; they are not resampled, a different grid is a "
            "`data_error` (resample them, e.g. with gdalwarp). An existing output "
            "file is replaced, missing directories are created. Needs the optional "
            "packages rasterio and pyproj (`pip install hydrolog[raster]`), otherwise "
            "`missing_dependency`. Result: `output_path`, `shape` (rows, columns), "
            "`crs` and `counts` (number of cells A, B, C, D and nodata); the written "
            "file is listed in `files`. Next step: `soil hsg-stats`."
        ),
        function="hydrolog.operations:soil_hsg",
        options=(
            Option(
                name="clay_path",
                type="path",
                description="Raster zawartości iłu (pierwsze pasmo), np. z SoilGrids.",
                description_en="Clay amount raster (first band), e.g. from SoilGrids.",
                required=True,
            ),
            Option(
                name="sand_path",
                type="path",
                description=(
                    "Raster zawartości piasku (pierwsze pasmo), ta sama siatka co "
                    "`clay_path`."
                ),
                description_en=(
                    "Sand amount raster (first band), on the same grid as `clay_path`."
                ),
                required=True,
            ),
            Option(
                name="silt_path",
                type="path",
                description=(
                    "Raster zawartości pyłu (pierwsze pasmo), ta sama siatka co "
                    "`clay_path`."
                ),
                description_en=(
                    "Silt amount raster (first band), on the same grid as `clay_path`."
                ),
                required=True,
            ),
            Option(
                name="output_path",
                type="path",
                description=(
                    "Plik GeoTIFF z wynikiem (kody HSG 1–4, 0 = brak danych); "
                    "istniejący plik jest zastępowany, nie może być jednym z wejść."
                ),
                description_en=(
                    "GeoTIFF file to write (HSG codes 1–4, 0 = no data); an existing "
                    "file is replaced, it must not be one of the inputs."
                ),
                required=True,
                writes=True,
            ),
        ),
        writes=True,
        examples=(
            {
                "clay_path": f"{_FIXTURES}/hsg_clay.tif",
                "sand_path": f"{_FIXTURES}/hsg_sand.tif",
                "silt_path": f"{_FIXTURES}/hsg_silt.tif",
                "output_path": "hsg.tif",
            },
        ),
    ),
    Command(
        name="soil hsg-stats",
        operation_id="soil_hsg_stats",
        summary=(
            "Powierzchnie grup HSG A–D z rastra HSG, opcjonalnie w prostokącie bbox; "
            "wymaga [raster]."
        ),
        summary_en=(
            "Areas of the HSG groups A–D from an HSG raster, optionally inside a "
            "bbox; needs [raster]."
        ),
        description=(
            "Liczy z rastra HSG (kody 1–4 = A–D, 0 = brak danych; wynik `soil hsg` "
            "albo Kartografu) liczbę komórek, powierzchnię [m², ha] i udział [%] "
            "każdej grupy: udział grup A–D to procent powierzchni z danymi, a udział "
            "braku danych – procent całej powierzchni. Powierzchnie komórek są "
            "podawane w m² niezależnie od układu rastra: dla układu geograficznego "
            "(np. EPSG:4326 w SoilGrids) liczone geodezyjnie na elipsoidzie WGS84 dla "
            "każdego wiersza, dla układu rzutowanego z transformacji afinicznej (bez "
            "poprawki na zniekształcenia odwzorowania). Opcjonalny `bbox` (min_x, "
            "min_y, max_x, max_y; x = easting lub długość, y = northing lub "
            "szerokość) w układzie `bbox_crs` (domyślnie układ rastra) ogranicza "
            "obszar: komórki przecięte krawędzią liczą się swoim udziałem w "
            "prostokącie (z dokładnością 1 % komórki). Prostokąt poza rastrem daje "
            "zerowe powierzchnie i ostrzeżenie w `notices`. Wynik: `groups` (A–D: "
            "`count`, `area_m2`, `area_ha`, `percent`), `nodata`, `total_area_m2` i "
            "`valid_area_m2`; powierzchnie grup są wagami dla `cn weighted`. Wymaga "
            "[raster] (`pip install hydrolog[raster]`), inaczej "
            "`missing_dependency`."
        ),
        description_en=(
            "Computes from an HSG raster (codes 1–4 = A–D, 0 = no data; the result of "
            "`soil hsg` or of Kartograf) the number of cells, the area [m², ha] and "
            "the share [%] of each group: the share of groups A–D is the percent of "
            "the area with data, the share of no data is the percent of the whole "
            "area. Cell areas are given in m² whatever the raster CRS: for a "
            "geographic CRS (e.g. EPSG:4326 of SoilGrids) they are computed "
            "geodetically on the WGS84 ellipsoid for every row, for a projected CRS "
            "from the affine transform (without correcting the distortion of the "
            "projection). An optional `bbox` (min_x, min_y, max_x, max_y; x = "
            "easting or longitude, y = northing or latitude) in the CRS `bbox_crs` "
            "(default: the CRS of the raster) limits the area: cells cut by its edges "
            "count with their share inside the box (accuracy 1 % of a cell). A box "
            "outside the raster gives zero areas and a warning in `notices`. Result: "
            "`groups` (A–D: `count`, `area_m2`, `area_ha`, `percent`), `nodata`, "
            "`total_area_m2` and `valid_area_m2`; the group areas are the weights of "
            "`cn weighted`. Needs [raster] (`pip install hydrolog[raster]`), "
            "otherwise `missing_dependency`."
        ),
        function="hydrolog.operations:soil_hsg_stats",
        options=(
            Option(
                name="hsg_path",
                type="path",
                description=(
                    "Raster HSG (GeoTIFF): kody 1–4 = A–D, 0 = brak danych; np. wynik "
                    "`soil hsg`."
                ),
                description_en=(
                    "HSG raster (GeoTIFF): codes 1–4 = A–D, 0 = no data; e.g. the "
                    "result of `soil hsg`."
                ),
                required=True,
            ),
            Option(
                name="bbox",
                type="number_list",
                description=(
                    "Obszar zainteresowania: cztery liczby min_x, min_y, max_x, max_y "
                    "(x = easting lub długość, y = northing lub szerokość); domyślnie "
                    "cały raster."
                ),
                description_en=(
                    "Area of interest: four numbers min_x, min_y, max_x, max_y (x = "
                    "easting or longitude, y = northing or latitude); default: the "
                    "whole raster."
                ),
            ),
            Option(
                name="bbox_crs",
                type="string",
                description=(
                    "Układ współrzędnych `bbox`, np. `EPSG:2180`; domyślnie układ "
                    "rastra. Wymaga `bbox`."
                ),
                description_en=(
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
    ),
)
