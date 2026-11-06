// The line swatch of „Statystyka przepływów” outside the charts (the filters of Dane, the
// distributions table): a short line drawn as the curves are, in the colour of its series
// class and the line style of its fit method's class (css/charts.css, `.sw-stroke`), the
// swatch of the charts' legends too (charts/draw.js, legend items of kind "stroke").

import { html } from "../../html.js";

/**
 * A line swatch.
 *
 * @param {{cls: string}} props its classes: a series class (the colour) and a fit method's
 *   class (the line style), either or both
 * @returns {object} the swatch
 */
export function Stroke({ cls }) {
  return html`<svg class=${`sw-stroke ${cls}`} viewBox="0 0 24 6" aria-hidden="true"><line x1="1" y1="3" x2="23" y2="3" /></svg>`;
}
