// Panels of every section: on a desktop the columns Dane and Wyniki open or closed (shared
// by every section), at 860 px and below bottom sheets above the bottom bar, one at a time,
// with a grip, a title and a close button; Escape closes an open sheet.

import { useEffect, useState } from "../html.js";

/** Phone layout at this width and below: sheets and a bottom bar (design/README.md). */
export const PHONE = "(max-width: 860px)";

const phoneQuery = window.matchMedia(PHONE);
const state = { open: { left: true, right: true }, sheet: null };
const listeners = new Set();

/** Tell every view of the panels that they changed. */
function emit() {
  const snapshot = { open: { ...state.open }, sheet: state.sheet };
  for (const listener of [...listeners]) listener(snapshot);
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
 * Open a panel: a column on a desktop, the sheet on a phone.
 *
 * @param {"left"|"right"} side the panel
 */
export function openPanel(side) {
  if (phoneQuery.matches) state.sheet = side;
  else state.open = { ...state.open, [side]: true };
  emit();
}

/**
 * Close a panel.
 *
 * @param {"left"|"right"} side the panel
 */
export function closePanel(side) {
  if (phoneQuery.matches) {
    if (state.sheet === side) state.sheet = null;
  } else {
    state.open = { ...state.open, [side]: false };
  }
  emit();
}

/**
 * Open a closed panel, close an open one.
 *
 * @param {"left"|"right"} side the panel
 */
export function togglePanel(side) {
  const isOpen = phoneQuery.matches ? state.sheet === side : state.open[side];
  if (isOpen) closePanel(side);
  else openPanel(side);
}

/** Close the phone sheet (a section was changed). */
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
 * @returns {{open: {left: boolean, right: boolean}, sheet: "left"|"right"|null, phone: boolean}}
 */
export function usePanels() {
  const [panels, setPanels] = useState(() => ({ open: { ...state.open }, sheet: state.sheet }));
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
