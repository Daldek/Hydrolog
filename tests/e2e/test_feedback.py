"""„Zgłoś uwagę” and the admin panel (Nogat DEV-15.12, DEV-15.13) in Chromium.

The button of the top bar opens a modal dialog with one text field, its counter and the
hint not to write personal data, with the operator's address for an answer on a public
GUI; there is no contact field and no diagnostics. A report goes to the server as its
text and the context the page builds (the view, the station, the view's parameters, the
app version) and nothing about the browser; the dialog closes 2 s after the thanks.
The admin panel (``admin/``, Nogat's kit shell, DEV-15.13) asks for the key and keeps
it in the tab, lists the reports newest first with the count of unread ones, shows each
one's context, marks it read and deletes it after a question; the markup of a report
stays text; „Statystyki” shows the days of ``stats.jsonl`` and „Stan” the checks.
"""

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
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


def test_the_admin_panel_lists_marks_and_deletes_reports_and_shows_stats_and_status(
    new_tab: Callable[..., Tab], gui_server: Served, admin_key: str
) -> None:
    tab = new_tab(prefixed=True)
    page = tab.page
    tab.open("admin")  # under a host's prefix, without the slash: 308 to the panel
    expect(page).to_have_url(re.compile(r"/m/hydrolog/admin/$"))
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
        {"message": "Pierwsze zgłoszenie", "context": {"view": "siec"}},
        {"message": markup, "context": context},
    ):
        response = page.request.post(gui_server.url("api/feedback"), data=body)
        assert response.status == 200, response.text()
    stats = gui_server.data_dir / "hydrolog" / "stats.jsonl"
    yesterday = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
    stats.write_text(
        json.dumps({"date": "2020-01-01", "visitors": 9, "page_views": 9})
        + "\n"
        + json.dumps(
            {
                "date": yesterday,
                "visitors": 3,
                "page_views": 5,
                "stations_opened": 1,
                "analyses_run": 2,
                "downloads": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    expect(page.get_by_role("heading", level=1)).to_have_text(
        "Hydrolog · Administracja"
    )
    expect(page.get_by_role("link", name="Wróć do aplikacji")).to_have_attribute(
        "href", gui_server.prefixed
    )
    page.get_by_label("Klucz administratora").fill("zly-klucz")
    page.get_by_role("button", name="Zaloguj", exact=True).click()
    expect(page.get_by_role("alert")).to_have_text(
        "Nieprawidłowy klucz. Spróbuj ponownie."
    )
    page.get_by_label("Klucz administratora").fill(KEY)
    page.get_by_role("button", name="Zaloguj", exact=True).click()

    nav = page.get_by_role("navigation", name="Sekcje panelu")
    expect(nav.get_by_role("link")).to_have_text(["Zgłoszenia", "Statystyki", "Stan"])
    rows = page.locator(".nogat-admin-report")
    expect(rows).to_have_count(2)
    expect(page.locator(".nogat-admin-count")).to_have_text("Nieprzeczytane: 2 z 2")
    newest = rows.first
    expect(newest.locator(".nogat-admin-message")).to_have_text(markup)
    expect(newest.locator(".nogat-admin-badge")).to_have_text("nowe")
    expect(
        page.locator(".nogat-admin-report b, .nogat-admin-report img")
    ).to_have_count(0)
    expect(rows.nth(1).locator(".nogat-admin-message")).to_have_text(
        "Pierwsze zgłoszenie"
    )

    # The context, folded, as text; the server's version, not the page's
    newest.locator("summary", has_text="Kontekst").click()
    expect(newest.locator("dt")).to_have_text(
        ["Widok", "Stacja", "Wersja aplikacji", "Parametry widoku"]
    )
    expect(newest.locator("dd").nth(2)).to_have_text(version)
    assert json.loads(newest.locator("pre").inner_text()) == context["parameters"]

    newest.get_by_role("button", name="Oznacz jako przeczytane").click()
    expect(page.locator(".nogat-admin-count")).to_have_text("Nieprzeczytane: 1 z 2")
    expect(
        newest.get_by_role("button", name="Oznacz jako nieprzeczytane")
    ).to_be_visible()
    assert reports(page, gui_server)[0]["is_read"] is True

    # The key stays in the tab: a reload lists again
    assert page.evaluate("() => Object.keys(sessionStorage)") == [
        "hydrolog/admin-key/1"
    ]
    page.reload()
    expect(rows).to_have_count(2)

    rows.nth(1).get_by_role("button", name="Usuń").click()
    question = page.get_by_role("dialog")
    expect(question.get_by_role("heading")).to_have_text(
        re.compile(r"^Usunąć zgłoszenie #\d+\?$")
    )
    question.get_by_role("button", name="Usuń").click()
    expect(rows).to_have_count(1)
    assert [item["message"] for item in reports(page, gui_server)] == [markup]

    # „Statystyki”: the days of stats.jsonl of the last 30 days
    nav.get_by_role("link", name="Statystyki").click()
    table = page.locator(".nogat-admin-table")
    expect(table.locator("tbody tr")).to_have_count(1)
    expect(table.locator("tbody tr th")).to_have_text(yesterday)
    expect(table.locator("tfoot td").nth(1)).to_have_text("5")

    # „Stan”: the version and the two checks
    nav.get_by_role("link", name="Stan").click()
    expect(page.locator("nogat-admin-status dd").nth(1)).to_have_text(version)
    checks = page.locator(".nogat-admin-check")
    expect(checks.locator(".nogat-admin-check-name")).to_have_text(
        ["data_dir", "feedback_db"]
    )
    expect(checks.locator(".nogat-admin-badge")).to_have_text(["OK", "OK"])
    expect(checks.nth(1)).to_contain_text("Zgłoszenia: 1, nieprzeczytane: 0.")

    page.get_by_role("button", name="Wyloguj").click()
    expect(page.get_by_label("Klucz administratora")).to_be_visible()
    expect(nav).to_be_hidden()
    assert page.evaluate("() => sessionStorage.length") == 0


def test_the_admin_panel_says_when_the_server_has_no_key(tab: Tab) -> None:
    tab.open("admin/")
    page = tab.page

    page.get_by_label("Klucz administratora").fill("dowolny")
    page.get_by_role("button", name="Zaloguj", exact=True).click()

    expect(page.get_by_role("alert")).to_have_text(
        "Serwer nie ma ustawionego klucza administratora."
    )
    expect(page.get_by_role("navigation", name="Sekcje panelu")).to_be_hidden()
