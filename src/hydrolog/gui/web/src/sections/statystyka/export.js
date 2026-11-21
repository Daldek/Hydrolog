// The export spec of „Statystyka przepływów” (plan D14): the quantiles of the combinations
// ticked „W tabeli kwantyli” as CSV (comma separator, decimal dot, UTF-8), the envelope as
// JSON, the probability plot as PNG and the call of the run; the CSV and the PNG carry the
// providers' lines of the run's envelope (Nogat DEV-20.5). The files are
// `hydrolog_quantiles_<series file>` (ExportButtons), a pasted series's without its part.

import { linesOf } from "../../attribution.js";
import { COMMAND, tickedFits } from "./state.js";

/**
 * The quantiles of a result as CSV: one row per return period, its exceedance probability
 * and a column of quantiles per ticked combination, `<distribution>_<fit_method>_m3s`, in
 * the order of the distributions table, as Hydrolog gave them; with none ticked only the
 * periods and the probabilities.
 *
 * @param {object} result the result of `stats flood-frequency`
 * @param {string[]} ticked the keys of the ticked combinations
 * @returns {string} the CSV text
 */
function quantilesCsv(result, ticked) {
  const fits = tickedFits(result, ticked);
  // Every combination of a run has the same periods and probabilities
  const [first] = result.distributions;
  const periods = first ? first.return_periods : [];
  const header = ["return_period_years", "exceedance_probability", ...fits.map((fit) => `${fit.distribution_name}_${fit.fit_method}_m3s`)];
  const lines = [header.join(",")];
  periods.forEach((period, index) => {
    lines.push([period, first.exceedance_probabilities[index], ...fits.map((fit) => fit.quantiles[index])].map(String).join(","));
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
