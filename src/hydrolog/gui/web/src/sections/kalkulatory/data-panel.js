// The panel Dane of „Kalkulatory”: the list of the sixteen calculators with a group and a
// search, the watershed of Hydrogram zlewni, and the chosen calculator's form: the methods
// and overland fields of the tc comparison, or a command's form generated from the catalog
// (forms/command-form.js).

import { NumberField } from "../../controls/number-field.js";
import { richText } from "../../controls/field.js";
import { inputText, plural } from "../../format.js";
import { CommandForm } from "../../forms/command-form.js";
import { commandEntry } from "../../forms/model.js";
import { html, useEffect, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { routeHash } from "../../router.js";
import { EmptyHint } from "../../ui/empty-hint.js";
import { COMPARE, filterCalculators, GROUPS, OVERLAND_FIELDS, TC_METHODS } from "./state.js";

/**
 * The searchable list of the calculators.
 *
 * @param {{docs: Map<string, object>, group: string, query: string, current: string,
 *   active: boolean, onGroup: (group: string) => void, onQuery: (query: string) => void,
 *   onPick: (id: string) => void}} props the catalog documents, the group and the search,
 *   the chosen calculator, whether the section is shown and the handlers
 * @returns {object} the list
 */
export function CalculatorList({ docs, group, query, current, active, onGroup, onQuery, onPick }) {
  const list = useRef(null);
  const shown = filterCalculators(docs, group, query);
  useEffect(() => {
    if (!active || !list.current) return;
    const item = list.current.querySelector(".cmd-item.active");
    if (item && list.current.clientHeight) list.current.scrollTop = Math.max(0, item.offsetTop - list.current.clientHeight / 3);
  }, [active, current]);
  const summaryOf = (id) => {
    if (id === COMPARE) return texts.compare.summary;
    const doc = docs.get(id);
    const polish = doc ? (commandEntry(doc).i18n || {}).pl : null;
    return (polish && polish.summary) || "";
  };
  return html`
    <div class="cmd-tools">
      <select class="sel-sm" aria-label=${texts.groupSelect} value=${group} onChange=${(event) => onGroup(event.currentTarget.value)}>
        <option value="">${texts.allGroups}</option>
        ${GROUPS.map((item) => html`<option value=${item}>${texts.groups[item]}</option>`)}
      </select>
      <span class="search">
        <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="5" /><path d="M13 13l4 4" /></svg>
        <input type="search" placeholder=${texts.search} aria-label=${texts.searchLabel} value=${query} onInput=${(event) => onQuery(event.currentTarget.value)} />
      </span>
    </div>
    <ul class="cmd-list short" ref=${list} aria-label=${texts.listLabel}>
      ${shown.map(
        (item) => html`<li class=${`cmd-item${item.id === current ? " active" : ""}`} key=${item.id} data-calculator=${item.id}>
          <button type="button" aria-current=${item.id === current ? "true" : undefined} onClick=${() => onPick(item.id)}>
            ${item.id === COMPARE ? html`<strong>${texts.compare.name}</strong>` : html`<code>${item.id}</code>`}
            <span>${richText(summaryOf(item.id))}</span>
          </button>
        </li>`,
      )}
      ${shown.length ? null : html`<li class="cmd-empty">${texts.empty}</li>`}
    </ul>
    <p class="sr-only" role="status">${plural(shown.length, texts.calculatorForms)}</p>
  `;
}

/**
 * The watershed of Hydrogram zlewni: its name and main fields, a button that fills the form
 * with them, or a pointer to Hydrogram zlewni when it has none.
 *
 * @param {{watershed: object|null, onFill?: () => void, fill?: {text?: string,
 *   error?: string}|null}} props the watershed, the fill handler (a form that takes its
 *   fields) and the state of the last fill
 * @returns {object} the box
 */
export function WatershedBox({ watershed, onFill, fill }) {
  if (!watershed) {
    return html`
      <div class="handoff sm kc-watershed" data-watershed="none">
        <img src="nogat/marks/hydrolog.svg" alt="" />
        <div>
          ${texts.watershed.none}
          <a href=${routeHash("hydrogram")}>${texts.watershed.open}</a>
          <${EmptyHint} anchor="przyklad-kalkulatory" name="kalkulatory" />
        </div>
      </div>
    `;
  }
  const value = (name) => (typeof watershed[name] === "number" ? inputText(watershed[name]) : "–");
  return html`
    <div class="handoff sm kc-watershed" data-watershed=${watershed.name || ""}>
      <img src="nogat/marks/hydrolog.svg" alt="" />
      <div>
        <strong>${texts.watershed.from}</strong>: ${watershed.name || texts.watershed.unnamed}
        <span class="muted">${t(texts.watershed.details, {
          area: value("area_km2"),
          length: value("channel_length_km"),
          slope: value("channel_slope_m_per_m"),
          cn: value("cn"),
        })}</span>
        ${fill && fill.text ? html`<span class="muted" role="status">${richText(fill.text)}</span>` : null}
        ${fill && fill.error ? html`<span class="err" role="alert">${richText(fill.error)}</span>` : null}
      </div>
      ${onFill ? html`<button class="btn sm" type="button" title=${texts.watershed.fillTitle} onClick=${onFill}>${texts.watershed.fill}</button>` : null}
    </div>
  `;
}

/**
 * The form of the tc comparison: the methods and the overland fields of the watershed.
 *
 * @param {{watershed: object|null, methods: Object<string, boolean>,
 *   overrides: Object<string, string>, fields: object[], errors: Object<string, string>,
 *   problem: string|null, formId: string, onMethod: (method: string, on: boolean) => void,
 *   onOverride: (name: string, text: string) => void, onSubmit: () => void}} props the
 *   watershed, the chosen methods, the overland fields as typed, their catalog fields, their
 *   messages, the message of the methods, the form's id and the handlers
 * @returns {object} the form
 */
export function CompareForm({ watershed, methods, overrides, fields, errors, problem, formId, onMethod, onOverride, onSubmit }) {
  const shown = (name) => {
    if (overrides[name] !== undefined) return overrides[name];
    return watershed && typeof watershed[name] === "number" ? inputText(watershed[name]) : "";
  };
  return html`
    <form class="cmd-form kc-compare" id=${formId} novalidate onSubmit=${(event) => {
      event.preventDefault();
      onSubmit();
    }}>
      <div class="cmd-head">
        <h3>${texts.compare.name}</h3>
        <p>${richText(texts.compare.head)}</p>
      </div>
      <${WatershedBox} watershed=${watershed} />
      <div class="field">
        <span class="label" id="kc-methods-label">${texts.compare.methods}<span class="key">method</span></span>
        <div class="check-grid" role="group" aria-labelledby="kc-methods-label">
          ${TC_METHODS.map(
            (method) => html`<label class="check">
              <input type="checkbox" checked=${Boolean(methods[method])} onChange=${(event) => onMethod(method, event.currentTarget.checked)} />
              ${texts.methods[method]}
            </label>`,
          )}
        </div>
        ${problem ? html`<span class="err" role="alert">${problem}</span>` : null}
      </div>
      <fieldset class="form-section">
        <legend>${texts.compare.overland}</legend>
        ${OVERLAND_FIELDS.map((name) => {
          const field = fields.find((item) => item.name === name);
          return field
            ? html`<${NumberField}
                key=${name}
                field=${field}
                id=${`kc-${name}`}
                value=${shown(name)}
                error=${errors[name]}
                required=${false}
                onInput=${(text) => onOverride(name, text)}
              />`
            : null;
        })}
        <p class="note">${texts.compare.overlandHint}</p>
      </fieldset>
    </form>
  `;
}

/**
 * The form of a calculator's command, generated from the catalog, under the watershed.
 *
 * @param {{doc: object, values: object, errors: object, watershed: object|null,
 *   fillable: boolean, fill: object|null, formId: string, onChange: (values: object) => void,
 *   onFill: () => void, onSubmit: () => void}} props the command's document, the form's
 *   values and messages, the watershed, whether the command takes its fields, the state of
 *   the last fill, the form's id and the handlers
 * @returns {object} the form
 */
export function CalculatorForm({ doc, values, errors, watershed, fillable, fill, formId, onChange, onFill, onSubmit }) {
  return html`
    ${fillable ? html`<${WatershedBox} watershed=${watershed} onFill=${watershed ? onFill : undefined} fill=${fill} />` : null}
    <${CommandForm}
      key=${commandEntry(doc).name}
      command=${doc}
      values=${values}
      onChange=${onChange}
      errors=${errors}
      formId=${formId}
      idPrefix=${`kc-${commandEntry(doc).operation_id || "form"}`}
      onSubmit=${onSubmit}
    />
  `;
}
