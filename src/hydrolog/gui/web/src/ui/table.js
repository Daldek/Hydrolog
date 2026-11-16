// A data table (the mockup's `.dtable`): a sticky header with units, numbers in Polish with
// tabular figures, the first column as row headers, long tables cut with a button to show
// every row.

import { plural } from "../format.js";
import { html, useState } from "../html.js";
import { t } from "../labels/common.js";
import { results as texts } from "../labels/results.js";

/** Rows shown before „Pokaż wszystkie wiersze”. */
const ROW_LIMIT = 500;

/** The controls inside a row whose clicks stay theirs, not the row's. */
const CONTROLS = "input, button, a, select, textarea, label";

/**
 * A data table.
 *
 * @param {{columns: Array<{key: string|number, label: any, unit?: string,
 *   format?: (value: any, row: any) => string, className?: string}>, rows: Array<object|any[]>,
 *   label: string, tall?: boolean, rowHeader?: boolean,
 *   rowClass?: (row: any, index: number) => string|null, limit?: number,
 *   onRow?: (row: any, index: number) => void, currentRow?: (row: any) => boolean}} props
 *   the columns (key into each row, header, unit, cell format, cell class), the rows, the
 *   table's accessible name, whether it fills the view's height, whether the first column
 *   heads its row, a class per row, the rows shown before the button, what a click on a row
 *   (or Enter and Space on it, focused) does, and the row it made current (aria-current)
 * @returns {object} the table
 */
export function DataTable({ columns, rows, label, tall = true, rowHeader = true, rowClass, limit = ROW_LIMIT, onRow, currentRow }) {
  const [all, setAll] = useState(false);
  const shown = all || rows.length <= limit ? rows : rows.slice(0, limit);
  const cell = (row, column) => {
    const value = row[column.key];
    return column.format ? column.format(value, row) : value === null || value === undefined ? "–" : String(value);
  };
  const rowProps = (row, index) => {
    const named = (rowClass && rowClass(row, index)) || "";
    if (!onRow) return { class: named || undefined };
    return {
      class: `pickable${named ? ` ${named}` : ""}`,
      tabindex: "0",
      "aria-current": currentRow && currentRow(row) ? "true" : undefined,
      onClick: (event) => {
        if (!event.target.closest(CONTROLS)) onRow(row, index);
      },
      onKeyDown: (event) => {
        if (event.target !== event.currentTarget || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        onRow(row, index);
      },
    };
  };
  return html`
    <div class=${`table-wrap${tall ? " tall" : ""}`} tabindex="0" role="region" aria-label=${label}>
      <table class="dtable">
        <thead>
          <tr>
            ${columns.map(
              (column) => html`<th scope="col">${column.label}${column.unit ? html` <span class="u">[${column.unit}]</span>` : null}</th>`,
            )}
          </tr>
        </thead>
        <tbody>
          ${shown.map(
            (row, index) => html`<tr ...${rowProps(row, index)}>
              ${columns.map((column, at) =>
                at === 0 && rowHeader
                  ? html`<th scope="row" class=${column.className}>${cell(row, column)}</th>`
                  : html`<td class=${column.className}>${cell(row, column)}</td>`,
              )}
            </tr>`,
          )}
        </tbody>
      </table>
    </div>
    ${shown.length < rows.length
      ? html`<p class="note table-more">
          ${t(texts.truncated, { shown: shown.length, rows: plural(rows.length, texts.rowForms) })}
          <button class="link-btn" type="button" onClick=${() => setAll(true)}>${texts.more}</button>
        </p>`
      : null}
  `;
}
