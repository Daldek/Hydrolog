// Numbers and texts for people, in Polish: a decimal comma and a non-breaking space between
// thousands from five digits (Intl.NumberFormat "pl-PL"). The GUI formats what Hydrolog
// computed; it never computes a hydrological value itself.

const LOCALE = "pl-PL";
const formats = new Map();

/**
 * Return a cached Intl.NumberFormat with fixed fraction digits.
 *
 * @param {number} digits fraction digits
 * @param {boolean} grouping whether thousands are separated
 * @returns {Intl.NumberFormat}
 */
function formatter(digits, grouping) {
  const key = `${digits}|${grouping}`;
  let found = formats.get(key);
  if (!found) {
    found = new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      useGrouping: grouping,
    });
    formats.set(key, found);
  }
  return found;
}

/**
 * Format a number with a fixed count of decimals: num(60.2148, 2) gives "60,21".
 *
 * @param {number|null|undefined} value the number
 * @param {number} [digits=2] decimals
 * @returns {string} the text, "–" for a missing or non-finite value
 */
export function num(value, digits = 2) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "–";
  return formatter(Math.max(0, Math.min(10, digits)), true).format(value);
}

/**
 * Decimals that show a number with `significant` significant digits (no fewer than 0).
 *
 * @param {number} value the number
 * @param {number} [significant=4] significant digits
 * @returns {number} the count of decimals
 */
export function decimalsFor(value, significant = 4) {
  const size = Math.abs(value);
  if (!Number.isFinite(size) || size === 0) return 0;
  const exponent = Math.floor(Math.log10(size));
  return Math.max(0, Math.min(10, significant - 1 - exponent));
}

/**
 * Format a number with four significant digits, whole numbers as whole numbers:
 * auto(60.2148) gives "60,21", auto(0.26778) "0,2678", auto(1046213.2) "1 046 213",
 * auto(30) "30".
 *
 * @param {number|null|undefined} value the number
 * @param {number} [significant=4] significant digits
 * @returns {string} the text, "–" for a missing or non-finite value
 */
export function auto(value, significant = 4) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "–";
  if (Number.isInteger(value)) return num(value, 0);
  return num(value, decimalsFor(value, significant));
}

/**
 * Parse a number typed by a person: a comma or a dot as the decimal separator, spaces
 * between thousands, a minus or the sign "−".
 *
 * @param {string|number|null|undefined} text what was typed
 * @returns {number|null} the number, null for an empty text, NaN for anything else
 */
export function parseNumber(text) {
  if (typeof text === "number") return Number.isFinite(text) ? text : Number.NaN;
  if (text === null || text === undefined) return null;
  const compact = String(text)
    .replace(/[\s\u00a0\u202f]/g, "")
    .replace(/\u2212/g, "-")
    .replace(",", ".");
  if (compact === "") return null;
  if (!/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(compact)) return Number.NaN;
  return Number(compact);
}

/**
 * Write a number into an input field: the shortest exact form with a decimal comma and
 * no grouping, inputText(0.0142) gives "0,0142".
 *
 * @param {number|null|undefined} value the number
 * @returns {string} the text, "" for a missing value
 */
export function inputText(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "";
  return String(value).replace(".", ",");
}

/**
 * Minutes as hours and minutes: hmm(380) gives "6:20".
 *
 * @param {number} minutes time [min]
 * @returns {string} "h:mm"
 */
export function hmm(minutes) {
  if (typeof minutes !== "number" || !Number.isFinite(minutes)) return "–";
  const whole = Math.round(Math.abs(minutes));
  const sign = minutes < 0 ? "−" : "";
  return `${sign}${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/**
 * A size in bytes for people: bytes(1234567) gives "1,2 MB".
 *
 * @param {number} size size [B]
 * @returns {string} the text
 */
export function bytes(size) {
  if (typeof size !== "number" || !Number.isFinite(size)) return "–";
  if (size < 1024) return `${num(size, 0)} B`;
  if (size < 1024 * 1024) return `${num(size / 1024, 1)} kB`;
  return `${num(size / (1024 * 1024), 1)} MB`;
}

/**
 * A count with the Polish plural form: plural(5, ["polecenie", "polecenia", "poleceń"])
 * gives "5 poleceń".
 *
 * @param {number} count the count
 * @param {[string, string, string]} forms one, few (2-4) and many
 * @returns {string} the count and the word
 */
export function plural(count, forms) {
  const tens = count % 100;
  const ones = count % 10;
  let word = forms[2];
  if (count === 1) word = forms[0];
  else if (ones >= 2 && ones <= 4 && (tens < 12 || tens > 14)) word = forms[1];
  return `${num(count, 0)} ${word}`;
}

/**
 * Fold a text for searching: lower case, without diacritics ("Łódź" gives "lodz").
 *
 * @param {string} text the text
 * @returns {string} the folded text
 */
export function fold(text) {
  return String(text)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ł/g, "l");
}
