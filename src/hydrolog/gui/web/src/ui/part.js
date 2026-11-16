// A part of the panel Wyniki: a collapsible card (<details class="step">) with a title
// and a summary on the right. Shared by Hydrogram zlewni and Sieć.

import { html } from "../html.js";

/**
 * A part of the panel Wyniki: a <details> with a title and a summary on the right.
 *
 * @param {{id: string, title: string, meta?: string, open?: boolean, children: any}} props
 *   the part
 * @returns {object} the part
 */
export function Part({ id, title, meta, open = true, children }) {
  return html`
    <details class="step" open=${open} data-part=${id}>
      <summary>
        <span class="title">${title}</span><span class="meta">${meta || ""}</span>
        <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
      </summary>
      <div class="step-body">${children}</div>
    </details>
  `;
}
