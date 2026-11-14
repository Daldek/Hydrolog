/**
 * Units for people: the catalog's units ("km2", "m3/s") as shown ("km²", "m³/s"), and the
 * unit of a result field read from its name's suffix (DEV-8.2: "peak_discharge_m3s").
 */

/** Catalog unit -> its display form. */
export const UNITS = Object.freeze({
  km2: "km²",
  m2: "m²",
  ha: "ha",
  km: "km",
  cm: "cm",
  m: "m",
  mm: "mm",
  "m/m": "m/m",
  "m/s": "m/s",
  m3: "m³",
  "m3/s": "m³/s",
  "s/m^(1/3)": "s/m¹ᐟ³",
  min: "min",
  h: "h",
  s: "s",
  d: "d",
  "%": "%",
  years: "lat",
  deg: "°",
  "°C": "°C",
});

/** Shown for a dimensionless value. */
export const NO_UNIT = "–";

/** Suffixes of result field names and their display units, the longest first. */
export const SUFFIX_UNITS = Object.freeze([
  ["_m3s_per_mm", "m³/s na 1 mm"],
  ["_m3_per_s", "m³/s"],
  ["_m_per_m", "m/m"],
  ["_m_per_s", "m/s"],
  ["_mm_per_h", "mm/h"],
  ["_per_hour", "1/h"],
  ["_km2", "km²"],
  ["_m3s", "m³/s"],
  ["_percent", "%"],
  ["_pct", "%"],
  ["_min", "min"],
  ["_km", "km"],
  ["_cm", "cm"],
  ["_mm", "mm"],
  ["_m2", "m²"],
  ["_m3", "m³"],
  ["_ha", "ha"],
  ["_hours", "h"],
  ["_days", "d"],
  ["_c", "°C"],
  ["_h", "h"],
  ["_s", "s"],
  ["_m", "m"],
]);

/**
 * The display form of a catalog unit.
 *
 * @param {string|null|undefined} unit the catalog's unit, e.g. "km2"
 * @returns {string} e.g. "km²"; "–" without a unit
 */
export function unitLabel(unit) {
  if (!unit) return NO_UNIT;
  return Object.hasOwn(UNITS, unit) ? UNITS[unit] : unit;
}

/**
 * The unit of a result field from its name: "peak_discharge_m3s" gives "m³/s".
 *
 * @param {string} name the field's name
 * @returns {string|null} the display unit, null when the name has no unit suffix
 */
export function unitOfName(name) {
  const key = String(name);
  for (const [suffix, unit] of SUFFIX_UNITS) {
    if (key.endsWith(suffix) && key.length > suffix.length) return unit;
  }
  return null;
}

/** The unit of a station series' values by its parameter (`parameter` of a result). */
const PARAMETER_UNITS = Object.freeze({ Q: "m³/s", H: "cm", T: "°C" });

/**
 * Result fields in the unit of the series (PARAMETER_UNITS), by command, each with what
 * follows that unit ("·d" for a sum of daily deficits).
 */
const SERIES_FIELDS = Object.freeze({
  "stats characteristic": Object.freeze(
    Object.fromEntries(["wwx", "swx", "zwx", "nwx", "wsx", "ssx", "zsx", "nsx", "wnx", "snx", "znx", "nnx"].map((key) => [key, ""])),
  ),
  "stats low-flow-sequences": Object.freeze({ threshold: "", total_deficit: "·d" }),
});

/**
 * Units of result fields their names do not give, by command; null for a field whose
 * suffix would give a wrong one (a count of spells named "_days", the variance `var_s`).
 */
const FIELD_UNITS = Object.freeze({
  "hydrometrics rating-curve": Object.freeze({ std_residuals: "m³/s" }),
  "stats mann-kendall": Object.freeze({ var_s: null }),
  "stats regime": Object.freeze({ annual_mean: "m³/s", monthly_mean: "m³/s" }),
  "meteo spells": Object.freeze({ mean_spells_10_days: null, mean_spells_15_days: null, mean_spells_20_days: null }),
  "meteo temperature": Object.freeze({ growing_degree_days: "°C·d", heating_degree_days: "°C·d" }),
});

/**
 * The unit of a field of a command's result: the command's own (FIELD_UNITS), the
 * series' unit for a field in it (SERIES_FIELDS), else the name's suffix.
 *
 * @param {string} name the field's name
 * @param {string|null} [command] the command of the result
 * @param {string|null} [parameter] the result's parameter ("Q", "H", "T")
 * @returns {string|null} the display unit, null without one
 */
export function fieldUnit(name, command = null, parameter = null) {
  const own = command && Object.hasOwn(FIELD_UNITS, command) ? FIELD_UNITS[command] : null;
  if (own && Object.hasOwn(own, name)) return own[name];
  const series = command && Object.hasOwn(SERIES_FIELDS, command) ? SERIES_FIELDS[command] : null;
  if (series && Object.hasOwn(series, name)) {
    return parameter && Object.hasOwn(PARAMETER_UNITS, parameter) ? `${PARAMETER_UNITS[parameter]}${series[name]}` : null;
  }
  return unitOfName(name);
}
