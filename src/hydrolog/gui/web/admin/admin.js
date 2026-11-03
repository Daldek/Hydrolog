// The admin page of the GUI (Nogat plan 2026-11-03, D3): the reports of „Zgłoś uwagę” for
// the holder of the admin key (HYDROLOG_ADMIN_API_KEY or HYDROLOG_ADMIN_API_KEY_FILE where
// the server runs). The key is asked for once per tab and kept in sessionStorage only; a
// refused key is forgotten. The list is newest first with the count of unread reports; a
// report opens its details (and is then read), is marked unread again, or deleted.
// Reports are anonymous input: every text of a report is a text node (a Preact child),
// never markup.

import { ApiError } from "../src/api.js";
import { html, render, useEffect, useRef, useState } from "../src/html.js";
import { admin as texts } from "../src/labels/admin.js";
import { t } from "../src/labels/common.js";
import { describeError, errorTitleForStatus } from "../src/labels/errors.js";
import { ThemeSwitch } from "../src/ui/top-bar.js";

/** The sessionStorage key of the admin key: this tab only. */
const STORED = "hydrolog-gui/admin-key/1";

/** Reports per page (the server gives at most 200). */
const PAGE = 100;

/** The characters of a report its row shows. */
const EXCERPT = 80;

/**
 * The key kept in this tab.
 *
 * @returns {string} the key, "" without one
 */
function storedKey() {
  try {
    return window.sessionStorage.getItem(STORED) || "";
  } catch {
    return "";
  }
}

/**
 * Keep the key in this tab, or forget it.
 *
 * @param {string} key the key; "" forgets it
 */
function keepKey(key) {
  try {
    if (key) window.sessionStorage.setItem(STORED, key);
    else window.sessionStorage.removeItem(STORED);
  } catch {
    // Storage blocked: the key lasts until the page closes.
  }
}

/**
 * Call an admin route (api/admin/…, beside the page's directory) with the key.
 *
 * @param {string} key the admin key
 * @param {string} method HTTP method
 * @param {string} path below api/admin/, e.g. "feedback?limit=100"
 * @param {unknown} [json] the body
 * @returns {Promise<any>} the JSON answer
 * @throws {ApiError} with the status and the hydrolog-error/1 document
 */
async function call(key, method, path, json) {
  const headers = { "X-Admin-Key": key };
  const init = { method, headers, credentials: "same-origin", cache: "no-store" };
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(json);
  }
  let response;
  try {
    response = await fetch(new URL(`../api/admin/${path}`, document.baseURI).href, init);
  } catch (error) {
    throw new ApiError(0, {
      code: "network_error",
      title: errorTitleForStatus(0),
      message: String((error && error.message) || error),
    });
  }
  let doc = null;
  if ((response.headers.get("Content-Type") || "").includes("json")) {
    try {
      doc = await response.json();
    } catch {
      doc = null;
    }
  }
  if (!response.ok) {
    throw new ApiError(
      response.status,
      doc && typeof doc.code === "string"
        ? doc
        : { code: "http_error", title: errorTitleForStatus(response.status), message: `HTTP ${response.status}` },
    );
  }
  return doc;
}

/**
 * The Polish sentence of a failed call: its reason, else the error's title.
 *
 * @param {unknown} error what call() threw
 * @returns {string} the sentence
 */
function errorText(error) {
  if (!(error instanceof ApiError)) return String((error && error.message) || error);
  const described = describeError(error.doc);
  return described.english ? described.title : described.text;
}

/**
 * Whether the server refused the key (401).
 *
 * @param {unknown} error what call() threw
 * @returns {boolean} true for a refusal
 */
function refused(error) {
  return error instanceof ApiError && error.status === 401;
}

/**
 * What the prompt says of a refused key: Hydrograf's sentence for a wrong one.
 *
 * @param {unknown} error what call() threw
 * @returns {string} the sentence
 */
function refusalText(error) {
  const reason = refused(error) && error.doc.details ? error.doc.details.reason : null;
  return reason === "admin_key_invalid" ? texts.auth.invalid : errorText(error);
}

/**
 * A moment of a report in the browser's time zone, "3.11.2026, 10:15".
 *
 * @param {string} iso ISO 8601
 * @param {boolean} [timeOnly] only the time, "10:15:30"
 * @returns {string} the text
 */
function when(iso, timeOnly = false) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso ?? "");
  return timeOnly
    ? date.toLocaleTimeString("pl-PL")
    : date.toLocaleString("pl-PL", { dateStyle: "short", timeStyle: "short" });
}

/**
 * The key prompt; the key is checked before it is kept.
 *
 * @param {{refusal: string|null, onKey: (key: string) => void}} props the sentence of
 *   the last refused key and what takes an accepted one
 * @returns {object} the form
 */
function Auth({ refusal, onKey }) {
  const [value, setValue] = useState("");
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState(refusal);
  const input = useRef(null);
  useEffect(() => {
    if (input.current) input.current.focus();
  }, []);
  const submit = async (event) => {
    event.preventDefault();
    const key = value.trim();
    if (!key) return;
    setChecking(true);
    setError(null);
    try {
      await call(key, "GET", "feedback?limit=1");
      onKey(key);
    } catch (failure) {
      setError(refusalText(failure));
      setValue("");
      setChecking(false);
      if (input.current) input.current.focus();
    }
  };
  const fromFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    if (file) setValue((await file.text()).trim());
  };
  return html`
    <form class="auth-card" onSubmit=${submit}>
      <h1>${texts.auth.title}</h1>
      <p class="muted">${texts.auth.text}</p>
      <input
        type="password"
        ref=${input}
        autocomplete="off"
        placeholder=${texts.auth.key}
        aria-label=${texts.auth.key}
        value=${value}
        onInput=${(event) => setValue(event.currentTarget.value)}
      />
      <label class="auth-file">
        <span>${texts.auth.file}</span>
        <input type="file" accept=".key,.txt,.token" onChange=${fromFile} />
      </label>
      <button class="btn primary" type="submit" disabled=${checking}>${checking ? texts.auth.checking : texts.auth.submit}</button>
      <p class="auth-error" role="alert" hidden=${!error}>${error || ""}</p>
    </form>
  `;
}

/**
 * The details of a report: the message, the contact, the page, the browser, the
 * workspace and the environment of the diagnostics, and their events.
 *
 * @param {{item: object}} props the report
 * @returns {object} the details
 */
function Details({ item }) {
  const diagnostics = item.diagnostics && typeof item.diagnostics === "object" ? item.diagnostics : null;
  const events = diagnostics && Array.isArray(diagnostics.events) ? diagnostics.events : [];
  return html`
    <div class="report-details">
      <p class="report-message">${item.message}</p>
      ${item.contact ? html`<p class="report-meta">${t(texts.contact, { value: item.contact })}</p>` : null}
      ${item.page_url ? html`<p class="report-meta">${t(texts.url, { value: item.page_url })}</p>` : null}
      ${item.user_agent ? html`<p class="report-meta">${t(texts.browser, { value: item.user_agent })}</p>` : null}
      ${diagnostics && diagnostics.workspace
        ? html`<h2>${texts.workspace}</h2><pre class="report-data">${JSON.stringify(diagnostics.workspace, null, 2)}</pre>`
        : null}
      ${diagnostics && diagnostics.env
        ? html`<h2>${texts.environment}</h2><pre class="report-data">${JSON.stringify(diagnostics.env, null, 2)}</pre>`
        : null}
      <h2>${texts.events}</h2>
      ${events.length
        ? html`<table class="report-events">
            <tbody>
              ${events.map(
                (event, index) => html`
                  <tr key=${index}>
                    <td class="num">${when(event && event.t, true)}</td>
                    <td>${String((event && event.type) ?? "")}</td>
                    <td><pre class="report-data">${JSON.stringify((event && event.data) ?? {})}</pre></td>
                  </tr>
                `,
              )}
            </tbody>
          </table>`
        : html`<p class="muted small">${texts.noEvents}</p>`}
    </div>
  `;
}

/**
 * One report: its row (date, excerpt, „nowe”, the read toggle, „Usuń”) and, open, its
 * details.
 *
 * @param {{item: object, open: boolean, onToggle: () => void, onRead: (read: boolean) =>
 *   void, onRemove: () => void}} props the report and its actions
 * @returns {object} the item of the list
 */
function Row({ item, open, onToggle, onRead, onRemove }) {
  const message = String(item.message ?? "");
  const excerpt = message.length > EXCERPT ? `${message.slice(0, EXCERPT)}…` : message;
  return html`
    <li class=${`report${item.is_read ? "" : " unread"}`} data-id=${item.id}>
      <div class="report-head">
        <button class="report-toggle" type="button" aria-expanded=${open} onClick=${onToggle}>
          <span class="report-date num">${when(item.created_at)}</span>
          <span class="report-excerpt">${excerpt}</span>
          ${item.is_read ? null : html`<span class="badge bad">${texts.fresh}</span>`}
        </button>
        <button class="btn sm" type="button" onClick=${() => onRead(!item.is_read)}>
          ${item.is_read ? texts.markUnread : texts.markRead}
        </button>
        <button class="btn sm danger" type="button" onClick=${onRemove}>${texts.remove}</button>
      </div>
      ${open ? html`<${Details} item=${item} />` : null}
    </li>
  `;
}

/**
 * The reports: newest first, a page at a time, with the count of unread ones.
 *
 * @param {{adminKey: string, onRefused: (text: string) => void, onSignOut: () => void}}
 *   props the key, what a refused key does, and „Wyloguj”
 * @returns {object} the list
 */
function Reports({ adminKey, onRefused, onSignOut }) {
  const [state, setState] = useState({ items: [], total: 0, unread: 0, loaded: false });
  const [open, setOpen] = useState(() => new Set());
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const fail = (failure, template) => {
    if (refused(failure)) onRefused(refusalText(failure));
    else setError(t(template, { message: errorText(failure) }));
  };
  const load = async (offset) => {
    setBusy(true);
    try {
      const page = await call(adminKey, "GET", `feedback?limit=${PAGE}&offset=${offset}`);
      setError(null);
      setState((old) => {
        const known = new Set(offset ? old.items.map((item) => item.id) : []);
        const items = offset ? [...old.items, ...page.items.filter((item) => !known.has(item.id))] : page.items;
        return { items, total: page.total, unread: page.unread_count, loaded: true };
      });
    } catch (failure) {
      fail(failure, texts.failed);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    load(0);
  }, [adminKey]);

  // Optimistic: the row and the count change at once and come back if the call fails
  const setRead = async (item, read) => {
    if (item.is_read === read) return;
    const show = (value) =>
      setState((old) => ({
        ...old,
        unread: old.unread + (value ? -1 : 1),
        items: old.items.map((other) => (other.id === item.id ? { ...other, is_read: value } : other)),
      }));
    show(read);
    try {
      await call(adminKey, "PATCH", `feedback/${item.id}`, { is_read: read });
    } catch (failure) {
      show(!read);
      fail(failure, texts.saveFailed);
    }
  };
  const remove = async (item) => {
    if (!window.confirm(t(texts.confirmRemove, { id: item.id }))) return;
    try {
      await call(adminKey, "DELETE", `feedback/${item.id}`);
      setState((old) => {
        const gone = old.items.find((other) => other.id === item.id);
        return {
          ...old,
          total: old.total - 1,
          unread: old.unread - (gone && !gone.is_read ? 1 : 0),
          items: old.items.filter((other) => other.id !== item.id),
        };
      });
    } catch (failure) {
      fail(failure, texts.removeFailed);
    }
  };
  const toggle = (item) => {
    setOpen((old) => {
      const next = new Set(old);
      if (next.has(item.id)) next.delete(item.id);
      else next.add(item.id);
      return next;
    });
    setRead(item, true);
  };

  let body;
  if (!state.loaded) body = html`<p class="muted">${texts.loading}</p>`;
  else if (!state.items.length) body = html`<p class="muted">${texts.empty}</p>`;
  else {
    body = html`
      <ul class="reports">
        ${state.items.map(
          (item) => html`
            <${Row}
              key=${item.id}
              item=${item}
              open=${open.has(item.id)}
              onToggle=${() => toggle(item)}
              onRead=${(read) => setRead(item, read)}
              onRemove=${() => remove(item)}
            />
          `,
        )}
      </ul>
    `;
  }
  return html`
    <section class="reports-card" aria-labelledby="reports-title">
      <div class="reports-head">
        <h1 id="reports-title">${texts.title}</h1>
        ${state.unread > 0
          ? html`<span class="badge bad unread-count" aria-label=${t(texts.unread, { count: state.unread })} title=${t(texts.unread, { count: state.unread })}>${state.unread}</span>`
          : null}
        <div class="reports-actions">
          <button class="btn sm" type="button" disabled=${busy} onClick=${() => load(0)}>${texts.refresh}</button>
          <button class="btn sm ghost" type="button" onClick=${onSignOut}>${texts.logout}</button>
        </div>
      </div>
      <p class="reports-error" role="alert" hidden=${!error}>${error || ""}</p>
      ${body}
      ${state.items.length < state.total
        ? html`<button class="btn" type="button" disabled=${busy} onClick=${() => load(state.items.length)}>
            ${t(texts.more, { shown: state.items.length, total: state.total })}
          </button>`
        : null}
    </section>
  `;
}

/**
 * The page: the key prompt until a key is accepted, then the reports.
 *
 * @returns {object} the page's content
 */
function AdminApp() {
  const [key, setKey] = useState(storedKey);
  const [refusal, setRefusal] = useState(null);
  const signOut = (text = null) => {
    keepKey("");
    setRefusal(text);
    setKey("");
  };
  if (!key) {
    return html`<${Auth}
      refusal=${refusal}
      onKey=${(accepted) => {
        keepKey(accepted);
        setRefusal(null);
        setKey(accepted);
      }}
    />`;
  }
  return html`<${Reports} adminKey=${key} onRefused=${signOut} onSignOut=${() => signOut()} />`;
}

const theme = document.getElementById("theme");
if (theme) render(html`<${ThemeSwitch} />`, theme);
render(html`<${AdminApp} />`, document.getElementById("admin"));
