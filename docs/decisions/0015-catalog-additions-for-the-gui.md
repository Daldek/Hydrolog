# 0015. Catalog additions for the GUI

- Status: accepted
- Date: 2026-11-02
- Amended by [ADR-0017](0017-typical-ranges-in-the-catalog.md) (2026-11-04): the bounds of the `outside_typical_range`
  notices come from one table
- Amends: [ADR-0001](0001-catalog-english-and-operation-ids.md) (the derivation of `check` and `families`),
  [ADR-0002](0002-result-envelope-and-domain-documents.md) (notices gain `details`),
  [ADR-0006](0006-mcp-server-conformance.md) (a catalog command that is not an MCP tool),
  [ADR-0009](0009-compact-index-line-for-large-groups.md) (a command that is not in the guide's index)
- Builds on: [ADR-0013](0013-network-schematic.md) (the schematic document)

## Context

The web GUI of [ADR-0014](0014-web-gui-enters-the-scope.md) is a client of the catalog: it shows the CLI line of every
run, words notices in Polish, draws a network before routing it and draws the unit hydrograph of a run. The plan
[2026-11-02-hydrolog-gui.md](../plans/2026-11-02-hydrolog-gui.md) (slice S0; decisions D3, D5, D11, D14 and D16)
found what the catalog lacked for that:

- no public function formats or parses a command line (AGI-2.1; the CLI's `format_example` was internal);
- library warnings became notices with the generic code `user_warning` and English text that held the values, so a
  client could neither word them in its language nor tell them apart;
- `route network` returned `hydrolog-network-schematic/1` only when it wrote the SVG, and no command laid a network out
  without routing it;
- `hydrograph generate` returned the hydrograph but not the unit hydrograph it convolved (`uh snyder` alone differs
  from the UH used inside, whose duration equals the step);
- a command to start the GUI's server must be in the catalog (Nogat's routes read `commands list`, HUB-2.9) but must
  not be an MCP tool (it blocks) nor a line of `AGENTS.md`, which had 107 of its 16,384 bytes left.

## Decision

- **`format_command` and `parse_command` (AGI-2.1)**, public in `hydrolog.catalog` and in `hydrolog`
  (`hydrolog.__all__`). `format_command(command, options=None, run=None)` returns the canonical line
  `hydrolog <group> <verb> --flag value ...`: options in catalog order, `shlex`-quoted, booleans as `--x` or `--no-x`,
  `None` left out, then the run flags `--json`, `--lang X`, `--verbose`, `--quiet` (run keys `json`, `lang`, `verbose`,
  `quiet`). It checks option names and value forms (types), not bounds, `required` or `one_of`, so the line of a call
  that the catalog would refuse can still be shown. `parse_command(line)` reads a line, or its words, with the CLI's
  own parser and returns `ParsedCommand(command, options, run)`; `--help`, `--version` and `--schema` are refused,
  because they ask for a description, not a call. `format_command(*parse_command(line))` is `line` for every canonical
  line, and the `call` of every catalog example (`commands-1`) is the canonical line of the example. The CLI uses the
  same function; `cli.parser.format_example` is gone.
- **Notices with stable codes, `details` and the registry `NOTICES`.**
  - `Notice` gains `details` (a mapping, optional, not part of equality); `to_dict()` adds `"details": {...}`
    (JSON-native) only when it is not empty. `result-1` leaves notice objects open, so the envelope schema is
    unchanged. This amends [ADR-0002](0002-result-envelope-and-domain-documents.md), whose notices had `level`, `code`
    and `message` only.
  - `hydrolog.catalog.NOTICES` maps every code that Hydrolog emits to a `NoticeSpec` (`code`, `level` `info` or
    `warning`, the English `template` whose fields are the `details` keys, `details`, the keys that every notice of
    the code carries, and `own_text`): a read-only, enumerable registry in the order of its table, so a client can
    check that it words every code. `notice(code, **details)` builds a notice from the registry and refuses an unknown
    code, an `own_text` code or keys other than the spec's.
  - Library warnings are subclasses of `HydrologWarning` (a `UserWarning`, in the leaf module `hydrolog._warnings`),
    one per code and named after it in CamelCase (`OutsideTypicalRange`, `IncompleteYears`, `SmallSample`,
    `ShortRecord`, `KsTestApproximate`, `UnknownHietogramType`, `UhModelMismatch`); the instance carries its `details`
    and renders its message from the template. `capture_warnings` turns one into a notice with the class's code and
    details. Any other warning becomes `user_warning` (the `UserWarning` family) or `runtime_warning`
    (`RuntimeWarning`, from NumPy and SciPy) with its own text, never a code made of a third-party class name, so the
    set of codes is closed. The deprecation warning of `NashIUH.from_tc` stays a `DeprecationWarning`.
  - The notices of the routing models (`tail_extended`, `tail_truncated`, `lag_interpolated`, `timestep_refined`,
    `substeps_added`, `subreaches_adjusted`, `accuracy_limit`, and `duration_not_covered` from a network) keep their
    codes and English text but carry no `details` yet (`own_text` in the registry), because the plan's decision D1
    limits the edits of routing code to `catalog/groups/route.py` and `operations/route.py`. `route network` adds
    `details.node_id` to the notice of a node (the message keeps its `R1: ` prefix), and a routing notice whose code is
    not in the registry becomes `user_warning`.
  - Changed codes and messages: the rating curve (`hydrometrics rating-curve`) reports removed pairs as
    `missing_pairs_removed` (formerly `missing_values_removed`, which stays for series); `slopes_from_relief` is one
    notice per given slope (`option`, `given_m_per_m`, `computed_m_per_m`) instead of one for both; the statistics emit
    `small_sample`, `short_record` and `ks_test_approximate` instead of `user_warning`, with new texts; the other former
    `user_warning` notices of the library are `outside_typical_range`, `incomplete_years`, `unknown_hietogram_type`
    and `uh_model_mismatch`.
  - The GUI's server adds `superseded` and `timeout` ([ADR-0014](0014-web-gui-enters-the-scope.md)) and `gui serve`
    adds `exposed_without_auth`; they are in the registry like every other code.
- **`route schematic`**, a read-only command (`hydrolog.operations.route_schematic`): the network as `network` or
  `network_file`, read as `route network` reads it, optionally `inflows_file` with `time_column` (a network whose
  subcatchments read their discharges from a file is checked as a whole when it is read, so it is laid out only with
  that file) and `main_stem`. Its result is the document `hydrolog-network-schematic/1` of
  [ADR-0013](0013-network-schematic.md) without values (`has_result` false), equal to `RoutingNetwork.schematic()`;
  it routes nothing and writes no file. The catalog names that document as the result schema
  (`Command.result_schema`) instead of a `hydrolog-route-schematic/1` of its own
  ([ADR-0002](0002-result-envelope-and-domain-documents.md)), because the result is exactly that document. The group
  `route` stays one index line of the guide (ADR-0009), so the command costs a few bytes.
- **The ordinates of the unit hydrograph in `hydrograph generate`:** `uh_times_min` [min] and
  `uh_discharge_m3s_per_mm` [m3/s per mm], the unit hydrograph used in the convolution, so that the UH ordinates
  convolved with the effective precipitation give the hydrograph. They are optional fields: the version stays
  `hydrolog-hydrograph-generate/1` (AGI-4.1), and the schema generator never makes a field added later required.
- **`gui serve` and `Command.agent_tool`.** `Command` gains `agent_tool: bool = True`. `gui serve` has
  `agent_tool=False`: it is not an MCP tool (its `families` are empty) and has no line in the index of `AGENTS.md`,
  `llms.txt` or the group list of the guides, but it is in `commands list` and `commands schema`, as Nogat's routes
  need (HUB-2.9). This amends [ADR-0006](0006-mcp-server-conformance.md) (one tool per catalog command) and
  [ADR-0009](0009-compact-index-line-for-large-groups.md) (every command named once in the index): both now hold for
  the commands with `agent_tool` only.
- **`Command.check` follows a `check` option.** The command plans itself when it declares an option `check`
  (formerly: when it writes a file). Every writing command declares one, so nothing changes for them, and
  `gui serve --check` is its own plan: `hydrolog-plan/1` with `targets: []`, `url` and `port_free`, without serving,
  so its catalog example runs in the contract tests. This amends [ADR-0001](0001-catalog-english-and-operation-ids.md),
  which derived `check` from writing.
- **`gui serve` itself:** options `host` (default `127.0.0.1`), `port` (1 to 65535, default `8070`), `no_browser` and
  `check`. Serving calls `hydrolog.gui.server.serve`, blocks, and on Ctrl+C or SIGTERM returns
  `hydrolog-gui-serve/1` (`url`, `started_at`, `stopped_at`) with exit 0. A host other than loopback adds the warning
  `exposed_without_auth`; without the extra `gui` the command ends with `missing_dependency` and the hint
  `pip install "hydrolog[gui]"`.

## Consequences

- The CLI line that the GUI shows is the line the CLI runs; an agent or a script can turn a call into a line and back
  with the same functions.
- A client can word every notice from `code` and `details` and test that it knows every code (`NOTICES`); the GUI's
  contract test fails for a code without a Polish text. A code is a promise: renaming one is a change of the public
  interface.
- Warnings caught by `warnings.catch_warnings` or filters on `UserWarning` work as before (the classes are
  `UserWarning`s), but the messages of the statistics and of the rating curve changed.
- No notice of any catalog example is `user_warning` (a contract test).
- `AGENTS.md` gains no index line for `gui serve`; `gui serve` is absent from MCP `tools/list`.
- Not done: `details` for the routing models' notices (after the routing branches are merged), and option names in
  the errors raised inside library classes (`details.option`; a later plan).

## Alternatives considered

- **Keep `user_warning` and let the GUI parse the English text:** brittle, and no client could know the full set of
  messages.
- **Polish messages in the library:** machine output is English (ADR-0001); the language belongs to the client.
- **Derive a notice code from any warning class:** the set of codes would depend on third-party libraries.
- **The schematic from `route network` only:** it lays a network out after routing it, and only when it writes the
  SVG; Sieć draws the network before „Oblicz sieć”, so the layout needs a command of its own that computes nothing.
- **A separate `uh` call for the GUI's unit hydrograph:** `uh snyder` alone differs from the UH used inside
  `hydrograph generate`; only the result of the run shows what was convolved.
- **`gui serve` outside the catalog (a plain CLI subcommand):** Nogat's registry would not see it, and it would
  bypass the error document and exit codes of every other command.
