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
  ["_pct", "%"],
  ["_min", "min"],
  ["_km", "km"],
  ["_mm", "mm"],
  ["_m2", "m²"],
  ["_m3", "m³"],
  ["_ha", "ha"],
  ["_hours", "h"],
  ["_days", "d"],
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
