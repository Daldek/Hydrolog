# Hydrolog

Biblioteka Python do obliczeń hydrologicznych.

## Funkcjonalności (v0.3.0)

- **Hydrogramy odpływu** - metoda SCS Curve Number
- **Hietogramy** - rozkład Beta, blokowy, trójkątny
- **Czas koncentracji** - wzory Kirpicha, SCS Lag, Giandotti
- **Parametry morfometryczne** - wskaźniki kształtu, teren, krzywa hipsograficzna
- **Klasyfikacja sieci rzecznej** - metody Strahlera i Shreve'a
- **Interpolacja opadów** - Thiessen, IDW, izohiety

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
from hydrolog.precipitation import BetaHietogram, BlockHietogram, TriangularHietogram

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
```

### Czas koncentracji

```python
from hydrolog.time import ConcentrationTime

# Wzór Kirpicha (L w km, S w m/m)
tc_kirpich = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)

# Wzór SCS Lag (L w m, S w %, CN 1-100)
tc_scs = ConcentrationTime.scs_lag(length_m=8200, slope_percent=2.3, cn=72)

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

## Struktura modułów

```
hydrolog/
├── runoff/          # Opad-odpływ (SCS-CN, hydrogramy) ✅
├── precipitation/   # Hietogramy + interpolacja ✅
├── time/            # Czas koncentracji ✅
├── morphometry/     # Parametry fizjograficzne ✅
├── network/         # Klasyfikacja sieci rzecznej ✅
└── cli/             # Interfejs CLI (v1.0.0)
```

## Roadmap

| Wersja | Zakres | Status |
|--------|--------|--------|
| v0.1.0 | Hydrogram SCS-CN, hietogramy, czas koncentracji | ✅ Wydana |
| v0.2.0 | Parametry morfometryczne | ✅ Wydana |
| **v0.3.0** | Interpolacja opadów, klasyfikacja sieci | ✅ Wydana |
| v1.0.0 | Stabilne API, CLI, dokumentacja | Planowana |

## Wymagania

- Python >= 3.12
- NumPy >= 1.24

## Powiązane projekty

- [IMGWTools](https://github.com/Daldek/IMGWTools) - Dane opadowe z IMGW

## Licencja

MIT License - zobacz [LICENSE](LICENSE)
