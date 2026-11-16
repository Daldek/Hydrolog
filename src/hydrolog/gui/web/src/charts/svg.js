/**
 * Creating SVG and HTML elements for the charts (the DOM only, no Preact).
 *
 * Attributes are set one by one; no `style` attribute is ever written, so the
 * charts stay within the page's `style-src 'self'` (plan D8): every colour,
 * stroke and font comes from `css/charts.css` through the element's classes.
 */

/** The SVG namespace. */
const SVG_NS = "http://www.w3.org/2000/svg";

/** Round a coordinate to 0.1 of the viewBox (short paths, stable tests). */
export function c1(value) {
  return Math.round(value * 10) / 10;
}

function apply(node, attrs) {
  for (const [name, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    node.setAttribute(name, typeof value === "number" ? String(c1(value)) : String(value));
  }
  return node;
}

/**
 * Create an SVG element.
 *
 * @param {string} tag e.g. "path"
 * @param {Record<string, string | number | boolean | undefined | null>} [attrs]
 *   numbers are rounded to 0.1; `undefined`, `null` and `false` are skipped
 * @param {(Node | string)[]} [children] nodes, or strings as text
 * @returns {SVGElement} the element
 */
export function svgEl(tag, attrs = {}, children = []) {
  const node = apply(document.createElementNS(SVG_NS, tag), attrs);
  for (const child of children) node.append(child);
  return node;
}

/**
 * Create an HTML element.
 *
 * @param {string} tag e.g. "span"
 * @param {Record<string, string | undefined>} [attrs]
 * @param {(Node | string)[]} [children]
 * @returns {HTMLElement} the element
 */
export function htmlEl(tag, attrs = {}, children = []) {
  const node = apply(document.createElement(tag), attrs);
  for (const child of children) node.append(child);
  return node;
}

/**
 * Create an SVG text.
 *
 * @param {string} cls its classes (`tick`, `axis-label`, `note`, …)
 * @param {number} x
 * @param {number} y
 * @param {string} text
 * @param {"start" | "middle" | "end"} [anchor]
 * @returns {SVGTextElement}
 */
export function textEl(cls, x, y, text, anchor) {
  return svgEl("text", { class: cls, x, y, "text-anchor": anchor }, [text]);
}
