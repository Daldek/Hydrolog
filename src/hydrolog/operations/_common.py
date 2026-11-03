"""Helpers shared by the operations of the groups ``cn`` ... ``hydrograph``.

They raise :class:`~hydrolog.exceptions.InvalidParameterError` with the same
``details`` vocabulary as :func:`hydrolog.catalog.validate_command` (``option`` and
``reason``), so an error raised by an operation looks like one raised by the
catalog.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Mapping, Sequence
from typing import Any

from hydrolog.exceptions import InvalidParameterError


def option_error(
    option: str,
    reason: str,
    message: str,
    *,
    hint: str | None = None,
    **details: Any,
) -> InvalidParameterError:
    """Build a validation error about one option.

    Parameters
    ----------
    option : str
        Name of the offending option (``details["option"]``).
    reason : str
        Machine-readable reason (``required``, ``one_of``, ``choice``,
        ``not_applicable``, ``conflict``, ``type``...).
    message : str
        English message.
    hint : str, optional
        One-line remediation suggestion.
    **details
        Further JSON-compatible ``details`` entries.

    Returns
    -------
    InvalidParameterError
        The exception to ``raise``.
    """
    return InvalidParameterError(
        message,
        details={"option": option, "reason": reason, **details},
        hint=hint,
    )


def check_choice(option: str, value: object, allowed: Sequence[str]) -> str:
    """Return ``value`` when it is one of ``allowed``.

    Parameters
    ----------
    option : str
        Option name for the error.
    value : object
        Value to check.
    allowed : sequence of str
        Allowed values.

    Returns
    -------
    str
        The value.

    Raises
    ------
    InvalidParameterError
        With ``reason = "choice"`` and the allowed values.
    """
    if not isinstance(value, str) or value not in allowed:
        raise option_error(
            option,
            "choice",
            f"Option {option!r}: {value!r} is not one of {', '.join(allowed)}",
            allowed=list(allowed),
            value=value if isinstance(value, str | int | float | bool) else str(value),
        )
    return value


def require_option(option: str, value: Any, *, when: str) -> Any:
    """Return ``value``, or fail when it was not given.

    Parameters
    ----------
    option : str
        Option name for the error.
    value : object
        Value, ``None`` when not given.
    when : str
        Condition that makes the option necessary (``"hietogram_type is beta"``).

    Returns
    -------
    object
        The value.

    Raises
    ------
    InvalidParameterError
        With ``reason = "required"``.
    """
    if value is None:
        raise option_error(
            option,
            "required",
            f"Option {option!r} is required when {when}",
        )
    return value


def forbid_options(
    given: Mapping[str, object], *, context: str, hint: str | None = None
) -> None:
    """Fail when an option that does not apply to the chosen variant is given.

    Parameters
    ----------
    given : Mapping[str, object]
        Option values that must be absent (``None``) in this variant.
    context : str
        The variant, for the message (``"hietogram_type is block"``).
    hint : str, optional
        Remediation suggestion.

    Raises
    ------
    InvalidParameterError
        With ``reason = "not_applicable"`` naming the first option that is given.
    """
    for option, value in given.items():
        if value is not None:
            raise option_error(
                option,
                "not_applicable",
                f"Option {option!r} does not apply when {context}",
                hint=hint,
            )


def select_group(
    values: Mapping[str, object],
    groups: Mapping[str, Sequence[str]],
    *,
    extra: Mapping[str, str | Sequence[str]] | None = None,
) -> str:
    """Pick the one complete group of alternative options.

    Mirrors the ``one_of`` rule of the catalog and goes one step further: an option
    that belongs to another alternative than the chosen one is rejected instead of
    being ignored silently.

    Parameters
    ----------
    values : Mapping[str, object]
        Value of every option of every group and of ``extra`` (``None`` = not
        given).
    groups : Mapping[str, Sequence[str]]
        Alternative name -> the options that must all be given for it.
    extra : Mapping[str, str or sequence of str], optional
        Options that refine alternatives without selecting one (option -> the
        alternative name, or the names of all alternatives they may accompany).

    Returns
    -------
    str
        Name of the chosen alternative.

    Raises
    ------
    InvalidParameterError
        With ``reason = "one_of"`` when no or several groups are complete, and
        ``reason = "not_applicable"`` for an option of another alternative.
    """
    group_options = {name: tuple(options) for name, options in groups.items()}
    owner: dict[str, set[str]] = {}
    for name, options in group_options.items():
        for option in options:
            owner.setdefault(option, set()).add(name)
    for option, names in (extra or {}).items():
        for name in [names] if isinstance(names, str) else names:
            owner.setdefault(option, set()).add(name)
    given = [option for option in owner if values.get(option) is not None]
    complete = [
        name
        for name, options in group_options.items()
        if all(values.get(option) is not None for option in options)
    ]
    if len(complete) != 1:
        pretty = " or ".join("+".join(options) for options in group_options.values())
        raise option_error(
            given[0] if given else next(iter(owner)),
            "one_of",
            f"Give exactly one complete group of options: {pretty}",
            groups=[list(options) for options in group_options.values()],
            given=given,
        )
    chosen = complete[0]
    chosen_options = "+".join(group_options[chosen])
    for option in given:
        if chosen not in owner[option]:
            raise option_error(
                option,
                "not_applicable",
                f"Option {option!r} does not apply with {chosen_options}",
                hint=f"{option!r} belongs to: {', '.join(sorted(owner[option]))}.",
            )
    return chosen


def real_number(option: str, value: object, *, index: int | None = None) -> float:
    """Return a finite real number, or fail with a ``type`` error.

    Parameters
    ----------
    option : str
        Option name for the error.
    value : object
        Value to convert (``bool`` and non-finite numbers are rejected).
    index : int, optional
        Position inside a list option, reported in the error.

    Returns
    -------
    float
        The value as ``float``.

    Raises
    ------
    InvalidParameterError
        With ``reason = "type"`` (``index`` for list items).
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, numbers.Real)
        or not math.isfinite(value)
    ):
        label = option if index is None else f"{option}[{index}]"
        extra: dict[str, Any] = {} if index is None else {"index": index}
        raise option_error(
            option,
            "type",
            f"Option {label!r} must be a finite number, got {value!r}",
            **extra,
        )
    return float(value)
