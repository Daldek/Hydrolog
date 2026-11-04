// The results of „Hydrogram zlewni”. In the centre: the hyetograph above the hydrograph, the
// cumulative rainfall and the unit hydrograph, or the table of the series. In the panel
// Wyniki: the peak, the time to peak, the volume and the runoff coefficient; the notes (the
// GUI's confirmations of Hydrolog's typical ranges, then Hydrolog's notices in Polish, those
// of Lutz's `uh nash` included); the balance of the rainfall; the parameters of the
// calculation; the exports (with the Markdown report and the print view) and the command
// line; „Przekazanie”, the hand-off nogat-handoff/1 of the shown run and a received
// producer's result beside it (handoff/handoff-panel.js). `run` holds the shown result
// ({inputs, options, envelope, lutz, lutzNotices, values}: its inputs and options, its
// envelope, Lutz's estimate and the notices of its run, and the values its notes checked),
// `spec` its export spec (export.js) and `current` the section's inputs now (with the record
// of a received hand-off, `handoff`).

import { Chart } from "../../charts/chart.js";
import { richText } from "../../controls/field.js";
import { hmm, inputText, num, roundedText } from "../../format.js";
import { Notices } from "../../forms/result-view.js";
import { html, useMemo } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { handoffLabels } from "../../labels/handoff.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { HydrogramHandoff } from "../../handoff/handoff-panel.js";
import { CommandLine, ExportButtons } from "../../ui/export-panel.js";
import { DataTable } from "../../ui/table.js";
import { cumulativeSpec, mainSpec, uhSpec } from "./charts.js";
import { durationText, shortText } from "./data-panel.js";
import { guiNotes } from "./notes.js";
import { COMMAND, PEAK_DEFAULTS, isEmpty, rainDuration, runNotices, usesLutz, usesTc } from "./state.js";

/** Icons of the notes by level (the mockup's). */
const ICONS = {
  warn: html`<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2l6.5 11.5h-13z" /><path d="M8 6.5v3.2M8 11.7v.01" /></svg>`,
  ok: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M5 8.2l2 2 4-4.2" /></svg>`,
  info: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>`,
};

/** The words of the notes' levels. */
const LEVELS = { warn: common.levels.warning, ok: common.levels.ok, info: common.levels.info };

/**
 * The name of a run's model and tc: "SCS · Kirpich", "Nash", "Clark · tc 120 min"; a tc
 * given to more decimals (handed over exactly) shows to 0,1 min.
 *
 * @param {object} inputs the inputs of the run
 * @returns {string} the name
 */
export function modelLabel(inputs) {
  let tc = "";
  if (usesTc(inputs.uh_model)) {
    tc = inputs.tc_manual
      ? t(texts.center.subTcManual, { tc: roundedText(inputs.tc_min, 1) })
      : t(texts.center.subTc, { method: texts.tc.names[inputs.tc_method] || inputs.tc_method });
  }
  return `${texts.uh.models[inputs.uh_model] || inputs.uh_model}${tc}`;
}

/**
 * The rainfall of a run in words: "PMAXTP p 1%, 12 h, Beta (2; 5)"; values given to more
 * decimals (handed over exactly) show to 0,01.
 *
 * @param {object} inputs the inputs of the run
 * @param {object} result its result
 * @returns {string} the words
 */
export function rainLabel(inputs, result) {
  if (inputs.rain_source === "series") {
    const steps = (result.precipitation_mm || []).length;
    return t(texts.center.rainSeries, { steps: `${steps} × ${inputText(result.timestep_min)} min` });
  }
  const type = inputs.hietogram_type;
  let shape = texts.rain.shapes[type] || type;
  if (type === "beta") {
    shape = t(texts.center.shapeBeta, {
      alpha: isEmpty(inputs.alpha) ? "2" : roundedText(inputs.alpha, 2),
      beta: isEmpty(inputs.beta) ? "5" : roundedText(inputs.beta, 2),
    });
  } else if (Object.hasOwn(PEAK_DEFAULTS, type)) {
    shape = t(texts.center.shapePeak, {
      shape,
      position: isEmpty(inputs.peak_position) ? inputText(PEAK_DEFAULTS[type]) : roundedText(inputs.peak_position, 2),
    });
  }
  const duration = durationText(rainDuration(inputs));
  if (inputs.rain_source === "pmaxtp") {
    return t(texts.center.rainPmaxtp, { p: inputText(Number(inputs.pmaxtp_probability_pct)), duration, shape });
  }
  return t(texts.center.rainDesign, { total: roundedText(inputs.total_mm, 2), duration, shape });
}

/**
 * The note that the results belong to the previous data.
 *
 * @param {{stale: {kind: "invalid"|"error", field?: string}|null}} props why they do
 * @returns {object|null} the note
 */
function StaleNote({ stale }) {
  if (!stale) return null;
  const text =
    stale.kind === "invalid" ? t(texts.stale.invalid, { field: stale.field }) : t(texts.stale.error, { message: stale.text || "" }).trim();
  return html`<ul class="notes stale-note" data-stale=${stale.kind}><li class="warn">${ICONS.warn}<div>${text}</div></li></ul>`;
}

/**
 * The value of a series in the step that ends at ordinate `index`, null outside it.
 *
 * @param {number[]|undefined} series the values per step
 * @param {number} index the ordinate
 * @returns {number|null} the value
 */
function endingAt(series, index) {
  const step = index - 1;
  return Array.isArray(series) && step >= 0 && step < series.length ? series[step] : null;
}

/**
 * The centre: the charts or the table of the shown result.
 *
 * @param {{run: object|null, tab: "chart"|"table", reference: object|null, chartSvg:
 *   {current: SVGSVGElement|null}, onClearReference: () => void, stale: object|null}} props
 *   the shown run, the tab, the reference discharge of Statystyka, the ref of the main chart,
 *   the handler that removes the reference, and why the result is stale
 * @returns {object} the centre's body
 */
export function CenterBody({ run, tab, reference, chartSvg, onClearReference, stale }) {
  const result = run ? run.envelope.result : null;
  const main = useMemo(() => (result ? mainSpec(result, reference) : null), [result, reference]);
  const cumulativeChart = useMemo(() => (result ? cumulativeSpec(result) : null), [result]);
  const unitChart = useMemo(() => (result ? uhSpec(result) : null), [result]);
  const rows = useMemo(() => {
    if (!result) return [];
    const times = result.times_min || [];
    return times.map((time, index) => ({
      clock: hmm(time),
      time,
      p: endingAt(result.precipitation_mm, index),
      pe: endingAt(result.effective_precipitation_mm, index),
      q: result.discharge_m3s[index],
    }));
  }, [result]);
  if (!run) return html`<p class="empty-note">${texts.center.noResult}</p>`;
  const { inputs } = run;
  const sub = t(texts.center.sub, {
    model: modelLabel(inputs),
    amc: result.amc,
    rain: rainLabel(inputs, result),
    dt: inputText(result.timestep_min),
  });
  const times = result.times_min || [];
  const end = times.length ? hmm(times[times.length - 1]) : "–";
  const optional = (value) => (value === null ? "–" : num(value, 2));
  const columns = [
    { key: "clock", label: texts.table.clock, unit: texts.table.clockUnit },
    { key: "time", label: texts.table.time, unit: texts.table.timeUnit, className: "t", format: (value) => inputText(value) },
    { key: "p", label: texts.table.p, unit: "mm", format: optional },
    { key: "pe", label: texts.table.pe, unit: "mm", format: optional },
    { key: "q", label: texts.table.q, unit: "m³/s", format: (value) => num(value, 2) },
  ];
  return html`
    <${StaleNote} stale=${stale} />
    <div class="tab-pane" data-tab-pane="chart" hidden=${tab !== "chart"}>
      <div class="card">
        <div class="card-head">
          <h3 class="card-title">${texts.center.mainTitle}</h3>
          <span class="card-sub" data-chart-sub="">${sub}</span>
          ${reference
            ? html`<button class="link-btn" type="button" title=${t(texts.center.referenceTitle, { label: reference.label })} onClick=${onClearReference}>
                ${texts.center.referenceRemove}
              </button>`
            : null}
        </div>
        <${Chart} spec=${main} svgRef=${chartSvg} class="wide" />
      </div>
      <div class="card">
        <div class="card-head">
          <h3 class="card-title">${texts.center.partsTitle}</h3>
          <span class="card-sub">${texts.center.partsSub}</span>
        </div>
        <div class="duo">
          <div class="chart-box" data-chart="cumulative">
            <div class="chart-title">${texts.center.cumTitle} <span>${t(texts.center.cumRange, { duration: hmm((result.precipitation_mm || []).length * result.timestep_min) })}</span></div>
            <${Chart} spec=${cumulativeChart} />
          </div>
          ${unitChart
            ? html`<div class="chart-box" data-chart="uh">
                <div class="chart-title">
                  ${t(texts.center.uhTitle, { model: texts.uh.models[result.uh_model] || result.uh_model })}
                  <span>${t(texts.center.uhSub, { dt: inputText(result.timestep_min), command: `uh ${result.uh_model}` })}</span>
                </div>
                <${Chart} spec=${unitChart} />
              </div>`
            : null}
        </div>
      </div>
    </div>
    <div class="tab-pane" data-tab-pane="table" hidden=${tab !== "table"}>
      <div class="card">
        <div class="card-head">
          <h3 class="card-title">${texts.center.tableTitle}</h3>
          <span class="card-sub">${t(texts.center.tableSub, { dt: inputText(result.timestep_min), end })}</span>
        </div>
        <${DataTable}
          columns=${columns}
          rows=${rows}
          label=${texts.center.tableLabel}
          rowClass=${(row) => (row.time === result.time_to_peak_min ? "peak" : null)}
        />
        <p class="note">${t(texts.center.tableNote, { time: hmm(result.time_to_peak_min) })}</p>
      </div>
    </div>
  `;
}

/**
 * The applicability notes of the GUI (notes.js), each with its explanation.
 *
 * @param {{notes: object[], values: object}} props the notes and the values the (i)
 *   explanations check
 * @returns {object|null} the list
 */
function GuiNotes({ notes, values }) {
  if (!notes.length) return null;
  const shownValues = JSON.stringify(values);
  return html`
    <ul class="notes" data-notes="gui">
      ${notes.map(
        (note) => html`<li class=${note.level} data-level=${note.level}>
          ${ICONS[note.level]}
          <div>
            <span class="lvl">${LEVELS[note.level]}</span> ${richText(note.text)}
            <span class="from">${richText(note.from)}${note.info
              ? html` · <button class="link-btn" type="button" data-info=${note.info} data-info-values=${shownValues} aria-haspopup="dialog" aria-expanded="false">${texts.notes.explain}</button>`
              : null}</span>
          </div>
        </li>`,
      )}
    </ul>
  `;
}

/**
 * The balance of the rainfall: P split into the initial abstraction, the infiltration and
 * the effective rainfall, with the retention S, and the volume against Pe·A.
 *
 * @param {{result: object}} props the result
 * @returns {object} the balance
 */
function Balance({ result }) {
  const total = result.total_precipitation_mm;
  const effective = result.total_effective_mm;
  const abstraction = Math.min(result.initial_abstraction_mm, total);
  const infiltration = Math.max(0, total - abstraction - effective);
  const share = (value) => (total > 0 ? (value / total) * 100 : 0);
  const pct = (value) => `${num(share(value), 1)} %`;
  const widths = [share(abstraction), share(infiltration), share(effective)];
  const pea = effective * result.area_km2 * 1000;
  const rows = [
    ["p", "P", total, "100 %", null],
    ["ia", "Ia", abstraction, pct(abstraction), "b-ia"],
    ["f", "F", infiltration, pct(infiltration), "b-f"],
    ["pe", "Pe", effective, pct(effective), "b-pe"],
    ["s", "S", result.retention_mm, "", null],
  ];
  return html`
    <svg class="stack" viewBox="0 0 100 1" preserveAspectRatio="none" role="img" aria-label=${t(texts.results.balanceLabel, {
      ia: pct(abstraction),
      f: pct(infiltration),
      pe: pct(effective),
    })}>
      <rect class="b-ia" x="0" y="0" width=${widths[0].toFixed(2)} height="1" />
      <rect class="b-f" x=${widths[0].toFixed(2)} y="0" width=${widths[1].toFixed(2)} height="1" />
      <rect class="b-pe" x=${(widths[0] + widths[1]).toFixed(2)} y="0" width=${widths[2].toFixed(2)} height="1" />
    </svg>
    <table class="params" data-table="balance">
      <tbody>
        ${rows.map(
          ([key, symbol, value, part, dot]) => html`<tr data-row=${key}>
            <th>${dot ? html`<i class=${`dot ${dot}`}></i>` : null}${texts.results.balanceRows[key]}<span class="sym">${symbol}</span></th>
            <td>${num(value, 2)}</td>
            <td class="u">mm</td>
            <td class="pct">${part}</td>
          </tr>`,
        )}
      </tbody>
    </table>
    ${pea > 0
      ? html`<p class="note" data-note="volume">${t(texts.results.balanceNote, {
          volume: num(result.total_volume_m3, 0),
          pea: num(pea, 0),
          diff: num((Math.abs(result.total_volume_m3 - pea) / pea) * 100, 2),
        })}</p>`
      : null}
  `;
}

/**
 * The parameters of the calculation: tc, CN after AMC, the UH's parameters, its time to
 * peak and peak, the length of the hydrograph and the time step.
 *
 * @param {{run: object}} props the shown run
 * @returns {object} the table
 */
function Parameters({ run }) {
  const { inputs, lutz } = run;
  const result = run.envelope.result;
  const parameters = result.uh_parameters || {};
  const rows = [];
  const rowTexts = texts.results.paramRows;
  if (!usesTc(result.uh_model)) rows.push(["tc", rowTexts.tc, "tc", rowTexts.tcUnused, ""]);
  else if (inputs.tc_manual) rows.push(["tc", rowTexts.tc, texts.results.paramSyms.tcManual, num(result.tc_min, 1), "min"]);
  else {
    const method = texts.tc.names[result.tc_method] || result.tc_method;
    rows.push(["tc", rowTexts.tc, t(texts.results.paramSyms.tcMethod, { method }), num(result.tc_min, 1), "min"]);
  }
  rows.push(["cn", rowTexts.cn, "cn_adjusted", inputText(result.cn_adjusted), "–"]);
  if (result.uh_model === "clark" && typeof parameters.r_min === "number") rows.push(["r", rowTexts.r, "R", num(parameters.r_min, 1), "min"]);
  if (result.uh_model === "nash") {
    const by = usesLutz(inputs) ? ` · ${texts.results.paramSyms.lutz}` : "";
    rows.push(["n", rowTexts.n, `n${by}`, shortText(parameters.n), "–"]);
    rows.push(["k", rowTexts.k, `K${by}`, shortText(parameters.k_min), "min"]);
    if (usesLutz(inputs) && lutz && typeof lutz.lag_time_min === "number") rows.push(["lag", rowTexts.lag, "t_lag = n·K", num(lutz.lag_time_min, 1), "min"]);
  }
  if (result.uh_model === "snyder") {
    rows.push(["snyderL", rowTexts.snyderL, "L", inputText(parameters.length_km), "km"]);
    rows.push(["snyderLc", rowTexts.snyderLc, "Lc", inputText(parameters.centroid_length_km), "km"]);
    rows.push(["ct", rowTexts.ct, "Ct", inputText(parameters.ct), "–"]);
    rows.push(["cp", rowTexts.cp, "Cp", inputText(parameters.cp), "–"]);
  }
  rows.push(
    ["tp", rowTexts.tp, "tp", num(result.uh_time_to_peak_min, 1), "min"],
    ["qp", rowTexts.qp, "qp", num(result.uh_peak_discharge_m3s_per_mm, 2), "m³/s/mm"],
    ["duration", rowTexts.duration, "", num(result.duration_min, 0), "min"],
    ["dt", rowTexts.dt, "Δt", inputText(result.timestep_min), "min"],
  );
  return html`
    <table class="params" data-table="parameters">
      <tbody>
        ${rows.map(
          ([key, label, symbol, value, unit]) => html`<tr data-row=${key}>
            <th>${label}${symbol ? html`<span class="sym">${symbol}</span>` : null}</th>
            <td>${value}</td>
            <td class="u">${unit}</td>
          </tr>`,
        )}
      </tbody>
    </table>
  `;
}

/**
 * A part of the panel Wyniki: a <details> with a title and a summary on the right.
 *
 * @param {{id: string, title: string, meta?: string, open?: boolean, children: any}} props
 *   the part
 * @returns {object} the part
 */
function Part({ id, title, meta, open = true, children }) {
  return html`
    <details class="step" open=${open} data-part=${id}>
      <summary>
        <span class="title">${title}</span><span class="meta">${meta || ""}</span>
        <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
      </summary>
      <div class="step-body">${children}</div>
    </details>
  `;
}

/**
 * The panel Wyniki.
 *
 * @param {{run: object|null, spec: object|null, stale: object|null, current?: object}}
 *   props the shown run, its export spec, why the result is stale, and the section's
 *   inputs now
 * @returns {object} the panel's body
 */
export function ResultsPanel({ run, spec, stale, current = null }) {
  if (!run) return html`<p class="muted">${texts.center.noResult}</p>`;
  const { envelope, inputs, values } = run;
  const result = envelope.result;
  const notices = runNotices(run);
  const notes = guiNotes({ inputs, values, result, notices });
  return html`
    <${StaleNote} stale=${stale} />
    <div class="summary" data-kpis="">
      <div class="kpi hi" data-kpi="q">
        <div class="k">${texts.results.kpi.q}</div>
        <div class="v"><span>${num(result.peak_discharge_m3s, 2)}</span> <span class="u">m³/s</span></div>
      </div>
      <div class="kpi" data-kpi="tp">
        <div class="k">${texts.results.kpi.tp}</div>
        <div class="v"><span>${hmm(result.time_to_peak_min)}</span> <span class="u">h</span></div>
      </div>
      <div class="kpi" data-kpi="volume">
        <div class="k">${texts.results.kpi.volume}</div>
        <div class="v"><span>${num(result.total_volume_m3, 0)}</span> <span class="u">m³</span></div>
      </div>
      <div class="kpi" data-kpi="c">
        <div class="k">${texts.results.kpi.c}</div>
        <div class="v">${num(result.runoff_coefficient, 3)}</div>
      </div>
    </div>
    <h3 class="group-title">${texts.results.notices}</h3>
    <${GuiNotes} notes=${notes} values=${values} />
    <${Notices} notices=${notices} />
    <div class="steps">
      <${Part} id="balance" title=${texts.results.balance} meta=${t(texts.results.balanceMeta, { c: num(result.runoff_coefficient, 3) })}>
        <${Balance} result=${result} />
      <//>
      <${Part} id="parameters" title=${texts.results.params} meta=${texts.results.paramsMeta} open=${false}>
        <${Parameters} run=${run} />
      <//>
      <${Part} id="exports" title=${texts.results.exports} meta=${texts.results.exportsMeta}>
        <${ExportButtons} spec=${spec} />
        <${CommandLine} command=${COMMAND} options=${run.options} title=${false} />
        ${usesLutz(inputs) ? html`<p class="note">${richText(texts.results.cliNote)}</p>` : null}
      <//>
      <${Part} id="handoff" title=${handoffLabels.export.title} meta=${handoffLabels.export.meta}>
        <${HydrogramHandoff} run=${run} current=${current} subject=${spec.subject} rain=${rainLabel(inputs, result)} />
      <//>
    </div>
  `;
}
