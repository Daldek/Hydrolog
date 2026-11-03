# Design: Hydrolog 1.0.0 — command catalog, MCP, result serialization, HSG

**Date:** 2026-10-19
**Version:** 1.0.0 (planned)
**Status:** Approved (owner decisions 2026-10-19)
**Context:** IMGWTools 3.0.0 (ADR-002, ADR-004), Kartograf 0.8.0 (ADR-044, ADR-046), Retman 0.1 (ARCHITECTURE.md)

---

## 1. Goals and owner decisions

1. Hydrolog joins the ecosystem pattern: **one command catalog** is the single source of truth
   for the Python operation layer, the CLI, the MCP server and the generated agent guides.
2. Every result type is **JSON-serializable** (`to_dict()`), so adapters (Retman handlers,
   MCP, CLI `--json`) never hand-serialize NumPy arrays.
3. **HSG computation moves from Kartograf to Hydrolog** (owner: computation needed for
   hydrology must live in Hydrolog). Kartograf keeps only data download (`download_soil`).
4. `WatershedParameters` JSON (`to_dict()` / `from_dict()`) is the proposed file format for
   Retman's `catchment_characteristics` kind.
5. Empirical peak-flow formulas (Punzet, Bogdanowicz–Stachy) are **in scope later**, not in 1.0.0.
6. 1.0.0 stabilizes the public API; semantic versioning applies from 1.0.0.

Non-goals for 1.0.0: REST API, data download of any kind (still OUT, see SCOPE.md),
visualization through the catalog (figures stay Python-only), changes in other repositories.

## 2. Compatibility policy

- The existing class/function API (`SCSCN`, `HydrographGenerator`, `NashIUH`, `ClarkIUH`,
  `SnyderUH`, `ConcentrationTime`, hietograms, `WatershedParameters`, statistics,
  hydrometrics, reports, visualization) **stays unchanged**. Hydrograf (pin v0.6.3) and
  Hydraulik (pin v0.7.0) import it. Changes are additive (new methods, new modules).
- `HydrologError`, `InvalidParameterError`, `CalculationError` keep their names and
  inheritance; they gain `code`, `details`, `hint` attributes (section 5).
- **Clean cutover:** the argparse CLI in `hydrolog/cli/commands/` is replaced by the
  catalog-generated CLI. No aliases for old command spellings.
- `kartograf` optional dependency (`spatial`, `all` extras) is removed: Hydrolog no longer
  depends on Kartograf.

## 3. Package layout (new/changed)

```
hydrolog/
├── _serialization.py       # to_jsonable(), JsonResultMixin (section 4)
├── exceptions.py           # + ERROR_CODES registry, codes on exceptions (section 5)
├── soil/                   # NEW: HSG from soil texture (section 8)
│   ├── __init__.py
│   ├── texture.py          # USDA texture triangle, texture→HSG (numpy only)
│   ├── hsg.py              # classify_hsg(), hsg_statistics_array(), HsgStatistics
│   └── raster.py           # GeoTIFF IO, needs extra [raster] (rasterio, pyproj)
├── operations/             # NEW: operation layer, one module per command group (section 6.3)
│   ├── __init__.py         # re-exports one public function per catalog command
│   └── <group>.py          # tc.py, cn.py, ..., meta.py (the `commands` group)
├── catalog/                # NEW: command catalog (section 6)
│   ├── __init__.py         # data_commands, command_schema, validate_command, run_command
│   ├── spec.py             # Command, Option dataclasses
│   ├── envelope.py         # CommandResult -> "hydrolog-result/1", Notice
│   ├── inputs.py           # loading series/stations/watershed from files or inline JSON
│   ├── dispatch.py         # validate/run, path policy
│   └── groups/             # one module per command group, each exports COMMANDS
├── cli/                    # REPLACED: argparse parser generated from the catalog
├── mcp/                    # NEW: MCP server (extra [mcp])
└── agent_guide.py          # NEW: AGENTS.md / llms.txt generator
AGENTS.md, llms.txt         # generated at repo root, drift-tested
```

## 4. Result serialization

- `hydrolog/_serialization.py`:
  - `to_jsonable(obj) -> Any`: recursive; dataclass → dict of fields (in declaration
    order); `numpy.ndarray` → list (NaN/±Inf → `None`); NumPy scalars → Python scalars;
    `Enum` → `.value`; `tuple` → list; `dict` keys → `str`; `Path` → POSIX string;
    `float` NaN/Inf → `None`. Unknown types → `TypeError` (no silent `str()`).
  - `JsonResultMixin` with `to_dict() -> dict[str, Any]` (= `to_jsonable(self)`) and
    `to_json(indent=None) -> str` (`json.dumps(..., ensure_ascii=False, allow_nan=False)`).
- Every public result dataclass in runoff, precipitation, morphometry, network, statistics,
  hydrometrics, soil inherits the mixin. `WatershedParameters.to_dict()/to_json()` keep their
  current output exactly (it is the `catchment_characteristics` file format).
- Fields typed `Any` (e.g. `HydrographGeneratorResult.unit_hydrograph_result`) serialize via
  the same recursion; computed properties (e.g. `peak_discharge_m3s`) are **not** added
  implicitly — the operation layer chooses what it returns.
- No `from_dict` for results (results are outputs). Inputs with `from_dict`:
  `WatershedParameters`, `WatershedGeometry`, `TerrainAnalysis` (existing).

## 5. Errors

`hydrolog/exceptions.py` gets a closed registry, modelled on IMGWTools `ERROR_CODES`:

| code | exit | meaning |
|---|---|---|
| `validation_error` | 2 | invalid option value/type, missing required option, unknown option |
| `not_found` | 3 | input file missing, unknown command |
| `calculation_error` | 4 | computation impossible for valid-looking input (no convergence, too short series) |
| `data_error` | 7 | input file unreadable/malformed (wrong columns, bad CSV/JSON, bad raster) |
| `missing_dependency` | 6 | optional extra not installed (`[raster]`, `[mcp]`, `[visualization]`) |
| `forbidden` | 8 | path outside allowed directories (MCP) |
| `io_error` | 9 | cannot write output |
| `internal_error` | 1 | bug |

- `ErrorSpec(code, title, title_en, exit_code)`; `ERROR_CODES: Mapping[str, ErrorSpec]`.
- `HydrologError(message, *, code=None, details=None, hint=None)`; class attribute
  `default_code`. `InvalidParameterError.default_code = "validation_error"`,
  `CalculationError.default_code = "calculation_error"`. New subclasses:
  `InputDataError` (`data_error`), `MissingDependencyError` (`missing_dependency`),
  `ForbiddenPathError` (`forbidden`), `NotFoundError` (`not_found`), `OutputError` (`io_error`).
  Existing `raise InvalidParameterError("...")` call sites keep working unchanged.
- Error document (CLI stderr line, MCP `isError` content):
  `{"schema": "hydrolog-error/1", "code", "title", "message", "hint", "details", "exit_code", "command"}`.

## 6. Command catalog

### 6.1 Declarations (`catalog/spec.py`)

```python
@dataclass(frozen=True)
class Option:
    name: str                       # snake_case; same in Python, JSON, MCP; CLI --kebab-case
    type: Literal["number", "integer", "string", "boolean", "choice",
                  "number_list", "path", "object"]
    description: str                # Polish
    description_en: str
    required: bool = False
    default: object = None          # only when the underlying API has a documented default
    choices: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    exclusive_minimum: float | None = None
    unit: str | None = None         # "km", "m/m", "mm", "min", "km2", "m3/s", ...
    writes: bool = False            # path option that is written (output)

@dataclass(frozen=True)
class Command:
    name: str                       # "<group> <command>", e.g. "tc kirpich"
    operation_id: str               # MCP tool name, e.g. "tc_kirpich"
    summary: str                    # Polish, ≤ 120 chars
    summary_en: str
    description: str                # Polish, for agents; includes method/literature
    description_en: str
    function: str                   # "hydrolog.operations:<name>"
    options: tuple[Option, ...]
    one_of: tuple[tuple[str, ...], ...] = ()   # exactly one group must be given
    writes: bool = False            # command writes files (only via `writes` options)
    examples: tuple[Mapping[str, object], ...] = ()
```

`writes`/`network` semantics follow IMGWTools: Hydrolog commands never use network
(`network` is not declared; MCP `openWorldHint=false` for all), `writes=True` only for
commands with an output path option.

### 6.2 Dispatch (`catalog/__init__.py`)

- `data_commands() -> tuple[Command, ...]` — ordered by group, then name.
- `get_command(name_or_operation_id) -> Command` (`NotFoundError` otherwise).
- `command_schema(command=None, *, lang="pl") -> dict` — JSON Schema (draft 2020-12) of
  options; root document `{"schema": "hydrolog-commands/1", "version", "commands": [...]}`.
  Each command: `name`, `operation_id`, `summary`, `description`, `input_schema`
  (`additionalProperties: false`, `required`, `oneOf` for `one_of`), `x-hydrolog`:
  `{"writes", "function", "units"}`.
- `validate_command(name, options) -> dict` — validates against the declaration, applies
  defaults, returns normalized options; raises `InvalidParameterError` with
  `details={"option": ..., "reason": ...}`.
- `run_command(name, options, *, allowed_dirs=None) -> CommandResult` — validate, enforce
  path policy (all `path` options absolute or resolved against CWD; when `allowed_dirs` is
  given, every path must be inside one of them → `ForbiddenPathError`), call the operation
  function with keyword arguments, wrap the result.

### 6.3 Operation layer (`hydrolog/operations/`)

One public, documented (NumPy docstring, full type hints, `Literal` for choices) function per
catalog command, keyword-only, taking JSON-friendly inputs (numbers, strings, lists, paths)
and returning a `JsonResultMixin` object (a small result dataclass defined in the module of
its group) or, when the command has notices or writes files, an
`OperationOutput(result, notices, files)` (return protocol: section 6.4 and
`catalog/envelope.py`). The functions live in one module per command group
(`operations/tc.py` implements `catalog/groups/tc.py`) and are re-exported by
`operations/__init__.py`, so `Command.function` = `"hydrolog.operations:<name>"` resolves to
the package. This is the surface for Retman handlers and `retman-scaffold` (signature +
docstring parsing). Operations compose the existing classes; they contain no new hydrology.

### 6.4 Envelope (`catalog/envelope.py`)

```json
{
  "schema": "hydrolog-result/1",
  "command": "tc kirpich",
  "hydrolog_version": "1.0.0",
  "status": "ok",
  "inputs": { "...normalized options..." },
  "result": { "...to_dict() of the operation result..." },
  "files": [ {"role": "output", "path": "/abs/out.tif", "sha256": "..."} ],
  "notices": [ {"level": "warning", "code": "...", "text": "..."} ]
}
```

`status` is `ok` (exit 0) or the command fails with an error document (no partial state:
computations are atomic). Notices carry non-fatal warnings (e.g. short series, NaN removed).

### 6.5 Inputs from files (`catalog/inputs.py`)

Long data must not be pasted by agents. Series options come in pairs resolved by `one_of`:
inline list (`values`, `dates`) **or** a file (`input_file` + `value_column`/`date_column`).
Supported files: CSV (comma or semicolon, UTF-8, header row; the format of IMGWTools
`export_series` CSV must load without preprocessing) and JSON. Watershed inputs:
`watershed_file` (WatershedParameters JSON) or inline `watershed` object. Stations:
CSV/JSON with `name,x,y,precipitation_mm`. Hydrolog does **not** import IMGWTools.

### 6.6 Command set for 1.0.0

| group | commands |
|---|---|
| `tc` | `kirpich`, `nrcs`, `giandotti`, `faa`, `kerby`, `kerby-kirpich`, `watershed` (method on a watershed file) |
| `cn` | `lookup`, `list`, `range`, `weighted` |
| `scs` | `effective` (total depth or hyetograph series, AMC, Ia) |
| `precip` | `hietogram` (block/triangular/beta/euler_ii), `areal` (arithmetic/thiessen/idw/isohyet) |
| `uh` | `scs`, `nash`, `clark`, `snyder` |
| `hydrograph` | `generate` (watershed or area+cn+tc; hietogram params or precipitation series; UH model) |
| `morphometry` | `watershed` (geometric + terrain indicators from WatershedParameters) |
| `network` | `stats` (segments file/inline, Strahler/Shreve) |
| `stats` | `characteristic`, `daily`, `monthly`, `flood-frequency`, `low-flow`, `low-flow-sequences`, `mann-kendall` |
| `hydrometrics` | `rating-curve`, `water-level-zones` |
| `soil` | `texture`, `hsg` (rasters → HSG GeoTIFF, writes), `hsg-stats` |
| `report` | `generate` (Markdown report, writes) |
| `commands` | `list`, `schema`, `guide` (guide writes when `path` given) |

## 7. Interfaces generated from the catalog

### 7.1 CLI (`hydrolog/cli/`)

- argparse (no new core dependency), generated from `data_commands()`:
  `hydrolog <group> <command> --option-name VALUE ...`; `number_list` accepts
  comma-separated values; `object` accepts JSON text.
- Global flags: `--json` (print envelope), `--schema` (print the command schema, no run),
  `--lang pl|en` (help and messages; env `HYDROLOG_LANG`, default `pl`), `-V/--version`.
- Default output: human-readable Polish summary; `--json`: envelope on stdout.
  Errors: one `hydrolog-error/1` JSON line on stderr when `--json`, readable text
  otherwise; exit code from `ERROR_CODES`.
- `hydrolog mcp` subcommand starts the MCP server (section 7.2); not a catalog command.

### 7.2 MCP server (`hydrolog/mcp/`, extra `hydrolog[mcp]` = `mcp>=2.3,<3`)

- Low-level SDK v2 `Server`, stdio transport; entry: `hydrolog mcp [--allow-dir DIR]...
  [--lang pl|en]`. Without `--allow-dir` commands with `path` options are refused
  (`forbidden`), pure-input commands work.
- One tool per catalog command: name = `operation_id`, title = `hydrolog <name>`,
  description from catalog (plus a sentence naming the `one_of` alternatives and, for
  a writing command, its output options), `inputSchema` = command `input_schema`
  without `$schema` (2020-12 is the MCP default) and without the top-level `oneOf` of
  the `one_of` groups: model APIs (Anthropic API, Claude Code) reject a tool whose
  input schema has `oneOf`/`anyOf`/`allOf` at the top level and fail the whole
  session. The alternatives are named in the description and still enforced by
  `validate_command` (`details.reason = "one_of"`). An option `lang` (choice `pl`/`en`)
  defaults to the server language. Annotations: `readOnlyHint = not writes`,
  `destructiveHint = writes` (a writing command replaces its output file),
  `idempotentHint = true`, `openWorldHint = false`.
- Success: `structuredContent` = envelope, plus the same JSON as text content.
  Failure: `isError=true` with the `hydrolog-error/1` document.
- Server `instructions`: short rules generated from the agent guide principles.
- Missing `mcp` package → `MissingDependencyError` with install hint
  (`pip install hydrolog[mcp]`).

### 7.3 Agent guides (`hydrolog/agent_guide.py`)

- `agent_guide(format: Literal["agents","llms"], lang="pl") -> str` from templates in
  `hydrolog/_data/agents/`, blocks filled from the catalog and `ERROR_CODES`
  (commands table, error table, typical flows, principles).
- Repo root `AGENTS.md` (pl) and `llms.txt` (pl, ≤ 150 lines) are generated by
  `hydrolog commands guide --format ... --path ...`; a test asserts byte equality.
- Typical flows documented: design hydrograph from a watershed file; flood frequency from an
  IMGWTools CSV export; HSG from Kartograf SoilGrids rasters → weighted CN.

## 8. HSG (migrated from Kartograf 0.8.0 `kartograf/hydrology/hsg.py`)

- `hydrolog.soil.texture` (numpy only): `TEXTURE_CLASSES` (12 USDA classes, codes 1–12),
  `TEXTURE_TO_HSG` (Kartograf ADR-025 mapping incl. deviations: sandy_loam→B,
  clay_loam/silty_clay_loam→C), `classify_usda_texture(clay, sand, silt) -> str`,
  `classify_usda_texture_array(...) -> uint8`, `texture_to_hsg_array(...)`.
  Rules ported verbatim (amount-vs-total comparisons in float64, first match wins,
  zero total → loam); units arbitrary but consistent (SoilGrids g/kg or %).
- `hydrolog.soil.hsg` (numpy only): `classify_hsg(clay, sand, silt, *, nodata=(None,None,None))
  -> uint8` (0 = nodata for NaN/Inf, nodata tags, all-zero), `HSG_CODES` (A..D → 1..4,
  raster encoding identical to Kartograf: uint8, nodata 0),
  `hsg_statistics_array(hsg, cell_area_m2, *, share=None) -> HsgStatistics`
  (per group count/area_m2/area_ha/percent of valid area; nodata percent of total area).
- `hydrolog.soil.raster` (extra `hydrolog[raster]`: `rasterio>=1.3`, `pyproj>=3.6`):
  `hsg_from_rasters(clay_path, sand_path, silt_path, output_path) -> HsgRasterResult`
  (inputs must share CRS, transform and shape, else `InputDataError`; output uint8
  GeoTIFF, nodata 0, deflate, band description as in Kartograf);
  `hsg_statistics(hsg_path, *, bbox=None, bbox_crs=None) -> HsgStatistics`
  (geodetic row cell areas for geographic CRS, affine area for projected; optional bbox
  share clipping as in Kartograf `_area_shares`).
- Kartograf tests for texture, mapping, nodata, simplex agreement and statistics are ported.
- Integration path for consumers: Kartograf `download_soil(property=clay|sand|silt)` →
  Hydrolog `hsg_from_rasters` → `hsg_statistics` → `cn weighted`.
  Removing HSG from Kartograf and migrating Hydrograf are follow-ups in those repositories.

## 9. Dependencies

```toml
dependencies = ["numpy>=1.24", "scipy>=1.10"]
[project.optional-dependencies]
raster = ["rasterio>=1.3", "pyproj>=3.6"]
mcp = ["mcp>=2.3,<3"]
visualization = ["matplotlib>=3.7", "seaborn>=0.12"]
all = [raster + mcp + visualization]
dev = [...]
```

## 10. Testing

- Serialization: every result type round-trips through `json.dumps(obj.to_dict())`.
- Catalog: every command has ≥1 example; a parametrized test runs each example through
  `run_command` and the CLI (`--json`) and compares envelopes (parity), and validates
  inputs against `command_schema` output.
- MCP: in-process client/server test listing tools and calling 2–3 tools, incl. error path.
- HSG: ported Kartograf cases; raster tests skipped when `rasterio` missing.
- Agent guide drift test.
