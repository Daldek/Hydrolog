// Numbers and texts for people, in Polish: a decimal comma, a non-breaking space between
// thousands from five digits (Intl.NumberFormat "pl-PL") and the minus sign U+2212, as the
// charts write them. The GUI formats what Hydrolog computed; it never computes a
// hydrological value itself.

const LOCALE = "pl-PL";
const MINUS = "\u2212";
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
      // "min2": no separator in 1234, one in 12 345 (`true` means "always" in Intl v3).
      useGrouping: grouping ? "min2" : false,
    });
    formats.set(key, found);
  }
  return found;
}

/**
 * Format a number with a fixed count of decimals: num(60.2148, 2) gives "60,21",
 * num(-3.5, 1) "−3,5"; a negative number rounded to zero has no sign.
 *
 * @param {number|null|undefined} value the number
 * @param {number} [digits=2] decimals
 * @returns {string} the text, "–" for a missing or non-finite value
 */
export function num(value, digits = 2) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "–";
  const text = formatter(Math.max(0, Math.min(10, digits)), true).format(value);
  return text.replace("-", MINUS).replace(/^\u2212(0(,0*)?)$/, "$1");
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
 * A typed number as headers and notes show it: at most `digits` decimals, written as in a
 * field. A value handed over exactly reads short, roundedText("360,68819771080604", 1)
 * gives "360,7", while the field and the run keep it whole; roundedText("120", 1) stays
 * "120".
 *
 * @param {string|number|null|undefined} text the number as typed
 * @param {number} digits the most decimals shown
 * @returns {string} the text, as typed when it is no number
 */
export function roundedText(text, digits) {
  const value = parseNumber(text);
  if (value === null || Number.isNaN(value)) return String(text ?? "");
  return inputText(Number(value.toFixed(digits)));
}

/**
 * A number in its shortest exact form, written as num writes it (a decimal comma, thousands
 * grouped): exact(70000) gives "70 000", exact(0.002) "0,002".
 *
 * @param {number} value the number
 * @returns {string} the text, "–" for a missing value
 */
export function exact(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "–";
  const rounded = Number(value.toPrecision(12));
  const decimals = (String(rounded).split(".")[1] || "").length;
  return num(rounded, Math.min(decimals, 10));
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
