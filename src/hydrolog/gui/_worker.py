"""A warm worker process of the GUI server: catalog commands over a pipe (plan D6).

:class:`hydrolog.gui._runner.Runner` starts ``python -m hydrolog.gui._worker`` with
``OPENBLAS_NUM_THREADS``, ``OMP_NUM_THREADS`` and ``MKL_NUM_THREADS`` at 1. The worker
caps its address space at :data:`MEMORY_LIMIT_BYTES` (POSIX), imports NumPy, SciPy and
:mod:`hydrolog.operations` once, writes the line ``{"ready": true, "pid": ...}`` and
then answers each request line with one response line (UTF-8 JSON):

* request ``{"command": "tc kirpich", "options": {...}, "root": "<session dir>",
  "check": false}`` -- :func:`~hydrolog.catalog.run_command` (or
  :func:`~hydrolog.catalog.check_command`) with ``allowed_dirs=[root]``;
* response ``{"document": {...}, "error": false}`` with the ``hydrolog-result/1``
  envelope, or ``"error": true`` with the ``hydrolog-error/1`` document (Polish
  ``title``); every path inside ``root`` is relative to it in both.

The protocol uses the process's original standard output; anything a library prints
goes to standard error instead. The worker ends at the end of its input; Ctrl+C in
the terminal is the server's, not the worker's.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import sys
from collections.abc import Mapping
from typing import Any, BinaryIO, Final

MEMORY_LIMIT_BYTES: Final = 2 << 30
"""Address space of a worker on POSIX [B] (``RLIMIT_AS``, 2 GiB)."""


def handle(request: Mapping[str, Any]) -> dict[str, Any]:
    """Run one request of the protocol.

    Parameters
    ----------
    request : Mapping
        ``command``, ``options``, ``root`` (the session directory) and ``check``.

    Returns
    -------
    dict
        ``{"document": <envelope or error document>, "error": <bool>}``, with the
        paths inside ``root`` relative to it.
    """
    from hydrolog.catalog import check_command, run_command
    from hydrolog.exceptions import error_document
    from hydrolog.gui._sessions import relative_paths

    command = str(request["command"])
    root = str(request["root"])
    run = check_command if request.get("check") else run_command
    try:
        envelope = run(command, request["options"], allowed_dirs=[root]).to_dict()
    except Exception as exc:  # every failure of a run is an error document
        document = error_document(exc, command, "pl")
        return {"document": relative_paths(document, root), "error": True}
    return {"document": relative_paths(envelope, root), "error": False}


def _send(stream: BinaryIO, message: Mapping[str, Any]) -> None:
    text = json.dumps(message, ensure_ascii=False, allow_nan=False)
    stream.write(text.encode("utf-8") + b"\n")
    stream.flush()


def _limit_memory() -> None:
    """Cap the address space at :data:`MEMORY_LIMIT_BYTES` (POSIX only)."""
    if sys.platform == "win32":
        return
    import resource

    _, hard = resource.getrlimit(resource.RLIMIT_AS)
    limit = MEMORY_LIMIT_BYTES
    if hard != resource.RLIM_INFINITY:
        limit = min(limit, hard)
    # macOS refuses some values: there the cap is best effort.
    with contextlib.suppress(ValueError, OSError):
        resource.setrlimit(resource.RLIMIT_AS, (limit, hard))


def main() -> None:
    """Serve requests from standard input until it ends."""
    protocol = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _limit_memory()
    import numpy  # noqa: F401 -- warm: imported once, before the first run
    import scipy  # noqa: F401

    import hydrolog.operations  # noqa: F401

    _send(protocol, {"ready": True, "pid": os.getpid()})
    for line in sys.stdin.buffer:
        _send(protocol, handle(json.loads(line)))


if __name__ == "__main__":
    main()
