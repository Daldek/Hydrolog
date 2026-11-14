"""The standalone GUI server: ``hydrolog gui serve`` (plan D3, D8).

:func:`serve` binds the address, serves :func:`hydrolog.gui.create_app` with uvicorn
and blocks until Ctrl+C or ``SIGTERM``, which stop it gracefully: it returns, so the
command ends with exit code 0. It keeps Nogat's logs (DEV-12.4 to DEV-12.9) in
``<state_dir>/hydrolog/logs``; its record ``start`` on standard error names the
address once it listens. It has no sign-in: anyone who reaches the address can use
it, so beyond loopback it belongs behind an authenticating proxy (``docs/USAGE.md``).

Importing this module imports neither Starlette nor uvicorn.
"""

from __future__ import annotations

import errno
import socket
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hydrolog.exceptions import ConflictError, InvalidParameterError

__all__ = ["serve"]

_IN_USE = frozenset(
    code
    for code in (errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", None))
    if code is not None
)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def url_of(host: str, port: int) -> str:
    """Return the address of the page, ``http://<host>:<port>/``.

    Parameters
    ----------
    host : str
        Host name or address; an IPv6 address is put in brackets.
    port : int
        TCP port.

    Returns
    -------
    str
        The URL.
    """
    shown = f"[{host}]" if ":" in host else host
    return f"http://{shown}:{port}/"


def _bind(host: str, port: int) -> socket.socket:
    """Return a listening socket bound to ``host:port`` (port 0: a free one)."""
    try:
        family, kind, proto, _, address = socket.getaddrinfo(
            host, port, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE
        )[0]
    except socket.gaierror as exc:
        raise InvalidParameterError(
            f"Option 'host': cannot resolve {host!r} ({exc})",
            details={"option": "host", "reason": "invalid_host", "value": host},
        ) from exc
    listener = socket.socket(family, kind, proto)
    try:
        if sys.platform != "win32":  # on Windows the option would share the port
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(address)
        listener.listen()
    except OSError as exc:
        listener.close()
        if exc.errno in _IN_USE:
            raise ConflictError(
                f"Port {port} of {host} is in use",
                details={"reason": "port_in_use", "host": host, "port": port},
                hint="Stop the program that uses it or choose another with --port.",
            ) from exc
        raise
    return listener


def serve(
    *,
    host: str,
    port: int,
    open_browser: bool,
    warnings: Sequence[tuple[str, str]] = (),
) -> dict[str, Any]:
    """Serve the GUI until Ctrl+C or ``SIGTERM``.

    Parameters
    ----------
    host : str
        Address to listen on (``127.0.0.1`` for this computer only).
    port : int
        TCP port (``0`` takes a free one; the record ``start`` names it).
    open_browser : bool
        Open the page in the default browser once the server listens.
    warnings : sequence of (str, str), optional
        ``(event, message)`` warnings of the caller, written as app records of the
        log once it has started, never on standard error (Nogat DEV-12.7).

    Returns
    -------
    dict
        ``url`` (the page), ``started_at`` and ``stopped_at`` (UTC, ISO 8601).

    Raises
    ------
    MissingDependencyError
        If the ``gui`` extra (Starlette, uvicorn) is not installed.
    ConflictError
        If the port is in use (``details.reason`` ``port_in_use``).
    InvalidParameterError
        If ``host`` cannot be resolved (``details.reason`` ``invalid_host``).
    """
    from hydrolog import __version__
    from hydrolog._settings import TOOL, resolve_setting
    from hydrolog.gui import create_app
    from hydrolog.gui._extra import require_gui_extra

    require_gui_extra()
    from hydrolog.gui._serving import run
    from hydrolog.gui.nogat_logging import ServerLog

    state_dir = Path(resolve_setting("state_dir").value)
    log = ServerLog(TOOL, __version__, state_dir / TOOL / "logs")
    listener = _bind(host, port)
    try:
        url = url_of(host, listener.getsockname()[1])
        started_at = _now()
        run(
            lambda: create_app(log=log),
            listener,
            url=url,
            open_browser=open_browser,
            log=log,
            warnings=warnings,
        )
    finally:
        listener.close()
    return {"url": url, "started_at": started_at, "stopped_at": _now()}
