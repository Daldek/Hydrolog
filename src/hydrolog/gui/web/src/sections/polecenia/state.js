// State of „Wszystkie polecenia”: the catalog (the list and each command's document), the
// groups and the search, and the inputs kept in the browser under
// "hydrolog-gui/polecenia/1": the chosen command, the group and the search, and the
// values of each command's form (no results). A command opened for the first time is
// filled with its first catalog example.

import { api } from "../../api.js";
import { fold } from "../../format.js";
import { useEffect, useState } from "../../html.js";
import { describeError } from "../../labels/errors.js";
import { groupTitle } from "../../labels/groups.js";
import { commandEntry, defaultOutputName, fieldModel, valuesFromCall } from "../../forms/model.js";

/** The key of the section's inputs. */
export const SECTION = "polecenia";

/** The command a first visit opens (the mockup's), when the catalog has it. */
export const FIRST_COMMAND = "uh nash";

/**
 * The inputs of a first visit.
 *
 * @returns {{command: string|null, group: string, query: string, values: object}} the state
 */
export function initialState() {
  return { command: null, group: "", query: "", values: {} };
}

/**
 * The group of a command: the first word of its name.
 *
 * @param {string} name e.g. "uh nash"
 * @returns {string} e.g. "uh"
 */
export function groupOf(name) {
  return String(name).split(" ")[0];
}

/**
 * The groups of the list, in catalog order, each with its Polish title and commands.
 *
 * @param {Array<{name: string}>} commands the command list
 * @returns {Array<{group: string, title: string|null, commands: object[]}>} the groups
 */
export function groupsOf(commands) {
  const groups = [];
  for (const command of commands) {
    const group = groupOf(command.name);
    let found = groups.find((item) => item.group === group);
    if (!found) {
      found = { group, title: groupTitle(group), commands: [] };
      groups.push(found);
    }
    found.commands.push(command);
  }
  return groups;
}

/**
 * What a search finds a command by: its name, operation id, Polish summary and
 * description, its options' names and their allowed values.
 *
 * @param {{name: string, operation_id?: string, summary?: string}} item the list's entry
 * @param {object|null} doc the command's catalog document, when it arrived
 * @returns {string} the folded text
 */
export function searchText(item, doc) {
  const parts = [item.name, item.operation_id || "", item.summary || ""];
  const entry = doc ? commandEntry(doc) : null;
  if (entry) {
    const polish = (entry.i18n && entry.i18n.pl) || {};
    parts.push(polish.summary || "", polish.description || "");
    for (const option of entry.options || []) {
      parts.push(option.name);
      for (const choice of option.enum || []) parts.push(choice.value);
    }
  }
  return fold(parts.join(" ").replace(/[_-]/g, " "));
}

/**
 * The commands a group and a search leave.
 *
 * @param {object[]} commands the command list
 * @param {Map<string, object>} docs the catalog documents by name
 * @param {string} group a group's name, "" for all
 * @param {string} query the search's words
 * @returns {object[]} the commands left
 */
export function filterCommands(commands, docs, group, query) {
  const words = fold(query).replace(/[_-]/g, " ").split(/\s+/).filter(Boolean);
  return commands.filter((item) => {
    if (group && groupOf(item.name) !== group) return false;
    if (!words.length) return true;
    const text = searchText(item, docs.get(item.name) || null);
    return words.every((word) => text.includes(word));
  });
}

/**
 * The catalog: the command list, then every command's document (its Polish summary and
 * options, for the list and the search), fetched once.
 *
 * @returns {{commands: object[]|null, docs: Map<string, object>, error: string|null}} the
 *   list (null until it arrives), the documents by name and a loading error
 */
export function useCatalog() {
  const [catalog, setCatalog] = useState({ commands: null, docs: new Map(), error: null });
  useEffect(() => {
    let alive = true;
    api
      .commands()
      .then((list) => {
        if (!alive) return;
        const commands = list.commands || [];
        setCatalog((old) => ({ ...old, commands }));
        for (const item of commands) {
          api
            .command(item.name)
            .then((doc) => {
              if (alive) setCatalog((old) => ({ ...old, docs: new Map(old.docs).set(item.name, doc) }));
            })
            .catch(() => {});
        }
      })
      .catch((error) => {
        if (alive) setCatalog((old) => ({ ...old, error: error.doc ? describeError(error.doc).text : String(error) }));
      });
    return () => {
      alive = false;
    };
  }, []);
  return catalog;
}

/**
 * The values of a command's form opened for the first time: its first catalog example,
 * and the default name of every output file.
 *
 * @param {object} doc the command's catalog document
 * @param {string[]} [sessionFiles] the session's files ("in/<name>")
 * @returns {object} the values
 */
export function firstValues(doc, sessionFiles = []) {
  const entry = commandEntry(doc);
  const model = fieldModel(doc);
  const example = entry.examples && entry.examples[0] ? entry.examples[0].call : "";
  const values = example ? valuesFromCall(model, example, sessionFiles) : {};
  for (const field of model.fields) {
    if (field.kind === "file-out" && !values[field.name] && field.required) values[field.name] = defaultOutputName(field);
  }
  return values;
}
