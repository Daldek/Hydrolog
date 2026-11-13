"""Duration curves of daily series and the frequencies of their classes.

The duration curve gives the value equalled or exceeded on p % of the days. The values
are ranked from the highest (rank m = 1 to n); the m-th has the Weibull plotting
position p = m / (n + 1) and a percentage between two positions is interpolated
linearly between their values, held at the end values beyond them (Searcy 1959; Vogel
and Fennessey 1994). The classes count the days of each class of values from the
highest down, with the cumulative days „including higher” and „including lower” and
their split by hydrological month (Byczkowski 1996; the author's table of 2024).

References
----------
Searcy, J. K. (1959): Flow-duration curves. Manual of Hydrology, Part 2. USGS
    Water-Supply Paper 1542-A.
Vogel, R. M. & Fennessey, N. M. (1994): Flow-duration curves. I: New interpretation
    and confidence intervals. Journal of Water Resources Planning and Management
    120(4), 485-504.
Byczkowski, A. (1996): Hydrologia, t. 1. Wydawnictwo SGGW, Warszawa.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "CURVE_PERCENTS",
    "DEFAULT_PERCENTS",
    "DurationClass",
    "DurationCurve",
    "ModalClass",
    "duration_curve",
    "exceedance_values",
]

ClassMethod = Literal["width", "log"]

CURVE_PERCENTS: tuple[float, ...] = (
    0.1,
    0.2,
    0.5,
    *(float(percent) for percent in range(1, 100)),
    99.5,
    99.8,
    99.9,
)
"""Exceedance percentages of the drawn curve (:attr:`DurationCurve.curve_values`)."""

DEFAULT_PERCENTS: tuple[float, ...] = (
    1.0,
    5.0,
    10.0,
    30.0,
    50.0,
    70.0,
    90.0,
    95.0,
    99.0,
)
"""Exceedance percentages of the table when none are given."""

# Calendar months in the order of the hydrological year: November first.
_HYDROLOGICAL_MONTHS = (11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)


def exceedance_values(
    values: NDArray[np.float64], percents: Sequence[float] | NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return the values equalled or exceeded on the given percentages of the days.

    Parameters
    ----------
    values : NDArray[np.float64]
        The series; ``NaN`` values are left out.
    percents : sequence of float
        Exceedance percentages, each in (0, 100).

    Returns
    -------
    NDArray[np.float64]
        One value per percentage: Weibull plotting positions m / (n + 1) of the
        values ranked from the highest, interpolated linearly between ranks.

    Raises
    ------
    InvalidParameterError
        If no value is finite.
    """
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise InvalidParameterError("the series has no value")
    ordered = np.sort(finite)[::-1]
    positions = np.arange(1, ordered.size + 1) / (ordered.size + 1) * 100.0
    result: NDArray[np.float64] = np.interp(
        np.asarray(percents, dtype=np.float64), positions, ordered
    )
    return result


@dataclass
class DurationClass(JsonResultMixin):
    """One class of values and its days.

    Attributes
    ----------
    lower, upper : float
        Bounds of the class: a value v belongs to it when lower <= v < upper (the
        highest class also holds its upper bound).
    days : int
        Days with a value in the class.
    percent : float
        ``days`` as a percentage of the days counted.
    days_with_higher : int
        Days in this class or a higher one („including higher”: the duration of the
        values from ``lower`` up).
    days_with_lower : int
        Days in this class or a lower one („including lower”).
    months : list of int
        ``days`` by hydrological month, November to October.
    """

    lower: float
    upper: float
    days: int
    percent: float
    days_with_higher: int
    days_with_lower: int
    months: list[int]


@dataclass
class ModalClass(JsonResultMixin):
    """The most frequent class (the lowest one when several are as frequent).

    Attributes
    ----------
    lower, upper : float
        Bounds of the class.
    days : int
        Its days.
    percent : float
        Its share of the days counted [%].
    """

    lower: float
    upper: float
    days: int
    percent: float


@dataclass
class DurationCurve(JsonResultMixin):
    """Duration curve of a daily series with the frequencies of its classes.

    Attributes
    ----------
    first_year, last_year : int
        First and last hydrological year of the days used.
    period_years : int
        Hydrological years with a value among the days used.
    month : int or None
        The calendar month whose days were used; ``None`` for every day.
    n_values : int
        Days with a value used.
    min, max, mean, median : float
        Statistics of those values.
    percents : list of float
        Exceedance percentages of the table.
    values : list of float
        The value equalled or exceeded on each percentage of ``percents``.
    curve_percents : list of float
        Exceedance percentages of the drawn curve (:data:`CURVE_PERCENTS`).
    curve_values : list of float
        The curve at ``curve_percents``.
    class_method : {"width", "log"}
        Classes of equal width or logarithmic classes.
    class_width : float or None
        Width of the classes (``"width"``), in the unit of the series.
    class_count : int or None
        Number of logarithmic classes (``"log"``).
    classes : list of DurationClass
        The classes from the highest down. Logarithmic classes count the positive
        values only.
    modal_class : ModalClass or None
        The most frequent class; ``None`` without classes.
    """

    first_year: int
    last_year: int
    period_years: int
    month: int | None
    n_values: int
    min: float
    max: float
    mean: float
    median: float
    percents: list[float]
    values: list[float]
    curve_percents: list[float]
    curve_values: list[float]
    class_method: str
    class_width: float | None
    class_count: int | None
    classes: list[DurationClass] = field(default_factory=list)
    modal_class: ModalClass | None = None


def _class_edges(
    values: NDArray[np.float64],
    method: ClassMethod,
    width: float,
    count: int,
) -> NDArray[np.float64]:
    """Edges of the classes, ascending; empty when the values allow no class."""
    if method == "width":
        origin = math.floor(float(values.min()) / width) * width
        n_classes = max(1, math.floor((float(values.max()) - origin) / width) + 1)
        return origin + width * np.arange(n_classes + 1, dtype=np.float64)
    positive = values[values > 0]
    if positive.size < 2 or positive.min() == positive.max():
        return np.empty(0, dtype=np.float64)
    edges: NDArray[np.float64] = np.logspace(
        math.log10(float(positive.min())), math.log10(float(positive.max())), count + 1
    )
    # The end edges are the extreme values themselves, not their rounded logarithms.
    edges[0], edges[-1] = float(positive.min()), float(positive.max())
    return edges


def _classes(
    values: NDArray[np.float64],
    months: NDArray[np.int_],
    edges: NDArray[np.float64],
) -> tuple[list[DurationClass], ModalClass | None]:
    """Count the days of each class, highest first, and find the modal class."""
    if edges.size < 2:
        return [], None
    inside = (values >= edges[0]) & (values <= edges[-1])
    counted = values[inside]
    month_index = (months[inside] - 11) % 12  # 0 = November ... 11 = October
    total = int(counted.size)
    index = np.clip(
        np.searchsorted(edges, counted, side="right") - 1, 0, edges.size - 2
    )
    table = np.zeros((edges.size - 1, 12), dtype=np.int64)
    np.add.at(table, (index, month_index), 1)
    days = table.sum(axis=1)
    classes: list[DurationClass] = []
    higher = 0
    for at in range(edges.size - 2, -1, -1):
        count = int(days[at])
        lower_days = total - higher
        higher += count
        classes.append(
            DurationClass(
                lower=float(edges[at]),
                upper=float(edges[at + 1]),
                days=count,
                percent=count / total * 100.0 if total else 0.0,
                days_with_higher=higher,
                days_with_lower=lower_days,
                months=[int(item) for item in table[at]],
            )
        )
    modal = int(np.argmax(days))
    return classes, ModalClass(
        lower=float(edges[modal]),
        upper=float(edges[modal + 1]),
        days=int(days[modal]),
        percent=float(days[modal]) / total * 100.0 if total else 0.0,
    )


def duration_curve(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    month: int | None = None,
    percents: Sequence[float] = DEFAULT_PERCENTS,
    class_method: ClassMethod = "width",
    class_width: float = 10.0,
    class_count: int = 40,
) -> DurationCurve:
    """Compute the duration curve and the class frequencies of a daily series.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` values are left out.
    dates : NDArray[np.datetime64]
        Their dates.
    month : int, optional
        Use only the days of this calendar month (1-12).
    percents : sequence of float, optional
        Exceedance percentages of the table, each in (0, 100), by default
        :data:`DEFAULT_PERCENTS`.
    class_method : {"width", "log"}, optional
        Classes of equal width ``class_width`` starting at the multiple of the width
        at or below the smallest value (default), or ``class_count`` logarithmic
        classes between the smallest positive and the largest value.
    class_width : float, optional
        Width of the classes, positive, in the unit of the series, by default 10.
    class_count : int, optional
        Number of logarithmic classes, at least 2, by default 40.

    Returns
    -------
    DurationCurve
        The curve, its table and the classes.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in length, an option is out of its range, or no day
        (of ``month``) has a value.
    """
    values = np.asarray(values, dtype=np.float64)
    dates = np.asarray(dates).astype("datetime64[D]")
    if values.size != dates.size:
        raise InvalidParameterError("values and dates must have the same length")
    table_percents = np.asarray(percents, dtype=np.float64)
    if (
        table_percents.ndim != 1
        or table_percents.size == 0
        or not np.all((table_percents > 0) & (table_percents < 100))
    ):
        raise InvalidParameterError("percents must lie in the open interval (0, 100)")
    if class_method not in ("width", "log"):
        raise InvalidParameterError(f"unknown class_method {class_method!r}")
    if not (math.isfinite(class_width) and class_width > 0) or class_count < 2:
        raise InvalidParameterError(
            "class_width must be positive and class_count at least 2"
        )
    calendar_months = dates.astype("datetime64[M]").astype(np.int64) % 12 + 1
    keep = np.isfinite(values)
    if month is not None:
        if not 1 <= month <= 12:
            raise InvalidParameterError(f"month must be 1 to 12, got {month}")
        keep &= calendar_months == month
    if not keep.any():
        raise InvalidParameterError("no day has a value")
    used = values[keep]
    years = hydrological_year(dates[keep])
    curve = exceedance_values(used, CURVE_PERCENTS)
    table = exceedance_values(used, table_percents)
    edges = _class_edges(used, class_method, class_width, class_count)
    classes, modal = _classes(used, calendar_months[keep], edges)
    return DurationCurve(
        first_year=int(years.min()),
        last_year=int(years.max()),
        period_years=int(np.unique(years).size),
        month=month,
        n_values=int(used.size),
        min=float(used.min()),
        max=float(used.max()),
        mean=float(used.mean()),
        median=float(np.median(used)),
        percents=[float(item) for item in table_percents],
        values=[float(item) for item in table],
        curve_percents=list(CURVE_PERCENTS),
        curve_values=[float(item) for item in curve],
        class_method=class_method,
        class_width=float(class_width) if class_method == "width" else None,
        class_count=int(class_count) if class_method == "log" else None,
        classes=classes,
        modal_class=modal,
    )
