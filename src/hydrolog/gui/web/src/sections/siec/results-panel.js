// The results of Sieć (plan S4, the mockup's „Wyniki” and „Tabela węzłów”): in the centre
// every node's kind, description, the node it flows into (plan 2026-11-10-network-editor,
// D1), peak, time to peak, volume, attenuation and delay, in the order of the calculation,
// each row choosing its node; in the panel the outlet's numbers, the chosen node's chart
// (its inflows and its outflow) and parameters, its hydrograph as a table, the notices,
// the exports (with the print view) and the call, and „Przekazanie”, the hand-off
// nogat-handoff/1 of the network (handoff/handoff-panel.js).

import { toPng } from "../../charts/png.js";
import { Chart } from "../../charts/chart.js";
import { auto, hmm, inputText, num, parseNumber } from "../../format.js";
import { Notices } from "../../forms/result-view.js";
import { html, useMemo, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { exportLabels } from "../../labels/exports.js";
import { handoffLabels } from "../../labels/handoff.js";
import { resultFields, options as optionLabels } from "../../labels/options.js";
import { results as resultTexts } from "../../labels/results.js";
import { siec as texts } from "../../labels/siec.js";
import { unitOfName } from "../../labels/units.js";
import { SiecHandoff } from "../../handoff/handoff-panel.js";
import { printView } from "../../print.js";
import { CommandLine, downloadBlob } from "../../ui/export-panel.js";
import { Part } from "../../ui/part.js";
import { DataTable } from "../../ui/table.js";
import { toast } from "../../ui/toast.js";
import { inflowsOf, nodeChartSpec, outflowLabel, resultNodes } from "./charts.js";
import { exportItems } from "./export.js";

/**
 * A volume for people: thousands of m³ in the table, millions in a tile.
 *
 * @param {number} volume the volume [m³]
 * @returns {{value: string, unit: string}} the number and its unit
 */
export function volumeText(volume) {
  if (typeof volume !== "number" || !Number.isFinite(volume)) return { value: common.empty, unit: "" };
  if (volume >= 1e6) return { value: num(volume / 1e6, 3), unit: texts.units.million };
  return { value: num(volume / 1e3, 1), unit: texts.units.thousand };
}

/**
 * The kind of a node in words, with its description.
 *
 * @param {object} node the node's structure
 * @param {object|undefined} words its description (nodeWords)
 * @returns {string} e.g. „zlewnia · 12,00 km² · CN 75”
 */
function kindText(node, words) {
  const kind = texts.kinds[node.type] ? texts.kinds[node.type].noun : node.type;
  return words && words.meta && node.type !== "junction" && node.type !== "outlet" ? `${kind} · ${words.meta}` : kind;
}

/**
 * The table of every node's result; a node is chosen by its row's button.
 *
 * @param {{skeleton: object[], words: Map<string, object>, result: object|null,
 *   selected: string|null, onSelect: (id: string) => void}} props the structure, the
 *   nodes' descriptions, the last result, the chosen node and the handler
 * @returns {object} the card
 */
export function NodeTable({ skeleton, words, result, selected, onSelect }) {
  const nodes = result ? resultNodes(result) : new Map();
  const order = result && Array.isArray(result.order) ? result.order.filter((id) => skeleton.some((node) => node.id === id)) : skeleton.map((node) => node.id);
  for (const node of skeleton) if (!order.includes(node.id)) order.push(node.id);
  const byId = new Map(skeleton.map((node) => [node.id, node]));
  const below = new Map();
  for (const node of skeleton) for (const up of node.from || []) if (!below.has(up)) below.set(up, []);
  for (const node of skeleton) for (const up of node.from || []) below.get(up).push(node.id);
  return html`
    <div class="card" data-card="nodes">
      <div class="card-head">
        <h3 class="card-title">${texts.nodeTable.title}</h3>
        <span class="card-sub">${result ? texts.nodeTable.subResult : texts.nodeTable.subNone}</span>
      </div>
      <div class="table-wrap" tabindex="0" role="region" aria-label=${texts.nodeTable.title}>
        <table class="dtable node-table">
          <thead>
            <tr>
              <th scope="col">${texts.nodeTable.node}</th>
              <th scope="col" class="txt">${texts.nodeTable.kind}</th>
              <th scope="col" class="txt">${texts.nodeTable.description}</th>
              <th scope="col" class="txt">${texts.nodeTable.to}</th>
              <th scope="col">Qp <span class="u">[m³/s]</span></th>
              <th scope="col">tp <span class="u">[h:min]</span></th>
              <th scope="col">V <span class="u">[${texts.units.thousand}]</span></th>
              <th scope="col">${texts.nodeTable.attenuation}</th>
              <th scope="col">${texts.nodeTable.delay}</th>
            </tr>
          </thead>
          <tbody>
            ${order.map((id) => {
              const node = byId.get(id);
              const value = nodes.get(id);
              const routed = value && typeof value.peak_attenuation_pct === "number";
              return html`<tr key=${id} class=${id === selected ? "sel" : undefined} data-node-row=${id}>
                <th scope="row">
                  <button class="link-btn node-pick" type="button" aria-pressed=${id === selected ? "true" : "false"} onClick=${() => onSelect(id)}>${id}</button>
                </th>
                <td class="txt">${kindText(node, words.get(id))}</td>
                <td class="txt desc" data-column="description">${node.description || common.empty}</td>
                <td class="txt" data-column="to">${below.has(id) ? below.get(id).join(", ") : common.empty}</td>
                <td>${value ? num(value.peak_m3s, 2) : common.empty}</td>
                <td>${value ? hmm(value.time_to_peak_min) : common.empty}</td>
                <td>${value ? num(value.volume_m3 / 1e3, 1) : common.empty}</td>
                <td>${routed ? `${num(value.peak_attenuation_pct, 1)} %` : common.empty}</td>
                <td>${routed ? hmm(value.peak_delay_min) : common.empty}</td>
              </tr>`;
            })}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/**
 * The tiles of a result: the outlet's peak, time to peak and volume, and the strongest
 * attenuation of a reach or reservoir (else the count of nodes).
 *
 * @param {{result: object}} props the result
 * @returns {object} the tiles
 */
function Tiles({ result }) {
  const nodes = resultNodes(result);
  const outlet = nodes.get(result.outlet);
  const volume = volumeText(outlet ? outlet.volume_m3 : null);
  let strongest = null;
  for (const node of nodes.values()) {
    if (typeof node.peak_attenuation_pct === "number" && (!strongest || node.peak_attenuation_pct > strongest.peak_attenuation_pct)) strongest = node;
  }
  return html`
    <div class="summary" data-tiles="network">
      <div class="kpi hi" data-tile="peak"><div class="k">${texts.tiles.peak}</div><div class="v">${outlet ? num(outlet.peak_m3s, 1) : common.empty} <span class="u">m³/s</span></div></div>
      <div class="kpi" data-tile="time"><div class="k">${texts.tiles.time}</div><div class="v">${outlet ? hmm(outlet.time_to_peak_min) : common.empty} <span class="u">h</span></div></div>
      <div class="kpi" data-tile="volume"><div class="k">${texts.tiles.volume}</div><div class="v">${volume.value} <span class="u">${volume.unit}</span></div></div>
      ${strongest
        ? html`<div class="kpi" data-tile="attenuation"><div class="k">${t(texts.tiles.attenuation, { id: strongest.id })}</div><div class="v">${num(strongest.peak_attenuation_pct, 1)} <span class="u">%</span></div></div>`
        : html`<div class="kpi" data-tile="nodes"><div class="k">${texts.tiles.nodes}</div><div class="v">${nodes.size}</div></div>`}
    </div>
  `;
}

/**
 * A parameter of a node's result as a row: its Polish label and name, value and unit.
 *
 * @param {string} name the parameter's name
 * @param {unknown} value its value
 * @returns {{name: string, sym: string|null, label: string|null, value: string,
 *   unit: string}} the row
 */
function parameterRow(name, value) {
  const label = texts.parameters[name] || resultFields[name] || optionLabels[name] || null;
  let shown = String(value);
  if (name === "balance_error_m3" && typeof value === "number") shown = num(value, 1);
  else if (typeof value === "number") shown = auto(value);
  else if (typeof value === "boolean") shown = value ? common.yes : common.no;
  // "subreaches_min" is the fewest sub-reaches, a count, not minutes
  const unit = name.startsWith("subreaches") ? "" : unitOfName(name) || "";
  return { name, sym: label ? name : null, label, value: shown, unit };
}

/**
 * The numbers of a node's result: peak, time and volume, how a reach changed the wave, and
 * the parameters its calculation used.
 *
 * @param {{node: object, nodes: Map<string, object>}} props the node of the result and
 *   every node
 * @returns {object} the table
 */
function NodeNumbers({ node, nodes }) {
  const rows = [];
  const inflows = inflowsOf(nodes, node);
  if (typeof node.peak_attenuation_pct === "number" && inflows.length === 1) {
    rows.push({
      name: "peak",
      sym: null,
      label: texts.numbers.peaks,
      value: t(texts.numbers.arrow, { from: num(inflows[0].peak_m3s, 2), to: num(node.peak_m3s, 2) }),
      unit: "m³/s",
    });
  } else {
    rows.push({ name: "peak_m3s", sym: "peak_m3s", label: texts.numbers.peak, value: num(node.peak_m3s, 2), unit: "m³/s" });
  }
  rows.push({ name: "time_to_peak_min", sym: "time_to_peak_min", label: texts.numbers.time, value: hmm(node.time_to_peak_min), unit: "h:min" });
  const volume = volumeText(node.volume_m3);
  rows.push({ name: "volume_m3", sym: "volume_m3", label: texts.numbers.volume, value: volume.value, unit: volume.unit });
  if (typeof node.peak_attenuation_pct === "number") {
    rows.push({ name: "peak_attenuation_pct", sym: "peak_attenuation_pct", label: resultFields.peak_attenuation_pct, value: num(node.peak_attenuation_pct, 1), unit: "%" });
    rows.push({ name: "peak_delay_min", sym: "peak_delay_min", label: resultFields.peak_delay_min, value: hmm(node.peak_delay_min), unit: "h:min" });
  }
  if (node.type === "junction") {
    for (const inflow of inflows) {
      rows.push({ name: `inflow:${inflow.id}`, sym: null, label: t(texts.numbers.inflowPeak, { id: inflow.id }), value: num(inflow.peak_m3s, 2), unit: "m³/s" });
    }
  }
  if (node.model) rows.push({ name: "model", sym: null, label: texts.numbers.model, value: node.model, unit: "" });
  for (const [name, value] of Object.entries(node.parameters || {})) rows.push(parameterRow(name, value));
  if (typeof node.balance_error_m3 === "number") rows.push(parameterRow("balance_error_m3", node.balance_error_m3));
  return html`
    <table class="params compact" data-params=${node.id}>
      <tbody>
        ${rows.map(
          (row) => html`<tr data-param=${row.name}>
            <th scope="row">${row.label || html`<code>${row.name}</code>`}${row.sym ? html`<span class="sym">${row.sym}</span>` : null}</th>
            <td>${row.value}</td>
            <td class="u">${row.unit}</td>
          </tr>`,
        )}
      </tbody>
    </table>
  `;
}

/**
 * The ordinates of a node's hydrograph and its inflows, as a table.
 *
 * @param {{node: object, nodes: Map<string, object>}} props the node and every node
 * @returns {object} the details
 */
function Ordinates({ node, nodes }) {
  const inflows = inflowsOf(nodes, node);
  const columns = [
    { key: "t", label: resultTexts.time, format: (value) => hmm(value) },
    ...inflows.map((inflow) => ({ key: `in-${inflow.id}`, label: t(texts.chart.inflow, { id: inflow.id }), unit: "m³/s", format: (value) => (typeof value === "number" ? num(value, 3) : common.empty) })),
    { key: "q", label: outflowLabel(node), unit: "m³/s", format: (value) => num(value, 3) },
  ];
  const rows = node.times_min.map((time, index) => {
    const row = { t: time, q: node.discharge_m3s[index] };
    for (const inflow of inflows) {
      const at = inflow.times_min.indexOf(time);
      row[`in-${inflow.id}`] = at >= 0 ? inflow.discharge_m3s[at] : null;
    }
    return row;
  });
  return html`
    <details class="more" data-more="ordinates">
      <summary>${texts.ordinates} <span class="meta">${rows.length}</span></summary>
      <${DataTable} columns=${columns} rows=${rows} label=${t(texts.ordinatesOf, { id: node.id })} tall=${false} rowHeader=${false} />
    </details>
  `;
}

/**
 * The export buttons of Sieć and the call of the last run.
 *
 * @param {{items: object[]}} props the exports of exportItems
 * @returns {object} the buttons
 */
function ExportRow({ items }) {
  const save = async (item) => {
    if (item.href) return;
    if (item.print) {
      printView();
      return;
    }
    if (item.svg) {
      const svg = item.svg();
      if (!svg) return;
      try {
        downloadBlob(await toPng(svg, { scale: 2 }), item.name);
        toast(t(exportLabels.saved, { name: item.name }));
      } catch (error) {
        toast(t(exportLabels.pngFailed, { message: String((error && error.message) || error) }), "bad");
      }
      return;
    }
    downloadBlob(new Blob([item.text()], { type: item.type }), item.name);
    toast(t(exportLabels.saved, { name: item.name }));
  };
  return html`
    <div class="btn-row export-row">
      ${items.map((item) =>
        item.href
          ? html`<a class="btn" data-export=${item.id} href=${item.href} download=${item.name} title=${item.title}><span class="fmt">${item.format}</span>${item.label}</a>`
          : html`<button
              class="btn"
              type="button"
              data-export=${item.id}
              title=${item.disabled || item.title}
              disabled=${Boolean(item.disabled)}
              onClick=${() => save(item)}
            >
              <span class="fmt">${item.format}</span>${item.label}
            </button>`,
      )}
    </div>
  `;
}

/**
 * The one-click changes of method of a reach Hydrolog refused at its time step (reachFix):
 * a lag of the wave's travel time, or of a typed value when the error does not give it, and
 * a level-pool storage.
 *
 * @param {{fix: object, onLag: (fix: object, minutes: number) => void, onLevelPool: (fix:
 *   object) => void}} props the offer and its actions
 * @returns {object} the buttons
 */
function ReachFix({ fix, onLag, onLevelPool }) {
  const words = texts.unstable;
  const [typed, setTyped] = useState("");
  const minutes = parseNumber(typed);
  const usable = Number.isFinite(minutes) && minutes > 0;
  const lagWords = { node: fix.node, lag: inputText(fix.lag), length: num(fix.length_m, 1), celerity: num(fix.celerity_m_per_s, 2) };
  return html`
    <div class="btn-row reach-fix" data-fix=${fix.node}>
      ${fix.lag !== null
        ? html`<button class="btn sm" type="button" data-fix-action="lag" title=${t(words.lagTitle, lagWords)} onClick=${() => onLag(fix, fix.lag)}>
            ${t(words.lag, lagWords)}
          </button>`
        : html`<label class="reach-fix-lag">
              <span>${words.lagField}</span>
              <input type="text" inputmode="decimal" size="5" data-fix-field="lag_min" value=${typed} onInput=${(event) => setTyped(event.currentTarget.value)} />
            </label>
            <button class="btn sm" type="button" data-fix-action="lag" disabled=${!usable} title=${t(words.lagTypedTitle, lagWords)} onClick=${() => onLag(fix, minutes)}>
              ${words.lagTyped}
            </button>`}
      ${fix.levelPool
        ? html`<button class="btn sm ghost" type="button" data-fix-action="level-pool" title=${t(words.levelPoolTitle, lagWords)} onClick=${() => onLevelPool(fix)}>
            ${words.levelPool}
          </button>`
        : null}
    </div>
  `;
}

/**
 * The panel Wyniki.
 *
 * @param {{run: object|null, stale: boolean, selected: string|null, state: object,
 *   document: object|null, valid: boolean, chartSvg: object, schematicSvg: object,
 *   error: object|null, fix: object|null, onLag: Function, onLevelPool: Function}} props
 *   the last run and whether the data changed since, the chosen node, the section's state,
 *   the network's document and whether it is complete, the refs of the node's chart and of
 *   the schematic, the last error and the changes of method it offers (ReachFix)
 * @returns {object} the panel's body
 */
export function ResultsPanel({ run, stale, selected, state, document, valid, chartSvg, schematicSvg, error, fix, onLag, onLevelPool }) {
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const nodes = useMemo(() => (result ? resultNodes(result) : new Map()), [result]);
  const node = result && selected ? nodes.get(selected) : null;
  const spec = useMemo(() => (result && selected ? nodeChartSpec(result, selected) : null), [result, selected]);
  const items = exportItems({ state, document, valid, run, selected, schematicSvg });
  return html`
    ${error
      ? html`<div class="form-errors" role="alert" data-error="run">
          <strong>${error.title}</strong>
          <ul><li>${error.text}${error.node ? html` <span class="reason">· ${t(texts.errorNode, { id: error.node })}</span>` : null}</li></ul>
          ${fix ? html`<${ReachFix} key=${fix.node} fix=${fix} onLag=${onLag} onLevelPool=${onLevelPool} />` : null}
        </div>`
      : null}
    ${result && stale
      ? html`<ul class="notes" data-stale="true">
          <li class="warn" role="status">
            <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 4.5v4M8 11v.01" /></svg>
            <div><span class="lvl">${common.levels.warning}</span> ${texts.staleNote}</div>
          </li>
        </ul>`
      : null}
    ${result ? html`<${Tiles} result=${result} />` : html`<p class="muted" data-empty="results">${run && run.envelope.status === "cancelled" ? resultTexts.cancelled : texts.noResult}</p>`}
    ${run && run.envelope.status === "cancelled" ? html`<${Notices} notices=${run.envelope.notices} />` : null}
    ${node
      ? html`
          <h3 class="group-title" data-result-node=${node.id}>${t(texts.selectedNode, { id: node.id })}</h3>
          <div class="node-res" data-node-res=${node.id}>
            <div class="chart-title" id=${`siec-res-${node.id}`}>${t(texts.chart.heading, { id: node.id, what: texts.chart.what[node.type] || "" })}</div>
            ${spec ? html`<${Chart} key=${node.id} spec=${spec} svgRef=${chartSvg} class="node-chart" />` : null}
            <${NodeNumbers} node=${node} nodes=${nodes} />
            ${Array.isArray(node.times_min) ? html`<${Ordinates} node=${node} nodes=${nodes} />` : null}
          </div>
        `
      : result
        ? html`<p class="muted">${texts.pickNode}</p>`
        : null}
    ${result
      ? html`<h3 class="group-title">${resultTexts.notices}</h3>
          <${Notices} notices=${run.envelope.notices} />`
      : null}
    <div class="steps">
      <${Part} id="exports" title=${exportLabels.title} meta="route network" open=${false}>
        <${ExportRow} items=${items} />
        ${run ? html`<${CommandLine} command="route network" options=${run.options} title=${false} />` : null}
      <//>
      <${Part} id="handoff" title=${handoffLabels.export.title} meta=${handoffLabels.export.meta} open=${Boolean(state.source && state.source.handoff)}>
        <${SiecHandoff} state=${state} document=${document} valid=${valid} run=${run} stale=${stale} />
      <//>
    </div>
  `;
}
