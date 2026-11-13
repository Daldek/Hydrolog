// The footer of a public GUI (Nogat DEV-15.7, DEV-15.8): the statement of what the service
// is, verbatim, and the link „Regulamin” to the regulamin the server fills
// (regulamin.html beside the page). Only a public GUI has it: the session's `terms` is null
// on a local run, and then nothing is drawn, so the layout stays as it was (the guide's
// pictures are taken that way). The link opens a new tab: the page's session lives in its
// memory only, and leaving the page would end it. The guide's page draws the same footer
// (instrukcja.js) from GET ../api/terms.

import { useSession } from "../controls/file-field.js";
import { html } from "../html.js";
import { shell } from "../labels/shell.js";

/**
 * The address of the regulamin a session document gives, or null on a GUI that is not
 * public (or before the document arrives).
 *
 * @param {object|null} doc hydrolog-gui-session/1 or the answer of GET api/terms
 * @returns {string|null} the address relative to the app's page
 */
export function termsOf(doc) {
  return doc && typeof doc.terms === "string" && doc.terms ? doc.terms : null;
}

/**
 * The footer with the statement and „Regulamin”.
 *
 * @param {{terms: string, newTab?: boolean}} props the regulamin's address, and whether
 *   the link opens a new tab (the app's page; the guide holds no session)
 * @returns {object} the <footer>
 */
export function TermsFooter({ terms, newTab = true }) {
  return html`
    <footer class="app-footer" aria-label=${shell.footer.label}>
      <p>
        <span>${shell.footer.statement}</span>${" "}
        <a href=${terms} target=${newTab ? "_blank" : undefined} rel=${newTab ? "noopener" : undefined}>${shell.footer.terms}</a>
      </p>
    </footer>
  `;
}

/**
 * The footer of the standalone shell: drawn only when the session names the regulamin.
 *
 * @returns {object|null} the footer, null on a GUI that is not public
 */
export function Footer() {
  const terms = termsOf(useSession());
  return terms ? html`<${TermsFooter} terms=${terms} />` : null;
}
