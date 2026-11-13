"""Standardized precipitation index and relative precipitation of months and years.

The SPI of a month for a scale of k months is the standard normal quantile of the sum
of the k months that end in it under the distribution of such sums of the same
calendar month: a gamma distribution fitted by Thom's (1958) approximation of maximum
likelihood to the positive sums, mixed with the probability of a zero sum,
H(x) = q + (1 - q) G(x) (McKee et al., 1993; Edwards and McKee, 1997; WMO, 2012). A
calendar month is fitted when its sums are known in at least 80 % of the years of the
period (WMO-No. 1203, 4.4.2) and three or more of them are positive; the SPI is held
within ±3.09 (the probabilities 0.001 and 0.999, as the ``climate_indices`` package).

The relative precipitation is the sum in % of its normal. A year is classed by
Kaczorowska (1962): below 50 % extremely dry, 50-74 very dry, 75-89 dry, 90-110
normal, 111-125 wet, 126-150 very wet, above 150 extremely wet (the percentage rounded
to a whole number). Kaczorowska gave no classes of months; a month is classed by the
limits used for months in Polish practice: below 25 % extremely dry, from 25 very dry,
from 50 dry, 75-125 normal, above 125 wet, above 150 very wet, above 200 extremely wet
(Tomaszewska, 1994, after Kosiba, 1948, as given by Gąsiorek and Musiał, 2011).

References
----------
McKee, T. B., Doesken, N. J. & Kleist, J. (1993): The relationship of drought frequency
    and duration to time scales. 8th Conference on Applied Climatology, Anaheim,
    179-184.
Edwards, D. C. & McKee, T. B. (1997): Characteristics of 20th century drought in the
    United States at multiple time scales. Climatology Report 97-2, Colorado State
    University.
Thom, H. C. S. (1958): A note on the gamma distribution. Monthly Weather Review 86,
    117-122.
WMO (2012): Standardized Precipitation Index User Guide. WMO-No. 1090, Geneva.
Kaczorowska, Z. (1962): Opady w Polsce w przekroju wieloletnim. Prace Geograficzne
    IG PAN 33.
Gąsiorek, E. & Musiał, E. (2011): Porównanie i klasyfikacja warunków opadowych na
    podstawie wskaźnika standaryzowanego opadu i wskaźnika względnego opadu.
    Woda-Środowisko-Obszary Wiejskie 11(4), 107-119 (Table 1 and p. 108).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from numpy.typing import NDArray
from scipy.special import gammainc, ndtri

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._climate import (
    WMO_NORMAL_SHARE,
    as_days,
    check_daily,
    check_year_type,
    classify,
    finite,
    grid_of_values,
    monthly_precipitation,
    normal,
    rolling_sum,
    years_with_values,
)

__all__ = [
    "DEFAULT_SCALES_MONTHS",
    "GammaFit",
    "KACZOROWSKA_CLASSES",
    "SPI_LIMIT",
    "SpiMonth",
    "SpiPeriod",
    "SpiScale",
    "SpiYear",
    "StandardizedPrecipitation",
    "fit_gamma",
    "month_precipitation_class",
    "spi_values",
    "standardized_precipitation_index",
    "year_precipitation_class",
]

DEFAULT_SCALES_MONTHS: tuple[int, ...] = (1, 3, 6, 12)
"""Scales of the SPI [months] (McKee et al., 1993; WMO-No. 1090)."""
SPI_LIMIT = 3.09
"""The SPI is held within ±3.09 (cumulative probabilities 0.001 and 0.999)."""
KACZOROWSKA_CLASSES: tuple[str, ...] = (
    "extremely_dry",
    "very_dry",
    "dry",
    "normal",
    "wet",
    "very_wet",
    "extremely_wet",
)
"""The classes of relative precipitation, driest first."""
_YEAR_LIMITS = (49.0, 74.0, 89.0, 110.0, 125.0, 150.0)
_MONTH_LIMITS = (25.0, 50.0, 75.0)
_MONTH_UPPER = (125.0, 150.0, 200.0)
_MIN_POSITIVE = 3


@dataclass
class GammaFit(JsonResultMixin):
    """The gamma distribution of the k-month sums of one calendar month.

    Attributes
    ----------
    month : int
        Calendar month the sums end in.
    alpha : float or None
        Shape of the gamma distribution; ``None`` without a fit.
    beta : float or None
        Its scale [mm].
    zero_probability : float or None
        q, the share of zero sums.
    n_values : int
        Sums of the period the fit is made from.
    """

    month: int
    alpha: float | None
    beta: float | None
    zero_probability: float | None
    n_values: int


class _Fit(NamedTuple):
    alpha: float
    beta: float
    zero_probability: float


def fit_gamma(sums: NDArray[np.float64] | Sequence[float]) -> _Fit | None:
    """Fit the SPI's gamma distribution by Thom's (1958) approximation.

    A = ln(mean) - mean(ln x) over the positive sums, alpha = (1 + √(1 + 4A/3)) / (4A),
    beta = mean / alpha; q is the share of zeros among the known sums.

    Parameters
    ----------
    sums : array_like of float
        Precipitation sums [mm]; ``NaN`` are left out.

    Returns
    -------
    tuple of (alpha, beta, q) or None
        ``None`` with fewer than three positive sums or all of them equal.
    """
    values = np.asarray(sums, dtype=np.float64)
    values = values[np.isfinite(values)]
    positive = values[values > 0]
    if positive.size < _MIN_POSITIVE:
        return None
    mean = float(positive.mean())
    a = math.log(mean) - float(np.log(positive).mean())
    if a <= 0:
        return None
    alpha = (1.0 + math.sqrt(1.0 + 4.0 * a / 3.0)) / (4.0 * a)
    return _Fit(alpha, mean / alpha, 1.0 - positive.size / values.size)


def spi_values(
    sums: NDArray[np.float64], alpha: float, beta: float, zero_probability: float
) -> NDArray[np.float64]:
    """SPI = Φ⁻¹(q + (1 - q) G(x; alpha, beta)), held within ±3.09.

    Parameters
    ----------
    sums : NDArray[np.float64]
        Precipitation sums [mm]; ``NaN`` stays ``NaN``.
    alpha, beta, zero_probability : float
        The fitted distribution.

    Returns
    -------
    NDArray[np.float64]
        The SPI of each sum.
    """
    known = np.isfinite(sums)
    x = np.where(known, np.maximum(sums, 0.0), 0.0)
    gamma = gammainc(alpha, np.where(x > 0, x, 0.0) / beta)
    cdf = np.where(
        x > 0, zero_probability + (1.0 - zero_probability) * gamma, zero_probability
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        index = np.clip(ndtri(cdf), -SPI_LIMIT, SPI_LIMIT)
    out: NDArray[np.float64] = np.where(known, index, np.nan)
    return out


def year_precipitation_class(percent: float | None) -> str | None:
    """Kaczorowska's (1962) class of a year's precipitation in % of its normal."""
    if percent is None or not math.isfinite(percent):
        return None
    return classify(float(round(percent)), _YEAR_LIMITS, KACZOROWSKA_CLASSES)


def month_precipitation_class(percent: float | None) -> str | None:
    """Return the class of a month's precipitation in % of its normal.

    Below 25 % extremely dry, [25, 50) very dry, [50, 75) dry, [75, 125] normal,
    (125, 150] wet, (150, 200] very wet, above 200 extremely wet (Gąsiorek and
    Musiał, 2011, Table 1, after Tomaszewska, 1994).
    """
    if percent is None or not math.isfinite(percent):
        return None
    for limit, name in zip(_MONTH_LIMITS, KACZOROWSKA_CLASSES[:3], strict=True):
        if percent < limit:
            return name
    return classify(percent, _MONTH_UPPER, KACZOROWSKA_CLASSES[3:])


@dataclass
class SpiScale(JsonResultMixin):
    """The fits of one scale.

    Attributes
    ----------
    scale_months : int
        k, the months summed.
    fits : list of GammaFit
        One per calendar month, January first.
    """

    scale_months: int
    fits: list[GammaFit]


@dataclass
class SpiMonth(JsonResultMixin):
    """One month of the period.

    Attributes
    ----------
    month : str
        The month, ``YYYY-MM``.
    total_mm : float or None
        Its precipitation [mm] (WMO-No. 1203, 4.4.1 c).
    percent_of_normal : float or None
        In % of the normal of the calendar month.
    precipitation_class : str or None
        Its class (:data:`KACZOROWSKA_CLASSES`, the limits of months).
    spi : list of float or None
        The SPI of each of ``scales_months``.
    """

    month: str
    total_mm: float | None
    percent_of_normal: float | None
    precipitation_class: str | None
    spi: list[float | None]


@dataclass
class SpiYear(JsonResultMixin):
    """One year of the period.

    Attributes
    ----------
    year : int
        The year.
    total_mm : float or None
        Its precipitation [mm]; ``None`` without its twelve monthly sums.
    percent_of_normal : float or None
        In % of the annual normal.
    precipitation_class : str or None
        Kaczorowska's (1962) class (:data:`KACZOROWSKA_CLASSES`).
    """

    year: int
    total_mm: float | None
    percent_of_normal: float | None
    precipitation_class: str | None


@dataclass
class SpiPeriod(JsonResultMixin):
    """The normals and the fits of the period.

    Attributes
    ----------
    normal_mm : float or None
        Annual normal [mm] (WMO-No. 1203, 4.4.2).
    normal_years : int
        Years with an annual sum.
    months_normal_mm : list of float or None
        Normals of the calendar months, January first [mm].
    scales : list of SpiScale
        The fits of each scale.
    """

    normal_mm: float | None
    normal_years: int
    months_normal_mm: list[float | None]
    scales: list[SpiScale]


@dataclass
class StandardizedPrecipitation(JsonResultMixin):
    """SPI of several scales and the relative precipitation of months and years (M8).

    Attributes
    ----------
    scales_months : list of int
        The scales [months] of ``months[].spi``.
    year_type : str
        ``"calendar"`` or ``"hydrological"``: the years of ``years``.
    first_year, last_year, period_years : int
        The period: first and last year with a value, years with a value.
    months : list of SpiMonth
        Every month from the first to the last with a value.
    years : list of SpiYear
        Every year with a value.
    period : SpiPeriod
        The normals and the fits.
    """

    scales_months: list[int]
    year_type: str
    first_year: int
    last_year: int
    period_years: int
    months: list[SpiMonth]
    years: list[SpiYear]
    period: SpiPeriod


def _scales(scales_months: Sequence[int]) -> list[int]:
    chosen: list[int] = []
    for item in scales_months:
        if isinstance(item, bool) or int(item) != item or not 1 <= item <= 48:
            raise InvalidParameterError(
                f"scales_months must be whole numbers from 1 to 48, got {item!r}"
            )
        if int(item) not in chosen:
            chosen.append(int(item))
    if not chosen:
        raise InvalidParameterError("scales_months must not be empty")
    return chosen


def standardized_precipitation_index(
    precipitation_mm: NDArray[np.float64] | Sequence[float],
    dates: NDArray[np.datetime64] | Sequence[object],
    *,
    scales_months: Sequence[int] = DEFAULT_SCALES_MONTHS,
    accumulated: NDArray[np.bool_] | Sequence[bool] | None = None,
    year_type: str = "calendar",
) -> StandardizedPrecipitation:
    """SPI of each scale and the relative precipitation of each month and year (M8).

    Parameters
    ----------
    precipitation_mm : array_like of float
        Daily precipitation [mm]; ``NaN`` on a missing day.
    dates : array_like of datetime64
        Their dates, strictly increasing.
    scales_months : sequence of int, optional
        Scales [months], each from 1 to 48, by default 1, 3, 6 and 12.
    accumulated : array_like of bool, optional
        Accumulated totals of the missing days before them (they stand for them in
        the monthly sums, WMO-No. 1203, 4.4.1 c).
    year_type : {"calendar", "hydrological"}, optional
        The kind of year of ``years`` and of the period.

    Returns
    -------
    StandardizedPrecipitation
        The SPI and the relative precipitation of the months, the years and the
        fits.

    Raises
    ------
    InvalidParameterError
        If the arrays are invalid, no day has a value, ``year_type`` is unknown or a
        scale is not a whole number from 1 to 48.
    """
    scales = _scales(scales_months)
    check_year_type(year_type)
    values = np.asarray(precipitation_mm, dtype=np.float64)
    days = as_days(dates)
    check_daily(days, values)
    flags = (
        np.zeros(values.size, dtype=bool)
        if accumulated is None
        else np.asarray(accumulated, dtype=bool)
    )
    if flags.size != values.size:
        raise InvalidParameterError("accumulated must have one flag per value")
    known = np.isfinite(values)
    grid = grid_of_values(days, known, year_type)
    raw = grid.place(days, values)
    table = monthly_precipitation(
        grid, raw, grid.place_flags(days, flags) & np.isfinite(raw)
    )
    flat = table.reshape(-1)
    calendar = np.array(grid.months * grid.n_years, dtype=np.int64)
    present = years_with_values(grid, np.isfinite(raw))
    month_with_value = (
        grid.per_month(np.isfinite(raw).astype(np.float64)).reshape(-1) > 0
    )
    have = np.flatnonzero(month_with_value)
    first, last = int(have[0]), int(have[-1])
    normals = {
        int(month): normal(table[:, slot])[0] for slot, month in enumerate(grid.months)
    }
    annual = table.sum(axis=1)
    normal_mm, normal_years = normal(annual)
    span = grid.n_years
    spi_table = np.full((len(scales), flat.size), np.nan)
    scale_fits: list[SpiScale] = []
    for number, scale in enumerate(scales):
        sums = rolling_sum(flat, scale)
        fits: list[GammaFit] = []
        for month in range(1, 13):
            where = calendar == month
            sample = sums[where]
            sample = sample[np.isfinite(sample)]
            fitted = (
                fit_gamma(sample) if sample.size >= WMO_NORMAL_SHARE * span else None
            )
            if fitted is None:
                fits.append(GammaFit(month, None, None, None, int(sample.size)))
                continue
            fits.append(
                GammaFit(
                    month,
                    fitted.alpha,
                    fitted.beta,
                    fitted.zero_probability,
                    int(sample.size),
                )
            )
            spi_table[number, where] = spi_values(sums[where], *fitted)
        scale_fits.append(SpiScale(scale, fits))
    months: list[SpiMonth] = []
    for cell in range(first, last + 1):
        row, slot = divmod(cell, 12)
        month = int(grid.months[slot])
        year = grid.first_year + row
        if grid.year_type == "hydrological" and month >= 11:
            year -= 1
        total = finite(flat[cell])
        reference = normals[month]
        percent = 100.0 * total / reference if total is not None and reference else None
        months.append(
            SpiMonth(
                month=f"{year:04d}-{month:02d}",
                total_mm=total,
                percent_of_normal=percent,
                precipitation_class=month_precipitation_class(percent),
                spi=[finite(spi_table[number, cell]) for number in range(len(scales))],
            )
        )
    years: list[SpiYear] = []
    for row in np.flatnonzero(present).tolist():
        total = finite(annual[row])
        percent = 100.0 * total / normal_mm if total is not None and normal_mm else None
        years.append(
            SpiYear(
                grid.first_year + row, total, percent, year_precipitation_class(percent)
            )
        )
    return StandardizedPrecipitation(
        scales_months=scales,
        year_type=year_type,
        first_year=grid.first_year,
        last_year=grid.last_year,
        period_years=int(present.sum()),
        months=months,
        years=years,
        period=SpiPeriod(
            normal_mm=normal_mm,
            normal_years=normal_years,
            months_normal_mm=[normals[month] for month in range(1, 13)],
            scales=scale_fits,
        ),
    )
