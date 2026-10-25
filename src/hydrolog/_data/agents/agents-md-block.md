<!-- BEGIN hydrolog -->
## Hydrolog

Hydrolog computes watershed hydrology locally: SCS-CN and curve numbers, design hyetographs, time of concentration, unit and runoff hydrographs, lumped flood routing, morphometry, flow statistics, hydrologic soil groups. It uses no network and downloads nothing. Not for spatial data and rasters (use Kartograf), IMGW/CHMU series (use IMGWTools) or hydraulics (use Hydraulik).

Rule: discover, check, run, read.

1. Discover: `hydrolog commands list`, then `hydrolog commands schema --command NAME`; do not guess options or units.
2. Check: add `--check` to a command that writes a file (`report generate`, `soil hsg`, `route` with `--output` or `--output-dir`); an existing file is replaced only with `--force`.
3. Run with `--json`: the result is a `hydrolog-result/1` envelope, an error a `hydrolog-error/1` document (decide by `code`).
4. Read `result`, `notices` and `result.files`; pass the notices on.

<!-- hydrolog:block_commands -->

Update this block: `hydrolog commands guide --format agents-md-block --inject AGENTS.md`.
Full guide: https://raw.githubusercontent.com/Daldek/Hydrolog/main/AGENTS.md
<!-- END hydrolog -->
