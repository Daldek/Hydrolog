"""Operations of the group ``stats``: statistics of hydrological series.

Characteristic values, daily and monthly statistics, flood frequency, low-flow
frequency and sequences, and the Mann-Kendall trend test. Every operation loads its
series from inline values or from a file (:func:`hydrolog.catalog.inputs.load_series`),
drops missing values with a notice and composes the classes of
:mod:`hydrolog.statistics`; the library's own warnings (short series, ...) become the
notices of the returned :class:`~hydrolog.catalog.envelope.OperationOutput`. The
functions are re-exported by :mod:`hydrolog.operations`.

Years are the Polish hydrological years (1 November - 31 October, named after the
calendar year in which they end), the same convention as
:func:`hydrolog.statistics.calculate_characteristic_values`.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.catalog.inputs import Series, load_series
from hydrolog.exceptions import CalculationError, HydrologError, InvalidParameterError
from hydrolog.operations._analysis import (
    check_choice,
    check_open_unit_interval,
    load_valid_series,
    require_count,
)
from hydrolog.statistics import (
    CharacteristicValues,
    DailyStatistics,
    EmpiricalFrequency,
    FloodFrequencyAnalysis,
    FrequencyAnalysisResult,
    LowFlowAnalysis,
    LowFlowFrequencyResult,
    MannKendallResult,
    MonthlyStatistics,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
    mann_kendall_test,
)
from hydrolog.statistics._hydrological_year import hydrological_year

__all__ = [
    "DEFAULT_RETURN_PERIODS",
    "FloodFrequencyResult",
    "LowFlowEvent",
    "LowFlowFrequencyAnalysis",
    "LowFlowSequencesResult",
    "stats_characteristic",
    "stats_daily",
    "stats_flood_frequency",
    "stats_low_flow",
    "stats_low_flow_sequences",
    "stats_mann_kendall",
    "stats_monthly",
]

DEFAULT_RETURN_PERIODS: tuple[float, ...] = (
    2.0,
    5.0,
    10.0,
    20.0,
    50.0,
    100.0,
    500.0,
    1000.0,
)
"""Return periods [years] used when none are given (the library default)."""

Distribution = Literal["all", "log_normal", "gev", "pearson3", "weibull"]

_DISTRIBUTIONS: tuple[str, ...] = ("all", "log_normal", "gev", "pearson3", "weibull")
_FIT_METHODS: dict[str, str] = {
    "log_normal": "fit_log_normal",
    "gev": "fit_gev",
    "pearson3": "fit_pearson3",
    "weibull": "fit_weibull",
}
# Three parameters cannot be estimated from fewer than three annual values.
_MIN_ANNUAL_VALUES = 3
_MIN_TREND_VALUES = 3  # the Mann-Kendall test of the library needs 3 observations
_NUMERIC_WARNINGS: tuple[type[Warning], ...] = (UserWarning, RuntimeWarning)
_ONE_DAY = np.timedelta64(1, "D")


# --- results --------------------------------------------------------------------------


@dataclass
class FloodFrequencyResult(JsonResultMixin):
    """Flood frequency analysis of annual maxima.

    Attributes
    ----------
    n_years : int
        Number of annual maxima the distributions were fitted to.
    annual_maxima : list of float
        The sample: annual maxima in time order (derived from a daily series by
        hydrological year, or the values as given).
    hydrological_years : list of int or None
        Hydrological year of every annual maximum when they were derived from a daily
        series; ``None`` when the annual maxima were given directly.
    best_distribution : str
        ``distribution_name`` of the first entry of ``distributions`` (lowest AIC).
    distributions : list of FrequencyAnalysisResult
        Fitted distributions: parameters, quantiles for the return periods and
        goodness of fit (K-S, Anderson-Darling, AIC). All four sorted by AIC
        (best first) for ``distribution="all"``, otherwise the one requested.
    empirical : EmpiricalFrequency
        Empirical frequency of the sample (Weibull plotting positions).
    """

    n_years: int
    annual_maxima: list[float]
    hydrological_years: list[int] | None
    best_distribution: str
    distributions: list[FrequencyAnalysisResult]
    empirical: EmpiricalFrequency


@dataclass
class LowFlowFrequencyAnalysis(JsonResultMixin):
    """Low-flow frequency analysis of annual minima.

    Attributes
    ----------
    n_years : int
        Number of hydrological years (annual minima) in the series.
    hydrological_years : list of int
        Hydrological year of every annual minimum.
    annual_minima : list of float
        Annual minima in the unit of the series, one per hydrological year.
    fisher_tippett : LowFlowFrequencyResult
        Fitted Fisher-Tippett distribution of smallest values (GEV for minima):
        parameters, low-flow quantiles for the return periods and K-S statistics.
    empirical : EmpiricalFrequency
        Empirical frequency of the annual minima (Weibull plotting positions; values
        sorted descending, exceedance probabilities).
    """

    n_years: int
    hydrological_years: list[int]
    annual_minima: list[float]
    fisher_tippett: LowFlowFrequencyResult
    empirical: EmpiricalFrequency


@dataclass
class LowFlowEvent(JsonResultMixin):
    """One low-flow (drought) sequence of a daily series.

    Attributes
    ----------
    start_date, end_date : str
        First and last day of the sequence (ISO ``YYYY-MM-DD``, inclusive).
    start_index, end_index : int
        Zero-based positions of those days in the series.
    duration_days : int
        Length of the sequence [days].
    min_flow, mean_flow : float
        Minimum and mean of the series values inside the sequence.
    deficit_volume : float
        Sum of ``threshold - value`` over the days below the threshold, in the unit of
        the series times days (multiply by 86400 for m3 when the unit is m3/s).
    """

    start_date: str
    end_date: str
    start_index: int
    end_index: int
    duration_days: int
    min_flow: float
    mean_flow: float
    deficit_volume: float


@dataclass
class LowFlowSequencesResult(JsonResultMixin):
    """Low-flow sequences of a daily series (threshold level method).

    Attributes
    ----------
    threshold : float
        Threshold used, in the unit of the series.
    min_duration_days : int
        Shortest sequence reported [days].
    max_gap_days : int
        Gaps shorter than this many days between two runs below the threshold are
        bridged.
    n_days : int
        Length of the series [days].
    n_events : int
        Number of sequences found.
    total_deficit : float
        Sum of the deficits of all sequences.
    max_duration_days : int
        Duration of the longest sequence [days]; 0 without sequences.
    sequences : list of LowFlowEvent
        The sequences in time order.
    """

    threshold: float
    min_duration_days: int
    max_gap_days: int
    n_days: int
    n_events: int
    total_deficit: float
    max_duration_days: int
    sequences: list[LowFlowEvent]


# --- helpers --------------------------------------------------------------------------


def _dates_of(series: Series) -> NDArray[np.datetime64]:
    """Dates of a series loaded with ``require_dates=True``."""
    if series.dates is None:
        raise InvalidParameterError(
            "The series has no dates",
            details={"option": "dates", "reason": "required"},
        )
    return series.dates


def _return_periods(return_periods: Sequence[float]) -> NDArray[np.float64]:
    """Return periods as an array; each must be a finite number above 1 year."""
    problem = {
        "option": "return_periods",
        "reason": "range",
        "value": str(return_periods),
    }
    try:
        periods = np.asarray(return_periods, dtype=np.float64)
    except (TypeError, ValueError):
        periods = np.array([np.nan])
    if (
        periods.ndim != 1
        or periods.size == 0
        or not np.all(np.isfinite(periods))
        or np.any(periods <= 1.0)
    ):
        raise InvalidParameterError(
            "Option 'return_periods': must be a non-empty list of finite numbers "
            "greater than 1 (years)",
            details=problem,
        )
    return periods


def _annual_extremes(
    series: Series, reduce: Callable[[NDArray[np.float64]], Any]
) -> tuple[list[int], NDArray[np.float64]]:
    """Maximum or minimum of every hydrological year of a dated series."""
    years = hydrological_year(_dates_of(series))
    labels = np.unique(years)
    extremes = np.array(
        [reduce(series.values[years == label]) for label in labels], dtype=np.float64
    )
    return [int(label) for label in labels], extremes


def _fit(what: str, fit: Callable[[], Any]) -> Any:
    """Run a fit; a numerical failure is a ``CalculationError``.

    Errors of Hydrolog itself pass unchanged (``InvalidParameterError`` is also a
    ``ValueError``, which would otherwise be reported as a numerical failure).
    """
    try:
        return fit()
    except HydrologError:
        raise
    except (ArithmeticError, ValueError, RuntimeError) as exc:
        raise CalculationError(
            f"Fitting {what} failed: {exc}",
            details={"fit": what},
            hint="Check the series for constant or implausible values.",
        ) from exc


# --- characteristic values and daily / monthly statistics -----------------------------


def stats_characteristic(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    parameter: Literal["Q", "H"] = "Q",
) -> OperationOutput:
    """Second-degree characteristic values (``stats characteristic``).

    Groups a daily series by hydrological year (1 November - 31 October), takes the
    annual maximum, mean and minimum and derives from each of these three series the
    highest, mean, median and lowest value (WWQ ... NNQ for discharge, WWH ... NNH for
    stage), following the IMGW-PIB methodology
    (:func:`hydrolog.statistics.calculate_characteristic_values`).

    Parameters
    ----------
    values : sequence of float, optional
        Inline daily values in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, strictly increasing, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates.
    parameter : {"Q", "H"}, optional
        Label of the series: discharge ``"Q"`` or stage ``"H"``, by default ``"Q"``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.CharacteristicValues`; the notices
        report removed missing values.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or ``parameter`` is not allowed.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing.
    """
    check_choice("parameter", parameter, ("Q", "H"))
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    result: CharacteristicValues = calculate_characteristic_values(
        series.values, _dates_of(series), parameter=parameter
    )
    return OperationOutput(result, notices)


def stats_daily(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
) -> OperationOutput:
    """Statistics per day of the hydrological year (``stats daily``).

    For every day of the hydrological year (1 = 1 November) gives the maximum, mean,
    median, minimum and number of observations over all years of the series
    (:func:`hydrolog.statistics.calculate_daily_statistics`).

    Parameters
    ----------
    values : sequence of float, optional
        Inline daily values in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, strictly increasing, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.DailyStatistics`; the notices
        report removed missing values.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing.
    """
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    result: DailyStatistics = calculate_daily_statistics(
        series.values, _dates_of(series)
    )
    return OperationOutput(result, notices)


def stats_monthly(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    confidence_level: float = 0.95,
) -> OperationOutput:
    """Monthly statistics with a confidence interval (``stats monthly``).

    Per calendar month (1-12) gives the maximum, mean, median, minimum, standard
    deviation (``ddof=1``), coefficient of variation, skewness and the t-Student
    confidence interval of the mean over all values of that month
    (:func:`hydrolog.statistics.calculate_monthly_statistics`). The series must hold
    values in every calendar month.

    Parameters
    ----------
    values : sequence of float, optional
        Inline values in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, strictly increasing, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates.
    confidence_level : float, optional
        Confidence level of the interval, in (0, 1), by default 0.95.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.MonthlyStatistics`; the notices
        report removed missing values and months with a single value (they have no
        standard deviation, coefficient of variation, skewness or confidence
        interval: ``None`` in JSON), and numerical warnings.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or ``confidence_level`` is outside
        (0, 1).
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing or a calendar month has no value
        (``details.missing_months``).
    """
    confidence = check_open_unit_interval("confidence_level", confidence_level)
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    dates_array = _dates_of(series)
    months = dates_array.astype("datetime64[M]").astype(int) % 12 + 1
    # The library rejects a series without a month as an invalid parameter; as a
    # series that is too short (like require_count) it is a calculation error here.
    counts = np.bincount(months, minlength=13)[1:]  # observations of month 1..12
    absent = [month for month in range(1, 13) if counts[month - 1] == 0]
    if absent:
        raise CalculationError(
            "Monthly statistics need values in every calendar month; no values in "
            f"month(s): {', '.join(str(month) for month in absent)}",
            details={"missing_months": absent},
            hint="Provide a series that covers at least one full year.",
        )
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        result: MonthlyStatistics = calculate_monthly_statistics(
            series.values, dates_array, confidence_level=confidence
        )
    single = [month for month in range(1, 13) if counts[month - 1] == 1]
    if single:
        notices.append(
            Notice(
                "warning",
                "single_value_month",
                f"Month(s) {', '.join(str(month) for month in single)} hold a single "
                "value: their standard deviation, coefficient of variation, skewness "
                "and confidence interval are undefined (null)",
            )
        )
    return OperationOutput(result, [*notices, *numeric])


# --- flood frequency ------------------------------------------------------------------


def stats_flood_frequency(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    distribution: Distribution = "all",
    return_periods: Sequence[float] = DEFAULT_RETURN_PERIODS,
) -> OperationOutput:
    """Flood frequency analysis (``stats flood-frequency``).

    Fits the log-normal, GEV, Pearson type III and Weibull distributions to the annual
    maxima and estimates the quantiles of the given return periods
    (:class:`hydrolog.statistics.FloodFrequencyAnalysis`). The series is either the
    annual maxima themselves (no dates) or a daily series with dates, from which the
    annual maxima of every hydrological year are taken first.

    Parameters
    ----------
    values : sequence of float, optional
        Inline series: annual maxima, or daily values when ``dates`` is given.
    dates : sequence of str, optional
        ISO dates of daily ``values``; omit when ``values`` are annual maxima.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates; omit for annual maxima.
    distribution : {"all", "log_normal", "gev", "pearson3", "weibull"}, optional
        Distribution to fit; ``"all"`` fits the four and sorts them by AIC, by default
        ``"all"``.
    return_periods : sequence of float, optional
        Return periods [years], each greater than 1, by default
        ``DEFAULT_RETURN_PERIODS``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`FloodFrequencyResult`; the notices report removed
        missing values and the warnings of the fit (short sample: fewer than 30 years
        in the KZGW 2017 methodology, fewer than 10 years unreliable; the K-S test is
        not valid for fitted parameters).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``distribution`` is not allowed or a
        return period is not greater than 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 annual maxima are available or a fit fails numerically.
    """
    check_choice("distribution", distribution, _DISTRIBUTIONS)
    periods = _return_periods(return_periods)
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
    )
    hydrological_years: list[int] | None = None
    if series.dates is None:
        maxima = series.values
    else:
        hydrological_years, maxima = _annual_extremes(series, np.max)
    require_count(
        len(maxima),
        _MIN_ANNUAL_VALUES,
        "Flood frequency analysis",
        unit="annual maxima",
    )
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        analysis = FloodFrequencyAnalysis(maxima, periods)
        fitted: list[FrequencyAnalysisResult]
        if distribution == "all":
            fitted = list(
                _fit(
                    "the four flood frequency distributions", analysis.fit_all
                ).values()
            )
        else:
            fitted = [
                _fit(
                    f"the {distribution} distribution",
                    getattr(analysis, _FIT_METHODS[distribution]),
                )
            ]
        empirical = analysis.empirical_frequency()
    result = FloodFrequencyResult(
        n_years=len(maxima),
        annual_maxima=[float(value) for value in maxima],
        hydrological_years=hydrological_years,
        best_distribution=fitted[0].distribution_name,
        distributions=fitted,
        empirical=empirical,
    )
    return OperationOutput(result, [*notices, *numeric])


# --- low flows ------------------------------------------------------------------------


def stats_low_flow(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    return_periods: Sequence[float] = DEFAULT_RETURN_PERIODS,
) -> OperationOutput:
    """Low-flow frequency analysis (``stats low-flow``).

    Takes the annual minima of a daily series by hydrological year, fits the
    Fisher-Tippett distribution of smallest values (GEV for minima) to them and
    estimates the low-flow quantile of every return period: the value not exceeded
    once in ``T`` years, with non-exceedance probability ``1 / T``
    (:class:`hydrolog.statistics.LowFlowAnalysis`; WMO No. 1029, 2009; Tallaksen and
    van Lanen, 2004).

    Parameters
    ----------
    values : sequence of float, optional
        Inline daily values in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, strictly increasing, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates.
    return_periods : sequence of float, optional
        Return periods [years], each greater than 1, by default
        ``DEFAULT_RETURN_PERIODS``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`LowFlowFrequencyAnalysis`; the notices report removed
        missing values and the warnings of the fit (fewer than 10 years: unreliable).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or a return period is not greater
        than 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If the series spans fewer than 3 hydrological years or the fit fails.
    """
    periods = _return_periods(return_periods)
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    dates_array = _dates_of(series)
    n_years = len(np.unique(hydrological_year(dates_array)))
    require_count(
        n_years,
        _MIN_ANNUAL_VALUES,
        "Low-flow frequency analysis",
        unit="hydrological years",
    )
    analysis = LowFlowAnalysis(series.values, dates_array, periods)
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        years, minima = _annual_extremes(series, np.min)
        fitted: LowFlowFrequencyResult = _fit(
            "the Fisher-Tippett distribution", analysis.fit_fisher_tippett
        )
        empirical = analysis.empirical_frequency()
    result = LowFlowFrequencyAnalysis(
        n_years=len(minima),
        hydrological_years=years,
        annual_minima=[float(value) for value in minima],
        fisher_tippett=fitted,
        empirical=empirical,
    )
    return OperationOutput(result, [*notices, *numeric])


def stats_low_flow_sequences(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    threshold: float,
    min_duration_days: int = 5,
    max_gap_days: int = 4,
) -> OperationOutput:
    """Low-flow sequences by the threshold level method (``stats low-flow-sequences``).

    A sequence is a run of days with a value below ``threshold``; two runs separated
    by a gap shorter than ``max_gap_days`` days are merged, and only sequences lasting
    at least ``min_duration_days`` days are kept
    (:meth:`hydrolog.statistics.LowFlowAnalysis.detect_sequences`; Tallaksen and van
    Lanen, 2004). The series must be a complete daily series.

    Parameters
    ----------
    values : sequence of float, optional
        Inline daily values in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, consecutive days, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates.
    threshold : float
        Threshold flow, positive, in the unit of the series.
    min_duration_days : int, optional
        Shortest sequence reported [days], at least 1, by default 5.
    max_gap_days : int, optional
        Gaps shorter than this [days] between two runs are bridged, by default 4.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`LowFlowSequencesResult`.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``threshold`` is not positive or
        ``min_duration_days`` is below 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If the series has missing values or its dates are not consecutive days
        (``details.reason``: ``missing_values`` or ``date_gap``).
    """
    series = load_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    dates_array = _dates_of(series)
    if series.n_missing:
        first = int(np.flatnonzero(np.isnan(series.values))[0])
        raise CalculationError(
            f"The series has {series.n_missing} missing value(s) (the first on "
            f"{dates_array[first]}); sequences can only be detected in a gapless "
            "daily series",
            details={
                "reason": "missing_values",
                "n_missing": series.n_missing,
                "first_missing_date": str(dates_array[first]),
            },
            hint="Fill the missing days or cut the series at the gap.",
        )
    jumps = np.flatnonzero(np.diff(dates_array) != _ONE_DAY)
    if jumps.size:
        before = int(jumps[0])
        raise CalculationError(
            f"The dates are not consecutive days: {dates_array[before]} is followed by "
            f"{dates_array[before + 1]}; sequences can only be detected in a gapless "
            "daily series",
            details={
                "reason": "date_gap",
                "after": str(dates_array[before]),
                "next": str(dates_array[before + 1]),
                "n_gaps": int(jumps.size),
            },
            hint="Fill the missing days or cut the series at the gap.",
        )
    analysis = LowFlowAnalysis(series.values, dates_array)
    found = analysis.detect_sequences(
        threshold=threshold,
        min_duration_days=min_duration_days,
        max_gap_days=max_gap_days,
    )
    events = [
        LowFlowEvent(
            start_date=str(dates_array[sequence.start_index]),
            end_date=str(dates_array[sequence.end_index]),
            start_index=sequence.start_index,
            end_index=sequence.end_index,
            duration_days=sequence.duration_days,
            min_flow=sequence.min_flow,
            mean_flow=sequence.mean_flow,
            deficit_volume=sequence.deficit_volume,
        )
        for sequence in found.sequences
    ]
    result = LowFlowSequencesResult(
        threshold=found.threshold,
        min_duration_days=min_duration_days,
        max_gap_days=max_gap_days,
        n_days=len(series),
        n_events=found.n_events,
        total_deficit=found.total_deficit,
        max_duration_days=found.max_duration_days,
        sequences=events,
    )
    return OperationOutput(result)


# --- trend ----------------------------------------------------------------------------


def stats_mann_kendall(
    *,
    values: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    alpha: float = 0.05,
) -> OperationOutput:
    """Mann-Kendall trend test (``stats mann-kendall``).

    Non-parametric test for a monotonic trend in a series ordered in time (Mann,
    1945; Kendall, 1975): the S statistic, its variance (without the correction for
    ties, so the test is slightly conservative), the continuity-corrected Z score and
    the two-sided p-value (:func:`hydrolog.statistics.mann_kendall_test`).

    Parameters
    ----------
    values : sequence of float, optional
        Inline series in time order, e.g. annual maxima.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values``); rows in time order.
    value_column : str, optional
        Column of ``input_file`` with the values.
    alpha : float, optional
        Significance level, in (0, 1), by default 0.05.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.MannKendallResult`; the notices
        report removed missing values.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or ``alpha`` is outside (0, 1).
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 values are left.
    """
    level = check_open_unit_interval("alpha", alpha)
    series, notices = load_valid_series(
        values=values, input_file=input_file, value_column=value_column
    )
    require_count(len(series), _MIN_TREND_VALUES, "The Mann-Kendall test")
    result: MannKendallResult = mann_kendall_test(series.values, alpha=level)
    return OperationOutput(result, notices)
