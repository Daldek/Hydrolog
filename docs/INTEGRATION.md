# Integracja Hydrograf ↔ Hydrolog

**Data utworzenia:** 2026-01-20
**Status:** W trakcie implementacji

---

## Cel

Umożliwić łatwą wymianę danych między Hydrografem (analizy przestrzenne GIS) a Hydrologiem (obliczenia hydrologiczne), z możliwością integracji z innymi systemami.

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
│  - Czas koncentracji (Kirpich, SCS Lag, Giandotti)              │
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
    "crs": {"type": "string", "description": "Układ współrzędnych"}
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

**Status:** 🔲 Do zaimplementowania

**Pliki:**
- `hydrolog/morphometry/geometric.py` - `WatershedGeometry.from_dict()`
- `hydrolog/morphometry/terrain.py` - `TerrainAnalysis.from_dict()`

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
hietogram = BetaHietogram(total_mm=50, duration_min=60, timestep_min=5)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
```

---

## Lista zmian do implementacji

### Hydrolog (w tej sesji)

| Plik | Zmiana | Status |
|------|--------|--------|
| `hydrolog/morphometry/watershed_params.py` | NOWY - WatershedParameters | ✅ |
| `hydrolog/morphometry/geometric.py` | + `from_dict()` | 🔲 |
| `hydrolog/morphometry/terrain.py` | + `from_dict()` | 🔲 |
| `hydrolog/morphometry/__init__.py` | Eksport WatershedParameters | 🔲 |
| `tests/unit/test_watershed_params.py` | NOWY - testy | 🔲 |

### Hydrograf (przy CP3)

| Plik | Zmiana | Status |
|------|--------|--------|
| `backend/core/morphometry.py` | NOWY - funkcje obliczające | 🔲 |
| `backend/models/schemas.py` | + MorphometricParameters | 🔲 |
| `backend/api/endpoints/watershed.py` | Zwracać morphometry | 🔲 |
| `backend/requirements.txt` | + hydrolog | 🔲 |

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

**Ostatnia aktualizacja:** 2026-01-20
