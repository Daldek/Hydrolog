// „Sieć i trasowanie” (plan S4; the approved mockup with the author's revisions): a river
// network of hydrolog-network/1, opened from a file or a hand-off (a first visit has none;
// the guide, instrukcja/#siec, has a worked example to load), drawn vertically on the
// canvas of „Schemat sieci” from the section's own inputs (plan 2026-11-10-network-editor,
// D1, D6: the sources at the top, the outlet at the bottom, every node on the cell of its
// position). A network opened without positions takes Hydrolog's layout (`route
// schematic`) as soon as Hydrolog can read it, and stands in provisional rows until then;
// a person moves nodes on the canvas, and „Uporządkuj” brings Hydrolog's layout back. A
// click on a node, Enter or Space, or its row in a table opens its settings in „Dane” and
// its result in „Wyniki”. The network is computed on „Oblicz sieć” only: the document,
// positions included, is written to the session's `in/` and `route network` routes it
// (with the inflows file and the rating files it reads); a change afterwards marks the
// result stale („Dane zmienione: oblicz ponownie”, plan D13), a move never does.

import { api } from "../../api.js";
import { inputFiles, uploadFile, useSession } from "../../controls/file-field.js";
import { plural } from "../../format.js";
import { html, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError } from "../../labels/errors.js";
import { routing } from "../../labels/info/routing.js";
import { siec as texts } from "../../labels/siec.js";
import { shell } from "../../labels/shell.js";
import { usePersistentState } from "../../persist.js";
import { navigate } from "../../router.js";
import { useStore } from "../../store.js";
import { downloadBlob } from "../../ui/export-panel.js";
import { registerInfo } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { isPhone, openPanel } from "../../ui/sheet.js";
import { status } from "../../ui/status.js";
import { toast } from "../../ui/toast.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { DataPanel, EmptyNetwork, networkRainWords, networkSummary } from "./data-panel.js";
import { NetworkCanvas } from "./editor/canvas.js";
import { placeAll } from "./editor/edits.js";
import { buildDocument, nodeWords } from "./node-model.js";
import { NodeTable, ResultsPanel } from "./results-panel.js";
import {
  documentName,
  documentProblems,
  fileStem,
  initialState,
  neededFiles,
  placementNotes,
  placeSkeleton,
  SECTION,
  stateOf,
  structureOf,
  useForms,
  useOpened,
  withoutPicture,
  withSessionNames,
} from "./state.js";

registerInfo(routing);

/** Delay of Hydrolog's layout after the last change of the network's structure [ms]. */
export const SCHEMATIC_DELAY_MS = 300;

/** The channel of the layout's runs (the network's runs use the section's). */
export const SCHEMATIC_CHANNEL = "siec-schematic";

/** Hydrolog's layout before it is asked for. */
const NO_LAYOUT = Object.freeze({ key: null, positions: null, error: null, busy: false });

/**
 * An error of the server in Polish, with the node and field it names.
 *
 * @param {unknown} error an ApiError or anything thrown
 * @returns {{title: string, text: string, node: string|null, field: string|null}} the error
 */
export function runFailure(error) {
  const doc = error && error.doc ? error.doc : { code: "internal_error", message: String((error && error.message) || error) };
  const details = doc.details || {};
  const described = describeError(doc);
  const reason = typeof details.reason === "string" ? details.reason : null;
  const own = reason && Object.hasOwn(texts.reasons, reason) ? t(texts.reasons[reason], { node: details.node_id || "–" }) : null;
  const field = typeof details.field === "string" ? details.field : null;
  const text = own || described.text;
  return {
    title: described.title,
    text: field && !own ? `${field}: ${text}` : text,
    node: typeof details.node_id === "string" ? details.node_id : null,
    field,
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
  const [schematic, setSchematic] = useState(NO_LAYOUT);
  const [run, setRun] = useState(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);
  const [note, setNote] = useState(null);
  const [scrollTo, setScrollTo] = useState(null);
  const [touched, setTouched] = useState(() => new Set());
  const [tried, setTried] = useState(false);
  const schematicSvg = useRef(null);
  const chartSvg = useRef(null);
  const sequence = useRef(0);
  const running = useRef(null);
  const drawn = useRef(0);

  // --- opening a network --------------------------------------------------------------
  const open = (doc, source, lines) => {
    const opened = stateOf(doc, source);
    setState(opened);
    setRun(null);
    setFailure(null);
    setTouched(new Set());
    setTried(false);
    setSchematic(NO_LAYOUT);
    setNote({ error: false, lines: [...lines, ...placementNotes(doc, opened)] });
  };
  // Inputs stored before the canvas have no positions: they are laid out like a file
  // without them
  useEffect(() => {
    if (state.skeleton.some((node) => !node.position)) setState((old) => ({ ...old, ...placeSkeleton(old.skeleton) }));
  }, [state.skeleton]);
  useOpened(({ doc, meta }) => {
    const problems = documentProblems(doc);
    if (problems.length) {
      setNote({ error: true, title: t(texts.file.refused, { name: meta.name }), lines: problems });
      return;
    }
    const named = withSessionNames(doc);
    open(named.doc, meta, [t(texts.file.loaded, { name: meta.name, nodes: plural(doc.nodes.length, texts.nodeForms) })]);
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
    if (companions.inflows) setState((old) => ({ ...old, inflowsFile: companions.inflows }));
  };

  const onCompanions = async (event) => {
    const chosen = [...(event.currentTarget.files || [])];
    event.currentTarget.value = "";
    if (!chosen.length) return;
    const needed = neededFiles(state);
    const companions = await uploadCompanions(chosen, needed.ratings.map((item) => item.name), needed.inflows.length > 0 && !state.inflowsFile);
    setNote({ error: false, lines: companions.lines });
    if (companions.inflows) setState((old) => ({ ...old, inflowsFile: companions.inflows }));
  };

  // --- the network and its checks -----------------------------------------------------
  const built = useMemo(
    () => (forms && state.skeleton.length ? buildDocument(forms, state) : null),
    [forms, state.network, state.skeleton, state.nodes],
  );
  const words = useMemo(
    () => new Map(state.skeleton.map((node) => [node.id, nodeWords(node, state.nodes[node.id] || {})])),
    [state.skeleton, state.nodes],
  );
  // A missing value is shown once its field was touched or „Oblicz sieć” was tried; any
  // other problem at once (as in the catalog forms)
  const visible = useMemo(
    () => (built ? built.problems.filter((item) => tried || !item.message.endsWith(" · required") || touched.has(`${item.node}|${item.key}`)) : []),
    [built, touched, tried],
  );
  const problems = useMemo(() => {
    const found = { network: {}, nodes: {} };
    for (const item of visible) {
      if (item.node === null) found.network[item.key] = item.message;
      else found.nodes[item.node] = { ...(found.nodes[item.node] || {}), [item.key]: item.message };
    }
    return found;
  }, [visible]);
  const touch = (node, before, after) => {
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    const changed = [...keys].filter((key) => JSON.stringify(before[key]) !== JSON.stringify(after[key]));
    if (changed.length) setTouched((old) => new Set([...old, ...changed.map((key) => `${node}|${key}`)]));
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
  const valid = Boolean(built) && built.problems.length === 0;
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
  // A move never marks the result stale: the key leaves the positions out (D11)
  const currentKey = built ? JSON.stringify([withoutPicture(built.document), runOptions(stem, name)]) : null;
  const layoutKey = ready
    ? JSON.stringify([
        structureOf(state.skeleton),
        state.skeleton.map((node) => (words.get(node.id) || {}).area ?? null),
        runOptions(stem, name),
        needed.ratings,
      ])
    : null;

  // --- Hydrolog's layout: its check of the network, the cells of „Uporządkuj” -----------
  useEffect(() => {
    if (!layoutKey || layoutKey === schematic.key) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      drawn.current += 1;
      const mine = drawn.current;
      setSchematic((old) => ({ ...old, busy: true }));
      // Without the positions, so Hydrolog lays the network out itself; inline, so the
      // session holds no file until „Oblicz sieć”; a network that reads rating files
      // needs its document in "in/" beside them
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
        if (mine !== drawn.current || envelope.status !== "ok") return;
        const positions = Object.fromEntries(envelope.result.nodes.map((node) => [node.id, { x: node.x, y: node.y }]));
        setSchematic({ key: layoutKey, positions, error: null, busy: false });
      } catch (error) {
        if ((error && error.name === "AbortError") || mine !== drawn.current) return;
        setSchematic({ key: layoutKey, positions: null, error: runFailure(error), busy: false });
      }
    }, SCHEMATIC_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [layoutKey]);
  const layout = schematic.key === layoutKey ? schematic.positions : null;
  // Provisional rows give way to Hydrolog's layout once it can read the network (D10);
  // this is part of opening, not an edit
  useEffect(() => {
    if (state.provisional && layout) setState((old) => ({ ...placeAll(old, layout), provisional: false }));
  }, [state.provisional, layout]);
  const tidy = () => {
    if (layout) setState((old) => ({ ...placeAll(old, layout), provisional: false }));
  };
  const shownRefusal = schematic.key === layoutKey && schematic.error ? schematic.error.text : null;
  let tidyBlocked = null;
  if (!ready) tidyBlocked = texts.canvas.tidyWaiting;
  else if (shownRefusal) tidyBlocked = t(texts.schematic.failed, { message: shownRefusal });
  else if (!layout) tidyBlocked = texts.canvas.tidyBusy;

  // --- choosing a node ------------------------------------------------------------------
  const select = (id, fromPicture = true) => {
    if (!state.skeleton.some((node) => node.id === id)) return;
    setState((old) => ({ ...old, selected: id }));
    if (active) navigate(SECTION, [id], { replace: true });
    if (fromPicture && isPhone()) openPanel("left");
    setScrollTo(id);
  };
  useEffect(() => {
    const id = path[0];
    if (id && id !== state.selected && state.skeleton.some((node) => node.id === id)) {
      setState((old) => ({ ...old, selected: id }));
    }
  }, [path[0], state.skeleton]);
  useEffect(() => {
    if (!scrollTo) return;
    const step = document.querySelector('section.section[data-section="siec"] .node-step');
    if (step && typeof step.scrollIntoView === "function") step.scrollIntoView({ block: "nearest" });
    setScrollTo(null);
  }, [scrollTo]);

  // --- „Oblicz sieć” ----------------------------------------------------------------------
  const focusProblem = () =>
    setTimeout(() => {
      const panel = document.querySelector('section.section[data-section="siec"] .view-panel.left');
      const field = panel && panel.querySelector('[aria-invalid="true"], .err');
      if (field && typeof field.focus === "function") field.focus();
    }, 0);
  const compute = async () => {
    if (!built) return;
    if (!ready) {
      setTried(true);
      const first = built.problems.find((item) => item.node);
      if (first && first.node !== state.selected) select(first.node, false);
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
    setBusy(true);
    try {
      await api.upload(new Blob([`${JSON.stringify(built.document, null, 2)}\n`], { type: "application/json" }), name);
      const envelope = await api.run("route network", options, { channel: SECTION, signal: controller.signal });
      if (mine !== sequence.current) return;
      setRun({ envelope, options, key, at: new Date() });
      setFailure(null);
      if (isPhone()) openPanel("right");
    } catch (error) {
      if ((error && error.name === "AbortError") || mine !== sequence.current) return;
      const found = runFailure(error);
      setFailure({ ...found, key });
      if (found.node && found.node !== state.selected) select(found.node, false);
    } finally {
      if (mine === sequence.current) {
        setBusy(false);
        running.current = null;
      }
    }
  };

  const clear = () => {
    reset();
    setRun(null);
    setFailure(null);
    setNote(null);
    setSchematic(NO_LAYOUT);
  };

  const save = () => {
    if (!built || !valid) return;
    const file = `${stem}.json`;
    downloadBlob(new Blob([`${JSON.stringify(built.document, null, 2)}\n`], { type: "application/json" }), file);
    toast(t(texts.file.saved, { name: file }));
  };

  // --- badge and context ------------------------------------------------------------------
  const shownFailure = failure && failure.key === currentKey ? failure : null;
  const firstProblem = visible.length ? visible[0] : null;
  let badge = null;
  if (busy) badge = status("busy");
  else if (shownFailure) badge = status("error", undefined, shownFailure.text);
  else if (firstProblem) {
    const where = firstProblem.node ? `${firstProblem.node} · ${firstProblem.key.split(".").pop()}` : firstProblem.key;
    badge = status("invalid", `${shell.status.invalid.text}: ${where}`, firstProblem.message);
  } else if (missing.length) badge = status("invalid", `${shell.status.invalid.text}: ${texts.files.short}`, missing[0]);
  else if (run && run.envelope.status === "ok" && run.key !== currentKey) badge = status("stale");
  else if (run && run.envelope.status === "ok") badge = status("ok");
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);
  const title = String(state.network.name || "").trim() || (state.source ? state.source.name : "");
  const context = state.skeleton.length ? t(texts.context, { name: title, nodes: plural(state.skeleton.length, texts.nodeForms) }) : null;
  useEffect(() => setContext(context), [context]);

  // --- the parts of the layout -------------------------------------------------------------
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const values = useMemo(() => (result ? new Map(result.nodes.map((node) => [node.id, node])) : null), [result]);
  const nodeResult = values && state.selected ? values.get(state.selected) || null : null;
  const formsProblem = formsError ? t(texts.formsFailed, { message: formsError }) : null;
  const left = {
    sub: "hydrolog-network/1",
    body: formsProblem
      ? html`<div class="form-errors" role="alert">${formsProblem}</div>`
      : !state.skeleton.length
        ? html`<${EmptyNetwork} note=${note} onLoad=${onLoad} />`
        : !forms
          ? html`<p class="muted" role="status">${common.loading}</p>`
          : html`<${DataPanel}
            state=${state}
            forms=${forms}
            words=${words}
            values=${values}
            problems=${problems}
            summary=${networkSummary(state.skeleton, words)}
            needed=${needed}
            note=${note}
            nodeResult=${nodeResult}
            networkRain=${networkRainWords(state.network)}
            canSave=${valid}
            onNetwork=${(network) => {
              touch(null, state.network, network);
              setState((old) => ({ ...old, network }));
            }}
            onRun=${(change) => setState((old) => ({ ...old, ...change }))}
            onNode=${(id, next) => {
              touch(id, state.nodes[id] || {}, next);
              setState((old) => ({ ...old, nodes: { ...old.nodes, [id]: next } }));
            }}
            onSelect=${select}
            onLoad=${onLoad}
            onCompanions=${onCompanions}
            onSave=${save}
          />`,
    foot: html`
      <button class="btn primary" type="button" data-action="compute" disabled=${!built || busy} onClick=${compute}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" /></svg>
        ${texts.compute}
      </button>
      <span class="muted small form-state" role="status">${busy
        ? texts.computing
        : run
          ? t(texts.lastRun, { time: run.at.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }) })
          : ""}</span>
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${clear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };

  const view = state.view === "table" ? "table" : "schem";
  // The canvas, once every node has a cell; a network opened without positions that
  // Hydrolog can read waits for its layout instead of showing the provisional rows first
  const waiting =
    state.skeleton.some((node) => !node.position) ||
    (state.provisional && ((!forms && !formsError) || (ready && !layout && !shownRefusal)));
  const canvas = () => {
    if (!state.skeleton.length) return html`<p class="empty-note" data-schematic="empty">${texts.schematic.empty}</p>`;
    if (waiting) return html`<p class="empty-note" role="status" data-schematic="busy">${texts.schematic.busy}</p>`;
    return html`<${NetworkCanvas}
      inputs=${state}
      words=${words}
      values=${values}
      selected=${state.selected}
      tidy=${{ blocked: tidyBlocked }}
      refusal=${shownRefusal}
      onTidy=${tidy}
      onEdit=${(next) => setState({ ...next, provisional: false })}
      onSelect=${select}
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
        onChange=${(next) => setState((old) => ({ ...old, view: next }))}
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
  return html`<${ViewLayout} left=${left} center=${center} right=${right} />`;
}
