// The words of the editor's problems and refusals (plan 2026-11-10-network-editor, D7,
// D8): a problem of the structure (editor/graph.js) or an error of Hydrolog with the same
// details (`reason`, `node_id`, `other_id`, `upstream_id`, `nodes`, `downstream`, `type`,
// `found`) in Polish, and why a link or a new inflow is refused, after „Nie można: ”.

import { inputText, num } from "../../format.js";
import { t } from "../../labels/common.js";
import { noticeValue } from "../../labels/notices.js";
import { siec as texts } from "../../labels/siec.js";

/**
 * The noun of a node type, „zlewnia” for a subcatchment.
 *
 * @param {string} type the type
 * @returns {string} the noun (the type itself when unknown)
 */
export function kindNoun(type) {
  return Object.hasOwn(texts.kinds, type) ? texts.kinds[type].noun : String(type);
}

/**
 * What a node of a type takes in `from`, in words, by the bounds of the schema.
 *
 * @param {{fewest: number, most: number|null}|undefined} rule the type's rule (inflowRules)
 * @returns {string} e.g. „przyjmuje dokładnie jeden dopływ”
 */
export function ruleWords(rule) {
  if (!rule) return texts.inflowRules.other;
  if (rule.most === 0) return texts.inflowRules.none;
  if (rule.most === 1) return texts.inflowRules.one;
  if (rule.most === null && rule.fewest >= 1) return texts.inflowRules.some;
  return texts.inflowRules.other;
}

/**
 * A loop in flow order as it is read: „A → B → A”.
 *
 * @param {string[]} nodes the nodes of the cycle in flow order
 * @returns {string} the loop
 */
export function loopWords(nodes) {
  return nodes.length ? [...nodes, nodes[0]].join(" → ") : "–";
}

/**
 * A problem of the structure, or an error of Hydrolog, in Polish.
 *
 * @param {{reason: string, node_id?: string, other_id?: string, upstream_id?: string,
 *   nodes?: string[], downstream?: string[], type?: string, found?: number}} problem the
 *   problem with the library's details
 * @param {Object<string, {fewest: number, most: number|null}>} [rules] inflowRules's, for
 *   the words of `upstream_count`
 * @returns {string|null} the sentence, or null for a reason without a text
 */
export function problemText(problem, rules = {}) {
  const reason = problem.reason;
  if (!Object.hasOwn(texts.reasons, reason)) return null;
  if (reason === "unstable_timestep") return unstableText(problem);
  const nodes = Array.isArray(problem.nodes) ? problem.nodes.map(String) : [];
  return t(texts.reasons[reason], {
    node: problem.node_id ?? "–",
    other: problem.other_id ?? "–",
    up: problem.upstream_id ?? "–",
    nodes: reason === "cycle" ? loopWords(nodes) : nodes.join(", ") || "–",
    down: Array.isArray(problem.downstream) ? problem.downstream.join(", ") : "–",
    found: problem.found ?? "–",
    rule: ruleWords(problem.type ? rules[problem.type] : undefined),
  });
}

/**
 * Whether `unstable_timestep` is a refusal of a step that would have to be divided into so
 * many parts that the hydrograph gets too many ordinates (Muskingum-Cunge, Muskingum: the
 * details give the parts and the most ordinates): a longer step, not another method, mends
 * it.
 *
 * @param {object} details the error's details
 * @returns {boolean} true for that refusal
 */
export function tooManyOrdinates(details) {
  return Number.isFinite(details.substeps) && Number.isFinite(details.maximum) && Number.isFinite(details.timestep_min);
}

/**
 * Whether `unstable_timestep` is Muskingum's refusal of sub-reaches whose weights need a
 * longer step than the network's (fewer than the window's least number): the details give
 * the window of the step for that number (routing/muskingum.py `_explicit_plan`).
 *
 * @param {object} details the error's details
 * @returns {boolean} true for that refusal
 */
export function stepTooShort(details) {
  return (
    details.option === "subreaches" &&
    Number.isFinite(details.value) &&
    Number.isFinite(details.minimum) &&
    details.value < details.minimum &&
    Number.isFinite(details.minimum_timestep_min) &&
    Number.isFinite(details.maximum_timestep_min)
  );
}

/**
 * Why a node cannot be routed at its time step, truthfully by the details: a step too short
 * for the sub-reaches (with the steps that fit them), a step that would need too many
 * ordinates, otherwise a step too long for the method's parameters; each says where the
 * network's step is set.
 *
 * @param {object} details the error's details (`node_id` and the method's numbers)
 * @returns {string} the words
 */
function unstableText(details) {
  const words = texts.unstable;
  const node = details.node_id ?? "–";
  if (stepTooShort(details)) {
    const fits = details.minimum <= details.maximum;
    return t(words.short, {
      node,
      timestep: inputText(details.timestep_min),
      count: details.value,
      shortest: noticeValue(details.minimum_timestep_min),
      longest: noticeValue(details.maximum_timestep_min),
      choice: fits ? t(words.shortCounts, { minimum: details.minimum, maximum: details.maximum }) : words.shortEmpty,
      step: words.step,
    });
  }
  if (tooManyOrdinates(details)) {
    return t(words.ordinates, {
      node,
      timestep: inputText(details.timestep_min),
      substeps: details.substeps,
      maximum: num(details.maximum, 0),
      step: words.step,
    });
  }
  return t(texts.reasons.unstable_timestep, { node, step: words.step });
}

/**
 * Why a Muskingum-Cunge reach of a result was routed as linear reservoirs (ADR-0026: no
 * grid of non-negative weights on the step), from its parameters: the reservoirs and their
 * K, the length, the celerity and the diffusion length; null for any other node.
 *
 * @param {string} id the node
 * @param {object|undefined} parameters the node's parameters in the result
 * @param {number} timestep the network's step [min]
 * @returns {string|null} the note
 */
export function reservoirsText(id, parameters, timestep) {
  if (!parameters || parameters.scheme !== "linear_reservoir") return null;
  const words = texts.reservoirs;
  const length = parameters.length_km * 1000;
  const diffusion = parameters.diffusion_length_m;
  const k = noticeValue(parameters.k_min);
  return t(diffusion > length ? words.longer : words.shorter, {
    node: id,
    what: parameters.n === 1 ? t(words.one, { k }) : t(words.many, { n: parameters.n, k }),
    length: num(length, 1),
    diffusion: num(diffusion, 0),
    celerity: num(parameters.celerity_m_per_s, 2),
    step: inputText(timestep),
  });
}

/**
 * Why a link from one node to another is refused (graph.js linkVerdict), after „Nie
 * można: ”.
 *
 * @param {{reason: string, nodes?: string[], offer?: string}} verdict the refusal
 * @param {Array<{id: string, type: string, from: string[]|null}>} skeleton the structure
 * @param {string} from the node that would flow
 * @param {string} to the node it would flow into
 * @returns {string} e.g. „zlewnia Z2 nie przyjmuje dopływów.”
 */
export function refusalText(verdict, skeleton, from, to) {
  const target = skeleton.find((node) => node.id === to);
  const kind = target ? kindNoun(target.type) : "";
  switch (verdict.reason) {
    case "cycle":
      return t(texts.refusals.cycle, { nodes: loopWords(verdict.nodes || [from]) });
    case "outlet_has_downstream":
      return t(texts.refusals.outlet_has_downstream, { from });
    case "upstream_count":
      if (verdict.offer || (target && target.from && target.from.length)) {
        const have = target && target.from ? target.from.filter((up) => up !== from) : [];
        if (have.length) return t(texts.refusals.full, { kind, to, have: have.join(", ") });
      }
      return t(texts.refusals.upstream_count, { kind, to });
    default:
      return texts.refusals.unknown_upstream;
  }
}

/**
 * Why a node takes no more inflows (D7: „Dodaj dopływ”), after „Nie można: ”; null when
 * it takes one more.
 *
 * @param {{id: string, type: string, from: string[]|null}} node the node
 * @param {Object<string, {fewest: number, most: number|null}>} rules inflowRules's
 * @returns {string|null} the reason, or null
 */
export function fullText(node, rules) {
  const rule = rules[node.type];
  const listed = node.from || [];
  if (!rule || rule.most === null || listed.length < rule.most) return null;
  if (rule.most === 0) return t(texts.refusals.upstream_count, { kind: kindNoun(node.type), to: node.id });
  return t(texts.refusals.full, { kind: kindNoun(node.type), to: node.id, have: listed.join(", ") });
}
