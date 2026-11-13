/**
 * Texts of the admin page (admin/, Nogat plan 2026-11-03, D3): the key prompt and the
 * reports of „Zgłoś uwagę”, as Hydrograf's admin panel words them.
 */

export const admin = {
  auth: {
    title: "Panel administracyjny",
    text: "Podaj klucz API, aby kontynuować.",
    key: "Klucz API",
    file: "lub wczytaj z pliku:",
    submit: "Zaloguj",
    checking: "Sprawdzanie…",
    invalid: "Nieprawidłowy klucz API. Spróbuj ponownie.",
  },
  title: "Zgłoszenia użytkowników",
  unread: "Nieprzeczytane: {count}",
  refresh: "Odśwież",
  logout: "Wyloguj",
  loading: "Ładowanie…",
  empty: "Brak zgłoszeń.",
  fresh: "nowe",
  markRead: "Oznacz przeczytane",
  markUnread: "Oznacz nieprzeczytane",
  remove: "Usuń",
  confirmRemove: "Usunąć zgłoszenie #{id}?",
  more: "Pokaż starsze ({shown} z {total})",
  /** The context of a report (Nogat DEV-15.12): what the page added to the text. */
  view: "Widok: {value}",
  station: "Stacja: {value}",
  version: "Wersja aplikacji: {value}",
  parameters: "Parametry widoku",
  noContext: "Zgłoszenie bez kontekstu.",
  failed: "Błąd: {message}",
  saveFailed: "Błąd zapisu: {message}",
  removeFailed: "Błąd usuwania: {message}",
};
