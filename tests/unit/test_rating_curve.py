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


class TestRatingCurveErrors:
    """Failure modes of ``RatingCurve`` are Hydrolog errors of the right kind."""

    @pytest.fixture
    def curve_data(self):
        h = np.linspace(60.0, 200.0, 20)
        return h, 2.5 * (h - 50.0) ** 1.8

    @pytest.mark.parametrize(
        "h0_initial", [60.0, 70.0, float("nan"), float("inf"), -float("inf")]
    )
    def test_initial_zero_level_must_be_finite_and_below_every_level(
        self, curve_data, h0_initial
    ):
        """Was a bare ``ValueError`` from SciPy (``x0`` is infeasible)."""
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        with pytest.raises(InvalidParameterError) as caught:
            RatingCurve(*curve_data).fit(h0_initial=h0_initial)
        assert caught.value.code == "validation_error"
        assert caught.value.details["option"] == "h0_initial"
        assert caught.value.details["maximum"] == 60.0
        assert "lower than every water level" in caught.value.hint

    def test_initial_zero_level_error_is_still_a_value_error(self, curve_data):
        from hydrolog.hydrometrics import RatingCurve

        with pytest.raises(ValueError):
            RatingCurve(*curve_data).fit(h0_initial=70.0)

    def test_initial_zero_level_just_below_the_lowest_level_is_accepted(
        self, curve_data
    ):
        """The optimiser keeps H0 1e-6 below the lowest level; a start inside that
        margin is moved to the bound instead of failing."""
        from hydrolog.hydrometrics import RatingCurve

        result = RatingCurve(*curve_data).fit(h0_initial=60.0 - 1e-7)
        assert result.h0 == pytest.approx(50.0, abs=0.5)

    @pytest.mark.parametrize("bad", [float("nan"), float("inf")])
    def test_non_finite_measurements_are_rejected(self, bad):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        with pytest.raises(InvalidParameterError, match="finite"):
            RatingCurve(np.array([60.0, 80.0, bad]), np.array([1.0, 2.0, 3.0]))
        with pytest.raises(InvalidParameterError, match="finite"):
            RatingCurve(np.array([60.0, 80.0, 90.0]), np.array([1.0, bad, 3.0]))

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_power_law_overflow_is_a_calculation_error(self):
        """Levels so large that the power law overflows: no fit is possible."""
        from hydrolog.exceptions import CalculationError
        from hydrolog.hydrometrics import RatingCurve, RatingCurveFitError

        curve = RatingCurve(
            np.array([1e250, 2e250, 3e250, 4e250]), np.array([1.0, 2.0, 3.0, 4.0])
        )
        with pytest.raises(RatingCurveFitError) as caught:
            curve.fit()
        assert isinstance(caught.value, CalculationError)
        assert caught.value.code == "calculation_error"
        assert caught.value.exit_code == 4
        assert caught.value.details == {"fit": "rating curve"}

    def test_non_convergence_is_a_calculation_error_catchable_as_before(
        self, curve_data, monkeypatch
    ):
        """Raised as ``InvalidParameterError`` (a ``ValueError``) before 1.0.0, so
        that is still what ``except`` clauses written for it catch."""
        from hydrolog.exceptions import CalculationError, InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve, RatingCurveFitError
        from hydrolog.hydrometrics import rating_curve

        def no_convergence(*args, **kwargs):
            raise RuntimeError("Optimal parameters not found: maxfev exceeded")

        monkeypatch.setattr(rating_curve, "curve_fit", no_convergence)
        with pytest.raises(RatingCurveFitError) as caught:
            RatingCurve(*curve_data).fit(h0_initial=50.0)
        error = caught.value
        assert isinstance(error, CalculationError)
        assert isinstance(error, InvalidParameterError)
        assert isinstance(error, ValueError)
        assert error.code == "calculation_error"
        assert "maxfev exceeded" in str(error)
        assert isinstance(error.__cause__, RuntimeError)


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
