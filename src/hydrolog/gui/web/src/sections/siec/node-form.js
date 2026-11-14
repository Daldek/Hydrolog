// The settings of the chosen node in „Dane” (plan S4, the mockup's `.node-form`): its
// structure as ordinary form controls (plan 2026-11-10-network-editor, D7, D12: the id,
// checked as it is typed and changed on Enter or when the field is left; „Opis”;
// „Odpływa do”, with „Wstaw złącze” where the node below takes one inflow; „Usuń węzeł”
// and „Usuń i połącz”), then a form per node type and reach method generated from
// hydrolog-network-1.schema.json (node-model.js) with the controls of the catalog forms,
// the alternatives as segmented choices, a storage table (or a rating file of the
// session) for a reservoir and a level-pool reach. A subcatchment chooses here how it
// brings its hydrograph: given as a table („Podany”), its column of the inflows file („Z
// pliku”), or from rainfall, whose data are Hydrogram zlewni's three steps in the
// subcatchment's own panel beside „Dane” („Dane zlewni →”; plan 2026-11-10-network-wizard,
// D1, D2).

import { ChoiceField, CheckField } from "../../controls/choice-field.js";
import { inputFiles, uploadFile, useSession } from "../../controls/file-field.js";
import { NumberField } from "../../controls/number-field.js";
import { readTable, SeriesField } from "../../controls/series-field.js";
import { TextField } from "../../controls/text-field.js";
import { splitReason } from "../../controls/field.js";
import { bytes, inputText, parseNumber } from "../../format.js";
import { withReason } from "../../forms/model.js";
import { html, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError } from "../../labels/errors.js";
import { siec as texts } from "../../labels/siec.js";
import { InfoButton } from "../../ui/info-button.js";
import { Seg } from "../../ui/seg.js";
import { JunctionOffer } from "./editor/canvas.js";
import { canBridge } from "./editor/edits.js";
import { foldId, idProblem, linkVerdicts, receiversOf, structureKey } from "./editor/graph.js";
import { descriptionProblem, fieldOf, METHODS, nodeLayout, VARIANTS } from "./node-model.js";
import { kindNoun, refusalText } from "./words.js";

const CONTROLS = {
  number: NumberField,
  integer: NumberField,
  choice: ChoiceField,
  boolean: CheckField,
  series: SeriesField,
  text: TextField,
};

/**
 * An id of a control from a value key ("watershed.area_km2" gives "…-watershed-area_km2").
 *
 * @param {string} prefix the form's prefix
 * @param {string} key the value key
 * @returns {string} the id
 */
export function controlId(prefix, key) {
  return `${prefix}-${String(key).replace(/[^\w-]+/g, "-")}`;
}

/**
 * The message of a problem as a field shows it.
 *
 * @param {string|undefined} message the problem
 * @returns {object|null} the message
 */
function Problem({ message, id }) {
  if (!message) return null;
  const { text, reason } = splitReason(message);
  return html`<span class="err" id=${id} role="alert">${text}${reason ? html` <span class="reason">· ${reason}</span>` : null}</span>`;
}

/**
 * The session's input files to choose a rating file from, or a new upload.
 *
 * @param {{slot: object, id: string, value?: string, error?: string, onInput: (name: string)
 *   => void}} props the slot, the control's id, the file name, the message and the handler
 * @returns {object} the field
 */
function RatingFile({ slot, id, value, error, onInput }) {
  const session = useSession();
  const picker = useRef(null);
  const [state, setState] = useState(null);
  const names = inputFiles(session).map((file) => ({ name: file.path.slice(3), size: file.size_bytes }));
  const current = typeof value === "string" ? value : "";
  const known = names.some((file) => file.name === current);
  const onFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (!file) return;
    setState({ text: t(texts.files.uploading, { name: file.name }) });
    try {
      const stored = await uploadFile(file);
      setState({ text: t(texts.files.uploaded, { name: stored.name }) });
      onInput(stored.name);
    } catch (failure) {
      const text = failure && failure.doc ? describeError(failure.doc).text : String((failure && failure.message) || failure);
      setState({ error: true, text: t(texts.files.uploadFailed, { message: text }) });
    }
  };
  const field = slot.field;
  return html`
    <div class=${`opt opt-file${error ? " invalid" : ""}`} data-option=${field.name}>
      <label for=${id}>
        ${field.label ? html`<span class="lbl-text">${field.label}</span>` : null}
        <code>${field.name}</code>
        <span class="req">${common.required}</span>
      </label>
      <div class="file-row">
        <select id=${id} value=${current} aria-invalid=${error ? "true" : "false"} onChange=${(event) => onInput(event.currentTarget.value)}>
          <option value="">${texts.files.choose}</option>
          ${current && !known ? html`<option value=${current}>${t(texts.files.missingOption, { name: current })}</option>` : null}
          ${names.map((file) => html`<option value=${file.name}>${file.name} (${bytes(file.size)})</option>`)}
        </select>
        <button class="btn sm" type="button" onClick=${() => picker.current.click()}>${common.actions.upload}</button>
        <input ref=${picker} type="file" hidden onChange=${onFile} />
      </div>
      ${state ? html`<span class=${state.error ? "err" : "file-state"} role=${state.error ? "alert" : "status"}>${state.text}</span>` : null}
      ${current && !known ? html`<span class="err">${t(texts.files.missing, { name: current })}</span>` : null}
      <span class="hint">${field.description}</span>
      <${Problem} message=${error} id=${`${id}-err`} />
    </div>
  `;
}

/**
 * One field of a form of Sieć, by its slot (a field and the key of its value).
 *
 * @param {{slot: object, values: object, problems: object, prefix: string, onValue:
 *   (key: string, value: unknown) => void}} props the slot, the values and problems of
 *   the form, the prefix of ids and the change handler
 * @returns {object} the field
 */
export function FieldSlot({ slot, values, problems, prefix, onValue }) {
  const id = controlId(prefix, slot.key);
  if (slot.field.name === "rating_file") {
    return html`<div class="slot" data-key=${slot.key}>
      <${RatingFile} slot=${slot} id=${id} value=${values[slot.key]} error=${problems[slot.key]} onInput=${(value) => onValue(slot.key, value)} />
    </div>`;
  }
  const Control = CONTROLS[slot.field.kind] || TextField;
  return html`<div class="slot" data-key=${slot.key}>
    <${Control}
      field=${slot.field}
      id=${id}
      value=${values[slot.key]}
      error=${problems[slot.key]}
      required=${slot.field.required}
      onInput=${(value) => onValue(slot.key, value)}
    />
  </div>`;
}

/**
 * Fields under a summary that opens by itself when one of them has a problem.
 *
 * @param {{title: string, slots: object[], problems: object, children?: any}} props the
 *   summary, the slots and the problems
 * @returns {object|null} the details
 */
function More({ title, slots, problems, render, name }) {
  const [open, setOpen] = useState(null);
  if (!slots.length) return null;
  const wrong = slots.some((slot) => problems[slot.key]);
  const shown = wrong || Boolean(open);
  return html`
    <details class="more" data-more=${name} open=${shown} onToggle=${(event) => setOpen(event.currentTarget.open)}>
      <summary>${title} <span class="meta">${slots.length}</span></summary>
      ${shown ? slots.map(render) : null}
    </details>
  `;
}

/**
 * A choice among alternatives as a segmented control with its title.
 *
 * @param {{id: string, title: string, items: Array<{value: any, label: string}>, value: any,
 *   onChange: (value: any) => void, name: string}} props
 * @returns {object} the choice
 */
function Choice({ id, title, items, value, onChange, name }) {
  return html`
    <div class="field choice-row" data-choice=${name}>
      <span class="label" id=${id}>${title}</span>
      <${Seg} items=${items} value=${value} onChange=${onChange} labelledBy=${id} full=${true} />
    </div>
  `;
}

/**
 * A table of numbers edited by cells: rows added and removed, a block pasted from a
 * spreadsheet, or columns read from a CSV file in the browser.
 *
 * @param {{table: {key: string, columns: Array<{name: string, field: object}>}, rows:
 *   string[][]|undefined, onRows: (rows: string[][]) => void, error?: string, prefix:
 *   string, label: string}} props the table's columns, its rows, the handler, the problem,
 *   the prefix of ids and the table's name
 * @returns {object} the table
 */
function TableEditor({ table, rows, onRows, error, prefix, label }) {
  const list = Array.isArray(rows) && rows.length ? rows : [table.columns.map(() => "")];
  const picker = useRef(null);
  const [note, setNote] = useState(null);
  const width = table.columns.length;
  const setCell = (row, column, value) => {
    const next = list.map((item) => [...item]);
    next[row][column] = value;
    onRows(next);
  };
  const onPaste = (row, column) => (event) => {
    const text = event.clipboardData ? event.clipboardData.getData("text") : "";
    if (!/[\t\n;]/.test(text)) return;
    event.preventDefault();
    const pasted = text
      .replace(/\r/g, "")
      .split("\n")
      .filter((line) => line.trim() !== "")
      .map((line) => line.split(/\t|;/).map((cell) => cell.trim()));
    const next = list.map((item) => [...item]);
    pasted.forEach((cells, offset) => {
      const at = row + offset;
      while (next.length <= at) next.push(table.columns.map(() => ""));
      cells.forEach((cell, index) => {
        if (column + index < width) next[at][column + index] = cell;
      });
    });
    onRows(next);
  };
  const onFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (!file) return;
    try {
      const read = readTable(await file.text());
      const header = (read.header || []).map((name) => String(name).trim());
      const indexOf = (name, at) => {
        const found = header.findIndex((item) => item === name || item.split(" ")[0] === name || (name === "times_min" && item === "time_min"));
        return found >= 0 ? found : read.header ? -1 : at;
      };
      const indices = table.columns.map((column, at) => indexOf(column.name, at));
      if (indices.slice(0, 2).some((index) => index < 0)) {
        setNote({ error: true, text: t(texts.table.noColumns, { columns: table.columns.slice(0, 2).map((column) => column.name).join(", ") }) });
        return;
      }
      onRows(read.rows.map((row) => indices.map((index) => (index >= 0 && row[index] !== undefined ? inputText(parseNumber(row[index])) || row[index] : ""))));
      setNote({ text: t(texts.table.read, { name: file.name, rows: read.rows.length }) });
    } catch (failure) {
      setNote({ error: true, text: t(texts.table.readFailed, { message: String((failure && failure.message) || failure) }) });
    }
  };
  const errorId = `${prefix}-table-err`;
  return html`
    <div class=${`opt table-edit${error ? " invalid" : ""}`} data-table=${table.key}>
      <div class="table-wrap">
        <table class="dtable cells edit" aria-label=${label} aria-describedby=${error ? errorId : undefined}>
          <thead>
            <tr>
              ${table.columns.map(
                (column) => html`<th scope="col">${column.name}${column.field.unitLabel && column.field.unitLabel !== "–" ? html`<br /><span class="u">[${column.field.unitLabel}]</span>` : null}</th>`,
              )}
              <th scope="col"><span class="sr-only">${texts.table.actions}</span></th>
            </tr>
          </thead>
          <tbody>
            ${list.map(
              (row, at) => html`<tr key=${at}>
                ${table.columns.map(
                  (column, index) => html`<td>
                    <input
                      type="text"
                      inputmode="decimal"
                      autocomplete="off"
                      spellcheck=${false}
                      value=${row[index] ?? ""}
                      aria-label=${t(texts.table.cellLabel, { row: at + 1, column: column.name })}
                      onInput=${(event) => setCell(at, index, event.currentTarget.value)}
                      onPaste=${onPaste(at, index)}
                    />
                  </td>`,
                )}
                <td>
                  <button
                    class="btn ghost sm icon"
                    type="button"
                    aria-label=${t(texts.table.removeRow, { row: at + 1 })}
                    title=${t(texts.table.removeRow, { row: at + 1 })}
                    disabled=${list.length === 1}
                    onClick=${() => onRows(list.filter((_, index) => index !== at))}
                  >
                    <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" /></svg>
                  </button>
                </td>
              </tr>`,
            )}
          </tbody>
        </table>
      </div>
      <div class="btn-row">
        <button class="btn sm ghost" type="button" onClick=${() => onRows([...list, table.columns.map(() => "")])}>${texts.table.addRow}</button>
        <button class="btn sm ghost" type="button" onClick=${() => picker.current.click()}>${texts.table.fromCsv}</button>
        <input ref=${picker} type="file" accept=".csv,.txt,text/csv,text/plain" hidden onChange=${onFile} />
        <span class="muted small">${t(texts.table.count, { rows: list.length })}</span>
      </div>
      ${note ? html`<p class=${note.error ? "err" : "note"} role=${note.error ? "alert" : "status"}>${note.text}</p>` : null}
      <${Problem} message=${error} id=${errorId} />
    </div>
  `;
}

/**
 * The structure of a node: its inflows and the node it flows into.
 *
 * @param {{node: object, to: string|null}} props the node and its downstream node
 * @returns {object} the head
 */
function NodeHead({ node, to }) {
  const parts = [html`<code>${node.type}</code>`];
  if (node.from && node.from.length) parts.push(html` · ${texts.form.from} <code>${node.from.join(" + ")}</code>`);
  if (to) parts.push(html` · ${texts.form.to} <code>${to}</code>`);
  return html`
    <p class="node-head"><i class=${`ng t-${node.type}`} aria-hidden="true"></i><code>${node.id}</code><span>${parts}</span></p>
    ${node.from && node.from.length
      ? html`<div class="field">
          <span class="label">${texts.form.inflows} <span class="key">from</span></span>
          <div class="chips">${node.from.map((id) => html`<span class="chip">${id}</span>`)}</div>
        </div>`
      : null}
  `;
}

/**
 * „Opis” of a node or of the network (D3): plain text with line breaks, checked as the
 * library checks it.
 *
 * @param {{id: string, label: string, value?: string, error?: string|null, onInput: (text:
 *   string) => void}} props the control's id, its label, the text, its problem and the
 *   handler
 * @returns {object} the field
 */
export function DescriptionField({ id, label, value, error, onInput }) {
  const message = error ? splitReason(error) : null;
  return html`<div class=${`opt${error ? " invalid" : ""}`} data-field="description">
    <label for=${id}><span class="lbl-text">${label}</span> <code>description</code></label>
    <textarea
      id=${id}
      rows="3"
      spellcheck=${true}
      value=${value || ""}
      aria-invalid=${error ? "true" : "false"}
      aria-describedby=${`${id}-hint${error ? ` ${id}-err` : ""}`}
      onInput=${(event) => onInput(event.currentTarget.value)}
    ></textarea>
    <span class="hint" id=${`${id}-hint`}>${texts.form.descriptionHint}</span>
    ${message
      ? html`<span class="err" id=${`${id}-err`} role="alert">${message.text}${message.reason ? html` <span class="reason">· ${message.reason}</span>` : null}</span>`
      : null}
  </div>`;
}

/**
 * The structure of a node as ordinary form controls (D7, D12: every structural edit of the
 * canvas is also here): the id, „Opis”, „Odpływa do” (refused targets disabled with their
 * reason; a node that takes one inflow and has it offers „Wstaw złącze”), „Usuń węzeł” and
 * „Usuń i połącz”.
 *
 * @param {{node: object, to: string|null, skeleton: object[], rules: object, prefix:
 *   string, offer: object|null, actions: object, onIdDone: (id: string) => void}} props
 *   the node, its downstream node, the structure, the inflow rules, the prefix of ids, a
 *   junction offered for it, the section's edits and the handler of Enter or Esc in the id
 * @returns {object} the controls
 */
function NodeStructure({ node, to, skeleton, rules, prefix, offer, actions, onIdDone }) {
  const [draft, setDraft] = useState(node.id);
  const reason = draft === node.id ? null : idProblem(draft, skeleton, node.id);
  const other = reason === "duplicate_node" ? (skeleton.find((item) => item.id !== node.id && foldId(item.id) === foldId(draft)) || {}).id : null;
  const idError = reason ? withReason(t(texts.idProblems[reason], { other: other || "–" }), reason) : null;
  const idMessage = idError ? splitReason(idError) : null;
  const commit = () => {
    if (draft !== node.id && !reason) actions.rename(node.id, draft);
  };
  const idId = `${prefix}-id`;
  const toId = `${prefix}-to`;
  // „Odpływa do”: the nodes below it and every target with its verdict, kept while the
  // structure stays (a move, a description or a value changes nothing here)
  const shape = useMemo(() => structureKey(skeleton), [skeleton]);
  const { below, targets } = useMemo(() => {
    const down = receiversOf(skeleton).get(node.id) || [];
    const verdicts = linkVerdicts(skeleton, rules, node.id);
    const listed = skeleton
      .filter((item) => item.id !== node.id)
      .map((item) => {
        const verdict = verdicts.get(item.id);
        const refused = !verdict.ok && !verdict.offer && !down.includes(item.id);
        const label = `${item.id} (${kindNoun(item.type)})`;
        const reason = refused ? refusalText(verdict, skeleton, node.id, item.id) : null;
        return { id: item.id, refused, text: refused ? `${label}: ${t(texts.canvas.refused, { reason })}` : label };
      });
    return { below: down, targets: listed };
  }, [shape, rules, node.id]);
  return html`
    <div class="node-structure" data-structure=${node.id}>
      <div class=${`opt${idError ? " invalid" : ""}`} data-field="id">
        <label for=${idId}><span class="lbl-text">${texts.form.id}</span> <code>id</code></label>
        <input
          id=${idId}
          type="text"
          autocomplete="off"
          spellcheck=${false}
          value=${draft}
          aria-invalid=${idError ? "true" : "false"}
          aria-describedby=${`${idId}-hint${idError ? ` ${idId}-err` : ""}`}
          onInput=${(event) => setDraft(event.currentTarget.value)}
          onChange=${commit}
          onKeyDown=${(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commit();
              onIdDone(reason || draft === node.id ? node.id : draft);
            } else if (event.key === "Escape") {
              event.preventDefault();
              setDraft(node.id);
              onIdDone(node.id);
            }
          }}
        />
        <span class="hint" id=${`${idId}-hint`}>${texts.form.idHint}</span>
        ${idMessage
          ? html`<span class="err" id=${`${idId}-err`} role="alert">${idMessage.text}${idMessage.reason ? html` <span class="reason">· ${idMessage.reason}</span>` : null}</span>`
          : null}
      </div>
      <${DescriptionField}
        id=${`${prefix}-description`}
        label=${texts.form.description}
        value=${node.description}
        error=${descriptionProblem(node.description)}
        onInput=${(text) => actions.describe(node.id, text)}
      />
      <div class="opt" data-field="to">
        <label for=${toId}><span class="lbl-text">${texts.form.to}</span></label>
        <select
          id=${toId}
          value=${to || ""}
          disabled=${node.type === "outlet"}
          aria-describedby=${`${toId}-hint`}
          onChange=${(event) => {
            const value = event.currentTarget.value;
            if (!value) actions.unlink(node.id, null);
            else actions.link(node.id, value, "data");
          }}
        >
          <option value="">${texts.form.toNone}</option>
          ${targets.map((item) => html`<option value=${item.id} disabled=${item.refused}>${item.text}</option>`)}
        </select>
        <span class="hint" id=${`${toId}-hint`}>${texts.form.toHint}</span>
      </div>
      ${offer
        ? html`<${JunctionOffer}
            offer=${offer}
            skeleton=${skeleton}
            onAccept=${() => actions.insertJunction(offer.from, offer.to)}
            onCancel=${() => actions.cancelOffer()}
          />`
        : null}
      <div class="btn-row">
        <button class="btn sm ghost" type="button" data-action="remove-node" title=${t(texts.form.removeTitle, { id: node.id })} onClick=${() => actions.remove(node.id, false)}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 6h10M8 6V4h4v2M6 6l1 11h6l1-11" /></svg>
          ${texts.form.remove}
        </button>
        ${canBridge(skeleton, node.id)
          ? html`<button
              class="btn sm ghost"
              type="button"
              data-action="bridge-node"
              title=${t(texts.form.bridgeTitle, { id: node.id, up: node.from[0], down: below[0] })}
              onClick=${() => actions.remove(node.id, true)}
            >
              ${texts.form.bridge}
            </button>`
          : null}
      </div>
    </div>
  `;
}

/**
 * The numbers of a routing element's fields by name, for the ranges of its explanation.
 *
 * @param {object} values the node's values
 * @param {string} method the method ("level-pool" for a reservoir)
 * @returns {Object<string, number>} the numbers given
 */
function methodNumbers(values, method) {
  const found = {};
  for (const [key, value] of Object.entries(values)) {
    if (!key.startsWith(`${method}.`) || typeof value !== "string") continue;
    const number = parseNumber(value);
    if (number !== null && Number.isFinite(number)) found[key.slice(method.length + 1)] = number;
  }
  return found;
}

/**
 * The method of a reach: a choice among the five, with its explanation (i).
 *
 * @param {{id: string, value: string, values: object, onInput: (method: string) => void}}
 *   props the control's id, the method, the node's values and the handler
 * @returns {object} the field
 */
function MethodField({ id, value, values, onInput }) {
  const field = fieldOf(
    "method",
    { type: "string", enum: [...METHODS] },
    true,
    { description: texts.method.hint, enum: Object.fromEntries(METHODS.map((method) => [method, texts.methods[method].meaning])) },
    texts.method.label,
  );
  return html`
    <div class="slot method-row" data-key="#method">
      <${ChoiceField} field=${field} id=${id} value=${value} required=${true} onInput=${onInput} />
      <${InfoButton} id=${`routing.${value}`} values=${methodNumbers(values, value)} />
    </div>
  `;
}

/**
 * The settings of one node.
 *
 * @param {{forms: object, node: object, to: string|null, skeleton: object[], values:
 *   object, problems: object, inflowsFile: string, offer: object|null, actions: object,
 *   onPanel: () => void, onIdDone: (id: string) => void, onChange: (values: object) =>
 *   void}} props the forms, the node's structure, its downstream node, the whole
 *   structure, its values and problems, the inflows file, a junction offered for it, the
 *   section's edits, what shows the panel of a subcatchment made from rainfall, the
 *   handler of Enter or Esc in the id and the change handler
 * @returns {object} the form
 */
export function NodeForm({ forms, node, to, skeleton, values, problems, inflowsFile, offer, actions, onPanel, onIdDone, onChange }) {
  const prefix = `nf-${String(node.id).replace(/[^\w-]+/g, "-")}`;
  const layout = nodeLayout(forms, node, values);
  const set = (key, value) => onChange({ ...values, [key]: value });
  const render = (slot) => html`<${FieldSlot} key=${slot.key} slot=${slot} values=${values} problems=${problems} prefix=${prefix} onValue=${set} />`;
  const parts = [
    html`<${NodeHead} node=${node} to=${to} />`,
    html`<${NodeStructure}
      node=${node}
      to=${to}
      skeleton=${skeleton}
      rules=${forms.inflow}
      prefix=${prefix}
      offer=${offer}
      actions=${actions}
      onIdDone=${onIdDone}
    />`,
  ];

  if (layout.kind === "subcatchment") {
    parts.push(html`<${Choice}
      id=${`${prefix}-variant`}
      name="#variant"
      title=${texts.form.variant}
      items=${VARIANTS.map((variant) => ({ value: variant, label: texts.variants[variant].label }))}
      value=${layout.variant}
      onChange=${(variant) => set("#variant", variant)}
    />`);
    if (layout.variant === "rain") {
      // Its data are Hydrogram's steps in its own panel (D1, D2); on a phone the panels
      // alternate, and this is the way there
      parts.push(html`<p class="note" data-note="panel">${texts.form.inPanel}</p>`);
      parts.push(html`<div class="btn-row">
        <button class="btn sm" type="button" data-action="open-panel" title=${t(texts.form.openPanelTitle, { id: node.id })} onClick=${onPanel}>
          ${texts.form.openPanel}
        </button>
      </div>`);
      parts.push(html`<${Problem} message=${problems.rain_source} id=${`${prefix}-rainfall-err`} />`);
    } else if (layout.variant === "file") {
      parts.push(layout.file.map(render));
      parts.push(
        inflowsFile
          ? html`<p class="note" data-note="inflows">${t(texts.form.fromFile, { file: inflowsFile.replace(/^in\//, ""), column: String(values.value_column || node.id) })}</p>`
          : html`<div class="form-errors" role="alert" data-note="inflows">${texts.form.noInflowsFile}</div>`,
      );
    } else {
      parts.push(html`<h4 class="sub-title">${texts.form.hydrograph}</h4>`);
      parts.push(html`<${TableEditor}
        table=${layout.table}
        rows=${values[layout.table.key]}
        onRows=${(rows) => set(layout.table.key, rows)}
        error=${problems[layout.table.key]}
        prefix=${prefix}
        label=${texts.form.hydrograph}
      />`);
    }
  } else if (layout.kind === "reach" || layout.kind === "reservoir") {
    if (layout.kind === "reach") {
      parts.push(html`<${MethodField} id=${`${prefix}-method`} value=${layout.method} values=${values} onInput=${(method) => set("#method", method)} />`);
    } else {
      parts.push(html`<div class="slot method-row" data-key="#method">
        <div class="opt">
          <span class="label-row">${texts.method.label} <code>route level-pool</code></span>
          <span class="meaning"><code>level-pool</code> ${texts.methods["level-pool"].meaning}</span>
        </div>
        <${InfoButton} id="routing.level-pool" values=${methodNumbers(values, "level-pool")} />
      </div>`);
    }
    parts.push(layout.main.map(render));
    if (layout.choice) {
      const words = texts.choices[layout.choice.id];
      parts.push(html`<${Choice}
        id=${`${prefix}-${layout.choice.id.slice(1)}`}
        name=${layout.choice.id}
        title=${words.title}
        items=${words.groups.map((label, index) => ({ value: index, label }))}
        value=${layout.choice.value}
        onChange=${(index) => set(layout.choice.key, index)}
      />`);
    }
    parts.push(layout.chosen.map(render));
    if (layout.table) {
      parts.push(html`<${TableEditor}
        table=${layout.table}
        rows=${values[layout.table.key]}
        onRows=${(rows) => set(layout.table.key, rows)}
        error=${problems[layout.table.key]}
        prefix=${prefix}
        label=${texts.choices["#table"].title}
      />`);
      parts.push(html`<p class="note">${texts.form.tableRules}</p>`);
    }
    parts.push(layout.after.map(render));
    parts.push(html`<${More} name="more" title=${texts.form.more} slots=${layout.more} problems=${problems} render=${render} />`);
    parts.push(html`<${More} name="wave" title=${texts.form.wave} slots=${layout.wave} problems=${problems} render=${render} />`);
  } else if (layout.kind === "junction") {
    parts.push(html`<p class="note">${texts.form.junction}</p>`);
  } else if (layout.kind === "outlet") {
    parts.push(html`<p class="note">${texts.form.outlet}</p>`);
  }
  return html`<div class="node-form" data-node-form=${node.id} data-kind=${layout.kind}>${parts}</div>`;
}
