// The vertical schematic of Sieć (plan D9, S4): the layout transform of
// hydrolog-network-schematic/1, a pure module without Preact or the DOM (the platform's
// kit takes it over). Hydrolog lays a network out like a metro map with `x` growing
// downstream (to the right) and `y` sideways; Sieć draws it turned, the sources at the top
// and the outlet at the bottom, so the grid is transposed: a node's column is its `y` and
// its row its `x`. The main stem is then a vertical line, the tributaries join it at 45
// degrees from both sides, and each label stands on the side of its node where no
// tributary runs.

/** Pixels per grid unit across the picture (between lines). */
export const COLUMN = 110;

/** Pixels per grid unit along the flow (between rows). */
export const ROW = 74;

/** Pixels around the nodes, before the labels. */
export const PAD = 42;

/** Pixels between a node's centre and its label. */
export const LABEL_GAP = 22;

/** Pixels between the baselines of a label's lines. */
export const LINE_HEIGHT = 14;

/** Width of a character of a label, a generous estimate [px] (12 px type). */
const CHAR_PX = 7.2;

/** The places of a label, in the order they are tried after the preferred side. */
export const PLACES = Object.freeze(["right", "left", "right-below", "left-below"]);

// The box a label takes beside its node, in grid units of the turned picture (columns
// across, rows along the flow), relative to the node: [col0, col1, row0, row1].
const BOXES = {
  right: [0.15, 1.0, -0.3, 0.3],
  left: [-1.0, -0.15, -0.3, 0.3],
  "right-below": [0.15, 1.0, 0.05, 0.65],
  "left-below": [-1.0, -0.15, 0.05, 0.65],
};

/**
 * A point of the schematic's grid in the turned picture.
 *
 * @param {[number, number]} point [x, y] of hydrolog-network-schematic/1
 * @returns {[number, number]} [column, row]
 */
export function transpose(point) {
  return [point[1], point[0]];
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
 * How many lines and other nodes lie where a label of a node would stand.
 *
 * @param {{id: string, col: number, row: number}} node the node
 * @param {string} place one of PLACES
 * @param {Array<{id: string, col: number, row: number}>} nodes every node
 * @param {Array<{points: Array<[number, number]>}>} edges every edge, in grid units
 * @returns {number} the count
 */
export function crowding(node, place, nodes, edges) {
  const [c0, c1, r0, r1] = BOXES[place];
  const box = [node.col + c0, node.col + c1, node.row + r0, node.row + r1];
  let count = 0;
  for (const other of nodes) {
    if (other.id === node.id) continue;
    if (other.col >= box[0] && other.col <= box[1] && other.row >= box[2] && other.row <= box[3]) count += 1;
  }
  for (const edge of edges) {
    for (let index = 1; index < edge.points.length; index += 1) {
      if (segmentTouches(edge.points[index - 1], edge.points[index], box)) count += 1;
    }
  }
  return count;
}

/**
 * The side of a node's label: the preferred side unless lines or nodes stand there, then
 * the free side, then below the node on either side; the least crowded place wins.
 *
 * @param {{id: string, col: number, row: number}} node the node
 * @param {"right"|"left"} preferred the side away from the parent line (the right on the
 *   main stem)
 * @param {Array<{id: string, col: number, row: number}>} nodes every node
 * @param {Array<{points: Array<[number, number]>}>} edges every edge, in grid units
 * @returns {string} one of PLACES
 */
export function labelPlace(node, preferred, nodes, edges) {
  const other = preferred === "right" ? "left" : "right";
  const order = [preferred, other, `${preferred}-below`, `${other}-below`];
  let best = order[0];
  let fewest = Infinity;
  for (const place of order) {
    const count = crowding(node, place, nodes, edges);
    if (count < fewest) {
      best = place;
      fewest = count;
    }
    if (count === 0) break;
  }
  return best;
}

/**
 * The turned picture of a schematic, in pixels: every node with its centre and the place
 * of its label, every edge as a polyline, and the extent of the nodes.
 *
 * @param {object} schematic a hydrolog-network-schematic/1 document
 * @returns {{outlet: string, nodes: Array<{id: string, type: string, col: number,
 *   row: number, cx: number, cy: number, line: number, main: boolean, place: string}>,
 *   edges: Array<{from: string, to: string, line: number, main: boolean,
 *   points: Array<[number, number]>}>, columns: number, rows: number}} the picture
 */
export function verticalLayout(schematic) {
  const lines = new Map((schematic.lines || []).map((line) => [line.index, line]));
  const gridNodes = (schematic.nodes || []).map((node) => {
    const [col, row] = transpose([node.x, node.y]);
    return { id: node.id, type: node.type, col, row, line: node.line };
  });
  const byId = new Map(gridNodes.map((node) => [node.id, node]));
  const gridEdges = (schematic.edges || []).map((edge) => ({
    from: edge.from,
    to: edge.to,
    line: edge.line,
    points: (edge.points || []).map(transpose),
  }));
  // The column of a line's parent (the line its last node flows into), for the side of
  // a tributary's labels: away from its parent.
  const parentColumn = (line) => {
    const entry = lines.get(line);
    if (!entry || entry.role === "main" || !entry.joins) return null;
    const joined = byId.get(entry.joins);
    return joined ? joined.col : null;
  };
  const nodes = gridNodes.map((node) => {
    const parent = parentColumn(node.line);
    const preferred = parent !== null && node.col < parent ? "left" : "right";
    return {
      ...node,
      cx: PAD + node.col * COLUMN,
      cy: PAD + node.row * ROW,
      main: (lines.get(node.line) || {}).role === "main",
      place: labelPlace(node, preferred, gridNodes, gridEdges),
    };
  });
  const edges = gridEdges.map((edge) => ({
    ...edge,
    main: (lines.get(edge.line) || {}).role === "main",
    points: edge.points.map(([col, row]) => [PAD + col * COLUMN, PAD + row * ROW]),
  }));
  const columns = gridNodes.reduce((most, node) => Math.max(most, node.col), 0);
  const rows = gridNodes.reduce((most, node) => Math.max(most, node.row), 0);
  return { outlet: schematic.outlet, nodes, edges, columns, rows };
}

/**
 * Where the lines of a label stand: the anchor, the x of the text and the baselines.
 *
 * @param {{cx: number, cy: number, place: string}} node a node of verticalLayout
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
 * The viewBox of a picture with its labels: the nodes' extent and an estimate of the
 * labels' widths (the type is set in CSS, so this errs on the wide side).
 *
 * @param {{nodes: Array<{cx: number, cy: number, place: string}>}} picture verticalLayout's
 * @param {Map<string, string[]>|Object<string, string[]>} labels the lines of each label
 * @returns {[number, number, number, number]} [x, y, width, height]
 */
export function pictureBox(picture, labels) {
  const linesOf = (id) => (labels instanceof Map ? labels.get(id) : labels[id]) || [];
  let left = Infinity;
  let right = -Infinity;
  let top = Infinity;
  let bottom = -Infinity;
  for (const node of picture.nodes) {
    left = Math.min(left, node.cx - 24);
    right = Math.max(right, node.cx + 24);
    top = Math.min(top, node.cy - 24);
    bottom = Math.max(bottom, node.cy + 24);
    const lines = linesOf(node.id);
    if (!lines.length) continue;
    const placed = labelLines(node, lines.length);
    const width = Math.max(...lines.map((line) => String(line).length)) * CHAR_PX;
    if (placed.anchor === "start") right = Math.max(right, placed.x + width);
    else left = Math.min(left, placed.x - width);
    top = Math.min(top, placed.ys[0] - 12);
    bottom = Math.max(bottom, placed.ys[placed.ys.length - 1] + 6);
  }
  if (!Number.isFinite(left)) return [0, 0, 2 * PAD, 2 * PAD];
  const margin = 8;
  return [
    Math.floor(left - margin),
    Math.floor(top - margin),
    Math.ceil(right - left + 2 * margin),
    Math.ceil(bottom - top + 2 * margin),
  ];
}
