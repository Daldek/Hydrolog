"""Checks of the parameters of the routing models.

They raise :class:`~hydrolog.exceptions.InvalidParameterError` with the ``details``
vocabulary of the catalog (``option``, ``reason`` and the bound), so that an error of a
library class looks like the error the same value gives at the command line.
"""

from __future__ import annotations

import math
import numbers

from hydrolog.exceptions import InvalidParameterError

__all__ = ["in_range", "positive", "whole_number"]


def _shown(value: float) -> float | str:
    return value if math.isfinite(value) else str(value)


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
