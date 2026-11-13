"""Operations of the group ``hydrometrics``: rating curves and water level zones.

Power-law rating curve fitting (:class:`hydrolog.hydrometrics.RatingCurve`) and
Rybczyński water level zones (:class:`hydrolog.hydrometrics.WaterLevelFrequency`) for
inline values or files. Dated stage-discharge pairs (a daily series with H and Q) can
be fitted for a range of hydrological years and for successive periods of it. The
functions are re-exported by :mod:`hydrolog.operations`.
"""

from __future__ import annotations

import dataclasses
import math
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from hydrolog._attribution import cite
from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.catalog.inputs import parse_dates, read_table
from hydrolog.catalog.notices import notice
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.hydrometrics import (
    FrequencyDistributionResult,
    RatingCurve,
    RatingCurveResult,
    WaterLevelFrequency,
    WaterLevelZones,
)
from hydrolog.operations._analysis import check_years, load_valid_series, require_count
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "RatingCurveAnalysis",
    "RatingPeriod",
    "WaterLevelAnalysis",
    "hydrometrics_rating_curve",
    "hydrometrics_water_level_zones",
]

_MIN_PAIRS = 3  # the rating curve has three parameters
_MIN_PERIOD_PAIRS = 30  # a period of a dated series is fitted from this many pairs
_MAX_BINS = 100_000  # guards the histogram of the water level zones against a tiny bin
_NUMERIC_WARNINGS: tuple[type[Warning], ...] = (UserWarning, RuntimeWarning)


@dataclass
class RatingPeriod(JsonResultMixin):
    """The rating curve of one period of a dated series.

    Attributes
    ----------
    first_year, last_year : int
        First and last hydrological year of the period (cut to the pairs fitted).
    n_pairs : int
        Pairs of the period.
    a, b, h0, r_squared, std_residuals : float or None
        The curve Q = a·(H − H₀)^b and its fit (as ``RatingCurveResult``); ``None``
        when the period has no curve (see ``reason``).
    n_points, n_outliers_removed : int or None
        Pairs of the final fit and pairs removed as outliers.
    discharge_at_reference_m3s : float or None
        Q of the period's curve at the result's ``reference_level`` [m³/s]; ``None``
        when that level is not above H₀.
    level_at_reference_discharge : float or None
        H of the period's curve at the result's ``reference_discharge_m3s``.
    reason : str or None
        Why the period has no curve: ``too_few_pairs`` (fewer than 30) or
        ``fit_failed``; ``None`` when it has one.
    """

    first_year: int
    last_year: int
    n_pairs: int
    a: float | None = None
    b: float | None = None
    h0: float | None = None
    r_squared: float | None = None
    std_residuals: float | None = None
    n_points: int | None = None
    n_outliers_removed: int | None = None
    discharge_at_reference_m3s: float | None = None
    level_at_reference_discharge: float | None = None
    reason: str | None = None


@dataclass
class RatingCurveAnalysis(RatingCurveResult):
    """A rating curve with the years of its pairs and the curves of its periods.

    The fields of :class:`~hydrolog.hydrometrics.RatingCurveResult` are those of the
    curve of all the pairs fitted.

    Attributes
    ----------
    first_year, last_year : int or None
        First and last hydrological year of the pairs; ``None`` without dates.
    periods : list of RatingPeriod or None
        The curve of each period of ``years_per_period`` years; ``None`` when no
        periods were asked for.
    reference_level : float or None
        Median water level of the pairs, at which the periods' curves are read;
        ``None`` without periods.
    reference_discharge_m3s : float or None
        Median discharge of the pairs [m³/s]; ``None`` without periods.
    """

    first_year: int | None = None
    last_year: int | None = None
    periods: list[RatingPeriod] | None = None
    reference_level: float | None = None
    reference_discharge_m3s: float | None = None


@dataclass
class WaterLevelAnalysis(JsonResultMixin):
    """Rybczyński water level zones with the frequency distribution behind them.

    Attributes
    ----------
    n_observations : int
        Number of water levels used.
    bin_width : float
        Width of the histogram classes, in the unit of the levels.
    zones : WaterLevelZones
        Upper limit of the low (NTW) and medium (STW) background water and the range
        of each zone, in the unit of the levels.
    frequency : FrequencyDistributionResult
        Histogram of the levels: class edges and centres, counts, relative and
        cumulative frequency [%] and the duration (exceedance) curve [%].
    """

    n_observations: int
    bin_width: float
    zones: WaterLevelZones
    frequency: FrequencyDistributionResult


def _required_with_file(option: str) -> InvalidParameterError:
    """Error of a column option that is missing next to ``input_file``."""
    return InvalidParameterError(
        f"Option {option!r} is required with 'input_file'",
        details={"option": option, "reason": "required"},
    )


def _inline_numbers(
    option: str, values: Sequence[object] | NDArray[Any]
) -> NDArray[np.float64]:
    """Finite ``float64`` array of an inline list."""
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError):
        array = np.array([np.nan])
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        raise InvalidParameterError(
            f"Option {option!r}: must be a non-empty list of finite numbers",
            details={"option": option, "reason": "type"},
        )
    return array


def _rating_pairs(
    water_levels: Sequence[object] | NDArray[Any] | None,
    discharges: Sequence[object] | NDArray[Any] | None,
    dates: Sequence[object] | NDArray[Any] | None,
    input_file: str | os.PathLike[str] | None,
    level_column: str | None,
    discharge_column: str | None,
    date_column: str | None,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.datetime64] | None,
    list[Notice],
]:
    """Return the pairs without missing values, their dates and the removal notice.

    The dates are ``None`` when none were given.
    """
    inline = water_levels is not None or discharges is not None or dates is not None
    if inline == (input_file is not None):
        raise InvalidParameterError(
            "Give either inline 'water_levels' with 'discharges' or 'input_file' "
            "with 'level_column' and 'discharge_column'",
            details={
                "option": "input_file" if input_file is not None else "water_levels",
                "reason": "one_of",
                "groups": [
                    ["water_levels", "discharges"],
                    ["input_file", "level_column", "discharge_column"],
                ],
            },
        )
    levels: NDArray[np.float64]
    flows: NDArray[np.float64]
    days: NDArray[np.datetime64] | None = None
    if input_file is not None:
        if level_column is None:
            raise _required_with_file("level_column")
        if discharge_column is None:
            raise _required_with_file("discharge_column")
        table = read_table(input_file)
        levels = table.numbers(level_column, option="level_column")
        flows = table.numbers(discharge_column, option="discharge_column")
        if date_column is not None:
            days = table.dates(date_column, option="date_column")
    else:
        for option, column in (
            ("level_column", level_column),
            ("discharge_column", discharge_column),
            ("date_column", date_column),
        ):
            if column is not None:
                raise InvalidParameterError(
                    f"Option {option!r} applies to 'input_file', not to inline values",
                    details={"option": option, "reason": "conflict"},
                )
        if water_levels is None or discharges is None:
            missing = "discharges" if discharges is None else "water_levels"
            raise InvalidParameterError(
                "Inline 'water_levels' and 'discharges' must be given together",
                details={"option": missing, "reason": "required"},
            )
        levels = _inline_numbers("water_levels", water_levels)
        flows = _inline_numbers("discharges", discharges)
        if levels.shape != flows.shape:
            raise InvalidParameterError(
                "water_levels and discharges must have the same length, got "
                f"{len(levels)} and {len(flows)}",
                details={
                    "option": "discharges",
                    "reason": "length_mismatch",
                    "water_levels": len(levels),
                    "discharges": len(flows),
                },
            )
        if dates is not None:
            days = parse_dates(dates)
            if days.shape != levels.shape:
                raise InvalidParameterError(
                    f"{len(days)} dates for {len(levels)} pairs",
                    details={
                        "option": "dates",
                        "reason": "length_mismatch",
                        "dates": len(days),
                        "water_levels": len(levels),
                    },
                )
    keep = ~(np.isnan(levels) | np.isnan(flows))
    notices: list[Notice] = []
    removed = int(keep.size - np.count_nonzero(keep))
    if removed:
        notices.append(
            notice("missing_pairs_removed", missing=removed, total=int(keep.size))
        )
    return levels[keep], flows[keep], None if days is None else days[keep], notices


def _discharge_at(curve: RatingCurveResult, level: float) -> float | None:
    """Q of a curve at a level; ``None`` at or below H0."""
    if level <= curve.h0:
        return None
    return float(curve.a * (level - curve.h0) ** curve.b)


def _level_at(curve: RatingCurveResult, discharge: float) -> float | None:
    """H of a curve at a discharge; ``None`` when the curve cannot give it."""
    if curve.a <= 0 or curve.b <= 0 or discharge <= 0:
        return None
    return float(curve.h0 + (discharge / curve.a) ** (1.0 / curve.b))


def _rating_periods(
    levels: NDArray[np.float64],
    flows: NDArray[np.float64],
    years: NDArray[np.int_],
    years_per_period: int,
    reference: tuple[float, float],
    fit: Callable[[NDArray[np.float64], NDArray[np.float64]], RatingCurveResult],
) -> list[RatingPeriod]:
    """Fit the curve of each block of ``years_per_period`` hydrological years.

    The blocks start at the years y with (y - 1) mod ``years_per_period`` = 0
    (1951-1960, 1961-1970 for 10), the first and the last cut to the years of the
    pairs.
    """
    first, last = int(years.min()), int(years.max())
    start = first - (first - 1) % years_per_period
    periods: list[RatingPeriod] = []
    while start <= last:
        end = start + years_per_period - 1
        rows = (years >= start) & (years <= end)
        period = RatingPeriod(
            first_year=max(start, first),
            last_year=min(end, last),
            n_pairs=int(rows.sum()),
        )
        if period.n_pairs < _MIN_PERIOD_PAIRS:
            period.reason = "too_few_pairs"
        else:
            try:
                curve = fit(levels[rows], flows[rows])
            except (CalculationError, InvalidParameterError, ArithmeticError):
                period.reason = "fit_failed"
            else:
                for name in (
                    "a",
                    "b",
                    "h0",
                    "r_squared",
                    "std_residuals",
                    "n_points",
                    "n_outliers_removed",
                ):
                    setattr(period, name, getattr(curve, name))
                period.discharge_at_reference_m3s = _discharge_at(curve, reference[0])
                period.level_at_reference_discharge = _level_at(curve, reference[1])
        periods.append(period)
        start += years_per_period
    return periods


def hydrometrics_rating_curve(
    *,
    water_levels: Sequence[float] | None = None,
    discharges: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    level_column: str | None = None,
    discharge_column: str | None = None,
    date_column: str | None = None,
    h0_initial: float | None = None,
    remove_outliers: bool = False,
    outlier_std: float = 2.0,
    first_year: int | None = None,
    last_year: int | None = None,
    years_per_period: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Power-law rating curve Q = a (H - H0)^b (``hydrometrics rating-curve``).

    Fits the rating curve to pairs of water level ``H`` and discharge ``Q`` by
    non-linear least squares (:class:`hydrolog.hydrometrics.RatingCurve`; ``a >= 0``,
    ``b >= 0``, ``H0`` below every observed level; starting point ``a = 1``,
    ``b = 1.5``, ``H0 = h0_initial``, by default chosen from the levels so that it
    works for stages at or below zero). With ``remove_outliers`` the pairs whose
    residual exceeds ``outlier_std`` standard deviations are dropped after the first
    fit and the curve is fitted again (when at least 3 pairs remain).

    Dated pairs (a daily series of H and Q) may be limited to the hydrological years
    ``first_year`` to ``last_year``; with ``years_per_period`` the curve of each block
    of that many years is fitted too (a block with fewer than 30 pairs has no curve)
    and read at the median level and the median discharge of all the pairs, so that
    the shift of the curve between periods is a number.

    Parameters
    ----------
    water_levels : sequence of float, optional
        Inline water levels H (cm or m).
    discharges : sequence of float, optional
        Inline discharges Q [m3/s], one per water level.
    dates : sequence of str, optional
        ISO dates of the inline pairs, one per pair.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the pairs (instead of the inline lists).
    level_column : str, optional
        Column of ``input_file`` with the water levels.
    discharge_column : str, optional
        Column of ``input_file`` with the discharges.
    date_column : str, optional
        Column of ``input_file`` with the dates of the pairs.
    h0_initial : float, optional
        Initial guess of H0, the level of zero flow, in the unit of the levels; below
        the lowest observed level. By default it is chosen from the data: the lowest
        level minus a tenth of the range of the levels (at least one unit), whatever
        the sign of the levels.
    remove_outliers : bool, optional
        Drop outlying pairs and refit, by default ``False``.
    outlier_std : float, optional
        Residual threshold of the outliers in standard deviations, positive, by
        default 2.0.
    first_year, last_year : int, optional
        First and last hydrological year of the pairs fitted; need dates.
    years_per_period : int, optional
        Also fit the curve of each block of this many hydrological years, at least 1;
        needs dates.
    attribution : list of str, optional
        Lines of the providers of the pairs (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`RatingCurveAnalysis`; the notices report pairs
        removed for a missing value (``missing_pairs_removed``) and the warnings of
        NumPy and SciPy (``runtime_warning``, ``user_warning``).

    Raises
    ------
    InvalidParameterError
        If the pairs are given inconsistently or differ in length, ``outlier_std`` is
        not positive, a given ``h0_initial`` is not below the lowest water level, the
        years or periods are asked for without dates, ``first_year`` is after
        ``last_year`` or ``years_per_period`` is below 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 pairs are left, the years have no pair, or the fit does not
        converge.
    """
    cite(attribution)
    if not math.isfinite(outlier_std) or outlier_std <= 0:
        raise InvalidParameterError(
            f"Option 'outlier_std': must be a positive number, got {outlier_std!r}",
            details={
                "option": "outlier_std",
                "reason": "exclusive_minimum",
                "value": str(outlier_std),
            },
        )
    check_years(first_year, last_year)
    if years_per_period is not None and years_per_period < 1:
        raise InvalidParameterError(
            f"Option 'years_per_period': must be at least 1, got {years_per_period}",
            details={"option": "years_per_period", "reason": "minimum", "minimum": 1},
        )
    levels, flows, days, notices = _rating_pairs(
        water_levels,
        discharges,
        dates,
        input_file,
        level_column,
        discharge_column,
        date_column,
    )
    years: NDArray[np.int_] | None = None
    if days is None:
        asked = [
            name
            for name, value in (
                ("first_year", first_year),
                ("last_year", last_year),
                ("years_per_period", years_per_period),
            )
            if value is not None
        ]
        if asked:
            raise InvalidParameterError(
                f"Option {asked[0]!r} needs the dates of the pairs",
                details={
                    "option": "dates" if input_file is None else "date_column",
                    "reason": "required",
                },
                hint="Give the dates of the pairs (dates, or date_column of the file).",
            )
    else:
        years = hydrological_year(days)
        keep = np.ones(years.size, dtype=bool)
        if first_year is not None:
            keep &= years >= first_year
        if last_year is not None:
            keep &= years <= last_year
        if years.size and not keep.any():
            raise CalculationError(
                f"No pair in the hydrological years {first_year} to {last_year}",
                details={
                    "reason": "no_values_in_period",
                    "first_year": first_year,
                    "last_year": last_year,
                    "available": [int(years.min()), int(years.max())],
                },
                hint="Choose hydrological years that the pairs cover.",
            )
        levels, flows, years = levels[keep], flows[keep], years[keep]
    require_count(
        len(levels), _MIN_PAIRS, "Rating curve fitting", unit="measurement pairs"
    )

    def fit(
        levels: NDArray[np.float64], flows: NDArray[np.float64]
    ) -> RatingCurveResult:
        return RatingCurve(levels, flows).fit(
            h0_initial=h0_initial,
            remove_outliers=remove_outliers,
            outlier_std=outlier_std,
        )

    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        curve = fit(levels, flows)
        periods: list[RatingPeriod] | None = None
        reference: tuple[float, float] | None = None
        if years_per_period is not None and years is not None:
            reference = (float(np.median(levels)), float(np.median(flows)))
            periods = _rating_periods(
                levels, flows, years, years_per_period, reference, fit
            )
    result = RatingCurveAnalysis(
        **{
            field.name: getattr(curve, field.name)
            for field in dataclasses.fields(curve)
        },
        first_year=None if years is None else int(years.min()),
        last_year=None if years is None else int(years.max()),
        periods=periods,
        reference_level=None if reference is None else reference[0],
        reference_discharge_m3s=None if reference is None else reference[1],
    )
    return OperationOutput(result, [*notices, *numeric])


def hydrometrics_water_level_zones(
    *,
    values: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    bin_width: float = 10.0,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Rybczyński water level zones (``hydrometrics water-level-zones``).

    Builds the histogram of the water levels (classes of ``bin_width`` starting at the
    lowest level rounded down), its duration curve, and delimits the zones of low (NTW),
    medium (STW) and high (WTW) background water
    (:class:`hydrolog.hydrometrics.WaterLevelFrequency`): NTW ends at the centre of the
    most frequent class, STW at the centre of the first class where the duration curve
    falls below 50 %.

    Parameters
    ----------
    values : sequence of float, optional
        Inline water levels (cm or m).
    input_file : str or os.PathLike, optional
        CSV or JSON file with the water levels (instead of ``values``).
    value_column : str, optional
        Column of ``input_file`` with the water levels.
    bin_width : float, optional
        Width of the histogram classes, in the unit of the levels, positive, by
        default 10.0.
    attribution : list of str, optional
        Lines of the providers of the levels (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`WaterLevelAnalysis`; the notices report removed
        missing values.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``bin_width`` is not positive or so
        small that the histogram would exceed 100000 classes.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing.
    """
    cite(attribution)
    if not math.isfinite(bin_width) or bin_width <= 0:
        raise InvalidParameterError(
            f"Option 'bin_width': must be a positive number, got {bin_width!r}",
            details={
                "option": "bin_width",
                "reason": "exclusive_minimum",
                "value": str(bin_width),
            },
        )
    series, notices = load_valid_series(
        values=values, input_file=input_file, value_column=value_column
    )
    span = float(np.max(series.values)) - float(np.min(series.values))
    if span / bin_width > _MAX_BINS:
        raise InvalidParameterError(
            f"Option 'bin_width': {bin_width:g} is too small for water levels spanning "
            f"{span:g} (more than {_MAX_BINS} classes)",
            details={
                "option": "bin_width",
                "reason": "minimum",
                "minimum": span / _MAX_BINS,
                "value": str(bin_width),
            },
            hint="Use a larger bin_width.",
        )
    analysis = WaterLevelFrequency(series.values, bin_width=bin_width)
    frequency = analysis.frequency_distribution()
    zones = analysis.rybczynski_zones()
    result = WaterLevelAnalysis(
        n_observations=len(series),
        bin_width=float(bin_width),
        zones=zones,
        frequency=frequency,
    )
    return OperationOutput(result, notices)
