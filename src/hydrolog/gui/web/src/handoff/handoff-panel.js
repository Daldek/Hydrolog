// The hand-off in the sections (plan D15, standalone; through Nogat's shell once it
// exists, D4). „Wczytaj z Hydrografa” (HandoffImport, beside a section's own file
// button) reads a hand-off from a file or the clipboard and opens it where it belongs: one
// subcatchment in „Hydrogram zlewni” (deliver → useHandoffInbox, which the section
// listens with), a network in „Sieć i trasowanie” (its openNetwork). The part
// „Przekazanie” of the panel Wyniki (HydrogramHandoff, SiecHandoff) writes one („Plik
// przekazania”, „Do schowka”) and shows a received producer's result beside Hydrolog's
// own, with the versions that computed them. Nothing here runs or writes at mount.

import { api } from "../api.js";
import { plural } from "../format.js";
import { html, useEffect, useRef, useState } from "../html.js";
import { common, t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { handoffLabels as texts } from "../labels/handoff.js";
import { siec as siecTexts } from "../labels/siec.js";
import { navigate } from "../router.js";
import { fileStem, openNetwork, withSessionNames } from "../sections/siec/state.js";
import { copyText, downloadBlob, fileBase } from "../ui/export-panel.js";
import { MenuButton } from "../ui/menu.js";
import { toast } from "../ui/toast.js";
import { MARKS, NETWORK_SCHEMA_FILE, compareResults, engineOf, handoffFileName, momentText, readHandoff, toolName } from "./handoff.js";
import { dataKey, hydrogramContents, hydrogramHandoff, hydrogramInputs, hydrogramResult, outletResult, siecHandoff, siecReceived } from "./mapping.js";
import { canonical, isObject } from "./validate.js";

/** The most problems of a refused hand-off listed. */
export const MAX_PROBLEMS = 8;

const ICONS = {
  load: html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 14V4M6 8l4-4 4 4M4 16h12" /></svg>`,
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
 * Open a hand-off: check it (the envelope against Nogat's schema, the payload against
 * hydrolog-network-1.schema.json) and hand it to the section it belongs to.
 *
 * @param {string} text the hand-off as text
 * @returns {Promise<{title: string, lines: string[]}|null>} why it was refused, null when
 *   it opened
 */
export async function openHandoff(text) {
  let networkSchema;
  try {
    networkSchema = await api.schema(NETWORK_SCHEMA_FILE);
  } catch (error) {
    return { title: texts.load.refused, lines: [t(texts.load.schemaFailed, { message: errorText(error) })] };
  }
  const read = readHandoff(text, { networkSchema });
  if (read.problems.length) return { title: texts.load.refused, lines: read.problems };
  const doc = read.doc;
  const producer = `${toolName(doc.producer.tool)} ${doc.producer.version}`;
  if (read.target === "hydrogram") {
    deliver("hydrogram", hydrogramInputs(doc));
    toast(t(texts.load.opened, { subject: doc.subject, producer }));
  } else {
    const named = withSessionNames(doc.payload);
    openNetwork(named.doc, { name: `${fileBase(doc.subject)}.json`, kind: "handoff", handoff: siecReceived(doc, named.doc) });
    toast(t(texts.load.openedSiec, { subject: doc.subject, producer, nodes: plural(named.doc.nodes.length, siecTexts.nodeForms) }));
  }
  return null;
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
 * „Wczytaj z Hydrografa”: a menu of a hand-off file and the clipboard; where the browser
 * does not give the clipboard, a field to paste into. A refused hand-off lists why below
 * the buttons. Placed in a section's row of file buttons (`.btn-row`).
 *
 * @returns {object} the button, its menu and what it says
 */
export function HandoffImport() {
  const [feedback, setFeedback] = useState(null);
  const area = useRef(null);
  const open = async (text) => {
    setFeedback({ kind: "busy" });
    const refusal = await openHandoff(text);
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
          text = await file.text();
        } catch (error) {
          setFeedback({ kind: "problems", title: texts.load.refused, lines: [t(texts.load.readFailed, { name: file.name, message: errorText(error) })] });
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
    let text = null;
    try {
      if (navigator.clipboard && typeof navigator.clipboard.readText === "function") text = await navigator.clipboard.readText();
    } catch {
      text = null;
    }
    if (text === null) {
      setFeedback({ kind: "paste" });
      return;
    }
    if (!text.trim()) {
      setFeedback({ kind: "problems", title: texts.load.refused, lines: [texts.load.empty] });
      return;
    }
    await open(text);
  };
  let shown = null;
  if (feedback && feedback.kind === "problems") {
    shown = html`<div class="form-errors handoff-feedback" role="alert" data-handoff-problems="">
      <strong>${feedback.title}</strong>
      <ul>${capped(feedback.lines).map((line) => html`<li>${line}</li>`)}</ul>
      <button class="link-btn" type="button" onClick=${() => setFeedback(null)}>${common.actions.close}</button>
    </div>`;
  } else if (feedback && feedback.kind === "paste") {
    shown = html`<div class="handoff-feedback" data-handoff-paste="">
      <p class="note">${texts.load.pasteHint}</p>
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
    shown = html`<p class="note handoff-feedback" role="status">${texts.load.reading}</p>`;
  }
  return html`
    <${MenuButton}
      className="btn sm"
      title=${texts.load.title}
      menuLabel=${texts.load.menu}
      label=${html`${ICONS.load}${texts.load.button}`}
      items=${[
        { label: texts.load.file, sub: texts.load.fileSub, onSelect: pickFile },
        { label: texts.load.paste, sub: texts.load.pasteSub, onSelect: paste },
      ]}
    />
    ${shown}
  `;
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
 * „Plik przekazania” and „Do schowka” for a hand-off made on demand.
 *
 * @param {{make: (() => object)|null, base: string, section: string, disabled?: string}}
 *   props the maker of the document (null while it cannot be made), the base of the file
 *   name, the section, and why the buttons are off
 * @returns {object} the buttons
 */
function ExportHandoff({ make, base, section, disabled }) {
  const off = disabled || !make;
  const text = () => `${JSON.stringify(make(), null, 2)}\n`;
  const save = () => {
    try {
      const name = handoffFileName(base);
      downloadBlob(new Blob([text()], { type: "application/json" }), name);
      toast(t(texts.export.saved, { name }));
    } catch (error) {
      toast(t(texts.export.failed, { message: errorText(error) }), "bad");
    }
  };
  const copy = () => {
    let written;
    try {
      written = text();
    } catch (error) {
      toast(t(texts.export.failed, { message: errorText(error) }), "bad");
      return;
    }
    copyText(written).then(
      () => toast(texts.export.copied),
      () => toast(common.copyFailed, "bad"),
    );
  };
  return html`
    <div class="btn-row" data-handoff-export=${section}>
      <button class="btn" type="button" data-handoff="file" title=${off ? disabled : texts.export.fileTitle} disabled=${Boolean(off)} onClick=${save}>
        ${ICONS.save}${texts.export.file}
      </button>
      <button class="btn" type="button" data-handoff="copy" title=${off ? disabled : texts.export.copyTitle} disabled=${Boolean(off)} onClick=${copy}>
        ${ICONS.copy}${texts.export.copy}
      </button>
    </div>
  `;
}

/**
 * The part „Przekazanie” of Hydrogram zlewni: a received producer's result beside the
 * shown one, and the hand-off of the shown run.
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
  return html`
    ${received
      ? html`<${ReceivedResult}
          received=${received}
          own=${hydrogramResult(run.envelope.result)}
          ownVersion=${run.envelope.version}
          state=${received.key === runKey ? "same" : "changed"}
        />`
      : null}
    <${ExportHandoff} make=${() => hydrogramHandoff({ run, inputs, subject })} base=${fileBase(subject)} section="hydrogram" />
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
  if (received && (!document || received.key !== canonical(document))) compared = "changed";
  else if (!result) compared = "none";
  else if (stale) compared = "stale";
  const ready = Boolean(document) && valid && Boolean(version);
  const nodes = document && Array.isArray(document.nodes) ? plural(document.nodes.length, siecTexts.nodeForms) : "";
  return html`
    <div class="handoff-part" data-handoff-part="siec">
      <h3 class="group-title">${texts.export.title}</h3>
      ${received
        ? html`<${ReceivedResult} received=${received} own=${fresh ? outletResult(result) : null} ownVersion=${version} state=${compared} />`
        : null}
      <${ExportHandoff}
        make=${ready ? () => siecHandoff({ subject, source: state.source, document, result: fresh ? result : null, version }) : null}
        base=${fileBase(subject)}
        section="siec"
        disabled=${ready ? undefined : texts.export.invalid}
      />
      <p class="note">${texts.export.standalone}</p>
      ${document ? html`<p class="note" data-handoff-contents="">${t(fresh ? texts.export.siec : texts.export.siecNoResult, { nodes })}</p>` : null}
    </div>
  `;
}
