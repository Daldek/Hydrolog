// „Statystyka przepływów”: the flood frequency analysis of annual maxima (`stats
// flood-frequency`, plan S5). The series is a file of the session, its columns read from the
// header, or pasted values; a first visit has neither (the guide, instrukcja/#statystyka,
// has a worked example). The form's fields are the catalog's. „Oblicz” runs the command,
// and a second run of the same series on a dense grid of return periods gives the curves
// of the probability plot. The result shows the active distribution (the best one after
// every computation, another one by a click on its row of the distributions table) in the
// tiles and on the plot, the quantiles of the distributions ticked in that table (the best
// one after every computation), the goodness of fit and the notices in Polish; neither
// choice is stored. „Do porównania” hands the active distribution's stressed quantile to
// Hydrogram zlewni (store "reference"). A change marks the result stale (plan D13).
// A station's series handed off by Archiwista (ADR-0020, „Wczytaj z Archiwisty”) arrives
// through useHandoffInbox as the source and values it opens with, and the data panel names
// where it came from until the series is changed.

import { api } from "../../api.js";
import { extent } from "../../charts/scale.js";
import { useSession } from "../../controls/file-field.js";
import { useHandoffInbox } from "../../handoff/handoff-panel.js";
import { inputText, num, plural } from "../../format.js";
import { FORM_ERROR } from "../../forms/command-form.js";
import { fieldModel, isActive, toOptions, validate, withReason } from "../../forms/model.js";
import { html, useEffect, useMemo, useRef, useState } from "../../html.js";
import { common, t } from "../../labels/common.js";
import { describeError, errors as errorTexts } from "../../labels/errors.js";
import { statsInfo } from "../../labels/info/stats.js";
import { shell } from "../../labels/shell.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { usePersistentState } from "../../persist.js";
import { useStore } from "../../store.js";
import { registerInfo, registerServed } from "../../ui/info.js";
import { Seg } from "../../ui/seg.js";
import { isPhone, openPanel } from "../../ui/sheet.js";
import { status } from "../../ui/status.js";
import { toast } from "../../ui/toast.js";
import { ViewLayout } from "../../ui/view-layout.js";
import { DataPanel } from "./data-panel.js";
import { exportSpec } from "./export.js";
import { CenterBody, distributionName, ResultsPanel } from "./results-panel.js";
import {
  columnOption,
  COMMAND,
  CURVE_PERIODS,
  CURVES_CHANNEL,
  formValues,
  guessDateColumn,
  guessValueColumn,
  initialState,
  maximaYears,
  percentAt,
  periodsOf,
  quantileAt,
  rankedMaxima,
  resolveColumn,
  SECTION,
  shortNumber,
  stressedPeriod,
  useCommandDoc,
  useFileTable,
} from "./state.js";

registerInfo(statsInfo);

const FORM_ID = "st-form";
const CLOCK = new Intl.DateTimeFormat("pl-PL", { hour: "2-digit", minute: "2-digit" });

/**
 * The key of a run's inputs: its options and the content of its file.
 *
 * @param {object|null} options the options
 * @param {object|null} file the session's entry of the input file
 * @returns {string} the key
 */
function runKey(options, file) {
  return JSON.stringify([options, file ? file.sha256 : null]);
}

/**
 * The message of a failed request, in Polish.
 *
 * @param {unknown} error the error
 * @returns {string} the message
 */
function messageOf(error) {
  if (error && error.doc) return describeError(error.doc).text;
  return String((error && error.message) || error);
}

/**
 * The section „Statystyka przepływów”.
 *
 * @returns {object} the section
 */
export default function Statystyka() {
  const { doc, error: docError } = useCommandDoc(COMMAND);
  const session = useSession();
  const [state, setState, reset] = usePersistentState(SECTION, initialState);
  // A hand-off: its series replaces the section's, the distributions and periods stay.
  useHandoffInbox(SECTION, ({ source, values: given, received }) => {
    setTouched({});
    setServerErrors({});
    setRun(null);
    setState((old) => ({ ...old, source, values: { ...old.values, ...given }, received }));
  });
  const [, setStatus] = useStore("status");
  const [, setContext] = useStore("context");
  const [reference, setReference] = useStore("reference");
  const [tab, setTab] = useState("chart");
  const [touched, setTouched] = useState({});
  const [tried, setTried] = useState(false);
  const [run, setRun] = useState(null);
  const [serverErrors, setServerErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const sequence = useRef(0);
  const running = useRef(null);
  const chartSvg = useRef(null);
  // The distributions ticked „W tabeli kwantyli” and the active one (null: the best) for
  // one run; another run starts again
  const [picked, setPicked] = useState({ run: null, names: [], active: null });

  const base = useMemo(() => (doc ? fieldModel(doc) : null), [doc]);
  // Hydrolog's range of the record's length, checked by the explanation of the analysis
  useEffect(() => {
    if (doc) registerServed(doc, (range) => (range.method === "flood_frequency" ? "stats-flood-frequency" : null));
  }, [doc]);
  const values = useMemo(() => formValues(state, base), [state, base]);
  const model = useMemo(() => (doc ? fieldModel(doc, { values }) : null), [doc, values]);
  const problems = useMemo(() => (model ? validate(model, values) : {}), [model, values]);
  const valid = Boolean(model) && !Object.keys(problems).length;
  const options = useMemo(() => (valid ? toOptions(model, values) : null), [valid, model, values]);

  const files = (session && session.files) || [];
  const path = state.source === "file" ? state.values.input_file || "" : "";
  const file = files.find((item) => item.path === path) || null;
  const preview = useFileTable(file ? path : null, file ? file.sha256 : null);

  // A first visit: the catalog's default return periods
  useEffect(() => {
    if (!base || state.values.return_periods !== undefined) return;
    const field = base.fields.find((item) => item.name === "return_periods");
    if (!field || !Array.isArray(field.default)) return;
    const text = field.default.map(inputText).join("; ");
    setState((old) => (old.values.return_periods !== undefined ? old : { ...old, values: { ...old.values, return_periods: text } }));
  }, [base, state.values.return_periods]);

  // The columns of a new file: the last column of numbers, a column of dates
  useEffect(() => {
    if (preview.state !== "ok") return;
    const { columns } = preview.table;
    setState((old) => {
      const next = { ...old.values };
      let changed = false;
      if (!next.value_column || !resolveColumn(next.value_column, columns)) {
        const guess = guessValueColumn(preview.table);
        if (guess && columnOption(guess, columns) !== next.value_column) {
          next.value_column = columnOption(guess, columns);
          changed = true;
        }
      }
      if (next.date_column === undefined) {
        const guess = guessDateColumn(preview.table);
        next.date_column = guess ? columnOption(guess, columns) : "";
        changed = true;
      }
      return changed ? { ...old, values: next } : old;
    });
  }, [preview]);

  const forget = (names) => {
    if (!Object.keys(serverErrors).length) return;
    const left = { ...serverErrors };
    for (const name of [...names, FORM_ERROR]) delete left[name];
    setServerErrors(left);
  };

  const onValue = (name, value) => {
    setTouched((old) => ({ ...old, [name]: true }));
    forget([name]);
    setState((old) => {
      const next = { ...old.values, [name]: value };
      if (name === "input_file" && value !== old.values.input_file) {
        next.value_column = undefined;
        next.date_column = undefined;
      }
      const series = name === "input_file" || name === "values";
      return { ...old, values: next, received: series ? null : old.received };
    });
  };

  const onSource = (source) => {
    forget(["input_file", "value_column", "date_column", "values"]);
    setState((old) => ({ ...old, source, received: null }));
  };

  const focusFirstProblem = () =>
    setTimeout(() => {
      const form = document.getElementById(FORM_ID);
      const field = form && form.querySelector('[aria-invalid="true"]');
      if (field) field.focus();
    }, 0);

  const submit = async () => {
    if (!model) return;
    if (!valid) {
      setTried(true);
      focusFirstProblem();
      return;
    }
    sequence.current += 1;
    const mine = sequence.current;
    if (running.current) running.current.abort();
    const controller = new AbortController();
    running.current = controller;
    const sent = options;
    const key = runKey(sent, file);
    const table = preview.state === "ok" ? preview.table : null;
    setBusy(true);
    try {
      const curves = api
        .run(COMMAND, { ...sent, return_periods: [...CURVE_PERIODS] }, { channel: CURVES_CHANNEL, signal: controller.signal })
        .then((envelope) => (envelope.status === "ok" ? { result: envelope.result } : { error: texts.results.cancelled }))
        .catch((error) => {
          if (error && error.name === "AbortError") throw error;
          return { error: messageOf(error) };
        });
      const [envelope, drawn] = await Promise.all([api.run(COMMAND, sent, { channel: SECTION, signal: controller.signal }), curves]);
      if (mine !== sequence.current) return;
      const result = envelope.status === "ok" ? envelope.result : null;
      const column = table && sent.value_column ? resolveColumn(sent.value_column, table.columns) : null;
      const years = result ? maximaYears(result, table, column) : null;
      setRun({
        options: sent,
        envelope,
        key,
        at: new Date(),
        curves: drawn.result || null,
        curvesError: result && !drawn.result ? drawn.error : null,
        years,
        ranked: result ? rankedMaxima(result, years) : [],
      });
      setServerErrors({});
      if (isPhone()) openPanel("right");
    } catch (error) {
      if (error && error.name === "AbortError") return;
      if (mine !== sequence.current) return;
      const described = describeError(error && error.doc ? error.doc : { code: "internal_error", message: messageOf(error) });
      const field = described.option && model.fields.find((item) => item.name === described.option);
      const message = withReason(described.text, described.reason);
      setServerErrors(
        field && isActive(model, field) ? { [described.option]: message } : { [FORM_ERROR]: { title: described.title, text: message } },
      );
      focusFirstProblem();
    } finally {
      if (mine === sequence.current) {
        setBusy(false);
        running.current = null;
      }
    }
  };

  const clear = () => {
    if (running.current) running.current.abort();
    sequence.current += 1;
    reset();
    setRun(null);
    setBusy(false);
    setServerErrors({});
    setTouched({});
    setTried(false);
  };

  // Messages: the server's, and the form's own once a field was touched or a run asked for
  const shownErrors = { ...serverErrors };
  for (const [name, message] of Object.entries(problems)) {
    if (!message.endsWith(" · required") || tried || touched[name]) shownErrors[name] = message;
  }
  const visibleCount = Object.keys(shownErrors).length;

  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  // The choices of this run: the ticked distributions and the active one, else the best
  const own = picked.run === run;
  const ticked = result ? (own ? picked.names : [result.best_distribution]) : [];
  const active = result ? (own && picked.active ? picked.active : result.best_distribution) : null;
  const onTick = (name, on) => setPicked({ run, names: on ? [...ticked, name] : ticked.filter((item) => item !== name), active });
  const onActive = (name) => setPicked({ run, names: ticked, active: name });
  const fit = result ? result.distributions.find((item) => item.distribution_name === active) || null : null;
  const runPeriods = fit ? fit.return_periods : [];
  const runStressed = stressedPeriod(runPeriods, state.chosen);
  const periods = periodsOf(state.values.return_periods);
  const stressed = stressedPeriod(periods, state.chosen);
  const runFile = run ? (typeof run.options.input_file === "string" ? run.options.input_file.replace(/^in\//, "") : texts.pasted) : null;

  // The badge: busy, an error of the server, the form's own problems, a stale result, ok
  let badge = null;
  const serverMessage = Object.values(serverErrors)[0];
  if (busy) badge = status("busy");
  else if (serverMessage) badge = status("error", undefined, typeof serverMessage === "object" ? serverMessage.text : serverMessage);
  else if (visibleCount) badge = status("invalid", `${shell.status.invalid.text}: ${Object.keys(shownErrors)[0]}`);
  else if (result && run.key !== runKey(options, file)) badge = status("stale");
  else if (result) badge = status("ok");
  const badgeKey = JSON.stringify(badge);
  useEffect(() => setStatus(badge), [badgeKey]);

  // The breadcrumbs: the series and its years
  let context = null;
  if (result) {
    const years = plural(result.n_years, texts.yearForms);
    const known = run.years && run.years.length ? extent(run.years) : null;
    context = known
      ? t(texts.contextRange, { file: runFile, years, first: known[0], last: known[1] })
      : t(texts.context, { file: runFile, years });
  } else if (state.source === "file" && path) {
    const name = path.replace(/^in\//, "");
    context = preview.state === "ok" ? t(texts.context, { file: name, years: plural(preview.table.rows, texts.rowForms) }) : name;
  } else if (state.source === "paste") {
    context = texts.pasted;
  }
  useEffect(() => setContext(context), [context]);

  // „Do porównania”: the stressed quantile of the active distribution
  const q = fit && runStressed !== null ? quantileAt(fit, runStressed) : null;
  const p = fit && runStressed !== null ? percentAt(fit, runStressed) : null;
  let referenceState = null;
  if (q !== null && p !== null) {
    const label = t(texts.results.referenceLabel, { p: shortNumber(p), name: distributionName(fit.distribution_name) });
    const pressed = Boolean(reference && reference.peak_m3s === q && reference.label === label);
    referenceState = {
      pressed,
      toggle: () => {
        if (pressed) {
          setReference(null);
          toast(texts.results.referenceCleared);
        } else {
          setReference({ label, peak_m3s: q, source: t(texts.results.referenceSource, { file: runFile }) });
          toast(t(texts.results.referenceSet, { p: shortNumber(p), q: num(q, 1) }));
        }
      },
    };
  }

  const spec = result
    ? exportSpec({ options: run.options, envelope: run.envelope, ticked, chartSvg: tab === "chart" ? chartSvg : null, pasted: texts.pasted })
    : null;

  const footState = busy
    ? texts.computing
    : visibleCount
      ? t(errorTexts.count, { count: plural(visibleCount, errorTexts.countForms) })
      : run
        ? t(texts.lastRun, { time: CLOCK.format(run.at) })
        : "";

  let leftBody;
  if (docError) leftBody = html`<p class="err" role="alert">${docError}</p>`;
  else if (!model) leftBody = html`<p class="muted" role="status">${common.loading}</p>`;
  else {
    leftBody = html`<${DataPanel}
      model=${model}
      values=${values}
      source=${state.source}
      received=${state.received || null}
      errors=${shownErrors}
      onValue=${onValue}
      onSource=${onSource}
      session=${session}
      preview=${preview}
      periods=${periods}
      stressed=${stressed}
      onChosen=${(period) => setState((old) => ({ ...old, chosen: period }))}
      seriesMeta=${result && run.key === runKey(options, file) ? plural(result.n_years, texts.yearForms) : null}
      formId=${FORM_ID}
      onSubmit=${submit}
    />`;
  }

  const left = {
    sub: COMMAND,
    body: leftBody,
    foot: html`
      <button class="btn primary" type="submit" form=${FORM_ID} disabled=${!model || visibleCount > 0 || busy}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4l10 6-10 6z" /></svg>
        ${texts.compute}
      </button>
      <span class="muted small form-state" role="status">${footState}</span>
      <button class="btn ghost sm icon foot-end" type="button" aria-label=${common.actions.clear} title=${texts.clearTitle} onClick=${clear}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10a6 6 0 1 0 1.8-4.3M4 4v3.5h3.5" /></svg>
      </button>
    `,
  };
  const center = {
    label: texts.tabs[tab],
    bar: html`
      <${Seg}
        items=${[
          { value: "chart", label: texts.tabs.chart },
          { value: "series", label: texts.tabs.series },
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
    body: html`<div class=${`result-area${busy ? " computing" : ""}`} aria-busy=${busy ? "true" : "false"}>
      <${CenterBody} run=${run} tab=${tab} stressed=${runStressed} active=${active} chartSvg=${chartSvg} />
    </div>`,
  };
  const right = {
    sub: result ? t(texts.results.sub, { name: distributionName(result.best_distribution) }) : null,
    body: html`<div class=${`result-area${busy ? " computing" : ""}`}>
      <${ResultsPanel}
        run=${run}
        periods=${runPeriods}
        stressed=${runStressed}
        ticked=${ticked}
        onTick=${onTick}
        active=${active}
        onActive=${onActive}
        spec=${spec}
        reference=${referenceState}
      />
    </div>`,
  };
  return html`<${ViewLayout} left=${left} center=${center} right=${right} />`;
}
