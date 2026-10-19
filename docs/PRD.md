# PRD.md - Product Requirements Document

## Hydrolog - Biblioteka Narzędzi Hydrologicznych

**Wersja:** 1.0.0 (w przygotowaniu)
**Data:** 2026-10-19
**Status:** v1.0.0 w przygotowaniu

---

## 1. Przegląd produktu

### 1.1 Wizja

Hydrolog to biblioteka Python, interfejs CLI i serwer MCP dostarczające zestaw narzędzi do obliczeń hydrologicznych - od generowania hydrogramów odpływu po analizę parametrów morfometrycznych zlewni, statystykę przepływów i wyznaczanie grup hydrologicznych gleb. Wszystkie interfejsy powstają z jednego katalogu komend, więc ta sama komenda działa w kodzie, w terminalu i w narzędziach agentów AI.

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
| **Automatyzacja** | Batch processing | CLI generowane z katalogu komend, wynik `--json` |
| **Retman (platforma agentowa)** | Handlery obliczeń i dane zlewni jako pliki | Warstwa `hydrolog.operations`, `WatershedParameters` JSON, koperta `hydrolog-result/1` |
| **Agent AI (Claude Code i inni klienci MCP)** | Wywoływanie obliczeń bez zgadywania opcji | Serwer MCP `hydrolog mcp`, `AGENTS.md`, `llms.txt` |

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

hietogram = BetaHietogram(alpha=2.0, beta=5.0).generate(
    total_mm=38.5, duration_min=60, timestep_min=5
)
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
- [ ] Metoda klasy `SCSCN` (class-based API)

**Przykład:**
```python
from hydrolog.runoff import SCSCN

result = SCSCN(cn=72).effective_precipitation(precipitation_mm=38.5)
print(f"Effective precipitation: {result.total_effective_mm:.2f} mm")
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

hietogram = BetaHietogram(alpha=2.0, beta=5.0)
result = hietogram.generate(total_mm=38.5, duration_min=60, timestep_min=5)

print(f"Intensities: {result.intensities_mm}")
print(f"Times: {result.times_min}")
print(f"Peak intensity: {result.intensity_mm_per_h.max():.2f} mm/h")
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
- [ ] Przyjmuje: długość cieku [km], spadek [m/m]
- [ ] Zwraca: czas koncentracji [min]
- [ ] Wzór: tc = 0.0195 × L^0.77 × S^(-0.385)

**Przykład:**
```python
from hydrolog.time import ConcentrationTime

tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)
print(f"tc = {tc:.1f} min")
```

---

#### US-T02: Obliczanie czasu koncentracji - NRCS (dawniej SCS Lag)
**Jako** deweloper
**Chcę** obliczyć czas koncentracji metodą NRCS
**Aby** uwzględnić CN w obliczeniach

**Kryteria akceptacji:**
- [ ] Przyjmuje: długość cieku [km], CN, spadek [m/m]
- [ ] Zwraca: czas koncentracji [min]
- [ ] Wzór: Lag = L^0.8 × (S+1)^0.7 / (1900 × Y^0.5), tc = Lag / 0.6

> **Uwaga:** Metoda przemianowana z `scs_lag` na `nrcs` w v0.3.0. Parametr `slope_percent` zmieniony na `slope_m_per_m`.

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

### 2.6 CLI (v0.4.0, przebudowany w v1.0.0)

#### US-C01: Generowanie hydrogramu przez CLI
**Jako** użytkownik
**Chcę** wygenerować hydrogram z linii poleceń
**Aby** zautomatyzować obliczenia

**Kryteria akceptacji:**
- [x] Komenda: `hydrolog hydrograph generate`
- [x] Parametry: `--area-km2`, `--cn`, `--tc-min`, `--hietogram-type`, `--total-mm`, `--duration-min` albo `--watershed-file` (WatershedParameters JSON)
- [x] Wynik: podsumowanie tekstowe albo, z `--json`, koperta `hydrolog-result/1`
- [x] Raport Markdown: `hydrolog report generate --output raport.md ...`

---

### 2.7 Dodatkowe typy hietogramów (v0.1.0-v0.5.0)

#### US-P03: Hietogram trójkątny
**Jako** deweloper
**Chcę** wygenerować hietogram trójkątny z konfigurowalną pozycją szczytu
**Aby** uzyskać uproszczony rozkład opadu z wyraźnym szczytem

#### US-P04: Hietogram Euler Type II
**Jako** deweloper
**Chcę** wygenerować hietogram Euler Type II (DVWK)
**Aby** zastosować standardowy opad projektowy stosowany w krajach niemieckojęzycznych

---

### 2.8 Dodatkowe metody czasu koncentracji (v0.1.0-v0.6.3)

#### US-T03: Czas koncentracji - Giandotti
**Jako** deweloper
**Chcę** obliczyć czas koncentracji wzorem Giandottiego
**Aby** uwzględnić powierzchnię i wysokości zlewni

#### US-T04: Czas koncentracji - FAA
**Jako** deweloper
**Chcę** obliczyć czas koncentracji metodą FAA
**Aby** określić czas odpowiedzi dla spływu powierzchniowego

#### US-T05: Czas koncentracji - Kerby
**Jako** deweloper
**Chcę** obliczyć czas koncentracji metodą Kerby'ego
**Aby** uwzględnić szorstkość powierzchni w obliczeniach spływu powierzchniowego

#### US-T06: Czas koncentracji - Kerby-Kirpich (metoda złożona)
**Jako** deweloper
**Chcę** obliczyć czas koncentracji metodą złożoną Kerby-Kirpich
**Aby** uwzględnić odrębnie segment spływu powierzchniowego i korytowego

---

### 2.9 Dodatkowe modele hydrogramu jednostkowego (v0.4.0-v0.5.0)

#### US-R03: Nash IUH
**Jako** deweloper
**Chcę** wygenerować chwilowy hydrogram jednostkowy modelem Nasha
**Aby** modelować odpływ z wykorzystaniem kaskady zbiorników liniowych

#### US-R04: Clark IUH
**Jako** deweloper
**Chcę** wygenerować chwilowy hydrogram jednostkowy modelem Clarka
**Aby** uwzględnić translację (histogram czas-powierzchnia) i retencję (routing liniowy)

#### US-R05: Snyder UH
**Jako** deweloper
**Chcę** wygenerować syntetyczny hydrogram jednostkowy Snydera
**Aby** wykorzystać zależności empiryczne oparte na L i Lc

---

### 2.10 Tablice CN (v0.4.0)

#### US-R06: Lookup CN z tablic TR-55
**Jako** deweloper
**Chcę** odczytać wartość CN z tablic TR-55
**Aby** nie musieć ręcznie szukać CN dla grupy hydrologicznej i pokrycia terenu

---

### 2.11 Interpolacja przestrzenna opadów (v0.3.0)

#### US-P05: Interpolacja przestrzenna
**Jako** deweloper
**Chcę** obliczyć średni opad na zlewnię z danych stacyjnych
**Aby** uwzględnić rozkład przestrzenny opadów (IDW, Thiessen, izohiety)

---

### 2.12 Moduł wizualizacji (v0.5.0)

#### US-V01: Wykresy wyników obliczeń
**Jako** deweloper
**Chcę** wygenerować wykresy hietogramów, hydrogramów i bilansu wodnego
**Aby** przedstawić wyniki obliczeń w formie graficznej

---

### 2.13 Moduł raportów (v0.6.0)

#### US-RP01: Generowanie raportów obliczeniowych
**Jako** deweloper
**Chcę** wygenerować raport z pełną procedurą obliczeniową w formacie Markdown
**Aby** udokumentować cały proces obliczeń hydrologicznych z wzorami i wynikami

---

### 2.14 Katalog komend, serwer MCP i HSG (v1.0.0)

#### US-K01: Jedna definicja komendy dla wszystkich interfejsów
**Jako** deweloper Hydrologa
**Chcę** zadeklarować komendę raz (operacja + `Command`/`Option`)
**Aby** biblioteka, CLI, serwer MCP i przewodniki dla agentów miały te same nazwy opcji, jednostki, zakresy i walidację

**Kryteria akceptacji:**
- [x] 37 komend w 13 grupach, lista: `hydrolog commands list`
- [x] Schemat opcji (JSON Schema) dla całego katalogu lub jednej komendy: `commands schema`, `--schema`
- [x] Koperta wyniku `hydrolog-result/1` i dokument błędu `hydrolog-error/1` z zamkniętym rejestrem `ERROR_CODES`
- [x] Wszystkie klasy wynikowe mają `to_dict()` i `to_json()`
- [x] Test zgodności CLI, MCP i Pythona oraz bajt po bajcie `AGENTS.md`/`llms.txt` z generatorem

#### US-K02: Obliczenia z plików
**Jako** agent lub skrypt
**Chcę** podawać serie, stacje, odcinki sieci i zlewnie plikiem CSV/JSON
**Aby** nie wklejać długich list liczb do argumentów

**Kryteria akceptacji:**
- [x] CSV (przecinek lub średnik, UTF-8, nagłówek) i JSON
- [x] Eksport szeregu IMGWTools (`export_series`) wczytuje się bez przetwarzania
- [x] Zlewnia: `WatershedParameters` JSON (format `catchment_characteristics` w Retmanie)

#### US-M01: Serwer MCP
**Jako** użytkownik klienta MCP (np. Claude Code)
**Chcę** wywoływać komendy Hydrologa jako narzędzia
**Aby** agent liczył hydrologię lokalnie, bez sieci i kluczy

**Kryteria akceptacji:**
- [x] `hydrolog mcp [--allow-dir DIR]... [--lang pl|en]` (dodatek `hydrolog[mcp]`)
- [x] Jedno narzędzie na komendę (nazwa = `operation_id`), `structuredContent` = koperta wyniku, błąd jako `isError` z `hydrolog-error/1`
- [x] Dostęp do plików tylko w katalogach `--allow-dir` (inaczej `forbidden`)

#### US-S01: Grupa hydrologiczna gleby (HSG)
**Jako** hydrolog
**Chcę** wyznaczyć rastr HSG z rastrów iłu, piasku i pyłu (np. SoilGrids) i powierzchnie grup A-D
**Aby** policzyć CN ważone powierzchnią zlewni

**Kryteria akceptacji:**
- [x] `hydrolog.soil`: klasa uziarnienia USDA i HSG (tylko NumPy), `hsg_from_rasters`, `hsg_statistics` (dodatek `hydrolog[raster]`)
- [x] Komendy `soil texture`, `soil hsg`, `soil hsg-stats`
- [x] Reguły zgodne z Kartografem 0.8.0 (ADR-025); Hydrolog nie zależy od Kartografa

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
- SciPy >= 1.10 (wymagane od v0.7.0; rozkłady statystyczne, funkcja gamma, optymalizacja)
- Matplotlib >= 3.7 (opcjonalnie, moduł visualization)
- Seaborn >= 0.12 (opcjonalnie, moduł visualization)
- rasterio >= 1.3, pyproj >= 3.6 (opcjonalnie, dodatek `[raster]`: HSG z rastrów)
- mcp >= 2.3, < 3 (opcjonalnie, dodatek `[mcp]`: serwer MCP)
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
- Operacje wejścia/wyjścia (pliki CSV/JSON, GeoTIFF, zapis raportu) tylko w warstwie operacji/katalogu i CLI/MCP; klasy obliczeniowe nie czytają plików
- Brak dostępu do sieci i pobierania danych (dane dostarczają IMGWTools i Kartograf)

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

### v0.1.0 - Hydrogram SCS-CN *(zrealizowane)*
- [x] `runoff.scs_cn` - obliczenia SCS-CN (klasa `SCSCN`)
- [x] `runoff.unit_hydrograph` - SCS UH
- [x] `runoff.convolution` - splot
- [x] `precipitation.hietogram` - Beta, blokowy, trójkątny
- [x] `time.concentration` - Kirpich, NRCS (dawniej SCS Lag), Giandotti
- [x] Testy: > 80% coverage (103 testy)
- [x] Dokumentacja: README, docstrings

### v0.2.0 - Parametry morfometryczne *(zrealizowane)*
- [x] `morphometry.geometric` - powierzchnia, obwód, wskaźniki kształtu
- [x] `morphometry.terrain` - wysokości, spadki
- [x] `morphometry.hypsometry` - krzywa hipsometryczna
- [x] Testy i dokumentacja (150 testów)

### v0.3.0 - Interpolacja i sieć *(zrealizowane)*
- [x] `precipitation.interpolation` - IDW, Thiessen, izohiety, średnia arytmetyczna
- [x] `network.classification` - Strahler, Shreve
- [x] `network.parameters` - wskaźniki sieci (gęstość drenażu, współczynnik bifurkacji)
- [ ] `precipitation.scenarios` - integracja PMAXTP
- [x] Testy i dokumentacja (210 testów)

### v0.4.0 - CLI + zaawansowane modele UH *(zrealizowane)*
- [x] `cli` - interfejs linii poleceń (tc, cn, scs, uh)
- [x] `runoff.nash_iuh` - Nash IUH (model kaskadowy)
- [x] `runoff.clark_iuh` - Clark IUH (histogram czas-powierzchnia + routing)
- [x] `runoff.snyder_uh` - Snyder UH (syntetyczny hydrogram jednostkowy)
- [x] `runoff.cn_lookup` - tablice CN wg TR-55 (20 typów pokrycia terenu)
- [x] Testy i dokumentacja (412 testów)

### v0.5.0 - Wizualizacja *(zrealizowane)*
- [x] `visualization` - moduł wykresów (matplotlib/seaborn)
  - [x] Hietogramy, hydrogramy, porównania UH
  - [x] Bilans wodny, krzywa CN, krzywa hipsometryczna
  - [x] Statystyki sieci rzecznej, mapa stacji opadowych
  - [x] Dashboard z pełnymi wynikami obliczeń
- [x] `precipitation.hietogram` - Euler Type II (DVWK)
- [x] `runoff.nash_iuh` - metoda Lutza (estymacja n, K z cech zlewni)
- [x] Testy i dokumentacja (538 testów)

### v0.5.1/v0.5.2 - Poprawki *(zrealizowane)*
- [x] Korekta stałej SCS peak discharge (2.08 -> 0.208)
- [x] `morphometry.WatershedParameters` - interfejs integracji GIS
- [x] Usunięcie nieużywanej zależności imgwtools

### v0.6.0 - Raporty *(zrealizowane)*
- [x] `reports` - moduł generowania raportów Markdown
  - [x] Pełna procedura obliczeniowa z wzorami LaTeX
  - [x] Obsługa wszystkich modeli UH (SCS, Nash, Clark, Snyder)
  - [x] Konfigurowalne sekcje (wzory, tabele, bilans wodny)
- [x] Testy i dokumentacja (610 testów)

### v0.6.1-v0.6.3 - Rozszerzenia i jakość *(zrealizowane)*
- [x] `runoff.nash_iuh` - metoda regresji urbanistycznej (Rao, Delleur, Sarma 1972)
- [x] Pełne wzory obliczeniowe w raportach dla wszystkich modeli UH
- [x] `time.concentration` - metody FAA, Kerby, Kerby-Kirpich
- [x] Korekty metryczne (Snyder W50/W75, Clark histogram, SCS Lag)
- [x] Rozszerzenie `WatershedParameters` o 8 nowych pól
- [x] Testy i dokumentacja (754 testy)

### v0.7.0 - Statystyka hydrologiczna + Hydrometria *(zrealizowane)*
- [x] `statistics.characteristic` - wartości charakterystyczne (NNQ–WWQ), statystyki dobowe/miesięczne
- [x] `statistics.high_flows` - analiza częstości: LogNormal, GEV, Pearson III, Weibull
- [x] `statistics.low_flows` - Fisher-Tippett, detekcja niżówek
- [x] `statistics.stationarity` - test Manna-Kendalla
- [x] `hydrometrics.rating_curve` - krzywa natężenia, strefy Rybczyńskiego
- [x] `visualization.statistics` - 10 funkcji wizualizacji
- [x] Testy i dokumentacja

### v1.0.0 - Stabilne API, katalog komend, MCP, HSG *(w przygotowaniu)*
- [x] `catalog`, `operations` - katalog 37 komend i warstwa operacji
- [x] `cli` - CLI generowane z katalogu (zmiana niezgodna wstecz: dawna składnia usunięta)
- [x] `mcp` - serwer MCP (`hydrolog mcp`, dodatek `[mcp]`)
- [x] `agent_guide` - `AGENTS.md` i `llms.txt` generowane z katalogu
- [x] `soil` - HSG z rastrów uziarnienia (dodatek `[raster]`), usunięcie zależności od Kartografa
- [x] Serializacja wyników (`JsonResultMixin`), rejestr błędów `ERROR_CODES`
- [x] Poprawki obliczeniowe: Fisher-Tippett dla minimów, Clark UH dla D niebędącego wielokrotnością kroku, raport obliczeniowy, StreamNetwork, RatingCurve (szczegóły: CHANGELOG)
- [ ] Empiryczne wzory na przepływ maksymalny (Punzet, Bogdanowicz-Stachy) - po v1.0.0
- [ ] Pełna dokumentacja API (MkDocs/Sphinx)
- [ ] Publikacja na PyPI

---

**Wersja dokumentu:** 1.0.0 (w przygotowaniu)
**Data ostatniej aktualizacji:** 2026-10-19
