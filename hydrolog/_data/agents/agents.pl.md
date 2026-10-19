# Hydrolog — przewodnik dla agentów

> Plik generowany z katalogu komend: `hydrolog commands guide --format agents --lang pl --path AGENTS.md`.
> Nie edytuj ręcznie. Wersja angielska: `hydrolog commands guide --lang en`.

## Czym jest Hydrolog

Hydrolog to biblioteka Pythona, CLI `hydrolog` i serwer MCP do obliczeń hydrologicznych zlewni: opad efektywny SCS-CN i liczby CN (TR-55), hietogramy projektowe, czas koncentracji, hydrogramy jednostkowe i hydrogram odpływu, morfometria zlewni i sieci rzecznej, statystyki przepływów (wartości charakterystyczne, częstość wezbrań i niżówek, test Manna–Kendalla), krzywa przepływu i strefy stanów wody, grupy hydrologiczne gleb (HSG) z rastrów uziarnienia oraz raport obliczeniowy w Markdown. Liczy lokalnie: bez sieci, bez kluczy i bez pobierania danych — szeregi pomiarowe dostarcza IMGWTools, rastry (NMT, pokrycie terenu, gleby) Kartograf. Wszystkie interfejsy powstają z jednego katalogu komend, więc mają te same nazwy opcji, walidację, kopertę wyniku i kody błędów. <!-- hydrolog:summary -->

Skróty w nazwach opcji i wynikach: `tc` — czas koncentracji [min]; `CN` — liczba krzywej (Curve Number, 1–100); `AMC` — wilgotność poprzedzająca (I, II, III); `Ia` — abstrakcja początkowa (`ia_coefficient` razy retencja, domyślnie 0,2); `HSG` — grupa hydrologiczna gleby (A–D); `UH` — hydrogram jednostkowy (modele `scs`, `nash`, `clark`, `snyder`); `WWQ` … `NNQ` — wartości charakterystyczne II stopnia.

## Zasady

<!-- hydrolog:rules -->

## Instalacja i uruchomienie

- Instalacja (Python ≥ 3.12; zależności: NumPy i SciPy): `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`. Dodatki: `hydrolog[raster]` (rasterio i pyproj; komendy `soil hsg` i `soil hsg-stats`), `hydrolog[mcp]` (serwer MCP), `hydrolog[visualization]` (wykresy w Pythonie, poza katalogiem komend) i `hydrolog[all]`, np. `pip install "hydrolog[mcp,raster] @ git+https://github.com/Daldek/Hydrolog.git"`.
- CLI: `hydrolog <grupa> <komenda> --opcja wartość` (także `python -m hydrolog.cli …`). Flaga opcji to `--` i jej nazwa z `-` zamiast `_`; lista liczb po przecinku (`--return-periods 10,50,100`), obiekt albo lista obiektów jako tekst JSON (`--parts '[{"cn": 55, "area": 27.2}]'`), wartość logiczna jako `--flaga` albo `--no-flaga`. Flagi ogólne: `--json` (koperta wyniku w jednej linii stdout), `--schema` (schemat opcji komendy, bez uruchamiania), `--lang pl|en` (język pomocy i komunikatów; zmienna `HYDROLOG_LANG`, domyślnie `pl`), `-V` (wersja).
- MCP: `hydrolog mcp --allow-dir KATALOG` (opcję `--allow-dir` można powtórzyć, `--lang pl|en` wybiera język opisów narzędzi). Claude Code: `claude mcp add hydrolog -- hydrolog mcp --allow-dir ~/hydrolog-data`; inni klienci: `{"mcpServers": {"hydrolog": {"command": "hydrolog", "args": ["mcp", "--allow-dir", "/home/ola/hydrolog-data"]}}}`. Narzędzie ma nazwę `operation_id` komendy i argumenty równe jej opcjom; bez `--allow-dir` komendy z opcjami typu path są odrzucane (`forbidden`), komendy bez plików działają.

## Interfejsy

| Interfejs | Odkrywanie | Wywołanie | Wynik | Błąd |
|---|---|---|---|---|
| Python | `data_commands()`, `command_schema()` z `hydrolog.catalog` | funkcja z `hydrolog.operations` (argumenty nazwane = opcje) albo `run_command("<grupa> <komenda>", {...})` | obiekt wynikowy z `to_dict()` i `to_json()`; `run_command` zwraca kopertę (`CommandResult`) | wyjątek `HydrologError` (`code`, `hint`, `details`) |
| CLI | `hydrolog commands list`, `hydrolog commands schema`, `--schema` | `hydrolog <grupa> <komenda> --opcja wartość` | podsumowanie tekstowe; z `--json` koperta w jednej linii stdout | tekst na stderr albo, z `--json`, jedna linia `hydrolog-error/1`; kod wyjścia z rejestru |
| MCP | `tools/list` | narzędzie `<operation_id>` z argumentami = opcjami | `structuredContent` = koperta (ten sam JSON jako tekst) | `isError: true` i dokument `hydrolog-error/1` |

<!-- hydrolog:call_example -->

Poza katalogiem komend biblioteka ma klasy do pracy w kodzie (`hydrolog.runoff`, `hydrolog.time`, `hydrolog.precipitation`, `hydrolog.morphometry`, `hydrolog.network`, `hydrolog.statistics`, `hydrolog.hydrometrics`, `hydrolog.soil`, `hydrolog.reports`); wykresy (`hydrolog.visualization`, dodatek `hydrolog[visualization]`) są tylko w Pythonie. Opisują je README i docstringi.

## Koperta wyniku i błędy

Komenda zwraca kopertę `hydrolog-result/1`: `{"schema", "command", "hydrolog_version", "status", "inputs", "result", "files", "notices"}`.

- `inputs` — opcje po normalizacji: wartości domyślne uzupełnione, ścieżki bezwzględne. Z tym policzono wynik.
- `result` — wartości komendy; kształt zależy od komendy (opisuje go opis komendy w `commands schema`), jednostki wynikają z nazw pól (`tc_min`, `peak_discharge_m3s`), a `NaN` i nieskończoności są `null`.
- `files` — pliki zapisane przez komendę z opcją wyjściową: `{"role", "path", "sha256"}`.
- `notices` — nieblokujące ostrzeżenia `{"level", "code", "text"}` (krótka seria, wartość poza typowym zakresem wzoru, pominięte braki): przekaż je użytkownikowi razem z wynikiem.
- `status` jest zawsze `ok`: komenda, która się nie udała, kończy się błędem, a nie kopertą z częściowym wynikiem — obliczenia są atomowe.

Błąd to dokument `hydrolog-error/1`: `{"schema", "code", "title", "message", "hint", "details", "exit_code", "command"}`. `code` pochodzi z zamkniętego rejestru poniżej i jest ten sam w Pythonie (`HydrologError.code`), CLI (kod wyjścia; z `--json` jedna linia JSON na stderr) i MCP (`isError`). `details.option` wskazuje błędną opcję, a `details.reason` powód (m.in. `required`, `type`, `minimum`, `maximum`, `choice`, `unknown_option`, `one_of`); `message` i `hint` są po angielsku, `title` w języku `--lang`. CLI kończy się też kodem 130 po Ctrl+C.

<!-- hydrolog:errors -->

## Dane wejściowe

- **Szeregi** (`values` z `dates` albo `input_file` z `value_column` i ewentualnie `date_column`; dokładne alternatywy podaje kolumna „Opcje” tabel komend): plik CSV (przecinek lub średnik, UTF-8, wiersz nagłówka) albo JSON (lista rekordów, obiekt kolumn albo lista liczb). Liczby `12.5` lub `12,5`; pusta komórka, `NaN`, `NA` i `null` to braki; daty ISO `RRRR-MM-DD`, ściśle rosnące. Kolumnę wskazujesz nazwą dokładną albo bez sufiksu jednostki (`Q` znajduje `Q [m3/s]`). CSV z eksportu szeregu IMGWTools (`series export`) wczytuje się bez przetwarzania.
- **Zlewnia** (`watershed_file` albo `watershed`): JSON w formacie `WatershedParameters` (`to_json()`); wymagane `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m`, `elevation_max_m`, opcjonalne m.in. `name`, `elevation_mean_m`, `mean_slope_m_per_m`, `channel_length_km`, `channel_slope_m_per_m`, `cn`. Pola wymagane przez metodę wymienia opis komendy; brak pola kończy się `validation_error` z listą braków.
- **Posterunki opadowe** (`precip areal`: `stations` albo `stations_file`): rekordy `name`, `x`, `y`, `precipitation_mm`, opcjonalnie `elevation_m`.
- **Odcinki sieci rzecznej** (`network stats`: `segments` albo `segments_file`): kolumny `segment_id`, `upstream_ids` (w CSV id rozdziela średnik, np. `3;4`) i `length_km`.
- **Rastry** (`soil hsg`, `soil hsg-stats`; dodatek `hydrolog[raster]`): GeoTIFF. Rastry iłu, piasku i pyłu muszą mieć ten sam układ współrzędnych, siatkę i rozmiar (inaczej `data_error`); jednostki dowolne, ale spójne (SoilGrids: g/kg). Wynik `soil hsg` to GeoTIFF `uint8`: 0 — brak danych, 1–4 to grupy A–D.

## Komendy

Tabela każdej grupy podaje komendę, nazwę narzędzia MCP (`operation_id`), opis, opcje w kolejności katalogu (`*` — wymagana, `=` — wartość domyślna; flaga CLI to `--` i nazwa opcji z `-` zamiast `_`) oraz skutek uruchomienia: `odczyt`; `zapis z nadpisaniem` — komenda zapisuje plik wskazany opcją wyjściową; `odczyt; opcja: zapis…` — zapisuje tylko wtedy, gdy podasz tę opcję. Żadna komenda nie używa sieci. Pełny schemat opcji (jednostki, zakresy, przykłady): `hydrolog commands schema --command "<komenda>"`.

<!-- hydrolog:commands -->

## Typowe przepływy

Każdy krok ma postać linii CLI, a pod nią wywołanie MCP (narzędzie i argumenty); w Pythonie te same opcje to argumenty nazwane funkcji z `hydrolog.operations`. Ścieżki `/dane/...` są przykładowe — podaj własne, bezwzględne i (w MCP) w katalogu dozwolonym. Symbole pisane wielkimi literami (<!-- hydrolog:flow_symbols -->) zastąp wartościami z IMGWTools; linie `imgw` i `kartograf` to osobne narzędzia ekosystemu, nie komendy Hydrologa.

<!-- hydrolog:flows -->

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
