// State of „Sieć i trasowanie” (plan D9, S4): the network being edited, kept in the
// browser under "hydrolog-gui/siec/2" (inputs only, no results): where it came from, its
// structure (ids, types, inflows, which are not edited, plan D18; and the cell of every
// node on the canvas, plan 2026-11-10-network-editor, D3, D10), the values of the network
// and of each node, the session files it reads (the inflows file and its time column),
// whether its layout is provisional (rows until Hydrolog lays it out) and the chosen node
// and view. A first visit has no network: it opens from a file or a hand-off (the guide's
// worked example, instrukcja/#siec, is a file to load).
//
// Another part of the page opens a network here with openNetwork(document, {name}) (the
// hand-off of S6); the section takes it when it is mounted, or on its first render.

import { api } from "../../api.js";
import { sessionFileName } from "../../controls/file-field.js";
import { useEffect, useRef, useState } from "../../html.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";
import { navigate } from "../../router.js";
import { registerRanges } from "../../ui/info.js";
import { cellOf, placeMissing, provisionalRows } from "./editor/geometry.js";
import { buildForms, HELP_COMMANDS, KINDS, METHODS, networkValues, nodeValues, skeletonOf } from "./node-model.js";

/** The section's id and the key of its inputs. */
export const SECTION = "siec";

/** The name of the network's document when its source gives none. */
export const DOCUMENT_NAME = "siec.json";

/** The schema of a network (GET api/schemas/…). */
export const SCHEMA_FILE = "hydrolog-network-1.schema.json";

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
  };
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
 * and provisional, when no node has one (Hydrolog's layout replaces them once it can read
 * the network); otherwise the cells it has, and the free cell nearest a neighbour for every
 * node without one or on a taken cell.
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
 * The state of a network document.
 *
 * @param {object} doc hydrolog-network/1 (checked with documentProblems)
 * @param {{name: string, kind: "file"|"handoff"}} source where it came from
 * @param {object} [keep] inputs kept from before (the inflows file and its column)
 * @returns {object} the state
 */
export function stateOf(doc, source, keep = {}) {
  const placed = placeSkeleton(skeletonOf(doc));
  const nodes = {};
  for (const node of doc.nodes) nodes[String(node.id)] = nodeValues(node);
  const outlet = placed.skeleton.find((node) => node.type === "outlet");
  return {
    ...initialState(),
    source,
    network: networkValues(doc),
    skeleton: placed.skeleton,
    nodes,
    inflowsFile: keep.inflowsFile || "",
    timeColumn: keep.timeColumn || "",
    selected: outlet ? outlet.id : placed.skeleton.length ? placed.skeleton[0].id : null,
    provisional: placed.provisional,
  };
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
 * The structure without the cells: what the layout of Hydrolog depends on.
 *
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @returns {Array<{id: string, type: string, from: string[]|null}>} ids, types, inflows
 */
export function structureOf(skeleton) {
  return skeleton.map((node) => ({ id: node.id, type: node.type, from: node.from }));
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
export function registerMethodRanges(forms) {
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
 * the schema's bounds of the methods' ranges go to their explanations.
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
    Promise.all([api.schema(SCHEMA_FILE), help])
      .then(([schema, docs]) => {
        const forms = buildForms(schema, new Map(docs.filter(Boolean)));
        registerMethodRanges(forms);
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
 * @param {{name?: string, kind?: string, handoff?: object}} [meta] its file name, where it
 *   came from ("handoff" by default) and, from a hand-off, its record (who wrote it, its
 *   provenance and result: handoff/mapping.js siecReceived); kept as the state's `source`
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
export function takeOpened() {
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
