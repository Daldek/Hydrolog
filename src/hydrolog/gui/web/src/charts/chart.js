/**
 * `Chart`: the Preact component of a chart (plan, "Interfaces fixed by this plan").
 *
 * ```js
 * html`<${Chart} spec=${{x: {label, scale}, y: {label}, y2, series: [{id, kind, data, axis, cls, label}],
 *                        marks, legend, readout}} svgRef=${ref} />`
 * ```
 *
 * The spec:
 * - `x`: `{label, scale: "linear" | "log" | "time" | "gumbel", min, max, domain, digits, short}`;
 *   `time` takes minutes and labels hours; `gumbel` takes the exceedance probability [%]
 *   (`domain: [99, 0.1]` fixes its ends) and labels p and T = 100 / p.
 * - `y`: `{label, unit, scale: "linear" | "log" | "band", min, max, zero, pad, ticks, digits}`;
 *   `band` draws one horizontal bar per point (`{x: value, y: name, sub, cls, text}`).
 * - `y2`: the same as `y` for a panel above the main one, sharing the x axis, whose bars
 *   hang from its top (the hyetograph above the hydrograph); `share` is its part of the height.
 * - `series`: `{id, kind: "line" | "step" | "area" | "bars" | "points" | "rug", data: [[x, y], …]
 *   (or `{x, y, cls}`; a `rug` takes x values only: short ticks on the x axis), axis: "y" | "y2",
 *   cls: "s1"…"s6" | "bar-p" | "bar-pe" | …, label, unit, digits, width, align, readout, legend}`.
 * - `marks`: `{kind: "peak", x, y, label, cls, guides: "x" | "xy"}`, `{kind: "hline", y, label}`,
 *   `{kind: "vline", x, from, to, extend, label}`, `{kind: "note", x, y, label, dx, dy, anchor}`;
 *   `axis: "y2"` puts a mark on the upper panel.
 * - `legend`: `true` (the labelled series) or items `{label, kind, cls}` (`kind: "text"` a note).
 * - `readout`: `true` or `{series, x: (x) => text, value: (value, series) => text}`: a cursor
 *   by pointer and by keys (arrows, Shift or Page for ten steps, Home, End, Esc).
 * - `size`: "wide" (760 × 432, the default), "small" (360 × 178) or `{width, height}`;
 *   `title` (the aria-label) or `labelledBy` (an element's id).
 *
 * The drawing itself is `drawChart` (DOM only); this component mounts it and
 * redraws when `spec` changes. `svgRef.current` is the SVG (for `toPng`).
 */

import htm from "../../vendor/htm/htm.mjs";
import { h } from "../../vendor/preact/preact.mjs";
import { useEffect, useRef } from "../../vendor/preact/hooks.mjs";
import { drawChart } from "./draw.js";

const html = htm.bind(h);

/**
 * A chart drawn from a spec.
 *
 * @param {{spec: object, svgRef?: {current: SVGSVGElement | null}, class?: string}} props
 * @returns {import("../../vendor/preact/preact.mjs").VNode}
 */
export function Chart({ spec, svgRef, class: extra }) {
  const host = useRef(null);
  const handle = useRef(null);

  useEffect(() => {
    handle.current = drawChart(host.current, spec);
    if (svgRef) svgRef.current = handle.current.svg;
    return () => {
      handle.current.destroy();
      handle.current = null;
      if (svgRef) svgRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (handle.current) handle.current.update(spec);
  }, [spec]);

  return html`<div class=${extra ? `chart ${extra}` : "chart"} ref=${host}></div>`;
}
