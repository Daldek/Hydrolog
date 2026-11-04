// „Wszystkie polecenia”: every command of the catalog (those the GUI's server runs) as a
// form generated from its commands-1 entry, run on its button, with the generic result
// view (plan D11). A first visit chooses no command and a form starts empty; the guide
// (instrukcja/#polecenia) has a worked example. The result is marked stale after a change
// („Dane zmienione: oblicz ponownie”, plan D13).

import { api } from "../../api.js";
import { plural } from "../../format.js";
import { CommandForm, FORM_ERROR } from "../../forms/command-form.js";
import { fieldModel, isActive, outputDefaults, toOptions, validate, withReason } from "../../forms/model.js";
import { analyzeResult } from "../../forms/result-view.js";
import { html, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError, errors as errorTexts } from "../../labels/errors.js";
import { polecenia as texts } from "../../labels/polecenia.js";
import { shell } from "../../labels/shell.js";
import { usePersistentState } from "../../persist.js";
import { navigate } from "../../router.js";
import { useStore } from "../../store.js";
import { Seg } from "../../ui/seg.js";
import { isPhone, openPanel } from "../../ui/sheet.js";
import { status } from "../../ui/status.js";
import { EmptyHint } from "../../ui/empty-hint.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { CommandList } from "./data-panel.js";
import { CenterBody, ResultsPanel } from "./results-panel.js";
import { SECTION, groupsOf, initialState, useCatalog } from "./state.js";

const FORM_ID = "pc-form";

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
 * The section „Wszystkie polecenia”.
 *
 * @param {{active: boolean, path: string[]}} props whether the section is shown, and the
 *   route's path ("uh", "nash" opens uh nash)
 * @returns {object} the section
 */
export default function Polecenia({ active, path = [] }) {
  const catalog = useCatalog();
  const [state, setState, reset] = usePersistentState(SECTION, initialState);
  const [, setStatus] = useStore("status");
  const [, setContext] = useStore("context");
  const [tab, setTab] = useState("table");
  const [touched, setTouched] = useState({});
  const [tried, setTried] = useState({});
  const [runs, setRuns] = useState({});
  const [serverErrors, setServerErrors] = useState({});
  const [busy, setBusy] = useState(null);
  const sequence = useRef(0);
  const running = useRef(null);
  const chartSvg = useRef(null);

  const names = catalog.commands ? catalog.commands.map((item) => item.name) : [];
  const routed = path.length === 2 ? `${path[0]} ${path[1]}` : null;
  let command = null;
  for (const candidate of [routed, state.command]) {
    if (candidate && names.includes(candidate)) {
      command = candidate;
      break;
    }
  }
  const doc = command ? catalog.docs.get(command) || null : null;

  useEffect(() => {
    if (!command || !doc || state.values[command]) return;
    setState((old) => (old.values[command] ? old : { ...old, values: { ...old.values, [command]: outputDefaults(fieldModel(doc)) } }));
  }, [command, doc, state.values]);
  useEffect(() => {
    if (command && command !== state.command) setState((old) => ({ ...old, command }));
  }, [command]);

  const values = (command && state.values[command]) || {};
  const model = useMemo(() => (doc ? fieldModel(doc, { values }) : null), [doc, values]);
  const problems = useMemo(() => (model ? validate(model, values) : {}), [model, values]);
  const valid = Boolean(model) && !Object.keys(problems).length;
  const options = useMemo(() => (valid ? toOptions(model, values) : null), [valid, model, values]);
  const run = command ? runs[command] || null : null;
  const fromServer = (command && serverErrors[command]) || {};
  const seen = (command && touched[command]) || {};
  const shownErrors = { ...fromServer };
  for (const [name, message] of Object.entries(problems)) {
    if (!message.endsWith(" · required") || (command && tried[command]) || seen[name]) shownErrors[name] = message;
  }
  const visibleCount = Object.keys(shownErrors).length;

  const onChange = (next) => {
    const changed = changedNames(values, next);
    setTouched((old) => ({ ...old, [command]: { ...(old[command] || {}), ...Object.fromEntries(changed.map((name) => [name, true])) } }));
    if (Object.keys(fromServer).length) {
      const left = { ...fromServer };
      for (const name of [...changed, FORM_ERROR]) delete left[name];
      setServerErrors((old) => ({ ...old, [command]: left }));
    }
    setState((old) => ({ ...old, values: { ...old.values, [command]: next } }));
  };

  const pick = (name) => {
    setState((old) => ({ ...old, command: name }));
    navigate(SECTION, name.split(" "), { replace: true });
  };

  const focusFirstProblem = () =>
    setTimeout(() => {
      const form = document.getElementById(FORM_ID);
      const field = form && form.querySelector('[aria-invalid="true"]');
      if (field) field.focus();
    }, 0);

  const submit = async () => {
    if (!command || !model) return;
    if (!valid) {
      setTried((old) => ({ ...old, [command]: true }));
      focusFirstProblem();
      return;
    }
    sequence.current += 1;
    const mine = sequence.current;
    if (running.current) running.current.abort();
    const controller = new AbortController();
    running.current = controller;
    const sent = options;
    setBusy(command);
    try {
      const envelope = await api.run(command, sent, { channel: SECTION, signal: controller.signal });
      if (mine !== sequence.current) return;
      setRuns((old) => ({ ...old, [command]: { command, options: sent, envelope, analysis: analyzeResult(envelope), key: JSON.stringify(sent) } }));
      setServerErrors((old) => ({ ...old, [command]: {} }));
      if (isPhone()) openPanel("right");
    } catch (error) {
      if (error && error.name === "AbortError") return;
      if (mine !== sequence.current) return;
      const doc2 = error && error.doc ? error.doc : { code: "internal_error", message: String(error) };
      const described = describeError(doc2);
      const field = described.option && model.fields.find((item) => item.name === described.option);
      const message = withReason(described.text, described.reason);
      setServerErrors((old) => ({
        ...old,
        [command]:
          field && isActive(model, field)
            ? { [described.option]: message }
            : { [FORM_ERROR]: { title: described.title, text: message } },
      }));
      focusFirstProblem();
    } finally {
      if (mine === sequence.current) {
        setBusy(null);
        running.current = null;
      }
    }
  };

  // „Wyczyść”: the first visit again: no command chosen (the route too), no form, no result
  const clear = () => {
    sequence.current += 1;
    if (running.current) running.current.abort();
    running.current = null;
    setBusy(null);
    reset();
    setRuns({});
    setServerErrors({});
    setTouched({});
    setTried({});
    navigate(SECTION, [], { replace: true });
  };

  // The badge: busy, an error of the server, the form's own problems, a stale result, ok
  let badge = null;
  const serverMessage = Object.values(fromServer)[0];
  if (busy === command && command) badge = status("busy");
  else if (serverMessage) badge = status("error", undefined, typeof serverMessage === "object" ? serverMessage.text : serverMessage);
  else if (visibleCount) badge = status("invalid", `${shell.status.invalid.text}: ${Object.keys(shownErrors)[0]}`);
  else if (run && run.envelope.status === "ok" && run.key !== JSON.stringify(options)) badge = status("stale");
  else if (run && run.envelope.status === "ok") badge = status("ok");
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);

  const groups = catalog.commands ? groupsOf(catalog.commands) : [];
  const counts = {
    commands: plural(names.length, texts.commandForms),
    groups: plural(groups.length, texts.groupForms),
  };
  const context = catalog.commands
    ? command
      ? t(texts.context, { command, ...counts })
      : t(texts.contextNone, counts)
    : null;
  useEffect(() => setContext(context), [context]);

  let formState = errorTexts.formOk;
  if (busy === command && command) formState = texts.running;
  else if (visibleCount) formState = t(errorTexts.count, { count: plural(visibleCount, errorTexts.countForms) });
  else if (!valid) formState = errorTexts.formIncomplete;

  const left = {
    sub: catalog.commands ? t(texts.catalog, { commands: counts.commands }) : null,
    body: html`
      <${CommandList}
        catalog=${catalog}
        group=${state.group}
        query=${state.query}
        current=${command}
        active=${active}
        onGroup=${(group) => setState((old) => ({ ...old, group }))}
        onQuery=${(query) => setState((old) => ({ ...old, query }))}
        onPick=${pick}
      />
      ${command && doc
        ? html`<${CommandForm}
            key=${command}
            command=${doc}
            values=${values}
            onChange=${onChange}
            errors=${shownErrors}
            formId=${FORM_ID}
            onSubmit=${submit}
          />`
        : command && catalog.commands
          ? html`<p class="muted" role="status">${texts.formLoading}</p>`
          : catalog.commands
            ? html`<${EmptyHint} text=${texts.pick} anchor="przyklad-polecenia" name="polecenia" />`
            : null}
    `,
    foot: html`
      <button class="btn primary" type="submit" form=${FORM_ID} disabled=${!model || visibleCount > 0 || busy === command}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" /></svg>
        ${common.actions.run}
      </button>
      <span class="muted small form-state" role="status">${model ? formState : ""}</span>
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${clear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };
  const center = {
    label: texts.tabs.table,
    bar: html`
      <${Seg}
        items=${[
          { value: "table", label: texts.tabs.table },
          { value: "json", label: texts.tabs.json },
        ]}
        value=${tab}
        onChange=${setTab}
        label=${texts.view}
      />
      <span class="hint">
        <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5" /><path d="M8 7.5v4M8 5v.01" /></svg>
        <span>${texts.hint}</span>
      </span>
    `,
    body: html`<div class=${`result-area${busy === command && command ? " computing" : ""}`} aria-busy=${busy === command ? "true" : "false"}>
      <${CenterBody} run=${run} tab=${tab} />
    </div>`,
  };
  const right = {
    sub: run ? run.command : null,
    body: html`<div class=${`result-area${busy === command && command ? " computing" : ""}`}>
      <${ResultsPanel} run=${run} chartSvg=${chartSvg} />
    </div>`,
  };
  return html`<${ViewLayout} left=${left} center=${center} right=${right} />`;
}
