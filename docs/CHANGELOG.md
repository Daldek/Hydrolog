# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

First release of the stable API (1.0.0, not yet released; `develop` carries 1.0.0.dev0), made together with the adoption of the Nogat standard 2.1 (decisions in [DECISIONS.md](DECISIONS.md)). From that version on semantic versioning applies: command and option names, `operation_id`s, the `hydrolog-result/1`, `hydrolog-error/1` and domain result schemas, and the error codes and exit codes are public API. The library classes (`SCSCN`, `HydrographGenerator`, `NashIUH`, `ClarkIUH`, `SnyderUH`, `ConcentrationTime`, hyetographs, `WatershedParameters`, statistics, hydrometrics, reports, visualization) keep their names and signatures; changes to them are additions or bug fixes described below. **Breaking** entries are relative to 0.7.0; the ones that also change the unreleased 1.0.0.dev0 of `develop` say so ("since 1.0.0.dev0").

### Added

#### Command catalog (`hydrolog.catalog`) and operations layer (`hydrolog.operations`)
A single source of truth for the library, the CLI, the MCP server and the agent guides: 38 commands in 14 groups (`tc`, `cn`, `scs`, `precip`, `uh`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`, `soil`, `report`, `config`, `commands`); list: `hydrolog commands list`.
- `Command` and `Option`: English texts with the Polish translation next to them (`summary_pl`, `description_pl`, `rules_pl`; serialized under `i18n.pl`), units, ranges, `one_of` groups, a meaning for every value of a choice, examples with a result, derived `effects`, `check` and `families` (the group, plus `core` for the ten main commands); the declaration checks itself at import (summary at most 100 characters, summary + description + rules at most 600) (ADR-0001). `data_commands()`, `get_command()`, `catalog_document()`, `input_schema()`, `capture_warnings()`.
- `hydrolog.operations`: one public, typed function per command (`tc_kirpich`, `hydrograph_generate`, `stats_flood_frequency`, `soil_hsg`, ...); it returns a result object with `to_dict()`/`to_json()` or an `OperationOutput` (result, notices, written files).
- The `hydrolog-result/1` result envelope: `schema`, `tool`, `version`, `command`, `check`, `status`, `result`, `notices` (`level`, `code`, `message`), `inputs` and, for lists, `page` (ADR-0002); `commands list` and `commands schema` page with `--limit` and `--cursor`.
- The `hydrolog-error/1` error document and the closed `ERROR_CODES` registry (see "Error registry and exit codes" below); `HydrologError` has `code`, `details` and `hint`.
- New exception classes: `InputDataError`, `MissingDependencyError`, `ForbiddenPathError`, `NotFoundError`, `OutputError`, `ConflictError` (exported from `hydrolog`).

#### Result serialization (`hydrolog._serialization`)
- `JsonResultMixin` with `to_dict()` and `to_json()` in all result classes (runoff, precipitation, morphometry, network, statistics, hydrometrics, soil); `NaN` and infinities become `null`, NumPy arrays become lists, an unknown type raises `TypeError`. `WatershedParameters.to_dict()`/`to_json()` are unchanged.

#### File inputs
- Series (`input_file` + `value_column`/`date_column`), rainfall stations (`stations_file`), network segments (`segments_file`) and watersheds (`watershed_file`) as CSV (comma or semicolon, UTF-8) or JSON; columns are selected by exact name or without the unit suffix (`Q` finds `Q [m3/s]`).
- An IMGWTools series export (`export_series` CSV) is read without preprocessing; `WatershedParameters` JSON is the proposed `catchment_characteristics` format in Retman.

#### `hydrolog.soil` - Hydrologic soil groups (HSG)
Rules moved from Kartograf 0.8.0 (`kartograf.hydrology.hsg`, ADR-025); Kartograf stays responsible for downloading rasters (`download_soil`).
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
- `report generate`, `soil hsg` and `commands guide` write exactly one plain file given by `--output`; an existing file is replaced only with `--force` (otherwise exit 4, `conflict`, `details.reason = output_exists`, `details.paths`, before anything is computed); `--check` returns the plan (`hydrolog-plan/1`: `result.targets[]` with `option`, `path`, `action` = `write` | `replace` | `conflict`) without effects. The files written are `result.files[]` = `{path, size_bytes, sha256, status}`, `status` `written` | `replaced`. Hydrolog has no store and downloads nothing: inputs come from files written by Kartograf (`soil download --output-dir`) and IMGWTools (`series export --output`).

#### Settings and `config show` (ADR-0004)
- `hydrolog._settings`: two settings, `lang` (default `pl`) and `log_level` (default `warning`); precedence option > `HYDROLOG_<KEY>` > `NOGAT_<KEY>` > `[hydrolog]`, then `[nogat]` in `nogat.toml` (`NOGAT_CONFIG`, else the user config directory) > default; a broken or non-UTF-8 file is ignored.
- `hydrolog config show [--json]` (also an MCP tool and a Python function) prints each setting with its source (option, environment, file, default), the settings file, and no credentials and no store.
- `-v/--verbose` and `-q/--quiet` set the log level of the CLI.

#### Top-level Python API
- `hydrolog.list_commands()`, `hydrolog.command_schema()`, `hydrolog.validate_command()`, `hydrolog.check_command()` and `hydrolog.run_command()` (the `hydrolog.catalog` functions, imported lazily); `hydrolog.__all__` is these five functions, `__version__` and the error classes. Importing `hydrolog` reads no files and imports no numerical library.

#### Result schemas
- JSON Schemas of every result document (`hydrolog-<group>-<command>/1`, plus `hydrolog-plan/1`, `hydrolog-config/1`, `hydrolog-guide/1`, `hydrolog-command-list/1`) in `src/hydrolog/schemas/`, generated by `scripts/generate_result_schemas.py`, shipped in the wheel and named by `result.schema` in `commands schema`.

#### Error registry and exit codes (ADR-0005)
- `ERROR_CODES` holds the codes of the shared Nogat registry that Hydrolog ends a call with: `internal_error` (1), `validation_error` (2), `not_found` (3), `conflict` (4), `missing_dependency` (6), `data_error` (7), `io_error` (9), `forbidden` (12), `calculation_error` (13), `cancelled` (130), `terminated` (143). Finer precision is `details.reason`; Hydrolog adds no code of its own. `hydrolog._errors` is generated from the vendored `schemas/nogat/error_registry.json` (`scripts/generate_errors.py`); a contract test compares it and validates error documents against `error-1`.
- The last line of stderr is always the `hydrolog-error/1` document as compact JSON, with and without `--json`; SIGTERM ends with `terminated` (143), Ctrl-C with 130 and no document.

#### Packaging, tooling and metadata
- The package lives in `src/hydrolog`, ships `py.typed` and has a dynamic version (`hydrolog.__version__`); the console scripts are `hydrolog` and `hydrolog-mcp`. uv and `uv.lock` manage the environment; ruff (format and lint with the `D` rules) and mypy `strict` replace Black and flake8; `scripts/gate.sh` runs the gate (ruff, mypy, pytest with coverage of at least 80%, commit check), CI runs it on Linux, macOS and Windows; the tests are split into `tests/unit`, `tests/integration` and `tests/contract`.
- Metadata for discovery (AGI-10.1): the `pyproject.toml` description (the shortest text of the description ladder), keywords, classifiers (`Typing :: Typed`), SPDX license, project URLs (Documentation, Changelog, Issues).
- `hydrolog.visualization` raises `MissingDependencyError` (hint: `pip install hydrolog[viz]`) when the extra is missing; formerly a bare `ImportError`.

#### Documentation
- English throughout (ECO-005): README, `docs/USAGE.md`, PRD, SCOPE, INTEGRATION, COMPUTATION_PATHS, CHANGELOG and the agent guides; Polish names are kept in parentheses where agents search for them. The plans moved to `docs/plans/`; architecture decisions are in `docs/decisions/` (ADR-0001 to ADR-0006) with the index `docs/DECISIONS.md`; `SECURITY.md`, `CONTRIBUTING.md`, `CONTRIBUTORS.md` and the pull request template were added.
- `docs/PROGRESS.md` is reduced to the three sections of DOC-6.1 (status, next, open questions); history lives in this file and the git log.

### Changed

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
  line; the exit code comes from `ERROR_CODES` (2, 3, 4, 6, 7, 9, 12, 13, 1; 130 after Ctrl-C,
  143 after SIGTERM). An unknown command is `not_found` (code 3) with a hint, a syntax error is
  `validation_error` (2).
- `hydrolog mcp [--allow-dir DIR]... [--allow-writes] [--tools FAMILIES]` starts the MCP server (the
  `hydrolog[mcp]` extra); `python -m hydrolog.cli` works like the `hydrolog` command.

#### Other changes
- `InvalidParameterError` is now also a `ValueError` (code with `except ValueError` still catches it); all Hydrolog exceptions have `code`, `details` and `hint`.
- `WatershedParameters.from_dict()` tolerates an extra `schema` key (e.g. `"hydrolog-catchment/1"`); `calculate_tc()` for an unknown method or a field missing for the method raises `InvalidParameterError` (`details.reason` = `choice` / `missing_field`, `details.missing` lists all missing fields), formerly a mix of `ValueError` and `InvalidParameterError`.
- `ClarkIUH.to_unit_hydrograph()`: `duration_min` and `timestep_min` must be positive and finite (`InvalidParameterError`).
- `HydrologyReportGenerator.generate()` has new optional arguments `ia_coefficient` and `tc_params`.
- `morphometry watershed`: when the watershed file gives `mean_slope_m_per_m` or `channel_slope_m_per_m`, the result (slopes from relief, as before) carries a `slopes_from_relief` note with both values, computed and given; formerly `tc watershed` computed with the given channel slope 0.02, while `morphometry watershed` reported 0.037 for the same file without explanation.
- The agent guide (`AGENTS.md`) describes the result of an operation function exactly: a result object with `to_dict()`/`to_json()` or `OperationOutput(result, notices, files)`; the `hydrolog.catalog` docstring and the 1.0.0 design point to the `hydrolog/operations/<group>.py` package (formerly `operations.py`).
- `LowFlowAnalysis.annual_minima()`, `fit_fisher_tippett()`, `empirical_frequency()` and `empirical_non_exceedance()` use only complete hydrological years: skipped years are reported by a `UserWarning`, and a series without a complete year is a `CalculationError` (formerly the minimum of every year present in the dates).
- `RatingCurve.fit(h0_initial=None)` and `hydrometrics_rating_curve(h0_initial=None)`: the default H₀ starting point is chosen from the data (formerly 0.0); the `h0_initial` option no longer has a default value in the command catalog.
- Tests: command catalog (CLI/Python parity for every example, catalog and envelope contracts, public API), CLI parser and rendering, MCP server (in-process client-server), serialization, settings, `hydrolog.soil` (ports of the Kartograf tests; raster tests skipped without `rasterio`), operations layer, agent guides (byte equality), error registry, concurrent file writes (`hydrolog._atomic`), regressions of the fixes from the "Fixed" section (with numbers before and after the fix).

#### Nogat standard 2.1
- The package, tooling, error registry, settings, writing commands, MCP server and documentation follow the Nogat standard 2.1: see the "Added" sections above and the breaking entries under "Breaking changes". Deliberate deviations from the standard are listed in `CLAUDE.md`.
- The error document `hydrolog-error/1` omits `hint` and `command` when there is none (formerly `null`) and its `title` is English unless `lang="pl"` is requested. An output file that cannot be written is `io_error` with `details.reason = "output_unwritable"`.

### Removed

- **Breaking:** `hydrolog.cli.commands` (the old subcommands `tc`, `cn`, `scs`, `uh` with the options `--length`,
  `--area`, `--tc`, `--csv`, ...). The old names have no aliases: e.g. `hydrolog scs --cn 72
  --precipitation 50` is now `hydrolog scs effective --cn 72 --precipitation-mm 50`;
  the CSV export is replaced by `--json` (the full result envelope).
- **Breaking - the `hydrolog[spatial]` (Kartograf) extra:** Hydrolog no longer depends on Kartograf (or on IMGWTools). Soil rasters are downloaded by Kartograf (`download_soil`), and HSG is computed by Hydrolog (`hydrolog.soil`, the `hydrolog[raster]` extra). The `all` extra includes `raster`, `mcp` and `viz`. The `spatial` extra (and the Kartograf dependency) was removed from `pyproject.toml`.
- The MCP server option `--lang`, the `lang` option of the `commands` group, the Polish and English variants of the guide templates (`_data/agents/agents.{pl,en}.md`, `llms.{pl,en}.md`; one English template remains), the `visualization` extra (renamed `viz`), and the documents `docs/DEVELOPMENT_STANDARDS.md`, `docs/IMPLEMENTATION_PROMPT.md` and `tmp/raport_nash_urban.md` (the standards live in the Nogat repository).

### Fixed

- **Fisher–Tippett distribution for minima (`LowFlowAnalysis.fit_fisher_tippett()`).** Versions < 1.0.0 fitted the distribution of *maxima* (GEV) to annual minima and read its quantile at p = 1/T; that is the mirror distribution, which describes the middle of the sample correctly but not the left tail of the distribution of smallest values. Now the GEV is fitted to the *negated* minima (`min(x) = −max(−x)`), and the quantile is `−genextreme.isf(p, c, loc=−loc, scale=scale)`. A synthetic sample of 1000 annual minima from the Gumbel distribution for minima (loc = 50, scale = 8), T = 100 years: **−3821 → 13.26** (theoretical value 13.20); Weibull distribution (k = 2, loc = 1, scale = 5): T = 100 years 1.24 → 1.51 (theory 1.50), T = 1000 years 0.33 → 1.18 (theory 1.16). The reported `shape` is `c` from `scipy.stats.genextreme`, `loc` refers to the minima. Details: `docs/COMPUTATION_PATHS.md` section 3.6.
- **Clark UH for a duration D that is not a multiple of the time step (`ClarkIUH.to_unit_hydrograph()`).** The S-curve was shifted by `round(D/dt)` steps but divided by D, so the hydrograph volume was `round(D/dt)·dt/D` mm: for D = 1.5·dt **1.333 → 1.000 mm**, for D = 2.5·dt 0.8 → 1.000 mm; for D < dt/2 the function raised `ValueError` (`s_curve[:-0]`). Now the delayed S-curve is interpolated linearly, the volume is 1 mm for any D > 0, and for integer multiples of the step the result is unchanged. The result is continuous in D (formerly a jump every half step).
- `WatershedParameters.calculate_tc("giandotti")`: `elevation_mean_m == 0` (mean elevation 0 m a.s.l.) was treated as a missing value and replaced by the middle of the elevation range.
- **Calculation report (`HydrologyReportGenerator`).** The unit hydrograph section now documents the hydrograph used in the calculation (`result.unit_hydrograph_result`: model, parameters, ordinates, time to peak), not a sketch from assumed values (formerly e.g. Nash n = 3, K = 30 min, triangular ordinates); the λ coefficient in Ia = λ·S comes from the calculation (formerly a constant 0.2); the concentration time section uses the formula inputs as `calculate_tc()` does (formerly NRCS took the nonexistent key `mean_slope_percent`, Giandotti computed the max − min difference instead of mean − min); the Kerby and Kerby-Kirpich formulas show the slope after the small-slope correction, and the Kirpich channel time is given in hours and minutes; the Snyder formulas work without L and Lc; the number of hydrograph steps in the convolution section is the actual one.
- `calculate_monthly_statistics()`: a month with a single value had the confidence interval `[mean, mean]` (a claim of an exactly known mean) and NumPy warnings; now the standard deviation, coefficient of variation, skewness and confidence interval of such a month are `NaN` (`null` in JSON). A month without any value raises `InvalidParameterError` (`details.missing_months`), formerly a NumPy error.
- `StreamNetwork`: the Shreve method ended with `KeyError` in the network statistics (Shreve orders are not contiguous, while the bifurcation and length ratios assumed contiguous ones); `classify()` looped forever for a network with a cycle or with a nonexistent `upstream_id` at a source, and without any source silently left all orders equal to 0 - now `InvalidParameterError` (`details.reason` = `cycle` / `unknown_upstream`), and the segments remain unchanged.
- `RatingCurve`: `fit(h0_initial=...)` with an infinite value, `NaN` or a value not lower than the lowest water level ended with a bare `ValueError` from SciPy (starting point outside the bounds) - now `InvalidParameterError` (`details.option` = `h0_initial`, `details.maximum` = the lowest water level, hint in `hint`); measurements with `NaN` or infinity are rejected when the object is created. Non-convergence and a power-law overflow are `RatingCurveFitError` (code `calculation_error`, also an `InvalidParameterError`, so an `except` written for versions < 1.0.0 still works), with the cause in `__cause__`.
- **`cn` alongside a watershed in `hydrograph generate` and `report generate` (NRCS concentration time).** A `cn` given alongside a watershed overrode the CN only in SCS-CN, while `tc_method=nrcs` computed the retention S of the lag equation (TR-55, ch. 3; NEH-630, ch. 15) from the file's CN; a watershed without `cn` given `cn` and `nrcs` ended with the error "missing: cn", contrary to the option description. Now `cn` is the CN of the whole calculation (the watershed receives it before the concentration time), so `tc_parameters`, `HydrographRun.watershed` and the report are consistent (the report stated "S = 98.78 mm (for CN = 72)" in the concentration time section next to "CN = 85" in the SCS-CN section). A watershed with CN 60 in the file (L = 12 km, S = 0.025), `cn` = 85, beta rainfall 50 mm/120 min: tc **657.7 → 322.1 min**, Qmax **27.64 → 55.62 m³/s**, time to peak 440 → 240 min.
- **Snyder unit hydrograph in `HydrographGenerator`.** The discrete convolution treats the unit hydrograph as the response to 1 mm of effective rainfall in one step, while the generator built the hydrograph for the standard duration tD = tL/5.5 regardless of the step. Snyder (1938; USACE-HEC, HEC-HMS Technical Reference Manual, "Snyder Unit Hydrograph Model"; Chow, Maidment, Mays 1988) gives a correction for a different duration D: tLR = tL + 0.25(D − tD), tpR = tLR + D/2, qpR = qp·tL/tLR; the `SnyderUH` class had it (`generate(duration_min=...)`), the generator did not use it. Now for the `snyder` model it calls `generate(timestep_min=dt, duration_min=dt)`: `uh_time_to_peak_min` of the result is tpR, and the report documents Δt equal to the step (formerly "Δt = 59.0 min" for a 5-minute hyetograph). For a step shorter than tD the unit hydrograph peak is higher and earlier than for tD, for a longer one lower and later. A 45 km² watershed, L = 12 km, Lc = 6 km, CN 72, beta rainfall 50 mm/120 min, 5 min step: unit hydrograph tp **354.2 → 313.7 min**, qp **1.379 → 1.542 m³/s/mm**; hydrograph Qmax **9.76 → 10.90 m³/s (+11.8%)**, time to peak 405 → 365 min.
- **`WatershedParameters.calculate_tc()` for FAA and Kerby: overland flow time, not channel length.** FAA (AC 150/5320-5A, 1966; AC 150/5320-5D, 2013) and Kerby (1959) are formulas for overland flow time; Kerby derived his for roads up to 366 m (1200 ft; Roussel et al. 2005, TxDOT Report 0-4696-2; TxDOT Hydraulic Design Manual, ch. 4, section 11), and the library warns for FAA outside 0.015–3 km. The method, however, substituted `channel_length_km` and the channel slope (even when the watershed had `overland_length_km` and `overland_slope_m_per_m`), so every watershed with a channel got a result outside the formula's range, and the report labelled 10 km of channel as "overland flow length". Now FAA and Kerby take `overland_length_km` and `overland_slope_m_per_m` and require them (see Breaking; `kerby_kirpich` serves watersheds with a channel). A watershed with a 10 km channel (S = 0.02), overland flow 0.2 km (S = 0.01), C = 0.5, N = 0.4: FAA **155.3 → 27.7 min** (the `length_km=10.0` warning disappears), Kerby **173.2 → 32.8 min** (two warnings disappear).
- **`WatershedParameters.calculate_tc("nrcs")`: mean watershed slope before channel slope.** The NRCS lag equation (TR-55, ch. 3; NEH-630, ch. 15) uses the mean ground slope of the watershed Y, not the slope of the flow path; the method took `channel_slope_m_per_m` before `mean_slope_m_per_m`. Now the order is `mean_slope_m_per_m`, `channel_slope_m_per_m`, relief/(L·1000) (Kirpich unchanged: channel, watershed, relief). The same watershed (channel S = 2.0%, ground slope 2.5%): **463.9 → 414.9 min (−10.6%)**.
- **File writes by parallel calls (MCP server).** `report generate` and `soil hsg` wrote the file through a temporary name depending only on the PID, while the MCP server runs calls in threads of one process: two simultaneous calls with the same output file shared the temporary file, so the second ended with `OutputError` (`io_error`, `[Errno 2] No such file or directory: '.<file>.<pid>.tmp'`) despite valid data. All three writes (`report generate`, `soil hsg`, `commands guide --output`) now use the shared `hydrolog._atomic.atomic_output` with a unique (random) temporary file name in the target directory. Four threads writing the same file, 40 trials (160 calls): `report generate` **44 errors → 0**, `soil hsg` **28 → 0**, `commands guide` 0 → 0.
- **Annual extremes only from complete hydrological years (`stats flood-frequency`, `stats low-flow`, `LowFlowAnalysis.annual_minima()`).** Maxima and minima were taken from every hydrological year present in the dates, including incomplete ones, and nothing said so: a typical export from calendar years (1991-01-01 … 2020-12-31) gave 31 "years", including the first without November and December and the last (2021) with only November and December 2020, whose "maximum" and "minimum" are the base level, not the extreme of the year (KZGW 2017 and WMO No. 1029, 2009 use complete years of observations for the analysis). Now a year (1 XI – 31 X) enters the sample only if the series has a value for every day (365 days, 366 in a year with 29 February; a missing date or `NaN` excludes the year), and the skipped years are listed by the `incomplete_years` notice (with the number of days with data: `1991 (304 of 365 days), 2021 (61 of 365 days)`) and the `incomplete_years` result field; a series without 3 complete years is a `calculation_error` with `details.incomplete_years`. A synthetic calendar series 1991–2020 (a flood on 15 III and a low flow on 15 IX every year): **31 → 29 years** (1992–2020); the 2021 "maximum" equal to **5.0** (median of complete years 13.0) and "minimum" 5.0 (median 2.2) no longer enter the sample; GEV for T = 100 years **16.08 → 16.35**, Fisher–Tippett for T = 100 years **2.002 → 1.968**. A day without a value costs the whole year: with gaps, fill in the data or give the annual maxima directly (`stats flood-frequency` without dates). `stats characteristic`, `stats daily` and `stats monthly` are unchanged.
- **`stats low-flow`: empirical frequency in the non-exceedance convention.** The `empirical` block was the result of `LowFlowAnalysis.empirical_frequency()`: values in descending order with the *exceedance* probability, so the deepest low flow of the sample got the exceedance return period (3 years from `tests/fixtures/daily_flows_3y.csv`: minimum 1.66 → P = 0.75, **T = 1.33**), while the `fisher_tippett` block (and WMO No. 1029; Tallaksen and van Lanen, 2004) computes T from the non-exceedance probability. Now `empirical` is `LowFlowEmpiricalFrequency` (`LowFlowAnalysis.empirical_non_exceedance()`): `values_ascending` (ascending), `non_exceedance_probabilities` F = m/(n+1) and `return_periods` T = 1/F; the same minimum 1.66 has F = 0.25 and **T = 4** (the deepest low flow of n years has T = n + 1), so empirical points can be compared with `fisher_tippett.return_periods` without conversion. `LowFlowAnalysis.empirical_frequency()` is unchanged (exceedance convention, described in the docstring), and `plot_non_exceedance_curve()` accepts both forms.
- **`RatingCurve.fit()` and `hydrometrics rating-curve`: H₀ starting point from the data.** The fixed default `h0_initial = 0.0` had to lie below the lowest water level, so every gauge with a reading ≤ 0 (levels below the gauge zero, e.g. −10 cm, are normal) ended with `validation_error` (exit code 2): `hydrolog hydrometrics rating-curve --water-levels=-10,5,20,40,80,120 --discharges 0.5,1.2,2.5,4.8,10.1,17.3` → "h0_initial must be a finite number below the lowest water level (-10), got 0.0". Now the default `h0_initial=None` picks the start `min(H) − max(1, 0.1·(max(H) − min(H)))` (in the unit of the levels), so the fit works for any levels: a = 0.004917, b = 1.640, H₀ = −25.17 (R² = 0.9998), the same as for any explicit start below the lowest level. An explicitly given value is validated as before (finite and lower than the lowest level). On 60 synthetic curves (levels in cm and m, positive and negative, noise 1–8 %) starts from 0.1 to 1 range below the lowest level always gave the best least-squares solution.

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
