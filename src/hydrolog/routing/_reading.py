"""Reading and writing the objects of a network document (ADR-0012).

A rainfall, a runoff model, a watershed and every node are JSON objects that a class
reads and writes itself. The helpers here are what those classes share: the errors of
an object that is not what the class takes, and the arguments of a constructor, which
name the fields of the object and give the defaults that a document leaves out.

An error of a nested object names the object in its message and in ``details.field``
(``rainfall.total_mm``), so that the document can be corrected without a search.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, NoReturn

from hydrolog.exceptions import InvalidParameterError
from hydrolog.routing._checks import shown

__all__ = [
    "as_object",
    "check_fields",
    "constructor_arguments",
    "constructor_defaults",
    "fail",
    "required",
    "within",
    "without_defaults",
]


def fail(
    message: str, *, reason: str, hint: str | None = None, **details: object
) -> NoReturn:
    """Raise the error of an object that is not valid."""
    raise InvalidParameterError(
        message, details={"reason": reason, **details}, hint=hint
    )


def as_object(value: object, subject: str) -> Mapping[str, Any]:
    """Return ``value`` when it is a JSON object, else refuse it (``type``)."""
    if not isinstance(value, Mapping):
        fail(
            f"{subject} must be an object, not {type(value).__name__}",
            reason="type",
            hint="Write it as a JSON object: {...}.",
        )
    return value


def check_fields(
    subject: str, fields: Mapping[str, Any], allowed: Sequence[str]
) -> None:
    """Refuse a field that the object does not take (``reason`` ``unknown_field``).

    Parameters
    ----------
    subject : str
        What the object is, for the message (``"A design rainfall"``).
    fields : mapping
        The object as the document has it.
    allowed : sequence of str
        The names of the fields that it takes.
    """
    for key in fields:
        if key not in allowed:
            fail(
                f"{subject} takes no {shown(key)}",
                reason="unknown_field",
                hint=f"{subject} takes {', '.join(allowed)}.",
                field=shown(key),
                allowed=list(allowed),
            )


def required(
    subject: str, fields: Mapping[str, Any], name: str, *, hint: str | None = None
) -> Any:
    """Return the field ``name``, or refuse the object for lacking it.

    A field whose value is ``None`` is not given. The error has ``reason``
    ``missing_field`` and ``details.field``.
    """
    value = fields.get(name)
    if value is None:
        fail(
            f"{subject} needs {name!r}",
            reason="missing_field",
            hint=hint,
            field=name,
        )
    return value


@contextmanager
def within(path: str) -> Iterator[None]:
    """Name ``path`` in the error of whatever is read inside the block.

    The message gets the path in front (``rainfall: Option 'total_mm'...``) and
    ``details.option`` and ``details.field``, when the error has them, become
    ``rainfall.total_mm``; an error that names no field gets ``details.field`` the
    path itself.

    Parameters
    ----------
    path : str
        Where the object is in its node or document (``"rainfall"``, ``"runoff"``).
    """
    try:
        yield
    except InvalidParameterError as exc:
        details = dict(exc.details)
        named = False
        for key in ("option", "field"):
            if isinstance(details.get(key), str):
                details[key] = f"{path}.{details[key]}"
                named = True
        if not named:
            details["field"] = path
        raise InvalidParameterError(
            f"{path}: {exc}", details=details, hint=exc.hint
        ) from exc


def constructor_arguments(cls: type) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the names of the arguments of a constructor and those it requires.

    The names are those of the fields of the object in a document: a class is read by
    handing it the fields that are in its signature.
    """
    arguments = [
        item
        for item in inspect.signature(cls).parameters.values()
        if item.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    return (
        tuple(item.name for item in arguments),
        tuple(
            item.name for item in arguments if item.default is inspect.Parameter.empty
        ),
    )


def constructor_defaults(cls: type) -> dict[str, object]:
    """Return the defaults of the arguments of a constructor; ``None`` is none."""
    return {
        name: item.default
        for name, item in inspect.signature(cls).parameters.items()
        if item.default is not inspect.Parameter.empty and item.default is not None
    }


def without_defaults(cls: type, values: Mapping[str, Any]) -> dict[str, Any]:
    """Return the ``values`` that are not the default of the constructor of ``cls``.

    A document leaves a default out, so that an object and its document are the same
    whether the default was written or not.
    """
    defaults = constructor_defaults(cls)
    return {
        name: value
        for name, value in values.items()
        if name not in defaults or value != defaults[name]
    }
