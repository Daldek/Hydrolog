"""The reports of the GUI's users, „Zgłoś uwagę” (Nogat plan 2026-11-03, D3 to D6).

A report is a message (1 to 5000 characters), an optional contact (at most 200), the
address of the page (at most 500), the browser's ``User-Agent`` (cut to 500) and
optional diagnostics, a JSON object of at most 100 000 bytes of compact UTF-8; the
limits and the shapes of the answers are Hydrograf's. The reports live in the SQLite
file ``<data_dir>/hydrolog/feedback.sqlite3`` (DEV-18.2), which the first report
creates with its directory (mode 0700, the file 0600); reading creates nothing. The
file is in WAL mode with a busy timeout, and one process works on it one call at a
time, so concurrent requests, and other processes on the same file, are safe.

The table ``feedback`` holds ``id``, ``created_at`` (UTC, ``2026-11-03T10:15:00Z``),
``message``, ``contact``, ``page_url``, ``user_agent``, ``diagnostics`` (JSON text)
and ``is_read`` (0 or 1), with the limits as ``CHECK`` constraints; ``PRAGMA
user_version`` is 1.
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

from hydrolog.exceptions import HydrologError, InvalidParameterError

__all__ = [
    "CONTACT_MAX",
    "DIAGNOSTICS_MAX_BYTES",
    "FILE_NAME",
    "LIST_LIMIT",
    "LIST_LIMIT_MAX",
    "MESSAGE_MAX",
    "PAGE_URL_MAX",
    "REQUEST_MAX_BYTES",
    "USER_AGENT_MAX",
    "FeedbackStore",
    "Report",
    "parse_read",
    "parse_report",
]

_LOG = logging.getLogger(__name__)

FILE_NAME: Final = "feedback.sqlite3"
"""The file of the reports in ``<data_dir>/hydrolog``."""
MESSAGE_MAX: Final = 5000
CONTACT_MAX: Final = 200
PAGE_URL_MAX: Final = 500
USER_AGENT_MAX: Final = 500
DIAGNOSTICS_MAX_BYTES: Final = 100_000
"""The largest diagnostics: their compact JSON in UTF-8 [bytes]."""
REQUEST_MAX_BYTES: Final = 256 * 1024
"""The largest body of a request of these routes [bytes]."""
LIST_LIMIT: Final = 50
LIST_LIMIT_MAX: Final = 200
ID_MAX: Final = 2**63 - 1
"""The largest id SQLite can hold; a larger one is no report."""
TIMEOUT_S: Final = 10.0
"""How long a call waits for another process's lock on the file [s]."""

_SURROGATE = re.compile("[\ud800-\udfff]")
_SCHEMA: Final = f"""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(message) BETWEEN 1 AND {MESSAGE_MAX}),
    contact TEXT CHECK (length(contact) <= {CONTACT_MAX}),
    page_url TEXT CHECK (length(page_url) <= {PAGE_URL_MAX}),
    user_agent TEXT CHECK (length(user_agent) <= {USER_AGENT_MAX}),
    diagnostics TEXT CHECK (
        json_valid(diagnostics)
        AND length(CAST(diagnostics AS BLOB)) <= {DIAGNOSTICS_MAX_BYTES}
    ),
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback (created_at DESC);
PRAGMA user_version = 1;
"""
_COLUMNS: Final = (
    "id",
    "created_at",
    "message",
    "contact",
    "page_url",
    "user_agent",
    "diagnostics",
    "is_read",
)


@dataclass(frozen=True)
class Report:
    """A checked report, ready to store.

    Attributes
    ----------
    message : str
        What the person wrote, 1 to 5000 characters.
    contact : str or None
        A name or an e-mail address, at most 200 characters.
    page_url : str or None
        The address of the page, at most 500 characters.
    diagnostics : str or None
        The diagnostics as compact JSON text, at most 100 000 bytes.
    """

    message: str
    contact: str | None
    page_url: str | None
    diagnostics: str | None


def _clean(text: str) -> str:
    """Replace lone surrogates, which UTF-8 cannot hold, with U+FFFD."""
    return _SURROGATE.sub("\ufffd", text)


def _invalid(name: str, reason: str, message: str, **details: Any) -> HydrologError:
    return InvalidParameterError(
        message, details={"parameter": name, "reason": reason, **details}
    )


def _text(
    body: Mapping[str, Any], name: str, maximum: int, *, required: bool = False
) -> str | None:
    """Return the text ``name`` of the body, checked against its limit."""
    value = body.get(name)
    if value is None:
        if required:
            raise _invalid(name, "required", f"The field {name!r} is required")
        return None
    if not isinstance(value, str):
        raise _invalid(
            name, "type", f"The field {name!r} must be a string", expected="string"
        )
    if required and not value:
        raise _invalid(name, "empty", f"The field {name!r} must not be empty")
    if len(value) > maximum:
        raise _invalid(
            name,
            "too_long",
            f"The field {name!r} has {len(value)} characters, at most {maximum}",
            max_length=maximum,
            length=len(value),
        )
    return _clean(value)


def _diagnostics(value: object) -> str | None:
    """Return the diagnostics as compact JSON text, checked against their limit."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise _invalid(
            "diagnostics",
            "type",
            "The field 'diagnostics' must be a JSON object",
            expected="object",
        )
    try:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (ValueError, RecursionError) as exc:
        raise _invalid(
            "diagnostics", "invalid_json", f"The diagnostics are not JSON: {exc}"
        ) from exc
    text = _clean(text)
    size = len(text.encode("utf-8"))
    if size > DIAGNOSTICS_MAX_BYTES:
        raise _invalid(
            "diagnostics",
            "too_large",
            f"The diagnostics have {size} bytes, at most {DIAGNOSTICS_MAX_BYTES}",
            limit_bytes=DIAGNOSTICS_MAX_BYTES,
            size_bytes=size,
        )
    return text


def parse_report(body: Mapping[str, Any]) -> Report:
    """Check the body of ``POST api/feedback`` (Hydrograf's ``FeedbackRequest``).

    Parameters
    ----------
    body : Mapping
        The JSON object: ``message`` (required), ``contact``, ``page_url`` and
        ``diagnostics`` (each optional or null); other fields are ignored.

    Returns
    -------
    Report
        The report, lone surrogates replaced with U+FFFD.

    Raises
    ------
    InvalidParameterError
        ``details.parameter`` names the field, ``details.reason`` is ``required``,
        ``type``, ``empty``, ``too_long`` (``max_length``) or ``too_large``
        (``limit_bytes``).
    """
    message = _text(body, "message", MESSAGE_MAX, required=True)
    assert message is not None
    return Report(
        message=message,
        contact=_text(body, "contact", CONTACT_MAX),
        page_url=_text(body, "page_url", PAGE_URL_MAX),
        diagnostics=_diagnostics(body.get("diagnostics")),
    )


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
    if item["diagnostics"] is not None:
        item["diagnostics"] = json.loads(item["diagnostics"])
    item["is_read"] = bool(item["is_read"])
    return item


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
        otherwise it yields ``None``.
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
                if not self._ready:
                    connection.execute("PRAGMA journal_mode = WAL")
                    if connection.execute("PRAGMA user_version").fetchone()[0] == 0:
                        connection.executescript(_SCHEMA)
                    self._ready = True
                yield connection

    def add(self, report: Report, *, user_agent: str) -> int:
        """Store a report; return its id.

        Parameters
        ----------
        report : Report
            The checked report.
        user_agent : str
            The ``User-Agent`` of the request, cut to 500 characters.

        Returns
        -------
        int
            The id of the new report.

        Raises
        ------
        HydrologError
            ``io_error`` (``feedback_store_failed``) if the file cannot be written.
        """
        values = (
            _now(),
            report.message,
            report.contact,
            report.page_url,
            _clean(user_agent[:USER_AGENT_MAX]),
            report.diagnostics,
        )
        try:
            with self._connection(create=True) as connection:
                assert connection is not None
                cursor = connection.execute(
                    "INSERT INTO feedback (created_at, message, contact, page_url,"
                    " user_agent, diagnostics) VALUES (?, ?, ?, ?, ?, ?)",
                    values,
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
            ``created_at``, ``message``, ``contact``, ``page_url``, ``user_agent``,
            ``diagnostics`` (an object or null) and ``is_read``.

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
