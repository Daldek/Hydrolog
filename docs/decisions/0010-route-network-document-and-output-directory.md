# 0010. `route network`: the network document, one table per node, `--output-dir`

- Status: accepted
- Date: 2026-10-25
- Amended by [ADR-0012](0012-network-objects-rainfall-and-runoff.md): the nodes of `RoutingNetwork` are typed
  objects that link by reference (`Subcatchment`, `Channel`, `Reservoir`, `Junction`, `Outlet`, all `Node`); the
  first version had one generic `NetworkNode`. The document and its errors are unchanged, and it gained fields.

## Context

The plan [2026-10-24-flood-routing.md](../plans/2026-10-24-flood-routing.md) ends with `route network`: the
elements of [ADR-0007](0007-flood-routing-enters-the-scope.md) composed over a river network, with a
hydrograph file per node as the hand-off to Hydraulik. Three things were open: how a network is written
down (Hydrograf will write it and an agent has to be able to write it inline), what a command writes when it
has many outputs ([ADR-0003](0003-writing-commands-output-force-check.md) said Hydrolog has no `--output-dir`
because every command wrote one file), and how the library finds the order of a network without a second
copy of the graph code of `StreamNetwork`.

## Decision

- **The document `hydrolog-network/1`.** A JSON object with `schema` (required, `hydrolog-network/1`) and
  `nodes` (required), and `name` (optional; an unknown field is an error). A node has
  `id`, `type` and `from` (the ids that flow into it) and the fields of its type: a subcatchment has
  `times_min` with `discharge_m3s`, or `value_column`; a reach has `method` and the options of
  `route <method>` that describe the element (the catalog options of that command without the inflow, the
  run and the output options), `initial_outflow_m3s` and `extend_min`; a reservoir has the options of
  `route level-pool`; a junction and the outlet have nothing more. Every option is validated by its catalog
  declaration (`Option.normalize`), so a document cannot hold a value that the command line refuses. The
  JSON Schema `hydrolog-network/1` is shipped and generated from the same declarations (a variant per type,
  and a reach per method).
- **Sources** are inline or columns of one `inflows_file` (a time column and a column per subcatchment,
  named by its `value_column` or else by its `id`). All sources have one time step and one first time:
  nothing is resampled (ADR-0008).
- **Files that a document names stay beside it.** The path rules of a server (`--allow-dir`) see the
  options of a call, not the files that a document names. A `rating_file` is therefore relative to the
  directory of `network_file` and must lie inside it after links are resolved (`path_outside`); an inline
  network cannot name files (`inline_file`).
- **Errors of the document** are a `data_error` with `details.path` for a file and a `validation_error`
  with `details.option` `network` for the inline option, with the same `details.reason`, `node_id` and
  `field`: the reasons of the reader (`shape`, `unknown_field`, `unknown_method`, `missing_field`, `type`,
  `conflict`...), the reasons of the option or the element that refuses a value (`minimum`, `one_of`,
  `unstable_timestep`...) and the structure reasons of `RoutingNetwork` (`unknown_upstream`, `cycle`,
  `several_downstream`, `no_outlet`, `several_outlets`, `outlet_has_downstream`, `disconnected_node`,
  `duplicate_node`, `invalid_id`, `upstream_count`, `duplicate_upstream`). Sources that do not share a time
  axis (`timestep_mismatch`, `start_mismatch`) stay a `validation_error` for both sources: that is a fact
  of the data, not of the document. A reach that fails names its node (`details.node_id`).
- **A bifurcation is refused** (`several_downstream`): a lumped model would count its water twice. A
  network has one outlet and water flows to it.
- **Order.** `RoutingNetwork` evaluates the headwaters first and, among the nodes that are ready, the
  smallest id first, with the graph code that `StreamNetwork` now shares (`hydrolog.network._graph`:
  `upstream_first`, `UnknownUpstream`, `UpstreamCycle`); the order of the nodes in a document changes
  nothing.
- **Output: `--output-dir`.** `route network` writes `<id>.csv` for each selected node (`--nodes`, default
  all) into the directory `--output-dir` (`-o`). Each file is the hydrograph table of ADR-0008 that leaves the
  node, which every `route` command reads again and which is the hand-off to Hydraulik. This is the plain
  mode of DEV section 19 for a directory (DEV-19.5 to DEV-19.11) and amends ADR-0003. The plan is shared in
  `operations/_outputs.py` (`plan_directory`: `write`, `replace` with `--force`, `conflict`; names compared
  without regard to case; `duplicate_output_name`; `output_in_store` for a directory that is, or lies in, a
  store of another Nogat tool, recognised by its marker file alone); a table that would overwrite an input
  (`network_file`, `inflows_file`, a `rating_file`) is refused; the files are written through
  `<dir>/.hydrolog-incoming/<host>_<pid>_<token>/` and moved with `os.replace` after the plan has been made
  again, so a file that appeared during the computation is a conflict. Without `--output-dir` the
  hydrographs of the selected nodes are in the result and `--check` computes (ADR-0008): a read-only MCP
  server can route a network.
- **Result `hydrolog-route-network/1`:** `name`, `timestep_min`, `outlet`, `order` and `nodes[]`, one entry
  per node with `id`, `type`, `from`, `peak_m3s`, `time_to_peak_min` and `volume_m3` and, for a reach or a
  reservoir, the `model`, `parameters`, `peak_attenuation_pct`, `peak_delay_min` and `balance_error_m3` of
  its run. The notices of a reach begin with the id of its node.

## Consequences

- Hydrograf can write the document and Hydraulik can read the table of each node it needs
  ([INTEGRATION.md](../INTEGRATION.md)); no other file of Hydrolog is read by another tool.
- Deviation DEV-19.7 narrows: a command that writes one file (`--output`) still goes through a temporary
  file beside the target; a directory goes through the staging directory (`CLAUDE.md`).
- `-o` is the short flag of `output_dir` and of no other option (AGI-3.4).
- One module reads a network: `hydrolog.operations._network_input`.
- Not done: bifurcations, sources computed from a watershed or from rain, channel parameters estimated from
  geometry in the document (a node gives the parameters of its method) and `request` issues in the Hydrograf
  and Hydraulik repositories (DEV-17.5).

## Amendment (2026-10-25, open points of the first version)

Three points that the first version left open were decided by the coordinating session
(the author has not reviewed the branch yet):

- **`schema` is required.** A document without `schema` is `missing_field` (`details.field` `schema`);
  one with another value is still `unknown_schema`. Reason: AGI-4.1, every machine-readable document has a
  top-level `schema`, and a reader that guesses the version of a document that does not say it has nothing to
  stand on when `hydrolog-network/2` exists. The JSON Schema lists `schema` in `required`. This replaces
  "optional" in the decision above.
- **An id that is a device name of Windows is refused.** `con`, `prn`, `aux`, `nul`, `com1` to `com9` and
  `lpt1` to `lpt9`, in any case and with any extension (`NUL.csv` is the device too), are a
  `validation_error` with `details.reason` `reserved_name`, from `Node` (so the library, the reader
  and `hydrolog-network/1`, in which the id is a pattern with a `not`, agree). Reason: the id names the file
  `<id>.csv` and a file of that name misbehaves on Windows, where the tables go to Hydraulik. The
  superscript digits (`com¹` to `lpt³`) that Windows also reserves are refused too.
- **A large result says so.** Without `--output-dir` the result holds the hydrograph of every selected node;
  the envelope does not page the result of a command (only collections are paged), so a result of more
  than 20,000 characters (the default page of DOC-1.7) carries the warning `large_result`, which names
  `--nodes` and `--output-dir`. The result is not cut: a client that cannot read it all has the choice the
  notice gives.
