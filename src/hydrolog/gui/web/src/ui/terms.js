// The link to the regulamin of a public GUI (Nogat DEV-15.7): the regulamin the server
// fills (regulamin.html beside the page), linked as a small quiet link at the bottom of
// the rail (Rail), in the welcome dialog (sources.js WelcomeSources) and at the bottom of
// the guide's contents (instrukcja.js, from GET ../api/terms); the kit's app menu
// „Aplikacje” ends with it too. Only a public GUI has it: the session's `terms` is null on
// a local run, and then nothing is drawn. The link opens a new tab, as every link to the
// regulamin does (DEV-15.7): the page's session lives in its memory only, and leaving the
// page would end it.

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
 * The link „Regulamin”, opened in a new tab.
 *
 * @param {{terms: string, className?: string, text?: string}} props the regulamin's
 *   address, the link's class (none by default) and its text („Regulamin” by default)
 * @returns {object} the <a>
 */
export function TermsLink({ terms, className, text = shell.terms }) {
  return html`<a class=${className} href=${terms} target="_blank" rel="noopener">${text}</a>`;
}
