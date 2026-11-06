"""The shell of the GUI (plan D4, D9, D10, D17) against the live server.

The page works at ``/`` and under a host's prefix with every request relative
to it; the top bar carries Hydrolog's mark, name and the breadcrumbs, the rail
lists only the registered sections. The theme switch Auto, Jasny, Ciemny sets
``data-theme`` on ``<html>`` and the ``nogat-theme`` key, which
``theme-init.js`` applies before the app (as it does ``?nogat=1``, hiding the
top bar and the rail). In both themes, at 1440, 1180 and 390 px, nothing
scrolls sideways: a 64 px rail and the panels Dane | Wyniki on a desktop, a
58 px bottom bar and bottom sheets on a phone. The panels resize by keys within
their bounds, the widths are kept, and the hash routes survive back and
forward.
"""

import json
import re
from collections.abc import Callable
from typing import Any

import pytest
from playwright.sync_api import Request, Route, expect

from tests.e2e.conftest import Tab, type_nash

# Nogat's tokens of both themes (tokens.css, Nogat d1b5820): --bg and --rail-bg.
BG = {"light": "rgb(250, 248, 248)", "dark": "rgb(13, 17, 23)"}
RAIL_BG = {"light": "rgb(13, 17, 23)", "dark": "rgb(1, 4, 9)"}
SECTION_TITLE = "Wszystkie polecenia"
LAYOUT_KEY = "hydrolog-gui/layout/1"
# The height of the desktop windows [px], a laptop's.
HEIGHT = 640
# The page without its app: theme-init.js alone decides what the first paint shows.
NO_APP = "**/src/main.js"
POL = 'section[data-section="polecenia"]'
"""Polecenia's section: every section's layout has panels of the same classes."""
# The registered sections in the order of the rail (app.js), and a section's title.
REGISTERED = "async () => (await import('./src/app.js')).ORDERED.map((item) => item.id)"
TITLE = "async (id) => (await import('./src/labels/shell.js')).shell.sections[id].title"


def body_bg(page: Any) -> str:
    """Return the computed background of <body>."""
    return str(page.evaluate("() => getComputedStyle(document.body).backgroundColor"))


def theme_attr(page: Any) -> str | None:
    """Return ``data-theme`` of <html>, None when absent."""
    value = page.evaluate("() => document.documentElement.dataset.theme ?? null")
    return None if value is None else str(value)


def stored(page: Any, key: str) -> Any:
    """Return the localStorage value of ``key``."""
    return page.evaluate("(key) => localStorage.getItem(key)", key)


def assert_page_fits(page: Any) -> None:
    """Check that the document scrolls neither sideways nor down: the shell fits."""
    sizes = page.evaluate(
        "() => ({width: [document.documentElement.scrollWidth,"
        " document.body.scrollWidth, window.innerWidth],"
        " height: [document.documentElement.scrollHeight,"
        " document.body.scrollHeight, window.innerHeight]})"
    )
    for axis in ("width", "height"):
        content_a, content_b, viewport = sizes[axis]
        assert max(content_a, content_b) <= viewport, sizes


def box(locator: Any) -> dict[str, float]:
    """Return the bounding box of a shown element."""
    found = locator.bounding_box()
    assert found is not None
    return dict(found)


def hold_app(page: Any) -> None:
    """Serve an empty ``src/main.js``: only theme-init.js runs on the page."""

    def empty(route: Route) -> None:
        route.fulfill(status=200, content_type="text/javascript", body="")

    page.route(NO_APP, empty)


def theme_button(page: Any, name: str) -> Any:
    """Return a button of the theme switch („Motyw”)."""
    return page.get_by_role("group", name="Motyw").get_by_role(
        "button", name=name, exact=True
    )


@pytest.mark.parametrize("prefixed", [False, True], ids=["root", "prefix"])
def test_page_brand_rail_route_and_relative_api(
    new_tab: Callable[..., Tab], prefixed: bool
) -> None:
    tab = new_tab(prefixed=prefixed)
    requests: list[str] = []

    def record(request: Request) -> None:
        if "/api/" in request.url:
            requests.append(request.url)

    tab.page.on("request", record)
    tab.open()
    page = tab.page
    base = tab.base

    topbar = page.locator("header.topbar")
    brand = topbar.get_by_role("link", name="Hydrolog, strona główna")
    expect(brand).to_contain_text("Hydrolog")
    expect(brand.locator("img")).to_have_js_property("complete", True)
    assert brand.locator("img").evaluate("(img) => img.naturalWidth") > 0
    icon = page.locator('link[rel="icon"]')
    expect(icon).to_have_attribute("type", "image/svg+xml")
    icon_url = icon.evaluate("(link) => link.href")
    assert icon_url == base + "nogat/marks/hydrolog.svg"
    answer = page.request.get(icon_url)
    assert answer.status == 200
    assert answer.headers["content-type"].startswith("image/svg+xml")

    # The registered sections in the order of the rail, the first active by default;
    # Polecenia under its Polish names
    registered = page.evaluate(REGISTERED)
    items = page.locator("nav.rail .rail-item")
    expect(items).to_have_count(len(registered))
    shown = items.evaluate_all("items => items.map((item) => item.dataset.section)")
    assert shown == registered
    expect(items.first).to_have_attribute("aria-current", "page")
    first = page.locator(f'section.section[data-section="{registered[0]}"]')
    expect(first).to_be_visible()
    assert page.evaluate("() => location.hash") == ""
    item = page.locator('nav.rail .rail-item[data-section="polecenia"]')
    expect(item).to_have_attribute("title", SECTION_TITLE)
    expect(item).to_have_attribute("href", "#polecenia")
    assert (item.text_content() or "").replace("\u00ad", "").strip() == "Polecenia"
    item.click()
    expect(item).to_have_attribute("aria-current", "page")
    expect(page.locator('section.section[data-section="polecenia"]')).to_be_visible()

    # Breadcrumbs and title follow the section (a first visit chooses no command); the
    # catalog came from the API next to the page
    expect(topbar.locator(".crumb-section")).to_have_text(SECTION_TITLE)
    expect(topbar.locator(".crumb-context")).to_have_text(
        re.compile(r"^\d+ polece(nia|ń) w \d+ grupach$")
    )
    expect(page).to_have_title(
        re.compile(rf"^Hydrolog: {SECTION_TITLE} — \d+ polece(nia|ń)")
    )
    expect(page.locator(f"{POL} .view-panel.left .panel-head .sub")).to_have_text(
        re.compile(r"^katalog: \d+ polece")
    )
    assert any(url.startswith(base + "api/commands") for url in requests), requests
    assert all(url.startswith(base + "api/") for url in requests), requests

    brand.click()
    expect(page).to_have_url(base + f"#{registered[0]}")
    expect(items.first).to_have_attribute("aria-current", "page")
    expect(first).to_be_visible()


def test_theme_switch_stores_and_survives_reload(tab: Tab) -> None:
    tab.open()
    page = tab.page
    auto, light, dark = (theme_button(page, n) for n in ("Auto", "Jasny", "Ciemny"))
    expect(auto).to_have_attribute("aria-pressed", "true")
    assert theme_attr(page) is None
    assert body_bg(page) == BG["light"]

    dark.click()
    expect(dark).to_have_attribute("aria-pressed", "true")
    expect(auto).to_have_attribute("aria-pressed", "false")
    assert theme_attr(page) == "dark"
    assert stored(page, "nogat-theme") == "dark"
    assert body_bg(page) == BG["dark"]
    rail = page.locator("nav.rail")
    expect(rail).to_have_css("background-color", RAIL_BG["dark"])

    # theme-init.js applies the stored theme before (and without) the app
    hold_app(page)
    page.reload()
    assert theme_attr(page) == "dark"
    assert body_bg(page) == BG["dark"]
    assert page.locator("#app").inner_html() == ""
    page.unroute(NO_APP)
    page.reload()
    expect(dark).to_have_attribute("aria-pressed", "true")
    assert body_bg(page) == BG["dark"]

    light.click()
    assert theme_attr(page) == "light"
    assert stored(page, "nogat-theme") == "light"
    assert body_bg(page) == BG["light"]
    expect(rail).to_have_css("background-color", RAIL_BG["light"])

    # Auto removes the attribute and follows the system, also when it changes
    auto.click()
    expect(auto).to_have_attribute("aria-pressed", "true")
    assert theme_attr(page) is None
    assert stored(page, "nogat-theme") == "auto"
    page.emulate_media(color_scheme="dark")
    assert body_bg(page) == BG["dark"]
    page.reload()
    expect(auto).to_have_attribute("aria-pressed", "true")
    assert theme_attr(page) is None
    assert body_bg(page) == BG["dark"]


def test_auto_follows_a_dark_system_until_light_is_chosen(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(theme="dark")
    tab.open()
    page = tab.page
    expect(theme_button(page, "Auto")).to_have_attribute("aria-pressed", "true")
    assert theme_attr(page) is None
    assert body_bg(page) == BG["dark"]
    expect(page.locator("nav.rail")).to_have_css("background-color", RAIL_BG["dark"])

    theme_button(page, "Jasny").click()
    assert theme_attr(page) == "light"
    assert body_bg(page) == BG["light"]
    hold_app(page)
    page.reload()
    assert theme_attr(page) == "light"
    assert body_bg(page) == BG["light"]


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width", [1440, 1180])
def test_desktop_rail_panels_and_page_fits(
    new_tab: Callable[..., Tab], width: int, theme: str
) -> None:
    # A laptop's height: the result's chart ends below the fold of its panel
    tab = new_tab(width=width, height=HEIGHT, theme=theme)
    tab.open("#polecenia/uh/nash")
    page = tab.page
    assert body_bg(page) == BG[theme]

    rail = box(page.locator("nav.rail"))
    topbar = box(page.locator("header.topbar"))
    assert (rail["x"], rail["width"]) == (0, 64)
    assert rail["y"] == topbar["height"]
    assert rail["y"] + rail["height"] == HEIGHT

    # Dane and Wyniki are columns at their default widths (narrower below 1240 px)
    left = page.locator(f"{POL} .view-panel.left")
    right = page.locator(f"{POL} .view-panel.right")
    expect(left.get_by_role("heading", name="Dane")).to_be_visible()
    expect(right.get_by_role("heading", name="Wyniki")).to_be_visible()
    expected = {1440: (300, 400), 1180: (260, 340)}[width]
    assert (box(left)["width"], box(right)["width"]) == expected
    assert box(left)["x"] == 64
    assert box(right)["x"] + box(right)["width"] == width
    expect(page.get_by_role("button", name="Dane", exact=True)).to_be_hidden()
    assert_page_fits(page)

    type_nash(page)  # a form starts empty: the guide's example
    page.get_by_role("button", name="Uruchom").click()
    expect(page.locator(".topbar .status")).to_have_attribute("data-state", "ok")
    expect(right.locator(".kpi").first).to_be_visible()
    expect(page.locator(f"{POL} .chart svg").first).to_be_visible()
    # The run's chart and its live region keep the shell in place
    assert_page_fits(page)
    assert box(page.locator("header.topbar"))["y"] == 0

    # A closed column frees its place and comes back from the bar
    right.get_by_role("button", name="Zamknij panel wyników").click()
    expect(right).to_be_hidden()
    reopen = page.get_by_role("button", name="Wyniki", exact=True)
    expect(reopen).to_have_attribute("aria-expanded", "false")
    reopen.click()
    expect(right).to_be_visible()
    assert box(right)["width"] == expected[1]
    assert_page_fits(page)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_bottom_bar_and_sheets(new_tab: Callable[..., Tab], theme: str) -> None:
    tab = new_tab(width=390, height=844, theme=theme)
    tab.open("#polecenia/uh/nash")
    page = tab.page
    assert body_bg(page) == BG[theme]
    expect(page.locator('section.section[data-section="polecenia"]')).to_be_visible()

    bar = box(page.locator("nav.rail"))
    assert (bar["x"], bar["width"], bar["height"]) == (0, 390, 58)
    assert bar["y"] + bar["height"] == 844
    assert box(page.locator("header.topbar"))["width"] == 390
    expect(page.locator("header.topbar .crumbs")).to_be_hidden()

    left = page.locator(f"{POL} .view-panel.left")
    right = page.locator(f"{POL} .view-panel.right")
    expect(left).to_be_hidden()
    expect(right).to_be_hidden()
    assert page.locator(".resizer").count() == 0
    assert_page_fits(page)

    # Dane opens as a sheet above the bottom bar; Escape closes it
    open_left = page.get_by_role("button", name="Dane", exact=True)
    open_left.click()
    expect(left).to_be_visible()
    expect(open_left).to_have_attribute("aria-expanded", "true")
    expect(left).to_have_css("transform", "none")
    sheet = box(left)
    assert (sheet["x"], sheet["width"]) == (0, 390)
    assert sheet["y"] + sheet["height"] == 844 - 58
    assert_page_fits(page)
    page.keyboard.press("Escape")
    expect(left).to_be_hidden()
    expect(open_left).to_have_attribute("aria-expanded", "false")

    # A run from Dane swaps the sheet for Wyniki; its close button closes it
    open_left.click()
    type_nash(page)  # a form starts empty: the guide's example
    left.get_by_role("button", name="Uruchom").click()
    expect(right).to_be_visible()
    expect(left).to_be_hidden()
    expect(right.locator(".kpi").first).to_be_visible()
    expect(page.locator(".chart svg").first).to_be_attached()
    expect(page.locator(".topbar .status")).to_have_attribute("data-state", "ok")
    assert_page_fits(page)
    assert box(page.locator("header.topbar"))["y"] == 0
    right.get_by_role("button", name="Zamknij panel wyników").click()
    expect(right).to_be_hidden()
    assert_page_fits(page)


def test_nogat_flag_hides_bar_and_rail_before_the_app(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab()
    page = tab.page
    hold_app(page)
    tab.open("?nogat=1#polecenia/uh/nash")
    assert page.evaluate("() => document.documentElement.dataset.host") == "nogat"
    page.unroute(NO_APP)

    page.reload()
    expect(page.locator(f"{POL} .view-panel.left .panel-head .sub")).to_have_text(
        re.compile(r"^katalog: \d+ polece")
    )
    assert page.locator("header.topbar, nav.rail").count() == 0
    main = box(page.locator("main.main"))
    assert (main["x"], main["y"], main["width"], main["height"]) == (0, 0, 1440, 900)
    assert_page_fits(page)

    tab.open("?nogat=0")
    expect(page.locator("header.topbar")).to_be_visible()
    expect(page.locator("nav.rail")).to_be_visible()
    assert page.evaluate("() => document.documentElement.dataset.host ?? null") is None


def test_panels_resize_by_keys_within_bounds_and_keep_widths(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(width=1920, height=1000)
    tab.open("#polecenia/uh/nash")
    page = tab.page
    left = page.locator(f"{POL} .view-panel.left")
    right = page.locator(f"{POL} .view-panel.right")
    left_sep = page.get_by_role("separator", name="Szerokość panelu danych")
    right_sep = page.get_by_role("separator", name="Szerokość panelu wyników")
    expect(left_sep).to_have_attribute("aria-valuenow", "300")
    expect(right_sep).to_have_attribute("aria-valuenow", "400")

    def press(separator: Any, panel: Any, key: str, width: int) -> None:
        separator.press(key)
        expect(separator).to_have_attribute("aria-valuenow", str(width))
        assert box(panel)["width"] == width

    press(left_sep, left, "ArrowRight", 316)
    press(left_sep, left, "Shift+ArrowRight", 380)
    press(left_sep, left, "ArrowLeft", 364)
    press(left_sep, left, "End", 560)
    press(left_sep, left, "ArrowRight", 560)
    press(left_sep, left, "Home", 260)
    press(left_sep, left, "ArrowLeft", 260)
    press(left_sep, left, "Enter", 300)
    # The right panel grows to the left
    press(right_sep, right, "ArrowLeft", 416)
    press(right_sep, right, "End", 720)
    press(right_sep, right, "Shift+ArrowLeft", 720)
    press(right_sep, right, "Home", 340)
    press(right_sep, right, "ArrowRight", 340)
    press(left_sep, left, "End", 560)
    press(right_sep, right, "Shift+ArrowLeft", 404)
    assert json.loads(stored(page, LAYOUT_KEY)) == {"left": 560, "right": 404}

    page.reload()
    expect(left_sep).to_have_attribute("aria-valuenow", "560")
    expect(right_sep).to_have_attribute("aria-valuenow", "404")
    assert (box(left)["width"], box(right)["width"]) == (560, 404)

    # A narrower window keeps the centre at least 480 px wide
    page.set_viewport_size({"width": 1440, "height": 900})
    expect(left_sep).to_have_attribute("aria-valuenow", "492")
    centre = box(page.locator(f"{POL} .view-center"))
    assert centre["width"] >= 480
    assert box(left)["width"] == 492
    assert_page_fits(page)


def test_hash_routes_back_forward_and_unknown_section(tab: Tab) -> None:
    tab.open("#polecenia/uh/nash")
    page = tab.page
    crumb = page.locator(".crumb-context")
    expect(crumb).to_have_text(re.compile(r"^uh nash · "))

    page.evaluate("() => { location.hash = '#polecenia/scs/effective'; }")
    expect(crumb).to_have_text(re.compile(r"^scs effective · "))
    expect(page).to_have_title(re.compile(r"— scs effective · "))
    page.go_back()
    expect(page).to_have_url(re.compile(r"#polecenia/uh/nash$"))
    expect(crumb).to_have_text(re.compile(r"^uh nash · "))
    page.go_forward()
    expect(page).to_have_url(re.compile(r"#polecenia/scs/effective$"))
    expect(crumb).to_have_text(re.compile(r"^scs effective · "))

    # An unknown section shows the first registered one, without a route of its own
    registered = page.evaluate(REGISTERED)
    title = page.evaluate(TITLE, registered[0])
    first = page.locator(f'section.section[data-section="{registered[0]}"]')
    page.evaluate("() => { location.hash = '#nieznana/sekcja'; }")
    expect(page.locator(".crumb-section")).to_have_text(title)
    expect(first).to_be_visible()
    expect(
        page.locator(f'.rail-item[data-section="{registered[0]}"]')
    ).to_have_attribute("aria-current", "page")
    page.go_back()
    expect(page).to_have_url(re.compile(r"#polecenia/scs/effective$"))
    expect(page.locator('section.section[data-section="polecenia"]')).to_be_visible()
    expect(crumb).to_have_text(re.compile(r"^scs effective · "))

    tab.open("#nieznana")
    expect(page.locator(".crumb-section")).to_have_text(title)
    expect(first).to_be_visible()
