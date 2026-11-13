"""Tests for Mann-Kendall trend test.

Source of the values with ties: Gilbert, R.O. (1987), Statistical Methods for
Environmental Pollution Monitoring, Eq. 16.3, Example 16.2 (pp. 212-213) and the
answer to Exercise 16.1 (p. 224).
"""

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
        """Without ties Var(S) = n(n-1)(2n+5)/18 for n=5."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = mann_kendall_test(series)
        n = 5
        expected_var = n * (n - 1) * (2 * n + 5) / 18
        assert abs(result.var_s - expected_var) < 0.001

    def test_gilbert_exercise_16_1_two_tied_values(self):
        """Two NDs tied below 1.1: S = 12, Var(S) = 43.3, Z = 1.67."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.array([0.25, 1.1, 0.25, 3.0, 1.5, 1.2, 4.0])
        result = mann_kendall_test(series, alpha=0.10, times=np.arange(1.0, 8.0))
        assert result.s_statistic == 12.0
        # [7(6)(19) - 2(1)(9)] / 18 = 43.33 (44.33 without the correction)
        assert result.var_s == pytest.approx(43.3, abs=0.05)
        assert result.z_score == pytest.approx(1.67, abs=0.005)
        assert result.trend_direction == "increasing"  # 1.67 > 1.645 (p < 0.10)

    def test_gilbert_example_16_2_tie_groups(self):
        """n = 22 with 6 values of 20 and 2 of both 23 and 30: Var(S) = 1227.33.

        Example 16.2 only plots its data (Figure 16.2), and the readings of the figure
        do not show the ties 23 x 2 and 30 x 2: this series has Gilbert's tie groups
        and S = +108, the other values are read from the figure.
        """
        from hydrolog.statistics.stationarity import mann_kendall_test

        series = np.array(
            [20, 20, 20, 20, 15, 20, 20, 30, 27.1, 25.9, 22.0]
            + [35.4, 24.3, 28.6, 69.3, 25.3, 23, 33.3, 30, 23, 48.3, 27.8]
        )
        result = mann_kendall_test(series)
        assert result.s_statistic == 108.0
        assert result.var_s == pytest.approx(1227.33, abs=0.005)
        assert result.z_score == pytest.approx(3.1, abs=0.05)  # (108 - 1) / 35.0

    def test_equal_values_have_no_variance_and_no_trend(self):
        """One group of n ties: Var(S) = 0, S = 0, Z = 0."""
        from hydrolog.statistics.stationarity import mann_kendall_test

        result = mann_kendall_test(np.full(6, 2.5))
        assert result.var_s == 0.0
        assert result.z_score == 0.0
        assert result.trend_direction == "none"

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
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.stationarity import mann_kendall_test

        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([]))

    def test_too_short_series_raises(self):
        """Series with < 3 values should raise InvalidParameterError."""
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.statistics.stationarity import mann_kendall_test

        with pytest.raises(InvalidParameterError):
            mann_kendall_test(np.array([1.0, 2.0]))
