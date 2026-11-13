/**
 * Notices of results in Polish (plan D16): one text per stable code of Hydrolog's NOTICES
 * registry, filled from the notice's `details`. A text with values has a plain form for a
 * notice without them (`route network` gives its nodes' notices only `node_id`), and may
 * name the codes a detail holds (`names`: detail -> code -> Polish name). A contract test
 * fails for a code without a text here; a code the GUI does not know shows the English
 * message marked „(EN)”.
 */

import { auto } from "../format.js";
import { common, t } from "./common.js";
import { statystyka } from "./statystyka.js";

/**
 * The distributions and fit methods of flood frequency named as Statystyka names them:
 * „Rozkład log-normalny dopasowany metodą L-momentów”.
 */
const FREQUENCY_NAMES = {
  distribution: Object.fromEntries(Object.entries(statystyka.distributions).map(([code, item]) => [code, item.name])),
  fit_method: Object.fromEntries(Object.entries(statystyka.fitMethods).map(([code, item]) => [code, item.by])),
};

export const notices = {
  none: "Brak uwag Hydrologa (notices: 0).",
  node: "Węzeł {node_id}: {text}",
  codes: {
    // Runs of the GUI's server
    superseded: "Nowsze obliczenie tego samego kanału zastąpiło to obliczenie.",
    timeout: { text: "Obliczenie przerwano po {timeout_s} s: trwało za długo.", plain: "Obliczenie przerwano: trwało za długo." },
    // Third-party warnings without a code of their own: the English text follows
    user_warning: "Ostrzeżenie biblioteki: {message}",
    runtime_warning: "Ostrzeżenie obliczeń numerycznych: {message}",
    // Routing models (the emitter's own English text; no values)
    tail_extended: "Wynik wydłużono, aby fala zdążyła odpłynąć z odcinka.",
    tail_truncated: "Wynik obcięto na końcu okresu obliczeń: fala nie odpłynęła w całości.",
    lag_interpolated: "Opóźnienie nie jest wielokrotnością kroku czasowego: odpływ interpolowano.",
    timestep_refined: "Krok czasowy zagęszczono, aby metoda Muskingum-Cunge była dokładna.",
    substeps_added: "Dodano kroki pośrednie, aby obliczenie było stabilne.",
    subreaches_adjusted: "Zmieniono liczbę pododcinków, aby obliczenie było stabilne.",
    accuracy_limit: "Przy tych parametrach dokładność metody jest ograniczona.",
    diffusion_dominated:
      "Metoda Muskingum-Cunge nie daje przy tym kroku nieujemnych wag dla żadnego podziału odcinka: odcinek trasowano jako " +
      "zbiorniki liniowe (ich liczba n i stała K są w parametrach odcinka); wynik jest przybliżony.",
    // Operations
    missing_values_removed: {
      text: "Usunięto {missing} z {total} wartości bez danych (pierwsza: {first_date}).",
      plain: "Usunięto z szeregu wartości bez danych.",
    },
    missing_pairs_removed: {
      text: "Usunięto {missing} z {total} par z brakującą wartością.",
      plain: "Usunięto pary z brakującą wartością.",
    },
    condition_defaulted: {
      text: "Nie podano stanu hydrologicznego dla {land_cover}: przyjęto „fair”.",
      plain: "Nie podano stanu hydrologicznego: przyjęto „fair”.",
    },
    condition_ignored: {
      text: "Pokrycie {land_cover} nie zależy od stanu hydrologicznego: pominięto „{condition}”.",
      plain: "Pominięto stan hydrologiczny: to pokrycie od niego nie zależy.",
    },
    tc_not_used: {
      text: "Model {uh_model} nie używa czasu koncentracji: tc = {tc_min} min pominięto.",
      plain: "Ten model hydrogramu jednostkowego nie używa czasu koncentracji.",
    },
    slopes_from_relief: {
      text: "Spadek {option}: podano {given_m_per_m} m/m, z rzeźby terenu wynika {computed_m_per_m} m/m.",
      plain: "Spadki porównano z rzeźbą terenu.",
    },
    mean_elevation_approximated: "Średnią wysokość zlewni przybliżono z wysokości najmniejszej i największej.",
    channel_length_defaulted: "Długość cieku głównego przyjęto równą długości zlewni.",
    duration_not_covered: {
      text: "Czas trwania {duration_min} min nie jest wielokrotnością kroku {timestep_min} min: hietogram ma {steps} kroków ({covered_min} min).",
      plain: "Opad nie pokrywa całego czasu trwania obliczeń.",
    },
    stations_without_polygon: {
      text: "Pominięto posterunki bez wieloboku Thiessena: {stations}.",
      plain: "Pominięto posterunki bez wieloboku Thiessena.",
    },
    pmaxtp_attribution: {
      text: "Wysokość opadu pochodzi z atlasu PMAXTP IMGW-PIB: jej źródło i warunki korzystania z danych są w części „Źródła danych” pod wynikiem (regulamin: {terms_url}).",
      plain: "Wysokość opadu pochodzi z atlasu PMAXTP IMGW-PIB: jej źródło i warunki korzystania z danych są w części „Źródła danych” pod wynikiem.",
    },
    ia_coefficient_nonstandard: {
      text: "λ = {ia_coefficient} różni się od 0,2, wartości, dla której skalibrowano tablice CN.",
      plain: "Współczynnik λ różni się od 0,2, wartości, dla której skalibrowano tablice CN.",
    },
    empty_area: "Obszar nie zawiera komórek rastra HSG z danymi.",
    incomplete_years: {
      text: "Pominięto {skipped} z {total} lat z niepełnymi danymi: {years}.",
      plain: "Pominięto lata z niepełnymi danymi.",
    },
    single_value_month: {
      text: "Miesiące z jedną wartością, bez przedziału ufności: {months}.",
      plain: "Niektóre miesiące mają jedną wartość: bez przedziału ufności.",
    },
    large_result: {
      text: "Duży wynik: {size_chars} znaków (strona: {page_chars}).",
      plain: "Duży wynik.",
    },
    outside_typical_range: {
      text: "{method}: {parameter} = {value} poza typowym zakresem od {minimum} do {maximum}.",
      plain: "Parametr metody poza typowym zakresem.",
    },
    outside_unverified_range: {
      text: "{method}: {parameter} = {value} poza typowym zakresem od {minimum} do {maximum}; zakres bez opublikowanego źródła, do weryfikacji.",
      plain: "Parametr metody poza typowym zakresem, który czeka na weryfikację.",
    },
    small_sample: {
      text: "Mała próba: {years} lat (zalecane co najmniej {minimum}).",
      plain: "Mała próba: wynik jest niepewny.",
    },
    short_record: {
      text: "Liczba lat w szeregu: {years}; KZGW (2017) wymaga co najmniej {minimum} lat danych do analizy częstości wezbrań.",
      plain: "Szereg jest krótszy, niż KZGW (2017) wymaga do analizy częstości wezbrań.",
    },
    ks_test_approximate: "Wartości krytyczne testu Kołmogorowa-Smirnowa są nieważne, gdy parametry szacuje się z tych samych danych; wybieraj rozkład wg A² i AIC.",
    distribution_left_out: {
      text: "Rozkład {distribution} pominięty: metoda {fit_method} nie daje jego parametrów dla tej próby ({reason}).",
      plain: "Wybrana metoda nie daje parametrów jednego z rozkładów; pominięto go.",
      names: FREQUENCY_NAMES,
    },
    outside_support: {
      text: "Rozkład {distribution} dopasowany metodą {fit_method} nie obejmuje maksimów {values}: jego AIC jest nieokreślone, rozkład jest na końcu rankingu.",
      plain: "Dopasowany rozkład nie obejmuje wszystkich maksimów: jego AIC jest nieokreślone.",
      names: FREQUENCY_NAMES,
    },
    homogeneity_rejected: {
      text: "Testy odrzucające jednorodność ciągu przy α = {alpha}: {tests}.",
      plain: "Test odrzuca jednorodność ciągu.",
      names: { tests: { mann_whitney: "Mann-Whitney", kolmogorov_smirnov: "Kołmogorow-Smirnow", pettitt: "Pettitt" } },
    },
    short_reference_period: {
      text: "Okres odniesienia {first_year}–{last_year} ma {years} lat z danymi; zalecane jest co najmniej {minimum} lat.",
      plain: "Okres odniesienia jest krótszy niż zalecane 30 lat.",
    },
    normal_not_computed: {
      text: "Normalna okresu {first_year}–{last_year} wymaga wartości rocznych w {required} latach, a ma je {years} (WMO-No. 1203): normalna i procenty normalnej są puste.",
      plain: "Za mało lat z wartościami rocznymi na normalną (WMO-No. 1203).",
    },
    accumulated_totals: {
      text: "{count} wartości kolumny {column} to sumy dni bez pomiaru przed nimi: w sumach miesięcznych zastępują te dni, w statystykach dobowych są brakami.",
      plain: "Niektóre wartości opadu to sumy z kilku dni bez pomiaru.",
    },
    spi_not_fitted: {
      text: "Sumy {scale_months}-miesięczne miesięcy {months} nie mają dopasowanego rozkładu gamma (sumy w mniej niż 80% lat lub mniej niż 3 dodatnie): ich SPI jest puste.",
      plain: "Dla niektórych miesięcy nie dopasowano rozkładu SPI.",
    },
    years_with_missing_days: {
      text: "{count} z {total} lat hydrologicznych ma dni bez danych; ich wartości skrajne weszły do obliczeń i mogą być łagodniejsze od rzeczywistych: {years}.",
      plain: "Niektóre lata mają dni bez danych; ich wartości skrajne mogą być łagodniejsze od rzeczywistych.",
    },
    short_years_left_out: {
      text: "{count} lat hydrologicznych okresu ma mniej niż {minimum} dni z danymi do obliczeń i nie ma własnych wartości: {years}.",
      plain: "Niektóre lata mają za mało dni z danymi, by mieć własne wartości.",
    },
    undated_extremes: {
      text: "{count} ekstremów rocznych nie ma daty w pliku półroczy i pominięto je: {years}.",
      plain: "Ekstrema roczne bez daty pominięto.",
    },
    unknown_hietogram_type: {
      text: "Nieznany typ hietogramu {hietogram_type}; dozwolone: {allowed}.",
      plain: "Nieznany typ hietogramu.",
    },
    uh_model_mismatch: {
      text: "Model hydrogramu jednostkowego {uh_model} różni się od użytego w wyniku: {result_uh_model}.",
      plain: "Model hydrogramu jednostkowego różni się od użytego w wyniku.",
    },
    positions_ignored: {
      text: "{reason}; schemat ułożono automatycznie, bez podanych położeń węzłów.",
      plain: "Podanych położeń węzłów nie użyto: schemat ułożono automatycznie.",
      names: {
        reason: {
          partial: "nie ma położenia, choć inne węzły je mają",
          shared_cell: "zajmuje tę samą komórkę siatki co inny węzeł",
        },
      },
    },
    exposed_without_auth: {
      text: "Serwer słucha na {host} bez logowania: udostępniaj {url} tylko za bramką z uwierzytelnianiem.",
      plain: "Serwer słucha poza komputerem bez logowania: udostępniaj go tylko za bramką z uwierzytelnianiem.",
    },
  },
};

/**
 * Whether a notice puts a value outside a two-sided typical range of Hydrolog: the code
 * `outside_typical_range`, or `outside_unverified_range` for a range to be verified
 * (`verified` false in the served `typical_ranges`).
 *
 * @param {{code?: string}|null} notice a notice of hydrolog-result/1
 * @returns {boolean} true for either code
 */
export function isRangeNotice(notice) {
  return Boolean(notice) && (notice.code === "outside_typical_range" || notice.code === "outside_unverified_range");
}

/**
 * A detail value in a notice: numbers in Polish with four significant digits and no
 * trailing zeros („0,082”, not „0,08200”), lists joined.
 *
 * @param {unknown} value the value
 * @returns {string} the text
 */
export function noticeValue(value) {
  if (typeof value === "number") return auto(value).replace(/(,\d*?)0+$/, "$1").replace(/,$/, "");
  if (Array.isArray(value)) return value.map(noticeValue).join(", ");
  return String(value);
}

/**
 * A detail value with its codes named: each code `names` holds, the value or an item of a
 * list, becomes its Polish name.
 *
 * @param {Object<string, string>|undefined} names the names of the detail's codes
 * @param {unknown} value the value
 * @returns {unknown} the value with its codes named
 */
function named(names, value) {
  if (!names) return value;
  const name = (item) => (typeof item === "string" && Object.hasOwn(names, item) ? names[item] : item);
  return Array.isArray(value) ? value.map(name) : name(value);
}

/**
 * Word a notice of a result in Polish.
 *
 * @param {{level?: string, code?: string, message?: string, details?: object}} notice a
 *   notice of hydrolog-result/1
 * @returns {{text: string, english: boolean}} the sentence and whether it carries the
 *   English message
 */
export function describeNotice(notice) {
  const code = notice && notice.code;
  const entry = code && Object.hasOwn(notices.codes, code) ? notices.codes[code] : null;
  const message = (notice && notice.message) || "";
  if (!entry) return { text: `${message} ${common.english}`.trim(), english: true };
  const details = (notice && notice.details) || {};
  const values = { message };
  const names = (typeof entry === "object" && entry.names) || {};
  for (const [key, value] of Object.entries(details)) values[key] = noticeValue(named(names[key], value));
  const full = typeof entry === "string" ? entry : entry.text;
  const needed = [...full.matchAll(/\{(\w+)\}/g)].map((match) => match[1]);
  const template = needed.every((key) => Object.hasOwn(values, key)) ? full : entry.plain || full;
  const english = template.includes("{message}");
  let text = t(template, values);
  if (english) text = `${text} ${common.english}`;
  if (Object.hasOwn(details, "node_id")) text = t(notices.node, { node_id: noticeValue(details.node_id), text });
  return { text, english };
}
