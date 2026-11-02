"""uvicorn for :func:`hydrolog.gui.server.serve` (imported with the ``gui`` extra)."""

from __future__ import annotations

import contextlib
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


def run(
    app: Starlette, listener: socket.socket, *, url: str, open_browser: bool
) -> None:
    """Serve ``app`` on the bound ``listener`` until a signal stops it."""
    config = uvicorn.Config(
        app,
        log_config=None,
        access_log=False,
        lifespan="on",
        timeout_graceful_shutdown=_GRACE_S,
    )
    _Server(config, url=url, open_browser=open_browser).run(sockets=[listener])
