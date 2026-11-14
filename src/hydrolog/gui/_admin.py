"""The admin panel's status (Nogat DEV-15.13): the server, its disk and its checks.

``GET api/admin/status`` answers :func:`status_document`. Hydrolog has two checks,
which the README names: ``data_dir``, the directory of the reports and the daily
totals (``<data_dir>/hydrolog``) can be written, and ``feedback_db``, the reports'
SQLite file can be read. A check's ``detail`` is Polish, as the panel is.
"""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from hydrolog.exceptions import HydrologError
from hydrolog.gui._feedback import FeedbackStore

__all__ = ["APP", "data_dir_check", "feedback_check", "status_document"]

APP: Final = "Hydrolog"
"""The app's name in the status (``app``)."""


def _existing(path: Path) -> Path:
    """Return ``path`` or its nearest ancestor that exists."""
    for candidate in (path, *path.parents):
        if candidate.exists():
            return candidate
    return Path(path.anchor or ".")


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def data_dir_check(directory: Path) -> dict[str, str]:
    """Check that the reports and the totals can be written in ``directory``.

    An existing directory takes a probe file, made and removed at once; a missing
    one, made by the first write, needs a writable directory above it.
    """
    name = "data_dir"
    failed = _check(name, "failed", "Nie można zapisywać w katalogu danych.")
    if directory.exists():
        probe = directory / f".write-check-{secrets.token_hex(8)}"
        try:
            os.close(os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
            probe.unlink()
        except OSError:
            return failed
        return _check(name, "ok", "Katalog danych jest zapisywalny.")
    above = _existing(directory)
    if above.is_dir() and os.access(above, os.W_OK | os.X_OK):
        return _check(name, "ok", "Katalog danych powstanie przy pierwszym zapisie.")
    return failed


def feedback_check(store: FeedbackStore) -> dict[str, str]:
    """Check that the reports' file can be read; give its counts."""
    name = "feedback_db"
    if not store.path.is_file():
        return _check(name, "ok", "Brak zgłoszeń; plik powstanie z pierwszym z nich.")
    try:
        counts = store.listing(limit=0, offset=0)
    except HydrologError:
        return _check(name, "failed", "Nie można odczytać pliku zgłoszeń.")
    total, unread = counts["total"], counts["unread_count"]
    return _check(name, "ok", f"Zgłoszenia: {total}, nieprzeczytane: {unread}.")


def _disk(directory: Path) -> dict[str, int | None]:
    """Return the free and total bytes of the file system that holds ``directory``."""
    try:
        usage = shutil.disk_usage(_existing(directory))
    except OSError:
        return {"free_bytes": None, "total_bytes": None}
    return {"free_bytes": usage.free, "total_bytes": usage.total}


def status_document(
    *,
    version: str,
    started_at: datetime,
    uptime_s: float,
    data_dir: Path,
    reports: FeedbackStore,
) -> dict[str, Any]:
    """Return the answer of ``GET api/admin/status``.

    Parameters
    ----------
    version : str
        Hydrolog's version.
    started_at : datetime
        When the app was built (aware, UTC).
    uptime_s : float
        The seconds since then [s].
    data_dir : Path
        ``<data_dir>/hydrolog``, the directory of the reports and the totals.
    reports : FeedbackStore
        The reports.

    Returns
    -------
    dict
        ``{app, version, started_at, uptime_s, data_dir, disk: {free_bytes,
        total_bytes}, checks: [{name, status, detail}]}``; ``status`` is ``ok``,
        ``warning`` or ``failed``.
    """
    return {
        "app": APP,
        "version": version,
        "started_at": started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "uptime_s": int(uptime_s),
        "data_dir": str(data_dir),
        "disk": _disk(data_dir),
        "checks": [data_dir_check(data_dir), feedback_check(reports)],
    }
