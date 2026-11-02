// The exports of „Kalkulatory” (plan D14): the tc comparison as CSV and as the shell loop of
// its six calls, and a calculator's result as CSV, JSON, PNG and its call.

import { csvCell, resultCsv } from "../../forms/result-view.js";
import { wrapLine } from "../../ui/export-panel.js";

/**
 * The tc comparison as CSV: one row per method with tc, how far it applies, the codes of its
 * notices and every parameter a method took (empty where it took none).
 *
 * @param {object[]} rows the rows of compareRows
 * @returns {string} the CSV text (comma separator, decimal dot)
 */
export function compareCsv(rows) {
  const parameters = [];
  for (const row of rows) for (const name of Object.keys(row.parameters)) if (!parameters.includes(name)) parameters.push(name);
  const header = ["method", "tc_min", "tc_h", "applicability", "notice_codes", ...parameters];
  const lines = [header.join(",")];
  for (const row of rows) {
    const state = row.ok ? row.cls.split(" ")[0] : "error";
    const cells = [
      row.method,
      row.tc_min ?? "",
      row.tc_h ?? "",
      state,
      row.notices.map((notice) => notice.code).join(";"),
      ...parameters.map((name) => row.parameters[name] ?? ""),
    ];
    lines.push(cells.map(csvCell).join(","));
  }
  return `${lines.join("\n")}\n`;
}

/**
 * The shell loop of the comparison from the formatted call of its first method: the method
 * becomes the loop's variable.
 *
 * @param {string} line the command line of `tc watershed` for `methods[0]`
 * @param {string[]} methods the methods
 * @returns {string} the loop, its body wrapped at " --"
 */
export function loopLine(line, methods) {
  const body = line.replace(new RegExp(` --method ${methods[0]}(?= |$)`), ' --method "$m"');
  const wrapped = wrapLine(body).replace(/\n/g, "\n  ");
  return `for m in ${methods.join(" ")}; do\n  ${wrapped}\ndone`;
}

/**
 * The export spec of a calculator's result.
 *
 * @param {{command: string, options: object, envelope: object, analysis: object,
 *   chartSvg: {current: SVGSVGElement|null}}} run the command, the options it ran with, its
 *   envelope, its analysis and the ref of the chart shown
 * @returns {object} the spec of ExportButtons
 */
export function exportSpec({ command, options, envelope, analysis, chartSvg }) {
  return {
    subject: command.trim().replace(/\s+/g, "-"),
    csv: () => resultCsv(analysis),
    json: () => envelope,
    chart: analysis.series.length ? () => chartSvg.current : undefined,
    cli: { command, options },
    files: analysis.files,
  };
}
