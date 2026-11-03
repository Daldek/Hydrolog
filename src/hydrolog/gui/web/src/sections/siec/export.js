// The exports of Sieć (plan D14): written in the browser, the hydrograph of the chosen node
// as `time_min,discharge_m3s` (what every `route` command reads) and every node's as
// columns of one table (an `inflows_file` of another network), the network's document
// and the envelope of the last run as JSON, the schematic as drawn as PNG; Hydrolog's
// own schematic, the SVG `route network` wrote with `schematic`; and the print view.

import { api } from "../../api.js";
import { t } from "../../labels/common.js";
import { exportLabels } from "../../labels/exports.js";
import { siec as texts } from "../../labels/siec.js";
import { fileStem } from "./state.js";

/**
 * A node's hydrograph as CSV: comma separated, decimal dot, UTF-8.
 *
 * @param {{times_min: number[], discharge_m3s: number[]}} node a node of the result
 * @returns {string} the CSV text
 */
export function nodeCsv(node) {
  const lines = ["time_min,discharge_m3s"];
  node.times_min.forEach((time, index) => lines.push(`${time},${node.discharge_m3s[index]}`));
  return `${lines.join("\n")}\n`;
}

/**
 * Every node's hydrograph as a column of one table on the union of their times (a node
 * whose hydrograph ended earlier has empty cells there).
 *
 * @param {object} result hydrolog-route-network/1 with the hydrographs
 * @returns {string} the CSV text: time_min and one column per node, in the order of the
 *   calculation
 */
export function networkCsv(result) {
  const byId = new Map((result.nodes || []).map((node) => [node.id, node]));
  const order = (result.order || []).filter((id) => byId.has(id) && Array.isArray(byId.get(id).times_min));
  const key = (time) => Math.round(time * 1e6) / 1e6;
  const times = new Map();
  const columns = order.map((id) => {
    const node = byId.get(id);
    const values = new Map();
    node.times_min.forEach((time, index) => {
      times.set(key(time), time);
      values.set(key(time), node.discharge_m3s[index]);
    });
    return values;
  });
  const sorted = [...times.keys()].sort((a, b) => a - b);
  const quote = (id) => (/[",\n\r]/.test(id) ? `"${id.replace(/"/g, '""')}"` : id);
  const lines = [["time_min", ...order.map(quote)].join(",")];
  for (const at of sorted) {
    lines.push([times.get(at), ...columns.map((values) => (values.has(at) ? values.get(at) : ""))].join(","));
  }
  return `${lines.join("\n")}\n`;
}

/**
 * The exports of the section now: what each saves, and whether it can.
 *
 * @param {{state: object, document: object|null, valid: boolean, run: object|null,
 *   selected: string|null, schematicSvg: {current: SVGSVGElement|null}}} at the state,
 *   the network's document and whether it is complete, the last run, the chosen node and
 *   the drawn schematic
 * @returns {Array<{id: string, format: string, label: string, title: string,
 *   disabled?: string, text?: () => string, type?: string, name?: string,
 *   svg?: () => SVGSVGElement|null, href?: string, print?: boolean}>} the exports
 */
export function exportItems({ state, document, valid, run, selected, schematicSvg }) {
  const stem = fileStem(state);
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const node = result && selected ? (result.nodes || []).find((item) => item.id === selected) : null;
  const svgFile = result && Array.isArray(result.files) ? result.files.find((file) => /\.svg$/i.test(String(file.path))) : null;
  const noRun = texts.exports.afterRun;
  return [
    {
      id: "csv-node",
      format: "CSV",
      label: selected ? t(texts.exports.node, { id: selected }) : texts.exports.nodeNone,
      title: texts.exports.nodeTitle,
      disabled: node && Array.isArray(node.times_min) ? null : noRun,
      text: () => nodeCsv(node),
      type: "text/csv;charset=utf-8",
      name: `${stem}-${selected}.csv`,
    },
    {
      id: "csv-all",
      format: "CSV",
      label: texts.exports.all,
      title: texts.exports.allTitle,
      disabled: result ? null : noRun,
      text: () => networkCsv(result),
      type: "text/csv;charset=utf-8",
      name: `${stem}-wezly.csv`,
    },
    {
      id: "json-network",
      format: "JSON",
      label: texts.exports.network,
      title: texts.exports.networkTitle,
      disabled: document && valid ? null : texts.exports.invalid,
      text: () => `${JSON.stringify(document, null, 2)}\n`,
      type: "application/json",
      name: `${stem}.json`,
    },
    {
      id: "json-result",
      format: "JSON",
      label: texts.exports.result,
      title: texts.exports.resultTitle,
      disabled: run ? null : noRun,
      text: () => `${JSON.stringify(run.envelope, null, 2)}\n`,
      type: "application/json",
      name: `${stem}.result.json`,
    },
    {
      id: "png",
      format: "PNG",
      label: texts.exports.png,
      title: texts.exports.pngTitle,
      disabled: schematicSvg.current ? null : texts.exports.noSchematic,
      svg: () => schematicSvg.current,
      name: `${stem}.png`,
    },
    {
      id: "svg",
      format: "SVG",
      label: texts.exports.svg,
      title: texts.exports.svgTitle,
      disabled: svgFile ? null : noRun,
      href: svgFile ? api.fileUrl(svgFile.path) : null,
      name: `${stem}.svg`,
    },
    {
      id: "print",
      format: exportLabels.print.format,
      label: exportLabels.print.label,
      title: exportLabels.print.title,
      print: true,
    },
  ];
}
