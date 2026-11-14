"""The rules of a public GUI (Nogat DEV-15.7 to DEV-15.11): limit and totals.

A deployment that sets ``[nogat.operator]`` opens the GUI to anyone (:class:`Public`);
the app then wraps every request in :class:`PublicGuard`:

* **Request limit** (DEV-15.9): :class:`RateLimiter` counts the requests of each
  client address, ``request_limit`` in ``request_window`` seconds (300 in 60 by
  default). Static files are not counted, nor the catalog documents
  (``api/commands…``, ``api/schemas/…``), which are as static as the files: the same
  for everyone while the server runs, and about fifty of them per page load. Over the
  limit a request gets ``429`` with ``Retry-After``: an API route the
  ``hydrolog-error/1`` of ``rate_limited``, a page „Zbyt wiele żądań. Spróbuj ponownie
  za <n> s.”. An address stays in memory for its window only and is never written.
* **Access log**: not this module's. ``hydrolog gui serve`` writes it in every run,
  public or not, with :class:`hydrolog.gui.nogat_logging.AccessLog` outside this
  guard (Nogat DEV-12.4 to DEV-12.9).
* **Daily totals** (DEV-15.11): :class:`DailyStats` keeps the day's distinct visitors
  as HMAC-SHA-256 of the address and the ``User-Agent`` under a 32-byte salt drawn at
  start and at 00:00 UTC, in memory only, and the day's counts; it rewrites the day's
  line of ``<data_dir>/hydrolog/stats.jsonl`` every five minutes, at a new day and at
  shutdown, and adds to the line of the day after a restart. The requests of the
  admin panel (:func:`is_admin`, DEV-15.13) count in none of the totals;
  :func:`stats_report` reads the totals back for ``api/admin/stats``.

The client's address is the ASGI ``client`` of the request; behind a proxy, the server
sets it from the proxy's header trusted only from the proxy (uvicorn's
``--proxy-headers`` with ``FORWARDED_ALLOW_IPS``, ``127.0.0.1`` by default).
"""

from __future__ import annotations

import collections
import contextlib
import hashlib
import hmac
import json
import logging
import math
import os
import re
import secrets
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import anyio
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import HTMLResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from hydrolog._settings import (
    config_path,
    gui_addresses,
    load_file,
    operator_table,
    resolve_setting,
)
from hydrolog.gui._terms import Terms, TermsError, load_terms

__all__ = [
    "STATS_FILE",
    "STATS_KEYS",
    "DailyStats",
    "Public",
    "PublicGuard",
    "RateLimiter",
    "Upkeep",
    "is_admin",
    "is_counted",
    "is_page",
    "load_public",
    "read_days",
    "route_path",
    "stats_report",
]

STATS_FILE: Final = "stats.jsonl"
"""The file of the daily totals in ``<data_dir>/hydrolog``."""
STATS_KEYS: Final[tuple[str, ...]] = (
    "visitors",
    "page_views",
    "stations_opened",
    "analyses_run",
    "downloads",
)
"""The totals of a day, in the order of DEV-15.11."""
FLUSH_S: Final = 300.0
"""How often the day's line is rewritten while it changes [s] (DEV-15.11: <= 600)."""

_LOG = logging.getLogger(__name__)
_CATALOG = ("/api/commands", "/api/schemas/")
_READS = frozenset({"GET", "HEAD"})
_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


@dataclass(frozen=True)
class Public:
    """A public deployment of the GUI (``[nogat.operator]`` is set).

    Attributes
    ----------
    operator_email : str or None
        ``[nogat.operator] email``: „Zgłoś uwagę” names it; ``None`` when not a string.
    terms : bytes or None
        The filled ``regulamin.html``; ``None`` when it cannot be filled (the GUI then
        serves no page and no link, DEV-15.7).
    request_limit : int
        Requests of one address in a window.
    request_window_s : int
        The window [s].
    """

    operator_email: str | None
    terms: bytes | None
    request_limit: int
    request_window_s: int


def route_path(scope: Scope) -> str:
    """Return the path below the app's prefix (``/api/run/...``, ``/index.html``)."""
    path = str(scope["path"])
    root = str(scope.get("root_path", ""))
    return path[len(root) :] if root and path.startswith(root) else path


def is_counted(method: str, route: str) -> bool:
    """Tell whether the request limit counts a request (DEV-15.9).

    Every request but static files and the catalog documents: a path under ``/api/``
    other than a read of ``/api/commands…`` or ``/api/schemas/…``, and a page, a path
    that ends with ``/`` or ``.html`` or whose last name has no extension.
    """
    if route.startswith("/api/"):
        return not (method in _READS and route.startswith(_CATALOG))
    name = route.rsplit("/", 1)[-1]
    return "." not in name or name.endswith(".html")


def is_admin(route: str) -> bool:
    """Tell whether a request is the admin panel's (Nogat DEV-15.13).

    ``/admin``, ``/admin/…`` and ``/api/admin/…``: never counted in the daily totals
    (DEV-15.11), always under the request limit (DEV-15.9).
    """
    return route == "/admin" or route.startswith(("/admin/", "/api/admin/"))


def is_page(method: str, route: str) -> bool:
    """Tell whether a request reads a public page (``page_views``).

    The app, its guide, the regulamin; not the admin page, not the API.
    """
    return (
        method in _READS
        and not route.startswith("/api/")
        and not is_admin(route)
        and is_counted(method, route)
    )


class RateLimiter:
    """A window of ``window_s`` per client address, from its first counted request.

    An address that has made ``limit`` requests in its window waits for the window's
    end. Addresses are forgotten as soon as their window ends (the oldest first), so
    one stays in memory for its window only.

    Parameters
    ----------
    limit : int
        Requests of one address in a window.
    window_s : float
        The window [s].
    clock : callable, optional
        Monotonic clock [s]; tests pass their own.
    """

    def __init__(
        self,
        limit: int,
        window_s: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_s = window_s
        self._clock = clock
        # address -> [start, count], in the order of the starts
        self._windows: collections.OrderedDict[str, list[float]] = (
            collections.OrderedDict()
        )

    def purge(self) -> None:
        """Forget the addresses whose window has ended."""
        now = self._clock()
        while self._windows:
            start = next(iter(self._windows.values()))[0]
            if now - start < self.window_s:
                break
            self._windows.popitem(last=False)

    def hit(self, address: str) -> int | None:
        """Count a request of ``address``.

        Returns
        -------
        int or None
            ``None`` when the request is within the limit; else the whole seconds until
            the address's window ends (at least 1), the ``Retry-After``.
        """
        self.purge()
        window = self._windows.get(address)
        if window is None:
            self._windows[address] = [self._clock(), 1]
            return None
        if window[1] >= self.limit:
            left = window[0] + self.window_s - self._clock()
            return max(1, math.ceil(left))
        window[1] += 1
        return None

    def __len__(self) -> int:
        """Return the number of addresses in memory."""
        return len(self._windows)


def _today(now: datetime) -> str:
    return now.astimezone(UTC).date().isoformat()


def read_days(path: Path) -> list[dict[str, Any]]:
    """Return the lines of ``stats.jsonl`` as objects; unusable lines are skipped.

    A missing or unreadable file has no lines.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    entries = []
    for line in text.splitlines():
        with contextlib.suppress(ValueError):
            entry = json.loads(line)
            if isinstance(entry, dict) and isinstance(entry.get("date"), str):
                entries.append(entry)
    return entries


def _total(value: object) -> int:
    """Return a stored total, 0 for a value that is not a whole number >= 0."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return 0


def stats_report(
    path: Path, first: str, last: str, today: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return ``{days, totals}`` of ``GET api/admin/stats`` (Nogat DEV-15.13).

    Parameters
    ----------
    path : Path
        ``<data_dir>/hydrolog/stats.jsonl``.
    first, last : str
        The UTC days ``YYYY-MM-DD`` of the period, both included.
    today : mapping, optional
        The current day as counted so far (:meth:`DailyStats.snapshot`), which
        replaces the file's line of that day.

    Returns
    -------
    dict
        ``days``: one object per day of the file in the period, in date order, with
        the keys of DEV-15.11 (a missing or unusable total is 0); ``totals``: the sum
        of each key but ``visitors``, which is not additive over days.
    """
    entries = {entry["date"]: entry for entry in read_days(path)}
    if today is not None:
        entries[str(today["date"])] = dict(today)
    days = [
        {"date": day, **{key: _total(entries[day].get(key)) for key in STATS_KEYS}}
        for day in sorted(entries)
        if _DAY.fullmatch(day) and first <= day <= last
    ]
    totals = {key: sum(day[key] for day in days) for key in STATS_KEYS[1:]}
    return {"days": days, "totals": totals}


class DailyStats:
    """The day's totals of a public GUI and their file (DEV-15.11).

    Parameters
    ----------
    path : Path
        ``<data_dir>/hydrolog/stats.jsonl``, created with its directory by the first
        write.
    clock : callable, optional
        The current time (aware); tests pass their own.
    """

    def __init__(
        self, path: Path, clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    ) -> None:
        self.path = path
        self._clock = clock
        self._lock = threading.Lock()
        self._day = _today(clock())
        self._salt = secrets.token_bytes(32)
        self._seen: set[bytes] = set()
        self._stored = self._stored_totals(self._day)
        self._counts = dict.fromkeys(STATS_KEYS[1:], 0)
        self._pending: list[dict[str, Any]] = []
        self._dirty = False

    def _stored_totals(self, day: str) -> dict[str, int]:
        """Return the totals the file holds for ``day`` (a restart adds to them)."""
        for entry in self._read():
            if entry.get("date") == day:
                return {
                    key: value
                    for key in STATS_KEYS
                    if isinstance(value := entry.get(key), int)
                    and not isinstance(value, bool)
                }
        return {}

    def _read(self) -> list[dict[str, Any]]:
        return read_days(self.path)

    def _roll(self) -> None:
        """Start a new day at 00:00 UTC: the old one's line is final, a new salt."""
        day = _today(self._clock())
        if day == self._day:
            return
        self._pending.append(self._line())
        self._day = day
        self._salt = secrets.token_bytes(32)
        self._seen = set()
        self._stored = {}
        self._counts = dict.fromkeys(STATS_KEYS[1:], 0)
        self._dirty = True

    def _line(self) -> dict[str, Any]:
        """Return the day's line: the stored totals plus this run's."""
        line: dict[str, Any] = {"date": self._day}
        line["visitors"] = self._stored.get("visitors", 0) + len(self._seen)
        for key in STATS_KEYS[1:]:
            line[key] = self._stored.get(key, 0) + self._counts[key]
        return line

    def visit(self, address: str, user_agent: str) -> None:
        """Count a visitor of a counted request.

        The visitor is the HMAC-SHA-256 of the address and the ``User-Agent`` under
        the day's salt, kept for the day in memory only.
        """
        message = f"{address}\n{user_agent}".encode("utf-8", "replace")
        with self._lock:
            self._roll()
            digest = hmac.new(self._salt, message, hashlib.sha256).digest()
            if digest not in self._seen:
                self._seen.add(digest)
                self._dirty = True

    def count(self, key: str) -> None:
        """Add one to a total other than ``visitors``."""
        if key not in self._counts:
            raise KeyError(key)
        with self._lock:
            self._roll()
            self._counts[key] += 1
            self._dirty = True

    def snapshot(self) -> dict[str, Any]:
        """Return the day's line as it would be written now."""
        with self._lock:
            self._roll()
            return self._line()

    def flush(self) -> None:
        """Rewrite the lines of the days that changed (atomically), in date order.

        A failure is logged and the totals stay for the next try.
        """
        with self._lock:
            self._roll()
            if not self._dirty:
                return
            lines = [*self._pending, self._line()]
            try:
                self._write(lines)
            except OSError:
                _LOG.exception("The daily totals could not be written")
                return
            self._pending = []
            self._dirty = False

    def _write(self, lines: list[dict[str, Any]]) -> None:
        entries = {entry["date"]: entry for entry in self._read()}
        for line in lines:
            entries[line["date"]] = line
        text = "".join(
            json.dumps(entries[day], ensure_ascii=False) + "\n"
            for day in sorted(entries)
        )
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{secrets.token_hex(4)}")
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def due(self, last_flush: float, now: float) -> bool:
        """Tell whether a flush is due.

        A day has ended (10 s after the last flush, so a failing file is not retried
        at every request), or the totals changed and :data:`FLUSH_S` passed since
        ``last_flush`` (both monotonic [s]).
        """
        with self._lock:
            ended = bool(self._pending) or _today(self._clock()) != self._day
            waited = now - last_flush
            return (ended and waited >= 10.0) or (self._dirty and waited >= FLUSH_S)


def _retry_page(seconds: int) -> Response:
    text = f"Zbyt wiele żądań. Spróbuj ponownie za {seconds} s."
    page = (
        '<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Zbyt wiele żądań</title>\n</head>\n<body>\n<p>{text}</p>\n"
        "</body>\n</html>\n"
    )
    return HTMLResponse(page, status_code=429)


class Upkeep:
    """The limit and the totals of a public GUI, and their periodic work.

    Parameters
    ----------
    limiter : RateLimiter
        The limit of each address.
    stats : DailyStats
        The day's totals.
    """

    def __init__(self, limiter: RateLimiter, stats: DailyStats) -> None:
        self.limiter = limiter
        self.stats = stats
        self._last_flush = time.monotonic()

    async def tend(self) -> None:
        """Forget the addresses of ended windows; rewrite the day's totals when due.

        Run after every request and every few seconds by the app's lifespan, so the
        memory and the file follow without traffic too.
        """
        self.limiter.purge()
        now = time.monotonic()
        if self.stats.due(self._last_flush, now):
            self._last_flush = now
            await anyio.to_thread.run_sync(self.stats.flush)


class PublicGuard:
    """The request limit and the visitors of a public GUI.

    The access log is not its own: :class:`hydrolog.gui.nogat_logging.AccessLog`,
    outside it, records its answers too (Nogat DEV-12.8).

    Parameters
    ----------
    app : ASGIApp
        The app below (the security headers, then the routes).
    upkeep : Upkeep
        The limit and the totals.
    refusal : callable
        Makes the ``429`` of an API route from the seconds to wait.
    secure : callable
        Adds the app's security headers to a response this guard answers itself.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        upkeep: Upkeep,
        refusal: Callable[[int], Response],
        secure: Callable[[MutableHeaders, Scope], None],
    ) -> None:
        self.app = app
        self.upkeep = upkeep
        self._refusal = refusal
        self._secure = secure

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = str(scope["method"])
        route = route_path(scope)
        stats = self.upkeep.stats
        status = 0

        async def watched(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        if is_counted(method, route):
            address = str((scope.get("client") or ("",))[0] or "")
            wait = self.upkeep.limiter.hit(address)
            if wait is not None:
                await self._refuse(scope, receive, send, route, wait)
                return
            if not is_admin(route):  # the operator is no visitor (DEV-15.11)
                stats.visit(address, Headers(scope=scope).get("user-agent", ""))
        await self.app(scope, receive, watched)
        if status in (200, 304) and is_page(method, route):
            stats.count("page_views")
        await self.upkeep.tend()

    async def _refuse(
        self, scope: Scope, receive: Receive, send: Send, route: str, wait: int
    ) -> None:
        """Answer ``429``: the error document of an API route, else the Polish page."""
        response = (
            self._refusal(wait) if route.startswith("/api/") else _retry_page(wait)
        )
        response.headers["retry-after"] = str(wait)
        self._secure(response.headers, scope)
        await response(scope, receive, send)


def load_public(file_data: Mapping[str, Any] | None) -> Public | None:
    """Return the public deployment of ``nogat.toml``, ``None`` when it is not one.

    Parameters
    ----------
    file_data : Mapping or None
        The parsed ``nogat.toml``; ``None`` reads the file (``NOGAT_CONFIG`` or the user
        configuration directory).

    Returns
    -------
    Public or None
        ``None`` without ``[nogat.operator]``; else the operator's address, the filled
        regulamin (``None``, with a warning in the log, when a field is missing) and the
        request limit (``request_limit``, ``request_window``: environment,
        ``[hydrolog]``, ``[nogat]``, default 300 in 60 s).
    """
    data = load_file(config_path()) if file_data is None else file_data
    operator = operator_table(file_data=data)
    if operator is None:
        return None
    service_url = (gui_addresses(file_data=data) or {}).get("hydrolog")
    terms: Terms | None
    try:
        terms = load_terms(operator, service_url)
    except TermsError as exc:
        _LOG.warning("No regulamin: %s ([nogat.operator], [nogat] gui.hydrolog)", exc)
        terms = None
    email = operator.get("email")
    return Public(
        operator_email=email.strip()
        if isinstance(email, str) and email.strip()
        else None,
        terms=None if terms is None else terms.page,
        request_limit=int(resolve_setting("request_limit", file_data=data).value),
        request_window_s=int(resolve_setting("request_window", file_data=data).value),
    )
