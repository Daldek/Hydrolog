// Inputs kept in the browser between visits: one localStorage key per section,
// "hydrolog-gui/<section>/1", holding inputs only (no results). A missing key is a first
// visit, which starts empty (no section opens an example); „Wyczyść” removes the key.
// Every stored shape is version 1 until the first release (Nogat REL-1.4).

import { useCallback, useEffect, useRef, useState } from "./html.js";

/**
 * The highest version of a section's stored shape before Nogat REL-1.4 set every id to 1:
 * its key holds the current shape and moves to version 1; a lower key above 1 held an
 * older shape (Hydrogram zlewni's five steps with the shipped example, the stored
 * examples of 2026-11-04, Statystyka's one distribution and fit method a run, Sieć's
 * rainfall of the schema's form), and so did the key of version 1 beside it, so neither is
 * read.
 */
const BEFORE = Object.freeze({ hydrogram: 2, siec: 3, statystyka: 3, kalkulatory: 2, polecenia: 2 });

/**
 * The storage key of a section's inputs.
 *
 * @param {string} name section or part ("polecenia", "layout")
 * @returns {string} "hydrolog-gui/<name>/1"
 */
export function storageKey(name) {
  return `hydrolog-gui/${name}/1`;
}

/**
 * Move a section's inputs stored before Nogat REL-1.4 to its key of version 1; older
 * shapes are removed. Storage errors reach the caller.
 *
 * @param {string} name section or part
 */
function moveEarlier(name) {
  if (!Object.hasOwn(BEFORE, name)) return;
  const storage = window.localStorage;
  const earlier = [];
  for (let version = 2; version <= BEFORE[name]; version += 1) earlier.push(`hydrolog-gui/${name}/${version}`);
  if (earlier.every((key) => storage.getItem(key) === null)) return;
  const current = storage.getItem(earlier[earlier.length - 1]);
  if (current === null) storage.removeItem(storageKey(name));
  else storage.setItem(storageKey(name), current);
  for (const key of earlier) storage.removeItem(key);
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
    moveEarlier(name);
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
    moveEarlier(name);
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
    moveEarlier(name);
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
