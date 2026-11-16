"""Networks to draw: a random tree of flow made into the nodes of a routing network."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BlockHietogram
from hydrolog.routing import (
    Channel,
    CurveNumberRunoff,
    DesignStorm,
    Hydrograph,
    Junction,
    LagReach,
    Node,
    Outlet,
    RoutingNetwork,
    Subcatchment,
)

STEP_MIN = 10.0


def watershed(area_km2: float) -> WatershedParameters:
    """A watershed of the given area with the rest of the fields of a small one."""
    return WatershedParameters(
        area_km2=area_km2,
        perimeter_km=4.5 * area_km2**0.5,
        length_km=1.2 * area_km2**0.5,
        elevation_min_m=210.0,
        elevation_max_m=330.0,
        cn=75,
    )


def headwater(node_id: str, area_km2: float | None = None) -> Subcatchment:
    """A subcatchment: given its hydrograph, or making it from a watershed."""
    if area_km2 is None:
        return Subcatchment(
            node_id, Hydrograph.from_step([0.0, 6.0, 2.0, 0.5, 0.0], STEP_MIN)
        )
    return Subcatchment(
        node_id,
        watershed=watershed(area_km2),
        runoff=CurveNumberRunoff(tc_min=60.0),
        rainfall=DesignStorm(30.0, 60.0, BlockHietogram()),
    )


def network_of(
    root: str,
    inflows: Mapping[str, Sequence[str]],
    areas: Mapping[str, float | None] | None = None,
    *,
    name: str | None = None,
) -> RoutingNetwork:
    """Make a routing network of a tree: ``root`` flows into an outlet called ``END``.

    A node that nothing flows into is a subcatchment (given its hydrograph, or making
    it when ``areas`` gives it an area), a node with one inflow a channel that lags by
    20 min and a node with more a junction.
    """

    def make(node_id: str) -> Node:
        above = [make(up) for up in inflows[node_id]]
        if not above:
            area = None if areas is None else areas.get(node_id)
            return headwater(node_id, area)
        if len(above) == 1:
            return Channel(node_id, LagReach(lag_min=20.0), inflow=above[0])
        return Junction(node_id, inflows=above)

    return RoutingNetwork(
        Outlet("END", inflow=make(root)), name=name, timestep_min=STEP_MIN
    )
