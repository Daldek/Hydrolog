// The hint of a section that holds no data yet (every section starts empty): what to enter,
// in Polish, and a link to the section's worked example in the guide (the values to enter
// and the result they give). The link opens the guide in a new tab, as „Otwórz
// instrukcję” of the welcome dialog does.

import { richText } from "../controls/field.js";
import { html } from "../html.js";
import { common } from "../labels/common.js";

/**
 * The hint of an empty section.
 *
 * @param {{text?: string, anchor: string, name: string}} props what to enter (rich text;
 *   none when the place says it already), the id of the example in the guide
 *   ("przyklad-siec") and the name of the hint for tests
 * @returns {object} the hint
 */
export function EmptyHint({ text, anchor, name }) {
  return html`
    <p class="note empty-hint" data-empty=${name}>
      ${text ? html`${richText(text)}${" "}` : null}<a href=${`instrukcja/#${anchor}`} target="_blank" rel="noopener" title=${common.guide.exampleTitle}>${common.guide.example}</a>
    </p>
  `;
}
