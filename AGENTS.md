# Hydrolog — przewodnik dla agentów

> Plik generowany z katalogu komend: `hydrolog commands guide --format agents --lang pl --path AGENTS.md`.
> Nie edytuj ręcznie. Wersja angielska: `hydrolog commands guide --lang en`.

## Czym jest Hydrolog

Hydrolog to biblioteka Pythona, CLI `hydrolog` i serwer MCP do obliczeń hydrologicznych zlewni: opad efektywny SCS-CN i liczby CN (TR-55), hietogramy projektowe, czas koncentracji, hydrogramy jednostkowe i hydrogram odpływu, morfometria zlewni i sieci rzecznej, statystyki przepływów (wartości charakterystyczne, częstość wezbrań i niżówek, test Manna–Kendalla), krzywa przepływu i strefy stanów wody, grupy hydrologiczne gleb (HSG) z rastrów uziarnienia oraz raport obliczeniowy w Markdown. Liczy lokalnie: bez sieci, bez kluczy i bez pobierania danych — szeregi pomiarowe dostarcza IMGWTools, rastry (NMT, pokrycie terenu, gleby) Kartograf. Wszystkie interfejsy powstają z jednego katalogu komend, więc mają te same nazwy opcji, walidację, kopertę wyniku i kody błędów. Liczba komend w katalogu: 37, liczba grup: 13.

Skróty w nazwach opcji i wynikach: `tc` — czas koncentracji [min]; `CN` — liczba krzywej (Curve Number, 1–100); `AMC` — wilgotność poprzedzająca (I, II, III); `Ia` — abstrakcja początkowa (`ia_coefficient` razy retencja, domyślnie 0,2); `HSG` — grupa hydrologiczna gleby (A–D); `UH` — hydrogram jednostkowy (modele `scs`, `nash`, `clark`, `snyder`); `WWQ` … `NNQ` — wartości charakterystyczne II stopnia.

## Zasady

1. **Schemat najpierw:** `commands list` (spis) i `commands schema` (opcje, jednostki, zakresy, przykłady); w MCP `tools/list`. Nie zgaduj opcji.
2. **Pliki zamiast tablic:** serie, stacje, odcinki sieci i zlewnie podawaj plikiem CSV/JSON (`input_file`, `watershed_file`...), nie wklejaj długich list liczb.
3. **Jednostki:** opis opcji podaje jednostkę (km, km2, m/m, mm, min, m3/s; spadek w m/m, nie w %); nie przeliczaj po cichu i nie zgaduj wartości użytkownika.
4. **Błędy po kodach:** `hydrolog-error/1`: decyduj po `code` i `details.option`/`details.reason`, popraw argument według `hint` i ponów; błędu nie podawaj jako wyniku.
5. **Ścieżki bezwzględne w katalogach dozwolonych:** MCP odrzuca (`forbidden`) pliki spoza `--allow-dir`, a bez niego każdą opcję typu path.
6. **Zapis zastępuje:** opcje wyjściowe (`output`, `output_path`, `path`) nadpisują plik bez pytania — podawaj nowe nazwy; `files` wylicza zapisane (SHA-256).
7. **Bez pobierania danych:** Hydrolog nie używa sieci; szeregi daje IMGWTools (`series export` → CSV), rastry gleb Kartograf (`soil download`).

## Instalacja i uruchomienie

- Instalacja (Python ≥ 3.12; zależności: NumPy i SciPy): `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`. Dodatki: `hydrolog[raster]` (rasterio i pyproj; komendy `soil hsg` i `soil hsg-stats`), `hydrolog[mcp]` (serwer MCP), `hydrolog[visualization]` (wykresy w Pythonie, poza katalogiem komend) i `hydrolog[all]`, np. `pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"`.
- CLI: `hydrolog <grupa> <komenda> --opcja wartość` (także `python -m hydrolog.cli …`). Flaga opcji to `--` i jej nazwa z `-` zamiast `_`; lista liczb po przecinku (`--return-periods 10,50,100`), obiekt albo lista obiektów jako tekst JSON (`--parts '[{"cn": 55, "area": 27.2}]'`), wartość logiczna jako `--flaga` albo `--no-flaga`. Flagi ogólne: `--json` (koperta wyniku w jednej linii stdout), `--schema` (schemat opcji komendy, bez uruchamiania), `--lang pl|en` (język pomocy i komunikatów; zmienna `HYDROLOG_LANG`, domyślnie `pl`), `-V` (wersja).
- MCP: `hydrolog mcp --allow-dir KATALOG` (opcję `--allow-dir` można powtórzyć, `--lang pl|en` wybiera język opisów narzędzi). Claude Code: `claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data`; inni klienci: `{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}}}`. Narzędzie ma nazwę `operation_id` komendy i argumenty równe jej opcjom; bez `--allow-dir` komendy z opcjami typu path są odrzucane (`forbidden`), komendy bez plików działają.

## Interfejsy

| Interfejs | Odkrywanie | Wywołanie | Wynik | Błąd |
|---|---|---|---|---|
| Python | `data_commands()`, `command_schema()` z `hydrolog.catalog` | funkcja z `hydrolog.operations` (argumenty nazwane = opcje) albo `run_command("<grupa> <komenda>", {...})` | funkcja operacji zwraca obiekt wynikowy z `to_dict()` i `to_json()` albo `OperationOutput(result, notices, files)` (wynik w `.result`, ostrzeżenia w `.notices`, zapisane pliki w `.files`); `run_command` zawsze zwraca kopertę (`CommandResult` z `to_dict()` i `to_json()`) | wyjątek `HydrologError` (`code`, `hint`, `details`) |
| CLI | `hydrolog commands list`, `hydrolog commands schema`, `--schema` | `hydrolog <grupa> <komenda> --opcja wartość` | podsumowanie tekstowe; z `--json` koperta w jednej linii stdout | tekst na stderr albo, z `--json`, jedna linia `hydrolog-error/1`; kod wyjścia z rejestru |
| MCP | `tools/list` | narzędzie `<operation_id>` z argumentami = opcjami | `structuredContent` = koperta (ten sam JSON jako tekst) | `isError: true` i dokument `hydrolog-error/1` |

Ta sama komenda (`tc kirpich`) w każdym interfejsie:

- Python: `hydrolog.operations.tc_kirpich(length_km=8.2, slope_m_per_m=0.023)`
- CLI: `hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023`
- MCP: narzędzie `tc_kirpich` z argumentami `{"length_km": 8.2, "slope_m_per_m": 0.023}`

Poza katalogiem komend biblioteka ma klasy do pracy w kodzie (`hydrolog.runoff`, `hydrolog.time`, `hydrolog.precipitation`, `hydrolog.morphometry`, `hydrolog.network`, `hydrolog.statistics`, `hydrolog.hydrometrics`, `hydrolog.soil`, `hydrolog.reports`); wykresy (`hydrolog.visualization`, dodatek `hydrolog[visualization]`) są tylko w Pythonie. Opisują je README i docstringi.

## Koperta wyniku i błędy

Komenda zwraca kopertę `hydrolog-result/1`: `{"schema", "command", "hydrolog_version", "status", "inputs", "result", "files", "notices"}`.

- `inputs` — opcje po normalizacji: wartości domyślne uzupełnione, ścieżki bezwzględne. Z tym policzono wynik.
- `result` — wartości komendy; kształt zależy od komendy (opisuje go opis komendy w `commands schema`), jednostki wynikają z nazw pól (`tc_min`, `peak_discharge_m3s`), a `NaN` i nieskończoności są `null`.
- `files` — pliki zapisane przez komendę z opcją wyjściową: `{"role", "path", "sha256"}`.
- `notices` — nieblokujące ostrzeżenia `{"level", "code", "text"}` (krótka seria, wartość poza typowym zakresem wzoru, pominięte braki): przekaż je użytkownikowi razem z wynikiem.
- `status` jest zawsze `ok`: komenda, która się nie udała, kończy się błędem, a nie kopertą z częściowym wynikiem — obliczenia są atomowe.

Błąd to dokument `hydrolog-error/1`: `{"schema", "code", "title", "message", "hint", "details", "exit_code", "command"}`. `code` pochodzi z zamkniętego rejestru poniżej i jest ten sam w Pythonie (`HydrologError.code`), CLI (kod wyjścia; z `--json` jedna linia JSON na stderr) i MCP (`isError`). `details.option` wskazuje błędną opcję, a `details.reason` powód (m.in. `required`, `type`, `minimum`, `maximum`, `choice`, `unknown_option`, `one_of`); `message` i `hint` są po angielsku, `title` w języku `--lang`. CLI kończy się też kodem 130 po Ctrl+C.

| Kod | Tytuł | Kod wyjścia CLI | Znaczenie i co robić |
|---|---|---|---|
| `validation_error` | Nieprawidłowe dane wejściowe | 2 | zła wartość, typ albo zakres opcji, brak opcji wymaganej, nieznana opcja albo naruszona grupa `one_of`: popraw opcję z `details.option` według `details.reason` i `hint` |
| `not_found` | Nie znaleziono | 3 | nieznana komenda (`details.suggestions` podaje podobne) albo brak pliku wejściowego (`details.path`) |
| `calculation_error` | Błąd obliczeń | 4 | dane poprawne formalnie, ale wyniku nie da się obliczyć (brak zbieżności, za krótka seria): zmień dane lub parametry, ponowienie bez zmian nic nie da |
| `data_error` | Niepoprawne dane | 7 | plik wejściowy nieczytelny albo błędny (zła kolumna, liczba, data, raster): `details.path`, `details.reason`, a dla tabeli `details.column`, `details.row` i `details.available` |
| `missing_dependency` | Brak opcjonalnej zależności | 6 | brak dodatku opcjonalnego (`hydrolog[raster]`, `hydrolog[mcp]`, `hydrolog[visualization]`): zainstaluj go według `hint` |
| `forbidden` | Ścieżka niedozwolona | 8 | ścieżka poza katalogami dozwolonymi serwera MCP: użyj ścieżki w jednym z `details.allowed_dirs` (bez `--allow-dir` każda opcja typu path jest odrzucana) |
| `io_error` | Błąd systemu plików | 9 | nie można zapisać pliku wyjściowego (uprawnienia, brak miejsca, katalog zamiast pliku): sprawdź `details.path` |
| `internal_error` | Błąd wewnętrzny | 1 | błąd w Hydrologu: zgłoś komendę, opcje i wersję (`hydrolog --version`), nie ponawiaj |

## Dane wejściowe

- **Szeregi** (`values` z `dates` albo `input_file` z `value_column` i ewentualnie `date_column`; dokładne alternatywy podaje kolumna „Opcje” tabel komend): plik CSV (przecinek lub średnik, UTF-8, wiersz nagłówka) albo JSON (lista rekordów, obiekt kolumn albo lista liczb). Liczby `12.5` lub `12,5`; pusta komórka, `NaN`, `NA` i `null` to braki; daty ISO `RRRR-MM-DD`, ściśle rosnące. Kolumnę wskazujesz nazwą dokładną albo bez sufiksu jednostki (`Q` znajduje `Q [m3/s]`). CSV z eksportu szeregu IMGWTools (`series export`) wczytuje się bez przetwarzania.
- **Zlewnia** (`watershed_file` albo `watershed`): JSON w formacie `WatershedParameters` (`to_json()`); wymagane `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`, opcjonalne m.in. `name`, `elevation_mean_m`, `mean_slope_m_per_m`, `channel_length_km`, `channel_slope_m_per_m`, `cn`. Pola wymagane przez metodę wymienia opis komendy; brak pola kończy się `validation_error` z listą braków.
- **Posterunki opadowe** (`precip areal`: `stations` albo `stations_file`): rekordy `name`, `x`, `y`, `precipitation_mm`, opcjonalnie `elevation_m`.
- **Odcinki sieci rzecznej** (`network stats`: `segments` albo `segments_file`): kolumny `segment_id`, `upstream_ids` (w CSV id rozdziela średnik, np. `3;4`) i `length_km`.
- **Rastry** (`soil hsg`, `soil hsg-stats`; dodatek `hydrolog[raster]`): GeoTIFF. Rastry iłu, piasku i pyłu muszą mieć ten sam układ współrzędnych, siatkę i rozmiar (inaczej `data_error`); jednostki dowolne, ale spójne (SoilGrids: g/kg). Wynik `soil hsg` to GeoTIFF `uint8`: 0 — brak danych, 1–4 to grupy A–D.

## Komendy

Tabela każdej grupy podaje komendę, nazwę narzędzia MCP (`operation_id`), opis, opcje w kolejności katalogu (`*` — wymagana, `=` — wartość domyślna; flaga CLI to `--` i nazwa opcji z `-` zamiast `_`) oraz skutek uruchomienia: `odczyt`; `zapis z nadpisaniem` — komenda zapisuje plik wskazany opcją wyjściową; `odczyt; opcja: zapis…` — zapisuje tylko wtedy, gdy podasz tę opcję. Żadna komenda nie używa sieci. Pełny schemat opcji (jednostki, zakresy, przykłady): `hydrolog commands schema --command "<komenda>"`.

### `tc` — Czas koncentracji

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `tc faa` | `tc_faa` | Czas koncentracji metodą FAA dla spływu powierzchniowego (L, spadek, C). | `length_km*`, `slope_m_per_m*`, `runoff_coeff*` | odczyt |
| `tc giandotti` | `tc_giandotti` | Czas koncentracji wzorem Giandottiego z powierzchni, długości i spadku. | `area_km2*`, `length_km*`, `elevation_diff_m*` | odczyt |
| `tc kerby` | `tc_kerby` | Czas spływu powierzchniowego wzorem Kerby'ego (L, spadek, retardancja N). | `length_km*`, `slope_m_per_m*`, `retardance*` | odczyt |
| `tc kerby-kirpich` | `tc_kerby_kirpich` | Czas koncentracji złożoną metodą Kerby–Kirpich (spływ powierzchniowy + koryto). | `overland_length_km*`, `overland_slope_m_per_m*`, `retardance*`, `channel_length_km*`, `channel_slope_m_per_m*` | odczyt |
| `tc kirpich` | `tc_kirpich` | Czas koncentracji wzorem Kirpicha z długości i spadku cieku głównego. | `length_km*`, `slope_m_per_m*` | odczyt |
| `tc nrcs` | `tc_nrcs` | Czas koncentracji metodą NRCS (TR-55, czas opóźnienia) z L, spadku i CN. | `length_km*`, `slope_m_per_m*`, `cn*` | odczyt |
| `tc watershed` | `tc_watershed` | Czas koncentracji wybraną metodą z parametrów zlewni (WatershedParameters). | `watershed`, `watershed_file`, `method=kirpich` (dokładnie jedno z: `watershed` / `watershed_file`) | odczyt |

### `cn` — Liczba CN (TR-55)

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `cn list` | `cn_list` | Pełna tablica CN TR-55: pokrycia terenu, stany hydrologiczne i CN dla grup A–D. | — | odczyt |
| `cn lookup` | `cn_lookup` | Liczba CN z tablic TR-55 dla grupy hydrologicznej gleby i pokrycia terenu. | `hsg*`, `land_cover*`, `condition` | odczyt |
| `cn range` | `cn_range` | Zakres CN (min–max po stanach hydrologicznych) pokrycia terenu dla grup A–D. | `land_cover*` | odczyt |
| `cn weighted` | `cn_weighted` | Średnia ważona powierzchnią liczba CN zlewni złożonej z kilku pokryć/gleb. | `parts`, `cn_values`, `areas`, `fractions` (dokładnie jedna grupa: `parts` / `cn_values`+`areas` / `cn_values`+`fractions`) | odczyt |

### `scs` — Opad efektywny SCS-CN

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `scs effective` | `scs_effective` | Opad efektywny metodą SCS-CN z sumy opadu lub hietogramu (CN, AMC, Ia). | `cn*`, `precipitation_mm`, `values`, `input_file`, `value_column`, `amc=II`, `ia_coefficient=0.2` (dokładnie jedno z: `precipitation_mm` / `values` / `input_file`) | odczyt |

### `precip` — Opady: hietogramy i opad obszarowy

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `precip areal` | `precip_areal` | Opad obszarowy z posterunków: średnia arytmetyczna, Thiessen, IDW lub izohiety. | `method*`, `stations`, `stations_file`, `polygon_areas_km2`, `target_x`, `target_y`, `grid_x`, `grid_y`, `power`, `max_distance`, `isohyet_values_mm`, `area_fractions` | odczyt |
| `precip hietogram` | `precip_hietogram` | Hietogram opadu projektowego: blokowy, trójkątny, beta lub Euler II. | `hietogram_type*`, `total_mm*`, `duration_min*`, `timestep_min=5.0`, `alpha`, `beta`, `peak_position` | odczyt |

### `uh` — Hydrogramy jednostkowe

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `uh clark` | `uh_clark` | Hydrogram jednostkowy Clarka (translacja + zbiornik liniowy) z tc oraz R lub R/tc. | `area_km2*`, `tc_min*`, `r_min`, `r_tc_ratio`, `timestep_min=5.0`, `rainfall_duration_min`, `total_duration_min` (dokładnie jedno z: `r_min` / `r_tc_ratio`) | odczyt |
| `uh nash` | `uh_nash` | Hydrogram jednostkowy Nasha (kaskada zbiorników): n i K, metoda Lutza lub regresja miejska. | `area_km2*`, `n`, `k_min`, `lutz_length_km`, `lutz_centroid_length_km`, `lutz_slope_m_per_m`, `lutz_manning_n`, `lutz_urban_pct`, `lutz_forest_pct`, `urban_effective_precip_mm`, `urban_duration_h`, `urban_fraction`, `timestep_min=5.0`, `rainfall_duration_min`, `total_duration_min` (dokładnie jedna grupa: `n`+`k_min` / `lutz_length_km`+`lutz_centroid_length_km`+`lutz_slope_m_per_m`+`lutz_manning_n` / `urban_effective_precip_mm`+`urban_duration_h`) | odczyt |
| `uh scs` | `uh_scs` | Hydrogram jednostkowy SCS (NRCS, TR-55) z powierzchni i czasu koncentracji. | `area_km2*`, `tc_min*`, `timestep_min=5.0` | odczyt |
| `uh snyder` | `uh_snyder` | Syntetyczny hydrogram jednostkowy Snydera z L, Lc oraz współczynników Ct i Cp. | `area_km2*`, `length_km*`, `centroid_length_km*`, `ct=1.5`, `cp=0.6`, `timestep_min=30.0`, `rainfall_duration_min`, `total_duration_min` | odczyt |

### `hydrograph` — Hydrogram odpływu

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `hydrograph generate` | `hydrograph_generate` | Hydrogram odpływu bezpośredniego zlewni: opad → SCS-CN → hydrogram jednostkowy → splot. | `watershed`, `watershed_file`, `area_km2`, `cn`, `tc_min`, `tc_method`, `ia_coefficient=0.2`, `amc=II`, `hietogram_type`, `total_mm`, `duration_min`, `alpha`, `beta`, `peak_position`, `values`, `input_file`, `value_column`, `timestep_min=5.0`, `uh_model=scs`, `nash_n`, `nash_k_min`, `clark_r_min`, `clark_r_tc_ratio`, `snyder_length_km`, `snyder_centroid_length_km`, `snyder_ct`, `snyder_cp` (dokładnie jedna grupa: `watershed` / `watershed_file` / `area_km2`+`cn`) | odczyt |

### `morphometry` — Morfometria zlewni

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `morphometry watershed` | `morphometry_watershed` | Wskaźniki geometryczne, kształtu i rzeźby zlewni z jej parametrów (obiekt albo plik JSON). | `watershed`, `watershed_file` (dokładnie jedno z: `watershed` / `watershed_file`) | odczyt |

### `network` — Sieć rzeczna

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `network stats` | `network_stats` | Klasyfikacja sieci rzecznej (Strahler, Shreve): rzędy, długości, wskaźniki Hortona, gęstość sieci. | `segments`, `segments_file`, `method=strahler`, `area_km2` (dokładnie jedno z: `segments` / `segments_file`) | odczyt |

### `stats` — Statystyki przepływów

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `stats characteristic` | `stats_characteristic` | Wartości charakterystyczne II stopnia (WWQ…NNQ) z szeregu dobowego, rok hydrologiczny XI–X. | `values`, `dates`, `input_file`, `value_column`, `date_column`, `parameter=Q` (dokładnie jedna grupa: `values`+`dates` / `input_file`+`value_column`+`date_column`) | odczyt |
| `stats daily` | `stats_daily` | Statystyki dobowe z wielolecia: maksimum, średnia, mediana i minimum dla każdej doby roku hydrologicznego. | `values`, `dates`, `input_file`, `value_column`, `date_column` (dokładnie jedna grupa: `values`+`dates` / `input_file`+`value_column`+`date_column`) | odczyt |
| `stats flood-frequency` | `stats_flood_frequency` | Analiza częstości wezbrań: rozkłady log-normalny, GEV, Pearsona III, Weibulla; kwantyle dla okresów powtarzalności. | `values`, `dates`, `input_file`, `value_column`, `date_column`, `distribution=all`, `return_periods=[2.0,5.0,10.0,20.0,50.0,100.0,500.0,1000.0]` (dokładnie jedna grupa: `values` / `input_file`+`value_column`) | odczyt |
| `stats low-flow` | `stats_low_flow` | Analiza częstości niżówek: rozkład Fishera–Tippetta (GEV) dla minimów rocznych, kwantyle niskich przepływów. | `values`, `dates`, `input_file`, `value_column`, `date_column`, `return_periods=[2.0,5.0,10.0,20.0,50.0,100.0,500.0,1000.0]` (dokładnie jedna grupa: `values`+`dates` / `input_file`+`value_column`+`date_column`) | odczyt |
| `stats low-flow-sequences` | `stats_low_flow_sequences` | Ciągi niżówkowe (susze hydrologiczne) metodą progową: terminy, czas trwania, niedobór. | `values`, `dates`, `input_file`, `value_column`, `date_column`, `threshold*`, `min_duration_days=5`, `max_gap_days=4` (dokładnie jedna grupa: `values`+`dates` / `input_file`+`value_column`+`date_column`) | odczyt |
| `stats mann-kendall` | `stats_mann_kendall` | Test trendu Manna–Kendalla szeregu (stacjonarność): statystyka, p-value, kierunek trendu. | `values`, `input_file`, `value_column`, `alpha=0.05` (dokładnie jedna grupa: `values` / `input_file`+`value_column`) | odczyt |
| `stats monthly` | `stats_monthly` | Statystyki miesięczne z przedziałem ufności średniej (t-Studenta) dla miesięcy 1–12. | `values`, `dates`, `input_file`, `value_column`, `date_column`, `confidence_level=0.95` (dokładnie jedna grupa: `values`+`dates` / `input_file`+`value_column`+`date_column`) | odczyt |

### `hydrometrics` — Hydrometria

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `hydrometrics rating-curve` | `hydrometrics_rating_curve` | Krzywa przepływu Q = a·(H − H₀)^b dopasowana do par stan–przepływ, z opcjonalnym usuwaniem odstających. | `water_levels`, `discharges`, `input_file`, `level_column`, `discharge_column`, `h0_initial`, `remove_outliers=false`, `outlier_std=2.0` (dokładnie jedna grupa: `water_levels`+`discharges` / `input_file`+`level_column`+`discharge_column`) | odczyt |
| `hydrometrics water-level-zones` | `hydrometrics_water_level_zones` | Strefy stanów wody wg Rybczyńskiego (NTW, STW, WTW) z histogramu i krzywej czasu trwania stanów. | `values`, `input_file`, `value_column`, `bin_width=10.0` (dokładnie jedna grupa: `values` / `input_file`+`value_column`) | odczyt |

### `soil` — Gleby: uziarnienie i HSG

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `soil hsg` | `soil_hsg` | Raster HSG (GeoTIFF) z rastrów iłu, piasku i pyłu, np. SoilGrids w g/kg; zapisuje plik, wymaga [raster]. | `clay_path*`, `sand_path*`, `silt_path*`, `output_path*` | zapis z nadpisaniem: `output_path` |
| `soil hsg-stats` | `soil_hsg_stats` | Powierzchnie grup HSG A–D z rastra HSG, opcjonalnie w prostokącie bbox; wymaga [raster]. | `hsg_path*`, `bbox`, `bbox_crs` | odczyt |
| `soil texture` | `soil_texture` | Klasa uziarnienia gleby (trójkąt USDA) i grupa hydrologiczna gleby HSG A–D z zawartości iłu, piasku i pyłu. | `clay*`, `sand*`, `silt*` | odczyt |

### `report` — Raport obliczeniowy

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `report generate` | `report_generate` | Raport obliczeniowy hydrogramu w Markdown (wzory, tabele, bilans); dane jak w `hydrograph generate`; zapisuje plik. | `output*`, `watershed_name`, `watershed`, `watershed_file`, `area_km2`, `cn`, `tc_min`, `tc_method`, `ia_coefficient=0.2`, `amc=II`, `hietogram_type`, `total_mm`, `duration_min`, `alpha`, `beta`, `peak_position`, `values`, `input_file`, `value_column`, `timestep_min=5.0`, `uh_model=scs`, `nash_n`, `nash_k_min`, `clark_r_min`, `clark_r_tc_ratio`, `snyder_length_km`, `snyder_centroid_length_km`, `snyder_ct`, `snyder_cp`, `include_formulas=true`, `include_tables=true`, `max_table_rows=50` (dokładnie jedna grupa: `watershed` / `watershed_file` / `area_km2`+`cn`) | zapis z nadpisaniem: `output` |

### `commands` — Opis katalogu komend

| Komenda | Narzędzie MCP | Opis | Opcje | Skutek |
|---|---|---|---|---|
| `commands guide` | `commands_guide` | Przewodnik dla agentów (AGENTS.md albo llms.txt) z katalogu komend; opcjonalnie zapisuje plik. | `format=agents`, `lang=pl`, `path` | odczyt; `path`: zapis z nadpisaniem |
| `commands list` | `commands_list` | Lista komend katalogu: nazwa, operation_id i krótki opis. | `lang=pl` | odczyt |
| `commands schema` | `commands_schema` | Opis opcji komend jako JSON Schema (cały katalog albo jedna komenda). | `command`, `lang=pl` | odczyt |

## Typowe przepływy

Każdy krok ma postać linii CLI, a pod nią wywołanie MCP (narzędzie i argumenty); w Pythonie te same opcje to argumenty nazwane funkcji z `hydrolog.operations`. Ścieżki `/dane/...` są przykładowe — podaj własne, bezwzględne i (w MCP) w katalogu dozwolonym. Symbole pisane wielkimi literami (`MAGAZYN_IMGW`, `KOD_STACJI`) zastąp wartościami z IMGWTools; linie `imgw` i `kartograf` to osobne narzędzia ekosystemu, nie komendy Hydrologa.

### 1. Hydrogram projektowy ze zlewni opisanej plikiem JSON

Plik zlewni ma format `WatershedParameters` (`to_json()`): wymagane są `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` i `elevation_max_m`, opcjonalne m.in. `name`, `cn`, `channel_length_km` i `channel_slope_m_per_m`. To proponowany format rodzaju `catchment_characteristics` w Retmanie.

1. `hydrolog morphometry watershed --watershed-file /dane/hydrolog/zlewnia.json` — wskaźniki geometryczne, kształtu i rzeźby zlewni; przy okazji sprawdzasz, że plik się wczytuje (zły plik to `data_error` z `details.path` i `details.reason`).
   - MCP: `morphometry_watershed {"watershed_file": "/dane/hydrolog/zlewnia.json"}`
2. `hydrolog tc watershed --watershed-file /dane/hydrolog/zlewnia.json --method kirpich` — czas koncentracji (`result.tc_min`) z pól pliku zlewni (długość i spadek cieku); brak pola wymaganego przez metodę to `validation_error` z listą braków.
   - MCP: `tc_watershed {"watershed_file": "/dane/hydrolog/zlewnia.json", "method": "kirpich"}`
3. `hydrolog hydrograph generate --watershed-file /dane/hydrolog/zlewnia.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60 --timestep-min 5 --uh-model scs` — hydrogram odpływu bezpośredniego: hietogram Beta (50 mm w 60 min) → SCS-CN (`cn` z pliku, AMC II) → hydrogram jednostkowy SCS → splot; `result` ma m.in. `peak_discharge_m3s`, `time_to_peak_min`, `total_volume_m3` i `runoff_coefficient`, ostrzeżenia są w `notices`.
   - MCP: `hydrograph_generate {"watershed_file": "/dane/hydrolog/zlewnia.json", "tc_method": "kirpich", "hietogram_type": "beta", "total_mm": 50, "duration_min": 60, "timestep_min": 5, "uh_model": "scs"}`
4. `hydrolog report generate --output /dane/hydrolog/raport.md --watershed-file /dane/hydrolog/zlewnia.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60 --timestep-min 5 --uh-model scs` — raport Markdown (wzory, tabele, bilans wodny) z tych samych opcji plus `output`; zastępuje istniejący plik, a `files` podaje jego ścieżkę i SHA-256.
   - MCP: `report_generate {"output": "/dane/hydrolog/raport.md", "watershed_file": "/dane/hydrolog/zlewnia.json", "tc_method": "kirpich", "hietogram_type": "beta", "total_mm": 50, "duration_min": 60, "timestep_min": 5, "uh_model": "scs"}`

### 2. Częstość wezbrań z eksportu CSV z IMGWTools

Hydrolog niczego nie pobiera: dobowy szereg przepływów eksportuje IMGWTools (`series export`) do pliku CSV z jednostkami w nagłówku (`Q [m3/s]`), kolumną `date`, flagami wartości i atrybucją. Hydrolog wczytuje ten plik bez przetwarzania.

1. `imgw series export --root MAGAZYN_IMGW --dataset pl.imgw.hydro_daily --station KOD_STACJI --variables Q --format csv --path /dane/hydrolog/q_dobowe.csv` — IMGWTools (osobne narzędzie, jego przewodnik to AGENTS.md w repozytorium IMGWTools): eksport szeregu jednej stacji do pliku; `KOD_STACJI` wskazuje `imgw stations find`, `MAGAZYN_IMGW` to magazyn IMGWTools. Do wiarygodnych kwantyli potrzeba co najmniej 30 lat.
2. `hydrolog stats flood-frequency --input-file /dane/hydrolog/q_dobowe.csv --value-column Q --date-column date --distribution all --return-periods 10,50,100` — maksima roczne są wybierane z lat hydrologicznych (XI–X); kolumny podajesz nazwą bez jednostki (`Q` znajduje `Q [m3/s]`); wynik: `best_distribution` (kryterium AIC) i `distributions[].quantiles` (kwantyle dla `return_periods`); seria krótsza niż 30 lat daje ostrzeżenie w `notices`.
   - MCP: `stats_flood_frequency {"input_file": "/dane/hydrolog/q_dobowe.csv", "value_column": "Q", "date_column": "date", "distribution": "all", "return_periods": [10, 50, 100]}`
3. `hydrolog stats characteristic --input-file /dane/hydrolog/q_dobowe.csv --value-column Q --date-column date --parameter Q` — wartości charakterystyczne II stopnia (WWQ … NNQ) z tego samego pliku (rok hydrologiczny XI–X).
   - MCP: `stats_characteristic {"input_file": "/dane/hydrolog/q_dobowe.csv", "value_column": "Q", "date_column": "date", "parameter": "Q"}`

### 3. Grupy hydrologiczne gleb (HSG) z rastrów SoilGrids i ważone CN

Hydrolog nie pobiera rastrów: ił, piasek i pył z SoilGrids (g/kg) pobiera Kartograf (`soil download`), a Hydrolog liczy z nich HSG (dodatek `hydrolog[raster]`).

1. `kartograf soil download --property clay --depth 0-5cm --stat mean --bbox 626000,480000,628000,482000 --bbox-crs EPSG:2180 --output /dane/kartograf --json` — Kartograf (osobne narzędzie): powtórz z `--property sand` i `--property silt`; ścieżki rastrów (`files[].file.path` odpowiedzi `--json`) są wejściami następnego kroku.
2. `hydrolog soil hsg --clay-path /dane/kartograf/soil/global_soilgrids_clay_0-5cm_mean/bbox/626000_480000_628000_482000.tif --sand-path /dane/kartograf/soil/global_soilgrids_sand_0-5cm_mean/bbox/626000_480000_628000_482000.tif --silt-path /dane/kartograf/soil/global_soilgrids_silt_0-5cm_mean/bbox/626000_480000_628000_482000.tif --output-path /dane/hydrolog/hsg.tif` — raster HSG (GeoTIFF `uint8`: 0 — brak danych, 1–4 to A–D) z trzech rastrów o tym samym układzie współrzędnych, siatce i rozmiarze; zapis zastępuje istniejący plik.
   - MCP: `soil_hsg {"clay_path": "/dane/kartograf/soil/global_soilgrids_clay_0-5cm_mean/bbox/626000_480000_628000_482000.tif", "sand_path": "/dane/kartograf/soil/global_soilgrids_sand_0-5cm_mean/bbox/626000_480000_628000_482000.tif", "silt_path": "/dane/kartograf/soil/global_soilgrids_silt_0-5cm_mean/bbox/626000_480000_628000_482000.tif", "output_path": "/dane/hydrolog/hsg.tif"}`
3. `hydrolog soil hsg-stats --hsg-path /dane/hydrolog/hsg.tif` — powierzchnia i udział każdej grupy (`groups.A` … `groups.D`: `area_ha`, `percent`) oraz brak danych (`nodata`); opcjonalnie tylko prostokąt `bbox` z `bbox_crs`.
   - MCP: `soil_hsg_stats {"hsg_path": "/dane/hydrolog/hsg.tif"}`
4. `hydrolog cn list` — tablica CN TR-55: dla każdego pokrycia terenu i stanu CN grup A–D (jedną parę daje `cn lookup`); wybierz wiersz pokrycia terenu zlewni, tu `meadow`, stan `good`.
   - MCP: `cn_list {}`
5. `hydrolog cn weighted --parts '[{"cn":30,"area":75.0},{"cn":58,"area":75.0},{"cn":71,"area":75.0},{"cn":78,"area":68.75}]'` — CN zlewni ważone powierzchnią (`result.cn`): `area` każdej części to `area_ha` grupy z `soil hsg-stats`; przy kilku pokryciach terenu części są parami (HSG × pokrycie), a przecięcie rastrów robisz poza Hydrologiem.
   - MCP: `cn_weighted {"parts": [{"cn": 30, "area": 75.0}, {"cn": 58, "area": 75.0}, {"cn": 71, "area": 75.0}, {"cn": 78, "area": 68.75}]}`
6. `hydrolog hydrograph generate --area-km2 45.3 --cn 58.85 --tc-min 120 --hietogram-type beta --total-mm 50 --duration-min 60` — hydrogram z samej powierzchni i CN (zamiast pliku zlewni); `tc_min` daje np. `tc watershed`.
   - MCP: `hydrograph_generate {"area_km2": 45.3, "cn": 58.85, "tc_min": 120, "hietogram_type": "beta", "total_mm": 50, "duration_min": 60}`

### 4. Porównanie metod czasu koncentracji

Metody dają różne `tc` (nawet kilkukrotnie) i każda ma swój zakres stosowalności: porównaj je i przeczytaj `notices`, nie wybieraj po cichu — pokaż różnice użytkownikowi albo uzasadnij wybór. Bez pliku zlewni służą komendy metod (`tc kirpich`, `tc nrcs`, `tc giandotti`...) z samymi liczbami. `faa` i `kerby` liczą czas spływu powierzchniowego (z `overland_length_km` i `overland_slope_m_per_m`, nie z długości i spadku koryta), więc nie zastępują czasu koncentracji zlewni z korytem — do tego służy `kerby_kirpich`.

1. `hydrolog tc watershed --watershed-file /dane/hydrolog/zlewnia.json --method kirpich` — metoda Kirpicha: długość i spadek cieku z pliku zlewni.
   - MCP: `tc_watershed {"watershed_file": "/dane/hydrolog/zlewnia.json", "method": "kirpich"}`
2. `hydrolog tc watershed --watershed-file /dane/hydrolog/zlewnia.json --method nrcs` — metoda NRCS (TR-55): długość cieku, średni spadek zlewni (`mean_slope_m_per_m`, dopiero bez niego spadek cieku) i `cn` z pliku zlewni.
   - MCP: `tc_watershed {"watershed_file": "/dane/hydrolog/zlewnia.json", "method": "nrcs"}`
3. `hydrolog tc watershed --watershed-file /dane/hydrolog/zlewnia.json --method giandotti` — metoda Giandottiego: powierzchnia, długość i wysokość średnia nad przekrojem zamykającym; wzór jest dla dużych zlewni górskich, więc dla małej zlewni (poza zakresem z opisu komendy) wynik ma ostrzeżenie w `notices`.
   - MCP: `tc_watershed {"watershed_file": "/dane/hydrolog/zlewnia.json", "method": "giandotti"}`
4. `hydrolog hydrograph generate --watershed-file /dane/hydrolog/zlewnia.json --tc-min 136 --hietogram-type beta --total-mm 50 --duration-min 60` — wybraną wartość podaj jako `tc_min` (zamiast `tc_method`), np. wynik pierwszego kroku.
   - MCP: `hydrograph_generate {"watershed_file": "/dane/hydrolog/zlewnia.json", "tc_min": 136, "hietogram_type": "beta", "total_mm": 50, "duration_min": 60}`

## Czego nie robić

1. Nie wklejaj długich szeregów do argumentów — zapisz je do pliku CSV lub JSON i podaj plik (`input_file`).
2. Nie zgaduj opcji, jednostek ani wartości, których użytkownik nie podał; spadek podajesz w m/m (nie w %), opad w mm, czas w minutach.
3. Nie parsuj angielskiego `message` ani `hint` — decyduj po `code`, `details.option`, `details.reason` i kodzie wyjścia; `hint` służy do poprawienia argumentu.
4. Nie ignoruj `notices`: ostrzeżenia (krótka seria, wartość poza zakresem wzoru, pominięte braki) przekaż użytkownikowi razem z wynikiem.
5. Nie wybieraj po cichu jednej metody (czasu koncentracji, hydrogramu jednostkowego, rozkładu), gdy dają różne wyniki — pokaż różnice albo uzasadnij wybór.
6. Nie łącz wzorów czasu koncentracji z każdym modelem hydrogramu jednostkowego: SCS i Clark biorą `tc`, Nash — `n` i `K` (metoda Lutza, regresja miejska albo wartości zadane), Snyder — `Ct` i `Cp` bez zewnętrznego `tc` (`docs/COMPUTATION_PATHS.md`).
7. Nie ponawiaj wywołania bez zmiany: `validation_error`, `data_error` i `calculation_error` wymagają poprawy opcji albo danych.
8. Nie nadpisuj plików wejściowych: opcje wyjściowe (`output`, `output_path`, `path`) zastępują istniejący plik bez pytania, a `report generate` odmawia, gdy `output` jest plikiem wejściowym.
9. Nie oczekuj sieci ani pobierania danych: szeregi pomiarowe dostarcza IMGWTools, rastry (NMT, pokrycie terenu, gleby) Kartograf.
10. W MCP nie zgaduj ścieżek: podawaj bezwzględne, w katalogach `--allow-dir`; `forbidden` wylicza dozwolone w `details.allowed_dirs`.
11. Nie uruchamiaj `soil hsg` ani `soil hsg-stats` bez dodatku `hydrolog[raster]` (`missing_dependency`).
12. Nie traktuj HSG jako CN: grupa gleby to jeden z dwóch czynników — CN wymaga też pokrycia terenu (`cn list`, `cn lookup`, `cn weighted`).
13. Nie edytuj `AGENTS.md` ani `llms.txt` ręcznie — regeneruj je komendą z nagłówka.

## Praca nad kodem repozytorium

Ten plik opisuje używanie Hydrologa. Przy zmianach kodu obowiązują `CLAUDE.md` (środowisko, gałęzie, konwencje), `docs/DEVELOPMENT_STANDARDS.md` (standardy), `docs/SCOPE.md` (zakres: Hydrolog niczego nie pobiera) i `docs/PROGRESS.md` (stan prac); zmiany dla użytkowników zapisuje `docs/CHANGELOG.md`. Bramka: `.venv/bin/python -m pytest tests/`, `.venv/bin/python -m black --check hydrolog/ tests/` i `.venv/bin/python -m mypy hydrolog/`.

**Jak dodać komendę** (szczegóły: docstring `hydrolog/catalog/__init__.py`):

1. Operacja: publiczna, udokumentowana (docstring NumPy), w pełni otypowana funkcja o argumentach nazwanych tak jak opcje, w `hydrolog/operations/<grupa>.py`; zwraca wynik z `to_dict()` albo `OperationOutput` (ostrzeżenia, zapisane pliki); wyeksportuj ją w `hydrolog/operations/__init__.py`.
2. Deklaracja: `Command` i `Option` w `hydrolog/catalog/groups/<grupa>.py` (krotka `COMMANDS`): nazwa `<grupa> <komenda>`, `operation_id`, opisy po polsku i angielsku (`summary` do 120 znaków), jednostki, zakresy, `one_of`, `writes` i co najmniej jeden przykład w `examples`. Nowa grupa: dopisz jej moduł do `GROUP_MODULES` w `hydrolog/catalog/groups/__init__.py` (to kolejność w pomocy CLI i w tym przewodniku; `commands` zostaje ostatnia) i tytuł do `_GROUP_TITLES` w `hydrolog/agent_guide.py`.
3. CLI, serwer MCP i przewodniki powstają z katalogu bez dalszych zmian. Testy katalogu uruchamiają każdy przykład przez `run_command` i CLI (`--json`) i porównują koperty.
4. Zregeneruj przewodniki w tej samej zmianie: `hydrolog commands guide --format agents --lang pl --path AGENTS.md` i `hydrolog commands guide --format llms --lang pl --path llms.txt`. Test `tests/unit/test_agent_guide.py` porównuje bajty obu plików z generatorem; to samo dotyczy zmiany szablonów w `hydrolog/_data/agents/`, rejestru błędów i przepływów w `hydrolog/agent_guide.py` (każdy krok przepływu jest walidowany, więc przemianowana opcja zatrzyma generator).
