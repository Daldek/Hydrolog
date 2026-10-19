"""Operations of the group ``hydrometrics``: rating curves and water level zones.

Power-law rating curve fitting (:class:`hydrolog.hydrometrics.RatingCurve`) and
Rybczyński water level zones (:class:`hydrolog.hydrometrics.WaterLevelFrequency`) for
inline values or files. The functions are re-exported by :mod:`hydrolog.operations`.
"""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.catalog.inputs import read_table
from hydrolog.exceptions import InvalidParameterError
from hydrolog.hydrometrics import (
    FrequencyDistributionResult,
    RatingCurve,
    RatingCurveResult,
    WaterLevelFrequency,
    WaterLevelZones,
)
from hydrolog.operations._analysis import load_valid_series, require_count

__all__ = [
    "WaterLevelAnalysis",
    "hydrometrics_rating_curve",
    "hydrometrics_water_level_zones",
]

_MIN_PAIRS = 3  # the rating curve has three parameters
_MAX_BINS = 100_000  # guards the histogram of the water level zones against a tiny bin
_NUMERIC_WARNINGS: tuple[type[Warning], ...] = (UserWarning, RuntimeWarning)


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
    input_file: str | os.PathLike[str] | None,
    level_column: str | None,
    discharge_column: str | None,
) -> tuple[NDArray[np.float64], NDArray[np.float64], list[Notice]]:
    """Measurement pairs without missing values, and the notice about removed pairs."""
    inline = water_levels is not None or discharges is not None
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
    if input_file is not None:
        if level_column is None:
            raise _required_with_file("level_column")
        if discharge_column is None:
            raise _required_with_file("discharge_column")
        table = read_table(input_file)
        levels = table.numbers(level_column, option="level_column")
        flows = table.numbers(discharge_column, option="discharge_column")
    else:
        for option, column in (
            ("level_column", level_column),
            ("discharge_column", discharge_column),
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
    keep = ~(np.isnan(levels) | np.isnan(flows))
    notices: list[Notice] = []
    removed = int(keep.size - np.count_nonzero(keep))
    if removed:
        notices.append(
            Notice(
                "warning",
                "missing_values_removed",
                f"{removed} of {keep.size} measurement pairs have a missing value "
                "(NaN) and were removed before the fit",
            )
        )
    return levels[keep], flows[keep], notices


def hydrometrics_rating_curve(
    *,
    water_levels: Sequence[float] | None = None,
    discharges: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    level_column: str | None = None,
    discharge_column: str | None = None,
    h0_initial: float | None = None,
    remove_outliers: bool = False,
    outlier_std: float = 2.0,
) -> OperationOutput:
    """Power-law rating curve Q = a (H - H0)^b (``hydrometrics rating-curve``).

    Fits the rating curve to pairs of water level ``H`` and discharge ``Q`` by
    non-linear least squares (:class:`hydrolog.hydrometrics.RatingCurve`; ``a >= 0``,
    ``b >= 0``, ``H0`` below every observed level; starting point ``a = 1``,
    ``b = 1.5``, ``H0 = h0_initial``, by default chosen from the levels so that it
    works for stages at or below zero). With ``remove_outliers`` the pairs whose
    residual exceeds ``outlier_std`` standard deviations are dropped after the first
    fit and the curve is fitted again (when at least 3 pairs remain).

    Parameters
    ----------
    water_levels : sequence of float, optional
        Inline water levels H (cm or m).
    discharges : sequence of float, optional
        Inline discharges Q [m3/s], one per water level.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the pairs (instead of the inline lists).
    level_column : str, optional
        Column of ``input_file`` with the water levels.
    discharge_column : str, optional
        Column of ``input_file`` with the discharges.
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

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.hydrometrics.RatingCurveResult`; the notices
        report pairs removed for a missing value and numerical warnings.

    Raises
    ------
    InvalidParameterError
        If the pairs are given inconsistently or differ in length, ``outlier_std`` is
        not positive, or a given ``h0_initial`` is not below the lowest water level.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 pairs are left or the fit does not converge.
    """
    if not math.isfinite(outlier_std) or outlier_std <= 0:
        raise InvalidParameterError(
            f"Option 'outlier_std': must be a positive number, got {outlier_std!r}",
            details={
                "option": "outlier_std",
                "reason": "exclusive_minimum",
                "value": str(outlier_std),
            },
        )
    levels, flows, notices = _rating_pairs(
        water_levels, discharges, input_file, level_column, discharge_column
    )
    require_count(
        len(levels), _MIN_PAIRS, "Rating curve fitting", unit="measurement pairs"
    )
    curve = RatingCurve(levels, flows)
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        result: RatingCurveResult = curve.fit(
            h0_initial=h0_initial,
            remove_outliers=remove_outliers,
            outlier_std=outlier_std,
        )
    return OperationOutput(result, [*notices, *numeric])


def hydrometrics_water_level_zones(
    *,
    values: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    bin_width: float = 10.0,
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
