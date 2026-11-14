// What the page knows of where it runs. Standalone only for now: "?nogat=1" (set before the
// first paint by theme-init.js as data-host="nogat") hides Hydrolog's own top bar and rail
// inside Nogat's shell. The postMessage handshake, the host's theme and the shell's hand-off
// come with the kit's embed.js, which replaces this module (plan D4).

import { useEffect, useState } from "./html.js";

/** localStorage key of the theme, shared by Nogat's pages on one origin. */
const THEME_KEY = "nogat-theme";

const root = document.documentElement;

/** Where the page runs: standalone, or embedded in Nogat's shell ("?nogat=1"). */
export const host = Object.freeze({
  embedded: root.dataset.host === "nogat",
});

/**
 * The stored theme choice.
 *
 * @returns {"auto"|"light"|"dark"} "auto" follows the system
 */
function storedTheme() {
  try {
    const value = window.localStorage.getItem(THEME_KEY);
    return value === "light" || value === "dark" ? value : "auto";
  } catch {
    return "auto";
  }
}

/**
 * Show a theme: data-theme on <html>, none for "auto".
 *
 * @param {"auto"|"light"|"dark"} choice the theme
 */
function showTheme(choice) {
  if (choice === "light" || choice === "dark") root.dataset.theme = choice;
  else delete root.dataset.theme;
}

/**
 * Choose a theme: shown at once and stored for every page of the origin.
 *
 * @param {"auto"|"light"|"dark"} choice the theme
 */
function setTheme(choice) {
  showTheme(choice);
  try {
    window.localStorage.setItem(THEME_KEY, choice);
  } catch {
    // Storage blocked: the choice lasts until the page closes.
  }
}

/**
 * The theme choice, following changes made in other pages of the origin.
 *
 * @returns {["auto"|"light"|"dark", (choice: string) => void]} the choice and its setter
 */
export function useTheme() {
  const [choice, setChoice] = useState(storedTheme);
  useEffect(() => {
    const onStorage = (event) => {
      if (event.key !== THEME_KEY && event.key !== null) return;
      const next = storedTheme();
      showTheme(next);
      setChoice(next);
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  return [
    choice,
    (next) => {
      setTheme(next);
      setChoice(next);
    },
  ];
}
