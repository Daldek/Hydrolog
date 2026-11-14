// Parts every control of a generated form shares: the label with the option's name, the
// flags „wymagane” and „domyślnie …”, the help text from the catalog and the message of a
// check (plan D11; the mockup's `.opt`).

import { html } from "../html.js";
import { common, t } from "../labels/common.js";

/**
 * Render a catalog text with its `code` spans as <code> elements (no HTML is parsed).
 *
 * @param {string} text the text, e.g. "Razem z `k_min`."
 * @returns {Array<string|object>} children for htm
 */
export function richText(text) {
  return String(text || "")
    .split("`")
    .map((part, index) => (index % 2 ? html`<code>${part}</code>` : part));
}

/**
 * Split a message of a check into its sentence and machine reason ("… · maximum").
 *
 * @param {string} message the message
 * @returns {{text: string, reason: string|null}} the parts
 */
export function splitReason(message) {
  const text = String(message || "");
  const cut = text.lastIndexOf(" · ");
  if (cut < 0) return { text, reason: null };
  const reason = text.slice(cut + 3);
  return /^[a-z_-]+$/.test(reason) ? { text: text.slice(0, cut), reason } : { text, reason: null };
}

/**
 * The flag beside a label: „wymagane” or „domyślnie 0,2”.
 *
 * @param {{field: object, required: boolean}} props the field and whether it is required now
 * @returns {object|null} the flag
 */
function FieldFlag({ field, required }) {
  if (required) return html`<span class="req">${common.required}</span>`;
  if (field.defaultText !== null && field.defaultText !== "") {
    return html`<span class="opt-flag">${t(common.defaultIs, { value: field.defaultText })}</span>`;
  }
  return null;
}

/**
 * The label of a field: its Polish label (when the GUI has one), the option's name in
 * monospace and the flag.
 *
 * @param {{field: object, id: string, required: boolean, as?: string}} props the field, its
 *   control's id, whether it is required now, and the element ("label" or "span")
 * @returns {object} the label
 */
export function FieldLabel({ field, id, required, as = "label" }) {
  const inner = html`
    ${field.label ? html`<span class="lbl-text">${field.label}</span>` : null}
    <code>${field.name}</code>
    <${FieldFlag} field=${field} required=${required} />
  `;
  return as === "label"
    ? html`<label for=${id}>${inner}</label>`
    : html`<span class="label-row" id=${`${id}-label`}>${inner}</span>`;
}

/**
 * The help text and the message of a field.
 *
 * @param {{field: object, id: string, error?: string, extra?: object}} props the field, its
 *   control's id, the message of a check, and more help after the catalog's text
 * @returns {object} the hint and the message
 */
export function FieldNotes({ field, id, error, extra }) {
  const message = error ? splitReason(error) : null;
  return html`
    ${field.description || extra
      ? html`<span class="hint" id=${`${id}-hint`}>${richText(field.description)}${extra ? html` ${extra}` : null}</span>`
      : null}
    ${message
      ? html`<span class="err" id=${`${id}-err`} role="alert">${message.text}${message.reason
          ? html` <span class="reason">· ${message.reason}</span>`
          : null}</span>`
      : null}
  `;
}

/**
 * The aria-describedby of a control: its hint and its message.
 *
 * @param {object} field the field
 * @param {string} id the control's id
 * @param {string} [error] the message of a check
 * @returns {string|undefined} the ids
 */
export function describedBy(field, id, error) {
  const ids = [];
  if (field.description) ids.push(`${id}-hint`);
  if (error) ids.push(`${id}-err`);
  return ids.length ? ids.join(" ") : undefined;
}
