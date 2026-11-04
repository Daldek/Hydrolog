// „Hydrogram zlewni” (plan D13, slice S3; the author's three steps of 2026-11-04): one
// watershed, `hydrograph generate` through the three steps of the panel Dane (Zlewnia,
// Hietogram, Hydrogram). A first visit is empty and runs nothing; the checks of what the
// model needs start when a model is chosen in step 3. From then on the result follows every
// change (no variants, no compute button): a change of valid data runs on channel
// "hydrogram" 250 ms later (recompute.js: debounce, abort, only the newest response
// applied); „Liczenie…” after 150 ms; invalid data run nothing and keep the last result,
// marked („Dane niepełne” with the field); an error of the server stays on its field or
// above the steps („Błąd danych”); Hydrolog's notices of a value outside its typical range
// stand on their field as warnings, which never stop a run. Nash by Lutz runs `uh nash`
// first and passes `nash_n` and `nash_k_min` on; the notices of that run stand beside those
// of `hydrograph generate`, in Wyniki and on the fields. The typical ranges the (i)
// explanations and the notes check are those the catalog documents of the two commands
// serve (`typical_ranges`), registered when the documents arrive.
//
// The section sets the store's "watershed" (the `watershed` of hydrolog-network/1, for
// Kalkulatory), its "status" and "context", and draws the store's "reference" (a quantile
// of Statystyka) on the hydrograph. The route #hydrogram/tc_method/<method> sets the method
// of tc (Kalkulatory's „Użyj w Hydrogramie zlewni”; it shows once SCS or Clark is chosen).
// A hand-off of one subcatchment („Wczytaj z Hydrografa”, here or in Sieć) arrives through
// useHandoffInbox as a patch of the inputs whose `origin` names the producer.

import { api } from "../../api.js";
import { plural } from "../../format.js";
import { withReason } from "../../forms/model.js";
import { useHandoffInbox } from "../../handoff/handoff-panel.js";
import { html, useCallback, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError } from "../../labels/errors.js";
import { hydrogram as texts } from "../../labels/hydrogram.js";
import { lossesInfo } from "../../labels/info/losses.js";
import { rainInfo } from "../../labels/info/rain.js";
import { tcInfo } from "../../labels/info/tc.js";
import { uhInfo } from "../../labels/info/uh.js";
import { describeNotice } from "../../labels/notices.js";
import { shell } from "../../labels/shell.js";
import { usePersistentState } from "../../persist.js";
import { navigate } from "../../router.js";
import { useStore } from "../../store.js";
import { registerInfo, registerServed } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { status } from "../../ui/status.js";
import { toast } from "../../ui/toast.js";
import { RenderGuard } from "../../ui/render-guard.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { DataPanel, durationText } from "./data-panel.js";
import { exportSpec } from "./export.js";
import { createChannel } from "./recompute.js";
import { CenterBody, ResultsPanel, modelLabel } from "./results-panel.js";
import {
  CHANNEL,
  COMMAND,
  LUTZ_COMMAND,
  LUTZ_SOURCES,
  NETWORK_SCHEMA,
  SECTION,
  TC_METHODS,
  checkInputs,
  checkedValues,
  fieldLabel,
  initialState,
  inputModels,
  isEmpty,
  lutzOptions,
  normalize,
  numberOf,
  panelFields,
  rangeInfoId,
  readWatershed,
  requirements,
  runNotices,
  toOptions,
  usesLutz,
  watershedErrors,
  watershedObject,
} from "./state.js";

registerInfo({ ...tcInfo, ...lossesInfo, ...uhInfo, ...rainInfo });

/**
 * The catalog documents of `hydrograph generate` and of Lutz's `uh nash`, and the network
 * schema, turned into the models that check the inputs; the typical ranges the documents
 * serve are registered with the (i) explanations.
 *
 * @returns {{models: object|null, error: string|null, retry: () => void}} the models (null
 *   until they arrive), a loading error and a retry
 */
function useModels() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ models: null, error: null });
  useEffect(() => {
    let alive = true;
    setState((old) => ({ ...old, error: null }));
    // Lutz's range is only an explanation's: without its document the section still works
    const lutz = api.command(LUTZ_COMMAND).catch(() => null);
    Promise.all([api.command(COMMAND), api.schema(NETWORK_SCHEMA), lutz])
      .then(([doc, schema, lutzDoc]) => {
        if (!alive) return;
        registerServed(doc, rangeInfoId);
        registerServed(lutzDoc, (range) => (range.method === "lutz" ? rangeInfoId(range) : null));
        setState({ models: inputModels(doc, schema), error: null });
      })
      .catch((error) => {
        if (alive) setState({ models: null, error: error && error.doc ? describeError(error.doc).text : String(error) });
      });
    return () => {
      alive = false;
    };
  }, [attempt]);
  return { ...state, retry: () => setAttempt((count) => count + 1) };
}

/**
 * The count of a watershed's fields in words: „19 pól”.
 *
 * @param {object} values the fields read
 * @returns {string} the words
 */
function fieldCount(values) {
  return plural(Object.keys(values).length, texts.watershed.fieldForms);
}

/**
 * Word an error of a run: on its field when the panel shows it (every field a tc method
 * or a model misses on its own), else above the steps.
 *
 * @param {object} doc the hydrolog-error/1 document
 * @param {boolean} lutz whether it came from Lutz's `uh nash`
 * @param {object|null} inputs the inputs of the run
 * @returns {{fields: Object<string, string>, form: {title: string, text: string}|null,
 *   text: string}} the messages
 */
function wordError(doc, lutz, inputs) {
  const described = describeError(doc);
  const details = (doc && doc.details) || {};
  const shown = inputs ? panelFields(inputs) : [];
  const place = (option) => {
    const name = lutz && Object.hasOwn(LUTZ_SOURCES, option) ? LUTZ_SOURCES[option] : option;
    if (name === "duration_min" && inputs && inputs.rain_source === "pmaxtp") return "pmaxtp_duration_min";
    return shown.includes(name) ? name : null;
  };
  const fields = {};
  if (described.reason === "missing_field") {
    const missing = Array.isArray(details.missing) ? details.missing : [described.option];
    const text = typeof details.method === "string" ? t(texts.missingField, { method: details.method }) : texts.missingFieldPlain;
    for (const option of missing) {
      const name = typeof option === "string" ? place(option) : null;
      if (name) fields[name] = withReason(text, "missing_field");
    }
    if (Object.keys(fields).length === missing.length) return { fields, form: null, text: described.text };
  } else if (typeof described.option === "string" && place(described.option)) {
    fields[place(described.option)] = withReason(described.text, described.reason);
    return { fields, form: null, text: described.text };
  }
  return { fields, form: { title: described.title || texts.formError, text: described.text }, text: described.text };
}

/**
 * The section „Hydrogram zlewni”.
 *
 * @param {{path: string[]}} props the route's path ("tc_method", "<method>" sets the method
 *   of tc)
 * @returns {object} the section
 */
export default function Hydrogram({ path = [] }) {
  const docs = useModels();
  const [stored, setState, reset] = usePersistentState(SECTION, initialState);
  const inputs = useMemo(() => normalize(stored), [stored]);
  const [, setStatus] = useStore("status");
  const [, setContext] = useStore("context");
  const [, setWatershedStore] = useStore("watershed");
  const [reference, setReference] = useStore("reference");
  const [tab, setTab] = useState("chart");
  const [run, setRun] = useState(null);
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);
  const [broken, setBroken] = useState(null);
  const chartSvg = useRef(null);
  const outcome = useRef(null);
  const channel = useMemo(
    () =>
      createChannel({
        onBusy: setBusy,
        onOutcome: (next) => outcome.current(next),
      }),
    [],
  );
  useEffect(() => () => channel.dispose(), [channel]);

  /** Replace inputs (a patch of the inputs; a watershed file and a hand-off use it). */
  const set = useCallback((patch) => setState((old) => ({ ...normalize(old), ...patch })), []);
  useHandoffInbox(SECTION, set);
  const setField = useCallback(
    (name, text) =>
      setState((old) => {
        const base = normalize(old);
        return { ...base, watershed: { ...base.watershed, [name]: text } };
      }),
    [],
  );

  // Kalkulatory's „Użyj w Hydrogramie zlewni”: #hydrogram/tc_method/<method>
  const route = path.join("/");
  useEffect(() => {
    if (path[0] === "tc_method" && TC_METHODS.includes(path[1])) {
      set({ tc_method: path[1], tc_manual: false });
      navigate(SECTION, [], { replace: true });
    }
  }, [route]);

  // The checks: errors stop a run; the warnings of the shown run's notices do not
  const shownRun = run ? { inputs: run.inputs, notices: runNotices(run) } : null;
  const checked = useMemo(
    () => (docs.models ? checkInputs(inputs, docs.models, shownRun) : null),
    [docs.models, inputs, run],
  );
  const required = useMemo(() => requirements(inputs).required, [inputs]);
  const valid = checked !== null && inputs.uh_model !== null && Object.keys(checked.errors).length === 0;
  const request = useMemo(() => {
    if (!valid) return null;
    return { inputs, options: toOptions(inputs), lutz: usesLutz(inputs) ? lutzOptions(inputs) : null };
  }, [valid, inputs]);
  const key = request ? JSON.stringify([request.options, request.lutz]) : null;
  const latestKey = useRef(key);
  latestKey.current = key;

  outcome.current = (next) => {
    // The task returns its errors; a rejection would be a fault of the GUI itself
    const value = next.ok
      ? next.value
      : { key: latestKey.current, stage: "generate", error: { code: "internal_error", message: String(next.error) }, inputs: null };
    if (value.error) {
      setFailure({ key: value.key, ...wordError(value.error, value.stage === "lutz", value.inputs) });
      return;
    }
    const envelope = value.envelope;
    if (envelope.status !== "ok") {
      const words = (envelope.notices || []).map((notice) => describeNotice(notice).text).join(" ");
      setFailure({ key: value.key, fields: {}, form: { title: texts.formError, text: words }, text: words });
      return;
    }
    setFailure(null);
    setRun({ ...value, values: checkedValues(value.inputs, envelope.result) });
  };

  useEffect(() => {
    if (!docs.models) return;
    if (!request) {
      channel.cancel();
      return;
    }
    if ((run && run.key === key) || (failure && failure.key === key)) {
      channel.cancel();
      return;
    }
    const sent = { ...request, key };
    channel.request(async (signal) => {
      let stage = "generate";
      try {
        let lutz = null;
        let lutzNotices = [];
        let options = sent.options;
        if (sent.lutz) {
          stage = "lutz";
          const first = await api.run(LUTZ_COMMAND, sent.lutz, { channel: CHANNEL, signal });
          if (first.status !== "ok") return { key: sent.key, inputs: sent.inputs, envelope: first };
          lutz = first.result;
          lutzNotices = first.notices || [];
          options = toOptions(sent.inputs, lutz.parameters);
          stage = "generate";
        }
        const envelope = await api.run(COMMAND, options, { channel: CHANNEL, signal });
        return { key: sent.key, inputs: sent.inputs, options, envelope, lutz, lutzNotices };
      } catch (error) {
        if (error && error.name === "AbortError") throw error;
        const doc = error && error.doc ? error.doc : { code: "internal_error", message: String(error) };
        return { key: sent.key, stage, error: doc, inputs: sent.inputs };
      }
    });
  }, [key, docs.models]);

  // The store's watershed: the last valid one with an area (Kalkulatory reads it)
  const watershedKey =
    docs.models &&
    numberOf(inputs.watershed.area_km2) !== null &&
    Object.keys(watershedErrors(inputs.watershed, docs.models)).length === 0
      ? JSON.stringify(watershedObject(inputs.watershed))
      : null;
  useEffect(() => {
    if (watershedKey) setWatershedStore(JSON.parse(watershedKey));
  }, [watershedKey]);

  const current = failure && failure.key === key ? failure : null;
  const errors = { ...(checked ? checked.errors : {}), ...(current ? current.fields : {}) };
  const warnings = checked ? checked.warnings : {};
  const firstProblem = checked ? Object.keys(checked.errors)[0] : null;
  let stale = null;
  if (run && firstProblem) stale = { kind: "invalid", field: fieldLabel(firstProblem) };
  else if (run && current) stale = { kind: "error", text: current.text };

  // The badge and the state under the panel Dane
  let badge = null;
  let calc = null;
  if (firstProblem) {
    badge = status("invalid", `${shell.status.invalid.text}: ${firstProblem}`);
    calc = { kind: "warn", text: t(texts.calc.invalid, { field: fieldLabel(firstProblem) }) };
  } else if (current) {
    badge = status("error", undefined, current.text);
    calc = { kind: "bad", text: texts.calc.error };
  } else if (busy) {
    badge = status("busy");
    calc = { kind: "busy", text: texts.calc.busy };
  } else if (checked !== null && inputs.uh_model === null) {
    calc = { kind: "idle", text: texts.calc.model };
  } else if (run && broken === run) {
    badge = status("error", common.render.badge, common.render.status);
    calc = { kind: "bad", text: common.render.status };
  } else if (run && run.key === key) {
    badge = status("ok");
    calc = { kind: "ok", text: texts.calc.ok };
  } else if (checked !== null) {
    calc = { kind: "ok", text: texts.calc.waiting };
    if (run) badge = status("ok");
  }
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);

  // The breadcrumbs: the watershed, the probability and the duration of the rainfall
  const named = String(inputs.watershed.name || "").trim();
  const hasWatershed = Object.keys(watershedObject(inputs.watershed)).length > 0;
  const name = named || texts.context.unnamed;
  let context = name;
  if (inputs.rain_source === "series") context = t(texts.context.series, { name });
  else if (inputs.rain_source === "design" && !isEmpty(inputs.total_mm) && !isEmpty(inputs.duration_min)) {
    context = t(texts.context.design, { name, total: inputs.total_mm, duration: durationText(inputs.duration_min) });
  } else if (inputs.rain_source === "pmaxtp" && !isEmpty(inputs.pmaxtp_probability_pct) && !isEmpty(inputs.pmaxtp_duration_min)) {
    context = t(texts.context.pmaxtp, {
      name,
      p: String(inputs.pmaxtp_probability_pct).replace(".", ","),
      duration: durationText(inputs.pmaxtp_duration_min),
    });
  }
  useEffect(() => setContext(hasWatershed ? context : null), [context, hasWatershed]);

  const spec = useMemo(() => {
    if (!run) return null;
    const subject = (run.options.watershed && run.options.watershed.name) || SECTION;
    return exportSpec({ subject, options: run.options, envelope: run.envelope, chartSvg });
  }, [run]);

  const onFile = async (file) => {
    try {
      let doc;
      try {
        doc = JSON.parse(await file.text());
      } catch {
        throw new Error(texts.watershed.fileNotJson);
      }
      const read = readWatershed(doc);
      if (read.missing) throw new Error(t(texts.watershed.fileNotWatershed, { missing: read.missing.join(", ") }));
      const time = new Date().toLocaleString("pl-PL", { dateStyle: "medium", timeStyle: "short" });
      set({
        watershed: read.texts,
        origin: {
          label: file.name,
          title: t(texts.watershed.fileTitle, { file: file.name }),
          detail: t(texts.watershed.detailFile, { time, fields: fieldCount(read.values) }),
          mark: null,
          values: read.values,
        },
      });
      toast(t(texts.watershed.fileLoaded, { file: file.name }));
    } catch (error) {
      toast(t(texts.watershed.fileFailed, { file: file.name, message: error.message || String(error) }), "bad");
    }
  };

  // „Wyczyść”: the steps empty, as on a first visit; Kalkulatory loses the watershed too
  const clear = () => {
    channel.cancel();
    reset();
    setRun(null);
    setFailure(null);
    setBroken(null);
    setWatershedStore(null);
  };

  const values = useMemo(() => checkedValues(inputs, run && run.key === key ? run.envelope.result : null), [inputs, run, key]);
  const result = run ? run.envelope.result : null;
  const version = run ? run.envelope.version : null;
  const dimmed = busy ? " computing" : "";
  // A result that does not draw is marked, never shown as the current one (RenderGuard)
  const onDrawError = () => setBroken(run);

  const left = {
    sub: texts.dataSub,
    body: html`
      ${docs.error
        ? html`<div class="form-errors" role="alert">
            <div>${docs.error}</div>
            <button class="btn sm" type="button" onClick=${docs.retry}>${common.actions.retry}</button>
          </div>`
        : null}
      ${docs.models
        ? html`<${DataPanel}
            inputs=${inputs}
            errors=${errors}
            warnings=${warnings}
            required=${required}
            formError=${current ? current.form : null}
            set=${set}
            setField=${setField}
            onFile=${onFile}
            result=${result}
            lutz=${run && usesLutz(inputs) ? run.lutz : null}
            models=${docs.models}
            infoValues=${values}
          />`
        : docs.error
          ? null
          : html`<p class="muted" role="status">${texts.loading}</p>`}
    `,
    foot: html`
      <span class=${`calc-state${calc && calc.kind !== "ok" ? ` ${calc.kind}` : ""}`} data-calc=${calc ? calc.kind : ""} role="status">
        <i class="dot" aria-hidden="true"></i><span>${calc ? calc.text : texts.loading}</span>
      </span>
      ${version ? html`<span class="muted small">${t(texts.version, { version })}</span>` : null}
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${clear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };
  const center = {
    label: texts.center.tabs.chart,
    bar: html`
      <${Seg}
        items=${[
          { value: "chart", label: texts.center.tabs.chart },
          { value: "table", label: texts.center.tabs.table },
        ]}
        value=${tab}
        onChange=${setTab}
        label=${texts.center.view}
      />
      <span class="hint">
        <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>
        <span>${texts.center.hint}</span>
      </span>
    `,
    body: html`<div class=${`result-area${dimmed}`} aria-busy=${busy ? "true" : "false"} data-hg-center="">
      <${RenderGuard} name="center" resetKey=${run} onError=${onDrawError}>
        <${CenterBody}
          run=${run}
          tab=${tab}
          reference=${reference}
          chartSvg=${chartSvg}
          onClearReference=${() => setReference(null)}
          stale=${stale}
        />
      <//>
    </div>`,
  };
  const right = {
    sub: run ? t(texts.results.sub, { model: modelLabel(run.inputs), amc: result.amc }) : null,
    body: html`<div class=${`result-area${dimmed}`} aria-busy=${busy ? "true" : "false"} data-hg-results="">
      <${RenderGuard} name="results" resetKey=${run} onError=${onDrawError}>
        <${ResultsPanel} run=${run} spec=${spec} stale=${stale} current=${inputs} />
      <//>
    </div>`,
  };
  return html`<${ViewLayout} left=${left} center=${center} right=${right} />`;
}
