// „Zakres osi” under each chart of „Statystyka przepływów” (plan 2026-11-06, D8): the limits
// the person sets on the chart's axes (T of the Gumbel axis, Q, the density), typed as text
// and kept with the section's inputs. An empty limit is the automatic end, shown as its
// placeholder; a limit that cannot be drawn is marked and left out (`axisLimits`); „Auto”
// empties the chart's limits.

import { html } from "../../html.js";
import { t } from "../../labels/common.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { AXES, shortNumber } from "./state.js";

const ENDS = ["min", "max"];

/**
 * The message of a limit left out.
 *
 * @param {string} axis the axis ("t", "q", "f")
 * @param {string} end the end ("min", "max")
 * @param {string} reason why: "number", "floor" or "order"
 * @param {[number, number]} wanted the range the limits ask for
 * @returns {string} the message
 */
function message(axis, end, reason, wanted) {
  if (reason === "floor") return axis === "t" ? texts.axes.errors.floorT : texts.axes.errors.floor;
  if (reason === "order") {
    return end === "min"
      ? t(texts.axes.errors.orderMin, { other: shortNumber(wanted[1], 4) })
      : t(texts.axes.errors.orderMax, { other: shortNumber(wanted[0], 4) });
  }
  return texts.axes.errors.number;
}

/**
 * The control of a chart's axis ranges: a row per axis with its limits „od” and „do”.
 *
 * @param {{chart: string, typed: object|undefined, auto: object, limits: object,
 *   onAxis: (chart: string, axis: string|null, end?: string, text?: string) => void}} props
 *   the chart (a key of `AXES`), the limits typed for it by axis, its automatic ranges by
 *   axis, the result of `axisLimits` by axis, and the change handler (`axis` null: „Auto”)
 * @returns {object} the control
 */
export function AxisRange({ chart, typed, auto, limits, onAxis }) {
  const custom = AXES[chart].some((axis) => ENDS.some((end) => (typed?.[axis]?.[end] ?? "").trim() !== ""));
  return html`
    <details class="more axis-range" data-axes=${chart}>
      <summary>${texts.axes.title} <span class="meta">${custom ? texts.axes.custom : texts.axes.auto}</span></summary>
      ${AXES[chart].map((axis) => {
        const { errors, wanted } = limits[axis];
        const id = `st-axis-${chart}-${axis}`;
        return html`
          <div class="axis-row" data-axis=${axis} role="group" aria-labelledby=${`${id}-name`}>
            <span class="axis-name" id=${`${id}-name`}>${texts.axes.names[axis]} [${texts.axes.units[axis]}]</span>
            ${ENDS.map(
              (end, index) => html`
                <label class=${`axis-end${errors[end] ? " invalid" : ""}`}>
                  <span>${texts.axes[end]}</span>
                  <span class="ibox">
                    <input
                      type="text"
                      inputmode="decimal"
                      autocomplete="off"
                      spellcheck=${false}
                      value=${typed?.[axis]?.[end] ?? ""}
                      placeholder=${shortNumber(auto[axis][index], 4)}
                      aria-label=${t(texts.axes.limit, { axis: texts.axes.names[axis], end: texts.axes[end] })}
                      aria-invalid=${errors[end] ? "true" : "false"}
                      aria-describedby=${errors[end] ? `${id}-${end}-err` : undefined}
                      onInput=${(event) => onAxis(chart, axis, end, event.currentTarget.value)}
                    />
                  </span>
                </label>
              `,
            )}
            ${ENDS.filter((end) => errors[end]).map(
              (end) => html`<p class="err" id=${`${id}-${end}-err`}>${texts.axes[end]}: ${message(axis, end, errors[end], wanted)}</p>`,
            )}
          </div>
        `;
      })}
      <button class="btn ghost sm" type="button" title=${texts.axes.resetTitle} disabled=${!custom} onClick=${() => onAxis(chart, null)}>
        ${texts.axes.reset}
      </button>
    </details>
  `;
}
