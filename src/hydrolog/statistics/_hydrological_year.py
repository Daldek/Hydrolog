"""Private utilities for Polish hydrological year (Nov 1 – Oct 31).

Polish hydrological year:
- Starts: November 1 of the previous calendar year
- Ends: October 31 of the current calendar year
- Winter half-year: XI–IV (November–April)
- Summer half-year: V–X (May–October)

Annual extremes (:func:`annual_extremes`) use complete hydrological years only: a
year in which a day has no value may have lost its maximum or minimum, and the
annual maxima and minima of frequency analysis are extremes of whole years of
observations (KZGW, 2017, for floods; WMO No. 1029, 2009, for low flows).

Reference: IMGW-PIB; https://pl.wikipedia.org/wiki/Rok_hydrologiczny
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

_MAX_LISTED_YEARS = 10


def hydrological_year(dates: NDArray[np.datetime64]) -> NDArray[np.int_]:
    """Assign hydrological year to each date.

    Parameters
    ----------
    dates : NDArray
        Array of dates (dtype datetime64[D] or similar).

    Returns
    -------
    NDArray[np.int_]
        Hydrological year for each date. Months XI–XII belong to the
        next calendar year's hydrological year.
    """
    months = dates.astype("datetime64[M]").astype(int) % 12 + 1
    years = dates.astype("datetime64[Y]").astype(int) + 1970
    # Nov (11) and Dec (12) → next year's hydro year
    return np.where(months >= 11, years + 1, years)


def hydrological_day_of_year(dates: NDArray[np.datetime64]) -> NDArray[np.int_]:
    """Compute day-of-year within the hydrological year.

    Parameters
    ----------
    dates : NDArray
        Array of dates (dtype datetime64[D]).

    Returns
    -------
    NDArray[np.int_]
        Day number (1 = Nov 1, up to 365 or 366).
    """
    hydro_years = hydrological_year(dates)
    # Start of each hydrological year is Nov 1 of the previous calendar year.
    # Construct Nov 1 by advancing 10 months from Jan 1 of (hydro_year - 1).
    prev_years = hydro_years - 1
    nov1 = prev_years.astype("U4").astype("datetime64[Y]") + np.timedelta64(10, "M")
    days: NDArray[np.int64] = (dates - nov1).astype(np.int64) + 1
    return days


def split_half_years(
    values: NDArray[np.float64], dates: NDArray[np.datetime64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Split values into winter and summer half-years.

    Parameters
    ----------
    values : NDArray[np.float64]
        Data values corresponding to dates.
    dates : NDArray
        Array of dates (dtype datetime64[D]).

    Returns
    -------
    tuple[NDArray[np.float64], NDArray[np.float64]]
        (winter_values, summer_values) where:
        - Winter: months 11, 12, 1, 2, 3, 4
        - Summer: months 5, 6, 7, 8, 9, 10
    """
    months = dates.astype("datetime64[M]").astype(int) % 12 + 1
    winter_mask = (months >= 11) | (months <= 4)
    return values[winter_mask], values[~winter_mask]


def days_in_hydrological_year(years: NDArray[np.int_]) -> NDArray[np.int_]:
    """Count calendar days of hydrological years.

    Parameters
    ----------
    years : NDArray[np.int_]
        Hydrological years, named after the calendar year in which they end.

    Returns
    -------
    NDArray[np.int_]
        365, or 366 for a hydrological year that contains 29 February, that is
        when its name is a leap year (1 November 2019 - 31 October 2020 holds
        29 February 2020 and has 366 days).
    """
    names: NDArray[np.int_] = np.asarray(years, dtype=np.int_)
    leap = (names % 4 == 0) & ((names % 100 != 0) | (names % 400 == 0))
    days: NDArray[np.int_] = (365 + leap).astype(np.int_)
    return days


class IncompleteYear(NamedTuple):
    """A hydrological year in which some days have no value.

    Attributes
    ----------
    year : int
        Hydrological year, named after the calendar year in which it ends.
    days_with_data : int
        Days of the year that have a value (not ``NaN``).
    days_in_year : int
        Calendar days of the year: 365, or 366 when it contains 29 February.
    """

    year: int
    days_with_data: int
    days_in_year: int


class AnnualExtremes(NamedTuple):
    """Annual maxima or minima of the complete hydrological years of a series.

    Attributes
    ----------
    years : NDArray[np.int_]
        Complete hydrological years, in ascending order.
    values : NDArray[np.float64]
        Extreme (maximum or minimum) of each year of ``years``.
    incomplete : tuple of IncompleteYear
        Hydrological years of the series that were skipped, in ascending order.
    """

    years: NDArray[np.int_]
    values: NDArray[np.float64]
    incomplete: tuple[IncompleteYear, ...]

    @property
    def incomplete_years(self) -> list[int]:
        """List of int: the skipped hydrological years, in ascending order."""
        return [item.year for item in self.incomplete]


def annual_extremes(
    values: NDArray[np.float64],
    dates: NDArray[np.datetime64],
    kind: Literal["max", "min"],
) -> AnnualExtremes:
    """Annual maximum or minimum of every complete hydrological year of a series.

    A hydrological year (1 November - 31 October) is *complete* when the series has
    a value for every day of it: 365 days, or 366 when it contains 29 February. A
    day without a value (its date is absent or its value is ``NaN``) makes the year
    incomplete, and an incomplete year is skipped. The extreme of a year with
    missing days may be milder than the true one (a lower maximum, a higher
    minimum), and the annual maxima and minima of a frequency analysis are extremes
    of whole years of observations (KZGW, 2017; WMO No. 1029, 2009). A calendar-year
    export (1 January - 31 December) therefore loses its first and last hydrological
    year: the first lacks November and December, the last holds only those two
    months.

    Parameters
    ----------
    values : NDArray[np.float64]
        Daily values; ``NaN`` marks a missing day.
    dates : NDArray
        Dates of the values (``datetime64``), one per value.
    kind : {"max", "min"}
        Take the annual maximum or the annual minimum.

    Returns
    -------
    AnnualExtremes
        The complete years with their extremes and the years that were skipped
        (no complete year gives empty ``years`` and ``values``).
    """
    flows = np.asarray(values, dtype=np.float64)
    days = np.asarray(dates).astype("datetime64[D]")
    day_years = hydrological_year(days)
    labels = np.unique(day_years)  # every hydrological year the dates touch
    has_value = ~np.isnan(flows)

    # Distinct days with a value, per year: duplicated dates count once.
    valued_days = np.unique(days[has_value])
    with_data = np.bincount(
        np.searchsorted(labels, hydrological_year(valued_days)), minlength=len(labels)
    )
    expected = days_in_hydrological_year(labels)
    complete = with_data == expected

    # Extreme of every complete year: sort the values of those years by year and
    # reduce each run (one pass, however many years the series spans).
    reduce = np.maximum if kind == "max" else np.minimum
    used = has_value & np.isin(day_years, labels[complete])
    order = np.argsort(day_years[used], kind="stable")
    used_years = day_years[used][order]
    first = np.flatnonzero(np.diff(used_years, prepend=used_years[:1] - 1))
    extremes = reduce.reduceat(flows[used][order], first)
    skipped = tuple(
        IncompleteYear(int(year), int(present), int(total))
        for year, present, total in zip(
            labels[~complete], with_data[~complete], expected[~complete], strict=False
        )
    )
    return AnnualExtremes(labels[complete], extremes, skipped)


def describe_incomplete_years(extremes: AnnualExtremes) -> str:
    """List the hydrological years skipped by :func:`annual_extremes`.

    Parameters
    ----------
    extremes : AnnualExtremes
        Result of :func:`annual_extremes`.

    Returns
    -------
    str
        Each skipped year with its days that have a value, for example
        ``"1991 (304 of 365 days), 2021 (61 of 365 days)"``; at most 10 years are
        listed, the rest is counted (``", and 3 more"``).
    """
    skipped: Sequence[IncompleteYear] = extremes.incomplete
    listed = ", ".join(
        f"{item.year} ({item.days_with_data} of {item.days_in_year} days)"
        for item in skipped[:_MAX_LISTED_YEARS]
    )
    hidden = len(skipped) - _MAX_LISTED_YEARS
    if hidden > 0:
        listed += f", and {hidden} more"
    return listed


def incomplete_years_message(extremes: AnnualExtremes) -> str:
    """One-line message about the hydrological years skipped by ``annual_extremes``.

    Parameters
    ----------
    extremes : AnnualExtremes
        Result of :func:`annual_extremes` with at least one incomplete year.

    Returns
    -------
    str
        For example ``"Skipped 2 of 31 hydrological year(s) that are incomplete
        (a value is needed for every day of the year): 1991 (304 of 365 days), 2021
        (61 of 365 days)"``.
    """
    total = len(extremes.years) + len(extremes.incomplete)
    return (
        f"Skipped {len(extremes.incomplete)} of {total} hydrological year(s) that "
        f"are incomplete (a value is needed for every day of the year): "
        f"{describe_incomplete_years(extremes)}"
    )
