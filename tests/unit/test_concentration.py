"""Tests for time of concentration calculations."""

import pytest

from hydrolog.time import ConcentrationTime
from hydrolog.exceptions import InvalidParameterError


class TestKirpich:
    """Tests for Kirpich formula."""

    def test_kirpich_typical_values(self):
        """Test Kirpich formula with typical watershed parameters."""
        # Arrange
        length_km = 8.2
        slope_m_per_m = 0.023

        # Act
        tc = ConcentrationTime.kirpich(length_km=length_km, slope_m_per_m=slope_m_per_m)

        # Assert - tc [h] = 0.0663 * 8.2^0.77 * 0.023^(-0.385) = ~1.43 h = ~86 min
        assert 80.0 < tc < 92.0

    def test_kirpich_known_value(self):
        """Test Kirpich formula against hand-calculated value."""
        # tc [h] = 0.0663 * L^0.77 * S^(-0.385)
        # tc [h] = 0.0663 * 1.0^0.77 * 0.01^(-0.385)
        # tc [h] = 0.0663 * 1.0 * 5.891 = 0.39 h = 23.4 min
        length_km = 1.0
        slope_m_per_m = 0.01

        tc = ConcentrationTime.kirpich(length_km=length_km, slope_m_per_m=slope_m_per_m)

        assert abs(tc - 23.4) < 1.0

    def test_kirpich_steep_slope(self):
        """Test that steeper slope gives shorter tc."""
        length_km = 5.0
        tc_gentle = ConcentrationTime.kirpich(length_km=length_km, slope_m_per_m=0.01)
        tc_steep = ConcentrationTime.kirpich(length_km=length_km, slope_m_per_m=0.05)

        assert tc_steep < tc_gentle

    def test_kirpich_longer_channel(self):
        """Test that longer channel gives longer tc."""
        slope_m_per_m = 0.02
        tc_short = ConcentrationTime.kirpich(length_km=2.0, slope_m_per_m=slope_m_per_m)
        tc_long = ConcentrationTime.kirpich(length_km=8.0, slope_m_per_m=slope_m_per_m)

        assert tc_long > tc_short

    def test_kirpich_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.kirpich(length_km=0, slope_m_per_m=0.02)

    def test_kirpich_negative_length_raises(self):
        """Test that negative length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.kirpich(length_km=-1.0, slope_m_per_m=0.02)

    def test_kirpich_zero_slope_raises(self):
        """Test that zero slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.kirpich(length_km=1.0, slope_m_per_m=0)

    def test_kirpich_negative_slope_raises(self):
        """Test that negative slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.kirpich(length_km=1.0, slope_m_per_m=-0.01)


class TestNRCS:
    """Tests for NRCS equation."""

    def test_nrcs_typical_values(self):
        """Test SCS Lag equation with typical watershed parameters."""
        # Arrange
        length_km = 8.2
        slope_m_per_m = 0.023
        cn = 72

        # Act
        tc = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=slope_m_per_m, cn=cn
        )

        # Assert - SCS Lag (metric) gives ~363 min for these parameters
        assert 350.0 < tc < 380.0

    def test_nrcs_higher_cn_gives_shorter_tc(self):
        """Test that higher CN (less retention) gives shorter tc."""
        length_km = 5.0
        slope_m_per_m = 0.03

        tc_low_cn = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=slope_m_per_m, cn=60
        )
        tc_high_cn = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=slope_m_per_m, cn=85
        )

        assert tc_high_cn < tc_low_cn

    def test_nrcs_cn_100(self):
        """Test SCS Lag with CN=100 (no retention)."""
        tc = ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=100)

        # Should still return a positive value
        assert tc > 0

    def test_nrcs_steeper_slope_shorter_tc(self):
        """Test that steeper slope gives shorter tc."""
        length_km = 5.0
        cn = 75

        tc_gentle = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=0.01, cn=cn
        )
        tc_steep = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=0.05, cn=cn
        )

        assert tc_steep < tc_gentle

    def test_nrcs_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.nrcs(length_km=0, slope_m_per_m=0.02, cn=75)

    def test_nrcs_negative_slope_raises(self):
        """Test that negative slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=-0.02, cn=75)

    def test_nrcs_cn_too_low_raises(self):
        """Test that CN < 1 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="cn must be in range 1-100"):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=0)

    def test_nrcs_cn_too_high_raises(self):
        """Test that CN > 100 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="cn must be in range 1-100"):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=101)


class TestGiandotti:
    """Tests for Giandotti formula."""

    def test_giandotti_typical_values(self):
        """Test Giandotti formula with typical watershed parameters."""
        # Arrange
        area_km2 = 45.0
        length_km = 12.0
        elevation_diff_m = 350.0

        # Act
        tc = ConcentrationTime.giandotti(
            area_km2=area_km2,
            length_km=length_km,
            elevation_diff_m=elevation_diff_m,
        )

        # Assert - Giandotti gives ~180 min for these parameters
        assert 170.0 < tc < 190.0

    def test_giandotti_known_value(self):
        """Test Giandotti formula against hand-calculated value."""
        # tc [h] = (4 * sqrt(A) + 1.5 * L) / (0.8 * sqrt(H))
        # tc [h] = (4 * sqrt(100) + 1.5 * 15) / (0.8 * sqrt(400))
        # tc [h] = (4 * 10 + 22.5) / (0.8 * 20)
        # tc [h] = 62.5 / 16 = 3.906 h = 234.4 min
        area_km2 = 100.0
        length_km = 15.0
        elevation_diff_m = 400.0

        tc = ConcentrationTime.giandotti(
            area_km2=area_km2,
            length_km=length_km,
            elevation_diff_m=elevation_diff_m,
        )

        assert abs(tc - 234.4) < 1.0

    def test_giandotti_larger_area_longer_tc(self):
        """Test that larger area gives longer tc."""
        length_km = 10.0
        elevation_diff_m = 300.0

        tc_small = ConcentrationTime.giandotti(
            area_km2=20.0, length_km=length_km, elevation_diff_m=elevation_diff_m
        )
        tc_large = ConcentrationTime.giandotti(
            area_km2=100.0, length_km=length_km, elevation_diff_m=elevation_diff_m
        )

        assert tc_large > tc_small

    def test_giandotti_higher_elevation_diff_shorter_tc(self):
        """Test that higher elevation difference gives shorter tc."""
        area_km2 = 50.0
        length_km = 12.0

        tc_low = ConcentrationTime.giandotti(
            area_km2=area_km2, length_km=length_km, elevation_diff_m=200.0
        )
        tc_high = ConcentrationTime.giandotti(
            area_km2=area_km2, length_km=length_km, elevation_diff_m=500.0
        )

        assert tc_high < tc_low

    def test_giandotti_zero_area_raises(self):
        """Test that zero area raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            ConcentrationTime.giandotti(
                area_km2=0, length_km=10.0, elevation_diff_m=300.0
            )

    def test_giandotti_negative_length_raises(self):
        """Test that negative length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.giandotti(
                area_km2=50.0, length_km=-10.0, elevation_diff_m=300.0
            )

    def test_giandotti_zero_elevation_raises(self):
        """Test that zero elevation difference raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="elevation_diff_m must be positive"
        ):
            ConcentrationTime.giandotti(
                area_km2=50.0, length_km=10.0, elevation_diff_m=0
            )


class TestFAA:
    """Tests for FAA method."""

    def test_faa_typical_values(self):
        """Test FAA method with typical parameters."""
        # tc = 22.213 * (1.1 - 0.6) * 0.15^0.5 / 0.02^(1/3)
        # tc = 22.213 * 0.5 * 0.38730 / 0.27144
        # tc = 22.213 * 0.5 * 1.42693
        # tc ≈ 15.85 min
        tc = ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.6)

        assert abs(tc - 15.85) < 0.1

    def test_faa_known_value(self):
        """Test FAA method against hand-calculated cross-reference value."""
        # C=0.9, L=1000 ft = 0.30480 km, S=0.006
        # tc = 22.213 * (1.1 - 0.9) * 0.30480^0.5 / 0.006^(1/3)
        # tc = 22.213 * 0.2 * 0.55209 / 0.18171
        # tc ≈ 13.50 min
        tc = ConcentrationTime.faa(
            length_km=0.30480, slope_m_per_m=0.006, runoff_coeff=0.9
        )

        assert abs(tc - 13.50) < 0.1

    def test_faa_higher_c_gives_shorter_tc(self):
        """Test that higher runoff coefficient gives shorter tc."""
        tc_low_c = ConcentrationTime.faa(
            length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.4
        )
        tc_high_c = ConcentrationTime.faa(
            length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.8
        )

        assert tc_high_c < tc_low_c

    def test_faa_longer_path_gives_longer_tc(self):
        """Test that longer flow path gives longer tc."""
        tc_short = ConcentrationTime.faa(
            length_km=0.10, slope_m_per_m=0.02, runoff_coeff=0.6
        )
        tc_long = ConcentrationTime.faa(
            length_km=0.50, slope_m_per_m=0.02, runoff_coeff=0.6
        )

        assert tc_long > tc_short

    def test_faa_steeper_slope_gives_shorter_tc(self):
        """Test that steeper slope gives shorter tc."""
        tc_gentle = ConcentrationTime.faa(
            length_km=0.15, slope_m_per_m=0.01, runoff_coeff=0.6
        )
        tc_steep = ConcentrationTime.faa(
            length_km=0.15, slope_m_per_m=0.05, runoff_coeff=0.6
        )

        assert tc_steep < tc_gentle

    def test_faa_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.faa(length_km=0, slope_m_per_m=0.02, runoff_coeff=0.6)

    def test_faa_negative_length_raises(self):
        """Test that negative length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.faa(length_km=-0.5, slope_m_per_m=0.02, runoff_coeff=0.6)

    def test_faa_zero_slope_raises(self):
        """Test that zero slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0, runoff_coeff=0.6)

    def test_faa_negative_slope_raises(self):
        """Test that negative slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=-0.02, runoff_coeff=0.6)

    def test_faa_c_zero_raises(self):
        """Test that runoff_coeff=0 raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="runoff_coeff must be in range"
        ):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0)

    def test_faa_c_negative_raises(self):
        """Test that negative runoff_coeff raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="runoff_coeff must be in range"
        ):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=-0.5)

    def test_faa_c_above_one_raises(self):
        """Test that runoff_coeff > 1 raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="runoff_coeff must be in range"
        ):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=1.5)

    def test_faa_c_one_valid(self):
        """Test that runoff_coeff=1.0 is valid (edge case)."""
        tc = ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=1.0)

        assert tc > 0


class TestKerby:
    """Tests for Kerby formula."""

    def test_kerby_typical_values(self):
        """Test Kerby formula with typical overland flow parameters."""
        # tc = 36.37 * (0.10 * 0.40)^0.467 * 0.008^(-0.2335)
        # tc ≈ 24.98 min
        tc = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.008, retardance=0.40
        )

        assert abs(tc - 24.98) < 0.5

    def test_kerby_known_value(self):
        """Test Kerby formula against hand-calculated cross-reference value."""
        # L=1000 ft (0.3048 km), N=0.40, S=0.01
        # tc = 36.37 * (0.3048 * 0.40)^0.467 * 0.01^(-0.2335)
        # = 36.37 * (0.12192)^0.467 * 0.01^(-0.2335)
        # = 36.37 * 0.3745 * 2.926
        # ≈ 39.90 min
        tc = ConcentrationTime.kerby(
            length_km=0.3048, slope_m_per_m=0.01, retardance=0.40
        )

        assert abs(tc - 39.90) < 0.1

    def test_kerby_higher_n_gives_longer_tc(self):
        """Test that rougher surface (higher N) gives longer tc."""
        tc_smooth = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.008, retardance=0.10
        )
        tc_rough = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.008, retardance=0.60
        )

        assert tc_rough > tc_smooth

    def test_kerby_longer_path_gives_longer_tc(self):
        """Test that longer overland flow path gives longer tc."""
        tc_short = ConcentrationTime.kerby(
            length_km=0.05, slope_m_per_m=0.008, retardance=0.40
        )
        tc_long = ConcentrationTime.kerby(
            length_km=0.30, slope_m_per_m=0.008, retardance=0.40
        )

        assert tc_long > tc_short

    def test_kerby_steeper_slope_gives_shorter_tc(self):
        """Test that steeper slope gives shorter tc."""
        tc_gentle = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.003, retardance=0.40
        )
        tc_steep = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.008, retardance=0.40
        )

        assert tc_steep < tc_gentle

    def test_kerby_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.kerby(length_km=0, slope_m_per_m=0.008, retardance=0.40)

    def test_kerby_negative_length_raises(self):
        """Test that negative length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.kerby(
                length_km=-0.1, slope_m_per_m=0.008, retardance=0.40
            )

    def test_kerby_zero_slope_raises(self):
        """Test that zero slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.kerby(length_km=0.10, slope_m_per_m=0, retardance=0.40)

    def test_kerby_negative_slope_raises(self):
        """Test that negative slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=-0.008, retardance=0.40
            )

    def test_kerby_zero_retardance_raises(self):
        """Test that zero retardance raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="retardance must be positive"):
            ConcentrationTime.kerby(length_km=0.10, slope_m_per_m=0.008, retardance=0)

    def test_kerby_negative_retardance_raises(self):
        """Test that negative retardance raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="retardance must be positive"):
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=0.008, retardance=-0.40
            )

    def test_kerby_low_slope_adjustment(self):
        """Test that low-slope adjustment is applied for S < 0.002."""
        # S=0.001 -> S_adj=0.0015 (adjusted)
        # Without adjustment: tc = 36.37 * (0.10*0.40)^0.467 * 0.001^(-0.2335) ≈ 40.59
        # With adjustment:    tc = 36.37 * (0.10*0.40)^0.467 * 0.0015^(-0.2335) ≈ 36.92
        tc = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.001, retardance=0.40
        )

        # The adjusted result (~36.92) should differ from unadjusted (~40.59)
        assert abs(tc - 36.92) < 0.5
        # Should NOT match unadjusted value
        assert abs(tc - 40.59) > 1.0

    def test_kerby_impervious_surface(self):
        """Test Kerby with smooth impervious surface (N=0.02)."""
        # N=0.02 should give short tc
        tc = ConcentrationTime.kerby(
            length_km=0.10, slope_m_per_m=0.008, retardance=0.02
        )

        # tc ≈ 6.17 min for impervious surface
        assert tc < 10.0
        assert tc > 0


class TestConcentrationTimeImport:
    """Test module imports."""

    def test_import_from_time_module(self):
        """Test that ConcentrationTime can be imported from hydrolog.time."""
        from hydrolog.time import ConcentrationTime as CT

        assert CT is not None
        assert hasattr(CT, "kirpich")
        assert hasattr(CT, "nrcs")
        assert hasattr(CT, "giandotti")
        assert hasattr(CT, "faa")
        assert hasattr(CT, "kerby")


class TestParameterRangeWarnings:
    """Tests for parameter range warnings."""

    def test_kirpich_warns_on_long_channel(self):
        """Test warning for length above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kirpich(length_km=100.0, slope_m_per_m=0.02)

    def test_kirpich_warns_on_small_slope(self):
        """Test warning for slope below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kirpich(length_km=5.0, slope_m_per_m=0.001)

    def test_kirpich_warns_on_large_slope(self):
        """Test warning for slope above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kirpich(length_km=5.0, slope_m_per_m=0.20)

    def test_kirpich_no_warning_in_range(self):
        """Test no warning when parameters are in typical range."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ConcentrationTime.kirpich(length_km=5.0, slope_m_per_m=0.03)

    def test_nrcs_warns_on_low_cn(self):
        """Test warning for CN below recommended range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=45)

    def test_nrcs_warns_on_high_cn(self):
        """Test warning for CN above recommended range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=98)

    def test_nrcs_warns_on_long_length(self):
        """Test warning for length above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.nrcs(length_km=50.0, slope_m_per_m=0.02, cn=72)

    def test_nrcs_no_warning_in_range(self):
        """Test no warning when parameters are in typical range."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0.02, cn=72)

    def test_giandotti_warns_on_small_area(self):
        """Test warning for area below recommended range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.giandotti(
                area_km2=50.0, length_km=10.0, elevation_diff_m=200.0
            )

    def test_giandotti_warns_on_small_length(self):
        """Test warning for length below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.giandotti(
                area_km2=200.0, length_km=0.5, elevation_diff_m=200.0
            )

    def test_giandotti_warns_on_small_elevation(self):
        """Test warning for elevation below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.giandotti(
                area_km2=200.0, length_km=15.0, elevation_diff_m=10.0
            )

    def test_giandotti_no_warning_in_range(self):
        """Test no warning when parameters are in typical range."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ConcentrationTime.giandotti(
                area_km2=200.0, length_km=15.0, elevation_diff_m=300.0
            )

    def test_faa_warns_on_long_length(self):
        """Test warning for length above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.faa(length_km=5.0, slope_m_per_m=0.02, runoff_coeff=0.6)

    def test_faa_warns_on_small_slope(self):
        """Test warning for slope below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.003, runoff_coeff=0.6)

    def test_faa_warns_on_large_slope(self):
        """Test warning for slope above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.15, runoff_coeff=0.6)

    def test_faa_warns_on_low_c(self):
        """Test warning for runoff coefficient below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.05)

    def test_faa_warns_on_high_c(self):
        """Test warning for runoff coefficient above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.99)

    def test_faa_no_warning_in_range(self):
        """Test no warning when parameters are in typical range."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ConcentrationTime.faa(length_km=0.15, slope_m_per_m=0.02, runoff_coeff=0.6)

    def test_kerby_warns_on_long_length(self):
        """Test warning for length above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kerby(
                length_km=0.50, slope_m_per_m=0.005, retardance=0.40
            )

    def test_kerby_warns_on_small_slope(self):
        """Test warning for slope below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=0.0005, retardance=0.40
            )

    def test_kerby_warns_on_large_slope(self):
        """Test warning for slope above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kerby(length_km=0.10, slope_m_per_m=0.02, retardance=0.40)

    def test_kerby_warns_on_low_n(self):
        """Test warning for retardance below typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=0.005, retardance=0.01
            )

    def test_kerby_warns_on_high_n(self):
        """Test warning for retardance above typical range."""
        with pytest.warns(UserWarning, match="outside typical range"):
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=0.005, retardance=0.90
            )

    def test_kerby_no_warning_in_range(self):
        """Test no warning when parameters are in typical range."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ConcentrationTime.kerby(
                length_km=0.10, slope_m_per_m=0.005, retardance=0.40
            )
