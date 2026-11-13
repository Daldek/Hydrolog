"""Browser sessions of the GUI server: work directories, file names and limits.

Plan 2026-11-02, D7; ADR-0034. A browser session is a random id, which the page keeps
in its memory only and sends in the header ``X-Hydrolog-Session`` (no cookie), and a
directory ``<work root>/<id>/`` (mode 0700) holding ``in/`` (uploads and the documents
the page writes) and ``out/`` (what commands write). A path that the page gives a
command is ``in/<name>`` or ``out/<name>``; :func:`check_name` is the rule of
``<name>``. The files serve the person's computations only: the page ends its session
when it is closed or reloaded, a session idle for :attr:`Limits.idle_s` is removed by
:meth:`Sessions.sweep`, and :class:`Sessions` keeps at most :attr:`Limits.sessions` of
them: a new one removes the least recently used idle session.

Nothing here knows HTTP; :mod:`hydrolog.gui._app` turns the errors raised here into
``hydrolog-error/1`` responses.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
import secrets
import shutil
import tempfile
import time
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

from hydrolog.catalog.spec import Command
from hydrolog.exceptions import ConflictError, ForbiddenPathError

MIB: Final = 1 << 20
AREAS: Final[tuple[str, ...]] = ("in", "out")
"""The directories of a session: uploads and documents (``in``), outputs (``out``)."""
NAME_PATTERN: Final = r"[A-Za-z0-9][A-Za-z0-9._ -]{0,127}"
"""A file name of a session (plan D7); :func:`check_name` adds the Windows rules."""
MAX_DEPTH: Final = 8
"""Most names in a path below an area (outputs a command writes into a directory)."""

_NAME = re.compile(NAME_PATTERN)
_SESSION_ID = re.compile(r"[A-Za-z0-9_-]{43}")
# Names that Windows reserves for devices in every directory, whatever the extension.
_DEVICES: Final = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in range(10)}
    | {f"lpt{digit}" for digit in range(10)}
)
_HASH_CHUNK = 1 << 20


@dataclass(frozen=True)
class Limits:
    """Limits of the GUI server (plan D7).

    Attributes
    ----------
    file_bytes : int
        Largest uploaded file [B].
    session_bytes : int
        Most bytes of all files of a session [B].
    session_files : int
        Most files of a session (uploads and outputs).
    request_bytes : int
        Largest JSON body of a request [B].
    sessions : int
        Most sessions at once.
    idle_s : float
        Idle time after which a session is removed [s].
    """

    file_bytes: int = 20 * MIB
    session_bytes: int = 100 * MIB
    session_files: int = 200
    request_bytes: int = 5 * MIB
    sessions: int = 64
    idle_s: float = 3600.0

    def to_dict(self) -> dict[str, Any]:
        """Return the limits as the ``limits`` of ``hydrolog-gui-session/1``."""
        return {
            "file_bytes": self.file_bytes,
            "session_bytes": self.session_bytes,
            "session_files": self.session_files,
            "request_bytes": self.request_bytes,
            "sessions": self.sessions,
            "idle_s": self.idle_s,
            "name_pattern": f"^{NAME_PATTERN}$",
        }


def check_name(name: str) -> bool:
    """Tell whether ``name`` is a file name of a session.

    Parameters
    ----------
    name : str
        One name, without a directory.

    Returns
    -------
    bool
        ``True`` for a name matching :data:`NAME_PATTERN` that Windows can also use:
        not ending with a dot or a space and not a device name (``CON``, ``nul.txt``).
    """
    if _NAME.fullmatch(name) is None or name.endswith((".", " ")):
        return False
    return name.split(".", 1)[0].rstrip(" ").lower() not in _DEVICES


def split_path(value: str) -> tuple[str, tuple[str, ...]] | None:
    """Split ``in/<name>`` or ``out/<name>/<name>`` into its area and names.

    Parameters
    ----------
    value : str
        A path as the page writes it, with ``/`` between the parts.

    Returns
    -------
    tuple or None
        The area and the names (at most :data:`MAX_DEPTH`), or ``None`` when the value
        is not such a path (absolute, ``..``, a backslash, a name breaking
        :func:`check_name`).
    """
    area, _, rest = value.partition("/")
    names = tuple(rest.split("/")) if rest else ()
    if area not in AREAS or not names or len(names) > MAX_DEPTH:
        return None
    if not all(check_name(name) for name in names):
        return None
    return area, names


def _forbidden(option: str, value: object, reason: str, message: str) -> NoReturn:
    raise ForbiddenPathError(
        message,
        details={
            "option": option,
            "reason": reason,
            "value": value if isinstance(value, str) else repr(value),
            "allowed": ["in/<name>", "out/<name>"],
            "pattern": f"^{NAME_PATTERN}$",
        },
        hint="Upload the file and give it as in/<name>; outputs go to out/<name>.",
    )


def relative_paths(value: Any, directory: str) -> Any:
    """Rewrite the paths inside a session directory relative to it (plan D5).

    Parameters
    ----------
    value : object
        A JSON-compatible document (an envelope, an error document).
    directory : str
        The session directory, absolute and resolved.

    Returns
    -------
    object
        A copy in which a text that is a path inside ``directory`` becomes relative
        with ``/`` (``in/x.csv``), the directory itself becomes ``.``, and paths
        inside longer texts (messages) lose the directory, so no server path reaches
        the browser.
    """
    base = directory.rstrip(os.sep)
    prefix = base + os.sep

    def rewrite(item: Any) -> Any:
        if isinstance(item, str):
            if base not in item:
                return item
            if item == base:
                return "."
            if item.startswith(prefix):
                return item[len(prefix) :].replace(os.sep, "/").replace(base, ".")
            return item.replace(prefix, "").replace(base, ".")
        if isinstance(item, dict):
            return {key: rewrite(child) for key, child in item.items()}
        if isinstance(item, list):
            return [rewrite(child) for child in item]
        return item

    return rewrite(value)


@dataclass(eq=False)
class Session:
    """One browser session and its work directory.

    Attributes
    ----------
    id : str
        The random id, which the page sends in ``X-Hydrolog-Session``.
    directory : Path
        ``<work root>/<id>``, resolved; ``in/`` and ``out/`` are inside.
    last_used : float
        Clock time of the last request [s].
    """

    id: str
    directory: Path
    last_used: float
    _busy: int = 0
    _hashes: dict[Path, tuple[int, int, str]] = field(default_factory=dict)

    @property
    def busy(self) -> bool:
        """bool: a run or an upload of the session is in progress."""
        return self._busy > 0

    @contextlib.contextmanager
    def use(self) -> Iterator[None]:
        """Mark the session busy (not removable) for the block."""
        self._busy += 1
        try:
            yield
        finally:
            self._busy -= 1

    def path(self, area: str, names: tuple[str, ...]) -> Path:
        """Return the absolute path of ``<area>/<names...>`` (checked by the caller)."""
        return self.directory.joinpath(area, *names)

    def command_options(
        self, command: Command, options: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Turn the page's paths into the session's absolute paths (plan D7).

        Parameters
        ----------
        command : Command
            The catalog command the options are for.
        options : Mapping
            The options as the page sent them.

        Returns
        -------
        dict
            The options with every path option absolute inside the session; the other
            options unchanged (the catalog validates them in the run).

        Raises
        ------
        ForbiddenPathError
            If a path option is not ``in/<name>`` or ``out/<name>`` (``details.reason``
            ``outside_session``), or an output option is not in ``out/``
            (``output_area``).
        """
        resolved = dict(options)
        for option in command.options:
            if option.type != "path" or option.name not in resolved:
                continue
            value = resolved[option.name]
            if not isinstance(value, str):
                continue  # a wrong type is the catalog's validation_error
            split = split_path(value)
            if split is None or len(split[1]) != 1:
                _forbidden(
                    option.name,
                    value,
                    "outside_session",
                    f"Option {option.name!r}: {value!r} is not a file of the session; "
                    "give in/<name> or out/<name>",
                )
            area, names = split
            if option.path_role == "output" and area != "out":
                _forbidden(
                    option.name,
                    value,
                    "output_area",
                    f"Option {option.name!r}: a command writes only into out/, "
                    f"got {value!r}",
                )
            resolved[option.name] = str(self.path(area, names))
        return resolved

    def usage(self) -> tuple[int, int]:
        """Return the bytes and the number of the files of the session."""
        size = count = 0
        for path in self._walk():
            with contextlib.suppress(OSError):
                size += path.stat().st_size
                count += 1
        return size, count

    def files(self) -> list[dict[str, Any]]:
        """Return the files of the session as ``{path, size_bytes, sha256}``.

        Returns
        -------
        list of dict
            Sorted by ``path``; a hash is computed once per size and modification
            time of a file.
        """
        listed: list[dict[str, Any]] = []
        seen: set[Path] = set()
        for path in self._walk():
            try:
                stat = path.stat()
                key = (stat.st_size, stat.st_mtime_ns)
                cached = self._hashes.get(path)
                digest = cached[2] if cached and cached[:2] == key else _sha256(path)
            except OSError:
                continue
            self._hashes[path] = (*key, digest)
            seen.add(path)
            listed.append(
                {
                    "path": path.relative_to(self.directory).as_posix(),
                    "size_bytes": stat.st_size,
                    "sha256": digest,
                }
            )
        for stale in set(self._hashes) - seen:  # two listings may run at once
            self._hashes.pop(stale, None)
        return sorted(listed, key=lambda item: str(item["path"]))

    def _walk(self) -> Iterator[Path]:
        """Yield the regular files of ``in/`` and ``out/`` (no links or temporaries)."""
        for area in AREAS:
            for folder, directories, names in os.walk(self.directory / area):
                directories[:] = [name for name in directories if check_name(name)]
                for name in names:
                    path = Path(folder, name)
                    if check_name(name) and path.is_file() and not path.is_symlink():
                        yield path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


class Sessions:
    """The sessions of one GUI app and their work root.

    Parameters
    ----------
    work_root : Path or None
        Directory that holds the session directories; ``None`` creates
        ``<tmp>/hydrolog-gui-<pid>-<random>/`` (mode 0700), removed by :meth:`close`.
        A given directory is created if missing and kept by :meth:`close`.
    limits : Limits
        The limits (:attr:`Limits.sessions` and :attr:`Limits.idle_s` apply here).
    clock : callable, optional
        Monotonic clock [s]; tests pass their own.
    """

    def __init__(
        self,
        *,
        work_root: Path | None,
        limits: Limits,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if work_root is None:
            created = tempfile.mkdtemp(prefix=f"hydrolog-gui-{os.getpid()}-")
            self.root = Path(created).resolve()
            self._owned = True
        else:
            Path(work_root).mkdir(mode=0o700, parents=True, exist_ok=True)
            self.root = Path(work_root).resolve()
            self._owned = False
        self.limits = limits
        self._clock = clock
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._closed = False

    def get(self, session_id: str | None) -> Session | None:
        """Return the session of ``session_id`` and mark it used, or ``None``."""
        self.sweep()
        if session_id is None or _SESSION_ID.fullmatch(session_id) is None:
            return None
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_used = self._clock()
            self._sessions.move_to_end(session_id)
        return session

    def create(self) -> Session:
        """Start a new session, removing the least recently used idle one if full.

        Returns
        -------
        Session
            The new session with its empty ``in/`` and ``out/``.

        Raises
        ------
        ConflictError
            If :attr:`Limits.sessions` sessions exist and all of them are busy
            (``details.reason`` ``too_many_sessions``), or the server is stopping
            (``stopping``).
        """
        if self._closed:
            raise ConflictError(
                "The GUI server is stopping", details={"reason": "stopping"}
            )
        self.sweep()
        while len(self._sessions) >= self.limits.sessions:
            idle = next((s for s in self._sessions.values() if not s.busy), None)
            if idle is None:
                raise ConflictError(
                    f"All {self.limits.sessions} sessions of the GUI server are busy",
                    details={
                        "reason": "too_many_sessions",
                        "limit": self.limits.sessions,
                    },
                    hint="Try again when a computation has finished.",
                )
            self.remove(idle)
        session_id = secrets.token_urlsafe(32)
        directory = self.root / session_id
        directory.mkdir(mode=0o700)
        for area in AREAS:
            (directory / area).mkdir(mode=0o700)
        session = Session(session_id, directory, self._clock())
        self._sessions[session_id] = session
        return session

    def remove(self, session: Session) -> None:
        """Forget a session and delete its directory."""
        self._sessions.pop(session.id, None)
        shutil.rmtree(session.directory, ignore_errors=True)

    def sweep(self) -> None:
        """Remove the sessions idle for longer than :attr:`Limits.idle_s`."""
        now = self._clock()
        for session in list(self._sessions.values()):
            if not session.busy and now - session.last_used > self.limits.idle_s:
                self.remove(session)

    def __len__(self) -> int:
        """Return the number of sessions."""
        return len(self._sessions)

    def close(self) -> None:
        """Remove every session; remove the work root too when it was created here."""
        self._closed = True
        for session in list(self._sessions.values()):
            self.remove(session)
        if self._owned:
            shutil.rmtree(self.root, ignore_errors=True)
