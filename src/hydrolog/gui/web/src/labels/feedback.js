/**
 * Texts of „Zgłoś uwagę” (Nogat DEV-15.12, the dialog of Nogat's mockup): the button of the
 * top bar, the dialog and the marks that stand in the context of a report for what is
 * left out of the view's parameters.
 */

export const feedback = {
  open: "Zgłoś uwagę",
  title: "Zgłoś uwagę",
  close: "Zamknij",
  intro: "Opisz błąd lub pomysł. Zgłoszenie trafi do operatora serwisu.",
  message: "Wiadomość",
  counter: "{count}/{max}",
  /** Under the field (DEV-15.12); the second sentence only with the operator's address. */
  hint: "Nie wpisuj danych osobowych.",
  hintEmail: "Nie wpisuj danych osobowych. Jeśli chcesz odpowiedzi, napisz na {email}",
  note: "Zgłoszenie zawiera też widok, jego parametry i wersję aplikacji.",
  cancel: "Anuluj",
  send: "Wyślij",
  empty: "Wiadomość nie może być pusta.",
  thanks: "Dziękujemy! Zgłoszenie zostało zapisane.",
  /** What the parameters carry instead of a long text, the rest of a list, a deep part. */
  marks: {
    text: "[tekst: {count} znaków]",
    more: "[i {count} więcej]",
    deep: "[pominięto]",
    tooLarge: "[pominięto: za duże]",
  },
};
