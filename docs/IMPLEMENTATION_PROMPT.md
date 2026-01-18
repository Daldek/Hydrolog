# IMPLEMENTATION_PROMPT.md

## Prompt dla AI - Implementacja Biblioteki Hydrolog

**Wersja:** 1.0
**Data:** 2026-01-18

---

## 1. Kontekst projektu

Jesteś jedynym deweloperem pracującym nad **Hydrolog** - biblioteką Python do obliczeń hydrologicznych. Pracujesz w **krótkich sesjach** z zerowaniem kontekstu, więc dokumentacja musi być samowystarczalna.

### 1.1 Cel projektu

Stworzyć bibliotekę analogiczną do Kartografa, ale dla obliczeń hydrologicznych:
- Generowanie hydrogramów (SCS-CN)
- Obliczanie parametrów morfometrycznych
- Hietogramy i interpolacja opadów
- Klasyfikacja sieci rzecznej

### 1.2 Stack technologiczny

- **Python:** 3.12+
- **Zależności:** NumPy, IMGWTools
- **Testy:** pytest
- **Formatowanie:** Black (88 znaków)
- **Dokumentacja:** NumPy style docstrings (EN)

---

## 2. Workflow sesji

### 2.1 Początek sesji

```bash
# 1. Przeczytaj dokumentację
cat CLAUDE.md
cat docs/PROGRESS.md  # KRYTYCZNE - stan projektu

# 2. Sprawdź stan repo
git status
git log --oneline -5
```

### 2.2 W trakcie sesji

1. **Commituj często** - małe, logiczne zmiany
2. **Aktualizuj PROGRESS.md** - po każdym milestone
3. **Pisz testy** - przed lub razem z kodem

### 2.3 Koniec sesji

**OBOWIĄZKOWO:**

1. Zaktualizuj `docs/PROGRESS.md`:
   - Co zrobione
   - Co w trakcie (plik, linia, kontekst)
   - Następne kroki

2. Commit i push:
   ```bash
   git add -A
   git commit -m "docs(progress): update session X"
   git push
   ```

---

## 3. Dokumentacja do przeczytania

### Przed rozpoczęciem pracy

| Plik | Zawartość | Kiedy czytać |
|------|-----------|--------------|
| `CLAUDE.md` | Instrukcje dla AI | Zawsze na początku |
| `docs/PROGRESS.md` | Stan projektu | Zawsze na początku |
| `docs/SCOPE.md` | Co IN/OUT | Przy nowych funkcjach |
| `docs/PRD.md` | User stories | Przy implementacji |
| `docs/DEVELOPMENT_STANDARDS.md` | Konwencje | Przy pisaniu kodu |

### Przed implementacją modułu

1. Przeczytaj user story w `docs/PRD.md`
2. Sprawdź zakres w `docs/SCOPE.md`
3. Sprawdź konwencje w `docs/DEVELOPMENT_STANDARDS.md`

---

## 4. Struktura kodu

### 4.1 Layout repozytorium

```
hydrolog2/
├── CLAUDE.md                 # Instrukcje dla AI
├── README.md                 # Opis projektu
├── pyproject.toml            # Konfiguracja pakietu
├── docs/
│   ├── PROGRESS.md           # Status projektu (KRYTYCZNE!)
│   ├── SCOPE.md              # Zakres
│   ├── PRD.md                # Wymagania
│   ├── DEVELOPMENT_STANDARDS.md
│   ├── IMPLEMENTATION_PROMPT.md
│   └── CHANGELOG.md
├── hydrolog/                 # Kod źródłowy
│   ├── __init__.py
│   ├── exceptions.py         # Własne wyjątki
│   ├── runoff/
│   ├── precipitation/
│   ├── time/
│   ├── morphometry/
│   ├── network/
│   └── cli/
└── tests/                    # Testy
    ├── conftest.py
    ├── unit/
    └── integration/
```

### 4.2 Wzorzec modułu

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

---

## 5. Przykładowe zadania

### 5.1 Implementacja funkcji

**Zadanie:** Zaimplementuj `calculate_effective_precipitation`

**Kroki:**

1. **Przeczytaj PRD.md** - sekcja US-R02
2. **Utwórz plik:**
   ```python
   # hydrolog/runoff/scs_cn.py

   from hydrolog.exceptions import InvalidParameterError

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
       InvalidParameterError
           If CN is not in range 0-100.
       """
       if not 0 <= cn <= 100:
           raise InvalidParameterError(f"CN must be 0-100, got {cn}")

       if cn == 100:
           return precipitation_mm

       # Maximum retention
       s_mm = 25400 / cn - 254

       # Initial abstraction
       ia_mm = ia_coefficient * s_mm

       # Effective precipitation
       if precipitation_mm <= ia_mm:
           return 0.0

       return (precipitation_mm - ia_mm) ** 2 / (precipitation_mm + (1 - ia_coefficient) * s_mm)
   ```

3. **Napisz testy:**
   ```python
   # tests/unit/test_scs_cn.py

   import pytest
   from hydrolog.runoff.scs_cn import calculate_effective_precipitation
   from hydrolog.exceptions import InvalidParameterError

   def test_calculate_effective_precipitation_typical():
       """Test with typical values."""
       result = calculate_effective_precipitation(38.5, 72)
       assert 10 < result < 20  # Reasonable range

   def test_calculate_effective_precipitation_zero_rainfall():
       """Zero rainfall returns zero."""
       result = calculate_effective_precipitation(0, 72)
       assert result == 0.0

   def test_calculate_effective_precipitation_cn_100():
       """CN=100 means all rainfall is effective."""
       result = calculate_effective_precipitation(38.5, 100)
       assert result == 38.5

   def test_calculate_effective_precipitation_invalid_cn():
       """Invalid CN raises exception."""
       with pytest.raises(InvalidParameterError):
           calculate_effective_precipitation(38.5, 150)
   ```

4. **Uruchom testy:**
   ```bash
   .venv/bin/python -m pytest tests/unit/test_scs_cn.py -v
   ```

5. **Commit:**
   ```bash
   git add hydrolog/runoff/scs_cn.py tests/unit/test_scs_cn.py
   git commit -m "feat(runoff): add SCS-CN effective precipitation calculation"
   ```

6. **Zaktualizuj PROGRESS.md**

---

### 5.2 Implementacja klasy

**Zadanie:** Zaimplementuj `BetaHietogram`

**Wzorzec:**

```python
# hydrolog/precipitation/hietogram.py

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.exceptions import InvalidParameterError


@dataclass
class HietogramResult:
    """Result of hietogram generation."""

    times_min: NDArray[np.float64]
    intensities_mm_per_min: NDArray[np.float64]
    total_mm: float
    duration_min: float
    timestep_min: float


class BetaHietogram:
    """
    Generate hietogram with Beta distribution.

    Parameters
    ----------
    total_mm : float
        Total precipitation depth [mm].
    duration_min : float
        Storm duration [min].
    timestep_min : float
        Time step [min].
    alpha : float, optional
        Beta distribution alpha parameter, by default 2.0.
    beta : float, optional
        Beta distribution beta parameter, by default 5.0.

    Examples
    --------
    >>> hietogram = BetaHietogram(38.5, 60, 5)
    >>> print(hietogram.peak_intensity_mm_per_min)
    1.23
    """

    def __init__(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float,
        alpha: float = 2.0,
        beta: float = 5.0
    ) -> None:
        self._validate_parameters(total_mm, duration_min, timestep_min)

        self.total_mm = total_mm
        self.duration_min = duration_min
        self.timestep_min = timestep_min
        self.alpha = alpha
        self.beta = beta

        self._result = self._generate()

    def _validate_parameters(
        self, total_mm: float, duration_min: float, timestep_min: float
    ) -> None:
        """Validate input parameters."""
        if total_mm <= 0:
            raise InvalidParameterError(f"total_mm must be > 0, got {total_mm}")
        if duration_min <= 0:
            raise InvalidParameterError(f"duration_min must be > 0, got {duration_min}")
        if timestep_min <= 0:
            raise InvalidParameterError(f"timestep_min must be > 0, got {timestep_min}")

    def _generate(self) -> HietogramResult:
        """Generate the hietogram."""
        # Implementation here
        pass

    @property
    def times_min(self) -> NDArray[np.float64]:
        """Time array [min]."""
        return self._result.times_min

    @property
    def intensities_mm_per_min(self) -> NDArray[np.float64]:
        """Intensity array [mm/min]."""
        return self._result.intensities_mm_per_min

    @property
    def peak_intensity_mm_per_min(self) -> float:
        """Peak intensity [mm/min]."""
        return float(np.max(self._result.intensities_mm_per_min))
```

---

## 6. Wzory hydrologiczne

### 6.1 SCS Curve Number

```
# Retencja maksymalna [mm]
S = 25400 / CN - 254

# Abstrakcja początkowa [mm]
Ia = 0.2 * S

# Opad efektywny [mm]
Pe = (P - Ia)² / (P + 0.8*S)   gdy P > Ia
Pe = 0                         gdy P <= Ia
```

### 6.2 Czas koncentracji - Kirpich

```
tc = 0.0195 * L^0.77 * S^(-0.385)

gdzie:
- tc: czas koncentracji [min]
- L: długość cieku [m]
- S: spadek cieku [m/m]
```

### 6.3 SCS Unit Hydrograph

```
# Czas do szczytu [h]
tp = 0.6 * tc

# Przepływ szczytowy [m³/s]
qp = 0.208 * A / tp

gdzie:
- A: powierzchnia zlewni [km²]
- tp: czas do szczytu [h]

# Czas bazowy [h]
tb = 2.67 * tp
```

### 6.4 Splot (convolution)

```
Q(t) = Σ Pe(τ) * UH(t - τ)

gdzie:
- Q(t): przepływ w czasie t
- Pe(τ): opad efektywny w czasie τ
- UH: hydrogram jednostkowy
```

---

## 7. Checklist implementacji

### Przed rozpoczęciem

- [ ] Przeczytałem PROGRESS.md
- [ ] Przeczytałem relevantne user story w PRD.md
- [ ] Sprawdziłem zakres w SCOPE.md

### W trakcie

- [ ] Kod zgodny z DEVELOPMENT_STANDARDS.md
- [ ] Type hints dla wszystkich funkcji
- [ ] Docstrings (NumPy style, EN)
- [ ] Walidacja parametrów wejściowych
- [ ] Testy jednostkowe

### Przed commitem

- [ ] Testy przechodzą (`pytest`)
- [ ] Formatowanie OK (`black --check`)
- [ ] Type hints OK (`mypy`)
- [ ] PROGRESS.md zaktualizowany

---

## 8. FAQ

**Q: Jak zacząć sesję po zerowym kontekście?**
A: Przeczytaj CLAUDE.md, potem docs/PROGRESS.md - tam jest stan projektu.

**Q: Gdzie jest dokumentacja metod hydrologicznych?**
A: W sekcji 6 tego dokumentu i w docstringach kodu.

**Q: Jak nazywać zmienne z jednostkami?**
A: Zawsze z jednostką w nazwie: `area_km2`, `time_min`, `discharge_m3s`.

**Q: Jak obsługiwać błędy?**
A: Używaj własnych wyjątków z `hydrolog/exceptions.py`.

**Q: Jak kończyć sesję?**
A: Zaktualizuj PROGRESS.md, commit, push.

---

**Wersja dokumentu:** 1.0
**Data ostatniej aktualizacji:** 2026-01-18
