"""The guide, „Instrukcja” and the welcome dialog (plan S7, D10, D18) in Chromium.

The guide (``instrukcja/``) is a page of its own under the app's top bar: it starts with
the plain-words part „Na start”, its contents lead to every chapter, every section of
the rail has a chapter, its links lead back into the app under a host's prefix too, and
its theme switch is the app's (``nogat-theme``). The welcome dialog, a modal <dialog>,
opens on a visit until „Nie pokazuj ponownie” is ticked, whichever way it is closed;
„Instrukcja” reopens it, and with a modifier key follows its link instead; „Otwórz
instrukcję” opens the guide in a new tab. It fits a phone in the dark theme, where
Escape over an open sheet closes the dialog alone, and stays away from Nogat's shell
(``?nogat=1``).
"""

import json
import re
from collections.abc import Callable
from typing import Any

from playwright.sync_api import Page, expect

from tests.e2e.conftest import Tab

WELCOME_KEY = "hydrolog-gui/welcome/1"
REGISTERED = "async () => (await import('./src/app.js')).ORDERED.map((item) => item.id)"
READY = 'section[data-section="hydrogram"] [data-kpi="q"] .v'
"""Hydrogram zlewni's peak: the app is mounted and has computed."""
# Nogat's --bg and --surface of the dark theme (tokens.css, Nogat 29e7e1c).
DARK_BG = "rgb(13, 17, 23)"
DARK_SURFACE = "rgb(22, 27, 34)"


def stored(page: Page) -> Any:
    """Return the stored choice of the welcome dialog, None when there is none."""
    text = page.evaluate("(key) => localStorage.getItem(key)", WELCOME_KEY)
    return None if text is None else json.loads(text)


def welcome(page: Page) -> Any:
    """Return the welcome dialog."""
    return page.get_by_role("dialog", name="Witaj w Hydrologu")


def is_modal(page: Page) -> bool:
    """Whether the welcome dialog is open as a modal one (the page behind it inert)."""
    return bool(
        page.locator("dialog.welcome").evaluate("(d) => d.open && d.matches(':modal')")
    )


def test_the_guide_starts_in_plain_words_and_has_a_chapter_per_section(
    tab: Tab,
) -> None:
    tab.open()
    registered = tab.page.evaluate(REGISTERED)
    tab.open("instrukcja/")
    page = tab.page
    expect(page).to_have_title("Hydrolog: instrukcja")

    # The plain-words part comes first, and the contents name it first
    parts = page.locator(".guide-text > section.part")
    assert parts.evaluate_all("parts => parts.map((part) => part.id)")[0] == "na-start"
    contents = page.get_by_role("navigation", name="Spis treści")
    expect(contents.locator("a").first).to_have_attribute("href", "#na-start")

    # Every link of the contents leads to a chapter, and every section has one
    targets = contents.locator("a").evaluate_all(
        "links => links.map((link) => link.getAttribute('href').slice(1))"
    )
    missing = page.evaluate(
        "(ids) => ids.filter((id) => !document.getElementById(id))", targets
    )
    assert missing == []
    assert set(registered) <= set(targets)

    contents.get_by_role("link", name=re.compile("Słowniczek")).click()
    expect(page).to_have_url(re.compile(r"instrukcja/#slowniczek$"))
    expect(page.locator("#slowniczek")).to_be_in_viewport()


def test_the_guides_links_and_theme_are_the_apps_under_a_prefix(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(prefixed=True)
    tab.open("instrukcja/")
    page = tab.page
    page.get_by_role("group", name="Motyw").get_by_role(
        "button", name="Ciemny", exact=True
    ).click()
    assert page.evaluate("() => document.documentElement.dataset.theme") == "dark"
    assert page.evaluate("() => localStorage.getItem('nogat-theme')") == "dark"

    page.get_by_role("link", name="Otwórz Hydrogram zlewni").click()
    expect(page).to_have_url(tab.base + "#hydrogram")
    expect(page.locator(READY)).to_contain_text("60,21")
    expect(page.locator("body")).to_have_css("background-color", DARK_BG)
    expect(
        page.get_by_role("group", name="Motyw").get_by_role(
            "button", name="Ciemny", exact=True
        )
    ).to_have_attribute("aria-pressed", "true")

    page.go_back()
    expect(page).to_have_url(tab.base + "instrukcja/")
    page.locator("header.topbar").get_by_role(
        "link", name="Wróć do aplikacji", exact=True
    ).click()
    expect(page).to_have_url(tab.base)
    expect(page.locator('section.section[data-section="hydrogram"]')).to_be_visible()


def test_the_welcome_dialog_opens_until_it_is_hidden(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(welcome=True)
    tab.open()
    page = tab.page
    dialog = welcome(page)
    expect(dialog).to_be_visible()
    assert is_modal(page)
    expect(dialog.get_by_role("button", name="Przejdź do aplikacji")).to_be_focused()
    box = dialog.get_by_role("checkbox", name="Nie pokazuj ponownie")
    expect(box).not_to_be_checked()

    # Escape closes it without the box ticked: it opens again on the next visit
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    assert stored(page) is None
    page.reload()
    expect(dialog).to_be_visible()

    # Ticked and closed by its button: the next visits start without it
    box.check()
    dialog.get_by_role("button", name="Przejdź do aplikacji").click()
    expect(dialog).to_be_hidden()
    assert stored(page) == {"hidden": True}
    page.reload()
    expect(page.locator(READY)).to_contain_text("60,21")
    expect(dialog).to_be_hidden()

    # „Instrukcja” brings it back with the choice shown; unticked and closed beside it
    guide = page.locator("header.topbar").get_by_role(
        "link", name="Instrukcja", exact=True
    )
    expect(guide).to_have_attribute("aria-haspopup", "dialog")
    guide.click()
    expect(dialog).to_be_visible()
    assert is_modal(page)
    expect(box).to_be_checked()
    box.uncheck()
    page.mouse.click(5, 5)
    expect(dialog).to_be_hidden()
    assert stored(page) is None
    expect(page).to_have_url(tab.base)
    page.reload()
    expect(dialog).to_be_visible()


def test_the_welcome_dialog_opens_the_guide_in_a_new_tab_under_a_prefix(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(prefixed=True, welcome=True)
    tab.open()
    page = tab.page
    dialog = welcome(page)
    with page.context.expect_page() as opened:
        dialog.get_by_role("link", name="Otwórz instrukcję").click()
    guide = opened.value
    expect(guide).to_have_url(tab.base + "instrukcja/")
    expect(guide.get_by_role("heading", level=1)).to_be_visible()
    expect(dialog).to_be_hidden()

    # A click with a modifier on „Instrukcja” follows its link instead of the dialog
    with page.context.expect_page() as followed:
        page.locator("header.topbar").get_by_role(
            "link", name="Instrukcja", exact=True
        ).click(modifiers=["ControlOrMeta"])
    expect(followed.value).to_have_url(tab.base + "instrukcja/")
    expect(dialog).to_be_hidden()


def test_the_welcome_dialog_fits_a_phone_in_the_dark(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(width=390, height=844, theme="dark", welcome=True)
    tab.open()
    page = tab.page
    dialog = welcome(page)
    expect(dialog).to_be_visible()
    expect(page.locator("dialog.welcome")).to_have_css("background-color", DARK_SURFACE)
    frame = dialog.bounding_box()
    assert frame is not None
    assert frame["x"] >= 0 and frame["x"] + frame["width"] <= 390
    assert frame["y"] >= 0 and frame["y"] + frame["height"] <= 844
    for name in ["Otwórz instrukcję", "Przejdź do aplikacji"]:
        button = dialog.get_by_role("link", name=name).or_(
            dialog.get_by_role("button", name=name)
        )
        size = button.bounding_box()
        assert size is not None and size["height"] >= 44, name
    dialog.get_by_role("button", name="Zamknij").click()
    expect(dialog).to_be_hidden()

    # Over an open sheet, Escape closes the dialog and leaves the sheet open
    page.get_by_role("button", name="Dane", exact=True).click()
    sheet = page.locator('section[data-section="hydrogram"] .view-panel.left')
    expect(sheet).to_have_css("transform", "none")
    page.locator("header.topbar").get_by_role(
        "link", name="Instrukcja", exact=True
    ).click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(sheet).to_have_class(re.compile(r"\bopen\b"))


def test_nogats_shell_gets_no_welcome_dialog(new_tab: Callable[..., Tab]) -> None:
    tab = new_tab(welcome=True)
    tab.open("?nogat=1")
    page = tab.page
    expect(page.locator(READY)).to_contain_text("60,21")
    assert page.locator("dialog").count() == 0
