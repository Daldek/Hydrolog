"""The routing formulas, each declared by a spec (Nogat CMP-2.1, ADR-0061).

The schemes that route a hydrograph on a given grid, and the normal flow of a channel
section that Muskingum-Cunge takes its celerity from, each beside its
``FormulaSpec``: the routing elements of :mod:`hydrolog.routing` choose the grid (the
sub-reaches, the sub-steps, the time axis, ADR-0008) and compute through them.

* :mod:`~hydrolog.routing.formulas.muskingum` -- ``muskingum``, the Muskingum scheme
  through equal sub-reaches;
* :mod:`~hydrolog.routing.formulas.cascade` -- ``linear_reservoir_cascade``, the exact
  response of a cascade of linear reservoirs to an inflow linear between ordinates;
* :mod:`~hydrolog.routing.formulas.lag` -- ``lag``, the translation of a hydrograph;
* :mod:`~hydrolog.routing.formulas.manning` -- ``manning_normal_flow``, the normal flow
  of a prismatic channel and its kinematic celerity;
* :mod:`~hydrolog.routing.formulas.cunge` -- ``muskingum_cunge``, Muskingum-Cunge with
  constant coefficients on equal distance steps;
* :mod:`~hydrolog.routing.formulas.level_pool` -- ``level_pool``, storage indication
  (the modified Puls method) through equal pools of a storage-outflow table.
"""
