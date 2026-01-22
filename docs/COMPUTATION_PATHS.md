# Ścieżki obliczeniowe dla modeli hydrogramów jednostkowych

**Wersja dokumentu:** 1.0
**Data:** 2026-01-22
**Dotyczy:** Hydrolog >= 0.6.0

---

## 1. Wprowadzenie

### 1.1 Cel dokumentu

Hydrolog implementuje 4 modele hydrogramów jednostkowych: **SCS**, **Nash**, **Clark** i **Snyder**. Każdy model ma inne parametry wejściowe i różne metody ich estymacji.

**Nieprawidłowe połączenie metod** (np. użycie czasu koncentracji z wzoru Kirpicha do modelu Nasha przez `from_tc()`) może prowadzić do błędnych wyników bez naukowego uzasadnienia.

Dokument ten służy jako przewodnik, który:
- Jasno wskazuje **prawidłowe ścieżki obliczeniowe** dla każdego modelu
- **Ostrzega** przed nieprawidłowym użyciem metod
- Podaje **uzasadnienie literaturowe** dla każdej ścieżki

### 1.2 Macierz kompatybilności

| Model | Kirpich | SCS Lag | Giandotti | from_lutz() | Bezpośrednio | Własna metoda |
|-------|:-------:|:-------:|:---------:|:-----------:|:------------:|:-------------:|
| **SCS UH** | ✅ | ✅ | ✅ | - | - | - |
| **Nash IUH** | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | - |
| **Clark IUH** | ✅ | ✅ | ✅ | - | ✅ | - |
| **Snyder UH** | ❌ | ❌ | ❌ | - | ✅ | ✅ |

**Legenda:**
- ✅ **OK** - prawidłowe użycie, potwierdzone literaturą
- ⚠️ **DEPRECATED** - działające, ale bez uzasadnienia naukowego (będzie usunięte w v1.0.0)
- ❌ **NIE DOTYCZY** - model nie używa zewnętrznego Tc

---

## 2. Modele hydrogramów - przegląd

### 2.1 SCS Unit Hydrograph

| Cecha | Wartość |
|-------|---------|
| **Typ** | Syntetyczny, empiryczny |
| **Parametry wejściowe** | `area_km2`, `tc_min` |
| **Źródło** | USDA-NRCS TR-55 (1986) |
| **Charakterystyka** | Bezwymiarowa krzywa NRCS (33 punkty) |

**Kluczowa relacja:** `tlag = 0.6 × Tc` (część metody SCS)

### 2.2 Nash IUH

| Cecha | Wartość |
|-------|---------|
| **Typ** | Koncepcyjny (kaskada zbiorników liniowych) |
| **Parametry wejściowe** | `n` (liczba zbiorników), `k_min` (stała magazynowania) |
| **Źródło** | Nash (1957), Lutz (1984) |
| **Charakterystyka** | Rozkład gamma, `u(t) = (t/K)^(n-1) × e^(-t/K) / (K×Γ(n))` |

**Kluczowa relacja:** `tlag = n × K` (wynik matematyczny, nie założenie!)

### 2.3 Clark IUH

| Cecha | Wartość |
|-------|---------|
| **Typ** | Koncepcyjny (translacja + zbiornik liniowy) |
| **Parametry wejściowe** | `tc_min` (czas translacji), `r_min` (stała retencji) |
| **Źródło** | Clark (1945), HEC-HMS |
| **Charakterystyka** | Histogram czas-powierzchnia + routing |

**Kluczowa relacja:** Tc = czas translacji przez zlewnię

### 2.4 Snyder UH

| Cecha | Wartość |
|-------|---------|
| **Typ** | Syntetyczny, empiryczny |
| **Parametry wejściowe** | `L_km`, `Lc_km`, `Ct`, `Cp` |
| **Źródło** | Snyder (1938) |
| **Charakterystyka** | Wbudowana estymacja: `tL = Ct × (L × Lc)^0.3` |

**Kluczowa relacja:** Model **NIE potrzebuje** zewnętrznego Tc!

---

## 3. Ścieżki obliczeniowe - szczegóły

### 3.1 SCS Unit Hydrograph

#### 3.1.1 Diagram przepływu danych

```
                    DANE WEJŚCIOWE
                    ┌─────────────────┐
                    │  L_km, S (m/m)  │
                    │     CN (opt)    │
                    │   A_km², H_m    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │    KIRPICH      │ │   SCS LAG   │ │  GIANDOTTI  │
    │ tc=0.0663×L^0.77│ │ tc=f(L,S,CN)│ │ tc=f(A,L,H) │
    │    ×S^(-0.385)  │ │             │ │             │
    └────────┬────────┘ └──────┬──────┘ └──────┬──────┘
             │                 │               │
             └─────────────────┼───────────────┘
                               ▼
                         ┌──────────┐
                         │   Tc     │
                         │  [min]   │
                         └────┬─────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 │                 ▼
    ┌───────────────┐         │         ┌───────────────┐
    │  tlag = 0.6×Tc│ ←───────┴─────────│ RELACJA SCS   │
    └───────┬───────┘                   │ (TR-55, 1986) │
            │                           └───────────────┘
            ▼
    ┌───────────────────────┐
    │  tp = D/2 + tlag      │ D = krok czasowy
    │  qp = 0.208 × A / tp  │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │   SCS UNIT HYDROGRAPH │
    │   (tablica 33 punkty) │
    └───────────────────────┘
```

#### 3.1.2 Prawidłowe metody estymacji Tc

| Metoda | Status | Uzasadnienie |
|--------|--------|--------------|
| Kirpich | ✅ OK | Tc jest parametrem wejściowym metody SCS |
| SCS Lag | ✅ OK | Metoda opracowana razem z SCS UH (TR-55) |
| Giandotti | ✅ OK | Tc jest parametrem wejściowym metody SCS |

**Uzasadnienie literaturowe:**
- Relacja `tlag = 0.6 × Tc` pochodzi z USDA TR-55 (1986)
- Została opracowana **specjalnie** dla SCS Dimensionless Unit Hydrograph
- Wszystkie metody obliczania Tc są odpowiednie jako wejście

#### 3.1.3 Wzory

```
tlag = 0.6 × Tc                              [min]
tp = D/2 + tlag                              [min]   (D = krok czasowy)
qp = 0.208 × A / tp                          [m³/s/mm]   (tp w godzinach!)
tb = 5.0 × tp                                [min]
```

**Wyprowadzenie stałej 0.208:**
- Dla trójkątnego przybliżenia: V = 0.5 × qp × tb
- Objętość 1 mm na A km²: V = A × 1000 m³
- Z tb ≈ 2.67 × tp: qp = 2V / (2.67 × tp × 3600) ≈ 0.208 × A / tp

#### 3.1.4 Przykład kodu

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import SCSUnitHydrograph, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Krok 1: Oblicz Tc dowolną metodą
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
print(f"Tc (Kirpich) = {tc:.1f} min")

# Krok 2: Utwórz SCS UH
scs_uh = SCSUnitHydrograph(area_km2=45.0, tc_min=tc)
result = scs_uh.generate(timestep_min=5.0)

print(f"tlag = {result.lag_time_min:.1f} min")
print(f"tp = {result.time_to_peak_min:.1f} min")
print(f"qp = {result.peak_discharge_m3s:.2f} m³/s/mm")

# Krok 3: Pełna transformacja opad → odpływ
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=tc)
hydrograph = generator.generate(precip)

print(f"Qmax = {hydrograph.peak_discharge_m3s:.2f} m³/s")
```

---

### 3.2 Nash IUH

#### 3.2.1 Diagram - prawidłowe ścieżki

```
                           DANE WEJŚCIOWE
    ┌─────────────────────────────────────────────────────────┐
    │        METODA LUTZA                 │  BEZPOŚREDNIE     │
    │  L_km, Lc_km, slope, manning_n      │  n (liczba zb.)   │
    │  urban_pct, forest_pct              │  K [min]          │
    └─────────────────┬───────────────────┴────────┬──────────┘
                      │                            │
                      ▼                            │
    ┌─────────────────────────────────────┐        │
    │          NashIUH.from_lutz()        │        │
    │  ────────────────────────────       │        │
    │  1. P1 = 3.989×n_manning + 0.028    │        │
    │  2. tp = P1×(L×Lc/Jg^1.5)^0.26      │        │
    │        ×e^(-0.016U)×e^(0.004W)      │        │
    │  3. up = 0.66 / tp^1.04             │        │
    │  4. f(N) = tp×up → rozwiąż dla N    │        │
    │  5. K = tp / (N-1)                  │        │
    └─────────────────┬───────────────────┘        │
                      │                            │
                      └────────────┬───────────────┘
                                   ▼
                           ┌───────────────┐
                           │   n, K [min]  │
                           └───────┬───────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │         NASH IUH             │
                    │  u(t) = (t/K)^(n-1)×e^(-t/K) │
                    │        / (K × Γ(n))          │
                    └──────────────────────────────┘
```

#### 3.2.2 OSTRZEŻENIE: from_tc() jest DEPRECATED

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ⚠️  ŚCIEŻKA DEPRECATED  ⚠️                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  Metoda NashIUH.from_tc() używa relacji: tlag = 0.6 × Tc           │
│                                                                     │
│  Ta relacja pochodzi z metody SCS (TR-55, 1986) i NIE ma           │
│  naukowego uzasadnienia dla modelu Nasha!                          │
│                                                                     │
│  W modelu Nasha: tlag = n × K jest WYNIKIEM MATEMATYCZNYM          │
│  kaskady zbiorników, NIE parametrem wejściowym!                    │
│                                                                     │
│  ┌─────────────────────────┐       ┌─────────────────────────┐     │
│  │   SCS Unit Hydrograph   │       │      Nash IUH           │     │
│  ├─────────────────────────┤       ├─────────────────────────┤     │
│  │ tlag = 0.6 × Tc         │       │ tlag = n × K            │     │
│  │ (ZAŁOŻENIE PROJEKTOWE)  │       │ (WYNIK MATEMATYCZNY)    │     │
│  │ Tc jest WEJŚCIEM        │       │ n, K są WEJŚCIEM       │     │
│  └─────────────────────────┘       └─────────────────────────┘     │
│                                                                     │
│  KONSEKWENCJE BŁĘDNEGO UŻYCIA:                                     │
│  - Parametr K obliczany z nieprawidłowej zależności                │
│  - Kształt IUH może nie odpowiadać charakterystyce zlewni          │
│  - Brak możliwości weryfikacji z danymi obserwowanymi              │
│                                                                     │
│  ROZWIĄZANIE:                                                       │
│  Użyj NashIUH.from_lutz() lub podaj n i K bezpośrednio            │
└─────────────────────────────────────────────────────────────────────┘
```

**Status:** `from_tc()` zostanie usunięta w wersji 1.0.0

#### 3.2.3 Prawidłowe metody estymacji

| Metoda | Status | Uzasadnienie |
|--------|--------|--------------|
| `from_lutz()` | ✅ ZALECANA | Opracowana specjalnie dla Nasha (Lutz, 1984) |
| Bezpośrednio `n`, `K` | ✅ OK | Gdy masz skalibrowane wartości |
| Metoda momentów | ✅ OK | Wymaga danych z obserwowanego hydrogramu |
| `from_tc()` | ⚠️ DEPRECATED | Brak uzasadnienia naukowego |

#### 3.2.4 Wzory metody Lutza

```
1. P₁ = 3.989 × n_manning + 0.028

2. tp = P₁ × (L × Lc / Jg^1.5)^0.26 × e^(-0.016U) × e^(0.004W)   [h]

3. up = 0.66 / tp^1.04                                            [1/h]

4. f(N) = tp × up → rozwiąż numerycznie dla N
   (gdzie f(N) = (N-1)^N × e^(-(N-1)) / Γ(N))

5. K = tp / (N-1)                                                 [h]
```

**Wpływ parametrów fizjograficznych:**

| Czynnik | Wpływ na odpływ |
|---------|-----------------|
| ↑ Las (W) | Wolniejszy (↑ tp, ↑ tlag) |
| ↑ Urbanizacja (U) | Szybszy (↓ tp, ↓ tlag) |
| ↑ Spadek (Jg) | Szybszy (↓ tp) |
| ↑ Manning (n) | Wolniejszy (↑ tp) |

#### 3.2.5 Przykład kodu - PRAWIDŁOWE UŻYCIE

```python
from hydrolog.runoff import NashIUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# METODA 1: from_lutz() - ZALECANA dla zlewni bez danych pomiarowych
nash = NashIUH.from_lutz(
    L_km=15.0,          # Długość cieku głównego
    Lc_km=8.0,          # Długość do centroidu zlewni
    slope=0.02,         # Spadek cieku
    manning_n=0.035,    # Współczynnik Manninga
    forest_pct=40.0,    # Udział lasów [%]
    urban_pct=5.0,      # Udział urbanizacji [%]
    area_km2=50.0       # Powierzchnia zlewni
)
print(f"n = {nash.n:.2f}")
print(f"K = {nash.k_min:.1f} min")
print(f"tlag = {nash.lag_time_min:.1f} min")

# METODA 2: Bezpośrednie podanie parametrów
# (gdy masz skalibrowane wartości)
nash_direct = NashIUH(n=3.5, k_min=45.0, area_km2=50.0)

# Generowanie hydrogramu
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(
    area_km2=50.0, cn=72,
    uh_model="nash",
    uh_params={"n": nash.n, "k": nash.k_min / 60.0, "k_unit": "hours"}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

#### 3.2.6 Przykład kodu - BŁĘDNE UŻYCIE (NIE RÓB TEGO!)

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import NashIUH

# ⚠️ NIEPRAWIDŁOWE - TO WYEMITUJE DeprecationWarning!
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
nash = NashIUH.from_tc(tc_min=tc, n=3.0)  # DEPRECATED!

# Zamiast tego użyj from_lutz():
nash_correct = NashIUH.from_lutz(
    L_km=8.2, Lc_km=4.5, slope=0.023, manning_n=0.035
)
```

---

### 3.3 Clark IUH

#### 3.3.1 Diagram przepływu danych

```
                    DANE WEJŚCIOWE
                    ┌─────────────────┐
                    │  L_km, S (m/m)  │
                    │  A_km², H_m     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │    KIRPICH      │ │   SCS LAG   │ │  GIANDOTTI  │
    └────────┬────────┘ └──────┬──────┘ └──────┬──────┘
             │                 │               │
             └─────────────────┼───────────────┘
                               ▼
                         ┌──────────┐
                         │   Tc     │  ← CZAS TRANSLACJI
                         │  [min]   │
                         └────┬─────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │     Tc        │   │  R [min]      │
            │  (translacja) │   │  (retencja)   │
            └───────┬───────┘   └───────┬───────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
            ┌──────────────────────────────────┐
            │           CLARK IUH              │
            │  1. Histogram czas-powierzchnia  │
            │  2. Routing przez zbiornik       │
            │     liniowy (S = R × O)          │
            └──────────────────────────────────┘
```

#### 3.3.2 Prawidłowe metody estymacji

| Metoda | Status | Uzasadnienie |
|--------|--------|--------------|
| Kirpich → Tc | ✅ OK | Tc = czas translacji (zgodne z modelem Clark) |
| SCS Lag → Tc | ✅ OK | Tc = czas translacji |
| Giandotti → Tc | ✅ OK | Tc = czas translacji |
| Bezpośrednio Tc, R | ✅ OK | Gdy masz zmierzone/skalibrowane wartości |
| R/Tc ratio | ✅ OK | Typowe wartości: 0.2-1.5 |

**Uzasadnienie literaturowe:**
- W modelu Clarka, Tc reprezentuje **czas translacji** - czas przejścia wody od najdalszego punktu zlewni do ujścia
- Jest to **zgodne** z fizyczną interpretacją czasu koncentracji
- Źródło: Clark (1945), HEC-HMS Technical Reference Manual

#### 3.3.3 Dobór współczynnika R

| Typ zlewni | R/Tc ratio | Opis |
|------------|------------|------|
| Strome, miejskie | 0.2-0.4 | Mała retencja, szybki odpływ |
| Naturalne, przeciętne | 0.4-0.8 | Typowe warunki |
| Płaskie, bagienne | 0.8-1.5 | Duża retencja, wolny odpływ |

#### 3.3.4 Wzory

```
Model dwuetapowy:

1. TRANSLACJA (histogram czas-powierzchnia):
   A_cum(t) = 1.414 × (t/Tc)^0.5 - 0.414 × (t/Tc)^1.5   dla t ≤ Tc
   (uproszczona krzywa dla zlewni eliptycznej)

2. ATENUACJA (zbiornik liniowy):
   O(t) = O(t-1) + C1 × (I(t) + I(t-1) - 2×O(t-1))
   gdzie C1 = dt / (2R + dt)
```

#### 3.3.5 Przykład kodu

```python
from hydrolog.time import ConcentrationTime
from hydrolog.runoff import ClarkIUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Krok 1: Oblicz Tc
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Krok 2: Określ współczynnik retencji R
r_min = 0.5 * tc  # R/Tc = 0.5 (typowa wartość)

# Krok 3: Utwórz Clark IUH
clark = ClarkIUH(tc_min=tc, r_min=r_min, area_km2=45.0)
result = clark.generate(timestep_min=5.0)

print(f"Tc = {tc:.1f} min")
print(f"R = {r_min:.1f} min")
print(f"Qmax UH = {result.peak_discharge_m3s:.2f} m³/s/mm")

# Alternatywnie: metoda from_tc_r_ratio
clark_alt = ClarkIUH.from_tc_r_ratio(tc_min=tc, r_tc_ratio=0.5)

# Pełna transformacja
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

generator = HydrographGenerator(
    area_km2=45.0, cn=72, tc_min=tc,
    uh_model="clark",
    uh_params={"r": r_min}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

---

### 3.4 Snyder UH

#### 3.4.1 Diagram przepływu danych

```
                    DANE WEJŚCIOWE
    ┌───────────────────────────────────────────────────────┐
    │  A_km²  - powierzchnia zlewni                         │
    │  L_km   - długość cieku głównego                      │
    │  Lc_km  - długość do centroidu zlewni                 │
    │  Ct     - współczynnik czasowy (1.35-1.65)            │
    │  Cp     - współczynnik szczytowy (0.4-0.8)            │
    └───────────────────────┬───────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │              WBUDOWANA METODA SNYDERA                 │
    │  ───────────────────────────────────────────────      │
    │  tL = Ct × (L × Lc)^0.3           [h]                │
    │       ↑                                               │
    │       └─── WŁASNA FORMUŁA (NIE Kirpich!)              │
    │                                                       │
    │  tD = tL / 5.5                    [h] (standardowy)   │
    │  tp = tL + tD/2                   [h]                 │
    │  qp = 0.275 × Cp × A / tL         [m³/s/mm]          │
    └───────────────────────┬───────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │                    SNYDER UH                          │
    │              (kształt gamma-podobny)                  │
    └───────────────────────────────────────────────────────┘
```

#### 3.4.2 Model NIE używa zewnętrznego Tc!

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ⚠️  MODEL SNYDERA NIE POTRZEBUJE ZEWNĘTRZNEGO Tc!                   │
│                                                                       │
│  Snyder ma WŁASNĄ metodę estymacji czasu opóźnienia (tL)             │
│  na podstawie L, Lc i współczynnika Ct.                              │
│                                                                       │
│  NIE UŻYWAJ z modelem Snydera:                                       │
│  ❌ ConcentrationTime.kirpich()                                       │
│  ❌ ConcentrationTime.scs_lag()                                       │
│  ❌ ConcentrationTime.giandotti()                                     │
│                                                                       │
│  Użycie zewnętrznego Tc byłoby nieuzasadnione metodologicznie,       │
│  ponieważ model Snydera został opracowany jako KOMPLETNA metoda.     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

#### 3.4.3 Wzory

**Dla standardowego czasu trwania (Δt = tD):**
```
tL = Ct × (L × Lc)^0.3                   [h]
tD = tL / 5.5                            [h]
tp = tL + tD/2                           [h]
qp = 0.275 × Cp × A / tL                 [m³/s/mm]
```

**Dla niestandardowego czasu trwania (Δt ≠ tD):**
```
tLR = tL + 0.25 × (Δt - tD)              [h]
tpR = tLR + Δt/2                         [h]
qpR = qp × (tL / tLR)                    [m³/s/mm]
tb = 0.556 × A / qpR                     [h]
```

#### 3.4.4 Dobór współczynników Ct i Cp

| Typ zlewni | Ct (SI) | Cp | Opis |
|------------|---------|-----|------|
| Górska, stroma | 1.35-1.45 | 0.60-0.80 | Szybki odpływ, mała retencja |
| Pagórkowata | 1.45-1.55 | 0.50-0.65 | Typowe warunki |
| Nizinna, płaska | 1.55-1.65 | 0.40-0.55 | Wolny odpływ, duża retencja |

**Uwaga:** Ct i Cp są **odwrotnie skorelowane** (większy Ct → mniejszy Cp)

#### 3.4.5 Przykład kodu

```python
from hydrolog.runoff import SnyderUH, HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Snyder NIE potrzebuje zewnętrznego Tc!
snyder = SnyderUH(
    area_km2=100.0,
    L_km=15.0,      # Długość cieku
    Lc_km=8.0,      # Długość do centroidu
    ct=1.5,         # Współczynnik czasowy
    cp=0.6          # Współczynnik szczytowy
)

# Parametry są obliczane automatycznie
print(f"tL = {snyder.lag_time_min:.1f} min")
print(f"tD = {snyder.standard_duration_min:.1f} min")

# Generowanie UH dla konkretnego czasu trwania opadu
delta_t = 60  # min
print(f"tpR = {snyder.time_to_peak_min(delta_t):.1f} min")
print(f"qpR = {snyder.peak_discharge(delta_t):.3f} m³/s/mm")

result = snyder.generate(timestep_min=10.0, duration_min=delta_t)

# Z HydrographGenerator
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=10.0)

generator = HydrographGenerator(
    area_km2=100.0, cn=72,
    uh_model="snyder",
    uh_params={"L_km": 15.0, "Lc_km": 8.0, "ct": 1.5, "cp": 0.6}
)
result = generator.generate(precip)
print(f"Qmax = {result.peak_discharge_m3s:.2f} m³/s")
```

---

## 4. Weryfikacja literaturowa

### 4.1 Tabela źródeł dla każdej ścieżki obliczeniowej

| Ścieżka obliczeniowa | Źródło | Status |
|----------------------|--------|:------:|
| SCS UH + Kirpich → Tc | USDA TR-55 (1986), Kirpich (1940) | ✅ |
| SCS UH + SCS Lag → Tc | USDA TR-55 (1986) | ✅ |
| SCS UH + Giandotti → Tc | Giandotti (1934), TR-55 | ✅ |
| Nash IUH + from_lutz() | Lutz (1984), KZGW (2017) | ✅ |
| Nash IUH + bezpośrednio n, K | Nash (1957) | ✅ |
| Nash IUH + from_tc() | **BRAK UZASADNIENIA** | ⚠️ |
| Clark IUH + Tc (dowolna metoda) | Clark (1945), HEC-HMS | ✅ |
| Clark IUH + R/Tc ratio | HEC-HMS, praktyka inżynierska | ✅ |
| Snyder UH + L, Lc, Ct, Cp | Snyder (1938) | ✅ |

### 4.2 Kluczowe publikacje

| Źródło | Rok | Znaczenie dla Hydrolog |
|--------|-----|------------------------|
| Nash, J.E. | 1957 | Podstawa teoretyczna modelu Nash IUH |
| Snyder, F.F. | 1938 | Definicja syntetycznego UH Snydera |
| Kirpich, Z.P. | 1940 | Formuła czasu koncentracji |
| Clark, C.O. | 1945 | Model translacja + zbiornik |
| Giandotti, M. | 1934 | Formuła Tc dla zlewni włoskich |
| Lutz, W. | 1984 | Estymacja parametrów Nasha z cech fizjograficznych |
| USDA TR-55 | 1986 | Metoda SCS-CN, relacja tlag = 0.6×Tc |
| KZGW | 2017 | Polska metodyka, tabela f(N) dla Lutza |

---

## 5. Typowe błędy i jak ich uniknąć

### 5.1 Błąd: Nash IUH + Kirpich bez from_lutz()

```
┌─────────────────────────────────────────────────────────────────────┐
│  BŁĄD: Użycie ConcentrationTime.kirpich() → NashIUH.from_tc()      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  from_tc() zakłada: tlag = 0.6 × Tc                                │
│  Ta relacja jest specyficzna dla metody SCS i NIE ma naukowego     │
│  uzasadnienia dla modelu Nasha.                                     │
│                                                                     │
│  KONSEKWENCJE:                                                      │
│  - Parametr K jest obliczany z błędnej zależności                  │
│  - Kształt IUH może nie odpowiadać charakterystyce zlewni          │
│  - Wyniki mogą znacząco różnić się od metod skalibrowanych         │
│                                                                     │
│  ROZWIĄZANIE:                                                       │
│  Użyj NashIUH.from_lutz() z parametrami fizjograficznymi:          │
│  - L_km (długość cieku)                                            │
│  - Lc_km (odległość do centroidu)                                  │
│  - slope (spadek)                                                   │
│  - manning_n (współczynnik Manninga)                               │
│  - forest_pct, urban_pct (pokrycie terenu)                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Błąd: Snyder UH + zewnętrzne Tc

```
┌─────────────────────────────────────────────────────────────────────┐
│  BŁĄD: Obliczanie Tc metodą Kirpicha i przekazywanie do Snydera    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  Model Snydera ma WBUDOWANĄ formułę estymacji czasu opóźnienia:    │
│  tL = Ct × (L × Lc)^0.3                                            │
│                                                                     │
│  NIE ISTNIEJE parametr "tc" w konstruktorze SnyderUH!              │
│                                                                     │
│  ROZWIĄZANIE:                                                       │
│  Podaj L_km i Lc_km bezpośrednio:                                  │
│                                                                     │
│  snyder = SnyderUH(                                                │
│      area_km2=100,                                                 │
│      L_km=15,      # długość cieku                                 │
│      Lc_km=8,      # do centroidu                                  │
│      ct=1.5,                                                       │
│      cp=0.6                                                        │
│  )                                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Błąd: Mieszanie jednostek K w modelu Nasha

```
┌─────────────────────────────────────────────────────────────────────┐
│  BŁĄD: Podanie K w godzinach gdy oczekiwane minuty (lub odwrotnie) │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROBLEM:                                                           │
│  - NashIUH(k_min=...) oczekuje K w MINUTACH                        │
│  - HydrographGenerator(uh_params={"k": ...}) domyślnie w GODZINACH │
│                                                                     │
│  ROZWIĄZANIE:                                                       │
│  Zawsze określaj jednostkę jawnie:                                 │
│                                                                     │
│  # Bezpośrednio (zawsze minuty)                                    │
│  nash = NashIUH(n=3, k_min=45.0)                                   │
│                                                                     │
│  # Przez HydrographGenerator (domyślnie godziny)                   │
│  gen = HydrographGenerator(                                        │
│      uh_model="nash",                                              │
│      uh_params={"n": 3, "k": 0.75, "k_unit": "hours"}  # 45 min   │
│  )                                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Referencje

### Publikacje oryginalne

1. **Clark, C.O.** (1945). Storage and the Unit Hydrograph. *Transactions of the American Society of Civil Engineers*, 110, 1419-1446.

2. **Giandotti, M.** (1934). Previsione delle piene e delle magre dei corsi d'acqua. *Memorie e Studi Idrografici*, Vol. 8. Ministero dei Lavori Pubblici, Roma.

3. **Kirpich, Z.P.** (1940). Time of concentration of small agricultural watersheds. *Civil Engineering*, 10(6), 362.

4. **Lutz, W.** (1984). Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen. *Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft*, H. 24, Universität Karlsruhe.

5. **Nash, J.E.** (1957). The form of the instantaneous unit hydrograph. *International Association of Scientific Hydrology*, 45(3), 114-121.

6. **Snyder, F.F.** (1938). Synthetic unit-graphs. *Transactions of the American Geophysical Union*, 19, 447-454.

### Dokumentacja techniczna

7. **KZGW** (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych. Załącznik 2, Tabela C.2.

8. **USACE HEC-HMS** (2024). Technical Reference Manual. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/

9. **USDA-NRCS** (1986). Urban Hydrology for Small Watersheds. Technical Release 55 (TR-55).

### Podręczniki

10. **Bedient, P.B. & Huber, W.C.** (1992). *Hydrology and Floodplain Analysis*. Addison-Wesley.

---

**Wersja dokumentu:** 1.0
**Data ostatniej aktualizacji:** 2026-01-22
