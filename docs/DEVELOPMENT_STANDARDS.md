# DEVELOPMENT_STANDARDS.md - Standardy Kodowania

## Hydrolog - Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.0
**Data:** 2026-01-18

---

## 1. Nazewnictwo

### 1.1 Python

```python
# Zmienne i funkcje: snake_case + jednostka
area_km2 = 45.3
time_concentration_min = 68.5
discharge_m3s = 42.3

def calculate_effective_precipitation(precipitation_mm: float, cn: int) -> float:
    pass

# Klasy: PascalCase
class HydrographGenerator:
    pass

class BetaHietogram:
    pass

# Stałe: UPPER_SNAKE_CASE
DEFAULT_TIMESTEP_MIN = 5
SCS_PEAK_FACTOR = 0.208
```

### 1.2 Jednostki w nazwach zmiennych

| Wielkość | Jednostka | Symbol | Przykład |
|----------|-----------|--------|----------|
| Powierzchnia | km² | km2 | `area_km2` |
| Długość | km, m | km, m | `length_km`, `length_m` |
| Opad | mm | mm | `precipitation_mm` |
| Intensywność | mm/min | mm_per_min | `intensity_mm_per_min` |
| Przepływ | m³/s | m3s | `discharge_m3s` |
| Czas | min | min | `tc_min`, `duration_min` |
| Spadek | % | percent | `slope_percent` |

---

## 2. Formatowanie

### 2.1 Black (88 znaków)

```python
# Maksymalna długość linii: 88 znaków
# Wcięcia: 4 spacje

# DOBRZE
def calculate_time_of_concentration(
    length_km: float,
    slope_percent: float,
    method: str = "kirpich"
) -> float:
    pass

# ŹLE (za długa linia)
def calculate_time_of_concentration(length_km: float, slope_percent: float, method: str = "kirpich") -> float:
    pass
```

### 2.2 Importy

```python
# Kolejność: stdlib → third-party → local
# Alfabetycznie w grupach
# Puste linie między grupami

from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.runoff.scs_cn import calculate_retention
from hydrolog.time import ConcentrationTime
```

---

## 3. Type Hints

### 3.1 Wymagane wszędzie

```python
from typing import Optional, Tuple, List
from numpy.typing import NDArray

def generate_hydrograph(
    area_km2: float,
    cn: int,
    tc_min: float,
    hietogram: NDArray[np.float64]
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate hydrograph."""
    pass

class HydrographResult:
    peak_discharge_m3s: float
    time_to_peak_min: float
    total_volume_m3: float
    times_min: NDArray[np.float64]
    discharges_m3s: NDArray[np.float64]
```

### 3.2 Typy NumPy

```python
from numpy.typing import NDArray
import numpy as np

# Tablica float
intensities: NDArray[np.float64]

# Tablica 2D
elevations: NDArray[np.float64]  # shape: (rows, cols)
```

---

## 4. Docstrings (NumPy Style, English)

### 4.1 Funkcje

```python
def calculate_effective_precipitation(
    precipitation_mm: float,
    cn: int,
    ia_coefficient: float = 0.2
) -> float:
    """
    Calculate effective precipitation using SCS-CN method.

    Parameters
    ----------
    precipitation_mm : float
        Total precipitation depth [mm].
    cn : int
        Curve Number (0-100).
    ia_coefficient : float, optional
        Initial abstraction coefficient, by default 0.2.

    Returns
    -------
    float
        Effective precipitation depth [mm].

    Raises
    ------
    ValueError
        If CN is not in range 0-100.

    Examples
    --------
    >>> calculate_effective_precipitation(38.5, 72)
    15.23
    """
    pass
```

### 4.2 Klasy

```python
class HydrographGenerator:
    """
    Generate runoff hydrograph using SCS-CN method.

    Parameters
    ----------
    area_km2 : float
        Watershed area [km²].
    cn : int
        Curve Number (0-100).
    tc_min : float
        Time of concentration [min].

    Attributes
    ----------
    retention_mm : float
        Maximum retention [mm].
    ia_mm : float
        Initial abstraction [mm].

    Examples
    --------
    >>> generator = HydrographGenerator(area_km2=45.3, cn=72, tc_min=68.5)
    >>> result = generator.generate(hietogram)
    >>> print(result.peak_discharge_m3s)
    42.3
    """

    def __init__(self, area_km2: float, cn: int, tc_min: float) -> None:
        pass
```

---

## 5. Testowanie

### 5.1 Struktura testów

```
tests/
├── unit/
│   ├── test_scs_cn.py
│   ├── test_unit_hydrograph.py
│   ├── test_hietogram.py
│   └── test_concentration.py
├── integration/
│   └── test_full_hydrograph.py
└── conftest.py
```

### 5.2 Nazewnictwo testów

```python
# test_<moduł>_<funkcja>_<scenariusz>

def test_calculate_effective_precipitation_typical_values():
    """Test effective precipitation for typical CN and rainfall."""
    pass

def test_calculate_effective_precipitation_zero_rainfall():
    """Test that zero rainfall returns zero effective precipitation."""
    pass

def test_calculate_effective_precipitation_invalid_cn_raises():
    """Test that invalid CN raises ValueError."""
    pass
```

### 5.3 AAA Pattern

```python
def test_kirpich_formula():
    # Arrange
    length_km = 8.2
    slope_percent = 2.3
    expected_tc_min = 68.5  # From literature

    # Act
    result = ConcentrationTime.kirpich(length_km, slope_percent)

    # Assert
    assert abs(result - expected_tc_min) < 1.0  # ±1 min tolerance
```

### 5.4 Pokrycie

```bash
# Wymagane: > 80%
pytest tests/ --cov=hydrolog --cov-report=html --cov-fail-under=80
```

---

## 6. Git Workflow

### 6.1 Branching

```
main          # Stabilna wersja
develop       # Aktywny rozwój
feature/*     # Nowe funkcjonalności
fix/*         # Poprawki błędów
```

### 6.2 Conventional Commits

```bash
# Format
<type>(<scope>): <description>

# Typy
feat     # Nowa funkcjonalność
fix      # Poprawka błędu
docs     # Dokumentacja
test     # Testy
refactor # Refaktoryzacja
chore    # Inne (config, deps)

# Przykłady
feat(runoff): add SCS-CN effective precipitation calculation
fix(hietogram): correct beta distribution normalization
docs(readme): add quick start examples
test(time): add tests for Kirpich formula
```

### 6.3 Commit często

- Każda logiczna zmiana = osobny commit
- Łatwiejsze code review
- Łatwiejszy rollback

---

## 7. Struktura modułów

### 7.1 Każdy moduł ma `__init__.py`

```python
# hydrolog/runoff/__init__.py
"""Runoff generation module."""

from hydrolog.runoff.scs_cn import (
    calculate_effective_precipitation,
    calculate_retention,
)
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph
from hydrolog.runoff.generator import HydrographGenerator

__all__ = [
    "calculate_effective_precipitation",
    "calculate_retention",
    "SCSUnitHydrograph",
    "HydrographGenerator",
]
```

### 7.2 Eksportuj tylko publiczne API

```python
# DOBRZE - import z modułu
from hydrolog.runoff import HydrographGenerator

# Unikaj - import z pliku wewnętrznego
from hydrolog.runoff.generator import HydrographGenerator
```

---

## 8. Error Handling

### 8.1 Własne wyjątki

```python
# hydrolog/exceptions.py

class HydrologError(Exception):
    """Base exception for Hydrolog."""
    pass

class InvalidParameterError(HydrologError):
    """Invalid parameter value."""
    pass

class CalculationError(HydrologError):
    """Error during calculation."""
    pass
```

### 8.2 Walidacja na wejściu

```python
def calculate_retention(cn: int) -> float:
    """Calculate maximum retention."""
    if not 0 <= cn <= 100:
        raise InvalidParameterError(f"CN must be 0-100, got {cn}")

    if cn == 100:
        return 0.0

    return 25400 / cn - 254
```

---

## 9. Komendy

```bash
# Testy
.venv/bin/python -m pytest tests/ -v

# Testy z pokryciem
.venv/bin/python -m pytest tests/ --cov=hydrolog --cov-report=html

# Formatowanie
.venv/bin/python -m black hydrolog/ tests/

# Sprawdzenie formatowania (bez zmian)
.venv/bin/python -m black hydrolog/ tests/ --check

# Type checking
.venv/bin/python -m mypy hydrolog/

# Linting
.venv/bin/python -m flake8 hydrolog/ tests/
```

---

## 10. Checklist przed commitem

- [ ] Testy przechodzą (`pytest`)
- [ ] Pokrycie > 80% (`pytest --cov`)
- [ ] Formatowanie OK (`black --check`)
- [ ] Type hints OK (`mypy`)
- [ ] Docstrings dla publicznych funkcji/klas
- [ ] PROGRESS.md zaktualizowany

---

**Wersja dokumentu:** 1.0
**Data ostatniej aktualizacji:** 2026-01-18
