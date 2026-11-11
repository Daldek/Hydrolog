"""The network's rainfall first in „Sieć i trasowanie” (plan 2026-11-10-network-wizard).

Stage W3: „Nowa sieć” opens step 1 with the name, the description, the network's time
step and „Opad sieci” (Hydrogram zlewni's step 2, PMAXTP at first), and the empty canvas
says to give that rainfall first. The network's PMAXTP depth is fetched once at its
point, p and duration on the channel ``siec-pmaxtp``, kept with the stored inputs
(``hydrolog-gui/siec/3``) and not fetched again after a reload. A subcatchment made from
rainfall in a network without a rainfall („Brak”) is the problem „Brak opadu” of its
node, and „Oblicz sieć” sends nothing until the network has a rainfall. Every section
mounted with Sieć's network open, a subcatchment chosen (its panel beside „Dane”, stage
W4), keeps the page's ids unique.
"""

import re

from playwright.sync_api import Page, Request, expect

from tests.e2e.conftest import KAMIENNIK_POINT, Tab, input_text
from tests.e2e.test_siec import BADGE, NODE
from tests.e2e.test_siec_editor import (
    PANEL,
    SECTION,
    drag_link,
    drop,
    said,
    start,
    type_node,
)

STEP = f'{SECTION} [data-step="network"]'
RAIN = f'{STEP} [data-rain-part="siec-net"]'
STORED = "hydrolog-gui/siec/3"
PMAXTP = "/api/run/precip/pmaxtp"
ROUTE = "/api/run/route/network"
# The parts of step 1 in the order of the page: the name, the description, the time step
# and the network's rainfall
ORDER = """() => {
  const step = document.querySelector(
    'section[data-section="siec"] [data-step="network"]');
  const parts = ['[data-key="name"]', '[data-field="description"]',
                 '[data-field="timestep_min"]', '[data-rain-part="siec-net"]'];
  const found = parts.map((part) => step.querySelectorAll(part));
  const counts = found.map((list) => list.length);
  const ordered = found.every((list, at) => at === 0
    || (found[at - 1][0].compareDocumentPosition(list[0])
        & Node.DOCUMENT_POSITION_FOLLOWING));
  return {counts, ordered};
}"""
DUPLICATES = """() => {
  const seen = new Map();
  for (const element of document.querySelectorAll('[id]')) {
    seen.set(element.id, (seen.get(element.id) || 0) + 1);
  }
  return [...seen].filter(([, count]) => count > 1).map(([id]) => id).sort();
}"""


def requests_to(page: Page, path: str) -> list[Request]:
    """Return the list the page's requests to ``path`` are appended to from now on."""
    found: list[Request] = []

    def keep(request: Request) -> None:
        if path in request.url:
            found.append(request)

    page.on("request", keep)
    return found


def test_a_new_network_opens_at_its_rainfall(tab: Tab) -> None:
    page = start(tab)
    assert page.evaluate(ORDER) == {"counts": [1, 1, 1, 1], "ordered": True}
    rain = page.locator(RAIN)
    expect(rain).to_be_visible()
    expect(rain.locator("h4")).to_contain_text("Opad sieci")
    expect(rain.get_by_role("radio", name="PMAXTP", exact=True)).to_have_attribute(
        "aria-checked", "true"
    )
    expect(rain.get_by_role("radio").filter(has_text="Brak")).to_have_attribute(
        "aria-checked", "false"
    )
    # The network's time step only: „Opad sieci” has none of its own
    expect(page.locator(f'{STEP} [data-field="timestep_min"]')).to_have_count(1)
    expect(page.locator('[data-canvas="empty"]')).to_contain_text(
        "Najpierw podaj opad sieci w kroku 1 „Sieć”"
    )


def test_the_networks_pmaxtp_depth_is_fetched_once_and_kept(tab: Tab) -> None:
    page = start(tab)
    fetches = requests_to(page, PMAXTP)
    page.locator("#siec-net-pmaxtp_latitude").fill(
        input_text(KAMIENNIK_POINT["latitude"])
    )
    page.locator("#siec-net-pmaxtp_longitude").fill(
        input_text(KAMIENNIK_POINT["longitude"])
    )
    page.locator("#siec-net-pmaxtp_probability_pct").select_option("1")
    page.locator("#siec-net-pmaxtp_duration_min").select_option("720")
    depth = page.locator("#siec-net-pmaxtp_depth")
    expect(depth).to_have_value("101,82")
    expect(page.locator(RAIN).locator("h4 .meta")).to_have_text(
        "101,8 mm · 12 h · p 1%"
    )
    options = {
        **KAMIENNIK_POINT,
        "duration_min": 720,
        "probability_percent": 1,
        "method": "POT",
    }
    assert [request.url.rsplit("?", 1)[1] for request in fetches] == [
        "channel=siec-pmaxtp"
    ]
    assert fetches[0].post_data_json == options
    stored = page.evaluate(
        "(key) => JSON.parse(localStorage.getItem(key)).network.pmaxtp_fetched", STORED
    )
    assert stored == {**options, "depth_mm": 101.82}
    # Remembered with the inputs: a reload shows it without a fetch
    page.reload()
    expect(depth).to_have_value("101,82")
    page.wait_for_timeout(1000)
    assert len(fetches) == 1


def test_a_subcatchment_without_any_rainfall_is_a_problem_of_its_node(
    tab: Tab,
) -> None:
    page = start(tab)
    page.locator(RAIN).get_by_role("radio", name="Brak", exact=True).click()
    expect(page.locator(f'{RAIN} [data-rain="none"]')).to_be_visible()
    drop(page, "outlet", (1, 0))
    said(page, "Dodano OUT (wylot).")
    drop(page, "subcatchment", (0, 0))
    said(page, "Dodano Z1 (zlewnia).")
    drag_link(page, "Z1", "OUT")
    said(page, "Połączono Z1 → OUT.")
    # The guide's C takes the network's rainfall: all its values given, none is missing
    type_node(page, "C", "Z1", "mouse")
    item = page.locator('[data-list="problems"] li[data-node="Z1"]')
    expect(item).to_have_count(1)
    expect(item).to_have_attribute("data-problem", "missing_field")
    expect(item).to_contain_text(
        "Z1: Brak opadu: ustaw opad sieci w kroku 1 albo własny opad zlewni"
    )
    expect(page.locator(NODE.format("Z1"))).to_have_class(re.compile(r"\bwrong\b"))
    # The node's „Jak w sieci” in its panel points at step 1
    expect(page.locator(f'{PANEL} [data-goto="network-rain"]')).to_be_visible()
    # „Oblicz sieć” sends nothing
    runs = requests_to(page, ROUTE)
    page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "invalid")
    expect(page.locator(BADGE)).to_contain_text("Z1 · rainfall")
    page.wait_for_timeout(500)
    assert runs == []
    # The network's rainfall mends it, and the network computes
    rain = page.locator(RAIN)
    rain.get_by_role("radio", name="Hietogram", exact=True).click()
    rain.get_by_role("radio", name="Blokowy", exact=True).click()
    page.locator("#siec-net-total_mm").fill("30")
    page.locator("#siec-net-duration_min").fill("60")
    expect(page.locator('[data-list="problems"]')).to_have_count(0)
    expect(page.locator(NODE.format("Z1"))).not_to_have_class(re.compile(r"\bwrong\b"))
    with page.expect_response(lambda answer: ROUTE in answer.url):
        page.get_by_role("button", name="Oblicz sieć").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    assert len(runs) == 1


def test_every_section_with_the_network_open_keeps_ids_unique(tab: Tab) -> None:
    page = start(tab)
    expect(page.locator(RAIN)).to_be_visible()
    assert page.evaluate(DUPLICATES) == []
    # A subcatchment chosen: its panel with Hydrogram's steps beside „Opad sieci”, and
    # Hydrogram zlewni's own steps mounted
    drop(page, "subcatchment", (0, 0))
    said(page, "Dodano Z1 (zlewnia).")
    page.locator(NODE.format("Z1")).click()
    expect(page.locator('[data-node-form="Z1"]')).to_be_visible()
    expect(page.locator(f"{PANEL} #sn-rain-source-label")).to_be_visible()
    hydrogram = page.locator('section[data-section="hydrogram"]')
    expect(hydrogram.locator("#hg-rain-source-label")).to_be_attached()
    assert page.evaluate(DUPLICATES) == []
