# Plan: station analyses for Obserwator: characteristic values, events, rating curves by period, low flows, duration curves, volumes, the batch, regime and meteorological statistics

Approved: 2026-11-13, the author's go-ahead for the Nogat plan's Hydrolog steps (in session)

The author approved Nogat's plan `docs/plans/2026-11-12-station-data-and-analyses.md` (Nogat branch
`plan/station-data-and-analyses`, `4c44a1f`) on 2026-11-13 with his answers (below) and the go-ahead to
implement, Hydrolog's extensions first. This plan is Hydrolog's part of it (DEV-17.4): Nogat's steps H1
to H4, the computations that Obserwator stores and serves. The decisions below are the agent's within
that approval; the merges wait for the author (DEV-3.3).

Requirements: DEV-17.4, DEV-3.3, AGI-1.1 (the catalog is the one source), AGI-4.1 to AGI-4.3 (result
documents and their schemas), AGI-5.3 (600 characters per tool description), DOC-1.7 (`AGENTS.md` at most
16 KiB), DOC-4.2, DOC-7.2, DOC-8.1 (ADRs), HUB-5.2 (producers before consumers); Nogat's decisions D6
(the batch), D8 (the same number), D12 (reference periods), F1 (IMGW-PIB's half-year extremes) and ECO-059.

## The author's answers that bind this plan (2026-11-13)

1. „Kod pobierania zostaje biblioteką Obserwatora, którą Archiwista wywołuje” (B1). Hydrolog keeps reading
   Obserwator's export files; nothing changes for it.
2. „… dane powinny być przeliczone raz, na początku i tyle, a pobieranie nowych będzie realizowane 1 raz w
   roku … Jeżeli user liczy jakieś rzeczy dla wybranego wycinka danych, to robimy to w locie i nie jest to w
   żaden sposób zapisywane na stałe.” Obserwator runs Hydrolog's batch once at the start and once a year
   (D10); a subset the person chooses is one call of a command, never stored. Every command is
   deterministic: the same series and options give the same bytes.
3. „Nie, danych operacyjnych nie archiwizujemy”: no IMGW-PIB warning or alarm levels. Events above a level
   take whatever level the caller gives (ČHMÚ's SPA 1–3, drought level and Q50, the characteristic levels
   of D3); Hydrolog has no table of levels.
5. Reference periods: the whole record by default, adjustable by the person, with a note that the
   recommended minimum period is 30 years (D1).
6. Exports are CSV, JSON and Parquet: Obserwator's files. Hydrolog's results stay JSON envelopes.

## Goal

- Every number of Obserwator's station analyses is computed by a command of Hydrolog's catalog (Nogat E1):
  the same series and options give the same result in Obserwator, in Hydrolog's CLI, MCP, Python and GUI.
- The mockup's prototypes (Obserwator branch `feat/gui-mockup`, `27cfb4e`,
  `mockup/gui/server/analyses/_hydro_proto.py` and `_meteo_proto.py`) move into the catalog with the method
  each names, and give the same numbers on the same series, or the difference is stated here.
- One process computes a whole station's analyses (the batch, D10).
- The catalog stays within its budgets: grouped commands where one method serves many indices, compact
  index lines (D2).

## Where it starts

Checked on 2026-11-13 on `develop` `912dbf2`, the Hydrolog the mockup runs.

| Fact | Consequence |
|---|---|
| `stats characteristic` gives the second degree of the whole series only: W, S, Z, N of the annual maxima, means and minima of every hydrological year with a value, partial years included (`statistics/characteristic.py:162-235`); `parameter` is a label, Q or H, and calls H's values WWH…NNH (`catalog/groups/stats.py:86-184`) | D3 adds the first degree, the half-years, the period, the Polish W labels, T and IMGW-PIB's half-year file |
| `stats low-flow-sequences` refuses a series with a missing value or a missing date (`operations/stats.py:850-881`) and needs a given `threshold` | D6: gaps in the record, thresholds from the series, yearly summaries |
| `hydrometrics rating-curve` fits stage–discharge pairs without dates (`catalog/groups/hydrometrics.py:17-215`) | D5: dated pairs, a range of years, successive periods |
| No command for runs above a level, duration curves or runoff volumes; class frequencies only inside `hydrometrics water-level-zones`, whose classes start at the floored lowest level (`hydrometrics/rating_curve.py:492-499`) | D4, D7, D8 are new commands |
| The mockup computes the characteristic values with `stats characteristic` and everything else of Nogat's H1–H4, H7, H8 and H17 in prototypes: `first_degree_daily`, `first_degree_half_years`, `second_degree`, `days_beyond_per_year`, `events_beyond`, `merge_low_flow_events`, `exceedance_values`, `log_classes`, `class_month_table`, and in `hydro.py` the rating periods, the low-flow summaries and the volumes | the method reference of D3 to D8 |
| The author's code of 2024/25 (IMGWTools `a10a0ec:code/hydro_stats.py`): `characteristic_values` (`:375`) pooled the winter and summer maxima for SWQ; `calculate_water_levels_frequency` (`:482`) counted 10 cm classes from a multiple of 10 by hydrological month, „including higher” and „including lower”; `find_low_sequences` (`:741`) kept runs of at least 5 days below a given threshold, merged across gaps under 4 days, with the deficit volume (`95ec3ea`) | D3 keeps the mean of *annual* maxima (Hydrolog's and IMGW-PIB's definition, as the mockup does); D7 takes the author's classes; D6 his defaults |
| Obserwator's daily export (`obserwator series export --dataset pl.imgw.hydro_daily`): `date,year,H [cm],H_flag,Q [m3/s],Q_flag,T [degC],T_flag,…`, a row per day with empty cells for missing values; the half-year export (`pl.imgw.hydro_semiannual`): `date,year,period,H_min [cm],…,H_min_start,H_min_end,…,Q_max [m3/s],…,T_max_start,…`, three rows per hydrological year, `winter`, `summer` and `annual`, the `annual` row with the means only. Kłodzko (150160180) in the demo store: 27,394 days of 1951–2025 without hydrological year 1997, 222 half-year rows | both files load without preprocessing (D3, D9); Kłodzko is the reproduction case of S1 |
| `AGENTS.md` has 15,922 of its 16,384 bytes (`tests/contract/test_agent_guide.py:134-138`); `stats` and `route` have one index line each (ADR-0009, ADR-0022), every other group one line per command | about 460 bytes for every step of this plan (D2) |
| A tool description (summary, description, rules) has at most 600 characters (`catalog/spec.py:82,842-847`); the GUI's „Wszystkie polecenia” shows 45 of the 48 commands (`tests/e2e/test_polecenia.py:190`); every notice code needs a Polish text in `gui/web/src/labels/notices.js` (`tests/contract/test_gui_web.py:168-173`) | short descriptions; the counts and the Polish texts follow each step |
| A CLI call costs about 1.4 s, mostly imports (plan 2026-11-02) | the batch (D10) |

## Decisions

### D1. The reference period: the whole record, a chosen range, a note under 30 years

- The commands of this plan that reduce a daily series over years take `first_year` and `last_year`
  (integers, hydrological years XI–X named after the year in which they end), either optional: by default
  the first and the last hydrological year with a value. They use the days of those years only. `first_year`
  after `last_year` is a `validation_error` (`reason` `range`); a period without a value a
  `calculation_error` (`reason` `no_values_in_period`).
- The result names the period used: `first_year`, `last_year` and `period_years`, the number of its
  hydrological years with a value.
- The notice `short_reference_period` (level `info`, details `years`, `first_year`, `last_year`, `minimum`)
  when `period_years` is under 30, from the commands whose result characterises the period as a whole: the
  second degree (`stats characteristic`), a threshold taken from the series (`stats low-flow-sequences`),
  `stats duration-curve`, the means of `stats runoff-volume` and, later, the regime, seasonality and
  normals of D11 and D12. Thirty years is the length of a climatological standard normal (WMO, 2017,
  *WMO Guidelines on the Calculation of Climate Normals*, WMO-No. 1203) and the author's recommended
  minimum. Lists of events and fits of chosen years (`stats threshold-events`,
  `hydrometrics rating-curve`) carry no such notice.

### D2. Budgets: grouped commands and compact index lines

- One command per method, with options for its variants: the meteorological statistics are two commands
  with an `index` option (D12), the water temperature days use `stats threshold-events` (D11), the flood
  quantiles of precipitation use `stats flood-frequency`. New commands join the compact `stats` line
  (ADR-0009, ADR-0022); the `meteo` group of D12 is compact from its first command.
- Measured before each commit; estimates: S1 adds three names and a shorter group clause to the `stats`
  line (about 110 bytes), S2 the line of `commands batch` (about 130), S3 four names (about 100), S4 the
  `meteo` group (about 300). Before S4 the guide would pass 16 KiB: S4 makes `hydrometrics` compact too and,
  if that is not enough, shortens the guide's prose or asks Nogat for a larger budget (DOC-1.7), with the
  measured sizes in its ADR.
- Every description stays within 600 characters; detail goes to the options' descriptions and to
  `docs/COMPUTATION_PATHS.md`.

### D3. `stats characteristic`: first degree, half-years, the period, W labels, T, IMGW-PIB's half-years (Nogat H1, H2)

Options (new or changed; the daily series options stay):

| Option | Type, default | Meaning |
|---|---|---|
| `half_year_file` | path | Obserwator's export of IMGW-PIB's half-year and annual characteristics (`pl.imgw.hydro_semiannual`, CSV or JSON): `year` (hydrological), `period` (`winter` XI–IV, `summer` V–X, `annual`), `<P>_min`, `<P>_mean`, `<P>_max` (found without the unit suffix) and, optional, `<P>_min_start`, `<P>_max_start` (the date of the extreme; a time part is dropped). A third `one_of` group beside the inline and the file series. |
| `parameter` | choice `Q`, `H`, `T`; `Q` | The variable: it names the labels and, with `half_year_file`, the columns. |
| `first_year`, `last_year` | integer | D1 |

Result `hydrolog-stats-characteristic/1` (additive; the number stays):

- Unchanged at the top: `wwx` … `nnx` of the year, `period_years`, `parameter`.
- `labels`: the Polish name of each key, `wwx` → `WWQ` (Q), `WWW` (H), `WWT` (T) and so on; the first
  letter is the statistic over the years (W highest, S mean, Z median, N lowest), the second the annual
  value it is taken of (W maximum, S mean, N minimum), the third the variable (W for the stage, „wodowskaz”).
  T follows the same scheme by analogy; IMGW-PIB publishes no such labels of water temperature.
- `first_degree_labels`: `{"max": "WW", "mean": "SW", "min": "NW"}` for H, `WQ`, `SQ`, `NQ` for Q, `WT`, `ST`,
  `NT` for T.
- `winter`, `summer`: the second degree of each half-year (`wwx` … `nnx`, `period_years`).
- `years`: the first degree of each hydrological year of the period with a value: `year` and `winter`,
  `summer`, `annual`, each `{min, mean, max, min_date, max_date, days_with_data, days}`.
- `source`: `daily` or `half_years`; `first_year`, `last_year`; `incomplete_years`: the years of the period
  with a day without a value (daily source).

Method:

- From a daily series: the minimum, mean and maximum of the days with a value of each half-year and year;
  the date of the extreme is the first day it occurs; `days_with_data` and the calendar `days`. A year with
  missing days stays in the second degree, as today, and is named in `incomplete_years` and in the notice
  `years_with_missing_days` (warning; details `count`, `total`, `years`): its extremes may be milder than
  the true ones. The annual second degree equals today's result on the same days, so the mockup's
  numbers stay.
- From IMGW-PIB's half-years (Nogat F1): the half-year values as published; the annual maximum is the
  larger of the two half-year maxima (with its date), the annual minimum the smaller of the minima, both
  `null` when a half-year is missing; the annual mean is the published one. `days_with_data` and `days`
  are `null`.
- Second degree: W, S, Z, N of the first-degree maxima, means and minima of the years that have them; SW is
  the mean of *annual* maxima, never of pooled half-year maxima (IMGW-PIB's definition; the author's 2024
  code pooled them). Each series counts its own years.
- Errors: a half-year file without the columns of `parameter` or with another `period` is a `data_error`
  (`missing_column`, `bad_period`); a year and period twice, `duplicate_period`.

### D4. `stats threshold-events` (new; Nogat H3, also the water temperature days of H15)

| Option | Type, default | Meaning |
|---|---|---|
| series | the dated options of `stats daily` | a daily series |
| `level` | number, required | the level, in the unit of the series |
| `direction` | choice `above`, `below`; `above` | a day is beyond the level when its value is at least `level` (`above`) or below it (`below`) |
| `min_duration_days` | integer ≥ 1; 1 | shortest event kept |
| `max_gap_days` | integer ≥ 0; 0 | runs parted by fewer days than this (days without a value or not beyond) merge; 0 merges none |
| `first_year`, `last_year` | integer | D1 |

Result `hydrolog-stats-threshold-events/1`: `level`, `direction`, `first_year`, `last_year`, `n_days`
(calendar days of the period), `n_missing_days`, `days_beyond`, `n_events`, `max_duration_days`;
`events`, each `{start_date, end_date, duration_days, days_beyond, missing_days, peak, peak_date,
hydrological_year, open_start, open_end}` (the peak is the maximum above a level, the minimum below one,
dated by its first day; `open_start` and `open_end` say that the day before or after has no value, so the
event may be longer); `years`, each `{year, days_beyond, n_events, days_with_data, days}` for the years of
the period with a value, an event counted in the year it starts. Method: the threshold level method
(Tallaksen and van Lanen, 2004) on the calendar of the series; a day without a value is never beyond the
level and, with `max_gap_days` 0, ends an event. With the defaults it gives the mockup's
`days_beyond_per_year` and `events_beyond`.

### D5. `hydrometrics rating-curve`: dated pairs, a range of years, successive periods (Nogat H4)

| Option | Type, default | Meaning |
|---|---|---|
| `dates` | string list | ISO dates of the inline pairs (with `water_levels` and `discharges`) |
| `date_column` | string | the date column of `input_file` |
| `first_year`, `last_year` | integer | the hydrological years of the pairs fitted; need dates |
| `years_per_period` | integer ≥ 1 | also fit the curve of each block of this many hydrological years; needs dates |

- The pairs are the days with both values; the curve of the range is the result as today (`a`, `b`,
  `h0`, …). Without dates nothing changes.
- Periods start at the years y with (y − 1) mod `years_per_period` = 0 (1951–1960, 1961–1970 for 10), the first
  and the last cut to the range, as the mockup's `rating_periods`. A period with at least 30 pairs is
  fitted with the same `h0_initial`, `remove_outliers` and `outlier_std`; one with fewer has no fit
  (`reason` `too_few_pairs`), one whose fit fails has `reason` `fit_failed`.
- Result `hydrolog-hydrometrics-rating-curve/1` (additive): `first_year`, `last_year` (`null` without
  dates); `periods` (`null` without `years_per_period`), each `{first_year, last_year, n_pairs, a, b, h0,
  r_squared, std_residuals, n_points, n_outliers_removed, discharge_at_reference_m3s,
  level_at_reference_discharge, reason}`; `reference_level` and `reference_discharge_m3s`, the medians of
  the pairs of the range, at which each period's curve is read, so that the shift of the curve is a number
  (`null` without periods).

### D6. `stats low-flow-sequences`: gaps, thresholds from the series, yearly summaries (Nogat H7)

| Option | Type, default | Meaning |
|---|---|---|
| `threshold` | number > 0, no longer required | the threshold of `threshold_method` `value` |
| `threshold_method` | choice `value`, `mean_annual_minimum`, `exceedance`; `value` | given; SNQ (SNW): the mean of the annual minima of the period, the `snx` of `stats characteristic`; the value of the duration curve of D7 at `exceedance_percent` (Q70, Q90) |
| `exceedance_percent` | number in (0, 100); 70 | for `exceedance` |
| `parameter` | choice `Q`, `H`; `Q` | with Q the deficits are also volumes in m³; with H (low-stage periods) they are not |
| `first_year`, `last_year` | integer | D1 |
| `min_duration_days`, `max_gap_days` | 5, 4 | unchanged: the author's 5 days and gaps under 4 days |

- The series may have missing values and missing dates (dates strictly increasing): it is laid on its
  calendar, a day without a value is never below the threshold, and runs merge across fewer than
  `max_gap_days` days of either kind, as the mockup's `merge_low_flow_events` does. The errors
  `missing_values` and `date_gap` go; a gapless series gives today's sequences.
- Result `hydrolog-stats-low-flow-sequences/1` (additive): `threshold_method`, `exceedance_percent`,
  `parameter`, `first_year`, `last_year`, `n_missing_days`, `total_deficit_volume_m3`; each sequence gains
  `missing_days`, `deficit_volume_m3` (deficit × 86,400 s; `null` for H), `hydrological_year` (of its
  start), `open_start`, `open_end`; `mean_flow` is the mean of its days with a value. `years`: each
  `{year, n_events, duration_days, max_duration_days, deficit, deficit_volume_m3, missing_days}`, an event
  counted in the year it starts (the mockup's summary). `n_days` counts the calendar days of the period.

### D7. `stats duration-curve` (new; Nogat H8)

| Option | Type, default | Meaning |
|---|---|---|
| series | the dated options | daily H or Q |
| `first_year`, `last_year` | integer | D1 |
| `month` | integer 1–12 | only the days of this calendar month (a curve per month) |
| `percents` | number list in (0, 100); 1, 5, 10, 30, 50, 70, 90, 95, 99 | exceedance percentages of the table |
| `class_method` | choice `width`, `log`; `width` | classes of equal width, or logarithmic classes |
| `class_width` | number > 0; 10 | in the unit of the series (10 cm for H) |
| `class_count` | integer ≥ 2; 40 | number of logarithmic classes between the smallest positive and the largest value (for Q) |

Result `hydrolog-stats-duration-curve/1`: `n_values`, `first_year`, `last_year`, `month`, `min`, `max`,
`mean`, `median`; `percents` and `values` (the table); `curve_percents` and `curve_values` (105 points
from 0.1 to 99.9 %); `class_method`, `class_width`, `class_count`; `classes` from the highest down, each
`{lower, upper, days, percent, days_with_higher, days_with_lower, months}` (`months`: the days of the class
in each hydrological month, XI to X); `modal_class` `{lower, upper, days, percent}`.

Method: the value equalled or exceeded on p % of the days, from the Weibull plotting position
p = m / (n + 1) of the values ranked from the highest, interpolated linearly between ranks and held at
the ends (Searcy, 1959, USGS Water-Supply Paper 1542-A; Vogel and Fennessey, 1994), the mockup's
`exceedance_values`. Classes of equal width are [k·w, (k + 1)·w), from the multiple of w at or below the
smallest value: the author's 10 cm table (`a10a0ec:code/hydro_stats.py:497-500`) with its cumulative days
„including higher” and „including lower”, the mockup's `class_month_table`. Logarithmic classes are the
mockup's `log_classes` (equal classes would put the mode of a skewed flow series in its lowest class). The
modal class is the most frequent, the lowest one on a tie, as in `hydrometrics water-level-zones`, which keeps its
classes from the floored smallest value; for Kłodzko's whole record both start at 30 cm.

### D8. `stats runoff-volume` (new; Nogat H17)

| Option | Type, default | Meaning |
|---|---|---|
| series | the dated options | daily Q [m³/s] |
| `first_year`, `last_year` | integer | D1 |
| `cumulative_year` | integer | the hydrological year of the cumulative curve; default the last complete year of the period |

Result `hydrolog-stats-runoff-volume/1`: `first_year`, `last_year`; `years`, each `{year, volume_m3,
days_with_data, days, complete, months}` with `months` in hydrological order XI–X, each `{month,
volume_m3, days_with_data, days}` (`volume_m3` `null` for a month without a value); `n_complete_years`,
`mean_annual_volume_m3` (of the complete years), `monthly_mean_volume_m3` (12, of the complete months);
`cumulative_year`, `cumulative_volume_m3` (each day of that year, a missing day adding nothing) and
`mean_cumulative_volume_m3` (365 days, the mean of the complete years' curves). Method: V = Σ Q · 86,400 s
over the days with a value; the author's daily volumes (`95ec3ea`) and the mockup's `runoff`.

### D9. IMGW-PIB's half-year extremes in the frequency commands (Nogat H4, F1)

- `stats flood-frequency`, `stats low-flow` and `stats homogeneity` gain `half_year_file` (as D3) and
  `parameter` (`Q`, `H`; `Q`): the annual maxima (`stats low-flow`: minima) are the larger of the winter
  and summer maxima (the smaller of the minima) of the years with both, with those years; a third `one_of`
  group. `first_year`, `last_year` choose the years.
- Results (additive): `source` (`daily`, `values` or `half_years`) and, for `half_years`, the
  `hydrological_years` from the file. The notices `short_record` and `small_sample` stay as they are.

### D10. `commands batch`: catalog calls of a JSON Lines file in one process (Nogat D6, H4)

| Option | Type, default | Meaning |
|---|---|---|
| `input_file` | path, required | JSON Lines, one call per line: `{"command": "<name or operation id>", "options": {...}}` |
| `output` | path, required | JSON Lines, line i the result of call i: its `hydrolog-result/1` envelope, or its `hydrolog-error/1` document |
| `check`, `force` | boolean | ADR-0003 |

- One process: each call runs through `run_command`, so a line equals the `--json` output of the same call
  run alone (the envelope; the error document as the CLI prints it). A failing call does not stop the
  batch. Paths of a call resolve against the directory of `input_file`; the path policy (MCP
  `--allow-dir`, writes) applies to every call. A line that is not a JSON object with `command` and
  `options`, `commands batch` itself and `gui serve` give that line a `validation_error` document.
- Result `hydrolog-commands-batch/1`: `n_calls`, `n_ok`, `n_failed`, `failed` (each `{line, command,
  code}`), `files`.
- Verified by a batch of 1,000 calls equal byte for byte to the same calls run singly, with the time of both.

### D11. Regime, seasonality, harmonics, trends, baseflow (Nogat H2)

| Command | Options (besides the dated series, `first_year`, `last_year`) | Result | Method |
|---|---|---|---|
| `stats regime` (new; H12) | none | `monthly_mean` (12, XI–X), `annual_mean`, `parde` (12), `regime_type` (`code`, `criteria`), `spring_share`, `seasonality_index` | Pardé's coefficients; Dynowska's (1997) types as Wrzesiński (2018) states their criteria (the mockup's `REGIME_RULE`, checked against both sources in S3); the March–April share of the annual volume; Walsh and Lawler (1981) |
| `stats seasonality` (new; H13) | `half_year_file`, `parameter`, `statistic` (`max`, `min`; `max`) | the dated annual extremes, `mean_day`, `mean_date`, `concentration`, `winter_share`, `summer_share` | circular statistics of the dates (Bayliss and Jones, 1993; Burn, 1997) |
| `stats harmonics` (new; H14, M12) | `harmonics` (1–4; 2) | `period` and `years`, each `{mean, harmonics: [{amplitude, phase_day, explained_variance}], r_squared, n_values}` | least squares on the day of the year, P = 365.25 d |
| `stats mann-kendall` (extended; H16, M13) | `years`, `year_column` | `sen_slope`, `sen_intercept`, `sen_slope_lower`, `sen_slope_upper` | Sen (1968), the intercept of Conover (1980), the 95 % interval of Gilbert (1987) |
| `stats baseflow` (new; H18) | `alpha` (0.925), `passes` (3), `series_year` | `bfi`, `years` (`{year, bfi, days, baseflow_mean, discharge_mean}`), `recession` (`k`, `half_life_days`, `segments`), the daily baseflow of `series_year` | Lyne and Hollick's filter on gapless spans of at least 60 days, reflected 30 days at each end (Nathan and McMahon, 1990; Ladson et al., 2013); k the median Q(t+1)/Q(t) of recessions of at least 5 days (Tallaksen, 1995) |

The water temperature days of H15 (≥ 15, 20, 25 °C, < 1 °C) are `stats threshold-events` on the series of
T, one call per level; the yearly maximum with its date is the first degree of D3 with `parameter` T.

### D12. Meteorological statistics: the group `meteo` (Nogat H3)

The series of a meteorological station come as Obserwator's daily export (`P`, `Tmax`, `Tmin`, `Tmean`,
`snow_cover`, `fresh_snow`); each command names its columns (`precipitation_column`,
`tmax_column`, …) or takes inline values with dates. Years are calendar years by default and hydrological
with `year_type` `hydrological`; `first_year`, `last_year` as D1.

| Command | `index` and options | Result | Method |
|---|---|---|---|
| `meteo precipitation` | `index`: `sums` (M1: year, half-year, season, month; the normal of the period and the anomaly in % of it), `maxima` (M2: the yearly and monthly largest daily sum and the largest sums of `durations_days`, default 2, 3, 5, 10, with dates), `days` (M5: days with P ≥ `thresholds_mm`, default 0.1, 1, 10, 20, per month and year), `intensity` (M4: the mean yearly sum, the mean sum of a wet day ≥ 1 mm), `heavy` (M7: the sums on days above the 95th and 99th percentiles of the wet days of the period), `seasonality` (M9: the monthly regime, the precipitation concentration index, the seasonality index) | `index`, the period, `years` (per year, by index) and `period` (the normal and the summary) | ETCCDI (Zhang et al., 2011) for `days`, `intensity`, `heavy`; Oliver (1980); Walsh and Lawler (1981) |
| `meteo spells` | `kind` (`dry`, `wet`; `dry`), `threshold_mm` (1.0) | the spells (`start_date`, `end_date`, `length_days`), per year the longest and the counts of at least 10, 15 and 20 days, the distribution of lengths | the run logic of D4 on P below (dry) or at least (wet) the threshold (M6) |
| `meteo spi` | `scales_months` (1, 3, 6, 12) | per month the SPI of each scale and Kaczorowska's class of the month and the year | gamma fit with the zero-precipitation mixture per calendar month (McKee et al., 1993; WMO, 2012, WMO-No. 1090); Kaczorowska (1962) (M8) |
| `meteo temperature` | `index`: `means` (monthly and yearly means and extremes, the normal and the anomaly), `days` (frost Tmin < 0, ice Tmax < 0, summer Tmax > 25, hot Tmax > 30 °C, tropical nights Tmin > 20 °C), `degree_days` (growing above 5 °C; heating 18 − Tmean on days with Tmean ≤ 15 °C, Eurostat's rule), `range` (the mean daily range) | per year and month, and `period` | ETCCDI (M11) |
| `meteo snow` | none | per winter (hydrological year): days with snow cover, the largest depth with its date, the first and the last day, the sum of fresh snow | M10 |
| `meteo hydrothermal` | none | Sielianinow's coefficient per month and season of the days with Tmean > 10 °C | M14; the source fixed in S4 |

The quantiles of the yearly precipitation maxima (M3) are `stats flood-frequency` on the values of
`meteo precipitation --index maxima`; the harmonics of temperature (M12) `stats harmonics`; the trends
(M13) `stats mann-kendall` with Sen's slope. The thresholds and bases are options with the defaults above;
S4 checks each against its source before its tests.

### D13. Common rules

- New result fields are optional in the schemas (`_ADDED_FIELDS` of `scripts/generate_result_schemas.py`);
  new documents are generated from the examples (AGI-4.1).
- New notice codes are in `NOTICES` and worded in Polish in `gui/web/src/labels/notices.js`.
- Every new or extended command has a catalog example that runs on `tests/fixtures`. The fixtures are
  synthetic series in the shape of Obserwator's exports (the daily file, the same for IMGW-PIB and ČHMÚ, and
  IMGW-PIB's half-year file), with gaps; IMGW-PIB's own data stay out of the repository until its terms are settled
  (Nogat's open question 4).
- The numbers of the mockup's prototypes are reproduced on Kłodzko's exported series by a check outside
  the repository (the demo store is not in the repository); its results go to Results below.
- Each step updates `docs/COMPUTATION_PATHS.md`, `docs/USAGE.md`, the CHANGELOG, `docs/PROGRESS.md`, the
  counts of commands (README, SCOPE, the GUI's test of „Wszystkie polecenia”), regenerates `AGENTS.md` and
  `llms.txt`, and records its ADR.

## Steps

Each branch starts from the previous one; each is gated (`scripts/gate.sh`) and committed; the merges wait
for the author.

| # | Nogat step | Branch | Content | Verified by |
|---|---|---|---|---|
| P | — | `plan/station-analyses` | this plan | — |
| S1 | H1 | `feature/station-hydro-analyses` | D1, D3 to D8; ADR-0029 | catalog examples; unit tests of each method against hand-computed series; the mockup's Kłodzko numbers reproduced |
| S2 | H4 | `feature/station-batch` | D9, D10; ADR-0030 | 1,000 calls in one batch equal the single calls; the half-year maxima equal the mockup's |
| S3 | H2 | `feature/station-regime` | D11; ADR-0031 | published worked examples of each method |
| S4 | H3 | `feature/station-meteo` | D12; ADR-0032 | hand-computed sequences; the ETCCDI counts of a fixture year |

## Risks

| Risk | Effect | Mitigation |
|---|---|---|
| `AGENTS.md` passes 16 KiB | the contract test fails | D2: measured per step; compact lines; Nogat's budget as the last resort |
| Methods without one standard (the regime type, SPI, the baseflow filter, the dry-day threshold) | numbers that differ from a reader's handbook | each method named with its source in the description and COMPUTATION_PATHS; checked in its step |
| A year with missing days in the second degree | a milder WWQ or NNQ | `incomplete_years` and the notice `years_with_missing_days`; the annual extremes of the frequency commands keep complete years only |
| `stats low-flow-sequences` accepts gaps it refused | a caller relying on the refusal | the result counts the missing days, each sequence its own |

## Not in this plan

Nogat's H5 („Wczytaj z Obserwatora” in Hydrolog's GUI); GUI panels for the new commands beyond their
generated forms in „Wszystkie polecenia”; IMGW-PIB's warning and alarm levels (answer 3); analyses across
stations; ČHMÚ's published rating curves, which Obserwator shows beside the fit.
