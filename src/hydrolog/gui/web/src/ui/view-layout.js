// The layout of a section, Dane | Wykresy | Wyniki (design/README.md, plan D10):
//   html`<${ViewLayout} left=${{title, sub, body, foot}} detail=${{title, sub, body, foot,
//     onClose}} center=${{bar, body}} right=${{title, body}} sources=${lines} />`
// The side panels resize by dragging or by keys (arrows 16 px, Shift 64 px, Home, End,
// Enter or a double click for the default width), left 260-560 px (300) and right
// 340-720 px (400), keeping the centre at least 480 px; the widths are shared by every
// section and kept in the browser. At 860 px and below the panels are bottom sheets.
// `detail` (null: none) is a second left panel (plan 2026-11-10-network-wizard, D2): a
// column right of Dane named by its title, 260-560 px (300), whose ✕ calls `onClose`.
// While it is there and the open columns do not fit beside a centre of 480 px, Wyniki
// narrows first, to 340 px, then Dane and the panel evenly, to 260 px: the wanted widths
// stay, only the shown ones shrink, and a resizer goes as far as the centre keeps 480 px.
// Where even that leaves the centre narrower (a layout under 1340 px with Dane open),
// Wyniki is not shown while the panel is: its button in the bar shows it in the panel's
// place, and its ✕ there, another title or openPanel("detail") bring the panel back, Wyniki
// staying open for the other sections. On a phone the panel is the sheet "detail", which
// alternates with Dane's: its „← Dane” shows Dane's sheet, its ✕ closes the sheet, and
// without a `detail` that sheet shows Dane.
// `sources` is the providers' lines of the data the view shows ({attribution,
// terms_notice}; none: null): the view's one strip of them under the centre (sources.js).

import { html, useEffect, useLayoutEffect, useRef, useState } from "../html.js";
import { shell } from "../labels/shell.js";
import { loadState, saveState } from "../persist.js";
import { closePanel, closeSheet, openPanel, togglePanel, usePanels } from "./sheet.js";
import { Sources } from "./sources.js";

/** Bounds of the side panels [px]. */
export const LIMITS = Object.freeze({
  left: Object.freeze({ min: 260, max: 560 }),
  detail: Object.freeze({ min: 260, max: 560 }),
  right: Object.freeze({ min: 340, max: 720 }),
});

/** The narrowest centre [px]. */
export const CENTRE_MIN = 480;

/** The side panels in the order of their columns. */
const SIDES = ["left", "detail", "right"];
const OTHER = { left: "right", right: "left" };
/** The texts of each side panel: its title when the section gives none, its ✕, its resizer. */
const TEXTS = {
  left: { title: shell.panels.left, close: shell.panels.closeLeft, resize: shell.panels.resizeLeft },
  detail: { title: null, close: shell.panels.closeDetail, resize: shell.panels.resizeDetail },
  right: { title: shell.panels.right, close: shell.panels.closeRight, resize: shell.panels.resizeRight },
};
const widths = { left: null, detail: null, right: null };
const widthListeners = new Set();
const stored = loadState("layout", null);
if (stored && typeof stored === "object") {
  for (const side of SIDES) {
    if (typeof stored[side] === "number") widths[side] = clampOwn(side, stored[side]);
  }
}

/**
 * A width within a panel's own bounds.
 *
 * @param {"left"|"detail"|"right"} side the panel
 * @param {number} width the width [px]
 * @returns {number} the width within the bounds
 */
function clampOwn(side, width) {
  return Math.min(LIMITS[side].max, Math.max(LIMITS[side].min, width));
}

/** The CSS default widths read, by panel and the window's width (a media query sets them). */
const defaults = new Map();

/**
 * The default width of a panel: the CSS variable --left-w, --detail-w or --right-w of the
 * root. It is read once per width of the window: reading a computed style while the page
 * has changed makes the browser restyle it there and then, which a network of hundreds of
 * nodes pays on every render.
 *
 * @param {"left"|"detail"|"right"} side the panel
 * @returns {number} the width [px]
 */
function cssDefault(side) {
  const key = `${side}:${window.innerWidth}`;
  if (defaults.has(key)) return defaults.get(key);
  const value = parseInt(getComputedStyle(document.documentElement).getPropertyValue(`--${side}-w`), 10);
  // Not yet styled (no value): the bound now, the CSS's value once it is there
  if (Number.isNaN(value)) return LIMITS[side].min;
  defaults.set(key, value);
  return value;
}

/**
 * The widest a panel of a layout without `detail` may be beside the other panel and the
 * centre.
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
 * The shown widths of the open columns of a layout with `detail` (plan
 * 2026-11-10-network-wizard, D2): where they do not fit beside a centre of CENTRE_MIN,
 * Wyniki narrows first, to its least width, then Dane and the panel evenly, to theirs.
 *
 * @param {number} total the width of the layout [px]
 * @param {{left?: number, detail?: number, right?: number}} wanted the wanted widths of the
 *   open columns [px]
 * @returns {{left?: number, detail?: number, right?: number}} their shown widths [px]
 */
function fit(total, wanted) {
  const shown = { ...wanted };
  let over = Object.values(shown).reduce((sum, width) => sum + width, 0) + CENTRE_MIN - total;
  if (over > 0 && shown.right !== undefined) {
    const cut = Math.min(over, shown.right - LIMITS.right.min);
    shown.right -= cut;
    over -= cut;
  }
  // Evenly: the one with less room to give gives at most half, the other the rest
  const pair = ["left", "detail"]
    .filter((side) => shown[side] !== undefined)
    .sort((a, b) => shown[a] - LIMITS[a].min - (shown[b] - LIMITS[b].min));
  pair.forEach((side, index) => {
    if (over <= 0) return;
    const cut = Math.min(Math.ceil(over / (pair.length - index)), shown[side] - LIMITS[side].min);
    shown[side] -= cut;
    over -= cut;
  });
  return shown;
}

/**
 * Set a panel's width (null: the default) for every section and keep it.
 *
 * @param {"left"|"detail"|"right"} side the panel
 * @param {number|null} width the width [px]
 */
function setWidth(side, width) {
  widths[side] = width === null ? null : clampOwn(side, width);
  // The panel's width only once set: without one the layout keeps what it always kept
  const kept = { left: widths.left, right: widths.right };
  if (widths.detail !== null) kept.detail = widths.detail;
  saveState("layout", kept);
  for (const listener of [...widthListeners]) listener({ ...widths });
}

/**
 * A resizer between a panel and the centre.
 *
 * @param {{side: "left"|"detail"|"right", now: number, max: number, onWidth: (width:
 *   number|null, keep: boolean) => void}} props the panel, its width, its widest width and
 *   the handler
 * @returns {object} the separator
 */
function Resizer({ side, now, max, onWidth }) {
  const drag = useRef(null);
  const lastDown = useRef(0);
  const sign = side === "right" ? -1 : 1;
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
      aria-label=${TEXTS[side].resize}
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
 * @param {{side: "left"|"detail"|"right", panel: {title?: any, sub?: any, body: any,
 *   foot?: any}, open: boolean, sheet: boolean, id: string, onClose: () => void,
 *   onBack?: () => void}} props the side, its content, whether the column is shown,
 *   whether its sheet is shown, the id of its title, its ✕ and, on a phone, „← Dane”
 * @returns {object} the panel
 */
function Panel({ side, panel, open, sheet, id, onClose, onBack }) {
  const title = panel.title || TEXTS[side].title;
  const classes = ["view-panel", side, open ? "" : "collapsed", sheet ? "open" : ""].filter(Boolean).join(" ");
  return html`
    <aside class=${classes} aria-labelledby=${id}>
      <div class="panel-head">
        <span class="grip" aria-hidden="true" onClick=${onClose}></span>
        ${onBack
          ? html`<button class="btn sm phone-only back" type="button" onClick=${onBack}>
              ${shell.panels.backToLeft}
            </button>`
          : null}
        <h2 id=${id}>${title}</h2>
        ${panel.sub ? html`<span class="sub">${panel.sub}</span>` : null}
        <button class="btn ghost sm icon" type="button" aria-label=${TEXTS[side].close} onClick=${onClose}>
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
 * @param {{left: {title?: any, sub?: any, body: any, foot?: any}, detail?: {title: any,
 *   sub?: any, body: any, foot?: any, onClose: () => void}|null, center: {bar?: any,
 *   body: any, label?: string}, right?: {title?: any, sub?: any, body: any, foot?: any},
 *   sources?: {attribution: string[], terms_notice: string[]}|null}} props the panel
 *   Dane, the second left panel (none: null), the centre (its bar and body), the panel
 *   Wyniki and the providers' lines of the view's data (none: null)
 * @returns {object} the layout
 */
export function ViewLayout({ left, detail, center, right, sources = null }) {
  const panels = usePanels();
  const box = useRef(null);
  const [ids] = useState(() => {
    layoutCounter += 1;
    return {
      left: `vl${layoutCounter}-left`,
      detail: `vl${layoutCounter}-detail`,
      right: `vl${layoutCounter}-right`,
    };
  });
  const [, setShared] = useState({ ...widths });
  const [total, setTotal] = useState(0);
  const [, setDragged] = useState(0);
  // Wyniki shown in the panel's place: the showing of the panel it was asked in
  const [inPlace, setInPlace] = useState(null);
  // Every showing of the panel (given, or given another title) counts
  const showing = useRef({ title: null, count: 0 });
  const title = detail ? String(detail.title) : null;
  if (showing.current.title !== title) showing.current = { title, count: showing.current.count + 1 };
  const here = `${showing.current.count}:${panels.detailOpened}`;
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
  // Too narrow for every open column at its least width beside the centre: there the
  // panel and Wyniki take turns
  const narrow =
    Boolean(detail && right) &&
    !panels.phone &&
    total > 0 &&
    (panels.open.left ? LIMITS.left.min : 0) + LIMITS.detail.min + LIMITS.right.min + CENTRE_MIN > total;
  const front = narrow && panels.open.right ? (inPlace === here ? "right" : "detail") : null;
  const open = {
    left: panels.open.left,
    detail: Boolean(detail) && front !== "right",
    right: Boolean(right) && panels.open.right && front !== "detail",
  };
  const wanted = (side) => clampOwn(side, widths[side] ?? cssDefault(side));
  // The wanted widths of the open columns, some of them changed
  const wantedWith = (change) => {
    const all = {};
    for (const side of SIDES) if (open[side]) all[side] = change[side] ?? wanted(side);
    return all;
  };
  const fitted = detail && total ? fit(total, wantedWith({})) : null;
  const width = (side) => {
    if (fitted) return { now: fitted[side], max: fit(total, wantedWith({ [side]: LIMITS[side].max }))[side] };
    const max = total ? maxFor(side, total, open) : LIMITS[side].max;
    return { now: Math.min(max, wanted(side)), max };
  };
  // The least wanted width that the fit shows as `target` (the shown one grows with it)
  const wantedFor = (side, target) => {
    let low = LIMITS[side].min;
    let high = LIMITS[side].max;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (fit(total, wantedWith({ [side]: middle }))[side] >= target) high = middle;
      else low = middle + 1;
    }
    return low;
  };
  const sizes = {};
  const style = {};
  if (!panels.phone) {
    for (const side of SIDES) {
      if (open[side]) sizes[side] = width(side);
      style[`--${side}-w`] = open[side] ? `${sizes[side].now}px` : "0px";
    }
  }
  const onWidth = (side) => (next, keep) => {
    let value = null;
    if (next !== null) value = fitted ? wantedFor(side, next) : clampOwn(side, next);
    if (keep) {
      setWidth(side, value);
    } else {
      widths[side] = value;
      setDragged((count) => count + 1);
    }
  };
  // The sheet shown on a phone: "detail" without a panel shows Dane
  const sheet = panels.phone ? (panels.sheet === "detail" && !detail ? "left" : panels.sheet) : null;
  const toggle = (side) => {
    if (panels.phone) {
      if (sheet === side) closeSheet();
      else openPanel(side);
    } else if (side === "right" && narrow) {
      // In the panel's place and back; Wyniki stays open for the other sections
      if (front === "right") {
        setInPlace(null);
      } else {
        if (!panels.open.right) openPanel("right");
        setInPlace(here);
      }
    } else {
      togglePanel(side);
    }
  };
  const close = (side) => () => {
    if (panels.phone) closeSheet();
    else if (side === "detail") detail.onClose();
    else if (side === "right" && front === "right") setInPlace(null);
    else closePanel(side);
  };
  const openButton = (side, label) => html`
    <button
      class=${`btn sm phone-only${open[side] ? "" : " show"}`}
      type="button"
      aria-expanded=${String(panels.phone ? sheet === side : open[side])}
      onClick=${() => toggle(side)}
    >
      ${side === "left"
        ? html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 5h12M4 10h12M4 15h8" /></svg>`
        : null}
      ${label}
    </button>
  `;
  return html`
    <div class="view-layout" ref=${box} style=${style}>
      <${Panel}
        side="left"
        panel=${left}
        open=${open.left}
        sheet=${sheet === "left"}
        id=${ids.left}
        onClose=${close("left")}
      />
      ${open.left && !panels.phone
        ? html`<${Resizer} side="left" ...${sizes.left} onWidth=${onWidth("left")} />`
        : null}
      ${detail
        ? html`<${Panel}
            side="detail"
            panel=${detail}
            open=${open.detail}
            sheet=${sheet === "detail"}
            id=${ids.detail}
            onClose=${close("detail")}
            onBack=${() => openPanel("left")}
          />`
        : null}
      ${open.detail && !panels.phone
        ? html`<${Resizer} side="detail" ...${sizes.detail} onWidth=${onWidth("detail")} />`
        : null}
      <section class="view-center" aria-label=${center.label || shell.panels.center}>
        <div class="view-bar">
          ${openButton("left", (left && left.title) || shell.panels.left)}
          ${center.bar || null}
          ${right ? html`<div class="end">${openButton("right", right.title || shell.panels.right)}</div>` : null}
        </div>
        <div class="view-body">${center.body}</div>
        <${Sources} lines=${sources} />
      </section>
      ${right && open.right && !panels.phone
        ? html`<${Resizer} side="right" ...${sizes.right} onWidth=${onWidth("right")} />`
        : null}
      ${right
        ? html`<${Panel}
            side="right"
            panel=${right}
            open=${open.right}
            sheet=${sheet === "right"}
            id=${ids.right}
            onClose=${close("right")}
          />`
        : null}
    </div>
  `;
}
