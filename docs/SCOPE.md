# SCOPE.md - Zakres Projektu Hydrolog

## Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.0
**Data:** 2026-01-18
**Status:** W trakcie realizacji

---

## 1. Wprowadzenie

### 1.1 Cel Projektu

**Hydrolog** to biblioteka Python dostarczająca narzędzia do obliczeń hydrologicznych. Zaprojektowana jako zewnętrzna zależność dla projektu Hydrograf oraz innych systemów wymagających funkcji hydrologicznych.

### 1.2 Główne cele

- Generowanie hydrogramów odpływu (SCS-CN)
- Obliczanie parametrów morfometrycznych zlewni
- Generowanie hietogramów (rozkład opadu w czasie)
- Interpolacja danych opadowych
- Klasyfikacja sieci rzecznej

### 1.3 Analogia

Hydrolog jest analogiczny do **Kartografa** (pobieranie danych przestrzennych) - modularna biblioteka Python z czystym API, możliwa do użycia jako zależność w innych projektach.

---

## 2. ZAKRES FUNKCJONALNY

### 2.1 ✅ IN SCOPE - Funkcjonalności

#### 2.1.1 Moduł `runoff` - Opad-Odpływ (v0.1.0)

**Metoda SCS Curve Number:**
- Obliczanie retencji maksymalnej: `S = 25400/CN - 254`
- Obliczanie abstrakcji początkowej: `Ia = 0.2 × S`
- Obliczanie opadu efektywnego: `Pe = (P - Ia)² / (P + 0.8S)`
- Warunki wilgotnościowe: AMC-I, AMC-II (domyślne), AMC-III

**Hydrogram jednostkowy SCS:**
- Czas do szczytu: `tp = 0.6 × tc`
- Przepływ szczytowy: `qp = 0.208 × A / tp`
- Czas bazowy: `tb = 2.67 × tp`
- Bezwymiarowy rozkład czasowy

**Transformacja opad → odpływ:**
- Splot dyskretny (convolution): `Q(t) = Pe(t) ⊗ UH(t)`
- Krok czasowy: konfigurowalny (domyślnie 5 min)

**Wyniki:**
- Qmax - przepływ maksymalny [m³/s]
- Czas do szczytu [min]
- Objętość odpływu [m³]
- Współczynnik odpływu [-]
- Szereg czasowy: czas vs przepływ

**Integracja z Kartografem (opcjonalna):**
- Automatyczne wyznaczanie CN z danych glebowych HSG (Hydrologic Soil Groups)
- Grupy hydrologiczne A, B, C, D z SoilGrids (tekstura gleby)
- Tabele CN według USDA-NRCS dla kombinacji HSG + pokrycie terenu

---

#### 2.1.2 Moduł `precipitation` - Opady (v0.1.0 / v0.3.0)

**Hietogramy (v0.1.0):**
- Rozkład Beta (α, β konfigurowalne, domyślnie α=2, β=5)
- Rozkład blokowy (stała intensywność)
- Rozkład trójkątny
- Rozkład NRCS Type II (opcjonalnie)

**Interpolacja (v0.3.0):**
- IDW (Inverse Distance Weighting)
- Thiessen (Voronoi polygons)
- Kriging (opcjonalnie)

**Scenariusze opadowe (przyszłość):**
- ❌ Nie zaimplementowane
- Dane PMAXTP pobiera aplikacja nadrzędna (np. Hydrograf via IMGWTools)
- Hydrolog otrzymuje gotowe wartości opadów

---

#### 2.1.3 Moduł `time` - Czasy charakterystyczne (v0.1.0)

**Czas koncentracji (tc):**
- Wzór Kirpicha: `tc = 0.0195 × L^0.77 × S^(-0.385)`
- Wzór SCS Lag: `tc = L^0.8 × (S + 1)^0.7 / (1900 × Y^0.5)`
- Wzór Giandotti (opcjonalnie)
- Wzór NRCS (opcjonalnie)

**Parametry wejściowe:**
- Długość głównego cieku [km lub m]
- Spadek cieku [% lub m/m]
- CN (dla metody SCS Lag)

---

#### 2.1.4 Moduł `morphometry` - Parametry fizjograficzne (v0.2.0)

**Parametry geometryczne:**
- Powierzchnia zlewni [km²]
- Obwód [km]
- Długość zlewni [km]
- Szerokość zlewni [km]

**Wskaźniki kształtu:**
- Wskaźnik formy Cf = A / L²
- Wskaźnik zwartości Cz = P / √A
- Wskaźnik kolistości Ck
- Wskaźnik wydłużenia Cw
- Wskaźnik lemniskaty Cl

**Parametry morfometryczne:**
- Wysokość: max, min, średnia [m n.p.m.]
- Deniwelacja [m]
- Spadek zlewni [%]
- Spadek głównego cieku [%]

**Krzywa hipsograficzna:**
- Rozkład wysokości
- Średnia wysokość ważona

---

#### 2.1.5 Moduł `network` - Sieć rzeczna (v0.3.0)

**Klasyfikacja:**
- Metoda Hortona
- Metoda Strahlera

**Wskaźniki:**
- Wskaźnik bifurkacji
- Gęstość sieci rzecznej
- Wskaźnik częstości cieków
- Współczynnik krętości

**Prawa Hortona:**
- Prawo liczby cieków
- Prawo długości cieków
- Prawo powierzchni zlewni

---

#### 2.1.6 Moduł `cli` - Interfejs CLI (v0.4.0) ✅

**Zaimplementowane komendy:**
```bash
# Czas koncentracji
hydrolog tc kirpich --length 2.5 --slope 0.02
hydrolog tc scs-lag --length 5.0 --slope 0.01 --cn 72
hydrolog tc giandotti --area 100 --length 15 --elevation 500

# Wyszukiwanie CN (tablice TR-55)
hydrolog cn lookup --hsg B --cover forest --condition good
hydrolog cn list
hydrolog cn range --cover pasture

# Obliczenia SCS-CN
hydrolog scs --cn 72 --precipitation 50
hydrolog scs --cn 72 --precipitation 50 --amc III

# Generowanie hydrogramów (SCS, Nash, Clark, Snyder)
hydrolog uh scs --area 45 --tc 90 --timestep 10
hydrolog uh nash --area 45 --n 3 --k 30 --timestep 10
hydrolog uh clark --area 45 --tc 60 --r 30 --timestep 10
hydrolog uh snyder --area 100 --L 15 --Lc 8 --timestep 30

# Eksport: --csv lub --json
```

---

### 2.2 ❌ OUT OF SCOPE - Poza zakresem

**Funkcjonalności:**
- ❌ Routing przepływu w kanałach
- ❌ Modelowanie zbiorników retencyjnych
- ❌ Symulacje powodziowe (mapy zalewowe)
- ❌ Modelowanie jakości wody
- ❌ Modelowanie erozji
- ❌ Modelowanie wód podziemnych
- ❌ Modelowanie topnienia śniegu
- ❌ Infiltracja szczegółowa (Green-Ampt)

**Pobieranie danych:**
- ❌ Pobieranie NMT (→ Kartograf)
- ❌ Pobieranie pokrycia terenu (→ Kartograf)
- ❌ Pobieranie danych glebowych/HSG (→ Kartograf)
- ❌ Pobieranie danych IMGW (→ IMGWTools)
- ❌ Operacje na bazach danych

**Wizualizacje:**
- ❌ Wykresy i mapy (→ aplikacja kliencka)
- ❌ Eksport PDF/raportów

---

### 2.3 ⏳ FUTURE SCOPE - Planowane na przyszłość

**Post v1.0:**
- Metoda racjonalna (Q = CIA) dla małych zlewni
- Kalibracja parametrów
- Analiza niepewności (Monte Carlo)

**Zaimplementowane (od v0.3+):**
- ✅ Nash Cascade (IUH) - `hydrolog.runoff.NashIUH`
- ✅ Clark Unit Hydrograph - `hydrolog.runoff.ClarkIUH`
- ✅ Snyder Unit Hydrograph - `hydrolog.runoff.SnyderUH`
- ✅ CN Lookup (TR-55) - `hydrolog.runoff.cn_lookup`

---

## 3. ARCHITEKTURA

### 3.1 Struktura modułów

```
hydrolog/
├── __init__.py              # Wersja, główne importy
├── runoff/                  # Moduł opad-odpływ
│   ├── __init__.py
│   ├── scs_cn.py           # SCS Curve Number calculations
│   ├── unit_hydrograph.py  # SCS Unit Hydrograph
│   ├── convolution.py      # Discrete convolution
│   ├── nash_iuh.py         # Nash Cascade IUH
│   ├── clark_iuh.py        # Clark IUH
│   ├── snyder_uh.py        # Snyder Synthetic UH
│   └── cn_lookup.py        # CN Lookup Tables (TR-55)
├── morphometry/             # Parametry fizjograficzne
│   ├── __init__.py
│   ├── geometric.py        # Area, perimeter, length
│   ├── terrain.py          # Elevation, slope
│   └── indicators.py       # Shape coefficients
├── precipitation/           # Opady
│   ├── __init__.py
│   ├── hietogram.py        # Temporal distributions
│   ├── interpolation.py    # IDW, Thiessen
│   └── scenarios.py        # PMAXTP integration
├── network/                 # Sieć rzeczna
│   ├── __init__.py
│   ├── classification.py   # Horton, Strahler
│   └── parameters.py       # Network indicators
├── time/                    # Czasy charakterystyczne
│   ├── __init__.py
│   └── concentration.py    # tc calculations
└── cli/                     # Interfejs CLI
    ├── __init__.py
    └── main.py             # Entry point
```

### 3.2 Zależności

**Wymagane:**
- Python >= 3.12
- NumPy >= 1.24

**Opcjonalne:**
- SciPy >= 1.10 (dla funkcji gamma w Nash IUH)
- Kartograf >= 0.3.0 (dla automatycznego wyznaczania CN z danych glebowych HSG)

### 3.3 API Design

**Styl:** Obiektowy z klasami

```python
# Przykład użycia
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram
from hydrolog.time import ConcentrationTime

# Czas koncentracji
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Hietogram
hietogram = BetaHietogram(
    total_mm=38.5,
    duration_min=60,
    timestep_min=5
)

# Hydrogram
generator = HydrographGenerator(
    area_km2=45.3,
    cn=72,
    tc_min=tc
)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Time to peak: {result.time_to_peak_min} min")
```

---

## 4. ROADMAP WERSJI

| Wersja | Zakres | Moduły | Status |
|--------|--------|--------|--------|
| **v0.1.0** | Hydrogram SCS-CN | `runoff`, `precipitation.hietogram`, `time` | ✅ Wydana |
| **v0.2.0** | Parametry morfometryczne | `morphometry` | ✅ Wydana |
| **v0.3.0** | Interpolacja + sieć | `precipitation.interpolation`, `network` | ✅ Wydana |
| **v0.4.0** | CLI + Clark + Snyder + CN Lookup | `cli`, `runoff.clark_iuh`, `runoff.snyder_uh`, `runoff.cn_lookup` | ✅ Wydana |
| **v1.0.0** | Stabilne API + dokumentacja | Wszystkie | 📋 Planowane |

---

## 5. OGRANICZENIA

### 5.1 Ograniczenia metodologiczne

- **SCS-CN:** Dla zlewni < 250 km² (ograniczenie metody USDA)
- **Opad równomierny:** Założenie dla małych zlewni
- **Warunki AMC-II:** Domyślne (przeciętne)
- **Brak routingu:** Hydrogram dla przekroju zamykającego

### 5.2 Ograniczenia techniczne

- **Pure Python + NumPy:** Brak zależności od GeoPandas/Shapely w core
- **Dane wejściowe:** NumPy arrays, listy, słowniki (nie GeoJSON/Shapefile)
- **Thread-safe:** Klasy są thread-safe (brak stanu globalnego)

---

## 6. ZALEŻNOŚCI ZEWNĘTRZNE

| Biblioteka | Cel | Wymagana |
|------------|-----|----------|
| NumPy | Obliczenia numeryczne | Tak |
| SciPy | Funkcje gamma (Nash IUH) | Nie (opcjonalna) |
| Kartograf | HSG, dane glebowe, pokrycie terenu | Nie (opcjonalna dla `runoff.cn_lookup`) |

**Hydrolog NIE zawiera funkcji pobierania danych:**
- Dane opadowe PMAXTP → pobiera aplikacja nadrzędna (np. Hydrograf via IMGWTools)
- Dane przestrzenne → Kartograf (opcjonalnie)

---

## 7. KRYTERIA SUKCESU

### 7.1 Jakościowe

- ✅ Pokrycie testami > 80%
- ✅ Type hints dla wszystkich publicznych funkcji
- ✅ Docstrings (NumPy style) dla wszystkich publicznych klas/metod
- ✅ Dokumentacja API (Sphinx/MkDocs)

### 7.2 Funkcjonalne

- ✅ Wyniki zgodne z obliczeniami ręcznymi (±1%)
- ✅ Walidacja względem przykładów z literatury (USDA TR-55)
- ✅ Obsługa edge cases (CN=100, tc=0, etc.)

### 7.3 Wydajnościowe

- ✅ Generowanie hydrogramu < 100ms dla typowych danych
- ✅ Brak wycieków pamięci dla dużych zbiorów danych

---

## 8. LICENCJA

**MIT License** - permisywna, zgodna z użyciem w projektach open-source i komercyjnych.

---

**Wersja dokumentu:** 1.1
**Data ostatniej aktualizacji:** 2026-01-19
**Status:** W trakcie realizacji
