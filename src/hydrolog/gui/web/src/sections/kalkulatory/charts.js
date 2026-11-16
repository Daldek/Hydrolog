// The chart of „Kalkulatory”: the comparison of the tc methods as horizontal bars on a band
// axis (plan D12), one per method, coloured by how far the method applies (ok, warn, bad)
// and outlined when Hydrogram zlewni uses it; each bar is labelled with tc in minutes and
// hours.

import { inputText, num, plural } from "../../format.js";
import { t } from "../../labels/common.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { barRows } from "./compare.js";

/** The height of the chart per bar and around them [viewBox units] (the mockup's). */
const ROW_HEIGHT = 47.3;
const FRAME_HEIGHT = 60;

/**
 * The spec of the tc comparison.
 *
 * @param {object[]} rows the rows of compareRows
 * @param {string} title the chart's accessible name
 * @returns {object|null} the Chart spec, null without a method to draw
 */
export function tcSpec(rows, title) {
  const drawn = barRows(rows);
  if (!drawn.length) return null;
  return {
    title,
    size: { width: 760, height: Math.round(FRAME_HEIGHT + ROW_HEIGHT * drawn.length) },
    x: { label: texts.chart.axis },
    y: { scale: "band", width: 160 },
    series: [
      {
        id: "tc",
        data: drawn.map((row) => ({
          y: row.name,
          sub: row.method,
          x: row.tc_min,
          cls: row.cls,
          text: t(texts.chart.bar, { min: num(row.tc_min, 1), h: num(row.tc_h, 2) }),
        })),
      },
    ],
    legend: [
      { kind: "box", cls: "ok", label: texts.chart.legend.ok },
      { kind: "box", cls: "warn", label: texts.chart.legend.warn },
      { kind: "box", cls: "bad", label: texts.chart.legend.bad },
      { kind: "box", cls: "used", label: texts.chart.legend.used },
    ],
  };
}

/**
 * The title of the chart: „Czas koncentracji: 6 metod”.
 *
 * @param {number} count the methods drawn
 * @returns {string} the title
 */
export function tcTitle(count) {
  return t(texts.chart.title, { count: plural(count, texts.chart.methodForms) });
}

/**
 * The line under the chart's title: the watershed sent and its main fields, L and S of its
 * longest flow path (Kirpich's).
 *
 * @param {object} watershed the watershed of the run
 * @returns {string} „Kamiennik — Świerzawa · A 37,22 km² · L 15,88 km · S 0,0114 m/m · CN 65”
 */
export function chartSub(watershed) {
  const value = (name) => (typeof watershed[name] === "number" ? inputText(watershed[name]) : "–");
  return t(texts.chart.sub, {
    name: watershed.name || texts.watershed.unnamed,
    area: value("area_km2"),
    length: value("flow_path_length_km"),
    slope: value("flow_path_slope_m_per_m"),
    cn: value("cn"),
  });
}
