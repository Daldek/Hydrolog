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
// both axes (none for „brak”). The axis ranges depend on the run alone (`axisRanges`), never
// on the combinations shown, ticked or active; a curve leaving a frame is clipped at it.
// Probabilities are drawn in per cent there; F = 1 − p is the only arithmetic of the browser.

import { extent, gumbelDomain, niceDomain } from "../../charts/scale.js";
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
 * Whether combinations name their methods (curves, rows, columns): more than one method is
 * among them, so a name tells them apart.
 *
 * @param {object[]} fits the combinations drawn or listed
 * @returns {boolean} whether they do
 */
export function namesMethods(fits) {
  return new Set(fits.map((fit) => fit.fit_method)).size > 1;
}

/** The highest a Q range reaches, as a multiple of the largest annual maximum. */
const FRAME_LIMIT = 10;

/** The smallest exceedance probability whose Q the density and distribution-function charts reach. */
const SHAPE_TAIL = 0.01;

/** The density's frame over the median of the combinations' largest densities. */
const DENSITY_HEADROOM = 1.25;

/**
 * The frame of the density and distribution-function charts, one under the other: as wide as
 * the probability plot's (the same text size at the same width), lower.
 */
const SHAPE_SIZE = { width: 760, height: 300 };

/**
 * The median of the finite values.
 *
 * @param {(number|null)[]} values the values (others than finite numbers are skipped)
 * @returns {number|null} the median, null when no value is finite
 */
function median(values) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

/**
 * A combination's Q at the rarest exceedance probability of at least `tail` on its grid (its
 * largest such quantile).
 *
 * @param {object} fit a combination of the result (or of the curves' run)
 * @param {number} tail the smallest exceedance probability counted (0: every one)
 * @returns {number|null} Q [m³/s], null when no finite quantile counts
 */
function quantileTo(fit, tail) {
  return extent(fit.quantiles.filter((_, index) => fit.exceedance_probabilities[index] >= tail - 1e-9))?.[1] ?? null;
}

/**
 * The automatic axis ranges of the three charts, the ones „Auto” restores when the person
 * set others (`axisLimits` of state.js). They depend on the run alone, every combination it
 * returned (of the curves' run on the dense grid, else of the result), never on the ones
 * shown, ticked or active: a filter or a click on a row moves no axis. The Gumbel axis of the
 * probability plot spans the probabilities of the run (its periods, the dense grid) and of
 * the annual maxima, given as return periods T = 100 / p. Every other range starts at 0 and
 * ends at the axis's own rounding (8% headroom; 7 ticks on y, 10 on x) of:
 * - Q of the density and distribution-function charts (x): the largest annual maximum or, if
 *   larger, the median over the combinations of Q at p = 1%;
 * - Q of the probability plot (y): the same at the rarest p of its curves (0,1% on the dense
 *   grid), so the curves reach its rare end;
 * - the density (y), without the headroom: 1,25 times the median of the largest densities
 *   within the Q range of the combinations with an AIC (of every combination when none has
 *   one). A combination without an AIC has a bound among the annual maxima, where its
 *   density often spikes (Weibull or Pearson III by most methods on a short series), and
 *   they can be half of them; the median sets aside the rest (a GEV near its bound by
 *   maximum likelihood). Such a spike is cut by the frame instead of flattening every other
 *   curve;
 * - F (y): 0 to 1, not settable.
 * The median keeps a runaway combination from setting a range; a Q range still ends at most
 * at ten times the largest annual maximum. Whatever leaves a frame is cut at it.
 *
 * @param {object} result the result of the run
 * @param {object|null} curves the result of the run on the dense grid, null when it failed
 * @returns {{probability: {t: [number, number], q: [number, number]}, density: {q: [number,
 *   number], f: [number, number]}, distribution: {q: [number, number]}}} per chart and
 *   axis (`AXES` of state.js) its range: T [years], Q [m³/s], the density [1/(m³/s)]
 */
export function axisRanges(result, curves) {
  const fits = (curves || result).distributions || [];
  const largest = extent(result.empirical.values_sorted)?.[1] ?? 0;
  const qTop = (tail, count) => {
    const typical = median(fits.map((fit) => quantileTo(fit, tail))) ?? largest;
    return niceDomain([0, Math.min(Math.max(largest, typical), largest * FRAME_LIMIT)], { count }).max;
  };
  const q = qTop(SHAPE_TAIL, 10);
  const covering = fits.filter((fit) => Number.isFinite(fit.aic));
  const peak = median(
    (covering.length ? covering : fits).map(
      (fit) => extent((fit.densities || []).filter((_, index) => fit.quantiles[index] >= 0 && fit.quantiles[index] <= q))?.[1] ?? null,
    ),
  );
  const grids = [...(result.distributions || []), ...(curves?.distributions || [])].flatMap((fit) => fit.exceedance_probabilities);
  const [left, right] = gumbelDomain([...grids, ...result.empirical.exceedance_prob].map((p) => p * 100));
  return {
    probability: { t: [100 / left, 100 / right], q: [0, qTop(0, 7)] },
    // Without a density (none computed) the frame is 0 to 1
    density: { q: [0, q], f: [0, peak > 0 ? niceDomain([0, DENSITY_HEADROOM * peak], { count: 7, pad: 0 }).max : 1] },
    distribution: { q: [0, q] },
  };
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
 *   methods: string[]}, chosen: number|null, active: string|null, ranges: object}} input
 *   the result of the run, the result of the run on the dense grid (null when it failed),
 *   the combinations shown, the return period to mark (null: none), the key of the active
 *   combination and the ranges drawn (`axisRanges`, with the person's limits)
 * @returns {object} the Chart spec
 */
export function probabilitySpec({ result, curves, shown, chosen, active, ranges }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const [shortest, longest] = ranges.probability.t;
  const [low, top] = ranges.probability.q;
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
    const data = fit.exceedance_probabilities.map((p, index) => [p * 100, fit.quantiles[index]]).filter(([, q]) => Number.isFinite(q));
    series.push(curve(fit, active, named, { unit: "m³/s", digits: 1, data: clipped(data, low, top) }));
  }
  const marks = [];
  const activeFit = chosen === null ? null : result.distributions.find((fit) => fitKey(fit) === active);
  const q = activeFit ? quantileAt(activeFit, chosen) : null;
  const p = activeFit ? percentAt(activeFit, chosen) : null;
  // A quantile beyond the frame is not marked: the tiles give it
  if (q !== null && p !== null && q >= low && q <= top && p <= 100 / shortest && p >= 100 / longest) {
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
    x: { label: texts.chart.x, scale: "gumbel", domain: [100 / shortest, 100 / longest] },
    y: { label: texts.chart.y, unit: "m³/s", min: low, max: top },
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
 * The points of a distribution's curve against Q: [Q, value at Q]. The chart cuts what lies
 * beyond its Q range.
 *
 * @param {object} fit a distribution of the result (or of the curves' run)
 * @param {(index: number) => number} value the value at an index of the quantiles
 * @returns {number[][]} the points
 */
function againstQ(fit, value) {
  const data = [];
  fit.quantiles.forEach((q, index) => {
    const y = value(index);
    if (Number.isFinite(q) && Number.isFinite(y)) data.push([q, y]);
  });
  return data;
}

/**
 * A curve clipped at its frame's range of values: its parts beyond end at the crossing of
 * the bound and leave a gap (a point without a value), so the readout reads nothing there
 * either.
 *
 * @param {number[][]} data the points [x, y] in the order drawn, with finite values
 * @param {number} low the lowest value shown
 * @param {number} top the highest value shown
 * @returns {number[][]} the points within the range, with the crossings and the gaps
 */
function clipped(data, low, top) {
  const out = [];
  data.forEach(([x, y], index) => {
    const previous = data[index - 1];
    if (previous) {
      const [px, py] = previous;
      const crossings = [low, top]
        .filter((bound) => (py - bound) * (y - bound) < 0)
        .map((bound) => [px + ((bound - py) / (y - py)) * (x - px), bound]);
      // From one bound to the other within a step: the nearer crossing first
      if (crossings.length === 2 && Math.abs(crossings[0][0] - px) > Math.abs(crossings[1][0] - px)) crossings.reverse();
      out.push(...crossings);
    }
    out.push(y >= low && y <= top ? [x, y] : [x, Number.NaN]);
  });
  return out;
}

/**
 * The series of a curve of a low chart (the density, the distribution function): with more
 * than one method drawn its readout reads the active curve only, as a row for each of up to
 * sixteen curves would not fit the low frame.
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
 * Q, the annual maxima as a rug on the Q axis, within the ranges drawn; a curve with a spike
 * above the frame is clipped at its top.
 *
 * @param {{result: object, curves: object|null, shown: {distributions: string[],
 *   methods: string[]}, active: string|null, ranges: object}} input the result of the run,
 *   the result of the run on the dense grid (null when it failed), the combinations shown,
 *   the key of the active one and the ranges drawn (as for `probabilitySpec`)
 * @returns {object} the Chart spec
 */
export function densitySpec({ result, curves, shown, active, ranges }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const [left, right] = ranges.density.q;
  const [low, top] = ranges.density.f;
  const series = fits.map((fit) =>
    smallCurve(fit, active, named, { data: clipped(againstQ(fit, (index) => (fit.densities || [])[index]), low, top) }),
  );
  series.push({ id: "maxima", kind: "rug", label: texts.chart.points, data: result.annual_maxima });
  return {
    size: SHAPE_SIZE,
    title: texts.shape.density,
    x: { label: texts.shape.x, min: left, max: right },
    y: { label: texts.shape.densityY, unit: texts.shape.densityUnit, min: low, max: top },
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
 *   methods: string[]}, active: string|null, ranges: object}} input as for `densitySpec`
 * @returns {object} the Chart spec
 */
export function distributionSpec({ result, curves, shown, active, ranges }) {
  const fits = shownFits((curves || result).distributions || [], shown);
  const named = namesMethods(fits);
  const [left, right] = ranges.distribution.q;
  const series = fits.map((fit) =>
    smallCurve(fit, active, named, { digits: 3, data: againstQ(fit, (index) => 1 - fit.exceedance_probabilities[index]) }),
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
    size: SHAPE_SIZE,
    title: texts.shape.distribution,
    x: { label: texts.shape.x, min: left, max: right },
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
