"""Tests of the SVG of a schematic (ADR-0013).

The drawing is a function of the document alone, so these tests draw documents: the one
of the example network, and small ones written by hand where a number or a text has to
be exact. The SVG must be well-formed XML whatever the ids and the name hold, and the
same text every time.
"""

import copy
import json
import xml.etree.ElementTree as ET

import pytest

from hydrolog.routing.schematic import schematic_svg
from hydrolog.testing import example_network

from ._schematic_networks import network_of

SVG = "{http://www.w3.org/2000/svg}"


def node(node_id, kind="reach", x=0, y=0, line=0, side="n", **values):
    entry = {
        "id": node_id,
        "type": kind,
        "x": x,
        "y": y,
        "line": line,
        "label": {"text": node_id, "side": side},
        "parameters": [],
    }
    return {**entry, **values}


def document(nodes, edges=(), **top):
    width = max(item["x"] for item in nodes)
    height = max(item["y"] for item in nodes)
    return {
        "schema": "hydrolog-network-schematic/1",
        "outlet": nodes[-1]["id"],
        "has_result": False,
        "grid": {"width": width, "height": height},
        "lines": [],
        "nodes": nodes,
        "edges": list(edges),
        **top,
    }


def drawn(svg):
    return ET.fromstring(svg)


def texts(root):
    return ["".join(item.itertext()) for item in root.iter(f"{SVG}text")]


@pytest.fixture(scope="module")
def full():
    network = example_network()
    return network.schematic(network.route())


def test_the_svg_is_well_formed_and_draws_every_edge_and_every_node(full):
    root = drawn(schematic_svg(full))

    assert root.tag == f"{SVG}svg"
    assert len(list(root.iter(f"{SVG}polyline"))) == len(full["edges"])
    groups = list(root.iter(f"{SVG}g"))
    assert len(groups) == len(full["nodes"])
    for group, entry in zip(groups, full["nodes"], strict=True):
        assert group.find(f"{SVG}title").text.startswith(
            f"{entry['id']} ({entry['type']})"
        )
    assert {entry["id"] for entry in full["nodes"]} <= set(texts(root))
    width, height = root.get("width"), root.get("height")
    assert root.get("viewBox") == f"0 0 {width} {height}"


def test_the_same_document_gives_the_same_text_every_time(full):
    again = json.loads(json.dumps(full))

    assert (
        schematic_svg(full)
        == schematic_svg(copy.deepcopy(full))
        == schematic_svg(again)
    )
    assert schematic_svg(full).endswith("</svg>\n")


def test_a_result_puts_its_values_in_the_label_and_no_result_leaves_the_id_alone(full):
    network = example_network()
    plain = network.schematic()

    with_values = texts(drawn(schematic_svg(full)))
    without = texts(drawn(schematic_svg(plain)))

    peak = full["nodes"][0]
    assert f"tp {peak['time_to_peak_min']:g} min" in with_values
    assert any(
        text.startswith("Qp ") and text.endswith("m\u00b3/s") for text in with_values
    )
    assert any(
        text.startswith("V ") and text.endswith("m\u00b3") for text in with_values
    )
    assert not any(text.startswith(("Qp ", "tp ", "V ")) for text in without)


@pytest.mark.parametrize(
    ("peak", "shown"),
    [
        (0.254, "0.254"),
        (5.678, "5.68"),
        (56.78, "56.8"),
        (567.8, "568"),
        (0.0, "0.000"),
    ],
)
def test_a_discharge_has_three_significant_digits(peak, shown):
    entry = node("A", peak_m3s=peak, time_to_peak_min=62.5, volume_m3=1234567.4)

    labels = texts(drawn(schematic_svg(document([entry]))))

    assert f"Qp {shown} m\u00b3/s" in labels
    assert "tp 62.5 min" in labels
    assert "V 1\u00a0234\u00a0567 m\u00b3" in labels


def test_the_name_and_the_ids_are_escaped():
    nodes = [node('a<b&"c', "subcatchment"), node("OUT", "outlet", x=1)]
    edges = [{"from": 'a<b&"c', "to": "OUT", "line": 0, "points": [[0, 0], [1, 0]]}]

    root = drawn(schematic_svg(document(nodes, edges, name="Rain & <flood>")))

    assert root.find(f"{SVG}title").text == "Rain & <flood>"
    assert 'a<b&"c' in texts(root)


def test_a_long_id_is_wrapped_and_the_tooltip_keeps_all_of_it():
    long = "subcatchment_upper_vistula_gauge_number_17"
    nodes = [node(long, "subcatchment"), node("OUT", "outlet", x=1)]

    root = drawn(schematic_svg(document(nodes)))

    lines = [
        text for text in texts(root) if text not in ("OUT", "subcatchment", "outlet")
    ]
    assert 1 < len(lines) <= 3
    assert all(len(line) <= 16 for line in lines)
    assert "".join(lines).replace("\u2026", "") in long
    assert next(root.iter(f"{SVG}title")).text == "Network schematic"
    tooltips = [item.text for item in root.iter(f"{SVG}title")]
    assert any(text.startswith(f"{long} (subcatchment)") for text in tooltips)
    # one long id does not stretch the picture without end
    short = drawn(
        schematic_svg(document([node("A", "subcatchment"), node("OUT", "outlet", x=1)]))
    )
    assert float(root.get("width")) < 2.5 * float(short.get("width"))


def test_a_warning_is_marked_on_its_node_and_an_info_is_not():
    warned = node(
        "A", notices=[{"level": "warning", "code": "w", "message": "careful"}]
    )
    quiet = node("B", x=1, notices=[{"level": "info", "code": "i", "message": "fyi"}])

    marked = texts(drawn(schematic_svg(document([warned]))))
    unmarked = texts(drawn(schematic_svg(document([quiet]))))

    assert "!" in marked
    assert "!" not in unmarked
    tooltip = next(drawn(schematic_svg(document([warned]))).iter(f"{SVG}g")).find(
        f"{SVG}title"
    )
    assert "[warning] w: careful" in tooltip.text


def test_a_kind_of_node_that_was_added_is_drawn_and_named_in_the_legend():
    nodes = [node("W", "weir"), node("OUT", "outlet", x=1)]

    root = drawn(schematic_svg(document(nodes)))

    assert {"weir", "outlet"} <= set(texts(root))


def test_the_main_stem_is_drawn_last_so_a_merge_shows_the_colour_of_the_line_it_joins():
    inflows = {"OUT": ["J"], "J": [f"s{i}" for i in range(7)]}
    inflows.update({f"s{i}": [] for i in range(7)})
    network = network_of("OUT", inflows)

    root = drawn(schematic_svg(network.schematic()))

    colours = [item.get("stroke") for item in root.iter(f"{SVG}polyline")]
    assert colours[-1] == "#1f5fa8"
    assert len(set(colours)) > 2


def test_the_parameters_of_a_node_are_the_text_of_its_tooltip(full):
    root = drawn(schematic_svg(full))

    tooltip = {
        group.find(f"{SVG}title").text.split(" ", 1)[0]: group.find(f"{SVG}title").text
        for group in root.iter(f"{SVG}g")
    }
    assert "tc_min = " in tooltip["A"]
    assert "(computed)" in tooltip["A"]
    assert "lag_min = 25 min (given)" in tooltip["R_A"]
