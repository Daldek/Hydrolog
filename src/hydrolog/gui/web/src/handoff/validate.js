// A check of a JSON value against a JSON Schema of draft 2020-12, with the keywords that
// Nogat's nogat-handoff/1 and Hydrolog's hydrolog-network-1.schema.json use: type, const,
// enum, the bounds of numbers, strings and arrays, pattern, required, properties,
// additionalProperties, propertyNames, minProperties, dependentRequired, items,
// uniqueItems, not, allOf, anyOf, oneOf and local $ref. Annotations (title, description,
// default, examples, format) check nothing, as in jsonschema without a format checker;
// `\w` in a pattern means a Unicode word character, as in Python's `re`.
//
// A problem names the path of the value, the keyword it breaks and the keyword's values;
// handoff.js words it in Polish. Where no branch of a oneOf fits an object, the problems
// are those of the branch its constants (`type`, `method`, `model`, `kind`) choose, or
// the constant that chooses none.

/**
 * A problem of a value.
 *
 * @typedef {{path: Array<string|number>, keyword: string, params: object}} Problem
 */

/**
 * A JSON value as text with the keys of every object sorted: equal values give equal
 * texts (1 and 1.0 alike, true and 1 not).
 *
 * @param {unknown} value a JSON value
 * @returns {string} the text
 */
export function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value === undefined ? null : value);
}

/**
 * Whether a value is a JSON object (not an array, not null).
 *
 * @param {unknown} value the value
 * @returns {boolean} true for an object
 */
export function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/**
 * Whether a value has a JSON Schema type.
 *
 * @param {unknown} value the value
 * @param {string} type "object", "array", "string", "number", "integer", "boolean" or "null"
 * @returns {boolean} true when it has
 */
function hasType(value, type) {
  switch (type) {
    case "object":
      return isObject(value);
    case "array":
      return Array.isArray(value);
    case "string":
      return typeof value === "string";
    case "number":
      return typeof value === "number" && Number.isFinite(value);
    case "integer":
      return Number.isInteger(value);
    case "boolean":
      return typeof value === "boolean";
    case "null":
      return value === null;
    default:
      return true;
  }
}

const patterns = new Map();

/**
 * A pattern of a schema as a regular expression: `\w` and `\W` as Python's `re` reads them
 * in a str pattern (letters, digits and "_" of any script), searched anywhere in the text.
 *
 * @param {string} pattern the pattern
 * @returns {RegExp} the expression
 */
function regexOf(pattern) {
  let found = patterns.get(pattern);
  if (found) return found;
  let source = "";
  let inClass = false;
  for (let index = 0; index < pattern.length; index += 1) {
    const char = pattern[index];
    if (char === "\\" && index + 1 < pattern.length) {
      const next = pattern[index + 1];
      if (next === "w") source += inClass ? "\\p{L}\\p{N}_" : "[\\p{L}\\p{N}_]";
      else if (next === "W" && !inClass) source += "[^\\p{L}\\p{N}_]";
      else source += char + next;
      index += 1;
      continue;
    }
    if (char === "[" && !inClass) inClass = true;
    else if (char === "]" && inClass) inClass = false;
    source += char;
  }
  try {
    found = new RegExp(source, "u");
  } catch {
    found = new RegExp(pattern);
  }
  patterns.set(pattern, found);
  return found;
}

/**
 * The part of a schema a local reference points to ("#/$defs/node").
 *
 * @param {object} root the whole schema
 * @param {string} ref the reference
 * @returns {object|boolean} the part (true, which allows everything, when not found)
 */
function pointer(root, ref) {
  if (ref === "#") return root;
  if (!ref.startsWith("#/")) return true;
  let at = root;
  for (const raw of ref.slice(2).split("/")) {
    const key = raw.replace(/~1/g, "/").replace(/~0/g, "~");
    if (!at || typeof at !== "object" || !Object.hasOwn(at, key)) return true;
    at = at[key];
  }
  return at;
}

/**
 * A schema with its references followed while it is only a reference.
 *
 * @param {object} root the whole schema
 * @param {object|boolean} schema a part of it
 * @returns {object|boolean} the part it stands for
 */
function deref(root, schema) {
  let at = schema;
  const seen = new Set();
  while (isObject(at) && typeof at.$ref === "string" && !seen.has(at.$ref)) {
    seen.add(at.$ref);
    at = pointer(root, at.$ref);
  }
  return at;
}

/**
 * The constants of a branch's properties (`type`, `method`, …), which choose it.
 *
 * @param {object} root the whole schema
 * @param {object|boolean} branch the branch
 * @returns {Array<[string, unknown]>} property names and their constants
 */
function constantsOf(root, branch) {
  const base = deref(root, branch);
  if (!isObject(base) || !isObject(base.properties)) return [];
  const found = [];
  for (const [name, property] of Object.entries(base.properties)) {
    const resolved = deref(root, property);
    if (isObject(resolved) && Object.hasOwn(resolved, "const")) found.push([name, resolved.const]);
  }
  return found;
}

/**
 * How far a value is from a branch by its problems: an unknown or missing field of the
 * value itself weighs as much as ten problems deeper, since the branch then does not
 * describe the value at all.
 *
 * @param {Problem[]} problems the problems of the branch
 * @param {number} depth the length of the value's path
 * @returns {number} the distance
 */
function distance(problems, depth) {
  let total = 0;
  for (const problem of problems) {
    const own = problem.path.length === depth && (problem.keyword === "additionalProperties" || problem.keyword === "required");
    total += own ? 10 : 1;
  }
  return total;
}

/**
 * The problems of the oneOf of a schema.
 *
 * @param {object} schema the schema with `oneOf`
 * @param {unknown} value the value
 * @param {object} root the whole schema
 * @param {Array<string|number>} path the path of the value
 * @param {Problem[]} out where the problems go
 */
function checkOneOf(schema, value, root, path, out) {
  const branches = schema.oneOf;
  const results = branches.map((branch) => schemaProblems(branch, value, root, path));
  const far = results.map((problems) => distance(problems, path.length));
  const passing = results.filter((problems) => problems.length === 0).length;
  if (passing === 1) return;
  if (passing > 1) {
    out.push({ path, keyword: "oneOfMany", params: {} });
    return;
  }
  if (isObject(value)) {
    const scored = branches.map((branch, index) => {
      const fixed = constantsOf(root, branch);
      const missed = fixed.filter(([name, constant]) => !(Object.hasOwn(value, name) && canonical(value[name]) === canonical(constant)));
      return { index, fixed, matched: fixed.length - missed.length, missed };
    });
    const most = Math.max(...scored.map((item) => item.matched));
    const close = scored.filter((item) => item.matched === most);
    const least = Math.min(...close.map((item) => item.missed.length));
    const pool = close.filter((item) => item.missed.length === least);
    if (least > 0) {
      const names = pool[0].missed.map(([name]) => name);
      const name = names.find((candidate) => pool.every((item) => item.missed.some(([other]) => other === candidate))) || names[0];
      const allowed = [];
      for (const item of scored) {
        for (const [other, constant] of item.fixed) {
          if (other === name && !allowed.some((known) => canonical(known) === canonical(constant))) allowed.push(constant);
        }
      }
      if (Object.hasOwn(value, name)) out.push({ path: [...path, name], keyword: "enum", params: { allowed } });
      else out.push({ path, keyword: "required", params: { name } });
      return;
    }
    const best = pool.reduce((a, b) => (far[b.index] < far[a.index] ? b : a));
    out.push(...results[best.index]);
    return;
  }
  let closest = 0;
  for (let index = 1; index < results.length; index += 1) if (far[index] < far[closest]) closest = index;
  out.push(...(results[closest].length ? results[closest] : [{ path, keyword: "oneOf", params: {} }]));
}

/**
 * Check a value against a schema, keyword by keyword.
 *
 * @param {object|boolean} schema the schema (or a part of `root`)
 * @param {unknown} value the value
 * @param {object} root the whole schema, for `$ref`
 * @param {Array<string|number>} path the path of the value
 * @param {Problem[]} out where the problems go
 */
function check(schema, value, root, path, out) {
  if (schema === true || schema === undefined || schema === null) return;
  if (schema === false) {
    out.push({ path, keyword: "false", params: {} });
    return;
  }
  if (typeof schema.$ref === "string") check(pointer(root, schema.$ref), value, root, path, out);
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => hasType(value, type))) {
      out.push({ path, keyword: "type", params: { types } });
      return;
    }
  }
  if (Object.hasOwn(schema, "const") && canonical(value) !== canonical(schema.const)) {
    out.push({ path, keyword: "const", params: { value: schema.const } });
  }
  if (Array.isArray(schema.enum) && !schema.enum.some((item) => canonical(item) === canonical(value))) {
    out.push({ path, keyword: "enum", params: { allowed: schema.enum } });
  }
  if (typeof value === "number") {
    if (typeof schema.minimum === "number" && value < schema.minimum) out.push({ path, keyword: "minimum", params: { limit: schema.minimum } });
    if (typeof schema.maximum === "number" && value > schema.maximum) out.push({ path, keyword: "maximum", params: { limit: schema.maximum } });
    if (typeof schema.exclusiveMinimum === "number" && !(value > schema.exclusiveMinimum)) {
      out.push({ path, keyword: "exclusiveMinimum", params: { limit: schema.exclusiveMinimum } });
    }
    if (typeof schema.exclusiveMaximum === "number" && !(value < schema.exclusiveMaximum)) {
      out.push({ path, keyword: "exclusiveMaximum", params: { limit: schema.exclusiveMaximum } });
    }
  }
  if (typeof value === "string") {
    const length = [...value].length;
    if (typeof schema.minLength === "number" && length < schema.minLength) out.push({ path, keyword: "minLength", params: { limit: schema.minLength } });
    if (typeof schema.maxLength === "number" && length > schema.maxLength) out.push({ path, keyword: "maxLength", params: { limit: schema.maxLength } });
    if (typeof schema.pattern === "string" && !regexOf(schema.pattern).test(value)) out.push({ path, keyword: "pattern", params: { pattern: schema.pattern } });
  }
  if (Array.isArray(value)) {
    if (typeof schema.minItems === "number" && value.length < schema.minItems) out.push({ path, keyword: "minItems", params: { limit: schema.minItems } });
    if (typeof schema.maxItems === "number" && value.length > schema.maxItems) out.push({ path, keyword: "maxItems", params: { limit: schema.maxItems } });
    if (schema.uniqueItems === true && new Set(value.map(canonical)).size !== value.length) out.push({ path, keyword: "uniqueItems", params: {} });
    if (schema.items !== undefined) value.forEach((item, index) => check(schema.items, item, root, [...path, index], out));
  }
  if (isObject(value)) {
    for (const name of Array.isArray(schema.required) ? schema.required : []) {
      if (!Object.hasOwn(value, name)) out.push({ path, keyword: "required", params: { name } });
    }
    const properties = isObject(schema.properties) ? schema.properties : {};
    for (const [name, item] of Object.entries(value)) {
      if (Object.hasOwn(properties, name)) check(properties[name], item, root, [...path, name], out);
      else if (schema.additionalProperties === false) out.push({ path, keyword: "additionalProperties", params: { name } });
      else if (schema.additionalProperties !== undefined) check(schema.additionalProperties, item, root, [...path, name], out);
    }
    if (schema.propertyNames !== undefined) {
      for (const name of Object.keys(value)) {
        if (schemaProblems(schema.propertyNames, name, root, path).length) out.push({ path, keyword: "propertyNames", params: { name } });
      }
    }
    if (typeof schema.minProperties === "number" && Object.keys(value).length < schema.minProperties) {
      out.push({ path, keyword: "minProperties", params: { limit: schema.minProperties } });
    }
    if (isObject(schema.dependentRequired)) {
      for (const [name, needed] of Object.entries(schema.dependentRequired)) {
        if (!Object.hasOwn(value, name)) continue;
        for (const other of needed) {
          if (!Object.hasOwn(value, other)) out.push({ path, keyword: "dependentRequired", params: { name, needed: other } });
        }
      }
    }
  }
  if (schema.not !== undefined && schemaProblems(schema.not, value, root, path).length === 0) {
    out.push({ path, keyword: "not", params: {} });
  }
  if (Array.isArray(schema.allOf)) for (const branch of schema.allOf) check(branch, value, root, path, out);
  if (Array.isArray(schema.anyOf)) {
    const results = schema.anyOf.map((branch) => schemaProblems(branch, value, root, path));
    if (!results.some((problems) => problems.length === 0)) {
      const closest = results.reduce((a, b) => (distance(b, path.length) < distance(a, path.length) ? b : a));
      out.push(...(closest.length ? closest : [{ path, keyword: "oneOf", params: {} }]));
    }
  }
  if (Array.isArray(schema.oneOf)) checkOneOf(schema, value, root, path, out);
}

/**
 * The problems of a value against a schema; none when the value is valid.
 *
 * @param {object|boolean} schema the schema, or a part of `root`
 * @param {unknown} value the value
 * @param {object} [root] the whole schema, for `$ref` (default: `schema`)
 * @param {Array<string|number>} [path] the path of the value, a prefix of every problem's
 * @returns {Problem[]} the problems
 */
export function schemaProblems(schema, value, root = schema, path = []) {
  const out = [];
  check(schema, value, root, path, out);
  return out;
}
