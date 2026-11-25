// The export spec of „Wszystkie polecenia” (plan D14): the table shown as CSV, the envelope
// as JSON, the chart as PNG, the command line of the run and the files it wrote; the CSV and
// the PNG carry the providers' lines of the envelope (Nogat DEV-20.5); the command is the
// content of their names, `hydrolog_uh-nash.csv` (ExportButtons).

import { linesOf } from "../../attribution.js";
import { resultCsv } from "../../forms/result-view.js";

/**
 * The group of series a command's chart and CSV take when not the first, by its x axis:
 * the flow-duration curve of `stats duration-curve` (`curve_exceedance_percents`: the
 * period-of-record curve, the median annual curve and its interval, ECO-091) rather than
 * its values at the percentages asked.
 */
const GROUPS = { "stats duration-curve": "curve_exceedance_percents" };

/**
 * The group of series of a run that its chart and CSV show: its command's (GROUPS), else
 * the first.
 *
 * @param {string} command the command
 * @param {object} analysis the run's analyzeResult
 * @returns {object|undefined} the group, none without series
 */
export function shownGroup(command, analysis) {
  const axis = Object.hasOwn(GROUPS, command) ? GROUPS[command] : null;
  return analysis.series.find((group) => axis && group.x && group.x.key === axis) ?? analysis.series[0];
}

/**
 * The export spec of a command's result.
 *
 * @param {{command: string, options: object, envelope: object, analysis: object,
 *   chartSvg: {current: SVGSVGElement|null}}} run the command, the options it ran with, its
 *   envelope, the envelope's analysis and the ref of the chart shown
 * @returns {object} the spec of ExportPanel
 */
export function exportSpec({ command, options, envelope, analysis, chartSvg }) {
  return {
    content: command.trim().replace(/\s+/g, "-"),
    csv: () => resultCsv(analysis, shownGroup(command, analysis)),
    json: () => envelope,
    chart: analysis.series.length ? () => chartSvg.current : undefined,
    cli: { command, options },
    files: analysis.files,
    lines: linesOf(envelope),
  };
}
