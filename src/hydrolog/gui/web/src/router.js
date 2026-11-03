// The route lives in the hash, relative to the page, so it survives any prefix the GUI is
// mounted at: "#polecenia" opens a section, "#polecenia/uh/nash" a section with a path
// (here the command uh nash).

import { useEffect, useState } from "./html.js";

/** The sections in the order of the rail (GuiModule.sections, plan D4). */
export const SECTION_ORDER = Object.freeze([
  "hydrogram",
  "siec",
  "statystyka",
  "kalkulatory",
  "polecenia",
]);

/**
 * Read a route from a hash.
 *
 * @param {string} hash e.g. "#polecenia/uh/nash"
 * @returns {{section: string, path: string[]}} the section ("" when none) and the path
 */
export function parseHash(hash) {
  const [section = "", ...path] = String(hash || "")
    .replace(/^#/, "")
    .split("/")
    .map((part) => {
      try {
        return decodeURIComponent(part);
      } catch {
        return part;
      }
    });
  return { section, path: path.filter(Boolean) };
}

/**
 * Write a route as a hash.
 *
 * @param {string} section the section's id
 * @param {string[]} [path] further parts
 * @returns {string} e.g. "#polecenia/uh/nash"
 */
export function routeHash(section, path = []) {
  return `#${[section, ...path].map(encodeURIComponent).join("/")}`;
}

/**
 * Go to a route.
 *
 * @param {string} section the section's id
 * @param {string[]} [path] further parts
 * @param {{replace?: boolean}} [how] replace the history entry instead of adding one
 */
export function navigate(section, path = [], how = {}) {
  const hash = routeHash(section, path);
  if (window.location.hash === hash) return;
  if (how.replace) {
    window.history.replaceState(window.history.state, "", hash);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = hash;
  }
}

/**
 * The current route, updated on every hash change.
 *
 * @returns {{section: string, path: string[]}} the route
 */
export function useRoute() {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const update = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return route;
}
