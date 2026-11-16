# 0025. The structure alone in the schematic: `route schematic --structure-only` and „Uporządkuj” before the values

- Status: accepted
- Date: 2026-11-10
- Amends: [ADR-0013](0013-network-schematic.md) (a layout of the structure alone beside the network's:
  `structure_schematic`, and a schematic with `structure_only`, empty `parameters` and an optional `timestep_min`),
  [ADR-0015](0015-catalog-additions-for-the-gui.md) (`route schematic` gains the option `structure_only`),
  [ADR-0023](0023-positions-and-descriptions-in-the-network.md) (Sieć's „Uporządkuj” and the opening of a network
  without positions take the structure's layout; the library still confirms every complete network)
- Builds on: the plan [2026-11-10-network-wizard.md](../plans/2026-11-10-network-wizard.md) (approved 2026-11-10;
  the author's decision A4 and the plan's D7 and D8), which reverses the network editor plan's decision 6

## Context

The author decided on 2026-11-10 (A4) that „Uporządkuj” in Sieć works on the structure alone (ids, types, links),
before the parameters are given. Until now:

- `route schematic` read the network as `route network` does: every field of every node, the files it names
  included. A draft whose nodes miss a value was refused, so Sieć asked for Hydrolog's layout only once the network
  was complete (the network editor plan's decision 6). A network opened without positions stood in provisional rows
  („Układ tymczasowy”) until every parameter was given, and „Uporządkuj” was disabled until then.
- The layout of ADR-0013 needs only the tree, the areas of the headwaters (when every headwater has one) and the
  declared main stem; the number of inflows that each type takes is a class attribute (`Node.inflow_count`). A
  reader of the structure therefore needs no node built.
- The schematic required `timestep_min`. A network's step is the given one, else its first source's, else 5 min,
  and a source may take its step from the inflows file, which a reader of the structure does not open.
- The structure was checked in two places that could drift apart: `Node.read_entry` (one node) and
  `RoutingNetwork._check_shape` (the graph); ADR-0023 tied the browser's checks to them by a corpus.

## Decision

1. **One check of the graph, shared.** `hydrolog.routing.network` checks the links of one node (`check_links`:
   `invalid_id`, `reserved_name`, `upstream_count` from the type's `inflow_count`, `duplicate_upstream`) and the
   graph (`check_graph`: `empty`, `duplicate_node`, `upstream_count`, `unknown_upstream`, `cycle`,
   `several_downstream`, `no_outlet`, `several_outlets`, `outlet_has_downstream`, `disconnected_node`).
   `Node.read_entry`, `RoutingNetwork` and the reader of the structure use them, so the reader of the structure and
   the reader of the network cannot give different reasons (ADR-0010's reasons and details, `node_id` included).
   `RoutingNetwork._check_shape` is removed.
2. **The reader of the structure.** `hydrolog.routing.document.read_structure(document)` returns a frozen
   `NetworkStructure` (`name`, `timestep_min`, `order`, `outlet`, `kinds`, `upstream`, `areas`). Of the document it
   reads `schema`, `name`, `timestep_min` (when it is a positive number), each node's `id`, `type` and `from`, and
   each headwater subcatchment's `watershed.area_km2`; the areas weigh the branches only when every headwater has a
   positive one (ADR-0013's rule). It checks the top of the document as `read_network` does (the same functions)
   and the structure by point 1; every other field may be missing or wrong. It is public by name and, like
   `check_unique`, not in `__all__`.
3. **The schematic of the structure.** `hydrolog.routing.structure_schematic(document, *, main_stem=None)` (and
   `schematic.schematic_of(structure, *, main_stem=None)`) lays the structure out with ADR-0013's computed layout,
   positions ignored. The document is `hydrolog-network-schematic/1` with `structure_only: true` (after `layout`),
   `layout` `computed`, `has_result` false, every node's `parameters` `[]`, no node `description`, and
   `timestep_min` only when the document gives it. For every document that makes a network, the structure's
   picture equals the computed picture of that network (the schematic's nodes, lines, edges and grid); the
   schematics of the existing modes are unchanged byte for byte.
4. **The option `structure_only` of `route schematic`** (boolean, default false; `--structure-only`): it lays out
   the structure by point 3, with `network` or `network_file` and `main_stem`. With `inflows_file` or
   `time_column` it is `conflict` (`details.option` names the option): no file is read. A third rule and a third
   catalog example (a draft without any value) say so.
5. **The JSON Schema** of the schematic: `timestep_min` leaves `required`, `structure_only` (boolean) is added, and
   a schematic without `structure_only: true` requires `timestep_min`. `/1` stays: the schematic is unreleased
   (AGI-4.1) and nothing outside Hydrolog reads it.
6. **Sieć lays out the structure** (plan D8). 300 ms after a change of the structure or of a headwater's area, when
   the browser's checks of the structure (ADR-0023, point 8) find nothing, Sieć sends `route schematic` with
   `structure_only` and a document of the structure alone (`state.js` `structureDocument`: each node's `id`, `type`
   and `from`, and the positive area of each subcatchment) on the channel `siec-layout`. That layout serves
   „Uporządkuj” and places a network opened without positions; the provisional rows remain only while the
   structure has a problem. The full `route schematic` on `siec-schematic` stays Hydrolog's check of a complete
   network (ADR-0023, point 8, „the library confirms”); its positions are no longer used. The canvas ranks its
   lines with the same areas (`geometry.js` `isArea`: a positive finite number). Positions still never mark a
   result stale.

## Consequences

- **A draft is laid out before its values.** A network built from „Nowa sieć” without any parameter is tidied by
  „Uporządkuj” at the library's positions, and a network opened without positions whose nodes miss values (Nogat's
  example network, whose reach `R1` has no section) appears at the library's positions without „Układ tymczasowy”.
  A structural problem still gives the provisional rows, and „Uporządkuj” says that it waits for the structure.
- **Consumers.** Nothing outside Hydrolog reads the schematic, and the documents of `route schematic` without the
  option and of `route network --schematic` do not change. A reader of the schematic that relied on `timestep_min`
  being present finds it in every schematic but those with `structure_only: true`.
- **Python API.** New: `structure_schematic` (in `hydrolog.routing`), `read_structure`, `NetworkStructure`,
  `check_links`, `check_graph`, `upstream_from_document`, `schematic_of`, and `route_schematic(...,
  structure_only=False)`. `RoutingNetwork._check_shape`, a private method, is gone.
- **The catalog.** One option, one rule and one example of `route schematic`; the MCP description stays within its
  budget (579 of 600 characters). `AGENTS.md` and `llms.txt` do not change.
- **Tests tie the readers together**: a property test on random trees (without areas, with areas, with some areas,
  with and without a declared main stem) compares the structure's layout with the network's, and the corpus of
  one-problem documents gives the same reason, `node_id` and message from both readers; the browser's
  `structureDocument` and `linesOf` are compared with `structure_schematic`.

## Alternatives considered

- **Keep „Uporządkuj” for complete networks** (the network editor plan's decision 6): a person who draws first and
  fills in the values later cannot tidy the drawing, and a network opened without positions, such as Hydrograf's,
  stays in provisional rows until every value is given. The author decided against it (A4).
- **Lay the structure out in the browser** with a copy of ADR-0013's layout: a second implementation of the layout
  to keep equal to the library's, against the GUI plan's D8 (Hydrolog computes, the browser draws).
- **Fill the missing values with placeholders** and send the network to the existing `route schematic`: the reader
  would check placeholders, not the person's document, and its reasons would name fields that the person never
  wrote.
- **A separate command** (`route structure`): a second command with the options and the result of `route
  schematic`; an option of the command keeps one entry in the catalog and one result schema.
- **A schematic of version `/2`** for the optional `timestep_min`: the schematic is unreleased (AGI-4.1).
