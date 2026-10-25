# 0013. The schematic of a network: a metro-style map that Hydrolog computes

- Status: accepted
- Date: 2026-10-25
- Builds on: [ADR-0012](0012-network-objects-rainfall-and-runoff.md) (`describe()` and `NetworkResult` carry the
  values that a drawing shows), [ADR-0010](0010-route-network-document-and-output-directory.md) (`route network`)

## Context

[ADR-0012](0012-network-objects-rainfall-and-runoff.md) made every part of a network report the values that it used
and left "a schematic of the network with the values of the calculation (a Beck-map style drawing)" to a later
decision. Hydrograf will show the picture next to its map, a report will print it and an agent will be asked for it.
If every consumer lays the network out for itself the pictures differ, and the one on the screen is not the one in
the report. The layout is therefore computed once, in the library, and published as a document that any program can
draw; the library draws it as SVG without a new dependency.

## Decision

- **The document `hydrolog-network-schematic/1`** (JSON-native, JSON Schema `hydrolog-network-schematic-1.schema.json`):
  `schema`, `name`, `outlet`, `timestep_min`, `has_result`, `grid` (`width`, `height` in grid units), `lines`, `nodes`
  and `edges`. A node has `id`, `type`, `x`, `y` (grid units; `x` grows downstream, to the right, `y` downwards, as on
  a screen), `line`, `label` (`text` and `side`, one of the eight compass points around the node) and `parameters`
  (`describe()`: `name`, `value`, `unit`, `source`); with a result also `peak_m3s`, `time_to_peak_min`, `volume_m3`
  and `notices`, which are the values of `NetworkResult` and nothing else, and the `parameters` that the run used. An
  edge has `from`, `to`, `line` and `points`, the corners of an octilinear polyline from the place of one node to the
  place of the other. A line is the main stem (`role` `main`) or a tributary that names the node it flows into
  (`joins`). Unknown fields are allowed and a new optional one keeps the version (AGI-4.1).
- **The layout** (`hydrolog.routing._layout`, a function of the tree and the areas, never of a result, so one network
  has one picture, and of nothing else, so the order of the nodes in a document changes nothing):
  - the **main stem** is a straight horizontal line from the outlet up through the inflow that drains the largest
    area (the sum of the `watershed.area_km2` of its headwaters, when every headwater has one) or else has the most
    nodes, ties to the smaller id; or through the nodes that the caller declares (`main_stem`, one path to the outlet,
    `unknown_node` and `main_stem_not_a_path` otherwise), continuing above the farthest of them by the same rule;
  - every other inflow starts a **tributary**, a straight line of the same kind; a tributary joins the node below it
    at **45 degrees**, from the row above or below the line it joins, after a vertical leg of **90 degrees** when it
    lies further out. On the main stem the tributaries take the **sides alternately**, the first above; a tributary
    of a tributary lies on the side that points away from its parent;
  - nodes are on the integer grid, **one unit apart** along a line, and tributaries are drawn headwaters first, each on
    the row nearest to its parent that is free, so a tributary downstream passes outside the ones upstream of it and
    **no two edges cross or touch** except at a node (a test of the cells of the picture, independent of the layout,
    checks random trees of every shape, nodes with up to twelve inflows included);
  - a node takes two joins on the main stem (one on each side) and one on a tributary; further lines join the line
    just before the node, at *taps*, and run along it into the node: the stretch before such a node is longer, and the
    edges that join at taps share their last stretch with the line and with each other. This is the only overlap the
    picture has, it says so in the document description, and it is what a bundle of lines is on a metro map;
  - the label of a node goes to the first of the eight compass points where it lies on no line, no other node and no
    other label (a label is at most one unit wide and four tenths of a unit high).
- **API.** `RoutingNetwork.schematic(result=None, *, main_stem=None)` returns the document (a result of another
  network is `result_mismatch`); `hydrolog.routing.schematic.schematic_svg(document)` draws a document and nothing
  else. A consumer that draws it itself needs the document alone: the colour of a line, the symbol of a kind of node
  and the text of a label are the consumer's.
- **SVG** (`hydrolog.routing._svg`, standard library only): lines in the colour of their line (the main stem blue, drawn
  last so that a merge shows its colour), a symbol for each kind of node (a diamond for a subcatchment, a ring for a
  reach, a box for a reservoir, a double ring for a junction, a target for the outlet), the id of the node and, with a
  result, `Qp` [m3/s], `tp` [min] and `V` [m3]; a mark on a node that has a warning; the parameters and the notices of
  a node are the text that a viewer shows over it; a legend. The text is language-neutral (ids, symbols, units, the
  names of the kinds as the document has them) and the same on every machine. The scale is chosen from the labels; an
  id longer than 16 characters is wrapped at its separators.
- **`route network --schematic FILE`** (catalog options `schematic`, an output file, and `main_stem`, a list of ids that
  applies only with `schematic`) writes the SVG and returns the document as `result.schematic`; the file follows the
  rules of every file a command writes: planned and refused before anything is computed (`output_exists`,
  `duplicate_output_name` against a table of `output_dir`, never an input file), replaced only with `--force`, written
  through a temporary file beside it, listed in `result.files`, and `--check` plans it together with the tables. The
  schematic shows every node whatever `nodes` selects, and its size does not count for the `large_result` notice. The
  human summary names its size and does not print the document.

## Consequences

- Hydrograf draws the same picture as the report: it reads `RoutingNetwork.schematic(result)` and draws the document,
  or calls `schematic_svg`; a change of the layout changes the picture for every consumer at once, and is a change of
  a documented format ([INTEGRATION.md](../INTEGRATION.md)).
- The picture is a drawing of a tree. Bifurcations are refused by the network (ADR-0010), so every valid network has
  one; the document is `/1` and a network that is not a tree would need the schema to grow, not to change.
- The labels carry up to four lines, so the unit is large (about 140 px with a result): the SVG is a picture to scale,
  not a thumbnail.
- The guide names the new option in one place; `AGENTS.md` is 16,277 of 16,384 bytes (it was 16,264).
- Not done: a layout that bends a long line at 45 degrees to save width, colours chosen so that neighbours differ, and
  labels with leader lines for the case where no place is clear (the label then takes the place that lies on the
  fewest lines).
