/**
 * Texts of Hydrolog's part of the admin panel (Nogat DEV-15.13): under „Statystyki”, what
 * each daily total counts (DEV-15.11), worded as info texts (DEV-15.14). The column
 * headings are the kit's (`STATS_COLUMNS` of nogat-admin.js); the keys are its keys.
 */

export const admin = {
  counts: "Co liczą kolumny",
  countsIntro:
    "Łączne liczby z każdego dnia UTC (doba zaczyna się o 1:00 czasu zimowego, o 2:00 " +
    "letniego w Polsce). Wejścia do panelu administracyjnego nie są liczone.",
  columns: {
    visitors:
      "Różne urządzenia, z których danego dnia przyszło co najmniej jedno żądanie strony, " +
      "obliczenia lub pliku; urządzenie rozpoznaje skrót adresu IP i oznaczenia przeglądarki, " +
      "zmieniany o północy UTC i po ponownym uruchomieniu serwera. W wierszu „Razem” to suma " +
      "dzienna: ta sama osoba liczy się w każdym dniu, w którym przyszła.",
    page_views:
      "Strony wysłane przez serwer: aplikacja, instrukcja i regulamin, także po odświeżeniu. " +
      "Przejście do innej sekcji otwartej strony nie jest odsłoną. Odwiedzający może nie mieć " +
      "odsłony: karta otwarta poprzedniego dnia albo przywrócona przez przeglądarkę z jej " +
      "pamięci liczy się tylko żądaniami obliczeń i plików.",
    stations_opened:
      "Serie stacji przekazane z Archiwisty lub Obserwatora i otwarte w Statystyce przepływów.",
    analyses_run:
      "Obliczenia zakończone wynikiem. Po otwarciu strony każda sekcja przelicza swoje " +
      "zapisane dane, a każda zmiana danych daje nowe obliczenie, więc obliczeń jest zwykle " +
      "kilka razy więcej niż odsłon. Obliczenie zakończone błędem nie jest liczone.",
    downloads:
      "Pliki zapisane na dysku z aplikacji: eksporty wyników, raport, pliki przekazania " +
      "i pliki wynikowe obliczeń.",
  },
};
