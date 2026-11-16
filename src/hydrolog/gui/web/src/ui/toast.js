// A short message at the bottom of the page (the mockup's toast): toast("Skopiowano…").

import { html, useEffect, useState } from "../html.js";

const listeners = new Set();
let counter = 0;

/**
 * Show a short message.
 *
 * @param {string} text the message
 * @param {"ok"|"bad"} [kind="ok"] a success or a failure
 */
export function toast(text, kind = "ok") {
  counter += 1;
  const item = { text, kind, id: counter };
  for (const listener of [...listeners]) listener(item);
}

/**
 * The place of the messages; the shell renders it once.
 *
 * @returns {object} a polite live region
 */
export function ToastHost() {
  const [item, setItem] = useState(null);
  useEffect(() => {
    listeners.add(setItem);
    return () => listeners.delete(setItem);
  }, []);
  useEffect(() => {
    if (!item) return undefined;
    const timer = setTimeout(() => setItem(null), 3200);
    return () => clearTimeout(timer);
  }, [item]);
  return html`
    <div class=${`toast${item ? ` ${item.kind}` : ""}`} role="status" aria-live="polite" hidden=${!item}>
      ${item ? item.text : ""}
    </div>
  `;
}
