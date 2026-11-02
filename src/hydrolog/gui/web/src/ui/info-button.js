// The (i) button of an explanation: html`<${InfoButton} id="kirpich" values=${{channel_length_km: 14.78}} />`.
// ui/info.js opens the popover on its click; `values` mark the ranges ok or warn.

import { html } from "../html.js";
import { t } from "../labels/common.js";
import { shell } from "../labels/shell.js";
import { infoText } from "./info.js";

/**
 * The (i) button of a registered explanation.
 *
 * @param {{id: string, label?: string, values?: Object<string, unknown>}} props the
 *   explanation's id, the button's accessible name (default: the explanation's title) and
 *   the current values of the options its ranges name
 * @returns {object} the button
 */
export function InfoButton({ id, label, values }) {
  const entry = infoText(id);
  const name = t(shell.info.open, { title: label || (entry ? entry.title : id) });
  return html`
    <button
      class="info-btn"
      type="button"
      data-info=${id}
      data-info-values=${values ? JSON.stringify(values) : undefined}
      aria-label=${name}
      aria-expanded="false"
      aria-haspopup="dialog"
      title=${name}
    >
      i
    </button>
  `;
}
