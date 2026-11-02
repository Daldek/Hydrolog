// State of „Sieć i trasowanie” (plan D9, S4): the network being edited, kept in the
// browser under "hydrolog-gui/siec/1" (inputs only, no results): where it came from, its
// structure (ids, types, inflows; not edited, plan D18), the values of the network and of
// each node, the session files it reads (the inflows file and its time column) and the
// chosen node and view. A first visit opens the shipped example (examples/siec.json,
// hydrolog.testing.example_network_document()).
//
// Another part of the page opens a network here with openNetwork(document, {name}) (the
// hand-off of S6); the section takes it when it is mounted, or on its first render.

import { api } from "../../api.js";
import { sessionFileName } from "../../controls/file-field.js";
import { useEffect, useRef, useState } from "../../html.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";
import { navigate } from "../../router.js";
import { buildForms, HELP_COMMANDS, KINDS, METHODS, networkValues, nodeValues, skeletonOf } from "./node-model.js";

/** The section's id and the key of its inputs. */
export const SECTION = "siec";

/** The shipped example, relative to the page. */
export const EXAMPLE = "examples/siec.json";

/** The file name the example is known by. */
export const EXAMPLE_NAME = "siec.json";

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
 * The state of a network document.
 *
 * @param {object} doc hydrolog-network/1 (checked with documentProblems)
 * @param {{name: string, kind: "example"|"file"|"handoff"}} source where it came from
 * @param {object} [keep] inputs kept from before (the inflows file and its column)
 * @returns {object} the state
 */
export function stateOf(doc, source, keep = {}) {
  const skeleton = skeletonOf(doc);
  const nodes = {};
  for (const node of doc.nodes) nodes[String(node.id)] = nodeValues(node);
  const outlet = skeleton.find((node) => node.type === "outlet");
  return {
    ...initialState(),
    source,
    network: networkValues(doc),
    skeleton,
    nodes,
    inflowsFile: keep.inflowsFile || "",
    timeColumn: keep.timeColumn || "",
    selected: outlet ? outlet.id : skeleton.length ? skeleton[0].id : null,
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
  const name = sessionFileName((state.source && state.source.name) || EXAMPLE_NAME);
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

/**
 * The forms of the nodes: the network's schema and the catalog's Polish help, fetched once.
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
        if (alive) setFound({ forms: buildForms(schema, new Map(docs.filter(Boolean))), error: null });
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

/**
 * Fetch the shipped example.
 *
 * @returns {Promise<object>} hydrolog-network/1
 */
export async function fetchExample() {
  const response = await fetch(new URL(EXAMPLE, document.baseURI).href, { cache: "no-cache" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
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
  opened = { doc, meta: { ...meta, name: meta.name || EXAMPLE_NAME, kind: meta.kind || "handoff" } };
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
