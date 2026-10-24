"""Checks of the parameters of the routing models.

They raise :class:`~hydrolog.exceptions.InvalidParameterError` with the ``details``
vocabulary of the catalog (``option``, ``reason`` and the bound), so that an error of a
library class looks like the error the same value gives at the command line.
"""

from __future__ import annotations

import math

from hydrolog.exceptions import InvalidParameterError

__all__ = ["positive"]


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
