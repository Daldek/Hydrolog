/**
 * The Polish texts of the chart module itself (DEV-2.3: texts apart from the code).
 *
 * The texts of a particular chart (titles, axis labels, series names) come
 * with its spec from the section; these are the module's own words.
 */
export const CHART_TEXT = {
  /** The first row of the probability axis: the exceedance probability. */
  probability: "p [%]",
  /** The second row of the probability axis: the return period. */
  returnPeriod: "T [lata]",
  /** The readout's heading on a time axis; `{t}` is "h:mm". */
  readoutTime: "t = {t}",
  /** The readout's heading on a probability axis. */
  readoutProbability: "p = {p} % · T = {T} lat",
  /** The readout's heading on any other axis. */
  readoutValue: "{label} = {x}",
  /** What the keys do, for screen readers (aria-description of the chart). */
  keysHint: "Strzałki w lewo i w prawo: odczyt wartości; Home, End: początek i koniec; Esc: ukryj odczyt.",
};

/**
 * Fill `{name}` placeholders of a text.
 *
 * @param {string} text e.g. CHART_TEXT.readoutTime
 * @param {Record<string, string>} values the values by name
 * @returns {string}
 */
export function fill(text, values) {
  return text.replace(/\{(\w+)\}/g, (_, name) => values[name] ?? "");
}
