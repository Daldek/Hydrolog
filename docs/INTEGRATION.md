# Integracja Hydrograf ↔ Hydrolog

**Data utworzenia:** 2026-01-20
**Ostatnia aktualizacja:** 2026-10-19 (Hydrolog 1.0.0: Retman, klienci MCP, migracja HSG, eksport IMGWTools)
**Status:** W trakcie implementacji (Hydrolog - gotowy; Hydrograf - do implementacji)

---

## Cel

Umożliwić łatwą wymianę danych między Hydrografem (analizy przestrzenne GIS) a Hydrologiem (obliczenia hydrologiczne), z możliwością integracji z innymi systemami: platformą agentową Retman, klientami MCP (np. Claude Code) oraz narzędziami IMGWTools i Kartograf, które dostarczają dane wejściowe. Hydrolog niczego nie pobiera i nie zależy od żadnego z tych narzędzi - wymiana odbywa się przez pliki (JSON, CSV, GeoTIFF).

---

## Podział odpowiedzialności

```
┌─────────────────────────────────────────────────────────────────┐
│                         HYDROGRAF                               │
│  Odpowiedzialność: ANALIZY PRZESTRZENNE (GIS)                   │
│                                                                 │
│  - Wyznaczanie zlewni z NMT (flow network)                      │
│  - Obliczanie parametrów geometrycznych z boundary/cells        │
│  - Obliczanie statystyk wysokości z DEM                         │
│  - Obliczanie CN z pokrycia terenu                              │
│  - Interpolacja opadów (IDW/Thiessen)                           │
│                                                                 │
│  OUTPUT: JSON zgodny ze schematem WatershedParameters           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  STANDARYZOWANY FORMAT JSON   │
              │  (WatershedParameters schema) │
              └───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         HYDROLOG                                │
│  Odpowiedzialność: OBLICZENIA HYDROLOGICZNE                     │
│                                                                 │
│  - Czas koncentracji (Kirpich, SCS Lag, Giandotti, FAA,         │
│    Kerby, Kerby-Kirpich)                                        │
│  - Hydrogramy jednostkowe (SCS, Nash, Clark, Snyder)            │
│  - Transformacja opad→odpływ (splot)                            │
│  - Wskaźniki kształtu zlewni                                    │
│  - Krzywa hipsograficzna                                        │
│                                                                 │
│  INPUT: WatershedParameters.from_dict(json_data)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Format wymiany danych

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WatershedParameters",
  "description": "Standaryzowany format parametrów zlewni dla integracji GIS ↔ Hydrolog",
  "type": "object",
  "required": ["area_km2", "perimeter_km", "length_km", "elevation_min_m", "elevation_max_m"],
  "properties": {
    "name": {"type": "string", "description": "Nazwa zlewni"},
    "area_km2": {"type": "number", "minimum": 0, "description": "Powierzchnia [km²]"},
    "perimeter_km": {"type": "number", "minimum": 0, "description": "Obwód [km]"},
    "length_km": {"type": "number", "minimum": 0, "description": "Długość zlewni [km]"},
    "elevation_min_m": {"type": "number", "description": "Min wysokość [m n.p.m.]"},
    "elevation_max_m": {"type": "number", "description": "Max wysokość [m n.p.m.]"},
    "elevation_mean_m": {"type": "number", "description": "Średnia wysokość [m n.p.m.]"},
    "mean_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Średni spadek [m/m]"},
    "channel_length_km": {"type": "number", "minimum": 0, "description": "Długość cieku [km]"},
    "channel_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Spadek cieku [m/m]"},
    "cn": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Curve Number"},
    "source": {"type": "string", "description": "Źródło danych"},
    "crs": {"type": "string", "description": "Układ współrzędnych"},

    "__comment_v063": "Pola opcjonalne dodane w v0.6.3+",
    "runoff_coeff": {"type": "number", "exclusiveMinimum": 0, "maximum": 1.0, "description": "Współczynnik spływu C dla metody FAA"},
    "retardance": {"type": "number", "exclusiveMinimum": 0, "description": "Współczynnik szorstkości Kerby (0.02-0.80)"},
    "overland_length_km": {"type": "number", "exclusiveMinimum": 0, "description": "Długość spływu powierzchniowego [km] (Kerby-Kirpich)"},
    "overland_slope_m_per_m": {"type": "number", "minimum": 0, "description": "Spadek spływu powierzchniowego [m/m] (Kerby-Kirpich)"},
    "Lc_km": {"type": "number", "exclusiveMinimum": 0, "description": "Odległość do centroidu zlewni wzdłuż cieku [km] (Nash/Snyder)"},
    "manning_n": {"type": "number", "exclusiveMinimum": 0, "description": "Współczynnik szorstkości Manninga (Nash)"},
    "urban_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "Procent obszaru zurbanizowanego [%] (Nash)"},
    "forest_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "Procent obszaru zalesionego [%] (Nash)"}
  }
}
```

### Przykład JSON

```json
{
  "name": "Zlewnia potoku X",
  "area_km2": 45.3,
  "perimeter_km": 32.1,
  "length_km": 12.5,
  "elevation_min_m": 150.0,
  "elevation_max_m": 520.0,
  "elevation_mean_m": 340.0,
  "mean_slope_m_per_m": 0.025,
  "cn": 72,
  "source": "Hydrograf",
  "crs": "EPSG:2180"
}
```

---

## Implementacja w Hydrologie

### Nowa klasa: `WatershedParameters`

**Plik:** `hydrolog/morphometry/watershed_params.py`

**Status:** ✅ Zaimplementowane

```python
from hydrolog.morphometry import WatershedParameters

# Tworzenie z dict (np. z API response)
params = WatershedParameters.from_dict(json_data)

# Tworzenie z JSON string
params = WatershedParameters.from_json(json_string)

# Eksport
d = params.to_dict()
s = params.to_json(indent=2)

# Konwersja do klas Hydrologa
geom = params.to_geometry()      # WatershedGeometry
terrain = params.to_terrain()    # TerrainAnalysis

# Obliczenia
tc = params.calculate_tc(method="kirpich")

# Właściwości obliczane
width = params.width_km    # A / L
relief = params.relief_m   # max - min
```

### Metody `from_dict()` w istniejących klasach

**Status:** ✅ Zaimplementowane

**Pliki:**
- `hydrolog/morphometry/geometric.py` - `WatershedGeometry.from_dict()`
- `hydrolog/morphometry/terrain.py` - `TerrainAnalysis.from_dict()`

> **Powiązane dokumenty:**
> - Szczegóły matematyczne modeli UH i ścieżek obliczeniowych: patrz [COMPUTATION_PATHS.md](COMPUTATION_PATHS.md)
> - Zakres projektu i granice odpowiedzialności: patrz [SCOPE.md](SCOPE.md)

---

## Implementacja w Hydrografie

> **Uwaga:** Te zmiany będą implementowane przy okazji CP3 (Hydrograph generation).

### Nowy moduł: `backend/core/morphometry.py`

**Status:** 🔲 Do zaimplementowania

```python
"""Morphometric calculations from watershed cells."""

from shapely.geometry import Polygon
from core.watershed import FlowCell
import numpy as np

def calculate_perimeter_km(boundary: Polygon) -> float:
    """Calculate watershed perimeter from boundary polygon."""
    return boundary.length / 1000  # m -> km

def calculate_watershed_length_km(
    cells: list[FlowCell],
    outlet: FlowCell
) -> float:
    """Calculate watershed length (max distance from outlet)."""
    distances = [
        ((c.x - outlet.x)**2 + (c.y - outlet.y)**2)**0.5
        for c in cells
    ]
    return max(distances) / 1000  # m -> km

def calculate_elevation_stats(cells: list[FlowCell]) -> dict:
    """Calculate elevation statistics from cells."""
    elevations = np.array([c.elevation for c in cells])
    areas = np.array([c.cell_area for c in cells])

    return {
        "elevation_min_m": float(np.min(elevations)),
        "elevation_max_m": float(np.max(elevations)),
        "elevation_mean_m": float(np.average(elevations, weights=areas)),
    }

def calculate_mean_slope(cells: list[FlowCell]) -> float:
    """Calculate area-weighted mean slope."""
    valid = [(c.slope, c.cell_area) for c in cells if c.slope is not None]
    if not valid:
        return 0.0
    slopes, areas = zip(*valid)
    return float(np.average(slopes, weights=areas)) / 100  # % -> m/m

def build_morphometric_params(
    cells: list[FlowCell],
    boundary: Polygon,
    outlet: FlowCell,
    cn: int | None = None,
) -> dict:
    """
    Build complete morphometric parameters dictionary.

    Returns dict compatible with Hydrolog's WatershedParameters.from_dict()
    """
    elev_stats = calculate_elevation_stats(cells)

    return {
        "area_km2": sum(c.cell_area for c in cells) / 1_000_000,
        "perimeter_km": calculate_perimeter_km(boundary),
        "length_km": calculate_watershed_length_km(cells, outlet),
        "elevation_min_m": elev_stats["elevation_min_m"],
        "elevation_max_m": elev_stats["elevation_max_m"],
        "elevation_mean_m": elev_stats["elevation_mean_m"],
        "mean_slope_m_per_m": calculate_mean_slope(cells),
        "cn": cn,
        "source": "Hydrograf",
        "crs": "EPSG:2180",
    }
```

### Rozszerzenie schematów Pydantic

**Plik:** `backend/models/schemas.py`

```python
class MorphometricParameters(BaseModel):
    """
    Morphometric parameters compatible with Hydrolog.

    This schema matches Hydrolog's WatershedParameters dataclass.
    """
    # Required
    area_km2: float = Field(..., ge=0)
    perimeter_km: float = Field(..., ge=0)
    length_km: float = Field(..., ge=0)
    elevation_min_m: float
    elevation_max_m: float

    # Optional
    elevation_mean_m: float | None = None
    mean_slope_m_per_m: float | None = None
    channel_length_km: float | None = None
    channel_slope_m_per_m: float | None = None
    cn: int | None = Field(None, ge=0, le=100)
    source: str | None = "Hydrograf"
    crs: str | None = "EPSG:2180"

class WatershedResponse(BaseModel):
    # ... existing fields ...
    morphometry: MorphometricParameters | None = None  # NEW
```

### Rozszerzenie endpointu

**Plik:** `backend/api/endpoints/watershed.py`

```python
from core.morphometry import build_morphometric_params

@router.post("/delineate-watershed")
def delineate_watershed(...):
    # ... existing code ...

    # NEW: Calculate morphometric parameters
    morph_dict = build_morphometric_params(cells, boundary, outlet_cell)

    response = DelineateResponse(
        watershed=WatershedResponse(
            # ... existing fields ...
            morphometry=MorphometricParameters(**morph_dict),  # NEW
        )
    )
```

---

## Przykład pełnej integracji

```python
# === W Hydrografie (lub innym systemie GIS) ===
import requests

# 1. Wyznacz zlewnię
response = requests.post(
    "http://localhost:8000/api/delineate-watershed",
    json={"latitude": 52.23, "longitude": 21.01}
)
data = response.json()

# 2. Pobierz parametry morfometryczne
morph_json = data["watershed"]["morphometry"]


# === W dowolnej aplikacji używającej Hydrologa ===
from hydrolog.morphometry import WatershedParameters
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# 3. Zaimportuj parametry do Hydrologa
params = WatershedParameters.from_dict(morph_json)

# 4. Oblicz czas koncentracji
tc = params.calculate_tc(method="kirpich")

# 5. Wygeneruj hydrogram
generator = HydrographGenerator(
    area_km2=params.area_km2,
    cn=params.cn,
    tc_min=tc,
)
hietogram_gen = BetaHietogram()
hietogram = hietogram_gen.generate(total_mm=50, duration_min=60, timestep_min=5)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
```

---

## Hydrolog 1.0.0: warstwa operacji, katalog komend i pliki

Od v1.0.0 Hydrolog ma jeden katalog komend (`hydrolog.catalog`, 37 komend, lista: `hydrolog commands list`), z którego powstają: warstwa operacji w Pythonie (`hydrolog.operations`), CLI `hydrolog`, serwer MCP (`hydrolog mcp`) i przewodniki dla agentów (`AGENTS.md`, `llms.txt`). Klasy biblioteki (`HydrographGenerator`, `WatershedParameters`, ...) działają jak dotąd; poniższe sekcje dotyczą nowych sposobów integracji.

### Retman (handlery obliczeń)

Retman wywołuje Hydrologa przez warstwę komend, a nie przez klasy biblioteki.

- **Warstwa operacji:** `hydrolog.operations` - po jednej publicznej, otypowanej funkcji na komendę (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...), argumenty nazwane tak jak opcje komendy, dokumentacja NumPy (z niej korzysta `retman-scaffold`). Funkcja zwraca obiekt wynikowy z `to_dict()`/`to_json()` albo `OperationOutput` (`result`, `notices`, `files`), gdy komenda ma ostrzeżenia lub zapisuje pliki.
- **Katalog i koperta:** `hydrolog.catalog.run_command("<grupa> <komenda>", {opcje})` waliduje opcje, uruchamia operację i zwraca kopertę `hydrolog-result/1` (`inputs`, `result`, `files` z SHA-256, `notices`; `to_dict()`, `to_json()`). Schemat opcji (JSON Schema): `command_schema()`, `hydrolog commands schema`. Błędy to wyjątki `HydrologError` z `code`, `hint` i `details` (rejestr `ERROR_CODES`; dokument `hydrolog-error/1`).
- **`catchment_characteristics`:** proponowany format to `WatershedParameters` JSON (`WatershedParameters.to_json()`; wymagane `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`). Plik trafia do komend jako `watershed_file`, a `WatershedParameters.from_dict()` ignoruje dodatkowy klucz `schema` (np. `"hydrolog-catchment/1"`) dopisany przez narzędzia katalogowe.
- **Wejścia i wyjścia przez pliki:** serie (`input_file` + `value_column`/`date_column`), stacje opadowe (`stations_file`), odcinki sieci (`segments_file`), zlewnia (`watershed_file`) jako CSV/JSON; wyniki zapisujące pliki (`soil hsg` - GeoTIFF, `report generate` - Markdown) podają je w `files`. Retman nie musi wklejać serii do argumentów.
- **Wersje:** manifest narzędzia w Retmanie: `supported_versions=">=1.0,<2"` (od 1.0.0 obowiązuje wersjonowanie semantyczne: opcje, nazwy komend i kształt kopert nie zmieniają się niezgodnie wstecz w serii 1.x).

```python
from hydrolog.catalog import run_command

result = run_command(
    "hydrograph generate",
    {
        "watershed_file": "/dane/zlewnie/potok_x.json",
        "tc_method": "kirpich",
        "hietogram_type": "beta",
        "total_mm": 50,
        "duration_min": 60,
    },
)
print(result.result.peak_discharge_m3s, [n.text for n in result.notices])  # obiekt wynikowy
envelope = result.to_dict()  # koperta hydrolog-result/1 jako słownik (result.to_json() - tekst)
```

### Klienci MCP (Claude Code i inni)

Serwer MCP udostępnia każdą komendę katalogu jako narzędzie (nazwa = `operation_id`, np. `tc_kirpich`). Wymaga dodatku `hydrolog[mcp]` (`mcp>=2.3,<3`) i działa na stdio.

```bash
pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"

# Claude Code
claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data
```

Inne klienty MCP (plik konfiguracji, np. `.mcp.json`):

```json
{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}}}
```

- `--allow-dir DIR` (można powtórzyć) wskazuje katalogi, w których narzędzia mogą czytać i zapisywać pliki; ścieżki spoza nich kończą się błędem `forbidden`. Bez `--allow-dir` komendy z opcjami typu ścieżka są odrzucane, komendy bez plików (np. `tc_kirpich`, `cn_lookup`) działają.
- `--lang pl|en` wybiera język opisów narzędzi.
- Sukces: `structuredContent` = koperta `hydrolog-result/1`; błąd: `isError: true` z dokumentem `hydrolog-error/1`.
- Przewodnik dla agentów: `AGENTS.md` w repozytorium (generowany: `hydrolog commands guide --format agents --lang pl`).

### IMGWTools: eksport szeregu → komendy `stats`

Hydrolog nie pobiera danych IMGW. Szereg dobowy eksportuje IMGWTools (`series export`) do pliku CSV z jednostkami w nagłówku (`Q [m3/s]`), kolumną `date`, flagami wartości i atrybucją. Plik wczytuje się bez przetwarzania (separator przecinek lub średnik, UTF-8; kolumny podaje się nazwą bez jednostki: `Q` znajduje `Q [m3/s]`):

```bash
hydrolog stats flood-frequency --input-file q_dobowe.csv --value-column Q --date-column date \
    --distribution all --return-periods 10,50,100
hydrolog stats low-flow --input-file q_dobowe.csv --value-column Q --date-column date
hydrolog stats characteristic --input-file q_dobowe.csv --value-column Q --date-column date
hydrolog stats monthly --input-file q_dobowe.csv --value-column Q --date-column date
```

Maksima i minima roczne wybierane są z lat hydrologicznych (XI-X); seria krótsza niż zalecana daje ostrzeżenie w `notices`. Te same komendy są dostępne w Pythonie (`hydrolog.operations.stats_flood_frequency(input_file=..., value_column="Q", date_column="date")`) i MCP (`stats_flood_frequency`).

### Hydrograf: migracja HSG z Kartografa do Hydrologa

Dotychczas grupy hydrologiczne gleb liczył Kartograf (`HSGCalculator`, `calculate_hsg`; w Hydrografie: `backend/core/cn_calculator.py` i `scripts/bootstrap.py`). Od Hydrologa 1.0.0 obliczanie HSG należy do Hydrologa (moduł `hydrolog.soil`; reguły i mapowanie tekstura → HSG przeniesione z Kartografa 0.8.0, ADR-025), a Kartograf zostaje przy samym pobieraniu rastrów (`download_soil`). Hydrolog nie zależy od Kartografa (dawny dodatek `hydrolog[spatial]` usunięto).

Dotychczasowa ścieżka w Hydrografie:

```python
from kartograf.hydrology import HSGCalculator

hsg_calc = HSGCalculator()
hsg_calc.calculate_hsg_by_bbox(bbox, hsg_path)      # pobranie + obliczenie HSG
hsg_stats = hsg_calc.get_hsg_statistics(hsg_path)   # udziały grup
```

Docelowa ścieżka (Kartograf `download_soil` → Hydrolog `hsg_from_rasters` → `hsg_statistics` → CN ważone):

```python
from kartograf import BBox, download_soil
from hydrolog.runoff import calculate_weighted_cn, get_cn
from hydrolog.soil import hsg_from_rasters, hsg_statistics   # wymaga hydrolog[raster]

bbox = BBox(626000, 480000, 628000, 482000, "EPSG:2180")

# 1. Kartograf: trzy rastry SoilGrids (g/kg) - ił, piasek, pył (te same: warstwa, głębokość, statystyka)
paths = {}
for prop in ("clay", "sand", "silt"):
    report = download_soil(
        output_dir="/dane/kartograf", bbox=bbox,
        property=prop, depth="0-5cm", stat="mean",
    )
    paths[prop] = report.files[0].file.path

# 2. Hydrolog: raster HSG (GeoTIFF uint8: 0 - brak danych, 1-4 to A-D)
hsg_from_rasters(paths["clay"], paths["sand"], paths["silt"], output_path="/dane/hydrolog/hsg.tif")

# 3. Hydrolog: powierzchnie grup A-D (opcjonalnie tylko prostokąt: bbox=..., bbox_crs=...)
stats = hsg_statistics("/dane/hydrolog/hsg.tif")

# 4. CN ważone powierzchnią: część to para (CN, powierzchnia); CN z tablic TR-55 dla pokrycia terenu zlewni
parts = [
    (get_cn(group, "meadow", "good"), group_stats.area_ha)
    for group, group_stats in stats.groups.items()
    if group_stats.area_ha > 0
]
cn = calculate_weighted_cn(parts)
```

- Rastry iłu, piasku i pyłu muszą mieć ten sam układ współrzędnych, siatkę i rozmiar (inaczej `InputDataError`, kod `data_error`); jednostki dowolne, ale spójne.
- Ta sama ścieżka w CLI: `hydrolog soil hsg --clay-path ... --sand-path ... --silt-path ... --output-path hsg.tif`, `hydrolog soil hsg-stats --hsg-path hsg.tif`, `hydrolog cn weighted --parts '[{"cn": 30, "area": 75.0}, ...]'`.
- HSG to tylko jeden z dwóch czynników CN: przy kilku pokryciach terenu części są parami (HSG × pokrycie), a przecięcie rastrów HSG i pokrycia robi Hydrograf (Hydrolog tego nie robi).
- Usunięcie HSG z Kartografa i przepięcie Hydrografa (`get_hsg_from_soilgrids`, `bootstrap.py`) to osobne zmiany w tamtych repozytoriach; do czasu ich wykonania Hydrograf (pin v0.6.3) działa ze starą ścieżką.

---

## Lista zmian do implementacji

### Hydrolog (w tej sesji)

| Plik | Zmiana | Status |
|------|--------|--------|
| `hydrolog/morphometry/watershed_params.py` | NOWY - WatershedParameters | ✅ |
| `hydrolog/morphometry/geometric.py` | + `from_dict()` | ✅ |
| `hydrolog/morphometry/terrain.py` | + `from_dict()` | ✅ |
| `hydrolog/morphometry/__init__.py` | Eksport WatershedParameters | ✅ |
| `tests/unit/test_watershed_params.py` | NOWY - testy jednostkowe | ✅ |
| `tests/integration/test_hydrograf_integration.py` | NOWY - testy integracyjne | ✅ |

### Hydrograf (przy CP3)

| Plik | Zmiana | Status |
|------|--------|--------|
| `backend/core/morphometry.py` | NOWY - funkcje obliczające | 🔲 |
| `backend/models/schemas.py` | + MorphometricParameters | 🔲 |
| `backend/api/endpoints/watershed.py` | Zwracać morphometry | 🔲 |
| `backend/requirements.txt` | + hydrolog | 🔲 |

---

## Status integracji (2026-10-19)

### Hydrolog - GOTOWY

| Komponent | Status | Uwagi |
|-----------|--------|-------|
| WatershedParameters | ✅ | from_dict(), to_json(), calculate_tc() — w tym pola v0.6.3+ |
| WatershedGeometry.from_dict() | ✅ | Wskaźniki kształtu |
| TerrainAnalysis.from_dict() | ✅ | Parametry terenu |
| HydrographGenerator | ✅ | Błąd SCS naprawiony w v0.5.1 (stała 0.208) |
| Testy jednostkowe | ✅ | 35 testów |
| Testy integracyjne | ✅ | 15 testów |
| Warstwa operacji, katalog komend, CLI, MCP (v1.0.0) | ✅ | 37 komend; `hydrolog.operations`, `hydrolog mcp` |
| Moduł `soil` (HSG, v1.0.0) | ✅ | `hsg_from_rasters`, `hsg_statistics`, komendy `soil *` |
| Serializacja wyników (v1.0.0) | ✅ | `to_dict()`/`to_json()` we wszystkich klasach wynikowych |

**Naprawione:** Błąd w `SCSUnitHydrograph.peak_discharge()` — stała 2.08 → 0.208 (naprawione w v0.5.1).

### Hydrograf - DO IMPLEMENTACJI

| Komponent | Status | Uwagi |
|-----------|--------|-------|
| MorphometricParameters schema | 🔲 | Pydantic model |
| build_morphometric_params() | 🔲 | Funkcja obliczająca |
| API endpoint /morphometry | 🔲 | Rozszerzenie API |
| Integracja z Hydrolog | 🔲 | pip install hydrolog; migracja HSG: sekcja "Hydrograf: migracja HSG z Kartografa do Hydrologa" |

### Przetestowane scenariusze

1. ✅ JSON → WatershedParameters (symulacja API)
2. ✅ Batch processing wielu zlewni
3. ✅ Walidacja nieprawidłowych danych
4. ✅ Round-trip serializacja (from_json → to_json → from_json)
5. ✅ Pełny workflow z HydrographGenerator (błąd SCS naprawiony w v0.5.1)
6. ✅ Test na danych rzeczywistych NMT (godło N-33-131-D-a-3-1)

---

## Kontekst dla kolejnych sesji

### Jeśli pracujesz nad Hydrologiem:
1. Przeczytaj ten plik (`docs/INTEGRATION.md`)
2. Sprawdź tabelę "Lista zmian" powyżej
3. Kontynuuj implementację od pierwszego niezakończonego zadania

### Jeśli pracujesz nad Hydrografem:
1. Przeczytaj `docs/HYDROGRAF_INTEGRATION.md` (skopiowany tam ten sam plik)
2. Sprawdź sekcję "Implementacja w Hydrografie"
3. Dodaj Hydrolog jako zależność przed implementacją

### Kluczowe pliki:
- **Format danych:** JSON Schema w sekcji "Format wymiany danych"
- **Hydrolog entry point:** `hydrolog.morphometry.WatershedParameters`
- **Hydrograf entry point:** `backend.core.morphometry.build_morphometric_params()`

---

**Ostatnia aktualizacja:** 2026-10-19
