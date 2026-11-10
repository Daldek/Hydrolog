// The canvas of „Sieć i trasowanie” (plan 2026-11-10-network-editor, D1, D6, D7, D12): the
// network drawn from the section's inputs as inline SVG, turned like ADR-0013's picture
// (the sources at the top, the outlet at the bottom), every edge by rule D from the cells
// of its two nodes and the lines ranked as the library ranks them (geometry.js). A node is
// a button named by its id, kind and result: a click, Enter or Space chooses it (its
// settings in „Dane”, its result in „Wyniki”), and the arrow keys go to the nearest node in
// their direction. A node moves to a cell of the grid by a drag (a press that moves 4 px or
// more: only the node's group follows the pointer, by its `transform` attribute, and the
// move is one edit on release; a taken cell refuses the drop), by Shift with an arrow (one
// cell) or by „Przesuń” and a click on a cell. „Uporządkuj” puts every node where Hydrolog
// lays it out. The zoom draws the viewBox larger or smaller and the card scrolls natively;
// „Dopasuj” fits the picture to the card. Nothing sets a `style` attribute (the page's
// CSP): the classes live in app.css, the marks of editing hide while the PNG is copied,
// and a polite live region says what each edit did and why a move was refused.

import { hmm, num } from "../../../format.js";
import { html, useCallback, useId, useLayoutEffect, useMemo, useRef, useState } from "../../../html.js";
import { t } from "../../../labels/common.js";
import { siec as texts } from "../../../labels/siec.js";
import { moveNode } from "./edits.js";
import { cellAt, cellKey, centreOf, HALO, labelLines, nearestInDirection, pictureBox, pictureOf, stepCell } from "./geometry.js";

/** The zoom levels of „+” and „−” (1 draws a cell 110 by 74 px). */
export const ZOOMS = Object.freeze([0.25, 0.33, 0.5, 0.67, 0.8, 1, 1.25, 1.5, 2]);

/** How far a press moves before it is a drag rather than a click [px]. */
export const DRAG_PX = 4;

/** The arrow keys and their directions in the turned picture. */
const ARROWS = Object.freeze({ ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" });

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
 * The accessible name of a node: its id, kind, description and result.
 *
 * @param {{id: string, type: string}} node the node
 * @param {object|undefined} words its description (nodeWords)
 * @param {object|undefined} value its result
 * @returns {string} the name
 */
export function nodeName(node, words, value) {
  const kind = texts.kinds[node.type] ? texts.kinds[node.type].noun : node.type;
  const parts = [`${node.id} · ${kind}`];
  if (words && words.meta) parts[0] += `, ${words.meta}`;
  if (value) {
    parts.push(
      t(texts.schematic.result, {
        peak: num(value.peak_m3s, 2),
        time: hmm(value.time_to_peak_min),
        volume: num(value.volume_m3 / 1000, 1),
      }),
    );
  }
  return parts.join(" · ");
}

/**
 * The canvas: its tools, the picture and the live region.
 *
 * @param {{inputs: {skeleton: object[], provisional?: boolean}, words: Map<string, object>,
 *   values: Map<string, object>|null, selected: string|null, tidy: {blocked: string|null},
 *   refusal: string|null, onTidy: () => void, onEdit: (inputs: object) => void,
 *   onSelect: (id: string) => void, svgRef?: {current: SVGSVGElement|null},
 *   titleId: string}} props the section's inputs (the structure with every node's
 *   position, and whether the layout is provisional), each node's description, each
 *   node's result (null before „Oblicz sieć”), the chosen node, why „Uporządkuj” cannot
 *   run now (null when it can), Hydrolog's refusal of the network, the handlers of
 *   „Uporządkuj”, of an edit (the new inputs) and of a choice, the ref of the svg (the
 *   PNG) and the id of the card's title
 * @returns {object} the canvas
 */
export function NetworkCanvas({ inputs, words, values, selected, tidy, refusal, onTidy, onEdit, onSelect, svgRef, titleId }) {
  const svg = useRef(null);
  const scroller = useRef(null);
  const marker = useRef(null);
  const drag = useRef(null);
  const dragged = useRef(false);
  const centre = useRef(null);
  const reveal = useRef(null);
  const [zoom, setZoom] = useState(null);
  const [moving, setMoving] = useState(null);
  const [keysOpen, setKeysOpen] = useState(false);
  const [focusId, setFocusId] = useState(null);
  const [said, setSaid] = useState(null);
  const id = useId();
  const keysId = `${id}-keys`;
  const listId = `${id}-list`;

  const areas = useMemo(() => new Map([...words].map(([node, word]) => [node, word.area])), [words]);
  const picture = useMemo(() => pictureOf(inputs.skeleton, areas), [inputs.skeleton, areas]);
  const owners = useMemo(() => new Map(picture.nodes.map((node) => [cellKey(node.cell), node.id])), [picture]);
  const byId = useMemo(() => new Map(picture.nodes.map((node) => [node.id, node])), [picture]);
  const labels = new Map(picture.nodes.map((node) => [node.id, labelOf(node.id, words.get(node.id), values ? values.get(node.id) : undefined)]));
  const box = pictureBox(picture, new Map([...labels].map(([node, lines]) => [node, lines.map((line) => line.text)])), 1);
  const edges = [...picture.edges].sort((a, b) => Number(a.main) - Number(b.main));
  const scale = zoom === null ? 1 : zoom;
  const roving = byId.has(focusId) ? focusId : byId.has(selected) ? selected : picture.nodes.length ? picture.nodes[0].id : null;

  const setSvg = useCallback(
    (element) => {
      svg.current = element;
      if (svgRef) svgRef.current = element;
    },
    [svgRef],
  );
  const say = (text) => setSaid((old) => ({ text, count: old ? old.count + 1 : 1 }));
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
  const showMarker = (cell, state) => {
    if (!marker.current) return;
    if (cell) {
      const [x, y] = centreOf(cell);
      marker.current.setAttribute("transform", `translate(${x} ${y})`);
    }
    marker.current.setAttribute("data-state", state);
  };

  // --- moving --------------------------------------------------------------------------
  const move = (node, cell, message) => {
    const owner = owners.get(cellKey(cell));
    if (owner && owner !== node) {
      say(t(texts.canvas.taken, { id: node, other: owner }));
      return false;
    }
    if (owner === node) return false;
    onEdit(moveNode(inputs, node, { x: cell[0], y: cell[1] }));
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
    if (move(node, cell, t(texts.canvas.movedTo, { id: node, direction: texts.canvas.directions[direction] }))) reveal.current = node;
  };
  const startMoving = () => {
    if (moving) {
      say(t(texts.canvas.moveStopped, { id: moving }));
      setMoving(null);
      showMarker(null, "off");
      return;
    }
    if (!selected || !byId.has(selected)) return;
    setMoving(selected);
    say(t(texts.canvas.prompt, { id: selected }));
  };

  // --- the pointer: one set of listeners on the svg -------------------------------------
  const finish = (current) => {
    current.element.removeAttribute("transform");
    current.element.removeAttribute("data-drag");
    if (svg.current) {
      svg.current.removeAttribute("data-drag");
      if (svg.current.hasPointerCapture(current.pointerId)) svg.current.releasePointerCapture(current.pointerId);
    }
    showMarker(null, "off");
  };
  const onPointerDown = (event) => {
    dragged.current = false;
    if (event.button !== 0 || moving || (drag.current && drag.current.active)) return;
    drag.current = null;
    const element = nodeAt(event.target);
    const placed = element ? byId.get(element.dataset.node) : null;
    const at = placed ? toPicture(event) : null;
    if (!at) return;
    drag.current = {
      id: placed.id,
      element,
      pointerId: event.pointerId,
      client: [event.clientX, event.clientY],
      from: placed.cell,
      grab: [at[0] - placed.cx, at[1] - placed.cy],
      active: false,
      target: null,
    };
  };
  const onPointerMove = (event) => {
    const current = drag.current;
    if (!current) {
      if (moving) {
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
      current.active = true;
      try {
        svg.current.setPointerCapture(event.pointerId);
      } catch {
        // The pointer is gone already: the drag goes on while it is over the picture
      }
      svg.current.setAttribute("data-drag", "");
      current.element.setAttribute("data-drag", "");
    }
    const at = toPicture(event);
    if (!at) return;
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
    const current = drag.current;
    if (!current || event.pointerId !== current.pointerId) return;
    drag.current = null;
    if (!current.active) return;
    finish(current);
    dragged.current = true;
    if (current.target) move(current.id, current.target, t(texts.canvas.moved, { id: current.id }));
  };
  const onPointerCancel = (event) => {
    const current = drag.current;
    if (!current || event.pointerId !== current.pointerId) return;
    drag.current = null;
    if (current.active) finish(current);
  };
  // A press that left the picture before it became a drag is no drag
  const onPointerLeave = () => {
    if (drag.current && !drag.current.active) drag.current = null;
    if (moving && !drag.current) showMarker(null, "off");
  };
  const onClick = (event) => {
    if (dragged.current) {
      dragged.current = false;
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
    if (element) onSelect(element.dataset.node);
  };

  // --- the keys, while a node of the canvas has the focus -------------------------------
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
  // Esc acts in the whole canvas (its tools too); the other keys while the picture has the
  // focus, so a single character never acts elsewhere (WCAG 2.1.4)
  const onKeyDown = (event) => {
    if (event.key === "Escape") {
      if (drag.current) {
        if (drag.current.active) finish(drag.current);
        drag.current = null;
      } else if (moving) {
        say(t(texts.canvas.moveStopped, { id: moving }));
        setMoving(null);
        showMarker(null, "off");
      } else if (keysOpen) setKeysOpen(false);
      else return;
      event.preventDefault();
      return;
    }
    if (!svg.current || !svg.current.contains(event.target)) return;
    if (event.altKey || event.ctrlKey || event.metaKey || drag.current) return;
    const element = nodeAt(event.target);
    const node = element ? element.dataset.node : null;
    if (Object.hasOwn(ARROWS, event.key)) {
      event.preventDefault();
      if (event.shiftKey && node) {
        moveBy(node, ARROWS[event.key]);
        return;
      }
      // From the picture's background (a click there focuses it) the arrows go to its node
      const next = node ? nearestInDirection(picture.nodes, node, ARROWS[event.key]) : roving;
      const target = next ? elementOf(next) : null;
      if (target) {
        target.focus();
        target.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
      return;
    }
    switch (event.key) {
      case "Enter":
      case " ":
        if (!node) return;
        event.preventDefault();
        onSelect(node);
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
  // by the keys the node stays in view
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
    if (!reveal.current) return;
    const element = elementOf(reveal.current);
    reveal.current = null;
    if (element) element.scrollIntoView({ block: "nearest", inline: "nearest" });
  });

  const tidyBlocked = tidy.blocked;
  const classes = ["chart-svg", "schem", zoom === null ? "fit" : "", moving ? "moving" : ""].filter(Boolean).join(" ");
  return html`<div class="canvas" onKeyDown=${onKeyDown}>
    <div class="canvas-bar" role="group" aria-label=${texts.canvas.tools}>
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
        disabled=${!moving && !(selected && byId.has(selected))}
        title=${moving ? t(texts.canvas.prompt, { id: moving }) : selected && byId.has(selected) ? texts.canvas.moveTitle : texts.canvas.moveNone}
        onClick=${startMoving}
      >
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2v16M2 10h16M10 2l-3 3M10 2l3 3M10 18l-3-3M10 18l3-3M2 10l3-3M2 10l3 3M18 10l-3-3M18 10l-3 3" /></svg>
        ${moving ? texts.canvas.moveCancel : texts.canvas.move}
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
    ${refusal ? html`<div class="form-errors" role="alert" data-schematic="error">${t(texts.schematic.failed, { message: refusal })}</div>` : null}
    ${inputs.provisional ? html`<p class="note canvas-note" data-canvas="provisional">${texts.canvas.provisional}</p>` : null}
    ${moving ? html`<p class="note canvas-note" data-canvas="prompt">${t(texts.canvas.prompt, { id: moving })}</p>` : null}
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
        onFocusCapture=${onFocusCapture}
      >
        <g class="lines">
          ${edges.map(
            (edge) => html`<polyline
              key=${`${edge.from}>${edge.to}`}
              class=${`ln ${edge.main ? "main" : "trib"}`}
              data-edge=${`${edge.from}>${edge.to}`}
              points=${edge.points.map((point) => point.join(",")).join(" ")}
            />`,
          )}
        </g>
        ${picture.nodes.map((node) => {
          const lines = labels.get(node.id);
          const placed = labelLines(node, lines.length);
          const value = values ? values.get(node.id) : undefined;
          const name = nodeName(node, words.get(node.id), value);
          const on = node.id === selected;
          return html`
            <g
              key=${node.id}
              class=${`node t-${node.type}${on ? " sel" : ""}`}
              data-node=${node.id}
              data-x=${node.cell[0]}
              data-y=${node.cell[1]}
              data-place=${node.place}
              tabindex=${node.id === roving ? "0" : "-1"}
              role="button"
              aria-pressed=${on ? "true" : "false"}
              aria-label=${name}
            >
              <title>${name}</title>
              <circle class="halo" cx=${node.cx} cy=${node.cy} r=${HALO} />
              <${Glyph} node=${node} />
              ${lines.map(
                (line, index) => html`<text class=${line.cls} x=${placed.x} y=${placed.ys[index]} text-anchor=${placed.anchor}>${line.text}</text>`,
              )}
            </g>
          `;
        })}
        <g class="drop-cell edit-mark" ref=${marker} data-state="off" aria-hidden="true">
          <rect x=${-HALO - 6} y=${-HALO - 6} width=${2 * HALO + 12} height=${2 * HALO + 12} rx="10" />
          <text class="drop-no" x=${HALO + 4} y=${-HALO + 2} text-anchor="middle">⊘</text>
        </g>
      </svg>
    </div>
    <p class="sr-only" id=${keysId}>${texts.canvas.described}</p>
    <p class="sr-only" role="status" aria-live="polite" data-canvas="said">${said ? html`<span key=${said.count}>${said.text}</span>` : null}</p>
  </div>`;
}
