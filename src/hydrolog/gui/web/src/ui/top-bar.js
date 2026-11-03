// The top bar of the standalone GUI (design/README.md, plan D10): Hydrolog's mark and name,
// the breadcrumbs (section / context), the status badge, „Instrukcja” (the welcome dialog,
// which links the guide) and the theme switch Auto, Jasny, Ciemny. Inside Nogat's shell
// ("?nogat=1") the shell's own bar replaces it.

import { useTheme } from "../host.js";
import { html, useEffect } from "../html.js";
import { t } from "../labels/common.js";
import { shell } from "../labels/shell.js";
import { useStore } from "../store.js";
import { Seg } from "./seg.js";
import { StatusBadge } from "./status.js";
import { openWelcome } from "./welcome.js";

const ICONS = {
  auto: () => html`<svg class="icon-svg" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6.5" /><path d="M10 3.5v13a6.5 6.5 0 0 0 0-13z" fill="currentColor" /></svg>`,
  light: () => html`<svg class="icon-svg" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.5" /><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4" /></svg>`,
  dark: () => html`<svg class="icon-svg" viewBox="0 0 20 20" aria-hidden="true"><path d="M16 12.5A6.5 6.5 0 0 1 7.5 4a6.5 6.5 0 1 0 8.5 8.5z" /></svg>`,
};

/** The book of „Instrukcja”, as in Hydrograf's top bar. */
const GUIDE_ICON = () => html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H16v12H5.5A1.5 1.5 0 0 0 4 16.5z" /><path d="M4 16.5V4.5M7.5 6.5h5" /></svg>`;

/**
 * „Instrukcja”: a plain click opens the welcome dialog; a click with a modifier or the
 * middle button follows the link to the guide, as a link does.
 *
 * @param {MouseEvent} event the click
 */
function onGuide(event) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  if (openWelcome()) event.preventDefault();
}

/**
 * The theme switch: Auto (the system's), Jasny, Ciemny; stored as "nogat-theme".
 *
 * @returns {object} the switch
 */
export function ThemeSwitch() {
  const [choice, setChoice] = useTheme();
  const items = [
    { value: "auto", label: shell.theme.auto, title: shell.theme.autoTitle, icon: ICONS.auto() },
    { value: "light", label: shell.theme.light, title: shell.theme.light, icon: ICONS.light() },
    { value: "dark", label: shell.theme.dark, title: shell.theme.dark, icon: ICONS.dark() },
  ];
  return html`<${Seg} items=${items} value=${choice} onChange=${setChoice} label=${shell.theme.label} mode="pressed" />`;
}

/**
 * The top bar.
 *
 * @param {{section: string|null, home: string}} props the active section's id and the
 *   link of the mark (the first section)
 * @returns {object} the bar
 */
export function TopBar({ section, home }) {
  const [context] = useStore("context");
  const title = section && shell.sections[section] ? shell.sections[section].title : "";
  useEffect(() => {
    document.title = title
      ? context
        ? t(shell.pageTitleContext, { section: title, context })
        : t(shell.pageTitle, { section: title })
      : shell.brand;
  }, [title, context]);
  return html`
    <header class="topbar">
      <a class="brand" href=${home} aria-label=${shell.home}>
        <img src="nogat/marks/hydrolog.svg" alt="" width="24" height="24" />
        <span class="name">${shell.brand}</span>
      </a>
      <nav class="crumbs" aria-label=${shell.crumbs}>
        <span class="crumb-section">${title}</span>
        ${context ? html`<span class="sep" aria-hidden="true">/</span><strong class="crumb-context">${context}</strong>` : null}
      </nav>
      <${StatusBadge} />
      <div class="top-actions">
        <a class="btn ghost" href="instrukcja/" aria-label=${shell.guide.label} title=${shell.guide.title} aria-haspopup="dialog" onClick=${onGuide}>
          ${GUIDE_ICON()}<span class="label">${shell.guide.label}</span>
        </a>
        <${ThemeSwitch} />
      </div>
    </header>
  `;
}
