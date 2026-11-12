// The hand-off in the sections (plan D15, standalone; through Nogat's shell once it
// exists, D4). „Wczytaj z Hydrografa” (HandoffImport, beside a section's own file
// button) reads a hand-off from a file or the clipboard and opens it where it belongs: one
// subcatchment in „Hydrogram zlewni” (deliver → useHandoffInbox, which the section
// listens with), a network in „Sieć i trasowanie” (its openNetwork); read in Sieć, every
// network opens there, and „Dodaj zlewnię z Hydrografa” (HandoffAdd) adds a hand-off's
// subcatchments to the open network (plan 2026-11-10-network-editor, D10). Given a caller
// (`onOpen`), it hands the checked hand-off of one watershed to it instead: Sieć's
// subcatchment panel fills its node (plan 2026-11-10-network-wizard, D10). The part
// „Przekazanie” of the panel Wyniki (HydrogramHandoff, SiecHandoff) writes one („Plik
// przekazania”, „Kopiuj do Hydrologa”) and shows a received producer's result beside
// Hydrolog's own, with the versions that computed them. The file, the clipboard and the
// download are Nogat's kit (nogat-handoff.js, DEV-15.5, ADR-0027): the file is named after
// the subject, and a copy the browser refuses goes selected into a field for Ctrl+C.
// Nothing here runs or writes at mount.

import { copyHandoff, downloadHandoff, readClipboard, readFile } from "../../nogat/nogat-handoff.js";
import { api } from "../api.js";
import { plural } from "../format.js";
import { html, useEffect, useRef, useState } from "../html.js";
import { common, t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { siec as siecTexts } from "../labels/siec.js";
import { navigate } from "../router.js";
import { fieldLabel, handoffMissing } from "../sections/hydrogram/state.js";
import { withoutPicture } from "../sections/siec/node-model.js";
import { fileStem, openNetwork, withSessionNames } from "../sections/siec/state.js";
import { fileBase } from "../ui/export-panel.js";
import { MenuButton } from "../ui/menu.js";
import { toast } from "../ui/toast.js";
import { uploadFile } from "../controls/file-field.js";
import {
  MARKS,
  NETWORK_SCHEMA_FILE,
  SERIES_SCHEMA_FILE,
  compareResults,
  engineOf,
  momentText,
  readHandoff,
  receivedOf,
  statystykaInputs,
  toolName,
} from "./handoff.js";
import {
  dataKey,
  hydrogramContents,
  hydrogramHandoff,
  hydrogramInputs,
  hydrogramResult,
  outletResult,
  siecHandoff,
  siecReceived,
  unknownOriginsNote,
} from "./mapping.js";
import { canonical, isObject } from "./validate.js";

/** The most problems of a refused hand-off listed. */
export const MAX_PROBLEMS = 8;

const ICONS = {
  load: html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 14V4M6 8l4-4 4 4M4 16h12" /></svg>`,
  add: html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12" /></svg>`,
  save: html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v10M6 9l4 4 4-4M4 16h12" /></svg>`,
  copy: html`<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" /><path d="M13 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" /></svg>`,
  file: html`<svg class="file-ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 3h7l3 3v11H5z" /><path d="M12 3v3h3" /></svg>`,
  ok: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M5 8.2l2 2 4-4.2" /></svg>`,
  warn: html`<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2l6.5 11.5h-13z" /><path d="M8 6.5v3.2M8 11.7v.01" /></svg>`,
  info: html`<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>`,
};

// --- delivery to a section ---------------------------------------------------------

const pending = new Map();
const receivers = new Map();

/**
 * Hand a value to a section and show it: its useHandoffInbox takes it now, or when it
 * mounts.
 *
 * @param {string} target the section's id ("hydrogram")
 * @param {unknown} value what the section takes (Hydrogram: a patch of its inputs)
 */
export function deliver(target, value) {
  pending.set(target, value);
  for (const listener of [...(receivers.get(target) || [])]) listener();
  navigate(target);
}

/**
 * Take the values delivered to a section.
 *
 * @param {string} target the section's id
 * @param {(value: unknown) => void} onValue the handler
 */
export function useHandoffInbox(target, onValue) {
  const latest = useRef(onValue);
  latest.current = onValue;
  useEffect(() => {
    const listener = () => {
      if (!pending.has(target)) return;
      const value = pending.get(target);
      pending.delete(target);
      latest.current(value);
    };
    let listeners = receivers.get(target);
    if (!listeners) {
      listeners = new Set();
      receivers.set(target, listeners);
    }
    listeners.add(listener);
    listener();
    return () => listeners.delete(listener);
  }, [target]);
}

// --- reading -------------------------------------------------------------------------

/**
 * A text of an error for people.
 *
 * @param {unknown} error an ApiError or anything thrown
 * @returns {string} the text
 */
function errorText(error) {
  return error && error.doc ? describeError(error.doc).text : String((error && error.message) || error);
}

/**
 * The schemas a hand-off's payload is checked against: hydrolog-network-1.schema.json and
 * hydrolog-series-1.schema.json.
 *
 * @param {string} refused the title of a refusal
 * @returns {Promise<{schemas: {networkSchema: object, seriesSchema: object}|null, refusal:
 *   {title: string, lines: string[]}|null}>} the schemas, or why they are missing
 */
async function payloadSchemas(refused) {
  try {
    const [networkSchema, seriesSchema] = await Promise.all([api.schema(NETWORK_SCHEMA_FILE), api.schema(SERIES_SCHEMA_FILE)]);
    return { schemas: { networkSchema, seriesSchema }, refusal: null };
  } catch (error) {
    return { schemas: null, refusal: { title: refused, lines: [t(texts.load.schemaFailed, { message: errorText(error) })] } };
  }
}

/**
 * Open a hand-off: check it (the envelope against Nogat's schema, the payload against
 * hydrolog-network-1.schema.json or hydrolog-series-1.schema.json) and hand it to the
 * section it belongs to, or to Sieć for every network when Sieć reads it (`into`). A
 * station's daily series is first written into the session's files, which Statystyka
 * przepływów reads like a file of the person's. A network takes the origins of its nodes
 * (node_provenance) to Sieć, and a key that names no node is said in the load's note.
 *
 * @param {string} text the hand-off as text
 * @param {{into?: "siec"|null}} [options] the section that reads it (readHandoff)
 * @returns {Promise<{title: string, lines: string[]}|null>} why it was refused, null when
 *   it opened
 */
export async function openHandoff(text, { into = null } = {}) {
  const found = await payloadSchemas(texts.load.refused);
  if (found.refusal) return found.refusal;
  const read = readHandoff(text, { ...found.schemas, into });
  if (read.problems.length) return { title: texts.load.refused, lines: read.problems };
  const doc = read.doc;
  const producer = `${toolName(doc.producer.tool)} ${doc.producer.version}`;
  if (read.target === "hydrogram") {
    deliver("hydrogram", hydrogramInputs(doc));
    toast(t(texts.load.opened, { subject: doc.subject, producer }));
  } else if (read.target === "statystyka") {
    const inputs = statystykaInputs(doc.payload);
    const values = { input_file: "", value_column: undefined, date_column: undefined, values: "", ...inputs.values };
    if (inputs.csv !== null) {
      try {
        const file = new File([inputs.csv], `${fileBase(doc.subject)}.csv`, { type: "text/csv" });
        values.input_file = (await uploadFile(file)).path;
      } catch (error) {
        return { title: texts.load.refused, lines: [t(texts.load.uploadFailed, { message: errorText(error) })] };
      }
    }
    deliver("statystyka", { source: inputs.source, values, received: receivedOf(doc) });
    const count = doc.payload.values.filter((value) => typeof value === "number").length;
    toast(t(texts.load.openedStatystyka, { subject: doc.subject, producer, values: plural(count, texts.valueForms) }));
  } else {
    const named = withSessionNames(doc.payload);
    openNetwork(named.doc, {
      name: `${fileBase(doc.subject)}.json`,
      kind: "handoff",
      handoff: siecReceived(doc, named.doc),
      notes: unknownOriginsNote(doc),
    });
    toast(t(texts.load.openedSiec, { subject: doc.subject, producer, nodes: plural(named.doc.nodes.length, siecTexts.nodeForms) }));
  }
  return null;
}

/**
 * „Dodaj zlewnię z Hydrografa” (plan 2026-11-10-network-editor, D10): check a hand-off as
 * openHandoff does and give its document to Sieć, which adds its subcatchments to the
 * open network; a station's series is refused.
 *
 * @param {string} text the hand-off as text
 * @param {(doc: object) => ({title: string, lines: string[]}|null)} onAdd Sieć's
 *   addition: null when it added them, else why not
 * @returns {Promise<{title: string, lines: string[]}|null>} why nothing was added, null
 *   when the subcatchments were
 */
export async function addHandoff(text, onAdd) {
  const found = await payloadSchemas(texts.add.refused);
  if (found.refusal) return found.refusal;
  const read = readHandoff(text, { ...found.schemas, into: "siec" });
  if (read.problems.length) return { title: texts.add.refused, lines: read.problems };
  if (read.target !== "siec") return { title: texts.add.refused, lines: [texts.add.series] };
  return onAdd(read.doc);
}

/**
 * „Wczytaj z Hydrografa” for a caller that takes one watershed (plan
 * 2026-11-10-network-wizard, D10: a subcatchment's panel in Sieć): check a hand-off as
 * openHandoff does and hand the document of one subcatchment to `onOpen`; a network is
 * refused with the two ways to take it, a station's series as what it is.
 *
 * @param {string} text the hand-off as text
 * @param {(doc: object) => ({title: string, lines: string[]}|null)} onOpen the caller's
 *   reading: null when it took the watershed, else why not
 * @returns {Promise<{title: string, lines: string[]}|null>} why it was refused, null when
 *   the caller took it
 */
export async function handoffFor(text, onOpen) {
  const found = await payloadSchemas(texts.fill.refused);
  if (found.refusal) return found.refusal;
  const read = readHandoff(text, found.schemas);
  if (read.problems.length) return { title: texts.fill.refused, lines: read.problems };
  if (read.target === "statystyka") return { title: texts.fill.refused, lines: [texts.fill.series] };
  if (read.target !== "hydrogram") {
    const nodes = Array.isArray(read.doc.payload.nodes) ? read.doc.payload.nodes.length : 0;
    return { title: texts.fill.refused, lines: [t(texts.fill.network, { nodes: plural(nodes, siecTexts.nodeForms) })] };
  }
  return onOpen(read.doc);
}

/**
 * The lines of a refusal, at most MAX_PROBLEMS and how many more.
 *
 * @param {string[]} lines the problems
 * @returns {string[]} the lines shown
 */
function capped(lines) {
  if (lines.length <= MAX_PROBLEMS) return lines;
  return [...lines.slice(0, MAX_PROBLEMS), t(texts.load.more, { count: lines.length - MAX_PROBLEMS })];
}

/**
 * A button that reads a hand-off: a menu of a hand-off file and the clipboard; where the
 * browser does not give the clipboard, a field to paste into. A refused hand-off lists why
 * below the buttons. Placed in a section's row of file buttons (`.btn-row`).
 *
 * @param {{name: string, words: object, icon: object, read: (text: string) =>
 *   Promise<{title: string, lines: string[]}|null>}} props the reader's name (its
 *   feedback's `data-handoff-reader`), its texts (labels/handoff.js `load` and what
 *   replaces them), the button's icon and what reading does: null when it was done, else
 *   why not
 * @returns {object} the button, its menu and what it says
 */
function HandoffReader({ name, words, icon, read }) {
  const [feedback, setFeedback] = useState(null);
  const area = useRef(null);
  const open = async (text) => {
    setFeedback({ kind: "busy" });
    const refusal = await read(text);
    setFeedback(refusal ? { kind: "problems", ...refusal } : null);
  };
  useEffect(() => {
    if (feedback && feedback.kind === "paste" && area.current) area.current.focus();
  }, [feedback && feedback.kind]);
  const pickFile = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json,application/json";
    input.hidden = true;
    input.dataset.handoffFile = "";
    const done = () => input.remove();
    input.addEventListener("cancel", done, { once: true });
    input.addEventListener(
      "change",
      async () => {
        const file = input.files && input.files[0];
        done();
        if (!file) return;
        let text;
        try {
          text = await readFile(file);
        } catch (error) {
          setFeedback({ kind: "problems", title: words.refused, lines: [t(texts.load.readFailed, { name: file.name, message: errorText(error) })] });
          return;
        }
        await open(text);
      },
      { once: true },
    );
    document.body.append(input);
    input.click();
  };
  const paste = async () => {
    const text = await readClipboard();
    if (text === null) {
      setFeedback({ kind: "paste" });
      return;
    }
    if (!text.trim()) {
      setFeedback({ kind: "problems", title: words.refused, lines: [texts.load.empty] });
      return;
    }
    await open(text);
  };
  let shown = null;
  if (feedback && feedback.kind === "problems") {
    shown = html`<div class="form-errors handoff-feedback" role="alert" data-handoff-problems="" data-handoff-reader=${name}>
      <strong>${feedback.title}</strong>
      <ul>${capped(feedback.lines).map((line) => html`<li>${line}</li>`)}</ul>
      <button class="link-btn" type="button" onClick=${() => setFeedback(null)}>${common.actions.close}</button>
    </div>`;
  } else if (feedback && feedback.kind === "paste") {
    shown = html`<div class="handoff-feedback" data-handoff-paste="" data-handoff-reader=${name}>
      <p class="note">${words.pasteHint}</p>
      <textarea
        ref=${area}
        rows="4"
        aria-label=${texts.load.pasteLabel}
        spellcheck="false"
        onPaste=${(event) => {
          const text = event.clipboardData ? event.clipboardData.getData("text") : "";
          if (text) {
            event.preventDefault();
            open(text);
          }
        }}
      ></textarea>
      <div class="btn-row">
        <button class="btn sm" type="button" onClick=${() => open(area.current ? area.current.value : "")}>${texts.load.pasteOpen}</button>
        <button class="btn sm ghost" type="button" onClick=${() => setFeedback(null)}>${texts.load.pasteCancel}</button>
      </div>
    </div>`;
  } else if (feedback && feedback.kind === "busy") {
    shown = html`<p class="note handoff-feedback" role="status" data-handoff-reader=${name}>${texts.load.reading}</p>`;
  }
  return html`
    <${MenuButton}
      className="btn sm"
      title=${words.title}
      menuLabel=${words.menu}
      label=${html`${icon}${words.button}`}
      items=${[
        { label: words.file, sub: words.fileSub, onSelect: pickFile },
        { label: words.paste, sub: words.pasteSub, onSelect: paste },
      ]}
    />
    ${shown}
  `;
}

/**
 * „Wczytaj z Hydrografa”: a hand-off read from a file or the clipboard opens where it
 * belongs (openHandoff). Statystyka przepływów names Archiwista instead (`series`); Sieć
 * opens every network itself (`into`, plan 2026-11-10-network-editor, D10); a caller that
 * takes one watershed gets it (`onOpen`, handoffFor; plan 2026-11-10-network-wizard, D10).
 *
 * @param {{series?: boolean, into?: "siec"|null, onOpen?: ((doc: object) => ({title:
 *   string, lines: string[]}|null))|null}} [props] the texts of a station's series
 *   (Archiwista), the section that reads it, and the caller of one watershed
 * @returns {object} the button, its menu and what it says
 */
export function HandoffImport({ series = false, into = null, onOpen = null } = {}) {
  if (onOpen) {
    return html`<${HandoffReader} name="fill" words=${{ ...texts.load, ...texts.fill }} icon=${ICONS.load} read=${(text) => handoffFor(text, onOpen)} />`;
  }
  let words = texts.load;
  if (series) words = { ...texts.load, ...texts.loadSeries };
  else if (into === "siec") words = { ...texts.load, ...texts.loadSiec };
  return html`<${HandoffReader} name="load" words=${words} icon=${ICONS.load} read=${(text) => openHandoff(text, { into })} />`;
}

/**
 * „Dodaj zlewnię z Hydrografa” in Sieć (plan 2026-11-10-network-editor, D10): a hand-off
 * read from a file or the clipboard gives its subcatchments to the open network
 * (addHandoff).
 *
 * @param {{onAdd: (doc: object) => ({title: string, lines: string[]}|null)}} props Sieć's
 *   addition: null when it added them, else why not
 * @returns {object} the button, its menu and what it says
 */
export function HandoffAdd({ onAdd }) {
  return html`<${HandoffReader} name="add" words=${{ ...texts.load, ...texts.add }} icon=${ICONS.add} read=${(text) => addHandoff(text, onAdd)} />`;
}

// --- a received producer's result ----------------------------------------------------

/**
 * The mark of a tool, or a file's icon for a tool the page has no mark of.
 *
 * @param {{tool: string}} props the tool
 * @returns {object} the image
 */
function Mark({ tool }) {
  return MARKS.includes(tool) ? html`<img src=${`nogat/marks/${tool}.svg`} alt="" />` : ICONS.file;
}

/**
 * Who handed the data off and when.
 *
 * @param {{received: object, small?: boolean}} props the record of the hand-off
 * @returns {object} the card
 */
export function HandoffOrigin({ received, small = false }) {
  const tool = received.producer.tool;
  return html`
    <div class=${small ? "handoff sm" : "handoff"} data-handoff-source=${tool}>
      <${Mark} tool=${tool} />
      <div>
        <strong>${t(texts.origin.title, { producer: toolName(tool, true), subject: received.subject })}</strong>
        <span class="muted">${t(texts.origin.received, { producer: toolName(tool), version: received.producer.version, time: momentText(received.created_at) })}</span>
      </div>
    </div>
  `;
}

/**
 * Where an input of a node came from (plan 2026-11-10-network-wizard, D9): a card of
 * mapping.js (originCard), in a node's panel or in „Dane”.
 *
 * @param {{card: {tool: string, title: string, detail: string}, input: string}} props the
 *   card and the input it tells (`watershed`, `runoff`, `rainfall`, `node`)
 * @returns {object} the card
 */
export function OriginCard({ card, input }) {
  return html`
    <div class="handoff sm" data-handoff-source=${card.tool} data-origin-input=${input}>
      <${Mark} tool=${card.tool} />
      <div>
        <strong>${card.title}</strong>
        <span class="muted">${card.detail}</span>
      </div>
    </div>
  `;
}

/**
 * The producer's result beside Hydrolog's own: the versions that computed them and each
 * quantity, a differing one marked, and what the comparison means.
 *
 * @param {{received: object, own: object|null, ownVersion: string|null, state:
 *   "same"|"changed"|"none"|"stale"}} props the record of the hand-off, Hydrolog's result
 *   in the D15 names, its version, and whether that result is of the received data
 *   ("same"), of changed data, missing or of an earlier state of the data
 * @returns {object} the comparison
 */
export function ReceivedResult({ received, own, ownVersion, state }) {
  const engine = engineOf(received);
  const comparable = state === "same" && own;
  const comparison = received.result ? compareResults(received.result, comparable ? own : null) : null;
  const engineText = t(texts.received.engine, { tool: toolName(engine.tool), version: engine.version });
  const versionDiffers = !(engine.tool === "hydrolog" && engine.version === ownVersion);
  let verdict;
  if (!comparison) verdict = { level: "info", text: texts.received.noResult };
  else if (state === "changed") verdict = { level: "info", text: texts.received.changed };
  else if (state === "stale") verdict = { level: "info", text: texts.received.stale };
  else if (!comparable) verdict = { level: "info", text: texts.received.noOwn };
  else if (!comparison.differs) verdict = { level: "ok", text: texts.received.same };
  else if (!versionDiffers) verdict = { level: "warn", text: texts.received.differSame };
  else verdict = { level: "warn", text: t(texts.received.differVersion, { engine: engineText, version: ownVersion }) };
  return html`
    <div class="handoff-received" data-handoff-received=${state}>
      <${HandoffOrigin} received=${received} />
      ${comparison
        ? html`<div class="table-wrap">
            <table class="dtable" data-table="handoff-compare">
              <thead>
                <tr>
                  <th scope="col" class="txt">${texts.received.quantity}</th>
                  <th scope="col">${texts.received.producer}</th>
                  <th scope="col">${texts.received.own}</th>
                </tr>
              </thead>
              <tbody>
                <tr data-row="version" class=${versionDiffers ? "conflict" : undefined}>
                  <th scope="row">${texts.received.version}</th>
                  <td>${engineText}</td>
                  <td>${ownVersion ? t(texts.received.engine, { tool: toolName("hydrolog"), version: ownVersion }) : common.empty}</td>
                </tr>
                ${comparison.rows.map(
                  (row) => html`<tr data-row=${row.key} class=${row.differs ? "conflict" : undefined}>
                    <th scope="row">${texts.received.rows[row.key]}</th>
                    <td>${row.producer} ${row.unit}</td>
                    <td>${row.own === null ? common.empty : `${row.own} ${row.unit}`}</td>
                  </tr>`,
                )}
              </tbody>
            </table>
          </div>`
        : null}
      <ul class="notes" data-handoff-verdict=${verdict.level}>
        <li class=${verdict.level}>${ICONS[verdict.level]}<div>${verdict.text}</div></li>
      </ul>
    </div>
  `;
}

// --- writing -------------------------------------------------------------------------

/**
 * „Plik przekazania” and „Kopiuj do Hydrologa” for a hand-off made on demand, through
 * Nogat's kit: the file `<subject>.handoff.json`, and the clipboard, or where the browser
 * gives none or refuses, the text selected in a field below the buttons for Ctrl+C.
 *
 * @param {{make: (() => object)|null, section: string, disabled?: string}} props the maker
 *   of the document (null while it cannot be made), the section, and why the buttons are
 *   off
 * @returns {object} the buttons and the field of a copy by hand
 */
function ExportHandoff({ make, section, disabled }) {
  const off = disabled || !make;
  const field = useRef(null);
  const [byHand, setByHand] = useState(false);
  const made = () => {
    try {
      return make();
    } catch (error) {
      toast(t(texts.export.failed, { message: errorText(error) }), "bad");
      return null;
    }
  };
  const save = () => {
    const doc = made();
    if (doc) toast(texts.export.saved(downloadHandoff(doc)));
  };
  const copy = async () => {
    const doc = made();
    if (!doc) return;
    if ((await copyHandoff(doc, field.current)) === "field") {
      setByHand(true);
      return;
    }
    field.current.hidden = true;
    setByHand(false);
    toast(texts.export.copied);
  };
  const done = () => {
    field.current.hidden = true;
    setByHand(false);
  };
  // The kit shows the field (`hidden` off) before it selects the text, so the field is
  // never inside a hidden box; Preact leaves `hidden` alone after the first render.
  return html`
    <div class="btn-row" data-handoff-export=${section}>
      <button class="btn" type="button" data-handoff="file" title=${off ? disabled : texts.export.fileTitle} disabled=${Boolean(off)} onClick=${save}>
        ${ICONS.save}${texts.export.file}
      </button>
      <button class="btn" type="button" data-handoff="copy" title=${off ? disabled : texts.export.copyTitle} disabled=${Boolean(off)} onClick=${copy}>
        ${ICONS.copy}${texts.export.copy}
      </button>
    </div>
    <div class="handoff-feedback" data-handoff-by-hand=${byHand ? "shown" : "none"}>
      ${byHand ? html`<p class="note" role="status">${texts.export.copyByHand}</p>` : null}
      <textarea ref=${field} rows="4" hidden aria-label=${texts.export.copyLabel} spellcheck="false"></textarea>
      ${byHand
        ? html`<div class="btn-row"><button class="btn sm ghost" type="button" onClick=${done}>${common.actions.close}</button></div>`
        : null}
    </div>
  `;
}

/**
 * The part „Przekazanie” of Hydrogram zlewni: a received producer's result beside the
 * shown one, and the hand-off of the shown run, offered once the run's watershed is the
 * full one a hand-off carries (HANDOFF_FIELDS; the model may need fewer fields).
 *
 * @param {{run: object, current: object|null, subject: string, rain: string}} props the
 *   shown run ({inputs, options, envelope}), the section's current inputs (their origin and
 *   received hand-off while their data are the run's), the subject of the exports and the
 *   rainfall in words
 * @returns {object} the part's body
 */
export function HydrogramHandoff({ run, current, subject, rain }) {
  const runKey = dataKey(run.inputs);
  const inputs = current && dataKey(current) === runKey ? current : run.inputs;
  const received = current && isObject(current.handoff) ? current.handoff : null;
  const missing = handoffMissing(run.options.watershed);
  const incomplete = missing.length
    ? t(texts.export.incomplete, { fields: missing.map((name) => `„${fieldLabel(name)}”`).join(", ") })
    : null;
  return html`
    ${received
      ? html`<${ReceivedResult}
          received=${received}
          own=${hydrogramResult(run.envelope.result)}
          ownVersion=${run.envelope.version}
          state=${received.key === runKey ? "same" : "changed"}
        />`
      : null}
    <${ExportHandoff}
      make=${() => hydrogramHandoff({ run, inputs, subject })}
      section="hydrogram"
      disabled=${incomplete || undefined}
    />
    ${incomplete ? html`<p class="note warn-note" data-handoff-incomplete="">${incomplete}</p>` : null}
    <p class="note">${texts.export.standalone}</p>
    <p class="note" data-handoff-contents="">${hydrogramContents(inputs, rain)}</p>
  `;
}

/**
 * The version of Hydrolog from the catalog's document of a command (fetched once by the
 * page anyway).
 *
 * @param {string} command the command
 * @returns {string|null} the version, null until it arrives
 */
function useCatalogVersion(command) {
  const [version, setVersion] = useState(null);
  useEffect(() => {
    let alive = true;
    api
      .command(command)
      .then((doc) => alive && setVersion(typeof doc.version === "string" ? doc.version : null))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [command]);
  return version;
}

/**
 * The part „Przekazanie” of Sieć: a received producer's result beside the outlet's, and
 * the hand-off of the network (with the outlet's result when the last run is of it).
 *
 * @param {{state: object, document: object|null, valid: boolean, run: object|null,
 *   stale: boolean}} props the section's state, the network's document and whether it is
 *   complete, the last run and whether the data changed since
 * @returns {object} the part
 */
export function SiecHandoff({ state, document, valid, run, stale }) {
  const catalogVersion = useCatalogVersion("route network");
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const fresh = Boolean(result) && !stale;
  const version = (run && run.envelope.version) || catalogVersion;
  const subject = String((document && document.name) || "").trim() || fileStem(state);
  const received = state.source && isObject(state.source.handoff) ? state.source.handoff : null;
  let compared = "same";
  if (received && (!document || received.key !== canonical(withoutPicture(document)))) compared = "changed";
  else if (!result) compared = "none";
  else if (stale) compared = "stale";
  const ready = Boolean(document) && valid && Boolean(version);
  const nodes = document && Array.isArray(document.nodes) ? plural(document.nodes.length, siecTexts.nodeForms) : "";
  return html`
    <div class="handoff-part" data-handoff-part="siec">
      ${received
        ? html`<${ReceivedResult} received=${received} own=${fresh ? outletResult(result) : null} ownVersion=${version} state=${compared} />`
        : null}
      <${ExportHandoff}
        make=${ready ? () => siecHandoff({ subject, state, document, result: fresh ? result : null, version }) : null}
        section="siec"
        disabled=${ready ? undefined : texts.export.invalid}
      />
      <p class="note">${texts.export.standalone}</p>
      ${document ? html`<p class="note" data-handoff-contents="">${t(fresh ? texts.export.siec : texts.export.siecNoResult, { nodes })}</p>` : null}
    </div>
  `;
}
