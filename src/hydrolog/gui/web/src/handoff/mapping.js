// The mapping between the sections and hydrolog-network/1 (plan D15). A subcatchment made
// from rainfall and Hydrogram's inputs map both ways in one place (plan
// 2026-11-10-network-wizard, D3): subcatchmentNode writes the node of the inputs as a run of
// `hydrograph generate` takes them, subcatchmentInputs reads a node back, with the
// library's defaults for what a document leaves out. „Hydrogram zlewni” writes its shown
// run as that node and the outlet it flows to (route network computes such a node as
// `hydrograph generate` does, so the payload gives the same peak; Nash by Lutz goes as
// `nash_estimation`, so whoever computes the node estimates n and K again from its
// watershed), with where its inputs came from (provenance: the PMAXTP point, method,
// probability and duration of the fetched depth, the watershed's source and the fields
// changed since) and its result; back, a payload's subcatchment becomes the section's
// inputs, its source the watershed's origin and the hand-off's record (`handoff`) what the
// results compare with. „Sieć i trasowanie” keeps the same inputs as the values of each such
// subcatchment (siecValues, siecSubcatchment), so a node of Sieć and Hydrogram's hand-off
// cannot differ. A rainfall of the document and the inputs of step 2 map both ways too
// (rainfallOf, rainfallInputs; D4), which Hydrogram zlewni and Sieć's network share. Sieć
// writes its whole network with the outlet's result, adds a hand-off's subcatchments to its
// open network („Dodaj zlewnię z Hydrografa”, plan 2026-11-10-network-editor, D10) and
// fills its chosen subcatchment from a hand-off of one watershed (siecFill; plan
// 2026-11-10-network-wizard, D10). Field names are Hydrolog's (channel_length_km; slopes
// in m/m); mapping Hydrograf's names is Hydrograf's side.

import { inputText, parseNumber, plural } from "../format.js";
import { t } from "../labels/common.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { hydrogram as hydrogramTexts } from "../labels/hydrogram.js";
import {
  PMAXTP_DURATIONS,
  PMAXTP_METHODS,
  PMAXTP_PROBABILITIES,
  SNYDER_LENGTHS,
  TEXT_FIELDS,
  WATERSHED_FIELDS,
  changedFrom,
  hasOwnRainfall,
  initialRain,
  initialState,
  isEmpty,
  normalize,
  numberOf,
  pmaxtpOptions,
  pmaxtpRecord,
  rainOptions,
  sentFields,
  sentWatershed,
  toOptions,
  usedTexts,
} from "../sections/hydrogram/state.js";
import { cellBeside, freeId } from "../sections/siec/editor/edits.js";
import { MAX_DESCRIPTION_CHARS, nodeValues, withoutPicture } from "../sections/siec/node-model.js";
import { MARKS, PAYLOAD_SCHEMA, buildHandoff, momentText, receivedOf, toolName } from "./handoff.js";
import { canonical, isObject } from "./validate.js";

/** The id of Hydrogram's subcatchment and of its outlet in the payload (D15). */
export const SUBCATCHMENT_ID = "Z1";
export const OUTLET_ID = "OUT";

/** The time step of `hydrograph generate` and of a network that gives none [min]. */
export const DEFAULT_TIMESTEP_MIN = 5;

/** The runoff model of a subcatchment made from rainfall: `hydrograph generate`'s. */
const RUNOFF_MODEL = "curve-number";

/** The key of the choice of how a subcatchment of Sieć brings its hydrograph (node-model.js VARIANTS). */
const VARIANT = "#variant";

/** The options of `hydrograph generate` that make the node's `runoff`, in its order. */
const RUNOFF_OPTIONS = Object.freeze([
  "tc_min",
  "tc_method",
  "ia_coefficient",
  "amc",
  "uh_model",
  "nash_n",
  "nash_k_min",
  "nash_estimation",
  "clark_r_min",
  "clark_r_tc_ratio",
  "snyder_length_km",
  "snyder_centroid_length_km",
  "snyder_ct",
  "snyder_cp",
]);

/** The options of a design storm, the `rainfall` of kind design. */
const DESIGN_OPTIONS = Object.freeze(["hietogram_type", "total_mm", "duration_min", "alpha", "beta", "peak_position"]);

/** The typed values that make the rainfall, for telling whether it changed. */
const RAIN_TEXTS = Object.freeze(["values", ...DESIGN_OPTIONS, "timestep_min"]);

/**
 * Hydrogram's inputs of a run as hydrolog-network/1: one subcatchment made from rainfall
 * (subcatchmentNode) and the outlet, with the run's time step.
 *
 * @param {object} inputs the inputs of the run
 * @param {string} [name] the network's name (the subject)
 * @returns {object} the payload
 */
export function hydrogramPayload(inputs, name) {
  const options = toOptions(inputs);
  const payload = { schema: PAYLOAD_SCHEMA };
  if (name) payload.name = name;
  if (options.timestep_min !== undefined) payload.timestep_min = options.timestep_min;
  payload.nodes = [subcatchmentNode(inputs, { id: SUBCATCHMENT_ID }), { id: OUTLET_ID, type: "outlet", from: [SUBCATCHMENT_ID] }];
  return payload;
}

/**
 * The node of hydrolog-network/1 of Hydrogram's inputs (plan 2026-11-10-network-wizard,
 * D3): a subcatchment made from rainfall, as a run of `hydrograph generate` takes the
 * inputs (toOptions). Its `watershed` holds the fields a step shows for the inputs'
 * choice (a field of another model or tc method stays in the inputs and is neither saved
 * nor sent); its `runoff` the curve-number model with the options of the chosen tc,
 * model and losses, and none before a model is chosen (the library refuses the node then,
 * as Sieć does); its `rainfall` its own (rainfallOf: none for „Jak w sieci”, a series at
 * the inputs' time step); then its description and position (ADR-0023).
 *
 * @param {object} inputs Hydrogram's inputs (normalize)
 * @param {{id: string, from?: string[]|null, description?: string, position?: {x:
 *   number, y: number}}} place the node's id, inflows (a subcatchment has none),
 *   description and cell
 * @returns {object} the node
 */
export function subcatchmentNode(inputs, { id, from = null, description, position } = {}) {
  const options = toOptions(inputs);
  const node = { id, type: "subcatchment" };
  if (Array.isArray(from) && from.length) node.from = [...from];
  node.watershed = options.watershed;
  if (inputs.uh_model) {
    const runoff = { model: RUNOFF_MODEL };
    for (const option of RUNOFF_OPTIONS) if (options[option] !== undefined) runoff[option] = options[option];
    node.runoff = runoff;
  }
  const rainfall = rainfallOf(inputs);
  if (rainfall) node.rainfall = rainfall;
  if (typeof description === "string" && description.trim()) node.description = description;
  if (position) node.position = { x: position.x, y: position.y };
  return node;
}

/**
 * The fields of a document's watershed as typed text and as values: each field of
 * WatershedParameters it gives (numbers, and the texts of the name, source and CRS), with
 * or without the area (a draft may lack it); unknown keys are left out, as
 * WatershedParameters.from_dict leaves them.
 *
 * @param {unknown} source the `watershed`
 * @returns {{texts: object, values: object}} the fields
 */
function watershedOf(source) {
  const texts = {};
  const values = {};
  for (const name of WATERSHED_FIELDS) {
    const value = isObject(source) ? source[name] : undefined;
    if (TEXT_FIELDS.has(name) ? typeof value === "string" && value.trim() : typeof value === "number" && Number.isFinite(value)) {
      texts[name] = TEXT_FIELDS.has(name) ? value : inputText(value);
      values[name] = value;
    }
  }
  return { texts, values };
}

/**
 * Where a watershed handed off came from, as Hydrogram's step 1 shows it: the producer
 * and its mark, the point of the watershed's provenance (Hydrograf's outlet) or the
 * subject, when it was written and how many fields it gave, and the values a change is
 * marked against.
 *
 * @param {{subject: string, created_at: string, producer: {tool: string}, provenance?:
 *   object}} record the hand-off's record
 * @param {object} values the fields it gave
 * @param {string[]} notes what the reading left out (Snyder's L and Lc), for the detail
 * @returns {object} the `origin` of the inputs
 */
function handedOrigin(record, values, notes) {
  const tool = record.producer.tool;
  const provenance = isObject(record.provenance) ? record.provenance : {};
  const where = isObject(provenance.watershed) ? provenance.watershed : { source: tool };
  const point =
    typeof where.latitude === "number" && typeof where.longitude === "number"
      ? t(texts.origin.point, {
          latitude: degrees(where.latitude),
          ns: where.latitude < 0 ? "S" : "N",
          longitude: degrees(where.longitude),
          ew: where.longitude < 0 ? "W" : "E",
        })
      : null;
  return {
    label: toolName(tool),
    title: t(texts.origin.title, { producer: toolName(tool, true), subject: point || record.subject }),
    detail:
      t(texts.origin.detail, { time: momentText(record.created_at), fields: plural(Object.keys(values).length, hydrogramTexts.watershed.fieldForms) }) +
      notes.map((text) => ` · ${text}`).join(""),
    mark: MARKS.includes(tool) ? tool : null,
    values,
    provenance: where,
  };
}

/**
 * Hydrogram's inputs of a subcatchment made from rainfall of hydrolog-network/1 (plan
 * 2026-11-10-network-wizard, D3): its watershed (every field the document gives; Snyder's
 * L and Lc of the runoff fill the watershed's channel_length_km and Lc_km it lacks, a
 * different one is left out and said in the origin's detail), its runoff with the
 * library's defaults for what the document leaves out (`tc_method` kirpich, `amc` II, λ
 * 0,2 and `uh_model` scs; no model chosen without a runoff), Nash by Lutz from
 * `nash_estimation` and n and K given otherwise (also a node written before
 * `nash_estimation`, whose n and K were Lutz's estimates: D6), and its own rainfall
 * (rainfallInputs). Without one, or with one that writes as the network's rainfall does
 * (`networkRainfall`, D10), it is „Jak w sieci” (`rain_source` "network"), PMAXTP left at
 * the watershed's point when the origin names one. With `origin`, the record of the
 * hand-off it came in, the watershed's origin names the producer (Hydrogram's step 1 marks
 * the fields changed since) and the rainfall's PMAXTP record is read from its provenance.
 *
 * @param {object} node a subcatchment of hydrolog-network/1 with a watershed, a runoff or
 *   a rainfall
 * @param {{origin?: {subject: string, created_at: string, producer: {tool: string},
 *   provenance?: object}|null, networkRainfall?: object|null}} [options] the record of the
 *   hand-off it came in, and the rainfall of the network it joins as the network's
 *   document writes it (rainfallOf)
 * @returns {object} the inputs, a whole state of Hydrogram's steps
 */
export function subcatchmentInputs(node, { origin = null, networkRainfall = null } = {}) {
  const record = isObject(origin) ? origin : null;
  const provenance = record && isObject(record.provenance) ? record.provenance : {};
  const runoff = isObject(node.runoff) ? node.runoff : null;
  const given = runoff || {};
  const { texts: watershed, values } = watershedOf(node.watershed);
  // Snyder's L and Lc are the watershed's channel_length_km and Lc_km: the runoff's fill
  // those the watershed lacks; a different one is left out, said in the origin's detail
  const skipped = [];
  for (const [option, field] of Object.entries(SNYDER_LENGTHS)) {
    const length = given[option];
    if (typeof length !== "number") continue;
    if (isEmpty(watershed[field])) {
      watershed[field] = inputText(length);
      values[field] = length;
    } else if (numberOf(watershed[field]) !== length) {
      skipped.push(t(texts.origin.snyderSkipped, { option, value: inputText(length), field, kept: watershed[field] }));
    }
  }
  const inputs = { ...initialState(), watershed, origin: record ? handedOrigin(record, values, skipped) : null };
  inputs.tc_manual = typeof given.tc_min === "number";
  inputs.tc_min = inputText(given.tc_min);
  inputs.tc_method = given.tc_method || "kirpich";
  inputs.amc = given.amc || "II";
  inputs.ia_coefficient = inputText(given.ia_coefficient);
  inputs.uh_model = runoff ? given.uh_model || "scs" : null;
  inputs.nash_source = inputs.uh_model === "nash" && given.nash_estimation !== "lutz" ? "given" : "lutz";
  inputs.nash_n = inputText(given.nash_n);
  inputs.nash_k_min = inputText(given.nash_k_min);
  inputs.clark_kind = typeof given.clark_r_min === "number" ? "r" : "ratio";
  inputs.clark_r_min = inputText(given.clark_r_min);
  inputs.clark_r_tc_ratio = inputText(given.clark_r_tc_ratio);
  inputs.snyder_ct = inputText(given.snyder_ct);
  inputs.snyder_cp = inputText(given.snyder_cp);
  const rainfall = isObject(node.rainfall) ? node.rainfall : null;
  const read = rainfallInputs(rainfall, provenance);
  const same = rainfall !== null && isObject(networkRainfall) && canonical(rainfallOf({ ...initialRain(), ...read })) === canonical(networkRainfall);
  if (rainfall === null || same) Object.assign(inputs, rainfallInputs(null, provenance), { rain_source: "network" });
  else Object.assign(inputs, read);
  return inputs;
}

/**
 * A design storm of hydrolog-network/1 from options of `hydrograph generate`: its shape,
 * depth and duration and the shape's own parameters, those given.
 *
 * @param {object} options the options
 * @returns {object} the `rainfall` of kind design
 */
function designRainfall(options) {
  const rainfall = { kind: "design" };
  for (const option of DESIGN_OPTIONS) if (options[option] !== undefined) rainfall[option] = options[option];
  return rainfall;
}

/**
 * A series of depths of hydrolog-network/1 at a time step.
 *
 * @param {number[]} values the depths [mm]
 * @param {number|null|undefined} step the time step [min] (DEFAULT_TIMESTEP_MIN without one)
 * @returns {object} the `rainfall` of kind series
 */
function seriesRainfall(values, step) {
  return { kind: "series", depths_mm: [...values], timestep_min: step ?? DEFAULT_TIMESTEP_MIN };
}

/**
 * The `rainfall` of hydrolog-network/1 of the inputs of step 2 (plan
 * 2026-11-10-network-wizard, D4): what a run of `hydrograph generate` takes, a design storm
 * (PMAXTP's with the fetched depth as `total_mm`, which it lacks until then) or a series at
 * the inputs' time step.
 *
 * @param {object} inputs the inputs of the rainfall (initialRain)
 * @returns {object|null} the rainfall, null for „Brak” and „Jak w sieci”
 */
export function rainfallOf(inputs) {
  if (!hasOwnRainfall(inputs)) return null;
  const options = rainOptions(inputs);
  if (inputs.rain_source === "series") return seriesRainfall(options.values || [], numberOf(inputs.timestep_min));
  return designRainfall(options);
}

/**
 * The data of Hydrogram's inputs as one text: the watershed a run sends and every option
 * in use. Equal texts compute the same result.
 *
 * @param {object} inputs the section's inputs
 * @returns {string} the text
 */
export function dataKey(inputs) {
  return JSON.stringify([sentWatershed(inputs), usedTexts(inputs)]);
}

/**
 * The rainfall of Hydrogram's inputs as one text: where it comes from and what makes it.
 *
 * @param {object} inputs the section's inputs
 * @returns {string} the text
 */
export function rainfallKey(inputs) {
  const used = usedTexts(inputs);
  const rain = { source: inputs.rain_source };
  if (inputs.rain_source === "pmaxtp") {
    rain.probability = inputs.pmaxtp_probability_pct;
    rain.point = [inputs.pmaxtp_latitude, inputs.pmaxtp_longitude];
    rain.method = inputs.pmaxtp_method;
  }
  for (const name of RAIN_TEXTS) if (Object.hasOwn(used, name)) rain[name] = used[name];
  return JSON.stringify(rain);
}

/**
 * Where the rainfall came from: the hand-off's own record while the rainfall is as it
 * came, else the PMAXTP depth's point, method, probability and duration, else the person.
 *
 * @param {object} inputs the section's inputs
 * @returns {object} the provenance of `rainfall`
 */
function rainfallOrigin(inputs) {
  const received = isObject(inputs.handoff) ? inputs.handoff : null;
  if (received && received.rainfallKey === rainfallKey(inputs) && isObject(received.provenance) && isObject(received.provenance.rainfall)) {
    return received.provenance.rainfall;
  }
  if (inputs.rain_source === "pmaxtp") {
    return {
      source: "pmaxtp",
      probability_percent: parseNumber(inputs.pmaxtp_probability_pct),
      duration_min: parseNumber(inputs.pmaxtp_duration_min),
      latitude: parseNumber(inputs.pmaxtp_latitude),
      longitude: parseNumber(inputs.pmaxtp_longitude),
      method: inputs.pmaxtp_method,
    };
  }
  return { source: "user" };
}

/**
 * Where the watershed came from: a hand-off's source, a file or the person, with the
 * fields the run sends that changed since (`changed`).
 *
 * @param {object} inputs the section's inputs
 * @returns {object} the provenance of `watershed`
 */
function watershedOrigin(inputs) {
  const origin = isObject(inputs.origin) ? inputs.origin : null;
  const fields = inputs.watershed || {};
  const changed = origin && isObject(origin.values) ? sentFields(inputs).filter((name) => changedFrom(origin, name, fields[name])) : [];
  let entry;
  if (origin && isObject(origin.provenance) && typeof origin.provenance.source === "string") {
    entry = { ...origin.provenance };
    delete entry.changed;
  } else if (origin) {
    entry = { source: "file", file: String(origin.label) };
  } else {
    entry = { source: "user" };
  }
  if (changed.length) entry.changed = changed;
  return entry;
}

/**
 * Where the inputs of Hydrogram's payload came from (`provenance` of nogat-handoff/1): the
 * rainfall and the watershed; the other records of a received hand-off while its data are
 * unchanged.
 *
 * @param {object} inputs the inputs of the run
 * @returns {object} the provenance
 */
export function hydrogramProvenance(inputs) {
  const received = isObject(inputs.handoff) ? inputs.handoff : null;
  const provenance = {};
  if (received && received.key === dataKey(inputs) && isObject(received.provenance)) Object.assign(provenance, received.provenance);
  provenance.rainfall = rainfallOrigin(inputs);
  provenance.watershed = watershedOrigin(inputs);
  return provenance;
}

/**
 * Hydrolog's result of a hand-off from `hydrograph generate`, in the D15 names.
 *
 * @param {object} result the result of hydrograph generate
 * @returns {object} the hand-off's `result`
 */
export function hydrogramResult(result) {
  return {
    command: "hydrograph generate",
    peak_discharge_m3s: result.peak_discharge_m3s,
    time_to_peak_min: result.time_to_peak_min,
    total_volume_m3: result.total_volume_m3,
  };
}

/**
 * The hand-off of Hydrogram's shown run.
 *
 * @param {{run: {inputs: object, options: object, envelope: object}, inputs?: object,
 *   subject: string, createdAt?: string}} parts the run, the inputs whose provenance it
 *   carries (the run's own unless given), the subject and the moment (now)
 * @returns {object} nogat-handoff/1
 */
export function hydrogramHandoff({ run, inputs = run.inputs, subject, createdAt }) {
  return buildHandoff({
    subject,
    provenance: hydrogramProvenance(inputs),
    payload: hydrogramPayload(run.inputs, subject),
    result: hydrogramResult(run.envelope.result),
    page: "#hydrogram",
    version: run.envelope.version,
    createdAt,
  });
}

/**
 * A latitude or longitude as the mockup writes it: „51,0154°”.
 *
 * @param {number} value degrees
 * @returns {string} the text
 */
function degrees(value) {
  return `${Math.abs(value).toFixed(4).replace(".", ",")}°`;
}

/**
 * The point of an origin of the provenance, when it names one.
 *
 * @param {unknown} entry an origin of `provenance`
 * @returns {{latitude: number, longitude: number}|null} the point
 */
function pointOf(entry) {
  return isObject(entry) && typeof entry.latitude === "number" && typeof entry.longitude === "number" ? entry : null;
}

/**
 * The inputs of a hand-off's subcatchment as Hydrogram zlewni reads them (plan
 * 2026-11-10-network-wizard, D10): the node with the hand-off's top rainfall when it has
 * none of its own, read by subcatchmentInputs with the hand-off's record as its origin; a
 * hand-off without any rainfall (Hydrograf's watershed alone) leaves the model to choose.
 *
 * @param {object} doc the hand-off
 * @param {object} node its subcatchment made from rainfall
 * @param {object|null} [networkRainfall] the rainfall of the network the node joins, as
 *   its document writes it (rainfallOf): an equal rainfall is „Jak w sieci”
 * @returns {object} the inputs
 */
function handedInputs(doc, node, networkRainfall = null) {
  const top = isObject(doc.payload.rainfall) ? doc.payload.rainfall : null;
  const rainfall = isObject(node.rainfall) ? node.rainfall : top;
  const inputs = subcatchmentInputs(rainfall ? { ...node, rainfall } : node, { origin: addedOrigin(doc), networkRainfall });
  if (!rainfall && !(isObject(node.runoff) && node.runoff.uh_model)) inputs.uh_model = null;
  return inputs;
}

/**
 * The inputs of Hydrogram zlewni from a hand-off of one subcatchment (readHandoff gave
 * the target "hydrogram"): its subcatchment as Hydrogram reads a hand-off's (handedInputs,
 * subcatchmentInputs), named after the payload or the subject when its watershed has no
 * name; every other input as on a first visit. A hand-off without rainfall (the watershed
 * only) leaves the probability, the duration and the model to choose, PMAXTP at the
 * watershed's point when the provenance names one (Hydrogram zlewni has neither „Brak”
 * nor „Jak w sieci”). The time step is the payload's, else a series' own. `handoff` keeps
 * what the results compare with, the depth handed over included.
 *
 * @param {object} doc the hand-off
 * @returns {object} the inputs, a patch of the whole state
 */
export function hydrogramInputs(doc) {
  const payload = doc.payload;
  const sub = payload.nodes.find((node) => node.type === "subcatchment");
  const watershed = isObject(sub.watershed) ? sub.watershed : {};
  const named = typeof watershed.name === "string" && watershed.name.trim();
  const name = named ? "" : (typeof payload.name === "string" ? payload.name.trim() : "") || doc.subject;
  const inputs = handedInputs(doc, name ? { ...sub, watershed: { ...watershed, name } } : sub);
  if (inputs.rain_source === "network") inputs.rain_source = "pmaxtp";
  const rainfall = isObject(sub.rainfall) ? sub.rainfall : payload.rainfall;
  inputs.timestep_min = typeof payload.timestep_min === "number" ? inputText(payload.timestep_min) : inputs.timestep_min;
  const handed = isObject(rainfall) && inputs.rain_source === "pmaxtp" ? pmaxtpRecord(pmaxtpOptions(normalize(inputs)), rainfall.total_mm) : null;
  const opened = normalize({ ...inputs, pmaxtp_fetched: handed });
  inputs.handoff = { ...receivedOf(doc), key: dataKey(opened), rainfallKey: rainfallKey(opened) };
  return inputs;
}

/**
 * The inputs of step 2 of a `rainfall` of hydrolog-network/1 (a subcatchment's or a
 * network's; plan 2026-11-10-network-wizard, D4), as Hydrogram zlewni reads a hand-off: a
 * design storm is PMAXTP when its origin's record (`rainfall` of the provenance, of
 * `source` pmaxtp) names the probability and the duration the section offers and a point
 * (its own, else the watershed's, such as Hydrograf's outlet) and the duration is the
 * rainfall's, else a design hyetograph; its depth is remembered as fetched only when the
 * record names its own point, otherwise the page fetches the depth of the point. A series
 * gives its depths and its step as `timestep_min`. Without a rainfall: „Brak”, with the
 * watershed's point for PMAXTP when the origin names one.
 *
 * @param {object|null} rainfall the `rainfall`, or null
 * @param {object|null} [origin] where it came from: a hand-off's `provenance`, whose
 *   `rainfall` and `watershed` are read
 * @returns {object} the inputs it gives, a patch of initialRain()
 */
export function rainfallInputs(rainfall, origin = null) {
  const provenance = isObject(origin) ? origin : {};
  const inputs = {};
  if (!isObject(rainfall)) {
    inputs.rain_source = "none";
    const spot = pointOf(provenance.watershed);
    if (spot) {
      inputs.pmaxtp_latitude = inputText(spot.latitude);
      inputs.pmaxtp_longitude = inputText(spot.longitude);
    }
    return inputs;
  }
  if (rainfall.kind === "series") {
    inputs.rain_source = "series";
    inputs.values = (Array.isArray(rainfall.depths_mm) ? rainfall.depths_mm : []).map(inputText).join("; ");
    inputs.timestep_min = inputText(rainfall.timestep_min);
    return inputs;
  }
  const atlas = isObject(provenance.rainfall) && provenance.rainfall.source === "pmaxtp" ? provenance.rainfall : null;
  const probability = atlas && typeof atlas.probability_percent === "number" ? String(atlas.probability_percent) : null;
  const duration = atlas && typeof atlas.duration_min === "number" ? String(atlas.duration_min) : null;
  const own = pointOf(atlas);
  const spot = own || pointOf(provenance.watershed);
  const pmaxtp =
    spot !== null &&
    probability !== null &&
    duration !== null &&
    PMAXTP_PROBABILITIES.includes(probability) &&
    PMAXTP_DURATIONS.includes(duration) &&
    Number(duration) === rainfall.duration_min;
  inputs.rain_source = pmaxtp ? "pmaxtp" : "design";
  if (pmaxtp) {
    inputs.pmaxtp_latitude = inputText(spot.latitude);
    inputs.pmaxtp_longitude = inputText(spot.longitude);
    inputs.pmaxtp_probability_pct = probability;
    inputs.pmaxtp_duration_min = duration;
    inputs.pmaxtp_method = PMAXTP_METHODS.includes(atlas.method) ? atlas.method : "POT";
  }
  inputs.total_mm = inputText(rainfall.total_mm);
  inputs.duration_min = inputText(rainfall.duration_min);
  inputs.hietogram_type = rainfall.hietogram_type;
  inputs.alpha = inputText(rainfall.alpha);
  inputs.beta = inputText(rainfall.beta);
  inputs.peak_position = inputText(rainfall.peak_position);
  if (pmaxtp && own) inputs.pmaxtp_fetched = pmaxtpRecord(pmaxtpOptions({ ...initialRain(), ...inputs }), rainfall.total_mm);
  return inputs;
}

/**
 * The words of Hydrogram's hand-off: what it holds.
 *
 * @param {object} inputs the inputs whose provenance it carries
 * @param {string} rain the rainfall in words (results-panel's rainLabel)
 * @returns {string} the note
 */
export function hydrogramContents(inputs, rain) {
  const fields = Object.keys(sentWatershed(inputs));
  const origin = isObject(inputs.origin) ? inputs.origin : null;
  const changed = origin && isObject(origin.values) ? sentFields(inputs).filter((name) => changedFrom(origin, name, (inputs.watershed || {})[name])).length : 0;
  return t(texts.export.hydrogram, {
    fields: plural(fields.length, hydrogramTexts.watershed.fieldForms),
    changed: changed ? t(texts.export.changed, { count: changed }) : "",
    rain,
  });
}

/**
 * The outlet's result of `route network` in the D15 names.
 *
 * @param {object} result hydrolog-route-network/1
 * @returns {object|null} the hand-off's `result`, null without the outlet
 */
export function outletResult(result) {
  const outlet = (result.nodes || []).find((node) => node.id === result.outlet);
  if (!outlet) return null;
  return {
    command: "route network",
    peak_discharge_m3s: outlet.peak_m3s,
    time_to_peak_min: outlet.time_to_peak_min,
    total_volume_m3: outlet.volume_m3,
  };
}

/**
 * Where Sieć's network came from: a received hand-off's provenance or a file.
 *
 * @param {{name: string, kind: string, handoff?: object}|null} source the network's source
 * @returns {object} the provenance
 */
export function siecProvenance(source) {
  if (source && isObject(source.handoff) && isObject(source.handoff.provenance)) return source.handoff.provenance;
  if (source && source.kind === "file") return { network: { source: "file", file: String(source.name) } };
  return {};
}

/**
 * The hand-off of Sieć's network, with the outlet's result when the last run is of this
 * very document.
 *
 * @param {{subject: string, source: object|null, document: object, result?: object|null,
 *   version: string, createdAt?: string}} parts the subject, the network's source, its
 *   document, the result of its run (route network) and Hydrolog's version
 * @returns {object} nogat-handoff/1
 */
export function siecHandoff({ subject, source, document, result = null, version, createdAt }) {
  return buildHandoff({
    subject,
    provenance: siecProvenance(source),
    payload: document,
    result: result ? outletResult(result) : null,
    page: "#siec",
    version,
    createdAt,
  });
}

/**
 * Whether a node of hydrolog-network/1 is a subcatchment that makes its hydrograph from
 * rainfall: it has a watershed, a runoff or a rainfall (any other subcatchment is given its
 * hydrograph or reads its column of the inflows file).
 *
 * @param {object} node a node of hydrolog-network/1
 * @returns {boolean} true for a subcatchment made from rainfall
 */
function fromRainfall(node) {
  return node.type === "subcatchment" && (isObject(node.watershed) || isObject(node.runoff) || isObject(node.rainfall));
}

/**
 * The values Sieć keeps of a node of hydrolog-network/1 (plan 2026-11-10-network-wizard,
 * D3): a subcatchment made from rainfall keeps Hydrogram's inputs (subcatchmentInputs)
 * under the variant "rain"; any other node the values of its form in „Dane”
 * (node-model.js nodeValues: a subcatchment given its hydrograph or reading its column of
 * the inflows file, a reach, a reservoir).
 *
 * @param {object} node a node of hydrolog-network/1
 * @param {{origin?: object|null, networkRainfall?: object|null}} [options] see
 *   subcatchmentInputs
 * @returns {object} the node's values
 */
export function siecValues(node, options = {}) {
  return fromRainfall(node) ? { [VARIANT]: "rain", ...subcatchmentInputs(node, options) } : nodeValues(node);
}

/**
 * A subcatchment's values in Sieć as Hydrogram's inputs (D3): those of a first visit for
 * what they lack, the rainfall „Jak w sieci” by default (D4); the variant and the values
 * of the other variants stay with them.
 *
 * @param {object} values the subcatchment's values
 * @returns {object} the inputs
 */
export function siecInputs(values) {
  return normalize({ rain_source: "network", ...values });
}

/**
 * The node Sieć writes of a subcatchment made from rainfall (D3, D4): subcatchmentNode of
 * its inputs, whose own series is at the network's time step unless it came with a step
 * of its own (a document's series; another step than the network's is the library's
 * `timestep_mismatch`).
 *
 * @param {object} values the subcatchment's values
 * @param {object} network the network's values (its `timestep_min`)
 * @param {object} place the node's id, inflows, description and position (subcatchmentNode)
 * @returns {object} the node of hydrolog-network/1
 */
export function siecSubcatchment(values, network, place) {
  const inputs = siecInputs(values);
  return subcatchmentNode(isEmpty(inputs.timestep_min) ? { ...inputs, timestep_min: network.timestep_min ?? "" } : inputs, place);
}

/**
 * The network's own values from its document (plan 2026-11-10-network-wizard, D4): its
 * name, description and time step, and its rainfall as the inputs of Hydrogram's step 2
 * (rainfallInputs): with the PMAXTP record of a hand-off's provenance, the way Hydrogram
 * zlewni reads a hand-off; „Brak” without one. A series without the document's time step
 * gives the step its own.
 *
 * @param {object} doc hydrolog-network/1
 * @param {object|null} [provenance] the provenance of the hand-off it came in
 * @returns {object} the values
 */
export function networkInputs(doc, provenance = null) {
  const rain = rainfallInputs(isObject(doc.rainfall) ? doc.rainfall : null, provenance);
  const values = { ...initialRain(), ...rain };
  if (typeof doc.name === "string") values.name = doc.name;
  if (typeof doc.description === "string") values.description = doc.description;
  values.timestep_min = typeof doc.timestep_min === "number" ? inputText(doc.timestep_min) : rain.timestep_min || "";
  return values;
}

/**
 * A network as Sieć writes it once it has opened it: each subcatchment made from rainfall
 * through its inputs (siecValues, siecSubcatchment), the other nodes as they come.
 *
 * @param {object} payload hydrolog-network/1
 * @returns {object} the network
 */
function siecPayload(payload) {
  const network = networkInputs(payload);
  return { ...payload, nodes: payload.nodes.map((node) => (fromRainfall(node) ? siecSubcatchment(siecValues(node), network, node) : node)) };
}

/**
 * What Sieć keeps of a hand-off it opens: the record and its document as Sieć writes it
 * (each subcatchment through Hydrogram's inputs, D3) as one text, to tell whether the
 * network was changed since; the text leaves out the nodes' positions and descriptions,
 * which change no computation (siec/node-model.js withoutPicture).
 *
 * @param {object} doc the hand-off
 * @param {object} payload its network as Sieć opens it (session names of its files)
 * @returns {object} the record
 */
export function siecReceived(doc, payload) {
  return { ...receivedOf(doc), key: canonical(withoutPicture(siecPayload(payload))) };
}

/**
 * A text as the description of a node (ADR-0023): its control characters but the line
 * feed as spaces, at most MAX_DESCRIPTION_CHARS characters.
 *
 * @param {string} text the text (a hand-off's subject)
 * @returns {string} the description, "" for a blank text
 */
function descriptionOf(text) {
  const plain = String(text)
    .replace(/[\u0000-\u0009\u000b-\u001f\u007f-\u009f]/gu, " ")
    .trim();
  return [...plain].slice(0, MAX_DESCRIPTION_CHARS).join("").trimEnd();
}

/**
 * Where a subcatchment added or filled from a hand-off came from (D10), kept beside its
 * structure and shown in „Dane”: who wrote the hand-off and when, its subject and
 * provenance; the hand-off's result, of its outlet, stays out.
 *
 * @param {object} doc the hand-off
 * @returns {{subject: string, created_at: string, producer: object, provenance: object}}
 *   the origin
 */
function addedOrigin(doc) {
  const { result: _result, ...origin } = receivedOf(doc);
  return origin;
}

/**
 * The network's time step beside a hand-off's (D10): the network keeps its own, and an
 * empty network without a step takes the hand-off's; a different step, or one the
 * network does not give, is said.
 *
 * @param {object} network the network's values
 * @param {object} payload the hand-off's hydrolog-network/1
 * @param {boolean} empty whether the network has no node yet
 * @returns {{network: object, notes: string[]}} the network's values and the notes, in Polish
 */
function handedStep(network, payload, empty) {
  const words = texts.add;
  const step = typeof payload.timestep_min === "number" ? payload.timestep_min : null;
  if (step === null) return { network, notes: [] };
  const typed = String(network.timestep_min ?? "").trim();
  const own = parseNumber(typed);
  if (typed) {
    const same = Number.isFinite(own) && Math.abs(own - step) <= 1e-9 * step;
    return { network, notes: same ? [] : [t(words.stepKept, { network: typed, handoff: inputText(step) })] };
  }
  if (empty) return { network: { ...network, timestep_min: inputText(step) }, notes: [t(words.stepTaken, { handoff: inputText(step) })] };
  return { network, notes: [t(words.stepNone, { handoff: inputText(step) })] };
}

/**
 * „Dodaj zlewnię z Hydrografa” (plan 2026-11-10-network-editor, D10): Sieć's inputs with
 * the subcatchments of a hand-off added, unconnected, in the order of its document. Each
 * keeps its id unless the library would refuse it in the network (then its stem with the
 * first free number: `Z1` becomes `Z2`; edits.js freeId), stands on the free cell right of
 * the top row, is described by its own description or else the hand-off's subject, and
 * keeps its values (a subcatchment made from rainfall as Hydrogram zlewni reads a
 * hand-off's, handedInputs) and, as `origin` beside its structure, the hand-off's record.
 * The hand-off's outlet and its other nodes stay out. The network keeps its time step (one
 * without a step and without nodes takes the hand-off's). A rainfall of the hand-off (a
 * subcatchment's own, else the top one) becomes the node's own when the network's
 * rainfall differs, and „Jak w sieci” when it is the same (both compared as the network's
 * document writes them, rainfallOf; plan 2026-11-10-network-wizard, D10).
 *
 * @param {{network: object, skeleton: object[], nodes: Object<string, object>}} inputs
 *   Sieć's inputs
 * @param {object} doc the hand-off (readHandoff opened it; its payload is
 *   hydrolog-network/1)
 * @returns {{inputs: object, added: string[], lines: string[]}} the new inputs (the same
 *   when nothing was added), the ids added and what the addition did, in Polish: the
 *   first line says what was added, or why nothing was
 */
export function siecAddition(inputs, doc) {
  const words = texts.add;
  const payload = doc.payload;
  const nodes = (Array.isArray(payload.nodes) ? payload.nodes : []).filter(isObject);
  const subcatchments = nodes.filter((node) => node.type === "subcatchment");
  const skipped = nodes.filter((node) => node.type !== "subcatchment" && node.type !== "outlet").map((node) => String(node.id));
  const { network, notes } = handedStep(inputs.network, payload, !inputs.skeleton.length);
  const networkRainfall = rainfallOf(network);
  const top = isObject(payload.rainfall) ? payload.rainfall : null;
  const origin = addedOrigin(doc);
  const description = descriptionOf(doc.subject);
  let skeleton = inputs.skeleton;
  const values = { ...inputs.nodes };
  const added = [];
  const renamed = [];
  const rained = [];
  for (const node of subcatchments) {
    const cell = cellBeside(skeleton, null);
    if (!cell) break;
    const own = String(node.id);
    const id = freeId(skeleton, own, "subcatchment");
    const nodeVals = fromRainfall(node) ? { [VARIANT]: "rain", ...handedInputs(doc, node, networkRainfall) } : nodeValues(node);
    if (fromRainfall(node) && top && !isObject(node.rainfall) && nodeVals.rain_source !== "network") rained.push(id);
    if (id !== own && nodeVals[VARIANT] === "file" && !String(nodeVals.value_column ?? "").trim()) nodeVals.value_column = own;
    const made = { id, type: "subcatchment", from: null, position: { x: cell[0], y: cell[1] } };
    const text = typeof node.description === "string" && node.description.trim() ? node.description : description;
    if (text) made.description = text;
    made.origin = origin;
    skeleton = [...skeleton, made];
    values[id] = nodeVals;
    added.push(id);
    if (id !== own) renamed.push({ from: own, to: id });
  }
  if (!added.length) return { inputs, added, lines: [subcatchments.length ? words.full : words.none] };
  const producer = `${toolName(doc.producer.tool)} ${doc.producer.version}`;
  const lines = [
    t(words.added, { count: plural(added.length, words.forms), subject: doc.subject, producer, nodes: added.join(", ") }),
    ...renamed.map((item) => t(words.renamed, item)),
  ];
  if (added.length < subcatchments.length) lines.push(words.full);
  if (skipped.length) lines.push(t(words.skipped, { nodes: skipped.join(", ") }));
  lines.push(...notes);
  if (rained.length) lines.push(t(words.ownRainfall, { nodes: rained.join(", ") }));
  return { inputs: { ...inputs, network, skeleton, nodes: values }, added, lines };
}

/**
 * „Wczytaj z Hydrografa” in a subcatchment's panel of Sieć (plan
 * 2026-11-10-network-wizard, D10): Sieć's inputs with the subcatchment `id` filled from a
 * hand-off of one watershed (readHandoff gave the target "hydrogram"): its watershed,
 * runoff and rainfall as Hydrogram zlewni reads them (handedInputs), the rainfall „Jak w
 * sieci” when it equals the network's, else the node's own. The node keeps its id, links,
 * position and description, and the hand-off's record becomes its origin beside its
 * structure. The network keeps its time step, and a different one is said.
 *
 * @param {{network: object, skeleton: object[], nodes: Object<string, object>}} inputs
 *   Sieć's inputs
 * @param {string} id the subcatchment filled
 * @param {object} doc the hand-off
 * @returns {{inputs: object, lines: string[]}} the new inputs and what the fill did, in
 *   Polish: the first line says what was read
 */
export function siecFill(inputs, id, doc) {
  const payload = doc.payload;
  const sub = payload.nodes.find((node) => isObject(node) && node.type === "subcatchment");
  const values = { [VARIANT]: "rain", ...handedInputs(doc, sub, rainfallOf(inputs.network)) };
  const skeleton = inputs.skeleton.map((node) => (node.id === id ? { ...node, origin: addedOrigin(doc) } : node));
  const producer = `${toolName(doc.producer.tool)} ${doc.producer.version}`;
  const lines = [t(texts.fill.filled, { id, subject: doc.subject, producer }), ...handedStep(inputs.network, payload, false).notes];
  if (values.rain_source !== "network") lines.push(t(texts.fill.ownRainfall, { id }));
  return { inputs: { ...inputs, skeleton, nodes: { ...inputs.nodes, [id]: values } }, lines };
}
