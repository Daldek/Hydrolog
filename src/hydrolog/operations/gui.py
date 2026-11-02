"""Operations of the group ``gui``: the web GUI of Hydrolog (ADR-0014).

:func:`gui_serve` starts the web server of :mod:`hydrolog.gui` (extra ``gui``:
Starlette and uvicorn) on this computer and blocks until Ctrl+C or ``SIGTERM`` stops
it; the result says where it served and when. With ``check`` it serves nothing and
returns the plan of the call: the address it would serve on and whether the port is
free. The server has no sign-in, so an address that other computers reach adds the
notice ``exposed_without_auth``, which is also logged when the server starts (the
result comes only when it stops). The function is re-exported by
:mod:`hydrolog.operations`.
"""

from __future__ import annotations

import errno
import importlib
import ipaddress
import logging
import os
import socket
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Final

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.notices import notice
from hydrolog.exceptions import InvalidParameterError, MissingDependencyError
from hydrolog.operations._outputs import PLAN_SCHEMA

__all__ = ["GuiServeResult", "gui_serve"]

LOG = logging.getLogger(__name__)

EXTRA_MODULES: Final = ("starlette", "uvicorn")
"""Packages of the extra ``gui`` that the server needs."""
INSTALL_HINT: Final = 'pip install "hydrolog[gui]"'
"""How to install the extra ``gui``."""


@dataclass
class GuiServeResult(JsonResultMixin):
    """Where and when a server of the GUI served (``hydrolog-gui-serve/1``).

    Attributes
    ----------
    url : str
        Address of the page, e.g. ``http://127.0.0.1:8070/``.
    started_at, stopped_at : str
        When the server started listening and when it stopped (ISO 8601, UTC, whole
        seconds, e.g. ``2026-11-02T10:15:00Z``).
    """

    url: str
    started_at: str
    stopped_at: str


def _url(host: str, port: int) -> str:
    """Address of the page: an IPv6 address in brackets."""
    shown = f"[{host}]" if ":" in host else host
    return f"http://{shown}:{port}/"


def _loopback(host: str) -> bool:
    """Whether ``host`` is reachable from this computer only."""
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _require_extra() -> None:
    """Refuse to plan or serve without the packages of the extra ``gui``."""
    for module in EXTRA_MODULES:
        if find_spec(module) is None:
            raise MissingDependencyError(
                f"The GUI needs the package {module!r} of the extra 'gui'",
                details={"extra": "gui", "module": module},
                hint=INSTALL_HINT,
            )


def _invalid_host(host: str, reason: object) -> InvalidParameterError:
    return InvalidParameterError(
        f"Option 'host': {host!r} is not an address of this computer: {reason}",
        details={"option": "host", "reason": "invalid_host", "value": host},
        hint="Give 127.0.0.1 (this computer only) or an address of a network "
        "interface of this computer (0.0.0.0 for all of them).",
    )


def _port_free(host: str, port: int) -> bool:
    """Whether a server could listen on ``host`` and ``port`` now.

    Binds a socket the way uvicorn does (``SO_REUSEADDR`` outside Windows) and closes
    it; ``False`` when the port is taken or may not be bound.
    """
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise _invalid_host(host, exc) from exc
    for family, kind, protocol, _, address in addresses:
        with socket.socket(family, kind, protocol) as probe:
            if os.name != "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(address)
            except OSError as exc:
                if exc.errno == errno.EADDRNOTAVAIL:
                    raise _invalid_host(host, exc) from exc
                return False
    return True


def gui_serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8070,
    no_browser: bool = False,
    check: bool = False,
) -> OperationOutput:
    """Serve the web GUI on this computer until it is stopped (``gui serve``).

    Parameters
    ----------
    host : str, optional
        Address to listen on, by default ``"127.0.0.1"`` (this computer only). Any
        other address (``"0.0.0.0"``, an address in a network) lets other computers
        in without a sign-in; expose it only behind an authenticating proxy.
    port : int, optional
        TCP port, 1 to 65535, by default 8070.
    no_browser : bool, optional
        Do not open the page in a web browser, by default ``False``.
    check : bool, optional
        Plan without serving, by default ``False``: the result is the
        ``hydrolog-plan/1`` document ``{"targets": [], "url", "port_free"}``.

    Returns
    -------
    OperationOutput
        After the server has stopped (Ctrl+C or ``SIGTERM``), a
        :class:`GuiServeResult`; with ``check``, the plan. A ``host`` other than a
        loopback address adds the warning ``exposed_without_auth``.

    Raises
    ------
    MissingDependencyError
        If the extra ``gui`` is not installed (``details.module``; the hint says how
        to install it).
    InvalidParameterError
        If ``host`` is not an address of this computer (``details.reason``
        ``invalid_host``).
    ConflictError
        If the port is taken when the server starts (``details.reason``
        ``port_in_use``).
    """
    _require_extra()
    url = _url(host, port)
    notices: list[Notice] = []
    if not _loopback(host):
        notices.append(notice("exposed_without_auth", host=host, url=url))
    if check:
        plan: dict[str, Any] = {
            "schema": PLAN_SCHEMA,
            "targets": [],
            "url": url,
            "port_free": _port_free(host, port),
        }
        return OperationOutput(plan, notices, check=True)
    for item in notices:
        LOG.warning("%s", item.message)
    # The server is the package hydrolog.gui, imported only to serve: it imports
    # Starlette and uvicorn, which the base install lacks.
    server = importlib.import_module("hydrolog.gui.server")
    served = server.serve(host=host, port=port, open_browser=not no_browser)
    result = GuiServeResult(
        url=str(served["url"]),
        started_at=str(served["started_at"]),
        stopped_at=str(served["stopped_at"]),
    )
    return OperationOutput(result, notices)
