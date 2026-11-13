// The form model of one catalog command (plan D11): a pure module without Preact, so a kit
// component can wrap it later. It turns a commands-1 entry into fields, checks values
// against the catalog's types and bounds, and builds the options a run sends.
//
// Values of a form are what a person typed: numbers and series as text, choices as text,
// booleans as booleans, chips as lists of text, JSON as text, an input file as
// "in/<name>", an output file as a bare name (sent as "out/<name>"). The chosen group of a
// command-level `one_of` is the value under ONE_OF_KEY.

import { inputText, parseNumber } from "../format.js";
import { t } from "../labels/common.js";
import { errors as errorTexts, reasonText } from "../labels/errors.js";
import {
  commandOptions,
  formTexts,
  ONE_OF_TITLE,
  oneOf as oneOfLabels,
  options as optionLabels,
} from "../labels/options.js";
import { unitLabel } from "../labels/units.js";

/** The key of `values` holding the index of the chosen `one_of` group. */
export const ONE_OF_KEY = "#one_of";

/** File names of the session's files (plan D7). */
export const FILE_NAME = /^[A-Za-z0-9][A-Za-z0-9._ -]{0,127}$/;

const DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const DATE_TIME = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})(:(\d{2})(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$/;

/**
 * Whether a text is a date of the calendar ("2024-02-29", not "2023-02-29" or "2024-13-01").
 *
 * @param {string} text the text
 * @returns {boolean} true for a valid RRRR-MM-DD date
 */
function isDate(text) {
  const found = DATE.exec(text);
  if (!found) return false;
  const [year, month, day] = found.slice(1).map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

/**
 * Whether a text is a date and a time ("2024-05-01T12:30", seconds and a zone optional).
 *
 * @param {string} text the text
 * @returns {boolean} true for a valid date and time
 */
function isDateTime(text) {
  const found = DATE_TIME.exec(text);
  if (!found || !isDate(found[1])) return false;
  return Number(found[2]) < 24 && Number(found[3]) < 60 && (found[5] === undefined || Number(found[5]) < 60);
}

/**
 * The command entry of a catalog document: a hydrolog-commands/1 document holding one
 * command, or the entry itself.
 *
 * @param {object} doc the document or the entry
 * @returns {object} the entry (name, options, one_of, i18n…)
 */
export function commandEntry(doc) {
  return doc && Array.isArray(doc.commands) ? doc.commands[0] : doc;
}

/**
 * The control kind of an option.
 *
 * @param {object} option an option of commands-1
 * @returns {string} number | integer | choice | boolean | series | chips | json | objects |
 *   file-in | file-out | text
 */
export function kindOf(option) {
  if (option.path_role === "input") return "file-in";
  if (option.path_role === "output") return "file-out";
  switch (option.type) {
    case "number":
      return "number";
    case "integer":
      return "integer";
    case "boolean":
      return "boolean";
    case "object":
      return "json";
    case "array":
      if (option.items === "number" || option.items === "integer") return "series";
      if (option.items === "string") return "chips";
      return "objects";
    default:
      return Array.isArray(option.enum) && option.enum.length ? "choice" : "text";
  }
}

/**
 * The first word of an option name: "lutz_urban_pct" gives "lutz".
 *
 * @param {string} name the option's name
 * @returns {string} the prefix
 */
function prefixOf(name) {
  const cut = name.indexOf("_");
  return cut > 0 ? name.slice(0, cut) : name;
}

/**
 * The `one_of` groups each option belongs to: its own groups, and for an option outside
 * every group, the group it describes. An option sharing the first word of every member of
 * exactly one group of two or more members belongs to it (uh nash: lutz_forest_pct joins
 * the Lutz group); a column of a file (`*_column`) belongs to the group holding
 * `input_file`.
 *
 * @param {object} entry the command entry
 * @returns {Map<string, {groups: number[], member: boolean}>} by option name
 */
export function paneMembership(entry) {
  const groups = Array.isArray(entry.one_of) ? entry.one_of : [];
  const found = new Map();
  groups.forEach((members, index) => {
    for (const name of members) {
      const known = found.get(name) || { groups: [], member: true };
      known.groups.push(index);
      found.set(name, known);
    }
  });
  const prefixes = groups.map((members) => {
    if (members.length < 2 || !members.every((name) => name.includes("_"))) return null;
    const first = prefixOf(members[0]);
    return members.every((name) => prefixOf(name) === first) ? first : null;
  });
  const fileGroup = groups.findIndex((members) => members.includes("input_file"));
  for (const option of entry.options || []) {
    if (found.has(option.name) || option.required) continue;
    const matching = prefixes
      .map((prefix, index) => (prefix && option.name.includes("_") && prefixOf(option.name) === prefix ? index : -1))
      .filter((index) => index >= 0);
    if (matching.length === 1) {
      found.set(option.name, { groups: matching, member: false });
    } else if (option.name.endsWith("_column") && fileGroup >= 0) {
      found.set(option.name, { groups: [fileGroup], member: false });
    }
  }
  return found;
}

/**
 * A value shown to a person: numbers with a decimal comma, lists joined.
 *
 * @param {unknown} value a catalog value
 * @returns {string} the text
 */
function shownValue(value) {
  if (typeof value === "number") return inputText(value);
  if (typeof value === "boolean") return value ? "tak" : "nie";
  if (Array.isArray(value)) return value.map(shownValue).join("; ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/**
 * Turn one catalog command into the fields of its form.
 *
 * @param {object} commandDoc a hydrolog-commands/1 document of one command, or its entry
 * @param {{labels?: Object<string, string>, hide?: string[], values?: object}} [settings]
 *   label overrides by option name (before the command's own labels and the shared
 *   ones), options the caller supplies itself (not shown, not checked, not sent), and
 *   the current values (the chosen group, `excludes`)
 * @returns {{command: object, fields: object[], groups: object[], oneOf: object|null}}
 *   the entry; the fields in catalog order; the sections of the form (`main`, sections
 *   named by the catalog, `more` „Opcje dodatkowe”), each listing field names and, in
 *   `main`, ONE_OF_KEY where the `one_of` choice stands; the `one_of` choice with its
 *   title, the chosen group and each group's label, members and fields
 */
export function fieldModel(commandDoc, settings = {}) {
  const entry = commandEntry(commandDoc);
  const hide = new Set(settings.hide || []);
  const values = settings.values || {};
  const own = Object.hasOwn(commandOptions, entry.name) ? commandOptions[entry.name] : {};
  const labels = { ...optionLabels, ...own, ...(settings.labels || {}) };
  const membership = paneMembership(entry);
  const examplesByName = new Map();
  for (const option of entry.options || []) {
    if (Array.isArray(option.examples) && option.examples.length) {
      examplesByName.set(option.name, option.examples);
    }
  }
  const fields = [];
  for (const option of entry.options || []) {
    if (hide.has(option.name)) continue;
    const kind = kindOf(option);
    const pane = membership.get(option.name) || null;
    const hasDefault = Object.hasOwn(option, "default") && option.default !== null;
    const polish = (option.i18n && option.i18n.pl) || {};
    const meanings = polish.enum || {};
    fields.push({
      name: option.name,
      kind,
      type: option.type,
      items: option.items || null,
      label: Object.hasOwn(labels, option.name) ? labels[option.name] : null,
      description: polish.description || option.description || "",
      unit: option.unit || null,
      unitLabel: option.unit ? unitLabel(option.unit) : null,
      required: Boolean(option.required),
      default: hasDefault ? option.default : null,
      defaultText: hasDefault ? shownValue(option.default) : null,
      min: typeof option.min === "number" ? option.min : null,
      max: typeof option.max === "number" ? option.max : null,
      exclusiveMinimum:
        typeof option.exclusive_minimum === "number" ? option.exclusive_minimum : null,
      choices: (option.enum || []).map((item) => ({
        value: item.value,
        meaning: Object.hasOwn(meanings, item.value) ? meanings[item.value] : item.meaning || "",
      })),
      pathRole: option.path_role || null,
      examples: examplesByName.get(option.name) || [],
      groups: pane ? pane.groups : [],
      member: pane ? pane.member : false,
      section: typeof option.section === "string" && option.section ? option.section : null,
      format: typeof option.format === "string" ? option.format : null,
      requires: Array.isArray(option.requires) ? option.requires : [],
      excludes: Array.isArray(option.excludes) ? option.excludes : [],
      disabledBy: null,
    });
  }
  const byName = new Map(fields.map((field) => [field.name, field]));
  for (const field of fields) {
    if (!isSet(field, values[field.name])) continue;
    for (const name of field.excludes) {
      const other = byName.get(name);
      if (other && !isSet(other, values[name])) other.disabledBy = field.name;
    }
  }

  let oneOf = null;
  const groups = Array.isArray(entry.one_of) ? entry.one_of : [];
  if (groups.length) {
    const named = Object.hasOwn(oneOfLabels, entry.name) ? oneOfLabels[entry.name] : null;
    let chosen = Number(values[ONE_OF_KEY]);
    if (!Number.isInteger(chosen) || chosen < 0 || chosen >= groups.length) chosen = 0;
    oneOf = {
      key: ONE_OF_KEY,
      title: named ? named.title : ONE_OF_TITLE,
      count: groups.length,
      chosen,
      groups: groups.map((members, index) => ({
        index,
        label:
          (named && named.groups[index]) ||
          members.map((name) => (byName.get(name) && byName.get(name).label) || name).join(" + "),
        members: [...members],
        names: fields.filter((field) => field.groups.includes(index)).map((field) => field.name),
      })),
    };
  }

  const main = { id: "main", title: null, names: [], open: true };
  const more = { id: "more", title: formTexts.more, names: [], open: false };
  const sections = new Map();
  for (const field of fields) {
    if (field.groups.length) {
      if (!main.names.includes(ONE_OF_KEY)) main.names.push(ONE_OF_KEY);
      continue;
    }
    if (field.section) {
      if (!sections.has(field.section)) {
        sections.set(field.section, { id: field.section, title: field.section, names: [], open: true });
      }
      sections.get(field.section).names.push(field.name);
    } else if (
      field.required ||
      field.default !== null ||
      field.kind === "boolean" ||
      field.kind === "file-out"
    ) {
      main.names.push(field.name);
    } else {
      more.names.push(field.name);
    }
  }
  if (oneOf && !main.names.includes(ONE_OF_KEY)) main.names.push(ONE_OF_KEY);
  more.open = main.names.length + sections.size <= 1;
  const sectionList = [main, ...sections.values(), more].filter((section) => section.names.length);
  return { command: entry, fields, groups: sectionList, oneOf };
}

/**
 * Whether a value counts as given.
 *
 * @param {object} field a field of fieldModel
 * @param {unknown} value its value
 * @returns {boolean} true when the value would be sent
 */
export function isGiven(field, value) {
  if (field.kind === "boolean") return typeof value === "boolean";
  if (Array.isArray(value)) return value.length > 0;
  return value !== undefined && value !== null && String(value).trim() !== "";
}

/**
 * Whether a value is set for `requires` and `excludes`: given, and for a boolean, other than
 * its default (an unticked flag asks for nothing and excludes nothing, as it is not sent).
 *
 * @param {object} field a field of fieldModel
 * @param {unknown} value its value
 * @returns {boolean} true when the value is set
 */
function isSet(field, value) {
  if (!isGiven(field, value)) return false;
  return field.kind !== "boolean" || value !== (field.default === null ? false : Boolean(field.default));
}

/**
 * Whether a field takes part in the form now: not in a group other than the chosen one,
 * and not disabled by an `excludes` of a given field.
 *
 * @param {object} model the result of fieldModel
 * @param {object} field one of its fields
 * @returns {boolean} true when the field is shown, checked and sent
 */
export function isActive(model, field) {
  if (field.disabledBy) return false;
  if (!field.groups.length || !model.oneOf) return true;
  return field.groups.includes(model.oneOf.chosen);
}

/**
 * Whether a field must have a value now: required by the catalog, a member of the chosen
 * group, or required by a given field's `requires`.
 *
 * @param {object} model the result of fieldModel
 * @param {object} field one of its fields
 * @param {object} values the form's values
 * @returns {boolean} true when the field is required
 */
export function isRequired(model, field, values) {
  if (field.required) return true;
  if (field.member && model.oneOf && field.groups.includes(model.oneOf.chosen)) return true;
  return model.fields.some(
    (other) =>
      other.requires.includes(field.name) && isActive(model, other) && isSet(other, values[other.name]),
  );
}

/**
 * A message with its machine reason, as the forms show it: "Najwyżej 100 (podano 150) ·
 * maximum".
 *
 * @param {string} text the Polish sentence
 * @param {string} reason the reason code
 * @returns {string} the message
 */
export function withReason(text, reason) {
  return reason ? `${text} · ${reason}` : text;
}

/**
 * Split a series typed or pasted by a person into tokens: semicolons, tabs, new lines and
 * spaces separate values; a comma is a decimal comma, unless the text has decimal dots,
 * when commas separate values too ("0.29,0.84").
 *
 * @param {string} text the series as text
 * @returns {string[]} the tokens
 */
export function seriesTokens(text) {
  const source = String(text || "").trim();
  if (!source) return [];
  const pattern = source.includes(".") ? /[\s;,]+/ : /[\s;]+/;
  return source.split(pattern).filter(Boolean);
}

/**
 * Parse a series typed or pasted by a person.
 *
 * @param {string} text the series as text
 * @returns {{values: number[], bad: {index: number, text: string}|null}} the numbers, and
 *   the first token that is not a number
 */
export function parseSeries(text) {
  const values = [];
  const tokens = seriesTokens(text);
  for (let index = 0; index < tokens.length; index += 1) {
    const value = parseNumber(tokens[index].replace(/,$/, ""));
    if (value === null || Number.isNaN(value)) return { values, bad: { index, text: tokens[index] } };
    values.push(value);
  }
  return { values, bad: null };
}

/**
 * Check a number against a field's bounds.
 *
 * @param {object} field a field of fieldModel
 * @param {number} value the number
 * @returns {{reason: string, details: object}|null} the broken bound, null when in bounds
 */
function boundProblem(field, value) {
  if (field.exclusiveMinimum !== null && !(value > field.exclusiveMinimum)) {
    return { reason: "exclusive_minimum", details: { exclusive_minimum: field.exclusiveMinimum, value } };
  }
  if (field.min !== null && value < field.min) {
    return { reason: "minimum", details: { minimum: field.min, value } };
  }
  if (field.max !== null && value > field.max) {
    return { reason: "maximum", details: { maximum: field.max, value } };
  }
  return null;
}

/**
 * The message of one field's value, or null when it is fine.
 *
 * @param {object} field a field of fieldModel
 * @param {unknown} value its value
 * @param {boolean} required whether a value is required now
 * @returns {string|null} the message with its reason
 */
function checkField(field, value, required) {
  const given = isGiven(field, value);
  if (!given) return required ? withReason(reasonText("required"), "required") : null;
  switch (field.kind) {
    case "number":
    case "integer": {
      const number = parseNumber(value);
      if (Number.isNaN(number)) {
        return withReason(reasonText("type", { expected: field.kind }), "type");
      }
      if (field.kind === "integer" && !Number.isInteger(number)) {
        return withReason(reasonText("type", { expected: "integer" }), "type");
      }
      const problem = boundProblem(field, number);
      return problem ? withReason(reasonText(problem.reason, problem.details), problem.reason) : null;
    }
    case "series": {
      const parsed = parseSeries(value);
      if (parsed.bad) {
        return withReason(
          t(errorTexts.reasons.not_a_number, { index: parsed.bad.index + 1, text: parsed.bad.text }),
          "type",
        );
      }
      for (let index = 0; index < parsed.values.length; index += 1) {
        if (field.items === "integer" && !Number.isInteger(parsed.values[index])) {
          return withReason(reasonText("type", { expected: "integer", index }), "type");
        }
        const problem = boundProblem(field, parsed.values[index]);
        if (problem) {
          return withReason(reasonText(problem.reason, { ...problem.details, index }), problem.reason);
        }
      }
      return null;
    }
    case "choice":
      if (!field.choices.some((choice) => choice.value === value)) {
        return withReason(
          reasonText("choice", { allowed: field.choices.map((choice) => choice.value) }),
          "choice",
        );
      }
      return null;
    case "json":
    case "objects": {
      let parsed;
      try {
        parsed = JSON.parse(value);
      } catch (error) {
        return withReason(t(errorTexts.reasons.json, { message: error.message }), "type");
      }
      const wanted = field.kind === "json" ? "object" : "array";
      const actual = Array.isArray(parsed) ? "array" : parsed === null ? "null" : typeof parsed;
      if (actual !== wanted) {
        return withReason(t(errorTexts.reasons.json_kind, { kind: errorTexts.kinds[wanted] }), "type");
      }
      return null;
    }
    case "file-out":
      return FILE_NAME.test(String(value)) ? null : withReason(errorTexts.reasons.file_name, "invalid_path");
    case "text":
      if (field.format === "date" && !isDate(String(value).trim())) {
        return withReason(errorTexts.reasons.date, "format");
      }
      if (field.format === "date-time" && !isDateTime(String(value).trim())) {
        return withReason(errorTexts.reasons["date-time"], "format");
      }
      return null;
    default:
      return null;
  }
}

/**
 * Check a form's values against the catalog: required options (and every member of the
 * chosen `one_of` group), types, bounds, choices, JSON, file names, `format`, `requires`
 * and `excludes`.
 *
 * @param {object} model the result of fieldModel
 * @param {object} values the form's values
 * @returns {Object<string, string>} a message by option name; empty when the form is fine
 */
export function validate(model, values) {
  const found = {};
  for (const field of model.fields) {
    if (!isActive(model, field)) continue;
    const value = values[field.name];
    const message = checkField(field, value, isRequired(model, field, values));
    if (message) {
      found[field.name] = message;
      continue;
    }
    if (!isSet(field, value)) continue;
    const given = (name) => {
      const other = model.fields.find((item) => item.name === name);
      return other ? isActive(model, other) && isSet(other, values[name]) : false;
    };
    const missing = field.requires.filter((name) => !given(name));
    if (missing.length) {
      found[field.name] = withReason(t(errorTexts.reasons.requires, { names: missing.join(", ") }), "requires");
      continue;
    }
    const clashing = field.excludes.filter(given);
    if (clashing.length) {
      found[field.name] = withReason(t(errorTexts.reasons.excludes, { names: clashing.join(", ") }), "excludes");
    }
  }
  return found;
}

/**
 * The options a run sends: the values converted to the catalog's types, only the chosen
 * `one_of` group's fields, nothing for an empty field (the command's default applies), a
 * boolean only when it differs from its default, an output file under "out/".
 *
 * @param {object} model the result of fieldModel
 * @param {object} values the form's values (checked with validate)
 * @returns {object} the options
 */
export function toOptions(model, values) {
  const options = {};
  for (const field of model.fields) {
    if (!isActive(model, field)) continue;
    const value = values[field.name];
    if (!isGiven(field, value)) continue;
    switch (field.kind) {
      case "number":
      case "integer":
        options[field.name] = parseNumber(value);
        break;
      case "series":
        options[field.name] = parseSeries(value).values;
        break;
      case "boolean":
        if (value !== (field.default === null ? false : Boolean(field.default))) {
          options[field.name] = value;
        }
        break;
      case "chips":
        options[field.name] = value.map((item) => String(item));
        break;
      case "json":
      case "objects":
        options[field.name] = JSON.parse(value);
        break;
      case "file-out":
        options[field.name] = `out/${String(value).trim()}`;
        break;
      default:
        options[field.name] = String(value).trim();
    }
  }
  return options;
}

/**
 * The default name of an output file: the basename of the first catalog example's value
 * (plan D11), else the option's name.
 *
 * @param {object} field a field of fieldModel with kind "file-out"
 * @returns {string} the name
 */
export function defaultOutputName(field) {
  const first = field.examples.find((value) => typeof value === "string");
  return first ? first.split(/[\\/]/).pop() : field.name;
}

/**
 * The values of a form opened for the first time: empty, but for the default name of
 * every required output file (where the result is written, not data of the calculation).
 *
 * @param {object} model the result of fieldModel
 * @returns {object} the values
 */
export function outputDefaults(model) {
  const values = {};
  for (const field of model.fields) {
    if (field.kind === "file-out" && field.required) values[field.name] = defaultOutputName(field);
  }
  return values;
}

/**
 * The key of the `one_of` choice in a title: „jedna z trzech”.
 *
 * @param {number} count the count of groups
 * @returns {string} the text
 */
export function oneOfKeyText(count) {
  const word = Object.hasOwn(formTexts.oneOfCounts, count) ? formTexts.oneOfCounts[count] : String(count);
  return t(formTexts.oneOfKey, { count: word });
}
