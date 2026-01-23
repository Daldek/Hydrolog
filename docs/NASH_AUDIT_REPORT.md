# Audyt architektury modułu Nash IUH w Hydrolog

**Data:** 2026-01-22
**Autor:** Claude Code (audyt na zlecenie)
**Wersja Hydrolog:** 0.6.0

---

## 1. Wyniki weryfikacji literaturowej

### 1.1. Metody estymacji parametrów N i K w modelu Nash IUH

#### Źródło 1: Nash (1957) - praca oryginalna

> "Nash proposed the formulation of the Instantaneous Unit Hydrograph (IUH) under the assumption that hydrograph generation was affected by n linear reservoirs with the same value of storage coefficient k."
>
> — ResearchGate: [Unit Hydrographs Derived from the Nash Model](https://www.researchgate.net/publication/230328558_Unit_Hydrographs_Derived_from_the_Nash_Model)

**Kluczowe właściwości modelu Nasha:**
- **Lag time = n × K** (pierwszy moment IUH)
- **Czas do szczytu IUH: tp = (n-1) × K** (dla n > 1)
- Parametry n i K opisują pełny kształt IUH

#### Źródło 2: Ahmad et al. (2009) - Water Resources Management

> "Nash instantaneous unit hydrograph is frequently used for simulating hydrological response in natural watersheds. The accuracy of estimating the parameters n and k in Nash model directly affect simulation results."
>
> "Different methods of estimating the Nash model parameters (n and k) include: moment, trial-and-error, Han's graphical method, time to peak – time to inflection point and Bhunya et al methods. Physiographic parameters can be used for experimental Nash formula."
>
> — Springer: [Genetic Algorithm Based Parameter Estimation of Nash Model](https://link.springer.com/article/10.1007/s11269-007-9208-6)

#### Źródło 3: Rosso (1984) - podejście geomorfologiczne

> "Rosso (1984) modified the parameters of the two-parameter gamma model presented by Nash (1957) by fitting the discharge values and time-to-peak of the geomorphological UH with the gamma distribution as a function of Horton ratios."
>
> — ScienceDirect: [Evaluation of geomorphological approaches for Nash's IUH](https://www.sciencedirect.com/science/article/abs/pii/S0895981120306957)

#### Źródło 4: Metoda Lutza (1984)

> "Lutz, W. (1984). Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen. Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe."
>
> — Cytowane w: KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych. Załącznik 2.

**Metoda Lutza estymuje parametry Nasha z cech fizjograficznych:**
- L (długość cieku głównego)
- Lc (odległość do centroidu)
- Jg (spadek)
- n (współczynnik Manninga)
- U (% urbanizacji)
- W (% zalesienia)

### 1.2. Zastosowanie wzorów Kirpich, SCS Lag, Giandotti

#### Źródło 1: Kirpich (1940) - oryginalne zastosowanie

> "The Kirpich equation was developed from data obtained in seven rural watersheds in Tennessee (USA). The watersheds had well-defined channels and steep slopes of 0.03 to 0.1 ft/ft (3 to 10%) and areas of 1 to 112 acres."
>
> "Kirpich did not derive the time of concentration from flow velocities, but from the translation of observed hydrographs."
>
> — CivilWeb: [Kirpich Formula](https://civilweb-spreadsheets.com/drainage-design-spreadsheets/runoff-and-rainfall-intensity-calculator-spreadsheet/kirpich-formula/)

**Oryginalne zastosowanie:** Małe zlewnie rolnicze, metoda racjonalna.

#### Źródło 2: SCS Lag - TR-55 (1986)

> "The SCS Lag equation was developed by the Soil Conservation Service. It is based on data from agricultural watersheds and is most valid for rural applications."
>
> "t_p = 0.6 × T_c" — The basin lag is estimated as 60% of the watershed's time of concentration.
>
> — HEC-HMS: [SCS Unit Hydrograph Model](https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/scs-unit-hydrograph-model)

**Oryginalne zastosowanie:** SCS Dimensionless Unit Hydrograph (nie Nash IUH).

#### Źródło 3: Giandotti (1934)

> "Giandotti's formula (Giandotti 1934) is extensively used in Italy."
>
> — Hydrological Sciences Journal: [Time of concentration: a paradox in modern hydrology](https://www.tandfonline.com/doi/full/10.1080/02626667.2011.644244)

**Oryginalne zastosowanie:** Włoskie zlewnie górskie (> 170 km²).

### 1.3. Relacja między Tc a parametrami Nasha (N, K)

#### Kluczowe znalezisko z literatury

> "In the Nash model, the **lag time equals nK** (the product of the number of linear reservoirs *n* and the storage coefficient *K*). This relationship is fundamental to the model."
>
> — Sciendo: [Nash Model Parameters Estimation](http://archive.sciendo.com/SGGW/sggw.2012.44.issue-2/v10060-011-0071-z/v10060-011-0071-z.pdf)

#### Porównanie SCS vs Nash

| Aspekt | SCS Unit Hydrograph | Nash IUH |
|--------|---------------------|----------|
| **Baza teoretyczna** | Empiryczny bezwymiarowy hydrogram | Kaskada liniowych zbiorników |
| **Parametry** | Tc, PRF (peak rate factor) | n (liczba zbiorników), K (stała magazynowania) |
| **Forma matematyczna** | Krzywa bezwymiarowa / trójkątna | Rozkład gamma |
| **Rola Tc** | **Parametr wejściowy** (Tp = D/2 + 0.6×Tc) | **BRAK** - lag = n×K jest wynikiem |

**Kluczowy wniosek:** W modelu SCS relacja `lag = 0.6 × Tc` jest **założeniem projektowym**. W modelu Nasha `lag = n × K` jest **wynikiem matematycznym** kaskady zbiorników. Te relacje NIE są zamienne.

---

## 2. Aktualny stan kodu

### 2.1. Moduł `hydrolog/runoff/nash_iuh.py`

#### Metoda `from_tc` (linie 594-657)

```python
@classmethod
def from_tc(
    cls,
    tc_min: float,
    n: Optional[float] = None,
    lag_ratio: float = 0.6,  # ← Relacja SCS!
) -> "NashIUH":
    # ...
    lag_time = lag_ratio * tc_min  # ← Założenie SCS
    k_min = lag_time / n
    return cls(n=n, k_min=k_min)
```

**Problem:** Metoda używa relacji `lag = 0.6 × Tc` która jest specyficzna dla SCS Unit Hydrograph, nie dla modelu Nasha. Brak naukowego uzasadnienia dla stosowania tej relacji w modelu Nasha.

#### Metoda `from_lutz` (linie 659-866)

```python
@classmethod
def from_lutz(
    cls,
    L_km: float,
    Lc_km: float,
    slope: float,
    manning_n: float,
    urban_pct: float = 0.0,
    forest_pct: float = 0.0,
    area_km2: Optional[float] = None,
) -> "NashIUH":
```

**Status:** ✅ PRAWIDŁOWA implementacja. Metoda Lutza (1984) została opracowana specjalnie dla estymacji parametrów modelu Nasha z cech fizjograficznych zlewni.

### 2.2. Moduł `hydrolog/time/concentration.py`

Zawiera trzy metody obliczania Tc:

| Metoda | Oryginalne zastosowanie | Status w Hydrolog |
|--------|-------------------------|-------------------|
| `kirpich()` | Małe zlewnie rolnicze, metoda racjonalna | ✅ Prawidłowa implementacja |
| `nrcs()` | SCS Unit Hydrograph | ✅ Prawidłowa implementacja |
| `giandotti()` | Włoskie zlewnie górskie | ✅ Prawidłowa implementacja |

**Ważne:** Te metody są **niezależne** od modułu Nash IUH. Problem występuje gdy użytkownik używa `NashIUH.from_tc()` z Tc obliczonym przez te metody.

### 2.3. Powiązania między modułami

```
┌─────────────────────────────────────────────────────────────────┐
│                    AKTUALNY STAN                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  concentration.py          nash_iuh.py                          │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │ kirpich()    │          │ NashIUH      │                     │
│  │ nrcs()       │──Tc──────│ ├─from_tc()  │ ← PROBLEMATYCZNE    │
│  │ giandotti()  │          │ └─from_lutz()│ ← PRAWIDŁOWE        │
│  └──────────────┘          └──────────────┘                     │
│                                                                 │
│  Brak bezpośredniego importu, ale użytkownik może               │
│  używać Tc z concentration.py w from_tc()                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4. Lista znalezionych problemów

| # | Problem | Lokalizacja | Priorytet |
|---|---------|-------------|-----------|
| 1 | `from_tc` używa relacji SCS `lag=0.6×Tc` bez uzasadnienia dla Nasha | `nash_iuh.py:654` | WYSOKI |
| 2 | Dokumentacja `from_tc` nie ostrzega o ograniczeniach metody | `nash_iuh.py:594-657` | ŚREDNI |
| 3 | Domyślne `n=3` w `from_tc` jest arbitralne | `nash_iuh.py:647` | NISKI |

---

## 3. Rekomendowana architektura

### 3.1. Metody które powinny pozostać w `nash_iuh.py`

| Metoda | Uzasadnienie |
|--------|--------------|
| `from_lutz()` | ✅ Specjalnie opracowana dla modelu Nasha (Lutz 1984, KZGW 2017) |
| `NashIUH.__init__(n, k_min)` | ✅ Bezpośrednie podanie parametrów |

### 3.2. Metody wymagające modyfikacji

#### Opcja A: Usunięcie `from_tc()` (REKOMENDOWANE)

**Uzasadnienie:**
- Brak naukowego uzasadnienia dla relacji `lag = 0.6 × Tc` w modelu Nasha
- Może prowadzić do błędnych wyników
- Użytkownicy powinni używać `from_lutz()` lub bezpośrednio podawać n i K

#### Opcja B: Zachowanie `from_tc()` z ostrzeżeniem (ALTERNATYWA)

Jeśli metoda ma pozostać dla kompatybilności wstecznej:

```python
@classmethod
def from_tc(
    cls,
    tc_min: float,
    n: Optional[float] = None,
    lag_ratio: float = 0.6,
) -> "NashIUH":
    """
    Create NashIUH from time of concentration.

    .. warning::
        This method uses the SCS relationship (lag = 0.6 × Tc) which was
        developed for the SCS Unit Hydrograph, NOT for the Nash model.
        For ungauged watersheds, prefer `from_lutz()` method which was
        specifically developed for Nash parameter estimation.

    ...
    """
    import warnings
    warnings.warn(
        "from_tc() uses SCS relationship (lag=0.6×Tc) which is not "
        "scientifically justified for Nash IUH. Consider using from_lutz() "
        "or providing n and K directly.",
        UserWarning,
        stacklevel=2
    )
    # ... reszta kodu
```

### 3.3. Moduł `concentration.py` - brak zmian

Metody Kirpich, SCS Lag i Giandotti są **prawidłowo zaimplementowane** i mają swoje uzasadnione zastosowania:
- Metoda racjonalna
- SCS Unit Hydrograph
- Ogólne szacowanie czasu koncentracji

**Nie należy ich usuwać** - problem leży w ich niewłaściwym użyciu z modelem Nasha.

### 3.4. Proponowana struktura modułów

```
┌─────────────────────────────────────────────────────────────────┐
│                    REKOMENDOWANA ARCHITEKTURA                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  concentration.py          nash_iuh.py                          │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │ kirpich()    │          │ NashIUH      │                     │
│  │ nrcs()       │          │ ├─__init__() │ ← Bezpośrednie n,K  │
│  │ giandotti()  │          │ └─from_lutz()│ ← Cechy fizjograf.  │
│  └──────────────┘          └──────────────┘                     │
│        │                                                        │
│        └──────────────────────────────────────────┐             │
│                                                   ▼             │
│                                          ┌──────────────┐       │
│                                          │ SCS UH       │       │
│                                          │ (scs_uh.py)  │       │
│                                          └──────────────┘       │
│                                                                 │
│  Tc z concentration.py → tylko do SCS UH, NIE do Nash IUH       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Plan działania

### Priorytet WYSOKI

| # | Działanie | Wpływ na API | Szacunkowa zmiana |
|---|-----------|--------------|-------------------|
| 1 | Dodać `DeprecationWarning` do `from_tc()` | Ostrzeżenie, brak breaking change | 5 linii |
| 2 | Zaktualizować dokumentację `from_tc()` z ostrzeżeniem | Brak | 20 linii docstring |
| 3 | Dodać test sprawdzający ostrzeżenie | Brak | 10 linii |

### Priorytet ŚREDNI

| # | Działanie | Wpływ na API | Szacunkowa zmiana |
|---|-----------|--------------|-------------------|
| 4 | Usunąć `from_tc()` w wersji 1.0.0 | **BREAKING CHANGE** | Usunięcie metody |
| 5 | Zaktualizować przykłady w dokumentacji | Brak | Aktualizacja docs |
| 6 | Dodać sekcję "Best Practices" do README | Brak | Nowa sekcja |

### Priorytet NISKI

| # | Działanie | Wpływ na API | Szacunkowa zmiana |
|---|-----------|--------------|-------------------|
| 7 | Rozważyć dodanie metody `from_moments()` | Nowa funkcjonalność | ~50 linii |
| 8 | Rozważyć dodanie metody `from_rosso()` (Horton ratios) | Nowa funkcjonalność | ~80 linii |

---

## 5. Podsumowanie

### Co jest PRAWIDŁOWE w obecnej architekturze:

1. ✅ **Metoda `from_lutz()`** - prawidłowa implementacja zgodna z literaturą
2. ✅ **Moduł `concentration.py`** - prawidłowe implementacje Kirpich, SCS Lag, Giandotti
3. ✅ **Brak bezpośredniego importu** między `concentration.py` a `nash_iuh.py`

### Co wymaga ZMIANY:

1. ⚠️ **Metoda `from_tc()`** - używa relacji SCS bez naukowego uzasadnienia dla modelu Nasha
2. ⚠️ **Dokumentacja** - brak ostrzeżenia o ograniczeniach `from_tc()`

### Rekomendacja końcowa:

**Opcja A (REKOMENDOWANE):** Oznaczenie `from_tc()` jako deprecated w wersji 0.7.0 i usunięcie w 1.0.0.

**Opcja B (ALTERNATYWA):** Zachowanie `from_tc()` z wyraźnym ostrzeżeniem w dokumentacji i runtime warning.

---

## 6. Źródła

### Prace oryginalne

1. Nash, J.E. (1957). The form of the instantaneous unit hydrograph. International Association of Scientific Hydrology, 45(3), 114-121.

2. Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds. Civil Engineering, 10(6), 362.

3. Giandotti, M. (1934). Previsione delle piene e delle magre dei corsi d'acqua. Memorie e Studi Idrografici, Vol. 8. Ministero dei Lavori Pubblici, Roma.

4. Lutz, W. (1984). Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen. Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe.

### Dokumentacja techniczna

5. USDA-NRCS (1986). Urban Hydrology for Small Watersheds. Technical Release 55 (TR-55).

6. KZGW (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych. Załącznik 2.

7. USACE HEC-HMS Technical Reference Manual - SCS Unit Hydrograph Model. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/scs-unit-hydrograph-model

### Publikacje naukowe

8. Rosso, R. (1984). Nash model relation to Horton order ratios. Water Resources Research, 20(7), 914-920.

9. Ahmad, M.M., Ghumman, A.R., Ahmad, S. (2009). Estimation of a Unique Pair of Nash Model Parameters. Water Resources Management, 23, 2263-2279. https://doi.org/10.1007/s11269-008-9378-z

10. Grimaldi, S. et al. (2012). Time of concentration: a paradox in modern hydrology. Hydrological Sciences Journal, 57(2), 217-228. https://doi.org/10.1080/02626667.2011.644244
