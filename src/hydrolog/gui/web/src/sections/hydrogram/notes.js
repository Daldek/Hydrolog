// The applicability notes of „Hydrogram zlewni” (plan D16), a pure module without Preact:
// the ranges of the (i) explanations (labels/info/*.js, data) checked against the current
// values, as the mockup lists them before Hydrolog's own notices. They compare inputs with
// ranges; every hydrological value they quote comes from the inputs or the result.

import { inputText, num } from "../../format.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { lossesInfo } from "../../labels/info/losses.js";
import { tcInfo } from "../../labels/info/tc.js";
import { uhInfo } from "../../labels/info/uh.js";
import { rangeState, rangeText } from "../../ui/info.js";
import { usesTc } from "./state.js";

/** The share of the unit hydrograph's time to peak a time step should not exceed. */
export const TIMESTEP_SHARE = 0.25;

/**
 * A value with its unit, as a person reads it: "37,22 km²".
 *
 * @param {number} value the value
 * @param {string} [unit] the unit
 * @returns {string} the text
 */
function shown(value, unit) {
  return `${inputText(value)}${unit ? `\u00a0${unit}` : ""}`;
}

/**
 * The note of an explanation's ranges against the current values: „poza zakresem” for
 * every range a value leaves, else „w zakresie stosowania” for the values it checked.
 *
 * @param {string} id the explanation's id (its (i) opens from the note)
 * @param {object|undefined} entry the explanation
 * @param {string} name the method's short name, e.g. „Kirpich”
 * @param {Object<string, unknown>} values the current values by option name
 * @returns {{level: string, text: string, from: string, info: string}|null} the note, null
 *   when no range has a value to check
 */
export function rangeNote(id, entry, name, values) {
  if (!entry || !Array.isArray(entry.ranges)) return null;
  const outside = [];
  const inside = [];
  for (const range of entry.ranges) {
    const state = rangeState(range, values[range.option]);
    if (state === "warn") outside.push(range);
    else if (state === "ok") inside.push(range);
  }
  const label = (range) => range.label || range.option;
  if (outside.length) {
    const items = outside.map((range) =>
      t(range.source ? texts.notes.outItem : texts.notes.outItemPlain, {
        label: label(range),
        value: shown(values[range.option], range.unit),
        range: rangeText(range),
        source: range.source || "",
      }),
    );
    return { level: "warn", text: t(texts.notes.outOfRange, { title: name, items: items.join("; ") }), from: texts.notes.rangeFrom, info: id };
  }
  if (!inside.length) return null;
  const checked = [];
  for (const range of inside) {
    const item = t(texts.notes.valueItem, { label: label(range), value: shown(values[range.option], range.unit) });
    if (!checked.includes(item)) checked.push(item);
  }
  return { level: "ok", text: t(texts.notes.inRange, { title: name, values: checked.join(", ") }), from: texts.notes.rangeFrom, info: id };
}

/**
 * The applicability notes of a result: tc not used by the model, or the ranges of the tc
 * method; the ranges of SCS-CN and of the unit hydrograph; the time step against the
 * unit hydrograph's time to peak.
 *
 * @param {{inputs: object, values: Object<string, unknown>, result: object|null}} run the
 *   inputs, the current values by option name (the watershed's fields and the options) and
 *   the result of `hydrograph generate`
 * @returns {Array<{level: "ok"|"warn"|"info", text: string, from: string, info?: string}>}
 *   the notes
 */
export function guiNotes({ inputs, values, result }) {
  const notes = [];
  const push = (note) => {
    if (note) notes.push(note);
  };
  const model = inputs.uh_model;
  const modelName = texts.uh.models[model] || model;
  if (!usesTc(model)) {
    notes.push({ level: "info", text: t(texts.notes.tcUnused, { model: modelName }), from: texts.notes.tcUnusedFrom });
  } else if (!inputs.tc_manual) {
    const id = `tc-${inputs.tc_method}`;
    push(rangeNote(id, tcInfo[id], texts.tc.names[inputs.tc_method] || inputs.tc_method, values));
  }
  push(rangeNote("losses-scs-cn", lossesInfo["losses-scs-cn"], "SCS-CN", values));
  push(rangeNote(`uh-${model}`, uhInfo[`uh-${model}`], modelName, values));
  const tp = result ? result.uh_time_to_peak_min : null;
  const step = result ? result.timestep_min : null;
  if (typeof tp === "number" && typeof step === "number" && tp > 0) {
    const limit = TIMESTEP_SHARE * tp;
    const words = { dt: inputText(step), limit: num(limit, 1) };
    notes.push(
      step <= limit
        ? { level: "ok", text: t(texts.notes.timestepOk, words), from: texts.notes.timestepFrom, info: "rain-timestep" }
        : { level: "warn", text: t(texts.notes.timestepWarn, words), from: texts.notes.timestepFrom, info: "rain-timestep" },
    );
  }
  return notes;
}
