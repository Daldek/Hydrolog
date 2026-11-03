"""Tests of the control points: a network as an application picks it (ADR-0012).

The references are the nodes that the points stand for, built by hand: the network of
the points has the same document, and routes to the same last ordinate, as the network
of those nodes. The workflow of the application is the test: the outlet alone, points
on a stream, a tributary that joins it at a confluence, and a point taken away; every
state is a valid network that routes, and an edit that is refused changes nothing. The
one thing the confluence is for is a nonlinear reach: the stream below it carries the
water of both streams, and is routed once.
"""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BlockHietogram, EulerIIHietogram
from hydrolog.routing import (
    Channel,
    ControlPoint,
    ControlPointNetwork,
    CurveNumberRunoff,
    DesignStorm,
    Hydrograph,
    Junction,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    Outlet,
    OutletPoint,
    RainfallSeries,
    Reservoir,
    RoutingNetwork,
    Subcatchment,
)

OWN = [0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
LOW = [0.0, 2.0, 8.0, 5.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
UPPER = [0.0, 1.0, 4.0, 3.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
TRIB = [0.0, 3.0, 9.0, 6.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
CATCHMENT = WatershedParameters(
    area_km2=12.0,
    perimeter_km=18.0,
    length_km=6.0,
    elevation_min_m=210.0,
    elevation_max_m=330.0,
    cn=75,
)


def area(node_id, values):
    return Subcatchment(node_id, Hydrograph.from_step(values, 10.0))


def stream(**options):
    """OUT, with P1 above it (a lag) and P2 above P1 (a Muskingum reach)."""
    points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)), **options)
    points.add_point(
        ControlPoint("P1", area("P1_area", LOW)),
        downstream="OUT",
        channel=LagReach(lag_min=20.0),
    )
    points.add_point(
        ControlPoint("P2", area("P2_area", UPPER)),
        downstream="P1",
        channel=MuskingumReach(k_min=30.0, x=0.2),
    )
    return points


def stream_by_hand():
    """The nodes that ``stream()`` stands for."""
    p2 = Junction("P2", inflows=[area("P2_area", UPPER)])
    above = Channel("P2_channel", MuskingumReach(k_min=30.0, x=0.2), inflow=p2)
    p1 = Junction("P1", inflows=[area("P1_area", LOW), above])
    below = Channel("P1_channel", LagReach(lag_min=20.0), inflow=p1)
    out = Junction("OUT_junction", inflows=[area("OUT_area", OWN), below])
    return RoutingNetwork(Outlet("OUT", inflow=out))


def assert_same_network(points, network):
    """The network of the points is the given one: its document and its hydrographs."""
    mine = points.network() if isinstance(points, ControlPointNetwork) else points
    assert mine.to_document() == network.to_document()
    one, other = mine.route(), network.route()
    assert one.order == other.order
    for node_id in one.order:
        np.testing.assert_array_equal(
            one.hydrographs[node_id].discharge_m3s,
            other.hydrographs[node_id].discharge_m3s,
        )


def refused(edit):
    with pytest.raises(InvalidParameterError) as caught:
        edit()
    return caught.value


class TestTheOutletAlone:
    def test_it_is_a_network_that_routes(self):
        points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))

        result = points.route()

        assert result.outlet == "OUT" == points.outlet
        assert result.order == ("OUT_area", "OUT_junction", "OUT")
        np.testing.assert_array_equal(result.hydrographs["OUT"].discharge_m3s, OWN)
        assert points.ids == ("OUT",)
        assert points.kind("OUT") == "outlet"
        assert points.downstream("OUT") is None
        assert points.upstream("OUT") == () and points.channels("OUT") == ()

    def test_it_needs_water(self):
        error = refused(lambda: ControlPointNetwork(OutletPoint("OUT")))

        assert error.details["reason"] == "no_inflow"
        assert error.details["point_id"] == "OUT"

    def test_it_is_made_of_an_outlet_point(self):
        error = refused(
            lambda: ControlPointNetwork(ControlPoint("OUT", area("A", OWN)))
        )

        assert error.details["reason"] == "type" and error.details["field"] == "outlet"

    def test_the_rainfall_belongs_to_the_subcatchment_of_a_point(self):
        made = Subcatchment(
            "OUT_area",
            watershed=CATCHMENT,
            runoff=CurveNumberRunoff(tc_min=90.0),
            rainfall=DesignStorm(45.0, 60.0, EulerIIHietogram()),
        )

        points = ControlPointNetwork(OutletPoint("OUT", made))

        result = points.route()
        assert result.rainfall["OUT_area"].total_mm == 45.0
        assert result.hydrographs["OUT"].peak_discharge_m3s > 0.0


class TestPointsOnAStream:
    def test_they_are_the_nodes_that_they_stand_for(self):
        assert_same_network(stream(), stream_by_hand())

    def test_the_discharge_at_every_point_is_in_the_result(self):
        points = stream()

        result = points.route()

        np.testing.assert_array_equal(result.hydrographs["P2"].discharge_m3s, UPPER)
        routed = Channel(
            "c", MuskingumReach(k_min=30.0, x=0.2), inflow=area("a", UPPER)
        )
        at_p1 = (
            result.hydrographs["P1_area"].discharge_m3s
            + RoutingNetwork(Outlet("OUT", inflow=routed))
            .route()
            .hydrographs["c"]
            .discharge_m3s[: len(LOW)]
        )
        np.testing.assert_allclose(
            result.hydrographs["P1"].discharge_m3s[: len(LOW)], at_p1, rtol=1e-12
        )

    def test_what_the_network_knows_of_its_points(self):
        points = stream()

        assert points.ids == ("OUT", "P1", "P2")
        assert [points.kind(p) for p in points.ids] == ["outlet", "point", "point"]
        assert points.downstream("P2") == "P1" and points.downstream("P1") == "OUT"
        assert points.upstream("OUT") == ("P1",) and points.upstream("P2") == ()
        assert points.subcatchment("P2").id == "P2_area"
        assert [channel.id for channel in points.channels("P2")] == ["P2_channel"]
        assert "P1" in points and "Q" not in points

    def test_a_reach_is_wrapped_in_a_channel_named_after_the_point_it_leaves(self):
        channel = stream().channels("P1")[0]

        assert isinstance(channel, Channel) and channel.id == "P1_channel"
        assert isinstance(channel.reach, LagReach)

    def test_a_channel_keeps_its_id_and_loses_its_inflows(self):
        mine = Channel("river", LagReach(lag_min=20.0), inflow=area("elsewhere", OWN))
        points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))

        points.add_point(
            ControlPoint("P1", area("P1_area", LOW)), downstream="OUT", channel=mine
        )

        (kept,) = points.channels("P1")
        assert kept.id == "river" and kept.inflows == ()
        assert "elsewhere" not in points.network().order

    def test_a_reservoir_can_be_the_channel_between_two_points(self):
        pond = Reservoir(
            "pond",
            LevelPoolReach(
                storage_m3=[0.0, 30000.0, 90000.0, 180000.0],
                outflow_m3s=[0.0, 5.0, 20.0, 60.0],
            ),
        )
        points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))

        points.add_point(
            ControlPoint("P1", area("P1_area", LOW)), downstream="OUT", channel=pond
        )

        assert points.network().node("pond").kind == "reservoir"
        assert points.route().runs["pond"].model == "level-pool"

    def test_a_point_picked_between_two_others_takes_the_one_above(self):
        points = stream()

        points.add_point(
            ControlPoint("M", area("M_area", TRIB)),
            downstream="P1",
            channel=LagReach(lag_min=10.0),
            upstream={"P2": LagReach(lag_min=10.0)},
        )

        assert points.upstream("P1") == ("M",) and points.upstream("M") == ("P2",)
        assert points.downstream("P2") == "M"
        (channel,) = points.channels("P2")
        assert channel.reach.lag_min == 10.0
        by_hand = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=Junction(
                    "OUT_junction",
                    inflows=[
                        area("OUT_area", OWN),
                        Channel(
                            "P1_channel",
                            LagReach(lag_min=20.0),
                            inflow=Junction(
                                "P1",
                                inflows=[
                                    area("P1_area", LOW),
                                    Channel(
                                        "M_channel",
                                        LagReach(lag_min=10.0),
                                        inflow=Junction(
                                            "M",
                                            inflows=[
                                                area("M_area", TRIB),
                                                Channel(
                                                    "P2_channel",
                                                    LagReach(lag_min=10.0),
                                                    inflow=Junction(
                                                        "P2",
                                                        inflows=[
                                                            area("P2_area", UPPER)
                                                        ],
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        )
        assert_same_network(points, by_hand)

    def test_a_point_must_flow_into_the_place_it_is_to_leave(self):
        points = stream()

        error = refused(
            lambda: points.add_point(
                ControlPoint("M", area("M_area", TRIB)),
                downstream="OUT",
                channel=LagReach(lag_min=10.0),
                upstream={"P2": LagReach(lag_min=10.0)},
            )
        )

        assert error.details["reason"] == "not_upstream"
        assert error.details["point_id"] == "P2"

    def test_the_new_point_is_below_a_place_that_exists(self):
        error = refused(
            lambda: stream().add_point(
                ControlPoint("P3", area("P3_area", TRIB)),
                downstream="Q",
                channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "unknown_point"
        assert error.details["point_id"] == "Q"
        assert error.details["allowed"] == ["OUT", "P1", "P2"]

    def test_a_point_needs_water(self):
        error = refused(
            lambda: stream().add_point(
                ControlPoint("P3"), downstream="P2", channel=LagReach(lag_min=10.0)
            )
        )

        assert error.details["reason"] == "no_inflow"
        assert error.details["point_id"] == "P3"

    def test_the_outlet_is_not_added_as_a_point(self):
        error = refused(
            lambda: stream().add_point(
                OutletPoint("O2", area("O2_area", OWN)),
                downstream="OUT",
                channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "type"

    @pytest.mark.parametrize("channel", [None, "river", 25.0, ControlPoint("x", None)])
    def test_a_channel_is_a_channel_or_a_reach(self, channel):
        error = refused(
            lambda: stream().add_point(
                ControlPoint("P3", area("P3_area", TRIB)),
                downstream="P2",
                channel=channel,
            )
        )

        assert error.details["reason"] == "type" and error.details["field"] == "channel"


class TestWhatAnEditChanges:
    def test_the_area_that_is_left_to_a_point_is_the_applications_to_give(self):
        points = stream()
        before = points.route().hydrographs["OUT"].volume_m3

        points.update_subcatchment("P1", area("P1_area", [v / 2 for v in LOW]))

        after = points.route().hydrographs["OUT"].volume_m3
        assert points.subcatchment("P1").hydrograph.discharge_m3s[2] == 4.0
        assert after < before

    def test_a_point_that_has_points_above_it_may_have_no_area(self):
        points = stream()

        points.update_subcatchment("P1", None)

        assert points.subcatchment("P1") is None
        result = points.route()
        assert "P1_area" not in result.order
        assert result.nodes["P1"].inflows == ("P2_channel",)

    def test_a_point_that_has_none_above_it_keeps_its_area(self):
        points = stream()
        document = points.network().to_document()

        error = refused(lambda: points.update_subcatchment("P2", None))

        assert error.details["reason"] == "no_inflow"
        assert points.network().to_document() == document
        assert points.subcatchment("P2").id == "P2_area"

    def test_the_edits_are_the_state_that_the_application_sees(self):
        points = stream()
        first = points.network()

        points.update_subcatchment("P2", area("P2_area", TRIB))

        assert points.network() is not first
        assert first.route().hydrographs["P2"].peak_discharge_m3s == max(UPPER)
        assert points.network().route().hydrographs["P2"].peak_discharge_m3s == max(
            TRIB
        )

    def test_an_id_that_is_used_is_refused_with_any_case(self):
        points = stream()
        document = points.network().to_document()

        error = refused(
            lambda: points.add_point(
                ControlPoint("p1", area("p1_area", TRIB)),
                downstream="P2",
                channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "duplicate_node"
        assert points.network().to_document() == document

    def test_a_subcatchment_that_takes_the_id_of_a_node_is_refused(self):
        points = stream()

        error = refused(
            lambda: points.add_point(
                ControlPoint("P3", area("P2", TRIB)),
                downstream="P2",
                channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "duplicate_node"
        assert points.ids == ("OUT", "P1", "P2")

    def test_a_subcatchment_that_cannot_be_routed_is_refused_and_changes_nothing(self):
        points = stream()
        document = points.network().to_document()
        coarse = Subcatchment("P3_area", Hydrograph.from_step(TRIB, 15.0))

        error = refused(
            lambda: points.add_point(
                ControlPoint("P3", coarse),
                downstream="P2",
                channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "timestep_mismatch"
        assert points.network().to_document() == document
        assert points.ids == ("OUT", "P1", "P2")

    def test_a_rain_that_is_nowhere_is_refused_when_the_subcatchment_is_added(self):
        points = stream()
        dry = Subcatchment(
            "P3_area", watershed=CATCHMENT, runoff=CurveNumberRunoff(tc_min=60.0)
        )

        error = refused(
            lambda: points.add_point(
                ControlPoint("P3", dry), downstream="P2", channel=LagReach(lag_min=10.0)
            )
        )

        assert error.details["reason"] == "missing_field"
        assert error.details["field"] == "rainfall"

    def test_the_default_rain_of_the_network_is_for_the_subcatchments_that_have_none(
        self,
    ):
        storm = DesignStorm(30.0, 60.0, BlockHietogram())
        dry = Subcatchment(
            "P1_area", watershed=CATCHMENT, runoff=CurveNumberRunoff(tc_min=60.0)
        )
        wet = Subcatchment(
            "P2_area",
            watershed=CATCHMENT,
            runoff=CurveNumberRunoff(tc_min=60.0),
            rainfall=RainfallSeries([0.0, 4.0, 11.0, 6.0, 1.0, 0.0], timestep_min=5.0),
        )
        points = ControlPointNetwork(
            OutletPoint(
                "OUT", Subcatchment("OUT_area", Hydrograph.from_step(OWN, 5.0))
            ),
            rainfall=storm,
            timestep_min=5.0,
        )

        points.add_point(
            ControlPoint("P1", dry), downstream="OUT", channel=LagReach(lag_min=20.0)
        )
        points.add_point(
            ControlPoint("P2", wet), downstream="P1", channel=LagReach(lag_min=20.0)
        )

        # the series and the storm are both cut at the step of the network
        assert points.network().timestep_min == 5.0
        result = points.route()
        assert result.rainfall["P1_area"].total_mm == 30.0
        assert result.rainfall["P2_area"].total_mm == 22.0


def with_confluence(shared):
    """OUT <- P1 <- C1 <- {P2, T}: the stream below C1 carries both streams."""
    points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))
    points.add_point(
        ControlPoint("P1", area("P1_area", LOW)),
        downstream="OUT",
        channel=LagReach(lag_min=20.0),
    )
    points.add_point(
        ControlPoint("P2", area("P2_area", UPPER)), downstream="P1", channel=shared
    )
    points.add_confluence(
        "C1",
        on_channel_of="P2",
        upstream_channel=LagReach(lag_min=10.0),
        downstream_channel=shared,
    )
    points.add_point(
        ControlPoint("T", area("T_area", TRIB)),
        downstream="C1",
        channel=LagReach(lag_min=10.0),
    )
    return points


def without_confluence(shared):
    """The same streams, each through its own copy of the shared one: by hand."""

    def branch(name, values):
        point = Junction(name, inflows=[area(f"{name}_area", values)])
        lag = Channel(f"{name}_lag", LagReach(lag_min=10.0), inflow=point)
        return Channel(f"{name}_shared", shared, inflow=lag)

    p1 = Junction(
        "P1",
        inflows=[area("P1_area", LOW), branch("P2", UPPER), branch("T", TRIB)],
    )
    below = Channel("P1_channel", LagReach(lag_min=20.0), inflow=p1)
    out = Junction("OUT_junction", inflows=[area("OUT_area", OWN), below])
    return RoutingNetwork(Outlet("OUT", inflow=out))


def routed_together(*hydrographs):
    """The discharge of hydrographs that meet: the sum, shorter ones held at the end."""
    size = max(len(hydrograph) for hydrograph in hydrographs)
    return sum(
        np.pad(hydrograph.discharge_m3s, (0, size - len(hydrograph)), mode="edge")
        for hydrograph in hydrographs
    )


class TestAConfluence:
    def test_it_splits_the_channel_of_the_point_that_it_is_on(self):
        points = with_confluence(MuskingumReach(k_min=30.0, x=0.2))

        assert points.ids == ("OUT", "P1", "P2", "C1", "T")
        assert points.kind("C1") == "confluence"
        assert points.downstream("P2") == "C1" and points.downstream("C1") == "P1"
        assert points.upstream("C1") == ("P2", "T")
        assert [c.id for c in points.channels("P2")] == ["P2_channel"]
        assert [c.id for c in points.channels("C1")] == ["C1_channel"]
        assert points.channels("P2")[0].reach.lag_min == 10.0

    def test_it_adds_the_streams_that_join_there_and_the_stream_below_carries_both(
        self,
    ):
        shared = MuskingumReach(k_min=30.0, x=0.2)
        points = with_confluence(shared)

        result = points.route()

        np.testing.assert_allclose(
            result.hydrographs["C1"].discharge_m3s,
            (
                result.hydrographs["P2_channel"].discharge_m3s
                + result.hydrographs["T_channel"].discharge_m3s
            ),
            rtol=1e-12,
        )
        assert result.nodes["C1_channel"].inflows == ("C1",)
        assert result.nodes["P1"].inflows == ("P1_area", "C1_channel")

    def test_a_linear_reach_is_the_same_with_and_without_it(self):
        shared = MuskingumReach(k_min=30.0, x=0.2)

        with_it = with_confluence(shared).route().hydrographs["C1_channel"]
        copies = without_confluence(shared).route().hydrographs
        without = routed_together(copies["P2_shared"], copies["T_shared"])

        size = min(len(with_it), len(without))
        np.testing.assert_allclose(
            with_it.discharge_m3s[:size], without[:size], rtol=1e-9, atol=1e-9
        )

    @pytest.mark.parametrize(
        "shared",
        [
            MuskingumCungeReach(
                length_km=6.0,
                slope_m_per_m=0.001,
                celerity_m_per_s=1.0,
                top_width_m=25.0,
            ),
            LevelPoolReach(
                storage_m3=[0.0, 3000.0, 12000.0, 40000.0, 100000.0],
                outflow_m3s=[0.0, 0.5, 3.0, 9.0, 20.0],
            ),
        ],
        ids=["muskingum-cunge", "level-pool"],
    )
    def test_a_nonlinear_reach_is_routed_once_for_both_streams_with_it(self, shared):
        with_it = with_confluence(shared).route().hydrographs["C1_channel"]
        copies = without_confluence(shared).route().hydrographs
        without = routed_together(copies["P2_shared"], copies["T_shared"])

        # the stream below the confluence is one reach that routes the sum of the two;
        # without the confluence each stream is routed through a copy of it
        assert abs(with_it.peak_discharge_m3s - without.max()) > 0.02 * without.max()

    def test_it_is_a_place_on_a_channel_and_not_on_the_outlet(self):
        error = refused(
            lambda: stream().add_confluence(
                "C1",
                on_channel_of="OUT",
                upstream_channel=LagReach(lag_min=10.0),
                downstream_channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "no_channel"

    def test_it_has_no_area_of_its_own(self):
        points = with_confluence(LagReach(lag_min=20.0))

        error = refused(lambda: points.update_subcatchment("C1", area("C1_area", OWN)))

        assert error.details["reason"] == "not_a_point"

    def test_its_id_is_an_id_of_the_network(self):
        points = stream()

        error = refused(
            lambda: points.add_confluence(
                "p2",
                on_channel_of="P2",
                upstream_channel=LagReach(lag_min=10.0),
                downstream_channel=LagReach(lag_min=10.0),
            )
        )

        assert error.details["reason"] == "duplicate_node"
        assert points.ids == ("OUT", "P1", "P2")


class TestRemovingAPoint:
    def test_a_point_that_has_nothing_above_it_goes_with_its_channel(self):
        points = stream()
        before = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))
        before.add_point(
            ControlPoint("P1", area("P1_area", LOW)),
            downstream="OUT",
            channel=LagReach(lag_min=20.0),
        )

        points.remove_point("P2")

        assert points.ids == ("OUT", "P1")
        assert_same_network(points, before.network())

    def test_a_point_with_one_stream_above_it_is_dropped_channels_stay_in_series(self):
        points = stream()

        points.remove_point("P1")

        assert points.ids == ("OUT", "P2") and points.downstream("P2") == "OUT"
        assert [c.id for c in points.channels("P2")] == ["P2_channel", "P1_channel"]
        by_hand = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=Junction(
                    "OUT_junction",
                    inflows=[
                        area("OUT_area", OWN),
                        Channel(
                            "P1_channel",
                            LagReach(lag_min=20.0),
                            inflow=Channel(
                                "P2_channel",
                                MuskingumReach(k_min=30.0, x=0.2),
                                inflow=Junction("P2", inflows=[area("P2_area", UPPER)]),
                            ),
                        ),
                    ],
                ),
            )
        )
        assert_same_network(points, by_hand)

    def test_the_application_may_give_the_channel_that_replaces_both(self):
        points = stream()
        merged = MuskingumReach(k_min=50.0, x=0.2)

        points.remove_point("P1", channel=merged)

        (channel,) = points.channels("P2")
        assert channel.id == "P2_channel" and channel.reach is merged
        assert "P1_channel" not in points.network().order

    def test_a_point_with_two_streams_above_it_stays_as_the_confluence_of_both(self):
        points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))
        points.add_point(
            ControlPoint("P1", area("P1_area", LOW)),
            downstream="OUT",
            channel=LagReach(lag_min=20.0),
        )
        for name, values in (("P2", UPPER), ("T", TRIB)):
            points.add_point(
                ControlPoint(name, area(f"{name}_area", values)),
                downstream="P1",
                channel=LagReach(lag_min=10.0),
            )
        full = points.route().hydrographs["P1"].discharge_m3s

        points.remove_point("P1")

        assert points.ids == ("OUT", "P1", "P2", "T")
        assert points.kind("P1") == "confluence" and points.subcatchment("P1") is None
        assert points.upstream("P1") == ("P2", "T")
        left = points.route().hydrographs["P1"].discharge_m3s
        # the area of the point went with it; the streams that met there still do
        assert len(left) == len(full)
        own = np.zeros(len(full))
        own[: len(LOW)] = LOW
        np.testing.assert_allclose(full - left, own, atol=1e-12)

    def test_a_channel_is_not_for_a_removal_that_merges_none(self):
        points = ControlPointNetwork(OutletPoint("OUT", area("OUT_area", OWN)))
        points.add_point(
            ControlPoint("P1", area("P1_area", LOW)),
            downstream="OUT",
            channel=LagReach(lag_min=20.0),
        )
        points.add_point(
            ControlPoint("P2", area("P2_area", UPPER)),
            downstream="P1",
            channel=LagReach(lag_min=10.0),
        )
        document = points.network().to_document()

        error = refused(
            lambda: points.remove_point("P2", channel=LagReach(lag_min=5.0))
        )

        assert error.details["reason"] == "not_applicable"
        assert error.details["field"] == "channel"
        assert points.network().to_document() == document

    def test_the_last_stream_but_one_takes_the_confluence_with_it(self):
        points = with_confluence(MuskingumReach(k_min=30.0, x=0.2))

        points.remove_point("T")

        assert points.ids == ("OUT", "P1", "P2")
        assert points.downstream("P2") == "P1"
        assert [c.id for c in points.channels("P2")] == ["P2_channel", "C1_channel"]
        assert points.route().hydrographs["P1"].peak_discharge_m3s > 0.0

    def test_the_channel_may_replace_the_two_of_a_confluence_that_goes(self):
        points = with_confluence(MuskingumReach(k_min=30.0, x=0.2))
        merged = MuskingumReach(k_min=45.0, x=0.2)

        points.remove_point("P2", channel=merged)

        assert points.ids == ("OUT", "P1", "T")
        (channel,) = points.channels("T")
        assert channel.reach is merged and channel.id == "T_channel"

    def test_a_confluence_that_still_joins_two_streams_stays(self):
        points = with_confluence(LagReach(lag_min=20.0))
        document = points.network().to_document()

        error = refused(lambda: points.remove_point("C1"))

        assert error.details["reason"] == "still_joins"
        assert points.network().to_document() == document

    def test_a_confluence_with_one_stream_is_taken_away_like_a_point(self):
        points = stream()
        document = points.network().to_document()
        points.add_confluence(
            "C1",
            on_channel_of="P2",
            upstream_channel=LagReach(lag_min=10.0),
            downstream_channel=LagReach(lag_min=10.0),
        )

        points.remove_point("C1")

        assert points.ids == ("OUT", "P1", "P2")
        assert [c.id for c in points.channels("P2")] == ["P2_channel", "C1_channel"]
        assert points.network().to_document() != document

    def test_a_point_that_the_last_one_above_it_leaves_without_water_is_refused(self):
        points = stream()
        points.update_subcatchment("P1", None)
        document = points.network().to_document()

        error = refused(lambda: points.remove_point("P2"))

        assert error.details["reason"] == "no_inflow"
        assert error.details["point_id"] == "P1"
        assert points.network().to_document() == document

    def test_the_outlet_stays(self):
        error = refused(lambda: stream().remove_point("OUT"))

        assert error.details["reason"] == "outlet_removal"

    def test_a_point_that_is_not_there_is_refused(self):
        error = refused(lambda: stream().remove_point("Q"))

        assert error.details["reason"] == "unknown_point"


class TestEveryStateIsANetwork:
    def test_the_workflow_of_the_application_routes_at_every_step(self):
        shared = MuskingumCungeReach(
            length_km=6.0, slope_m_per_m=0.001, celerity_m_per_s=1.0, top_width_m=25.0
        )
        points = ControlPointNetwork(
            OutletPoint("OUT", area("OUT_area", OWN)), name="W"
        )
        states = [points.network()]
        points.add_point(
            ControlPoint("P1", area("P1_area", LOW)),
            downstream="OUT",
            channel=LagReach(lag_min=20.0),
        )
        states.append(points.network())
        points.add_point(
            ControlPoint("P2", area("P2_area", UPPER)), downstream="P1", channel=shared
        )
        states.append(points.network())
        points.add_confluence(
            "C1",
            on_channel_of="P2",
            upstream_channel=LagReach(lag_min=10.0),
            downstream_channel=shared,
        )
        points.add_point(
            ControlPoint("T", area("T_area", TRIB)),
            downstream="C1",
            channel=LagReach(lag_min=10.0),
        )
        states.append(points.network())
        points.remove_point("P2")
        states.append(points.network())

        for network in states:
            result = network.route()
            again = RoutingNetwork.from_document(network.to_document()).route()
            assert result.name == "W" and result.outlet == "OUT"
            for node_id in result.order:
                np.testing.assert_array_equal(
                    result.hydrographs[node_id].discharge_m3s,
                    again.hydrographs[node_id].discharge_m3s,
                )
        assert [len(network.order) for network in states] == [3, 6, 9, 14, 10]

    def test_the_network_that_was_handed_out_does_not_change_with_later_edits(self):
        points = stream()
        handed = points.network()
        document = handed.to_document()

        points.remove_point("P2")

        assert handed.to_document() == document
        assert points.network().to_document() != document
