// Pure edits of Sieć's inputs (plan 2026-11-10-network-editor, D7, D9), without Preact or
// the DOM: each takes the section's inputs (`network`, `skeleton`, `nodes` and the rest of
// its state) and returns new ones that share every node the edit does not change, so a
// history of steps costs only what each step changed. A position is `{x, y}`, a cell of
// ADR-0013's grid.

import { cellOf } from "./geometry.js";

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
