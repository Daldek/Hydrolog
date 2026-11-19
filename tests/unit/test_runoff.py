"""Tests for runoff generation module.

The SCS unit hydrograph and the convolution are tested against their specs in
``test_formulas_unit_hydrographs.py``.
"""

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.precipitation import BetaHietogram, BlockHietogram
from hydrolog.runoff import (
    AMC,
    HydrographGenerator,
    HydrographResult,
    SCSUnitHydrograph,
    SnyderUH,
    convolve_discrete,
)


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

        The unit hydrograph had tp = 354.2 min (the value for D = tD = 59 min); for
        D = 5 min tLR = 311.2 min, tpR = 313.7 min and the peak is
        qpR = 0.275 Cp A / tLR = 1.432 m3/s/mm.
        """
        unit = generator.generate(storm).unit_hydrograph_result

        assert unit.duration_min == 5.0
        assert unit.standard_duration_min == pytest.approx(59.03, abs=0.01)
        assert unit.adjusted_lag_time_min == pytest.approx(311.16, abs=0.01)
        assert unit.time_to_peak_min == pytest.approx(313.66, abs=0.01)
        assert unit.peak_discharge_m3s == pytest.approx(1.4317, abs=2e-4)

    def test_the_peak_of_the_hydrograph_rises_and_comes_earlier(self, generator, storm):
        """Qmax 9.71 m3/s at 405 min -> 10.12 m3/s at 365 min (+4.3 %)."""
        result = generator.generate(storm)
        standard = SnyderUH(self.AREA, self.L_KM, self.LC_KM).generate(timestep_min=5.0)
        before = convolve_discrete(
            result.effective_precip_mm, standard.ordinates_m3s, 5.0
        )

        assert standard.time_to_peak_min == pytest.approx(354.19, abs=0.01)
        assert standard.peak_discharge_m3s == pytest.approx(1.3723, abs=1e-4)
        assert before.peak_discharge_m3s == pytest.approx(9.7053, abs=1e-4)
        assert before.time_to_peak_min == 405.0
        assert result.peak_discharge_m3s == pytest.approx(10.1242, abs=1e-4)
        assert result.time_to_peak_min == 365.0
        assert result.peak_discharge_m3s / before.peak_discharge_m3s == pytest.approx(
            1.0432, abs=1e-4
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
