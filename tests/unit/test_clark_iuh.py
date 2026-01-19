"""Tests for Clark Instantaneous Unit Hydrograph (IUH)."""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.runoff.clark_iuh import ClarkIUH, ClarkIUHResult, ClarkUHResult


class TestClarkIUHInit:
    """Tests for ClarkIUH initialization."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        assert iuh.tc_min == 60.0
        assert iuh.r_min == 30.0

    def test_init_zero_tc_raises(self):
        """Test that zero tc raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH(tc_min=0.0, r_min=30.0)
        assert "tc_min must be positive" in str(exc_info.value)

    def test_init_negative_tc_raises(self):
        """Test that negative tc raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH(tc_min=-10.0, r_min=30.0)
        assert "tc_min must be positive" in str(exc_info.value)

    def test_init_zero_r_raises(self):
        """Test that zero r raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH(tc_min=60.0, r_min=0.0)
        assert "r_min must be positive" in str(exc_info.value)

    def test_init_negative_r_raises(self):
        """Test that negative r raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH(tc_min=60.0, r_min=-10.0)
        assert "r_min must be positive" in str(exc_info.value)


class TestClarkIUHProperties:
    """Tests for ClarkIUH properties."""

    def test_lag_time(self):
        """Test lag time calculation."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        # lag = tc/2 + r = 30 + 30 = 60
        assert iuh.lag_time_min == 60.0

    def test_lag_time_different_values(self):
        """Test lag time with different parameters."""
        iuh = ClarkIUH(tc_min=100.0, r_min=50.0)

        # lag = 100/2 + 50 = 100
        assert iuh.lag_time_min == 100.0


class TestClarkIUHTimeArea:
    """Tests for time-area curve calculations."""

    def test_cumulative_time_area_at_zero(self):
        """Test cumulative area at t=0 is zero."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        assert iuh.cumulative_time_area(0.0) == 0.0

    def test_cumulative_time_area_at_tc(self):
        """Test cumulative area at t=Tc is 1."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        assert iuh.cumulative_time_area(60.0) == 1.0

    def test_cumulative_time_area_beyond_tc(self):
        """Test cumulative area beyond Tc is 1."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        assert iuh.cumulative_time_area(100.0) == 1.0

    def test_cumulative_time_area_monotonic(self):
        """Test cumulative area is monotonically increasing."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        times = np.linspace(0, 60, 13)
        areas = [iuh.cumulative_time_area(t) for t in times]

        for i in range(1, len(areas)):
            assert areas[i] >= areas[i - 1]

    def test_cumulative_time_area_range(self):
        """Test cumulative area is in [0, 1]."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        for t in np.linspace(-10, 100, 23):
            area = iuh.cumulative_time_area(t)
            assert 0.0 <= area <= 1.0

    def test_incremental_time_area_sums_to_one(self):
        """Test incremental areas sum to approximately 1."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        times = np.arange(0, 65, 5.0)
        incremental = iuh.incremental_time_area(times)

        assert abs(np.sum(incremental) - 1.0) < 0.01

    def test_incremental_time_area_non_negative(self):
        """Test all incremental areas are non-negative."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        times = np.arange(0, 65, 5.0)
        incremental = iuh.incremental_time_area(times)

        assert np.all(incremental >= 0)


class TestClarkIUHGenerate:
    """Tests for IUH generation."""

    def test_generate_returns_result(self):
        """Test generate returns ClarkIUHResult."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        assert isinstance(result, ClarkIUHResult)

    def test_generate_result_attributes(self):
        """Test result contains correct attributes."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        assert result.tc_min == 60.0
        assert result.r_min == 30.0
        assert len(result.times_min) == len(result.ordinates_per_min)
        assert result.time_to_peak_min >= 0
        assert result.peak_ordinate_per_min >= 0

    def test_generate_ordinates_sum_to_one(self):
        """Test IUH ordinates integrate to approximately 1."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        # Numerical integration
        integral = np.sum(result.ordinates_per_min) * 5.0

        assert abs(integral - 1.0) < 0.05

    def test_generate_ordinates_non_negative(self):
        """Test all ordinates are non-negative."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        assert np.all(result.ordinates_per_min >= 0)

    def test_generate_times_start_at_zero(self):
        """Test times start at zero."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        assert result.times_min[0] == 0.0

    def test_generate_n_steps_property(self):
        """Test n_steps property."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        assert result.n_steps == len(result.times_min)

    def test_generate_invalid_timestep_raises(self):
        """Test that invalid timestep raises error."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        with pytest.raises(InvalidParameterError) as exc_info:
            iuh.generate(timestep_min=0.0)
        assert "timestep_min must be positive" in str(exc_info.value)

    def test_generate_custom_duration(self):
        """Test generation with custom duration."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0, duration_min=500.0)

        assert result.times_min[-1] >= 500.0

    def test_generate_peak_timing_reasonable(self):
        """Test peak occurs at reasonable time."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        # Peak should occur after some translation but before too long
        assert 0 < result.time_to_peak_min < 2 * (60.0 + 30.0)


class TestClarkIUHToUnitHydrograph:
    """Tests for conversion to D-minute unit hydrograph."""

    def test_to_unit_hydrograph_returns_result(self):
        """Test to_unit_hydrograph returns ClarkUHResult."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=5.0
        )

        assert isinstance(result, ClarkUHResult)

    def test_to_unit_hydrograph_attributes(self):
        """Test result attributes are correct."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=5.0
        )

        assert result.area_km2 == 45.0
        assert result.duration_min == 30.0
        assert result.tc_min == 60.0
        assert result.r_min == 30.0

    def test_to_unit_hydrograph_water_balance(self):
        """Test unit hydrograph conserves water volume."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=5.0
        )

        # Volume = sum of ordinates * timestep in seconds
        volume_m3 = np.sum(result.ordinates_m3s) * 5.0 * 60.0

        # Expected volume for 1 mm over 45 km²
        expected_volume_m3 = 45.0 * 1e6 * 0.001  # 45000 m³

        # Allow 10% tolerance due to discretization
        assert abs(volume_m3 - expected_volume_m3) / expected_volume_m3 < 0.1

    def test_to_unit_hydrograph_invalid_area_raises(self):
        """Test that invalid area raises error."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        with pytest.raises(InvalidParameterError) as exc_info:
            iuh.to_unit_hydrograph(area_km2=0.0, duration_min=30.0)
        assert "area_km2 must be positive" in str(exc_info.value)

    def test_to_unit_hydrograph_invalid_duration_raises(self):
        """Test that invalid duration raises error."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)

        with pytest.raises(InvalidParameterError) as exc_info:
            iuh.to_unit_hydrograph(area_km2=45.0, duration_min=0.0)
        assert "duration_min must be positive" in str(exc_info.value)

    def test_to_unit_hydrograph_peak_discharge_positive(self):
        """Test peak discharge is positive."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=5.0
        )

        assert result.peak_discharge_m3s > 0

    def test_to_unit_hydrograph_n_steps(self):
        """Test n_steps property."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.to_unit_hydrograph(
            area_km2=45.0, duration_min=30.0, timestep_min=5.0
        )

        assert result.n_steps == len(result.times_min)


class TestClarkIUHFactoryMethods:
    """Tests for factory methods."""

    def test_from_recession_valid(self):
        """Test from_recession with valid parameters."""
        iuh = ClarkIUH.from_recession(tc_min=60.0, recession_constant=0.9)

        assert iuh.tc_min == 60.0
        assert iuh.r_min > 0

    def test_from_recession_invalid_tc_raises(self):
        """Test from_recession with invalid tc."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH.from_recession(tc_min=0.0, recession_constant=0.9)
        assert "tc_min must be positive" in str(exc_info.value)

    def test_from_recession_invalid_constant_raises(self):
        """Test from_recession with invalid recession constant."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH.from_recession(tc_min=60.0, recession_constant=1.5)
        assert "recession_constant must be in (0, 1)" in str(exc_info.value)

    def test_from_recession_constant_zero_raises(self):
        """Test from_recession with zero constant."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH.from_recession(tc_min=60.0, recession_constant=0.0)
        assert "recession_constant must be in (0, 1)" in str(exc_info.value)

    def test_from_tc_r_ratio_valid(self):
        """Test from_tc_r_ratio with valid parameters."""
        iuh = ClarkIUH.from_tc_r_ratio(tc_min=90.0, r_tc_ratio=0.5)

        assert iuh.tc_min == 90.0
        assert iuh.r_min == 45.0

    def test_from_tc_r_ratio_default(self):
        """Test from_tc_r_ratio with default ratio."""
        iuh = ClarkIUH.from_tc_r_ratio(tc_min=100.0)

        assert iuh.tc_min == 100.0
        assert iuh.r_min == 50.0  # 0.5 * 100

    def test_from_tc_r_ratio_invalid_tc_raises(self):
        """Test from_tc_r_ratio with invalid tc."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH.from_tc_r_ratio(tc_min=-10.0)
        assert "tc_min must be positive" in str(exc_info.value)

    def test_from_tc_r_ratio_invalid_ratio_raises(self):
        """Test from_tc_r_ratio with invalid ratio."""
        with pytest.raises(InvalidParameterError) as exc_info:
            ClarkIUH.from_tc_r_ratio(tc_min=60.0, r_tc_ratio=0.0)
        assert "r_tc_ratio must be positive" in str(exc_info.value)


class TestClarkIUHBehavior:
    """Tests for physical behavior of Clark model."""

    def test_larger_r_produces_broader_hydrograph(self):
        """Test that larger R produces broader, flatter hydrograph."""
        iuh_small_r = ClarkIUH(tc_min=60.0, r_min=20.0)
        iuh_large_r = ClarkIUH(tc_min=60.0, r_min=60.0)

        result_small = iuh_small_r.generate(timestep_min=5.0)
        result_large = iuh_large_r.generate(timestep_min=5.0)

        # Larger R should have lower peak
        assert result_large.peak_ordinate_per_min < result_small.peak_ordinate_per_min

    def test_larger_tc_shifts_peak_later(self):
        """Test that larger Tc shifts peak later."""
        iuh_small_tc = ClarkIUH(tc_min=30.0, r_min=30.0)
        iuh_large_tc = ClarkIUH(tc_min=90.0, r_min=30.0)

        result_small = iuh_small_tc.generate(timestep_min=5.0)
        result_large = iuh_large_tc.generate(timestep_min=5.0)

        # Larger Tc should have later peak
        assert result_large.time_to_peak_min > result_small.time_to_peak_min

    def test_hydrograph_shape_unimodal(self):
        """Test hydrograph has single peak (unimodal)."""
        iuh = ClarkIUH(tc_min=60.0, r_min=30.0)
        result = iuh.generate(timestep_min=5.0)

        # Find peaks (local maxima)
        ordinates = result.ordinates_per_min
        peaks = []
        for i in range(1, len(ordinates) - 1):
            if ordinates[i] > ordinates[i - 1] and ordinates[i] > ordinates[i + 1]:
                peaks.append(i)

        # Should have exactly one significant peak
        # (may have small numerical artifacts near zero)
        significant_peaks = [
            p for p in peaks if ordinates[p] > 0.1 * result.peak_ordinate_per_min
        ]
        assert len(significant_peaks) == 1
