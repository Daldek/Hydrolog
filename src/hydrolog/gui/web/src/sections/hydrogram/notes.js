// The applicability notes of „Hydrogram zlewni” (plan D16; the author's decision of
// 2026-11-04), a pure module without Preact: confirmations that the values a method or a
// model checks are inside Hydrolog's typical ranges (`typical_ranges` of the served catalog
// documents, registered with the (i) explanations, ui/info.js), listed before Hydrolog's own
// notices. A value outside a range is never worded here: Hydrolog's notice
// `outside_typical_range` (`outside_unverified_range` for a range to be verified) says so,
// in Wyniki and on its field; a confirmation marks a range to be verified „do weryfikacji”.
// Every number a note quotes comes from the inputs, the result or the served ranges.

import { exact, inputText } from "../../format.js";
import { t } from "../../labels/common.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { isRangeNotice, noticeValue } from "../../labels/notices.js";
import { infoRanges, infoText, listedRanges, rangeMark, rangeScale, rangeState, rangeUnit, rangeValue } from "../../ui/info.js";
import { usesTc } from "./state.js";

/**
 * A value with its unit, written as Hydrolog's notices write it: "37,22 km²".
 *
 * @param {number} value the value
 * @param {string} [unit] the unit
 * @returns {string} the text
 */
function shown(value, unit) {
  return `${noticeValue(value)}${unit ? `\u00a0${unit}` : ""}`;
}

/**
 * Whether Hydrolog's notices put a value of the methods outside its typical range.
 *
 * @param {object[]} notices the notices of the run
 * @param {Set<string>} methods the methods (`details.method`)
 * @param {string|null} [parameter] only this parameter (`details.parameter`)
 * @returns {boolean} true when one of them does
 */
function warned(notices, methods, parameter = null) {
  return (notices || []).some((notice) => {
    const details = (notice && notice.details) || {};
    return (
      isRangeNotice(notice) &&
      methods.has(details.method) &&
      (parameter === null || details.parameter === parameter)
    );
  });
}

/**
 * The confirmation of an explanation's ranges: „w zakresie stosowania” with the values it
 * checked, unless Hydrolog's notices put a value of its methods outside them.
 *
 * @param {string} id the explanation's id (its (i) opens from the note)
 * @param {string} name the method's short name, e.g. „Kirpich”
 * @param {Object<string, unknown>} values the current values by name
 * @param {object[]} notices Hydrolog's notices of the run
 * @returns {{level: string, text: string, from: string, info: string}|null} the note, null
 *   when Hydrolog warned about the method or no value lies inside a range
 */
function rangeNote(id, name, values, notices) {
  const found = infoRanges(id).filter((range) => !range.relative_to);
  if (!found.length || warned(notices, new Set(found.map((range) => range.method)))) return null;
  const checked = [];
  for (const { range, label } of listedRanges(infoText(id), found)) {
    const value = rangeValue(range, values);
    if (!value || rangeState(range, value.value, rangeScale(range, values)) !== "ok") continue;
    const mark = rangeMark(range);
    const words = { label, value: shown(value.value, rangeUnit(range)) };
    const item = mark ? t(texts.notes.markedItem, { ...words, mark }) : t(texts.notes.valueItem, words);
    if (!checked.includes(item)) checked.push(item);
  }
  if (!checked.length) return null;
  return { level: "ok", text: t(texts.notes.inRange, { title: name, values: checked.join(", ") }), from: texts.notes.rangeFrom, info: id };
}

/**
 * The confirmation of the time step against the unit hydrograph's time to peak (the range
 * of the model's `timestep_min`, relative to the result's `uh_time_to_peak_min`), unless
 * Hydrolog's notices put the step outside it.
 *
 * @param {string} model the unit hydrograph model
 * @param {object|null} result the result of `hydrograph generate`
 * @param {object[]} notices Hydrolog's notices of the run
 * @returns {{level: string, text: string, from: string, info: string}|null} the note
 */
function timestepNote(model, result, notices) {
  if (!result || typeof result.timestep_min !== "number") return null;
  const range = infoRanges("rain-timestep").find((found) => found.method === model && found.parameter === "timestep_min");
  if (!range || typeof range.maximum !== "number" || warned(notices, new Set([model]), "timestep_min")) return null;
  const scale = rangeScale(range, result);
  if (scale === null || rangeState(range, result.timestep_min, scale) !== "ok") return null;
  const words = { dt: inputText(result.timestep_min), share: exact(range.maximum), limit: noticeValue(range.maximum * scale) };
  return { level: "ok", text: t(texts.notes.timestepOk, words), from: texts.notes.rangeFrom, info: "rain-timestep" };
}

/**
 * The applicability notes of a result: tc not used by the model, or the confirmation of the
 * tc method's ranges; those of SCS-CN and of the unit hydrograph; the time step against the
 * unit hydrograph's time to peak.
 *
 * @param {{inputs: object, values: Object<string, unknown>, result: object|null,
 *   notices?: object[]}} run the inputs, the current values by name (the watershed's fields
 *   and the options), the result of `hydrograph generate` and Hydrolog's notices of the run
 * @returns {Array<{level: "ok"|"info", text: string, from: string, info?: string}>} the notes
 */
export function guiNotes({ inputs, values, result, notices = [] }) {
  const notes = [];
  const push = (note) => {
    if (note) notes.push(note);
  };
  const model = inputs.uh_model;
  const modelName = texts.uh.models[model] || model;
  if (!usesTc(model)) {
    notes.push({ level: "info", text: t(texts.notes.tcUnused, { model: modelName }), from: texts.notes.tcUnusedFrom });
  } else if (!inputs.tc_manual) {
    push(rangeNote(`tc-${inputs.tc_method}`, texts.tc.names[inputs.tc_method] || inputs.tc_method, values, notices));
  }
  push(rangeNote("losses-scs-cn", "SCS-CN", values, notices));
  push(rangeNote(`uh-${model}`, modelName, values, notices));
  push(timestepNote(model, result, notices));
  return notes;
}
