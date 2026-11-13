/**
 * Texts of the shell: the top bar, the rail, the panels Dane | Wykresy | Wyniki and the
 * second left panel beside Dane (ViewLayout's `detail`, plan 2026-11-10-network-wizard D2),
 * the phone sheets, the status badge, „Instrukcja”, the welcome dialog and the footer of a
 * public GUI. `sections` names every section by its id (router.js), the titles of
 * GuiModule.sections (plan D4).
 */

export const shell = {
  brand: "Hydrolog",
  home: "Hydrolog, strona główna",
  crumbs: "Kontekst",
  nav: "Sekcje",
  sections: {
    hydrogram: { title: "Hydrogram zlewni", short: "Hydrogram" },
    siec: { title: "Sieć i trasowanie", short: "Sieć" },
    statystyka: { title: "Statystyka przepływów", short: "Staty\u00adstyka" },
    kalkulatory: { title: "Kalkulatory", short: "Kalku\u00adlatory" },
    polecenia: { title: "Wszystkie polecenia", short: "Polece\u00adnia" },
  },
  pageTitle: "Hydrolog: {section}",
  pageTitleContext: "Hydrolog: {section} — {context}",
  theme: {
    label: "Motyw",
    auto: "Auto",
    autoTitle: "Motyw systemowy",
    light: "Jasny",
    dark: "Ciemny",
  },
  guide: {
    label: "Instrukcja",
    title: "Okno powitalne i przewodnik użytkownika",
  },
  welcome: {
    title: "Witaj w Hydrologu",
    text: [
      "Hydrolog szacuje, ile wody spłynie do potoku lub rzeki po silnym deszczu, jak taka fala płynie dalej korytem i jak często zdarzają się duże przepływy.",
      "Każda sekcja jest na początku pusta, bez przykładowych danych: wpisz albo wczytaj swoje dane w panelu „Dane”, a wynik zobaczysz w panelu „Wyniki”. Przykłady krok po kroku, z liczbami do wpisania i wynikiem, są w instrukcji.",
      "To szacunki z uproszczonych metod, a nie prognoza ani oficjalna mapa zagrożenia powodziowego.",
    ],
    hide: "Nie pokazuj ponownie",
    guide: "Otwórz instrukcję",
    app: "Przejdź do aplikacji",
    close: "Zamknij",
  },
  /** The footer of a public GUI (Nogat DEV-15.7, DEV-15.8): the statement verbatim. */
  footer: {
    label: "Informacje o serwisie",
    statement:
      "Serwis jest niekomercyjny i bezpłatny, nie zawiera reklam i nie służy działalności gospodarczej operatora. Służy celom badawczym i edukacyjnym. Dane IMGW-PIB są w nim wykorzystywane do celów niezarobkowych, zgodnie z regulaminami IMGW-PIB.",
    terms: "Regulamin",
  },
  panels: {
    left: "Dane",
    center: "Wykresy",
    right: "Wyniki",
    closeLeft: "Zamknij panel danych",
    closeDetail: "Zamknij panel",
    closeRight: "Zamknij panel wyników",
    resizeLeft: "Szerokość panelu danych",
    resizeDetail: "Szerokość panelu",
    resizeRight: "Szerokość panelu wyników",
    backToLeft: "← Dane",
  },
  status: {
    ok: { text: "Wynik aktualny", title: "Wyniki odpowiadają danym w panelu Dane" },
    busy: { text: "Liczenie…", title: "Hydrolog liczy wynik dla zmienionych danych" },
    stale: {
      text: "Dane zmienione: oblicz ponownie",
      title: "Wyniki odpowiadają poprzednim danym",
    },
    invalid: { text: "Dane niepełne", title: "Popraw pola oznaczone na czerwono" },
    error: { text: "Błąd danych", title: "Hydrolog nie policzył wyniku dla tych danych" },
  },
  sectionLoading: "Wczytywanie sekcji…",
  sectionFailed: "Nie udało się wczytać sekcji „{section}”: {message}",
  noSections: "Brak sekcji do pokazania.",
  info: {
    open: "Objaśnienie: {title}",
    close: "Zamknij objaśnienie",
    ranges: "Zakres stosowania",
    sources: "Źródła",
    inRange: "w zakresie",
    outOfRange: "poza zakresem",
    noValue: "zakres",
    unverified: "do weryfikacji",
    range: "{label}: {range}",
    rangeValue: "{label} = {value}: {range}",
    between: "od {min} do {max}",
    atLeast: "co najmniej {min}",
    atMost: "najwyżej {max}",
    missing: "Brak objaśnienia „{id}”.",
  },
};
