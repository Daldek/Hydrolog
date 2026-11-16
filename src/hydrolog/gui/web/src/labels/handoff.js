/**
 * Texts of the hand-off between the GUIs (plan D15, nogat-handoff/1 carrying
 * hydrolog-network/1): reading a hand-off from a file or the clipboard, the problems found
 * in it, the received producer's result beside Hydrolog's own, and writing one from
 * Hydrogram zlewni and Sieć i trasowanie. The labels, messages and problem words every GUI
 * shares come from Nogat's kit (`TEXTS` of nogat-handoff.js, DEV-15.5, ADR-0027).
 */

import { TEXTS as KIT, guiName } from "../../nogat/nogat-handoff.js";

export const handoffLabels = {
  load: {
    button: KIT.loadFrom("hydrograf"),
    title: "Wczytaj przekazanie nogat-handoff/1: jedna zlewnia otworzy się w Hydrogramie zlewni, sieć w Sieci i trasowaniu",
    menu: KIT.loadFrom("hydrograf"),
    file: KIT.openFile,
    fileSub: `„${KIT.file}” z ${guiName("hydrograf", "genitive")}`,
    paste: KIT.paste,
    pasteSub: `„${KIT.copyTo("hydrolog")}” w Hydrografie`,
    pasteTitle: "Wklej przekazanie",
    pasteHint: `${KIT.pasteByHand} Przekazanie kopiuje w Hydrografie przycisk „${KIT.copyTo("hydrolog")}”; nada się też treść jego „Pliku przekazania”.`,
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
    unknownNodes: "Pominięto pochodzenie węzłów, których nie ma w sieci przekazania (node_provenance): {nodes}.",
  },
  /** „Wczytaj z Archiwisty” in Statystyka przepływów: the same reading, a station's series. */
  loadSeries: {
    button: KIT.loadFrom("archiwista"),
    title:
      "Wczytaj przekazanie nogat-handoff/1 z Archiwisty: szereg dobowy stacji albo maksima roczne otworzą się tutaj",
    menu: KIT.loadFrom("archiwista"),
    fileSub: `„${KIT.file}” z karty stacji w Archiwiście`,
    pasteSub: `„${KIT.copyTo("hydrolog")}” na karcie stacji w Archiwiście`,
    pasteHint: `${KIT.pasteByHand} Przekazanie kopiuje przycisk „${KIT.copyTo("hydrolog")}” na karcie stacji w Archiwiście; nada się też treść jego „Pliku przekazania”.`,
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
  /** The words of a problem against a JSON Schema, after the path of the value: the kit's. */
  keywords: KIT.keywords,
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
  /**
   * Where data came from: a hand-off's record and the origins of its provenance and of each
   * node (node_provenance; plan 2026-11-10-network-wizard, D9), with the words of
   * Hydrograf's elements of a network (its plan 2026-11-10-network-delineation, D14). A
   * headwater is a „dopływ”, as Hydrograf shows and names it (its ADR-080, amended
   * 2026-11-11): which branch of a junction is the headwater changes nothing here.
   */
  origin: {
    title: "Z {producer}: {subject}",
    point: "zlewnia punktu {latitude} {ns}, {longitude} {ew}",
    place: "{latitude} {ns}, {longitude} {ew}",
    detail: "{time} · {fields} · nogat-handoff/1",
    received: "{producer} {version} · {time} · nogat-handoff/1",
    snyderSkipped: "{option} = {value} pominięte: zlewnia ma {field} = {kept}",
    elements: {
      headwater: "dopływ",
      tributary: "dopływ",
      intermediate: "przyrzecze",
      reach: "odcinek",
      confluence: "zbieg",
      point: "punkt kontrolny",
      outlet: "przekrój zamykający",
    },
    ofPoint: "do punktu {point}",
    atMouth: "do ujścia przy punkcie {point}",
    ofReach: "odcinka {reach}",
    lengths: { flow_distance: "długość wzdłuż spływu" },
    slopes: { nmt: "spadek z NMT", minimum: "spadek minimalny" },
    ends: "NMT {upstream} → {downstream} m n.p.m.",
    vector: "długość kontrolna {length} km ({source})",
    vectorSources: { bdot10k: "BDOT10k", mphp: "MPHP" },
    pmaxtp: "PMAXTP p {p}%, {duration}",
    interpolations: { thiessen: "Thiessen", idw: "IDW" },
    tc: "tc: {method}",
    user: "wpisane ręcznie",
    file: "plik {file}",
    changed: "zmienione: {fields}",
  },
  export: {
    title: "Przekazanie",
    meta: "nogat-handoff/1",
    file: KIT.file,
    fileTitle: "Pobierz przekazanie nogat-handoff/1 (dane, ich pochodzenie i wynik do porównania)",
    copy: KIT.copyTo("hydrolog"),
    copyTitle: "Skopiuj przekazanie nogat-handoff/1 do schowka",
    copied: KIT.copied,
    copyByHand: KIT.copyByHand,
    copyLabel: "Przekazanie nogat-handoff/1 (JSON) do skopiowania",
    saved: KIT.saved,
    standalone: `Samodzielnie: przez plik albo schowek; wczytasz go z powrotem w Hydrologu przyciskiem „${KIT.loadFrom("hydrograf")}”, np. w innej przeglądarce.`,
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
