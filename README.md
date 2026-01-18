# Hydrolog

Biblioteka Python do obliczeń hydrologicznych.

## Funkcjonalności (v0.1.0)

- **Hydrogramy odpływu** - metoda SCS Curve Number
- **Hietogramy** - rozkład Beta, blokowy, trójkątny
- **Czas koncentracji** - wzory Kirpicha, SCS Lag, Giandotti

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

## Struktura modułów

```
hydrolog/
├── runoff/          # Opad-odpływ (SCS-CN, hydrogramy) ✅
├── precipitation/   # Hietogramy ✅
├── time/            # Czas koncentracji ✅
├── morphometry/     # Parametry fizjograficzne (v0.2.0)
├── network/         # Klasyfikacja sieci rzecznej (v0.3.0)
└── cli/             # Interfejs CLI (v1.0.0)
```

## Roadmap

| Wersja | Zakres | Status |
|--------|--------|--------|
| **v0.1.0** | Hydrogram SCS-CN, hietogramy, czas koncentracji | ✅ Wydana |
| v0.2.0 | Parametry morfometryczne | Planowana |
| v0.3.0 | Interpolacja opadów, klasyfikacja sieci | Planowana |
| v1.0.0 | Stabilne API, CLI, dokumentacja | Planowana |

## Wymagania

- Python >= 3.12
- NumPy >= 1.24

## Powiązane projekty

- [IMGWTools](https://github.com/Daldek/IMGWTools) - Dane opadowe z IMGW

## Licencja

MIT License - zobacz [LICENSE](LICENSE)
