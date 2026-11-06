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

from tests.e2e.conftest import Tab, type_nash

BADGE = ".topbar .badge.status"
SPACES = re.compile(r"[\s\u00a0\u202f]+")
REGISTERED = "async () => (await import('./src/app.js')).ORDERED.map((item) => item.id)"
# The document and an open sheet: neither may scroll sideways.
SIDEWAYS = """() => [document.documentElement,
  ...document.querySelectorAll('.view-panel.open .view-panel-body')]
  .filter((element) => element.scrollWidth > element.clientWidth)
  .map((element) => element.className || element.tagName)"""
RUN = "/api/run/"
# What a first visit of each section shows once it is in place: every section empty.
READY: dict[str, Callable[[Page], None]] = {
    "hydrogram": lambda page: expect(
        page.locator('section[data-section="hydrogram"] .step > summary .title')
    ).to_have_text(["Zlewnia", "Hietogram", "Hydrogram"]),
    "siec": lambda page: expect(
        page.locator('section[data-section="siec"] [data-empty="siec"]')
    ).to_be_attached(),
    "statystyka": lambda page: expect(
        page.locator('section[data-section="statystyka"] [data-empty="statystyka"]')
    ).to_be_attached(),
    "kalkulatory": lambda page: expect(
        page.locator('section[data-section="kalkulatory"] .cmd-list .cmd-item')
    ).to_have_count(16),
    "polecenia": lambda page: expect(
        page.locator('section[data-section="polecenia"] [data-empty="polecenia"]')
    ).to_be_attached(),
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
    runs: list[str] = []
    tab.page.on(
        "request",
        lambda request: runs.append(request.url) if RUN in request.url else None,
    )
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
    assert runs == []  # every section starts empty: nothing to compute

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


def test_the_guides_examples_typed_give_the_guides_numbers(tab: Tab) -> None:
    page = reopen(tab, "instrukcja/")
    quoted = page.locator("[data-example]").evaluate_all(
        "items => items.map((item) => [item.dataset.example, item.textContent])"
    )
    assert quoted
    pasted = page.locator('[data-paste="statystyka-values"]').text_content() or ""
    network = page.locator("#siec a[download]").get_attribute("href")
    assert network
    network_file = page.request.get(tab.base + "instrukcja/" + network).body()
    shown: dict[str, str] = {}

    def read(key: str, locator: Locator) -> None:
        expect(locator).to_have_text(re.compile(r"\S"))
        shown[key] = flat(locator.text_content())

    # Hydrogram zlewni: step 1 of chapter 02 in full, the storm, SCS; then AMC III
    page = reopen(tab, "#hydrogram")
    left = page.locator('section[data-section="hydrogram"] .view-panel.left')
    right = page.locator('section[data-section="hydrogram"] .view-panel.right')
    typed = {
        "name": "Kamiennik — Świerzawa",
        "area_km2": "37,22",
        "cn": "65",
        "perimeter_km": "40,89",
        "length_km": "16,05",
        "elevation_min_m": "257,3",
        "elevation_max_m": "475,1",
        "elevation_mean_m": "363,2",
        "mean_slope_m_per_m": "0,082",
        "channel_length_km": "14,78",
        "channel_slope_m_per_m": "0,0142",
        "flow_path_length_km": "15,88",
        "flow_path_slope_m_per_m": "0,0114",
        "pmaxtp_latitude": "51,01544",
        "pmaxtp_longitude": "15,88984",
        "timestep_min": "10",
    }
    for name, value in typed.items():
        left.locator(f"#hg-{name}").fill(value)
    left.locator("#hg-pmaxtp_probability_pct").select_option("1")
    left.locator("#hg-pmaxtp_duration_min").select_option("720")
    page.locator('[aria-labelledby="hg-uh-label"]').get_by_role(
        "radio", name="SCS", exact=True
    ).click()
    expect(right.locator('[data-kpi="q"] .v')).to_contain_text("54,20")
    shown["hydrogram-depth"] = flat(
        left.locator("#hg-pmaxtp_depth").input_value() + " mm"
    )
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    for name in ["q", "tp", "volume", "c"]:
        read(f"hydrogram-{name}", right.locator(f'[data-kpi="{name}"] .v'))
    # The example's longest flow path is flatter than Kirpich's data: Hydrolog's
    # warning on its slope
    outside = left.locator('[data-field="flow_path_slope_m_per_m"] .warn')
    expect(outside).to_contain_text("outside_typical_range")
    shown["hydrogram-outside"] = flat(
        outside.evaluate("node => node.firstChild.textContent")
    )
    page.locator('[aria-labelledby="hg-amc-label"]').get_by_role(
        "radio", name="III", exact=True
    ).click()
    expect(right.locator('[data-kpi="q"] .v')).not_to_contain_text("54,20")
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    read("hydrogram-q-amc3", right.locator('[data-kpi="q"] .v'))

    # Sieć i trasowanie: the guide's file, then its reach R_A by Muskingum
    page = reopen(tab, "#siec")
    page.locator('section[data-section="siec"] [data-input="network"]').set_input_files(
        {"name": "siec.json", "mimeType": "application/json", "buffer": network_file}
    )
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

    # Statystyka przepływów: the guide's maxima pasted, T = 100 highlighted; no „Oblicz”
    page = reopen(tab, "#statystyka")
    section = page.locator('section[data-section="statystyka"]')
    section.locator(".step").first.get_by_role("radio", name="Wklej").click()
    section.locator("#st-values").fill(pasted)
    section.locator(".st-chosen").get_by_role("button", name="100", exact=True).click()
    expect(section.locator(".panel-foot [data-calc]")).to_have_attribute(
        "data-calc", "ok"
    )
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    tiles = section.locator(".view-panel.right .summary")
    for key, tile in [
        ("statystyka-best", "distribution"),
        ("statystyka-q1", "q-100"),
        ("statystyka-q10", "q-10"),
        ("statystyka-years", "n_years"),
    ]:
        read(key, tiles.locator(f'.kpi[data-key="{tile}"] .v'))

    # Kalkulatory: the six tc methods for Hydrogram's watershed and the overland fields
    page = reopen(tab, "#kalkulatory")
    calculators = page.locator('section[data-section="kalkulatory"]')
    READY["kalkulatory"](page)
    expect(calculators.locator(".kc-watershed").first).to_have_attribute(
        "data-watershed", "Kamiennik — Świerzawa"
    )
    for name, value in {
        "overland_length_km": "0,3",
        "overland_slope_m_per_m": "0,082",
        "runoff_coeff": "0,25",
        "retardance": "0,4",
    }.items():
        calculators.locator(f"#kc-{name}").fill(value)
    calculators.locator(".panel-foot .btn.primary").click()
    expect(tc_row(page, "kerby_kirpich").locator("td").first).to_have_text(
        re.compile(r"\d")
    )
    for method in TC_METHODS:
        read(f"tc-{method}", tc_row(page, method).locator("td").first)
        read(f"tc-{method}-range", tc_row(page, method).locator(".badge"))
    # cn lookup: soil group B, forest
    calculators.locator('.cmd-item[data-calculator="cn lookup"] button').click()
    command = calculators.locator(".cmd-form")
    for name, value in {"hsg": "B", "land_cover": "forest"}.items():
        choice = command.locator(f'[data-option="{name}"]')
        if choice.locator("select").count():
            choice.locator("select").select_option(value)
        else:
            choice.get_by_role("radio", name=value, exact=True).click()
    calculators.locator(".panel-foot .btn.primary").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    read("cn-lookup", calculators.locator('.view-panel.right .kpi[data-key="cn"] .v'))

    # Wszystkie polecenia: uh nash by n and K
    page = reopen(tab, "#polecenia")
    commands = page.locator('section[data-section="polecenia"]')
    commands.locator('.cmd-item[data-command="uh nash"] button').click()
    type_nash(page)
    page.get_by_role("button", name="Uruchom").click()
    expect(page.locator(BADGE)).to_have_attribute("data-state", "ok")
    kpis = commands.locator(".view-panel.right .summary .kpi .v")
    for index, key in enumerate(
        ["uh-nash-n", "uh-nash-k", "uh-nash-lag", "uh-nash-qp"]
    ):
        read(key, kpis.nth(index))

    assert {key for key, _ in quoted} == set(shown)
    assert [(key, flat(text)) for key, text in quoted] == [
        (key, shown[key]) for key, _ in quoted
    ]
