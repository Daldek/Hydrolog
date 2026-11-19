"""The hydrological year of IMGW-PIB (1 November - 31 October) and its calendar.

The hydrological year runs from 1 November to 31 October and is named after the
calendar year in which it ends; its winter half-year is November to April (XI-IV)
and its summer half-year May to October (V-X) (IMGW-PIB, ``hydrologia_info_ogolne.txt``
of its public hydrological data; Rocznik Hydrologiczny 2022, p. 5; ČHMÚ's
Hydrologická ročenka counts the year alike). These conventions are the Tier B
formulas of :data:`TIER_B` (Nogat's computation standard, CMP-2.2), shown with their
sources in ``docs/FORMULAS.md``.

Annual extremes (:func:`annual_extremes`) use complete hydrological years only: a
year in which a day has no value may have lost its maximum or minimum, and the
annual maxima and minima of frequency analysis are extremes of whole years of
observations (KZGW, 2017, for floods; WMO No. 1029, 2009, for low flows); IMGW-PIB
publishes no characteristic of a period with a break in observations.

Examples
--------
>>> import numpy as np
>>> days = np.array(["2019-11-01", "2020-02-29", "2020-10-31"], dtype="datetime64[D]")
>>> hydrological_year(days).tolist()
[2020, 2020, 2020]
>>> hydrological_day_of_year(days).tolist()
[1, 121, 366]
>>> days_in_hydrological_year(np.array([2020, 2021, 2100])).tolist()
[366, 365, 365]
>>> str(hydrological_year_start(2020))
'2019-11-01'
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any, Final, Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

from hydrolog.nogat_formulas import Constant, FormulaSpec, Source, TierBSpec

_MAX_LISTED_YEARS = 10

FIRST_MONTH: Final = 11
"""November, the first month of the hydrological year."""

SUMMER_FIRST_MONTH: Final = 5
"""May, the first month of the summer half-year (V-X); the winter half-year is XI-IV."""

_IMGW_INFO: Final = Source(
    citation="IMGW-PIB, public hydrological data: hydrologia_info_ogolne.txt (file of "
    "2020-06-23)",
    locator="'rok hydrologiczny 2016 to okres od 1.11.2015 r. do 31.10.2016 r.'; "
    "'półrocze zimowe odpowiada okresowi 1.11.2015-30.04.2016, natomiast półrocze "
    "letnie - okresowi 1.05.2016-31.10.2016'",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/hydrologia_info_ogolne.txt",
)
_IMGW_BREAKS: Final = Source(
    citation="IMGW-PIB, public hydrological data: POLR_publiczne_format.txt (file of "
    "2026-04-29)",
    locator="'Wartość stanu wody/przepływu/temperatury wody równa 99999.999 albo NULL "
    "oznacza przerwy w obserwacjach': no characteristic of a period with a break",
    url="https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/"
    "dane_hydrologiczne/polroczne_i_roczne/POLR_publiczne_format.txt",
)
_STATION_ANALYSES: Final = Source(
    citation="Hydrolog, ADR-0029: station analyses for Obserwator",
    locator="docs/decisions/0029-station-analyses-for-obserwator.md: a day whose date "
    "is absent or whose value is empty has no value",
)
_FIRST_MONTH: Final = Constant(
    name="first_month",
    value=Fraction(FIRST_MONTH),
    unit="month",
    source=_IMGW_INFO,
)

SPECS: Final[tuple[FormulaSpec, ...]] = ()
"""No Tier A formula: the calendar is Tier B (:data:`TIER_B`)."""

TIER_B: Final[tuple[TierBSpec, ...]] = (
    TierBSpec(
        name="hydrological_year",
        function="hydrolog.statistics._hydrological_year.hydrological_year",
        definition="The hydrological year of a date: its calendar year, one more for "
        "November and December.",
        convention="IMGW-PIB's year 1 November - 31 October, named after the calendar "
        "year in which it ends (2016 = 1.11.2015 - 31.10.2016); ČHMÚ's the same "
        "(Hydrologická ročenka České republiky 2010, introduction).",
        source=_IMGW_INFO,
        constants=(_FIRST_MONTH,),
    ),
    TierBSpec(
        name="hydrological_day_of_year",
        function="hydrolog.statistics._hydrological_year.hydrological_day_of_year",
        definition="The day of a date in its hydrological year: the days since 1 "
        "November, plus one.",
        convention="1 November is day 1 and 29 February day 121; from 1 March a leap "
        "year's days are one higher than a common year's (1 March is day 122 or 121, "
        "31 October day 366 or 365): a day number names no calendar date.",
        source=_IMGW_INFO,
        constants=(_FIRST_MONTH,),
    ),
    TierBSpec(
        name="days_in_hydrological_year",
        function="hydrolog.statistics._hydrological_year.days_in_hydrological_year",
        definition="The calendar days of a hydrological year: 366 when its name is a "
        "leap year, else 365.",
        convention="A year holds 29 February of the calendar year it is named after; "
        "leap years of the Gregorian calendar, a multiple of 4 but not of 100 unless "
        "of 400 (2000 leap, 2100 common).",
        source=_IMGW_INFO,
    ),
    TierBSpec(
        name="hydrological_year_start",
        function="hydrolog.statistics._hydrological_year.hydrological_year_start",
        definition="The first day of a hydrological year: 1 November of the calendar "
        "year before its name.",
        convention="The year named after the calendar year in which it ends.",
        source=_IMGW_INFO,
        constants=(_FIRST_MONTH,),
    ),
    TierBSpec(
        name="daily_calendar",
        function="hydrolog.statistics._hydrological_year.on_daily_calendar",
        definition="Every day from the first to the last date of a series, with its "
        "value.",
        convention="A day whose date is absent or whose value is NaN has no value "
        "(NaN); no value is filled in.",
        source=_STATION_ANALYSES,
    ),
    TierBSpec(
        name="complete_year_extremes",
        function="hydrolog.statistics._hydrological_year.annual_extremes",
        definition="The maximum or the minimum of each complete hydrological year, "
        "one with a value on each of its 365 or 366 days.",
        convention="A year with a day without a value is skipped and reported (its "
        "extreme may fall on that day); a date given twice counts once.",
        source=_IMGW_BREAKS,
    ),
)
"""The calendar of the hydrological year (CMP-2.2)."""


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
    # November and December belong to the next calendar year's hydrological year
    return np.where(months >= FIRST_MONTH, years + 1, years)


def hydrological_day_of_year(dates: NDArray[np.datetime64]) -> NDArray[np.int_]:
    """Compute day-of-year within the hydrological year.

    Parameters
    ----------
    dates : NDArray
        Array of dates (dtype datetime64[D]).

    Returns
    -------
    NDArray[np.int_]
        Day number (1 = 1 November, up to 365 or 366); from 1 March a leap year's
        days are one higher than a common year's (29 February is day 121).
    """
    hydro_years = hydrological_year(dates)
    # Start of each hydrological year is Nov 1 of the previous calendar year.
    # Construct Nov 1 by advancing 10 months from Jan 1 of (hydro_year - 1).
    prev_years = hydro_years - 1
    nov1 = prev_years.astype("U4").astype("datetime64[Y]") + np.timedelta64(
        FIRST_MONTH - 1, "M"
    )
    days: NDArray[np.int64] = (dates - nov1).astype(np.int64) + 1
    return days


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


def hydrological_year_start(year: int) -> np.datetime64:
    """Return the first day of a hydrological year.

    Parameters
    ----------
    year : int
        Hydrological year, named after the calendar year in which it ends.

    Returns
    -------
    numpy.datetime64
        1 November of the calendar year before ``year`` (``datetime64[D]``).
    """
    return np.datetime64(f"{year - 1:04d}-{FIRST_MONTH:02d}-01", "D")


def on_daily_calendar(
    values: NDArray[np.float64], dates: NDArray[np.datetime64]
) -> tuple[NDArray[np.datetime64], NDArray[np.float64]]:
    """Lay a dated series on the calendar of its days.

    Parameters
    ----------
    values : NDArray[np.float64]
        Values of the series; ``NaN`` marks a missing value.
    dates : NDArray
        Their dates, strictly increasing (days may be absent).

    Returns
    -------
    tuple of NDArray
        Every day from the first to the last date (``datetime64[D]``) and its value,
        ``NaN`` on a day whose date is absent or whose value is missing.
    """
    days = np.asarray(dates).astype("datetime64[D]")
    first = days[0]
    count = int((days[-1] - first).astype(np.int64)) + 1
    daily = np.full(count, np.nan)
    daily[(days - first).astype(np.int64)] = np.asarray(values, dtype=np.float64)
    calendar: NDArray[np.datetime64] = first + np.arange(count)
    return calendar, daily


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


def incomplete_years_details(extremes: AnnualExtremes) -> dict[str, Any]:
    """Return the details of a warning about the years that were skipped.

    Parameters
    ----------
    extremes : AnnualExtremes
        Result of :func:`annual_extremes` with at least one incomplete year.

    Returns
    -------
    dict
        The details of :class:`~hydrolog._warnings.IncompleteYears` (notice code
        ``incomplete_years``): ``skipped`` and ``total`` years, the skipped ``years``
        and, in their order, ``days_with_data`` and ``days_in_year``; for example
        ``{"skipped": 2, "total": 31, "years": [1991, 2021], "days_with_data":
        [304, 61], "days_in_year": [365, 365]}``.
    """
    skipped = extremes.incomplete
    return {
        "skipped": len(skipped),
        "total": len(extremes.years) + len(skipped),
        "years": [item.year for item in skipped],
        "days_with_data": [item.days_with_data for item in skipped],
        "days_in_year": [item.days_in_year for item in skipped],
    }
