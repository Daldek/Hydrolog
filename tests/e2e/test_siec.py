"""„Sieć i trasowanie” (GUI plan S4, D13, D14, D18) in Chromium on the live server.

The example network is drawn vertically from ``route schematic`` before any run: the
sources at the top, the outlet at the bottom, each label on the side of its node
without a tributary. „Oblicz sieć” writes the document to the session and runs
``route network``; the outlet's and every node's values are those of the library. A
network loaded from a file with its referenced files (an inflows file and a rating
table) computes too, and every node type opens its form. A node is chosen by a click,
Enter or Space on the schematic and in the node table; a changed reach method shows its
fields and marks the result stale. The SVG of Hydrolog and the network's document
export, the document unchanged. A phone in the dark theme shows the schematic without
scrolling sideways.
"""

import json
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect

from hydrolog.catalog import run_command
from hydrolog.testing import example_network_document
from tests.e2e.conftest import Tab

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
BADGE = ".topbar .badge.status"
NODE = 'svg.schem g.node[data-node="{}"]'
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""


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


def open_section(tab: Tab) -> Page:
    """Open Sieć and wait for the schematic of the example."""
    tab.open("#siec")
    expect(tab.page.locator("svg.schem g.node")).to_have_count(8)
    return tab.page


def compute(page: Page) -> None:
    """Press „Oblicz sieć” and wait for the current result."""
    with page.expect_response(lambda answer: "/api/run/route/network" in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")


def centre(page: Page, node: str) -> float:
    """Return the vertical position of a node of the schematic."""
    return float(
        page.locator(NODE.format(node) + " circle.halo").get_attribute("cy") or 0
    )


def test_the_example_is_drawn_first_and_computes_the_librarys_values(tab: Tab) -> None:
    runs: list[str] = []
    tab.page.on(
        "request",
        lambda request: (
            runs.append(request.url) if "/api/run/" in request.url else None
        ),
    )
    page = open_section(tab)

    # Drawn before any run, turned: the sources on top, the outlet at the bottom
    assert any("/api/run/route/schematic" in url for url in runs)
    assert not any("/api/run/route/network" in url for url in runs)
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

    # The node table: every node's peak, time and volume, rows in the order computed
    page.get_by_role("radio", name="Tabela węzłów").click()
    rows = page.locator(".node-table tbody tr")
    expect(rows).to_have_count(8)
    for node, value in expected.items():
        cells = page.locator(f'.node-table tr[data-node-row="{node}"] td')
        expect(cells.nth(1)).to_have_text(polish(value["peak_m3s"], 2))
        expect(cells.nth(2)).to_have_text(hmm(value["time_to_peak_min"]))
        expect(cells.nth(3)).to_have_text(polish(value["volume_m3"] / 1000, 1))

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
    page = open_section(tab)
    page.locator('[data-input="network"]').set_input_files(
        [
            FIXTURES / "network_flood.json",
            FIXTURES / "network_inflows.csv",
            FIXTURES / "pond_rating.csv",
        ]
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
    assert reach == {
        "id": "R_A",
        "type": "reach",
        "from": ["A"],
        "method": "muskingum",
        "k_min": 30,
        "x": 0.2,
    }


def test_the_svg_and_the_network_document_export(tab: Tab) -> None:
    page = open_section(tab)
    with page.expect_download() as saved:
        page.locator('[data-export="json-network"]').click()
    document = json.loads(Path(saved.value.path()).read_text(encoding="utf-8"))
    assert document == example_network_document()

    compute(page)
    with page.expect_download() as drawing:
        page.locator('[data-export="svg"]').click()
    svg = Path(drawing.value.path()).read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<svg")
    assert drawing.value.suggested_filename == "siec.svg"


def test_a_phone_in_the_dark_theme_shows_the_schematic(new_tab: Any) -> None:
    tab = new_tab(width=390, height=844, theme="dark")
    page = open_section(tab)
    expect(page.locator("svg.schem")).to_be_visible()
    assert page.evaluate(SIDEWAYS) == []
    page.locator(NODE.format("B")).click()
    expect(
        page.locator('section[data-section="siec"] .view-panel.left')
    ).to_be_visible()
    expect(page.locator('[data-node-form="B"]')).to_be_attached()
    assert page.evaluate(SIDEWAYS) == []
