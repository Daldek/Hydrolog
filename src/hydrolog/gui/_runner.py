"""Warm worker processes of the GUI server: one queue, the newest run wins (plan D6).

A :class:`Runner` keeps ``workers`` processes of :mod:`hydrolog.gui._worker`, each
driven by a thread of its own, and one first-in, first-out queue of runs. A run may
name a channel (the app passes the session and the page's channel): a newer run of the
same channel ends an older one that is still queued with the ``cancelled`` envelope
and the notice ``superseded``; one that already runs finishes (milliseconds), and the
page ignores it. A run longer than ``timeout_s`` kills its worker, which is replaced;
the run ends ``cancelled`` with the notice ``timeout``. A worker that dies during a
run is replaced too, and the run ends with ``internal_error``.

Threads, not processes, wait for the workers, so a :class:`~concurrent.futures.Future`
carries each outcome to any event loop (``asyncio.wrap_future``); cancelling the
future of a queued run (the browser went away) drops the run.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import queue
import subprocess
import sys
import threading
from collections import deque
from collections.abc import Hashable, Mapping
from concurrent.futures import Future, InvalidStateError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import hydrolog
from hydrolog.catalog.envelope import RESULT_SCHEMA, TOOL
from hydrolog.exceptions import HydrologError, error_document

WORKER_MODULE: Final = "hydrolog.gui._worker"
"""The module a worker process runs (``python -m``)."""
THREAD_VARIABLES: Final[tuple[str, ...]] = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
)
"""Set to 1 for the workers: two processes, one thread of numerical code each."""
START_TIMEOUT_S: Final = 120.0
"""How long a new worker may take to import its libraries [s]."""
SUPERSEDED: Final = "superseded"
TIMEOUT: Final = "timeout"

_LOG = logging.getLogger(__name__)
_STOP_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class Job:
    """One run of a catalog command for a session.

    Attributes
    ----------
    command : str
        Catalog name (``"tc kirpich"``).
    options : Mapping
        The options, paths already absolute inside ``root``.
    root : str
        The session directory: the one allowed directory of the run.
    check : bool
        Plan the command instead of running it.
    """

    command: str
    options: Mapping[str, Any]
    root: str
    check: bool = False


@dataclass(frozen=True)
class Outcome:
    """How a run ended: an envelope (also ``cancelled``) or an error document."""

    document: dict[str, Any]
    error: bool = False


def superseded_notice() -> dict[str, Any]:
    """Return the notice of a run replaced by a newer one of its channel."""
    return {
        "level": "info",
        "code": SUPERSEDED,
        "message": "A newer run of the same channel replaced this one.",
    }


def timeout_notice(timeout_s: float) -> dict[str, Any]:
    """Return the notice of a run stopped after ``timeout_s`` seconds."""
    return {
        "level": "warning",
        "code": TIMEOUT,
        "message": f"The run took longer than {timeout_s:g} s and was stopped.",
        "details": {"timeout_s": timeout_s},
    }


def cancelled(job: Job, notice: Mapping[str, Any]) -> Outcome:
    """Return the ``cancelled`` envelope of ``job`` with its one notice (AGI-4.2)."""
    return Outcome(
        {
            "schema": RESULT_SCHEMA,
            "tool": TOOL,
            "version": hydrolog.__version__,
            "command": job.command,
            "check": job.check,
            "status": "cancelled",
            "result": None,
            "notices": [dict(notice)],
        }
    )


def _failed(job: Job, exc: HydrologError) -> Outcome:
    return Outcome(error_document(exc, job.command, "pl"), error=True)


def _stopped(job: Job) -> Outcome:
    return _failed(
        job,
        HydrologError("The GUI server stopped before the run ended", code="terminated"),
    )


def _resolve(future: Future[Outcome], outcome: Outcome) -> None:
    """Give ``future`` its outcome unless it already has one or was cancelled."""
    with contextlib.suppress(InvalidStateError):
        future.set_result(outcome)


def _environment() -> dict[str, str]:
    """Return the environment of a worker: one thread, this ``hydrolog`` importable."""
    environment = dict(os.environ)
    environment.update(dict.fromkeys(THREAD_VARIABLES, "1"))
    package_root = str(Path(hydrolog.__file__).resolve().parent.parent)
    paths = [package_root, *environment.get("PYTHONPATH", "").split(os.pathsep)]
    environment["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(p for p in paths if p))
    return environment


class _Crashed(Exception):
    """The worker process ended or its pipe broke."""

    def __init__(self, exit_code: int | None) -> None:
        super().__init__(f"exit code {exit_code}")
        self.exit_code = exit_code


class _Worker:
    """One worker process and the thread that reads its answers."""

    def __init__(self, module: str, cwd: Path | None) -> None:
        argv = [sys.executable, "-m", module]
        pipe = subprocess.PIPE
        environment = _environment()
        # A group of its own: Ctrl+C in the terminal stops the server, which stops
        # the workers, instead of reaching the workers in the middle of a run.
        if sys.platform == "win32":
            self.process = subprocess.Popen(
                argv,
                stdin=pipe,
                stdout=pipe,
                env=environment,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            self.process = subprocess.Popen(
                argv,
                stdin=pipe,
                stdout=pipe,
                env=environment,
                cwd=cwd,
                start_new_session=True,
            )
        self._lines: queue.Queue[bytes | None] = queue.Queue()
        self._reader = threading.Thread(
            target=self._read,
            name=f"hydrolog-gui-reader-{self.process.pid}",
            daemon=True,
        )
        self._reader.start()

    @property
    def pid(self) -> int:
        """int: the process id."""
        return self.process.pid

    def alive(self) -> bool:
        """Tell whether the process still runs."""
        return self.process.poll() is None

    def _read(self) -> None:
        stdout = self.process.stdout
        assert stdout is not None
        try:
            for line in stdout:
                self._lines.put(line)
        except (OSError, ValueError):  # the pipe was closed by stop()
            pass
        finally:
            self._lines.put(None)

    def _exit_code(self) -> int | None:
        try:
            return self.process.wait(timeout=_STOP_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return None

    def wait_ready(self, timeout_s: float) -> None:
        """Wait for the line ``{"ready": true}``.

        Raises
        ------
        _Crashed
            If the process ends first.
        TimeoutError
            If it is not ready within ``timeout_s``.
        """
        try:
            line = self._lines.get(timeout=timeout_s)
        except queue.Empty as exc:
            raise TimeoutError(f"not ready within {timeout_s:g} s") from exc
        if line is None:
            raise _Crashed(self._exit_code())
        if json.loads(line).get("ready") is not True:
            raise _Crashed(None)

    def call(self, job: Job, timeout_s: float) -> Outcome | None:
        """Run ``job``; return ``None`` if it takes longer than ``timeout_s``.

        Raises
        ------
        _Crashed
            If the process ends or its pipe breaks during the run.
        """
        request = {
            "command": job.command,
            "options": dict(job.options),
            "root": job.root,
            "check": job.check,
        }
        line = json.dumps(request, ensure_ascii=False, allow_nan=False)
        stdin = self.process.stdin
        assert stdin is not None
        try:
            stdin.write(line.encode("utf-8") + b"\n")
            stdin.flush()
        except (OSError, ValueError) as exc:
            raise _Crashed(self._exit_code()) from exc
        try:
            reply = self._lines.get(timeout=timeout_s)
        except queue.Empty:
            return None
        if reply is None:
            raise _Crashed(self._exit_code())
        message = json.loads(reply)
        return Outcome(message["document"], error=bool(message["error"]))

    def stop(self) -> None:
        """Kill the process and close its pipes."""
        if self.alive():
            self.process.kill()
        self._exit_code()
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                with contextlib.suppress(OSError):
                    stream.close()
        self._reader.join(timeout=_STOP_TIMEOUT_S)


@dataclass(eq=False)
class _Item:
    job: Job
    channel: Hashable | None
    future: Future[Outcome] = field(default_factory=Future)


class Runner:
    """Worker processes and the queue of runs of one GUI app.

    Parameters
    ----------
    workers : int, optional
        Number of worker processes (at least 1).
    timeout_s : float, optional
        Longest run [s]; a longer one kills its worker.
    cwd : Path, optional
        Working directory of the workers (the work root of the sessions).
    worker_module : str, optional
        The module the workers run; :data:`WORKER_MODULE` by default.
    """

    def __init__(
        self,
        *,
        workers: int = 2,
        timeout_s: float = 30.0,
        cwd: Path | None = None,
        worker_module: str | None = None,
    ) -> None:
        self.workers = workers
        self.timeout_s = timeout_s
        self._cwd = cwd
        self._module = WORKER_MODULE if worker_module is None else worker_module
        self._lock = threading.Condition()
        self._queue: deque[_Item] = deque()
        self._pending: dict[Hashable, _Item] = {}
        self._threads: list[threading.Thread] = []
        self._live: set[_Worker] = set()
        self._started = False
        self._closed = False

    def start(self) -> None:
        """Start the workers (they import their libraries in the background)."""
        with self._lock:
            self._start()

    def _start(self) -> None:
        if self._started or self._closed:
            return
        self._started = True
        for slot in range(self.workers):
            thread = threading.Thread(
                target=self._drive, name=f"hydrolog-gui-worker-{slot}", daemon=True
            )
            thread.start()
            self._threads.append(thread)

    def submit(self, job: Job, *, channel: Hashable | None = None) -> Future[Outcome]:
        """Queue a run; the newest run of a channel replaces its queued older one.

        Parameters
        ----------
        job : Job
            The run.
        channel : hashable, optional
            Key of the run's channel; ``None`` is a run that no other replaces.

        Returns
        -------
        concurrent.futures.Future
            Its :class:`Outcome`; cancel it to drop the run while it is queued.
        """
        item = _Item(job, channel)
        replaced: _Item | None = None
        with self._lock:
            if self._closed:
                _resolve(item.future, _stopped(job))
                return item.future
            self._start()
            if channel is not None:
                replaced = self._pending.pop(channel, None)
                if replaced is not None:
                    self._queue.remove(replaced)
                self._pending[channel] = item
            self._queue.append(item)
            self._lock.notify()
        if replaced is not None:
            _resolve(replaced.future, cancelled(replaced.job, superseded_notice()))
        return item.future

    def close(self) -> None:
        """Stop the workers; queued runs end with ``terminated``."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            dropped = list(self._queue)
            self._queue.clear()
            self._pending.clear()
            live = list(self._live)
            self._lock.notify_all()
        for item in dropped:
            _resolve(item.future, _stopped(item.job))
        for worker in live:
            worker.stop()
        for thread in self._threads:
            thread.join(timeout=_STOP_TIMEOUT_S)

    def _take(self) -> _Item | None:
        """Wait for the next queued run that was not cancelled; ``None`` when closed."""
        with self._lock:
            while not self._closed:
                while self._queue:
                    item = self._queue.popleft()
                    if (
                        item.channel is not None
                        and self._pending.get(item.channel) is item
                    ):
                        del self._pending[item.channel]
                    if item.future.set_running_or_notify_cancel():
                        return item
                self._lock.wait()
            return None

    def _spawn(self) -> _Worker | None:
        """Start a worker and wait until it is ready; ``None`` if it cannot start."""
        with self._lock:
            if self._closed:
                return None
            try:
                worker = _Worker(self._module, self._cwd)
            except OSError:
                _LOG.exception("The worker process of the GUI server cannot start")
                return None
            self._live.add(worker)
        try:
            worker.wait_ready(START_TIMEOUT_S)
        except (_Crashed, TimeoutError, ValueError) as exc:
            if not self._closed:  # close() kills the workers that are starting
                _LOG.error(
                    "The worker process of the GUI server did not start: %s", exc
                )
            self._retire(worker)
            return None
        return worker

    def _retire(self, worker: _Worker) -> None:
        worker.stop()
        with self._lock:
            self._live.discard(worker)

    def _drive(self) -> None:
        """Run the queue on one worker, replacing the worker when it fails."""
        worker = self._spawn()
        try:
            while (item := self._take()) is not None:
                if worker is None or not worker.alive():
                    if worker is not None:
                        self._retire(worker)
                    worker = self._spawn()
                if worker is None:
                    message = "The worker process of the GUI server did not start"
                    _resolve(item.future, _failed(item.job, HydrologError(message)))
                    continue
                outcome = self._call(worker, item.job)
                if outcome is None:
                    self._retire(worker)
                    worker = None
                    outcome = (
                        _stopped(item.job)
                        if self._closed
                        else cancelled(item.job, timeout_notice(self.timeout_s))
                    )
                _resolve(item.future, outcome)
                if worker is None or not worker.alive():
                    if worker is not None:
                        self._retire(worker)
                    worker = self._spawn()  # replaced now, warm for the next run
        finally:
            if worker is not None:
                self._retire(worker)

    def _call(self, worker: _Worker, job: Job) -> Outcome | None:
        """Run ``job`` on ``worker``; ``None`` for a timeout or a stop."""
        try:
            return worker.call(job, self.timeout_s)
        except _Crashed as crash:
            if self._closed:
                return None
            _LOG.error(
                "The worker process of the GUI server ended during %r (%s)",
                job.command,
                crash,
            )
            worker.stop()
            message = (
                "The worker process of the GUI server ended during the run "
                f"(exit code {crash.exit_code})"
            )
            details = {"exit_code": crash.exit_code}
            return _failed(job, HydrologError(message, details=details))
