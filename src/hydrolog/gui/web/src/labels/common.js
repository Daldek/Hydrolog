/**
 * Words every part of the GUI shares (Polish; DEV-2.3: no text is typed into a
 * component). Each part keeps its own file `labels/<part>.js` exporting one object; texts
 * are strings with `{name}` placeholders filled by `t`.
 */

export const common = {
  actions: {
    close: "Zamknij",
    copy: "Kopiuj",
    clear: "Wyczyść",
    run: "Uruchom",
    cancel: "Anuluj",
    add: "Dodaj",
    remove: "Usuń",
    download: "Pobierz",
    upload: "Wczytaj plik…",
    paste: "Wklej",
    retry: "Spróbuj ponownie",
  },
  guide: {
    example: "Przykład w instrukcji",
    exampleTitle: "Rozdział instrukcji z przykładem: co wpisać i jaki wynik wyjdzie (nowa karta)",
  },
  copied: "Skopiowano do schowka",
  copyFailed: "Nie udało się skopiować: zaznacz tekst i skopiuj ręcznie",
  loading: "Wczytywanie…",
  empty: "–",
  yes: "tak",
  no: "nie",
  none: "brak",
  required: "wymagane",
  defaultIs: "domyślnie {value}",
  english: "(EN)",
  levels: {
    info: "Informacja",
    warning: "Uwaga",
    ok: "W zakresie",
    error: "Błąd",
  },
  from: "Hydrolog",
};

/**
 * Fill the `{name}` placeholders of a text.
 *
 * @param {string} text a text of a dictionary
 * @param {Object<string, string|number>} [values] values by placeholder name; a placeholder
 *   without a value stays as it is
 * @returns {string} the filled text
 */
export function t(text, values = {}) {
  return String(text).replace(/\{(\w+)\}/g, (whole, name) =>
    Object.hasOwn(values, name) ? String(values[name]) : whole,
  );
}
