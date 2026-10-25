"""Tests of the schematic of a network: the picture and the document (ADR-0013).

The picture is judged by what it must be: every segment at 0, 45 or 90 degrees, no two
edges crossing or overlapping, the main stem straight and the larger branch, the
tributaries on alternating sides and one unit apart. ``_schematic_checks`` looks at the
cells of the picture without using the layout, on random trees of every shape. The
document is judged against the result it carries: its values are those of the
``NetworkResult``, and the picture is the same whether or not there is one.
"""

import json
import random

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import RoutingNetwork
from hydrolog.routing._layout import LABEL_SIDES, layout
from hydrolog.routing.schematic import SCHEMA
from hydrolog.testing import example_network, example_network_document

from ._schematic_checks import random_tree, violations
from ._schematic_networks import network_of

SHAPES = [
    pytest.param(size, seed, fan_in, deep, id=f"n{size}-s{seed}-f{fan_in}-d{deep}")
    for size in (2, 3, 6, 13, 30, 70)
    for seed in range(4)
    for fan_in, deep in ((1, 0.0), (2, 0.0), (3, 0.5), (5, 0.2), (12, 0.0))
]


def drawn(size, seed, fan_in, deep, **options):
    root, inflows = random_tree(size, seed, fan_in=fan_in, deep=deep)
    return root, inflows, layout(root, inflows, **options)


# --- the picture ---------------------------------------------------------------------


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES)
def test_no_picture_of_a_tree_has_a_crossing_an_overlap_or_a_slanted_segment(
    size, seed, fan_in, deep
):
    root, inflows, picture = drawn(size, seed, fan_in, deep)

    assert violations(root, inflows, picture) == []


def test_a_chain_is_one_straight_line_with_a_unit_between_nodes():
    inflows = {"OUT": ["c1"], "c1": ["c2"], "c2": ["c3"], "c3": []}

    picture = layout("OUT", inflows)

    assert picture.positions == {
        "OUT": (3, 0),
        "c1": (2, 0),
        "c2": (1, 0),
        "c3": (0, 0),
    }
    assert [line.nodes for line in picture.lines] == [("c3", "c2", "c1", "OUT")]
    assert picture.routes["c3"] == ((0, 0), (1, 0))


def test_the_branch_with_more_nodes_is_the_main_stem_and_the_other_a_tributary():
    inflows = {"R": ["T", "S"], "S": ["S1"], "S1": ["S2"], "T": [], "S2": []}

    picture = layout("R", inflows)

    stem, tributary = picture.lines
    assert stem.nodes == ("S2", "S1", "S", "R")
    assert (tributary.nodes, tributary.joins, tributary.parent) == (("T",), "R", 0)


def test_branches_of_the_same_size_go_by_id():
    picture = layout("R", {"R": ["B", "A"], "A": [], "B": []})

    assert picture.lines[0].nodes == ("A", "R")
    assert picture.lines[1].nodes == ("B",)


def test_the_area_decides_when_it_is_given_and_the_count_of_nodes_when_it_is_not():
    inflows = {"R": ["A", "B"], "A": ["A1", "A2"], "A1": [], "A2": [], "B": []}

    by_nodes = layout("R", inflows)
    by_area = layout("R", inflows, weight={"A1": 1.0, "A2": 1.0, "B": 10.0})

    assert by_nodes.lines[0].nodes[-2:] == ("A", "R")
    assert by_area.lines[0].nodes == ("B", "R")
    assert violations("R", inflows, by_area) == []


def test_areas_that_are_equal_to_rounding_are_a_tie():
    inflows = {"R": ["B", "A"], "A": ["A1", "A2"], "B": ["B1"]}
    weight = {"A1": 0.1, "A2": 0.2, "B1": 0.3}  # 0.1 + 0.2 is not 0.3 in floating point

    picture = layout("R", inflows, weight=weight)

    # equal areas: the branch with more nodes (A, A1, A2) is the stem
    assert picture.lines[0].nodes[-2:] == ("A", "R")


def test_a_declared_stem_is_followed_and_goes_on_by_size_above_its_farthest_node():
    inflows = {"R": ["A", "B"], "A": ["A1", "A2"], "A2": ["A3"], "B": ["B1"]}

    assert layout("R", inflows).lines[0].nodes == ("A3", "A2", "A", "R")
    assert layout("R", inflows, main_stem=["B"]).lines[0].nodes == ("B1", "B", "R")
    assert layout("R", inflows, main_stem=["A", "R"]).lines[0].nodes == (
        "A3",
        "A2",
        "A",
        "R",
    )
    through = layout("R", inflows, main_stem=["A1", "R"])
    assert through.lines[0].nodes == ("A1", "A", "R")
    assert violations("R", inflows, through) == []


def test_a_declared_main_stem_must_name_nodes_on_one_path():
    inflows = {"R": ["A", "B"], "A": ["A1"], "B": []}

    with pytest.raises(InvalidParameterError) as unknown:
        layout("R", inflows, main_stem=["Z"])
    with pytest.raises(InvalidParameterError) as split:
        layout("R", inflows, main_stem=["A1", "B"])

    assert unknown.value.details["reason"] == "unknown_node"
    assert unknown.value.details["node_id"] == "Z"
    assert split.value.details["reason"] == "main_stem_not_a_path"
    assert split.value.details["node_id"] == "B"


def test_a_picture_is_the_same_whatever_the_order_of_the_inflows_and_of_the_nodes():
    root, inflows = random_tree(40, 3, fan_in=4, deep=0.3)
    mixed = random.Random(5)
    shuffled = {
        node: random.Random(node).sample(ups, len(ups))
        for node, ups in mixed.sample(sorted(inflows.items()), len(inflows))
    }

    weight = {node: float(len(node)) for node in inflows if not inflows[node]}
    assert layout(root, inflows) == layout(root, inflows)
    assert layout(root, shuffled) == layout(root, inflows)
    assert layout(root, shuffled, weight=weight) == layout(root, inflows, weight=weight)


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES[::7])
def test_the_main_stem_is_a_row_and_its_tributaries_take_sides_in_turn(
    size, seed, fan_in, deep
):
    _, _, picture = drawn(size, seed, fan_in, deep)

    stem = picture.lines[0]
    sides = [
        -1 if line.row < stem.row else 1
        for line in picture.lines[1:]
        if line.parent == 0
    ]
    assert {picture.positions[node][1] for node in stem.nodes} == {stem.row}
    assert all(first != second for first, second in zip(sides, sides[1:], strict=False))
    assert sides[:1] in ([], [-1])


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES[::5])
def test_nodes_of_a_line_are_one_unit_apart_unless_taps_make_room_for_more_inflows(
    size, seed, fan_in, deep
):
    root, inflows, picture = drawn(size, seed, fan_in, deep)

    for line in picture.lines:
        slots = 2 if line.parent is None else 1
        for before, node in zip(line.nodes, line.nodes[1:], strict=False):
            gap = picture.positions[node][0] - picture.positions[before][0]
            side_inflows = len(inflows[node]) - 1
            assert gap >= 1
            if side_inflows <= slots:
                assert gap == 1


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES[::3])
def test_a_tributary_joins_at_45_degrees_after_a_vertical_leg(size, seed, fan_in, deep):
    _, _, picture = drawn(size, seed, fan_in, deep)

    for line in picture.lines[1:]:
        route = picture.routes[line.nodes[-1]]
        segments = [
            (end[0] - start[0], end[1] - start[1])
            for start, end in zip(route, route[1:], strict=False)
        ]
        diagonals = [i for i, (dx, dy) in enumerate(segments) if dx != 0 and dy != 0]
        assert len(diagonals) == 1
        assert abs(segments[diagonals[0]][0]) == abs(segments[diagonals[0]][1]) == 1
        # what comes before the diagonal is the vertical leg, what follows runs along
        # the line it joins
        assert all(dx == 0 for dx, _ in segments[: diagonals[0]])
        assert all(dy == 0 for _, dy in segments[diagonals[0] + 1 :])


def test_a_node_with_many_inflows_takes_its_lines_at_taps_and_draws_all_of_them():
    inflows = {"OUT": ["J"], "J": [f"s{i}" for i in range(9)]}
    inflows.update({f"s{i}": [] for i in range(9)})

    picture = layout("OUT", inflows)

    assert violations("OUT", inflows, picture) == []
    assert len(picture.lines) == 9


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES[::9])
def test_every_node_has_a_label_on_one_of_the_eight_sides(size, seed, fan_in, deep):
    _, _, picture = drawn(size, seed, fan_in, deep)

    assert set(picture.labels) == set(picture.positions)
    assert set(picture.labels.values()) <= set(LABEL_SIDES)


def test_a_very_long_line_and_a_very_bushy_tree_are_drawn_without_recursion():
    chain = {
        "OUT": ["c0"],
        **{f"c{i}": [f"c{i + 1}"] for i in range(2999)},
        "c2999": [],
    }
    comb = {"OUT": ["c0"]}
    for i in range(400):
        comb[f"c{i}"] = [f"c{i + 1}", f"l{i}"] if i < 399 else [f"l{i}"]

    assert layout("OUT", chain).width == 3000
    assert violations("OUT", comb, layout("OUT", comb)) == []


def test_a_node_that_two_nodes_flow_into_is_not_a_tree():
    with pytest.raises(ValueError, match="flows into two nodes"):
        layout("R", {"R": ["A", "B"], "A": ["X"], "B": ["X"]})


# --- the document --------------------------------------------------------------------


def test_the_document_of_the_example_network_with_its_result():
    network = example_network()
    result = network.route()

    document = network.schematic(result)

    assert document["schema"] == SCHEMA == "hydrolog-network-schematic/1"
    assert document["name"] == "Three subcatchments"
    assert document["has_result"] is True
    assert document["outlet"] == "OUT"
    assert document["grid"] == {"width": 5, "height": 2}
    positions = {node["id"]: (node["x"], node["y"]) for node in document["nodes"]}
    # the stem is A, R_A, J1, R_J1, J2, OUT on row 1; B joins J1 from above and C joins
    # J2 from below
    assert positions == {
        "A": (0, 1),
        "B": (1, 0),
        "C": (3, 2),
        "R_A": (1, 1),
        "J1": (2, 1),
        "R_J1": (3, 1),
        "J2": (4, 1),
        "OUT": (5, 1),
    }
    assert [line["role"] for line in document["lines"]] == [
        "main",
        "tributary",
        "tributary",
    ]
    assert document["lines"][0]["nodes"] == ["A", "R_A", "J1", "R_J1", "J2", "OUT"]
    assert document["lines"][1] == {
        "index": 1,
        "role": "tributary",
        "nodes": ["B"],
        "joins": "J1",
    }
    edges = {(edge["from"], edge["to"]): edge["points"] for edge in document["edges"]}
    assert edges[("B", "J1")] == [[1, 0], [2, 1]]
    assert edges[("C", "J2")] == [[3, 2], [4, 1]]
    assert edges[("R_A", "J1")] == [[1, 1], [2, 1]]


def test_the_values_of_a_node_are_those_of_the_result():
    network = example_network()
    result = network.route()

    document = network.schematic(result)

    assert [node["id"] for node in document["nodes"]] == list(network.order)
    for node in document["nodes"]:
        summary = result.nodes[node["id"]]
        assert node["type"] == summary.type
        assert node["peak_m3s"] == summary.peak_m3s
        assert node["time_to_peak_min"] == summary.time_to_peak_min
        assert node["volume_m3"] == summary.volume_m3
        assert node["parameters"] == [item.to_dict() for item in summary.parameters]
        assert node["notices"] == [
            {"level": n.level, "code": n.code, "message": n.message}
            for n in summary.notices
        ]
    sources = {
        item["source"] for node in document["nodes"] for item in node["parameters"]
    }
    assert sources == {"given", "computed", "default"}


def test_without_a_result_a_node_carries_what_describe_says_and_no_values():
    network = example_network()

    document = network.schematic()
    run = network.schematic(network.route())

    assert document["has_result"] is False
    for node in document["nodes"]:
        assert "peak_m3s" not in node
        assert "notices" not in node
        described = network.node(node["id"]).describe()
        assert node["parameters"] == [item.to_dict() for item in described]
    # the run adds what it used and nobody gave: the initial outflow and the tail
    names = {
        label["id"]: {item["name"] for item in label["parameters"]}
        for label in document["nodes"]
    }
    used = {
        label["id"]: {item["name"] for item in label["parameters"]}
        for label in run["nodes"]
    }
    assert names["R_A"] < used["R_A"]
    assert {"initial_outflow_m3s", "extend_min"} <= used["R_A"] - names["R_A"]


def test_the_picture_is_the_same_with_and_without_a_result():
    network = example_network()
    plain = network.schematic()
    full = network.schematic(network.route())

    def picture(document):
        return (
            document["grid"],
            document["lines"],
            document["edges"],
            [
                (n["id"], n["x"], n["y"], n["line"], n["label"])
                for n in document["nodes"]
            ],
        )

    assert picture(plain) == picture(full)


def test_a_result_of_another_network_is_refused():
    network = example_network()
    other = network_of("OUT", {"OUT": ["a"], "a": []}).route()

    with pytest.raises(InvalidParameterError) as error:
        network.schematic(other)

    assert error.value.details["reason"] == "result_mismatch"


def test_the_document_is_json_native_and_does_not_change_when_read_again():
    document = example_network().schematic(example_network().route())

    assert json.loads(json.dumps(document, allow_nan=False)) == document


def test_a_network_that_is_read_from_its_document_has_the_picture_of_the_network():
    network = example_network()
    nodes = list(reversed(example_network_document()["nodes"]))
    again = RoutingNetwork.from_document({**example_network_document(), "nodes": nodes})

    assert again.schematic(again.route()) == network.schematic(network.route())


def test_edges_are_the_inflows_of_the_network_and_end_at_the_node_below():
    network = example_network()

    document = network.schematic()

    ends = {(edge["from"], edge["to"]) for edge in document["edges"]}
    assert ends == {(up, node.id) for node in network.nodes for up in node.upstream}
    places = {node["id"]: [node["x"], node["y"]] for node in document["nodes"]}
    for edge in document["edges"]:
        assert edge["points"][0] == places[edge["from"]]
        assert edge["points"][-1] == places[edge["to"]]


def test_the_stem_follows_the_larger_area_and_the_count_of_nodes_without_areas():
    inflows = {"R": ["A", "B"], "A": ["A1", "A2"], "A1": [], "A2": [], "B": []}
    areas = {"A1": 1.0, "A2": 1.0, "B": 10.0}

    by_area = network_of("R", inflows, areas).schematic()
    given = network_of("R", inflows, {"A1": 1.0, "A2": 1.0, "B": None}).schematic()
    none = network_of("R", inflows).schematic()

    assert by_area["lines"][0]["nodes"] == ["B", "R", "END"]
    # a headwater that is given its hydrograph has no area: the nodes are counted
    assert given["lines"][0]["nodes"][-3:] == ["A", "R", "END"]
    assert none["lines"][0]["nodes"][-3:] == ["A", "R", "END"]


def test_a_main_stem_can_be_declared_for_the_network():
    network = example_network()

    default = network.schematic()
    declared = network.schematic(main_stem="C")
    listed = network.schematic(main_stem=["B", "J1"])

    assert default["lines"][0]["nodes"] == ["A", "R_A", "J1", "R_J1", "J2", "OUT"]
    assert declared["lines"][0]["nodes"] == ["C", "J2", "OUT"]
    assert listed["lines"][0]["nodes"] == ["B", "J1", "R_J1", "J2", "OUT"]
    with pytest.raises(InvalidParameterError) as unknown:
        network.schematic(main_stem="nothing")
    with pytest.raises(InvalidParameterError) as kind:
        network.schematic(main_stem=[1])  # type: ignore[list-item]
    assert unknown.value.details["reason"] == "unknown_node"
    assert kind.value.details["reason"] == "type"


@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES[::11])
def test_the_picture_of_a_network_is_right_and_has_every_node_once(
    size, seed, fan_in, deep
):
    root, inflows = random_tree(size, seed, fan_in=fan_in, deep=deep)
    network = network_of(root, inflows)

    document = network.schematic(network.route())

    nodes = [node["id"] for node in document["nodes"]]
    assert sorted(nodes) == sorted(network.order)
    assert document["grid"]["width"] == max(node["x"] for node in document["nodes"])
    assert document["grid"]["height"] == max(node["y"] for node in document["nodes"])
    assert sum(len(line["nodes"]) for line in document["lines"]) == len(nodes)
