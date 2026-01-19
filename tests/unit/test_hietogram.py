"""Tests for hyetograph generation."""

import numpy as np
import pytest

from hydrolog.precipitation import (
    HietogramResult,
    BlockHietogram,
    TriangularHietogram,
    BetaHietogram,
)
from hydrolog.exceptions import InvalidParameterError


class TestHietogramResult:
    """Tests for HietogramResult dataclass."""

    def test_n_steps_property(self):
        """Test n_steps returns correct number of time steps."""
        result = HietogramResult(
            times_min=np.array([10.0, 20.0, 30.0]),
            intensities_mm=np.array([5.0, 5.0, 5.0]),
            total_mm=15.0,
            duration_min=30.0,
            timestep_min=10.0,
        )

        assert result.n_steps == 3

    def test_intensity_mm_per_h_property(self):
        """Test intensity_mm_per_h converts correctly."""
        result = HietogramResult(
            times_min=np.array([10.0, 20.0, 30.0]),
            intensities_mm=np.array([5.0, 10.0, 5.0]),
            total_mm=20.0,
            duration_min=30.0,
            timestep_min=10.0,
        )

        # 5 mm in 10 min = 30 mm/h, 10 mm in 10 min = 60 mm/h
        expected = np.array([30.0, 60.0, 30.0])
        np.testing.assert_array_almost_equal(result.intensity_mm_per_h, expected)


class TestBlockHietogram:
    """Tests for BlockHietogram (uniform distribution)."""

    def test_block_uniform_distribution(self):
        """Test that block hyetograph has uniform intensity."""
        hietogram = BlockHietogram()
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # All intensities should be equal
        assert np.allclose(result.intensities_mm, 5.0)
        assert result.n_steps == 6

    def test_block_total_preserved(self):
        """Test that total precipitation is preserved."""
        hietogram = BlockHietogram()
        result = hietogram.generate(total_mm=50.0, duration_min=100.0, timestep_min=5.0)

        assert np.isclose(result.intensities_mm.sum(), 50.0)

    def test_block_times_correct(self):
        """Test that time values are at end of each interval."""
        hietogram = BlockHietogram()
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        expected_times = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        np.testing.assert_array_almost_equal(result.times_min, expected_times)

    def test_block_result_attributes(self):
        """Test that result contains correct attributes."""
        hietogram = BlockHietogram()
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        assert result.total_mm == 30.0
        assert result.duration_min == 60.0
        assert result.timestep_min == 10.0

    def test_block_default_timestep(self):
        """Test default timestep of 5 minutes."""
        hietogram = BlockHietogram()
        result = hietogram.generate(total_mm=30.0, duration_min=60.0)

        assert result.timestep_min == 5.0
        assert result.n_steps == 12


class TestTriangularHietogram:
    """Tests for TriangularHietogram."""

    def test_triangular_peak_at_center(self):
        """Test triangular with peak at center."""
        hietogram = TriangularHietogram(peak_position=0.5)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be near the center
        peak_idx = np.argmax(result.intensities_mm)
        assert 2 <= peak_idx <= 3  # Center of 6 steps

    def test_triangular_peak_early(self):
        """Test triangular with peak early in storm."""
        hietogram = TriangularHietogram(peak_position=0.25)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be in first half
        peak_idx = np.argmax(result.intensities_mm)
        assert peak_idx < 3

    def test_triangular_peak_late(self):
        """Test triangular with peak late in storm."""
        hietogram = TriangularHietogram(peak_position=0.75)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be in second half
        peak_idx = np.argmax(result.intensities_mm)
        assert peak_idx >= 3

    def test_triangular_total_preserved(self):
        """Test that total precipitation is preserved."""
        hietogram = TriangularHietogram(peak_position=0.4)
        result = hietogram.generate(total_mm=50.0, duration_min=100.0, timestep_min=5.0)

        assert np.isclose(result.intensities_mm.sum(), 50.0)

    def test_triangular_invalid_peak_zero_raises(self):
        """Test that peak_position=0 raises error."""
        with pytest.raises(
            InvalidParameterError, match="peak_position must be in range"
        ):
            TriangularHietogram(peak_position=0.0)

    def test_triangular_invalid_peak_one_raises(self):
        """Test that peak_position=1 raises error."""
        with pytest.raises(
            InvalidParameterError, match="peak_position must be in range"
        ):
            TriangularHietogram(peak_position=1.0)

    def test_triangular_invalid_peak_negative_raises(self):
        """Test that negative peak_position raises error."""
        with pytest.raises(
            InvalidParameterError, match="peak_position must be in range"
        ):
            TriangularHietogram(peak_position=-0.5)


class TestBetaHietogram:
    """Tests for BetaHietogram."""

    def test_beta_early_peak(self):
        """Test Beta with early peak (alpha=2, beta=5)."""
        hietogram = BetaHietogram(alpha=2.0, beta=5.0)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be early (before center)
        peak_idx = np.argmax(result.intensities_mm)
        assert peak_idx < 3  # First half of 6 steps

    def test_beta_late_peak(self):
        """Test Beta with late peak (alpha=5, beta=2)."""
        hietogram = BetaHietogram(alpha=5.0, beta=2.0)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be late (after center)
        peak_idx = np.argmax(result.intensities_mm)
        assert peak_idx > 2  # Second half of 6 steps

    def test_beta_symmetric(self):
        """Test Beta with symmetric distribution (alpha=2, beta=2)."""
        hietogram = BetaHietogram(alpha=2.0, beta=2.0)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Peak should be near center
        peak_idx = np.argmax(result.intensities_mm)
        assert 2 <= peak_idx <= 3

    def test_beta_total_preserved(self):
        """Test that total precipitation is preserved."""
        hietogram = BetaHietogram(alpha=2.0, beta=5.0)
        result = hietogram.generate(total_mm=50.0, duration_min=100.0, timestep_min=5.0)

        assert np.isclose(result.intensities_mm.sum(), 50.0)

    def test_beta_invalid_alpha_zero_raises(self):
        """Test that alpha=0 raises error."""
        with pytest.raises(InvalidParameterError, match="alpha must be positive"):
            BetaHietogram(alpha=0.0, beta=5.0)

    def test_beta_invalid_alpha_negative_raises(self):
        """Test that negative alpha raises error."""
        with pytest.raises(InvalidParameterError, match="alpha must be positive"):
            BetaHietogram(alpha=-1.0, beta=5.0)

    def test_beta_invalid_beta_zero_raises(self):
        """Test that beta=0 raises error."""
        with pytest.raises(InvalidParameterError, match="beta must be positive"):
            BetaHietogram(alpha=2.0, beta=0.0)

    def test_beta_invalid_beta_negative_raises(self):
        """Test that negative beta raises error."""
        with pytest.raises(InvalidParameterError, match="beta must be positive"):
            BetaHietogram(alpha=2.0, beta=-1.0)

    def test_beta_edge_case_small_alpha(self):
        """Test Beta with very small alpha (peak at start)."""
        hietogram = BetaHietogram(alpha=0.5, beta=5.0)
        result = hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=10.0)

        # Should have highest intensity at start
        assert result.intensities_mm[0] > result.intensities_mm[-1]
        assert np.isclose(result.intensities_mm.sum(), 30.0)


class TestHietogramValidation:
    """Tests for parameter validation common to all hyetograms."""

    def test_zero_total_raises(self):
        """Test that zero total_mm raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(InvalidParameterError, match="total_mm must be positive"):
            hietogram.generate(total_mm=0, duration_min=60.0, timestep_min=10.0)

    def test_negative_total_raises(self):
        """Test that negative total_mm raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(InvalidParameterError, match="total_mm must be positive"):
            hietogram.generate(total_mm=-30.0, duration_min=60.0, timestep_min=10.0)

    def test_zero_duration_raises(self):
        """Test that zero duration_min raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(
            InvalidParameterError, match="duration_min must be positive"
        ):
            hietogram.generate(total_mm=30.0, duration_min=0, timestep_min=10.0)

    def test_negative_duration_raises(self):
        """Test that negative duration_min raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(
            InvalidParameterError, match="duration_min must be positive"
        ):
            hietogram.generate(total_mm=30.0, duration_min=-60.0, timestep_min=10.0)

    def test_zero_timestep_raises(self):
        """Test that zero timestep_min raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(
            InvalidParameterError, match="timestep_min must be positive"
        ):
            hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=0)

    def test_negative_timestep_raises(self):
        """Test that negative timestep_min raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(
            InvalidParameterError, match="timestep_min must be positive"
        ):
            hietogram.generate(total_mm=30.0, duration_min=60.0, timestep_min=-5.0)

    def test_timestep_exceeds_duration_raises(self):
        """Test that timestep > duration raises error."""
        hietogram = BlockHietogram()
        with pytest.raises(InvalidParameterError, match="timestep_min.*cannot exceed"):
            hietogram.generate(total_mm=30.0, duration_min=10.0, timestep_min=20.0)

    def test_triangular_validation(self):
        """Test that TriangularHietogram validates generate params."""
        hietogram = TriangularHietogram(peak_position=0.5)
        with pytest.raises(InvalidParameterError, match="total_mm must be positive"):
            hietogram.generate(total_mm=-10.0, duration_min=60.0, timestep_min=10.0)

    def test_beta_validation(self):
        """Test that BetaHietogram validates generate params."""
        hietogram = BetaHietogram(alpha=2.0, beta=5.0)
        with pytest.raises(
            InvalidParameterError, match="duration_min must be positive"
        ):
            hietogram.generate(total_mm=30.0, duration_min=-60.0, timestep_min=10.0)


class TestHietogramImport:
    """Test module imports."""

    def test_import_from_precipitation_module(self):
        """Test that classes can be imported from hydrolog.precipitation."""
        from hydrolog.precipitation import (
            HietogramResult,
            Hietogram,
            BlockHietogram,
            TriangularHietogram,
            BetaHietogram,
        )

        assert HietogramResult is not None
        assert Hietogram is not None
        assert BlockHietogram is not None
        assert TriangularHietogram is not None
        assert BetaHietogram is not None
