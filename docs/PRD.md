# PRD.md - Product Requirements Document

## Hydrolog - Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.0
**Data:** 2026-01-18
**Status:** W trakcie realizacji

---

## 1. Przegląd produktu

### 1.1 Wizja

Hydrolog to biblioteka Python dostarczająca zestaw narzędzi do obliczeń hydrologicznych - od generowania hydrogramów odpływu po analizę parametrów morfometrycznych zlewni.

### 1.2 Cele biznesowe

1. **Modularność:** Możliwość użycia pojedynczych modułów bez instalacji całości
2. **Reużywalność:** Zewnętrzna zależność dla projektu Hydrograf i innych
3. **Rozszerzalność:** Łatwe dodawanie nowych metod obliczeniowych
4. **Jakość:** Pokrycie testami > 80%, pełna dokumentacja

### 1.3 Użytkownicy docelowi

| Użytkownik | Potrzeba | Jak Hydrolog pomaga |
|------------|----------|---------------------|
| **Deweloper Hydrograf** | Obliczenia hydrologiczne w API | Import modułów jako zależność |
| **Hydrolog/badacz** | Szybkie obliczenia w Jupyter | Proste API, przykłady |
| **Automatyzacja** | Batch processing | CLI interface |

---

## 2. User Stories

### 2.1 Moduł runoff (v0.1.0)

#### US-R01: Generowanie hydrogramu SCS-CN
**Jako** deweloper aplikacji hydrologicznej
**Chcę** wygenerować hydrogram odpływu metodą SCS-CN
**Aby** określić przepływ maksymalny dla danego scenariusza opadowego

**Kryteria akceptacji:**
- [ ] Przyjmuje: powierzchnię zlewni [km²], CN, czas koncentracji [min]
- [ ] Przyjmuje: hietogram (array intensywności) lub obiekt Hietogram
- [ ] Zwraca: obiekt HydrographResult z Qmax, czasem do szczytu, objętością
- [ ] Zwraca: szereg czasowy (czas, przepływ) jako numpy arrays
- [ ] Obsługuje warunki AMC-I, AMC-II, AMC-III
- [ ] Rzuca wyjątek dla nieprawidłowych danych (CN<0, CN>100, area<=0)

**Przykład użycia:**
```python
from hydrolog.runoff import HydrographGenerator
from hydrolog.precipitation import BetaHietogram

hietogram = BetaHietogram(total_mm=38.5, duration_min=60, timestep_min=5)
generator = HydrographGenerator(area_km2=45.3, cn=72, tc_min=68.5)
result = generator.generate(hietogram)

print(f"Qmax: {result.peak_discharge_m3s:.2f} m³/s")
print(f"Time to peak: {result.time_to_peak_min} min")
print(f"Volume: {result.total_volume_m3:.0f} m³")
```

---

#### US-R02: Obliczanie opadu efektywnego
**Jako** deweloper
**Chcę** obliczyć opad efektywny metodą SCS-CN
**Aby** określić ile opadu zamieni się w odpływ

**Kryteria akceptacji:**
- [ ] Przyjmuje: opad całkowity [mm], CN
- [ ] Zwraca: opad efektywny [mm]
- [ ] Obsługuje przypadek P < Ia (zwraca 0)
- [ ] Metoda statyczna lub funkcja modułu

**Przykład:**
```python
from hydrolog.runoff import calculate_effective_precipitation

pe = calculate_effective_precipitation(precipitation_mm=38.5, cn=72)
print(f"Effective precipitation: {pe:.2f} mm")
```

---

### 2.2 Moduł precipitation (v0.1.0)

#### US-P01: Generowanie hietogramu Beta
**Jako** deweloper
**Chcę** wygenerować hietogram o rozkładzie Beta
**Aby** uzyskać realistyczny rozkład opadu w czasie

**Kryteria akceptacji:**
- [ ] Przyjmuje: opad całkowity [mm], czas trwania [min], krok czasowy [min]
- [ ] Opcjonalnie: parametry alpha, beta (domyślnie α=2, β=5)
- [ ] Zwraca: obiekt z tablicą intensywności i czasów
- [ ] Suma intensywności × dt = opad całkowity (±0.01 mm)

**Przykład:**
```python
from hydrolog.precipitation import BetaHietogram

hietogram = BetaHietogram(
    total_mm=38.5,
    duration_min=60,
    timestep_min=5,
    alpha=2.0,
    beta=5.0
)

print(f"Intensities: {hietogram.intensities_mm_per_min}")
print(f"Times: {hietogram.times_min}")
print(f"Peak intensity: {hietogram.peak_intensity_mm_per_min:.2f} mm/min")
```

---

#### US-P02: Generowanie hietogramu blokowego
**Jako** deweloper
**Chcę** wygenerować hietogram blokowy (stała intensywność)
**Aby** wykonać uproszczone obliczenia

**Kryteria akceptacji:**
- [ ] Przyjmuje: opad całkowity [mm], czas trwania [min], krok czasowy [min]
- [ ] Zwraca: obiekt z tablicą stałej intensywności
- [ ] Intensywność = total_mm / duration_min

---

### 2.3 Moduł time (v0.1.0)

#### US-T01: Obliczanie czasu koncentracji - Kirpich
**Jako** deweloper
**Chcę** obliczyć czas koncentracji wzorem Kirpicha
**Aby** określić czas odpowiedzi zlewni

**Kryteria akceptacji:**
- [ ] Przyjmuje: długość cieku [km], spadek [%]
- [ ] Zwraca: czas koncentracji [min]
- [ ] Wzór: tc = 0.0195 × L^0.77 × S^(-0.385)
- [ ] Obsługuje jednostki: km i m dla długości, % i m/m dla spadku

**Przykład:**
```python
from hydrolog.time import ConcentrationTime

tc = ConcentrationTime.kirpich(length_km=8.2, slope_percent=2.3)
print(f"tc = {tc:.1f} min")

# Alternatywnie z metrami
tc = ConcentrationTime.kirpich(length_m=8200, slope_m_per_m=0.023)
```

---

#### US-T02: Obliczanie czasu koncentracji - SCS Lag
**Jako** deweloper
**Chcę** obliczyć czas koncentracji metodą SCS Lag
**Aby** uwzględnić CN w obliczeniach

**Kryteria akceptacji:**
- [ ] Przyjmuje: długość cieku [m lub ft], CN, spadek [%]
- [ ] Zwraca: czas koncentracji [min]
- [ ] Wzór: Lag = L^0.8 × (S+1)^0.7 / (1900 × Y^0.5), tc = Lag / 0.6

---

### 2.4 Moduł morphometry (v0.2.0)

#### US-M01: Obliczanie parametrów geometrycznych
**Jako** deweloper
**Chcę** obliczyć podstawowe parametry geometryczne zlewni
**Aby** scharakteryzować jej kształt

**Kryteria akceptacji:**
- [ ] Przyjmuje: tablicę wysokości (2D array), rozmiar komórki [m]
- [ ] Oblicza: powierzchnię, obwód, długość, szerokość
- [ ] Zwraca: słownik lub obiekt z parametrami

---

#### US-M02: Obliczanie wskaźników kształtu
**Jako** deweloper
**Chcę** obliczyć wskaźniki kształtu zlewni
**Aby** porównać ją z innymi zlewniami

**Kryteria akceptacji:**
- [ ] Oblicza: Cf, Cz, Ck, Cw, Cl
- [ ] Wymaga wcześniejszego obliczenia parametrów geometrycznych

---

### 2.5 Moduł network (v0.3.0)

#### US-N01: Klasyfikacja Strahlera
**Jako** deweloper
**Chcę** sklasyfikować sieć rzeczną metodą Strahlera
**Aby** określić rząd cieku głównego

**Kryteria akceptacji:**
- [ ] Przyjmuje: strukturę sieci (adjacency list lub podobne)
- [ ] Zwraca: rząd dla każdego segmentu

---

### 2.6 CLI (v1.0.0)

#### US-C01: Generowanie hydrogramu przez CLI
**Jako** użytkownik
**Chcę** wygenerować hydrogram z linii poleceń
**Aby** zautomatyzować obliczenia

**Kryteria akceptacji:**
- [ ] Komenda: `hydrolog generate-hydrograph`
- [ ] Parametry: --area, --cn, --tc, --precipitation, --duration
- [ ] Opcje: --output (JSON/CSV), --hietogram-type
- [ ] Wyświetla wyniki lub zapisuje do pliku

---

## 3. Wymagania niefunkcjonalne

### 3.1 Wydajność

| Operacja | Target |
|----------|--------|
| Generowanie hydrogramu (typowe dane) | < 100 ms |
| Generowanie hietogramu | < 10 ms |
| Obliczenie tc | < 1 ms |
| Parametry morfometryczne (100x100 grid) | < 1 s |

### 3.2 Jakość kodu

- **Pokrycie testami:** > 80%
- **Type hints:** 100% publicznych funkcji
- **Docstrings:** 100% publicznych klas/metod
- **Linting:** flake8, mypy bez błędów

### 3.3 Dokumentacja

- README z quick start
- Docstrings NumPy style
- Przykłady użycia dla każdego modułu
- API reference (Sphinx lub MkDocs)

### 3.4 Kompatybilność

- Python >= 3.12
- NumPy >= 1.24
- Brak zależności od GeoPandas/Shapely w core

---

## 4. Ograniczenia i założenia

### 4.1 Ograniczenia metodologiczne

- SCS-CN dla zlewni < 250 km²
- Opad równomierny na całą zlewnię
- Warunki wilgotnościowe AMC-II jako domyślne
- Brak routingu przepływu

### 4.2 Założenia techniczne

- Dane wejściowe: NumPy arrays, podstawowe typy Python
- Thread-safe (brak stanu globalnego)
- Brak operacji I/O w core (tylko CLI)

---

## 5. Metryki sukcesu

| Metryka | Target | Pomiar |
|---------|--------|--------|
| Pokrycie testami | > 80% | pytest-cov |
| Czas generowania hydrogramu | < 100 ms | benchmark |
| Dokładność obliczeń | ±1% vs literatura | testy walidacyjne |
| Dokumentacja | 100% public API | sphinx-apidoc |

---

## 6. Roadmap

### v0.1.0 - Hydrogram SCS-CN
- [ ] `runoff.scs_cn` - obliczenia SCS-CN
- [ ] `runoff.unit_hydrograph` - SCS UH
- [ ] `runoff.convolution` - splot
- [ ] `precipitation.hietogram` - Beta, blokowy
- [ ] `time.concentration` - Kirpich, SCS Lag
- [ ] Testy: > 80% coverage
- [ ] Dokumentacja: README, docstrings

### v0.2.0 - Parametry morfometryczne
- [ ] `morphometry.geometric` - powierzchnia, obwód
- [ ] `morphometry.terrain` - wysokości, spadki
- [ ] `morphometry.indicators` - wskaźniki kształtu
- [ ] Testy i dokumentacja

### v0.3.0 - Interpolacja i sieć
- [ ] `precipitation.interpolation` - IDW, Thiessen
- [ ] `precipitation.scenarios` - integracja PMAXTP
- [ ] `network.classification` - Horton, Strahler
- [ ] `network.parameters` - wskaźniki sieci
- [ ] Testy i dokumentacja

### v1.0.0 - Stabilne API + CLI
- [ ] `cli.main` - interfejs CLI
- [ ] Stabilizacja API (bez breaking changes)
- [ ] Pełna dokumentacja (MkDocs/Sphinx)
- [ ] Publikacja na PyPI

---

**Wersja dokumentu:** 1.0
**Data ostatniej aktualizacji:** 2026-01-18
