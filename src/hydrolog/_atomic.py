"""Atomic replacement of output files, shared by the writers of the library.

The operations that write a file (``report generate``, ``soil hsg``,
``commands guide --path``) write it aside and rename it over the target, so a reader
never sees a half-written file and a failed computation leaves the old file as it
was. The temporary name must be unique per call: the MCP server runs calls in
worker threads of one process, and two calls may write the same target.

A command that writes several files into a directory (``--output-dir``) goes through
a staging directory instead (DEV-19.7, :func:`staging_directory`): every file is
written there first, so an error or an interrupt before the moves leaves no partial
target.
"""

from __future__ import annotations

import contextlib
import os
import re
import secrets
import shutil
import socket
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Final

__all__ = ["STAGING_NAME", "atomic_output", "staging_directory"]

STAGING_NAME: Final = ".hydrolog-incoming"
"""Name of the directory, inside the output directory, that holds the staging of a
write (DEV-19.7)."""
_STALE_SECONDS: Final = 24 * 3600.0


@contextlib.contextmanager
def atomic_output(target: str | os.PathLike[str]) -> Iterator[Path]:
    """Yield a temporary path beside ``target``; on success move it over ``target``.

    The block writes the new content to the yielded path (a file in the directory of
    ``target``, so the final rename stays on one file system and is atomic). When the
    block ends without an exception the file replaces ``target`` (an existing file is
    replaced). The temporary file is removed whatever the outcome, so a failure leaves
    neither a partial output nor a stray file behind.

    The name of the temporary file holds a random token: every call gets its own file
    even when several threads or processes write the same ``target`` at once. Each
    of them replaces ``target`` with its complete content; the last one wins.

    Parameters
    ----------
    target : str or os.PathLike
        File to write. Missing parent directories are created when the block is
        entered (so a caller that validates its inputs first leaves nothing behind on
        a validation error).

    Yields
    ------
    pathlib.Path
        Where to write the new content.

    Raises
    ------
    OSError
        If the directory cannot be created, the content cannot be written or the file
        cannot be moved. Callers turn it into the error of their own interface.

    Examples
    --------
    >>> with atomic_output("out/report.md") as temporary:  # doctest: +SKIP
    ...     _ = temporary.write_text("# Report", encoding="utf-8")
    """
    path = Path(target)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        yield temporary
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()


def _remove_stale(parent: Path) -> None:
    """Remove the staging directories that a killed run left over (older than 24 h)."""
    cutoff = time.time() - _STALE_SECONDS
    with contextlib.suppress(OSError):
        for entry in parent.iterdir():
            try:
                if entry.is_dir() and entry.stat().st_mtime < cutoff:
                    shutil.rmtree(entry, ignore_errors=True)
            except OSError:
                continue


@contextlib.contextmanager
def staging_directory(directory: str | os.PathLike[str]) -> Iterator[Path]:
    """Yield a staging directory for writing several files into ``directory``.

    The directory is ``<directory>/.hydrolog-incoming/<host>_<pid>_<token>/``, on the
    file system of ``directory``, so the files written there move into place with
    ``os.replace`` (DEV-19.7). It is removed whatever the outcome (a normal end, an
    error, SIGINT or, through the handler of the command line, SIGTERM), and with it
    ``.hydrolog-incoming`` when nothing else is in it; the staging directories of
    other runs that are older than 24 hours (a run that was killed) are removed when
    a new one is made. Nothing else is created or deleted: no sidecar, no link
    (DEV-19.8).

    Parameters
    ----------
    directory : str or os.PathLike
        The output directory; it is created, with its parents, when it is missing.

    Yields
    ------
    pathlib.Path
        The empty staging directory.

    Raises
    ------
    OSError
        If the directories cannot be created; callers turn it into the error of their
        own interface.

    Examples
    --------
    >>> with staging_directory("out") as staging:  # doctest: +SKIP
    ...     _ = (staging / "a.csv").write_text("x", encoding="utf-8")
    ...     os.replace(staging / "a.csv", "out/a.csv")
    """
    parent = Path(directory) / STAGING_NAME
    host = re.sub(r"[^\w.-]", "_", socket.gethostname()) or "host"
    staging = parent / f"{host}_{os.getpid()}_{secrets.token_hex(4)}"
    try:
        staging.mkdir(parents=True)
        _remove_stale(parent)
        yield staging
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        with contextlib.suppress(OSError):
            parent.rmdir()
