// Lists of a generated form (plan D11): an `array` of numbers is a series pasted from a
// spreadsheet or text, or read from a CSV file in the browser, with the count, the range
// and the catalog's bounds of each value; an `array` of strings is a row of chips.

import { auto, inputText, parseNumber, plural } from "../format.js";
import { html, useRef, useState } from "../html.js";
import { t } from "../labels/common.js";
import { formTexts } from "../labels/options.js";
import { parseSeries } from "../forms/model.js";
import { describedBy, FieldLabel, FieldNotes } from "./field.js";

/**
 * Read a delimited text file: the delimiter from the first line (semicolon, tab or
 * comma), a header when the first row is not all numbers.
 *
 * @param {string} text the file's text
 * @returns {{header: string[]|null, rows: string[][]}} the header and the data rows
 */
export function readTable(text) {
  const lines = String(text || "")
    .replace(/^\ufeff/, "")
    .split(/\r?\n/)
    .filter((line) => line.trim() !== "");
  if (!lines.length) return { header: null, rows: [] };
  const first = lines[0];
  const delimiter = first.includes(";") ? ";" : first.includes("\t") ? "\t" : ",";
  const rows = lines.map((line) => line.split(delimiter).map((cell) => cell.trim().replace(/^"(.*)"$/, "$1")));
  const isNumber = (cell) => {
    const value = parseNumber(cell);
    return value !== null && !Number.isNaN(value);
  };
  const header = rows[0].every(isNumber) ? null : rows[0];
  return { header, rows: header ? rows.slice(1) : rows };
}

/**
 * The columns of a table that hold numbers in every row.
 *
 * @param {{header: string[]|null, rows: string[][]}} table a table of readTable
 * @returns {Array<{index: number, name: string}>} the columns
 */
export function numericColumns(table) {
  const width = Math.max(0, ...table.rows.map((row) => row.length));
  const columns = [];
  for (let index = 0; index < width; index += 1) {
    const numeric = table.rows.length > 0 && table.rows.every((row) => {
      const value = parseNumber(row[index]);
      return value !== null && !Number.isNaN(value);
    });
    if (numeric) {
      const name = table.header && table.header[index] ? table.header[index] : t(formTexts.columnN, { n: index + 1 });
      columns.push({ index, name });
    }
  }
  return columns;
}

/**
 * A column of a table as the text of a series field ("0,2954; 0,8376; …").
 *
 * @param {{rows: string[][]}} table a table of readTable
 * @param {number} index the column
 * @returns {string} the series text
 */
export function columnText(table, index) {
  return table.rows.map((row) => inputText(parseNumber(row[index]))).join("; ");
}

/**
 * The catalog's bounds of each value of a series, in words.
 *
 * @param {object} field a field of fieldModel
 * @returns {string|null} e.g. „każda ≥ 0”
 */
export function eachBound(field) {
  const min = field.min === null ? null : inputText(field.min);
  const max = field.max === null ? null : inputText(field.max);
  const above = field.exclusiveMinimum === null ? null : inputText(field.exclusiveMinimum);
  if (min !== null && max !== null) return t(formTexts.eachBetween, { min, max });
  if (above !== null && max !== null) return t(formTexts.eachAboveMax, { min: above, max });
  if (above !== null) return t(formTexts.eachAbove, { min: above });
  if (min !== null) return t(formTexts.eachMin, { min });
  if (max !== null) return t(formTexts.eachMax, { max });
  return null;
}

/**
 * A series of numbers.
 *
 * @param {{field: object, id: string, value?: string, error?: string, required: boolean,
 *   disabled?: boolean, onInput: (text: string) => void}} props the field, the control's
 *   id, the series as text, the message of a check, whether a value is required now, and
 *   the change handler
 * @returns {object} the field
 */
export function SeriesField({ field, id, value, error, required, disabled, onInput }) {
  const fileInput = useRef(null);
  const [table, setTable] = useState(null);
  const [column, setColumn] = useState(null);
  const [problem, setProblem] = useState(null);
  const parsed = parseSeries(value);
  const count = parsed.bad ? null : parsed.values.length;
  const bound = eachBound(field);
  const summary = [];
  if (count) {
    let low = Infinity;
    let high = -Infinity;
    for (const item of parsed.values) {
      if (item < low) low = item;
      if (item > high) high = item;
    }
    summary.push(plural(count, formTexts.seriesForms));
    summary.push(t(formTexts.seriesRange, { min: auto(low), max: auto(high) }));
  }
  if (bound) summary.push(bound);

  const onFile = async (event) => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    event.currentTarget.value = "";
    if (!file) return;
    try {
      const read = readTable(await file.text());
      const columns = numericColumns(read);
      if (!columns.length) {
        setProblem(formTexts.noNumbers);
        return;
      }
      const chosen = columns[columns.length - 1].index;
      setProblem(null);
      setTable(columns.length > 1 ? read : null);
      setColumn(chosen);
      onInput(columnText(read, chosen));
    } catch (failure) {
      setProblem(t(formTexts.readFailed, { message: failure.message }));
    }
  };

  return html`
    <div class=${`opt opt-series${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <textarea
        id=${id}
        rows="3"
        spellcheck=${false}
        disabled=${disabled}
        value=${value ?? ""}
        aria-invalid=${error ? "true" : "false"}
        aria-required=${required ? "true" : "false"}
        aria-describedby=${describedBy(field, id, error)}
        onInput=${(event) => onInput(event.currentTarget.value)}
      ></textarea>
      <div class="series-tools">
        <button class="btn sm" type="button" disabled=${disabled} onClick=${() => fileInput.current.click()}>
          ${formTexts.fromCsv}
        </button>
        <input ref=${fileInput} type="file" accept=".csv,.txt,.tsv,text/csv,text/plain" hidden onChange=${onFile} />
        ${table
          ? html`<select
              class="sel-sm"
              aria-label=${formTexts.column}
              value=${String(column)}
              onChange=${(event) => {
                const index = Number(event.currentTarget.value);
                setColumn(index);
                onInput(columnText(table, index));
              }}
            >
              ${numericColumns(table).map((item) => html`<option value=${String(item.index)}>${item.name}</option>`)}
            </select>`
          : null}
        <span class="series-sum">${summary.join(" · ")}</span>
      </div>
      ${problem ? html`<span class="err" role="alert">${problem}</span>` : null}
      <${FieldNotes} field=${field} id=${id} error=${error} />
    </div>
  `;
}

/**
 * A list of texts as chips: Enter or a comma adds the typed text, × removes a chip.
 *
 * @param {{field: object, id: string, value?: string[], error?: string, required: boolean,
 *   disabled?: boolean, onInput: (items: string[]) => void}} props the field, the control's
 *   id, the texts, the message of a check, whether a value is required now, and the change
 *   handler
 * @returns {object} the field
 */
export function ChipsField({ field, id, value, error, required, disabled, onInput }) {
  const items = Array.isArray(value) ? value : [];
  const [draft, setDraft] = useState("");
  const add = (text) => {
    const words = String(text)
      .split(",")
      .map((word) => word.trim())
      .filter(Boolean);
    if (words.length) onInput([...items, ...words.filter((word) => !items.includes(word))]);
    setDraft("");
  };
  const onKeyDown = (event) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      add(draft);
    } else if (event.key === "Backspace" && draft === "" && items.length) {
      onInput(items.slice(0, -1));
    }
  };
  return html`
    <div class=${`opt opt-chips${error ? " invalid" : ""}`} data-option=${field.name}>
      <${FieldLabel} field=${field} id=${id} required=${required} />
      <div class="chips edit">
        ${items.map(
          (item) => html`<span class="chip on">${item}<button
              type="button"
              class="chip-x"
              disabled=${disabled}
              aria-label=${t(formTexts.chipRemove, { value: item })}
              onClick=${() => onInput(items.filter((other) => other !== item))}
            >×</button></span>`,
        )}
      </div>
      <input
        id=${id}
        type="text"
        autocomplete="off"
        spellcheck=${false}
        disabled=${disabled}
        value=${draft}
        placeholder=${formTexts.chipsAdd}
        aria-invalid=${error ? "true" : "false"}
        aria-describedby=${describedBy(field, id, error)}
        onInput=${(event) => setDraft(event.currentTarget.value)}
        onKeyDown=${onKeyDown}
        onBlur=${() => draft.trim() && add(draft)}
      />
      <${FieldNotes} field=${field} id=${id} error=${error} extra=${formTexts.chipsHint} />
    </div>
  `;
}
