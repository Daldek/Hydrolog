"""Descriptions and positions of a network and of its nodes (ADR-0023).

Every node, whatever its kind, may have a ``description`` and a ``position`` in the
grid of the schematic, and the network a ``description`` of its own. The document keeps
them in its canonical form, after the fields of the kind; a value that breaks a rule is
refused with the reason of the plan (D3), the node and the field; and nothing that is
computed changes, down to the bytes of the result and of the tables.
"""

import json

import pytest

from hydrolog import testing
from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import (
    MAX_DESCRIPTION_CHARS,
    MAX_POSITION,
    NODE_TYPES,
    Channel,
    Hydrograph,
    LagReach,
    Node,
    NodeOutput,
    Outlet,
    Position,
    RoutingNetwork,
    Subcatchment,
)

from ._network_documents import FLOOD, TIMES, document, outlet, source

POND = {
    "storage_m3": [0.0, 30000.0, 90000.0, 180000.0],
    "outflow_m3s": [0.0, 10.0, 40.0, 100.0],
}
PLACES = {
    "A": (0, 1),
    "B": (1, 0),
    "R1": (1, 1),
    "J1": (2, 1),
    "D": (3, 1),
    "OUT": (4, 1),
}
WORDS = {
    "A": "Górny potok",
    "B": "Zlewnia leśna\nz dwoma dopływami",
    "R1": "Odcinek <b>poniżej</b> mostu & jazu",
    "J1": "Ujście",
    "D": "Suchy zbiornik powyżej Świerzawy",
    "OUT": "Profil zamykający",
}


def every_kind() -> dict:
    """A network of every kind of node: given and made subcatchments, a reach, a
    junction, a reservoir and the outlet."""
    return testing.network_document(
        testing.subcatchment("A", times_min=TIMES, discharge_m3s=FLOOD),
        testing.subcatchment(
            "B",
            watershed=testing.watershed(),
            runoff=testing.curve_number_runoff(tc_min=60.0),
            rainfall=testing.design_storm(),
        ),
        testing.reach("R1", "A", lag_min=25),
        testing.junction("J1", "R1", "B"),
        {"id": "D", "type": "reservoir", "from": ["J1"], **POND},
        testing.outlet("D"),
        name="Every kind",
    )


def placed(doc: dict) -> dict:
    """``doc`` with a description and a position on every node."""
    return {
        **doc,
        "nodes": [
            testing.placed(
                node, description=WORDS[node["id"]], position=PLACES[node["id"]]
            )
            for node in doc["nodes"]
        ],
    }


def text(doc) -> str:
    """The document as JSON text: the order of the keys shows."""
    return json.dumps(doc, ensure_ascii=False, allow_nan=False)


def refused(doc: dict) -> dict:
    """The ``details`` of the error that reading ``doc`` raises."""
    with pytest.raises(InvalidParameterError) as caught:
        RoutingNetwork.from_document(doc)
    details: dict = caught.value.details
    return details


class TestTheDocument:
    def test_every_kind_of_node_keeps_both_fields_after_the_fields_of_its_kind(self):
        bare = RoutingNetwork.from_document(every_kind()).to_document()

        written = RoutingNetwork.from_document(placed(every_kind())).to_document()

        for before, after in zip(bare["nodes"], written["nodes"], strict=True):
            x, y = PLACES[before["id"]]
            assert after == {
                **before,
                "description": WORDS[before["id"]],
                "position": {"x": x, "y": y},
            }
            assert list(after) == [*before, "description", "position"]

    def test_the_document_that_is_written_reads_back_to_the_same_text(self):
        written = RoutingNetwork.from_document(placed(every_kind())).to_document()

        again = RoutingNetwork.from_document(written).to_document()

        assert text(again) == text(written)

    def test_the_nodes_read_from_a_document_carry_the_values(self):
        network = RoutingNetwork.from_document(placed(every_kind()))

        for node in network.nodes:
            assert node.description == WORDS[node.id]
            assert node.position == Position(*PLACES[node.id])
            assert isinstance(node.position, Position)

    def test_the_description_of_the_network_follows_its_name(self):
        given = {**every_kind(), "description": "Sieć\nz opisem", "timestep_min": 10}

        network = RoutingNetwork.from_document(given)
        written = network.to_document()

        assert network.description == "Sieć\nz opisem"
        assert list(written) == [
            "schema",
            "name",
            "description",
            "timestep_min",
            "nodes",
        ]
        assert written["description"] == "Sieć\nz opisem"

    def test_a_whole_number_written_with_a_fraction_is_a_cell(self):
        doc = document(source("A", position={"x": 2.0, "y": -3}), outlet("A"))

        network = RoutingNetwork.from_document(doc)

        assert network.node("A").position == Position(2, -3)
        assert network.to_document()["nodes"][0]["position"] == {"x": 2, "y": -3}

    def test_the_bounds_and_the_longest_text_are_allowed(self):
        longest = "ż" * MAX_DESCRIPTION_CHARS
        corner = {"x": -MAX_POSITION, "y": MAX_POSITION}
        doc = document(source("A", description=longest, position=corner), outlet("A"))

        node = RoutingNetwork.from_document(doc).node("A")

        assert (node.description, node.position) == (longest, Position(-1000, 1000))

    def test_a_misspelt_field_is_still_refused(self):
        details = refused(document(source("A", descripton="x"), outlet("A")))

        assert details["reason"] == "unknown_field"
        assert (details["node_id"], details["field"]) == ("A", "descripton")


class TestNothingThatIsComputedChanges:
    def test_the_result_and_every_description_of_a_node_are_the_same(self):
        bare = RoutingNetwork.from_document(every_kind())
        given = RoutingNetwork.from_document(
            {**placed(every_kind()), "description": "Opis sieci"}
        )

        assert text(given.route().to_dict()) == text(bare.route().to_dict())
        for node in bare.nodes:
            assert given.node(node.id).describe() == node.describe()

    def test_the_command_gives_the_same_result_and_the_same_tables(self, tmp_path):
        outputs = {}
        for name, doc in (("bare", every_kind()), ("placed", placed(every_kind()))):
            envelope = run_command(
                "route network", {"network": doc, "output_dir": str(tmp_path / name)}
            ).to_dict()
            tables = {
                path.name: path.read_bytes()
                for path in sorted((tmp_path / name).iterdir())
            }
            outputs[name] = (text(envelope["result"]["nodes"]), tables)

        assert outputs["placed"] == outputs["bare"]
        assert set(outputs["bare"][1]) == {f"{node_id}.csv" for node_id in PLACES}


class TestTheNodes:
    def test_the_copies_have_the_fields_and_the_node_keeps_its_own(self):
        source_node = Subcatchment("A", Hydrograph(TIMES, FLOOD))
        reach = Channel("R", LagReach(lag_min=25), inflow=source_node)

        described = reach.with_description("Odcinek").with_position(Position(1, 0))

        assert (described.description, described.position) == ("Odcinek", (1, 0))
        assert (reach.description, reach.position) == (None, None)
        assert type(described) is Channel
        assert described.upstream == ("A",) and described.reach is reach.reach

    def test_none_removes_a_field_and_a_pair_or_a_list_is_a_position(self):
        node = Outlet("OUT").with_description("x").with_position((3, 4))

        assert node.with_description(None).description is None
        assert node.with_position(None).position is None
        assert node.with_position([5, -6]).position == Position(5, -6)
        assert isinstance(node.position, Position)

    def test_connecting_a_node_keeps_its_fields(self):
        source_node = Subcatchment("A", Hydrograph(TIMES, FLOOD))
        loose = Outlet("OUT").with_description("Koniec").with_position((2, 0))

        joined = loose.with_inflows(source_node)

        assert (joined.description, joined.position) == ("Koniec", (2, 0))

    def test_a_network_of_objects_writes_what_its_nodes_carry(self):
        source_node = Subcatchment("A", Hydrograph(TIMES, FLOOD)).with_position((0, 0))
        network = RoutingNetwork(
            Outlet("OUT", inflow=source_node).with_description("Koniec"),
            description="Mała sieć",
        )

        written = network.to_document()

        assert written["description"] == "Mała sieć"
        assert written["nodes"][0]["position"] == {"x": 0, "y": 0}
        assert written["nodes"][1]["description"] == "Koniec"
        assert "position" not in written["nodes"][1]

    def test_a_kind_from_another_package_carries_them_without_code_of_its_own(
        self, monkeypatch
    ):
        monkeypatch.setitem(NODE_TYPES._classes, "half", Half)
        doc = document(
            source("A"),
            {
                "id": "H",
                "type": "half",
                "from": ["A"],
                "description": "Połowa",
                "position": {"x": 1, "y": 0},
            },
            outlet("H"),
        )

        network = RoutingNetwork.from_document(doc)
        written = network.to_document()

        assert network.node("H").description == "Połowa"
        assert written["nodes"][1] == {
            "id": "H",
            "type": "half",
            "from": ["A"],
            "description": "Połowa",
            "position": {"x": 1, "y": 0},
        }


class Half(Node):
    """A kind of node that the library does not know: half of its inflow leaves."""

    kind = "half"

    def evaluate(self, inflows, context):
        flow = inflows[0]
        return NodeOutput(Hydrograph(flow.times_min, flow.discharge_m3s / 2))

    def describe(self, output=None):
        return []

    def document_fields(self):
        return {}

    @classmethod
    def read_document(cls, node_id, fields):
        return {}


DESCRIPTIONS = [
    pytest.param(12, "type", {}, id="not-text"),
    pytest.param("", "empty", {}, id="empty"),
    pytest.param(" \n\u00a0", "empty", {}, id="blank"),
    pytest.param(
        "x" * (MAX_DESCRIPTION_CHARS + 1),
        "too_long",
        {"max_length": 500, "length": 501},
        id="too-long",
    ),
    pytest.param("a\tb", "control_character", {"character": "U+0009"}, id="tab"),
    pytest.param("a\r\nb", "control_character", {"character": "U+000D"}, id="cr"),
    pytest.param("a\x7fb", "control_character", {"character": "U+007F"}, id="del"),
    pytest.param("a\x85b", "control_character", {"character": "U+0085"}, id="c1"),
]

POSITIONS = [
    pytest.param("0,0", "type", "position", {}, id="text"),
    pytest.param([1, 2], "type", "position", {}, id="list"),
    pytest.param({"y": 1}, "missing_field", "position.x", {}, id="no-x"),
    pytest.param({"x": 1, "y": None}, "missing_field", "position.y", {}, id="null-y"),
    pytest.param(
        {"x": 1, "y": 2, "z": 3},
        "unknown_field",
        "position.z",
        {"allowed": ["x", "y"]},
        id="third-key",
    ),
    pytest.param({"x": 1.5, "y": 0}, "type", "position.x", {}, id="fraction"),
    pytest.param({"x": True, "y": 0}, "type", "position.x", {}, id="boolean"),
    pytest.param({"x": "1", "y": 0}, "type", "position.x", {}, id="string"),
    pytest.param(
        {"x": -1001, "y": 0},
        "minimum",
        "position.x",
        {"minimum": -1000, "value": -1001},
        id="minimum",
    ),
    pytest.param(
        {"x": 0, "y": 1001},
        "maximum",
        "position.y",
        {"maximum": 1000, "value": 1001},
        id="maximum",
    ),
]


class TestTheReasons:
    @pytest.mark.parametrize(("value", "reason", "facts"), DESCRIPTIONS)
    def test_a_description_of_a_node(self, value, reason, facts):
        details = refused(document(source("A", description=value), outlet("A")))

        assert details["reason"] == reason
        assert (details["node_id"], details["field"]) == ("A", "description")
        assert facts.items() <= details.items()

    @pytest.mark.parametrize(("value", "reason", "facts"), DESCRIPTIONS)
    def test_a_description_of_the_network(self, value, reason, facts):
        doc = document(source("A"), outlet("A"), description=value)

        details = refused(doc)

        assert (details["reason"], details["field"]) == (reason, "description")
        assert "node_id" not in details
        assert facts.items() <= details.items()

    @pytest.mark.parametrize(("value", "reason", "field", "facts"), POSITIONS)
    def test_a_position(self, value, reason, field, facts):
        details = refused(document(outlet("A"), source("A", position=value)))

        assert (details["reason"], details["field"]) == (reason, field)
        assert details["node_id"] == "A"
        assert facts.items() <= details.items()

    @pytest.mark.parametrize(
        ("value", "reason", "field"),
        [
            ((1,), "type", "position"),
            ((1, 2, 3), "type", "position"),
            ("12", "type", "position"),
            ((1.5, 0), "type", "position.x"),
            ((0, -1001), "minimum", "position.y"),
        ],
    )
    def test_a_position_given_to_a_node(self, value, reason, field):
        with pytest.raises(InvalidParameterError) as caught:
            Outlet("OUT").with_position(value)

        details = caught.value.details
        assert (details["reason"], details["field"], details["node_id"]) == (
            reason,
            field,
            "OUT",
        )

    def test_a_description_given_to_a_node_or_a_network(self):
        with pytest.raises(InvalidParameterError) as node:
            Outlet("OUT").with_description("a\tb")
        with pytest.raises(InvalidParameterError) as network:
            RoutingNetwork(
                Outlet("OUT", inflow=Subcatchment("A", Hydrograph(TIMES, FLOOD))),
                description=" ",
            )

        assert node.value.details["reason"] == "control_character"
        assert node.value.details["node_id"] == "OUT"
        assert network.value.details["reason"] == "empty"
        assert "node_id" not in network.value.details
