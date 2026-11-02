// The navigation rail (design/README.md): a 64 px dark column of the sections, icon over a
// short label; a 58 px bottom bar on phones.

import { html } from "../html.js";
import { shell } from "../labels/shell.js";
import { routeHash } from "../router.js";

/** Icons of the sections (24 × 24, stroked), from the approved mockup. */
export const SECTION_ICONS = {
  hydrogram: () => html`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v3M11 3v4.5M15 3v2" /><path d="M3 20h18" /><path d="M4 19c3.5 0 4.5-8.5 7.5-8.5S15 17 20 18" /></svg>`,
  siec: () => html`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 15h18" /><path d="M6 7l4 8M14 7l4 8" /><circle cx="6" cy="6.5" r="1.8" /><circle cx="14" cy="6.5" r="1.8" /><circle cx="10" cy="15" r="2.2" /><circle cx="18" cy="15" r="2.2" /></svg>`,
  statystyka: () => html`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4v16h16" /><path d="M6.5 17.5C11 16 15 12 19.5 5" /><circle cx="8" cy="15" r="1.1" /><circle cx="11" cy="14" r="1.1" /><circle cx="14.5" cy="10.5" r="1.1" /><circle cx="16.5" cy="9.5" r="1.1" /></svg>`,
  kalkulatory: () => html`<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2.5" /><path d="M8.5 7.5h7" /><path d="M8.5 12h.01M12 12h.01M15.5 12h.01M8.5 16h.01M12 16h.01M15.5 16h.01" /></svg>`,
  polecenia: () => html`<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2.5" /><path d="M7 9.5l3 2.5-3 2.5M12.5 15h4.5" /></svg>`,
};

/**
 * The rail of the sections.
 *
 * @param {{sections: string[], active: string|null}} props the ids of the sections shown,
 *   in the order of the rail, and the active one
 * @returns {object} the rail
 */
export function Rail({ sections, active }) {
  return html`
    <nav class="rail" aria-label=${shell.nav}>
      ${sections.map((id) => {
        const names = shell.sections[id] || { title: id, short: id };
        const on = id === active;
        return html`
          <a
            class=${`rail-item${on ? " active" : ""}`}
            href=${routeHash(id)}
            aria-current=${on ? "page" : undefined}
            title=${names.title}
            data-section=${id}
          >
            ${SECTION_ICONS[id] ? SECTION_ICONS[id]() : null}
            ${names.short}
          </a>
        `;
      })}
    </nav>
  `;
}
