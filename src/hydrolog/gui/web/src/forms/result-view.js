// The generic view of a hydrolog-result/1 envelope (plan D11): notices in Polish, scalars
// with units from their name suffixes, series as a chart and a table, tables of records,
// the targets of a plan and the JSON. The pure part (analyzeResult and the helpers) reads
// the envelope; the components show it, and each section's results panel puts them together.

import { Chart } from "../charts/chart.js";
import { auto, decimalsFor, hmm, num, plural } from "../format.js";
import { html, useMemo } from "../html.js";
import { common, t } from "../labels/common.js";
import { exportLabels } from "../labels/exports.js";
import { describeNotice, notices as noticeTexts } from "../labels/notices.js";
import { commandOptions, commandResultFields, resultFields, options as optionLabels } from "../labels/options.js";
import { results as texts } from "../labels/results.js";
import { NO_UNIT, fieldUnit } from "../labels/units.js";
import { richText } from "../controls/field.js";
import { DataTable } from "../ui/table.js";

/** The longest array shown in full in the JSON view. */
const JSON_FOLD = 8;

/**
 * The label of a result field: the GUI's Polish name, else none. A field named as an
 * option of the command that gave the result takes the command's own label of that
 * option first (`stats threshold-events`: `threshold` „Poziom progowy”), then the
 * command's own label of a result field (`stats regime`: `code`), then the shared ones.
 *
 * @param {string} key the field's name
 * @param {string|null} [command] the command of the result, e.g. "stats threshold-events"
 * @returns {string|null} the label
 */
export function fieldLabel(key, command = null) {
  for (const labels of [commandOptions, commandResultFields]) {
    const own = command && Object.hasOwn(labels, command) ? labels[command] : null;
    if (own && Object.hasOwn(own, key)) return own[key];
  }
  if (Object.hasOwn(resultFields, key)) return resultFields[key];
  if (Object.hasOwn(optionLabels, key)) return optionLabels[key];
  return null;
}

/**
 * Whether a key names a time axis: "times_min", "time_min", "uh_times_min".
 *
 * @param {string} key the field's name
 * @returns {boolean} true for a time in minutes or hours
 */
function isTimeKey(key) {
  return /(^|_)times?(_|$)/.test(key) && /_(min|h)$/.test(key);
}

/**
 * Top-level arrays that are the x axis of the arrays of their length, never a series
 * of their own: calendar months, exceedance percentages, durations, thresholds,
 * percentiles, the scales of SPI and the years of annual values.
 */
const AXES = [
  "months",
  "exceedance_percents",
  "curve_exceedance_percents",
  "durations_days",
  "thresholds_mm",
  "percentiles",
  "scales_months",
  "hydrological_years",
  "years",
];

/**
 * Whether an array lists years ("incomplete_years"): never a series, an axis only as
 * one of AXES.
 *
 * @param {string} name the field's name
 * @returns {boolean} true for a list of years
 */
function isYearList(name) {
  return /(^|_)years$/.test(name);
}

/** Calendar months in the order of a hydrological year (November to October). */
const HYDROLOGICAL_MONTHS = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

/**
 * Arrays without an axis of their own whose items are months, with the months' order:
 * the mean monthly volumes (November first) and the monthly normals of SPI (January
 * first).
 */
const MONTH_SERIES = {
  monthly_mean_volume_m3: HYDROLOGICAL_MONTHS,
  months_normal_mm: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
};

/** Arrays without an axis of their own whose items are the days of a hydrological year. */
const DAY_SERIES = ["cumulative_volume_m3", "mean_cumulative_volume_m3", "series_baseflow"];

/**
 * The x axis of a group of arrays of one length: a time, an array of AXES, else the
 * months or days its arrays are known to run over (an axis of no field of the result,
 * `implied`), else none.
 *
 * @param {object[]} group the arrays, each `{key, name, values}`
 * @param {object[]} ys the arrays drawn against it
 * @returns {object|null} the axis, `kind` "months" for calendar months
 */
function groupAxis(group, ys) {
  const time = group.find((array) => isTimeKey(array.name));
  if (time) return time;
  const listed = AXES.map((name) => group.find((array) => array.key === name)).find(Boolean);
  if (listed) return listed.name === "months" ? { ...listed, kind: "months" } : listed;
  if (!ys.length) return null;
  const months = ys.map((array) => MONTH_SERIES[array.name]);
  if (months[0] && months.every((order) => order === months[0]) && months[0].length === ys[0].values.length) {
    return { key: "month", name: "month", values: months[0], kind: "months", implied: true, label: texts.month };
  }
  if (ys.every((array) => DAY_SERIES.includes(array.name))) {
    return { key: "day", name: "day", values: ys[0].values.map((_, index) => index + 1), implied: true, label: texts.day };
  }
  return null;
}

/**
 * A field of a result as a row.
 *
 * @param {string} key the field's name
 * @param {unknown} value its value
 * @param {string|null} command the command of the result
 * @param {string|null} parameter the result's parameter ("Q", "H", "T")
 * @returns {{key: string, label: string|null, value: unknown, unit: string|null}} the row
 */
function row(key, value, command, parameter) {
  return { key, label: fieldLabel(key, command), value, unit: typeof value === "number" ? fieldUnit(key, command, parameter) : null };
}

/**
 * Whether a value is a scalar shown in a table (a number, a short text, a boolean).
 *
 * @param {unknown} value the value
 * @returns {boolean} true for a scalar
 */
function isScalar(value) {
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value === "boolean") return true;
  return typeof value === "string" && value.length <= 80;
}

/**
 * Read an envelope for display.
 *
 * @param {object|null} envelope a hydrolog-result/1 envelope
 * @returns {{schema: string|null, status: string|null, notices: object[], scalars: object[],
 *   objects: object[], series: object[], records: object[], files: object[],
 *   targets: object[]|null}} its parts: top-level scalars, nested objects of scalars, groups
 *   of numeric arrays of one length (each with its x axis when it has one: a time, months,
 *   days or another array of the result, see groupAxis; lists of years are neither),
 *   arrays of records, written files and the targets of a plan
 */
export function analyzeResult(envelope) {
  const empty = {
    schema: null,
    status: envelope ? envelope.status || null : null,
    notices: (envelope && envelope.notices) || [],
    scalars: [],
    objects: [],
    series: [],
    records: [],
    files: [],
    targets: null,
  };
  const result = envelope && envelope.result;
  if (!result || typeof result !== "object" || Array.isArray(result)) return empty;
  const command = envelope.command || null;
  const parameter = typeof result.parameter === "string" ? result.parameter : null;
  const found = { ...empty, schema: result.schema || null };
  if (Array.isArray(result.targets)) found.targets = result.targets;
  if (Array.isArray(result.files)) found.files = result.files;
  const arrays = [];
  const collect = (key, value, owner) => {
    if (Array.isArray(value) && value.length && value.every((item) => typeof item === "number")) {
      arrays.push({ key: owner ? `${owner}.${key}` : key, name: key, values: value });
      return true;
    }
    return false;
  };
  for (const [key, value] of Object.entries(result)) {
    if (key === "schema" || key === "files" || key === "targets" || value === null) continue;
    if (isScalar(value)) {
      found.scalars.push(row(key, value, command, parameter));
    } else if (collect(key, value, null)) {
      // a numeric array, grouped below
    } else if (Array.isArray(value) && value.length && value.every((item) => item && typeof item === "object" && !Array.isArray(item))) {
      const columns = [];
      for (const item of value) {
        for (const [name, cell] of Object.entries(item)) {
          if (isScalar(cell) && !columns.includes(name)) columns.push(name);
        }
      }
      if (columns.length) found.records.push({ key, label: fieldLabel(key, command), columns, rows: value });
    } else if (value && typeof value === "object" && !Array.isArray(value)) {
      const rows = [];
      for (const [name, item] of Object.entries(value)) {
        if (isScalar(item)) rows.push(row(name, item, command, parameter));
        else collect(name, item, key);
      }
      if (rows.length) found.objects.push({ key, label: fieldLabel(key, command), rows });
    }
  }
  const byLength = new Map();
  for (const array of arrays) {
    if (!byLength.has(array.values.length)) byLength.set(array.values.length, []);
    byLength.get(array.values.length).push(array);
  }
  for (const [length, group] of byLength) {
    const data = group.filter((array) => !isYearList(array.name) && !isTimeKey(array.name) && !AXES.includes(array.key));
    const axis = groupAxis(group, data);
    const ys = data.filter((array) => array !== axis);
    if (!ys.length) continue;
    const unit = (array) => fieldUnit(array.name, command, parameter);
    found.series.push({
      length,
      x: axis ? { label: fieldLabel(axis.name, command), unit: axis.implied ? null : unit(axis), ...axis } : null,
      ys: ys.map((array) => ({ ...array, label: fieldLabel(array.name, command), unit: unit(array) })),
    });
  }
  return found;
}

/**
 * The scalars shown as tiles: the fields named by `keys` ("lag_time_min",
 * "parameters.n"; a short text too, "mean_date"), else the first four numbers that are
 * not echoes of the inputs, those of the result itself before those of its nested objects.
 *
 * @param {object} analysis the result of analyzeResult
 * @param {object} [inputs] the envelope's inputs
 * @param {string[]|null} [keys] the fields to show, "<object>.<field>" inside an object
 * @returns {object[]} the rows of the tiles
 */
export function headline(analysis, inputs = {}, keys = null) {
  const top = analysis.scalars.map((item) => ({ ...item, path: item.key }));
  const nested = analysis.objects.flatMap((object) => object.rows.map((item) => ({ ...item, path: `${object.key}.${item.key}` })));
  if (keys && keys.length) {
    const all = [...top, ...nested].filter((item) => typeof item.value === "number" || typeof item.value === "string");
    return keys.map((key) => all.find((item) => item.path === key)).filter(Boolean);
  }
  const fresh = (item) => typeof item.value === "number" && !(Object.hasOwn(inputs || {}, item.key) && inputs[item.key] === item.value);
  return [...top.filter(fresh), ...nested.filter(fresh)].slice(0, 4);
}

/**
 * The decimals of a column of numbers: none for whole numbers, else five significant
 * digits of the largest.
 *
 * @param {number[]} values the column
 * @returns {number} the decimals
 */
function columnDecimals(values) {
  if (values.every((value) => Number.isInteger(value))) return 0;
  let largest = 0;
  for (const value of values) if (Math.abs(value) > largest) largest = Math.abs(value);
  return Math.min(6, decimalsFor(largest, 5));
}

/**
 * A group of series as CSV: comma separated, decimal dot, a header of field names.
 *
 * @param {object} group a group of analyzeResult's `series`
 * @returns {string} the CSV text
 */
function seriesCsv(group) {
  const columns = [group.x || { name: "index", values: Array.from({ length: group.length }, (_, index) => index + 1) }, ...group.ys];
  const lines = [columns.map((column) => column.name).join(",")];
  for (let index = 0; index < group.length; index += 1) {
    lines.push(columns.map((column) => String(column.values[index])).join(","));
  }
  return `${lines.join("\n")}\n`;
}

/**
 * A cell of a CSV file: quoted when it holds a comma, a quote or a line break.
 *
 * @param {unknown} value the value
 * @returns {string} the cell
 */
export function csvCell(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/**
 * A table of records as CSV.
 *
 * @param {{columns: string[], rows: object[]}} record a record table of analyzeResult
 * @returns {string} the CSV text
 */
function recordsCsv(record) {
  const lines = [record.columns.map(csvCell).join(",")];
  for (const item of record.rows) lines.push(record.columns.map((name) => csvCell(item[name])).join(","));
  return `${lines.join("\n")}\n`;
}

/**
 * The table of a result as CSV: its first group of series, else its first table of
 * records, else its scalars as name, value and unit.
 *
 * @param {object} analysis the result of analyzeResult
 * @returns {string} the CSV text
 */
export function resultCsv(analysis) {
  if (analysis.series.length) return seriesCsv(analysis.series[0]);
  if (analysis.records.length) return recordsCsv(analysis.records[0]);
  const rows = [
    ...analysis.scalars,
    ...analysis.objects.flatMap((object) => object.rows.map((item) => ({ ...item, key: `${object.key}.${item.key}` }))),
  ];
  const lines = ["name,value,unit", ...rows.map((item) => [item.key, item.value, item.unit || ""].map(csvCell).join(","))];
  return `${lines.join("\n")}\n`;
}

/**
 * A group of series as a Chart spec (charts/chart.js): lines against the time axis (in
 * hours), the months (one step each, named, in the group's order: November first in a
 * hydrological year), another axis of the group or the step.
 *
 * @param {object} group a group of analyzeResult's `series`
 * @param {{size?: string}} [how] the chart's size ("wide", the default, or "small")
 * @returns {object} the spec
 */
export function seriesChartSpec(group, how = {}) {
  const months = group.x && group.x.kind === "months" ? group.x.values : null;
  const steps = Array.from({ length: group.length }, (_, index) => index + 1);
  const xs = group.x && !months ? group.x.values : steps;
  const name = (array) => array.label || array.name;
  const time = Boolean(group.x) && group.x.unit === "min";
  const unit = group.ys[0].unit ? ` [${group.ys[0].unit}]` : "";
  let x = {
    label: time ? texts.timeAxis : group.x ? `${name(group.x)}${group.x.unit ? ` [${group.x.unit}]` : ""}` : texts.index,
    scale: time ? "time" : "linear",
  };
  if (months) {
    x = {
      label: texts.month,
      scale: "linear",
      min: 0.5,
      max: group.length + 0.5,
      labels: months.map((month, index) => ({ value: index + 1, label: texts.months[month - 1] })),
    };
  }
  return {
    x,
    y: { label: group.ys.length === 1 ? `${name(group.ys[0])}${unit}` : unit.trim() },
    series: group.ys.slice(0, 6).map((array) => ({
      id: array.key,
      kind: "line",
      data: xs.map((at, index) => [at, array.values[index]]),
      label: name(array),
    })),
    legend: group.ys.length > 1,
    readout: months ? { x: (at) => texts.monthNames[months[Math.round(at) - 1] - 1] } : true,
    size: how.size || "wide",
    title: group.ys.map(name).join(", "),
  };
}

/**
 * The notices of a result in Polish.
 *
 * @param {{notices: object[], empty?: boolean}} props the notices, and whether to say
 *   „Brak uwag” when there are none
 * @returns {object} the list
 */
export function Notices({ notices, empty = true }) {
  const items = notices || [];
  if (!items.length && !empty) return null;
  const icon = () => html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>`;
  return html`
    <ul class="notes">
      ${items.length
        ? items.map((notice) => {
            const level = notice.level === "warning" ? "warn" : "info";
            const { text } = describeNotice(notice);
            return html`<li class=${level} data-code=${notice.code}>
              ${icon()}
              <div><span class="lvl">${level === "warn" ? common.levels.warning : common.levels.info}</span> ${richText(text)}<span class="from">${common.from} · <code>${notice.code}</code></span></div>
            </li>`;
          })
        : html`<li class="info">${icon()}<div><span class="lvl">${common.levels.info}</span> ${noticeTexts.none}<span class="from">${common.from}</span></div></li>`}
    </ul>
  `;
}

/**
 * A value of a result for a person.
 *
 * @param {unknown} value the value
 * @returns {string} the text
 */
function shownValue(value) {
  if (typeof value === "number") return auto(value);
  if (typeof value === "boolean") return value ? common.yes : common.no;
  return String(value);
}

/**
 * The name of a row: its label with the field's name, or the name alone.
 *
 * @param {{key: string, label: string|null}} item the row
 * @returns {object} the cell's content
 */
function rowName(item) {
  return item.label ? html`${item.label}<span class="sym">${item.key}</span>` : html`<code>${item.key}</code>`;
}

/**
 * The name of a tile: the symbol the result gives its field (`labels` of
 * `stats characteristic`: "SWQ"), its short name, its label or its name.
 *
 * @param {object} item the row of the tile
 * @param {object} analysis the result of analyzeResult
 * @returns {string} the name
 */
function tileName(item, analysis) {
  const symbols = analysis.objects.find((object) => object.key === "labels");
  const symbol = item.path === item.key && symbols ? symbols.rows.find((row) => row.key === item.key) : null;
  if (symbol && typeof symbol.value === "string") return symbol.value;
  if (Object.hasOwn(texts.tiles, item.key)) return texts.tiles[item.key];
  return item.label || item.key;
}

/**
 * The tiles and the table of a result's scalars.
 *
 * @param {{analysis: object, inputs?: object, keys?: string[], showTiles?: boolean}} props
 *   the analysis, the inputs, the fields of the tiles (see headline) and whether to show
 *   the tiles at all
 * @returns {object|null} the summary
 */
export function ResultSummary({ analysis, inputs, keys, showTiles = true }) {
  const tiles = showTiles ? headline(analysis, inputs, keys) : [];
  const tables = [{ key: null, label: null, rows: analysis.scalars }, ...analysis.objects];
  if (!tiles.length && !analysis.scalars.length && !analysis.objects.length) return null;
  const codeName = (item) => (Object.hasOwn(texts.codes, item.path) ? texts.codes[item.path][item.value] || null : null);
  return html`
    ${tiles.length
      ? html`<div class="summary">
          ${tiles.map(
            (item, index) => html`<div class=${`kpi${index === tiles.length - 1 ? " hi" : ""}`} data-key=${item.path}>
              <div class="k" title=${item.label ? `${item.label} (${item.path})` : item.path}>${tileName(item, analysis)}</div>
              <div class="v">${typeof item.value === "number" ? auto(item.value) : item.value}${item.unit ? html` <span class="u">${item.unit}</span>` : null}</div>
              ${codeName(item) ? html`<div class="sub">${codeName(item)}</div>` : null}
            </div>`,
          )}
        </div>`
      : null}
    ${tables
      .filter((table) => table.rows.length)
      .map(
        (table) => html`
          ${table.key ? html`<h3 class="group-title">${table.label || table.key}</h3>` : null}
          <table class="params compact" data-object=${table.key || "result"}>
            <tbody>
              ${table.rows.map(
                (item) => html`<tr data-key=${item.key}>
                  <th>${rowName(item)}</th>
                  <td>${shownValue(item.value)}</td>
                  <td class="u">${typeof item.value === "number" ? item.unit || NO_UNIT : ""}</td>
                </tr>`,
              )}
            </tbody>
          </table>
        `,
      )}
  `;
}

/**
 * A group of series: the chart and the table.
 *
 * @param {{group: object, chart?: boolean, table?: boolean, svgRef?: object,
 *   size?: string, bare?: boolean}} props the group, whether to draw the chart and the
 *   table, a ref that receives the chart's SVG (for PNG), the chart's size, and a chart
 *   with a title instead of a card (the panel Wyniki)
 * @returns {object} the card or the chart
 */
export function ResultSeries({ group, chart = true, table = true, svgRef, size = "wide", bare = false }) {
  const spec = useMemo(() => seriesChartSpec(group, { size }), [group, size]);
  const name = (array) => array.label || array.name;
  const title = group.ys.map(name).join(", ");
  const sub = t(texts.seriesSub, {
    names: [group.x && !group.x.implied ? group.x : null, ...group.ys].filter(Boolean).map((array) => array.name).join(", "),
    rows: plural(group.length, texts.rowForms),
  });
  if (bare) {
    return html`
      <div class="result-chart">
        <div class="chart-title">${title} <span>${sub}</span></div>
        <${Chart} spec=${spec} svgRef=${svgRef} />
      </div>
    `;
  }
  const xs = group.x ? group.x.values : Array.from({ length: group.length }, (_, index) => index + 1);
  const months = group.x && group.x.kind === "months";
  let xLabel = texts.index;
  if (group.x) xLabel = group.x.implied ? group.x.label : html`<code>${group.x.name}</code>`;
  const columns = [
    {
      key: "x",
      label: xLabel,
      unit: group.x ? group.x.unit : null,
      format: months ? (value) => texts.monthNames[value - 1] : (value) => num(value, group.x ? columnDecimals(group.x.values) : 0),
    },
  ];
  if (group.x && group.x.unit === "min") {
    columns.push({ key: "x", label: texts.time, format: (value) => hmm(value), className: "t" });
  }
  for (const array of group.ys) {
    const digits = columnDecimals(array.values);
    columns.push({ key: array.key, label: html`<code>${array.name}</code>`, unit: array.unit, format: (value) => num(value, digits) });
  }
  const rows = xs.map((x, index) => {
    const item = { x };
    for (const array of group.ys) item[array.key] = array.values[index];
    return item;
  });
  return html`
    <div class="card result-series">
      <div class="card-head">
        <h3 class="card-title">${title}</h3>
        <span class="card-sub">${sub}</span>
      </div>
      ${chart ? html`<${Chart} spec=${spec} svgRef=${svgRef} />` : null}
      ${table ? html`<${DataTable} columns=${columns} rows=${rows} label=${title} />` : null}
    </div>
  `;
}

/**
 * Tables of records (arrays of objects) of a result.
 *
 * @param {{records: object[]}} props the records of analyzeResult
 * @returns {object[]} the cards
 */
export function ResultRecords({ records }) {
  return records.map((record) => {
    const columns = record.columns.map((name) => ({
      key: name,
      label: html`<code>${name}</code>`,
      unit: null,
      format: (value) => (value === undefined || value === null ? "–" : shownValue(value)),
    }));
    return html`
      <div class="card result-records" key=${record.key}>
        <div class="card-head">
          <h3 class="card-title">${record.label || record.key}</h3>
          <span class="card-sub">${t(texts.records, { name: record.key, rows: plural(record.rows.length, texts.rowForms) })}</span>
        </div>
        <${DataTable} columns=${columns} rows=${record.rows} label=${record.label || record.key} />
      </div>
    `;
  });
}

/**
 * The targets of a plan (`check`): each file and what the command would do.
 *
 * @param {{targets: Array<{option?: string, path: string, action: string}>}} props the targets
 * @returns {object} the card
 */
export function PlanTargets({ targets }) {
  const plan = exportLabels.plan;
  return html`
    <div class="card plan-targets">
      <div class="card-head">
        <h3 class="card-title">${plan.title}</h3>
        <span class="card-sub">${plan.sub}</span>
      </div>
      <${DataTable}
        tall=${false}
        label=${plan.title}
        columns=${[
          { key: "option", label: plan.option, format: (value) => value || "–" },
          { key: "path", label: plan.path, format: (value) => String(value).replace(/^(in|out)\//, "") },
          { key: "action", label: plan.action, format: (value) => plan.actions[value] || value },
        ]}
        rows=${targets}
        rowClass=${(item) => (item.action === "conflict" ? "conflict" : null)}
      />
    </div>
  `;
}

/**
 * A JSON value as a pretty text with long arrays folded („… razem 152 wartości”).
 *
 * @param {unknown} value the value
 * @param {string} [indent] the current indentation
 * @returns {Array<string|object>} children for htm
 */
function foldedJson(value, indent = "") {
  const inner = `${indent}  `;
  if (Array.isArray(value)) {
    if (!value.length) return ["[]"];
    const shown = value.length > JSON_FOLD ? value.slice(0, 4) : value;
    const parts = ["[\n"];
    shown.forEach((item, index) => {
      parts.push(inner, ...foldedJson(item, inner));
      if (index < shown.length - 1 || shown.length < value.length) parts.push(",");
      parts.push("\n");
    });
    if (shown.length < value.length) {
      parts.push(inner, html`<span class="fold">${t(texts.fold, { count: plural(value.length, texts.valueForms) })}</span>`, "\n");
    }
    parts.push(`${indent}]`);
    return parts;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value);
    if (!entries.length) return ["{}"];
    const parts = ["{\n"];
    entries.forEach(([key, item], index) => {
      parts.push(inner, html`<span class="k">${JSON.stringify(key)}</span>`, ": ", ...foldedJson(item, inner));
      if (index < entries.length - 1) parts.push(",");
      parts.push("\n");
    });
    parts.push(`${indent}}`);
    return parts;
  }
  return [JSON.stringify(value)];
}

/**
 * The envelope as JSON, long lists folded.
 *
 * @param {{envelope: object}} props the envelope
 * @returns {object} the card
 */
export function ResultJson({ envelope }) {
  const schema = (envelope && envelope.result && envelope.result.schema) || "";
  return html`
    <div class="card result-json">
      <div class="card-head">
        <h3 class="card-title">${texts.json}</h3>
        <span class="card-sub">${richText(t(texts.jsonSub, { envelope: `\`${envelope.schema}\``, schema: `\`${schema}\`` }))}</span>
      </div>
      <pre class="code json" tabindex="0">${foldedJson(envelope)}</pre>
    </div>
  `;
}
