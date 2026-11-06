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
