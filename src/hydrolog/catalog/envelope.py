"""Result envelope ``hydrolog-result/1`` and the return protocol of operations.

:func:`~hydrolog.catalog.run_command` wraps what an operation returns in a
:class:`CommandResult`, the one document that the CLI (``--json``), the MCP server
and Python callers share (Nogat ``result-1``, AGI-4.2)::

    {
      "schema": "hydrolog-result/1",
      "tool": "hydrolog",
      "version": "1.0.0",
      "command": "tc kirpich",
      "check": false,
      "status": "ok",
      "result": {"schema": "hydrolog-tc-kirpich/1", "...": "..."},
      "notices": [{"level": "warning", "code": "...", "message": "..."}],
      "inputs": {"length_km": 8.2, "slope_m_per_m": 0.023}
    }

``result`` is the domain document of the command: its ``to_dict()`` plus the
``schema`` key of the catalog entry (``Command.result_schema``). A command that
writes files lists them in ``result["files"]`` as ``{path, size_bytes, sha256,
status}`` (DEV-19.19, status ``written`` or ``replaced``). ``inputs`` (the normalized
options of the call) is a Hydrolog addition; ``page`` appears for paginated
collections. ``status`` is always ``"ok"``: a failing command raises (see
:func:`hydrolog.exceptions.error_document`) and leaves no partial state, and
Hydrolog has no batch commands, so there are no ``items``.

Return protocol of an operation
-------------------------------
An operation (a function of :mod:`hydrolog.operations`) returns either

1. **a plain result** -- a :class:`~hydrolog._serialization.JsonResultMixin`
   dataclass, a ``dict``, a ``list`` or a scalar; the envelope gets no notices and no
   files, except the files named by the optional ``output_files()`` method below; or
2. **an** :class:`OperationOutput` -- ``OperationOutput(result, notices, files)``:
   the wrapper carries the result together with the non-fatal :class:`Notice`
   objects (short series, values removed, extrapolation...) and the paths of the
   files the operation wrote.

A result object may additionally expose ``output_files()`` returning an iterable of
paths it wrote; these are added to ``result["files"]`` after the files of the
wrapper (duplicates removed). Every reported file must exist when the operation
returns: the envelope records its absolute ``path``, ``size_bytes`` and ``sha256``,
and a missing file is an ``io_error``. A file listed in ``OperationOutput.replaced``
has the status ``replaced`` (it existed before), every other one ``written``.

Notices are *non-fatal* observations. Anything that prevents a result is an
exception from :mod:`hydrolog.exceptions`, not a notice. The library reports many such
observations as Python ``UserWarning`` (short series, value outside the typical
range...); :func:`capture_warnings` turns them into notices inside an operation::

    with capture_warnings() as notices:
        result = FloodFrequencyAnalysis(maxima).fit_gev()
    return OperationOutput(result, notices)
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import threading
import warnings
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from hydrolog._serialization import to_jsonable
from hydrolog.exceptions import OutputError

RESULT_SCHEMA: Final = "hydrolog-result/1"
"""Value of the ``schema`` key of a serialized :class:`CommandResult`."""
TOOL: Final = "hydrolog"
"""Value of the ``tool`` key of a serialized :class:`CommandResult`."""
FileStatus = Literal["written", "replaced"]

NoticeLevel = Literal["info", "warning"]
NOTICE_LEVELS: Final[tuple[str, ...]] = ("info", "warning")

_NOTICE_CODE = re.compile(r"[a-z][a-z0-9_]*")
_HASH_CHUNK = 1 << 20
_WARNING_LOCK = threading.Lock()


@dataclass(frozen=True)
class Notice:
    """Non-fatal observation reported next to a result.

    Parameters
    ----------
    level : {"info", "warning"}
        Severity.
    code : str
        Stable machine-readable ``snake_case`` identifier (``"short_series"``).
    message : str
        Human-readable message (English).

    Raises
    ------
    ValueError
        If ``level`` is unknown, ``code`` is not ``snake_case`` or ``message`` is
        empty.
    """

    level: NoticeLevel
    code: str
    message: str

    def __post_init__(self) -> None:
        """Validate the field values."""
        if self.level not in NOTICE_LEVELS:
            raise ValueError(
                f"Unknown notice level {self.level!r}; "
                f"allowed: {', '.join(NOTICE_LEVELS)}"
            )
        if not _NOTICE_CODE.fullmatch(self.code):
            raise ValueError(f"Notice code {self.code!r} must be snake_case")
        if not self.message.strip():
            raise ValueError("Notice message must not be empty")

    def to_dict(self) -> dict[str, str]:
        """Return ``{"level", "code", "message"}``."""
        return {"level": self.level, "code": self.code, "message": self.message}


@dataclass(frozen=True)
class FileRecord:
    """File written by a command, as listed in ``result["files"]`` (DEV-19.19).

    Parameters
    ----------
    path : str
        Absolute path of the file.
    size_bytes : int
        Size of the file in bytes.
    sha256 : str
        Hex SHA-256 digest of the file content.
    status : {"written", "replaced"}, optional
        ``"replaced"`` when the file existed before (``force``), else ``"written"``.
    """

    path: str
    size_bytes: int
    sha256: str
    status: FileStatus = "written"

    def to_dict(self) -> dict[str, Any]:
        """Return ``{"path", "size_bytes", "sha256", "status"}``."""
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "status": self.status,
        }


@dataclass(frozen=True)
class OperationOutput:
    """Operation result together with its notices and written files.

    Parameters
    ----------
    result : object
        The result (a ``JsonResultMixin`` dataclass, ``dict``, ``list``...).
    notices : sequence of Notice, optional
        Non-fatal observations.
    files : sequence of str or os.PathLike, optional
        Paths of the files the operation wrote (absolute; they must exist).
    replaced : sequence of str or os.PathLike, optional
        The files among ``files`` that existed before and were replaced.
    check : bool, optional
        The result is the plan of a ``check`` run, nothing was written.
    page : Mapping, optional
        ``{"total", "next_cursor", "truncated"}`` of a paginated collection.
    """

    result: Any
    notices: Sequence[Notice] = ()
    files: Sequence[str | os.PathLike[str]] = ()
    replaced: Sequence[str | os.PathLike[str]] = ()
    check: bool = False
    page: Mapping[str, Any] | None = None


def _warning_code(category: type[Warning]) -> str:
    """``UserWarning`` -> ``user_warning``."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", category.__name__).lower()


@contextlib.contextmanager
def capture_warnings(
    categories: tuple[type[Warning], ...] = (UserWarning,),
) -> Iterator[list[Notice]]:
    """Turn Python warnings raised inside the block into notices.

    The library signals non-fatal observations (a short series, a value outside the
    typical range...) with ``warnings.warn``. Inside this block every warning of the
    given ``categories`` is recorded instead of printed and, when the block ends,
    appended to the yielded list as a :class:`Notice` (level ``"warning"``, code the
    snake_case category such as ``"user_warning"``, text the message; identical
    warnings once). Warnings of other categories are re-issued unchanged after the
    block. Blocks are serialized by a lock because ``warnings.catch_warnings`` changes
    process-wide state; keep the block to the computation itself.

    Parameters
    ----------
    categories : tuple of type, optional
        Warning classes to capture, by default ``(UserWarning,)``.

    Yields
    ------
    list of Notice
        Empty inside the block; filled when the block ends, so read it afterwards.

    Examples
    --------
    >>> import warnings
    >>> with capture_warnings() as notices:
    ...     warnings.warn("only 5 years of data", UserWarning)
    >>> [(n.level, n.code, n.message) for n in notices]
    [('warning', 'user_warning', 'only 5 years of data')]
    """
    notices: list[Notice] = []
    with _WARNING_LOCK:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            yield notices
        seen: dict[Notice, None] = {}
        for item in caught:
            if issubclass(item.category, categories):
                text = str(item.message).strip() or item.category.__name__
                seen.setdefault(Notice("warning", _warning_code(item.category), text))
            else:
                warnings.warn_explicit(
                    item.message, item.category, item.filename, item.lineno
                )
        notices.extend(seen)


def sha256_file(path: str | os.PathLike[str]) -> str:
    """Return the hex SHA-256 digest of a file.

    Parameters
    ----------
    path : str or os.PathLike
        File to hash.

    Returns
    -------
    str
        64-character lowercase hex digest.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while chunk := stream.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _file_records(
    paths: Iterable[str | os.PathLike[str]],
    replaced: Iterable[str | os.PathLike[str]] = (),
) -> tuple[FileRecord, ...]:
    replaced_paths = {os.path.abspath(os.fspath(item)) for item in replaced}
    records: dict[str, FileRecord] = {}
    for item in paths:
        path = os.path.abspath(os.fspath(item))
        if path in records:
            continue
        if not os.path.isfile(path):
            raise OutputError(
                f"The operation reported an output file that does not exist: {path}",
                details={"path": path},
            )
        records[path] = FileRecord(
            path=path,
            size_bytes=os.path.getsize(path),
            sha256=sha256_file(path),
            status="replaced" if path in replaced_paths else "written",
        )
    return tuple(records.values())


@dataclass(frozen=True)
class CommandResult:
    """Envelope of a successful command run (``hydrolog-result/1``).

    Parameters
    ----------
    command : str
        Catalog name of the command (``"tc kirpich"``).
    inputs : Mapping[str, Any]
        Normalized options the operation was called with (defaults applied, paths
        resolved to absolute).
    result : object
        What the operation returned; serialized by :meth:`to_dict`.
    result_schema : str
        Id of the domain document of the command (``"hydrolog-tc-kirpich/1"``); the
        ``schema`` key of the serialized ``result``.
    files : tuple of FileRecord, optional
        Files the command wrote, with size and SHA-256; listed in ``result["files"]``.
    notices : tuple of Notice, optional
        Non-fatal observations of the operation.
    check : bool, optional
        The run was a plan without effects.
    page : Mapping, optional
        Pagination of a collection result.
    """

    command: str
    inputs: Mapping[str, Any]
    result: Any
    result_schema: str
    files: tuple[FileRecord, ...] = ()
    notices: tuple[Notice, ...] = ()
    check: bool = False
    page: Mapping[str, Any] | None = None

    @property
    def status(self) -> Literal["ok"]:
        """str: always ``"ok"``; a failing command raises instead."""
        return "ok"

    @classmethod
    def from_output(
        cls,
        command: str,
        inputs: Mapping[str, Any],
        output: object,
        result_schema: str,
    ) -> CommandResult:
        """Build the envelope from what an operation returned.

        Parameters
        ----------
        command : str
            Catalog name of the command.
        inputs : Mapping[str, Any]
            Normalized options of the call.
        output : object
            Return value of the operation: a result or an :class:`OperationOutput`
            (see the module docstring for the protocol).
        result_schema : str
            Id of the domain document of the command.

        Returns
        -------
        CommandResult
            Envelope with the unwrapped result, the notices and the written files.

        Raises
        ------
        OutputError
            If a reported output file does not exist.
        """
        notices: tuple[Notice, ...] = ()
        paths: list[str | os.PathLike[str]] = []
        replaced: list[str | os.PathLike[str]] = []
        check = False
        page: Mapping[str, Any] | None = None
        result = output
        if isinstance(output, OperationOutput):
            result = output.result
            notices = tuple(output.notices)
            paths.extend(output.files)
            replaced.extend(output.replaced)
            check = output.check
            page = output.page
        reporter = getattr(result, "output_files", None)
        if callable(reporter):
            paths.extend(reporter())
        return cls(
            command=command,
            inputs=inputs,
            result=result,
            result_schema=result_schema,
            files=_file_records(paths, replaced),
            notices=notices,
            check=check,
            page=page,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the envelope to a JSON-compatible ``hydrolog-result/1`` dict.

        Returns
        -------
        dict
            ``schema``, ``tool``, ``version``, ``command``, ``check``, ``status``,
            ``result`` (via :func:`~hydrolog._serialization.to_jsonable`, a document
            with its ``schema`` first and, when files were written, ``files``),
            ``notices``, ``inputs`` and, for a collection, ``page``.

        Raises
        ------
        TypeError
            If the result holds an object that has no JSON form, or is not a
            document (a mapping).
        """
        import hydrolog

        document = to_jsonable(self.result)
        if not isinstance(document, dict):
            raise TypeError(
                f"The result of {self.command!r} must be a document (a mapping), "
                f"got {type(document).__name__}"
            )
        domain = {"schema": self.result_schema, **document}
        if self.files:
            domain["files"] = [record.to_dict() for record in self.files]
        envelope: dict[str, Any] = {
            "schema": RESULT_SCHEMA,
            "tool": TOOL,
            "version": hydrolog.__version__,
            "command": self.command,
            "check": self.check,
            "status": self.status,
            "result": domain,
            "notices": [notice.to_dict() for notice in self.notices],
            "inputs": to_jsonable(dict(self.inputs)),
        }
        if self.page is not None:
            envelope["page"] = to_jsonable(dict(self.page))
        return envelope

    def to_json(self, indent: int | None = None) -> str:
        """Serialize the envelope to JSON text.

        Parameters
        ----------
        indent : int, optional
            Indentation of the output; ``None`` gives a single line.

        Returns
        -------
        str
            UTF-8-safe JSON (``ensure_ascii=False``, no ``NaN``).
        """
        return json.dumps(
            self.to_dict(), ensure_ascii=False, allow_nan=False, indent=indent
        )
