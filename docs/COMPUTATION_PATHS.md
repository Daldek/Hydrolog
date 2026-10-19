# Ścieżki obliczeniowe dla modeli hydrogramów jednostkowych (oraz HSG i rozkład Fishera–Tippetta)

**Wersja dokumentu:** 1.2
**Data:** 2026-10-19
**Dotyczy:** Hydrolog >= 1.0.0 (sekcje 3.3.6, 3.5 i 3.6 opisują zachowanie od v1.0.0; pozostałe: >= 0.6.0)

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

| Model | Kirpich | NRCS | Giandotti | FAA | Kerby | Kerby-Kirpich | from_lutz() | from_urban_regression() | Bezpośrednio | Własna metoda |
|-------|:-------:|:-------:|:---------:|:---:|:-----:|:-------------:|:-----------:|:-----------------------:|:------------:|:-------------:|
| **SCS UH** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - |
| **Nash IUH** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | - |
| **Clark IUH** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | ✅ | - |
| **Snyder UH** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | - | ✅ | ✅ |

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
    │    KIRPICH      │ │    NRCS     │ │  GIANDOTTI  │
    │ tc=3.981×L^0.77 │ │ tc=f(L,S,CN)│ │ tc=f(A,L,H) │
    │  ×S^(-0.385)    │ │             │ │             │
    │    [min]        │ │             │ │             │
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

> **Uwaga o stałej Kirpicha:** W literaturze spotyka się dwie równoważne formy:
> - `tc[min] = 3.981 × L[km]^0.77 × S^(-0.385)` (wynik w minutach -- używana w kodzie)
> - `tc[h] = 0.0663 × L[km]^0.77 × S^(-0.385)` (wynik w godzinach)
>
> Obie formy są tożsame: `3.981 / 60 ≈ 0.0663`. Implementacja w Hydrolog używa stałej **3.981** i zwraca wynik w **minutach**.

#### 3.1.2 Prawidłowe metody estymacji Tc

| Metoda | Status | Uzasadnienie |
|--------|--------|--------------|
| Kirpich | ✅ OK | Tc jest parametrem wejściowym metody SCS |
| NRCS | ✅ OK | Metoda opracowana razem z SCS UH (TR-55) |
| Giandotti | ✅ OK | Tc jest parametrem wejściowym metody SCS |
| FAA | ✅ OK | Tc jest parametrem wejściowym metody SCS (spływ powierzchniowy) |
| Kerby | ✅ OK | Tc jest parametrem wejściowym metody SCS (spływ arkuszowy) |
| Kerby-Kirpich | ✅ OK | Kompozytowe Tc (spływ powierzchniowy + korytowy) jest parametrem wejściowym SCS |

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

**Uwaga o czasie bazy (tb):** W kontekście SCS UH występują dwie wartości tb — obie są poprawne dla swoich celów:
- `tb ≈ 2.67 × tp` — przybliżenie trójkątne, używane do wyprowadzenia stałej 0.208
- `tb = 5.0 × tp` — pełny zakres bezwymiarowej tablicy NRCS (33 punkty), używany przy dyskretyzacji UH

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
    ┌──────────────────────────────────────────────────────────────────────┐
    │   METODA LUTZA            │  REGRESJA URBAN.    │  BEZPOŚREDNIE     │
    │  L_km, Lc_km, slope,      │  area_km2,          │  n (liczba zb.)   │
    │  manning_n, urban_pct,    │  effective_precip_mm,│  K [min]          │
    │  forest_pct              │  duration_h,         │                   │
    │                          │  urban_fraction      │                   │
    └──────────┬───────────────┴──────────┬───────────┴────────┬──────────┘
               │                          │                    │
               ▼                          ▼                    │
    ┌───────────────────────────┐ ┌───────────────────────┐    │
    │  NashIUH.from_lutz()      │ │ NashIUH               │    │
    │  ─────────────────────── │ │ .from_urban_regression │    │
    │  1. P1 = 3.989×n + 0.028 │ │ ──────────────────── │    │
    │  2. tp = P1×(L×Lc/       │ │ 1. tL = 1.28×A^0.46  │    │
    │     Jg^1.5)^0.26         │ │    ×(1+U)^(-1.66)    │    │
    │    ×e^(-0.016U)          │ │    ×H^(-0.27)        │    │
    │    ×e^(0.004W)           │ │    ×D^0.37           │    │
    │  3. up = 0.66/tp^1.04    │ │ 2. k = 0.56×A^0.39   │    │
    │  4. f(N) = tp×up →      │ │    ×(1+U)^(-0.62)    │    │
    │     rozwiąż dla N        │ │    ×H^(-0.11)        │    │
    │  5. K = tp / (N-1)       │ │    ×D^0.22           │    │
    └──────────┬────────────────┘ │ 3. N = tL / k        │    │
               │                  └──────────┬────────────┘    │
               │                             │                 │
               └─────────────┬───────────────┘                 │
                             └──────────────┬──────────────────┘
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
| `from_urban_regression()` | ✅ OK | Regresja dla zlewni zurbanizowanych (Rao, Delleur, Sarma 1972) |
| Bezpośrednio `n`, `K` | ✅ OK | Gdy masz skalibrowane wartości |
| ~~Metoda momentów~~ | USUNIĘTA w v0.5.1 | Wymaga danych z obserwowanego hydrogramu |
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

#### 3.2.5 Wzory metody regresji dla zlewni zurbanizowanych

Metoda `from_urban_regression()` wykorzystuje empiryczne równania regresji potęgowej
(Rao, Delleur, Sarma 1972) opracowane dla zlewni zurbanizowanych i częściowo
zurbanizowanych:

```
1. Czas opóźnienia:
   tL = 1.28 × A^0.46 × (1+U)^(-1.66) × H^(-0.27) × D^0.37        [h]

2. Stała magazynowania:
   k = 0.56 × A^0.39 × (1+U)^(-0.62) × H^(-0.11) × D^0.22         [h]

3. Liczba zbiorników:
   N = tL / k                                                        [-]
```

**Parametry wejściowe:**

| Symbol | Parametr | Jednostka |
|--------|----------|-----------|
| A | Powierzchnia zlewni | km² |
| U | Wskaźnik urbanizacji (0 = naturalna, 0.5 = 50% zurbanizowana) | - |
| H | Opad efektywny (suma) | mm |
| D | Czas trwania opadu efektywnego | h |

**Pochodzenie stałych metrycznych:**
Oryginalna regresja (Sarma, Delleur, Rao 1969) została opracowana w jednostkach
imperialnych (mi², in). Stałe metryczne 1.28 i 0.56 uwzględniają konwersję jednostek
i pojawiają się w publikacji ASCE z 1972 roku.

**Wpływ parametrów:**

| Czynnik | Wpływ na odpływ |
|---------|-----------------|
| ↑ Powierzchnia (A) | Wolniejszy (↑ tL, ↑ k) |
| ↑ Urbanizacja (U) | Szybszy (↓ tL, ↓ k) |
| ↑ Opad efektywny (H) | Szybszy (↓ tL, ↓ k) |
| ↑ Czas trwania (D) | Wolniejszy (↑ tL, ↑ k) |

#### 3.2.6 Przykład kodu - PRAWIDŁOWE UŻYCIE

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

# METODA 2: from_urban_regression() - dla zlewni zurbanizowanych
nash_urban = NashIUH.from_urban_regression(
    area_km2=1.3,
    effective_precip_mm=1.305,
    duration_h=0.167,
    urban_fraction=0.05,
)
print(f"n = {nash_urban.n:.3f}")
print(f"K = {nash_urban.k_min:.1f} min")

# METODA 3: Bezpośrednie podanie parametrów
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

#### 3.2.7 Przykład kodu - BŁĘDNE UŻYCIE (NIE RÓB TEGO!)

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
    │    KIRPICH      │ │    NRCS     │ │  GIANDOTTI  │
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
| NRCS → Tc | ✅ OK | Tc = czas translacji |
| Giandotti → Tc | ✅ OK | Tc = czas translacji |
| FAA → Tc | ✅ OK | Tc = czas translacji (spływ powierzchniowy) |
| Kerby → Tc | ✅ OK | Tc = czas translacji (spływ arkuszowy) |
| Kerby-Kirpich → Tc | ✅ OK | Tc = czas translacji (kompozytowy: spływ powierzchniowy + korytowy) |
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
   Krzywa HEC-HMS dla zlewni eliptycznej (dwuczęściowa):

   tau = t / Tc

   Dla tau ≤ 0.5:  A_cum(t) = 1.414 × tau^1.5
   Dla tau > 0.5:  A_cum(t) = 1.0 - 1.414 × (1.0 - tau)^1.5

   Warunki brzegowe:
   - A_cum(0)    = 0
   - A_cum(Tc/2) = 1.414 × 0.5^1.5 ≈ 0.5  (symetryczny centroid)
   - A_cum(Tc)   = 1.0

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

#### 3.3.6 Hydrogram D-minutowy z krzywej S (`to_unit_hydrograph`)

`ClarkIUH.to_unit_hydrograph(area_km2, duration_min, timestep_min)` przekształca IUH w hydrogram jednostkowy opadu efektywnego o czasie trwania D metodą krzywej S:

```
S(t)  = ∑ u(t_i) × dt                     (suma skumulowana rzędnych IUH; odpowiedź na ciągły opad o jednostkowej intensywności)
U_D(t) = [ S(t) - S(t - D) ] / D          (hydrogram jednostkowy dla opadu 1 mm w czasie D)
```

Krzywa S jest znana tylko w węzłach `t_i = i × dt`, więc opóźniona krzywa `S(t_i - D)` jest odczytywana interpolacją liniową (przed t = 0 jest równa 0). Dzięki temu **D nie musi być wielokrotnością kroku `dt`**:

| D / dt | Zachowanie |
|--------|------------|
| całkowite k (D = k·dt) | dokładnie krzywa S przesunięta o k kroków (jak dotąd) |
| niecałkowite (np. 1,5) | interpolacja liniowa między dwoma sąsiednimi węzłami; objętość UH = 1 mm |
| < 1 | S rozwiązana co najwyżej do kroku: wynik jak dla D = dt; do rozdzielenia krótkiego opadu użyj `timestep_min <= duration_min` |

Objętość hydrogramu (suma rzędnych × dt, przeliczona na warstwę wody nad zlewnią) wynosi **1 mm** dla dowolnego D > 0, o ile całą odpowiedź obejmuje `total_duration_min` (domyślnie `tc + 5R + D` gubi tylko pomijalny ogon).

> **Zmiana w v1.0.0 (poprawka błędu).** Wersje < 1.0.0 przesuwały krzywą S o `round(D/dt)` kroków, ale dzieliły przez D. Dla D niebędącego wielokrotnością kroku objętość wynosiła `round(D/dt)·dt/D` mm: **1,333 mm dla D = 1,5·dt** i 0,8 mm dla D = 2,5·dt (przepływy o 33% za duże lub 20% za małe), a dla D < dt/2 `to_unit_hydrograph` zgłaszało `ValueError` (`s_curve[:-0]`). Od v1.0.0 objętość wynosi 1,000 mm dla każdego D, a niedodatnie lub nieskończone D i krok zgłaszają `InvalidParameterError`.

```python
iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
# D = 1,5 kroku: objętość UH = 1 mm (dawniej 1,333 mm)
uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=7.5, timestep_min=5.0,
                            total_duration_min=1000.0)
print(f"{uh.ordinates_m3s.sum() * 5.0 * 60.0 / 45000.0:.3f} mm")   # 1.000 mm
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
│  ❌ ConcentrationTime.nrcs()                                          │
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

### 3.5 Grupy hydrologiczne gleb (HSG) i CN ważone powierzchnią (`hydrolog.soil`, od v1.0.0)

HSG (A-D) jest jednym z dwóch czynników liczby CN (drugim jest pokrycie terenu). Moduł `hydrolog.soil` wyznacza HSG z zawartości iłu, piasku i pyłu; reguły i mapowanie przeniesiono z Kartografa 0.8.0 (`kartograf.hydrology.hsg`, ADR-025), a Kartograf zostaje przy pobieraniu rastrów (`download_soil`).

#### 3.5.1 Diagram przepływu danych

```
Kartograf download_soil (property = clay | sand | silt, SoilGrids, g/kg)
        │   trzy rastry GeoTIFF: ten sam CRS, siatka i rozmiar
        ▼
hydrolog.soil.hsg_from_rasters(clay, sand, silt, output_path)      [dodatek hydrolog[raster]]
        │   klasa uziarnienia USDA (12 klas) → HSG; GeoTIFF uint8: 0 = brak danych, 1-4 = A-D
        ▼
hydrolog.soil.hsg_statistics(hsg_path, bbox=None, bbox_crs=None)
        │   powierzchnia (m², ha) i udział (%) grup A-D oraz brak danych
        ▼
get_cn(HSG, pokrycie terenu, stan) × powierzchnia grupy  →  calculate_weighted_cn(...)
        ▼
CN zlewni  →  SCSCN / HydrographGenerator
```

Te same kroki w CLI: `soil hsg`, `soil hsg-stats`, `cn weighted`; klasę uziarnienia i HSG pojedynczej próbki daje `soil texture` (`classify_usda_texture`, `texture_to_hsg`).

#### 3.5.2 Klasyfikacja uziarnienia (trójkąt USDA)

Reguły (c - ił, s - piasek, si - pył, w % sumy trzech frakcji), pierwsza spełniona wygrywa:

| # | Klasa | Warunek |
|---|-------|---------|
| 1 | `sand` | si + 1,5·c < 15 |
| 2 | `loamy_sand` | si + 1,5·c ≥ 15 i si + 2·c < 30 |
| 3 | `sandy_loam` | (7 ≤ c ≤ 20, s > 52, si + 2·c ≥ 30) lub (c < 7, si < 50, si + 2·c ≥ 30) |
| 4 | `silt` | si ≥ 80, c < 12 |
| 5 | `silt_loam` | (si ≥ 50, 12 ≤ c < 27) lub (50 ≤ si < 80, c < 12) |
| 6 | `loam` | 7 ≤ c ≤ 27, 28 ≤ si < 50, s ≤ 52 |
| 7 | `sandy_clay_loam` | 20 ≤ c < 35, si < 28, s > 45 |
| 8 | `clay_loam` | 27 ≤ c < 40, 20 < s ≤ 45 |
| 9 | `silty_clay_loam` | 27 ≤ c < 40, s ≤ 20 |
| 10 | `sandy_clay` | c ≥ 35, s > 45 |
| 11 | `silty_clay` | c ≥ 40, si ≥ 40 |
| 12 | `clay` | c ≥ 40, s ≤ 45, si < 40 |

- Reguły porównują **ilości** frakcji z ich sumą (bez dzielenia, w `float64`), więc wynik nie zależy od jednostki (%, g/kg), byle była wspólna dla trzech rastrów, a wartości na granicach trójkąta są klasyfikowane dokładnie.
- Suma równa zero daje `loam` w klasyfikatorze uziarnienia; w `classify_hsg` taka komórka (wszystkie trzy frakcje równe 0, konwencja SoilGrids dla luk) to brak danych.
- Brak danych (kod 0) to także NaN/±Inf i wartość równa znacznikowi `nodata` któregokolwiek z trzech rastrów. Ujemna ilość w komórce z danymi jest błędem.

#### 3.5.3 Uziarnienie → HSG

| HSG | Klasy uziarnienia |
|-----|-------------------|
| A | `sand`, `loamy_sand` |
| B | `sandy_loam`, `loam`, `silt_loam`, `silt` |
| C | `sandy_clay_loam`, `clay_loam`, `silty_clay_loam` |
| D | `sandy_clay`, `silty_clay`, `clay` |

Mapowanie jest **łagodniejsze niż tablica TR-55** (USDA-NRCS NEH Part 630, rozdz. 7) dla trzech klas przejściowych: `sandy_loam` = B (TR-55: A), `clay_loam` i `silty_clay_loam` = C (TR-55: D). Ich rzeczywista grupa zależy też od struktury gleby, a środkowa grupa jest dla metody SCS-CN ostrożna (Kartograf ADR-025, decyzja b). Zmiana tabeli `TEXTURE_TO_HSG` zmienia CN u każdego użytkownika.

#### 3.5.4 Statystyki powierzchni

- Powierzchnia komórki: dla układu współrzędnych **geograficznego** liczona geodezyjnie dla każdego wiersza rastra (zależy od szerokości), dla **rzutowanego** z transformacji afinicznej.
- `percent` grup A-D to udział w powierzchni **z danymi**, `percent` braku danych - udział w powierzchni całkowitej; sumy grup i braku danych dają `total_area_m2`.
- Opcjonalny prostokąt `bbox` (z `bbox_crs`) przycina statystykę z uwzględnieniem udziału komórek brzegowych.

#### 3.5.5 Przykład kodu

```python
from hydrolog.runoff import calculate_weighted_cn, get_cn
from hydrolog.soil import hsg_from_rasters, hsg_statistics   # wymaga hydrolog[raster]

hsg_from_rasters("clay.tif", "sand.tif", "silt.tif", output_path="hsg.tif")
stats = hsg_statistics("hsg.tif")

# CN ważone powierzchnią (jedno pokrycie terenu, np. łąka w dobrym stanie)
parts = [(get_cn(g, "meadow", "good"), s.area_ha)
         for g, s in stats.groups.items() if s.area_ha > 0]
cn = calculate_weighted_cn(parts)
```

> **Uwaga.** HSG nie jest liczbą CN. Przy kilku pokryciach terenu części CN są parami (HSG × pokrycie), a przecięcie rastra HSG z rastrem pokrycia terenu wykonuje się poza Hydrologiem.

---

### 3.6 Przepływy minimalne: rozkład Fishera–Tippetta dla minimów (`LowFlowAnalysis`, poprawka w v1.0.0)

`LowFlowAnalysis.fit_fisher_tippett()` dopasowuje do minimów rocznych (rok hydrologiczny XI-X) rozkład wartości **najmniejszych**: uogólniony rozkład wartości ekstremalnych (GEV) dla minimów, którego szczególnymi przypadkami są rozkład Gumbela dla minimów i trójparametrowy rozkład Weibulla.

#### 3.6.1 Wzory

```
Dystrybuanta minimów rocznych x:

   F(x) = 1 - exp( -( 1 + c × (x - loc) / scale )^(1/c) ),     1 + c × (x - loc) / scale > 0

   c → 0   rozkład Gumbela dla minimów:  F(x) = 1 - exp( -exp( (x - loc) / scale ) )
   c > 0   minima mają dolną granicę  loc - scale / c  (Weibull o kształcie 1/c)

Kwantyl o prawdopodobieństwie nieprzewyższenia p = 1/T (przepływ, który wystąpi raz na T lat
jako równy lub mniejszy):

   Q_T = loc + scale / c × ( (-ln(1 - p))^c - 1 )
```

Ponieważ minimum próby jest ujemnym maksimum próby ze zmienionym znakiem, `min(x) = -max(-x)`, parametry estymuje się metodą największej wiarygodności z **zanegowanych** minimów (`scipy.stats.genextreme`), a kwantyl to `Q_T = -genextreme.isf(p, c, loc=-loc, scale=scale)`. Raportowany `shape` to parametr `c` z `scipy.stats.genextreme` (czyli minus parametr kształtu ξ w zwykłej notacji GEV).

> **Zmiana w v1.0.0 (poprawka błędu).** Wersje < 1.0.0 dopasowywały do minimów wprost rozkład **maksimów** i czytały jego kwantyl w punkcie p. To rozkład zwierciadlany: poprawnie przybliża środek próby, ale jego lewy ogon nie jest ogonem rozkładu wartości najmniejszych, więc kwantyle rzadkich niżówek były obciążone, coraz bardziej wraz z T, i mogły być ujemne. Dla syntetycznej próby 1000 minimów rocznych z rozkładu Gumbela dla minimów (loc = 50, scale = 8) kwantyl dla T = 100 lat wynosił **−3821**, a od v1.0.0 wynosi **13,26** (wartość teoretyczna 13,20). Dla rozkładu Weibulla (k = 2, loc = 1, scale = 5) dla T = 100 lat: 1,24 → 1,51 (teoria 1,50), dla T = 1000 lat: 0,33 → 1,18 (teoria 1,16).

#### 3.6.2 Ograniczenia

- Rozkład nie jest ograniczony do przepływów dodatnich: przy `shape ≤ 0` minima nie mają dolnej granicy, a kwantyle bardzo długich okresów powtarzalności mogą być ujemne.
- Trzy parametry z kilkudziesięciu lat danych są niepewne, zwłaszcza kształt, a z nim kwantyle rzadkich niżówek (poniżej 10 lat danych wynik ma ostrzeżenie).
- Test Kołmogorowa-Smirnowa jest informacyjny (`ks_valid = False`: parametry estymowano z tych samych danych).

```python
from hydrolog.statistics import LowFlowAnalysis

analysis = LowFlowAnalysis(daily_flows, dates, return_periods=[10, 50, 100])
ft = analysis.fit_fisher_tippett()
print(ft.parameters)   # {"shape": ..., "loc": ..., "scale": ...}
print(ft.quantiles)    # przepływ [m³/s] raz na 10, 50, 100 lat
```

Ta sama analiza w CLI: `hydrolog stats low-flow --input-file q_dobowe.csv --value-column Q --date-column date --return-periods 10,50,100`.

---

## 4. Weryfikacja literaturowa

### 4.1 Tabela źródeł dla każdej ścieżki obliczeniowej

| Ścieżka obliczeniowa | Źródło | Status |
|----------------------|--------|:------:|
| SCS UH + Kirpich → Tc | USDA TR-55 (1986), Kirpich (1940) | ✅ |
| SCS UH + NRCS → Tc | USDA TR-55 (1986) | ✅ |
| SCS UH + Giandotti → Tc | Giandotti (1934), TR-55 | ✅ |
| SCS UH + FAA → Tc | FAA AC 150/5320-5D (2013), TR-55 | ✅ |
| SCS UH + Kerby → Tc | Kerby (1959), TR-55 | ✅ |
| Clark IUH + FAA → Tc | FAA AC 150/5320-5D (2013), Clark (1945) | ✅ |
| Clark IUH + Kerby → Tc | Kerby (1959), Clark (1945) | ✅ |
| SCS UH + Kerby-Kirpich → Tc | Roussel et al. (2005), TR-55 | ✅ |
| Clark IUH + Kerby-Kirpich → Tc | Roussel et al. (2005), Clark (1945) | ✅ |
| Nash IUH + from_lutz() | Lutz (1984), KZGW (2017) | ✅ |
| Nash IUH + from_urban_regression() | Rao, Delleur, Sarma (1972), Banasik (2009) | ✅ |
| Nash IUH + bezpośrednio n, K | Nash (1957) | ✅ |
| Nash IUH + from_tc() | **BRAK UZASADNIENIA** | ⚠️ |
| Clark IUH + Tc (dowolna metoda) | Clark (1945), HEC-HMS | ✅ |
| Clark IUH + R/Tc ratio | HEC-HMS, praktyka inżynierska | ✅ |
| Snyder UH + L, Lc, Ct, Cp | Snyder (1938) | ✅ |
| Clark UH D-minutowy (krzywa S, dowolne D > 0) | Clark (1945), metoda krzywej S (np. Chow, Maidment, Mays 1988) | ✅ |
| HSG z uziarnienia USDA (mapowanie klas) | USDA Soil Survey Manual (Handbook 18), NEH Part 630 rozdz. 7 (TR-55), Kartograf ADR-025 | ✅ (z odstępstwem dla 3 klas) |
| Rozkład minimów rocznych (GEV dla minimów) | Fisher i Tippett (1928), Gumbel (1958), Coles (2001) | ✅ |

### 4.2 Kluczowe publikacje

| Źródło | Rok | Znaczenie dla Hydrolog |
|--------|-----|------------------------|
| Nash, J.E. | 1957 | Podstawa teoretyczna modelu Nash IUH |
| Snyder, F.F. | 1938 | Definicja syntetycznego UH Snydera |
| Kirpich, Z.P. | 1940 | Formuła czasu koncentracji |
| Clark, C.O. | 1945 | Model translacja + zbiornik |
| FAA | 2013 | Formuła Tc dla spływu powierzchniowego (AC 150/5320-5D) |
| Kerby, W.S. | 1959 | Formuła Tc dla spływu arkuszowego (retardance coefficient) |
| Giandotti, M. | 1934 | Formuła Tc dla zlewni włoskich |
| Roussel, M.C. et al. | 2005 | Metoda kompozytowa Kerby-Kirpich (TxDOT 0-4696-2) |
| Rao, Delleur, Sarma | 1972 | Regresja parametrów Nasha dla zlewni zurbanizowanych |
| Lutz, W. | 1984 | Estymacja parametrów Nasha z cech fizjograficznych |
| USDA TR-55 | 1986 | Metoda SCS-CN, relacja tlag = 0.6×Tc |
| KZGW | 2017 | Polska metodyka, tabela f(N) dla Lutza |
| Fisher, R.A. i Tippett, L.H.C. | 1928 | Rozkłady graniczne wartości najmniejszej i największej próby |
| Gumbel, E.J. | 1958 | Statystyka wartości ekstremalnych (rozkład dla minimów) |
| Coles, S. | 2001 | Estymacja GEV metodą największej wiarygodności (rozdz. 3) |
| USDA Soil Survey Manual | 1993 | Trójkąt uziarnienia, klasy tekstury |

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

6. **Rao, R.A., Delleur, J.W., & Sarma, B.S.P.** (1972). Conceptual Hydrologic Models for Urbanizing Basins. *Journal of the Hydraulics Division, ASCE*, 98(HY7), 1205-1220.

7. **Sarma, P.B.S., Delleur, J.W., & Rao, A.R.** (1969). A Program in Urban Hydrology, Part II. *Purdue University Water Resources Research Center, Technical Report No. 9*. https://docs.lib.purdue.edu/watertech/8/

8. **Snyder, F.F.** (1938). Synthetic unit-graphs. *Transactions of the American Geophysical Union*, 19, 447-454.

### Dokumentacja techniczna

9. **FAA** (2013). Airport Drainage Design. Advisory Circular AC 150/5320-5D. Federal Aviation Administration, U.S. Department of Transportation.

10. **Kerby, W.S.** (1959). Time of concentration for overland flow. *Civil Engineering*, 29(3), 174.

11. **Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., & Garcia, C.A.** (2005). Time-parameter estimation for applicable Texas watersheds. *TxDOT Research Report 0-4696-2*. Texas Department of Transportation.

12. **KZGW** (2017). Aktualizacja metodyki obliczania przepływów i opadów maksymalnych. Załącznik 2, Tabela C.2.

13. **USACE HEC-HMS** (2024). Technical Reference Manual. https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/

14. **USDA-NRCS** (1986). Urban Hydrology for Small Watersheds. Technical Release 55 (TR-55).

### Podręczniki

15. **Banasik, K.** (2009). Wyznaczanie wezbrań powodziowych w małych zlewniach zurbanizowanych. *Wyd. SGGW, Warszawa*.

16. **Bedient, P.B. & Huber, W.C.** (1992). *Hydrology and Floodplain Analysis*. Addison-Wesley.

17. **Fisher, R.A. & Tippett, L.H.C.** (1928). Limiting forms of the frequency distribution of the largest or smallest member of a sample. *Proceedings of the Cambridge Philosophical Society*, 24(2), 180-190.

18. **Gumbel, E.J.** (1958). *Statistics of Extremes*. Columbia University Press, New York.

19. **Coles, S.** (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer, London.

20. **USDA** (1993). Soil Survey Manual. Handbook No. 18. Soil Survey Division Staff, USDA.

21. **USDA-NRCS** (2007). National Engineering Handbook, Part 630 Hydrology, Chapter 7: Hydrologic Soil Groups.

22. **Chow, V.T., Maidment, D.R. & Mays, L.W.** (1988). *Applied Hydrology*. McGraw-Hill (metoda krzywej S hydrogramu jednostkowego).

---

**Wersja dokumentu:** 1.2
**Data ostatniej aktualizacji:** 2026-10-19
