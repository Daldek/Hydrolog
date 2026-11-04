// State of „Kalkulatory”: the sixteen calculators (the comparison of the methods of the time
// of concentration and fifteen catalog commands), their entries in the catalog, and the
// inputs kept under "hydrolog-gui/kalkulatory/2": the chosen calculator, the group and the
// search, the methods and the overland fields of the comparison, and each command's form
// (no results). A form opened for the first time is empty (outputDefaults), then filled
// with the fields of the watershed of Hydrogram zlewni when there is one.

import { api } from "../../api.js";
import { fold, inputText, parseNumber } from "../../format.js";
import { commandEntry, ONE_OF_KEY } from "../../forms/model.js";
import { useEffect, useState } from "../../html.js";
import { describeError } from "../../labels/errors.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { loadState } from "../../persist.js";
import { registerServed } from "../../ui/info.js";

/** The key of the section's inputs and the prefix of its run channels. */
export const SECTION = "kalkulatory";

/** The id of the comparison of the tc methods (its route: "#kalkulatory/porownanie-tc"). */
export const COMPARE = "porownanie-tc";

/** The command the comparison runs once per method. */
export const TC_COMMAND = "tc watershed";

/** The methods of `tc watershed`, in the catalog's order. */
export const TC_METHODS = Object.freeze(["kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"]);

/**
 * Methods that time the overland flow only (Hydrolog, `tc watershed`): their tc is not the
 * time of concentration of a watershed with a channel.
 */
export const OVERLAND_ONLY = Object.freeze(["faa", "kerby"]);

/** The watershed's fields of the overland flow, which the comparison lets a person set. */
export const OVERLAND_FIELDS = Object.freeze(["overland_length_km", "overland_slope_m_per_m", "runoff_coeff", "retardance"]);

/** The single-method command whose catalog entry describes each overland field. */
export const OVERLAND_SOURCE = Object.freeze({
  overland_length_km: "tc kerby-kirpich",
  overland_slope_m_per_m: "tc kerby-kirpich",
  runoff_coeff: "tc faa",
  retardance: "tc kerby-kirpich",
});

/** The calculators in the order of the list, each with its group. */
export const CALCULATORS = Object.freeze([
  { id: COMPARE, group: "tc" },
  { id: "tc kirpich", group: "tc", method: "kirpich" },
  { id: "tc nrcs", group: "tc", method: "nrcs" },
  { id: "tc giandotti", group: "tc", method: "giandotti" },
  { id: "tc kerby-kirpich", group: "tc", method: "kerby_kirpich" },
  { id: "tc faa", group: "tc", method: "faa" },
  { id: "tc kerby", group: "tc", method: "kerby" },
  { id: "cn lookup", group: "cn" },
  { id: "cn weighted", group: "cn" },
  { id: "scs effective", group: "cn" },
  { id: "precip hietogram", group: "precip" },
  { id: "uh scs", group: "uh" },
  { id: "uh nash", group: "uh" },
  { id: "uh snyder", group: "uh" },
  { id: "uh clark", group: "uh" },
  { id: "morphometry watershed", group: "morphometry" },
]);

/** The catalog commands of the calculators. */
export const COMMANDS = Object.freeze(CALCULATORS.filter((item) => item.id !== COMPARE).map((item) => item.id));

/** The groups of the list, in its order. */
export const GROUPS = Object.freeze(["tc", "cn", "precip", "uh", "morphometry"]);

/**
 * The options a calculator takes from the watershed of Hydrogram zlewni, as copies of its
 * fields (option: field). The six tc commands take what `tc watershed` itself derives from
 * the watershed (its `parameters`); `morphometry watershed` takes the whole watershed.
 */
export const FROM_WATERSHED = Object.freeze({
  "scs effective": { cn: "cn" },
  "uh scs": { area_km2: "area_km2" },
  "uh clark": { area_km2: "area_km2" },
  "uh snyder": { area_km2: "area_km2", length_km: "channel_length_km", centroid_length_km: "Lc_km" },
  "uh nash": {
    area_km2: "area_km2",
    lutz_length_km: "channel_length_km",
    lutz_centroid_length_km: "Lc_km",
    lutz_slope_m_per_m: "channel_slope_m_per_m",
    lutz_manning_n: "manning_n",
    lutz_urban_pct: "urban_pct",
    lutz_forest_pct: "forest_pct",
  },
});

/**
 * The inputs of a first visit: the comparison with all six methods, the overland fields of
 * the watershed, no form filled yet.
 *
 * @returns {{current: string, group: string, query: string, methods: Object<string, boolean>,
 *   overrides: Object<string, string>, values: Object<string, object>}} the state
 */
export function initialState() {
  return {
    current: COMPARE,
    group: "",
    query: "",
    methods: Object.fromEntries(TC_METHODS.map((method) => [method, true])),
    overrides: {},
    values: {},
  };
}

/**
 * A calculator by id.
 *
 * @param {string} id the calculator's id
 * @returns {object|null} the calculator
 */
export function calculatorOf(id) {
  return CALCULATORS.find((item) => item.id === id) || null;
}

/**
 * The route path of a calculator: ["porownanie-tc"] or the command's words.
 *
 * @param {string} id the calculator's id
 * @returns {string[]} the path
 */
export function pathOf(id) {
  return id === COMPARE ? [COMPARE] : id.split(" ");
}

/**
 * The calculator a route path names.
 *
 * @param {string[]} path the route's path
 * @returns {string|null} the calculator's id
 */
export function idOfPath(path) {
  const id = path.length === 1 ? path[0] : path.length === 2 ? `${path[0]} ${path[1]}` : null;
  return id && calculatorOf(id) ? id : null;
}

/**
 * What a search finds a calculator by: its name, keywords and the catalog's summary.
 *
 * @param {object} item a calculator
 * @param {object|null} doc its catalog document
 * @returns {string} the folded text
 */
export function searchText(item, doc) {
  const parts = [item.id, texts.keywords[item.id] || ""];
  if (item.id === COMPARE) parts.push(texts.compare.name, texts.compare.summary);
  const entry = doc ? commandEntry(doc) : null;
  if (entry) {
    const polish = (entry.i18n && entry.i18n.pl) || {};
    parts.push(polish.summary || "", entry.summary || "");
  }
  return fold(parts.join(" ").replace(/[_`-]/g, " "));
}

/**
 * The calculators a group and a search leave.
 *
 * @param {Map<string, object>} docs the catalog documents by command
 * @param {string} group a group, "" for all
 * @param {string} query the search's words
 * @returns {object[]} the calculators
 */
export function filterCalculators(docs, group, query) {
  const words = fold(query).replace(/[_-]/g, " ").split(/\s+/).filter(Boolean);
  return CALCULATORS.filter((item) => {
    if (group && item.group !== group) return false;
    const text = searchText(item, docs.get(item.id) || null);
    return words.every((word) => text.includes(word));
  });
}

/**
 * The catalog entries of the calculators' commands and of `tc watershed`, fetched once
 * each; a failed fetch is reported by command. The typical ranges `tc watershed` serves are
 * registered with the explanations of the six methods ("tc-<method>").
 *
 * @returns {{docs: Map<string, object>, errors: Map<string, string>}} the documents and the
 *   messages of the failures
 */
export function useCatalogDocs() {
  const [state, setState] = useState(() => ({ docs: new Map(), errors: new Map() }));
  useEffect(() => {
    let alive = true;
    for (const name of [...COMMANDS, TC_COMMAND]) {
      api
        .command(name)
        .then((doc) => {
          if (name === TC_COMMAND) registerServed(doc, (range) => (TC_METHODS.includes(range.method) ? `tc-${range.method}` : null));
          if (alive) setState((old) => ({ ...old, docs: new Map(old.docs).set(name, doc) }));
        })
        .catch((error) => {
          const message = error && error.doc ? describeError(error.doc).text : String((error && error.message) || error);
          if (alive) setState((old) => ({ ...old, errors: new Map(old.errors).set(name, message) }));
        });
    }
    return () => {
      alive = false;
    };
  }, []);
  return state;
}

/**
 * A number of Hydrolog as a person types it, without the noise of binary fractions
 * (105.89999999999998 gives "105,9").
 *
 * @param {number} value the number
 * @returns {string} the text of a field
 */
export function typed(value) {
  return inputText(Number(value.toPrecision(12)));
}

/**
 * The values a command's form takes from fields: numbers as typed, and for `uh nash` the
 * pane of Lutz when the watershed gives all of its members.
 *
 * @param {object} doc the command's catalog document
 * @param {Object<string, number>} found option values from the watershed
 * @returns {object} the values to merge into the form
 */
export function formFields(doc, found) {
  const values = {};
  for (const [name, value] of Object.entries(found)) if (typeof value === "number" && Number.isFinite(value)) values[name] = typed(value);
  const entry = commandEntry(doc);
  for (const [index, members] of (entry.one_of || []).entries()) {
    if (members.length > 1 && members.every((name) => Object.hasOwn(values, name))) values[ONE_OF_KEY] = index;
  }
  return values;
}

/**
 * The option values a command takes from a watershed by copying its fields.
 *
 * @param {string} command the command
 * @param {object|null} watershed the watershed of hydrolog-network/1
 * @returns {Object<string, number>|null} the values, null when the command takes none
 */
export function copiedFields(command, watershed) {
  const map = FROM_WATERSHED[command];
  if (!map || !watershed) return null;
  const found = {};
  for (const [option, field] of Object.entries(map)) if (typeof watershed[field] === "number") found[option] = watershed[field];
  return found;
}

/**
 * The watershed the comparison sends: Hydrogram's, with the overland fields set here.
 *
 * @param {object|null} watershed the watershed of Hydrogram zlewni
 * @param {Object<string, string>} overrides the overland fields as typed
 * @returns {object|null} the watershed of `tc watershed`
 */
export function comparedWatershed(watershed, overrides) {
  if (!watershed) return null;
  const merged = { ...watershed };
  for (const name of OVERLAND_FIELDS) {
    const value = parseNumber(overrides[name] ?? "");
    if (typeof value === "number" && Number.isFinite(value)) merged[name] = value;
  }
  return merged;
}

/**
 * The tc method Hydrogram zlewni uses now: its stored inputs (read only), when tc comes
 * from a method and the chosen unit hydrograph takes tc (SCS, Clark; none is chosen on a
 * first visit).
 *
 * @returns {string|null} the method, null when Hydrogram does not use one
 */
export function hydrogramMethod() {
  const stored = loadState("hydrogram", null);
  if (!stored || typeof stored !== "object" || stored.tc_manual) return null;
  if (!["scs", "clark"].includes(stored.uh_model)) return null;
  return TC_METHODS.includes(stored.tc_method) ? stored.tc_method : null;
}
