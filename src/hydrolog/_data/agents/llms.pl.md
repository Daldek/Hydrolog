# Hydrolog

> Biblioteka Pythona, CLI i serwer MCP do obliczeń hydrologicznych zlewni: SCS-CN i liczby CN, hietogramy projektowe, czas koncentracji, hydrogramy jednostkowe i odpływu, morfometria, statystyki przepływów, grupy hydrologiczne gleb (HSG) z rastrów, raport w Markdown. Liczy lokalnie, bez sieci i bez pobierania danych. <!-- hydrolog:summary -->

<!-- hydrolog:rules -->

- Interfejsy: Python (`hydrolog.operations`, argumenty nazwane = opcje komendy), CLI `hydrolog <grupa> <komenda> --opcja wartość` (`--json` — koperta w jednej linii, `--schema` — schemat opcji) i serwer MCP `hydrolog mcp --allow-dir KATALOG` (dodatek `hydrolog[mcp]`; narzędzie = `operation_id`, np. `tc_kirpich`). Instalacja: `pip install "hydrolog @ git+https://github.com/Daldek/Hydrolog.git"`; komendy `soil hsg` i `soil hsg-stats` wymagają dodatku `hydrolog[raster]`.
- Wynik: koperta `hydrolog-result/1` z polami `inputs`, `result`, `files` i `notices` (ostrzeżenia przekaż użytkownikowi).
- Błąd: dokument `hydrolog-error/1` (`code`, `title`, `message`, `hint`, `details`; CLI: ostatnia linia stderr z `--json`); kody z zamkniętego rejestru (kod wyjścia CLI w nawiasie): <!-- hydrolog:error_codes -->.
- Dane wejściowe: CSV (przecinek lub średnik, nagłówek) albo JSON; kolumnę wskazujesz nazwą z jednostką albo bez (`Q` znajduje `Q [m3/s]`); zlewnia to JSON `WatershedParameters`.

Grupy komend (`hydrolog commands list`; opcje i przykłady: `hydrolog commands schema --command "<komenda>"`):

<!-- hydrolog:groups -->

Typowe przepływy (CLI; w MCP wywołaj narzędzie `operation_id` z argumentami = opcje; symbole wielkimi literami zastąp własnymi wartościami):

<!-- hydrolog:flows_short -->

## Dokumentacja

- [AGENTS.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/AGENTS.md): pełny przewodnik dla agentów — zasady, koperta i błędy, formaty plików, wszystkie komendy z opcjami, przepływy w CLI i MCP, czego nie robić
- [README.md](https://raw.githubusercontent.com/Daldek/Hydrolog/main/README.md): instalacja i przykłady użycia biblioteki
- [Zakres](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/SCOPE.md): co jest w zakresie, a co poza nim (Hydrolog niczego nie pobiera)
- [Ścieżki obliczeniowe](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/COMPUTATION_PATHS.md): które metody czasu koncentracji i parametry pasują do modeli hydrogramu jednostkowego (SCS, Nash, Clark, Snyder)
- [Integracja](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/INTEGRATION.md): wymiana zlewni z Hydrografem (format `WatershedParameters`)
- [Zmiany](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/CHANGELOG.md): zmiany per wydanie

## Optional

- [Projekt 1.0.0](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/superpowers/specs/2026-10-19-v1-catalog-mcp-hsg-design.md): katalog komend, serwer MCP, serializacja wyników, HSG
- [Standardy](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/DEVELOPMENT_STANDARDS.md): zasady pracy nad kodem
- [PRD](https://raw.githubusercontent.com/Daldek/Hydrolog/main/docs/PRD.md): wymagania produktowe
