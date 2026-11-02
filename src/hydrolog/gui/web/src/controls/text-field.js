// A `string` option without choices (a column name, a label, a date with `format`).

import { html } from "../html.js";
import { describedBy, FieldLabel, FieldNotes } from "./field.js";

/** Placeholders of the string formats the forms check. */
const FORMAT_PLACEHOLDERS = { date: "RRRR-MM-DD", "date-time": "RRRR-MM-DDTgg:mm" };

/**
 * A text of a generated form.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, onInput: (text: string) => void}} props the field, the control's
 *   id, the text, the message of a check, whether a value is required now, and the change
 *   handler
 * @returns {object} the field
 */
export function TextField({ field, id, value, error, required, disabled, onInput }) {
  const example = field.examples.find((item) => typeof item === "string");
  return html`
    <div class=${`opt${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <input
        id=${id}
        type="text"
        autocomplete="off"
        spellcheck="false"
        disabled=${disabled}
        value=${value ?? ""}
        placeholder=${FORMAT_PLACEHOLDERS[field.format] || field.defaultText || example || ""}
        aria-invalid=${error ? "true" : "false"}
        aria-required=${required ? "true" : "false"}
        aria-describedby=${describedBy(field, id, error)}
        onInput=${(event) => onInput(event.currentTarget.value)}
      />
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}
