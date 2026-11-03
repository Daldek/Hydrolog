// The panel „Dane” of Sieć (plan S4, the mockup's steps): 1 the network (its file, loaded
// from the disk, a hand-off („Wczytaj z Hydrografa”), the example or saved; its name, time
// step and default rainfall; the session files it reads), 2 its nodes (a list that chooses
// a node, with each node's peak after „Oblicz sieć”) and 3 the settings of the chosen node.

import { FileField } from "../../controls/file-field.js";
import { num, plural } from "../../format.js";
import { HandoffImport, HandoffOrigin } from "../../handoff/handoff-panel.js";
import { html, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { siec as texts } from "../../labels/siec.js";
import { KINDS, networkLayout, RAINFALLS } from "./node-model.js";
import { Choice, controlId, FieldSlot, NodeForm } from "./node-form.js";

/**
 * A step of the panel: a numbered, collapsible section.
 *
 * @param {{number: number, title: any, meta?: any, name: string, children: any,
 *   open?: boolean}} props
 * @returns {object} the step
 */
function Step({ number, title, meta, name, children, open = true }) {
  return html`
    <details class=${`step${name === "node" ? " node-step" : ""}`} data-step=${name} open=${open}>
      <summary>
        <span class="step-num">${number}</span>
        <span class="title">${title}</span>
        ${meta ? html`<span class="meta">${meta}</span>` : null}
        <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
      </summary>
      <div class="step-body">${children}</div>
    </details>
  `;
}

/**
 * The counts of the network's nodes by kind, in words: „3 zlewnie (25,00 km²), 2 odcinki,
 * 2 złącza, wylot”.
 *
 * @param {object[]} skeleton the structure
 * @param {Map<string, object>} words the nodes' descriptions
 * @returns {string} the summary
 */
export function networkSummary(skeleton, words) {
  const parts = [];
  for (const kind of KINDS) {
    const nodes = skeleton.filter((node) => node.type === kind);
    if (!nodes.length) continue;
    let part = plural(nodes.length, texts.kinds[kind].forms);
    if (kind === "subcatchment") {
      const areas = nodes.map((node) => (words.get(node.id) || {}).area).filter((area) => typeof area === "number");
      if (areas.length) part += ` (${t(texts.meta.area, { area: num(areas.reduce((sum, area) => sum + area, 0), 2) })})`;
    }
    if (kind === "outlet" && nodes.length === 1) part = texts.kinds.outlet.noun;
    parts.push(part);
  }
  return parts.join(", ");
}

/**
 * Step 1: the network.
 *
 * @param {object} props see DataPanel
 * @returns {object} the step
 */
function NetworkStep({ state, forms, problems, summary, needed, note, onNetwork, onRun, onLoad, onCompanions, onExample, onSave, canSave }) {
  const fileInput = useRef(null);
  const companions = useRef(null);
  const layout = networkLayout(forms, state.network);
  const prefix = "siec-net";
  const set = (key, value) => onNetwork({ ...state.network, [key]: value });
  const render = (slot) => html`<${FieldSlot} key=${slot.key} slot=${slot} values=${state.network} problems=${problems} prefix=${prefix} onValue=${set} />`;
  const name = (state.source && state.source.name) || "";
  const inflows = forms.run.get("inflows_file");
  const timeColumn = forms.run.get("time_column");
  const needsInflows = needed.inflows.length > 0;
  return html`
    <div class="handoff network-file" data-network-file=${name}>
      <svg class="file-ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>
      <div>
        <strong>${name}</strong>: ${texts.file.document} <code>hydrolog-network/1</code>
        <span class="muted">${state.source && state.source.kind === "example" ? `${texts.file.example} · ` : ""}${summary}</span>
      </div>
    </div>
    ${state.source && state.source.handoff ? html`<${HandoffOrigin} received=${state.source.handoff} small=${true} />` : null}
    <div class="btn-row">
      <${HandoffImport} />
      <button class="btn sm" type="button" data-action="load" onClick=${() => fileInput.current.click()}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 14V4M6 8l4-4 4 4M4 16h12" /></svg>
        ${texts.file.load}
      </button>
      <input ref=${fileInput} type="file" multiple hidden data-input="network" onChange=${onLoad} />
      <button class="btn sm ghost" type="button" data-action="companions" title=${texts.file.companionsTitle} onClick=${() => companions.current.click()}>${texts.file.companions}</button>
      <input ref=${companions} type="file" multiple hidden data-input="companions" onChange=${onCompanions} />
      <button class="btn sm ghost" type="button" data-action="example" onClick=${onExample}>${texts.file.loadExample}</button>
      <button class="btn sm ghost" type="button" data-action="save" title=${canSave ? texts.file.saveTitle : texts.exports.invalid} disabled=${!canSave} onClick=${onSave}>${texts.file.save}</button>
    </div>
    ${note
      ? html`<div class=${note.error ? "form-errors" : "note"} role=${note.error ? "alert" : "status"} data-note="load">
          ${note.error ? html`<strong>${note.title}</strong>` : null}
          ${note.lines.length === 1 && !note.error ? note.lines[0] : html`<ul>${note.lines.map((line) => html`<li>${line}</li>`)}</ul>`}
        </div>`
      : null}
    <p class="note">${texts.file.structure}</p>
    ${layout.slots.map(render)}
    <${Choice}
      id=${`${prefix}-rainfall`}
      name="#rainfall"
      title=${texts.form.networkRainfall}
      items=${RAINFALLS.filter((kind) => layout.rainfall.choice.items.includes(kind)).map((kind) => ({ value: kind, label: texts.rainfalls.network[kind] }))}
      value=${layout.rainfall.choice.value}
      onChange=${(kind) => set("#rainfall", kind)}
    />
    ${layout.rainfall.slots.map(render)}
    <h4 class="sub-title">${texts.files.title}</h4>
    ${inflows && (needsInflows || state.inflowsFile)
      ? html`
          <div class="slot" data-key="inflows_file">
            <${FileField}
              field=${inflows}
              id=${controlId(prefix, "inflows_file")}
              value=${state.inflowsFile}
              error=${needsInflows && !state.inflowsFile ? texts.files.inflowsMissing : undefined}
              required=${needsInflows}
              onInput=${(value) => onRun({ inflowsFile: value })}
            />
          </div>
          ${timeColumn
            ? html`<div class="slot" data-key="time_column">
                <${FieldSlot}
                  slot=${{ key: "time_column", field: timeColumn }}
                  values=${{ time_column: state.timeColumn }}
                  problems=${{}}
                  prefix=${prefix}
                  onValue=${(_, value) => onRun({ timeColumn: value })}
                />
              </div>`
            : null}
          ${needsInflows ? html`<p class="note">${t(texts.files.inflowsFor, { nodes: needed.inflows.join(", ") })}</p>` : null}
        `
      : null}
    ${needed.ratings.length
      ? html`<ul class="file-status" data-files="ratings">
          ${needed.ratings.map(
            (item) => html`<li data-rating=${item.name} class=${item.present ? "ok" : "missing"}>
              <code>${item.node}</code> ${texts.files.rating} <code>${item.name}</code>:
              <span class=${item.present ? "ok-mark" : "bad-mark"}>${item.present ? texts.files.present : texts.files.absent}</span>
            </li>`,
          )}
        </ul>`
      : null}
    ${!needed.ratings.length && !(inflows && (needsInflows || state.inflowsFile)) ? html`<p class="note">${texts.files.none}</p>` : null}
  `;
}

/**
 * Step 2: the list of nodes; a node is chosen by its button.
 *
 * @param {{skeleton: object[], words: Map<string, object>, values: Map<string, object>|null,
 *   wrong: Set<string>, selected: string|null, onSelect: (id: string) => void}} props
 * @returns {object} the list
 */
function NodeList({ skeleton, words, values, wrong, selected, onSelect }) {
  return html`
    <ul class="node-list" aria-label=${texts.list.label}>
      ${skeleton.map((node) => {
        const on = node.id === selected;
        const value = values ? values.get(node.id) : null;
        const word = words.get(node.id) || { meta: "" };
        return html`<li key=${node.id}>
          <button type="button" class=${on ? "sel" : ""} data-node=${node.id} aria-pressed=${on ? "true" : "false"} onClick=${() => onSelect(node.id)}>
            <i class=${`ng t-${node.type}`} aria-hidden="true"></i>
            <code>${node.id}</code>
            <span>${word.meta || texts.kinds[node.type].noun}</span>
            ${wrong.has(node.id)
              ? html`<span class="nq bad-mark" title=${texts.list.wrong}>!</span>`
              : html`<span class="nq">${value ? num(value.peak_m3s, 1) : ""}</span>`}
          </button>
        </li>`;
      })}
    </ul>
    <p class="note">${texts.list.note}</p>
  `;
}

/**
 * The panel „Dane” of Sieć.
 *
 * @param {object} props the section's state and handlers: `state`, `forms`, `words`,
 *   `values` (each node's result), `problems` (by node, and `network`), `summary`,
 *   `needed` (the session files), `note` (of the last load), `nodeResult` (the chosen
 *   node's result), `networkRain` (the words of the network's rainfall), and the handlers
 *   `onNetwork`, `onRun`, `onNode`, `onSelect`, `onLoad`, `onCompanions`, `onExample`,
 *   `onSave`, `canSave`
 * @returns {object} the panel's body
 */
export function DataPanel(props) {
  const { state, forms, words, values, problems, onSelect, onNode, nodeResult, networkRain } = props;
  const node = state.skeleton.find((item) => item.id === state.selected) || null;
  const to = node ? (state.skeleton.find((item) => item.from && item.from.includes(node.id)) || {}).id || null : null;
  const wrong = new Set(Object.keys(problems.nodes).filter((id) => Object.keys(problems.nodes[id]).length));
  const counts = KINDS.filter((kind) => kind !== "outlet" && kind !== "junction")
    .map((kind) => {
      const count = state.skeleton.filter((item) => item.type === kind).length;
      return count ? plural(count, texts.kinds[kind].forms) : null;
    })
    .filter(Boolean)
    .join(" · ");
  const word = node ? words.get(node.id) : null;
  return html`
    <div class="steps">
      <${Step} number=${1} name="network" title=${texts.steps.network} meta=${plural(state.skeleton.length, texts.nodeForms)}>
        <${NetworkStep} ...${props} problems=${problems.network} />
      </${Step}>
      <${Step} number=${2} name="nodes" title=${texts.steps.nodes} meta=${counts}>
        <${NodeList} skeleton=${state.skeleton} words=${words} values=${values} wrong=${wrong} selected=${state.selected} onSelect=${(id) => onSelect(id, false)} />
      </${Step}>
      ${node
        ? html`<${Step} number=${3} name="node" title=${word ? word.title : node.id} meta=${word ? word.meta : ""}>
            <${NodeForm}
              key=${node.id}
              forms=${forms}
              node=${node}
              to=${to}
              values=${state.nodes[node.id] || {}}
              problems=${problems.nodes[node.id] || {}}
              result=${nodeResult}
              networkRain=${networkRain}
              inflowsFile=${state.inflowsFile}
              onChange=${(next) => onNode(node.id, next)}
            />
          </${Step}>`
        : null}
    </div>
  `;
}

/**
 * The words of the network's default rainfall for the subcatchments that take it.
 *
 * @param {object} network the network's values
 * @returns {string} e.g. „Opad sieci (rainfall w kroku 1): projektowy, block, 30 mm, 60 min.”
 */
export function networkRainWords(network) {
  const kind = network["#rainfall"];
  if (kind === "design") {
    return t(texts.form.networkDesign, {
      type: network["rainfall.design.hietogram_type"] || "–",
      total: network["rainfall.design.total_mm"] || "–",
      duration: network["rainfall.design.duration_min"] || "–",
    });
  }
  if (kind === "series") return texts.form.networkSeries;
  return texts.form.networkNone;
}
