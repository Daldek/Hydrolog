// The lines the data providers' terms require on everything made with their data (Nogat
// DEV-20, ECO-060, ECO-065): the attribution lines of IMGW-PIB, PMAXTP and ČHMÚ and the
// links to IMGW-PIB's terms (PMAXTP's among them). The page never writes the lines
// itself: they come from the
// server, in the `attribution` and `terms_notice` of a result (hydrolog-result/1), of a
// hand-off (nogat-handoff/1), of a fetched PMAXTP depth, and, for the provider an older
// hand-off names without them, of GET api/session (`attribution`, every provider's set).
// A section keeps the lines of its sources and passes them as the command option
// `attribution` of every run made from those data, so the server answers the canonical
// lines; the views and exports then take the run's. On screen a view shows them in its one
// strip (ui/sources.js, Nogat ECO-064); Attribution writes them in full, the addresses as
// links, under a result for the print view; csvWithLines adds the
// columns of DEV-20.5 to a CSV, footerLines gives the rows drawn under a PNG
// (charts/png.js), linesFields the fields of a JSON document or hand-off.

import { useSession } from "./controls/file-field.js";
import { fold } from "./format.js";
import { html } from "./html.js";
import { attributionLabels as texts } from "./labels/attribution.js";

/** No lines: a product without provider data. */
export const NO_LINES = Object.freeze({ attribution: Object.freeze([]), terms_notice: Object.freeze([]) });

/** The CSV columns that hold lines, not data (DEV-20.5, Obserwator's two of its export). */
export const LINE_COLUMNS = Object.freeze(["attribution", "terms_notice", "attribution_source", "attribution_processed"]);

/** How the series of a hand-off without lines names its provider, by provider. */
const PROVIDER_NAMES = Object.freeze([
  { provider: "imgw", pattern: /^(imgw([-_ ]?pib)?|pl\.imgw(\..+)?)$/ },
  { provider: "chmi", pattern: /^(chmi|chmu|cz\.chmi(\..+)?)$/ },
]);

/** An address in a line (`https://…`), without the comma or bracket after it. */
const ADDRESS = /https?:\/\/[^\s),]*[^\s),.]/g;

/**
 * Whether a value is a JSON object (not an array, not null).
 *
 * @param {unknown} value the value
 * @returns {boolean} true for an object
 */
function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/**
 * The lines of a list: its non-blank strings, each once, verbatim.
 *
 * @param {unknown} value the list
 * @returns {string[]} the lines
 */
function strings(value) {
  return Array.isArray(value) ? [...new Set(value.filter((line) => typeof line === "string" && line.trim()))] : [];
}

/**
 * The lines a document carries: its `attribution` and `terms_notice` (a result, a hand-off
 * or its record, a fetched PMAXTP depth, a network document).
 *
 * @param {unknown} doc the document
 * @returns {{attribution: string[], terms_notice: string[]}} the lines, none when it has none
 */
export function linesOf(doc) {
  if (!isObject(doc)) return { attribution: [], terms_notice: [] };
  return { attribution: strings(doc.attribution), terms_notice: strings(doc.terms_notice) };
}

/**
 * Whether there are lines to show or carry.
 *
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines
 * @returns {boolean} true when any line is there
 */
export function hasLines(lines) {
  return Boolean(lines) && (lines.attribution.length > 0 || lines.terms_notice.length > 0);
}

/**
 * The lines of several sources: the union of each part, in their first order, each line
 * once; unknown (null) while a source's lines are not known yet (GET api/session pending).
 *
 * @param {...({attribution: string[], terms_notice: string[]}|null|undefined)} sets the
 *   lines of each source (undefined: none)
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines, null while one
 *   is unknown
 */
export function mergeLines(...sets) {
  if (sets.some((set) => set === null)) return null;
  const union = (field) => [...new Set(sets.flatMap((set) => (set ? set[field] : [])))];
  return { attribution: union("attribution"), terms_notice: union("terms_notice") };
}

/**
 * Lines in the order the providers' sets of GET api/session give (DEV-20.4: S, P, PS, PP,
 * M, C, CP; DEV-20.7: RD, RH, RK), a line the sets do not hold after them in its
 * first order: the order of lines merged in the page without a run of the server. A line
 * Nogat retired (ECO-065: H, N, „Regulamin: <address>”), kept with a depth or carried by
 * an older hand-off, becomes the line the session's `retired_lines` names, or goes.
 *
 * @param {{attribution: string[], terms_notice: string[]}} lines the lines
 * @param {object|null} session hydrolog-gui-session/1
 * @returns {{attribution: string[], terms_notice: string[]}} the lines in order
 */
export function orderLines(lines, session) {
  const sets = isObject(session) && isObject(session.attribution) ? Object.values(session.attribution) : [];
  const retired = isObject(session) && isObject(session.retired_lines) ? session.retired_lines : {};
  const current = (line) => (Object.hasOwn(retired, line) ? (retired[line] === null ? [] : [retired[line]]) : [line]);
  const sorted = (field) => {
    const order = [...new Set(sets.flatMap((set) => linesOf(set)[field]))];
    const rank = (line) => (order.includes(line) ? order.indexOf(line) : order.length);
    return [...new Set(lines[field].flatMap(current))].sort((a, b) => rank(a) - rank(b));
  };
  return { attribution: sorted("attribution"), terms_notice: sorted("terms_notice") };
}

/**
 * The value of the command option `attribution`: every attribution and terms line of the
 * data's sources (the server sorts them and adds what the providers' terms require).
 *
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines
 * @returns {string[]|null} the lines, null without any
 */
export function attributionOption(lines) {
  return hasLines(lines) ? [...new Set([...lines.attribution, ...lines.terms_notice])] : null;
}

/**
 * The options of a run with the option `attribution` of the data's lines, when there are.
 *
 * @param {object} options the options of the run
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines
 * @returns {object} the options
 */
export function withAttribution(options, lines) {
  const value = attributionOption(lines);
  return value ? { ...options, attribution: value } : options;
}

/**
 * The fields of a JSON document (a hand-off, a network, a record) that carry lines: each
 * only when it holds any (DEV-20.6, DEV-20.7).
 *
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines
 * @returns {{attribution?: string[], terms_notice?: string[]}} the fields
 */
export function linesFields(lines) {
  const fields = {};
  if (lines && lines.attribution.length) fields.attribution = [...lines.attribution];
  if (lines && lines.terms_notice.length) fields.terms_notice = [...lines.terms_notice];
  return fields;
}

/**
 * The lines of a provider's data as GET api/session gives them.
 *
 * @param {object|null} session hydrolog-gui-session/1, null while it has not arrived
 * @param {string} provider "imgw", "imgw_hydro", "pmaxtp" or "chmi"
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines, null while
 *   the session is not known
 */
export function providerLines(session, provider) {
  if (!isObject(session)) return null;
  const sets = isObject(session.attribution) ? session.attribution : {};
  return Object.hasOwn(sets, provider) ? linesOf(sets[provider]) : { attribution: [], terms_notice: [] };
}

/**
 * The provider a series names in its provenance (`series.provider`, `source` or `dataset`):
 * IMGW-PIB, „imgw-pib” or „pl.imgw.…” is IMGW-PIB's public data, CHMI, ČHMÚ or „cz.chmi.…”
 * ČHMÚ's.
 *
 * @param {unknown} provenance the provenance of a hand-off
 * @returns {"imgw"|"chmi"|null} the provider, null when none is named
 */
export function providerOf(provenance) {
  const series = isObject(provenance) && isObject(provenance.series) ? provenance.series : null;
  if (!series) return null;
  for (const key of ["provider", "source", "dataset"]) {
    if (typeof series[key] !== "string") continue;
    const name = fold(series[key].trim());
    const found = PROVIDER_NAMES.find((item) => item.pattern.test(name));
    if (found) return found.provider;
  }
  return null;
}

/**
 * The lines of a received hand-off (its record or the document): its own, else, for an
 * older hand-off without them, the set of the provider its series names (providerOf) from
 * GET api/session.
 *
 * @param {object} record the hand-off or what a section keeps of it (receivedOf)
 * @param {object|null} session hydrolog-gui-session/1, null while it has not arrived
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines (none when it
 *   names no provider), null while the session they need is not known
 */
export function receivedLines(record, session) {
  const own = linesOf(record);
  if (hasLines(own)) return own;
  const provider = isObject(record) ? providerOf(record.provenance) : null;
  return provider ? providerLines(session, provider) : own;
}

/**
 * A cell of a CSV file: quoted when it holds a comma, a quote or a line break, as
 * forms/result-view.js csvCell quotes.
 *
 * @param {string} text the text
 * @returns {string} the cell
 */
function cell(text) {
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/**
 * The records of a CSV text: its lines, a line break inside a quoted cell kept.
 *
 * @param {string} text the CSV text
 * @returns {string[]} the records without their line breaks
 */
function records(text) {
  const found = [];
  let quoted = false;
  let start = 0;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"') quoted = !quoted;
    else if (char === "\n" && !quoted) {
      found.push(text.slice(start, index).replace(/\r$/, ""));
      start = index + 1;
    }
  }
  if (start < text.length) found.push(text.slice(start).replace(/\r$/, ""));
  return found;
}

/**
 * The cells of a column of lines over `rows` data rows (DEV-20.5): one line per cell from
 * the first row down, empty cells below; the lines a short table has no row for join its
 * last row's cell with a line break.
 *
 * @param {string[]} lines the lines
 * @param {number} rows the count of data rows
 * @returns {string[]} the cells
 */
function column(lines, rows) {
  if (lines.length <= rows) return [...lines, ...new Array(rows - lines.length).fill("")];
  return [...lines.slice(0, rows - 1), lines.slice(rows - 1).join("\n")];
}

/**
 * A CSV table with the providers' lines in two trailing columns, `attribution` and
 * `terms_notice` (DEV-20.5); without lines the text unchanged. A table without data rows
 * gets one row of empty data cells to hold them. Hydrolog's readers drop both columns, so
 * the table still reads back into its commands.
 *
 * @param {string} text the table: a header and its data rows, comma separated
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines of its data
 * @returns {string} the table with the columns, a final line break
 */
export function csvWithLines(text, lines) {
  if (!hasLines(lines)) return text;
  const [header = "", ...rows] = records(String(text));
  if (!rows.length) rows.push(",".repeat(header.replace(/"(?:[^"]|"")*"/g, "").split(",").length - 1));
  const sources = column(lines.attribution, rows.length);
  const terms = column(lines.terms_notice, rows.length);
  const out = [`${header},attribution,terms_notice`, ...rows.map((row, index) => `${row},${cell(sources[index])},${cell(terms[index])}`)];
  return `${out.join("\n")}\n`;
}

/**
 * The rows of a footer drawn under an image (a PNG of a chart): the attribution lines,
 * then the terms notice.
 *
 * @param {{attribution: string[], terms_notice: string[]}|null} lines the lines
 * @returns {string[]} the rows, none without lines
 */
export function footerLines(lines) {
  return hasLines(lines) ? [...lines.attribution, ...lines.terms_notice] : [];
}

/**
 * A line with its addresses as links.
 *
 * @param {string} line the line
 * @returns {Array<string|object>} its parts
 */
function linked(line) {
  const parts = [];
  let last = 0;
  for (const match of line.matchAll(ADDRESS)) {
    if (match.index > last) parts.push(line.slice(last, match.index));
    parts.push(html`<a href=${match[0]} target="_blank" rel="noopener noreferrer">${match[0]}</a>`);
    last = match.index + match[0].length;
  }
  if (last < line.length) parts.push(line.slice(last));
  return parts;
}

/**
 * The providers' full lines under a result, for the print view (the screen hides them and
 * shows the view's strip): the attribution lines, then the links to the providers' terms,
 * every line verbatim, the addresses as links, a retired line as orderLines gives it;
 * nothing without lines.
 *
 * @param {{lines: {attribution: string[], terms_notice: string[]}|null, name?: string,
 *   compact?: boolean}} props the lines, the footer's name (its `data-attribution`) and
 *   whether it stands inside a panel's part without its heading (a fetched depth, a
 *   received hand-off)
 * @returns {object|null} the footer
 */
export function Attribution({ lines, name = "result", compact = false }) {
  const session = useSession();
  if (!hasLines(lines)) return null;
  const shown = orderLines(lines, session);
  const rows = (items) => items.map((line) => html`<p>${linked(line)}</p>`);
  return html`
    <footer class=${compact ? "attribution compact" : "attribution"} data-attribution=${name} aria-label=${texts.title}>
      ${compact ? null : html`<h3 class="group-title">${texts.title}</h3>`}
      ${shown.attribution.length ? html`<div class="attribution-lines">${rows(shown.attribution)}</div>` : null}
      ${shown.terms_notice.length ? html`<div class="attribution-terms">${rows(shown.terms_notice)}</div>` : null}
    </footer>
  `;
}
