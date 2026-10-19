"""Helpers shared by the operations of the analysis groups.

Private module (not part of the public operation layer). It holds what the operations
of ``stats``, ``hydrometrics`` and ``network`` need:

* loading a series from inline values or a file, dropping its missing values with a
  notice (:func:`load_valid_series`) and requiring a minimum number of observations
  (:func:`require_count`);
* the checks the catalog applies to options (:func:`check_choice`,
  :func:`check_open_unit_interval`), repeated here because the operations are also
  called directly from Python, without the catalog in front of them.
"""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from hydrolog.catalog.envelope import Notice
from hydrolog.catalog.inputs import Series, load_series
from hydrolog.exceptions import CalculationError, InvalidParameterError

__all__ = [
    "check_choice",
    "check_open_unit_interval",
    "drop_missing",
    "load_valid_series",
    "require_count",
]


def check_choice(option: str, value: str, allowed: Sequence[str]) -> str:
    """Require ``value`` to be one of ``allowed``.

    Parameters
    ----------
    option : str
        Name of the option (reported in ``details``).
    value : str
        Value to check.
    allowed : sequence of str
        Allowed values.

    Returns
    -------
    str
        ``value``, unchanged.

    Raises
    ------
    InvalidParameterError
        If ``value`` is not allowed (``details``: ``option``, ``reason="choice"``,
        ``allowed``, ``value``).
    """
    if value not in allowed:
        listed = ", ".join(allowed)
        raise InvalidParameterError(
            f"Option {option!r}: {value!r} is not one of: {listed}",
            details={
                "option": option,
                "reason": "choice",
                "allowed": list(allowed),
                "value": str(value),
            },
            hint=f"Allowed values: {listed}.",
        )
    return value


def check_open_unit_interval(option: str, value: float) -> float:
    """Require ``0 < value < 1`` (a probability that is neither 0 nor 1).

    Parameters
    ----------
    option : str
        Name of the option (reported in ``details``).
    value : float
        Value to check.

    Returns
    -------
    float
        ``value`` as a ``float``.

    Raises
    ------
    InvalidParameterError
        If ``value`` is not a finite number in the open interval ``(0, 1)``
        (``details``: ``option``, ``reason``, ``value``).
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = math.nan
    if not (math.isfinite(number) and 0.0 < number < 1.0):
        raise InvalidParameterError(
            f"Option {option!r}: must be a number in the open interval (0, 1), "
            f"got {value!r}",
            details={"option": option, "reason": "range", "value": str(value)},
        )
    return number


def drop_missing(series: Series) -> tuple[Series, list[Notice]]:
    """Remove the missing values (``NaN``) of a series.

    Parameters
    ----------
    series : Series
        Series as loaded by :func:`hydrolog.catalog.inputs.load_series`.

    Returns
    -------
    Series
        The series without missing values (dates stay aligned).
    list of Notice
        One ``missing_values_removed`` warning when values were removed, else empty.

    Raises
    ------
    CalculationError
        If every value is missing.
    """
    missing = series.n_missing
    if missing == 0:
        return series, []
    if missing == len(series):
        raise CalculationError(
            f"All {missing} values of the series are missing; nothing to analyse",
            details={"n_values": len(series), "n_missing": missing},
            hint="Check the value column: it holds no numbers.",
        )
    where = ""
    if series.dates is not None:
        first = int(np.flatnonzero(np.isnan(series.values))[0])
        where = f" (the first on {series.dates[first]})"
    notice = Notice(
        "warning",
        "missing_values_removed",
        f"{missing} of {len(series)} values are missing (NaN) and were removed "
        f"before the analysis{where}",
    )
    return series.without_missing(), [notice]


def load_valid_series(
    *,
    values: Sequence[object] | NDArray[Any] | None = None,
    dates: Sequence[object] | NDArray[Any] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    require_dates: bool = False,
) -> tuple[Series, list[Notice]]:
    """Load a series from inline values or a file and drop its missing values.

    Parameters
    ----------
    values, dates, input_file, value_column, date_column
        Source of the series, see :func:`hydrolog.catalog.inputs.load_series`.
    require_dates : bool, optional
        Require dates (inline ``dates`` or ``date_column``), by default ``False``.

    Returns
    -------
    Series
        Series without missing values.
    list of Notice
        Notice about the removed missing values, if any.

    Raises
    ------
    InvalidParameterError, NotFoundError, InputDataError
        As raised by :func:`hydrolog.catalog.inputs.load_series`.
    CalculationError
        If every value of the series is missing.
    """
    series = load_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=require_dates,
    )
    return drop_missing(series)


def require_count(count: int, minimum: int, what: str, *, unit: str = "values") -> None:
    """Require a minimum number of observations.

    Parameters
    ----------
    count : int
        Number of observations available.
    minimum : int
        Smallest number the computation can work with.
    what : str
        Name of the computation for the message (``"Mann-Kendall test"``).
    unit : str, optional
        What is counted (``"values"``, ``"annual maxima"``...).

    Raises
    ------
    CalculationError
        If ``count < minimum`` (``details``: ``count``, ``minimum``).
    """
    if count < minimum:
        raise CalculationError(
            f"{what} needs at least {minimum} {unit}, got {count}",
            details={"count": count, "minimum": minimum},
            hint="Provide a longer series.",
        )
