/**
 * The layout of a chart and its axes.
 *
 * `chartLayout(spec)` is pure: from a chart spec (see `chart.js`) it computes
 * the viewBox, the plot area, the panels (the second axis `y2` is a panel above
 * the main one, its bars hanging from the top, sharing the x axis: a
 * hyetograph above a hydrograph) and each axis's scale and ticks.
 * `drawGrid` and `drawAxes` turn a layout into SVG elements.
 */

import { CHART_TEXT } from "./labels.js";
import {
  gumbelDomain,
  gumbelScale,
  gumbelTicks,
  linearScale,
  logDomain,
  logScale,
  logTicks,
  niceDomain,
  timeDomain,
} from "./scale.js";
import { svgEl, textEl } from "./svg.js";

/** The sizes of the viewBox: the mockup's wide chart and its small one. */
export const SIZES = {
  wide: { width: 760, height: 432 },
  small: { width: 360, height: 178 },
};

/** The gap between the y2 panel and the main panel [viewBox units]. */
const PANEL_GAP = 28;

/**
 * Return a series' points as `{x, y, cls?, label?, sub?, text?}` objects.
 *
 * @param {object} series a series of the spec; `data` holds `[x, y]` pairs, objects or (a
 *   rug) bare x values
 * @returns {{x: number | string, y: number | string, cls?: string, label?: string, sub?: string, text?: string}[]}
 */
export function points(series) {
  return (series.data ?? []).map((datum) => {
    if (Array.isArray(datum)) return { x: datum[0], y: datum[1] };
    return typeof datum === "number" ? { x: datum } : { ...datum };
  });
}

/**
 * Return the width of a bar series in x units: its `width`, otherwise the
 * smallest spacing of its x values (1 for a single bar).
 *
 * @param {object} series a series of kind "bars"
 * @param {{x: number}[]} [data] its points
 * @returns {number}
 */
export function barWidth(series, data = points(series)) {
  if (series.width > 0) return series.width;
  let width = Infinity;
  for (let i = 1; i < data.length; i += 1) {
    const step = Math.abs(data[i].x - data[i - 1].x);
    if (step > 0) width = Math.min(width, step);
  }
  return Number.isFinite(width) ? width : 1;
}

function isBand(spec) {
  return spec.y?.scale === "band";
}

function sizeOf(spec) {
  if (spec.size && typeof spec.size === "object") return { ...spec.size, small: spec.size.width < 500 };
  const name = spec.size === "small" ? "small" : "wide";
  return { ...SIZES[name], small: name === "small" };
}

function labelWidth(labels) {
  const longest = Math.max(0, ...labels.map((label) => String(label).length));
  return 14 + 6.5 * longest;
}

/** Values of the x and y axes over the series and the marks. */
function extents(spec, band) {
  const xs = [];
  const ys = { y: [], y2: [] };
  for (const series of spec.series ?? []) {
    const axis = series.axis === "y2" ? "y2" : "y";
    const data = points(series);
    if (band) {
      for (const point of data) xs.push(point.x);
      continue;
    }
    const width = series.kind === "bars" ? barWidth(series, data) : 0;
    for (const point of data) {
      xs.push(point.x);
      if (width) xs.push(point.x + (series.align === "center" ? width / 2 : width));
      if (series.kind === "bars" && series.align === "center") xs.push(point.x - width / 2);
      if (series.kind !== "rug") ys[axis].push(point.y);
    }
  }
  for (const mark of spec.marks ?? []) {
    const axis = mark.axis === "y2" ? "y2" : "y";
    if (Number.isFinite(mark.x) && mark.kind !== "hline") xs.push(mark.x);
    if (Number.isFinite(mark.y) && mark.kind !== "vline") ys[axis].push(mark.y);
  }
  return { xs, ys };
}

function yAxis(axisSpec, values, range, count) {
  const options = axisSpec ?? {};
  if (options.scale === "log") {
    const domain =
      options.min !== undefined && options.max !== undefined
        ? { min: options.min, max: options.max, ticks: logTicks(options.min, options.max) }
        : logDomain(values);
    return { ...domain, scale: logScale([domain.min, domain.max], range) };
  }
  const domain = niceDomain(values, {
    count: options.ticks ?? count,
    zero: options.zero ?? true,
    pad: options.pad ?? 0.08,
    min: options.min,
    max: options.max,
  });
  return { ...domain, scale: linearScale([domain.min, domain.max], range) };
}

function xAxis(axisSpec, values, range, small) {
  const options = axisSpec ?? {};
  const kind = options.scale ?? "linear";
  if (kind === "time") {
    const domain = timeDomain(values, { min: options.min, max: options.max, count: small ? 8 : 13 });
    return { ...domain, scale: linearScale([domain.min, domain.max], range) };
  }
  if (kind === "gumbel") {
    const [left, right] = options.domain ?? gumbelDomain(values);
    const scale = gumbelScale([left, right], range);
    return { min: left, max: right, ticks: gumbelTicks(scale, small ? 26 : 30), scale };
  }
  if (kind === "log") {
    const domain =
      options.min !== undefined && options.max !== undefined
        ? { min: options.min, max: options.max, ticks: logTicks(options.min, options.max) }
        : logDomain(values);
    return { ...domain, scale: logScale([domain.min, domain.max], range) };
  }
  const domain = niceDomain(values, {
    count: options.ticks ?? (small ? 6 : 10),
    zero: options.zero ?? false,
    pad: options.pad ?? 0,
    min: options.min,
    max: options.max,
  });
  return { ...domain, scale: linearScale([domain.min, domain.max], range) };
}

/**
 * Compute the layout of a chart.
 *
 * @param {object} spec the chart spec (see `chart.js`)
 * @returns {{
 *   width: number, height: number, small: boolean, band: boolean,
 *   plot: {left: number, right: number, top: number, bottom: number},
 *   main: {top: number, bottom: number}, upper: {top: number, bottom: number} | null,
 *   x: object, y: object, y2: object | null, categories: object[] | null
 * }} the axes carry `scale`, `ticks`, `min`, `max` and their spec (`label`, `unit`, …)
 */
export function chartLayout(spec) {
  const { width, height, small } = sizeOf(spec);
  const band = isBand(spec);
  const gumbel = spec.x?.scale === "gumbel";
  const top = small ? 16 : 26;
  const bottom = height - (gumbel ? 60 : small ? 28 : 38);
  const { xs, ys } = extents(spec, band);

  if (band) {
    const categories = [];
    for (const series of spec.series ?? []) for (const point of points(series)) categories.push(point);
    const left = spec.y.width ?? 160;
    const right = width - (small ? 10 : 16);
    const x = xAxis({ zero: true, pad: 0.3, ...spec.x }, xs, [left, right], small);
    const rows = Math.max(1, categories.length);
    const step = (bottom - top) / rows;
    return {
      width,
      height,
      small,
      band,
      plot: { left, right, top, bottom },
      main: { top, bottom },
      upper: null,
      x: { ...spec.x, ...x },
      y: { ...spec.y, step, bar: Math.min(24, step * 0.6) },
      y2: null,
      categories,
    };
  }

  const right = width - (small ? 10 : 16);
  let main = { top, bottom };
  let upper = null;
  if (spec.y2) {
    const share = spec.y2.share ?? 0.27;
    const upperBottom = top + (bottom - top - PANEL_GAP) * share;
    upper = { top, bottom: upperBottom };
    main = { top: upperBottom + PANEL_GAP, bottom };
  }
  const y = yAxis(spec.y, ys.y, [main.bottom, main.top], small ? 5 : 7);
  const y2 = spec.y2 ? yAxis(spec.y2, ys.y2, [upper.top, upper.bottom], 4) : null;
  const tickLabels = [...y.ticks, ...(y2 ? y2.ticks : [])].map((tick) => tick.label);
  const base = gumbel ? 64 : small ? 40 : 56;
  const left = Math.max(base, labelWidth(tickLabels));
  const x = xAxis(spec.x, xs, [left, right], small);
  return {
    width,
    height,
    small,
    band,
    plot: { left, right, top, bottom },
    main,
    upper,
    x: { ...spec.x, ...x },
    y: { ...spec.y, ...y },
    y2: y2 ? { ...spec.y2, ...y2 } : null,
    categories: null,
  };
}

function hLines(values, left, right) {
  return values.map((at) => svgEl("line", { x1: left, x2: right, y1: at, y2: at }));
}

/**
 * Draw the grid: a horizontal line at each y tick of each panel and a dashed
 * vertical line at each x tick across the panels.
 *
 * @param {ReturnType<typeof chartLayout>} layout
 * @returns {SVGGElement[]} the grid groups
 */
export function drawGrid(layout) {
  const { plot, x, y, y2, band } = layout;
  const groups = [];
  if (!band) {
    const at = [...y.ticks.map((tick) => y.scale(tick.value))];
    if (y2) at.push(...y2.ticks.map((tick) => y2.scale(tick.value)));
    groups.push(svgEl("g", { class: "grid" }, hLines(at, plot.left, plot.right)));
  }
  const vertical = x.ticks
    .filter((tick) => !band || tick.value !== x.min)
    .map((tick) => {
      const at = x.scale(tick.value);
      return svgEl("line", { x1: at, x2: at, y1: plot.top, y2: plot.bottom });
    });
  groups.push(svgEl("g", { class: "grid v" }, vertical));
  return groups;
}

/**
 * Draw the axis lines, the tick labels and the axis labels.
 *
 * @param {ReturnType<typeof chartLayout>} layout
 * @returns {SVGElement[]}
 */
export function drawAxes(layout) {
  const { plot, main, upper, x, y, y2, small, band, categories } = layout;
  const out = [];
  const tickY = plot.bottom + (small ? 14 : 15);
  if (band) {
    out.push(svgEl("line", { class: "axis", x1: plot.left, x2: plot.left, y1: plot.top, y2: plot.bottom }));
    categories.forEach((category, index) => {
      const middle = plot.top + y.step * (index + 0.5);
      const name = textEl("bar-name", plot.left - 10, category.sub ? middle - 2 : middle + 4, String(category.y), "end");
      out.push(name);
      if (category.sub) out.push(textEl("bar-sub", plot.left - 10, middle + 12, category.sub, "end"));
    });
  } else {
    out.push(svgEl("line", { class: "axis", x1: plot.left, x2: plot.right, y1: main.bottom, y2: main.bottom }));
    if (upper) out.push(svgEl("line", { class: "axis", x1: plot.left, x2: plot.right, y1: upper.top, y2: upper.top }));
    for (const tick of y.ticks) out.push(textEl("tick", plot.left - 6, y.scale(tick.value) + 3, tick.label, "end"));
    if (y2) for (const tick of y2.ticks) out.push(textEl("tick", plot.left - 6, y2.scale(tick.value) + 3, tick.label, "end"));
  }
  for (const tick of x.ticks) {
    out.push(textEl("tick", x.scale(tick.value), tickY, tick.label, "middle"));
    if (tick.sub !== undefined) out.push(textEl("tick sub", x.scale(tick.value), tickY + 13, tick.sub, "middle"));
  }
  if (x.scale.type === "gumbel") {
    out.push(textEl("axis-label", plot.left - 6, tickY, CHART_TEXT.probability, "end"));
    out.push(textEl("axis-label", plot.left - 6, tickY + 13, CHART_TEXT.returnPeriod, "end"));
    if (x.label) out.push(textEl("axis-label", plot.right, tickY + 31, x.label, "end"));
  } else if (x.label) {
    out.push(textEl("axis-label", plot.right, tickY + (small ? 13 : 17), x.label, "end"));
  }
  const labelY = small ? 8 : 14;
  if (y2) {
    if (y2.label) out.push(textEl("axis-label", 4, labelY, y2.label));
    if (y.label) out.push(textEl("axis-label", 4, main.top - 8, y.label));
  } else if (y.label && !band) {
    out.push(textEl("axis-label", 4, labelY, y.label));
  }
  return out;
}
