"""Tests of routing over a network: identities, order independence, structure, axes.

The references are the elements themselves: a network with one reach must give what
the reach gives, a junction adds, and for a linear reach the sum of the routed parts is
the routed sum. The structure rules are the ones of the plan: a cycle, an unknown id,
two outlets and a node that flows nowhere are errors, and neither the order of the
nodes nor anything else but the links decides the result.
"""

import itertools

import numpy as np
import pytest

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing import (
    CascadeReach,
    Hydrograph,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    NetworkNode,
    Reach,
    RoutingNetwork,
)
from hydrolog.routing.network import MAX_ID_CHARS, NODE_KINDS

FLOOD = Hydrograph.from_step([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0)
SMALL = Hydrograph.from_step([0.0, 4.0, 12.0, 8.0, 3.0, 0.0, 0.0, 0.0], 10.0)


def source(node_id: str, hydrograph: Hydrograph = FLOOD) -> NetworkNode:
    return NetworkNode(node_id, "subcatchment", hydrograph=hydrograph)


def reach(node_id: str, upstream: str, element: Reach, **options) -> NetworkNode:
    return NetworkNode(node_id, "reach", [upstream], reach=element, **options)


def junction(node_id: str, *upstream: str) -> NetworkNode:
    return NetworkNode(node_id, "junction", list(upstream))


def outlet(upstream: str, node_id: str = "OUT") -> NetworkNode:
    return NetworkNode(node_id, "outlet", [upstream])


def stream() -> list[NetworkNode]:
    """A tributary A through a lag reach, joined by B, then a pond, then the outlet."""
    return [
        source("A"),
        source("B", SMALL),
        reach("R1", "A", LagReach(lag_min=25.0)),
        junction("J1", "R1", "B"),
        NetworkNode(
            "D",
            "reservoir",
            ["J1"],
            reach=LevelPoolReach(
                storage_m3=[0.0, 30000.0, 90000.0, 180000.0, 400000.0],
                outflow_m3s=[0.0, 10.0, 40.0, 100.0, 300.0],
            ),
        ),
        outlet("D"),
    ]


ELEMENTS = {
    "lag": LagReach(lag_min=25.0),
    "muskingum": MuskingumReach(k_min=40.0, x=0.2),
    "muskingum-cunge": MuskingumCungeReach(
        length_km=8.0,
        slope_m_per_m=0.001,
        celerity_m_per_s=1.2,
        top_width_m=25.0,
        reference_discharge_m3s=10.0,
    ),
    "cascade": CascadeReach(n=3.0, k_min=20.0),
    "level-pool": LevelPoolReach(
        storage_m3=[0.0, 30000.0, 90000.0, 180000.0],
        outflow_m3s=[0.0, 10.0, 40.0, 100.0],
    ),
}


class TestOneReachNetwork:
    @pytest.mark.parametrize("model", ELEMENTS)
    def test_it_gives_what_the_single_element_gives(self, model):
        element = ELEMENTS[model]
        network = RoutingNetwork([source("A"), reach("R", "A", element), outlet("R")])

        result = network.route()

        single = element.route(FLOOD)
        np.testing.assert_array_equal(
            result.hydrographs["OUT"].discharge_m3s, single.outflow.discharge_m3s
        )
        np.testing.assert_array_equal(
            result.hydrographs["OUT"].times_min, single.outflow.times_min
        )
        assert result.runs["R"].parameters == single.parameters
        assert [n.code for n in result.runs["R"].notices] == [
            n.code for n in single.notices
        ]
        assert result.hydrographs["A"] is FLOOD
        assert set(result.runs) == {"R"}

    def test_the_run_options_of_a_node_reach_its_element(self):
        element = MuskingumReach(k_min=40.0, x=0.2)
        node = reach("R", "A", element, initial_outflow_m3s=5.0, extend_min=0.0)

        result = RoutingNetwork([source("A"), node, outlet("R")]).route()

        single = element.route(FLOOD, initial_outflow_m3s=5.0, extend_min=0.0)
        np.testing.assert_array_equal(
            result.hydrographs["OUT"].discharge_m3s, single.outflow.discharge_m3s
        )
        assert len(result.hydrographs["OUT"]) == len(FLOOD)

    def test_a_reservoir_is_a_level_pool_reach(self):
        element = ELEMENTS["level-pool"]
        network = RoutingNetwork(
            [
                source("A"),
                NetworkNode("D", "reservoir", ["A"], reach=element),
                outlet("D"),
            ]
        )

        result = network.route()

        np.testing.assert_array_equal(
            result.hydrographs["OUT"].discharge_m3s,
            element.route(FLOOD).outflow.discharge_m3s,
        )
        assert result.runs["D"].parameters["storage_peak_m3"] > 0.0


class TestJunction:
    def test_it_adds_the_hydrographs_that_flow_into_it(self):
        network = RoutingNetwork(
            [source("A"), source("B", SMALL), junction("J", "A", "B"), outlet("J")]
        )

        result = network.route()

        np.testing.assert_allclose(
            result.hydrographs["J"].discharge_m3s,
            FLOOD.discharge_m3s + SMALL.discharge_m3s,
            rtol=0,
            atol=1e-12,
        )
        assert result.hydrographs["OUT"] is result.hydrographs["J"]

    def test_a_shorter_hydrograph_is_held_at_its_last_value(self):
        short = Hydrograph.from_step([1.0, 3.0, 2.0], 10.0)
        long = Hydrograph.from_step([0.0, 2.0, 4.0, 6.0, 4.0], 10.0)

        result = RoutingNetwork(
            [
                source("A", short),
                source("B", long),
                junction("J", "A", "B"),
                outlet("J"),
            ]
        ).route()

        np.testing.assert_array_equal(
            result.hydrographs["J"].discharge_m3s, [1.0, 5.0, 6.0, 8.0, 6.0]
        )
        np.testing.assert_array_equal(result.hydrographs["J"].times_min, long.times_min)

    def test_the_sum_of_the_routed_parts_is_the_routed_sum_for_a_linear_reach(self):
        # the cascade is linear and the sources start from zero: superposition holds
        element = CascadeReach(n=2.5, k_min=15.0)
        joined = RoutingNetwork(
            [
                source("A"),
                source("B", SMALL),
                junction("J", "A", "B"),
                reach("R", "J", element, extend_min=300.0),
                outlet("R"),
            ]
        ).route()

        parts = [
            element.route(hydrograph, extend_min=300.0).outflow.discharge_m3s
            for hydrograph in (FLOOD, SMALL)
        ]

        np.testing.assert_allclose(
            joined.hydrographs["OUT"].discharge_m3s,
            parts[0] + parts[1],
            rtol=0,
            atol=1e-10,
        )

    def test_a_network_of_lags_keeps_every_cubic_metre(self):
        # a lag stores nothing, so the outlet holds the volume of the sources, each
        # held at its last value over the axis of the outlet
        network = RoutingNetwork(
            [
                source("A"),
                source("B", SMALL),
                reach("R1", "A", LagReach(lag_min=35.0)),
                junction("J", "R1", "B"),
                reach("R2", "J", LagReach(lag_min=12.0)),
                outlet("R2"),
            ]
        )

        result = network.route()

        out = result.hydrographs["OUT"]
        expected = sum(
            hydrograph.extended(len(out) - len(hydrograph)).volume_m3
            for hydrograph in (FLOOD, SMALL)
        )
        assert out.volume_m3 == pytest.approx(expected, rel=1e-12)

    def test_the_runs_of_a_pond_balance_their_own_storage(self):
        result = RoutingNetwork(stream()).route()

        for node_id, run in result.runs.items():
            assert abs(run.balance_error_m3) < 1e-6 * run.inflow.volume_m3, node_id


class TestOrder:
    def test_the_headwaters_come_first_and_the_smallest_id_among_the_ready(self):
        network = RoutingNetwork(stream())

        assert network.order == ("A", "B", "R1", "J1", "D", "OUT")
        assert [node.id for node in network.nodes] == list(network.order)
        assert network.outlet == "OUT"
        assert network.timestep_min == 10.0
        assert network.node("R1").kind == "reach"

    def test_the_order_of_the_nodes_does_not_change_anything(self):
        reference = RoutingNetwork(stream()).route()

        for permutation in itertools.permutations(stream()):
            result = RoutingNetwork(list(permutation)).route()

            assert result.order == reference.order
            for node_id, hydrograph in reference.hydrographs.items():
                np.testing.assert_array_equal(
                    result.hydrographs[node_id].discharge_m3s,
                    hydrograph.discharge_m3s,
                )

    def test_the_result_names_the_network_and_its_axis(self):
        result = RoutingNetwork(stream(), name="Example stream").route()

        assert result.name == "Example stream"
        assert result.outlet == "OUT"
        assert result.timestep_min == 10.0
        assert set(result.hydrographs) == {"A", "B", "R1", "J1", "D", "OUT"}
        assert set(result.runs) == {"R1", "D"}
        assert RoutingNetwork(stream()).route().name is None


def broken(case: str) -> list[NetworkNode]:
    """The nodes of a network that breaks one rule."""
    base = {
        "unknown": [source("A"), reach("R", "X", LagReach(10.0)), outlet("R")],
        "two unknown": [
            source("A"),
            junction("J", "A", "X", "Y"),
            outlet("J"),
        ],
        "cycle": [
            source("A"),
            reach("R2", "R1", LagReach(10.0)),
            reach("R1", "R2", LagReach(10.0)),
            junction("J", "A", "R1"),
            outlet("J"),
        ],
        "self": [source("A"), reach("R", "R", LagReach(10.0)), outlet("R")],
        "bifurcation": [
            source("A"),
            reach("R", "A", LagReach(10.0)),
            junction("J", "A", "R"),
            outlet("J"),
        ],
        "no outlet": [source("A"), reach("R", "A", LagReach(10.0))],
        "two outlets": [
            source("A"),
            source("B"),
            outlet("A", "OUT1"),
            outlet("B", "OUT2"),
        ],
        "outlet with a downstream node": [
            source("A"),
            outlet("A"),
            reach("R", "OUT", LagReach(10.0)),
        ],
        "disconnected": [
            source("A"),
            source("B"),
            reach("R", "B", LagReach(10.0)),
            outlet("A"),
        ],
        "duplicate": [
            source("A"),
            source("a", SMALL),
            junction("J", "A", "a"),
            outlet("J"),
        ],
        "empty": [],
    }
    return base[case]


class TestStructure:
    @pytest.mark.parametrize(
        ("case", "details"),
        [
            (
                "unknown",
                {
                    "reason": "unknown_upstream",
                    "node_id": "R",
                    "upstream_id": "X",
                    "n_unknown": 1,
                },
            ),
            (
                "two unknown",
                {
                    "reason": "unknown_upstream",
                    "node_id": "J",
                    "upstream_id": "X",
                    "n_unknown": 2,
                },
            ),
            ("cycle", {"reason": "cycle", "nodes": ["R1", "R2"]}),
            ("self", {"reason": "cycle", "nodes": ["R"]}),
            (
                "bifurcation",
                {
                    "reason": "several_downstream",
                    "node_id": "A",
                    "downstream": ["R", "J"],  # in the order of evaluation
                },
            ),
            ("no outlet", {"reason": "no_outlet"}),
            ("two outlets", {"reason": "several_outlets", "nodes": ["OUT1", "OUT2"]}),
            (
                "outlet with a downstream node",
                {
                    "reason": "outlet_has_downstream",
                    "node_id": "OUT",
                    "downstream": ["R"],
                },
            ),
            (
                "disconnected",
                {"reason": "disconnected_node", "node_id": "R", "n_disconnected": 2},
            ),
            (
                "duplicate",
                {"reason": "duplicate_node", "node_id": "a", "other_id": "A"},
            ),
            ("empty", {"reason": "empty"}),
        ],
    )
    def test_a_network_that_breaks_a_rule_is_refused_with_the_reason(
        self, case, details
    ):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(broken(case))

        assert caught.value.details == details
        assert caught.value.code == "validation_error"

    def test_the_cycle_is_listed_in_flow_order_whatever_the_order_of_the_nodes(self):
        for permutation in itertools.permutations(broken("cycle")):
            with pytest.raises(InvalidParameterError) as caught:
                RoutingNetwork(list(permutation))

            assert caught.value.details["nodes"] == ["R1", "R2"]
        assert "'R1' -> 'R2' -> 'R1'" in str(caught.value)

    def test_a_node_that_flows_nowhere_is_named_not_the_nodes_above_it(self):
        nodes = [
            source("A"),
            source("B"),
            reach("R1", "B", LagReach(10.0)),
            reach("R2", "R1", LagReach(10.0)),
            outlet("A"),
        ]

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(nodes)

        assert caught.value.details == {
            "reason": "disconnected_node",
            "node_id": "R2",
            "n_disconnected": 3,
        }


class TestNode:
    @pytest.mark.parametrize(
        "node_id",
        [
            "",
            " A",
            "a b",
            "a/b",
            "a\\b",
            "..",
            ".A",
            "a:b",
            "a.",
            "x" * (MAX_ID_CHARS + 1),
        ],
    )
    def test_an_id_that_cannot_name_a_file_is_refused(self, node_id):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode(node_id, "subcatchment", hydrograph=FLOOD)

        assert caught.value.details["reason"] == "invalid_id"

    @pytest.mark.parametrize("node_id", ["A", "R1.2", "seg-12", "_x", "Młynówka", "9"])
    def test_a_plain_id_is_accepted(self, node_id):
        assert NetworkNode(node_id, "subcatchment", hydrograph=FLOOD).id == node_id
        assert NetworkNode("x" * MAX_ID_CHARS, "outlet", ["A"]).id == "x" * MAX_ID_CHARS

    def test_an_upstream_id_is_checked_like_an_id(self):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("J", "junction", ["A", "b/c"])

        assert caught.value.details["reason"] == "invalid_id"

    @pytest.mark.parametrize(
        "node_id",
        [
            "con",
            "CON",
            "Prn",
            "aux",
            "nul",
            "NuL.csv",
            "com1",
            "COM9",
            "lpt1",
            "Lpt9.x.y",
        ],
    )
    def test_a_windows_device_name_is_refused(self, node_id):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode(node_id, "subcatchment", hydrograph=FLOOD)

        assert caught.value.details == {"reason": "reserved_name", "node_id": node_id}
        assert "Windows" in caught.value.hint

    @pytest.mark.parametrize(
        "node_id",
        ["console", "com0", "com10", "lpt0", "aux1", "x.con", "con-1", "_nul"],
    )
    def test_a_name_that_only_looks_like_a_device_is_accepted(self, node_id):
        assert NetworkNode(node_id, "subcatchment", hydrograph=FLOOD).id == node_id

    def test_an_upstream_id_that_is_a_device_name_is_refused(self):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("J", "junction", ["A", "nul"])

        assert caught.value.details["reason"] == "reserved_name"

    def test_the_kinds_are_the_five_of_the_plan(self):
        assert NODE_KINDS == (
            "subcatchment",
            "reach",
            "reservoir",
            "junction",
            "outlet",
        )
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("A", "lake")  # type: ignore[arg-type]
        assert caught.value.details["reason"] == "unknown_type"
        assert caught.value.details["allowed"] == list(NODE_KINDS)

    @pytest.mark.parametrize(
        ("kind", "upstream"),
        [
            ("subcatchment", ["X"]),
            ("reach", []),
            ("reach", ["X", "Y"]),
            ("reservoir", []),
            ("junction", []),
            ("outlet", []),
            ("outlet", ["X", "Y"]),
        ],
    )
    def test_the_number_of_upstream_nodes_follows_the_kind(self, kind, upstream):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode(
                "N",
                kind,
                upstream,
                hydrograph=FLOOD if kind == "subcatchment" else None,
                reach=LagReach(10.0) if kind == "reach" else None,
            )

        assert caught.value.details["reason"] == "upstream_count"
        assert caught.value.details["found"] == len(upstream)

    def test_an_upstream_node_listed_twice_would_count_its_water_twice(self):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("J", "junction", ["A", "A"])

        assert caught.value.details["reason"] == "duplicate_upstream"

    @pytest.mark.parametrize(
        ("kind", "upstream", "options", "field", "reason"),
        [
            ("subcatchment", [], {}, "hydrograph", "missing_field"),
            ("reach", ["A"], {}, "reach", "missing_field"),
            (
                "subcatchment",
                [],
                {"hydrograph": FLOOD, "reach": LagReach(10.0)},
                "reach",
                "unexpected_field",
            ),
            (
                "junction",
                ["A"],
                {"hydrograph": FLOOD},
                "hydrograph",
                "unexpected_field",
            ),
            ("outlet", ["A"], {"extend_min": 10.0}, "extend_min", "unexpected_field"),
            (
                "reach",
                ["A"],
                {"reach": LagReach(10.0), "hydrograph": FLOOD},
                "hydrograph",
                "unexpected_field",
            ),
        ],
    )
    def test_a_node_needs_what_its_kind_needs_and_takes_nothing_else(
        self, kind, upstream, options, field, reason
    ):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("N", kind, upstream, **options)

        assert caught.value.details["reason"] == reason
        assert caught.value.details["field"] == field

    def test_a_reservoir_routes_with_a_level_pool_only(self):
        with pytest.raises(InvalidParameterError) as caught:
            NetworkNode("D", "reservoir", ["A"], reach=LagReach(10.0))

        assert caught.value.details == {
            "reason": "reservoir_model",
            "node_id": "D",
            "model": "LagReach",
        }


class TestTimeAxes:
    def test_sources_with_different_steps_are_refused_not_resampled(self):
        coarse = Hydrograph.from_step([0.0, 5.0, 2.0, 0.0], 15.0)

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(
                [source("A"), source("B", coarse), junction("J", "A", "B"), outlet("J")]
            )

        assert caught.value.details == {
            "reason": "timestep_mismatch",
            "nodes": ["A", "B"],
            "timesteps_min": [10.0, 15.0],
        }

    def test_sources_that_start_at_different_times_are_refused(self):
        late = Hydrograph.from_step([0.0, 5.0, 2.0, 0.0], 10.0, start_min=30.0)

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(
                [source("A"), source("B", late), junction("J", "A", "B"), outlet("J")]
            )

        assert caught.value.details == {
            "reason": "start_mismatch",
            "nodes": ["A", "B"],
            "starts_min": [0.0, 30.0],
        }

    def test_sources_of_different_lengths_and_a_common_origin_are_fine(self):
        late = Hydrograph.from_step([1.0, 5.0, 2.0], 10.0, start_min=600.0)
        other = Hydrograph.from_step([0.0, 3.0, 2.0, 1.0, 1.0], 10.0, start_min=600.0)

        result = RoutingNetwork(
            [
                source("A", late),
                source("B", other),
                junction("J", "A", "B"),
                outlet("J"),
            ]
        ).route()

        assert result.hydrographs["J"].times_min.tolist() == [
            600.0 + 10.0 * i for i in range(5)
        ]


class TestRoutingErrors:
    def test_a_reach_that_fails_names_its_node(self):
        pond = LevelPoolReach(storage_m3=[0.0, 36000.0], outflow_m3s=[0.0, 10.0])
        flood = Hydrograph.from_step([0.0, 20.0, 20.0, 20.0, 20.0, 0.0], 60.0)

        with pytest.raises(CalculationError) as caught:
            RoutingNetwork(
                [
                    source("A", flood),
                    NetworkNode("D", "reservoir", ["A"], reach=pond),
                    outlet("D"),
                ]
            ).route()

        assert caught.value.details["reason"] == "table_exceeded"
        assert caught.value.details["node_id"] == "D"
        assert "Node 'D'" in str(caught.value)
        assert caught.value.hint

    def test_an_invalid_run_option_names_its_node(self):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(
                [
                    source("A"),
                    reach("R", "A", LagReach(10.0), initial_outflow_m3s=-1.0),
                    outlet("R"),
                ]
            ).route()

        assert caught.value.details["option"] == "initial_outflow_m3s"
        assert caught.value.details["node_id"] == "R"
