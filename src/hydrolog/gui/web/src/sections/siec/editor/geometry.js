// The geometry of Sieć's canvas (plan 2026-11-10-network-editor, D5, D6, D10): a pure
// module without Preact or the DOM, which Nogat's kit can wrap (GUI plan D9). A position
// is a cell of ADR-0013's grid, `x` growing downstream and `y` sideways: `{x, y}` in the
// document and the section's inputs, `[x, y]` here. The canvas draws the grid turned, the
// sources at the top and the outlet at the bottom: a node's column is its `y` and its row
// its `x`, COLUMN pixels across and ROW along the flow. Every edge follows rule D
// (ADR-0023) from the cells of its two nodes, as the library draws it; the lines are
// ranked as the library ranks them (ADR-0013, rules 1 and 2), so the main stem is the
// library's; each label stands on the side of its node where no tributary runs.

/** Pixels per grid unit across the picture (between lines). */
export const COLUMN = 110;

/** Pixels per grid unit along the flow (between rows). */
export const ROW = 74;

/** The largest |x| and |y| of a position (hydrolog-network/1, the library's MAX_POSITION). */
export const MAX_POSITION = 1000;

/** The radius of a node's halo [px]: its target (40 px across) and its focus ring. */
export const HALO = 20;

/** Pixels between a node's centre and its label. */
export const LABEL_GAP = 22;

/** Pixels between the baselines of a label's lines. */
export const LINE_HEIGHT = 14;

/** Width of a character of a label, a generous estimate [px] (12 px type). */
const CHAR_PX = 7.2;

/** The places of a label, in the order they are tried after the preferred side. */
export const PLACES = Object.freeze(["right", "left", "right-below", "left-below"]);

/** The steps [dx, dy] of the directions of the turned picture: up is upstream. */
export const DIRECTIONS = Object.freeze({
  up: Object.freeze([-1, 0]),
  down: Object.freeze([1, 0]),
  left: Object.freeze([0, -1]),
  right: Object.freeze([0, 1]),
});

// The box a label takes beside its node, in grid units of the turned picture (columns
// across, rows along the flow), relative to the node: [col0, col1, row0, row1].
const BOXES = {
  right: [0.15, 1.0, -0.3, 0.3],
  left: [-1.0, -0.15, -0.3, 0.3],
  "right-below": [0.15, 1.0, 0.05, 0.65],
  "left-below": [-1.0, -0.15, 0.05, 0.65],
};

/**
 * Whether a cell lies on the grid of positions.
 *
 * @param {[number, number]} cell [x, y]
 * @returns {boolean} true when |x| and |y| are at most MAX_POSITION
 */
function inside(cell) {
  return Math.abs(cell[0]) <= MAX_POSITION && Math.abs(cell[1]) <= MAX_POSITION;
}

/**
 * The cell of a position of a document: whole numbers from −MAX_POSITION to MAX_POSITION
 * under the keys `x` and `y` and no other (hydrolog-network/1, ADR-0023).
 *
 * @param {unknown} value a node's `position`
 * @returns {[number, number]|null} [x, y], or null when the value is not a position
 */
export function cellOf(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const keys = Object.keys(value);
  if (keys.length !== 2 || !keys.includes("x") || !keys.includes("y")) return null;
  const whole = (number) => Number.isInteger(number) && Math.abs(number) <= MAX_POSITION;
  return whole(value.x) && whole(value.y) ? [value.x, value.y] : null;
}

/**
 * The key of a cell in a set or map of cells.
 *
 * @param {[number, number]} cell [x, y]
 * @returns {string} "x,y"
 */
export function cellKey(cell) {
  return `${cell[0]},${cell[1]}`;
}

/**
 * A point of the grid in the turned picture.
 *
 * @param {[number, number]} point [x, y] of the grid
 * @returns {[number, number]} [column, row]
 */
export function transpose(point) {
  return [point[1], point[0]];
}

/**
 * The centre of a cell in the turned picture.
 *
 * @param {[number, number]} cell [x, y]
 * @returns {[number, number]} [px across, px along the flow]
 */
export function centreOf(cell) {
  return [cell[1] * COLUMN, cell[0] * ROW];
}

/**
 * The cell whose centre is nearest to a point of the turned picture, on the grid.
 *
 * @param {[number, number]} point [px across, px along the flow]
 * @returns {[number, number]} [x, y]
 */
export function cellAt(point) {
  const bound = (number) => Math.max(-MAX_POSITION, Math.min(MAX_POSITION, number)) || 0;
  return [bound(Math.round(point[1] / ROW)), bound(Math.round(point[0] / COLUMN))];
}

/**
 * The cell next to a cell in a direction of the turned picture.
 *
 * @param {[number, number]} cell [x, y]
 * @param {"up"|"down"|"left"|"right"} direction up is upstream (`x` smaller)
 * @returns {[number, number]|null} the cell, or null beyond the grid
 */
export function stepCell(cell, direction) {
  const [dx, dy] = DIRECTIONS[direction];
  const next = [cell[0] + dx, cell[1] + dy];
  return inside(next) ? next : null;
}

/**
 * Drop the corners that lie on a straight line between their neighbours.
 *
 * @param {Array<[number, number]>} route the corners
 * @returns {Array<[number, number]>} the corners kept
 */
function straight(route) {
  const kept = [route[0]];
  for (let index = 1; index < route.length - 1; index += 1) {
    const [x0, y0] = kept[kept.length - 1];
    const [x1, y1] = route[index];
    const [x2, y2] = route[index + 1];
    if ((x1 - x0) * (y2 - y1) !== (y1 - y0) * (x2 - x1)) kept.push(route[index]);
  }
  kept.push(route[route.length - 1]);
  return kept;
}

/**
 * The corners of the edge from a node to the node it flows into, by rule D (ADR-0023),
 * as the library draws it (`hydrolog.routing._layout.edge_route`). With `dx` and `dy` the
 * steps from `start` to `end`: one straight segment when either is 0; for `dx > 0` a
 * sideways leg of |dy| − 1 to the row next to `end`'s, one step at 45 degrees onto it and
 * the rest along it; for `dx < 0` 45 degrees for min(|dx|, |dy|) steps, then straight on.
 * A stretch of length 0 is left out; every segment runs at 0, 45 or 90 degrees.
 *
 * @param {[number, number]} start [x, y] of the node
 * @param {[number, number]} end [x, y] of the node it flows into
 * @returns {Array<[number, number]>} the corners in grid units, from `start` to `end`
 */
export function edgeRoute(start, end) {
  const [x0, y0] = start;
  const [x1, y1] = end;
  const dx = x1 - x0;
  const dy = y1 - y0;
  if (dx === 0 || dy === 0) {
    return [
      [x0, y0],
      [x1, y1],
    ];
  }
  const step = dy > 0 ? 1 : -1;
  if (dx > 0) {
    return straight([
      [x0, y0],
      [x0, y1 - step],
      [x0 + 1, y1],
      [x1, y1],
    ]);
  }
  const diagonal = Math.min(-dx, Math.abs(dy));
  return straight([
    [x0, y0],
    [x0 - diagonal, y0 + step * diagonal],
    [x1, y1],
  ]);
}

/**
 * Whether one rank comes before another, the first values first.
 *
 * @param {number[]} rank a rank
 * @param {number[]} other a rank of the same length
 * @returns {boolean} true when `rank` is smaller
 */
function before(rank, other) {
  for (let index = 0; index < rank.length; index += 1) {
    if (rank[index] !== other[index]) return rank[index] < other[index];
  }
  return false;
}

/**
 * The nearest free cell to `near`, first on `side`: the cell itself when it is free, else
 * the rings around it one after another (the cells one step away in any direction, then
 * two…), in each ring the cells on `side` first (upstream, `x` smaller, for "up";
 * downstream for "down"), then those level with `near`, then the others; among them the
 * nearer sideways, the nearer along the flow, and the right before the left.
 *
 * @param {Set<string>} taken the keys (cellKey) of the cells taken
 * @param {[number, number]} near [x, y]
 * @param {"up"|"down"} side where to look first
 * @returns {[number, number]|null} [x, y], or null when the grid is full
 */
export function freeCell(taken, near, side) {
  const [x0, y0] = near;
  if (inside(near) && !taken.has(cellKey(near))) return [x0, y0];
  const toward = side === "down" ? 1 : -1;
  for (let ring = 1; ring <= 2 * MAX_POSITION; ring += 1) {
    let best = null;
    let bestRank = null;
    for (let dx = -ring; dx <= ring; dx += 1) {
      const edge = Math.abs(dx) === ring;
      for (let dy = -ring; dy <= ring; dy += edge ? 1 : 2 * ring) {
        const cell = [x0 + dx, y0 + dy];
        if (!inside(cell) || taken.has(cellKey(cell))) continue;
        const rank = [Math.sign(dx) === toward ? 0 : dx === 0 ? 1 : 2, Math.abs(dy), Math.abs(dx), -dy];
        if (!bestRank || before(rank, bestRank)) {
          best = cell;
          bestRank = rank;
        }
      }
    }
    if (best) return best;
  }
  return null;
}

/**
 * The inflows of every node: the ids of its `from` that are nodes of the network, each
 * once, never the node itself.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @returns {Map<string, string[]>} the inflows by id
 */
function inflowsOf(skeleton) {
  const ids = new Set(skeleton.map((node) => node.id));
  return new Map(
    skeleton.map((node) => [node.id, [...new Set((node.from || []).filter((up) => ids.has(up) && up !== node.id))]]),
  );
}

/**
 * Rows for a network that Hydrolog cannot lay out yet (D10): each node on the row of its
 * longest distance from a headwater (the headwaters on row 0, at the top), the nodes of a
 * row side by side in the order of the document, centred on column 0. A node in a cycle,
 * or below one, has no such distance and goes on the row after the last.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @returns {Map<string, [number, number]>} the cell [x, y] of every node
 */
export function provisionalRows(skeleton) {
  const inflows = inflowsOf(skeleton);
  const depth = new Map();
  const visiting = new Set();
  const rowOf = (id) => {
    if (depth.has(id)) return depth.get(id);
    if (visiting.has(id)) return null;
    visiting.add(id);
    let row = 0;
    let looped = false;
    for (const up of inflows.get(id)) {
      const above = rowOf(up);
      if (above === null) looped = true;
      else row = Math.max(row, above + 1);
    }
    visiting.delete(id);
    const found = looped ? null : row;
    depth.set(id, found);
    return found;
  };
  for (const node of skeleton) rowOf(node.id);
  const last = Math.max(-1, ...[...depth.values()].filter((row) => row !== null));
  const rows = new Map();
  for (const node of skeleton) {
    const row = depth.get(node.id) ?? last + 1;
    if (!rows.has(row)) rows.set(row, []);
    rows.get(row).push(node.id);
  }
  const cells = new Map();
  for (const [row, ids] of rows) {
    const shift = Math.floor((ids.length - 1) / 2);
    ids.forEach((id, index) => cells.set(id, [row, index - shift]));
  }
  return cells;
}

/**
 * The cells of the nodes of an opened network that has positions (D10): a node keeps the
 * cell of its position unless a node before it took that cell; every other node goes to
 * the free cell nearest the node it flows into (above it), else nearest a placed inflow
 * (below it), else after the nodes placed. Nodes are placed downstream first, so the
 * inflows of a node placed anew stand around it.
 *
 * @param {Array<{id: string, from: string[]|null, position?: {x: number, y: number}}>}
 *   skeleton the structure with the valid positions of the document
 * @returns {{cells: Map<string, [number, number]>, moved: string[]}} the cell [x, y] of
 *   every node and the ids of the nodes placed anew, in the order of the document
 */
export function placeMissing(skeleton) {
  const inflows = inflowsOf(skeleton);
  const below = new Map();
  for (const node of skeleton) for (const up of inflows.get(node.id)) if (!below.has(up)) below.set(up, node.id);
  const cells = new Map();
  const taken = new Set();
  const waiting = [];
  for (const node of skeleton) {
    const cell = node.position ? [node.position.x, node.position.y] : null;
    if (cell && !taken.has(cellKey(cell))) {
      cells.set(node.id, cell);
      taken.add(cellKey(cell));
    } else waiting.push(node.id);
  }
  const place = (id, near, side) => {
    const cell = freeCell(taken, near, side);
    cells.set(id, cell);
    taken.add(cellKey(cell));
  };
  let left = waiting;
  while (left.length) {
    const next = [];
    for (const id of left) {
      const down = below.get(id);
      const up = inflows.get(id).find((item) => cells.has(item));
      if (down !== undefined && cells.has(down)) place(id, cells.get(down), "up");
      else if (up !== undefined) place(id, cells.get(up), "down");
      else next.push(id);
    }
    if (next.length === left.length) {
      const [first, ...rest] = next;
      const lowest = Math.max(-1, ...[...cells.values()].map((cell) => cell[0]));
      place(first, [lowest + 1, 0], "down");
      left = rest;
    } else left = next;
  }
  const order = new Set(waiting);
  return { cells, moved: skeleton.filter((node) => order.has(node.id)).map((node) => node.id) };
}

/**
 * Whether a value is an area that weighs a branch of the layout: a positive number, as
 * the library takes a headwater's `watershed.area_km2` (ADR-0013, ADR-0025).
 *
 * @param {unknown} value the area [km²], or anything
 * @returns {boolean} true for a finite number above 0
 */
export function isArea(value) {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

/**
 * The lines of the picture as the library ranks them (ADR-0013, rules 1 and 2): the
 * inflows of a node ranked by the area that drains through them when every headwater has
 * an area (isArea), else by their count of nodes, ties to the smaller id; the main stem
 * runs from the outlet up through the best inflow of every node, and a tributary starts
 * at any other inflow and joins the node it flows into. In a network that is not one tree
 * below one outlet (a file being mended), the nodes that do not reach the first outlet
 * are on lines that join nothing.
 *
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @param {Map<string, number|null>} areas the area of a subcatchment [km²], or null when
 *   it has none (a hydrograph given or read from a file)
 * @returns {Map<string, {main: boolean, joins: string|null}>} for each node whether it is
 *   on the main stem, and the node its line joins (null for the main stem)
 */
export function linesOf(skeleton, areas) {
  const inflows = inflowsOf(skeleton);
  const below = new Map();
  for (const node of skeleton) for (const up of inflows.get(node.id)) if (!below.has(up)) below.set(up, node.id);
  const heads = skeleton.filter((node) => !inflows.get(node.id).length);
  const weighed = heads.every((node) => isArea(areas.get(node.id)));
  const size = new Map();
  const drained = new Map();
  const visiting = new Set();
  const measure = (id) => {
    if (size.has(id) || visiting.has(id)) return;
    visiting.add(id);
    let count = 1;
    let area = weighed && !inflows.get(id).length ? areas.get(id) : 0;
    for (const up of [...inflows.get(id)].sort()) {
      measure(up);
      count += size.get(up) || 0;
      area += drained.get(up) || 0;
    }
    visiting.delete(id);
    size.set(id, count);
    drained.set(id, area);
  };
  for (const node of skeleton) measure(node.id);
  const rank = (a, b) => {
    if (weighed) {
      const difference = Math.round(drained.get(b) * 1e9) - Math.round(drained.get(a) * 1e9);
      if (difference) return difference;
    }
    return size.get(b) - size.get(a) || (a < b ? -1 : a > b ? 1 : 0);
  };
  const best = new Map();
  for (const node of skeleton) {
    const ranked = [...inflows.get(node.id)].sort(rank);
    if (ranked.length) best.set(node.id, ranked[0]);
  }
  const outlet = skeleton.find((node) => node.type === "outlet");
  const lines = new Map();
  for (const node of skeleton) {
    let at = node.id;
    const seen = new Set([at]);
    let found = { main: false, joins: null };
    for (;;) {
      const down = below.get(at);
      if (down === undefined) {
        found = { main: Boolean(outlet) && at === outlet.id, joins: null };
        break;
      }
      if (best.get(down) !== at) {
        found = { main: false, joins: down };
        break;
      }
      if (seen.has(down)) break;
      seen.add(down);
      at = down;
    }
    lines.set(node.id, found);
  }
  return lines;
}

/**
 * Whether a segment touches an axis-aligned box (Liang–Barsky clipping).
 *
 * @param {[number, number]} a one end [column, row]
 * @param {[number, number]} b the other end
 * @param {[number, number, number, number]} box [col0, col1, row0, row1]
 * @returns {boolean} true when some part of the segment lies in the box
 */
export function segmentTouches(a, b, box) {
  const [c0, c1, r0, r1] = box;
  const dc = b[0] - a[0];
  const dr = b[1] - a[1];
  let low = 0;
  let high = 1;
  const edges = [
    [-dc, a[0] - c0],
    [dc, c1 - a[0]],
    [-dr, a[1] - r0],
    [dr, r1 - a[1]],
  ];
  for (const [p, q] of edges) {
    if (p === 0) {
      if (q < 0) return false;
    } else {
      const ratio = q / p;
      if (p < 0) low = Math.max(low, ratio);
      else high = Math.min(high, ratio);
      if (low > high) return false;
    }
  }
  return true;
}

/**
 * Add a value to the list of a key.
 *
 * @param {Map<string, unknown[]>} lists the lists by key
 * @param {string} key the key
 * @param {unknown} value the value
 */
function listUnder(lists, key, value) {
  const list = lists.get(key);
  if (list) list.push(value);
  else lists.set(key, [value]);
}

/**
 * Where a picture's nodes and lines stand, for crowding: the nodes by their cell, and each
 * segment of an edge under every unit square of the grid (keyed by its lower corner) that
 * a step of it of at most one unit touches. A label's box then meets a few squares instead
 * of the whole picture, and crowding counts the same.
 *
 * @param {Array<{id: string, col: number, row: number}>} nodes every node
 * @param {Array<{points: Array<[number, number]>}>} edges every edge, in grid units
 * @returns {{nodes: Map<string, string[]>, segments: Array<Array<[number, number]>>,
 *   squares: Map<string, number[]>}} the ids by cell, the segments, and the indices of the
 *   segments by square
 */
export function crowdIndex(nodes, edges) {
  const byCell = new Map();
  for (const node of nodes) listUnder(byCell, `${node.col},${node.row}`, node.id);
  const segments = [];
  const squares = new Map();
  for (const edge of edges) {
    for (let index = 1; index < edge.points.length; index += 1) {
      const [a, b] = [edge.points[index - 1], edge.points[index]];
      const at = segments.push([a, b]) - 1;
      const steps = Math.max(1, Math.ceil(Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]))));
      const seen = new Set();
      for (let step = 0; step < steps; step += 1) {
        const p = [a[0] + ((b[0] - a[0]) * step) / steps, a[1] + ((b[1] - a[1]) * step) / steps];
        const q = [a[0] + ((b[0] - a[0]) * (step + 1)) / steps, a[1] + ((b[1] - a[1]) * (step + 1)) / steps];
        for (let col = Math.floor(Math.min(p[0], q[0])); col <= Math.floor(Math.max(p[0], q[0])); col += 1) {
          for (let row = Math.floor(Math.min(p[1], q[1])); row <= Math.floor(Math.max(p[1], q[1])); row += 1) {
            const key = `${col},${row}`;
            if (seen.has(key)) continue;
            seen.add(key);
            listUnder(squares, key, at);
          }
        }
      }
    }
  }
  return { nodes: byCell, segments, squares };
}

/**
 * How many lines and other nodes lie where a label of a node would stand.
 *
 * @param {{id: string, col: number, row: number}} node the node
 * @param {string} place one of PLACES
 * @param {Array<{id: string, col: number, row: number}>} nodes every node (on whole cells)
 * @param {Array<{points: Array<[number, number]>}>} edges every edge, in grid units
 * @param {object|null} [index] crowdIndex of the nodes and edges: the same count, without
 *   going through every node and line
 * @returns {number} the count
 */
export function crowding(node, place, nodes, edges, index = null) {
  const [c0, c1, r0, r1] = BOXES[place];
  const box = [node.col + c0, node.col + c1, node.row + r0, node.row + r1];
  let count = 0;
  if (index) {
    for (let col = Math.ceil(box[0]); col <= Math.floor(box[1]); col += 1) {
      for (let row = Math.ceil(box[2]); row <= Math.floor(box[3]); row += 1) {
        for (const id of index.nodes.get(`${col},${row}`) || []) if (id !== node.id) count += 1;
      }
    }
    const near = new Set();
    for (let col = Math.floor(box[0]); col <= Math.floor(box[1]); col += 1) {
      for (let row = Math.floor(box[2]); row <= Math.floor(box[3]); row += 1) {
        for (const at of index.squares.get(`${col},${row}`) || []) near.add(at);
      }
    }
    for (const at of near) if (segmentTouches(index.segments[at][0], index.segments[at][1], box)) count += 1;
    return count;
  }
  for (const other of nodes) {
    if (other.id === node.id) continue;
    if (other.col >= box[0] && other.col <= box[1] && other.row >= box[2] && other.row <= box[3]) count += 1;
  }
  for (const edge of edges) {
    for (let at = 1; at < edge.points.length; at += 1) {
      if (segmentTouches(edge.points[at - 1], edge.points[at], box)) count += 1;
    }
  }
  return count;
}

/**
 * The side of a node's label: the preferred side unless lines or nodes stand there, then
 * the free side, then below the node on either side; the least crowded place wins.
 *
 * @param {{id: string, col: number, row: number}} node the node
 * @param {"right"|"left"} preferred the side away from the line its line joins (the right
 *   on the main stem)
 * @param {Array<{id: string, col: number, row: number}>} nodes every node
 * @param {Array<{points: Array<[number, number]>}>} edges every edge, in grid units
 * @param {object|null} [index] crowdIndex of the nodes and edges (crowding)
 * @returns {string} one of PLACES
 */
export function labelPlace(node, preferred, nodes, edges, index = null) {
  const other = preferred === "right" ? "left" : "right";
  const order = [preferred, other, `${preferred}-below`, `${other}-below`];
  let best = order[0];
  let fewest = Infinity;
  for (const place of order) {
    const count = crowding(node, place, nodes, edges, index);
    if (count < fewest) {
      best = place;
      fewest = count;
    }
    if (count === 0) break;
  }
  return best;
}

/**
 * The turned picture of the placed nodes, in pixels: every node with its cell, centre,
 * line and the place of its label, and every edge by rule D (an edge for each inflow of a
 * node, so a file's broken links are drawn too). Nodes without a position are left out.
 *
 * @param {Array<{id: string, type: string, from: string[]|null,
 *   position?: {x: number, y: number}}>} skeleton the structure with the positions
 * @param {Map<string, number|null>} areas the area of each subcatchment (linesOf)
 * @returns {{nodes: Array<{id: string, type: string, cell: [number, number], cx: number,
 *   cy: number, main: boolean, place: string}>, edges: Array<{from: string, to: string,
 *   main: boolean, route: Array<[number, number]>, points: Array<[number, number]>}>}}
 *   the picture
 */
export function pictureOf(skeleton, areas) {
  const lines = linesOf(skeleton, areas);
  const placed = skeleton.filter((node) => node.position);
  const cells = new Map(placed.map((node) => [node.id, [node.position.x, node.position.y]]));
  const edges = [];
  for (const node of placed) {
    for (const up of new Set(node.from || [])) {
      if (up === node.id || !cells.has(up)) continue;
      const route = edgeRoute(cells.get(up), cells.get(node.id));
      edges.push({ from: up, to: node.id, main: lines.get(up).main, route, points: route.map(centreOf) });
    }
  }
  const grid = placed.map((node) => {
    const [col, row] = transpose(cells.get(node.id));
    return { id: node.id, col, row };
  });
  const gridEdges = edges.map((edge) => ({ points: edge.route.map(transpose) }));
  const crowd = crowdIndex(grid, gridEdges);
  const columns = new Map(grid.map((node) => [node.id, node.col]));
  const nodes = placed.map((node, index) => {
    const line = lines.get(node.id);
    const parent = line.joins !== null && columns.has(line.joins) ? columns.get(line.joins) : null;
    const preferred = parent !== null && grid[index].col < parent ? "left" : "right";
    const cell = cells.get(node.id);
    const [cx, cy] = centreOf(cell);
    return { id: node.id, type: node.type, cell, cx, cy, main: line.main, place: labelPlace(grid[index], preferred, grid, gridEdges, crowd) };
  });
  return { nodes, edges };
}

/**
 * The nearest node from a node in a direction of the turned picture (the arrow keys, D7):
 * among the nodes ahead of it, those within 45 degrees of the direction first, then the
 * nearest; ties to the node first in `nodes`.
 *
 * @param {Array<{id: string, cell: [number, number]}>} nodes the nodes with their cells
 * @param {string} from the id of the node the key is pressed on
 * @param {"up"|"down"|"left"|"right"} direction up is upstream
 * @returns {string|null} the id, or null when no node lies that way
 */
export function nearestInDirection(nodes, from, direction) {
  const start = nodes.find((node) => node.id === from);
  if (!start) return null;
  const [ax, ay] = DIRECTIONS[direction];
  let best = null;
  let bestRank = null;
  for (const node of nodes) {
    if (node.id === from) continue;
    const dx = node.cell[0] - start.cell[0];
    const dy = node.cell[1] - start.cell[1];
    const ahead = dx * ax + dy * ay;
    if (ahead <= 0) continue;
    const aside = Math.abs(dx * ay - dy * ax);
    const rank = [aside <= ahead ? 0 : 1, Math.hypot(dx * ROW, dy * COLUMN)];
    if (!bestRank || before(rank, bestRank)) {
      best = node.id;
      bestRank = rank;
    }
  }
  return best;
}

/**
 * Whether a cell lies on a route: on one of its segments, the corners included.
 *
 * @param {Array<[number, number]>} route the corners in grid units (edgeRoute's)
 * @param {[number, number]} cell [x, y]
 * @returns {boolean} true when a segment runs through the cell's centre
 */
export function onRoute(route, cell) {
  const [x, y] = cell;
  for (let index = 1; index < route.length; index += 1) {
    const [x0, y0] = route[index - 1];
    const [x1, y1] = route[index];
    const cross = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0);
    if (cross !== 0) continue;
    if (x >= Math.min(x0, x1) && x <= Math.max(x0, x1) && y >= Math.min(y0, y1) && y <= Math.max(y0, y1)) return true;
  }
  return false;
}

/**
 * The edges that run through a node other than their two (D5): a hint, not a problem, as
 * Hydrolog draws a given layout as it is placed; „Uporządkuj” lays the network out anew.
 *
 * @param {{nodes: Array<{id: string, cell: [number, number]}>, edges: Array<{from: string,
 *   to: string, route: Array<[number, number]>}>}} picture pictureOf's
 * @returns {Array<{from: string, to: string, node: string}>} each edge with a node it runs
 *   through, in the order of the edges and the nodes
 */
export function edgesThroughNodes(picture) {
  const found = [];
  for (const edge of picture.edges) {
    for (const node of picture.nodes) {
      if (node.id !== edge.from && node.id !== edge.to && onRoute(edge.route, node.cell)) {
        found.push({ from: edge.from, to: edge.to, node: node.id });
      }
    }
  }
  return found;
}

/**
 * Where the lines of a label stand: the anchor, the x of the text and the baselines.
 *
 * @param {{cx: number, cy: number, place: string}} node a node of pictureOf
 * @param {number} count the label's lines (1 to 3)
 * @returns {{anchor: "start"|"end", x: number, ys: number[]}} the placement
 */
export function labelLines(node, count) {
  const right = node.place.startsWith("right");
  const x = right ? node.cx + LABEL_GAP : node.cx - LABEL_GAP;
  const below = node.place.endsWith("below");
  const first = below ? node.cy + 16 : node.cy + 4 - ((count - 1) * LINE_HEIGHT) / 2;
  const ys = Array.from({ length: count }, (_, index) => Math.round(first + index * LINE_HEIGHT));
  return { anchor: right ? "start" : "end", x, ys };
}

/**
 * The viewBox of a picture with its labels and a ring of free cells around the nodes,
 * where a node can be dropped beyond them: the nodes' extent, an estimate of the labels'
 * widths (the type is set in CSS, so this errs on the wide side) and `ring` cells more on
 * every side.
 *
 * @param {{nodes: Array<{cx: number, cy: number, place: string}>}} picture pictureOf's
 * @param {Map<string, string[]>} labels the lines of each label
 * @param {number} [ring] the free cells around the nodes
 * @returns {[number, number, number, number]} [x, y, width, height]
 */
export function pictureBox(picture, labels, ring = 0) {
  let left = Infinity;
  let right = -Infinity;
  let top = Infinity;
  let bottom = -Infinity;
  for (const node of picture.nodes) {
    left = Math.min(left, node.cx - HALO - ring * COLUMN);
    right = Math.max(right, node.cx + HALO + ring * COLUMN);
    top = Math.min(top, node.cy - HALO - ring * ROW);
    bottom = Math.max(bottom, node.cy + HALO + ring * ROW);
    const lines = labels.get(node.id) || [];
    if (!lines.length) continue;
    const placed = labelLines(node, lines.length);
    const width = Math.max(...lines.map((line) => String(line).length)) * CHAR_PX;
    if (placed.anchor === "start") right = Math.max(right, placed.x + width);
    else left = Math.min(left, placed.x - width);
    top = Math.min(top, placed.ys[0] - 12);
    bottom = Math.max(bottom, placed.ys[placed.ys.length - 1] + 6);
  }
  if (!Number.isFinite(left)) return [0, 0, 2 * HALO, 2 * HALO];
  const margin = 8;
  return [
    Math.floor(left - margin),
    Math.floor(top - margin),
    Math.ceil(right - left + 2 * margin),
    Math.ceil(bottom - top + 2 * margin),
  ];
}
