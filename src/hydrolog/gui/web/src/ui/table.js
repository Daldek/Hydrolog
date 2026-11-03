// A data table (the mockup's `.dtable`): a sticky header with units, numbers in Polish with
// tabular figures, the first column as row headers, long tables cut with a button to show
// every row.

import { plural } from "../format.js";
import { html, useState } from "../html.js";
import { t } from "../labels/common.js";
import { results as texts } from "../labels/results.js";

/** Rows shown before „Pokaż wszystkie wiersze”. */
export const ROW_LIMIT = 500;

/**
 * A data table.
 *
 * @param {{columns: Array<{key: string|number, label: any, unit?: string,
 *   format?: (value: any, row: any) => string, className?: string}>, rows: Array<object|any[]>,
 *   label: string, tall?: boolean, rowHeader?: boolean,
 *   rowClass?: (row: any, index: number) => string|null, limit?: number}} props the
 *   columns (key into each row, header, unit, cell format, cell class), the rows, the
 *   table's accessible name, whether it fills the view's height, whether the first column
 *   heads its row, a class per row, and the rows shown before the button
 * @returns {object} the table
 */
export function DataTable({ columns, rows, label, tall = true, rowHeader = true, rowClass, limit = ROW_LIMIT }) {
  const [all, setAll] = useState(false);
  const shown = all || rows.length <= limit ? rows : rows.slice(0, limit);
  const cell = (row, column) => {
    const value = row[column.key];
    return column.format ? column.format(value, row) : value === null || value === undefined ? "–" : String(value);
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
            (row, index) => html`<tr class=${(rowClass && rowClass(row, index)) || undefined}>
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
