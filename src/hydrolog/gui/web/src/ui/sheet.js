// Panels of every section: on a desktop the columns Dane and Wyniki open or closed (shared
// by every section), at 860 px and below bottom sheets above the bottom bar, one at a time,
// with a grip, a title and a close button; Escape closes an open sheet. A section's second
// left panel (ViewLayout's `detail`, plan 2026-11-10-network-wizard D2) is the sheet
// "detail" on a phone, which takes the place of Dane's sheet (the two alternate). On a
// desktop its column is there while the section gives it and closes with the section's
// `onClose`; openPanel("detail") shows it again where a layout too narrow for it and
// Wyniki shows Wyniki in its place.

import { useEffect, useState } from "../html.js";

/** Phone layout at this width and below: sheets and a bottom bar (design/README.md). */
const PHONE = "(max-width: 860px)";

const phoneQuery = window.matchMedia(PHONE);
// detailOpened counts openPanel("detail") on a desktop: a layout that shows Wyniki in the
// panel's place shows the panel again when it changes
const state = { open: { left: true, right: true }, sheet: null, detailOpened: 0 };
const listeners = new Set();

/**
 * The panels' state as a view keeps it.
 *
 * @returns {{open: {left: boolean, right: boolean}, sheet: "left"|"detail"|"right"|null,
 *   detailOpened: number}} a copy of the state
 */
function snapshot() {
  return { open: { ...state.open }, sheet: state.sheet, detailOpened: state.detailOpened };
}

/** Tell every view of the panels that they changed. */
function emit() {
  const copy = snapshot();
  for (const listener of [...listeners]) listener(copy);
}

phoneQuery.addEventListener("change", () => {
  state.sheet = null;
  emit();
});

/**
 * Whether the page is in the phone layout.
 *
 * @returns {boolean} true at 860 px and below
 */
export function isPhone() {
  return phoneQuery.matches;
}

/**
 * Open a panel: a column on a desktop, the sheet on a phone. The panel "detail" has no
 * open state of its own on a desktop (its section gives it or not): there it is shown again
 * where a layout too narrow for it and Wyniki shows Wyniki in its place.
 *
 * @param {"left"|"detail"|"right"} side the panel
 */
export function openPanel(side) {
  if (phoneQuery.matches) state.sheet = side;
  else if (side === "detail") state.detailOpened += 1;
  else state.open = { ...state.open, [side]: true };
  emit();
}

/**
 * Close a panel. On a desktop the panel "detail" is closed by its section (ViewLayout's
 * `detail.onClose`), not here.
 *
 * @param {"left"|"detail"|"right"} side the panel
 */
export function closePanel(side) {
  if (phoneQuery.matches) {
    if (state.sheet === side) state.sheet = null;
  } else if (side !== "detail") {
    state.open = { ...state.open, [side]: false };
  }
  emit();
}

/**
 * Open a closed panel, close an open one; on a desktop the panel "detail" is only opened
 * (see closePanel).
 *
 * @param {"left"|"detail"|"right"} side the panel
 */
export function togglePanel(side) {
  const isOpen = phoneQuery.matches ? state.sheet === side : state.open[side];
  if (isOpen) closePanel(side);
  else openPanel(side);
}

/** Close the phone sheet, whichever it is (a section was changed, Escape, a sheet's ✕). */
export function closeSheet() {
  if (state.sheet === null) return;
  state.sheet = null;
  emit();
}

/**
 * Whether a sheet is open on a phone.
 *
 * @returns {boolean} true when a sheet is shown
 */
export function sheetOpen() {
  return phoneQuery.matches && state.sheet !== null;
}

/**
 * The panels' state and the phone layout, updated on every change.
 *
 * @returns {{open: {left: boolean, right: boolean}, sheet: "left"|"detail"|"right"|null,
 *   detailOpened: number, phone: boolean}}
 */
export function usePanels() {
  const [panels, setPanels] = useState(snapshot);
  const [phone, setPhone] = useState(phoneQuery.matches);
  useEffect(() => {
    const onPhone = () => setPhone(phoneQuery.matches);
    listeners.add(setPanels);
    phoneQuery.addEventListener("change", onPhone);
    return () => {
      listeners.delete(setPanels);
      phoneQuery.removeEventListener("change", onPhone);
    };
  }, []);
  return { ...panels, phone };
}
