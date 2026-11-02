// Exports of a result (plan D14):
//   html`<${ExportPanel} spec=${{subject, csv: () => text, json: () => obj, chart: () => svg,
//                               cli: {command, options}, report: {command, options}, files}} />`
// CSV and JSON are written in the browser, PNG is the chart shown (charts/png.js), the
// command line comes from the server's format_command (debounced) with the paths as the
// person gave them ("in/x.csv" shown as "x.csv"), wrapped at " --" for display and copied
// as shown; Python and MCP show the same options. The Markdown report runs
// `report generate` into out/<subject>.md and downloads it; files are the result's own.

import { api } from "../api.js";
import { toPng } from "../charts/png.js";
import { bytes } from "../format.js";
import { html, useEffect, useState } from "../html.js";
import { common, t } from "../labels/common.js";
import { describeError } from "../labels/errors.js";
import { exportLabels as texts } from "../labels/exports.js";
import { sessionFileName } from "../controls/file-field.js";
import { Seg } from "./seg.js";
import { toast } from "./toast.js";

/** Delay of the command line after the last change [ms]. */
export const LINE_DELAY_MS = 300;

/**
 * A file name of a subject: characters a file system refuses replaced by "-".
 *
 * @param {string} subject e.g. "Kamiennik — Świerzawa"
 * @returns {string} the base of the file names
 */
export function fileBase(subject) {
  const base = String(subject || "")
    .replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "-")
    .replace(/\s+/g, " ")
    .trim();
  return base || "hydrolog";
}

/**
 * Save a blob as a download.
 *
 * @param {Blob} blob the content
 * @param {string} name the file name
 */
export function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Copy a text to the clipboard (a hidden text area where the Clipboard API is missing).
 *
 * @param {string} text the text
 * @returns {Promise<void>} resolves when copied
 */
export function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
  return new Promise((resolve, reject) => {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.className = "offscreen";
    document.body.append(area);
    area.select();
    let done = false;
    try {
      done = document.execCommand("copy");
    } catch {
      done = false;
    }
    area.remove();
    if (done) resolve();
    else reject(new Error("copy"));
  });
}

/**
 * The options as the person gave them: session paths without "in/" and "out/".
 *
 * @param {object} options the options sent to the server
 * @returns {object} the options to show
 */
export function shownOptions(options) {
  const shown = {};
  for (const [name, value] of Object.entries(options || {})) {
    shown[name] = typeof value === "string" ? value.replace(/^(in|out)\//, "") : value;
  }
  return shown;
}

/**
 * Wrap a command line for display: a break with " \" before an option ("--") outside
 * quotes, when the line grows longer than `width`.
 *
 * @param {string} line the line
 * @param {number} [width=50] the longest line (the panel Wyniki's width at 400 px)
 * @returns {string} the wrapped line; joined, it runs in a POSIX shell as it is
 */
export function wrapLine(line, width = 50) {
  const parts = [];
  let current = "";
  let quote = null;
  const text = String(line || "");
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quote) {
      if (char === quote) quote = null;
    } else if (char === "'" || char === '"') {
      quote = char;
    } else if (char === " " && text.startsWith("--", index + 1)) {
      parts.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  parts.push(current);
  const lines = [];
  let row = "";
  for (const part of parts) {
    if (row && row.length + 1 + part.length > width) {
      lines.push(row);
      row = part;
    } else {
      row = row ? `${row} ${part}` : part;
    }
  }
  if (row) lines.push(row);
  return lines.join(" \\\n  ");
}

/**
 * A value as a Python literal.
 *
 * @param {unknown} value a JSON value
 * @returns {string} the literal
 */
function pythonValue(value) {
  if (value === null || value === undefined) return "None";
  if (value === true) return "True";
  if (value === false) return "False";
  if (Array.isArray(value)) return `[${value.map(pythonValue).join(", ")}]`;
  if (typeof value === "object") {
    return `{${Object.entries(value)
      .map(([key, item]) => `${JSON.stringify(key)}: ${pythonValue(item)}`)
      .join(", ")}}`;
  }
  return JSON.stringify(value);
}

/**
 * The call in Python: hydrolog.run_command with keyword options.
 *
 * @param {string} command the command's name
 * @param {object} options the options as shown
 * @returns {string} the code
 */
export function pythonCall(command, options) {
  const parts = [JSON.stringify(command), ...Object.entries(options).map(([key, value]) => `${key}=${pythonValue(value)}`)];
  const lines = [];
  let row = "";
  for (const part of parts) {
    const piece = `${part},`;
    if (row && row.length + 1 + piece.length > 72) {
      lines.push(row);
      row = piece;
    } else {
      row = row ? `${row} ${piece}` : piece;
    }
  }
  if (row) lines.push(row);
  return `import hydrolog\n\nresult = hydrolog.run_command(\n${lines.map((item) => `    ${item}`).join("\n")}\n)`;
}

/**
 * The call through MCP: the tool's name and its arguments.
 *
 * @param {string} command the command's name
 * @param {object} options the options as shown
 * @returns {string} the tool and the JSON arguments
 */
export function mcpCall(command, options) {
  const tool = `hydrolog_${String(command).trim().replace(/[\s-]+/g, "_")}`;
  return `${t(texts.call.tool, { tool })}\n${JSON.stringify(options, null, 1).replace(/\n\s*/g, " ")}`;
}

/**
 * The call of a result: the command line, Python or MCP, with a copy button.
 *
 * @param {{command: string, options: object, title?: boolean}} props the command, the
 *   options sent, and whether to show the block's heading
 * @returns {object} the block
 */
export function CommandLine({ command, options, title = true }) {
  const [view, setView] = useState("cli");
  const [line, setLine] = useState(null);
  const [problem, setProblem] = useState(null);
  const shown = shownOptions(options);
  const key = JSON.stringify([command, options]);
  useEffect(() => {
    if (!command) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api
        .format(command, options, { signal: controller.signal })
        .then((text) => {
          setLine(text);
          setProblem(null);
        })
        .catch((error) => {
          if (error && error.name === "AbortError") return;
          setProblem(t(texts.call.failed, { message: error.doc ? describeError(error.doc).text : String(error) }));
        });
    }, LINE_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key]);
  let text = "";
  if (view === "cli") text = line ? wrapLine(line) : "";
  else if (view === "py") text = pythonCall(command, shown);
  else text = mcpCall(command, shown);
  const copy = () =>
    copyText(text).then(
      () => toast(common.copied),
      () => toast(common.copyFailed, "bad"),
    );
  return html`
    ${title ? html`<h3 class="group-title">${texts.call.title}</h3>` : null}
    <div class="cli">
      <div class="cli-head">
        <${Seg}
          items=${[
            { value: "cli", label: texts.call.cli },
            { value: "py", label: texts.call.python },
            { value: "mcp", label: texts.call.mcp },
          ]}
          value=${view}
          onChange=${setView}
          label=${texts.call.interfaces}
          tiny=${true}
        />
        <button class="btn sm ghost icon" type="button" aria-label=${texts.call.copy} title=${texts.call.copy} disabled=${!text} onClick=${copy}>
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" /><path d="M13 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" /></svg>
        </button>
      </div>
      <pre class="code" data-view=${view} aria-live="polite">${text || (view === "cli" ? problem || texts.call.pending : "")}</pre>
    </div>
  `;
}

/**
 * The files of a result, each to download.
 *
 * @param {{files: Array<{path: string, size_bytes?: number, status?: string}>}} props the
 *   files ("out/<name>")
 * @returns {object|null} the list
 */
export function FileList({ files }) {
  if (!files || !files.length) return null;
  return html`
    <h3 class="group-title">${texts.files.title}</h3>
    <ul class="file-list">
      ${files.map((file) => {
        const name = String(file.path).split("/").pop();
        const sessionPath = /^(in\/[^/]+|out\/.+)$/.test(String(file.path)) ? file.path : null;
        return html`<li>
          ${sessionPath
            ? html`<a class="btn sm" href=${api.fileUrl(sessionPath)} download=${name} title=${t(texts.files.download, { name })}>
                <span class="fmt">${(name.split(".").pop() || "").toUpperCase()}</span>${name}
              </a>`
            : html`<code>${file.path}</code>`}
          <span class="muted small">
            ${typeof file.size_bytes === "number" ? bytes(file.size_bytes) : ""}
            ${file.status ? ` · ${texts.files[file.status] || file.status}` : ""}
          </span>
        </li>`;
      })}
    </ul>
  `;
}

/**
 * The export buttons: CSV, JSON, PNG and the Markdown report.
 *
 * @param {{spec: object}} props the export spec
 * @returns {object} the buttons
 */
export function ExportButtons({ spec }) {
  const base = fileBase(spec.subject);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const saveCsv = () => {
    const name = `${base}.csv`;
    downloadBlob(new Blob([spec.csv()], { type: "text/csv;charset=utf-8" }), name);
    toast(t(texts.saved, { name }));
  };
  const saveJson = () => {
    const name = `${base}.result.json`;
    downloadBlob(new Blob([`${JSON.stringify(spec.json(), null, 2)}\n`], { type: "application/json" }), name);
    toast(t(texts.saved, { name }));
  };
  const savePng = async () => {
    const svg = spec.chart();
    if (!svg) return;
    try {
      const blob = await toPng(svg, { scale: 2 });
      const name = `${base}.png`;
      downloadBlob(blob, name);
      toast(t(texts.saved, { name }));
    } catch (error) {
      toast(t(texts.pngFailed, { message: String((error && error.message) || error) }), "bad");
    }
  };
  const makeReport = async () => {
    const name = `${sessionFileName(base)}.md`;
    setBusy(true);
    try {
      const envelope = await api.run(
        spec.report.command,
        { ...spec.report.options, output: `out/${name}`, force: true },
        { channel: "report" },
      );
      if (envelope.status === "ok") {
        setReport(`out/${name}`);
        const link = document.createElement("a");
        link.href = api.fileUrl(`out/${name}`);
        link.download = name;
        link.hidden = true;
        document.body.append(link);
        link.click();
        link.remove();
        toast(t(texts.saved, { name }));
      }
    } catch (error) {
      toast(error.doc ? describeError(error.doc).text : String(error), "bad");
    } finally {
      setBusy(false);
    }
  };
  return html`
    <div class="btn-row export-row">
      ${spec.csv
        ? html`<button class="btn" type="button" title=${texts.csv.title} onClick=${saveCsv}><span class="fmt">${texts.csv.format}</span>${texts.csv.label}</button>`
        : null}
      ${spec.json
        ? html`<button class="btn" type="button" title=${texts.json.title} onClick=${saveJson}><span class="fmt">${texts.json.format}</span>${texts.json.label}</button>`
        : null}
      ${spec.chart
        ? html`<button class="btn" type="button" title=${texts.png.title} onClick=${savePng}><span class="fmt">${texts.png.format}</span>${texts.png.label}</button>`
        : null}
      ${spec.report
        ? html`<button class="btn" type="button" title=${texts.report.title} disabled=${busy} onClick=${makeReport}><span class="fmt">${texts.report.format}</span>${texts.report.label}</button>`
        : null}
    </div>
    ${report ? html`<${FileList} files=${[{ path: report }]} />` : null}
  `;
}

/**
 * The export panel of a result.
 *
 * @param {{spec: {subject: string, csv?: () => string, json?: () => object,
 *   chart?: () => SVGSVGElement|null, cli?: {command: string, options: object},
 *   report?: {command: string, options: object}, files?: object[]}}} props the export spec
 * @returns {object} the panel
 */
export function ExportPanel({ spec }) {
  return html`
    <div class="export-panel">
      ${spec.cli ? html`<${CommandLine} command=${spec.cli.command} options=${spec.cli.options} />` : null}
      <${ExportButtons} spec=${spec} />
      <${FileList} files=${spec.files} />
    </div>
  `;
}
