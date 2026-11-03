// Explanations (i) (plan D16): a registry of Polish texts and the popover that shows one.
// A pure module without Preact (the kit's info.js takes it over later): it draws the
// popover with the DOM and listens, once, to clicks on any element with data-info="<id>"
// (its current values in data-info-values, a JSON object).
//
// An explanation, as the files of labels/info/*.js export them (keys are the ids):
//   {
//     title: "Kirpich (1940): czas koncentracji",
//     intro: "<p>…</p>",                      HTML: what it is, which command and option
//     formula: "<math display=\"block\">…</math>",          MathML, one or more
//     vars: [{symbol: "<math>…</math>", text: "czas koncentracji", unit: "min"}],
//     ranges: [{option: "channel_length_km", label: "L", unit: "km", min: 0, max: 80,
//               source: "próg ostrzeżenia Hydrologu"}],   checked against the values
//     note: "<p>…</p>",                       HTML, optional
//     sources: "Kirpich 1940; Hydrolog, <code>docs/COMPUTATION_PATHS.md</code> 3.1",
//   }
// The fragments are trusted repository files (a contract test refuses scripts, inline
// styles, event attributes and remote URLs in them); they are set as HTML.

import { inputText } from "../format.js";
import { t } from "../labels/common.js";
import { shell } from "../labels/shell.js";

const registry = new Map();
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
 * A range of applicability against the current value.
 *
 * @param {{min?: number, max?: number}} range the range
 * @param {unknown} value the value of its option
 * @returns {"ok"|"warn"|null} inside, outside, or null without a number
 */
export function rangeState(range, value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  if (typeof range.min === "number" && value < range.min) return "warn";
  if (typeof range.max === "number" && value > range.max) return "warn";
  return "ok";
}

/**
 * The words of a range: „od 0,002 do 0,15 m/m”.
 *
 * @param {{min?: number, max?: number, unit?: string}} range the range
 * @returns {string} the text
 */
export function rangeText(range) {
  const unit = range.unit ? ` ${range.unit}` : "";
  const min = typeof range.min === "number" ? inputText(range.min) : null;
  const max = typeof range.max === "number" ? inputText(range.max) : null;
  if (min !== null && max !== null) return `${t(shell.info.between, { min, max })}${unit}`;
  if (min !== null) return `${t(shell.info.atLeast, { min })}${unit}`;
  if (max !== null) return `${t(shell.info.atMost, { max })}${unit}`;
  return "";
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
 * The HTML of an explanation's body.
 *
 * @param {object} entry the explanation
 * @param {Object<string, unknown>} [values] the current values by option name
 * @returns {string} the HTML
 */
export function infoBody(entry, values = {}) {
  const parts = [];
  if (entry.intro) parts.push(entry.intro);
  if (entry.formula) parts.push(`<div class="formula">${entry.formula}</div>`);
  if (Array.isArray(entry.vars) && entry.vars.length) {
    const rows = entry.vars
      .map((item) => `<tr><th>${item.symbol}</th><td>${item.text}</td><td class="u">${escape(item.unit || "–")}</td></tr>`)
      .join("");
    parts.push(`<table class="vars"><tbody>${rows}</tbody></table>`);
  }
  if (Array.isArray(entry.ranges) && entry.ranges.length) {
    const items = entry.ranges
      .map((range) => {
        const value = values[range.option];
        const state = rangeState(range, value);
        const label = escape(range.label || range.option);
        const words = state
          ? t(shell.info.rangeValue, { label, value: escape(`${inputText(value)}${range.unit ? ` ${range.unit}` : ""}`), range: escape(rangeText(range)) })
          : t(shell.info.range, { label, range: escape(rangeText(range)) });
        const badge = state
          ? `<span class="badge ${state}">${state === "ok" ? shell.info.inRange : shell.info.outOfRange}</span>`
          : `<span class="badge info">${shell.info.noValue}</span>`;
        const source = range.source ? ` (${escape(range.source)})` : "";
        return `<li class="${state || "none"}" data-range="${escape(range.option)}">${badge}<span>${words}${source}</span></li>`;
      })
      .join("");
    parts.push(`<h3>${shell.info.ranges}</h3><ul class="range-list">${items}</ul>`);
  }
  if (entry.note) parts.push(`<div class="note">${entry.note}</div>`);
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
export function infoOpen() {
  return Boolean(popover && !popover.hidden);
}

/**
 * Open the explanation of an id beside its button; the same button closes it again.
 *
 * @param {string} id the explanation's id
 * @param {HTMLElement} target the button
 * @param {Object<string, unknown>} [values] the current values by option name
 */
export function openInfo(id, target, values = {}) {
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
    `<div class="ip-body">${entry ? infoBody(entry, values) : ""}</div>`;
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
