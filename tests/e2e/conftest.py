"""Fixtures of the browser tests: a live GUI server and watched Chromium tabs.

``gui_server`` serves the GUI (the package's ``web/`` and its API, two workers) on a
free port of 127.0.0.1, at ``/`` and, as a host mounts it, under ``/m/hydrolog/``.
``new_tab(width=1440, height=900, theme="light", prefixed=False)`` opens a page in a
fresh Chromium context (cookies of its own: a new session; Polish locale, Warsaw
time, ``prefers-color-scheme`` of ``theme`` with the stored theme left on Auto) that
records console errors, page errors and CSP violations (``securitypolicyviolation``):
any of them fails the test when the tab closes. ``tab`` is ``new_tab()``.

Pure JavaScript modules are tested in a tab, without Node::

    tab.open()
    tab.page.evaluate("async () => (await import('./src/format.js')).number(1.5)")

Chromium is installed once: ``uv run --no-sync playwright install chromium``.
"""

import contextlib
import socket
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Playwright,
    expect,
    sync_playwright,
)
from playwright.sync_api import Error as PlaywrightError

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


@dataclass(frozen=True)
class Served:
    """The live server of the browser tests."""

    base: str
    """The page at the root: ``http://127.0.0.1:<port>/``."""

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


@pytest.fixture(scope="package")
def gui_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Served]:
    """Serve the GUI on a free port at ``/`` and under ``/m/hydrolog/``."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    from hydrolog.gui import create_app

    gui = create_app(work_root=tmp_path_factory.mktemp("gui-work"))

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
    yield Served(f"http://127.0.0.1:{port}/")
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
    """Yield ``new_tab(width=1440, height=900, theme="light", prefixed=False)``."""
    opened: list[tuple[BrowserContext, Tab]] = []

    def open_tab(
        *,
        width: int = 1440,
        height: int = 900,
        theme: str = "light",
        prefixed: bool = False,
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
