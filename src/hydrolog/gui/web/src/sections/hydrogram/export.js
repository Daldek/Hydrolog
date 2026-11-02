// The export spec of „Hydrogram zlewni” (plan D14): the hydrograph as CSV (written in the
// browser: `time_min,discharge_m3s,precipitation_mm,effective_precipitation_mm`, comma
// separator, decimal dot, UTF-8, the table every `route` command reads), the envelope as
// JSON, the chart shown as PNG and the command line of the run. The Markdown report, the
// print view and the hand-off are slice S6's.

import { COMMAND } from "./state.js";

/** The columns of the hydrograph's CSV (hydrolog-hydrograph-csv). */
export const CSV_COLUMNS = Object.freeze([
  "time_min",
  "discharge_m3s",
  "precipitation_mm",
  "effective_precipitation_mm",
]);

/**
 * The value of a series in the step that ends at ordinate `index` (rainfall falls in the
 * step before the ordinate; nothing before the first ordinate or after the last step).
 *
 * @param {number[]|undefined} series the values per step
 * @param {number} index the ordinate
 * @returns {number} the value, 0 outside the series
 */
export function stepEndingAt(series, index) {
  const step = index - 1;
  return Array.isArray(series) && step >= 0 && step < series.length ? series[step] : 0;
}

/**
 * The hydrograph as CSV: a row per ordinate, the rainfall of the step ending at it, every
 * number in its shortest exact form (it reads back unchanged).
 *
 * @param {object} result the result of `hydrograph generate`
 * @returns {string} the CSV text
 */
export function hydrographCsv(result) {
  const times = result.times_min || [];
  const flows = result.discharge_m3s || [];
  const lines = [CSV_COLUMNS.join(",")];
  for (let index = 0; index < times.length; index += 1) {
    lines.push(
      [
        times[index],
        flows[index],
        stepEndingAt(result.precipitation_mm, index),
        stepEndingAt(result.effective_precipitation_mm, index),
      ]
        .map(String)
        .join(","),
    );
  }
  return `${lines.join("\n")}\n`;
}

/**
 * The export spec of the section's result.
 *
 * @param {{subject: string, options: object, envelope: object,
 *   chartSvg: {current: SVGSVGElement|null}}} run the subject (the watershed's name), the
 *   options of the run, its envelope and the ref of the main chart
 * @returns {object} the spec of ExportPanel (CSV, JSON, PNG, the call)
 */
export function exportSpec({ subject, options, envelope, chartSvg }) {
  return {
    subject,
    csv: () => hydrographCsv(envelope.result),
    json: () => envelope,
    chart: () => chartSvg.current,
    cli: { command: COMMAND, options },
  };
}
