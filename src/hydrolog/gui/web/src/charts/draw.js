/**
 * Drawing a chart into a container with the DOM only (no Preact), so a kit
 * component can wrap it as `Chart` does (plan D9, D12).
 *
 * `drawChart(container, spec)` builds the SVG, the legend and the readout and
 * returns a handle: `update(spec)` redraws in place (the readout keeps its
 * position), `readout.show(index)` and `readout.hide()` move it, `destroy()`
 * empties the container. The theme switch needs no redraw: colours are classes.
 */

import { chartLayout, drawAxes, drawGrid } from "./axes.js";
import { CHART_TEXT, fill } from "./labels.js";
import { formatNumber, formatTime } from "./scale.js";
import { drawMarks, drawSeries, fitBoxes, seriesGeometry, valueAt } from "./series.js";
import { c1, htmlEl, svgEl, textEl } from "./svg.js";

/**
 * Format a readout value: the axis's `digits`, otherwise by magnitude.
 *
 * @param {number} value
 * @param {number} [digits]
 * @returns {string}
 */
export function readoutNumber(value, digits) {
  if (digits !== undefined) return formatNumber(value, digits);
  const size = Math.abs(value);
  return formatNumber(value, size >= 1000 ? 0 : size >= 100 ? 1 : size >= 1 || size === 0 ? 2 : 3);
}

function headingText(layout, x, spec) {
  const custom = spec.readout?.x;
  if (typeof custom === "function") return custom(x);
  const type = layout.x.scale.type;
  if (spec.x?.scale === "time") return fill(CHART_TEXT.readoutTime, { t: formatTime(x) });
  if (type === "gumbel") {
    const years = 100 / x;
    return fill(CHART_TEXT.readoutProbability, {
      p: readoutNumber(x, x >= 1 ? 1 : 2),
      T: readoutNumber(years, years >= 10 ? 0 : 1),
    });
  }
  return fill(CHART_TEXT.readoutValue, { label: spec.x?.short ?? "x", x: readoutNumber(x, spec.x?.digits) });
}

/**
 * The lines of the readout at an index of the master series.
 *
 * @param {object} spec the chart spec
 * @param {ReturnType<typeof chartLayout>} layout
 * @param {object[]} geometries from `seriesGeometry`
 * @param {object} master the geometry the readout steps over
 * @param {number} index an index of the master's points
 * @returns {{heading: string, at: number, rows: {id: string, cls: string, text: string, py: number | null}[]}}
 */
export function readoutAt(spec, layout, geometries, master, index) {
  const at = master.kind === "bars" ? (master.spans[index][0] + master.spans[index][1]) / 2 : master.px[index];
  const x = master.xs[index];
  const rows = [];
  for (const geometry of geometries) {
    if (geometry.series.readout === false) continue;
    const value =
      geometry === master
        ? master.values[index]
        : valueAt(geometry, master.kind === "bars" ? master.spans[index][0] : at);
    if (value === null || !Number.isFinite(value)) continue;
    const axisSpec = geometry.axis === "y2" ? layout.y2 : layout.y;
    const format = spec.readout?.value;
    const number =
      typeof format === "function"
        ? format(value, geometry.series)
        : readoutNumber(value, geometry.series.digits ?? axisSpec.digits);
    const unit = geometry.series.unit ?? axisSpec.unit;
    const label = geometry.series.label ?? geometry.series.id;
    const scale = axisSpec.scale;
    rows.push({
      id: geometry.series.id,
      cls: geometry.cls,
      kind: geometry.kind,
      text: `${label}: ${number}${unit ? `\u00a0${unit}` : ""}`,
      py: geometry.kind === "bars" ? null : scale(value),
    });
  }
  return { heading: headingText(layout, x, spec), at, rows };
}

function pickMaster(spec, geometries) {
  const wanted = spec.readout?.series;
  const usable = geometries.filter((geometry) => geometry.px.length && geometry.kind !== "hbars");
  if (wanted) return usable.find((geometry) => geometry.series.id === wanted) ?? null;
  return usable.find((geometry) => geometry.kind !== "bars") ?? usable[0] ?? null;
}

function legendItems(spec, geometries) {
  if (Array.isArray(spec.legend)) return spec.legend;
  return geometries
    .filter((geometry) => geometry.series.label && geometry.series.legend !== false)
    .map((geometry) => ({ label: geometry.series.label, kind: geometry.kind, cls: geometry.cls }));
}

function swatch(item) {
  if (item.kind === "bars" || item.kind === "hbars" || item.kind === "box") return htmlEl("i", { class: `sw ${item.cls ?? ""}`.trim() });
  if (item.kind === "points") return htmlEl("i", { class: "sw-dot" });
  if (item.kind === "rug") return htmlEl("i", { class: "sw-rug" });
  if (item.kind === "stroke") {
    const line = svgEl("line", { x1: 1, y1: 3, x2: 23, y2: 3 });
    return svgEl("svg", { class: `sw-stroke ${item.cls ?? ""}`.trim(), viewBox: "0 0 24 6", "aria-hidden": "true" }, [line]);
  }
  return htmlEl("i", { class: `sw-line ${item.cls ?? "s1"}` });
}

function drawLegend(spec, geometries) {
  const items = legendItems(spec, geometries);
  const legend = htmlEl("div", { class: "chart-legend" });
  for (const item of items) {
    if (item.kind === "text") legend.append(htmlEl("span", { class: "muted" }, [item.label]));
    else if (item.kind === "break") legend.append(htmlEl("span", { class: "legend-break", "aria-hidden": "true" }));
    else legend.append(htmlEl("span", {}, [swatch(item), item.label]));
  }
  return legend;
}

/** The ids of the frames' clip paths: one per chart, unique on the page. */
let clips = 0;

/** How far a series may spill over the frame [viewBox units]: a line or a point on an edge keeps its whole stroke. */
const SPILL = 4;

/**
 * The series of a chart cut at its frame: below an axis that starts at 0 (`niceDomain`),
 * above a fixed maximum, beyond a fixed end of the x axis.
 *
 * @param {string} id the id of the frame's clip path
 * @param {{left: number, right: number, top: number, bottom: number}} plot the frame
 * @param {SVGElement[]} nodes the drawn series
 * @returns {SVGElement[]} the clip path and the series within it
 */
function framed(id, plot, nodes) {
  const rect = svgEl("rect", {
    x: plot.left - SPILL,
    y: plot.top - SPILL,
    width: plot.right - plot.left + 2 * SPILL,
    height: plot.bottom - plot.top + 2 * SPILL,
  });
  return [svgEl("defs", {}, [svgEl("clipPath", { id }, [rect])]), svgEl("g", { class: "framed", "clip-path": `url(#${id})` }, nodes)];
}

/**
 * The first and the last index of the master's points within the frame's width (its points
 * are in the order of x), null when none is: the readout steps over these only.
 *
 * @param {object} master the geometry the readout steps over
 * @param {{left: number, right: number}} plot the frame
 * @returns {{first: number, last: number} | null}
 */
function withinFrame(master, plot) {
  let first = -1;
  let last = -1;
  master.px.forEach((x, at) => {
    const middle = master.kind === "bars" ? (master.spans[at][0] + master.spans[at][1]) / 2 : x;
    if (middle < plot.left - 0.5 || middle > plot.right + 0.5) return;
    if (first < 0) first = at;
    last = at;
  });
  return first < 0 ? null : { first, last };
}

/**
 * Draw a chart into a container.
 *
 * @param {HTMLElement} container it gets the class `chart` (and `wide` for a wide chart)
 * @param {object} spec the chart spec (see `chart.js`)
 * @returns {{
 *   svg: SVGSVGElement, update: (spec: object) => void, destroy: () => void,
 *   readout: {show: (index: number) => void, hide: () => void, index: () => number | null}
 * }}
 */
export function drawChart(container, spec) {
  container.classList.add("chart");
  const svg = svgEl("svg", { class: "chart-svg", role: "img", focusable: "false" });
  const legendSlot = htmlEl("div", { class: "chart-legend-slot" });
  const live = htmlEl("div", { class: "chart-sr", "aria-live": "polite" });
  container.append(svg, legendSlot, live);
  clips += 1;
  const clipId = `chart-frame-${clips}`;

  let current = spec;
  let layout;
  let geometries;
  let master = null;
  let shown = null;
  let index = null;
  let layer = null;

  function hide() {
    layer?.replaceChildren();
    layer?.setAttribute("visibility", "hidden");
    live.textContent = "";
  }

  function show(next) {
    if (!master || !layer) return;
    index = Math.max(shown.first, Math.min(shown.last, next));
    const reading = readoutAt(current, layout, geometries, master, index);
    const { plot } = layout;
    const top = layout.upper ? layout.upper.top : layout.main.top;
    layer.replaceChildren();
    layer.removeAttribute("visibility");
    layer.append(svgEl("line", { class: "readout-line", x1: reading.at, x2: reading.at, y1: top, y2: plot.bottom }));
    for (const row of reading.rows) {
      if (row.py === null) continue;
      layer.append(svgEl("circle", { class: `readout-dot ${row.cls}`, cx: reading.at, cy: row.py, r: 3.5 }));
    }
    const lines = [reading.heading, ...reading.rows.map((row) => row.text)];
    const size = layout.small ? 10 : 11;
    const lineHeight = size + 4;
    const width = Math.max(...lines.map((line) => line.length)) * size * 0.56 + 16;
    const height = lines.length * lineHeight + 8;
    // Right of the cursor when it fits, else left of it, never past the chart's left edge
    const right = reading.at + 10 + width <= plot.right;
    const left = right ? reading.at + 10 : Math.max(0, reading.at - 10 - width);
    const boxTop = top + 4;
    layer.append(svgEl("rect", { class: "readout-box", x: left, y: boxTop, width, height, rx: 4 }));
    lines.forEach((line, row) => {
      layer.append(textEl(row === 0 ? "readout-head" : "readout-text", left + 8, boxTop + 4 + lineHeight * (row + 1) - 4, line));
    });
    if (svg.isConnected) {
      const texts = [...layer.querySelectorAll("text")];
      try {
        const measured = Math.max(...texts.map((text) => text.getComputedTextLength())) + 16;
        if (measured > 16) {
          const box = layer.querySelector(".readout-box");
          const fitLeft = right ? reading.at + 10 : Math.max(0, reading.at - 10 - measured);
          box.setAttribute("width", String(c1(measured)));
          box.setAttribute("x", String(c1(fitLeft)));
          for (const text of texts) text.setAttribute("x", String(c1(fitLeft + 8)));
        }
      } catch {
        // an SVG without layout (display: none) keeps the estimate
      }
    }
    live.textContent = lines.join(" · ");
  }

  function render(nextSpec) {
    current = nextSpec;
    layout = chartLayout(current);
    geometries = seriesGeometry(current, layout);
    master = current.readout && !layout.band ? pickMaster(current, geometries) : null;
    shown = master ? withinFrame(master, layout.plot) : null;
    if (!shown) master = null;
    container.classList.toggle("wide", !layout.small);
    svg.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);
    if (current.title) svg.setAttribute("aria-label", current.title);
    else svg.removeAttribute("aria-label");
    if (current.labelledBy) svg.setAttribute("aria-labelledby", current.labelledBy);
    else svg.removeAttribute("aria-labelledby");
    if (master) {
      svg.setAttribute("tabindex", "0");
      svg.setAttribute("aria-description", CHART_TEXT.keysHint);
    } else {
      svg.removeAttribute("tabindex");
      svg.removeAttribute("aria-description");
    }
    layer = master ? svgEl("g", { class: "readout", visibility: "hidden" }) : null;
    svg.replaceChildren(
      ...drawGrid(layout),
      ...(layout.band ? drawSeries(geometries, layout) : framed(clipId, layout.plot, drawSeries(geometries, layout))),
      ...drawMarks(current.marks, layout),
      ...drawAxes(layout),
      ...(layer ? [layer] : []),
    );
    fitBoxes(svg, layout.plot);
    legendSlot.replaceChildren(...(current.legend ? [drawLegend(current, geometries)] : []));
    if (master && index !== null && document.activeElement === svg) show(index);
    else {
      if (!master || index === null || index < shown.first || index > shown.last) index = null;
      live.textContent = "";
    }
  }

  function nearest(clientX, clientY) {
    const matrix = svg.getScreenCTM();
    if (!matrix) return null;
    const point = new DOMPoint(clientX, clientY).matrixTransform(matrix.inverse());
    let best = shown.first;
    for (let at = shown.first; at <= shown.last; at += 1) {
      const middle = master.kind === "bars" ? (master.spans[at][0] + master.spans[at][1]) / 2 : master.px[at];
      const bestMiddle = master.kind === "bars" ? (master.spans[best][0] + master.spans[best][1]) / 2 : master.px[best];
      if (Math.abs(middle - point.x) < Math.abs(bestMiddle - point.x)) best = at;
    }
    return { index: best, x: point.x };
  }

  function onPointerMove(event) {
    if (!master) return;
    const found = nearest(event.clientX, event.clientY);
    if (!found || found.x < layout.plot.left - 8 || found.x > layout.plot.right + 8) {
      hide();
      return;
    }
    show(found.index);
  }

  function onPointerLeave() {
    if (document.activeElement !== svg) hide();
  }

  function onKeyDown(event) {
    if (!master) return;
    const { first, last } = shown;
    const step = event.shiftKey || event.key === "PageUp" || event.key === "PageDown" ? 10 : 1;
    const from = index ?? first;
    let next = null;
    if (event.key === "ArrowRight" || event.key === "ArrowUp" || event.key === "PageUp") next = index === null ? first : from + step;
    else if (event.key === "ArrowLeft" || event.key === "ArrowDown" || event.key === "PageDown") next = index === null ? last : from - step;
    else if (event.key === "Home") next = first;
    else if (event.key === "End") next = last;
    else if (event.key === "Escape") {
      index = null;
      hide();
      return;
    } else return;
    event.preventDefault();
    show(next);
  }

  function onFocus() {
    if (master && index !== null) show(index);
  }

  function onBlur() {
    hide();
  }

  svg.addEventListener("pointermove", onPointerMove);
  svg.addEventListener("pointerleave", onPointerLeave);
  svg.addEventListener("keydown", onKeyDown);
  svg.addEventListener("focus", onFocus);
  svg.addEventListener("blur", onBlur);
  render(spec);

  return {
    svg,
    update: render,
    destroy() {
      svg.removeEventListener("pointermove", onPointerMove);
      svg.removeEventListener("pointerleave", onPointerLeave);
      svg.removeEventListener("keydown", onKeyDown);
      svg.removeEventListener("focus", onFocus);
      svg.removeEventListener("blur", onBlur);
      container.replaceChildren();
      container.classList.remove("chart", "wide");
    },
    readout: {
      show,
      hide() {
        index = null;
        hide();
      },
      index: () => index,
    },
  };
}
