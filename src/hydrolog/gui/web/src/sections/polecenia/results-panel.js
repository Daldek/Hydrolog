// The results of „Wszystkie polecenia”: in the centre the tables (or the JSON) of the last
// run, in the panel Wyniki its tiles, chart, call, notices and exports; both end with the
// providers' lines of the run's envelope (attribution.js, Nogat DEV-20.5), none without.

import { Attribution, linesOf } from "../../attribution.js";
import { html } from "../../html.js";
import { polecenia as texts } from "../../labels/polecenia.js";
import { results as resultTexts } from "../../labels/results.js";
import {
  Notices,
  PlanTargets,
  ResultJson,
  ResultRecords,
  ResultSeries,
  ResultSummary,
} from "../../forms/result-view.js";
import { CommandLine, ExportButtons, FileList } from "../../ui/export-panel.js";
import { exportSpec } from "./export.js";

/** Tiles of the commands the mockup shows (the generic choice elsewhere). */
const TILES = {
  "uh nash": ["parameters.n", "parameters.k_min", "lag_time_min", "peak_discharge_m3s_per_mm"],
  "scs effective": ["cn_adjusted", "retention_mm", "initial_abstraction_mm", "total_effective_mm"],
};

/**
 * The centre: the tables of the last run, or its JSON.
 *
 * @param {{run: object|null, tab: "table"|"json"}} props the last run and the tab shown
 * @returns {object} the centre's body
 */
export function CenterBody({ run, tab }) {
  if (!run) return html`<p class="empty-note">${texts.noResult}</p>`;
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
 * The panel Wyniki: tiles and parameters, the chart, the call, the notices and the exports.
 *
 * @param {{run: object|null, chartSvg: object}} props the last run and the ref of its
 *   chart's SVG (for PNG)
 * @returns {object} the panel's body
 */
export function ResultsPanel({ run, chartSvg }) {
  if (!run) return html`<p class="muted">${texts.noResult}</p>`;
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
    <${ResultSummary} analysis=${analysis} inputs=${envelope.inputs} keys=${TILES[command] || null} />
    ${first ? html`<${ResultSeries} group=${first} table=${false} svgRef=${chartSvg} size="small" bare=${true} />` : null}
    <${CommandLine} command=${command} options=${options} />
    <h3 class="group-title">${resultTexts.notices}</h3>
    <${Notices} notices=${analysis.notices} />
    <${ExportButtons} spec=${spec} />
    <${FileList} files=${analysis.files} />
    <${Attribution} lines=${linesOf(envelope)} />
  `;
}
