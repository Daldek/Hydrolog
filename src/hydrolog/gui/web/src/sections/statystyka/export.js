// The export spec of „Statystyka przepływów” (plan D14): the quantiles of the combinations
// ticked „W tabeli kwantyli” with the ends of their confidence intervals as CSV (comma
// separator, decimal dot, UTF-8), the envelope as JSON, the probability plot as PNG and the
// call of the run; the CSV and the PNG carry the providers' lines of the run's envelope
// (Nogat DEV-20.5). The files are `hydrolog_quantiles_<series file>` (ExportButtons), a
// pasted series's without its part.

import { linesOf } from "../../attribution.js";
import { COMMAND, tickedFits } from "./state.js";

/**
 * A confidence level as a column name writes it: the per cent, its shortest exact form with
 * a decimal dot, 0.95 gives "ci95", 0.683 "ci68.3".
 *
 * @param {number} level the confidence level, in (0, 1)
 * @returns {string} the part of the column name
 */
function levelName(level) {
  return `ci${Number((level * 100).toPrecision(12))}`;
}

/**
 * The quantiles of a result as CSV: one row per return period, its exceedance probability
 * and per ticked combination, in the order of the distributions table, a column of its
 * quantiles, `<distribution>_<fit_method>_m3s`, then the ends of its confidence interval at
 * each level asked (ECO-091), `<distribution>_<fit_method>_ci95_lower_m3s` and `…_upper_m3s`,
 * as Hydrolog gave them; an end Hydrolog did not compute (a method without an interval, a
 * bound below 0) is an empty cell. With none ticked only the periods and the probabilities.
 *
 * @param {object} result the result of `stats flood-frequency`
 * @param {string[]} ticked the keys of the ticked combinations
 * @returns {string} the CSV text
 */
function quantilesCsv(result, ticked) {
  const columns = tickedFits(result, ticked).flatMap((fit) => {
    const name = `${fit.distribution_name}_${fit.fit_method}`;
    const ends = (fit.intervals || []).flatMap((entry) => [
      { header: `${name}_${levelName(entry.confidence_level)}_lower_m3s`, values: entry.ci_lower },
      { header: `${name}_${levelName(entry.confidence_level)}_upper_m3s`, values: entry.ci_upper },
    ]);
    return [{ header: `${name}_m3s`, values: fit.quantiles }, ...ends];
  });
  // Every combination of a run has the same periods and probabilities
  const [first] = result.distributions;
  const periods = first ? first.return_periods : [];
  const cell = (value) => (value === null || value === undefined ? "" : String(value));
  const lines = [["return_period_years", "exceedance_probability", ...columns.map((column) => column.header)].join(",")];
  periods.forEach((period, index) => {
    lines.push([period, first.exceedance_probabilities[index], ...columns.map((column) => column.values?.[index])].map(cell).join(","));
  });
  return `${lines.join("\n")}\n`;
}

/**
 * The subject of the file names of an export: the series' file without its extension, ""
 * for a pasted series.
 *
 * @param {object} options the options of the run
 * @returns {string} e.g. "maksima_roczne"
 */
function subjectOf(options) {
  return typeof options.input_file === "string" ? options.input_file.replace(/^in\//, "").replace(/\.[^.]+$/, "") : "";
}

/**
 * The export spec of a run.
 *
 * @param {{options: object, envelope: object, ticked: string[],
 *   chartSvg: {current: SVGSVGElement|null}|null}} run the options sent, the envelope, the
 *   keys of the combinations ticked for the quantile table and the ref of the chart when it
 *   is shown (PNG exports the chart on the screen)
 * @returns {object} the spec of ExportButtons
 */
export function exportSpec({ options, envelope, ticked, chartSvg }) {
  return {
    content: "quantiles",
    subject: subjectOf(options),
    csv: () => quantilesCsv(envelope.result, ticked),
    json: () => envelope,
    chart: chartSvg ? () => chartSvg.current : undefined,
    cli: { command: COMMAND, options },
    lines: linesOf(envelope),
  };
}
