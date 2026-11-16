// The panel Dane of „Wszystkie polecenia”: the catalog's commands by group with a search,
// and the generated form of the chosen command.

import { plural } from "../../format.js";
import { html, useEffect, useRef } from "../../html.js";
import { t } from "../../labels/common.js";
import { polecenia as texts } from "../../labels/polecenia.js";
import { commandEntry } from "../../forms/model.js";
import { groupsOf, filterCommands } from "./state.js";

/**
 * The searchable list of the catalog's commands.
 *
 * @param {{catalog: {commands: object[]|null, docs: Map<string, object>, error: string|null},
 *   group: string, query: string, current: string|null, active: boolean,
 *   onGroup: (group: string) => void, onQuery: (query: string) => void,
 *   onPick: (name: string) => void}} props the catalog, the chosen group, the search, the
 *   chosen command, whether the section is shown, and the handlers
 * @returns {object} the list
 */
export function CommandList({ catalog, group, query, current, active, onGroup, onQuery, onPick }) {
  const list = useRef(null);
  const commands = catalog.commands || [];
  const groups = groupsOf(commands);
  const left = filterCommands(commands, catalog.docs, group, query);
  const shown = new Set(left.map((item) => item.name));
  useEffect(() => {
    if (!active || !list.current) return;
    const item = list.current.querySelector(".cmd-item.active");
    if (item && list.current.clientHeight) {
      list.current.scrollTop = Math.max(0, item.offsetTop - list.current.clientHeight / 3);
    }
  }, [active, current, commands.length]);
  if (catalog.error) return html`<p class="err" role="alert">${t(texts.loadFailed, { message: catalog.error })}</p>`;
  if (!catalog.commands) return html`<p class="muted" role="status">${texts.loading}</p>`;
  const summaryOf = (item) => {
    const doc = catalog.docs.get(item.name);
    const polish = doc ? (commandEntry(doc).i18n || {}).pl : null;
    return (polish && polish.summary) || item.summary || "";
  };
  return html`
    <div class="cmd-tools">
      <select class="sel-sm" aria-label=${texts.groupSelect} value=${group} onChange=${(event) => onGroup(event.currentTarget.value)}>
        <option value="">${t(texts.allGroups, { count: commands.length })}</option>
        ${groups.map(
          (item) => html`<option value=${item.group}>${t(texts.groupOption, {
            group: item.group,
            title: item.title || item.group,
            count: item.commands.length,
          })}</option>`,
        )}
      </select>
      <span class="search">
        <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="5" /><path d="M13 13l4 4" /></svg>
        <input
          type="search"
          placeholder=${texts.search}
          aria-label=${texts.searchLabel}
          value=${query}
          onInput=${(event) => onQuery(event.currentTarget.value)}
        />
      </span>
    </div>
    <ul class="cmd-list" ref=${list} aria-label=${texts.listLabel}>
      ${groups.map((item) => {
        const visible = item.commands.filter((command) => shown.has(command.name));
        if (!visible.length) return null;
        return html`
          <li class="cmd-group" key=${`g-${item.group}`}>${item.title ? t(texts.groupHeading, { group: item.group, title: item.title }) : item.group}</li>
          ${visible.map(
            (command) => html`<li class=${`cmd-item${command.name === current ? " active" : ""}`} key=${command.name} data-command=${command.name}>
              <button type="button" aria-current=${command.name === current ? "true" : undefined} onClick=${() => onPick(command.name)}>
                <code>${command.name}</code>
                <span>${summaryOf(command)}</span>
              </button>
            </li>`,
          )}
        `;
      })}
      ${left.length ? null : html`<li class="cmd-empty">${texts.empty}</li>`}
    </ul>
    <p class="sr-only" role="status">${plural(left.length, texts.commandForms)}</p>
  `;
}
