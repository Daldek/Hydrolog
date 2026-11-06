// The results of „Statystyka przepływów”: in the centre the probability plot with the density
// and distribution-function charts, and the ranked annual maxima, in the panel Wyniki the
// tiles of the active combination of distribution and fit method, the notices in Polish (with
// those of the homogeneity tests; one naming a combination only while it is shown), the
// combinations shown with their goodness of fit (a click on a row makes its combination the
// active one), the quantiles of the combinations ticked in their table, the homogeneity of the
// series (`stats homogeneity`: three tests, the split and Pettitt's change point) and the
// exports (CSV of those quantiles, the envelope as JSON, the probability plot as PNG, „Do
// porównania” and the call).

import { Chart } from "../../charts/chart.js";
import { auto, num, plural } from "../../format.js";
import { Notices } from "../../forms/result-view.js";
import { html, useMemo } from "../../html.js";
import { t } from "../../labels/common.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { CommandLine, ExportButtons } from "../../ui/export-panel.js";
import { InfoButton } from "../../ui/info-button.js";
import { DataTable } from "../../ui/table.js";
import { AxisRange } from "./axis-range.js";
import { axisRanges, curveClass, densitySpec, distributionSpec, methodName, namesMethods, probabilitySpec } from "./charts.js";
import {
  AXES,
  axisLimits,
  COMMAND,
  FIT_METHODS,
  fitKey,
  percentAt,
  quantileAt,
  secondPeriod,
  shortNumber,
  shownFits,
  shownNotices,
  tickedFits,
} from "./state.js";
import { Stroke } from "./swatch.js";

/** Lists in Polish: „L-momentów i największej wiarygodności”. */
const AND = new Intl.ListFormat("pl-PL", { type: "conjunction" });

/**
 * The name of a distribution in the tables.
 *
 * @param {string} name the distribution's name in the result
 * @returns {string} the Polish name
 */
export function distributionName(name) {
  return Object.hasOwn(texts.distributions, name) ? texts.distributions[name].name : name;
}

/**
 * The name of a combination of a distribution and a fit method in the results and the
 * comparison: „log-normalny, L-momenty”.
 *
 * @param {object} fit a fitted distribution of the result
 * @returns {string} the name
 */
export function fitName(fit) {
  return t(texts.combination, { name: distributionName(fit.distribution_name), method: methodName(fit.fit_method) });
}

/**
 * The name of a combination in a table: its distribution, and its method too when the table
 * holds more than one („GEV, L-momenty”), so that the names tell the rows apart.
 *
 * @param {object} fit a fitted distribution of the result
 * @param {boolean} named whether the method is named
 * @returns {string} the name
 */
function rowName(fit, named) {
  return named ? fitName(fit) : distributionName(fit.distribution_name);
}

/**
 * A fit method after „metodą” or „metodami”: „największej wiarygodności”.
 *
 * @param {string} method the method's name in the result
 * @returns {string} the Polish words
 */
function methodBy(method) {
  return Object.hasOwn(texts.fitMethods, method) ? texts.fitMethods[method].by : method;
}

/**
 * The critical value of A² at the 5% level of a fit.
 *
 * @param {object} fit a fitted distribution
 * @returns {number|null} the value
 */
function adCritical(fit) {
  const values = fit.ad_critical_values || {};
  return typeof values["5%"] === "number" ? values["5%"] : null;
}

/**
 * The label of a quantile: „Q 1%”.
 *
 * @param {object} fit a fitted distribution
 * @param {number} period the return period
 * @returns {string} the label
 */
function quantileLabel(fit, period) {
  return t(texts.results.q, { p: shortNumber(percentAt(fit, period)) });
}

/**
 * The subtitle of the probability plot: the maxima and the distributions shown with their
 * fit methods.
 *
 * @param {object} result the result of the run
 * @param {object[]} fits the combinations shown
 * @returns {string} the subtitle
 */
function chartSub(result, fits) {
  const count = plural(result.n_years, texts.chart.maximaForms);
  if (!fits.length) return t(texts.chart.noFits, { count });
  const names = new Set(fits.map((fit) => fit.distribution_name));
  const methods = FIT_METHODS.filter((method) => fits.some((fit) => fit.fit_method === method));
  const by = methods.length === 1
    ? t(texts.chart.byMethod, { method: methodBy(methods[0]) })
    : t(texts.chart.byMethods, { methods: AND.format(methods.map(methodBy)) });
  return t(texts.chart.sub, { count, fits: plural(names.size, texts.chart.fitForms), by });
}

/**
 * The centre: the probability plot with the density and distribution-function charts, each
 * with its „Zakres osi”, or the table of the ranked annual maxima.
 *
 * @param {{run: object|null, tab: "chart"|"series", shown: {distributions: string[],
 *   methods: string[]}, stressed: number|null, active: string|null, chartSvg: object,
 *   axes: object, onAxis: (chart: string, axis: string|null, end?: string, text?: string) =>
 *   void}} props the last run, the tab shown, the combinations shown, the stressed return
 *   period, the key of the active combination, the ref of the chart's SVG (for PNG), the
 *   axis limits typed by chart and axis, and their change handler (`axis` null: „Auto”)
 * @returns {object} the centre's body
 */
export function CenterBody({ run, tab, shown, stressed, active, chartSvg, axes, onAxis }) {
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const curves = run && run.curves;
  // The automatic ranges of the run, then the person's limits on them
  const auto = useMemo(() => (result ? axisRanges(result, curves) : null), [result, curves]);
  const limits = useMemo(() => {
    if (!auto) return null;
    const out = {};
    for (const [chart, names] of Object.entries(AXES)) {
      out[chart] = {};
      for (const axis of names) out[chart][axis] = axisLimits(axes[chart]?.[axis], auto[chart][axis], axis);
    }
    return out;
  }, [auto, axes]);
  const ranges = useMemo(() => {
    if (!limits) return null;
    const out = {};
    for (const [chart, byAxis] of Object.entries(limits)) {
      out[chart] = Object.fromEntries(Object.entries(byAxis).map(([axis, limit]) => [axis, limit.range]));
    }
    return out;
  }, [limits]);
  const spec = useMemo(
    () => (result ? probabilitySpec({ result, curves, shown, chosen: stressed, active, ranges }) : null),
    [result, curves, shown, stressed, active, ranges],
  );
  const shapes = useMemo(
    () =>
      result
        ? {
            density: densitySpec({ result, curves, shown, active, ranges }),
            distribution: distributionSpec({ result, curves, shown, active, ranges }),
          }
        : null,
    [result, curves, shown, active, ranges],
  );
  const control = (chart) => html`<${AxisRange} chart=${chart} typed=${axes[chart]} auto=${auto[chart]} limits=${limits[chart]} onAxis=${onAxis} />`;
  if (!run) return html`<p class="empty-note">${texts.noResult}</p>`;
  if (!result) return html`<p class="empty-note">${texts.results.cancelled}</p>`;
  if (tab === "series") {
    const columns = [{ key: "rank", label: texts.series.rank, format: (value) => String(value) }];
    if (run.ranked.some((row) => row.year !== null)) {
      columns.push({ key: "year", label: texts.series.year, className: "t", format: (value) => (value === null ? "–" : String(value)) });
    }
    columns.push(
      { key: "value", label: texts.series.value, unit: "m³/s", format: (value) => num(value, 1) },
      { key: "p", label: texts.series.p, unit: "%", format: (value) => num(value * 100, 1) },
    );
    return html`
      <div class="card st-maxima">
        <div class="card-head">
          <h3 class="card-title">${texts.series.title}</h3>
          <span class="card-sub">${texts.series.sub}</span>
        </div>
        <${DataTable} columns=${columns} rows=${run.ranked} label=${texts.series.title} />
      </div>
    `;
  }
  return html`
    <div class="card st-chart">
      <div class="card-head">
        <h3 class="card-title" id="st-chart-title">${texts.chart.title} <${InfoButton} id="stats-plot" /></h3>
        <span class="card-sub">${chartSub(result, shownFits(result.distributions, shown))}</span>
      </div>
      <${Chart} spec=${spec} svgRef=${chartSvg} />
      ${run.curvesError ? html`<p class="note">${t(texts.chart.curvesFailed, { message: run.curvesError })}</p>` : null}
      ${control("probability")}
    </div>
    <div class="card st-shape">
      <div class="card-head">
        <h3 class="card-title">${texts.shape.title}</h3>
        <span class="card-sub">${texts.shape.sub}</span>
      </div>
      <div class="chart-box" data-chart="density">
        <div class="chart-title">${texts.shape.density}</div>
        <${Chart} spec=${shapes.density} />
        ${control("density")}
      </div>
      <div class="chart-box" data-chart="distribution">
        <div class="chart-title">${texts.shape.distribution}</div>
        <${Chart} spec=${shapes.distribution} />
        ${control("distribution")}
      </div>
    </div>
  `;
}

/**
 * The tiles: the active combination („najlepszy” when it is the best shown; its method
 * below the distribution), its stressed quantile (none for „brak”) and another one, the
 * length.
 *
 * @param {{result: object, fit: object|null, best: string|null, stressed: number|null,
 *   second: number|null}} props the result, the active combination (null when none is
 *   shown), the key of the best one and the two return periods
 * @returns {object} the tiles
 */
function Tiles({ result, fit, best, stressed, second }) {
  const tile = (key, label, value, unit, hi = false, sub = null) => html`
    <div class=${`kpi${hi ? " hi" : ""}`} data-key=${key}>
      <div class="k">${label}</div>
      <div class="v">${value}${unit ? html` <span class="u">${unit}</span>` : null}</div>
      ${sub ? html`<div class="sub">${sub}</div>` : null}
    </div>
  `;
  const quantile = (period, hi) => {
    const q = quantileAt(fit, period);
    return q === null ? null : tile(`q-${period}`, quantileLabel(fit, period), num(q, 1), "m³/s", hi);
  };
  const [count, ...word] = plural(result.n_years, texts.yearForms).split(" ");
  const label = fit && fitKey(fit) === best ? texts.results.bestDistribution : texts.results.distribution;
  return html`
    <div class="summary">
      ${fit ? tile("distribution", label, distributionName(fit.distribution_name), null, false, methodName(fit.fit_method)) : null}
      ${fit && stressed !== null ? quantile(stressed, true) : null}
      ${fit && second !== null ? quantile(second, false) : null}
      ${tile("n_years", texts.results.length, count, word.join(" "))}
    </div>
  `;
}

/**
 * The combinations shown: the method, the box „W tabeli kwantyli” (any row can leave the
 * quantile table, the best one too), AIC, A² against its critical value, the p-value of KS
 * and two quantiles; the best first, as Hydrolog sorts them. A click on a row makes its
 * combination the active one.
 *
 * @param {{fits: object[], best: string|null, stressed: number|null, second: number|null,
 *   ticked: string[], onTick: (key: string, on: boolean) => void, active: string|null,
 *   onActive: (key: string) => void}} props the combinations shown, the key of the best
 *   one, the two return periods, the keys of the combinations in the quantile table and the
 *   change of one of them, the key of the active combination and its change
 * @returns {object} the table and its note
 */
function Distributions({ fits, best, stressed, second, ticked, onTick, active, onActive }) {
  const critical = adCritical(fits[0]);
  const named = namesMethods(fits);
  const columns = [
    {
      key: "distribution_name",
      label: texts.results.distribution,
      format: (name, fit) => html`<${Stroke} cls=${curveClass(fit)} />${distributionName(name)}${fitKey(fit) === best
        ? html` <span class="badge ok">${texts.results.best}</span>`
        : null}`,
    },
    { key: "fit_method", label: texts.results.method, className: "txt", format: (method) => methodName(method) },
    // Beside the combination, in sight in a narrow panel
    {
      key: "distribution_name",
      label: html`<span class="wrap">${texts.results.inQuantiles}</span>`,
      className: "pick",
      format: (_, fit) => {
        const key = fitKey(fit);
        return html`<input
          type="checkbox"
          checked=${ticked.includes(key)}
          aria-label=${t(texts.results.inQuantilesOf, { name: rowName(fit, named) })}
          onChange=${(event) => onTick(key, event.currentTarget.checked)}
        />`;
      },
    },
    { key: "aic", label: texts.results.aic, format: (value) => (typeof value === "number" ? num(value, 1) : "—") },
    {
      key: "ad_statistic",
      label: html`${texts.results.ad}${critical !== null ? html` <span class="u">${t(texts.results.adCritical, { value: num(critical, 2) })}</span>` : null}`,
      format: (value, fit) => {
        const limit = adCritical(fit);
        if (typeof value !== "number") return "—";
        if (limit === null) return num(value, 2);
        const ok = value < limit;
        return html`${num(value, 2)} <span class=${ok ? "ok-mark" : "bad-mark"} title=${ok ? texts.results.adOk : texts.results.adBad}>${ok ? "✓" : "✗"}</span>`;
      },
    },
    { key: "ks_p_value", label: texts.results.ks, format: (value) => (typeof value === "number" ? num(value, 2) : "—") },
  ];
  for (const period of [stressed, second]) {
    if (period === null) continue;
    columns.push({
      key: `q-${period}`,
      label: quantileLabel(fits[0], period),
      format: (_, fit) => {
        const q = quantileAt(fit, period);
        return q === null ? "—" : num(q, 1);
      },
    });
  }
  const issues = [];
  for (const fit of fits) {
    const found = [];
    if (typeof fit.aic !== "number") found.push(texts.results.noAic);
    const limit = adCritical(fit);
    if (typeof fit.ad_statistic === "number" && limit !== null && fit.ad_statistic >= limit) found.push(texts.results.adAbove);
    if (found.length) issues.push(t(texts.results.issues, { name: rowName(fit, named), issues: found.join(", ") }));
  }
  return html`
    <${DataTable}
      columns=${columns}
      rows=${fits}
      label=${texts.results.distributions}
      tall=${false}
      rowClass=${(fit) => (fitKey(fit) === active ? "sel" : null)}
      onRow=${(fit) => onActive(fitKey(fit))}
      currentRow=${(fit) => fitKey(fit) === active}
    />
    <p class="note">${[...issues, texts.results.unit, texts.results.activeHint].join(" ")}</p>
  `;
}

/**
 * The quantiles of the ticked combinations, one column each, the stressed period marked
 * (none for „brak”).
 *
 * @param {{fits: object[], named: boolean, stressed: number|null}} props the ticked fits, in
 *   the order of the distributions table, whether their names hold the method and the
 *   stressed period
 * @returns {object} the table
 */
function Quantiles({ fits, named, stressed }) {
  const [first] = fits;
  const rows = first.return_periods.map((period, index) => {
    const row = { period, p: first.exceedance_probabilities[index] * 100 };
    for (const fit of fits) row[fitKey(fit)] = fit.quantiles[index];
    return row;
  });
  return html`<${DataTable}
    columns=${[
      { key: "period", label: texts.results.period, unit: texts.results.periodUnit, format: (value) => shortNumber(value, 6) },
      { key: "p", label: texts.results.probability, unit: "%", format: (value) => shortNumber(value) },
      ...fits.map((fit) => ({
        key: fitKey(fit),
        // A long name wraps, its unit with it: the table stays within the panel
        label: html`<span class="wrap">${t(texts.results.quantileOf, { name: rowName(fit, named) })} <span class="u">[m³/s]</span></span>`,
        format: (value) => num(value, 1),
      })),
    ]}
    rows=${rows}
    label=${quantilesTitle(fits, named)}
    tall=${false}
    rowClass=${(row) => (row.period === stressed ? "hl" : null)}
  />`;
}

/**
 * The title of the quantile table: „Kwantyle: GEV, Weibull”, or with the methods named
 * „Kwantyle: GEV, L-momenty; GEV, największa wiarygodność”.
 *
 * @param {object[]} fits the ticked fits
 * @param {boolean} named whether their names hold the method
 * @returns {string} the title
 */
function quantilesTitle(fits, named) {
  return t(texts.results.quantiles, { name: fits.map((fit) => rowName(fit, named)).join(named ? "; " : ", ") });
}

/** The homogeneity tests in the order of the panel, as keys of the result. */
const TESTS = ["mann_whitney", "kolmogorov_smirnov", "pettitt"];

/**
 * A p-value as the panel shows it: three decimals, „< 0,001” below.
 *
 * @param {number} value the p-value
 * @returns {string} the text
 */
function pValue(value) {
  return value < 0.001 ? texts.homogeneity.pBelow : num(value, 3);
}

/**
 * The notices of the homogeneity tests that belong beside the section's own: the tests
 * that reject (the series' notices are the run's already).
 *
 * @param {object} run the last run
 * @returns {object[]} the notices
 */
function homogeneityNotices(run) {
  const notices = (run.homogeneity && run.homogeneity.notices) || [];
  return notices.filter((notice) => notice.code === "homogeneity_rejected");
}

/**
 * „Jednorodność ciągu”: each test's statistic, p-value and verdict, the split and Pettitt's
 * most probable change point, or why the tests gave nothing.
 *
 * @param {{run: object}} props the last run (its `homogeneity` envelope or error)
 * @returns {object} the part
 */
function Homogeneity({ run }) {
  const words = texts.homogeneity;
  const result = run.homogeneity ? run.homogeneity.result : null;
  const heading = html`<h3 class="group-title">${words.title} <${InfoButton} id="stats-homogeneity" /></h3>`;
  if (!result) {
    return html`<div data-part="homogeneity">
      ${heading}
      <p class="note">${t(words.failed, { message: run.homogeneityError || texts.results.cancelled })}</p>
    </div>`;
  }
  const alpha = shortNumber(result.significance_level);
  const verdict = (ok) => html`<span class=${ok ? "ok-mark" : "bad-mark"} title=${ok ? words.homogeneousTitle : words.rejectedTitle}>${ok ? "✓" : "✗"}</span> ${ok
      ? words.homogeneous
      : words.rejected}`;
  const columns = [
    { key: "name", label: words.test, format: (name) => words.tests[name] },
    { key: "statistic", label: words.statistic, format: (value, row) => `${words.symbols[row.name]} = ${auto(value, 3)}` },
    { key: "p_value", label: words.p, format: pValue },
    { key: "homogeneous", label: words.verdict, format: verdict },
  ];
  const n = result.n_years;
  const first = result.split_index;
  const split =
    result.split_year === null
      ? t(words.splitValues, { first, next: first + 1, n })
      : t(words.split, { year: result.split_year, first: plural(first, texts.yearForms), second: plural(n - first, texts.yearForms) });
  const { pettitt } = result;
  const weight = pettitt.homogeneous ? t(words.notSignificant, { alpha }) : "";
  const change =
    pettitt.change_point_year === null
      ? t(words.changePointValues, { index: pettitt.change_point_index, weight })
      : t(words.changePoint, { year: pettitt.change_point_year, weight });
  return html`<div data-part="homogeneity">
    ${heading}
    <${DataTable}
      columns=${columns}
      rows=${TESTS.map((name) => ({ name, ...result[name] }))}
      label=${words.title}
      tall=${false}
    />
    <p class="note">${[split, change, t(words.level, { alpha })].join(" ")}</p>
  </div>`;
}

/**
 * The panel Wyniki.
 *
 * @param {{run: object|null, shown: {distributions: string[], methods: string[]},
 *   fits: object[], best: string|null, periods: number[], stressed: number|null,
 *   ticked: string[], onTick: (key: string, on: boolean) => void, active: string|null,
 *   onActive: (key: string) => void, spec: object|null,
 *   reference: {pressed: boolean, toggle: (() => void)|null}|null}} props the last run, the
 *   filters of the combinations shown (the notices of the others stay hidden), the
 *   combinations shown and the key of the best one, its return periods and the stressed one
 *   (null for „brak”), the keys of the combinations in the quantile table and the change of
 *   one of them, the key of the active combination and its change, the export spec and the
 *   state of „Do porównania” (no toggle: off until a period is highlighted)
 * @returns {object} the panel's body
 */
export function ResultsPanel({ run, shown, fits, best, periods, stressed, ticked, onTick, active, onActive, spec, reference }) {
  if (!run) return html`<p class="muted">${texts.noResult}</p>`;
  const { envelope } = run;
  if (envelope.status !== "ok") {
    return html`
      <h3 class="group-title">${texts.results.notices}</h3>
      <${Notices} notices=${envelope.notices || []} />
    `;
  }
  const result = envelope.result;
  const quantileFits = tickedFits(result, ticked);
  const named = namesMethods(fits);
  const second = secondPeriod(periods, stressed);
  const fit = fits.find((item) => fitKey(item) === active) || null;
  // The quantile table: the ticked combinations, or a note while none is ticked
  let quantiles = null;
  if (quantileFits.length) {
    quantiles = html`
      <h3 class="group-title">${quantilesTitle(quantileFits, named)} <${InfoButton} id="stats-distributions" /></h3>
      <${Quantiles} fits=${quantileFits} named=${named} stressed=${stressed} />
    `;
  } else if (fits.length) {
    quantiles = html`
      <h3 class="group-title">${texts.results.quantilesNone} <${InfoButton} id="stats-distributions" /></h3>
      <p class="note">${texts.results.noneTicked}</p>
    `;
  }
  return html`
    <${Tiles} result=${result} fit=${fit} best=${best} stressed=${stressed} second=${second} />
    <h3 class="group-title">${texts.results.notices} <${InfoButton} id="stats-flood-frequency" values=${{ n_years: result.n_years }} /></h3>
    <${Notices} notices=${[...shownNotices(envelope.notices || [], shown), ...homogeneityNotices(run)]} />
    <h3 class="group-title">${texts.results.distributions} <${InfoButton} id="stats-fit" /></h3>
    ${fits.length
      ? html`<${Distributions}
          fits=${fits}
          best=${best}
          stressed=${stressed}
          second=${second}
          ticked=${ticked}
          onTick=${onTick}
          active=${active}
          onActive=${onActive}
        />`
      : html`<p class="note">${texts.results.noneShown}</p>`}
    ${quantiles}
    <${Homogeneity} run=${run} />
    <div class="steps">
      <details class="step" data-part="exports">
        <summary>
          <span class="title">${texts.results.export}</span><span class="meta">${COMMAND}</span>
          <svg class="chev" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 5l4 4 4-4" /></svg>
        </summary>
        <div class="step-body">
          <${ExportButtons} spec=${spec} />
          ${reference
            ? html`<div class="btn-row">
                <button
                  class="btn"
                  type="button"
                  aria-pressed=${reference.pressed ? "true" : "false"}
                  disabled=${!reference.toggle}
                  title=${reference.toggle ? texts.results.referenceTitle : texts.results.referenceNone}
                  onClick=${reference.toggle}
                >${reference.pressed ? `✓ ${texts.results.referenceOn}` : texts.results.reference}</button>
              </div>`
            : null}
          <${CommandLine} command=${COMMAND} options=${run.options} title=${false} />
        </div>
      </details>
    </div>
  `;
}
