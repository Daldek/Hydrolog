"""„Kalkulatory” (plan S5, D11, D13, D14) in Chromium.

Against the real server of ``gui_server``, with the Kamiennik watershed in the store
(``useStore("watershed")``, which Hydrogram zlewni sets): the comparison runs ``tc
watershed`` once per method and lists the six methods with their range words, coloured
by Hydrolog's notices, with the shell loop of the calls; „Użyj w Hydrogramie zlewni”
routes the chosen method to Hydrogram. The list holds sixteen calculators; a calculator
is the catalog's form filled from the watershed, and its call and result are the CLI's.
"""

import contextlib
import io
import json
import re
import shlex

from playwright.sync_api import Page, Response, expect

from hydrolog.catalog import format_command, run_command
from hydrolog.cli.main import main
from tests.e2e.conftest import Tab, seed_hydrogram

SECTION = 'section[data-section="kalkulatory"]'
RIGHT = f"{SECTION} .view-panel.right"
KAMIENNIK = {
    "name": "Kamiennik — Świerzawa",
    "area_km2": 37.22,
    "perimeter_km": 40.89,
    "length_km": 16.05,
    "elevation_min_m": 257.3,
    "elevation_max_m": 475.1,
    "elevation_mean_m": 363.2,
    "mean_slope_m_per_m": 0.082,
    "channel_length_km": 14.78,
    "channel_slope_m_per_m": 0.0142,
    "cn": 65,
    "runoff_coeff": 0.25,
    "retardance": 0.4,
    "overland_length_km": 0.3,
    "overland_slope_m_per_m": 0.082,
    "Lc_km": 6.76,
    "manning_n": 0.035,
    "urban_pct": 1.0,
    "forest_pct": 57.4,
}
"""The watershed of Hydrogram zlewni's example (web/examples/kamiennik.json)."""
METHODS = ["kirpich", "nrcs", "giandotti", "faa", "kerby", "kerby_kirpich"]
WORDS = {
    "kirpich": "poza zakresem",
    "nrcs": "poza zakresem",
    "giandotti": "poza zakresem",
    "faa": "nie dla zlewni",
    "kerby": "nie dla zlewni",
    "kerby_kirpich": "w zakresie",
}
"""The range words for Kamiennik: Hydrolog's notices and the overland flow."""


def open_section(tab: Tab, path: str = "") -> Page:
    """Open the section (at ``path``) with the Kamiennik watershed in the store.

    Hydrogram zlewni, mounted with the shell, holds the guide's worked example (stored
    with ``seed_hydrogram``, SCS chosen, as „Użyj w Hydrogramie zlewni” needs) and
    writes its watershed into the store; the store is set here only after its first
    result is shown, so that write cannot follow and change the data of a comparison.
    """
    seed_hydrogram(tab)
    tab.open(f"#kalkulatory{path}")
    page = tab.page
    expect(page.locator(f"{SECTION} .cmd-list .cmd-item")).to_have_count(16)
    expect(
        page.locator('section[data-section="hydrogram"] [data-kpi="q"] .v')
    ).to_have_text(re.compile(r"^60,21\s*m³/s$"))
    page.evaluate(
        "async (ws) => (await import('./src/store.js')).setStore('watershed', ws)",
        KAMIENNIK,
    )
    expect(page.locator(f"{SECTION} .kc-watershed").first).to_have_attribute(
        "data-watershed", str(KAMIENNIK["name"])
    )
    return page


def compute(page: Page) -> None:
    """Press „Oblicz” of the panel Dane."""
    page.locator(f"{SECTION} .panel-foot .btn.primary").click()


def test_the_tc_comparison_lists_six_methods_with_their_range_words(tab: Tab) -> None:
    page = open_section(tab)
    expect(page.locator(".crumb-context")).to_have_text(
        f"Porównanie metod tc · {KAMIENNIK['name']}"
    )
    with page.expect_response(
        lambda response: "channel=kalkulatory-tc-giandotti" in response.url
    ) as answer:
        compute(page)
    assert answer.value.request.post_data_json == {
        "watershed": KAMIENNIK,
        "method": "giandotti",
    }

    rows = page.locator(f"{RIGHT} .dtable tbody tr")
    expect(rows).to_have_count(6)
    for index, method in enumerate(METHODS):
        expected = run_command(
            "tc watershed", {"watershed": KAMIENNIK, "method": method}
        ).to_dict()
        row = rows.nth(index)
        expect(row.locator(".row-sub").first).to_have_text(method)
        expect(row.locator(".badge")).to_have_text(WORDS[method])
        tc = f"{expected['result']['tc_min']:.1f}".replace(".", ",")
        expect(row.locator("td").first).to_have_text(tc)
        expect(row.locator("td").last).to_have_text(str(len(expected["notices"])))
    expect(rows.first.locator(".kc-range")).to_have_text(
        "A = 37,22 poza 0,005–0,45 km²; S = 0,0142 poza 0,03–0,1"
    )
    expect(rows.nth(2).locator(".kc-range")).to_have_text(
        "A = 37,22 poza 170–70\u00a0000 km²"
    )
    expect(rows.nth(3).locator(".kc-range")).to_have_text(
        "tylko spływ powierzchniowy, L 0,3 km"
    )

    # The bars: the watershed's methods by tc, then those of the overland flow; the
    # method Hydrogram zlewni computes with (Kirpich on its first visit) is marked
    bars = page.locator(f"{SECTION} .view-center .chart rect.hbar")
    expect(bars).to_have_count(6)
    names = page.locator(f"{SECTION} .view-center .chart .bar-sub").all_text_contents()
    assert names == ["kirpich", "kerby_kirpich", "giandotti", "nrcs", "faa", "kerby"]
    classes = bars.evaluate_all(
        "rects => rects.map((rect) => rect.getAttribute('class'))"
    )
    assert classes == [
        "hbar warn used",
        "hbar ok",
        "hbar warn",
        "hbar warn",
        "hbar bad",
        "hbar bad",
    ]

    # Hydrolog's notices in Polish, once each; the loop of the calls
    notices = page.locator(f'{RIGHT} .notes li[data-code="outside_typical_range"]')
    expect(notices).to_have_count(6)
    expect(notices.first).to_contain_text(
        "kirpich: area_km2 = 37,22 poza typowym zakresem od 0,005 do 0,45."
    )
    loop = page.locator(f"{RIGHT} .kc-loop pre")
    expect(loop).to_have_text(
        re.compile(
            r"^for m in kirpich nrcs giandotti faa kerby kerby_kirpich; do\n"
            r"  hydrolog tc watershed"
        )
    )
    expect(loop).to_contain_text('--method "$m"')

    # The chosen method goes to Hydrogram zlewni, which computes with it (the mockup's
    # run); back in Kalkulatory it is the one marked
    rows.nth(1).get_by_role("button", name="NRCS (TR-55)", exact=True).click()
    expect(rows.nth(1)).to_have_class(re.compile(r"\bsel\b"))
    page.get_by_role("button", name="Użyj w Hydrogramie zlewni").click()
    page.wait_for_function("location.hash.startsWith('#hydrogram')")
    hydrogram = 'section[data-section="hydrogram"]'
    expect(page.locator(f"{hydrogram} #hg-tc_method")).to_have_value("nrcs")
    expect(
        page.locator(f'{hydrogram} .view-panel.right [data-kpi="q"] .v')
    ).to_have_text(re.compile(r"^43,01\s*m³/s$"))
    page.go_back()
    expect(bars.nth(3)).to_have_attribute("class", "hbar warn used")
    expect(bars.first).to_have_attribute("class", "hbar warn")


def test_a_method_left_out_and_an_overland_field_changed_make_the_result_stale(
    tab: Tab,
) -> None:
    page = open_section(tab)
    compute(page)
    expect(page.locator(".topbar .badge.status")).to_have_attribute("data-state", "ok")
    page.locator(f"{SECTION} .kc-compare").get_by_label("Kerby", exact=True).uncheck()
    expect(page.locator(".topbar .badge.status")).to_have_attribute(
        "data-state", "stale"
    )
    page.locator(f"{SECTION} #kc-retardance").fill("0")
    expect(page.locator(f'{SECTION} [data-option="retardance"] .err')).to_contain_text(
        "exclusive_minimum"
    )
    expect(page.locator(f"{SECTION} .panel-foot .btn.primary")).to_be_disabled()
    page.locator(f"{SECTION} #kc-retardance").fill("0,6")
    with page.expect_response(
        lambda response: "channel=kalkulatory-tc-kerby_kirpich" in response.url
    ) as answer:
        compute(page)
    body = answer.value.request.post_data_json
    assert isinstance(body, dict)
    assert body["watershed"]["retardance"] == 0.6
    expect(page.locator(f"{RIGHT} .dtable tbody tr")).to_have_count(5)


def test_the_list_filters_and_routes_the_calculators(tab: Tab) -> None:
    page = open_section(tab)
    items = page.locator(f"{SECTION} .cmd-list .cmd-item")
    page.locator(f"{SECTION} .cmd-tools select").select_option("uh")
    expect(items).to_have_count(4)
    page.locator(f"{SECTION} .cmd-tools select").select_option("")
    page.locator(f"{SECTION} .cmd-tools").get_by_role("searchbox").fill("LUTZ")
    expect(items).to_have_count(1)
    expect(items).to_have_attribute("data-calculator", "uh nash")
    items.first.get_by_role("button").click()
    assert page.evaluate("location.hash") == "#kalkulatory/uh/nash"
    form = page.locator(f"{SECTION} .cmd-form")
    expect(form.locator(".cmd-head code")).to_have_text("uh nash")
    # Lutz from the watershed: the pane of Lutz, filled with its fields
    expect(form.locator('.one-of [role="radio"][aria-checked="true"]')).to_have_text(
        "Lutz"
    )
    expect(form.locator('[data-option="lutz_centroid_length_km"] input')).to_have_value(
        "6,76"
    )


def test_a_calculators_call_and_result_are_the_clis(tab: Tab) -> None:
    page = open_section(tab, "/tc/giandotti")
    form = page.locator(f"{SECTION} .cmd-form")
    # What tc watershed derives from the watershed: the area, the channel, the relief
    expect(form.locator('[data-option="area_km2"] input')).to_have_value("37,22")
    expect(form.locator('[data-option="length_km"] input')).to_have_value("14,78")
    expect(form.locator('[data-option="elevation_diff_m"] input')).to_have_value(
        "105,9"
    )
    with page.expect_response(
        lambda response: "/api/run/tc/giandotti" in response.url
    ) as answer:
        compute(page)
    response: Response = answer.value
    options = response.request.post_data_json
    assert isinstance(options, dict)
    assert options == {"area_km2": 37.22, "length_km": 14.78, "elevation_diff_m": 105.9}
    shown = page.locator(f"{RIGHT} .cli pre")
    expect(shown).to_have_text(re.compile(r"^hydrolog tc giandotti"))
    line = (shown.text_content() or "").replace(" \\\n  ", " ")
    assert line == format_command("tc giandotti", options)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main([*shlex.split(line)[1:], "--json"])
    assert code == 0
    cli = json.loads(out.getvalue())
    assert cli["result"] == response.json()["result"]
    expect(page.locator(f'{RIGHT} .kpi[data-key="tc_min"] .v')).to_have_text(
        "339,4 min"
    )
    expect(page.locator(".topbar .badge.status")).to_have_attribute("data-state", "ok")
