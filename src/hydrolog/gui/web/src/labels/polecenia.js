/**
 * Texts of the section „Wszystkie polecenia”: every catalog command as a generated form,
 * run on its button, with the generic result view.
 */

export const polecenia = {
  commandForms: ["polecenie", "polecenia", "poleceń"],
  groupForms: ["grupie", "grupach", "grupach"],
  context: "{command} · {commands} w {groups}",
  contextNone: "{commands} w {groups}",
  catalog: "katalog: {commands}",
  allGroups: "Wszystkie grupy ({count})",
  groupOption: "{group}: {title} ({count})",
  groupHeading: "{group} · {title}",
  groupSelect: "Grupa poleceń",
  search: "Szukaj: nazwa, metoda, opis",
  searchLabel: "Szukaj polecenia",
  listLabel: "Polecenia katalogu",
  empty: "Brak poleceń dla tego wyszukiwania.",
  loading: "Wczytywanie katalogu…",
  loadFailed: "Nie udało się wczytać katalogu: {message}",
  pick: "Wybierz polecenie z listy: jego formularz jest pusty, wpisz dane i naciśnij „Uruchom”.",
  formLoading: "Wczytywanie opisu polecenia…",
  hint: "Formularz, tabela i JSON z katalogu (commands schema), bez kodu dla polecenia",
  view: "Widok",
  tabs: { table: "Tabela", chart: "Wykres", json: "JSON" },
  noResult: "Wypełnij formularz i uruchom polecenie: wynik pojawi się tutaj.",
  running: "Hydrolog liczy…",
  cancelled: "Obliczenie anulowano.",
  rightSub: "{command}",
  clearTitle: "Wyczyść dane wszystkich poleceń: puste formularze",
};
