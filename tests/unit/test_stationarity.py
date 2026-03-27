"""Tests for Mann-Kendall trend test."""

import numpy as np
import pytest


class TestMannKendall:
    """Tests for mann_kendall_test function."""

    def test_increasing_trend_detected(self):
        """Clear increasing trend should be detected."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        series = np.arange(1.0, 51.0)
        result = mann_kendall_test(series)
        assert result.trend_detected is True
        assert result.trend_direction == "increasing"
        assert result.s_statistic > 0

    def test_decreasing_trend_detected(self):
        """Clear decreasing trend should be detected."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        series = np.arange(50.0, 0.0, -1.0)
        result = mann_kendall_test(series)
        assert result.trend_detected is True
        assert result.trend_direction == "decreasing"
        assert result.s_statistic < 0

    def test_no_trend_in_random_data(self):
        """Random stationary data should (usually) not show trend."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        rng = np.random.default_rng(42)
        series = rng.normal(100, 10, size=50)
        result = mann_kendall_test(series)
        assert result.trend_direction == "none"
        assert result.p_value > 0.05

    def test_variance_formula(self):
        """Var(S) = n(n-1)(2n+5)/18 for n=5."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = mann_kendall_test(series)
        n = 5
        expected_var = n * (n - 1) * (2 * n + 5) / 18
        assert abs(result.var_s - expected_var) < 0.001

    def test_s_statistic_for_known_sequence(self):
        """S = number of concordant - discordant pairs."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        series = np.array([1.0, 2.0, 3.0])
        result = mann_kendall_test(series)
        assert result.s_statistic == 3.0

    def test_significance_level_stored(self):
        """Result stores the alpha used."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        series = np.arange(1.0, 20.0)
        result = mann_kendall_test(series, alpha=0.01)
        assert result.significance_level == 0.01

    def test_empty_series_raises(self):
        """Empty series should raise InvalidParameterError."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        from hydrolog.exceptions import InvalidParameterError
        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([]))

    def test_too_short_series_raises(self):
        """Series with < 3 values should raise InvalidParameterError."""
        from hydrolog.statistics.stationarity import mann_kendall_test
        from hydrolog.exceptions import InvalidParameterError
        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([1.0, 2.0]))
