"""uvicorn for :func:`hydrolog.gui.server.serve` (imported with the ``gui`` extra).

The server keeps Nogat's logs (DEV-12.4 to DEV-12.9) through
:class:`~hydrolog.gui.nogat_logging.ServerLog`: the access log of the app's
:class:`~hydrolog.gui.nogat_logging.AccessLog`, the application log and the lifecycle
records in ``<state_dir>/hydrolog/logs/<kind>-YYYY-MM-DD.jsonl``, deleted after 14 days
by the server itself; standard error gets only the lifecycle records and the errors
reduced to their type. uvicorn runs with ``log_config=None`` and ``access_log=False``
(its access line names the client), and while the server runs the CLI's own handler
of the ``hydrolog`` logger is set aside, so the log reaches standard error only as
those records. Behind a proxy uvicorn takes the client's address from
``X-Forwarded-For`` only when the connection comes from ``FORWARDED_ALLOW_IPS``
(``127.0.0.1`` by default: a proxy on the same machine, such as ``cloudflared``); no
log holds it.
"""

from __future__ import annotations

import contextlib
import logging
import signal
import socket
import sys
import threading
import webbrowser
from collections.abc import Iterator

import uvicorn
from starlette.applications import Starlette

from hydrolog.gui.nogat_logging import ServerLog

_GRACE_S = 5
"""How long open requests may take to end at a stop [s]."""
_CLI_LOGGER = "hydrolog"
"""The logger whose stderr handler the CLI adds (``hydrolog.cli.main``)."""


class _Server(uvicorn.Server):
    """uvicorn's server that opens the browser and stops quietly on a signal.

    uvicorn re-raises a captured ``SIGINT`` or ``SIGTERM`` after its graceful stop;
    this server does not, so :func:`run` returns and the command exits with 0.
    """

    def __init__(self, config: uvicorn.Config, *, url: str, open_browser: bool) -> None:
        super().__init__(config)
        self._url = url
        self._open_browser = open_browser

    @contextlib.contextmanager
    def capture_signals(self) -> Iterator[None]:
        """Stop gracefully on ``SIGINT``/``SIGTERM`` (twice ``SIGINT``: at once)."""
        if threading.current_thread() is not threading.main_thread():
            yield
            return
        handled = [signal.SIGINT, signal.SIGTERM]
        if sys.platform == "win32":
            handled.append(signal.SIGBREAK)
        previous = {
            number: signal.signal(number, self.handle_exit) for number in handled
        }
        try:
            yield
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        """Start, then open the browser."""
        await super().startup(sockets=sockets)
        if self.should_exit:
            return
        if self._open_browser:
            threading.Thread(
                target=webbrowser.open, args=(self._url,), daemon=True
            ).start()


@contextlib.contextmanager
def _without_cli_handlers() -> Iterator[None]:
    """Set aside the CLI's handlers of the ``hydrolog`` logger while serving.

    Its records still reach the server's application log through the root logger;
    a handler of its own would print them on standard error beside the records of
    Nogat DEV-12.7.
    """
    logger = logging.getLogger(_CLI_LOGGER)
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
    try:
        yield
    finally:
        for handler in handlers:
            logger.addHandler(handler)


def run(
    app: Starlette,
    listener: socket.socket,
    *,
    url: str,
    open_browser: bool,
    log: ServerLog,
) -> None:
    """Serve ``app`` on the bound ``listener`` until a signal stops it.

    ``log`` starts before uvicorn, with the settings ``url`` and ``public`` in its
    record ``start``, and stops after it; the listener already listens, so a client
    that reads the record may connect at once.
    """
    config = uvicorn.Config(
        app,
        log_config=None,
        access_log=False,
        proxy_headers=True,
        lifespan="on",
        timeout_graceful_shutdown=_GRACE_S,
    )
    gui = getattr(app.state, "gui", None)
    public = getattr(gui, "public", None) is not None
    with _without_cli_handlers():
        log.start({"url": url, "public": public})
        try:
            server = _Server(config, url=url, open_browser=open_browser)
            server.run(sockets=[listener])
        finally:
            log.stop()
