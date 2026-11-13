// Client of the GUI's private API (plan D5). Every URL is relative to the page
// (document.baseURI), so the GUI works at "/" and under any prefix a host mounts it at.
// The routes are generic over a commands-1 catalog: a command "uh nash" is the path
// "uh/nash".
//
// The session (the work directory of the tab's files) is named by the header
// X-Hydrolog-Session, never by a cookie (Nogat DEV-15.10: a public GUI sets no cookie of
// its own). The id lives in this module's memory only, so a reload or a second tab starts
// a new session, and leaving the page ends it (pagehide). Files of the session are fetched
// with the header and saved through a Blob, since a plain link could not carry it.

import { errorTitleForStatus } from "./labels/errors.js";

/** The request and response header with the session id. */
const SESSION_HEADER = "X-Hydrolog-Session";

/** The session id of this tab, null until a response names one. */
let sessionId = null;

/** The GET api/session in flight while no id is known, shared by every caller. */
let opening = null;

/** Whether the pagehide listener that ends the session is installed. */
let watching = false;

/**
 * A failed request: the HTTP status (0 when the server was not reached) and the
 * hydrolog-error/1 document of the answer (a stand-in when the answer had none).
 */
export class ApiError extends Error {
  /**
   * @param {number} status HTTP status, 0 without an answer
   * @param {{code: string, title?: string, message?: string, details?: object}} doc the error
   */
  constructor(status, doc) {
    super(doc.message || doc.title || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.doc = doc;
  }
}

/**
 * Resolve an API path against the page.
 *
 * @param {string} path relative path, e.g. "api/session"
 * @returns {string} the absolute URL
 */
function resolve(path) {
  return new URL(path, document.baseURI).href;
}

/**
 * The URL path of a command: "route level-pool" gives "route/level-pool".
 *
 * @param {string} name the command's name, "<group> <verb>"
 * @returns {string} "<group>/<verb>", each part percent-encoded
 */
export function commandPath(name) {
  const words = String(name).trim().split(/\s+/);
  if (words.length !== 2) throw new TypeError(`Not a command name: ${name}`);
  return words.map(encodeURIComponent).join("/");
}

/**
 * The URL path of a session file: "in/opad 1.csv" gives "in/opad%201.csv"; outputs may be
 * nested ("out/siec/A.csv", the files of an output directory).
 *
 * @param {string} path "in/<name>" or "out/<name>[/<name>…]"
 * @returns {string} the encoded path
 */
export function filePath(path) {
  const [area, ...rest] = String(path).split("/");
  const nested = area === "out" ? rest.length >= 1 : rest.length === 1;
  if ((area !== "in" && area !== "out") || !nested || rest.some((part) => !part || part === "." || part === "..")) {
    throw new TypeError(`Not a session file: ${path}`);
  }
  return [area, ...rest.map(encodeURIComponent)].join("/");
}

/**
 * Read a JSON body, or null when the answer is not JSON.
 *
 * @param {Response} response the answer
 * @returns {Promise<any>} the document or null
 */
async function readJson(response) {
  const type = response.headers.get("Content-Type") || "";
  if (!type.includes("json")) return null;
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Take the session id a response names (the server started a session for the request);
 * the first id installs the pagehide listener, so a page that never holds a session (the
 * admin page) never ends one.
 *
 * @param {Response} response any answer, ok or not
 */
function adopt(response) {
  const id = response.headers.get(SESSION_HEADER);
  if (!id) return;
  sessionId = id;
  if (watching) return;
  watching = true;
  // A page kept in the back-forward cache (persisted) may come back and still needs its
  // files; any other pagehide is the end of the tab's visit.
  window.addEventListener("pagehide", (event) => {
    if (!event.persisted) api.endSession();
  });
}

/**
 * Wait until the tab has a session: the first caller without an id opens it with GET
 * api/session and every concurrent one awaits that same request, so parallel first calls
 * end up in one session. A failed opening is left to the request itself (the server then
 * starts the session and names it in its answer).
 *
 * @returns {Promise<void>}
 */
async function established() {
  if (sessionId) return;
  try {
    await openSession();
  } catch {
    // the request that follows reports the failure
  }
}

/**
 * GET api/session while no id is known, one request for every concurrent caller.
 *
 * @returns {Promise<object>} hydrolog-gui-session/1
 */
function openSession() {
  if (!opening) {
    opening = getJson("api/session").finally(() => {
      opening = null;
    });
  }
  return opening;
}

/**
 * Send a request with the session's header; a non-2xx answer throws ApiError, an aborted
 * one the AbortError. The session id of any answer is adopted.
 *
 * @param {string} method HTTP method
 * @param {string} path relative API path
 * @param {{body?: BodyInit, json?: unknown, signal?: AbortSignal, session?: boolean,
 *   keepalive?: boolean}} [init] body, signal, whether the request needs a session (it waits
 *   for the tab's first one) and whether it may outlive the page
 * @returns {Promise<Response>} the successful answer
 */
async function request(method, path, init = {}) {
  if (init.session) await established();
  const headers = {};
  if (sessionId) headers[SESSION_HEADER] = sessionId;
  let body = init.body;
  if (init.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.json);
  }
  let response;
  try {
    response = await fetch(resolve(path), {
      method,
      body,
      headers,
      signal: init.signal,
      keepalive: Boolean(init.keepalive),
      cache: "no-store",
    });
  } catch (error) {
    if (error && error.name === "AbortError") throw error;
    throw new ApiError(0, {
      code: "network_error",
      title: errorTitleForStatus(0),
      message: String((error && error.message) || error),
    });
  }
  adopt(response);
  if (!response.ok) {
    const doc = await readJson(response);
    throw new ApiError(
      response.status,
      doc && typeof doc.code === "string"
        ? doc
        : { code: "http_error", title: errorTitleForStatus(response.status), message: `HTTP ${response.status}` },
    );
  }
  return response;
}

/**
 * GET a JSON document.
 *
 * @param {string} path relative API path
 * @returns {Promise<any>} the document
 */
async function getJson(path) {
  return (await request("GET", path)).json();
}

/**
 * Save a blob on the person's disk as a download, and count the download (DEV-15.11):
 * every file the page saves goes through here.
 *
 * @param {Blob} blob the content
 * @param {string} name the file name
 */
export function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  api.count("download");
}

/** Documents that do not change while the server runs, fetched once. */
const cache = new Map();

/**
 * Fetch a document once; a failed fetch is not kept, so the next call tries again.
 *
 * @param {string} path relative API path
 * @returns {Promise<any>} the document
 */
function cached(path) {
  let found = cache.get(path);
  if (!found) {
    found = getJson(path);
    cache.set(path, found);
    found.catch(() => cache.delete(path));
  }
  return found;
}

/** The API of the GUI (plan D5), every call relative to the page. */
export const api = {
  /**
   * The session: version, limits, the session's files, its id and the address of the
   * regulamin; the tab's first call opens the session (one request for concurrent callers).
   *
   * @returns {Promise<{schema: string, version: string, id: string, terms: string|null,
   *   operator_email: string|null, limits: object, files: Array<{path: string, size_bytes:
   *   number, sha256: string}>}>} hydrolog-gui-session/1
   */
  session() {
    return sessionId ? getJson("api/session") : openSession();
  },

  /**
   * End the tab's session: the server deletes its files. Sent with keepalive, so it
   * reaches the server while the page goes away; a failure is ignored (the server ends an
   * idle session by itself).
   *
   * @returns {Promise<void>}
   */
  async endSession() {
    if (!sessionId) return;
    // request() reads the id before its first await, so the DELETE still carries it; the
    // next request that needs a session then opens a new one.
    const ending = request("DELETE", "api/session", { keepalive: true });
    sessionId = null;
    try {
      await ending;
    } catch {
      // nothing to tell: the page is leaving
    }
  },

  /**
   * The command list (hydrolog-command-list/1) without the commands the GUI leaves out.
   *
   * @returns {Promise<{commands: Array<{name: string, operation_id: string, summary: string, families: string[], read_only: boolean}>}>}
   */
  commands() {
    return cached("api/commands");
  },

  /**
   * One command's catalog document (hydrolog-commands/1 holding that command).
   *
   * @param {string} name "<group> <verb>", e.g. "uh nash"
   * @returns {Promise<{schema: string, commands: object[]}>} the document
   */
  command(name) {
    return cached(`api/commands/${commandPath(name)}`);
  },

  /**
   * A JSON Schema of Hydrolog, e.g. "hydrolog-network-1.schema.json".
   *
   * @param {string} file the schema's file name
   * @returns {Promise<object>} the schema
   */
  schema(file) {
    return cached(`api/schemas/${encodeURIComponent(file)}`);
  },

  /**
   * Run a command; a newer run of the same channel supersedes an older one.
   *
   * @param {string} name "<group> <verb>"
   * @param {object} options the options; paths are "in/<name>" or "out/<name>"
   * @param {{channel?: string, check?: boolean, signal?: AbortSignal}} [run] the channel
   *   ("polecenia", "hydrogram", …), plan mode and an abort signal
   * @returns {Promise<object>} the hydrolog-result/1 envelope (status "ok" or "cancelled")
   * @throws {ApiError} with the status and the hydrolog-error/1 document
   */
  async run(name, options, run = {}) {
    const query = new URLSearchParams();
    if (run.channel) query.set("channel", run.channel);
    if (run.check) query.set("check", "true");
    const suffix = query.toString() ? `?${query}` : "";
    const response = await request("POST", `api/run/${commandPath(name)}${suffix}`, {
      json: options || {},
      signal: run.signal,
      session: true,
    });
    return response.json();
  },

  /**
   * The command line of a call (format_command on the server).
   *
   * @param {string} name "<group> <verb>"
   * @param {object} options the options as given
   * @param {{signal?: AbortSignal}} [init] an abort signal
   * @returns {Promise<string>} the line, "hydrolog <group> <verb> --option value …"
   */
  async format(name, options, init = {}) {
    const response = await request("POST", `api/format/${commandPath(name)}`, {
      json: options || {},
      signal: init.signal,
    });
    return (await response.json()).line;
  },

  /**
   * Upload a file into the session's "in/".
   *
   * @param {Blob} file the file's bytes
   * @param {string} name the file name, [A-Za-z0-9][A-Za-z0-9._ -]{0,127}
   * @returns {Promise<{path: string, size_bytes: number, sha256: string}>} hydrolog-gui-file/1
   */
  async upload(file, name) {
    const response = await request("PUT", `api/files/${filePath(`in/${name}`)}`, { body: file, session: true });
    return response.json();
  },

  /**
   * The bytes of a session file, fetched with the session's header.
   *
   * @param {string} path "in/<name>" or "out/<name>"
   * @returns {Promise<Blob>} the content
   * @throws {ApiError} with the status and the hydrolog-error/1 document
   */
  async fileBlob(path) {
    return (await request("GET", `api/files/${filePath(path)}`)).blob();
  },

  /**
   * The text of a session file, fetched with the session's header.
   *
   * @param {string} path "in/<name>" or "out/<name>"
   * @returns {Promise<string>} the content as UTF-8 text
   * @throws {ApiError} with the status and the hydrolog-error/1 document
   */
  async fileText(path) {
    return (await request("GET", `api/files/${filePath(path)}`)).text();
  },

  /**
   * Save a session file on the person's disk (fetched with the session's header, saved
   * through a Blob and counted, downloadBlob).
   *
   * @param {string} path "in/<name>" or "out/<name>"
   * @param {string} [name] the file name, the path's last part by default
   * @returns {Promise<void>}
   * @throws {ApiError} with the status and the hydrolog-error/1 document
   */
  async downloadFile(path, name = String(path).split("/").pop()) {
    downloadBlob(await api.fileBlob(path), name);
  },

  /**
   * Remove a session file.
   *
   * @param {string} path "in/<name>" or "out/<name>"
   * @returns {Promise<void>}
   */
  async remove(path) {
    await request("DELETE", `api/files/${filePath(path)}`);
  },

  /**
   * Send a report of „Zgłoś uwagę”.
   *
   * @param {{message: string, context: {view: string, station: string|null, parameters:
   *   object, app_version: string}}} report the message (1 to 5000 characters) and its
   *   context; any other field is refused (400 validation_error, unknown_field)
   * @returns {Promise<{id: number, status: string}>} the id of the stored report
   * @throws {ApiError} with the status and the hydrolog-error/1 document
   */
  async feedback(report) {
    const response = await request("POST", "api/feedback", { json: report });
    return response.json();
  },

  /**
   * Count an event in the server's anonymous daily totals (DEV-15.11): "download" for a
   * file saved on the person's disk, "station" for a station's series opened. Fire and
   * forget: it never throws and nothing waits for it.
   *
   * @param {"download"|"station"} event the event
   */
  count(event) {
    request("POST", `api/stats/${encodeURIComponent(event)}`, { keepalive: true }).catch(() => {});
  },
};
