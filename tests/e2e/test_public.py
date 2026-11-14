"""A public GUI (Nogat DEV-15.7 to DEV-15.9) in Chromium.

A server whose ``nogat.toml`` names the operator (``[nogat.operator]``) is public: the
regulamin is linked, in a new tab (the page's session lives in its memory only), at the
bottom of the rail of the sections, in the welcome dialog, at the end of the app menu
„Aplikacje” and at the end of the guide's contents; there is no footer. A server that is
not public has no such link and no ``regulamin.html``, and Nogat's shell (``?nogat=1``)
has its own chrome. Over the request limit a page answers 429 with ``Retry-After`` and
says when to try again.
"""

import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from tests.e2e.conftest import Served, Tab
from tests.e2e.test_shell import assert_page_fits, box

SECTIONS = ["hydrogram", "siec", "statystyka", "kalkulatory", "polecenia"]
RAIL_TERMS = "nav.rail a.rail-terms"
# The statement of the footer that is gone: the regulamin's § 3 alone holds it
STATEMENT = "Serwis jest niekomercyjny i bezpłatny"
WELCOME = "Witaj w Hydrologu"
# The blocks Hydrolog keeps (imgw, pmaxtp, chmi)
BLOCKS = [
    "IMGW-PIB: dane publiczne",
    "IMGW-PIB: opady maksymalne PMAXTP",
    "ČHMÚ",
]


def open_app(tab: Tab, path: str = "") -> None:
    """Open the app and wait for its session, which says whether it is public."""
    with tab.page.expect_response(lambda answer: answer.url.endswith("/api/session")):
        tab.open(path)


def check_regulamin(page: Page) -> None:
    """Check the filled regulamin of the public test server."""
    expect(page).to_have_url(re.compile(r"/regulamin\.html$"))
    expect(page.get_by_role("heading", level=1)).to_have_text(
        "Regulamin serwisu Hydrolog"
    )
    expect(page.get_by_role("heading", level=3)).to_have_text(BLOCKS)
    expect(page.locator("body")).to_contain_text("kontakt@example.org")


def test_the_rail_ends_with_the_regulamin_in_a_new_tab(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    open_app(tab, "#hydrogram")
    rail = page.locator("nav.rail")
    link = page.locator(RAIL_TERMS)

    for section in SECTIONS:
        rail.locator(f'a[href="#{section}"]').click()
        shown = page.locator(f'section[data-section="{section}"]')
        expect(shown).to_be_visible()
        expect(shown.locator(".section-note")).to_have_count(0)  # loaded
        expect(link).to_have_text("Regulamin")
        expect(link).to_have_attribute("href", "regulamin.html")
        expect(link).to_have_attribute("target", "_blank")
        # The rail's last child, at its bottom, below the last section's item; no footer
        # and no statement
        assert link.evaluate("(a) => a.parentElement.lastElementChild === a")
        side, last, terms = box(rail), box(rail.locator("a.rail-item").last), box(link)
        assert terms["y"] > last["y"] + last["height"]
        assert side["y"] + side["height"] - (terms["y"] + terms["height"]) <= 16
        assert side["y"] + side["height"] == 900
        expect(page.get_by_text(STATEMENT)).to_have_count(0)
        assert_page_fits(page)

    with page.context.expect_page() as opened:
        link.click()
    check_regulamin(opened.value)
    expect(page).to_have_url(tab.base + "#polecenia")  # the app stays in its tab


def test_the_welcome_links_the_regulamin_in_a_new_tab(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public", welcome=True)
    page = tab.page
    open_app(tab)
    welcome = page.get_by_role("dialog", name=WELCOME)
    # A first visit shows no provider data: the link stands alone, once
    link = welcome.get_by_role("link", name=re.compile("^Regulamin"))
    expect(link).to_have_count(1)
    expect(link).to_have_attribute("href", "regulamin.html")
    expect(link).to_have_attribute("target", "_blank")

    with page.context.expect_page() as opened:
        link.click()
    check_regulamin(opened.value)
    expect(page).to_have_url(tab.base)


def test_the_app_menu_ends_with_the_regulamin(new_tab: Callable[..., Tab]) -> None:
    tab = new_tab(server="public")
    page = tab.page
    open_app(tab)
    menu = page.locator("header.topbar nogat-app-menu")

    menu.get_by_role("button", name="Aplikacje").click()
    terms = menu.get_by_role("link", name="Regulamin", exact=True)
    expect(terms).to_be_visible()
    assert terms.evaluate("(link) => link.parentElement.lastElementChild === link")

    with page.context.expect_page() as opened:
        terms.click()
    check_regulamin(opened.value)
    expect(page).to_have_url(tab.base)


def test_a_phones_bottom_bar_leaves_the_regulamin_out(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public", width=390, height=844)
    page = tab.page
    open_app(tab, "#statystyka")
    section = page.locator('section[data-section="statystyka"]')
    expect(section.locator(".view-layout")).to_be_visible()

    rail = box(page.locator("nav.rail"))
    assert (rail["height"], rail["y"] + rail["height"]) == (58, 844)
    expect(page.locator(RAIL_TERMS)).to_be_hidden()
    expect(page.get_by_text(STATEMENT)).to_have_count(0)
    assert_page_fits(page)
    expect(
        page.locator("nav.rail").get_by_role("link", name=re.compile("Kalku"))
    ).to_be_visible()


def test_the_guides_contents_end_with_the_regulamin(
    new_tab: Callable[..., Tab], public_server: Served
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    tab.open("instrukcja/")

    link = page.locator("nav.guide-toc").get_by_role(
        "link", name="Regulamin", exact=True
    )
    expect(link).to_have_attribute("href", public_server.url("regulamin.html"))
    expect(link).to_have_attribute("target", "_blank")
    expect(page.get_by_text(STATEMENT)).to_have_count(0)
    with page.context.expect_page() as opened:
        link.click()
    check_regulamin(opened.value)


def test_a_gui_that_is_not_public_links_no_regulamin(
    new_tab: Callable[..., Tab], gui_server: Served
) -> None:
    tab = new_tab(welcome=True)
    page = tab.page
    open_app(tab, "#hydrogram")

    expect(page.get_by_role("dialog", name=WELCOME)).to_be_visible()
    expect(page.locator("section[data-section='hydrogram']")).to_be_attached()
    expect(page.get_by_role("link", name=re.compile("^Regulamin"))).to_have_count(0)
    expect(page.locator(".nogat-app-menu-terms")).to_have_count(0)
    assert page.request.get(gui_server.url("regulamin.html")).status == 404

    with page.expect_response(lambda answer: answer.url.endswith("/api/terms")) as got:
        tab.open("instrukcja/")
    assert got.value.json()["terms"] is None
    expect(page.get_by_role("heading", level=1)).to_be_visible()
    expect(page.get_by_role("link", name="Regulamin", exact=True)).to_have_count(0)


def test_nogats_shell_draws_its_own_chrome_without_the_regulamin(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    open_app(tab, "?nogat=1#kalkulatory")

    expect(page.locator('section[data-section="kalkulatory"]')).to_be_visible()
    expect(page.get_by_role("link", name=re.compile("^Regulamin"))).to_have_count(0)


def test_over_the_limit_a_page_says_when_to_try_again(
    new_tab: Callable[..., Tab], limited_server: Served
) -> None:
    page = new_tab(server="limited").page
    address = limited_server.url("regulamin.html")
    for _ in range(3):
        answer = page.goto(address)
        assert answer is not None and answer.status == 200

    answer = page.goto(address)

    assert answer is not None and answer.status == 429
    assert int(answer.headers["retry-after"]) > 0
    expect(page.locator("body")).to_contain_text(
        re.compile(r"Zbyt wiele żądań\. Spróbuj ponownie za \d+ s\.")
    )
