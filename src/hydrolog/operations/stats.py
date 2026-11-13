"""Operations of the group ``stats``: statistics of hydrological series.

Characteristic values, events beyond a level, duration curves, runoff volumes, daily
and monthly statistics, flood frequency, low-flow frequency and sequences, the
Mann-Kendall trend test and the homogeneity tests. Every operation loads its series
from inline values or from a file (:func:`hydrolog.catalog.inputs.load_series`),
drops missing values with a notice or keeps them as gaps in the record, and composes
the classes of :mod:`hydrolog.statistics`; the library's own warnings (short series,
...) become the notices of the returned
:class:`~hydrolog.catalog.envelope.OperationOutput`. The functions are re-exported by
:mod:`hydrolog.operations`.

Years are the Polish hydrological years (1 November - 31 October, named after the
calendar year in which they end), the same convention as
:func:`hydrolog.statistics.calculate_characteristic_values`. ``first_year`` and
``last_year`` choose the hydrological years of a daily series (by default the whole
record); a result that describes the period as a whole carries the notice
``short_reference_period`` when it has fewer than 30 years with values (plan
2026-11-13, D1).

The annual maxima of ``stats flood-frequency`` (from a daily series) and the annual
minima of ``stats low-flow`` are extremes of *complete* hydrological years only: a
year in which some day has no value (an absent date or a ``NaN``) is skipped and
named in the ``incomplete_years`` notice and result field (KZGW, 2017; WMO No. 1029,
2009). A calendar-year export therefore loses its first and last hydrological year.
``stats homogeneity`` takes the annual maxima of a daily series the same way (the
skipped years are named in the notice only). The characteristic values keep a year
with missing days and name it (``years_with_missing_days``).
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from hydrolog._attribution import cite
from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput, capture_warnings
from hydrolog.catalog.inputs import Series, load_half_years, load_series
from hydrolog.catalog.notices import notice
from hydrolog.exceptions import CalculationError, HydrologError, InvalidParameterError
from hydrolog.operations._analysis import (
    check_choice,
    check_open_unit_interval,
    check_years,
    load_valid_series,
    reference_period_notices,
    require_count,
    require_values,
    select_years,
)
from hydrolog.statistics import (
    DEFAULT_PERCENTS,
    FIT_METHODS,
    CharacteristicValues,
    DailyStatistics,
    DurationCurve,
    EmpiricalFrequency,
    FitMethod,
    FloodFrequencyAnalysis,
    FrequencyAnalysisResult,
    HalfYearValues,
    HomogeneityResult,
    LowFlowAnalysis,
    LowFlowEmpiricalFrequency,
    LowFlowFrequencyResult,
    MannKendallResult,
    MonthlyStatistics,
    RunoffVolumes,
    ThresholdEvents,
    calculate_characteristic_values,
    calculate_daily_statistics,
    calculate_monthly_statistics,
    characteristic_values_from_half_years,
    duration_curve,
    exceedance_values,
    homogeneity_tests,
    mann_kendall_test,
    runoff_volumes,
    threshold_events,
)
from hydrolog.statistics._hydrological_year import (
    AnnualExtremes,
    annual_extremes,
    describe_incomplete_years,
    hydrological_year,
    incomplete_years_details,
    on_daily_calendar,
)
from hydrolog.statistics.volumes import DAY_SECONDS

__all__ = [
    "DEFAULT_RETURN_PERIODS",
    "FloodFrequencyResult",
    "LowFlowEvent",
    "LowFlowFrequencyAnalysis",
    "LowFlowSequencesResult",
    "LowFlowYear",
    "stats_characteristic",
    "stats_daily",
    "stats_duration_curve",
    "stats_flood_frequency",
    "stats_homogeneity",
    "stats_low_flow",
    "stats_low_flow_sequences",
    "stats_mann_kendall",
    "stats_monthly",
    "stats_runoff_volume",
    "stats_threshold_events",
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
_FIT_METHOD_CHOICES: tuple[str, ...] = (*FIT_METHODS, "all")
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
        complete hydrological year, or the values as given).
    hydrological_years : list of int or None
        Hydrological year of every annual maximum when they were derived from a daily
        series; ``None`` when the annual maxima were given directly.
    best_distribution : str
        ``distribution_name`` of the first entry of ``distributions`` (lowest AIC).
    distributions : list of FrequencyAnalysisResult
        Fitted distributions: parameters, quantiles for the return periods with the
        probability density at each [1/(m³/s)], goodness of fit (K-S,
        Anderson-Darling, AIC) and the ``fit_method`` that gave them. One per
        distribution requested (all four for ``distribution="all"``), each by each
        of the four methods for ``fit_method="all"``; sorted by AIC (best first).
    empirical : EmpiricalFrequency
        Empirical frequency of the sample (Weibull plotting positions; values sorted
        descending, exceedance probabilities and return periods of exceedance).
    incomplete_years : list of int or None
        Hydrological years of the daily series that were skipped because some day
        has no value (empty when every year was complete); ``None`` when the annual
        maxima were given directly.
    fit_method : str
        Method requested: ``"mle"``, ``"moments"``, ``"l_moments"``,
        ``"least_squares"`` or ``"all"`` (every item names its own).
    """

    n_years: int
    annual_maxima: list[float]
    hydrological_years: list[int] | None
    best_distribution: str
    distributions: list[FrequencyAnalysisResult]
    empirical: EmpiricalFrequency
    incomplete_years: list[int] | None = None
    fit_method: str = "l_moments"


@dataclass
class LowFlowFrequencyAnalysis(JsonResultMixin):
    """Low-flow frequency analysis of annual minima.

    Attributes
    ----------
    n_years : int
        Number of complete hydrological years (annual minima) the distribution was
        fitted to.
    hydrological_years : list of int
        Hydrological year of every annual minimum.
    annual_minima : list of float
        Annual minima in the unit of the series, one per complete hydrological year.
    fisher_tippett : LowFlowFrequencyResult
        Fitted Fisher-Tippett distribution of smallest values (GEV for minima):
        parameters, low-flow quantiles for the return periods and K-S statistics.
    empirical : LowFlowEmpiricalFrequency
        Empirical non-exceedance frequency of the annual minima (Weibull plotting
        positions): ``values_ascending``, ``non_exceedance_probabilities``
        ``F = m / (n + 1)`` and ``return_periods`` ``T = 1 / F``, in the same
        convention as ``fisher_tippett`` (the deepest low flow has the smallest
        ``F`` and the longest ``T``).
    incomplete_years : list of int
        Hydrological years of the series that were skipped because some day has no
        value (empty when every year was complete).
    """

    n_years: int
    hydrological_years: list[int]
    annual_minima: list[float]
    fisher_tippett: LowFlowFrequencyResult
    empirical: LowFlowEmpiricalFrequency
    incomplete_years: list[int] = field(default_factory=list)


@dataclass
class LowFlowEvent(JsonResultMixin):
    """One low-flow (drought) sequence of a daily series.

    Attributes
    ----------
    start_date, end_date : str
        First and last day of the sequence (ISO ``YYYY-MM-DD``, inclusive).
    start_index, end_index : int
        Zero-based positions of those days in the series of the period.
    duration_days : int
        Length of the sequence [days], bridged gap days included.
    min_flow, mean_flow : float
        Minimum and mean of the series values inside the sequence (the days with a
        value).
    deficit_volume : float
        Sum of ``threshold - value`` over the days below the threshold, in the unit of
        the series times days (multiply by 86400 for m3 when the unit is m3/s).
    missing_days : int
        Days of the sequence without a value.
    deficit_volume_m3 : float or None
        The deficit as a volume, ``deficit_volume`` times 86,400 s [m³], for a
        discharge series in m³/s (``parameter="Q"``); ``None`` for stages.
    hydrological_year : int
        Hydrological year of the first day; the yearly summary counts the sequence
        there.
    open_start, open_end : bool
        The day before the first (after the last) has no value: the sequence may
        have begun earlier (lasted longer).
    """

    start_date: str
    end_date: str
    start_index: int
    end_index: int
    duration_days: int
    min_flow: float
    mean_flow: float
    deficit_volume: float
    missing_days: int = 0
    deficit_volume_m3: float | None = None
    hydrological_year: int | None = None
    open_start: bool = False
    open_end: bool = False


@dataclass
class LowFlowYear(JsonResultMixin):
    """Low-flow sequences that start in one hydrological year.

    Attributes
    ----------
    year : int
        Hydrological year.
    n_events : int
        Sequences that start in the year.
    duration_days : int
        Their total duration [days] (a sequence may reach into the next year).
    max_duration_days : int
        Duration of the longest of them; 0 without one.
    deficit : float
        Sum of their deficits, in the unit of the series times days.
    deficit_volume_m3 : float or None
        The same as a volume [m³] for discharge (``None`` for stages).
    missing_days : int
        Days of the year without a value, within the period of the series.
    """

    year: int
    n_events: int
    duration_days: int
    max_duration_days: int
    deficit: float
    deficit_volume_m3: float | None
    missing_days: int


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
        Calendar days of the series, from its first to its last date.
    n_events : int
        Number of sequences found.
    total_deficit : float
        Sum of the deficits of all sequences.
    max_duration_days : int
        Duration of the longest sequence [days]; 0 without sequences.
    sequences : list of LowFlowEvent
        The sequences in time order.
    threshold_method : str
        Where the threshold comes from: ``"value"`` (given),
        ``"mean_annual_minimum"`` (SNQ or SNW of the period) or ``"exceedance"``
        (the value of the duration curve at ``exceedance_percent``).
    exceedance_percent : float or None
        The percentage of ``"exceedance"``; ``None`` for the other methods.
    parameter : str
        ``"Q"`` (discharge, deficits also in m³) or ``"H"`` (stage).
    first_year, last_year : int or None
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    n_missing_days : int
        Days of ``n_days`` without a value.
    total_deficit_volume_m3 : float or None
        ``total_deficit`` as a volume [m³] for discharge; ``None`` for stages.
    years : list of LowFlowYear
        Every hydrological year with a value, in order.
    """

    threshold: float
    min_duration_days: int
    max_gap_days: int
    n_days: int
    n_events: int
    total_deficit: float
    max_duration_days: int
    sequences: list[LowFlowEvent]
    threshold_method: str = "value"
    exceedance_percent: float | None = None
    parameter: str = "Q"
    first_year: int | None = None
    last_year: int | None = None
    period_years: int = 0
    n_missing_days: int = 0
    total_deficit_volume_m3: float | None = None
    years: list[LowFlowYear] = field(default_factory=list)


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
    series: Series, kind: Literal["max", "min"]
) -> tuple[AnnualExtremes, list[Notice]]:
    """Maximum or minimum of every complete hydrological year of a dated series.

    The notice (code ``incomplete_years``) names the years that were skipped, with
    the same template and details as the warning of the library.
    """
    extremes = annual_extremes(series.values, _dates_of(series), kind)
    notices: list[Notice] = []
    if extremes.incomplete:
        notices.append(notice("incomplete_years", **incomplete_years_details(extremes)))
    return extremes, notices


def _require_years(extremes: AnnualExtremes, what: str, *, advice: str = "") -> None:
    """Require ``_MIN_ANNUAL_VALUES`` complete hydrological years.

    Parameters
    ----------
    extremes : AnnualExtremes
        Annual extremes of the complete years of the series.
    what : str
        Name of the analysis for the message.
    advice : str, optional
        Sentence appended to the hint when years were skipped.

    Raises
    ------
    CalculationError
        If fewer are available (``details``: ``count``, ``minimum`` and, when years
        were skipped, ``incomplete_years``).
    """
    count = len(extremes.years)
    if count >= _MIN_ANNUAL_VALUES:
        return
    message = (
        f"{what} needs at least {_MIN_ANNUAL_VALUES} complete hydrological years, "
        f"got {count}"
    )
    details: dict[str, Any] = {"count": count, "minimum": _MIN_ANNUAL_VALUES}
    hint = "Provide a longer series."
    if extremes.incomplete:
        message += f"; incomplete years: {describe_incomplete_years(extremes)}"
        details["incomplete_years"] = extremes.incomplete_years
        hint = (
            "A hydrological year counts only with a value for every day of it; "
            "fill the gaps or provide a longer series."
        )
        if advice:
            hint = f"{hint} {advice}"
    raise CalculationError(message, details=details, hint=hint)


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

_PARAMETERS: tuple[str, ...] = ("Q", "H", "T")


def _half_years_of_period(
    half_year_file: str | os.PathLike[str],
    parameter: str,
    first_year: int | None,
    last_year: int | None,
    **daily: object,
) -> HalfYearValues:
    """IMGW-PIB's half-year values of the period, read from ``half_year_file``.

    ``daily`` holds the options of a daily series, which ``half_year_file`` excludes.
    """
    given = [name for name, value in daily.items() if value is not None]
    if given:
        raise InvalidParameterError(
            "Give either a daily series or 'half_year_file', not both",
            details={"option": "half_year_file", "reason": "conflict", "given": given},
            hint="Remove the options of the daily series or half_year_file.",
        )
    whole = load_half_years(half_year_file, parameter)
    half = whole.select(first_year, last_year)

    def known(values: HalfYearValues) -> NDArray[np.bool_]:
        parts = (values.winter, values.summer)
        found = np.isfinite(values.annual_mean)
        for part in parts:
            found |= np.isfinite(part.min) | np.isfinite(part.mean)
            found |= np.isfinite(part.max)
        return found

    if not known(half).any():
        present = whole.years[known(whole)]
        raise CalculationError(
            f"The half-year file has no value of {parameter} in the hydrological years "
            f"{first_year} to {last_year}",
            details={
                "reason": "no_values_in_period",
                "first_year": first_year,
                "last_year": last_year,
                "available": (
                    [int(present.min()), int(present.max())] if present.size else None
                ),
            },
            hint="Choose another parameter or years that the file covers.",
        )
    return half


def stats_characteristic(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    half_year_file: str | os.PathLike[str] | None = None,
    parameter: Literal["Q", "H", "T"] = "Q",
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Characteristic values of the first and second degree (``stats characteristic``).

    Takes the minimum, mean and maximum of each hydrological year (1 November - 31
    October) and of its half-years (XI-IV, V-X) of the period, the first degree, and
    the highest, mean, median and lowest of each over the years, the second degree
    (WWQ ... NNQ for discharge, WWW ... NNW for the stage, WWT ... NNT for water
    temperature), following the IMGW-PIB methodology. The first degree comes from a
    daily series (:func:`hydrolog.statistics.calculate_characteristic_values`) or
    from IMGW-PIB's published half-year characteristics, whose annual maximum is the
    larger of the half-year maxima
    (:func:`hydrolog.statistics.characteristic_values_from_half_years`).

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
    half_year_file : str or os.PathLike, optional
        Obserwator's export of IMGW-PIB's half-year characteristics
        (``pl.imgw.hydro_semiannual``), instead of a daily series
        (:func:`hydrolog.catalog.inputs.load_half_years`).
    parameter : {"Q", "H", "T"}, optional
        The variable: discharge ``"Q"``, stage ``"H"`` or water temperature ``"T"``,
        by default ``"Q"``. It names the labels and the columns of
        ``half_year_file``.
    first_year, last_year : int, optional
        First and last hydrological year of the period, by default those of the
        record.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file`` or ``half_year_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.CharacteristicValues`; the notices
        report removed missing values, years with missing days
        (``years_with_missing_days``) and a period shorter than 30 years
        (``short_reference_period``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent (a daily series with
        ``half_year_file``), ``parameter`` is not allowed or ``first_year`` is after
        ``last_year``.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing or the period has no value.
    """
    cite(attribution)
    check_choice("parameter", parameter, _PARAMETERS)
    check_years(first_year, last_year)
    notices: list[Notice]
    result: CharacteristicValues
    if half_year_file is not None:
        half = _half_years_of_period(
            half_year_file,
            parameter,
            first_year,
            last_year,
            values=values,
            dates=dates,
            input_file=input_file,
            value_column=value_column,
            date_column=date_column,
        )
        result = characteristic_values_from_half_years(half, parameter)
        notices = []
    else:
        series, notices = load_valid_series(
            values=values,
            dates=dates,
            input_file=input_file,
            value_column=value_column,
            date_column=date_column,
            require_dates=True,
        )
        series = select_years(series, first_year, last_year)
        result = calculate_characteristic_values(
            series.values, _dates_of(series), parameter=parameter
        )
        if result.incomplete_years:
            notices.append(
                notice(
                    "years_with_missing_days",
                    count=len(result.incomplete_years),
                    total=result.period_years,
                    years=result.incomplete_years,
                )
            )
    notices.extend(
        reference_period_notices(
            result.period_years, int(result.first_year or 0), int(result.last_year or 0)
        )
    )
    return OperationOutput(result, notices)


def stats_daily(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    attribution: list[str] | None = None,
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
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

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
    cite(attribution)
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
    attribution: list[str] | None = None,
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
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

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
    cite(attribution)
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
        notices.append(notice("single_value_month", months=single))
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
    fit_method: FitMethod | Literal["all"] = "l_moments",
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Flood frequency analysis (``stats flood-frequency``).

    Fits the log-normal, GEV, Pearson type III and Weibull distributions to the annual
    maxima and estimates the quantiles of the given return periods
    (:class:`hydrolog.statistics.FloodFrequencyAnalysis`). The series is either the
    annual maxima themselves (no dates) or a daily series with dates, from which the
    annual maxima of every *complete* hydrological year are taken first (a year with
    a day without a value is skipped and named in the ``incomplete_years`` notice).

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
        Distribution to fit; ``"all"`` fits the four, by default ``"all"``. The fits
        are sorted by AIC.
    return_periods : sequence of float, optional
        Return periods [years], each greater than 1, by default
        ``DEFAULT_RETURN_PERIODS``.
    fit_method : {"mle", "moments", "l_moments", "least_squares", "all"}, optional
        Method that estimates the parameters (ADR-0021), by default ``"l_moments"``;
        ``"all"`` fits each distribution by each of the four methods.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028), e.g. those of the hand-off
        it came from; the envelope carries them, with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`FloodFrequencyResult`; the notices report removed
        missing values, skipped incomplete years (code ``incomplete_years``) and the
        warnings of the fit: a sample of fewer than 10 years (``small_sample``) or of
        fewer than the 30 years of the KZGW 2017 methodology (``short_record``), a
        K-S test that is not valid for fitted parameters (``ks_test_approximate``), a
        combination of a distribution and a method that gives it no parameters, left
        out when several are fitted (``distribution_left_out``), and annual maxima
        without density under a fitted distribution, whose AIC is then null
        (``outside_support``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``distribution`` or ``fit_method``
        is not allowed or a return period is not greater than 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 annual maxima (complete hydrological years) are available, a
        fit fails numerically, or ``fit_method`` gives no parameters of the
        distribution requested (of none of the four for ``"all"``).
    """
    cite(attribution)
    check_choice("distribution", distribution, _DISTRIBUTIONS)
    check_choice("fit_method", fit_method, _FIT_METHOD_CHOICES)
    periods = _return_periods(return_periods)
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
    )
    hydrological_years: list[int] | None = None
    incomplete_years: list[int] | None = None
    if series.dates is None:
        maxima = series.values
        require_count(
            len(maxima),
            _MIN_ANNUAL_VALUES,
            "Flood frequency analysis",
            unit="annual maxima",
        )
    else:
        extremes, year_notices = _annual_extremes(series, "max")
        _require_years(
            extremes,
            "Flood frequency analysis",
            advice="Annual maxima that are already extracted go without dates.",
        )
        maxima = extremes.values
        hydrological_years = [int(year) for year in extremes.years]
        incomplete_years = extremes.incomplete_years
        notices.extend(year_notices)
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        analysis = FloodFrequencyAnalysis(maxima, periods)
        fitted: list[FrequencyAnalysisResult] = list(
            _fit(
                "the four flood frequency distributions"
                if distribution == "all"
                else f"the {distribution} distribution",
                lambda: analysis.fit_all(
                    fit_method=fit_method, distribution=distribution
                ),
            ).values()
        )
        empirical = analysis.empirical_frequency()
    result = FloodFrequencyResult(
        n_years=len(maxima),
        annual_maxima=[float(value) for value in maxima],
        hydrological_years=hydrological_years,
        best_distribution=fitted[0].distribution_name,
        distributions=fitted,
        empirical=empirical,
        incomplete_years=incomplete_years,
        fit_method=fit_method,
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
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Low-flow frequency analysis (``stats low-flow``).

    Takes the annual minima of a daily series by complete hydrological year (a year
    with a day without a value is skipped and named in the ``incomplete_years``
    notice), fits the Fisher-Tippett distribution of smallest values (GEV for minima)
    to them and estimates the low-flow quantile of every return period: the value not
    exceeded once in ``T`` years, with non-exceedance probability ``1 / T``
    (:class:`hydrolog.statistics.LowFlowAnalysis`; WMO No. 1029, 2009; Tallaksen and
    van Lanen, 2004). The empirical block uses the same convention (ascending annual
    minima with non-exceedance probabilities ``F = m / (n + 1)`` and return periods
    ``T = 1 / F``).

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
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`LowFlowFrequencyAnalysis`; the notices report removed
        missing values, skipped incomplete years (code ``incomplete_years``) and the
        warnings of the fit (fewer than 10 years: ``small_sample``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or a return period is not greater
        than 1.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If the series has fewer than 3 complete hydrological years or the fit fails.
    """
    cite(attribution)
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
    extremes, year_notices = _annual_extremes(series, "min")
    _require_years(extremes, "Low-flow frequency analysis")
    # The analysis takes the complete years of the days it is given; hand it those
    # only, so that the skipped years are reported once, in the notice above.
    complete = np.isin(hydrological_year(dates_array), extremes.years)
    analysis = LowFlowAnalysis(series.values[complete], dates_array[complete], periods)
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        fitted: LowFlowFrequencyResult = _fit(
            "the Fisher-Tippett distribution", analysis.fit_fisher_tippett
        )
        empirical = analysis.empirical_non_exceedance()
    result = LowFlowFrequencyAnalysis(
        n_years=len(extremes.years),
        hydrological_years=[int(year) for year in extremes.years],
        annual_minima=[float(value) for value in extremes.values],
        fisher_tippett=fitted,
        empirical=empirical,
        incomplete_years=extremes.incomplete_years,
    )
    return OperationOutput(result, [*notices, *year_notices, *numeric])


_THRESHOLD_METHODS: tuple[str, ...] = ("value", "mean_annual_minimum", "exceedance")


def _low_flow_threshold(
    series: Series,
    threshold: float | None,
    threshold_method: str,
    exceedance_percent: float,
) -> float:
    """Return the low-flow threshold: the given one or one from the series."""
    if threshold_method == "value":
        if threshold is None:
            raise InvalidParameterError(
                "Option 'threshold' is required with threshold_method 'value'",
                details={"option": "threshold", "reason": "required"},
                hint=(
                    "Give threshold, or threshold_method mean_annual_minimum or "
                    "exceedance to take it from the series."
                ),
            )
        if not (math.isfinite(threshold) and threshold > 0):
            raise InvalidParameterError(
                f"Option 'threshold': must be a positive number, got {threshold!r}",
                details={
                    "option": "threshold",
                    "reason": "exclusive_minimum",
                    "value": str(threshold),
                },
            )
        return float(threshold)
    if threshold is not None:
        raise InvalidParameterError(
            f"Option 'threshold' applies to threshold_method 'value', not "
            f"{threshold_method!r}",
            details={"option": "threshold", "reason": "conflict"},
        )
    known = ~np.isnan(series.values)
    if threshold_method == "mean_annual_minimum":
        characteristic = calculate_characteristic_values(
            series.values[known], _dates_of(series)[known]
        )
        return float(characteristic.snx)
    return float(exceedance_values(series.values[known], [exceedance_percent])[0])


def stats_low_flow_sequences(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    threshold: float | None = None,
    threshold_method: Literal["value", "mean_annual_minimum", "exceedance"] = "value",
    exceedance_percent: float = 70.0,
    parameter: Literal["Q", "H"] = "Q",
    min_duration_days: int = 5,
    max_gap_days: int = 4,
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Low-flow sequences by the threshold level method (``stats low-flow-sequences``).

    A sequence is a run of days with a value below the threshold; two runs separated
    by a gap shorter than ``max_gap_days`` days are merged, and only sequences lasting
    at least ``min_duration_days`` days are kept
    (:meth:`hydrolog.statistics.LowFlowAnalysis.detect_sequences`; Tallaksen and van
    Lanen, 2004). The series may have gaps (missing values, absent dates): a day
    without a value is never below the threshold and counts as a gap day. The
    threshold is given, or the mean of the annual minima of the period (SNQ, SNW:
    ``snx`` of :func:`hydrolog.statistics.calculate_characteristic_values`), or the
    value of the duration curve exceeded on ``exceedance_percent`` % of the days
    (Q70, Q90: :func:`hydrolog.statistics.exceedance_values`). The yearly summary
    counts a sequence in the hydrological year in which it starts.

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
    threshold : float, optional
        Threshold, positive, in the unit of the series; required with
        ``threshold_method="value"`` and only with it.
    threshold_method : {"value", "mean_annual_minimum", "exceedance"}, optional
        Where the threshold comes from, by default ``"value"``.
    exceedance_percent : float, optional
        The exceedance percentage of ``"exceedance"``, in (0, 100), by default 70.
    parameter : {"Q", "H"}, optional
        Discharge in m³/s (the deficits are also volumes in m³) or stage, by default
        ``"Q"``.
    min_duration_days : int, optional
        Shortest sequence reported [days], at least 1, by default 5.
    max_gap_days : int, optional
        Gaps shorter than this [days] between two runs are bridged, by default 4.
    first_year, last_year : int, optional
        First and last hydrological year of the period, by default those of the
        record.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`LowFlowSequencesResult`; with a threshold from the
        series, the notices report a period shorter than 30 years
        (``short_reference_period``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``threshold`` is missing or given
        with another method, a choice is not allowed, ``exceedance_percent`` is not
        in (0, 100), ``min_duration_days`` is below 1, ``max_gap_days`` below 0 or
        ``first_year`` after ``last_year``.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing, the period has no value, or the threshold is not
        positive (``details.reason`` ``threshold_not_positive``).
    """
    cite(attribution)
    check_choice("threshold_method", threshold_method, _THRESHOLD_METHODS)
    check_choice("parameter", parameter, ("Q", "H"))
    _check_percent("exceedance_percent", exceedance_percent)
    _check_days(min_duration_days, max_gap_days)
    series = require_values(
        load_series(
            values=values,
            dates=dates,
            input_file=input_file,
            value_column=value_column,
            date_column=date_column,
            require_dates=True,
        )
    )
    series = select_years(series, first_year, last_year)
    dates_array = _dates_of(series)
    level = _low_flow_threshold(series, threshold, threshold_method, exceedance_percent)
    if not (math.isfinite(level) and level > 0):
        raise CalculationError(
            f"The low-flow threshold must be positive, got {level:g}",
            details={
                "reason": "threshold_not_positive",
                "threshold": level,
                "threshold_method": threshold_method,
            },
            hint="Give a positive threshold or another threshold_method.",
        )
    found = LowFlowAnalysis(series.values, dates_array).detect_sequences(
        threshold=level,
        min_duration_days=min_duration_days,
        max_gap_days=max_gap_days,
    )
    volumes = parameter == "Q"

    def volume(deficit: float) -> float | None:
        return deficit * DAY_SECONDS if volumes else None

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
            missing_days=sequence.missing_days,
            deficit_volume_m3=volume(sequence.deficit_volume),
            hydrological_year=int(
                hydrological_year(
                    dates_array[sequence.start_index : sequence.start_index + 1]
                )[0]
            ),
            open_start=sequence.open_start,
            open_end=sequence.open_end,
        )
        for sequence in found.sequences
    ]
    calendar, daily = on_daily_calendar(series.values, dates_array)
    calendar_years = hydrological_year(calendar)
    known = ~np.isnan(daily)
    years: list[LowFlowYear] = []
    for year in np.unique(calendar_years[known]).tolist():
        mine = [event for event in events if event.hydrological_year == year]
        deficit = float(sum(event.deficit_volume for event in mine))
        years.append(
            LowFlowYear(
                year=int(year),
                n_events=len(mine),
                duration_days=sum(event.duration_days for event in mine),
                max_duration_days=max(
                    (event.duration_days for event in mine), default=0
                ),
                deficit=deficit,
                deficit_volume_m3=volume(deficit),
                missing_days=int((~known[calendar_years == year]).sum()),
            )
        )
    result = LowFlowSequencesResult(
        threshold=found.threshold,
        min_duration_days=min_duration_days,
        max_gap_days=max_gap_days,
        n_days=int(daily.size),
        n_events=found.n_events,
        total_deficit=found.total_deficit,
        max_duration_days=found.max_duration_days,
        sequences=events,
        threshold_method=threshold_method,
        exceedance_percent=(
            float(exceedance_percent) if threshold_method == "exceedance" else None
        ),
        parameter=parameter,
        first_year=years[0].year,
        last_year=years[-1].year,
        period_years=len(years),
        n_missing_days=int((~known).sum()),
        total_deficit_volume_m3=volume(found.total_deficit),
        years=years,
    )
    notices: list[Notice] = []
    if threshold_method != "value":
        notices = reference_period_notices(len(years), years[0].year, years[-1].year)
    return OperationOutput(result, notices)


def _check_percent(option: str, value: float) -> float:
    """Require a percentage in the open interval (0, 100)."""
    if not (math.isfinite(value) and 0.0 < value < 100.0):
        raise InvalidParameterError(
            f"Option {option!r}: must be a percentage in the open interval (0, 100), "
            f"got {value!r}",
            details={"option": option, "reason": "range", "value": str(value)},
        )
    return float(value)


def _check_days(min_duration_days: int, max_gap_days: int) -> None:
    """Require ``min_duration_days`` >= 1 and ``max_gap_days`` >= 0."""
    for option, value, minimum in (
        ("min_duration_days", min_duration_days, 1),
        ("max_gap_days", max_gap_days, 0),
    ):
        if value < minimum:
            raise InvalidParameterError(
                f"Option {option!r}: must be at least {minimum}, got {value}",
                details={
                    "option": option,
                    "reason": "minimum",
                    "minimum": minimum,
                    "value": str(value),
                },
            )


# --- events beyond a level, duration curves, runoff volumes ---------------------------


def stats_threshold_events(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    level: float,
    direction: Literal["above", "below"] = "above",
    min_duration_days: int = 1,
    max_gap_days: int = 0,
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Events and days beyond a level (``stats threshold-events``).

    Lays the daily series on its calendar and finds the runs of days with a value at
    or above ``level`` (``direction="above"``) or below it (``"below"``): start, end,
    duration and peak of each, and the days beyond the level in each hydrological
    year (:func:`hydrolog.statistics.threshold_events`; the threshold level method,
    Tallaksen and van Lanen, 2004). A day without a value ends a run unless
    ``max_gap_days`` bridges it.

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
    level : float
        The level, in the unit of the series.
    direction : {"above", "below"}, optional
        Days at or above the level (default) or below it.
    min_duration_days : int, optional
        Shortest event reported [days], at least 1, by default 1.
    max_gap_days : int, optional
        Events parted by fewer days merge, at least 0, by default 0.
    first_year, last_year : int, optional
        First and last hydrological year of the period, by default those of the
        record.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.ThresholdEvents`.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``level`` is not finite,
        ``direction`` is not allowed, ``min_duration_days`` is below 1,
        ``max_gap_days`` below 0 or ``first_year`` after ``last_year``.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing or the period has no value.
    """
    cite(attribution)
    check_choice("direction", direction, ("above", "below"))
    if not math.isfinite(level):
        raise InvalidParameterError(
            f"Option 'level': must be a finite number, got {level!r}",
            details={"option": "level", "reason": "type", "value": str(level)},
        )
    _check_days(min_duration_days, max_gap_days)
    series = require_values(
        load_series(
            values=values,
            dates=dates,
            input_file=input_file,
            value_column=value_column,
            date_column=date_column,
            require_dates=True,
        )
    )
    series = select_years(series, first_year, last_year)
    result: ThresholdEvents = threshold_events(
        series.values,
        _dates_of(series),
        level=level,
        direction=direction,
        min_duration_days=min_duration_days,
        max_gap_days=max_gap_days,
    )
    return OperationOutput(result)


def stats_duration_curve(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
    month: int | None = None,
    percents: Sequence[float] = DEFAULT_PERCENTS,
    class_method: Literal["width", "log"] = "width",
    class_width: float = 10.0,
    class_count: int = 40,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Duration curve with class frequencies (``stats duration-curve``).

    The value equalled or exceeded on p % of the days of the period (or of one
    calendar month of it), from the Weibull plotting positions m / (n + 1) of the
    values ranked from the highest, interpolated between ranks, and the days of each
    class of values from the highest down with the cumulative days including higher
    and lower and their split by hydrological month
    (:func:`hydrolog.statistics.duration_curve`).

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
    first_year, last_year : int, optional
        First and last hydrological year of the period, by default those of the
        record.
    month : int, optional
        Only the days of this calendar month (1-12).
    percents : sequence of float, optional
        Exceedance percentages of the table, each in (0, 100), by default 1, 5, 10,
        30, 50, 70, 90, 95, 99.
    class_method : {"width", "log"}, optional
        Classes of equal width (default) or logarithmic classes.
    class_width : float, optional
        Width of the classes in the unit of the series, positive, by default 10.
    class_count : int, optional
        Number of logarithmic classes, at least 2, by default 40.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.DurationCurve`; the notices
        report removed missing values and a period shorter than 30 years
        (``short_reference_period``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent or an option is out of its range.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing or the period (its ``month``) has no value.
    """
    cite(attribution)
    check_choice("class_method", class_method, ("width", "log"))
    for percent in percents:
        _check_percent("percents", percent)
    if not percents:
        raise InvalidParameterError(
            "Option 'percents': must not be an empty list",
            details={"option": "percents", "reason": "empty"},
        )
    if not (math.isfinite(class_width) and class_width > 0):
        raise InvalidParameterError(
            f"Option 'class_width': must be a positive number, got {class_width!r}",
            details={
                "option": "class_width",
                "reason": "exclusive_minimum",
                "value": str(class_width),
            },
        )
    if class_count < 2:
        raise InvalidParameterError(
            f"Option 'class_count': must be at least 2, got {class_count}",
            details={"option": "class_count", "reason": "minimum", "minimum": 2},
        )
    if month is not None and not 1 <= month <= 12:
        raise InvalidParameterError(
            f"Option 'month': must be a month 1 to 12, got {month}",
            details={"option": "month", "reason": "range", "value": str(month)},
        )
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        require_dates=True,
    )
    series = select_years(series, first_year, last_year)
    dates_array = _dates_of(series)
    if month is not None:
        months = dates_array.astype("datetime64[M]").astype(np.int64) % 12 + 1
        if not (months == month).any():
            raise CalculationError(
                f"No value in month {month} of the period",
                details={"reason": "no_values_in_month", "month": month},
                hint="Choose another month or a longer period.",
            )
    result: DurationCurve = duration_curve(
        series.values,
        dates_array,
        month=month,
        percents=percents,
        class_method=class_method,
        class_width=class_width,
        class_count=class_count,
    )
    notices.extend(
        reference_period_notices(
            result.period_years, result.first_year, result.last_year
        )
    )
    return OperationOutput(result, notices)


def stats_runoff_volume(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
    cumulative_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Annual and monthly runoff volumes (``stats runoff-volume``).

    The volume V = Σ Q · 86,400 s [m³] of each hydrological year of the period and of
    its months, their means over the complete years and months, and the cumulative
    volume of one year beside the mean cumulative volume of the complete years
    (:func:`hydrolog.statistics.runoff_volumes`).

    Parameters
    ----------
    values : sequence of float, optional
        Inline daily discharges [m³/s] in time order; needs ``dates``.
    dates : sequence of str, optional
        ISO dates ``YYYY-MM-DD``, strictly increasing, one per value.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values`` and ``dates``).
    value_column : str, optional
        Column of ``input_file`` with the discharges.
    date_column : str, optional
        Column of ``input_file`` with the dates.
    first_year, last_year : int, optional
        First and last hydrological year of the period, by default those of the
        record.
    cumulative_year : int, optional
        The hydrological year of the cumulative volume, by default the last complete
        year of the period.
    attribution : list of str, optional
        Lines of the providers of the discharges (ADR-0028); the envelope carries
        them, with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.RunoffVolumes`; the notices
        report a period shorter than 30 years (``short_reference_period``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``first_year`` is after
        ``last_year`` or ``cumulative_year`` has no value in the period.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If every value is missing or the period has no value.
    """
    cite(attribution)
    series = require_values(
        load_series(
            values=values,
            dates=dates,
            input_file=input_file,
            value_column=value_column,
            date_column=date_column,
            require_dates=True,
        )
    )
    series = select_years(series, first_year, last_year)
    dates_array = _dates_of(series)
    if cumulative_year is not None:
        known = hydrological_year(dates_array[~np.isnan(series.values)])
        if cumulative_year not in set(known.tolist()):
            raise InvalidParameterError(
                f"Option 'cumulative_year': {cumulative_year} has no value in the "
                "period",
                details={
                    "option": "cumulative_year",
                    "reason": "range",
                    "minimum": int(known.min()),
                    "maximum": int(known.max()),
                },
                hint="Choose a hydrological year of the period that has values.",
            )
    result: RunoffVolumes = runoff_volumes(
        series.values, dates_array, cumulative_year=cumulative_year
    )
    notices = reference_period_notices(
        result.period_years, result.first_year, result.last_year
    )
    return OperationOutput(result, notices)


# --- trend ----------------------------------------------------------------------------


def stats_mann_kendall(
    *,
    values: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    alpha: float = 0.05,
    attribution: list[str] | None = None,
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
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

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
    cite(attribution)
    level = check_open_unit_interval("alpha", alpha)
    series, notices = load_valid_series(
        values=values, input_file=input_file, value_column=value_column
    )
    require_count(len(series), _MIN_TREND_VALUES, "The Mann-Kendall test")
    result: MannKendallResult = mann_kendall_test(series.values, alpha=level)
    return OperationOutput(result, notices)


# --- homogeneity ----------------------------------------------------------------------

_TESTS: tuple[str, ...] = ("mann_whitney", "kolmogorov_smirnov", "pettitt")


def stats_homogeneity(
    *,
    values: Sequence[float] | None = None,
    dates: Sequence[str] | None = None,
    years: Sequence[int] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    year_column: str | None = None,
    split_year: int | None = None,
    alpha: float = 0.05,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Homogeneity tests of annual maxima (``stats homogeneity``, ADR-0022).

    Splits the annual maxima in two at ``split_year`` (by default into halves) and
    compares the parts with the two-sided Mann-Whitney U test and the two-sample
    Kolmogorov-Smirnov test; Pettitt's test finds the most probable change point
    (:func:`hydrolog.statistics.homogeneity_tests`). The series is the annual maxima
    themselves (no dates; their years, if given, name the split and the change
    point) or a daily series with dates, whose annual maxima of the *complete*
    hydrological years are taken first (a year with a day without a value is skipped
    and named in the ``incomplete_years`` notice).

    Parameters
    ----------
    values : sequence of float, optional
        Inline series: annual maxima, or daily values when ``dates`` is given.
    dates : sequence of str, optional
        ISO dates of daily ``values``; omit when ``values`` are annual maxima.
    years : sequence of int, optional
        Years of the annual maxima in ``values`` (whole numbers, strictly
        increasing); not with ``dates``.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the series (instead of ``values``).
    value_column : str, optional
        Column of ``input_file`` with the values.
    date_column : str, optional
        Column of ``input_file`` with the dates; omit for annual maxima.
    year_column : str, optional
        Column of ``input_file`` with the years of the annual maxima; not with
        ``date_column``.
    split_year : int, optional
        First year of the second part; needs years (``years``, ``year_column`` or the
        dates of a daily series). By default the first half of the values, ``n // 2``,
        is the first part.
    alpha : float, optional
        Significance level of the tests, in (0, 1), by default 0.05.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.HomogeneityResult`; the notices
        report removed missing values, skipped incomplete years
        (``incomplete_years``) and the tests that reject homogeneity at ``alpha``
        (``homogeneity_rejected``).

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent, ``alpha`` is outside (0, 1), the
        years are not whole numbers or not strictly increasing, or ``split_year`` is
        given without years or leaves a part empty.
    NotFoundError, InputDataError
        If the file does not exist or cannot be read.
    CalculationError
        If fewer than 3 annual maxima (complete hydrological years) are available or
        all of them are equal.
    """
    cite(attribution)
    level = check_open_unit_interval("alpha", alpha)
    series, notices = load_valid_series(
        values=values,
        dates=dates,
        years=years,
        input_file=input_file,
        value_column=value_column,
        date_column=date_column,
        year_column=year_column,
    )
    labels: NDArray[np.integer] | None
    if series.dates is None:
        maxima, labels = series.values, series.years
        require_count(
            len(maxima), _MIN_ANNUAL_VALUES, "Homogeneity testing", unit="annual maxima"
        )
    else:
        extremes, year_notices = _annual_extremes(series, "max")
        _require_years(
            extremes,
            "Homogeneity testing",
            advice="Annual maxima that are already extracted go without dates.",
        )
        maxima, labels = extremes.values, extremes.years
        notices.extend(year_notices)
    if split_year is not None and labels is None:
        raise InvalidParameterError(
            "Option 'split_year' needs the years of the annual maxima",
            details={
                "option": "years" if input_file is None else "year_column",
                "reason": "required",
            },
            hint=(
                "Give the years of the annual maxima (years, or year_column of the "
                "file) or a daily series with dates, or leave out split_year to split "
                "the series into halves."
            ),
        )
    with capture_warnings(_NUMERIC_WARNINGS) as numeric:
        result: HomogeneityResult = homogeneity_tests(
            maxima, labels, split_year=split_year, alpha=level
        )
    rejected = [name for name in _TESTS if not getattr(result, name).homogeneous]
    if rejected:
        notices.append(notice("homogeneity_rejected", tests=rejected, alpha=level))
    return OperationOutput(result, [*notices, *numeric])
