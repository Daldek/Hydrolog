// The welcome dialog: a few plain sentences on what Hydrolog is, shown on every visit until
// „Nie pokazuj ponownie” is ticked (stored as "hydrolog-gui/welcome/1") and again from
// „Instrukcja” in the top bar. A native <dialog> opened with showModal(): the page behind
// it is inert, Escape or a click beside it closes it, and every way out keeps the choice of
// the checkbox. „Otwórz instrukcję” opens the guide (instrukcja/) in a new tab. The shell
// mounts it only standalone: inside Nogat's shell there is no top bar to reopen it.

import { html, useEffect, useId, useRef, useState } from "../html.js";
import { shell } from "../labels/shell.js";
import { clearState, loadState, saveState } from "../persist.js";

/** The stored part ("hydrolog-gui/welcome/1"): {hidden: true} once the box is ticked. */
const PART = "welcome";

/** Opens the mounted dialog; null while none is mounted. */
let opener = null;

/**
 * Whether „Nie pokazuj ponownie” was ticked.
 *
 * @returns {boolean} true when the dialog stays closed on a visit
 */
export function welcomeHidden() {
  const stored = loadState(PART, null);
  return Boolean(stored && stored.hidden === true);
}

/**
 * Keep the choice of „Nie pokazuj ponownie”; unticked removes the key.
 *
 * @param {boolean} hidden whether the dialog stays closed on the next visits
 */
function keepChoice(hidden) {
  if (hidden) saveState(PART, { hidden: true });
  else clearState(PART);
}

/**
 * Open the welcome dialog, as „Instrukcja” in the top bar does.
 *
 * @returns {boolean} false when no dialog is mounted (the caller follows its link)
 */
export function openWelcome() {
  if (!opener) return false;
  opener();
  return true;
}

/**
 * The welcome dialog, opened when the shell mounts unless it was hidden.
 *
 * @returns {object} the <dialog>
 */
export function Welcome() {
  const id = useId();
  const dialog = useRef(null);
  const box = useRef(null);
  const start = useRef(null);
  const [hidden, setHidden] = useState(welcomeHidden);
  const texts = shell.welcome;

  useEffect(() => {
    const open = () => {
      const element = dialog.current;
      if (!element || element.open) return;
      setHidden(welcomeHidden());
      element.showModal();
      if (start.current) start.current.focus();
    };
    opener = open;
    if (!welcomeHidden()) open();
    return () => {
      if (opener === open) opener = null;
    };
  }, []);

  const close = () => {
    if (dialog.current && dialog.current.open) dialog.current.close();
  };
  // A click on the dialog itself (not on its content, which fills it) is on the backdrop
  const onClick = (event) => {
    if (event.target === event.currentTarget) close();
  };
  return html`
    <dialog
      class="modal welcome"
      ref=${dialog}
      aria-labelledby=${`${id}-title`}
      aria-describedby=${`${id}-text`}
      onClose=${() => keepChoice(Boolean(box.current && box.current.checked))}
      onClick=${onClick}
    >
      <div class="modal-head">
        <img src="nogat/marks/hydrolog.svg" alt="" width="24" height="24" />
        <h2 id=${`${id}-title`}>${texts.title}</h2>
        <button class="btn ghost sm icon" type="button" aria-label=${texts.close} title=${texts.close} onClick=${close}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" /></svg>
        </button>
      </div>
      <div class="modal-body">
        <div id=${`${id}-text`}>${texts.text.map((sentence) => html`<p>${sentence}</p>`)}</div>
        <label class="check">
          <input type="checkbox" ref=${box} checked=${hidden} onChange=${(event) => setHidden(event.currentTarget.checked)} />
          <span>${texts.hide}</span>
        </label>
      </div>
      <div class="modal-foot">
        <a class="btn" href="instrukcja/" target="_blank" rel="noopener" onClick=${close}>${texts.guide}</a>
        <button class="btn primary" type="button" ref=${start} onClick=${close}>${texts.app}</button>
      </div>
    </dialog>
  `;
}
