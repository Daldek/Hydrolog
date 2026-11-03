// „Zgłoś uwagę” (Nogat plan 2026-11-03, D1, D3, D4), as Hydrograf's: the button of the top
// bar opens a native <dialog> (modal: Escape or a click beside it closes it) with the
// description and its counter (at most 5000 characters), an optional name or e-mail,
// „Dołącz dane diagnostyczne” (ticked) with a preview of exactly what is sent, Anuluj and
// Wyślij, and a status line; it closes 2 s after the report is stored. The snapshot of the
// diagnostics is taken when the dialog opens, shown, and sent unchanged. The shell mounts it
// only standalone, with the top bar.

import { api } from "../api.js";
import { snapshot } from "../diagnostics.js";
import { html, useEffect, useId, useRef, useState } from "../html.js";
import { t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { feedback as texts } from "../labels/feedback.js";

/** The server's limits (api/feedback). */
export const MESSAGE_MAX = 5000;
export const CONTACT_MAX = 200;
const PAGE_URL_MAX = 500;

/** How long the thanks stay before the dialog closes [ms]. */
const CLOSE_AFTER_MS = 2000;

/** The id of the dialog, which the button controls. */
const DIALOG_ID = "feedback-dialog";

/** A speech bubble, as in Hydrograf's top bar. */
const ICON = () => html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 4h14v10H8.5L5 17v-3H3z" /></svg>`;

/** Opens the mounted dialog; null while none is mounted. */
let opener = null;

/**
 * Open the dialog, as the button does.
 *
 * @returns {boolean} false when no dialog is mounted
 */
export function openFeedback() {
  if (!opener) return false;
  opener();
  return true;
}

/**
 * The button of the top bar; on a phone only its icon shows.
 *
 * @returns {object} the button
 */
export function FeedbackButton() {
  return html`
    <button class="btn ghost" type="button" aria-label=${texts.open} title=${texts.open} aria-haspopup="dialog" aria-controls=${DIALOG_ID} onClick=${openFeedback}>
      ${ICON()}<span class="label">${texts.open}</span>
    </button>
  `;
}

/**
 * The sentence of a failed report: the reason in Polish, else the error's title.
 *
 * @param {unknown} error what api.feedback threw
 * @returns {string} the sentence
 */
function failure(error) {
  if (!error || !error.doc) return String((error && error.message) || error);
  const described = describeError(error.doc);
  return described.english ? described.title : described.text;
}

/**
 * The dialog of a report.
 *
 * @returns {object} the <dialog>
 */
export function FeedbackDialog() {
  const id = useId();
  const dialog = useRef(null);
  const field = useRef(null);
  const timer = useRef(null);
  const [message, setMessage] = useState("");
  const [contact, setContact] = useState("");
  const [include, setInclude] = useState(true);
  const [diagnostics, setDiagnostics] = useState(null);
  const [status, setStatus] = useState(null);
  const [sending, setSending] = useState(false);

  const stopTimer = () => {
    clearTimeout(timer.current);
    timer.current = null;
  };
  const close = () => {
    stopTimer();
    if (dialog.current && dialog.current.open) dialog.current.close();
  };

  useEffect(() => {
    const open = () => {
      const element = dialog.current;
      if (!element || element.open) return;
      setStatus(null);
      setDiagnostics(snapshot());
      element.showModal();
      if (field.current) field.current.focus();
    };
    opener = open;
    return () => {
      if (opener === open) opener = null;
      stopTimer();
    };
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    const text = message.trim();
    if (!text) {
      setStatus({ kind: "bad", text: texts.empty });
      if (field.current) field.current.focus();
      return;
    }
    setSending(true);
    try {
      await api.feedback({
        message: text,
        contact: contact.trim() || null,
        page_url: window.location.href.slice(0, PAGE_URL_MAX),
        diagnostics: include ? diagnostics : null,
      });
      setStatus({ kind: "ok", text: texts.thanks });
      setMessage("");
      setContact("");
      stopTimer();
      timer.current = setTimeout(close, CLOSE_AFTER_MS);
    } catch (error) {
      setStatus({ kind: "bad", text: failure(error) });
    } finally {
      setSending(false);
    }
  };
  // A click on the dialog itself (not on its content, which fills it) is on the backdrop
  const onClick = (event) => {
    if (event.target === event.currentTarget) close();
  };
  return html`
    <dialog class="modal feedback" id=${DIALOG_ID} ref=${dialog} aria-labelledby=${`${id}-title`} onClose=${stopTimer} onClick=${onClick}>
      <div class="modal-head">
        <h2 id=${`${id}-title`}>${texts.title}</h2>
        <button class="btn ghost sm icon" type="button" aria-label=${texts.close} title=${texts.close} onClick=${close}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" /></svg>
        </button>
      </div>
      <form novalidate onSubmit=${submit}>
        <div class="modal-body">
          <p class="intro">${texts.intro}</p>
          <div class="field">
            <label for=${`${id}-message`}>${texts.message}</label>
            <textarea
              id=${`${id}-message`}
              ref=${field}
              rows="6"
              maxlength=${MESSAGE_MAX}
              placeholder=${texts.placeholder}
              value=${message}
              onInput=${(event) => setMessage(event.currentTarget.value)}
            ></textarea>
            <span class="counter num">${t(texts.counter, { count: message.length, max: MESSAGE_MAX })}</span>
          </div>
          <div class="field">
            <label for=${`${id}-contact`}>${texts.contact} <span class="muted">${texts.optional}</span></label>
            <input type="text" id=${`${id}-contact`} maxlength=${CONTACT_MAX} value=${contact} onInput=${(event) => setContact(event.currentTarget.value)} />
          </div>
          <label class="check">
            <input type="checkbox" checked=${include} onChange=${(event) => setInclude(event.currentTarget.checked)} />
            <span>${texts.diagnostics}</span>
          </label>
          <details class="preview">
            <summary>${texts.preview}</summary>
            <pre>${include ? JSON.stringify(diagnostics, null, 2) : texts.noDiagnostics}</pre>
          </details>
          <p class=${`feedback-status${status ? ` ${status.kind}` : ""}`} role="status" hidden=${!status}>${status ? status.text : ""}</p>
        </div>
        <div class="modal-foot">
          <button class="btn" type="button" onClick=${close}>${texts.cancel}</button>
          <button class="btn primary" type="submit" disabled=${sending}>${texts.send}</button>
        </div>
      </form>
    </dialog>
  `;
}
