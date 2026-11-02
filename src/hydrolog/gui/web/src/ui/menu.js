// A button that opens a menu below it (the mockup's `.menu`): arrow keys move between the
// items, Escape or a click outside closes it and gives the focus back to the button.

import { html, useEffect, useLayoutEffect, useRef, useState } from "../html.js";

/**
 * Place a floating element below an anchor, inside the window.
 *
 * @param {HTMLElement} element the floating element (position: fixed)
 * @param {HTMLElement} anchor the element it belongs to
 */
export function placeBelow(element, anchor) {
  const box = anchor.getBoundingClientRect();
  const width = element.offsetWidth;
  const height = element.offsetHeight;
  const left = Math.min(box.left, window.innerWidth - width - 12);
  let top = box.bottom + 6;
  if (top + height > window.innerHeight - 12) top = Math.max(12, box.top - height - 6);
  element.style.left = `${Math.max(12, left)}px`;
  element.style.top = `${Math.max(12, top)}px`;
}

/**
 * A menu button.
 *
 * @param {{label: any, items: Array<{label: any, sub?: string, onSelect: () => void,
 *   disabled?: boolean}>, className?: string, title?: string, menuLabel: string}} props the
 *   button's content, the items, the button's classes and title, and the menu's name
 * @returns {object} the button and its menu
 */
export function MenuButton({ label, items, className = "btn sm", title, menuLabel }) {
  const [open, setOpen] = useState(false);
  const button = useRef(null);
  const menu = useRef(null);
  useLayoutEffect(() => {
    if (!open || !menu.current) return;
    placeBelow(menu.current, button.current);
    const first = menu.current.querySelector("button:not([disabled])");
    if (first) first.focus({ preventScroll: true });
  }, [open]);
  useEffect(() => {
    if (!open) return undefined;
    const onPointer = (event) => {
      if (!menu.current.contains(event.target) && !button.current.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        button.current.focus();
      }
    };
    const onResize = () => setOpen(false);
    document.addEventListener("pointerdown", onPointer, true);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("pointerdown", onPointer, true);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
    };
  }, [open]);
  const onMenuKey = (event) => {
    const step = { ArrowDown: 1, ArrowUp: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const buttons = [...menu.current.querySelectorAll("button:not([disabled])")];
    const index = buttons.indexOf(document.activeElement);
    const next = buttons[(index + step + buttons.length) % buttons.length];
    if (next) next.focus();
  };
  return html`
    <button
      ref=${button}
      type="button"
      class=${className}
      title=${title}
      aria-haspopup="menu"
      aria-expanded=${String(open)}
      onClick=${() => setOpen(!open)}
    >
      ${label}
    </button>
    ${open
      ? html`<div class="menu" ref=${menu} role="menu" aria-label=${menuLabel} onKeyDown=${onMenuKey}>
          ${items.map(
            (item) => html`<button
              type="button"
              role="menuitem"
              disabled=${item.disabled}
              onClick=${() => {
                setOpen(false);
                button.current.focus();
                item.onSelect();
              }}
            >
              ${item.label}${item.sub ? html`<span>${item.sub}</span>` : null}
            </button>`,
          )}
        </div>`
      : null}
  `;
}
