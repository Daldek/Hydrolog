"""„Sieć i trasowanie” (GUI plan S4, D13, D14, D18; plan 2026-11-10-network-editor, E2).

A first visit has no network and sends nothing: step 1 says what to load and links the
guide's worked example; „Wyczyść” returns there. The guide's network (loaded with „Plik
sieci…”) opens on the canvas at the cells of Hydrolog's layout, drawn vertically: the
sources at the top, the outlet at the bottom, every edge by rule D as the library draws
it, each label on the side of its node without a tributary. A node moves by a drag, by
Shift with an arrow key and by „Przesuń” and a click; the move survives a reload and a
saved and reopened file, never marks the result stale, and „Uporządkuj” brings
Hydrolog's layout back. The arrow keys go between nodes and the zoom follows „+” and
„−”, all without a mouse. A network Hydrolog cannot read yet stands in provisional rows
until it can, and inputs stored before the canvas are laid out like a file without
positions. The PNG leaves out the marks of editing. „Oblicz sieć” writes the document,
positions included, to the session and runs ``route network``; the outlet's and every
node's values are those of the library. A network loaded from a file with its
referenced files (an inflows file and a rating table) computes too, and every node type
opens its form. A node is chosen by a click, Enter or Space on the canvas and in the
node table; a changed reach method shows its fields and marks the result stale. The SVG
of Hydrolog and the network's document export, the document with the positions shown.
A phone in the dark theme shows the canvas without scrolling sideways.
"""

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from playwright.sync_api import Page, expect

from hydrolog.catalog import run_command
from hydrolog.routing import RoutingNetwork
from hydrolog.testing import example_network_document, placed
from tests.e2e.conftest import Tab, load_network, open_part

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
BADGE = ".topbar .badge.status"
NODE = 'svg.schem g.node[data-node="{}"]'
SAID = '[data-canvas="said"]'
COLUMN = 110
"""Pixels across the canvas per grid unit at a zoom of 1 (``editor/geometry.js``)."""
ROW = 74
"""Pixels along the flow per grid unit at a zoom of 1."""
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""
CELLS = """() => Object.fromEntries(
  [...document.querySelectorAll('svg.schem g.node')].map((node) =>
    [node.dataset.node, [Number(node.dataset.x), Number(node.dataset.y)]]))"""
ROUTES = """() => Object.fromEntries(
  [...document.querySelectorAll('svg.schem polyline.ln')].map((line) =>
    [line.dataset.edge, line.getAttribute('points').split(' ')
      .map((point) => point.split(',').map(Number))]))"""

Cell = tuple[int, int]


def polish(value: float, digits: int) -> str:
    """Return ``value`` as the GUI writes it: a decimal comma, U+2212 for minus."""
    text = f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")
    if len(text.split(",")[0].replace("-", "")) < 6:
        text = text.replace(" ", "")
    return text.replace(" ", "\u00a0").replace("-", "\u2212")


def hmm(minutes: float) -> str:
    """Return minutes as h:mm."""
    whole = round(minutes)
    return f"{whole // 60}:{whole % 60:02d}"


def routed(options: dict[str, Any], allowed: list[str] | None = None) -> dict[str, Any]:
    """Return the nodes of ``route network`` by id."""
    envelope = run_command("route network", options, allowed_dirs=allowed).to_dict()
    return {node["id"]: node for node in envelope["result"]["nodes"]}


def library(document: dict[str, Any]) -> tuple[dict[str, Cell], dict[str, list[Cell]]]:
    """Return the cells and the edges of Hydrolog's schematic of ``document``."""
    drawn = RoutingNetwork.from_document(document).schematic()
    cells = {node["id"]: (node["x"], node["y"]) for node in drawn["nodes"]}
    routes = {
        f"{edge['from']}>{edge['to']}": [(x, y) for x, y in edge["points"]]
        for edge in drawn["edges"]
    }
    return cells, routes


def with_cells(document: dict[str, Any], cells: dict[str, Cell]) -> dict[str, Any]:
    """Return ``document`` with the cells as the positions of its nodes."""
    nodes = [placed(node, position=cells[node["id"]]) for node in document["nodes"]]
    return {**document, "nodes": nodes}


def canvas_cells(page: Page) -> dict[str, Cell]:
    """Return the cell of every node of the canvas."""
    return {node: (x, y) for node, (x, y) in page.evaluate(CELLS).items()}


def canvas_routes(page: Page) -> dict[str, list[Cell]]:
    """Return the corners of every edge of the canvas in grid units."""
    found: dict[str, list[Cell]] = {}
    for edge, points in page.evaluate(ROUTES).items():
        assert all(px % COLUMN == 0 and py % ROW == 0 for px, py in points), points
        found[edge] = [(py // ROW, px // COLUMN) for px, py in points]
    return found


def open_section(tab: Tab) -> Page:
    """Open Sieć, load the guide's network and wait for its canvas."""
    tab.open("#siec")
    load_network(tab.page)
    expect(tab.page.locator("svg.schem g.node")).to_have_count(8)
    return tab.page


def compute(page: Page) -> None:
    """Press „Oblicz sieć” and wait for the current result."""
    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")


def centre(page: Page, node: str) -> float:
    """Return the vertical position of a node of the canvas."""
    return float(
        page.locator(NODE.format(node) + " circle.halo").get_attribute("cy") or 0
    )


def screen_point(page: Page, node: str, steps: Cell = (0, 0)) -> tuple[float, float]:
    """Return where on the screen the cell ``steps`` away from ``node``'s is.

    ``steps`` are cells along the flow (down) and sideways (to the right).
    """
    halo = page.locator(NODE.format(node) + " circle.halo").bounding_box()
    assert halo is not None
    scale = halo["width"] / 40
    return (
        halo["x"] + halo["width"] / 2 + steps[1] * COLUMN * scale,
        halo["y"] + halo["height"] / 2 + steps[0] * ROW * scale,
    )


def drag(page: Page, node: str, steps: Cell) -> None:
    """Drag ``node`` with the mouse ``steps`` cells away (down, right)."""
    page.mouse.move(*screen_point(page, node))
    page.mouse.down()
    page.mouse.move(*screen_point(page, node, steps), steps=8)
    page.mouse.up()


def test_a_first_visit_is_empty_and_clearing_returns_there(tab: Tab) -> None:
    sent: list[str] = []
    tab.page.on(
        "request",
        lambda request: (
            sent.append(request.url) if "/api/run/" in request.url else None
        ),
    )
    tab.open("#siec")
    page = tab.page
    section = page.locator('section[data-section="siec"]')
    hint = section.locator('[data-empty="siec"]')
    expect(hint).to_contain_text("Plik sieci…")
    expect(hint.get_by_role("link")).to_have_attribute(
        "href", "instrukcja/#przyklad-siec"
    )
    expect(section.locator('[data-schematic="empty"]')).to_be_visible()
    expect(section.locator("[data-network-file]")).to_have_count(0)
    expect(page.get_by_role("button", name="Oblicz sieć")).to_be_disabled()

    load_network(page)
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    page.reload()  # the network is kept
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    section.get_by_role("button", name="Wyczyść").click()
    expect(hint).to_be_visible()
    expect(page.locator("svg.schem")).to_have_count(0)
    page.reload()
    expect(hint).to_be_visible()
    assert not any("/api/run/route/network" in url for url in sent)


def test_the_example_is_drawn_first_and_computes_the_librarys_values(tab: Tab) -> None:
    runs: list[str] = []
    tab.page.on(
        "request",
        lambda request: (
            runs.append(request.url) if "/api/run/" in request.url else None
        ),
    )
    page = open_section(tab)

    # At the cells of Hydrolog's layout, every edge by rule D as the library draws it;
    # turned: the sources on top, the outlet at the bottom
    assert any("/api/run/route/schematic" in url for url in runs)
    assert not any("/api/run/route/network" in url for url in runs)
    hydrolog_cells, hydrolog_routes = library(example_network_document())
    assert canvas_cells(page) == hydrolog_cells
    assert canvas_routes(page) == hydrolog_routes
    heights = {
        node: centre(page, node) for node in ["A", "R_A", "J1", "R_J1", "J2", "OUT"]
    }
    assert list(heights.values()) == sorted(heights.values())
    assert centre(page, "OUT") == max(centre(page, n) for n in ["A", "B", "C", "OUT"])
    places = {
        node: page.locator(NODE.format(node)).get_attribute("data-place")
        for node in ["A", "B", "C", "J1", "R_J1", "J2"]
    }
    assert places == {
        "A": "right",
        "B": "left",
        "C": "right",
        "J1": "right",
        "R_J1": "left",
        "J2": "left",
    }
    expect(page.locator(BADGE)).to_be_hidden()

    compute(page)
    expected = routed({"network": example_network_document()})
    outlet = expected["OUT"]
    tiles = page.locator('[data-tiles="network"]')
    expect(tiles.locator('[data-tile="peak"] .v')).to_have_text(
        f"{polish(outlet['peak_m3s'], 1)} m³/s"
    )
    expect(tiles.locator('[data-tile="time"] .v')).to_have_text(
        f"{hmm(outlet['time_to_peak_min'])} h"
    )
    expect(tiles.locator('[data-tile="volume"] .v')).to_have_text(
        f"{polish(outlet['volume_m3'] / 1000, 1)} tys. m³"
    )
    expect(page.locator(NODE.format("OUT") + " .lbl-v")).to_have_text(
        f"{polish(outlet['peak_m3s'], 1)} · {hmm(outlet['time_to_peak_min'])}"
    )

    # The node table: every node's kind, description, the node below, peak, time and
    # volume, rows in the order computed
    page.get_by_role("radio", name="Tabela węzłów").click()
    rows = page.locator(".node-table tbody tr")
    expect(rows).to_have_count(8)
    below = {"A": "R_A", "B": "J1", "C": "J2", "R_A": "J1", "J1": "R_J1"}
    below |= {"R_J1": "J2", "J2": "OUT", "OUT": "–"}
    for node, value in expected.items():
        cells = page.locator(f'.node-table tr[data-node-row="{node}"] td')
        expect(cells.nth(1)).to_have_text("–")
        expect(cells.nth(2)).to_have_text(below[node])
        expect(cells.nth(3)).to_have_text(polish(value["peak_m3s"], 2))
        expect(cells.nth(4)).to_have_text(hmm(value["time_to_peak_min"]))
        expect(cells.nth(5)).to_have_text(polish(value["volume_m3"] / 1000, 1))

    # A row chooses its node: its chart (inflow and outflow) and numbers in Wyniki
    page.locator('.node-table tr[data-node-row="R_J1"] button').click()
    result = page.locator('[data-node-res="R_J1"]')
    expect(result.locator(".chart-legend")).to_contain_text("Dopływ J1")
    expect(result.locator(".chart-legend")).to_contain_text("Odpływ R_J1")
    expect(result.locator('[data-param="peak_attenuation_pct"] td').first).to_have_text(
        polish(expected["R_J1"]["peak_attenuation_pct"], 1)
    )
    expect(page.locator('[data-node-form="R_J1"]')).to_be_visible()


def test_a_network_file_with_its_files_opens_every_node_type(tab: Tab) -> None:
    tab.open("#siec")
    page = tab.page
    load_network(
        page,
        FIXTURES / "network_flood.json",
        FIXTURES / "network_inflows.csv",
        FIXTURES / "pond_rating.csv",
    )
    expect(page.locator('[data-network-file="network_flood.json"]')).to_be_visible()
    expect(page.locator('[data-rating="pond_rating.csv"]')).to_have_class("ok")
    expect(page.locator("svg.schem g.node")).to_have_count(6)

    kinds = {
        "A": "subcatchment",
        "R1": "reach",
        "J1": "junction",
        "D": "reservoir",
        "OUT": "outlet",
    }
    for node, kind in kinds.items():
        page.locator(NODE.format(node)).click()
        expect(page.locator(f'[data-node-form="{node}"]')).to_have_attribute(
            "data-kind", kind
        )
    page.locator(NODE.format("D")).click()
    reservoir = page.locator('[data-node-form="D"]')
    expect(reservoir.get_by_role("radio", name="Plik")).to_have_attribute(
        "aria-checked", "true"
    )
    expect(
        reservoir.locator('[data-key="level-pool.rating_file"] select')
    ).to_have_value("pond_rating.csv")
    page.locator(NODE.format("R1")).click()
    channel = page.locator('[data-node-form="R1"]')
    expect(
        channel.locator('[data-key="muskingum-cunge.manning_n"] input')
    ).to_have_value("0,035")

    compute(page)
    expected = routed(
        {
            "network_file": str(FIXTURES / "network_flood.json"),
            "inflows_file": str(FIXTURES / "network_inflows.csv"),
        },
        [str(FIXTURES)],
    )
    expect(page.locator('[data-tile="peak"] .v')).to_have_text(
        f"{polish(expected['OUT']['peak_m3s'], 1)} m³/s"
    )


def test_keys_choose_nodes_and_a_new_method_marks_the_result_stale(tab: Tab) -> None:
    page = open_section(tab)
    compute(page)

    page.locator(NODE.format("J1")).focus()
    page.keyboard.press("Enter")
    expect(page.locator(NODE.format("J1"))).to_have_attribute("aria-pressed", "true")
    expect(page.locator('[data-node-form="J1"]')).to_have_attribute(
        "data-kind", "junction"
    )
    page.locator(NODE.format("R_A")).focus()
    page.keyboard.press(" ")
    expect(page).to_have_url(re.compile(r"#siec/R_A$"))
    form = page.locator('[data-node-form="R_A"]')
    expect(form.locator('[data-key="lag.lag_min"] input')).to_have_value("25")

    form.locator('[data-key="#method"] select').select_option("muskingum")
    expect(form.locator('[data-key="lag.lag_min"]')).to_have_count(0)
    form.locator('[data-key="muskingum.k_min"] input').fill("30")
    form.locator('[data-key="muskingum.x"] input').fill("0,2")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "stale")
    expect(page.locator('[data-stale="true"]')).to_be_visible()

    compute(page)
    expect(page.locator('[data-stale="true"]')).to_have_count(0)
    sent = json.loads(page.request.get(tab.base + "api/files/in/siec.json").text())
    reach = next(node for node in sent["nodes"] if node["id"] == "R_A")
    x, y = library(example_network_document())[0]["R_A"]
    assert reach == {
        "id": "R_A",
        "type": "reach",
        "from": ["A"],
        "method": "muskingum",
        "k_min": 30,
        "x": 0.2,
        "position": {"x": x, "y": y},
    }


def test_the_svg_and_the_network_document_export(tab: Tab) -> None:
    page = open_section(tab)
    open_part(page, 'section[data-section="siec"]', "exports")
    with page.expect_download() as saved:
        page.locator('[data-export="json-network"]').click()
    document = json.loads(Path(saved.value.path()).read_text(encoding="utf-8"))
    example = example_network_document()
    assert document == with_cells(example, library(example)[0])

    compute(page)
    with page.expect_download() as drawing:
        page.locator('[data-export="svg"]').click()
    svg = Path(drawing.value.path()).read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<svg")
    assert drawing.value.suggested_filename == "siec.svg"


def test_a_dragged_node_keeps_its_cell_after_a_reload_and_in_a_saved_file(
    tab: Tab, tmp_path: Path
) -> None:
    page = open_section(tab)
    compute(page)
    cells = library(example_network_document())[0]
    x, y = cells["C"]

    # A press that moves less than 4 px is a click; a longer one drags the node by
    # whole cells, and the edges follow rule D as the library draws the new cells
    drag(page, "C", (0, 1))
    moved = {**cells, "C": (x, y + 1)}
    expect(page.locator(NODE.format("C"))).to_have_attribute("data-y", str(y + 1))
    expect(page.locator(SAID)).to_have_text("Przesunięto C.")
    assert canvas_cells(page) == moved
    assert (
        canvas_routes(page) == library(with_cells(example_network_document(), moved))[1]
    )
    expect(page.locator(NODE.format("C"))).not_to_have_attribute(
        "transform", re.compile(".")
    )
    # A taken cell refuses the drop
    drag(page, "B", (0, 1))
    expect(page.locator(SAID)).to_have_text(
        "Nie można przesunąć B: to pole zajmuje R_A."
    )
    assert canvas_cells(page) == moved
    # A move is no change of the data: the result stays current
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(page.locator('[data-stale="true"]')).to_have_count(0)

    page.reload()
    expect(page.locator(NODE.format("C"))).to_have_attribute("data-y", str(y + 1))
    assert canvas_cells(page) == moved

    with page.expect_download() as saved:
        page.get_by_role("button", name="Zapisz sieć").click()
    saved.value.save_as(tmp_path / "siec.json")
    document = json.loads((tmp_path / "siec.json").read_text(encoding="utf-8"))
    assert document == with_cells(example_network_document(), moved)
    page.locator('section[data-section="siec"]').get_by_role(
        "button", name="Wyczyść"
    ).click()
    expect(page.locator("svg.schem")).to_have_count(0)
    load_network(page, tmp_path / "siec.json")
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    assert canvas_cells(page) == moved
    expect(page.locator('[data-canvas="provisional"]')).to_have_count(0)


def test_uporzadkuj_brings_back_hydrologs_layout(tab: Tab) -> None:
    page = open_section(tab)
    cells = library(example_network_document())[0]
    drag(page, "C", (1, 1))
    drag(page, "A", (0, -1))
    expect(page.locator(NODE.format("A"))).to_have_attribute(
        "data-y", str(cells["A"][1] - 1)
    )
    assert canvas_cells(page) != cells

    page.get_by_role("button", name="Uporządkuj").click()
    expect(page.locator(SAID)).to_have_text(
        "Uporządkowano schemat: węzły stoją tak, jak układa je Hydrolog."
    )
    assert canvas_cells(page) == cells
    page.reload()
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    assert canvas_cells(page) == cells


def test_the_keys_go_between_nodes_move_them_and_zoom_without_a_mouse(
    tab: Tab,
) -> None:
    page = open_section(tab)
    cells = library(example_network_document())[0]
    canvas = page.locator("svg.schem")
    expect(canvas).to_have_attribute("aria-describedby", re.compile("."))
    focused = "() => document.activeElement.dataset.node"

    # One stop in the tab order (the chosen node); the arrows go to the nearest node
    page.locator(NODE.format("OUT")).focus()
    expect(page.locator(NODE.format("OUT"))).to_have_attribute("tabindex", "0")
    expect(page.locator(NODE.format("J2"))).to_have_attribute("tabindex", "-1")
    for key, node in [("ArrowUp", "J2"), ("ArrowUp", "R_J1"), ("ArrowRight", "C")]:
        page.keyboard.press(key)
        assert page.evaluate(focused) == node
    page.keyboard.press("Enter")
    expect(page.locator(NODE.format("C"))).to_have_attribute("aria-pressed", "true")
    expect(page.locator('[data-node-form="C"]')).to_be_visible()

    # Shift with an arrow moves the node one cell; a taken cell refuses
    x, y = cells["C"]
    page.keyboard.press("Shift+ArrowRight")
    expect(page.locator(NODE.format("C"))).to_have_attribute("data-y", str(y + 1))
    expect(page.locator(SAID)).to_have_text("Przesunięto C w prawo.")
    assert page.evaluate(focused) == "C"
    page.keyboard.press("Shift+ArrowLeft")
    page.keyboard.press("Shift+ArrowLeft")
    expect(page.locator(SAID)).to_have_text(
        "Nie można przesunąć C: to pole zajmuje R_J1."
    )
    assert canvas_cells(page) == cells
    page.keyboard.press("Shift+ArrowDown")
    expect(page.locator(NODE.format("C"))).to_have_attribute("data-x", str(x + 1))

    # The zoom: „+” and „−” step through the levels, „Dopasuj” fits the picture again
    expect(canvas).to_have_attribute("data-zoom", "fit")
    width = float(canvas.get_attribute("width") or 0)
    page.keyboard.press("+")
    expect(canvas).to_have_attribute("data-zoom", "1.25")
    assert float(canvas.get_attribute("width") or 0) == round(width * 1.25)
    page.keyboard.press("-")
    page.keyboard.press("-")
    expect(canvas).to_have_attribute("data-zoom", "0.8")
    expect(page.locator(SAID)).to_have_text("Powiększenie 80 %.")
    page.keyboard.press("?")
    expect(page.locator('[data-canvas="keys-list"]')).to_be_visible()
    expect(page.locator('[data-canvas="keys-list"]')).to_contain_text(
        "Shift + strzałka"
    )
    page.keyboard.press("Escape")
    expect(page.locator('[data-canvas="keys-list"]')).to_be_hidden()
    assert page.evaluate(focused) == "C"
    # The tools come before the picture: „Skróty”, then „Dopasuj”
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("() => document.activeElement.dataset.canvas") == "fit"
    page.keyboard.press("Enter")
    expect(canvas).to_have_attribute("data-zoom", "fit")


def test_przesun_and_a_click_move_the_chosen_node_without_a_drag(tab: Tab) -> None:
    page = open_section(tab)
    cells = library(example_network_document())[0]
    move = page.get_by_role("button", name="Przesuń")
    page.locator(NODE.format("B")).click()
    move.click()
    expect(page.locator('[data-canvas="prompt"]')).to_have_text(
        "Kliknij wolne pole, na które ma przejść B; Esc przerywa."
    )
    expect(page.get_by_role("button", name="Przerwij")).to_have_attribute(
        "aria-pressed", "true"
    )
    # A taken cell: the move waits for a free one
    page.mouse.click(*screen_point(page, "B", (0, 1)))
    expect(page.locator(SAID)).to_have_text(
        "Nie można przesunąć B: to pole zajmuje R_A."
    )
    page.mouse.click(*screen_point(page, "B", (0, -1)))
    expect(page.locator(SAID)).to_have_text("Przesunięto B.")
    expect(page.locator('[data-canvas="prompt"]')).to_have_count(0)
    x, y = cells["B"]
    assert canvas_cells(page) == {**cells, "B": (x, y - 1)}
    # Esc ends the move without one
    move.click()
    page.keyboard.press("Escape")
    expect(page.locator('[data-canvas="prompt"]')).to_have_count(0)
    expect(page.locator(SAID)).to_have_text("Przerwano przesuwanie B.")


def test_a_network_hydrolog_cannot_read_yet_stands_in_provisional_rows(
    tab: Tab, tmp_path: Path
) -> None:
    example = example_network_document()
    incomplete = {
        **example,
        "nodes": [
            {key: value for key, value in node.items() if key != "lag_min"}
            for node in example["nodes"]
        ],
    }
    (tmp_path / "siec.json").write_text(json.dumps(incomplete), encoding="utf-8")
    tab.open("#siec")
    page = tab.page
    load_network(page, tmp_path / "siec.json")
    expect(page.locator('[data-canvas="provisional"]')).to_be_visible()
    # Rows by the longest distance from a headwater, side by side in the file's order
    assert canvas_cells(page) == {
        "A": (0, -1),
        "B": (0, 0),
        "C": (0, 1),
        "R_A": (1, 0),
        "J1": (2, 0),
        "R_J1": (3, 0),
        "J2": (4, 0),
        "OUT": (5, 0),
    }
    expect(page.get_by_role("button", name="Uporządkuj")).to_be_disabled()

    page.locator(NODE.format("R_A")).click()
    page.locator('[data-node-form="R_A"] [data-key="lag.lag_min"] input').fill("25")
    expect(page.locator('[data-canvas="provisional"]')).to_have_count(0)
    expect(page.get_by_role("button", name="Uporządkuj")).to_be_enabled()
    assert canvas_cells(page) == library(example)[0]


def test_inputs_stored_before_the_canvas_are_laid_out_like_a_file(tab: Tab) -> None:
    page = open_section(tab)
    page.evaluate(
        """() => {
          const key = 'hydrolog-gui/siec/2';
          const stored = JSON.parse(localStorage.getItem(key));
          delete stored.provisional;
          stored.skeleton = stored.skeleton.map(({position, ...node}) => node);
          localStorage.setItem(key, JSON.stringify(stored));
        }"""
    )
    page.reload()
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    assert canvas_cells(page) == library(example_network_document())[0]
    expect(page.locator('[data-canvas="provisional"]')).to_have_count(0)


def style_of(element: ElementTree.Element) -> dict[str, str]:
    """Return the declarations of an element's ``style`` attribute."""
    pairs = (
        item.split(":", 1)
        for item in element.get("style", "").split(";")
        if ":" in item
    )
    return {name.strip(): value.strip() for name, value in pairs}


def test_the_png_leaves_out_the_marks_of_editing(tab: Tab) -> None:
    page = open_section(tab)
    expect(page.locator(NODE.format("OUT"))).to_have_attribute("aria-pressed", "true")
    copied = page.evaluate(
        """async () => {
          const { svgText } = await import('./src/charts/png.js');
          const svg = document.querySelector('svg.schem');
          const fill = (selector) => getComputedStyle(svg.querySelector(selector)).fill;
          return {
            text: svgText(svg).text,
            shown: fill('g.node.sel circle.halo'),
            other: fill('g.node:not(.sel) circle.halo'),
            classes: svg.getAttribute('class'),
          };
        }"""
    )
    # The image the PNG is drawn from: the chosen node's halo as every other's, the
    # mark of a drop hidden; the canvas keeps its classes
    copy = ElementTree.fromstring(copied["text"])
    svg = "{http://www.w3.org/2000/svg}"
    halos = {
        group.get("data-node"): style_of(group.findall(f"{svg}circle")[0])["fill"]
        for group in copy.iter(f"{svg}g")
        if group.get("data-node")
    }
    marker = next(
        group for group in copy.iter(f"{svg}g") if "drop-cell" in group.get("class", "")
    )
    assert copied["shown"] != copied["other"]
    assert halos["OUT"] == copied["other"]
    assert set(halos.values()) == {copied["other"]}
    assert style_of(marker)["display"] == "none"
    assert "exporting" not in copied["classes"]


def test_a_phone_in_the_dark_theme_shows_the_schematic(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    page = open_section(tab)
    expect(page.locator("svg.schem")).to_be_visible()
    assert page.evaluate(SIDEWAYS) == []
    # The chosen node (the outlet) moves by „Przesuń” and a tap on a free cell
    x, y = library(example_network_document())[0]["OUT"]
    page.get_by_role("button", name="Przesuń").click()
    page.mouse.click(*screen_point(page, "OUT", (0, -1)))
    expect(page.locator(NODE.format("OUT"))).to_have_attribute("data-y", str(y - 1))
    assert page.evaluate(SIDEWAYS) == []
    page.locator(NODE.format("B")).click()
    expect(
        page.locator('section[data-section="siec"] .view-panel.left')
    ).to_be_visible()
    expect(page.locator('[data-node-form="B"]')).to_be_attached()
    assert page.evaluate(SIDEWAYS) == []
