"""Tests for rating curve and water level frequency."""

import numpy as np
import pytest


class TestRatingCurve:

    @pytest.fixture
    def synthetic_rating_data(self):
        """Q = 2.5 * (H - 50)^1.8 with noise."""
        rng = np.random.default_rng(42)
        h = np.linspace(60, 200, 50)
        q = 2.5 * (h - 50) ** 1.8 + rng.normal(0, 5, size=50)
        q = np.maximum(q, 0.1)
        return h, q

    def test_fit_recovers_parameters(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        rc = RatingCurve(h, q)
        result = rc.fit(h0_initial=50.0)
        assert abs(result.a - 2.5) < 1.0
        assert abs(result.b - 1.8) < 0.3
        assert abs(result.h0 - 50.0) < 10.0
        assert result.r_squared > 0.95

    def test_predict_returns_correct_shape(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        rc = RatingCurve(h, q)
        rc.fit(h0_initial=50.0)
        predicted = rc.predict(np.array([100.0, 150.0]))
        assert len(predicted) == 2
        assert np.all(predicted > 0)

    def test_outlier_removal(self, synthetic_rating_data):
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        h, q = synthetic_rating_data
        q_with_outlier = q.copy()
        q_with_outlier[25] = q[25] * 10
        rc = RatingCurve(h, q_with_outlier)
        result = rc.fit(h0_initial=50.0, remove_outliers=True, outlier_std=2.0)
        assert result.n_outliers_removed >= 1

    def test_mismatched_lengths_raises(self):
        from hydrolog.hydrometrics.rating_curve import RatingCurve
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            RatingCurve(np.array([1.0, 2.0]), np.array([1.0]))

    def test_too_few_points_raises(self):
        from hydrolog.hydrometrics.rating_curve import RatingCurve
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            RatingCurve(np.array([1.0, 2.0]), np.array([1.0, 2.0]))


class TestWaterLevelFrequency:

    def test_frequency_distribution(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        rng = np.random.default_rng(42)
        levels = rng.uniform(100, 300, size=1000)
        wlf = WaterLevelFrequency(levels, bin_width=20.0)
        result = wlf.frequency_distribution()
        assert abs(result.frequency_pct.sum() - 100.0) < 0.1
        assert result.cumulative_frequency_pct[-1] == pytest.approx(100.0, abs=0.1)

    def test_rybczynski_zones(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        rng = np.random.default_rng(42)
        levels = rng.uniform(100, 300, size=1000)
        wlf = WaterLevelFrequency(levels, bin_width=10.0)
        zones = wlf.rybczynski_zones()
        assert zones.ntw_upper < zones.stw_upper
        assert zones.ntw_range[1] == zones.stw_range[0]
        assert zones.stw_range[1] == zones.wtw_range[0]

    def test_empty_data_raises(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            WaterLevelFrequency(np.array([]))

    def test_invalid_bin_width_raises(self):
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency
        from hydrolog.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            WaterLevelFrequency(np.array([1.0, 2.0]), bin_width=0.0)
