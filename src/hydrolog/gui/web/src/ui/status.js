// The status badge of the top bar: the active section's state of its result (plan D13):
// ok „Wynik aktualny”, busy „Liczenie…”, stale „Dane zmienione: oblicz ponownie”, invalid
// „Dane niepełne”, error „Błąd danych”. A section sets it with useStore("status").

import { html } from "../html.js";
import { shell } from "../labels/shell.js";
import { useStore } from "../store.js";

const BADGE = { ok: "ok", busy: "info busy", stale: "warn", invalid: "warn", error: "bad" };

/**
 * A status with the shell's text and title for its state.
 *
 * @param {"ok"|"busy"|"stale"|"invalid"|"error"} state the state of the result
 * @param {string} [text] a text instead of the state's own, e.g. „Dane niepełne: cn”
 * @param {string} [title] a longer explanation
 * @returns {{state: string, text: string, title: string}} the status
 */
export function status(state, text, title) {
  const preset = shell.status[state] || shell.status.ok;
  return { state, text: text || preset.text, title: title || preset.title };
}

/**
 * The badge of the active section; hidden while the section has no status.
 *
 * @returns {object} the badge
 */
export function StatusBadge() {
  const [current] = useStore("status");
  if (!current) return html`<span class="badge status" role="status" hidden></span>`;
  const shown = status(current.state, current.text, current.title);
  return html`
    <span
      class=${`badge status ${BADGE[shown.state] || "ok"}`}
      role="status"
      title=${shown.title}
      aria-busy=${shown.state === "busy" ? "true" : "false"}
      data-state=${shown.state}
    >
      <span class="label">${shown.text}</span>
    </span>
  `;
}
