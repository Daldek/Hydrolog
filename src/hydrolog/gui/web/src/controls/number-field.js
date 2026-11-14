// A number with its unit (plan D11): a decimal comma or dot, the default as placeholder and
// „domyślnie 0,2” beside the label, Polish messages for the catalog's bounds.

import { inputText } from "../format.js";
import { html } from "../html.js";
import { t } from "../labels/common.js";
import { formTexts } from "../labels/options.js";
import { NO_UNIT } from "../labels/units.js";
import { describedBy, FieldLabel, FieldNotes } from "./field.js";

/**
 * The placeholder of a number: its default, else „np.” and the first catalog example.
 *
 * @param {object} field a field of fieldModel
 * @returns {string} the placeholder
 */
function numberPlaceholder(field) {
  if (field.defaultText) return field.defaultText;
  const example = field.examples.find((value) => typeof value === "number");
  return example === undefined ? "" : t(formTexts.example, { value: inputText(example) });
}

/**
 * A number field of a generated form.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, onInput: (text: string) => void}} props the field, the control's
 *   id, the typed text, the message of a check, whether a value is required now, and the
 *   change handler
 * @returns {object} the field
 */
export function NumberField({ field, id, value, error, required, disabled, onInput }) {
  return html`
    <div class=${`opt${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <span class="ibox">
        <input
          id=${id}
          type="text"
          inputmode=${field.kind === "integer" ? "numeric" : "decimal"}
          autocomplete="off"
          spellcheck=${false}
          value=${value ?? ""}
          placeholder=${numberPlaceholder(field)}
          disabled=${disabled}
          aria-invalid=${error ? "true" : "false"}
          aria-required=${required ? "true" : "false"}
          aria-describedby=${describedBy(field, id, error)}
          onInput=${(event) => onInput(event.currentTarget.value)}
        />
        <span class="unit">${field.unitLabel || NO_UNIT}</span>
      </span>
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}
