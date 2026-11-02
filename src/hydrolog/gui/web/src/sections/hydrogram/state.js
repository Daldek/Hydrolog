// State of „Hydrogram zlewni” (plan D9, D13): the inputs of the five steps, kept in the
// browser under "hydrolog-gui/hydrogram/1" (inputs only, no results), their checks and
// the options of `hydrograph generate` (toOptions). The fields of `watershed` are checked
// against `watershed` of hydrolog-network-1.schema.json, the other options against the
// catalog entry of `hydrograph generate` (forms/model.js words both). A first visit opens
// the shipped example, examples/kamiennik.json (a WatershedParameters JSON, as
// --watershed-file reads it), with the mockup's rainfall, losses and model.
//
// Numbers are kept as typed (texts with a decimal comma or dot), as the generated forms
// keep them. `origin` is where the watershed came from (the example, a file, a hand-off):
// {title, detail, label, mark, values}; a field that differs from `origin.values` is
// marked „zmieniono” with „przywróć”.

import { inputText, parseNumber } from "../../format.js";
import { fieldModel, parseSeries, validate, withReason } from "../../forms/model.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";

/** The key of the section's inputs and its route. */
export const SECTION = "hydrogram";

/** The channel of the section's runs (plan D6): a newer run replaces an older one. */
export const CHANNEL = "hydrogram";

/** The command the section runs. */
export const COMMAND = "hydrograph generate";

/** The command that estimates Nash's n and K by Lutz (plan D13). */
export const LUTZ_COMMAND = "uh nash";

/** The shipped example, relative to the page. */
export const EXAMPLE_FILE = "examples/kamiennik.json";

/** The schema whose `watershed` bounds the watershed's fields (plan D13). */
export const NETWORK_SCHEMA = "hydrolog-network-1.schema.json";

/** Fields of the watershed in step 1, in the order of WatershedParameters. */
export const WATERSHED_MAIN = Object.freeze([
  "area_km2",
  "perimeter_km",
  "length_km",
  "elevation_min_m",
  "elevation_max_m",
  "elevation_mean_m",
  "mean_slope_m_per_m",
  "channel_length_km",
  "channel_slope_m_per_m",
]);

/** Fields of the watershed under „Parametry modeli i metod spływu”. */
export const WATERSHED_MORE = Object.freeze([
  "Lc_km",
  "manning_n",
  "forest_pct",
  "urban_pct",
  "overland_length_km",
  "overland_slope_m_per_m",
  "runoff_coeff",
  "retardance",
]);

/** Every field of `watershed` the section keeps, in the order a run sends them. */
export const WATERSHED_FIELDS = Object.freeze(["name", ...WATERSHED_MAIN, "cn", ...WATERSHED_MORE, "source", "crs"]);

/** The fields of `watershed` that hold texts. */
const TEXT_FIELDS = new Set(["name", "source", "crs"]);

/** The fields of `watershed` WatershedParameters cannot do without. */
const WATERSHED_REQUIRED = Object.freeze(["area_km2", "perimeter_km", "length_km", "elevation_min_m", "elevation_max_m"]);

/** The watershed fields Lutz's estimation of n and K reads (plan D13, `uh nash`). */
export const LUTZ_FIELDS = Object.freeze(["channel_length_km", "Lc_km", "channel_slope_m_per_m", "manning_n"]);

/** Slopes in m/m, shown with a % hint (the author's choice: m/m with a % hint). */
export const SLOPE_FIELDS = new Set(["mean_slope_m_per_m", "channel_slope_m_per_m", "overland_slope_m_per_m"]);

/** Options sent as texts; every other option is a number. */
const TEXT_OPTIONS = new Set(["tc_method", "amc", "hietogram_type", "uh_model"]);

/** Options of `hydrograph generate` the section gives in another way (or not at all). */
export const HIDDEN_OPTIONS = Object.freeze(["watershed", "watershed_file", "area_km2", "cn", "input_file", "value_column"]);

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
  channel_slope_m_per_m: "m/m",
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
  snyder_length_km: "km",
  snyder_centroid_length_km: "km",
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

/** Probabilities of PMAXTP [%], as the mockup offers them. */
export const PMAXTP_PROBABILITIES = Object.freeze(["0.5", "1", "2", "5", "10", "20", "50"]);

/** Durations of PMAXTP [min], as the mockup offers them (1 h to 72 h). */
export const PMAXTP_DURATIONS = Object.freeze(["60", "120", "180", "360", "720", "1440", "2880", "4320"]);

/** The defaults of `peak_position` by hyetograph type (the catalog's description). */
export const PEAK_DEFAULTS = Object.freeze({ triangular: 0.5, euler_ii: 0.33 });

/**
 * The inputs of a first visit: the mockup's Kamiennik run; the watershed itself comes
 * from the example file (null until it is read).
 *
 * @returns {object} the inputs
 */
export function initialState() {
  return {
    watershed: null,
    origin: null,
    tc_method: "kirpich",
    tc_manual: false,
    tc_min: "",
    rain_source: "pmaxtp",
    pmaxtp_probability_pct: "1",
    pmaxtp_duration_min: "720",
    total_mm: "105",
    duration_min: "720",
    hietogram_type: "beta",
    alpha: "2",
    beta: "5",
    peak_position: "",
    values: "",
    timestep_min: "10",
    amc: "II",
    ia_coefficient: "",
    uh_model: "scs",
    nash_source: "lutz",
    nash_n: "",
    nash_k_min: "",
    clark_kind: "ratio",
    clark_r_tc_ratio: "0,5",
    clark_r_min: "",
    snyder_length_km: "",
    snyder_centroid_length_km: "",
    snyder_ct: "",
    snyder_cp: "",
  };
}

/**
 * Stored inputs completed with the first visit's for keys they lack.
 *
 * @param {object|null} stored the stored inputs
 * @returns {object} the inputs
 */
export function normalize(stored) {
  const inputs = { ...initialState(), ...(stored && typeof stored === "object" ? stored : {}) };
  if (!inputs.watershed || typeof inputs.watershed !== "object" || Array.isArray(inputs.watershed)) inputs.watershed = null;
  if (!inputs.origin || typeof inputs.origin !== "object") inputs.origin = null;
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
 * @param {string} model the `uh_model`
 * @returns {boolean} true when tc matters
 */
export function usesTc(model) {
  return model === "scs" || model === "clark";
}

/**
 * Whether Nash's n and K come from Lutz's method (`uh nash`) before the run.
 *
 * @param {object} inputs the inputs
 * @returns {boolean} true for Nash by Lutz
 */
export function usesLutz(inputs) {
  return inputs.uh_model === "nash" && inputs.nash_source !== "given";
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
  if (source && typeof source === "object" && !Array.isArray(source) && !("area_km2" in source)) {
    if (source.watershed && typeof source.watershed === "object") source = source.watershed;
  }
  if (!source || typeof source !== "object" || Array.isArray(source)) return { missing: [...WATERSHED_REQUIRED] };
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
 * @returns {object} the `watershed` of hydrolog-network/1
 */
export function watershedObject(fields) {
  const out = {};
  for (const name of WATERSHED_FIELDS) {
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
 * A catalog-like entry of the watershed's fields from `watershed` of
 * hydrolog-network-1.schema.json: its types, bounds and required fields, so that
 * forms/model.js checks and words them as it does the catalog's options.
 *
 * @param {object} schema hydrolog-network-1.schema.json
 * @returns {{name: string, options: object[]}} the entry
 */
export function watershedEntry(schema) {
  const definition = schema && schema.$defs ? schema.$defs.watershed : null;
  if (!definition || !definition.properties) throw new Error(`${NETWORK_SCHEMA}: no $defs.watershed`);
  const required = new Set(definition.required || []);
  const options = Object.entries(definition.properties).map(([name, property]) => {
    const option = {
      name,
      type: property.type === "number" || property.type === "integer" ? property.type : "string",
      required: required.has(name),
    };
    if (typeof property.exclusiveMinimum === "number") option.exclusive_minimum = property.exclusiveMinimum;
    if (typeof property.minimum === "number") option.min = property.minimum;
    if (typeof property.maximum === "number") option.max = property.maximum;
    return option;
  });
  return { name: "watershed", options };
}

/**
 * The models that check the inputs: the watershed's (from the network schema) and the
 * options' (the catalog entry of `hydrograph generate`, without the options the section
 * gives in another way).
 *
 * @param {object} commandDoc the catalog document of `hydrograph generate`
 * @param {object} schema hydrolog-network-1.schema.json
 * @returns {{watershed: object, options: object}} the field models
 */
export function inputModels(commandDoc, schema) {
  return {
    watershed: fieldModel(watershedEntry(schema)),
    options: fieldModel(commandDoc, { hide: [...HIDDEN_OPTIONS] }),
  };
}

/**
 * The options a setting sends, as typed: only those that apply to the chosen tc, rainfall,
 * shape and model (an option that does not apply is refused by the command).
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
  if (inputs.rain_source === "series") {
    used.values = inputs.values;
  } else {
    used.hietogram_type = inputs.hietogram_type;
    used.total_mm = inputs.total_mm;
    used.duration_min = rainDuration(inputs);
    if (inputs.hietogram_type === "beta") {
      used.alpha = inputs.alpha;
      used.beta = inputs.beta;
    } else if (Object.hasOwn(PEAK_DEFAULTS, inputs.hietogram_type)) {
      used.peak_position = inputs.peak_position;
    }
  }
  used.timestep_min = inputs.timestep_min;
  used.uh_model = inputs.uh_model;
  if (inputs.uh_model === "nash" && !usesLutz(inputs)) {
    used.nash_n = inputs.nash_n;
    used.nash_k_min = inputs.nash_k_min;
  } else if (inputs.uh_model === "clark") {
    if (inputs.clark_kind === "r") used.clark_r_min = inputs.clark_r_min;
    else used.clark_r_tc_ratio = inputs.clark_r_tc_ratio;
  } else if (inputs.uh_model === "snyder") {
    const watershed = inputs.watershed || {};
    used.snyder_length_km = isEmpty(inputs.snyder_length_km) ? watershed.channel_length_km : inputs.snyder_length_km;
    used.snyder_centroid_length_km = isEmpty(inputs.snyder_centroid_length_km)
      ? watershed.Lc_km
      : inputs.snyder_centroid_length_km;
    used.snyder_ct = inputs.snyder_ct;
    used.snyder_cp = inputs.snyder_cp;
  }
  return used;
}

/**
 * The options that a setting needs although the catalog marks them optional.
 *
 * @param {object} inputs the inputs
 * @returns {string[]} their names
 */
function requiredNow(inputs) {
  const names = [];
  if (usesTc(inputs.uh_model) && inputs.tc_manual) names.push("tc_min");
  if (inputs.rain_source === "series") names.push("values");
  else names.push("total_mm", "duration_min");
  if (inputs.uh_model === "nash" && !usesLutz(inputs)) names.push("nash_n", "nash_k_min");
  if (inputs.uh_model === "clark") names.push(inputs.clark_kind === "r" ? "clark_r_min" : "clark_r_tc_ratio");
  if (inputs.uh_model === "snyder") names.push("snyder_length_km", "snyder_centroid_length_km");
  return names;
}

/** The fields in the order of the panel Dane, for the first problem the badge names. */
const PANEL_ORDER = Object.freeze([
  "name",
  ...WATERSHED_MAIN,
  ...WATERSHED_MORE,
  "tc_min",
  "total_mm",
  "duration_min",
  "values",
  "alpha",
  "beta",
  "peak_position",
  "timestep_min",
  "cn",
  "ia_coefficient",
  "nash_n",
  "nash_k_min",
  "clark_r_tc_ratio",
  "clark_r_min",
  "snyder_length_km",
  "snyder_centroid_length_km",
  "snyder_ct",
  "snyder_cp",
]);

/**
 * Check the inputs (plan D13): the watershed's fields against the network schema, the
 * options in use against the catalog, and what the chosen setting needs.
 *
 * @param {object} inputs the inputs
 * @param {{watershed: object, options: object}} models from inputModels
 * @returns {Object<string, string>} a message by field name, in the order of the panel;
 *   empty when the inputs can run
 */
export function checkInputs(inputs, models) {
  const found = {};
  const watershed = inputs.watershed || {};
  Object.assign(found, validate(models.watershed, watershed));
  const used = usedTexts(inputs);
  Object.assign(found, validate(models.options, used));
  for (const name of requiredNow(inputs)) {
    if (!found[name] && isEmpty(used[name])) {
      found[name] = withReason(t(texts.required, { what: texts.requiredFor[name] }), "required");
    }
  }
  if (usesLutz(inputs)) {
    for (const name of LUTZ_FIELDS) {
      if (!found[name] && isEmpty(watershed[name])) {
        found[name] = withReason(t(texts.required, { what: texts.requiredFor.lutz }), "required");
      }
    }
  }
  const rank = (name) => {
    const at = PANEL_ORDER.indexOf(name);
    return at < 0 ? PANEL_ORDER.length : at;
  };
  return Object.fromEntries(Object.entries(found).sort(([a], [b]) => rank(a) - rank(b)));
}

/**
 * The options of `hydrograph generate` for valid inputs (checked with checkInputs).
 *
 * @param {object} inputs the inputs
 * @param {{n: number, k_min: number}|null} [lutz] Nash's parameters by Lutz, when the
 *   model is Nash by Lutz
 * @returns {object} the options
 */
export function toOptions(inputs, lutz = null) {
  const options = { watershed: watershedObject(inputs.watershed) };
  for (const [name, text] of Object.entries(usedTexts(inputs))) {
    if (isEmpty(text)) continue;
    if (name === "values") options.values = parseSeries(text).values;
    else if (TEXT_OPTIONS.has(name)) options[name] = String(text);
    else options[name] = parseNumber(text);
  }
  if (usesLutz(inputs) && lutz) {
    options.nash_n = lutz.n;
    options.nash_k_min = lutz.k_min;
  }
  return options;
}

/**
 * The options of `uh nash` that estimate Nash's n and K by Lutz from the watershed.
 *
 * @param {object} inputs valid inputs of Nash by Lutz
 * @returns {object} the options
 */
export function lutzOptions(inputs) {
  const watershed = watershedObject(inputs.watershed);
  const options = {
    area_km2: watershed.area_km2,
    lutz_length_km: watershed.channel_length_km,
    lutz_centroid_length_km: watershed.Lc_km,
    lutz_slope_m_per_m: watershed.channel_slope_m_per_m,
    lutz_manning_n: watershed.manning_n,
  };
  if (watershed.forest_pct !== undefined) options.lutz_forest_pct = watershed.forest_pct;
  if (watershed.urban_pct !== undefined) options.lutz_urban_pct = watershed.urban_pct;
  const step = numberOf(inputs.timestep_min);
  if (step !== null) options.timestep_min = step;
  return options;
}

/** The watershed field each option of Lutz's `uh nash` run comes from. */
export const LUTZ_SOURCES = Object.freeze({
  area_km2: "area_km2",
  lutz_length_km: "channel_length_km",
  lutz_centroid_length_km: "Lc_km",
  lutz_slope_m_per_m: "channel_slope_m_per_m",
  lutz_manning_n: "manning_n",
  lutz_forest_pct: "forest_pct",
  lutz_urban_pct: "urban_pct",
  timestep_min: "timestep_min",
});

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
 * The values the (i) explanations and the notes check, by option name: the watershed's
 * numbers and the numbers of the options in use; with a result, what it ran with (the UH's
 * parameters, λ and tc, defaults included).
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
    for (const [name, key] of Object.entries(UH_PARAMETERS)) {
      if (typeof parameters[key] === "number") values[name] = parameters[key];
    }
    if (typeof result.ia_coefficient === "number") values.ia_coefficient = result.ia_coefficient;
    if (typeof result.tc_min === "number") values.tc_min = result.tc_min;
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
