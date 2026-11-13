// The export spec of „Wszystkie polecenia” (plan D14): the table shown as CSV, the envelope
// as JSON, the chart as PNG, the command line of the run and the files it wrote; the CSV and
// the PNG carry the providers' lines of the envelope (Nogat DEV-20.5).

import { linesOf } from "../../attribution.js";
import { resultCsv } from "../../forms/result-view.js";

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
    subject: command.trim().replace(/\s+/g, "-"),
    csv: () => resultCsv(analysis),
    json: () => envelope,
    chart: analysis.series.length ? () => chartSvg.current : undefined,
    cli: { command, options },
    files: analysis.files,
    lines: linesOf(envelope),
  };
}
