# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

First release of the stable API (1.0.0, not yet released; `develop` carries 1.0.0.dev0), made together with the adoption of the Nogat standard 1.0 (its drafts were called 2.0 and 2.1; decisions in [DECISIONS.md](DECISIONS.md)). From that version on semantic versioning applies: command and option names, `operation_id`s, the `hydrolog-result/1`, `hydrolog-error/1` and domain result schemas, and the error codes and exit codes are public API. The library classes (`SCSCN`, `HydrographGenerator`, `NashIUH`, `ClarkIUH`, `SnyderUH`, `ConcentrationTime`, hyetographs, `WatershedParameters`, statistics, hydrometrics, reports, visualization) keep their names and signatures; changes to them are additions or bug fixes described below. **Breaking** entries are relative to 0.7.0; the ones that also change the unreleased 1.0.0.dev0 of `develop` say so ("since 1.0.0.dev0").

### Added

#### Nogat's admin panel (Nogat DEV-15.13, ECO-067, kit 0.7.0; plan `2026-11-13-admin-panel`, step 2; ADR-0038)
- **Breaking for the admin page:** `admin/` is Nogat's kit panel `<nogat-admin>` (kit 0.7.0, copied byte for byte from Nogat `229ade3`: `nogat-admin.js` and `nogat-admin.css` are new) with „Zgłoszenia”, „Statystyki” and „Stan”; the Preact page (`admin/admin.js`, `admin/admin.css`, `src/labels/admin.js`) is gone. The key is kept in the tab under `hydrolog/admin-key/1` (was `hydrolog-gui/admin-key/1`), so the operator signs in once more.
- `GET api/admin/stats?from=&to=` answers `{days, totals}`: the lines of `<data_dir>/hydrolog/stats.jsonl` between two UTC days, both included (default the last 30 days), today's as counted so far, and the sums of every key but `visitors`; a day not `YYYY-MM-DD` or `from` after `to` is `validation_error`.
- `GET api/admin/status` answers `{app, version, started_at, uptime_s, data_dir, disk: {free_bytes, total_bytes}, checks}` with the checks `data_dir` (the data directory can be written) and `feedback_db` (the reports' file can be read, with its counts).
- **Breaking:** `PATCH api/admin/feedback/{id}` answers the report instead of `{"status": "ok"}`.
- `admin` answers `308` to `admin/` (was Starlette's `307`), every answer of `admin`, `admin/…` and `api/admin/…` has `Cache-Control: no-store`, and a public GUI counts the admin panel's requests in no daily total (they stay under the request limit).
- The sign-in is unchanged: `HYDROLOG_ADMIN_API_KEY` or `HYDROLOG_ADMIN_API_KEY_FILE`, read at every request, and `401 unauthorized` with `admin_key_not_configured`, `admin_key_missing` or `admin_key_invalid` on every admin route, `stats` and `status` included.

#### Nogat's logs in `gui serve` (Nogat DEV-12.4 to DEV-12.9, ECO-066; plan `2026-11-13-terms-fix`, step 4; ADR-0037)
- `hydrolog gui serve` keeps an access, an application and a lifecycle log in every run, public or not, as JSON Lines of `nogat-log/1` in `<state_dir>/hydrolog/logs/<kind>-YYYY-MM-DD.jsonl` (UTC dates), and deletes each file itself 14 days after its date, at the start and at every midnight UTC: Nogat's reference module, copied byte for byte into `src/hydrolog/gui/nogat_logging.py` from Nogat `a41d971`, and its schema into `schemas/nogat/record-1.schema.json`.
- The access log: one record per request (`method`, `path` with its query, the values of personal or secret parameters dropped, `status`, `bytes`, `duration_ms`, `agent` the kind of client, a random `request_id`), the request limit's `429` included; the page's files and the catalog documents are logged only when answered with 400 or more. No log holds an IP address, a cookie or the `User-Agent`.
- Standard error, and so the journal of a service, gets only the records `start` (with `url` and `public`), `stop` and `prune`, and errors reduced to their type; the README gives the `jq` command that reads the logs.
- A new setting `state_dir` (`HYDROLOG_STATE_DIR`, `NOGAT_STATE_DIR`, `[hydrolog]` or `[nogat] state_dir`; default the user state directory of `nogat`, `~/.local/state/nogat` on Linux); `config show` reports six settings.
- `create_app(log=...)` takes a `ServerLog` and then logs the app's requests as its outermost middleware; without it (a host's mount) the app logs none.

#### The GUI: the results of the station analyses in „Wszystkie polecenia”
- Every scalar, object and series of the results of the station commands (`stats` of steps S1 to S3, `hydrometrics rating-curve`, `stats mann-kendall`, the `meteo` group) has a Polish label (about 160 new ones; per command where one name means two things, `commandResultFields`), with units the field names do not give: `m³/s` of the regime's means and the rating curve's residuals, the series' unit (`m³/s`, `cm`, `°C` by `parameter`) of the characteristic values and of the low-flow threshold and deficit, `°C·d` of the degree days, none for `var_s` and the counts of spells. A contract test keeps every field of the commands' example results labelled.
- Their tiles show each command's key figures, by `index` for `meteo precipitation` and `meteo temperature`: e.g. `stats regime` the regime type (its code and name, „4 niwalno-pluwialny”), the share of March and April, the seasonality index and the mean flow; `stats characteristic` names its tiles with its own symbols (WWQ, SWQ, SNQ, SSQ); a tile may hold a short text (`mean_date` of `stats seasonality`), and three tiles give the last one the empty fourth column.
- The charts draw months, years, exceedance percentages, durations, thresholds and percentiles as the x axis, never as a series: the months as named ticks in the result's order (November to October in a hydrological year; also the mean monthly volumes of `stats runoff-volume` and the monthly normals of `meteo spi`), the days of a hydrological year for the cumulative volumes and the baseflow, `hydrological_years` for the annual values; lists of other years (`incomplete_years`) are not drawn. The panel's chart of `stats regime` shows Pardé's coefficients, that of the heavy precipitation its thresholds (one unit on the axis). Charts take named ticks (`x.labels`).

#### The GUI: one strip of the providers' lines per view (Nogat DEV-20.5, ECO-064, kit 0.5.1; ADR-0035)
- Each section's view shows the providers' lines of its data once, in Nogat's `<nogat-sources>` under the centre: 12 px, the short lines only (IMGW-PIB's source and „przetworzone”, PMAXTP's two, ČHMÚ's „Źródło: ČHMÚ, CC BY 4.0”) and „Źródła i warunki”, which opens a dialog with every line, the terms notice and, on a public GUI, „Regulamin serwisu”. The part „Źródła danych” under the charts and at the end of „Wyniki”, and the lines under a PMAXTP depth and in a received hand-off's card, are no longer on screen: a view of Hydrogram zlewni with a PMAXTP depth goes from 56 lines in three blocks to 4 lines at 1440 px (54 to 6 at 390 px). They still print in full, as before; the CSV, JSON, PNG, report and hand-off are unchanged.
- The welcome dialog lists the lines of the data the page shows (the kit's `fillSources`), and nothing on a first visit with every section empty.
- The guide: „Źródła danych” and the step „Hietogram” describe the strip, its dialog and the welcome; the pictures `ekran.png`, `hydrogram.png` and `eksport.png` are retaken.
- Nogat's GUI kit 0.5.1 (copied byte for byte from Nogat `9940bb8`): `nogat-sources.js` and `.css` are new, and the regulamin's links of the app menu and the sources dialog open a new tab; the footer's „Regulamin” on the guide's page opens a new tab too (DEV-15.7).

#### The GUI's guide: „Analiza szeregów stacji” (Nogat steps H1 to H4; ADR-0029 to ADR-0033)
- A new chapter 07 of `instrukcja/` (chapters 07 to 10 become 08 to 11): the input of the station analyses (Obserwator's daily export, IMGW-PIB's half-year file, Archiwista's hand-off in „Statystyka przepływów”), what each command of `stats`, `hydrometrics rating-curve` and `meteo` computes, `commands batch` left out of the GUI, the defaults (the whole record, the 30-year notice, the reference period of normals, missing days), the methods' sources by name, and a worked example: `stats regime` of the synthetic station `przyklady/stacja.csv` (the fixture `station_daily.csv`), whose numbers the browser smoke test compares with the page.

#### A public web GUI: the regulamin, the request limit, the access log, daily totals, „Zgłoś uwagę” without contact, sessions without a cookie (Nogat plan `2026-11-13-gui-terms`, step 4; DEV-15.7 to DEV-15.12; ADR-0034)
With `[nogat.operator]` in `nogat.toml` the GUI is public and keeps Nogat's rules; without it (a local run) nothing below applies but the feedback form and the sessions.
- The regulamin of Nogat's GUI kit 0.4.0 (copied byte for byte from Nogat `2b513d0` into `web/nogat/`), filled at the start with the blocks of PMAXTP, IMGW-PIB and ČHMÚ, served at `regulamin.html`; every view shows at its foot the statement „Serwis jest niekomercyjny i bezpłatny…” and „Regulamin”, the menu „Aplikacje” ends with it, and the guide shows the same footer (`GET api/terms`).
- A request limit per client address, `request_limit` in `request_window` seconds (new settings, default 300 and 60; `HYDROLOG_REQUEST_LIMIT`, `NOGAT_REQUEST_LIMIT`, `HYDROLOG_REQUEST_WINDOW`, `NOGAT_REQUEST_WINDOW`, `[hydrolog]`, `[nogat]`; `config show` reports them), static files and catalog documents not counted; over it `429` with `Retry-After`, the error `rate_limited` or a Polish page.
- An access log without the client's address, one JSON line per request on standard error (`time`, `request_id`, `method`, `path`, `status`, `size`, `duration_ms`, `user_agent`), and the answer's `X-Request-Id`; replaced before any release by Nogat's logs (ADR-0037, above).
- Daily totals in `<data_dir>/hydrolog/stats.jsonl`: `visitors` (distinct salted hashes in memory only), `page_views`, `stations_opened`, `analyses_run`, `downloads`; the page sends `POST api/stats/station` and `POST api/stats/download`.

#### Review of the station analyses: one name per concept, reference periods of normals, Mann–Kendall ties (the author's request of 2026-11-13; plan `docs/plans/2026-11-13-station-analyses.md`, Results; ADR-0033)
The commands of steps S1 to S4 checked option by option against the catalog that `develop` (`48358a5`) deploys, and the three methodological questions S4 left open settled. The renamed options and fields were never released; the catalog keeps 62 commands in 17 groups.
- One name per concept (AGI-1.2, DEV-8.2). `stats threshold-events`: the option and the result field `threshold` (was `level`; CLI `--threshold`), the name `stats low-flow-sequences` has for the same method. `stats duration-curve`: the options and result fields `exceedance_percents` (was `percents`), `bin_method`, `bin_width`, `bin_count` (were `class_method`, `class_width`, `class_count`), the result's `curve_exceedance_percents` (was `curve_percents`) and `share_percent` of each class and of `modal_class` (was `percent`). `stats seasonality`: the dated extremes are `years` (was `extremes`). `stats baseflow`: `n_values` (was `days`, also of each year), `n_spans` (was `spans`), `recession.n_segments` (was `segments`). `meteo spells`: a spell's `duration_days` (was `length_days`), `max_duration_days` of the period and of each year (were `max_length_days`, `longest_days`), each year's `max_start_date`, `max_end_date` (were `longest_start_date`, `longest_end_date`), the period's `n_years` and `mean_max_duration_days` (were `complete_years`, `mean_longest_days`). `meteo snow`: `period.incomplete_years` (was `skipped_years`). `meteo spi`: each month gives `year` (of `year_type`) and `month` (1–12) as integers instead of a `"YYYY-MM"` string in `month`. Percent options declare the unit `%`.
- Variant options, as in `precip areal`, `precip hietogram` and `hydrograph generate`: an option of one value of `index`, `bin_method` or `threshold_method` has no catalog default (its description names the default the command fills) and is `validation_error` `not_applicable` with another value. `meteo precipitation`: `durations_days` (`maxima`), `thresholds_mm` (`days`), `wet_day_mm` (`intensity`, `heavy`), `percentiles` (`heavy`); `meteo temperature`: `frost_tmin_c`, `ice_tmax_c`, `summer_tmax_c`, `hot_tmax_c`, `tropical_tmin_c` (`days`), `growing_base_c`, `heating_base_c`, `heating_limit_c` (`degree_days`); `stats duration-curve`: `bin_width` (`width`), `bin_count` (`log`); `stats low-flow-sequences`: `exceedance_percent` (`exceedance`), and `threshold` with a threshold from the series is `not_applicable` (was `conflict`).
- The reference period of normals: `meteo precipitation` (`index` `sums`, `heavy`, `seasonality`), `meteo spi` and `meteo temperature` (`index` `means`) take `reference_first_year` and `reference_last_year`, years of `year_type`, by default the analysed period, so a call without them gives the numbers it gave; their results name `reference_first_year`, `reference_last_year` and `reference_period_years`. The analysed years keep their own values (the sums and means, the SPI's sums, R95p and R99p); the reference period, from its own days, gives the baselines: the normals and with them `percent_of_normal`, `anomaly_c`, the classes of relative precipitation and the regime of `seasonality` (WMO-No. 1203, 2017: normals as the benchmark of anomalies, the climatological standard normal 1991–2020 and the reference normal 1961–1990, a normal from 80 % of the reference period's years), the wet-day percentiles of R95p and R99p (the base period of the ETCCDI: Zhang et al., 2011; Klein Tank, Zwiers and Zhang, 2009) and the gamma fits of the SPI (WMO-No. 1090, 2012; McKee et al., 1993; the Copernicus European Drought Observatory calibrates on 1991–2020); `period.normal_years` and the `wet_days` of `heavy` count the reference period. A reference period under 30 years gets its own `short_reference_period`; another index refuses the options (`not_applicable`); `reference_first_year` after `reference_last_year` is `validation_error` `range`, a reference period without a value `calculation_error` `no_values_in_period`.
- Exact sums: every sum of daily precipitation in `meteo` (of months, half-years, seasons and years, the SPI's k-month sums, the heavy and wet-day totals, the hydrothermal sums) is rounded to 1e-6 mm, as the window sums of `maxima` were, so a sum of 0.1-mm data is the number nearest its decimal value (622.0, not 621.9999999999999) and equal sums are equal.
- `stats mann-kendall` (also `develop`'s users): the variance of S is corrected for groups of tied values, Var(S) = [n(n − 1)(2n + 5) − Σ t(t − 1)(2t + 5)] / 18 (Kendall, 1975; Hirsch, Slack and Smith, 1982; Gilbert, 1987, Eq. 16.3), and Sen's interval is built on it. A series with equal values gets a smaller `var_s`, so `z_score` grows in absolute value, `p_value` falls and `trend_detected` and `trend_direction` can change for a series near `alpha`; `s_statistic`, the schema and a series without ties are unchanged. With the exact sums, the annual precipitation sums give the mockup's S, Z and p (Kraków 1961–2025: S 47, was 46, p 0.7945; Praha 1805–2025: S −340, was −345, p 0.7561); Gilbert's Exercise 16.1 (Var(S) 43.3, Z 1.67) and Example 16.2's tie groups (Var(S) 1227.33) are reproduced.
- `meteo spells`: `min_duration_days` (1 by default), the shortest spell listed in `spells`; the yearly and period summaries always count every spell (the ETCCDI's CDD and CWD have no minimum duration), so `n_spells` and `max_duration_days` describe all spells. A long record's list shrinks with it: Kraków's dry spells at 1 mm, 3,859 in 1961–2025, are 388 of at least 10 days (about 60,000 instead of 470,000 characters of JSON).
- `commands batch` runs offline and writes only its output: a line that calls `precip pmaxtp` or gives an output option (`output`, `output_dir`, `schematic`) gets `validation_error` `not_in_batch`, as `commands batch` and `gui serve` did, so the batch's `effects` (no network, one `output`), its MCP annotations and its `--check` plan are true.
- The GUI: every option of the 58 commands of „Wszystkie polecenia” has a Polish label (51 new shared labels; per command where one name means two things: `threshold` of `stats threshold-events`, `precipitation_mm` of the `meteo` commands, `alpha` of `stats baseflow`, `parameter` of the frequency commands, the winters of `meteo snow`), the `one_of` groups of the new `stats` commands have names (the third „Plik półroczny IMGW-PIB”), the units `cm` and `°C` and the suffixes `_percent`, `_cm` and `_c` are shown; a contract test keeps every option labelled. The result view takes a command's own label first too (the `threshold` of `stats threshold-events` reads „Poziom progowy”, that of `stats low-flow-sequences` „Próg niżówkowy”). The guide's picture of „Wszystkie polecenia” (`polecenia.png`) is taken again with the 58 commands.
- Library: `threshold_events(threshold=...)`, `duration_curve(exceedance_percents=..., bin_method=..., bin_width=..., bin_count=...)` and `precipitation_spells(min_duration_days=...)`; `precipitation_sums`, `heavy_precipitation`, `precipitation_seasonality`, `standardized_precipitation_index` and `temperature_means` take the whole record with `first_year`, `last_year`, `reference_first_year` and `reference_last_year` (`standardized_precipitation_index` refuses negative precipitation, as `precipitation_sums` does); the result classes carry the new names; `mann_kendall_test` corrects Var(S) for ties.

#### Meteorological statistics of a station: the group `meteo` (plan `docs/plans/2026-11-13-station-analyses.md`, step S4; ADR-0032)
The meteorological statistics that Obserwator stores and serves (Nogat's plan of 2026-11-12, step H3), from a weather station's daily export of IMGW-PIB or ČHMÚ; the numbers of Obserwator's GUI mockup are reproduced on Kraków and Praha-Klementinum to its rounding. The catalog has 62 commands in 17 groups.
- `meteo precipitation` (new), one `index` per call: `sums` (months, half-years, seasons, years, the normals of the period and each sum in % of its normal), `maxima` (the largest 1-day and `durations_days` sums with dates, yearly and monthly), `days` (days with P at or above `thresholds_mm`), `intensity` (SDII), `heavy` (R95pTOT, R99pTOT), `seasonality` (the monthly regime, PCI, SI).
- `meteo spells` (new): the dry or wet spells (`kind`) below or at least `threshold_mm` (1 mm), each spell, per year the longest and the spells of at least 10, 15 and 20 days, the distribution of durations.
- `meteo spi` (new): the SPI of `scales_months` (1, 3, 6, 12; a gamma distribution with the probability of zero per calendar month, Thom's estimates) and the precipitation of each month and year in % of its normal with its class (years by Kaczorowska, 1962; months by the monthly limits, Tomaszewska, 1994).
- `meteo temperature` (new), one `index` per call: `means` (monthly and annual means of Tmean, Tmax, Tmin, the normal and the anomaly, extremes with dates), `days` (frost, ice, summer and hot days, tropical nights), `degree_days` (growing above 5 °C, heating by Eurostat's rule), `range` (the mean daily range); thresholds and bases are options.
- `meteo snow` (new): per winter (the season August to July, named after the hydrological year it ends in) the days with snow cover, the largest depth with its date, the first and the last day with cover and the fresh snow.
- `meteo hydrothermal` (new): Sielianinov's coefficient of the months April to September and of the days with Tmean above 10 °C of each year, with the nine classes of Skowera and Puła (2004).
- All six: the export's columns by name (`P`, `P_flag`, `Tmax`, `Tmin`, `Tmean`, `snow_cover`, `fresh_snow`, each changed by its `*_column` option) or inline values with `dates`; `year_type` (`calendar` or `hydrological`) and `first_year`, `last_year`; missing days by WMO-No. 1203; IMGW-PIB's accumulated totals (`P_flag` `accumulated`) stand for the missing days before them in the monthly sums; `attribution` and the lines of an Obserwator export in the envelope (ADR-0028).
- Notices `normal_not_computed` (warning), `accumulated_totals` (info) and `spi_not_fitted` (warning). The English text of `short_reference_period` says „year(s)” instead of „hydrological year(s)”.
- `AGENTS.md`: the groups `tc`, `hydrometrics` and `meteo` have one index line each, as `route` and `stats` (ADR-0032 amends ADR-0009).
- Library: `hydrolog.statistics` gains `precipitation_sums`, `precipitation_maxima`, `precipitation_days`, `precipitation_intensity`, `heavy_precipitation`, `precipitation_seasonality`, `precipitation_concentration_index`, `pci_class`, `si_class`, `precipitation_spells`, `fit_gamma`, `spi_values`, `standardized_precipitation_index`, `month_precipitation_class`, `year_precipitation_class`, `temperature_means`, `temperature_days`, `degree_days`, `temperature_range`, `snow_cover`, `hydrothermal_coefficient`, `sielianinov_class` and their result classes; `hydrolog.operations` the six `meteo_*` functions.

#### Regime, seasonality, harmonics, Sen's slope and baseflow (plan `docs/plans/2026-11-13-station-analyses.md`, step S3; ADR-0031)
The regime statistics of a station that Obserwator stores and serves (Nogat's plan of 2026-11-12, step H2), each method checked against a published example where one exists; the numbers of Obserwator's GUI mockup are reproduced on Kłodzko's and Słupsk's series, except the baseflow filter and Sen's intercept and interval, which follow their sources. The catalog has 56 commands in 16 groups.
- `stats regime` (new): the mean flow of each month (November to October) and the annual mean, Pardé's coefficients, Dynowska's (1997) regime type 1 to 5 by the criteria Wrzesiński (2018) quotes (`regime_type.code` and `criteria`), the March–April share of the annual volume and Walsh and Lawler's (1981) seasonality index.
- `stats seasonality` (new): the dates of the annual maxima (`statistic` `max`) or minima of the complete hydrological years of a daily series or of IMGW-PIB's half-year file (`half_year_file`, `parameter` Q, H or T), their mean date (`mean_day`, `mean_date`), concentration and the shares of the winter and summer half-years (Bayliss and Jones, 1993; Burn, 1997).
- `stats harmonics` (new): the mean and 1 to 4 harmonics (period 365.25 d) of the annual cycle of a daily series, over the period and in each hydrological year with at least 300 values: amplitude, day of the first maximum (1 = 1 November) and explained variance; for water or air temperature or flow.
- `stats mann-kendall`: `years` and `year_column`; Sen's slope (`sen_slope`), Conover's intercept (`sen_intercept`) and Gilbert's interval of the slope at 1 − `alpha` (`sen_slope_lower`, `sen_slope_upper`), per year with years, otherwise per step.
- `stats baseflow` (new): Lyne and Hollick's filter in the standard of Ladson et al. (2013) (`alpha` 0.925, `passes` 3, on each gapless span of at least 60 days, reflected by 30 days at each end), the baseflow index of the period and of each year, the recession constant k with its half-life (Tallaksen, 1995) and the daily baseflow of `series_year` (by default the last complete year).
- Notices `short_years_left_out` (info: years with fewer than 300 days left out of the yearly values) and `undated_extremes` (warning: half-year extremes without a date).
- The four new commands take `attribution` and carry the lines of an Obserwator export into the envelope (ADR-0028).
- The days of water temperature at or above 15, 20 and 25 °C and below 1 °C are `stats threshold-events` on T (`docs/USAGE.md`).
- Library: `hydrolog.statistics` gains `flow_regime`, `dynowska_regime_type`, `seasonality_index`, `FlowRegime`, `RegimeType`, `RegimeCriteria`; `extreme_seasonality`, `daily_extremes`, `half_year_extremes`, `circular_mean_date`, `ExtremeSeasonality`, `DatedExtreme`, `CircularMean`; `annual_cycle`, `harmonic_fit`, `AnnualCycle`, `HarmonicFit`, `HarmonicYear`, `Harmonic`; `baseflow_separation`, `lyne_hollick_filter`, `recession_constant`, `BaseflowSeparation`, `BaseflowYear`, `RecessionConstant`; `sen_slope`, `SenSlope`. `mann_kendall_test` takes `times` and raises for a value that is not finite.

#### The batch and IMGW-PIB's half-years in the frequency commands (plan `docs/plans/2026-11-13-station-analyses.md`, step S2; ADR-0030)
One process computes a whole station's analyses (Nogat's plan of 2026-11-12, step H4). The catalog has 52 commands in 16 groups.
- `commands batch` (new): runs the catalog calls of a JSON Lines file (`{"command", "options"}` per line) in one process and writes line i of `output` for call i: the call's `hydrolog-result/1` envelope or its `hydrolog-error/1` document, the very line that `--json` prints for the call alone. A failed call does not stop the batch; relative paths are taken from the directory of `input_file`; the path policy of the batch (MCP's `--allow-dir`) covers every call; `check` and `force` as for every writing command. Result `hydrolog-commands-batch/1`: `n_calls`, `n_ok`, `n_failed`, `failed`. The GUI does not offer it.
- The envelope: `items` (`{id, status, code?, reason?, message?}`) for a batch, whose `status` is `partial` when some calls failed and `failed` when all did; the CLI then exits with 10 or 11 and prints the envelope (the outcomes of the Nogat standard). Every other command keeps `status` `ok`.
- `stats flood-frequency`, `stats low-flow`, `stats homogeneity`: `half_year_file` (Obserwator's export of IMGW-PIB's half-year characteristics), `parameter` (`Q`, `H`) and `first_year`, `last_year`; the annual maximum (minimum) is the larger (smaller) of the half-year values of a year with both, a year with one only is left out and named in `incomplete_years`. The results gain `source` (`daily`, `values`, `half_years`) and, for homogeneity, `hydrological_years`.
- The providers' lines (ADR-0028): each line of a batch's output carries the lines of its own call, the batch's envelope the union of them; the lines of IMGW-PIB's half-year file reach the results of the frequency commands.
- Library: `hydrolog.statistics.annual_extremes_from_half_years`, `HalfYearExtremes`, `fit_fisher_tippett_minima`; `hydrolog.catalog.inputs.read_json_lines`; `hydrolog.catalog.dispatch.call_allowed_dirs`.

#### Station analyses for Obserwator (plan `docs/plans/2026-11-13-station-analyses.md`, step S1; ADR-0029)
The hydrological analyses that Obserwator stores and serves (Nogat's plan of 2026-11-12, step H1), computed by Hydrolog's catalog; the numbers of Obserwator's GUI mockup are reproduced on Kłodzko's series. The catalog has 51 commands in 16 groups.
- The reference period of a daily series: `first_year` and `last_year` (hydrological years, the whole record by default); results name the period and add the notice `short_reference_period` (info) under 30 years; a period without a value is `calculation_error` `no_values_in_period`.
- `stats characteristic`: the first degree of each hydrological year and half-year (`years`, with the dates of the extremes and the days with data), the second degree of each half-year (`winter`, `summer`), the Polish names (`labels`: WWQ…NNQ, WWW…NNW for the stage, WWT…NNT; `first_degree_labels`), `parameter` T, `source`, `first_year`, `last_year`, `incomplete_years` and the notice `years_with_missing_days`; `half_year_file` reads Obserwator's export of IMGW-PIB's half-year characteristics (`pl.imgw.hydro_semiannual`), the annual maximum being the larger of the half-year maxima. The top-level values are unchanged.
- `stats threshold-events` (new): the events and the days at or above (below) a `threshold`, per hydrological year, with start, end, duration and peak.
- `stats duration-curve` (new): the duration curve (Weibull positions) and its table, the classes of equal width or logarithmic with the days including higher and lower, split by hydrological month, and the modal class.
- `stats runoff-volume` (new): the runoff volumes of hydrological years and months [m³], their means over complete years and months, and the cumulative volume of a year beside the mean one.
- `stats low-flow-sequences`: gaps in the record are allowed (the errors `missing_values` and `date_gap` are gone), `threshold_method` (`value`, `mean_annual_minimum` for SNQ, `exceedance` with `exceedance_percent` for Q70 or Q90), `parameter` (`Q` gives the deficits in m³), `first_year`, `last_year`, `missing_days`, `deficit_volume_m3`, `open_start`, `open_end` of each sequence and a summary per hydrological year (`years`); `threshold` is optional.
- `hydrometrics rating-curve`: `dates`, `date_column`, `first_year`, `last_year` and `years_per_period` (the curves of successive periods, read at the median level and discharge); the result gains `first_year`, `last_year`, `periods`, `reference_level` and `reference_discharge_m3s`.
- The providers' lines (ADR-0028): the three new commands take the option `attribution`, and the lines of an Obserwator export or of IMGW-PIB's half-year file reach the result's `attribution` and `terms_notice`, as for every `stats` command.
- Library: `hydrolog.statistics` gains `threshold_runs`, `threshold_events`, `duration_curve`, `exceedance_values`, `runoff_volumes`, `characteristic_values_from_half_years`, `HalfYearValues` and the first-degree classes; `LowFlowAnalysis.detect_sequences` works on the calendar of the dates, across missing values and absent dates (`LowFlowSequence.missing_days`, `open_start`, `open_end`); `hydrolog.catalog.inputs.load_half_years` and `parse_dates`.

#### The providers' lines in every product (ADR-0028, Nogat DEV §20)
The terms of IMGW-PIB, of the PMAXTP project and of ČHMÚ's licence (CC BY 4.0) bind every product made with their data; the lines are Nogat's, verbatim, from one module (`hydrolog._attribution`).
- The envelope `hydrolog-result/1` gains `attribution` and `terms_notice` (arrays of strings, after `result`, only for a run with a provider's data): the source and processed-data lines (IMGW-PIB S and P, hydro.imgw.pl H, PMAXTP PS, PP and the monograph M, ČHMÚ C and CP) and the notice of IMGW-PIB's terms of use with the address of each terms that apply.
- Hydrolog finds the lines in its input files: the CSV columns `attribution` and `terms_notice` and Obserwator's `attribution_source` and `attribution_processed`, now left out of the data (an Obserwator export's lines reach the result of every `stats` and `hydrometrics` command), and the fields `attribution` and `terms_notice` of a JSON document; `hydrolog-network/1` accepts them at its top.
- New option `attribution` (a JSON array on the command line) of `precip hietogram`, `precip areal`, `scs effective`, `hydrograph generate`, `report generate`, the routing `route` commands, every `stats` and both `hydrometrics` commands: the lines of data given inline (a PMAXTP depth as `total_mm`, a handed-off series); the command completes them.
- Files: the tables of `route * --output` and `route network --output-dir` get the trailing columns `attribution` and `terms_notice`; `route network --output-dir` writes `ATTRIBUTION.txt` (merged with one already there, in `result.files`); the `--schematic` SVG draws the lines under its legend; `report generate` ends with „Źródła danych”.
- The CLI prints „Źródła danych” („Data sources”) with the lines; the MCP instructions and the notice `pmaxtp_attribution` say to show them and pass them on; `GET api/session` of the GUI gains `attribution`, each provider's lines.
- The web GUI shows the lines and the terms notice under every result with a provider's data and carries them into its CSV, JSON, PNG, print, report and hand-off exports; `nogat-handoff/1` is copied again from Nogat (`edd559b`, the optional `attribution` and `terms_notice`) and read and written with them.

#### Command catalog (`hydrolog.catalog`) and operations layer (`hydrolog.operations`)
A single source of truth for the library, the CLI, the MCP server and the agent guides: 44 commands in 15 groups (`tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `route`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `config`, `commands`); list: `hydrolog commands list`.
- `Command` and `Option`: English texts with the Polish translation next to them (`summary_pl`, `description_pl`, `rules_pl`; serialized under `i18n.pl`), units, ranges, `one_of` groups, a meaning for every value of a choice, examples with a result, derived `effects`, `check` and `families` (the group, plus `core` for the ten main commands); the declaration checks itself at import (summary at most 100 characters, summary + description + rules at most 600) (ADR-0001). `data_commands()`, `get_command()`, `catalog_document()`, `input_schema()`, `capture_warnings()`.
- `hydrolog.operations`: one public, typed function per command (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...); it returns a result object with `to_dict()`/`to_json()` or an `OperationOutput` (result, notices, written files).
- The `hydrolog-result/1` result envelope: `schema`, `tool`, `version`, `command`, `check`, `status`, `result`, `notices` (`level`, `code`, `message`), `inputs` and, for lists, `page` (ADR-0002); `commands list` and `commands schema` page with `--limit` and `--cursor`.
- The `hydrolog-error/1` error document and the closed `ERROR_CODES` registry (see "Error registry and exit codes" below); `HydrologError` has `code`, `details` and `hint`.
- New exception classes: `InputDataError`, `MissingDependencyError`, `ForbiddenPathError`, `NotFoundError`, `OutputError`, `ConflictError` (exported from `hydrolog`).

#### Result serialization (`hydrolog._serialization`)
- `JsonResultMixin` with `to_dict()` and `to_json()` in all result classes (runoff, precipitation, morphometry, network, statistics, hydrometrics, soil); `NaN` and infinities become `null`, NumPy arrays become lists, an unknown type raises `TypeError`. `WatershedParameters.to_dict()`/`to_json()` are unchanged.

#### File inputs
- Series (`input_file` + `value_column`/`date_column`), rainfall stations (`stations_file`), network segments (`segments_file`) and watersheds (`watershed_file`) as CSV (comma or semicolon, UTF-8) or JSON; columns are selected by exact name or without the unit suffix (`Q` finds `Q [m3/s]`).
- An Obserwator (formerly IMGWTools) series export (`export_series` CSV) is read without preprocessing; `WatershedParameters` JSON is the proposed `catchment_characteristics` format in Retman.

#### `hydrolog.soil` - Hydrologic soil groups (HSG)
Rules moved from Kartograf 0.8.0 (`kartograf.hydrology.hsg`, Kartograf ADR-025); Kartograf stays responsible for downloading rasters (`download_soil`).
- `texture`: USDA texture classification (12 classes) from clay, sand and silt content (`classify_usda_texture`, `classify_usda_texture_array`), `TEXTURE_TO_HSG`, `texture_to_hsg` (NumPy only).
- `hsg`: `classify_hsg`, `hsg_statistics_array`, `HsgStatistics`, `HSG_CODES` (`uint8` GeoTIFF: 0 - no data, 1-4 are A-D).
- `raster` (`hydrolog[raster]` extra: `rasterio>=1.3`, `pyproj>=3.6`): `hsg_from_rasters()` (clay, sand and silt rasters → HSG GeoTIFF) and `hsg_statistics()` (group areas, optionally within a `bbox` rectangle).
- Commands `soil texture`, `soil hsg`, `soil hsg-stats`.

#### MCP server (`hydrolog mcp`, `hydrolog-mcp`) (ADR-0006)
- The `hydrolog[mcp]` extra (`mcp>=2.3,<3`): every catalog command is a tool (name = `operation_id`, prefixed `hydrolog_`, e.g. `hydrolog_tc_kirpich`), `structuredContent` = the result envelope, an error is returned as `isError` with `hydrolog-error/1`.
- `hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]` and the console script `hydrolog-mcp` (the same server). Without `--allow-dir`, commands with path-type options end with `forbidden`. The server starts read-only: without `--allow-writes` the writing tools (`report generate`, `soil hsg`, `commands guide`) only plan (`check`) and report `readOnlyHint: true`; with it they write only inside `--allow-dir` directories. `--tools` selects families (a command group name or `core`).
- Conformance: tool annotations (`title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`), `outputSchema` (the result envelope), `inputSchema` in JSON Schema 2020-12 without a top-level `oneOf`, server instructions of at most 4,096 characters and tool descriptions of at most 600; start and `tools/list` import no numerical library. The server output is always English: it has no `--lang` option, and an explicit `--lang` when the server starts (`hydrolog mcp --lang en`, `hydrolog-mcp --lang en`) is rejected with `validation_error` (exit 2, `details.reason` = `ineffective_option`); `--lang` still selects the language of `hydrolog mcp --help`.

#### Agent guides
- `AGENTS.md` and `llms.txt` in the repository (English), generated from the catalog by `hydrolog commands guide --format agents|llms|agents-md-block [--output FILE] [--inject FILE] [--force] [--check]`; `--inject` replaces the Hydrolog block between its markers in a consumer's `AGENTS.md` (idempotent); a test compares the bytes with the generator (`hydrolog.agent_guide`).

#### Other additions
- `hydrolog.hydrometrics.RatingCurveFitError`.
- `pyproject.toml`: extras `raster`, `mcp`, `viz`, `all`; guide templates and result schemas in the package (`package-data`); `platformdirs` as the only new runtime dependency; `jsonschema` in the `dev` dependencies.
- `WatershedParameters.tc_parameters(method)`: the concentration-time formula arguments that `calculate_tc()` derives from the watershed fields (`calculate_tc` is the formula applied to `tc_parameters`); this is the source of `parameters` in the `tc watershed` result.
- `LowFlowAnalysis.empirical_non_exceedance(method)` and `LowFlowEmpiricalFrequency` (`values_ascending`, `non_exceedance_probabilities`, `return_periods`; exported from `hydrolog.statistics`).
- The `incomplete_years` result field in `stats flood-frequency` (list of years; `null` for maxima given without dates) and `stats low-flow` (list of years), and the `incomplete_years` notice.

#### Writing commands: `--output`, `--force`, `--check` (ADR-0003)
- `report generate`, `soil hsg` and `commands guide` write exactly one plain file given by `--output`; an existing file is replaced only with `--force` (otherwise exit 4, `conflict`, `details.reason = output_exists`, `details.paths`, before anything is computed); `--check` returns the plan (`hydrolog-plan/1`: `result.targets[]` with `option`, `path`, `action` = `write` | `replace` | `conflict`) without effects. The files written are `result.files[]` = `{path, size_bytes, sha256, status}`, `status` `written` | `replaced`. Hydrolog has no store and downloads nothing but the PMAXTP depth of `precip pmaxtp` (below): inputs come from files written by Kartograf (`soil download --output-dir`) and Obserwator (`series export --output`).

#### Settings and `config show` (ADR-0004)
- `hydrolog._settings`: three settings, `lang` (default `pl`), `log_level` (default `warning`) and `data_dir` (default the user data directory of `nogat`; see „Zgłoś uwagę” below); precedence option > `HYDROLOG_<KEY>` > `NOGAT_<KEY>` > `[hydrolog]`, then `[nogat]` in `nogat.toml` (`NOGAT_CONFIG`, else the user config directory) > default; a broken or non-UTF-8 file is ignored.
- `hydrolog config show [--json]` (also an MCP tool and a Python function) prints each setting with its source (option, environment, file, default), the settings file, whether each credential variable is set (`HYDROLOG_ADMIN_API_KEY`, `HYDROLOG_ADMIN_API_KEY_FILE`; never the value) and no store.
- `-v/--verbose` and `-q/--quiet` set the log level of the CLI.

#### Top-level Python API
- `hydrolog.list_commands()`, `hydrolog.command_schema()`, `hydrolog.validate_command()`, `hydrolog.check_command()` and `hydrolog.run_command()` (the `hydrolog.catalog` functions, imported lazily); `hydrolog.__all__` is these five functions, `__version__` and the error classes. Importing `hydrolog` reads no files and imports no numerical library.

#### Result schemas
- JSON Schemas of every result document (`hydrolog-<group>-<command>/1`, plus `hydrolog-plan/1`, `hydrolog-config/1`, `hydrolog-guide/1`, `hydrolog-command-list/1`) in `src/hydrolog/schemas/`, generated by `scripts/generate_result_schemas.py`, shipped in the wheel and named by `result.schema` in `commands schema`.

#### Error registry and exit codes (ADR-0005)
- `ERROR_CODES` holds the codes of the shared Nogat registry that Hydrolog ends a call with: `internal_error` (1), `validation_error` (2), `not_found` (3), `conflict` (4), `source_unavailable` (5, `precip pmaxtp` only, [ADR-0018](decisions/0018-pmaxtp-through-obserwator.md)), `missing_dependency` (6), `data_error` (7), `io_error` (9), `forbidden` (12), `calculation_error` (13), `cancelled` (130), `terminated` (143). Finer precision is `details.reason`; Hydrolog adds no code of its own. `hydrolog._errors` is generated from the vendored `schemas/nogat/error_registry.json` (`scripts/generate_errors.py`); a contract test compares it and validates error documents against `error-1`.
- The last line of stderr is always the `hydrolog-error/1` document as compact JSON, with and without `--json`; SIGTERM ends with `terminated` (143), Ctrl-C with 130 and no document.

#### Packaging, tooling and metadata
- The package lives in `src/hydrolog`, ships `py.typed` and has a dynamic version (`hydrolog.__version__`); the console scripts are `hydrolog` and `hydrolog-mcp`. uv and `uv.lock` manage the environment; ruff (format and lint with the `D` rules) and mypy `strict` replace Black and flake8; `scripts/gate.sh` runs the gate (ruff, mypy, pytest with coverage of at least 80%, commit check), CI runs it on Linux, macOS and Windows; the tests are split into `tests/unit`, `tests/integration` and `tests/contract`.
- Metadata for discovery (AGI-10.1): the `pyproject.toml` description (the shortest text of the description ladder), keywords, classifiers (`Typing :: Typed`), SPDX license, project URLs (Documentation, Changelog, Issues).
- `hydrolog.visualization` raises `MissingDependencyError` (hint: `pip install hydrolog[viz]`) when the extra is missing; formerly a bare `ImportError`.

#### Documentation
- English throughout (ECO-005): README, `docs/USAGE.md`, PRD, SCOPE, INTEGRATION, COMPUTATION_PATHS, CHANGELOG and the agent guides; Polish names are kept in parentheses where agents search for them. The plans moved to `docs/plans/`; architecture decisions are in `docs/decisions/` (ADR-0001 to ADR-0006) with the index `docs/DECISIONS.md`; `SECURITY.md`, `CONTRIBUTING.md`, `CONTRIBUTORS.md` and the pull request template were added.
- `docs/PROGRESS.md` is reduced to the three sections of DOC-6.1 (status, next, open questions); history lives in this file and the git log.
- Every amended ADR names its amending ADR at the top with the date (`Amended by`, DOC-8.1), ADR-0010 names ADR-0003 under `Amends`, and the index `docs/DECISIONS.md` gives the status `accepted, amended by …`; `docs/PROGRESS.md` keeps the author's decisions under `### Decided`.

#### Flood routing (`hydrolog.routing`, group `route`, ADR-0007 to ADR-0009; branches `feature/routing-*`)
- `Hydrograph` (a discharge table at a regular time step, `time_min` and `discharge_m3s`, with the checks of ADR-0008 and the volume under it), `Reach` (the base class of the routing elements: initial condition, extension of the time axis until the inflow is released, non-negativity), `RoutingResult` (outflow, storage at both ends, volume balance, notices) and `LagReach` (the outflow is the inflow shifted by `lag_min`, linear interpolation for a fraction of a step).
- Command `route lag` (`hydrolog_route_lag`, `hydrolog.operations.route_lag`, result `hydrolog-route-lag/1`): the hydrograph is given inline (`times_min`, `discharge_m3s`) or in a CSV/JSON `input_file` (`time_column`, `value_column`; `load_hydrograph`); `output` writes the outflow as a hydrograph table that every `route` command reads (with `force` and `check`); without `output` the series is in the result and `check` computes as usual, so a read-only MCP server can route. The guide shows the group `route` as one index line (ADR-0009). The other models follow on their own branches (`docs/plans/2026-10-24-flood-routing.md`).
- `MuskingumReach(k_min, x, subreaches=None)` (`hydrolog.routing`): the Muskingum method `S = K [X I + (1 - X) O]` over `N` equal sub-reaches of `K/N` (default `N = K/dt` rounded, the HEC-HMS rule), each inside the positivity window `|2KX| <= dt <= 2K(1 - X)` (`subreach_window`). A time step for which no whole `N` fits is divided into sub-steps (notice `substeps_added`; the volume balance then has a sampling error); a `subreaches` outside the window is a `validation_error` with `details.reason` `unstable_timestep` and the window, `K` too short for 100 sub-steps is refused. It reproduces the University of Iowa example (`K` = 20 h, `X` = 0.25, `dt` = 12 h) within 0.05 cfs, the rounding of the published table (largest difference 0.049 cfs); `X = 0.5` with `K` of `N` steps equals `LagReach`, `X = 0` the Clark scheme, and the mean delay is `K` and the variance `K²(1 - 2X)/N`. The weights are `hydrolog.routing._kernels.muskingum_coefficients`.
- Command `route muskingum` (`hydrolog_route_muskingum`, `hydrolog.operations.route_muskingum`, result `hydrolog-route-muskingum/1`): options `k_min`, `x` (0 to 0.5) and `subreaches` next to the hydrograph, run and output options of `route lag`; `parameters` of the result give the weights of a sub-reach, the number of sub-steps and the window of sub-reaches (`subreaches_min`, `subreaches_max`).
- `MuskingumCungeReach(length_km, slope_m_per_m, ...)` and `TrapezoidalSection` (`hydrolog.routing`): Muskingum-Cunge with constant coefficients (the NRCS form of NEH-630 chapter 17): `K = dx / c` and `X = (1 - Q / (T S0 c dx)) / 2` per routing distance step, the number of steps of the NRCS rule `ceil(L / dx_c)` replaced when its weights would be negative (`subreaches_adjusted`, `substeps_added`, `accuracy_limit`; a reach with no grid of non-negative weights was `unstable_timestep`, and is routed as linear reservoirs since ADR-0026, see Changed), the rise-time rule of at least 10 steps from 5 % of the peak to the peak (`timestep_refined`, `rise_steps`). The celerity and top width are given, or follow from a rectangle, trapezoid or triangle and Manning's equation. NEH-630 example 17-4 is reproduced to 0.24 ft3/s (0.04 % of the peak) with the published celerity and top width, and the table follows from its printed three-decimal coefficients to 0.0049 ft3/s. Muskingum and Muskingum-Cunge share one cascade routine (`route_muskingum_cascade`). The command `route muskingum-cunge` follows.
- Command `route muskingum-cunge` (`hydrolog_route_muskingum_cunge`, `hydrolog.operations.route_muskingum_cunge`, result `hydrolog-route-muskingum-cunge/1`): `length_km` and `slope_m_per_m` with exactly one group of hydraulics options, `manning_n` with `bottom_width_m` (and `side_slope_m_per_m`) or `celerity_m_per_s` with `top_width_m` (anything else is a `validation_error`, `details.reason` `one_of`), and optionally `reference_discharge_m3s`, next to the hydrograph, run and output options of `route lag`; `parameters` of the result give the celerity and top width used, `K`, `X`, the numbers of distance steps and sub-steps, the weights, the Courant and grid Reynolds numbers and the accuracy limit. ADR-0008 now says what the notice `accuracy_limit` means: every distance step inside the positivity window is within the accuracy limit of NEH-630 (`Dg <= exp(2.3 Cg)`), so the notice reports an NRCS step that was replaced, not an inaccurate result.
- `CascadeReach(n, k_min=None, length_km=None, celerity_m_per_s=None)` and `cascade_weights` (`hydrolog.routing`): a cascade of `n` equal linear reservoirs (Nash; the Kalinin-Milyukov method with `n = L / (Q / (T S0 c))`) with the exact response to the piecewise-linear inflow. The weights follow from the incomplete gamma function, so any time step is allowed (no window, no sub-steps) and `n` need not be whole; all `n` reservoirs start with the initial outflow, the storage follows from continuity and `balance_error_m3` is the trapezoid error of the outflow series (ADR-0008). The time scale is `k_min`, or the travel time `length_km / celerity_m_per_s` shared by the `n` reservoirs. It is checked against the exact solution of the chain of reservoirs by the matrix exponential (1e-10), the convolution integral of the `NashIUH` density with the inflow (1e-8), the integral of `NashIUH.ordinate` against a hat, 60-digit arithmetic, and the second-order convergence of the Clark scheme to it. The command `route cascade` follows.
- Command `route cascade` (`hydrolog_route_cascade`, `hydrolog.operations.route_cascade`, result `hydrolog-route-cascade/1`): `n` (> 0, need not be whole) with exactly one time scale, `k_min` or `length_km` with `celerity_m_per_s` (anything else is a `validation_error`, `details.reason` `one_of`), next to the hydrograph, run and output options of `route lag`; `parameters` of the result give `n`, `k_min`, the delay `lag_min` = `n K`, `timestep_over_k` and the length and celerity when given. No time step is refused or divided: the command has no `unstable_timestep` and its only notices are `tail_extended` and `tail_truncated`.
- `LevelPoolReach(storage_m3, outflow_m3s, stage_m=None, subreaches=1)` and `timestep_limit_min` (`hydrolog.routing`): level-pool routing by storage indication (the modified Puls method, `S2/dt + O2/2 = (I1 + I2)/2 + S1/dt - O1/2` with the working curve read from the storage-outflow table; NEH-630 chapter 17, HEC-HMS). The table may have a dead zone below a crest (the pool starts full to it) and a stage; `parameters` of the result give the peak storage and stage with their times and the longest step, and `subreaches` divides the storage among reaches in series. A step longer than twice the shortest storage constant `dS/dO` between the lowest and the highest flow of the run is divided (`timestep_refined`; the rule of NEH-630 for the whole curve lets the outflow overshoot the inflow peak on a table with a sharp change of slope), more than 100 parts are `unstable_timestep`; an initial outflow outside the table is a `validation_error`, a flood beyond the table a `calculation_error` (`table_exceeded`, `table_emptied`). NEH-630 example 17-1 is reproduced to 0.85 ft3/s (0.49 ft3/s with the average inflows as printed), a table of constant storage constant equals Muskingum with `X = 0`, and a tank with a weir follows its exact solution with second-order convergence. The shared array check `as_array` moved to `hydrolog.routing._checks`.
- Command `route level-pool` (`hydrolog_route_level_pool`, `hydrolog.operations.route_level_pool`, result `hydrolog-route-level-pool/1`): the storage-outflow table is given inline (`storage_m3` with `outflow_m3s` and optionally `stage_m`) or as a `rating_file` (CSV or JSON with those columns, read by `load_rating` of `hydrolog.catalog.inputs`), exactly one of the two (anything else is a `validation_error`, `details.reason` `one_of`; a `stage_m` next to a `rating_file` is a `conflict`), and `subreaches` (default 1), next to the hydrograph, run and output options of `route lag`. The file is read after the output has been planned, and `output` must not be the `rating_file`. A bad inline table is a `validation_error` and a bad file a `data_error` that names the row and the column (`details.reason` as in `LevelPoolReach`); a step above the limit of the table is divided (`timestep_refined`) and a flood beyond the table is a `calculation_error`. `parameters` of the result give the sub-reaches and sub-steps, the longest step, the peak storage and, with a stage, the peak stage, with their times. NEH-630 example 17-1 runs through the command from `tests/fixtures/neh17_1_inflow.csv` and `neh17_1_rating.csv`.
- `RoutingNetwork`, the typed nodes `Subcatchment`, `Channel`, `Reservoir`, `Junction` and `Outlet`, and `NetworkResult` (`hydrolog.routing`, [ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)): the elements above composed over a river network, a directed acyclic graph in the convention of `StreamSegment.upstream_ids`. The nodes are immutable objects that **link by reference**: `Subcatchment` (a source hydrograph), `Channel` (any `Reach`; the `type` of a document is `reach`), `Reservoir` (a `LevelPoolReach`), `Junction` (the sum of the hydrographs that flow into it) and one `Outlet`; a node holds the nodes that flow into it (`inflow=`, `inflows=`, `Node.with_inflows` for a copy fed later) and `RoutingNetwork(outlet)` is the network that ends there, everything upstream being in it (a list of nodes is also accepted). The nodes are evaluated headwaters first and, among the ready ones, the smallest id first, so the order of the nodes in a list or a file changes nothing; a one-reach network equals the reach, a junction adds (a shorter hydrograph is held at its last value, as an inflow is over the extension of a reach) and the sum of the routed parts is the routed sum for a linear reach. The structure is checked when the network is made, with the vocabulary of `StreamNetwork` (`details.reason`): `several_downstream` (a bifurcation would count the water twice), `no_outlet`, `several_outlets`, `outlet_has_downstream`, `disconnected_node` (the node that flows nowhere), `upstream_count`, `duplicate_upstream`, `duplicate_node` (ids equal without regard to case), `invalid_id` (an id names the file of the node: letters, digits, `_`, `.` and `-`, at most 64 characters); an id that is not there (`unknown_upstream`) and a cycle (`cycle`, the nodes in flow order) can come only from a document, which links by id. The sources must share one time step and first time (`timestep_mismatch`, `start_mismatch`; nothing is resampled), and a node that fails in `route` names itself (`details.node_id`). `RoutingNetwork.from_document(dict)` reads the document `hydrolog-network/1`. Every node, reach, and so every element that a network is made of, has `describe()`, a list of `Parameter` (name, value, unit, source `given`, `computed` or `default`) with the values that the calculation used (a Muskingum-Cunge reach: the celerity, `K`, `X` and the sub-reaches as computed); `NetworkResult.nodes` carries them for every node next to its peak, time to peak and volume, and `NetworkResult.hydrographs` the hydrograph of every node. A new kind of node, and a new method of a reach, is a class registered in `NODE_TYPES` and `REACH_METHODS`: nothing else lists them. `StreamNetwork` and the network share the ordering and the cycle search (`hydrolog.network._graph`), unchanged in what `network stats` reports. The command `route network` follows.
- A subcatchment can make its own hydrograph (`Subcatchment(id, watershed=, runoff=, rainfall=)`, [ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)). The rain belongs to the subcatchment: `RainfallSource` is a protocol (`DesignStorm`, a depth over a duration in the shape of a `Hietogram`; `RainfallSeries`, the depth of every step, never resampled), and two subcatchments of a network can take it from different sources; `RoutingNetwork(..., rainfall=)` is only a default for those that have none (`missing_field` when neither exists). `RunoffModel` is a protocol (`CurveNumberRunoff`: the SCS Curve Number loss and a unit hydrograph by `HydrographGenerator`, the options of `hydrograph generate`, a CN and the data of a time-of-concentration formula from the `WatershedParameters`); the hydrograph is the one of the generator to the last ordinate, and a network of such nodes routes as the network of their hydrographs. The time step is one for the network: `RoutingNetwork(..., timestep_min=)`, else the step of the given hydrographs and rainfall series (they must agree: `timestep_mismatch`), else 5 min; generated hydrographs start at 0. Kinds of rainfall, runoff models and shapes of a design storm are named in documents through the registries `RAINFALL_KINDS`, `RUNOFF_MODELS` and `HIETOGRAMS`, so a new one is a class and a registry entry. `describe()` of a rainfall, a runoff model and a node lists the values used (given, computed, default), `NetworkResult.rainfall` holds the rain of each such node and `NodeSummary.notices` the notices of every node: a warning of the library is the notice of the node that caused it, and a storm that ends before its duration is `duration_not_covered`.
- A network is written as a document (`RoutingNetwork.to_document()`, `Node.to_document()`, `hydrolog.routing.document.write_network`, [ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)): the `hydrolog-network/1` document of a network, JSON-native, with the nodes in the order of evaluation and nothing that has its default. Every node class writes its own fields (`Node.document_fields()`, abstract, the counterpart of `read_document`), and a reach, a rainfall, a shape of a storm and a runoff model write the object that their class reads; a class that no registry names is refused (`details.reason` `unregistered`), because a document could not name it. A document in that form is written back to the same text, any other one in that form once, and a network read from what was written routes to the last ordinate as the first did.
- A network as an application picks it: `ControlPointNetwork`, `OutletPoint` and `ControlPoint` (`hydrolog.routing`, [ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)). The network is made of its outlet and is a valid network, ready to route, at every step; `add_point(ControlPoint(id, subcatchment), downstream=, channel=)` puts a point above a point (`upstream={id: channel}` for a point picked between two others), `update_subcatchment(id, subcatchment)` gives a point the residual area that is left to it (the area bookkeeping, and the parameters of every channel, are the application's: Hydrolog makes up none), `add_confluence(id, on_channel_of=, upstream_channel=, downstream_channel=)` splits a channel where another stream joins it, and `remove_point(id, channel=)` takes a point away (the points above it stay: through the two channels in series, or through the one that the application gives; two streams that meet in it keep a confluence; a confluence that is left with one stream is dropped). Every point and confluence is a `Junction` that has its id, so `hydrographs[id]` is the discharge at the point, and a nonlinear reach below a confluence is routed once for the water of both streams. Each edit builds the `RoutingNetwork` and is refused, changing nothing, if it is not valid (`details.reason` `unknown_point`, `duplicate_node`, `no_channel`, `not_upstream`, `not_a_point`, `no_inflow`, `outlet_removal`, `still_joins`, `not_applicable`, `type`, and the reasons of a network); `network()` and `route()` give the immutable network and its result.
- Output of several files into a directory (DEV-19.5, DEV-19.6, DEV-19.7, DEV-19.11, AGI-3.4): `plan_directory` plans the files of an `--output-dir` (names compared without regard to case, `output_exists`, `duplicate_output_name`, and `output_in_store` for a directory that is, or lies in, a store of another Nogat tool, recognised by `kartograf-store.json` or `obserwator-store.json`), `staging_directory` writes through `<dir>/.hydrolog-incoming/<host>_<pid>_<token>/` and removes it on every outcome (leftovers older than 24 hours go on the next run), and `-o` is the short flag of `--output-dir` and of no other option; `hydrolog-plan/1` lists the new reason.
- Command `route network` (`hydrolog_route_network`, `hydrolog.operations.route_network`, result `hydrolog-route-network/1`, [ADR-0010](decisions/0010-route-network-document-and-output-directory.md)): routes the hydrographs of many subcatchments down the network of a document `hydrolog-network/1`, given inline (`network`) or as `network_file`, with the discharges inline or in the columns of `inflows_file` (`time_column`). A reach takes a `method` (`lag`, `muskingum`, `muskingum-cunge`, `cascade`, `level-pool`) and the options of `route <method>`, validated by their catalog declaration; a reservoir takes those of `route level-pool`; a `rating_file` is relative to `network_file` and must lie inside its directory (`path_outside`), and an inline network cannot name files (`inline_file`). A wrong document is a `data_error` for a file and a `validation_error` for the inline option, with the same `details.reason`, `node_id` and `field` (the structure reasons of `RoutingNetwork` included); sources with different time axes stay a `validation_error`. `output_dir` (`-o`) writes `<id>.csv` for each node of `nodes` (default all) through the staging directory, planned before anything is computed, never over an input file and re-planned before the files move; without it the hydrographs of the selected nodes are in the result. `result.nodes[]` gives the peak, its time and the volume of every node and, for a reach or a reservoir, what `route <method>` reports; the notices begin with the node id. Fixtures `network_flood.json` and `network_inflows.csv`.
- JSON Schema `hydrolog-network/1` (`hydrolog/schemas/hydrolog-network-1.schema.json`), generated by `scripts/generate_result_schemas.py` from the catalog options: a variant per node type and a reach per method, closed against unknown fields. The CLI texts of the plan and of the conflict `output_in_store` exist in Polish and English; the refusal of an output that is an input now says that the option would overwrite the input file.
- `route network` and the document `hydrolog-network/1`: a subcatchment can have `watershed`, `runoff` (`model` `curve-number` with the fields of `hydrograph generate`) and `rainfall` (`kind` `design` or `series`) in place of its discharges, and the document can have `rainfall` and `timestep_min` at its top; the library checks them with the vocabulary of the catalog (`details.field` of an object inside a node is `rainfall.total_mm`), the entry of such a node has `parameters` (the numbers that its rain and model used), every notice begins with the id of its node, and a warning of the library is a notice and is no longer printed. Documents without these fields are read and answered as before. The JSON Schema has a variant for the subcatchment that makes its hydrograph and definitions of `watershed`, `runoff` and `rainfall`.
- `route network`, three rules decided after the first review: the `schema` of the document is required (`missing_field`, `details.field` `schema`; AGI-4.1: every machine-readable document has one) and the JSON Schema lists it in `required`; a node id that is a Windows device name (`con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`, in any case and with any extension, so `NUL.csv` too) is a `validation_error` with `details.reason` `reserved_name`, because the id names the file `<id>.csv` (`Node`, the reader and the JSON Schema agree); and without `output_dir` a result of more than 20,000 characters, the default page of DOC-1.7, carries the warning `large_result` that suggests `nodes` and `output_dir` (the envelope does not page the result of a command).
- `hydrolog.testing` (DEV-10.6, [ADR-0011](decisions/0011-public-testing-module.md)): public module in the wheel with offline, deterministic builders of what other projects read from Hydrolog, made by the real code: `hydrolog-network/1` documents (`subcatchment`, `reach`, `junction`, `outlet`, `network_document`, `write_network_document`), hydrograph tables as `route network --output-dir` writes them (`hydrograph_table`, `network_tables`, `write_network_tables`), a complete small case (`build_network_fixture`) and the envelope of `precip hietogram` (`hietogram_envelope`, `write_hietogram_envelope`). `tests/contract/test_testing_module.py` compares the builders with the files of the real program.
- `hydrolog.testing` builds the documents of subcatchments that make their hydrograph ([ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md)): `watershed`, `curve_number_runoff`, `design_storm` and `rainfall_series` (each read by the real reader of its kind before it is returned, so a value the command would refuse is refused when it is built), `subcatchment(..., watershed=, runoff=, rainfall=)` and `network_document(..., timestep_min=, rainfall=)`, and a network of three subcatchments, `example_network_document()` and `example_network()` (the `RoutingNetwork` that the document makes, in memory). A column that is read from a file is still checked as an inline source, now on the time step of the network. The contract test runs `route network` on the example and compares its outlet with the in-memory result, and checks the documents of the builders and of `to_document()` against the shipped JSON Schema.
- The schematic of a network ([ADR-0013](decisions/0013-network-schematic.md)): `RoutingNetwork.schematic(result=None, main_stem=None)` returns the document `hydrolog-network-schematic/1` (JSON Schema `hydrolog-network-schematic-1.schema.json`): the nodes on an integer grid, the polylines of the edges (0, 45 and 90 degrees), the labels, the `parameters` of every node and, with a result, its `peak_m3s`, `time_to_peak_min`, `volume_m3` and `notices`, exactly the values of `NetworkResult`. The main stem is a straight line (the branch that drains the larger area, or has more nodes, or the nodes that the caller declares), the tributaries join it at 45 degrees on alternating sides, nodes are one unit apart and no two edges cross; a node with many inflows takes its lines at taps. The picture is a function of the network alone, never of a result, and the same whatever the order of the nodes. `hydrolog.routing.schematic.schematic_svg(document)` draws it with the standard library only; `route network --schematic FILE` writes the SVG (planned, `--force`, `--check`, written through a temporary file, listed in `result.files`) and returns the document as `result.schematic`, `--main-stem` declares the stem, and the human summary names its size. The guide names the option (`AGENTS.md` 16,277 of 16,384 bytes).

#### Web GUI: catalog additions (`hydrolog.catalog`, groups `route` and `gui`, [ADR-0014](decisions/0014-web-gui-enters-the-scope.md), [ADR-0015](decisions/0015-catalog-additions-for-the-gui.md); branch `feature/gui`)
The web GUI enters the scope (ADR-0014; plan `docs/plans/2026-11-02-hydrolog-gui.md`); these are the catalog additions it needs, usable by any client. The catalog has 46 commands in 16 groups.
- `format_command(command, options=None, run=None)` and `parse_command(line)` (in `hydrolog` and `hydrolog.catalog`, AGI-2.1): a call as the canonical CLI line `hydrolog <group> <verb> --flag value ...` (options in catalog order, `shlex`-quoted, booleans `--x`/`--no-x`, then the run flags `--json`, `--lang`, `--verbose`, `--quiet`) and back as `ParsedCommand(command, options, run)`, read by the CLI's own parser. `format_command` checks option names and value forms, not bounds, `required` or `one_of`; `parse_command` refuses `--help`, `--version` and `--schema`. `format_command(*parse_command(line))` gives the line back, and the `call` of every catalog example is its canonical line.
- Notices with stable codes and values: `Notice.details` (in `to_dict()` only when not empty; the envelope schema is unchanged), the read-only registry `NOTICES` of every code Hydrolog emits (`NoticeSpec`: `code`, `level`, English `template`, `details` keys, `own_text`) and `notice(code, **details)` (`hydrolog.catalog`). Library warnings are `HydrologWarning` subclasses (`UserWarning`s) named after their code and carry their `details`; any other captured warning is `user_warning` or `runtime_warning`. New codes: `missing_pairs_removed`, `outside_typical_range`, `small_sample`, `short_record`, `ks_test_approximate`, `unknown_hietogram_type`, `uh_model_mismatch`, `runtime_warning`, `exposed_without_auth`, and `superseded` and `timeout` for the GUI's server. The routing models' notices keep their codes and text without `details`; `route network` adds `details.node_id` to the notice of a node.
- Command `route schematic` (`hydrolog_route_schematic`, `hydrolog.operations.route_schematic`): the layout of a network (`network` or `network_file`, optionally `inflows_file` with `time_column`, and `main_stem`) as the document `hydrolog-network-schematic/1` without values, equal to `RoutingNetwork.schematic()`; read-only, it routes nothing and writes no file.
- `hydrograph generate` returns the unit hydrograph used in the convolution, `uh_times_min` [min] and `uh_discharge_m3s_per_mm` [m3/s per mm] (optional fields; the result stays `hydrolog-hydrograph-generate/1`).
- Command `gui serve` (group `gui`, `hydrolog.operations.gui_serve`): starts the web GUI's server (`host`, default `127.0.0.1`; `port`, default `8070`; `no_browser`) and on Ctrl+C or SIGTERM returns `hydrolog-gui-serve/1` (`url`, `started_at`, `stopped_at`) with exit 0; the server comes with the extra `gui` (without it: `missing_dependency`, hint `pip install "hydrolog[gui]"`). `--check` returns `hydrolog-plan/1` with `targets: []`, `url` and `port_free` without serving; a host other than loopback adds the warning `exposed_without_auth`.
- `Command.agent_tool` (default `True`): `gui serve` has `False`, so it is in `commands list` and `commands schema` (as Nogat's routes need, HUB-2.9) but is not an MCP tool (`families` empty) and has no line in `AGENTS.md` or `llms.txt`.

#### Web GUI server (`hydrolog.gui`, extra `gui`; plan `docs/plans/2026-11-02-hydrolog-gui.md`)
- The extra `gui` (`starlette>=1.10,<2`, `uvicorn>=0.54,<1`, repeated in `all`); importing `hydrolog.gui` needs neither, `create_app` and `serve` raise `missing_dependency` with the hint `pip install "hydrolog[gui]"`. The dev group gains `httpx2` (Starlette's `TestClient`) and `playwright`; the browser tests (`tests/e2e`) run in the gate with Chromium, which CI installs on all three systems.
- `hydrolog.gui.create_app(work_root=None, workers=2, run_timeout_s=30.0)`: the ASGI app that serves the page (`hydrolog/gui/web/`) at its root and its private API under `api/`, relative to the page, so a host may mount it at any prefix: `GET api/session` (`hydrolog-gui-session/1`: version, limits, the session's files), `GET api/commands` and `api/commands/{group}/{verb}` (the catalog without `gui serve`, `config show` and `commands guide`), `GET api/schemas/{file}`, `POST api/run/{group}/{verb}?channel=…&check=true` (the `hydrolog-result/1` envelope; an error is `hydrolog-error/1` with the registry's HTTP status and the Polish `title`), `POST api/format/{group}/{verb}` (`hydrolog-gui-line/1`), `PUT api/files/in/{name}` (`201`, `hydrolog-gui-file/1`), `GET` and `DELETE api/files/{in|out}/{name}`. It is not a REST interface of Hydrolog (no `/api/v1`, no OpenAPI; a deviation from AGI section 6).
- Runs go to warm worker processes (NumPy, SciPy and the operations imported once, one thread of numerical code, 2 GiB of address space on POSIX): a newer run of the same session and channel ends a queued older one (`cancelled`, notice `superseded`); a run longer than `run_timeout_s` kills its worker, which is replaced (`cancelled`, notice `timeout`). Paths in envelopes and errors are relative to the session (`in/x.csv`).
- One work directory per browser session (cookie `hydrolog_gui`, HttpOnly, SameSite=Strict), with `in/` (uploads) and `out/` (outputs); a path option takes only `in/<name>` or `out/<name>`, an output only `out/` (`forbidden`, `details.reason` `outside_session` or `output_area`). Limits: 20 MiB per file and 5 MiB of JSON per request (`validation_error`, `too_large`), 100 MiB and 200 files per session (`conflict`, `session_full`), 64 sessions (the least recently used idle one goes first), 12 hours idle.
- Every response has the headers of the plan (CSP `default-src 'self'` with `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `no-referrer`, COOP, CORP, Permissions-Policy; `no-store` under `api/`, `no-cache` for the page); `POST`, `PUT` and `DELETE` are refused when `Sec-Fetch-Site` is `cross-site` or `same-site` (`forbidden`, `cross_site`), and runs and lines take only `application/json`.
- `hydrolog.gui.serve(host=, port=, open_browser=)`, the standalone server of `hydrolog gui serve`: writes `Hydrolog GUI: <url>` to stderr, stops gracefully on Ctrl+C or `SIGTERM` and returns `url`, `started_at` and `stopped_at`; a port in use is a `conflict` (`port_in_use`).
- `hydrolog.gui.gui_module()` returns the `GuiModule` (name, title, the page's directory, `index.html`, the five sections, `create_app`) that Nogat's GUI platform finds through the entry point group `nogat.gui`.

#### Web GUI: the foundation (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S2)
- The page `src/hydrolog/gui/web/` in Polish and Nogat's identity: `tokens.css` and the marks of Hydrolog, Hydrograf and Nogat copied from Nogat `29e7e1c` with their SHA-256 in `nogat/nogat.json`; Preact 10.29.8 and htm 3.1.1 vendored byte-identical with Archiwista's files (`vendor/vendor.json`); no build, no remote resource, no inline script or style.
- The shell: top bar (mark, breadcrumbs, status badge, theme Auto | Jasny | Ciemny stored as `nogat-theme`), the rail (a bottom bar at 860 px and below), Dane | Wykresy | Wyniki with panels resizable by drag and keys and bottom sheets on phones, `?nogat=1` hiding the top bar and rail before the first paint; every URL relative to the page, so it works under any prefix.
- The API client, the shared store (`watershed`, `reference`, `status`, `context`), inputs kept per section in `localStorage` (`hydrolog-gui/<section>/1`), Polish numbers (`Intl.NumberFormat("pl-PL")`, a comma or a dot typed), the (i) popover and its registry, the export panel (CSV, JSON, PNG, the Markdown report, the command line with Python and MCP, files).
- The catalog form generator: numbers with units and bounds, choices with their Polish meanings, series pasted or read from a CSV in the browser, chips, JSON, session files (upload, `in/`, `out/`), `one_of` groups as „Sposób podania” panes, `requires`, `excludes`, `section` and `format` when present; errors and notices worded in Polish from their codes, the English message marked „(EN)” as the fallback.
- „Wszystkie polecenia”: every command the server runs, by group with a search, its form, the generic result view (tiles, parameters, series as a chart and a table, records, plan targets, files, JSON) and its call.

#### Web GUI: charts (`src/hydrolog/gui/web/src/charts/`, `css/charts.css`)
Inline SVG charts of the GUI in the look of the approved mockup, coloured by Nogat's tokens only, so the theme switch needs no redraw (plan `2026-11-02-hydrolog-gui`, D12).
- Linear, log and time axes (minutes, labelled in hours) and a Gumbel probability axis (the exceedance probability p in % on the reduced variate, labelled with p and the return period T); rounded ticks in Polish numbers (decimal comma, a non-breaking space between thousands from five digits).
- Lines, steps, areas, bars (on the second axis a panel above the main one with the bars hanging from its top: the hyetograph above the hydrograph on one time axis), points, horizontal bars on a category axis; peak, reference-line, moment and note marks; a legend.
- A readout by pointer and by keys (arrows, Shift or Page for ten steps, Home, End, Esc), also announced to screen readers.
- `toPng(svg, {scale: 2})`: the chart as drawn (computed styles, current theme, no readout) as a PNG at twice its size, through a `blob:` image within the page's Content-Security-Policy.
- `Chart` (Preact) wraps `drawChart`, which uses the DOM only, so a kit component can wrap it too.

#### Web GUI: „Hydrogram zlewni” (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S3)
- One watershed through `hydrograph generate` in five steps (Zlewnia, Czas koncentracji, Opad, Straty SCS-CN, Model UH); the result follows every change: a valid change runs on channel `hydrogram` 250 ms after the last one, an older run is aborted and only the newest response applies, „Liczenie…” after 150 ms; invalid data run nothing and keep the last result, marked („Dane niepełne” with the field, checked against the catalog and `watershed` of `hydrolog-network-1.schema.json`); a server error stands on its field (a tc method's missing watershed fields each on theirs) or above the steps („Błąd danych”).
- The watershed is typed or a WatershedParameters JSON read in the browser (as `--watershed-file` reads it); fields changed from their source are marked with „przywróć”. Rainfall: PMAXTP (the depth typed for p and the duration), a design hyetograph or an own series; Nash by Lutz runs `uh nash` first and passes `nash_n` and `nash_k_min` on. (The steps and the first visit changed with the three steps below, and PMAXTP's depth is fetched by `precip pmaxtp`, no longer typed: ADR-0018, below.)
- The hyetograph above the hydrograph, cumulative P and Pe with Ia, the convolved unit hydrograph, the table of the series, the peak, time to peak, volume and runoff coefficient, the balance of the rainfall, the parameters, applicability notes from the (i) ranges before Hydrolog's notices, and the exports: the hydrograph CSV (`time_min,discharge_m3s,precipitation_mm,effective_precipitation_mm`, read by every `route` command), the envelope, the chart as PNG and the command line (CLI, Python, MCP).
- The (i) explanations of the tc methods, SCS-CN, the unit hydrographs and the rainfall (`web/src/labels/info/{tc,losses,uh,rain}.js`); the store's `watershed` for Kalkulatory, Statystyka's `reference` drawn on the hydrograph, and the route `#hydrogram/tc_method/<method>`.

#### Web GUI: „Sieć i trasowanie” (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S4)
- The network drawn vertically from `route schematic` before any run: the sources at the top, the outlet at the bottom, the main stem straight and the tributaries at 45 degrees, each label on the side of its node without a tributary (`sections/siec/schematic.js`, a pure transform of `hydrolog-network-schematic/1`); after a run each node shows its peak and time to peak.
- A node is chosen by a click, Enter or Space on the schematic, in the node list or in the node table (also `#siec/<id>`); its settings open in „Dane”: forms per node type and reach method generated from `hydrolog-network-1.schema.json` with the catalog's Polish help (a subcatchment from rainfall, from the inflows file or with its own hydrograph; lag, Muskingum, Muskingum-Cunge by section or celerity, a cascade by K or by length and celerity, level-pool and a reservoir with a storage table or a rating file; the network's name, time step and default rainfall). The structure is not edited.
- Networks open from a file together with the files they read (rating tables, the inflows file), from the shipped example (`examples/siec.json`, `hydrolog.testing.example_network_document()`) or from another part of the page (`openNetwork`); „Zapisz sieć” saves the document.
- „Oblicz sieć” writes the document to the session's `in/` and runs `route network`; „Wyniki” shows the outlet's peak, time and volume, the chosen node's inflows and outflow as a chart, its parameters and ordinates, the notices and the call; a change afterwards marks the result stale. Exports: one node's or every node's hydrograph as CSV, the network's document and the envelope as JSON, the schematic as PNG and Hydrolog's own SVG.
- The (i) explanations of the five routing methods (`labels/info/routing.js`).

#### Web GUI: „Statystyka przepływów” and „Kalkulatory” (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S5)
- „Statystyka przepływów”: `stats flood-frequency` on a file of the session (its columns read from the header in the browser, `date_column` guessed for a daily series) or on pasted annual maxima, with the catalog's fields; a first visit uploads the shipped sample `examples/maksima_roczne.csv` (the years 1998–2023 of `tests/fixtures/annual_maxima.csv`: GEV, Q 1% = 307,3 m³/s). „Oblicz” runs the command and a second run on a dense grid of return periods draws the probability plot on Gumbel paper (the maxima in Weibull positions, four curves, the best thicker); the tiles, the notices in Polish (the KZGW 30-year notice among them), the distributions with AIC, A² and KS, the quantiles of the best one, the ranked maxima with their years, CSV of the quantiles, JSON, PNG, the call, and „Do porównania”, which hands the stressed quantile to Hydrogram zlewni (`store.reference`). (i) texts in `labels/info/stats.js`.
- „Kalkulatory”: sixteen calculators. The comparison of the six tc methods runs `tc watershed` once per method with the watershed of Hydrogram zlewni and the overland fields set here: bars and a table coloured and worded by Hydrolog's notices (FAA and Kerby „nie dla zlewni”), the parameters each method took, the notices once each, CSV, the shell loop of the calls and „Użyj w Hydrogramie zlewni”. Fifteen catalog commands as generated forms, filled from their first example and from the watershed (the tc commands with what `tc watershed` derives from it), each with the generic result view and its call.

#### Web GUI: the hand-off, the Markdown report and the print view (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S6)
- `nogat-handoff/1` carrying `hydrolog-network/1`: Nogat's schema copied unchanged to `schemas/nogat/handoff-1.schema.json` (Nogat `a01097c`, SHA-256 in `schemas/nogat/README.md`). „Przekazanie” in the panel Wyniki of Hydrogram zlewni writes the shown run as one subcatchment made from rainfall and the outlet, with its provenance (the PMAXTP probability and duration, the watershed's source and the fields changed since, Lutz's estimate of Nash's n and K) and the result in D15's names; Sieć writes its network with the outlet's result when the last run is of it. „Plik przekazania” downloads `<subject>.handoff.json`, „Do schowka” copies it.
- „Wczytaj z Hydrografa” (a hand-off file or the clipboard, with a field to paste into where the browser gives no clipboard) in the first step of Hydrogram zlewni and Sieć: the envelope is checked against the validation keywords of Nogat's schema and the payload against `hydrolog-network-1.schema.json` (`handoff/validate.js`, Polish problems with their paths); one subcatchment opens in Hydrogram zlewni with the producer as the watershed's source, any other network in Sieć. The producer's result is shown beside Hydrolog's with both versions (`result.computed_with`, e.g. Hydrograf computing with Hydrolog 0.6.3), a differing value marked, and a note when the data changed since.
- The Markdown report from Hydrogram zlewni: „MD Raport” runs `report generate` with the run's options into `out/<subject>.md` and downloads it.
- The print view: `css/print.css` (`media="print"`) puts the shown section on A4 in one column (its charts, results, notices, a received hand-off, the command line, then the data with their source) without controls; „Raport do druku” in Hydrogram zlewni and Sieć, and the browser's own print, print it in the light theme with every part open (`src/print.js`); PDF through the browser.

#### Web GUI: „Instrukcja”, the welcome dialog and the guide (plan [2026-11-02-hydrolog-gui](plans/2026-11-02-hydrolog-gui.md), slice S7)
- The guide for users, `web/instrukcja/` (Polish, static HTML under the app's top bar and theme, both themes, phones): it starts in plain words for people interested in rivers and wetlands, not hydrology (what Hydrolog is; what to expect and what not: estimates, not a forecast or an official flood hazard map; example questions and who can use it; a first result in three steps; a glossary of zlewnia, przepływ, opad projektowy, hietogram, hydrogram, CN, czas koncentracji and trasowanie fali), then one chapter per section with pictures of the running GUI, the exports (the Markdown report, the print view and the hand-off with Hydrograf among them), the phone, the theme, the user's data, troubleshooting and running it. Its contents tell a beginner to read only „Na start”. The numbers it quotes are those of the shipped examples, and a browser test computes the examples and compares them.
- „Instrukcja” in the top bar opens a welcome dialog: a native modal `<dialog>` with three plain sentences, „Otwórz instrukcję” (the guide in a new tab), „Przejdź do aplikacji” and „Nie pokazuj ponownie”. It opens on every visit until that box is ticked (`localStorage` `hydrolog-gui/welcome/1`), keeps the choice whichever way it is closed (a button, Escape, a click beside it), and a click with a modifier on „Instrukcja” follows the link to the guide instead. Inside Nogat's shell (`?nogat=1`) there is none.
- Documentation: the extra `gui` and a „Web GUI” section in the README; „8. The web GUI” in `docs/USAGE.md` (in plain words first, where results go, starting it, the data it keeps, running it as a service behind an authenticating proxy such as Cloudflare Access); hosting it in Nogat's GUI platform and the hand-off with Hydrograf (`nogat-handoff/1`: writing, provenance, reading, comparing) in `docs/INTEGRATION.md`.
- The final smoke (`tests/e2e/test_smoke.py`): every section and the guide open without a console error or a CSP violation in both themes at 1440 and 390 px. The browser tests start with the welcome dialog hidden unless a test asks for it, and the contract checks of the page (no inline script or style, every linked file present) cover the guide too.

#### Web GUI: „Zgłoś uwagę” and the admin page (Nogat plan `docs/plans/2026-11-03-feedback-in-archiwista-and-hydrolog.md`, D3 to D6; [ADR-0016](decisions/0016-gui-feedback-and-data-dir.md))
- „Zgłoś uwagę” in the top bar, Hydrograf's mechanism and texts: a modal dialog with the description and its counter (1 to 5,000 characters), an optional name or e-mail (up to 200), „Dołącz dane diagnostyczne” (ticked) with „Pokaż co zostanie wysłane”, the very diagnostics that are sent, „Anuluj” and „Wyślij”, a status line, and closing 2 s after the thanks. Not inside Nogat's shell (`?nogat=1`), which hides the top bar.
- The diagnostics (`web/src/diagnostics.js`), kept in the page's memory until a report is sent: the last 50 events (JavaScript errors; API calls with the endpoint, method, status, duration and the error's code, without bodies; changes of the section; the catalog documents read at load only when they fail), the workspace (the section, its route, status badge, context and stored inputs, a text over 200 characters or with lines and the rest of a list over 50 replaced by their size) and the environment; at most 100,000 bytes of JSON, the oldest events dropped first; never the contents of files, cookies or keys.
- `POST api/feedback` (a GUI session, JSON of at most 256 KiB) → `{"id", "status": "ok"}`; `GET api/admin/feedback?limit=1..200&offset=` → `{"items", "total", "unread_count"}` newest first; `PATCH api/admin/feedback/{id}` `{"is_read": bool}` → `{"status": "ok"}`; `DELETE api/admin/feedback/{id}` → `{"status": "deleted"}`. Hydrograf's limits (`validation_error` with `details.parameter` and `reason` `required`, `type`, `empty`, `too_long`, `too_large`), `not_found` (`feedback_not_found`), `io_error` (`feedback_store_failed` and the like, without the file's path). The admin routes need `X-Admin-Key` equal to `HYDROLOG_ADMIN_API_KEY` or the text of the file named by `HYDROLOG_ADMIN_API_KEY_FILE` (read at every request, compared in constant time); without a key on the server they refuse every request (`401 unauthorized`, `admin_key_not_configured`; also `admin_key_missing`, `admin_key_invalid`); no key is generated.
- The reports live in SQLite `<data_dir>/hydrolog/feedback.sqlite3` (table `feedback` with the limits as checks, WAL, `PRAGMA user_version` 1), made with its directory (0700, the file 0600) by the first report; reading makes nothing. `hydrolog.gui.create_app(..., data_dir=None)` places it for a host. README, USAGE (section 8, „Reports of users”) and the guide say how to read the file (`sqlite3`, the admin page, `curl`) and back it up (`sqlite3 ... ".backup ..."`).
- The admin page `admin/` (static HTML and a Preact module under the CSP `'self'`): the key or a key file, kept in `sessionStorage` (`hydrolog-gui/admin-key/1`) until „Wyloguj”; the reports newest first with the count of unread ones, a report's details (message, contact, page, browser, workspace, environment, events; every text a text node), „Oznacz przeczytane” / „Oznacz nieprzeczytane”, „Usuń”, „Pokaż starsze”.

#### PMAXTP through Obserwator (`precip pmaxtp`, extra `pmaxtp`, [ADR-0018](decisions/0018-pmaxtp-through-obserwator.md); branch `feature/pmaxtp-from-obserwator`)
The author's decision of 2026-11-04: with PMAXTP a person gives the point, the probability and the duration, and the depth is fetched from IMGW-PIB through Obserwator, never typed. It is Hydrolog's only network access; every other command still computes offline on numbers and local files. The catalog has 47 commands in 16 groups.
- The extra `pmaxtp` (`obserwator>=3.0.0.dev0,<4`, repeated in `gui` and `all`), which `[tool.uv.sources]` pins to commit `1ee54573453473392f21e2c8bb34f76e4976e03f` of Nogat's release set candidate-1 until Obserwator is tagged; `uv.lock` adds obserwator, httpx, httpcore, pydantic-settings and python-dotenv. The pytest marker `live` now names the PMAXTP of IMGW-PIB.
- Command `precip pmaxtp` (`hydrolog_precip_pmaxtp`, `hydrolog.operations.precip_pmaxtp`, result `hydrolog-precip-pmaxtp/1`, `PrecipPmaxtpResult`): `latitude` and `longitude` (WGS84, decimal degrees, bounds 49–55 and 14–24.5), `duration_min` (one of the 16 durations of the atlas, 5 min to 72 h), `probability_percent` (one of the 27 probabilities, 0.01 % to 99.9 %) and `method` (`POT`, the default, or `AMP`) give `depth_mm` with the point, the method, the duration, the probability and `attribution`. A duration, probability or method the atlas lacks is a `validation_error` (`details.reason` `choice`, `details.allowed`) before anything is fetched. Obserwator is imported only when the command runs (without it: `missing_dependency`, `details.extra` `pmaxtp`, hint `pip install "hydrolog[pmaxtp]"`), and a request may take 20 s, under the GUI's 30 s run limit (`hydrolog._pmaxtp`). Its errors become registry codes: a point inside the box but outside the atlas is `validation_error` on `latitude` with `details.reason` `outside_pmaxtp`, IMGW-PIB unreachable `source_unavailable`, an unreadable answer or a missing cell `data_error`. The JSON Schema is one of the hand-written ones of `scripts/generate_result_schemas.py`, because its example would need the network (the script runs offline).
- `Command.network` (default false), true for `precip pmaxtp` alone: `effects.network` of `hydrolog-commands/1` and the `openWorldHint` of the MCP tool follow it (formerly false for every command). The agent guides, the MCP instructions and the README say that only `precip pmaxtp` goes online.
- `source_unavailable` (exit 5) joins `ERROR_CODES`: IMGW-PIB did not answer, with `details.source` `imgw-pmaxtp` and Obserwator's `url`, `reason` and `status`; the hint offers `precip hietogram --total-mm`.
- The notice `pmaxtp_attribution` (`info`, `details` `attribution` and `terms_url`, <https://danepubliczne.imgw.pl/regulations>): every run names IMGW-PIB as the source, as its terms of use prescribe; the message points to the result's `attribution`, so the CLI prints the formula once. Its Polish text is in `web/src/labels/notices.js`.
- Tests stay offline: an autouse fixture of `tests/conftest.py` answers `obserwator.fetch_pmaxtp` with IMGW-PIB's table for Warsaw recorded on 2026-11-04 (`tests/fixtures/pmaxtp_warszawa_pot.json`), so Hydrolog's real code reads it; one test marked `live` asks IMGW-PIB and the gate deselects it. `docs/USAGE.md` shows the command and `SECURITY.md` says what goes out.

#### A station's series from Archiwista in Statystyka przepływów (the author's decision of 2026-11-05; [ADR-0020](decisions/0020-a-stations-series-through-the-handoff.md); Nogat plan `2026-11-05-archiwista-series-to-hydrolog`; branch `feature/series-handoff`)
- **The payload `hydrolog-series/1`** (`hydrolog/schemas/hydrolog-series-1.schema.json`, generated with the other schemas): a variable's daily values (`step` `day`, `dates`) or an annual extreme of each year (`step` `year`, `statistic`, `year_type`, `years`), `values` with `null` for a missing value, carried by Nogat's `nogat-handoff/1`.
- **Web GUI: „Wczytaj z Archiwisty”** in the first step of Statystyka przepływów reads such a hand-off from a file or the clipboard (any hand-off opens where it belongs; „Wczytaj z Hydrografa” opens a series here too): annual maxima become the pasted values without the missing years, daily values a file of the session `<subject>.csv` (`date` and the variable) with its columns chosen; where the series came from is shown until it is changed. Annual minima are refused with the reason (low flows are `stats low-flow`).

#### Fit methods of flood frequency (reports 4 and 12 of „Zgłoś uwagę”; [ADR-0021](decisions/0021-fit-methods-of-flood-frequency.md); plan `2026-11-06-flow-statistics-feedback`, D1; branch `feature/fit-methods`)
- **`stats flood-frequency --fit-method`**: `mle`, `moments`, `l_moments` (the default since D6, see "Changed") or `least_squares`; the result carries `fit_method` (an optional field of `hydrolog-stats-flood-frequency/1`). Every method fits the same scipy distributions (log-normal with location 0, GEV, Pearson III, Weibull), so quantiles, K-S, A² and AIC follow alike.
- **Library**: the keyword `fit_method` of `FloodFrequencyAnalysis.fit_log_normal`, `fit_gev`, `fit_pearson3`, `fit_weibull` and `fit_all`; `hydrolog.statistics.FIT_METHODS` and `FitMethod`. The moments use the unbiased variance and the adjusted skewness G1; the L-moments the unbiased probability-weighted moments (Hosking and Wallis 1997); least squares fits the quantiles at the Weibull plotting positions from the moments (it follows the largest annual maxima). The Weibull distribution of these methods is the GEV of the negated sample.
- **New notices** `distribution_left_out` (a method gives no parameters of a distribution: too few or equal values, a sample skewness or L-skewness outside its range, a value not above 0 for the log-normal; `fit_all` and `distribution all` leave it out, a single distribution is a `calculation_error`) and `outside_support` (annual maxima without density under a fitted distribution: its AIC is `null` and it ranks last; any method, also maximum likelihood, whose Weibull of the guide's example has had a `null` AIC).
- **Web GUI**: „Metoda estymacji parametrów” in the step „Rozkłady” of Statystyka przepływów, sent by both runs (the tables and the curves; nothing is sent until a method is picked); the chart's subtitle names the method; an (i) text explains the four. `ChoiceField` takes `select` to show a select for long values.

#### Distributions chosen in Statystyka przepływów (reports 8 and 11 of „Zgłoś uwagę”; plan `2026-11-06-flow-statistics-feedback`, D2; branch `feature/stats-distribution-selection`)
- **Web GUI: „W tabeli kwantyli”**: each row of the distributions table has a checkbox. The quantile table has one Q column per ticked distribution, in the order of the distributions table, and its CSV export has the same columns (`<distribution>_m3s`). After every computation only the best one is ticked, and the last ticked one cannot be unticked.
- **Web GUI: the active distribution**: a click on a row of the distributions table (or Enter on a focused row) makes that distribution the active one. Its row is marked, the tiles and „Do porównania” use its quantiles (the tile says „Najlepszy” when it is the best), and on the probability plot its curve is full and thick and the others are dimmed. The best one is active after every computation; neither choice is stored. `DataTable` takes `onRow` and `currentRow` for such rows.

#### Density and distribution-function charts in Statystyka przepływów (report 10 of „Zgłoś uwagę”; plan `2026-11-06-flow-statistics-feedback`, D3; branch `feature/stats-density-charts`)
- **`stats flood-frequency`: `densities`** in every distribution of the result: the fitted probability density [1/(m³/s)] at each of its `quantiles`, in the same order (an optional field of `hydrolog-stats-flood-frequency/1`, nested in `distributions[]`, so the schema does not change). The library's `FrequencyAnalysisResult` has the field `densities` after `quantiles`.
- **Web GUI**: under the probability plot of Statystyka przepływów, the card „Gęstość prawdopodobieństwa i dystrybuanta” has two charts against Q. „Gęstość prawdopodobieństwa” shows f(Q) of every distribution, with the annual maxima as a rug on the Q axis; its scale follows the active distribution (its largest density with the axis's headroom), and a curve that rises above it, such as a GEV's spike at its lower bound on a short series, is clipped at the frame. „Dystrybuanta” shows F = 1 − p of every distribution, with the annual maxima as points at their Weibull positions. The active distribution's curve is full, the others are dimmed, as on the probability plot. Both charts end at the larger of the largest maximum and the active distribution's Q 1%. The curves' run now has 106 return periods instead of 24: p every 1% from 99% to 2%, plus finer steps at both ends, from 99.5% to 0.1%. The charts kit has a series kind `rug`.

#### No highlighted period by default in Statystyka przepływów (report 9 of „Zgłoś uwagę”; plan `2026-11-06-flow-statistics-feedback`, D4; branch `feature/stats-no-chosen-period`)
- **Web GUI: „Wyróżniony w wynikach” starts with „brak”** (a new first value; T = 100 before). Without a highlighted period the tiles have no tile of its quantile, no row of the quantile table is marked, the probability plot marks no quantile, and „Do porównania” is disabled until a period is chosen. A chosen period works as before and is stored. The stored inputs keep their key `hydrolog-gui/statystyka/2`: a stored T = 100 (the former default) stays highlighted until „brak” is chosen or „Wyczyść” clears the inputs. The guide's example chooses 100 before „Oblicz”.

#### Homogeneity tests of annual maxima (report 3 of „Zgłoś uwagę”; [ADR-0022](decisions/0022-homogeneity-tests.md); plan `2026-11-06-flow-statistics-feedback`, D5; branch `feature/homogeneity-tests`)
- **`stats homogeneity`** (result `hydrolog-stats-homogeneity/1`): the series of `stats flood-frequency` (a daily series with dates, whose complete hydrological years give the annual maxima and their years, or annual maxima with optional years: `years` inline, `year_column` in a file), `split_year` and `alpha` (default 0.05). The two-sided Mann-Whitney U test and the two-sample Kolmogorov-Smirnov test compare the annual maxima before `split_year` with those from it on (by default the first ⌊n/2⌋ values with the rest); Pettitt's test finds the most probable change point, K = max |U_t| with p ≈ 2·exp(−6K²/(n³ + n²)), at most 1. Each test gives `statistic`, `p_value` and `homogeneous` (`p_value ≥ alpha`); the split (`split_index`, `split_year`) and Pettitt's change point (`change_point_index`, `change_point_year`) are named by the first value after them. The new notice `homogeneity_rejected` names the tests that reject.
- **Library**: `hydrolog.statistics.homogeneity_tests(series, years=None, *, split_year=None, alpha=0.05)` returns `HomogeneityResult` with `TwoSampleTestResult` and `PettittResult`. `hydrolog.catalog.inputs.load_series` and `Series` take the years of annual values without dates (`years`, `year_column`: whole numbers, strictly increasing; not with dates).
- **Agent guide**: the command index of `AGENTS.md` names the commands of `stats` on one line, as those of `route`, to stay within 16 KiB (a deviation from DOC-4.2 in `CLAUDE.md`).
- **Web GUI: „Jednorodność ciągu”** in Wyniki of Statystyka przepływów: „Oblicz” also runs `stats homogeneity` on the same series (with the year column of a file of annual maxima), and the panel shows each test's statistic, p-value and answer „Jednorodny” (tak/nie), the split and Pettitt's change point (years, or positions for pasted values); `homogeneity_rejected` joins „Uwagi” and an (i) text explains the tests. `stats homogeneity` is also linked from the data panel. A Polish notice text may name the codes of a detail (`names` in `labels/notices.js`).

#### Every fit method at once (the author's review of 2026-11-06; [ADR-0021](decisions/0021-fit-methods-of-flood-frequency.md) amended; plan `2026-11-06-flow-statistics-feedback`, D6; branch `feature/fit-method-all`)
- **`stats flood-frequency --fit-method all`**: each distribution fitted by each of the four methods (with `--distribution all` up to 16 items, with one distribution its four), ranked by AIC over all of them. Every item of `distributions` carries its `fit_method`; the result's `fit_method` is the value asked for. A combination a method cannot fit is left out with `distribution_left_out`, which names its distribution and method; maximum likelihood fits each distribution, so `all` never ends with the error of none remaining.
- **Library**: `FloodFrequencyAnalysis.fit_all(fit_method="all")` keys the results `"<distribution>/<fit_method>"` (one method keeps the distribution names), and `fit_all` takes `distribution` (`"all"` or one of the four; one combination asked for raises its own `CalculationError` instead of leaving it out). `FrequencyAnalysisResult` has the field `fit_method` after `distribution_name`. `plot_frequency_comparison` labels a curve by its distribution and, when the results hold several methods, its method.
- **Web GUI**: „Metoda estymacji parametrów” keeps one method a run; `all` waits for the view of the combinations (plan D7).

#### Every combination in Statystyka przepływów (the author's review of 2026-11-06; plan `2026-11-06-flow-statistics-feedback`, D7; branch `feature/stats-combinations-view`)
- **Web GUI: one run of every combination, filters that only show.** Both runs of Statystyka przepływów (the tables and the curves) send `distribution` `all` and `fit_method` `all`. „Rozkłady” and „Metody estymacji” in Dane are multiple choices of what is shown (every distribution by the L-moments at first; one of each stays chosen); changing them sends nothing, and they are stored. The colour of a curve is its distribution, its line style the fit method (L-moments solid, maximum likelihood dashed, moments dotted, least squares dash-dot), on every chart, legend and swatch; the legends key the colours and the line styles. „Najlepszy” is the lowest AIC among the combinations shown, and the (i) text says that AIC across methods favours maximum likelihood when scipy's search converges.
- **Web GUI: tables of combinations.** The distributions table has a row per combination shown and the column „Metoda”; with more than one method shown, the checkboxes, the notices, the quantile columns and their title name the method too. „W tabeli kwantyli” can untick every row, the best one included (it could not before); with none ticked the quantile table gives way to a note and the CSV holds only the periods and their probabilities. The CSV columns are `<distribution>_<fit_method>_m3s` (formerly `<distribution>_m3s`). The notices `outside_support` and `distribution_left_out` show only for the combinations shown.
- **`outside_support` names its fit method**: `details.fit_method` and the message („The gev distribution fitted by mle gives no density…”), so the notices of one distribution by several methods stay apart; the Polish text names the method.
- **Stored inputs**: their key is `hydrolog-gui/statystyka/3`. `distribution` and `fit_method` left the stored values and `shown` came, so a version-2 store (one distribution and one method a run) is not read and the section opens as on a first visit.

#### Charts readable at every width, axes from zero, stable ranges (the author's review of 2026-11-06; plan `2026-11-06-flow-statistics-feedback`, D8; branch `feature/stats-chart-layout`)
- **Web GUI: Statystyka's charts stacked and fitted to their column.** „Gęstość prawdopodobieństwa” and „Dystrybuanta” stand one under the other at every width. All three charts are centred in their column and drawn at its width, at most 880 px, so their text keeps its size: the probability plot in the ratio 760 : 432 and at least 260 px high, the other two in 760 : 300 and at least 200 px (at most 500 and 347 px), with the small layout below 500 px. They are redrawn when the column's width changes and never scroll sideways. The chart kit's spec gained `fit: {ratio, minHeight}` for this (`web/src/charts/chart.js`); a wide chart of fixed size still scrolls on a phone below 560 px.
- **Web GUI: no axis starts below 0**, in every chart of every section: the linear and time domains of the chart kit (`niceDomain`, `timeDomain` in `web/src/charts/scale.js`) never begin below 0, a given minimum included. The series of a chart are clipped at its frame (an SVG clip path that spills 4 units over it, so an edge keeps its stroke), and the readout steps over the points inside it only.
- **Web GUI: Statystyka's axis ranges depend on the result only**, never on the combinations shown, ticked or active, so a filter or a click on a row moves no axis (`axisRanges` in `web/src/sections/statystyka/charts.js`). Q of the density and distribution-function charts runs from 0 to a rounded value above the largest annual maximum or the median over the combinations of Q at p = 1%; Q of the probability plot the same at the rarest p of its curves (0,1%), and its Gumbel axis spans the probabilities of the run and of the maxima; F is 0 to 1. The density's frame is 1,25 times the median of the largest densities of the combinations with an AIC (a combination without one has a bound among the maxima, where its density often spikes), so a spike at a distribution's bound is clipped instead of flattening the other curves; the (i) text of the probability plot says so. This replaces D3's density scaled to the active distribution. A quantile beyond the frame is not marked on the plot.
- **Web GUI: „Zakres osi”** under each chart of Statystyka: the limits „od” and „do” of its axes (T of the Gumbel axis and Q of the probability plot, Q and f(Q) of the density, Q of the distribution function), typed, checked (a number, at least 0, T above 1 year, „od” below „do”; a limit left out is marked with the reason) and stored with the inputs; an empty limit is the automatic end, shown as its placeholder, and „Auto” restores the chart's automatic ranges. Nothing is computed again.

#### Live recompute in Statystyka przepływów (the author's review of 2026-11-06; plan `2026-11-06-flow-statistics-feedback`, D9; branch `feature/stats-live-recompute`)
- **Web GUI: the result follows every change, „Oblicz” is gone**, as in Hydrogram zlewni (plan `2026-11-02-hydrolog-gui`, D13): 250 ms after the last change of valid inputs sent (the series, a file and its columns, the periods) the tables, the curves and the homogeneity tests run, „Liczenie…” after 150 ms, an older request aborted and only the newest applied (`web/src/recompute.js`, moved from `sections/hydrogram/` and shared by both sections). Invalid inputs run nothing and keep the last result („Dane niepełne”); an empty required field says so once touched, so a first visit runs nothing. The filters, „Zakres osi”, the active and ticked rows and „Wyróżniony w wynikach” only change the view. The state under Dane is Hydrogram's (`calc-state`); on a phone Wyniki no longer opens by itself after a run.

#### TR-55 rows for Hydrograf's land covers (Hydrograf's request of 2026-11-08, its ADR-075; branch `feature/tr55-rows`)
- **Three covers of USDA-SCS (1986) TR-55, 2nd ed.** in `hydrolog.runoff.LandCover`, `get_cn` and the choices of `cn lookup`, `cn list` and `cn range` (CLI, MCP, GUI): `paved_road_open_ditches`, streets and roads paved with open ditches, right-of-way included (table 2-2a, p. 2-5: A 83, B 89, C 92, D 93); `residential_quarter_acre`, residential districts of 1/4 acre lots, 38 % impervious (table 2-2a, p. 2-5: 61, 75, 83, 87); `woods_grass`, the woods-grass combination of orchards and tree farms (table 2-2c, p. 2-7: poor 57, 73, 82, 86; fair 43, 65, 76, 82; good 32, 58, 72, 79). The module and the cover descriptions cite the table and page of each new row and of the water row.

#### Positions and descriptions in the network (the author's request of 2026-11-10; [ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md); plan `2026-11-10-network-editor`, stage E1; branch `feat/network-editor-e1`)
- **`description` and `position` in `hydrolog-network/1`** (optional, the version stays `/1`): every node, of any type, may have `description`, plain text for people (1 to 500 characters, not blank, no control character but the line feed; `details.reason` `type`, `empty`, `too_long` with `max_length` and `length`, `control_character` with `character`), and `position`, `{"x": ..., "y": ...}`, the cell of the node in the schematic's grid (whole numbers from −1000 to 1000, these two keys only; `2.0` is read and written as `2`; `type`, `unknown_field`, `missing_field`, `minimum`, `maximum`, with `details.field` `position.x`...); always with `details.node_id`. The document may have its own `description` at its top (no `node_id`). The canonical form writes them after the fields of the kind, `description` then `position` (at the top: `schema`, `name`, `description`, `timestep_min`, `rainfall`, `nodes`); a document without them is written byte for byte as before. Neither changes a computation: the result, the tables and `describe()` are the same, and `NetworkResult` does not carry them. The reader stays strict: a misspelt field is still `unknown_field`, and a Hydrolog without this change refuses a document with the new fields. `route network`, `route schematic` and the MCP tools pass them to the library (a file: `data_error` with `details.path`; inline: `validation_error` with `details.option` `network`); no catalog option changed.
- **Python API** (`hydrolog.routing`): `Position(x, y)` (a `NamedTuple` of two integers), `MAX_DESCRIPTION_CHARS` (500) and `MAX_POSITION` (1000); `Node.description`, `Node.position` and the checked copies `Node.with_description(text | None)` and `Node.with_position(Position | (x, y) | None)`, on the base class, so every registered node type carries them; `RoutingNetwork(..., description=None)` and its attribute `description`; `NodeEntry` and `check_description`, `check_position`, `position_from_document`, `position_to_document` in `hydrolog.routing.network`.
- **The given layout and rule D** ([ADR-0013](decisions/0013-network-schematic.md) amended): `RoutingNetwork.schematic()`, `route network --schematic` and `route schematic` draw the nodes at their positions when every node has one and no two share a cell (moved together so that the smallest `x` and `y` are 0; the lines ranked and the labels placed as in the computed layout, `main_stem` honoured). Every edge follows rule D (`hydrolog.routing._layout.edge_route`) from the positions of its two nodes: straight when `dx` or `dy` is 0; for `dx > 0` a sideways leg of `|dy| − 1`, one 45° step and the row into the lower node; for `dx < 0` a 45° leg of `min(|dx|, |dy|)`, then straight. Rule D gives every edge of the computed layout (5,040 random trees, 216,720 edges; a property test keeps it), so stored computed positions draw ADR-0013's picture exactly. A given picture may cross itself. `hydrolog.routing._layout.given_layout` is the given layout.
- **Notice `positions_ignored`** (warning; `reason` `partial` or `shared_cell`, `node_id`): positions on some nodes only, or two nodes on one cell, give the computed layout and name the first node at fault (`Positions ignored at node 'R3' (partial): the layout is computed`). `hydrolog._warnings.PositionsIgnored` (a `HydrologWarning`) in `LIBRARY_WARNINGS` and `NOTICES`; `route network` (with `schematic`) and `route schematic` return it as a notice; the GUI has its Polish text („Węzeł R3: nie ma położenia, choć inne węzły je mają; schemat ułożono automatycznie, bez podanych położeń węzłów.”).
- **`hydrolog-network-schematic/1`** (optional fields, the version stays `/1`): `layout` (`given` or `computed`, after `has_result`, always written) and a node's `description` (after `label`); the network's own description is in neither the schematic nor the result. `schematic_svg` puts a node's description in its tooltip, on the line after `id (type)`, escaped.
- **`hydrolog.testing`** (DEV-10.6): `placed(node, *, description=None, position=None)` adds the fields to a node of the builders, checked by the library, and `network_document(..., description=None)` gives the network its description.
- **JSON Schemas regenerated:** `hydrolog-network-1.schema.json` has `$defs.description` and `$defs.position`, both in every node branch, and `description` at the top; `hydrolog-network-schematic-1.schema.json` has `layout` and a node's `description`.
- ADR-0023 records the decisions, with „Amended by” lines in ADR-0010, ADR-0012, ADR-0013 and ADR-0014; the browser's structure checks of the editor that it decides come with stage E3.

#### The canvas of Sieć (plan `2026-11-10-network-editor`, stage E2; branch `feat/network-editor-e2`)
- **„Schemat sieci” is a canvas** drawn from Sieć's own inputs (`web/src/sections/siec/editor/canvas.js`, inline SVG without a library), turned as before (the sources at the top, the outlet at the bottom): every node on the cell of its position, every edge by rule D as the library draws it, the main stem and the tributaries ranked as the library ranks them, each label on the side of its node without a tributary. The pure parts are `editor/geometry.js` (rule D, the cells, free cells, provisional rows, the lines, the labels) and `editor/edits.js` (`moveNode`, `placeAll`). It replaces the picture of `route schematic` (`siec/schematic.js` and `siec/schematic-view.js` are removed); `route schematic` still checks the network 300 ms after a change of its structure, and its refusal stands above the canvas.
- **Moving a node:** a drag (a press that moves 4 px or more; the node follows the grid, and a taken cell refuses the drop), Shift with an arrow key (one cell), or „Przesuń” and a click on a free cell. A move changes no data: the result stays current. The positions are kept with the inputs (a reload keeps them), sent with the document to `route network` (so its `--schematic` draws the same picture) and saved by „Zapisz sieć”; a saved file reopens as it was placed.
- **„Uporządkuj”** puts every node where Hydrolog lays it out (`route schematic` of the document without positions); it works once Hydrolog can read the network.
- **Opening a network:** a document with a cell of its own for every node opens as placed. Without positions the network takes Hydrolog's layout as soon as Hydrolog can read it, and stands until then in provisional rows by its longest distance from a headwater, marked „Układ tymczasowy”. A node without a position, or on a cell a node before it took, goes to the free cell nearest a neighbour, an invalid position is dropped, and the note of the load names them. Inputs stored before the canvas are laid out the same way (the key stays `hydrolog-gui/siec/2`).
- **Keys and accessibility:** while a node of the canvas has the focus the arrows go to the nearest node in their direction (the canvas is one stop of the tab order), Enter or Space chooses it, Shift with an arrow moves it, `+` and `−` zoom and `?` shows the keys („Skróty” lists them; the canvas names them in its description); Esc ends a move. A polite live region says each move and why a move was refused („Nie można przesunąć B: to pole zajmuje R_A.”). Nodes take touch drags; a node's target is its halo, 40 px across at 100 %.
- **Zoom:** „−” and „+” (25 to 200 %) draw the picture smaller or larger and the card scrolls it; „Dopasuj” fits the whole picture to the card.
- **PNG:** the export of the canvas leaves out the selection and the marks of editing; `toPng` reads the picture's styles under the class `exporting`.

#### The editing of Sieć (plan `2026-11-10-network-editor`, stage E3; branch `feat/network-editor-e3`)
- **„Nowa sieć”** (step 1, beside „Plik sieci…” and „Wczytaj z Hydrografa”) opens an empty canvas with a hint. The palette of the canvas adds the five elements („Zlewnia”, „Odcinek”, „Zbiornik”, „Złącze”, „Wylot”; a subcatchment is also HEC-HMS's source): dragged onto a cell, clicked and then a free cell clicked, or Enter on the palette, which places it beside the chosen node; `D` on a node adds an element above it as its inflow, and „Dodaj węzeł” in step 2 beside the chosen node. A new element takes the first free id `Z1`, `R1`, `ZB1` or `J1`, the outlet `OUT`. On a phone the palette is the menu „Dodaj element”.
- **Links:** a drag from a node's handle (the dot below it) onto the node it flows into, `P` and the arrows among the nodes it may flow into, „Połącz z…” of the node menu and a click, or „Odpływa do” in „Dane”; a node's one downstream link moves when it is linked anew. While a link is dragged its target shows „✓” or „⊘” and the live region says why; a cycle, an inflow into a subcatchment and a link out of the outlet are refused with the reason, and a second inflow into a reach, a reservoir or the outlet offers „Wstaw złącze” (a junction above it takes both inflows and flows into it; one step) or „Anuluj”. A link goes by a click on it and Delete, `O`, „Odłącz” or „Odpływa do: brak”.
- **Removing, renaming, describing:** Delete, „Usuń” or „Usuń węzeł” removes a node with its links, and „Usuń i połącz” links its one inflow to the node below it. The id (F2, „Zmień id”, the field in „Dane”) is checked as it is typed, as the library checks it (`invalid_id`, `reserved_name`, `duplicate_node` without regard to case), and changes on Enter or when the field is left: every `from` follows, and a subcatchment that read its column of the inflows file by its id keeps that column (`value_column`). „Opis” describes a node and „Opis sieci” the network (plain text of up to 500 characters with line breaks, checked as the library checks it); a node's description stands in its tooltip and accessible name and in the new column „Opis” of „Tabela węzłów”, beside „Odpływa do”. Descriptions are kept with the inputs, sent and saved; neither a description nor a move marks the result stale.
- **The node menu** (a right click, a long press, Shift+F10 or the Menu key, „Węzeł…” in the toolbar): „Dodaj dopływ…”, „Połącz z…”, „Odłącz”, „Przesuń”, „Zmień id”, „Usuń”, „Usuń i połącz”.
- **The problems of the structure** are checked in the browser after every edit (`editor/graph.js`, a pure module), every problem at once, with the library's reasons: `empty`, `invalid_id`, `reserved_name`, `duplicate_node`, `unknown_upstream`, `duplicate_upstream`, `upstream_count` (by the `from` bounds of the schema), `several_downstream`, `cycle`, `no_outlet`, `several_outlets`, `outlet_has_downstream` and `disconnected_node`. A node with a problem has „!” beside its glyph and the problem in its tooltip and name, the links of a cycle are dashed, and the list „Problemy sieci (n)” above the canvas names every problem, a node's incomplete values and Hydrolog's refusal, each item choosing its node; the status badge says „Dane niepełne” as for the values. Once the browser finds nothing, Hydrolog checks the network (`route schematic`) 300 ms after every change of what it computes, and its refusal marks its node. An edge that runs through another node is a hint (a dotted ring and „Wskazówki”), not a problem. A test runs a corpus of one-problem documents through the browser's checks and `RoutingNetwork.from_document`.
- **Undo and redo:** „Cofnij” and „Ponów” (Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y on the canvas and its toolbar; a text field keeps the browser's own undo) go through up to 100 steps kept in memory (`editor/history.js`): every edit is one step, moves of one node by keys within 1 s are one, and a value is one step when its field commits; opening, starting or clearing a network starts a new history, and a reload keeps the network but not its history.
- **„Zapisz szkic”:** a network with problems is saved as the same `hydrolog-network/1` file (the button „Zapisz sieć” says „Zapisz szkic” then); the toast says that `route network` refuses it until the problems are fixed, and the GUI reopens it as it was saved.
- **Questions before a loss:** „Wyczyść” and „Nowa sieć” ask first when the network changed since it was opened or saved.
- **Keys:** `D`, `P`, `O`, Delete, F2, Shift+F10 and the Menu key act while the canvas has the focus, and „Skróty” lists them with the others.
- The GUI plan's erratum of 2026-11-10 supersedes its points that the structure of a network is shown, not edited (D18, S4).

#### The hand-off in the editor of Sieć (plan `2026-11-10-network-editor`, stage E4; branch `feat/network-editor-e4`)
- **„Wczytaj z Hydrografa” in Sieć** opens every network hand-off there, also one subcatchment with its outlet (which still opens in Hydrogram zlewni from the other sections).
- **„Dodaj zlewnię z Hydrografa”** (step 1 of an open network) adds the subcatchments of a hand-off (a file or the clipboard, checked as „Wczytaj z Hydrografa” checks it) to the network, unconnected and as one step of the history: an id the network has takes its stem with the first free number (`Z1` becomes `Z2`), each stands on the free cell right of the top row, described by its own description or else the hand-off's subject; the hand-off's outlet and its other nodes stay out and are named. The network keeps its time step (a network without one and without nodes takes the hand-off's) and says so, a subcatchment's own rainfall comes with it, and the hand-off's rainfall at its top becomes the node's own when the network's differs. Where the subcatchment came from (the hand-off's producer, moment, subject and provenance) stays with it in the browser and stands in „Dane”; the written hand-off keeps the provenance of the network it was opened from, as before.
- **A network of hundreds of nodes edits without delay:** the targets of a link (`editor/graph.js` `linkVerdicts`, one pass instead of one per target), the places of the labels (`editor/geometry.js` `crowdIndex`), the structure's problems and the nodes' words (kept per `structureKey`, so a move recomputes none of them) and the nodes and lines of the canvas and the rows of the node list (drawn again only when they change) no longer grow with the square of the network; the panels' default widths are read from the CSS once per window width instead of on every render. At 300 nodes a move, a link and an added element paint in about 35–90 ms instead of 60–190 ms.

#### The guide and the docs of the network editor (plan `2026-11-10-network-editor`, stage E5; branch `feat/network-editor-e5`)
- **The guide (`web/instrukcja/`), chapter 03 „Sieć i trasowanie”:** the section is an editor, started by „Nowa sieć”, a file or a hand-off; „Elementy sieci” (the palette's five elements beside HEC-HMS's: Subbasin and Source, Reach, Reservoir, Junction, Sink, and Diversion, which Hydrolog lacks, with the inflows each takes and the ids of new elements); „Budowanie sieci” (adding, linking with „✓” and „⊘”, „Wstaw złącze”, unlinking and removing, ids and descriptions, moving and „Uporządkuj”, „Problemy sieci”, „Cofnij” and „Ponów”, „Zapisz sieć” and „Zapisz szkic”, „Dodaj zlewnię z Hydrografa”); „Klawisze schematu” (every key of „Skróty”). The worked example's table gains the flow paths of A and B, with which the table alone builds the same network from „Nowa sieć” and gives the same 19.1 m³/s at 2:25 h; the text says how.
- **The guide, other chapters:** „Wczytaj z Hydrografa” in Sieć and „Dodaj zlewnię z Hydrografa” (07), Sieć on a phone and the positions and descriptions kept in the browser (08), „Problemy sieci (n)”, „Nie można…” and „Uporządkuj” before Hydrolog can read the network (09).
- **The guide's pictures:** `siec.png` taken again (the canvas with its palette and tools, the chosen node's id, description and „Odpływa do”), `telefon.png` taken again on Sieć (the canvas's tools on a 390 px phone in the dark theme; it showed Hydrogram zlewni's results), and the new `siec-edycja.png` (a problem on the canvas and „Wstawić złącze?”), all 256-colour PNG.
- **Docs:** [USAGE.md](USAGE.md) section 8 „Building a network in Sieć” (elements, editing, the structure checks with the library's reasons, positions, files) and a pointer from the document's fields; the sections of the GUI start empty (the text still said they open with an example). [README.md](../README.md): the paragraph on the GUI. [PRD.md](PRD.md): US-G02 revised, US-G09 „Building a network as in HEC-HMS”. [SCOPE.md](SCOPE.md): the GUI edits networks and checks their structure; a background map, diversions and multiple selection are out. [INTEGRATION.md](INTEGRATION.md): the schematic keeps `/1` for its optional fields (it said every change of the layout takes a new version), Sieć keeps positions and descriptions in what it writes, and a hand-off read or added in Sieć.

#### Nash by Lutz from the watershed (plan `2026-11-10-network-wizard`, stage W1; [ADR-0024](decisions/0024-nash-by-lutz-from-the-watershed.md); branch `feat/network-wizard-w1`)
- **`nash_estimation`** (`lutz`): an option of `hydrograph generate` and `report generate` (`--nash-estimation lutz`) and a field of the `curve-number` runoff of `hydrolog-network/1` (`CurveNumberRunoff(nash_estimation=...)`, `NASH_ESTIMATIONS` in `hydrolog.routing`), optional, `/1` kept: Nash's n and K estimated by Lutz from the watershed in the same run, instead of `nash_n` and `nash_k_min`. The inputs are the fields the method defines (`hydrolog._ranges.NASH_INPUTS`, `WatershedParameters.nash_parameters("lutz")`): L and J of the main stream from the divide, the longest flow path (`flow_path_length_km`, `flow_path_slope_m_per_m`), `Lc_km`, `manning_n`, `urban_pct` and `forest_pct` (0 when missing). Reasons: `not_applicable` (another model, or no watershed), `conflict` (with `nash_n` or `nash_k_min`), `required` on `nash_n` (Nash with neither), `missing_field` with `details.method` `lutz`, `maximum` on `Lc_km` longer than the flow path. One run equals `uh nash` with those inputs followed by `hydrograph generate` with its n and K; a network node with the field equals the command.
- The result of `hydrograph generate` has `nash_estimation`, its `uh_parameters` the estimate; `HydrographRun` keeps `nash_estimation` and `lutz`; `report generate` prints Lutz's inputs and steps; the node's `describe()` lists `nash_estimation` (given) and `nash_n`, `nash_k_min` (computed); `typical_ranges` of both commands serve Lutz's area (method `lutz`). An estimate is not checked against the ranges of given n and K (`HydrographGenerator` Nash `uh_params` take `estimated`). A catalog example of `hydrograph generate` with Lutz; schemas regenerated.
- Docs: ADR-0024 (amends ADR-0012), [COMPUTATION_PATHS.md](COMPUTATION_PATHS.md) 3.2.7, [USAGE.md](USAGE.md), [INTEGRATION.md](INTEGRATION.md), the GUI plan's erratum of D13, the wizard plan's answers to its questions Q1 and Q2.

#### Nogat's GUI kit: the app menu and the shared hand-off (Nogat ECO-058, plan `2026-11-12-gui-links-and-handoff`, step 4; [ADR-0027](decisions/0027-nogats-gui-kit-the-app-menu-and-the-handoff.md); branch `feature/nogat-kit`)
- **Web GUI: „Aplikacje”**, Nogat's app menu `<nogat-app-menu>` (DEV-15.4) in the top bar left of the theme switch: the GUIs of the deployment's table `gui` of `[nogat]` in `nogat.toml` (e.g. `gui = { hydrograf = "http://127.0.0.1:8080/", archiwista = "/archiwista/" }`), each with its mark, a line of what it does and a tab of its own (`nogat-<name>`), Hydrolog marked as the current one; a sheet on a phone. Without another GUI in the table it is not drawn; there is no default. `GET api/session` gives the table as `gui` (`null` without it), read at every request (`hydrolog._settings.gui_addresses`), so a changed address needs no restart.
- **Nogat's kit 0.1.0 in `web/nogat/`** (`nogat-app-menu.js`, `nogat-app-menu.css`, `nogat-handoff.js`, `nogat-kit.json`), copied byte for byte from Nogat `7786271` (DEV-15.6), with Obserwator's mark beside the other four; the contract test checks the kit against `nogat-kit.json` and every file of `web/nogat/` against one of the two manifests.
- **The hand-off through the kit** (DEV-15.5): the file, the clipboard, the download and the envelope's check are `nogat-handoff.js`'s, the same in every GUI. The payload's check stays Hydrolog's (`handoff/validate.js`: Unicode `\w` as in Python, the problem inside the branch of a `oneOf`), now worded by the kit's texts with Polish numbers; the domain checks are unchanged.
- Copies of the standard (`schemas/nogat/`) from Nogat `7786271`: `error_registry.json` names the standard 1.0 (`_errors.py` regenerated, `STANDARD_VERSION`); the agent schemas and `handoff-1.schema.json` unchanged. `tokens.css` names `7786271` (its tokens unchanged).

### Changed
- **The documentation checked against the code of 2026-11-14** (the author's request): README, `docs/USAGE.md`, `INTEGRATION.md`, `COMPUTATION_PATHS.md`, `PRD.md`, `SCOPE.md`, `PROGRESS.md`, `DECISIONS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md` and the agent guide describe `develop` as it is: the providers' lines of Nogat DEV §20 (Hydrolog writes S, P, PS, PP, M, C and CP and the terms lines RD, RH and RK, carries every other line of its inputs, GUGiK's G, ISRIC's SG and ČÚZK's Z among them, verbatim and writes none of those itself; an HSG raster carries no line), Nogat's kit 0.7.0 with its admin panel and the corrected regulamin 1.0, Nogat's logs of `gui serve`, the 62 commands in 17 groups with the station analyses, the members the cleanup of dead code removed, and the Nogat standard 1.0 (its drafts were called 2.0 and 2.1). `AGENTS.md` names the envelope's `attribution` and `terms_notice`; the ADRs amended since 2026-11-13 name their amending ADR at the top (DOC-8.1); `PROGRESS.md` gives the merges into `develop` and the deployment of 2026-11-14.
- **Web GUI: the info texts by Nogat DEV-15.14** (ECO-069, the author's request of 2026-11-14): the 28 explanations (i) of `labels/info/*.js` give a definition, the formula with its symbols and units, how to read the value and the sources (literature, norms, the data provider), in at most about 400 characters without the formula and the sources; command, option, field and program names, plan steps and `docs/…` are gone from them. Their longer method detail moved into the guide's new chapter 12 „Metody obliczeń” (`instrukcja/#metody`), which each explanation links as „Więcej w instrukcji” (its `guide`, opened in a new tab); a contract test keeps every such link on an id of the guide. Corrected on the way: Snyder's shape (the gamma curve through the peak), Nash's path from tc (removed in 1.0.0.dev0) and the step of tc in Hydrogram zlewni.
- **Breaking (`gui serve`).** The server no longer prints `Hydrolog GUI: <url>` on standard error: its first line there is the lifecycle record `start`, whose `settings.url` is the address, written once the socket listens. The answers carry no `X-Request-Id`, the logger `hydrolog.gui.access` and `hydrolog.gui._public.ACCESS_LOGGER` are gone, and the access log is a file (ADR-0037).
- **The regulamin 1.0 corrected in place** (Nogat plan `2026-11-13-terms-fix`, ECO-068; kit 0.6.2, copied byte for byte from Nogat `5703c53`): § 8 ust. 3 says what the logs of ADR-0037 keep (no IP address, the access and error logs gone after 14 days, start, stop and error messages without request data, the kind of program instead of the browser's name); § 8 ust. 5 names the map layers of other providers; the history links the template on Nogat's `develop`; the blocks Hydrolog lists (`imgw`, `pmaxtp`, `chmi`) are unchanged and a test keeps the filled page to them. The number stays 1.0 (the author's decision of 2026-11-13). `<nogat-sources>` also shows the short forms GK, SK and ZK of the new lines G, SG and Z, which Hydrolog writes into no product itself (it carries them from its inputs).
- **The providers' terms are linked, not restated** (Nogat ECO-065, kit 0.6.0; [ADR-0036](decisions/0036-link-the-providers-terms-instead-of-restating-them.md)). The lines H („Dane pochodzą z serwisu hydrologicznego IMGW-PIB …”) and N („Dane IMGW-PIB można wykorzystywać nieodpłatnie …”) are gone from `hydrolog._attribution` (`IMGW_HYDRO` and `IMGW_TERMS` removed) and from every product; `terms_notice` holds one link per terms that apply, in the order RD „Regulamin danych IMGW-PIB: …”, RH „Regulamin serwisu hydrologicznego IMGW-PIB: …”, RK „Regulamin danych PMAXTP: …” (none for ČHMÚ). A line Hydrolog does not know is a terms line in the form „Regulamin <whose terms>: <address>”. Lines written before (an input's columns or fields, the option `attribution`, an `ATTRIBUTION.txt` merged on a later write) are read as the current ones: H names hydro.imgw.pl, an old „Regulamin: <address>” of RD, RH or RK becomes the new line, N and other „Regulamin: …” lines are dropped. `GET api/session` gains `retired_lines`, by which the GUI shows a depth it kept or an older hand-off's lines as the current ones. The regulamin is filled without the block `imgw-terms`; Nogat's kit 0.6.0 (`nogat-terms.md`, `nogat-terms.html`, `nogat-sources.js`, `nogat-kit.json`) and `handoff-1.schema.json` are copied byte for byte from Nogat `b29eada`. The guide no longer summarises IMGW-PIB's terms, and `eksport.png` is retaken.
- **Breaking (the GUI's private API).** „Zgłoś uwagę” has one text field and „Nie wpisuj danych osobowych…” with the operator's address; no contact field and no diagnostics. `POST api/feedback` takes `{message, context}` only (`view`, `station`, `parameters`, `app_version`) and refuses any other field (`validation_error`, `unknown_field`); the admin page shows the context. The file `feedback.sqlite3` goes to version 2 (`context` instead of `contact`, `page_url`, `user_agent`, `diagnostics`; `secure_delete`); a file of version 1 is first copied whole to `feedback-v1-<UTC time>.sqlite3` beside it, for the operator to decide on (ADR-0034).
- **Breaking (the GUI's private API).** No cookie: the session is named by the header `X-Hydrolog-Session`, which the page keeps in its memory; it ends when the page is closed or reloaded (`DELETE api/session`) or after an hour idle (was 12 hours). Downloads of the session's files go through `fetch`. Links that leave the app open a new tab (ADR-0034).
- GUI user guide: refreshed the Hydrograf network hand-off chapter against a live network (confluence and point IDs, outlet `O`, headwater and intermediate subcatchments, node provenance), corrected the statistics file action and retook the changed network, statistics and command-catalogue screenshots as indexed PNGs; the worked example fixture and its numbers remain unchanged.

- Obserwator pin (extra `pmaxtp`, `[tool.uv.sources]`) moved from candidate-1 `1ee5457` to commit `f9f4ee7927ba520d3e82d3e289872090ae24e2ec` of Nogat's release set candidate-2; `uv.lock` updated.

- GUI: the cards „Eksport” and „Przekazanie” of the panel Wyniki (Hydrogram zlewni, Sieć; „Eksport” also in Statystyka) are collapsed by default; „Przekazanie” opens itself when a received hand-off brings a producer's result to compare.

- GUI, Sieć: a reach `route network` refuses with `unstable_timestep` is explained by the error's details instead of always „krok czasowy jest za długi”. A reach Muskingum-Cunge cannot route at any time step (too short or too flat, e.g. Hydrograf's 50 m reach with the minimum slope) says so, with its length, celerity and diffusion length, and that a change of the step does not help; a step that would need too many ordinates says to lengthen the step; every variant says where the network's step is (step 1 „Sieć”, field „Krok czasowy”, empty: the default). Below the error a reach gets „Zamień na opóźnienie (lag) X min”, X = max(1, round(length / celerity / 60)) from the error, which computes the network again, or a typed lag where the error gives no travel time, and „Zamień na zbiornik (level-pool)”, which waits in „Dane” for the storage table. The library is unchanged. Since ADR-0026 (below) such a reach is routed, so its words and the lag of the travel time are gone; the typed lag and the level-pool stay for the other refusals.

- GUI, Sieć: the origin of a subcatchment Hydrograf hands off as `element: "headwater"` reads „dopływ” (with its point: „dopływ do punktu P2”, „dopływ do ujścia przy punkcie P2”) instead of „zlewnia górna”, the words Hydrograf now uses for it (its ADR-080, amended 2026-11-11: two kinds for the person, dopływ and przyrzecze; which branch of a junction is the headwater follows the larger upstream area and changes nothing in the computation). The hand-off's `element` values stay. The guide's section „Sieć z Hydrografa i pochodzenie węzłów” says so.

- Muskingum-Cunge (`MuskingumCungeReach`, `route muskingum-cunge`, a `muskingum-cunge` reach of `route network`): a reach for which no division of the reach and of the time step into at most 100 parts keeps the weights non-negative (typically its diffusion length `D = Q / (T S0 c)` is long against `c dt`: a flat, short or narrow reach) is no longer refused with `unstable_timestep`. It is routed as `n = L / D` (rounded, at least 1) linear reservoirs of `K = L / (n c)` with the exact kernel of the cascade, which keep the travel time of the diffusion wave and nearly its spread, with the new warning `diffusion_dominated` ([ADR-0026](decisions/0026-a-reach-without-a-muskingum-cunge-grid.md), amends ADR-0008). Its `parameters` are the hydraulics of the reach, `diffusion_length_m`, `scheme` `linear_reservoir`, `n`, `k_min` (one reservoir) and `lag_min` (`L / c`); a reach that a grid routes gives the same result as before, bit for bit (6,000 random reaches). Against the linear diffusion wave the peak is from -7.8 % to +0.6 % in the cases of the ADR, the volume the same. Hydrograf's network of the Nysa Szalona (the author's report of 2026-11-11: 60 mm in a 120 min block, n 0.05 and a 5 m bottom, 5 min step), refused at R2 before, routes with an outlet peak of 239.85 m3/s; only a grid beyond a million ordinates is still refused. `ReachRun.parameters`, `RoutingResult.parameters` and `RouteResult.parameters` are typed `dict[str, ParameterValue]`.

- `route muskingum` (`MuskingumReach`): the refusal of a `subreaches` outside the window gives the steps on which that number fits, `details.minimum_timestep_min` (`2KX / N`) and `details.maximum_timestep_min` (`2K(1 - X) / N`), and its hint names them.

- GUI, Sieć: a Muskingum-Cunge reach without a grid no longer stops „Oblicz sieć”: the network computes, the reach chosen in „Wyniki” says „Odcinek R2 trasowano jako zbiornik liniowy o K = … min, bo …” with its length, celerity and diffusion length, its parameters show „Schemat obliczeń: zbiorniki liniowe”, and the notices name the node. `unstable_timestep` reads by its details: a step too short for the sub-reaches given to Muskingum (with the steps that fit them and the sub-reaches that fit the step), a step that would need too many ordinates, otherwise a step too long; the typed lag and the level-pool storage stay below those refusals, while „Zamień na opóźnienie (lag) X min” of the travel time and the words that no step could help, both of a reach without a grid, are gone. The guide's „Płaski albo krótki odcinek” says so; the e2e fixture `handoff_hydrograf_network_nysa_szalona.json` (the author's hand-off) replaces `handoff_hydrograf_network_short_reach.json`.

- GUI, the hand-off (ADR-0027): „Do schowka” is „Kopiuj do Hydrologa”, as in Hydrograf and Archiwista; where the browser gives no clipboard (a plain-HTTP address other than localhost) or refuses it, the text goes selected into a field below the buttons for Ctrl+C (Hydrolog used to try the deprecated `document.execCommand("copy")` there, or report a failed copy when the Clipboard API refused). The file is named after the hand-off's subject by the kit's rule (as before for every subject but one with a DEL character). After a copy or a download the status reads „Skopiowano przekazanie do schowka.” or „Zapisano plik „…”.”; a refused envelope is worded by the kit („producer.tool: niezgodne ze wzorem ^[a-z][a-z0-9]*$”, „To nie jest przekazanie nogat-handoff/1.”), and a payload's problems in the kit's words („za krótkie: co najmniej 1 znaków” where it was „nie może być pusty”). The guide's chapter 07 and its picture `eksport.png` follow.

#### Breaking changes
- **Breaking - CLI:** the old syntax (v0.4.0-v0.7.0) was removed without aliases; commands now have the form `hydrolog <group> <command> --option value` with the catalog option names (`--kebab-case`, unit in the name). Migration examples: `hydrolog scs --cn 72 --precipitation 50` → `hydrolog scs effective --cn 72 --precipitation-mm 50`; `hydrolog tc kirpich --length 2.5 --slope 0.02` → `hydrolog tc kirpich --length-km 2.5 --slope-m-per-m 0.02`; `hydrolog uh scs --area 45 --tc 90 --timestep 10` → `hydrolog uh scs --area-km2 45 --tc-min 90 --timestep-min 10`; `hydrolog cn lookup --cover forest` → `hydrolog cn lookup --land-cover forest`. The `--csv` export does not exist; `--json` gives the full result (the `hydrolog-result/1` envelope).
- **Breaking - changed numerical results** (bug fixes, see "Fixed"): quantiles of `LowFlowAnalysis.fit_fisher_tippett()`, the Clark unit hydrograph for a duration D that is not a multiple of the time step, `calculate_monthly_statistics()` for a month with a single value (`NaN` instead of the interval `[mean, mean]`), the content of the calculation report and (since the pre-release review) the concentration time `WatershedParameters.calculate_tc()` for the FAA, Kerby and NRCS methods, the `HydrographGenerator` hydrograph with the Snyder model and `hydrograph generate`/`report generate` with `cn` given alongside a watershed (NRCS concentration time), as well as annual maxima and minima (`stats flood-frequency`, `stats low-flow`, `LowFlowAnalysis`) for series with incomplete hydrological years, the `empirical` block in `stats low-flow` (non-exceedance convention) and the default H₀ start of the rating curve.
- **Breaking - exception types changed:** validation exceptions are now `InvalidParameterError` (also a `ValueError`) instead of a bare `ValueError` (`WatershedParameters.calculate_tc()`, `calculate_monthly_statistics()` for a month without values); `RatingCurve` raises `RatingCurveFitError` (a `CalculationError` and, for backward compatibility, also an `InvalidParameterError`). Code with `except ValueError` or `except InvalidParameterError` works as before.
- **Breaking - `WatershedParameters.calculate_tc()` for FAA and Kerby requires `overland_length_km` and `overland_slope_m_per_m`:** both methods compute overland flow time, so they no longer substitute the channel length and slope (they used to compute silently with them, also for watersheds without overland-flow fields). A watershed without these fields ends with `InvalidParameterError` (`details.reason` = `missing_field`, `details.missing`, hint in `hint`: `kerby_kirpich` or `kirpich` for a watershed with a channel); this also applies to `tc watershed`, `hydrograph generate --tc-method` and `report generate --tc-method`.
- **Breaking:** `HydrologyReportGenerator.generate()` raises `InvalidParameterError` when `result.unit_hydrograph_result` is `None` (the report documents the unit hydrograph used in the calculation, and `HydrographGenerator.generate()` always returns it).
- **Breaking - operation ids and MCP tool names (since 1.0.0.dev0)** gain the prefix `hydrolog_` (`tc_kirpich` → `hydrolog_tc_kirpich`); the CLI command names (`tc kirpich`) are unchanged. Migration: use the new name in MCP clients; `get_command()` and `run_command()` accept both the command name and the `operation_id`. The catalog is authored in English: `Command(summary_en=..., description_en=...)` and `Option(description_en=...)` became `summary_pl`, `description_pl`, `rules_pl` (Polish) next to the English `summary`, `description`, `rules` (ADR-0001).
- **Breaking - `commands schema` document (since 1.0.0.dev0)** has the Nogat shape `hydrolog-commands/1` (`commands[]` with `options`, `result`, `effects`, `check`, `families`, `rules`, `examples`, `errors`; Polish texts under `i18n.pl`), and the `lang` option of the `commands` group was removed: machine output (JSON, MCP, guides) is always English, the language of human output is the general `--lang` flag. Migration: read the new keys; `hydrolog commands guide` no longer takes `--lang` and renders English only (ADR-0001).
- **Breaking - result envelope (since 1.0.0.dev0):** `version` replaces `hydrolog_version`, `files` moved from the envelope into `result.files[]`, `notices[].message` replaces `notices[].text`, and `tool`, `check`, `page` and the domain `result.schema` are new. Migration: read `$.version`, `$.result.files[]` and `$.notices[].message` (ADR-0002).
- **Breaking - writing commands (since 1.0.0.dev0):** `soil hsg --output-path` and `commands guide --path` became `--output` (the `output_path` argument of `operations.soil_hsg` became `output`); an existing output file is no longer replaced silently: the run ends with `conflict` (exit 4) unless `--force` is given; `report generate` also takes `--force` and `--check`. Migration: rename the option and add `--force` where overwriting is intended; `--check` previews the plan (ADR-0003).
- **Breaking - exit codes (since 1.0.0.dev0):** `calculation_error` 4 → 13 and `forbidden` 8 → 12; exit code 4 now means `conflict`. Migration: scripts that test for 4 or 8 must test for 13 or 12 (and treat 4 as "output file exists, use `--force`") (ADR-0005).
- **Breaking - MCP server (since 1.0.0.dev0):** `--lang` was removed (the server output is always English; `hydrolog mcp --lang` and `hydrolog-mcp --lang` are rejected with `validation_error`); tools write only with `--allow-writes` (before, they wrote inside `--allow-dir`); tool names carry the `hydrolog_` prefix. Migration: remove `--lang` from the server command, add `--allow-writes` to it where files must be written, and rename tool calls; the console script `hydrolog-mcp` starts the same server (ADR-0006).
- **Breaking - extra `visualization` renamed `viz`:** `pip install hydrolog[viz]`; the missing-extra error of `hydrolog.visualization` is now `MissingDependencyError` (not an `ImportError`). Migration: change the extra in requirements and `except ImportError` into `except MissingDependencyError` (or `HydrologError`).
- **Breaking - package layout and tooling (contributors):** the package lives in `src/hydrolog` (the import path `hydrolog` is unchanged), the version is dynamic, ruff replaces Black and flake8, uv with `uv.lock` replaces the pip workflow, and the gate is `scripts/gate.sh`. Migration: `uv sync --all-extras`, then `scripts/gate.sh`.
- **Breaking - values: the CN of `water` is 98, not 100**, for every soil group (`get_cn`, `lookup_cn`, `get_cn_range`, `cn lookup`, `cn list`, `cn range`). 100 had no published source; NEH 630 ch. 9 (p. 9-1) assigns CN 98 to impervious and water surfaces. Migration: none in code; a water cover now has the retention S = 25400/98 − 254 = 5.18 mm instead of 0, so its runoff depth is smaller than the rainfall and weighted CNs with water areas are lower.

#### `hydrolog.cli` - CLI generated from the command catalog (breaking change)
The argparse parser is built from `hydrolog.catalog.data_commands()`: every catalog command
is available as `hydrolog <group> <command> --options`, with help, units and
examples from the catalog (PL/EN). The entry point is unchanged (`hydrolog.cli.main:main`).
- Options: `--kebab-case` catalog option names; numbers and lists of numbers (`--values 1,2,3`),
  strings, objects and lists of objects as JSON, boolean options `--flag` / `--no-flag`,
  negative numbers (`--option -5`); validation (ranges, choices, `one_of`) is done by the catalog,
  so the CLI, the MCP server and Python raise the same errors.
- General flags (before the group and after the command): `--json` (the `hydrolog-result/1` envelope
  on a single line), `--schema` (JSON Schema of the options without running), `--lang pl|en`
  (language of human output; settings `HYDROLOG_LANG`, `NOGAT_LANG`, `nogat.toml`, default `pl`),
  `-v/--verbose`, `-q/--quiet`, `-V/--version`. Without `--json` the result is a concise summary
  (scalars, tables, first rows of arrays, notes, written files).
- Errors: readable text on stderr, and always, as the last line of stderr, a single `hydrolog-error/1`
  line; the exit code comes from `ERROR_CODES` (2, 3, 4, 5, 6, 7, 9, 12, 13, 1; 130 after Ctrl-C,
  143 after SIGTERM). An unknown command is `not_found` (code 3) with a hint, a syntax error is
  `validation_error` (2).
- `hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]` starts the MCP server (the
  `hydrolog[mcp]` extra); `python -m hydrolog.cli` works like the `hydrolog` command.

#### Other changes
- **One set of typical ranges, each with its source (`hydrolog._ranges.TYPICAL_RANGES`; the author's decision of 2026-11-04, plan erratum; [ADR-0017](decisions/0017-typical-ranges-in-the-catalog.md)).** The formulas and models warn (`outside_typical_range`, `details.field` the input) with the bounds of one table, and the catalog serves them as `typical_ranges` of the commands that check them (`method`, `parameter`, `inputs`, `result`, `minimum`, `maximum`, `unit`, `relative_to`, `notice`, `verified`, `source`, `i18n.pl.source`) in the document of one command only: `commands schema --command`, `hydrolog <group> <command> --schema` and `command_schema()`. The pages of `commands schema` and the documents of a group or of the catalog leave them out, so a default page stays within 20,000 characters; the document of one command is one response of at most 50,000 (DOC-1.7). The option descriptions quote the table. A threshold without a published source is gone, a range the GUI held with a source moved into the library. Changed thresholds:
  - Kirpich: slope 0.002–0.15 → 0.03–0.10 m/m and new area 0.005–0.45 km² (the 7 Tennessee watersheds of Kirpich 1940, 1.25–112 acres, slopes 3–10%: Roussel et al. 2005, TxDOT 0-4696-1/-2; USDA-NRCS 2010, NEH 630 ch. 15); length 0.001–80 km removed (no source). The area is checked when a watershed gives it (`tc watershed`, `hydrograph generate`, `WatershedParameters.calculate_tc`).
  - NRCS lag: new area 0.005–24 km² (Mockus 1961, 24 watersheds of 1.3 acres to 9.2 mi², NEH 630 ch. 15); CN 50–95 kept with that source; length 0.03–30 km and slope 0.001–0.15 removed (no source).
  - Giandotti: area 100–10 000 → 170–70 000 km² (Giandotti 1934, after Grimaldi et al. 2012); length 1–300 km and elevation difference 20–3000 m removed (no source).
  - FAA: runoff coefficient 0.10–0.95 → at most 0.95 (FAA 1970, AC 150/5320-5B, table I); length 0.015–3 km and slope 0.005–0.10 removed (no source; the FAA curves end at 800 ft and the formula serves longer paths).
  - Kerby: length 0.01–0.366 → at most 0.366 km, slope 0.001–0.01 → at most 0.01, N 0.02–0.80 kept, new area at most 0.04 km² (Kerby 1959: overland flow up to 1200 ft, slopes below 1%, watersheds below 10 acres, his N table; Roussel et al. 2005).
  - Kerby–Kirpich: the method's own data instead of Kerby's and Kirpich's thresholds: area 0.65–388 km², channel length 1.6–80 km, channel slope 0.002–0.02 (92 Texas watersheds, 0.25–150 mi², channels 1–50 mi: Roussel et al. 2005; Cleveland et al. 2012), overland length at most 0.366 km and N 0.02–0.80 (Kerby 1959); the overland slope range is removed (the method's guidance gives none).
  - New: SCS unit hydrograph area at most 52 km² (Sorrell 2010, Michigan DNRE: about 20 mi²), Snyder area 26–26 000 km² (Snyder 1938, 10–10 000 mi², after Chow et al. 1988), the Lutz method's area at most 236 km² (KZGW 2017, annex 2, p. 96; `uh nash`, method `lutz`).
  - Kept, with their sources now served: Snyder Ct 1.35–1.65 and Cp 0.4–0.8 (KZGW 2017, annex 2, eq. 6.5 and 6.7), Clark R/tc 0.2–1.5 (HEC-HMS Technical Reference Manual), the CN of an AMC conversion 55–95 (Hawkins et al. 1985), the time step at most 0.25 tp (NEH 630 ch. 16), a flood frequency record of at least 30 years (KZGW 2017, `short_record`).
  - Kept to be verified: given Nash n 1–10 and K 10–200 min have no published source; they stay with `verified` false (every other range is `verified` true) and the source „Hydrolog; no published source, to be verified”, and a value outside them warns with `OutsideUnverifiedRange` (`hydrolog._warnings`), a subclass of `OutsideTypicalRange` with the same details (`field` included) and its own notice code `outside_unverified_range`, so a filter on `OutsideTypicalRange` still catches it. The option descriptions say „typically 1-10, to be verified”.
  - **Breaking:** `uh scs` returns an `OperationOutput` with notices (the area); `uh nash` with the Lutz options checks the area; `hydrolog.runoff.generator.TIMESTEP_SHARE_OF_TP` is removed (the share is the `timestep_min` range of the table, relative to `uh_time_to_peak_min`).
- `InvalidParameterError` is now also a `ValueError` (code with `except ValueError` still catches it); all Hydrolog exceptions have `code`, `details` and `hint`.
- `WatershedParameters.from_dict()` tolerates an extra `schema` key (e.g. `"hydrolog-catchment/1"`); `calculate_tc()` for an unknown method or a field missing for the method raises `InvalidParameterError` (`details.reason` = `choice` / `missing_field`, `details.missing` lists all missing fields), formerly a mix of `ValueError` and `InvalidParameterError`.
- `ClarkIUH.to_unit_hydrograph()`: `duration_min` and `timestep_min` must be positive and finite (`InvalidParameterError`).
- `HydrologyReportGenerator.generate()` has new optional arguments `ia_coefficient` and `tc_params`.
- `morphometry watershed`: when the watershed file gives `mean_slope_m_per_m` or `channel_slope_m_per_m`, the result (slopes from relief, as before) carries a `slopes_from_relief` note with both values, computed and given; formerly `tc watershed` computed with the given channel slope 0.02, while `morphometry watershed` reported 0.037 for the same file without explanation.
- The agent guide (`AGENTS.md`) describes the result of an operation function exactly: a result object with `to_dict()`/`to_json()` or `OperationOutput(result, notices, files)`; the `hydrolog.catalog` docstring and the 1.0.0 design point to the `hydrolog/operations/<group>.py` package (formerly `operations.py`).
- `LowFlowAnalysis.annual_minima()`, `fit_fisher_tippett()`, `empirical_frequency()` and `empirical_non_exceedance()` use only complete hydrological years: skipped years are reported by a `UserWarning`, and a series without a complete year is a `CalculationError` (formerly the minimum of every year present in the dates).
- `RatingCurve.fit(h0_initial=None)` and `hydrometrics_rating_curve(h0_initial=None)`: the default H₀ starting point is chosen from the data (formerly 0.0); the `h0_initial` option no longer has a default value in the command catalog.
- Tests: command catalog (CLI/Python parity for every example, catalog and envelope contracts, public API), CLI parser and rendering, MCP server (in-process client-server), serialization, settings, `hydrolog.soil` (ports of the Kartograf tests; raster tests skipped without `rasterio`), operations layer, agent guides (byte equality), error registry, concurrent file writes (`hydrolog._atomic`), regressions of the fixes from the "Fixed" section (with numbers before and after the fix).
- IMGWTools is now Obserwator (its v3.0.0; the institute IMGW-PIB and the dataset ids `pl.imgw.*` keep their names): the agent guides, the MCP instructions, the catalog texts (EN and PL), the GUI and the documentation name Obserwator and its command `obserwator` (`obserwator series export`, `obserwator stations find`; formerly `imgw`); the store marker that `output_in_store` recognises is `obserwator-store.json` (formerly `imgw-store.json`, since 1.0.0.dev0); the hand-off producer label is `obserwator`; the test fixture is `tests/fixtures/obserwator_series_export.csv` (formerly `imgwtools_series_export.csv`), used by the examples of `stats characteristic` and `hydrometrics water-level-zones`.

#### Web GUI: catalog changes ([ADR-0015](decisions/0015-catalog-additions-for-the-gui.md); branch `feature/gui`)
- Notice codes and messages (since 1.0.0.dev0): the removed pairs of `hydrometrics rating-curve` are `missing_pairs_removed` (formerly `missing_values_removed`, which stays for series); `slopes_from_relief` of `morphometry watershed` is one notice per given slope (`option`, `given_m_per_m`, `computed_m_per_m`) instead of one for both; the frequency statistics emit `small_sample`, `short_record` and `ks_test_approximate` instead of `user_warning`, with new texts; the other library warnings that were `user_warning` are `outside_typical_range`, `incomplete_years`, `unknown_hietogram_type` and `uh_model_mismatch`. Filters on `UserWarning` still catch the library warnings; filters on their old messages do not.
- `Command.check` follows the presence of a `check` option (formerly: of an output file); nothing changes for the writing commands, and `gui serve` plans itself. A declaration that writes a file without a boolean `check` option is refused at import, and the MCP server's plan-only mode follows `Command.writes`.
- The writer of command lines moved from the CLI to the catalog: `hydrolog.cli.parser.format_example` and `example_arguments` are removed; use `format_command` and `hydrolog.catalog.lines.option_arguments`. The human output of a `--check` plan also shows the plan's other fields (`url`, `port_free` of `gui serve`).

#### Partial watersheds, field-level errors and typical ranges (branch `feature/partial-watershed`, for the three-step „Hydrogram zlewni” of the GUI)
- **`WatershedParameters` requires only `area_km2`** (since 1.0.0.dev0: `perimeter_km`, `length_km`, `elevation_min_m` and `elevation_max_m` were required too). The other fields are optional, and whatever needs a missing one raises `InvalidParameterError` with `details.reason` `missing_field`, `details.option` the (first) missing field and `details.missing` all of them: `width_km` (`length_km`), `relief_m` (both elevations), `to_geometry()` (`perimeter_km`, `length_km`), `to_terrain()` (both elevations, `length_km`), `calculate_tc()`/`tc_parameters()` (the fields the method's source defines, with no substitute, [ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md): e.g. `flow_path_length_km` for Kirpich). `elevation_max_m > elevation_min_m` is checked when both are given. `hydrolog-network-1.schema.json` (`$defs/watershed`), the loader of `watershed`/`watershed_file` and the reader of `route network` (`watershed_from_document`, which follows the class) require only `area_km2`; `morphometry watershed` still needs the five fields of its indicators. `report generate` leaves out of its watershed section the values whose fields are missing. `hydrolog.testing.watershed()` leaves out a field given as `None`. The `nogat-handoff/1` hand-off of the GUI still carries a full watershed.
- **`details.option` names the field:** the errors of `hydrograph generate` and `tc watershed` for missing watershed fields have `details.option` the first missing field (formerly `watershed` or `watershed_file`), with `details.method` and `details.missing` as before. Every check of `WatershedParameters` names its field in `details.option` with a reason (`exclusive_minimum`, `minimum`, `range`; `elevation_max_m` not above `elevation_min_m` is `exclusive_minimum` with the minimum), and the loader of a watershed passes them on with `details.field` too (formerly `details.option` `watershed`, `details.reason` `invalid_value`). A value that a time of concentration formula refuses (e.g. a channel slope of 0) names the field it came from (`details.option`, `details.parameter` the argument of the formula; formerly `invalid_value` with the option of the watershed). `NashIUH.from_lutz` names `Lc_km` for Lc > L (`uh nash`: `lutz_centroid_length_km`), and a Snyder `cp` without a unit hydrograph of 1 mm is `details.option` `cp` (`hydrograph generate`: `snyder_cp`). The positivity checks of `ConcentrationTime` name their argument.
- **`OutsideTypicalRange` has `details.field`** (notice `outside_typical_range`): the input the value came from. For a formula of `tc` it is the argument; for the time of concentration of a watershed it is the watershed field the method takes (`flow_path_length_km`, `flow_path_slope_m_per_m`, `mean_slope_m_per_m`, `channel_length_km`, `elevation_mean_m`, `overland_*`...); in `hydrograph generate` it is the option (`snyder_ct`, `nash_k_min`, `clark_r_min` or `clark_r_tc_ratio`, `cn`, `timestep_min`). `hydrolog._warnings.typical_range_fields()` names the inputs inside a block and `warn_outside_typical_range()` warns.
- **New typical ranges** (warnings, the run proceeds): Snyder `ct` 1.35-1.65 and `cp` 0.4-0.8 (`SnyderUH`; Ct 1.8-2.2 of Snyder 1938 in SI, Chow, Maidment and Mays 1988), given Nash `n` 1-10 and `k_min` 10-200 min (`NashIUH(...)`; the estimates of `from_lutz` and `from_urban_regression` are not checked), Clark R/tc 0.2-1.5 (`ClarkIUH`, parameter `r_tc_ratio`, also for a given R; USACE HEC-HMS), the CN of an AMC I or III conversion 55-95 (`SCSCN.adjust_cn_for_amc`, method `scs_cn_amc`; Hawkins et al. 1985), and the time step of `HydrographGenerator.generate` at most 0.25 of the time to peak of the unit hydrograph (method the unit hydrograph model, parameter `timestep_min`; NEH 630, chapter 16). They are the ranges the GUI's explanations quote. `uh nash`, `uh clark`, `uh snyder` and `scs effective` return them as notices (an `OperationOutput`; formerly the warnings were not captured). `ConcentrationTime.kerby_kirpich` no longer warns twice for the same value (once under `kerby` or `kirpich`).

#### Web GUI: „Hydrogram zlewni” in three steps, without the example (the author's decision of 2026-11-04; branch `feature/gui-wizard`)
- The panel Dane has three steps instead of five: 1 Zlewnia (the watershed's basic fields with CN), 2 Hietogram (the former „Opad”), 3 Hydrogram (the unit hydrograph model, none chosen at first, then only the chosen model's block: tc with the tc method's own fields for SCS and Clark, Clark's R or R/tc, Nash by Lutz with Lc, Manning's n, forest and urban shares or n and K, Snyder with Lc, Ct and Cp; then „Straty SCS-CN”, AMC and λ, common to every model). Other models' fields are not in the page and are never sent; a run's `watershed` holds the fields of step 1 and those the chosen model and tc method read.
- Checks follow the chosen model (`requirements()` and `checkInputs()` → `{errors, warnings}` in `web/src/sections/hydrogram/state.js`): nothing is required and nothing runs before a model is chosen; a value that is not a number or leaves a bound (or the highest elevation not above the lowest) is an error at once. Then an empty field the model, its tc method or its rainfall needs is an error (red, „Podaj wartość: potrzebna dla metody Kirpicha”, naming the substitutes of a length or a slope; the fields of step 1 it reads say „wymagane dla …”), and Hydrolog's `outside_typical_range` notices stand on the field of their `details.field` as warnings (amber; the run goes on), as do `ia_coefficient_nonstandard` and `duration_not_covered`. Errors of the server land on the field of `details.option` (every field of `details.missing`). Step 3 sums up what is missing, what to correct and what is outside its range, each a link to its field. Empty fields mean Hydrolog's defaults (Δt 5 min, λ 0,2, Ct 1,5, Cp 0,6); PMAXTP's probability and duration start unselected.
- No example prefill: a first visit and „Wyczyść” show empty steps (and „Wyczyść” clears the watershed Kalkulatory reads); `web/examples/kamiennik.json` moved to `tests/fixtures/kamiennik.json`, and the guide (`web/instrukcja/`) gives Kamiennik at Świerzawa as a worked example with the values to type and the expected result (60,21 m³/s at 6:20 h). The inputs are kept under `hydrolog-gui/hydrogram/2` (`VERSIONS` in `web/src/persist.js`), so a browser's stored example is no longer read. A hand-off („Przekazanie”) is offered only for a full watershed (area, perimeter, length, both elevations); its `watershed` provenance is a file, the person or the producer (no longer `{"source": "hydrolog", "file": "examples/kamiennik.json"}`).

#### Web GUI: every section starts empty (the author's decision of 2026-11-04, decision 1; branch `feature/gui-empty-sections`)
- Sieć, Statystyka, Kalkulatory and Wszystkie polecenia start empty, as Hydrogram zlewni does: no example on a first visit or after „Wyczyść”, no „Przykład” or „Dane przykładowe” button, and no request until the person enters data. Sieć opens a network only from a file or a hand-off; Statystyka has no file and no values; a calculator's or command's form opens empty (only the default name of a required output file, `outputDefaults` in `web/src/forms/model.js`, which replaces `valuesFromCall`); Wszystkie polecenia chooses no command. Each empty section says in Polish what to enter and links its worked example in the guide (`web/src/ui/empty-hint.js`).
- The stored inputs moved to `hydrolog-gui/{siec,statystyka,kalkulatory,polecenia}/2`, so a browser's stored examples are no longer read.
- The guide (`web/instrukcja/`) gives a worked example per section with the values to enter and the result: the network `instrukcja/przyklady/siec.json` (formerly `web/examples/siec.json`, still `hydrolog.testing.example_network_document()`) to download and load, the annual maxima 1998–2023 to paste, the tc comparison and `cn lookup`, and `uh nash`; `web/examples/maksima_roczne.csv` moved to `tests/fixtures/`. The welcome dialog says every section starts empty and the examples are in the guide. The browser tests seed their data (upload or typing) and type the guide's examples through the page.

#### Web GUI: typical ranges from Hydrolog only (the author's decision of 2026-11-04, decision 2; [ADR-0017](decisions/0017-typical-ranges-in-the-catalog.md); branch `feature/ranges-from-hydrolog`)
- The GUI keeps no range numbers. The explanations (i) list the `typical_ranges` of the catalog documents the sections load (`hydrograph generate` and Lutz's area of `uh nash` in Hydrogram zlewni, `tc watershed` in Kalkulatory, `stats flood-frequency` in Statystyka), each with its Polish source (`i18n.pl.source`), checked against the current values („w zakresie”, „poza zakresem”; the time step against the unit hydrograph's time to peak, `relative_to`), and Muskingum's X in Sieć takes the bounds of the network schema. `web/src/labels/info/*.js` keep only the symbols of the parameters (`symbols`), `web/src/ui/info.js` registers the served ranges (`registerServed`, `infoRanges`), and the GUI's own ranges are gone, with the browser test that compared them with the library's constants.
- Hydrogram zlewni words no range verdict of its own: a value outside a range is Hydrolog's notice `outside_typical_range` (`outside_unverified_range` for a range to be verified), on its field and in Wyniki, now also from Lutz's `uh nash` (on the field the panel names). The GUI's notes only confirm that the values of a method Hydrolog did not warn about lie inside its ranges, the time step's note quotes the served share of tp, and the notes of given Nash n and K and of Clark's R/tc quote the served ranges.
- A range Hydrolog serves with `verified` false (given Nash n and K) is marked „do weryfikacji”: in its row of the explanation (`data-verified="false"`), in the note of given n and K, in the confirmation in Wyniki and in the warning on the field („…; zakres do weryfikacji”); Kalkulatory and the notices in Wyniki treat `outside_unverified_range` as a range notice too. Browser test: a given n = 12 warns on its field, in Wyniki and in the explanation.
- The guide (`web/instrukcja/`) says that Hydrolog gives the ranges with their sources; its tc table, the warning of the worked example (`data-example="hydrogram-outside"`) and the picture of Kirpich's explanation (`img/objasnienie.png`) follow the new ranges: Kamiennik lies outside the data of Kirpich and NRCS and inside those of Kerby–Kirpich. Browser tests: the explanations show exactly what `commands schema --command` serves, and the fields, the explanation and Wyniki give the example the same verdicts.

#### Web GUI: Hydrogram zlewni fetches the PMAXTP depth (the author's decision of 2026-11-04; [ADR-0018](decisions/0018-pmaxtp-through-obserwator.md); branch `feature/pmaxtp-from-obserwator`)
- Step 2 „Hietogram”, source PMAXTP, has no typed depth: the person gives the point, „Szerokość geograficzna φ” (`pmaxtp_latitude`) and „Długość geograficzna λ” (`pmaxtp_longitude`) in WGS84 decimal degrees, checked at once against the bounds of `precip pmaxtp` (49–55, 14–24.5), p (all 27 values of the atlas, 0,01 %–99,9 %), the duration (all 16, 5 min–72 h) and the method (POT by default, or AMP). Once the point, p and the duration are complete and valid, the page runs `precip pmaxtp` on a debounced channel of its own, `hydrogram-pmaxtp`, separate from the hydrograph's runs, and shows the depth read-only („Wysokość opadu P”, „PMAXTP IMGW-PIB, metoda POT”); `hydrograph generate` takes it as `total_mm`, and no hydrograph is computed until a depth is known.
- The fetched depth is kept with the inputs (`pmaxtp_fetched`, the options it was fetched for, `latitude`, `longitude`, `duration_min`, `probability_percent` and `method`, with `depth_mm`, in `hydrolog-gui/hydrogram/2`): a reload does not fetch again, and a change of the point, p, the duration or the method fetches anew.
- A point outside the box is an error on its field at once, a point inside it but outside the atlas an error on the latitude („Punkt poza atlasem PMAXTP”, `outside_pmaxtp`), and `source_unavailable` or a timeout an error on the row of the depth, with „Pobierz ponownie”. Step 2 shows the attribution „Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy”.
- Hand-off: `provenance.rainfall` is `{"source": "pmaxtp", "probability_percent", "duration_min", "latitude", "longitude", "method"}` (formerly the probability and the duration as typed). Reading takes the point from `provenance.rainfall`, else from `provenance.watershed` (Hydrograf's outlet); the payload's depth is remembered without a fetch only when `provenance.rainfall` carries the point, a point only in the watershed's provenance is fetched for, and without a point the rainfall opens as a design hyetograph („Hietogram”) of the payload's depth and duration.
- The guide's worked example (Kamiennik at Świerzawa) gives Hydrograf's outlet 51,01544 / 15,88984, p 1 %, 12 h and POT: the fetched 101,82 mm (2026-11-04; AMP gives 99,10 mm) gives 56,39 m³/s at 6:20 h, 976 759 m³ and C 0,258, with AMC III 109,92 m³/s (formerly a typed 105 mm: 60,21 m³/s, 1 046 213 m³, 0,268 and 115,23 m³/s). IMGW-PIB may update the atlas, so the depth and the result may change.
- The browser tests stay offline: they route `api/run/precip/pmaxtp` to an envelope computed in the test process from IMGW-PIB's table at Kamiennik's outlet (`tests/fixtures/pmaxtp_kamiennik_pot.json`, POT, recorded 2026-11-04).

#### Web GUI: hand-offs from Hydrograf (branch `feature/handoff-from-hydrograf`)
- A hand-off of one subcatchment without rainfall opens in Hydrogram zlewni (formerly refused: „Zlewnia Z1 nie ma opadu…”): Hydrograf hands the watershed alone off before it has a hydrograph. Step 1 has the watershed; step 2 is PMAXTP at the point of `provenance.watershed` (Hydrograf's outlet) with p and the duration to pick, after which the depth is fetched, and empty without a point; step 3 has no model chosen. A network of more nodes without rainfall opens in Sieć as before.
- Headers and notes round a value handed over exactly, while the field and the run keep it whole (`roundedText` in `web/src/format.js`): a given tc to 0,1 min („SCS · tc 209,1 min”, step 3's „209,1 min · podany”), a design depth and Beta's or the peak's parameters to 0,01, a duration in minutes to 0,1 min.
- Texts: „Wczytaj z Hydrografa” names Hydrograf's buttons („Kopiuj do Hydrologa”, „Plik przekazania”) in its menu and in the field to paste into; the note under „Przekazanie” no longer says that Hydrograf reads a hand-off („Wczytaj z Hydrologa” does not exist). The guide's chapter „Przekazanie” says how to copy in Hydrograf („Kopiuj do Hydrologa” in its panel „Zlewnia”, from the release after Hydrograf v0.5.0) and paste here, and what a watershed-only hand-off opens with.
- Browser tests paste two hand-offs written by Hydrograf's builder (`tests/fixtures/handoff_hydrograf.json`, `tests/fixtures/handoff_hydrograf_watershed.json`): the full one gives Hydrograf's result again with its exact tc and depth, the watershed alone opens with PMAXTP at Hydrograf's outlet.

#### Nogat standard 1.0 (its drafts 2.0 and 2.1)
- The package, tooling, error registry, settings, writing commands, MCP server and documentation follow the Nogat standard 1.0: see the "Added" sections above and the breaking entries under "Breaking changes". Deliberate deviations from the standard are listed in `CLAUDE.md`.
- The error document `hydrolog-error/1` omits `hint` and `command` when there is none (formerly `null`) and its `title` is English unless `lang="pl"` is requested. An output file that cannot be written is `io_error` with `details.reason = "output_unwritable"`.
- The README links to Obserwator point at its renamed repository `https://github.com/Daldek/Obserwator` (formerly `Daldek/IMGWTools`).

#### Time of concentration from the inputs its source defines (the author's decision of 2026-11-05; [ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md); Nogat plan `2026-11-05-official-tc-inputs`, step 1; branch `feature/official-tc-inputs`)
- **New `WatershedParameters` fields** `flow_path_length_km` (the longest flow path, from the watershed divide to the outlet [km], > 0) and `flow_path_slope_m_per_m` (the elevation of its head on the divide minus the outlet elevation, over its length [m/m], >= 0), appended at the end of the dataclass, read by `from_dict` and part of the `watershed` of `hydrolog-network/1` (schema regenerated). The report's watershed table lists them. `hydrolog.testing.watershed()` gives a flow path of 6 km at 0.02 by default (the length and relief of its default catchment), and `example_network_document()` gives B 3.5 km at 0.0229.
- **Breaking - every time of concentration method takes the fields its source defines, with no substitute** (`hydrolog._ranges.TC_INPUTS`; `WatershedParameters.calculate_tc`, `tc_parameters`, `tc watershed`, `hydrograph generate`, `report generate`, the `curve-number` runoff of `route network`): Kirpich `flow_path_length_km` and `flow_path_slope_m_per_m` (Fang et al. 2005, TxDOT 0-4696-1, eq. 3.14; formerly the channel length, else the watershed length, and the channel slope, else the mean slope, else the relief over the length); NRCS `flow_path_length_km`, `mean_slope_m_per_m` and `cn` (NEH 630 ch. 15, eq. 15-4; formerly the channel length, else the watershed length, and the mean slope, else the channel slope, else the relief); Giandotti `channel_length_km`, `elevation_mean_m` and `elevation_min_m` (formerly the watershed length without a channel and the middle of the elevation range without a mean). A missing field is `validation_error` with `details.reason` `missing_field` naming it, whatever other fields the watershed has; a missing flow path has a hint saying how it is measured. The default `tc_method` (`kirpich`) now needs the flow path. Migration: add `flow_path_length_km` and `flow_path_slope_m_per_m` (from Hydrograf: `hydraulic_length_km` and (head elevation − outlet elevation) / length; `flow_path_length_km` = the channel length and `flow_path_slope_m_per_m` = the channel slope give back the old Kirpich number), and `elevation_mean_m` for Giandotti.
- **Breaking - Kerby-Kirpich takes the flow path:** `tc kerby-kirpich` (its options), `operations.tc_kerby_kirpich` and `ConcentrationTime.kerby_kirpich` take `flow_path_length_km` and `flow_path_slope_m_per_m` instead of `channel_length_km` and `channel_slope_m_per_m`. The channel segment is `flow_path_length_km − overland_length_km`, timed by Kirpich at the slope of the whole path (Roussel et al. 2005, supplement); a flow path not longer than the overland segment is `exclusive_minimum` on `flow_path_length_km`. The typical ranges 1.6-80 km and 0.002-0.02 are now those of `flow_path_length_km` and `flow_path_slope_m_per_m` (`details.parameter`). The report follows: `generate_tc_section(flow_path_length_km=, flow_path_slope_m_per_m=)` and `FormulaRenderer.kerby_kirpich_tc(ov_length_km, ov_slope_m_per_m, retardance, fp_length_km, fp_slope_m_per_m, ...)` replace the channel arguments and show L_ch = L − L_ov. Migration: `--channel-length-km X --channel-slope-m-per-m S` becomes `--flow-path-length-km` (X + the overland length) `--flow-path-slope-m-per-m S`, which gives the same number; the official slope (the drop from the divide to the outlet over the whole path) changes it. Hydrolog reproduces the method's published examples: 24.6 + 32.0 = 56.5 min against "about 57" (Roussel et al. 2005) and 52.1 + 86.8 = 138.9 min against "about 140" (Cleveland et al. 2012, low slope).
- **Changed results.** The guide's Kamiennik at Świerzawa gains Hydrograf's longest flow path of 2026-11-05 (15.88 km from the divide at 440.16 m to the outlet at 258.72 m, 0.0114 m/m): Kirpich 162.9 → 187.4 min, NRCS 377.5 → 399.8 min, Kerby-Kirpich 187.2 → 208.9 min (Giandotti 339.4, FAA 23.8 and Kerby 24.2 unchanged). Its hydrograph (PMAXTP 101.82 mm) goes from 56.39 to 54.20 m³/s, the time to peak from 6:20 to 6:40 h and the volume from 976 759 to 977 225 m³; with AMC III, 109.92 → 105.97 m³/s; the 105 mm run, 60.21 → 57.88 m³/s. In the second example of `route network`, B gets 3.5 km at 0.0229 instead of the relief over the length (0.022857): its tc goes 44.741 → 44.708 min and its peak 1.1904 → 1.1913 m³/s (the USAGE network: B 4.35 → 4.36 m³/s, its schematic redrawn). The documented examples whose old inputs become their flow path (`watershed_example.json`, the examples of `tc watershed` and `hydrograph generate`, the guide's network) keep their numbers.
- **Web GUI** (Hydrogram zlewni, Sieć, Kalkulatory): step 1 has „Długość najdłuższej drogi spływu” and „Spadek najdłuższej drogi spływu”. A tc method asks for exactly its fields, with no other way named: Kirpich both flow-path fields; NRCS the flow-path length, the mean slope and CN; Giandotti the channel and the lowest and mean elevations; Kerby-Kirpich the overland fields, N and the flow path. The (i) explanations, the Sieć hints and Kalkulatory's comparison say so (it shows the L and S of the flow path; Kirpich and NRCS share the length, not the slope). The guide's worked example, its tc table and its pictures `ekran`, `hydrogram`, `telefon`, `kalkulatory`, `objasnienie` and `eksport` follow.
- **Nogat's hand-off example** (`schemas/nogat/handoff-1.schema.json`, copied again from Nogat `8727f6e`): its watershed carries Kamiennik's flow path (15.88 km, 0.0114 m/m) and its result is Hydrolog's for it, 57.8786 m³/s at 400 min and 1,046,712.9 m³; pasted into Hydrogram zlewni it opens complete and the comparison reads „zgodny”.

#### The default fit method of flood frequency is the L-moments (the author's review of 2026-11-06; [ADR-0021](decisions/0021-fit-methods-of-flood-frequency.md) amended; plan `2026-11-06-flow-statistics-feedback`, D6; branch `feature/fit-method-all`)
- **Changed results.** `fit_method` defaults to `l_moments` instead of `mle` in the library (`FloodFrequencyAnalysis.fit_*` and `fit_all`), `stats flood-frequency` (CLI, MCP) and the GUI: maximum likelihood is less stable on the short samples of annual maxima. Pass `fit_method="mle"` (`--fit-method mle`) for the former results. The guide's example of Statystyka (26 annual maxima) gives GEV Q 1% 324.9 m³/s (307.3 by maximum likelihood) and Q 10% 197.4 (196.5); its Pearson III, like its Weibull, now leaves out the smallest maxima and has no AIC.

#### Nash by Lutz from the watershed (stage W1, [ADR-0024](decisions/0024-nash-by-lutz-from-the-watershed.md))
- **Numbers of Nash by Lutz change:** Lutz's L and J are the longest flow path's (the main stream from the divide), no longer the channel's, which ends at the channel head. Hydrogram zlewni and Kalkulatory read the flow path; the guide's Kamiennik (PMAXTP 101.82 mm, 12 h, Beta, Δt 10 min): n 3.631 → 3.610, K 82.35 → 92.13 min, peak 37.66 → 35.03 m³/s at 8:50 → 9:10 h, volume unchanged.
- **Hydrogram zlewni** runs Nash by Lutz as one `hydrograph generate` with `nash_estimation` (no `uh nash` before it); its command line says `--nash-estimation lutz`, its hand-off carries `nash_estimation` instead of n and K and no `provenance.runoff` of `uh nash` (an older hand-off opens with its n and K given); the chip of Lutz's lag time is gone.

#### Positions and descriptions in the network (plan `2026-11-10-network-editor`, stage E1; [ADR-0023](decisions/0023-positions-and-descriptions-in-the-network.md); branch `feat/network-editor-e1`)
- **Python API:** `hydrolog.operations.route_schematic(...)` returns an `OperationOutput` (its `result` is the `RouteSchematicResult` as before, its `notices` the layout's notices) instead of the bare `RouteSchematicResult`; the envelope of `route schematic` changes only by the notice `positions_ignored` and the field `layout`.
- **Node classes** ([ADR-0012](decisions/0012-network-objects-rainfall-and-runoff.md) amended): `Node.read_entry(node_id, fields)` returns a `NodeEntry(upstream, arguments, description, position)` instead of `(upstream, arguments)`, and `Node.build(node_id, entry, inflows)` takes it instead of `arguments`; `Node.to_document()` writes the two fields after `document_fields()`, and a kind's `read_document()` receives the whole node and must not take fields named `description` or `position`.
- `Line.row` of the layout (`hydrolog.routing._layout`) is `int | None`: `None` for a line of a given layout whose nodes lie on several rows.
- **Web GUI:** Sieć leaves `description` and `position` out of its node and network forms (they are not parameters). A document with them opens and computes as without them; Sieć keeps, sends and saves the positions since stage E2 (the canvas, above) and the descriptions since stage E3 (the editing, above), which edits them in „Opis” and „Opis sieci”.

#### The structure alone in the schematic (plan `2026-11-10-network-wizard`, stage W2; [ADR-0025](decisions/0025-the-structure-alone-in-the-schematic.md); branch `feat/network-wizard-w2`)
- **`route schematic --structure-only`** (`structure_only`, boolean, default false; `route_schematic(..., structure_only=True)`) and **`hydrolog.routing.structure_schematic(document, main_stem=None)`**: a draft whose nodes miss their values is laid out by its structure alone. Read: `schema`, `name`, `timestep_min`, each node's `id`, `type` and `from` and each headwater's `watershed.area_km2` (weighing the branches when every headwater has a positive one); every other field may be missing or wrong, positions are ignored, and no file is read (`inflows_file` or `time_column` with it is `conflict`). The schematic has `structure_only: true`, empty `parameters`, no node `description`, and `timestep_min` only when the document gives it; the JSON Schema of `hydrolog-network-schematic/1` takes `timestep_min` out of `required` but for the other schematics, which do not change. A third rule and a third example of `route schematic` (a draft without any value). Nogat's example network, whose reach `R1` has no section, is laid out with the option and refused without it.
- **One check of the structure** (`hydrolog.routing.network.check_links`, `check_graph`, `upstream_from_document`) shared by `Node.read_entry`, `RoutingNetwork` and the new `hydrolog.routing.document.read_structure` (`NetworkStructure`), so the structure and the network are refused with the same reason, details and message; `RoutingNetwork._check_shape` is gone. For every network, the structure's layout equals the network's computed layout (a property test on random trees, with and without areas and a declared main stem).
- **Web GUI, Sieć:** „Uporządkuj” and the opening of a network without positions take Hydrolog's layout of the structure (`structure_only` on the channel `siec-layout`, 300 ms after a change of the structure or of a headwater's area) as soon as the structure has no problem, before any value is given: a network built from „Nowa sieć” is tidied at once, and a network opened with incomplete nodes appears at the library's positions without „Układ tymczasowy”, which remains only while the structure has a problem. The full `route schematic` stays the check of a complete network on `siec-schematic`. The canvas weighs its lines only with positive areas, as the library does. The button's title and the provisional note say so.
- Docs: ADR-0025 (amends ADR-0013, ADR-0015 and ADR-0023), [USAGE.md](USAGE.md) (the structure alone; section 8's positions), [INTEGRATION.md](INTEGRATION.md) (the structure's schematic), and the guide's entries „Przesuwanie i układ” and „Uporządkuj” in its troubleshooting.

#### The network's rainfall first (plan `2026-11-10-network-wizard`, stage W3; branch `feat/network-wizard-w3`)
- **Web GUI, Sieć, step 1 „Sieć”:** after the name and the description come „Krok czasowy Δt” (the network's `timestep_min`) and „Opad sieci”, Hydrogram zlewni's step 2 bound to the network (`RainStep`, now `hydrogram/rain-step.js`, with its rows in `hydrogram/rows.js`): „Brak” (a network of given hydrographs needs none), PMAXTP (the point, p, the duration, POT or AMP), a design hyetograph or a series at Δt. PMAXTP's depth is fetched by `precip pmaxtp` on the channel `siec-pmaxtp` (`usePmaxtp`, `hydrogram/pmaxtp.js`, the hook Hydrogram zlewni fetches its own depth with), kept with the inputs as `pmaxtp_fetched` and not fetched again after a reload or an undo; „Oblicz sieć” waits for it. The document's top `rainfall` is what a run of `hydrograph generate` takes: `design` with the fetched depth as `total_mm`, or `series` (`rainfallOf`; back with `rainfallInputs`, which reads a hand-off's PMAXTP record as Hydrogram zlewni does).
- „Nowa sieć” opens step 1 (on a phone too: „Dane” stays open) and the empty canvas says to give the network's rainfall first, then to place the elements. A subcatchment made from rainfall with neither its own rainfall nor the network's is the problem „Brak opadu” of its node (the library's `missing_field` `rainfall`), marked on the canvas and in „Problemy sieci” before „Oblicz sieć”, which sends nothing. A subcatchment's default rainfall is called „Jak w sieci” and its note links to „Opad sieci” in step 1.
- **Stored inputs:** Sieć keeps its inputs under `hydrolog-gui/siec/3`; a network stored under version 2 is not read (save it with „Zapisz sieć” or „Zapisz szkic” before updating). „Dodaj zlewnię z Hydrografa” compares the hand-off's rainfall with the network's as the document writes them.
- Hydrogram zlewni is unchanged: its step 2 is the same `RainStep`, and its browser tests pass without a change.

#### The subcatchment in Hydrogram's three steps (plan `2026-11-10-network-wizard`, stage W4; branch `feat/network-wizard-w4`)
- **Web GUI, Sieć:** choosing a subcatchment made from rainfall opens its panel beside „Dane”, titled „Zlewnia <id>”: Hydrogram zlewni's three steps (Zlewnia, Hietogram, Hydrogram: the model first, then only its fields) with the same fields, order, checks, (i) explanations and inputs as in Hydrogram zlewni (`SubcatchmentSteps`, `hydrogram/steps.js`, which replaces `hydrogram/data-panel.js`; the ids prefixed `sn` in Sieć, `hg` in Hydrogram zlewni). Step 2 starts at „Jak w sieci” and Δt is the network's; a node's own PMAXTP depth is fetched on the channel `siec-node-pmaxtp`. A subcatchment whose model is not chosen is incomplete, in „Problemy sieci”. Step 3 shows the values of the last „Oblicz sieć” (tc, the CN after AMC, S, Ia, the unit hydrograph's parameters) while the node is unchanged since. „Wczytaj z Hydrografa” of step 1 fills the chosen node from a hand-off of one watershed in one step of the history (its id, links, position and description stay; its rainfall is „Jak w sieci” when it equals the network's, else its own) and refuses a network, naming „Wczytaj z Hydrografa” of step 1 and „Dodaj zlewnię z Hydrografa”.
- **The layout:** `ViewLayout` takes a second left panel (`detail`: 260-560 px, 300 by default, its width kept like the others). When the four columns do not fit beside a centre of 480 px, „Wyniki” narrows first, to 340 px, then „Dane” and the panel evenly, to 260 px (a 1440 px window: about 278 px each, a centre of 480 px and „Wyniki” of 340 px); below 1340 px „Wyniki” gives the panel its place and its button shows it there. Enter on a subcatchment moves the focus to the panel's first step, a click, the arrows or the list do not; ✕ closes the panel and keeps the node chosen. On a phone the panel is a sheet of its own that alternates with „Dane” („← Dane”, and „Dane zlewni →” in „Dane”'s step 3). The print view prints it after „Dane”.
- **One mapping** (`handoff/mapping.js`): `subcatchmentNode` writes the node of Hydrogram's inputs as a run of `hydrograph generate` takes them (the runoff's `amc`, `uh_model` and, for SCS and Clark without a given tc, `tc_method` written out), `subcatchmentInputs` reads a node back with the library's defaults; Hydrogram zlewni's hand-off (`hydrogramPayload` takes the inputs, no longer the options) and Sieć's network are made of the two. A watershed field that no step shows for the node's choice stays in the page's inputs and is neither saved nor sent. „Dodaj zlewnię z Hydrografa” reads each subcatchment as Hydrogram zlewni reads a hand-off (an own rainfall with a PMAXTP record in the provenance is PMAXTP at its point) and still compares the rainfall with the network's as the documents write them.
- **Removed:** Sieć's own form of a subcatchment made from rainfall (its watershed, runoff and rainfall parts with „Pozostałe pola zlewni”) and its texts; a subcatchment given its hydrograph („Podany”) or reading the inflows file („Z pliku”) keeps its form in „Dane”.
- **Step 1 „Zlewnia” without „Spadek cieku głównego”** (`channel_slope_m_per_m`; the coordinator's decision of 2026-11-10, the plan's erratum), in Hydrogram zlewni and in Sieć: no calculation reads it (Kirpich, Kerby–Kirpich and Nash by Lutz take the longest flow path's slope). A value that comes with a watershed file or a hand-off stays in the inputs but is neither shown, sent to a run, saved in Sieć's document nor written into Hydrogram zlewni's hand-off; the guide's table of the worked example drops its row.
- Docs: the GUI plan's erratum (S4: a subcatchment made from rainfall in Hydrogram's three steps, in a panel beside „Dane”) and the plan's erratum on the channel slope. Tests: `tests/e2e/test_siec_subcatchment.py`, the contract of A3 over the 24 model choices (the panel's fields, the saved node and the fields the library reads and needs), one peak in Hydrogram zlewni and in Sieć, the panel's fill, the layout at 1440, 1180 and 390 px; the mapping's round trips in `tests/e2e/test_js_units.py`.

#### The origin of each node (plan `2026-11-10-network-wizard`, stage W5; Nogat plan `2026-11-10-node-provenance-in-handoff`, step 3; branch `feat/network-wizard-w5`)
- **The hand-off schema:** `schemas/nogat/handoff-1.schema.json` copied again from Nogat `8848c26` (SHA-256 `84c6856d…`): the optional `node_provenance`, `{<node id>: {<input>: origin}}`, and a second example, Hydrograf's network of three subcatchments. `handoff/envelope.js` takes its validation keywords.
- **Reading (Sieć):** a network hand-off opens with the origin of each node, Nogat's precedence (`nodeOrigins`): input *i* of node *n* comes from `node_provenance[n][i]`, else `provenance[i]`. A key that names no node of the payload is left out and the load's note says so; the network still opens. Each node keeps its origins beside its structure, and they follow it through a rename and through „Dodaj zlewnię z Hydrografa” under a free id (`Z1` added as `Z4` keeps `Z1`'s origins).
- **Shown:** a subcatchment's panel names its watershed's element in step 1 (Hydrograf's words: „zlewnia górna”, since Hydrograf's ADR-080 amendment „dopływ”, see Changed; „dopływ do punktu P1”, „dopływ do ujścia przy punkcie P1”, „przyrzecze odcinka R1”, with its outlet's place) with the marks of the fields changed since, and the received origins of its rainfall in step 2 and of its runoff in step 3; a reach, a junction or the outlet shows its `node` origin in „Dane”'s step 3 (the element, the point, the length „wzdłuż spływu”, the slope „z NMT” or „minimalny”, the NMT at its ends and the check length of BDOT10k's line), and a node without one shows the hand-off's, the network's origin.
- **Writing:** Sieć's hand-off writes `node_provenance` under the nodes' current ids (`siecNodeProvenance`): the received entries while their inputs are unchanged, `changed` with the fields edited since for a watershed or a node's own fields (a reach given its Manning's n and width names them), `{"source": "user"}` for an edited runoff or an own rainfall typed by the person (an own PMAXTP rainfall its record), the provenance of the single-watershed hand-off that added or filled a node, and, for a node made in Sieć, `{"source": "user"}` only where `provenance` would claim its input. `provenance` keeps the received one or the file's; the network's rainfall changed since it was opened takes Hydrogram's rule (the PMAXTP record of its fetch, else `{"source": "user"}`). A hand-off written so reopens with the same origins.
- Docs: [INTEGRATION.md](INTEGRATION.md) (`node_provenance` read and written, Hydrograf's origin parameters). Tests: Nogat's second example in the contract test (it names only nodes of its payload and lacks only its reach's section), the browser's check of `node_provenance` against jsonschema, `nodeOrigins` and `siecNodeProvenance` in `tests/e2e/test_js_units.py`, and Hydrograf's network (`tests/fixtures/handoff_hydrograf_network.json`, built from Nogat's second example with Hydrograf's origin parameters) opened, completed, computed, written and reopened in `tests/e2e/test_exports.py`.

#### The guide and the docs of the network wizard (plan `2026-11-10-network-wizard`, stage W6; branch `feat/network-wizard-w6`)
- **The guide (`web/instrukcja/`), chapter 03 „Sieć i trasowanie”:** the order of the wizard (the network's time step and rainfall first, then the elements, then each subcatchment in its panel); „Opad sieci” with Hydrogram zlewni's fields and the empty canvas's reminder; the settings of a node with a subcatchment's kinds („Z opadu”, „Podany”, „Z pliku”); „Panel zlewni” (Hydrogram zlewni's three steps, „Jak w sieci”, the model first, „Brak opadu”, the values of the last run, ✕, the narrow layout); Enter on a subcatchment moves to its panel; the example built from „Nowa sieć” in the new order; the new part „Sieć z Hydrografa i pochodzenie węzłów” (the elements Hydrograf delineates, the origin cards of subcatchments, reaches and junctions, what Hydrograf leaves to Hydrolog, the origins kept when the network is handed on).
- **The guide, other chapters:** Nash by Lutz in Hydrogram zlewni (02: L and J of the longest flow path from step 1, n and K estimated in the same run and shown read-only), with a „Spróbuj” of Kamiennik: n 3,61, K 92,13 min, 35,03 m³/s at 9:10 h; Sieć's hand-off with the origin of each node and Hydrograf's networks (07); the subcatchment's panel and „Dane” alternating on a phone, the PMAXTP depth and the origins kept by Sieć (08); „Brak opadu” and a subcatchment without a model among „Problemy sieci” (09).
- **The guide's pictures:** `siec.png` taken again (the network's rainfall in step 1 beside the panel of C with „Jak w sieci”), `telefon.png` taken again (a subcatchment's panel as a sheet on a 390 px phone in the dark theme), and the new `siec-hydrograf.png` (Hydrograf's network with the origin card of a subcatchment), all 256-colour PNG.
- **Docs:** [README.md](../README.md) (the paragraph on the GUI, Hydrograf's networks), [USAGE.md](USAGE.md) section 8 (Sieć's order, the subcatchment's panel, hand-offs and the origin of each node, Sieć's stored version 3 and its PMAXTP fetch), [PRD.md](PRD.md) (US-G02 and US-G09 revised, US-G10 „A network delineated by Hydrograf opens ready”), [SCOPE.md](SCOPE.md) (Sieć's wizard, Nash by Lutz in the runoff, the structure's schematic, what Sieć leaves out).
- **Fixed (Sieć):** a network opened without positions (a file, a hand-off, or inputs stored without them) was drawn once in provisional rows, in the render in which Hydrolog's layout arrived and before the nodes moved there; the canvas now waits until the layout has placed them. `tests/e2e/test_siec.py` records every picture of the canvas (a `MutationObserver`), so a test that read the cells in that render no longer fails now and then.
- **Tests:** `tests/fixtures/handoff_hydrograf_network.json` is Hydrograf's own hand-off, written by its `POST /api/delineate-network` (branch `feat/network-delineation-api`, `5586edb`) on the synthetic DEM of its tests: eight subcatchments, four reaches without their section, five junctions. It opened in Sieć with nothing to change in Hydrolog and replaces the fixture built from Nogat's example; `test_smoke.py` checks the guide's numbers of Nash by Lutz.

### Removed

- **Breaking:** `hydrolog.cli.commands` (the old subcommands `tc`, `cn`, `scs`, `uh` with the options `--length`,
  `--area`, `--tc`, `--csv`, ...). The old names have no aliases: e.g. `hydrolog scs --cn 72
  --precipitation 50` is now `hydrolog scs effective --cn 72 --precipitation-mm 50`;
  the CSV export is replaced by `--json` (the full result envelope).
- **Breaking - the `hydrolog[spatial]` (Kartograf) extra:** Hydrolog no longer depends on Kartograf (or on Obserwator, formerly IMGWTools; the extra `pmaxtp` brings Obserwator back for `precip pmaxtp` only, [ADR-0018](decisions/0018-pmaxtp-through-obserwator.md)). Soil rasters are downloaded by Kartograf (`download_soil`), and HSG is computed by Hydrolog (`hydrolog.soil`, the `hydrolog[raster]` extra). The `all` extra includes `raster`, `mcp` and `viz`. The `spatial` extra (and the Kartograf dependency) was removed from `pyproject.toml`.
- The MCP server option `--lang`, the `lang` option of the `commands` group, the Polish and English variants of the guide templates (`_data/agents/agents.{pl,en}.md`, `llms.{pl,en}.md`; one English template remains), the `visualization` extra (renamed `viz`), and the documents `docs/DEVELOPMENT_STANDARDS.md`, `docs/IMPLEMENTATION_PROMPT.md` and `tmp/raport_nash_urban.md` (the standards live in the Nogat repository).
- **Breaking - `NashIUH.from_tc()` (the author's decision of 2026-11-05; branch `fix/remove-nash-from-tc`):** the Nash parameters from the time of concentration (`tlag = lag_ratio × tc`, `K = tlag / n`), deprecated since 0.6.2 because `tlag = 0.6 × tc` is the SCS relation and has no basis for the Nash cascade, are gone with what only they used: `FormulaRenderer.nash_from_tc_formulas()` and the report's formulas for `model_params["estimation_method"] == "from_tc"` (such parameters are now reported as given n and K). The catalog (`uh nash`, `hydrograph generate`) and the GUI never offered it; a hand-off whose `provenance.runoff` says `"nash_estimation": "from_tc"` (Hydrograf) opens in Hydrogram zlewni as the given n and K of its runoff. Migration: `NashIUH.from_lutz()` or `NashIUH.from_urban_regression()` for an ungauged watershed, or `NashIUH(n=..., k_min=...)` with calibrated values; where the old numbers must be reproduced, `NashIUH(n=3.0, k_min=0.6 * tc_min / 3.0)` gives them (with the typical-range warnings of given n and K).
- **Breaking - library methods that nothing in Hydrolog, its docs or the other tools called (the author's cleanup of dead code, branch `refactor/dead-code`):** `TerrainAnalysis.mean_elevation_from_dem()` (use `numpy.average`), `StreamNetwork.get_segments_by_order()` (filter `segments` by `order`), `Hydrograph.coarsened()` (take `discharge_m3s[::factor]`) and the property `LutzCalculationResult.tp_iuh_min` (`NashIUH.time_to_peak_min` gives the same `(n - 1) × K`), with their tests; the private `statistics._hydrological_year.split_half_years()`; the commented-out `plot_generator_result()` of `hydrolog.visualization` (disabled in 0.6.2, "to be removed"); the unused report texts `FORMULA_EXPLANATIONS`, `REFERENCES` and `GLOSSARY` of `hydrolog.reports.templates` and the unused constant `CORE_FAMILY_MAX` of `hydrolog.catalog.spec` (the contract test keeps the standard's 10). Web GUI: the unused `ResultView` (the panels compose the result's parts), the constants `THEMES` and `STATES`, the re-exports `Fragment`, `createRef` and `useReducer` and the label `nothing`; 138 names that no other module imported are no longer exported. Duplicates merged: `_atomic.is_same_file` serves `soil hsg` and the `--output` check, `gui._public.route_path` both middlewares, and `gui serve` takes the GUI's own `require_gui_extra` and `url_of` (`gui serve --check` without the extra now names the module that fails to import).

### Fixed

- **Locked `opentelemetry-api` 1.45.1 had CVE-2026-126360** (the dependency audit of CI failed on it): `uv.lock` now pins 1.45.2, the fixed version; no other package moved.
- **Web GUI: `alpha` of `stats mann-kendall` and `stats homogeneity` read „Parametr α”** (the author's decision of 2026-11-13): there it is the significance level of the test, not a parameter of a formula, as `alpha` is in the beta hyetograph (`precip hietogram`, `hydrograph generate`, `report generate`) and in the filter of `stats baseflow`. The two tests now label it „Poziom istotności α”; the option, its values and the results are unchanged.
- **Web GUI on Windows did not start**: the page's scripts came as `text/plain` where the Windows registry maps `.js` so, and the browser refuses a module script of that type; the GUI now serves `.js`, `.mjs` and `.css` with their own types on every platform.
- **Reports on Windows had CRLF line ends**: `report generate` and `HydrologyReportGenerator` write UTF-8 with `"\n"` line ends on every platform, like every other file Hydrolog writes.
- **Files written by parallel calls on Windows** (`report generate`, `soil hsg`, `commands guide --output`): Windows refuses to replace a file while another thread or process replaces it or holds it open, so of calls that wrote the same output at once some could end with `OutputError` (`io_error`, `output_unwritable`, „Access is denied”); in the test of the shared writer 5 of 8 threads writing one file were refused. The move over the target now waits out such a refusal for up to a second, so the last call wins on Windows as it does on Linux and macOS; elsewhere nothing changes.
- **A directory given as an input file on Windows** was `data_error` with `details.reason` `unreadable`, because Windows refuses to open a directory with a permission error; it is `not_a_file` there too, as on Linux and macOS.
- **Web GUI: „Instrukcja” on a phone pushed the page sideways** in a wider system font (macOS, Windows): a sentence of an example („Poza typowym zakresem…”) did not wrap.
- **Web GUI: Statystyka przepływów's file box said „undefined”** under a session file: the text of its size (`file.session`, „plik sesji · {size}”) was missing.
- **Wording of the longest flow path.** `flow_path_length_km` and `flow_path_slope_m_per_m` are described as starting at the hydraulically most distant point of the watershed (usually on the divide, possibly on a ridge inside it), not "on the divide", in docstrings, the catalog, the GUI, the guide and the docs (NEH 630 ch. 15; Fang et al. 2005); numbers unchanged.
- **Citations of the time of concentration methods** (docstrings, catalog, report, GUI; [ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md)): the NRCS lag equation is NEH 630 ch. 15, eq. 15-4 (TR-55, cited until now, does not contain it). The FAA formula is AC 150/5320-5B, fig. 7 and table I (not 5A, never verified, and not 5D or 5C, which lack it). The low-slope offset of Kerby and Kerby-Kirpich is Cleveland, Thompson, Fang and Li (2012), TxDOT 0-6382-P1; the cited "0-6544-1, Use of the Kerby-Kirpich approach" does not exist. Kirpich's L and S are those of Fang et al. (2005, TxDOT 0-4696-1, eq. 3.14) and Mota and Kobiyama (2015). The option texts of `tc kirpich`, `tc nrcs`, `tc faa` and `tc kerby` describe these inputs (the slope of the overland flow surface, not a mean ground slope), and the `slopes_from_relief` notice no longer says that the time of concentration takes the given channel slope.
- **Web GUI: the time axis of a short chart** (`web/src/charts/scale.js`): a span up to about two hours took a 5 or 10 min tick step, which is no exact decimal of an hour, so the labels in hours had ten decimals („0,1666666667”) and overlapped on the small charts (e.g. „Opad i straty narastająco” of a 1 h rain). The steps are now 6 and 12 min (0,1 and 0,2 h).
- **Fisher–Tippett distribution for minima (`LowFlowAnalysis.fit_fisher_tippett()`).** Versions < 1.0.0 fitted the distribution of *maxima* (GEV) to annual minima and read its quantile at p = 1/T; that is the mirror distribution, which describes the middle of the sample correctly but not the left tail of the distribution of smallest values. Now the GEV is fitted to the *negated* minima (`min(x) = −max(−x)`), and the quantile is `−genextreme.isf(p, c, loc=−loc, scale=scale)`. A synthetic sample of 1000 annual minima from the Gumbel distribution for minima (loc = 50, scale = 8), T = 100 years: **−3821 → 13.26** (theoretical value 13.20); Weibull distribution (k = 2, loc = 1, scale = 5): T = 100 years 1.24 → 1.51 (theory 1.50), T = 1000 years 0.33 → 1.18 (theory 1.16). The reported `shape` is `c` from `scipy.stats.genextreme`, `loc` refers to the minima. Details: `docs/COMPUTATION_PATHS.md` section 3.6.
- **Clark UH for a duration D that is not a multiple of the time step (`ClarkIUH.to_unit_hydrograph()`).** The S-curve was shifted by `round(D/dt)` steps but divided by D, so the hydrograph volume was `round(D/dt)·dt/D` mm: for D = 1.5·dt **1.333 → 1.000 mm**, for D = 2.5·dt 0.8 → 1.000 mm; for D < dt/2 the function raised `ValueError` (`s_curve[:-0]`). Now the delayed S-curve is interpolated linearly, the volume is 1 mm for any D > 0, and for integer multiples of the step the result is unchanged. The result is continuous in D (formerly a jump every half step).
- `WatershedParameters.calculate_tc("giandotti")`: `elevation_mean_m == 0` (mean elevation 0 m a.s.l.) was treated as a missing value and replaced by the middle of the elevation range.
- **Calculation report (`HydrologyReportGenerator`).** The unit hydrograph section now documents the hydrograph used in the calculation (`result.unit_hydrograph_result`: model, parameters, ordinates, time to peak), not a sketch from assumed values (formerly e.g. Nash n = 3, K = 30 min, triangular ordinates); the λ coefficient in Ia = λ·S comes from the calculation (formerly a constant 0.2); the concentration time section uses the formula inputs as `calculate_tc()` does (formerly NRCS took the nonexistent key `mean_slope_percent`, Giandotti computed the max − min difference instead of mean − min); the Kerby and Kerby-Kirpich formulas show the slope after the small-slope correction, and the Kirpich channel time is given in hours and minutes; the Snyder formulas work without L and Lc; the number of hydrograph steps in the convolution section is the actual one.
- `calculate_monthly_statistics()`: a month with a single value had the confidence interval `[mean, mean]` (a claim of an exactly known mean) and NumPy warnings; now the standard deviation, coefficient of variation, skewness and confidence interval of such a month are `NaN` (`null` in JSON). A month without any value raises `InvalidParameterError` (`details.missing_months`), formerly a NumPy error.
- `StreamNetwork`: the Shreve method ended with `KeyError` in the network statistics (Shreve orders are not contiguous, while the bifurcation and length ratios assumed contiguous ones); `classify()` looped forever for a network with a cycle or with a nonexistent `upstream_id` at a source, and without any source silently left all orders equal to 0 - now `InvalidParameterError` (`details.reason` = `cycle` / `unknown_upstream`), and the segments remain unchanged.
- `RatingCurve`: `fit(h0_initial=...)` with an infinite value, `NaN` or a value not lower than the lowest water level ended with a bare `ValueError` from SciPy (starting point outside the bounds) - now `InvalidParameterError` (`details.option` = `h0_initial`, `details.maximum` = the lowest water level, hint in `hint`); measurements with `NaN` or infinity are rejected when the object is created. Non-convergence and a power-law overflow are `RatingCurveFitError` (code `calculation_error`, also an `InvalidParameterError`, so an `except` written for versions < 1.0.0 still works), with the cause in `__cause__`.
- **`cn` alongside a watershed in `hydrograph generate` and `report generate` (NRCS concentration time).** A `cn` given alongside a watershed overrode the CN only in SCS-CN, while `tc_method=nrcs` computed the retention S of the lag equation (TR-55, ch. 3; NEH-630, ch. 15) from the file's CN; a watershed without `cn` given `cn` and `nrcs` ended with the error "missing: cn", contrary to the option description. Now `cn` is the CN of the whole calculation (the watershed receives it before the concentration time), so `tc_parameters`, `HydrographRun.watershed` and the report are consistent (the report stated "S = 98.78 mm (for CN = 72)" in the concentration time section next to "CN = 85" in the SCS-CN section). A watershed with CN 60 in the file (L = 12 km, S = 0.025), `cn` = 85, beta rainfall 50 mm/120 min: tc **657.7 → 322.1 min**, Qmax **27.64 → 55.62 m³/s**, time to peak 440 → 240 min.
- **Snyder unit hydrograph in `HydrographGenerator`.** The discrete convolution treats the unit hydrograph as the response to 1 mm of effective rainfall in one step, while the generator built the hydrograph for the standard duration tD = tL/5.5 regardless of the step. Snyder (1938; USACE-HEC, HEC-HMS Technical Reference Manual, "Snyder Unit Hydrograph Model"; Chow, Maidment, Mays 1988) gives a correction for a different duration D: tLR = tL + 0.25(D − tD), tpR = tLR + D/2, qpR = qp·tL/tLR; the `SnyderUH` class had it (`generate(duration_min=...)`), the generator did not use it. Now for the `snyder` model it calls `generate(timestep_min=dt, duration_min=dt)`: `uh_time_to_peak_min` of the result is tpR, and the report documents Δt equal to the step (formerly "Δt = 59.0 min" for a 5-minute hyetograph). For a step shorter than tD the unit hydrograph peak is higher and earlier than for tD, for a longer one lower and later. A 45 km² watershed, L = 12 km, Lc = 6 km, CN 72, beta rainfall 50 mm/120 min, 5 min step: unit hydrograph tp **354.2 → 313.7 min**, qp **1.379 → 1.542 m³/s/mm**; hydrograph Qmax **9.76 → 10.90 m³/s (+11.8%)**, time to peak 405 → 365 min.
- **Snyder unit hydrograph: the whole recession and the peak qpR (`SnyderUH.generate()`, `uh snyder`, the `snyder` model of `hydrograph generate`).** The ordinates were a gamma curve of one fixed shape (n = 3.7) scaled to qp, cut at the triangular time base tb = 0.556·A/qpR and rescaled to 1 mm. tb shrinks as Cp grows while the curve does not, so the cut came at 4.6% of the peak for Cp = 0.6 and at 20% for Cp = 0.8 (a 5-minute step), and the runoff hydrograph ended in a near-vertical drop (Hydrograf front-end test, 2026-11-01: Kamiennik 37.23 km², Ct 1.65, Cp 0.8, from about a fifth of the peak to zero in 30 min, with the right volume). The peak of the ordinates was not qpR either: Cp acted only through the cut (Cp 0.4 → 1.0 moved qpR 0.64 → 1.60 m³/s/mm and the peak of the ordinates only 1.02 → 1.22). Now the ordinates are the gamma unit hydrograph through the peak, q(t) = qpR·[(t/tpR)·e^(1 − t/tpR)]^K, with K from its volume of 1 mm, Γ(K)·(e/K)^K = V/(qpR·tpR) (Asquith and Roussel 2007, USGS SIR 2007-5243, eq. 2 and 4), and they run until 99.99% of the volume has passed (the new default of `total_duration_min`; `time_base_min` stays tb, a parameter of the method). Kamiennik, PMAXTP 1 h p = 1%, 5-minute step: Ct 1.65/Cp 0.8 **Qmax 3.852 → 4.487 m³/s** at 410 min, the steepest 5-minute fall **5.7% → 1.2%** of the peak, the hydrograph ends at 1735 min instead of 1025; the defaults Ct 1.5/Cp 0.6 Qmax 3.990 → 3.701 m³/s, end 1230 → 2210 min; the volume is unchanged. In the case of the entry above (45 km², D = 5 min) the unit hydrograph peak is **1.542 → 1.432 m³/s/mm (= qpR)** and Qmax 10.90 → 10.12 m³/s. A Cp for which no hydrograph of 1 mm can have the peak qpR (below about 10⁻¹² or above about 10⁵) raises `InvalidParameterError` (`validation_error`). Details: COMPUTATION_PATHS.md, section 3.4.7.
- **`WatershedParameters.calculate_tc()` for FAA and Kerby: overland flow time, not channel length.** FAA (AC 150/5320-5B, 1970, fig. 7) and Kerby (1959) are formulas for overland flow time; Kerby derived his for roads up to 366 m (1200 ft; Roussel et al. 2005, TxDOT Report 0-4696-2; TxDOT Hydraulic Design Manual, ch. 4, section 11), and the library warns for FAA outside 0.015–3 km. The method, however, substituted `channel_length_km` and the channel slope (even when the watershed had `overland_length_km` and `overland_slope_m_per_m`), so every watershed with a channel got a result outside the formula's range, and the report labelled 10 km of channel as "overland flow length". Now FAA and Kerby take `overland_length_km` and `overland_slope_m_per_m` and require them (see Breaking; `kerby_kirpich` serves watersheds with a channel). A watershed with a 10 km channel (S = 0.02), overland flow 0.2 km (S = 0.01), C = 0.5, N = 0.4: FAA **155.3 → 27.7 min** (the `length_km=10.0` warning disappears), Kerby **173.2 → 32.8 min** (two warnings disappear).
- **`WatershedParameters.calculate_tc("nrcs")`: the mean watershed slope, not the channel slope.** The NRCS lag equation (NEH 630, ch. 15, eq. 15-4) uses the mean ground slope of the watershed Y, not the slope of the flow path; the method took `channel_slope_m_per_m` before `mean_slope_m_per_m`. Now it takes `mean_slope_m_per_m` only (and the longest flow path as its length, [ADR-0019](decisions/0019-tc-from-the-inputs-its-source-defines.md)). The same watershed (channel S = 2.0%, ground slope 2.5%): **463.9 → 414.9 min (−10.6%)**.
- **File writes by parallel calls (MCP server).** `report generate` and `soil hsg` wrote the file through a temporary name depending only on the PID, while the MCP server runs calls in threads of one process: two simultaneous calls with the same output file shared the temporary file, so the second ended with `OutputError` (`io_error`, `[Errno 2] No such file or directory: '.<file>.<pid>.tmp'`) despite valid data. All three writes (`report generate`, `soil hsg`, `commands guide --output`) now use the shared `hydrolog._atomic.atomic_output` with a unique (random) temporary file name in the target directory. Four threads writing the same file, 40 trials (160 calls): `report generate` **44 errors → 0**, `soil hsg` **28 → 0**, `commands guide` 0 → 0.
- **Annual extremes only from complete hydrological years (`stats flood-frequency`, `stats low-flow`, `LowFlowAnalysis.annual_minima()`).** Maxima and minima were taken from every hydrological year present in the dates, including incomplete ones, and nothing said so: a typical export from calendar years (1991-01-01 … 2020-12-31) gave 31 "years", including the first without November and December and the last (2021) with only November and December 2020, whose "maximum" and "minimum" are the base level, not the extreme of the year (KZGW 2017 and WMO No. 1029, 2009 use complete years of observations for the analysis). Now a year (1 XI – 31 X) enters the sample only if the series has a value for every day (365 days, 366 in a year with 29 February; a missing date or `NaN` excludes the year), and the skipped years are listed by the `incomplete_years` notice (with the number of days with data: `1991 (304 of 365 days), 2021 (61 of 365 days)`) and the `incomplete_years` result field; a series without 3 complete years is a `calculation_error` with `details.incomplete_years`. A synthetic calendar series 1991–2020 (a flood on 15 III and a low flow on 15 IX every year): **31 → 29 years** (1992–2020); the 2021 "maximum" equal to **5.0** (median of complete years 13.0) and "minimum" 5.0 (median 2.2) no longer enter the sample; GEV for T = 100 years **16.08 → 16.35**, Fisher–Tippett for T = 100 years **2.002 → 1.968**. A day without a value costs the whole year: with gaps, fill in the data or give the annual maxima directly (`stats flood-frequency` without dates). `stats characteristic`, `stats daily` and `stats monthly` are unchanged.
- **`stats low-flow`: empirical frequency in the non-exceedance convention.** The `empirical` block was the result of `LowFlowAnalysis.empirical_frequency()`: values in descending order with the *exceedance* probability, so the deepest low flow of the sample got the exceedance return period (3 years from `tests/fixtures/daily_flows_3y.csv`: minimum 1.66 → P = 0.75, **T = 1.33**), while the `fisher_tippett` block (and WMO No. 1029; Tallaksen and van Lanen, 2004) computes T from the non-exceedance probability. Now `empirical` is `LowFlowEmpiricalFrequency` (`LowFlowAnalysis.empirical_non_exceedance()`): `values_ascending` (ascending), `non_exceedance_probabilities` F = m/(n+1) and `return_periods` T = 1/F; the same minimum 1.66 has F = 0.25 and **T = 4** (the deepest low flow of n years has T = n + 1), so empirical points can be compared with `fisher_tippett.return_periods` without conversion. `LowFlowAnalysis.empirical_frequency()` is unchanged (exceedance convention, described in the docstring), and `plot_non_exceedance_curve()` accepts both forms.
- **`RatingCurve.fit()` and `hydrometrics rating-curve`: H₀ starting point from the data.** The fixed default `h0_initial = 0.0` had to lie below the lowest water level, so every gauge with a reading ≤ 0 (levels below the gauge zero, e.g. −10 cm, are normal) ended with `validation_error` (exit code 2): `hydrolog hydrometrics rating-curve --water-levels=-10,5,20,40,80,120 --discharges 0.5,1.2,2.5,4.8,10.1,17.3` → "h0_initial must be a finite number below the lowest water level (-10), got 0.0". Now the default `h0_initial=None` picks the start `min(H) − max(1, 0.1·(max(H) − min(H)))` (in the unit of the levels), so the fit works for any levels: a = 0.004917, b = 1.640, H₀ = −25.17 (R² = 0.9998), the same as for any explicit start below the lowest level. An explicitly given value is validated as before (finite and lower than the lowest level). On 60 synthetic curves (levels in cm and m, positive and negative, noise 1–8 %) starts from 0.1 to 1 range below the lowest level always gave the best least-squares solution.
- **Clark UH: a time step above 2R no longer gives a negative ordinate (`ClarkIUH.generate_iuh()`, `to_unit_hydrograph()`, `uh clark`).** The linear reservoir of the Clark IUH is the Muskingum scheme with X = 0, whose weight of the previous outflow, (2R − Δt)/(2R + Δt), is negative for Δt > 2R: `ClarkIUH(tc_min=60, r_min=2).generate_iuh(timestep_min=5)` returned a negative ordinate (−0.00031 per minute) and an oscillating tail. Now a step above 2R is refused with `InvalidParameterError` (`validation_error`, `details.option` = `timestep_min`, `details.reason` = `unstable_timestep`, `details.maximum` = 2R, and a hint with the limit); a step up to 2R gives a non-negative IUH. The recurrence moved into the shared routing kernel (`hydrolog.routing._kernels`) and gives the same values to rounding. The docstring no longer calls the scheme "Muskingum-Cunge" (it is Muskingum with X = 0).
- **Web GUI: a long result draws, a result that does not draw is an error (branch `fix/gui-test-defects`).** Nash with n = 200 and K = 1500 min in Hydrogram zlewni (a unit hydrograph of 150 002 steps and a hydrograph of 150 073, a 6 MB answer) ended with `RangeError: Maximum call stack size exceeded` in the chart of the unit hydrograph (`Math.max(...ordinates)`), left the previous result (13,94 m³/s) on screen under „Wynik aktualny” and kept it after „Wyczyść”. The charts and their domains spread no series into a call any more (`extent` in `web/src/charts/scale.js`, used by the chart scales, the unit hydrograph and Statystyka); a line, area or step with more than four points per column of the plot is drawn thinned to each column's first, last, lowest and highest point and its first gap (`thinPoints` in `web/src/charts/series.js`; the tables and exports keep every value); a time axis beyond the longest step takes whole weeks, still at most 13 ticks. The charts and Wyniki of Hydrogram zlewni stand in `RenderGuard` (`web/src/ui/render-guard.js`): an error while they render or draw shows „Nie udało się pokazać wyniku” in their place, the badge „Błąd wyświetlania” and the state under the panel Dane, never the previous result; the next result or „Wyczyść” draws again. The library is unchanged: its Nash unit hydrograph lasts 5·n·K + Δt by default (`NashIUH.to_unit_hydrograph`), so for n = 200 about three quarters of it lie below 1 % of the peak. Browser tests: the 12/300 → 200/1500 run of the report and a stubbed result that cannot be drawn.
- **Web GUI: the empty Hydrogram zlewni links its worked example**, „Przykład w instrukcji” to `instrukcja/#przyklad` in step 1, as the other empty sections do.
- **Web GUI: „Wyczyść” of Wszystkie polecenia returns to the first visit**: no command chosen (the hash `#polecenia`), no form and no result, the hint to choose a command; it formerly kept the command and its hash. The state under the form says „uzupełnij pola wymagane” while required fields are empty (formerly „formularz poprawny”).
- **Web GUI: Snyder's L and Lc only once.** Hydrogram zlewni's Snyder block shows the watershed's „Długość do środka ciężkości” (`Lc_km`) with Ct and Cp; L is the watershed's `channel_length_km` (step 1), both sent as `snyder_length_km`/`snyder_centroid_length_km` and required on those watershed fields (the separate „Długość cieku”/„Do środka ciężkości” fields are gone). Stored inputs of earlier visits move their own L and Lc into empty watershed fields; a received hand-off's `runoff.snyder_*` fills missing watershed fields and, when different, the watershed's stay and the origin's detail says so. Sieć's subcatchment does the same with its watershed fields.
- **Description of the cover `residential_medium`** (catalog in English and Polish, `LandCover` and the table of `hydrolog.runoff.cn_lookup`): it said 1/4–1/2 acre lots, 25–38 % impervious, but its curve numbers 57/72/81/86 are the TR-55 row "Residential, 1/3 acre, 30 % impervious" (table 2-2a, p. 2-5); it now says so and cites the row. The values are unchanged.
- **Description of the cover `residential_low`** (catalog in English and Polish, `LandCover` and the table of `hydrolog.runoff.cn_lookup`): it said 1–2 acre lots, 12–20 % impervious, but its curve numbers 46/65/77/82 are the TR-55 row "Residential, 2 acre, 12 % impervious" alone (table 2-2a, p. 2-5; the 1 acre, 20 % row is 51/68/79/84); it now says so and cites the row. The values are unchanged.

---

## [0.7.0] - 2026-03-26

### Added

#### `hydrolog.statistics` - Hydrological statistics
New module for the statistical analysis of hydrological series.

**Characteristic values (`characteristic.py`):**
- `CharacteristicValues` — dataclass with the NNQ, SNQ, SSQ, SWQ, WWQ values
- `DailyStatistics` — daily statistics (percentiles, quantiles)
- `MonthlyStatistics` — monthly statistics
- `calculate_characteristic_values()` — determination of characteristic values (Polish system)
- `calculate_daily_statistics()` — statistics for daily series
- `calculate_monthly_statistics()` — statistics for monthly series

**Frequency analysis of maximum flows (`high_flows.py`):**
- `FrequencyAnalysisResult` — distribution fit results (parameters, AIC, goodness-of-fit tests)
- `FloodFrequencyAnalysis` — frequency analysis with 4 distributions:
  - LogNormal (two-parameter)
  - GEV (Generalized Extreme Value)
  - Pearson III (shifted Gamma)
  - Weibull (extreme values, minima)
- Goodness-of-fit tests: Kolmogorov-Smirnov, Anderson-Darling
- Akaike information criterion (AIC) for choosing the best distribution

**Frequency analysis of minimum flows (`low_flows.py`):**
- `LowFlowFrequencyResult` — Fisher-Tippett fit results
- `LowFlowSequence` — low-flow sequence (duration, deficit, intensity)
- `LowFlowAnalysisResult` — complete low-flow analysis results
- `LowFlowAnalysis` — low-flow analysis:
  - Fisher-Tippett distribution fit for minimum flows
  - Detection of low-flow sequences with the threshold method

**Trend test (`stationarity.py`):**
- `MannKendallResult` — test result (statistic S, Z, p-value, trend direction)
- `mann_kendall_test()` — non-parametric Mann-Kendall test (KZGW 2017)

**Shared types (`_types.py`, `_hydrological_year.py`):**
- Data types for hydrological series
- Hydrological year utilities (1 XI – 31 X)

#### `hydrolog.hydrometrics` - Hydrometrics
New module for hydrometric analyses.

**Rating curve (`rating_curve.py`):**
- `RatingCurveResult` — curve fit results (parameters a, H₀, b, R², RMSE)
- `WaterLevelZones` — gauge zones by the Rybczyński method (NTW/STW/WTW)
- `FrequencyDistributionResult` — frequency and duration distribution of water levels
- `RatingCurve` — rating curve Q = a × (H − H₀)^b fitted with NLS
- `WaterLevelFrequency` — frequency and duration analysis of water levels + Rybczyński zones

#### `hydrolog.visualization.statistics` — 10 statistical visualization functions
- `plot_frequency_curve()` — frequency curve with confidence intervals
- `plot_frequency_comparison()` — comparison of distributions on one plot
- `plot_non_exceedance_curve()` — flow duration curve (FDC)
- `plot_daily_characteristics()` — characteristic values NNQ–WWQ
- `plot_monthly_statistics()` — monthly statistics (box plot)
- `plot_annual_hydrographs()` — annual hydrographs
- `plot_flow_histogram()` — flow distribution histogram
- `plot_low_flow_sequences()` — low-flow sequences against the series
- `plot_rating_curve()` — rating curve with measurement data
- `plot_water_level_frequency()` — frequency and duration of water levels

### Changed
- SciPy moved from an optional to a required dependency (core dependency).
  Previously used optionally by `runoff.nash_iuh`; since v0.7.0 it is required
  by the `statistics` module (GEV, Pearson III, Fisher-Tippett distributions).

### Testing
- 70 new unit tests (754 → 824):
  - `test_characteristic.py` — characteristic values, daily/monthly statistics
  - `test_high_flows.py` — frequency analysis of maximum flows
  - `test_low_flows.py` — Fisher-Tippett, low-flow detection
  - `test_stationarity.py` — Mann-Kendall test
  - `test_rating_curve.py` — rating curve, Rybczyński zones
  - `test_visualization_statistics.py` — 10 visualization functions

---


## [0.6.4] - 2026-03-25

### Added

#### `hydrolog.morphometry.WatershedParameters` - Extended Fields
- 8 new Optional fields for full integration with all tc methods and UH models:
  - `runoff_coeff` — FAA tc method (Rational method C, 0-1)
  - `retardance` — Kerby/Kerby-Kirpich tc (roughness coefficient, 0.02-0.80)
  - `overland_length_km` — Kerby-Kirpich overland segment length [km]
  - `overland_slope_m_per_m` — Kerby-Kirpich overland slope [m/m]
  - `Lc_km` — Length to watershed centroid along main channel [km] (Nash Lutz, Snyder)
  - `manning_n` — Manning's roughness coefficient (Nash Lutz)
  - `urban_pct` — Urbanized area percentage [%] (Nash Lutz)
  - `forest_pct` — Forested area percentage [%] (Nash Lutz)
- `calculate_tc()` extended from 3 to 6 methods: added `"faa"`, `"kerby"`, `"kerby_kirpich"`
- `from_dict()`/`to_dict()` updated for all new fields (backward compatible)

#### `hydrolog.reports` - FAA/Kerby/Kerby-Kirpich Formula Rendering
- `FormulaRenderer.faa_tc()` — LaTeX rendering: `tc = 22.213 × (1.1 - C) × L^{0.5} / S^{1/3}`
- `FormulaRenderer.kerby_tc()` — LaTeX rendering: `tc = 36.37 × (L × N)^{0.467} × S^{-0.2335}`
- `FormulaRenderer.kerby_kirpich_tc()` — LaTeX composite: `tc = t_{ov} + t_{ch}`
- `generate_tc_section()` extended with full formula rendering for 3 new tc methods
- Polish method descriptions added to `templates.py` (TC_METHODS, FORMULA_EXPLANATIONS, REFERENCES)

#### `hydrolog.reports.generator` - Hietogram Type Validation
- `generate()` emits `UserWarning` if `config.hietogram_type` is not in valid set

#### `hydrolog.runoff.generator` - UH Ordinates Exposure
- `HydrographGeneratorResult.unit_hydrograph_result` — new Optional field storing computed UH result
  - Populated automatically by `HydrographGenerator.generate()`
  - Stores concrete UH type (UnitHydrographResult, NashUHResult, ClarkUHResult, SnyderUHResult)
  - Backward compatible (defaults to None)

### Changed
- `hydrolog.cli.commands.uh` — Snyder `--ct` default changed from 2.0 to **1.5** (aligned with Python class default; SI typical range 1.35-1.65)
- `hydrolog.runoff.snyder_uh` — `generate()` docstring documents why default timestep (30 min) differs from other models (5 min)
- `hydrolog.runoff.generator` — `generate()` docstring documents explicit timestep passing to all UH models

### Fixed
- `hydrolog.reports.sections.scs_cn` — added None guards for `retention_mm` and `initial_abstraction_mm` (prevents crash when data missing)
- `hydrolog.visualization.water_balance` — `F = max(0.0, P - Pe - Ia)` prevents negative continuing abstraction
- `hydrolog.precipitation.hietogram` — `HietogramResult.intensities_mm` docstring clarified: contains incremental depths [mm], not intensity rates [mm/h]
- `hydrolog.precipitation.interpolation` — `Station.x`/`y` docstring clarified: must use consistent coordinate system; unit affects IDW distance calculations

### Testing
- 45 new tests (754 total, all passing):
  - 30 tests for WatershedParameters extension (fields, validation, tc methods, serialization)
  - 10 tests for reports (FormulaRenderer, tc sections, SCS-CN guards, hietogram validation)
  - 6 tests for UH ordinates exposure in HydrographGeneratorResult (all 4 models)
  - 2 tests for CLI Snyder Ct default alignment (integrated from worktree)

### Documentation
- Comprehensive audit of all 8 docs files against codebase v0.6.3
- Fixed outdated API examples: SCSCN class-based, BetaHietogram.generate()
- Corrected SCS formulas: Pe = (P-Ia)²/(P-Ia+S), tb = 5.0×tp
- Updated PRD with +7 user stories for missing modules (visualization, reports, Nash/Clark/Snyder)
- DEVELOPMENT_STANDARDS: added TYPE_CHECKING, dataclass, warnings patterns
- Moved NASH_AUDIT_REPORT.md to tmp/

---

## [0.6.3] - 2026-03-23

### Added

#### `hydrolog.time.concentration` - FAA Method
- `ConcentrationTime.faa()` - FAA (Federal Aviation Agency) method for overland/sheet flow tc calculation
  - Formula: `tc = 22.213 × (1.1 - C) × L^0.5 / S^(1/3)`
  - Parameters: C (rational method runoff coefficient), L (overland flow length in km), S (slope in m/m)
  - Source: FAA Advisory Circular AC 150/5320-5D (2013)
  - CLI support: `hydrolog tc faa --length 0.15 --slope 0.02 --runoff-coeff 0.6`

#### `hydrolog.time.concentration` - Kerby Method
- `ConcentrationTime.kerby()` - Kerby (1959) method for overland/sheet flow tc calculation
  - Formula: `tc = 36.37 × (L × N)^0.467 × S^(-0.2335)`
  - Parameters: L (overland flow length in km), N (Kerby retardance roughness coefficient), S (slope in m/m)
  - Low-slope adjustment: for S < 0.002, S_adj = S + 0.0005 (Cleveland et al. 2012)
  - Source: Kerby, W.S. (1959). "Time of concentration for overland flow." Civil Engineering, 29(3), 174
  - CLI support: `hydrolog tc kerby --length 0.10 --slope 0.008 --retardance 0.40`

#### `hydrolog.time.concentration` - Kerby-Kirpich Composite Method
- `ConcentrationTime.kerby_kirpich()` - Kerby-Kirpich composite method for time of concentration
  - Combines Kerby (overland flow) and Kirpich (channel flow) for composite tc estimation
  - Formula: `tc = t_overland(Kerby) + t_channel(Kirpich)`
    - Kerby: `tc_ov = 36.37 × (L_ov × N)^0.467 × S_ov^(-0.2335)`
    - Kirpich: `tc_ch = 3.981 × L_ch^0.77 × S_ch^(-0.385)`
  - Low-slope adjustment (Cleveland et al. 2012): for S < 0.002, S_adj = S + 0.0005 (applied to both segments)
  - Source: Roussel et al. (2005). TxDOT Report 0-4696-2
  - CLI support: `hydrolog tc kerby-kirpich --ov-length 0.25 --ov-slope 0.008 --retardance 0.40 --ch-length 5.0 --ch-slope 0.005`

### Changed
- `refactor(time): harmonize API consistency across all tc methods` — rename `_SCS_LAG_*` to `_NRCS_*`, fix CLI formatting, add 28 parity tests (90 → 118)

### Fixed
- `fix(types): resolve all 88 mypy errors across the codebase` — float() casts, type narrowing, TYPE_CHECKING imports, assert guards
- `docs: fix stale content and cross-document inconsistencies` — CHANGELOG, SCOPE, PROGRESS, COMPUTATION_PATHS, PRD, DEV_STANDARDS, IMPL_PROMPT

---

## [0.6.2] - 2026-03-22

### Added

#### `hydrolog.runoff.nash_iuh` - Lutz Calculation Results
- `LutzCalculationResult` - new dataclass storing all intermediate calculation steps
  - Input parameters: L_km, Lc_km, slope, manning_n, urban_pct, forest_pct
  - Intermediate values: P1, geometric_factor, urban_factor, forest_factor
  - Output values: tp_hours, up_per_hour, f_N_target, n, k_hours, k_min
  - Computed properties: tp_min, lag_min, lag_hours
- `NashIUH.lutz_params` - stores LutzCalculationResult when created via `from_lutz()`

#### `hydrolog.reports` - Enhanced Report Generation
- `figures_dir` parameter in `HydrologyReportGenerator.generate()`
  - Automatically embeds PNG figures in report as Markdown images
  - Expected files: hietogram_beta.png, hydrogram_jednostkowy_nash.png, rainfall_runoff.png, bilans_wodny.png, generator_dashboard.png
- Automatic Lutz method documentation in Nash UH section
  - Full calculation steps with LaTeX formulas when `lutz_params` provided
  - All intermediate values automatically substituted
  - Literature references (Lutz 1984, KZGW 2017)

#### Reports — full calculation formulas for all UH models
- **Nash IUH** — 3 parameter estimation methods in reports:
  - `from_tc` — formulas tlag = λ·tc, K = tlag/n with substituted values
  - `from_lutz` — 6 steps of the Lutz method (P1, tp, up, f(N), N, K) with substitutions
  - `from_urban_regression` — 3 regression steps (tL, k, N) with an input table and a reference
- **Clark IUH** — rozbudowana sekcja raportu:
  - R estimation from the R/Tc method with substitutions
  - Routing coefficient C1 = Δt/(2R+Δt) with values
  - Time-area histogram (two-part HEC-HMS) with Tc
  - Lag time tlag ≈ Tc/2 + R
- **Snyder UH** — full formulas with numerical substitutions:
  - tL, tD = tL/5.5, tp, qp, tb — all with values
  - W50, W75 — hydrograph widths with correct metric constants
  - Correction for a non-standard duration (tLR, tpR, qpR)
- **6 nowych metod** `FormulaRenderer`:
  - `nash_from_tc_formulas()`, `nash_from_lutz_formulas()`,
    `nash_urban_regression_formulas()`
  - `clark_from_tc_r_ratio()`, `clark_routing_coefficient()`,
    `clark_time_area_substituted()`
- Detekcja `estimation_method` w `model_params` we wszystkich sekcjach UH

### Changed
- Terminology: "ordynaty" → "rzędne" throughout codebase (Polish orthography; both mean "ordinates")
  - Updated: templates.py, formatters.py, convolution.py, visualization modules
- `hydrolog.runoff.nash_iuh` module docstring updated with literature references:
  - Nash (1957), Lutz (1984), Rosso (1984), KZGW (2017)
- `hydrolog.time.concentration` module enhanced with literature references:
  - `kirpich()`: Added Ponce (2014), CivilWeb (2023); clarified original units (minutes, slope in m/m)
  - `nrcs()`: Added TR-55, HEC-HMS references; clarified tc vs tl vs tp distinction
  - `giandotti()`: Added Grimaldi (2012), Michailidi (2018); verified original output in hours
- **BREAKING:** `ConcentrationTime.scs_lag()` renamed to `ConcentrationTime.nrcs()`
  - Method calculates tc directly using the NRCS equation
  - Formula simplified: `tc = 0.01416 × L^0.8 × (S+25.4)^0.7 × Y^-0.5`
  - All references in codebase updated (CLI, reports, morphometry, tests)
- `hydrolog.visualization`: Temporarily disabled `plot_generator_result()` export (to be removed)

### Deprecated

#### `hydrolog.runoff.nash_iuh.NashIUH.from_tc()`
- **Will be removed in version 1.0.0**
- This method uses the SCS relationship `lag = 0.6 × Tc` which was developed for
  the SCS Unit Hydrograph, NOT for the Nash model
- The Nash model lag time (`n × K`) is a mathematical result of the cascade,
  not an input parameter
- **Recommended alternatives:**
  - Use `from_lutz()` for ungauged watersheds (Lutz 1984, KZGW 2017)
  - Provide `n` and `K` directly to the constructor

### Fixed

#### Metric formula corrections
- **Snyder W50/W75** — corrected metric constants:
  - W50: 5.87 → **0.1783** (imperial 770 / conv^1.08, conv ≈ 2323)
  - W75: 3.35 → **0.1019** (imperial 440 / conv^1.08)
  - The previous values gave results overestimated ~33×
- **Clark histogram czas-powierzchnia** — zmiana na standard HEC-HMS:
  - Was: `1.414·(t/Tc)^0.5 - 0.414·(t/Tc)^1.5` (singularity at t=0)
  - Now: two-part with exponent 1.5 (symmetric, centroid = Tc/2)
- **SCS Lag docstring** — constant 7182 → **7069** (the code was correct, the error was in the documentation)

### Documentation
- Added `docs/NASH_AUDIT_REPORT.md` - architectural audit of Nash IUH module
  - Literature verification (10 sources)
  - Analysis of `from_tc()` vs `from_lutz()` methods
  - Recommendations for module architecture
- Added `docs/COMPUTATION_PATHS.md` - computation paths for all UH models
  - Compatibility matrix: model × parameter estimation method
  - ASCII flow diagrams for each model (SCS, Nash, Clark, Snyder)
  - Literature verification for each computation path
  - Code examples for correct usage
  - "Common errors and how to avoid them" section
  - 10 literature references
- `SCSCN` documentation — added the Woodward et al. (2003) reference for λ=0.05
  with a warning about the need to recalibrate CN
- `from_urban_regression()` documentation — full history of the
  imperial→metric conversion with references (Sarma 1969, Rao 1972, Kołodziejczyk 2017)
- ~~New file `docs/NASH_URBAN_REGRESSION_DERIVATION.md`~~ — mathematical proof
  of the constant conversion 0.831→1.28 and 0.569→0.56 with numerical verification (file removed)

### Testing
- 5 new Clark IUH tests (histogram: symmetry, no singularity, centroid)
- Updated Nash urban regression reference tests
- Total: 626 tests (all pass)

---

## [0.6.1] - 2026-03-20

### Added

#### `hydrolog.runoff.nash_iuh` - Urban Regression Method
- `NashIUH.from_urban_regression()` - parameter estimation for urbanized catchments
  - Estimates Nash model parameters (N, k) from catchment area, effective
    precipitation, rainfall duration, and urbanization index
  - Power-law regression equations: tL = 1.28·A^0.46·(1+U)^(-1.66)·H^(-0.27)·D^0.37,
    k = 0.56·A^0.39·(1+U)^(-0.62)·H^(-0.11)·D^0.22
  - Verified against reference spreadsheet (Obliczenia.xlsx)
  - References: Rao, Delleur, Sarma (1972), ASCE J. Hydraulics Div. 98(HY7)

### Testing
- 11 new tests for urban regression method (including reference value verification)
- Total: 621 tests (all passing)

---

## [0.6.0] - 2026-01-21

### Added

#### `hydrolog.reports` - Report Generation Module
New module for generating comprehensive hydrological calculation reports in Markdown format.

**Main classes:**
- `HydrologyReportGenerator` - main class for report generation
  - `generate()` - create report from HydrographGeneratorResult
  - Supports all UH models (SCS, Nash, Clark, Snyder)
  - Outputs complete calculation procedure with formulas
- `ReportConfig` - configuration dataclass
  - `tc_method` - concentration time method (kirpich, nrcs, giandotti)
  - `uh_model` - unit hydrograph model (scs, nash, clark, snyder)
  - `include_formulas` - include LaTeX formulas (default: True)
  - `include_tables` - include data tables (default: True)
  - `max_table_rows` - maximum rows before abbreviation (default: 50)

**Formatters (`formatters.py`):**
- `FormulaRenderer` - render LaTeX formulas with substituted values
  - SCS-CN formulas: retention, initial abstraction, effective precipitation
  - Time of concentration: Kirpich, SCS Lag, Giandotti
  - Unit hydrograph: SCS, Nash IUH, Clark IUH, Snyder UH
  - Convolution and water balance formulas
- `TableGenerator` - generate Markdown tables
  - Parameters tables with alignment
  - Time series tables with automatic abbreviation
  - Water balance summary tables
  - Hydrograph results tables

**Report sections (`sections/`):**
- `generate_watershed_section()` - watershed parameters and shape indicators
- `generate_tc_section()` - concentration time calculations
- `generate_hietogram_section()` - precipitation temporal distribution
- `generate_scs_cn_section()` - SCS-CN effective precipitation
- `generate_uh_section()` - unit hydrograph (all models)
- `generate_convolution_section()` - discrete convolution
- `generate_water_balance_section()` - water balance summary

**Templates (`templates.py`):**
- Polish section headers and labels
- Method descriptions (Kirpich, SCS, Nash, Clark, Snyder)
- AMC condition descriptions
- Literature references
- Glossary of hydrological terms

**Report structure:**
1. Watershed parameters (geometry, terrain, shape indicators)
2. Time of concentration (formula with substitutions)
3. Hietogram (parameters, temporal distribution table)
4. SCS-CN effective precipitation (S, Ia, Pe formulas with values)
5. Unit hydrograph (model-specific formulas and ordinates)
6. Convolution (formula, procedure description)
7. Hydrograph results (Qmax, tp, V, time series)
8. Water balance (summary table with percentages)

### Testing
- 37 new tests for reports module
- Total: 610 tests (all passing)

### Documentation
- Updated CHANGELOG.md
- Report examples in module docstrings

---

## [0.5.2] - 2026-01-21

### Changed
- Removed unused `imgwtools` from required dependencies in `pyproject.toml`
- IMGWTools is now only imported directly in Hydrograf where it is actually used
- Updated documentation (CLAUDE.md, SCOPE.md) to reflect dependency changes

---

## [0.5.1] - 2026-01-21

### Fixed
- **CRITICAL:** `SCSUnitHydrograph.peak_discharge()` - corrected constant from `2.08` to `0.208`
  - Previous implementation caused ~10x overestimation of Qmax
  - Correct formula: `qp = 0.208 * A / tp` [m³/s per mm]
  - Updated docstring with proper mathematical derivation
  - Reference: USDA TR-55 triangular unit hydrograph approximation

### Changed
- Synchronized version numbers: `__init__.py` and `pyproject.toml` now both show `0.5.1`
- Updated test expectations in `test_runoff.py` for correct peak discharge values

### Added

#### `hydrolog.morphometry.WatershedParameters` - GIS Integration Interface
New dataclass for standardized data exchange between GIS systems (Hydrograf, QGIS, ArcGIS) and Hydrolog.

- `WatershedParameters` - complete watershed parameters container
  - Required: area_km2, perimeter_km, length_km, elevation_min_m, elevation_max_m
  - Optional: name, elevation_mean_m, mean_slope_m_per_m, channel_length_km, channel_slope_m_per_m, cn, source, crs
  - `from_dict()` / `from_json()` - create from API response or JSON
  - `to_dict()` / `to_json()` - export for serialization
  - `to_geometry()` - convert to WatershedGeometry
  - `to_terrain()` - convert to TerrainAnalysis
  - `calculate_tc(method)` - calculate concentration time (kirpich, nrcs, giandotti)
  - Computed properties: `width_km`, `relief_m`

#### Factory methods for morphometry classes
- `WatershedGeometry.from_dict()` - create from dictionary
- `TerrainAnalysis.from_dict()` - create from dictionary

#### Documentation
- `docs/INTEGRATION.md` - comprehensive integration guide for GIS systems
  - JSON schema for data exchange
  - Usage examples with Hydrograf
  - Implementation details for third-party integrations

### Removed (from v0.5.0-unreleased)
- `SnyderUH.from_lag_time()` - Estimated L and Lc from lag time (impractical, these parameters should be measured from maps/GIS)
- `SnyderUH.from_tc()` - Delegated to `from_lag_time()`, same issue
- `NashIUH.from_moments()` - Required variance and lag time from observed hydrograph (not practical for ungauged catchments)
- `ClarkIUH.from_recession()` - Required recession constant from observed hydrograph

### Testing
- 35 new tests for WatershedParameters and from_dict() methods
- 15 new integration tests for Hydrograf API workflow (`tests/integration/test_hydrograf_integration.py`)
  - Full workflow: JSON → WatershedParameters → HydrographGenerator
  - Batch processing of multiple watersheds
  - Data validation and error handling
  - Round-trip serialization
- Total: 573 tests (558 unit + 15 integration, all passing)

---

## [0.5.0] - 2026-01-19

### Added

#### `hydrolog.visualization` - Visualization Module
New module for graphical presentation of hydrological results.
Requires optional dependencies: `pip install hydrolog[visualization]`

**Hietogram plots (`hietogram.py`):**
- `plot_hietogram()` - precipitation hyetograph with intensity bars and optional cumulative line
- `plot_hietogram_comparison()` - comparison of total vs effective precipitation

**Hydrograph plots (`hydrograph.py`):**
- `plot_hydrograph()` - runoff hydrograph Q(t) with peak annotation and volume
- `plot_unit_hydrograph()` - unit hydrograph for any model (SCS, Nash, Clark, Snyder)

**Combined plots (`combined.py`):**
- `plot_rainfall_runoff()` - classic rainfall-runoff plot with inverted hietogram on top
- `plot_generator_result()` - full dashboard with water balance table

**Unit hydrograph comparison (`unit_hydrograph.py`):**
- `plot_uh_comparison()` - multiple UH models on one plot with comparison table

**Water balance (`water_balance.py`):**
- `plot_water_balance()` - SCS-CN water balance visualization (bars or pie)
- `plot_cn_curve()` - P → Pe relationship with AMC variants

**Morphometry (`morphometry.py`):**
- `plot_hypsometric_curve()` - hypsometric curve h/H vs a/A with HI integral
- `plot_elevation_histogram()` - elevation distribution histogram

**Network (`network.py`):**
- `plot_stream_order_stats()` - three-panel stream network statistics
- `plot_bifurcation_ratios()` - bifurcation ratios by stream order

**Interpolation (`interpolation.py`):**
- `plot_stations_map()` - precipitation station map with weights

**Styles (`styles.py`):**
- `setup_hydrolog_style()` - configure matplotlib/seaborn for consistent styling
- `COLORS`, `LABELS_PL`, `PALETTE` - color scheme and Polish labels
- `get_color()`, `get_label()` - helper functions
- `format_time_axis()`, `add_peak_annotation()`, `add_stats_box()`, `add_watermark()`

#### `hydrolog.runoff.nash_iuh` - Lutz Method
- `NashIUH.from_lutz()` - parameter estimation from catchment characteristics
  - Estimates Nash model parameters (n, K) from physiographic data
  - Input parameters: L, Lc, slope, Manning's n, urban%, forest%
  - Numerical solution of f(N) equation using Brent's method
  - Verified against KZGW (2017) Table C.2 (accuracy < 0.001)
  - Reference: Lutz W. (1984), Universität Karlsruhe

#### `hydrolog.precipitation` - Euler Type II Hyetograph
- `EulerIIHietogram` - DVWK Euler Type II hyetograph for design storms

#### `hydrolog.runoff.snyder_uh` - Enhancements
- `SnyderUHResult` - added duration tracking (`duration_hours` field)
- Water balance formula for Snyder time base calculation

### Changed
- **BREAKING:** Unified UH model API — `area_km2` parameter moved to constructor for all UH models
- Enhanced README.md documentation:
  - Nash model theory (reservoir cascade, IUH formula, properties)
  - All parameter estimation methods (from_tc, from_moments, from_lutz)
  - Lutz method algorithm with full equations
  - Influence of physiographic parameters on runoff
  - New visualization module section with examples

### Fixed
- `fix(snyder)`: Corrected time-to-peak formula and updated notation
- `fix(snyder)`: Corrected SI unit formulas for Snyder UH model

### Dependencies
- Added optional `visualization` dependency group: matplotlib>=3.7, seaborn>=0.12

### Testing
- 53 new tests for visualization module
- 17 new tests for Lutz method
- Total: 538 unit tests (all passing)

---

## [0.4.0] - 2026-01-19

### Added

#### `hydrolog.cli` - Command-Line Interface
- `hydrolog tc` - concentration time calculation
  - `kirpich` - Kirpich formula
  - `scs-lag` - SCS Lag equation
  - `giandotti` - Giandotti formula
- `hydrolog cn` - Curve Number lookup (TR-55)
  - `lookup` - look up CN for HSG and land cover
  - `list` - list available land cover types
  - `range` - show CN range for a land cover
- `hydrolog scs` - SCS-CN runoff calculation
  - AMC conditions support (I, II, III)
  - Custom initial abstraction coefficient
- `hydrolog uh` - unit hydrograph generation
  - `scs` - SCS dimensionless unit hydrograph
  - `nash` - Nash cascade IUH
  - `clark` - Clark IUH
  - `snyder` - Snyder synthetic UH
  - Output formats: table, CSV, JSON

#### `hydrolog.runoff.clark_iuh` - Clark IUH
- `ClarkIUH` - Clark Instantaneous Unit Hydrograph
  - Translation via time-area histogram
  - Linear reservoir routing
  - Simplified elliptical time-area curve
- `ClarkIUHResult` and `ClarkUHResult` dataclasses
- `from_recession()` - parameter estimation from recession analysis
- `from_tc_r_ratio()` - estimation from Tc and R/Tc ratio

#### `hydrolog.runoff.snyder_uh` - Snyder UH
- `SnyderUH` - Snyder Synthetic Unit Hydrograph
  - Empirical relationships (Snyder, 1938)
  - Parameters: L, Lc, Ct, Cp
  - Width calculations at 50% and 75% of peak
- `SnyderUHResult` dataclass
- `from_lag_time()` - parameter estimation from lag time
- `from_tc()` - estimation from concentration time

#### `hydrolog.runoff.cn_lookup` - CN Lookup Tables
- `get_cn()` - look up CN for HSG and land cover
- `lookup_cn()` - detailed lookup with result object
- `get_cn_range()` - CN range for land cover type
- `list_land_covers()` - list available land covers
- `calculate_weighted_cn()` - area-weighted CN calculation
- `LandCover` - 20 land cover types (TR-55)
- `HydrologicCondition` - poor, fair, good conditions

#### `hydrolog.runoff.nash_iuh` - Nash IUH
- `NashIUH` - Nash Instantaneous Unit Hydrograph
  - Nash cascade model with n reservoirs and K storage constant
  - `generate()` - IUH generation at specified timestep
  - `to_unit_hydrograph()` - S-curve conversion to D-minute UH
  - `from_tc()` - parameter estimation from concentration time
  - `from_moments()` - parameter estimation from lag time and variance
- `IUHResult` and `NashUHResult` dataclasses

### Changed
- **BREAKING:** `ConcentrationTime.scs_lag()` signature changed (now renamed to `nrcs()`):
  - `length_m` → `length_km` (meters to kilometers)
  - `slope_percent` → `slope_m_per_m` (percent to dimensionless)
- Added parameter range warnings to all concentration time methods

### Fixed
- Corrected NRCS constant: `7182` → `7069` (proper metric conversion)
- Fixed docstring examples in `scs_cn.py` (Pe = 7.09 mm, not 12.89 mm)

### Dependencies
- Added `scipy` as dependency (for gamma functions in Nash IUH)
- Added optional `kartograf` dependency for spatial/soil data

### Testing
- 412 unit tests (all passing)
- 27 new CLI tests
- 41 Clark IUH tests
- 43 Snyder UH tests
- 38 CN lookup tests

---

## [0.3.0] - 2026-01-18

### Added

#### `hydrolog.network` - River Network Classification

**Stream ordering (stream_order.py):**
- `StreamSegment` - dataclass for network segments
- `StreamNetwork` - main class for network analysis
- `OrderingMethod` - enum (STRAHLER, SHREVE)
- `NetworkStatistics` - complete network statistics
- Strahler stream ordering method
- Shreve stream ordering method
- Bifurcation ratio calculation
- Length ratio calculation

**Utility functions:**
- `bifurcation_ratio()` - calculate Rb between orders
- `drainage_density()` - streams length / watershed area
- `stream_frequency()` - streams count / watershed area

#### `hydrolog.precipitation.interpolation` - Spatial Interpolation

**Interpolation methods:**
- `Station` - dataclass for measurement stations
- `thiessen_polygons()` - Thiessen/Voronoi polygon method
- `inverse_distance_weighting()` - IDW interpolation
- `areal_precipitation_idw()` - grid-based IDW averaging
- `isohyet_method()` - isohyet contour method
- `arithmetic_mean()` - simple station average

**Result dataclasses:**
- `ThiessenResult` - weights and contributions
- `IDWResult` - interpolated values with weights
- `IsohyetResult` - zone-based precipitation

#### Testing & Quality
- 60 new tests for network and interpolation (210 total)
- 95% code coverage

---

## [0.2.0] - 2026-01-18

### Added

#### `hydrolog.morphometry` - Morphometric Parameters

**Geometric parameters (geometric.py):**
- `WatershedGeometry` - main class for geometric analysis
- `GeometricParameters` - dataclass with area, perimeter, length, width
- `ShapeIndicators` - dataclass with shape coefficients:
  - Form factor (Horton)
  - Compactness coefficient (Gravelius)
  - Circularity ratio (Miller)
  - Elongation ratio (Schumm)
  - Lemniscate ratio (Chorley)

**Terrain analysis (terrain.py):**
- `TerrainAnalysis` - elevation and slope analysis
- `ElevationParameters` - min, max, mean elevation, relief
- `SlopeParameters` - watershed and channel slopes
- `mean_elevation_from_dem()` - DEM-based calculation

**Hypsometric curve (hypsometry.py):**
- `HypsometricCurve` - hypsometric analysis from DEM
- `HypsometricResult` - curve data and statistics
- Hypsometric integral calculation
- Elevation percentiles

#### Testing & Quality
- 47 new tests for morphometry (150 total)
- 95% code coverage

---

## [0.1.0] - 2026-01-18

### Added

#### `hydrolog.time` - Concentration Time
- `ConcentrationTime.kirpich()` - Kirpich formula (L in km, S in m/m)
- `ConcentrationTime.nrcs()` - NRCS equation (metric units)
- `ConcentrationTime.giandotti()` - Giandotti formula

#### `hydrolog.precipitation` - Hyetographs
- `HietogramResult` - dataclass with time series results
- `BlockHietogram` - uniform intensity distribution
- `TriangularHietogram` - triangular distribution with configurable peak
- `BetaHietogram` - Beta distribution for realistic storm patterns

#### `hydrolog.runoff` - Rainfall-Runoff
- `SCSCN` - SCS Curve Number calculations
  - Maximum retention S calculation
  - Initial abstraction Ia calculation
  - Effective precipitation Pe calculation
  - AMC conditions (I, II, III) support
- `SCSUnitHydrograph` - SCS dimensionless unit hydrograph
  - Standard NRCS tabulated ratios
  - Lag time and time to peak calculations
- `convolve_discrete()` - discrete convolution function
- `HydrographGenerator` - complete rainfall-runoff transformation
  - Integration with hyetograph module
  - Water balance tracking
  - Runoff coefficient calculation

#### Testing & Quality
- 103 unit tests
- 94% code coverage
- Full type hints (mypy)
- Black formatting

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| **0.1.0** | 2026-01-18 | SCS-CN hydrograph, hyetographs, concentration time |
| **0.2.0** | 2026-01-18 | Morphometric parameters |
| **0.3.0** | 2026-01-18 | Interpolation + river network |
| **0.4.0** | 2026-01-19 | CLI + Clark IUH + Snyder UH + CN lookup |
| **0.5.0** | 2026-01-19 | Visualization module (matplotlib/seaborn) |
| **0.5.1** | 2026-01-21 | Fix SCS peak discharge constant |
| **0.5.2** | 2026-01-21 | Remove unused imgwtools dependency |
| **0.6.0** | 2026-01-21 | Report generation module |
| **0.6.1** | 2026-03-20 | Nash urban regression method |
| **0.6.2** | 2026-03-22 | UH report formulas + metric corrections |
| **0.6.3** | 2026-03-23 | FAA + Kerby + Kerby-Kirpich tc, API audit |
| **0.6.4** | 2026-03-25 | WatershedParams extension + UH ordinates + docs audit |
| **0.7.0** | 2026-03-26 | Hydrological statistics + Hydrometrics |
| **Unreleased** | - | 1.0.0 (in preparation): Stable API: command catalog, CLI from catalog, MCP server, HSG (`hydrolog.soil`), result serialization, calculation fixes |
