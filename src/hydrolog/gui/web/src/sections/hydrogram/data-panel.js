// The panel Dane of „Hydrogram zlewni”: the three steps of the author's flow (2026-11-04).
// 1 Zlewnia: where the watershed came from (a WatershedParameters JSON read in the
// browser, or a hand-off with „Wczytaj z Hydrografa”) and its basic fields, CN included.
// 2 Hietogram: PMAXTP (the point, p, the duration and the method; the depth `precip
// pmaxtp` fetched from IMGW-PIB is shown, never typed), a design hyetograph or a series,
// its shape and the time step.
// 3 Hydrogram: the unit hydrograph model, none chosen at first; only the chosen model's
// block (its tc with the tc method's own fields for SCS and Clark, Clark's R, Nash by
// Lutz with the watershed fields Lutz reads or n and K, Snyder with Lc), then the losses
// of SCS-CN common to every model. Once a model is chosen, the fields it needs are marked
// where they live („wymagane dla …”), an empty one is an error (red), a value outside its
// typical range a warning (amber), and step 3 sums them up with a link to each field.
// Every change goes to the section, which checks it and recomputes (plan D13); the steps
// show what the last result gave (tc, CN after AMC, S, Ia, the UH's parameters).

import { SeriesField } from "../../controls/series-field.js";
import { richText, splitReason } from "../../controls/field.js";
import { inputText, num, plural, roundedText } from "../../format.js";
import { seriesTokens } from "../../forms/model.js";
import { HandoffImport } from "../../handoff/handoff-panel.js";
import { html, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { EmptyHint } from "../../ui/empty-hint.js";
import { InfoButton } from "../../ui/info-button.js";
import { infoRanges, infoText, rangeKey, rangeMark, rangeText, symbolOf } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import {
  AMC,
  PEAK_DEFAULTS,
  PMAXTP_DURATIONS,
  PMAXTP_METHODS,
  PMAXTP_PROBABILITIES,
  SHAPES,
  SLOPE_FIELDS,
  TC_BLOCK,
  TC_METHODS,
  UH_MODELS,
  UNITS,
  WATERSHED_STEP,
  changedFrom,
  fieldLabel,
  isEmpty,
  numberOf,
  originText,
  panelFields,
  purposeText,
  stepOf,
  usesLutz,
  usesTc,
} from "./state.js";

/** Icons of the lines of step 3's summary. */
const ICONS = {
  bad: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 4.8v4M8 11.2v.01" /></svg>`,
  warn: html`<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2l6.5 11.5h-13z" /><path d="M8 6.5v3.2M8 11.7v.01" /></svg>`,
  ok: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M5 8.2l2 2 4-4.2" /></svg>`,
};

/**
 * A model's note with Hydrolog's typical ranges of its parameters („typowo n od 1 do 10 (do
 * weryfikacji), K od 10 do 200 min (do weryfikacji)”: a range to be verified says so), or
 * its plain form while they have not arrived.
 *
 * @param {string} id the explanation the ranges are registered with
 * @param {string[]} keys the ranges, "method.parameter"
 * @param {string} text the note, with {ranges}
 * @param {string} plain the note without them
 * @returns {string} the note
 */
function typicalNote(id, keys, text, plain) {
  const entry = infoText(id);
  const words = infoRanges(id)
    .filter((range) => keys.includes(rangeKey(range)))
    .map((range) => {
      const mark = rangeMark(range);
      return `${symbolOf(entry, range.parameter)} ${rangeText(range)}${mark ? ` (${mark})` : ""}`;
    });
  return words.length ? t(text, { ranges: words.join(", ") }) : plain;
}

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
 * Bring a field of the panel into view and focus it, opening its step.
 *
 * @param {string} name the field
 */
function focusField(name) {
  const control = document.getElementById(`hg-${name}`);
  if (!control) return;
  const step = control.closest("details");
  if (step && !step.open) step.open = true;
  control.scrollIntoView({ block: "center" });
  control.focus({ preventScroll: true });
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
 * A dense form row (the mockup's `.frow`): label with the symbol and key, the value with its
 * unit, a hint, whom the field is needed for, the change mark and the message of a check
 * (an error before a warning).
 *
 * @param {{name: string, value?: string, error?: string, warning?: string, need?: string,
 *   onInput: (text: string) => void, placeholder?: string, keyText?: string, aux?:
 *   string|null, origin?: object|null, onRestore?: (name: string, text: string) => void,
 *   info?: object|null, readOnly?: boolean, text?: boolean}} props the field and its parts
 * @returns {object} the row
 */
function Row({ name, value, error, warning, need, onInput, placeholder, keyText, aux, origin, onRestore, info, readOnly, text }) {
  const id = `hg-${name}`;
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
 * One step of the calculation: a numbered <details>, open at first.
 *
 * @param {{id: string, number: number, title: string, meta?: string, children: any}} props
 *   the step's id, number, title, the summary on the right and the body
 * @returns {object} the step
 */
function Step({ id, number, title, meta, children }) {
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

/**
 * A row of a field of the watershed, with its change mark and checks.
 *
 * @param {object} props see DataPanel, and `name` the field and `extra` more props of Row
 * @returns {object} the row
 */
function WatershedRow({ name, inputs, errors, warnings, required, setField, extra = {} }) {
  const fields = inputs.watershed || {};
  const need = stepOf(name) === 1 && required[name] ? t(texts.need, { what: purposeText(required[name].purpose) }) : null;
  return html`<${Row}
    name=${name}
    value=${fields[name]}
    error=${errors[name]}
    warning=${warnings[name]}
    need=${need}
    onInput=${(text) => setField(name, text)}
    aux=${SLOPE_FIELDS.has(name) ? percentHint(fields[name]) : null}
    origin=${inputs.origin}
    onRestore=${setField}
    ...${extra}
  />`;
}

/**
 * Step 1, Zlewnia: where the watershed came from, a WatershedParameters JSON read in the
 * browser, and its basic fields; a field the chosen model reads says so.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function WatershedStep(props) {
  const { inputs, onFile, infoValues } = props;
  const fileInput = useRef(null);
  const fields = inputs.watershed || {};
  const origin = inputs.origin;
  const area = numberOf(fields.area_km2);
  const source = origin ? origin.label : texts.watershed.noSource;
  let meta = t(texts.watershed.metaNoArea, { source });
  const blank = !origin && !Object.values(fields).some((text) => !isEmpty(text));
  if (area !== null) meta = t(texts.watershed.meta, { area: num(area, 2), source });
  else if (blank) meta = texts.empty;
  const onPick = (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (file) onFile(file);
  };
  const row = (name) => {
    const extra = name === "cn" ? { info: html`<${InfoButton} id="losses-scs-cn" values=${infoValues} />` } : {};
    return html`<${WatershedRow} key=${name} name=${name} ...${props} extra=${extra} />`;
  };
  return html`
    <${Step} id="watershed" number=${1} title=${texts.steps.watershed} meta=${meta}>
      ${blank ? html`<${EmptyHint} anchor="przyklad" name="hydrogram" />` : null}
      <div class="handoff" data-origin=${origin ? origin.label : ""}>
        ${origin && origin.mark
          ? html`<img src=${`nogat/marks/${origin.mark}.svg`} alt="" />`
          : html`<svg class="file-ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>`}
        <div>
          <strong>${origin ? origin.title : texts.watershed.noSource}</strong>
          ${origin && origin.detail ? html`<span class="muted">${origin.detail}</span>` : null}
        </div>
      </div>
      <div class="btn-row">
        <${HandoffImport} />
        <button class="btn sm ghost" type="button" title=${texts.watershed.fileHint} onClick=${() => fileInput.current.click()}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>
          ${texts.watershed.file}
        </button>
        <input ref=${fileInput} type="file" accept=".json,application/json" hidden onChange=${onPick} />
      </div>
      <p class="note">${texts.watershed.note}</p>
      <div class="form">
        <${WatershedRow} name="name" ...${props} extra=${{ text: true }} />
        ${WATERSHED_STEP.map(row)}
      </div>
    <//>
  `;
}

/**
 * A select in a form row (PMAXTP's probability, duration and method), empty until chosen.
 *
 * @param {{name: string, value: string, options: readonly string[], label: (value: string)
 *   => string, error?: string, keyText?: string, onChange: (value: string) => void}} props
 *   the field, its value, the values offered and their words, the message of a check, the
 *   key shown and the handler
 * @returns {object} the row
 */
function SelectRow({ name, value, options, label, error, keyText, onChange }) {
  const id = `hg-${name}`;
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
 * Step 2, Hietogram: PMAXTP (the point, p, the duration and the method, with the depth
 * fetched from IMGW-PIB shown read-only), a design hyetograph, or a series of depths; the
 * shape of the hyetograph and the time step.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function RainStep({ inputs, errors, warnings, set, valuesField, infoValues, required, pmaxtp }) {
  const source = inputs.rain_source;
  const shape = inputs.hietogram_type;
  const series = source === "series";
  const atlas = source === "pmaxtp";
  let meta;
  if (series) {
    const steps = seriesTokens(inputs.values).length;
    meta = steps ? t(texts.rain.metaSeries, { steps: plural(steps, texts.rain.stepForms) }) : texts.empty;
  } else {
    const total = atlas ? pmaxtp.depth : numberOf(inputs.total_mm);
    const duration = atlas ? inputs.pmaxtp_duration_min : inputs.duration_min;
    const probability = numberOf(inputs.pmaxtp_probability_pct);
    const words = {
      total: total === null ? "–" : num(total, 1),
      duration: durationText(duration),
      p: probability === null ? "–" : inputText(probability),
    };
    const point = !isEmpty(inputs.pmaxtp_latitude) || !isEmpty(inputs.pmaxtp_longitude);
    const blank = total === null && numberOf(duration) === null && (!atlas || (probability === null && !point));
    meta = blank ? texts.empty : t(atlas ? texts.rain.metaPmaxtp : texts.rain.metaDesign, words);
  }
  const numberRow = (name, extra = {}) => html`<${Row}
    name=${name}
    value=${inputs[name]}
    error=${errors[name]}
    warning=${warnings[name]}
    onInput=${(text) => set({ [name]: text })}
    ...${extra}
  />`;
  const peakDefault = Object.hasOwn(PEAK_DEFAULTS, shape) ? inputText(PEAK_DEFAULTS[shape]) : "";
  return html`
    <${Step} id="rain" number=${2} title=${texts.steps.rain} meta=${meta}>
      <div class="field">
        <span class="label-row">
          <span class="label" id="hg-rain-source-label">${texts.rain.source}</span>
          <${InfoButton} id="rain-source" values=${infoValues} />
        </span>
        <${Seg}
          items=${["pmaxtp", "design", "series"].map((value) => ({ value, label: texts.rain.sources[value] }))}
          value=${source}
          onChange=${(value) => set({ rain_source: value })}
          labelledBy="hg-rain-source-label"
          full=${true}
        />
      </div>
      ${atlas
        ? html`
            <div class="form">
              ${numberRow("pmaxtp_latitude", { keyText: "latitude" })}
              ${numberRow("pmaxtp_longitude", { keyText: "longitude" })}
              <${SelectRow}
                name="pmaxtp_probability_pct"
                value=${inputs.pmaxtp_probability_pct}
                options=${PMAXTP_PROBABILITIES}
                label=${(value) => t(texts.rain.probabilityValue, { value: inputText(Number(value)) })}
                error=${errors.pmaxtp_probability_pct}
                keyText=${false}
                onChange=${(value) => set({ pmaxtp_probability_pct: value })}
              />
              <${SelectRow}
                name="pmaxtp_duration_min"
                value=${inputs.pmaxtp_duration_min}
                options=${PMAXTP_DURATIONS}
                label=${durationText}
                error=${errors.pmaxtp_duration_min}
                keyText=${isEmpty(inputs.pmaxtp_duration_min) ? "duration_min" : t(texts.keyValue, { key: "duration_min", value: inputs.pmaxtp_duration_min })}
                onChange=${(value) => set({ pmaxtp_duration_min: value })}
              />
              <${SelectRow}
                name="pmaxtp_method"
                value=${inputs.pmaxtp_method}
                options=${PMAXTP_METHODS}
                label=${(value) => texts.rain.methods[value] || value}
                error=${errors.pmaxtp_method}
                keyText="method"
                onChange=${(value) => set({ pmaxtp_method: value })}
              />
              <${Row}
                name="pmaxtp_depth"
                value=${pmaxtp.depth === null ? "" : inputText(pmaxtp.depth)}
                error=${errors.pmaxtp_depth}
                onInput=${() => {}}
                readOnly=${true}
                placeholder=${pmaxtp.busy ? texts.rain.depthFetching : texts.rain.depthPending}
                keyText="total_mm"
                aux=${pmaxtp.depth === null ? null : t(texts.rain.depthSource, { method: inputs.pmaxtp_method })}
              />
            </div>
            ${pmaxtp.onRetry
              ? html`<div class="btn-row">
                  <button class="btn sm ghost" type="button" data-retry="pmaxtp" title=${texts.rain.retryTitle} onClick=${pmaxtp.onRetry}>
                    ${texts.rain.retry}
                  </button>
                </div>`
              : null}
            <p class="note">${richText(texts.rain.pmaxtpNote)}</p>
            <p class="note" data-attribution="pmaxtp">${texts.rain.attribution}</p>
          `
        : null}
      ${source === "design"
        ? html`
            <div class="form">${numberRow("total_mm")}${numberRow("duration_min")}</div>
            <p class="note">${richText(texts.rain.designNote)}</p>
          `
        : null}
      ${series
        ? html`
            <p class="note">${richText(texts.rain.seriesNote)}</p>
            ${valuesField
              ? html`<${SeriesField}
                  field=${valuesField}
                  id="hg-values"
                  value=${inputs.values}
                  error=${errors.values}
                  required=${Boolean(required.values)}
                  onInput=${(text) => set({ values: text })}
                />`
              : null}
          `
        : html`
            <div class="field">
              <span class="label-row">
                <span class="label" id="hg-shape-label">${texts.rain.shape}<span class="key">hietogram_type</span></span>
                <${InfoButton} id=${`rain-${shape}`} values=${infoValues} />
              </span>
              <${Seg}
                items=${SHAPES.map((value) => ({ value, label: texts.rain.shapes[value] }))}
                value=${shape}
                onChange=${(value) => set({ hietogram_type: value })}
                labelledBy="hg-shape-label"
                full=${true}
              />
            </div>
            ${shape === "beta"
              ? html`<div class="form">${numberRow("alpha", { placeholder: "2" })}${numberRow("beta", { placeholder: "5" })}</div>
                  <p class="note">${texts.rain.betaNote}</p>`
              : null}
            ${Object.hasOwn(PEAK_DEFAULTS, shape)
              ? html`<div class="form">${numberRow("peak_position", {
                  placeholder: peakDefault,
                  keyText: t(texts.keyDefault, { key: "peak_position", value: peakDefault }),
                })}</div>`
              : null}
            ${shape === "block" ? html`<p class="note">${texts.rain.blockNote}</p>` : null}
          `}
      <div class="form">
        ${numberRow("timestep_min", {
          placeholder: "5",
          keyText: t(texts.keyDefault, { key: "timestep_min", value: "5" }),
          info: html`<${InfoButton} id="rain-timestep" values=${infoValues} />`,
        })}
      </div>
    <//>
  `;
}

/**
 * The summary of the checks under the choice of the model: the fields missing, those to
 * correct and those outside their typical range, each a link to its field; before a
 * choice, what choosing does.
 *
 * @param {{inputs: object, errors: Object<string, string>, warnings: Object<string,
 *   string>}} props the inputs and the messages by field
 * @returns {object} the summary
 */
function Summary({ inputs, errors, warnings }) {
  if (!inputs.uh_model) return html`<p class="note" data-summary="none">${texts.uh.choose}</p>`;
  const missing = [];
  const invalid = [];
  const outside = [];
  for (const name of panelFields(inputs)) {
    if (errors[name]) (splitReason(errors[name]).reason === "required" ? missing : invalid).push(name);
    else if (warnings[name]) outside.push(name);
  }
  const link = (name, index) => html`${index ? ", " : ""}<button
      class="link-btn"
      type="button"
      data-goto=${name}
      title=${t(texts.summary.goTo, { field: fieldLabel(name), step: stepOf(name) })}
      onClick=${() => focusField(name)}
    >${fieldLabel(name)}</button> <span class="step-ref">(${t(texts.summary.step, { step: stepOf(name) })})</span>`;
  const line = (kind, level, title, names) =>
    names.length
      ? html`<li class=${level} data-summary=${kind}>${ICONS[level]}<div><span class="lvl">${title}</span> ${names.map(link)}</div></li>`
      : null;
  return html`
    <ul class="notes check-summary" data-summary="">
      ${line("missing", "bad", texts.summary.missing, missing)}
      ${line("invalid", "bad", texts.summary.invalid, invalid)}
      ${missing.length || invalid.length ? null : html`<li class="ok" data-summary="ok">${ICONS.ok}<div>${texts.summary.ok}</div></li>`}
      ${line("warnings", "warn", texts.summary.warnings, outside)}
    </ul>
  `;
}

/**
 * The tc of SCS and Clark in step 3: the method (with the watershed fields of step 3 it
 * reads), or tc typed, and what the last result gave.
 *
 * @param {object} props see DataPanel
 * @returns {object} the block
 */
function TcBlock(props) {
  const { inputs, errors, warnings, set, result, infoValues } = props;
  const method = inputs.tc_method;
  const tc = result && typeof result.tc_min === "number" ? result.tc_min : null;
  return html`
    <div class="block" data-block="tc">
      <h4 class="group-title">${texts.blocks.tc}</h4>
      <div class="field">
        <span class="label-row">
          <label for="hg-tc_method">${texts.tc.method}<span class="key">tc_method</span></label>
          <${InfoButton} id=${`tc-${method}`} values=${infoValues} />
        </span>
        <select id="hg-tc_method" value=${method} disabled=${inputs.tc_manual} onChange=${(event) => set({ tc_method: event.currentTarget.value })}>
          ${TC_METHODS.map((value) => html`<option value=${value}>${texts.tc.methods[value]}</option>`)}
        </select>
        <span class="hint">${texts.tc.hints[method]}</span>
      </div>
      ${!inputs.tc_manual && TC_BLOCK[method] && TC_BLOCK[method].length
        ? html`<div class="form">${TC_BLOCK[method].map((name) => html`<${WatershedRow} key=${name} name=${name} ...${props} />`)}</div>`
        : null}
      <div class="result-chip" data-chip="tc">
        <span class="k">tc</span>
        <span class="v">${tc !== null ? `${num(tc, 1)} min` : "–"}</span>
        <span class="u">${tc !== null ? t(texts.tc.chipHours, { hours: num(tc / 60, 2) }) : ""}</span>
      </div>
      <label class="check">
        <input type="checkbox" id="hg-tc_manual" checked=${inputs.tc_manual} onChange=${(event) => set({ tc_manual: event.currentTarget.checked })} />
        <span>${texts.tc.manual} <code>tc_min</code></span>
      </label>
      ${inputs.tc_manual
        ? html`<div class="form"><${Row}
            name="tc_min"
            value=${inputs.tc_min}
            error=${errors.tc_min}
            warning=${warnings.tc_min}
            onInput=${(text) => set({ tc_min: text })}
          /></div>`
        : null}
      <p class="note">${texts.tc.note} <a href="#kalkulatory">${texts.tc.compare}</a></p>
    </div>
  `;
}

/**
 * The losses of SCS-CN in step 3, common to every model: AMC and λ, and what the last
 * result gave (CN after AMC, S, Ia).
 *
 * @param {object} props see DataPanel
 * @returns {object} the block
 */
function LossesBlock({ inputs, errors, warnings, set, result, amcField }) {
  const fields = inputs.watershed || {};
  const cn = numberOf(fields.cn);
  const meaning = (value) => {
    const choice = amcField ? amcField.choices.find((item) => item.value === value) : null;
    return choice ? choice.meaning : "";
  };
  const fresh = result && result.amc === inputs.amc && typeof result.cn_adjusted === "number" && result.cn === cn;
  const hint =
    fresh && result.cn_adjusted !== result.cn
      ? t(texts.losses.amcAdjusted, { meaning: meaning(inputs.amc).replace(/\.$/, ""), cn: inputText(result.cn), adjusted: inputText(result.cn_adjusted) })
      : meaning(inputs.amc);
  const chips = [];
  if (result && typeof result.cn_adjusted === "number") {
    chips.push(
      result.amc === "II" || result.cn_adjusted === result.cn
        ? t(texts.losses.chipCn, { cn: inputText(result.cn_adjusted) })
        : t(texts.losses.chipCnAdjusted, { adjusted: inputText(result.cn_adjusted), cn: inputText(result.cn), amc: result.amc }),
    );
  }
  if (result && typeof result.retention_mm === "number") chips.push(t(texts.losses.chipS, { value: num(result.retention_mm, 1) }));
  if (result && typeof result.initial_abstraction_mm === "number") {
    chips.push(t(texts.losses.chipIa, { value: num(result.initial_abstraction_mm, 1) }));
  }
  return html`
    <div class="block" data-block="losses">
      <h4 class="group-title">${texts.blocks.losses}</h4>
      <p class="note">${texts.losses.note}</p>
      <div class="field">
        <span class="label-row"><span class="label" id="hg-amc-label">${texts.losses.amc}<span class="key">amc</span></span></span>
        <${Seg}
          items=${AMC.map((value) => ({ value, label: value, title: meaning(value) }))}
          value=${inputs.amc}
          onChange=${(value) => set({ amc: value })}
          labelledBy="hg-amc-label"
          full=${true}
        />
        <span class="hint" data-hint="amc">${hint}</span>
      </div>
      <div class="form">
        <${Row}
          name="ia_coefficient"
          value=${inputs.ia_coefficient}
          error=${errors.ia_coefficient}
          warning=${warnings.ia_coefficient}
          onInput=${(text) => set({ ia_coefficient: text })}
          placeholder="0,2"
          keyText=${t(texts.keyDefault, { key: "ia_coefficient", value: "0,2" })}
        />
      </div>
      ${chips.length ? html`<div class="chips" data-chips="losses">${chips.map((text) => html`<span class="chip">${text}</span>`)}</div>` : null}
    </div>
  `;
}

/**
 * Step 3, Hydrogram: the unit hydrograph model (none chosen at first) with the summary of
 * the checks, the chosen model's block (tc for SCS and Clark; Clark's R or R/tc; Nash by
 * Lutz with Lc, Manning's n, forest and urban shares and, read-only, the n and K the shown
 * result estimated, or n and K typed; Snyder's Lc of the watershed, L, Lc, Ct and Cp), the
 * losses, and what the last result gave.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function HydrographStep(props) {
  const { inputs, errors, warnings, set, result, infoValues } = props;
  const model = inputs.uh_model;
  const fields = inputs.watershed || {};
  const byLutz = usesLutz(inputs);
  const numberRow = (name, extra = {}) => html`<${Row}
    name=${name}
    value=${inputs[name]}
    error=${errors[name]}
    warning=${warnings[name]}
    onInput=${(text) => set({ [name]: text })}
    ...${extra}
  />`;
  const watershedRow = (name) => html`<${WatershedRow} key=${name} name=${name} ...${props} />`;
  const fresh = result && result.uh_model === model ? result : null;
  const parameters = (fresh && fresh.uh_parameters) || {};
  const chips = [];
  if (fresh) {
    if (model === "scs" && typeof parameters.tc_min === "number") chips.push(t(texts.uh.chipTc, { value: num(parameters.tc_min, 1) }));
    if (model === "clark" && typeof parameters.r_min === "number") chips.push(t(texts.uh.chipR, { value: num(parameters.r_min, 1) }));
    if (model === "nash") {
      if (typeof parameters.n === "number") chips.push(t(texts.uh.chipN, { value: shortText(parameters.n) }));
      if (typeof parameters.k_min === "number") chips.push(t(texts.uh.chipK, { value: shortText(parameters.k_min) }));
    }
    if (model === "snyder") {
      if (typeof parameters.ct === "number") chips.push(t(texts.uh.chipCt, { value: inputText(parameters.ct) }));
      if (typeof parameters.cp === "number") chips.push(t(texts.uh.chipCp, { value: inputText(parameters.cp) }));
    }
    if (typeof fresh.uh_time_to_peak_min === "number") chips.push(t(texts.uh.chipTp, { value: num(fresh.uh_time_to_peak_min, 1) }));
    if (typeof fresh.uh_peak_discharge_m3s_per_mm === "number") {
      chips.push(t(texts.uh.chipQp, { value: num(fresh.uh_peak_discharge_m3s_per_mm, 2) }));
    }
  }
  // Lutz's n and K are those the shown result estimated (`nash_estimation`)
  const estimate = result && result.nash_estimation === "lutz" && result.uh_parameters ? result.uh_parameters : null;
  const toGiven = () => {
    const patch = { nash_source: "given" };
    if (isEmpty(inputs.nash_n) && estimate) patch.nash_n = shortText(estimate.n);
    if (isEmpty(inputs.nash_k_min) && estimate) patch.nash_k_min = shortText(estimate.k_min);
    set(patch);
  };
  let meta = texts.uh.metaNone;
  if (model) {
    const tc = result && result.uh_model === model && typeof result.tc_min === "number" ? result.tc_min : null;
    meta = texts.uh.models[model] || model;
    if (usesTc(model) && inputs.tc_manual) meta += ` · ${t(texts.tc.metaManual, { tc: isEmpty(inputs.tc_min) ? "–" : roundedText(inputs.tc_min, 1) })}`;
    else if (usesTc(model)) {
      const name = texts.tc.names[inputs.tc_method] || inputs.tc_method;
      meta += ` · ${tc === null ? name : t(texts.tc.metaMethod, { tc: num(tc, 1), method: name })}`;
    }
  }
  return html`
    <${Step} id="hydrograph" number=${3} title=${texts.steps.hydrograph} meta=${meta}>
      <div class="field">
        <span class="label-row">
          <span class="label" id="hg-uh-label">${texts.uh.model}<span class="key">uh_model</span></span>
          ${model ? html`<${InfoButton} id=${`uh-${model}`} values=${infoValues} />` : null}
        </span>
        <${Seg}
          items=${UH_MODELS.map((value) => ({ value, label: texts.uh.models[value] }))}
          value=${model}
          onChange=${(value) => set({ uh_model: value })}
          labelledBy="hg-uh-label"
          full=${true}
        />
      </div>
      <${Summary} inputs=${inputs} errors=${errors} warnings=${warnings} />
      ${usesTc(model) ? html`<${TcBlock} ...${props} />` : null}
      ${model === "scs" ? html`<p class="note">${texts.uh.scsNote}</p>` : null}
      ${model === "nash"
        ? html`
            <div class="field">
              <span class="label" id="hg-nash-source-label">${texts.uh.nashSource}</span>
              <${Seg}
                items=${["lutz", "given"].map((value) => ({ value, label: texts.uh.nashSources[value] }))}
                value=${byLutz ? "lutz" : "given"}
                onChange=${(value) => (value === "given" ? toGiven() : set({ nash_source: "lutz" }))}
                labelledBy="hg-nash-source-label"
                full=${true}
              />
            </div>
            <div class="form">
              ${byLutz
                ? html`${["Lc_km", "manning_n", "forest_pct", "urban_pct"].map(watershedRow)}
                    ${numberRow("nash_n", { value: estimate ? shortText(estimate.n) : "", readOnly: true, placeholder: texts.uh.lutzPending })}
                    ${numberRow("nash_k_min", { value: estimate ? shortText(estimate.k_min) : "", readOnly: true })}`
                : html`${numberRow("nash_n")}${numberRow("nash_k_min")}`}
            </div>
            <p class="note">${richText(
              byLutz ? texts.uh.lutzNote : typicalNote("uh-nash", ["nash.n", "nash.k_min"], texts.uh.givenNote, texts.uh.givenNotePlain),
            )}</p>
          `
        : null}
      ${model === "clark"
        ? html`
            <div class="field">
              <span class="label" id="hg-clark-label">${texts.uh.clarkKind}</span>
              <${Seg}
                items=${["ratio", "r"].map((value) => ({ value, label: texts.uh.clarkKinds[value] }))}
                value=${inputs.clark_kind === "r" ? "r" : "ratio"}
                onChange=${(value) => set({ clark_kind: value })}
                labelledBy="hg-clark-label"
                full=${true}
              />
            </div>
            <div class="form">${inputs.clark_kind === "r" ? numberRow("clark_r_min") : numberRow("clark_r_tc_ratio")}</div>
            <p class="note">${richText(typicalNote("uh-clark", ["clark.r_tc_ratio"], texts.uh.clarkNote, texts.uh.clarkNotePlain))}</p>
          `
        : null}
      ${model === "snyder"
        ? html`
            <div class="form">
              ${watershedRow("Lc_km")}
              ${numberRow("snyder_ct", { placeholder: "1,5", keyText: t(texts.keyDefault, { key: "snyder_ct", value: "1,5" }) })}
              ${numberRow("snyder_cp", { placeholder: "0,6", keyText: t(texts.keyDefault, { key: "snyder_cp", value: "0,6" }) })}
            </div>
            <p class="note">${richText(texts.uh.snyderNote)}</p>
          `
        : null}
      ${chips.length ? html`<div class="chips" data-chips="uh">${chips.map((text) => html`<span class="chip">${text}</span>`)}</div>` : null}
      <${LossesBlock} ...${props} />
    <//>
  `;
}

/**
 * The panel Dane: the error the server gave without a field, then the three steps.
 *
 * @param {{inputs: object, errors: Object<string, string>, warnings: Object<string,
 *   string>, required: Object<string, {purpose: string}>, formError: {title: string,
 *   text: string}|null, set: (patch: object) => void, setField: (name: string, text:
 *   string) => void, onFile: (file: File) => void, result: object|null, models:
 *   object|null, infoValues: object, pmaxtp: {depth: number|null, busy: boolean, onRetry:
 *   (() => void)|null}}} props the inputs, the errors and warnings by field, what the
 *   chosen model needs (requirements), the error above the steps, the handlers (a patch of
 *   the inputs, a field of the watershed, a watershed file), the shown result, the field
 *   models, the values the (i) explanations check, and PMAXTP's fetched depth (null until
 *   known), whether it is being fetched and how to fetch it again after a failure
 * @returns {object} the panel's body
 */
export function DataPanel(props) {
  const { formError, models } = props;
  const field = (name) => (models ? models.options.fields.find((item) => item.name === name) || null : null);
  return html`
    ${formError
      ? html`<div class="form-errors" role="alert" data-form-error="">
          <strong>${formError.title}</strong>
          <div>${formError.text}</div>
        </div>`
      : null}
    <div class="steps">
      <${WatershedStep} ...${props} />
      <${RainStep} ...${props} valuesField=${field("values")} />
      <${HydrographStep} ...${props} amcField=${field("amc")} />
    </div>
  `;
}
