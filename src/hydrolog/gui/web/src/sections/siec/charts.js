// The chart of a node's result in Sieć (plan S4, D12): the hydrographs flowing into the
// node, dashed, and the one leaving it, a line over an area, with its peak; a pure module
// (the spec of charts/chart.js). The browser draws what `route network` computed: the
// inflows of a node are the hydrographs of the nodes it names in `from`.

import { hmm, num } from "../../format.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";

/** Classes of the inflow lines, dashed and dotted (charts.css). */
const INFLOW_CLASSES = ["s4", "s5", "s6", "s2", "s3"];

/**
 * The points of a node's hydrograph.
 *
 * @param {{times_min: number[], discharge_m3s: number[]}} node a node of the result
 * @returns {Array<[number, number]>} [time, discharge] pairs
 */
export function hydrographPoints(node) {
  return node.times_min.map((time, index) => [time, node.discharge_m3s[index]]);
}

/**
 * The nodes of a result by id.
 *
 * @param {object} result hydrolog-route-network/1
 * @returns {Map<string, object>} the nodes
 */
export function resultNodes(result) {
  return new Map(((result && result.nodes) || []).map((node) => [node.id, node]));
}

/**
 * The nodes whose hydrographs flow into a node, with their hydrographs (none for the
 * outlet, whose one inflow is its own hydrograph).
 *
 * @param {Map<string, object>} nodes the result's nodes by id
 * @param {object} node the node
 * @returns {object[]} the upstream nodes of the result
 */
export function inflowsOf(nodes, node) {
  if (node.type === "outlet") return [];
  return (node.from || []).map((id) => nodes.get(id)).filter((item) => item && Array.isArray(item.times_min));
}

/**
 * The words of a node's own line: the hydrograph of a source, the outflow of a routing
 * element, the sum at a junction, the outlet.
 *
 * @param {object} node the node of the result
 * @returns {string} the legend's label
 */
export function outflowLabel(node) {
  const words = texts.chart.own[node.type] || texts.chart.own.other;
  return t(words, { id: node.id });
}

/**
 * The chart spec of a node of a result.
 *
 * @param {object} result hydrolog-route-network/1 with the hydrographs
 * @param {string} id the node
 * @param {{size?: string}} [how] the chart's size ("small" by default)
 * @returns {object|null} the spec of Chart, null when the result has no hydrograph of it
 */
export function nodeChartSpec(result, id, how = {}) {
  const nodes = resultNodes(result);
  const node = nodes.get(id);
  if (!node || !Array.isArray(node.times_min) || !node.times_min.length) return null;
  const series = inflowsOf(nodes, node).map((inflow, index) => ({
    id: `in-${inflow.id}`,
    kind: "line",
    data: hydrographPoints(inflow),
    cls: INFLOW_CLASSES[index % INFLOW_CLASSES.length],
    label: t(texts.chart.inflow, { id: inflow.id }),
    unit: "m³/s",
  }));
  const points = hydrographPoints(node);
  series.push({ id: `area-${node.id}`, kind: "area", data: points, cls: "s1", legend: false, readout: false });
  series.push({ id: `out-${node.id}`, kind: "line", data: points, cls: "s1", label: outflowLabel(node), unit: "m³/s" });
  return {
    x: { label: texts.chart.time, scale: "time" },
    y: { label: texts.chart.discharge, unit: "m³/s", min: 0 },
    series,
    marks: [
      {
        kind: "peak",
        x: node.time_to_peak_min,
        y: node.peak_m3s,
        label: t(texts.chart.peak, { peak: num(node.peak_m3s, 1), time: hmm(node.time_to_peak_min) }),
        cls: "s1",
      },
    ],
    legend: true,
    readout: true,
    size: how.size || "small",
    title: t(texts.chart.title, { id: node.id }),
  };
}
