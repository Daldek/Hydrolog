// Files of a generated form (plan D7, D11). An input path is one of the session's uploaded
// files or a new upload ("in/<name>"); an output path is a file name in "out/" (by default
// the basename of the first catalog example's value). No other path reaches the server.

import { api } from "../api.js";
import { bytes, fold } from "../format.js";
import { html, useEffect, useRef, useState } from "../html.js";
import { common, t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { formTexts } from "../labels/options.js";
import { defaultOutputName, FILE_NAME } from "../forms/model.js";
import { describedBy, FieldLabel, FieldNotes } from "./field.js";

let session = null;
let pending = null;
const listeners = new Set();

/**
 * Read the session again (its files and limits) and tell every file field.
 *
 * @returns {Promise<object|null>} the hydrolog-gui-session/1 document, null on failure
 */
export function refreshSession() {
  pending = api
    .session()
    .then((doc) => {
      session = doc;
      for (const listener of [...listeners]) listener(doc);
      return doc;
    })
    .catch(() => session)
    .finally(() => {
      pending = null;
    });
  return pending;
}

/**
 * The session's document, read once and shared by every file field.
 *
 * @returns {object|null} hydrolog-gui-session/1, null until it arrives
 */
export function useSession() {
  const [doc, setDoc] = useState(session);
  useEffect(() => {
    listeners.add(setDoc);
    if (!session && !pending) refreshSession();
    return () => listeners.delete(setDoc);
  }, []);
  return doc;
}

/**
 * The session's input files.
 *
 * @param {object|null} doc the session's document
 * @returns {Array<{path: string, size_bytes: number}>} files under "in/"
 */
export function inputFiles(doc) {
  return ((doc && doc.files) || []).filter((file) => String(file.path).startsWith("in/"));
}

/**
 * A file name the server accepts (D7): diacritics folded with the case kept
 * ("Dopływ.csv" gives "Doplyw.csv", as the command line then names it), other characters
 * replaced by "_", a letter or digit first, 128 characters at most.
 *
 * @param {string} name the name of the person's file
 * @returns {string} the name to upload under
 */
export function sessionFileName(name) {
  const base = String(name).split(/[\\/]/).pop();
  const plain = base.replace(/[\u0080-\uffff]/g, (char) =>
    char === char.toLowerCase() ? fold(char) : fold(char).toUpperCase(),
  );
  let safe = plain.replace(/[^A-Za-z0-9._ -]/g, "_");
  if (!/^[A-Za-z0-9]/.test(safe)) safe = `f${safe}`;
  if (safe.length > 128) {
    const dot = safe.lastIndexOf(".");
    const extension = dot > 0 && safe.length - dot <= 10 ? safe.slice(dot) : "";
    safe = safe.slice(0, 128 - extension.length) + extension;
  }
  return FILE_NAME.test(safe) ? safe : "plik";
}

/**
 * Upload a person's file into the session's "in/"; a file over the session's limit is
 * refused before it is sent.
 *
 * @param {File} file the file
 * @returns {Promise<{path: string, name: string}>} the session path and the name used
 * @throws {Error} with a Polish message when the file is too large
 */
export async function uploadFile(file) {
  const name = sessionFileName(file.name);
  const limit = session && session.limits && session.limits.file_bytes;
  if (typeof limit === "number" && file.size > limit) {
    throw new Error(t(formTexts.tooLarge, { name: file.name, size: bytes(file.size), limit: bytes(limit) }));
  }
  const stored = await api.upload(file, name);
  await refreshSession();
  return { path: stored.path || `in/${name}`, name };
}

/**
 * A path option of a generated form: an input file or an output name.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, onInput: (value: string) => void}} props the field, the control's
 *   id, "in/<name>" or an output name, the message of a check, whether a value is required
 *   now, and the change handler
 * @returns {object} the field
 */
export function FileField(props) {
  return props.field.kind === "file-out" ? html`<${OutputFile} ...${props} />` : html`<${InputFile} ...${props} />`;
}

/**
 * An input file: one of the session's files, or a new upload.
 *
 * @param {object} props as FileField
 * @returns {object} the field
 */
function InputFile({ field, id, value, error, required, disabled, onInput }) {
  const doc = useSession();
  const picker = useRef(null);
  const [state, setState] = useState(null);
  const files = inputFiles(doc);
  const current = value || "";
  const known = files.some((file) => file.path === current);
  const onFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (!file) return;
    setState({ busy: true, text: t(formTexts.uploading, { name: file.name }) });
    try {
      const stored = await uploadFile(file);
      setState({ busy: false, text: t(formTexts.uploaded, { name: stored.name }) });
      onInput(stored.path);
    } catch (failure) {
      const text = failure && failure.doc ? describeError(failure.doc).text : String((failure && failure.message) || failure);
      setState({ busy: false, error: true, text: t(formTexts.uploadFailed, { message: text }) });
    }
  };
  return html`
    <div class=${`opt opt-file${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <div class="file-row">
        <select
          id=${id}
          value=${current}
          disabled=${disabled}
          aria-invalid=${error ? "true" : "false"}
          aria-required=${required ? "true" : "false"}
          aria-describedby=${describedBy(field, id, error)}
          onChange=${(event) => onInput(event.currentTarget.value)}
        >
          <option value="">${formTexts.noFile}</option>
          ${!known && current ? html`<option value=${current}>${current.slice(3)}</option>` : null}
          ${files.map(
            (file) => html`<option value=${file.path}>${file.path.slice(3)} (${bytes(file.size_bytes)})</option>`,
          )}
        </select>
        <button class="btn sm" type="button" disabled=${disabled || (state && state.busy)} onClick=${() => picker.current.click()}>
          ${common.actions.upload}
        </button>
        <input ref=${picker} type="file" hidden onChange=${onFile} />
      </div>
      ${state ? html`<span class=${state.error ? "err" : "file-state"} role=${state.error ? "alert" : "status"}>${state.text}</span>` : null}
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}

/**
 * An output file: a name in the session's "out/".
 *
 * @param {object} props as FileField
 * @returns {object} the field
 */
function OutputFile({ field, id, value, error, required, disabled, onInput }) {
  return html`
    <div class=${`opt opt-file${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <span class="ibox file-out">
        <span class="prefix" aria-hidden="true">${formTexts.outPrefix}</span>
        <input
          id=${id}
          type="text"
          autocomplete="off"
          spellcheck=${false}
          disabled=${disabled}
          value=${value ?? ""}
          placeholder=${defaultOutputName(field)}
          aria-invalid=${error ? "true" : "false"}
          aria-required=${required ? "true" : "false"}
          aria-describedby=${describedBy(field, id, error)}
          onInput=${(event) => onInput(event.currentTarget.value)}
        />
      </span>
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}
