// The diagnostics of „Zgłoś uwagę” (Nogat plan 2026-11-03, D4), as Hydrograf's: a ring
// buffer of the last 50 events of the page (JavaScript errors, calls of the API with their
// status and duration, changes of the view), kept in memory only, and a snapshot of what
// the person sees: the section, its route, status and context, the inputs of its form and
// the environment. Nothing leaves the browser until a report is sent with „Dołącz dane
// diagnostyczne” ticked; the dialog shows the very snapshot it sends. Never in it: the
// contents of files (uploads stay on the server; a pasted text and the rest of a long list
// are replaced by their size), request bodies, cookies or keys. A snapshot is at most
// 100 000 bytes of JSON: the oldest events go first. The page reads about fifty catalog
// documents when it loads (api/commands/…, api/schemas/…): only a failed one is an event,
// or they would push every other event out of the buffer.

import { host, storedTheme } from "./host.js";
import { t } from "./labels/common.js";
import { feedback as texts } from "./labels/feedback.js";
import { loadState } from "./persist.js";
import { parseHash } from "./router.js";
import { getActiveSection, getStore } from "./store.js";

/** How many events the buffer keeps. */
export const MAX_EVENTS = 50;

/** The server's limit of the diagnostics: their JSON in UTF-8 [bytes]. */
export const LIMIT_BYTES = 100_000;

/** The size a snapshot is cut to: Python writes some numbers longer (1e-7 as 1e-07). */
const TARGET_BYTES = LIMIT_BYTES - 1_000;

/** The longest text of an input sent as it is; a longer one, or one with lines, is not. */
const MAX_TEXT = 200;

/** The items of a list, or the fields of an object, sent; the rest are counted. */
const MAX_ITEMS = 50;

/** How deep the inputs are followed. */
const MAX_DEPTH = 6;

/** Catalog documents: an event only when their GET fails. */
const QUIET = /^api\/(commands|schemas)(\/|\?|$)/;

const events = [];
let installed = false;

/**
 * A text cut to a length.
 *
 * @param {unknown} value anything
 * @param {number} length the most characters
 * @returns {string} the text
 */
function cut(value, length) {
  return String(value ?? "").slice(0, length);
}

/**
 * Record an event; the oldest goes when the buffer is full.
 *
 * @param {string} type "js_error", "api_call", "view"…
 * @param {object} [data] its values (JSON)
 */
export function logEvent(type, data = {}) {
  events.push({ t: new Date().toISOString(), type, data });
  if (events.length > MAX_EVENTS) events.shift();
}

/**
 * The path of an API call relative to the page ("api/run/uh/nash?channel=polecenia"), or
 * null for any other request.
 *
 * @param {RequestInfo|URL} input the first argument of fetch
 * @returns {string|null} the endpoint
 */
function apiEndpoint(input) {
  let url;
  try {
    const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    url = new URL(href, document.baseURI);
  } catch {
    return null;
  }
  const root = new URL("api/", document.baseURI);
  if (url.origin !== root.origin || !url.pathname.startsWith(root.pathname)) return null;
  return `api/${url.pathname.slice(root.pathname.length)}${url.search}`;
}

/**
 * Start recording: errors, rejected promises, changes of the view and the API calls of
 * fetch (endpoint, method, status, duration and, for a failure, the error's code and
 * reason; an aborted call is not one, nor a catalog document read). Once per page.
 */
export function installDiagnostics() {
  if (installed) return;
  installed = true;
  window.addEventListener("error", (event) => {
    logEvent("js_error", {
      message: cut(event.message, 300),
      source: event.filename ? `${event.filename}:${event.lineno}` : null,
      stack: event.error && event.error.stack ? cut(event.error.stack, 500) : null,
    });
  });
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    logEvent("js_error", {
      message: cut(reason && reason.message ? reason.message : reason, 300),
      stack: reason && reason.stack ? cut(reason.stack, 500) : null,
    });
  });
  const view = () => logEvent("view", parseHash(window.location.hash));
  window.addEventListener("hashchange", view);
  view();
  const original = window.fetch;
  window.fetch = function fetch(input, init) {
    const endpoint = apiEndpoint(input);
    if (endpoint === null) return original.call(window, input, init);
    const method = (init && init.method) || (input instanceof Request ? input.method : "GET");
    const started = performance.now();
    const duration = () => Math.round(performance.now() - started);
    return original.call(window, input, init).then(
      (response) => {
        if (response.ok && QUIET.test(endpoint)) return response;
        const data = { endpoint, method, status: response.status, duration_ms: duration() };
        logEvent("api_call", data);
        if (!response.ok && (response.headers.get("Content-Type") || "").includes("json")) {
          response
            .clone()
            .json()
            .then((doc) => {
              if (doc && typeof doc.code === "string") data.code = doc.code;
              if (doc && doc.details && typeof doc.details.reason === "string") data.reason = doc.details.reason;
            })
            .catch(() => {});
        }
        return response;
      },
      (error) => {
        if (!(error && error.name === "AbortError")) {
          logEvent("api_call", { endpoint, method, status: null, duration_ms: duration(), error: cut(error, 200) });
        }
        throw error;
      },
    );
  };
}

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
 * What the person sees: the active section, its route, status, context and inputs.
 *
 * @returns {object} the workspace
 */
function workspace() {
  const section = getActiveSection();
  const status = getStore("status");
  return {
    section,
    path: parseHash(window.location.hash).path,
    status: status ? { state: status.state, text: status.text } : null,
    context: getStore("context"),
    inputs: section ? summarize(loadState(section, null)) : null,
  };
}

/**
 * The size of a value as JSON in UTF-8.
 *
 * @param {unknown} value the value
 * @returns {number} bytes
 */
export function jsonBytes(value) {
  return new TextEncoder().encode(JSON.stringify(value)).length;
}

/**
 * The diagnostics of a report now: {events, workspace, env}, a copy that later events do
 * not change, at most LIMIT_BYTES as JSON (the oldest events go first, then the inputs).
 *
 * @returns {{events: object[], workspace: object|null, env: object}} the diagnostics
 */
export function snapshot() {
  const payload = JSON.parse(
    JSON.stringify({
      events,
      workspace: workspace(),
      env: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        viewport: { width: window.innerWidth, height: window.innerHeight },
        url: window.location.href,
        theme: storedTheme(),
        embedded: host.embedded,
        timestamp: new Date().toISOString(),
      },
    }),
  );
  while (jsonBytes(payload) > TARGET_BYTES && payload.events.length > 0) payload.events.splice(0, 10);
  if (jsonBytes(payload) > TARGET_BYTES) payload.workspace.inputs = texts.marks.tooLarge;
  if (jsonBytes(payload) > TARGET_BYTES) payload.workspace = null;
  return payload;
}
