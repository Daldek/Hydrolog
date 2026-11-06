# Plan: flow statistics after the reports of „Zgłoś uwagę” (2026-11-04, 2026-11-06)

Requested: 2026-11-06

The author asked on 2026-11-06 for the reports 3, 4, 8, 9, 10, 11 and 12 of
`feedback.sqlite3` (Statystyka przepływów), on new branches stacked one on another (each from
the previous; merged in order only with the author's approval, DEV-3.3), and chose the
homogeneity tests of report 3. The other decisions below are the agent's, for the author's
review before the merge. Requirements: DEV-17.4, AGI-1.1, AGI-4.1 to AGI-4.3, DOC-7.2.

## Reports

| # | Report (Polish, as sent) | Branch |
|---|---|---|
| 4, 12 | Brakuje wyboru metody dopasowania parametrów rozkładu; poza MLE dodać MoM, L-momenty i najmniejsze kwadraty | `feature/fit-methods` |
| 8, 11 | Kwantyle tylko dla najlepszego rozkładu, dodać wybrane z tabeli rozkładów; wybrany rozkład wyróżniony na wykresach, pozostałe przygaszone | `feature/stats-distribution-selection` |
| 10 | Dodać 2 wykresy: gęstości prawdopodobieństwa i dystrybuanty | `feature/stats-density-charts` |
| 9 | „Wyróżniony w wynikach” domyślnie wyłączony, dodać taką opcję | `feature/stats-no-chosen-period` |
| 3 | Brakuje badania jednorodności ciągów pomiarowych | `feature/homogeneity-tests` |

Order of the stack: the table above, top to bottom; `feature/fit-methods` starts from `develop`
(`d12131e`).

## Decisions

### D1. Fit methods (`stats flood-frequency --fit-method`, ADR-0021)

- New option `fit_method` of `stats flood-frequency`: `mle` (default; results unchanged),
  `moments`, `l_moments`, `least_squares`. The result carries `fit_method`; the schema
  `hydrolog-stats-flood-frequency/1` gains the field (additive).
- Every method gives the same parameters as today's MLE for each distribution (the scipy
  parametrisation of `high_flows.py`: log-normal with location 0, GEV, Pearson III, Weibull),
  so quantiles, K-S, A² and the ranking code stay as they are.
- `moments`: the sample mean, variance and (three-parameter distributions) skewness, unbiased.
- `l_moments`: the sample L-moments (unbiased probability-weighted moments) and the closed
  forms or the published approximations of Hosking and Wallis (1997); Weibull through the GEV
  of the negated sample.
- `least_squares`: the parameters minimising the sum of squared differences between the
  sorted sample and the quantiles at the plotting positions the result's `empirical` already
  uses, started from the `moments` estimate.
- AIC stays the ranking: the log-likelihood at the estimated parameters with the same number
  of parameters; for a method other than `mle` the ranking compares distributions fitted by
  that method. A method that gives no parameters for a distribution (fewer than 3 values, all
  values equal, a sample skewness or L-skewness outside the distribution's range, a value not
  above 0 for the log-normal) leaves that distribution out with a notice, not an error,
  unless no distribution remains (then the registry's computation error code). A fit whose
  support leaves out an annual maximum (with the moments and the L-moments most often a lower
  bound of Pearson III or Weibull above the smallest one, in 9-91 % of samples of 30 to 60
  years in trials) stays with its quantiles: its AIC is infinite (`null` in JSON), it ranks
  after the fits with a finite AIC and a notice names the values outside the support.
- GUI: a choice field „Metoda estymacji parametrów” in Dane of Statystyka; both runs (the
  table's and the curves') use it.

### D2. Distributions chosen in the table (reports 8 and 11, GUI only)

- Each row of the distributions table gets a checkbox „W tabeli kwantyli” (only the best one
  ticked after every computation) and can be made the active distribution by a click (the best
  one after every computation).
- The quantile table has one Q column per ticked distribution, in the order of the
  distributions table; the CSV export follows it.
- The active distribution drives the tiles and „Do porównania”, its curve is drawn full and
  thick, the others dimmed; the tile names the distribution (and „najlepszy” when it is).
- The choice is not stored: a new result resets it.

### D3. Density and distribution-function charts (report 10)

- The GUI computes no hydrological value (plan 2026-11-02, Goal), so the library gives the
  density: every distribution of the result gains `densities` [1/(m³/s)], the density at each
  of its `quantiles` (additive field of `hydrolog-stats-flood-frequency/1`).
- Two charts beside the probability plot, from the curves' run (its grid of return periods is
  made dense enough for a smooth density): „Gęstość prawdopodobieństwa” (density against Q,
  the annual maxima as a rug on the axis) and „Dystrybuanta” (F = 1 − p against Q, with the
  empirical points of `empirical`). Highlighting as D2.

### D4. No highlighted period by default (report 9, GUI only)

- „Wyróżniony w wynikach” gains „brak” and starts with it. Without a highlighted period the
  tiles show no Q p% tile, no row of the quantile table is marked, the charts have no guides
  and „Do porównania” is off until a period is chosen. The stored inputs' version is raised
  only if their shape changes.

### D5. Homogeneity tests (`stats homogeneity`, report 3, ADR-0022)

- The author chose Mann-Whitney U, the two-sample Kolmogorov-Smirnov test and Pettitt's test.
- New command `stats homogeneity` with the series options of `stats flood-frequency` (annual
  maxima of complete hydrological years from a daily series, or values with optional years),
  `split_year` (default: the series split into halves, the first ⌊n/2⌋ values) and `alpha`
  (default 0.05). Result `hydrolog-stats-homogeneity/1`: the series length, the split, and for
  each test its statistic, p-value and `homogeneous` at `alpha`; Pettitt also the change point
  (index and year). Mann-Whitney and K-S two-sided (scipy); Pettitt's statistic K and its
  approximate p-value 2·exp(−6K²/(n³ + n²)).
- GUI: a panel „Jednorodność ciągu” in Wyniki of Statystyka, run with the same series; a
  notice when a test rejects homogeneity.

## Steps

Each branch in small commits; tests of the changed parts only (no `scripts/gate.sh` until the
author asks, his decision of 2026-11-06); the docs (CHANGELOG, COMPUTATION_PATHS, USAGE, the
guide `instrukcja/`, regenerated `AGENTS.md` and `llms.txt`) on the branch that changes them.

## Results

- `feature/fit-methods` (D1, ADR-0021): `stats flood-frequency --fit-method` (`mle`, `moments`,
  `l_moments`, `least_squares`), the library keyword `fit_method`, the notices
  `distribution_left_out` and `outside_support`, „Metoda estymacji parametrów” in the GUI; the
  Statystyka pictures of the guide are to be taken again (PROGRESS, Next 8).
- `feature/stats-distribution-selection` (D2, GUI only): „W tabeli kwantyli” in each row of the
  distributions table (one Q column per ticked distribution in the quantile table and the CSV)
  and the active distribution chosen by a click on its row (the tiles, „Do porównania” and the
  full curve of the plot, the others dimmed); the best one after every computation, nothing
  stored. The last ticked distribution cannot be unticked, so the quantile table always has a
  column. The Statystyka pictures of the guide are to be taken again (PROGRESS, Next 8).
- `feature/stats-density-charts` (D3): `densities` [1/(m³/s)] in every distribution of the
  `stats flood-frequency` result (the fitted density at each quantile; nested, so the schema is
  unchanged) and, under the probability plot, „Gęstość prawdopodobieństwa” (a rug of the annual
  maxima) and „Dystrybuanta” (the empirical points), highlighted as D2 and cut at the larger of
  the largest maximum and the active distribution's Q 1%. The curves' run has 106 return periods
  (p every 1% from 99% to 2%, finer at both ends). The charts kit gained the series kind `rug`.
  The Statystyka pictures of the guide are to be taken again (PROGRESS, Next 8).
- `feature/stats-no-chosen-period` (D4, GUI only): „brak” is the first value of „Wyróżniony w
  wynikach” and the value of a first visit and of „Wyczyść”: no highlighted tile, no marked row of
  the quantile table, no marked quantile on the probability plot (the density and
  distribution-function charts never marked one) and „Do porównania” disabled with a title saying
  why; the second Q tile (10 years) stays, unhighlighted. The stored shape did not change (`chosen`
  may be `null`), so the key stays `hydrolog-gui/statystyka/2` and a stored 100, the former
  default, which cannot be told apart from a chosen 100, stays highlighted until „brak” or
  „Wyczyść”. The guide's example chooses 100 before „Oblicz”; the Statystyka pictures of the guide
  are to be taken again (PROGRESS, Next 8).
- `feature/homogeneity-tests` (D5, ADR-0022): `stats homogeneity` and
  `hydrolog.statistics.homogeneity_tests`: Mann-Whitney U and two-sample Kolmogorov-Smirnov of the
  series split at `split_year` (default: the first ⌊n/2⌋ values against the rest), Pettitt's K
  with p ≈ 2·exp(−6K²/(n³ + n²)) and its change point; the split and the change point are named by
  the first value after them (index and year), so `split_year` = `change_point_year` compares the
  parts Pettitt found. Beyond the plan's wording: annual maxima take their years from `years`
  (inline) or `year_column` (a file), which the series loader gained; the notice
  `homogeneity_rejected` names the tests that reject; `AGENTS.md` names the `stats` commands on
  one line, as those of `route` (16 KiB; a DOC-4.2 deviation in CLAUDE.md). GUI: „Jednorodność
  ciągu” under the quantile table in Wyniki, run on the same series (a file's year column; pasted
  values and a hand-off's annual maxima have positions, not years), with the defaults (halves,
  α = 0.05); the notice joins „Uwagi”. The Statystyka pictures of the guide are to be taken again
  (PROGRESS, Next 8).
- `feature/fit-method-all` (D6, ADR-0021 amended): `fit_method` `all` in the library
  (`FloodFrequencyAnalysis.fit_all(fit_method="all", distribution=...)`, keys
  `"<distribution>/<fit_method>"`) and in `stats flood-frequency` (also with one distribution);
  every item carries `fit_method`; one AIC ranking; a combination without parameters is left out
  with `distribution_left_out` (one combination asked for is its own error). The default is
  `l_moments` in the library, the operation, the catalog and so the GUI; the guide's example gives
  GEV Q 1% 324,9 m³/s (307,3 by maximum likelihood) and its Pearson III has no AIC. Beyond the
  plan's wording: the GUI's choice field hides `all` until D7; `plot_frequency_comparison` names
  the method of a curve when the results hold several. Found: scipy's maximum likelihood does not
  always reach the lowest AIC of its distribution (its GEV of the unit tests' 11 values: 129.1
  against 118.6 by the L-moments), hence the wording of D7. The Statystyka picture of the guide is
  to be taken again (PROGRESS, Next 8).

## Erratum 2026-11-06: the author's review of the deployed Statystyka

The author approved the decisions reported for review (the compact `stats` line of `AGENTS.md`,
Pettitt's change point as the first year after it, the least-squares note, the stored T = 100,
`densities` from the library, fits outside their support kept with a null AIC) and asked for the
following. Each item is a new branch, stacked on `feature/homogeneity-tests` in this order.

### D6. Every combination of distribution and fit method (`feature/fit-method-all`, ADR-0021 amended)

- `fit_method` of `stats flood-frequency` and of the library gains `all` (each distribution
  fitted by each method, as `distribution` has `all`); every item of `distributions` carries its
  `fit_method`; the ranking stays AIC over all items; the result's `fit_method` is the value asked
  for. A combination the method cannot fit is left out with `distribution_left_out`, as today.
- The default of `fit_method` becomes `l_moments` (library, CLI, MCP, GUI): maximum likelihood is
  less stable on the short samples of annual maxima. The guide's quoted numbers follow.

### D7. Combinations in the GUI (`feature/stats-combinations-view`)

- Statystyka runs `fit_method=all`, `distribution=all` once; in Dane, „Rozkłady” and „Metody
  estymacji” are multiple choices that only filter what is shown (default: every distribution,
  L-moments only); changing them does not recompute.
- Colour = distribution, line style = fit method (solid, dashed, dotted, dash-dot), on every
  chart and legend; the distributions table has one row per shown combination (distribution,
  method, AIC, …); „najlepszy” is the lowest AIC among the shown combinations (with every method
  shown, AIC across the methods favours maximum likelihood when its search converges; scipy's
  search may stop short of the maximum, ADR-0021 amendment: the (i) text says so).
- „W tabeli kwantyli” can untick every row, the best one included; with none ticked the quantile
  table says so instead of showing columns.

### D8. Charts readable at every width, axes from zero, stable ranges (`feature/stats-chart-layout`)

- The density and distribution-function charts stand one under the other; every Statystyka chart
  has a maximum width and height, so a very wide window does not blow them up.
- No axis of any GUI chart starts below 0.
- An axis range depends only on the result, not on the active, ticked or shown combinations; the
  density's range ignores spikes at a distribution's bound (a robust rule over the combinations'
  peaks, recorded in the code and the (i) text); the person may set the range of each axis
  (min/max, „Auto” restores the default).

### D9. Live recompute (`feature/stats-live-recompute`)

- As in Hydrogram zlewni (plan 2026-11-02, D13, extended to Statystyka): every change of an input
  recomputes after a short debounce, the newest run wins; „Oblicz” goes.
