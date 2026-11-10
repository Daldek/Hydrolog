// The structure of Sieć's network (plan 2026-11-10-network-editor, D7, D8): a pure module
// without Preact or the DOM, which Nogat's kit can wrap (GUI plan D9). It checks the
// structure synchronously after every edit with ADR-0010's reasons and the library's codes
// (`RoutingNetwork.from_document`), every problem at once where the library stops at the
// first: the ids (the pattern and length, the device names of Windows, uniqueness without
// regard to case), the inflows of each node (their count from the `from` bounds of the
// network's schema, unknown and repeated ones), the downstream links, cycles, the outlet,
// and nodes that flow nowhere. It also judges a link before it is made (a cycle, an
// inflow into a subcatchment, a link out of the outlet, a second inflow where only one is
// taken, which offers a junction) and an id as it is typed. A structure is the section's
// skeleton: `[{id, type, from}]`, `from` null or the ids of the inflows.

/** The structure reasons the editor reports, in the library's vocabulary (ADR-0010). */
export const REASONS = Object.freeze([
  "empty",
  "invalid_id",
  "reserved_name",
  "duplicate_node",
  "unknown_upstream",
  "duplicate_upstream",
  "upstream_count",
  "several_downstream",
  "cycle",
  "no_outlet",
  "several_outlets",
  "outlet_has_downstream",
  "disconnected_node",
]);

/** The reasons of the whole network: in the list of problems only, on no node (D8). */
export const NETWORK_REASONS = Object.freeze(["empty", "no_outlet", "several_outlets"]);

/** The longest id: it names the file of its node (the library's MAX_ID_CHARS). */
export const MAX_ID_CHARS = 64;

/** An id as the library reads it (Python's `\w[\w.-]*`): a letter, a digit or `_` first. */
const WORD = /^[\p{L}\p{N}_][\p{L}\p{N}_.-]*$/u;

/** The device names of Windows, with any extension and in any case (the library's). */
const RESERVED = /^(?:con|prn|aux|nul|(?:com|lpt)[1-9\u00b9\u00b2\u00b3])(?:\..*)?$/isu;

/**
 * An id without regard to case, as the library compares ids (`str.casefold`): upper case
 * and then lower case folds „ß” to „ss” and „ς” to „σ” as casefold does.
 *
 * @param {string} id an id
 * @returns {string} the folded id
 */
export function foldId(id) {
  return String(id).toUpperCase().toLowerCase();
}

/**
 * What is wrong with an id itself, as the library checks it.
 *
 * @param {unknown} id an id
 * @returns {null|"invalid_id"|"reserved_name"} null for a valid id
 */
export function idReason(id) {
  if (typeof id !== "string" || [...id].length > MAX_ID_CHARS || !WORD.test(id) || id.endsWith(".")) return "invalid_id";
  return RESERVED.test(id) ? "reserved_name" : null;
}

/**
 * Whether an id names another node of the structure without regard to case.
 *
 * @param {string} id the id
 * @param {Array<{id: string}>} skeleton the structure
 * @param {string|null} [self] the id of the node that would take it (not counted)
 * @returns {string|null} the id of the other node, or null
 */
function sameId(id, skeleton, self = null) {
  const folded = foldId(id);
  const other = skeleton.find((node) => node.id !== self && foldId(node.id) === folded);
  return other ? other.id : null;
}

/**
 * The problem of an id typed for a node (D7: renaming), as the library would refuse it.
 *
 * @param {string} id the id typed
 * @param {Array<{id: string}>} skeleton the structure
 * @param {string|null} [self] the node's current id (not a duplicate of itself), null for
 *   a new node
 * @returns {null|"invalid_id"|"reserved_name"|"duplicate_node"} null when the id is free
 *   and valid
 */
export function idProblem(id, skeleton, self = null) {
  const reason = idReason(id);
  if (reason) return reason;
  return sameId(id, skeleton, self) ? "duplicate_node" : null;
}

/**
 * Follow a local `$ref` of a schema.
 *
 * @param {object} schema the whole schema
 * @param {object} part a part of it
 * @returns {object} the part referred to (the part itself without a reference)
 */
function resolve(schema, part) {
  let current = part || {};
  const seen = new Set();
  while (typeof current.$ref === "string" && current.$ref.startsWith("#/") && !seen.has(current.$ref)) {
    seen.add(current.$ref);
    current =
      current.$ref
        .slice(2)
        .split("/")
        .reduce((at, key) => (at && typeof at === "object" ? at[key] : undefined), schema) || {};
  }
  return current;
}

/**
 * The inflows each node type takes, from the `from` bounds of the node branches of
 * hydrolog-network-1.schema.json (`minItems`, `maxItems`): the GUI keeps no copy of them.
 *
 * @param {object} schema hydrolog-network-1.schema.json
 * @returns {Object<string, {fewest: number, most: number|null}>} by type; `most` null for
 *   no limit (a junction)
 */
export function inflowRules(schema) {
  const rules = {};
  const node = resolve(schema, ((schema && schema.$defs) || {}).node);
  for (const item of node.oneOf || []) {
    const branch = resolve(schema, item);
    const properties = branch.properties || {};
    const type = properties.type ? properties.type.const : null;
    if (typeof type !== "string") continue;
    const from = resolve(schema, properties.from);
    const fewest = Number.isInteger(from.minItems) ? from.minItems : 0;
    const most = Number.isInteger(from.maxItems) ? from.maxItems : null;
    const known = rules[type];
    rules[type] = known
      ? { fewest: Math.min(known.fewest, fewest), most: known.most === null || most === null ? null : Math.max(known.most, most) }
      : { fewest, most };
  }
  return Object.freeze(Object.fromEntries(Object.entries(rules).map(([type, rule]) => [type, Object.freeze(rule)])));
}

/**
 * The known inflows of every node: the ids of its `from` that are nodes, each once.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @returns {Map<string, string[]>} by id, in the order of `from`
 */
function inflowsOf(skeleton) {
  const ids = new Set(skeleton.map((node) => node.id));
  return new Map(skeleton.map((node) => [node.id, [...new Set(node.from || [])].filter((up) => ids.has(up))]));
}

/**
 * The nodes each node flows into: those that list it.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @returns {Map<string, string[]>} by id, in the order of the structure
 */
export function receiversOf(skeleton) {
  const receivers = new Map(skeleton.map((node) => [node.id, []]));
  for (const [id, inflows] of inflowsOf(skeleton)) {
    for (const up of inflows) receivers.get(up).push(id);
  }
  return receivers;
}

/**
 * The nodes that cannot be ordered upstream first (Kahn's algorithm): those in a cycle and
 * those below one.
 *
 * @param {Map<string, string[]>} inflows the inflows by id
 * @param {Set<string>} within the ids considered (a link from outside them is free)
 * @returns {Set<string>} the blocked ids
 */
function blockedOf(inflows, within) {
  const waiting = new Map();
  const down = new Map([...within].map((id) => [id, []]));
  for (const id of within) {
    const listed = inflows.get(id).filter((up) => within.has(up));
    waiting.set(id, listed.length);
    for (const up of listed) down.get(up).push(id);
  }
  const ready = [...within].filter((id) => waiting.get(id) === 0);
  const done = new Set();
  while (ready.length) {
    const id = ready.pop();
    done.add(id);
    for (const next of down.get(id)) {
      waiting.set(next, waiting.get(next) - 1);
      if (waiting.get(next) === 0) ready.push(next);
    }
  }
  return new Set([...within].filter((id) => !done.has(id)));
}

/**
 * The smallest of some ids, as Python orders strings.
 *
 * @param {Iterable<string>} ids the ids
 * @returns {string} the smallest
 */
function smallest(ids) {
  let found = null;
  for (const id of ids) if (found === null || id < found) found = id;
  return found;
}

/**
 * One cycle among blocked nodes, as the library finds it: the walk upstream from the
 * smallest blocked id through the first blocked inflow, in flow order from its smallest id.
 *
 * @param {Map<string, string[]>} inflows the inflows by id
 * @param {Set<string>} blocked the blocked ids
 * @returns {string[]} the nodes of the cycle in flow order
 */
function cycleIn(inflows, blocked) {
  const walk = [];
  const position = new Map();
  let current = smallest(blocked);
  while (!position.has(current)) {
    position.set(current, walk.length);
    walk.push(current);
    current = inflows.get(current).find((up) => blocked.has(up));
  }
  const cycle = walk.slice(position.get(current)).reverse();
  const start = cycle.indexOf(smallest(cycle));
  return [...cycle.slice(start), ...cycle.slice(0, start)];
}

/**
 * Every cycle of a structure, each once: the first is the one the library names; the
 * nodes below a cycle are not in one.
 *
 * @param {Array<{id: string, from: string[]|null}>} skeleton the structure
 * @returns {string[][]} the cycles, each in flow order from its smallest id
 */
export function cyclesOf(skeleton) {
  const inflows = inflowsOf(skeleton);
  const cycles = [];
  let left = new Set(inflows.keys());
  for (;;) {
    const blocked = blockedOf(inflows, left);
    if (!blocked.size) return cycles;
    const cycle = cycleIn(inflows, blocked);
    cycles.push(cycle);
    const gone = new Set(cycle);
    left = new Set([...left].filter((id) => !gone.has(id)));
  }
}

/**
 * The nodes a problem marks on the canvas: none for a problem of the whole network.
 *
 * @param {{reason: string, node_id?: string, listed_by?: string, nodes?: string[]}} problem
 *   a problem of graphProblems
 * @returns {string[]} the ids
 */
export function problemNodes(problem) {
  if (NETWORK_REASONS.includes(problem.reason)) return [];
  if (problem.reason === "cycle") return [...problem.nodes];
  if (problem.listed_by) return [problem.listed_by];
  return problem.node_id ? [problem.node_id] : [];
}

/**
 * Every problem of a structure at once, with the library's reasons and details:
 * `empty`; per node `invalid_id` and `reserved_name` (also of an id in `from` that is not
 * a node, `listed_by` the node that lists it), `duplicate_node` (`other_id` the earlier),
 * `upstream_count` (`type`, `found`), `duplicate_upstream`, `unknown_upstream`
 * (`upstream_id`), `several_downstream` (`downstream`), `outlet_has_downstream`
 * (`downstream`) and `disconnected_node` (a node other than an outlet that flows nowhere);
 * `cycle` with its `nodes` in flow order; `no_outlet` and `several_outlets` (`nodes`). The
 * problems of the whole network come first, then those of each node in the order of the
 * structure.
 *
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @param {Object<string, {fewest: number, most: number|null}>} rules inflowRules's
 * @returns {Array<{reason: string, node_id?: string, nodes?: string[]}>} the problems
 */
export function graphProblems(skeleton, rules) {
  if (!skeleton.length) return [{ reason: "empty" }];
  const found = [];
  const ids = new Set(skeleton.map((node) => node.id));
  const folded = new Map();
  for (const node of skeleton) {
    const reason = idReason(node.id);
    if (reason) found.push({ reason, node_id: node.id });
    const key = foldId(node.id);
    if (folded.has(key)) found.push({ reason: "duplicate_node", node_id: node.id, other_id: folded.get(key) });
    else folded.set(key, node.id);
  }
  for (const node of skeleton) {
    const listed = node.from || [];
    const rule = rules[node.type];
    if (rule && (listed.length < rule.fewest || (rule.most !== null && listed.length > rule.most))) {
      found.push({ reason: "upstream_count", node_id: node.id, type: node.type, found: listed.length });
    }
    if (new Set(listed).size !== listed.length) found.push({ reason: "duplicate_upstream", node_id: node.id });
    for (const up of new Set(listed)) {
      if (ids.has(up)) continue;
      const reason = idReason(up);
      if (reason) found.push({ reason, node_id: String(up), listed_by: node.id });
      else found.push({ reason: "unknown_upstream", node_id: node.id, upstream_id: up });
    }
  }
  const receivers = receiversOf(skeleton);
  for (const node of skeleton) {
    const down = receivers.get(node.id);
    if (down.length > 1) found.push({ reason: "several_downstream", node_id: node.id, downstream: [...down] });
  }
  for (const cycle of cyclesOf(skeleton)) found.push({ reason: "cycle", nodes: cycle });
  const outlets = skeleton.filter((node) => node.type === "outlet").map((node) => node.id);
  if (!outlets.length) found.push({ reason: "no_outlet" });
  if (outlets.length > 1) found.push({ reason: "several_outlets", nodes: outlets });
  for (const id of outlets) {
    if (receivers.get(id).length) found.push({ reason: "outlet_has_downstream", node_id: id, downstream: [...receivers.get(id)] });
  }
  for (const node of skeleton) {
    if (node.type !== "outlet" && !receivers.get(node.id).length) found.push({ reason: "disconnected_node", node_id: node.id });
  }
  const order = new Map(skeleton.map((node, index) => [node.id, index]));
  const rank = (problem) => {
    const marked = problemNodes(problem);
    const at = marked.length && order.has(marked[0]) ? order.get(marked[0]) : -1;
    return [NETWORK_REASONS.includes(problem.reason) ? 0 : 1, at, REASONS.indexOf(problem.reason)];
  };
  return found
    .map((problem, index) => ({ problem, key: [...rank(problem), index] }))
    .sort((a, b) => {
      for (let at = 0; at < a.key.length; at += 1) if (a.key[at] !== b.key[at]) return a.key[at] - b.key[at];
      return 0;
    })
    .map((item) => item.problem);
}

/**
 * The path downstream from one node to another, if there is one.
 *
 * @param {Map<string, string[]>} receivers receiversOf's
 * @param {string} start the first node
 * @param {string} goal the node to reach
 * @returns {string[]|null} the nodes from `start` to `goal`, or null
 */
function pathDown(receivers, start, goal) {
  const before = new Map([[start, null]]);
  const queue = [start];
  while (queue.length) {
    const id = queue.shift();
    if (id === goal) {
      const path = [];
      for (let at = id; at !== null; at = before.get(at)) path.unshift(at);
      return path;
    }
    for (const next of receivers.get(id) || []) {
      if (!before.has(next)) {
        before.set(next, id);
        queue.push(next);
      }
    }
  }
  return null;
}

/**
 * Whether a node may flow into another (D7: connecting moves its one downstream link):
 * refused when it would close a cycle (`cycle`, with the loop in flow order from `from`),
 * when the outlet would flow on (`outlet_has_downstream`), when the target takes no
 * inflow (`upstream_count`: a subcatchment) or no more inflows (`upstream_count` with the
 * offer of a junction that takes both: a reach, a reservoir or the outlet).
 *
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @param {Object<string, {fewest: number, most: number|null}>} rules inflowRules's
 * @param {string} from the node that would flow
 * @param {string} to the node it would flow into
 * @returns {{ok: true}|{ok: false, reason: string, nodes?: string[], offer?: "junction"}}
 *   the verdict
 */
export function linkVerdict(skeleton, rules, from, to) {
  if (from === to) return { ok: false, reason: "cycle", nodes: [from] };
  const source = skeleton.find((node) => node.id === from);
  const target = skeleton.find((node) => node.id === to);
  if (!source || !target) return { ok: false, reason: "unknown_upstream" };
  if (source.type === "outlet") return { ok: false, reason: "outlet_has_downstream" };
  const rule = rules[target.type] || { fewest: 0, most: null };
  if (rule.most === 0) return { ok: false, reason: "upstream_count" };
  const loop = pathDown(receiversOf(skeleton), to, from);
  if (loop) return { ok: false, reason: "cycle", nodes: [from, ...loop.slice(0, -1)] };
  const others = (target.from || []).filter((up) => up !== from);
  if (rule.most !== null && others.length + 1 > rule.most) return { ok: false, reason: "upstream_count", offer: "junction" };
  return { ok: true };
}
