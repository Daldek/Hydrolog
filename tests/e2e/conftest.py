"""Fixtures of the browser tests: a live GUI server and watched Chromium tabs.

``gui_server`` serves the GUI (the package's ``web/`` and its API, two workers) on a
free port of 127.0.0.1, at ``/`` and, as a host mounts it, under ``/m/hydrolog/``; the
reports of „Zgłoś uwagę” go to a data directory of its own (``Served.data_dir``).
``new_tab(width=1440, height=900, theme="light", prefixed=False, welcome=False)`` opens
a page in a fresh Chromium context (cookies of its own: a new session; Polish locale,
Warsaw time, ``prefers-color-scheme`` of ``theme`` with the stored theme left on Auto)
that records console errors, page errors and CSP violations
(``securitypolicyviolation``): any of them fails the test when the tab closes. The
welcome dialog of a visit covers the page, so a tab starts as a visitor who ticked „Nie
pokazuj ponownie” unless ``welcome=True``. ``tab`` is ``new_tab()``.

Every section starts empty. ``seed_hydrogram(tab)`` stores the inputs of the guide's
worked example of Hydrogram zlewni, Kamiennik at Świerzawa
(``tests/fixtures/kamiennik.json`` read with „Plik zlewni…”, the mockup's storm, SCS
with Kirpich: ``kamiennik_inputs()``), before the tab's first page runs, as a browser
that typed them would have them; ``load_network(page)`` loads the guide's worked
example of Sieć (``web/instrukcja/przyklady/siec.json``, eight nodes) with „Plik
sieci…”.

``precip pmaxtp`` is the one command that goes to IMGW-PIB (ADR-0018): every tab
answers the page's runs of it in this process (``pmaxtp_route()``), Obserwator reading
the PMAXTP table recorded at Kamiennik's outlet, so the tests stay offline; a test
routes ``PMAXTP_RUN`` on its page to answer otherwise.

Pure JavaScript modules are tested in a tab, without Node::

    tab.open()
    tab.page.evaluate("async () => (await import('./src/format.js')).number(1.5)")

Chromium is installed once: ``uv run --no-sync playwright install chromium``.
"""

import contextlib
import json
import socket
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Playwright,
    Route,
    expect,
    sync_playwright,
)
from playwright.sync_api import Error as PlaywrightError

from tests.conftest import recorded_fetch

PREFIX = "/m/hydrolog"
"""Where the test host mounts the app, as Nogat's host would."""
EXPECT_TIMEOUT_MS = 30_000
"""How long an expectation waits: a bound for what never comes, not a speed."""
START_TIMEOUT_S = 60.0
# Chromium logs every 4xx/5xx answer like this; tests assert expected API errors.
FAILED_RESOURCE = "Failed to load resource"
# Installed before any script of the page; the page's CSP does not apply to it.
CSP_WATCH = """
document.addEventListener("securitypolicyviolation", (event) => {
  window.hydrologCspViolation({
    directive: event.violatedDirective,
    blocked: event.blockedURI,
    sample: event.sample,
  });
});
"""
# Run before the page's scripts: the welcome dialog's „Nie pokazuj ponownie” is ticked.
WELCOME_OFF = """
try {
  localStorage.setItem("hydrolog-gui/welcome/1", JSON.stringify({ hidden: true }));
} catch (error) {}
"""
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
KAMIENNIK: dict[str, Any] = json.loads(
    (FIXTURES / "kamiennik.json").read_text(encoding="utf-8")
)
"""The watershed of the guide's worked example, Kamiennik at Świerzawa (a
WatershedParameters JSON, as ``--watershed-file`` reads it)."""
HYDROGRAM_KEY = "hydrolog-gui/hydrogram/2"
"""Where Hydrogram zlewni keeps its inputs (``persist.js``)."""
GUIDE_NETWORK = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "hydrolog"
    / "gui"
    / "web"
    / "instrukcja"
    / "przyklady"
    / "siec.json"
)
"""The guide's worked example of Sieć (``example_network_document()``)."""
NASH_TYPED = {"area_km2": "45,3", "n": "3", "k_min": "30"}
"""The guide's worked example of Wszystkie polecenia: ``uh nash`` by n and K."""
PMAXTP_TABLE = FIXTURES / "pmaxtp_kamiennik_pot.json"
"""IMGW-PIB's PMAXTP answer at Kamiennik's outlet (51.01544, 15.88984, POT), recorded
on 2026-11-04 as Obserwator returns it: 12 h at 1 % is 101.82 mm."""
PMAXTP_RUN = "**/api/run/precip/pmaxtp*"
"""The page's runs of ``precip pmaxtp``."""
KAMIENNIK_POINT = {"latitude": 51.01544, "longitude": 15.88984}
"""Kamiennik's outlet at Świerzawa in Hydrograf (WGS84): the guide's PMAXTP point."""


def pmaxtp_answer(
    options: dict[str, Any], fetch: Callable[..., Any] | None = None
) -> tuple[int, dict[str, Any]]:
    """Return the GUI server's answer to ``precip pmaxtp`` with ``options``, made here.

    The worker's own code runs in this process with Obserwator answering from
    :data:`PMAXTP_TABLE`, or from ``fetch`` (a stand-in of ``obserwator.fetch_pmaxtp``):
    the HTTP status and the ``hydrolog-result/1`` envelope or the ``hydrolog-error/1``
    document the page receives, without the network.
    """
    import obserwator

    from hydrolog.gui._app import _http_status
    from hydrolog.gui._worker import handle

    request = {"command": "precip pmaxtp", "options": options, "root": str(FIXTURES)}
    with mock.patch.object(
        obserwator, "fetch_pmaxtp", fetch or recorded_fetch(PMAXTP_TABLE)
    ):
        reply = handle(request)
    document: dict[str, Any] = reply["document"]
    return (_http_status(document["code"]) if reply["error"] else 200), document


def pmaxtp_route(fetch: Callable[..., Any] | None = None) -> Callable[[Route], None]:
    """Return a route handler that answers the page's ``precip pmaxtp`` here."""

    def answer(route: Route) -> None:
        status, document = pmaxtp_answer(route.request.post_data_json or {}, fetch)
        route.fulfill(status=status, json=document)

    return answer


def load_network(page: Page, *files: Path) -> None:
    """Load ``files`` (default: the guide's network) with Sieć's „Plik sieci…”.

    Sieć must be shown; the input is the empty section's or the open network's.
    """
    page.locator('section[data-section="siec"] [data-input="network"]').set_input_files(
        list(files) or [GUIDE_NETWORK]
    )


def type_nash(page: Page) -> None:
    """Type the guide's example (``NASH_TYPED``) into the shown form of ``uh nash``."""
    form = page.locator('section[data-section="polecenia"] .cmd-form')
    for name, text in NASH_TYPED.items():
        form.locator(f'[data-option="{name}"] input').fill(text)


def input_text(value: float) -> str:
    """Return ``value`` as the page writes a number into a field (``inputText``)."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).replace(".", ",")


def kamiennik_inputs(**changes: Any) -> dict[str, Any]:
    """Return Hydrogram zlewni's stored inputs of the guide's worked example.

    The watershed is ``kamiennik.json`` as „Plik zlewni…” reads it (the file its
    origin); the storm is PMAXTP at the outlet (``KAMIENNIK_POINT``), p 1 %, 12 h, POT,
    with the depth remembered as fetched there: 105 mm, the mockup's (IMGW-PIB's atlas
    gives 101,82 mm, which a fetch answers), the depth also typed for „Hietogram”;
    Beta (2; 5), Δt 10 min, the model SCS with tc by Kirpich, AMC II, and Clark's R/tc
    0,5: the mockup's runs. ``changes`` replace inputs (``watershed`` replaces the
    typed watershed, not its origin).
    """
    inputs: dict[str, Any] = {
        "watershed": {
            name: value if isinstance(value, str) else input_text(value)
            for name, value in KAMIENNIK.items()
        },
        "origin": {
            "label": "kamiennik.json",
            "title": "Z pliku: kamiennik.json",
            "detail": "wczytano 4 lis 2026, 10:00 · 21 pól",
            "mark": None,
            "values": KAMIENNIK,
        },
        "tc_method": "kirpich",
        "tc_manual": False,
        "tc_min": "",
        "rain_source": "pmaxtp",
        "pmaxtp_latitude": input_text(KAMIENNIK_POINT["latitude"]),
        "pmaxtp_longitude": input_text(KAMIENNIK_POINT["longitude"]),
        "pmaxtp_probability_pct": "1",
        "pmaxtp_duration_min": "720",
        "pmaxtp_method": "POT",
        "pmaxtp_fetched": {
            **KAMIENNIK_POINT,
            "duration_min": 720,
            "probability_percent": 1,
            "method": "POT",
            "depth_mm": 105,
        },
        "total_mm": "105",
        "duration_min": "",
        "hietogram_type": "beta",
        "alpha": "2",
        "beta": "5",
        "peak_position": "",
        "values": "",
        "timestep_min": "10",
        "amc": "II",
        "ia_coefficient": "",
        "uh_model": "scs",
        "nash_source": "lutz",
        "nash_n": "",
        "nash_k_min": "",
        "clark_kind": "ratio",
        "clark_r_tc_ratio": "0,5",
        "clark_r_min": "",
        "snyder_length_km": "",
        "snyder_centroid_length_km": "",
        "snyder_ct": "",
        "snyder_cp": "",
    }
    inputs.update(changes)
    return inputs


@dataclass(frozen=True)
class Served:
    """The live server of the browser tests."""

    base: str
    """The page at the root: ``http://127.0.0.1:<port>/``."""
    data_dir: Path
    """The ``data_dir`` of the app: its reports are ``hydrolog/feedback.sqlite3``."""

    @property
    def prefixed(self) -> str:
        """str: the page as a host mounts it, ``<base>m/hydrolog/``."""
        return self.base + PREFIX.lstrip("/") + "/"

    def url(self, path: str = "") -> str:
        """Return ``base`` + ``path`` (``"api/session"``, ``"#siec"``)."""
        return self.base + path


@dataclass
class Tab:
    """A page of a fresh browser context and what went wrong on it."""

    page: Page
    base: str
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)

    def watch(self) -> None:
        """Start recording; called once, before the first navigation."""
        self.page.expose_function(
            "hydrologCspViolation", lambda violation: self.violations.append(violation)
        )
        self.page.add_init_script(CSP_WATCH)
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.on("console", self._console)

    def open(self, path: str = "") -> None:
        """Open ``base`` + ``path`` (``""``, ``"#hydrogram"``, ``"?nogat=1"``)."""
        self.page.goto(self.base + path)

    def csp_violations(self) -> list[dict[str, Any]]:
        """Return the CSP violations of every page opened in this tab so far."""
        return list(self.violations)

    def assert_clean(self) -> None:
        """Check that no CSP violation, page error or console error happened."""
        assert self.violations == [], self.violations
        assert self.page_errors == [], self.page_errors
        assert self.console_errors == [], self.console_errors

    def _console(self, message: ConsoleMessage) -> None:
        if message.type == "error" and not message.text.startswith(FAILED_RESOURCE):
            self.console_errors.append(message.text)


def seed_hydrogram(tab: Tab, inputs: dict[str, Any] | None = None) -> None:
    """Store Hydrogram zlewni's inputs (default ``kamiennik_inputs()``) for the tab.

    The script runs before the scripts of the tab's first page of the app and stores
    them once per tab (a mark in ``sessionStorage``): a reload or „Wyczyść” afterwards
    shows what the page itself stored.
    """
    stored = json.dumps(
        json.dumps(inputs if inputs is not None else kamiennik_inputs())
    )
    tab.page.add_init_script(
        "try {"
        " if (!sessionStorage.getItem('hydrolog-test/seeded')) {"
        f"  localStorage.setItem({json.dumps(HYDROGRAM_KEY)}, {stored});"
        "  sessionStorage.setItem('hydrolog-test/seeded', '1');"
        " }"
        "} catch (error) {}"
    )


@pytest.fixture(scope="package")
def gui_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Served]:
    """Serve the GUI on a free port at ``/`` and under ``/m/hydrolog/``."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    from hydrolog.gui import create_app

    data_dir = tmp_path_factory.mktemp("gui-data")
    gui = create_app(work_root=tmp_path_factory.mktemp("gui-work"), data_dir=data_dir)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with gui.router.lifespan_context(gui):
            yield

    host = Starlette(
        routes=[Mount(PREFIX, app=gui), Mount("/", app=gui)], lifespan=lifespan
    )
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    config = uvicorn.Config(host, log_config=None, access_log=False, lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [listener]}, daemon=True
    )
    thread.start()
    deadline = time.monotonic() + START_TIMEOUT_S
    while not server.started:
        assert thread.is_alive(), "the GUI server did not start"
        assert time.monotonic() < deadline, "the GUI server did not start in time"
        time.sleep(0.05)
    yield Served(f"http://127.0.0.1:{port}/", data_dir)
    server.should_exit = True
    thread.join(timeout=START_TIMEOUT_S)
    listener.close()


@pytest.fixture(scope="package")
def playwright() -> Iterator[Playwright]:
    """Yield Playwright; expectations wait up to ``EXPECT_TIMEOUT_MS``."""
    with sync_playwright() as running:
        expect.set_options(timeout=EXPECT_TIMEOUT_MS)
        yield running
        expect.set_options(timeout=None)


@pytest.fixture(scope="package")
def chromium(playwright: Playwright) -> Iterator[Browser]:
    """Yield one headless Chromium; fail saying how to install it."""
    try:
        browser = playwright.chromium.launch()
    except PlaywrightError as error:
        pytest.fail(
            "Chromium for Playwright is missing; install it with "
            f"`uv run --no-sync playwright install chromium` ({error})"
        )
    yield browser
    browser.close()


@pytest.fixture
def new_tab(chromium: Browser, gui_server: Served) -> Iterator[Callable[..., Tab]]:
    """Yield ``new_tab(width=1440, height=900, theme="light", prefixed=False,
    welcome=False)``."""
    opened: list[tuple[BrowserContext, Tab]] = []

    def open_tab(
        *,
        width: int = 1440,
        height: int = 900,
        theme: str = "light",
        prefixed: bool = False,
        welcome: bool = False,
    ) -> Tab:
        context = chromium.new_context(
            viewport={"width": width, "height": height},
            locale="pl-PL",
            timezone_id="Europe/Warsaw",
            color_scheme="dark" if theme == "dark" else "light",
        )
        base = gui_server.prefixed if prefixed else gui_server.base
        tab = Tab(context.new_page(), base)
        tab.watch()
        context.route(PMAXTP_RUN, pmaxtp_route())
        if not welcome:
            tab.page.add_init_script(WELCOME_OFF)
        opened.append((context, tab))
        return tab

    yield open_tab
    for context, _ in opened:
        context.close()
    for _, tab in opened:
        tab.assert_clean()


@pytest.fixture
def tab(new_tab: Callable[..., Tab]) -> Tab:
    """Return ``new_tab()``: 1440 x 900, light, at the root."""
    return new_tab()
