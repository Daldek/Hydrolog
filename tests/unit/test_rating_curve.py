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

    def test_mismatched_lengths_are_refused_by_the_fit(self):
        """The spec rating_curve_fit checks the pairs when ``fit`` uses them; the
        constructor no longer does (CMP-3.5)."""
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        curve = RatingCurve(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))
        with pytest.raises(InvalidParameterError) as caught:
            curve.fit()
        assert caught.value.details["reason"] == "outside_physical_range"
        assert caught.value.details["constraint"] == "same_length"
        assert caught.value.details["option"] == "discharges"

    def test_too_few_points_are_refused_by_the_fit(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics.rating_curve import RatingCurve

        with pytest.raises(InvalidParameterError) as caught:
            RatingCurve(np.array([1.0, 2.0]), np.array([1.0, 2.0])).fit()
        assert caught.value.details["reason"] == "precondition_failed"
        assert caught.value.details["constraint"] == "enough_pairs"


class TestRatingCurveErrors:
    """Failure modes of ``RatingCurve`` are Hydrolog errors of the right kind."""

    @pytest.fixture
    def curve_data(self):
        h = np.linspace(60.0, 200.0, 20)
        return h, 2.5 * (h - 50.0) ** 1.8

    @pytest.mark.parametrize(
        ("h0_initial", "reason"),
        [
            (60.0, "precondition_failed"),
            (70.0, "precondition_failed"),
            (float("nan"), "outside_physical_range"),
            (float("inf"), "outside_physical_range"),
            (-float("inf"), "outside_physical_range"),
        ],
    )
    def test_initial_zero_level_must_be_finite_and_below_every_level(
        self, curve_data, h0_initial, reason
    ):
        """Was a bare ``ValueError`` from SciPy (``x0`` is infeasible); since 0.9.0
        the refusal of spec ``rating_curve_fit``."""
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        with pytest.raises(InvalidParameterError) as caught:
            RatingCurve(*curve_data).fit(h0_initial=h0_initial)
        assert caught.value.code == "validation_error"
        assert caught.value.details["option"] == "h0_initial"
        assert caught.value.details["reason"] == reason
        if reason == "precondition_failed":
            assert caught.value.details["constraint"] == "start_below_levels"
            assert "lower than every water level" in caught.value.hint

    def test_initial_zero_level_error_is_still_a_value_error(self, curve_data):
        from hydrolog.hydrometrics import RatingCurve

        with pytest.raises(ValueError):
            RatingCurve(*curve_data).fit(h0_initial=70.0)

    def test_initial_zero_level_just_below_the_lowest_level_is_accepted(
        self, curve_data
    ):
        """The search keeps H0 a little below the lowest level; a start inside that
        margin is moved to the bound instead of failing."""
        from hydrolog.hydrometrics import RatingCurve

        result = RatingCurve(*curve_data).fit(h0_initial=60.0 - 1e-7)
        assert result.h0 == pytest.approx(50.0, abs=0.5)

    @pytest.mark.parametrize("bad", [float("nan"), float("inf")])
    def test_non_finite_measurements_are_refused(self, bad):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        for levels, discharges, option in (
            ([60.0, 80.0, bad], [1.0, 2.0, 3.0], "water_levels"),
            ([60.0, 80.0, 90.0], [1.0, bad, 3.0], "discharges"),
        ):
            with pytest.raises(InvalidParameterError, match="finite") as caught:
                RatingCurve(np.array(levels), np.array(discharges)).fit(50.0)
            assert caught.value.details["option"] == option

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_a_curve_beyond_float64_is_refused(self):
        """Levels of 1e250 fit now, as the search runs on normalised pairs (their power
        law overflowed into a calculation_error before 0.9.0): Q = 1e-250 H. Their
        square, Q = 1e-400 H^2, has an a below every float64: the precondition
        least_squares_minimum refuses it."""
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        huge = np.array([1e250, 2e250, 3e250, 4e250])
        linear = RatingCurve(huge, np.array([1.0, 2.0, 3.0, 4.0])).fit()
        assert linear.b == pytest.approx(1.0, rel=1e-6)
        assert linear.a == pytest.approx(1e-250, rel=1e-5)
        with pytest.raises(InvalidParameterError) as caught:
            RatingCurve(huge / 1e50, np.array([1.0, 4.0, 9.0, 16.0])).fit()
        assert caught.value.code == "validation_error"
        assert caught.value.details["reason"] == "precondition_failed"
        assert caught.value.details["constraint"] == "least_squares_minimum"

    def test_non_convergence_is_still_a_value_error(self, curve_data, monkeypatch):
        """A search that does not settle was ``RatingCurveFitError`` (a
        ``CalculationError`` and an ``InvalidParameterError``) up to 0.8.1: an
        ``except ValueError`` or ``except InvalidParameterError`` written for it still
        catches the refusal of the precondition."""
        from hydrolog.exceptions import CalculationError, InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve, rating_curve

        def no_convergence(*args, **kwargs):
            raise RuntimeError("Optimal parameters not found: maxfev exceeded")

        rating_curve._normalised_search.cache_clear()
        monkeypatch.setattr(rating_curve, "curve_fit", no_convergence)
        with pytest.raises(ValueError) as caught:
            RatingCurve(*curve_data).fit(h0_initial=50.0)
        rating_curve._normalised_search.cache_clear()
        error = caught.value
        assert isinstance(error, InvalidParameterError)
        assert not isinstance(error, CalculationError)
        assert error.code == "validation_error"
        assert error.details["constraint"] == "least_squares_minimum"


class TestRatingCurveDefaultStart:
    """The start of H0 is chosen from the data when ``h0_initial`` is not given.

    Regression: the fixed default 0.0 had to lie below the lowest level, so a series
    with a reading at or below zero (a stage of -10 cm is normal) could not be fitted
    without choosing a start by hand: "h0_initial must be a finite number below the
    lowest water level (-10), got 0.0".
    """

    NEGATIVE_LEVELS = np.array([-10.0, 5.0, 20.0, 40.0, 80.0, 120.0])
    NEGATIVE_FLOWS = np.array([0.5, 1.2, 2.5, 4.8, 10.1, 17.3])

    def test_a_series_with_negative_levels_can_be_fitted_without_a_start(self):
        from hydrolog.hydrometrics import RatingCurve

        result = RatingCurve(self.NEGATIVE_LEVELS, self.NEGATIVE_FLOWS).fit()
        assert result.a == pytest.approx(0.004917, rel=1e-3)
        assert result.b == pytest.approx(1.640, abs=1e-3)
        assert result.h0 == pytest.approx(-25.17, abs=0.01)
        assert result.r_squared > 0.999

    @pytest.mark.parametrize(
        ("levels", "start"),
        [
            ([60.0, 80.0, 100.0, 130.0, 160.0, 200.0], 60.0 - 14.0),
            ([-10.0, 5.0, 20.0, 40.0, 80.0, 120.0], -10.0 - 13.0),
            ([-300.0, -250.0, -200.0, -100.0], -300.0 - 20.0),
            ([1.2, 1.5, 1.9, 2.4], 1.2 - 1.0),
        ],
        ids=["a tenth of the range", "negative", "all negative", "at least one unit"],
    )
    def test_the_start_is_a_tenth_of_the_range_below_the_lowest_level(
        self, levels, start
    ):
        """``min(H) - max(1, 0.1 * range)`` (Tier B ``rating_curve_start``): the fit
        without a start is the fit from it."""
        from hydrolog.hydrometrics import RatingCurve

        h = np.array(levels)
        q = 0.05 * (h - (h.min() - 0.3 * (h.max() - h.min()))) ** 1.6
        assert RatingCurve(h, q).fit() == RatingCurve(h, q).fit(h0_initial=start)

    def test_no_start_is_the_same_as_the_documented_start(self):
        from hydrolog.hydrometrics import RatingCurve

        h = np.linspace(60.0, 200.0, 20)
        q = 2.5 * (h - 50.0) ** 1.8
        assert RatingCurve(h, q).fit() == RatingCurve(h, q).fit(h0_initial=46.0)
        assert RatingCurve(h, q).fit(h0_initial=None) == RatingCurve(h, q).fit()

    def test_the_default_start_gives_the_solution_of_the_explicit_starts(self):
        """Noisy synthetic curve, levels in m: the start does not change the fit."""
        from hydrolog.hydrometrics import RatingCurve

        rng = np.random.default_rng(11)
        h = np.sort(rng.uniform(-0.4, 2.1, 25))
        q = 12.0 * (h + 0.9) ** 1.7 * np.exp(rng.normal(0.0, 0.03, 25))
        by_default = RatingCurve(h, q).fit()
        for start in (h.min() - 0.05, h.min() - 1.0, h.min() - 3.0):
            explicit = RatingCurve(h, q).fit(h0_initial=start)
            assert explicit.h0 == pytest.approx(by_default.h0, abs=1e-3)
            assert explicit.b == pytest.approx(by_default.b, abs=1e-3)
        assert by_default.h0 == pytest.approx(-0.9, abs=0.1)
        assert by_default.b == pytest.approx(1.7, abs=0.1)

    @pytest.mark.parametrize("bad", [-5.0, 0.0, float("nan"), float("inf")])
    def test_a_given_start_is_validated_whatever_the_levels(self, bad):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics import RatingCurve

        curve = RatingCurve(self.NEGATIVE_LEVELS, self.NEGATIVE_FLOWS)
        with pytest.raises(InvalidParameterError) as caught:
            curve.fit(h0_initial=bad)
        assert caught.value.details["option"] == "h0_initial"


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
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        with pytest.raises(InvalidParameterError):
            WaterLevelFrequency(np.array([]))

    def test_invalid_bin_width_raises(self):
        from hydrolog.exceptions import InvalidParameterError
        from hydrolog.hydrometrics.rating_curve import WaterLevelFrequency

        with pytest.raises(InvalidParameterError):
            WaterLevelFrequency(np.array([1.0, 2.0]), bin_width=0.0)
