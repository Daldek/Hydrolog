"""Atomic replacement of an output file, shared by the writers of the library.

The operations that write a file (``report generate``, ``soil hsg``,
``commands guide --path``) write it aside and rename it over the target, so a reader
never sees a half-written file and a failed computation leaves the old file as it
was. The temporary name must be unique per call: the MCP server runs calls in
worker threads of one process, and two calls may write the same target.
"""

from __future__ import annotations

import contextlib
import os
import secrets
from collections.abc import Iterator
from pathlib import Path

__all__ = ["atomic_output"]


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
