"""A public GUI (Nogat DEV-15.7 to DEV-15.9) in Chromium.

A server whose ``nogat.toml`` names the operator (``[nogat.operator]``) is public: every
section of the standalone shell shows the footer with the statement of DEV-15.8 and the
link „Regulamin”, which opens the filled regulamin in a new tab (the page's session
lives in its memory only); the app menu ends with „Regulamin”, and the guide shows the
same footer, its link in a new tab too. On a desktop the footer is one thin row under
the main area (its text on one line, or two in a font too wide for one), on a phone it
sits above the bottom rail; neither covers the rest. A server that is not public has
neither footer nor ``regulamin.html``, and Nogat's shell
(``?nogat=1``) has its own chrome. Over the request limit a page answers 429 with
``Retry-After`` and says when to try again.
"""

import re
from collections.abc import Callable

from playwright.sync_api import Page, expect

from tests.e2e.conftest import Served, Tab
from tests.e2e.test_shell import assert_page_fits, box

STATEMENT = (
    "Serwis jest niekomercyjny i bezpłatny, nie zawiera reklam i nie służy "
    "działalności gospodarczej operatora. Służy celom badawczym i edukacyjnym. "
    "Dane IMGW-PIB są w nim wykorzystywane do celów niezarobkowych, zgodnie z "
    "regulaminami IMGW-PIB."
)
FOOTER = "footer.app-footer"
SECTIONS = ["hydrogram", "siec", "statystyka", "kalkulatory", "polecenia"]
# The blocks Hydrolog keeps (imgw, pmaxtp, chmi)
BLOCKS = [
    "IMGW-PIB: dane publiczne",
    "IMGW-PIB: opady maksymalne PMAXTP",
    "ČHMÚ",
]
FOOTER_TEXT = """(footer) => {
  const text = footer.querySelector('p');
  const unwrapped = text.cloneNode(true);
  unwrapped.style.cssText = 'position: fixed; visibility: hidden; white-space: nowrap';
  footer.append(unwrapped);
  const width = unwrapped.getBoundingClientRect().width;
  unwrapped.remove();
  const height = text.getBoundingClientRect().height;
  return {
    lines: Math.round(height / parseFloat(getComputedStyle(text).lineHeight)),
    needed: Math.ceil(width / text.clientWidth),
    around: footer.getBoundingClientRect().height - height,
  };
}"""
"""The footer's lines of text, the lines its unwrapped width needs in the row, and the
height of the footer around the text (its padding and border)."""


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


def test_every_section_shows_the_statement_and_the_regulamin_in_a_new_tab(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    open_app(tab, "#hydrogram")
    footer = page.locator(FOOTER)
    rail = page.locator("nav.rail")

    for section in SECTIONS:
        rail.locator(f'a[href="#{section}"]').click()
        expect(page.locator(f'section[data-section="{section}"]')).to_be_visible()
        expect(footer).to_be_visible()
        expect(footer).to_contain_text(STATEMENT)
        link = footer.get_by_role("link", name="Regulamin", exact=True)
        expect(link).to_have_attribute("href", "regulamin.html")
        expect(link).to_have_attribute("target", "_blank")
        # One thin row under the main area, beside the rail, at the bottom of the shell
        main, bar, side = box(page.locator("main.main")), box(footer), box(rail)
        assert bar["y"] == main["y"] + main["height"]
        assert (bar["x"], bar["y"] + bar["height"]) == (64, 900)
        # Small text in as few lines as the font's width allows: one with Lato, two
        # with a wider font (macOS's system font) where the statement cannot fit in one
        text = footer.evaluate(FOOTER_TEXT)
        assert text["lines"] == text["needed"] <= 2, text
        assert text["around"] < 10, text
        assert side["y"] + side["height"] == 900
        assert_page_fits(page)

    with page.context.expect_page() as opened:
        footer.get_by_role("link", name="Regulamin", exact=True).click()
    check_regulamin(opened.value)
    expect(page).to_have_url(tab.base + "#polecenia")  # the app stays in its tab


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


def test_a_phone_shows_the_footer_above_the_rail(new_tab: Callable[..., Tab]) -> None:
    tab = new_tab(server="public", width=390, height=844)
    page = tab.page
    open_app(tab, "#statystyka")
    footer = page.locator(FOOTER)
    expect(footer).to_contain_text(STATEMENT)

    bar, rail = box(footer), box(page.locator("nav.rail"))
    main = box(page.locator("main.main"))
    assert (rail["height"], rail["y"] + rail["height"]) == (58, 844)
    assert bar["y"] + bar["height"] == rail["y"]  # above the rail, not over it
    assert bar["y"] == main["y"] + main["height"]
    assert (bar["x"], bar["width"]) == (0, 390)
    assert_page_fits(page)
    expect(
        page.locator("nav.rail").get_by_role("link", name=re.compile("Kalku"))
    ).to_be_visible()


def test_the_guide_shows_the_footer_of_a_public_gui(
    new_tab: Callable[..., Tab], public_server: Served
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    tab.open("instrukcja/")

    footer = page.locator(FOOTER)
    expect(footer).to_contain_text(STATEMENT)
    link = footer.get_by_role("link", name="Regulamin", exact=True)
    expect(link).to_have_attribute("href", public_server.url("regulamin.html"))
    with page.context.expect_page() as opened:
        link.click()
    check_regulamin(opened.value)


def test_a_gui_that_is_not_public_has_no_footer_and_no_regulamin(
    tab: Tab, gui_server: Served
) -> None:
    page = tab.page
    open_app(tab, "#hydrogram")

    expect(page.locator("section[data-section='hydrogram']")).to_be_visible()
    expect(page.locator(FOOTER)).to_have_count(0)
    expect(page.locator(".nogat-app-menu-terms")).to_have_count(0)
    rail = box(page.locator("nav.rail"))
    assert rail["y"] + rail["height"] == 900
    assert page.request.get(gui_server.url("regulamin.html")).status == 404

    with page.expect_response(lambda answer: answer.url.endswith("/api/terms")) as got:
        tab.open("instrukcja/")
    assert got.value.json()["terms"] is None
    expect(page.get_by_role("heading", level=1)).to_be_visible()
    expect(page.locator(FOOTER)).to_have_count(0)


def test_nogats_shell_draws_its_own_chrome_without_the_footer(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public")
    page = tab.page
    open_app(tab, "?nogat=1#kalkulatory")

    expect(page.locator('section[data-section="kalkulatory"]')).to_be_visible()
    expect(page.locator(FOOTER)).to_have_count(0)


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
