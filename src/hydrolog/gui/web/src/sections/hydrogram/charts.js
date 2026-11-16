// The chart specs of „Hydrogram zlewni” (plan D12, D13): the hyetograph hanging above the
// hydrograph on one time axis, the cumulative rainfall and effective rainfall with the
// initial abstraction, and the unit hydrograph the run convolved. Every value comes from
// the result of `hydrograph generate`; the browser only sums the series for display.

import { extent } from "../../charts/scale.js";
import { hmm, inputText, num } from "../../format.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";

/** The unit hydrograph is drawn until it falls below this share of its peak. */
const UH_TAIL_SHARE = 0.01;

/**
 * The index of the first step with effective rainfall.
 *
 * @param {number[]} effective the effective rainfall per step [mm]
 * @returns {number} the index, -1 when there is none
 */
function firstEffective(effective) {
  return (effective || []).findIndex((value) => value > 0);
}

/**
 * The index of the largest rainfall step (the first of equal ones).
 *
 * @param {number[]} rainfall the rainfall per step [mm]
 * @returns {number} the index, -1 for no steps
 */
function largestStep(rainfall) {
  let found = -1;
  (rainfall || []).forEach((value, index) => {
    if (found < 0 || value > rainfall[found]) found = index;
  });
  return found;
}

/**
 * Running sums of a series at the end of each step, from 0 at the start.
 *
 * @param {number[]} values the values per step
 * @param {number} step the time step [min]
 * @returns {Array<[number, number]>} [time, sum] pairs, one more than the steps
 */
export function cumulative(values, step) {
  const points = [[0, 0]];
  let sum = 0;
  (values || []).forEach((value, index) => {
    sum += value;
    points.push([(index + 1) * step, sum]);
  });
  return points;
}

/**
 * The hyetograph above the hydrograph (the mockup's main chart): P and Pe as bars hanging
 * from the top of the upper panel, Q as an area, the peak, the start of effective rainfall,
 * the largest rainfall step and, when Statystyka gave one, the reference discharge.
 *
 * @param {object} result the result of `hydrograph generate`
 * @param {{label: string, peak_m3s: number, source?: string}|null} [reference] the
 *   reference discharge (store "reference")
 * @returns {object} the chart spec
 */
export function mainSpec(result, reference = null) {
  const step = result.timestep_min;
  const rain = result.precipitation_mm || [];
  const effective = result.effective_precipitation_mm || [];
  const times = result.times_min || [];
  const flows = result.discharge_m3s || [];
  const marks = [
    {
      kind: "peak",
      x: result.time_to_peak_min,
      y: result.peak_discharge_m3s,
      label: t(texts.chart.peak, { q: num(result.peak_discharge_m3s, 2), time: hmm(result.time_to_peak_min) }),
    },
  ];
  const first = firstEffective(effective);
  if (first >= 0) {
    marks.push({
      kind: "vline",
      axis: "y2",
      x: first * step,
      extend: 8,
      label: t(texts.chart.peStart, { time: hmm(first * step), ia: num(result.initial_abstraction_mm, 1) }),
    });
  }
  const top = largestStep(rain);
  if (top >= 0 && rain[top] > 0) {
    marks.push({
      kind: "note",
      axis: "y2",
      x: (top + 1) * step,
      y: rain[top],
      dx: 6,
      dy: -4,
      label: t(texts.chart.pmax, {
        p: num(rain[top], 2),
        dt: inputText(step),
        from: hmm(top * step),
        to: hmm((top + 1) * step),
      }),
    });
  }
  const legend = [
    { kind: "bars", cls: "bar-p", label: texts.chart.p },
    { kind: "bars", cls: "bar-pe", label: texts.chart.pe },
    { kind: "area", cls: "s1", label: texts.chart.flow },
  ];
  if (reference && typeof reference.peak_m3s === "number") {
    const label = t(texts.chart.reference, { label: reference.label, q: num(reference.peak_m3s, 1) });
    marks.push({ kind: "hline", y: reference.peak_m3s, label });
    legend.push({ kind: "text", label: reference.source ? `${label} (${reference.source})` : label });
  }
  legend.push({ kind: "text", label: texts.chart.fromResult });
  return {
    title: texts.center.mainTitle,
    x: { label: texts.chart.time, scale: "time" },
    y: { label: texts.chart.q, unit: "m³/s" },
    y2: { label: t(texts.chart.rain, { dt: inputText(step) }), unit: "mm" },
    series: [
      { id: "p", kind: "bars", axis: "y2", cls: "bar-p", label: texts.chart.p, data: rain.map((value, index) => [index * step, value]) },
      {
        id: "pe",
        kind: "bars",
        axis: "y2",
        cls: "bar-pe",
        label: texts.chart.pe,
        data: effective.map((value, index) => [index * step, value]),
      },
      { id: "q", kind: "area", cls: "s1", label: texts.chart.flow, data: flows.map((value, index) => [times[index], value]) },
    ],
    marks,
    legend,
    readout: { series: "q" },
  };
}

/**
 * Rainfall and effective rainfall summed over the rainfall's steps, with the initial
 * abstraction Ia and the time effective rainfall starts.
 *
 * @param {object} result the result of `hydrograph generate`
 * @returns {object} the chart spec (small)
 */
export function cumulativeSpec(result) {
  const step = result.timestep_min;
  const rain = cumulative(result.precipitation_mm, step);
  const effective = cumulative(result.effective_precipitation_mm, step);
  const end = rain[rain.length - 1];
  const endEffective = effective[effective.length - 1];
  const ia = result.initial_abstraction_mm;
  const marks = [];
  if (typeof ia === "number") marks.push({ kind: "hline", y: ia, label: t(texts.chart.cumIa, { value: num(ia, 1) }) });
  const first = firstEffective(result.effective_precipitation_mm);
  if (first >= 0 && typeof ia === "number") {
    marks.push({ kind: "vline", x: first * step, from: ia, to: 0, label: hmm(first * step) });
  }
  marks.push(
    { kind: "note", cls: "peak-tag", x: end[0], y: end[1], dy: 14, dx: -2, anchor: "end", label: t(texts.chart.cumPTotal, { value: num(end[1], 1) }) },
    {
      kind: "note",
      cls: "peak-tag",
      x: endEffective[0],
      y: endEffective[1],
      dy: -6,
      dx: -2,
      anchor: "end",
      label: t(texts.chart.cumPeTotal, { value: num(endEffective[1], 1) }),
    },
  );
  return {
    size: "small",
    title: texts.center.cumTitle,
    x: { label: texts.chart.time, scale: "time" },
    y: { label: texts.chart.cumSum, unit: "mm" },
    series: [
      { id: "pe", kind: "area", cls: "s1", label: texts.chart.cumPe, data: effective },
      { id: "p", kind: "line", cls: "s4", label: texts.chart.cumP, data: rain },
    ],
    marks,
    legend: true,
    readout: { series: "p" },
  };
}

/**
 * The unit hydrograph the run convolved, until it falls below 1 % of its peak.
 *
 * @param {object} result the result of `hydrograph generate`
 * @returns {object|null} the chart spec (small), null without the UH's ordinates
 */
export function uhSpec(result) {
  const times = result.uh_times_min;
  const ordinates = result.uh_discharge_m3s_per_mm;
  if (!Array.isArray(times) || !Array.isArray(ordinates) || !ordinates.length) return null;
  const peak = result.uh_peak_discharge_m3s_per_mm;
  const floor = UH_TAIL_SHARE * (typeof peak === "number" ? peak : (extent(ordinates)?.[1] ?? 0));
  let last = 0;
  ordinates.forEach((value, index) => {
    if (value > floor) last = index;
  });
  const end = Math.min(ordinates.length - 1, last + 1);
  const marks = [];
  if (typeof peak === "number" && typeof result.uh_time_to_peak_min === "number") {
    marks.push({
      kind: "peak",
      x: result.uh_time_to_peak_min,
      y: peak,
      label: t(texts.chart.uhPeak, { qp: num(peak, 2), tp: hmm(result.uh_time_to_peak_min) }),
    });
  }
  return {
    size: "small",
    title: t(texts.center.uhTitle, { model: texts.uh.models[result.uh_model] || result.uh_model }),
    x: { label: texts.chart.time, scale: "time" },
    y: { label: texts.chart.uh, unit: "m³/s/mm" },
    series: [
      {
        id: "u",
        kind: "area",
        cls: "s1",
        label: texts.chart.uhSeries,
        data: ordinates.slice(0, end + 1).map((value, index) => [times[index], value]),
      },
    ],
    marks,
    legend: true,
    readout: true,
  };
}
