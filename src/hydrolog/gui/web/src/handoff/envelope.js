// The envelope nogat-handoff/1 as the browser checks it: the validation keywords of
// Nogat's schema, schemas/nogat/handoff-1.schema.json (Nogat 8727f6e, copied unchanged;
// Hydrolog never defines the envelope, plan D15), without its annotations ($schema, $id,
// title, description, examples). The page cannot load the copy itself (it lies outside
// the package and names remote identifiers), so tests/e2e/test_exports.py checks that
// these keywords are the copy's, and that handoff/validate.js judges documents as
// jsonschema judges them against the copy. Copy the schema again, then these keywords.

/**
 * Freeze an object and everything in it.
 *
 * @param {object} value the object
 * @returns {object} the same object, frozen
 */
function deepFreeze(value) {
  for (const item of Object.values(value)) if (item && typeof item === "object") deepFreeze(item);
  return Object.freeze(value);
}

/** The validation keywords of nogat-handoff/1. */
export const ENVELOPE_SCHEMA = deepFreeze({
  type: "object",
  required: ["schema", "created_at", "producer", "subject", "provenance", "payload"],
  properties: {
    schema: { const: "nogat-handoff/1" },
    created_at: {
      type: "string",
      format: "date-time",
      pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$",
    },
    producer: { $ref: "#/$defs/producer" },
    subject: { type: "string", minLength: 1 },
    provenance: {
      type: "object",
      propertyNames: { pattern: "^[a-z][a-z0-9_]*$" },
      additionalProperties: { $ref: "#/$defs/origin" },
    },
    payload: { $ref: "#/$defs/payload" },
    result: { $ref: "#/$defs/result" },
  },
  $defs: {
    tool: { type: "string", pattern: "^[a-z][a-z0-9]*$" },
    producer: {
      type: "object",
      required: ["tool", "version"],
      properties: {
        tool: { $ref: "#/$defs/tool" },
        version: { type: "string", minLength: 1 },
        page: { type: "string", minLength: 1 },
      },
    },
    origin: {
      type: "object",
      required: ["source"],
      properties: { source: { type: "string", pattern: "^[a-z][a-z0-9_-]*$" } },
    },
    payload: {
      type: "object",
      required: ["schema"],
      properties: { schema: { type: "string", pattern: "^[a-z][a-z0-9]*-[a-z0-9][a-z0-9-]*/[1-9][0-9]*$" } },
    },
    result: {
      type: "object",
      minProperties: 1,
      properties: {
        command: { type: "string", minLength: 1 },
        computed_with: {
          type: "object",
          required: ["tool", "version"],
          properties: { tool: { $ref: "#/$defs/tool" }, version: { type: "string", minLength: 1 } },
        },
        peak_discharge_m3s: { type: "number", minimum: 0 },
        time_to_peak_min: { type: "number", minimum: 0 },
        total_volume_m3: { type: "number", minimum: 0 },
      },
    },
  },
});
