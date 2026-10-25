"""Tests of a subcatchment that makes its own hydrograph, inside a network (ADR-0012).

The references are the generator and the network of the plan: the hydrograph of such a
node is what ``HydrographGenerator`` gives for its rain, and a network of them routes
exactly like the network in which the same hydrographs were given. The rain belongs to
the subcatchment: nothing assumes one for the network, two subcatchments can take it
from different sources, and the default of the network is a convenience that a
subcatchment's own rainfall beats. The time step is one for the network and nothing is
resampled.
"""

import warnings

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BlockHietogram, EulerIIHietogram
from hydrolog.routing import (
    HIETOGRAMS,
    NODE_TYPES,
    RAINFALL_KINDS,
    RUNOFF_MODELS,
    Channel,
    CurveNumberRunoff,
    DesignStorm,
    Hydrograph,
    Junction,
    LagReach,
    MuskingumReach,
    Outlet,
    RainfallSeries,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.document import SCHEMA
from hydrolog.routing.network import DEFAULT_TIMESTEP_MIN
from hydrolog.runoff import AMC, HydrographGenerator

from ._routing_extensions import Constant, Growing, Share

UPPER = WatershedParameters(
    area_km2=12.0,
    perimeter_km=18.0,
    length_km=6.0,
    elevation_min_m=210.0,
    elevation_max_m=330.0,
    cn=75,
)
LOWER = WatershedParameters(
    area_km2=5.0,
    perimeter_km=11.0,
    length_km=3.5,
    elevation_min_m=210.0,
    elevation_max_m=290.0,
    cn=70,
)
STORM = DesignStorm(45.0, 60.0, EulerIIHietogram())
BLOCK = DesignStorm(30.0, 60.0, BlockHietogram())
MODEL = CurveNumberRunoff(tc_min=90.0)
FLOOD = Hydrograph.from_step([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0)


def made(node_id, watershed=UPPER, **options) -> Subcatchment:
    options.setdefault("runoff", MODEL)
    return Subcatchment(node_id, watershed=watershed, **options)


def generated(storm, step, watershed=UPPER, tc_min=90.0, amc=AMC.II):
    """What the generator gives for a storm: the reference of a made hydrograph."""
    area = watershed.area_km2
    return HydrographGenerator(area_km2=area, cn=watershed.cn, tc_min=tc_min).generate(
        storm.hyetograph(step), amc=amc
    )


def refused(build) -> InvalidParameterError:
    with pytest.raises(InvalidParameterError) as caught:
        build()
    return caught.value


class TestItMakesTheHydrographOfTheGenerator:
    def test_the_hydrograph_of_the_node_is_the_generators_to_the_last_ordinate(self):
        network = RoutingNetwork(Outlet("OUT", inflow=made("A", rainfall=STORM)))

        result = network.route()

        reference = generated(STORM, 5.0)
        np.testing.assert_array_equal(
            result.hydrographs["A"].discharge_m3s, reference.hydrograph.discharge_m3s
        )
        np.testing.assert_array_equal(
            result.hydrographs["A"].times_min, reference.hydrograph.times_min
        )
        assert result.hydrographs["OUT"].peak_discharge_m3s == (
            reference.peak_discharge_m3s
        )
        assert result.timestep_min == network.timestep_min == DEFAULT_TIMESTEP_MIN

    def test_the_rain_that_it_took_is_in_the_result(self):
        a = made("A", rainfall=STORM)
        b = Subcatchment("B", FLOOD)
        network = RoutingNetwork(
            Outlet("OUT", inflow=Junction("J", inflows=[a, b])), timestep_min=10.0
        )

        result = network.route()

        assert set(result.rainfall) == {"A"}
        rain = result.rainfall["A"]
        np.testing.assert_array_equal(
            rain.intensities_mm, STORM.hyetograph(10.0).intensities_mm
        )
        assert rain.timestep_min == 10.0 and rain.total_mm == 45.0

    def test_a_network_of_them_routes_as_the_network_of_their_hydrographs(self):
        def stream(a, b):
            r = Channel("R", MuskingumReach(k_min=40.0, x=0.2), inflow=a)
            return RoutingNetwork(Outlet("OUT", inflow=Junction("J", inflows=[r, b])))

        a = made("A", rainfall=STORM)
        b = made("B", LOWER, rainfall=BLOCK, runoff=CurveNumberRunoff(tc_min=40.0))
        flood_a = generated(STORM, 5.0).hydrograph
        flood_b = generated(BLOCK, 5.0, LOWER, 40.0).hydrograph

        by_making = stream(a, b).route()
        by_giving = stream(
            Subcatchment("A", Hydrograph(flood_a.times_min, flood_a.discharge_m3s)),
            Subcatchment("B", Hydrograph(flood_b.times_min, flood_b.discharge_m3s)),
        ).route()

        assert by_making.order == by_giving.order
        for node_id in by_making.order:
            np.testing.assert_array_equal(
                by_making.hydrographs[node_id].discharge_m3s,
                by_giving.hydrographs[node_id].discharge_m3s,
            )
        assert by_making.nodes["R"].parameters == by_giving.nodes["R"].parameters

    def test_a_node_that_is_given_its_hydrograph_has_no_rain_and_no_parameters(self):
        given = Subcatchment("B", FLOOD)
        network = RoutingNetwork(
            Outlet(
                "OUT", inflow=Junction("J", inflows=[made("A", rainfall=STORM), given])
            )
        )

        result = network.route()

        assert "B" not in result.rainfall
        assert result.nodes["B"].parameters == [] and result.nodes["B"].notices == []
        assert given.hydrograph is FLOOD and given.watershed is None

    def test_its_summary_says_what_the_rain_and_the_model_used(self):
        result = RoutingNetwork(
            Outlet("OUT", inflow=made("A", rainfall=STORM, runoff=MODEL))
        ).route()

        summary = result.nodes["A"]
        listed = {p.name: p for p in summary.parameters}
        reference = generated(STORM, 5.0)
        assert summary.type == "subcatchment" and summary.inflows == ()
        assert summary.peak_m3s == reference.peak_discharge_m3s
        assert (listed["total_mm"].value, listed["total_mm"].source) == (45.0, "given")
        assert (listed["timestep_min"].value, listed["timestep_min"].source) == (
            5.0,
            "computed",
        )
        assert listed["area_km2"].value == 12.0 and listed["cn"].value == 75
        assert listed["tc_min"].source == "given"
        assert listed["total_effective_mm"].value == reference.total_effective_mm
        assert listed["runoff_coefficient"].value == reference.runoff_coefficient
        assert result.nodes["OUT"].parameters == []
        json_form = summary.to_dict()
        assert json_form["parameters"][0] == {
            "name": "total_mm",
            "value": 45.0,
            "unit": "mm",
            "source": "given",
        }


class TestTheRainBelongsToTheSubcatchment:
    def test_two_subcatchments_take_it_from_different_sources(self):
        a = made("A", rainfall=STORM)
        record = RainfallSeries([0.0, 4.0, 11.0, 6.0, 1.0, 0.0], timestep_min=5.0)
        b = made("B", LOWER, rainfall=record, runoff=CurveNumberRunoff(tc_min=40.0))
        c = made("C", LOWER, rainfall=Constant(2.0, 6), runoff=Share(0.5))
        network = RoutingNetwork(
            Outlet("OUT", inflow=Junction("J", inflows=[a, b, c])), name="mixed"
        )

        result = network.route()

        assert network.rainfall is None
        np.testing.assert_array_equal(
            result.hydrographs["A"].discharge_m3s,
            generated(STORM, 5.0).hydrograph.discharge_m3s,
        )
        reference_b = HydrographGenerator(area_km2=5.0, cn=70, tc_min=40.0).generate(
            record.hyetograph(5.0)
        )
        np.testing.assert_array_equal(
            result.hydrographs["B"].discharge_m3s,
            reference_b.hydrograph.discharge_m3s,
        )
        assert result.hydrographs["C"].volume_m3 == pytest.approx(
            0.5 * 12.0 / 1000.0 * 5.0e6, rel=0.2
        )
        assert set(result.rainfall) == {"A", "B", "C"}
        assert result.rainfall["B"].total_mm == 22.0
        listed = {p.name for p in result.nodes["C"].parameters}
        assert {"depth_mm", "share"} <= listed, "a source and a model of the user"

    def test_the_default_of_the_network_is_taken_by_the_subcatchment_that_has_none(
        self,
    ):
        own = made("A", rainfall=STORM)
        lacking = made("B", LOWER, runoff=CurveNumberRunoff(tc_min=40.0))
        network = RoutingNetwork(
            Outlet("OUT", inflow=Junction("J", inflows=[own, lacking])), rainfall=BLOCK
        )

        result = network.route()

        assert network.rainfall is BLOCK
        np.testing.assert_array_equal(
            result.hydrographs["A"].discharge_m3s,
            generated(STORM, 5.0).hydrograph.discharge_m3s,
        )
        np.testing.assert_array_equal(
            result.hydrographs["B"].discharge_m3s,
            generated(BLOCK, 5.0, LOWER, 40.0).hydrograph.discharge_m3s,
        )
        assert result.rainfall["A"].total_mm == 45.0
        assert result.rainfall["B"].total_mm == 30.0
        assert {p.name: p.value for p in result.nodes["B"].parameters}["total_mm"] == (
            30.0
        )

    def test_a_network_in_which_every_subcatchment_has_its_own_needs_no_default(self):
        network = RoutingNetwork(Outlet("OUT", inflow=made("A", rainfall=STORM)))

        assert network.rainfall is None and network.route().rainfall.keys() == {"A"}

    def test_a_subcatchment_without_rain_is_refused_when_the_network_is_made(self):
        lonely = made("A")
        error = refused(lambda: RoutingNetwork(Outlet("OUT", inflow=lonely)))

        assert error.details == {
            "reason": "missing_field",
            "node_id": "A",
            "field": "rainfall",
        }
        assert "Node 'A'" in str(error) and "RoutingNetwork" in str(error.hint)
        RoutingNetwork(Outlet("OUT", inflow=lonely), rainfall=STORM)

    def test_the_default_must_be_a_rainfall_and_the_step_positive(self):
        outlet = Outlet("OUT", inflow=made("A", rainfall=STORM))

        error = refused(lambda: RoutingNetwork(outlet, rainfall="heavy"))
        assert (error.details["reason"], error.details["field"]) == (
            "type",
            "rainfall",
        )
        for value in (0.0, -5.0):
            error = refused(
                lambda value=value: RoutingNetwork(outlet, timestep_min=value)
            )
            assert (error.details["option"], error.details["reason"]) == (
                "timestep_min",
                "exclusive_minimum",
            )


class TestTheTimeStep:
    @staticmethod
    def network(*nodes, **options):
        return RoutingNetwork(
            Outlet("OUT", inflow=Junction("J", inflows=nodes)), **options
        )

    def test_a_network_of_design_storms_takes_the_default_step_or_the_one_it_is_given(
        self,
    ):
        a = made("A", rainfall=STORM)

        default = self.network(a).route()
        given = self.network(a, timestep_min=10.0).route()

        assert default.timestep_min == DEFAULT_TIMESTEP_MIN == 5.0
        assert (
            given.timestep_min == 10.0 and given.hydrographs["A"].timestep_min == 10.0
        )
        assert given.rainfall["A"].timestep_min == 10.0
        np.testing.assert_array_equal(
            given.hydrographs["A"].discharge_m3s,
            generated(STORM, 10.0).hydrograph.discharge_m3s,
        )

    def test_a_given_hydrograph_fixes_the_step_of_the_subcatchments_that_make_theirs(
        self,
    ):
        result = self.network(
            made("A", rainfall=STORM), Subcatchment("B", FLOOD)
        ).route()

        assert result.timestep_min == 10.0
        assert result.hydrographs["A"].timestep_min == 10.0
        assert result.rainfall["A"].timestep_min == 10.0

    def test_a_series_fixes_it_too_and_so_does_the_series_of_the_network(self):
        record = RainfallSeries([0.0, 3.0, 8.0, 4.0], timestep_min=15.0)

        own = self.network(made("A", rainfall=record)).route()
        default = self.network(made("A"), rainfall=record).route()

        assert own.timestep_min == default.timestep_min == 15.0
        np.testing.assert_array_equal(
            own.hydrographs["A"].discharge_m3s, default.hydrographs["A"].discharge_m3s
        )

    def test_a_series_and_a_given_hydrograph_of_different_steps_are_refused(self):
        record = RainfallSeries([0.0, 3.0, 8.0, 4.0], timestep_min=5.0)

        error = refused(
            lambda: self.network(made("A", rainfall=record), Subcatchment("B", FLOOD))
        )

        assert error.details["reason"] == "timestep_mismatch"
        assert error.details["nodes"] == ["A", "B"]
        assert error.details["timesteps_min"] == [5.0, 10.0]

    def test_a_step_that_is_given_and_a_source_with_another_are_refused(self):
        record = RainfallSeries([0.0, 3.0, 8.0, 4.0], timestep_min=5.0)

        for node, found in (
            (made("A", rainfall=record), 5.0),
            (Subcatchment("A", FLOOD), 10.0),
        ):
            error = refused(lambda node=node: self.network(node, timestep_min=20.0))
            assert error.details["reason"] == "timestep_mismatch"
            assert error.details["nodes"] == ["A"]
            assert error.details["timesteps_min"] == [20.0, found]
            assert "network" in str(error)

    def test_a_step_that_is_given_and_agrees_with_the_sources_is_fine(self):
        network = self.network(Subcatchment("A", FLOOD), timestep_min=10.0)

        assert network.timestep_min == 10.0
        assert network.given_timestep_min == 10.0
        assert self.network(Subcatchment("A", FLOOD)).given_timestep_min is None

    def test_the_hydrograph_that_is_made_starts_at_zero_like_the_others_must(self):
        late = Hydrograph([10.0, 20.0, 30.0], [0.0, 1.0, 0.0])

        error = refused(
            lambda: self.network(
                made("A", rainfall=STORM), Subcatchment("B", late), timestep_min=10.0
            )
        )

        assert error.details["reason"] == "start_mismatch"
        assert error.details["nodes"] == ["A", "B"]
        assert error.details["starts_min"] == [0.0, 10.0]

    def test_a_step_longer_than_the_storm_is_the_error_of_the_node_when_routing(self):
        network = self.network(
            made("A", rainfall=DesignStorm(30.0, 20.0, BlockHietogram())),
            timestep_min=60.0,
        )

        error = refused(network.route)

        assert error.details["node_id"] == "A" and "Node 'A'" in str(error)


class TestWhatTheRunObserves:
    def test_a_duration_that_is_not_a_whole_number_of_steps_is_a_notice_of_the_node(
        self,
    ):
        short = DesignStorm(30.0, 62.0, BlockHietogram())
        whole = DesignStorm(30.0, 60.0, BlockHietogram())
        network = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=Junction(
                    "J", inflows=[made("A", rainfall=short), made("B", rainfall=whole)]
                ),
            )
        )

        result = network.route()

        (notice,) = result.nodes["A"].notices
        assert (notice.code, notice.level) == ("duration_not_covered", "warning")
        assert "62 min" in notice.message and "60 min" in notice.message
        assert result.nodes["B"].notices == []

    def test_a_warning_of_the_library_is_a_notice_of_the_node_that_caused_it(self):
        flat = WatershedParameters(
            area_km2=12.0,
            perimeter_km=18.0,
            length_km=12.0,
            elevation_min_m=210.0,
            elevation_max_m=220.0,
            cn=75,
        )
        network = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=Junction(
                    "J",
                    inflows=[
                        made("A", flat, rainfall=STORM, runoff=CurveNumberRunoff()),
                        made("B", rainfall=STORM),
                    ],
                ),
            )
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = network.route()

        (notice,) = result.nodes["A"].notices
        assert (notice.code, notice.level) == ("user_warning", "warning")
        assert "outside typical range" in notice.message
        assert result.nodes["B"].notices == []

    def test_the_same_warning_is_one_notice_and_another_kind_is_not_swallowed(self):
        class Noisy(Share):
            def hydrograph(self, rainfall, watershed, timestep_min):
                warnings.warn("loose parameters", UserWarning, stacklevel=2)
                warnings.warn("loose parameters", UserWarning, stacklevel=2)
                warnings.warn("old name", DeprecationWarning, stacklevel=2)
                return super().hydrograph(rainfall, watershed, timestep_min)

        network = RoutingNetwork(
            Outlet("OUT", inflow=made("A", rainfall=STORM, runoff=Noisy(0.5)))
        )

        with pytest.warns(DeprecationWarning, match="old name"):
            result = network.route()

        assert [n.message for n in result.nodes["A"].notices] == ["loose parameters"]

    def test_the_notices_of_a_reach_are_reported_with_the_node_of_the_reach(self):
        stream = Channel("R", LagReach(lag_min=12.0), inflow=Subcatchment("A", FLOOD))

        result = RoutingNetwork(Outlet("OUT", inflow=stream)).route()

        assert [n.code for n in result.nodes["R"].notices] == [
            n.code for n in result.runs["R"].notices
        ]
        assert "lag_interpolated" in [n.code for n in result.nodes["R"].notices]


class TestWhatItRefuses:
    @pytest.mark.parametrize("field", ["watershed", "runoff", "rainfall"])
    def test_a_hydrograph_and_the_means_to_make_one_are_refused_together(self, field):
        options = {"watershed": UPPER, "runoff": MODEL, "rainfall": STORM}

        error = refused(lambda: Subcatchment("A", FLOOD, **{field: options[field]}))

        assert error.details == {
            "reason": "conflict",
            "node_id": "A",
            "field": field,
        }

    @pytest.mark.parametrize(
        ("arguments", "field"),
        [
            ({}, "hydrograph"),
            ({"rainfall": STORM}, "hydrograph"),
            ({"watershed": UPPER}, "runoff"),
            ({"runoff": MODEL}, "watershed"),
        ],
    )
    def test_a_node_without_a_source_says_which_part_is_missing(self, arguments, field):
        error = refused(lambda: Subcatchment("A", **arguments))

        assert error.details["reason"] == "missing_field"
        assert (error.details["node_id"], error.details["field"]) == ("A", field)

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("watershed", {"area_km2": 12.0}),
            ("runoff", "curve-number"),
            ("rainfall", 45.0),
        ],
    )
    def test_an_argument_of_another_class_is_refused(self, field, value):
        arguments = {"watershed": UPPER, "runoff": MODEL, "rainfall": STORM}
        arguments[field] = value

        error = refused(lambda: Subcatchment("A", **arguments))

        assert (error.details["reason"], error.details["field"]) == ("type", field)

    def test_a_hydrograph_of_another_class_is_refused(self):
        error = refused(lambda: Subcatchment("A", [0.0, 1.0]))

        assert (error.details["reason"], error.details["field"]) == (
            "type",
            "hydrograph",
        )

    def test_a_watershed_that_the_model_cannot_use_is_refused_when_the_node_is_made(
        self,
    ):
        bare = WatershedParameters(
            area_km2=12.0,
            perimeter_km=18.0,
            length_km=6.0,
            elevation_min_m=210.0,
            elevation_max_m=330.0,
        )

        error = refused(lambda: made("A", bare, rainfall=STORM))

        assert error.details["reason"] == "missing_field"
        assert (error.details["node_id"], error.details["field"]) == (
            "A",
            "watershed.cn",
        )
        assert str(error).startswith("Node 'A': watershed:")

    def test_a_node_is_immutable_and_with_inflows_keeps_what_it_makes_from(self):
        node = made("A", rainfall=STORM)

        assert node.inflows == () and node.rainfall is STORM
        assert node.runoff is MODEL and node.watershed is UPPER
        assert node.hydrograph is None
        with pytest.raises(InvalidParameterError):
            node.with_inflows(Subcatchment("B", FLOOD))


def document(*nodes, **top):
    return {"schema": SCHEMA, "nodes": list(nodes), **top}


def made_node(node_id, watershed=UPPER, **fields):
    return {
        "id": node_id,
        "type": "subcatchment",
        "watershed": watershed.to_dict(),
        "runoff": {"model": "curve-number", "tc_min": 90.0},
        **fields,
    }


class TestTheDocument:
    RAIN = {
        "kind": "design",
        "hietogram_type": "euler_ii",
        "total_mm": 45.0,
        "duration_min": 60.0,
    }

    def test_a_document_makes_the_network_that_the_objects_make(self):
        by_document = RoutingNetwork.from_document(
            document(
                made_node("A", rainfall=self.RAIN),
                made_node("B", LOWER, rainfall=self.RAIN),
                {"id": "J", "type": "junction", "from": ["A", "B"]},
                {"id": "OUT", "type": "outlet", "from": ["J"]},
            )
        )
        by_objects = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=Junction(
                    "J",
                    inflows=[
                        made("A", rainfall=STORM),
                        made("B", LOWER, rainfall=STORM),
                    ],
                ),
            )
        )

        left, right = by_document.route(), by_objects.route()

        assert left.order == right.order
        for node_id in left.order:
            np.testing.assert_array_equal(
                left.hydrographs[node_id].discharge_m3s,
                right.hydrographs[node_id].discharge_m3s,
            )

    def test_the_rainfall_and_the_step_of_the_network_are_read_from_its_top(self):
        network = RoutingNetwork.from_document(
            document(
                made_node("A"),
                {"id": "OUT", "type": "outlet", "from": ["A"]},
                rainfall=self.RAIN,
                timestep_min=10,
            )
        )

        assert network.rainfall == STORM
        assert network.timestep_min == network.given_timestep_min == 10.0
        assert network.route().rainfall["A"].timestep_min == 10.0

    def test_the_rainfall_of_a_node_beats_the_one_of_the_document(self):
        network = RoutingNetwork.from_document(
            document(
                made_node("A", rainfall={**self.RAIN, "total_mm": 20}),
                {"id": "OUT", "type": "outlet", "from": ["A"]},
                rainfall=self.RAIN,
            )
        )

        assert network.route().rainfall["A"].total_mm == 20.0

    @pytest.mark.parametrize(
        ("top", "node", "reason", "facts"),
        [
            (
                {},
                made_node("A", times_min=[0, 10], discharge_m3s=[0, 1]),
                "conflict",
                {"node_id": "A", "field": "times_min"},
            ),
            (
                {},
                made_node("A", colour="red"),
                "unknown_field",
                {"node_id": "A", "field": "colour"},
            ),
            (
                {},
                made_node("A", rainfall={**RAIN, "total_mm": -5}),
                "exclusive_minimum",
                {"node_id": "A", "option": "rainfall.total_mm"},
            ),
            (
                {},
                made_node("A", rainfall={**RAIN, "kind": "radar"}),
                "unknown_kind",
                {"node_id": "A", "field": "rainfall.kind", "value": "radar"},
            ),
            (
                {},
                made_node("A", runoff={"model": "gr4j"}),
                "unknown_model",
                {"node_id": "A", "field": "runoff.model"},
            ),
            (
                {},
                made_node("A", runoff={"model": "curve-number", "tc_min": -1}),
                "exclusive_minimum",
                {"node_id": "A", "option": "runoff.tc_min"},
            ),
            (
                {},
                {**made_node("A", rainfall=RAIN), "watershed": {"area_km2": 3}},
                "missing_field",
                {"node_id": "A", "field": "watershed.perimeter_km"},
            ),
            (
                {},
                {
                    k: v
                    for k, v in made_node("A", rainfall=RAIN).items()
                    if k != "runoff"
                },
                "missing_field",
                {"node_id": "A", "field": "runoff"},
            ),
            (
                {"rainfall": {**RAIN, "kind": "radar"}},
                made_node("A"),
                "unknown_kind",
                {"field": "rainfall.kind"},
            ),
            (
                {"timestep_min": -2},
                made_node("A", rainfall=RAIN),
                "exclusive_minimum",
                {"option": "timestep_min"},
            ),
            (
                {"timestep_min": "fast"},
                made_node("A", rainfall=RAIN),
                "type",
                {"option": "timestep_min"},
            ),
            (
                {},
                made_node("A"),
                "missing_field",
                {"node_id": "A", "field": "rainfall"},
            ),
        ],
    )
    def test_a_document_that_is_wrong_says_which_node_and_which_field(
        self, top, node, reason, facts
    ):
        nodes = [node, {"id": "OUT", "type": "outlet", "from": ["A"]}]

        error = refused(lambda: RoutingNetwork.from_document(document(*nodes, **top)))

        assert error.details["reason"] == reason
        assert {key: error.details.get(key) for key in facts} == facts

    def test_a_field_of_a_node_inside_an_object_is_named_in_the_message(self):
        node = made_node("A", rainfall={**self.RAIN, "total_mm": -5})

        error = refused(
            lambda: RoutingNetwork.from_document(
                document(node, {"id": "OUT", "type": "outlet", "from": ["A"]})
            )
        )

        assert str(error).startswith("Node 'A': rainfall: Option 'total_mm'")


class TestExtending:
    def test_a_rainfall_and_a_model_that_are_not_registered_are_used_as_they_are(self):
        network = RoutingNetwork(
            Outlet(
                "OUT",
                inflow=made("A", rainfall=Constant(2.0, 4), runoff=Share(0.5)),
            )
        )

        result = network.route()

        assert result.rainfall["A"].total_mm == 8.0
        assert result.hydrographs["A"].volume_m3 > 0.0
        assert {p.name for p in result.nodes["A"].parameters} == {"depth_mm", "share"}

    def test_a_rainfall_a_shape_and_a_model_are_registry_entries_and_nothing_else(
        self, monkeypatch
    ):
        monkeypatch.setitem(RAINFALL_KINDS._classes, "constant", Constant)
        monkeypatch.setitem(HIETOGRAMS._classes, "growing", Growing)
        monkeypatch.setitem(RUNOFF_MODELS._classes, "share-of-rain", Share)
        nodes = [
            made_node(
                "A",
                rainfall={"kind": "constant", "depth_mm": 2.0, "steps": 4},
                runoff={"model": "share-of-rain", "share": 0.5},
            ),
            made_node(
                "B",
                LOWER,
                rainfall={
                    "kind": "design",
                    "hietogram_type": "growing",
                    "growth": 2.0,
                    "total_mm": 45.0,
                    "duration_min": 60.0,
                },
            ),
            {"id": "J", "type": "junction", "from": ["A", "B"]},
            {"id": "OUT", "type": "outlet", "from": ["J"]},
        ]

        result = RoutingNetwork.from_document(document(*nodes)).route()

        assert result.rainfall["A"].total_mm == 8.0
        weights = np.arange(1, 13) ** 2.0
        np.testing.assert_allclose(
            result.rainfall["B"].intensities_mm, 45.0 * weights / weights.sum()
        )

    def test_a_kind_of_node_that_makes_hydrographs_is_still_a_subcatchment(self):
        assert NODE_TYPES["subcatchment"] is Subcatchment
