// Explanations (i) (plan D16): a registry of Polish texts and the popover that shows one.
// A pure module without Preact (the kit's info.js takes it over later): it draws the
// popover with the DOM and listens, once, to clicks on any element with data-info="<id>"
// (its current values in data-info-values, a JSON object).
//
// An explanation, as the files of labels/info/*.js export them (keys are the ids), in the
// order and shape of Nogat DEV-15.14 (a definition, the formula with its symbols and units,
// how to read the value, the sources; at most about 400 characters without the formula and
// the sources, a longer explanation in the guide's chapter „Metody obliczeń”):
//   {
//     title: "Kirpich (1940): czas koncentracji",
//     intro: "<p>…</p>",                      HTML: the definition, one or two sentences
//     formula: "<math display=\"block\">…</math>",          MathML, one or more
//     vars: [{symbol: "<math>…</math>", text: "czas koncentracji", unit: "min"}],
//     symbols: {area_km2: "A", slope_m_per_m: "S"},  the symbol of a range's parameter
//     note: "<p>…</p>",                       HTML, optional: how to read the value
//     guide: "metoda-tc-kirpich",             optional: the id of its part of the guide
//     sources: "Kirpich 1940 (za Mota i Kobiyama 2015); Fang i in. 2005",
//   }
// The fragments are trusted repository files (a contract test refuses scripts, inline
// styles, event attributes and remote URLs in them); they are set as HTML.
//
// The ranges an explanation checks are Hydrolog's, never the GUI's (the author's decision
// of 2026-11-04): the `typical_ranges` of a command's catalog document (`commands schema
// --command X`), which a section registers under the explanation's id when the document
// arrives (registerServed). A range is {method, parameter, inputs, result?, minimum,
// maximum, unit, relative_to?, notice, verified, source, i18n: {pl: {source}}}: its value
// is the first of `inputs` the values hold, else `result`; with `relative_to` the bounds
// are shares of that quantity. A range with `verified` false has no published source yet:
// its row is marked „do weryfikacji” (data-verified="false").

import { exact } from "../format.js";
import { t } from "../labels/common.js";
import { noticeValue } from "../labels/notices.js";
import { shell } from "../labels/shell.js";
import { unitLabel } from "../labels/units.js";

const registry = new Map();
const ranges = new Map();
let popover = null;
let anchor = null;
let installed = false;

/**
 * Register explanations.
 *
 * @param {Object<string, object>} entries explanations by id
 */
export function registerInfo(entries) {
  for (const [id, entry] of Object.entries(entries)) registry.set(id, entry);
}

/**
 * The explanation of an id.
 *
 * @param {string} id the id
 * @returns {object|null} the explanation
 */
export function infoText(id) {
  return registry.get(id) || null;
}

/**
 * The key of a range: its method and parameter, "kirpich.slope_m_per_m".
 *
 * @param {{method: string, parameter: string}} range the range
 * @returns {string} the key
 */
export function rangeKey(range) {
  return `${range.method}.${range.parameter}`;
}

/**
 * Register the ranges an explanation checks, as Hydrolog serves them; a range of the same
 * method and parameter replaces the one registered before.
 *
 * @param {string} id the explanation's id
 * @param {object[]} found ranges of `typical_ranges`
 */
export function registerRanges(id, found) {
  const kept = new Map(infoRanges(id).map((range) => [rangeKey(range), range]));
  for (const range of found) kept.set(rangeKey(range), range);
  ranges.set(id, [...kept.values()]);
}

/**
 * The ranges registered for an explanation.
 *
 * @param {string} id the explanation's id
 * @returns {object[]} the ranges, none before a section registered its documents
 */
export function infoRanges(id) {
  return ranges.get(id) || [];
}

/**
 * The typical ranges of a command's catalog document.
 *
 * @param {object|null} doc hydrolog-commands/1 of one command (`api.command`)
 * @returns {object[]} its `typical_ranges`, none when it has none
 */
function servedRanges(doc) {
  const entry = doc && Array.isArray(doc.commands) ? doc.commands[0] : null;
  return entry && Array.isArray(entry.typical_ranges) ? entry.typical_ranges : [];
}

/**
 * Register the typical ranges of a command's catalog document for the explanations that
 * check them.
 *
 * @param {object|null} doc hydrolog-commands/1 of one command
 * @param {(range: object) => string|null} place the id of the explanation of a range, null
 *   for a range no explanation shows
 */
export function registerServed(doc, place) {
  const byId = new Map();
  for (const range of servedRanges(doc)) {
    const id = place(range);
    if (!id) continue;
    if (!byId.has(id)) byId.set(id, []);
    byId.get(id).push(range);
  }
  for (const [id, found] of byId) registerRanges(id, found);
}

/**
 * The value a range checks: the first of its inputs the values hold, else its result field.
 *
 * @param {{inputs?: string[], result?: string}} range the range
 * @param {Object<string, unknown>} [values] the current values by name
 * @returns {{field: string, value: number}|null} the field and its value, null without one
 */
export function rangeValue(range, values = {}) {
  const names = [...(range.inputs || []), ...(range.result ? [range.result] : [])];
  for (const name of names) {
    const value = values[name];
    if (typeof value === "number" && Number.isFinite(value)) return { field: name, value };
  }
  return null;
}

/**
 * The quantity the bounds of a range are shares of (`relative_to`).
 *
 * @param {{relative_to?: string}} range the range
 * @param {Object<string, unknown>} [values] the current values by name
 * @returns {number|null} 1 for bounds in the parameter's unit, the quantity, or null when
 *   the values do not hold it
 */
export function rangeScale(range, values = {}) {
  if (!range.relative_to) return 1;
  const value = values[range.relative_to];
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
}

/**
 * A range against a value, both bounds included.
 *
 * @param {{minimum?: number|null, maximum?: number|null}} range the range
 * @param {unknown} value the value
 * @param {number|null} [scale] the quantity of `relative_to` (rangeScale)
 * @returns {"ok"|"warn"|null} inside, outside, or null without a number or a quantity
 */
export function rangeState(range, value, scale = 1) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  if (typeof scale !== "number" || !Number.isFinite(scale)) return null;
  if (typeof range.minimum === "number" && value < range.minimum * scale) return "warn";
  if (typeof range.maximum === "number" && value > range.maximum * scale) return "warn";
  return "ok";
}

/**
 * The unit of a range as shown: "km²", "" for a dimensionless one.
 *
 * @param {{unit?: string}} range the range
 * @returns {string} the unit
 */
export function rangeUnit(range) {
  return !range.unit || range.unit === "-" ? "" : unitLabel(range.unit);
}

/**
 * The words of a range: „od 0,03 do 0,1 m/m”, „najwyżej 52 km²” (a range from 0), „co
 * najmniej 30 lat”; with `relative_to` the bounds are shares of its symbol, „najwyżej
 * 0,25·tp”, followed by their value when the quantity is known, „najwyżej 0,25·tp = 47,5
 * min”.
 *
 * @param {{minimum?: number|null, maximum?: number|null, unit?: string,
 *   relative_to?: string}} range the range
 * @param {{scale?: number|null, symbol?: string}} [how] the quantity of `relative_to`
 *   (rangeScale) and its symbol
 * @returns {string} the text, "" for a range without bounds
 */
export function rangeText(range, how = {}) {
  const low = typeof range.minimum === "number" && range.minimum !== 0 ? range.minimum : null;
  const high = typeof range.maximum === "number" ? range.maximum : null;
  const words = (format) => {
    if (low !== null && high !== null) return t(shell.info.between, { min: format(low), max: format(high) });
    if (low !== null) return t(shell.info.atLeast, { min: format(low) });
    if (high !== null) return t(shell.info.atMost, { max: format(high) });
    return "";
  };
  const unit = rangeUnit(range);
  const withUnit = (text) => (text && unit ? `${text} ${unit}` : text);
  if (!range.relative_to) return withUnit(words(exact));
  const symbol = how.symbol || range.relative_to;
  const shares = words((share) => `${exact(share)}·${symbol}`);
  const scale = how.scale;
  if (!shares || typeof scale !== "number" || !Number.isFinite(scale)) return shares;
  const bound = (share) => noticeValue(share * scale);
  if (low !== null && high !== null) return `${shares} (${withUnit(words(bound))})`;
  return `${shares} = ${withUnit(bound(high !== null ? high : low))}`;
}

/**
 * The mark of a range to be verified (`verified` false in the served `typical_ranges`: no
 * published source yet, Hydrolog's notice `outside_unverified_range`).
 *
 * @param {{verified?: boolean}} range the range
 * @returns {string} „do weryfikacji”, "" for a verified range
 */
export function rangeMark(range) {
  return range && range.verified === false ? shell.info.unverified : "";
}

/**
 * The symbol of a range's parameter (or of any quantity) in an explanation.
 *
 * @param {object|null} entry the explanation
 * @param {string} name the parameter
 * @returns {string} its symbol, else the name
 */
export function symbolOf(entry, name) {
  const symbols = (entry && entry.symbols) || {};
  return Object.hasOwn(symbols, name) ? symbols[name] : name;
}

/**
 * The source of a range, in Polish when Hydrolog gives it.
 *
 * @param {{source?: string, i18n?: object}} range the range
 * @returns {string} the source
 */
export function rangeSource(range) {
  const polish = range.i18n && range.i18n.pl && range.i18n.pl.source;
  return polish || range.source || "";
}

/**
 * Escape a text for HTML.
 *
 * @param {unknown} text the text
 * @returns {string} the escaped text
 */
function escape(text) {
  return String(text ?? "").replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}

/**
 * The ranges an explanation lists: each once (the four unit hydrograph models serve the same
 * range of the time step), with its label; a parameter listed twice names its method.
 *
 * @param {object} entry the explanation
 * @param {object[]} found the registered ranges
 * @returns {Array<{range: object, label: string}>} the ranges with their labels
 */
export function listedRanges(entry, found) {
  const seen = new Set();
  const listed = [];
  for (const range of found) {
    const same = JSON.stringify([range.parameter, range.minimum, range.maximum, range.unit, range.relative_to || null, rangeSource(range)]);
    if (seen.has(same)) continue;
    seen.add(same);
    listed.push(range);
  }
  const count = (parameter) => listed.filter((range) => range.parameter === parameter).length;
  return listed.map((range) => {
    const label = symbolOf(entry, range.parameter);
    return { range, label: count(range.parameter) > 1 ? `${label} (${range.method})` : label };
  });
}

/**
 * The HTML of an explanation's body.
 *
 * @param {object} entry the explanation
 * @param {Object<string, unknown>} [values] the current values by name
 * @param {object[]} [found] its ranges, as Hydrolog serves them (infoRanges)
 * @returns {string} the HTML
 */
export function infoBody(entry, values = {}, found = []) {
  const parts = [];
  if (entry.intro) parts.push(entry.intro);
  if (entry.formula) parts.push(`<div class="formula">${entry.formula}</div>`);
  if (Array.isArray(entry.vars) && entry.vars.length) {
    const rows = entry.vars
      .map((item) => `<tr><th>${item.symbol}</th><td>${item.text}</td><td class="u">${escape(item.unit || "–")}</td></tr>`)
      .join("");
    parts.push(`<table class="vars"><tbody>${rows}</tbody></table>`);
  }
  const listed = listedRanges(entry, found);
  if (listed.length) {
    const items = listed
      .map(({ range, label }) => {
        const checked = rangeValue(range, values);
        const scale = rangeScale(range, values);
        const state = checked ? rangeState(range, checked.value, scale) : null;
        const unit = rangeUnit(range);
        const bounds = escape(rangeText(range, { scale, symbol: symbolOf(entry, range.relative_to) }));
        const words = state
          ? t(shell.info.rangeValue, { label: escape(label), value: escape(`${noticeValue(checked.value)}${unit ? ` ${unit}` : ""}`), range: bounds })
          : t(shell.info.range, { label: escape(label), range: bounds });
        const badge = state
          ? `<span class="badge ${state}">${state === "ok" ? shell.info.inRange : shell.info.outOfRange}</span>`
          : `<span class="badge info">${shell.info.noValue}</span>`;
        const source = rangeSource(range) ? ` (${escape(rangeSource(range))})` : "";
        const field = state ? ` data-field="${escape(checked.field)}"` : "";
        const mark = rangeMark(range);
        const verified = mark ? ' data-verified="false"' : "";
        const marked = mark ? `<span class="badge warn">${mark}</span>` : "";
        return `<li class="${state || "none"}" data-range="${escape(rangeKey(range))}"${field}${verified}>${badge}${marked}<span>${words}${source}</span></li>`;
      })
      .join("");
    parts.push(`<h3>${shell.info.ranges}</h3><ul class="range-list">${items}</ul>`);
  }
  if (entry.note) parts.push(`<div class="note">${entry.note}</div>`);
  if (entry.guide) {
    const href = `instrukcja/#${encodeURIComponent(entry.guide)}`;
    parts.push(`<p class="guide-link"><a href="${href}" target="_blank" rel="noopener">${shell.info.guide}</a></p>`);
  }
  if (entry.sources) parts.push(`<p class="sources">${shell.info.sources}: ${entry.sources}</p>`);
  return parts.join("");
}

/**
 * Place the popover beside the panel that holds the anchor, over the centre, so the form
 * stays visible (on a phone the CSS puts it above the bottom bar).
 *
 * @param {HTMLElement} element the popover
 * @param {HTMLElement} target the anchor
 */
function place(element, target) {
  const box = target.getBoundingClientRect();
  const width = element.offsetWidth;
  const height = element.offsetHeight;
  const holder = target.closest(".view-panel");
  const area = holder ? holder.getBoundingClientRect() : box;
  const onRight = holder && holder.classList.contains("right");
  let left = onRight ? area.left - width - 12 : area.right + 12;
  if (left + width > window.innerWidth - 12) left = box.left - width - 12;
  if (left < 12) left = Math.max(12, (window.innerWidth - width) / 2);
  const top = Math.min(Math.max(12, box.top - 48), window.innerHeight - height - 12);
  element.style.left = `${Math.max(12, left)}px`;
  element.style.top = `${Math.max(12, top)}px`;
}

/**
 * Close the open explanation.
 *
 * @param {{restoreFocus?: boolean}} [how] give the focus back to its button
 */
export function closeInfo(how = {}) {
  if (!popover || popover.hidden) return;
  popover.hidden = true;
  const back = anchor;
  anchor = null;
  if (back) {
    back.setAttribute("aria-expanded", "false");
    if (how.restoreFocus && back.isConnected) back.focus();
  }
}

/**
 * Whether an explanation is open.
 *
 * @returns {boolean} true while the popover is shown
 */
function infoOpen() {
  return Boolean(popover && !popover.hidden);
}

/**
 * Open the explanation of an id beside its button; the same button closes it again.
 *
 * @param {string} id the explanation's id
 * @param {HTMLElement} target the button
 * @param {Object<string, unknown>} [values] the current values by option name
 */
function openInfo(id, target, values = {}) {
  if (anchor === target && infoOpen()) {
    closeInfo();
    return;
  }
  closeInfo();
  if (!popover) {
    popover = document.createElement("section");
    popover.className = "info-pop";
    popover.setAttribute("role", "dialog");
    popover.setAttribute("aria-modal", "false");
    popover.setAttribute("aria-labelledby", "info-pop-title");
    popover.hidden = true;
    document.body.append(popover);
  }
  const entry = infoText(id);
  const title = entry ? entry.title : t(shell.info.missing, { id });
  popover.innerHTML =
    `<div class="ip-head"><h2 id="info-pop-title">${escape(title)}</h2>` +
    `<button class="btn ghost sm icon" type="button" data-info-close aria-label="${escape(shell.info.close)}">` +
    '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15"/></svg></button></div>' +
    `<div class="ip-body">${entry ? infoBody(entry, values, infoRanges(id)) : ""}</div>`;
  popover.dataset.infoId = id;
  popover.hidden = false;
  place(popover, target);
  anchor = target;
  target.setAttribute("aria-expanded", "true");
  popover.querySelector("[data-info-close]").focus({ preventScroll: true });
}

/**
 * Listen, once, to the buttons of explanations: a click on [data-info] opens or closes
 * its explanation, a click outside or Escape closes it, and so does a resized window.
 */
export function installInfo() {
  if (installed) return;
  installed = true;
  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;
    if (target.closest("[data-info-close]")) {
      closeInfo({ restoreFocus: true });
      return;
    }
    const button = target.closest("[data-info]");
    if (button) {
      event.preventDefault();
      let values = {};
      try {
        values = JSON.parse(button.dataset.infoValues || "{}");
      } catch {
        values = {};
      }
      openInfo(button.dataset.info, button, values);
      return;
    }
    if (popover && !popover.hidden && !popover.contains(target)) closeInfo();
  });
  document.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape" && infoOpen()) {
        event.stopPropagation();
        closeInfo({ restoreFocus: true });
      }
    },
    true,
  );
  window.addEventListener("resize", () => closeInfo());
}
