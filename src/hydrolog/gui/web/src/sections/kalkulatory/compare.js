// The comparison of the tc methods, read for display: one row per method of the last run
// with its tc, the parameters `tc watershed` took and how far the method applies, coloured
// and worded by Hydrolog's notices (plan S5). A method of the overland flow (FAA, Kerby)
// is „nie dla zlewni” whatever its notices say; a warning puts a method „poza zakresem”,
// worded by the value and the range of the warning; a method without warnings is „w
// zakresie”, worded by the values it took. The ranges of each method, the data its formula
// came from included, are in its explanation (i) beside the word.

import { exact } from "../../format.js";
import { t } from "../../labels/common.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { describeNotice } from "../../labels/notices.js";
import { OVERLAND_ONLY, TC_METHODS } from "./state.js";

/**
 * The symbol and unit of a field of a method.
 *
 * @param {string} name the field's name
 * @returns {{label: string, unit: string}} the symbol
 */
function symbolOf(name) {
  return Object.hasOwn(texts.symbols, name) ? texts.symbols[name] : { label: name, unit: "" };
}

/**
 * The words of a method's warnings: „A = 37,22 poza 100–10 000 km²”, once per value and
 * range (Kerby–Kirpich repeats the warning of the Kerby part).
 *
 * @param {object[]} notices the notices of the method's run
 * @returns {string[]} the words
 */
export function warningWords(notices) {
  const seen = new Set();
  const words = [];
  for (const notice of notices) {
    if (notice.level !== "warning") continue;
    const details = notice.details || {};
    if (notice.code === "outside_typical_range" && typeof details.value === "number") {
      const key = `${details.value}|${details.minimum}|${details.maximum}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const symbol = symbolOf(details.parameter);
      words.push(t(texts.results.outside, {
        label: symbol.label,
        value: exact(details.value),
        min: exact(details.minimum),
        max: exact(details.maximum),
        unit: symbol.unit,
      }));
    } else {
      words.push(describeNotice(notice).text);
    }
  }
  return words;
}

/**
 * The parameters a method took, in words: „L 14,78 km · S 0,0142”.
 *
 * @param {object} parameters `result.parameters` of `tc watershed`
 * @returns {string} the words
 */
export function parameterWords(parameters) {
  return Object.entries(parameters || {})
    .map(([name, value]) => {
      const symbol = symbolOf(name);
      return `${symbol.label} ${exact(value)}${symbol.unit}`;
    })
    .join(" · ");
}

/**
 * One method of a comparison, read for display.
 *
 * @param {string} method the method
 * @param {{envelope?: object, error?: {text: string}}} outcome the method's run: its
 *   envelope, or the Polish message of its failure
 * @param {string|null} used the method Hydrogram zlewni uses
 * @returns {{method: string, name: string, ok: boolean, tc_min: number|null,
 *   tc_h: number|null, parameters: object, notices: object[], cls: string, word: string,
 *   sub: string, used: boolean}} the row: `cls` is ok | warn | bad (and " used")
 */
export function methodRow(method, outcome, used) {
  const name = texts.methods[method] || method;
  const isUsed = method === used;
  const result = outcome.envelope && outcome.envelope.status === "ok" ? outcome.envelope.result : null;
  if (!result) {
    const text = outcome.error ? outcome.error.text : texts.results.words.error;
    return { method, name, ok: false, tc_min: null, tc_h: null, parameters: {}, notices: [], cls: "bad", word: texts.results.words.error, sub: text, used: isUsed };
  }
  const notices = outcome.envelope.notices || [];
  const warnings = warningWords(notices);
  let state;
  let sub;
  if (OVERLAND_ONLY.includes(method)) {
    state = "bad";
    const length = result.parameters && typeof result.parameters.length_km === "number" ? exact(result.parameters.length_km) : "–";
    sub = [t(texts.results.overland, { length }), ...warnings].join("; ");
  } else if (warnings.length) {
    state = "warn";
    sub = warnings.join("; ");
  } else {
    state = "ok";
    sub = parameterWords(result.parameters);
  }
  return {
    method,
    name,
    ok: true,
    tc_min: result.tc_min,
    tc_h: result.tc_h,
    parameters: result.parameters || {},
    notices,
    cls: isUsed ? `${state} used` : state,
    word: texts.results.words[state],
    sub,
    used: isUsed,
  };
}

/**
 * The rows of a comparison's run, in the catalog's order of the methods.
 *
 * @param {{methods: string[], outcomes: Object<string, object>}} run the run
 * @param {string|null} used the method Hydrogram zlewni uses
 * @returns {object[]} the rows (see methodRow)
 */
export function compareRows(run, used) {
  return TC_METHODS.filter((method) => run.methods.includes(method)).map((method) => methodRow(method, run.outcomes[method] || {}, used));
}

/**
 * The rows of the chart: the methods of a watershed by tc, then those of the overland flow
 * by tc; failed runs are left out.
 *
 * @param {object[]} rows the rows of compareRows
 * @returns {object[]} the rows to draw
 */
export function barRows(rows) {
  const drawn = rows.filter((row) => row.ok);
  const byTc = (a, b) => a.tc_min - b.tc_min;
  return [
    ...drawn.filter((row) => !OVERLAND_ONLY.includes(row.method)).sort(byTc),
    ...drawn.filter((row) => OVERLAND_ONLY.includes(row.method)).sort(byTc),
  ];
}

/**
 * The notices of a comparison, once each (the same warning of two runs is one notice).
 *
 * @param {object[]} rows the rows of compareRows
 * @returns {object[]} the notices
 */
export function uniqueNotices(rows) {
  const seen = new Set();
  const found = [];
  for (const row of rows) {
    for (const notice of row.notices) {
      const key = JSON.stringify([notice.code, notice.details || notice.message]);
      if (seen.has(key)) continue;
      seen.add(key);
      found.push(notice);
    }
  }
  return found;
}
