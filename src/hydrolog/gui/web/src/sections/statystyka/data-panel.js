// The panel Dane of „Statystyka przepływów”: the series (a file of the session with its
// columns read from the header, or pasted annual maxima; before either, a hint and the
// guide's worked example), the combinations of distribution and fit method shown (filters of
// the one run of all of them) and the return periods. The fields are the catalog's
// (forms/model.js, the generated controls), laid out as the mockup's steps.

import { describedBy, FieldLabel, FieldNotes, richText } from "../../controls/field.js";
import { FileField } from "../../controls/file-field.js";
import { HandoffImport, HandoffOrigin } from "../../handoff/handoff-panel.js";
import { SeriesField } from "../../controls/series-field.js";
import { TextField } from "../../controls/text-field.js";
import { bytes, plural } from "../../format.js";
import { isRequired } from "../../forms/model.js";
import { html } from "../../html.js";
import { t } from "../../labels/common.js";
import { errors as errorTexts } from "../../labels/errors.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { routeHash } from "../../router.js";
import { Seg } from "../../ui/seg.js";
import { EmptyHint } from "../../ui/empty-hint.js";
import { InfoButton } from "../../ui/info-button.js";
import { legendName, methodLegend } from "./charts.js";
import { columnOption, DISTRIBUTION_CLASS, DISTRIBUTIONS, FIT_METHODS, METHOD_CLASS, resolveColumn, shortNumber } from "./state.js";
import { Stroke } from "./swatch.js";

const ID = "st";

/** The other commands of the group `stats`, run in „Wszystkie polecenia”. */
const OTHER_COMMANDS = ["stats low-flow", "stats low-flow-sequences", "stats mann-kendall", "stats homogeneity", "stats characteristic", "stats monthly", "stats daily"];

/**
 * A step of the panel: a numbered, collapsible part of the calculation.
 *
 * @param {{num: number, title: string, meta?: string, children: any}} props the step
 * @returns {object} the step
 */
function Step({ num: number, title, meta, children }) {
  return html`
    <details class="step" open>
      <summary>
        <span class="step-num">${number}</span><span class="title">${title}</span>${meta ? html`<span class="meta">${meta}</span>` : null}
        <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
      </summary>
      <div class="step-body">${children}</div>
    </details>
  `;
}

/**
 * A column of the file: a choice among the columns of its header, or a typed name while the
 * header is not known.
 *
 * @param {{field: object, value: string|undefined, error?: string, required: boolean,
 *   columns: string[]|null, none?: string, onInput: (value: string) => void}} props the
 *   catalog's field, the value, its message, whether it is required, the file's columns
 *   (null when unknown) and the text of „no column” (for an optional column)
 * @returns {object} the field
 */
function ColumnField({ field, value, error, required, columns, none, onInput }) {
  const id = `${ID}-${field.name}`;
  if (!columns) return html`<${TextField} field=${field} id=${id} value=${value} error=${error} required=${required} onInput=${onInput} />`;
  const current = value || "";
  const known = !current || resolveColumn(current, columns) !== null;
  return html`
    <div class=${`opt${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <select
        id=${id}
        value=${known && current ? columnOption(resolveColumn(current, columns), columns) : current}
        aria-invalid=${error ? "true" : "false"}
        aria-required=${required ? "true" : "false"}
        aria-describedby=${describedBy(field, id, error)}
        onChange=${(event) => onInput(event.currentTarget.value)}
      >
        ${none !== undefined ? html`<option value="">${none}</option>` : null}
        ${!known ? html`<option value=${current}>${current}</option>` : null}
        ${columns.map((column) => html`<option value=${columnOption(column, columns)}>${column}</option>`)}
      </select>
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}

/**
 * The box naming the chosen file: its rows and columns, or what went wrong while reading it.
 *
 * @param {{path: string, file: object|null, preview: object}} props the file's path, its
 *   entry in the session (null when it is not there) and the columns read
 * @returns {object} the box
 */
function FileBox({ path, file, preview }) {
  const name = path.replace(/^in\//, "");
  let line;
  let sub = null;
  if (!file) {
    line = t(texts.file.missing, { name });
  } else if (preview.state === "ok") {
    line = t(texts.file.summary, {
      name,
      rows: plural(preview.table.rows, texts.rowForms),
      columns: preview.table.columns.map((column) => `\`${column}\``).join(", "),
    });
    sub = t(texts.file.session, { size: bytes(file.size_bytes) });
  } else if (preview.state === "error") {
    line = t(texts.file.unreadable, { message: preview.message });
  } else {
    line = texts.file.loading;
  }
  return html`
    <div class="handoff" data-file=${path}>
      <svg class="file-ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>
      <div>
        <span role="status">${richText(line)}</span>
        ${sub ? html`<span class="muted">${sub}</span>` : null}
      </div>
    </div>
  `;
}

/**
 * A multiple choice of the combinations shown („Rozkłady”, „Metody estymacji”): a chip per
 * value with its swatch, pressed while shown; the last one pressed stays, so something is
 * always shown. Nothing is recomputed: the run fitted every combination.
 *
 * @param {{name: string, label: string, items: Array<{value: string, label: string,
 *   cls: string, title?: string}>, ticked: string[], onToggle: (value: string, on: boolean)
 *   => void}} props the filter's name, its label, its values (with their swatch classes and
 *   the catalog's meanings), the values ticked and the change of one of them
 * @returns {object} the field
 */
function ShownChoice({ name, label, items, ticked, onToggle }) {
  const labelId = `${ID}-${name}-label`;
  return html`
    <div class="field st-shown" data-shown=${name}>
      <span class="label" id=${labelId}>${label}</span>
      <div class="chips" role="group" aria-labelledby=${labelId}>
        ${items.map((item) => {
          const on = ticked.includes(item.value);
          return html`<button
            type="button"
            class=${`chip${on ? " on" : ""}`}
            aria-pressed=${on ? "true" : "false"}
            disabled=${on && ticked.length === 1}
            title=${item.title}
            onClick=${() => onToggle(item.value, !on)}
          ><${Stroke} cls=${item.cls} />${item.label}</button>`;
        })}
      </div>
    </div>
  `;
}

/** The options the panel shows, by the source of the series. */
const SHOWN = {
  file: ["input_file", "value_column", "date_column", "return_periods"],
  paste: ["values", "return_periods"],
};

/**
 * The panel Dane.
 *
 * @param {{model: object, values: object, source: "file"|"paste", errors: object,
 *   onValue: (name: string, value: any) => void, onSource: (source: string) => void,
 *   session: object|null, preview: object, shown: {distributions: string[],
 *   methods: string[]}, onShown: (filter: "distributions"|"methods", value: string,
 *   on: boolean) => void, periods: number[], stressed: number|null,
 *   onChosen: (period: number|null) => void, seriesMeta: string|null, formId: string}}
 *   props the catalog's model and the form's values, the source, the messages by option, the
 *   change handlers, the session, the columns of the chosen file, the combinations shown and
 *   the change of a filter, the return periods with the stressed one (null for „brak”), the
 *   length of the series computed and the form's id (the result follows every change: no
 *   submit)
 * @returns {object} the panel's body
 */
export function DataPanel(props) {
  const { model, values, source, received, errors, onValue, onSource, session, preview, shown, onShown, periods, stressed, onChosen, seriesMeta, formId } = props;
  const field = (name) => model.fields.find((item) => item.name === name);
  // The catalog's Polish meaning of a value of `distribution` or `fit_method`: a chip's title
  const meaning = (name, value) => {
    const choice = (field(name)?.choices || []).find((item) => item.value === value);
    return choice ? choice.meaning : undefined;
  };
  const required = (item) => isRequired(model, item, values);
  const error = (name) => (typeof errors[name] === "object" ? errors[name].text : errors[name]);
  const path = values.input_file || "";
  const file = ((session && session.files) || []).find((item) => item.path === path) || null;
  const columns = preview.state === "ok" ? preview.table.columns : null;
  const loose = Object.entries(errors)
    .filter(([name, message]) => message && !SHOWN[source].includes(name))
    .map(([, message]) => message);
  const titled = loose.find((message) => typeof message === "object" && message.title);
  const fits = shown.distributions.length * shown.methods.length;
  const rows = preview.state === "ok" && source === "file" ? plural(preview.table.rows, texts.rowForms) : null;
  return html`
    <form id=${formId} class="st-form" novalidate onSubmit=${(event) => event.preventDefault()}>
      ${loose.length
        ? html`<div class="form-errors" role="alert">
            <strong>${titled ? titled.title : errorTexts.aboveForm}</strong>
            <ul>${loose.map((message) => html`<li>${richText(typeof message === "object" ? message.text : message)}</li>`)}</ul>
          </div>`
        : null}
      <div class="steps">
        <${Step} num=${1} title=${texts.steps.series} meta=${seriesMeta || rows}>
          <div class="btn-row"><${HandoffImport} series=${true} /></div>
          ${received ? html`<${HandoffOrigin} received=${received} small=${true} />` : null}
          <div class="field">
            <span class="label" id=${`${ID}-source-label`}>${texts.source}</span>
            <${Seg}
              items=${[
                { value: "file", label: texts.sources.file },
                { value: "paste", label: texts.sources.paste },
              ]}
              value=${source}
              onChange=${onSource}
              labelledBy=${`${ID}-source-label`}
              full=${true}
            />
          </div>
          ${source === "file"
            ? html`
                ${path
                  ? html`<${FileBox} path=${path} file=${file} preview=${preview} />`
                  : html`<${EmptyHint} text=${texts.file.empty} anchor="przyklad-statystyka" name="statystyka" />`}
                <${FileField}
                  field=${field("input_file")}
                  id=${`${ID}-input_file`}
                  value=${path}
                  error=${error("input_file")}
                  required=${required(field("input_file"))}
                  onInput=${(value) => onValue("input_file", value)}
                />
                <${ColumnField}
                  field=${field("value_column")}
                  value=${values.value_column}
                  error=${error("value_column")}
                  required=${required(field("value_column"))}
                  columns=${columns}
                  onInput=${(value) => onValue("value_column", value)}
                />
                <${ColumnField}
                  field=${field("date_column")}
                  value=${values.date_column}
                  error=${error("date_column")}
                  required=${false}
                  columns=${columns}
                  none=${texts.noDates}
                  onInput=${(value) => onValue("date_column", value)}
                />
                <p class="note">${richText(texts.dailyNote)}</p>
              `
            : html`
                ${values.values ? null : html`<${EmptyHint} text=${texts.pasteEmpty} anchor="przyklad-statystyka" name="statystyka" />`}
                <${SeriesField}
                  field=${field("values")}
                  id=${`${ID}-values`}
                  value=${values.values}
                  error=${error("values")}
                  required=${required(field("values"))}
                  onInput=${(value) => onValue("values", value)}
                />
                <p class="note">${texts.pasteNote}</p>
              `}
        </${Step}>
        <${Step} num=${2} title=${texts.steps.distributions} meta=${t(texts.distributionsMeta, { count: fits })}>
          <${ShownChoice}
            name="distributions"
            label=${texts.shown.distributions}
            items=${DISTRIBUTIONS.map((name) => ({ value: name, label: legendName(name), cls: DISTRIBUTION_CLASS[name], title: meaning("distribution", name) }))}
            ticked=${shown.distributions}
            onToggle=${(value, on) => onShown("distributions", value, on)}
          />
          <${ShownChoice}
            name="methods"
            label=${texts.shown.methods}
            items=${FIT_METHODS.map((method) => ({ value: method, label: methodLegend(method), cls: METHOD_CLASS[method], title: meaning("fit_method", method) }))}
            ticked=${shown.methods}
            onToggle=${(value, on) => onShown("methods", value, on)}
          />
          <p class="note">${texts.shown.note} <${InfoButton} id="stats-fit-method" /></p>
          <${SeriesField}
            field=${field("return_periods")}
            id=${`${ID}-return_periods`}
            value=${values.return_periods}
            error=${error("return_periods")}
            required=${false}
            onInput=${(value) => onValue("return_periods", value)}
          />
          ${periods.length
            ? html`<div class="field st-chosen">
                <span class="label" id=${`${ID}-chosen-label`}>${texts.chosen}</span>
                <div class="chips" role="group" aria-labelledby=${`${ID}-chosen-label`}>
                  <button
                    type="button"
                    class=${`chip${stressed === null ? " on" : ""}`}
                    aria-pressed=${stressed === null ? "true" : "false"}
                    title=${texts.chosenNoneItem}
                    onClick=${() => onChosen(null)}
                  >${texts.chosenNone}</button>
                  ${periods.map(
                    (period) => html`<button
                      type="button"
                      class=${`chip${period === stressed ? " on" : ""}`}
                      aria-pressed=${period === stressed ? "true" : "false"}
                      title=${t(texts.chosenItem, { t: shortNumber(period), p: shortNumber(100 / period) })}
                      onClick=${() => onChosen(period)}
                    >${shortNumber(period, 6)}</button>`,
                  )}
                </div>
                <span class="hint">${texts.chosenHint}</span>
              </div>`
            : null}
        </${Step}>
      </div>
      <p class="note st-more">
        ${texts.more}
        ${OTHER_COMMANDS.map(
          (command, index) => html`${index ? ", " : " "}<a href=${routeHash("polecenia", command.split(" "))} title=${t(texts.moreLink, { command })}><code>${command.replace("stats ", "")}</code></a>`,
        )}.
      </p>
    </form>
  `;
}
