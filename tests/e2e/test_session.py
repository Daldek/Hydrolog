"""The session of a tab without a cookie (Nogat DEV-15.10, DEV-15.11) in Chromium.

The page keeps the session id in memory and names it in the header
``X-Hydrolog-Session`` of its requests; the server never sets a cookie. A visit that
uploads a file, runs a command and downloads its output (at the root and under the
host's prefix) stores no cookie and sends none, and every request of the page names
the one session the first answer opened. Two tabs have sessions of their own; leaving
the page (or reloading it) ends its session, whose files the server then no longer
gives. A saved file sends ``POST api/stats/download``, once per file.

``page_session(page)`` and ``session_text(page, path)`` read the tab's session the way
the page does (its own ``api.js``, with its header), for tests that check what the page
sent.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page, Request, Response, expect

from tests.e2e.conftest import Tab

HEADER = "x-hydrolog-session"
"""The header with the session id (Playwright gives header names in lower case)."""
FLOOD_INFLOW = Path(__file__).resolve().parents[1] / "fixtures" / "flood_inflow.csv"
POL = 'section[data-section="polecenia"]'
RIGHT = f"{POL} .view-panel.right"
STATS_DOWNLOAD = "/api/stats/download"


def page_session(page: Page) -> dict[str, Any]:
    """Return the tab's ``GET api/session`` as the page reads it (with its header)."""
    document: dict[str, Any] = page.evaluate(
        "async () => (await import('./src/api.js')).api.session()"
    )
    return document


def session_text(page: Page, path: str) -> str:
    """Return the text of the tab's session file ``path`` (``"in/siec.json"``)."""
    text: str = page.evaluate(
        "async (path) => (await import('./src/api.js')).api.fileText(path)", path
    )
    return text


def option(page: Page, name: str) -> Any:
    """Return the field of the option ``name`` in the form of Polecenia."""
    return page.locator(f'{POL} .cmd-form [data-option="{name}"]')


def upload_inflow(page: Page) -> None:
    """Open ``route lag`` with its inflow from a file; upload ``flood_inflow.csv``."""
    expect(page.locator(f"{POL} .cmd-form .cmd-head code")).to_have_text("route lag")
    page.locator(f'{POL} .cmd-form .one-of [role="radio"]').nth(1).click()
    source = option(page, "input_file")
    # A reload keeps the form's choice of the file, so wait for the upload's own answer
    with page.expect_response(
        lambda answer: answer.request.method == "PUT" and "/api/files/in/" in answer.url
    ) as stored:
        source.locator('input[type="file"]').set_input_files(FLOOD_INFLOW)
    assert stored.value.ok
    expect(source.locator("select")).to_have_value("in/flood_inflow.csv")


def run_lag(page: Page) -> Response:
    """Fill the lag and the output, press „Uruchom” and return the run's answer."""
    option(page, "lag_min").locator("input").fill("30")
    option(page, "output").locator("input").fill("outflow.csv")
    with page.expect_response(
        lambda response: "/api/run/route/lag" in response.url
    ) as answer:
        page.get_by_role("button", name="Uruchom").click()
    return answer.value


def download(page: Page, trigger: Any) -> tuple[str, bytes]:
    """Click ``trigger``; return the name and the bytes of the download it starts."""
    with page.expect_download() as started:
        trigger.click()
    return started.value.suggested_filename, Path(started.value.path()).read_bytes()


def answered_ids(page: Page) -> list[str]:
    """Record the session ids the server names in its answers to ``page``."""
    ids: list[str] = []

    def keep(response: Response) -> None:
        named = response.headers.get(HEADER)
        if named:
            ids.append(named)

    page.on("response", keep)
    return ids


def eventually(check: Callable[[], bool], seconds: float = 10.0) -> bool:
    """Return whether ``check()`` becomes true within ``seconds``."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.1)
    return check()


@pytest.mark.parametrize("prefixed", [False, True], ids=["root", "prefixed"])
def test_a_visit_keeps_one_session_without_a_cookie(
    new_tab: Callable[..., Tab], prefixed: bool
) -> None:
    tab = new_tab(prefixed=prefixed)
    page = tab.page
    requests: list[Request] = []
    page.on("request", lambda request: requests.append(request))
    ids = answered_ids(page)
    tab.open("#polecenia/route/lag")

    upload_inflow(page)
    response = run_lag(page)
    assert response.ok
    button = page.locator(f"{RIGHT} .file-list button")
    expect(button).to_have_count(1)
    name, data = download(page, button)
    assert name == "outflow.csv"
    assert data.decode().splitlines()[0] == "time_min,discharge_m3s"

    # The first answer opened the session, and only that one named it
    session = page_session(page)
    assert ids == [session["id"]]
    assert {item["path"] for item in session["files"]} == {
        "in/flood_inflow.csv",
        "out/outflow.csv",
    }
    # No cookie stored or sent; the upload, the run and the download named the session
    assert page.context.cookies() == []
    api = [request for request in requests if "/api/" in request.url]
    assert api
    for request in api:
        assert "cookie" not in request.all_headers(), request.url
    for marker in ("/api/files/in/", "/api/run/", "/api/files/out/outflow.csv"):
        used = [request for request in api if marker in request.url]
        assert used, marker
        assert {request.all_headers().get(HEADER) for request in used} == {
            session["id"]
        }


def test_two_tabs_have_sessions_of_their_own(new_tab: Callable[..., Tab]) -> None:
    first, second = new_tab(), new_tab()
    first.open("#polecenia/route/lag")
    upload_inflow(first.page)
    second.open("#polecenia/route/lag")
    expect(second.page.locator(f"{POL} .cmd-form .cmd-head code")).to_have_text(
        "route lag"
    )
    second.page.locator(f'{POL} .cmd-form .one-of [role="radio"]').nth(1).click()

    # The second tab's file field offers none of the first tab's files
    expect(option(second.page, "input_file").locator("select option")).to_have_count(1)
    mine, theirs = page_session(first.page), page_session(second.page)
    assert mine["id"] != theirs["id"]
    assert [item["path"] for item in mine["files"]] == ["in/flood_inflow.csv"]
    assert theirs["files"] == []


def test_leaving_or_reloading_the_page_ends_its_session(tab: Tab) -> None:
    page = tab.page
    ids = answered_ids(page)
    tab.open("#polecenia/route/lag")
    upload_inflow(page)
    url = tab.base + "api/files/in/flood_inflow.csv"

    def status(session: str) -> int:
        return page.request.get(url, headers={"X-Hydrolog-Session": session}).status

    # The file is the session's: given with its id, not without it
    first = ids[0]
    assert status(first) == 200
    assert page.request.get(url).status == 404

    # A reload is a new visit: the old session ends, the page opens another
    page.reload()
    upload_inflow(page)
    assert eventually(lambda: status(first) == 404)
    assert len(set(ids)) == 2
    second = ids[-1]
    assert second != first
    assert status(second) == 200

    # Leaving the page ends the session (pagehide)
    page.goto("about:blank")
    assert eventually(lambda: status(second) == 404)


def test_a_saved_file_is_counted_once(tab: Tab) -> None:
    page = tab.page
    counted: list[Request] = []
    page.on(
        "request",
        lambda request: (
            counted.append(request) if "/api/stats/" in request.url else None
        ),
    )
    tab.open("#polecenia/route/lag")
    upload_inflow(page)
    run_lag(page)
    assert counted == []  # neither the upload nor the run is a download

    # A file of the session
    with page.expect_response(lambda answer: STATS_DOWNLOAD in answer.url) as sent:
        download(page, page.locator(f"{RIGHT} .file-list button"))
    assert sent.value.status == 204
    # An export written in the browser
    with page.expect_response(lambda answer: STATS_DOWNLOAD in answer.url):
        download(page, page.locator(f"{RIGHT} .export-row button", has_text="CSV"))

    assert [(request.method, request.post_data) for request in counted] == [
        ("POST", None),
        ("POST", None),
    ]
    assert all(request.url.endswith(STATS_DOWNLOAD) for request in counted)
