"""The final smoke of the GUI (plan S7, D17) in Chromium, against the live server.

Every registered section opens as a new document at 1440 and at 390 px, in the light
and in the dark theme, with its first visit in place (a section's example, Hydrogram
zlewni's empty steps), nothing scrolling sideways and no console error, page error or
CSP violation (the tab's checks); so does the guide. The numbers the guide quotes (the
elements with ``data-example`` in ``instrukcja/index.html``) are the ones the page shows
for the shipped examples and for the guide's worked example typed as the guide says.
"""

import re
from collections.abc import Callable

import pytest
from playwright.sync_api import Locator, Page, expect

from tests.e2e.conftest import FIXTURES, Tab

BADGE = ".topbar .badge.status"
SPACES = re.compile(r"[\s\u00a0\u202f]+")
REGISTERED = "async () => (await import('./src/app.js')).ORDERED.map((item) => item.id)"
# The document and an open sheet: neither may scroll sideways.
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""
SAMPLE = '.handoff[data-file="in/maksima_roczne.csv"]'
"""Statystyka's card of the shipped sample, which a first visit uploads."""
# What a first visit of each section shows once it is in place.
READY: dict[str, Callable[[Page], None]] = {
    "hydrogram": lambda page: expect(
        page.locator('section[data-section="hydrogram"] .step > summary .title')
    ).to_have_text(["Zlewnia", "Hietogram", "Hydrogram"]),
    "siec": lambda page: expect(page.locator("svg.schem g.node")).to_have_count(8),
    "statystyka": lambda page: expect(
        page.locator(f'section[data-section="statystyka"] {SAMPLE}')
    ).to_contain_text("26 wierszy"),
    "kalkulatory": lambda page: expect(
        page.locator('section[data-section="kalkulatory"] .cmd-list .cmd-item')
    ).to_have_count(16),
    "polecenia": lambda page: expect(
        page.locator(
            'section[data-section="polecenia"] .view-panel.left .panel-head .sub'
        )
    ).to_have_text(re.compile(r"^katalog: \d+ polece")),
}
TC_METHODS = ["kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"]
"""The rows of Kalkulatory's tc comparison, in their order."""


def flat(text: str | None) -> str:
    """Return ``text`` with its runs of (non-breaking) spaces as one space."""
    return SPACES.sub(" ", text or "").strip()


def reopen(tab: Tab, path: str) -> Page:
    """Open ``path`` as a new document: a hash alone would not reload the page."""
    tab.page.goto("about:blank")
    tab.open(path)
    return tab.page


@pytest.mark.parametrize(
    ("width", "height", "theme"),
    [
        (1440, 900, "light"),
        (1440, 900, "dark"),
        (390, 844, "light"),
        (390, 844, "dark"),
    ],
    ids=["desktop-light", "desktop-dark", "phone-light", "phone-dark"],
)
def test_every_section_and_the_guide_open_cleanly(
    new_tab: Callable[..., Tab], width: int, height: int, theme: str
) -> None:
    tab = new_tab(width=width, height=height, theme=theme)
    tab.open()
    registered = tab.page.evaluate(REGISTERED)
    assert sorted(registered) == sorted(READY)

    for section in registered:
        page = reopen(tab, f"#{section}")
        expect(
            page.locator(f'section.section[data-section="{section}"]')
        ).to_be_visible()
        expect(
            page.locator(f'nav.rail .rail-item[data-section="{section}"]')
        ).to_have_attribute("aria-current", "page")
        READY[section](page)
        assert page.evaluate(SIDEWAYS) == [], section

    page = reopen(tab, "instrukcja/")
    expect(page.get_by_role("heading", level=1)).to_be_visible()
    page.locator("img").evaluate_all(
        "images => images.forEach((image) => { image.loading = 'eager'; })"
    )
    page.wait_for_function(
        "() => [...document.images].every((image) => image.complete)"
    )
    broken = page.locator("img").evaluate_all(
        "images => images.filter((image) => image.naturalWidth === 0)"
        ".map((image) => image.getAttribute('src'))"
    )
    assert broken == []
    assert page.evaluate(SIDEWAYS) == []


def tc_row(page: Page, method: str) -> Locator:
    """Return the row of ``method`` in Kalkulatory's tc comparison."""
    rows = page.locator(
        'section[data-section="kalkulatory"] .view-panel.right .dtable tbody tr'
    )
    return rows.nth(TC_METHODS.index(method))


def test_the_guides_examples_are_the_shipped_examples(tab: Tab) -> None:
    page = reopen(tab, "instrukcja/")
    quoted = page.locator("[data-example]").evaluate_all(
        "items => items.map((item) => [item.dataset.example, item.textContent])"
    )
    assert quoted
    shown: dict[str, str] = {}

    def read(key: str, locator: Locator) -> None:
        expect(locator).to_have_text(re.compile(r"\S"))
        shown[key] = flat(locator.text_content())

    # Hydrogram zlewni: the worked example of „Na start” typed, then AMC III
    page = reopen(tab, "#hydrogram")
    left = page.locator('section[data-section="hydrogram"] .view-panel.left')
    right = page.locator('section[data-section="hydrogram"] .view-panel.right')
    typed = {
        "area_km2": "37,22",
        "cn": "65",
        "channel_length_km": "14,78",
        "channel_slope_m_per_m": "0,0142",
        "total_mm": "105",
        "timestep_min": "10",
    }
    for name, value in typed.items():
        left.locator(f"#hg-{name}").fill(value)
    left.locator("#hg-pmaxtp_probability_pct").select_option("1")
    left.locator("#hg-pmaxtp_duration_min").select_option("720")
    page.locator('[aria-labelledby="hg-uh-label"]').get_by_role(
        "radio", name="SCS", exact=True
    ).click()
    expect(right.locator('[data-kpi="q"] .v')).to_contain_text("60,21")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    for name in ["q", "tp", "volume", "c"]:
        read(f"hydrogram-{name}", right.locator(f'[data-kpi="{name}"] .v'))
    # The example's channel is flatter than Kirpich's data: Hydrolog's warning on it
    outside = left.locator('[data-field="channel_slope_m_per_m"] .warn')
    expect(outside).to_contain_text("outside_typical_range")
    shown["hydrogram-outside"] = flat(
        outside.evaluate("node => node.firstChild.textContent")
    )
    page.locator('[aria-labelledby="hg-amc-label"]').get_by_role(
        "radio", name="III", exact=True
    ).click()
    expect(right.locator('[data-kpi="q"] .v')).not_to_contain_text("60,21")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    read("hydrogram-q-amc3", right.locator('[data-kpi="q"] .v'))
    # Every field of the example (Kalkulatory compares the six methods with them)
    left.locator('input[type="file"]').set_input_files(str(FIXTURES / "kamiennik.json"))
    expect(page.locator(".toast")).to_have_text("Wczytano zlewnię z kamiennik.json")

    # Sieć i trasowanie: the example network, then its reach R_A by Muskingum
    page = reopen(tab, "#siec")
    expect(page.locator("svg.schem g.node")).to_have_count(8)
    tiles = page.locator('[data-tiles="network"]')

    def compute() -> None:
        with page.expect_response(
            lambda answer: "/api/run/route/network" in answer.url
        ):
            page.get_by_role("button", name="Oblicz sieć").click()
        expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")

    compute()
    read("siec-q", tiles.locator('[data-tile="peak"] .v'))
    read("siec-tp", tiles.locator('[data-tile="time"] .v'))
    page.locator('svg.schem g.node[data-node="R_A"]').click()
    form = page.locator('[data-node-form="R_A"]')
    form.locator('[data-key="#method"] select').select_option("muskingum")
    form.locator('[data-key="muskingum.k_min"] input').fill("30")
    form.locator('[data-key="muskingum.x"] input').fill("0,2")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "stale")
    compute()
    expect(tiles.locator('[data-tile="peak"] .v')).not_to_have_text(shown["siec-q"])
    read("siec-q-muskingum", tiles.locator('[data-tile="peak"] .v'))
    read("siec-tp-muskingum", tiles.locator('[data-tile="time"] .v'))

    # Statystyka przepływów: the sample of annual maxima
    page = reopen(tab, "#statystyka")
    section = page.locator('section[data-section="statystyka"]')
    READY["statystyka"](page)
    section.locator(".panel-foot .btn.primary").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    tiles = section.locator(".view-panel.right .summary")
    for key, tile in [
        ("statystyka-best", "distribution"),
        ("statystyka-q1", "q-100"),
        ("statystyka-q10", "q-10"),
        ("statystyka-years", "n_years"),
    ]:
        read(key, tiles.locator(f'.kpi[data-key="{tile}"] .v'))

    # Kalkulatory: the six tc methods for Hydrogram's watershed
    page = reopen(tab, "#kalkulatory")
    READY["kalkulatory"](page)
    expect(
        page.locator('section[data-section="kalkulatory"] .kc-watershed').first
    ).to_have_attribute("data-watershed", "Kamiennik — Świerzawa")
    page.locator('section[data-section="kalkulatory"] .panel-foot .btn.primary').click()
    expect(tc_row(page, "kerby_kirpich").locator("td").first).to_have_text(
        re.compile(r"\d")
    )
    for method in TC_METHODS:
        read(f"tc-{method}", tc_row(page, method).locator("td").first)
        read(f"tc-{method}-range", tc_row(page, method).locator(".badge"))

    assert {key for key, _ in quoted} == set(shown)
    assert [(key, flat(text)) for key, text in quoted] == [
        (key, shown[key]) for key, _ in quoted
    ]
