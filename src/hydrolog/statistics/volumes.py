"""Runoff volumes of a daily discharge series.

The volume of a day is its mean discharge times the 86,400 seconds of the day; the
volume of a month or a hydrological year (1 November - 31 October) is the sum over its
days with a value. A year or a month is *complete* when every one of its days has a
value; the mean volumes take the complete ones only. The cumulative volume of a year
adds the days in order (a day without a value adds nothing).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.statistics._hydrological_year import (
    hydrological_year,
    hydrological_year_start,
)

__all__ = [
    "DAY_SECONDS",
    "MonthVolume",
    "RunoffVolumes",
    "YearVolume",
    "runoff_volumes",
]

DAY_SECONDS = 86_400.0
"""Seconds of a day: a discharge of 1 m³/s for a day is 86,400 m³."""

# Calendar months in the order of the hydrological year: November first.
_HYDROLOGICAL_MONTHS = (11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
_COMMON_YEAR_DAYS = 365


@dataclass
class MonthVolume(JsonResultMixin):
    """Runoff volume of one month of a hydrological year.

    Attributes
    ----------
    month : int
        Calendar month (11 = November).
    volume_m3 : float or None
        Sum of the daily volumes of its days with a value [m³]; ``None`` when no day
        has one.
    days_with_data : int
        Days of the month with a value.
    days : int
        Calendar days of the month.
    """

    month: int
    volume_m3: float | None
    days_with_data: int
    days: int


@dataclass
class YearVolume(JsonResultMixin):
    """Runoff volume of one hydrological year and its months.

    Attributes
    ----------
    year : int
        Hydrological year (named after the calendar year in which it ends).
    volume_m3 : float
        Sum of the daily volumes of its days with a value [m³].
    days_with_data : int
        Days of the year with a value.
    days : int
        Calendar days of the year (365 or 366).
    complete : bool
        Every day of the year has a value.
    months : list of MonthVolume
        The months from November to October.
    """

    year: int
    volume_m3: float
    days_with_data: int
    days: int
    complete: bool
    months: list[MonthVolume]


@dataclass
class RunoffVolumes(JsonResultMixin):
    """Annual and monthly runoff volumes and the cumulative volume of a year.

    Attributes
    ----------
    first_year, last_year : int
        First and last hydrological year with a value.
    period_years : int
        Hydrological years with a value.
    years : list of YearVolume
        Every hydrological year with a value, in order.
    n_complete_years : int
        Complete years among them.
    mean_annual_volume_m3 : float or None
        Mean volume of the complete years [m³]; ``None`` without one.
    monthly_mean_volume_m3 : list of float or None
        Mean volume of each month (November to October) over its complete months
        [m³]; ``None`` for a month that is never complete.
    cumulative_year : int
        The year of ``cumulative_volume_m3``.
    cumulative_volume_m3 : list of float
        Cumulative volume of ``cumulative_year`` at the end of each of its days [m³].
    mean_cumulative_volume_m3 : list of float or None
        Mean of the cumulative volumes of the complete years at the end of each of
        their first 365 days [m³]; ``None`` without a complete year.
    """

    first_year: int
    last_year: int
    period_years: int
    years: list[YearVolume]
    n_complete_years: int
    mean_annual_volume_m3: float | None
    monthly_mean_volume_m3: list[float | None]
    cumulative_year: int
    cumulative_volume_m3: list[float]
    mean_cumulative_volume_m3: list[float] | None = field(default=None)


def runoff_volumes(
    discharge: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    *,
    cumulative_year: int | None = None,
) -> RunoffVolumes:
    """Compute the runoff volumes of a daily discharge series.

    Parameters
    ----------
    discharge : NDArray[np.float64]
        Daily mean discharge [m³/s]; ``NaN`` marks a day without a value.
    dates : NDArray[np.datetime64]
        Their dates, strictly increasing (days may be absent).
    cumulative_year : int, optional
        Hydrological year of the cumulative volume; by default the last complete
        year, or the last year when none is complete.

    Returns
    -------
    RunoffVolumes
        The volumes of the years and months, their means and the cumulative volume.

    Raises
    ------
    InvalidParameterError
        If the arrays are empty or differ in length, no day has a value, or
        ``cumulative_year`` has no value.
    """
    flows = np.asarray(discharge, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    if flows.size == 0 or flows.size != days.size:
        raise InvalidParameterError(
            "discharge and dates must be non-empty and of the same length"
        )
    present = np.isfinite(flows)
    if not present.any():
        raise InvalidParameterError("the series has no value")
    year_of_day = hydrological_year(days)
    rows: list[YearVolume] = []
    curves: dict[int, NDArray[np.float64]] = {}
    month_sums: list[list[float]] = [[] for _ in _HYDROLOGICAL_MONTHS]
    for year in np.unique(year_of_day[present]).tolist():
        start = hydrological_year_start(int(year))
        end = hydrological_year_start(int(year) + 1)
        n_days = int((end - start).astype(np.int64))
        daily = np.full(n_days, np.nan)
        mine = year_of_day == year
        daily[(days[mine] - start).astype(np.int64)] = flows[mine]
        volumes = daily * DAY_SECONDS
        good = np.isfinite(volumes)
        calendar = start + np.arange(n_days)
        calendar_months = calendar.astype("datetime64[M]").astype(np.int64) % 12 + 1
        months: list[MonthVolume] = []
        for slot, month in enumerate(_HYDROLOGICAL_MONTHS):
            part = calendar_months == month
            with_data = int(good[part].sum())
            total = int(part.sum())
            volume = float(volumes[part][good[part]].sum()) if with_data else None
            months.append(MonthVolume(month, volume, with_data, total))
            if with_data == total and volume is not None:
                month_sums[slot].append(volume)
        complete = bool(good.all())
        rows.append(
            YearVolume(
                year=int(year),
                volume_m3=float(volumes[good].sum()),
                days_with_data=int(good.sum()),
                days=n_days,
                complete=complete,
                months=months,
            )
        )
        curves[int(year)] = np.cumsum(np.where(good, volumes, 0.0))
    complete_years = [row.year for row in rows if row.complete]
    if cumulative_year is None:
        cumulative_year = complete_years[-1] if complete_years else rows[-1].year
    elif cumulative_year not in curves:
        raise InvalidParameterError(
            f"cumulative_year {cumulative_year} has no value in the series"
        )
    mean_curve = None
    if complete_years:
        stacked = np.array(
            [curves[year][:_COMMON_YEAR_DAYS] for year in complete_years]
        )
        mean_curve = [float(item) for item in stacked.mean(axis=0)]
    annual = [row.volume_m3 for row in rows if row.complete]
    return RunoffVolumes(
        first_year=rows[0].year,
        last_year=rows[-1].year,
        period_years=len(rows),
        years=rows,
        n_complete_years=len(complete_years),
        mean_annual_volume_m3=float(np.mean(annual)) if annual else None,
        monthly_mean_volume_m3=[
            float(np.mean(sums)) if sums else None for sums in month_sums
        ],
        cumulative_year=int(cumulative_year),
        cumulative_volume_m3=[float(item) for item in curves[int(cumulative_year)]],
        mean_cumulative_volume_m3=mean_curve,
    )
