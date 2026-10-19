# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [1.0.0] - niewydana (w przygotowaniu)

Pierwsze wydanie stabilnego API: od tej wersji obowiązuje wersjonowanie semantyczne (nazwy komend i opcji, schematy `hydrolog-result/1` i `hydrolog-error/1` oraz kody błędów są publicznym API). Klasy biblioteki (`SCSCN`, `HydrographGenerator`, `NashIUH`, `ClarkIUH`, `SnyderUH`, `ConcentrationTime`, hietogramy, `WatershedParameters`, statystyki, hydrometria, raporty, wizualizacja) zachowują nazwy i sygnatury; zmiany w nich są dodatkami lub poprawkami błędów opisanymi niżej.

### BREAKING

- **CLI:** dawna składnia (v0.4.0-v0.7.0) została usunięta bez aliasów; komendy mają teraz postać `hydrolog <grupa> <komenda> --opcja wartość` z nazwami opcji katalogu (`--kebab-case`, jednostka w nazwie). Przykłady: `hydrolog scs --cn 72 --precipitation 50` → `hydrolog scs effective --cn 72 --precipitation-mm 50`; `hydrolog tc kirpich --length 2.5 --slope 0.02` → `hydrolog tc kirpich --length-km 2.5 --slope-m-per-m 0.02`; `hydrolog uh scs --area 45 --tc 90 --timestep 10` → `hydrolog uh scs --area-km2 45 --tc-min 90 --timestep-min 10`; `hydrolog cn lookup --cover forest` → `hydrolog cn lookup --land-cover forest`. Eksport `--csv` nie istnieje; pełny wynik daje `--json` (koperta `hydrolog-result/1`).
- **Dodatek `hydrolog[spatial]` (Kartograf) usunięty:** Hydrolog nie zależy już od Kartografa (ani od IMGWTools). Rastry gleb pobiera Kartograf (`download_soil`), a HSG liczy Hydrolog (`hydrolog.soil`, dodatek `hydrolog[raster]`). Dodatek `all` obejmuje teraz `raster`, `mcp` i `visualization`.
- **Zmienione wyniki liczbowe** (poprawki błędów, patrz „Fixed"): kwantyle `LowFlowAnalysis.fit_fisher_tippett()`, hydrogram jednostkowy Clarka dla czasu trwania D niebędącego wielokrotnością kroku, `calculate_monthly_statistics()` dla miesiąca z jedną wartością (`NaN` zamiast przedziału `[średnia, średnia]`), treść raportu obliczeniowego oraz (od przeglądu przed wydaniem) czas koncentracji `WatershedParameters.calculate_tc()` dla metod FAA, Kerby'ego i NRCS, hydrogram `HydrographGenerator` z modelem Snydera i `hydrograph generate`/`report generate` z `cn` podanym obok zlewni (czas koncentracji NRCS), a także maksima i minima roczne (`stats flood-frequency`, `stats low-flow`, `LowFlowAnalysis`) dla szeregów z niepełnymi latami hydrologicznymi, blok `empirical` w `stats low-flow` (konwencja nieprzekroczenia) i domyślny start H₀ krzywej przepływu.
- **Zmiana typów wyjątków:** wyjątki walidacji są teraz `InvalidParameterError` (także `ValueError`), a nie gołe `ValueError` (`WatershedParameters.calculate_tc()`, `calculate_monthly_statistics()` dla miesiąca bez wartości); `RatingCurve` zgłasza `RatingCurveFitError` (`CalculationError`, a zgodnie wstecz także `InvalidParameterError`). Kod z `except ValueError` lub `except InvalidParameterError` działa jak dotąd.
- **`WatershedParameters.calculate_tc()` dla FAA i Kerby'ego wymaga `overland_length_km` i `overland_slope_m_per_m`:** obie metody liczą czas spływu powierzchniowego, więc nie podstawiają już długości i spadku koryta (dawniej liczyły z nimi cicho, także dla zlewni bez pól spływu powierzchniowego). Zlewnia bez tych pól kończy się `InvalidParameterError` (`details.reason` = `missing_field`, `details.missing`, wskazówka w `hint`: `kerby_kirpich` lub `kirpich` dla zlewni z korytem); dotyczy też `tc watershed`, `hydrograph generate --tc-method` i `report generate --tc-method`.
- `HydrologyReportGenerator.generate()` zgłasza `InvalidParameterError`, gdy `result.unit_hydrograph_result` jest `None` (raport dokumentuje hydrogram jednostkowy użyty w obliczeniach, a `HydrographGenerator.generate()` zawsze go zwraca).

### Added

#### Katalog komend (`hydrolog.catalog`) i warstwa operacji (`hydrolog.operations`)
Jedno źródło prawdy dla biblioteki, CLI, serwera MCP i przewodników dla agentów: 37 komend w 13 grupach (`tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `commands`); lista: `hydrolog commands list`.
- `Command` i `Option` (opisy PL/EN, jednostki, zakresy, grupy `one_of`, przykłady), `data_commands()`, `get_command()`, `command_schema()` (JSON Schema 2020-12, dokument `hydrolog-commands/1`), `validate_command()`, `run_command()` (polityka ścieżek `allowed_dirs`), `capture_warnings()`.
- `hydrolog.operations`: po jednej publicznej, otypowanej funkcji na komendę (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...); zwraca obiekt wynikowy z `to_dict()`/`to_json()` albo `OperationOutput` (wynik, ostrzeżenia, zapisane pliki).
- Koperta wyniku `hydrolog-result/1` (`schema`, `command`, `hydrolog_version`, `status`, `inputs`, `result`, `files` z SHA-256, `notices`).
- Dokument błędu `hydrolog-error/1` i zamknięty rejestr `ERROR_CODES`: `validation_error` (2), `not_found` (3), `calculation_error` (4), `missing_dependency` (6), `data_error` (7), `forbidden` (8), `io_error` (9), `internal_error` (1); `HydrologError` ma `code`, `details` i `hint`.
- Nowe klasy wyjątków: `InputDataError`, `MissingDependencyError`, `ForbiddenPathError`, `NotFoundError`, `OutputError` (wyeksportowane z `hydrolog`).

#### Serializacja wyników (`hydrolog._serialization`)
- `JsonResultMixin` z `to_dict()` i `to_json()` we wszystkich klasach wynikowych (runoff, precipitation, morphometry, network, statistics, hydrometrics, soil); `NaN` i nieskończoności są `null`, tablice NumPy listami, nieznany typ to `TypeError`. `WatershedParameters.to_dict()`/`to_json()` bez zmian.

#### Dane wejściowe z plików
- Serie (`input_file` + `value_column`/`date_column`), stacje opadowe (`stations_file`), odcinki sieci (`segments_file`) i zlewnie (`watershed_file`) jako CSV (przecinek lub średnik, UTF-8) albo JSON; kolumny wskazuje się nazwą dokładną lub bez sufiksu jednostki (`Q` znajduje `Q [m3/s]`).
- Eksport szeregu IMGWTools (`export_series` CSV) wczytuje się bez przetwarzania; `WatershedParameters` JSON jest proponowanym formatem `catchment_characteristics` w Retmanie.

#### `hydrolog.soil` - Grupy hydrologiczne gleb (HSG)
Reguły przeniesione z Kartografa 0.8.0 (`kartograf.hydrology.hsg`, ADR-025); Kartograf zostaje przy pobieraniu rastrów (`download_soil`).
- `texture`: klasyfikacja uziarnienia USDA (12 klas) z zawartości iłu, piasku i pyłu (`classify_usda_texture`, `classify_usda_texture_array`), `TEXTURE_TO_HSG`, `texture_to_hsg` (tylko NumPy).
- `hsg`: `classify_hsg`, `hsg_statistics_array`, `HsgStatistics`, `HSG_CODES` (GeoTIFF `uint8`: 0 - brak danych, 1-4 to A-D).
- `raster` (dodatek `hydrolog[raster]`: `rasterio>=1.3`, `pyproj>=3.6`): `hsg_from_rasters()` (rastry iłu, piasku i pyłu → GeoTIFF HSG) i `hsg_statistics()` (powierzchnie grup, opcjonalnie w prostokącie `bbox`).
- Komendy `soil texture`, `soil hsg`, `soil hsg-stats`.

#### Serwer MCP (`hydrolog mcp`)
- Dodatek `hydrolog[mcp]` (`mcp>=2.3,<3`): każda komenda katalogu jest narzędziem (nazwa = `operation_id`), `structuredContent` = koperta wyniku, błąd jako `isError` z `hydrolog-error/1`.
- `hydrolog mcp [--allow-dir DIR]... [--lang pl|en]`: dostęp do plików tylko w katalogach `--allow-dir` (bez nich komendy z opcjami typu ścieżka kończą się `forbidden`).

#### Przewodniki dla agentów
- `AGENTS.md` i `llms.txt` w repozytorium, generowane z katalogu przez `hydrolog commands guide --format agents|llms --lang pl|en [--path PLIK]`; test porównuje bajty z generatorem (`hydrolog.agent_guide`).

#### Pozostałe
- `hydrolog.hydrometrics.RatingCurveFitError`.
- `pyproject.toml`: dodatki `raster`, `mcp`, `all`; szablony przewodników w pakiecie (`package-data`); `jsonschema` w zależnościach `dev`.
- `WatershedParameters.tc_parameters(method)`: argumenty wzoru czasu koncentracji, które `calculate_tc()` wyprowadza z pól zlewni (`calculate_tc` to wzór zastosowany do `tc_parameters`); stąd pochodzi `parameters` wyniku `tc watershed`.
- `LowFlowAnalysis.empirical_non_exceedance(method)` i `LowFlowEmpiricalFrequency` (`values_ascending`, `non_exceedance_probabilities`, `return_periods`; eksport z `hydrolog.statistics`).
- Pole wyniku `incomplete_years` w `stats flood-frequency` (lista lat; `null` dla maksimów podanych bez dat) i `stats low-flow` (lista lat) oraz notice `incomplete_years`.

### Changed

#### `hydrolog.cli` - CLI generowane z katalogu komend (zmiana niezgodna wstecz)
Parser argparse powstaje z `hydrolog.catalog.data_commands()`: każda komenda katalogu
jest dostępna jako `hydrolog <grupa> <komenda> --opcje`, z pomocą, jednostkami i
przykładami z katalogu (PL/EN). Punkt wejścia bez zmian (`hydrolog.cli.main:main`).
- Opcje: `--kebab-case` nazw opcji katalogu; liczby i listy liczb (`--values 1,2,3`),
  teksty, obiekty i listy obiektów jako JSON, opcje logiczne `--flaga` / `--no-flaga`,
  liczby ujemne (`--opcja -5`); walidację (zakresy, wybory, `one_of`) robi katalog,
  więc CLI, serwer MCP i Python zgłaszają te same błędy.
- Flagi ogólne (przed grupą i po komendzie): `--json` (koperta `hydrolog-result/1`
  w jednej linii), `--schema` (JSON Schema opcji bez uruchamiania), `--lang pl|en`
  (zmienna `HYDROLOG_LANG`, domyślnie `pl`; dla komend z opcją `lang` jest to ta opcja),
  `-V/--version`. Bez `--json` wynik to zwięzłe podsumowanie (skalary, tabele,
  pierwsze wiersze tablic, uwagi, zapisane pliki).
- Błędy: czytelny tekst na stderr albo jedna linia `hydrolog-error/1` z `--json`;
  kod wyjścia z `ERROR_CODES` (2, 3, 4, 6, 7, 8, 9, 1; 130 po Ctrl-C). Nieznana
  komenda to `not_found` (kod 3) z podpowiedzią, błąd składni to `validation_error` (2).
- `hydrolog mcp [--allow-dir DIR]... [--lang pl|en]` uruchamia serwer MCP (dodatek
  `hydrolog[mcp]`); `python -m hydrolog.cli` działa jak komenda `hydrolog`.

#### Pozostałe zmiany
- `InvalidParameterError` jest teraz także `ValueError` (kod z `except ValueError` nadal go łapie); wszystkie wyjątki Hydrologa mają `code`, `details` i `hint`.
- `WatershedParameters.from_dict()` toleruje dodatkowy klucz `schema` (np. `"hydrolog-catchment/1"`); `calculate_tc()` dla nieznanej metody lub brakującego pola wymaganego przez metodę zgłasza `InvalidParameterError` (`details.reason` = `choice` / `missing_field`, `details.missing` wymienia wszystkie braki), dawniej mieszanka `ValueError` i `InvalidParameterError`.
- `ClarkIUH.to_unit_hydrograph()`: `duration_min` i `timestep_min` muszą być dodatnie i skończone (`InvalidParameterError`).
- `HydrologyReportGenerator.generate()` ma nowe argumenty opcjonalne `ia_coefficient` i `tc_params`.
- `morphometry watershed`: gdy plik zlewni podaje `mean_slope_m_per_m` lub `channel_slope_m_per_m`, wynik (spadki z deniwelacji, jak dotąd) ma uwagę `slopes_from_relief` z obiema wartościami, policzoną i podaną; dawniej `tc watershed` liczył z podanym spadkiem koryta 0,02, a `morphometry watershed` dla tego samego pliku podawał 0,037 bez wyjaśnienia.
- Przewodnik dla agentów (`AGENTS.md`) opisuje wynik funkcji operacji dokładnie: obiekt wynikowy z `to_dict()`/`to_json()` albo `OperationOutput(result, notices, files)`; docstring `hydrolog.catalog` i projekt 1.0.0 wskazują pakiet `hydrolog/operations/<grupa>.py` (dawniej `operations.py`).
- `LowFlowAnalysis.annual_minima()`, `fit_fisher_tippett()`, `empirical_frequency()` i `empirical_non_exceedance()` używają tylko kompletnych lat hydrologicznych: pominięte lata zgłasza `UserWarning`, a seria bez kompletnego roku to `CalculationError` (dawniej minimum z każdego roku obecnego w datach).
- `RatingCurve.fit(h0_initial=None)` i `hydrometrics_rating_curve(h0_initial=None)`: domyślny punkt startowy H₀ dobierany z danych (dawniej 0.0); opcja `h0_initial` nie ma już wartości domyślnej w katalogu komend.

### Removed

- `hydrolog.cli.commands` (stare podkomendy `tc`, `cn`, `scs`, `uh` z opcjami `--length`,
  `--area`, `--tc`, `--csv`, ...). Bez aliasów starych nazw: np. `hydrolog scs --cn 72
  --precipitation 50` to teraz `hydrolog scs effective --cn 72 --precipitation-mm 50`;
  eksport CSV zastępuje `--json` (pełna koperta wyniku).
- Dodatki `spatial` (i zależność od Kartografa) z `pyproject.toml`.

### Fixed

- **Rozkład Fishera–Tippetta dla minimów (`LowFlowAnalysis.fit_fisher_tippett()`).** Wersje < 1.0.0 dopasowywały do minimów rocznych rozkład *maksimów* (GEV) i czytały jego kwantyl w punkcie p = 1/T; to rozkład zwierciadlany, który poprawnie opisuje środek próby, ale nie lewy ogon rozkładu wartości najmniejszych. Teraz GEV dopasowuje się do *zanegowanych* minimów (`min(x) = −max(−x)`), a kwantyl to `−genextreme.isf(p, c, loc=−loc, scale=scale)`. Syntetyczna próba 1000 minimów rocznych z rozkładu Gumbela dla minimów (loc = 50, scale = 8), T = 100 lat: **−3821 → 13,26** (wartość teoretyczna 13,20); rozkład Weibulla (k = 2, loc = 1, scale = 5): T = 100 lat 1,24 → 1,51 (teoria 1,50), T = 1000 lat 0,33 → 1,18 (teoria 1,16). Raportowane `shape` to `c` z `scipy.stats.genextreme`, `loc` odnosi się do minimów. Szczegóły: `docs/COMPUTATION_PATHS.md` sekcja 3.6.
- **Clark UH dla czasu trwania D niebędącego wielokrotnością kroku (`ClarkIUH.to_unit_hydrograph()`).** Krzywa S była przesuwana o `round(D/dt)` kroków, ale dzielona przez D, więc objętość hydrogramu wynosiła `round(D/dt)·dt/D` mm: dla D = 1,5·dt **1,333 → 1,000 mm**, dla D = 2,5·dt 0,8 → 1,000 mm; dla D < dt/2 funkcja zgłaszała `ValueError` (`s_curve[:-0]`). Teraz opóźniona krzywa S jest interpolowana liniowo, objętość wynosi 1 mm dla dowolnego D > 0, a dla całkowitych wielokrotności kroku wynik jest bez zmian. Wynik jest ciągły względem D (dawniej skok co pół kroku).
- `WatershedParameters.calculate_tc("giandotti")`: `elevation_mean_m == 0` (średnia wysokość 0 m n.p.m.) była traktowana jak brak wartości i zastępowana środkiem przedziału wysokości.
- **Raport obliczeniowy (`HydrologyReportGenerator`).** Sekcja hydrogramu jednostkowego dokumentuje teraz hydrogram użyty w obliczeniach (`result.unit_hydrograph_result`: model, parametry, rzędne, czas do szczytu), a nie szkic z założonych wartości (dawniej np. Nash n = 3, K = 30 min, trójkątne rzędne); współczynnik λ w Ia = λ·S pochodzi z obliczeń (dawniej stałe 0,2); sekcja czasu koncentracji używa wejść wzoru tak jak `calculate_tc()` (dawniej NRCS brał nieistniejący klucz `mean_slope_percent`, Giandotti liczył różnicę max − min zamiast średnia − min); wzory Kerby i Kerby-Kirpich pokazują spadek po korekcie małych spadków, a czas koryta Kirpicha jest podany w godzinach i minutach; wzory Snydera działają bez L i Lc; liczba kroków hydrogramu w sekcji splotu jest rzeczywista.
- `calculate_monthly_statistics()`: miesiąc z jedną wartością miał przedział ufności `[średnia, średnia]` (twierdzenie o dokładnie znanej średniej) i ostrzeżenia NumPy; teraz odchylenie standardowe, współczynnik zmienności, skośność i przedział ufności takiego miesiąca to `NaN` (`null` w JSON). Miesiąc bez żadnej wartości zgłasza `InvalidParameterError` (`details.missing_months`), dawniej błąd NumPy.
- `StreamNetwork`: metoda Shreve'a kończyła się `KeyError` w statystykach sieci (rzędy Shreve'a nie są ciągłe, a wskaźniki bifurkacji i długości zakładały ciągłe); `classify()` zapętlał się nieskończenie dla sieci z cyklem lub z nieistniejącym `upstream_id` przy źródle, a bez żadnego źródła po cichu zostawiał wszystkie rzędy równe 0 - teraz `InvalidParameterError` (`details.reason` = `cycle` / `unknown_upstream`), a segmenty pozostają bez zmian.
- `RatingCurve`: `fit(h0_initial=...)` z wartością nieskończoną, `NaN` lub nie niższą od najniższego stanu kończyło się gołym `ValueError` ze SciPy (punkt startowy poza ograniczeniami) - teraz `InvalidParameterError` (`details.option` = `h0_initial`, `details.maximum` = najniższy stan, wskazówka w `hint`); pomiary z `NaN` lub nieskończonością są odrzucane przy tworzeniu obiektu. Brak zbieżności i przepełnienie prawa potęgowego to `RatingCurveFitError` (kod `calculation_error`, także `InvalidParameterError`, więc `except` napisane dla wersji < 1.0.0 nadal działa), z przyczyną w `__cause__`.
- **`cn` obok zlewni w `hydrograph generate` i `report generate` (czas koncentracji NRCS).** `cn` podane obok zlewni nadpisywało CN tylko w SCS-CN, a `tc_method=nrcs` liczyło retencję S równania opóźnienia (TR-55, rozdz. 3; NEH-630, rozdz. 15) z CN pliku; zlewnia bez `cn` z `cn` i `nrcs` kończyła się błędem „missing: cn", wbrew opisowi opcji. Teraz `cn` jest CN całego obliczenia (zlewnia dostaje je przed czasem koncentracji), więc `tc_parameters`, `HydrographRun.watershed` i raport są spójne (raport podawał „S = 98,78 mm (dla CN = 72)" w sekcji czasu koncentracji obok „CN = 85" w sekcji SCS-CN). Zlewnia z CN 60 w pliku (L = 12 km, S = 0,025), `cn` = 85, opad beta 50 mm/120 min: tc **657,7 → 322,1 min**, Qmax **27,64 → 55,62 m³/s**, czas do szczytu 440 → 240 min.
- **Hydrogram jednostkowy Snydera w `HydrographGenerator`.** Splot dyskretny traktuje hydrogram jednostkowy jak odpowiedź na 1 mm opadu efektywnego w jednym kroku, a generator budował hydrogram dla standardowego czasu trwania tD = tL/5,5 bez względu na krok. Snyder (1938; USACE-HEC, HEC-HMS Technical Reference Manual, „Snyder Unit Hydrograph Model"; Chow, Maidment, Mays 1988) podaje poprawkę na inny czas trwania D: tLR = tL + 0,25(D − tD), tpR = tLR + D/2, qpR = qp·tL/tLR; klasa `SnyderUH` ją miała (`generate(duration_min=...)`), generator jej nie używał. Teraz dla modelu `snyder` woła `generate(timestep_min=dt, duration_min=dt)`: `uh_time_to_peak_min` wyniku to tpR, a raport dokumentuje Δt równe krokowi (dawniej „Δt = 59,0 min" przy hietogramie 5-minutowym). Dla kroku krótszego od tD szczyt hydrogramu jednostkowego jest wyższy i wcześniejszy niż dla tD, dla dłuższego niższy i późniejszy. Zlewnia 45 km², L = 12 km, Lc = 6 km, CN 72, opad beta 50 mm/120 min, krok 5 min: hydrogram jednostkowy tp **354,2 → 313,7 min**, qp **1,379 → 1,542 m³/s/mm**; hydrogram Qmax **9,76 → 10,90 m³/s (+11,8%)**, czas do szczytu 405 → 365 min.
- **`WatershedParameters.calculate_tc()` dla FAA i Kerby'ego: czas spływu powierzchniowego, nie długość koryta.** FAA (AC 150/5320-5A, 1966; AC 150/5320-5D, 2013) i Kerby (1959) to wzory na czas spływu powierzchniowego; Kerby wyprowadził swój dla dróg do 366 m (1200 ft; Roussel i in. 2005, TxDOT Report 0-4696-2; TxDOT Hydraulic Design Manual, rozdz. 4, sekcja 11), a biblioteka ostrzega dla FAA poza 0,015–3 km. Metoda podstawiała jednak `channel_length_km` i spadek koryta (nawet gdy zlewnia miała `overland_length_km` i `overland_slope_m_per_m`), więc każda zlewnia z korytem dostawała wynik spoza zakresu wzoru, a raport podpisywał 10 km koryta jako „długość spływu powierzchniowego". Teraz FAA i Kerby biorą `overland_length_km` i `overland_slope_m_per_m` i wymagają ich (patrz BREAKING; dla zlewni z korytem służy `kerby_kirpich`). Zlewnia z korytem 10 km (S = 0,02), spływem powierzchniowym 0,2 km (S = 0,01), C = 0,5, N = 0,4: FAA **155,3 → 27,7 min** (ostrzeżenie `length_km=10.0` znika), Kerby **173,2 → 32,8 min** (dwa ostrzeżenia znikają).
- **`WatershedParameters.calculate_tc("nrcs")`: średni spadek zlewni przed spadkiem koryta.** Równanie opóźnienia NRCS (TR-55, rozdz. 3; NEH-630, rozdz. 15) używa średniego spadku terenu zlewni Y, a nie spadku drogi spływu; metoda brała `channel_slope_m_per_m` przed `mean_slope_m_per_m`. Teraz kolejność to `mean_slope_m_per_m`, `channel_slope_m_per_m`, relief/(L·1000) (Kirpich bez zmian: koryto, zlewnia, relief). Ta sama zlewnia (koryto S = 2,0%, spadek terenu 2,5%): **463,9 → 414,9 min (−10,6%)**.
- **Zapis plików przez równoległe wywołania (serwer MCP).** `report generate` i `soil hsg` zapisywały plik przez nazwę tymczasową zależną tylko od PID, a serwer MCP wykonuje wywołania w wątkach jednego procesu: dwa równoczesne wywołania z tym samym `output`/`output_path` dzieliły plik tymczasowy, więc drugie kończyło się `OutputError` (`io_error`, `[Errno 2] No such file or directory: '.<plik>.<pid>.tmp'`) mimo poprawnych danych. Wszystkie trzy zapisy (`report generate`, `soil hsg`, `commands guide --path`) używają teraz wspólnego `hydrolog._atomic.atomic_output` z unikalną (losową) nazwą pliku tymczasowego w katalogu docelowym. Cztery wątki piszące ten sam plik, 40 prób (160 wywołań): `report generate` **44 błędy → 0**, `soil hsg` **28 → 0**, `commands guide` 0 → 0.
- **Ekstrema roczne tylko z kompletnych lat hydrologicznych (`stats flood-frequency`, `stats low-flow`, `LowFlowAnalysis.annual_minima()`).** Maksima i minima brano z każdego roku hydrologicznego obecnego w datach, także z niepełnych, i nic o tym nie mówiono: typowy eksport z lat kalendarzowych (1991-01-01 … 2020-12-31) dawał 31 „lat”, w tym pierwszy bez listopada i grudnia oraz ostatni (2021) z samymi listopadem i grudniem 2020, którego „maksimum” i „minimum” to poziom bazowy, a nie ekstremum roku (KZGW 2017 i WMO nr 1029, 2009 biorą do analizy pełne lata obserwacji). Teraz rok (1 XI – 31 X) wchodzi do próby tylko wtedy, gdy szereg ma wartość dla każdego dnia (365 dni, 366 w roku z 29 lutego; brak daty albo `NaN` wyklucza rok), a pominięte lata wymienia notice `incomplete_years` (z liczbą dni z danymi: `1991 (304 of 365 days), 2021 (61 of 365 days)`) i pole wyniku `incomplete_years`; seria bez 3 kompletnych lat to `calculation_error` z `details.incomplete_years`. Syntetyczna seria kalendarzowa 1991–2020 (wezbranie 15 III i niżówka 15 IX każdego roku): **31 → 29 lat** (1992–2020); „maksimum” 2021 równe **5,0** (mediana pełnych lat 13,0) i „minimum” 5,0 (mediana 2,2) nie wchodzą już do próby; GEV dla T = 100 lat **16,08 → 16,35**, Fisher–Tippett dla T = 100 lat **2,002 → 1,968**. Dzień bez wartości kosztuje cały rok: przy lukach uzupełnij dane albo podaj maksima roczne wprost (`stats flood-frequency` bez dat). `stats characteristic`, `stats daily` i `stats monthly` bez zmian.
- **`stats low-flow`: częstość empiryczna w konwencji nieprzekroczenia.** Blok `empirical` był wynikiem `LowFlowAnalysis.empirical_frequency()`: wartości malejąco z prawdopodobieństwem *przewyższenia*, więc najgłębsza niżówka próbki dostawała okres powtarzalności przewyższenia (3 lata z `tests/fixtures/daily_flows_3y.csv`: minimum 1,66 → P = 0,75, **T = 1,33**), podczas gdy blok `fisher_tippett` (i WMO nr 1029; Tallaksen i van Lanen, 2004) liczy T z prawdopodobieństwa nieprzekroczenia. Teraz `empirical` to `LowFlowEmpiricalFrequency` (`LowFlowAnalysis.empirical_non_exceedance()`): `values_ascending` (rosnąco), `non_exceedance_probabilities` F = m/(n+1) i `return_periods` T = 1/F; to samo minimum 1,66 ma F = 0,25 i **T = 4** (najgłębsza niżówka n lat ma T = n + 1), więc punkty empiryczne można zestawiać z `fisher_tippett.return_periods` bez przeliczeń. `LowFlowAnalysis.empirical_frequency()` zostaje bez zmian (konwencja przewyższenia, opisana w docstringu), a `plot_non_exceedance_curve()` przyjmuje obie postacie.
- **`RatingCurve.fit()` i `hydrometrics rating-curve`: punkt startowy H₀ z danych.** Stały domyślny `h0_initial = 0.0` musiał leżeć poniżej najniższego stanu, więc każdy wodowskaz z odczytem ≤ 0 (stany poniżej zera wodowskazu, np. −10 cm, są normalne) kończył się `validation_error` (kod wyjścia 2): `hydrolog hydrometrics rating-curve --water-levels=-10,5,20,40,80,120 --discharges 0.5,1.2,2.5,4.8,10.1,17.3` → „h0_initial must be a finite number below the lowest water level (-10), got 0.0”. Teraz domyślne `h0_initial=None` wybiera start `min(H) − max(1, 0,1·(max(H) − min(H)))` (w jednostce stanów), więc dopasowanie działa dla dowolnych stanów: a = 0,004917, b = 1,640, H₀ = −25,17 (R² = 0,9998), tak samo jak dla każdego jawnego startu poniżej najniższego stanu. Jawnie podana wartość jest walidowana jak dotąd (skończona i niższa niż najniższy stan). Na 60 syntetycznych krzywych (stany w cm i m, dodatnie i ujemne, szum 1–8 %) starty od 0,1 do 1 rozstępu poniżej najniższego stanu zawsze dawały najlepsze rozwiązanie najmniejszych kwadratów.

### Testing

- Zbieranych jest 3297 testów (824 w v0.7.0): katalog komend (parytet CLI/Python dla każdego przykładu), parser i render CLI, serwer MCP (klient-serwer w procesie), serializacja, `hydrolog.soil` (porty testów Kartografa; testy rastrów pomijane bez `rasterio`), warstwa operacji, przewodniki dla agentów (zgodność bajtów), współbieżny zapis plików (`hydrolog._atomic`), regresje poprawek z sekcji „Fixed" (z liczbami sprzed i po poprawce).

---

## [0.7.0] - 2026-03-26

### Added

#### `hydrolog.statistics` - Statystyka hydrologiczna
Nowy moduł do analizy statystycznej szeregów hydrologicznych.

**Wartości charakterystyczne (`characteristic.py`):**
- `CharacteristicValues` — dataclass z wartościami NNQ, SNQ, SSQ, SWQ, WWQ
- `DailyStatistics` — statystyki dzienne (percentyle, kwantyle)
- `MonthlyStatistics` — statystyki miesięczne
- `calculate_characteristic_values()` — wyznaczanie wartości charakterystycznych (system polski)
- `calculate_daily_statistics()` — statystyki dla szeregów dobowych
- `calculate_monthly_statistics()` — statystyki dla szeregów miesięcznych

**Analiza częstości przepływów maksymalnych (`high_flows.py`):**
- `FrequencyAnalysisResult` — wyniki dopasowania rozkładu (parametry, AIC, testy zgodności)
- `FloodFrequencyAnalysis` — analiza częstości z 4 rozkładami:
  - LogNormal (dwuparametrowy)
  - GEV (Generalized Extreme Value)
  - Pearson III (Gamma z przesunięciem)
  - Weibull (wartości ekstremalne min)
- Testy zgodności: Kołmogorowa-Smirnowa, Andersona-Darlinga
- Kryterium informacyjne Akaike'a (AIC) do wyboru najlepszego rozkładu

**Analiza częstości przepływów minimalnych (`low_flows.py`):**
- `LowFlowFrequencyResult` — wyniki dopasowania Fisher-Tippett
- `LowFlowSequence` — sekwencja niżówkowa (czas trwania, deficyt, intensywność)
- `LowFlowAnalysisResult` — kompletne wyniki analizy niżówkowej
- `LowFlowAnalysis` — analiza niżówek:
  - Dopasowanie rozkładu Fisher-Tippett dla przepływów minimalnych
  - Detekcja sekwencji niżówkowych metodą progową

**Test trendu (`stationarity.py`):**
- `MannKendallResult` — wynik testu (statystyka S, Z, p-value, kierunek trendu)
- `mann_kendall_test()` — nieparametryczny test Manna-Kendalla (KZGW 2017)

**Typy wspólne (`_types.py`, `_hydrological_year.py`):**
- Typy danych dla szeregów hydrologicznych
- Narzędzia do obsługi roku hydrologicznego (1.XI – 31.X)

#### `hydrolog.hydrometrics` - Hydrometria
Nowy moduł do analiz hydrometrycznych.

**Krzywa natężenia przepływu (`rating_curve.py`):**
- `RatingCurveResult` — wyniki dopasowania krzywej (parametry a, H₀, b, R², RMSE)
- `WaterLevelZones` — strefy wodowskazowe metodą Rybczyńskiego (NTW/STW/WTW)
- `FrequencyDistributionResult` — rozkład częstości i czasu trwania stanów wody
- `RatingCurve` — krzywa natężenia Q = a × (H − H₀)^b z dopasowaniem metodą NLS
- `WaterLevelFrequency` — analiza częstości i czasu trwania stanów wody + strefy Rybczyńskiego

#### `hydrolog.visualization.statistics` — 10 funkcji wizualizacji statystycznej
- `plot_frequency_curve()` — krzywa częstości z przedziałami ufności
- `plot_frequency_comparison()` — porównanie rozkładów na jednym wykresie
- `plot_non_exceedance_curve()` — krzywa czasu trwania przepływów (FDC)
- `plot_daily_characteristics()` — wartości charakterystyczne NNQ–WWQ
- `plot_monthly_statistics()` — statystyki miesięczne (box plot)
- `plot_annual_hydrographs()` — hydrogramy roczne
- `plot_flow_histogram()` — histogram rozkładu przepływów
- `plot_low_flow_sequences()` — sekwencje niżówkowe na tle szeregu
- `plot_rating_curve()` — krzywa natężenia z danymi pomiarowymi
- `plot_water_level_frequency()` — częstość i czas trwania stanów wody

### Changed
- SciPy przeniesiona z zależności opcjonalnej do wymaganej (core dependency).
  Używana wcześniej opcjonalnie przez `runoff.nash_iuh`; od v0.7.0 wymagana
  przez moduł `statistics` (rozkłady GEV, Pearson III, Fisher-Tippett).

### Testing
- 70 nowych testów jednostkowych (754 → 824):
  - `test_characteristic.py` — wartości charakterystyczne, statystyki dobowe/miesięczne
  - `test_high_flows.py` — analiza częstości przepływów maksymalnych
  - `test_low_flows.py` — Fisher-Tippett, detekcja niżówek
  - `test_stationarity.py` — test Manna-Kendalla
  - `test_rating_curve.py` — krzywa natężenia, strefy Rybczyńskiego
  - `test_visualization_statistics.py` — 10 funkcji wizualizacji

---

## [0.6.4] - 2026-03-25

### Added

#### `hydrolog.morphometry.WatershedParameters` - Extended Fields
- 8 new Optional fields for full integration with all tc methods and UH models:
  - `runoff_coeff` — FAA tc method (Rational method C, 0-1)
  - `retardance` — Kerby/Kerby-Kirpich tc (roughness coefficient, 0.02-0.80)
  - `overland_length_km` — Kerby-Kirpich overland segment length [km]
  - `overland_slope_m_per_m` — Kerby-Kirpich overland slope [m/m]
  - `Lc_km` — Length to watershed centroid along main channel [km] (Nash Lutz, Snyder)
  - `manning_n` — Manning's roughness coefficient (Nash Lutz)
  - `urban_pct` — Urbanized area percentage [%] (Nash Lutz)
  - `forest_pct` — Forested area percentage [%] (Nash Lutz)
- `calculate_tc()` extended from 3 to 6 methods: added `"faa"`, `"kerby"`, `"kerby_kirpich"`
- `from_dict()`/`to_dict()` updated for all new fields (backward compatible)

#### `hydrolog.reports` - FAA/Kerby/Kerby-Kirpich Formula Rendering
- `FormulaRenderer.faa_tc()` — LaTeX rendering: `tc = 22.213 × (1.1 - C) × L^{0.5} / S^{1/3}`
- `FormulaRenderer.kerby_tc()` — LaTeX rendering: `tc = 36.37 × (L × N)^{0.467} × S^{-0.2335}`
- `FormulaRenderer.kerby_kirpich_tc()` — LaTeX composite: `tc = t_{ov} + t_{ch}`
- `generate_tc_section()` extended with full formula rendering for 3 new tc methods
- Polish method descriptions added to `templates.py` (TC_METHODS, FORMULA_EXPLANATIONS, REFERENCES)

#### `hydrolog.reports.generator` - Hietogram Type Validation
- `generate()` emits `UserWarning` if `config.hietogram_type` is not in valid set

#### `hydrolog.runoff.generator` - UH Ordinates Exposure
- `HydrographGeneratorResult.unit_hydrograph_result` — new Optional field storing computed UH result
  - Populated automatically by `HydrographGenerator.generate()`
  - Stores concrete UH type (UnitHydrographResult, NashUHResult, ClarkUHResult, SnyderUHResult)
  - Backward compatible (defaults to None)

### Changed
- `hydrolog.cli.commands.uh` — Snyder `--ct` default changed from 2.0 to **1.5** (aligned with Python class default; SI typical range 1.35-1.65)
- `hydrolog.runoff.snyder_uh` — `generate()` docstring documents why default timestep (30 min) differs from other models (5 min)
- `hydrolog.runoff.generator` — `generate()` docstring documents explicit timestep passing to all UH models

### Fixed
- `hydrolog.reports.sections.scs_cn` — added None guards for `retention_mm` and `initial_abstraction_mm` (prevents crash when data missing)
- `hydrolog.visualization.water_balance` — `F = max(0.0, P - Pe - Ia)` prevents negative continuing abstraction
- `hydrolog.precipitation.hietogram` — `HietogramResult.intensities_mm` docstring clarified: contains incremental depths [mm], not intensity rates [mm/h]
- `hydrolog.precipitation.interpolation` — `Station.x`/`y` docstring clarified: must use consistent coordinate system; unit affects IDW distance calculations

### Testing
- 45 new tests (754 total, all passing):
  - 30 tests for WatershedParameters extension (fields, validation, tc methods, serialization)
  - 10 tests for reports (FormulaRenderer, tc sections, SCS-CN guards, hietogram validation)
  - 6 tests for UH ordinates exposure in HydrographGeneratorResult (all 4 models)
  - 2 tests for CLI Snyder Ct default alignment (integrated from worktree)

### Documentation
- Comprehensive audit of all 8 docs files against codebase v0.6.3
- Fixed outdated API examples: SCSCN class-based, BetaHietogram.generate()
- Corrected SCS formulas: Pe = (P-Ia)²/(P-Ia+S), tb = 5.0×tp
- Updated PRD with +7 user stories for missing modules (visualization, reports, Nash/Clark/Snyder)
- DEVELOPMENT_STANDARDS: added TYPE_CHECKING, dataclass, warnings patterns
- Moved NASH_AUDIT_REPORT.md to tmp/

---

## [0.6.3] - 2026-03-23

### Added

#### `hydrolog.time.concentration` - FAA Method
- `ConcentrationTime.faa()` - FAA (Federal Aviation Agency) method for overland/sheet flow tc calculation
  - Formula: `tc = 22.213 × (1.1 - C) × L^0.5 / S^(1/3)`
  - Parameters: C (rational method runoff coefficient), L (overland flow length in km), S (slope in m/m)
  - Source: FAA Advisory Circular AC 150/5320-5D (2013)
  - CLI support: `hydrolog tc faa --length 0.15 --slope 0.02 --runoff-coeff 0.6`

#### `hydrolog.time.concentration` - Kerby Method
- `ConcentrationTime.kerby()` - Kerby (1959) method for overland/sheet flow tc calculation
  - Formula: `tc = 36.37 × (L × N)^0.467 × S^(-0.2335)`
  - Parameters: L (overland flow length in km), N (Kerby retardance roughness coefficient), S (slope in m/m)
  - Low-slope adjustment: for S < 0.002, S_adj = S + 0.0005 (Cleveland et al. 2012)
  - Source: Kerby, W.S. (1959). "Time of concentration for overland flow." Civil Engineering, 29(3), 174
  - CLI support: `hydrolog tc kerby --length 0.10 --slope 0.008 --retardance 0.40`

#### `hydrolog.time.concentration` - Kerby-Kirpich Composite Method
- `ConcentrationTime.kerby_kirpich()` - Kerby-Kirpich composite method for time of concentration
  - Combines Kerby (overland flow) and Kirpich (channel flow) for composite tc estimation
  - Formula: `tc = t_overland(Kerby) + t_channel(Kirpich)`
    - Kerby: `tc_ov = 36.37 × (L_ov × N)^0.467 × S_ov^(-0.2335)`
    - Kirpich: `tc_ch = 3.981 × L_ch^0.77 × S_ch^(-0.385)`
  - Low-slope adjustment (Cleveland et al. 2012): for S < 0.002, S_adj = S + 0.0005 (applied to both segments)
  - Source: Roussel et al. (2005). TxDOT Report 0-4696-2
  - CLI support: `hydrolog tc kerby-kirpich --ov-length 0.25 --ov-slope 0.008 --retardance 0.40 --ch-length 5.0 --ch-slope 0.005`

### Changed
- `refactor(time): harmonize API consistency across all tc methods` — rename `_SCS_LAG_*` to `_NRCS_*`, fix CLI formatting, add 28 parity tests (90 → 118)

### Fixed
- `fix(types): resolve all 88 mypy errors across the codebase` — float() casts, type narrowing, TYPE_CHECKING imports, assert guards
- `docs: fix stale content and cross-document inconsistencies` — CHANGELOG, SCOPE, PROGRESS, COMPUTATION_PATHS, PRD, DEV_STANDARDS, IMPL_PROMPT

---

## [0.6.2] - 2026-03-22

### Added

#### `hydrolog.runoff.nash_iuh` - Lutz Calculation Results
- `LutzCalculationResult` - new dataclass storing all intermediate calculation steps
  - Input parameters: L_km, Lc_km, slope, manning_n, urban_pct, forest_pct
  - Intermediate values: P1, geometric_factor, urban_factor, forest_factor
  - Output values: tp_hours, up_per_hour, f_N_target, n, k_hours, k_min
  - Computed properties: tp_min, lag_min, lag_hours
- `NashIUH.lutz_params` - stores LutzCalculationResult when created via `from_lutz()`

#### `hydrolog.reports` - Enhanced Report Generation
- `figures_dir` parameter in `HydrologyReportGenerator.generate()`
  - Automatically embeds PNG figures in report as Markdown images
  - Expected files: hietogram_beta.png, hydrogram_jednostkowy_nash.png, rainfall_runoff.png, bilans_wodny.png, generator_dashboard.png
- Automatic Lutz method documentation in Nash UH section
  - Full calculation steps with LaTeX formulas when `lutz_params` provided
  - All intermediate values automatically substituted
  - Literature references (Lutz 1984, KZGW 2017)

#### Raporty — pełne wzory obliczeniowe dla wszystkich modeli UH
- **Nash IUH** — 3 metody estymacji parametrów w raportach:
  - `from_tc` — formuły tlag = λ·tc, K = tlag/n z podstawionymi wartościami
  - `from_lutz` — 6 kroków metody Lutza (P1, tp, up, f(N), N, K) z podstawieniami
  - `from_urban_regression` — 3 kroki regresji (tL, k, N) z tabelą wejść i referencją
- **Clark IUH** — rozbudowana sekcja raportu:
  - Estymacja R z metody R/Tc z podstawieniami
  - Współczynnik routingu C1 = Δt/(2R+Δt) z wartościami
  - Histogram czas-powierzchnia (dwuczęściowy HEC-HMS) z Tc
  - Czas opóźnienia tlag ≈ Tc/2 + R
- **Snyder UH** — pełne wzory z podstawieniami numerycznymi:
  - tL, tD = tL/5.5, tp, qp, tb — wszystkie z wartościami
  - W50, W75 — szerokości hydrogramu z poprawnymi stałymi metrycznymi
  - Korekta dla niestandardowego czasu trwania (tLR, tpR, qpR)
- **6 nowych metod** `FormulaRenderer`:
  - `nash_from_tc_formulas()`, `nash_from_lutz_formulas()`,
    `nash_urban_regression_formulas()`
  - `clark_from_tc_r_ratio()`, `clark_routing_coefficient()`,
    `clark_time_area_substituted()`
- Detekcja `estimation_method` w `model_params` we wszystkich sekcjach UH

### Changed
- Terminology: "ordynaty" → "rzędne" throughout codebase (Polish orthography)
  - Updated: templates.py, formatters.py, convolution.py, visualization modules
- `hydrolog.runoff.nash_iuh` module docstring updated with literature references:
  - Nash (1957), Lutz (1984), Rosso (1984), KZGW (2017)
- `hydrolog.time.concentration` module enhanced with literature references:
  - `kirpich()`: Added Ponce (2014), CivilWeb (2023); clarified original units (minutes, slope in m/m)
  - `nrcs()`: Added TR-55, HEC-HMS references; clarified tc vs tl vs tp distinction
  - `giandotti()`: Added Grimaldi (2012), Michailidi (2018); verified original output in hours
- **BREAKING:** `ConcentrationTime.scs_lag()` renamed to `ConcentrationTime.nrcs()`
  - Method calculates tc directly using the NRCS equation
  - Formula simplified: `tc = 0.01416 × L^0.8 × (S+25.4)^0.7 × Y^-0.5`
  - All references in codebase updated (CLI, reports, morphometry, tests)
- `hydrolog.visualization`: Temporarily disabled `plot_generator_result()` export (to be removed)

### Deprecated

#### `hydrolog.runoff.nash_iuh.NashIUH.from_tc()`
- **Will be removed in version 1.0.0**
- This method uses the SCS relationship `lag = 0.6 × Tc` which was developed for
  the SCS Unit Hydrograph, NOT for the Nash model
- The Nash model lag time (`n × K`) is a mathematical result of the cascade,
  not an input parameter
- **Recommended alternatives:**
  - Use `from_lutz()` for ungauged watersheds (Lutz 1984, KZGW 2017)
  - Provide `n` and `K` directly to the constructor

### Fixed

#### Korekty wzorów metrycznych
- **Snyder W50/W75** — poprawione stałe metryczne:
  - W50: 5.87 → **0.1783** (imperialna 770 / conv^1.08, conv ≈ 2323)
  - W75: 3.35 → **0.1019** (imperialna 440 / conv^1.08)
  - Poprzednie wartości dawały wyniki zawyżone ~33×
- **Clark histogram czas-powierzchnia** — zmiana na standard HEC-HMS:
  - Było: `1.414·(t/Tc)^0.5 - 0.414·(t/Tc)^1.5` (osobliwość przy t=0)
  - Jest: dwuczęściowy z wykładnikiem 1.5 (symetryczny, centroid = Tc/2)
- **SCS Lag docstring** — stała 7182 → **7069** (kod był poprawny, błąd w dokumentacji)

### Documentation
- Added `docs/NASH_AUDIT_REPORT.md` - architectural audit of Nash IUH module
  - Literature verification (10 sources)
  - Analysis of `from_tc()` vs `from_lutz()` methods
  - Recommendations for module architecture
- Added `docs/COMPUTATION_PATHS.md` - computation paths for all UH models
  - Compatibility matrix: model × parameter estimation method
  - ASCII flow diagrams for each model (SCS, Nash, Clark, Snyder)
  - Literature verification for each computation path
  - Code examples for correct usage
  - "Common errors and how to avoid them" section
  - 10 literature references
- Dokumentacja `SCSCN` — dodano referencję Woodward et al. (2003) dla λ=0.05
  z ostrzeżeniem o konieczności rekalibracji CN
- Dokumentacja `from_urban_regression()` — pełna historia konwersji
  imperial→metryczny z referencjami (Sarma 1969, Rao 1972, Kołodziejczyk 2017)
- ~~Nowy plik `docs/NASH_URBAN_REGRESSION_DERIVATION.md`~~ — dowód matematyczny
  konwersji stałych 0.831→1.28 i 0.569→0.56 z weryfikacją numeryczną (plik usunięty)

### Testing
- 5 nowych testów Clark IUH (histogram: symetria, brak osobliwości, centroid)
- Aktualizacja testów referencyjnych Nash urban regression
- Total: 626 testów (wszystkie przechodzą)

---

## [0.6.1] - 2026-03-20

### Added

#### `hydrolog.runoff.nash_iuh` - Urban Regression Method
- `NashIUH.from_urban_regression()` - parameter estimation for urbanized catchments
  - Estimates Nash model parameters (N, k) from catchment area, effective
    precipitation, rainfall duration, and urbanization index
  - Power-law regression equations: tL = 1.28·A^0.46·(1+U)^(-1.66)·H^(-0.27)·D^0.37,
    k = 0.56·A^0.39·(1+U)^(-0.62)·H^(-0.11)·D^0.22
  - Verified against reference spreadsheet (Obliczenia.xlsx)
  - References: Rao, Delleur, Sarma (1972), ASCE J. Hydraulics Div. 98(HY7)

### Testing
- 11 new tests for urban regression method (including reference value verification)
- Total: 621 tests (all passing)

---

## [0.6.0] - 2026-01-21

### Added

#### `hydrolog.reports` - Report Generation Module
New module for generating comprehensive hydrological calculation reports in Markdown format.

**Main classes:**
- `HydrologyReportGenerator` - main class for report generation
  - `generate()` - create report from HydrographGeneratorResult
  - Supports all UH models (SCS, Nash, Clark, Snyder)
  - Outputs complete calculation procedure with formulas
- `ReportConfig` - configuration dataclass
  - `tc_method` - concentration time method (kirpich, nrcs, giandotti)
  - `uh_model` - unit hydrograph model (scs, nash, clark, snyder)
  - `include_formulas` - include LaTeX formulas (default: True)
  - `include_tables` - include data tables (default: True)
  - `max_table_rows` - maximum rows before abbreviation (default: 50)

**Formatters (`formatters.py`):**
- `FormulaRenderer` - render LaTeX formulas with substituted values
  - SCS-CN formulas: retention, initial abstraction, effective precipitation
  - Time of concentration: Kirpich, SCS Lag, Giandotti
  - Unit hydrograph: SCS, Nash IUH, Clark IUH, Snyder UH
  - Convolution and water balance formulas
- `TableGenerator` - generate Markdown tables
  - Parameters tables with alignment
  - Time series tables with automatic abbreviation
  - Water balance summary tables
  - Hydrograph results tables

**Report sections (`sections/`):**
- `generate_watershed_section()` - watershed parameters and shape indicators
- `generate_tc_section()` - concentration time calculations
- `generate_hietogram_section()` - precipitation temporal distribution
- `generate_scs_cn_section()` - SCS-CN effective precipitation
- `generate_uh_section()` - unit hydrograph (all models)
- `generate_convolution_section()` - discrete convolution
- `generate_water_balance_section()` - water balance summary

**Templates (`templates.py`):**
- Polish section headers and labels
- Method descriptions (Kirpich, SCS, Nash, Clark, Snyder)
- AMC condition descriptions
- Literature references
- Glossary of hydrological terms

**Report structure:**
1. Watershed parameters (geometry, terrain, shape indicators)
2. Time of concentration (formula with substitutions)
3. Hietogram (parameters, temporal distribution table)
4. SCS-CN effective precipitation (S, Ia, Pe formulas with values)
5. Unit hydrograph (model-specific formulas and ordinates)
6. Convolution (formula, procedure description)
7. Hydrograph results (Qmax, tp, V, time series)
8. Water balance (summary table with percentages)

### Testing
- 37 new tests for reports module
- Total: 610 tests (all passing)

### Documentation
- Updated CHANGELOG.md
- Report examples in module docstrings

---

## [0.5.2] - 2026-01-21

### Changed
- Removed unused `imgwtools` from required dependencies in `pyproject.toml`
- IMGWTools is now only imported directly in Hydrograf where it is actually used
- Updated documentation (CLAUDE.md, SCOPE.md) to reflect dependency changes

---

## [0.5.1] - 2026-01-21

### Fixed
- **CRITICAL:** `SCSUnitHydrograph.peak_discharge()` - corrected constant from `2.08` to `0.208`
  - Previous implementation caused ~10x overestimation of Qmax
  - Correct formula: `qp = 0.208 * A / tp` [m³/s per mm]
  - Updated docstring with proper mathematical derivation
  - Reference: USDA TR-55 triangular unit hydrograph approximation

### Changed
- Synchronized version numbers: `__init__.py` and `pyproject.toml` now both show `0.5.1`
- Updated test expectations in `test_runoff.py` for correct peak discharge values

### Added

#### `hydrolog.morphometry.WatershedParameters` - GIS Integration Interface
New dataclass for standardized data exchange between GIS systems (Hydrograf, QGIS, ArcGIS) and Hydrolog.

- `WatershedParameters` - complete watershed parameters container
  - Required: area_km2, perimeter_km, length_km, elevation_min_m, elevation_max_m
  - Optional: name, elevation_mean_m, mean_slope_m_per_m, channel_length_km, channel_slope_m_per_m, cn, source, crs
  - `from_dict()` / `from_json()` - create from API response or JSON
  - `to_dict()` / `to_json()` - export for serialization
  - `to_geometry()` - convert to WatershedGeometry
  - `to_terrain()` - convert to TerrainAnalysis
  - `calculate_tc(method)` - calculate concentration time (kirpich, nrcs, giandotti)
  - Computed properties: `width_km`, `relief_m`

#### Factory methods for morphometry classes
- `WatershedGeometry.from_dict()` - create from dictionary
- `TerrainAnalysis.from_dict()` - create from dictionary

#### Documentation
- `docs/INTEGRATION.md` - comprehensive integration guide for GIS systems
  - JSON schema for data exchange
  - Usage examples with Hydrograf
  - Implementation details for third-party integrations

### Removed (from v0.5.0-unreleased)
- `SnyderUH.from_lag_time()` - Estimated L and Lc from lag time (impractical, these parameters should be measured from maps/GIS)
- `SnyderUH.from_tc()` - Delegated to `from_lag_time()`, same issue
- `NashIUH.from_moments()` - Required variance and lag time from observed hydrograph (not practical for ungauged catchments)
- `ClarkIUH.from_recession()` - Required recession constant from observed hydrograph

### Testing
- 35 new tests for WatershedParameters and from_dict() methods
- 15 new integration tests for Hydrograf API workflow (`tests/integration/test_hydrograf_integration.py`)
  - Full workflow: JSON → WatershedParameters → HydrographGenerator
  - Batch processing of multiple watersheds
  - Data validation and error handling
  - Round-trip serialization
- Total: 573 tests (558 unit + 15 integration, all passing)

---

## [0.5.0] - 2026-01-19

### Added

#### `hydrolog.visualization` - Visualization Module
New module for graphical presentation of hydrological results.
Requires optional dependencies: `pip install hydrolog[visualization]`

**Hietogram plots (`hietogram.py`):**
- `plot_hietogram()` - precipitation hyetograph with intensity bars and optional cumulative line
- `plot_hietogram_comparison()` - comparison of total vs effective precipitation

**Hydrograph plots (`hydrograph.py`):**
- `plot_hydrograph()` - runoff hydrograph Q(t) with peak annotation and volume
- `plot_unit_hydrograph()` - unit hydrograph for any model (SCS, Nash, Clark, Snyder)

**Combined plots (`combined.py`):**
- `plot_rainfall_runoff()` - classic rainfall-runoff plot with inverted hietogram on top
- `plot_generator_result()` - full dashboard with water balance table

**Unit hydrograph comparison (`unit_hydrograph.py`):**
- `plot_uh_comparison()` - multiple UH models on one plot with comparison table

**Water balance (`water_balance.py`):**
- `plot_water_balance()` - SCS-CN water balance visualization (bars or pie)
- `plot_cn_curve()` - P → Pe relationship with AMC variants

**Morphometry (`morphometry.py`):**
- `plot_hypsometric_curve()` - hypsometric curve h/H vs a/A with HI integral
- `plot_elevation_histogram()` - elevation distribution histogram

**Network (`network.py`):**
- `plot_stream_order_stats()` - three-panel stream network statistics
- `plot_bifurcation_ratios()` - bifurcation ratios by stream order

**Interpolation (`interpolation.py`):**
- `plot_stations_map()` - precipitation station map with weights

**Styles (`styles.py`):**
- `setup_hydrolog_style()` - configure matplotlib/seaborn for consistent styling
- `COLORS`, `LABELS_PL`, `PALETTE` - color scheme and Polish labels
- `get_color()`, `get_label()` - helper functions
- `format_time_axis()`, `add_peak_annotation()`, `add_stats_box()`, `add_watermark()`

#### `hydrolog.runoff.nash_iuh` - Lutz Method
- `NashIUH.from_lutz()` - parameter estimation from catchment characteristics
  - Estimates Nash model parameters (n, K) from physiographic data
  - Input parameters: L, Lc, slope, Manning's n, urban%, forest%
  - Numerical solution of f(N) equation using Brent's method
  - Verified against KZGW (2017) Table C.2 (accuracy < 0.001)
  - Reference: Lutz W. (1984), Universität Karlsruhe

#### `hydrolog.precipitation` - Euler Type II Hyetograph
- `EulerIIHietogram` - DVWK Euler Type II hyetograph for design storms

#### `hydrolog.runoff.snyder_uh` - Enhancements
- `SnyderUHResult` - added duration tracking (`duration_hours` field)
- Water balance formula for Snyder time base calculation

### Changed
- **BREAKING:** Unified UH model API — `area_km2` parameter moved to constructor for all UH models
- Enhanced README.md documentation:
  - Nash model theory (reservoir cascade, IUH formula, properties)
  - All parameter estimation methods (from_tc, from_moments, from_lutz)
  - Lutz method algorithm with full equations
  - Influence of physiographic parameters on runoff
  - New visualization module section with examples

### Fixed
- `fix(snyder)`: Corrected time-to-peak formula and updated notation
- `fix(snyder)`: Corrected SI unit formulas for Snyder UH model

### Dependencies
- Added optional `visualization` dependency group: matplotlib>=3.7, seaborn>=0.12

### Testing
- 53 new tests for visualization module
- 17 new tests for Lutz method
- Total: 538 unit tests (all passing)

---

## [0.4.0] - 2026-01-19

### Added

#### `hydrolog.cli` - Command-Line Interface
- `hydrolog tc` - concentration time calculation
  - `kirpich` - Kirpich formula
  - `scs-lag` - SCS Lag equation
  - `giandotti` - Giandotti formula
- `hydrolog cn` - Curve Number lookup (TR-55)
  - `lookup` - look up CN for HSG and land cover
  - `list` - list available land cover types
  - `range` - show CN range for a land cover
- `hydrolog scs` - SCS-CN runoff calculation
  - AMC conditions support (I, II, III)
  - Custom initial abstraction coefficient
- `hydrolog uh` - unit hydrograph generation
  - `scs` - SCS dimensionless unit hydrograph
  - `nash` - Nash cascade IUH
  - `clark` - Clark IUH
  - `snyder` - Snyder synthetic UH
  - Output formats: table, CSV, JSON

#### `hydrolog.runoff.clark_iuh` - Clark IUH
- `ClarkIUH` - Clark Instantaneous Unit Hydrograph
  - Translation via time-area histogram
  - Linear reservoir routing
  - Simplified elliptical time-area curve
- `ClarkIUHResult` and `ClarkUHResult` dataclasses
- `from_recession()` - parameter estimation from recession analysis
- `from_tc_r_ratio()` - estimation from Tc and R/Tc ratio

#### `hydrolog.runoff.snyder_uh` - Snyder UH
- `SnyderUH` - Snyder Synthetic Unit Hydrograph
  - Empirical relationships (Snyder, 1938)
  - Parameters: L, Lc, Ct, Cp
  - Width calculations at 50% and 75% of peak
- `SnyderUHResult` dataclass
- `from_lag_time()` - parameter estimation from lag time
- `from_tc()` - estimation from concentration time

#### `hydrolog.runoff.cn_lookup` - CN Lookup Tables
- `get_cn()` - look up CN for HSG and land cover
- `lookup_cn()` - detailed lookup with result object
- `get_cn_range()` - CN range for land cover type
- `list_land_covers()` - list available land covers
- `calculate_weighted_cn()` - area-weighted CN calculation
- `LandCover` - 20 land cover types (TR-55)
- `HydrologicCondition` - poor, fair, good conditions

#### `hydrolog.runoff.nash_iuh` - Nash IUH
- `NashIUH` - Nash Instantaneous Unit Hydrograph
  - Nash cascade model with n reservoirs and K storage constant
  - `generate()` - IUH generation at specified timestep
  - `to_unit_hydrograph()` - S-curve conversion to D-minute UH
  - `from_tc()` - parameter estimation from concentration time
  - `from_moments()` - parameter estimation from lag time and variance
- `IUHResult` and `NashUHResult` dataclasses

### Changed
- **BREAKING:** `ConcentrationTime.scs_lag()` signature changed (now renamed to `nrcs()`):
  - `length_m` → `length_km` (meters to kilometers)
  - `slope_percent` → `slope_m_per_m` (percent to dimensionless)
- Added parameter range warnings to all concentration time methods

### Fixed
- Corrected NRCS constant: `7182` → `7069` (proper metric conversion)
- Fixed docstring examples in `scs_cn.py` (Pe = 7.09 mm, not 12.89 mm)

### Dependencies
- Added `scipy` as dependency (for gamma functions in Nash IUH)
- Added optional `kartograf` dependency for spatial/soil data

### Testing
- 412 unit tests (all passing)
- 27 new CLI tests
- 41 Clark IUH tests
- 43 Snyder UH tests
- 38 CN lookup tests

---

## [0.3.0] - 2026-01-18

### Added

#### `hydrolog.network` - River Network Classification

**Stream ordering (stream_order.py):**
- `StreamSegment` - dataclass for network segments
- `StreamNetwork` - main class for network analysis
- `OrderingMethod` - enum (STRAHLER, SHREVE)
- `NetworkStatistics` - complete network statistics
- Strahler stream ordering method
- Shreve stream ordering method
- Bifurcation ratio calculation
- Length ratio calculation

**Utility functions:**
- `bifurcation_ratio()` - calculate Rb between orders
- `drainage_density()` - streams length / watershed area
- `stream_frequency()` - streams count / watershed area

#### `hydrolog.precipitation.interpolation` - Spatial Interpolation

**Interpolation methods:**
- `Station` - dataclass for measurement stations
- `thiessen_polygons()` - Thiessen/Voronoi polygon method
- `inverse_distance_weighting()` - IDW interpolation
- `areal_precipitation_idw()` - grid-based IDW averaging
- `isohyet_method()` - isohyet contour method
- `arithmetic_mean()` - simple station average

**Result dataclasses:**
- `ThiessenResult` - weights and contributions
- `IDWResult` - interpolated values with weights
- `IsohyetResult` - zone-based precipitation

#### Testing & Quality
- 60 new tests for network and interpolation (210 total)
- 95% code coverage

---

## [0.2.0] - 2026-01-18

### Added

#### `hydrolog.morphometry` - Morphometric Parameters

**Geometric parameters (geometric.py):**
- `WatershedGeometry` - main class for geometric analysis
- `GeometricParameters` - dataclass with area, perimeter, length, width
- `ShapeIndicators` - dataclass with shape coefficients:
  - Form factor (Horton)
  - Compactness coefficient (Gravelius)
  - Circularity ratio (Miller)
  - Elongation ratio (Schumm)
  - Lemniscate ratio (Chorley)

**Terrain analysis (terrain.py):**
- `TerrainAnalysis` - elevation and slope analysis
- `ElevationParameters` - min, max, mean elevation, relief
- `SlopeParameters` - watershed and channel slopes
- `mean_elevation_from_dem()` - DEM-based calculation

**Hypsometric curve (hypsometry.py):**
- `HypsometricCurve` - hypsometric analysis from DEM
- `HypsometricResult` - curve data and statistics
- Hypsometric integral calculation
- Elevation percentiles

#### Testing & Quality
- 47 new tests for morphometry (150 total)
- 95% code coverage

---

## [0.1.0] - 2026-01-18

### Added

#### `hydrolog.time` - Concentration Time
- `ConcentrationTime.kirpich()` - Kirpich formula (L in km, S in m/m)
- `ConcentrationTime.nrcs()` - NRCS equation (metric units)
- `ConcentrationTime.giandotti()` - Giandotti formula

#### `hydrolog.precipitation` - Hyetographs
- `HietogramResult` - dataclass with time series results
- `BlockHietogram` - uniform intensity distribution
- `TriangularHietogram` - triangular distribution with configurable peak
- `BetaHietogram` - Beta distribution for realistic storm patterns

#### `hydrolog.runoff` - Rainfall-Runoff
- `SCSCN` - SCS Curve Number calculations
  - Maximum retention S calculation
  - Initial abstraction Ia calculation
  - Effective precipitation Pe calculation
  - AMC conditions (I, II, III) support
- `SCSUnitHydrograph` - SCS dimensionless unit hydrograph
  - Standard NRCS tabulated ratios
  - Lag time and time to peak calculations
- `convolve_discrete()` - discrete convolution function
- `HydrographGenerator` - complete rainfall-runoff transformation
  - Integration with hyetograph module
  - Water balance tracking
  - Runoff coefficient calculation

#### Testing & Quality
- 103 unit tests
- 94% code coverage
- Full type hints (mypy)
- Black formatting

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| **0.1.0** | 2026-01-18 | SCS-CN hydrograph, hyetographs, concentration time |
| **0.2.0** | 2026-01-18 | Morphometric parameters |
| **0.3.0** | 2026-01-18 | Interpolation + river network |
| **0.4.0** | 2026-01-19 | CLI + Clark IUH + Snyder UH + CN lookup |
| **0.5.0** | 2026-01-19 | Visualization module (matplotlib/seaborn) |
| **0.5.1** | 2026-01-21 | Fix SCS peak discharge constant |
| **0.5.2** | 2026-01-21 | Remove unused imgwtools dependency |
| **0.6.0** | 2026-01-21 | Report generation module |
| **0.6.1** | 2026-03-20 | Nash urban regression method |
| **0.6.2** | 2026-03-22 | UH report formulas + metric corrections |
| **0.6.3** | 2026-03-23 | FAA + Kerby + Kerby-Kirpich tc, API audit |
| **0.6.4** | 2026-03-25 | WatershedParams extension + UH ordinates + docs audit |
| **0.7.0** | 2026-03-26 | Statystyka hydrologiczna + Hydrometria |
| **1.0.0** | niewydana (w przygotowaniu) | Stable API: command catalog, CLI from catalog, MCP server, HSG (`hydrolog.soil`), result serialization, calculation fixes |
