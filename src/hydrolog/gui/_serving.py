"""uvicorn for :func:`hydrolog.gui.server.serve` (imported with the ``gui`` extra).

uvicorn writes no access log of its own (it names the client); a public GUI writes
its own, without the client's address, as JSON lines on standard error (Nogat
DEV-15.10), which the service manager keeps (journald: 14 days, ``docs/USAGE.md``).
Behind a proxy uvicorn takes the client's address from ``X-Forwarded-For`` only when
the connection comes from ``FORWARDED_ALLOW_IPS`` (``127.0.0.1`` by default: a proxy
on the same machine, such as ``cloudflared``).
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

_GRACE_S = 5
"""How long open requests may take to end at a stop [s]."""


class _Server(uvicorn.Server):
    """uvicorn's server that announces its address and stops quietly on a signal.

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
        """Start, then announce the address (and open the browser)."""
        await super().startup(sockets=sockets)
        if self.should_exit:
            return
        print(f"Hydrolog GUI: {self._url}", file=sys.stderr, flush=True)
        if self._open_browser:
            threading.Thread(
                target=webbrowser.open, args=(self._url,), daemon=True
            ).start()


@contextlib.contextmanager
def _access_log(app: Starlette) -> Iterator[None]:
    """Send the access log of a public GUI to standard error while it serves."""
    gui = getattr(app.state, "gui", None)
    if getattr(gui, "public", None) is None:
        yield
        return
    from hydrolog.gui._public import ACCESS_LOGGER

    logger = logging.getLogger(ACCESS_LOGGER)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    previous = (logger.level, logger.propagate)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        yield
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous[0])
        logger.propagate = previous[1]


def run(
    app: Starlette, listener: socket.socket, *, url: str, open_browser: bool
) -> None:
    """Serve ``app`` on the bound ``listener`` until a signal stops it."""
    config = uvicorn.Config(
        app,
        log_config=None,
        access_log=False,
        proxy_headers=True,
        lifespan="on",
        timeout_graceful_shutdown=_GRACE_S,
    )
    with _access_log(app):
        _Server(config, url=url, open_browser=open_browser).run(sockets=[listener])
