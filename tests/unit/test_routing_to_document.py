"""Tests of writing a network as a document (ADR-0012).

The reader is the reference. What a network writes, read again, is a network that
routes the same, down to the last ordinate, and the document that it writes is the
canonical form of every document that makes it: one that is in that form is written
back to the same text (the order of the keys included), any other is written in that
form once and then no more. A class that no registry names cannot be written, because
a document could not name it.
"""

import json
from typing import Any

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedParameters
from hydrolog.precipitation import BlockHietogram, EulerIIHietogram
from hydrolog.routing import (
    Channel,
    CurveNumberRunoff,
    DesignStorm,
    Hydrograph,
    Junction,
    LagReach,
    MuskingumReach,
    Node,
    NodeOutput,
    Outlet,
    RainfallSeries,
    Reach,
    Reservoir,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.document import SCHEMA

from ._routing_extensions import Constant, Growing, Share

TIMES = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
FLOOD = [0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0]
UPPER: dict[str, Any] = {
    "area_km2": 12.0,
    "perimeter_km": 18.0,
    "length_km": 6.0,
    "elevation_min_m": 210.0,
    "elevation_max_m": 330.0,
    "cn": 75,
}
LOWER: dict[str, Any] = {**UPPER, "area_km2": 5.0, "length_km": 3.5, "cn": 70}
BLOCK = {
    "kind": "design",
    "hietogram_type": "block",
    "total_mm": 30.0,
    "duration_min": 60.0,
}
EULER = {**BLOCK, "hietogram_type": "euler_ii", "total_mm": 45.0}
POND = {
    "storage_m3": [0.0, 30000.0, 90000.0, 180000.0],
    "outflow_m3s": [0.0, 10.0, 40.0, 100.0],
}

# every kind of node, a rain of its own and the default of the network, in the order
# in which the network evaluates them: the canonical form
CANONICAL = {
    "schema": SCHEMA,
    "name": "Upper catchment",
    "timestep_min": 10.0,
    "rainfall": BLOCK,
    "nodes": [
        {"id": "A", "type": "subcatchment", "times_min": TIMES, "discharge_m3s": FLOOD},
        {
            "id": "B",
            "type": "subcatchment",
            "watershed": UPPER,
            "runoff": {"model": "curve-number", "tc_min": 90.0},
            "rainfall": EULER,
        },
        {
            "id": "C",
            "type": "subcatchment",
            "watershed": LOWER,
            "runoff": {"model": "curve-number", "tc_method": "kirpich"},
        },
        {"id": "R1", "type": "reach", "from": ["A"], "method": "lag", "lag_min": 25.0},
        {"id": "J1", "type": "junction", "from": ["B", "C", "R1"]},
        {
            "id": "D",
            "type": "reservoir",
            "from": ["J1"],
            **POND,
            "initial_outflow_m3s": 1.0,
        },
        {"id": "OUT", "type": "outlet", "from": ["D"]},
    ],
}

# the same kind of network as a person writes it: integers, defaults spelt out, the
# nodes in any order
UNTIDY = {
    "schema": SCHEMA,
    "nodes": [
        {"id": "OUT", "type": "outlet", "from": ["J1"]},
        {"id": "J1", "type": "junction", "from": ["R1", "B"]},
        {
            "id": "R1",
            "type": "reach",
            "from": ["A"],
            "method": "muskingum",
            "k_min": 40,
            "x": 0.2,
            "subreaches": None,
            "extend_min": None,
        },
        {
            "id": "B",
            "type": "subcatchment",
            "watershed": UPPER,
            "runoff": {
                "model": "curve-number",
                "tc_min": 90,
                "ia_coefficient": 0.2,
                "amc": "II",
                "uh_model": "scs",
            },
            "rainfall": {**EULER, "total_mm": 45, "duration_min": 60},
        },
        {"id": "A", "type": "subcatchment", "times_min": TIMES, "discharge_m3s": FLOOD},
    ],
}


def text(document) -> str:
    """The document as JSON text; the key order and any NaN would show."""
    return json.dumps(document, allow_nan=False)


def assert_same_results(first: RoutingNetwork, second: RoutingNetwork) -> None:
    """The two networks give the same hydrograph and parameters at every node."""
    one, other = first.route(), second.route()
    assert one.order == other.order
    for node_id in one.order:
        np.testing.assert_array_equal(
            one.hydrographs[node_id].times_min, other.hydrographs[node_id].times_min
        )
        np.testing.assert_array_equal(
            one.hydrographs[node_id].discharge_m3s,
            other.hydrographs[node_id].discharge_m3s,
        )
        assert one.nodes[node_id].parameters == other.nodes[node_id].parameters


def single(reach_fields: dict, **run) -> dict:
    """A document of one subcatchment, one reach of the given method and the outlet."""
    return {
        "schema": SCHEMA,
        "nodes": [
            {
                "id": "A",
                "type": "subcatchment",
                "times_min": TIMES,
                "discharge_m3s": FLOOD,
            },
            {"id": "R", "type": "reach", "from": ["A"], **reach_fields, **run},
            {"id": "OUT", "type": "outlet", "from": ["R"]},
        ],
    }


class TestTheCanonicalForm:
    def test_a_document_in_that_form_is_written_back_to_the_same_text(self):
        network = RoutingNetwork.from_document(CANONICAL)

        assert text(network.to_document()) == text(CANONICAL)

    def test_another_document_is_written_in_that_form_once_and_then_no_more(self):
        network = RoutingNetwork.from_document(UNTIDY)

        written = network.to_document()

        assert [node["id"] for node in written["nodes"]] == [
            "A",
            "B",
            "R1",
            "J1",
            "OUT",
        ]
        assert written["nodes"][2] == {
            "id": "R1",
            "type": "reach",
            "from": ["A"],
            "method": "muskingum",
            "k_min": 40.0,
            "x": 0.2,
        }
        assert written["nodes"][1]["runoff"] == {
            "model": "curve-number",
            "tc_min": 90.0,
        }
        again = RoutingNetwork.from_document(written)
        assert text(again.to_document()) == text(written)
        assert_same_results(network, again)

    def test_the_time_step_and_the_default_rainfall_are_written_only_when_given(self):
        bare = RoutingNetwork.from_document(UNTIDY).to_document()

        given = RoutingNetwork.from_document(
            {**UNTIDY, "name": "Given", "timestep_min": 10, "rainfall": BLOCK}
        ).to_document()

        assert list(bare) == ["schema", "nodes"]
        assert list(given) == ["schema", "name", "timestep_min", "rainfall", "nodes"]
        assert given["timestep_min"] == 10.0 and given["rainfall"] == BLOCK

    def test_a_subcatchment_writes_a_rainfall_only_when_it_has_its_own(self):
        written = RoutingNetwork.from_document(CANONICAL).to_document()

        by_id = {node["id"]: node for node in written["nodes"]}

        assert "rainfall" in by_id["B"]
        assert "rainfall" not in by_id["C"]

    def test_the_front_door_of_the_command_reads_what_the_library_writes(self):
        from hydrolog.operations._network_input import load_network

        written = RoutingNetwork.from_document(CANONICAL).to_document()

        loaded = load_network(network=written).network

        assert loaded.order == RoutingNetwork.from_document(CANONICAL).order
        assert text(loaded.to_document()) == text(CANONICAL)


ELEMENTS = {
    "lag": {"method": "lag", "lag_min": 25},
    "muskingum": {"method": "muskingum", "k_min": 40, "x": 0.2},
    "muskingum with sub-reaches": {
        "method": "muskingum",
        "k_min": 40,
        "x": 0.2,
        "subreaches": 4,
    },
    "muskingum-cunge from the wave": {
        "method": "muskingum-cunge",
        "length_km": 8,
        "slope_m_per_m": 0.001,
        "celerity_m_per_s": 1.2,
        "top_width_m": 25,
        "reference_discharge_m3s": 10,
    },
    "muskingum-cunge from a section": {
        "method": "muskingum-cunge",
        "length_km": 8,
        "slope_m_per_m": 0.001,
        "manning_n": 0.035,
        "bottom_width_m": 10,
        "side_slope_m_per_m": 2,
    },
    "cascade by its constant": {"method": "cascade", "n": 3, "k_min": 20},
    "cascade by the reach": {
        "method": "cascade",
        "n": 2,
        "length_km": 5,
        "celerity_m_per_s": 1.0,
    },
    "level pool with a stage": {
        "method": "level-pool",
        **POND,
        "stage_m": [100.0, 101.0, 102.0, 103.0],
        "subreaches": 2,
    },
}


class TestEveryElement:
    @pytest.mark.parametrize("name", ELEMENTS)
    def test_it_is_written_with_its_method_and_options_and_read_back_equal(self, name):
        network = RoutingNetwork.from_document(single(ELEMENTS[name]))

        written = network.to_document()
        read = RoutingNetwork.from_document(written)

        assert text(written) == text(read.to_document())
        assert written["nodes"][1]["method"] == ELEMENTS[name]["method"]
        assert read.node("R").reach.options() == network.node("R").reach.options()
        assert_same_results(network, read)

    def test_an_option_that_has_its_default_is_not_written(self):
        spelt = {**ELEMENTS["level pool with a stage"], "subreaches": 1}

        node = RoutingNetwork.from_document(single(spelt)).to_document()["nodes"][1]

        assert "subreaches" not in node
        assert node["stage_m"] == [100.0, 101.0, 102.0, 103.0]

    def test_the_run_options_are_written_when_they_were_given_and_only_then(self):
        fields = ELEMENTS["lag"]

        plain = RoutingNetwork.from_document(single(fields)).to_document()["nodes"][1]
        run = RoutingNetwork.from_document(
            single(fields, initial_outflow_m3s=0, extend_min=0)
        ).to_document()["nodes"][1]

        assert "initial_outflow_m3s" not in plain and "extend_min" not in plain
        assert run["initial_outflow_m3s"] == 0.0 and run["extend_min"] == 0.0

    def test_a_reservoir_is_written_without_a_method(self):
        network = RoutingNetwork.from_document(
            {
                "schema": SCHEMA,
                "nodes": [
                    {
                        "id": "A",
                        "type": "subcatchment",
                        "times_min": TIMES,
                        "discharge_m3s": FLOOD,
                    },
                    {"id": "D", "type": "reservoir", "from": ["A"], **POND},
                    {"id": "OUT", "type": "outlet", "from": ["D"]},
                ],
            }
        )

        node = network.to_document()["nodes"][1]

        assert node == {"id": "D", "type": "reservoir", "from": ["A"], **POND}
        assert isinstance(network.node("D"), Reservoir)


RUNOFFS = {
    "scs with a time of concentration": {"model": "curve-number", "tc_min": 90.0},
    "scs with a formula and a wet soil": {
        "model": "curve-number",
        "tc_method": "giandotti",
        "amc": "III",
    },
    "nash": {
        "model": "curve-number",
        "uh_model": "nash",
        "nash_n": 2.5,
        "nash_k_min": 20.0,
        "ia_coefficient": 0.1,
    },
    "clark": {
        "model": "curve-number",
        "uh_model": "clark",
        "tc_min": 80.0,
        "clark_r_tc_ratio": 0.6,
    },
    "snyder": {
        "model": "curve-number",
        "uh_model": "snyder",
        "snyder_length_km": 6.0,
        "snyder_centroid_length_km": 3.0,
        "snyder_cp": 0.5,
    },
}
RAINS = {
    "block": BLOCK,
    "euler": EULER,
    "triangular": {**BLOCK, "hietogram_type": "triangular", "peak_position": 0.3},
    "beta": {**BLOCK, "hietogram_type": "beta", "alpha": 3.0, "beta": 4.0},
    "a record": {
        "kind": "series",
        "depths_mm": [0.0, 2.0, 8.0, 12.0, 6.0, 2.0, 0.0],
        "timestep_min": 10.0,
    },
}


def made(runoff: dict, rainfall: dict) -> dict:
    """A document of one subcatchment that makes its hydrograph, and the outlet."""
    return {
        "schema": SCHEMA,
        "nodes": [
            {
                "id": "A",
                "type": "subcatchment",
                "watershed": UPPER,
                "runoff": runoff,
                "rainfall": rainfall,
            },
            {"id": "OUT", "type": "outlet", "from": ["A"]},
        ],
    }


class TestNodesThatMakeTheirHydrograph:
    @pytest.mark.parametrize("runoff", RUNOFFS)
    def test_every_runoff_model_is_written_and_read_back_equal(self, runoff):
        network = RoutingNetwork.from_document(made(RUNOFFS[runoff], EULER))

        written = network.to_document()
        read = RoutingNetwork.from_document(written)

        assert written["nodes"][0]["runoff"] == RUNOFFS[runoff]
        assert read.node("A").runoff == network.node("A").runoff
        assert_same_results(network, read)

    @pytest.mark.parametrize("rain", RAINS)
    def test_every_rainfall_is_written_and_read_back_equal(self, rain):
        network = RoutingNetwork.from_document(made(RUNOFFS["clark"], RAINS[rain]))

        written = network.to_document()
        read = RoutingNetwork.from_document(written)

        assert written["nodes"][0]["rainfall"] == RAINS[rain]
        assert read.node("A").rainfall == network.node("A").rainfall
        assert_same_results(network, read)

    def test_the_watershed_is_written_with_the_fields_that_were_given(self):
        network = RoutingNetwork.from_document(
            made(RUNOFFS["scs with a time of concentration"], EULER)
        )

        watershed = network.to_document()["nodes"][0]["watershed"]

        assert watershed == UPPER
        assert RoutingNetwork.from_document(
            made({"model": "curve-number", "tc_min": 90.0}, EULER)
        ).node("A").watershed == WatershedParameters(**UPPER)


class TestObjectsThatWereNeverADocument:
    def test_a_network_made_of_objects_routes_as_the_one_read_from_its_document(self):
        a = Subcatchment(
            "A",
            watershed=WatershedParameters(**UPPER),
            runoff=CurveNumberRunoff(tc_method="kirpich"),
            rainfall=DesignStorm(45.0, 60.0, EulerIIHietogram()),
        )
        b = Subcatchment(
            "B",
            watershed=WatershedParameters(**LOWER),
            runoff=CurveNumberRunoff(tc_min=60.0, amc="III"),
            rainfall=RainfallSeries([0.0, 4.0, 11.0, 6.0, 1.0, 0.0], timestep_min=5.0),
        )
        c = Subcatchment(
            "C", watershed=WatershedParameters(**LOWER), runoff=CurveNumberRunoff()
        )
        lagged = Channel("R_A", LagReach(lag_min=25.0), inflow=a)
        j1 = Junction("J1", inflows=[lagged, b])
        routed = Channel("R_J1", MuskingumReach(k_min=40.0, x=0.2), inflow=j1)
        j2 = Junction("J2", inflows=[routed, c])
        network = RoutingNetwork(
            Outlet("OUT", inflow=j2),
            name="Three subcatchments",
            rainfall=DesignStorm(30.0, 60.0, BlockHietogram()),
        )

        read = RoutingNetwork.from_document(network.to_document())

        assert read.name == "Three subcatchments"
        assert read.order == network.order
        assert read.rainfall == network.rainfall
        assert_same_results(network, read)

    def test_the_time_step_is_written_only_when_it_was_given(self):
        hydrograph = Hydrograph.from_step([0.0, 2.0, 1.0], 10.0)
        steps = [
            RoutingNetwork(Outlet("OUT", inflow=Subcatchment("A", hydrograph))),
            RoutingNetwork(
                Outlet("OUT", inflow=Subcatchment("A", hydrograph)), timestep_min=10.0
            ),
        ]

        written = [network.to_document() for network in steps]

        assert "timestep_min" not in written[0]
        assert written[1]["timestep_min"] == 10.0


class Unlisted(Node):
    """A kind of node that no registry names."""

    kind = "unlisted"

    def evaluate(self, inflows, context):
        return NodeOutput(inflows[0])

    def describe(self, output=None):
        return []

    @classmethod
    def read_document(cls, node_id, fields):
        return {}

    def document_fields(self):
        return {}


class UnlistedReach(Reach):
    """A routing method that no registry names."""

    model = "unlisted"

    def options(self):
        return {}

    def _run(self, inflow, initial_outflow_m3s):
        raise NotImplementedError


def _source():
    return Subcatchment("A", Hydrograph.from_step([0.0, 2.0, 1.0], 10.0))


def _made(**fields):
    fields.setdefault("runoff", CurveNumberRunoff(tc_min=90.0))
    return Subcatchment("A", watershed=WatershedParameters(**UPPER), **fields)


def _network(inflow, **options):
    return RoutingNetwork(Outlet("OUT", inflow=inflow), **options)


def _unlisted_node():
    return _network(Unlisted("U", [_source()]))


def _unlisted_reach():
    return _network(Channel("R", UnlistedReach(), inflow=_source()))


def _unlisted_rainfall():
    return _network(_made(rainfall=Constant(2.0, 4)))


def _unlisted_runoff():
    return _network(
        _made(runoff=Share(0.5), rainfall=DesignStorm(30.0, 60.0, BlockHietogram()))
    )


def _unlisted_shape():
    return _network(_made(rainfall=DesignStorm(30.0, 60.0, Growing())))


def _unlisted_default_rainfall():
    return _network(_made(), rainfall=Constant(2.0, 4))


UNLISTED = {
    "a node": _unlisted_node,
    "a routing method": _unlisted_reach,
    "a rainfall": _unlisted_rainfall,
    "a runoff model": _unlisted_runoff,
    "a shape of a storm": _unlisted_shape,
    "the default rainfall of the network": _unlisted_default_rainfall,
}


class TestWhatCannotBeWritten:
    @pytest.mark.parametrize("name", UNLISTED)
    def test_a_class_that_no_registry_names_is_refused(self, name):
        network = UNLISTED[name]()

        with pytest.raises(InvalidParameterError) as caught:
            network.to_document()

        assert caught.value.details["reason"] == "unregistered"
