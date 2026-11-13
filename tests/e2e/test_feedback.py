"""„Zgłoś uwagę” and the admin page (Nogat DEV-15.12) in Chromium.

The button of the top bar opens a modal dialog with one text field, its counter and the
hint not to write personal data, with the operator's address for an answer on a public
GUI; there is no contact field and no diagnostics. A report goes to the server as its
text and the context the page builds (the view, the station, the view's parameters, the
app version) and nothing about the browser; the dialog closes 2 s after the thanks.
The admin page (``admin/``) asks for the key and keeps it in the tab, lists the reports
newest first with the count of unread ones, opens one (which reads it) with its context,
marks it unread again and deletes it; the markup of a report stays text.
"""

import json
from collections.abc import Callable
from typing import Any

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import Served, Tab, seed_hydrogram

KEY = "klucz-testowy-0123"
READY = 'section[data-section="hydrogram"] [data-kpi="q"] .v'
"""Hydrogram zlewni's peak: the app is mounted and has computed."""
THANKS = "Dziękujemy! Zgłoszenie zostało zapisane."
HINT = "Nie wpisuj danych osobowych."
CONTEXT_KEYS = {"view", "station", "parameters", "app_version"}


@pytest.fixture
def admin_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Give the live server (a thread of this process) its admin key."""
    monkeypatch.setenv("HYDROLOG_ADMIN_API_KEY", KEY)
    return KEY


def reports(page: Page, served: Served) -> list[dict[str, Any]]:
    """Return every report through the admin route, newest first."""
    response = page.request.get(
        served.url("api/admin/feedback?limit=200"), headers={"X-Admin-Key": KEY}
    )
    assert response.status == 200, response.text()
    items: list[dict[str, Any]] = response.json()["items"]
    return items


def remove_all(page: Page, served: Served) -> None:
    """Delete the reports other tests left on the shared server."""
    for item in reports(page, served):
        page.request.delete(
            served.url(f"api/admin/feedback/{item['id']}"),
            headers={"X-Admin-Key": KEY},
        )


def dialog(page: Page) -> Any:
    return page.get_by_role("dialog", name="Zgłoś uwagę")


def open_dialog(page: Page) -> Any:
    page.locator("header.topbar").get_by_role("button", name="Zgłoś uwagę").click()
    found = dialog(page)
    expect(found).to_be_visible()
    return found


def send(page: Page, found: Any) -> dict[str, Any]:
    """Press „Wyślij” and return the body the page posted to ``api/feedback``."""
    with page.expect_request(
        lambda request: (
            request.method == "POST" and request.url.endswith("api/feedback")
        )
    ) as posted:
        found.get_by_role("button", name="Wyślij").click()
    body = posted.value.post_data_json
    assert isinstance(body, dict), body
    return body


def test_a_report_goes_as_its_text_and_the_context_of_the_view(
    tab: Tab, gui_server: Served, admin_key: str
) -> None:
    seed_hydrogram(tab)
    tab.open("#hydrogram")
    page = tab.page
    expect(page.locator(READY)).to_contain_text("57,88")
    version = page.request.get(gui_server.url("api/session")).json()["version"]

    found = open_dialog(page)
    assert found.evaluate("(d) => d.open && d.matches(':modal')")
    message = found.get_by_label("Wiadomość")
    expect(message).to_be_focused()
    # One text field and nothing else to fill: no contact, no diagnostics
    expect(found.get_by_role("textbox")).to_have_count(1)
    expect(found.get_by_role("checkbox")).to_have_count(0)
    expect(found.locator("details, pre, input")).to_have_count(0)
    # No operator on this server: the hint has no address
    expect(message).to_have_accessible_description(HINT)
    expect(found.get_by_text(HINT, exact=True)).to_be_visible()
    expect(
        found.get_by_text(
            "Zgłoszenie zawiera też widok, jego parametry i wersję aplikacji."
        )
    ).to_be_visible()
    expect(found.get_by_text("0/5000")).to_be_visible()
    message.fill("Qmax wygląda na za duży")
    expect(found.get_by_text("23/5000")).to_be_visible()

    body = send(page, found)
    expect(found.get_by_role("status")).to_have_text(THANKS)
    expect(found).to_be_hidden()  # 2 s after the thanks

    assert set(body) == {"message", "context"}
    context = body["context"]
    assert set(context) == CONTEXT_KEYS
    assert context["view"] == "hydrogram"
    assert context["station"] is None
    assert context["parameters"]["tc_method"] == "kirpich"
    assert context["app_version"] == version
    sent = json.dumps(body)
    user_agent = page.evaluate("() => navigator.userAgent")
    assert user_agent not in sent
    assert tab.base not in sent

    stored = next(
        item
        for item in reports(page, gui_server)
        if item["message"] == "Qmax wygląda na za duży"
    )
    assert set(stored) == {"id", "created_at", "message", "context", "is_read"}
    assert stored["context"] == context


def test_an_empty_report_is_not_sent_and_the_view_names_its_route(
    tab: Tab, gui_server: Served, admin_key: str
) -> None:
    tab.open("#polecenia/uh/nash")
    page = tab.page
    before = len(reports(page, gui_server))
    found = open_dialog(page)
    found.get_by_label("Wiadomość").fill("   ")

    found.get_by_role("button", name="Wyślij").click()

    expect(found.get_by_role("status")).to_have_text("Wiadomość nie może być pusta.")
    expect(found.get_by_label("Wiadomość")).to_be_focused()
    assert len(reports(page, gui_server)) == before

    found.get_by_label("Wiadomość").fill("  Brak jednostki  ")
    body = send(page, found)
    expect(found.get_by_role("status")).to_have_text(THANKS)
    expect(found).to_be_hidden()

    assert body["message"] == "Brak jednostki"
    assert body["context"]["view"] == "polecenia/uh/nash"
    newest = reports(page, gui_server)[0]
    assert (newest["message"], newest["context"]["view"]) == (
        "Brak jednostki",
        "polecenia/uh/nash",
    )

    # Escape and „Anuluj” close it; the next opening asks afresh
    open_dialog(page)
    page.keyboard.press("Escape")
    expect(found).to_be_hidden()
    open_dialog(page).get_by_role("button", name="Anuluj").click()
    expect(found).to_be_hidden()


def test_a_public_gui_gives_the_operators_address_for_an_answer(
    new_tab: Callable[..., Tab],
) -> None:
    tab = new_tab(server="public")
    tab.open("#kalkulatory")
    page = tab.page

    message = open_dialog(page).get_by_label("Wiadomość")

    expect(message).to_have_accessible_description(
        "Nie wpisuj danych osobowych. Jeśli chcesz odpowiedzi, napisz na "
        "kontakt@example.org"
    )


def test_the_admin_page_lists_opens_marks_and_deletes_reports(
    new_tab: Callable[..., Tab], gui_server: Served, admin_key: str
) -> None:
    tab = new_tab(prefixed=True)
    page = tab.page
    tab.open("admin/")  # the admin page under a host's prefix
    remove_all(page, gui_server)
    # The server writes its own version into every report's context
    version = page.request.get(gui_server.url("api/session")).json()["version"]
    markup = "<b>Pogrubione?</b> <img src=x> " + "długi opis " * 10
    context = {
        "view": "statystyka",
        "station": "Kłodzko (Nysa Kłodzka)",
        "parameters": {"source": "file", "values": {"return_periods": "2; 10; 100"}},
        "app_version": "9.9.9",
    }
    for body in (
        {
            "message": "Pierwsze zgłoszenie",
            "context": {
                "view": "siec",
                "station": None,
                "parameters": {},
                "app_version": "9.9.9",
            },
        },
        {"message": markup, "context": context},
    ):
        response = page.request.post(gui_server.url("api/feedback"), data=body)
        assert response.status == 200, response.text()

    expect(page.get_by_role("heading", name="Panel administracyjny")).to_be_visible()
    page.get_by_label("Klucz API").fill("zly-klucz")
    page.get_by_role("button", name="Zaloguj").click()
    expect(page.get_by_role("alert")).to_have_text(
        "Nieprawidłowy klucz API. Spróbuj ponownie."
    )
    page.get_by_label("Klucz API").fill(KEY)
    page.get_by_role("button", name="Zaloguj").click()

    expect(page.get_by_role("heading", name="Zgłoszenia użytkowników")).to_be_visible()
    rows = page.locator("li.report")
    expect(rows).to_have_count(2)
    expect(page.locator(".unread-count")).to_have_text("2")
    newest = rows.first
    expect(newest.locator(".report-excerpt")).to_have_text(markup[:80] + "…")
    expect(newest.locator(".badge")).to_have_text("nowe")
    expect(rows.nth(1).locator(".report-excerpt")).to_have_text("Pierwsze zgłoszenie")

    # Opened: its text and context as text, and read
    newest.locator(".report-toggle").click()
    details = newest.locator(".report-details")
    expect(newest.locator(".report-message")).to_have_text(markup)
    expect(page.locator("li.report b, li.report img")).to_have_count(0)
    expect(details.locator(".report-meta")).to_have_text(
        [
            "Widok: statystyka",
            "Stacja: Kłodzko (Nysa Kłodzka)",
            f"Wersja aplikacji: {version}",
        ]
    )
    expect(details.get_by_role("heading", name="Parametry widoku")).to_be_visible()
    assert json.loads(details.locator("pre").inner_text()) == context["parameters"]
    expect(page.locator(".unread-count")).to_have_text("1")
    expect(newest.locator(".badge")).to_have_count(0)
    newest.get_by_role("button", name="Oznacz nieprzeczytane").click()
    expect(page.locator(".unread-count")).to_have_text("2")
    assert reports(page, gui_server)[0]["is_read"] is False

    # A report without a station names none
    rows.nth(1).locator(".report-toggle").click()
    expect(rows.nth(1).locator(".report-meta")).to_have_text(
        ["Widok: siec", f"Wersja aplikacji: {version}"]
    )

    # The key stays in the tab: a reload lists again
    page.reload()
    expect(rows).to_have_count(2)

    page.once("dialog", lambda question: question.accept())
    rows.nth(1).get_by_role("button", name="Usuń").click()
    expect(rows).to_have_count(1)
    assert [item["message"] for item in reports(page, gui_server)] == [markup]

    page.get_by_role("button", name="Wyloguj").click()
    expect(page.get_by_role("heading", name="Panel administracyjny")).to_be_visible()
    assert page.evaluate("() => sessionStorage.length") == 0


def test_the_admin_page_says_when_the_server_has_no_key(tab: Tab) -> None:
    tab.open("admin/")
    page = tab.page

    page.get_by_label("Klucz API").fill("dowolny")
    page.get_by_role("button", name="Zaloguj").click()

    expect(page.get_by_role("alert")).to_contain_text("HYDROLOG_ADMIN_API_KEY")
