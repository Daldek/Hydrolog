"""Harmonic analysis of the annual cycle of a daily series.

The annual cycle is fitted by least squares as a mean and K harmonics of the year,

    x(t) = A₀ + Σₖ [aₖ cos(2πkt / P) + bₖ sin(2πkt / P)],  k = 1 … K,

with t the day of the hydrological year counted from 0 (1 November) and P = 365.25
days. Each harmonic has the amplitude Cₖ = √(aₖ² + bₖ²) and the phase
φₖ = atan2(bₖ, aₖ), which puts its first maximum on the day φₖ P / (2πk) + 1 of the
hydrological year; its share of the variance is what it adds to the R² of the
harmonics before it (the coefficients of the whole fit, cut after harmonic k). The
fit of a whole period is the mean annual cycle of its years; a year is fitted on its
own when it has at least 300 days with a value. The method serves any daily variable:
water or air temperature, discharge, stage.

References
----------
Wilks, D. S. (2011): Statistical Methods in the Atmospheric Sciences, 3rd ed.
    Academic Press, section 9.4 (harmonic analysis).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    hydrological_day_of_year,
    hydrological_year,
)

__all__ = [
    "MAX_HARMONICS",
    "MIN_YEAR_VALUES",
    "PERIOD_DAYS",
    "AnnualCycle",
    "Harmonic",
    "HarmonicFit",
    "HarmonicYear",
    "annual_cycle",
    "harmonic_fit",
]

PERIOD_DAYS = 365.25
"""Period of the first harmonic [days]: the mean length of a Gregorian year."""
MAX_HARMONICS = 4
"""Largest number of harmonics fitted."""
MIN_YEAR_VALUES = 300
"""Days with a value that a hydrological year needs for a fit of its own."""


@dataclass
class Harmonic(JsonResultMixin):
    """One harmonic of a fitted annual cycle.

    Attributes
    ----------
    amplitude : float
        Cₖ = √(aₖ² + bₖ²), in the unit of the series.
    phase_day : float
        Day of the hydrological year of its first maximum (1 = 1 November).
    explained_variance : float or None
        What the harmonic adds to the R² of the harmonics before it; ``None`` for a
        constant series.
    """

    amplitude: float
    phase_day: float
    explained_variance: float | None


@dataclass
class HarmonicFit(JsonResultMixin):
    """A fit of the annual cycle: the mean and the harmonics.

    Attributes
    ----------
    mean : float
        A₀, the mean of the fitted cycle, in the unit of the series.
    harmonics : list of Harmonic
        Harmonics 1 to K.
    r_squared : float or None
        Share of the variance explained by the whole fit; ``None`` for a constant
        series.
    n_values : int
        Days with a value in the fit.
    """

    mean: float
    harmonics: list[Harmonic]
    r_squared: float | None
    n_values: int


@dataclass
class HarmonicYear(JsonResultMixin):
    """The fit of one hydrological year (fields of :class:`HarmonicFit`).

    Attributes
    ----------
    year : int
        Hydrological year (1 November - 31 October, named after its end).
    mean, harmonics, r_squared, n_values
        As in :class:`HarmonicFit`, from the days of this year.
    """

    year: int
    mean: float
    harmonics: list[Harmonic]
    r_squared: float | None
    n_values: int


@dataclass
class AnnualCycle(JsonResultMixin):
    """The harmonic fits of the annual cycle of a period and of its years.

    Attributes
    ----------
    n_harmonics : int
        Harmonics fitted, 1 to 4.
    period_days : float
        Period of the first harmonic [days], 365.25.
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    period : HarmonicFit
        The fit of every day of the period: the mean annual cycle.
    years : list of HarmonicYear
        The fit of each year with at least :data:`MIN_YEAR_VALUES` days with a value.
    """

    n_harmonics: int
    period_days: float
    first_year: int
    last_year: int
    period_years: int
    period: HarmonicFit
    years: list[HarmonicYear] = field(default_factory=list)


def _check_count(n_harmonics: int) -> None:
    if isinstance(n_harmonics, bool) or not 1 <= n_harmonics <= MAX_HARMONICS:
        raise InvalidParameterError(
            f"n_harmonics must be 1 to {MAX_HARMONICS}, got {n_harmonics!r}"
        )


def harmonic_fit(
    day_of_year: NDArray[np.integer],
    values: NDArray[np.float64],
    n_harmonics: int = 2,
) -> HarmonicFit:
    """Fit the mean and ``n_harmonics`` harmonics of the year by least squares.

    Parameters
    ----------
    day_of_year : NDArray[np.integer]
        Day of the hydrological year of each value (1 = 1 November).
    values : NDArray[np.float64]
        The values; ``NaN`` marks a day without a value.
    n_harmonics : int, optional
        Number of harmonics, 1 to 4, by default 2.

    Returns
    -------
    HarmonicFit
        The mean, the harmonics and the share of the variance explained.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in length, ``n_harmonics`` is out of range or fewer than
        ``4 n_harmonics + 2`` values are known.
    """
    _check_count(n_harmonics)
    days = np.asarray(day_of_year)
    numbers = np.asarray(values, dtype=np.float64)
    if days.shape != numbers.shape:
        raise InvalidParameterError("day_of_year and values must have the same length")
    keep = np.isfinite(numbers)
    t = days[keep].astype(np.float64) - 1.0
    y = numbers[keep]
    needed = 4 * n_harmonics + 2
    if y.size < needed:
        raise InvalidParameterError(
            f"A fit of {n_harmonics} harmonic(s) needs at least {needed} values, "
            f"got {y.size}"
        )
    columns = [np.ones_like(t)]
    for k in range(1, n_harmonics + 1):
        omega = 2.0 * np.pi * k * t / PERIOD_DAYS
        columns += [np.cos(omega), np.sin(omega)]
    design = np.column_stack(columns)
    coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
    total = float(np.sum((y - y.mean()) ** 2))
    harmonics: list[Harmonic] = []
    explained = 0.0
    for k in range(1, n_harmonics + 1):
        a, b = float(coefficients[2 * k - 1]), float(coefficients[2 * k])
        phase = math.atan2(b, a) % (2.0 * math.pi)
        share: float | None = None
        if total > 0:
            fitted = design[:, : 2 * k + 1] @ coefficients[: 2 * k + 1]
            cumulative = 1.0 - float(np.sum((y - fitted) ** 2)) / total
            share = cumulative - explained
            explained = cumulative
        harmonics.append(
            Harmonic(
                amplitude=math.hypot(a, b),
                phase_day=phase * PERIOD_DAYS / (2.0 * math.pi * k) + 1.0,
                explained_variance=share,
            )
        )
    return HarmonicFit(
        mean=float(coefficients[0]),
        harmonics=harmonics,
        r_squared=explained if total > 0 else None,
        n_values=int(y.size),
    )


def annual_cycle(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    n_harmonics: int = 2,
) -> AnnualCycle:
    """Fit the annual cycle of a daily series over the period and in each year.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates (days may be absent).
    n_harmonics : int, optional
        Number of harmonics, 1 to 4, by default 2.

    Returns
    -------
    AnnualCycle
        The fit of the period and of each year with at least
        :data:`MIN_YEAR_VALUES` days with a value.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, ``n_harmonics`` is out of range
        or the period has fewer than ``4 n_harmonics + 2`` values.
    """
    _check_count(n_harmonics)
    numbers = np.asarray(values, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    if numbers.size == 0 or numbers.size != days.size:
        raise InvalidParameterError(
            "values and dates must be non-empty and of the same length"
        )
    known = np.isfinite(numbers)
    numbers, days = numbers[known], days[known]
    day_of_year = hydrological_day_of_year(days)
    period = harmonic_fit(day_of_year, numbers, n_harmonics)
    year_of_day = hydrological_year(days)
    years = np.unique(year_of_day)
    rows: list[HarmonicYear] = []
    for year in years.tolist():
        mine = year_of_day == year
        if int(mine.sum()) < MIN_YEAR_VALUES:
            continue
        fit = harmonic_fit(day_of_year[mine], numbers[mine], n_harmonics)
        rows.append(
            HarmonicYear(
                year=int(year),
                mean=fit.mean,
                harmonics=fit.harmonics,
                r_squared=fit.r_squared,
                n_values=fit.n_values,
            )
        )
    return AnnualCycle(
        n_harmonics=n_harmonics,
        period_days=PERIOD_DAYS,
        first_year=int(years[0]),
        last_year=int(years[-1]),
        period_years=int(years.size),
        period=period,
        years=rows,
    )
