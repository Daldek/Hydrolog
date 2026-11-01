/**
 * `toPng`: a chart as a PNG image (plan D12, D14).
 *
 * The SVG is cloned with its computed styles written into the clone (the
 * image has no access to the page's stylesheets, so the current theme's
 * colours go with it), serialized, loaded as an Image from a `blob:` URL
 * (`img-src 'self' data: blob:` of the page's policy) and drawn on a canvas
 * filled with the theme's `--surface`.
 */

/** The properties that carry a chart's look. */
const PROPERTIES = [
  "display",
  "visibility",
  "opacity",
  "fill",
  "fill-opacity",
  "stroke",
  "stroke-width",
  "stroke-opacity",
  "stroke-dasharray",
  "stroke-linecap",
  "stroke-linejoin",
  "paint-order",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "font-variant-numeric",
  "text-anchor",
  "dominant-baseline",
];

/**
 * Write the computed styles of `source` and its descendants into `clone`
 * (a deep clone of it) through the CSSOM, never as markup.
 *
 * @param {Element} source the drawn element
 * @param {Element} clone its clone
 */
export function inlineStyles(source, clone) {
  const sources = [source, ...source.querySelectorAll("*")];
  const clones = [clone, ...clone.querySelectorAll("*")];
  sources.forEach((element, index) => {
    const target = clones[index];
    if (!target?.style) return;
    const computed = getComputedStyle(element);
    for (const name of PROPERTIES) {
      const value = computed.getPropertyValue(name);
      if (value) target.style.setProperty(name, value);
    }
  });
}

/**
 * Serialize a drawn SVG with its styles, at its drawn size.
 *
 * @param {SVGSVGElement} svg the drawn chart
 * @returns {{text: string, width: number, height: number}}
 */
export function svgText(svg) {
  const box = svg.getBoundingClientRect();
  const width = Math.max(1, Math.round(box.width));
  const height = Math.max(1, Math.round(box.height));
  const clone = svg.cloneNode(true);
  inlineStyles(svg, clone);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  clone.removeAttribute("tabindex");
  clone.style.removeProperty("display");
  for (const transient of clone.querySelectorAll(".readout")) transient.remove();
  return { text: new XMLSerializer().serializeToString(clone), width, height };
}

/**
 * Render a drawn SVG as a PNG.
 *
 * @param {SVGSVGElement} svg the drawn chart (attached and visible)
 * @param {{scale?: number, background?: string}} [options] `scale` (2 by default)
 *   multiplies the drawn size; `background` replaces the theme's `--surface`
 * @returns {Promise<Blob>} the PNG, `scale` times the drawn width and height
 */
export async function toPng(svg, options = {}) {
  const { scale = 2 } = options;
  const { text, width, height } = svgText(svg);
  const url = URL.createObjectURL(new Blob([text], { type: "image/svg+xml" }));
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const context = canvas.getContext("2d");
    const background = options.background ?? getComputedStyle(svg).getPropertyValue("--surface").trim();
    if (background) {
      context.fillStyle = background;
      context.fillRect(0, 0, canvas.width, canvas.height);
    }
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toPng: no image"))), "image/png");
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}
