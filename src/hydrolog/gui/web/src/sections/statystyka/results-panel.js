// The results of „Statystyka przepływów”: in the centre the probability plot and the ranked
// annual maxima, in the panel Wyniki the tiles, the notices in Polish, the fitted
// distributions with their goodness of fit, the quantiles of the distributions ticked in
// their table (the best one after every computation) and the exports (CSV of those
// quantiles, the envelope as JSON, the chart as PNG, „Do porównania” and the call).

import { Chart } from "../../charts/chart.js";
import { num, plural } from "../../format.js";
import { Notices } from "../../forms/result-view.js";
import { html, useMemo } from "../../html.js";
import { t } from "../../labels/common.js";
import { statystyka as texts } from "../../labels/statystyka.js";
import { CommandLine, ExportButtons } from "../../ui/export-panel.js";
import { InfoButton } from "../../ui/info-button.js";
import { DataTable } from "../../ui/table.js";
import { probabilitySpec } from "./charts.js";
import { COMMAND, DISTRIBUTION_CLASS, percentAt, quantileAt, secondPeriod, shortNumber, tickedFits } from "./state.js";

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
 * The fit of the best distribution of a result.
 *
 * @param {object} result the result of `stats flood-frequency`
 * @returns {object|null} the fit
 */
export function bestFit(result) {
  return result.distributions.find((fit) => fit.distribution_name === result.best_distribution) || null;
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
 * The centre: the probability plot, or the table of the ranked annual maxima.
 *
 * @param {{run: object|null, tab: "chart"|"series", stressed: number|null,
 *   chartSvg: object}} props the last run, the tab shown, the stressed return period and the
 *   ref of the chart's SVG (for PNG)
 * @returns {object} the centre's body
 */
export function CenterBody({ run, tab, stressed, chartSvg }) {
  const result = run && run.envelope.status === "ok" ? run.envelope.result : null;
  const spec = useMemo(
    () => (result ? probabilitySpec({ result, curves: run.curves, chosen: stressed }) : null),
    [result, run && run.curves, stressed],
  );
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
  const fits = result.distributions.length;
  const method = result.fit_method || "mle";
  return html`
    <div class="card st-chart">
      <div class="card-head">
        <h3 class="card-title" id="st-chart-title">${texts.chart.title} <${InfoButton} id="stats-plot" /></h3>
        <span class="card-sub" data-fit-method=${method}>${t(texts.chart.sub, {
          count: plural(result.n_years, texts.chart.maximaForms),
          fits: plural(fits, texts.chart.fitForms),
          method: Object.hasOwn(texts.fitMethods, method) ? texts.fitMethods[method] : method,
        })}</span>
      </div>
      <${Chart} spec=${spec} svgRef=${chartSvg} />
      ${run.curvesError ? html`<p class="note">${t(texts.chart.curvesFailed, { message: run.curvesError })}</p>` : null}
    </div>
  `;
}

/**
 * The tiles: the best distribution, the stressed quantile and another one, the length.
 *
 * @param {{result: object, stressed: number|null, second: number|null}} props the result
 *   and the two return periods
 * @returns {object} the tiles
 */
function Tiles({ result, stressed, second }) {
  const fit = bestFit(result);
  const tile = (key, label, value, unit, hi = false) => html`
    <div class=${`kpi${hi ? " hi" : ""}`} data-key=${key}>
      <div class="k">${label}</div>
      <div class="v">${value}${unit ? html` <span class="u">${unit}</span>` : null}</div>
    </div>
  `;
  const quantile = (period, hi) => {
    const q = quantileAt(fit, period);
    return q === null ? null : tile(`q-${period}`, quantileLabel(fit, period), num(q, 1), "m³/s", hi);
  };
  const [count, ...word] = plural(result.n_years, texts.yearForms).split(" ");
  return html`
    <div class="summary">
      ${tile("distribution", texts.results.distribution, distributionName(result.best_distribution))}
      ${stressed !== null ? quantile(stressed, true) : null}
      ${second !== null ? quantile(second, false) : null}
      ${tile("n_years", texts.results.length, count, word.join(" "))}
    </div>
  `;
}

/**
 * The fitted distributions: the box „W tabeli kwantyli”, AIC, A² against its critical
 * value, the p-value of KS and two quantiles; the best first, as Hydrolog sorts them.
 *
 * @param {{result: object, stressed: number|null, second: number|null, ticked: string[],
 *   onTick: (name: string, on: boolean) => void}} props the result, the two return periods,
 *   the distributions in the quantile table and the change of one of them
 * @returns {object} the table and its note
 */
function Distributions({ result, stressed, second, ticked, onTick }) {
  const best = result.best_distribution;
  const critical = adCritical(result.distributions[0]);
  const columns = [
    {
      key: "distribution_name",
      label: texts.results.distribution,
      format: (name) => html`<i class=${`sw-line ${DISTRIBUTION_CLASS[name] || "s4"}`} aria-hidden="true"></i>${distributionName(name)}${name === best
        ? html` <span class="badge ok">${texts.results.best}</span>`
        : null}`,
    },
    // Beside the name, in sight in a narrow panel; the last ticked one stays, so the
    // quantile table always has a column
    {
      key: "distribution_name",
      label: html`<span class="wrap">${texts.results.inQuantiles}</span>`,
      className: "pick",
      format: (name) => {
        const on = ticked.includes(name);
        return html`<input
          type="checkbox"
          checked=${on}
          disabled=${on && ticked.length === 1}
          aria-label=${t(texts.results.inQuantilesOf, { name: distributionName(name) })}
          onChange=${(event) => onTick(name, event.currentTarget.checked)}
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
      label: quantileLabel(bestFit(result), period),
      format: (_, fit) => {
        const q = quantileAt(fit, period);
        return q === null ? "—" : num(q, 1);
      },
    });
  }
  const issues = [];
  for (const fit of result.distributions) {
    const found = [];
    if (typeof fit.aic !== "number") found.push(texts.results.noAic);
    const limit = adCritical(fit);
    if (typeof fit.ad_statistic === "number" && limit !== null && fit.ad_statistic >= limit) found.push(texts.results.adAbove);
    if (found.length) issues.push(t(texts.results.issues, { name: distributionName(fit.distribution_name), issues: found.join(", ") }));
  }
  return html`
    <${DataTable}
      columns=${columns}
      rows=${result.distributions}
      label=${texts.results.distributions}
      tall=${false}
      rowClass=${(fit) => (fit.distribution_name === best ? "best" : null)}
    />
    <p class="note">${[...issues, texts.results.unit].join(" ")}</p>
  `;
}

/**
 * The quantiles of the ticked distributions, one column each, the stressed period marked.
 *
 * @param {{fits: object[], stressed: number|null}} props the ticked fits, in the order of
 *   the distributions table, and the stressed period
 * @returns {object} the table
 */
function Quantiles({ fits, stressed }) {
  const [first] = fits;
  const rows = first.return_periods.map((period, index) => {
    const row = { period, p: first.exceedance_probabilities[index] * 100 };
    for (const fit of fits) row[fit.distribution_name] = fit.quantiles[index];
    return row;
  });
  return html`<${DataTable}
    columns=${[
      { key: "period", label: texts.results.period, unit: texts.results.periodUnit, format: (value) => shortNumber(value, 6) },
      { key: "p", label: texts.results.probability, unit: "%", format: (value) => shortNumber(value) },
      ...fits.map((fit) => ({
        key: fit.distribution_name,
        // A long name wraps, its unit with it: the table stays within the panel
        label: html`<span class="wrap">${t(texts.results.quantileOf, { name: distributionName(fit.distribution_name) })} <span class="u">[m³/s]</span></span>`,
        format: (value) => num(value, 1),
      })),
    ]}
    rows=${rows}
    label=${quantilesTitle(fits)}
    tall=${false}
    rowClass=${(row) => (row.period === stressed ? "hl" : null)}
  />`;
}

/**
 * The title of the quantile table: „Kwantyle: GEV, Weibull”.
 *
 * @param {object[]} fits the ticked fits
 * @returns {string} the title
 */
function quantilesTitle(fits) {
  return t(texts.results.quantiles, { name: fits.map((fit) => distributionName(fit.distribution_name)).join(", ") });
}

/**
 * The panel Wyniki.
 *
 * @param {{run: object|null, periods: number[], stressed: number|null, ticked: string[],
 *   onTick: (name: string, on: boolean) => void, spec: object|null,
 *   reference: {pressed: boolean, toggle: () => void}|null}} props the last run, its return
 *   periods and the stressed one, the distributions in the quantile table and the change of
 *   one of them, the export spec and the state of „Do porównania”
 * @returns {object} the panel's body
 */
export function ResultsPanel({ run, periods, stressed, ticked, onTick, spec, reference }) {
  if (!run) return html`<p class="muted">${texts.noResult}</p>`;
  const { envelope } = run;
  if (envelope.status !== "ok") {
    return html`
      <h3 class="group-title">${texts.results.notices}</h3>
      <${Notices} notices=${envelope.notices || []} />
    `;
  }
  const result = envelope.result;
  const fits = tickedFits(result, ticked);
  const second = secondPeriod(periods, stressed);
  return html`
    <${Tiles} result=${result} stressed=${stressed} second=${second} />
    <h3 class="group-title">${texts.results.notices} <${InfoButton} id="stats-flood-frequency" values=${{ n_years: result.n_years }} /></h3>
    <${Notices} notices=${envelope.notices || []} />
    <h3 class="group-title">${texts.results.distributions} <${InfoButton} id="stats-fit" /></h3>
    <${Distributions} result=${result} stressed=${stressed} second=${second} ticked=${ticked} onTick=${onTick} />
    ${fits.length
      ? html`
          <h3 class="group-title">${quantilesTitle(fits)} <${InfoButton} id="stats-distributions" /></h3>
          <${Quantiles} fits=${fits} stressed=${stressed} />
        `
      : null}
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
                  title=${texts.results.referenceTitle}
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
