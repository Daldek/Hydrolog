// The chart of „Statystyka przepływów”: the probability plot on Gumbel paper (plan D12). The
// annual maxima are points at their empirical exceedance probability, each distribution a
// curve through the quantiles Hydrolog computed (a dense grid of return periods, else the
// periods of the run), the active one full and thick, the others dimmed, and the chosen
// quantile of the active one marked with guides to both axes. Probabilities are drawn in
// per cent.

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

/**
 * The spec of the probability plot.
 *
 * @param {{result: object, curves: object|null, chosen: number, active: string}} input the
 *   result of the run, the result of the run on the dense grid (null when it failed), the
 *   return period to mark and the name of the active distribution
 * @returns {object} the Chart spec
 */
export function probabilitySpec({ result, curves, chosen, active }) {
  const best = result.best_distribution;
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
    const name = fit.distribution_name;
    const isBest = name === best;
    let label = legendName(name);
    if (isBest) {
      label = typeof fit.aic === "number"
        ? t(texts.chart.best, { name: label, aic: num(fit.aic, 1) })
        : t(texts.chart.bestNoAic, { name: label });
    }
    const data = [];
    fit.exceedance_probabilities.forEach((p, index) => {
      const q = fit.quantiles[index];
      if (Number.isFinite(q) && Math.abs(q) <= top) data.push([p * 100, q]);
    });
    series.push({
      id: name,
      kind: "line",
      cls: `${DISTRIBUTION_CLASS[name] || "s4"} ${name === active ? "active" : "dim"}`,
      label,
      unit: "m³/s",
      digits: 1,
      data,
    });
  }
  const marks = [];
  const activeFit = result.distributions.find((fit) => fit.distribution_name === active);
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
