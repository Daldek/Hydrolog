// Client of the GUI's private API (plan D5). Every URL is relative to the page
// (document.baseURI), so the GUI works at "/" and under any prefix a host mounts it at.
// The routes are generic over a commands-1 catalog: a command "uh nash" is the path
// "uh/nash".

import { errorTitleForStatus } from "./labels/errors.js";

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
 * Send a request; a non-2xx answer throws ApiError, an aborted one the AbortError.
 *
 * @param {string} method HTTP method
 * @param {string} path relative API path
 * @param {{body?: BodyInit, json?: unknown, signal?: AbortSignal}} [init] body and signal
 * @returns {Promise<Response>} the successful answer
 */
async function request(method, path, init = {}) {
  const headers = {};
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
      credentials: "same-origin",
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
   * The session: version, limits and the session's files.
   *
   * @returns {Promise<{schema: string, version: string, limits: object, files: Array<{path: string, size_bytes: number, sha256: string}>}>}
   *   hydrolog-gui-session/1
   */
  session() {
    return getJson("api/session");
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
    const response = await request("PUT", `api/files/${filePath(`in/${name}`)}`, { body: file });
    return response.json();
  },

  /**
   * The download URL of a session file.
   *
   * @param {string} path "in/<name>" or "out/<name>"
   * @returns {string} the absolute URL
   */
  fileUrl(path) {
    return resolve(`api/files/${filePath(path)}`);
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
};
