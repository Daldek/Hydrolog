/**
 * Texts of „Zgłoś uwagę” (Nogat plan 2026-11-03, D1: Hydrograf's texts): the button of the
 * top bar, the dialog and the marks that stand in the diagnostics for what is left out.
 */

export const feedback = {
  open: "Zgłoś uwagę",
  title: "Zgłoś uwagę",
  close: "Zamknij",
  intro: "Opisz błąd lub pomysł. Zgłoszenie trafi do administratora Hydrologa.",
  message: "Opis problemu lub sugestii",
  placeholder: "Opisz co się stało lub co można poprawić…",
  counter: "{count}/{max}",
  contact: "Imię lub e-mail",
  optional: "(opcjonalnie)",
  diagnostics: "Dołącz dane diagnostyczne (ostatnie akcje w aplikacji, błędy, parametry zapytań)",
  preview: "Pokaż co zostanie wysłane",
  noDiagnostics: "Dane diagnostyczne nie zostaną dołączone.",
  cancel: "Anuluj",
  send: "Wyślij",
  empty: "Opis nie może być pusty.",
  thanks: "Dziękujemy! Zgłoszenie zostało zapisane.",
  /** What the diagnostics carry instead of a long text, the rest of a list, a deep part. */
  marks: {
    text: "[tekst: {count} znaków]",
    more: "[i {count} więcej]",
    deep: "[pominięto]",
    tooLarge: "[pominięto: za duże]",
  },
};
