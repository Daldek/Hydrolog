// The canvas of „Sieć i trasowanie” (plan 2026-11-10-network-editor, D1, D5 to D8, D12):
// the network drawn from the section's inputs as inline SVG, turned like ADR-0013's picture
// (the sources at the top, the outlet at the bottom), every edge by rule D from the cells
// of its two nodes and the lines ranked as the library ranks them (geometry.js). A node is
// a button named by its id, kind, description, result and problems: a click, Enter or
// Space chooses it (its settings in „Dane”, its result in „Wyniki”), and the arrow keys go
// to the nearest node in their direction.
//
// The network is edited here, every action by a pointer, by keys and by a single pointer
// without a drag (D7): the palette adds the five elements (a drag onto a cell, a click and
// then a cell, Enter beside the chosen node; `D` adds an inflow above a node); a drag from
// a node's handle onto another node, `P` and the arrows, or „Połącz z…” and a click
// connects it, graph.js judging the link on the target before the drop („✓” or „⊘”) and a
// second inflow into a node that takes one offering „Wstaw złącze”; a chosen link and
// Delete, or `O`, disconnects; Delete removes a node, F2 renames it in „Dane”, and the node
// menu (a right click, a long press, Shift+F10, „Węzeł…”) offers it all. A node moves to a
// cell by a drag (only the node's group follows the pointer, by its `transform` attribute,
// and the move is one edit on release; a taken cell refuses the drop), by Shift with an
// arrow or by „Przesuń” and a click. „Uporządkuj” puts every node where Hydrolog lays it
// out; „Cofnij” and „Ponów” (Ctrl+Z, Ctrl+Shift+Z, Ctrl+Y) step through the history.
//
// The problems of the structure and of the values mark their nodes („!” beside the glyph,
// in the tooltip and the name: never colour alone), the links of a cycle are dashed, and
// an edge that runs through another node is a hint (D5); the list above the picture names
// them all, each item choosing its node. Nothing sets a `style` attribute of the picture
// (the page's CSP): the classes live in app.css, and the marks of editing (handles,
// selection, problems, the drop and the verdict) hide while the PNG is copied.

import { hmm, num } from "../../../format.js";
import { Component, html, useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "../../../html.js";
import { t } from "../../../labels/common.js";
import { siec as texts } from "../../../labels/siec.js";
import { placeBelow } from "../../../ui/menu.js";
import { fullText, kindNoun, refusalText } from "../words.js";
import { canBridge, cellAbove, cellBeside, moveNode } from "./edits.js";
import {
  cellAt,
  cellKey,
  centreOf,
  COLUMN,
  edgesThroughNodes,
  HALO,
  labelLines,
  nearestInDirection,
  pictureBox,
  pictureOf,
  ROW,
  stepCell,
} from "./geometry.js";
import { linkVerdict, linkVerdicts, receiversOf, structureKey } from "./graph.js";

/** The zoom levels of „+” and „−” (1 draws a cell 110 by 74 px). */
export const ZOOMS = Object.freeze([0.25, 0.33, 0.5, 0.67, 0.8, 1, 1.25, 1.5, 2]);

/** How far a press moves before it is a drag rather than a click [px]. */
export const DRAG_PX = 4;

/** How long a touch rests on a node before it opens the node's menu [ms]. */
export const LONG_PRESS_MS = 550;

/** How long moves of one node by keys stay one step of the history [ms] (D9). */
export const KEY_MOVES_MS = 1000;

/** The five elements of the palette, in the order of the legend (D2). */
export const PALETTE = Object.freeze(["subcatchment", "reach", "reservoir", "junction", "outlet"]);

/** The handle of a node: its centre below the node's [px] and its target's radius (24 px across). */
const HANDLE_DY = 30;
const HANDLE_R = 12;

/** How near a node the pointer of a link drag must come to aim at it [px]. */
const AIM_PX = HALO + 8;

/** The arrow keys and their directions in the turned picture. */
const ARROWS = Object.freeze({ ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" });

/** The viewBox of a network without nodes: the cells around [0, 0], to drop the first element on. */
const EMPTY_BOX = Object.freeze([-2.5 * COLUMN, -1.5 * ROW, 5 * COLUMN, 5 * ROW]);

/**
 * The glyph of a node: a diamond (subcatchment), a bar across the line (reach), a circle
 * (junction), a rounded box (reservoir), a ringed circle (outlet).
 *
 * @param {{node: {type: string, cx: number, cy: number}}} props the node
 * @returns {object} the SVG shapes
 */
function Glyph({ node }) {
  const { cx, cy } = node;
  switch (node.type) {
    case "subcatchment":
      return html`<polygon class="glyph" points=${`${cx},${cy - 11} ${cx + 11},${cy} ${cx},${cy + 11} ${cx - 11},${cy}`} />`;
    case "reach":
      return html`<rect class="glyph" x=${cx - 12} y=${cy - 4} width="24" height="8" rx="2" />`;
    case "reservoir":
      return html`<rect class="glyph" x=${cx - 10} y=${cy - 13} width="20" height="26" rx="4" />`;
    case "outlet":
      return html`<circle class="glyph" cx=${cx} cy=${cy} r="11" /><circle class="glyph-in" cx=${cx} cy=${cy} r="5" />`;
    default:
      return html`<circle class="glyph" cx=${cx} cy=${cy} r="8" />`;
  }
}

/**
 * The lines of a node's label: the id (with the area of a subcatchment), its short
 * description and, with a result, the peak and the time to peak.
 *
 * @param {string} id the node's id
 * @param {{short: string, area: number|null}|undefined} words its description (nodeWords)
 * @param {{peak_m3s: number, time_to_peak_min: number}|undefined} value its result
 * @returns {Array<{cls: string, text: string}>} the lines
 */
export function labelOf(id, words, value) {
  const area = words && words.area !== null ? t(texts.schematic.area, { area: num(words.area, 1) }) : null;
  const lines = [{ cls: "lbl-id", text: area ? `${id} · ${area}` : id }];
  if (words && words.short) lines.push({ cls: "lbl-m", text: words.short });
  if (value) {
    lines.push({ cls: "lbl-v", text: t(texts.schematic.values, { peak: num(value.peak_m3s, 1), time: hmm(value.time_to_peak_min) }) });
  }
  return lines;
}

/**
 * The accessible name of a node (D12): its id, kind, description, result and problems,
 * and the edges that run through it.
 *
 * @param {{id: string, type: string}} node the node
 * @param {object|undefined} words its description (nodeWords)
 * @param {object|undefined} value its result
 * @param {{description?: string, problems?: string[], hints?: string[]}} [notes] the
 *   node's description, the texts of its problems and its hints
 * @returns {string} the name
 */
export function nodeName(node, words, value, notes = {}) {
  const kind = texts.kinds[node.type] ? texts.kinds[node.type].noun : node.type;
  const parts = [`${node.id} · ${kind}`];
  if (words && words.meta) parts[0] += `, ${words.meta}`;
  if (notes.description && notes.description.trim()) parts.push(notes.description.trim());
  if (value) {
    parts.push(
      t(texts.schematic.result, {
        peak: num(value.peak_m3s, 2),
        time: hmm(value.time_to_peak_min),
        volume: num(value.volume_m3 / 1000, 1),
      }),
    );
  }
  for (const text of notes.problems || []) parts.push(t(texts.problems.named, { text }));
  for (const text of notes.hints || []) parts.push(text);
  return parts.join(" · ");
}

/**
 * A node of the canvas: a button (D12) with its glyph, label, problem mark and handle. It
 * is drawn again only when what it shows changes (`look`, all of it as one text), so an
 * edit of a network of hundreds of nodes redraws the nodes it touched, not every node.
 *
 * @param {{look: string, node: object, lines: Array<{cls: string, text: string}>, name:
 *   string, classes: string, problems: number, focusable: boolean, on: boolean}} props
 *   what it shows as one text; the node of pictureOf, its label's lines, its accessible
 *   name, its classes, its problems' count, whether it is the node the keys reach and
 *   whether it is chosen
 */
class CanvasNode extends Component {
  shouldComponentUpdate(next) {
    return next.look !== this.props.look;
  }

  render({ node, lines, name, classes, problems, focusable, on }) {
    const placed = labelLines(node, lines.length);
    return html`
      <g
        class=${classes}
        data-node=${node.id}
        data-x=${node.cell[0]}
        data-y=${node.cell[1]}
        data-place=${node.place}
        data-problems=${problems ? String(problems) : undefined}
        tabindex=${focusable ? "0" : "-1"}
        role="button"
        aria-pressed=${on ? "true" : "false"}
        aria-label=${name}
      >
        <title>${name}</title>
        <circle class="halo" cx=${node.cx} cy=${node.cy} r=${HALO} />
        <${Glyph} node=${node} />
        ${lines.map(
          (item, index) => html`<text class=${item.cls} x=${placed.x} y=${placed.ys[index]} text-anchor=${placed.anchor}>${item.text}</text>`,
        )}
        ${problems
          ? html`<g class="mark edit-mark" aria-hidden="true">
              <circle class="mark-bg" cx=${node.cx + 14} cy=${node.cy - 14} r="8" />
              <text class="mark-t" x=${node.cx + 14} y=${node.cy - 10} text-anchor="middle">${texts.problems.mark}</text>
            </g>`
          : null}
        ${node.type !== "outlet"
          ? html`<g class="handle edit-mark" data-handle=${node.id} aria-hidden="true">
              <title>${t(texts.canvas.handle, { id: node.id })}</title>
              <circle class="handle-hit" cx=${node.cx} cy=${node.cy + HANDLE_DY} r=${HANDLE_R} />
              <circle class="handle-dot" cx=${node.cx} cy=${node.cy + HANDLE_DY} r="5" />
            </g>`
          : null}
      </g>
    `;
  }
}

/**
 * A line of the picture, an edge by rule D, drawn again only when it changes (`look`).
 *
 * @param {{look: string, edge: {key: string, line: string}, classes: string}} props what
 *   it shows as one text, the edge with its key and points, and its classes
 */
class CanvasLine extends Component {
  shouldComponentUpdate(next) {
    return next.look !== this.props.look;
  }

  render({ edge, classes }) {
    return html`<polyline class=${classes} data-edge=${edge.key} points=${edge.line} />`;
  }
}

/**
 * The hit line of an edge (24 px wide, D12) with its name: a click chooses the link. It is
 * drawn again only when the edge changes (`look`).
 *
 * @param {{look: string, edge: {from: string, to: string, key: string, line: string}}}
 *   props what it shows as one text, and the edge
 */
class CanvasHit extends Component {
  shouldComponentUpdate(next) {
    return next.look !== this.props.look;
  }

  render({ edge }) {
    return html`<polyline class="ln-hit" data-link=${edge.key} points=${edge.line}><title>${t(texts.canvas.linkName, edge)}</title></polyline>`;
  }
}

/**
 * A menu of the canvas (the node menu, the menu of a new inflow, the palette of a phone):
 * below its anchor, the first item focused; the arrows, Home and End move between the
 * items, Escape or Tab closes it and gives the focus back to the anchor, and so does a
 * click outside it.
 *
 * @param {{menu: {kind: string, label: string, anchor: Element|null, items: Array<{name:
 *   string, label: any, sub?: string, disabled?: boolean, onSelect: (event: Event) =>
 *   void}>}, onClose: () => void}} props the menu and the handler that closes it
 * @returns {object} the menu
 */
function CanvasMenu({ menu, onClose }) {
  const box = useRef(null);
  useLayoutEffect(() => {
    if (!box.current) return;
    if (menu.anchor && menu.anchor.isConnected) placeBelow(box.current, menu.anchor);
    const first = box.current.querySelector('[role="menuitem"]:not([disabled])');
    if (first) first.focus({ preventScroll: true });
  }, [menu]);
  useEffect(() => {
    const onPointer = (event) => {
      if (box.current && !box.current.contains(event.target)) onClose(false);
    };
    const onResize = () => onClose(false);
    document.addEventListener("pointerdown", onPointer, true);
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("pointerdown", onPointer, true);
      window.removeEventListener("resize", onResize);
    };
  }, [menu]);
  const onKeyDown = (event) => {
    const items = [...box.current.querySelectorAll('[role="menuitem"]:not([disabled])')];
    const at = items.indexOf(document.activeElement);
    let next = null;
    if (event.key === "ArrowDown") next = items[(at + 1) % items.length];
    else if (event.key === "ArrowUp") next = items[(at - 1 + items.length) % items.length];
    else if (event.key === "Home") next = items[0];
    else if (event.key === "End") next = items[items.length - 1];
    else if (event.key === "Escape" || event.key === "Tab") {
      event.preventDefault();
      event.stopPropagation();
      onClose(true);
      return;
    } else return;
    event.preventDefault();
    event.stopPropagation();
    if (next) next.focus();
  };
  return html`<div class="menu canvas-menu" ref=${box} role="menu" aria-label=${menu.label} data-canvas-menu=${menu.kind} onKeyDown=${onKeyDown}>
    ${menu.items.map(
      (item) => html`<button
        type="button"
        role="menuitem"
        data-item=${item.name}
        disabled=${Boolean(item.disabled)}
        onClick=${(event) => {
          onClose(true);
          item.onSelect(event);
        }}
      >
        ${item.label}${item.sub ? html`<span>${item.sub}</span>` : null}
      </button>`,
    )}
  </div>`;
}

/**
 * „Wstaw złącze” (D7, Q7): the offer of a junction when a node would take a second inflow
 * where it takes one, with „Anuluj”; its first button takes the focus, Escape cancels.
 *
 * @param {{offer: {from: string, to: string}, skeleton: object[], onAccept: () => void,
 *   onCancel: () => void}} props the link offered, the structure and the handlers
 * @returns {object} the offer
 */
export function JunctionOffer({ offer, skeleton, onAccept, onCancel }) {
  const id = useId();
  const accept = useRef(null);
  useEffect(() => {
    if (accept.current) accept.current.focus({ preventScroll: true });
  }, [offer.from, offer.to]);
  const target = skeleton.find((node) => node.id === offer.to);
  const have = target && target.from ? target.from.filter((up) => up !== offer.from).join(", ") : "–";
  return html`<div
    class="offer"
    role="alertdialog"
    aria-labelledby=${`${id}-title`}
    aria-describedby=${`${id}-text`}
    data-offer=${`${offer.from}>${offer.to}`}
    onKeyDown=${(event) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      onCancel();
    }}
  >
    <strong id=${`${id}-title`}>${texts.offer.title}</strong>
    <p id=${`${id}-text`}>${t(texts.offer.text, { to: offer.to, have, from: offer.from })}</p>
    <div class="btn-row">
      <button class="btn sm primary" type="button" ref=${accept} data-offer-action="insert" onClick=${onAccept}>${texts.offer.insert}</button>
      <button class="btn sm" type="button" data-offer-action="cancel" onClick=${onCancel}>${texts.offer.cancel}</button>
    </div>
  </div>`;
}

/**
 * The list „Problemy sieci (n)” above the picture (D8) and the hints of edges that run
 * through nodes (D5): each item of a node chooses it.
 *
 * @param {{problems: Array<{key: string, reason: string, text: string, node: string|null}>,
 *   hints: Array<{key: string, text: string, node: string}>, onChoose: (id: string) =>
 *   void}} props the problems, the hints and the handler of a choice
 * @returns {object|null} the list
 */
function ProblemList({ problems, hints, onChoose }) {
  const id = useId();
  if (!problems.length && !hints.length) return null;
  const item = (entry, mark) =>
    entry.node
      ? html`<li key=${entry.key} data-problem=${entry.reason} data-node=${entry.node}>
          <button class="link-btn" type="button" onClick=${() => onChoose(entry.node)}>
            <span class=${`problem-mark ${mark}`} aria-hidden="true">${mark === "bad" ? texts.problems.mark : "i"}</span>${entry.text}
          </button>
        </li>`
      : html`<li key=${entry.key} data-problem=${entry.reason}>
          <span class=${`problem-mark ${mark}`} aria-hidden="true">${mark === "bad" ? texts.problems.mark : "i"}</span>${entry.text}
        </li>`;
  return html`<div class="canvas-problems" data-canvas="problems">
    ${problems.length
      ? html`<h4 class="problems-title" id=${`${id}-problems`}>${t(texts.problems.title, { count: problems.length })}</h4>
          <ul aria-labelledby=${`${id}-problems`} data-list="problems">${problems.map((entry) => item(entry, "bad"))}</ul>`
      : null}
    ${hints.length
      ? html`<h4 class="problems-title" id=${`${id}-hints`}>${texts.problems.hints}</h4>
          <ul aria-labelledby=${`${id}-hints`} data-list="hints">${hints.map((entry) => item({ ...entry, reason: "through" }, "hint"))}</ul>`
      : null}
  </div>`;
}

/**
 * The canvas: its tools, the list of problems, the picture and its menus.
 *
 * @param {{inputs: {skeleton: object[], provisional?: boolean}, words: Map<string, object>,
 *   values: Map<string, object>|null, selected: string|null, rules: object, problems:
 *   {list: object[], marks: Map<string, string[]>, loops: Set<string>}, history:
 *   {canUndo: boolean, canRedo: boolean}, tidy: {blocked: string|null}, offer: object|null,
 *   onTidy: () => void, onEdit: (inputs: object, options?: object) => void, onSelect: (id:
 *   string, fromPicture?: boolean, enter?: boolean) => void, actions: object, onRename:
 *   (id: string) => void, say: (text: string) => void, svgRef?: {current:
 *   SVGSVGElement|null}, titleId: string}} props the
 *   section's inputs (the structure with every node's position, and whether the layout is
 *   provisional), each node's description and result (null before „Oblicz sieć”), the
 *   chosen node, the inflow rules of the schema (graph.js inflowRules), the problems (the
 *   list, the texts that mark each node, the links of cycles), whether there is a step to
 *   undo and to redo, why „Uporządkuj” cannot run now (null when it can), a junction
 *   offered on the canvas, the handlers of „Uporządkuj”, of a move (the new inputs and the
 *   options of the history) and of a choice, the section's edits (add, link, unlink,
 *   remove, insertJunction, undo, redo), F2's handler, the live region, the ref of the svg
 *   (the PNG) and the id of the card's title
 * @returns {object} the canvas
 */
export function NetworkCanvas({
  inputs,
  words,
  values,
  selected,
  rules,
  problems,
  history,
  tidy,
  offer,
  onTidy,
  onEdit,
  onSelect,
  actions,
  onRename,
  say,
  svgRef,
  titleId,
}) {
  const svg = useRef(null);
  const scroller = useRef(null);
  const marker = useRef(null);
  const line = useRef(null);
  const verdict = useRef(null);
  const drag = useRef(null);
  const dragged = useRef(false);
  const centre = useRef(null);
  const reveal = useRef(null);
  const focusNext = useRef(null);
  const paletteDrag = useRef(null);
  const swallowClick = useRef(false);
  const pressTimer = useRef(null);
  const [zoom, setZoom] = useState(null);
  const [moving, setMoving] = useState(null);
  const [placing, setPlacing] = useState(null);
  const [linking, setLinking] = useState(null);
  const [picked, setPicked] = useState(null);
  const [menu, setMenu] = useState(null);
  const [keysOpen, setKeysOpen] = useState(false);
  const [focusId, setFocusId] = useState(null);
  const id = useId();
  const keysId = `${id}-keys`;
  const listId = `${id}-list`;
  const skeleton = inputs.skeleton;

  const areas = useMemo(() => new Map([...words].map(([node, word]) => [node, word.area])), [words]);
  const picture = useMemo(() => pictureOf(skeleton, areas), [skeleton, areas]);
  const owners = useMemo(() => new Map(picture.nodes.map((node) => [cellKey(node.cell), node.id])), [picture]);
  const byId = useMemo(() => new Map(picture.nodes.map((node) => [node.id, node])), [picture]);
  const structure = useMemo(() => new Map(skeleton.map((node) => [node.id, node])), [skeleton]);
  // What depends on the structure alone stays while only cells and descriptions change
  const shape = useMemo(() => structureKey(skeleton), [skeleton]);
  const receivers = useMemo(() => receiversOf(skeleton), [shape]);
  const through = useMemo(() => edgesThroughNodes(picture), [picture]);
  const hintsOf = useMemo(() => {
    const found = new Map();
    for (const item of through) {
      if (!found.has(item.node)) found.set(item.node, []);
      found.get(item.node).push(t(texts.problems.throughNode, item));
    }
    return found;
  }, [through]);
  const labels = new Map(picture.nodes.map((node) => [node.id, labelOf(node.id, words.get(node.id), values ? values.get(node.id) : undefined)]));
  const box = picture.nodes.length
    ? pictureBox(picture, new Map([...labels].map(([node, lines]) => [node, lines.map((item) => item.text)])), 1)
    : EMPTY_BOX;
  // The edges with their keys and lines, the tributaries under the main stem, and those
  // that run through a node, kept while the picture stays
  const edges = useMemo(
    () =>
      [...picture.edges]
        .sort((a, b) => Number(a.main) - Number(b.main))
        .map((edge) => ({ ...edge, key: `${edge.from}>${edge.to}`, line: edge.points.map((point) => point.join(",")).join(" ") })),
    [picture],
  );
  const throughEdges = useMemo(() => new Set(through.map((item) => `${item.from}>${item.to}`)), [through]);
  const scale = zoom === null ? 1 : zoom;
  const roving = byId.has(focusId) ? focusId : byId.has(selected) ? selected : picture.nodes.length ? picture.nodes[0].id : null;
  const targets = useMemo(() => {
    if (!linking) return new Set();
    const verdicts = linkVerdicts(skeleton, rules, linking.from);
    return new Set([...verdicts].filter(([, found]) => found.ok || Boolean(found.offer)).map(([id]) => id));
  }, [linking, shape, rules]);

  const setSvg = useCallback(
    (element) => {
      svg.current = element;
      if (svgRef) svgRef.current = element;
    },
    [svgRef],
  );
  const elementOf = (node) => (svg.current ? svg.current.querySelector(`g.node[data-node="${CSS.escape(node)}"]`) : null);
  const nodeAt = (target) => {
    const element = target && typeof target.closest === "function" ? target.closest("g.node") : null;
    return element && svg.current && svg.current.contains(element) ? element : null;
  };
  // A point of the screen in the picture's units (the viewBox), whatever the zoom
  const toPicture = (event) => {
    const matrix = svg.current ? svg.current.getScreenCTM() : null;
    if (!matrix) return null;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    return [point.x, point.y];
  };
  const overPicture = (event) => {
    if (!scroller.current) return false;
    const frame = scroller.current.getBoundingClientRect();
    return event.clientX >= frame.left && event.clientX <= frame.right && event.clientY >= frame.top && event.clientY <= frame.bottom;
  };
  const showMarker = (cell, state) => {
    if (!marker.current) return;
    if (cell) {
      const [x, y] = centreOf(cell);
      marker.current.setAttribute("transform", `translate(${x} ${y})`);
    }
    marker.current.setAttribute("data-state", state);
  };
  const showVerdict = (target, state) => {
    if (!verdict.current) return;
    if (target) {
      const node = byId.get(target);
      if (node) verdict.current.setAttribute("transform", `translate(${node.cx + 20} ${node.cy - 20})`);
    }
    verdict.current.setAttribute("data-state", target ? state : "off");
  };
  // The node a link drag aims at: the nearest within its halo, never the node it starts at
  const aimAt = (point, from) => {
    let found = null;
    let nearest = AIM_PX;
    for (const node of picture.nodes) {
      if (node.id === from) continue;
      const distance = Math.hypot(point[0] - node.cx, point[1] - node.cy);
      if (distance <= nearest) {
        found = node.id;
        nearest = distance;
      }
    }
    return found;
  };
  const verdictWords = (from, to) => {
    const found = linkVerdict(skeleton, rules, from, to);
    if (found.ok) return { state: "ok", text: t(texts.canvas.target, { to }) };
    const reason = refusalText(found, skeleton, from, to);
    return { state: found.offer ? "offer" : "no", text: t(texts.canvas.targetRefused, { to, reason }) };
  };
  const stopModes = () => {
    setMoving(null);
    setPlacing(null);
    setLinking(null);
    setPicked(null);
    showMarker(null, "off");
    showVerdict(null, "off");
  };

  // --- adding ---------------------------------------------------------------------------
  const place = (type, cell) => {
    const owner = owners.get(cellKey(cell));
    if (owner) {
      say(t(texts.canvas.noRoom, { other: owner }));
      return false;
    }
    actions.add(type, cell, null);
    return true;
  };
  const addBeside = (type) => {
    const cell = cellBeside(skeleton, selected && structure.has(selected) ? selected : null);
    if (!cell) {
      say(texts.canvas.full);
      return;
    }
    const added = actions.add(type, cell, null);
    if (added) focusNext.current = added;
  };
  const addInflow = (type, into) => {
    const cell = cellAbove(skeleton, into);
    if (!cell) {
      say(texts.canvas.full);
      return;
    }
    const added = actions.add(type, cell, into);
    if (added) focusNext.current = added;
  };
  const openInflowMenu = (node, anchor) => {
    const target = structure.get(node);
    if (!target) return;
    const full = fullText(target, rules);
    if (full) {
      say(t(texts.canvas.refused, { reason: full }));
      return;
    }
    setMenu({
      kind: "inflow",
      label: t(texts.canvas.menu.inflow, { id: node }),
      anchor: anchor || elementOf(node),
      items: PALETTE.filter((type) => type !== "outlet").map((type) => ({
        name: type,
        label: html`<span class="menu-kind"><i class=${`ng t-${type}`} aria-hidden="true"></i>${texts.kinds[type].title}</span>`,
        onSelect: () => addInflow(type, node),
      })),
    });
  };
  const onPaletteClick = (type) => (event) => {
    if (swallowClick.current) {
      swallowClick.current = false;
      return;
    }
    // Enter or Space on the palette (a click without a pointer) adds beside the chosen node
    if (event.detail === 0) {
      stopModes();
      addBeside(type);
      return;
    }
    if (placing === type) {
      setPlacing(null);
      showMarker(null, "off");
      say(texts.canvas.placeStopped);
      return;
    }
    stopModes();
    setPlacing(type);
    say(t(texts.canvas.placing, { kind: kindNoun(type) }));
  };
  // The palette's button keeps the pointer from the press on (a drag leaves it at once)
  const onPalettePointerDown = (type) => (event) => {
    if (event.button !== 0 || event.pointerType === "touch") return;
    paletteDrag.current = { type, pointerId: event.pointerId, client: [event.clientX, event.clientY], active: false, cell: null, button: event.currentTarget };
    try {
      event.currentTarget.setPointerCapture(event.pointerId);
    } catch {
      // The pointer is gone already: no drag
    }
  };
  const onPalettePointerMove = (event) => {
    const current = paletteDrag.current;
    if (!current || current.pointerId !== event.pointerId) return;
    if (!current.active) {
      if (Math.hypot(event.clientX - current.client[0], event.clientY - current.client[1]) < DRAG_PX) return;
      current.active = true;
      stopModes();
      if (svg.current) svg.current.setAttribute("data-drag", "");
    }
    const at = overPicture(event) ? toPicture(event) : null;
    current.cell = at ? cellAt(at) : null;
    if (current.cell) showMarker(current.cell, owners.has(cellKey(current.cell)) ? "taken" : "ok");
    else showMarker(null, "off");
  };
  const onPalettePointerUp = (event) => {
    const current = paletteDrag.current;
    if (!current || current.pointerId !== event.pointerId) return;
    paletteDrag.current = null;
    if (!current.active) return;
    // The click that ends the drag comes in the same task: it adds nothing more
    swallowClick.current = true;
    setTimeout(() => {
      swallowClick.current = false;
    }, 0);
    if (svg.current) svg.current.removeAttribute("data-drag");
    try {
      if (current.button.hasPointerCapture(event.pointerId)) current.button.releasePointerCapture(event.pointerId);
    } catch {
      // already released
    }
    showMarker(null, "off");
    if (current.cell) place(current.type, current.cell);
    else say(texts.canvas.placeStopped);
  };
  const onPalettePointerCancel = () => {
    if (!paletteDrag.current) return;
    paletteDrag.current = null;
    if (svg.current) svg.current.removeAttribute("data-drag");
    showMarker(null, "off");
  };

  // --- moving ---------------------------------------------------------------------------
  const move = (node, cell, message, options = {}) => {
    const owner = owners.get(cellKey(cell));
    if (owner && owner !== node) {
      say(t(texts.canvas.taken, { id: node, other: owner }));
      return false;
    }
    if (owner === node) return false;
    onEdit(moveNode(inputs, node, { x: cell[0], y: cell[1] }), options);
    say(message);
    return true;
  };
  const moveBy = (node, direction) => {
    const placed = byId.get(node);
    if (!placed) return;
    const cell = stepCell(placed.cell, direction);
    if (!cell) {
      say(t(texts.canvas.edge, { id: node }));
      return;
    }
    const message = t(texts.canvas.movedTo, { id: node, direction: texts.canvas.directions[direction] });
    if (move(node, cell, message, { merge: `move:${node}`, within: KEY_MOVES_MS })) reveal.current = node;
  };
  const startMoving = (node) => {
    if (moving) {
      say(t(texts.canvas.moveStopped, { id: moving }));
      setMoving(null);
      showMarker(null, "off");
      return;
    }
    if (!node || !byId.has(node)) return;
    stopModes();
    setMoving(node);
    say(t(texts.canvas.prompt, { id: node }));
  };

  // --- linking --------------------------------------------------------------------------
  const startLinking = (node, via) => {
    const source = structure.get(node);
    if (!source) return;
    if (source.type === "outlet") {
      say(t(texts.canvas.refused, { reason: t(texts.refusals.outlet_has_downstream, { from: node }) }));
      return;
    }
    const allowed = [...linkVerdicts(skeleton, rules, node).values()].some((found) => found.ok || Boolean(found.offer));
    if (!allowed) {
      say(t(texts.canvas.noTargets, { id: node }));
      return;
    }
    stopModes();
    setLinking({ from: node, via });
    say(t(texts.canvas.linking, { id: node }));
  };
  // Make the link; a refused target keeps a link by clicks waiting for another
  const linkTo = (from, to, via) => {
    const outcome = actions.link(from, to);
    if (outcome === "refused" && via === "click") return;
    setLinking(null);
    showVerdict(null, "off");
  };

  // --- the node menu ----------------------------------------------------------------------
  const openNodeMenu = (node, anchor) => {
    const source = structure.get(node);
    if (!source) return;
    const below = receivers.get(node) || [];
    const items = [
      { name: "add-inflow", label: texts.canvas.menu.addInflow, sub: texts.canvas.menuKeys.addInflow, onSelect: () => openInflowMenu(node, anchor) },
      { name: "link", label: texts.canvas.menu.link, sub: texts.canvas.menuKeys.link, onSelect: () => startLinking(node, "click") },
      { name: "unlink", label: texts.canvas.menu.unlink, sub: texts.canvas.menuKeys.unlink, onSelect: () => actions.unlink(node, null) },
      { name: "move", label: texts.canvas.menu.move, onSelect: () => startMoving(node) },
      { name: "rename", label: texts.canvas.menu.rename, sub: texts.canvas.menuKeys.rename, onSelect: () => onRename(node) },
      { name: "remove", label: texts.canvas.menu.remove, sub: texts.canvas.menuKeys.remove, onSelect: () => remove(node, false) },
    ];
    if (canBridge(skeleton, node)) {
      items.push({
        name: "bridge",
        label: texts.canvas.menu.bridge,
        sub: t(texts.canvas.bridgeSub, { up: source.from[0], down: below[0] }),
        onSelect: () => remove(node, true),
      });
    }
    setMenu({ kind: "node", label: t(texts.canvas.menu.label, { id: node }), anchor: anchor || elementOf(node), items });
  };
  const openPaletteMenu = (anchor) => {
    setMenu({
      kind: "palette",
      label: texts.palette.menu,
      anchor,
      items: PALETTE.map((type) => ({
        name: type,
        label: html`<span class="menu-kind"><i class=${`ng t-${type}`} aria-hidden="true"></i>${texts.kinds[type].title}</span>`,
        sub: texts.palette.hints[type],
        onSelect: (event) => {
          if (event.detail === 0) {
            addBeside(type);
            return;
          }
          stopModes();
          setPlacing(type);
          say(t(texts.canvas.placing, { kind: kindNoun(type) }));
        },
      })),
    });
  };
  const closeMenu = (restore) => {
    const anchor = menu ? menu.anchor : null;
    setMenu(null);
    if (restore && anchor && anchor.isConnected && typeof anchor.focus === "function") anchor.focus({ preventScroll: true });
  };
  const remove = (node, bridge) => {
    const down = (receivers.get(node) || [])[0] || null;
    const up = (structure.get(node) || {}).from;
    const next = down || (up && up[0]) || null;
    actions.remove(node, bridge);
    focusNext.current = next || "svg";
  };

  // --- the pointer: one set of listeners on the svg -------------------------------------
  const finish = (current) => {
    if (current.element) {
      current.element.removeAttribute("transform");
      current.element.removeAttribute("data-drag");
    }
    if (line.current) line.current.setAttribute("data-state", "off");
    if (svg.current) {
      svg.current.removeAttribute("data-drag");
      if (svg.current.hasPointerCapture(current.pointerId)) svg.current.releasePointerCapture(current.pointerId);
    }
    showMarker(null, "off");
    showVerdict(null, "off");
  };
  const onPointerDown = (event) => {
    dragged.current = false;
    clearTimeout(pressTimer.current);
    if (event.button !== 0 || (drag.current && drag.current.active)) return;
    drag.current = null;
    const handle = typeof event.target.closest === "function" ? event.target.closest(".handle") : null;
    if (handle && svg.current.contains(handle) && !moving && !placing) {
      const placed = byId.get(handle.dataset.handle);
      if (placed) {
        drag.current = { kind: "link", id: placed.id, pointerId: event.pointerId, client: [event.clientX, event.clientY], active: false, target: null };
      }
      return;
    }
    if (moving || placing || linking) return;
    const element = nodeAt(event.target);
    const placed = element ? byId.get(element.dataset.node) : null;
    const at = placed ? toPicture(event) : null;
    if (!at) return;
    drag.current = {
      kind: "node",
      id: placed.id,
      element,
      pointerId: event.pointerId,
      client: [event.clientX, event.clientY],
      from: placed.cell,
      grab: [at[0] - placed.cx, at[1] - placed.cy],
      active: false,
      target: null,
    };
    // A long press of a finger opens the node's menu (D7, D12)
    if (event.pointerType === "touch") {
      pressTimer.current = setTimeout(() => {
        const current = drag.current;
        if (!current || current.active || current.id !== placed.id) return;
        drag.current = null;
        dragged.current = true;
        openNodeMenu(placed.id, element);
      }, LONG_PRESS_MS);
    }
  };
  const onPointerMove = (event) => {
    const current = drag.current;
    if (!current) {
      if (moving || placing) {
        const at = toPicture(event);
        if (!at) return;
        const cell = cellAt(at);
        const owner = owners.get(cellKey(cell));
        showMarker(cell, owner && owner !== moving ? "taken" : "ok");
      }
      return;
    }
    if (event.pointerId !== current.pointerId) return;
    if (!current.active) {
      if (Math.hypot(event.clientX - current.client[0], event.clientY - current.client[1]) < DRAG_PX) return;
      clearTimeout(pressTimer.current);
      current.active = true;
      try {
        svg.current.setPointerCapture(event.pointerId);
      } catch {
        // The pointer is gone already: the drag goes on while it is over the picture
      }
      svg.current.setAttribute("data-drag", "");
      if (current.kind === "node") current.element.setAttribute("data-drag", "");
      else if (line.current) {
        const source = byId.get(current.id);
        line.current.setAttribute("x1", String(source.cx));
        line.current.setAttribute("y1", String(source.cy + HANDLE_DY));
        line.current.setAttribute("data-state", "on");
      }
    }
    const at = toPicture(event);
    if (!at) return;
    if (current.kind === "link") {
      line.current.setAttribute("x2", String(at[0]));
      line.current.setAttribute("y2", String(at[1]));
      const target = aimAt(at, current.id);
      if (target === current.target) return;
      current.target = target;
      if (!target) {
        showVerdict(null, "off");
        return;
      }
      const found = verdictWords(current.id, target);
      showVerdict(target, found.state);
      say(found.text);
      return;
    }
    const cell = cellAt([at[0] - current.grab[0], at[1] - current.grab[1]]);
    if (current.target && current.target[0] === cell[0] && current.target[1] === cell[1]) return;
    current.target = cell;
    const [fromX, fromY] = centreOf(current.from);
    const [toX, toY] = centreOf(cell);
    current.element.setAttribute("transform", `translate(${toX - fromX} ${toY - fromY})`);
    const owner = owners.get(cellKey(cell));
    showMarker(cell, owner && owner !== current.id ? "taken" : "ok");
  };
  const onPointerUp = (event) => {
    clearTimeout(pressTimer.current);
    const current = drag.current;
    if (!current || event.pointerId !== current.pointerId) return;
    drag.current = null;
    if (!current.active) {
      // A tap on a handle starts a link by clicks: the next click chooses the target
      if (current.kind === "link") {
        dragged.current = true;
        startLinking(current.id, "click");
      }
      return;
    }
    finish(current);
    dragged.current = true;
    if (current.kind === "link") {
      if (current.target) linkTo(current.id, current.target, "drag");
      else say(t(texts.canvas.linkStopped, { id: current.id }));
      return;
    }
    if (current.target) move(current.id, current.target, t(texts.canvas.moved, { id: current.id }));
  };
  const onPointerCancel = (event) => {
    clearTimeout(pressTimer.current);
    const current = drag.current;
    if (!current || event.pointerId !== current.pointerId) return;
    drag.current = null;
    if (current.active) finish(current);
  };
  // A press that left the picture before it became a drag is no drag
  const onPointerLeave = () => {
    if (drag.current && !drag.current.active) {
      clearTimeout(pressTimer.current);
      drag.current = null;
    }
    if ((moving || placing) && !drag.current) showMarker(null, "off");
  };
  const onClick = (event) => {
    if (dragged.current) {
      dragged.current = false;
      return;
    }
    if (placing) {
      const at = toPicture(event);
      if (!at) return;
      if (place(placing, cellAt(at))) {
        setPlacing(null);
        showMarker(null, "off");
      }
      return;
    }
    if (moving) {
      const at = toPicture(event);
      if (!at) return;
      const cell = cellAt(at);
      const placed = byId.get(moving);
      if (placed && placed.cell[0] === cell[0] && placed.cell[1] === cell[1]) {
        say(t(texts.canvas.moveStopped, { id: moving }));
      } else if (!move(moving, cell, t(texts.canvas.moved, { id: moving }))) return;
      setMoving(null);
      showMarker(null, "off");
      return;
    }
    const element = nodeAt(event.target);
    if (linking) {
      if (element) linkTo(linking.from, element.dataset.node, "click");
      return;
    }
    const hit = typeof event.target.closest === "function" ? event.target.closest(".ln-hit") : null;
    if (hit && !element) {
      const [from, to] = hit.dataset.link.split(">");
      setPicked({ from, to });
      if (svg.current) svg.current.focus({ preventScroll: true });
      say(t(texts.canvas.linkChosen, { from, to }));
      return;
    }
    setPicked(null);
    if (element) onSelect(element.dataset.node);
  };
  const onContextMenu = (event) => {
    const element = nodeAt(event.target);
    if (!element) return;
    event.preventDefault();
    clearTimeout(pressTimer.current);
    if (drag.current && drag.current.active) finish(drag.current);
    drag.current = null;
    if (!menu) openNodeMenu(element.dataset.node, element);
  };

  // --- the keys ---------------------------------------------------------------------------
  const zoomTo = (next) => {
    const element = svg.current;
    const view = scroller.current;
    const matrix = element ? element.getScreenCTM() : null;
    if (matrix && view) {
      const frame = view.getBoundingClientRect();
      const point = new DOMPoint(frame.left + frame.width / 2, frame.top + frame.height / 2).matrixTransform(matrix.inverse());
      centre.current = [point.x, point.y];
    }
    setZoom(next);
    say(next === null ? texts.canvas.fitted : t(texts.canvas.zoomed, { percent: Math.round(next * 100) }));
  };
  const zoomBy = (direction) => {
    const matrix = svg.current ? svg.current.getScreenCTM() : null;
    const now = matrix ? matrix.a : scale;
    const next = direction > 0 ? ZOOMS.find((level) => level > now * 1.01) : [...ZOOMS].reverse().find((level) => level < now / 1.01);
    if (next !== undefined) zoomTo(next);
  };
  const focusNode = (node) => {
    const target = node ? elementOf(node) : null;
    if (!target) return false;
    target.focus();
    target.scrollIntoView({ block: "nearest", inline: "nearest" });
    return true;
  };
  // Esc and the history's keys act in the whole canvas (its tools too); the other keys
  // while the picture has the focus, so a single character never acts elsewhere (WCAG
  // 2.1.4)
  const onKeyDown = (event) => {
    if (event.key === "Escape") {
      if (drag.current) {
        if (drag.current.active) finish(drag.current);
        drag.current = null;
      } else if (placing) {
        setPlacing(null);
        showMarker(null, "off");
        say(texts.canvas.placeStopped);
      } else if (linking) {
        say(t(texts.canvas.linkStopped, { id: linking.from }));
        setLinking(null);
        showVerdict(null, "off");
      } else if (moving) {
        say(t(texts.canvas.moveStopped, { id: moving }));
        setMoving(null);
        showMarker(null, "off");
      } else if (picked) setPicked(null);
      else if (keysOpen) setKeysOpen(false);
      else return;
      event.preventDefault();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && !event.altKey) {
      const key = event.key.toLowerCase();
      if (key === "z") {
        if (event.shiftKey) actions.redo();
        else actions.undo();
      } else if (key === "y") actions.redo();
      else return;
      event.preventDefault();
      if (svg.current && svg.current.contains(event.target)) focusNext.current = focusId || "svg";
      return;
    }
    if (!svg.current || !svg.current.contains(event.target)) return;
    if (event.altKey || event.ctrlKey || event.metaKey || drag.current) return;
    const element = nodeAt(event.target);
    const node = element ? element.dataset.node : null;
    if (Object.hasOwn(ARROWS, event.key)) {
      event.preventDefault();
      if (event.shiftKey && node && !linking) {
        moveBy(node, ARROWS[event.key]);
        return;
      }
      if (linking) {
        // Among the targets the link may take, from the node in focus
        const among = picture.nodes.filter((item) => item.id === (node || linking.from) || targets.has(item.id));
        const next = nearestInDirection(among, node || linking.from, ARROWS[event.key]);
        if (next && focusNode(next)) {
          const found = verdictWords(linking.from, next);
          showVerdict(next, found.state);
          say(found.text);
        }
        return;
      }
      // From the picture's background (a click there focuses it) the arrows go to its node
      focusNode(node ? nearestInDirection(picture.nodes, node, ARROWS[event.key]) : roving);
      return;
    }
    if (linking && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      if (node && node !== linking.from) linkTo(linking.from, node, "keys");
      return;
    }
    if ((event.key === "Delete" || event.key === "Backspace") && picked) {
      event.preventDefault();
      actions.unlink(picked.from, picked.to);
      setPicked(null);
      return;
    }
    if (event.key === "ContextMenu" || (event.key === "F10" && event.shiftKey)) {
      if (!node) return;
      event.preventDefault();
      openNodeMenu(node, element);
      return;
    }
    switch (event.key) {
      case "Enter":
      case " ":
        if (!node) return;
        event.preventDefault();
        // Enter is the key of a node's parameters: a subcatchment's panel takes the focus
        // (plan 2026-11-10-network-wizard, D2); Space only chooses
        onSelect(node, true, event.key === "Enter");
        return;
      case "d":
      case "D":
        if (!node) return;
        event.preventDefault();
        openInflowMenu(node, element);
        return;
      case "p":
      case "P":
        if (!node) return;
        event.preventDefault();
        startLinking(node, "keys");
        return;
      case "o":
      case "O":
        if (!node) return;
        event.preventDefault();
        actions.unlink(node, null);
        return;
      case "Delete":
      case "Backspace":
        if (!node) return;
        event.preventDefault();
        remove(node, false);
        return;
      case "F2":
        if (!node) return;
        event.preventDefault();
        onRename(node);
        return;
      case "+":
      case "=":
        event.preventDefault();
        zoomBy(1);
        return;
      case "-":
      case "\u2212":
        event.preventDefault();
        zoomBy(-1);
        return;
      case "?":
        event.preventDefault();
        setKeysOpen((open) => !open);
        return;
      default:
    }
  };
  const onFocusCapture = (event) => {
    const element = nodeAt(event.target);
    if (element) setFocusId(element.dataset.node);
  };

  // After a zoom the point that was in the middle of the view stays there; after a move
  // by the keys the node stays in view; after an edit by the keys the focus goes to the
  // node it made (or to the picture when its node is gone)
  useLayoutEffect(() => {
    const point = centre.current;
    centre.current = null;
    const element = svg.current;
    const view = scroller.current;
    const matrix = element ? element.getScreenCTM() : null;
    if (!point || !matrix || !view) return;
    const at = new DOMPoint(point[0], point[1]).matrixTransform(matrix);
    const frame = view.getBoundingClientRect();
    view.scrollLeft += at.x - (frame.left + frame.width / 2);
    view.scrollTop += at.y - (frame.top + frame.height / 2);
  }, [zoom]);
  useLayoutEffect(() => {
    if (reveal.current) {
      const element = elementOf(reveal.current);
      reveal.current = null;
      if (element) element.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
    if (focusNext.current) {
      const wanted = focusNext.current;
      focusNext.current = null;
      if (!(wanted !== "svg" && focusNode(wanted)) && svg.current && !svg.current.contains(document.activeElement)) {
        svg.current.focus({ preventScroll: true });
      }
    }
  });
  useEffect(() => () => clearTimeout(pressTimer.current), []);
  // A link chosen on the canvas goes when the link does
  useEffect(() => {
    if (picked && !(structure.get(picked.to) && (structure.get(picked.to).from || []).includes(picked.from))) setPicked(null);
  }, [structure]);

  const tidyBlocked = tidy.blocked;
  const marks = problems.marks;
  const empty = !picture.nodes.length;
  const classes = ["chart-svg", "schem", zoom === null ? "fit" : "", moving || placing ? "moving" : "", linking ? "linking" : ""].filter(Boolean).join(" ");
  const chosen = selected && byId.has(selected) ? selected : null;
  const paletteButton = (type) => html`<button
    class="btn sm palette-item"
    type="button"
    data-palette=${type}
    aria-pressed=${placing === type ? "true" : "false"}
    title=${`${texts.palette.hints[type]}. ${texts.palette.how}`}
    onClick=${onPaletteClick(type)}
    onPointerDown=${onPalettePointerDown(type)}
    onPointerMove=${onPalettePointerMove}
    onPointerUp=${onPalettePointerUp}
    onPointerCancel=${onPalettePointerCancel}
  >
    <i class=${`ng t-${type}`} aria-hidden="true"></i>${texts.kinds[type].title}
  </button>`;
  const hints = through.map((item) => ({ key: `${item.from}>${item.to}@${item.node}`, text: t(texts.problems.through, item), node: item.node }));
  return html`<div class="canvas" onKeyDown=${onKeyDown}>
    <div class="canvas-bar" role="group" aria-label=${texts.canvas.tools}>
      <span class="canvas-palette" role="group" aria-label=${texts.palette.label}>${PALETTE.map(paletteButton)}</span>
      <button
        class="btn sm palette-menu"
        type="button"
        data-canvas="add"
        aria-haspopup="menu"
        aria-expanded=${menu && menu.kind === "palette" ? "true" : "false"}
        title=${texts.palette.menuTitle}
        onClick=${(event) => openPaletteMenu(event.currentTarget)}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12" /></svg>
        ${texts.palette.menu}
      </button>
      <span class="canvas-sep" aria-hidden="true"></span>
      <button
        class="btn sm"
        type="button"
        data-canvas="undo"
        aria-disabled=${history.canUndo ? "false" : "true"}
        title=${texts.canvas.undoTitle}
        onClick=${() => history.canUndo && actions.undo()}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8 5L4 9l4 4M4 9h8a4 4 0 0 1 0 8h-2" /></svg>
        ${texts.canvas.undo}
      </button>
      <button
        class="btn sm"
        type="button"
        data-canvas="redo"
        aria-disabled=${history.canRedo ? "false" : "true"}
        title=${texts.canvas.redoTitle}
        onClick=${() => history.canRedo && actions.redo()}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M12 5l4 4-4 4M16 9H8a4 4 0 0 0 0 8h2" /></svg>
        ${texts.canvas.redo}
      </button>
      <button
        class="btn sm"
        type="button"
        data-canvas="tidy"
        disabled=${Boolean(tidyBlocked)}
        title=${tidyBlocked || texts.canvas.tidyTitle}
        onClick=${() => {
          onTidy();
          say(texts.canvas.tidied);
        }}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v4M10 13v4M5 7h10M5 13h10M5 7v6M15 7v6" /></svg>
        ${texts.canvas.tidy}
      </button>
      <button
        class="btn sm"
        type="button"
        data-canvas="move"
        aria-pressed=${moving ? "true" : "false"}
        disabled=${!moving && !chosen}
        title=${moving ? t(texts.canvas.prompt, { id: moving }) : chosen ? texts.canvas.moveTitle : texts.canvas.moveNone}
        onClick=${() => startMoving(chosen)}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2v16M2 10h16M10 2l-3 3M10 2l3 3M10 18l-3-3M10 18l3-3M2 10l3-3M2 10l3 3M18 10l-3-3M18 10l-3 3" /></svg>
        ${moving ? texts.canvas.moveCancel : texts.canvas.move}
      </button>
      <button
        class="btn sm"
        type="button"
        data-canvas="node-menu"
        aria-haspopup="menu"
        aria-expanded=${menu && menu.kind === "node" ? "true" : "false"}
        disabled=${!chosen}
        title=${chosen ? texts.canvas.nodeMenuTitle : texts.canvas.nodeMenuNone}
        onClick=${(event) => openNodeMenu(chosen, event.currentTarget)}
      >
        ${texts.canvas.nodeMenu}
      </button>
      <span class="canvas-zoom">
        <button class="btn sm icon" type="button" data-canvas="zoom-out" aria-label=${texts.canvas.zoomOut} title=${texts.canvas.zoomOutTitle} onClick=${() => zoomBy(-1)}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 10h10" /></svg>
        </button>
        <button class="btn sm icon" type="button" data-canvas="zoom-in" aria-label=${texts.canvas.zoomIn} title=${texts.canvas.zoomInTitle} onClick=${() => zoomBy(1)}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 10h10M10 5v10" /></svg>
        </button>
        <button class="btn sm" type="button" data-canvas="fit" aria-pressed=${zoom === null ? "true" : "false"} title=${texts.canvas.fitTitle} onClick=${() => zoomTo(null)}>
          ${texts.canvas.fit}
        </button>
      </span>
      <button
        class="btn sm ghost"
        type="button"
        data-canvas="keys"
        aria-expanded=${keysOpen ? "true" : "false"}
        aria-controls=${listId}
        title=${texts.canvas.keysTitle}
        onClick=${() => setKeysOpen((open) => !open)}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="2" y="5" width="16" height="10" rx="2" /><path d="M5 8h1M8 8h1M11 8h1M14 8h1M6 12h8" /></svg>
        ${texts.canvas.keys}
      </button>
    </div>
    <ul class="canvas-keys" id=${listId} hidden=${!keysOpen} data-canvas="keys-list">
      ${texts.canvas.keyList.map(([keys, meaning]) => html`<li><kbd>${keys}</kbd><span>${meaning}</span></li>`)}
    </ul>
    <${ProblemList}
      problems=${problems.list}
      hints=${hints}
      onChoose=${(node) => {
        onSelect(node);
        focusNext.current = node;
      }}
    />
    ${offer
      ? html`<${JunctionOffer}
          offer=${offer}
          skeleton=${skeleton}
          onAccept=${() => {
            const made = actions.insertJunction(offer.from, offer.to);
            if (made) focusNext.current = made;
          }}
          onCancel=${() => actions.cancelOffer()}
        />`
      : null}
    ${empty ? html`<p class="note canvas-note" data-canvas="empty">${texts.canvas.empty}</p>` : null}
    ${inputs.provisional && !empty ? html`<p class="note canvas-note" data-canvas="provisional">${texts.canvas.provisional}</p>` : null}
    ${moving ? html`<p class="note canvas-note" data-canvas="prompt">${t(texts.canvas.prompt, { id: moving })}</p>` : null}
    ${placing ? html`<p class="note canvas-note" data-canvas="placing">${t(texts.canvas.placing, { kind: kindNoun(placing) })}</p>` : null}
    ${linking ? html`<p class="note canvas-note" data-canvas="linking">${t(texts.canvas.linking, { id: linking.from })}</p>` : null}
    <div class="canvas-scroll" ref=${scroller}>
      <svg
        class=${classes}
        ref=${setSvg}
        viewBox=${box.join(" ")}
        width=${Math.round(box[2] * scale)}
        height=${Math.round(box[3] * scale)}
        role="group"
        tabindex="-1"
        aria-labelledby=${titleId}
        aria-describedby=${keysId}
        data-zoom=${zoom === null ? "fit" : String(zoom)}
        onPointerDown=${onPointerDown}
        onPointerMove=${onPointerMove}
        onPointerUp=${onPointerUp}
        onPointerCancel=${onPointerCancel}
        onLostPointerCapture=${onPointerCancel}
        onPointerLeave=${onPointerLeave}
        onClick=${onClick}
        onContextMenu=${onContextMenu}
        onFocusCapture=${onFocusCapture}
      >
        <g class="lines">
          ${picked
            ? edges
                .filter((edge) => edge.from === picked.from && edge.to === picked.to)
                .map((edge) => html`<polyline key="picked" class="ln-pick edit-mark" points=${edge.line} />`)
            : null}
          ${edges.map((edge) => {
            const extra = `${problems.loops.has(edge.key) ? " loop" : ""}${throughEdges.has(edge.key) ? " through" : ""}`;
            const classes = `ln ${edge.main ? "main" : "trib"}${extra}`;
            return html`<${CanvasLine} key=${edge.key} look=${`${classes}|${edge.line}`} edge=${edge} classes=${classes} />`;
          })}
        </g>
        <g class="hits edit-mark">
          ${edges.map((edge) => html`<${CanvasHit} key=${edge.key} look=${`${edge.key}|${edge.line}`} edge=${edge} />`)}
        </g>
        ${through.map((item) => {
          const node = byId.get(item.node);
          return node ? html`<circle key=${`${item.from}>${item.to}@${item.node}`} class="through-mark edit-mark" cx=${node.cx} cy=${node.cy} r=${HALO + 5} />` : null;
        })}
        ${picture.nodes.map((node) => {
          const lines = labels.get(node.id);
          const value = values ? values.get(node.id) : undefined;
          const own = structure.get(node.id) || {};
          const wrong = marks.get(node.id) || [];
          const name = nodeName(node, words.get(node.id), value, { description: own.description, problems: wrong, hints: hintsOf.get(node.id) });
          const on = node.id === selected;
          const target = linking && targets.has(node.id);
          const classes = `node t-${node.type}${on ? " sel" : ""}${target ? " target" : ""}${linking && linking.from === node.id ? " source" : ""}${wrong.length ? " wrong" : ""}`;
          const focusable = node.id === roving;
          const look = JSON.stringify([classes, node.cell, node.place, lines, name, wrong.length, focusable, on]);
          return html`<${CanvasNode}
            key=${node.id}
            look=${look}
            node=${node}
            lines=${lines}
            name=${name}
            classes=${classes}
            problems=${wrong.length}
            focusable=${focusable}
            on=${on}
          />`;
        })}
        <line class="link-line edit-mark" ref=${line} x1="0" y1="0" x2="0" y2="0" data-state="off" aria-hidden="true" />
        <g class="verdict edit-mark" ref=${verdict} data-state="off" aria-hidden="true">
          <circle r="10" />
          <text class="verdict-ok" y="5" text-anchor="middle">${texts.canvas.ok}</text>
          <text class="verdict-no" y="5" text-anchor="middle">${texts.canvas.no}</text>
        </g>
        <g class="drop-cell edit-mark" ref=${marker} data-state="off" aria-hidden="true">
          <rect x=${-HALO - 6} y=${-HALO - 6} width=${2 * HALO + 12} height=${2 * HALO + 12} rx="10" />
          <text class="drop-no" x=${HALO + 4} y=${-HALO + 2} text-anchor="middle">⊘</text>
        </g>
      </svg>
    </div>
    <p class="sr-only" id=${keysId}>${texts.canvas.described}</p>
    ${menu ? html`<${CanvasMenu} menu=${menu} onClose=${closeMenu} />` : null}
  </div>`;
}
