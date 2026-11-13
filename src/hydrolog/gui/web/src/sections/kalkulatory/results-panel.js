// The results of „Kalkulatory”. The tc comparison: in the centre the bars of the methods or
// the parameters each took, in the panel Wyniki the methods with their range words, the
// notices of Hydrolog, „Użyj w Hydrogramie zlewni”, the CSV and the shell loop of the six
// calls. A calculator's command: the generic result view of the catalog (tables, tiles, the
// chart, the call, the notices and the exports), the centre and the panel ending with the
// providers' lines of its envelope (attribution.js, Nogat DEV-20.5), none without them.

import { api } from "../../api.js";
import { Attribution, linesOf } from "../../attribution.js";
import { Chart } from "../../charts/chart.js";
import { richText } from "../../controls/field.js";
import { num } from "../../format.js";
import {
  Notices,
  PlanTargets,
  ResultJson,
  ResultRecords,
  ResultSeries,
  ResultSummary,
} from "../../forms/result-view.js";
import { html, useEffect, useMemo, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError } from "../../labels/errors.js";
import { exportLabels } from "../../labels/exports.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { results as resultTexts } from "../../labels/results.js";
import { CommandLine, copyText, downloadBlob, ExportButtons, FileList, LINE_DELAY_MS } from "../../ui/export-panel.js";
import { InfoButton } from "../../ui/info-button.js";
import { DataTable } from "../../ui/table.js";
import { toast } from "../../ui/toast.js";
import { tcSpec, tcTitle } from "./charts.js";
import { barRows, parameterWords, uniqueNotices } from "./compare.js";
import { compareCsv, exportSpec, loopLine } from "./export.js";
import { TC_COMMAND } from "./state.js";

/**
 * The centre of the comparison: the bars, or the parameters each method took.
 *
 * @param {{rows: object[]|null, tab: "chart"|"table", sub: string|null,
 *   chartSvg: object}} props the rows of the last run, the tab shown, the line naming the
 *   watershed and the ref of the chart's SVG
 * @returns {object} the centre's body
 */
export function CompareCenter({ rows, tab, sub, chartSvg }) {
  const title = rows ? tcTitle(barRows(rows).length) : "";
  const spec = useMemo(() => (rows ? tcSpec(rows, title) : null), [rows, title]);
  if (!rows) return html`<p class="empty-note">${texts.noResult}</p>`;
  if (tab === "table") {
    return html`
      <div class="card kc-parameters">
        <div class="card-head">
          <h3 class="card-title">${texts.table.title}</h3>
          <span class="card-sub">${richText(texts.table.sub)}</span>
        </div>
        <${DataTable}
          tall=${false}
          label=${texts.table.title}
          columns=${[
            { key: "name", label: texts.table.method },
            { key: "parameters", label: texts.table.parameters, className: "txt", format: (value) => parameterWords(value) || "–" },
            { key: "tc_min", label: texts.table.tcMin, unit: "min", format: (value) => num(value, 1) },
            { key: "tc_h", label: texts.table.tcH, unit: "h", format: (value) => num(value, 3) },
            {
              key: "notices",
              label: texts.table.codes,
              className: "txt",
              format: (notices, row) => (row.ok ? notices.map((notice) => notice.code).join(", ") || "—" : row.sub),
            },
          ]}
          rows=${rows}
        />
        <p class="note">${richText(texts.table.note)}</p>
      </div>
    `;
  }
  return html`
    <div class="card kc-chart">
      <div class="card-head">
        <h3 class="card-title" id="kc-chart-title">${title}</h3>
        ${sub ? html`<span class="card-sub">${sub}</span>` : null}
      </div>
      ${spec ? html`<${Chart} spec=${spec} svgRef=${chartSvg} />` : null}
    </div>
  `;
}

/**
 * The shell loop of the comparison's calls, formatted by the server, with a copy button.
 *
 * @param {{watershed: object, methods: string[]}} props the watershed sent and the methods
 * @returns {object} the block
 */
function LoopLine({ watershed, methods }) {
  const [line, setLine] = useState(null);
  const [problem, setProblem] = useState(null);
  const key = JSON.stringify([watershed, methods]);
  useEffect(() => {
    if (!methods.length) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api
        .format(TC_COMMAND, { watershed, method: methods[0] }, { signal: controller.signal })
        .then((text) => {
          setLine(loopLine(text, methods));
          setProblem(null);
        })
        .catch((error) => {
          if (error && error.name === "AbortError") return;
          setProblem(t(texts.results.failed, { message: error.doc ? describeError(error.doc).text : String(error) }));
        });
    }, LINE_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key]);
  const copy = () =>
    copyText(line).then(
      () => toast(common.copied),
      () => toast(common.copyFailed, "bad"),
    );
  return html`
    <div class="cli kc-loop">
      <div class="cli-head">
        <span class="label">${texts.results.cli}</span>
        <button class="btn sm ghost icon" type="button" aria-label=${texts.results.copy} title=${texts.results.copy} disabled=${!line} onClick=${copy}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" /><path d="M13 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" /></svg>
        </button>
      </div>
      <pre class="code" aria-live="polite">${line || problem || texts.results.cliPending}</pre>
    </div>
  `;
}

/**
 * The panel Wyniki of the comparison.
 *
 * @param {{run: object|null, rows: object[]|null, selected: string|null,
 *   onSelect: (method: string) => void, onUse: () => void, usable: boolean}} props the last
 *   run and its rows, the method chosen for Hydrogram zlewni, the handlers, and whether it
 *   differs from the one Hydrogram uses
 * @returns {object} the panel's body
 */
export function CompareResults({ run, rows, selected, onSelect, onUse, usable }) {
  if (!run || !rows) return html`<p class="muted">${texts.noResult}</p>`;
  const notices = uniqueNotices(rows);
  const overland = rows.some((row) => row.ok && (row.method === "faa" || row.method === "kerby"));
  const chosen = rows.find((row) => row.method === selected) || null;
  const saveCsv = () => {
    const name = "porownanie-tc.csv";
    downloadBlob(new Blob([compareCsv(rows)], { type: "text/csv;charset=utf-8" }), name);
    toast(t(exportLabels.saved, { name }));
  };
  return html`
    <${DataTable}
      tall=${false}
      label=${texts.results.sub}
      rowClass=${(row) => (row.method === selected ? "sel" : null)}
      columns=${[
        {
          key: "name",
          label: texts.results.method,
          format: (name, row) => html`<button
              class="link-btn kc-pick"
              type="button"
              aria-pressed=${row.method === selected ? "true" : "false"}
              title=${t(texts.results.pick, { method: name })}
              disabled=${!row.ok}
              onClick=${() => onSelect(row.method)}
            >${name}</button>${row.used ? html` <span class="chip" title=${texts.results.usedTitle}>${texts.results.used}</span>` : null}<span class="row-sub">${row.method}</span>`,
        },
        { key: "tc_min", label: texts.results.tc, unit: "min", format: (value) => (value === null ? "—" : num(value, 1)) },
        {
          key: "word",
          label: texts.results.range,
          className: "txt",
          format: (word, row) => html`<span class=${`badge ${row.cls.split(" ")[0]}`}>${word}</span> <${InfoButton} id=${`tc-${row.method}`} values=${run.watershed} /><span class="row-sub kc-range">${richText(row.sub)}</span>`,
        },
        { key: "notices", label: html`<span title=${texts.results.noticesTitle}>${texts.results.notices}</span>`, format: (notices) => String(notices.length) },
      ]}
      rows=${rows}
    />
    <h3 class="group-title">${texts.results.hydrolog}</h3>
    <${Notices} notices=${notices} empty=${!overland} />
    ${overland
      ? html`<ul class="notes kc-overland">
          <li class="info">
            <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>
            <div><span class="lvl">${common.levels.info}</span> ${texts.results.overlandNote}<span class="from">${texts.results.overlandFrom}</span></div>
          </li>
        </ul>`
      : null}
    ${chosen ? html`<p class="note">${t(texts.results.chosen, { method: chosen.name })}</p>` : null}
    <div class="btn-row">
      <button
        class="btn primary"
        type="button"
        disabled=${!usable}
        title=${chosen ? t(texts.results.useTitle, { method: chosen.name }) : undefined}
        onClick=${onUse}
      >${texts.results.use}</button>
      <button class="btn" type="button" title=${texts.results.csvTitle} onClick=${saveCsv}><span class="fmt">CSV</span>${texts.results.csv}</button>
    </div>
    <${LoopLine} watershed=${run.watershed} methods=${run.methods} />
  `;
}

/**
 * The centre of a calculator: the tables of its result, or its JSON.
 *
 * @param {{run: object|null, tab: "result"|"json"}} props the last run and the tab shown
 * @returns {object} the centre's body
 */
export function CommandCenter({ run, tab }) {
  if (!run) return html`<p class="empty-note">${texts.noResultCommand}</p>`;
  const footer = html`<${Attribution} lines=${linesOf(run.envelope)} />`;
  if (tab === "json") return html`<${ResultJson} envelope=${run.envelope} />${footer}`;
  const { analysis } = run;
  const tables = analysis.series.length + analysis.records.length + (analysis.targets ? 1 : 0);
  return html`
    ${analysis.targets ? html`<${PlanTargets} targets=${analysis.targets} />` : null}
    ${analysis.series.map((group) => html`<${ResultSeries} key=${group.length} group=${group} chart=${false} />`)}
    <${ResultRecords} records=${analysis.records} />
    ${tables
      ? null
      : html`<div class="card">
          <div class="card-head"><h3 class="card-title">${resultTexts.parameters}</h3></div>
          <${ResultSummary} analysis=${analysis} inputs=${run.envelope.inputs} showTiles=${false} />
        </div>`}
    ${footer}
  `;
}

/**
 * The panel Wyniki of a calculator: tiles and parameters, the chart, the call, the notices
 * and the exports.
 *
 * @param {{run: object|null, chartSvg: object}} props the last run and the ref of its chart
 * @returns {object} the panel's body
 */
export function CommandResults({ run, chartSvg }) {
  if (!run) return html`<p class="muted">${texts.noResultCommand}</p>`;
  const { analysis, envelope, command, options } = run;
  if (envelope.status === "cancelled") {
    return html`
      <h3 class="group-title">${resultTexts.notices}</h3>
      <${Notices} notices=${analysis.notices} />
    `;
  }
  const spec = exportSpec({ command, options, envelope, analysis, chartSvg });
  const first = analysis.series[0];
  return html`
    <${ResultSummary} analysis=${analysis} inputs=${envelope.inputs} keys=${texts.tiles[command] || null} />
    ${first ? html`<${ResultSeries} group=${first} table=${false} svgRef=${chartSvg} size="small" bare=${true} />` : null}
    <${CommandLine} command=${command} options=${options} />
    <h3 class="group-title">${resultTexts.notices}</h3>
    <${Notices} notices=${analysis.notices} />
    <${ExportButtons} spec=${spec} />
    <${FileList} files=${analysis.files} />
    <${Attribution} lines=${linesOf(envelope)} />
  `;
}
