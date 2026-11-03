// The layout of a section, Dane | Wykresy | Wyniki (design/README.md, plan D10):
//   html`<${ViewLayout} left=${{title, sub, body, foot}} center=${{bar, body}} right=${{title, body}} />`
// The side panels resize by dragging or by keys (arrows 16 px, Shift 64 px, Home, End,
// Enter or a double click for the default width), left 260-560 px (300) and right
// 340-720 px (400), keeping the centre at least 480 px; the widths are shared by every
// section and kept in the browser. At 860 px and below the panels are bottom sheets.

import { html, useEffect, useLayoutEffect, useRef, useState } from "../html.js";
import { shell } from "../labels/shell.js";
import { loadState, saveState } from "../persist.js";
import { closePanel, togglePanel, usePanels } from "./sheet.js";

/** Bounds of the side panels [px]. */
export const LIMITS = Object.freeze({
  left: Object.freeze({ min: 260, max: 560 }),
  right: Object.freeze({ min: 340, max: 720 }),
});

/** The narrowest centre [px]. */
export const CENTRE_MIN = 480;

const OTHER = { left: "right", right: "left" };
const widths = { left: null, right: null };
const widthListeners = new Set();
const stored = loadState("layout", null);
if (stored && typeof stored === "object") {
  for (const side of ["left", "right"]) {
    if (typeof stored[side] === "number") widths[side] = clampOwn(side, stored[side]);
  }
}

/**
 * A width within a panel's own bounds.
 *
 * @param {"left"|"right"} side the panel
 * @param {number} width the width [px]
 * @returns {number} the width within the bounds
 */
function clampOwn(side, width) {
  return Math.min(LIMITS[side].max, Math.max(LIMITS[side].min, width));
}

/**
 * The default width of a panel: the CSS variable --left-w or --right-w.
 *
 * @param {"left"|"right"} side the panel
 * @returns {number} the width [px]
 */
function cssDefault(side) {
  const value = parseInt(getComputedStyle(document.documentElement).getPropertyValue(`--${side}-w`), 10);
  return Number.isNaN(value) ? LIMITS[side].min : value;
}

/**
 * The widest a panel may be beside the other panel and the centre.
 *
 * @param {"left"|"right"} side the panel
 * @param {number} total the width of the layout [px]
 * @param {{left: boolean, right: boolean}} open which panels are open
 * @returns {number} the width [px]
 */
function maxFor(side, total, open) {
  const other = OTHER[side];
  const otherWidth = open[other] ? clampOwn(other, widths[other] ?? cssDefault(other)) : 0;
  return Math.max(LIMITS[side].min, Math.min(LIMITS[side].max, total - otherWidth - CENTRE_MIN));
}

/**
 * Set a panel's width (null: the default) for every section and keep it.
 *
 * @param {"left"|"right"} side the panel
 * @param {number|null} width the width [px]
 */
function setWidth(side, width) {
  widths[side] = width === null ? null : clampOwn(side, width);
  saveState("layout", { left: widths.left, right: widths.right });
  for (const listener of [...widthListeners]) listener({ ...widths });
}

/**
 * A resizer between a panel and the centre.
 *
 * @param {{side: "left"|"right", now: number, max: number, onWidth: (width: number|null,
 *   keep: boolean) => void}} props the panel, its width, its widest width and the handler
 * @returns {object} the separator
 */
function Resizer({ side, now, max, onWidth }) {
  const drag = useRef(null);
  const lastDown = useRef(0);
  const sign = side === "left" ? 1 : -1;
  const onPointerDown = (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    event.currentTarget.focus();
    if (event.timeStamp - lastDown.current < 400) {
      lastDown.current = 0;
      onWidth(null, true);
      return;
    }
    lastDown.current = event.timeStamp;
    drag.current = { x: event.clientX, width: now };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.currentTarget.classList.add("dragging");
    document.body.classList.add("resizing");
  };
  const onPointerMove = (event) => {
    if (!drag.current) return;
    if (Math.abs(event.clientX - drag.current.x) > 3) lastDown.current = 0;
    onWidth(Math.min(max, drag.current.width + sign * (event.clientX - drag.current.x)), false);
  };
  const end = (event) => {
    if (!drag.current) return;
    drag.current = null;
    event.currentTarget.classList.remove("dragging");
    document.body.classList.remove("resizing");
    onWidth(now, true);
  };
  const onKeyDown = (event) => {
    const step = event.shiftKey ? 64 : 16;
    let next;
    switch (event.key) {
      case "ArrowRight":
        next = now + sign * step;
        break;
      case "ArrowLeft":
        next = now - sign * step;
        break;
      case "Home":
        next = LIMITS[side].min;
        break;
      case "End":
        next = max;
        break;
      case "Enter":
        next = null;
        break;
      default:
        return;
    }
    event.preventDefault();
    onWidth(next === null ? null : Math.min(max, next), true);
  };
  return html`
    <div
      class=${`resizer r-${side}`}
      role="separator"
      aria-orientation="vertical"
      aria-label=${side === "left" ? shell.panels.resizeLeft : shell.panels.resizeRight}
      aria-valuemin=${LIMITS[side].min}
      aria-valuemax=${max}
      aria-valuenow=${now}
      tabindex="0"
      onPointerDown=${onPointerDown}
      onPointerMove=${onPointerMove}
      onPointerUp=${end}
      onPointerCancel=${end}
      onLostPointerCapture=${end}
      onKeyDown=${onKeyDown}
    ></div>
  `;
}

/**
 * One side panel: a column on a desktop, a bottom sheet on a phone.
 *
 * @param {{side: "left"|"right", panel: {title?: any, sub?: any, body: any, foot?: any},
 *   open: boolean, sheet: boolean, id: string}} props the side, its content, whether the
 *   column is open, whether its sheet is shown, and the id of its title
 * @returns {object} the panel
 */
function Panel({ side, panel, open, sheet, id }) {
  const title = panel.title || (side === "left" ? shell.panels.left : shell.panels.right);
  const closeLabel = side === "left" ? shell.panels.closeLeft : shell.panels.closeRight;
  const classes = ["view-panel", side, open ? "" : "collapsed", sheet ? "open" : ""].filter(Boolean).join(" ");
  return html`
    <aside class=${classes} aria-labelledby=${id}>
      <div class="panel-head">
        <span class="grip" aria-hidden="true" onClick=${() => closePanel(side)}></span>
        <h2 id=${id}>${title}</h2>
        ${panel.sub ? html`<span class="sub">${panel.sub}</span>` : null}
        <button class="btn ghost sm icon" type="button" aria-label=${closeLabel} onClick=${() => closePanel(side)}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" /></svg>
        </button>
      </div>
      <div class="view-panel-body">${panel.body}</div>
      ${panel.foot ? html`<div class="panel-foot">${panel.foot}</div>` : null}
    </aside>
  `;
}

let layoutCounter = 0;

/**
 * The layout of a section.
 *
 * @param {{left: {title?: any, sub?: any, body: any, foot?: any}, center: {bar?: any,
 *   body: any, label?: string}, right?: {title?: any, sub?: any, body: any, foot?: any}}}
 *   props the panel Dane, the centre (its bar and body) and the panel Wyniki
 * @returns {object} the layout
 */
export function ViewLayout({ left, center, right }) {
  const panels = usePanels();
  const box = useRef(null);
  const [ids] = useState(() => {
    layoutCounter += 1;
    return { left: `vl${layoutCounter}-left`, right: `vl${layoutCounter}-right` };
  });
  const [, setShared] = useState({ ...widths });
  const [total, setTotal] = useState(0);
  const [, setDragged] = useState(0);
  useEffect(() => {
    widthListeners.add(setShared);
    return () => widthListeners.delete(setShared);
  }, []);
  useLayoutEffect(() => {
    const measure = () => {
      if (box.current && box.current.clientWidth) setTotal(box.current.clientWidth);
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (box.current) observer.observe(box.current);
    return () => observer.disconnect();
  }, []);
  const open = { left: panels.open.left, right: Boolean(right) && panels.open.right };
  const width = (side) => {
    const max = total ? maxFor(side, total, open) : LIMITS[side].max;
    return { now: Math.min(max, clampOwn(side, widths[side] ?? cssDefault(side))), max };
  };
  const style = {};
  if (!panels.phone) {
    for (const side of ["left", "right"]) {
      style[`--${side}-w`] = open[side] ? `${width(side).now}px` : "0px";
    }
  }
  const onWidth = (side) => (next, keep) => {
    if (keep) {
      setWidth(side, next);
    } else {
      widths[side] = next === null ? null : clampOwn(side, next);
      setDragged((count) => count + 1);
    }
  };
  const openButton = (side, label) => html`
    <button
      class=${`btn sm phone-only${open[side] ? "" : " show"}`}
      type="button"
      aria-expanded=${String(panels.phone ? panels.sheet === side : open[side])}
      onClick=${() => togglePanel(side)}
    >
      ${side === "left"
        ? html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 5h12M4 10h12M4 15h8" /></svg>`
        : null}
      ${label}
    </button>
  `;
  return html`
    <div class="view-layout" ref=${box} style=${style}>
      <${Panel} side="left" panel=${left} open=${open.left} sheet=${panels.phone && panels.sheet === "left"} id=${ids.left} />
      ${open.left && !panels.phone
        ? html`<${Resizer} side="left" ...${width("left")} onWidth=${onWidth("left")} />`
        : null}
      <section class="view-center" aria-label=${center.label || shell.panels.center}>
        <div class="view-bar">
          ${openButton("left", (left && left.title) || shell.panels.left)}
          ${center.bar || null}
          ${right ? html`<div class="end">${openButton("right", right.title || shell.panels.right)}</div>` : null}
        </div>
        <div class="view-body">${center.body}</div>
      </section>
      ${right && open.right && !panels.phone
        ? html`<${Resizer} side="right" ...${width("right")} onWidth=${onWidth("right")} />`
        : null}
      ${right
        ? html`<${Panel} side="right" panel=${right} open=${open.right} sheet=${panels.phone && panels.sheet === "right"} id=${ids.right} />`
        : null}
    </div>
  `;
}
