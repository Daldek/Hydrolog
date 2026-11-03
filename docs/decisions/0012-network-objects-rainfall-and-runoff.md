# 0012. Network objects, rainfall and runoff per subcatchment, and control points

- Status: accepted
- Date: 2026-10-25
- Amends: [ADR-0010](0010-route-network-document-and-output-directory.md) (the nodes of `RoutingNetwork`)

## Context

[ADR-0010](0010-route-network-document-and-output-directory.md) made `RoutingNetwork` from generic
`NetworkNode(kind=...)` records that name their inflows by id, and every subcatchment was given its hydrograph.
The author set four binding requirements for what Hydrograf will do with it: the rainfall belongs to each
subcatchment and is never one value of the network; the model that turns rain into discharge is replaceable (a
continuous model such as GR4J or HBV later, without touching the network); an application that lets the user pick
points on the streams must be able to map its picks to the network one to one; and a new kind of node, rainfall,
runoff model or reach method is added by a class, not by an edit of a central switch. A schematic of the network
with the values of the calculation (a Beck-map style drawing) will be built on top of the result, so every part
reports the values that it used.

## Decision

- **Typed nodes that link by reference.** `Subcatchment`, `Channel` (the `type` of a document stays `reach`),
  `Reservoir`, `Junction` and `Outlet` replace `NetworkNode`. A node holds the nodes that flow into it (`inflows`,
  the convention of `StreamSegment.upstream_ids`) and is immutable; `with_inflows` returns a copy, so a node can be
  made before the nodes above it. `RoutingNetwork(outlet)` is the network that the outlet reaches; a list of nodes
  is accepted too. An id still names every node, the result and the file of the node. The structure checks, their
  reasons and the rule of the evaluation order (headwaters first, the smallest id first among the ready nodes) are
  those of ADR-0010; `unknown_upstream` and `cycle` can only come from a document, which links by id.
- **Registries, no central switch.** Five registries map the name of a document to a class: `NODE_TYPES` (`type`),
  `REACH_METHODS` (`method`), `RAINFALL_KINDS` (`rainfall.kind`), `RUNOFF_MODELS` (`runoff.model`) and `HIETOGRAMS`
  (`rainfall.hietogram_type`). A new kind is a class that implements its protocol and a registry entry; the reader
  and the writer of `hydrolog-network/1` find classes by name and nothing else lists them. A registry can require
  methods (`Registry(needs=...)`: a rainfall and a runoff model must read and write their own document), and
  `name_of` finds the name of an object through its parents. A class that no registry names cannot be written:
  `details.reason` `unregistered`.
- **Two protocols.** `RainfallSource` (`kind`, `timestep_min`, `hyetograph(timestep_min, duration_min=None)`,
  `describe`, `to_document`, `from_document`) and `RunoffModel` (`model`, `validate(watershed)`,
  `hydrograph(rainfall, watershed, timestep_min)`, `describe`, `to_document`, `from_document`). The network needs the
  protocol and nothing else of the library: objects that are not registered work in a network. In the package:
  `DesignStorm` (a depth over a duration in the shape of a `Hietogram`; a duration other than its own is refused,
  `duration_mismatch`), `RainfallSeries` (the depth of every step; another step is refused, `timestep_mismatch`,
  never resampled) and `CurveNumberRunoff`, which is `HydrographGenerator` as a model with the options of
  `hydrograph generate` (a time of concentration given or computed from the watershed, the CN loss, the unit
  hydrograph); the hydrograph equals the generator's to the last ordinate.
- **A subcatchment is given its hydrograph or makes it.** `Subcatchment(id, hydrograph)` or
  `Subcatchment(id, watershed=, runoff=, rainfall=)`, one lumped, homogeneous area with no flow paths inside; the
  runoff model validates the watershed when the node is made. **The rainfall belongs to the subcatchment**: two of
  them can take it from different sources, and `RoutingNetwork(..., rainfall=)` is only a default for those that
  have none. Nothing assumes that it exists: a subcatchment with no rain of its own in a network that has none is
  `missing_field` (`field` `rainfall`).
- **One time step for a network.** `RoutingNetwork(..., timestep_min=)`, else the step of the given hydrographs and
  rainfall series (they must agree, `timestep_mismatch`), else 5 min (`DEFAULT_TIMESTEP_MIN`, that of `hydrograph
  generate`); every source starts at the same time and a generated hydrograph starts at 0 (`start_mismatch`).
  Nothing is resampled (ADR-0008).
- **Additive within `hydrolog-network/1`.** A document gains `timestep_min` and `rainfall` (the default) at its top
  and `watershed`, `runoff` and `rainfall` in a subcatchment; the fields are those of the classes (`rainfall`:
  `kind` `design` with `hietogram_type`, `total_mm`, `duration_min` and the arguments of the shape, or `series` with
  `depths_mm` and `timestep_min`; `runoff`: `model` `curve-number` with the options of `hydrograph generate`). An
  old document is read and answered as before, so the schema stays `/1`. The errors of an object inside a node name
  it in `details.field` (`rainfall.total_mm`).
- **Every part describes itself.** `describe()` of a node, a reach, a rainfall and a runoff model returns a list of
  `Parameter` (`name`, `value`, `unit`, `source`: `given`, `computed` or `default`) with the values that the
  calculation used, the derived ones too (the number of sub-reaches, the celerity, the time of concentration).
  `NetworkResult.nodes` carries them for every node with the peak, the time to peak, the volume and the `notices`;
  `NetworkResult.rainfall` the rain of each subcatchment that made its hydrograph. A warning of the library
  (a value outside the range of a formula) is a notice of the node that caused it, and `route network` begins every
  notice with the id of its node.
- **The network is written as it is read.** `RoutingNetwork.to_document()` returns the document, JSON-native, with
  the nodes in the order of evaluation and nothing that has its default: a document in that form is written back to
  the same text, any other one in that form once, and the network that is read from what was written routes to the
  last ordinate as the first did. Every node class writes its own fields (`document_fields`, next to
  `read_document`).
- **Control points** (`hydrolog.routing.points`). The application picks the outlet first, then points upstream of
  it; every point closes its *residual* area (the contributing area minus the areas of the points above it) and the
  stream between two points is a reach. `ControlPointNetwork(OutletPoint(id, subcatchment))` is valid and routes
  alone, and stays valid: each edit builds the immutable `RoutingNetwork` of the new state and keeps the state only
  if that works, so a refused edit changes nothing. The edits are `add_point(ControlPoint(id, subcatchment),
  downstream=, channel=)` (`upstream={id: channel}` for a point picked between two others),
  `update_subcatchment(id, subcatchment)`, `add_confluence(id, on_channel_of=, upstream_channel=,
  downstream_channel=)` and `remove_point(id, channel=None)`; `network()` and `route()` give the network and its
  result. A point and a confluence are a `Junction` that has their id (so `hydrographs[id]` is the discharge there)
  and adds the subcatchment and the outflow of the channel of every point that flows into it; the outlet is the
  junction `<id>_junction` and an `Outlet` with the id of the outlet point. A bare `Reach` is wrapped in a channel
  named `<id>_channel` after the point it leaves; a `Channel` is used as it is, without its inflows.
  - **Residual areas and channel parameters are the application's.** Hydrolog does not compute or check that areas
    add up, and never makes up a channel: a confluence takes both channels of the stream it splits. It checks
    topology (one outlet, no bifurcation, no cycle), ids and the time axis.
  - **A confluence exists to be shared.** The stream below it carries the water of both, so a nonlinear reach (a
    Muskingum-Cunge reach whose coefficients follow the inflow peak, a pond) is routed once for the sum; routed once
    for each stream, as a network without the confluence does, it gives another hydrograph. For a linear reach the
    two are the same. A confluence has no area (`not_a_point`) and is dropped when it joins fewer than two streams.
  - **Removing a point** takes its subcatchment and keeps the points above it. With nothing above it the point goes
    with its channel; with one stream above it the place above flows into the place below through the two channels in
    series (`channels(id)` lists them), or through the `channel` that the application gives for both; with two or
    more it stays as a confluence, because the streams still meet there and the channel below must carry them
    together (`channel` is then `not_applicable`). The outlet cannot be removed (`outlet_removal`) and a confluence
    that still joins two streams neither (`still_joins`).
  - **Refusals** are `InvalidParameterError` with `details.reason`: `unknown_point`, `duplicate_node` (ids of
    points, confluences, subcatchments and channels are the ids of nodes, equal without regard to case), `type`,
    `no_channel`, `not_upstream`, `not_a_point`, `no_inflow` (a point that would get no water), `outlet_removal`,
    `still_joins`, `not_applicable`, and the reasons of a network (`timestep_mismatch`, `missing_field`...).
  - **No document of its own.** The document of `network()` is the exchange format; a second one for the points
    would have no consumer.
- **`hydrolog.testing`** builds what a consumer writes for this: `watershed`, `curve_number_runoff`, `design_storm`,
  `rainfall_series` (each read by the real reader before it is returned), `subcatchment(..., watershed=, runoff=,
  rainfall=)`, `network_document(..., timestep_min=, rainfall=)` and a network of three subcatchments
  (`example_network_document`, `example_network`). The contract test runs `route network` on it.

## Consequences

- `NetworkNode` is gone (clean cutover, every caller migrated); a document that ADR-0010 accepted is read and
  routed as before, and `route network` reads the new fields with the errors of the catalog vocabulary. Its JSON
  Schema has a variant for a subcatchment that makes its hydrograph.
- A continuous model (GR4J, HBV), an areal rainfall (IMGWTools, radar, PMAXTP) or another kind of node is a class and
  a registry entry; the network and the document code do not change. A model that keeps a state between steps meets
  the lumped, one-step-per-network rule of ADR-0008 and is a later decision.
- A schematic of the network can be drawn from `NetworkResult` alone: the places (`order`, `inflows`), the values of
  every node (`parameters`, `peak_m3s`, `time_to_peak_min`, `volume_m3`) and what the calculation said (`notices`).
  Nothing about drawing is decided here.
- Hydrograf, which holds the stream network and the areas, builds the control points in Python, edits them as the
  user picks and reads `hydrographs[point_id]` and `nodes[...]` back; no file is involved ([INTEGRATION.md](../INTEGRATION.md)).
- The state of a `ControlPointNetwork` is rebuilt at every edit, in time linear in the number of nodes: for the
  hundreds of points that a catchment has, this is not noticeable.
