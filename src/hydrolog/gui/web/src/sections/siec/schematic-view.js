// The schematic of the network, drawn vertically (plan S4, the mockup's `.schem-v`): the
// sources at the top, the outlet at the bottom, the main stem straight and the
// tributaries joining it at 45 degrees, from Hydrolog's hydrolog-network-schematic/1
// turned by schematic.js. A node is a button: a click, Enter or Space selects it (its
// settings open in „Dane”, its result in „Wyniki”). Beside each node: its id, a short
// description and, after „Oblicz sieć”, the peak and the time to peak.

import { hmm, num } from "../../format.js";
import { html, useMemo } from "../../html.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";
import { labelLines, pictureBox, verticalLayout } from "./schematic.js";

/**
 * The glyph of a node: a diamond (subcatchment), a bar across the line (reach), a circle
 * (junction), a rounded box (reservoir), a ringed circle (outlet).
 *
 * @param {{type: string, cx: number, cy: number}} node the node
 * @returns {object} the SVG shapes
 */
function Glyph({ node }) {
  const { cx, cy } = node;
  switch (node.type) {
    case "subcatchment":
      return html`<polygon class="glyph" points=${`${cx},${cy - 11} ${cx + 11},${cy} ${cx},${cy + 11} ${cx - 11},${cy}`} />`;
    case "reach":
      return html`<rect class="glyph" x=${cx - 12} y=${cy - 4} width="24" height="8" rx="2" />`;
    case "reservoir":
      return html`<rect class="glyph" x=${cx - 10} y=${cy - 13} width="20" height="26" rx="4" />`;
    case "outlet":
      return html`<circle class="glyph" cx=${cx} cy=${cy} r="11" /><circle class="glyph-in" cx=${cx} cy=${cy} r="5" />`;
    default:
      return html`<circle class="glyph" cx=${cx} cy=${cy} r="8" />`;
  }
}

/**
 * The lines of a node's label: the id (with the area of a subcatchment), its description
 * and, with a result, the peak and the time to peak.
 *
 * @param {string} id the node's id
 * @param {{short: string, area: number|null}|undefined} words its description (nodeWords)
 * @param {{peak_m3s: number, time_to_peak_min: number}|undefined} value its result
 * @returns {Array<{cls: string, text: string}>} the lines
 */
export function labelOf(id, words, value) {
  const area = words && words.area !== null ? t(texts.schematic.area, { area: num(words.area, 1) }) : null;
  const lines = [{ cls: "lbl-id", text: area ? `${id} · ${area}` : id }];
  if (words && words.short) lines.push({ cls: "lbl-m", text: words.short });
  if (value) {
    lines.push({ cls: "lbl-v", text: t(texts.schematic.values, { peak: num(value.peak_m3s, 1), time: hmm(value.time_to_peak_min) }) });
  }
  return lines;
}

/**
 * The accessible name of a node: its id, kind, description and result.
 *
 * @param {{id: string, type: string}} node the node
 * @param {object|undefined} words its description
 * @param {object|undefined} value its result
 * @returns {string} the name
 */
export function nodeName(node, words, value) {
  const kind = texts.kinds[node.type] ? texts.kinds[node.type].noun : node.type;
  const parts = [`${node.id} · ${kind}`];
  if (words && words.meta) parts[0] += `, ${words.meta}`;
  if (value) {
    parts.push(
      t(texts.schematic.result, {
        peak: num(value.peak_m3s, 2),
        time: hmm(value.time_to_peak_min),
        volume: num(value.volume_m3 / 1000, 1),
      }),
    );
  }
  return parts.join(" · ");
}

/**
 * The schematic.
 *
 * @param {{schematic: object, words: Map<string, object>, values: Map<string, object>|null,
 *   selected: string|null, onSelect: (id: string) => void, svgRef?: object,
 *   titleId: string}} props the hydrolog-network-schematic/1 document, each node's
 *   description, each node's result (null before „Oblicz sieć”), the chosen node, the
 *   handler of a choice, the ref of the svg (PNG) and the id of the card's title
 * @returns {object} the svg
 */
export function Schematic({ schematic, words, values, selected, onSelect, svgRef, titleId }) {
  const picture = useMemo(() => verticalLayout(schematic), [schematic]);
  const labels = new Map(
    picture.nodes.map((node) => [node.id, labelOf(node.id, words.get(node.id), values ? values.get(node.id) : undefined)]),
  );
  const box = pictureBox(picture, new Map([...labels].map(([id, lines]) => [id, lines.map((line) => line.text)])));
  const edges = [...picture.edges].sort((a, b) => Number(a.main) - Number(b.main));
  const onKeyDown = (id) => (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(id);
    }
  };
  return html`
    <svg
      class="chart-svg schem"
      ref=${svgRef}
      viewBox=${box.join(" ")}
      width=${box[2]}
      height=${box[3]}
      role="group"
      aria-labelledby=${titleId}
      data-outlet=${picture.outlet}
    >
      <g class="lines">
        ${edges.map((edge) =>
          edge.points.slice(1).map((point, index) => {
            const from = edge.points[index];
            return html`<line
              class=${`ln ${edge.main ? "main" : "trib"}`}
              data-edge=${`${edge.from}>${edge.to}`}
              x1=${from[0]}
              y1=${from[1]}
              x2=${point[0]}
              y2=${point[1]}
            />`;
          }),
        )}
      </g>
      ${picture.nodes.map((node) => {
        const lines = labels.get(node.id);
        const placed = labelLines(node, lines.length);
        const value = values ? values.get(node.id) : undefined;
        const name = nodeName(node, words.get(node.id), value);
        const on = node.id === selected;
        return html`
          <g
            key=${node.id}
            class=${`node t-${node.type}${on ? " sel" : ""}`}
            data-node=${node.id}
            data-place=${node.place}
            tabindex="0"
            role="button"
            aria-pressed=${on ? "true" : "false"}
            aria-label=${name}
            onClick=${() => onSelect(node.id)}
            onKeyDown=${onKeyDown(node.id)}
          >
            <title>${name}</title>
            <circle class="halo" cx=${node.cx} cy=${node.cy} r="20" />
            <${Glyph} node=${node} />
            ${lines.map(
              (line, index) => html`<text class=${line.cls} x=${placed.x} y=${placed.ys[index]} text-anchor=${placed.anchor}>${line.text}</text>`,
            )}
          </g>
        `;
      })}
    </svg>
  `;
}
