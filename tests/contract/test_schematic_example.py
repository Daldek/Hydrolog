"""The picture in the documentation is what the code draws (ADR-0013).

``docs/images/network-schematic.svg`` is the schematic of the example network of
``docs/USAGE.md`` ("Networks of objects"), with the values of its run. The drawing is a
function of the network, so a change of the layout or of the SVG shows here: write the
file again from ``schematic_svg(network.schematic(network.route()))`` of the network
below.
"""

from pathlib import Path

from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BlockHietogram, EulerIIHietogram
from hydrolog.routing import (
    Channel,
    CurveNumberRunoff,
    DesignStorm,
    Junction,
    LagReach,
    MuskingumReach,
    Outlet,
    RainfallSeries,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.schematic import schematic_svg

PICTURE = (
    Path(__file__).resolve().parents[2] / "docs" / "images" / "network-schematic.svg"
)


def usage_network() -> RoutingNetwork:
    """The network of the USAGE example: three subcatchments, two junctions."""
    upper = WatershedParameters(
        area_km2=12.0,
        perimeter_km=18.0,
        length_km=6.0,
        elevation_min_m=210.0,
        elevation_max_m=330.0,
        cn=75,
    )
    lower = WatershedParameters(
        area_km2=5.0,
        perimeter_km=11.0,
        length_km=3.5,
        elevation_min_m=210.0,
        elevation_max_m=290.0,
        cn=70,
    )
    model = CurveNumberRunoff(tc_method="kirpich")
    storm = DesignStorm(45.0, 60.0, EulerIIHietogram())
    record = RainfallSeries([0.0, 2.0, 5.0, 10.0, 12.0, 6.0, 3.0], timestep_min=5.0)
    a = Subcatchment("A", watershed=upper, runoff=model, rainfall=storm)
    b = Subcatchment("B", watershed=lower, runoff=model, rainfall=record)
    c = Subcatchment("C", watershed=lower, runoff=model)
    j1 = Junction("J1", inflows=[Channel("R_A", LagReach(lag_min=25.0), inflow=a), b])
    reach = Channel("R_J1", MuskingumReach(k_min=40.0, x=0.2), inflow=j1)
    j2 = Junction("J2", inflows=[reach, c])
    return RoutingNetwork(
        Outlet("OUT", inflow=j2), rainfall=DesignStorm(30.0, 60.0, BlockHietogram())
    )


def test_the_documented_picture_is_the_drawing_of_the_usage_network():
    network = usage_network()

    drawing = schematic_svg(network.schematic(network.route()))

    assert PICTURE.read_text(encoding="utf-8") == drawing
