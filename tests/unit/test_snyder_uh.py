"""Tests for Snyder Synthetic Unit Hydrograph."""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.runoff.snyder_uh import SnyderUH, SnyderUHResult


class TestSnyderUHInit:
    """Tests for SnyderUH initialization."""

    def test_init_valid_parameters(self):
        """Test initialization with valid parameters."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        assert uh.area_km2 == 100.0
        assert uh.L_km == 15.0
        assert uh.Lc_km == 8.0
        assert uh.ct == 1.5  # default (SI)
        assert uh.cp == 0.6  # default

    def test_init_custom_coefficients(self):
        """Test initialization with custom coefficients."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=1.8, cp=0.7)

        assert uh.ct == 1.8
        assert uh.cp == 0.7

    def test_init_zero_area_raises(self):
        """Test that zero area raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=0.0, L_km=15.0, Lc_km=8.0)
        assert "area_km2 must be positive" in str(exc_info.value)

    def test_init_negative_area_raises(self):
        """Test that negative area raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=-100.0, L_km=15.0, Lc_km=8.0)
        assert "area_km2 must be positive" in str(exc_info.value)

    def test_init_zero_L_raises(self):
        """Test that zero L raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=100.0, L_km=0.0, Lc_km=8.0)
        assert "L_km must be positive" in str(exc_info.value)

    def test_init_zero_Lc_raises(self):
        """Test that zero Lc raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=0.0)
        assert "Lc_km must be positive" in str(exc_info.value)

    def test_init_zero_ct_raises(self):
        """Test that zero ct raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=0.0)
        assert "ct must be positive" in str(exc_info.value)

    def test_init_zero_cp_raises(self):
        """Test that zero cp raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.0)
        assert "cp must be positive" in str(exc_info.value)


class TestSnyderUHProperties:
    """Tests for SnyderUH properties."""

    def test_lag_time_calculation(self):
        """Test lag time calculation."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=1.5)

        # tL = Ct * (L * Lc)^0.3 = 1.5 * (15 * 8)^0.3 = 1.5 * 120^0.3
        expected_hours = 1.5 * (120.0**0.3)
        assert abs(uh.lag_time_hours - expected_hours) < 0.01

    def test_lag_time_min_conversion(self):
        """Test lag time conversion to minutes."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        assert abs(uh.lag_time_min - uh.lag_time_hours * 60.0) < 0.01

    def test_standard_duration_calculation(self):
        """Test standard duration calculation."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        # D = tL / 5.5
        expected_hours = uh.lag_time_hours / 5.5
        assert abs(uh.standard_duration_hours - expected_hours) < 0.01

    def test_standard_duration_min_conversion(self):
        """Test standard duration conversion to minutes."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        assert abs(uh.standard_duration_min - uh.standard_duration_hours * 60.0) < 0.01


class TestSnyderUHTimings:
    """Tests for time calculations."""

    def test_time_to_peak_standard_duration(self):
        """Test time to peak with standard duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        # tp = tL + tD/2 for standard duration (where tLR = tL)
        tD = uh.standard_duration_hours
        expected_hours = uh.lag_time_hours + tD / 2.0
        actual_hours = uh.time_to_peak_hours()

        assert abs(actual_hours - expected_hours) < 0.01

    def test_time_to_peak_custom_duration(self):
        """Test time to peak with custom duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        tp_30 = uh.time_to_peak_min(duration_min=30.0)
        tp_60 = uh.time_to_peak_min(duration_min=60.0)

        # Longer duration should give later peak
        assert tp_60 > tp_30

    def test_time_base_calculation(self):
        """Test time base calculation using water balance formula."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        # tb = 0.556 * A / qP [hours] (water balance for triangular UH)
        qp = uh.peak_discharge()
        expected_hours = 0.556 * uh.area_km2 / qp
        assert abs(uh.time_base_hours() - expected_hours) < 0.01

    def test_time_base_min_conversion(self):
        """Test time base conversion to minutes."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        assert abs(uh.time_base_min() - uh.time_base_hours() * 60.0) < 0.01

    def test_time_base_adjusts_with_duration(self):
        """Test that time base adjusts for non-standard duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        tb_30 = uh.time_base_min(duration_min=30.0)
        tb_120 = uh.time_base_min(duration_min=120.0)

        # Longer duration -> lower qPR -> longer time base
        assert tb_120 > tb_30


class TestSnyderUHPeakDischarge:
    """Tests for peak discharge calculations."""

    def test_peak_discharge_standard_duration(self):
        """Test peak discharge with standard duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.6)

        # qp = 0.275 * Cp * A / tL (SI units)
        expected = 0.275 * 0.6 * 100.0 / uh.lag_time_hours
        actual = uh.peak_discharge()

        assert abs(actual - expected) < 0.01

    def test_peak_discharge_increases_with_area(self):
        """Test that peak discharge increases with area."""
        uh_small = SnyderUH(area_km2=50.0, L_km=15.0, Lc_km=8.0)
        uh_large = SnyderUH(area_km2=200.0, L_km=15.0, Lc_km=8.0)

        assert uh_large.peak_discharge() > uh_small.peak_discharge()

    def test_peak_discharge_increases_with_cp(self):
        """Test that peak discharge increases with Cp."""
        uh_low_cp = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.4)
        uh_high_cp = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.8)

        assert uh_high_cp.peak_discharge() > uh_low_cp.peak_discharge()


class TestSnyderUHWidth:
    """Tests for hydrograph width calculations."""

    def test_width_at_50_percent(self):
        """Test width at 50% of peak."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        w50 = uh.width_at_percent(50.0)
        assert w50 > 0

    def test_width_at_75_percent(self):
        """Test width at 75% of peak."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        w75 = uh.width_at_percent(75.0)
        assert w75 > 0

    def test_width_75_less_than_50(self):
        """Test that width at 75% is less than at 50%."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        w50 = uh.width_at_percent(50.0)
        w75 = uh.width_at_percent(75.0)

        assert w75 < w50

    def test_width_invalid_percent_raises(self):
        """Test that invalid percent raises error."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        with pytest.raises(InvalidParameterError) as exc_info:
            uh.width_at_percent(0.0)
        assert "percent must be in (0, 100]" in str(exc_info.value)

        with pytest.raises(InvalidParameterError) as exc_info:
            uh.width_at_percent(150.0)
        assert "percent must be in (0, 100]" in str(exc_info.value)


class TestSnyderUHGenerate:
    """Tests for UH generation."""

    def test_generate_returns_result(self):
        """Test generate returns SnyderUHResult."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        assert isinstance(result, SnyderUHResult)

    def test_generate_result_attributes(self):
        """Test result contains correct attributes."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        assert result.area_km2 == 100.0
        assert result.ct == 1.5
        assert result.cp == 0.6
        assert len(result.times_min) == len(result.ordinates_m3s)

    def test_generate_water_balance(self):
        """Test unit hydrograph conserves water volume."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        # Volume = sum of ordinates * timestep in seconds
        volume_m3 = np.sum(result.ordinates_m3s) * 30.0 * 60.0

        # Expected volume for 1 mm over 100 km²
        expected_volume_m3 = 100.0 * 1e6 * 0.001  # 100000 m³

        # Allow 10% tolerance
        assert abs(volume_m3 - expected_volume_m3) / expected_volume_m3 < 0.1

    def test_generate_ordinates_non_negative(self):
        """Test all ordinates are non-negative."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        assert np.all(result.ordinates_m3s >= 0)

    def test_generate_times_start_at_zero(self):
        """Test times start at zero."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        assert result.times_min[0] == 0.0

    def test_generate_n_steps_property(self):
        """Test n_steps property."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        assert result.n_steps == len(result.times_min)

    def test_generate_invalid_timestep_raises(self):
        """Test that invalid timestep raises error."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        with pytest.raises(InvalidParameterError) as exc_info:
            uh.generate(timestep_min=0.0)
        assert "timestep_min must be positive" in str(exc_info.value)

    def test_generate_custom_duration(self):
        """Test generation with custom duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0, duration_min=60.0)

        assert result.standard_duration_min == uh.standard_duration_min
        assert result.duration_min == 60.0

    def test_generate_duration_adjustment(self):
        """Test that lag time is correctly adjusted for non-standard duration."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)

        # Generate with standard duration
        result_std = uh.generate(timestep_min=30.0)
        assert abs(result_std.duration_min - uh.standard_duration_min) < 0.01
        assert abs(result_std.adjusted_lag_time_min - uh.lag_time_min) < 0.5

        # Generate with custom duration (longer than standard)
        D_prime = 120.0
        result_custom = uh.generate(timestep_min=30.0, duration_min=D_prime)

        # Verify adjustment formula: tLR = tL + 0.25 × (Δt - tD)
        D_std = uh.standard_duration_min
        expected_adj_lag = uh.lag_time_min + 0.25 * (D_prime - D_std)

        assert result_custom.duration_min == D_prime
        assert abs(result_custom.adjusted_lag_time_min - expected_adj_lag) < 0.5

        # Longer duration should increase adjusted lag time
        assert result_custom.adjusted_lag_time_min > result_std.adjusted_lag_time_min

    def test_generate_peak_timing_reasonable(self):
        """Test peak occurs at reasonable time."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        # Peak should be near calculated time to peak
        peak_idx = np.argmax(result.ordinates_m3s)
        actual_peak_time = result.times_min[peak_idx]

        # Allow some discretization error
        assert abs(actual_peak_time - result.time_to_peak_min) < 2 * 30.0


class TestSnyderUHBehavior:
    """Tests for physical behavior of Snyder model."""

    def test_larger_ct_produces_longer_lag(self):
        """Test that larger Ct produces longer lag time."""
        uh_small_ct = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=1.5)
        uh_large_ct = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, ct=2.5)

        assert uh_large_ct.lag_time_min > uh_small_ct.lag_time_min

    def test_larger_cp_produces_higher_peak(self):
        """Test that larger Cp produces higher peak discharge."""
        uh_small_cp = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.4)
        uh_large_cp = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0, cp=0.8)

        assert uh_large_cp.peak_discharge() > uh_small_cp.peak_discharge()

    def test_longer_stream_produces_longer_lag(self):
        """Test that longer stream produces longer lag time."""
        uh_short = SnyderUH(area_km2=100.0, L_km=10.0, Lc_km=5.0)
        uh_long = SnyderUH(area_km2=100.0, L_km=20.0, Lc_km=10.0)

        assert uh_long.lag_time_min > uh_short.lag_time_min

    def test_hydrograph_shape_unimodal(self):
        """Test hydrograph has single peak (unimodal)."""
        uh = SnyderUH(area_km2=100.0, L_km=15.0, Lc_km=8.0)
        result = uh.generate(timestep_min=30.0)

        # Find peaks (local maxima)
        ordinates = result.ordinates_m3s
        peaks = []
        for i in range(1, len(ordinates) - 1):
            if ordinates[i] > ordinates[i - 1] and ordinates[i] > ordinates[i + 1]:
                peaks.append(i)

        # Should have exactly one significant peak
        significant_peaks = [
            p for p in peaks if ordinates[p] > 0.1 * result.peak_discharge_m3s
        ]
        assert len(significant_peaks) == 1
