// State of „Statystyka przepływów”: the inputs of `stats flood-frequency` kept in the browser
// under "hydrolog-gui/statystyka/2" (the form's values, the source and the return period
// highlighted in the results, null for „brak”; no results); the columns of the chosen file,
// read in the browser from its header; the ranking of the annual maxima for display; and
// the options of `stats homogeneity` for the same series. A first visit starts empty: no
// file, no values, no highlighted period. The version stayed 2 when „brak” came
// (2026-11-06): null is one more value of the same field, and a stored 100 (the former first
// value, not told apart from a 100 chosen) stays highlighted until the person picks „brak”
// or „Wyczyść” clears the inputs.

import { api } from "../../api.js";
import { num, parseNumber } from "../../format.js";
import { useEffect, useState } from "../../html.js";
import { readTable } from "../../controls/series-field.js";
import { describeError } from "../../labels/errors.js";
import { ONE_OF_KEY, parseSeries } from "../../forms/model.js";

/** The key of the section's inputs and its run channel. */
export const SECTION = "statystyka";

/** The command of the section. */
export const COMMAND = "stats flood-frequency";

/**
 * Exceedance probabilities p [%] of the curves: every 1% from 99% to 2% (smooth densities
 * in the body, about the mode) and finer steps at both ends, to 99,5% and 0,1%.
 */
const CURVE_PERCENTS = [
  99.5,
  ...Array.from({ length: 98 }, (_, index) => 99 - index),
  1.5, 1, 0.7, 0.5, 0.3, 0.2, 0.1,
];

/**
 * Return periods [years] of the curves of the three charts: a second run of the same series
 * gives the quantiles of every distribution with their densities on this grid, from p 99,5%
 * to 0,1% (T = 100 / p), so the curves span the empirical points; the tables show the
 * periods the person chose.
 */
export const CURVE_PERIODS = Object.freeze(CURVE_PERCENTS.map((p) => 100 / p));

/** The run channel of the curves (a channel of its own: it must not supersede the run). */
export const CURVES_CHANNEL = "statystyka-krzywe";

/** The command of the panel „Jednorodność ciągu”: the homogeneity tests of the series. */
export const HOMOGENEITY = "stats homogeneity";

/** The run channel of the homogeneity tests (its own: it must not supersede the run). */
export const HOMOGENEITY_CHANNEL = "statystyka-jednorodnosc";

/** The options of the series that `stats homogeneity` shares with the section's command. */
const SERIES_OPTIONS = ["values", "input_file", "value_column", "date_column"];

/** The period stressed when the chosen one is not among the periods: T = 100 years, p 1%. */
const FALLBACK_PERIOD = 100;

/** The series classes of the distributions: one colour each, whichever is best. */
export const DISTRIBUTION_CLASS = Object.freeze({ gev: "s1", log_normal: "s2", pearson3: "s3", weibull: "s6" });

/**
 * The inputs of a first visit: no series yet, all four distributions, no highlighted
 * period („brak”); the return periods are the catalog's default, set when the command's
 * entry arrives. `fit_method` is absent until the person picks one: the field shows the
 * catalog's default (`mle`), the run sends nothing for it, and inputs stored before it
 * existed keep their version.
 *
 * @returns {{source: "file"|"paste", values: object, chosen: number|null}} the state
 */
export function initialState() {
  return {
    source: "file",
    values: {
      input_file: "",
      value_column: "",
      date_column: "",
      values: "",
      distribution: "all",
    },
    chosen: null,
  };
}

/**
 * A number for a label, with at most `significant` significant digits and no trailing
 * zeros: shortNumber(1) gives "1", shortNumber(0.2) "0,2", shortNumber(3.3333) "3,33".
 *
 * @param {number} value the number
 * @param {number} [significant=3] significant digits
 * @returns {string} the text
 */
export function shortNumber(value, significant = 3) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "–";
  const rounded = Number(value.toPrecision(significant));
  const decimals = (String(rounded).split(".")[1] || "").length;
  return num(rounded, decimals);
}

/**
 * The return periods of the form, as numbers (empty when the text does not parse).
 *
 * @param {string|undefined} text the series text of `return_periods`
 * @returns {number[]} the periods in the order given
 */
export function periodsOf(text) {
  const parsed = parseSeries(text || "");
  return parsed.bad ? [] : parsed.values;
}

/**
 * The return period the results stress: none for „brak” (null chosen), else the one chosen
 * when the periods hold it, else 100 years, else the longest period.
 *
 * @param {number[]} periods the return periods
 * @param {number|null} chosen the period chosen, null for „brak”
 * @returns {number|null} the period, null for „brak” or without periods
 */
export function stressedPeriod(periods, chosen) {
  if (chosen === null || chosen === undefined || !periods.length) return null;
  if (periods.includes(chosen)) return chosen;
  if (periods.includes(FALLBACK_PERIOD)) return FALLBACK_PERIOD;
  return Math.max(...periods);
}

/**
 * The second return period of the tiles and the table: 10 years, else the first other one.
 *
 * @param {number[]} periods the return periods
 * @param {number|null} stressed the stressed period
 * @returns {number|null} the period, null when there is no other
 */
export function secondPeriod(periods, stressed) {
  if (periods.includes(10) && stressed !== 10) return 10;
  return periods.find((period) => period !== stressed) ?? null;
}

/**
 * The index of the catalog's `one_of` group that reads a file.
 *
 * @param {object} model the result of fieldModel
 * @returns {number} the index (the file group: the one holding `input_file`)
 */
export function fileGroup(model) {
  const found = model && model.oneOf ? model.oneOf.groups.findIndex((group) => group.members.includes("input_file")) : -1;
  return found < 0 ? 0 : found;
}

/**
 * The values of the form for the catalog's model: the inputs and the chosen `one_of` group.
 *
 * @param {{source: string, values: object}} state the section's inputs
 * @param {object|null} model the result of fieldModel (null before the entry arrives)
 * @returns {object} the values
 */
export function formValues(state, model) {
  if (!model || !model.oneOf) return { ...state.values };
  const file = fileGroup(model);
  const paste = model.oneOf.groups.findIndex((group) => group.index !== file);
  return { ...state.values, [ONE_OF_KEY]: state.source === "paste" ? paste : file };
}

/**
 * A column name without its unit in square brackets: "Qmax [m3/s]" gives "Qmax".
 *
 * @param {string} name the column's name
 * @returns {string} the name without the unit
 */
export function stripUnit(name) {
  return String(name).replace(/\s*\[[^\]]*\]\s*$/, "").trim();
}

/**
 * The option value naming a column: its name without the unit when that is unique among
 * the columns (as Hydrolog resolves it), else the full name.
 *
 * @param {string} name the column's name
 * @param {string[]} columns every column of the file
 * @returns {string} the value of `value_column` or `date_column`
 */
export function columnOption(name, columns) {
  const short = stripUnit(name);
  if (!short || short === name) return name;
  const matches = columns.filter((column) => column === short || stripUnit(column) === short);
  return matches.length === 1 ? short : name;
}

/**
 * The column an option value names, as Hydrolog resolves it: the exact name, else the one
 * column whose name without the unit matches.
 *
 * @param {string} value the option's value
 * @param {string[]} columns every column of the file
 * @returns {string|null} the column, null when none or several match
 */
export function resolveColumn(value, columns) {
  if (!value) return null;
  if (columns.includes(value)) return value;
  const matches = columns.filter((column) => stripUnit(column) === value.trim());
  return matches.length === 1 ? matches[0] : null;
}

/**
 * Read the columns of a series file in the browser: a CSV with a header (comma, semicolon
 * or tab) or a JSON document (records, columns or a list of numbers), as Hydrolog reads it.
 *
 * @param {string} text the file's text
 * @returns {{columns: string[], rows: number, cells: (column: string) => unknown[]}} the
 *   column names, the count of data rows and the cells of a column
 * @throws {Error} when the file has no header or is not valid JSON
 */
export function readColumns(text) {
  const source = String(text || "").replace(/^\ufeff/, "");
  const start = source.trimStart()[0];
  if (start === "[" || start === "{") {
    const doc = JSON.parse(source);
    if (Array.isArray(doc) && doc.every((item) => typeof item === "number" || item === null)) {
      return { columns: ["values"], rows: doc.length, cells: () => doc };
    }
    if (Array.isArray(doc)) {
      const columns = [];
      for (const record of doc) {
        if (record && typeof record === "object") for (const key of Object.keys(record)) if (!columns.includes(key)) columns.push(key);
      }
      return { columns, rows: doc.length, cells: (column) => doc.map((record) => (record ? record[column] : null)) };
    }
    if (doc && typeof doc === "object") {
      const columns = Object.keys(doc).filter((key) => Array.isArray(doc[key]));
      const rows = columns.length ? doc[columns[0]].length : 0;
      return { columns, rows, cells: (column) => doc[column] || [] };
    }
    throw new Error("JSON");
  }
  const table = readTable(source);
  if (!table.header) throw new Error("CSV");
  const columns = table.header.map((name) => name.trim());
  return {
    columns,
    rows: table.rows.length,
    cells: (column) => {
      const index = columns.indexOf(column);
      return table.rows.map((row) => (index >= 0 ? row[index] : undefined));
    },
  };
}

/**
 * Whether a cell is a number or a missing value (empty, NaN, NA).
 *
 * @param {unknown} cell the cell
 * @returns {"number"|"missing"|"other"} the kind
 */
function cellKind(cell) {
  if (cell === null || cell === undefined) return "missing";
  if (typeof cell === "number") return Number.isFinite(cell) ? "number" : "missing";
  const text = String(cell).trim();
  if (!text || /^(nan|na|n\/a|null|none)$/i.test(text)) return "missing";
  const value = parseNumber(text);
  return value === null || Number.isNaN(value) ? "other" : "number";
}

/**
 * A guess of the value column of a file: the last column of numbers.
 *
 * @param {{columns: string[], cells: Function}} table the columns of readColumns
 * @returns {string|null} the column
 */
export function guessValueColumn(table) {
  const numeric = table.columns.filter((column) => {
    const kinds = table.cells(column).map(cellKind);
    return kinds.includes("number") && !kinds.includes("other");
  });
  return numeric.length ? numeric[numeric.length - 1] : null;
}

/**
 * A guess of the date column of a file: the first column of ISO dates (a daily series).
 *
 * @param {{columns: string[], cells: Function}} table the columns of readColumns
 * @returns {string|null} the column, null for annual maxima
 */
export function guessDateColumn(table) {
  const iso = /^\d{4}-\d{2}-\d{2}([T ]00:00(:00(\.0+)?)?)?$/;
  return (
    table.columns.find((column) => {
      const cells = table.cells(column).filter((cell) => cell !== null && cell !== undefined && String(cell).trim() !== "");
      return cells.length > 0 && cells.every((cell) => iso.test(String(cell).trim()));
    }) || null
  );
}

/**
 * The cells of a column as years, when every one is a whole year (1000 to 2999).
 *
 * @param {{cells: Function}} table the file's columns
 * @param {string} column the column
 * @returns {number[]|null} the years in file order, null when a cell is not a year
 */
function columnYears(table, column) {
  const years = table.cells(column).map((cell) => parseNumber(cell === null || cell === undefined ? "" : String(cell)));
  return years.every((year) => Number.isInteger(year) && year >= 1000 && year <= 2999) ? years : null;
}

/**
 * The years of the annual maxima of a file without dates: the column other than the
 * values whose every cell is a whole year (1000 to 2999), one per maximum.
 *
 * @param {{columns: string[], rows: number, cells: Function}} table the file's columns
 * @param {string} valueColumn the value column (as resolved)
 * @param {number} count the count of maxima the result holds
 * @returns {number[]|null} the years in file order, null when there is no such column
 */
export function fileYears(table, valueColumn, count) {
  if (!table || table.rows !== count) return null;
  for (const column of table.columns) {
    if (column === valueColumn) continue;
    const years = columnYears(table, column);
    if (years) return years;
  }
  return null;
}

/**
 * The year column of a file of annual maxima, which Hydrolog takes as `year_column`: the
 * first column other than the values whose cells are whole years, strictly increasing.
 *
 * @param {{columns: string[], cells: Function}} table the file's columns
 * @param {string|null} valueColumn the value column (as resolved)
 * @returns {string|null} the column, null when the file has none
 */
function yearColumn(table, valueColumn) {
  const increasing = (years) => Boolean(years) && years.every((year, index) => index === 0 || year > years[index - 1]);
  return table.columns.find((column) => column !== valueColumn && increasing(columnYears(table, column))) || null;
}

/**
 * The options of `stats homogeneity` for the series of a run of the section: the pasted
 * values, or the file with its value and date columns; the annual maxima of a file without
 * dates also take its year column, so the split and the change point have their years.
 *
 * @param {object} sent the options of the run of `stats flood-frequency`
 * @param {{columns: string[], cells: Function}|null} table the file's columns, if read
 * @returns {object} the options
 */
export function homogeneityOptions(sent, table) {
  const options = {};
  for (const name of SERIES_OPTIONS) if (sent[name] !== undefined) options[name] = sent[name];
  if (options.input_file === undefined || options.date_column !== undefined || !table) return options;
  const valueColumn = options.value_column ? resolveColumn(options.value_column, table.columns) : table.columns[0];
  const column = yearColumn(table, valueColumn);
  return column ? { ...options, year_column: column } : options;
}

/**
 * The annual maxima ranked for the table: each sorted value with its year (when known) and
 * the empirical exceedance probability of the result. A stable sort keeps tied maxima in
 * the order of the years.
 *
 * @param {object} result the result of `stats flood-frequency`
 * @param {number[]|null} years the years of `annual_maxima`, in its order
 * @returns {Array<{rank: number, year: number|null, value: number, p: number}>} the rows
 */
export function rankedMaxima(result, years) {
  const maxima = result.annual_maxima || [];
  const order = maxima.map((value, index) => ({ value, year: years && years.length === maxima.length ? years[index] : null }));
  order.sort((a, b) => b.value - a.value);
  const empirical = result.empirical || {};
  const probabilities = empirical.exceedance_prob || [];
  const sorted = empirical.values_sorted || [];
  return sorted.map((value, index) => ({
    rank: index + 1,
    year: order[index] && order[index].value === value ? order[index].year : null,
    value,
    p: probabilities[index],
  }));
}

/**
 * The years of a result's maxima: the hydrological years of a daily series, else those of
 * the file.
 *
 * @param {object} result the result
 * @param {{columns: string[], rows: number, cells: Function}|null} table the file's columns
 * @param {string|null} valueColumn the value column as resolved
 * @returns {number[]|null} the years
 */
export function maximaYears(result, table, valueColumn) {
  if (Array.isArray(result.hydrological_years)) return result.hydrological_years;
  return table && valueColumn ? fileYears(table, valueColumn, result.n_years) : null;
}

/**
 * The quantile of a distribution at a return period.
 *
 * @param {object} fit a fitted distribution of the result
 * @param {number} period the return period [years]
 * @returns {number|null} the quantile, null when the period was not asked for
 */
export function quantileAt(fit, period) {
  const index = (fit.return_periods || []).findIndex((value) => Math.abs(value - period) < 1e-9);
  return index < 0 ? null : fit.quantiles[index];
}

/**
 * The exceedance probability [%] of a return period as Hydrolog gives it.
 *
 * @param {object} fit a fitted distribution of the result
 * @param {number} period the return period [years]
 * @returns {number|null} p [%], null when the period was not asked for
 */
export function percentAt(fit, period) {
  const index = (fit.return_periods || []).findIndex((value) => Math.abs(value - period) < 1e-9);
  return index < 0 ? null : fit.exceedance_probabilities[index] * 100;
}

/**
 * The fits of the distributions ticked „W tabeli kwantyli”, in the order of the table.
 *
 * @param {object} result the result of `stats flood-frequency`
 * @param {string[]} ticked the names of the ticked distributions
 * @returns {object[]} the fits
 */
export function tickedFits(result, ticked) {
  return result.distributions.filter((fit) => ticked.includes(fit.distribution_name));
}

const docs = new Map();

/**
 * One command's catalog entry, fetched once; a failed fetch is reported (and tried again on
 * the next mount).
 *
 * @param {string} name the command
 * @returns {{doc: object|null, error: string|null}} the hydrolog-commands/1 document
 */
export function useCommandDoc(name) {
  const [state, setState] = useState(() => ({ doc: docs.get(name) || null, error: null }));
  useEffect(() => {
    if (state.doc) return undefined;
    let alive = true;
    api
      .command(name)
      .then((doc) => {
        docs.set(name, doc);
        if (alive) setState({ doc, error: null });
      })
      .catch((error) => {
        if (alive) setState({ doc: null, error: error && error.doc ? describeError(error.doc).text : String((error && error.message) || error) });
      });
    return () => {
      alive = false;
    };
  }, [name]);
  return state;
}

const tables = new Map();

/**
 * The columns of a session file, read in the browser from its bytes (fetched once per
 * content): the header and, for the table of annual maxima, the cells.
 *
 * @param {string|null} path "in/<name>", null for none
 * @param {string|null} sha256 the file's digest in the session (null when it is not there)
 * @returns {{state: "none"|"loading"|"ok"|"error", table?: object, message?: string}} the columns
 */
export function useFileTable(path, sha256) {
  const key = path && sha256 ? `${path}|${sha256}` : null;
  const [found, setFound] = useState(() => (key && tables.has(key) ? { state: "ok", table: tables.get(key) } : { state: key ? "loading" : "none" }));
  useEffect(() => {
    if (!key) {
      setFound({ state: "none" });
      return undefined;
    }
    if (tables.has(key)) {
      setFound({ state: "ok", table: tables.get(key) });
      return undefined;
    }
    let alive = true;
    setFound({ state: "loading" });
    fetch(api.fileUrl(path), { credentials: "same-origin", cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      })
      .then((text) => {
        const table = readColumns(text);
        tables.set(key, table);
        if (alive) setFound({ state: "ok", table });
      })
      .catch((error) => {
        if (alive) setFound({ state: "error", message: String((error && error.message) || error) });
      });
    return () => {
      alive = false;
    };
  }, [key]);
  return found;
}
