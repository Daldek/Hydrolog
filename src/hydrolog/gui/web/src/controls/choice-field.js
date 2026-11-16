// Choices of a generated form (plan D11): a `string` with `enum` is a segmented control up
// to four values and a select above, with the catalog's Polish meaning of the chosen value
// below; a `boolean` is a checkbox („force” as „Zastąp istniejące”, „check” as „Tylko
// plan”).

import { html } from "../html.js";
import { formTexts } from "../labels/options.js";
import { Seg } from "../ui/seg.js";
import { describedBy, FieldLabel, FieldNotes, richText } from "./field.js";

/** The most values shown as a segmented control. */
const SEGMENTED_MAX = 4;

/**
 * The value a choice shows: the value given, else the default, else none ("").
 *
 * @param {object} field a field of fieldModel
 * @param {string|undefined} value the value given
 * @returns {string} the value shown
 */
function shownChoice(field, value) {
  if (value !== undefined && value !== null && value !== "") return value;
  return field.default === null ? "" : String(field.default);
}

/**
 * A choice among the catalog's values.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, select?: boolean, onInput: (value: string) => void}} props the
 *   field, the control's id, the value, the message of a check, whether a value is
 *   required now, a select whatever the number of values (values too long for a segmented
 *   control in a narrow panel), and the change handler
 * @returns {object} the field
 */
export function ChoiceField({ field, id, value, error, required, disabled, select = false, onInput }) {
  const current = shownChoice(field, value);
  const optional = !required && field.default === null;
  const items = [
    ...(optional ? [{ value: "", label: formTexts.none, title: formTexts.noneTitle }] : []),
    ...field.choices.map((choice) => ({ value: choice.value, label: choice.value, title: choice.meaning })),
  ];
  const meaning = field.choices.find((choice) => choice.value === current);
  const segmented = !select && field.choices.length <= SEGMENTED_MAX;
  return html`
    <div class=${`opt${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} as=${segmented ? "span" : "label"} />
      ${segmented
        ? html`<${Seg}
            items=${items}
            value=${current}
            onChange=${disabled ? () => {} : onInput}
            labelledBy=${`${id}-label`}
            className="choice-seg"
            full=${items.length > 1}
          />`
        : html`<select
            id=${id}
            value=${current}
            disabled=${disabled}
            aria-invalid=${error ? "true" : "false"}
            aria-describedby=${describedBy(field, id, error)}
            onChange=${(event) => onInput(event.currentTarget.value)}
          >
            ${items.map(
              (item) => html`<option value=${item.value}>${item.value === "" ? item.label : choiceText(item)}</option>`,
            )}
          </select>`}
      ${meaning && meaning.meaning
        ? html`<span class="meaning"><code>${meaning.value}</code> ${richText(meaning.meaning)}</span>`
        : null}
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}

/**
 * The text of a select's option: the value and a short meaning.
 *
 * @param {{label: string, title?: string}} item the choice
 * @returns {string} "forest — Las"
 */
function choiceText(item) {
  const meaning = String(item.title || "").replace(/`/g, "").replace(/\.$/, "");
  return meaning && meaning.length <= 48 ? `${item.label} — ${meaning}` : item.label;
}

/**
 * A boolean option as a checkbox; an untouched box shows the default.
 *
 * @param {{field: object, id: string, value?: boolean, error?: string, disabled?: boolean,
 *   onInput: (value: boolean) => void}} props the field, the control's id, the value, the
 *   message of a check and the change handler
 * @returns {object} the field
 */
export function CheckField({ field, id, value, error, disabled, onInput }) {
  const checked = typeof value === "boolean" ? value : Boolean(field.default);
  return html`
    <div class=${`opt opt-check${error ? " invalid" : ""}`} data-option=${field.name}>
      <label class="check" for=${id}>
        <input
          id=${id}
          type="checkbox"
          checked=${checked}
          disabled=${disabled}
          aria-describedby=${describedBy(field, id, error)}
          onChange=${(event) => onInput(event.currentTarget.checked)}
        />
        ${field.label ? html`<span class="lbl-text">${field.label}</span>` : null}
        <code>${field.name}</code>
      </label>
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}
