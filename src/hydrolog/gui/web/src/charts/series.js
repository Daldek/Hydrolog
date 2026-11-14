/**
 * Series and marks of a chart: path geometry (pure) and SVG elements.
 *
 * Series kinds: `line`, `step` (a value holds until the next point), `area`
 * (filled down to zero, with its line), `bars` (vertical; on the `y2` panel
 * they hang from its top: the hyetograph), `points` (the empirical points of
 * a probability plot), `rug` (short ticks on the x axis at x values, without
 * a y and without a readout value) and, on a band y axis, horizontal bars (one
 * category per point, `{x: value, y: name, sub, cls, text}`). A series' `cls`
 * (`s1` to `s6`, `bar-p`, `bar-pe`, `best`, …) picks its colour in `css/charts.css`.
 * Marks: `peak` (a dot, a guide to the axis and a boxed label), `hline` (a
 * reference value across the plot), `vline` (a moment, with a note) and
 * `note` (a text at a point).
 */

import { barWidth, points } from "./axes.js";
import { c1, svgEl, textEl } from "./svg.js";

/** The default colour classes, by the series' order. */
const SERIES_CLASSES = ["s1", "s2", "s3", "s4", "s5", "s6"];

/**
 * A polyline's `d`: "M x,y L x,y …"; a non-finite point starts a new subpath.
 *
 * @param {[number, number][]} xy points in viewBox units
 * @returns {string}
 */
function linePath(xy) {
  let d = "";
  let pen = false;
  for (const [x, y] of xy) {
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      pen = false;
      continue;
    }
    d += `${pen ? "L" : "M"}${c1(x)},${c1(y)}`;
    pen = true;
  }
  return d;
}

/**
 * A step line (each value holds until the next point; the last one ends there).
 *
 * @param {[number, number][]} xy points in viewBox units
 * @returns {[number, number][]} the corners
 */
function stepPoints(xy) {
  const out = [];
  xy.forEach(([x, y], index) => {
    if (index > 0) out.push([x, xy[index - 1][1]]);
    out.push([x, y]);
  });
  return out;
}

/**
 * A filled area between a line and a baseline: "M…Z" for each finite run.
 *
 * @param {[number, number][]} xy points in viewBox units
 * @param {number} base the baseline's y
 * @returns {string}
 */
function areaPath(xy, base) {
  const runs = [];
  let run = [];
  for (const point of xy) {
    if (Number.isFinite(point[0]) && Number.isFinite(point[1])) run.push(point);
    else if (run.length) {
      runs.push(run);
      run = [];
    }
  }
  if (run.length) runs.push(run);
  return runs
    .map((part) => `${linePath([[part[0][0], base], ...part, [part.at(-1)[0], base]])}Z`)
    .join("");
}

/**
 * Value of a series at an x coordinate of the viewBox: linear between points
 * (lines, areas), the last value before it (steps), the bar that contains it
 * (bars), the nearest point within `snap` (points); a rug has none.
 *
 * @param {{kind: string, px: number[], values: number[], spans?: [number, number][]}} geometry
 *   a series' points in viewBox x (`px`, increasing) and their values
 * @param {number} at an x of the viewBox
 * @param {number} [snap=6] how far a point of a `points` series may be
 * @returns {number | null} the value, or null outside the series
 */
export function valueAt(geometry, at, snap = 6) {
  const { kind, px, values, spans } = geometry;
  if (!px.length || kind === "rug") return null;
  if (kind === "bars") {
    const index = spans.findIndex(([a, b]) => at >= a - 1e-6 && at < b - 1e-6);
    return index < 0 ? null : values[index];
  }
  if (kind === "points") {
    let best = -1;
    for (let i = 0; i < px.length; i += 1) {
      if (Math.abs(px[i] - at) <= snap && (best < 0 || Math.abs(px[i] - at) < Math.abs(px[best] - at))) best = i;
    }
    return best < 0 ? null : values[best];
  }
  if (at < px[0] - 1e-6 || at > px.at(-1) + 1e-6) return null;
  const hi = px.findIndex((x) => x >= at - 1e-6);
  if (Math.abs(px[hi] - at) <= 1e-6) return values[hi];
  const lo = hi - 1;
  if (kind === "step") return values[lo];
  const share = (at - px[lo]) / (px[hi] - px[lo]);
  return values[lo] + share * (values[hi] - values[lo]);
}

/**
 * The points of a long line, area or step drawn (drawing only; the tables and exports keep
 * every value): with more than four points per column of the plot, each column keeps its
 * first, last, lowest and highest point and its first gap, so the drawn line and its peaks
 * look the same with a few thousand points instead of a hundred thousand.
 *
 * @param {{x: number, y: number}[]} points the points in increasing x
 * @param {(x: number) => number} place the x scale (to viewBox units)
 * @param {number} columns the plot's width in viewBox units
 * @returns {{x: number, y: number}[]} the points kept, in their order
 */
export function thinPoints(points, place, columns) {
  if (points.length <= 4 * columns) return points;
  const start = place(points[0].x);
  const width = place(points.at(-1).x) - start || 1;
  const out = [];
  let column = -1;
  let first;
  let last;
  let low;
  let high;
  let gap;
  const flush = () => {
    const kept = [first, low, high, gap, last].filter((index) => index !== null);
    kept.sort((a, b) => a - b);
    kept.forEach((index, at) => {
      if (at === 0 || index !== kept[at - 1]) out.push(points[index]);
    });
  };
  points.forEach((point, index) => {
    const at = Math.min(columns - 1, Math.floor(((place(point.x) - start) / width) * columns));
    if (at !== column) {
      if (column >= 0) flush();
      column = at;
      first = index;
      low = null;
      high = null;
      gap = null;
    }
    last = index;
    if (!Number.isFinite(point.y)) {
      if (gap === null) gap = index;
      return;
    }
    if (low === null || point.y < points[low].y) low = index;
    if (high === null || point.y > points[high].y) high = index;
  });
  flush();
  return out;
}

/**
 * The geometry of each series of a layout: its viewBox points, values, class.
 *
 * @param {object} spec the chart spec
 * @param {ReturnType<import("./axes.js").chartLayout>} layout
 * @returns {object[]} per series: `{series, kind, cls, axis, px, py, values, spans, xs}`
 */
export function seriesGeometry(spec, layout) {
  let row = 0;
  return (spec.series ?? []).map((series, index) => {
    const kind = layout.band ? "hbars" : (series.kind ?? "line");
    const cls = series.cls ?? SERIES_CLASSES[index % SERIES_CLASSES.length];
    const data = points(series);
    if (kind === "hbars") {
      row += data.length;
      return { series, kind, cls, axis: "y", data, row: row - data.length, px: [], py: [], values: [], xs: [] };
    }
    const axis = series.axis === "y2" && layout.y2 ? layout.y2 : layout.y;
    const sorted = data
      .map((point, at) => ({ point, at }))
      .filter(({ point }) => Number.isFinite(point.x))
      .sort((a, b) => layout.x.scale(a.point.x) - layout.x.scale(b.point.x))
      .map(({ point }) => point);
    const thin = kind === "line" || kind === "area" || kind === "step";
    const order = thin ? thinPoints(sorted, layout.x.scale, Math.ceil(layout.plot.right - layout.plot.left)) : sorted;
    const px = order.map((point) => layout.x.scale(point.x));
    const py = order.map((point) => (Number.isFinite(point.y) ? axis.scale(point.y) : NaN));
    let spans;
    if (kind === "bars") {
      const width = barWidth(series, order);
      const shift = series.align === "center" ? width / 2 : 0;
      spans = order.map((point) => [
        layout.x.scale(point.x - shift),
        layout.x.scale(point.x - shift + width),
      ]);
    }
    return {
      series,
      kind,
      cls,
      axis: series.axis === "y2" && layout.y2 ? "y2" : "y",
      data: order,
      xs: order.map((point) => point.x),
      px,
      py,
      values: order.map((point) => point.y),
      spans,
    };
  });
}

function drawBars(geometry, layout) {
  const axis = geometry.axis === "y2" ? layout.y2 : layout.y;
  const zero = axis.scale(Math.max(axis.min, Math.min(axis.max, 0)));
  const rects = [];
  geometry.spans.forEach(([a, b], index) => {
    const value = geometry.values[index];
    if (!Number.isFinite(value) || value === 0) return;
    const at = axis.scale(value);
    const gap = b - a > 3 ? 0.5 : 0;
    rects.push(
      svgEl("rect", {
        x: a + gap,
        y: Math.min(at, zero),
        width: Math.max(0.5, b - a - 2 * gap),
        height: Math.abs(at - zero),
        class: geometry.data[index].cls,
      }),
    );
  });
  return svgEl("g", { class: `bars ${geometry.cls}`, "data-series": geometry.series.id }, rects);
}

function drawHorizontalBars(geometry, layout) {
  const { plot, x, y } = layout;
  const zero = x.scale(0);
  const offset = geometry.row;
  const group = svgEl("g", { class: `hbars ${geometry.cls}`, "data-series": geometry.series.id });
  geometry.data.forEach((point, index) => {
    const middle = plot.top + y.step * (offset + index + 0.5);
    const end = x.scale(point.x);
    group.append(
      svgEl("rect", {
        class: ["hbar", point.cls].filter(Boolean).join(" "),
        x: Math.min(zero, end),
        y: middle - y.bar / 2,
        width: Math.max(0.5, Math.abs(end - zero)),
        height: y.bar,
        rx: 3,
      }),
    );
    if (point.text) group.append(textEl("bar-val", Math.max(zero, end) + 8, middle + 4, point.text));
  });
  return group;
}

/**
 * Draw the series: areas first, then bars, lines and points on top.
 *
 * @param {object[]} geometries from `seriesGeometry`
 * @param {ReturnType<import("./axes.js").chartLayout>} layout
 * @returns {SVGElement[]}
 */
export function drawSeries(geometries, layout) {
  const rank = { area: 0, bars: 1, hbars: 1, step: 2, line: 2, points: 3, rug: 3 };
  const ordered = [...geometries].sort((a, b) => (rank[a.kind] ?? 2) - (rank[b.kind] ?? 2));
  const out = [];
  for (const geometry of ordered) {
    const { kind, cls, series } = geometry;
    const xy = geometry.px.map((x, i) => [x, geometry.py[i]]);
    if (kind === "bars") out.push(drawBars(geometry, layout));
    else if (kind === "hbars") out.push(drawHorizontalBars(geometry, layout));
    else if (kind === "points") {
      const dots = xy
        .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
        .map(([x, y]) => svgEl("circle", { cx: x, cy: y, r: layout.small ? 3 : 3.6 }));
      out.push(svgEl("g", { class: `emp ${cls}`, "data-series": series.id }, dots));
    } else if (kind === "rug") {
      const { bottom } = geometry.axis === "y2" ? layout.upper : layout.main;
      const length = layout.small ? 6 : 8;
      const ticks = geometry.px
        .filter((x) => Number.isFinite(x))
        .map((x) => svgEl("line", { x1: x, x2: x, y1: bottom, y2: bottom - length }));
      out.push(svgEl("g", { class: `rug ${cls}`, "data-series": series.id }, ticks));
    } else {
      const path = kind === "step" ? stepPoints(xy) : xy;
      if (kind === "area") {
        const axis = geometry.axis === "y2" ? layout.y2 : layout.y;
        const base = axis.scale(Math.max(axis.min, Math.min(axis.max, 0)));
        out.push(svgEl("path", { class: `q-area ${cls}`, d: areaPath(path, base), "data-series": series.id }));
      }
      out.push(svgEl("path", { class: `ser ${cls}`, d: linePath(path), "data-series": series.id }));
    }
  }
  return out;
}

/** An estimate of a text's width in viewBox units, corrected after drawing (`fitBoxes`). */
function textWidth(text, size = 12) {
  return String(text).length * size * 0.56;
}

/**
 * Draw the marks.
 *
 * @param {object[]} marks the spec's `marks`
 * @param {ReturnType<import("./axes.js").chartLayout>} layout
 * @returns {SVGElement[]}
 */
export function drawMarks(marks, layout) {
  const { plot, main, upper, x } = layout;
  const out = [];
  for (const mark of marks ?? []) {
    const axis = mark.axis === "y2" && layout.y2 ? layout.y2 : layout.y;
    const panel = mark.axis === "y2" && upper ? upper : main;
    const cls = mark.cls ?? "s1";
    if (mark.kind === "peak") {
      const px = x.scale(mark.x);
      const py = axis.scale(mark.y);
      const group = svgEl("g", { class: "mark peak", "data-mark": mark.id });
      group.append(svgEl("line", { class: "peak-line", x1: px, x2: px, y1: py, y2: panel.bottom }));
      if (mark.guides === "xy") group.append(svgEl("line", { class: "peak-line", x1: plot.left, x2: px, y1: py, y2: py }));
      group.append(svgEl("circle", { class: `peak-dot ${cls}`, cx: px, cy: py, r: layout.small ? 3.5 : 4.5 }));
      if (mark.label) {
        if (layout.small) {
          const right = px > plot.left + (plot.right - plot.left) * 0.66;
          group.append(textEl("peak-tag", right ? px - 7 : px + 7, py - 5, mark.label, right ? "end" : undefined));
        } else {
          const width = textWidth(mark.label) + 16;
          const left = px + 12 + width > plot.right ? px - 12 - width : px + 12;
          const box = svgEl("rect", { class: "peak-box", x: left, y: py - 15, width, height: 22, rx: 4 });
          const text = textEl("peak-label", left + 8, py, mark.label);
          group.append(box, text);
        }
      }
      out.push(group);
    } else if (mark.kind === "hline") {
      const py = axis.scale(mark.y);
      const group = svgEl("g", { class: `mark hline ${mark.cls ?? ""}`.trim(), "data-mark": mark.id });
      group.append(svgEl("line", { class: "peak-line ref", x1: plot.left, x2: plot.right, y1: py, y2: py }));
      if (mark.label) group.append(textEl("peak-tag", plot.right - 2, py - 4, mark.label, "end"));
      out.push(group);
    } else if (mark.kind === "vline") {
      const px = x.scale(mark.x);
      const from = Number.isFinite(mark.from) ? axis.scale(mark.from) : panel.top;
      const to = Number.isFinite(mark.to) ? axis.scale(mark.to) : panel.bottom;
      const group = svgEl("g", { class: "mark vline", "data-mark": mark.id });
      group.append(svgEl("line", { class: "mark-line", x1: px, x2: px, y1: from, y2: to + (mark.extend ?? 0) }));
      if (mark.label) group.append(textEl("note", px + 5, to + (mark.extend ?? 0) - 2, mark.label));
      out.push(group);
    } else if (mark.kind === "note") {
      const px = x.scale(mark.x);
      const py = axis.scale(mark.y);
      out.push(textEl(mark.cls ?? "note", px + (mark.dx ?? 0), py + (mark.dy ?? 0), mark.label, mark.anchor));
    }
  }
  return out;
}

/**
 * Fit the boxes of the peak labels to their measured texts (an attached SVG only).
 *
 * @param {SVGSVGElement} svg the drawn chart
 * @param {{right: number}} plot the plot area
 */
export function fitBoxes(svg, plot) {
  if (!svg.isConnected) return;
  for (const group of svg.querySelectorAll("g.mark.peak")) {
    const box = group.querySelector(".peak-box");
    const text = group.querySelector(".peak-label");
    const dot = group.querySelector(".peak-dot");
    if (!box || !text || !dot) continue;
    let width;
    try {
      width = text.getComputedTextLength() + 16;
    } catch {
      continue;
    }
    if (!(width > 16)) continue;
    const px = Number(dot.getAttribute("cx"));
    const left = px + 12 + width > plot.right ? px - 12 - width : px + 12;
    box.setAttribute("x", String(c1(left)));
    box.setAttribute("width", String(c1(width)));
    text.setAttribute("x", String(c1(left + 8)));
  }
}
