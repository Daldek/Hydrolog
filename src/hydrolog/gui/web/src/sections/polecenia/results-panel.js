// The results of „Wszystkie polecenia”: in the centre the tables (or the JSON) of the last
// run, in the panel Wyniki its tiles, chart, call, notices and exports, ending with the
// full providers' lines of the run's envelope, on paper only (attribution.js, Nogat
// DEV-20.5; on screen the view's strip, ui/sources.js), none without.

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

/**
 * Tiles of a command's result, the key figure last (highlighted); a command whose result
 * depends on its `index` lists them as "<command> <index>". Other commands get the
 * generic choice.
 */
const TILES = {
  "uh nash": ["parameters.n", "parameters.k_min", "lag_time_min", "peak_discharge_m3s_per_mm"],
  "scs effective": ["cn_adjusted", "retention_mm", "initial_abstraction_mm", "total_effective_mm"],
  "hydrometrics rating-curve": ["a", "b", "h0", "r_squared"],
  "stats baseflow": ["n_values", "recession.k", "recession.half_life_days", "bfi"],
  "stats characteristic": ["wwx", "swx", "snx", "ssx"],
  "stats duration-curve": ["max", "mean", "min", "median"],
  "stats harmonics": ["n_harmonics", "period_years", "period.r_squared", "period.mean"],
  "stats low-flow-sequences": ["threshold", "max_duration_days", "total_deficit", "n_events"],
  "stats mann-kendall": ["s_statistic", "z_score", "sen_slope", "p_value"],
  "stats regime": ["regime_type.code", "spring_share", "seasonality_index", "annual_mean"],
  "stats runoff-volume": ["period_years", "n_complete_years", "mean_annual_volume_m3"],
  "stats seasonality": ["period_years", "winter_share", "concentration", "mean_date"],
  "stats threshold-events": ["period_years", "days_beyond", "max_duration_days", "n_events"],
  "meteo hydrothermal": ["period_years", "period.n_years", "period.mean_season_coefficient"],
  "meteo precipitation sums": ["period.mean_mm", "period.cv", "period.max_mm", "period.normal_mm"],
  "meteo precipitation maxima": ["period_years", "period.n_years"],
  "meteo precipitation days": ["period_years", "period.n_years"],
  "meteo precipitation intensity": ["period.n_years", "period.mean_total_mm", "period.mean_sdii_mm"],
  "meteo precipitation heavy": ["period.n_years", "period.wet_days"],
  "meteo precipitation seasonality": ["period.mean_pci", "period.mean_si", "period.pci", "period.si"],
  "meteo snow": ["period.mean_max_depth_cm", "period.years_without_cover", "period.max_depth_cm", "period.mean_cover_days"],
  "meteo spells": ["n_spells", "max_duration_days", "period.mean_max_duration_days", "period.mean_n_spells"],
  "meteo spi": ["reference_period_years", "period.normal_years", "period.normal_mm"],
  "meteo temperature means": ["period.tmin_c", "period.tmax_c", "period.normal_c", "period.tmean_c"],
  "meteo temperature days": ["period.frost_days", "period.ice_days", "period.summer_days", "period.hot_days"],
  "meteo temperature degree_days": ["period.n_years", "period.growing_degree_days", "period.heating_degree_days"],
  "meteo temperature range": ["period.n_years", "period.dtr_c"],
};

/**
 * The series a command's chart draws of its first group, when not all of them: one unit
 * on the axis (Pardé's coefficients, not the monthly means in m³/s beside them; the
 * thresholds of the heavy precipitation, not their shares in %).
 */
const CHARTED = {
  "stats regime": ["parde"],
  "meteo precipitation": ["period.thresholds_mm"],
};

/**
 * The tiles of a run's result: its command's, by its `index` when it has one.
 *
 * @param {string} command the command
 * @param {object} envelope the run's envelope
 * @returns {string[]|null} the fields of the tiles, null for the generic choice
 */
function tilesOf(command, envelope) {
  const index = envelope.result && envelope.result.index;
  return (typeof index === "string" && TILES[`${command} ${index}`]) || TILES[command] || null;
}

/**
 * The group a run's chart draws: its series of CHARTED when it has any, else all.
 *
 * @param {string} command the command
 * @param {object} group a group of analyzeResult's `series`
 * @returns {object} the group to draw
 */
function charted(command, group) {
  const keys = CHARTED[command] || [];
  const ys = group.ys.filter((array) => keys.includes(array.key));
  return ys.length ? { ...group, ys } : group;
}

/**
 * The centre: the tables of the last run, or its JSON.
 *
 * @param {{run: object|null, tab: "table"|"json"}} props the last run and the tab shown
 * @returns {object} the centre's body
 */
export function CenterBody({ run, tab }) {
  if (!run) return html`<p class="empty-note">${texts.noResult}</p>`;
  if (tab === "json") return html`<${ResultJson} envelope=${run.envelope} />`;
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
  const first = analysis.series[0] ? charted(command, analysis.series[0]) : null;
  return html`
    <${ResultSummary} analysis=${analysis} inputs=${envelope.inputs} keys=${tilesOf(command, envelope)} />
    ${first ? html`<${ResultSeries} group=${first} table=${false} svgRef=${chartSvg} size="small" bare=${true} />` : null}
    <${CommandLine} command=${command} options=${options} />
    <h3 class="group-title">${resultTexts.notices}</h3>
    <${Notices} notices=${analysis.notices} />
    <${ExportButtons} spec=${spec} />
    <${FileList} files=${analysis.files} />
    <${Attribution} lines=${linesOf(envelope)} />
  `;
}
