# Hydrolog

Biblioteka Python do obliczeń hydrologicznych.

## Funkcjonalności

- **Hydrogramy odpływu** - metoda SCS Curve Number
- **Hietogramy** - rozkład Beta, blokowy, trójkątny
- **Czas koncentracji** - wzory Kirpicha, SCS Lag
- **Parametry morfometryczne** - wskaźniki geometryczne i terenowe
- **Klasyfikacja sieci rzecznej** - metody Hortona i Strahlera
- **Interpolacja opadów** - IDW, Thiessen

## Instalacja

```bash
# Z GitHub
pip install git+https://github.com/Daldek/hydrolog2.git

# Lokalna instalacja deweloperska
git clone https://github.com/Daldek/hydrolog2.git
cd hydrolog2
pip install -e .
```

## Quick Start

### Generowanie hydrogramu

```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram
from hydrolog.time import ConcentrationTime

# 1. Oblicz czas koncentracji
tc = ConcentrationTime.kirpich(length_km=8.2, slope_percent=2.3)
print(f"Czas koncentracji: {tc:.1f} min")

# 2. Utwórz hietogram
hietogram = BetaHietogram(
    total_mm=38.5,
    duration_min=60,
    timestep_min=5
)

# 3. Wygeneruj hydrogram
generator = HydrographGenerator(
    area_km2=45.3,
    cn=72,
    tc_min=tc
)
result = generator.generate(hietogram)

# 4. Wyniki
print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Czas do szczytu: {result.time_to_peak_min} min")
print(f"Objętość odpływu: {result.total_volume_m3:.0f} m³")
```

### Tylko hietogram

```python
from hydrolog.precipitation import BetaHietogram, BlockHietogram

# Hietogram Beta (realistyczny)
beta = BetaHietogram(total_mm=38.5, duration_min=60, timestep_min=5)
print(f"Intensywności: {beta.intensities_mm_per_min}")

# Hietogram blokowy (stała intensywność)
block = BlockHietogram(total_mm=38.5, duration_min=60, timestep_min=5)
print(f"Intensywność: {block.intensity_mm_per_min:.3f} mm/min")
```

### Czas koncentracji

```python
from hydrolog.time import ConcentrationTime

# Wzór Kirpicha
tc_kirpich = ConcentrationTime.kirpich(length_km=8.2, slope_percent=2.3)

# Wzór SCS Lag
tc_scs = ConcentrationTime.scs_lag(length_m=8200, cn=72, slope_percent=2.3)

print(f"Kirpich: {tc_kirpich:.1f} min")
print(f"SCS Lag: {tc_scs:.1f} min")
```

## Struktura modułów

```
hydrolog/
├── runoff/          # Opad-odpływ (SCS-CN, hydrogramy)
├── precipitation/   # Hietogramy, interpolacja
├── time/            # Czas koncentracji
├── morphometry/     # Parametry fizjograficzne
├── network/         # Klasyfikacja sieci rzecznej
└── cli/             # Interfejs CLI
```

## CLI

```bash
# Generowanie hydrogramu
hydrolog generate-hydrograph \
    --area 45.3 --cn 72 --tc 68.5 \
    --precipitation 38.5 --duration 60 \
    --output result.json

# Obliczenie czasu koncentracji
hydrolog calculate-tc \
    --length 8.2 --slope 2.3 --method kirpich

# Generowanie hietogramu
hydrolog hietogram \
    --total 38.5 --duration 60 --type beta \
    --timestep 5 --output hietogram.csv
```

## Roadmap

| Wersja | Zakres |
|--------|--------|
| v0.1.0 | Hydrogram SCS-CN, hietogramy, czas koncentracji |
| v0.2.0 | Parametry morfometryczne |
| v0.3.0 | Interpolacja opadów, klasyfikacja sieci |
| v1.0.0 | Stabilne API, CLI, dokumentacja |

## Zależności

- Python >= 3.12
- NumPy >= 1.24
- IMGWTools (dla danych PMAXTP)

## Powiązane projekty

- [Hydrograf](https://github.com/Daldek/Hydrograf) - System analizy hydrologicznej (używa Hydrolog)
- [Kartograf](https://github.com/Daldek/Kartograf) - Pobieranie danych przestrzennych
- [IMGWTools](https://github.com/Daldek/IMGWTools) - Dane z IMGW

## Licencja

MIT License - zobacz [LICENSE](LICENSE)

## Dokumentacja

- [SCOPE.md](docs/SCOPE.md) - Zakres projektu
- [PRD.md](docs/PRD.md) - Wymagania produktowe
- [DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md) - Standardy kodowania
- [PROGRESS.md](docs/PROGRESS.md) - Status projektu
