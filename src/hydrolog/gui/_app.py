"""The Starlette app of the GUI: the page and its private API (plan D4 to D8).

The app serves ``web/`` at its root and answers the routes of D5 under ``api/``,
relative to the page, so a host may mount it at any prefix. The routes serve this GUI
only: no ``/api/v1``, no OpenAPI and no stability promise (a deviation from AGI
section 6 recorded in ``CLAUDE.md``). Every error is a ``hydrolog-error/1`` document
with the registry's HTTP status and the Polish ``title``; a run replaced by a newer
one or stopped by the timeout is the ``cancelled`` envelope.

A browser session is named by the header ``X-Hydrolog-Session``, which the page keeps
in its memory only: no cookie (ADR-0034). A request that needs a session and names
none, or an unknown one, starts one, whose id the answer gives in the same header.

„Zgłoś uwagę” (Nogat DEV-15.12): ``POST api/feedback`` stores a report, its text and
the context the page adds, in ``<data_dir>/hydrolog/feedback.sqlite3``. The admin
panel (Nogat DEV-15.13) is Nogat's kit shell at ``admin/`` (``admin`` answers ``308``
to it) on the core API ``api/admin/feedback``, ``api/admin/stats`` and
``api/admin/status``, which answers only the key of ``HYDROLOG_ADMIN_API_KEY`` or
``HYDROLOG_ADMIN_API_KEY_FILE`` in ``X-Admin-Key`` and refuses everything
(``401 unauthorized``) when neither is set; no admin answer is stored
(``Cache-Control: no-store``).

A deployment with ``[nogat.operator]`` in ``nogat.toml`` is public (Nogat DEV-15.7 to
DEV-15.11, :mod:`hydrolog.gui._public`): the app serves ``regulamin.html``, limits the
requests of each address and counts its use in daily totals. Given a
:class:`~hydrolog.gui.nogat_logging.ServerLog`, public or not, it writes the access log
of Nogat DEV-12.4 with :class:`~hydrolog.gui.nogat_logging.AccessLog`, outermost; the
name of a file in ``api/files/<area>/<name>`` is logged as ``[file]`` (DEV-12.5).
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import hashlib
import json
import logging
import mimetypes
import os
import re
import secrets
import shutil
import time
import weakref
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Final, cast

import anyio
from starlette.applications import Starlette
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import ClientDisconnect, Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

import hydrolog
from hydrolog._attribution import provider_lines, retired_lines
from hydrolog._errors import BY_CODE
from hydrolog._settings import (
    ADMIN_API_KEY,
    ADMIN_API_KEY_FILE,
    TOOL,
    admin_api_key,
    gui_addresses,
)
from hydrolog.catalog import command_schema, format_command, get_command, list_commands
from hydrolog.catalog.spec import Command
from hydrolog.exceptions import (
    ERROR_SCHEMA,
    ConflictError,
    ForbiddenPathError,
    HydrologError,
    InvalidParameterError,
    NotFoundError,
    error_document,
)
from hydrolog.gui import WEB_DIR
from hydrolog.gui._admin import status_document
from hydrolog.gui._feedback import (
    FILE_NAME,
    ID_MAX,
    LIST_LIMIT,
    LIST_LIMIT_MAX,
    REQUEST_MAX_BYTES,
    FeedbackStore,
    parse_read,
    parse_report,
)
from hydrolog.gui._public import (
    STATS_FILE,
    DailyStats,
    Public,
    PublicGuard,
    RateLimiter,
    Upkeep,
    is_admin,
    load_public,
    route_path,
    stats_report,
)
from hydrolog.gui._runner import Job, Outcome, Runner
from hydrolog.gui._sessions import (
    NAME_PATTERN,
    Limits,
    Session,
    Sessions,
    check_name,
    relative_paths,
    split_path,
)
from hydrolog.gui.nogat_logging import AccessLog, ServerLog

# The page's own types, whatever the host's registry says: on Windows it may map
# ``.js`` to ``text/plain``, and a browser refuses a module script of that type.
for _suffix, _type in (
    (".js", "text/javascript"),
    (".mjs", "text/javascript"),
    (".css", "text/css"),
):
    mimetypes.add_type(_type, _suffix)

SESSION_HEADER: Final = "X-Hydrolog-Session"
"""The header that names a browser session, both ways (no cookie, ADR-0034)."""
TERMS_PAGE: Final = "regulamin.html"
"""The address of the regulamin beside the page (Nogat DEV-15.7)."""
STATS_EVENTS: Final[Mapping[str, str]] = {
    "station": "stations_opened",
    "download": "downloads",
}
"""What the page counts itself (``POST api/stats/{event}``): event -> daily total."""
STATS_DAYS: Final = 30
"""The days ``api/admin/stats`` gives without ``from`` (Nogat DEV-15.13)."""
EXCLUDED: Final = frozenset(
    {"gui serve", "config show", "commands guide", "commands batch"}
)
"""Commands the GUI does not offer: a server in the server, server settings, guides
and the batch, whose calls would reach the commands left out here."""
SESSION_SCHEMA: Final = "hydrolog-gui-session/1"
FILE_SCHEMA: Final = "hydrolog-gui-file/1"
LINE_SCHEMA: Final = "hydrolog-gui-line/1"
CHANNEL_PATTERN: Final = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"
"""The ``channel`` of a run (``hydrogram``, ``polecenia``...)."""
CONTENT_SECURITY_POLICY: Final = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS: Final[tuple[tuple[str, str], ...]] = (
    ("content-security-policy", CONTENT_SECURITY_POLICY),
    ("x-frame-options", "DENY"),
    ("x-content-type-options", "nosniff"),
    ("referrer-policy", "no-referrer"),
    ("cross-origin-opener-policy", "same-origin"),
    ("cross-origin-resource-policy", "same-origin"),
    ("permissions-policy", "camera=(), microphone=(), geolocation=()"),
)
"""Headers of every response (plan D8); ``Cache-Control`` depends on the path."""
ADMIN_PAGE: Final = "/admin"
"""The admin page's path without its slash, which answers ``308`` to the page."""

_API = "/api"
_UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_REFUSED_SITES = frozenset({"cross-site", "same-site"})
_CHANNEL = re.compile(CHANNEL_PATTERN)
_JSON = "application/json"
_PATHS = ["in/<name>", "out/<name>"]
_LOG = logging.getLogger(__name__)
TEND_S: Final = 10.0
"""How often a public GUI forgets ended windows and rewrites its totals when due [s]."""
QUIET: Final = (
    r"^/(css|src|vendor|nogat)/|^/theme-init\.js$|^/api/(commands|schemas)(/|$)"
)
"""The static content of the access log (Nogat DEV-12.5): the page's files and the
catalog documents, the same for every client, are logged only when answered with 400
or more."""
FILE_PATH: Final = re.compile(r"(/api/files/[^/?]+/)[^?]+")
"""A file's address in the API, whose name the access log writes ``[file]``."""


class _NamelessLog:
    """The server's log as :class:`AccessLog` writes to it, without file names.

    ``PUT api/files/in/<name>`` and the reads and deletions of ``api/files`` name a
    file a visitor uploaded, or a result named after one: the access record keeps the
    area and writes the name ``[file]``, e.g. ``/api/files/in/[file]`` (Nogat
    DEV-12.5). The reference module is copied byte for byte (DEV-12.9), so the path
    is replaced here, between its :class:`AccessLog` and the log.
    """

    def __init__(self, log: ServerLog) -> None:
        self._log = log

    def access(self, *, path: str, **fields: Any) -> None:
        """Write the access record with the file's name replaced."""
        self._log.access(path=FILE_PATH.sub(r"\1[file]", path, count=1), **fields)

    def application(self, *args: Any) -> None:
        """Write an app record as :meth:`ServerLog.application` does."""
        self._log.application(*args)


def _http_status(code: str) -> int:
    """Return the HTTP status of a registry code (503 for the CLI-only outcomes)."""
    status = BY_CODE[code].http_status
    return 503 if status is None else status


def _error_response(document: Mapping[str, Any]) -> JSONResponse:
    return JSONResponse(dict(document), status_code=_http_status(document["code"]))


def _rest_error(
    code: str,
    message: str,
    details: dict[str, Any],
    *,
    hint: str | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Return the error document of a REST code of the registry (no exit code)."""
    entry = BY_CODE[code]
    document: dict[str, Any] = {
        "schema": ERROR_SCHEMA,
        "code": entry.code,
        "title": entry.title_pl,
        "message": message,
    }
    if hint:
        document["hint"] = hint
    document["details"] = details
    document["exit_code"] = entry.exit_code
    return JSONResponse(document, status_code=_http_status(code), headers=headers)


def _admin_refusal(supplied: str | None) -> Response | None:
    """Return the ``401`` of a request without the admin key, ``None`` with it.

    The key is read on every request (a rotated key file applies at once) and
    compared in constant time with the bytes of ``X-Admin-Key``; without a key on the
    server the admin routes refuse every request.
    """
    expected = admin_api_key()
    if expected is None:
        return _rest_error(
            "unauthorized",
            "No admin key is set on the server",
            {"reason": "admin_key_not_configured"},
            hint=f"Start the server with {ADMIN_API_KEY} or {ADMIN_API_KEY_FILE}.",
        )
    if not supplied:
        return _rest_error(
            "unauthorized",
            "The admin API key is missing",
            {"reason": "admin_key_missing"},
            hint="Send it in the X-Admin-Key header.",
        )
    # Starlette decodes a header as Latin-1: these are the bytes the client sent
    if not secrets.compare_digest(supplied.encode("latin-1"), expected.encode("utf-8")):
        return _rest_error(
            "unauthorized",
            "The admin API key is invalid",
            {"reason": "admin_key_invalid"},
            hint="Send the configured key in the X-Admin-Key header.",
        )
    return None


def _query_int(
    request: Request, name: str, default: int, *, minimum: int, maximum: int
) -> int:
    """Return the whole-number query parameter ``name`` within its bounds."""
    text = request.query_params.get(name)
    if text is None:
        return default
    if re.fullmatch(r"-?[0-9]{1,30}", text) is None:
        raise InvalidParameterError(
            f"The parameter {name} must be a whole number, got {text!r}",
            details={
                "parameter": name,
                "reason": "type",
                "expected": "integer",
                "value": text,
            },
        )
    value = int(text)
    for reason, bound, outside in (
        ("minimum", minimum, value < minimum),
        ("maximum", maximum, value > maximum),
    ):
        if outside:
            raise InvalidParameterError(
                f"The parameter {name} must be {'>=' if reason == 'minimum' else '<='}"
                f" {bound}, got {value}",
                details={
                    "parameter": name,
                    "reason": reason,
                    reason: bound,
                    "value": value,
                },
            )
    return value


def _query_day(request: Request, name: str, default: date) -> date:
    """Return the query parameter ``name``, a UTC day ``YYYY-MM-DD``."""
    text = request.query_params.get(name)
    if text is None:
        return default
    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text) is None:
            raise ValueError(text)
        return date.fromisoformat(text)
    except ValueError:
        raise InvalidParameterError(
            f"The parameter {name} must be a day YYYY-MM-DD, got {text!r}",
            details={
                "parameter": name,
                "reason": "format",
                "expected": "YYYY-MM-DD",
                "value": text,
            },
        ) from None


def _is_stored(scope: Scope) -> bool:
    """Tell whether a browser may keep the answer: not the API's, not the admin's."""
    route = route_path(scope)
    return not (route.startswith(_API + "/") or is_admin(route))


def _secure(headers: MutableHeaders, stored: bool) -> None:
    """Set the security headers of every response and its ``Cache-Control`` (D8).

    The page's files are revalidated (``no-cache``); the API's answers and every
    answer of the admin panel are not stored (``no-store``, Nogat DEV-15.13).
    """
    for name, value in SECURITY_HEADERS:
        headers[name] = value
    headers["cache-control"] = "no-cache" if stored else "no-store"


def _secure_request(headers: MutableHeaders, scope: Scope) -> None:
    """:func:`_secure` for the answer to a request no router has seen (a ``429``)."""
    _secure(headers, _is_stored(scope))


class _Guard:
    """Security headers of every response and the refusal of cross-site writes (D8).

    ``POST``, ``PUT`` and ``DELETE`` are refused when ``Sec-Fetch-Site`` is
    ``cross-site`` or ``same-site``. Responses under ``api/`` and of the admin panel
    are not stored (``no-store``); the page's files are revalidated (``no-cache``).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False
        stored = _is_stored(scope)

        async def guarded(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                _secure(MutableHeaders(scope=message), stored)
            await send(message)

        site = Headers(scope=scope).get("sec-fetch-site", "").lower()
        if scope["method"] in _UNSAFE and site in _REFUSED_SITES:
            refused = HydrologError(
                f"A {site} request may not change anything here",
                code="forbidden",
                details={"reason": "cross_site", "sec_fetch_site": site},
            )
            refusal = _error_response(error_document(refused, None, "pl"))
            await refusal(scope, receive, guarded)
            return
        try:
            await self.app(scope, receive, guarded)
        except Exception:
            if not started:  # a defect below that sent nothing
                failure = PlainTextResponse("Internal Server Error", status_code=500)
                await failure(scope, receive, guarded)
            raise


def _rate_limited(wait: int) -> Response:
    """Return the ``429`` of an API route over the request limit (Nogat DEV-15.9)."""
    return _rest_error(
        "rate_limited",
        f"Too many requests from this address; try again in {wait} s",
        {"reason": "rate_limited", "retry_after_s": wait},
        hint=f"Wait {wait} s before the next request.",
    )


@dataclass
class _Call:
    """What an API request has found out, for its error document and its session."""

    command: str | None = None
    session: Session | None = None
    created: bool = False


_Handler = Callable[[Request, _Call], Awaitable[Response]]


async def _disconnected(receive: Receive) -> None:
    """Return when the client has gone away."""
    while (await receive())["type"] != "http.disconnect":
        pass


async def _outcome(request: Request, future: Future[Outcome]) -> Outcome | None:
    """Wait for a run; drop it (``None``) if the client goes away while it waits."""
    result = asyncio.wrap_future(future)
    gone = asyncio.ensure_future(_disconnected(request.receive))
    try:
        await asyncio.wait((result, gone), return_when=asyncio.FIRST_COMPLETED)
    finally:
        gone.cancel()
        if not result.done():
            result.cancel()  # a queued run is dropped; a running one finishes unseen
    if result.cancelled():
        return None
    return result.result()


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _schema_files() -> dict[str, Traversable]:
    folder = resources.files("hydrolog") / "schemas"
    return {
        entry.name: entry
        for entry in folder.iterdir()
        if entry.name.endswith(".schema.json")
    }


def _outside(value: str) -> ForbiddenPathError:
    return ForbiddenPathError(
        f"{value!r} is not a file of the session",
        details={
            "reason": "outside_session",
            "value": value,
            "allowed": _PATHS,
            "pattern": f"^{NAME_PATTERN}$",
        },
    )


def _no_file(shown: str) -> NotFoundError:
    return NotFoundError(
        f"No file {shown!r}", details={"reason": "no_file", "path": shown}
    )


def _too_large(limit: int) -> InvalidParameterError:
    return InvalidParameterError(
        f"The request is larger than {limit} bytes",
        details={"reason": "too_large", "limit_bytes": limit},
    )


def _declared_length(request: Request) -> int | None:
    """Return ``Content-Length``, if the request has one."""
    text = request.headers.get("content-length")
    if text is None:
        return None
    if not text.isdigit():
        raise InvalidParameterError(
            "Content-Length must be a number of bytes",
            details={"reason": "content_length", "value": text},
        )
    return int(text)


def _command(request: Request, call: _Call) -> Command:
    """Return the command of ``{group}/{verb}``; the excluded ones do not exist."""
    name = f"{request.path_params['group']} {request.path_params['verb']}"
    call.command = name
    command = get_command(name)
    if command.name != name or name in EXCLUDED:
        raise NotFoundError(
            f"The command {name!r} is not available in the GUI",
            details={"command": name, "reason": "excluded"},
        )
    return command


class _Gui:
    """The state of one app and its handlers.

    The limits, the sessions, the workers, the reports and the deployment.
    """

    def __init__(
        self,
        *,
        work_root: Path | None,
        workers: int,
        run_timeout_s: float,
        data_dir: Path,
        config: Mapping[str, Any] | None,
    ) -> None:
        self.limits = Limits()
        self.sessions = Sessions(work_root=work_root, limits=self.limits)
        self.runner = Runner(
            workers=workers, timeout_s=run_timeout_s, cwd=self.sessions.root
        )
        self.started_at = datetime.now(UTC)
        self.started = time.monotonic()
        self.data_dir = data_dir / TOOL
        """``<data_dir>/hydrolog``: the reports and the daily totals."""
        self.reports = FeedbackStore(self.data_dir / FILE_NAME)
        self.config = config
        self.public: Public | None = load_public(config)
        self.stats: DailyStats | None = None
        self.upkeep: Upkeep | None = None
        if self.public is not None:
            self.stats = DailyStats(self.data_dir / STATS_FILE)
            limiter = RateLimiter(
                self.public.request_limit, self.public.request_window_s
            )
            self.upkeep = Upkeep(limiter, self.stats)
        self._finalizer = weakref.finalize(
            self, _close, self.runner, self.sessions, self.stats
        )

    def close(self) -> None:
        """Stop the workers, remove the sessions, write the day's totals (once).

        Also run at exit.
        """
        self._finalizer()

    def count(self, total: str) -> None:
        """Add one to a daily total of a public GUI (nothing otherwise)."""
        if self.stats is not None:
            self.stats.count(total)

    # --- plumbing -------------------------------------------------------------------

    def endpoint(self, handler: _Handler) -> Callable[[Request], Awaitable[Response]]:
        """Wrap a handler: errors become documents, a new session gets its header."""

        async def endpoint(request: Request) -> Response:
            call = _Call()
            try:
                response = await handler(request, call)
            except (HydrologError, OSError) as exc:
                document = error_document(exc, call.command, "pl")
                if call.session is not None:
                    document = relative_paths(document, str(call.session.directory))
                response = _error_response(document)
            except ClientDisconnect:  # nobody reads the answer
                response = Response(status_code=400)
            if call.created and call.session is not None:
                response.headers[SESSION_HEADER] = call.session.id
            return response

        return endpoint

    def open_session(self, request: Request, call: _Call) -> Session:
        """Return the request's session, starting one if it names none (or not one).

        A session the server does not know (ended, swept, of a previous run) is no
        session: a new one starts, and the answer names it.
        """
        session = self.sessions.get(request.headers.get(SESSION_HEADER))
        if session is None:
            session = self.sessions.create()
            call.created = True
        call.session = session
        return session

    def admin(self, handler: _Handler) -> _Handler:
        """Wrap a handler of the admin page: it runs only with the admin key."""

        async def admin(request: Request, call: _Call) -> Response:
            refusal = _admin_refusal(request.headers.get("x-admin-key"))
            return refusal if refusal is not None else await handler(request, call)

        return admin

    async def options(
        self, request: Request, *, limit: int | None = None
    ) -> dict[str, Any]:
        """Return the JSON object of the request body: a command's options, a report.

        ``limit`` is the largest body [bytes], by default the 5 MiB of D7.
        """
        media_type = request.headers.get("content-type", "").partition(";")[0]
        if media_type.strip().lower() != _JSON:
            raise InvalidParameterError(
                f"The body must be {_JSON}",
                details={"reason": "content_type", "expected": _JSON},
            )
        if limit is None:
            limit = self.limits.request_bytes
        declared = _declared_length(request)
        if declared is not None and declared > limit:
            raise _too_large(limit)
        chunks: list[bytes] = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit:
                raise _too_large(limit)
            chunks.append(chunk)
        try:
            options = json.loads(b"".join(chunks), parse_constant=_reject_constant)
        except (ValueError, RecursionError) as exc:
            raise InvalidParameterError(
                f"The body is not valid JSON: {exc}", details={"reason": "invalid_json"}
            ) from exc
        if not isinstance(options, dict):
            raise InvalidParameterError(
                "The body must be a JSON object",
                details={"reason": "type", "expected": "object"},
            )
        return options

    def full(self, *, used: int, count: int, adding: int) -> None:
        """Refuse when ``adding`` bytes in one more file break the limits of D7.

        ``used`` and ``count`` are the bytes and files of the session without the
        file being written (a replaced file does not count).
        """
        if used + adding > self.limits.session_bytes:
            raise ConflictError(
                f"The files of this session would exceed "
                f"{self.limits.session_bytes} bytes",
                details={
                    "reason": "session_full",
                    "limit_bytes": self.limits.session_bytes,
                    "used_bytes": used,
                },
                hint="Delete files you no longer need.",
            )
        if count + 1 > self.limits.session_files:
            raise ConflictError(
                f"This session already has {count} files",
                details={
                    "reason": "session_full",
                    "limit_files": self.limits.session_files,
                    "files": count,
                },
                hint="Delete files you no longer need.",
            )

    # --- routes ---------------------------------------------------------------------

    def terms_document(self) -> dict[str, Any]:
        """Return ``terms`` and ``operator_email`` of the deployment.

        ``terms`` is the regulamin's address beside the page, ``None`` when the GUI
        serves none; ``operator_email`` is ``[nogat.operator] email`` of a public
        deployment.
        """
        public = self.public
        return {
            "terms": TERMS_PAGE if public is not None and public.terms else None,
            "operator_email": None if public is None else public.operator_email,
        }

    async def session(self, request: Request, call: _Call) -> Response:
        """``GET api/session``: ``hydrolog-gui-session/1``.

        ``id`` is the session's id, which the page sends back in ``X-Hydrolog-Session``.
        ``gui`` is the deployment's table of GUI addresses (``[nogat] gui`` of
        ``nogat.toml``, read at every request; ``None`` without it), which the page
        gives Nogat's app menu (DEV-15.4, ADR-0027). ``attribution`` is the complete
        lines of each provider Hydrolog knows (``imgw``, ``imgw_hydro``, ``pmaxtp``,
        ``chmi``: ``attribution`` and ``terms_notice``), by which the page names the
        provider of a hand-off that carries no lines of its own (ADR-0028).
        ``retired_lines`` maps each line Nogat retired (ECO-065) to its current line or
        ``None``, by which the page shows a kept depth's or an older hand-off's lines as
        a run would give them (ADR-0036). ``terms`` and ``operator_email`` are those of
        :meth:`terms_document` (Nogat DEV-15.7, DEV-15.12).
        """
        session = self.open_session(request, call)
        files = await anyio.to_thread.run_sync(session.files)
        gui = await anyio.to_thread.run_sync(self.gui_table)
        limits = {**self.limits.to_dict(), "run_timeout_s": self.runner.timeout_s}
        return JSONResponse(
            {
                "schema": SESSION_SCHEMA,
                "version": hydrolog.__version__,
                "id": session.id,
                "limits": limits,
                "used_bytes": sum(item["size_bytes"] for item in files),
                "files": files,
                "gui": gui,
                "attribution": provider_lines(),
                "retired_lines": retired_lines(),
                **self.terms_document(),
            }
        )

    def gui_table(self) -> dict[str, str] | None:
        """Return ``[nogat] gui`` of the app's settings, else of the file now."""
        return gui_addresses(file_data=self.config)

    async def end_session(self, request: Request, call: _Call) -> Response:
        """``DELETE api/session``: ``204``; the session and its files are deleted.

        The page sends it when it is closed or reloaded, so the files it gave stay
        on the server only while it is open (Nogat regulamin § 8 ust. 7).
        """
        session = self.sessions.get(request.headers.get(SESSION_HEADER))
        if session is not None and not session.busy:
            await anyio.to_thread.run_sync(self.sessions.remove, session)
        return Response(status_code=204)

    async def terms(self, request: Request, call: _Call) -> Response:
        """``GET api/terms``: ``{"terms", "operator_email"}`` for the guide's footer."""
        return JSONResponse(self.terms_document())

    async def stats_event(self, request: Request, call: _Call) -> Response:
        """``POST api/stats/{event}``: ``204``, one more of a daily total.

        ``station``: a station's series the page opened; ``download``: a file it
        saved. Nothing is counted when the GUI is not public.
        """
        event = request.path_params["event"]
        total = STATS_EVENTS.get(event)
        if total is None:
            raise NotFoundError(
                f"No total {event!r}",
                details={
                    "reason": "no_total",
                    "value": event,
                    "allowed": [*STATS_EVENTS],
                },
            )
        self.count(total)
        return Response(status_code=204)

    async def commands(self, request: Request, call: _Call) -> Response:
        """``GET api/commands``: the command list without the excluded commands."""
        document = list_commands().to_dict()
        document["commands"] = [
            entry for entry in document["commands"] if entry["name"] not in EXCLUDED
        ]
        return JSONResponse(document)

    async def describe(self, request: Request, call: _Call) -> Response:
        """``GET api/commands/{group}/{verb}``: ``hydrolog-commands/1``."""
        return JSONResponse(command_schema(_command(request, call)).to_dict())

    async def schema(self, request: Request, call: _Call) -> Response:
        """``GET api/schemas/{file}``: a JSON Schema of the package."""
        name = request.path_params["file"]
        entry = _schema_files().get(name)
        if entry is None:
            raise NotFoundError(
                f"No schema {name!r}", details={"reason": "no_schema", "value": name}
            )
        return Response(entry.read_bytes(), media_type=_JSON)

    async def run(self, request: Request, call: _Call) -> Response:
        """``POST api/run/{group}/{verb}?channel=...&check=true``: the envelope."""
        command = _command(request, call)
        channel = request.query_params.get("channel")
        if channel is not None and _CHANNEL.fullmatch(channel) is None:
            raise InvalidParameterError(
                f"The channel {channel!r} does not match {CHANNEL_PATTERN}",
                details={
                    "parameter": "channel",
                    "reason": "pattern",
                    "value": channel,
                    "pattern": f"^{CHANNEL_PATTERN}$",
                },
            )
        check = request.query_params.get("check", "false")
        if check not in ("true", "false"):
            raise InvalidParameterError(
                f"The parameter check must be true or false, got {check!r}",
                details={
                    "parameter": "check",
                    "reason": "choice",
                    "allowed": ["true", "false"],
                    "value": check,
                },
            )
        options = await self.options(request)
        session = self.open_session(request, call)
        with session.use():
            resolved = session.command_options(command, options)
            writes = any(
                option.path_role == "output" and option.name in resolved
                for option in command.options
            )
            if writes and check == "false":  # a full session takes no more output
                used, count = await anyio.to_thread.run_sync(session.usage)
                self.full(used=used, count=count, adding=1)
            job = Job(command.name, resolved, str(session.directory), check == "true")
            key = None if channel is None else (session.id, channel)
            outcome = await _outcome(request, self.runner.submit(job, channel=key))
        if outcome is None:  # the browser went away; nobody reads this
            return Response(status_code=400)
        if outcome.error:
            return _error_response(outcome.document)
        if check == "false" and outcome.document.get("status") == "ok":
            self.count("analyses_run")
        return JSONResponse(outcome.document)

    async def line(self, request: Request, call: _Call) -> Response:
        """``POST api/format/{group}/{verb}``: the CLI line, ``hydrolog-gui-line/1``."""
        command = _command(request, call)
        shown = await self.options(request)
        for option in command.options:
            value = shown.get(option.name)
            if option.type == "path" and isinstance(value, str):
                split = split_path(value)
                if split is not None:
                    shown[option.name] = split[1][-1]  # in/x.csv is shown as x.csv
        line = format_command(command.name, shown)
        return JSONResponse({"schema": LINE_SCHEMA, "line": line})

    async def upload(self, request: Request, call: _Call) -> Response:
        """``PUT api/files/in/{name}``: ``201`` and ``hydrolog-gui-file/1``."""
        name = request.path_params["name"]
        if not check_name(name):
            raise _outside(f"in/{name}")
        session = self.open_session(request, call)
        limit = self.limits.file_bytes
        declared = _declared_length(request)
        if declared is not None and declared > limit:
            raise _too_large(limit)
        target = session.path("in", (name,))
        with session.use():
            used, count = await anyio.to_thread.run_sync(session.usage)
            if target.is_file():  # the file it replaces does not count
                used -= target.stat().st_size
                count -= 1
            self.full(used=used, count=count, adding=declared or 0)
            temporary = target.with_name(f".upload-{secrets.token_hex(8)}")
            digest = hashlib.sha256()
            size = 0
            try:
                with temporary.open("xb") as stream:
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > limit:
                            raise _too_large(limit)
                        self.full(used=used, count=count, adding=size)
                        stream.write(chunk)
                        digest.update(chunk)
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return JSONResponse(
            {
                "schema": FILE_SCHEMA,
                "path": f"in/{name}",
                "size_bytes": size,
                "sha256": digest.hexdigest(),
            },
            status_code=201,
        )

    async def file(self, request: Request, call: _Call) -> Response:
        """``GET`` (the bytes as an attachment) or ``DELETE`` (``204``) of a file."""
        value = f"{request.path_params['area']}/{request.path_params['name']}"
        split = split_path(value)
        if split is None:
            raise _outside(value)
        session = self.sessions.get(request.headers.get(SESSION_HEADER))
        if session is None:
            raise _no_file(value)
        call.session = session
        path = session.path(*split)
        if request.method == "DELETE":
            if path.is_dir() and not path.is_symlink():
                await anyio.to_thread.run_sync(shutil.rmtree, path)
            elif path.is_file() or path.is_symlink():
                path.unlink()
            else:
                raise _no_file(value)
            return Response(status_code=204)
        if not path.is_file() or path.is_symlink():
            raise _no_file(value)
        return FileResponse(path, filename=path.name)

    # --- „Zgłoś uwagę” and the admin page -------------------------------------------

    async def feedback(self, request: Request, call: _Call) -> Response:
        """``POST api/feedback``: store a report; ``{"id", "status"}``.

        The body is ``{"message", "context"}`` and nothing else (Nogat DEV-15.12).
        """
        report = parse_report(
            await self.options(request, limit=REQUEST_MAX_BYTES),
            app_version=hydrolog.__version__,
        )
        number = await anyio.to_thread.run_sync(self.reports.add, report)
        return JSONResponse({"id": number, "status": "ok"})

    async def feedback_list(self, request: Request, call: _Call) -> Response:
        """``GET api/admin/feedback?limit=50&offset=0``: a page, newest first.

        The answer is ``{"items", "total", "unread_count"}``; ``limit`` is 1 to 200.
        """
        limit = _query_int(
            request, "limit", LIST_LIMIT, minimum=1, maximum=LIST_LIMIT_MAX
        )
        offset = _query_int(request, "offset", 0, minimum=0, maximum=ID_MAX)
        listing = await anyio.to_thread.run_sync(
            functools.partial(self.reports.listing, limit=limit, offset=offset)
        )
        return JSONResponse(listing)

    async def feedback_mark(self, request: Request, call: _Call) -> Response:
        """``PATCH api/admin/feedback/{id}`` with ``{"is_read": bool}``: the report."""
        number = request.path_params["feedback_id"]
        is_read = parse_read(await self.options(request, limit=REQUEST_MAX_BYTES))
        report = await anyio.to_thread.run_sync(
            functools.partial(self.reports.set_read, number, is_read=is_read)
        )
        if report is None:
            raise _missing(number)
        return JSONResponse(report)

    async def feedback_delete(self, request: Request, call: _Call) -> Response:
        """``DELETE api/admin/feedback/{id}``: ``{"status": "deleted"}``."""
        number = request.path_params["feedback_id"]
        if not await anyio.to_thread.run_sync(self.reports.delete, number):
            raise _missing(number)
        return JSONResponse({"status": "deleted"})

    async def admin_stats(self, request: Request, call: _Call) -> Response:
        """``GET api/admin/stats?from=&to=``: ``{days, totals}`` (Nogat DEV-15.13).

        The days of ``stats.jsonl`` from ``from`` to ``to``, UTC days ``YYYY-MM-DD``
        both included: by default the last :data:`STATS_DAYS` up to today, the
        current day as counted so far. A GUI that is not public counts nothing, but
        gives the lines a public run left.
        """
        last = _query_day(request, "to", datetime.now(UTC).date())
        first = _query_day(request, "from", last - timedelta(days=STATS_DAYS - 1))
        if first > last:
            raise InvalidParameterError(
                f"The day from ({first}) is after the day to ({last})",
                details={
                    "parameter": "from",
                    "reason": "maximum",
                    "maximum": last.isoformat(),
                    "value": first.isoformat(),
                },
            )
        today = None if self.stats is None else self.stats.snapshot()
        report = await anyio.to_thread.run_sync(
            stats_report,
            self.data_dir / STATS_FILE,
            first.isoformat(),
            last.isoformat(),
            today,
        )
        return JSONResponse(report)

    async def admin_status(self, request: Request, call: _Call) -> Response:
        """``GET api/admin/status``: the server and its checks (Nogat DEV-15.13).

        The checks are ``data_dir`` and ``feedback_db``
        (:mod:`hydrolog.gui._admin`).
        """
        document = await anyio.to_thread.run_sync(
            functools.partial(
                status_document,
                version=hydrolog.__version__,
                started_at=self.started_at,
                uptime_s=time.monotonic() - self.started,
                data_dir=self.data_dir,
                reports=self.reports,
            )
        )
        return JSONResponse(document)


def _missing(number: int) -> NotFoundError:
    """Return the ``404`` of a report that does not exist (``feedback_not_found``)."""
    return NotFoundError(
        f"Feedback {number} not found",
        details={"reason": "feedback_not_found", "feedback_id": number},
    )


def _close(runner: Runner, sessions: Sessions, stats: DailyStats | None) -> None:
    runner.close()
    sessions.close()
    if stats is not None:
        stats.flush()


async def _api_http_error(request: Request, exc: Exception) -> Response:
    """Turn the router's 404 and 405 under ``api/`` into error documents."""
    assert isinstance(exc, HTTPException)
    if exc.status_code == 405:
        return _rest_error(
            "method_not_allowed",
            f"The method {request.method} is not allowed here",
            {"reason": "method", "method": request.method},
            headers=exc.headers,
        )
    missing = NotFoundError(
        f"No API route {request.url.path!r}", details={"reason": "no_route"}
    )
    return _error_response(error_document(missing, None, "pl"))


async def _api_defect(request: Request, exc: Exception) -> Response:
    """Turn a defect under ``api/`` into ``internal_error``."""
    return _error_response(error_document(exc, None, "pl"))


def build_app(
    *,
    work_root: Path | None,
    workers: int,
    run_timeout_s: float,
    data_dir: Path,
    config: Mapping[str, Any] | None = None,
    log: ServerLog | None = None,
) -> Starlette:
    """Build the app; see :func:`hydrolog.gui.create_app`."""
    gui = _Gui(
        work_root=work_root,
        workers=workers,
        run_timeout_s=run_timeout_s,
        data_dir=data_dir,
        config=config,
    )
    report = "/admin/feedback/{feedback_id:int}"
    api = Starlette(
        routes=[
            Route("/session", gui.endpoint(gui.session), methods=["GET"]),
            Route("/session", gui.endpoint(gui.end_session), methods=["DELETE"]),
            Route("/terms", gui.endpoint(gui.terms), methods=["GET"]),
            Route("/stats/{event}", gui.endpoint(gui.stats_event), methods=["POST"]),
            Route("/commands", gui.endpoint(gui.commands), methods=["GET"]),
            Route(
                "/commands/{group}/{verb}", gui.endpoint(gui.describe), methods=["GET"]
            ),
            Route("/schemas/{file}", gui.endpoint(gui.schema), methods=["GET"]),
            Route("/run/{group}/{verb}", gui.endpoint(gui.run), methods=["POST"]),
            Route("/format/{group}/{verb}", gui.endpoint(gui.line), methods=["POST"]),
            Route("/files/in/{name}", gui.endpoint(gui.upload), methods=["PUT"]),
            Route(
                "/files/{area}/{name:path}",
                gui.endpoint(gui.file),
                methods=["GET", "DELETE"],
            ),
            Route("/feedback", gui.endpoint(gui.feedback), methods=["POST"]),
            Route(
                "/admin/feedback",
                gui.endpoint(gui.admin(gui.feedback_list)),
                methods=["GET"],
            ),
            Route(
                report, gui.endpoint(gui.admin(gui.feedback_mark)), methods=["PATCH"]
            ),
            Route(
                report,
                gui.endpoint(gui.admin(gui.feedback_delete)),
                methods=["DELETE"],
            ),
            Route(
                "/admin/stats",
                gui.endpoint(gui.admin(gui.admin_stats)),
                methods=["GET"],
            ),
            Route(
                "/admin/status",
                gui.endpoint(gui.admin(gui.admin_status)),
                methods=["GET"],
            ),
        ],
        exception_handlers={HTTPException: _api_http_error, Exception: _api_defect},
    )

    async def admin_page(request: Request) -> Response:
        """``admin``: ``308`` to ``admin/``, the panel (Nogat DEV-15.13).

        The address is relative, so it holds under a host's prefix.
        """
        query = request.url.query
        target = "admin/" + (f"?{query}" if query else "")
        return RedirectResponse(target, status_code=308)

    async def regulamin(request: Request) -> Response:
        """``regulamin.html``: the filled regulamin of a public deployment, else 404."""
        page = None if gui.public is None else gui.public.terms
        if page is None:
            return PlainTextResponse("Not Found", status_code=404)
        return HTMLResponse(page)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        gui.runner.start()
        tending = None
        if gui.upkeep is not None:
            tending = asyncio.ensure_future(_tend(gui.upkeep))
        try:
            yield
        finally:
            if tending is not None:
                tending.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await tending
            await anyio.to_thread.run_sync(gui.close)

    middleware = [Middleware(_Guard)]
    if gui.upkeep is not None:
        middleware.insert(
            0,
            Middleware(
                PublicGuard,
                upkeep=gui.upkeep,
                refusal=_rate_limited,
                secure=_secure_request,
            ),
        )
    if log is not None:
        nameless = cast(ServerLog, _NamelessLog(log))
        middleware.insert(0, Middleware(AccessLog, log=nameless, quiet=QUIET))
    app = Starlette(
        routes=[
            Route(f"/{TERMS_PAGE}", regulamin, methods=["GET"]),
            Route(ADMIN_PAGE, admin_page, methods=["GET"]),
            Mount(_API, app=api),
            Mount("/", app=StaticFiles(directory=WEB_DIR, html=True, check_dir=False)),
        ],
        middleware=middleware,
        lifespan=lifespan,
    )
    app.state.gui = gui
    return app


async def _tend(upkeep: Upkeep) -> None:
    """Tend the limit and the totals every :data:`TEND_S` seconds until cancelled."""
    while True:
        await asyncio.sleep(TEND_S)
        try:
            await upkeep.tend()
        except Exception:  # the next round tries again
            _LOG.exception("The upkeep of the public GUI failed")
