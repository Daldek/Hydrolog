/**
 * Texts of the export panel (plan D14) and of the call shown under a result: CSV and JSON
 * written in the browser, PNG of the chart shown, the command line, Python and MCP, and the
 * files a command wrote.
 */

export const exportLabels = {
  title: "Eksport",
  csv: { format: "CSV", label: "Tabela", title: "Tabela wyniku jako CSV (przecinek, kropka dziesiętna, UTF-8)" },
  json: { format: "JSON", label: "Wynik", title: "Dokument wyniku hydrolog-result/1, jak go zwrócił Hydrolog" },
  png: { format: "PNG", label: "Wykres", title: "Wykres widoczny na ekranie jako obraz PNG" },
  report: { format: "MD", label: "Raport", title: "Raport obliczeniowy w Markdown (report generate)" },
  saved: "Zapisano {name}",
  pngFailed: "Nie udało się zapisać wykresu: {message}",
  call: {
    title: "Wywołanie",
    interfaces: "Interfejs",
    cli: "CLI",
    python: "Python",
    mcp: "MCP",
    copy: "Kopiuj wywołanie",
    pending: "Wywołanie pojawi się dla poprawnego formularza",
    failed: "Nie udało się ułożyć wywołania: {message}",
    tool: "narzędzie: {tool}",
  },
  files: {
    title: "Pliki wyniku",
    written: "zapisany",
    replaced: "zastąpiony",
    download: "Pobierz {name}",
  },
  plan: {
    title: "Plan zapisu",
    sub: "Tryb planu: Hydrolog niczego nie zapisał",
    option: "Opcja",
    path: "Plik",
    action: "Akcja",
    actions: { write: "zapisze", replace: "zastąpi", conflict: "konflikt: plik istnieje" },
  },
};
