# DEVELOPMENT_STANDARDS.md - Standardy Kodowania

## Hydrolog - Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.2
**Data:** 2026-10-19

---

## 1. Nazewnictwo

### 1.1 Python

```python
# Zmienne i funkcje: snake_case + jednostka
area_km2 = 45.3
time_concentration_min = 68.5
discharge_m3s = 42.3

def effective_precipitation(precipitation_mm: float, cn: int) -> float:
    pass

# Klasy: PascalCase
class SCSCN:
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
| Spadek | m/m | m_per_m | `slope_m_per_m` |

### 1.3 Symbole prywatne/wewnętrzne

```python
# Prefiks podkreślenia dla symboli niepublicznych
_KIRPICH_LENGTH_RANGE = (0.5, 300.0)  # prywatna stała modułowa
_warn_if_out_of_range(value, range)    # wewnętrzna funkcja pomocnicza

# Używaj pojedynczego podkreślenia (nie podwójnego __name_mangling)
# Przykłady: hydrolog/time/concentration.py
```

---

## 2. Formatowanie

### 2.1 Black (88 znaków)

```python
# Maksymalna długość linii: 88 znaków
# Wcięcia: 4 spacje

# DOBRZE
def calculate_time_of_concentration(
    length_km: float,
    slope_m_per_m: float,
    method: str = "kirpich"
) -> float:
    pass

# ŹLE (za długa linia)
def calculate_time_of_concentration(length_km: float, slope_m_per_m: float, method: str = "kirpich") -> float:
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

### 3.3 Wzorzec TYPE_CHECKING

```python
# Zapobieganie cyklicznym importom (np. hydrolog/morphometry/watershed_params.py)
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hydrolog.other_module import SomeClass
```

### 3.4 Dataclasses dla obiektów wynikowych

```python
from dataclasses import dataclass

@dataclass
class SCSCNResult:
    """Result container — preferowany wzorzec dla wyników obliczeń."""
    effective_precipitation_mm: float
    retention_mm: float
    initial_abstraction_mm: float
```

Stosować dla wszystkich obiektów wynikowych (np. `HietogramResult`, `UnitHydrographResult`).

---

## 4. Docstrings (NumPy Style, English)

### 4.1 Funkcje

```python
def effective_precipitation(
    self,
    precipitation_mm: float | NDArray[np.float64],
    amc: AMC = AMC.II,
) -> EffectivePrecipitationResult:
    """
    Calculate effective precipitation using SCS-CN method.

    Parameters
    ----------
    precipitation_mm : float or NDArray[np.float64]
        Total precipitation depth [mm].
    amc : AMC, optional
        Antecedent moisture condition, by default AMC.II.

    Returns
    -------
    EffectivePrecipitationResult
        Result with effective_mm, retention_mm, initial_abstraction_mm.

    Raises
    ------
    InvalidParameterError
        If precipitation is negative.

    Examples
    --------
    >>> scs = SCSCN(cn=72)
    >>> result = scs.effective_precipitation(38.5)
    >>> result.total_effective_mm
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
│   ├── test_concentration.py
│   ├── test_catalog_core.py       # katalog komend (walidacja, przykłady, parytet CLI/Python)
│   ├── test_cli_*.py              # parser, wartości, render, parytet CLI
│   ├── test_mcp.py                # serwer MCP (klient-serwer w procesie)
│   └── test_agent_guide.py        # zgodność AGENTS.md / llms.txt z generatorem
├── integration/
│   └── test_full_hydrograph.py
├── fixtures/                      # pliki CSV/JSON/GeoTIFF używane przez testy
└── conftest.py
```

### 5.2 Nazewnictwo testów

```python
# test_<moduł>_<funkcja>_<scenariusz>

def test_scscn_effective_precipitation_typical_values():
    """Test effective precipitation for typical CN and rainfall."""
    pass

def test_scscn_effective_precipitation_zero_rainfall():
    """Test that zero rainfall returns zero effective precipitation."""
    pass

def test_scscn_effective_precipitation_invalid_cn_raises():
    """Test that invalid CN raises InvalidParameterError."""
    pass
```

### 5.3 AAA Pattern

```python
def test_kirpich_formula():
    # Arrange
    length_km = 8.2
    slope_m_per_m = 0.023
    expected_tc_min = 68.5  # From literature

    # Act
    result = ConcentrationTime.kirpich(length_km, slope_m_per_m)

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
main          # Stabilna wersja (tylko merge z develop)
develop       # Aktywny rozwój (DOMYŚLNA GAŁĄŹ ROBOCZA)
feature/*     # Nowe funkcjonalności
fix/*         # Poprawki błędów
```

**WAŻNE:** Cały rozwój kodu odbywa się na gałęzi `develop`.
Gałąź `main` otrzymuje tylko merge z `develop` przy wydaniach.

### 6.2 Tagowanie

Tagi `v<X.Y.Z>` są tworzone automatycznie przez Claude Code przy wydaniach:

```bash
# Tworzenie tagu wersji
git tag -a v0.1.0 -m "Release v0.1.0: SCS-CN hydrograph generation"
git push origin v0.1.0

# Lista tagów
git tag -l
```

**Uwaga:** Checkpointy (CP) są śledzone tylko w `docs/PROGRESS.md`, bez tagów Git.

### 6.4 Conventional Commits

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

### 6.5 Commit często

- Każda logiczna zmiana = osobny commit
- Łatwiejsze code review
- Łatwiejszy rollback

---

## 7. Struktura modułów

### 7.1 Każdy moduł ma `__init__.py`

```python
# hydrolog/runoff/__init__.py
"""Runoff generation module."""

from hydrolog.runoff.scs_cn import SCSCN, AMC, EffectivePrecipitationResult
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph
from hydrolog.runoff.generator import HydrographGenerator

__all__ = [
    "SCSCN",
    "AMC",
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
# hydrolog/exceptions.py (skrót)

class HydrologError(Exception):
    """Base exception: code, details, hint (keyword-only, optional)."""

class InvalidParameterError(HydrologError, ValueError):  # code "validation_error"
class CalculationError(HydrologError):                    # code "calculation_error"
class InputDataError(HydrologError):                      # code "data_error"
class MissingDependencyError(HydrologError):              # code "missing_dependency"
class ForbiddenPathError(HydrologError):                  # code "forbidden"
class NotFoundError(HydrologError):                       # code "not_found"
class OutputError(HydrologError):                         # code "io_error"
```

`InvalidParameterError` jest też `ValueError` (kod napisany pod `except ValueError` z wersji < 1.0.0 nadal działa). Błąd, który ma być jednocześnie `CalculationError` i zgodny wstecz z `InvalidParameterError`, to `RatingCurveFitError(CalculationError, InvalidParameterError)`.

Dotychczasowe `raise InvalidParameterError("komunikat")` działa bez zmian; `code`, `details` i `hint` są opcjonalnymi argumentami nazwanymi.

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

### 8.3 Ostrzeżenia dla zakresów parametrów

```python
import warnings

# Używaj warnings.warn() gdy wartość jest nietypowa, ale nie błędna
if param < TYPICAL_MIN or param > TYPICAL_MAX:
    warnings.warn(f"param={param} outside typical range", UserWarning, stacklevel=2)
```

Wzorzec stosowany w `hydrolog/time/concentration.py` — pozwala użytkownikowi kontynuować obliczenia z nietypowymi wartościami.

### 8.4 Kody błędów (`ERROR_CODES`) i szczegóły błędu

Zamknięty rejestr `hydrolog.exceptions.ERROR_CODES` mapuje kod na tytuł (PL/EN) i kod wyjścia CLI; ten sam kod widzi użytkownik Pythona (`exc.code`), CLI (kod wyjścia, z `--json` linia `hydrolog-error/1` na stderr) i klient MCP (`isError`).

| Kod | Kod wyjścia | Klasa wyjątku | Kiedy |
|-----|:-----------:|---------------|-------|
| `validation_error` | 2 | `InvalidParameterError` | zła wartość, typ lub zakres argumentu, brak wymaganego argumentu |
| `not_found` | 3 | `NotFoundError` | brak pliku wejściowego, nieznana komenda |
| `calculation_error` | 4 | `CalculationError` | dane poprawne formalnie, ale wyniku nie da się policzyć (brak zbieżności, za krótka seria) |
| `data_error` | 7 | `InputDataError` | plik wejściowy nieczytelny lub błędny (kolumna, liczba, data, raster) |
| `missing_dependency` | 6 | `MissingDependencyError` | brak dodatku opcjonalnego (`[raster]`, `[mcp]`, `[visualization]`) |
| `forbidden` | 8 | `ForbiddenPathError` | ścieżka poza katalogami dozwolonymi serwera MCP |
| `io_error` | 9 | `OutputError` | nie można zapisać pliku wyjściowego |
| `internal_error` | 1 | `HydrologError` | błąd w Hydrologu (kod domyślny klasy bazowej) |

Zasady:

- Rzucaj najwęższą klasę (`InvalidParameterError` zamiast gołego `ValueError`); komunikat (`message`) i `hint` są po angielsku, w jednej linii.
- `details` to JSON-owy słownik z kontekstem błędu. Konwencja: `option` - nazwa błędnej opcji (taka jak w katalogu), `reason` - powód (`required`, `type`, `minimum`, `maximum`, `choice`, `one_of`, `unknown_option`, `missing_field`, `cycle`...), a do tego `value`, `allowed`, `path`, `column` zależnie od błędu. Agenci decydują po `code`, `details.option` i `details.reason`, nie po tekście komunikatu.
- `hint` mówi, jak poprawić wywołanie (jedno zdanie).
- Nowy kod błędu to zmiana publicznego kontraktu (kod wyjścia, dokument `hydrolog-error/1`): dopisz go do `ErrorCode` i `ERROR_CODES`, do `_ERROR_ADVICE` w `hydrolog/agent_guide.py` (opis w tabeli błędów przewodników) i zregeneruj przewodniki (sekcja 11). Zwykle wystarcza istniejący kod z innym `reason`.
- Ostrzeżenia nie są błędami: `warnings.warn(..., UserWarning)` (sekcja 8.3); w operacjach katalogu `capture_warnings` zamienia je na `notices` koperty wyniku.

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

# Linting (domyślna konfiguracja — brak pliku .flake8)
.venv/bin/python -m flake8 hydrolog/ tests/
```

**Uwaga:** flake8 jest zainstalowany jako zależność, ale używa domyślnej konfiguracji (brak pliku `.flake8` ani sekcji w `setup.cfg`).

---

## 10. Checklist przed commitem

- [ ] Testy przechodzą (`pytest`)
- [ ] Pokrycie > 80% (`pytest --cov`)
- [ ] Formatowanie OK (`black --check`)
- [ ] Type hints OK (`mypy`)
- [ ] Docstrings dla publicznych funkcji/klas
- [ ] Zmiana komendy lub opcji katalogu: `AGENTS.md` i `llms.txt` zregenerowane (sekcja 11)
- [ ] CHANGELOG.md i PROGRESS.md zaktualizowane

---

## 11. Katalog komend: dodawanie komendy i przewodniki dla agentów

Biblioteka, CLI, serwer MCP i przewodniki powstają z jednego katalogu komend (`hydrolog/catalog/`). Nie edytuje się osobno parsera CLI, narzędzi MCP ani `AGENTS.md`/`llms.txt`.

### 11.1 Jak dodać komendę

1. **Operacja** w `hydrolog/operations/<grupa>.py`: publiczna, udokumentowana (docstring NumPy po angielsku), w pełni otypowana funkcja o argumentach nazwanych (keyword-only) dokładnie tak jak opcje komendy; nazwa `<grupa>_<komenda>` (`tc_kirpich`), `Literal` dla wyborów, wartości przyjazne JSON-owi (liczby, teksty, listy, ścieżki jako `str`). Operacja składa istniejące klasy (bez nowej hydrologii), serie, stacje i zlewnie wczytuje przez `hydrolog.catalog.inputs`, błędy zgłasza wyjątkami z `hydrolog.exceptions`. Zwraca wynik z `JsonResultMixin` (`to_dict()`/`to_json()`) albo `OperationOutput` (wynik + `notices` + zapisane `files`). Wyeksportuj ją w `hydrolog/operations/__init__.py` (z `__all__`).
2. **Deklaracja** w `hydrolog/catalog/groups/<grupa>.py` (krotka `COMMANDS`): `Command` (`name` `"<grupa> <komenda>"`, `operation_id`, `summary` do 120 znaków i `description` po polsku, `summary_en`/`description_en`, `function="hydrolog.operations:<nazwa>"`, `options`, `one_of`, `writes`, `examples`) i `Option` (typ, opis PL/EN, `required`, `default` tylko gdy API ma udokumentowaną wartość domyślną, `minimum`/`maximum`/`exclusive_minimum`, `unit`, `writes` dla opcji wyjściowej). Co najmniej jeden przykład w `examples`. Nowa grupa: dopisz jej moduł do `GROUP_MODULES` w `hydrolog/catalog/groups/__init__.py` (kolejność w pomocy i przewodnikach; `commands` zostaje ostatnia) i tytuł do `_GROUP_TITLES` w `hydrolog/agent_guide.py`.
3. **CLI i MCP** nie wymagają zmian: flagi `--kebab-case`, schemat (`--schema`), narzędzie MCP o nazwie `operation_id` i wiersz w przewodnikach powstają z deklaracji. Opcje typu `path` podlegają polityce ścieżek (MCP: tylko katalogi `--allow-dir`).
4. **Testy:** przykłady z `examples` uruchamia test parytetu przez `run_command` i CLI (`--json`) i porównuje koperty; dodaj testy operacji dla przypadków brzegowych i błędów (`code`, `details.option`, `details.reason`).
5. **Przewodniki:** zregeneruj `AGENTS.md` i `llms.txt` w tej samej zmianie (sekcja 11.2).
6. **Dokumentacja:** CHANGELOG.md (liczba komend, nowa komenda), README i PROGRESS.md, jeśli komenda jest widoczna dla użytkownika.

### 11.2 Regeneracja przewodników dla agentów

`AGENTS.md` i `llms.txt` w katalogu głównym repozytorium są generowane (nie edytuj ich ręcznie):

```bash
.venv/bin/hydrolog commands guide --format agents --lang pl --path AGENTS.md
.venv/bin/hydrolog commands guide --format llms --lang pl --path llms.txt
```

Wersja angielska (na stdout): `hydrolog commands guide --format agents --lang en`. Test `tests/unit/test_agent_guide.py` porównuje bajty obu plików z generatorem, więc zmiana katalogu, szablonów w `hydrolog/_data/agents/`, rejestru błędów, zasad albo przepływów w `hydrolog/agent_guide.py` bez regeneracji kończy się niepowodzeniem testu. Każdy krok przepływu w przewodniku jest walidowany względem katalogu: zmiana nazwy opcji zatrzyma generator, dopóki nie poprawisz przepływu.

### 11.3 Wersjonowanie interfejsów (od v1.0.0)

Od v1.0.0 obowiązuje wersjonowanie semantyczne. Nazwy komend, nazwy i typy opcji, schematy `hydrolog-result/1` i `hydrolog-error/1` oraz kody błędów rejestru są publicznym API: zmiana niezgodna wstecz wymaga nowej wersji głównej. Dodawanie komend, opcji opcjonalnych i pól wyniku jest zmianą zgodną wstecz.

---

**Wersja dokumentu:** 1.2
**Data ostatniej aktualizacji:** 2026-10-19
