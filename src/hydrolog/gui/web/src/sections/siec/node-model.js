// The forms of the network's nodes in „Dane” (plan D9, S4), a pure module without Preact
// or the DOM. Fields, types, bounds, defaults and what is required come from
// hydrolog-network-1.schema.json: every node type and reach method is a branch of its
// `node`. The GUI adds the order of the fields, the alternatives the schema states in words
// (a channel by its section or by the wave's celerity, a cascade by K or by length and
// celerity, a storage table in the document or in a file) and the Polish labels and help
// (the catalog's Polish descriptions of the same options of `route <method>`). A property of
// the schema the GUI does not place goes under the node's more fields, so a new field
// shows without a change here. A subcatchment made from rainfall has no form here: its
// values are Hydrogram's inputs, entered in Hydrogram zlewni's three steps in its own panel
// and mapped to the document by handoff/mapping.js (plan 2026-11-10-network-wizard, D1,
// D3); neither is the network's own rainfall, Hydrogram's step 2 (D4). A subcatchment given
// its hydrograph („Podany”) or reading its column of the inflows file („Z pliku”) keeps its
// small form.
//
// A node's values here are what a person typed, flat by key: "muskingum.k_min" (a reach
// keeps the fields of each method apart, so switching methods back restores them),
// "initial_outflow_m3s", "value_column"; choices are keys starting with "#": "#variant" (a
// subcatchment: rain, file, given), "#method", "<method>.#section" and the like; tables are
// lists of rows of text.

import { auto, inputText, num, parseNumber } from "../../format.js";
import { fieldModel, toOptions, validate, withReason } from "../../forms/model.js";
import { t } from "../../labels/common.js";
import { reasonText } from "../../labels/errors.js";
import { siec as texts } from "../../labels/siec.js";
import { cellOf } from "./editor/geometry.js";
import { inflowRules } from "./editor/graph.js";

/** The longest description of a node or of the network [characters] (ADR-0023). */
export const MAX_DESCRIPTION_CHARS = 500;

/** The node types the forms know (hydrolog-network/1). */
export const KINDS = Object.freeze(["subcatchment", "reach", "reservoir", "junction", "outlet"]);

/** The routing methods of a reach. */
export const METHODS = Object.freeze(["lag", "muskingum", "muskingum-cunge", "cascade", "level-pool"]);

/** The ways a subcatchment brings its hydrograph; "rain" (from rainfall) by default. */
export const VARIANTS = Object.freeze(["rain", "file", "given"]);

/**
 * The way a subcatchment brings its hydrograph, by its values: "rain" unless it was
 * chosen otherwise.
 *
 * @param {object} values the node's values
 * @returns {"rain"|"file"|"given"} the variant
 */
export function variantOf(values) {
  return VARIANTS.includes(values["#variant"]) ? values["#variant"] : "rain";
}

/** The fields every routing element shares, under „Początek i koniec fali”. */
const WAVE = ["initial_outflow_m3s", "extend_min"];

/**
 * The fields of each routing method shown first, its alternatives (`choice`: a key and
 * groups of required and optional fields, or a table) and the fields after them.
 */
const LAYOUT = {
  lag: { main: ["lag_min"] },
  muskingum: { main: ["k_min", "x", "subreaches"] },
  "muskingum-cunge": {
    main: ["length_km", "slope_m_per_m"],
    choice: {
      key: "#section",
      groups: [
        { required: ["manning_n", "bottom_width_m"], optional: ["side_slope_m_per_m"] },
        { required: ["celerity_m_per_s", "top_width_m"] },
      ],
    },
    after: ["reference_discharge_m3s"],
  },
  cascade: {
    main: ["n"],
    choice: {
      key: "#k",
      groups: [{ required: ["k_min"] }, { required: ["length_km", "celerity_m_per_s"] }],
    },
  },
  "level-pool": {
    main: [],
    choice: {
      key: "#table",
      groups: [{ table: ["storage_m3", "outflow_m3s", "stage_m"] }, { required: ["rating_file"] }],
    },
    after: ["subreaches"],
  },
};

/** The catalog commands whose Polish descriptions are the help of the fields. */
export const HELP_COMMANDS = Object.freeze([
  "route lag",
  "route muskingum",
  "route muskingum-cunge",
  "route cascade",
  "route level-pool",
  "route network",
]);

/** Catalog units of fields whose names carry none. */
const NAMED_UNITS = { manning_n: "s/m^(1/3)" };

/** Name suffixes and their catalog units, the longest first. */
const SUFFIX_UNITS = [
  ["_m_per_m", "m/m"],
  ["_m_per_s", "m/s"],
  ["_km2", "km2"],
  ["_m3s", "m3/s"],
  ["_pct", "%"],
  ["_min", "min"],
  ["_km", "km"],
  ["_mm", "mm"],
  ["_m3", "m3"],
  ["_m", "m"],
];

/**
 * The catalog unit of a field from its name: "lag_min" gives "min", "slope_m_per_m" "m/m".
 *
 * @param {string} name the field's name
 * @returns {string|null} the unit, null for a dimensionless field
 */
function unitOf(name) {
  if (Object.hasOwn(NAMED_UNITS, name)) return NAMED_UNITS[name];
  for (const [suffix, unit] of SUFFIX_UNITS) {
    if (name.endsWith(suffix) && name.length > suffix.length) return unit;
  }
  return null;
}

/**
 * Follow a local `$ref` of the schema.
 *
 * @param {object} schema the whole schema
 * @param {object} node a part of it
 * @returns {object} the part referred to (the part itself without a reference)
 */
function resolve(schema, node) {
  let current = node || {};
  const seen = new Set();
  while (typeof current.$ref === "string" && current.$ref.startsWith("#/") && !seen.has(current.$ref)) {
    seen.add(current.$ref);
    current = current.$ref
      .slice(2)
      .split("/")
      .reduce((at, key) => (at && typeof at === "object" ? at[key] : undefined), schema) || {};
  }
  return current;
}

/**
 * The branches of the network schema the forms use.
 *
 * @param {object} schema hydrolog-network-1.schema.json
 * @returns {{network: {properties: object, required: string[]}, branches: object[]}} the
 *   network's own fields, and each node branch with its `type`, `method` (a reach) or
 *   `variant` (a subcatchment: "rain" or "given"), properties and required fields
 */
function readSchema(schema) {
  const defs = schema.$defs || {};
  const branchOf = (item) => ({
    properties: item.properties || {},
    required: Array.isArray(item.required) ? item.required : [],
  });
  const branches = (resolve(schema, defs.node).oneOf || []).map((item) => {
    const base = branchOf(item);
    const type = base.properties.type ? base.properties.type.const : null;
    const method = base.properties.method ? base.properties.method.const || null : null;
    let variant = null;
    if (type === "subcatchment") variant = base.required.includes("watershed") ? "rain" : "given";
    return { ...base, type, method, variant };
  });
  return { network: branchOf(schema), branches };
}

/**
 * The Polish help of a field: the GUI's own words for the part, else the catalog's
 * description of the same option in the part's commands.
 *
 * @param {Map<string, object>} docs catalog documents by command name
 * @param {string[]} commands the commands to look in, the first first
 * @param {string} part the part ("watershed", "reach", …), for the GUI's own words
 * @param {string} name the field's name
 * @returns {{description: string, enum: object}} the help and the meanings of its values
 */
function helpOf(docs, commands, part, name) {
  const own = texts.hints[part] && Object.hasOwn(texts.hints[part], name) ? texts.hints[part][name] : null;
  const shared = Object.hasOwn(texts.hints.any, name) ? texts.hints.any[name] : null;
  let description = own || shared || "";
  let meanings = {};
  for (const command of commands) {
    const doc = docs.get(command);
    const entry = doc && Array.isArray(doc.commands) ? doc.commands[0] : null;
    const option = entry ? (entry.options || []).find((item) => item.name === name) : null;
    if (!option) continue;
    const polish = (option.i18n && option.i18n.pl) || {};
    if (!description) description = polish.description || "";
    meanings = polish.enum || {};
    break;
  }
  return { description, enum: meanings };
}

/**
 * A field of a form from a property of the schema, through the catalog's form model
 * (forms/model.js), so it is shown and checked like an option of a command.
 *
 * @param {string} name the property's name
 * @param {object} property its JSON Schema
 * @param {boolean} required whether the schema requires it
 * @param {{description: string, enum: object}} help the Polish help
 * @param {string|null} label the GUI's label, null for the shared one
 * @returns {object} the field (fieldModel's)
 */
export function fieldOf(name, property, required, help, label) {
  const option = { name, required: Boolean(required) };
  const type = property.type;
  let bounds = property;
  if (type === "array") {
    const items = property.items || {};
    option.type = "array";
    option.items = items.type === "integer" ? "integer" : items.type === "number" ? "number" : "string";
    bounds = items;
  } else if (type === "number" || type === "integer" || type === "boolean") {
    option.type = type;
  } else {
    option.type = "string";
  }
  if (Array.isArray(property.enum)) option.enum = property.enum.map((value) => ({ value, meaning: "" }));
  if (typeof bounds.minimum === "number") option.min = bounds.minimum;
  if (typeof bounds.maximum === "number") option.max = bounds.maximum;
  if (typeof bounds.exclusiveMinimum === "number") option.exclusive_minimum = bounds.exclusiveMinimum;
  if (Object.hasOwn(property, "default")) option.default = property.default;
  const unit = unitOf(name);
  if (unit) option.unit = unit;
  option.i18n = { pl: { description: help.description, enum: help.enum } };
  const labels = label ? { [name]: label } : {};
  return fieldModel({ name: "siec", options: [option] }, { labels }).fields[0];
}

/**
 * A field that must have a value here, whatever the schema says (the chosen alternative).
 *
 * @param {object} field a field of fieldOf
 * @returns {object} the same field, required
 */
function needed(field) {
  return field.required ? field : { ...field, required: true };
}

/**
 * The forms of every node type from the schema and the catalog's help (a subcatchment
 * made from rainfall has none: Hydrogram's steps).
 *
 * @param {object} schema hydrolog-network-1.schema.json
 * @param {Map<string, object>} [docs] catalog documents of HELP_COMMANDS by name
 * @returns {object} the forms: `network`, `methods` (by method), `reservoir`, `given` (a
 *   subcatchment's own discharges and its column of the inflows file), each a map of
 *   fields by name with the schema's order, `run`, the options of `route network` the
 *   section sets (`inflows_file`, `time_column`), and `inflow`, the inflow rules
 */
export function buildForms(schema, docs = new Map()) {
  const read = readSchema(schema);
  const group = (branch, part, commands, skip = []) => {
    const fields = new Map();
    for (const [name, property] of Object.entries(branch.properties)) {
      if (skip.includes(name) || (property && Object.hasOwn(property, "const"))) continue;
      const label = texts.labels[part] && Object.hasOwn(texts.labels[part], name) ? texts.labels[part][name] : texts.labels.any[name] || null;
      fields.set(name, fieldOf(name, resolve(schema, property), branch.required.includes(name), helpOf(docs, commands, part, name), label));
    }
    return fields;
  };
  // the description and the position of a node or the network (ADR-0023) are not
  // parameters: the forms leave them out
  const structural = ["id", "type", "from", "method", "schema", "nodes", "description", "position"];
  const methods = {};
  for (const branch of read.branches) {
    if (branch.type === "reach" && branch.method) {
      methods[branch.method] = group(branch, "reach", [`route ${branch.method}`], structural);
    }
  }
  const reservoirBranch = read.branches.find((branch) => branch.type === "reservoir");
  const givenBranch = read.branches.find((branch) => branch.type === "subcatchment" && branch.variant === "given");
  const runHelp = (name) => helpOf(docs, ["route network"], "run", name).description;
  const run = fieldModel({
    name: "siec",
    options: [
      { name: "inflows_file", type: "string", path_role: "input", i18n: { pl: { description: runHelp("inflows_file") } } },
      { name: "time_column", type: "string", i18n: { pl: { description: runHelp("time_column") } } },
    ],
  }).fields;
  return {
    network: group(read.network, "network", [], structural.concat(["rainfall"])),
    methods,
    reservoir: reservoirBranch ? group(reservoirBranch, "reach", ["route level-pool"], structural) : new Map(),
    given: givenBranch ? group(givenBranch, "given", ["route lag"], structural) : new Map(),
    run: new Map(run.map((field) => [field.name, field])),
    inflow: inflowRules(schema),
  };
}

// --- values of a node -------------------------------------------------------------------

/**
 * A value of the document as a person types it: numbers with a decimal comma, lists of
 * numbers as a series ("0; 2,5; 5").
 *
 * @param {unknown} value a JSON value
 * @returns {string|boolean} the text (a boolean stays a boolean)
 */
function textOf(value) {
  if (typeof value === "number") return inputText(value);
  if (typeof value === "boolean") return value;
  if (Array.isArray(value)) return value.map((item) => (typeof item === "number" ? inputText(item) : String(item))).join("; ");
  if (value === null || value === undefined) return "";
  return String(value);
}

/**
 * Put an object's fields into values under a prefix.
 *
 * @param {object} values the values being filled
 * @param {string} prefix e.g. "muskingum."
 * @param {object} source the object
 * @param {string[]} [skip] fields left out
 */
function spread(values, prefix, source, skip = []) {
  for (const [name, value] of Object.entries(source || {})) {
    if (!skip.includes(name)) values[`${prefix}${name}`] = textOf(value);
  }
}

/**
 * The rows of a table from columns of the document.
 *
 * @param {Array<unknown[]|undefined>} columns the columns (a missing one is left empty)
 * @returns {string[][]} the rows as text
 */
function rowsOf(columns) {
  const length = Math.max(0, ...columns.map((column) => (Array.isArray(column) ? column.length : 0)));
  return Array.from({ length }, (_, index) =>
    columns.map((column) => (Array.isArray(column) && index < column.length ? textOf(column[index]) : "")),
  );
}

/**
 * The values of a routing element (a reach's method or a reservoir) from the document.
 *
 * @param {object} values the values being filled
 * @param {string} method the method ("level-pool" for a reservoir)
 * @param {object} node the document's node
 */
function elementValues(values, method, node) {
  const prefix = `${method}.`;
  const skip = ["id", "type", "from", "method", "description", "position", ...WAVE];
  for (const name of WAVE) if (Object.hasOwn(node, name)) values[name] = textOf(node[name]);
  if (method === "level-pool") {
    values[`${prefix}#table`] = typeof node.rating_file === "string" ? 1 : 0;
    values[`${prefix}#rows`] = rowsOf([node.storage_m3, node.outflow_m3s, node.stage_m]);
    skip.push("storage_m3", "outflow_m3s", "stage_m");
  } else if (method === "muskingum-cunge") {
    const byCelerity = Object.hasOwn(node, "celerity_m_per_s") || Object.hasOwn(node, "top_width_m");
    values[`${prefix}#section`] = byCelerity ? 1 : 0;
  } else if (method === "cascade") {
    const byLength = Object.hasOwn(node, "length_km") || Object.hasOwn(node, "celerity_m_per_s");
    values[`${prefix}#k`] = byLength ? 1 : 0;
  }
  spread(values, prefix, node, skip);
}

/**
 * The values of a node of the document that has a form here: a subcatchment given its
 * hydrograph (its table) or reading its column of the inflows file, a reach (its method's
 * fields), a reservoir; none for a junction and the outlet. A subcatchment made from
 * rainfall is handoff/mapping.js's (siecValues: Hydrogram's inputs).
 *
 * @param {object} node a node of hydrolog-network/1
 * @returns {object} its values
 */
export function nodeValues(node) {
  const values = {};
  if (node.type === "subcatchment") {
    if (Array.isArray(node.times_min) || Array.isArray(node.discharge_m3s)) {
      values["#variant"] = "given";
      values["#hydrograph"] = rowsOf([node.times_min, node.discharge_m3s]);
    } else {
      values["#variant"] = "file";
      if (typeof node.value_column === "string") values.value_column = node.value_column;
    }
  } else if (node.type === "reach") {
    const method = METHODS.includes(node.method) ? node.method : "lag";
    values["#method"] = method;
    elementValues(values, method, node);
  } else if (node.type === "reservoir") {
    elementValues(values, "level-pool", node);
  }
  return values;
}

/**
 * The structure of a network: each node's id, type, inflows, the cell of its position
 * when it is one, and its description (plan 2026-11-10-network-editor, D3).
 *
 * @param {object} doc hydrolog-network/1
 * @returns {Array<{id: string, type: string, from: string[]|null,
 *   position?: {x: number, y: number}, description?: string}>} the nodes in document
 *   order; `from` is null where the document has none or an empty list, `position` is
 *   left out where it is missing or invalid, `description` where it is not a string
 */
export function skeletonOf(doc) {
  return (doc.nodes || []).map((node) => {
    const made = {
      id: String(node.id),
      type: String(node.type),
      from: Array.isArray(node.from) && node.from.length ? node.from.map(String) : null,
    };
    const cell = cellOf(node.position);
    if (cell) made.position = { x: cell[0], y: cell[1] };
    if (typeof node.description === "string") made.description = node.description;
    return made;
  });
}

/**
 * The problem of a description (D3) as the library would refuse it: more than
 * MAX_DESCRIPTION_CHARS characters, or a control character other than the line feed. A
 * blank description is no problem here: it is left out of the document.
 *
 * @param {string|undefined} text the description
 * @returns {string|null} the message with its reason, null when it can be written
 */
export function descriptionProblem(text) {
  if (typeof text !== "string" || !text.trim()) return null;
  const length = [...text].length;
  if (length > MAX_DESCRIPTION_CHARS) return withReason(t(texts.descriptionProblems.too_long, { length }), "too_long");
  if (/[\u0000-\u0009\u000b-\u001f\u007f-\u009f]/u.test(text)) return withReason(texts.descriptionProblems.control_character, "control_character");
  return null;
}

/**
 * A network document without what changes no computation (plan 2026-11-10-network-editor,
 * D3, D11): the nodes' positions and descriptions and the network's description. The key
 * that marks a result stale is made of it, and Hydrolog lays it out anew.
 *
 * @param {object} document hydrolog-network/1
 * @returns {object} the document without them
 */
export function withoutPicture(document) {
  const { description: _network, ...rest } = document;
  return { ...rest, nodes: document.nodes.map(({ position: _cell, description: _text, ...node }) => node) };
}

// --- what a form shows ---------------------------------------------------------------

/**
 * A slot of a form: a field and the key of its value.
 *
 * @typedef {{key: string, field: object}} Slot
 */

/**
 * Slots of named fields of a group, in the given order, skipping fields the group lacks.
 *
 * @param {Map<string, object>} fields the group's fields
 * @param {string[]} names the names
 * @param {string} prefix the prefix of the keys
 * @param {boolean} [required] make them required
 * @returns {Slot[]} the slots
 */
function slots(fields, names, prefix, required = false) {
  return names
    .filter((name) => fields.has(name))
    .map((name) => ({ key: `${prefix}${name}`, field: required ? needed(fields.get(name)) : fields.get(name) }));
}

/**
 * The slots of the fields of a group not named in `placed`, required ones first.
 *
 * @param {Map<string, object>} fields the group's fields
 * @param {string[]} placed the names placed elsewhere
 * @param {string} prefix the prefix of the keys
 * @returns {Slot[]} the slots
 */
function rest(fields, placed, prefix) {
  const left = [...fields.keys()].filter((name) => !placed.includes(name));
  return slots(fields, left, prefix);
}

/**
 * The parts of a routing element (a reach by a method, or a reservoir).
 *
 * @param {Map<string, object>} fields the method's fields
 * @param {string} method the method ("level-pool" for a reservoir)
 * @param {object} values the node's values
 * @returns {{main: Slot[], choice: object|null, chosen: Slot[], table: object|null,
 *   after: Slot[], wave: Slot[], more: Slot[]}} the slots in the order shown
 */
function elementParts(fields, method, values) {
  const layout = LAYOUT[method] || { main: [] };
  const prefix = `${method}.`;
  const placed = [...layout.main, ...(layout.after || []), ...WAVE];
  let choice = null;
  let chosen = [];
  let table = null;
  if (layout.choice) {
    const key = `${prefix}${layout.choice.key}`;
    const groups = layout.choice.groups;
    const index = Number.isInteger(values[key]) && values[key] >= 0 && values[key] < groups.length ? values[key] : 0;
    choice = { key, count: groups.length, value: index, id: layout.choice.key };
    for (const item of groups) placed.push(...(item.required || []), ...(item.optional || []), ...(item.table || []));
    const group = groups[index];
    chosen = [...slots(fields, group.required || [], prefix, true), ...slots(fields, group.optional || [], prefix)];
    if (group.table) {
      table = {
        key: `${prefix}#rows`,
        columns: group.table.filter((name) => fields.has(name)).map((name) => ({ name, field: fields.get(name) })),
      };
    }
  }
  const wave = WAVE.filter((name) => fields.has(name)).map((name) => ({ key: name, field: fields.get(name) }));
  const required = rest(fields, placed, prefix).filter((slot) => slot.field.required);
  const optional = rest(fields, placed, prefix).filter((slot) => !slot.field.required);
  return {
    main: [...slots(fields, layout.main, prefix), ...required],
    choice,
    chosen,
    table,
    after: slots(fields, layout.after || [], prefix),
    wave,
    more: optional,
  };
}

/**
 * What the form of a node shows now: its choices, its slots by part, and its tables; a
 * subcatchment made from rainfall only its variant (its data are Hydrogram's steps).
 *
 * @param {object} forms the forms of buildForms
 * @param {{id: string, type: string, from: string[]|null}} node the node's structure
 * @param {object} values the node's values
 * @returns {object} the layout: `kind`, and per kind its parts (see the form component)
 */
export function nodeLayout(forms, node, values) {
  if (node.type === "subcatchment") {
    const variant = variantOf(values);
    const layout = { kind: "subcatchment", variant };
    if (variant === "file") {
      layout.file = slots(forms.given, ["value_column"], "");
    } else if (variant === "given") {
      layout.table = {
        key: "#hydrograph",
        columns: ["times_min", "discharge_m3s"]
          .filter((name) => forms.given.has(name))
          .map((name) => ({ name, field: forms.given.get(name) })),
      };
    }
    return layout;
  }
  if (node.type === "reach" || node.type === "reservoir") {
    const method = node.type === "reservoir" ? "level-pool" : METHODS.includes(values["#method"]) ? values["#method"] : "lag";
    const fields = node.type === "reservoir" ? forms.reservoir : forms.methods[method] || new Map();
    return { kind: node.type, method, ...elementParts(fields, method, values) };
  }
  return { kind: node.type };
}

/**
 * Every slot of a layout that is shown, checked and sent.
 *
 * @param {object} layout a layout of nodeLayout
 * @returns {Slot[]} the slots
 */
function layoutSlots(layout) {
  const found = [];
  if (layout.kind === "subcatchment") {
    if (layout.file) found.push(...layout.file);
  } else if (layout.kind === "reach" || layout.kind === "reservoir") {
    found.push(...layout.main, ...layout.chosen, ...layout.after, ...layout.wave, ...layout.more);
  }
  return found;
}

// --- checks and the document -----------------------------------------------------------

/**
 * The message of one slot's value, or null when it is fine (forms/model.js's checks).
 *
 * @param {Slot} slot the slot
 * @param {unknown} value its value
 * @returns {string|null} the message with its reason
 */
function slotProblem(slot, value) {
  const name = slot.field.name;
  const found = validate({ fields: [slot.field], oneOf: null }, { [name]: value });
  return found[name] || null;
}

/**
 * The problems of a table: numbers in every cell of a required column, the columns' own
 * bounds, the order the schema asks for, and at least one row.
 *
 * @param {{key: string, columns: Array<{name: string, field: object}>}} table the table
 * @param {string[][]|undefined} rows its rows
 * @param {"increasing"|"nondecreasing"} order the order of the first column ("increasing"
 *   for times, "nondecreasing" for a storage table, whose every column is non-decreasing)
 * @returns {string|null} the first problem, null when the table is fine
 */
function tableProblem(table, rows, order) {
  const list = Array.isArray(rows) ? rows.filter((row) => row.some((cell) => String(cell ?? "").trim() !== "")) : [];
  if (!list.length) return withReason(texts.table.empty, "required");
  const columns = table.columns;
  const parsed = columns.map(() => []);
  for (let at = 0; at < list.length; at += 1) {
    for (let column = 0; column < columns.length; column += 1) {
      const text = String(list[at][column] ?? "").trim();
      const optional = !columns[column].field.required && column > 1;
      if (text === "") {
        if (optional) {
          parsed[column].push(null);
          continue;
        }
        return withReason(t(texts.table.missing, { row: at + 1, column: columns[column].name }), "required");
      }
      const value = parseNumber(text);
      if (value === null || Number.isNaN(value)) {
        return withReason(t(texts.table.notNumber, { row: at + 1, column: columns[column].name, text }), "type");
      }
      const field = columns[column].field;
      const bound = reasonFor(field, value);
      if (bound) return withReason(t(texts.table.cell, { row: at + 1, column: columns[column].name, message: bound.text }), bound.reason);
      parsed[column].push(value);
    }
  }
  for (let column = 2; column < columns.length; column += 1) {
    const given = parsed[column].filter((value) => value !== null).length;
    if (given && given < list.length) {
      return withReason(t(texts.table.partial, { column: columns[column].name }), "required");
    }
  }
  for (let column = 0; column < columns.length; column += 1) {
    if (order === "increasing" && column > 0) break;
    const values = parsed[column];
    for (let at = 1; at < values.length; at += 1) {
      if (values[at] === null || values[at - 1] === null) continue;
      const wrong = order === "increasing" ? values[at] <= values[at - 1] : values[at] < values[at - 1];
      if (wrong) {
        const text = order === "increasing" ? texts.table.increasing : texts.table.nondecreasing;
        return withReason(t(text, { row: at + 1, column: columns[column].name }), "order");
      }
    }
  }
  return null;
}

/**
 * A broken bound of a field's value, in words.
 *
 * @param {object} field the field
 * @param {number} value the value
 * @returns {{text: string, reason: string}|null} the problem
 */
function reasonFor(field, value) {
  if (field.exclusiveMinimum !== null && !(value > field.exclusiveMinimum)) {
    return { reason: "exclusive_minimum", text: reasonText("exclusive_minimum", { exclusive_minimum: field.exclusiveMinimum, value }) };
  }
  if (field.min !== null && value < field.min) return { reason: "minimum", text: reasonText("minimum", { minimum: field.min, value }) };
  if (field.max !== null && value > field.max) return { reason: "maximum", text: reasonText("maximum", { maximum: field.max, value }) };
  return null;
}

/**
 * The problems of a node's values by key (empty when the node is complete).
 *
 * @param {object} forms the forms of buildForms
 * @param {{id: string, type: string}} node the node's structure
 * @param {object} values the node's values
 * @returns {Object<string, string>} messages by value key
 */
export function nodeProblems(forms, node, values) {
  const layout = nodeLayout(forms, node, values);
  const found = {};
  for (const slot of layoutSlots(layout)) {
    const message = slotProblem(slot, values[slot.key]);
    if (message) found[slot.key] = message;
  }
  if (layout.table) {
    const order = layout.kind === "subcatchment" ? "increasing" : "nondecreasing";
    const message = tableProblem(layout.table, values[layout.table.key], order);
    if (message) found[layout.table.key] = message;
  }
  return found;
}

/**
 * The JSON values of slots: the typed text converted to the schema's types, nothing for
 * an empty field.
 *
 * @param {Slot[]} list the slots
 * @param {object} values the values
 * @param {string} prefix the prefix to strip from the keys
 * @returns {object} the fields by name
 */
function jsonOf(list, values, prefix) {
  const fields = list.filter((slot) => slot.key.startsWith(prefix));
  const named = {};
  for (const slot of fields) named[slot.field.name] = values[slot.key];
  return toOptions({ fields: fields.map((slot) => slot.field), oneOf: null }, named);
}

/**
 * The columns of a table as lists of numbers, an optional column left out when empty.
 *
 * @param {{columns: Array<{name: string}>}} table the table
 * @param {string[][]} rows its rows
 * @returns {object} the lists by column name
 */
function tableJson(table, rows) {
  const list = (rows || []).filter((row) => row.some((cell) => String(cell ?? "").trim() !== ""));
  const result = {};
  table.columns.forEach((column, index) => {
    const values = list.map((row) => parseNumber(String(row[index] ?? "").trim()));
    if (values.every((value) => value !== null && !Number.isNaN(value))) result[column.name] = values;
  });
  return result;
}

/**
 * The node of the document made of the values of its form (they are checked with
 * nodeProblems), its description and position last, after the fields of its kind (the
 * canonical order of ADR-0023). A subcatchment made from rainfall is handoff/mapping.js's
 * (siecSubcatchment, from Hydrogram's inputs).
 *
 * @param {object} forms the forms of buildForms
 * @param {{id: string, type: string, from: string[]|null, description?: string,
 *   position?: {x: number, y: number}}} node the node's structure
 * @param {object} values the node's values
 * @returns {object} the node of hydrolog-network/1
 */
export function nodeOf(forms, node, values) {
  const made = { id: node.id, type: node.type };
  if (node.from && node.from.length) made.from = [...node.from];
  const layout = nodeLayout(forms, node, values);
  if (layout.kind === "subcatchment") {
    if (layout.variant === "given") {
      const columns = tableJson(layout.table, values[layout.table.key]);
      Object.assign(made, columns);
    } else if (layout.variant === "file") {
      Object.assign(made, jsonOf(layout.file, values, ""));
    }
  } else if (layout.kind === "reach" || layout.kind === "reservoir") {
    if (layout.kind === "reach") made.method = layout.method;
    const prefix = `${layout.method}.`;
    const own = [...layout.main, ...layout.chosen, ...layout.after, ...layout.more];
    Object.assign(made, jsonOf(own, values, prefix));
    if (layout.table) Object.assign(made, tableJson(layout.table, values[layout.table.key]));
    Object.assign(made, jsonOf(layout.wave, values, ""));
  }
  if (typeof node.description === "string" && node.description.trim()) made.description = node.description;
  if (node.position) made.position = { x: node.position.x, y: node.position.y };
  return made;
}

/**
 * The layout of the network's own fields of the schema: its name and time step (its
 * rainfall is Hydrogram's step 2, not a form of the schema).
 *
 * @param {object} forms the forms of buildForms
 * @returns {{slots: Slot[]}} the slots
 */
export function networkLayout(forms) {
  return { slots: slots(forms.network, [...forms.network.keys()], "") };
}

/**
 * The problems of the network's own fields of the schema by key.
 *
 * @param {object} forms the forms of buildForms
 * @param {object} values the network's values
 * @returns {Object<string, string>} messages by value key
 */
export function networkProblems(forms, values) {
  const found = {};
  for (const slot of networkLayout(forms).slots) {
    const message = slotProblem(slot, values[slot.key]);
    if (message) found[slot.key] = message;
  }
  return found;
}

/**
 * The network's own fields of the schema as its document writes them: its name and time
 * step, those given.
 *
 * @param {object} forms the forms of buildForms
 * @param {object} values the network's values
 * @returns {object} the fields by name
 */
export function networkFields(forms, values) {
  return jsonOf(networkLayout(forms).slots, values, "");
}

// --- words of a node ----------------------------------------------------------------

/**
 * The short description of a node from its values: the list's and the schematic's.
 *
 * @param {{id: string, type: string, from: string[]|null}} node the node's structure
 * @param {object} values the node's values
 * @returns {{title: string, meta: string, short: string, area: number|null}} „Zlewnia
 *   A”; the list's description („12,00 km² · CN 75”, „lag 25 min”); the schematic's,
 *   whose first line carries the area („CN 75”); and the area of a subcatchment
 */
export function nodeWords(node, values) {
  const kind = Object.hasOwn(texts.kinds, node.type) ? texts.kinds[node.type] : null;
  const title = kind ? t(texts.nodeTitle, { kind: kind.title, id: node.id }) : node.id;
  const number = (key) => parseNumber(values[key]);
  let meta = "";
  let short = "";
  let area = null;
  if (node.type === "subcatchment") {
    const variant = variantOf(values);
    if (variant === "rain") {
      const watershed = values.watershed && typeof values.watershed === "object" ? values.watershed : {};
      area = parseNumber(watershed.area_km2);
      const cn = parseNumber(watershed.cn);
      short = Number.isFinite(cn) ? t(texts.meta.cn, { cn: auto(cn) }) : "";
      const parts = Number.isFinite(area) ? [t(texts.meta.area, { area: num(area, 2) })] : [];
      if (short) parts.push(short);
      meta = parts.join(" · ");
    } else {
      meta = texts.variants[variant].meta;
      short = meta;
    }
  } else if (node.type === "reach") {
    const method = METHODS.includes(values["#method"]) ? values["#method"] : "lag";
    const lag = number("lag.lag_min");
    const k = number("muskingum.k_min");
    if (method === "lag" && Number.isFinite(lag)) meta = t(texts.meta.lag, { lag: auto(lag) });
    else if (method === "muskingum" && Number.isFinite(k)) {
      meta = t(texts.meta.muskingum, { k: auto(k), x: auto(number("muskingum.x")) });
    } else meta = texts.methods[method].short;
    short = meta;
  } else if (node.type === "reservoir") {
    meta = texts.methods["level-pool"].short;
    short = meta;
  } else if (node.type === "junction" && node.from) {
    meta = t(texts.meta.junction, { from: node.from.join(" + ") });
  } else if (node.type === "outlet" && node.from) {
    meta = t(texts.meta.outlet, { from: node.from.join(", ") });
  }
  return { title, meta, short, area: Number.isFinite(area) ? area : null };
}
