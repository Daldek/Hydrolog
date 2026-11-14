// State of „Sieć i trasowanie” (plan D9, S4): the network being edited, kept in the
// browser under "hydrolog-gui/siec/3" (inputs only, no results): where it came from (with
// the key of its rainfall as it was opened, which tells whether the received origin of the
// rainfall still holds), its structure (ids, types, inflows, the cell of every node on the
// canvas and its description: plan 2026-11-10-network-editor, D3, D10; and `origin`, the
// record of the hand-off a node came in with the origins of its inputs and the node as it
// came, which no document carries: plan 2026-11-10-network-wizard, D9), the values of the
// network and of each node, the session files it reads (the inflows file and its time
// column), whether its layout is provisional (rows until Hydrolog lays it out), the key of
// the inputs as they were opened or last saved (whether discarding them needs a question)
// and the chosen node and view. A first visit has no network: „Nowa sieć” starts an empty
// one, or it opens from a file or a hand-off (the guide's worked example, instrukcja/#siec,
// is a file to load).
//
// The network's values are its name, description and time step and its rainfall as the
// inputs of Hydrogram's step 2 (plan 2026-11-10-network-wizard, D4: `rain_source` "none",
// "pmaxtp", "design" or "series" and their fields, the PMAXTP depth fetched kept as
// `pmaxtp_fetched`; handoff/mapping.js networkInputs). A subcatchment made from rainfall
// keeps Hydrogram's inputs as its values (D3: `watershed`, `tc_method`, `uh_model`,
// `rain_source` with „Jak w sieci” as "network"…, beside its `#variant`; mapping.js
// siecValues), any other node the values of its form (node-model.js); version 3 of the
// stored shape, version 2 is not read. buildDocument writes the document of the inputs: the
// top `rainfall` is what a run of `hydrograph generate` takes (rainfallOf), each such
// subcatchment the node of its inputs (siecSubcatchment) checked by Hydrogram's own checks
// (subcatchmentProblems), and a subcatchment made from rainfall that has neither its own
// rainfall nor the network's is a problem of its node.
//
// Another part of the page opens a network here with openNetwork(document, {name}) (the
// hand-off of S6); the section takes it when it is mounted, or on its first render.
//
// The providers' lines of the network's data (siecLines; attribution.js, Nogat DEV-20):
// those its document or hand-off came with (kept in `source`), those of the hand-off a node
// came in (its `origin`), and those of every PMAXTP depth in use (the network's rainfall's
// and a subcatchment's own). „Oblicz sieć” passes them as the option `attribution`, and the
// network's document saved or exported carries them as its `attribution` and
// `terms_notice`.

import { api } from "../../api.js";
import { linesFields, linesOf, mergeLines, orderLines } from "../../attribution.js";
import { sessionFileName } from "../../controls/file-field.js";
import { withReason } from "../../forms/model.js";
import { cameRainfallKey, networkInputs, networkRainfallKey, rainfallOf, siecInputs, siecNodes, siecSubcatchment } from "../../handoff/mapping.js";
import { isObject } from "../../handoff/validate.js";
import { useEffect, useRef, useState } from "../../html.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";
import { navigate } from "../../router.js";
import { registerRanges, registerServed } from "../../ui/info.js";
import {
  COMMAND,
  PMAXTP_COMMAND,
  checkInputs,
  initialRain,
  inputModels,
  pmaxtpDepth,
  pmaxtpLines,
  pmaxtpOptions,
  rainChecks,
  rangeInfoId,
  usesLutz,
} from "../hydrogram/state.js";
import { cellOf, isArea, placeMissing, provisionalRows } from "./editor/geometry.js";
import {
  buildForms,
  descriptionProblem,
  HELP_COMMANDS,
  KINDS,
  METHODS,
  networkFields,
  networkProblems,
  nodeOf,
  nodeProblems,
  skeletonOf,
  variantOf,
} from "./node-model.js";

/** The section's id and the key of its inputs. */
export const SECTION = "siec";

/** The name of the network's document when its source gives none. */
const DOCUMENT_NAME = "siec.json";

/** The schema of a network (GET api/schemas/…). */
const SCHEMA_FILE = "hydrolog-network-1.schema.json";

/** The key of a node's problem „Brak opadu” (buildDocument): its choice of the rainfall. */
export const NO_RAINFALL_KEY = "rain_source";

/** A node's id as hydrolog-network-1.schema.json's `$defs.id` reads it (Python's `\w`). */
const ID = /^[\p{L}\p{N}_][\p{L}\p{N}_.-]*$/u;

/**
 * The inputs before a network is open (a first visit, or after „Wyczyść”).
 *
 * @returns {object} the state
 */
export function initialState() {
  return {
    source: null,
    network: {},
    skeleton: [],
    nodes: {},
    inflowsFile: "",
    timeColumn: "",
    selected: null,
    view: "schem",
    provisional: false,
    savedKey: null,
  };
}

/**
 * The state of „Nowa sieć” (D10): an open network without nodes, to build on the canvas,
 * whose rainfall starts as Hydrogram's step 2 does (PMAXTP, nothing given).
 *
 * @returns {object} the state
 */
export function newState() {
  const started = { ...initialState(), source: { name: DOCUMENT_NAME, kind: "new" }, network: initialRain() };
  return { ...started, savedKey: inputsKey(started) };
}

/**
 * A JSON value with its keys sorted and without empty values ("", null, undefined), so
 * that inputs that hold the same data give the same text.
 *
 * @param {unknown} value a value of the inputs
 * @returns {unknown} the canonical value
 */
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  const kept = {};
  for (const key of Object.keys(value).sort()) {
    const item = value[key];
    if (item !== "" && item !== null && item !== undefined) kept[key] = canonical(item);
  }
  return kept;
}

/**
 * The key of a network's inputs (its values, structure, positions and descriptions): equal
 * keys hold the same network. „Wyczyść” and „Nowa sieć” ask first when the key differs
 * from the one kept when the network was opened or saved (D10).
 *
 * @param {{network: object, skeleton: object[], nodes: Object<string, object>}} state the
 *   section's inputs
 * @returns {string} the key: the length and FNV-1a hash of the canonical JSON
 */
export function inputsKey(state) {
  const text = JSON.stringify(canonical([state.network, state.skeleton, state.nodes]));
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return `${text.length.toString(36)}-${hash.toString(36)}`;
}

/**
 * Whether the network changed since it was opened or saved (D10).
 *
 * @param {object} state the section's state
 * @returns {boolean} true when discarding it needs a question
 */
export function changedSinceSaved(state) {
  return Boolean(state.source) && inputsKey(state) !== state.savedKey;
}

/**
 * Check a document read from a file before it opens: what the forms need of it (the
 * server checks the rest when it lays the network out).
 *
 * @param {unknown} doc the parsed JSON
 * @returns {string[]} the problems in Polish; none when the document can open
 */
export function documentProblems(doc) {
  if (!doc || typeof doc !== "object" || Array.isArray(doc)) return [texts.file.notObject];
  if (doc.schema !== "hydrolog-network/1") return [t(texts.file.wrongSchema, { schema: String(doc.schema ?? "–") })];
  if (!Array.isArray(doc.nodes) || !doc.nodes.length) return [texts.file.noNodes];
  const problems = [];
  const seen = new Set();
  doc.nodes.forEach((node, index) => {
    if (!node || typeof node !== "object") {
      problems.push(t(texts.file.notNode, { index: index + 1 }));
      return;
    }
    const id = typeof node.id === "string" ? node.id : null;
    if (!id || !ID.test(id)) problems.push(t(texts.file.badId, { index: index + 1, id: String(node.id ?? "–") }));
    else if (seen.has(id)) problems.push(t(texts.file.duplicateId, { id }));
    else seen.add(id);
    if (!KINDS.includes(node.type)) problems.push(t(texts.file.unknownType, { id: id || index + 1, type: String(node.type ?? "–") }));
    else if (node.type === "reach" && !METHODS.includes(node.method)) {
      problems.push(t(texts.file.unknownMethod, { id: id || index + 1, method: String(node.method ?? "–") }));
    }
    if (node.from !== undefined && !(Array.isArray(node.from) && node.from.every((item) => typeof item === "string"))) {
      problems.push(t(texts.file.badFrom, { id: id || index + 1 }));
    }
  });
  return problems;
}

/**
 * The rating files of a document under the names the session stores them by: a bare,
 * safe file name ("tabele/Zbiornik ś.csv" gives "Zbiornik s.csv"), since a session has
 * no directories (plan D7).
 *
 * @param {object} doc hydrolog-network/1
 * @returns {{doc: object, renamed: Array<{node: string, from: string, to: string}>}} the
 *   document with the names changed, and what was changed
 */
export function withSessionNames(doc) {
  const renamed = [];
  const nodes = doc.nodes.map((node) => {
    if (typeof node.rating_file !== "string") return node;
    const name = sessionFileName(node.rating_file);
    if (name === node.rating_file) return node;
    renamed.push({ node: String(node.id), from: node.rating_file, to: name });
    return { ...node, rating_file: name };
  });
  return { doc: { ...doc, nodes }, renamed };
}

/**
 * A structure with a cell for every node (plan 2026-11-10-network-editor, D10): as it is
 * when every node has a cell of its own; in rows by the longest distance from a headwater,
 * and provisional, when no node has one (Hydrolog's layout of the structure replaces them
 * once the structure has no problem, plan 2026-11-10-network-wizard, D8); otherwise the
 * cells it has, and the free cell nearest a neighbour for every node without one or on a
 * taken cell.
 *
 * @param {Array<{id: string, from: string[]|null, position?: {x: number, y: number}}>}
 *   skeleton the structure, with the valid positions it has
 * @returns {{skeleton: object[], provisional: boolean}} the structure with every node's
 *   position, and whether they are provisional rows
 */
export function placeSkeleton(skeleton) {
  const provisional = !skeleton.some((node) => node.position);
  const cells = provisional ? provisionalRows(skeleton) : placeMissing(skeleton).cells;
  return {
    skeleton: skeleton.map((node) => {
      const [x, y] = cells.get(node.id);
      return node.position && node.position.x === x && node.position.y === y ? node : { ...node, position: { x, y } };
    }),
    provisional,
  };
}

/**
 * The state of a network document. A network that came in a hand-off keeps the origin of
 * each node beside its structure (handoff/mapping.js siecNodes: the hand-off's record, the
 * node's own origins and the node as it came; plan 2026-11-10-network-wizard, D9), and its
 * source keeps the key of its rainfall as it was opened and the providers' lines the
 * document came with.
 *
 * @param {object} doc hydrolog-network/1 (checked with documentProblems)
 * @param {{name: string, kind: "file"|"handoff", handoff?: object}} source where it came
 *   from (a hand-off's record, whose provenance gives the PMAXTP origin of the rainfall and
 *   whose node_provenance the origins of the nodes)
 * @param {object} [keep] inputs kept from before (the inflows file and its column)
 * @returns {object} the state
 */
export function stateOf(doc, source, keep = {}) {
  const placed = placeSkeleton(skeletonOf(doc));
  const received = source && isObject(source.handoff) ? source.handoff : null;
  const { values: nodes, origins } = siecNodes(doc, received);
  const network = networkInputs(doc, received ? received.provenance : null);
  const outlet = placed.skeleton.find((node) => node.type === "outlet");
  const opened = {
    ...initialState(),
    source: {
      ...source,
      ...linesFields(linesOf(doc)),
      rainfallKey: cameRainfallKey(network, isObject(doc.rainfall) ? doc.rainfall : null, networkRainfallKey),
    },
    network,
    skeleton: placed.skeleton.map((node) => (origins[node.id] ? { ...node, origin: origins[node.id] } : node)),
    nodes,
    inflowsFile: keep.inflowsFile || "",
    timeColumn: keep.timeColumn || "",
    selected: outlet ? outlet.id : placed.skeleton.length ? placed.skeleton[0].id : null,
    provisional: placed.provisional,
  };
  return { ...opened, savedKey: inputsKey(opened) };
}

/**
 * The providers' lines of the network's data: its document's and its hand-off's (`source`),
 * those of the hand-off each node came in, and those of every PMAXTP depth in use (the
 * network's rainfall's and each subcatchment's own: pmaxtpLines), in the order of the
 * providers' sets of GET api/session.
 *
 * @param {object} state the section's state
 * @param {object|null} session hydrolog-gui-session/1, null while it has not arrived
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines, null while
 *   a depth kept without its lines waits for the session
 */
export function siecLines(state, session) {
  const source = isObject(state.source) ? state.source : {};
  const sets = [linesOf(source), linesOf(source.handoff), pmaxtpLines(state.network || {}, session)];
  for (const node of state.skeleton) {
    sets.push(linesOf(node.origin));
    const values = state.nodes[node.id] || {};
    if (node.type === "subcatchment" && variantOf(values) === "rain") sets.push(pmaxtpLines(siecInputs(values), session));
  }
  const merged = mergeLines(...sets);
  return merged === null ? null : orderLines(merged, session);
}

/**
 * What opening a document did to its positions, for the note of the load (D10): the
 * nodes whose position is not a cell of the grid, and, when the document had positions,
 * the nodes placed anew (without a position, or on a cell a node before them took).
 *
 * @param {object} doc hydrolog-network/1 as it was opened
 * @param {object} state its state (stateOf)
 * @returns {string[]} the lines of the note, in Polish
 */
export function placementNotes(doc, state) {
  const dropped = [];
  const moved = [];
  doc.nodes.forEach((node, index) => {
    const given = cellOf(node.position);
    if (node.position !== undefined && !given) dropped.push(String(node.id));
    const now = state.skeleton[index].position;
    if (!state.provisional && (!given || given[0] !== now.x || given[1] !== now.y)) moved.push(String(node.id));
  });
  const lines = [];
  if (dropped.length) lines.push(t(texts.canvas.dropped, { nodes: dropped.join(", ") }));
  if (moved.length) lines.push(t(texts.canvas.placed, { nodes: moved.join(", ") }));
  return lines;
}

/**
 * The problems of a subcatchment made from rainfall (plan 2026-11-10-network-wizard, D1),
 * each with the field of its panel: Hydrogram zlewni's own checks of its inputs
 * (checkInputs: the bounds, the relations, and, once a model is chosen, every field the
 * model, its tc method and its own rainfall need), which stand at once as they do there
 * (`shown`); a model not chosen yet (Hydrogram runs nothing before one is) and an own
 * PMAXTP depth not fetched yet, which wait for „Oblicz sieć” like a missing value.
 *
 * @param {object} forms the forms of useForms (`rain`: the models of Hydrogram's checks)
 * @param {object} inputs the subcatchment's inputs (siecInputs)
 * @returns {Array<{key: string, message: string, shown?: boolean}>} the problems
 */
function subcatchmentProblems(forms, inputs) {
  const found = [];
  if (!inputs.uh_model) found.push({ key: "uh_model", message: withReason(texts.form.noModel, "required") });
  const errors = checkInputs(inputs, forms.rain).errors;
  for (const [key, message] of Object.entries(errors)) found.push({ key, message, shown: true });
  if (pmaxtpOptions(inputs) !== null && pmaxtpDepth(inputs) === null && !errors.pmaxtp_depth) {
    found.push({ key: "pmaxtp_depth", message: withReason(texts.form.noDepth, "required") });
  }
  return found;
}

/**
 * The values a run of the network gave a subcatchment, named as the result of `hydrograph
 * generate` that Hydrogram's steps show read-only (plan 2026-11-10-network-wizard, D1):
 * tc, the CN after AMC, S, Ia, λ and the unit hydrograph's parameters, from the node's
 * `parameters` in the result of `route network`, with the model and AMC of the inputs it
 * ran with.
 *
 * @param {Object<string, number>} parameters the node's parameters in the result
 * @param {object} inputs the subcatchment's inputs of that run (siecInputs)
 * @returns {object} the values
 */
export function nodeComputed(parameters, inputs) {
  const value = (name) => (typeof parameters[name] === "number" ? parameters[name] : undefined);
  const uh = { tc_min: value("tc_min"), r_min: value("clark_r_min"), n: value("nash_n"), k_min: value("nash_k_min"), ct: value("snyder_ct"), cp: value("snyder_cp") };
  return {
    tc_min: value("tc_min"),
    amc: inputs.amc,
    cn: value("cn"),
    cn_adjusted: value("cn_adjusted") ?? value("cn"),
    retention_mm: value("retention_mm"),
    initial_abstraction_mm: value("initial_abstraction_mm"),
    ia_coefficient: value("ia_coefficient"),
    uh_model: inputs.uh_model,
    uh_parameters: Object.fromEntries(Object.entries(uh).filter(([, number]) => number !== undefined)),
    nash_estimation: usesLutz(inputs) ? "lutz" : null,
  };
}

/**
 * The document of the network: its own fields (its name and description first, ADR-0023),
 * its rainfall (rainfallOf: what a run of `hydrograph generate` takes) and every node, in
 * the order of its structure: a subcatchment made from rainfall as its inputs make it
 * (siecSubcatchment), any other node as its form does (nodeOf).
 *
 * @param {object} forms the forms of useForms (`rain`: the models of Hydrogram's step 2)
 * @param {{network: object, skeleton: object[], nodes: Object<string, object>}} state the
 *   network's values, its structure and the values of each node
 * @returns {{document: object, problems: Array<{node: string|null, key: string,
 *   message: string, shown?: boolean}>}} hydrolog-network/1 and every problem of the
 *   values and the descriptions (the structure is graph.js's): the network's own fields,
 *   its rainfall (rainChecks), each node's values (a subcatchment's subcatchmentProblems)
 *   and description, and „Brak opadu” of a subcatchment that takes the network's rainfall
 *   when the network has none (the library's `missing_field` `rainfall`)
 */
export function buildDocument(forms, state) {
  const network = state.network;
  const problems = [];
  const add = (node, found) => {
    for (const [key, message] of Object.entries(found)) problems.push({ node, key, message });
  };
  add(null, networkProblems(forms, network));
  const ownDescription = descriptionProblem(network.description);
  if (ownDescription) problems.push({ node: null, key: "description", message: ownDescription });
  add(null, rainChecks(network, forms.rain));
  const document = { schema: "hydrolog-network/1" };
  const own = networkFields(forms, network);
  if (own.name !== undefined) document.name = own.name;
  const description = network.description;
  if (typeof description === "string" && description.trim()) document.description = description;
  if (own.timestep_min !== undefined) document.timestep_min = own.timestep_min;
  const rainfall = rainfallOf(network);
  if (rainfall) document.rainfall = rainfall;
  document.nodes = state.skeleton.map((node) => {
    const values = state.nodes[node.id] || {};
    const rain = node.type === "subcatchment" && variantOf(values) === "rain";
    if (rain) {
      const inputs = siecInputs(values);
      for (const item of subcatchmentProblems(forms, inputs)) problems.push({ node: node.id, ...item });
      if (!rainfall && inputs.rain_source === "network") {
        problems.push({ node: node.id, key: NO_RAINFALL_KEY, message: withReason(texts.form.noRainfall, "missing_field") });
      }
    } else {
      add(node.id, nodeProblems(forms, node, values));
    }
    const text = descriptionProblem(node.description);
    if (text) problems.push({ node: node.id, key: "description", message: text });
    return rain ? siecSubcatchment(values, network, node) : nodeOf(forms, node, values);
  });
  return { document, problems };
}

/**
 * The document of which Hydrolog lays out the structure alone (`route schematic
 * --structure-only`, ADR-0025; plan 2026-11-10-network-wizard, D8): each node's id, type
 * and inflows, and the area of each subcatchment that has a positive one, which weighs
 * the branches as in the library. Nothing else: the layout must not wait for the values.
 *
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @param {Map<string, number|null>} areas the area of a subcatchment [km²] (nodeWords)
 * @returns {object} hydrolog-network/1 with the structure only
 */
export function structureDocument(skeleton, areas) {
  return {
    schema: "hydrolog-network/1",
    nodes: skeleton.map((node) => {
      const made = { id: node.id, type: node.type };
      if (node.from && node.from.length) made.from = [...node.from];
      const area = areas.get(node.id);
      if (node.type === "subcatchment" && isArea(area)) made.watershed = { area_km2: area };
      return made;
    }),
  };
}

/**
 * The name of the network's document in the session's "in/", where „Oblicz sieć” writes
 * it (rating files are read next to it).
 *
 * @param {object} state the section's state
 * @returns {string} e.g. "siec.json"
 */
export function documentName(state) {
  const name = sessionFileName((state.source && state.source.name) || DOCUMENT_NAME);
  return /\.json$/i.test(name) ? name : `${name}.json`;
}

/**
 * The base of the names of the files the section writes and exports.
 *
 * @param {object} state the section's state
 * @returns {string} e.g. "siec"
 */
export function fileStem(state) {
  return documentName(state).replace(/\.json$/i, "");
}

/**
 * The session files the network reads: the rating file of every node with a table in a
 * file, and whether a subcatchment takes its discharges from the inflows file.
 *
 * @param {object} state the section's state
 * @returns {{ratings: Array<{node: string, name: string}>, inflows: string[]}} the rating
 *   files by node, and the subcatchments that read the inflows file
 */
export function neededFiles(state) {
  const ratings = [];
  const inflows = [];
  for (const node of state.skeleton) {
    const values = state.nodes[node.id] || {};
    if (node.type === "subcatchment" && values["#variant"] === "file") inflows.push(node.id);
    if (node.type === "reservoir" || (node.type === "reach" && values["#method"] === "level-pool")) {
      const name = values["level-pool.rating_file"];
      if (values["level-pool.#table"] === 1 && typeof name === "string" && name.trim()) {
        ratings.push({ node: node.id, name: name.trim() });
      }
    }
  }
  return { ratings, inflows };
}

/** The fields of a routing method whose bounds in the network's schema are its range of applicability. */
const METHOD_RANGES = Object.freeze({ muskingum: ["x"] });

/**
 * Register with the explanations of the routing methods ("routing.<method>") the bounds the
 * network's schema gives the fields of METHOD_RANGES (Muskingum's X): the GUI keeps no bound
 * of its own.
 *
 * @param {object} forms the forms of buildForms
 */
function registerMethodRanges(forms) {
  for (const [method, names] of Object.entries(METHOD_RANGES)) {
    const fields = forms.methods[method];
    if (!fields) continue;
    const found = [];
    for (const name of names) {
      const field = fields.get(name);
      if (!field || (field.min === null && field.max === null)) continue;
      found.push({ method, parameter: name, inputs: [name], minimum: field.min, maximum: field.max, unit: "-", source: texts.method.rangeSource });
    }
    if (found.length) registerRanges(`routing.${method}`, found);
  }
}

/**
 * The forms of the nodes: the network's schema and the catalog's Polish help, fetched once;
 * the schema's bounds of the methods' ranges go to their explanations. With them `rain`,
 * the models that check the network's rainfall as Hydrogram's step 2 (inputModels of the
 * catalog documents of `hydrograph generate` and `precip pmaxtp`), whose typical ranges go
 * to the explanations of the rainfall.
 *
 * @returns {{forms: object|null, error: string|null}} the forms (null until they arrive)
 *   and a loading error
 */
export function useForms() {
  const [found, setFound] = useState({ forms: null, error: null });
  useEffect(() => {
    let alive = true;
    const help = Promise.all(
      HELP_COMMANDS.map((name) =>
        api
          .command(name)
          .then((doc) => [name, doc])
          .catch(() => null),
      ),
    );
    Promise.all([api.schema(SCHEMA_FILE), api.command(COMMAND), api.command(PMAXTP_COMMAND), help])
      .then(([schema, generate, pmaxtp, docs]) => {
        const forms = { ...buildForms(schema, new Map(docs.filter(Boolean))), rain: inputModels(generate, schema, pmaxtp) };
        registerMethodRanges(forms);
        registerServed(generate, rangeInfoId);
        if (alive) setFound({ forms, error: null });
      })
      .catch((error) => {
        if (alive) setFound({ forms: null, error: String((error && error.message) || error) });
      });
    return () => {
      alive = false;
    };
  }, []);
  return found;
}

// --- a network opened from elsewhere (the hand-off) ----------------------------------

let opened = null;
const openers = new Set();

/**
 * Open a network in Sieć: the section shows it and its schematic (the hand-off of S6
 * opens a network of more than one subcatchment here).
 *
 * @param {object} doc hydrolog-network/1
 * @param {{name?: string, kind?: string, handoff?: object, notes?: string[]}} [meta] its
 *   file name, where it came from ("handoff" by default) and, from a hand-off, its record
 *   (who wrote it, its provenance, the origins of its nodes and its result:
 *   handoff/mapping.js siecReceived), kept as the state's `source`; and the lines the
 *   load's note adds (a key of node_provenance that names no node)
 */
export function openNetwork(doc, meta = {}) {
  opened = { doc, meta: { ...meta, name: meta.name || DOCUMENT_NAME, kind: meta.kind || "handoff" } };
  for (const listener of [...openers]) listener();
  navigate(SECTION);
}

/**
 * Take a network opened with openNetwork, once.
 *
 * @returns {{doc: object, meta: {name: string, kind: string}}|null} the network, or null
 */
function takeOpened() {
  const found = opened;
  opened = null;
  return found;
}

/**
 * Call `onOpen` whenever a network is opened with openNetwork (and for one opened before
 * the section was mounted).
 *
 * @param {(found: {doc: object, meta: object}) => void} onOpen the handler
 */
export function useOpened(onOpen) {
  const latest = useRef(onOpen);
  latest.current = onOpen;
  useEffect(() => {
    const listener = () => {
      const found = takeOpened();
      if (found) latest.current(found);
    };
    openers.add(listener);
    listener();
    return () => openers.delete(listener);
  }, []);
}
