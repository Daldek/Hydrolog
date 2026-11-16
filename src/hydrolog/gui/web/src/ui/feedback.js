// „Zgłoś uwagę” (Nogat DEV-15.12, the dialog of Nogat's mockup): the button of the top bar
// opens a native <dialog> (modal: Escape or a click beside it closes it) with one text
// field and its counter (at most 5000 characters), the hint under it not to write personal
// data (with the operator's address for an answer, `operator_email` of GET api/session,
// when the deployment names one), the note of what the report carries besides the text,
// Anuluj and Wyślij, and a status line; it closes 2 s after the report is stored. There is
// no contact field: a report goes as {message, context}, the context built by the page
// (context.js: the view, the station, the view's parameters and the app version), never
// anything about the browser. The shell mounts it only standalone, with the top bar.

import { api } from "../api.js";
import { feedbackContext } from "../context.js";
import { useSession } from "../controls/file-field.js";
import { html, useEffect, useId, useRef, useState } from "../html.js";
import { t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { feedback as texts } from "../labels/feedback.js";

/** The server's limit of the text (api/feedback) [characters]. */
export const MESSAGE_MAX = 5000;

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
function openFeedback() {
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
 * The hint under the text field: no personal data, and where to write for an answer.
 *
 * @param {object|null} session hydrolog-gui-session/1, null until it arrives
 * @returns {string} the hint
 */
function feedbackHint(session) {
  const email = session && typeof session.operator_email === "string" ? session.operator_email.trim() : "";
  return email ? t(texts.hintEmail, { email }) : texts.hint;
}

/**
 * The dialog of a report.
 *
 * @returns {object} the <dialog>
 */
export function FeedbackDialog() {
  const id = useId();
  const session = useSession();
  const dialog = useRef(null);
  const field = useRef(null);
  const timer = useRef(null);
  const [message, setMessage] = useState("");
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
      // The dialog is modal: the context is the page as it was when the dialog opened
      await api.feedback({ message: text, context: feedbackContext(session && session.version) });
      setStatus({ kind: "ok", text: texts.thanks });
      setMessage("");
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
              aria-describedby=${`${id}-hint`}
              value=${message}
              onInput=${(event) => setMessage(event.currentTarget.value)}
            ></textarea>
            <span class="counter num">${t(texts.counter, { count: message.length, max: MESSAGE_MAX })}</span>
            <span class="hint" id=${`${id}-hint`}>${feedbackHint(session)}</span>
          </div>
          <p class="note muted">${texts.note}</p>
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
