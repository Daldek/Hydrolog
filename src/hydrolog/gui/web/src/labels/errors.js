/**
 * Errors in Polish (plan D16): worded from the error's `code` and `details` (`option`,
 * `reason`, `allowed`, the bounds, `groups`), under the registry's Polish `title` that the
 * server sends; the English `message` is the fallback, marked „(EN)”. The checks of the
 * forms word their messages with the same functions, so a field says the same before and
 * after a run. An error of the depth-duration curve of Euler II (`depth_duration_mm`, also
 * a rainfall's field of a network document) is worded as the curve's. A refused constraint
 * of a formula (`details.constraint`) the GUI knows is worded by its name (constraints);
 * one that names no option stands on the input the constraint asks to change
 * (CONSTRAINT_OPTIONS).
 */

import { bytes, inputText, num } from "../format.js";
import { common, t } from "./common.js";

/** The option, and the field of a rainfall of a network, of Euler II's depth-duration curve. */
const CURVE = "depth_duration_mm";

/**
 * The option a refused constraint of a formula stands on, by `details.constraint`, when
 * the refusal names none: the input the constraint asks to change. Lutz's constraints name
 * theirs (`uh nash` and NashIUH.from_lutz), Kerby–Kirpich's condition between its inputs
 * and the texture's positive total of clay, sand and silt (`soil texture`) do not.
 */
const CONSTRAINT_OPTIONS = Object.freeze({
  flow_path_longer_than_overland: "flow_path_length_km",
  positive_total: "clay",
});

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
    exclusive_maximum: "Musi być mniejsza od {exclusive_maximum} (podano {value})",
    choice: "Dozwolone wartości: {allowed}",
    outside_physical_range: "Wartość {value} jest poza zakresem fizycznym {range}",
    outside_physical_constraint: "Niespełniony warunek fizyczny: {text}",
    precondition_failed: "Niespełniony warunek stosowalności wzoru: {text}",
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
    not_multiple: "Czas trwania musi być wielokrotnością kroku Δt = {timestep} min: hietogram składa się z całych kroków",
    total_mismatch: "Euler II ma sumę równą wysokości krzywej wysokość–czas trwania dla {duration} min: {depth} mm",
  },
  /** The sentences of the refused constraints of the formulas, by `details.constraint`. */
  constraints: {
    flow_path_longer_than_overland:
      "Długość najdłuższej drogi spływu musi być większa od długości spływu po stoku: Kerby–Kirpich liczy resztę drogi jako przepływ korytem",
    centroid_within_length:
      "Długość do środka ciężkości Lc nie może być większa od długości cieku L: obie biegną wzdłuż cieku głównego od przekroju zamykającego, Lc do punktu najbliższego środka ciężkości zlewni, L do działu wodnego",
    shares_within_catchment:
      "Udział terenów zurbanizowanych i udział lasów razem nie mogą przekroczyć 100 % powierzchni zlewni",
    within_reach:
      "Powierzchnia zlewni nie może być większa od pola koła o promieniu równym długości zlewni L (A ≤ πL²): cała zlewnia leży nie dalej niż L od przekroju zamykającego",
    isoperimetric:
      "Obwód zlewni nie może być krótszy od obwodu koła o tej samej powierzchni (P² ≥ 4πA): powierzchnia i obwód pochodzą wtedy z różnych obrysów zlewni",
    rises_above_outlet:
      "Najwyższy punkt zlewni musi leżeć wyżej niż przekrój zamykający (Hmax > Hmin): woda spływa do przekroju",
    positive_total:
      "Zawartości iłu, piasku i pyłu nie mogą być wszystkie zerowe: klasa uziarnienia wynika z udziałów frakcji w ich sumie",
    start_below_levels:
      "Początkowe H₀ musi być niższe od najniższego stanu wody z pomiarów, w tej samej jednostce",
    levels_not_all_equal:
      "Wszystkie stany wody są równe: z takich par nie da się wyznaczyć wykładnika b ani stanu zerowego przepływu H₀",
    discharges_not_all_equal:
      "Wszystkie przepływy są równe: przepływ, który nie zmienia się ze stanem, nie wyznacza krzywej przepływu",
    least_squares_minimum:
      "Metoda najmniejszych kwadratów nie ma dla tych par minimum: przepływ rośnie ze stanem jak funkcja wykładnicza, a nie potęgowa (np. pary dwóch krzywych przepływu po przesunięciu zera wodowskazu albo zmianie koryta); dopasuj krzywą do lat jednej krzywej",
  },
  /** The sentences of the errors of Euler II's depth-duration curve, by `details.reason`. */
  curve: {
    required: "Euler II buduje się z krzywej wysokość–czas trwania jednego p (np. wysokości PMAXTP kolejnych czasów trwania), a jej nie podano",
    type: "Krzywa wysokość–czas trwania to obiekt: czas trwania [min] → wysokość [mm]",
    depthType: "Krzywa wysokość–czas trwania: wysokość dla {duration} min nie jest liczbą",
    empty: "Krzywa wysokość–czas trwania nie ma żadnego punktu",
    invalid_duration: "Krzywa wysokość–czas trwania: czas „{value}” nie jest liczbą minut większą od 0",
    duplicate_duration: "Krzywa wysokość–czas trwania: czas {duration} min podano dwa razy",
    not_finite: "Krzywa wysokość–czas trwania: wysokość dla {duration} min nie jest liczbą skończoną",
    minimum: "Krzywa wysokość–czas trwania: wysokość dla {duration} min jest ujemna",
    decreasing: "Krzywa wysokość–czas trwania nie może maleć: {first} mm dla {from} min, a {second} mm dla {to} min",
    before:
      "Krzywa wysokość–czas trwania zaczyna się od {first} min, a pierwszy blok potrzebuje wysokości dla {duration} min: krok Δt nie może być krótszy (nic nie jest ekstrapolowane)",
    after: "Krzywa wysokość–czas trwania kończy się na {last} min, a opad trwa {duration} min: nic nie jest ekstrapolowane",
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
 * The physical range of a refused value, as `details.range` of the formula
 * standard gives it (null for an unbounded end).
 *
 * @param {{low?: number|null, high?: number|null, low_inclusive?: boolean, high_inclusive?: boolean}|undefined} range
 * @returns {string} "[1; 100]" or "[0; ∞)"
 */
function physicalRange(range) {
  if (!range || typeof range !== "object") return "–";
  const low = typeof range.low === "number" ? shown(range.low) : "−∞";
  const high = typeof range.high === "number" ? shown(range.high) : "∞";
  return `${range.low_inclusive ? "[" : "("}${low}; ${high}${range.high_inclusive ? "]" : ")"}`;
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
 * The Polish sentence of a refused constraint of a formula: its own (errors.constraints),
 * else `template` with the library's statement of the condition.
 *
 * @param {object} details the error's details: `constraint` and its `text`
 * @param {string} template the sentence of the reason, with {text}
 * @returns {string} the sentence
 */
function constraintText(details, template) {
  const name = details.constraint;
  if (typeof name === "string" && Object.hasOwn(errors.constraints, name)) return errors.constraints[name];
  return t(template, { text: String(details.text || details.constraint || "–") });
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
    case "exclusive_maximum":
      text = t(r[reason], {
        [reason]: shown(details[reason]),
        value: shown(details.value),
      });
      break;
    case "choice":
      text = t(r.choice, { allowed: listed(details.allowed) });
      break;
    case "outside_physical_range":
      text =
        typeof details.constraint === "string"
          ? constraintText(details, r.outside_physical_constraint)
          : t(r.outside_physical_range, {
              value: typeof details.value === "number" ? shown(details.value) : String(details.value ?? "–"),
              range: physicalRange(details.range),
            });
      break;
    case "precondition_failed":
      text = constraintText(details, r.precondition_failed);
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
    case "not_multiple":
      text = t(r.not_multiple, { timestep: shown(details.timestep_min ?? "–") });
      break;
    case "total_mismatch":
      text = t(r.total_mismatch, {
        duration: shown(details.duration_min ?? "–"),
        depth: typeof details.depth_mm === "number" ? num(details.depth_mm, 2) : "–",
      });
      break;
    default:
      return null;
  }
  if (typeof details.index === "number" && reason !== "one_of") {
    return t(r.item, { index: details.index + 1, message: text });
  }
  return text;
}

/**
 * Whether an error is one of Euler II's depth-duration curve: it names the option
 * `depth_duration_mm`, or the field of that name of a rainfall of a network document.
 *
 * @param {object} details the error's details
 * @returns {boolean} true for an error of the curve
 */
export function isCurveError(details) {
  const field = typeof details.field === "string" ? details.field : "";
  return details.option === CURVE || field === CURVE || field.endsWith(`.${CURVE}`);
}

/**
 * The option an error belongs to: the one it names, else the input a refused constraint of
 * a formula asks to change (CONSTRAINT_OPTIONS).
 *
 * @param {object} details the error's details
 * @returns {string|null} the option, null for an error of no option (it stands above the form)
 */
export function errorOptionOf(details) {
  if (typeof details.option === "string") return details.option;
  const name = details.constraint;
  return typeof name === "string" && Object.hasOwn(CONSTRAINT_OPTIONS, name) ? CONSTRAINT_OPTIONS[name] : null;
}

/**
 * The Polish sentence of an error of Euler II's depth-duration curve, by its reason (a
 * network document's `missing_field` is the curve not given).
 *
 * @param {string} reason the error's `details.reason`
 * @param {object} details its details: the duration and the durations or depths it names
 * @returns {string|null} the sentence, null for a reason the GUI does not word
 */
function curveText(reason, details) {
  const c = errors.curve;
  const pair = (name) => (Array.isArray(details[name]) ? details[name] : []);
  const duration = shown(details.duration_min ?? "–");
  switch (reason) {
    case "required":
    case "missing_field":
      return c.required;
    case "empty":
      return c.empty;
    case "type":
      return typeof details.duration_min === "number" ? t(c.depthType, { duration }) : c.type;
    case "invalid_duration":
      return t(c.invalid_duration, { value: String(details.value ?? "–") });
    case "duplicate_duration":
    case "not_finite":
    case "minimum":
      return t(c[reason], { duration });
    case "decreasing": {
      const [from, to] = pair("durations_min");
      const [first, second] = pair("depths_mm");
      return t(c.decreasing, { from: shown(from ?? "–"), to: shown(to ?? "–"), first: shown(first ?? "–"), second: shown(second ?? "–") });
    }
    case "not_covered": {
      const [shortest, longest] = pair("durations_min");
      const before = typeof shortest === "number" && typeof details.duration_min === "number" && details.duration_min < shortest;
      return t(before ? c.before : c.after, { first: shown(shortest ?? "–"), last: shown(longest ?? "–"), duration });
    }
    default:
      return null;
  }
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
  const option = errorOptionOf(details);
  const reason = typeof details.reason === "string" ? details.reason : null;
  let text = null;
  if (reason) text = isCurveError(details) ? curveText(reason, details) : reasonText(reason, details);
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
