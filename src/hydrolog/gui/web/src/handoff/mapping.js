// The mapping between the sections and hydrolog-network/1 (plan D15). „Hydrogram zlewni”
// writes the options of its shown run as one subcatchment made from rainfall and the
// outlet it flows to (route network computes such a node as `hydrograph generate` does,
// so the payload gives the same peak), with where its inputs came from (provenance: the
// PMAXTP point, method, probability and duration of the fetched depth, the watershed's
// source and the fields changed since, Lutz's estimate of Nash's n and K) and its result;
// back, a payload's subcatchment becomes the section's inputs, its source the watershed's
// origin and the hand-off's record (`handoff`) what the results compare with. „Sieć i
// trasowanie” writes its whole network with the outlet's result. Field names are
// Hydrolog's (channel_length_km; slopes in m/m); mapping Hydrograf's names is Hydrograf's
// side.

import { inputText, parseNumber, plural } from "../format.js";
import { t } from "../labels/common.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { hydrogram as hydrogramTexts } from "../labels/hydrogram.js";
import {
  LUTZ_FIELDS,
  PMAXTP_DURATIONS,
  PMAXTP_METHODS,
  PMAXTP_PROBABILITIES,
  changedFrom,
  initialState,
  normalize,
  pmaxtpOptions,
  pmaxtpRecord,
  readWatershed,
  sentFields,
  sentWatershed,
  usedTexts,
  usesLutz,
} from "../sections/hydrogram/state.js";
import { MARKS, PAYLOAD_SCHEMA, buildHandoff, momentText, receivedOf, toolName } from "./handoff.js";
import { canonical, isObject } from "./validate.js";

/** The id of Hydrogram's subcatchment and of its outlet in the payload (D15). */
export const SUBCATCHMENT_ID = "Z1";
export const OUTLET_ID = "OUT";

/** The time step of `hydrograph generate` and of a network that gives none [min]. */
export const DEFAULT_TIMESTEP_MIN = 5;

/** The options of `hydrograph generate` that make the node's `runoff`, in its order. */
const RUNOFF_OPTIONS = Object.freeze([
  "tc_min",
  "tc_method",
  "ia_coefficient",
  "amc",
  "uh_model",
  "nash_n",
  "nash_k_min",
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

/** Where Hydrogram's Nash parameters come from when Lutz estimated them. */
const LUTZ_ORIGIN = Object.freeze({ source: "hydrolog", command: "uh nash", method: "lutz" });

/**
 * The options of a run of `hydrograph generate` as hydrolog-network/1: one subcatchment
 * made from rainfall and the outlet.
 *
 * @param {object} options the options the run sent (with Lutz's n and K when it used them)
 * @param {string} [name] the network's name (the subject)
 * @returns {object} the payload
 */
export function hydrogramPayload(options, name) {
  const runoff = { model: "curve-number" };
  for (const option of RUNOFF_OPTIONS) if (options[option] !== undefined) runoff[option] = options[option];
  let rainfall;
  if (Array.isArray(options.values)) {
    rainfall = { kind: "series", depths_mm: [...options.values], timestep_min: options.timestep_min ?? DEFAULT_TIMESTEP_MIN };
  } else {
    rainfall = { kind: "design" };
    for (const option of DESIGN_OPTIONS) if (options[option] !== undefined) rainfall[option] = options[option];
  }
  const payload = { schema: PAYLOAD_SCHEMA };
  if (name) payload.name = name;
  if (options.timestep_min !== undefined) payload.timestep_min = options.timestep_min;
  payload.nodes = [
    { id: SUBCATCHMENT_ID, type: "subcatchment", watershed: { ...options.watershed }, runoff, rainfall },
    { id: OUTLET_ID, type: "outlet", from: [SUBCATCHMENT_ID] },
  ];
  return payload;
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
 * rainfall, the watershed and, for Nash by Lutz, the runoff; the other records of a
 * received hand-off while its data are unchanged.
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
  if (usesLutz(inputs)) provenance.runoff = { ...LUTZ_ORIGIN };
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
    payload: hydrogramPayload(run.options, subject),
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
 * The inputs of Hydrogram zlewni from a hand-off of one subcatchment (readHandoff gave
 * the target "hydrogram"): the watershed with its origin (the producer, its mark and the
 * watershed's provenance), tc, the rainfall, the losses and the unit hydrograph; every
 * other input as on a first visit. The rainfall is PMAXTP when the provenance names the
 * probability and the duration the section offers and a point (the rainfall's own, else
 * the watershed's, such as Hydrograf's outlet), else a design storm or the series. The
 * depth handed over is remembered as fetched only when the rainfall names its point;
 * otherwise the page fetches the depth of the point. `handoff` keeps what the results
 * compare with, the depth handed over included.
 *
 * @param {object} doc the hand-off
 * @returns {object} the inputs, a patch of the whole state
 */
export function hydrogramInputs(doc) {
  const payload = doc.payload;
  const provenance = isObject(doc.provenance) ? doc.provenance : {};
  const sub = payload.nodes.find((node) => node.type === "subcatchment");
  const runoff = sub.runoff;
  const rainfall = isObject(sub.rainfall) ? sub.rainfall : payload.rainfall;
  const read = readWatershed(sub.watershed);
  const watershed = { ...read.texts };
  const values = { ...read.values };
  const name = values.name || (typeof payload.name === "string" ? payload.name.trim() : "") || doc.subject;
  if (!watershed.name && name) {
    watershed.name = name;
    values.name = name;
  }
  const tool = doc.producer.tool;
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
  const inputs = {
    ...initialState(),
    watershed,
    origin: {
      label: toolName(tool),
      title: t(texts.origin.title, { producer: toolName(tool, true), subject: point || doc.subject }),
      detail: t(texts.origin.detail, {
        time: momentText(doc.created_at),
        fields: plural(Object.keys(values).length, hydrogramTexts.watershed.fieldForms),
      }),
      mark: MARKS.includes(tool) ? tool : null,
      values,
      provenance: where,
    },
  };
  inputs.tc_manual = typeof runoff.tc_min === "number";
  inputs.tc_min = inputText(runoff.tc_min);
  inputs.tc_method = runoff.tc_method || "kirpich";
  inputs.amc = runoff.amc || "II";
  inputs.ia_coefficient = inputText(runoff.ia_coefficient);
  inputs.uh_model = runoff.uh_model || "scs";
  const lutz =
    isObject(provenance.runoff) && provenance.runoff.method === "lutz" && LUTZ_FIELDS.every((field) => typeof sub.watershed[field] === "number");
  inputs.nash_source = inputs.uh_model === "nash" && !lutz ? "given" : "lutz";
  inputs.nash_n = lutz ? "" : inputText(runoff.nash_n);
  inputs.nash_k_min = lutz ? "" : inputText(runoff.nash_k_min);
  inputs.clark_kind = typeof runoff.clark_r_min === "number" ? "r" : "ratio";
  inputs.clark_r_min = inputText(runoff.clark_r_min);
  inputs.clark_r_tc_ratio = inputText(runoff.clark_r_tc_ratio);
  inputs.snyder_length_km = inputText(runoff.snyder_length_km);
  inputs.snyder_centroid_length_km = inputText(runoff.snyder_centroid_length_km);
  inputs.snyder_ct = inputText(runoff.snyder_ct);
  inputs.snyder_cp = inputText(runoff.snyder_cp);
  let handed = null;
  if (rainfall.kind === "series") {
    inputs.rain_source = "series";
    inputs.values = rainfall.depths_mm.map(inputText).join("; ");
    inputs.timestep_min = inputText(typeof payload.timestep_min === "number" ? payload.timestep_min : rainfall.timestep_min);
  } else {
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
    inputs.timestep_min = inputText(payload.timestep_min);
    if (pmaxtp) handed = pmaxtpRecord(pmaxtpOptions(normalize(inputs)), rainfall.total_mm);
    if (pmaxtp && own) inputs.pmaxtp_fetched = handed;
  }
  const opened = normalize({ ...inputs, pmaxtp_fetched: handed });
  inputs.handoff = { ...receivedOf(doc), key: dataKey(opened), rainfallKey: rainfallKey(opened) };
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
 * What Sieć keeps of a hand-off it opens: the record and its document as one text, to
 * tell whether the network was changed since.
 *
 * @param {object} doc the hand-off
 * @param {object} payload its network as Sieć opens it (session names of its files)
 * @returns {object} the record
 */
export function siecReceived(doc, payload) {
  return { ...receivedOf(doc), key: canonical(payload) };
}
