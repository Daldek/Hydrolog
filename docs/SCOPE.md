# SCOPE.md - Zakres Projektu Hydrolog

## Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.5
**Data:** 2026-10-19
**Status:** v1.0.0 w przygotowaniu

---

## 1. Wprowadzenie

### 1.1 Cel Projektu

**Hydrolog** to biblioteka Python, interfejs CLI (`hydrolog`) i serwer MCP dostarczające narzędzia do obliczeń hydrologicznych. Zaprojektowana jako zewnętrzna zależność dla projektu Hydrograf oraz innych systemów wymagających funkcji hydrologicznych (m.in. Retman, agenci AI).

### 1.2 Główne cele

- Generowanie hydrogramów odpływu (SCS-CN)
- Obliczanie parametrów morfometrycznych zlewni
- Generowanie hietogramów (rozkład opadu w czasie)
- Interpolacja danych opadowych
- Klasyfikacja sieci rzecznej
- Wyznaczanie grup hydrologicznych gleb (HSG) z rastrów uziarnienia
- Statystyka przepływów i hydrometria
- Jeden katalog komend jako źródło prawdy dla biblioteki, CLI, serwera MCP i przewodników dla agentów

### 1.3 Analogia

Hydrolog jest analogiczny do **Kartografa** (pobieranie danych przestrzennych) i **IMGWTools** (pobieranie danych IMGW) - modularna biblioteka Python z czystym API, możliwa do użycia jako zależność w innych projektach. Od v1.0.0 podobnie jak one udostępnia jeden katalog komend (CLI + MCP + AGENTS.md/llms.txt), ale nie zależy od żadnej z tych bibliotek: Hydrolog niczego nie pobiera, pliki z danymi dostarczają narzędzia zewnętrzne.

---

## 2. ZAKRES FUNKCJONALNY

### 2.1 ✅ IN SCOPE - Funkcjonalności

#### 2.1.1 Moduł `runoff` - Opad-Odpływ (v0.1.0)

**Metoda SCS Curve Number:**
- Obliczanie retencji maksymalnej: `S = 25400/CN - 254`
- Obliczanie abstrakcji początkowej: `Ia = 0.2 × S`
- Obliczanie opadu efektywnego: `Pe = (P - Ia)² / (P - Ia + S)` gdy P > Ia, w przeciwnym razie Pe = 0
  - Forma uproszczona `(P - 0.2S)² / (P + 0.8S)` obowiązuje tylko przy Ia = 0.2S
- Warunki wilgotnościowe: AMC-I, AMC-II (domyślne), AMC-III

**Hydrogram jednostkowy SCS:**
- Czas do szczytu: `tp = 0.6 × tc`
- Przepływ szczytowy: `qp = 0.208 × A / tp` (A w km², tp w godzinach)
- Czas bazowy: `tb = 5.0 × tp` (pełny zakres bezwymiarowego UH; przybliżenie trójkątne to 2.67 × tp)
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

**Grupy hydrologiczne gleb (HSG) - moduł `soil` (v1.0.0):**
- Klasa uziarnienia USDA z zawartości iłu, piasku i pyłu (12 klas) oraz jej przypisanie do HSG A-D (reguły z Kartografa 0.8.0, ADR-025)
- Raster HSG (GeoTIFF `uint8`: 0 - brak danych, 1-4 to A-D) z rastrów iłu, piasku i pyłu (np. SoilGrids w g/kg) oraz powierzchnie grup w całej zlewni lub w prostokącie bbox (dodatek `hydrolog[raster]`)
- Tabele CN według USDA-NRCS dla kombinacji HSG + pokrycie terenu (`runoff.cn_lookup`) i CN ważone powierzchnią (`cn weighted`)
- Pobranie rastrów gleb pozostaje poza zakresem (Kartograf `download_soil`)

---

#### 2.1.2 Moduł `precipitation` - Opady (v0.1.0 / v0.3.0)

**Hietogramy (v0.1.0):**
- Rozkład Beta (α, β konfigurowalne, domyślnie α=2, β=5)
- Rozkład blokowy (stała intensywność)
- Rozkład trójkątny
- Rozkład DVWK Euler Type II (`EulerIIHietogram`)

**Interpolacja (v0.3.0):**
- IDW (Inverse Distance Weighting)
- Thiessen (Voronoi polygons)
- Metoda izohiet (`isohyet_method`)
- Średnia arytmetyczna (`arithmetic_mean`)
- Kriging (opcjonalnie — niezaimplementowany)

**Scenariusze opadowe (przyszłość):**
- ❌ Nie zaimplementowane
- Dane PMAXTP pobiera aplikacja nadrzędna (np. Hydrograf via IMGWTools)
- Hydrolog otrzymuje gotowe wartości opadów

---

#### 2.1.3 Moduł `time` - Czasy charakterystyczne (v0.1.0)

**Czas koncentracji (tc) — 6 metod:**
- Wzór Kirpicha: `tc = 0.0195 × L^0.77 × S^(-0.385)`
- Wzór NRCS: `tc = 0.01416 × L^0.8 × (S+25.4)^0.7 × Y^-0.5`
- Wzór Giandotti: `tc = (4√A + 1.5L) / (0.8 × √Hśr)`
- Wzór FAA: `tc = 22.213 × (1.1 - C) × L^0.5 / S^(1/3)`
- Wzór Kerby: `tc = 36.37 × (L × N)^0.467 × S^(-0.2335)`
- Metoda Kerby-Kirpich: `tc = t_overland(Kerby) + t_channel(Kirpich)`

**Parametry wejściowe:**
- Długość głównego cieku [km lub m]
- Spadek cieku [% lub m/m]
- CN (dla metody NRCS)

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

**WatershedParameters — dodatkowe pola opcjonalne (v0.6.3):**
- `runoff_coeff` — współczynnik odpływu dla metody FAA
- `retardance` — współczynnik szorstkości Kerby (0.02–0.80)
- `overland_length_km` — długość spływu powierzchniowego [km] (Kerby-Kirpich)
- `overland_slope_m_per_m` — spadek powierzchniowy [m/m] (Kerby-Kirpich)
- `Lc_km` — odległość do centroidu zlewni [km] (Nash/Snyder)
- `manning_n` — współczynnik Manninga (Nash)
- `urban_pct` — procent zabudowy [%] (Nash)
- `forest_pct` — procent zalesienia [%] (Nash)

---

#### 2.1.5 Moduł `network` - Sieć rzeczna (v0.3.0)

**Klasyfikacja:**
- Metoda Strahlera
- Metoda Shreve'a

**Wskaźniki:**
- Wskaźnik bifurkacji (`bifurcation_ratio`)
- Gęstość sieci rzecznej (`drainage_density`)
- Wskaźnik częstości cieków (`stream_frequency`)

**Statystyki sieci (`NetworkStatistics`):**
- Liczba cieków wg rzędu
- Średnia długość cieków wg rzędu
- Maksymalny rząd cieku

---

#### 2.1.6 Moduł `cli` - Interfejs CLI (v0.4.0, przebudowany w v1.0.0) ✅

Od v1.0.0 CLI jest generowane z katalogu komend (`hydrolog.catalog`): 37 komend w 13 grupach (lista: `hydrolog commands list`). Składnia: `hydrolog <grupa> <komenda> --opcja wartość`; flagi ogólne `--json`, `--schema`, `--lang pl|en`, `-V`. Dawna składnia CLI (v0.4.0-v0.7.0) została usunięta bez aliasów.

```bash
# Czas koncentracji
hydrolog tc kirpich --length-km 2.5 --slope-m-per-m 0.02
hydrolog tc nrcs --length-km 5.0 --slope-m-per-m 0.01 --cn 72
hydrolog tc giandotti --area-km2 100 --length-km 15 --elevation-diff-m 500
hydrolog tc faa --length-km 0.15 --slope-m-per-m 0.02 --runoff-coeff 0.6
hydrolog tc kerby --length-km 0.10 --slope-m-per-m 0.008 --retardance 0.40
hydrolog tc kerby-kirpich --overland-length-km 0.25 --overland-slope-m-per-m 0.008 \
    --retardance 0.40 --channel-length-km 5.0 --channel-slope-m-per-m 0.005

# Wyszukiwanie CN (tablice TR-55)
hydrolog cn lookup --hsg B --land-cover forest --condition good
hydrolog cn list
hydrolog cn range --land-cover pasture

# Obliczenia SCS-CN
hydrolog scs effective --cn 72 --precipitation-mm 50
hydrolog scs effective --cn 72 --precipitation-mm 50 --amc III

# Hydrogramy jednostkowe (SCS, Nash, Clark, Snyder)
hydrolog uh scs --area-km2 45 --tc-min 90 --timestep-min 10
hydrolog uh nash --area-km2 45 --n 3 --k-min 30 --timestep-min 10
hydrolog uh clark --area-km2 45 --tc-min 60 --r-min 30 --timestep-min 10
hydrolog uh snyder --area-km2 100 --length-km 15 --centroid-length-km 8 --timestep-min 30

# Wynik w formacie JSON (koperta hydrolog-result/1)
hydrolog uh scs --area-km2 45 --tc-min 90 --json
```

Pozostałe grupy: `precip`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `commands`.

---

#### 2.1.6a Warstwa operacji, katalog komend i interfejsy dla agentów (v1.0.0)

- **Katalog komend** (`hydrolog.catalog`) - jedno źródło prawdy: deklaracje `Command` i `Option` (opisy PL/EN, jednostki, zakresy, grupy `one_of`, przykłady), `data_commands()`, `command_schema()`, `validate_command()`, `run_command()`
- **Warstwa operacji** (`hydrolog.operations`) - po jednej publicznej, otypowanej funkcji na komendę; komponuje istniejące klasy, nie zawiera nowej hydrologii
- **Koperta wyniku** `hydrolog-result/1` i dokument błędu `hydrolog-error/1` z zamkniętym rejestrem `ERROR_CODES` (kody wyjścia CLI: 1, 2, 3, 4, 6, 7, 8, 9)
- **Serializacja** - wszystkie klasy wynikowe mają `to_dict()` i `to_json()` (`JsonResultMixin`)
- **Dane z plików** - szeregi, stacje, odcinki sieci i zlewnie jako CSV/JSON (w tym eksport szeregu IMGWTools `export_series` bez przetwarzania); `WatershedParameters` JSON to format `catchment_characteristics` w Retmanie
- **Serwer MCP** (`hydrolog mcp`, dodatek `hydrolog[mcp]`) - każda komenda katalogu jest narzędziem; dostęp do plików ograniczony do katalogów `--allow-dir`
- **Przewodniki dla agentów** - `AGENTS.md` i `llms.txt` generowane z katalogu (`hydrolog commands guide`), pilnowane testem zgodności bajt po bajcie
- Wykresy (`hydrolog.visualization`) pozostają tylko w Pythonie, poza katalogiem komend

---

#### 2.1.7 Moduł `reports` - Raporty obliczeniowe (v0.6.0)

**Generowanie raportów Markdown z formułami LaTeX:**
- `HydrologyReportGenerator` — główna klasa generująca raport
- `ReportConfig` — konfiguracja (metoda tc, model UH, opcje tabel/formuł)
- `FormulaRenderer` — renderowanie wzorów z podstawionymi wartościami
- `TableGenerator` — generowanie tabel Markdown (parametry, szeregi czasowe)

**Sekcje raportu:**
- Parametry zlewni (geometria, teren, wskaźniki kształtu)
- Czas koncentracji (wzory z podstawieniami)
- Hietogram (parametry, rozkład czasowy)
- Opad efektywny SCS-CN (S, Ia, Pe z wartościami)
- Hydrogram jednostkowy (SCS, Nash, Clark, Snyder — wzory specyficzne dla modelu)
- Splot dyskretny (procedura, wzory)
- Bilans wodny (tabela podsumowująca)

**Szablony (`templates.py`):**
- Polskie nagłówki i etykiety
- Opisy metod, warunków AMC
- Referencje literaturowe, glosariusz terminów

---

#### 2.1.8 Moduł `visualization` - Wykresy (v0.5.0)

Moduł wymaga opcjonalnych zależności: `pip install hydrolog[visualization]`

**Hietogramy:**
- `plot_hietogram()` — wykres intensywności opadu z opcjonalną linią kumulatywną
- `plot_hietogram_comparison()` — porównanie opadu całkowitego i efektywnego

**Hydrogramy:**
- `plot_hydrograph()` — hydrogram odpływu Q(t) z anotacją szczytu
- `plot_unit_hydrograph()` — hydrogram jednostkowy (dowolny model)

**Wykresy złożone:**
- `plot_rainfall_runoff()` — klasyczny wykres opad-odpływ

**Porównanie UH:**
- `plot_uh_comparison()` — porównanie wielu modeli UH na jednym wykresie

**Bilans wodny:**
- `plot_water_balance()` — wizualizacja bilansu SCS-CN (słupki lub kołowy)
- `plot_cn_curve()` — relacja P → Pe z wariantami AMC

**Morfometria:**
- `plot_hypsometric_curve()` — krzywa hipsograficzna z całką HI
- `plot_elevation_histogram()` — histogram rozkładu wysokości

**Sieć rzeczna:**
- `plot_stream_order_stats()` — statystyki sieci w 3 panelach
- `plot_bifurcation_ratios()` — wskaźniki bifurkacji wg rzędu

**Interpolacja:**
- `plot_stations_map()` — mapa stacji opadowych z wagami

---

#### 2.1.9 Moduł `statistics` — Statystyka hydrologiczna (v0.7.0)

- Wartości charakterystyczne przepływów (system polski: NNQ–WWQ)
- Analiza częstości przepływów maksymalnych (LogNormal, GEV, Pearson III, Weibull)
- Analiza częstości przepływów minimalnych (Fisher-Tippett)
- Detekcja sekwencji niżówkowych (metoda progowa)
- Test trendu Manna-Kendalla (weryfikacja stacjonarności)
- Testy zgodności: Kołmogorowa-Smirnowa, Andersona-Darlinga
- Kryterium informacyjne Akaike'a (AIC)

---

#### 2.1.10 Moduł `hydrometrics` — Hydrometria (v0.7.0)

- Krzywa natężenia przepływu Q = a × (H − H₀)^b
- Analiza częstości i czasu trwania stanów wody
- Metoda Rybczyńskiego (strefy wodowskazowe NTW/STW/WTW)

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
- ❌ Pobieranie rastrów gleb (→ Kartograf `download_soil`); samo obliczanie HSG z pobranych rastrów uziarnienia jest w zakresie (moduł `soil`, od v1.0.0)
- ❌ Pobieranie danych IMGW (→ IMGWTools); Hydrolog wczytuje gotowy plik CSV/JSON z eksportu
- ❌ REST API (interfejsy: biblioteka Python, CLI i serwer MCP)
- ❌ Operacje na bazach danych

**Wizualizacje i raporty:**
- ✅ Wykresy statyczne (matplotlib) — moduł `visualization` (od v0.5.0)
- ✅ Raporty Markdown/LaTeX — moduł `reports` (od v0.6.0)
- ❌ Eksport PDF (→ zewnętrzne narzędzia, np. Pandoc)
- ❌ Interaktywne mapy (→ aplikacja kliencka)

---

### 2.3 ⏳ FUTURE SCOPE - Planowane na przyszłość

**Post v1.0:**
- Empiryczne wzory na przepływ maksymalny (Punzet, Bogdanowicz-Stachy) - decyzja właściciela projektu z 2026-10-19: w zakresie, ale po v1.0.0
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
├── exceptions.py            # Wspólne wyjątki (InvalidParameterError)
├── runoff/                  # Moduł opad-odpływ
│   ├── __init__.py
│   ├── scs_cn.py           # SCS Curve Number calculations
│   ├── unit_hydrograph.py  # SCS Unit Hydrograph
│   ├── convolution.py      # Discrete convolution
│   ├── generator.py        # HydrographGenerator (opad→odpływ)
│   ├── nash_iuh.py         # Nash Cascade IUH
│   ├── clark_iuh.py        # Clark IUH
│   ├── snyder_uh.py        # Snyder Synthetic UH
│   └── cn_lookup.py        # CN Lookup Tables (TR-55)
├── morphometry/             # Parametry fizjograficzne
│   ├── __init__.py
│   ├── geometric.py        # Area, perimeter, length
│   ├── terrain.py          # Elevation, slope
│   ├── hypsometry.py       # Krzywa hipsograficzna
│   └── watershed_params.py # WatershedParameters (GIS integration)
├── precipitation/           # Opady
│   ├── __init__.py
│   ├── hietogram.py        # Temporal distributions
│   └── interpolation.py    # IDW, Thiessen, isohyet, arithmetic mean
├── network/                 # Sieć rzeczna
│   ├── __init__.py
│   └── stream_order.py     # Strahler, Shreve, wskaźniki sieci
├── time/                    # Czasy charakterystyczne
│   ├── __init__.py
│   └── concentration.py    # tc calculations (6 metod)
├── _serialization.py        # to_jsonable(), JsonResultMixin (to_dict/to_json) (v1.0.0)
├── agent_guide.py           # Generator AGENTS.md / llms.txt z katalogu (v1.0.0)
├── _data/agents/            # Szablony przewodników dla agentów (PL/EN)
├── catalog/                 # Katalog komend (v1.0.0)
│   ├── spec.py              # Command, Option
│   ├── envelope.py          # Koperta hydrolog-result/1, Notice
│   ├── inputs.py            # Szeregi, stacje, zlewnie z JSON lub plików CSV/JSON
│   ├── dispatch.py          # validate_command, run_command, polityka ścieżek
│   └── groups/              # Po jednym module na grupę komend (COMMANDS)
├── operations/              # Po jednej funkcji publicznej na komendę katalogu (v1.0.0)
├── mcp/                     # Serwer MCP (v1.0.0, dodatek [mcp])
├── soil/                    # HSG z uziarnienia gleby (v1.0.0)
│   ├── texture.py           # Trójkąt uziarnienia USDA, tekstura → HSG (tylko NumPy)
│   ├── hsg.py               # classify_hsg(), hsg_statistics_array()
│   └── raster.py            # Wejście/wyjście GeoTIFF (dodatek [raster])
├── cli/                     # Interfejs CLI generowany z katalogu (v1.0.0)
│   ├── main.py              # Punkt wejścia (hydrolog.cli.main:main)
│   ├── parser.py            # Parser argparse z deklaracji katalogu
│   ├── args.py, values.py   # Obsługa opcji i wartości z wiersza poleceń
│   ├── render.py, texts.py  # Podsumowanie tekstowe i komunikaty PL/EN
│   └── __main__.py          # python -m hydrolog.cli
├── reports/                 # Generowanie raportów (v0.6.0)
│   ├── __init__.py
│   ├── generator.py        # HydrologyReportGenerator
│   ├── formatters.py       # FormulaRenderer, TableGenerator
│   ├── templates.py        # Polskie szablony i nagłówki
│   └── sections/            # Sekcje raportu
│       ├── __init__.py
│       ├── watershed.py     # Parametry zlewni
│       ├── concentration.py # Czas koncentracji
│       ├── hietogram.py     # Hietogram
│       ├── scs_cn.py        # Opad efektywny SCS-CN
│       ├── unit_hydrograph.py # Hydrogram jednostkowy
│       ├── convolution.py   # Splot dyskretny
│       └── water_balance.py # Bilans wodny
├── statistics/              # Statystyka hydrologiczna (v0.7.0)
│   ├── __init__.py
│   ├── _types.py            # Wspólne typy danych
│   ├── _hydrological_year.py # Rok hydrologiczny
│   ├── characteristic.py   # Wartości charakterystyczne (NNQ–WWQ)
│   ├── high_flows.py       # Analiza częstości maksymalnych
│   ├── low_flows.py        # Fisher-Tippett, niżówki
│   └── stationarity.py     # Test Manna-Kendalla
├── hydrometrics/            # Hydrometria (v0.7.0)
│   ├── __init__.py
│   └── rating_curve.py     # Krzywa natężenia, strefy Rybczyńskiego
└── visualization/           # Wykresy (v0.5.0, wymaga matplotlib)
    ├── __init__.py
    ├── styles.py            # Style, kolory, etykiety PL
    ├── hietogram.py         # Wykresy hietogramów
    ├── hydrograph.py        # Wykresy hydrogramów
    ├── combined.py          # Wykresy opad-odpływ
    ├── unit_hydrograph.py   # Porównanie UH
    ├── water_balance.py     # Bilans wodny, krzywa CN
    ├── morphometry.py       # Krzywa hipsograficzna, histogram
    ├── network.py           # Statystyki sieci rzecznej
    ├── interpolation.py     # Mapa stacji opadowych
    └── statistics.py        # Statystyka hydrologiczna (v0.7.0)
```

### 3.2 Zależności

**Wymagane:**
- Python >= 3.12
- NumPy >= 1.24
- SciPy >= 1.10 (rozkłady statystyczne, funkcja gamma, optymalizacja — wymagane od v0.7.0)

**Opcjonalne (dodatki `pip install hydrolog[...]`):**
- `raster`: rasterio >= 1.3 + pyproj >= 3.6 (komendy `soil hsg` i `soil hsg-stats`, `hydrolog.soil.raster`)
- `mcp`: mcp >= 2.3, < 3 (serwer MCP `hydrolog mcp`)
- `visualization`: matplotlib >= 3.7 + seaborn >= 0.12 (moduł `visualization`)
- `all`: wszystkie powyższe

Hydrolog nie zależy od Kartografa ani IMGWTools; dawny dodatek `spatial` (Kartograf) został usunięty w v1.0.0.

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
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(
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
result = generator.generate(precip)

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
| **v0.5.0** | Wizualizacja + metoda Lutza | `visualization`, `runoff.nash_iuh.from_lutz` | ✅ Wydana |
| **v0.5.1** | Korekta SCS peak discharge | `runoff.unit_hydrograph`, `morphometry.watershed_params` | ✅ Wydana |
| **v0.5.2** | Czyszczenie zależności | `pyproject.toml` | ✅ Wydana |
| **v0.6.0** | Raporty obliczeniowe | `reports` | ✅ Wydana |
| **v0.6.1** | Nash urban regression | `runoff.nash_iuh.from_urban_regression` | ✅ Wydana |
| **v0.6.2** | Wzory UH w raportach + korekty metryczne | `reports`, `runoff.snyder_uh`, `runoff.clark_iuh` | ✅ Wydana |
| **v0.6.3** | FAA + Kerby + Kerby-Kirpich tc, API audit, WatershedParameters extension | `time.concentration`, `morphometry.watershed_params`, `reports` | ✅ Wydana |
| **v0.6.4** | WatershedParams extension + UH ordinates + docs audit | `morphometry.watershed_params`, `runoff.generator`, `reports`, `docs` | ✅ Wydana |
| **v0.7.0** | Statystyka hydrologiczna + Hydrometria | `statistics`, `hydrometrics`, `visualization.statistics` | ✅ Wydana |
| **v1.0.0** | Stabilne API, katalog komend, CLI z katalogu, serwer MCP, HSG, serializacja wyników, poprawki obliczeniowe | `catalog`, `operations`, `mcp`, `soil`, `cli`, `agent_guide` | 🔄 W przygotowaniu |

---

## 5. OGRANICZENIA

### 5.1 Ograniczenia metodologiczne

- **SCS-CN:** Dla zlewni < 250 km² (ograniczenie metody USDA)
- **Opad równomierny:** Założenie dla małych zlewni
- **Warunki AMC-II:** Domyślne (przeciętne)
- **Brak routingu:** Hydrogram dla przekroju zamykającego

### 5.2 Ograniczenia techniczne

- **Pure Python + NumPy:** Brak zależności od GeoPandas/Shapely w core
- **Dane wejściowe:** NumPy arrays, listy, słowniki; w CLI/MCP pliki CSV/JSON i rastry GeoTIFF (nie Shapefile)
- **Thread-safe:** Klasy są thread-safe (brak stanu globalnego)

---

## 6. ZALEŻNOŚCI ZEWNĘTRZNE

| Biblioteka | Cel | Wymagana |
|------------|-----|----------|
| NumPy | Obliczenia numeryczne | Tak |
| SciPy | Funkcje gamma (Nash IUH), rozkłady statystyczne (`statistics`) | Tak (od v0.7.0) |
| IMGWTools | Dane IMGW (szeregi pomiarowe) | Nie (Hydrolog wczytuje jego eksport CSV) |
| rasterio, pyproj | Rastry GeoTIFF dla HSG | Nie (dodatek `[raster]`) |
| mcp | Serwer MCP | Nie (dodatek `[mcp]`) |

**Hydrolog NIE zawiera funkcji pobierania danych:**
- Dane opadowe PMAXTP → pobiera aplikacja nadrzędna (np. Hydrograf via IMGWTools)
- Szeregi pomiarowe → IMGWTools (`series export` do CSV)
- Rastry (NMT, pokrycie terenu, gleby) → Kartograf; Hydrolog nie zależy od Kartografa

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

**Wersja dokumentu:** 1.5
**Data ostatniej aktualizacji:** 2026-10-19
**Status:** v1.0.0 w przygotowaniu
