"""Tests of reading a network from its document, in the library.

The document names the nodes by id; the objects link by reference. A network read from a
document must be the one that is built by hand, and what only a document can get wrong
(an id that is not there, a cycle, a field that a type does not take) arrives with the
reasons of the plan. New kinds of node and of reach are registered, and the document
finds them without any change of the code that reads it.
"""

import itertools

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import (
    NODE_TYPES,
    REACH_METHODS,
    Channel,
    Hydrograph,
    Junction,
    LagReach,
    MuskingumReach,
    Node,
    NodeOutput,
    Outlet,
    Reach,
    RoutingNetwork,
    Subcatchment,
)
from hydrolog.routing.parameters import parameter
from hydrolog.routing.reach import ReachRun

from ._network_documents import (
    FLOOD,
    SMALL,
    TIMES,
    document,
    junction,
    outlet,
    reach,
    source,
)


def by_hand() -> RoutingNetwork:
    """The network of ``confluence`` of the document helpers, made of objects."""
    a = Subcatchment("A", Hydrograph(TIMES, FLOOD))
    b = Subcatchment("B", Hydrograph(TIMES, SMALL))
    r = Channel("R", LagReach(lag_min=25), inflow=a)
    return RoutingNetwork(Outlet("OUT", inflow=Junction("J", inflows=[r, b])))


CONFLUENCE = document(
    source("A"),
    source("B", SMALL),
    reach("R", "A"),
    junction("J", "R", "B"),
    outlet("J"),
)


class TestTheSameNetwork:
    def test_a_document_gives_what_the_objects_give(self):
        read = RoutingNetwork.from_document(CONFLUENCE)
        built = by_hand()

        assert read.order == built.order == ("A", "B", "R", "J", "OUT")
        for node_id, hydrograph in built.route().hydrographs.items():
            np.testing.assert_array_equal(
                read.route().hydrographs[node_id].discharge_m3s,
                hydrograph.discharge_m3s,
            )

    def test_the_order_of_the_nodes_in_the_document_changes_nothing(self):
        nodes = CONFLUENCE["nodes"]
        reference = RoutingNetwork.from_document(CONFLUENCE).route()

        for permutation in itertools.permutations(nodes):
            read = RoutingNetwork.from_document(document(*permutation)).route()

            assert read.order == reference.order
            np.testing.assert_array_equal(
                read.hydrographs["OUT"].discharge_m3s,
                reference.hydrographs["OUT"].discharge_m3s,
            )

    def test_a_node_of_a_document_is_the_node_of_its_class(self):
        network = RoutingNetwork.from_document(CONFLUENCE)

        kinds = {node.id: type(node) for node in network.nodes}
        assert kinds == {
            "A": Subcatchment,
            "B": Subcatchment,
            "R": Channel,
            "J": Junction,
            "OUT": Outlet,
        }
        assert network.node("J").upstream == ("R", "B")

    def test_a_name_is_read(self):
        assert RoutingNetwork.from_document({**CONFLUENCE, "name": "x"}).name == "x"


class TestWhatOnlyADocumentCanGetWrong:
    @pytest.mark.parametrize(
        ("nodes", "details"),
        [
            (
                [source("A"), reach("R", "X"), outlet("R")],
                {
                    "reason": "unknown_upstream",
                    "node_id": "R",
                    "upstream_id": "X",
                    "n_unknown": 1,
                },
            ),
            (
                [source("A"), junction("J", "A", "X", "Y"), outlet("J")],
                {
                    "reason": "unknown_upstream",
                    "node_id": "J",
                    "upstream_id": "X",
                    "n_unknown": 2,
                },
            ),
            (
                [
                    source("A"),
                    reach("R2", "R1"),
                    reach("R1", "R2"),
                    junction("J", "A", "R1"),
                    outlet("J"),
                ],
                {"reason": "cycle", "nodes": ["R1", "R2"]},
            ),
            (
                [source("A"), reach("R", "R"), outlet("R")],
                {"reason": "cycle", "nodes": ["R"]},
            ),
        ],
    )
    def test_an_id_that_is_not_there_and_a_cycle_are_refused(self, nodes, details):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(*nodes))

        assert caught.value.details == details

    def test_the_cycle_is_listed_in_flow_order_whatever_the_order_of_the_nodes(self):
        nodes = [
            source("A"),
            reach("R2", "R1"),
            reach("R1", "R2"),
            junction("J", "A", "R1"),
            outlet("J"),
        ]

        for permutation in itertools.permutations(nodes):
            with pytest.raises(InvalidParameterError) as caught:
                RoutingNetwork.from_document(document(*permutation))

            assert caught.value.details["nodes"] == ["R1", "R2"]
        assert "'R1' -> 'R2' -> 'R1'" in str(caught.value)

    @pytest.mark.parametrize(
        ("nodes", "details"),
        [
            (
                [source("A"), reach("R", "A", **{"from": ["A", "A"]}), outlet("R")],
                {
                    "reason": "upstream_count",
                    "node_id": "R",
                    "type": "reach",
                    "found": 2,
                },
            ),
            (
                [{**source("A"), "from": ["A"]}, outlet("A")],
                {
                    "reason": "upstream_count",
                    "node_id": "A",
                    "type": "subcatchment",
                    "found": 1,
                },
            ),
            (
                [source("A"), junction("J", "A", "A"), outlet("J")],
                {"reason": "duplicate_upstream", "node_id": "J"},
            ),
            (
                [source("A"), source("a"), outlet("A")],
                {"reason": "duplicate_node", "node_id": "a", "other_id": "A"},
            ),
        ],
    )
    def test_the_count_of_the_inflows_and_the_ids_are_checked(self, nodes, details):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(*nodes))

        assert caught.value.details == details

    @pytest.mark.parametrize(
        ("listed", "reason"),
        [("b/c", "invalid_id"), ("nul", "reserved_name"), (7, "type")],
    )
    def test_an_id_in_from_is_checked_like_an_id(self, listed, reason):
        nodes = [source("A"), junction("J", "A", listed), outlet("J")]

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(*nodes))

        assert caught.value.details["reason"] == reason

    def test_the_rules_of_the_network_apply_to_a_document_too(self):
        nodes = [source("A"), reach("R", "A"), outlet("R"), source("B")]

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(*nodes))

        assert caught.value.details["reason"] == "disconnected_node"
        assert caught.value.details["node_id"] == "B"


class TestTheFieldsOfAType:
    def test_an_unknown_type_lists_the_registered_ones(self):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document({"id": "A", "type": "lake"}))

        assert caught.value.details == {
            "reason": "unknown_type",
            "node_id": "A",
            "value": "lake",
            "allowed": list(NODE_TYPES.names),
        }

    @pytest.mark.parametrize(
        ("node", "field"),
        [
            (source("A", lag_min=5), "lag_min"),
            ({**outlet("A"), "lag_min": 5}, "lag_min"),
            ({**reach("R", "A"), "k_min": 5}, "k_min"),
            ({**reach("R", "A"), "times_min": [0, 10]}, "times_min"),
            (
                {
                    "id": "D",
                    "type": "reservoir",
                    "from": ["A"],
                    "method": "lag",
                    "lag_min": 5,
                },
                "method",
            ),
        ],
    )
    def test_a_field_that_the_type_does_not_take_is_refused(self, node, field):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(source("A"), node, outlet("A")))

        assert caught.value.details["reason"] == "unknown_field"
        assert caught.value.details["field"] == field

    @pytest.mark.parametrize(
        ("node", "field"),
        [
            ({"id": "A", "type": "subcatchment"}, "discharge_m3s"),
            (
                {"id": "A", "type": "subcatchment", "times_min": [0, 10]},
                "discharge_m3s",
            ),
            ({"id": "A", "type": "subcatchment", "discharge_m3s": [1, 2]}, "times_min"),
            ({**reach("R", "A"), "method": None}, "method"),
            ({**reach("R", "A"), "lag_min": None}, "lag_min"),
            ({"id": "D", "type": "reservoir", "from": ["A"]}, "storage_m3"),
        ],
    )
    def test_a_field_that_the_type_needs_is_asked_for(self, node, field):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(node))

        assert caught.value.details["reason"] == "missing_field"
        assert caught.value.details["field"] == field
        assert caught.value.details["node_id"] in {"A", "R", "D"}

    def test_an_unknown_method_lists_the_registered_ones(self):
        node = reach("R", "A", method="kinematic")

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(source("A"), node, outlet("R")))

        assert caught.value.details["reason"] == "unknown_method"
        assert caught.value.details["allowed"] == list(REACH_METHODS.names)

    def test_a_value_that_the_element_refuses_names_the_node(self):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(
                document(source("A"), reach("R", "A", lag_min=-1), outlet("R"))
            )

        assert caught.value.details["option"] == "lag_min"
        assert caught.value.details["node_id"] == "R"
        assert "Node 'R'" in str(caught.value)

    def test_a_hydrograph_that_is_not_one_names_the_node(self):
        node = source("A", discharge=[1, -2, 3, 4, 5, 6, 7, 8])

        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(document(node, outlet("A")))

        assert caught.value.details["option"] == "discharge_m3s"
        assert caught.value.details["reason"] == "negative"
        assert caught.value.details["node_id"] == "A"

    def test_from_must_be_a_list_of_ids(self):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(
                document(source("A"), reach("R", "A", **{"from": "A"}), outlet("R"))
            )

        assert caught.value.details["reason"] == "type"
        assert caught.value.details["field"] == "from"

    @pytest.mark.parametrize(
        ("content", "reason", "facts"),
        [
            ([1, 2], "shape", {}),
            ({"schema": "hydrolog-network/1"}, "missing_field", {"field": "nodes"}),
            (
                {"schema": "hydrolog-network/1", "nodes": {"A": 1}},
                "type",
                {"field": "nodes"},
            ),
            (
                {"schema": "hydrolog-network/1", "nodes": [5]},
                "shape",
                {"index": 0},
            ),
            (
                {"schema": "hydrolog-network/1", "nodes": [], "color": "blue"},
                "unknown_field",
                {"field": "color"},
            ),
            ({"nodes": []}, "missing_field", {"field": "schema"}),
            (
                {"schema": "hydrolog-network/2", "nodes": []},
                "unknown_schema",
                {"expected": "hydrolog-network/1"},
            ),
            (
                {"schema": "hydrolog-network/1", "name": " ", "nodes": []},
                "type",
                {"field": "name"},
            ),
            ({"schema": "hydrolog-network/1", "nodes": []}, "empty", {}),
        ],
    )
    def test_the_document_itself_is_checked(self, content, reason, facts):
        with pytest.raises(InvalidParameterError) as caught:
            RoutingNetwork.from_document(content)

        assert caught.value.details["reason"] == reason
        for key, value in facts.items():
            assert caught.value.details[key] == value


class TestThePrepareHook:
    def test_it_is_called_for_every_node_with_its_id_and_type(self):
        seen: list[tuple[str, str]] = []

        def prepare(node_id, kind, entry):
            seen.append((node_id, kind))
            return entry

        RoutingNetwork.from_document(CONFLUENCE, prepare=prepare)

        assert seen == [
            ("A", "subcatchment"),
            ("B", "subcatchment"),
            ("R", "reach"),
            ("J", "junction"),
            ("OUT", "outlet"),
        ]

    def test_the_entry_it_returns_is_the_one_that_is_read(self):
        def prepare(node_id, kind, entry):
            if node_id == "R":
                return {**entry, "lag_min": 50}
            return entry

        slow = RoutingNetwork.from_document(CONFLUENCE, prepare=prepare)

        node = slow.node("R")
        assert isinstance(node, Channel) and node.reach.lag_min == 50.0

    def test_an_error_it_raises_is_not_changed(self):
        class Refused(Exception):
            pass

        def prepare(node_id, kind, entry):
            raise Refused(node_id)

        with pytest.raises(Refused):
            RoutingNetwork.from_document(CONFLUENCE, prepare=prepare)


class Share(Node):
    """A node of a kind the library does not know: it lets a share of its inflow by."""

    kind = "share"

    def __init__(self, id, fraction, inflow=None):
        super().__init__(id, () if inflow is None else (inflow,))
        self.fraction = fraction

    def evaluate(self, inflows, context):
        flow = inflows[0]
        return NodeOutput(
            Hydrograph(flow.times_min, flow.discharge_m3s * self.fraction)
        )

    def describe(self, output=None):
        return [parameter("fraction", self.fraction, "given")]

    @classmethod
    def read_document(cls, node_id, fields):
        return {"fraction": fields["fraction"]}


class Halving(Reach):
    """A routing method the library does not know: a share of the inflow leaves."""

    model = "share-of-inflow"

    def __init__(self, fraction):
        self.fraction = fraction

    def options(self):
        return {"fraction": self.fraction}

    def _run(self, inflow, initial_outflow_m3s):
        return ReachRun(
            outflow_m3s=inflow.discharge_m3s * self.fraction,
            storage_start_m3=0.0,
            storage_end_m3=0.0,
            storage_steady_m3=0.0,
            parameters={"fraction": self.fraction},
        )


class TestExtending:
    def test_a_new_kind_of_node_is_a_registry_entry_and_nothing_else(self, monkeypatch):
        monkeypatch.setitem(NODE_TYPES._classes, "share", Share)
        nodes = [
            source("A"),
            {"id": "S", "type": "share", "from": ["A"], "fraction": 0.25},
            outlet("S"),
        ]

        network = RoutingNetwork.from_document(document(*nodes))
        result = network.route()

        np.testing.assert_allclose(
            result.hydrographs["OUT"].discharge_m3s, np.array(FLOOD) * 0.25
        )
        assert result.nodes["S"].type == "share"
        assert [p.name for p in result.nodes["S"].parameters] == ["fraction"]

    def test_a_new_method_of_a_reach_is_a_registry_entry_and_nothing_else(
        self, monkeypatch
    ):
        monkeypatch.setitem(REACH_METHODS._classes, "share-of-inflow", Halving)
        node = {
            "id": "R",
            "type": "reach",
            "from": ["A"],
            "method": "share-of-inflow",
            "fraction": 0.5,
        }

        result = RoutingNetwork.from_document(
            document(source("A"), node, outlet("R"))
        ).route()

        np.testing.assert_allclose(
            result.hydrographs["R"].discharge_m3s[: len(FLOOD)], np.array(FLOOD) * 0.5
        )
        assert result.runs["R"].model == "share-of-inflow"

    def test_a_class_without_a_name_is_not_registered(self):
        class Nameless(Node):
            pass

        with pytest.raises(TypeError):
            NODE_TYPES.register(Nameless)

    def test_a_name_is_taken_once(self):
        class Another(Node):
            kind = "outlet"

        with pytest.raises(ValueError, match="already registered"):
            NODE_TYPES.register(Another)

    def test_the_name_of_a_class_is_found_through_its_parents(self):
        class Wider(MuskingumReach):
            pass

        assert REACH_METHODS.name_of(Wider(k_min=10.0, x=0.2)) == "muskingum"
        with pytest.raises(InvalidParameterError) as caught:
            REACH_METHODS.name_of(object())
        assert caught.value.details["reason"] == "unregistered"
