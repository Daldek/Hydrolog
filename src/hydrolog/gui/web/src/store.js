// State shared by sections (plan D9, interfaces):
//   useStore("watershed")  Hydrogram's watershed, the `watershed` of hydrolog-network/1;
//                          Kalkulatory reads it.
//   useStore("reference")  {label, peak_m3s, source}: a Statystyka quantile drawn on the
//                          hydrograph.
//   useStore("status")     the badge of the top bar: {state, text, title?} with state
//                          ok | busy | stale | invalid | error.
//   useStore("context")    the context of the breadcrumbs and the page title, e.g.
//                          "Kamiennik — Świerzawa · p 1% · 12 h".
//   useStore("sources")    the providers' lines of the data a section's view shows
//                          ({attribution, terms_notice}; ui/sources.js), which the welcome
//                          dialog lists (sectionValues).
// "status", "context" and "sources" belong to a section: inside a section
// (SectionContext) they are that section's; outside, the top bar reads the active
// section's.

import { createContext, useCallback, useContext, useEffect, useState } from "./html.js";

/** The section a component belongs to; the shell provides it around each section. */
export const SectionContext = createContext(null);

/** Keys of the shared values. */
export const STORE_KEYS = Object.freeze(["watershed", "reference", "status", "context", "sources"]);

/** Keys whose value belongs to a section. */
const PER_SECTION = new Set(["status", "context", "sources"]);

const shared = new Map([
  ["watershed", null],
  ["reference", null],
]);
const bySection = new Map([...PER_SECTION].map((key) => [key, new Map()]));
const listeners = new Map(STORE_KEYS.map((key) => [key, new Set()]));
let activeSection = null;

/**
 * Check a key of the store.
 *
 * @param {string} key one of STORE_KEYS
 */
function known(key) {
  if (!listeners.has(key)) throw new Error(`Unknown store key: ${key}`);
}

/**
 * Tell the listeners of a key that its value changed.
 *
 * @param {string} key the key
 */
function emit(key) {
  for (const listener of [...listeners.get(key)]) listener();
}

/**
 * Listen to changes of a key.
 *
 * @param {string} key one of STORE_KEYS
 * @param {() => void} listener called after each change
 * @returns {() => void} stops listening
 */
export function subscribe(key, listener) {
  known(key);
  listeners.get(key).add(listener);
  return () => listeners.get(key).delete(listener);
}

/**
 * Read a shared value.
 *
 * @param {string} key one of STORE_KEYS
 * @param {string|null} [section] for a key of a section: the section (default: the
 *   active one)
 * @returns {any} the value, null when unset
 */
export function getStore(key, section = null) {
  known(key);
  if (PER_SECTION.has(key)) {
    const value = bySection.get(key).get(section || activeSection);
    return value === undefined ? null : value;
  }
  return shared.get(key);
}

/**
 * The values a key of a section has in every section that set one.
 *
 * @param {string} key one of the keys that belong to a section
 * @returns {any[]} the values, in the order the sections set them first
 */
export function sectionValues(key) {
  known(key);
  if (!PER_SECTION.has(key)) throw new Error(`"${key}" does not belong to a section`);
  return [...bySection.get(key).values()];
}

/**
 * Set a shared value.
 *
 * @param {string} key one of STORE_KEYS
 * @param {any} value the new value (null clears it)
 * @param {string|null} [section] for a key of a section: the section it belongs to
 */
export function setStore(key, value, section = null) {
  known(key);
  if (PER_SECTION.has(key)) {
    if (!section) throw new Error(`"${key}" belongs to a section`);
    if (value === null || value === undefined) bySection.get(key).delete(section);
    else bySection.get(key).set(section, value);
  } else {
    shared.set(key, value);
  }
  emit(key);
}

/**
 * Make a section the active one: the top bar shows its status and context.
 *
 * @param {string|null} section the section's id
 */
export function setActiveSection(section) {
  if (section === activeSection) return;
  activeSection = section;
  for (const key of PER_SECTION) emit(key);
}

/**
 * The active section's id.
 *
 * @returns {string|null} the id
 */
export function getActiveSection() {
  return activeSection;
}

/**
 * A shared value and its setter, like useState.
 *
 * @param {string} key one of STORE_KEYS
 * @returns {[any, (next: any) => void]} the value and a setter (a value, or a function
 *   of the old value)
 */
export function useStore(key) {
  known(key);
  const section = useContext(SectionContext);
  const read = () => getStore(key, section);
  const [value, setValue] = useState(read);
  useEffect(() => {
    setValue(read);
    return subscribe(key, () => setValue(read));
  }, [key, section]);
  const set = useCallback(
    (next) => {
      const old = getStore(key, section);
      setStore(key, typeof next === "function" ? next(old) : next, section);
    },
    [key, section],
  );
  return [value, set];
}
