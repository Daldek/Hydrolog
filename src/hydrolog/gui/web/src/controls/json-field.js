// An `object` option (or an `array` of objects) as a JSON editor with its parse errors
// (plan D11); sections give such options editors of their own. A JSON file can be read
// into it in the browser.

import { html, useRef, useState } from "../html.js";
import { t } from "../labels/common.js";
import { formTexts } from "../labels/options.js";
import { describedBy, FieldLabel, FieldNotes } from "./field.js";

/**
 * A JSON value of a generated form.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, onInput: (text: string) => void}} props the field, the control's
 *   id, the JSON text, the message of a check, whether a value is required now, and the
 *   change handler
 * @returns {object} the field
 */
export function JsonField({ field, id, value, error, required, disabled, onInput }) {
  const picker = useRef(null);
  const [problem, setProblem] = useState(null);
  const onFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (!file) return;
    try {
      const text = await file.text();
      setProblem(null);
      try {
        onInput(JSON.stringify(JSON.parse(text), null, 2));
      } catch {
        onInput(text);
      }
    } catch (failure) {
      setProblem(t(formTexts.readFailed, { message: failure.message }));
    }
  };
  return html`
    <div class=${`opt opt-json${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <textarea
        id=${id}
        class="json"
        rows="6"
        spellcheck="false"
        disabled=${disabled}
        value=${value ?? ""}
        placeholder=${field.kind === "objects" ? "[ { … } ]" : "{ … }"}
        aria-invalid=${error ? "true" : "false"}
        aria-required=${required ? "true" : "false"}
        aria-describedby=${describedBy(field, id, error)}
        onInput=${(event) => onInput(event.currentTarget.value)}
      ></textarea>
      <div class="series-tools">
        <button class="btn sm" type="button" disabled=${disabled} onClick=${() => picker.current.click()}>
          ${formTexts.fromJson}
        </button>
        <input ref=${picker} type="file" accept=".json,application/json" hidden onChange=${onFile} />
        <span class="series-sum">${field.kind === "objects" ? formTexts.objects : formTexts.object}</span>
      </div>
      ${problem ? html`<span class="err" role="alert">${problem}</span>` : null}
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}
