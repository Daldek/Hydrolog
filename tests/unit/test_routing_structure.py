"""The structure of a network alone: its reader and its schematic (ADR-0025).

``structure_schematic`` lays a draft out from the ids, types and links of its nodes and
the areas of its headwaters. For every network that the full reader accepts, the
picture is the computed picture of that network: on random trees, with and without
areas and with a declared main stem. A document with one problem of its structure gets
the error that ``RoutingNetwork.from_document`` gives, because both readers share one
check of the graph; the other fields of a node may be missing or wrong, and positions
are ignored.
"""

import copy
import random
import warnings
from typing import Any

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing import RoutingNetwork, structure_schematic
from hydrolog.routing.document import read_structure
from hydrolog.routing.schematic import SCHEMA
from hydrolog.testing import example_network_document

from ._network_documents import (
    STRUCTURE_CORPUS,
    document,
    junction,
    outlet,
    reach,
    source,
)
from ._schematic_checks import random_tree
from ._schematic_networks import network_of

SHAPES = [
    pytest.param(size, seed, fan_in, deep, id=f"n{size}-s{seed}-f{fan_in}-d{deep}")
    for size in (2, 3, 6, 13, 30, 70)
    for seed in range(3)
    for fan_in, deep in ((1, 0.0), (3, 0.5), (12, 0.0))
]

# Nogat's example of a network hand-off (plan 2026-11-10-node-provenance-in-handoff):
# Hydrograf gives the reach R1 its length and slope, not its section
NOGAT_EXAMPLE: dict[str, Any] = {
    "schema": "hydrolog-network/1",
    "name": "Kamiennik — Świerzawa, sieć 3 zlewni",
    "timestep_min": 10,
    "rainfall": {
        "kind": "design",
        "hietogram_type": "beta",
        "total_mm": 105.0,
        "duration_min": 720.0,
        "alpha": 2.0,
        "beta": 5.0,
    },
    "nodes": [
        {
            "id": "Z1",
            "type": "subcatchment",
            "watershed": {
                "area_km2": 20.1,
                "cn": 63,
                "flow_path_length_km": 9.84,
                "flow_path_slope_m_per_m": 0.0187,
            },
            "runoff": {
                "model": "curve-number",
                "tc_method": "kirpich",
                "amc": "II",
                "uh_model": "scs",
            },
        },
        {
            "id": "Z2",
            "type": "subcatchment",
            "watershed": {
                "area_km2": 12.4,
                "cn": 68,
                "flow_path_length_km": 7.21,
                "flow_path_slope_m_per_m": 0.0236,
            },
            "runoff": {
                "model": "curve-number",
                "tc_method": "kirpich",
                "amc": "II",
                "uh_model": "scs",
            },
        },
        {"id": "J1", "type": "junction", "from": ["Z1", "Z2"]},
        {
            "id": "R1",
            "type": "reach",
            "method": "muskingum-cunge",
            "from": ["J1"],
            "length_km": 5.07,
            "slope_m_per_m": 0.0098,
        },
        {
            "id": "Z3",
            "type": "subcatchment",
            "watershed": {
                "area_km2": 4.72,
                "cn": 66,
                "flow_path_length_km": 3.35,
                "flow_path_slope_m_per_m": 0.0311,
            },
            "runoff": {
                "model": "curve-number",
                "tc_method": "kirpich",
                "amc": "II",
                "uh_model": "scs",
            },
        },
        {"id": "J2", "type": "junction", "from": ["R1", "Z3"]},
        {"id": "OUT", "type": "outlet", "from": ["J2"]},
    ],
}


def picture(drawn: dict[str, Any]) -> dict[str, Any]:
    """Return a schematic without what the schematic of a structure leaves out."""
    nodes = [
        {key: value for key, value in node.items() if key != "parameters"}
        for node in drawn["nodes"]
    ]
    kept = {key: value for key, value in drawn.items() if key != "structure_only"}
    return {**kept, "nodes": nodes}


def bare(content: dict[str, Any]) -> dict[str, Any]:
    """Return a document with the ids, types and links of its nodes only."""
    return {
        "schema": content["schema"],
        "nodes": [
            {key: node[key] for key in ("id", "type", "from") if key in node}
            for node in content["nodes"]
        ],
    }


def guide() -> dict[str, Any]:
    """Return the guide's network with its time step given, as a structure keeps it."""
    return {**example_network_document(), "timestep_min": 5}


# --- the layout of a structure is the layout of its network --------------------------


@pytest.mark.parametrize("weighed", ["no areas", "areas", "some areas"])
@pytest.mark.parametrize(("size", "seed", "fan_in", "deep"), SHAPES)
def test_the_structure_of_a_network_is_laid_out_as_the_network(
    size, seed, fan_in, deep, weighed
):
    root, inflows = random_tree(size, seed, fan_in=fan_in, deep=deep)
    chance = random.Random(seed)
    heads = sorted(node for node, ups in inflows.items() if not ups)
    areas = {head: chance.uniform(0.5, 5.0) for head in heads}
    if weighed == "no areas":
        areas = {}
    elif weighed == "some areas":
        del areas[heads[0]]
    network = network_of(root, inflows, areas)
    content = network.to_document()

    for main_stem in (None, [chance.choice(heads)]):
        drawn = structure_schematic(content, main_stem=main_stem)

        assert drawn["structure_only"] is True
        assert picture(drawn) == picture(network.schematic(main_stem=main_stem))


def test_a_draft_without_any_value_is_laid_out_as_its_network_without_areas():
    full = example_network_document()
    sourced = document(
        *(
            source(node["id"]) if node["type"] == "subcatchment" else node
            for node in full["nodes"]
        )
    )

    drawn = structure_schematic({**bare(full), "timestep_min": 10})

    # The sources are given their hydrographs (at 10 min): no headwater has an area
    assert picture(drawn) == picture(RoutingNetwork.from_document(sourced).schematic())


def test_nogats_example_is_laid_out_without_the_section_of_its_reach():
    with pytest.raises(InvalidParameterError) as refused:
        RoutingNetwork.from_document(NOGAT_EXAMPLE)
    completed = copy.deepcopy(NOGAT_EXAMPLE)
    completed["nodes"][3].update(manning_n=0.035, bottom_width_m=4.0)

    drawn = structure_schematic(NOGAT_EXAMPLE)

    assert (refused.value.details["reason"], refused.value.details["node_id"]) == (
        "one_of",
        "R1",
    )
    complete = RoutingNetwork.from_document(completed).schematic()
    assert picture(drawn) == picture(complete)
    assert drawn["grid"] == {"width": 4, "height": 2}
    # Z1 drains more than Z2: the main stem runs through it
    assert drawn["lines"][0]["nodes"] == ["Z1", "J1", "R1", "J2", "OUT"]


# --- the reasons of a structure are the network's ------------------------------------

DOCUMENT_PROBLEMS = [
    ("not an object", [1, 2], "shape"),
    ("no schema", {"nodes": []}, "missing_field"),
    ("another schema", {"schema": "hydrolog-network/2", "nodes": []}, "unknown_schema"),
    ("no nodes", {"schema": "hydrolog-network/1"}, "missing_field"),
    ("nodes that are no list", {"schema": "hydrolog-network/1", "nodes": {}}, "type"),
    (
        "a node that is no object",
        {"schema": "hydrolog-network/1", "nodes": [5]},
        "shape",
    ),
    ("a node without an id", document({"type": "outlet"}), "missing_field"),
    ("an id that is no text", document({"id": 7, "type": "outlet"}), "invalid_id"),
    ("a node without a type", document({"id": "OUT"}), "missing_field"),
    ("an unknown type", document({"id": "OUT", "type": "sink"}), "unknown_type"),
    (
        "from that is no list",
        document(source("A"), reach("R", "A", **{"from": "A"}), outlet("R")),
        "type",
    ),
]


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        pytest.param(content, reason, id=name)
        for name, content, reason in [*STRUCTURE_CORPUS, *DOCUMENT_PROBLEMS]
    ],
)
def test_a_problem_of_the_structure_is_refused_as_the_network_refuses_it(
    content, reason
):
    with pytest.raises(InvalidParameterError) as network:
        RoutingNetwork.from_document(content)
    with pytest.raises(InvalidParameterError) as structure:
        structure_schematic(content)

    assert network.value.details["reason"] == reason
    assert structure.value.details == network.value.details
    assert str(structure.value) == str(network.value)


def test_a_problem_of_the_structure_is_found_whatever_the_other_fields_hold():
    looped = document(
        {"id": "A", "type": "subcatchment"},
        {"id": "J1", "type": "junction", "from": ["A", "J2"]},
        {"id": "J2", "type": "junction", "from": ["J1"]},
        {"id": "R", "type": "reach", "from": ["J2"], "method": "lag"},
        outlet("R"),
    )

    with pytest.raises(InvalidParameterError) as caught:
        structure_schematic(looped)

    assert caught.value.details["reason"] == "cycle"
    assert caught.value.details["nodes"] == ["J1", "J2"]


# --- what of the document is read ----------------------------------------------------


def test_the_other_fields_of_a_node_may_be_missing_or_wrong():
    draft = document(
        {"id": "A", "type": "subcatchment", "watershed": {"area_km2": "large"}},
        {"id": "B", "type": "subcatchment", "times_min": "soon", "color": "blue"},
        {"id": "R", "type": "reach", "from": ["A"], "method": "teleport"},
        {"id": "D", "type": "reservoir", "from": ["R"], "rating_file": "absent.csv"},
        junction("J", "D", "B"),
        {"id": "OUT", "type": "outlet", "from": ["J"], "description": "\t" * 600},
        rainfall=42,
        timestep_min="ten",
        name=" ",
        colour="blue",
    )

    drawn = structure_schematic(draft)

    assert [node["id"] for node in drawn["nodes"]] == ["A", "B", "R", "D", "J", "OUT"]
    assert all(node["parameters"] == [] for node in drawn["nodes"])
    assert "description" not in drawn["nodes"][-1]
    assert "name" not in drawn and "timestep_min" not in drawn
    # an area that is no positive number weighs nothing: the nodes are counted
    assert drawn["lines"][0]["nodes"] == ["A", "R", "D", "J", "OUT"]


@pytest.mark.parametrize(
    ("area", "weighed"),
    [
        (30.0, True),
        (30, True),
        (0, False),
        (-30.0, False),
        (True, False),
        (None, False),
    ],
)
def test_the_areas_weigh_the_branches_when_every_headwater_has_a_positive_one(
    area, weighed
):
    # B drains the larger area, A heads the branch with more nodes
    nodes = [
        {"id": "A", "type": "subcatchment", "watershed": {"area_km2": 1.0}},
        {"id": "B", "type": "subcatchment", "watershed": {"area_km2": area}},
        {"id": "R", "type": "reach", "from": ["A"]},
        junction("J", "R", "B"),
        outlet("J"),
    ]

    read = read_structure(document(*nodes))
    drawn = structure_schematic(document(*nodes))

    assert read.areas == ({"A": 1.0, "B": float(area)} if weighed else None)
    assert drawn["lines"][0]["nodes"][0] == ("B" if weighed else "A")


def test_positions_are_ignored_and_the_layout_is_computed():
    content = guide()
    for column, node in enumerate(content["nodes"]):
        node["position"] = {"x": 7 - column, "y": column}
    partial = guide()
    partial["nodes"][0]["position"] = {"x": 3, "y": 3}

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        placed = structure_schematic(content)
        some = structure_schematic(partial)

    computed = RoutingNetwork.from_document(guide()).schematic()
    assert placed["layout"] == some["layout"] == "computed"
    assert picture(placed) == picture(some) == picture(computed)


def test_the_document_is_the_schematic_of_a_structure():
    content = {**guide(), "name": "Draft", "description": "The network of the guide"}
    content["nodes"][0]["description"] = "A subcatchment"

    drawn = structure_schematic(content)
    stepless = structure_schematic({**content, "timestep_min": 0})

    assert list(drawn) == [
        "schema",
        "name",
        "outlet",
        "timestep_min",
        "has_result",
        "layout",
        "structure_only",
        "grid",
        "lines",
        "nodes",
        "edges",
    ]
    assert drawn["schema"] == SCHEMA
    assert (drawn["name"], drawn["outlet"], drawn["timestep_min"]) == (
        "Draft",
        "OUT",
        5.0,
    )
    assert (drawn["has_result"], drawn["layout"], drawn["structure_only"]) == (
        False,
        "computed",
        True,
    )
    assert [list(node) for node in drawn["nodes"]] == [
        ["id", "type", "x", "y", "line", "label", "parameters"]
    ] * len(content["nodes"])
    assert "timestep_min" not in stepless


def test_a_declared_main_stem_is_followed_or_refused_as_in_the_network():
    draft = bare(example_network_document())

    declared = structure_schematic(draft, main_stem="C")
    with pytest.raises(InvalidParameterError) as unknown:
        structure_schematic(draft, main_stem=["nothing"])
    with pytest.raises(InvalidParameterError) as apart:
        structure_schematic(draft, main_stem=["A", "B"])

    assert declared["lines"][0]["nodes"] == ["C", "J2", "OUT"]
    assert unknown.value.details["reason"] == "unknown_node"
    assert apart.value.details["reason"] == "main_stem_not_a_path"
