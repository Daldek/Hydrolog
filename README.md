# Hydrolog

Biblioteka Python, interfejs CLI i serwer MCP do obliczeń hydrologicznych zlewni. Liczy lokalnie: bez sieci, bez kluczy i bez pobierania danych - szeregi pomiarowe dostarcza [IMGWTools](https://github.com/Daldek/IMGWTools), rastry (NMT, pokrycie terenu, gleby) [Kartograf](https://github.com/Daldek/Kartograf).

## Funkcjonalności

- **Hydrogramy odpływu** - SCS-CN, Nash IUH, Clark IUH, Snyder UH
- **Hietogramy** - rozkład Beta, blokowy, trójkątny, DVWK Euler Type II
- **Czas koncentracji** - wzory Kirpicha, NRCS, Giandotti, FAA, Kerby, Kerby-Kirpich
- **Parametry morfometryczne** - wskaźniki kształtu, teren, krzywa hipsograficzna
- **Klasyfikacja sieci rzecznej** - metody Strahlera i Shreve'a
- **Interpolacja opadów** - Thiessen, IDW, izohiety
- **CN Lookup** - tablice TR-55 (20 typów pokrycia terenu) i CN ważone powierzchnią
- **Grupy hydrologiczne gleb (HSG)** - z rastrów iłu, piasku i pyłu (np. SoilGrids)
- **Statystyka przepływów** - wartości charakterystyczne (NNQ-WWQ), częstość wezbrań i niżówek, test Manna-Kendalla
- **Hydrometria** - krzywa przepływu, strefy stanów wody (Rybczyński)
- **Wizualizacja** - hietogramy, hydrogramy, wykresy kombinowane, porównania UH
- **Raporty** - kompletne raporty obliczeniowe w Markdown z wzorami LaTeX
- **Katalog komend (37 komend)** - jedno źródło prawdy dla biblioteki, CLI, serwera MCP i przewodników dla agentów (`AGENTS.md`, `llms.txt`)
- **CLI** - `hydrolog <grupa> <komenda> --opcja wartość`, wynik w JSON (`--json`)
- **Serwer MCP** - `hydrolog mcp`: komendy jako narzędzia agentów AI (np. Claude Code)

## Instalacja

```bash
# Z GitHub
pip install git+https://github.com/Daldek/Hydrolog.git

# Z dodatkami opcjonalnymi
pip install "hydrolog[raster] @ git+https://github.com/Daldek/Hydrolog.git"
pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"

# Lokalna instalacja deweloperska
git clone https://github.com/Daldek/Hydrolog.git
cd Hydrolog
pip install -e ".[all,dev]"
```

| Dodatek | Zawartość | Do czego |
|---------|-----------|----------|
| *(brak)* | NumPy, SciPy | cała biblioteka, CLI, katalog komend |
| `[raster]` | rasterio, pyproj | rastry GeoTIFF: komendy `soil hsg`, `soil hsg-stats`, moduł `hydrolog.soil.raster` |
| `[mcp]` | mcp >= 2.3, < 3 | serwer MCP `hydrolog mcp` |
| `[visualization]` | matplotlib, seaborn | wykresy w Pythonie (`hydrolog.visualization`) |
| `[all]` | wszystkie powyższe | |

## Quick Start

### Generowanie hydrogramu

```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram
from hydrolog.time import ConcentrationTime

# 1. Oblicz czas koncentracji
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
print(f"Czas koncentracji: {tc:.1f} min")

# 2. Utwórz hietogram
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=38.5, duration_min=60.0, timestep_min=5.0)

# 3. Wygeneruj hydrogram
generator = HydrographGenerator(area_km2=45.3, cn=72, tc_min=tc)
result = generator.generate(precip)

# 4. Wyniki
print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Czas do szczytu: {result.time_to_peak_min:.0f} min")
print(f"Objętość odpływu: {result.total_volume_m3:.0f} m³")
print(f"Współczynnik odpływu: {result.runoff_coefficient:.3f}")
```

### Hietogramy

```python
from hydrolog.precipitation import (
    BetaHietogram, BlockHietogram, TriangularHietogram, EulerIIHietogram
)

# Hietogram Beta (realistyczny rozkład burzy)
beta = BetaHietogram(alpha=2.0, beta=5.0)
result = beta.generate(total_mm=38.5, duration_min=60.0, timestep_min=5.0)
print(f"Intensywności [mm]: {result.intensities_mm}")

# Hietogram blokowy (stała intensywność)
block = BlockHietogram()
result = block.generate(total_mm=38.5, duration_min=60.0, timestep_min=5.0)
print(f"Intensywność na krok: {result.intensities_mm[0]:.2f} mm")

# Hietogram trójkątny (szczyt w 40% czasu trwania)
tri = TriangularHietogram(peak_position=0.4)
result = tri.generate(total_mm=38.5, duration_min=60.0, timestep_min=5.0)

# Hietogram DVWK Euler Type II (metoda alternating block, szczyt w 1/3 czasu)
euler = EulerIIHietogram(peak_position=0.33)  # domyślnie 1/3
result = euler.generate(total_mm=38.5, duration_min=60.0, timestep_min=5.0)
print(f"Szczyt: {result.intensities_mm.max():.2f} mm w kroku {result.intensities_mm.argmax()+1}")
```

### Czas koncentracji

```python
from hydrolog.time import ConcentrationTime

# Wzór Kirpicha (L w km, S w m/m)
tc_kirpich = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Wzór NRCS (L w km, S w m/m, CN 1-100)
tc_nrcs = ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72)

# Wzór Giandotti (A w km², L w km, H w m)
tc_giandotti = ConcentrationTime.giandotti(
    area_km2=45.0, length_km=12.0, elevation_diff_m=350.0
)

print(f"Kirpich: {tc_kirpich:.1f} min")
print(f"NRCS: {tc_nrcs:.1f} min")
print(f"Giandotti: {tc_giandotti:.1f} min")
```

### Warunki wilgotnościowe (AMC)

```python
from hydrolog.runoff import HydrographGenerator, AMC
from hydrolog.precipitation import BlockHietogram

hietogram = BlockHietogram()
precip = hietogram.generate(total_mm=50.0, duration_min=60.0)

generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)

# Suche warunki (AMC-I) - mniejszy odpływ
result_dry = generator.generate(precip, amc=AMC.I)

# Normalne warunki (AMC-II) - domyślne
result_normal = generator.generate(precip, amc=AMC.II)

# Mokre warunki (AMC-III) - większy odpływ
result_wet = generator.generate(precip, amc=AMC.III)
```

### HydrographGenerator z różnymi modelami UH

```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Hietogram
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

# Model SCS (domyślny)
gen_scs = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
result_scs = gen_scs.generate(precip)

# Model Nasha
gen_nash = HydrographGenerator(
    area_km2=45.0, cn=72,
    uh_model="nash",
    uh_params={"n": 3.0, "k": 0.5}  # k w godzinach (domyślnie)
)
result_nash = gen_nash.generate(precip)

# Model Clarka
gen_clark = HydrographGenerator(
    area_km2=45.0, cn=72, tc_min=60.0,
    uh_model="clark",
    uh_params={"r": 30.0}  # współczynnik retencji [min]
)
result_clark = gen_clark.generate(precip)

# Model Snydera
gen_snyder = HydrographGenerator(
    area_km2=100.0, cn=72,
    uh_model="snyder",
    uh_params={"L_km": 15.0, "Lc_km": 8.0}  # długość cieku i do centroidu
)
result_snyder = gen_snyder.generate(precip)

print(f"SCS: Qmax = {result_scs.peak_discharge_m3s:.2f} m³/s")
print(f"Nash: Qmax = {result_nash.peak_discharge_m3s:.2f} m³/s")
print(f"Clark: Qmax = {result_clark.peak_discharge_m3s:.2f} m³/s")
print(f"Snyder: Qmax = {result_snyder.peak_discharge_m3s:.2f} m³/s")
```

### Model Nasha (Nash IUH)

Model Nasha reprezentuje zlewnię jako **kaskadę n identycznych zbiorników liniowych**, każdy ze stałą retencji K:

```
Opad → [Zbiornik 1] → [Zbiornik 2] → ... → [Zbiornik n] → Odpływ
           K              K                    K
```

**Wzór IUH:**
```
u(t) = 1/(K×Γ(n)) × (t/K)^(n-1) × e^(-t/K)    [1/min]
```

**Właściwości:**
| Wielkość | Wzór |
|----------|------|
| Czas opóźnienia | tlag = n × K |
| Czas do szczytu | tp = (n-1) × K |
| Wariancja | σ² = n × K² |

```python
from hydrolog.runoff import NashIUH
from hydrolog.time import ConcentrationTime

# Metoda 1: Bezpośrednie podanie parametrów (IUH, wartości bezwymiarowe [1/min])
iuh = NashIUH(n=3.0, k_min=30.0)
result_iuh = iuh.generate(timestep_min=5.0)  # IUHResult
print(f"Czas do szczytu IUH: {iuh.time_to_peak_min:.1f} min")
print(f"Czas opóźnienia: {iuh.lag_time_min:.1f} min")

# Metoda 2: Z powierzchnią zlewni (UH, wartości wymiarowe [m³/s/mm])
nash = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)
result_uh = nash.generate(timestep_min=5.0)  # NashUHResult
print(f"Qmax UH: {result_uh.peak_discharge_m3s:.2f} m³/s na mm")

# Metoda 3: Estymacja metodą Lutza (ZALECANA dla zlewni bez danych pomiarowych)
nash_lutz = NashIUH.from_lutz(
    L_km=8.2, Lc_km=4.5, slope=0.023, manning_n=0.035,
    forest_pct=30.0, urban_pct=5.0, area_km2=45.0
)
print(f"Lutz: n={nash_lutz.n:.2f}, K={nash_lutz.k_min:.1f} min")

# Jawne generowanie IUH (zawsze zwraca IUHResult)
result = iuh.generate_iuh(timestep_min=5.0, duration_min=300.0)

# Konwersja IUH do D-minutowego hydrogramu jednostkowego
uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)
print(f"Qmax UH: {uh.peak_discharge_m3s:.2f} m³/s")
```

### Metoda Lutza (estymacja parametrów Nasha)

Metoda Lutza służy do estymacji parametrów modelu Nasha (n, K) z charakterystyk
fizjograficznych zlewni. **Zalecana dla zlewni niezurbanizowanych** bez danych pomiarowych.

**Algorytm:**
```
1. P₁ = 3.989×n + 0.028                    (n = współczynnik Manninga)
2. tp = P₁ × (L×Lc/Jg^1.5)^0.26 × e^(-0.016U) × e^(0.004W)   [h]
3. up = 0.66 / tp^1.04                     [1/h]
4. f(N) = tp × up  →  N (z tabeli lub numerycznie)
5. K = tp / (N-1)                          [h]
```

**Wpływ parametrów:**
| Czynnik | Wpływ na odpływ |
|---------|-----------------|
| ↑ Las (W) | Wolniejszy (↑ tp) |
| ↑ Urbanizacja (U) | Szybszy (↓ tp) |
| ↑ Spadek (Jg) | Szybszy (↓ tp) |
| ↑ Manning (n) | Wolniejszy (↑ tp) |

```python
from hydrolog.runoff import NashIUH

# Estymacja parametrów metodą Lutza
nash = NashIUH.from_lutz(
    L_km=15.0,          # Długość cieku głównego [km]
    Lc_km=8.0,          # Długość do centroidu zlewni [km]
    slope=0.02,         # Spadek cieku [-]
    manning_n=0.035,    # Współczynnik Manninga [-]
    forest_pct=40.0,    # Udział lasów [%]
    urban_pct=5.0,      # Udział urbanizacji [%]
    area_km2=50.0       # Powierzchnia zlewni [km²]
)

print(f"n = {nash.n:.2f}")           # n = 3.66
print(f"K = {nash.k_min:.1f} min")   # K = 70.9 min
print(f"tlag = {nash.lag_time_min:.1f} min")  # tlag = 259.3 min

# Generowanie hydrogramu jednostkowego
uh = nash.generate(timestep_min=10.0)
print(f"Qmax = {uh.peak_discharge_m3s:.2f} m³/s/mm")
```

**Referencje (Lutz):**
- Lutz W. (1984). *Berechnung von Hochwasserabflüssen unter Anwendung von Gebietskenngrößen*.
  Mitteilungen des Instituts für Hydrologie und Wasserwirtschaft, H. 24, Universität Karlsruhe.
- KZGW (2017). *Aktualizacja metodyki obliczania przepływów i opadów maksymalnych*.
  Załącznik 2, Tabela C.2.

#### Estymacja parametrów Nasha — regresja dla zlewni zurbanizowanych

```python
from hydrolog.runoff import NashIUH

# Estymacja parametrów dla zlewni zurbanizowanej
nash = NashIUH.from_urban_regression(
    area_km2=1.3,              # Powierzchnia zlewni [km²]
    effective_precip_mm=1.31,  # Opad efektywny [mm]
    duration_h=0.17,           # Czas trwania opadu [h]
    urban_fraction=0.05,       # Wskaźnik urbanizacji [-]
)

print(f"N = {nash.n:.3f}")           # N = 1.625
print(f"k = {nash.k_min:.1f} min")   # k = 23.7 min
print(f"tL = {nash.lag_time_min:.1f} min")  # tL = 38.6 min

# Generowanie hydrogramu jednostkowego
uh = nash.generate(timestep_min=6.0)
print(f"Qmax = {uh.peak_discharge_m3s:.4f} m³/s/mm")
```

**Referencje (regresja dla zlewni zurbanizowanych):**
- Rao, R.A.; Delleur, J.W.; Sarma, B.S.P. (1972). *Conceptual Hydrologic Models for
  Urbanizing Basins*. Journal of the Hydraulics Division, ASCE, 98(HY7), 1205-1220.
- Sarma, P.B.S.; Delleur, J.W.; Rao, A.R. (1969). *A Program in Urban Hydrology, Part II*.
  Purdue University WRRC, Technical Report No. 9.

### Clark IUH

```python
from hydrolog.runoff import ClarkIUH

# Metoda 1: IUH bez powierzchni (zwraca wartości bezwymiarowe [1/min])
iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
result_iuh = iuh.generate(timestep_min=5.0)  # ClarkIUHResult
print(f"Czas opóźnienia: {iuh.lag_time_min:.1f} min")

# Metoda 2: UH z powierzchnią (zwraca wartości wymiarowe [m³/s/mm])
clark = ClarkIUH(tc_min=60.0, r_min=30.0, area_km2=45.0)
result_uh = clark.generate(timestep_min=5.0)  # ClarkUHResult
print(f"Qmax UH: {result_uh.peak_discharge_m3s:.2f} m³/s na mm")

# Metoda 3: Z proporcji R/Tc
iuh = ClarkIUH.from_tc_r_ratio(tc_min=90.0, r_tc_ratio=0.5)

# Jawne generowanie IUH (zawsze zwraca ClarkIUHResult)
result = iuh.generate_iuh(timestep_min=5.0)

# Konwersja IUH do D-minutowego hydrogramu jednostkowego
uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0, timestep_min=5.0)
print(f"Qmax UH: {uh.peak_discharge_m3s:.2f} m³/s")
```

### Model Snydera (Snyder UH)

Model Snydera (1938) to **empiryczna metoda syntetycznego hydrogramu jednostkowego** oparta na charakterystykach fizjograficznych zlewni. Jeden z najstarszych i najczęściej stosowanych modeli w hydrologii inżynierskiej.

#### Teoria i wzory

**Parametry wejściowe:**
| Symbol | Opis | Jednostka |
|--------|------|-----------|
| A | Powierzchnia zlewni | km² |
| L | Długość cieku głównego (od ujścia do działu wód) | km |
| Lc | Długość wzdłuż cieku od ujścia do środka ciężkości zlewni | km |
| Ct | Współczynnik czasowy (zależy od charakteru zlewni) | - |
| Cp | Współczynnik szczytowy (zależy od retencji) | - |

**Krok 1: Czas opóźnienia (lag time)**
```
tL = Ct × (L × Lc)^0.3    [h]
```

**Krok 2: Standardowy czas trwania opadu**
```
tD = tL / 5.5    [h]
```

**Krok 3: Parametry dla standardowego czasu trwania (Δt = tD)**
```
tp = tL + tD/2           [h]  ← czas do szczytu
qp = 0.275 × Cp × A / tL [m³/s/mm]  ← przepływ szczytowy
```

**Krok 4: Korekta dla niestandardowego czasu trwania (Δt ≠ tD)**

Jeżeli rzeczywisty czas trwania opadu Δt różni się od standardowego tD:
```
tLR = tL + 0.25 × (Δt - tD)    [h]  ← skorygowany czas opóźnienia
tpR = tLR + Δt/2               [h]  ← skorygowany czas do szczytu
qpR = qp × (tL / tLR)          [m³/s/mm]  ← skorygowany przepływ szczytowy
```

**Krok 5: Czas podstawy hydrogramu (z bilansu wodnego)**
```
tb = 0.556 × A / qpR    [h]
```

*Wyprowadzenie:* Dla trójkątnego hydrogramu jednostkowego objętość V = 0.5 × qp × tb × 3600 s/h.
Dla 1 mm opadu na A km²: V = A × 10⁶ m² × 0.001 m = A × 1000 m³.
Stąd: tb = 2 × A × 1000 / (qp × 3600) = 0.556 × A / qp.

**Szerokości hydrogramu:**
```
W50 = 5.87 / (qp/A)^1.08    [h]  ← szerokość przy 50% szczytu
W75 = 3.35 / (qp/A)^1.08    [h]  ← szerokość przy 75% szczytu
```

#### Współczynniki Ct i Cp

| Typ zlewni | Ct (SI) | Cp | Opis |
|------------|---------|-----|------|
| Górska, stroma | 1.35-1.45 | 0.60-0.80 | Szybki odpływ, mała retencja |
| Pagórkowata | 1.45-1.55 | 0.50-0.65 | Typowe warunki |
| Nizinna, płaska | 1.55-1.65 | 0.40-0.55 | Wolny odpływ, duża retencja |

**Zakresy typowe:** Ct = 1.35-1.65, Cp = 0.4-0.8

**Zależności:**
- Ct i Cp są **odwrotnie skorelowane** (większy Ct → mniejszy Cp)
- **Urbanizacja**: ↓ Ct, ↑ Cp (szybszy odpływ, wyższy szczyt)
- **Zalesienie**: ↑ Ct, ↓ Cp (wolniejszy odpływ, niższy szczyt)

#### Przykład obliczeniowy

**Dane zlewni:**
- A = 45.3 km²
- L = 14.9 km
- Lc = 7.0 km
- Ct = 1.65, Cp = 0.565
- Δt = 60 min (rzeczywisty czas trwania opadu)

**Obliczenia:**

```
Krok 1: Czas opóźnienia
  tL = 1.65 × (14.9 × 7.0)^0.3 = 1.65 × 104.3^0.3 = 1.65 × 4.03 = 6.65 h

Krok 2: Standardowy czas trwania opadu
  tD = 6.65 / 5.5 = 1.21 h = 72.6 min

Krok 3: Parametry dla standardowego czasu (Δt = tD = 72.6 min)
  tp = 6.65 + 1.21/2 = 6.65 + 0.605 = 7.26 h
  qp = 0.275 × 0.565 × 45.3 / 6.65 = 1.058 m³/s/mm

Krok 4: Korekta dla Δt = 60 min (niestandardowy)
  tLR = 6.65 + 0.25 × (1.00 - 1.21) = 6.65 - 0.05 = 6.60 h
  tpR = 6.60 + 1.00/2 = 6.60 + 0.50 = 7.10 h = 426 min
  qpR = 1.058 × (6.65 / 6.60) = 1.058 × 1.008 = 1.066 m³/s/mm

Krok 5: Czas podstawy
  tb = 0.556 × 45.3 / 1.066 = 23.62 h = 1417 min
```

**Wyniki:**
| Parametr | Wartość | Jednostka |
|----------|---------|-----------|
| tL | 399.1 | min |
| tD | 72.6 | min |
| tpR | 426.0 | min |
| qpR | 1.066 | m³/s/mm |
| tb | 1417 | min |

#### Użycie w kodzie

```python
from hydrolog.runoff import SnyderUH

# Metoda 1: Bezpośrednie podanie parametrów
snyder = SnyderUH(
    area_km2=45.3,
    L_km=14.9,
    Lc_km=7.0,
    ct=1.65,
    cp=0.565
)

# Podstawowe parametry (właściwości)
print(f"tL = {snyder.lag_time_min:.1f} min")          # 399.1 min
print(f"tD = {snyder.standard_duration_min:.1f} min") # 72.6 min

# Parametry dla konkretnego czasu trwania opadu (metody)
delta_t = 60  # min
print(f"tpR = {snyder.time_to_peak_min(delta_t):.1f} min")  # 426.0 min
print(f"qpR = {snyder.peak_discharge(delta_t):.3f} m³/s/mm") # 1.066 m³/s/mm
print(f"tb = {snyder.time_base_min(delta_t):.1f} min")       # 1417.0 min

# Generowanie hydrogramu jednostkowego
result = snyder.generate(timestep_min=10.0, duration_min=60.0)
print(f"Qmax = {result.peak_discharge_m3s:.3f} m³/s/mm")
```

**Referencje:**
- Snyder, F.F. (1938). *Synthetic unit-graphs*. Transactions of the AGU, 19, 447-454.
- Bedient, P.B. & Huber, W.C. (1992). *Hydrology and Floodplain Analysis*. Addison-Wesley.

### CN Lookup (tablice TR-55)

```python
from hydrolog.runoff import get_cn, lookup_cn, LandCover, HydrologicCondition

# Proste wyszukanie CN
cn = get_cn("B", "forest", "good")
print(f"CN dla lasu (HSG B, good): {cn}")  # 55

# Szczegółowe wyszukanie
result = lookup_cn("C", LandCover.PASTURE, HydrologicCondition.FAIR)
print(f"CN: {result.cn}, Opis: {result.description}")

# Lista dostępnych pokryć terenu
from hydrolog.runoff import list_land_covers
covers = list_land_covers()
```

### Grupy hydrologiczne gleb (HSG)

HSG (A-D) liczy się z zawartości iłu, piasku i pyłu (tylko NumPy) albo z rastrów GeoTIFF (dodatek `hydrolog[raster]`). Reguły (trójkąt uziarnienia USDA → HSG) przeniesiono z Kartografa 0.8.0; Hydrolog nie pobiera rastrów - ił, piasek i pył z SoilGrids (g/kg) pobiera Kartograf (`download_soil`).

```python
from hydrolog.runoff import calculate_weighted_cn, get_cn
from hydrolog.soil import classify_usda_texture, hsg_from_rasters, hsg_statistics, texture_to_hsg

# Pojedyncza próbka (jednostka dowolna, byle wspólna dla trzech frakcji)
texture = classify_usda_texture(clay=20, sand=40, silt=40)  # "loam"
print(texture_to_hsg(texture))                              # "B"

# Rastry iłu, piasku i pyłu (ten sam układ współrzędnych, siatka i rozmiar) -> raster HSG
# GeoTIFF uint8: 0 - brak danych, 1-4 to grupy A-D
hsg_from_rasters("clay.tif", "sand.tif", "silt.tif", output_path="hsg.tif")

# Powierzchnie grup A-D (opcjonalnie tylko prostokąt: bbox=..., bbox_crs="EPSG:2180")
stats = hsg_statistics("hsg.tif")
for group, s in stats.groups.items():
    print(f"HSG {group}: {s.area_ha:.1f} ha ({s.percent:.1f}%)")

# CN ważone powierzchnią grup (jedno pokrycie terenu, np. łąka w dobrym stanie)
parts = [(get_cn(g, "meadow", "good"), s.area_ha) for g, s in stats.groups.items() if s.area_ha > 0]
print(f"CN zlewni: {calculate_weighted_cn(parts):.1f}")
```

Mapowanie tekstura → HSG jest łagodniejsze niż tablica TR-55 dla `sandy_loam` (B), `clay_loam` i `silty_clay_loam` (C); szczegóły i wzory: [Ścieżki obliczeniowe](docs/COMPUTATION_PATHS.md). HSG nie jest liczbą CN - CN wymaga też pokrycia terenu (przecięcie rastrów HSG i pokrycia robi się poza Hydrologiem).

### Serializacja wyników

Każda klasa wynikowa ma `to_dict()` i `to_json()` (`NaN` i nieskończoności to `null`, tablice NumPy listy):

```python
from hydrolog.runoff import SCSCN

result = SCSCN(cn=72).effective_precipitation(50.0)
print(result.to_json())
```

### Parametry morfometryczne

```python
from hydrolog.morphometry import WatershedGeometry, TerrainAnalysis, HypsometricCurve
import numpy as np

# Wskaźniki kształtu zlewni
geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
indicators = geom.get_shape_indicators()
print(f"Wskaźnik formy: {indicators.form_factor:.3f}")
print(f"Wskaźnik zwartości: {indicators.compactness_coefficient:.3f}")

# Parametry terenu
terrain = TerrainAnalysis(
    elevation_min_m=150.0,
    elevation_max_m=520.0,
    length_km=12.0,
    elevation_mean_m=340.0
)
elev = terrain.get_elevation_parameters()
print(f"Deniwelacja: {elev.relief_m} m")

# Krzywa hipsograficzna (z danych DEM)
elevations = np.random.uniform(150, 520, 10000)  # Symulacja DEM
hypso = HypsometricCurve(elevations)
result = hypso.analyze()
print(f"Całka hipsograficzna: {result.hypsometric_integral:.3f}")
```

### Klasyfikacja sieci rzecznej

```python
from hydrolog.network import StreamNetwork, StreamSegment, OrderingMethod

# Definiuj sieć rzeczną
segments = [
    StreamSegment(1, [], length_km=1.0),   # Źródłowy
    StreamSegment(2, [], length_km=0.8),   # Źródłowy
    StreamSegment(3, [1, 2], length_km=2.0),  # Połączenie
]

# Klasyfikuj metodą Strahlera
network = StreamNetwork(segments, area_km2=10.0)
network.classify(OrderingMethod.STRAHLER)

# Statystyki sieci
stats = network.get_statistics()
print(f"Rząd maksymalny: {stats.max_order}")
print(f"Gęstość drenażu: {stats.drainage_density:.2f} km/km²")
```

### Interpolacja opadów

```python
from hydrolog.precipitation import Station, thiessen_polygons, inverse_distance_weighting

# Stacje pomiarowe
stations = [
    Station("S1", x=0, y=0, precipitation_mm=25.0),
    Station("S2", x=10, y=0, precipitation_mm=35.0),
    Station("S3", x=5, y=8, precipitation_mm=30.0),
]

# Metoda Thiessena
areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}  # km²
result = thiessen_polygons(stations, areas)
print(f"Opad średni (Thiessen): {result.areal_precipitation_mm:.1f} mm")

# Metoda IDW
result = inverse_distance_weighting(stations, target_x=5, target_y=4, power=2)
print(f"Opad w punkcie (IDW): {result.areal_precipitation_mm:.1f} mm")
```

### Wizualizacja

```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram
from hydrolog.visualization import (
    setup_hydrolog_style,
    plot_rainfall_runoff,
    plot_hietogram,
    plot_hydrograph,
    plot_uh_comparison,
)

# Ustaw styl wykresów
setup_hydrolog_style()

# Generuj dane
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=120.0, timestep_min=10.0)

generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
result = generator.generate(precip)

# Wykres hietogramu z sumą kumulatywną
fig = plot_hietogram(precip, show_cumulative=True)
fig.savefig("hietogram.png", dpi=150)

# Wykres hydrogramu
fig = plot_hydrograph(result.hydrograph, show_peak=True)
fig.savefig("hydrograph.png", dpi=150)

# Wykres kombinowany (hietogram + hydrogram)
fig = plot_rainfall_runoff(
    hietogram=precip,
    hydrograph=result.hydrograph,
    effective_precip=result.effective_precip_mm,
    title="Zlewnia - epizod opadowy"
)
fig.savefig("rainfall_runoff.png", dpi=150)
```

#### Porównanie modeli UH

```python
from hydrolog.runoff import SCSUnitHydrograph, NashIUH, ClarkIUH, SnyderUH
from hydrolog.visualization import plot_uh_comparison

# Generuj hydrogramy jednostkowe różnych modeli
scs = SCSUnitHydrograph(area_km2=45, tc_min=90).generate(timestep_min=10)
nash = NashIUH(n=3, k_min=30, area_km2=45).generate(timestep_min=10)
clark = ClarkIUH(tc_min=60, r_min=30, area_km2=45).generate(timestep_min=10)
snyder = SnyderUH(area_km2=45, L_km=15, Lc_km=8).generate(timestep_min=10)

# Porównaj na jednym wykresie z tabelą
models = {
    "SCS": scs,
    "Nash (n=3, K=30)": nash,
    "Clark (Tc=60, R=30)": clark,
    "Snyder (Ct=1.5)": snyder,
}
fig = plot_uh_comparison(models, show_table=True)
fig.savefig("uh_comparison.png", dpi=150)
```

#### Krzywa hipsograficzna

```python
import numpy as np
from hydrolog.morphometry import HypsometricCurve
from hydrolog.visualization import plot_hypsometric_curve

# Analiza DEM
elevations = np.random.uniform(200, 800, 10000)  # Symulacja
hypso = HypsometricCurve(elevations)
result = hypso.analyze()

# Wykres z integralem i krzywymi referencyjnymi
fig = plot_hypsometric_curve(result, show_integral=True, show_reference=True)
fig.savefig("hypsometry.png", dpi=150)
```

#### Instalacja zależności wizualizacji

```bash
pip install hydrolog[visualization]
```

### Generowanie raportów

Moduł `hydrolog.reports` generuje kompletne raporty obliczeniowe w formacie Markdown z wzorami LaTeX i pełną procedurą obliczeniową.

```python
from hydrolog.reports import HydrologyReportGenerator, ReportConfig
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

# Generuj dane
hietogram = BetaHietogram(alpha=2.0, beta=5.0)
precip = hietogram.generate(total_mm=50.0, duration_min=120.0, timestep_min=10.0)

generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
result = generator.generate(precip)

# Konfiguracja raportu
config = ReportConfig(
    tc_method="kirpich",      # kirpich, nrcs, giandotti
    uh_model="scs",           # scs, nash, clark, snyder
    include_formulas=True,    # Wzory LaTeX
    include_tables=True,      # Tabele z wynikami
    max_table_rows=50         # Automatyczne skracanie
)

# Wygeneruj raport
report_gen = HydrologyReportGenerator(config)
report = report_gen.generate(
    result=result,
    hietogram=precip,
    watershed_name="Zlewnia Testowa",
    tc_min=90.0
)

# Zapisz do pliku
with open("raport.md", "w") as f:
    f.write(report)
```

**Przykładowy fragment raportu:**

```markdown
## 4. Opad Efektywny (SCS-CN)

### 4.1 Parametry metody
- Curve Number: **CN = 72**
- Warunki wilgotnościowe: **AMC-II**

### 4.2 Retencja maksymalna

$$S = \frac{25400}{CN} - 254 = \frac{25400}{72} - 254 = 98.78 \text{ mm}$$

### 4.3 Abstrakcja początkowa

$$I_a = 0.2 \cdot S = 0.2 \cdot 98.78 = 19.76 \text{ mm}$$
```

**Struktura raportu:**
1. Parametry zlewni (geometria, teren, wskaźniki kształtu)
2. Czas koncentracji (wzór z podstawieniami)
3. Hietogram (parametry, rozkład czasowy)
4. Opad efektywny SCS-CN (S, Ia, Pe z wzorami)
5. Hydrogram jednostkowy (parametry modelu, ordinaty)
6. Splot dyskretny (procedura konwolucji)
7. Wyniki (Qmax, tp, V, szereg czasowy)
8. Bilans wodny (tabela z procentami)

### Katalog komend, CLI, serwer MCP i przewodniki dla agentów

Wszystkie interfejsy powstają z jednego katalogu komend (`hydrolog.catalog`): 37 komend w grupach `tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report` i `commands`. Ta sama komenda działa w trzech miejscach (przykład `tc kirpich`):

- Python: `hydrolog.operations.tc_kirpich(length_km=8.2, slope_m_per_m=0.023)` albo `hydrolog.catalog.run_command("tc kirpich", {...})`
- CLI: `hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023`
- MCP: narzędzie `tc_kirpich` z argumentami `{"length_km": 8.2, "slope_m_per_m": 0.023}`

#### CLI

```bash
hydrolog --help                 # grupy komend
hydrolog commands list          # wszystkie komendy z opisami
hydrolog tc kirpich --help      # opcje komendy, jednostki, przykłady
hydrolog tc kirpich --schema    # schemat opcji (JSON Schema), bez uruchamiania

# Czas koncentracji
hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023
hydrolog tc nrcs --length-km 8.2 --slope-m-per-m 0.023 --cn 72
hydrolog tc giandotti --area-km2 145 --length-km 21.5 --elevation-diff-m 320

# Wyszukiwanie CN i opad efektywny
hydrolog cn lookup --hsg B --land-cover forest --condition good
hydrolog cn range --land-cover pasture
hydrolog scs effective --cn 72 --precipitation-mm 50 --amc III

# Hydrogramy jednostkowe i hydrogram odpływu
hydrolog uh scs --area-km2 45 --tc-min 90 --timestep-min 10
hydrolog uh nash --area-km2 45 --n 3 --k-min 30 --timestep-min 10
hydrolog uh snyder --area-km2 100 --length-km 15 --centroid-length-km 8 --timestep-min 30
hydrolog hydrograph generate --area-km2 45.3 --cn 72 --tc-min 90 \
    --hietogram-type beta --total-mm 50 --duration-min 60

# Zlewnia z pliku JSON (format WatershedParameters.to_json())
hydrolog hydrograph generate --watershed-file zlewnia.json --tc-method kirpich \
    --hietogram-type beta --total-mm 50 --duration-min 60

# Dane z plików (CSV/JSON), wynik jako JSON dla skryptów
hydrolog stats flood-frequency --input-file maxima.csv --value-column Qmax --json > wynik.json

# HSG z rastrów iłu, piasku i pyłu (dodatek [raster]) i powierzchnie grup
hydrolog soil hsg --clay-path clay.tif --sand-path sand.tif --silt-path silt.tif --output-path hsg.tif
hydrolog soil hsg-stats --hsg-path hsg.tif
hydrolog cn weighted --parts '[{"cn": 30, "area": 75.0}, {"cn": 58, "area": 75.0}, {"cn": 71, "area": 75.0}, {"cn": 78, "area": 68.75}]'
```

- Opcje to nazwy opcji katalogu w `--kebab-case`; listy liczb podaje się po przecinku
  (`--values 1,2,3`), obiekty jako tekst JSON (`--watershed '{"area_km2": 45.3, ...}'`),
  opcje logiczne jako `--flaga` / `--no-flaga`. Liczba ujemna: `--opcja -5`.
- Długie serie i listy podawaj plikiem CSV/JSON (`--input-file`, `--watershed-file`, `--stations-file`, `--segments-file`); eksport szeregu IMGWTools (`series export` do CSV) wczytuje się bez przetwarzania, a kolumnę można wskazać nazwą bez jednostki (`Q` znajduje `Q [m3/s]`).
- `--json` drukuje kopertę wyniku `hydrolog-result/1` (jedna linia: `schema`, `command`, `hydrolog_version`, `status`, `inputs`, `result`, `files`, `notices`), `--schema` - schemat
  opcji komendy (JSON Schema) bez uruchamiania, `--lang pl|en` wybiera język pomocy i
  komunikatów (domyślnie zmienna `HYDROLOG_LANG`, a gdy jej brak - `pl`).
- Błąd to czytelny tekst na stderr albo, z `--json`, jedna linia `hydrolog-error/1` (`code`, `message`, `hint`, `details`).
  Kod wyjścia: `2` błędne dane wejściowe, `3` brak pliku lub komendy, `4` obliczenia
  niemożliwe, `6` brak opcjonalnego dodatku, `7` uszkodzone dane, `8` ścieżka
  niedozwolona, `9` błąd zapisu, `1` błąd wewnętrzny.
- Eksport CSV (`--csv`) i dawne nazwy opcji (`--length`, `--area`, ...) nie istnieją;
  pełny wynik w JSON daje `--json`.

#### Serwer MCP

Serwer MCP udostępnia każdą komendę jako narzędzie (nazwa = `operation_id`, np. `tc_kirpich`); wymaga dodatku `hydrolog[mcp]`.

```bash
# Claude Code
claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data
```

Inne klienty MCP:

```json
{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}}}
```

- `--allow-dir KATALOG` (można powtórzyć) wskazuje katalogi, w których narzędzia mogą czytać i zapisywać pliki; ścieżki spoza nich kończą się błędem `forbidden`. Bez `--allow-dir` komendy z opcjami typu ścieżka są odrzucane, komendy bez plików (np. `tc_kirpich`) działają.
- `--lang pl|en` wybiera język opisów narzędzi.
- Sukces: `structuredContent` = koperta `hydrolog-result/1`; błąd: `isError: true` z dokumentem `hydrolog-error/1`.

#### Przewodniki dla agentów

[`AGENTS.md`](AGENTS.md) (pełny przewodnik: zasady, tabele komend i błędów, typowe przepływy) i [`llms.txt`](llms.txt) (skrót) są generowane z katalogu komend, nie edytuje się ich ręcznie:

```bash
hydrolog commands guide --format agents --lang pl --path AGENTS.md
hydrolog commands guide --format llms --lang pl --path llms.txt
```

Wersja angielska: `--lang en`. Jak dodać komendę i zregenerować przewodniki: [DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md), sekcja 11.

## Struktura modułów

```
hydrolog/
├── runoff/          # Opad-odpływ (SCS-CN, Nash, Clark, Snyder) ✅
├── precipitation/   # Hietogramy + interpolacja ✅
├── time/            # Czas koncentracji ✅
├── morphometry/     # Parametry fizjograficzne ✅
├── network/         # Klasyfikacja sieci rzecznej ✅
├── statistics/      # Statystyka przepływów ✅
├── hydrometrics/    # Krzywa przepływu, strefy stanów wody ✅
├── soil/            # HSG z uziarnienia gleby (GeoTIFF: dodatek [raster]) ✅
├── catalog/         # Katalog komend: źródło prawdy dla CLI, MCP i przewodników ✅
├── operations/      # Funkcja operacji na komendę katalogu ✅
├── cli/             # Interfejs CLI generowany z katalogu ✅
├── mcp/             # Serwer MCP (dodatek [mcp]) ✅
├── visualization/   # Wykresy (matplotlib/seaborn) ✅
└── reports/         # Raporty Markdown z wzorami LaTeX ✅
```

## Roadmap

| Wersja | Zakres | Status |
|--------|--------|--------|
| v0.1.0 | Hydrogram SCS-CN, hietogramy, czas koncentracji | ✅ Wydana |
| v0.2.0 | Parametry morfometryczne | ✅ Wydana |
| v0.3.0 | Interpolacja opadów, klasyfikacja sieci | ✅ Wydana |
| v0.4.0 | CLI, Clark IUH, Snyder UH, CN Lookup | ✅ Wydana |
| v0.5.0 | Wizualizacja (matplotlib/seaborn) | ✅ Wydana |
| **v0.6.0** | Raporty Markdown z wzorami LaTeX | ✅ Wydana |
| v0.7.0 | Statystyka hydrologiczna, hydrometria | ✅ Wydana |
| **v1.0.0** | Stabilne API, katalog komend, CLI z katalogu, serwer MCP, HSG, serializacja wyników | 🔄 W przygotowaniu |
| po v1.0.0 | Empiryczne wzory na przepływ maksymalny (Punzet, Bogdanowicz-Stachy) | Planowane |

## Wymagania

- Python >= 3.12
- NumPy >= 1.24
- SciPy >= 1.10

**Zależności opcjonalne:**
- `rasterio >= 1.3` + `pyproj >= 3.6` - rastry GeoTIFF dla HSG (`pip install hydrolog[raster]`)
- `mcp >= 2.3, < 3` - serwer MCP (`pip install hydrolog[mcp]`)
- `matplotlib >= 3.7` + `seaborn >= 0.12` - wizualizacja (`pip install hydrolog[visualization]`)
- `pip install hydrolog[all]` - wszystkie powyższe

Hydrolog nie zależy od Kartografa ani IMGWTools; dane z tych narzędzi wczytuje z plików (CSV/JSON, GeoTIFF).

## Dokumentacja

- [Ścieżki obliczeniowe](docs/COMPUTATION_PATHS.md) - Prawidłowe metody estymacji parametrów dla każdego modelu UH, HSG, rozkład Fishera-Tippetta dla minimów
- [Integracja](docs/INTEGRATION.md) - Hydrograf (GIS), Retman, klienci MCP, migracja HSG z Kartografa, eksport IMGWTools
- [Przewodnik dla agentów](AGENTS.md) - komendy, błędy i typowe przepływy (generowany z katalogu)
- [Zakres projektu](docs/SCOPE.md), [PRD](docs/PRD.md), [Standardy kodowania](docs/DEVELOPMENT_STANDARDS.md), [Changelog](docs/CHANGELOG.md)

## Powiązane projekty

- [IMGWTools](https://github.com/Daldek/IMGWTools) - dane IMGW (szeregi pomiarowe, opady); eksport CSV wczytuje Hydrolog
- [Kartograf](https://github.com/Daldek/Kartograf) - pobieranie NMT, pokrycia terenu i rastrów gleb (SoilGrids) dla HSG

## Licencja

MIT License - zobacz [LICENSE](LICENSE)
