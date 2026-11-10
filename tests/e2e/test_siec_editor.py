"""The network editor of „Sieć i trasowanie” (plan 2026-11-10-network-editor, stage E3).

The guide's network of three subcatchments is built from „Nowa sieć” three times, with
the guide's parameters typed into „Dane”, and gives the outlet values the library gives
for the guide's file: by the mouse (the palette dragged onto cells, the handles dragged
onto the nodes below, the node menu of a right click), by the keyboard alone (no
``page.mouse`` call: Enter on the palette, ``D`` and its menu, ``P`` and the arrows, F2)
and without any drag (a palette item and a cell, „Węzeł…” and „Połącz z…” with a click).
Built by the keyboard without any value, its structure is tidied by „Uporządkuj” at the
cells of ``structure_schematic``, laid out on the channel ``siec-layout`` with
``structure_only`` (ADR-0025) and never computed.
Each refusal says its reason: a cycle, an inflow into a subcatchment, a link out of the
outlet, a second inflow into a reach (which offers „Wstaw złącze”), a node that takes no
more inflows, a taken cell and the ids the library refuses. The problems of the
structure mark their nodes and the list above the canvas, and go as edits mend them; an
edge through a node is a hint. Undo to the start and redo to the end give the same
document; a rename updates every ``from`` and keeps the column of the inflows file; a
draft is saved and reopened; „Wyczyść” and „Nowa sieć” ask before a changed network is
lost; descriptions are shown, kept, saved and never mark the result stale; a link is
removed by a click and Delete, ``O`` or „Usuń i połącz”. A phone in the dark theme edits
through the menus and tidies a structure of two nodes.
"""

import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect

from hydrolog.catalog import run_command
from hydrolog.routing import structure_schematic
from hydrolog.testing import example_network_document
from tests.e2e.conftest import Tab, input_text, load_network
from tests.e2e.test_siec import (
    BADGE,
    NODE,
    SAID,
    SIDEWAYS,
    canvas_cells,
    hmm,
    library,
    polish,
    routed,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SECTION = 'section[data-section="siec"]'
CELL_POINT = """([x, y]) => {
  const svg = document.querySelector('svg.schem');
  const view = svg.closest('.canvas-scroll');
  const at = () => new DOMPoint(y * 110, x * 74).matrixTransform(svg.getScreenCTM());
  const frame = view.getBoundingClientRect();
  const first = at();
  if (first.y < frame.top + 40 || first.y > frame.bottom - 40) {
    view.scrollTop += first.y - (frame.top + frame.height / 2);
  }
  if (first.x < frame.left + 40 || first.x > frame.right - 40) {
    view.scrollLeft += first.x - (frame.left + frame.width / 2);
  }
  // The card's column scrolls too: the cell must be within the window to be clicked
  for (let box = view.parentElement; box; box = box.parentElement) {
    const now = at();
    if (now.y > 40 && now.y < window.innerHeight - 40) break;
    if (box.scrollHeight > box.clientHeight + 1) {
      const outer = box.getBoundingClientRect();
      const middle = Math.max(outer.top, 0) + Math.min(outer.height, innerHeight) / 2;
      box.scrollTop += now.y - middle;
    }
  }
  const point = at();
  return [point.x, point.y];
}"""
"""Where on the screen the centre of a cell of the canvas is, scrolled into the card."""
STRUCTURE = """() => JSON.parse(localStorage.getItem('hydrolog-gui/siec/3')).skeleton
  .map((node) => [node.id, node.type, node.from])"""
"""The structure the section keeps: each node's id, type and inflows."""
STORED = """() => {
  const stored = JSON.parse(localStorage.getItem('hydrolog-gui/siec/3'));
  const skeleton = stored ? stored.skeleton : [];
  const ids = (nodes) => nodes.sort().join(' ');
  const drawn = [...document.querySelectorAll('svg.schem g.node')]
    .map((n) => n.dataset.node);
  const links = skeleton
    .reduce((sum, node) => sum + (node.from ? node.from.length : 0), 0);
  return ids(skeleton.map((node) => node.id)) === ids(drawn)
    && links === document.querySelectorAll('svg.schem polyline.ln').length;
}"""
"""Whether the stored structure is the one drawn (it is stored after a render)."""
INFLOW_MENU = ["subcatchment", "reach", "reservoir", "junction"]
"""The items of the menu of `D`, in order (an outlet is never an inflow)."""

Cell = tuple[int, int]


def guide() -> dict[str, Any]:
    """Return the guide's network."""
    return example_network_document()


def guide_node(node_id: str) -> dict[str, Any]:
    """Return a node of the guide's network."""
    return next(node for node in guide()["nodes"] if node["id"] == node_id)


def start(tab: Tab) -> Page:
    """Open Sieć and start a new network with the mouse."""
    tab.open("#siec")
    page = tab.page
    page.get_by_role("button", name="Nowa sieć").click()
    expect(page.locator('[data-canvas="empty"]')).to_be_visible()
    return page


def cell_point(page: Page, cell: Cell) -> tuple[float, float]:
    """Return the screen point of the centre of a cell of the canvas."""
    x, y = page.evaluate(CELL_POINT, list(cell))
    return float(x), float(y)


def centre_of(page: Page, node: str) -> tuple[float, float]:
    """Return the screen point of a node's centre."""
    halo = page.locator(NODE.format(node) + " circle.halo").bounding_box()
    assert halo is not None
    return halo["x"] + halo["width"] / 2, halo["y"] + halo["height"] / 2


def structure(page: Page) -> dict[str, tuple[str, list[str] | None]]:
    """Return the structure the section keeps by id, once it is the one drawn."""
    page.wait_for_function(STORED)
    return {node: (kind, ups) for node, kind, ups in page.evaluate(STRUCTURE)}


def said(page: Page, text: str) -> None:
    """Expect the live region to say ``text``."""
    expect(page.locator(SAID)).to_have_text(text)


def drop(page: Page, kind: str, cell: Cell) -> None:
    """Drag the palette's element ``kind`` onto ``cell`` with the mouse."""
    box = page.locator(f'[data-palette="{kind}"]').bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(*cell_point(page, cell), steps=8)
    page.mouse.up()


def drag_link(page: Page, source: str, target: str) -> None:
    """Choose ``source`` and drag its handle onto ``target`` with the mouse."""
    page.locator(NODE.format(source)).click()
    handle = page.locator(NODE.format(source) + " .handle-dot").bounding_box()
    assert handle is not None
    page.mouse.move(
        handle["x"] + handle["width"] / 2, handle["y"] + handle["height"] / 2
    )
    page.mouse.down()
    page.mouse.move(*centre_of(page, target), steps=8)
    page.mouse.up()


def menu_item(page: Page, item: str) -> None:
    """Click an item of the open menu of the canvas."""
    page.locator(f'[data-canvas-menu] [data-item="{item}"]').click()


def rename(page: Page, new: str, keys: bool = False) -> None:
    """Type ``new`` into the focused id field and press Enter."""
    field = page.locator(f'{SECTION} [data-field="id"] input')
    expect(field).to_be_focused()
    if keys:
        page.keyboard.press("Control+a")
        page.keyboard.type(new)
    else:
        field.fill(new)
    page.keyboard.press("Enter")


def choose(page: Page, node: str, how: str) -> None:
    """Choose a node: a click (``mouse``, ``click``) or focus and Enter (``keys``)."""
    if how == "keys":
        page.locator(NODE.format(node)).focus()
        page.keyboard.press("Enter")
    else:
        page.locator(NODE.format(node)).click()
    expect(page.locator(f'[data-node-form="{node}"]')).to_be_visible()


def press(page: Page, locator: Any, how: str) -> None:
    """Press a button: a click, or its focus and Enter (``keys``)."""
    if how == "keys":
        locator.focus()
        page.keyboard.press("Enter")
    else:
        locator.click()


def fill(page: Page, scope: Any, key: str, text: str, how: str) -> None:
    """Give the field of a value key ``text``: typed, chosen in a list, or pressed."""
    slot = scope.locator(f'[data-key="{key}"]')
    expect(slot).to_be_attached()
    if slot.locator("select").count():
        slot.locator("select").select_option(text)
    elif slot.get_by_role("radio").count():
        press(page, slot.get_by_role("radio", name=text, exact=True), how)
    else:
        slot.locator("input, textarea").first.fill(text)


def typed(value: Any) -> str:
    """Return a value of the document as a person types it."""
    if isinstance(value, list):
        return "; ".join(input_text(item) for item in value)
    return value if isinstance(value, str) else input_text(value)


def type_network(page: Page, how: str) -> None:
    """Type the guide's name and rainfall of the network in step 1 („Opad sieci”)."""
    step = page.locator(f'{SECTION} [data-step="network"]')
    fill(page, step, "name", guide()["name"], how)
    rain = step.locator('[data-rain-part="siec-net"]')
    rainfall = guide()["rainfall"]
    assert rainfall["hietogram_type"] == "block"
    press(page, rain.get_by_role("radio", name="Hietogram", exact=True), how)
    press(page, rain.get_by_role("radio", name="Blokowy", exact=True), how)
    for name in ("total_mm", "duration_min"):
        rain.locator(f"#siec-net-{name}").fill(input_text(rainfall[name]))


def type_node(page: Page, guide_id: str, node: str, how: str) -> None:
    """Type the guide's values of ``guide_id`` into the form of the chosen ``node``."""
    form = page.locator(f'[data-node-form="{node}"]')
    source = guide_node(guide_id)
    if source["type"] == "reach":
        fill(page, form, "#method", source["method"], how)
        for name, value in source.items():
            if name not in {"id", "type", "from", "method"}:
                fill(page, form, f"{source['method']}.{name}", typed(value), how)
        return
    more = form.locator('details[data-more="watershed"]')
    for name, value in source["watershed"].items():
        if name not in {"area_km2", "cn"} and more.get_attribute("open") is None:
            press(page, more.locator("summary"), how)
        fill(page, form, f"watershed.{name}", typed(value), how)
    for name, value in source["runoff"].items():
        if name != "model":
            fill(page, form, f"runoff.{name}", typed(value), how)
    rainfall = source.get("rainfall")
    if rainfall:
        kind = rainfall["kind"]
        label = "Projektowy" if kind == "design" else "Szereg"
        choice = form.locator('[data-choice="#rainfall"]')
        press(page, choice.get_by_role("radio", name=label), how)
        for name, value in rainfall.items():
            if name != "kind":
                fill(page, form, f"rainfall.{kind}.{name}", typed(value), how)


def type_guide(page: Page, ids: dict[str, str], how: str) -> None:
    """Type the guide's values into every node (``ids``: guide id → node id)."""
    type_network(page, how)
    for guide_id, node in ids.items():
        if guide_node(guide_id)["type"] in {"subcatchment", "reach"}:
            choose(page, node, how)
            type_node(page, guide_id, node, how)


def computes_the_guides_values(page: Page, how: str) -> None:
    """Run „Oblicz sieć” and expect the outlet values of the guide's file."""
    button = page.get_by_role("button", name="Oblicz sieć")
    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        press(page, button, how)
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    outlet = routed({"network": guide()})["OUT"]
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


def guide_structure() -> dict[str, tuple[str, list[str] | None]]:
    """Return the guide's structure by id."""
    return {node["id"]: (node["type"], node.get("from")) for node in guide()["nodes"]}


# The guide's elements in an order that keeps every cell within the drawn picture (which
# reaches one cell beyond its nodes), with their types and the guide's cells
TOP_DOWN = ["A", "B", "R_A", "J1", "R_J1", "C", "J2", "OUT"]
NEW_IDS = {
    "A": "Z1",
    "B": "Z2",
    "R_A": "R1",
    "J1": "J1",
    "R_J1": "R2",
    "C": "Z3",
    "J2": "J2",
    "OUT": "OUT",
}
"""The id each of the guide's elements gets when added in the order of TOP_DOWN."""


def test_the_guides_network_built_by_mouse_gives_its_outlet_values(tab: Tab) -> None:
    page = start(tab)
    cells = library(guide())[0]
    for node in TOP_DOWN:
        drop(page, guide_node(node)["type"], cells[node])
        expect(page.locator(NODE.format(NEW_IDS[node]))).to_be_visible()
    said(page, "Dodano OUT (wylot).")
    # The ids of the guide: the node menu of a right click, „Zmień id”
    for node, made in NEW_IDS.items():
        if node == made:
            continue
        page.locator(NODE.format(made)).click(button="right")
        menu_item(page, "rename")
        rename(page, node)
        said(page, f"Zmieniono id {made} na {node}.")
    # The links: each node's handle dragged onto the node below it
    for node, (_, ups) in guide_structure().items():
        for up in ups or []:
            drag_link(page, up, node)
            said(page, f"Połączono {up} → {node}.")
    assert structure(page) == guide_structure()
    assert canvas_cells(page) == cells
    expect(page.locator('[data-list="problems"]')).to_have_count(0)

    type_guide(page, {node: node for node in TOP_DOWN}, "mouse")
    computes_the_guides_values(page, "mouse")
    # Placed as the library places it: „Uporządkuj” keeps every cell
    page.get_by_role("button", name="Uporządkuj").click()
    assert canvas_cells(page) == cells


def build_by_keys(tab: Tab) -> tuple[Page, dict[str, str]]:
    """Build the guide's structure from „Nowa sieć” by the keyboard alone.

    Returns the page and the id each of the guide's nodes has on it.
    """
    tab.open("#siec")
    page = tab.page
    page.get_by_role("button", name="Nowa sieć").focus()
    page.keyboard.press("Enter")
    page.locator('[data-palette="outlet"]').focus()
    page.keyboard.press("Enter")
    said(page, "Dodano OUT (wylot).")
    focused = "() => document.activeElement.dataset.node"
    assert page.evaluate(focused) == "OUT"

    def inflow(kind: str, expected: str, into: str) -> None:
        page.keyboard.press("d")
        expect(page.locator('[data-canvas-menu="inflow"]')).to_be_visible()
        for _ in range(INFLOW_MENU.index(kind)):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        noun = {"subcatchment": "zlewnia", "reach": "odcinek", "junction": "złącze"}[
            kind
        ]
        said(page, f"Dodano {expected} ({noun}) jako dopływ {into}.")
        assert page.evaluate(focused) == expected

    # From the outlet up the main stem, each element an inflow of the one in focus
    inflow("junction", "J1", "OUT")
    inflow("reach", "R1", "J1")
    inflow("junction", "J2", "R1")
    inflow("reach", "R2", "J2")
    inflow("subcatchment", "Z1", "R2")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert page.evaluate(focused) == "J2"
    inflow("subcatchment", "Z2", "J2")
    page.locator(NODE.format("J1")).focus()
    inflow("subcatchment", "Z3", "J1")
    # F2: the id in „Dane”; Enter gives the focus back to the node
    page.locator(NODE.format("R2")).focus()
    page.keyboard.press("F2")
    rename(page, "R_A", keys=True)
    said(page, "Zmieniono id R2 na R_A.")
    expect(page.locator(NODE.format("R_A"))).to_be_focused()
    ids = {
        "A": "Z1",
        "B": "Z2",
        "C": "Z3",
        "R_A": "R_A",
        "J1": "J2",
        "R_J1": "R1",
        "J2": "J1",
        "OUT": "OUT",
    }
    built = structure(page)
    for node, (kind, ups) in guide_structure().items():
        assert built[ids[node]] == (kind, [ids[up] for up in ups] if ups else None)
    return page, ids


def test_the_same_network_built_by_the_keyboard_alone(tab: Tab) -> None:
    page, ids = build_by_keys(tab)
    type_guide(page, ids, "keys")
    computes_the_guides_values(page, "keys")


def structure_cells(page: Page) -> dict[str, Cell]:
    """Return the cells of the library's layout of the structure the section keeps."""
    nodes = []
    for node, kind, ups in page.evaluate(STRUCTURE):
        nodes.append({"id": node, "type": kind, **({"from": ups} if ups else {})})
    drawn = structure_schematic({"schema": "hydrolog-network/1", "nodes": nodes})
    return {node["id"]: (node["x"], node["y"]) for node in drawn["nodes"]}


def test_uporzadkuj_lays_out_a_structure_without_any_parameter(tab: Tab) -> None:
    sent: list[tuple[str, Any]] = []
    tab.page.on(
        "request",
        lambda request: (
            sent.append((request.url, request.post_data_json))
            if "/api/run/" in request.url
            else None
        ),
    )
    page, _ = build_by_keys(tab)
    expect(page.locator('[data-list="problems"]')).to_have_count(0)
    tidy = page.get_by_role("button", name="Uporządkuj", exact=True)
    expect(tidy).to_be_enabled()
    # Z3 one cell aside, by keys
    before = canvas_cells(page)
    page.locator(NODE.format("Z3")).focus()
    page.keyboard.press("Shift+ArrowRight")
    expect(page.locator(NODE.format("Z3"))).not_to_have_attribute(
        "data-y", str(before["Z3"][1])
    )

    press(page, tidy, "keys")
    said(page, "Uporządkowano schemat: węzły stoją tak, jak układa je Hydrolog.")
    assert canvas_cells(page) == structure_cells(page)
    # Laid out by the structure alone, on its own channel; nothing was computed
    laid = [
        options
        for url, options in sent
        if "/api/run/route/schematic?channel=siec-layout" in url
    ]
    assert laid
    assert all(options["structure_only"] is True for options in laid)
    assert not any("/api/run/route/network" in url for url, _ in sent)


def test_the_same_network_built_without_any_drag(tab: Tab) -> None:
    page = start(tab)
    cells = library(guide())[0]
    for node in TOP_DOWN:
        page.locator(f'[data-palette="{guide_node(node)["type"]}"]').click()
        expect(page.locator('[data-canvas="placing"]')).to_be_visible()
        page.mouse.click(*cell_point(page, cells[node]))
        expect(page.locator(NODE.format(NEW_IDS[node]))).to_be_visible()
    # „Węzeł…”, „Połącz z…” and a click on the node below
    for node, (_, ups) in guide_structure().items():
        for up in ups or []:
            page.locator(NODE.format(NEW_IDS[up])).click()
            page.get_by_role("button", name="Węzeł…").click()
            menu_item(page, "link")
            expect(page.locator('[data-canvas="linking"]')).to_be_visible()
            page.locator(NODE.format(NEW_IDS[node])).click()
            said(page, f"Połączono {NEW_IDS[up]} → {NEW_IDS[node]}.")
    for node, made in NEW_IDS.items():
        if node != made:
            page.locator(NODE.format(made)).click()
            page.get_by_role("button", name="Węzeł…").click()
            menu_item(page, "rename")
            rename(page, node)
    assert structure(page) == guide_structure()
    assert canvas_cells(page) == cells

    type_guide(page, {node: node for node in TOP_DOWN}, "click")
    computes_the_guides_values(page, "click")


def small_network(page: Page) -> None:
    """Build Z1 → J1 → R1 → OUT and an unconnected Z2 by keys from a new network."""
    page.locator('[data-palette="outlet"]').focus()
    page.keyboard.press("Enter")
    for steps in [1, 3, 0]:  # a reach, a junction, a subcatchment, each above the last
        page.keyboard.press("d")
        for _ in range(steps):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
    page.locator('[data-palette="subcatchment"]').focus()
    page.keyboard.press("Enter")
    assert structure(page) == {
        "OUT": ("outlet", ["R1"]),
        "R1": ("reach", ["J1"]),
        "J1": ("junction", ["Z1"]),
        "Z1": ("subcatchment", None),
        "Z2": ("subcatchment", None),
    }


def focused(page: Page) -> str | None:
    """Return the id of the node that has the focus."""
    found: str | None = page.evaluate(
        "() => document.activeElement.dataset.node || null"
    )
    return found


def link_by_keys(page: Page, source: str, target: str) -> None:
    """Press P on ``source``, go to ``target`` by the arrows among the targets, Enter.

    The arrows go to the nearest target in their direction: down first, then sideways,
    then up, until ``target`` has the focus.
    """
    page.locator(NODE.format(source)).focus()
    page.keyboard.press("p")
    for _ in range(8):
        if focused(page) == target:
            break
        before = focused(page)
        for key in ["ArrowDown", "ArrowLeft", "ArrowRight", "ArrowUp"]:
            page.keyboard.press(key)
            if focused(page) != before:
                break
    assert focused(page) == target
    page.keyboard.press("Enter")


def test_each_refusal_says_its_reason(tab: Tab) -> None:
    page = start(tab)
    small_network(page)
    before = structure(page)
    # Out of the outlet: P refuses at once
    page.locator(NODE.format("OUT")).focus()
    page.keyboard.press("p")
    said(page, "Nie można: z wylotu OUT nic nie odpływa.")
    # Into a subcatchment, and a cycle: the verdict stands on the target before the drop
    drag_link(page, "R1", "Z1")
    said(page, "Nie można: zlewnia Z1 nie przyjmuje dopływów.")
    page.locator(NODE.format("R1")).click()
    handle = page.locator(NODE.format("R1") + " .handle-dot").bounding_box()
    assert handle is not None
    page.mouse.move(
        handle["x"] + handle["width"] / 2, handle["y"] + handle["height"] / 2
    )
    page.mouse.down()
    page.mouse.move(*centre_of(page, "J1"), steps=8)
    said(page, "J1: nie można, pętla R1 → J1 → R1.")
    expect(page.locator("svg.schem g.verdict")).to_have_attribute("data-state", "no")
    page.mouse.up()
    said(page, "Nie można: pętla R1 → J1 → R1.")
    # D on a node that takes no more inflows
    page.locator(NODE.format("Z2")).focus()
    page.keyboard.press("d")
    said(page, "Nie można: zlewnia Z2 nie przyjmuje dopływów.")
    page.locator(NODE.format("R1")).focus()
    page.keyboard.press("d")
    said(page, "Nie można: odcinek R1 przyjmuje jeden dopływ i ma już J1.")
    expect(page.locator("[data-canvas-menu]")).to_have_count(0)
    # A taken cell refuses a new element
    x, y = page.evaluate(
        "() => { const n = document.querySelector('g.node[data-node=\"R1\"]');"
        " return [Number(n.dataset.x), Number(n.dataset.y)]; }"
    )
    drop(page, "junction", (x, y))
    said(page, "Nie można dodać elementu: to pole zajmuje R1.")
    assert structure(page) == before

    # A second inflow into a reach offers „Wstaw złącze”; „Anuluj” leaves the network
    link_by_keys(page, "Z2", "R1")
    said(page, "Nie można: odcinek R1 przyjmuje jeden dopływ i ma już J1.")
    offer = page.locator(".offer")
    expect(offer).to_contain_text("Złącze nad R1 zbierze J1 i Z2 i odpłynie do R1")
    expect(offer.get_by_role("button", name="Wstaw złącze")).to_be_focused()
    page.keyboard.press("Escape")
    expect(offer).to_have_count(0)
    assert structure(page) == before
    link_by_keys(page, "Z2", "R1")
    expect(offer.get_by_role("button", name="Wstaw złącze")).to_be_focused()
    page.keyboard.press("Enter")
    said(page, "Wstawiono złącze J2: J1, Z2 odpływają przez nie do R1.")
    assert structure(page) == {
        **before,
        "R1": ("reach", ["J2"]),
        "J2": ("junction", ["J1", "Z2"]),
    }
    # One step undoes it
    page.get_by_role("button", name="Cofnij").click()
    assert structure(page) == before

    # The ids the library refuses, as they are typed
    page.locator(NODE.format("Z1")).click()
    field = page.locator(f'{SECTION} [data-field="id"]')
    for typed, message in [
        (
            "z2",
            "To id ma już węzeł Z2 (wielkość liter nie ma znaczenia) · duplicate_node",
        ),
        (
            "con",
            "To nazwa urządzenia Windows (con, prn, aux, nul, com1–com9, lpt1–lpt9):"
            " wybierz inne id · reserved_name",
        ),
        (
            "a b",
            "Nieprawidłowe id: litery, cyfry, _, . i -, bez spacji; na początku litera,"
            " cyfra albo _, bez kropki na końcu, najwyżej 64 znaki · invalid_id",
        ),
    ]:
        field.locator("input").fill(typed)
        expect(field.locator(".err")).to_have_text(message)
        field.locator("input").press("Enter")
        assert "Z1" in structure(page)
    field.locator("input").press("Escape")
    expect(field.locator("input")).to_have_value("Z1")


def test_problems_appear_and_go_as_edits_make_and_mend_them(
    tab: Tab, tmp_path: Path
) -> None:
    page = start(tab)
    problems = page.locator('[data-list="problems"] li')
    expect(problems).to_have_text(["!Sieć nie ma węzłów: dodaj je z palety."])
    expect(page.locator(BADGE)).to_have_text(re.compile("empty"))
    page.locator('[data-palette="outlet"]').focus()
    page.keyboard.press("Enter")
    expect(problems).to_have_text(
        ["!Węzeł OUT: przyjmuje dokładnie jeden dopływ (ma 0)."]
    )
    expect(page.locator(NODE.format("OUT"))).to_have_attribute("data-problems", "1")
    expect(page.locator(NODE.format("OUT"))).to_have_attribute(
        "aria-label", re.compile("problem: Węzeł OUT: przyjmuje dokładnie jeden dopływ")
    )
    page.locator('[data-palette="subcatchment"]').focus()
    page.keyboard.press("Enter")
    expect(problems).to_have_text(
        [
            "!Węzeł OUT: przyjmuje dokładnie jeden dopływ (ma 0).",
            "!Węzeł Z1 nie odpływa do żadnego węzła: połącz go z węzłem poniżej.",
        ]
    )
    # An item chooses its node
    problems.nth(1).get_by_role("button").click()
    expect(page.locator(NODE.format("Z1"))).to_have_attribute("aria-pressed", "true")
    link_by_keys(page, "Z1", "OUT")
    expect(problems).to_have_count(0)
    expect(page.locator(NODE.format("OUT"))).not_to_have_attribute(
        "data-problems", re.compile(".")
    )
    # A second outlet: in the list only, on no node
    page.locator('[data-palette="outlet"]').focus()
    page.keyboard.press("Enter")
    expect(problems.first).to_have_text(
        "!Sieć ma kilka wylotów (OUT, OUT2); dozwolony jest jeden."
    )
    expect(
        page.locator('[data-list="problems"] li[data-problem="several_outlets"] button')
    ).to_have_count(0)
    page.locator(NODE.format("OUT2")).focus()
    page.keyboard.press("Delete")
    said(page, "Usunięto OUT2.")
    expect(problems).to_have_count(0)

    # A file can have what the edits never make: its problems at once, a cycle dashed
    looped = {
        "schema": "hydrolog-network/1",
        "nodes": [
            {
                "id": "A",
                "type": "subcatchment",
                "times_min": [0, 10],
                "discharge_m3s": [0, 1],
            },
            {"id": "J1", "type": "junction", "from": ["A", "R1"]},
            {
                "id": "R1",
                "type": "reach",
                "from": ["J1"],
                "method": "lag",
                "lag_min": 10,
            },
            {"id": "OUT", "type": "outlet", "from": ["J1", "X"]},
        ],
    }
    path = tmp_path / "petla.json"
    path.write_text(json.dumps(looped), encoding="utf-8")
    load_network(page, path)
    expect(
        page.locator('[data-list="problems"] li[data-problem="cycle"]')
    ).to_have_text(
        "!Pętla J1 → R1 → J1: woda nie może wracać do węzła, z którego wypłynęła."
    )
    expect(
        page.locator('[data-list="problems"] li[data-problem="several_downstream"]')
    ).to_contain_text("J1")
    expect(
        page.locator('[data-list="problems"] li[data-problem="unknown_upstream"]')
    ).to_contain_text("X")
    expect(page.locator("svg.schem polyline.ln.loop")).to_have_count(2)
    # Mended: R1 no longer flows back, OUT takes J1 only
    page.locator(NODE.format("R1")).focus()
    page.keyboard.press("o")
    said(page, "Odłączono R1 od J1.")
    expect(page.locator("svg.schem polyline.ln.loop")).to_have_count(0)
    expect(
        page.locator('[data-list="problems"] li[data-problem="cycle"]')
    ).to_have_count(0)


def save_document(page: Page, path: Path) -> dict[str, Any]:
    """Press the save button of step 1 and return the document it downloads."""
    with page.expect_download() as saved:
        page.locator(f'{SECTION} [data-action="save"]').click()
    saved.value.save_as(path)
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def steps_back(page: Page) -> int:
    """Press Ctrl+Z on „Cofnij” until nothing is left to undo; return the steps."""
    undo = page.locator('[data-canvas="undo"]')
    undo.focus()
    count = 0
    while undo.get_attribute("aria-disabled") == "false":
        page.keyboard.press("Control+z")
        count += 1
        assert count <= 100
    return count


def test_undo_to_the_start_and_redo_to_the_end_give_the_same_document(
    tab: Tab, tmp_path: Path
) -> None:
    page = start(tab)
    small_network(page)  # five steps: two from the palette, three by D
    # Two moves by keys within a second are one step
    page.locator(NODE.format("Z2")).focus()
    page.keyboard.press("Shift+ArrowRight")
    page.keyboard.press("Shift+ArrowRight")
    # „Wstaw złącze”: one step
    link_by_keys(page, "Z2", "R1")
    expect(page.get_by_role("button", name="Wstaw złącze")).to_be_focused()
    page.keyboard.press("Enter")
    said(page, "Wstawiono złącze J2: J1, Z2 odpływają przez nie do R1.")
    # A description, a rename, a parameter typed key by key: one step each
    page.locator(NODE.format("Z1")).click()
    page.locator(
        f'{SECTION} [data-structure="Z1"] [data-field="description"] textarea'
    ).fill("Zlewnia górna")
    field = page.locator(f'{SECTION} [data-field="id"] input')
    field.fill("Gorna")
    field.press("Enter")
    page.locator(NODE.format("R1")).click()
    lag = page.locator('[data-node-form="R1"] [data-key="lag.lag_min"] input')
    lag.focus()
    page.keyboard.type("25")
    page.keyboard.press("Tab")
    # „Usuń i połącz”: J1 goes, Gorna flows into J2
    page.locator(NODE.format("J1")).click()
    page.get_by_role("button", name="Usuń i połącz").click()
    said(page, "Usunięto J1; Gorna odpływa teraz do J2.")
    end = save_document(page, tmp_path / "end.json")

    assert steps_back(page) == 11
    assert structure(page) == {}
    expect(page.locator('[data-canvas="empty"]')).to_be_visible()
    said(page, "Cofnięto zmianę.")
    redo = page.locator('[data-canvas="redo"]')
    redo.focus()
    count = 0
    while redo.get_attribute("aria-disabled") == "false":
        page.keyboard.press("Control+y")
        count += 1
    assert count == 11
    assert save_document(page, tmp_path / "again.json") == end
    # A new edit after undo leaves nothing to redo
    page.get_by_role("button", name="Cofnij").click()
    page.locator(NODE.format("Gorna")).focus()
    page.keyboard.press("Shift+ArrowLeft")
    expect(redo).to_have_attribute("aria-disabled", "true")


def test_a_rename_updates_from_and_keeps_the_inflows_column(tab: Tab) -> None:
    tab.open("#siec")
    page = tab.page
    load_network(
        page,
        FIXTURES / "network_flood.json",
        FIXTURES / "network_inflows.csv",
        FIXTURES / "pond_rating.csv",
    )
    expect(page.locator("svg.schem g.node")).to_have_count(6)
    page.locator(NODE.format("A")).click()
    field = page.locator(f'{SECTION} [data-field="id"] input')
    field.fill("Gorna")
    field.press("Enter")
    said(
        page,
        "Zmieniono id A na Gorna. Kolumna pliku dopływów zostaje „A” (value_column):"
        " zlewnia czytała ją po dawnym id.",
    )
    assert structure(page)["R1"] == ("reach", ["Gorna"])
    expect(
        page.locator('[data-node-form="Gorna"] [data-key="value_column"] input')
    ).to_have_value("A")
    expect(page).to_have_url(re.compile(r"#siec/Gorna$"))

    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
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
    sent = json.loads(
        page.request.get(tab.base + "api/files/in/network_flood.json").text()
    )
    nodes = {node["id"]: node for node in sent["nodes"]}
    assert nodes["Gorna"]["value_column"] == "A"
    assert nodes["R1"]["from"] == ["Gorna"]


def test_a_draft_is_saved_and_reopened(tab: Tab, tmp_path: Path) -> None:
    page = start(tab)
    small_network(page)
    shape = structure(page)
    step = page.locator(f'{SECTION} [data-step="network"]')
    step.locator('[data-field="description"] textarea').fill(
        "Szkic sieci\nw dwóch wierszach"
    )
    page.locator(NODE.format("Z1")).click()
    page.locator(
        f'{SECTION} [data-structure="Z1"] [data-field="description"] textarea'
    ).fill("Zlewnia górna")
    problems = page.locator('[data-list="problems"] li').all_text_contents()
    assert problems
    save = page.locator(f'{SECTION} [data-action="save"]')
    expect(save).to_have_text("Zapisz szkic")
    draft = save_document(page, tmp_path / "siec.json")
    expect(page.locator(".toast")).to_contain_text(
        "Zapisano szkic siec.json: route network go nie przyjmie,"
        " dopóki nie poprawisz problemów"
    )
    assert draft["description"] == "Szkic sieci\nw dwóch wierszach"
    # The description first; the network's rainfall (PMAXTP, nothing given yet) before
    # the nodes
    assert list(draft)[:4] == ["schema", "description", "rainfall", "nodes"]
    z1 = next(node for node in draft["nodes"] if node["id"] == "Z1")
    assert list(z1)[-2:] == ["description", "position"]
    assert z1["description"] == "Zlewnia górna"
    cells = canvas_cells(page)
    # route network refuses it; the GUI reopens it as it was saved, without a question
    try:
        run_command("route network", {"network_file": str(tmp_path / "siec.json")})
    except Exception as error:  # noqa: BLE001 - any refusal of the library
        assert getattr(error, "code", None) == "data_error"
    else:
        raise AssertionError("route network computed a draft")
    page.locator(SECTION).get_by_role("button", name="Wyczyść").click()
    expect(page.locator("svg.schem")).to_have_count(0)
    load_network(page, tmp_path / "siec.json")
    expect(page.locator("svg.schem g.node")).to_have_count(5)
    assert canvas_cells(page) == cells
    assert structure(page) == shape
    expect(step.locator('[data-field="description"] textarea')).to_have_value(
        "Szkic sieci\nw dwóch wierszach"
    )
    expect(page.locator('[data-list="problems"] li')).to_have_text(problems)


def test_wyczysc_and_nowa_siec_ask_when_the_network_changed(
    tab: Tab, tmp_path: Path
) -> None:
    tab.open("#siec")
    page = tab.page
    load_network(page)
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    clear = page.locator(SECTION).get_by_role("button", name="Wyczyść")
    dialog = page.locator('dialog[data-confirm="clear"]')
    # Unchanged since it was opened: no question
    clear.click()
    expect(page.locator("svg.schem")).to_have_count(0)
    load_network(page)
    page.locator(NODE.format("C")).focus()
    page.keyboard.press("Shift+ArrowRight")
    clear.click()
    expect(dialog).to_be_visible()
    expect(dialog.get_by_role("button", name="Anuluj")).to_be_focused()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    # „Nowa sieć” asks too, and goes on when told
    page.get_by_role("button", name="Nowa sieć").click()
    question = page.locator('dialog[data-confirm="new"]')
    expect(question).to_contain_text("Zacząć nową sieć?")
    question.get_by_role("button", name="Nowa sieć").click()
    expect(page.locator('[data-canvas="empty"]')).to_be_visible()
    # A saved network is no change; undoing back to it neither
    load_network(page)
    page.locator(NODE.format("C")).focus()
    page.keyboard.press("Shift+ArrowRight")
    save_document(page, tmp_path / "siec.json")
    clear.click()
    expect(page.locator("svg.schem")).to_have_count(0)
    load_network(page)
    page.locator(NODE.format("C")).focus()
    page.keyboard.press("Shift+ArrowRight")
    page.keyboard.press("Control+z")
    clear.click()
    expect(page.locator("svg.schem")).to_have_count(0)


def test_descriptions_are_shown_saved_and_never_stale(tab: Tab, tmp_path: Path) -> None:
    tab.open("#siec")
    page = tab.page
    load_network(page)
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    page.locator(NODE.format("C")).click()
    text = page.locator(
        f'{SECTION} [data-structure="C"] [data-field="description"] textarea'
    )
    text.fill("Zlewnia boczna\nz zalewem")
    page.locator(
        f'{SECTION} [data-step="network"] [data-field="description"] textarea'
    ).fill("Przykład z instrukcji")
    # In the node's name and tooltip, and in the node table; the result stays current
    expect(page.locator(NODE.format("C"))).to_have_attribute(
        "aria-label", re.compile("Zlewnia boczna\nz zalewem")
    )
    expect(page.locator(NODE.format("C") + " > title")).to_contain_text(
        "Zlewnia boczna"
    )
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    expect(page.locator('[data-stale="true"]')).to_have_count(0)
    page.get_by_role("radio", name="Tabela węzłów").click()
    row = page.locator('.node-table tr[data-node-row="C"]')
    expect(row.locator('[data-column="description"]')).to_have_text(
        "Zlewnia boczna\nz zalewem"
    )
    expect(row.locator('[data-column="to"]')).to_have_text("J2")
    page.get_by_role("radio", name="Schemat").click()
    document = save_document(page, tmp_path / "siec.json")
    assert document["description"] == "Przykład z instrukcji"
    node = next(item for item in document["nodes"] if item["id"] == "C")
    assert list(node)[-2:] == ["description", "position"]
    # Too long or with a tab: the field says why and the network waits
    text.fill("x" * 501)
    expect(
        page.locator(f'{SECTION} [data-structure="C"] [data-field="description"] .err')
    ).to_have_text("Opis ma 501 znaków; najwyżej 500 · too_long")
    text.fill("a\tb")
    expect(
        page.locator(f'{SECTION} [data-structure="C"] [data-field="description"] .err')
    ).to_contain_text("control_character")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "invalid")


def test_a_link_goes_by_a_click_and_delete_by_o_and_by_usun_i_polacz(tab: Tab) -> None:
    page = start(tab)
    small_network(page)
    # A click on the line between J1 and R1 chooses the link; Delete removes it
    j1 = centre_of(page, "J1")
    r1 = centre_of(page, "R1")
    page.mouse.click((j1[0] + r1[0]) / 2, (j1[1] + r1[1]) / 2)
    said(page, "Wybrano połączenie J1 → R1; Delete je usuwa.")
    page.keyboard.press("Delete")
    said(page, "Odłączono J1 od R1.")
    assert structure(page)["R1"] == ("reach", None)
    page.keyboard.press("Control+z")
    assert structure(page)["R1"] == ("reach", ["J1"])
    # O on a node, and „Odpływa do: brak” in „Dane”
    page.locator(NODE.format("Z1")).focus()
    page.keyboard.press("o")
    said(page, "Odłączono Z1 od J1.")
    page.keyboard.press("o")
    said(page, "Z1 nie odpływa do żadnego węzła.")
    page.locator(NODE.format("Z1")).click()
    to = page.locator(f'{SECTION} [data-structure="Z1"] [data-field="to"] select')
    expect(to.locator('option[value="Z2"]')).to_be_disabled()
    to.select_option("J1")
    said(page, "Połączono Z1 → J1.")
    to.select_option("")
    said(page, "Odłączono Z1 od J1.")
    # „Usuń i połącz” through the node menu: J1's inflow takes its place
    to.select_option("J1")
    page.locator(NODE.format("J1")).click(button="right")
    menu_item(page, "bridge")
    said(page, "Usunięto J1; Z1 odpływa teraz do R1.")
    assert structure(page)["R1"] == ("reach", ["Z1"])
    assert "J1" not in structure(page)


def test_an_edge_through_a_node_is_a_hint(tab: Tab) -> None:
    page = start(tab)
    small_network(page)
    hints = page.locator('[data-list="hints"] li')
    expect(hints).to_have_count(0)
    # OUT two cells lower: the edge R1 → OUT runs down the cells below R1
    x, y = canvas_cells(page)["R1"]
    page.locator(NODE.format("OUT")).focus()
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")
    # Z2 onto one of them, by keys: a hint, not a problem
    z2 = canvas_cells(page)["Z2"]
    page.locator(NODE.format("Z2")).focus()
    for _ in range(x + 1 - z2[0]):
        page.keyboard.press("Shift+ArrowDown")
    for _ in range(z2[1] - y):
        page.keyboard.press("Shift+ArrowLeft")
    assert canvas_cells(page)["Z2"] == (x + 1, y)
    expect(hints).to_have_text(
        [
            "iKrawędź R1 → OUT biegnie przez węzeł Z2;"
            " „Uporządkuj” rozkłada sieć bez takich przejść."
        ]
    )
    expect(page.locator("svg.schem circle.through-mark")).to_have_count(1)
    expect(
        page.locator('svg.schem polyline.ln.through[data-edge="R1>OUT"]')
    ).to_have_count(1)
    expect(page.locator(NODE.format("Z2"))).to_have_attribute(
        "aria-label", re.compile("przez ten węzeł biegnie krawędź R1 → OUT")
    )
    expect(
        page.locator('[data-list="problems"] li[data-problem="through"]')
    ).to_have_count(0)
    # The moves of Z2 by keys are one step: one undo takes it back
    page.keyboard.press("Control+z")
    assert canvas_cells(page)["Z2"] == z2
    expect(hints).to_have_count(0)


def test_a_phone_in_the_dark_theme_edits_through_the_menus(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    tab.open("#siec")
    page = tab.page
    page.get_by_role("button", name="Dane").click()
    page.get_by_role("button", name="Nowa sieć").click()
    # „Dane” stays open at step 1, the network's rainfall first; Escape shows the canvas
    left = page.locator(f"{SECTION} .view-panel.left")
    expect(left.locator('[data-rain-part="siec-net"]')).to_be_visible()
    page.keyboard.press("Escape")
    expect(left).to_be_hidden()
    expect(page.locator('[data-canvas="empty"]')).to_be_visible()
    # The palette is a menu: an element, then a tap on a cell
    expect(page.locator('[data-palette="outlet"]')).to_be_hidden()
    add = page.get_by_role("button", name="Dodaj element")
    add.click()
    menu_item(page, "outlet")
    page.mouse.click(*cell_point(page, (1, 0)))
    said(page, "Dodano OUT (wylot).")
    add.click()
    menu_item(page, "subcatchment")
    page.mouse.click(*cell_point(page, (0, 0)))
    said(page, "Dodano Z1 (zlewnia).")
    assert page.evaluate(SIDEWAYS) == []
    # Links through the node menu of „Węzeł…”
    page.get_by_role("button", name="Węzeł…").click()
    menu_item(page, "link")
    page.locator(NODE.format("OUT")).click()
    said(page, "Połączono Z1 → OUT.")
    assert structure(page) == {"OUT": ("outlet", ["Z1"]), "Z1": ("subcatchment", None)}
    assert page.evaluate(SIDEWAYS) == []
    # Z1 aside by „Przesuń” and a tap; „Uporządkuj” takes it back without any value
    page.get_by_role("button", name="Przesuń").click()
    page.mouse.click(*cell_point(page, (0, 1)))
    expect(page.locator(NODE.format("Z1"))).to_have_attribute("data-y", "1")
    tidy = page.get_by_role("button", name="Uporządkuj", exact=True)
    tidy.click()
    said(page, "Uporządkowano schemat: węzły stoją tak, jak układa je Hydrolog.")
    assert canvas_cells(page) == structure_cells(page)
    # „Odpływa do” in „Dane” takes the link away; two outlets leave nothing to tidy
    page.locator(NODE.format("Z1")).click()
    expect(page.locator(f"{SECTION} .view-panel.left")).to_be_visible()
    page.locator(
        f'{SECTION} [data-structure="Z1"] [data-field="to"] select'
    ).select_option("")
    assert structure(page)["OUT"] == ("outlet", None)
    assert page.evaluate(SIDEWAYS) == []
    expect(tidy).to_be_disabled()
