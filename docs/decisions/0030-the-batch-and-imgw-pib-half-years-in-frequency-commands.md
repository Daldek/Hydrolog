# 0030. The batch of catalog calls and IMGW-PIB's half-years in the frequency commands

- Status: accepted
- Date: 2026-11-13
- Builds on: plan `docs/plans/2026-11-13-station-analyses.md` (decisions D9, D10, step S2), Nogat's plan `2026-11-12-station-data-and-analyses` (step H4, decisions D6, F1), approved by the author on 2026-11-13; ADR-0002 (the envelope), ADR-0003 (writes), ADR-0028 (the providers' lines), ADR-0029
- Amended by [ADR-0033](0033-review-of-the-station-analyses.md) (2026-11-13): the batch runs offline and writes only its output (its point 3)

## Context

Obserwator computes a whole station's analyses with Hydrolog once at the start and once a year (the author's answer 2 of 2026-11-13). A call of the CLI costs about 1.4 s, mostly imports, and a station has tens of calls. Nogat's F1 makes IMGW-PIB's published half-year extremes a source of the annual maxima and minima beside the daily series; `stats characteristic` reads them since ADR-0029, the frequency commands did not.

## Decision

1. **`commands batch`** (D10, new): `input_file` is JSON Lines, one `{"command": "<name or operation_id>", "options": {...}}` per line; `output` gets line i for call i, the `hydrolog-result/1` envelope of `run_command` or the `hydrolog-error/1` document of its error, compact UTF-8 JSON, the very line the CLI prints with `--json` for the call alone. One process; a failing call does not stop the batch; relative paths of a call are taken from the directory of `input_file`; `check` and `force` as ADR-0003, the output written atomically when the last call is done.
2. **The path policy covers every call.** `run_command` holds the `allowed_dirs` of its call while the operation runs (`hydrolog.catalog.dispatch.call_allowed_dirs`, a context variable), and the batch passes them to each call: MCP's `--allow-dir` applies to the calls; a server without `--allow-writes` plans the batch and runs nothing.
3. **Lines that are not calls**: a line that is not JSON, not an object with exactly `command` and `options`, or calls `commands batch` or `gui serve` gets a `validation_error` document (`details.reason` `invalid_call`, `not_in_batch`, `details.line`); an unknown command is `not_found`, as alone. A file without a line is `data_error` `empty`.
4. **Outcomes of ERR §1.** The plan's result `hydrolog-commands-batch/1` (`n_calls`, `n_ok`, `n_failed`, `failed` of `{line, command, code}`, `files`) is accompanied by the envelope's `items`, one `{id, status, code?, reason?, message?}` per line (`id` the line), as AGI-4.2 asks of a batch: `status` is `partial` when some calls failed and `failed` when all did, and the CLI then exits with 10 or 11 and prints the envelope as for success. Every other command keeps `status` `ok`. The plan named the result fields only; the outcome is the standard's for any batch (requirements AGI-4.1 to AGI-4.3 of the plan).
5. **The GUI does not offer the batch**: its calls would reach the commands the GUI leaves out (`config show`, `gui serve`, `commands guide`); 48 of 52 commands stay in „Wszystkie polecenia”.
6. **Half-years in the frequency commands** (D9): `stats flood-frequency`, `stats low-flow` and `stats homogeneity` take `half_year_file` (a third `one_of` group), `parameter` (`Q`, `H`; the columns of the file) and `first_year`, `last_year`. The annual maximum is the larger of the winter and summer maxima, the annual minimum the smaller of the minima, of the years that have both (`hydrolog.statistics.annual_extremes_from_half_years`, the values of ADR-0029's first degree); a year with one half-year only is left out and named in `incomplete_years`. The results gain `source` (`daily`, `values`, `half_years`) and, for homogeneity, `hydrological_years`. `first_year`, `last_year` choose the years of a daily series or of the file; given for annual values without dates they are a `validation_error` (`not_applicable`). The notices `short_record` and `small_sample` stay as they are; `stats low-flow` of half-years fits the minima directly (`hydrolog.statistics.fit_fisher_tippett_minima`).
7. **The providers' lines** (ADR-0028): `run_command` collects the lines of a call inside the collection of the batch's own call, which takes them when the call ends, so a line of `output` carries the `attribution` and `terms_notice` of its call alone and the batch's envelope the union of the lines of its calls (the file it writes holds their data). The lines of IMGW-PIB's half-year file, read by `hydrolog.catalog.inputs.read_table`, reach the results of the three frequency commands as those of a daily export do.
8. Budgets: `commands batch` has its own line in the command index; `AGENTS.md` has 16,246 of 16,384 bytes.

## Consequences

- A whole station runs in one process: 1,000 calls in one batch give the same bytes as the same calls run alone with the CLI (the plan's Results, with the times).
- The envelope's `status` is no longer always `ok`: a client of `commands batch` reads `status` and `items`; the exit codes 10 and 11 are outcomes, not errors.
- Additive for the result schemas (`source`, `hydrological_years` in `_ADDED_FIELDS`); one new schema.

## Alternatives considered

- **`status` always `ok` with the failures in the result only**: an agent reading `status` would take a batch with failed calls for a success, and the standard's outcomes exist for this case.
- **Blank lines skipped**: line i of `output` would no longer answer line i of `input_file`; a blank line is a call that is not one.
- **A server of warm workers instead of a batch**: Obserwator's computation is a yearly job; a file in, a file out is simpler to run, check and store.
