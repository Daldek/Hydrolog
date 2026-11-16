# 0022. Homogeneity tests of annual maxima: Mann-Whitney U, two-sample Kolmogorov-Smirnov and Pettitt

- Status: accepted
- Date: 2026-11-06
- Builds on: plan `docs/plans/2026-11-06-flow-statistics-feedback.md` (decision D5), the report 3 of „Zgłoś uwagę”

## Context

A report of „Zgłoś uwagę” on Statystyka przepływów asked for a test of the homogeneity of the series („Brakuje
badania jednorodności ciągów pomiarowych”). A flood frequency analysis takes the annual maxima as a sample of one
distribution; a change of the catchment or of the gauge (a reservoir, a regulated reach, a moved station) breaks that.
Hydrolog tested a series only for a monotonic trend (`stats mann-kendall`). The author chose three tests: Mann-Whitney
U, the two-sample Kolmogorov-Smirnov test and Pettitt's test.

## Decision

1. **The command `stats homogeneity`** takes the series of `stats flood-frequency` (the annual maxima of the complete
   hydrological years of a daily series, or annual maxima given as values) and, for annual maxima, their years:
   `years` with `values`, `year_column` with `input_file` (whole numbers, strictly increasing, gaps allowed; not with
   `dates` or `date_column`, whose hydrological years are the years then); then `split_year` and `alpha` (default
   0.05, in (0, 1)). Its result `hydrolog-stats-homogeneity/1` is the library's result. The library function is
   `hydrolog.statistics.homogeneity_tests(series, years=None, *, split_year=None, alpha=0.05)`; its
   `HomogeneityResult` gives `n_years` (the number of values, one a year), the split (`split_index`, `split_year`),
   `mann_whitney` and `kolmogorov_smirnov` (`TwoSampleTestResult`: `statistic`, `p_value`, `homogeneous`), `pettitt`
   (`PettittResult`: the same and `change_point_index`, `change_point_year`) and `significance_level`.
2. **The split**: the first part holds the values of the years before `split_year`, the second those from
   `split_year` on. Without `split_year` the first part is the first ⌊n/2⌋ values (an odd n puts the middle value in
   the second part). `split_year` needs the years (integers, one per value, increasing; gaps allowed); it need not be
   a year of the series (a skipped incomplete year splits between its neighbours) but must leave a value in each part,
   so it lies from the first year + 1 to the last year. The result names the split by `split_index`, the number of
   values of the first part (the 0-based index of the first value of the second part), and `split_year`, the year of
   that value (`null` without years).
3. **Mann-Whitney U**, two-sided (scipy's `mannwhitneyu`: exact when a part has at most 8 values and there are no
   ties, otherwise the normal approximation with the corrections for ties and continuity). The statistic is U of the
   first part: the number of pairs (a value of the first part, a value of the second) in which the first is larger, a
   tie counting ½. Under homogeneity it is about n₁n₂/2; 0 means that every value of the first part is smaller.
4. **The two-sample Kolmogorov-Smirnov test** (Smirnov 1939), two-sided (scipy's `ks_2samp`, exact for series of
   annual maxima): the statistic D is the largest distance between the empirical distribution functions of the parts.
5. **Pettitt's test** of the whole series (Pettitt 1979): U_t = Σ_{i≤t} Σ_{j>t} sgn(x_i − x_j) for t = 1, …, n − 1,
   computed from the ranks r_i (mid-ranks for ties) as U_t = 2 Σ_{i≤t} r_i − t(n + 1); the statistic K = max |U_t|
   and the approximate p-value 2·exp(−6K²/(n³ + n²)), capped at 1 (the approximation is good for p ≤ 0.5 and exceeds 1
   for a small K). The change point is the t of K (the first t if several give K), named like the split:
   `change_point_index` = t, the number of values before the change (the 0-based index of the first value after it),
   and `change_point_year`, the year of the first value after the change. So `split_year` = `change_point_year` makes
   Mann-Whitney and Kolmogorov-Smirnov compare the parts that Pettitt's test found.
6. **`homogeneous`** is `p_value ≥ alpha`: the test does not reject homogeneity at `alpha` (as `trend_detected` of the
   Mann-Kendall test is `p_value < alpha`).
7. **Errors** (registry codes, `details.reason`). The library: fewer than 3 values: `calculation_error`,
   `too_few_values` (`count`, `minimum`); all values equal: `calculation_error`, `constant_values` (Mann-Whitney's U
   has no variance and Pettitt's test no change point); a value that is not a finite number: `validation_error`,
   `not_finite`; years that are not integers, not one per value or not increasing: `validation_error` with `option`
   `years` and `type`, `length_mismatch` or `not_increasing`; `split_year` without years: `validation_error`,
   `option` `years`, `required`; `split_year` that leaves a part empty: `validation_error`, `option` `split_year`,
   `range` (`minimum`, `maximum`). The command checks its series first: fewer than 3 annual maxima end with
   `calculation_error` (`count`, `minimum`, as `stats flood-frequency`); years that are not whole numbers (`type`, in
   a file `bad_year`), not one per value (`length_mismatch`) or not increasing (`years_not_increasing`), and `years`
   with `dates` or `year_column` with `date_column` (`conflict`) end with `validation_error`, from a file with
   `data_error`; `split_year` without years ends with `validation_error`, `option` `years` (inline values) or
   `year_column` (a file), `required`.
8. **The notice `homogeneity_rejected`** (warning) when a test rejects homogeneity: `details.tests` lists the tests
   that reject by their keys in the result (`mann_whitney`, `kolmogorov_smirnov`, `pettitt`), `details.alpha` the
   level.
9. **GUI**: a panel „Jednorodność ciągu” in Wyniki of Statystyka, run with the same series; a notice when a test
   rejects homogeneity.

## Consequences

- An additive change: a new command, its schema, a notice code and a library function; no other result changes. The
  series loader (`hydrolog.catalog.inputs.load_series`) gains `years` and `year_column`, which only this command
  declares.
- The command index of `AGENTS.md` names the `stats` commands on one line, as it does those of `route` (ADR-0009):
  with one line per command the guide would grow to 16,504 bytes, past its 16 KiB; `commands list` still gives every
  summary. A deviation from DOC-4.2 listed in `CLAUDE.md`.
- A short series rarely rejects homogeneity: split into halves, Mann-Whitney and Kolmogorov-Smirnov can reject at
  α = 0.05 from 8 values (4 and 4), Pettitt's test from 11. `homogeneous` says that a test found no difference, not
  that there is none. The tests take the values as independent, as the Mann-Kendall test does.
- The unit tests: a series with a step (all three tests reject), a deterministic series without one (none rejects),
  the change point of a step, K of a small series computed by hand, the split and the errors.
- COMPUTATION_PATHS, USAGE, the CHANGELOG, the guide `instrukcja/`, `AGENTS.md` and `llms.txt` describe the command
  on the branch that adds it.

## Alternatives considered

- **The change point as the last value before the change** (Pettitt's t as a 1-based position, as R's `trend` and
  Python's `pyHomogeneity` give it, and the year of that value): `split_year` would then have to be the last year of
  the first part, though a user who splits at the year of a change (a reservoir filled in 1975) means the years before
  it and from it on. `change_point_index` is the same number as their position; the year here is the next one.
- **Pettitt's p-value by simulation** (the default of `pyHomogeneity`: 20 000 series drawn from the normal
  distribution): random and slower; the approximation of Pettitt is the one of the plan and of R's `trend`.
- **`split_year` only a year of the series**: a skipped incomplete year would be refused, though the split it means is
  clear.
- **Years only from the dates of a daily series** (exactly the series options of `stats flood-frequency`): annual
  maxima with a year column (`annual_maxima.csv` and `maksima_roczne.csv` of `tests/fixtures/`, the `step` `year`
  series of the hand-off) would have no years, so no `split_year` and no year of the change point, though D5 of the
  plan names values with optional years.
- **min(U₁, U₂)**, the statistic of the printed tables: it loses the direction of the difference.
- **No default split**: the halves give a first answer without a year; Pettitt's change point then suggests one.
- **Other tests** (Buishand's range, the standard normal homogeneity test, the Wald-Wolfowitz runs test): the author
  chose these three.
