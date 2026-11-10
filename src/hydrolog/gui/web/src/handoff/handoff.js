// The hand-off between the GUIs of the ecosystem (plan D15): `nogat-handoff/1` exactly as
// Nogat publishes it (schemas/nogat/handoff-1.schema.json, copied unchanged), carrying
// `hydrolog-network/1` or `hydrolog-series/1` (ADR-0020). buildHandoff writes the envelope
// around a network; readHandoff reads a text: the envelope against Nogat's schema
// (envelope.js), the payload's kind and, given its schema, the payload's content, then
// tells which section opens it: one subcatchment made from rainfall with its outlet opens
// in „Hydrogram zlewni”, any other network in „Sieć i trasowanie”, a station's series
// (Archiwista) in „Statystyka przepływów”; read in Sieć, every network opens there (plan
// 2026-11-10-network-editor, D10). The producer's result is for comparison only
// (compareResults): Hydrolog recomputes and shows both.
//
// Pure functions without Preact, tested in the page (tests/e2e/test_exports.py).

import { hmm, inputText, num } from "../format.js";
import { t } from "../labels/common.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { ENVELOPE_SCHEMA } from "./envelope.js";
import { isObject, schemaProblems } from "./validate.js";

/** The envelope's `schema`. */
export const HANDOFF_SCHEMA = "nogat-handoff/1";

/** The payload Hydrolog writes and takes into Hydrogram zlewni and Sieć. */
export const PAYLOAD_SCHEMA = "hydrolog-network/1";

/** The payload of a station's series, taken into Statystyka przepływów (ADR-0020). */
export const SERIES_SCHEMA = "hydrolog-series/1";

/** The schema of the network payload, GET api/schemas/… */
export const NETWORK_SCHEMA_FILE = "hydrolog-network-1.schema.json";

/** The schema of the series payload, GET api/schemas/… */
export const SERIES_SCHEMA_FILE = "hydrolog-series-1.schema.json";

/** The producer of the hand-offs this GUI writes. */
export const TOOL = "hydrolog";

/** The tools whose marks the page holds (nogat/marks/<tool>.svg). */
export const MARKS = Object.freeze(["archiwista", "hydrograf", "hydrolog", "nogat"]);

/** The quantities of a result compared, with their D15 names and how they are shown. */
export const QUANTITIES = Object.freeze([
  { key: "q", field: "peak_discharge_m3s", unit: "m³/s", format: (value) => num(value, 2) },
  { key: "tp", field: "time_to_peak_min", unit: "h", format: (value) => hmm(value) },
  { key: "volume", field: "total_volume_m3", unit: "m³", format: (value) => num(value, 0) },
]);

/**
 * A moment as RFC 3339 in UTC without fractions: "2026-11-02T10:15:00Z".
 *
 * @param {Date} [date] the moment (now)
 * @returns {string} the text
 */
export function stamp(date = new Date()) {
  return date.toISOString().replace(/\.\d+Z$/, "Z");
}

/**
 * Write a hand-off (nogat-handoff/1) with Hydrolog as its producer.
 *
 * @param {{subject: string, provenance?: object, payload: object, result?: object|null,
 *   page?: string, version: string, createdAt?: string}} parts what is handed off (the
 *   watershed's or network's name), where its inputs came from, the hydrolog-network/1
 *   document, Hydrolog's result of it (peak_discharge_m3s, time_to_peak_min,
 *   total_volume_m3, command), the page to return to ("#hydrogram"), Hydrolog's version
 *   and the moment (now)
 * @returns {object} the document
 */
export function buildHandoff({ subject, provenance = {}, payload, result = null, page, version, createdAt }) {
  const producer = { tool: TOOL, version: String(version) };
  if (page) producer.page = page;
  const doc = {
    schema: HANDOFF_SCHEMA,
    created_at: createdAt || stamp(),
    producer,
    subject: String(subject),
    provenance: provenance || {},
    payload,
  };
  if (result && Object.keys(result).length) doc.result = result;
  return doc;
}

/**
 * The file name of a hand-off: "<subject>.handoff.json".
 *
 * @param {string} base the base of the section's file names (export-panel's fileBase)
 * @returns {string} the name
 */
export function handoffFileName(base) {
  return `${base}.handoff.json`;
}

/**
 * The section a payload opens in: one subcatchment made from rainfall (a watershed and its
 * runoff) and the outlet it flows to open in Hydrogram zlewni, anything else in Sieć.
 *
 * @param {object} payload hydrolog-network/1
 * @returns {"hydrogram"|"siec"} the section
 */
export function targetOf(payload) {
  const nodes = isObject(payload) && Array.isArray(payload.nodes) ? payload.nodes : [];
  if (nodes.length !== 2) return "siec";
  const sub = nodes.find((node) => isObject(node) && node.type === "subcatchment" && isObject(node.watershed) && isObject(node.runoff));
  const outlet = nodes.find((node) => isObject(node) && node.type === "outlet");
  if (!sub || !outlet) return "siec";
  return Array.isArray(outlet.from) && outlet.from.length === 1 && outlet.from[0] === sub.id ? "hydrogram" : "siec";
}

/**
 * A value as a problem shows it.
 *
 * @param {unknown} value the value
 * @returns {string} the text
 */
function shown(value) {
  if (typeof value === "number") return inputText(value);
  if (typeof value === "string") return value;
  return JSON.stringify(value === undefined ? null : value);
}

/**
 * The path of a value in words: "payload.nodes[0] (Z1).watershed", the node's id after
 * its index; the whole document is „dokument”.
 *
 * @param {Array<string|number>} path the path
 * @param {unknown} doc the document the path is in
 * @returns {string} the path
 */
export function pathText(path, doc) {
  if (!path.length) return texts.problems.root;
  let text = "";
  let at = doc;
  for (const part of path) {
    if (typeof part === "number") {
      at = Array.isArray(at) ? at[part] : undefined;
      text += `[${part}]`;
      if (isObject(at) && typeof at.id === "string") text += ` (${at.id})`;
    } else {
      at = isObject(at) ? at[part] : undefined;
      text += text ? `.${part}` : part;
    }
  }
  return text;
}

/**
 * A problem of validate.js in Polish, after the path of its value.
 *
 * @param {{path: Array<string|number>, keyword: string, params: object}} problem the problem
 * @param {unknown} doc the document the path is in
 * @returns {string} e.g. „payload.nodes[0] (Z1).watershed: nieznane pole „lc_km””
 */
export function problemText(problem, doc) {
  const words = texts.schema;
  const params = problem.params || {};
  let what;
  switch (problem.keyword) {
    case "required":
      what = t(words.required, { name: params.name });
      break;
    case "additionalProperties":
      what = t(words.additional, { name: params.name });
      break;
    case "type":
      what = t(words.type, { type: params.types.map((type) => words.types[type] || type).join(words.or) });
      break;
    case "const":
      what = t(words.const, { value: shown(params.value) });
      break;
    case "enum":
      what = t(words.enum, { allowed: params.allowed.map(shown).join(", ") });
      break;
    case "minimum":
    case "maximum":
    case "exclusiveMinimum":
    case "exclusiveMaximum":
    case "maxLength":
    case "minItems":
    case "maxItems":
      what = t(words[problem.keyword], { limit: shown(params.limit) });
      break;
    case "minLength":
      what = params.limit === 1 ? words.minLength : t(words.minLengthOf, { limit: params.limit });
      break;
    case "dependentRequired":
      what = t(words.dependentRequired, { name: params.name, needed: params.needed });
      break;
    case "propertyNames":
      what = t(words.propertyName, { name: params.name });
      break;
    default:
      what = words[problem.keyword] || words.not;
  }
  return `${pathText(problem.path, doc)}: ${what}`;
}

/**
 * What Hydrogram zlewni needs of a payload beyond its schema: a series of rain in the
 * network's time step. A subcatchment without rainfall (Hydrograf hands the watershed off
 * before it has a hydrograph) opens with the rainfall still to choose.
 *
 * @param {object} payload a valid hydrolog-network/1 of one subcatchment and its outlet
 * @returns {string[]} the problems in Polish
 */
function hydrogramProblems(payload) {
  const sub = payload.nodes.find((node) => node.type === "subcatchment");
  const rainfall = sub.rainfall || payload.rainfall;
  const step = payload.timestep_min;
  if (isObject(rainfall) && rainfall.kind === "series" && typeof step === "number" && Math.abs(step - rainfall.timestep_min) > 1e-9 * step) {
    return [t(texts.problems.stepMismatch, { id: sub.id, network: inputText(step), series: inputText(rainfall.timestep_min) })];
  }
  return [];
}

/**
 * What Statystyka przepływów needs of a series beyond its schema: as many values as dates
 * or years, some of them numbers, and annual maxima (the section computes flood
 * quantiles; low flows are `stats low-flow` in Polecenia).
 *
 * @param {object} payload a valid hydrolog-series/1
 * @returns {string[]} the problems in Polish
 */
function seriesProblems(payload) {
  const keys = payload.step === "day" ? payload.dates : payload.years;
  if (!Array.isArray(keys) || !Array.isArray(payload.values)) return [texts.problems.seriesEmpty];
  if (keys.length !== payload.values.length) {
    return [t(texts.problems.seriesLength, { keys: keys.length, values: payload.values.length })];
  }
  if (!payload.values.some((value) => typeof value === "number")) return [texts.problems.seriesEmpty];
  if (payload.step === "year" && payload.statistic !== "max") return [texts.problems.seriesMinima];
  return [];
}

/**
 * Read a hand-off: parse the text, check the envelope against Nogat's schema, the
 * payload's kind and, given its schema, the payload against it, then tell the section
 * that opens it: targetOf's, or Sieć for every network when Sieć reads it (`into`).
 *
 * @param {string} text the hand-off as text (a file's or the clipboard's)
 * @param {{networkSchema?: object|null, seriesSchema?: object|null, into?: "siec"|null}}
 *   [options] hydrolog-network-1.schema.json and hydrolog-series-1.schema.json (a
 *   payload is not checked against its schema without it), and the section that reads
 *   it: "siec" opens a network there even when it holds one subcatchment (plan
 *   2026-11-10-network-editor, D10); a series still goes to Statystyka przepływów
 * @returns {{doc: object|null, target: "hydrogram"|"siec"|"statystyka"|null, problems:
 *   string[]}} the document, the section that opens it (null when it cannot open) and
 *   the problems in Polish; none when it opens
 */
export function readHandoff(text, { networkSchema = null, seriesSchema = null, into = null } = {}) {
  let doc;
  try {
    doc = JSON.parse(String(text).replace(/^\uFEFF/, ""));
  } catch (error) {
    return { doc: null, target: null, problems: [t(texts.problems.notJson, { message: error.message })] };
  }
  if (!isObject(doc)) return { doc: null, target: null, problems: [texts.problems.notObject] };
  if (doc.schema !== HANDOFF_SCHEMA) {
    const problems = [t(texts.problems.notHandoff, { schema: shown(doc.schema) })];
    if (doc.schema === PAYLOAD_SCHEMA) problems.push(texts.problems.network);
    else if (typeof doc.area_km2 === "number" || isObject(doc.watershed)) problems.push(texts.problems.watershed);
    return { doc, target: null, problems };
  }
  const problems = schemaProblems(ENVELOPE_SCHEMA, doc).map((problem) => problemText(problem, doc));
  const payload = doc.payload;
  const kind = isObject(payload) && typeof payload.schema === "string" ? payload.schema : null;
  const schema = kind === SERIES_SCHEMA ? seriesSchema : networkSchema;
  if (kind !== null && kind !== PAYLOAD_SCHEMA && kind !== SERIES_SCHEMA) {
    problems.push(t(texts.problems.payloadKind, { schema: kind }));
  } else if (isObject(payload) && schema) {
    for (const problem of schemaProblems(schema, payload, schema, ["payload"])) problems.push(problemText(problem, doc));
  }
  if (problems.length) return { doc, target: null, problems };
  if (kind === SERIES_SCHEMA) {
    const needs = seriesProblems(payload);
    return { doc, target: needs.length ? null : "statystyka", problems: needs };
  }
  const target = into === "siec" ? "siec" : targetOf(payload);
  const needs = target === "hydrogram" ? hydrogramProblems(payload) : [];
  return { doc, target: needs.length ? null : target, problems: needs };
}

/**
 * The inputs of Statystyka przepływów a series opens with: annual maxima as the pasted
 * values (the missing years left out), daily values as a file of the session, `date` and
 * the variable, whose columns the section then finds.
 *
 * @param {object} payload a hydrolog-series/1 readHandoff opened
 * @returns {{source: "paste"|"file", values: object, csv: string|null}} the section's
 *   source and form values, and the file's text of a daily series
 */
export function statystykaInputs(payload) {
  if (payload.step === "year") {
    const values = payload.values.filter((value) => typeof value === "number");
    return { source: "paste", values: { values: values.map(inputText).join("; ") }, csv: null };
  }
  const rows = payload.dates.map((date, index) => {
    const value = payload.values[index];
    return `${date},${typeof value === "number" ? String(value) : ""}`;
  });
  return { source: "file", values: {}, csv: `date,${payload.variable}\n${rows.join("\n")}\n` };
}

/**
 * The name of a tool: as a subject („Hydrograf”) or after „z” („Hydrografa”).
 *
 * @param {string} tool the registry's name ("hydrograf")
 * @param {boolean} [after=false] the form after „z”
 * @returns {string} the name
 */
export function toolName(tool, after = false) {
  const known = Object.hasOwn(texts.tools, tool) ? texts.tools[tool] : null;
  if (known) return known[after ? 1 : 0];
  const word = String(tool || "");
  return word ? word[0].toUpperCase() + word.slice(1) : "–";
}

/**
 * The tool and version that computed a hand-off's result: `result.computed_with`, else
 * the producer.
 *
 * @param {{producer: {tool: string, version: string}, result?: object|null}} received
 *   what the hand-off held
 * @returns {{tool: string, version: string}} the engine
 */
export function engineOf(received) {
  const given = received.result && isObject(received.result.computed_with) ? received.result.computed_with : null;
  return given || { tool: received.producer.tool, version: received.producer.version };
}

/**
 * The producer's result beside Hydrolog's own: each quantity the producer gave, as both
 * show it, and whether they differ as shown.
 *
 * @param {object} theirs the hand-off's result (peak_discharge_m3s, time_to_peak_min,
 *   total_volume_m3)
 * @param {object|null} ours Hydrolog's result in the same names (null before a run)
 * @returns {{rows: Array<{key: string, unit: string, producer: string, own: string|null,
 *   differs: boolean}>, differs: boolean}} the rows and whether any differs
 */
export function compareResults(theirs, ours) {
  const rows = QUANTITIES.filter((item) => typeof theirs[item.field] === "number").map((item) => {
    const producer = item.format(theirs[item.field]);
    const own = ours && typeof ours[item.field] === "number" ? item.format(ours[item.field]) : null;
    return { key: item.key, unit: item.unit, producer, own, differs: own !== null && own !== producer };
  });
  return { rows, differs: rows.some((row) => row.differs) };
}

/**
 * What a section keeps of a hand-off it opened: who wrote it and when, its subject,
 * provenance and result.
 *
 * @param {object} doc the hand-off
 * @returns {{subject: string, created_at: string, producer: object, provenance: object,
 *   result: object|null}} the record
 */
export function receivedOf(doc) {
  return {
    subject: doc.subject,
    created_at: doc.created_at,
    producer: { ...doc.producer },
    provenance: doc.provenance,
    result: isObject(doc.result) ? doc.result : null,
  };
}

/**
 * A moment of a hand-off for people: „2 lis 2026, 11:15” in the page's time zone.
 *
 * @param {string} createdAt RFC 3339
 * @returns {string} the text, the given text when it does not parse
 */
export function momentText(createdAt) {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return String(createdAt);
  return date.toLocaleString("pl-PL", { dateStyle: "medium", timeStyle: "short" });
}
