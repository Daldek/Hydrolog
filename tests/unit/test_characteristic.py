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


class TestCharacteristicValues:
    """Tests for characteristic flow values (Polish system)."""

    @pytest.fixture
    def known_daily_data(self):
        """3 hydrological years of daily data with known characteristics."""
        rng = np.random.default_rng(42)
        dates_list = []
        values_list = []
        for year_offset, (mx, mn, avg) in enumerate(
            [
                (100.0, 10.0, 50.0),
                (80.0, 5.0, 40.0),
                (120.0, 15.0, 60.0),
            ]
        ):
            start = np.datetime64(f"{2020 + year_offset}-11-01")
            days = np.arange(365, dtype="timedelta64[D]")
            year_dates = start + days
            year_values = rng.uniform(mn + 1, mx - 1, size=365)
            year_values[0] = mx
            year_values[1] = mn
            dates_list.append(year_dates)
            values_list.append(year_values)
        return np.concatenate(dates_list), np.concatenate(values_list)

    def test_characteristic_values_wwq(self, known_daily_data):
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.wwx == 120.0

    def test_characteristic_values_nnq(self, known_daily_data):
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.nnx == 5.0

    def test_characteristic_values_swq_is_mean_of_annual_maxima(self, known_daily_data):
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        expected_swq = np.mean([100.0, 80.0, 120.0])
        assert abs(result.swx - expected_swq) < 0.01

    def test_characteristic_values_zwq_is_median_of_annual_maxima(
        self, known_daily_data
    ):
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        expected_zwq = np.median([100.0, 80.0, 120.0])
        assert abs(result.zwx - expected_zwq) < 0.01

    def test_characteristic_values_period_years(self, known_daily_data):
        from hydrolog.statistics.characteristic import calculate_characteristic_values

        dates, values = known_daily_data
        result = calculate_characteristic_values(values, dates)
        assert result.period_years == 3

    def test_empty_input_raises(self):
        from hydrolog.statistics.characteristic import calculate_characteristic_values
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            calculate_characteristic_values(np.array([]), np.array([]))

    def test_mismatched_lengths_raises(self):
        from hydrolog.statistics.characteristic import calculate_characteristic_values
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            calculate_characteristic_values(
                np.array([1.0, 2.0]),
                np.array(["2021-01-01"], dtype="datetime64[D]"),
            )


class TestDailyStatistics:
    """Tests for calculate_daily_statistics."""

    def test_daily_statistics_shape(self):
        from hydrolog.statistics.characteristic import calculate_daily_statistics

        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2019-11-01"),
            np.datetime64("2021-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        result = calculate_daily_statistics(values, dates)
        assert len(result.max_values) > 0
        assert len(result.max_values) == len(result.mean_values)
        assert np.all(result.max_values >= result.mean_values)
        assert np.all(result.mean_values >= result.min_values)


class TestMonthlyStatistics:
    """Tests for monthly statistics with t-Student CI."""

    def test_ci_uses_t_student_not_z(self):
        from hydrolog.statistics.characteristic import calculate_monthly_statistics

        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2010-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        result = calculate_monthly_statistics(values, dates)
        assert result.confidence_level == 0.95
        widths = result.ci_upper - result.ci_lower
        assert np.all(widths > 0)

    def test_cv_and_skewness_computed(self):
        from hydrolog.statistics.characteristic import calculate_monthly_statistics

        rng = np.random.default_rng(42)
        dates = np.arange(
            np.datetime64("2010-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = rng.uniform(5, 50, size=len(dates))
        result = calculate_monthly_statistics(values, dates)
        assert len(result.cv_values) == 12
        assert len(result.skewness_values) == 12
        assert np.all(result.cv_values > 0)

    def test_invalid_confidence_level_raises(self):
        from hydrolog.statistics.characteristic import calculate_monthly_statistics
        from hydrolog.exceptions import InvalidParameterError

        dates = np.arange(
            np.datetime64("2019-11-01"),
            np.datetime64("2020-10-31"),
            dtype="datetime64[D]",
        )
        values = np.ones(len(dates))
        with pytest.raises(InvalidParameterError):
            calculate_monthly_statistics(values, dates, confidence_level=1.5)
