"""Tests for Nash Instantaneous Unit Hydrograph (IUH)."""

import numpy as np
import pytest

from hydrolog.runoff import NashIUH, IUHResult, NashUHResult
from hydrolog.exceptions import InvalidParameterError


class TestNashIUHInit:
    """Tests for NashIUH initialization."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        assert iuh.n == 3.0
        assert iuh.k_min == 30.0

    def test_init_non_integer_n(self):
        """Test that non-integer n is allowed."""
        iuh = NashIUH(n=2.5, k_min=20.0)

        assert iuh.n == 2.5

    def test_init_zero_n_raises(self):
        """Test that n=0 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="n must be positive"):
            NashIUH(n=0, k_min=30.0)

    def test_init_negative_n_raises(self):
        """Test that negative n raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="n must be positive"):
            NashIUH(n=-1.0, k_min=30.0)

    def test_init_zero_k_raises(self):
        """Test that k_min=0 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="k_min must be positive"):
            NashIUH(n=3.0, k_min=0)

    def test_init_negative_k_raises(self):
        """Test that negative k_min raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="k_min must be positive"):
            NashIUH(n=3.0, k_min=-10.0)


class TestNashIUHProperties:
    """Tests for NashIUH properties."""

    def test_lag_time(self):
        """Test lag time calculation."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        # tlag = n × K = 3 × 30 = 90 min
        assert iuh.lag_time_min == 90.0

    def test_time_to_peak_n_greater_than_1(self):
        """Test time to peak for n > 1."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        # tp = (n-1) × K = 2 × 30 = 60 min
        assert iuh.time_to_peak_min == 60.0

    def test_time_to_peak_n_equals_1(self):
        """Test time to peak for n = 1 (exponential decay)."""
        iuh = NashIUH(n=1.0, k_min=30.0)

        # For n <= 1, peak is at t = 0
        assert iuh.time_to_peak_min == 0.0

    def test_time_to_peak_n_less_than_1(self):
        """Test time to peak for n < 1."""
        iuh = NashIUH(n=0.5, k_min=30.0)

        assert iuh.time_to_peak_min == 0.0

    def test_peak_ordinate_n_equals_1(self):
        """Test peak ordinate for n = 1."""
        iuh = NashIUH(n=1.0, k_min=30.0)

        # For n = 1, up = 1/K
        assert abs(iuh.peak_ordinate_per_min - 1.0 / 30.0) < 1e-10

    def test_peak_ordinate_n_greater_than_1(self):
        """Test peak ordinate for n > 1."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        # Peak should be positive and less than 1/K
        assert iuh.peak_ordinate_per_min > 0
        assert iuh.peak_ordinate_per_min < 1.0 / 30.0


class TestNashIUHOrdinate:
    """Tests for single ordinate calculation."""

    def test_ordinate_at_zero(self):
        """Test that ordinate at t=0 is 0."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        assert iuh.ordinate(0.0) == 0.0

    def test_ordinate_negative_time(self):
        """Test that ordinate for negative time is 0."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        assert iuh.ordinate(-10.0) == 0.0

    def test_ordinate_at_peak(self):
        """Test ordinate at time to peak."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        ordinate_at_peak = iuh.ordinate(iuh.time_to_peak_min)

        # Should be close to peak ordinate
        assert abs(ordinate_at_peak - iuh.peak_ordinate_per_min) < 1e-6

    def test_ordinate_positive(self):
        """Test that ordinates are positive for positive time."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        for t in [10.0, 30.0, 60.0, 90.0, 120.0]:
            assert iuh.ordinate(t) > 0


class TestNashIUHGenerate:
    """Tests for IUH generation."""

    def test_generate_returns_iuh_result(self):
        """Test that generate returns IUHResult."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=5.0)

        assert isinstance(result, IUHResult)

    def test_generate_result_attributes(self):
        """Test that result has correct attributes."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=5.0)

        assert result.n == 3.0
        assert result.k_min == 30.0
        assert result.time_to_peak_min == 60.0
        assert result.lag_time_min == 90.0

    def test_generate_times_start_at_zero(self):
        """Test that times array starts at 0."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=5.0)

        assert result.times_min[0] == 0.0

    def test_generate_timestep_respected(self):
        """Test that timestep is correctly applied."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=10.0)

        # Check constant timestep
        diffs = np.diff(result.times_min)
        assert np.allclose(diffs, 10.0)

    def test_generate_ordinates_sum_to_one(self):
        """Test that IUH integrates to approximately 1."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=1.0, duration_min=500.0)

        # Numerical integration (trapezoidal)
        integral = np.trapezoid(result.ordinates_per_min, result.times_min)

        # Should integrate to 1.0 (unit impulse response)
        assert abs(integral - 1.0) < 0.01

    def test_generate_zero_timestep_raises(self):
        """Test that zero timestep raises error."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        with pytest.raises(InvalidParameterError, match="timestep_min must be positive"):
            iuh.generate(timestep_min=0)

    def test_generate_custom_duration(self):
        """Test generation with custom duration."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=5.0, duration_min=200.0)

        assert result.times_min[-1] >= 200.0


class TestNashIUHToUnitHydrograph:
    """Tests for conversion to D-minute unit hydrograph."""

    def test_to_uh_returns_nash_uh_result(self):
        """Test that to_unit_hydrograph returns NashUHResult."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)

        assert isinstance(result, NashUHResult)

    def test_to_uh_result_attributes(self):
        """Test result attributes."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)

        assert result.area_km2 == 45.0
        assert result.duration_min == 30.0
        assert result.n == 3.0
        assert result.k_min == 30.0

    def test_to_uh_positive_ordinates(self):
        """Test that UH ordinates are non-negative."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=30.0)

        assert np.all(result.ordinates_m3s >= 0)

    def test_to_uh_volume_conservation(self):
        """Test that UH preserves volume (1 mm over area)."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=1.0
        )

        # Volume = integral of Q(t) dt
        # Q in m³/s, t in min -> need to convert
        volume_m3 = np.trapezoid(result.ordinates_m3s, result.times_min * 60.0)

        # Expected volume: 1 mm over 45 km² = 45 × 1000 m³ = 45000 m³
        expected_volume = 45.0 * 1000.0

        # Allow 5% tolerance for numerical integration
        assert abs(volume_m3 - expected_volume) / expected_volume < 0.05

    def test_to_uh_peak_increases_with_area(self):
        """Test that larger area gives higher peak discharge."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result_small = iuh.to_unit_hydrograph(area_km2=20.0, duration_min=30.0)
        result_large = iuh.to_unit_hydrograph(area_km2=100.0, duration_min=30.0)

        assert result_large.peak_discharge_m3s > result_small.peak_discharge_m3s

    def test_to_uh_longer_duration_lower_peak(self):
        """Test that longer rainfall duration gives lower peak (same volume)."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result_short = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=15.0)
        result_long = iuh.to_unit_hydrograph(area_km2=45.0, duration_min=60.0)

        assert result_long.peak_discharge_m3s < result_short.peak_discharge_m3s

    def test_to_uh_zero_area_raises(self):
        """Test that zero area raises error."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            iuh.to_unit_hydrograph(area_km2=0, duration_min=30.0)

    def test_to_uh_zero_duration_raises(self):
        """Test that zero duration raises error."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        with pytest.raises(InvalidParameterError, match="duration_min must be positive"):
            iuh.to_unit_hydrograph(area_km2=45.0, duration_min=0)


class TestNashIUHFromTC:
    """Tests for creating NashIUH from time of concentration.

    Note: from_tc() is deprecated and will be removed in v1.0.0.
    These tests verify both functionality and deprecation warning.
    """

    def test_from_tc_emits_deprecation_warning(self):
        """Test that from_tc emits DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match="from_tc.*deprecated"):
            NashIUH.from_tc(tc_min=90.0)

    def test_from_tc_default_n(self):
        """Test from_tc with default n."""
        with pytest.warns(DeprecationWarning):
            iuh = NashIUH.from_tc(tc_min=90.0)

        # Default n = 3, lag_ratio = 0.6
        # tlag = 0.6 × 90 = 54 min
        # K = tlag / n = 54 / 3 = 18 min
        assert iuh.n == 3.0
        assert abs(iuh.k_min - 18.0) < 0.01

    def test_from_tc_custom_n(self):
        """Test from_tc with custom n."""
        with pytest.warns(DeprecationWarning):
            iuh = NashIUH.from_tc(tc_min=90.0, n=4.0)

        # tlag = 0.6 × 90 = 54 min
        # K = 54 / 4 = 13.5 min
        assert iuh.n == 4.0
        assert abs(iuh.k_min - 13.5) < 0.01

    def test_from_tc_custom_lag_ratio(self):
        """Test from_tc with custom lag ratio."""
        with pytest.warns(DeprecationWarning):
            iuh = NashIUH.from_tc(tc_min=100.0, n=3.0, lag_ratio=0.5)

        # tlag = 0.5 × 100 = 50 min
        # K = 50 / 3 = 16.67 min
        assert abs(iuh.lag_time_min - 50.0) < 0.01

    def test_from_tc_zero_tc_raises(self):
        """Test that zero tc raises error."""
        with pytest.warns(DeprecationWarning):
            with pytest.raises(InvalidParameterError, match="tc_min must be positive"):
                NashIUH.from_tc(tc_min=0)

    def test_from_tc_invalid_lag_ratio_raises(self):
        """Test that invalid lag ratio raises error."""
        with pytest.warns(DeprecationWarning):
            with pytest.raises(InvalidParameterError, match="lag_ratio must be in"):
                NashIUH.from_tc(tc_min=90.0, lag_ratio=0)

        with pytest.warns(DeprecationWarning):
            with pytest.raises(InvalidParameterError, match="lag_ratio must be in"):
                NashIUH.from_tc(tc_min=90.0, lag_ratio=1.5)


class TestNashIUHWithArea:
    """Tests for NashIUH with area_km2 parameter in constructor."""

    def test_init_with_area(self):
        """Test initialization with area_km2."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        assert iuh.n == 3.0
        assert iuh.k_min == 30.0
        assert iuh.area_km2 == 45.0

    def test_init_without_area(self):
        """Test initialization without area_km2."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        assert iuh.area_km2 is None

    def test_init_zero_area_raises(self):
        """Test that area_km2=0 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            NashIUH(n=3.0, k_min=30.0, area_km2=0)

    def test_init_negative_area_raises(self):
        """Test that negative area_km2 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            NashIUH(n=3.0, k_min=30.0, area_km2=-10.0)

    def test_generate_with_area_returns_nash_uh_result(self):
        """Test that generate() returns NashUHResult when area_km2 is set."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate(timestep_min=5.0)

        assert isinstance(result, NashUHResult)

    def test_generate_without_area_returns_iuh_result(self):
        """Test that generate() returns IUHResult when area_km2 is None."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate(timestep_min=5.0)

        assert isinstance(result, IUHResult)

    def test_generate_with_area_has_correct_attributes(self):
        """Test that NashUHResult has correct attributes."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate(timestep_min=5.0)

        assert result.area_km2 == 45.0
        assert result.n == 3.0
        assert result.k_min == 30.0
        assert result.duration_min == 5.0  # D = timestep

    def test_generate_with_area_positive_ordinates(self):
        """Test that UH ordinates are non-negative."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate(timestep_min=5.0)

        assert np.all(result.ordinates_m3s >= 0)

    def test_generate_with_area_volume_conservation(self):
        """Test that UH preserves volume (1 mm over area)."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate(timestep_min=1.0)

        # Volume = integral of Q(t) dt
        # Q in m³/s, t in min -> convert to seconds
        volume_m3 = np.trapezoid(result.ordinates_m3s, result.times_min * 60.0)

        # Expected volume: 1 mm over 45 km² = 45 × 1000 m³
        expected_volume = 45.0 * 1000.0

        # Allow 5% tolerance for numerical integration
        assert abs(volume_m3 - expected_volume) / expected_volume < 0.05


class TestNashIUHGenerateIUH:
    """Tests for explicit generate_iuh() method."""

    def test_generate_iuh_returns_iuh_result(self):
        """Test that generate_iuh() returns IUHResult even with area_km2."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate_iuh(timestep_min=5.0)

        assert isinstance(result, IUHResult)

    def test_generate_iuh_without_area_works(self):
        """Test that generate_iuh() works without area_km2."""
        iuh = NashIUH(n=3.0, k_min=30.0)

        result = iuh.generate_iuh(timestep_min=5.0)

        assert isinstance(result, IUHResult)

    def test_generate_iuh_ordinates_sum_to_one(self):
        """Test that IUH integrates to approximately 1."""
        iuh = NashIUH(n=3.0, k_min=30.0, area_km2=45.0)

        result = iuh.generate_iuh(timestep_min=1.0, duration_min=500.0)

        integral = np.trapezoid(result.ordinates_per_min, result.times_min)

        assert abs(integral - 1.0) < 0.01


class TestNashIUHFromLutz:
    """Tests for creating NashIUH using Lutz method."""

    def test_from_lutz_basic(self):
        """Test from_lutz with basic parameters."""
        nash = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
        )

        # Should return valid Nash parameters
        assert nash.n > 1.0
        assert nash.k_min > 0
        assert nash.area_km2 is None

    def test_from_lutz_with_area(self):
        """Test from_lutz with area_km2."""
        nash = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            area_km2=50.0,
        )

        assert nash.area_km2 == 50.0

    def test_from_lutz_forest_effect(self):
        """Test that forest increases time to peak (larger K)."""
        nash_no_forest = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            forest_pct=0.0,
        )
        nash_with_forest = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            forest_pct=50.0,
        )

        # Forest should increase lag time (more retention)
        assert nash_with_forest.lag_time_min > nash_no_forest.lag_time_min

    def test_from_lutz_urban_effect(self):
        """Test that urbanization decreases time to peak (smaller K)."""
        nash_no_urban = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            urban_pct=0.0,
        )
        nash_with_urban = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            urban_pct=30.0,
        )

        # Urbanization should decrease lag time (faster response)
        assert nash_with_urban.lag_time_min < nash_no_urban.lag_time_min

    def test_from_lutz_steeper_slope_faster_response(self):
        """Test that steeper slope gives faster response."""
        nash_gentle = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.01,
            manning_n=0.035,
        )
        nash_steep = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.05,
            manning_n=0.035,
        )

        # Steeper slope should give faster response (smaller lag)
        assert nash_steep.lag_time_min < nash_gentle.lag_time_min

    def test_from_lutz_higher_manning_slower_response(self):
        """Test that higher Manning n gives slower response."""
        nash_smooth = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.025,
        )
        nash_rough = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.050,
        )

        # Rougher channel should give slower response (larger lag)
        assert nash_rough.lag_time_min > nash_smooth.lag_time_min

    def test_from_lutz_longer_stream_slower_response(self):
        """Test that longer stream gives slower response."""
        nash_short = NashIUH.from_lutz(
            L_km=10.0,
            Lc_km=5.0,
            slope=0.02,
            manning_n=0.035,
        )
        nash_long = NashIUH.from_lutz(
            L_km=30.0,
            Lc_km=15.0,
            slope=0.02,
            manning_n=0.035,
        )

        # Longer stream should give slower response
        assert nash_long.lag_time_min > nash_short.lag_time_min

    def test_from_lutz_n_in_reasonable_range(self):
        """Test that calculated N is in reasonable range for natural catchments."""
        nash = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
        )

        # N should typically be between 1.5 and 10 for natural catchments
        assert 1.1 < nash.n < 15.0

    def test_from_lutz_zero_L_raises(self):
        """Test that L_km=0 raises error."""
        with pytest.raises(InvalidParameterError, match="L_km must be positive"):
            NashIUH.from_lutz(
                L_km=0,
                Lc_km=5.0,
                slope=0.02,
                manning_n=0.035,
            )

    def test_from_lutz_zero_Lc_raises(self):
        """Test that Lc_km=0 raises error."""
        with pytest.raises(InvalidParameterError, match="Lc_km must be positive"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=0,
                slope=0.02,
                manning_n=0.035,
            )

    def test_from_lutz_Lc_greater_than_L_raises(self):
        """Test that Lc > L raises error."""
        with pytest.raises(InvalidParameterError, match="Lc_km.*cannot exceed L_km"):
            NashIUH.from_lutz(
                L_km=10.0,
                Lc_km=15.0,
                slope=0.02,
                manning_n=0.035,
            )

    def test_from_lutz_zero_slope_raises(self):
        """Test that slope=0 raises error."""
        with pytest.raises(InvalidParameterError, match="slope must be positive"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0,
                manning_n=0.035,
            )

    def test_from_lutz_zero_manning_raises(self):
        """Test that manning_n=0 raises error."""
        with pytest.raises(InvalidParameterError, match="manning_n must be positive"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0.02,
                manning_n=0,
            )

    def test_from_lutz_invalid_urban_pct_raises(self):
        """Test that invalid urban_pct raises error."""
        with pytest.raises(InvalidParameterError, match="urban_pct must be in"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0.02,
                manning_n=0.035,
                urban_pct=-10.0,
            )

        with pytest.raises(InvalidParameterError, match="urban_pct must be in"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0.02,
                manning_n=0.035,
                urban_pct=150.0,
            )

    def test_from_lutz_invalid_forest_pct_raises(self):
        """Test that invalid forest_pct raises error."""
        with pytest.raises(InvalidParameterError, match="forest_pct must be in"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0.02,
                manning_n=0.035,
                forest_pct=-5.0,
            )

    def test_from_lutz_zero_area_raises(self):
        """Test that area_km2=0 raises error."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            NashIUH.from_lutz(
                L_km=15.0,
                Lc_km=8.0,
                slope=0.02,
                manning_n=0.035,
                area_km2=0,
            )

    def test_from_lutz_generate_works(self):
        """Test that generated Nash can produce hydrograph."""
        nash = NashIUH.from_lutz(
            L_km=15.0,
            Lc_km=8.0,
            slope=0.02,
            manning_n=0.035,
            area_km2=50.0,
        )

        result = nash.generate(timestep_min=10.0)

        assert isinstance(result, NashUHResult)
        assert result.peak_discharge_m3s > 0
        assert len(result.times_min) > 0


class TestNashIUHImport:
    """Test module imports."""

    def test_import_from_runoff_module(self):
        """Test that Nash classes can be imported from hydrolog.runoff."""
        from hydrolog.runoff import NashIUH, IUHResult, NashUHResult

        assert NashIUH is not None
        assert IUHResult is not None
        assert NashUHResult is not None
