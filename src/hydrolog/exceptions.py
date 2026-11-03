"""Exceptions and the error-code registry of Hydrolog.

Every :class:`HydrologError` carries a machine-readable ``code`` from
:data:`ERROR_CODES`, JSON-compatible ``details`` and an optional one-line
``hint``. Each exception class has a default code (:attr:`HydrologError.default_code`);
a raise site may pass another registered code with ``code=``. The registry maps
every code to a Polish and an English title and to the CLI exit code, so the CLI,
the MCP server and Python callers report the same error the same way (see
:func:`error_document`, the ``hydrolog-error/1`` document). The registry is the
Nogat error registry (ERR-3): ``hydrolog._errors`` is generated from the copy in
``schemas/nogat/error_registry.json``.

Existing call sites such as ``raise InvalidParameterError("message")`` keep working
unchanged: ``code``, ``details`` and ``hint`` are optional keyword-only arguments.

Notes
-----
Messages are English (as everywhere in the library); only the registry titles are
localized (``lang="pl"`` or ``"en"``). :class:`InvalidParameterError` is also a
:class:`ValueError` (which several modules raised for invalid arguments before the
registry existed), so existing ``except ValueError`` handlers keep working;
:func:`error_document` checks :class:`HydrologError` first, so it never reports such
an error as a bug.
"""

from __future__ import annotations

import copy
import errno
import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, ClassVar, Final, Literal, cast

from hydrolog._errors import CODES, ErrorCodeName

__all__ = [
    "ERROR_CODES",
    "ERROR_SCHEMA",
    "CalculationError",
    "ConflictError",
    "ErrorCode",
    "ErrorSpec",
    "ForbiddenPathError",
    "HydrologError",
    "InputDataError",
    "InvalidParameterError",
    "MissingDependencyError",
    "NotFoundError",
    "OutputError",
    "error_document",
]

ErrorCode = ErrorCodeName
"""Name of a registry code that a CLI or MCP call can end with."""

ERROR_SCHEMA: Final = "hydrolog-error/1"
"""Value of the ``schema`` key of an error document."""


@dataclass(frozen=True)
class ErrorSpec:
    """Registry entry describing one error code.

    Attributes
    ----------
    code : ErrorCode
        Machine-readable error code.
    title : str
        Short Polish title.
    title_en : str
        Short English title.
    exit_code : int
        Exit code of the CLI for this error.
    """

    code: ErrorCode
    title: str
    title_en: str
    exit_code: int


_USED_CODES: Final = (
    "internal_error",
    "validation_error",
    "not_found",
    "conflict",
    "missing_dependency",
    "data_error",
    "io_error",
    "forbidden",
    "calculation_error",
    "cancelled",
    "terminated",
)
"""Registry codes that Hydrolog can end a call with (ERR-1: none of its own)."""

ERROR_CODES: Mapping[str, ErrorSpec] = MappingProxyType(
    {
        entry.code: ErrorSpec(
            code=cast(ErrorCode, entry.code),
            title=entry.title_pl,
            title_en=entry.title,
            exit_code=entry.exit_code,
        )
        for entry in CODES
        if entry.code in _USED_CODES and entry.exit_code is not None
    }
)
"""The registry codes Hydrolog uses, keyed by code (from ``_errors``, ERR-3)."""

_INTERNAL_HINT: Final = (
    "This is a bug: report it with the command, the inputs and the Hydrolog version."
)
_IO_HINT: Final = "Check that the path exists and that you have permission to use it."


class HydrologError(Exception):
    """Base exception for all Hydrolog errors.

    Parameters
    ----------
    message : str, optional
        Human-readable description (English); becomes ``str(exc)``.
    code : ErrorCode or None, optional
        Error code from :data:`ERROR_CODES`; ``None`` selects the class default
        (:attr:`default_code`).
    details : Mapping[str, object] or None, optional
        JSON-compatible context (e.g. ``option``, ``value``, ``allowed``,
        ``path``); stored as an independent deep copy.
    hint : str or None, optional
        One-line remediation suggestion shown next to the message.

    Attributes
    ----------
    default_code : ErrorCode
        Code used when the raise site does not pass ``code``.
    code : ErrorCode
        Registered error code of this instance.
    details : dict
        Copy of the given context; empty when none was given.
    hint : str or None
        Remediation suggestion, if any.

    Raises
    ------
    ValueError
        If ``code`` is not a key of :data:`ERROR_CODES`.

    Examples
    --------
    >>> exc = InvalidParameterError("CN must be 0-100, got 120")
    >>> exc.code
    'validation_error'
    >>> exc = InvalidParameterError("bad", details={"option": "cn"}, hint="Use 0-100.")
    >>> exc.details
    {'option': 'cn'}
    """

    default_code: ClassVar[ErrorCode] = "internal_error"

    code: ErrorCode
    details: dict[str, Any]
    hint: str | None

    def __init__(
        self,
        message: str = "",
        *,
        code: ErrorCode | None = None,
        details: Mapping[str, object] | None = None,
        hint: str | None = None,
    ) -> None:
        resolved = self.default_code if code is None else code
        if resolved not in ERROR_CODES:
            raise ValueError(
                f"Unknown error code {resolved!r}; allowed: {', '.join(ERROR_CODES)}"
            )
        super().__init__(message)
        self.code = resolved
        self.details = copy.deepcopy(dict(details or {}))
        self.hint = hint

    @property
    def exit_code(self) -> int:
        """int: CLI exit code of this error's code (see :data:`ERROR_CODES`)."""
        return ERROR_CODES[self.code].exit_code


class InvalidParameterError(HydrologError, ValueError):
    """Invalid parameter value.

    Default code: ``validation_error``. Also a :class:`ValueError`, so code written
    for the plain ``ValueError`` of earlier versions (``except ValueError``) keeps
    catching invalid arguments. Where an ``except`` chain must tell the two apart,
    list :class:`HydrologError` (or this class) before :class:`ValueError`.
    """

    default_code: ClassVar[ErrorCode] = "validation_error"


class ConflictError(HydrologError):
    """The operation conflicts with the current state (an output file exists).

    Default code: ``conflict``.
    """

    default_code: ClassVar[ErrorCode] = "conflict"


class CalculationError(HydrologError):
    """Error during calculation (valid-looking input, no result possible).

    Default code: ``calculation_error``.
    """

    default_code: ClassVar[ErrorCode] = "calculation_error"


class InputDataError(HydrologError):
    """Input data is unreadable or malformed (bad CSV/JSON, wrong columns, bad raster).

    Default code: ``data_error``.
    """

    default_code: ClassVar[ErrorCode] = "data_error"


class MissingDependencyError(HydrologError):
    """An optional extra (``[raster]``, ``[mcp]``, ...) is not installed.

    Default code: ``missing_dependency``.
    """

    default_code: ClassVar[ErrorCode] = "missing_dependency"


class ForbiddenPathError(HydrologError):
    """A path lies outside the allowed directories.

    Default code: ``forbidden``.
    """

    default_code: ClassVar[ErrorCode] = "forbidden"


class NotFoundError(HydrologError):
    """An input file or a command does not exist.

    Default code: ``not_found``.
    """

    default_code: ClassVar[ErrorCode] = "not_found"


class OutputError(HydrologError):
    """An output file cannot be written.

    Default code: ``io_error``.
    """

    default_code: ClassVar[ErrorCode] = "io_error"


def _jsonable_details(details: Mapping[str, object]) -> dict[str, Any]:
    """JSON-compatible copy of ``details``; unknown objects become their ``str``."""
    from hydrolog._serialization import to_jsonable

    try:
        converted: dict[str, Any] = to_jsonable(dict(details))
    except (TypeError, ValueError):
        return {str(key): _fallback_value(value) for key, value in details.items()}
    return converted


def _fallback_value(value: object) -> Any:
    if value is None or isinstance(value, str | bool | int):
        return value
    return str(value)


def _os_error_parts(exc: OSError) -> tuple[str, dict[str, Any]]:
    """Message and details of a file-system error (``errno`` name and ``path``)."""
    filename = exc.filename
    path = (
        os.fsdecode(filename)
        if isinstance(filename, str | bytes | os.PathLike)
        else None
    )
    reason = exc.strerror or str(exc)
    details: dict[str, Any] = {}
    if exc.errno is not None:
        details["errno"] = errno.errorcode.get(exc.errno, str(exc.errno))
    if path is not None:
        details["path"] = path
    return (f"{reason}: {path}" if path else reason), details


def error_document(
    exc: BaseException,
    command: str | None = None,
    lang: Literal["pl", "en"] = "en",
) -> dict[str, Any]:
    """Describe an exception as a ``hydrolog-error/1`` document.

    The document is the CLI stderr line (``--json``) and the content of an MCP
    ``isError`` result. A :class:`HydrologError` keeps its ``code``, ``hint``
    and ``details``. An :class:`OSError` that no operation wrapped is reported as
    ``io_error`` (``details``: ``errno`` name and ``path``). Every other exception
    is a bug in Hydrolog and becomes ``internal_error`` with the exception class
    in ``details["exception"]`` — including the ``ValueError``/``TypeError``
    raised by existing modules for invalid arguments.

    Parameters
    ----------
    exc : BaseException
        The exception to describe.
    command : str or None, optional
        Catalog name of the failed command (``"tc kirpich"``), if known.
    lang : {"pl", "en"}, optional
        Language of ``title`` (machine output is English, AGI-9.2); ``message`` and
        ``hint`` are always English.

    Returns
    -------
    dict
        ``{"schema": "hydrolog-error/1", "code", "title", "message", "hint",
        "details", "exit_code", "command"}``; JSON-compatible. ``hint`` and
        ``command`` are left out when there is none.

    Raises
    ------
    ValueError
        If ``lang`` is not ``"pl"`` or ``"en"``.

    Examples
    --------
    >>> doc = error_document(NotFoundError("No such command"), "x y", "en")
    >>> doc["code"], doc["title"], doc["exit_code"]
    ('not_found', 'Not found', 3)
    """
    if lang not in ("pl", "en"):
        raise ValueError(f"Unknown language {lang!r}; allowed: pl, en")
    details: Mapping[str, object]
    if isinstance(exc, HydrologError):
        code: ErrorCode = exc.code
        message = str(exc)
        hint = exc.hint
        details = exc.details
    elif isinstance(exc, OSError):
        code = "io_error"
        message, details = _os_error_parts(exc)
        hint = _IO_HINT
    else:
        code = "internal_error"
        message = f"{type(exc).__name__}: {exc}"
        hint = _INTERNAL_HINT
        details = {"exception": type(exc).__name__}
    spec = ERROR_CODES[code]
    document: dict[str, Any] = {
        "schema": ERROR_SCHEMA,
        "code": code,
        "title": spec.title_en if lang == "en" else spec.title,
        "message": message,
    }
    if hint:
        document["hint"] = hint
    document["details"] = _jsonable_details(details)
    document["exit_code"] = spec.exit_code
    if command is not None:
        document["command"] = command
    return document
