# 0023. Positions and descriptions in the network: the given picture, rule D and the editor's structure checks

- Status: accepted
- Date: 2026-11-10
- Amended by [ADR-0025](0025-the-structure-alone-in-the-schematic.md) (2026-11-10): Sieć's „Uporządkuj” and the
  opening of a network without positions take the layout of the structure alone (`route schematic
  --structure-only`); the library still confirms every complete network.
- Amends: [ADR-0010](0010-route-network-document-and-output-directory.md) (a node of `hydrolog-network/1` may have
  `description` and `position`, and the document a `description` at its top; the reader stays strict),
  [ADR-0012](0012-network-objects-rainfall-and-runoff.md) (the fields that every node has are read and written by the
  base class `Node`; `Node.read_entry` returns a `NodeEntry` and `Node.build` takes it),
  [ADR-0013](0013-network-schematic.md) (the picture depends on the network and on the positions its document holds:
  the given layout, rule D, `layout` and a node's `description` in the schematic, the notice `positions_ignored`),
  [ADR-0014](0014-web-gui-enters-the-scope.md) (Sieć becomes the editor of the network's structure and checks the
  structure in the browser with the library's reason codes; the library confirms every complete network)
- Builds on: the plan [2026-11-10-network-editor.md](../plans/2026-11-10-network-editor.md) (approved 2026-11-10;
  decisions D1, D3, D4, D5, D8, D13, D14 and the author's decisions)

## Context

The author asked on 2026-11-10 for a graphical editor of the network in „Sieć i trasowanie”, modelled on the basin
model editor of HEC-HMS: the person adds elements, connects each to the element below it and describes each one.
Until now Sieć showed the structure and never edited it (the GUI plan's D18 and S4), and its picture was the answer of
`route schematic`, which needs a complete network. An editor needs the document to keep the picture (where each node
is) and words for people (what each node is), and it needs a picture of a draft that the library cannot read yet.

Facts that shaped the decision (checked in the plan):

- The reader refuses an unknown field at the top, in a node and in the front door of the commands, and the node
  branches of the JSON Schema are closed. A new field is therefore refused by every Hydrolog before it. AGI-4.1 keeps
  the version for optional fields, and ADR-0012 added `timestep_min`, `rainfall`, `watershed` and `runoff` to `/1`
  under that rule.
- ADR-0013's layout depends on the tree, the areas of the headwaters and the declared main stem. On 5,040 random
  trees (3 to 150 nodes, up to 12 inflows, with and without areas) all 216,720 edges of the computed layout equal one
  rule computed from the positions of the edge's two nodes alone (rule D below). The positions are the whole picture.
- A simpler one-bend rule does not reproduce it: from the same positions it differs on 4 % of the edges (1,000 trees)
  and breaks the independent check of the picture (crossings, an edge through a node) in 31 % of the trees.
- The network and its reader stop at the first problem (`InvalidParameterError` with `details.reason` and `node_id`,
  ADR-0010). The library cannot list every problem of a draft at once.

## Decision

1. **The document `hydrolog-network/1` keeps its version** (AGI-4.1, as ADR-0012 did). Every node, of any type (a
   type registered by another package too), may have two optional fields:
   - `description`: plain text for people, never read as HTML or Markdown. A string of 1 to 500 characters (Unicode
     code points; `MAX_DESCRIPTION_CHARS`), not blank, with no control character (Unicode category Cc) other than the
     line feed `\n`, because the others are not valid in the SVG. Reasons (`details.reason`): `type` (not a string),
     `empty` (blank), `too_long` (`details.max_length` 500, `details.length`), `control_character`
     (`details.character`, e.g. `U+0009`); always `details.field` `description` and `details.node_id`.
   - `position`: `{"x": int, "y": int}`, the cell of the node in the grid of ADR-0013's schematic: `x` grows
     downstream, `y` sideways (downwards on a screen). Whole numbers from −1000 to 1000 (`MAX_POSITION`), exactly
     these two keys; a number with a zero fraction (`2.0`) is read as `2` and written as `2`. Reasons: `type` (`field`
     `position` when it is not an object; `position.x` or `position.y` when a coordinate is not a whole number, with
     `details.value`), `unknown_field` (`field` `position.z`, `details.allowed` `["x", "y"]`), `missing_field`
     (`field` `position.x`), `minimum` and `maximum` (`field` `position.x`, `details.minimum` −1000 or
     `details.maximum` 1000, `details.value`); always `details.node_id`.

   The document may have its own `description` at its top, with the same rules and reasons (`details.field`
   `description`, no `node_id`). Positions are snapped to the grid (the author's decision 1): the keys move a node by
   one cell, and the computed picture is stored exactly. A description is plain text of up to 500 characters with line
   breaks, for every node and for the whole network (the author's decision 3); the id stays the name of a node.
   - **The canonical form** (`to_document()`, `write_network`): a node is `id`, `type`, `from`, the fields of its kind,
     then `description`, then `position`, each only when given; the top is `schema`, `name`, `description`,
     `timestep_min`, `rainfall`, `nodes`. A document without the new fields is written byte for byte as before.
   - **Neither field changes a computation.** The result `hydrolog-route-network/1`, the tables and `describe()` are
     the same with and without them; `NetworkResult` does not carry them.
   - **The reader stays strict** (ADR-0010): a misspelt field is still `unknown_field`, not something ignored.
   - **The front door** (`route network`, `route schematic`, the MCP tools) passes the fields through
     `operations/_network_input.py` (its common fields are now `id`, `type`, `from`, `description`, `position`) to the
     library, which checks them. An error of a file is `InputDataError` (`data_error`) with `details.path`; of an
     inline network, `InvalidParameterError` (`validation_error`) with `details.option` `network`. No catalog option
     changes.
2. **The library** (`hydrolog.routing`).
   - `Position(x, y)`, a `NamedTuple` of two integers, exported with `MAX_DESCRIPTION_CHARS = 500` and
     `MAX_POSITION = 1000`.
   - `Node.description` (`str | None`) and `Node.position` (`Position | None`), and the copies
     `Node.with_description(text | None)` and `Node.with_position(Position | (x, y) | None)`: like `with_inflows()`
     they return a copy, and they check the value with the reasons above and `details.node_id`.
   - They live on the base class `Node`, which reads and writes them in one place, so every registered type carries
     them without code of its own. `Node.read_entry(node_id, fields)` returns a `NodeEntry(upstream, arguments,
     description, position)` (a `NamedTuple` in `hydrolog.routing.network`) and `Node.build(node_id, entry, inflows)`
     takes it; before, they returned and took `(upstream, arguments)` and `arguments`. `Node.to_document()` writes the
     fields after `document_fields()`. `read_document()` of a kind receives the whole node and must not take fields
     named `description` or `position`.
   - `RoutingNetwork(nodes, *, name=None, description=None, rainfall=None, timestep_min=None)` keeps the network's
     description as `description`, like `name`. `from_document` and `to_document`, `read_network` and `write_network`
     keep everything.
   - The module `hydrolog.routing.network` has the checks and the conversions: `check_description(value,
     node_id=None)`, `check_position(value, node_id)`, `position_from_document(value, node_id)` and
     `position_to_document(position)`.
   - `hydrolog.testing` keeps in step with the format (DEV-10.6): `placed(node, *, description=None, position=None)`
     returns a copy of a builder's node with the fields, checked by the library's own checks and in the canonical
     order, and `network_document(..., description=None)` gives the network its description; `network_document`
     checks everything through the real loader of `route network`.
3. **The given picture.** `RoutingNetwork.schematic()`, and with it `route network --schematic` and
   `route schematic`, draws the **given** layout when every node has a position and no two share a cell. The nodes
   stay where they are, moved together so that the smallest `x` and `y` are 0. The lines (colours, the main stem) are
   ranked exactly as in the computed layout, `main_stem` included, and the labels follow ADR-0013's rule (the first
   free compass place). A given picture may cross itself or run an edge through a node: that is the person's
   arrangement. Otherwise the layout is **computed** as in ADR-0013 (point 4).

   **Rule D** draws the edge from node A to the node B it flows into, with `dx` and `dy` the steps from A to B in grid
   units (`hydrolog.routing._layout.edge_route(start, end)`):
   1. `dx = 0` or `dy = 0`: one straight segment;
   2. `dx > 0`: a sideways leg of `|dy| − 1` to the row next to B's, one 45° step onto B's row, then along that row
      into B (`dx − 1`); a leg of length 0 is left out. This is ADR-0013's join: the vertical leg, 45 degrees, the
      taps;
   3. `dx < 0` (B upstream of A): a 45° leg of `min(|dx|, |dy|)` from A, then straight into B.

   Every segment is at 0, 45 or 90 degrees. Rule D gives every edge of the computed layout from its two end positions
   (the measurement above; a property test in the gate keeps it on random trees), so a document that stores the
   computed positions draws exactly ADR-0013's picture. A document stores no routes.
   `hydrolog.routing._layout.given_layout(root, inflows, positions, *, weight=None, main_stem=())` is the given layout;
   `Line.row` is `int | None`, `None` for a line of a given layout whose nodes lie on several rows.
4. **The notice `positions_ignored`** (level `warning`; details `reason`, `node_id`). When some nodes have positions
   and another has none (`reason` `partial`), or every node has one but two share a cell (`shared_cell`), the layout
   is computed and the warning names the first node at fault in the order of evaluation (for a shared cell, the later
   of the two). A network in which no node has a position is computed silently. The English template is
   `Positions ignored at node {node_id!r} ({reason}): the layout is computed`. The library class is
   `hydrolog._warnings.PositionsIgnored`, a `HydrologWarning` (so a `UserWarning`), in `LIBRARY_WARNINGS` and in
   `NOTICES`; `RoutingNetwork.schematic()` issues it as a Python warning, and `route network` (only with `schematic`)
   and `route schematic` turn it into a notice of the envelope. The GUI has its Polish text (GUI plan D16).
5. **The schematic `hydrolog-network-schematic/1` keeps its version** and gains two optional fields: `layout`
   (`"given"` or `"computed"`, at the top after `has_result`; the library always writes it, and a document without it
   is computed) and a node's `description` (after `label`, only when the node has one). The network's own description
   is in neither the schematic nor the result. `schematic_svg` puts a node's description in its tooltip (`<title>`), on
   the line after `id (type)`, escaped like all text.
6. **The JSON Schemas** are regenerated: `hydrolog-network-1.schema.json` has `$defs.description` and
   `$defs.position`, both properties in every node branch and `description` at the top;
   `hydrolog-network-schematic-1.schema.json` has `layout` and a node's `description`.
7. **The GUI.** Sieć becomes the editor of the network's structure (plan D1): the canvas and the editing come with the
   plan's stages E2 and E3, which supersede the GUI plan's D18 point and S4 that the structure is shown, not edited.
8. **The editor's structure checks** (plan D8; implemented by stage E3).
   - **In the browser**, synchronously after every edit, with ADR-0010's reasons and the library's codes, every problem
     at once: `empty`, `invalid_id`, `reserved_name`, `duplicate_node`, `unknown_upstream`, `duplicate_upstream`,
     `upstream_count`, `several_downstream`, `cycle` (its nodes in flow order), `no_outlet`, `several_outlets`,
     `outlet_has_downstream` and `disconnected_node`. The inflow counts come from the `from` bounds of the schema. The
     edits never make `unknown_upstream`, `duplicate_upstream` or `several_downstream`; an opened file can, so they are
     checked too.
   - **Tied to the library**: a test runs a corpus of one-problem documents through the browser's module and through
     `RoutingNetwork.from_document`; the library's `details.reason` and `node_id` must be in the browser's list.
   - **The library confirms**: once the fields and the structure show no problem and the files are present,
     `route schematic` runs 300 ms after the last change; its error marks its node with the Polish text of its reason.

## Consequences

- **Consumers** (HUB-5.2; Hydrolog owns the document and the change is additive). Hydrograf keeps writing `/1`
  hand-offs without the fields and is unaffected; its test against the schema keeps passing. Retman recognises the
  file by the exact `schema` string, which does not change; it reads the fields once its release set takes a Hydrolog
  with them. A Hydrolog older than this decision refuses a document with the new fields (`unknown_field`), as every
  Hydrolog before ADR-0012 refused `watershed`; older documents read as before everywhere. A hand-off written by Sieć
  may carry the fields once Sieć keeps them; only Hydrolog reads such hand-offs today. No other project has to change.
- **Python API changes.** `hydrolog.operations.route_schematic(...)` returns an `OperationOutput` (its `result` is the
  `RouteSchematicResult` as before, its `notices` the layout's notices) instead of the bare `RouteSchematicResult`. A
  node type of another package that overrides `Node.read_entry` or `Node.build` follows the new signatures
  (`NodeEntry`). Code that reads `Line.row` handles `None`. The envelope of `route schematic` changes only by the
  notice and the `layout` field.
- No catalog option changes, so `AGENTS.md` and `llms.txt` stay as they are. The result `hydrolog-route-network/1`
  does not change.
- **The GUI does not keep positions or descriptions yet.** Nothing visible changes in Sieć: its forms leave the two
  fields out (they are not parameters), and a document with them opens and computes as without them, but Sieć drops
  them from what it sends and saves until the canvas (E2) and the editing (E3).
- A given picture may cross itself and the computed one never does; „Uporządkuj” (stage E2) restores the computed
  picture.
- ADR-0013's statement that the picture depends on the tree and the areas only now holds for the computed layout.

## Alternatives considered

- **A `hydrolog-network/2`:** it would break Retman's recognition (the exact `schema`) and Hydrograf's payload for a
  change that alters no meaning (the author's decision 2).
- **A reader that ignores unknown fields:** an older Hydrolog would then read the new documents, but a misspelt field
  would pass silently.
- **Free placement** (fractional positions): another edge rule would be needed, the computed picture could no longer be
  stored exactly, and the keys would move a node by an arbitrary step (the author's decision 1).
- **Stored routes** (the bends of each edge in the document): rule D gives every edge from its two ends, so stored
  routes would repeat the positions and could disagree with them.
- **A one-bend rule** for the edges of a given picture: from the computed positions it differs on 4 % of the edges and
  breaks the check of the picture (crossings, an edge through a node) in 31 % of the trees, so a stored computed
  picture would not be drawn as computed.
- **A diagram library for the canvas** (JointJS, Drawflow; React Flow and Svelte Flow need their frameworks and a
  bundler): a second visual language beside Nogat's tokens, built for the mouse, generic ports where a node has one
  downstream link, and bare imports that `script-src 'self'` refuses without an import map; renderers on a `<canvas>`
  (Cytoscape.js) have no element per node to focus, name or test.
