"""„Zgłoś uwagę” and the admin page (Nogat plan 2026-11-03, D1, D3, D4) in Chromium.

The button of the top bar opens a modal dialog with Hydrograf's fields; a report goes
to the server with the very diagnostics its preview shows (the page's events, the
section with its inputs, the environment), and the dialog closes 2 s after the thanks.
The admin page (``admin/``) asks for the key and keeps it in the tab, lists the reports
newest first with the count of unread ones, opens one (which reads it), marks it unread
again and deletes it; the markup of a report stays text. ``diagnostics.js`` keeps a
snapshot within the server's 100 000 bytes and leaves long texts and lists out.
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


def test_a_report_goes_with_the_diagnostics_its_preview_shows(
    tab: Tab, gui_server: Served, admin_key: str
) -> None:
    seed_hydrogram(tab)
    tab.open("#hydrogram")
    page = tab.page
    expect(page.locator(READY)).to_contain_text("60,21")

    found = open_dialog(page)
    assert found.evaluate("(d) => d.open && d.matches(':modal')")
    message = found.get_by_label("Opis problemu lub sugestii")
    expect(message).to_be_focused()
    expect(found.get_by_text("0/5000")).to_be_visible()
    message.fill("Qmax wygląda na za duży")
    expect(found.get_by_text("23/5000")).to_be_visible()
    found.get_by_label("Imię lub e-mail").fill("jan@example.com")
    expect(
        found.get_by_role("checkbox", name="Dołącz dane diagnostyczne")
    ).to_be_checked()
    found.get_by_text("Pokaż co zostanie wysłane").click()
    preview = json.loads(found.locator("pre").inner_text())

    assert set(preview) == {"events", "workspace", "env"}
    assert preview["workspace"]["section"] == "hydrogram"
    assert preview["workspace"]["inputs"]["tc_method"] == "kirpich"
    assert preview["workspace"]["status"]["state"] == "ok"
    runs = [
        event["data"]
        for event in preview["events"]
        if event["type"] == "api_call"
        and event["data"]["endpoint"].startswith("api/run/hydrograph/generate")
    ]
    assert runs and runs[-1]["status"] == 200
    assert isinstance(runs[-1]["duration_ms"], int)
    assert preview["env"]["viewport"] == {"width": 1440, "height": 900}

    found.get_by_role("button", name="Wyślij").click()
    expect(found.get_by_role("status")).to_have_text(THANKS)
    expect(found).to_be_hidden()  # 2 s after the thanks

    stored = next(
        item
        for item in reports(page, gui_server)
        if item["message"] == "Qmax wygląda na za duży"
    )
    assert stored["contact"] == "jan@example.com"
    assert stored["page_url"] == tab.base + "#hydrogram"
    assert "Chrome" in stored["user_agent"]
    assert stored["diagnostics"] == preview


def test_an_empty_report_is_not_sent_and_unticked_diagnostics_stay_home(
    tab: Tab, gui_server: Served, admin_key: str
) -> None:
    tab.open("#statystyka")
    page = tab.page
    before = len(reports(page, gui_server))
    found = open_dialog(page)
    found.get_by_label("Opis problemu lub sugestii").fill("   ")

    found.get_by_role("button", name="Wyślij").click()

    expect(found.get_by_role("status")).to_have_text("Opis nie może być pusty.")
    expect(found.get_by_label("Opis problemu lub sugestii")).to_be_focused()
    assert len(reports(page, gui_server)) == before

    found.get_by_label("Opis problemu lub sugestii").fill("  Bez diagnostyki  ")
    found.get_by_role("checkbox", name="Dołącz dane diagnostyczne").uncheck()
    found.get_by_text("Pokaż co zostanie wysłane").click()
    expect(found.locator("pre")).to_have_text(
        "Dane diagnostyczne nie zostaną dołączone."
    )
    found.get_by_role("button", name="Wyślij").click()
    expect(found.get_by_role("status")).to_have_text(THANKS)
    expect(found).to_be_hidden()

    newest = reports(page, gui_server)[0]
    assert (newest["message"], newest["contact"], newest["diagnostics"]) == (
        "Bez diagnostyki",
        None,
        None,
    )

    # Escape and „Anuluj” close it; the next opening asks afresh
    open_dialog(page)
    page.keyboard.press("Escape")
    expect(found).to_be_hidden()
    open_dialog(page).get_by_role("button", name="Anuluj").click()
    expect(found).to_be_hidden()


def test_the_admin_page_lists_opens_marks_and_deletes_reports(
    new_tab: Callable[..., Tab], gui_server: Served, admin_key: str
) -> None:
    tab = new_tab(prefixed=True)
    page = tab.page
    tab.open("admin/")  # the admin page under a host's prefix
    remove_all(page, gui_server)
    markup = "<b>Pogrubione?</b> <img src=x> " + "długi opis " * 10
    diagnostics = {
        "events": [
            {
                "t": "2026-11-03T10:15:00.000Z",
                "type": "api_call",
                "data": {"status": 500},
            }
        ],
        "workspace": {"section": "siec", "path": []},
        "env": {"viewport": {"width": 390, "height": 844}},
    }
    for body in (
        {"message": "Pierwsze zgłoszenie"},
        {"message": markup, "diagnostics": diagnostics},
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

    # Opened: its details as text, and read
    newest.locator(".report-toggle").click()
    expect(newest.locator(".report-message")).to_have_text(markup)
    expect(page.locator("li.report b, li.report img")).to_have_count(0)
    expect(newest.locator(".report-details")).to_contain_text('"section": "siec"')
    expect(newest.locator(".report-events")).to_contain_text("api_call")
    expect(page.locator(".unread-count")).to_have_text("1")
    expect(newest.locator(".badge")).to_have_count(0)
    newest.get_by_role("button", name="Oznacz nieprzeczytane").click()
    expect(page.locator(".unread-count")).to_have_text("2")
    assert reports(page, gui_server)[0]["is_read"] is False

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


def test_the_diagnostics_stay_within_the_limit_and_leave_long_inputs_out(
    tab: Tab,
) -> None:
    tab.open()
    result = tab.page.evaluate(
        """async () => {
          const d = await import('./src/diagnostics.js');
          for (let i = 0; i < 60; i += 1) {
            d.logEvent('js_error', {i, stack: 'x'.repeat(3000)});
          }
          const snap = d.snapshot();
          return {
            bytes: d.jsonBytes(snap),
            first: snap.events[0].data.i,
            last: snap.events[snap.events.length - 1].data.i,
            count: snap.events.length,
            inputs: d.summarize({
              total_mm: '105', method: 'beta', ok: true, n: 2.5,
              pasted: '12.5\\n13.1', long: 'q'.repeat(201),
              list: Array.from({length: 60}, (_, i) => i),
            }),
          };
        }"""
    )

    assert result["bytes"] <= 100_000
    assert result["last"] == 59  # the newest kept, the oldest gone
    assert result["first"] > 10
    assert result["inputs"] == {
        "total_mm": "105",
        "method": "beta",
        "ok": True,
        "n": 2.5,
        "pasted": "[tekst: 9 znaków]",
        "long": "[tekst: 201 znaków]",
        "list": [*range(50), "[i 10 więcej]"],
    }
