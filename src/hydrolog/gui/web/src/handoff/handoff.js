// The hand-off between the GUIs of the ecosystem (plan D15): `nogat-handoff/1` exactly as
// Nogat publishes it (schemas/nogat/handoff-1.schema.json, copied unchanged), carrying
// `hydrolog-network/1`. buildHandoff writes the envelope around a payload; readHandoff
// reads a text: the envelope against Nogat's schema (envelope.js), the payload's kind,
// and, given hydrolog-network-1.schema.json, the payload's content, then tells which
// section opens it: one subcatchment made from rainfall with its outlet opens in
// „Hydrogram zlewni”, any other network in „Sieć i trasowanie”. The producer's result is
// for comparison only (compareResults): Hydrolog recomputes and shows both.
//
// Pure functions without Preact, tested in the page (tests/e2e/test_exports.py).

import { hmm, inputText, num } from "../format.js";
import { t } from "../labels/common.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { ENVELOPE_SCHEMA } from "./envelope.js";
import { isObject, schemaProblems } from "./validate.js";

/** The envelope's `schema`. */
export const HANDOFF_SCHEMA = "nogat-handoff/1";

/** The only payload Hydrolog takes and writes. */
export const PAYLOAD_SCHEMA = "hydrolog-network/1";

/** The schema of the payload, GET api/schemas/… */
export const NETWORK_SCHEMA_FILE = "hydrolog-network-1.schema.json";

/** The producer of the hand-offs this GUI writes. */
export const TOOL = "hydrolog";

/** The tools whose marks the page holds (nogat/marks/<tool>.svg). */
export const MARKS = Object.freeze(["hydrograf", "hydrolog", "nogat"]);

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
 * What Hydrogram zlewni needs of a payload beyond its schema: a rainfall for the
 * subcatchment, and a series of rain in the network's time step.
 *
 * @param {object} payload a valid hydrolog-network/1 of one subcatchment and its outlet
 * @returns {string[]} the problems in Polish
 */
function hydrogramProblems(payload) {
  const sub = payload.nodes.find((node) => node.type === "subcatchment");
  const rainfall = sub.rainfall || payload.rainfall;
  if (!isObject(rainfall)) return [t(texts.problems.noRainfall, { id: sub.id })];
  const step = payload.timestep_min;
  if (rainfall.kind === "series" && typeof step === "number" && Math.abs(step - rainfall.timestep_min) > 1e-9 * step) {
    return [t(texts.problems.stepMismatch, { id: sub.id, network: inputText(step), series: inputText(rainfall.timestep_min) })];
  }
  return [];
}

/**
 * Read a hand-off: parse the text, check the envelope against Nogat's schema, the
 * payload's kind and, given the network schema, the payload against it, then tell the
 * section that opens it.
 *
 * @param {string} text the hand-off as text (a file's or the clipboard's)
 * @param {{networkSchema?: object|null}} [schemas] hydrolog-network-1.schema.json (the
 *   payload is not checked against it without)
 * @returns {{doc: object|null, target: "hydrogram"|"siec"|null, problems: string[]}} the
 *   document, the section that opens it (null when it cannot open) and the problems in
 *   Polish; none when it opens
 */
export function readHandoff(text, { networkSchema = null } = {}) {
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
  if (isObject(payload) && typeof payload.schema === "string" && payload.schema !== PAYLOAD_SCHEMA) {
    problems.push(t(texts.problems.payloadKind, { schema: payload.schema }));
  } else if (isObject(payload) && networkSchema) {
    for (const problem of schemaProblems(networkSchema, payload, networkSchema, ["payload"])) problems.push(problemText(problem, doc));
  }
  if (problems.length) return { doc, target: null, problems };
  const target = targetOf(payload);
  const needs = target === "hydrogram" ? hydrogramProblems(payload) : [];
  return { doc, target: needs.length ? null : target, problems: needs };
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
