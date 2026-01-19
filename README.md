# Hydrolog

Biblioteka Python do obliczeń hydrologicznych.

## Funkcjonalności

- **Hydrogramy odpływu** - SCS-CN, Nash IUH, Clark IUH, Snyder UH
- **Hietogramy** - rozkład Beta, blokowy, trójkątny, DVWK Euler Type II
- **Czas koncentracji** - wzory Kirpicha, SCS Lag, Giandotti
- **Parametry morfometryczne** - wskaźniki kształtu, teren, krzywa hipsograficzna
- **Klasyfikacja sieci rzecznej** - metody Strahlera i Shreve'a
- **Interpolacja opadów** - Thiessen, IDW, izohiety
- **CN Lookup** - tablice TR-55 (20 typów pokrycia terenu)
- **CLI** - interfejs linii poleceń

## Instalacja

```bash
# Z GitHub
pip install git+https://github.com/Daldek/Hydrolog.git

# Lokalna instalacja deweloperska
git clone https://github.com/Daldek/Hydrolog.git
cd Hydrolog
pip install -e .
```

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

# Wzór SCS Lag (L w km, S w m/m, CN 1-100)
tc_scs = ConcentrationTime.scs_lag(length_km=8.2, slope_m_per_m=0.023, cn=72)

# Wzór Giandotti (A w km², L w km, H w m)
tc_giandotti = ConcentrationTime.giandotti(
    area_km2=45.0, length_km=12.0, elevation_diff_m=350.0
)

print(f"Kirpich: {tc_kirpich:.1f} min")
print(f"SCS Lag: {tc_scs:.1f} min")
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

### Chwilowy hydrogram jednostkowy (Nash IUH)

```python
from hydrolog.runoff import NashIUH
from hydrolog.time import ConcentrationTime

# Metoda 1: IUH bez powierzchni (zwraca wartości bezwymiarowe [1/min])
iuh = NashIUH(n=3.0, k_min=30.0)
result_iuh = iuh.generate(timestep_min=5.0)  # IUHResult
print(f"Czas do szczytu IUH: {iuh.time_to_peak_min:.1f} min")
print(f"Czas opóźnienia: {iuh.lag_time_min:.1f} min")

# Metoda 2: UH z powierzchnią (zwraca wartości wymiarowe [m³/s/mm])
nash = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)
result_uh = nash.generate(timestep_min=5.0)  # NashUHResult
print(f"Qmax UH: {result_uh.peak_discharge_m3s:.2f} m³/s na mm")

# Metoda 3: Estymacja z czasu koncentracji
tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
iuh = NashIUH.from_tc(tc_min=tc, n=3.0, lag_ratio=0.6)

# Jawne generowanie IUH (zawsze zwraca IUHResult)
result = iuh.generate_iuh(timestep_min=5.0, duration_min=300.0)

# Konwersja IUH do D-minutowego hydrogramu jednostkowego
uh = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)
print(f"Qmax UH: {uh.peak_discharge_m3s:.2f} m³/s")
```

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

### Snyder UH

```python
from hydrolog.runoff import SnyderUH

# Metoda 1: Bezpośrednie podanie parametrów (L, Lc w km)
uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=2.0, cp=0.6)

# Metoda 2: Z czasu koncentracji
uh = SnyderUH.from_tc(area_km2=100.0, tc_min=180.0, ct=2.0, cp=0.6)

# Generowanie hydrogramu
result = uh.generate(timestep_min=30.0)
print(f"Czas opóźnienia: {uh.lag_time_min:.1f} min")
print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Czas bazy: {result.time_base_min:.0f} min")
```

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

### CLI - Interfejs linii poleceń

```bash
# Czas koncentracji
hydrolog tc kirpich --length 2.5 --slope 0.02
hydrolog tc scs-lag --length 5.0 --slope 0.01 --cn 72
hydrolog tc giandotti --area 100 --length 15 --elevation 500

# Wyszukiwanie CN
hydrolog cn lookup --hsg B --cover forest --condition good
hydrolog cn list
hydrolog cn range --cover pasture

# Obliczenia SCS-CN
hydrolog scs --cn 72 --precipitation 50
hydrolog scs --cn 72 --precipitation 50 --amc III

# Generowanie hydrogramów
hydrolog uh scs --area 45 --tc 90 --timestep 10
hydrolog uh nash --area 45 --n 3 --k 30 --timestep 10
hydrolog uh clark --area 45 --tc 60 --r 30 --timestep 10
hydrolog uh snyder --area 100 --L 15 --Lc 8 --timestep 30

# Eksport wyników
hydrolog uh scs --area 45 --tc 90 --timestep 10 --csv > hydrograph.csv
hydrolog uh scs --area 45 --tc 90 --timestep 10 --json > hydrograph.json
```

## Struktura modułów

```
hydrolog/
├── runoff/          # Opad-odpływ (SCS-CN, Nash, Clark, Snyder) ✅
├── precipitation/   # Hietogramy + interpolacja ✅
├── time/            # Czas koncentracji ✅
├── morphometry/     # Parametry fizjograficzne ✅
├── network/         # Klasyfikacja sieci rzecznej ✅
└── cli/             # Interfejs CLI ✅
```

## Roadmap

| Wersja | Zakres | Status |
|--------|--------|--------|
| v0.1.0 | Hydrogram SCS-CN, hietogramy, czas koncentracji | ✅ Wydana |
| v0.2.0 | Parametry morfometryczne | ✅ Wydana |
| v0.3.0 | Interpolacja opadów, klasyfikacja sieci | ✅ Wydana |
| **v0.4.0** | CLI, Clark IUH, Snyder UH, CN Lookup | ✅ Wydana |
| v1.0.0 | Stabilne API, dokumentacja | Planowana |

## Wymagania

- Python >= 3.12
- NumPy >= 1.24
- SciPy >= 1.10 (dla Nash IUH)
- IMGWTools (dla danych opadowych PMAXTP)

## Powiązane projekty

- [IMGWTools](https://github.com/Daldek/IMGWTools) - Dane opadowe z IMGW

## Licencja

MIT License - zobacz [LICENSE](LICENSE)
