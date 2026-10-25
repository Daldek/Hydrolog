"""Lumped hydrologic flood routing (ADR-0007).

The package routes a discharge hydrograph through a reach, a reservoir or a network
with storage-based methods. It computes discharge only: water levels, inundation,
backwater and structures are hydraulics and stay with Hydraulik, HEC-RAS and IMGW HD.
Time is in minutes and discharge in m3/s.

* :class:`Hydrograph` -- the discharge table every model takes and gives;
* :class:`Reach` -- the base class of the routing elements; :meth:`Reach.route`
  returns a :class:`RoutingResult` (outflow, storage at both ends, volume balance,
  notices);
* :class:`LagReach` -- lag routing;
* :class:`MuskingumReach` -- the Muskingum method, with sub-reaches inside the window of
  non-negative weights;
* :class:`MuskingumCungeReach` -- Muskingum-Cunge with constant coefficients (the NRCS
  form), from the celerity and top width or from a channel section
  (:class:`TrapezoidalSection`, Manning's equation);
* :class:`CascadeReach` -- a cascade of ``n`` linear reservoirs (Nash, Kalinin-Milyukov)
  with the exact kernel for a piecewise-linear inflow (:func:`cascade_weights`);
* :class:`LevelPoolReach` -- a reservoir or a reach with a storage-outflow table, by
  storage indication (the modified Puls method; :func:`timestep_limit_min`);
* :class:`RoutingNetwork` -- the elements above composed over a river network, a
  directed acyclic graph of :class:`Node` objects that link by reference
  (:class:`Subcatchment` brings a hydrograph, :class:`Channel` routes through a
  :class:`Reach`, :class:`Reservoir` through a level pool, :class:`Junction` adds,
  :class:`Outlet` ends the network); :meth:`RoutingNetwork.route` gives a
  :class:`NetworkResult`, the hydrograph, the figures and the parameters
  (:class:`Parameter`) of every node.

A new kind of node and a new method of a reach are classes that are registered in
:data:`NODE_TYPES` and :data:`REACH_METHODS`, which is how a document names them
(ADR-0012). The recurrences shared with the Clark unit hydrograph are in
``hydrolog.routing._kernels``.

Examples
--------
>>> from hydrolog.routing import Hydrograph, LagReach
>>> inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], timestep_min=30.0)
>>> LagReach(lag_min=60.0).route(inflow).outflow.time_to_peak_min
120.0
"""

from __future__ import annotations

from hydrolog.routing.cascade import CascadeReach, cascade_weights
from hydrolog.routing.cunge import MuskingumCungeReach
from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.lag import LagReach
from hydrolog.routing.level_pool import LevelPoolReach, timestep_limit_min
from hydrolog.routing.muskingum import MuskingumReach
from hydrolog.routing.network import (
    NODE_TYPES,
    Axis,
    Channel,
    Context,
    Junction,
    NetworkResult,
    Node,
    NodeOutput,
    NodeSummary,
    Outlet,
    Reservoir,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.parameters import Parameter
from hydrolog.routing.reach import (
    REACH_METHODS,
    Reach,
    RoutingNotice,
    RoutingResult,
)
from hydrolog.routing.sections import FlowState, TrapezoidalSection

__all__ = [
    "NODE_TYPES",
    "REACH_METHODS",
    "Axis",
    "CascadeReach",
    "Channel",
    "Context",
    "FlowState",
    "Hydrograph",
    "Junction",
    "LagReach",
    "LevelPoolReach",
    "MuskingumCungeReach",
    "MuskingumReach",
    "NetworkResult",
    "Node",
    "NodeOutput",
    "NodeSummary",
    "Outlet",
    "Parameter",
    "Reach",
    "Reservoir",
    "RoutingNetwork",
    "RoutingNotice",
    "RoutingResult",
    "Subcatchment",
    "TrapezoidalSection",
    "cascade_weights",
    "timestep_limit_min",
]
