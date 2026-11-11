// „Sieć i trasowanie” (plan S4; the approved mockup with the author's revisions; plan
// 2026-11-10-network-editor): a river network of hydrolog-network/1, built here on the
// canvas of „Schemat sieci” („Nowa sieć”), opened from a file or a hand-off (the guide,
// instrukcja/#siec, has a worked example to load), and drawn vertically from the
// section's own inputs (D1, D6: the sources at the top, the outlet at the bottom, every
// node on the cell of its position). The person adds elements, connects, disconnects,
// removes, renames and describes them on the canvas or in „Dane” (D7), adds the
// subcatchments of a hand-off („Dodaj zlewnię z Hydrografa”, D10), and every edit is a
// step of the history („Cofnij”, „Ponów”, D9). The structure is checked in the browser
// after every edit with the library's reasons (editor/graph.js, D8) and the problems mark
// their nodes. As soon as the structure has no problem Hydrolog lays it out
// (`route schematic --structure-only`, ADR-0025; plan 2026-11-10-network-wizard, D8:
// 300 ms after a change of the structure or of a subcatchment's area, whatever values the
// nodes still miss), and that layout places a network opened without positions and
// serves „Uporządkuj”; once the values are complete too Hydrolog checks the whole network
// (`route schematic`, 300 ms after the last change). A click on a node, Enter or Space,
// or its row in a table opens its settings in „Dane” and its result in „Wyniki”.
// The network's rainfall comes first, in step 1 (plan 2026-11-10-network-wizard, D4): „Nowa
// sieć” opens there and the empty canvas says so; a PMAXTP depth is fetched on the channel
// "siec-pmaxtp" (usePmaxtp, as Hydrogram zlewni fetches its own) and kept with the
// network's values, and a subcatchment that has neither its own rainfall nor the network's
// is a problem of its node („Brak opadu”) before „Oblicz sieć”.
// A chosen subcatchment made from rainfall opens its panel beside „Dane” (D1, D2: the
// layout's `detail`; on a phone the two sheets alternate): Hydrogram zlewni's own three
// steps (SubcatchmentSteps) on the node's inputs, checked by Hydrogram's checks, with the
// values the last „Oblicz sieć” gave the node while it is unchanged since and the warnings
// of its notices; its own PMAXTP depth is fetched on "siec-node-pmaxtp", and „Wczytaj z
// Hydrografa” of its step 1 fills the node from a hand-off of one watershed (D10). Choosing
// a node opens or changes the panel without moving the focus, Enter on a subcatchment moves
// it to the panel's first step, and ✕ closes the panel while the node stays chosen.
// A node that came in a hand-off shows where its inputs came from (D9: handoff/mapping.js
// siecOrigins): a subcatchment in its panel's steps, any other node in „Dane”'s step 3.
// The network is computed on „Oblicz sieć” only: the document, positions and descriptions
// included, is written to the session's `in/` and `route network` routes it (with the
// inflows file and the rating files it reads); a change of the structure or the values
// afterwards marks the result stale („Dane zmienione: oblicz ponownie”, plan D13), a move
// or a description never does (D11). „Zapisz sieć” saves a complete network, „Zapisz
// szkic” an incomplete one; „Wyczyść” and „Nowa sieć” ask first when the network changed
// since it was opened or saved (D10).

import { api } from "../../api.js";
import { splitReason } from "../../controls/field.js";
import { inputFiles, uploadFile, useSession } from "../../controls/file-field.js";
import { plural } from "../../format.js";
import { withReason } from "../../forms/model.js";
import { panelOrigins, siecAddition, siecFill, siecInputs, siecOrigins } from "../../handoff/mapping.js";
import { canonical } from "../../handoff/validate.js";
import { html, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError } from "../../labels/errors.js";
import { handoffLabels as handoffTexts } from "../../labels/handoff.js";
import { hydrogram as rainTexts } from "../../labels/hydrogram.js";
import { routing } from "../../labels/info/routing.js";
import { siec as texts } from "../../labels/siec.js";
import { shell } from "../../labels/shell.js";
import { usePersistentState } from "../../persist.js";
import { navigate } from "../../router.js";
import { useStore } from "../../store.js";
import { ConfirmDialog } from "../../ui/confirm.js";
import { downloadBlob } from "../../ui/export-panel.js";
import { registerInfo } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { isPhone, openPanel } from "../../ui/sheet.js";
import { status } from "../../ui/status.js";
import { toast } from "../../ui/toast.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { usePmaxtp } from "../hydrogram/pmaxtp.js";
import {
  PMAXTP_FIELDS,
  checkInputs,
  checkedValues,
  fieldLabel,
  panelFields,
  pmaxtpDepth,
  pmaxtpKey,
  pmaxtpOptions,
  requirements,
} from "../hydrogram/state.js";
import { SubcatchmentSteps, readWatershedFile } from "../hydrogram/steps.js";
import { DataPanel, EmptyNetwork, networkRainWords, networkSummary, showNetworkRain } from "./data-panel.js";
import { NetworkCanvas } from "./editor/canvas.js";
import { addNode, canBridge, cellBeside, connect, describeNode, disconnect, insertJunction, placeAll, removeNode, renameNode } from "./editor/edits.js";
import { graphProblems, linkVerdict, problemNodes, receiversOf, structureKey } from "./editor/graph.js";
import { createHistory } from "./editor/history.js";
import { nodeWords, variantOf, withoutPicture } from "./node-model.js";
import { NodeTable, ResultsPanel } from "./results-panel.js";
import {
  buildDocument,
  changedSinceSaved,
  documentName,
  documentProblems,
  fileStem,
  initialState,
  inputsKey,
  neededFiles,
  newState,
  NO_RAINFALL_KEY,
  nodeComputed,
  placementNotes,
  placeSkeleton,
  SECTION,
  stateOf,
  structureDocument,
  useForms,
  useOpened,
  withSessionNames,
} from "./state.js";
import { kindNoun, problemText, refusalText } from "./words.js";

registerInfo(routing);

/** Delay of Hydrolog's layout and check after the last change of the network [ms]. */
export const SCHEMATIC_DELAY_MS = 300;

/** The channel of Hydrolog's check of a complete network (the runs use the section's). */
export const SCHEMATIC_CHANNEL = "siec-schematic";

/** The channel of Hydrolog's layout of the structure alone (ADR-0025). */
export const LAYOUT_CHANNEL = "siec-layout";

/** The channel of the fetches of the depth of the network's PMAXTP (plan 2026-11-10-network-wizard, D4). */
export const PMAXTP_CHANNEL = "siec-pmaxtp";

/** The channel of the fetches of the PMAXTP depth of the chosen subcatchment's own rainfall (D1). */
export const NODE_PMAXTP_CHANNEL = "siec-node-pmaxtp";

/** The prefix of the ids of the subcatchment's panel (D1): the steps of Hydrogram zlewni are „hg”. */
const PANEL_PREFIX = "sn";

/** The choices of the network's rainfall: each a step of the history of its own (D9). */
const RAIN_CHOICES = new Set(["rain_source", "hietogram_type"]);

/** The choices of a subcatchment's steps: each a step of the history of its own (D9). */
const STEP_CHOICES = new Set([
  "uh_model",
  "tc_method",
  "tc_manual",
  "nash_source",
  "clark_kind",
  "amc",
  "rain_source",
  "hietogram_type",
  "pmaxtp_probability_pct",
  "pmaxtp_duration_min",
  "pmaxtp_method",
]);

/** The fields of the network's PMAXTP that must pass their checks before its depth is fetched. */
const PMAXTP_NAMES = new Set(Object.values(PMAXTP_FIELDS));

/** The most steps the history keeps (D9). */
export const HISTORY_STEPS = 100;

/** Hydrolog's check of the complete network before it is asked for. */
const NO_CHECK = Object.freeze({ key: null, error: null });

/** Hydrolog's layout of the structure before it is asked for. */
const NO_LAYOUT = Object.freeze({ key: null, positions: null, error: null });

/**
 * The part of the state the history keeps (D9): the network's values, its structure and
 * the values of its nodes.
 *
 * @param {object} state the section's state
 * @returns {{network: object, skeleton: object[], nodes: Object<string, object>}} the step
 */
function stepOf(state) {
  return { network: state.network, skeleton: state.skeleton, nodes: state.nodes };
}

/**
 * The keys of the values that differ between two sets of values.
 *
 * @param {object} before the values before
 * @param {object} after the values after
 * @returns {string[]} the keys
 */
function changedKeys(before, after) {
  const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
  return [...keys].filter((key) => JSON.stringify(before[key]) !== JSON.stringify(after[key]));
}

/**
 * The key under which typing into one field stays one step of the history (D9): the
 * field's own; a choice (a key with "#", but not the rows of a table, and the source and
 * the shape of the network's rainfall) is a step of its own.
 *
 * @param {string} prefix whose field ("network", a node's id)
 * @param {string[]} keys the keys the edit changed
 * @returns {string|null} the key to merge under, or null
 */
function mergeKey(prefix, keys) {
  if (keys.length !== 1) return null;
  const [key] = keys;
  if (key.includes("#") && !/#(rows|hydrograph)$/.test(key)) return null;
  if (prefix === "network" && RAIN_CHOICES.has(key)) return null;
  return `value:${prefix}:${key}`;
}

/**
 * An error of the server in Polish, with the node and field it names.
 *
 * @param {unknown} error an ApiError or anything thrown
 * @param {object} [rules] the inflow rules of the schema (the words of upstream_count)
 * @returns {{title: string, text: string, node: string|null, field: string|null, reason:
 *   string|null}} the error
 */
export function runFailure(error, rules = {}) {
  const doc = error && error.doc ? error.doc : { code: "internal_error", message: String((error && error.message) || error) };
  const details = doc.details || {};
  const described = describeError(doc);
  const reason = typeof details.reason === "string" ? details.reason : null;
  const own = reason ? problemText({ ...details, reason }, rules) : null;
  const field = typeof details.field === "string" ? details.field : null;
  const text = own || described.text;
  return {
    title: described.title,
    text: field && !own ? `${field}: ${text}` : text,
    node: typeof details.node_id === "string" ? details.node_id : null,
    field,
    reason,
  };
}

/**
 * The section „Sieć i trasowanie”.
 *
 * @param {{active: boolean, path: string[]}} props whether the section is shown, and the
 *   route's path (a node's id chooses it)
 * @returns {object} the section
 */
export default function Siec({ active, path = [] }) {
  const { forms, error: formsError } = useForms();
  const session = useSession();
  const [state, setState, reset] = usePersistentState(SECTION, initialState);
  const [, setStatus] = useStore("status");
  const [, setContext] = useStore("context");
  const [check, setCheck] = useState(NO_CHECK);
  const [laidOut, setLaidOut] = useState(NO_LAYOUT);
  const [run, setRun] = useState(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);
  const [note, setNote] = useState(null);
  const [scrollTo, setScrollTo] = useState(null);
  const [touched, setTouched] = useState(() => new Set());
  const [tried, setTried] = useState(false);
  const [said, setSaid] = useState(null);
  const [offer, setOffer] = useState(null);
  const [asking, setAsking] = useState(null);
  const [closed, setClosed] = useState(null);
  const schematicSvg = useRef(null);
  const chartSvg = useRef(null);
  const sequence = useRef(0);
  const running = useRef(null);
  const checked = useRef(0);
  const arranged = useRef(0);
  const renaming = useRef(null);
  // The newest state, also between an edit and its render, and the history of the edits
  const latest = useRef(state);
  latest.current = state;
  const history = useRef(null);
  if (history.current === null) {
    history.current = createHistory({ limit: HISTORY_STEPS });
    history.current.reset(stepOf(state));
  }
  const rules = forms ? forms.inflow : {};

  const update = (next) => {
    latest.current = next;
    setState(next);
    return next;
  };
  // An edit: the new state, and a step of the history when the network changed
  const apply = (next, options = {}) => {
    const base = latest.current;
    if (next === base) return base;
    update(next);
    if (next.network !== base.network || next.skeleton !== base.skeleton || next.nodes !== base.nodes) {
      history.current.push(stepOf(next), options);
    }
    return next;
  };
  const say = (text) => setSaid((old) => ({ text, count: old ? old.count + 1 : 1 }));

  // --- opening a network --------------------------------------------------------------
  const begin = (next) => {
    pmaxtp.reset();
    update(next);
    history.current.reset(stepOf(next));
    setRun(null);
    setFailure(null);
    setTouched(new Set());
    setTried(false);
    setCheck(NO_CHECK);
    setLaidOut(NO_LAYOUT);
    setOffer(null);
  };
  const open = (doc, source, lines) => {
    const opened = stateOf(doc, source);
    begin(opened);
    setNote({ error: false, lines: [...lines, ...placementNotes(doc, opened)] });
  };
  // Inputs stored before the canvas have no positions: they are laid out like a file
  // without them; this is part of opening, not a step
  useEffect(() => {
    if (!state.skeleton.some((node) => !node.position)) return;
    const base = latest.current;
    const clean = !base.savedKey || inputsKey(base) === base.savedKey;
    const placed = { ...base, ...placeSkeleton(base.skeleton) };
    update(clean ? { ...placed, savedKey: inputsKey(placed) } : placed);
    history.current.reset(stepOf(placed));
  }, [state.skeleton]);
  useOpened(({ doc, meta }) => {
    const { notes = [], ...source } = meta;
    const problems = documentProblems(doc);
    if (problems.length) {
      setNote({ error: true, title: t(texts.file.refused, { name: source.name }), lines: problems });
      return;
    }
    const named = withSessionNames(doc);
    open(named.doc, source, [t(texts.file.loaded, { name: source.name, nodes: plural(doc.nodes.length, texts.nodeForms) }), ...notes]);
  });

  // Uploads the companions of a network (rating files, the inflows file) into "in/"
  const uploadCompanions = async (files, ratings, needsInflows) => {
    const lines = [];
    let inflows = null;
    for (const file of files) {
      try {
        const stored = await uploadFile(file);
        const rating = ratings.includes(stored.name);
        if (!rating && needsInflows && !inflows) inflows = stored.path;
        lines.push(t(rating ? texts.files.uploadedRating : stored.path === inflows ? texts.files.uploadedInflows : texts.files.uploaded, { name: stored.name }));
      } catch (error) {
        const text = error && error.doc ? describeError(error.doc).text : String((error && error.message) || error);
        lines.push(t(texts.files.uploadFailed, { message: `${file.name}: ${text}` }));
      }
    }
    return { lines, inflows };
  };

  const onLoad = async (event) => {
    const chosen = [...(event.currentTarget.files || [])];
    event.currentTarget.value = "";
    if (!chosen.length) return;
    let found = null;
    const others = [];
    for (const file of chosen) {
      if (!found && /\.json$/i.test(file.name)) {
        try {
          const doc = JSON.parse(await file.text());
          if (doc && doc.schema === "hydrolog-network/1") {
            found = { file, doc };
            continue;
          }
        } catch {
          // not a network: a companion
        }
      }
      others.push(file);
    }
    if (!found) {
      const first = chosen[0];
      let problems = [texts.file.notNetwork];
      try {
        problems = documentProblems(JSON.parse(await first.text()));
      } catch (error) {
        problems = [t(texts.file.notJson, { message: String((error && error.message) || error) })];
      }
      setNote({ error: true, title: t(texts.file.refused, { name: first.name }), lines: problems });
      return;
    }
    const problems = documentProblems(found.doc);
    if (problems.length) {
      setNote({ error: true, title: t(texts.file.refused, { name: found.file.name }), lines: problems });
      return;
    }
    const named = withSessionNames(found.doc);
    const lines = [t(texts.file.loaded, { name: found.file.name, nodes: plural(found.doc.nodes.length, texts.nodeForms) })];
    for (const item of named.renamed) lines.push(t(texts.file.renamed, item));
    const loaded = stateOf(named.doc, { name: found.file.name, kind: "file" });
    const ratings = neededFiles(loaded).ratings.map((item) => item.name);
    const companions = await uploadCompanions(others, ratings, neededFiles(loaded).inflows.length > 0);
    open(named.doc, { name: found.file.name, kind: "file" }, [...lines, ...companions.lines]);
    if (companions.inflows) update({ ...latest.current, inflowsFile: companions.inflows });
  };

  const onCompanions = async (event) => {
    const chosen = [...(event.currentTarget.files || [])];
    event.currentTarget.value = "";
    if (!chosen.length) return;
    const needed = neededFiles(state);
    const companions = await uploadCompanions(chosen, needed.ratings.map((item) => item.name), needed.inflows.length > 0 && !state.inflowsFile);
    setNote({ error: false, lines: companions.lines });
    if (companions.inflows) update({ ...latest.current, inflowsFile: companions.inflows });
  };

  // --- the network and its checks -----------------------------------------------------
  const built = useMemo(
    () => (forms && state.source ? buildDocument(forms, state) : null),
    [forms, state.source, state.network, state.skeleton, state.nodes],
  );
  // Where each node's inputs came from as they stand (plan 2026-11-10-network-wizard, D9):
  // its panel and „Dane” show the received ones
  const origins = useMemo(() => siecOrigins(state, built ? built.document : null), [state.source, state.network, state.skeleton, state.nodes, built]);
  // The structure's problems and the nodes' words stay while only the cells and the
  // descriptions change (a move): they are kept per structure key
  const shape = useMemo(() => structureKey(state.skeleton), [state.skeleton]);
  const structure = useMemo(
    () => (forms && state.source ? graphProblems(state.skeleton, forms.inflow) : []),
    [forms, state.source, shape],
  );
  const words = useMemo(
    () => new Map(state.skeleton.map((node) => [node.id, nodeWords(node, state.nodes[node.id] || {})])),
    [shape, state.nodes],
  );
  // The depth of the network's PMAXTP (D4): remembered with its values, else fetched on
  // "siec-pmaxtp" once the point, p and the duration pass their checks. A fetched depth
  // belongs to every step of the history with the same options, so an undo does not fetch
  // it again, and fetching it keeps a network as it was opened or saved.
  const network = state.network;
  const pmaxtp = usePmaxtp(network, {
    channel: PMAXTP_CHANNEL,
    valid: Boolean(built) && !built.problems.some((item) => item.node === null && PMAXTP_NAMES.has(item.key)),
    onDepth: (record) => {
      const fetched = (values) => (pmaxtpKey(pmaxtpOptions(values)) === pmaxtpKey(record) ? { ...values, pmaxtp_fetched: record } : values);
      const base = latest.current;
      const next = { ...base, network: fetched(base.network) };
      if (next.network === base.network) return;
      history.current.rewrite((step) => {
        const kept = fetched(step.network);
        return kept === step.network ? step : { ...step, network: kept };
      });
      const clean = inputsKey(base) === base.savedKey;
      update(clean ? { ...next, savedKey: inputsKey(next) } : next);
    },
  });
  // The chosen subcatchment made from rainfall has its panel (D1): Hydrogram zlewni's steps
  // on its inputs, checked by Hydrogram's checks with the warnings of its notices in the
  // last run while its fields are as they were then
  const chosen = state.skeleton.find((node) => node.id === state.selected) || null;
  const chosenValues = chosen ? state.nodes[chosen.id] || {} : null;
  const panelNode = chosen && chosen.type === "subcatchment" && variantOf(chosenValues) === "rain" ? chosen : null;
  const panelInputs = useMemo(() => siecInputs(panelNode ? chosenValues : {}), [panelNode, chosenValues]);
  const panelRun = run && run.envelope.status === "ok" && panelNode && run.nodes[panelNode.id] ? run : null;
  const panelChecks = useMemo(() => {
    if (!forms || !panelNode) return null;
    const last = panelRun
      ? {
          inputs: siecInputs(panelRun.nodes[panelNode.id]),
          notices: (panelRun.envelope.notices || []).filter((notice) => notice.details && notice.details.node_id === panelNode.id),
        }
      : null;
    return checkInputs(panelInputs, forms.rain, last);
  }, [forms, panelNode, panelInputs, panelRun]);
  // Its own PMAXTP depth (D4: „Własny opad”): remembered with its inputs, else fetched on
  // "siec-node-pmaxtp"; a depth belongs to every subcatchment with the same options in
  // every step of the history, and fetching it keeps a network as it was opened or saved
  const nodePmaxtp = usePmaxtp(panelInputs, {
    channel: NODE_PMAXTP_CHANNEL,
    valid: panelChecks !== null && !Object.values(PMAXTP_FIELDS).some((name) => panelChecks.errors[name]),
    onDepth: (record) => {
      const key = pmaxtpKey(record);
      const fetched = (nodes) => {
        let next = nodes;
        for (const [id, values] of Object.entries(nodes)) {
          const inputs = siecInputs(values);
          if (variantOf(values) !== "rain" || pmaxtpKey(pmaxtpOptions(inputs)) !== key || pmaxtpDepth(inputs) !== null) continue;
          if (next === nodes) next = { ...nodes };
          next[id] = { ...values, pmaxtp_fetched: record };
        }
        return next;
      };
      const base = latest.current;
      const next = { ...base, nodes: fetched(base.nodes) };
      if (next.nodes === base.nodes) return;
      history.current.rewrite((step) => {
        const kept = fetched(step.nodes);
        return kept === step.nodes ? step : { ...step, nodes: kept };
      });
      const clean = inputsKey(base) === base.savedKey;
      update(clean ? { ...next, savedKey: inputsKey(next) } : next);
    },
  });
  // Its document lacks the depth while it is fetched or after a failure, which stands on
  // its field as a problem of the network
  const depthMissing = network.rain_source === "pmaxtp" && pmaxtpOptions(network) !== null && pmaxtp.depth === null;
  // A missing value is shown once its field was touched or „Oblicz sieć” was tried; any
  // other problem at once (as in the catalog forms), and a subcatchment's Hydrogram checks
  // at once, as Hydrogram zlewni shows them once a model is chosen (`shown`)
  const visible = useMemo(() => {
    const shown = built
      ? built.problems.filter((item) => tried || item.shown || !item.message.endsWith(" · required") || touched.has(`${item.node}|${item.key}`))
      : [];
    const failed = pmaxtp.failed ? Object.entries(pmaxtp.failed.fields).map(([key, message]) => ({ node: null, key, message })) : [];
    const nodeFailed =
      nodePmaxtp.failed && panelNode ? Object.entries(nodePmaxtp.failed.fields).map(([key, message]) => ({ node: panelNode.id, key, message })) : [];
    return [...shown, ...failed, ...nodeFailed];
  }, [built, touched, tried, pmaxtp.failed, nodePmaxtp.failed, panelNode]);
  const problems = useMemo(() => {
    const found = { network: {}, nodes: {} };
    for (const item of visible) {
      if (item.node === null) found.network[item.key] = item.message;
      else found.nodes[item.node] = { ...(found.nodes[item.node] || {}), [item.key]: item.message };
    }
    return found;
  }, [visible]);
  const touch = (node, before, after) => {
    const changed = changedKeys(before, after);
    if (changed.length) setTouched((old) => new Set([...old, ...changed.map((key) => `${node}|${key}`)]));
    return changed;
  };
  // The edits of the subcatchment's panel (D1): a patch of its inputs, a field of its
  // watershed, a watershed file; typing into one field stays one step of the history until
  // it commits, and a choice is a step of its own (D9)
  const editNode = (id, change, merge) => {
    const base = latest.current;
    const before = siecInputs(base.nodes[id] || {});
    const next = change(before);
    touch(id, before, next);
    apply({ ...base, nodes: { ...base.nodes, [id]: next } }, { merge });
  };
  const nodeSet = (id) => (patch) => {
    const keys = Object.keys(patch);
    const merge = keys.length === 1 && !STEP_CHOICES.has(keys[0]) ? `value:${id}:${keys[0]}` : null;
    editNode(id, (inputs) => ({ ...inputs, ...patch }), merge);
  };
  const nodeSetField = (id) => (name, text) =>
    editNode(id, (inputs) => ({ ...inputs, watershed: { ...inputs.watershed, [name]: text } }), `value:${id}:watershed.${name}`);
  const nodeFile = (id) => async (file) => {
    try {
      nodeSet(id)(await readWatershedFile(file));
      toast(t(rainTexts.watershed.fileLoaded, { file: file.name }));
    } catch (error) {
      toast(t(rainTexts.watershed.fileFailed, { file: file.name, message: error.message || String(error) }), "bad");
    }
  };
  const sessionNames = new Set(inputFiles(session).map((file) => file.path.slice(3)));
  const needed = neededFiles(state);
  needed.ratings = needed.ratings.map((item) => ({ ...item, present: sessionNames.has(item.name) }));
  const missing = [
    ...needed.ratings.filter((item) => !item.present).map((item) => t(texts.files.ratingMissing, { node: item.node, name: item.name })),
    ...(needed.inflows.length && !state.inflowsFile ? [texts.files.inflowsMissing] : []),
    ...(state.inflowsFile && session && !sessionNames.has(state.inflowsFile.replace(/^in\//, ""))
      ? [t(texts.files.inflowsGone, { name: state.inflowsFile.replace(/^in\//, "") })]
      : []),
  ];
  const valid = Boolean(built) && built.problems.length === 0 && structure.length === 0 && !depthMissing;
  const ready = valid && missing.length === 0;
  const runOptions = (stem, name) => {
    const options = { network_file: `in/${name}` };
    if (needed.inflows.length && state.inflowsFile) options.inflows_file = state.inflowsFile;
    if (options.inflows_file && String(state.timeColumn || "").trim()) options.time_column = String(state.timeColumn).trim();
    options.schematic = `out/${stem}.svg`;
    options.force = true;
    return options;
  };
  const name = documentName(state);
  const stem = fileStem(state);
  // Neither a move nor a description marks the result stale: the key leaves them out (D11)
  const currentKey = built ? JSON.stringify([withoutPicture(built.document), runOptions(stem, name)]) : null;
  // Hydrolog checks the complete network after every change of what it computes (D8,
  // point 3), so its verdict is never older than the values
  const checkKey = ready ? JSON.stringify([currentKey, needed.ratings]) : null;
  // Hydrolog lays out the structure as soon as the browser's checks find no problem in
  // it, whatever values the nodes still miss (plan 2026-11-10-network-wizard, D8); a move,
  // a description or a value other than a subcatchment's area changes nothing of it
  const areas = useMemo(() => new Map([...words].map(([id, word]) => [id, word.area])), [words]);
  const shaped = Boolean(forms && state.source) && structure.length === 0;
  const layoutKey = useMemo(
    () => (shaped ? JSON.stringify(structureDocument(state.skeleton, areas)) : null),
    [shaped, shape, areas],
  );

  // --- Hydrolog's check of the complete network ----------------------------------------
  useEffect(() => {
    if (!checkKey || checkKey === check.key) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      checked.current += 1;
      const mine = checked.current;
      // Inline, so the session holds no file until „Oblicz sieć”; a network that reads
      // rating files needs its document in "in/" beside them
      const plain = withoutPicture(built.document);
      const options = { ...runOptions(stem, name) };
      delete options.schematic;
      delete options.force;
      try {
        if (needed.ratings.length) {
          await api.upload(new Blob([`${JSON.stringify(plain, null, 2)}\n`], { type: "application/json" }), name);
        } else {
          delete options.network_file;
          options.network = plain;
        }
        const envelope = await api.run("route schematic", options, { channel: SCHEMATIC_CHANNEL, signal: controller.signal });
        if (mine !== checked.current || envelope.status !== "ok") return;
        setCheck({ key: checkKey, error: null });
      } catch (error) {
        if ((error && error.name === "AbortError") || mine !== checked.current) return;
        setCheck({ key: checkKey, error: runFailure(error, rules) });
      }
    }, SCHEMATIC_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [checkKey]);
  const refusal = check.key === checkKey && check.error ? check.error : null;

  // --- Hydrolog's layout of the structure: the cells of „Uporządkuj” ---------------------
  useEffect(() => {
    if (!layoutKey || layoutKey === laidOut.key) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      arranged.current += 1;
      const mine = arranged.current;
      const options = { network: JSON.parse(layoutKey), structure_only: true };
      try {
        const envelope = await api.run("route schematic", options, { channel: LAYOUT_CHANNEL, signal: controller.signal });
        if (mine !== arranged.current || envelope.status !== "ok") return;
        const positions = Object.fromEntries(envelope.result.nodes.map((node) => [node.id, { x: node.x, y: node.y }]));
        setLaidOut({ key: layoutKey, positions, error: null });
      } catch (error) {
        if ((error && error.name === "AbortError") || mine !== arranged.current) return;
        setLaidOut({ key: layoutKey, positions: null, error: runFailure(error, rules) });
      }
    }, SCHEMATIC_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [layoutKey]);
  const layout = laidOut.key === layoutKey ? laidOut.positions : null;
  const misfit = laidOut.key === layoutKey && laidOut.error ? laidOut.error : null;
  // Provisional rows give way to Hydrolog's layout once the structure has no problem
  // (D10); this is part of opening, not an edit: every step of the history takes the
  // cells too
  useEffect(() => {
    if (!state.provisional || !layout) return;
    const base = latest.current;
    const clean = inputsKey(base) === base.savedKey;
    const placed = { ...placeAll(base, layout), provisional: false };
    history.current.rewrite((step) => placeAll(step, layout));
    update(clean ? { ...placed, savedKey: inputsKey(placed) } : placed);
  }, [state.provisional, layout]);
  const tidy = () => {
    if (layout) apply({ ...placeAll(latest.current, layout), provisional: false });
  };
  let tidyBlocked = null;
  if (!shaped) tidyBlocked = texts.canvas.tidyWaiting;
  else if (misfit) tidyBlocked = t(texts.schematic.failed, { message: misfit.text });
  else if (!layout) tidyBlocked = texts.canvas.tidyBusy;

  // --- the problems on the canvas (D8) ---------------------------------------------------
  const shown = useMemo(() => {
    const list = [];
    const marks = new Map();
    const loops = new Set();
    const mark = (id, text) => {
      if (!marks.has(id)) marks.set(id, []);
      marks.get(id).push(text);
    };
    structure.forEach((problem, index) => {
      const text = problemText(problem, rules) || problem.reason;
      const nodes = problemNodes(problem);
      list.push({ key: `structure-${index}`, reason: problem.reason, text, node: nodes[0] || null });
      for (const id of nodes) mark(id, text);
      if (problem.reason === "cycle") {
        problem.nodes.forEach((id, at) => loops.add(`${id}>${problem.nodes[(at + 1) % problem.nodes.length]}`));
      }
    });
    const fields = new Map();
    for (const item of visible) {
      // „Brak opadu” (D4) says itself what to do: the network's rainfall or the node's own
      if (item.node !== null && item.key === NO_RAINFALL_KEY) {
        const text = t(texts.problems.node, { id: item.node, message: splitReason(item.message).text });
        list.push({ key: `rainfall-${item.node}`, reason: "missing_field", text, node: item.node });
        mark(item.node, text);
        continue;
      }
      if (!fields.has(item.node)) fields.set(item.node, []);
      fields.get(item.node).push(item.key.split(".").pop());
    }
    for (const [node, keys] of fields) {
      const named = keys.slice(0, 3).join(", ") + (keys.length > 3 ? ", …" : "");
      const text = node === null ? t(texts.problems.networkFields, { fields: named }) : t(texts.problems.fields, { id: node, fields: named });
      list.push({ key: `fields-${node}`, reason: "fields", text, node });
      if (node !== null) mark(node, text);
    }
    // Hydrolog's refusals: of the complete network, and of the structure alone when it
    // says something else (the two read the structure with one check)
    const refusals = [
      ["hydrolog", refusal],
      ["hydrolog-layout", misfit && (!refusal || misfit.text !== refusal.text) ? misfit : null],
    ];
    for (const [key, found] of refusals) {
      if (!found) continue;
      const text = t(texts.problems.hydrolog, { message: found.text });
      list.push({ key, reason: found.reason || "hydrolog", text, node: found.node });
      if (found.node) mark(found.node, found.text);
    }
    return { list, marks, loops };
  }, [structure, visible, refusal, misfit, rules]);

  // --- choosing a node ------------------------------------------------------------------
  // A choice opens the panel of a subcatchment made from rainfall again after its ✕ (D2)
  const choose = (id) => {
    setClosed(null);
    if (latest.current.selected !== id) update({ ...latest.current, selected: id });
    if (active) navigate(SECTION, id ? [id] : [], { replace: true });
  };
  // The focus to the first step of the subcatchment's panel (Enter on it, „Dane zlewni →”);
  // a phone's sheet cannot take it while it is still hidden, so again once it has slid in
  const focusPanel = () =>
    setTimeout(() => {
      const panel = document.querySelector('section.section[data-section="siec"] .view-panel.detail');
      const first = panel && panel.querySelector("[data-step] > summary");
      if (!first) return;
      first.focus();
      if (document.activeElement === first) return;
      const slid = (event) => {
        if (event.target !== panel) return;
        panel.removeEventListener("transitionend", slid);
        first.focus();
      };
      panel.addEventListener("transitionend", slid);
    }, 0);
  // A click, the arrows or the list open or change the panel without moving the focus;
  // Enter on a subcatchment moves it there (D2). The subcatchment's panel takes its place
  // back from „Wyniki” in a narrow window and takes the left sheet on a phone; any other
  // node shows „Dane” on a phone when it was chosen on the picture.
  const select = (id, fromPicture = true, enter = false) => {
    const base = latest.current;
    const node = base.skeleton.find((item) => item.id === id);
    if (!node) return;
    choose(id);
    const panel = node.type === "subcatchment" && variantOf(base.nodes[id] || {}) === "rain";
    if (panel) openPanel("detail");
    else if (fromPicture && isPhone()) openPanel("left");
    if (panel && enter) focusPanel();
    setScrollTo(id);
  };
  // „Dane zlewni →” in „Dane”'s step 3: the subcatchment's panel, open and in focus
  const showPanel = () => {
    setClosed(null);
    openPanel("detail");
    focusPanel();
  };
  // „Opad sieci w kroku 1” of the panel: „Dane” (its sheet on a phone) at the network's rainfall
  const showRain = () => {
    openPanel("left");
    setTimeout(showNetworkRain, 0);
  };
  useEffect(() => {
    const id = path[0];
    if (id && id !== state.selected && state.skeleton.some((node) => node.id === id)) update({ ...latest.current, selected: id });
  }, [path[0], state.skeleton]);
  useEffect(() => {
    if (!scrollTo) return;
    const step = document.querySelector('section.section[data-section="siec"] .node-step');
    if (step && typeof step.scrollIntoView === "function") step.scrollIntoView({ block: "nearest" });
    setScrollTo(null);
  }, [scrollTo]);

  // --- the edits of the structure (D7) and the history (D9) -------------------------------
  const restore = (step) => {
    const base = latest.current;
    const ids = new Set(step.skeleton.map((node) => node.id));
    const outlet = step.skeleton.find((node) => node.type === "outlet");
    let selected = base.selected && ids.has(base.selected) ? base.selected : null;
    if (!selected) selected = outlet ? outlet.id : step.skeleton.length ? step.skeleton[0].id : null;
    update({ ...base, ...step, selected, provisional: false });
    setOffer(null);
    if (active && selected !== base.selected) navigate(SECTION, selected ? [selected] : [], { replace: true });
  };
  const actions = {
    add(type, cell, into = null) {
      const base = latest.current;
      let next = addNode(base, type, { x: cell[0], y: cell[1] });
      if (next === base) return null;
      const made = next.skeleton[next.skeleton.length - 1].id;
      if (into) next = connect(next, made, into);
      apply({ ...next, selected: made, provisional: false });
      if (active) navigate(SECTION, [made], { replace: true });
      say(t(into ? texts.canvas.addedInto : texts.canvas.added, { id: made, kind: kindNoun(type), to: into }));
      return made;
    },
    addBeside(type) {
      const base = latest.current;
      const cell = cellBeside(base.skeleton, base.selected);
      if (!cell) {
        say(texts.canvas.full);
        return null;
      }
      return actions.add(type, cell, null);
    },
    // „Dodaj zlewnię z Hydrografa” (D10): the hand-off's subcatchments, one step; the
    // first is chosen, so „Dane” shows where it came from
    addHandoff(doc) {
      const base = latest.current;
      const found = siecAddition(base, doc);
      if (!found.added.length) return { title: handoffTexts.add.refused, lines: found.lines };
      const [first] = found.added;
      apply({ ...found.inputs, selected: first, provisional: false });
      if (active) navigate(SECTION, [first], { replace: true });
      setNote({ error: false, lines: found.lines });
      toast(found.lines[0]);
      return null;
    },
    // „Wczytaj z Hydrografa” in the panel (plan 2026-11-10-network-wizard, D10): the
    // hand-off's watershed fills the subcatchment, which keeps its id, links, position and
    // description; one step
    fill(id, doc) {
      const base = latest.current;
      if (!base.skeleton.some((node) => node.id === id)) return null;
      const found = siecFill(base, id, doc);
      apply(found.inputs);
      setNote({ error: false, lines: found.lines });
      toast(found.lines[0]);
      return null;
    },
    link(from, to, where = "canvas") {
      const base = latest.current;
      const verdict = linkVerdict(base.skeleton, rules, from, to);
      if (!verdict.ok) {
        say(t(texts.canvas.refused, { reason: refusalText(verdict, base.skeleton, from, to) }));
        if (!verdict.offer) return "refused";
        setOffer({ from, to, where });
        return "offer";
      }
      const before = receiversOf(base.skeleton).get(from) || [];
      if (before.length === 1 && before[0] === to) {
        say(t(texts.canvas.already, { from, to }));
        return "same";
      }
      apply({ ...connect(base, from, to), provisional: false });
      setOffer(null);
      say(before.length ? t(texts.canvas.relinked, { from, to, old: before.join(", ") }) : t(texts.canvas.linked, { from, to }));
      return "linked";
    },
    insertJunction(from, to) {
      const base = latest.current;
      const next = insertJunction(base, from, to);
      setOffer(null);
      if (next === base) {
        say(texts.canvas.full);
        return null;
      }
      const known = new Set(base.skeleton.map((node) => node.id));
      const made = next.skeleton.find((node) => !known.has(node.id));
      apply({ ...next, provisional: false });
      say(t(texts.canvas.junction, { id: made.id, inflows: made.from.join(", "), to }));
      return made.id;
    },
    cancelOffer() {
      if (offer) say(t(texts.canvas.linkStopped, { id: offer.from }));
      setOffer(null);
    },
    unlink(from, to = null) {
      const base = latest.current;
      const below = (receiversOf(base.skeleton).get(from) || []).filter((id) => to === null || id === to);
      if (!below.length) {
        say(t(texts.canvas.notLinked, { id: from }));
        return;
      }
      apply({ ...disconnect(base, from, to), provisional: false });
      say(t(texts.canvas.unlinked, { from, to: below.join(", ") }));
    },
    remove(id, bridge = false) {
      const base = latest.current;
      const node = base.skeleton.find((item) => item.id === id);
      if (!node) return;
      const down = (receiversOf(base.skeleton).get(id) || [])[0] || null;
      const bridged = bridge && canBridge(base.skeleton, id);
      const next = removeNode(base, id, { bridge: bridged });
      let selected = base.selected;
      if (selected === id) selected = down || (node.from && node.from[0]) || null;
      apply({ ...next, selected, provisional: false });
      setTouched((old) => new Set([...old].filter((key) => !key.startsWith(`${id}|`))));
      if (offer && (offer.from === id || offer.to === id)) setOffer(null);
      if (active && selected !== base.selected) navigate(SECTION, selected ? [selected] : [], { replace: true });
      say(bridged ? t(texts.canvas.bridged, { id, up: node.from[0], down }) : t(texts.canvas.removed, { id }));
    },
    rename(id, next) {
      const base = latest.current;
      const renamed = renameNode(base, id, next);
      if (renamed === base) return false;
      apply(renamed);
      setTouched((old) => new Set([...old].map((key) => (key.startsWith(`${id}|`) ? `${next}|${key.slice(id.length + 1)}` : key))));
      if (active && renamed.selected === next) navigate(SECTION, [next], { replace: true });
      const column = (renamed.nodes[next] || {}).value_column;
      const kept = column !== (base.nodes[id] || {}).value_column;
      say(`${t(texts.canvas.renamed, { old: id, next })}${kept ? ` ${t(texts.form.columnKept, { column })}` : ""}`);
      return true;
    },
    describe(id, text) {
      apply(describeNode(latest.current, id, text), { merge: `describe:${id}` });
    },
    undo() {
      const step = history.current.undo();
      if (!step) return;
      restore(step);
      say(texts.canvas.undone);
    },
    redo() {
      const step = history.current.redo();
      if (!step) return;
      restore(step);
      say(texts.canvas.redone);
    },
  };
  // F2 and „Zmień id”: the id field of the node in „Dane”; Enter or Esc there gives the
  // focus back to the node on the canvas
  const renameRequest = (id) => {
    if (!latest.current.skeleton.some((node) => node.id === id)) return;
    renaming.current = id;
    choose(id);
    if (isPhone()) openPanel("left");
    setTimeout(() => {
      const field = document.querySelector('section.section[data-section="siec"] [data-field="id"] input');
      if (field) {
        field.focus();
        field.select();
      }
    }, 0);
  };
  const idDone = (id) => {
    if (renaming.current === null) return;
    renaming.current = null;
    setTimeout(() => {
      const node = document.querySelector(`section.section[data-section="siec"] svg.schem g.node[data-node="${CSS.escape(id)}"]`);
      if (node) node.focus();
    }, 0);
  };

  // --- „Oblicz sieć” ----------------------------------------------------------------------
  const focusProblem = () =>
    setTimeout(() => {
      const section = document.querySelector('section.section[data-section="siec"]');
      for (const panel of section ? section.querySelectorAll(".view-panel.detail, .view-panel.left") : []) {
        const field = panel.querySelector('[aria-invalid="true"], .err');
        if (field && typeof field.focus === "function") {
          field.focus();
          return;
        }
      }
    }, 0);
  const compute = async () => {
    if (!built) return;
    if (!ready) {
      setTried(true);
      const first = structure.map((problem) => problemNodes(problem)[0]).find(Boolean) || (built.problems.find((item) => item.node) || {}).node;
      if (first && first !== state.selected) select(first, false);
      focusProblem();
      return;
    }
    sequence.current += 1;
    const mine = sequence.current;
    if (running.current) running.current.abort();
    const controller = new AbortController();
    running.current = controller;
    const options = runOptions(stem, name);
    const key = currentKey;
    // What the panel compares and reads the run with: its document and the nodes' inputs
    const sent = built.document;
    const nodes = state.nodes;
    setBusy(true);
    try {
      await api.upload(new Blob([`${JSON.stringify(built.document, null, 2)}\n`], { type: "application/json" }), name);
      const envelope = await api.run("route network", options, { channel: SECTION, signal: controller.signal });
      if (mine !== sequence.current) return;
      setRun({ envelope, options, key, at: new Date(), document: sent, nodes });
      setFailure(null);
      if (isPhone()) openPanel("right");
    } catch (error) {
      if ((error && error.name === "AbortError") || mine !== sequence.current) return;
      const found = runFailure(error, rules);
      setFailure({ ...found, key });
      if (found.node && found.node !== state.selected) select(found.node, false);
    } finally {
      if (mine === sequence.current) {
        setBusy(false);
        running.current = null;
      }
    }
  };

  // --- starting, saving and discarding (D10) ----------------------------------------------
  const clear = () => {
    reset();
    pmaxtp.reset();
    latest.current = initialState();
    history.current.reset(stepOf(latest.current));
    setRun(null);
    setFailure(null);
    setNote(null);
    setCheck(NO_CHECK);
    setLaidOut(NO_LAYOUT);
    setOffer(null);
    setTouched(new Set());
    setTried(false);
    if (active) navigate(SECTION, [], { replace: true });
  };
  // A new network starts at its rainfall in step 1 (plan 2026-11-10-network-wizard, D4):
  // „Dane” shows it, on a phone too, and the empty canvas says what comes next
  const startNew = () => {
    begin(newState());
    setNote({ error: false, lines: [texts.file.started] });
    if (active) navigate(SECTION, [], { replace: true });
  };
  const askClear = () => (changedSinceSaved(latest.current) ? setAsking("clear") : clear());
  const askNew = () => (changedSinceSaved(latest.current) ? setAsking("new") : startNew());
  const problemCount = structure.length + (built ? built.problems.length : 0);
  const save = () => {
    if (!built || !state.skeleton.length) return;
    const file = `${stem}.json`;
    downloadBlob(new Blob([`${JSON.stringify(built.document, null, 2)}\n`], { type: "application/json" }), file);
    update({ ...latest.current, savedKey: inputsKey(latest.current) });
    toast(valid ? t(texts.file.saved, { name: file }) : t(texts.file.draftSaved, { name: file, count: problemCount }));
  };

  // --- badge and context ------------------------------------------------------------------
  const shownFailure = failure && failure.key === currentKey ? failure : null;
  const firstStructure = structure.length ? structure[0] : null;
  const firstProblem = visible.length ? visible[0] : null;
  let badge = null;
  if (busy) badge = status("busy");
  else if (pmaxtp.busy || nodePmaxtp.busy) badge = status("busy", rainTexts.calc.fetchingBadge, rainTexts.calc.fetching);
  else if (shownFailure) badge = status("error", undefined, shownFailure.text);
  else if (firstStructure) {
    const at = problemNodes(firstStructure)[0];
    const where = at ? `${at} · ${firstStructure.reason}` : firstStructure.reason;
    badge = status("invalid", `${shell.status.invalid.text}: ${where}`, problemText(firstStructure, rules));
  } else if (firstProblem) {
    // „Brak opadu” names the library's field (`missing_field` `rainfall`), not the choice
    const field = firstProblem.key === NO_RAINFALL_KEY ? "rainfall" : firstProblem.key.split(".").pop();
    const where = firstProblem.node ? `${firstProblem.node} · ${field}` : firstProblem.key;
    badge = status("invalid", `${shell.status.invalid.text}: ${where}`, firstProblem.message);
  } else if (missing.length) badge = status("invalid", `${shell.status.invalid.text}: ${texts.files.short}`, missing[0]);
  else if (run && run.envelope.status === "ok" && run.key !== currentKey) badge = status("stale");
  else if (run && run.envelope.status === "ok") badge = status("ok");
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);
  const title = String(state.network.name || "").trim() || (state.source ? state.source.name : "");
  const context = state.source ? t(texts.context, { name: title, nodes: plural(state.skeleton.length, texts.nodeForms) }) : null;
  useEffect(() => setContext(context), [context]);

  // --- the parts of the layout -------------------------------------------------------------
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const values = useMemo(() => (result ? new Map(result.nodes.map((node) => [node.id, node])) : null), [result]);
  const formsProblem = formsError ? t(texts.formsFailed, { message: formsError }) : null;
  const left = {
    sub: "hydrolog-network/1",
    body: formsProblem
      ? html`<div class="form-errors" role="alert">${formsProblem}</div>`
      : !state.source
        ? html`<${EmptyNetwork} note=${note} onLoad=${onLoad} onNew=${askNew} />`
        : !forms
          ? html`<p class="muted" role="status">${common.loading}</p>`
          : html`<${DataPanel}
            state=${state}
            forms=${forms}
            words=${words}
            values=${values}
            origins=${origins}
            problems=${problems}
            summary=${networkSummary(state.skeleton, words)}
            needed=${needed}
            note=${note}
            onPanel=${showPanel}
            pmaxtp=${{ depth: pmaxtp.depth, busy: pmaxtp.busy, onRetry: pmaxtp.onRetry }}
            canSave=${state.skeleton.length > 0}
            complete=${valid}
            offer=${offer && offer.where === "data" ? offer : null}
            actions=${actions}
            onNetwork=${(network) => {
              const base = latest.current;
              const changed = touch(null, base.network, network);
              apply({ ...base, network }, { merge: mergeKey("network", changed) });
            }}
            onRun=${(change) => update({ ...latest.current, ...change })}
            onNode=${(id, next) => {
              const base = latest.current;
              const changed = touch(id, base.nodes[id] || {}, next);
              apply({ ...base, nodes: { ...base.nodes, [id]: next } }, { merge: mergeKey(id, changed) });
            }}
            onCommit=${() => history.current.seal()}
            onSelect=${select}
            onLoad=${onLoad}
            onCompanions=${onCompanions}
            onSave=${save}
            onNew=${askNew}
            onIdDone=${idDone}
          />`,
    foot: html`
      <button class="btn primary" type="button" data-action="compute" disabled=${!built || !state.skeleton.length || busy || pmaxtp.busy || nodePmaxtp.busy} onClick=${compute}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" /></svg>
        ${texts.compute}
      </button>
      <span class="muted small form-state" role="status">${busy
        ? texts.computing
        : run
          ? t(texts.lastRun, { time: run.at.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) })
          : ""}</span>
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${askClear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };

  const view = state.view === "table" ? "table" : "schem";
  // The canvas, once every node has a cell; a network opened without positions whose
  // structure has no problem waits until Hydrolog's layout has placed it, instead of
  // showing the provisional rows first: the render in which the layout arrives still
  // holds them, and the effect above replaces them only after it
  const waiting =
    state.skeleton.some((node) => !node.position) ||
    (state.provisional && ((!forms && !formsError) || (shaped && !misfit)));
  const canvas = () => {
    if (!state.source) return html`<p class="empty-note" data-schematic="empty">${texts.schematic.empty}</p>`;
    if (waiting || !forms) return html`<p class="empty-note" role="status" data-schematic="busy">${texts.schematic.busy}</p>`;
    return html`<${NetworkCanvas}
      inputs=${state}
      words=${words}
      values=${values}
      selected=${state.selected}
      rules=${rules}
      problems=${shown}
      history=${{ canUndo: history.current.canUndo, canRedo: history.current.canRedo }}
      tidy=${{ blocked: tidyBlocked }}
      offer=${offer && offer.where === "canvas" ? offer : null}
      onTidy=${tidy}
      onEdit=${(next, options) => apply({ ...next, provisional: false }, options)}
      onSelect=${select}
      actions=${actions}
      onRename=${renameRequest}
      say=${say}
      svgRef=${schematicSvg}
      titleId="siec-schem-title"
    />`;
  };
  const center = {
    label: texts.schematic.title,
    bar: html`
      <${Seg}
        items=${[
          { value: "schem", label: texts.views.schematic },
          { value: "table", label: texts.views.table },
        ]}
        value=${view}
        onChange=${(next) => update({ ...latest.current, view: next })}
        label=${texts.views.label}
      />
      <span class="hint">
        <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>
        <span>${texts.hint}</span>
      </span>
    `,
    body: html`<div class=${`result-area${busy ? " computing" : ""}`} aria-busy=${busy ? "true" : "false"}>
      ${view === "schem"
        ? html`<div class="card" data-card="schematic">
            <div class="card-head">
              <h3 class="card-title" id="siec-schem-title">${texts.schematic.title}</h3>
              <span class="card-sub">${texts.schematic.sub}</span>
            </div>
            ${canvas()}
            <div class="chart-legend">
              ${["subcatchment", "reach", "junction", "reservoir", "outlet"].map(
                (kind) => html`<span><i class=${`ng t-${kind}`} aria-hidden="true"></i>${texts.kinds[kind].noun}</span>`,
              )}
              <span><i class="sw-line ln-main" aria-hidden="true"></i>${texts.schematic.main}</span>
              <span><i class="sw-line ln-trib" aria-hidden="true"></i>${texts.schematic.tributary}</span>
              <span class="muted">${texts.schematic.legend}</span>
            </div>
          </div>`
        : html`<${NodeTable} skeleton=${state.skeleton} words=${words} result=${result} selected=${state.selected} onSelect=${(id) => select(id, false)} />`}
      <p class="sr-only" role="status" aria-live="polite" data-canvas="said">${said ? html`<span key=${said.count}>${said.text}</span>` : null}</p>
    </div>`,
  };
  const outlet = state.skeleton.find((node) => node.type === "outlet");
  const right = {
    sub: state.selected ? t(texts.resultsSub, { outlet: outlet ? outlet.id : "–", node: state.selected }) : null,
    body: html`<div class=${`result-area${busy ? " computing" : ""}`}>
      <${ResultsPanel}
        run=${run}
        stale=${Boolean(run && run.key !== currentKey)}
        selected=${state.selected}
        state=${state}
        document=${built ? built.document : null}
        valid=${valid}
        chartSvg=${chartSvg}
        schematicSvg=${schematicSvg}
        error=${shownFailure}
      />
    </div>`,
  };

  // --- the subcatchment's panel (plan 2026-11-10-network-wizard, D1, D2, D10) ---------------
  let detail = null;
  if (panelNode && forms && panelChecks && closed !== panelNode.id) {
    const id = panelNode.id;
    // What the last run gave the node, while its node of the document is as it was then
    const plain = (node) => {
      const { position: _cell, description: _text, ...rest } = node;
      return canonical(rest);
    };
    const now = built ? built.document.nodes.find((node) => node.id === id) : null;
    const then = panelRun ? panelRun.document.nodes.find((node) => node.id === id) : null;
    const routed = now && then && plain(now) === plain(then) && values ? values.get(id) : null;
    const computed = routed && routed.parameters ? nodeComputed(routed.parameters, siecInputs(panelRun.nodes[id])) : null;
    // Hydrolog's refusal of the node stands on its field when the panel shows it, else above
    // the steps
    const errors = { ...panelChecks.errors, ...(nodePmaxtp.failed ? nodePmaxtp.failed.fields : {}) };
    const told = [shownFailure, refusal].find((found) => found && found.node === id) || null;
    let formError = null;
    if (told && told.field && panelFields(panelInputs).includes(told.field)) errors[told.field] = withReason(told.text, told.reason || "");
    else if (told) formError = { title: told.title, text: told.text };
    const firstError = Object.keys(errors)[0] || null;
    const noRain = Boolean(built) && built.problems.some((item) => item.node === id && item.key === NO_RAINFALL_KEY);
    let calc = { kind: "ok", text: computed ? texts.panel.calc.computed : texts.panel.calc.ok };
    if (!panelInputs.uh_model) calc = { kind: "idle", text: texts.panel.calc.model };
    else if (firstError) calc = { kind: "warn", text: t(texts.panel.calc.invalid, { field: fieldLabel(firstError) }) };
    else if (nodePmaxtp.busy) calc = { kind: "busy", text: texts.panel.calc.fetching };
    else if (noRain) calc = { kind: "warn", text: texts.panel.calc.noRainfall };
    detail = {
      title: (words.get(id) || {}).title || id,
      sub: texts.panel.sub,
      body: html`<div class="node-panel" data-node-panel=${id} onChange=${() => history.current.seal()}>
        <${SubcatchmentSteps}
          key=${id}
          prefix=${PANEL_PREFIX}
          inputs=${panelInputs}
          set=${nodeSet(id)}
          setField=${nodeSetField(id)}
          errors=${errors}
          warnings=${panelChecks.warnings}
          required=${requirements(panelInputs).required}
          formError=${formError}
          computed=${computed}
          models=${forms.rain}
          infoValues=${checkedValues(panelInputs, computed)}
          pmaxtp=${{ depth: nodePmaxtp.depth, busy: nodePmaxtp.busy, onRetry: nodePmaxtp.onRetry }}
          network=${{ rainfall: networkRainWords(network, pmaxtp.depth) || texts.form.noNetworkRain, timestep_min: String(network.timestep_min ?? ""), onOpen: showRain }}
          origins=${panelOrigins(panelNode, origins[id])}
          onFile=${nodeFile(id)}
          onHandoff=${(doc) => actions.fill(id, doc)}
          hint=${null}
        />
      </div>`,
      foot: html`<span class=${`calc-state${calc.kind === "ok" ? "" : ` ${calc.kind}`}`} data-calc=${calc.kind} role="status">
        <i class="dot" aria-hidden="true"></i><span>${calc.text}</span>
      </span>`,
      onClose: () => setClosed(id),
    };
  }
  const question = asking === "new" ? "new" : "clear";
  return html`
    <${ViewLayout} left=${left} detail=${detail} center=${center} right=${right} />
    <${ConfirmDialog}
      open=${asking !== null}
      name=${question}
      title=${question === "new" ? texts.confirm.newTitle : texts.confirm.clearTitle}
      text=${question === "new" ? texts.confirm.newText : texts.confirm.clearText}
      confirm=${question === "new" ? texts.confirm.new : texts.confirm.clear}
      cancel=${texts.confirm.cancel}
      onConfirm=${() => {
        setAsking(null);
        if (question === "new") startNew();
        else clear();
      }}
      onCancel=${() => setAsking(null)}
    />
  `;
}
