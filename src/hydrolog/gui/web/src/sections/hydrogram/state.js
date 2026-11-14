// State of „Hydrogram zlewni” (plan D9, D13; the author's three steps of 2026-11-04): the
// inputs of the steps Zlewnia, Hietogram and Hydrogram, kept in the browser under
// "hydrolog-gui/hydrogram/2" (inputs only, no results), what the chosen model needs
// (requirements), their checks (checkInputs: errors that stop a run, warnings that do not)
// and the options of `hydrograph generate` (toOptions). A first visit starts empty: no
// watershed, no storm, no model.
//
// PMAXTP (ADR-0018): the person gives the point (latitude and longitude, WGS84), the
// probability and the duration of IMGW-PIB's atlas and its method; the depth is never typed.
// `precip pmaxtp` fetches it (pmaxtpOptions), and the depth it gave is kept with the inputs
// as `pmaxtp_fetched` (the options it was fetched for, `depth_mm` and the providers' lines
// of the answer, `attribution` and `terms_notice`), so a reload shows it without fetching
// again; it is the `total_mm` of a run while the options are the same (pmaxtpDepth), and
// its lines go with the run (pmaxtpLines: a depth kept before the lines came, or handed
// off without them, takes PMAXTP's set of GET api/session).
//
// Nothing is required until a model is chosen in step 3; a value that is not a number or
// leaves the bounds of `watershed` of hydrolog-network-1.schema.json or of the catalog
// entries of `hydrograph generate` and `precip pmaxtp` (forms/model.js words them) is an
// error at once. Once a model is chosen, an empty field the model, its tc method or its
// rainfall reads is an error; Hydrolog's notices of a value outside its typical range
// stand on the field they name (`details.field`) as warnings, which never stop a run.
//
// The rainfall of step 2 is shared (plan 2026-11-10-network-wizard, D4): Sieć keeps its
// network's rainfall in the same inputs (initialRain), where `rain_source` also takes
// "none" („Brak”) and, for a subcatchment, "network" („Jak w sieci”), neither of which makes
// a rainfall of its own (hasOwnRainfall); rainRequirements, rainTexts, rainChecks and
// rainOptions are the parts of requirements, usedTexts, checkInputs and toOptions that
// concern it.
//
// Numbers are kept as typed (texts with a decimal comma or dot), as the generated forms
// keep them. `origin` is where the watershed came from (a file, a hand-off): {title,
// detail, label, mark, values}; a field that differs from `origin.values` is marked
// „zmieniono” with „przywróć”.

import { NO_LINES, hasLines, linesFields, linesOf, providerLines } from "../../attribution.js";
import { inputText, parseNumber } from "../../format.js";
import { commandEntry, fieldModel, parseSeries, validate, withReason } from "../../forms/model.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { describeNotice, isRangeNotice, noticeValue } from "../../labels/notices.js";

/** The key of the section's inputs and its route. */
export const SECTION = "hydrogram";

/** The channel of the section's runs (plan D6): a newer run replaces an older one. */
export const CHANNEL = "hydrogram";

/** The command the section runs. */
export const COMMAND = "hydrograph generate";

/** The schema whose `watershed` bounds the watershed's fields (plan D13). */
export const NETWORK_SCHEMA = "hydrolog-network-1.schema.json";

/**
 * Fields of the watershed in step 1, in the order of the panel. The channel's slope
 * (`channel_slope_m_per_m`) is not among them: no calculation reads it (Kirpich,
 * Kerby–Kirpich and Lutz take the longest flow path's), so a value that came with a
 * watershed stays in the inputs and is neither shown nor sent (plan
 * 2026-11-10-network-wizard, erratum of 2026-11-10).
 */
export const WATERSHED_STEP = Object.freeze([
  "area_km2",
  "cn",
  "perimeter_km",
  "length_km",
  "elevation_min_m",
  "elevation_max_m",
  "elevation_mean_m",
  "mean_slope_m_per_m",
  "channel_length_km",
  "flow_path_length_km",
  "flow_path_slope_m_per_m",
]);

/** Fields of the watershed only some models and tc methods read, shown in their block of step 3. */
const MODEL_FIELDS = Object.freeze([
  "Lc_km",
  "manning_n",
  "forest_pct",
  "urban_pct",
  "overland_length_km",
  "overland_slope_m_per_m",
  "runoff_coeff",
  "retardance",
]);

/** Every field of `watershed` the section keeps, in the order of WatershedParameters (and of a run). */
export const WATERSHED_FIELDS = Object.freeze([
  "name",
  "area_km2",
  "perimeter_km",
  "length_km",
  "elevation_min_m",
  "elevation_max_m",
  "elevation_mean_m",
  "mean_slope_m_per_m",
  "channel_length_km",
  "channel_slope_m_per_m",
  "flow_path_length_km",
  "flow_path_slope_m_per_m",
  "cn",
  ...MODEL_FIELDS,
  "source",
  "crs",
]);

/** The fields of `watershed` that hold texts. */
export const TEXT_FIELDS = new Set(["name", "source", "crs"]);

/** The field of `watershed` a watershed file must have (WatershedParameters). */
const WATERSHED_REQUIRED = Object.freeze(["area_km2"]);

/**
 * The fields of the watershed a hand-off carries (nogat-handoff/1): the full watershed
 * that Hydrograf produces and reads, whatever the chosen model reads.
 */
export const HANDOFF_FIELDS = Object.freeze(["area_km2", "perimeter_km", "length_km", "elevation_min_m", "elevation_max_m"]);

/**
 * The watershed fields Lutz's estimation of n and K needs (`nash_estimation` of `hydrograph
 * generate`): L and J of the main stream from the divide to the outlet, which are the
 * length and the slope of the longest flow path, then Lc and Manning's n.
 */
const LUTZ_FIELDS = Object.freeze(["flow_path_length_km", "Lc_km", "flow_path_slope_m_per_m", "manning_n"]);

/** The watershed fields of Nash by Lutz shown in its block (Lutz also reads the flow path of step 1). */
export const LUTZ_BLOCK = Object.freeze(["Lc_km", "manning_n", "forest_pct", "urban_pct"]);

/**
 * The watershed fields each tc method reads: those its source defines, with no substitute
 * (WatershedParameters.calculate_tc). Besides them every model needs the area, and NRCS's CN
 * is the losses' own.
 */
const TC_FIELDS = Object.freeze({
  kirpich: ["flow_path_length_km", "flow_path_slope_m_per_m"],
  nrcs: ["flow_path_length_km", "mean_slope_m_per_m"],
  giandotti: ["channel_length_km", "elevation_min_m", "elevation_mean_m"],
  faa: ["overland_length_km", "overland_slope_m_per_m", "runoff_coeff"],
  kerby: ["overland_length_km", "overland_slope_m_per_m", "retardance"],
  kerby_kirpich: ["overland_length_km", "overland_slope_m_per_m", "retardance", "flow_path_length_km", "flow_path_slope_m_per_m"],
});

/** The watershed fields of step 3 each tc method reads (the others are in step 1). */
export const TC_BLOCK = Object.freeze({
  kirpich: [],
  nrcs: [],
  giandotti: [],
  faa: ["overland_length_km", "overland_slope_m_per_m", "runoff_coeff"],
  kerby: ["overland_length_km", "overland_slope_m_per_m", "retardance"],
  kerby_kirpich: ["overland_length_km", "overland_slope_m_per_m", "retardance"],
});

/** Slopes in m/m, shown with a % hint (the author's choice: m/m with a % hint). */
export const SLOPE_FIELDS = new Set(["mean_slope_m_per_m", "flow_path_slope_m_per_m", "overland_slope_m_per_m"]);

/** Options sent as texts; every other option is a number. */
const TEXT_OPTIONS = new Set(["tc_method", "amc", "hietogram_type", "uh_model", "nash_estimation"]);

/** Options of `hydrograph generate` the section gives in another way (or not at all). */
const HIDDEN_OPTIONS = Object.freeze(["watershed", "watershed_file", "area_km2", "cn", "input_file", "value_column"]);

/** Units of the fields, as shown. */
export const UNITS = Object.freeze({
  area_km2: "km²",
  perimeter_km: "km",
  length_km: "km",
  elevation_min_m: texts.units.elevation,
  elevation_max_m: texts.units.elevation,
  elevation_mean_m: texts.units.elevation,
  mean_slope_m_per_m: "m/m",
  channel_length_km: "km",
  flow_path_length_km: "km",
  flow_path_slope_m_per_m: "m/m",
  Lc_km: "km",
  manning_n: "–",
  forest_pct: "%",
  urban_pct: "%",
  overland_length_km: "km",
  overland_slope_m_per_m: "m/m",
  runoff_coeff: "–",
  retardance: "–",
  cn: "–",
  tc_min: "min",
  total_mm: "mm",
  pmaxtp_latitude: "°",
  pmaxtp_longitude: "°",
  pmaxtp_depth: "mm",
  duration_min: "min",
  alpha: "–",
  beta: "–",
  peak_position: "–",
  timestep_min: "min",
  ia_coefficient: "–",
  nash_n: "–",
  nash_k_min: "min",
  clark_r_tc_ratio: "–",
  clark_r_min: "min",
  snyder_ct: "–",
  snyder_cp: "–",
});

/** The methods of tc (`tc_method`), in the catalog's order. */
export const TC_METHODS = Object.freeze(["kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"]);

/** The unit hydrograph models (`uh_model`). */
export const UH_MODELS = Object.freeze(["scs", "nash", "clark", "snyder"]);

/** The hyetograph types (`hietogram_type`). */
export const SHAPES = Object.freeze(["block", "triangular", "beta", "euler_ii"]);

/** The antecedent moisture conditions (`amc`). */
export const AMC = Object.freeze(["I", "II", "III"]);

/** The command that fetches the depth of PMAXTP for a point (ADR-0018). */
export const PMAXTP_COMMAND = "precip pmaxtp";

/** The channel of the PMAXTP fetches: a newer fetch replaces an older one, never a run. */
export const PMAXTP_CHANNEL = "hydrogram-pmaxtp";

/** Probabilities of PMAXTP [%], those of IMGW-PIB's tables (`precip pmaxtp`). */
export const PMAXTP_PROBABILITIES = Object.freeze([
  "0.01",
  "0.02",
  "0.03",
  "0.05",
  "0.1",
  "0.2",
  "0.3",
  "0.5",
  "1",
  "2",
  "3",
  "5",
  "10",
  "20",
  "30",
  "40",
  "50",
  "60",
  "70",
  "80",
  "90",
  "95",
  "98",
  "98.5",
  "99",
  "99.5",
  "99.9",
]);

/** Durations of PMAXTP [min], those of IMGW-PIB's tables (5 min to 72 h). */
export const PMAXTP_DURATIONS = Object.freeze([
  "5",
  "10",
  "15",
  "30",
  "45",
  "60",
  "90",
  "120",
  "180",
  "360",
  "720",
  "1080",
  "1440",
  "2160",
  "2880",
  "4320",
]);

/** The methods of PMAXTP: POT (Hydrolog's default, which IMGW-PIB recommends) and AMP. */
export const PMAXTP_METHODS = Object.freeze(["POT", "AMP"]);

/** The field of the panel that holds each option of `precip pmaxtp`. */
export const PMAXTP_FIELDS = Object.freeze({
  latitude: "pmaxtp_latitude",
  longitude: "pmaxtp_longitude",
  probability_percent: "pmaxtp_probability_pct",
  duration_min: "pmaxtp_duration_min",
  method: "pmaxtp_method",
});

/** The defaults of `peak_position` by hyetograph type (the catalog's description). */
export const PEAK_DEFAULTS = Object.freeze({ triangular: 0.5, euler_ii: 0.33 });

/** The fields of step 2 (Hietogram); every other field that is not the watershed's is step 3's. */
const RAIN_FIELDS = new Set([
  "pmaxtp_latitude",
  "pmaxtp_longitude",
  "pmaxtp_probability_pct",
  "pmaxtp_duration_min",
  "pmaxtp_method",
  "pmaxtp_depth",
  "total_mm",
  "duration_min",
  "values",
  "alpha",
  "beta",
  "peak_position",
  "timestep_min",
]);

/** The parts of the inputs a warning of a run belongs to: it stands while they are the run's. */
const SETTING = Object.freeze(["uh_model", "tc_manual", "tc_method", "nash_source", "clark_kind", "rain_source", "hietogram_type"]);

/** Snyder's L and Lc: the options `hydrograph generate` takes them as, by the watershed's field they come from. */
export const SNYDER_LENGTHS = Object.freeze({ snyder_length_km: "channel_length_km", snyder_centroid_length_km: "Lc_km" });

/**
 * The inputs of a first visit (and after „Wyczyść”): every field empty and no model
 * chosen; the choices that Hydrolog defaults (AMC II, tc by Kirpich) and the forms of
 * the rainfall and of the models' parameters are preset.
 *
 * @returns {object} the inputs
 */
export function initialState() {
  return {
    watershed: {},
    origin: null,
    tc_method: "kirpich",
    tc_manual: false,
    tc_min: "",
    ...initialRain(),
    amc: "II",
    ia_coefficient: "",
    uh_model: null,
    nash_source: "lutz",
    nash_n: "",
    nash_k_min: "",
    clark_kind: "ratio",
    clark_r_tc_ratio: "",
    clark_r_min: "",
    snyder_ct: "",
    snyder_cp: "",
  };
}

/**
 * The inputs of step 2 (Hietogram) of a first visit, and of a new network in Sieć: PMAXTP
 * with POT and nothing fetched, the Beta shape, every number empty, and the time step.
 *
 * @returns {object} the inputs of the rainfall and the time step
 */
export function initialRain() {
  return {
    rain_source: "pmaxtp",
    pmaxtp_latitude: "",
    pmaxtp_longitude: "",
    pmaxtp_probability_pct: "",
    pmaxtp_duration_min: "",
    pmaxtp_method: "POT",
    pmaxtp_fetched: null,
    total_mm: "",
    duration_min: "",
    hietogram_type: "beta",
    alpha: "",
    beta: "",
    peak_position: "",
    values: "",
    timestep_min: "",
  };
}

/**
 * Whether a value is a plain object (not an array, not null).
 *
 * @param {unknown} value the value
 * @returns {boolean} true for an object
 */
function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/**
 * Stored inputs completed with the first visit's for keys they lack. Snyder's L and Lc of
 * earlier visits (own fields then) move to the watershed's channel_length_km and Lc_km
 * when those are empty, else are dropped.
 *
 * @param {object|null} stored the stored inputs
 * @returns {object} the inputs
 */
export function normalize(stored) {
  const inputs = { ...initialState(), ...(isPlainObject(stored) ? stored : {}) };
  if (!isPlainObject(inputs.watershed)) inputs.watershed = {};
  for (const [option, name] of Object.entries(SNYDER_LENGTHS)) {
    if (!Object.hasOwn(inputs, option)) continue;
    if (!isEmpty(inputs[option]) && isEmpty(inputs.watershed[name])) {
      inputs.watershed = { ...inputs.watershed, [name]: String(inputs[option]) };
    }
    delete inputs[option];
  }
  if (!isPlainObject(inputs.origin)) inputs.origin = null;
  if (!UH_MODELS.includes(inputs.uh_model)) inputs.uh_model = null;
  if (!PMAXTP_METHODS.includes(inputs.pmaxtp_method)) inputs.pmaxtp_method = "POT";
  if (!isPlainObject(inputs.pmaxtp_fetched)) inputs.pmaxtp_fetched = null;
  return inputs;
}

/**
 * Whether a typed value is empty.
 *
 * @param {unknown} text the value
 * @returns {boolean} true for nothing, null or blank text
 */
export function isEmpty(text) {
  return text === undefined || text === null || String(text).trim() === "";
}

/**
 * Whether a unit hydrograph model uses tc (scs and clark do; nash and snyder do not).
 *
 * @param {string|null} model the `uh_model`
 * @returns {boolean} true when tc matters
 */
export function usesTc(model) {
  return model === "scs" || model === "clark";
}

/**
 * Whether Nash's n and K are estimated by Lutz from the watershed, in the run itself
 * (`nash_estimation` "lutz" of `hydrograph generate`).
 *
 * @param {object} inputs the inputs
 * @returns {boolean} true for Nash by Lutz
 */
export function usesLutz(inputs) {
  return inputs.uh_model === "nash" && inputs.nash_source !== "given";
}

/**
 * Whether the inputs make a rainfall of their own: PMAXTP, a design hyetograph or a series
 * of depths; not „Brak” of Sieć's network or „Jak w sieci” of a subcatchment in it.
 *
 * @param {object} inputs the inputs
 * @returns {boolean} true when `rain_source` is "pmaxtp", "design" or "series"
 */
export function hasOwnRainfall(inputs) {
  return inputs.rain_source === "pmaxtp" || inputs.rain_source === "design" || inputs.rain_source === "series";
}

/**
 * The duration of the design rainfall as typed or chosen [min], as text.
 *
 * @param {object} inputs the inputs
 * @returns {string} the duration
 */
export function rainDuration(inputs) {
  return inputs.rain_source === "pmaxtp" ? inputs.pmaxtp_duration_min : inputs.duration_min;
}

/**
 * The field of the panel that holds an option of `hydrograph generate`: under PMAXTP the
 * duration is its select and the depth the row of the fetched depth.
 *
 * @param {object} inputs the inputs
 * @param {string} option the option's name
 * @returns {string} the field
 */
export function optionField(inputs, option) {
  if (Object.hasOwn(SNYDER_LENGTHS, option)) return SNYDER_LENGTHS[option];
  if (inputs.rain_source !== "pmaxtp") return option;
  if (option === "duration_min") return "pmaxtp_duration_min";
  if (option === "total_mm") return "pmaxtp_depth";
  return option;
}

/**
 * The options of `precip pmaxtp` the inputs give: the point, the probability and the
 * duration as numbers once all four are given (their bounds are checkInputs'), and the
 * method.
 *
 * @param {object} inputs the inputs
 * @returns {{latitude: number, longitude: number, duration_min: number,
 *   probability_percent: number, method: string}|null} the options, null unless the rainfall
 *   is PMAXTP with its point, probability and duration given as numbers
 */
export function pmaxtpOptions(inputs) {
  if (inputs.rain_source !== "pmaxtp") return null;
  const latitude = numberOf(inputs.pmaxtp_latitude);
  const longitude = numberOf(inputs.pmaxtp_longitude);
  const duration = numberOf(inputs.pmaxtp_duration_min);
  const probability = numberOf(inputs.pmaxtp_probability_pct);
  if (latitude === null || longitude === null || duration === null || probability === null) return null;
  const method = PMAXTP_METHODS.includes(inputs.pmaxtp_method) ? inputs.pmaxtp_method : "POT";
  return { latitude, longitude, duration_min: duration, probability_percent: probability, method };
}

/**
 * The options of a PMAXTP fetch as one text, which tells two fetches apart.
 *
 * @param {object|null} options the options of `precip pmaxtp`, or a remembered fetch
 * @returns {string|null} the text, null without options
 */
export function pmaxtpKey(options) {
  if (!options) return null;
  const { latitude, longitude, duration_min: duration, probability_percent: probability, method } = options;
  return JSON.stringify([latitude, longitude, duration, probability, method || "POT"]);
}

/**
 * The PMAXTP depth of the inputs: the one remembered with them (`pmaxtp_fetched`) while it
 * was fetched for the same point, probability, duration and method.
 *
 * @param {object} inputs the inputs
 * @returns {number|null} the depth [mm], null when it is to be fetched or the rainfall is
 *   not PMAXTP
 */
export function pmaxtpDepth(inputs) {
  const fetched = inputs.pmaxtp_fetched;
  if (!isPlainObject(fetched) || typeof fetched.depth_mm !== "number" || !Number.isFinite(fetched.depth_mm)) return null;
  const key = pmaxtpKey(pmaxtpOptions(inputs));
  return key !== null && pmaxtpKey(fetched) === key ? fetched.depth_mm : null;
}

/**
 * What the inputs keep of a fetched depth (`pmaxtp_fetched`): the options it was fetched
 * for, the depth and the providers' lines of the answer.
 *
 * @param {object} options the options of `precip pmaxtp`
 * @param {number} depth the depth [mm]
 * @param {{attribution: string[], terms_notice: string[]}} [lines] the `attribution` and
 *   `terms_notice` of the answer (none for a depth handed off)
 * @returns {object} the record
 */
export function pmaxtpRecord(options, depth, lines = NO_LINES) {
  return { ...options, depth_mm: depth, ...linesFields(lines) };
}

/**
 * The providers' lines of the PMAXTP depth the inputs use (Nogat DEV-20.2): the lines
 * kept with it, else PMAXTP's set of GET api/session (a depth kept before the lines came,
 * or handed off).
 *
 * @param {object} inputs the inputs
 * @param {object|null} session hydrolog-gui-session/1, null while it has not arrived
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines, none when the
 *   rainfall uses no PMAXTP depth, null while the session they need is not known
 */
export function pmaxtpLines(inputs, session) {
  if (pmaxtpDepth(inputs) === null) return NO_LINES;
  const kept = linesOf(inputs.pmaxtp_fetched);
  return hasLines(kept) ? kept : providerLines(session, "pmaxtp");
}

/**
 * Read a watershed from a JSON document: WatershedParameters (as --watershed-file reads
 * it), or any object that holds one under `watershed` (the options of a run, a node of a
 * network). Unknown keys are left out, as WatershedParameters.from_dict leaves them.
 *
 * @param {unknown} doc the parsed JSON
 * @returns {{texts: object, values: object}|{missing: string[]}} the fields as typed text
 *   and as values, or the required fields the document lacks
 */
export function readWatershed(doc) {
  let source = doc;
  if (isPlainObject(source) && !("area_km2" in source) && isPlainObject(source.watershed)) source = source.watershed;
  if (!isPlainObject(source)) return { missing: [...WATERSHED_REQUIRED] };
  const missing = WATERSHED_REQUIRED.filter((name) => typeof source[name] !== "number");
  if (missing.length) return { missing };
  const fields = {};
  const values = {};
  for (const name of WATERSHED_FIELDS) {
    const value = source[name];
    if (TEXT_FIELDS.has(name)) {
      if (typeof value === "string" && value.trim()) {
        fields[name] = value;
        values[name] = value;
      }
    } else if (typeof value === "number" && Number.isFinite(value)) {
      fields[name] = inputText(value);
      values[name] = value;
    }
  }
  return { texts: fields, values };
}

/**
 * The watershed as `hydrograph generate` takes it: numbers parsed, texts trimmed, empty
 * fields left out, in the order of WATERSHED_FIELDS.
 *
 * @param {object|null} fields the watershed's fields as typed
 * @param {readonly string[]} [names] the fields to take (default: all)
 * @returns {object} the `watershed` of hydrolog-network/1
 */
export function watershedObject(fields, names = WATERSHED_FIELDS) {
  const out = {};
  for (const name of WATERSHED_FIELDS) {
    if (!names.includes(name)) continue;
    const text = fields ? fields[name] : undefined;
    if (isEmpty(text)) continue;
    out[name] = TEXT_FIELDS.has(name) ? String(text).trim() : parseNumber(text);
  }
  return out;
}

/**
 * The value of a field as a number (null when empty or not a number).
 *
 * @param {unknown} text the field as typed
 * @returns {number|null} the number
 */
export function numberOf(text) {
  const value = parseNumber(text);
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/**
 * The text of a field of the panel as typed: a field of the watershed or an input.
 *
 * @param {object} inputs the inputs
 * @param {string} name the field
 * @returns {unknown} its text
 */
function fieldText(inputs, name) {
  return WATERSHED_FIELDS.includes(name) ? (inputs.watershed || {})[name] : inputs[name];
}

/**
 * The number of the step a field of the panel is in.
 *
 * @param {string} name the field
 * @returns {1|2|3} the step
 */
export function stepOf(name) {
  if (name === "name" || WATERSHED_STEP.includes(name)) return 1;
  return RAIN_FIELDS.has(name) ? 2 : 3;
}

/**
 * The fields of the panel Dane now, in its order: step 1 (the watershed), step 2 (the
 * rainfall of the chosen source and shape) and step 3 (the chosen model's block, with
 * the watershed fields it and its tc method read, then the losses). Other models' fields
 * are not in the panel.
 *
 * @param {object} inputs the inputs
 * @returns {string[]} the fields
 */
export function panelFields(inputs) {
  const names = ["name", ...WATERSHED_STEP];
  if (inputs.rain_source === "series") {
    names.push("values");
  } else {
    if (inputs.rain_source === "pmaxtp") {
      names.push("pmaxtp_latitude", "pmaxtp_longitude", "pmaxtp_probability_pct", "pmaxtp_duration_min", "pmaxtp_method", "pmaxtp_depth");
    } else names.push("total_mm", "duration_min");
    if (inputs.hietogram_type === "beta") names.push("alpha", "beta");
    else if (Object.hasOwn(PEAK_DEFAULTS, inputs.hietogram_type)) names.push("peak_position");
  }
  names.push("timestep_min");
  const model = inputs.uh_model;
  if (usesTc(model)) {
    if (inputs.tc_manual) names.push("tc_min");
    else names.push(...(TC_BLOCK[inputs.tc_method] || []));
  }
  if (model === "clark") names.push(inputs.clark_kind === "r" ? "clark_r_min" : "clark_r_tc_ratio");
  if (model === "nash") {
    if (usesLutz(inputs)) names.push(...LUTZ_BLOCK);
    names.push("nash_n", "nash_k_min");
  }
  if (model === "snyder") names.push("Lc_km", "snyder_ct", "snyder_cp");
  names.push("ia_coefficient");
  return names;
}

/**
 * The fields of the watershed a run sends: those of step 1 and those of step 3 that the
 * chosen model and tc method read (with its name, source and CRS). A field another model
 * reads is not in the panel and is not sent.
 *
 * @param {object} inputs the inputs
 * @returns {string[]} the fields, in the order of WATERSHED_FIELDS
 */
export function sentFields(inputs) {
  const shown = new Set(panelFields(inputs));
  return WATERSHED_FIELDS.filter((name) => TEXT_FIELDS.has(name) || shown.has(name));
}

/**
 * The watershed a run sends (sentFields), parsed.
 *
 * @param {object} inputs the inputs
 * @returns {object} the `watershed` of hydrolog-network/1
 */
export function sentWatershed(inputs) {
  return watershedObject(inputs.watershed, sentFields(inputs));
}

/**
 * The fields of the watershed a hand-off needs that a run's watershed lacks.
 *
 * @param {object} watershed the watershed a run sent
 * @returns {string[]} the missing fields, in the order of HANDOFF_FIELDS
 */
export function handoffMissing(watershed) {
  return HANDOFF_FIELDS.filter((name) => !watershed || typeof watershed[name] !== "number");
}

/**
 * What the chosen setting needs: no model, nothing. A chosen model needs the area, CN
 * (the losses of every model), the rainfall of the chosen source, and its own inputs:
 * SCS and Clark tc (typed, or the fields its method's source defines, with no substitute:
 * Kirpich the length and the slope of the longest flow path, NRCS that length and the mean
 * slope of the watershed, Giandotti the length of the main channel, the lowest and the
 * mean elevation, FAA, Kerby and Kerby–Kirpich their overland fields, Kerby–Kirpich also
 * the longest flow path), Clark R or R/tc, Nash n and K or the fields of Lutz (the length
 * and the slope of the longest flow path, Lc and Manning's n), Snyder L and Lc of the
 * watershed (channel_length_km and Lc_km).
 *
 * @param {object} inputs the inputs
 * @returns {{model: string|null, required: Object<string, {purpose: string, or?:
 *   string[]}>}} the chosen model and the fields it needs, with whom they are needed for
 *   (a key of the labels' `requiredFor`)
 */
export function requirements(inputs) {
  const model = UH_MODELS.includes(inputs.uh_model) ? inputs.uh_model : null;
  const required = {};
  if (!model) return { model, required };
  const need = (name, purpose, or = []) => {
    if (!Object.hasOwn(required, name)) required[name] = or.length ? { purpose, or } : { purpose };
  };
  need("area_km2", model);
  need("cn", "losses");

  for (const [name, { purpose }] of Object.entries(rainRequirements(inputs))) need(name, purpose);

  if (usesTc(model) && inputs.tc_manual) need("tc_min", "tc_min");
  else if (usesTc(model)) {
    const method = TC_METHODS.includes(inputs.tc_method) ? inputs.tc_method : "kirpich";
    for (const name of TC_FIELDS[method]) need(name, method);
  }

  if (model === "clark") need(inputs.clark_kind === "r" ? "clark_r_min" : "clark_r_tc_ratio", "clark");
  if (model === "nash" && usesLutz(inputs)) for (const name of LUTZ_FIELDS) need(name, "lutz");
  if (model === "nash" && !usesLutz(inputs)) {
    need("nash_n", "nash");
    need("nash_k_min", "nash");
  }
  if (model === "snyder") {
    need("channel_length_km", "snyder");
    need("Lc_km", "snyder");
  }
  return { model, required };
}

/**
 * What the rainfall of the chosen source needs: a series its depths, PMAXTP the point, p and
 * the duration, a design hyetograph its depth and duration; „Brak” and „Jak w sieci” nothing.
 *
 * @param {object} inputs the inputs
 * @returns {Object<string, {purpose: string}>} the fields, with whom they are needed for (a
 *   key of the labels' `requiredFor`)
 */
export function rainRequirements(inputs) {
  const source = inputs.rain_source;
  const needs = (names, purpose) => Object.fromEntries(names.map((name) => [name, { purpose }]));
  if (source === "series") return needs(["values"], "series");
  if (source === "pmaxtp") return needs(["pmaxtp_latitude", "pmaxtp_longitude", "pmaxtp_probability_pct", "pmaxtp_duration_min"], "pmaxtp");
  if (source === "design") return needs(["total_mm", "duration_min"], "hietogram");
  return {};
}

/**
 * The words of whom a field is needed for: „metody Kirpicha”, „modelu SCS”.
 *
 * @param {string} purpose a key of the labels' `requiredFor`
 * @returns {string} the words
 */
export function purposeText(purpose) {
  return texts.requiredFor[purpose] || purpose;
}

/**
 * The name of a field as the panel shows it.
 *
 * @param {string} name the field
 * @returns {string} its label
 */
export function fieldLabel(name) {
  return texts.fields[name] ? texts.fields[name].label : name;
}

/**
 * A catalog-like entry of the watershed's fields from `watershed` of
 * hydrolog-network-1.schema.json: its types and bounds, so that forms/model.js checks and
 * words them as it does the catalog's options. None is required here: what a run needs
 * comes from requirements().
 *
 * @param {object} schema hydrolog-network-1.schema.json
 * @returns {{name: string, options: object[]}} the entry
 */
function watershedEntry(schema) {
  const definition = schema && schema.$defs ? schema.$defs.watershed : null;
  if (!definition || !definition.properties) throw new Error(`${NETWORK_SCHEMA}: no $defs.watershed`);
  const options = Object.entries(definition.properties).map(([name, property]) => {
    const option = {
      name,
      type: property.type === "number" || property.type === "integer" ? property.type : "string",
      required: false,
    };
    if (typeof property.exclusiveMinimum === "number") option.exclusive_minimum = property.exclusiveMinimum;
    if (typeof property.minimum === "number") option.min = property.minimum;
    if (typeof property.maximum === "number") option.max = property.maximum;
    return option;
  });
  return { name: "watershed", options };
}

/**
 * The model that checks the fields of PMAXTP: the catalog entry of `precip pmaxtp` (the
 * bounds of the point), none of them required here: what a run needs comes from
 * requirements().
 *
 * @param {object} commandDoc the catalog document of `precip pmaxtp`
 * @returns {object} the field model
 */
function pmaxtpModel(commandDoc) {
  const entry = commandEntry(commandDoc);
  return fieldModel({ ...entry, options: (entry.options || []).map((option) => ({ ...option, required: false })) });
}

/**
 * The models that check the inputs: the watershed's (from the network schema), the
 * options' (the catalog entry of `hydrograph generate`, without the options the section
 * gives in another way) and PMAXTP's (pmaxtpModel).
 *
 * @param {object} commandDoc the catalog document of `hydrograph generate`
 * @param {object} schema hydrolog-network-1.schema.json
 * @param {object} pmaxtpDoc the catalog document of `precip pmaxtp`
 * @returns {{watershed: object, options: object, pmaxtp: object}} the field models
 */
export function inputModels(commandDoc, schema, pmaxtpDoc) {
  return {
    watershed: fieldModel(watershedEntry(schema)),
    options: fieldModel(commandDoc, { hide: [...HIDDEN_OPTIONS] }),
    pmaxtp: pmaxtpModel(pmaxtpDoc),
  };
}

/**
 * The explanation (i) that shows a typical range Hydrolog serves for `hydrograph generate`:
 * the time step's, the tc method's, the losses', the unit hydrograph model's, or Lutz's
 * area (Nash's).
 *
 * @param {{method: string, parameter: string}} range a range of `typical_ranges`
 * @returns {string|null} the explanation's id, null for a range no explanation shows
 */
export function rangeInfoId(range) {
  if (range.parameter === "timestep_min") return "rain-timestep";
  if (TC_METHODS.includes(range.method)) return `tc-${range.method}`;
  if (range.method === "scs_cn_amc") return "losses-scs-cn";
  if (UH_MODELS.includes(range.method)) return `uh-${range.method}`;
  if (range.method === "lutz") return "uh-nash";
  return null;
}

/**
 * The options a setting sends, as typed: only those that apply to the chosen tc, rainfall,
 * shape and model (an option that does not apply is refused by the command); Nash by Lutz
 * sends `nash_estimation` instead of n and K.
 *
 * @param {object} inputs the inputs
 * @returns {Object<string, string>} the typed values by option name
 */
export function usedTexts(inputs) {
  const used = { amc: inputs.amc, ia_coefficient: inputs.ia_coefficient };
  if (usesTc(inputs.uh_model)) {
    if (inputs.tc_manual) used.tc_min = inputs.tc_min;
    else used.tc_method = inputs.tc_method;
  }
  Object.assign(used, rainTexts(inputs));
  used.timestep_min = inputs.timestep_min;
  if (inputs.uh_model) used.uh_model = inputs.uh_model;
  if (usesLutz(inputs)) {
    used.nash_estimation = "lutz";
  } else if (inputs.uh_model === "nash") {
    used.nash_n = inputs.nash_n;
    used.nash_k_min = inputs.nash_k_min;
  } else if (inputs.uh_model === "clark") {
    if (inputs.clark_kind === "r") used.clark_r_min = inputs.clark_r_min;
    else used.clark_r_tc_ratio = inputs.clark_r_tc_ratio;
  } else if (inputs.uh_model === "snyder") {
    const watershed = inputs.watershed || {};
    for (const [option, name] of Object.entries(SNYDER_LENGTHS)) used[option] = watershed[name];
    used.snyder_ct = inputs.snyder_ct;
    used.snyder_cp = inputs.snyder_cp;
  }
  return used;
}

/**
 * The options of `hydrograph generate` that make the rainfall of the inputs, as typed: a
 * series of depths, or the shape, the depth (PMAXTP's is the fetched one, never typed) and
 * the duration of a design storm with the shape's own parameters; nothing for „Brak” and
 * „Jak w sieci”. The time step is not among them: it is the run's, or the network's.
 *
 * @param {object} inputs the inputs
 * @returns {Object<string, string>} the typed values by option name
 */
export function rainTexts(inputs) {
  const used = {};
  if (inputs.rain_source === "series") {
    used.values = inputs.values;
  } else if (inputs.rain_source === "pmaxtp" || inputs.rain_source === "design") {
    used.hietogram_type = inputs.hietogram_type;
    // PMAXTP's depth is the fetched one, never typed
    used.total_mm = inputs.rain_source === "pmaxtp" ? inputText(pmaxtpDepth(inputs)) : inputs.total_mm;
    used.duration_min = rainDuration(inputs);
    if (inputs.hietogram_type === "beta") {
      used.alpha = inputs.alpha;
      used.beta = inputs.beta;
    } else if (Object.hasOwn(PEAK_DEFAULTS, inputs.hietogram_type)) {
      used.peak_position = inputs.peak_position;
    }
  }
  return used;
}

/**
 * The errors of the watershed's fields that hold a value: not a number, outside the
 * bounds of the network schema, or the highest elevation not above the lowest one.
 *
 * @param {object} watershed the watershed's fields as typed
 * @param {{watershed: object}} models from inputModels
 * @param {readonly string[]} [names] the fields to check (default: all)
 * @returns {Object<string, string>} a message by field name
 */
export function watershedErrors(watershed, models, names = WATERSHED_FIELDS) {
  const fields = {};
  for (const name of names) if (Object.hasOwn(watershed || {}, name)) fields[name] = watershed[name];
  const found = validate(models.watershed, fields);
  const low = numberOf(fields.elevation_min_m);
  const high = numberOf(fields.elevation_max_m);
  if (!found.elevation_max_m && !found.elevation_min_m && low !== null && high !== null && high <= low) {
    found.elevation_max_m = withReason(t(texts.relation.elevation, { value: inputText(low) }), "exclusive_minimum");
  }
  return found;
}

/**
 * The warnings a run's notices give the panel's fields: a value outside its typical range
 * on the field Hydrolog names (`details.field`; a range to be verified says so), λ other
 * than 0,2 on λ and a duration the time step does not divide on the duration.
 *
 * @param {object[]} notices the notices of hydrolog-result/1
 * @param {object} inputs the inputs of the run
 * @returns {Object<string, string>} a message by field name
 */
function noticeWarnings(notices, inputs) {
  const found = {};
  const add = (name, text, code) => {
    const message = withReason(text, code);
    found[name] = found[name] ? `${found[name]}; ${message}` : message;
  };
  for (const notice of notices || []) {
    const details = (notice && notice.details) || {};
    if (isRangeNotice(notice) && typeof details.field === "string") {
      const bounded = typeof details.minimum === "number" && typeof details.maximum === "number";
      const label = notice.code === "outside_unverified_range" ? texts.outOfRangeUnverified : texts.outOfRange;
      const text = bounded
        ? t(label, { minimum: noticeValue(details.minimum), maximum: noticeValue(details.maximum), method: details.method || "" })
        : describeNotice(notice).text;
      add(details.field, text, notice.code);
    } else if (notice.code === "ia_coefficient_nonstandard") {
      add("ia_coefficient", describeNotice(notice).text, notice.code);
    } else if (notice.code === "duration_not_covered") {
      add(optionField(inputs, "duration_min"), describeNotice(notice).text, notice.code);
    }
  }
  return found;
}

/**
 * Check the inputs (plan D13, the author's three steps): the watershed's fields in the
 * panel against the network schema, the options in use against the catalog and the point
 * of PMAXTP against `precip pmaxtp` (all at once, model or not), and, once a model is
 * chosen, every field it needs (requirements) and the relations Hydrolog refuses without
 * naming a field (the highest elevation above the lowest; Lutz's Lc not longer than L, the
 * longest flow path). The warnings are those of the newest run's notices on the fields
 * that still hold the run's values under the run's setting.
 *
 * @param {object} inputs the inputs
 * @param {{watershed: object, options: object, pmaxtp: object}} models from inputModels
 * @param {{inputs: object, notices: object[]}|null} [last] the newest run shown: its
 *   inputs and the notices of its result
 * @returns {{errors: Object<string, string>, warnings: Object<string, string>}} the
 *   messages by field name, in the order of the panel; no error means the inputs can run
 *   once a model is chosen (and, under PMAXTP, the depth is fetched: pmaxtpDepth)
 */
export function checkInputs(inputs, models, last = null) {
  const shown = panelFields(inputs);
  const found = { ...watershedErrors(inputs.watershed, models, sentFields(inputs)), ...pmaxtpErrors(inputs, models) };
  addOptionErrors(found, inputs, models, usedTexts(inputs));
  const { required } = requirements(inputs);
  const quoted = (other, name) => {
    const step = stepOf(other);
    return `„${fieldLabel(other)}”${step === stepOf(name) ? "" : t(texts.inStep, { step })}`;
  };
  for (const [name, { purpose, or }] of Object.entries(required)) {
    if (found[name] || !isEmpty(fieldText(inputs, name))) continue;
    const what = purposeText(purpose);
    const others = (or || []).map((other) => quoted(other, name));
    const text = others.length ? t(texts.requiredOr, { what, others: others.join(texts.orJoin) }) : t(texts.required, { what });
    found[name] = withReason(text, "required");
  }
  if (usesLutz(inputs) && !found.Lc_km && !found.flow_path_length_km) {
    const lc = numberOf((inputs.watershed || {}).Lc_km);
    const length = numberOf((inputs.watershed || {}).flow_path_length_km);
    if (lc !== null && length !== null && lc > length) {
      found.Lc_km = withReason(t(texts.relation.lutz, { value: inputText(length) }), "maximum");
    }
  }
  const warnings = {};
  if (last && Array.isArray(last.notices)) {
    const same = SETTING.every((key) => last.inputs[key] === inputs[key]);
    const words = same ? noticeWarnings(last.notices, last.inputs) : {};
    for (const [name, message] of Object.entries(words)) {
      if (found[name] || !shown.includes(name)) continue;
      if (String(fieldText(last.inputs, name) ?? "") === String(fieldText(inputs, name) ?? "")) warnings[name] = message;
    }
  }
  const rank = (name) => {
    const at = shown.indexOf(name);
    return at < 0 ? shown.length : at;
  };
  const ordered = (messages) => Object.fromEntries(Object.entries(messages).sort(([a], [b]) => rank(a) - rank(b)));
  return { errors: ordered(found), warnings: ordered(warnings) };
}

/**
 * The errors of PMAXTP's point, probability, duration and method against the catalog entry
 * of `precip pmaxtp`, when the rainfall is PMAXTP.
 *
 * @param {object} inputs the inputs
 * @param {{pmaxtp: object}} models from inputModels
 * @returns {Object<string, string>} a message by field name
 */
function pmaxtpErrors(inputs, models) {
  const found = {};
  if (inputs.rain_source !== "pmaxtp") return found;
  const typed = Object.fromEntries(Object.entries(PMAXTP_FIELDS).map(([option, name]) => [option, inputs[name]]));
  for (const [option, message] of Object.entries(validate(models.pmaxtp, typed))) found[PMAXTP_FIELDS[option]] = message;
  return found;
}

/**
 * Add the errors of options as typed, checked against the catalog entry of `hydrograph
 * generate`, to the fields of the panel that hold them (optionField), where those have
 * none yet.
 *
 * @param {Object<string, string>} found the messages by field name so far, extended
 * @param {object} inputs the inputs
 * @param {{options: object}} models from inputModels
 * @param {Object<string, string>} used the typed values by option name
 */
function addOptionErrors(found, inputs, models, used) {
  for (const [option, message] of Object.entries(validate(models.options, used))) {
    const name = optionField(inputs, option);
    if (!found[name]) found[name] = message;
  }
}

/**
 * Check a rainfall alone with checkInputs' rules (Sieć's network, plan
 * 2026-11-10-network-wizard, D4): PMAXTP's point, p, duration and method against `precip
 * pmaxtp`, the options of the rainfall against `hydrograph generate`, and every field the
 * chosen source needs (rainRequirements), at once: no model is waited for. The time step is
 * the host's own field.
 *
 * @param {object} inputs the inputs of the rainfall (initialRain)
 * @param {{options: object, pmaxtp: object}} models from inputModels
 * @returns {Object<string, string>} a message by field name, in the order of step 2
 */
export function rainChecks(inputs, models) {
  const found = pmaxtpErrors(inputs, models);
  addOptionErrors(found, inputs, models, rainTexts(inputs));
  for (const [name, { purpose }] of Object.entries(rainRequirements(inputs))) {
    if (!found[name] && isEmpty(inputs[name])) found[name] = withReason(t(texts.required, { what: purposeText(purpose) }), "required");
  }
  const order = [...RAIN_FIELDS];
  return Object.fromEntries(Object.entries(found).sort(([a], [b]) => order.indexOf(a) - order.indexOf(b)));
}

/**
 * The options of `hydrograph generate` for valid inputs (checked with checkInputs, a model
 * chosen).
 *
 * @param {object} inputs the inputs
 * @returns {object} the options
 */
export function toOptions(inputs) {
  return { watershed: sentWatershed(inputs), ...parsedOptions(usedTexts(inputs)) };
}

/**
 * The options of `hydrograph generate` that make the rainfall of the inputs (rainTexts),
 * as a run sends them.
 *
 * @param {object} inputs the inputs
 * @returns {object} the options, none for „Brak” and „Jak w sieci”
 */
export function rainOptions(inputs) {
  return parsedOptions(rainTexts(inputs));
}

/**
 * Typed options as a run sends them: numbers parsed, a series as its numbers, the texts of
 * choices as they are, and nothing for an empty one.
 *
 * @param {Object<string, string>} typed the typed values by option name
 * @returns {object} the options
 */
function parsedOptions(typed) {
  const options = {};
  for (const [name, text] of Object.entries(typed)) {
    if (isEmpty(text)) continue;
    if (name === "values") options.values = parseSeries(text).values;
    else if (TEXT_OPTIONS.has(name)) options[name] = String(text);
    else options[name] = parseNumber(text);
  }
  return options;
}

/** The options of the result's `uh_parameters`, by the name of their field in the panel. */
const UH_PARAMETERS = Object.freeze({
  nash_n: "n",
  nash_k_min: "k_min",
  clark_r_min: "r_min",
  snyder_ct: "ct",
  snyder_cp: "cp",
  snyder_length_km: "length_km",
  snyder_centroid_length_km: "centroid_length_km",
});

/**
 * The values the (i) explanations and the notes check against Hydrolog's ranges, by name:
 * the watershed's numbers and the numbers of the options in use; with a result, what it ran
 * with (the UH's parameters, λ, tc and the time step, defaults included) and the unit
 * hydrograph's time to peak, of which the time step's range is a share. Nash's n and K
 * that Lutz estimated are left out: as Hydrolog, the GUI checks only given ones against
 * their ranges.
 *
 * @param {object} inputs the inputs
 * @param {object|null} [result] the result of `hydrograph generate` for these inputs
 * @returns {Object<string, number>} the values
 */
export function checkedValues(inputs, result = null) {
  const values = {};
  const watershed = inputs.watershed || {};
  for (const name of WATERSHED_FIELDS) {
    if (TEXT_FIELDS.has(name)) continue;
    const value = numberOf(watershed[name]);
    if (value !== null) values[name] = value;
  }
  for (const [name, text] of Object.entries(usedTexts(inputs))) {
    if (TEXT_OPTIONS.has(name) || name === "values") continue;
    const value = numberOf(text);
    if (value !== null) values[name] = value;
  }
  if (result) {
    const parameters = result.uh_parameters || {};
    const estimated = result.nash_estimation === "lutz";
    for (const [name, key] of Object.entries(UH_PARAMETERS)) {
      if (estimated && (name === "nash_n" || name === "nash_k_min")) continue;
      if (typeof parameters[key] === "number") values[name] = parameters[key];
    }
    if (typeof result.ia_coefficient === "number") values.ia_coefficient = result.ia_coefficient;
    if (typeof result.tc_min === "number") values.tc_min = result.tc_min;
    // The step it ran with (5 min when left empty) and the quantity its range is a share of
    if (typeof result.timestep_min === "number") values.timestep_min = result.timestep_min;
    if (typeof result.uh_time_to_peak_min === "number") values.uh_time_to_peak_min = result.uh_time_to_peak_min;
  }
  return values;
}

/**
 * The value of an origin's field as typed text, or null when the origin has none.
 *
 * @param {object|null} origin the watershed's origin
 * @param {string} name the field
 * @returns {string|null} the text
 */
export function originText(origin, name) {
  if (!origin || !origin.values || !Object.hasOwn(origin.values, name)) return null;
  const value = origin.values[name];
  return typeof value === "number" ? inputText(value) : String(value);
}

/**
 * Whether a field differs from where the watershed came from.
 *
 * @param {object|null} origin the watershed's origin
 * @param {string} name the field
 * @param {unknown} text the field as typed
 * @returns {boolean} true when it was changed
 */
export function changedFrom(origin, name, text) {
  if (!origin || !origin.values) return false;
  const had = Object.hasOwn(origin.values, name) ? origin.values[name] : null;
  if (TEXT_FIELDS.has(name)) return (had || "") !== (isEmpty(text) ? "" : String(text).trim());
  const now = numberOf(text);
  if (had === null) return now !== null;
  return now === null || now !== had;
}
