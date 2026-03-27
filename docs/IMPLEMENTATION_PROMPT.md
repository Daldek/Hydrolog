# IMPLEMENTATION_PROMPT.md

## Prompt dla AI - Implementacja Biblioteki Hydrolog

**Wersja:** 0.7.0
**Data:** 2026-03-26

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
- **Zależności:** NumPy (IMGWTools usunięte w v0.2.0)
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
Hydrolog/
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
│   ├── cli/
│   ├── reports/              # Dodane w v0.6.0
│   ├── visualization/        # Dodane w v0.5.0
│   ├── statistics/           # Dodane w v0.7.0
│   └── hydrometrics/         # Dodane w v0.7.0
└── tests/                    # Testy
    ├── conftest.py
    ├── unit/
    └── integration/
```

### 4.2 Wzorzec modułu

```python
# hydrolog/runoff/__init__.py
"""Runoff generation module using SCS-CN method."""

from hydrolog.runoff.scs_cn import SCSCN, AMC, EffectivePrecipitationResult
from hydrolog.runoff.unit_hydrograph import SCSUnitHydrograph
from hydrolog.runoff.generator import HydrographGenerator
from hydrolog.runoff.nash_iuh import NashIUH
from hydrolog.runoff.clark_iuh import ClarkIUH
from hydrolog.runoff.snyder_uh import SnyderUH
from hydrolog.runoff.cn_lookup import get_cn, lookup_cn, calculate_weighted_cn
from hydrolog.runoff.convolution import convolve_discrete

# Reprezentatywny podzbiór — pełna lista w __all__ modułu
# Klasy: SCSCN, AMC, HydrographGenerator, SCSUnitHydrograph,
#         NashIUH, ClarkIUH, SnyderUH
# Funkcje: get_cn, lookup_cn, calculate_weighted_cn, convolve_discrete
```

---

## 5. Przykładowe zadania

### 5.1 Implementacja funkcji

**Zadanie:** Oblicz opad efektywny metodą SCS-CN (klasa `SCSCN`)

**Kroki:**

1. **Przeczytaj PRD.md** - sekcja US-R02
2. **Użyj klasy SCSCN:**
   ```python
   # hydrolog/runoff/scs_cn.py zawiera klasę SCSCN

   from hydrolog.runoff import SCSCN, AMC

   # Inicjalizacja z Curve Number (1-100)
   scs = SCSCN(cn=72)

   # Obliczenie opadu efektywnego (scalar)
   result = scs.effective_precipitation(precipitation_mm=50.0)
   print(result.total_effective_mm)       # 7.09 mm
   print(result.effective_mm)             # float dla scalar input
   print(result.retention_mm)             # S [mm]
   print(result.initial_abstraction_mm)   # Ia [mm]
   print(result.cn_adjusted)              # CN (skorygowany dla AMC)

   # Z korekcją AMC (warunki wilgotnościowe)
   result_wet = scs.effective_precipitation(
       precipitation_mm=50.0,
       amc=AMC.III,  # warunki mokre
   )

   # Obliczenie dla tablicy opadów (hietogram)
   result_array = scs.effective_precipitation(
       precipitation_mm=[5.0, 10.0, 15.0, 8.0]
   )
   print(result_array.effective_mm)       # NDArray przyrostów opadu efektywnego
   ```

3. **Napisz testy:**
   ```python
   # tests/unit/test_scs_cn.py

   import pytest
   from hydrolog.runoff import SCSCN, AMC
   from hydrolog.exceptions import InvalidParameterError

   def test_effective_precipitation_typical():
       """Test with typical values."""
       scs = SCSCN(cn=72)
       result = scs.effective_precipitation(precipitation_mm=50.0)
       assert 5 < result.total_effective_mm < 15  # Reasonable range

   def test_effective_precipitation_zero_rainfall():
       """Zero rainfall returns zero."""
       scs = SCSCN(cn=72)
       result = scs.effective_precipitation(precipitation_mm=0.0)
       assert result.total_effective_mm == 0.0

   def test_effective_precipitation_cn_100():
       """CN=100 means all rainfall is effective."""
       scs = SCSCN(cn=100)
       result = scs.effective_precipitation(precipitation_mm=38.5)
       assert result.total_effective_mm == 38.5

   def test_invalid_cn_raises():
       """Invalid CN raises exception."""
       with pytest.raises(InvalidParameterError):
           SCSCN(cn=150)
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
    """Result of hyetograph generation."""

    times_min: NDArray[np.float64]
    intensities_mm: NDArray[np.float64]       # przyrostowe głębokości [mm/krok]
    total_mm: float
    duration_min: float
    timestep_min: float

    # Właściwości (properties):
    # n_steps -> int              — liczba kroków
    # intensity_mm_per_h -> array — intensywność [mm/h]


class BetaHietogram(Hietogram):
    """
    Beta distribution hyetograph.

    Dziedziczy po abstrakcyjnej klasie Hietogram.
    Parametry kształtu (alpha, beta) przekazywane do __init__,
    dane opadu (total_mm, duration_min, timestep_min) — do generate().

    Parameters
    ----------
    alpha : float, optional
        Alpha parameter of Beta distribution, by default 2.0.
    beta : float, optional
        Beta parameter of Beta distribution, by default 5.0.

    Examples
    --------
    >>> hietogram = BetaHietogram(alpha=2.0, beta=5.0)
    >>> result = hietogram.generate(total_mm=38.5, duration_min=60, timestep_min=5)
    >>> print(result.intensities_mm)        # przyrostowe głębokości [mm]
    >>> print(result.intensity_mm_per_h)    # intensywność [mm/h]
    """

    def __init__(self, alpha: float = 2.0, beta: float = 5.0) -> None:
        if alpha <= 0:
            raise InvalidParameterError(f"alpha must be positive, got {alpha}")
        if beta <= 0:
            raise InvalidParameterError(f"beta must be positive, got {beta}")
        self.alpha = alpha
        self.beta = beta

    def generate(
        self,
        total_mm: float,
        duration_min: float,
        timestep_min: float = 5.0,
    ) -> HietogramResult:
        """Generate Beta distribution hyetograph."""
        # Walidacja i obliczenia — zwraca HietogramResult
        ...
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
Pe = (P - Ia)² / (P - Ia + S)   gdy P > Ia
Pe = 0                          gdy P <= Ia

# Uwaga: forma (P + 0.8·S) jest równoważna tylko gdy Ia = 0.2·S.
# Ogólna postać (P - Ia + S) jest poprawna dla dowolnego λ.
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
# Aproksymacja trójkątna: tb ≈ 2.67 * tp
# Pełna tablica bezwymiarowa NRCS (33 punkty): tb = 5.0 * tp
tb = 5.0 * tp
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

**Wersja dokumentu:** 0.7.0
**Data ostatniej aktualizacji:** 2026-03-26
