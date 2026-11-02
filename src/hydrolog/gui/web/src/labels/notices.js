/**
 * Notices of results in Polish (plan D16): one text per stable code of Hydrolog's NOTICES
 * registry, filled from the notice's `details`. A text with values has a plain form for a
 * notice without them (`route network` gives its nodes' notices only `node_id`). A
 * contract test fails for a code without a text here; a code the GUI does not know shows
 * the English message marked „(EN)”.
 */

import { auto } from "../format.js";
import { common, t } from "./common.js";

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
    small_sample: {
      text: "Mała próba: {years} lat (zalecane co najmniej {minimum}).",
      plain: "Mała próba: wynik jest niepewny.",
    },
    short_record: {
      text: "Krótki okres obserwacji: {years} lat (zalecane co najmniej {minimum}).",
      plain: "Krótki okres obserwacji.",
    },
    ks_test_approximate: "Test Kołmogorowa-Smirnowa jest przybliżony: parametry dopasowano z tej samej próby.",
    unknown_hietogram_type: {
      text: "Nieznany typ hietogramu {hietogram_type}; dozwolone: {allowed}.",
      plain: "Nieznany typ hietogramu.",
    },
    uh_model_mismatch: {
      text: "Model hydrogramu jednostkowego {uh_model} różni się od użytego w wyniku: {result_uh_model}.",
      plain: "Model hydrogramu jednostkowego różni się od użytego w wyniku.",
    },
    exposed_without_auth: {
      text: "Serwer słucha na {host} bez logowania: udostępniaj {url} tylko za bramką z uwierzytelnianiem.",
      plain: "Serwer słucha poza komputerem bez logowania: udostępniaj go tylko za bramką z uwierzytelnianiem.",
    },
  },
};

/**
 * A detail value in a notice: numbers in Polish, lists joined.
 *
 * @param {unknown} value the value
 * @returns {string} the text
 */
function shown(value) {
  if (typeof value === "number") return auto(value);
  if (Array.isArray(value)) return value.map(shown).join(", ");
  return String(value);
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
  for (const [key, value] of Object.entries(details)) values[key] = shown(value);
  const full = typeof entry === "string" ? entry : entry.text;
  const needed = [...full.matchAll(/\{(\w+)\}/g)].map((match) => match[1]);
  const template = needed.every((key) => Object.hasOwn(values, key)) ? full : entry.plain || full;
  const english = template.includes("{message}");
  let text = t(template, values);
  if (english) text = `${text} ${common.english}`;
  if (Object.hasOwn(details, "node_id")) text = t(notices.node, { node_id: shown(details.node_id), text });
  return { text, english };
}
