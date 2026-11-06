// The charts of „Statystyka przepływów”: the probability plot on Gumbel paper (plan D12), the
// probability density and the distribution function against Q (plan 2026-11-06, D3). The
// annual maxima are points at their empirical exceedance probability (on the density chart
// a rug on the Q axis), each combination of a distribution and a fit method shown a curve
// through the quantiles and densities Hydrolog computed (a dense grid of return periods,
// else the periods of the run): the distribution's colour, the method's line style (plan
// 2026-11-06, D7), the active one thick, the others dimmed; a legend keys the colours and
// the line styles, and a curve's name holds its method when more than one is drawn (the
// density and distribution-function charts then read the active curve only). On the
// probability plot the chosen quantile of the active combination is marked with guides to
// both axes (none for „brak”). The density chart is scaled to the active combination; the
// other curves are clipped at its frame.
// Probabilities are drawn in per cent there; F = 1 − p is the only arithmetic of the browser.

import { extent, niceDomain } from "../../charts/scale.js";
import { num } from "../../format.js";
import { t } from "../../labels/common.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { DISTRIBUTION_CLASS, DISTRIBUTIONS, FIT_METHODS, fitKey, METHOD_CLASS, percentAt, quantileAt, shortNumber, shownFits } from "./state.js";

/**
 * The name of a distribution in the chart's legend.
 *
 * @param {string} name the distribution's name in the result
 * @returns {string} the Polish name
 */
export function legendName(name) {
  return Object.hasOwn(texts.distributions, name) ? texts.distributions[name].legend : name;
}

/**
 * The name of a fit method in the name of a combination: „największa wiarygodność”.
 *
 * @param {string} method the method's name in the result
 * @returns {string} the Polish name
 */
export function methodName(method) {
  return Object.hasOwn(texts.fitMethods, method) ? texts.fitMethods[method].name : method;
}

/**
 * The name of a fit method in „Metody estymacji” and the legends: „Największa wiarygodność”.
 *
 * @param {string} method the method's name in the result
 * @returns {string} the Polish name
 */
export function methodLegend(method) {
  return Object.hasOwn(texts.fitMethods, method) ? texts.fitMethods[method].legend : method;
}

/**
 * The name of a curve on a chart: its distribution, and its method when the chart draws more
 * than one („Log-normalny, L-momenty”), so that the names tell the curves apart.
 *
 * @param {object} fit a combination of the result
 * @param {boolean} named whether the method is named
 * @returns {string} the name
 */
function curveName(fit, named) {
  const name = legendName(fit.distribution_name);
  return named ? t(texts.combination, { name, method: methodName(fit.fit_method) }) : name;
}

/**
 * Whether the curves of a chart name their methods: more than one method is drawn.
 *
 * @param {object[]} fits the combinations drawn
 * @returns {boolean} whether they do
 */
function namesMethods(fits) {
  return new Set(fits.map((fit) => fit.fit_method)).size > 1;
}

/** The highest the plot frames, as a multiple of the largest annual maximum. */
const FRAME_LIMIT = 10;

/**
 * The top of the plot's frame: the largest annual maximum or the active combination's
 * largest quantile of the run, at most ten times the largest maximum. A curve that leaves
 * the frame (a fit with a runaway tail on a short series) is cut where it does.
 *
 * @param {object} result the result of the run
 * @param {string|null} active the key of the active combination (fitKey), null for none
 * @returns {number} the top [m³/s]
 */
export function frameTop(result, active) {
  const largest = extent(result.empirical.values_sorted)?.[1] ?? 0;
  const fit = result.distributions.find((item) => fitKey(item) === active);
  const top = fit ? (extent(fit.quantiles)?.[1] ?? largest) : largest;
  return Math.min(Math.max(largest, top), largest * FRAME_LIMIT);
}

/** The smallest exceedance probability the density and distribution-function charts reach. */
const SHAPE_TAIL = 0.01;

/**
 * The top of the density and distribution-function charts: the largest annual maximum or the
 * active combination's largest quantile of p ≥ 1% on the curves, within the probability
 * plot's frame. Further out the density lies on the axis and F is 1, so the body, where the
 * distributions differ, keeps the width.
 *
 * @param {object} result the result of the run
 * @param {object[]} fits the combinations drawn (of the curves' run, else of the result)
 * @param {string|null} active the key of the active combination, null for none
 * @returns {number} the top [m³/s]
 */
function shapeTop(result, fits, active) {
  const largest = extent(result.empirical.values_sorted)?.[1] ?? 0;
  const fit = fits.find((item) => fitKey(item) === active);
  const body = fit ? fit.quantiles.filter((_, index) => fit.exceedance_probabilities[index] >= SHAPE_TAIL - 1e-9) : [];
  return Math.min(Math.max(largest, extent(body)?.[1] ?? largest), frameTop(result, active)) * 1.08;
}

/**
 * The legend of a chart: the annual maxima and a key of the colours (the distributions
 * drawn), then on a line of its own a key of the line styles (the fit methods drawn), not an
 * entry per curve.
 *
 * @param {object[]} fits the combinations drawn
 * @param {object} maxima the legend item of the annual maxima
 * @returns {object[]} the legend items
 */
function legendOf(fits, maxima) {
  const names = DISTRIBUTIONS.filter((name) => fits.some((fit) => fit.distribution_name === name));
  const methods = FIT_METHODS.filter((method) => fits.some((fit) => fit.fit_method === method));
  const items = [maxima];
  if (names.length) {
    items.push({ kind: "text", label: texts.chart.keyDistributions });
    for (const name of names) items.push({ kind: "stroke", cls: DISTRIBUTION_CLASS[name], label: legendName(name) });
  }
  if (methods.length) {
    items.push({ kind: "break" }, { kind: "text", label: texts.chart.keyMethods });
    for (const method of methods) items.push({ kind: "stroke", cls: METHOD_CLASS[method], label: methodLegend(method) });
  }
  return items;
}

/**
 * The spec of the probability plot.
 *
 * @param {{result: object, curves: object|null, shown: {distributions: string[],
 *   methods: string[]}, chosen: number|null, active: string|null}} input the result of the
 *   run, the result of the run on the dense grid (null when it failed), the combinations
 *   shown, the return period to mark (null: none) and the key of the active combination
 * @returns {object} the Chart spec
 */
export function probabilitySpec({ result, curves, shown, chosen, active }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const top = frameTop(result, active) * 1.08;
  const series = [
    {
      id: "maxima",
      kind: "points",
      label: texts.chart.points,
      unit: "m³/s",
      digits: 1,
      data: result.empirical.exceedance_prob.map((p, index) => [p * 100, result.empirical.values_sorted[index]]),
    },
  ];
  for (const fit of fits) {
    const data = [];
    fit.exceedance_probabilities.forEach((p, index) => {
      const q = fit.quantiles[index];
      if (Number.isFinite(q) && Math.abs(q) <= top) data.push([p * 100, q]);
    });
    series.push(curve(fit, active, named, { unit: "m³/s", digits: 1, data }));
  }
  const marks = [];
  const activeFit = chosen === null ? null : result.distributions.find((fit) => fitKey(fit) === active);
  const q = activeFit ? quantileAt(activeFit, chosen) : null;
  const p = activeFit ? percentAt(activeFit, chosen) : null;
  if (q !== null && p !== null) {
    marks.push({
      kind: "peak",
      x: p,
      y: q,
      guides: "xy",
      cls: DISTRIBUTION_CLASS[activeFit.distribution_name] || "s1",
      label: t(texts.chart.peak, { p: shortNumber(p), q: num(q, 1), name: curveName(activeFit, named) }),
    });
  }
  return {
    title: texts.chart.title,
    x: { label: texts.chart.x, scale: "gumbel" },
    y: { label: texts.chart.y, unit: "m³/s" },
    series,
    marks,
    legend: legendOf(fits, { kind: "points", label: texts.chart.points }),
    readout: { series: active },
  };
}

/**
 * The classes of a combination's line, on the charts and in its swatches: the distribution's
 * colour and the fit method's line style.
 *
 * @param {object} fit a combination of the result (or of the curves' run)
 * @returns {string} the classes
 */
export function curveClass(fit) {
  return [DISTRIBUTION_CLASS[fit.distribution_name] || "s4", METHOD_CLASS[fit.fit_method]].filter(Boolean).join(" ");
}

/**
 * The series of a combination's curve: its classes, active or dimmed, and its name.
 *
 * @param {object} fit a combination of the result (or of the curves' run)
 * @param {string|null} active the key of the active combination
 * @param {boolean} named whether its name holds the method (more than one drawn)
 * @param {{unit?: string, digits?: number, data: number[][], readout?: boolean}} fields the
 *   rest of the series
 * @returns {object} the series
 */
function curve(fit, active, named, fields) {
  const key = fitKey(fit);
  return { id: key, kind: "line", cls: `${curveClass(fit)} ${key === active ? "active" : "dim"}`, label: curveName(fit, named), ...fields };
}

/**
 * The points of a distribution's curve against Q within the plot's frame: [Q, value at Q].
 *
 * @param {object} fit a distribution of the result (or of the curves' run)
 * @param {number} top the top of the frame [m³/s]
 * @param {(index: number) => number} value the value at an index of the quantiles
 * @returns {number[][]} the points
 */
function againstQ(fit, top, value) {
  const data = [];
  fit.quantiles.forEach((q, index) => {
    const y = value(index);
    if (Number.isFinite(q) && Math.abs(q) <= top && Number.isFinite(y)) data.push([q, y]);
  });
  return data;
}

/**
 * A curve clipped at a ceiling: its parts above end at the crossing of the ceiling and
 * leave a gap (a point without a value), as if the frame cut them.
 *
 * @param {number[][]} data the points [x, y], in the order of x
 * @param {number} ceiling the highest value shown
 * @returns {number[][]} the points within the ceiling, with the crossings and the gaps
 */
function clipped(data, ceiling) {
  const out = [];
  data.forEach(([x, y], index) => {
    const previous = data[index - 1];
    if (previous && (previous[1] <= ceiling) !== (y <= ceiling)) {
      const [px, py] = previous;
      out.push([px + ((ceiling - py) / (y - py)) * (x - px), ceiling]);
    }
    out.push(y <= ceiling ? [x, y] : [x, Number.NaN]);
  });
  return out;
}

/**
 * The series of a curve of a small chart (the density, the distribution function): with more
 * than one method drawn its readout reads the active curve only, as a row for each of up to
 * sixteen curves would not fit the small frame.
 *
 * @param {object} fit a combination of the curves' run (or of the result)
 * @param {string|null} active the key of the active combination
 * @param {boolean} named whether more than one method is drawn
 * @param {{digits?: number, data: number[][]}} fields the rest of the series
 * @returns {object} the series
 */
function smallCurve(fit, active, named, fields) {
  return curve(fit, active, named, named && fitKey(fit) !== active ? { ...fields, readout: false } : fields);
}

/**
 * The spec of the probability density chart: the density of every combination shown against
 * Q, the annual maxima as a rug on the Q axis. The frame is the active combination's: its
 * largest density with the axis's headroom, so a curve with a spike (a GEV near its bound on
 * a short series) neither flattens it nor leaves the frame; such a curve is clipped at the
 * top.
 *
 * @param {{result: object, curves: object|null, shown: {distributions: string[],
 *   methods: string[]}, active: string|null}} input the result of the run, the result of
 *   the run on the dense grid (null when it failed), the combinations shown and the key of
 *   the active one
 * @returns {object} the Chart spec (small)
 */
export function densitySpec({ result, curves, shown, active }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const top = shapeTop(result, fits, active);
  const drawn = fits.map((fit) => ({ fit, data: againstQ(fit, top, (index) => (fit.densities || [])[index]) }));
  const own = drawn.find((item) => fitKey(item.fit) === active);
  const peak = own ? extent(own.data.map(([, y]) => y))?.[1] : undefined;
  // The axis's own rounding of a small chart (5 ticks, 8% headroom), fixed as its top
  const ceiling = peak === undefined ? undefined : niceDomain([0, peak], { count: 5 }).max;
  const series = drawn.map(({ fit, data }) => smallCurve(fit, active, named, { data: ceiling === undefined ? data : clipped(data, ceiling) }));
  series.push({ id: "maxima", kind: "rug", label: texts.chart.points, data: result.annual_maxima });
  return {
    size: "small",
    title: texts.shape.density,
    x: { label: texts.shape.x },
    y: { label: texts.shape.densityY, unit: texts.shape.densityUnit, ...(ceiling === undefined ? {} : { max: ceiling }) },
    series,
    legend: legendOf(fits, { kind: "rug", label: texts.chart.points }),
    readout: { series: active, x: readoutQ, value: (value) => shortNumber(value) },
  };
}

/**
 * The spec of the distribution-function chart: F = 1 − p of every combination shown against
 * Q, the annual maxima as points at their empirical F.
 *
 * @param {{result: object, curves: object|null, shown: {distributions: string[],
 *   methods: string[]}, active: string|null}} input as for `densitySpec`
 * @returns {object} the Chart spec (small)
 */
export function distributionSpec({ result, curves, shown, active }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const top = shapeTop(result, fits, active);
  const series = fits.map((fit) =>
    smallCurve(fit, active, named, { digits: 3, data: againstQ(fit, top, (index) => 1 - fit.exceedance_probabilities[index]) }),
  );
  const { values_sorted: values, exceedance_prob: exceedance } = result.empirical;
  series.push({
    id: "maxima",
    kind: "points",
    label: texts.chart.points,
    digits: 3,
    data: values.map((q, index) => [q, 1 - exceedance[index]]),
  });
  return {
    size: "small",
    title: texts.shape.distribution,
    x: { label: texts.shape.x },
    y: { label: texts.shape.distributionY, min: 0, max: 1 },
    series,
    legend: legendOf(fits, { kind: "points", label: texts.chart.points }),
    readout: { series: active, x: readoutQ },
  };
}

/**
 * The readout heading of the density and distribution-function charts: „Q = 122,1 m³/s”.
 *
 * @param {number} q the flow under the cursor [m³/s]
 * @returns {string} the heading
 */
function readoutQ(q) {
  return t(texts.shape.readout, { q: num(q, 1) });
}
