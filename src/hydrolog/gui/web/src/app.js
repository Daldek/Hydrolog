// The shell of the GUI (design/README.md, plan D10): the top bar, the rail of the sections,
// the sections themselves and, standalone, the welcome dialog. Every registered section is
// loaded and mounted with the shell and stays mounted (its inputs and last result survive a
// change of section); only the active one is shown. Sections rely on that: Kalkulatory reads
// the watershed and the tc method Hydrogram zlewni sets when it mounts.

import { host } from "./host.js";
import { html, useEffect, useLayoutEffect, useState } from "./html.js";
import { t } from "./labels/common.js";
import { shell } from "./labels/shell.js";
import { routeHash, SECTION_ORDER, useRoute } from "./router.js";
import { SECTIONS } from "./sections/index.js";
import { SectionContext, setActiveSection } from "./store.js";
import { closeInfo, installInfo } from "./ui/info.js";
import { Rail } from "./ui/rail.js";
import { closeSheet, sheetOpen } from "./ui/sheet.js";
import { ToastHost } from "./ui/toast.js";
import { TopBar } from "./ui/top-bar.js";
import { Welcome } from "./ui/welcome.js";

/** The registered sections in the order of the rail. */
export const ORDERED = [
  ...SECTION_ORDER.map((id) => SECTIONS.find((entry) => entry.id === id)).filter(Boolean),
  ...SECTIONS.filter((entry) => !SECTION_ORDER.includes(entry.id)),
];

/**
 * One section: loaded and mounted with the shell, then kept; hidden unless active.
 *
 * @param {{entry: {id: string, load: () => Promise<{default: Function}>}, active: boolean,
 *   path: string[]}} props the registered section, whether it is shown, and the route's
 *   path when it is
 * @returns {object} the section
 */
function SectionHost({ entry, active, path }) {
  const [component, setComponent] = useState(null);
  const [failure, setFailure] = useState(null);
  useEffect(() => {
    let alive = true;
    entry
      .load()
      .then((module) => alive && setComponent(() => module.default))
      .catch((error) => alive && setFailure(String((error && error.message) || error)));
    return () => {
      alive = false;
    };
  }, [entry]);
  const names = shell.sections[entry.id] || { title: entry.id };
  const Section = component;
  let body;
  if (failure) {
    body = html`<p class="section-note err" role="alert">${t(shell.sectionFailed, { section: names.title, message: failure })}</p>`;
  } else if (Section) {
    body = html`<${Section} active=${active} path=${active ? path : []} />`;
  } else {
    body = html`<p class="section-note muted" role="status">${shell.sectionLoading}</p>`;
  }
  return html`
    <section class="section" data-section=${entry.id} aria-label=${names.title} hidden=${!active}>
      <${SectionContext.Provider} value=${entry.id}>${body}</${SectionContext.Provider}>
    </section>
  `;
}

/**
 * The GUI.
 *
 * @returns {object} the shell's parts, rendered into <div id="app" class="shell">
 */
export function App() {
  const route = useRoute();
  const ids = ORDERED.map((entry) => entry.id);
  const active = ids.includes(route.section) ? route.section : ids[0] || null;
  useLayoutEffect(() => setActiveSection(active), [active]);
  useEffect(() => {
    closeInfo();
    closeSheet();
  }, [active]);
  useEffect(() => {
    installInfo();
    const onKey = (event) => {
      // An open dialog (the welcome) takes Escape for itself
      if (document.querySelector("dialog[open]")) return;
      if (event.key === "Escape" && sheetOpen()) closeSheet();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);
  return html`
    ${host.embedded ? null : html`<${TopBar} section=${active} home=${routeHash(ids[0] || "")} />`}
    ${host.embedded ? null : html`<${Rail} sections=${ids} active=${active} />`}
    <main class="main" id="main">
      ${ORDERED.length
        ? ORDERED.map(
            (entry) => html`<${SectionHost} key=${entry.id} entry=${entry} active=${entry.id === active} path=${route.path} />`,
          )
        : html`<p class="section-note muted">${shell.noSections}</p>`}
    </main>
    <${ToastHost} />
    ${host.embedded ? null : html`<${Welcome} />`}
  `;
}
