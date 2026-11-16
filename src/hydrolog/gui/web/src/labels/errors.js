/**
 * Errors in Polish (plan D16): worded from the error's `code` and `details` (`option`,
 * `reason`, `allowed`, the bounds, `groups`), under the registry's Polish `title` that the
 * server sends; the English `message` is the fallback, marked „(EN)”. The checks of the
 * forms word their messages with the same functions, so a field says the same before and
 * after a run.
 */

import { bytes, inputText } from "../format.js";
import { common, t } from "./common.js";

export const errors = {
  reasons: {
    required: "Podaj wartość: opcja wymagana",
    number: "Podaj liczbę, np. {example}",
    integer: "Podaj liczbę całkowitą",
    string: "Podaj tekst",
    boolean: "Podaj tak albo nie",
    array: "Podaj listę wartości",
    object: "Podaj obiekt JSON",
    type: "Nieprawidłowy rodzaj wartości",
    not_finite: "Podaj liczbę skończoną",
    minimum: "Najmniej {minimum} (podano {value})",
    maximum: "Najwyżej {maximum} (podano {value})",
    exclusive_minimum: "Musi być większa od {exclusive_minimum} (podano {value})",
    choice: "Dozwolone wartości: {allowed}",
    empty: "Nie może być puste",
    invalid_path: "Nieprawidłowa ścieżka pliku",
    unknown_option: "Nieznana opcja tego polecenia",
    one_of: "Podaj dokładnie jedną kompletną grupę: {groups}",
    one_of_missing: "Podaj dokładnie jedną kompletną grupę: {groups}; brakuje: {missing}",
    one_of_several: "Podano kilka grup naraz; zostaw jedną: {groups}",
    no_check: "To polecenie tylko czyta: nie ma trybu planu",
    json: "Nieprawidłowy JSON: {message}",
    json_kind: "Oczekiwano {kind} JSON",
    item: "Wartość {index}: {message}",
    not_a_number: "Wartość {index} („{text}”) nie jest liczbą",
    requires: "Podaj też: {names}",
    excludes: "Nie łącz z: {names}",
    date: "Podaj datę w formacie RRRR-MM-DD",
    "date-time": "Podaj datę i godzinę w formacie RRRR-MM-DDTgg:mm",
    file_name: "Nazwa pliku: litery, cyfry, kropka, myślnik, podkreślenie lub spacja, do 128 znaków",
    forbidden_path: "Plik musi leżeć w katalogu sesji (in/… albo out/…)",
    outside_session: "Plik musi leżeć w katalogu sesji (in/… albo out/…)",
    output_area: "Plik wynikowy zapisuje się tylko w out/",
    cross_site: "Żądanie z innej strony zostało odrzucone",
    too_large: "Za duże: najwięcej {limit}",
    session_full: "Sesja jest pełna: usuń niepotrzebne pliki",
    content_type: "Serwer przyjmuje tylko dane JSON",
    invalid_json: "Nieprawidłowy JSON żądania",
    too_long: "Za długie: najwięcej {max_length} znaków",
    feedback_store_failed: "Nie udało się zapisać zgłoszenia. Spróbuj ponownie później.",
    outside_pmaxtp: "Punkt poza atlasem PMAXTP: podaj punkt w Polsce, nie na morzu",
    timeout: "{source} nie odpowiedział na czas: spróbuj ponownie później",
    network: "Brak połączenia z {source}: sprawdź sieć i spróbuj ponownie",
    http_status: "{source} odpowiedział błędem HTTP {status}: spróbuj ponownie później",
  },
  /** The sources of data an error of `source_unavailable` names (`details.source`). */
  sources: { "imgw-pmaxtp": "IMGW-PIB" },
  kinds: { object: "obiektu", array: "listy" },
  statuses: {
    0: "Brak połączenia z serwerem Hydrologa",
    400: "Nieprawidłowe dane wejściowe",
    403: "Operacja niedozwolona",
    404: "Nie znaleziono",
    409: "Konflikt stanu",
    413: "Za duży plik lub żądanie",
    415: "Nieobsługiwany rodzaj danych",
    500: "Błąd serwera Hydrologa",
  },
  formTitle: "Błędy formularza",
  aboveForm: "Hydrolog odrzucił dane",
  countForms: ["błąd", "błędy", "błędów"],
  count: "{count}: popraw pola oznaczone na czerwono",
  formOk: "formularz poprawny",
  formIncomplete: "uzupełnij pola wymagane",
};

/**
 * A short Polish title for an HTTP status without an error document.
 *
 * @param {number} status HTTP status, 0 when the server was not reached
 * @returns {string} the title
 */
export function errorTitleForStatus(status) {
  if (Object.hasOwn(errors.statuses, status)) return errors.statuses[status];
  return status >= 500 ? errors.statuses[500] : `HTTP ${status}`;
}

/**
 * A number in a message, as a person types it ("0,0142").
 *
 * @param {unknown} value the number
 * @returns {string} the text
 */
function shown(value) {
  return typeof value === "number" ? inputText(value) : String(value);
}

/**
 * A list of option names or groups in a message.
 *
 * @param {unknown} items names, or groups of names
 * @returns {string} "a, b" or "a + b albo c"
 */
function listed(items) {
  if (!Array.isArray(items)) return String(items ?? "");
  if (items.some(Array.isArray)) {
    return items.map((group) => (Array.isArray(group) ? group.join(" + ") : group)).join(" albo ");
  }
  return items.join(", ");
}

/**
 * The Polish sentence of a validation reason (the catalog's `details.reason`).
 *
 * @param {string} reason e.g. "maximum"
 * @param {object} [details] the error's details: bounds, value, allowed, groups, missing…
 * @returns {string|null} the sentence, null for a reason the GUI does not word
 */
export function reasonText(reason, details = {}) {
  const r = errors.reasons;
  let text = null;
  switch (reason) {
    case "required":
    case "not_finite":
    case "empty":
    case "invalid_path":
    case "unknown_option":
    case "no_check":
    case "outside_session":
    case "output_area":
    case "cross_site":
    case "session_full":
    case "content_type":
    case "invalid_json":
    case "feedback_store_failed":
    case "outside_pmaxtp":
      text = r[reason];
      break;
    case "timeout":
    case "network":
    case "http_status":
      // A source the GUI does not name keeps the English message
      if (!Object.hasOwn(errors.sources, details.source)) return null;
      text = t(r[reason], { source: errors.sources[details.source], status: shown(details.status ?? "–") });
      break;
    case "too_long":
      text = t(r.too_long, { max_length: shown(details.max_length) });
      break;
    case "too_large":
      text = t(r.too_large, { limit: typeof details.limit_bytes === "number" ? bytes(details.limit_bytes) : "–" });
      break;
    case "minimum":
    case "maximum":
    case "exclusive_minimum":
      text = t(r[reason], {
        [reason]: shown(details[reason]),
        value: shown(details.value),
      });
      break;
    case "choice":
      text = t(r.choice, { allowed: listed(details.allowed) });
      break;
    case "type": {
      const expected = String(details.expected || "");
      if (expected === "number") text = t(r.number, { example: "14,78" });
      else if (Object.hasOwn(r, expected)) text = r[expected];
      else text = r.type;
      break;
    }
    case "one_of": {
      const groups = listed(details.groups);
      if (Array.isArray(details.missing) && details.missing.length) {
        text = t(r.one_of_missing, { groups, missing: details.missing.join(", ") });
      } else if (Array.isArray(details.missing)) {
        text = t(r.one_of, { groups });
      } else {
        text = t(r.one_of_several, { groups });
      }
      break;
    }
    default:
      return null;
  }
  if (typeof details.index === "number" && reason !== "one_of") {
    return t(r.item, { index: details.index + 1, message: text });
  }
  return text;
}

/**
 * Word an error document of the server in Polish.
 *
 * @param {{code?: string, title?: string, message?: string, details?: object}} doc a
 *   hydrolog-error/1 document (or the stand-in of api.js)
 * @returns {{option: string|null, reason: string|null, title: string, text: string,
 *   english: boolean}} the option the error belongs to (null: it stands above the form),
 *   its reason, the Polish title, the sentence, and whether the sentence is the English
 *   message
 */
export function describeError(doc) {
  const details = (doc && doc.details) || {};
  const option = typeof details.option === "string" ? details.option : null;
  const reason = typeof details.reason === "string" ? details.reason : null;
  let text = reason ? reasonText(reason, details) : null;
  if (!text && doc && doc.code === "forbidden" && option) text = errors.reasons.forbidden_path;
  const english = !text;
  if (!text) text = (doc && (doc.message || doc.title)) || "";
  return {
    option,
    reason,
    title: (doc && doc.title) || errorTitleForStatus(400),
    text: english && text ? `${text} ${common.english}` : text,
    english,
  };
}
