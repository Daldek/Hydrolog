"""Tests for runoff generation module."""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation import BetaHietogram, BlockHietogram
from hydrolog.runoff import (
    AMC,
    SCSCN,
    HydrographGenerator,
    HydrographResult,
    SCSUnitHydrograph,
    SnyderUH,
    convolve_discrete,
)


class TestSCSCN:
    """Tests for SCS Curve Number calculations."""

    def test_retention_typical_cn(self):
        """Test retention calculation for typical CN."""
        scs = SCSCN(cn=72)
        s = scs.retention(72)
        # S = 25400/72 - 254 = 98.78 mm
        assert abs(s - 98.78) < 0.1

    def test_retention_cn_100(self):
        """Test that CN=100 gives zero retention."""
        scs = SCSCN(cn=100)
        s = scs.retention(100)
        assert s == 0.0

    def test_retention_cn_50(self):
        """Test retention for CN=50."""
        scs = SCSCN(cn=50)
        s = scs.retention(50)
        # S = 25400/50 - 254 = 254 mm
        assert abs(s - 254.0) < 0.1

    def test_initial_abstraction(self):
        """Test initial abstraction calculation."""
        scs = SCSCN(cn=72)
        s = scs.retention(72)
        ia = scs.initial_abstraction(s)
        # Ia = 0.2 * 98.78 = 19.76 mm
        assert abs(ia - 19.76) < 0.1

    def test_initial_abstraction_custom_coefficient(self):
        """Test initial abstraction with custom coefficient."""
        scs = SCSCN(cn=72, ia_coefficient=0.05)
        s = scs.retention(72)
        ia = scs.initial_abstraction(s)
        # Ia = 0.05 * 98.78 = 4.94 mm
        assert abs(ia - 4.94) < 0.1

    def test_effective_precipitation_below_ia(self):
        """Test that precipitation below Ia gives no runoff."""
        scs = SCSCN(cn=72)
        result = scs.effective_precipitation(10.0)  # Below Ia ≈ 19.76 mm
        assert result.total_effective_mm == 0.0

    def test_effective_precipitation_above_ia(self):
        """Test effective precipitation calculation."""
        scs = SCSCN(cn=72)
        result = scs.effective_precipitation(50.0)
        # Pe = (50 - 19.76)² / (50 - 19.76 + 98.78) = 7.08 mm
        assert 6.5 < result.total_effective_mm < 7.5

    def test_effective_precipitation_array_input(self):
        """Test effective precipitation with array input."""
        scs = SCSCN(cn=72)
        precip = [10.0, 15.0, 20.0, 10.0, 5.0]
        result = scs.effective_precipitation(precip)

        # Total precipitation = 60 mm
        assert isinstance(result.effective_mm, np.ndarray)
        assert len(result.effective_mm) == 5
        assert result.total_effective_mm > 0

    def test_effective_precipitation_cn_100(self):
        """Test that CN=100 gives all precipitation as runoff after Ia."""
        scs = SCSCN(cn=100)
        result = scs.effective_precipitation(50.0)
        # CN=100: S=0, Ia=0, Pe = P
        assert abs(result.total_effective_mm - 50.0) < 0.01

    def test_amc_adjustment_dry(self):
        """Test CN adjustment for dry conditions (AMC-I)."""
        scs = SCSCN(cn=72)
        cn_i = scs.adjust_cn_for_amc(AMC.I)
        # Dry conditions should give lower CN
        assert cn_i < 72

    def test_amc_adjustment_wet(self):
        """Test CN adjustment for wet conditions (AMC-III)."""
        scs = SCSCN(cn=72)
        cn_iii = scs.adjust_cn_for_amc(AMC.III)
        # Wet conditions should give higher CN
        assert cn_iii > 72

    def test_amc_adjustment_normal(self):
        """Test CN adjustment for normal conditions (AMC-II)."""
        scs = SCSCN(cn=72)
        cn_ii = scs.adjust_cn_for_amc(AMC.II)
        # Normal conditions: no change
        assert cn_ii == 72

    def test_effective_precipitation_with_amc(self):
        """Test effective precipitation with AMC adjustment."""
        scs = SCSCN(cn=72)

        result_dry = scs.effective_precipitation(50.0, amc=AMC.I)
        result_normal = scs.effective_precipitation(50.0, amc=AMC.II)
        result_wet = scs.effective_precipitation(50.0, amc=AMC.III)

        # Wet > Normal > Dry
        assert result_wet.total_effective_mm > result_normal.total_effective_mm
        assert result_normal.total_effective_mm > result_dry.total_effective_mm

    def test_runoff_coefficient(self):
        """Test runoff coefficient calculation."""
        scs = SCSCN(cn=72)
        c = scs.runoff_coefficient(50.0)
        # C should be between 0 and 1
        assert 0 < c < 1

    def test_runoff_coefficient_zero_precip(self):
        """Test runoff coefficient with zero precipitation."""
        scs = SCSCN(cn=72)
        c = scs.runoff_coefficient(0.0)
        assert c == 0.0

    def test_invalid_cn_too_low(self):
        """Test that CN < 1 raises error."""
        with pytest.raises(InvalidParameterError, match="cn must be in range"):
            SCSCN(cn=0)

    def test_invalid_cn_too_high(self):
        """Test that CN > 100 raises error."""
        with pytest.raises(InvalidParameterError, match="cn must be in range"):
            SCSCN(cn=101)

    def test_invalid_ia_coefficient(self):
        """Test that invalid ia_coefficient raises error."""
        with pytest.raises(InvalidParameterError, match="ia_coefficient"):
            SCSCN(cn=72, ia_coefficient=0.0)


class TestSCSUnitHydrograph:
    """Tests for SCS Unit Hydrograph generation."""

    def test_lag_time(self):
        """Test lag time calculation."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        # tlag = 0.6 * tc = 54 min
        assert abs(uh.lag_time_min - 54.0) < 0.1

    def test_time_to_peak(self):
        """Test time to peak calculation."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        tp = uh.time_to_peak(timestep_min=10.0)
        # tp = D/2 + tlag = 5 + 54 = 59 min
        assert abs(tp - 59.0) < 0.1

    def test_peak_discharge(self):
        """Test peak discharge calculation."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        qp = uh.peak_discharge(timestep_min=10.0)
        # qp = 0.208 * A / tp_h = 0.208 * 45 / (59/60) = 9.52 m³/s per mm
        assert 9 < qp < 10

    def test_generate_hydrograph(self):
        """Test unit hydrograph generation."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        result = uh.generate(timestep_min=5.0)

        assert result.n_steps > 0
        assert result.peak_discharge_m3s > 0
        assert result.time_to_peak_min > 0
        assert len(result.times_min) == len(result.ordinates_m3s)

    def test_hydrograph_starts_at_zero(self):
        """Test that hydrograph starts at zero."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        result = uh.generate(timestep_min=5.0)
        assert result.ordinates_m3s[0] == 0.0

    def test_hydrograph_ends_near_zero(self):
        """Test that hydrograph ends near zero."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        result = uh.generate(timestep_min=5.0)
        assert result.ordinates_m3s[-1] < 0.01 * result.peak_discharge_m3s

    def test_peak_at_expected_time(self):
        """Test that peak occurs at expected time."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        result = uh.generate(timestep_min=5.0)

        peak_idx = np.argmax(result.ordinates_m3s)
        peak_time = result.times_min[peak_idx]

        # Peak should be near tp
        assert abs(peak_time - result.time_to_peak_min) < 10.0

    def test_invalid_area(self):
        """Test that non-positive area raises error."""
        with pytest.raises(InvalidParameterError, match="area_km2"):
            SCSUnitHydrograph(area_km2=0, tc_min=90.0)

    def test_invalid_tc(self):
        """Test that non-positive tc raises error."""
        with pytest.raises(InvalidParameterError, match="tc_min"):
            SCSUnitHydrograph(area_km2=45.0, tc_min=-10.0)

    def test_invalid_timestep(self):
        """Test that non-positive timestep raises error."""
        uh = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0)
        with pytest.raises(InvalidParameterError, match="timestep_min"):
            uh.generate(timestep_min=0)


class TestConvolution:
    """Tests for discrete convolution."""

    def test_convolution_simple(self):
        """Test simple convolution."""
        pe = np.array([0.0, 5.0, 10.0, 5.0, 0.0])
        uh = np.array([0.0, 0.5, 1.0, 0.5, 0.0])

        result = convolve_discrete(pe, uh, timestep_min=5.0)

        # Result length should be len(pe) + len(uh) - 1
        assert result.n_steps == 9

    def test_convolution_peak(self):
        """Test that convolution produces a peak."""
        pe = np.array([0.0, 5.0, 10.0, 5.0, 0.0])
        uh = np.array([0.0, 0.5, 1.0, 0.5, 0.0])

        result = convolve_discrete(pe, uh, timestep_min=5.0)

        assert result.peak_discharge_m3s > 0

    def test_convolution_volume(self):
        """Test that convolution preserves volume."""
        pe = np.array([5.0, 10.0, 5.0])  # 20 mm total
        uh = np.array([0.5, 1.0, 0.5])  # Simple unit hydrograph

        result = convolve_discrete(pe, uh, timestep_min=10.0)

        # Volume should be positive
        assert result.total_volume_m3 > 0

    def test_convolution_time_array(self):
        """Test that time array is correct."""
        pe = np.array([5.0, 10.0, 5.0])
        uh = np.array([0.5, 1.0])

        result = convolve_discrete(pe, uh, timestep_min=10.0)

        # Check time increments
        expected_times = np.array([0.0, 10.0, 20.0, 30.0])
        np.testing.assert_array_almost_equal(result.times_min, expected_times)

    def test_convolution_empty_precip_raises(self):
        """Test that empty precipitation raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            convolve_discrete(np.array([]), np.array([1.0]), timestep_min=5.0)

    def test_convolution_empty_uh_raises(self):
        """Test that empty unit hydrograph raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            convolve_discrete(np.array([1.0]), np.array([]), timestep_min=5.0)

    def test_convolution_invalid_timestep(self):
        """Test that invalid timestep raises error."""
        with pytest.raises(InvalidParameterError, match="timestep_min"):
            convolve_discrete(np.array([1.0]), np.array([1.0]), timestep_min=0)


class TestHydrographGenerator:
    """Tests for HydrographGenerator."""

    def test_generator_with_hietogram(self):
        """Test generator with HietogramResult input."""
        hietogram = BlockHietogram()
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip)

        assert result.peak_discharge_m3s > 0
        assert result.time_to_peak_min > 0
        assert result.total_volume_m3 > 0

    def test_generator_with_array(self):
        """Test generator with array input."""
        precip = [5.0, 10.0, 15.0, 10.0, 5.0, 3.0]

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip, timestep_min=10.0)

        assert result.peak_discharge_m3s > 0
        assert result.total_precip_mm == 48.0

    def test_generator_runoff_coefficient(self):
        """Test that runoff coefficient is calculated correctly."""
        hietogram = BlockHietogram()
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip)

        # Runoff coefficient should be between 0 and 1
        assert 0 < result.runoff_coefficient < 1

        # Verify: C = Pe_total / P_total
        expected_c = result.total_effective_mm / result.total_precip_mm
        assert abs(result.runoff_coefficient - expected_c) < 0.001

    def test_generator_with_amc(self):
        """Test generator with different AMC conditions."""
        hietogram = BlockHietogram()
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)

        result_dry = generator.generate(precip, amc=AMC.I)
        result_normal = generator.generate(precip, amc=AMC.II)
        result_wet = generator.generate(precip, amc=AMC.III)

        # Wet conditions should produce more runoff
        assert result_wet.peak_discharge_m3s > result_normal.peak_discharge_m3s
        assert result_normal.peak_discharge_m3s > result_dry.peak_discharge_m3s

    def test_generator_effective_precipitation_length(self):
        """Test that effective precipitation has correct length."""
        precip = [5.0, 10.0, 15.0, 10.0, 5.0]

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip, timestep_min=10.0)

        assert len(result.effective_precip_mm) == len(precip)

    def test_generator_water_balance(self):
        """Test water balance (effective <= total)."""
        hietogram = BetaHietogram(alpha=2.0, beta=5.0)
        precip = hietogram.generate(total_mm=80.0, duration_min=120.0, timestep_min=5.0)

        generator = HydrographGenerator(area_km2=45.0, cn=75, tc_min=60.0)
        result = generator.generate(precip)

        # Effective precipitation should be <= total
        assert result.total_effective_mm <= result.total_precip_mm

        # Sum of effective increments should equal total effective
        assert (
            abs(np.sum(result.effective_precip_mm) - result.total_effective_mm) < 0.01
        )

    def test_generator_invalid_area(self):
        """Test that invalid area raises error."""
        with pytest.raises(InvalidParameterError, match="area_km2"):
            HydrographGenerator(area_km2=0, cn=72, tc_min=90.0)

    def test_generator_invalid_tc(self):
        """Test that invalid tc raises error."""
        with pytest.raises(InvalidParameterError, match="tc_min"):
            HydrographGenerator(area_km2=45.0, cn=72, tc_min=-10.0)

    def test_generator_empty_precip(self):
        """Test that empty precipitation raises error."""
        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            generator.generate([])

    def test_generator_cn_property(self):
        """Test CN property accessor."""
        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        assert generator.cn == 72

    def test_generator_unit_hydrograph_result_populated(self):
        """Test that unit_hydrograph_result is populated after generate()."""
        hietogram = BlockHietogram()
        precip = hietogram.generate(total_mm=50.0, duration_min=60.0, timestep_min=5.0)

        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate(precip)

        assert result.unit_hydrograph_result is not None
        # SCS model returns UnitHydrographResult with ordinates_m3s
        assert hasattr(result.unit_hydrograph_result, "ordinates_m3s")
        assert hasattr(result.unit_hydrograph_result, "times_min")
        assert len(result.unit_hydrograph_result.ordinates_m3s) > 0

    def test_generator_unit_hydrograph_result_default_none(self):
        """Test that unit_hydrograph_result defaults to None."""
        from hydrolog.runoff import HydrographGeneratorResult

        # Create a minimal HydrographGeneratorResult without the new field
        hydrograph = HydrographResult(
            times_min=np.array([0.0, 5.0]),
            discharge_m3s=np.array([0.0, 1.0]),
            peak_discharge_m3s=1.0,
            time_to_peak_min=5.0,
            total_volume_m3=300.0,
            timestep_min=5.0,
        )
        gen_result = HydrographGeneratorResult(
            hydrograph=hydrograph,
            effective_precip_mm=np.array([1.0]),
            total_precip_mm=10.0,
            total_effective_mm=1.0,
            runoff_coefficient=0.1,
            cn_used=72,
            retention_mm=50.0,
            initial_abstraction_mm=10.0,
        )
        assert gen_result.unit_hydrograph_result is None


class TestHydrographGeneratorModels:
    """Tests for HydrographGenerator with different UH models."""

    def test_default_is_scs_model(self):
        """Test that default model is SCS."""
        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        assert generator.uh_model == "scs"

    def test_scs_model_explicit(self):
        """Test SCS model with explicit parameter."""
        generator = HydrographGenerator(
            area_km2=45.0, cn=72, tc_min=90.0, uh_model="scs"
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)

        assert result.peak_discharge_m3s > 0
        assert result.hydrograph is not None

    def test_nash_model(self):
        """Test Nash model."""
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            uh_params={"n": 3.0, "k": 0.5},  # k in hours by default
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)

        assert result.peak_discharge_m3s > 0
        assert result.hydrograph is not None

    def test_nash_model_k_in_minutes(self):
        """Test Nash model with k in minutes."""
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            uh_params={"n": 3.0, "k": 30.0, "k_unit": "min"},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)

        assert result.peak_discharge_m3s > 0

    def test_clark_model(self):
        """Test Clark model."""
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            tc_min=60.0,
            uh_model="clark",
            uh_params={"r": 30.0},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)

        assert result.peak_discharge_m3s > 0
        assert result.hydrograph is not None

    def test_snyder_model(self):
        """Test Snyder model."""
        generator = HydrographGenerator(
            area_km2=100.0,
            cn=72,
            uh_model="snyder",
            uh_params={"L_km": 15.0, "Lc_km": 8.0},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=30.0)

        assert result.peak_discharge_m3s > 0
        assert result.hydrograph is not None

    def test_snyder_model_with_coefficients(self):
        """Test Snyder model with custom coefficients."""
        generator = HydrographGenerator(
            area_km2=100.0,
            cn=72,
            uh_model="snyder",
            uh_params={"L_km": 15.0, "Lc_km": 8.0, "ct": 1.8, "cp": 0.55},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=30.0)

        assert result.peak_discharge_m3s > 0

    def test_invalid_uh_model_raises(self):
        """Test that invalid model name raises error."""
        with pytest.raises(InvalidParameterError, match="uh_model must be one of"):
            HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0, uh_model="invalid")

    def test_nash_missing_n_raises(self):
        """Test that Nash model without n parameter raises error."""
        with pytest.raises(InvalidParameterError, match="'n' parameter"):
            HydrographGenerator(
                area_km2=45.0, cn=72, uh_model="nash", uh_params={"k": 0.5}
            )

    def test_nash_missing_k_raises(self):
        """Test that Nash model without k parameter raises error."""
        with pytest.raises(InvalidParameterError, match="'k' parameter"):
            HydrographGenerator(
                area_km2=45.0, cn=72, uh_model="nash", uh_params={"n": 3.0}
            )

    def test_clark_missing_r_raises(self):
        """Test that Clark model without r parameter raises error."""
        with pytest.raises(InvalidParameterError, match="'r' parameter"):
            HydrographGenerator(
                area_km2=45.0, cn=72, tc_min=60.0, uh_model="clark", uh_params={}
            )

    def test_clark_without_tc_raises(self):
        """Test that Clark model without tc_min raises error."""
        with pytest.raises(InvalidParameterError, match="tc_min is required"):
            HydrographGenerator(
                area_km2=45.0, cn=72, uh_model="clark", uh_params={"r": 30.0}
            )

    def test_snyder_missing_L_raises(self):
        """Test that Snyder model without L_km raises error."""
        with pytest.raises(InvalidParameterError, match="'L_km' parameter"):
            HydrographGenerator(
                area_km2=100.0,
                cn=72,
                uh_model="snyder",
                uh_params={"Lc_km": 8.0},
            )

    def test_snyder_missing_Lc_raises(self):
        """Test that Snyder model without Lc_km raises error."""
        with pytest.raises(InvalidParameterError, match="'Lc_km' parameter"):
            HydrographGenerator(
                area_km2=100.0,
                cn=72,
                uh_model="snyder",
                uh_params={"L_km": 15.0},
            )

    def test_scs_without_tc_raises(self):
        """Test that SCS model without tc_min raises error."""
        with pytest.raises(InvalidParameterError, match="tc_min is required"):
            HydrographGenerator(area_km2=45.0, cn=72, uh_model="scs")

    def test_model_name_case_insensitive(self):
        """Test that model name is case insensitive."""
        generator_lower = HydrographGenerator(
            area_km2=45.0, cn=72, tc_min=90.0, uh_model="scs"
        )
        generator_upper = HydrographGenerator(
            area_km2=45.0, cn=72, tc_min=90.0, uh_model="SCS"
        )
        generator_mixed = HydrographGenerator(
            area_km2=45.0, cn=72, tc_min=90.0, uh_model="Scs"
        )

        assert generator_lower.uh_model == "scs"
        assert generator_upper.uh_model == "scs"
        assert generator_mixed.uh_model == "scs"

    def test_uh_result_populated_scs(self):
        """Test unit_hydrograph_result is populated for SCS model."""
        generator = HydrographGenerator(
            area_km2=45.0, cn=72, tc_min=90.0, uh_model="scs"
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)
        assert result.unit_hydrograph_result is not None
        assert hasattr(result.unit_hydrograph_result, "ordinates_m3s")

    def test_uh_result_populated_nash(self):
        """Test unit_hydrograph_result is populated for Nash model."""
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            uh_model="nash",
            uh_params={"n": 3.0, "k": 0.5},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)
        assert result.unit_hydrograph_result is not None
        assert hasattr(result.unit_hydrograph_result, "ordinates_m3s")

    def test_uh_result_populated_clark(self):
        """Test unit_hydrograph_result is populated for Clark model."""
        generator = HydrographGenerator(
            area_km2=45.0,
            cn=72,
            tc_min=60.0,
            uh_model="clark",
            uh_params={"r": 30.0},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=10.0)
        assert result.unit_hydrograph_result is not None
        assert hasattr(result.unit_hydrograph_result, "ordinates_m3s")

    def test_uh_result_populated_snyder(self):
        """Test unit_hydrograph_result is populated for Snyder model."""
        generator = HydrographGenerator(
            area_km2=100.0,
            cn=72,
            uh_model="snyder",
            uh_params={"L_km": 15.0, "Lc_km": 8.0},
        )
        result = generator.generate([5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=30.0)
        assert result.unit_hydrograph_result is not None
        assert hasattr(result.unit_hydrograph_result, "ordinates_m3s")


class TestHydrographGeneratorSnyderDuration:
    """The convolution needs the Snyder unit hydrograph of D = the time step.

    The discrete convolution takes the unit hydrograph as the response to 1 mm of
    effective precipitation falling in one time step. Snyder (1938; HEC-HMS Technical
    Reference Manual) gives the hydrograph of the standard duration tD = tL / 5.5 and
    corrects it for another duration D: tLR = tL + 0.25 (D - tD), tpR = tLR + D / 2,
    qpR = qp tL / tLR. The generator used the standard one whatever the step was.
    """

    AREA, L_KM, LC_KM = 45.0, 12.0, 6.0

    @pytest.fixture
    def storm(self):
        """A beta storm of 50 mm in 120 min in 5-minute steps."""
        return BetaHietogram().generate(
            total_mm=50.0, duration_min=120.0, timestep_min=5.0
        )

    @pytest.fixture
    def generator(self):
        return HydrographGenerator(
            area_km2=self.AREA,
            cn=72,
            uh_model="snyder",
            uh_params={"L_km": self.L_KM, "Lc_km": self.LC_KM},
        )

    def test_the_unit_hydrograph_is_the_one_for_the_time_step(self, generator, storm):
        """Review case: tL = 324.7 min, tD = 59.0 min, step 5 min.

        The unit hydrograph had tp = 354.2 min and a peak of 1.379 m3/s/mm (the
        values for D = tD = 59 min); for D = 5 min tLR = 311.2 min, tpR = 313.7 min
        and the peak is 1.542 m3/s/mm.
        """
        unit = generator.generate(storm).unit_hydrograph_result

        assert unit.duration_min == 5.0
        assert unit.standard_duration_min == pytest.approx(59.03, abs=0.01)
        assert unit.adjusted_lag_time_min == pytest.approx(311.16, abs=0.01)
        assert unit.time_to_peak_min == pytest.approx(313.66, abs=0.01)
        assert unit.peak_discharge_m3s == pytest.approx(1.5424, abs=1e-4)

    def test_the_peak_of_the_hydrograph_rises_and_comes_earlier(self, generator, storm):
        """Qmax 9.76 m3/s at 405 min -> 10.90 m3/s at 365 min (+11.8 %)."""
        result = generator.generate(storm)
        standard = SnyderUH(self.AREA, self.L_KM, self.LC_KM).generate(timestep_min=5.0)
        before = convolve_discrete(
            result.effective_precip_mm, standard.ordinates_m3s, 5.0
        )

        assert standard.time_to_peak_min == pytest.approx(354.19, abs=0.01)
        assert standard.peak_discharge_m3s == pytest.approx(1.3793, abs=1e-4)
        assert before.peak_discharge_m3s == pytest.approx(9.7556, abs=1e-4)
        assert before.time_to_peak_min == 405.0
        assert result.peak_discharge_m3s == pytest.approx(10.9023, abs=1e-4)
        assert result.time_to_peak_min == 365.0
        assert result.peak_discharge_m3s / before.peak_discharge_m3s == pytest.approx(
            1.1175, abs=1e-4
        )

    def test_the_volume_is_the_effective_depth_over_the_area(self, generator, storm):
        """The corrected unit hydrograph still holds 1 mm: the runoff is conserved."""
        result = generator.generate(storm)

        assert result.hydrograph.total_volume_m3 == pytest.approx(
            result.total_effective_mm * self.AREA * 1000.0, rel=1e-9
        )

    def test_a_step_equal_to_the_standard_duration_changes_nothing(self, generator):
        """For D = tD the correction vanishes: tLR = tL, the standard hydrograph."""
        snyder = SnyderUH(self.AREA, self.L_KM, self.LC_KM)
        step = snyder.standard_duration_min

        unit = generator.generate(
            [4.0, 12.0, 20.0, 9.0, 3.0], timestep_min=step
        ).unit_hydrograph_result

        standard = snyder.generate(timestep_min=step)
        assert unit.duration_min == pytest.approx(step)
        assert unit.adjusted_lag_time_min == pytest.approx(unit.lag_time_min)
        np.testing.assert_allclose(unit.ordinates_m3s, standard.ordinates_m3s)

    @pytest.mark.parametrize("step", [5.0, 15.0, 60.0, 120.0])
    def test_the_unit_hydrograph_follows_the_time_step(self, generator, step):
        """The unit hydrograph is that of the step, whatever the step is."""
        unit = generator.generate(
            [5.0, 10.0, 15.0, 10.0, 5.0], timestep_min=step
        ).unit_hydrograph_result
        expected = SnyderUH(self.AREA, self.L_KM, self.LC_KM).generate(
            timestep_min=step, duration_min=step
        )

        assert unit.duration_min == step
        np.testing.assert_allclose(unit.ordinates_m3s, expected.ordinates_m3s)
        # the longer the rainfall of the unit hydrograph, the lower and later its peak
        assert unit.time_to_peak_min == pytest.approx(expected.time_to_peak_min)

    def test_other_models_do_not_take_a_duration(self):
        """The SCS unit hydrograph is generated for the step as before."""
        generator = HydrographGenerator(area_km2=45.0, cn=72, tc_min=90.0)
        result = generator.generate([5.0, 10.0, 15.0], timestep_min=10.0)

        expected = SCSUnitHydrograph(area_km2=45.0, tc_min=90.0).generate(10.0)
        np.testing.assert_allclose(
            result.unit_hydrograph_result.ordinates_m3s, expected.ordinates_m3s
        )


class TestRunoffImport:
    """Test module imports."""

    def test_import_all_classes(self):
        """Test that all classes can be imported."""
        from hydrolog.runoff import (
            AMC,
            SCSCN,
            HydrographGenerator,
            SCSUnitHydrograph,
            convolve_discrete,
        )

        assert HydrographGenerator is not None
        assert SCSCN is not None
        assert AMC is not None
        assert SCSUnitHydrograph is not None
        assert convolve_discrete is not None
