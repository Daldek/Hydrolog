// Pure edits of Sieć's inputs (plan 2026-11-10-network-editor, D7, D9), without Preact or
// the DOM: each takes the section's inputs (`network`, `skeleton`, `nodes` and the rest of
// its state) and returns new ones that share every node the edit does not change, so a
// history of steps costs only what each step changed; an edit that cannot be made returns
// the same inputs. A position is `{x, y}`, a cell of ADR-0013's grid. A node's `from` is
// null or the non-empty list of the ids that flow into it: connecting moves a node's one
// downstream link, so the edits never make a bifurcation, an unknown inflow or a repeated
// one (only a file can).

import { cellOf, cellKey, freeCell } from "./geometry.js";
import { foldId, idProblem, receiversOf } from "./graph.js";

/** The prefix of the id of a new element of each type (the ids of Hydrograf's hand-off). */
const PREFIXES = Object.freeze({ subcatchment: "Z", reach: "R", reservoir: "ZB", junction: "J", outlet: "OUT" });

/**
 * The id of a new element: its type's prefix with the first free number (`Z1`, `R2`…),
 * the outlet `OUT` (then `OUT2`…), free without regard to case.
 *
 * @param {Array<{id: string}>} skeleton the structure
 * @param {string} type the element's type
 * @returns {string} the id
 */
export function nextId(skeleton, type) {
  const taken = new Set(skeleton.map((node) => foldId(node.id)));
  const prefix = Object.hasOwn(PREFIXES, type) ? PREFIXES[type] : "N";
  if (type === "outlet" && !taken.has(foldId(prefix))) return prefix;
  for (let number = type === "outlet" ? 2 : 1; ; number += 1) {
    const id = `${prefix}${number}`;
    if (!taken.has(foldId(id))) return id;
  }
}

/**
 * The id of a node that comes with an id of its own (D10: a hand-off's subcatchment): that
 * id when the library would take it in the structure, else its stem (the id without its
 * last digits) with the first free number from 2 (`Z1` becomes `Z2`, `Dolna` `Dolna2`),
 * else nextId's.
 *
 * @param {Array<{id: string}>} skeleton the structure
 * @param {string} id the node's own id
 * @param {string} type the node's type
 * @returns {string} the id
 */
export function freeId(skeleton, id, type) {
  if (!idProblem(id, skeleton)) return id;
  const stem = String(id).replace(/\d+$/u, "");
  const taken = new Set(skeleton.map((node) => foldId(node.id)));
  for (let number = 2; stem; number += 1) {
    const next = `${stem}${number}`;
    if (taken.has(foldId(next))) continue;
    if (!idProblem(next, skeleton)) return next;
    break;
  }
  return nextId(skeleton, type);
}

/**
 * The keys of the cells the nodes stand on.
 *
 * @param {Array<{position?: {x: number, y: number}}>} skeleton the structure
 * @returns {Set<string>} the keys (cellKey)
 */
function takenCells(skeleton) {
  return new Set(skeleton.filter((node) => node.position).map((node) => cellKey([node.position.x, node.position.y])));
}

/**
 * Where a new element stands beside a node (D7: the palette by keys, „Dodaj węzeł”): the
 * free cell nearest the cell right of it; without the node, right of the top row (the
 * cell [0, 0] of an empty network).
 *
 * @param {Array<{id: string, position?: {x: number, y: number}}>} skeleton the structure
 * @param {string|null} id the chosen node, or null
 * @returns {[number, number]|null} [x, y], or null when the grid is full
 */
export function cellBeside(skeleton, id) {
  const taken = takenCells(skeleton);
  const node = skeleton.find((item) => item.id === id && item.position);
  if (node) return freeCell(taken, [node.position.x, node.position.y + 1], "up");
  const placed = skeleton.filter((item) => item.position);
  if (!placed.length) return [0, 0];
  const top = Math.min(...placed.map((item) => item.position.x));
  const right = Math.max(...placed.filter((item) => item.position.x === top).map((item) => item.position.y));
  return freeCell(taken, [top, right + 1], "up");
}

/**
 * Where a new inflow of a node stands (D7: `D`, „Dodaj dopływ”): the free cell nearest the
 * cell above it, upstream first.
 *
 * @param {Array<{id: string, position?: {x: number, y: number}}>} skeleton the structure
 * @param {string} id the node it flows into
 * @returns {[number, number]|null} [x, y], or null when the grid is full
 */
export function cellAbove(skeleton, id) {
  const node = skeleton.find((item) => item.id === id && item.position);
  if (!node) return cellBeside(skeleton, null);
  return freeCell(takenCells(skeleton), [node.position.x - 1, node.position.y], "up");
}

/**
 * A list of inflows as the structure keeps it: null when empty.
 *
 * @param {string[]} listed the ids
 * @returns {string[]|null} the list, or null
 */
function inflowList(listed) {
  return listed.length ? listed : null;
}

/**
 * The structure without a node's downstream links, or without its link to one node.
 *
 * @param {object[]} skeleton the structure
 * @param {string} id the node
 * @param {string|null} [to] the node of the one link to take away (null: every link)
 * @returns {object[]} the structure (the same array when there is no such link)
 */
function unlinked(skeleton, id, to = null) {
  let changed = false;
  const next = skeleton.map((node) => {
    if ((to !== null && node.id !== to) || !node.from || !node.from.includes(id)) return node;
    changed = true;
    return { ...node, from: inflowList(node.from.filter((up) => up !== id)) };
  });
  return changed ? next : skeleton;
}

/**
 * Move a node to a cell.
 *
 * @param {{skeleton: Array<{id: string, position?: {x: number, y: number}}>}} inputs the
 *   section's inputs
 * @param {string} id the node
 * @param {{x: number, y: number}} position its new cell
 * @returns {object} the new inputs; the same inputs when the node is unknown, the
 *   position is not a cell of the grid, or another node stands there
 */
export function moveNode(inputs, id, position) {
  const index = inputs.skeleton.findIndex((node) => node.id === id);
  if (index < 0 || !cellOf(position)) return inputs;
  const taken = inputs.skeleton.some(
    (node) => node.id !== id && node.position && node.position.x === position.x && node.position.y === position.y,
  );
  if (taken) return inputs;
  const skeleton = inputs.skeleton.slice();
  skeleton[index] = { ...skeleton[index], position: { x: position.x, y: position.y } };
  return { ...inputs, skeleton };
}

/**
 * Put nodes on new cells at once (Hydrolog's layout of „Uporządkuj”).
 *
 * @param {{skeleton: Array<{id: string, position?: {x: number, y: number}}>}} inputs the
 *   section's inputs
 * @param {Object<string, {x: number, y: number}>} positions the cell of each node; a node
 *   not named keeps its own
 * @returns {object} the new inputs
 */
export function placeAll(inputs, positions) {
  const skeleton = inputs.skeleton.map((node) =>
    Object.hasOwn(positions, node.id) && cellOf(positions[node.id])
      ? { ...node, position: { x: positions[node.id].x, y: positions[node.id].y } }
      : node,
  );
  return { ...inputs, skeleton };
}

/**
 * Add an element on a free cell, unconnected, with empty values (D2, D7): its id is
 * nextId's, the last node of the new structure.
 *
 * @param {{skeleton: object[], nodes: Object<string, object>}} inputs the section's inputs
 * @param {string} type one of the five types
 * @param {{x: number, y: number}} position its cell
 * @returns {object} the new inputs; the same inputs for an unknown type, a position off
 *   the grid or a taken cell
 */
export function addNode(inputs, type, position) {
  if (!Object.hasOwn(PREFIXES, type) || !cellOf(position)) return inputs;
  if (takenCells(inputs.skeleton).has(cellKey([position.x, position.y]))) return inputs;
  const id = nextId(inputs.skeleton, type);
  const node = { id, type, from: null, position: { x: position.x, y: position.y } };
  return { ...inputs, skeleton: [...inputs.skeleton, node], nodes: { ...inputs.nodes, [id]: {} } };
}

/**
 * Make a node flow into another (D7): its one downstream link moves there, at the end of
 * the target's inflows. The structure is not checked here (graph.js linkVerdict judges a
 * link first).
 *
 * @param {{skeleton: object[]}} inputs the section's inputs
 * @param {string} from the node that flows
 * @param {string} to the node it flows into
 * @returns {object} the new inputs; the same inputs when nothing changes or a node is
 *   unknown
 */
export function connect(inputs, from, to) {
  const { skeleton } = inputs;
  if (from === to || !skeleton.some((node) => node.id === from) || !skeleton.some((node) => node.id === to)) return inputs;
  let changed = false;
  const next = skeleton.map((node) => {
    const listed = node.from || [];
    if (node.id === to) {
      if (listed.includes(from)) return node;
      changed = true;
      return { ...node, from: [...listed, from] };
    }
    if (!listed.includes(from)) return node;
    changed = true;
    return { ...node, from: inflowList(listed.filter((up) => up !== from)) };
  });
  return changed ? { ...inputs, skeleton: next } : inputs;
}

/**
 * Take away a node's downstream link (D7: „Odłącz”, „Odpływa do: brak”, a chosen link and
 * Delete).
 *
 * @param {{skeleton: object[]}} inputs the section's inputs
 * @param {string} id the node
 * @param {string|null} [to] the node of the one link to take away (a file's node may flow
 *   into several); null takes away every link of the node
 * @returns {object} the new inputs; the same inputs when there is no such link
 */
export function disconnect(inputs, id, to = null) {
  const skeleton = unlinked(inputs.skeleton, id, to);
  return skeleton === inputs.skeleton ? inputs : { ...inputs, skeleton };
}

/**
 * „Wstaw złącze” (D7, Q7): a node becomes a second inflow of a node that takes one only (a
 * reach, a reservoir or the outlet) through a new junction on the free cell above the
 * target, which takes the target's inflows and the node and flows into the target.
 *
 * @param {{skeleton: object[], nodes: Object<string, object>}} inputs the section's inputs
 * @param {string} from the node that flows
 * @param {string} to the node that takes one inflow
 * @returns {object} the new inputs: the junction stands before the target; the same
 *   inputs when a node is unknown or the grid is full
 */
export function insertJunction(inputs, from, to) {
  const index = inputs.skeleton.findIndex((node) => node.id === to);
  if (from === to || index < 0 || !inputs.skeleton.some((node) => node.id === from)) return inputs;
  const target = inputs.skeleton[index];
  const near = target.position ? [target.position.x - 1, target.position.y] : [0, 0];
  const cell = freeCell(takenCells(inputs.skeleton), near, "up");
  if (!cell) return inputs;
  const id = nextId(inputs.skeleton, "junction");
  const inflows = [...new Set([...(target.from || []).filter((up) => up !== from), from])];
  const skeleton = unlinked(inputs.skeleton, from).map((node) => (node.id === to ? { ...node, from: [id] } : node));
  skeleton.splice(index, 0, { id, type: "junction", from: inflows, position: { x: cell[0], y: cell[1] } });
  return { ...inputs, skeleton, nodes: { ...inputs.nodes, [id]: {} } };
}

/**
 * Whether „Usuń i połącz” can remove a node: it has one inflow and flows into one node.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @param {string} id the node
 * @returns {boolean} true when its inflow can take its place
 */
export function canBridge(skeleton, id) {
  const node = skeleton.find((item) => item.id === id);
  if (!node || !node.from || node.from.length !== 1 || !skeleton.some((item) => item.id === node.from[0])) return false;
  const receivers = receiversOf(skeleton);
  return (receivers.get(id) || []).length === 1;
}

/**
 * Remove a node with its links and values (D7: „Usuń”); with `bridge` („Usuń i połącz”,
 * when canBridge), its inflow takes its place in the node it flowed into.
 *
 * @param {{skeleton: object[], nodes: Object<string, object>}} inputs the section's inputs
 * @param {string} id the node
 * @param {{bridge?: boolean}} [options] whether its inflow joins the node below it
 * @returns {object} the new inputs; the same inputs for an unknown node
 */
export function removeNode(inputs, id, { bridge = false } = {}) {
  const node = inputs.skeleton.find((item) => item.id === id);
  if (!node) return inputs;
  const inflow = bridge && canBridge(inputs.skeleton, id) ? node.from[0] : null;
  const skeleton = [];
  for (const other of inputs.skeleton) {
    if (other.id === id) continue;
    if (!other.from || !other.from.includes(id)) {
      skeleton.push(other);
      continue;
    }
    const listed = inflow ? other.from.map((up) => (up === id ? inflow : up)) : other.from.filter((up) => up !== id);
    skeleton.push({ ...other, from: inflowList([...new Set(listed)]) });
  }
  const nodes = { ...inputs.nodes };
  delete nodes[id];
  return { ...inputs, skeleton, nodes };
}

/**
 * Give a node another id (D7): every `from` that names it follows, its values move with
 * it, and a subcatchment that reads its column of the inflows file by its id keeps that
 * column (`value_column` takes the old id). The chosen node follows too.
 *
 * @param {{skeleton: object[], nodes: Object<string, object>, selected?: string|null}}
 *   inputs the section's inputs
 * @param {string} id the node
 * @param {string} next its new id
 * @returns {object} the new inputs; the same inputs for an unknown node or an id the
 *   library would refuse (graph.js idProblem)
 */
export function renameNode(inputs, id, next) {
  const node = inputs.skeleton.find((item) => item.id === id);
  if (!node || id === next || idProblem(next, inputs.skeleton, id)) return inputs;
  const skeleton = inputs.skeleton.map((item) => {
    if (item.id === id) return { ...item, id: next };
    return item.from && item.from.includes(id) ? { ...item, from: item.from.map((up) => (up === id ? next : up)) } : item;
  });
  let values = inputs.nodes[id] || {};
  if (node.type === "subcatchment" && values["#variant"] === "file" && !String(values.value_column ?? "").trim()) {
    values = { ...values, value_column: id };
  }
  const nodes = {};
  for (const [key, value] of Object.entries(inputs.nodes)) nodes[key === id ? next : key] = key === id ? values : value;
  if (!Object.hasOwn(inputs.nodes, id)) nodes[next] = values;
  const renamed = { ...inputs, skeleton, nodes };
  if (inputs.selected === id) renamed.selected = next;
  return renamed;
}

/**
 * Describe a node (D3: plain text, kept as typed; a blank text removes the description).
 *
 * @param {{skeleton: object[]}} inputs the section's inputs
 * @param {string} id the node
 * @param {string} text the description
 * @returns {object} the new inputs; the same inputs when nothing changes
 */
export function describeNode(inputs, id, text) {
  const index = inputs.skeleton.findIndex((node) => node.id === id);
  if (index < 0) return inputs;
  const value = typeof text === "string" && text.trim() ? text : null;
  const node = inputs.skeleton[index];
  if ((node.description ?? null) === value) return inputs;
  const { description: _old, ...rest } = node;
  const skeleton = inputs.skeleton.slice();
  skeleton[index] = value === null ? rest : { ...rest, description: value };
  return { ...inputs, skeleton };
}
