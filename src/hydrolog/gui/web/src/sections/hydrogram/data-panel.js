// The panel Dane of „Hydrogram zlewni”: the five steps of the calculation, numbered as the
// chain of `hydrograph generate` (the mockup's steps): Zlewnia (also read from a
// WatershedParameters JSON in the browser), Czas koncentracji, Opad, Straty SCS-CN and
// Model UH. Every change goes to the section, which checks it and recomputes (plan D13);
// the steps show what the last result gave (tc, CN after AMC, S, Ia, the UH's parameters).

import { SeriesField } from "../../controls/series-field.js";
import { richText, splitReason } from "../../controls/field.js";
import { inputText, num, plural } from "../../format.js";
import { seriesTokens } from "../../forms/model.js";
import { html, useEffect, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { InfoButton } from "../../ui/info-button.js";
import { Seg } from "../../ui/seg.js";
import {
  AMC,
  PEAK_DEFAULTS,
  PMAXTP_DURATIONS,
  PMAXTP_PROBABILITIES,
  SHAPES,
  SLOPE_FIELDS,
  TC_METHODS,
  UH_MODELS,
  UNITS,
  WATERSHED_MAIN,
  WATERSHED_MORE,
  changedFrom,
  isEmpty,
  numberOf,
  originText,
  usesLutz,
  usesTc,
} from "./state.js";

/**
 * A duration for people: whole hours as hours, otherwise minutes.
 *
 * @param {number|string} minutes the duration [min]
 * @returns {string} e.g. "12 h", "90 min"
 */
export function durationText(minutes) {
  const value = numberOf(minutes);
  if (value === null) return "–";
  return value % 60 === 0 ? t(texts.rain.hours, { value: inputText(value / 60) }) : t(texts.rain.minutes, { value: inputText(value) });
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
 * @param {{name: string, id: string, keyText?: string}} props the field, its control's id
 *   and the key shown (default: the name)
 * @returns {object} the label
 */
function FieldName({ name, id, keyText }) {
  const words = texts.fields[name] || { label: name };
  return html`<label for=${id}>${words.label}${words.symbol ? html` <i class="sym">${words.symbol}</i>` : null}<span class="key">${keyText || name}</span></label>`;
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
 * The message of a check under a field.
 *
 * @param {{id: string, error?: string}} props the control's id and the message
 * @returns {object|null} the message
 */
function FieldError({ id, error }) {
  if (!error) return null;
  const message = splitReason(error);
  return html`<span class="err" id=${`${id}-err`} role="alert">${message.text}${message.reason
    ? html` <span class="reason">· ${message.reason}</span>`
    : null}</span>`;
}

/**
 * A dense form row (the mockup's `.frow`): label with the symbol and key, the value with its
 * unit, a hint, the change mark and the message of a check.
 *
 * @param {{name: string, value?: string, error?: string, onInput: (text: string) => void,
 *   placeholder?: string, keyText?: string, aux?: string|null, changed?: object|null,
 *   info?: object|null, readOnly?: boolean, text?: boolean}} props the field and its parts
 * @returns {object} the row
 */
function Row({ name, value, error, onInput, placeholder, keyText, aux, changed, info, readOnly, text }) {
  const id = `hg-${name}`;
  const classes = ["frow", text ? "wide" : "", changed ? "edited" : "", error ? "invalid" : ""].filter(Boolean).join(" ");
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
    aria-describedby=${error ? `${id}-err` : undefined}
    onInput=${(event) => onInput(event.currentTarget.value)}
  />`;
  return html`
    <div class=${classes} data-field=${name}>
      ${info
        ? html`<span class="label-row"><${FieldName} name=${name} id=${id} keyText=${keyText} />${info}</span>`
        : html`<${FieldName} name=${name} id=${id} keyText=${keyText} />`}
      ${text ? input : html`<span class="ibox">${input}<span class="unit">${UNITS[name] || "–"}</span></span>`}
      ${aux ? html`<span class="aux">${aux}</span>` : null}
      ${changed}
      <${FieldError} id=${id} error=${error} />
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
 * Step 1, Zlewnia: where the watershed came from, a WatershedParameters JSON read in the
 * browser, and its fields (the models' and methods' ones folded).
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function WatershedStep({ inputs, errors, setField, onFile }) {
  const fileInput = useRef(null);
  const more = useRef(null);
  const fields = inputs.watershed || {};
  const origin = inputs.origin;
  const moreProblem = WATERSHED_MORE.some((name) => errors[name]);
  useEffect(() => {
    if (moreProblem && more.current) more.current.open = true;
  }, [moreProblem]);
  const row = (name) => html`<${Row}
    key=${name}
    name=${name}
    value=${fields[name]}
    error=${errors[name]}
    onInput=${(text) => setField(name, text)}
    aux=${SLOPE_FIELDS.has(name) ? percentHint(fields[name]) : null}
    changed=${html`<${Changed} origin=${origin} name=${name} text=${fields[name]} onRestore=${setField} />`}
  />`;
  const area = numberOf(fields.area_km2);
  const source = origin ? origin.label : texts.watershed.noSource;
  const meta = area === null ? t(texts.watershed.metaNoArea, { source }) : t(texts.watershed.meta, { area: num(area, 2), source });
  const onPick = (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (file) onFile(file);
  };
  return html`
    <${Step} id="watershed" number=${1} title=${texts.steps.watershed} meta=${meta}>
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
        <button class="btn sm ghost" type="button" title=${texts.watershed.fileHint} onClick=${() => fileInput.current.click()}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>
          ${texts.watershed.file}
        </button>
        <input ref=${fileInput} type="file" accept=".json,application/json" hidden onChange=${onPick} />
      </div>
      <div class="form">
        <${Row}
          name="name"
          text=${true}
          value=${fields.name}
          error=${errors.name}
          onInput=${(text) => setField("name", text)}
          changed=${html`<${Changed} origin=${origin} name="name" text=${fields.name} onRestore=${setField} />`}
        />
        ${WATERSHED_MAIN.map(row)}
      </div>
      <details class="more" ref=${more}>
        <summary>${texts.watershed.more} <span class="meta">${WATERSHED_MORE.length}</span></summary>
        <p class="note">${texts.watershed.moreNote}</p>
        <div class="form">${WATERSHED_MORE.map(row)}</div>
      </details>
    <//>
  `;
}

/**
 * Step 2, Czas koncentracji: the method of tc, or tc typed, and what the last result gave.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function TcStep({ inputs, errors, set, result, infoValues }) {
  const method = inputs.tc_method;
  const used = usesTc(inputs.uh_model);
  const model = texts.uh.models[inputs.uh_model] || inputs.uh_model;
  const tc = result && typeof result.tc_min === "number" ? result.tc_min : null;
  let meta;
  if (!used) meta = t(texts.tc.metaUnused, { model });
  else if (inputs.tc_manual) meta = t(texts.tc.metaManual, { tc: isEmpty(inputs.tc_min) ? "–" : inputs.tc_min });
  else if (tc !== null) meta = t(texts.tc.metaMethod, { tc: num(tc, 1), method: texts.tc.names[method] });
  else meta = t(texts.tc.metaPending, { method: texts.tc.names[method] });
  return html`
    <${Step} id="tc" number=${2} title=${texts.steps.tc} meta=${meta}>
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
      <div class="result-chip" data-chip="tc">
        <span class="k">tc</span>
        <span class="v">${used && tc !== null ? `${num(tc, 1)} min` : used ? "–" : texts.tc.unused}</span>
        <span class="u">${used ? (tc !== null ? t(texts.tc.chipHours, { hours: num(tc / 60, 2) }) : "") : t(texts.tc.chipUnused, { model })}</span>
      </div>
      <label class="check">
        <input type="checkbox" id="hg-tc_manual" checked=${inputs.tc_manual} onChange=${(event) => set({ tc_manual: event.currentTarget.checked })} />
        <span>${texts.tc.manual} <code>tc_min</code></span>
      </label>
      ${inputs.tc_manual
        ? html`<div class="form"><${Row} name="tc_min" value=${inputs.tc_min} error=${errors.tc_min} onInput=${(text) => set({ tc_min: text })} /></div>`
        : null}
      <p class="note">${texts.tc.note} <a href="#kalkulatory">${texts.tc.compare}</a></p>
    <//>
  `;
}

/**
 * Step 3, Opad: PMAXTP (the depth typed for p and the duration), a design hyetograph, or a
 * series of depths; the shape of the hyetograph and the time step.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function RainStep({ inputs, errors, set, valuesField, infoValues }) {
  const source = inputs.rain_source;
  const shape = inputs.hietogram_type;
  const series = source === "series";
  let meta;
  if (series) {
    const steps = seriesTokens(inputs.values).length;
    meta = t(texts.rain.metaSeries, { steps: plural(steps, texts.rain.stepForms) });
  } else {
    const total = numberOf(inputs.total_mm);
    const words = {
      total: total === null ? "–" : num(total, 1),
      duration: durationText(source === "pmaxtp" ? inputs.pmaxtp_duration_min : inputs.duration_min),
      p: inputText(Number(inputs.pmaxtp_probability_pct)),
    };
    meta = t(source === "pmaxtp" ? texts.rain.metaPmaxtp : texts.rain.metaDesign, words);
  }
  const numberRow = (name, extra = {}) => html`<${Row}
    name=${name}
    value=${inputs[name]}
    error=${errors[name]}
    onInput=${(text) => set({ [name]: text })}
    ...${extra}
  />`;
  const peakDefault = Object.hasOwn(PEAK_DEFAULTS, shape) ? inputText(PEAK_DEFAULTS[shape]) : "";
  return html`
    <${Step} id="rain" number=${3} title=${texts.steps.rain} meta=${meta}>
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
      ${source === "pmaxtp"
        ? html`
            <div class="form">
              <div class="frow">
                <label for="hg-pmaxtp-p">${texts.rain.probability} <i class="sym">p</i></label>
                <select id="hg-pmaxtp-p" class="sel-sm" value=${inputs.pmaxtp_probability_pct} onChange=${(event) => set({ pmaxtp_probability_pct: event.currentTarget.value })}>
                  ${PMAXTP_PROBABILITIES.map((value) => html`<option value=${value}>${t(texts.rain.probabilityValue, { value: inputText(Number(value)) })}</option>`)}
                </select>
              </div>
              <div class="frow">
                <label for="hg-pmaxtp-duration">${texts.fields.duration_min.label}<span class="key">${t(texts.keyValue, { key: "duration_min", value: inputs.pmaxtp_duration_min })}</span></label>
                <select id="hg-pmaxtp-duration" class="sel-sm" value=${inputs.pmaxtp_duration_min} onChange=${(event) => set({ pmaxtp_duration_min: event.currentTarget.value })}>
                  ${PMAXTP_DURATIONS.map((value) => html`<option value=${value}>${durationText(value)}</option>`)}
                </select>
              </div>
              ${numberRow("total_mm")}
            </div>
            <p class="note">${richText(texts.rain.pmaxtpNote)}</p>
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
                  required=${true}
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
 * Step 4, Straty SCS-CN: CN of the watershed, AMC and λ, and what the last result gave.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function LossStep({ inputs, errors, set, setField, result, amcField, infoValues }) {
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
  const meta = cn === null ? t(texts.losses.metaNoCn, { amc: inputs.amc }) : t(texts.losses.meta, { cn: inputText(cn), amc: inputs.amc });
  return html`
    <${Step} id="losses" number=${4} title=${texts.steps.losses} meta=${meta}>
      <div class="form">
        <${Row}
          name="cn"
          value=${fields.cn}
          error=${errors.cn}
          onInput=${(text) => setField("cn", text)}
          info=${html`<${InfoButton} id="losses-scs-cn" values=${infoValues} />`}
          changed=${html`<${Changed} origin=${inputs.origin} name="cn" text=${fields.cn} onRestore=${setField} />`}
        />
      </div>
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
          onInput=${(text) => set({ ia_coefficient: text })}
          placeholder="0,2"
          keyText=${t(texts.keyDefault, { key: "ia_coefficient", value: "0,2" })}
        />
      </div>
      ${chips.length ? html`<div class="chips" data-chips="losses">${chips.map((text) => html`<span class="chip">${text}</span>`)}</div>` : null}
    <//>
  `;
}

/**
 * Step 5, Model UH: the model and its parameters (Nash by Lutz through `uh nash`, or n and
 * K typed; Clark's R or R/tc; Snyder's L, Lc, Ct and Cp), and what the last result gave.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function UhStep({ inputs, errors, set, result, lutz, infoValues }) {
  const model = inputs.uh_model;
  const fields = inputs.watershed || {};
  const byLutz = usesLutz(inputs);
  const numberRow = (name, extra = {}) => html`<${Row}
    name=${name}
    value=${inputs[name]}
    error=${errors[name]}
    onInput=${(text) => set({ [name]: text })}
    ...${extra}
  />`;
  const fresh = result && result.uh_model === model ? result : null;
  const parameters = (fresh && fresh.uh_parameters) || {};
  const chips = [];
  if (fresh) {
    if (model === "scs" && typeof parameters.tc_min === "number") chips.push(t(texts.uh.chipTc, { value: num(parameters.tc_min, 1) }));
    if (model === "clark" && typeof parameters.r_min === "number") chips.push(t(texts.uh.chipR, { value: num(parameters.r_min, 1) }));
    if (model === "nash") {
      if (typeof parameters.n === "number") chips.push(t(texts.uh.chipN, { value: shortText(parameters.n) }));
      if (typeof parameters.k_min === "number") chips.push(t(texts.uh.chipK, { value: shortText(parameters.k_min) }));
      if (byLutz && lutz && typeof lutz.lag_time_min === "number") chips.push(t(texts.uh.chipLag, { value: num(lutz.lag_time_min, 1) }));
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
  const estimate = lutz && lutz.parameters ? lutz.parameters : null;
  const toGiven = () => {
    const patch = { nash_source: "given" };
    if (isEmpty(inputs.nash_n) && estimate) patch.nash_n = shortText(estimate.n);
    if (isEmpty(inputs.nash_k_min) && estimate) patch.nash_k_min = shortText(estimate.k_min);
    set(patch);
  };
  return html`
    <${Step} id="uh" number=${5} title=${texts.steps.uh} meta=${texts.uh.models[model] || model}>
      <div class="field">
        <span class="label-row">
          <span class="label" id="hg-uh-label">${texts.uh.model}<span class="key">uh_model</span></span>
          <${InfoButton} id=${`uh-${model}`} values=${infoValues} />
        </span>
        <${Seg}
          items=${UH_MODELS.map((value) => ({ value, label: texts.uh.models[value] }))}
          value=${model}
          onChange=${(value) => set({ uh_model: value })}
          labelledBy="hg-uh-label"
          full=${true}
        />
      </div>
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
                ? html`${numberRow("nash_n", { value: estimate ? shortText(estimate.n) : "", readOnly: true, placeholder: texts.uh.lutzPending })}
                    ${numberRow("nash_k_min", { value: estimate ? shortText(estimate.k_min) : "", readOnly: true })}`
                : html`${numberRow("nash_n")}${numberRow("nash_k_min")}`}
            </div>
            <p class="note">${richText(byLutz ? texts.uh.lutzNote : texts.uh.givenNote)}</p>
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
            <p class="note">${richText(texts.uh.clarkNote)}</p>
          `
        : null}
      ${model === "snyder"
        ? html`
            <div class="form">
              ${numberRow("snyder_length_km", { placeholder: isEmpty(fields.channel_length_km) ? "" : t(texts.fromWatershed, { value: fields.channel_length_km }) })}
              ${numberRow("snyder_centroid_length_km", { placeholder: isEmpty(fields.Lc_km) ? "" : t(texts.fromWatershed, { value: fields.Lc_km }) })}
              ${numberRow("snyder_ct", { placeholder: "1,5", keyText: t(texts.keyDefault, { key: "snyder_ct", value: "1,5" }) })}
              ${numberRow("snyder_cp", { placeholder: "0,6", keyText: t(texts.keyDefault, { key: "snyder_cp", value: "0,6" }) })}
            </div>
            <p class="note">${richText(texts.uh.snyderNote)}</p>
          `
        : null}
      ${chips.length ? html`<div class="chips" data-chips="uh">${chips.map((text) => html`<span class="chip">${text}</span>`)}</div>` : null}
    <//>
  `;
}

/**
 * The panel Dane: the error the server gave without a field, then the five steps.
 *
 * @param {{inputs: object, errors: Object<string, string>, formError: {title: string,
 *   text: string}|null, set: (patch: object) => void, setField: (name: string, text:
 *   string) => void, onFile: (file: File) => void, result: object|null, lutz: object|null,
 *   models: object|null, infoValues: object}} props the inputs, the messages by field, the
 *   error above the steps, the handlers (a patch of the inputs, a field of the watershed, a
 *   watershed file), the last result and Lutz's estimate, the field models and the values
 *   the (i) explanations check
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
      <${TcStep} ...${props} />
      <${RainStep} ...${props} valuesField=${field("values")} />
      <${LossStep} ...${props} amcField=${field("amc")} />
      <${UhStep} ...${props} />
    </div>
  `;
}
