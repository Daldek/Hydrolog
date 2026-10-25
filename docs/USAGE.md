# Hydrolog usage guide

Task-oriented guide to Hydrolog for the command line, Python and MCP clients. Options, units,
ranges and allowed values are not repeated here: they come from the command catalog, the single
source of truth of every interface (see [Finding options](#finding-options)). Installation and
MCP client configuration are in the [README](../README.md); scope is in [SCOPE.md](SCOPE.md);
which time-of-concentration method fits which unit hydrograph model is in
[COMPUTATION_PATHS.md](COMPUTATION_PATHS.md).

## Finding options

```bash
hydrolog commands list --lang en
hydrolog commands schema --command "tc kirpich"
hydrolog tc kirpich --help --lang en
```

- `hydrolog commands list` lists every command with its summary; with `--json` each entry also
  has the `operation_id` (the MCP tool name).
- `hydrolog commands schema --command "<name>"` returns the `hydrolog-commands/1` document of
  one command (the name or the `operation_id`): options with type, unit, bounds and examples,
  the result schema, the effects (does it write a file?), rules and the errors it can raise. The
  JSON Schemas of the results ship in the package (`src/hydrolog/schemas/`).
- `hydrolog <group> <command> --help` prints the same as readable text. Help and summaries are in
  Polish by default; add `--lang en` or set `HYDROLOG_LANG=en` ([Settings](#6-settings)).

## 1. CLI conventions

```text
hydrolog <group> <command> --option value [--json] [--schema] [--lang pl|en] [-v | -q]
```

- **Option names** are the catalog names in kebab-case with the unit in the name: `--length-km`,
  `--slope-m-per-m`, `--total-mm`, `--tc-min`, `--area-km2`. A slope is in m/m, never in percent.
- **Lists** are comma-separated without spaces (`--return-periods 10,50,100`); **objects** are
  JSON text in single quotes (`--parts '[{"cn":55,"area":27.2}]'`). For more than a few numbers
  give a file instead: `--input-file`, `--watershed-file`, `--segments-file`.
- **Booleans** are `--flag` and `--no-flag` (`--remove-outliers`, `--no-remove-outliers`).
- **Negative numbers**: `--option -5` and `--option=-5` are equivalent; write
  `--water-levels=-10,5,20` for a list that starts with a minus sign.
- **`--json`** prints the result envelope (`hydrolog-result/1`) as the only document on stdout,
  on one line; without it you get a short summary. **`--schema`** prints the command description
  (`hydrolog-commands/1`) instead of running it.
- **`--lang pl|en`** selects the language of help and summaries only; JSON is always English.
  **`-v`** shows debug messages and **`-q`** only errors, both on stderr.

```bash
hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023 --json
```

```json output
{"schema": "hydrolog-result/1", "tool": "hydrolog", "command": "tc kirpich", "check": false, "status": "ok", "result": {"schema": "hydrolog-tc-kirpich/1", "method": "kirpich", "tc_min": 85.97330594494066, "tc_h": 1.4328884324156776}, "notices": [], "inputs": {"length_km": 8.2, "slope_m_per_m": 0.023}}
```

The envelope keys are `schema`, `tool`, `version`, `command`, `check`, `status`, `result`,
`notices`, `inputs` and, for paged lists, `page`. The domain result has its own `schema`
(`hydrolog-<group>-<command>/1`); units follow from field names (`tc_min`, `area_ha`); `NaN` and
infinities are `null`. `inputs` echoes the options after normalisation (defaults filled in, paths
made absolute). `notices` carries non-fatal warnings (a short series, a value outside the range of
a formula): read it next to the result.

**Errors.** A failing command prints nothing to stdout and leaves nothing half done. The last line
of stderr is the `hydrolog-error/1` document (English): `code`, `title`, `message`, `hint`,
`details`, `exit_code`, `command`. Decide by `code`, `details.option` and `details.reason`, not by
the message text.

| Exit | `code` | Typical cause |
|---|---|---|
| 1 | `internal_error` | a bug: report the command, the options and the version |
| 2 | `validation_error` | a wrong or missing option (`details.option`) |
| 3 | `not_found` | unknown command (`details.suggestions`) or missing input file |
| 4 | `conflict` | the output file exists ([Writing files](#3-writing-files)) |
| 6 | `missing_dependency` | an optional extra is not installed (`hint` names it) |
| 7 | `data_error` | a malformed input file (`details.path`, `details.reason`) |
| 9 | `io_error` | the output cannot be written |
| 12 | `forbidden` | a path outside the directories an MCP server allows |
| 13 | `calculation_error` | valid input, no result (for example a fit that does not converge) |
| 130, 143 | `cancelled`, `terminated` | Ctrl+C or SIGTERM; nothing is left half written |

```console
$ hydrolog tc kirpich --length-km -1 --slope-m-per-m 0.023 --json
{"schema": "hydrolog-error/1", "code": "validation_error", "title": "Invalid input", "message": "Option 'length_km': must be > 0, got -1", "details": {"option": "length_km", "reason": "exclusive_minimum", "exclusive_minimum": 0, "value": -1.0}, "exit_code": 2, "command": "tc kirpich"}
```

The same code is the CLI exit status, `HydrologError.code` in Python and the error `code` over MCP.

## 2. Tasks

Each task shows the CLI call, then the Python equivalent. In Python,
`hydrolog.run_command("<command>", **options)` takes the catalog option names as keyword
arguments (`slope_m_per_m=0.023`) and returns the envelope: `envelope.result` is the domain
result and `envelope.to_dict()` the JSON-compatible form. The same calculation is a plain function
in `hydrolog.operations` (`tc_kirpich`) returning an object with the `result`. The examples read
the sample files of `tests/fixtures/` of the repository (watershed JSON, CSV series, GeoTIFF
rasters).

### Time of concentration

Kirpich needs the main channel length and slope; NRCS (TR-55 lag) also needs the CN. Both return
`tc_min` and `tc_h`. Other methods: `tc giandotti`, `tc faa`, `tc kerby`, `tc kerby-kirpich`.
`tc watershed` computes any of them from a watershed JSON file (the `WatershedParameters` format,
see [Exchange](#7-exchange-with-kartograf-imgwtools-and-hydrograf)); a field the method needs but
the file lacks is a `validation_error` that lists it.

```bash
hydrolog tc nrcs --length-km 8.2 --slope-m-per-m 0.023 --cn 72 --json
```

```bash
hydrolog tc watershed --watershed-file tests/fixtures/watershed_example.json --method kirpich --json
```

```json output
{"result": {"method": "kirpich", "tc_min": 135.89384108269536, "parameters": {"length_km": 14.2, "slope_m_per_m": 0.021}, "watershed_name": "Zlewnia Przykładowa"}}
```

```python
import hydrolog

envelope = hydrolog.run_command("tc kirpich", length_km=8.2, slope_m_per_m=0.023)
print(f"tc = {envelope.result.tc_min:.1f} min")

envelope = hydrolog.run_command(
    "tc watershed", watershed_file="tests/fixtures/watershed_example.json", method="kirpich"
)
print(f"{envelope.result.watershed_name}: tc = {envelope.result.tc_min:.1f} min")
```

### Curve number: lookup and weighting

`cn lookup` reads the TR-55 table for a hydrologic soil group (A-D) and a land cover (`cn list`
and `cn range` show the table). `condition` (poor, fair, good) matters only for the covers that
depend on it; the result reports `condition_applied`. `cn weighted` gives one area-weighted CN for
a watershed of several parts: `--parts`, or parallel lists `--cn-values` with `--areas` or
`--fractions`. The result is fractional and `scs effective`, `tc nrcs` and `hydrograph generate`
accept it.

```bash
hydrolog cn lookup --hsg B --land-cover forest --condition good --json
```

```json output
{"result": {"schema": "hydrolog-cn-lookup/1", "cn": 55, "hsg": "B", "land_cover": "forest", "condition": "good", "condition_applied": "good"}}
```

```bash
hydrolog cn weighted --cn-values 55,79,98 --fractions 0.6,0.3,0.1 --json
```

```json output
{"result": {"schema": "hydrolog-cn-weighted/1", "cn": 66.50000000000001, "n_parts": 3, "shares": [0.6, 0.3, 0.1]}}
```

```python
import hydrolog

cn = hydrolog.run_command("cn lookup", hsg="B", land_cover="forest", condition="good").result.cn
parts = [{"cn": 55, "area": 27.2}, {"cn": 69, "area": 13.6}]
print(cn, round(hydrolog.run_command("cn weighted", parts=parts).result.cn, 1))
```

### Effective precipitation and design hyetograph

`scs effective` turns a total (`--precipitation-mm`) or a hyetograph (`--values`, or a file with
`--input-file` and `--value-column`) into effective precipitation by the SCS-CN method; `--amc`
selects the antecedent moisture condition (I, II, III; default II) and `--ia-coefficient` the
initial abstraction ratio (default 0.2).

`precip hietogram` builds a design rainfall of a total, duration and step; types are `block`,
`triangular`, `beta` and `euler_ii`. Parameters of another type are rejected (`--alpha` and
`--beta` belong to `beta`, `--peak-position` to `triangular` and `euler_ii`). A duration that is
not a multiple of the step adds a notice about the uncovered tail. Depths and intensities are
`result.depths_mm` and `result.intensities_mm_per_h`. `precip areal` computes areal precipitation
from gauges (arithmetic mean, Thiessen, IDW, isohyets).

```bash
hydrolog scs effective --cn 72 --precipitation-mm 50 --amc III --json
```

```bash
hydrolog precip hietogram --hietogram-type beta --total-mm 50 --duration-min 30 --timestep-min 10 --json
```

```json output
{"result": {"schema": "hydrolog-precip-hietogram/1", "hietogram_type": "beta", "n_steps": 3, "times_min": [10.0, 20.0, 30.0], "parameters": {"alpha": 2.0, "beta": 5.0}}}
```

### Unit hydrograph and runoff hydrograph

`uh scs`, `uh nash`, `uh clark` and `uh snyder` return the ordinates (`ordinates_m3s_per_mm` at
`times_min`) with `time_to_peak_min` and `peak_discharge_m3s_per_mm`. Nash takes `--n` and
`--k-min`, the Lutz method (`--lutz-...`) or the urban regression (`--urban-...`); Clark takes
`--r-min` or `--r-tc-ratio`.

```bash
hydrolog uh scs --area-km2 45.3 --tc-min 90 --timestep-min 5 --json
```

```json output
{"result": {"schema": "hydrolog-uh-scs/1", "model": "scs", "time_to_peak_min": 56.5, "peak_discharge_m3s_per_mm": 10.006088495575222}}
```

`hydrograph generate` chains design rainfall, SCS-CN, a unit hydrograph and convolution. The
watershed comes from `--watershed-file`, `--watershed` (JSON) or `--area-km2` with `--cn`. Without
`--tc-min` the time of concentration is computed by `--tc-method` (default `kirpich`);
`--uh-model` selects `scs` (default), `nash`, `clark` or `snyder` with their own parameters
(`--nash-n`, `--nash-k-min`, `--clark-r-tc-ratio`, `--snyder-length-km`...). Measured rainfall
(`--values`, `--input-file`) replaces the design rainfall.

```bash
hydrolog hydrograph generate --watershed-file tests/fixtures/watershed_example.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60 --json
```

```json output
{"result": {"schema": "hydrolog-hydrograph-generate/1", "peak_discharge_m3s": 47.02725674740998, "time_to_peak_min": 110.0, "total_volume_m3": 321254.9494884561, "runoff_coefficient": 0.1417936234546637, "cn": 72.0, "tc_method": "kirpich", "uh_model": "scs"}}
```

```python
import hydrolog

result = hydrolog.run_command(
    "hydrograph generate",
    watershed_file="tests/fixtures/watershed_example.json",
    tc_method="kirpich",
    hietogram_type="beta",
    total_mm=50,
    duration_min=60,
).result
print(f"Qmax {result.peak_discharge_m3s:.1f} m3/s at {result.time_to_peak_min:.0f} min")
```

### Flood routing

The `route` commands send a discharge hydrograph through one element and return the outflow
hydrograph; they are lumped hydrologic methods, so they give discharge only (water levels and
inundation are hydraulics: Hydraulik, HEC-RAS). `route lag` shifts the hydrograph by `--lag-min`
without attenuating it; a lag that is not a whole number of time steps is interpolated linearly
(notice `lag_interpolated`).

- **The hydrograph** is given inline (`--times-min`, `--discharge-m3s`) or from a CSV or JSON file
  (`--input-file`, with `--time-column` and `--value-column`, by default `time_min` and
  `discharge_m3s`). Times are minutes, discharges m3/s and not negative, and the time step is
  regular: an irregular table is an error (`details.reason` `irregular_step`), nothing is
  resampled.
- **The start** of the outflow is the first inflow ordinate (a steady state) unless
  `--initial-outflow-m3s` is given.
- **The tail**: the outflow outlasts the inflow, so the time axis is extended after the last inflow
  ordinate, where the inflow is held, until the outflow has settled (notice `tail_extended`);
  `--extend-min` sets the extension instead, `0` adds nothing.
- **The result** has the parameters used, the peaks, the volumes, the storage at both ends and
  `balance_error_m3` (inflow volume - outflow volume - change of storage, zero to rounding), and the
  series `times_min` and `outflow_m3s`. With `--output` the series goes to a CSV file with the
  columns `time_min` and `discharge_m3s` instead (`outflow_m3s` is then `null`), which is a valid
  `--input-file` of every `route` command: the outflow of one reach is the inflow of the next, or
  of a hydraulic model. Without `--output` there is no file to plan, so `--check` computes as usual.

```bash
hydrolog route lag --lag-min 30 --input-file tests/fixtures/flood_inflow.csv --output outflow.csv --json
```

```json output
{"result": {"schema": "hydrolog-route-lag/1", "model": "lag", "parameters": {"lag_min": 30.0, "lag_steps": 3.0}, "extension_min": 10.0, "outflow_peak_m3s": 40.0, "outflow_time_to_peak_min": 90.0, "peak_delay_min": 30.0, "outflow_m3s": null, "files": [{"path": "...", "status": "written"}]}}
```

`route muskingum` is the Muskingum method (the University of Iowa example below: `K` = 20 h,
`X` = 0.25, steps of 12 h, so `--k-min 1200` and times in minutes). The reach stores
`K [X I + (1 - X) O]`: `--k-min` is the travel time `K` and `--x` the weight, from 0 (a linear
reservoir, the most attenuation) to 0.5 (none). The reach is divided into `--subreaches` equal
sub-reaches of `K/N`, and more of them attenuate less; without `--subreaches` the number is `K`
over the time step, rounded. The weights of a sub-reach stay non-negative only while
`|2KX| <= step <= 2K(1 - X)`: a `--subreaches` outside that window is an error
(`details.reason` `unstable_timestep`, the window in `details.minimum` and `details.maximum`),
and when no whole number of sub-reaches is inside it the time step is divided into sub-steps
(notice `substeps_added`; `balance_error_m3` is then the sampling error of the trapezoid rule).

```bash
hydrolog route muskingum --k-min 1200 --x 0.25 --subreaches 1 --extend-min 0 \
  --times-min 720,1440,2160,2880,3600,4320,5040,5760,6480,7200 \
  --discharge-m3s 100,300,680,500,400,310,230,180,100,50 --json
```

```json output
{"result": {"schema": "hydrolog-route-muskingum/1", "model": "muskingum", "parameters": {"k_min": 1200.0, "x": 0.25, "subreaches": 1, "substeps": 1, "c_current": 0.047619047619047616, "c_previous": 0.5238095238095238, "c_outflow": 0.42857142857142855}, "outflow_peak_m3s": 487.24142718311816, "outflow_time_to_peak_min": 3600.0, "peak_delay_min": 1440.0, "outflow_m3s": [100.0, 109.52380952380952, 236.46258503401359, 481.3411078717201, 487.24142718311816, 433.10346879276494, 358.9491056730898, 282.8829500503718, 220.28316906920696, 149.16897722013633]}}
```

The published outflow of the example is 100.0, 109.5, 236.5, 481.3, 487.2, 433.1, 358.9, 282.9,
220.3 and 149.2 cfs: the largest difference from the printed table is 0.049 cfs, inside its
rounding (see COMPUTATION_PATHS 3.9.3).

`route muskingum-cunge` takes the Muskingum parameters from the reach itself (the NRCS form of
NEH-630 chapter 17): `K = dx / c` and `X = (1 - Q / (T S0 c dx)) / 2` for a distance step `dx`,
with the flood-wave celerity `c`, the top width `T`, the slope `S0` (`--slope-m-per-m`) and a
reference discharge `Q` (the inflow peak, or `--reference-discharge-m3s`); `X` may be negative.
`--length-km` is divided into equal steps, each a Muskingum sub-reach. Give the hydraulics as one
of two groups: a channel section (`--manning-n` with `--bottom-width-m` and `--side-slope-m-per-m`,
0 for a rectangle), from which Manning's equation gives `c` and `T` at `Q`, or the wave itself
(`--celerity-m-per-s` with `--top-width-m`, for example from a hydraulic model); both groups or
neither is an error (`details.reason` `one_of`). The steps are those of NRCS,
`dx_c = (c dt + Q / (T S0 c)) / 2`, changed so that every weight stays non-negative (notice
`subreaches_adjusted`; `substeps_added` when the time step has to be divided); a reach so short and
flat that it acts as storage is refused (`unstable_timestep`; use a reservoir method). A
hydrograph that rises from 5 % of its peak to the peak in fewer than 10 steps is interpolated to a
shorter step (`timestep_refined`). Every step inside the non-negative window meets the accuracy
limit of NEH-630, so `accuracy_limit` only reports that the NRCS step was beyond it and was
replaced.

The example is NEH-630 example 17-4 in SI: `L` = 2,600 ft, `S0` = 0.00091, and `c` = 4.297 ft/s and
`T` = 44.6 ft as printed in the text; the inflow is the 37 ordinates of Table 17-18 in m3/s
(`tests/fixtures/neh17_4_inflow.csv`, one ordinate per 6 minutes).

```bash
hydrolog route muskingum-cunge --length-km 0.79248 --slope-m-per-m 0.00091 \
  --celerity-m-per-s 1.3097256 --top-width-m 13.59408 \
  --input-file tests/fixtures/neh17_4_inflow.csv --extend-min 0 --json
```

```json output
{"result": {"schema": "hydrolog-route-muskingum-cunge/1", "model": "muskingum-cunge", "parameters": {"k_min": 10.084555115972385, "x": -0.25444124673728363, "subreaches": 1, "substeps": 1, "c_current": 0.3556393224656159, "c_previous": 0.027735454184956914, "c_outflow": 0.6166252233494272}, "outflow_peak_m3s": 18.286546121803077, "outflow_time_to_peak_min": 786.0, "peak_delay_min": 12.0, "outflow_m3s": [0.0, 0.007452066362944516, 0.01655604783271178, 0.02751124432336292, "..."]}}
```

The reach has one step (`K` = 605 s, `X` = -0.254, the weights 0.0277, 0.3556 and 0.6166 against
the printed 0.028, 0.355 and 0.617). The outflow peaks at 645.78 ft3/s (18.2865 m3/s) at 13.1 h, the
published 645.72 ft3/s, and the largest difference from Table 17-18 is 0.24 ft3/s, 0.04 % of the
peak; the three-decimal coefficients printed in the text give the table to 0.0049 ft3/s, so the
difference is their rounding (see COMPUTATION_PATHS 3.9.4). The notice `tail_truncated` is correct
here: the published table ends in the recession and `--extend-min 0` keeps its axis.

`route cascade` sends the hydrograph through `--n` equal linear reservoirs in series, each with the
storage `S = K O` (the Nash model of `uh nash`; with `n` equal to the reach length over
`Q / (T S0 c)` it is the Kalinin-Milyukov method). `--n` need not be whole: 1 is one reservoir (the
most attenuation) and a large `n` only delays the wave by `n K`. Give the time scale as one of two
groups: the storage constant of one reservoir (`--k-min`), or the length and the celerity of the
reach (`--length-km` with `--celerity-m-per-s`), whose travel time `L / c` is the delay `n K`; both
groups or neither is an error (`details.reason` `one_of`). The outflow is the exact response of the
cascade to the inflow taken as straight lines between the ordinates, so there is no window of
stable steps as in Muskingum: nothing is divided or refused, and a time step longer than `K` is
routed as it is. Between the ordinates the outflow is a curve, so `balance_error_m3` is only the
quadrature error of the trapezoid rule (9.7 m3 of 712,500 m3 here). The example is 18 km at 1.5
m/s, a travel time of 200 min shared by 2.5 reservoirs of 80 min, with a time step of 60 min.

```bash
hydrolog route cascade --n 2.5 --length-km 18 --celerity-m-per-s 1.5 \
  --times-min 0,60,120,180,240,300,360 --discharge-m3s 5,20,60,35,15,8,5 --json
```

```json output
{"result": {"schema": "hydrolog-route-cascade/1", "model": "cascade", "parameters": {"n": 2.5, "k_min": 80.0, "lag_min": 200.0, "timestep_over_k": 0.75, "length_km": 18.0, "celerity_m_per_s": 1.5}, "extension_min": 660.0, "outflow_peak_m3s": 26.544046088994683, "outflow_time_to_peak_min": 300.0, "peak_delay_min": 180.0, "outflow_m3s": [5.0, 5.419435772176586, 8.94959612609301, 18.041114804691578, 25.403667771343876, 26.544046088994683, "..."]}}
```

`route level-pool` sends the hydrograph through a reservoir, a pond or a reach that is given by a
storage-outflow table, by storage indication (the modified Puls method of NEH-630 chapter 17):
each row of the table is a state of the pool, the storage `S` [m3] it holds while it releases the
outflow `O` [m3/s], both not decreasing from the empty state. Give the table inline
(`--storage-m3` with `--outflow-m3s`, and `--stage-m` for the water level of each row) or as a CSV
or JSON `--rating-file` with the columns `storage_m3`, `outflow_m3s` and, if the table has one,
`stage_m` (the file brings its own stage, so `--stage-m` next to it is an error); neither source or
both is an error (`details.reason` `one_of`), and so is a table that decreases or repeats a row (a
file names the row and the column). The table has to cover the flood: one that fills the reservoir
beyond the last row (`table_exceeded`) or empties it below the first (`table_emptied`) is a
`calculation_error`, never an extrapolation. The pool starts at rest with the first inflow
ordinate, or with `--initial-outflow-m3s`, which must lie inside the table. The time step must not
exceed twice the shortest `K = dS/dO` of the table between the lowest and the highest flow of the
run, divided by `--subreaches`; a longer step is divided (notice `timestep_refined`) and one that
would need more than 100 parts is refused (`unstable_timestep`). `--subreaches N` routes through
`N` pools in series, each holding `S / N`, for a channel reach whose travel time is about `N`
steps; the default 1 is a pond. The result gives the peak storage and its time and, with a stage,
the peak stage.

The example is NEH-630 example 17-1 in SI: the channel reach of Table 17-4
(`tests/fixtures/neh17_1_rating.csv`) with the 19 ordinates at 30 min of the inflow of Table 17-7
(`tests/fixtures/neh17_1_inflow.csv`).

```bash
hydrolog route level-pool --rating-file tests/fixtures/neh17_1_rating.csv \
  --input-file tests/fixtures/neh17_1_inflow.csv --extend-min 0 --json
```

```json output
{"result": {"schema": "hydrolog-route-level-pool/1", "model": "level-pool", "parameters": {"subreaches": 1, "substeps": 1, "timestep_limit_min": 78.11998862867867, "storage_peak_m3": 364057.24683300115, "storage_peak_time_min": 180.0}, "outflow_peak_m3s": 108.34456539046381, "outflow_time_to_peak_min": 180.0, "peak_delay_min": 60.0, "outflow_m3s": [0.0, 8.224364051456476, 28.76328459115899, 53.43626436816038, 81.58471391462896, 102.50593786102928, "..."]}}
```

The outflow peaks at 3,826 ft3/s (108.34 m3/s) at 3 h, the published 3,827 ft3/s, and the largest
difference from Table 17-7 is 0.85 ft3/s, 0.02 % of the peak; the table prints each average inflow
rounded up from .5, and with the ordinates that give the printed averages all 19 values agree to
0.49 ft3/s (see COMPUTATION_PATHS 3.9.6). The limit of the step is 78.12 min, so the published
step of 30 min is not divided. The notice `tail_truncated` is correct here: the published table
ends in the recession and `--extend-min 0` keeps its axis.

`route network` routes the hydrographs of many subcatchments down a river network. The network is a
JSON document `hydrolog-network/1`, inline (`--network`, JSON text) or in a file
(`--network-file`): `nodes` of five types linked by `from`, the ids of the nodes that flow into a
node. A `subcatchment` brings a hydrograph, inline (`times_min` with `discharge_m3s`) or as a column
of `--inflows-file` (a time column, `--time-column`, by default `time_min`, and a column per
subcatchment named by its `value_column` or else by its `id`). A `reach` has a `method` (`lag`,
`muskingum`, `muskingum-cunge`, `cascade` or `level-pool`) and the options of `route <method>` that
describe the element (`lag_min`; `k_min`, `x`, `subreaches`; `length_km` and `slope_m_per_m` with a
section or a celerity; `n` with `k_min`; a table), next to `initial_outflow_m3s` and `extend_min`; a
`reservoir` has the options of `route level-pool`, a table inline or a `rating_file` that lies beside
the network file (a path that leads out of its directory is `path_outside`, and an inline network
cannot name files); a `junction` adds the hydrographs that flow into it; the `outlet` is the end.
There is one outlet, every node leads to it and a node flows into one node: a bifurcation is
refused. The order of the nodes in the document changes nothing. A document that is wrong is a
`data_error` (a file) or a `validation_error` (inline) with the node and the field in `details`.
All sources have one time step and one first time; nothing is resampled.

`--output-dir DIR` (`-o`) writes the hydrograph that leaves each node as `<id>.csv`, a table that
every `route` command reads again and the hand-off to Hydraulik; `--nodes` selects the nodes
(default all). Without a directory the hydrographs of the selected nodes are in the result. The files
follow the rules of section 3 and are never written over an input file. The example is the fixture
network: two subcatchments (`A` by its id, `B` by its `value_column`), a Muskingum-Cunge reach below
`A`, a junction, a pond with a rating file and the outlet; the series of the outlet only:

```bash
hydrolog route network --network-file tests/fixtures/network_flood.json \
  --inflows-file tests/fixtures/network_inflows.csv --nodes OUT --json
```

```json output
{"result": {"schema": "hydrolog-route-network/1", "name": "Pond catchment", "timestep_min": 10.0, "outlet": "OUT", "order": ["A", "B", "R1", "J1", "D", "OUT"], "nodes": [{"id": "A", "type": "subcatchment", "from": [], "peak_m3s": 24.0, "time_to_peak_min": 60.0, "volume_m3": 143706.0}, {"id": "B", "type": "subcatchment", "from": [], "peak_m3s": 6.8, "time_to_peak_min": 40.0, "volume_m3": 53169.0}, {"id": "R1", "type": "reach", "from": ["A"], "peak_m3s": 22.23188918773083, "time_to_peak_min": 120.0, "model": "muskingum-cunge", "peak_attenuation_pct": 7.36712838445488, "peak_delay_min": 60.0}, {"id": "J1", "type": "junction", "from": ["R1", "B"], "peak_m3s": 25.47188918773083, "time_to_peak_min": 120.0}, {"id": "D", "type": "reservoir", "from": ["J1"], "peak_m3s": 13.863880195745784, "time_to_peak_min": 170.0, "model": "level-pool", "peak_attenuation_pct": 45.57184159538639, "peak_delay_min": 50.0}, {"id": "OUT", "type": "outlet", "from": ["D"], "peak_m3s": 13.863880195745784, "time_to_peak_min": 170.0, "times_min": [0.0, 10.0, 20.0, "..."], "discharge_m3s": [2.0, 2.101548946146755, 2.3546878578993646, "..."]}]}}
```

The outlet peaks at 13.86 m3/s at 170 min: the Muskingum-Cunge reach lowers the peak of `A` by 7.4 %
and delays it by an hour, the junction adds `B`, and the pond lowers it by a further 45.6 % and
delays it by 50 min.

In Python the classes of `hydrolog.routing` do the same on arrays; `route` returns the outflow
with the notices, the storage at both ends and the balance.

```python
from hydrolog.routing import Hydrograph, LagReach

inflow = Hydrograph.from_step([0, 10, 40, 20, 0], timestep_min=30)
result = LagReach(lag_min=60).route(inflow)
print(result.outflow.time_to_peak_min, result.balance_error_m3)
```

### Morphometry and river network

`morphometry watershed` returns geometry, shape indicators, elevation and slope figures from a
watershed JSON. `network stats` computes Strahler or Shreve order statistics from segments; a CSV
file has the columns `segment_id`, `upstream_ids` (separated by `;`) and `length_km`.

```bash
hydrolog morphometry watershed --watershed-file tests/fixtures/watershed_example.json --json
```

```bash
hydrolog network stats --segments-file tests/fixtures/network_segments.csv --method strahler --area-km2 4.5 --json
```

```json output
{"result": {"schema": "hydrolog-network-stats/1", "method": "strahler", "n_segments": 9, "statistics": {"max_order": 3, "total_stream_length_km": 12.7}}}
```

### Flow statistics from a CSV file

The `stats` commands read a daily series from CSV: `--input-file`, the discharge column
(`--value-column`) and, where the date matters, `--date-column`. A column is named without its
unit, so `Q` finds `Q [m3/s]`. The CSV that IMGWTools writes loads without preprocessing
([Exchange](#7-exchange-with-kartograf-imgwtools-and-hydrograf)). Hydrological years run from
November to October. A series shorter than the method needs adds a notice (reliable flood
quantiles need at least 30 years).

- `stats flood-frequency`: flood quantiles for return periods from annual maxima
  (`--distribution all` compares several distributions); `stats low-flow`: low-flow quantiles from
  annual minima; `stats low-flow-sequences`: drought sequences below a threshold.
- `stats characteristic`: second-degree characteristic values (WWQ ... NNQ); `stats daily` and
  `stats monthly`: day-of-year and monthly statistics.
- `stats mann-kendall`: monotonic trend test.

```bash
hydrolog stats flood-frequency --input-file tests/fixtures/annual_maxima.csv --value-column Qmax --distribution gev --return-periods 10,100 --json
```

```json output
{"result": {"schema": "hydrolog-stats-flood-frequency/1", "n_years": 35, "best_distribution": "gev"}}
```

```bash
hydrolog stats mann-kendall --input-file tests/fixtures/annual_maxima.csv --value-column Qmax --alpha 0.05 --json
```

```python
import hydrolog

envelope = hydrolog.run_command(
    "stats characteristic",
    input_file="tests/fixtures/imgwtools_series_export.csv",
    value_column="Q",
    date_column="date",
    parameter="Q",
)
print(envelope.to_dict()["result"]["wwx"], [n.code for n in envelope.notices])
```

### Rating curve

`hydrometrics rating-curve` fits `Q = a * (H - H0)^b` to stage-discharge pairs from a file with
level and discharge columns or from two parallel lists. `--h0-initial` sets the start value of
`H0`, `--remove-outliers` drops pairs far from the fit. A fit that does not converge is a
`calculation_error` (exit 13). `hydrometrics water-level-zones` delimits the Rybczynski water
level zones from a level series.

```bash
hydrolog hydrometrics rating-curve --input-file tests/fixtures/rating_curve_pairs.csv --level-column H --discharge-column Q --h0-initial 40 --json
```

### Hydrologic soil groups

`soil texture` classifies one sample (clay, sand and silt in one common unit) into a USDA texture
class and a hydrologic soil group. `soil hsg` classifies three rasters (clay, sand, silt; GeoTIFF
with the same coordinate system, grid and size) into one HSG raster, a `uint8` GeoTIFF where 0 is
no data and 1-4 are A-D; `soil hsg-stats` reports the area and share of each group. Both raster
commands need the `raster` extra. `soil hsg` writes a file, so it takes `--output`, `--check` and
`--force` ([Writing files](#3-writing-files)).

```bash
hydrolog soil texture --clay 200 --sand 400 --silt 400 --json
```

```bash
hydrolog soil hsg --clay-path tests/fixtures/hsg_clay.tif --sand-path tests/fixtures/hsg_sand.tif --silt-path tests/fixtures/hsg_silt.tif --output hsg.tif --json
hydrolog soil hsg-stats --hsg-path hsg.tif --json
```

```json output
{"result": {"schema": "hydrolog-soil-hsg-stats/1", "groups": {"A": {"area_ha": 75.0}, "D": {"area_ha": 68.75}}, "nodata": {"count": 1}}}
```

The HSG is not the CN: the CN also needs the land cover. Intersecting the HSG raster with a land
cover layer happens outside Hydrolog; the area of each group from `soil hsg-stats` then feeds
`cn weighted` (`--parts '[{"cn":30,"area":75.0},{"cn":58,"area":75.0}]'`).

```python
import hydrolog

hydrolog.run_command(
    "soil hsg",
    clay_path="tests/fixtures/hsg_clay.tif",
    sand_path="tests/fixtures/hsg_sand.tif",
    silt_path="tests/fixtures/hsg_silt.tif",
    output="hsg.tif",
)
stats = hydrolog.run_command("soil hsg-stats", hsg_path="hsg.tif").result
for group, area in stats.groups.items():
    print(group, area.area_ha, "ha")
```

### Markdown report

`report generate` runs the same computation as `hydrograph generate` (same options) and writes a
Markdown report with formulas, tables and the water balance. The report text is Polish. It writes
exactly one file, so it requires `--output`; `--max-table-rows` shortens long tables.

```bash
hydrolog report generate --output report.md --watershed-file tests/fixtures/watershed_example.json --tc-method kirpich --hietogram-type beta --total-mm 50 --duration-min 60 --json
```

```json output
{"result": {"schema": "hydrolog-report-generate/1", "peak_discharge_m3s": 47.02725674740998, "files": [{"path": "...", "status": "written"}]}}
```

## 3. Writing files

Three commands write a file: `report generate`, `soil hsg` and `commands guide` (the agent guide
rendered from the catalog). The `route` commands write the outflow only when they are given
`--output` (without it `--check` has nothing to plan and computes), and `route network` writes one
file per node into `--output-dir`. Every other command only reads. A writing command takes:

- `--output FILE`: exactly one plain file; missing directories are created. Hydrolog has no store
  and no managed directory layout.
- `--output-dir DIR` (`route network` only, short flag `-o`): one plain file per node, `<id>.csv`;
  the directory is created if it is missing. The plan lists every file; a directory that is, or
  lies in, the store of another Nogat tool is a `conflict` (`details.reason` `output_in_store`: the
  tool that owns a store writes into it with its own `--root`), and so is a node named twice in
  `--nodes` (`duplicate_output_name`). The files are written into
  `DIR/.hydrolog-incoming/<host>_<pid>_<token>/` and moved into place, so an error leaves no
  partial file and the staging directory is removed; a file that appeared during the computation
  is a conflict, not replaced.
- `--check`: plan without effects. The result is a `hydrolog-plan/1` document whose
  `result.targets[]` lists the `option` that names each file, its absolute `path` and the
  `action`: `write` (no such file), `replace` (it exists and `--force` is given) or `conflict` (it
  exists and `--force` is not given). `--check` exits 0 even for a conflict: read the action.
- `--force`: replace an existing file. The replacement is atomic (a reader sees the old or the
  new file; an interrupted run leaves the old one). Nothing is overwritten without `--force`.

After a real run `result.files[]` lists each file as `{path, size_bytes, sha256, status}` with
`status` `written` (new file) or `replaced`. This block plans, runs, and plans again; the last
plan reports the conflict:

```bash
hydrolog report generate --output report.md --area-km2 45.3 --cn 72 --tc-min 90 --hietogram-type beta --total-mm 50 --duration-min 60 --check --json
hydrolog report generate --output report.md --area-km2 45.3 --cn 72 --tc-min 90 --hietogram-type beta --total-mm 50 --duration-min 60 --json
hydrolog report generate --output report.md --area-km2 45.3 --cn 72 --tc-min 90 --hietogram-type beta --total-mm 50 --duration-min 60 --check --json
```

```json output
{"check": true, "result": {"schema": "hydrolog-plan/1", "targets": [{"option": "output", "path": "...", "action": "conflict"}]}}
```

Running without `--check` against an existing file fails with `conflict` and exit 4, and nothing
is touched:

```console
$ hydrolog soil hsg --clay-path clay.tif --sand-path sand.tif --silt-path silt.tif --output hsg.tif --json
{"schema": "hydrolog-error/1", "code": "conflict", "title": "State conflict", "message": "The output file already exists: /work/hsg.tif", "hint": "Give another path or add --force to replace the file.", "details": {"reason": "output_exists", "paths": ["/work/hsg.tif"]}, "exit_code": 4, "command": "soil hsg"}
```

Resolve it by giving another `--output` or by adding `--force`:

```bash
hydrolog report generate --output report.md --area-km2 45.3 --cn 72 --tc-min 90 --hietogram-type beta --total-mm 50 --duration-min 60 --json
hydrolog report generate --output report.md --area-km2 45.3 --cn 72 --tc-min 90 --hietogram-type beta --total-mm 50 --duration-min 60 --force --json
```

```json output
{"result": {"files": [{"path": "...", "status": "replaced"}]}}
```

In Python, `hydrolog.check_command("report generate", output="report.md", ...)` returns the plan,
and a conflict raises `hydrolog.ConflictError` (code `conflict`, `details["paths"]`).

## 4. The Python interface

`import hydrolog` reads no files and imports no numerical library. The public API is the error
classes and five functions that drive any catalog command:

- `run_command(command, **options)` runs a command and returns the envelope;
- `validate_command(command, **options)` checks the options without running and returns them
  normalised, with the defaults filled in;
- `check_command(command, **options)` plans a writing command (the plan of `--check`);
- `list_commands(limit=None, cursor=None)` returns the command list document, optionally paged;
- `command_schema(command)` returns the `hydrolog-commands/1` document of one command.

`command` is a catalog name (`"tc kirpich"`) or an `operation_id` (`"hydrolog_tc_kirpich"`).
Options are keyword arguments with the catalog names; lists are Python lists and objects are
dicts, not JSON text.

```python
import hydrolog

envelope = hydrolog.run_command("scs effective", cn=72, precipitation_mm=50)
print(envelope.command, envelope.status, envelope.check)
print(envelope.result.total_effective_mm)
print(envelope.to_dict()["result"]["schema"])   # hydrolog-scs-effective/1
print(envelope.to_json()[:60])                  # the document of the CLI --json

options = hydrolog.validate_command("scs effective", cn=72, precipitation_mm=50)
print(options["amc"], options["ia_coefficient"])  # defaults filled in

page = hydrolog.list_commands(limit=5).to_dict()
print([item["name"] for item in page["commands"]], page["page"]["next_cursor"])
print(hydrolog.command_schema("tc kirpich").to_dict()["commands"][0]["operation_id"])
```

The envelope has `command`, `inputs`, `result`, `notices`, `files`, `check` and `status`; `to_dict()`
and `to_json()` give the document of `--json`. The function behind a command is named in the
`function` field of `commands schema` (`hydrolog.operations.hydrograph_generate`).

**Errors are exceptions.** Every failure is a subclass of `hydrolog.HydrologError` with `code`
(the codes of the table in section 1), `details` (a dict), `hint` (a string or `None`),
`exit_code` and the English message as `str(exc)`. The classes are `InvalidParameterError`
(`validation_error`; also a `ValueError`), `NotFoundError`, `ConflictError`,
`MissingDependencyError`, `InputDataError` (`data_error`), `OutputError` (`io_error`),
`ForbiddenPathError` and `CalculationError`.

```python
import hydrolog

try:
    hydrolog.run_command("tc kirpich", length_km=-1, slope_m_per_m=0.023)
except hydrolog.HydrologError as error:
    print(error.code, error.exit_code, error.details["option"], error.details["reason"])

try:
    hydrolog.run_command("tc kirpic")
except hydrolog.NotFoundError as error:
    print(error.code, error.details["suggestions"])
```

### The library classes

The commands are thin wrappers over a calculation library. Use the classes directly when you need
objects, arrays or several steps in one process; result objects have `to_dict()` and `to_json()`.
Time of concentration, curve number, hyetograph, hydrograph and unit hydrograph models
(`NashIUH` with `from_lutz` and `from_urban_regression`, `ClarkIUH` with `from_tc_r_ratio`,
`SnyderUH`, `SCSUnitHydrograph`):

```python
from hydrolog.precipitation import BetaHietogram
from hydrolog.runoff import AMC, SCSCN, HydrographGenerator, NashIUH, get_cn
from hydrolog.time import ConcentrationTime

tc = ConcentrationTime.kirpich(length_km=8.2, slope_m_per_m=0.023)   # min
print(tc, ConcentrationTime.nrcs(length_km=8.2, slope_m_per_m=0.023, cn=72))
print(get_cn("B", "forest", "good"), SCSCN(cn=72).effective_precipitation(50.0).total_effective_mm)

precip = BetaHietogram(alpha=2.0, beta=5.0).generate(
    total_mm=38.5, duration_min=60.0, timestep_min=5.0
)
generator = HydrographGenerator(area_km2=45.3, cn=72, tc_min=tc)
result = generator.generate(precip)
print(result.peak_discharge_m3s, result.time_to_peak_min, result.runoff_coefficient)
print(generator.generate(precip, amc=AMC.III).peak_discharge_m3s)   # wetter soil, more runoff

nash = HydrographGenerator(
    area_km2=45.0, cn=72, uh_model="nash", uh_params={"n": 3.0, "k": 0.5}  # k in hours
)
print(nash.generate(precip).peak_discharge_m3s)
lutz = NashIUH.from_lutz(
    L_km=15.0, Lc_km=8.0, slope=0.02, manning_n=0.035,
    forest_pct=40.0, urban_pct=5.0, area_km2=50.0,
)
print(round(lutz.n, 2), round(lutz.k_min, 1))
```

`WatershedParameters` is the exchange format with Hydrograf (`from_dict`, `from_json`,
`to_dict`, `to_json`, `width_km`, `relief_m`, `calculate_tc(method=...)`). The statistics and the
rating curve take NumPy arrays; the soil functions take numbers or raster paths:

```python
import numpy as np

from hydrolog.hydrometrics import RatingCurve
from hydrolog.morphometry import WatershedParameters
from hydrolog.soil import classify_usda_texture, texture_to_hsg
from hydrolog.statistics import FloodFrequencyAnalysis, mann_kendall_test

with open("tests/fixtures/watershed_example.json", encoding="utf-8") as handle:
    watershed = WatershedParameters.from_json(handle.read())
print(watershed.width_km, watershed.relief_m, watershed.calculate_tc(method="kirpich"))

maxima = np.loadtxt("tests/fixtures/annual_maxima.csv", delimiter=",", skiprows=1, usecols=1)
gev = FloodFrequencyAnalysis(maxima, return_periods=np.array([10.0, 100.0])).fit_gev()
print(gev.distribution_name, gev.quantiles, mann_kendall_test(maxima).trend_detected)

pairs = np.loadtxt("tests/fixtures/rating_curve_pairs.csv", delimiter=",", skiprows=1)
fit = RatingCurve(pairs[:, 0], pairs[:, 1]).fit(h0_initial=40.0)
print(fit.a, fit.b, fit.h0, fit.r_squared)

texture = classify_usda_texture(clay=20, sand=40, silt=40)
print(texture, texture_to_hsg(texture))
```

Also in the library: `WatershedGeometry` and `TerrainAnalysis` (shape and relief indicators),
`HypsometricCurve`, `StreamNetwork` (Strahler and Shreve), `thiessen_polygons` and
`inverse_distance_weighting` (areal precipitation), `hydrolog.routing` (`Hydrograph`,
`LagReach`, `MuskingumReach`, `MuskingumCungeReach`: the flood routing of [Flood routing](#flood-routing)) and
`hydrolog.reports.HydrologyReportGenerator` with a `ReportConfig` (the command
`report generate` is the shorter way).

Plots are in `hydrolog.visualization`. They need the `viz` extra (matplotlib and seaborn; without
it a plot function raises `MissingDependencyError`) and are not part of the command catalog. The
functions include `plot_hietogram`, `plot_hydrograph`, `plot_rainfall_runoff`,
`plot_uh_comparison` and `plot_hypsometric_curve`.

```sh
pip install "hydrolog[viz] @ git+https://github.com/Daldek/Hydrolog.git"
```

```python
import matplotlib

matplotlib.use("Agg")  # no display needed

from hydrolog.precipitation import BetaHietogram
from hydrolog.runoff import HydrographGenerator
from hydrolog.visualization import plot_hietogram, plot_hydrograph, setup_hydrolog_style

setup_hydrolog_style()
precip = BetaHietogram(alpha=2.0, beta=5.0).generate(
    total_mm=50.0, duration_min=120.0, timestep_min=10.0
)
result = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0).generate(precip)
plot_hietogram(precip, show_cumulative=True).savefig("hietogram.png", dpi=150)
plot_hydrograph(result.hydrograph, show_peak=True).savefig("hydrograph.png", dpi=150)
```

## 5. The MCP server

The server (extra `mcp`) exposes every catalog command as a tool over standard input and output.
The console script `hydrolog-mcp` and the command `hydrolog mcp` start the same server.

```sh
hydrolog mcp --allow-dir ~/hydrolog-data
hydrolog mcp --allow-dir ~/hydrolog-data --allow-writes
hydrolog mcp --tools tc,cn,core
uvx --from "hydrolog[mcp] @ git+https://github.com/Daldek/Hydrolog.git" hydrolog-mcp --allow-dir ~/hydrolog-data
```

- **`--allow-dir DIR`** (repeatable) is the only place tools may read files from and, with
  `--allow-writes`, write to. A path outside it is refused with `forbidden`
  (`details.allowed_dirs`); a missing directory is a `not_found` error at start-up. Without
  `--allow-dir` every path option is refused, while commands that take numbers (`tc_kirpich`,
  `cn_weighted`, `scs_effective`) work. Give absolute paths inside an allowed directory.
- **`--allow-writes`** lets the writing tools (`hydrolog_report_generate`, `hydrolog_soil_hsg`,
  `hydrolog_commands_guide`) write inside the allowed directories; an existing file is replaced
  only with `force`. Without it the server is read-only: a writing tool runs as `check` (`check`
  is forced to true, `force` is ignored) and returns the plan; nothing is written.
- **`--tools FAMILIES`** limits the tools to comma-separated families: a command group (`tc`,
  `cn`, `scs`, `precip`, `uh`, `hydrograph`, `morphometry`, `network`, `stats`, `hydrometrics`,
  `soil`, `report`, `config`, `commands`) or `core`, the main tasks. An unknown family is a
  `validation_error` that lists the allowed ones.
- The server output is always English; `--lang` only selects the language of
  `hydrolog mcp --help`.

A tool is named `hydrolog_<group>_<command>` with dashes turned into underscores
(`hydrolog_tc_kirpich`, `hydrolog_stats_flood_frequency`, `hydrolog_soil_hsg_stats`): the
`operation_id` of the command. Its arguments are the catalog options:

```json
{"name": "hydrolog_tc_kirpich", "arguments": {"length_km": 8.2, "slope_m_per_m": 0.023}}
```

`tools/list` returns the description, input schema, output schema and annotations (read-only,
destructive, idempotent, open-world) of each tool; `hydrolog_commands_list` and
`hydrolog_commands_schema` are the discovery tools. The server instructions (at most 4,096
characters) state the working order: discover, check, run, read.

- **Success:** `structuredContent` is the `hydrolog-result/1` envelope; the text content is the
  same document as compact JSON.
- **Failure:** `isError` is true and the `hydrolog-error/1` document comes in the same two forms
  (`code`, `details`, `hint`). The code is the one the CLI uses as an exit status.

Client configuration (Claude Code, other MCP clients, `uvx`) is in the [README](../README.md);
the design is in [ADR 0006](decisions/0006-mcp-server-conformance.md).

## 6. Settings

Hydrolog has two settings: `lang` (language of human-readable output, `pl` or `en`; default `pl`)
and `log_level` (verbosity of the log on stderr; default `warning`; `-v` and `-q` change it for
one call). It needs no credentials and has no data directory or cache.

```bash
hydrolog config show --json
```

```json output
{"result": {"schema": "hydrolog-config/1", "settings": [{"key": "lang"}, {"key": "log_level"}]}}
```

`config show` prints each setting with its value and its source (`environment`, `file` or
`default`), the path of the settings file and whether it exists. An option of the call itself
(`--lang en`) applies to that call only and is not reported. A setting comes from the first of:

1. the command-line option (`--lang`, `-v`, `-q`);
2. the environment variable `HYDROLOG_<KEY>` (`HYDROLOG_LANG`, `HYDROLOG_LOG_LEVEL`);
3. the shared variable `NOGAT_<KEY>` (`NOGAT_LANG`, `NOGAT_LOG_LEVEL`);
4. the `[hydrolog]` table of `nogat.toml`, then its `[nogat]` table;
5. the default.

`nogat.toml` is the settings file the Nogat tools share. Its path is `NOGAT_CONFIG`, else
`nogat.toml` in the user configuration directory of `nogat` (`config show` prints it). A missing,
broken or non-UTF-8 file is ignored, so it never stops a calculation.

```toml
[nogat]
lang = "en"

[hydrolog]
log_level = "info"
```

```sh
HYDROLOG_LANG=en hydrolog tc kirpich --length-km 8.2 --slope-m-per-m 0.023
NOGAT_CONFIG=./nogat.toml hydrolog config show
```

`--lang` changes summaries and help only. JSON output, error documents, MCP output and the keys of
results are always English; the Polish texts of the catalog are served from `i18n` of the command
description, and the Markdown report is written in Polish.

## 7. Exchange with Kartograf, IMGWTools and Hydrograf

Hydrolog downloads nothing and does not depend on the other Nogat tools: data arrives as plain
files. Formats and the division of responsibilities are in [INTEGRATION.md](INTEGRATION.md).

- **Kartograf** (spatial data) writes the clay, sand and silt rasters (SoilGrids, g/kg) of
  `kartograf soil download --output-dir DIR`. The `files[].path` entries of its `--json` result
  are the `--clay-path`, `--sand-path` and `--silt-path` of `soil hsg`. Hydrolog reads plain
  files, not a Kartograf store.
- **IMGWTools** (IMGW measurement series) writes a daily series with `imgw series export`. The CSV
  has a `date` column and `Q [m3/s]`; pass it as `--input-file FILE --value-column Q
  --date-column date` to the `stats` commands. Hydrolog ignores the attribution columns; keep them
  when you publish results.
- **Hydrograf** (watershed delineation) produces a JSON in the `WatershedParameters` format:
  `area_km2`, `perimeter_km`, `length_km`, `elevation_min_m` and `elevation_max_m` are required;
  `cn`, `channel_length_km`, `channel_slope_m_per_m` and others are optional. Give it as
  `--watershed-file` to `morphometry watershed`, `tc watershed`, `hydrograph generate` and
  `report generate`, or load it with `WatershedParameters.from_json`. A bad file is a
  `data_error` with `details.path`.

```sh
kartograf soil download --property clay --depth 0-5cm --stat mean --bbox 626000,480000,628000,482000 --bbox-crs EPSG:2180 --output-dir data/kartograf --json
imgw series export --dataset pl.imgw.hydro_daily --station CODE --variables Q --format csv --output q_daily.csv
```

The agent-facing summary of these flows is in [AGENTS.md](../AGENTS.md).
