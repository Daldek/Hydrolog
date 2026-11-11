// Inputs kept in the browser between visits: one localStorage key per section,
// "hydrolog-gui/<section>/<version>", holding inputs only (no results). A missing key is a
// first visit, which starts empty (no section opens an example); „Wyczyść” removes the
// key. A section whose stored shape changed gets a new version in VERSIONS, so what the
// old shape stored is no longer read.

import { useCallback, useEffect, useRef, useState } from "./html.js";

/**
 * The versions of the stored shapes other than 1: Hydrogram zlewni's three steps of
 * 2026-11-04 left the five steps with the shipped example behind, the other sections left
 * their stored examples behind when every section started empty (2026-11-04), Statystyka's
 * filters of the combinations shown left one distribution and one fit method a run behind
 * (2026-11-06), and Sieć's network rainfall as Hydrogram's step 2 left its rainfall of the
 * schema's form behind (plan 2026-11-10-network-wizard, D3, D4).
 */
export const VERSIONS = Object.freeze({ hydrogram: 2, siec: 3, statystyka: 3, kalkulatory: 2, polecenia: 2 });

/**
 * The storage key of a section's inputs.
 *
 * @param {string} name section or part ("polecenia", "layout")
 * @param {number} [version] version of the stored shape (default: VERSIONS, else 1)
 * @returns {string} "hydrolog-gui/<name>/<version>"
 */
export function storageKey(name, version = Object.hasOwn(VERSIONS, name) ? VERSIONS[name] : 1) {
  return `hydrolog-gui/${name}/${version}`;
}

/**
 * Read stored inputs.
 *
 * @template T
 * @param {string} name section or part
 * @param {T} [fallback] what a first visit (or unreadable data) gives
 * @returns {T} the stored value or the fallback
 */
export function loadState(name, fallback = undefined) {
  try {
    const text = window.localStorage.getItem(storageKey(name));
    return text === null ? fallback : JSON.parse(text);
  } catch {
    return fallback;
  }
}

/**
 * Store inputs; a full or blocked storage is ignored (the page still works).
 *
 * @param {string} name section or part
 * @param {unknown} value JSON-compatible value
 */
export function saveState(name, value) {
  try {
    window.localStorage.setItem(storageKey(name), JSON.stringify(value));
  } catch {
    // Private mode or a full storage: the inputs live until the page closes.
  }
}

/**
 * Remove stored inputs.
 *
 * @param {string} name section or part
 */
export function clearState(name) {
  try {
    window.localStorage.removeItem(storageKey(name));
  } catch {
    // Nothing stored or storage blocked.
  }
}

/**
 * State of a component that is stored under the section's key after every change.
 *
 * @template T
 * @param {string} name section or part
 * @param {() => T} initial the value of a first visit
 * @returns {[T, (next: T | ((old: T) => T)) => void, () => void, boolean]} the value, its
 *   setter, a reset to the first-visit value (the key removed), and whether the value was
 *   read from storage
 */
export function usePersistentState(name, initial) {
  const fromStorage = useRef(null);
  const [value, setValue] = useState(() => {
    const stored = loadState(name);
    fromStorage.current = stored !== undefined;
    return stored !== undefined ? stored : initial();
  });
  const skipSave = useRef(false);
  useEffect(() => {
    if (skipSave.current) {
      skipSave.current = false;
      return;
    }
    saveState(name, value);
  }, [name, value]);
  const reset = useCallback(() => {
    clearState(name);
    skipSave.current = true;
    setValue(initial());
  }, [name, initial]);
  return [value, setValue, reset, fromStorage.current];
}
