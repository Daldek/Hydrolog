// „Kalkulatory” (plan S5): sixteen calculators. The comparison of the tc methods runs
// `tc watershed` once per method with the watershed of Hydrogram zlewni (store "watershed")
// and the overland fields set here, and words each method by Hydrolog's notices; „Użyj w
// Hydrogramie zlewni” hands the chosen method to Hydrogram (#hydrogram/tc_method/<method>).
// The fifteen others are catalog forms (plan D11), empty when first opened and filled with
// the fields of the watershed of Hydrogram zlewni when there is one (the tc commands with
// what `tc watershed` derives from it). Every calculator computes on its button and marks
// its result stale after a change (plan D13). The guide (instrukcja/#kalkulatory) has a
// worked example.

import { api } from "../../api.js";
import { plural } from "../../format.js";
import { FORM_ERROR } from "../../forms/command-form.js";
import { commandEntry, fieldModel, isActive, ONE_OF_KEY, outputDefaults, toOptions, validate, withReason } from "../../forms/model.js";
import { analyzeResult } from "../../forms/result-view.js";
import { html, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError, errors as errorTexts } from "../../labels/errors.js";
import { tcInfo } from "../../labels/info/tc.js";
import { kalkulatory as texts } from "../../labels/kalkulatory.js";
import { shell } from "../../labels/shell.js";
import { usePersistentState } from "../../persist.js";
import { navigate } from "../../router.js";
import { useStore } from "../../store.js";
import { registerInfo } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { isPhone, openPanel } from "../../ui/sheet.js";
import { status } from "../../ui/status.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { chartSub } from "./charts.js";
import { compareRows } from "./compare.js";
import { CalculatorForm, CalculatorList, CompareForm } from "./data-panel.js";
import { CommandCenter, CommandResults, CompareCenter, CompareResults } from "./results-panel.js";
import {
  calculatorOf,
  comparedWatershed,
  COMPARE,
  copiedFields,
  formFields,
  FROM_WATERSHED,
  hydrogramMethod,
  idOfPath,
  initialState,
  OVERLAND_FIELDS,
  OVERLAND_SOURCE,
  pathOf,
  SECTION,
  TC_COMMAND,
  TC_METHODS,
  useCatalogDocs,
} from "./state.js";

registerInfo(tcInfo);

const FORM_ID = "kc-form";
const CLOCK = new Intl.DateTimeFormat("pl-PL", { hour: "2-digit", minute: "2-digit" });

/**
 * The message of a failed request, in Polish: a missing field of the watershed by its name.
 *
 * @param {unknown} error the error
 * @returns {{text: string, title: string|null, option: string|null, reason: string|null}} the message
 */
function describeFailure(error) {
  if (!error || !error.doc) return { text: String((error && error.message) || error), title: null, option: null, reason: null };
  const details = error.doc.details || {};
  if (details.reason === "missing_field" && Array.isArray(details.missing)) {
    return { text: t(texts.results.missing, { fields: details.missing.join(", ") }), title: error.doc.title || null, option: details.option || null, reason: "missing_field" };
  }
  const described = describeError(error.doc);
  return { text: described.text, title: described.title, option: described.option || null, reason: described.reason || null };
}

/**
 * The names of the options whose values differ between two forms.
 *
 * @param {object} before the old values
 * @param {object} after the new values
 * @returns {string[]} the changed names
 */
function changedNames(before, after) {
  const names = new Set([...Object.keys(before), ...Object.keys(after)]);
  return [...names].filter((name) => JSON.stringify(before[name]) !== JSON.stringify(after[name]));
}

/**
 * The section „Kalkulatory”.
 *
 * @param {{active: boolean, path: string[]}} props whether the section is shown, and the
 *   route's path ("porownanie-tc", or a command's words: "tc", "kirpich")
 * @returns {object} the section
 */
export default function Kalkulatory({ active, path = [] }) {
  const catalog = useCatalogDocs();
  const [state, setState, reset] = usePersistentState(SECTION, initialState);
  const [watershed] = useStore("watershed");
  const [, setStatus] = useStore("status");
  const [, setContext] = useStore("context");
  const [tab, setTab] = useState("chart");
  const [commandTab, setCommandTab] = useState("result");
  const [compareRun, setCompareRun] = useState(null);
  const [runs, setRuns] = useState({});
  const [serverErrors, setServerErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [tried, setTried] = useState({});
  const [busy, setBusy] = useState(null);
  const [fills, setFills] = useState({});
  const [used, setUsed] = useState(() => hydrogramMethod());
  const [selected, setSelected] = useState(null);
  const sequence = useRef(0);
  const running = useRef(null);
  const chartSvg = useRef(null);
  const commandSvg = useRef(null);
  const unfilled = useRef(new Set());

  const routed = idOfPath(path);
  const current = routed || (calculatorOf(state.current) ? state.current : COMPARE);
  useEffect(() => {
    if (current !== state.current) setState((old) => ({ ...old, current }));
  }, [current]);
  useEffect(() => {
    if (active) setUsed(hydrogramMethod());
  }, [active]);

  const compared = useMemo(() => comparedWatershed(watershed, state.overrides), [watershed, state.overrides]);
  const methods = TC_METHODS.filter((method) => state.methods[method]);

  // --- a calculator's command ---------------------------------------------------------
  const isCommand = current !== COMPARE;
  const doc = isCommand ? catalog.docs.get(current) || null : null;
  const values = (isCommand && state.values[current]) || {};
  const model = useMemo(() => (doc ? fieldModel(doc, { values }) : null), [doc, values]);
  const problems = useMemo(() => (model ? validate(model, values) : {}), [model, values]);
  const valid = Boolean(model) && !Object.keys(problems).length;
  const options = useMemo(() => (valid ? toOptions(model, values) : null), [valid, model, values]);
  const fillable = isCommand && (Object.hasOwn(FROM_WATERSHED, current) || current === "morphometry watershed" || Boolean(calculatorOf(current).method));

  const fill = async (command, base) => {
    const found = catalog.docs.get(command);
    if (!found || !watershed) return;
    const calculator = calculatorOf(command);
    let fields = null;
    let names = [];
    if (calculator.method) {
      try {
        const envelope = await api.run(TC_COMMAND, { watershed: compared, method: calculator.method }, { channel: `${SECTION}-wypelnij` });
        if (envelope.status !== "ok") return;
        names = Object.keys(envelope.result.parameters);
        fields = formFields(found, envelope.result.parameters);
      } catch (error) {
        setFills((old) => ({ ...old, [command]: { error: t(texts.watershed.fillFailed, { message: describeFailure(error).text }) } }));
        return;
      }
    } else if (command === "morphometry watershed") {
      const group = (commandEntry(found).one_of || []).findIndex((members) => members.includes("watershed"));
      names = ["watershed"];
      fields = { watershed: JSON.stringify(watershed), ...(group >= 0 ? { [ONE_OF_KEY]: group } : {}) };
    } else {
      const copied = copiedFields(command, watershed) || {};
      names = Object.keys(copied);
      fields = formFields(found, copied);
    }
    if (!names.length) {
      setFills((old) => ({ ...old, [command]: { text: texts.watershed.notUsed } }));
      return;
    }
    setState((old) => ({ ...old, values: { ...old.values, [command]: { ...(old.values[command] || base || {}), ...fields } } }));
    setFills((old) => ({ ...old, [command]: { text: t(texts.watershed.filled, { names: names.map((name) => `\`${name}\``).join(", ") }) } }));
  };

  // A command opened for the first time: an empty form, then the watershed's fields (now,
  // or when the watershed arrives, unless the form was edited meanwhile)
  useEffect(() => {
    if (!isCommand || !doc) return;
    if (!state.values[current]) {
      const first = outputDefaults(fieldModel(doc));
      setState((old) => (old.values[current] ? old : { ...old, values: { ...old.values, [current]: first } }));
      if (fillable && watershed) fill(current, first);
      else if (fillable) unfilled.current.add(current);
    } else if (watershed && unfilled.current.has(current)) {
      unfilled.current.delete(current);
      if (!touched[current]) fill(current);
    }
  }, [current, doc, watershed]);

  // --- the comparison ---------------------------------------------------------------
  const overlandFields = useMemo(() => {
    const fields = [];
    for (const name of OVERLAND_FIELDS) {
      const source = catalog.docs.get(OVERLAND_SOURCE[name]);
      const field = source ? fieldModel(source).fields.find((item) => item.name === name) : null;
      if (field) fields.push({ ...field, required: false, groups: [], member: false, requires: [], excludes: [], disabledBy: null });
    }
    return fields;
  }, [catalog.docs.get("tc kerby-kirpich"), catalog.docs.get("tc faa")]);
  const overlandProblems = useMemo(() => {
    const typed = {};
    for (const name of OVERLAND_FIELDS) if (state.overrides[name] !== undefined) typed[name] = state.overrides[name];
    return validate({ fields: overlandFields, oneOf: null }, typed);
  }, [overlandFields, state.overrides]);
  const methodProblem = methods.length ? null : texts.compare.noMethods;
  const compareKey = JSON.stringify([compared, methods]);
  const rows = useMemo(() => (compareRun ? compareRows(compareRun, used) : null), [compareRun, used]);
  useEffect(() => {
    if (!rows) return;
    if (selected && rows.some((row) => row.method === selected && row.ok)) return;
    const pick = rows.find((row) => row.used && row.ok) || rows.find((row) => row.ok && row.cls.startsWith("ok")) || rows.find((row) => row.ok);
    setSelected(pick ? pick.method : null);
  }, [rows]);

  // --- runs -------------------------------------------------------------------------
  const focusFirstProblem = () =>
    setTimeout(() => {
      const form = document.getElementById(FORM_ID);
      const field = form && form.querySelector('[aria-invalid="true"]');
      if (field) field.focus();
    }, 0);

  const start = () => {
    sequence.current += 1;
    if (running.current) running.current.abort();
    const controller = new AbortController();
    running.current = controller;
    return { mine: sequence.current, signal: controller.signal };
  };
  const finish = (mine) => {
    if (mine === sequence.current) {
      setBusy(null);
      running.current = null;
    }
  };

  const runCompare = async () => {
    if (!compared || methodProblem || Object.keys(overlandProblems).length) {
      setTried((old) => ({ ...old, [COMPARE]: true }));
      focusFirstProblem();
      return;
    }
    const { mine, signal } = start();
    const sent = compared;
    const chosen = [...methods];
    const key = compareKey;
    setBusy(COMPARE);
    try {
      const outcomes = {};
      await Promise.all(
        chosen.map((method) =>
          api
            .run(TC_COMMAND, { watershed: sent, method }, { channel: `${SECTION}-tc-${method}`, signal })
            .then((envelope) => {
              outcomes[method] = { envelope };
            })
            .catch((error) => {
              if (error && error.name === "AbortError") throw error;
              outcomes[method] = { error: describeFailure(error) };
            }),
        ),
      );
      if (mine !== sequence.current) return;
      setUsed(hydrogramMethod());
      setCompareRun({ methods: chosen, outcomes, watershed: sent, key, at: new Date() });
      if (isPhone()) openPanel("right");
    } catch (error) {
      if (error && error.name === "AbortError") return;
    } finally {
      finish(mine);
    }
  };

  const runCommand = async () => {
    if (!model) return;
    if (!valid) {
      setTried((old) => ({ ...old, [current]: true }));
      focusFirstProblem();
      return;
    }
    const { mine, signal } = start();
    const command = current;
    const sent = options;
    setBusy(command);
    try {
      const envelope = await api.run(command, sent, { channel: SECTION, signal });
      if (mine !== sequence.current) return;
      setRuns((old) => ({ ...old, [command]: { command, options: sent, envelope, analysis: analyzeResult(envelope), key: JSON.stringify(sent), at: new Date() } }));
      setServerErrors((old) => ({ ...old, [command]: {} }));
      if (isPhone()) openPanel("right");
    } catch (error) {
      if (error && error.name === "AbortError") return;
      if (mine !== sequence.current) return;
      const described = describeFailure(error);
      const field = described.option && model.fields.find((item) => item.name === described.option);
      const message = withReason(described.text, described.reason);
      setServerErrors((old) => ({
        ...old,
        [command]: field && isActive(model, field) ? { [described.option]: message } : { [FORM_ERROR]: { title: described.title, text: message } },
      }));
      focusFirstProblem();
    } finally {
      finish(mine);
    }
  };

  // --- changes ----------------------------------------------------------------------
  const pick = (id) => {
    setState((old) => ({ ...old, current: id }));
    navigate(SECTION, pathOf(id), { replace: true });
  };

  const onChange = (next) => {
    const changed = changedNames(values, next);
    setTouched((old) => ({ ...old, [current]: { ...(old[current] || {}), ...Object.fromEntries(changed.map((name) => [name, true])) } }));
    const fromServer = serverErrors[current] || {};
    if (Object.keys(fromServer).length) {
      const left = { ...fromServer };
      for (const name of [...changed, FORM_ERROR]) delete left[name];
      setServerErrors((old) => ({ ...old, [current]: left }));
    }
    setState((old) => ({ ...old, values: { ...old.values, [current]: next } }));
  };

  const onMethod = (method, on) => setState((old) => ({ ...old, methods: { ...old.methods, [method]: on } }));
  const onOverride = (name, text) => {
    setTouched((old) => ({ ...old, [COMPARE]: { ...(old[COMPARE] || {}), [name]: true } }));
    setState((old) => ({ ...old, overrides: { ...old.overrides, [name]: text } }));
  };

  const useInHydrogram = () => {
    if (!selected) return;
    navigate("hydrogram", ["tc_method", selected]);
  };

  const clear = () => {
    if (running.current) running.current.abort();
    sequence.current += 1;
    reset();
    setCompareRun(null);
    setRuns({});
    setServerErrors({});
    setTouched({});
    setTried({});
    setFills({});
    setBusy(null);
    setSelected(null);
  };

  // --- messages and the badge -------------------------------------------------------
  const shownErrors = {};
  let visibleCount = 0;
  if (isCommand) {
    Object.assign(shownErrors, serverErrors[current] || {});
    const seen = touched[current] || {};
    for (const [name, message] of Object.entries(problems)) {
      if (!message.endsWith(" · required") || tried[current] || seen[name]) shownErrors[name] = message;
    }
    visibleCount = Object.keys(shownErrors).length;
  } else {
    Object.assign(shownErrors, overlandProblems);
    visibleCount = Object.keys(overlandProblems).length + (methodProblem ? 1 : 0);
  }
  const run = isCommand ? runs[current] || null : null;
  const busyHere = busy === current;
  let badge = null;
  if (busyHere) badge = status("busy");
  else if (isCommand) {
    const serverMessage = Object.values(serverErrors[current] || {})[0];
    if (serverMessage) badge = status("error", undefined, typeof serverMessage === "object" ? serverMessage.text : serverMessage);
    else if (visibleCount) badge = status("invalid", `${shell.status.invalid.text}: ${Object.keys(shownErrors)[0]}`);
    else if (run && run.envelope.status === "ok" && run.key !== JSON.stringify(options)) badge = status("stale");
    else if (run && run.envelope.status === "ok") badge = status("ok");
  } else if (visibleCount) {
    badge = status("invalid", `${shell.status.invalid.text}: ${Object.keys(overlandProblems)[0] || "method"}`);
  } else if (compareRun && compareRun.key !== compareKey) badge = status("stale");
  else if (compareRun) badge = status("ok");
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);

  const name = watershed ? watershed.name || texts.watershed.unnamed : null;
  const context = isCommand
    ? name
      ? `${current} · ${name}`
      : current
    : name
      ? t(texts.compare.context, { name })
      : texts.compare.contextNone;
  useEffect(() => setContext(context), [context]);

  // --- the layout -------------------------------------------------------------------
  const lastAt = isCommand ? run && run.at : compareRun && compareRun.at;
  let footState = "";
  if (busyHere) footState = texts.computing;
  else if (visibleCount && (isCommand || tried[COMPARE] || Object.keys(overlandProblems).length)) {
    footState = t(errorTexts.count, { count: plural(visibleCount, errorTexts.countForms) });
  } else if (lastAt) footState = t(texts.lastRun, { time: CLOCK.format(lastAt) });
  else if (!isCommand) footState = t(texts.compare.runs, { count: methods.length });

  let form = null;
  if (!isCommand) {
    form = html`<${CompareForm}
      watershed=${watershed}
      methods=${state.methods}
      overrides=${state.overrides}
      fields=${overlandFields}
      errors=${overlandProblems}
      problem=${methodProblem}
      formId=${FORM_ID}
      onMethod=${onMethod}
      onOverride=${onOverride}
      onSubmit=${runCompare}
    />`;
  } else if (doc) {
    form = html`<${CalculatorForm}
      doc=${doc}
      values=${values}
      errors=${shownErrors}
      watershed=${watershed}
      fillable=${fillable}
      fill=${fills[current] || null}
      formId=${FORM_ID}
      onChange=${onChange}
      onFill=${() => fill(current)}
      onSubmit=${runCommand}
    />`;
  } else if (catalog.errors.has(current)) {
    form = html`<p class="err" role="alert">${t(texts.loadFailed, { command: current, message: catalog.errors.get(current) })}</p>`;
  } else {
    form = html`<p class="muted" role="status">${texts.loading}</p>`;
  }
  const disabled = busyHere || (isCommand ? !model || visibleCount > 0 : !compared || visibleCount > 0);

  const left = {
    sub: t(texts.count, { count: 16 }),
    body: html`
      <${CalculatorList}
        docs=${catalog.docs}
        group=${state.group}
        query=${state.query}
        current=${current}
        active=${active}
        onGroup=${(group) => setState((old) => ({ ...old, group }))}
        onQuery=${(query) => setState((old) => ({ ...old, query }))}
        onPick=${pick}
      />
      ${form}
    `,
    foot: html`
      <button class="btn primary" type="submit" form=${FORM_ID} disabled=${disabled}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" /></svg>
        ${texts.compute}
      </button>
      <span class="muted small form-state" role="status">${footState}</span>
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${clear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };

  const hint = (text) => html`<span class="hint">
    <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>
    <span>${text}</span>
  </span>`;
  const center = isCommand
    ? {
        label: texts.tabs[commandTab],
        bar: html`
          <${Seg}
            items=${[
              { value: "result", label: texts.tabs.result },
              { value: "json", label: texts.tabs.json },
            ]}
            value=${commandTab}
            onChange=${setCommandTab}
            label=${texts.view}
          />
          ${hint(texts.hintCommand)}
        `,
        body: html`<div class=${`result-area${busyHere ? " computing" : ""}`} aria-busy=${busyHere ? "true" : "false"}>
          <${CommandCenter} run=${run} tab=${commandTab} />
        </div>`,
      }
    : {
        label: texts.tabs[tab],
        bar: html`
          <${Seg}
            items=${[
              { value: "chart", label: texts.tabs.chart },
              { value: "table", label: texts.tabs.table },
            ]}
            value=${tab}
            onChange=${setTab}
            label=${texts.view}
          />
          ${hint(texts.hint)}
        `,
        body: html`<div class=${`result-area${busyHere ? " computing" : ""}`} aria-busy=${busyHere ? "true" : "false"}>
          <${CompareCenter} rows=${rows} tab=${tab} sub=${compareRun ? chartSub(compareRun.watershed) : null} chartSvg=${chartSvg} />
        </div>`,
      };
  const right = isCommand
    ? {
        sub: run ? run.command : null,
        body: html`<div class=${`result-area${busyHere ? " computing" : ""}`}>
          <${CommandResults} run=${run} chartSvg=${commandSvg} />
        </div>`,
      }
    : {
        sub: compareRun ? texts.results.sub : null,
        body: html`<div class=${`result-area${busyHere ? " computing" : ""}`}>
          <${CompareResults}
            run=${compareRun}
            rows=${rows}
            selected=${selected}
            onSelect=${setSelected}
            onUse=${useInHydrogram}
            usable=${Boolean(selected) && selected !== used}
          />
        </div>`,
      };
  return html`<${ViewLayout} left=${left} center=${center} right=${right} />`;
}
