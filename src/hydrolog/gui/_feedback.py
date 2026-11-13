"""The reports of the GUI's users, „Zgłoś uwagę” (Nogat DEV-15.12, ECO-062).

A report is the text a person wrote (1 to 5000 characters) and the context the page
adds itself: ``view`` (the section and its route), ``station`` (``null`` without one),
``parameters`` (the view's inputs) and ``app_version`` (the server's version, whatever
the page says), a JSON object of at most 100 000 bytes of compact UTF-8. Nothing else:
no contact field, no address of the page, no ``User-Agent``, no IP address; a body with
any other field, at the top or in the context, is refused (``unknown_field``). The
reports live in the SQLite file ``<data_dir>/hydrolog/feedback.sqlite3`` (DEV-18.2),
which the first report creates with its directory (mode 0700, the file 0600); reading
creates nothing. The file is in WAL mode with a busy timeout and ``secure_delete``, so a
deleted report leaves no text in the file, and one process works on it one call at a
time, so concurrent requests, and other processes on the same file, are safe.

The table ``feedback`` holds ``id``, ``created_at`` (UTC, ``2026-11-03T10:15:00Z``),
``message``, ``context`` (JSON text) and ``is_read`` (0 or 1), with the limits as
``CHECK`` constraints; ``PRAGMA user_version`` is 2. A file of version 1 (the form with
a contact, the page's address, the browser and diagnostics) is copied whole to
``feedback-v1-<UTC time>.sqlite3`` beside it, for the operator to decide on, before its
reports are moved to version 2 with the context their address and diagnostics give
(``view``, ``parameters``) and the rest dropped from the file.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
from collections.abc import Iterator, Mapping
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

from hydrolog.exceptions import HydrologError, InvalidParameterError

__all__ = [
    "APP_VERSION_MAX",
    "CONTEXT_KEYS",
    "CONTEXT_MAX_BYTES",
    "FILE_NAME",
    "LIST_LIMIT",
    "LIST_LIMIT_MAX",
    "MESSAGE_MAX",
    "REQUEST_MAX_BYTES",
    "STATION_MAX",
    "VIEW_MAX",
    "FeedbackStore",
    "Report",
    "parse_read",
    "parse_report",
]

_LOG = logging.getLogger(__name__)

FILE_NAME: Final = "feedback.sqlite3"
"""The file of the reports in ``<data_dir>/hydrolog``."""
VERSION: Final = 2
"""``PRAGMA user_version`` of the file."""
MESSAGE_MAX: Final = 5000
VIEW_MAX: Final = 200
STATION_MAX: Final = 200
APP_VERSION_MAX: Final = 50
CONTEXT_MAX_BYTES: Final = 100_000
"""The largest context: its compact JSON in UTF-8 [bytes]."""
CONTEXT_KEYS: Final[tuple[str, ...]] = ("view", "station", "parameters", "app_version")
"""The fields of a context (DEV-15.12), in the order they are stored."""
BODY_KEYS: Final = frozenset({"message", "context"})
"""The fields of the body of ``POST api/feedback``; any other is refused."""
REQUEST_MAX_BYTES: Final = 256 * 1024
"""The largest body of a request of these routes [bytes]."""
LIST_LIMIT: Final = 50
LIST_LIMIT_MAX: Final = 200
ID_MAX: Final = 2**63 - 1
"""The largest id SQLite can hold; a larger one is no report."""
TIMEOUT_S: Final = 10.0
"""How long a call waits for another process's lock on the file [s]."""

_SURROGATE = re.compile("[\ud800-\udfff]")
_TABLE: Final = f"""
CREATE TABLE IF NOT EXISTS {{name}} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(message) BETWEEN 1 AND {MESSAGE_MAX}),
    context TEXT NOT NULL CHECK (
        json_valid(context)
        AND json_type(context) = 'object'
        AND length(CAST(context AS BLOB)) <= {CONTEXT_MAX_BYTES}
    ),
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1))
);
"""
_INDEX: Final = (
    "CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback (created_at DESC);"
)
_SCHEMA: Final = (
    _TABLE.format(name="feedback") + _INDEX + f"\nPRAGMA user_version = {VERSION};\n"
)
_COLUMNS: Final = ("id", "created_at", "message", "context", "is_read")


@dataclass(frozen=True)
class Report:
    """A checked report, ready to store.

    Attributes
    ----------
    message : str
        What the person wrote, 1 to 5000 characters.
    context : str
        The context as compact JSON text, at most 100 000 bytes: ``view``, ``station``,
        ``parameters``, ``app_version``.
    """

    message: str
    context: str


def _clean(text: str) -> str:
    """Replace lone surrogates, which UTF-8 cannot hold, with U+FFFD."""
    return _SURROGATE.sub("\ufffd", text)


def _invalid(name: str, reason: str, message: str, **details: Any) -> HydrologError:
    return InvalidParameterError(
        message, details={"parameter": name, "reason": reason, **details}
    )


def _unknown(body: Mapping[str, Any], allowed: frozenset[str], prefix: str) -> None:
    """Refuse a field outside ``allowed``: the form has no other (no contact)."""
    for name in body:
        if name not in allowed:
            shown = f"{prefix}{name}"
            raise _invalid(
                shown,
                "unknown_field",
                f"The field {shown!r} is not accepted: a report holds only its text "
                "and the context the page adds",
                allowed=sorted(f"{prefix}{key}" for key in allowed),
            )


def _text(
    body: Mapping[str, Any],
    name: str,
    maximum: int,
    *,
    shown: str | None = None,
    required: bool = False,
    nullable: bool = False,
) -> str | None:
    """Return the text ``name`` of the body, checked against its limit."""
    shown = shown or name
    value = body.get(name)
    if value is None:
        if required and not nullable:
            raise _invalid(shown, "required", f"The field {shown!r} is required")
        return None
    if not isinstance(value, str):
        raise _invalid(
            shown, "type", f"The field {shown!r} must be a string", expected="string"
        )
    if required and not nullable and not value:
        raise _invalid(shown, "empty", f"The field {shown!r} must not be empty")
    if len(value) > maximum:
        raise _invalid(
            shown,
            "too_long",
            f"The field {shown!r} has {len(value)} characters, at most {maximum}",
            max_length=maximum,
            length=len(value),
        )
    return _clean(value)


def _context(value: object, app_version: str) -> str:
    """Return the checked context as compact JSON text, ``app_version`` the server's."""
    if not isinstance(value, dict):
        raise _invalid(
            "context",
            "required" if value is None else "type",
            "The field 'context' must be a JSON object",
            expected="object",
        )
    _unknown(value, frozenset(CONTEXT_KEYS), "context.")
    view = _text(value, "view", VIEW_MAX, shown="context.view", required=True)
    station = _text(value, "station", STATION_MAX, shown="context.station")
    _text(value, "app_version", APP_VERSION_MAX, shown="context.app_version")
    parameters = value.get("parameters", {})
    if not isinstance(parameters, dict):
        raise _invalid(
            "context.parameters",
            "type",
            "The field 'context.parameters' must be a JSON object",
            expected="object",
        )
    context = {
        "view": view,
        "station": station,
        "parameters": parameters,
        "app_version": app_version,
    }
    try:
        text = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    except (ValueError, RecursionError) as exc:
        raise _invalid(
            "context", "invalid_json", f"The context is not JSON: {exc}"
        ) from exc
    text = _clean(text)
    size = len(text.encode("utf-8"))
    if size > CONTEXT_MAX_BYTES:
        raise _invalid(
            "context",
            "too_large",
            f"The context has {size} bytes, at most {CONTEXT_MAX_BYTES}",
            limit_bytes=CONTEXT_MAX_BYTES,
            size_bytes=size,
        )
    return text


def parse_report(body: Mapping[str, Any], *, app_version: str) -> Report:
    """Check the body of ``POST api/feedback`` (Nogat DEV-15.12).

    Parameters
    ----------
    body : Mapping
        The JSON object: ``message`` (required) and ``context`` (required: ``view``,
        ``station``, ``parameters``, ``app_version``); no other field.
    app_version : str
        The server's version, stored as the context's ``app_version``.

    Returns
    -------
    Report
        The report, lone surrogates replaced with U+FFFD.

    Raises
    ------
    InvalidParameterError
        ``details.parameter`` names the field (``context.view`` inside the context),
        ``details.reason`` is ``unknown_field`` (a contact, the page's address, the
        browser or any other field), ``required``, ``type``, ``empty``, ``too_long``
        (``max_length``) or ``too_large`` (``limit_bytes``).
    """
    _unknown(body, BODY_KEYS, "")
    message = _text(body, "message", MESSAGE_MAX, required=True)
    assert message is not None
    return Report(message=message, context=_context(body.get("context"), app_version))


def parse_read(body: Mapping[str, Any]) -> bool:
    """Return ``is_read`` of the body of ``PATCH api/admin/feedback/{id}``.

    Parameters
    ----------
    body : Mapping
        The JSON object ``{"is_read": true}`` or ``{"is_read": false}``.

    Returns
    -------
    bool
        The new read flag.

    Raises
    ------
    InvalidParameterError
        If ``is_read`` is missing (``required``) or not a JSON boolean (``type``).
    """
    if "is_read" not in body:
        raise _invalid("is_read", "required", "The field 'is_read' is required")
    value = body["is_read"]
    if not isinstance(value, bool):
        raise _invalid(
            "is_read",
            "type",
            "The field 'is_read' must be true or false",
            expected="boolean",
        )
    return value


def _failure(reason: str, message: str, hint: str | None = None) -> HydrologError:
    """Log a failed call on the file; return its ``io_error``, without the path."""
    _LOG.exception("%s", message)
    return HydrologError(
        message, code="io_error", details={"reason": reason}, hint=hint
    )


def _item(row: tuple[Any, ...]) -> dict[str, Any]:
    item = dict(zip(_COLUMNS, row, strict=True))
    item["context"] = json.loads(item["context"])
    item["is_read"] = bool(item["is_read"])
    return item


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _old_context(page_url: object, diagnostics: object) -> str:
    """Return the context of a report of version 1: its view and inputs.

    The view is the section and route of its diagnostics, else the fragment of its
    page's address; the parameters are the inputs of its diagnostics. The contact, the
    address itself, the browser, the environment and the events are not kept.
    """
    view = ""
    parameters: Any = {}
    try:
        recorded = json.loads(diagnostics) if isinstance(diagnostics, str) else None
    except ValueError:
        recorded = None
    workspace = recorded.get("workspace") if isinstance(recorded, dict) else None
    if isinstance(workspace, dict):
        section = workspace.get("section")
        path = workspace.get("path")
        if isinstance(section, str):
            parts = [section]
            if isinstance(path, list):
                parts += [part for part in path if isinstance(part, str)]
            view = "/".join(parts)
        if isinstance(workspace.get("inputs"), dict):
            parameters = workspace["inputs"]
    if not view and isinstance(page_url, str):
        view = urlsplit(page_url).fragment
    context = {
        "view": view[:VIEW_MAX],
        "station": None,
        "parameters": parameters,
        "app_version": None,
    }
    text = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    if len(text.encode("utf-8")) > CONTEXT_MAX_BYTES:
        context["parameters"] = {}
        text = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    return _clean(text)


class FeedbackStore:
    """The reports in one SQLite file, created by the first report.

    Parameters
    ----------
    path : Path
        The file, ``<data_dir>/hydrolog/feedback.sqlite3``.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._ready = False

    @contextmanager
    def _connection(self, *, create: bool) -> Iterator[sqlite3.Connection | None]:
        """Yield a connection in autocommit mode, one call at a time in this process.

        Without the file, ``create`` makes it (and its directory) and the table;
        otherwise it yields ``None``. A file of version 1 is moved to version 2 first.
        """
        with self._lock:
            if not self.path.is_file():
                if not create:
                    yield None
                    return
                self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.close(os.open(self.path, os.O_WRONLY | os.O_CREAT, 0o600))
                self._ready = False
            connection = sqlite3.connect(
                self.path, timeout=TIMEOUT_S, isolation_level=None
            )
            with closing(connection):
                connection.execute("PRAGMA secure_delete = ON")
                if not self._ready:
                    connection.execute("PRAGMA journal_mode = WAL")
                    version = connection.execute("PRAGMA user_version").fetchone()[0]
                    if version == 0:
                        connection.executescript(_SCHEMA)
                    elif version == 1:
                        self._migrate(connection)
                    self._ready = True
                yield connection

    def _migrate(self, connection: sqlite3.Connection) -> None:
        """Move a file of version 1 to version 2, after a whole copy beside it."""
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        copy = self.path.with_name(f"feedback-v1-{stamp}.sqlite3")
        os.close(os.open(copy, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        with closing(sqlite3.connect(copy)) as target:
            connection.backup(target)
        rows = connection.execute(
            "SELECT id, created_at, message, page_url, diagnostics, is_read"
            " FROM feedback ORDER BY id"
        ).fetchall()
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(_TABLE.format(name="feedback_v2"))
            connection.executemany(
                "INSERT INTO feedback_v2 (id, created_at, message, context, is_read)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (number, created, message, _old_context(page, recorded), read)
                    for number, created, message, page, recorded, read in rows
                ],
            )
            # The ids of deleted reports are not given again: the new table takes on
            # the old one's AUTOINCREMENT counter
            connection.execute(
                "UPDATE sqlite_sequence SET seq = (SELECT seq FROM sqlite_sequence"
                " WHERE name = 'feedback') WHERE name = 'feedback_v2' AND seq <"
                " (SELECT seq FROM sqlite_sequence WHERE name = 'feedback')"
            )
            connection.execute(
                "INSERT INTO sqlite_sequence (name, seq) SELECT 'feedback_v2', seq"
                " FROM sqlite_sequence WHERE name = 'feedback' AND NOT EXISTS"
                " (SELECT 1 FROM sqlite_sequence WHERE name = 'feedback_v2')"
            )
            connection.execute("DROP TABLE feedback")
            connection.execute("ALTER TABLE feedback_v2 RENAME TO feedback")
            connection.execute(_INDEX)
            connection.execute(f"PRAGMA user_version = {VERSION}")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        connection.execute("COMMIT")
        connection.execute("VACUUM")  # no page of the old table stays in the file
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        _LOG.warning(
            "Moved %d feedback reports to version %d; the previous file, with its "
            "contacts, addresses, browsers and diagnostics, is kept as %s for the "
            "operator to decide on",
            len(rows),
            VERSION,
            copy.name,
        )

    def add(self, report: Report) -> int:
        """Store a report; return its id.

        Parameters
        ----------
        report : Report
            The checked report.

        Returns
        -------
        int
            The id of the new report.

        Raises
        ------
        HydrologError
            ``io_error`` (``feedback_store_failed``) if the file cannot be written.
        """
        try:
            with self._connection(create=True) as connection:
                assert connection is not None
                cursor = connection.execute(
                    "INSERT INTO feedback (created_at, message, context)"
                    " VALUES (?, ?, ?)",
                    (_now(), report.message, report.context),
                )
                number = cursor.lastrowid
        except (OSError, sqlite3.Error) as exc:
            raise _failure(
                "feedback_store_failed",
                "The feedback could not be stored",
                "Try again later.",
            ) from exc
        assert number is not None
        _LOG.info("Stored the feedback report %d", number)
        return number

    def listing(self, *, limit: int, offset: int) -> dict[str, Any]:
        """Return a page of the reports, newest first, with the counts.

        Parameters
        ----------
        limit : int
            The most reports to return.
        offset : int
            How many of the newest reports to skip.

        Returns
        -------
        dict
            ``{"items", "total", "unread_count"}``; an item has ``id``,
            ``created_at``, ``message``, ``context`` (an object) and ``is_read``.

        Raises
        ------
        HydrologError
            ``io_error`` (``feedback_list_failed``) if the file cannot be read.
        """
        try:
            with self._connection(create=False) as connection:
                if connection is None:
                    return {"items": [], "total": 0, "unread_count": 0}
                connection.execute("BEGIN")
                try:
                    rows = connection.execute(
                        f"SELECT {', '.join(_COLUMNS)} FROM feedback"
                        " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                        (limit, offset),
                    ).fetchall()
                    total, unread = connection.execute(
                        "SELECT COUNT(*), COALESCE(SUM(is_read = 0), 0) FROM feedback"
                    ).fetchone()
                finally:
                    connection.execute("COMMIT")
                items = [_item(row) for row in rows]
        except (OSError, sqlite3.Error, ValueError) as exc:
            raise _failure(
                "feedback_list_failed", "The feedback list could not be read"
            ) from exc
        return {"items": items, "total": total, "unread_count": unread}

    def set_read(self, number: int, *, is_read: bool) -> bool:
        """Mark a report read or unread; ``False`` when there is no such report.

        Raises
        ------
        HydrologError
            ``io_error`` (``feedback_update_failed``) if the file cannot be written.
        """
        return self._change(
            "UPDATE feedback SET is_read = ? WHERE id = ?",
            (int(is_read), number),
            "feedback_update_failed",
            "The feedback could not be updated",
        )

    def delete(self, number: int) -> bool:
        """Delete a report; ``False`` when there is no such report.

        Its text is overwritten in the file (``secure_delete``).

        Raises
        ------
        HydrologError
            ``io_error`` (``feedback_delete_failed``) if the file cannot be written.
        """
        return self._change(
            "DELETE FROM feedback WHERE id = ?",
            (number,),
            "feedback_delete_failed",
            "The feedback could not be deleted",
        )

    def _change(
        self, statement: str, values: tuple[int, ...], reason: str, message: str
    ) -> bool:
        """Run one ``UPDATE`` or ``DELETE`` of report ``values[-1]``."""
        if values[-1] > ID_MAX:
            return False
        try:
            with self._connection(create=False) as connection:
                if connection is None:
                    return False
                return connection.execute(statement, values).rowcount > 0
        except (OSError, sqlite3.Error) as exc:
            raise _failure(reason, message) from exc
