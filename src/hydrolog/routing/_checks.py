"""Checks of the parameters of the routing models.

They raise :class:`~hydrolog.exceptions.InvalidParameterError` with the ``details``
vocabulary of the catalog (``option``, ``reason`` and the bound), so that an error of a
library class looks like the error the same value gives at the command line.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Collection, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog.exceptions import InvalidParameterError

__all__ = ["as_array", "in_range", "one_complete_group", "positive", "whole_number"]


def _shown(value: float) -> float | str:
    return value if math.isfinite(value) else str(value)


def as_array(value: ArrayLike, option: str) -> NDArray[np.float64]:
    """Return ``value`` as a new ``float64`` array.

    Parameters
    ----------
    value : array_like
        The list of numbers.
    option : str
        Its name, for the error (``details.option``).

    Returns
    -------
    numpy.ndarray
        A copy of the values.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` when the values are not numbers.
    """
    try:
        return np.array(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise InvalidParameterError(
            f"{option} must be a list of numbers",
            details={"option": option, "reason": "type"},
        ) from exc


def positive(value: float, option: str) -> float:
    """Return ``value`` as a float when it is a finite number above zero.

    Parameters
    ----------
    value : float
        The parameter.
    option : str
        Its name, for the error (``details.option``).

    Returns
    -------
    float
        The value.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``not_finite`` or ``exclusive_minimum`` (bound 0).
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or math.isnan(value)
    ):
        raise InvalidParameterError(
            f"Option {option!r}: must be a number > 0, got {value!r}",
            details={"option": option, "reason": "type", "value": str(value)},
        )
    if not math.isfinite(value):
        raise InvalidParameterError(
            f"Option {option!r}: must be a finite number, got {value}",
            details={"option": option, "reason": "not_finite", "value": str(value)},
        )
    if value <= 0.0:
        raise InvalidParameterError(
            f"Option {option!r}: must be > 0, got {value}",
            details={
                "option": option,
                "reason": "exclusive_minimum",
                "exclusive_minimum": 0.0,
                "value": _shown(value),
            },
        )
    return float(value)


def in_range(
    value: float,
    option: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Return ``value`` as a float when it is a finite number within the bounds.

    Parameters
    ----------
    value : float
        The parameter.
    option : str
        Its name, for the error (``details.option``).
    minimum, maximum : float, optional
        Inclusive bounds.

    Returns
    -------
    float
        The value.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type``, ``not_finite``, ``minimum`` or ``maximum``.
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or math.isnan(value)
    ):
        raise InvalidParameterError(
            f"Option {option!r}: must be a number, got {value!r}",
            details={"option": option, "reason": "type", "value": str(value)},
        )
    if not math.isfinite(value):
        raise InvalidParameterError(
            f"Option {option!r}: must be a finite number, got {value}",
            details={"option": option, "reason": "not_finite", "value": str(value)},
        )
    if minimum is not None and value < minimum:
        raise InvalidParameterError(
            f"Option {option!r}: must be >= {minimum:g}, got {value:g}",
            details={
                "option": option,
                "reason": "minimum",
                "minimum": minimum,
                "value": value,
            },
        )
    if maximum is not None and value > maximum:
        raise InvalidParameterError(
            f"Option {option!r}: must be <= {maximum:g}, got {value:g}",
            details={
                "option": option,
                "reason": "maximum",
                "maximum": maximum,
                "value": value,
            },
        )
    return float(value)


def whole_number(value: int, option: str, *, minimum: int = 1) -> int:
    """Return ``value`` when it is an integer of at least ``minimum``.

    Parameters
    ----------
    value : int
        The parameter; a boolean or a number with a fraction is refused.
    option : str
        Its name, for the error (``details.option``).
    minimum : int, optional
        Inclusive lower bound, by default 1.

    Returns
    -------
    int
        The value.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``type`` or ``minimum``.
    """
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise InvalidParameterError(
            f"Option {option!r}: must be an integer, got {value!r}",
            details={
                "option": option,
                "reason": "type",
                "expected": "integer",
                "value": str(value),
            },
        )
    if value < minimum:
        raise InvalidParameterError(
            f"Option {option!r}: must be >= {minimum}, got {value}",
            details={
                "option": option,
                "reason": "minimum",
                "minimum": minimum,
                "value": int(value),
            },
        )
    return int(value)


def one_complete_group(
    given: Collection[str], groups: Sequence[Sequence[str]], what: str
) -> int:
    """Return the index of the one group whose options are all given.

    The error has the shape of the catalog's ``one_of`` rule, so that a class and a
    command refuse the same options in the same words.

    Parameters
    ----------
    given : collection of str
        The names of the options that have a value.
    groups : sequence of sequence of str
        The alternatives; each is a set of options that go together.
    what : str
        What takes the options, for the message (``"The reach"``).

    Returns
    -------
    int
        The index of the complete group.

    Raises
    ------
    InvalidParameterError
        With ``details.reason`` ``one_of`` (``groups``, ``given``, and ``missing`` for
        the closest group) when no group or several groups are complete.
    """
    names = set(given)
    complete = [index for index, group in enumerate(groups) if names.issuperset(group)]
    if len(complete) == 1:
        return complete[0]
    pretty = " or ".join("+".join(group) for group in groups)
    details: dict[str, object] = {
        "reason": "one_of",
        "groups": [list(group) for group in groups],
        "given": [
            name
            for name in dict.fromkeys(item for group in groups for item in group)
            if name in names
        ],
    }
    if complete:
        raise InvalidParameterError(
            f"{what} takes exactly one group of options ({pretty}), but several are "
            "given",
            details={"option": groups[complete[1]][0], **details},
            hint=f"Give only one of: {pretty}.",
        )
    closest = max(groups, key=lambda group: len(names.intersection(group)))
    missing = [name for name in closest if name not in names]
    message = f"{what} needs exactly one complete group of options: {pretty}"
    if names.intersection(closest):
        message += f"; missing for the closest group: {', '.join(missing)}"
    details["missing"] = missing
    raise InvalidParameterError(
        message,
        details={"option": missing[0], **details},
        hint=f"Give one complete group: {pretty}.",
    )
