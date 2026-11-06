// The charts of „Statystyka przepływów”: the probability plot on Gumbel paper (plan D12), the
// probability density and the distribution function against Q (plan 2026-11-06, D3). The
// annual maxima are points at their empirical exceedance probability (on the density chart
// a rug on the Q axis), each distribution a curve through the quantiles and densities
// Hydrolog computed (a dense grid of return periods, else the periods of the run), the
// active one full and thick, the others dimmed, and on the probability plot the chosen
// quantile of the active one marked with guides to both axes (none for „brak”).
// Probabilities are drawn in per cent there; F = 1 − p is the only arithmetic of the browser.

import { extent } from "../../charts/scale.js";
import { num } from "../../format.js";
import { t } from "../../labels/common.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { DISTRIBUTION_CLASS, percentAt, quantileAt, shortNumber } from "./state.js";

/**
 * The name of a distribution in the chart's legend.
 *
 * @param {string} name the distribution's name in the result
 * @returns {string} the Polish name
 */
export function legendName(name) {
  return Object.hasOwn(texts.distributions, name) ? texts.distributions[name].legend : name;
}

/** The highest the plot frames, as a multiple of the largest annual maximum. */
const FRAME_LIMIT = 10;

/**
 * The top of the plot's frame: the largest annual maximum or the active distribution's
 * largest quantile of the run, at most ten times the largest maximum. A curve that leaves
 * the frame (a fit with a runaway tail on a short series) is cut where it does.
 *
 * @param {object} result the result of the run
 * @param {string} active the name of the active distribution
 * @returns {number} the top [m³/s]
 */
export function frameTop(result, active) {
  const largest = extent(result.empirical.values_sorted)?.[1] ?? 0;
  const fit = result.distributions.find((item) => item.distribution_name === active);
  const top = fit ? (extent(fit.quantiles)?.[1] ?? largest) : largest;
  return Math.min(Math.max(largest, top), largest * FRAME_LIMIT);
}

/** The smallest exceedance probability the density and distribution-function charts reach. */
const SHAPE_TAIL = 0.01;

/**
 * The top of the density and distribution-function charts: the largest annual maximum or the
 * active distribution's largest quantile of p ≥ 1% on the curves, within the probability
 * plot's frame. Further out the density lies on the axis and F is 1, so the body, where the
 * distributions differ, keeps the width.
 *
 * @param {object} result the result of the run
 * @param {object[]} fits the distributions drawn (of the curves' run, else of the result)
 * @param {string} active the name of the active distribution
 * @returns {number} the top [m³/s]
 */
function shapeTop(result, fits, active) {
  const largest = extent(result.empirical.values_sorted)?.[1] ?? 0;
  const fit = fits.find((item) => item.distribution_name === active);
  const body = fit ? fit.quantiles.filter((_, index) => fit.exceedance_probabilities[index] >= SHAPE_TAIL - 1e-9) : [];
  return Math.min(Math.max(largest, extent(body)?.[1] ?? largest), frameTop(result, active)) * 1.08;
}

/**
 * The spec of the probability plot.
 *
 * @param {{result: object, curves: object|null, chosen: number|null, active: string}} input
 *   the result of the run, the result of the run on the dense grid (null when it failed),
 *   the return period to mark (null: none) and the name of the active distribution
 * @returns {object} the Chart spec
 */
export function probabilitySpec({ result, curves, chosen, active }) {
  const fits = (curves || result).distributions || [];
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
    series.push(curve(fit, result, active, { unit: "m³/s", digits: 1, data }));
  }
  const marks = [];
  const activeFit = chosen === null ? null : result.distributions.find((fit) => fit.distribution_name === active);
  const q = activeFit ? quantileAt(activeFit, chosen) : null;
  const p = activeFit ? percentAt(activeFit, chosen) : null;
  if (q !== null && p !== null) {
    marks.push({
      kind: "peak",
      x: p,
      y: q,
      guides: "xy",
      cls: DISTRIBUTION_CLASS[active] || "s1",
      label: t(texts.chart.peak, { p: shortNumber(p), q: num(q, 1), name: legendName(active) }),
    });
  }
  return {
    title: texts.chart.title,
    x: { label: texts.chart.x, scale: "gumbel" },
    y: { label: texts.chart.y, unit: "m³/s" },
    series,
    marks,
    legend: true,
    readout: { series: active },
  };
}

/**
 * The series of a distribution's curve: its colour, active or dimmed, its legend label (the
 * best one with its AIC).
 *
 * @param {object} fit a distribution of the result (or of the curves' run)
 * @param {object} result the result of the run
 * @param {string} active the name of the active distribution
 * @param {{unit?: string, digits?: number, data: number[][]}} fields the rest of the series
 * @returns {object} the series
 */
function curve(fit, result, active, fields) {
  const name = fit.distribution_name;
  let label = legendName(name);
  if (name === result.best_distribution) {
    label = typeof fit.aic === "number"
      ? t(texts.chart.best, { name: label, aic: num(fit.aic, 1) })
      : t(texts.chart.bestNoAic, { name: label });
  }
  return {
    id: name,
    kind: "line",
    cls: `${DISTRIBUTION_CLASS[name] || "s4"} ${name === active ? "active" : "dim"}`,
    label,
    ...fields,
  };
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
 * The spec of the probability density chart: the density of every distribution against Q,
 * the annual maxima as a rug on the Q axis.
 *
 * @param {{result: object, curves: object|null, active: string}} input the result of the
 *   run, the result of the run on the dense grid (null when it failed) and the name of the
 *   active distribution
 * @returns {object} the Chart spec (small)
 */
export function densitySpec({ result, curves, active }) {
  const fits = (curves || result).distributions || [];
  const top = shapeTop(result, fits, active);
  const series = fits.map((fit) =>
    curve(fit, result, active, { data: againstQ(fit, top, (index) => (fit.densities || [])[index]) }),
  );
  series.push({ id: "maxima", kind: "rug", label: texts.chart.points, data: result.annual_maxima });
  return {
    size: "small",
    title: texts.shape.density,
    x: { label: texts.shape.x },
    y: { label: texts.shape.densityY, unit: texts.shape.densityUnit },
    series,
    legend: true,
    readout: { series: active, x: readoutQ, value: (value) => shortNumber(value) },
  };
}

/**
 * The spec of the distribution-function chart: F = 1 − p of every distribution against Q,
 * the annual maxima as points at their empirical F.
 *
 * @param {{result: object, curves: object|null, active: string}} input as for `densitySpec`
 * @returns {object} the Chart spec (small)
 */
export function distributionSpec({ result, curves, active }) {
  const fits = (curves || result).distributions || [];
  const top = shapeTop(result, fits, active);
  const series = fits.map((fit) =>
    curve(fit, result, active, { digits: 3, data: againstQ(fit, top, (index) => 1 - fit.exceedance_probabilities[index]) }),
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
    legend: true,
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
