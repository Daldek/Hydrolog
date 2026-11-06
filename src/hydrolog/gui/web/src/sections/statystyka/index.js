// „Statystyka przepływów”: the flood frequency analysis of annual maxima (`stats
// flood-frequency`, plan S5). The series is a file of the session, its columns read from the
// header, or pasted values; a first visit has neither (the guide, instrukcja/#statystyka,
// has a worked example). The form's fields are the catalog's. „Oblicz” runs the command with
// every distribution by every fit method, and a second run of the same series on a dense
// grid of return periods gives the curves of the probability plot, the density and the
// distribution function; a third, `stats homogeneity` of the same series (with the year
// column of a file of annual maxima), gives the panel „Jednorodność ciągu” and its notice.
// „Rozkłady” and „Metody estymacji” choose the combinations shown without a new run (plan
// 2026-11-06, D7). The result shows the active combination (the best one shown, the lowest
// AIC, until a click on another's row of the distributions table) in the tiles and on the
// charts, the quantiles of the combinations ticked in that table (the best one until the
// person ticks or unticks a row; any, none included), the goodness of fit and the notices in
// Polish (a notice naming a combination only while it is shown); neither choice is stored,
// and an active one no longer shown gives way to the best one. „Do porównania” hands the
// active combination's stressed quantile to Hydrogram zlewni (store "reference"); it is off
// while „Wyróżniony w wynikach” is „brak” (the first visit). A change of the inputs marks the
// result stale (plan D13). „Zakres osi” under each chart sets its axis ranges without a new
// run, stored with the inputs; „Auto” restores the ranges of the result (plan 2026-11-06, D8).
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
import { CenterBody, fitName, ResultsPanel } from "./results-panel.js";
import {
  bestFit,
  columnOption,
  COMMAND,
  CURVE_PERIODS,
  CURVES_CHANNEL,
  DISTRIBUTIONS,
  FIT_METHODS,
  fitKey,
  formValues,
  guessDateColumn,
  guessValueColumn,
  HOMOGENEITY,
  HOMOGENEITY_CHANNEL,
  homogeneityOptions,
  initialState,
  maximaYears,
  percentAt,
  periodsOf,
  quantileAt,
  rankedMaxima,
  resolveColumn,
  SECTION,
  shortNumber,
  shownFits,
  stressedPeriod,
  toggled,
  useCommandDoc,
  useFileTable,
} from "./state.js";

registerInfo(statsInfo);

const FORM_ID = "st-form";
const CLOCK = new Intl.DateTimeFormat("pl-PL", { hour: "2-digit", minute: "2-digit" });
/** The axis limits of a store from before „Zakres osi”: every axis automatic. */
const NO_AXES = Object.freeze({});

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
  // The combinations ticked „W tabeli kwantyli” (null: the best one) and the active one
  // (null: the best) of one run, as keys (fitKey); another run starts again
  const [picked, setPicked] = useState({ run: null, names: null, active: null });

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

  // „Rozkłady” and „Metody estymacji”: what the run shows, not what it computes
  const onShown = (filter, value, on) =>
    setState((old) => {
      const order = filter === "methods" ? FIT_METHODS : DISTRIBUTIONS;
      return { ...old, shown: { ...old.shown, [filter]: toggled(order, old.shown[filter], value, on) } };
    });

  // „Zakres osi”: a limit typed for an axis of a chart, or „Auto” (axis null) for the chart
  const onAxis = (chart, axis, end, text) =>
    setState((old) => {
      const axes = { ...(old.axes || {}) };
      if (axis === null) delete axes[chart];
      else axes[chart] = { ...axes[chart], [axis]: { ...axes[chart]?.[axis], [end]: text } };
      return { ...old, axes };
    });

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
    // The curves and the homogeneity tests are not the result: their failure leaves it shown
    const beside = (promise) =>
      promise
        .then((envelope) => (envelope.status === "ok" ? { envelope } : { error: texts.results.cancelled }))
        .catch((error) => {
          if (error && error.name === "AbortError") throw error;
          return { error: messageOf(error) };
        });
    try {
      const curves = beside(
        api.run(COMMAND, { ...sent, return_periods: [...CURVE_PERIODS] }, { channel: CURVES_CHANNEL, signal: controller.signal }),
      );
      const tested = beside(api.run(HOMOGENEITY, homogeneityOptions(sent, table), { channel: HOMOGENEITY_CHANNEL, signal: controller.signal }));
      const [envelope, drawn, homogeneity] = await Promise.all([api.run(COMMAND, sent, { channel: SECTION, signal: controller.signal }), curves, tested]);
      if (mine !== sequence.current) return;
      const result = envelope.status === "ok" ? envelope.result : null;
      const column = table && sent.value_column ? resolveColumn(sent.value_column, table.columns) : null;
      const years = result ? maximaYears(result, table, column) : null;
      setRun({
        options: sent,
        envelope,
        key,
        at: new Date(),
        curves: drawn.envelope ? drawn.envelope.result : null,
        curvesError: result && !drawn.envelope ? drawn.error : null,
        homogeneity: homogeneity.envelope || null,
        homogeneityError: result && !homogeneity.envelope ? homogeneity.error : null,
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
  // The combinations shown and the best of them (the lowest AIC)
  const visible = useMemo(() => (result ? shownFits(result.distributions, state.shown) : []), [result, state.shown]);
  const best = bestFit(visible);
  const bestKey = best ? fitKey(best) : null;
  // The choices of this run: the ticked combinations (the best one until the person ticks or
  // unticks one, then any, none included; those shown count) and the active one, else the
  // best
  const own = picked.run === run;
  const keys = visible.map(fitKey);
  const wanted = own && picked.names !== null ? picked.names : bestKey ? [bestKey] : [];
  const ticked = wanted.filter((key) => keys.includes(key));
  const active = own && picked.active && keys.includes(picked.active) ? picked.active : bestKey;
  const onTick = (key, on) =>
    setPicked({ run, names: on ? [...wanted, key] : wanted.filter((item) => item !== key), active: own ? picked.active : null });
  const onActive = (key) => setPicked({ run, names: own ? picked.names : null, active: key });
  const fit = visible.find((item) => fitKey(item) === active) || null;
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

  // „Do porównania”: the stressed quantile of the active distribution; off for „brak”
  const q = fit && runStressed !== null ? quantileAt(fit, runStressed) : null;
  const p = fit && runStressed !== null ? percentAt(fit, runStressed) : null;
  let referenceState = null;
  if (q !== null && p !== null) {
    const label = t(texts.results.referenceLabel, { p: shortNumber(p), name: fitName(fit) });
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
  } else if (fit && runStressed === null) {
    referenceState = { pressed: false, toggle: null };
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
      shown=${state.shown}
      onShown=${onShown}
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
      <${CenterBody}
        run=${run}
        tab=${tab}
        shown=${state.shown}
        stressed=${runStressed}
        active=${active}
        chartSvg=${chartSvg}
        axes=${state.axes || NO_AXES}
        onAxis=${onAxis}
      />
    </div>`,
  };
  const right = {
    sub: best ? t(texts.results.sub, { name: fitName(best) }) : null,
    body: html`<div class=${`result-area${busy ? " computing" : ""}`}>
      <${ResultsPanel}
        run=${run}
        shown=${state.shown}
        fits=${visible}
        best=${bestKey}
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
