// The providers' lines on screen (Nogat DEV-20.5, ECO-064): one strip per view, Nogat's
// kit element <nogat-sources> at the foot of a section's centre (ViewLayout's `sources`).
// It shows the short lines (IMGW-PIB's S and P, PMAXTP's PS and PP, ČHMÚ's short form)
// and „Źródła i warunki”, which opens the kit's dialog with every line, the links to the
// providers' terms and, on a public GUI, „Regulamin serwisu”; without lines it is not drawn.
// A view gives the union of the lines of the data it shows (its inputs' and its last
// run's, attribution.js mergeLines); the strip orders them as GET api/session's sets do
// and keeps them as the section's "sources" in the store, from which the welcome dialog
// lists the lines of the data on the page (WelcomeSources, the kit's fillSources). Files,
// exports, PNG, hand-offs and the print view keep the full lines (attribution.js).

import { hasLines, mergeLines, orderLines } from "../attribution.js";
import { useSession } from "../controls/file-field.js";
import { html, useEffect, useLayoutEffect, useRef, useState } from "../html.js";
import { sectionValues, subscribe, useStore } from "../store.js";
import { termsOf } from "./footer.js";
import { fillSources } from "../../nogat/nogat-sources.js";

/**
 * The lines in the order of the providers' sets, none while they are not known.
 *
 * @param {{attribution: string[], terms_notice: string[]}|null|undefined} lines the lines
 * @param {object|null} session hydrolog-gui-session/1
 * @returns {{attribution: string[], terms_notice: string[]}|null} the ordered lines, null
 *   without any
 */
function shown(lines, session) {
  return hasLines(lines) ? orderLines(lines, session) : null;
}

/**
 * The strip of a view: the kit's <nogat-sources> with the lines of the data it shows.
 *
 * @param {{lines: {attribution: string[], terms_notice: string[]}|null|undefined}} props
 *   the lines of the view's data (null or undefined: none, or not known yet)
 * @returns {object} the element
 */
export function Sources({ lines }) {
  const session = useSession();
  const element = useRef(null);
  const [, keep] = useStore("sources");
  const ordered = shown(lines, session);
  const key = JSON.stringify(ordered);
  useLayoutEffect(() => {
    element.current.attribution = ordered ? ordered.attribution : [];
    element.current.termsNotice = ordered ? ordered.terms_notice : [];
  }, [key]);
  useEffect(() => keep(ordered), [key]);
  useEffect(() => () => keep(null), []);
  const terms = termsOf(session);
  return html`<nogat-sources class="view-sources" ref=${element} terms=${terms || undefined}></nogat-sources>`;
}

/**
 * The lines of the data every section shows, in the order of the providers' sets.
 *
 * @param {object|null} session hydrolog-gui-session/1
 * @returns {{attribution: string[], terms_notice: string[]}|null} the lines, null without
 *   any
 */
function pageLines(session) {
  return shown(mergeLines(...sectionValues("sources")), session);
}

/**
 * The welcome dialog's part „Źródła danych”: every line of the data on the page, the terms
 * notice and „Regulamin serwisu” (the content of the strips' dialog); nothing while the
 * page shows no provider data, so a first visit keeps the welcome to its sentences.
 *
 * @returns {object|null} the part
 */
export function WelcomeSources() {
  const session = useSession();
  const box = useRef(null);
  const [lines, setLines] = useState(() => pageLines(session));
  useEffect(() => {
    const update = () => setLines(pageLines(session));
    update();
    return subscribe("sources", update);
  }, [session]);
  const terms = termsOf(session);
  const key = JSON.stringify([lines, terms]);
  useLayoutEffect(() => {
    if (lines && box.current) fillSources(box.current, { attribution: lines.attribution, termsNotice: lines.terms_notice, terms });
  }, [key]);
  return lines ? html`<div class="welcome-sources" ref=${box} data-welcome-sources=""></div>` : null;
}
