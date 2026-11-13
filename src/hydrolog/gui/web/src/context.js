// The context of a report of „Zgłoś uwagę” (Nogat DEV-15.12): what the page adds itself to
// the text a person writes, so the operator can see where the report comes from without
// asking. Four keys only: the view (the active section and its route), the station (of a
// station's series opened in Statystyka przepływów from a hand-off, else null), the view's
// parameters (the section's stored inputs, summarized) and the app version. Nothing about
// the browser or the person goes in: no User-Agent, address, language or screen size, no
// contents of files (a pasted text and the rest of a long list are replaced by their size).
// The compact JSON is at most 100 000 bytes of UTF-8, the server's limit.

import { t } from "./labels/common.js";
import { feedback as texts } from "./labels/feedback.js";
import { loadState } from "./persist.js";
import { parseHash } from "./router.js";
import { getActiveSection } from "./store.js";

/** The server's limit of the context: its compact JSON in UTF-8 [bytes]. */
export const LIMIT_BYTES = 100_000;

/** The size a context is cut to: Python writes some numbers longer (1e-7 as 1e-07). */
const TARGET_BYTES = LIMIT_BYTES - 1_000;

/** The server's limits of `view` and `station` and of `app_version` [characters]. */
const NAME_MAX = 200;
const VERSION_MAX = 50;

/** The longest text of an input sent as it is; a longer one, or one with lines, is not. */
const MAX_TEXT = 200;

/** The items of a list, or the fields of an object, sent; the rest are counted. */
const MAX_ITEMS = 50;

/** How deep the inputs are followed. */
const MAX_DEPTH = 6;

/** The section whose hand-off may carry a station's series (ADR-0020). */
const STATION_SECTION = "statystyka";

/**
 * The inputs of a form as they may be sent: numbers, choices and short texts as they are;
 * a long text, or one with lines (a pasted series or table), by its size; at most 50 items
 * of a list and fields of an object, six levels deep.
 *
 * @param {unknown} value the stored inputs
 * @param {number} [depth] the level of value
 * @returns {unknown} the value to send
 */
export function summarize(value, depth = 0) {
  if (value === null || typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "string") {
    return value.length > MAX_TEXT || /[\r\n]/.test(value) ? t(texts.marks.text, { count: value.length }) : value;
  }
  if (typeof value !== "object") return null;
  if (depth >= MAX_DEPTH) return texts.marks.deep;
  if (Array.isArray(value)) {
    const items = value.slice(0, MAX_ITEMS).map((item) => summarize(item, depth + 1));
    if (value.length > MAX_ITEMS) items.push(t(texts.marks.more, { count: value.length - MAX_ITEMS }));
    return items;
  }
  const entries = Object.entries(value);
  const shown = Object.fromEntries(entries.slice(0, MAX_ITEMS).map(([key, item]) => [key, summarize(item, depth + 1)]));
  if (entries.length > MAX_ITEMS) shown["…"] = t(texts.marks.more, { count: entries.length - MAX_ITEMS });
  return shown;
}

/**
 * The size of a value as compact JSON in UTF-8.
 *
 * @param {unknown} value the value
 * @returns {number} bytes
 */
export function jsonBytes(value) {
  return new TextEncoder().encode(JSON.stringify(value)).length;
}

/**
 * The view: the section and, when the address is of that section, its route
 * ("polecenia/uh/nash"); a first visit without a route is the section alone.
 *
 * @param {string} section the active section's id
 * @returns {string} the view
 */
function viewOf(section) {
  const route = parseHash(window.location.hash);
  const path = route.section === section ? route.path : [];
  return [section, ...path].join("/").slice(0, NAME_MAX);
}

/**
 * The station of a station's series handed off to Statystyka przepływów: the subject of
 * the hand-off the section keeps (its `received`) while the series is the one shown.
 *
 * @param {string} section the active section's id
 * @param {unknown} stored the section's stored inputs
 * @returns {string|null} the station, null without one
 */
function stationOf(section, stored) {
  if (section !== STATION_SECTION || !stored || typeof stored !== "object") return null;
  const received = stored.received;
  if (!received || typeof received !== "object" || typeof received.subject !== "string") return null;
  return received.subject.slice(0, NAME_MAX) || null;
}

/**
 * The context of a report now: a copy that later changes of the page do not touch, at
 * most LIMIT_BYTES as compact JSON (over it, the parameters give way to a mark).
 *
 * @param {string|null|undefined} version the app version (the session's `version`)
 * @returns {{view: string, station: string|null, parameters: object, app_version: string}}
 *   the context
 */
export function feedbackContext(version) {
  const section = getActiveSection() || "";
  const stored = section ? loadState(section, null) : null;
  const summary = summarize(stored);
  const context = {
    view: section ? viewOf(section) : "",
    station: stationOf(section, stored),
    parameters: summary && typeof summary === "object" && !Array.isArray(summary) ? summary : {},
    app_version: String(version ?? "").slice(0, VERSION_MAX),
  };
  if (jsonBytes(context) > TARGET_BYTES) context.parameters = { "…": texts.marks.tooLarge };
  return context;
}
