// The parts the steps of „Hydrogram zlewni” are made of, shared by its panel Dane and by
// Sieć, which shows its network's rainfall with Hydrogram's step 2 (plan
// 2026-11-10-network-wizard, D1, D4): a numbered step, a dense form row (the mockup's
// `.frow`: the label with the symbol and the option's key, the value with its unit, a hint,
// whom the field is needed for, the change mark and the message of a check), a select row,
// and the texts the rows show. A control's id is the host's prefix and the field's name
// (`hg-total_mm`), so two hosts mounted together never share one.

import { splitReason } from "../../controls/field.js";
import { inputText, roundedText } from "../../format.js";
import { html } from "../../html.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { UNITS, changedFrom, numberOf, originText } from "./state.js";

/**
 * A duration for people: whole hours as hours, otherwise minutes to 0,1 min.
 *
 * @param {number|string} minutes the duration [min]
 * @returns {string} e.g. "12 h", "90 min"
 */
export function durationText(minutes) {
  const value = numberOf(minutes);
  if (value === null) return "–";
  return value % 60 === 0 ? t(texts.rain.hours, { value: inputText(value / 60) }) : t(texts.rain.minutes, { value: roundedText(value, 1) });
}

/**
 * A number shown with four significant digits as an input would hold it ("3,631").
 *
 * @param {number|null|undefined} value the number
 * @returns {string} the text, "" without a number
 */
export function shortText(value) {
  return typeof value === "number" && Number.isFinite(value) ? inputText(Number(value.toPrecision(4))) : "";
}

/**
 * A slope in m/m as percent, for the hint beside the field: "= 1,42 %".
 *
 * @param {unknown} text the slope as typed [m/m]
 * @returns {string|null} the hint, null without a number
 */
export function percentHint(text) {
  const value = numberOf(text);
  return value === null ? null : t(texts.percent, { value: inputText(Number((value * 100).toPrecision(6))) });
}

/**
 * The label of a field: its Polish name, the symbol and the option's key.
 *
 * @param {{name: string, id: string, keyText?: string|false}} props the field, its
 *   control's id and the key shown (default: the name; false: none)
 * @returns {object} the label
 */
function FieldName({ name, id, keyText }) {
  const words = texts.fields[name] || { label: name };
  const key = keyText === false ? null : keyText || name;
  return html`<label for=${id}>${words.label}${words.symbol ? html` <i class="sym">${words.symbol}</i>` : null}${key ? html`<span class="key">${key}</span>` : null}</label>`;
}

/**
 * The mark of a field changed from where the watershed came from, with „przywróć”.
 *
 * @param {{origin: object|null, name: string, text: unknown, onRestore: (name: string, text:
 *   string) => void}} props the origin, the field, its typed value and the handler
 * @returns {object|null} the mark
 */
function Changed({ origin, name, text, onRestore }) {
  if (!changedFrom(origin, name, text)) return null;
  const before = originText(origin, name);
  const shown = before === null ? "–" : before;
  return html`
    <span class="chg">
      <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M13.5 3.5l3 3L7 16H4v-3z" /></svg>
      ${t(texts.changed, { source: origin.label, value: shown })}
      <button
        class="link-btn"
        type="button"
        title=${t(texts.restoreTitle, { value: shown, source: origin.label })}
        onClick=${() => onRestore(name, before === null ? "" : before)}
      >${texts.restore}</button>
    </span>
  `;
}

/**
 * The message of a check under a field: an error (red) or a warning (amber).
 *
 * @param {{id: string, message?: string, warning?: boolean}} props the control's id, the
 *   message and whether it is a warning
 * @returns {object|null} the message
 */
function FieldMessage({ id, message, warning = false }) {
  if (!message) return null;
  const words = splitReason(message);
  return html`<span class=${warning ? "warn" : "err"} id=${`${id}-${warning ? "warn" : "err"}`} role=${warning ? "status" : "alert"}>${words.text}${words.reason
    ? html` <span class="reason">· ${words.reason}</span>`
    : null}</span>`;
}

/**
 * A dense form row: label with the symbol and key, the value with its unit, a hint, whom
 * the field is needed for, the change mark and the message of a check (an error before a
 * warning).
 *
 * @param {{prefix: string, name: string, value?: string, error?: string, warning?: string,
 *   need?: string, onInput: (text: string) => void, placeholder?: string, keyText?: string,
 *   aux?: string|null, origin?: object|null, onRestore?: (name: string, text: string) =>
 *   void, info?: object|null, readOnly?: boolean, text?: boolean}} props the host's prefix
 *   of ids, the field and its parts
 * @returns {object} the row
 */
export function Row({ prefix, name, value, error, warning, need, onInput, placeholder, keyText, aux, origin, onRestore, info, readOnly, text }) {
  const id = `${prefix}-${name}`;
  const edited = Boolean(origin) && changedFrom(origin, name, value);
  const level = error ? "invalid" : warning ? "warning" : "";
  const classes = ["frow", text ? "wide" : "", edited ? "edited" : "", level].filter(Boolean).join(" ");
  let described;
  if (error) described = `${id}-err`;
  else if (warning) described = `${id}-warn`;
  else if (need) described = `${id}-need`;
  const input = html`<input
    id=${id}
    type="text"
    inputmode=${text ? undefined : "decimal"}
    autocomplete="off"
    spellcheck=${false}
    value=${value ?? ""}
    placeholder=${placeholder || ""}
    readonly=${readOnly}
    aria-invalid=${error ? "true" : "false"}
    aria-describedby=${described}
    onInput=${(event) => onInput(event.currentTarget.value)}
  />`;
  return html`
    <div class=${classes} data-field=${name} data-level=${level || undefined}>
      ${info
        ? html`<span class="label-row"><${FieldName} name=${name} id=${id} keyText=${keyText} />${info}</span>`
        : html`<${FieldName} name=${name} id=${id} keyText=${keyText} />`}
      ${text ? input : html`<span class="ibox">${input}<span class="unit">${UNITS[name] || "–"}</span></span>`}
      ${aux ? html`<span class="aux">${aux}</span>` : null}
      ${origin ? html`<${Changed} origin=${origin} name=${name} text=${value} onRestore=${onRestore} />` : null}
      ${error
        ? html`<${FieldMessage} id=${id} message=${error} />`
        : warning
          ? html`<${FieldMessage} id=${id} message=${warning} warning=${true} />`
          : null}
      ${!error && need ? html`<span class="need" id=${`${id}-need`}>${need}</span>` : null}
    </div>
  `;
}

/**
 * A select in a form row (PMAXTP's probability, duration and method), empty until chosen.
 *
 * @param {{prefix: string, name: string, value: string, options: readonly string[], label:
 *   (value: string) => string, error?: string, keyText?: string|false, onChange: (value:
 *   string) => void}} props the host's prefix of ids, the field, its value, the values
 *   offered and their words, the message of a check, the key shown and the handler
 * @returns {object} the row
 */
export function SelectRow({ prefix, name, value, options, label, error, keyText, onChange }) {
  const id = `${prefix}-${name}`;
  return html`
    <div class=${`frow${error ? " invalid" : ""}`} data-field=${name} data-level=${error ? "invalid" : undefined}>
      <${FieldName} name=${name} id=${id} keyText=${keyText} />
      <select
        id=${id}
        class="sel-sm"
        value=${value}
        aria-invalid=${error ? "true" : "false"}
        aria-describedby=${error ? `${id}-err` : undefined}
        onChange=${(event) => onChange(event.currentTarget.value)}
      >
        <option value="" disabled hidden>${texts.rain.choose}</option>
        ${options.map((item) => html`<option value=${item}>${label(item)}</option>`)}
      </select>
      <${FieldMessage} id=${id} message=${error} />
    </div>
  `;
}

/**
 * One step of the calculation: a numbered <details>, open at first.
 *
 * @param {{id: string, number: number, title: string, meta?: string, children: any}} props
 *   the step's id, number, title, the summary on the right and the body
 * @returns {object} the step
 */
export function Step({ id, number, title, meta, children }) {
  return html`
    <details class="step" open data-step=${id}>
      <summary>
        <span class="step-num">${number}</span><span class="title">${title}</span><span class="meta">${meta || ""}</span>
        <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
      </summary>
      <div class="step-body">${children}</div>
    </details>
  `;
}
