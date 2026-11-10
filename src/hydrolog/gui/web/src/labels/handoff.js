/**
 * Texts of the hand-off between the GUIs (plan D15, nogat-handoff/1 carrying
 * hydrolog-network/1): reading a hand-off from a file or the clipboard, the problems found
 * in it, the received producer's result beside Hydrolog's own, and writing one from
 * Hydrogram zlewni and Sieć i trasowanie.
 */

export const handoffLabels = {
  load: {
    button: "Wczytaj z Hydrografa",
    title: "Wczytaj przekazanie nogat-handoff/1: jedna zlewnia otworzy się w Hydrogramie zlewni, sieć w Sieci i trasowaniu",
    menu: "Wczytaj z Hydrografa",
    file: "Plik przekazania…",
    fileSub: "„Plik przekazania” z Hydrografa",
    paste: "Wklej ze schowka",
    pasteSub: "„Kopiuj do Hydrologa” w Hydrografie",
    pasteTitle: "Wklej przekazanie",
    pasteHint:
      "Przeglądarka nie dała dostępu do schowka: wklej w pole poniżej (Ctrl+V) przekazanie skopiowane przyciskiem „Kopiuj do Hydrologa” w Hydrografie albo treść jego „Pliku przekazania”.",
    pasteLabel: "Przekazanie nogat-handoff/1 (JSON)",
    pasteOpen: "Wczytaj",
    pasteCancel: "Anuluj",
    reading: "Wczytywanie przekazania…",
    refused: "Nie wczytano przekazania",
    more: "… i {count} więcej",
    schemaFailed: "Nie udało się pobrać schematu przekazania: {message}",
    readFailed: "Nie udało się odczytać {name}: {message}",
    empty: "Schowek jest pusty.",
    opened: "Wczytano przekazanie „{subject}” ({producer})",
    openedSiec: "Wczytano przekazanie „{subject}” ({producer}) w Sieci i trasowaniu: {nodes}",
    openedStatystyka: "Wczytano przekazanie „{subject}” ({producer}) w Statystyce przepływów: {values}",
    uploadFailed: "Nie udało się zapisać szeregu w plikach sesji: {message}",
  },
  /** „Wczytaj z Archiwisty” in Statystyka przepływów: the same reading, a station's series. */
  loadSeries: {
    button: "Wczytaj z Archiwisty",
    title:
      "Wczytaj przekazanie nogat-handoff/1 z Archiwisty: szereg dobowy stacji albo maksima roczne otworzą się tutaj",
    menu: "Wczytaj z Archiwisty",
    fileSub: "„Plik przekazania” z karty stacji w Archiwiście",
    pasteSub: "„Kopiuj do Hydrologa” na karcie stacji w Archiwiście",
    pasteHint:
      "Przeglądarka nie dała dostępu do schowka: wklej w pole poniżej (Ctrl+V) przekazanie skopiowane przyciskiem „Kopiuj do Hydrologa” na karcie stacji w Archiwiście albo treść jego „Pliku przekazania”.",
  },
  /** „Wczytaj z Hydrografa” in Sieć i trasowanie: every network opens there (plan 2026-11-10-network-editor, D10). */
  loadSiec: {
    title: "Wczytaj przekazanie nogat-handoff/1: sieć otworzy się tutaj, także jedna zlewnia z wylotem",
  },
  /** „Dodaj zlewnię z Hydrografa” in Sieć i trasowanie: a hand-off's subcatchments added to the open network (D10). */
  add: {
    button: "Dodaj zlewnię z Hydrografa",
    title: "Dodaj do otwartej sieci zlewnie z przekazania nogat-handoff/1, bez jego wylotu; połączysz je na schemacie",
    menu: "Dodaj zlewnię z Hydrografa",
    refused: "Nie dodano zlewni",
    series: "To przekazanie niesie szereg stacji (hydrolog-series/1): zlewnię dodasz z przekazania sieci hydrolog-network/1.",
    none: "Przekazanie nie ma zlewni do dodania.",
    full: "Na schemacie nie ma wolnego pola na zlewnię.",
    /** Forms of „zlewnia” after „Dodano” and a number (the accusative). */
    forms: ["zlewnię", "zlewnie", "zlewni"],
    added: "Dodano {count} z przekazania „{subject}” ({producer}): {nodes}.",
    renamed: "Zlewnia {from} z przekazania ma w sieci id {to}.",
    skipped: "Pominięto węzły przekazania inne niż zlewnie: {nodes}.",
    stepKept: "Sieć zostaje przy swoim kroku czasowym {network} min; przekazanie ma krok {handoff} min.",
    stepTaken: "Krok czasowy sieci: {handoff} min, jak w przekazaniu.",
    stepNone: "Sieć nie podaje kroku czasowego i tak zostaje; przekazanie ma krok {handoff} min.",
    ownRainfall: "Opad przekazania różni się od opadu sieci, więc jest opadem własnym: {nodes}.",
  },
  /**
   * „Wczytaj z Hydrografa” in a subcatchment's panel of Sieć: a hand-off of one watershed
   * fills the chosen node (plan 2026-11-10-network-wizard, D10).
   */
  fill: {
    title:
      "Wczytaj przekazanie nogat-handoff/1 jednej zlewni do tej zlewni sieci: jej dane, model i opad; id, połączenia, położenie i opis węzła zostają",
    refused: "Nie wczytano zlewni",
    network:
      "To przekazanie niesie sieć ({nodes}): wczytasz ją przyciskiem „Wczytaj z Hydrografa” w kroku 1 panelu Dane (zastąpi otwartą sieć), a jej zlewnie dodasz przyciskiem „Dodaj zlewnię z Hydrografa”.",
    series: "To przekazanie niesie szereg stacji (hydrolog-series/1), nie zlewnię.",
    filled: "Wczytano zlewnię {id} z przekazania „{subject}” ({producer}).",
    ownRainfall: "Opad przekazania różni się od opadu sieci, więc jest opadem własnym zlewni {id}.",
  },
  problems: {
    notJson: "To nie jest JSON: {message}",
    notObject: "Przekazanie nie jest obiektem JSON.",
    notHandoff: "To nie jest przekazanie nogat-handoff/1 (schema: {schema}).",
    network: "To jest sieć hydrolog-network/1: wczytaj ją w Sieci i trasowaniu przyciskiem „Plik sieci…”.",
    watershed: "To jest plik zlewni: wczytaj go w Hydrogramie zlewni przyciskiem „Plik zlewni…”.",
    payloadKind: "Przekazanie niesie {schema}; Hydrolog przyjmuje hydrolog-network/1 i hydrolog-series/1.",
    seriesLength: "Szereg ma {keys} dat albo lat i {values} wartości: powinno być tyle samo.",
    seriesEmpty: "Szereg nie ma żadnej wartości.",
    seriesMinima:
      "To są minima roczne: Statystyka przepływów liczy kwantyle przepływów maksymalnych; niskie przepływy liczy polecenie stats low-flow w Poleceniach.",
    stepMismatch: "Krok sieci {network} min różni się od kroku szeregu opadu zlewni {id} ({series} min).",
    root: "dokument",
  },
  /** Forms of „wartość” after a number. */
  valueForms: ["wartość", "wartości", "wartości"],
  /** Words of the checks against a JSON Schema, after the path of the value. */
  schema: {
    required: "brak pola „{name}”",
    additional: "nieznane pole „{name}”",
    type: "oczekiwano: {type}",
    types: {
      object: "obiekt",
      array: "lista",
      string: "tekst",
      number: "liczba",
      integer: "liczba całkowita",
      boolean: "tak lub nie",
      null: "null",
    },
    or: " albo ",
    const: "oczekiwano „{value}”",
    enum: "wartość spoza listy: {allowed}",
    minimum: "musi być ≥ {limit}",
    maximum: "musi być ≤ {limit}",
    exclusiveMinimum: "musi być > {limit}",
    exclusiveMaximum: "musi być < {limit}",
    minLength: "nie może być pusty",
    minLengthOf: "co najmniej {limit} znaków",
    maxLength: "najwyżej {limit} znaków",
    pattern: "niepoprawny zapis",
    minItems: "co najmniej {limit} elementów",
    maxItems: "najwyżej {limit} elementów",
    uniqueItems: "elementy się powtarzają",
    minProperties: "nie może być pusty",
    dependentRequired: "„{name}” wymaga pola „{needed}”",
    not: "niedozwolona wartość albo połączenie pól",
    propertyName: "niepoprawna nazwa „{name}”",
    oneOf: "nie pasuje do żadnego wariantu",
    oneOfMany: "pasuje do więcej niż jednego wariantu",
  },
  /** Names of the tools of the ecosystem: as a subject and after „z” (genitive). */
  tools: {
    hydrograf: ["Hydrograf", "Hydrografa"],
    hydrolog: ["Hydrolog", "Hydrologa"],
    nogat: ["Nogat", "Nogatu"],
    archiwista: ["Archiwista", "Archiwisty"],
    kartograf: ["Kartograf", "Kartografa"],
    obserwator: ["Obserwator", "Obserwatora"],
    hydraulik: ["Hydraulik", "Hydraulika"],
    retman: ["Retman", "Retmana"],
  },
  origin: {
    title: "Z {producer}: {subject}",
    point: "zlewnia punktu {latitude} {ns}, {longitude} {ew}",
    detail: "{time} · {fields} · nogat-handoff/1",
    received: "{producer} {version} · {time} · nogat-handoff/1",
    snyderSkipped: "{option} = {value} pominięte: zlewnia ma {field} = {kept}",
  },
  export: {
    title: "Przekazanie",
    meta: "nogat-handoff/1",
    file: "Plik przekazania",
    fileTitle: "Pobierz przekazanie nogat-handoff/1 (dane, ich pochodzenie i wynik do porównania)",
    copy: "Do schowka",
    copyTitle: "Skopiuj przekazanie nogat-handoff/1 do schowka",
    copied: "Skopiowano przekazanie do schowka (nogat-handoff/1)",
    saved: "Zapisano {name}",
    standalone: "Samodzielnie: przez plik albo schowek; wczytasz go z powrotem w Hydrologu przyciskiem „Wczytaj z Hydrografa”, np. w innej przeglądarce.",
    hydrogram: "Zawiera zlewnię ({fields}{changed}), opad ({rain}), straty, model i wynik (Qmax, czas do szczytu, objętość) do porównania.",
    changed: ", zmienione: {count}",
    siec: "Zawiera sieć ({nodes}) i wynik wylotu (Qmax, czas do szczytu, objętość) do porównania.",
    siecNoResult: "Zawiera sieć ({nodes}), bez wyniku: „Oblicz sieć” dołączy wynik wylotu do porównania.",
    invalid: "Dostępne, gdy dane sieci są kompletne",
    incomplete: "Przekazanie niesie pełną zlewnię: uzupełnij w kroku 1 pola {fields}.",
    failed: "Nie udało się przygotować przekazania: {message}",
  },
  received: {
    title: "Wczytane przekazanie",
    quantity: "Wielkość",
    producer: "Producent",
    own: "Hydrolog",
    version: "Wersja",
    rows: { q: "Qmax", tp: "Czas do szczytu", volume: "Objętość" },
    engine: "{tool} {version}",
    same: "Wynik producenta zgodny z wynikiem Hydrologa.",
    differVersion: "Wyniki się różnią: producent liczył wersją {engine}, ten wynik to Hydrolog {version}.",
    differSame: "Wyniki się różnią przy tej samej wersji Hydrologa: sprawdź dane przekazania.",
    changed: "Dane zmieniono po wczytaniu przekazania: wynik producenta dotyczy danych z przekazania.",
    noOwn: "„Oblicz sieć” policzy wynik Hydrologa do porównania.",
    stale: "Wynik Hydrologa jest dla poprzednich danych: „Oblicz sieć” odświeży porównanie.",
    noResult: "Przekazanie nie niesie wyniku producenta do porównania.",
  },
};
