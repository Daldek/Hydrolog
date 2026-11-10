// The panel Dane of „Hydrogram zlewni”: the three steps of the author's flow (2026-11-04).
// 1 Zlewnia: where the watershed came from (a WatershedParameters JSON read in the
// browser, or a hand-off with „Wczytaj z Hydrografa”) and its basic fields, CN included.
// 2 Hietogram (rain-step.js, shared with Sieć's network): PMAXTP (the point, p, the
// duration and the method; the depth `precip pmaxtp` fetched from IMGW-PIB is shown, never
// typed), a design hyetograph or a series, its shape and the time step.
// 3 Hydrogram: the unit hydrograph model, none chosen at first; only the chosen model's
// block (its tc with the tc method's own fields for SCS and Clark, Clark's R, Nash by
// Lutz with the watershed fields Lutz reads or n and K, Snyder with Lc), then the losses
// of SCS-CN common to every model. Once a model is chosen, the fields it needs are marked
// where they live („wymagane dla …”), an empty one is an error (red), a value outside its
// typical range a warning (amber), and step 3 sums them up with a link to each field.
// Every change goes to the section, which checks it and recomputes (plan D13); the steps
// show what the last result gave (tc, CN after AMC, S, Ia, the UH's parameters).

import { richText, splitReason } from "../../controls/field.js";
import { inputText, num, roundedText } from "../../format.js";
import { HandoffImport } from "../../handoff/handoff-panel.js";
import { html, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { EmptyHint } from "../../ui/empty-hint.js";
import { InfoButton } from "../../ui/info-button.js";
import { infoRanges, infoText, rangeKey, rangeMark, rangeText, symbolOf } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { RainStep } from "./rain-step.js";
import { Row, Step, percentHint, shortText } from "./rows.js";
import {
  AMC,
  SLOPE_FIELDS,
  TC_BLOCK,
  TC_METHODS,
  UH_MODELS,
  WATERSHED_STEP,
  fieldLabel,
  isEmpty,
  numberOf,
  panelFields,
  purposeText,
  stepOf,
  usesLutz,
  usesTc,
} from "./state.js";

/** The prefix of the ids of the panel's controls. */
const PREFIX = "hg";

/** The sources of the rainfall Hydrogram zlewni offers. */
const RAIN_KINDS = Object.freeze(["pmaxtp", "design", "series"]);

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
 * Bring a field of the panel into view and focus it, opening its step.
 *
 * @param {string} name the field
 */
function focusField(name) {
  const control = document.getElementById(`${PREFIX}-${name}`);
  if (!control) return;
  const step = control.closest("details");
  if (step && !step.open) step.open = true;
  control.scrollIntoView({ block: "center" });
  control.focus({ preventScroll: true });
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
    prefix=${PREFIX}
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
            prefix=${PREFIX}
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
          prefix=${PREFIX}
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
    prefix=${PREFIX}
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
      <${RainStep}
        ...${props}
        prefix=${PREFIX}
        number=${2}
        title=${texts.steps.rain}
        kinds=${RAIN_KINDS}
        timestep=${{ own: true }}
        valuesField=${field("values")}
      />
      <${HydrographStep} ...${props} amcField=${field("amc")} />
    </div>
  `;
}
