"""Tests of routing over a network: identities, order independence, structure, axes.

The references are the elements themselves: a network with one reach must give what
the reach gives, a junction adds, and for a linear reach the sum of the routed parts is
the routed sum. The structure rules are the ones of the plan: two outlets, a node that
flows nowhere and a bifurcation are errors, and neither the order of the nodes nor
anything else but the links decides the result. The nodes link by reference; the rules
that only a document can break (an unknown id, a cycle) are tested with the document
in ``test_routing_document``.
"""

import itertools

import numpy as np
import pytest

from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.routing import (
    NODE_TYPES,
    CascadeReach,
    Channel,
    Hydrograph,
    Junction,
    LagReach,
    LevelPoolReach,
    MuskingumCungeReach,
    MuskingumReach,
    Node,
    Outlet,
    Reach,
    Reservoir,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.network import MAX_ID_CHARS

FLOOD = Hydrograph.from_step([0.0, 10.0, 40.0, 90.0, 60.0, 30.0, 10.0, 0.0], 10.0)
SMALL = Hydrograph.from_step([0.0, 4.0, 12.0, 8.0, 3.0, 0.0, 0.0, 0.0], 10.0)


def source(node_id: str, hydrograph: Hydrograph = FLOOD) -> Subcatchment:
    return Subcatchment(node_id, hydrograph)


def reach(node_id: str, upstream: Node, element: Reach, **options) -> Channel:
    return Channel(node_id, element, inflow=upstream, **options)


def junction(node_id: str, *upstream: Node) -> Junction:
    return Junction(node_id, inflows=upstream)


def outlet(upstream: Node, node_id: str = "OUT") -> Outlet:
    return Outlet(node_id, inflow=upstream)


def pond() -> LevelPoolReach:
    return LevelPoolReach(
        storage_m3=[0.0, 30000.0, 90000.0, 180000.0, 400000.0],
        outflow_m3s=[0.0, 10.0, 40.0, 100.0, 300.0],
    )


def stream() -> list[Node]:
    """A tributary A through a lag reach, joined by B, then a pond, then the outlet."""
    a, b = source("A"), source("B", SMALL)
    r1 = reach("R1", a, LagReach(lag_min=25.0))
    j1 = junction("J1", r1, b)
    d = Reservoir("D", pond(), inflow=j1)
    return [a, b, r1, j1, d, outlet(d)]


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
        network = RoutingNetwork(outlet(reach("R", source("A"), element)))

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
        node = reach("R", source("A"), element, initial_outflow_m3s=5.0, extend_min=0.0)

        result = RoutingNetwork(outlet(node)).route()

        single = element.route(FLOOD, initial_outflow_m3s=5.0, extend_min=0.0)
        np.testing.assert_array_equal(
            result.hydrographs["OUT"].discharge_m3s, single.outflow.discharge_m3s
        )
        assert len(result.hydrographs["OUT"]) == len(FLOOD)

    def test_a_reservoir_is_a_level_pool_reach(self):
        element = ELEMENTS["level-pool"]
        network = RoutingNetwork(outlet(Reservoir("D", element, inflow=source("A"))))

        result = network.route()

        np.testing.assert_array_equal(
            result.hydrographs["OUT"].discharge_m3s,
            element.route(FLOOD).outflow.discharge_m3s,
        )
        assert result.runs["D"].parameters["storage_peak_m3"] > 0.0


class TestJunction:
    def test_it_adds_the_hydrographs_that_flow_into_it(self):
        a, b = source("A"), source("B", SMALL)
        network = RoutingNetwork(outlet(junction("J", a, b)))

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
            outlet(junction("J", source("A", short), source("B", long)))
        ).route()

        np.testing.assert_array_equal(
            result.hydrographs["J"].discharge_m3s, [1.0, 5.0, 6.0, 8.0, 6.0]
        )
        np.testing.assert_array_equal(result.hydrographs["J"].times_min, long.times_min)

    def test_the_sum_of_the_routed_parts_is_the_routed_sum_for_a_linear_reach(self):
        # the cascade is linear and the sources start from zero: superposition holds
        element = CascadeReach(n=2.5, k_min=15.0)
        joined = RoutingNetwork(
            outlet(
                reach(
                    "R",
                    junction("J", source("A"), source("B", SMALL)),
                    element,
                    extend_min=300.0,
                )
            )
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
        r1 = reach("R1", source("A"), LagReach(lag_min=35.0))
        j = junction("J", r1, source("B", SMALL))
        network = RoutingNetwork(outlet(reach("R2", j, LagReach(lag_min=12.0))))

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

    def test_the_outlet_alone_is_the_network(self):
        nodes = stream()
        by_the_outlet = RoutingNetwork(nodes[-1])
        by_the_list = RoutingNetwork(nodes)

        assert by_the_outlet.order == by_the_list.order
        assert by_the_outlet.nodes == by_the_list.nodes

    def test_the_result_names_the_network_and_its_axis(self):
        result = RoutingNetwork(stream(), name="Example stream").route()

        assert result.name == "Example stream"
        assert result.outlet == "OUT"
        assert result.timestep_min == 10.0
        assert set(result.hydrographs) == {"A", "B", "R1", "J1", "D", "OUT"}
        assert set(result.runs) == {"R1", "D"}
        assert RoutingNetwork(stream()).route().name is None


class TestLinks:
    def test_a_node_is_fed_by_a_copy_and_the_original_is_left_alone(self):
        template = Channel("R", LagReach(lag_min=25.0))
        a = source("A")

        fed = template.with_inflows(a)

        assert template.inflows == () and template.upstream == ()
        assert fed.inflows == (a,) and fed.upstream == ("A",)
        assert fed is not template and fed.id == "R" and fed.reach is template.reach

    def test_a_node_can_be_in_two_networks(self):
        a = source("A")
        r = reach("R", a, LagReach(lag_min=25.0))

        first = RoutingNetwork(outlet(r, "ONE"))
        second = RoutingNetwork(outlet(r, "TWO"))

        assert first.outlet == "ONE" and second.outlet == "TWO"
        np.testing.assert_array_equal(
            first.route().hydrographs["R"].discharge_m3s,
            second.route().hydrographs["R"].discharge_m3s,
        )


def broken(case: str) -> list[Node]:
    """The nodes of a network that breaks one rule."""
    a, b = source("A"), source("B")
    if case == "bifurcation":
        r = reach("R", a, LagReach(10.0))
        return [a, r, outlet(junction("J", a, r))]
    if case == "no outlet":
        return [a, reach("R", a, LagReach(10.0))]
    if case == "two outlets":
        return [outlet(a, "OUT1"), outlet(b, "OUT2")]
    if case == "outlet with a downstream node":
        out = outlet(a)
        return [a, out, reach("R", out, LagReach(10.0))]
    if case == "disconnected":
        return [a, b, reach("R", b, LagReach(10.0)), outlet(a)]
    if case == "duplicate":
        return [a, source("a", SMALL), outlet(junction("J", a, source("a", SMALL)))]
    if case == "no inflow":
        return [a, outlet(junction("J"))]
    if case == "empty":
        return []
    raise KeyError(case)


class TestStructure:
    @pytest.mark.parametrize(
        ("case", "details"),
        [
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
            (
                "no inflow",
                {
                    "reason": "upstream_count",
                    "node_id": "J",
                    "type": "junction",
                    "found": 0,
                },
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

    def test_a_node_that_flows_nowhere_is_named_not_the_nodes_above_it(self):
        a, b = source("A"), source("B")
        r1 = reach("R1", b, LagReach(10.0))
        r2 = reach("R2", r1, LagReach(10.0))

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork([a, b, r1, r2, outlet(a)])

        assert caught.value.details == {
            "reason": "disconnected_node",
            "node_id": "R2",
            "n_disconnected": 3,
        }

    def test_a_node_that_has_no_inflow_yet_is_a_template_not_a_network(self):
        template = Channel("R", LagReach(10.0))

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(outlet(template))

        assert caught.value.details == {
            "reason": "upstream_count",
            "node_id": "R",
            "type": "reach",
            "found": 0,
        }

    def test_a_network_is_made_of_nodes(self):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(["A"])  # type: ignore[list-item]

        assert caught.value.details["reason"] == "type"


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
            Subcatchment(node_id, FLOOD)

        assert caught.value.details["reason"] == "invalid_id"

    @pytest.mark.parametrize("node_id", ["A", "R1.2", "seg-12", "_x", "Młynówka", "9"])
    def test_a_plain_id_is_accepted(self, node_id):
        assert Subcatchment(node_id, FLOOD).id == node_id
        assert Outlet("x" * MAX_ID_CHARS).id == "x" * MAX_ID_CHARS

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
            Subcatchment(node_id, FLOOD)

        assert caught.value.details == {"reason": "reserved_name", "node_id": node_id}
        assert "Windows" in caught.value.hint

    @pytest.mark.parametrize(
        "node_id",
        ["console", "com0", "com10", "lpt0", "aux1", "x.con", "con-1", "_nul"],
    )
    def test_a_name_that_only_looks_like_a_device_is_accepted(self, node_id):
        assert Subcatchment(node_id, FLOOD).id == node_id

    def test_the_types_are_the_five_of_the_plan(self):
        assert NODE_TYPES.names == (
            "subcatchment",
            "reach",
            "reservoir",
            "junction",
            "outlet",
        )

    @pytest.mark.parametrize(
        ("node", "found"),
        [
            (source("N"), 1),
            (Channel("N", LagReach(10.0)), 2),
            (Reservoir("N", ELEMENTS["level-pool"]), 2),
            (Outlet("N"), 2),
        ],
    )
    def test_a_node_takes_no_more_inflows_than_its_kind(self, node, found):
        inflows = [source("X"), source("Y")][:found]

        with pytest.raises(InvalidParameterError) as caught:
            node.with_inflows(*inflows)

        assert caught.value.details == {
            "reason": "upstream_count",
            "node_id": "N",
            "type": node.kind,
            "found": found,
        }

    def test_an_upstream_node_listed_twice_would_count_its_water_twice(self):
        a = source("A")

        with pytest.raises(InvalidParameterError) as caught:
            Junction("J", inflows=[a, a])

        assert caught.value.details == {
            "reason": "duplicate_upstream",
            "node_id": "J",
        }

    def test_an_inflow_must_be_a_node(self):
        with pytest.raises(InvalidParameterError) as caught:
            Junction("J", inflows=["A"])  # type: ignore[list-item]

        assert caught.value.details["reason"] == "type"
        assert caught.value.details["field"] == "inflows"

    @pytest.mark.parametrize(
        ("build", "field"),
        [
            (lambda: Subcatchment("A", "FLOOD"), "hydrograph"),  # type: ignore[arg-type]
            (lambda: Channel("R", "lag"), "reach"),  # type: ignore[arg-type]
        ],
    )
    def test_a_value_of_the_wrong_class_is_refused(self, build, field):
        with pytest.raises(InvalidParameterError) as caught:
            build()

        assert caught.value.details["reason"] == "type"
        assert caught.value.details["field"] == field

    def test_a_reservoir_routes_with_a_level_pool_only(self):
        with pytest.raises(InvalidParameterError) as caught:
            Reservoir("D", LagReach(10.0))

        assert caught.value.details == {
            "reason": "reservoir_model",
            "node_id": "D",
            "model": "LagReach",
        }

    @pytest.mark.parametrize(
        ("options", "option", "reason"),
        [
            ({"initial_outflow_m3s": -1.0}, "initial_outflow_m3s", "minimum"),
            ({"extend_min": -5.0}, "extend_min", "minimum"),
            ({"extend_min": float("inf")}, "extend_min", "not_finite"),
            ({"initial_outflow_m3s": "5"}, "initial_outflow_m3s", "type"),
        ],
    )
    def test_an_invalid_run_option_names_its_node(self, options, option, reason):
        with pytest.raises(InvalidParameterError) as caught:
            Channel("R", LagReach(10.0), **options)

        assert caught.value.details["option"] == option
        assert caught.value.details["reason"] == reason
        assert caught.value.details["node_id"] == "R"
        assert "Node 'R'" in str(caught.value)


class TestTimeAxes:
    def test_sources_with_different_steps_are_refused_not_resampled(self):
        coarse = Hydrograph.from_step([0.0, 5.0, 2.0, 0.0], 15.0)

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(outlet(junction("J", source("A"), source("B", coarse))))

        assert caught.value.details == {
            "reason": "timestep_mismatch",
            "nodes": ["A", "B"],
            "timesteps_min": [10.0, 15.0],
        }

    def test_sources_that_start_at_different_times_are_refused(self):
        late = Hydrograph.from_step([0.0, 5.0, 2.0, 0.0], 10.0, start_min=30.0)

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(outlet(junction("J", source("A"), source("B", late))))

        assert caught.value.details == {
            "reason": "start_mismatch",
            "nodes": ["A", "B"],
            "starts_min": [0.0, 30.0],
        }

    def test_sources_of_different_lengths_and_a_common_origin_are_fine(self):
        late = Hydrograph.from_step([1.0, 5.0, 2.0], 10.0, start_min=600.0)
        other = Hydrograph.from_step([0.0, 3.0, 2.0, 1.0, 1.0], 10.0, start_min=600.0)

        result = RoutingNetwork(
            outlet(junction("J", source("A", late), source("B", other)))
        ).route()

        assert result.hydrographs["J"].times_min.tolist() == [
            600.0 + 10.0 * i for i in range(5)
        ]


class TestRoutingErrors:
    def test_a_reach_that_fails_names_its_node(self):
        small_pond = LevelPoolReach(storage_m3=[0.0, 36000.0], outflow_m3s=[0.0, 10.0])
        flood = Hydrograph.from_step([0.0, 20.0, 20.0, 20.0, 20.0, 0.0], 60.0)

        with pytest.raises(CalculationError) as caught:
            RoutingNetwork(
                outlet(Reservoir("D", small_pond, inflow=source("A", flood)))
            ).route()

        assert caught.value.details["reason"] == "table_exceeded"
        assert caught.value.details["node_id"] == "D"
        assert "Node 'D'" in str(caught.value)
        assert caught.value.hint

    def test_a_run_that_the_hydrograph_does_not_allow_names_its_node(self):
        # an initial outflow above the table of the pond is known only to the run
        node = Reservoir("D", ELEMENTS["level-pool"], initial_outflow_m3s=500.0)

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork(outlet(node.with_inflows(source("A")))).route()

        assert caught.value.details["option"] == "initial_outflow_m3s"
        assert caught.value.details["node_id"] == "D"
