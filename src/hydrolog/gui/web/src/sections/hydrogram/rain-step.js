// Step 2 of a subcatchment, Hietogram, of „Hydrogram zlewni” (the author's three steps of
// 2026-11-04), and the same step bound to a network in Sieć (plan
// 2026-11-10-network-wizard, D4): the source of the rainfall among the host's `kinds`, then
// its fields. PMAXTP gives the point, p, the duration and the method, with the depth that
// `precip pmaxtp` fetched shown read-only (usePmaxtp; never typed); a design hyetograph its
// depth and duration; both the shape of the hyetograph. A series gives its depths in steps
// of the time step. Sieć adds „Brak” (its network without a rainfall, which a network of
// given hydrographs needs) and, for a subcatchment, „Jak w sieci” (the network's rainfall in
// words, with a link to it). The time step is the step's own (Hydrogram zlewni), the
// network's shown read-only (a subcatchment in Sieć), or the host's field before the step
// (Sieć's network). Hydrogram zlewni shows it as its numbered step 2; Sieć's network as a
// part of its step 1, „Opad sieci”.

import { richText } from "../../controls/field.js";
import { SeriesField } from "../../controls/series-field.js";
import { inputText, num, plural } from "../../format.js";
import { seriesTokens } from "../../forms/model.js";
import { html } from "../../html.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { rainInfo } from "../../labels/info/rain.js";
import { InfoButton } from "../../ui/info-button.js";
import { registerInfo } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { Row, SelectRow, Step, durationText } from "./rows.js";
import { PEAK_DEFAULTS, PMAXTP_DURATIONS, PMAXTP_METHODS, PMAXTP_PROBABILITIES, SHAPES, isEmpty, numberOf } from "./state.js";

registerInfo(rainInfo);

/**
 * The rainfall in words, as the step's summary shows it: „105 mm · 12 h · p 1%” for PMAXTP,
 * „30 mm · 1 h” for a design hyetograph, „własna seria · 7 kroków”, „brak opadu”, „jak w
 * sieci”, or „brak danych” before anything is given.
 *
 * @param {object} inputs the inputs of the rainfall
 * @param {number|null} depth PMAXTP's depth [mm] (usePmaxtp), null while unknown
 * @returns {string} the words
 */
export function rainWords(inputs, depth) {
  const source = inputs.rain_source;
  if (source === "series") {
    const steps = seriesTokens(inputs.values).length;
    return steps ? t(texts.rain.metaSeries, { steps: plural(steps, texts.rain.stepForms) }) : texts.empty;
  }
  if (source === "network") return texts.rain.metaNetwork;
  if (source !== "pmaxtp" && source !== "design") return texts.rain.metaNone;
  const atlas = source === "pmaxtp";
  const total = atlas ? depth : numberOf(inputs.total_mm);
  const duration = atlas ? inputs.pmaxtp_duration_min : inputs.duration_min;
  const probability = numberOf(inputs.pmaxtp_probability_pct);
  const words = {
    total: total === null ? "–" : num(total, 1),
    duration: durationText(duration),
    p: probability === null ? "–" : inputText(probability),
  };
  const point = !isEmpty(inputs.pmaxtp_latitude) || !isEmpty(inputs.pmaxtp_longitude);
  const blank = total === null && numberOf(duration) === null && (!atlas || (probability === null && !point));
  return blank ? texts.empty : t(atlas ? texts.rain.metaPmaxtp : texts.rain.metaDesign, words);
}

/**
 * The fields of PMAXTP: the point, p, the duration and the method, the fetched depth
 * (read-only), „Pobierz ponownie” after a failure of the source, and the atlas's notes.
 *
 * @param {object} props see RainStep, and `row` the step's number row
 * @returns {object} the fields
 */
function PmaxtpFields({ prefix, inputs, errors, set, pmaxtp, row }) {
  return html`
    <div class="form">
      ${row("pmaxtp_latitude", { keyText: "latitude" })}
      ${row("pmaxtp_longitude", { keyText: "longitude" })}
      <${SelectRow}
        prefix=${prefix}
        name="pmaxtp_probability_pct"
        value=${inputs.pmaxtp_probability_pct}
        options=${PMAXTP_PROBABILITIES}
        label=${(value) => t(texts.rain.probabilityValue, { value: inputText(Number(value)) })}
        error=${errors.pmaxtp_probability_pct}
        keyText=${false}
        onChange=${(value) => set({ pmaxtp_probability_pct: value })}
      />
      <${SelectRow}
        prefix=${prefix}
        name="pmaxtp_duration_min"
        value=${inputs.pmaxtp_duration_min}
        options=${PMAXTP_DURATIONS}
        label=${durationText}
        error=${errors.pmaxtp_duration_min}
        keyText=${isEmpty(inputs.pmaxtp_duration_min) ? "duration_min" : t(texts.keyValue, { key: "duration_min", value: inputs.pmaxtp_duration_min })}
        onChange=${(value) => set({ pmaxtp_duration_min: value })}
      />
      <${SelectRow}
        prefix=${prefix}
        name="pmaxtp_method"
        value=${inputs.pmaxtp_method}
        options=${PMAXTP_METHODS}
        label=${(value) => texts.rain.methods[value] || value}
        error=${errors.pmaxtp_method}
        keyText="method"
        onChange=${(value) => set({ pmaxtp_method: value })}
      />
      <${Row}
        prefix=${prefix}
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
  `;
}

/**
 * The shape of a design storm (PMAXTP's or a design hyetograph's) and its parameters.
 *
 * @param {object} props see RainStep, and `row` the step's number row
 * @returns {object} the fields
 */
function ShapeFields({ prefix, inputs, set, infoValues, row }) {
  const shape = inputs.hietogram_type;
  const peakDefault = Object.hasOwn(PEAK_DEFAULTS, shape) ? inputText(PEAK_DEFAULTS[shape]) : "";
  return html`
    <div class="field">
      <span class="label-row">
        <span class="label" id=${`${prefix}-shape-label`}>${texts.rain.shape}<span class="key">hietogram_type</span></span>
        <${InfoButton} id=${`rain-${shape}`} values=${infoValues} />
      </span>
      <${Seg}
        items=${SHAPES.map((value) => ({ value, label: texts.rain.shapes[value] }))}
        value=${shape}
        onChange=${(value) => set({ hietogram_type: value })}
        labelledBy=${`${prefix}-shape-label`}
        full=${true}
      />
    </div>
    ${shape === "beta"
      ? html`<div class="form">${row("alpha", { placeholder: "2" })}${row("beta", { placeholder: "5" })}</div>
          <p class="note">${texts.rain.betaNote}</p>`
      : null}
    ${Object.hasOwn(PEAK_DEFAULTS, shape)
      ? html`<div class="form">${row("peak_position", {
          placeholder: peakDefault,
          keyText: t(texts.keyDefault, { key: "peak_position", value: peakDefault }),
        })}</div>`
      : null}
    ${shape === "block" ? html`<p class="note">${texts.rain.blockNote}</p>` : null}
  `;
}

/**
 * The rainfall: the source among `kinds`, then its fields, the shape of a design storm and
 * the time step; a numbered step („2 Hietogram”) when given `number`, otherwise a part of the
 * host's step titled `title` („Opad sieci”).
 *
 * @param {{prefix: string, kinds: string[], inputs: object, errors: Object<string,
 *   string>, warnings: Object<string, string>, required: Object<string, object>, set:
 *   (patch: object) => void, pmaxtp: {depth: number|null, busy: boolean, onRetry: (() =>
 *   void)|null}, timestep?: {own: true}|{network: string}|null, network?: {words: string,
 *   onOpen: () => void}, infoValues: object, valuesField: object|null, number?: number,
 *   title: string}} props the host's prefix of ids; the sources offered, of "none"
 *   („Brak”), "network" („Jak w sieci”), "pmaxtp", "design" and "series"; the inputs and
 *   their errors and warnings by field; what the rainfall needs; the handler of a patch of
 *   the inputs; PMAXTP's fetched depth (null until known), whether it is being fetched and
 *   how to fetch it again after a failure; the time step: the step's own field, the
 *   network's shown, or none; with "network", the network's rainfall in words and how to
 *   open it; the values the (i) explanations check; the field model of the series; and the
 *   frame
 * @returns {object} the step
 */
export function RainStep(props) {
  const { prefix, kinds, inputs, errors, warnings, required, set, pmaxtp, timestep, network, infoValues, valuesField, number, title } = props;
  const source = inputs.rain_source;
  const row = (name, extra = {}) => html`<${Row}
    prefix=${prefix}
    name=${name}
    value=${inputs[name]}
    error=${errors[name]}
    warning=${warnings[name]}
    onInput=${(text) => set({ [name]: text })}
    ...${extra}
  />`;
  let step = null;
  if (timestep && timestep.own) {
    step = row("timestep_min", {
      placeholder: "5",
      keyText: t(texts.keyDefault, { key: "timestep_min", value: "5" }),
      info: html`<${InfoButton} id="rain-timestep" values=${infoValues} />`,
    });
  } else if (timestep && typeof timestep.network === "string") {
    step = row("timestep_min", {
      value: timestep.network,
      onInput: () => {},
      readOnly: true,
      placeholder: "5",
      keyText: t(texts.rain.timestepNetwork, { key: "timestep_min" }),
      info: html`<${InfoButton} id="rain-timestep" values=${infoValues} />`,
    });
  }
  const body = html`
    <div class="field">
      <span class="label-row">
        <span class="label" id=${`${prefix}-rain-source-label`}>${texts.rain.source}</span>
        <${InfoButton} id="rain-source" values=${infoValues} />
      </span>
      <${Seg}
        items=${kinds.map((value) => ({ value, label: texts.rain.sources[value] }))}
        value=${source}
        onChange=${(value) => set({ rain_source: value })}
        labelledBy=${`${prefix}-rain-source-label`}
        full=${true}
      />
    </div>
    ${source === "none" ? html`<p class="note" data-rain="none">${texts.rain.noneNote}</p>` : null}
    ${source === "network" && network
      ? html`<p class="note" data-rain="network">
          ${network.words} <button class="link-btn" type="button" data-goto="network-rain" onClick=${network.onOpen}>${texts.rain.networkOpen}</button>
        </p>`
      : null}
    ${source === "pmaxtp" ? html`<${PmaxtpFields} ...${props} row=${row} />` : null}
    ${source === "design"
      ? html`
          <div class="form">${row("total_mm")}${row("duration_min")}</div>
          <p class="note">${richText(texts.rain.designNote)}</p>
        `
      : null}
    ${source === "series"
      ? html`
          <p class="note">${richText(texts.rain.seriesNote)}</p>
          ${valuesField
            ? html`<${SeriesField}
                field=${valuesField}
                id=${`${prefix}-values`}
                value=${inputs.values}
                error=${errors.values}
                required=${Boolean(required.values)}
                onInput=${(text) => set({ values: text })}
              />`
            : null}
        `
      : null}
    ${source === "pmaxtp" || source === "design" ? html`<${ShapeFields} ...${props} row=${row} />` : null}
    ${step ? html`<div class="form">${step}</div>` : null}
  `;
  const meta = rainWords(inputs, pmaxtp.depth);
  if (number) return html`<${Step} id="rain" number=${number} title=${title} meta=${meta}>${body}<//>`;
  return html`
    <div class="rain-part" id=${`${prefix}-rain`} role="group" aria-labelledby=${`${prefix}-rain-title`} data-rain-part=${prefix}>
      <h4 class="sub-title" id=${`${prefix}-rain-title`}>${title}<span class="meta">${meta}</span></h4>
      ${body}
    </div>
  `;
}
