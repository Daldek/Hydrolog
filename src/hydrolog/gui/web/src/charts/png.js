/**
 * `toPng`: a chart as a PNG image (plan D12, D14).
 *
 * The SVG is cloned with its computed styles written into the clone (the
 * image has no access to the page's stylesheets, so the current theme's
 * colours go with it), serialized, loaded as an Image from a `blob:` URL
 * (`img-src 'self' data: blob:` of the page's policy) and drawn on a canvas
 * filled with the theme's `--surface`. While the styles are read the SVG has
 * the class `exporting`, under which a picture hides what is not part of it
 * (the selection and the other marks of editing on Sieć's canvas). Rows of a
 * footer (the providers' lines of the data, Nogat DEV-20.5: attribution.js
 * footerLines) are drawn below the chart in the theme's `--text` and the
 * chart's font, each wrapped to the image's width; the image grows by their
 * height.
 */

/** The footer's text [px of the drawn chart]: its size, its line height and the margins. */
const FOOTER = Object.freeze({ size: 11, leading: 1.4, margin: 8 });

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
function inlineStyles(source, clone) {
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
  svg.classList.add("exporting");
  try {
    inlineStyles(svg, clone);
  } finally {
    svg.classList.remove("exporting");
  }
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  clone.removeAttribute("tabindex");
  clone.style.removeProperty("display");
  for (const transient of clone.querySelectorAll(".readout")) transient.remove();
  return { text: new XMLSerializer().serializeToString(clone), width, height };
}

/**
 * The rows of a footer wrapped to a width: each row split at spaces, a word wider than the
 * width at its characters.
 *
 * @param {CanvasRenderingContext2D} context a context with the footer's font set
 * @param {string[]} rows the rows
 * @param {number} width the width they may take [canvas px]
 * @returns {string[]} the lines drawn
 */
function wrapRows(context, rows, width) {
  const fits = (text) => context.measureText(text).width <= width;
  const out = [];
  for (const row of rows) {
    let line = "";
    for (const word of String(row).split(/\s+/).filter(Boolean)) {
      const joined = line ? `${line} ${word}` : word;
      if (fits(joined)) {
        line = joined;
        continue;
      }
      if (line) out.push(line);
      line = "";
      for (const char of word) {
        if (line && !fits(line + char)) {
          out.push(line);
          line = "";
        }
        line += char;
      }
    }
    if (line) out.push(line);
  }
  return out;
}

/**
 * Render a drawn SVG as a PNG.
 *
 * @param {SVGSVGElement} svg the drawn chart (attached and visible)
 * @param {{scale?: number, background?: string, footer?: string[]}} [options] `scale`
 *   (2 by default) multiplies the drawn size; `background` replaces the theme's
 *   `--surface`; `footer` the rows drawn below the chart (none by default)
 * @returns {Promise<Blob>} the PNG, `scale` times the drawn width and height, taller by
 *   the footer's rows
 */
export async function toPng(svg, options = {}) {
  const { scale = 2, footer = [] } = options;
  const { text, width, height } = svgText(svg);
  const style = getComputedStyle(svg);
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  const family = style.getPropertyValue("--font-sans").trim() || style.fontFamily || "sans-serif";
  const font = `${FOOTER.size * scale}px ${family}`;
  context.font = font;
  const rows = footer.length ? wrapRows(context, footer, (width - 2 * FOOTER.margin) * scale) : [];
  const step = FOOTER.size * FOOTER.leading;
  const added = rows.length ? Math.ceil(FOOTER.margin * 2 + rows.length * step) : 0;
  const url = URL.createObjectURL(new Blob([text], { type: "image/svg+xml" }));
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round((height + added) * scale);
    const background = options.background ?? style.getPropertyValue("--surface").trim();
    if (background) {
      context.fillStyle = background;
      context.fillRect(0, 0, canvas.width, canvas.height);
    }
    context.drawImage(image, 0, 0, Math.round(width * scale), Math.round(height * scale));
    if (rows.length) {
      // The canvas's size reset its state: the footer's font again, in the theme's text
      context.font = font;
      context.fillStyle = style.getPropertyValue("--text").trim() || style.color || "#000";
      context.textBaseline = "top";
      rows.forEach((row, index) => {
        const top = height + FOOTER.margin + index * step + (step - FOOTER.size) / 2;
        context.fillText(row, FOOTER.margin * scale, top * scale);
      });
    }
    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toPng: no image"))), "image/png");
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}
