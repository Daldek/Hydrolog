"""Lumped hydrologic flood routing (ADR-0007).

The package routes a discharge hydrograph through a reach, a reservoir or a network
with storage-based methods. It computes discharge only: water levels, inundation,
backwater and structures are hydraulics and stay with Hydraulik, HEC-RAS and IMGW HD.
Time is in minutes and discharge in m3/s.

* :class:`Hydrograph` -- the discharge table every model takes and gives;
* :class:`Reach` -- the base class of the routing elements; :meth:`Reach.route`
  returns a :class:`RoutingResult` (outflow, storage at both ends, volume balance,
  notices);
* :class:`LagReach` -- lag routing.

The recurrences shared with the Clark unit hydrograph are in
``hydrolog.routing._kernels``.

Examples
--------
>>> from hydrolog.routing import Hydrograph, LagReach
>>> inflow = Hydrograph.from_step([0.0, 10.0, 40.0, 20.0, 0.0], timestep_min=30.0)
>>> LagReach(lag_min=60.0).route(inflow).outflow.time_to_peak_min
120.0
"""

from __future__ import annotations

from hydrolog.routing.hydrograph import Hydrograph
from hydrolog.routing.lag import LagReach
from hydrolog.routing.reach import Reach, RoutingNotice, RoutingResult

__all__ = ["Hydrograph", "LagReach", "Reach", "RoutingNotice", "RoutingResult"]
