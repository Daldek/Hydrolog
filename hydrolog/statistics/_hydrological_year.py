"""Private utilities for Polish hydrological year (Nov 1 – Oct 31).

Polish hydrological year:
- Starts: November 1 of the previous calendar year
- Ends: October 31 of the current calendar year
- Winter half-year: XI–IV (November–April)
- Summer half-year: V–X (May–October)

Reference: IMGW-PIB; https://pl.wikipedia.org/wiki/Rok_hydrologiczny
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def hydrological_year(dates: NDArray) -> NDArray[np.int_]:
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


def hydrological_day_of_year(dates: NDArray) -> NDArray[np.int_]:
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
    return (dates - nov1).astype(int) + 1


def split_half_years(
    values: NDArray[np.float64], dates: NDArray
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
