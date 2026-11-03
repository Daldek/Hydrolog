"""The Starlette app of the GUI: the page and its private API (plan D4 to D8).

The app serves ``web/`` at its root and answers the routes of D5 under ``api/``,
relative to the page, so a host may mount it at any prefix. The routes serve this GUI
only: no ``/api/v1``, no OpenAPI and no stability promise (a deviation from AGI
section 6 recorded in ``CLAUDE.md``). Every error is a ``hydrolog-error/1`` document
with the registry's HTTP status and the Polish ``title``; a run replaced by a newer
one or stopped by the timeout is the ``cancelled`` envelope.

„Zgłoś uwagę” (Nogat plan 2026-11-03, D3): ``POST api/feedback`` stores a report of
a GUI session in ``<data_dir>/hydrolog/feedback.sqlite3``; the admin page
(``admin/``) reads, marks and deletes them through ``api/admin/feedback``, which
answers only the key of ``HYDROLOG_ADMIN_API_KEY`` or ``HYDROLOG_ADMIN_API_KEY_FILE``
in ``X-Admin-Key`` and refuses everything (``401 unauthorized``) when neither is set.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import hashlib
import json
import os
import re
import secrets
import shutil
import weakref
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Final

import anyio
from starlette.applications import Starlette
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import ClientDisconnect, Request
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

import hydrolog
from hydrolog._errors import BY_CODE
from hydrolog._settings import (
    ADMIN_API_KEY,
    ADMIN_API_KEY_FILE,
    TOOL,
    admin_api_key,
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

COOKIE: Final = "hydrolog_gui"
"""The cookie with the session id (HttpOnly, SameSite=Strict, the page's path)."""
EXCLUDED: Final = frozenset({"gui serve", "config show", "commands guide"})
"""Commands the GUI does not offer: a server in the server, server settings, guides."""
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

_API = "/api"
_UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_REFUSED_SITES = frozenset({"cross-site", "same-site"})
_CHANNEL = re.compile(CHANNEL_PATTERN)
_JSON = "application/json"
_PATHS = ["in/<name>", "out/<name>"]


def _route_path(scope: Scope) -> str:
    """Return the path below the app's prefix (``/api/run/...``)."""
    path = str(scope["path"])
    root = str(scope.get("root_path", ""))
    return path[len(root) :] if root and path.startswith(root) else path


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


class _Guard:
    """Security headers of every response and the refusal of cross-site writes (D8).

    ``POST``, ``PUT`` and ``DELETE`` are refused when ``Sec-Fetch-Site`` is
    ``cross-site`` or ``same-site``. Responses under ``api/`` are not stored
    (``no-store``); the page's files are revalidated (``no-cache``).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cache = "no-store" if _route_path(scope).startswith(_API + "/") else "no-cache"
        started = False

        async def guarded(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS:
                    headers[name] = value
                headers["cache-control"] = cache
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


@dataclass
class _Call:
    """What an API request has found out, for its error document and its cookie."""

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
    """The state of one app (limits, sessions, workers, reports) and its handlers."""

    def __init__(
        self,
        *,
        work_root: Path | None,
        workers: int,
        run_timeout_s: float,
        data_dir: Path,
    ) -> None:
        self.limits = Limits()
        self.sessions = Sessions(work_root=work_root, limits=self.limits)
        self.runner = Runner(
            workers=workers, timeout_s=run_timeout_s, cwd=self.sessions.root
        )
        self.reports = FeedbackStore(data_dir / TOOL / FILE_NAME)
        self._finalizer = weakref.finalize(self, _close, self.runner, self.sessions)

    def close(self) -> None:
        """Stop the workers and remove the sessions (once; also at exit)."""
        self._finalizer()

    # --- plumbing -------------------------------------------------------------------

    def endpoint(self, handler: _Handler) -> Callable[[Request], Awaitable[Response]]:
        """Wrap a handler: errors become documents, a new session gets its cookie."""

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
                root = str(request.scope.get("root_path", "")).removesuffix(_API)
                response.set_cookie(
                    COOKIE,
                    call.session.id,
                    path=root.rstrip("/") + "/",
                    secure=request.url.scheme == "https",
                    httponly=True,
                    samesite="strict",
                )
            return response

        return endpoint

    def open_session(self, request: Request, call: _Call) -> Session:
        """Return the request's session, starting one if it has none."""
        session = self.sessions.get(request.cookies.get(COOKIE))
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

    async def session(self, request: Request, call: _Call) -> Response:
        """``GET api/session``: ``hydrolog-gui-session/1``."""
        session = self.open_session(request, call)
        files = await anyio.to_thread.run_sync(session.files)
        limits = {**self.limits.to_dict(), "run_timeout_s": self.runner.timeout_s}
        return JSONResponse(
            {
                "schema": SESSION_SCHEMA,
                "version": hydrolog.__version__,
                "limits": limits,
                "used_bytes": sum(item["size_bytes"] for item in files),
                "files": files,
            }
        )

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
        session = self.sessions.get(request.cookies.get(COOKIE))
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
        """``POST api/feedback``: store a GUI session's report; ``{"id", "status"}``."""
        report = parse_report(await self.options(request, limit=REQUEST_MAX_BYTES))
        self.open_session(request, call)
        user_agent = request.headers.get("user-agent", "")
        number = await anyio.to_thread.run_sync(
            functools.partial(self.reports.add, report, user_agent=user_agent)
        )
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
        """``PATCH api/admin/feedback/{id}`` with ``{"is_read": bool}``."""
        number = request.path_params["feedback_id"]
        is_read = parse_read(await self.options(request, limit=REQUEST_MAX_BYTES))
        found = await anyio.to_thread.run_sync(
            functools.partial(self.reports.set_read, number, is_read=is_read)
        )
        _found(found, number)
        return JSONResponse({"status": "ok"})

    async def feedback_delete(self, request: Request, call: _Call) -> Response:
        """``DELETE api/admin/feedback/{id}``: ``{"status": "deleted"}``."""
        number = request.path_params["feedback_id"]
        found = await anyio.to_thread.run_sync(self.reports.delete, number)
        _found(found, number)
        return JSONResponse({"status": "deleted"})


def _found(found: bool, number: int) -> None:
    """Refuse a report that does not exist (``404``, ``feedback_not_found``)."""
    if not found:
        raise NotFoundError(
            f"Feedback {number} not found",
            details={"reason": "feedback_not_found", "feedback_id": number},
        )


def _close(runner: Runner, sessions: Sessions) -> None:
    runner.close()
    sessions.close()


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
    *, work_root: Path | None, workers: int, run_timeout_s: float, data_dir: Path
) -> Starlette:
    """Build the app; see :func:`hydrolog.gui.create_app`."""
    gui = _Gui(
        work_root=work_root,
        workers=workers,
        run_timeout_s=run_timeout_s,
        data_dir=data_dir,
    )
    report = "/admin/feedback/{feedback_id:int}"
    api = Starlette(
        routes=[
            Route("/session", gui.endpoint(gui.session), methods=["GET"]),
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
        ],
        exception_handlers={HTTPException: _api_http_error, Exception: _api_defect},
    )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        gui.runner.start()
        try:
            yield
        finally:
            await anyio.to_thread.run_sync(gui.close)

    app = Starlette(
        routes=[
            Mount(_API, app=api),
            Mount("/", app=StaticFiles(directory=WEB_DIR, html=True, check_dir=False)),
        ],
        middleware=[Middleware(_Guard)],
        lifespan=lifespan,
    )
    app.state.gui = gui
    return app
