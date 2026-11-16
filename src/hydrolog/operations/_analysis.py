"""Helpers shared by the operations of the analysis groups.

Private module (not part of the public operation layer). It holds what the operations
of ``stats``, ``hydrometrics`` and ``network`` need:

* loading a series from inline values or a file, dropping its missing values with a
  notice (:func:`load_valid_series`) and requiring a minimum number of observations
  (:func:`require_count`) or a value at all (:func:`require_values`);
* the reference period of a dated series: the hydrological years ``first_year`` to
  ``last_year`` (:func:`check_years`, :func:`select_years`) and the notice of a period
  shorter than the recommended 30 years (:func:`reference_period_notices`);
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
from hydrolog.catalog.notices import notice
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "MIN_REFERENCE_YEARS",
    "check_choice",
    "check_open_unit_interval",
    "check_years",
    "drop_missing",
    "load_valid_series",
    "reference_period_notices",
    "require_count",
    "require_values",
    "select_years",
]

MIN_REFERENCE_YEARS = 30
"""Recommended shortest reference period [years]: a climatological standard normal
(WMO-No. 1203, 2017) and the author's minimum for characteristic values (plan
2026-11-13, D1)."""


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
        One ``missing_values_removed`` warning when values were removed (details
        ``missing``, ``total`` and ``first_date``, the date of the first missing value
        or ``None`` for a series without dates), else empty.

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
    first_date: str | None = None
    if series.dates is not None:
        first = int(np.flatnonzero(np.isnan(series.values))[0])
        first_date = str(series.dates[first])
    removed = notice(
        "missing_values_removed",
        missing=missing,
        total=len(series),
        first_date=first_date,
    )
    return series.without_missing(), [removed]


def load_valid_series(
    *,
    values: Sequence[object] | NDArray[Any] | None = None,
    dates: Sequence[object] | NDArray[Any] | None = None,
    years: Sequence[object] | NDArray[Any] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    year_column: str | None = None,
    require_dates: bool = False,
) -> tuple[Series, list[Notice]]:
    """Load a series from inline values or a file and drop its missing values.

    Parameters
    ----------
    values, dates, years, input_file, value_column, date_column, year_column
        Source of the series, see :func:`hydrolog.catalog.inputs.load_series`.
    require_dates : bool, optional
        Require dates (inline ``dates`` or ``date_column``), by default ``False``.

    Returns
    -------
    Series
        Series without missing values (its dates or years stay aligned).
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
        years=years,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        year_column=year_column,
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


def require_values(series: Series) -> Series:
    """Require at least one value in a series that keeps its missing values.

    Parameters
    ----------
    series : Series
        Series as loaded by :func:`hydrolog.catalog.inputs.load_series`.

    Returns
    -------
    Series
        ``series``, unchanged.

    Raises
    ------
    CalculationError
        If every value is missing (``details``: ``n_values``, ``n_missing``).
    """
    if series.n_missing == len(series):
        raise CalculationError(
            f"All {len(series)} values of the series are missing; nothing to analyse",
            details={"n_values": len(series), "n_missing": series.n_missing},
            hint="Check the value column: it holds no numbers.",
        )
    return series


def check_years(first_year: int | None, last_year: int | None) -> None:
    """Require ``first_year`` not after ``last_year`` when both are given.

    Raises
    ------
    InvalidParameterError
        If ``first_year > last_year`` (``details``: ``option`` ``first_year``,
        ``reason`` ``range``, ``first_year``, ``last_year``).
    """
    if first_year is not None and last_year is not None and first_year > last_year:
        raise InvalidParameterError(
            f"Option 'first_year' ({first_year}) is after 'last_year' ({last_year})",
            details={
                "option": "first_year",
                "reason": "range",
                "first_year": first_year,
                "last_year": last_year,
            },
            hint="Give the first hydrological year of the period, then the last.",
        )


def select_years(
    series: Series, first_year: int | None, last_year: int | None
) -> Series:
    """Keep the hydrological years ``first_year`` to ``last_year`` of a dated series.

    A hydrological year runs from 1 November to 31 October and is named after the
    year in which it ends. A missing bound keeps the years on that side.

    Parameters
    ----------
    series : Series
        A series with dates; it may hold missing values (``NaN``).
    first_year, last_year : int or None
        First and last hydrological year to keep.

    Returns
    -------
    Series
        The values and dates of those years, missing values kept.

    Raises
    ------
    InvalidParameterError
        If ``first_year`` is after ``last_year``.
    CalculationError
        If no day of those years has a value (``details.reason``
        ``no_values_in_period``, ``first_year``, ``last_year`` and ``available``,
        the first and last year with a value).
    """
    check_years(first_year, last_year)
    if series.dates is None:
        raise InvalidParameterError(
            "The series has no dates",
            details={"option": "dates", "reason": "required"},
        )
    years = hydrological_year(series.dates)
    keep = np.ones(len(series), dtype=bool)
    if first_year is not None:
        keep &= years >= first_year
    if last_year is not None:
        keep &= years <= last_year
    known = ~np.isnan(series.values)
    if not (keep & known).any():
        present = years[known]
        available = [int(present.min()), int(present.max())] if present.size else None
        raise CalculationError(
            f"No value in the hydrological years {first_year} to {last_year}",
            details={
                "reason": "no_values_in_period",
                "first_year": first_year,
                "last_year": last_year,
                "available": available,
            },
            hint="Choose hydrological years that the series covers.",
        )
    if keep.all():
        return series
    return Series(
        values=series.values[keep], dates=series.dates[keep], source=series.source
    )


def reference_period_notices(
    period_years: int, first_year: int, last_year: int
) -> list[Notice]:
    """Return the notice of a reference period shorter than 30 years, if it is.

    Parameters
    ----------
    period_years : int
        Hydrological years with a value in the period.
    first_year, last_year : int
        The period.

    Returns
    -------
    list of Notice
        One ``short_reference_period`` notice (level ``info``) when ``period_years``
        is below :data:`MIN_REFERENCE_YEARS`, else none.
    """
    if period_years >= MIN_REFERENCE_YEARS:
        return []
    return [
        notice(
            "short_reference_period",
            years=period_years,
            first_year=first_year,
            last_year=last_year,
            minimum=MIN_REFERENCE_YEARS,
        )
    ]
