// A question before something is lost (plan 2026-11-10-network-editor, D10: „Wyczyść” and
// „Nowa sieć” with a changed network): a native <dialog> opened with showModal(), so the
// page behind it is inert. „Anuluj” has the focus first; Escape, a click beside it or
// „Anuluj” keep everything, the other button goes on.

import { html, useEffect, useId, useRef } from "../html.js";

/**
 * The dialog of a question.
 *
 * @param {{open: boolean, name: string, title: string, text: string, confirm: string,
 *   cancel: string, onConfirm: () => void, onCancel: () => void}} props whether it is
 *   shown, its name (`data-confirm`), its title, text and buttons, and the handlers of the
 *   two answers
 * @returns {object} the <dialog>
 */
export function ConfirmDialog({ open, name, title, text, confirm, cancel, onConfirm, onCancel }) {
  const id = useId();
  const dialog = useRef(null);
  const stay = useRef(null);
  const answered = useRef(false);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) {
      answered.current = false;
      element.showModal();
      if (stay.current) stay.current.focus();
    } else if (!open && element.open) {
      answered.current = true;
      element.close();
    }
  }, [open]);
  const answer = (yes) => {
    answered.current = true;
    if (dialog.current && dialog.current.open) dialog.current.close();
    if (yes) onConfirm();
    else onCancel();
  };
  return html`
    <dialog
      class="modal confirm"
      ref=${dialog}
      data-confirm=${name}
      aria-labelledby=${`${id}-title`}
      aria-describedby=${`${id}-text`}
      onClose=${() => {
        if (!answered.current) {
          answered.current = true;
          onCancel();
        }
      }}
      onClick=${(event) => {
        if (event.target === event.currentTarget) answer(false);
      }}
    >
      <div class="modal-head"><h2 id=${`${id}-title`}>${title}</h2></div>
      <div class="modal-body"><p id=${`${id}-text`}>${text}</p></div>
      <div class="modal-foot">
        <button class="btn" type="button" ref=${stay} onClick=${() => answer(false)}>${cancel}</button>
        <button class="btn primary" type="button" data-confirm-action="yes" onClick=${() => answer(true)}>${confirm}</button>
      </div>
    </dialog>
  `;
}
