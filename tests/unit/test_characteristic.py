"""Tests for hydrological year utilities and characteristic values."""

import numpy as np
import pytest
from numpy.typing import NDArray


class TestHydrologicalYear:
    """Tests for _hydrological_year module."""

    def test_hydrological_year_november_december_next_year(self):
        """Nov-Dec dates belong to the next calendar year's hydro year."""
        from hydrolog.statistics._hydrological_year import hydrological_year

        dates = np.array(
            ["2020-11-01", "2020-12-15", "2021-01-10", "2021-10-31"],
            dtype="datetime64[D]",
        )
        result = hydrological_year(dates)
        np.testing.assert_array_equal(result, [2021, 2021, 2021, 2021])

    def test_hydrological_year_boundary_october_vs_november(self):
        """Oct 31 is last day of current year; Nov 1 is first day of next."""
        from hydrolog.statistics._hydrological_year import hydrological_year

        dates = np.array(
            ["2020-10-31", "2020-11-01"],
            dtype="datetime64[D]",
        )
        result = hydrological_year(dates)
        np.testing.assert_array_equal(result, [2020, 2021])

    def test_hydrological_day_of_year_nov1_is_day1(self):
        """November 1 is day 1 of the hydrological year."""
        from hydrolog.statistics._hydrological_year import hydrological_day_of_year

        dates = np.array(["2020-11-01"], dtype="datetime64[D]")
        result = hydrological_day_of_year(dates)
        assert result[0] == 1

    def test_hydrological_day_of_year_oct31_is_last(self):
        """October 31 is day 366 (leap) or 365 (non-leap)."""
        from hydrolog.statistics._hydrological_year import hydrological_day_of_year

        dates = np.array(["2021-10-31"], dtype="datetime64[D]")
        result = hydrological_day_of_year(dates)
        assert result[0] in (365, 366)

    def test_split_half_years_winter_summer(self):
        """Winter = Nov-Apr, Summer = May-Oct."""
        from hydrolog.statistics._hydrological_year import split_half_years

        dates = np.array(
            ["2021-01-15", "2021-05-15", "2021-11-15", "2021-07-20"],
            dtype="datetime64[D]",
        )
        values = np.array([10.0, 20.0, 30.0, 40.0])
        winter, summer = split_half_years(values, dates)
        np.testing.assert_array_equal(winter, [10.0, 30.0])  # Jan, Nov
        np.testing.assert_array_equal(summer, [20.0, 40.0])  # May, Jul
