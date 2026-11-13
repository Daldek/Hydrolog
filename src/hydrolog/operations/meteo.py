"""Operations of the group ``meteo``: statistics of a meteorological station.

Precipitation (sums and normals, maxima, days, intensity, heavy precipitation,
seasonality), dry and wet spells, the standardized precipitation index with the
relative precipitation, air temperature (means and normals, characteristic days,
degree days, the daily range), snow cover and Sielianinov's hydrothermal coefficient
of a daily series (Nogat's plan, M1 to M14 without M3, M12 and M13; plan 2026-11-13,
D12). The computations are in :mod:`hydrolog.statistics`.

A series comes from Obserwator's daily export of a meteorological station
(``obserwator series export``: ``date``, ``P [mm]``, ``P_flag``, ``Tmax [degC]``,
``Tmin [degC]``, ``Tmean [degC]``, ``snow_cover [cm]``, ``fresh_snow [cm]``...), each
variable from its column (``precipitation_column`` and the like, by default the
export's name; the unit suffix may be left out), or from inline lists with ``dates``.
A precipitation value flagged ``accumulated`` (``precipitation_flag_column``, by
default ``P_flag`` when the file has it) is a multi-day total of the missing days
before it: it stands for them in the monthly sums (WMO-No. 1203, 4.4.1 c) and is a
missing day for every daily statistic.

Years are calendar years by default and hydrological years (November - October, named
after the year in which they end) with ``year_type`` ``hydrological``; ``first_year``
and ``last_year`` choose the years of that kind (by default the whole record), and a
result that describes the period carries the notice ``short_reference_period`` when
it has fewer than 30 years with a value (plan 2026-11-13, D1). Snow cover is counted
per winter, a snow season August - July named after the year in which it ends (the
hydrological year of its winter); the hydrothermal coefficient per calendar year.
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Sequence
from typing import Any, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog._attribution import cite
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.catalog.inputs import Table, parse_dates, read_table
from hydrolog.catalog.notices import notice
from hydrolog.exceptions import CalculationError, InputDataError, InvalidParameterError
from hydrolog.operations._analysis import (
    check_choice,
    check_years,
    reference_period_notices,
)
from hydrolog.statistics import (
    DEFAULT_DURATIONS_DAYS,
    DEFAULT_PERCENTILES,
    DEFAULT_SCALES_MONTHS,
    DEFAULT_SPELL_THRESHOLD_MM,
    DEFAULT_THRESHOLDS_MM,
    DEFAULT_WET_DAY_MM,
    PRECIPITATION_INDICES,
    TEMPERATURE_INDICES,
    YEAR_TYPES,
    degree_days,
    heavy_precipitation,
    hydrothermal_coefficient,
    precipitation_days,
    precipitation_intensity,
    precipitation_maxima,
    precipitation_seasonality,
    precipitation_spells,
    precipitation_sums,
    snow_cover,
    standardized_precipitation_index,
    temperature_days,
    temperature_means,
    temperature_range,
)
from hydrolog.statistics._climate import SNOW_SEASON, WMO_NORMAL_SHARE, year_of

__all__ = [
    "meteo_hydrothermal",
    "meteo_precipitation",
    "meteo_snow",
    "meteo_spells",
    "meteo_spi",
    "meteo_temperature",
]

_UNIT_SUFFIX = re.compile(r"\s*\[[^\]]*\]\s*$")
_ACCUMULATED = "accumulated"


class _Variable(NamedTuple):
    """A daily variable: its inline option, its column option and the export's name."""

    inline: str
    column: str
    default: str


_P = _Variable("precipitation_mm", "precipitation_column", "P")
_TMEAN = _Variable("tmean_c", "tmean_column", "Tmean")
_TMAX = _Variable("tmax_c", "tmax_column", "Tmax")
_TMIN = _Variable("tmin_c", "tmin_column", "Tmin")
_SNOW = _Variable("snow_cover_cm", "snow_cover_column", "snow_cover")
_FRESH = _Variable("fresh_snow_cm", "fresh_snow_column", "fresh_snow")


class _Wanted(NamedTuple):
    """A variable an operation reads: its inline values, its column, whether needed."""

    variable: _Variable
    values: Sequence[object] | NDArray[Any] | None
    column: str | None
    required: bool


class _Station(NamedTuple):
    """The daily series of a station: dates and values by inline option name."""

    dates: NDArray[np.datetime64]
    values: dict[str, NDArray[np.float64]]
    accumulated: NDArray[np.bool_] | None
    flag_column: str | None


# --- loading --------------------------------------------------------------------------


def _inline_numbers(
    option: str, values: Sequence[object] | NDArray[Any]
) -> NDArray[np.float64]:
    """``float64`` array of an inline list; ``None`` is a missing value."""
    try:
        if isinstance(values, str) or any(
            isinstance(item, bool | str) for item in values
        ):
            raise TypeError
        array = np.asarray(
            [math.nan if item is None else item for item in values], dtype=np.float64
        )
    except (TypeError, ValueError):
        raise InvalidParameterError(
            f"Option {option!r}: must be a list of numbers",
            details={"option": option, "reason": "type"},
        ) from None
    if array.ndim != 1 or array.size == 0 or bool(np.isinf(array).any()):
        raise InvalidParameterError(
            f"Option {option!r}: must be a non-empty list of finite numbers",
            details={"option": option, "reason": "type"},
        )
    return array


def _first_not_increasing(dates: NDArray[np.datetime64]) -> int | None:
    """Return the 1-based row of the first date not after the one before, if any."""
    if dates.size < 2:
        return None
    bad = np.flatnonzero(dates[1:] <= dates[:-1])
    return int(bad[0]) + 2 if bad.size else None


def _has_column(table: Table, name: str) -> bool:
    try:
        table.resolve_column(name)
    except InputDataError as exc:
        if exc.details.get("reason") == "missing_column":
            return False
        raise
    return True


def _file_dates(table: Table, date_column: str | None) -> NDArray[np.datetime64]:
    days = table.dates(date_column or "date", option="date_column")
    row = _first_not_increasing(days)
    if row is not None:
        raise InputDataError(
            f"{table.source}: row {row}: date {days[row - 1]} does not come after "
            f"{days[row - 2]}",
            details={
                "path": str(table.source),
                "reason": "dates_not_increasing",
                "row": row,
                "value": str(days[row - 1]),
            },
            hint="Dates of a series must be strictly increasing (sorted, unique).",
        )
    return days


def _accumulated(
    table: Table, precipitation_column: str, flag_column: str | None
) -> tuple[NDArray[np.bool_] | None, str | None]:
    """Read the ``accumulated`` flags of a precipitation column, and their column."""
    if flag_column is None:
        name = _UNIT_SUFFIX.sub("", precipitation_column) + "_flag"
        if not _has_column(table, name):
            return None, None
    else:
        name = flag_column
    resolved = table.resolve_column(name, option="precipitation_flag_column")
    cells = table.data[resolved]
    flags = np.array(
        [isinstance(cell, str) and cell.strip() == _ACCUMULATED for cell in cells],
        dtype=bool,
    )
    return flags, resolved


def _load(
    *,
    dates: Sequence[object] | NDArray[Any] | None,
    input_file: str | os.PathLike[str] | None,
    date_column: str | None,
    wanted: Sequence[_Wanted],
    flag_column: str | None = None,
) -> _Station:
    """Read the daily series an operation needs, from inline lists or a file.

    Raises
    ------
    InvalidParameterError
        If both or neither source is given, a needed series is missing, a file option
        is given with inline lists, the lengths differ or the dates do not increase.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read, lacks a needed column or has
        dates that do not increase.
    """
    inline = dates is not None or any(item.values is not None for item in wanted)
    if inline == (input_file is not None):
        groups = [
            ["dates", *(item.variable.inline for item in wanted if item.required)],
            ["input_file"],
        ]
        raise InvalidParameterError(
            "Give either inline 'dates' with the daily values or 'input_file'",
            details={
                "option": "input_file" if input_file is not None else "dates",
                "reason": "one_of",
                "groups": groups,
            },
        )
    values: dict[str, NDArray[np.float64]] = {}
    if input_file is not None:
        table = read_table(input_file)
        days = _file_dates(table, date_column)
        accumulated: NDArray[np.bool_] | None = None
        used_flags: str | None = None
        for item in wanted:
            name = item.column if item.column is not None else item.variable.default
            if (
                item.column is None
                and not item.required
                and not _has_column(table, name)
            ):
                continue
            values[item.variable.inline] = table.numbers(
                name, option=item.variable.column
            )
            if item.variable is _P:
                resolved = table.resolve_column(name, option=_P.column)
                accumulated, used_flags = _accumulated(table, resolved, flag_column)
        return _Station(days, values, accumulated, used_flags)
    for option, given in (
        ("date_column", date_column),
        ("precipitation_flag_column", flag_column),
        *((item.variable.column, item.column) for item in wanted),
    ):
        if given is not None:
            raise InvalidParameterError(
                f"Option {option!r} applies to 'input_file', not to inline values",
                details={"option": option, "reason": "conflict"},
            )
    if dates is None:
        raise InvalidParameterError(
            "Inline daily values need 'dates'",
            details={"option": "dates", "reason": "required"},
        )
    days = parse_dates(dates)
    row = _first_not_increasing(days)
    if row is not None:
        raise InvalidParameterError(
            f"Option 'dates': item {row - 1} ({days[row - 1]}) does not come after "
            f"{days[row - 2]}",
            details={
                "option": "dates",
                "reason": "dates_not_increasing",
                "index": row - 1,
                "value": str(days[row - 1]),
            },
            hint="Dates of a series must be strictly increasing (sorted, unique).",
        )
    for item in wanted:
        if item.values is None:
            if item.required:
                raise InvalidParameterError(
                    f"Option {item.variable.inline!r} is required with inline 'dates'",
                    details={"option": item.variable.inline, "reason": "required"},
                )
            continue
        array = _inline_numbers(item.variable.inline, item.values)
        if array.size != days.size:
            raise InvalidParameterError(
                f"{days.size} dates for {array.size} values of "
                f"{item.variable.inline!r}",
                details={
                    "option": item.variable.inline,
                    "reason": "length_mismatch",
                    "dates": int(days.size),
                    "values": int(array.size),
                },
            )
        values[item.variable.inline] = array
    return _Station(days, values, None, None)


def _check_not_negative(
    station: _Station, variable: _Variable, input_file: str | os.PathLike[str] | None
) -> None:
    """Refuse a negative precipitation or snow depth."""
    values = station.values.get(variable.inline)
    if values is None:
        return
    bad = np.flatnonzero(np.isfinite(values) & (values < 0))
    if not bad.size:
        return
    at = int(bad[0])
    if input_file is not None:
        raise InputDataError(
            f"{input_file}: row {at + 1}: {variable.default} = {values[at]:g} is "
            "negative",
            details={
                "path": str(input_file),
                "reason": "negative_value",
                "column": variable.default,
                "row": at + 1,
                "value": f"{values[at]:g}",
            },
        )
    raise InvalidParameterError(
        f"Option {variable.inline!r}: item {at} is negative ({values[at]:g})",
        details={"option": variable.inline, "reason": "minimum", "minimum": 0},
    )


def _select(
    station: _Station,
    year_type: str,
    first_year: int | None,
    last_year: int | None,
    keys: Sequence[str],
) -> _Station:
    """Keep the days of the years ``first_year`` to ``last_year`` of ``year_type``.

    Raises
    ------
    InvalidParameterError
        If ``first_year`` is after ``last_year``.
    CalculationError
        If no value of ``keys`` is known at all (``no_values``) or in the years
        (``no_values_in_period``).
    """
    check_years(first_year, last_year)
    known = np.zeros(station.dates.size, dtype=bool)
    for key in keys:
        if key in station.values:
            known |= np.isfinite(station.values[key])
    if not known.any():
        raise CalculationError(
            f"All {station.dates.size} days of the series are missing; nothing to "
            "analyse",
            details={"reason": "no_values", "n_values": int(station.dates.size)},
            hint="Check the columns: they hold no numbers.",
        )
    years = year_of(station.dates, year_type)
    keep = np.ones(station.dates.size, dtype=bool)
    if first_year is not None:
        keep &= years >= first_year
    if last_year is not None:
        keep &= years <= last_year
    if not (keep & known).any():
        present = years[known]
        raise CalculationError(
            f"No value in the years {first_year} to {last_year}",
            details={
                "reason": "no_values_in_period",
                "first_year": first_year,
                "last_year": last_year,
                "available": [int(present.min()), int(present.max())],
            },
            hint="Choose years that the series covers.",
        )
    if keep.all():
        return station
    accumulated = None if station.accumulated is None else station.accumulated[keep]
    return _Station(
        station.dates[keep],
        {key: values[keep] for key, values in station.values.items()},
        accumulated,
        station.flag_column,
    )


# --- notices --------------------------------------------------------------------------


def _accumulated_notices(station: _Station) -> list[Notice]:
    if station.accumulated is None:
        return []
    precipitation = station.values.get(_P.inline)
    flagged = station.accumulated
    if precipitation is not None:
        flagged = flagged & np.isfinite(precipitation)
    count = int(flagged.sum())
    if not count:
        return []
    return [notice("accumulated_totals", count=count, column=station.flag_column)]


def _normal_notices(
    normal_value: float | None,
    years: int,
    first_year: int,
    last_year: int,
) -> list[Notice]:
    if normal_value is not None:
        return []
    return [
        notice(
            "normal_not_computed",
            years=years,
            required=math.ceil(WMO_NORMAL_SHARE * (last_year - first_year + 1)),
            first_year=first_year,
            last_year=last_year,
        )
    ]


def _period_notices(result: Any) -> list[Notice]:
    return reference_period_notices(
        result.period_years, result.first_year, result.last_year
    )


def _year_type(year_type: str) -> str:
    return check_choice("year_type", year_type, YEAR_TYPES)


# --- precipitation --------------------------------------------------------------------


def meteo_precipitation(
    *,
    index: Literal["sums", "maxima", "days", "intensity", "heavy", "seasonality"],
    dates: Sequence[str] | None = None,
    precipitation_mm: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    precipitation_column: str | None = None,
    precipitation_flag_column: str | None = None,
    year_type: Literal["calendar", "hydrological"] = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    durations_days: Sequence[int] = DEFAULT_DURATIONS_DAYS,
    thresholds_mm: Sequence[float] = DEFAULT_THRESHOLDS_MM,
    wet_day_mm: float = DEFAULT_WET_DAY_MM,
    percentiles: Sequence[float] = DEFAULT_PERCENTILES,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Precipitation statistics of a daily series (``meteo precipitation``).

    One ``index`` per call (:mod:`hydrolog.statistics.meteo_precipitation`): ``sums``
    of months, half-years, seasons and years with the normals of the period and the
    sums in % of them (M1); ``maxima``, the largest daily sums of each year and month
    and the largest sums of ``durations_days`` with dates (M2); ``days`` with P at or
    above ``thresholds_mm`` (M5); ``intensity``, the mean annual sum and the SDII
    (M4); ``heavy``, the sums above the ``percentiles`` of the wet days (R95pTOT,
    R99pTOT; M7); ``seasonality``, the regime of the normals, PCI and SI (M9).

    Parameters
    ----------
    index : {"sums", "maxima", "days", "intensity", "heavy", "seasonality"}
        The statistic.
    dates : sequence of str, optional
        ISO dates of the inline values, strictly increasing.
    precipitation_mm : sequence of float, optional
        Inline daily precipitation [mm], one per date.
    input_file : str or os.PathLike, optional
        CSV or JSON file with the daily series (Obserwator's export).
    date_column : str, optional
        Column of the dates, default ``date``.
    precipitation_column : str, optional
        Column of the precipitation [mm], default ``P``.
    precipitation_flag_column : str, optional
        Column of the flags of the precipitation; by default ``P_flag`` (the
        precipitation column's name and ``_flag``) when the file has it.
    year_type : {"calendar", "hydrological"}, optional
        Calendar years (default) or hydrological years (November - October).
    first_year, last_year : int, optional
        First and last year of the period, by default those of the record.
    durations_days : sequence of int, optional
        ``maxima``: durations of the largest multi-day sums [days], default 2, 3, 5,
        10.
    thresholds_mm : sequence of float, optional
        ``days``: thresholds [mm], default 0.1, 1, 10, 20.
    wet_day_mm : float, optional
        ``intensity`` and ``heavy``: a wet day has at least this precipitation [mm],
        default 1.
    percentiles : sequence of float, optional
        ``heavy``: percentiles of the wet days, default 95 and 99.
    attribution : list of str, optional
        Lines of the providers of the series (ADR-0028); the envelope carries them,
        with those of ``input_file``.

    Returns
    -------
    OperationOutput
        ``result`` is the index's result of :mod:`hydrolog.statistics`; the notices
        report accumulated totals (``accumulated_totals``), a normal that cannot be
        computed (``normal_not_computed``) and a period shorter than 30 years
        (``short_reference_period``).

    Raises
    ------
    InvalidParameterError
        If an option is invalid or the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read or lacks a column.
    CalculationError
        If the series or the period has no value, or ``heavy`` has fewer than 100
        wet days.
    """
    cite(attribution)
    check_choice("index", index, PRECIPITATION_INDICES)
    _year_type(year_type)
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[_Wanted(_P, precipitation_mm, precipitation_column, True)],
        flag_column=precipitation_flag_column,
    )
    _check_not_negative(station, _P, input_file)
    station = _select(station, year_type, first_year, last_year, [_P.inline])
    values = station.values[_P.inline]
    common: dict[str, Any] = {
        "accumulated": station.accumulated,
        "year_type": year_type,
    }
    notices = _accumulated_notices(station)
    result: Any
    if index == "sums":
        result = precipitation_sums(values, station.dates, **common)
        notices += _normal_notices(
            result.period.normal_mm,
            result.period.normal_years,
            result.first_year,
            result.last_year,
        )
    elif index == "maxima":
        result = precipitation_maxima(
            values, station.dates, durations_days=durations_days, **common
        )
    elif index == "days":
        result = precipitation_days(
            values, station.dates, thresholds_mm=thresholds_mm, **common
        )
    elif index == "intensity":
        result = precipitation_intensity(
            values, station.dates, wet_day_mm=wet_day_mm, **common
        )
    elif index == "heavy":
        result = heavy_precipitation(
            values,
            station.dates,
            wet_day_mm=wet_day_mm,
            percentiles=percentiles,
            **common,
        )
    else:
        result = precipitation_seasonality(values, station.dates, **common)
    notices += _period_notices(result)
    return OperationOutput(result, notices)


def meteo_spells(
    *,
    kind: Literal["dry", "wet"] = "dry",
    threshold_mm: float = DEFAULT_SPELL_THRESHOLD_MM,
    dates: Sequence[str] | None = None,
    precipitation_mm: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    precipitation_column: str | None = None,
    precipitation_flag_column: str | None = None,
    year_type: Literal["calendar", "hydrological"] = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Dry or wet spells of a daily precipitation series (``meteo spells``).

    Runs of days with P below ``threshold_mm`` (``dry``) or at least it (``wet``),
    found by the run logic of ``stats threshold-events`` on the calendar of the
    series; per year the longest spell and the spells of at least 10, 15 and 20 days,
    and the distribution of lengths (:func:`hydrolog.statistics.precipitation_spells`,
    M6).

    Parameters
    ----------
    kind : {"dry", "wet"}, optional
        Dry spells (default) or wet spells.
    threshold_mm : float, optional
        The threshold [mm], positive, default 1.
    dates, precipitation_mm, input_file, date_column, precipitation_column, \
precipitation_flag_column
        The daily series, as for :func:`meteo_precipitation`.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year of the summaries.
    first_year, last_year : int, optional
        First and last year of the period, by default those of the record.
    attribution : list of str, optional
        As for :func:`meteo_precipitation`.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.PrecipitationSpells`.

    Raises
    ------
    InvalidParameterError
        If an option is invalid or the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read or lacks a column.
    CalculationError
        If the series or the period has no value.
    """
    cite(attribution)
    check_choice("kind", kind, ("dry", "wet"))
    _year_type(year_type)
    if not (math.isfinite(threshold_mm) and threshold_mm > 0):
        raise InvalidParameterError(
            f"Option 'threshold_mm': must be a positive number, got {threshold_mm!r}",
            details={
                "option": "threshold_mm",
                "reason": "exclusive_minimum",
                "value": str(threshold_mm),
            },
        )
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[_Wanted(_P, precipitation_mm, precipitation_column, True)],
        flag_column=precipitation_flag_column,
    )
    _check_not_negative(station, _P, input_file)
    station = _select(station, year_type, first_year, last_year, [_P.inline])
    result = precipitation_spells(
        station.values[_P.inline],
        station.dates,
        kind=kind,
        threshold_mm=threshold_mm,
        accumulated=station.accumulated,
        year_type=year_type,
    )
    return OperationOutput(
        result, [*_accumulated_notices(station), *_period_notices(result)]
    )


def meteo_spi(
    *,
    scales_months: Sequence[int] = DEFAULT_SCALES_MONTHS,
    dates: Sequence[str] | None = None,
    precipitation_mm: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    precipitation_column: str | None = None,
    precipitation_flag_column: str | None = None,
    year_type: Literal["calendar", "hydrological"] = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """SPI and the relative precipitation of months and years (``meteo spi``).

    The SPI of each month for each scale, from a gamma distribution with the
    probability of zero fitted to the sums of each calendar month in the period
    (McKee et al., 1993; WMO-No. 1090), and the precipitation of each month and year
    in % of its normal with its class (Kaczorowska, 1962, for years)
    (:func:`hydrolog.statistics.standardized_precipitation_index`, M8).

    Parameters
    ----------
    scales_months : sequence of int, optional
        Scales [months], each from 1 to 48, default 1, 3, 6, 12.
    dates, precipitation_mm, input_file, date_column, precipitation_column, \
precipitation_flag_column
        The daily series, as for :func:`meteo_precipitation`.
    year_type : {"calendar", "hydrological"}, optional
        The kind of year of the period and of the annual classes.
    first_year, last_year : int, optional
        First and last year of the period, by default those of the record.
    attribution : list of str, optional
        As for :func:`meteo_precipitation`.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.StandardizedPrecipitation`; the
        notices report months without a fit (``spi_not_fitted``), a normal that
        cannot be computed and a period shorter than 30 years.

    Raises
    ------
    InvalidParameterError
        If an option is invalid or the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read or lacks a column.
    CalculationError
        If the series or the period has no value.
    """
    cite(attribution)
    _year_type(year_type)
    for item in scales_months:
        if isinstance(item, bool) or int(item) != item or not 1 <= item <= 48:
            raise InvalidParameterError(
                f"Option 'scales_months': each must be a whole number from 1 to 48, "
                f"got {item!r}",
                details={
                    "option": "scales_months",
                    "reason": "range",
                    "value": str(item),
                },
            )
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[_Wanted(_P, precipitation_mm, precipitation_column, True)],
        flag_column=precipitation_flag_column,
    )
    _check_not_negative(station, _P, input_file)
    station = _select(station, year_type, first_year, last_year, [_P.inline])
    result = standardized_precipitation_index(
        station.values[_P.inline],
        station.dates,
        scales_months=[int(scale) for scale in scales_months],
        accumulated=station.accumulated,
        year_type=year_type,
    )
    notices = _accumulated_notices(station)
    for scale in result.period.scales:
        missing = [fit.month for fit in scale.fits if fit.alpha is None]
        if missing:
            notices.append(
                notice(
                    "spi_not_fitted", scale_months=scale.scale_months, months=missing
                )
            )
    notices += _normal_notices(
        result.period.normal_mm,
        result.period.normal_years,
        result.first_year,
        result.last_year,
    )
    notices += _period_notices(result)
    return OperationOutput(result, notices)


# --- temperature ----------------------------------------------------------------------


def meteo_temperature(
    *,
    index: Literal["means", "days", "degree_days", "range"],
    dates: Sequence[str] | None = None,
    tmean_c: Sequence[float] | None = None,
    tmax_c: Sequence[float] | None = None,
    tmin_c: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    tmean_column: str | None = None,
    tmax_column: str | None = None,
    tmin_column: str | None = None,
    year_type: Literal["calendar", "hydrological"] = "calendar",
    first_year: int | None = None,
    last_year: int | None = None,
    frost_tmin_c: float = 0.0,
    ice_tmax_c: float = 0.0,
    summer_tmax_c: float = 25.0,
    hot_tmax_c: float = 30.0,
    tropical_tmin_c: float = 20.0,
    growing_base_c: float = 5.0,
    heating_base_c: float = 18.0,
    heating_limit_c: float = 15.0,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Air temperature statistics of a daily series (``meteo temperature``).

    One ``index`` per call (:mod:`hydrolog.statistics.meteo_temperature`, M11):
    ``means`` (monthly and annual means of Tmean, Tmax and Tmin, the normal and the
    anomaly of Tmean, the extremes), ``days`` (frost, ice, summer and hot days and
    tropical nights), ``degree_days`` (growing above ``growing_base_c``, heating by
    Eurostat's rule) and ``range`` (the mean daily range).

    Parameters
    ----------
    index : {"means", "days", "degree_days", "range"}
        The statistic. ``means`` and ``degree_days`` need Tmean, ``range`` Tmax and
        Tmin, ``days`` one of them.
    dates : sequence of str, optional
        ISO dates of the inline values, strictly increasing.
    tmean_c, tmax_c, tmin_c : sequence of float, optional
        Inline daily mean, maximum and minimum temperature [°C].
    input_file : str or os.PathLike, optional
        CSV or JSON file with the daily series (Obserwator's export).
    date_column : str, optional
        Column of the dates, default ``date``.
    tmean_column, tmax_column, tmin_column : str, optional
        Columns of the temperatures [°C], default ``Tmean``, ``Tmax``, ``Tmin``; a
        column the index may use is read when the file has it.
    year_type : {"calendar", "hydrological"}, optional
        Calendar years (default) or hydrological years.
    first_year, last_year : int, optional
        First and last year of the period, by default those of the record.
    frost_tmin_c, ice_tmax_c, summer_tmax_c, hot_tmax_c, tropical_tmin_c : float
        ``days``: thresholds [°C], default 0, 0, 25, 30, 20.
    growing_base_c, heating_base_c, heating_limit_c : float
        ``degree_days``: bases and the heating limit [°C], default 5, 18, 15.
    attribution : list of str, optional
        As for :func:`meteo_precipitation`.

    Returns
    -------
    OperationOutput
        ``result`` is the index's result of :mod:`hydrolog.statistics`; the notices
        report a normal that cannot be computed (``means``) and a period shorter than
        30 years.

    Raises
    ------
    InvalidParameterError
        If an option is invalid, the series options are inconsistent or the index
        lacks its series.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read or lacks a column.
    CalculationError
        If the series or the period has no value.
    """
    cite(attribution)
    check_choice("index", index, TEMPERATURE_INDICES)
    _year_type(year_type)
    needs = {
        "means": ((_TMEAN, True), (_TMAX, False), (_TMIN, False)),
        "days": ((_TMAX, False), (_TMIN, False)),
        "degree_days": ((_TMEAN, True),),
        "range": ((_TMAX, True), (_TMIN, True)),
    }[index]
    inline = {_TMEAN: tmean_c, _TMAX: tmax_c, _TMIN: tmin_c}
    columns = {_TMEAN: tmean_column, _TMAX: tmax_column, _TMIN: tmin_column}
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[
            _Wanted(variable, inline[variable], columns[variable], required)
            for variable, required in needs
        ],
    )
    if not station.values:
        option = "tmax_column" if input_file is not None else "tmax_c"
        raise InvalidParameterError(
            "Index 'days' needs the maximum or the minimum temperature",
            details={"option": option, "reason": "required"},
        )
    station = _select(station, year_type, first_year, last_year, list(station.values))
    series = station.values
    result: Any
    notices: list[Notice] = []
    if index == "means":
        result = temperature_means(
            station.dates,
            tmean_c=series[_TMEAN.inline],
            tmax_c=series.get(_TMAX.inline),
            tmin_c=series.get(_TMIN.inline),
            year_type=year_type,
        )
        notices += _normal_notices(
            result.period.normal_c,
            result.period.normal_years,
            result.first_year,
            result.last_year,
        )
    elif index == "days":
        result = temperature_days(
            station.dates,
            tmax_c=series.get(_TMAX.inline),
            tmin_c=series.get(_TMIN.inline),
            frost_tmin_c=frost_tmin_c,
            ice_tmax_c=ice_tmax_c,
            summer_tmax_c=summer_tmax_c,
            hot_tmax_c=hot_tmax_c,
            tropical_tmin_c=tropical_tmin_c,
            year_type=year_type,
        )
    elif index == "degree_days":
        result = degree_days(
            station.dates,
            tmean_c=series[_TMEAN.inline],
            growing_base_c=growing_base_c,
            heating_base_c=heating_base_c,
            heating_limit_c=heating_limit_c,
            year_type=year_type,
        )
    else:
        result = temperature_range(
            station.dates,
            tmax_c=series[_TMAX.inline],
            tmin_c=series[_TMIN.inline],
            year_type=year_type,
        )
    notices += _period_notices(result)
    return OperationOutput(result, notices)


# --- snow and the hydrothermal coefficient --------------------------------------------


def meteo_snow(
    *,
    dates: Sequence[str] | None = None,
    snow_cover_cm: Sequence[float] | None = None,
    fresh_snow_cm: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    snow_cover_column: str | None = None,
    fresh_snow_column: str | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Snow cover of each winter (``meteo snow``).

    Per winter (a snow season August - July named after the hydrological year it
    ends in): days with snow cover, the largest depth with its day, the first and the
    last day with cover and the sum of fresh snow
    (:func:`hydrolog.statistics.snow_cover`, M10).

    Parameters
    ----------
    dates : sequence of str, optional
        ISO dates of the inline values, strictly increasing.
    snow_cover_cm, fresh_snow_cm : sequence of float, optional
        Inline depth of the snow cover and of fresh snow [cm].
    input_file : str or os.PathLike, optional
        CSV or JSON file with the daily series (Obserwator's export).
    date_column : str, optional
        Column of the dates, default ``date``.
    snow_cover_column, fresh_snow_column : str, optional
        Columns of the depths [cm], default ``snow_cover`` and ``fresh_snow`` (read
        when the file has it).
    first_year, last_year : int, optional
        First and last winter (named after the year it ends in), by default those of
        the record.
    attribution : list of str, optional
        As for :func:`meteo_precipitation`.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.SnowCover`.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read, lacks a column or has a negative
        depth.
    CalculationError
        If the series or the period has no value.
    """
    cite(attribution)
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[
            _Wanted(_SNOW, snow_cover_cm, snow_cover_column, True),
            _Wanted(_FRESH, fresh_snow_cm, fresh_snow_column, False),
        ],
    )
    for variable in (_SNOW, _FRESH):
        _check_not_negative(station, variable, input_file)
    station = _select(station, SNOW_SEASON, first_year, last_year, [_SNOW.inline])
    result = snow_cover(
        station.dates,
        snow_cover_cm=station.values[_SNOW.inline],
        fresh_snow_cm=station.values.get(_FRESH.inline),
    )
    return OperationOutput(result, _period_notices(result))


def meteo_hydrothermal(
    *,
    dates: Sequence[str] | None = None,
    precipitation_mm: Sequence[float] | None = None,
    tmean_c: Sequence[float] | None = None,
    input_file: str | os.PathLike[str] | None = None,
    date_column: str | None = None,
    precipitation_column: str | None = None,
    precipitation_flag_column: str | None = None,
    tmean_column: str | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
    attribution: list[str] | None = None,
) -> OperationOutput:
    """Sielianinov's hydrothermal coefficient (``meteo hydrothermal``).

    k = P / (0.1 Σt) of the months April to September and of the days with a mean
    temperature above 10 °C of each calendar year, with the classes of Skowera and
    Puła (2004) (:func:`hydrolog.statistics.hydrothermal_coefficient`, M14).

    Parameters
    ----------
    dates : sequence of str, optional
        ISO dates of the inline values, strictly increasing.
    precipitation_mm : sequence of float, optional
        Inline daily precipitation [mm].
    tmean_c : sequence of float, optional
        Inline daily mean temperature [°C].
    input_file : str or os.PathLike, optional
        CSV or JSON file with the daily series (Obserwator's export).
    date_column, precipitation_column, precipitation_flag_column : str, optional
        As for :func:`meteo_precipitation`.
    tmean_column : str, optional
        Column of the mean temperature [°C], default ``Tmean``.
    first_year, last_year : int, optional
        First and last calendar year, by default those of the record.
    attribution : list of str, optional
        As for :func:`meteo_precipitation`.

    Returns
    -------
    OperationOutput
        ``result`` is a :class:`~hydrolog.statistics.HydrothermalCoefficient`.

    Raises
    ------
    InvalidParameterError
        If the series options are inconsistent.
    NotFoundError, InputDataError
        If the file does not exist, cannot be read or lacks a column.
    CalculationError
        If the series or the period has no value.
    """
    cite(attribution)
    station = _load(
        dates=dates,
        input_file=input_file,
        date_column=date_column,
        wanted=[
            _Wanted(_P, precipitation_mm, precipitation_column, True),
            _Wanted(_TMEAN, tmean_c, tmean_column, True),
        ],
        flag_column=precipitation_flag_column,
    )
    _check_not_negative(station, _P, input_file)
    station = _select(
        station, "calendar", first_year, last_year, [_P.inline, _TMEAN.inline]
    )
    result = hydrothermal_coefficient(
        station.dates,
        precipitation_mm=station.values[_P.inline],
        tmean_c=station.values[_TMEAN.inline],
        accumulated=station.accumulated,
    )
    return OperationOutput(
        result, [*_accumulated_notices(station), *_period_notices(result)]
    )
