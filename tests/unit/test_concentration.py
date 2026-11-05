"""Tests for time of concentration calculations."""

import warnings

import pytest

from hydrolog._warnings import OutsideTypicalRange
from hydrolog.exceptions import InvalidParameterError
from hydrolog.time import ConcentrationTime


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

    def test_nrcs_known_value(self):
        """Test NRCS formula against hand-calculated value."""
        # L=1.0 km, S=0.02, CN=75
        # retention_mm = (25400/75) - 254 = 338.667 - 254 = 84.667 mm
        # length_m = 1000 m, slope_percent = 2.0
        # tc = 0.01416 * 1000^0.8 * (84.667+25.4)^0.7 * 2.0^(-0.5)
        # 1000^0.8 = 251.189
        # (84.667+25.4)^0.7 = (110.067)^0.7 = 26.853
        # 2.0^(-0.5) = 0.70711
        # tc = 0.01416 * 251.189 * 26.853 * 0.70711
        # tc ≈ 67.6 min
        tc = ConcentrationTime.nrcs(length_km=1.0, slope_m_per_m=0.02, cn=75)

        assert abs(tc - 67.6) < 1.0

    def test_nrcs_longer_path_gives_longer_tc(self):
        """Test that longer flow path gives longer tc."""
        cn = 75
        slope = 0.02

        tc_short = ConcentrationTime.nrcs(length_km=2.0, slope_m_per_m=slope, cn=cn)
        tc_long = ConcentrationTime.nrcs(length_km=10.0, slope_m_per_m=slope, cn=cn)

        assert tc_long > tc_short

    def test_nrcs_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.nrcs(length_km=0, slope_m_per_m=0.02, cn=75)

    def test_nrcs_negative_length_raises(self):
        """Test that negative length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.nrcs(length_km=-1.0, slope_m_per_m=0.02, cn=75)

    def test_nrcs_zero_slope_raises(self):
        """Test that zero slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_m_per_m must be positive"
        ):
            ConcentrationTime.nrcs(length_km=5.0, slope_m_per_m=0, cn=75)

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

    def test_giandotti_longer_channel_longer_tc(self):
        """Test that longer channel gives longer tc."""
        area_km2 = 50.0
        elevation_diff_m = 300.0

        tc_short = ConcentrationTime.giandotti(
            area_km2=area_km2, length_km=5.0, elevation_diff_m=elevation_diff_m
        )
        tc_long = ConcentrationTime.giandotti(
            area_km2=area_km2, length_km=20.0, elevation_diff_m=elevation_diff_m
        )

        assert tc_long > tc_short

    def test_giandotti_zero_area_raises(self):
        """Test that zero area raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            ConcentrationTime.giandotti(
                area_km2=0, length_km=10.0, elevation_diff_m=300.0
            )

    def test_giandotti_negative_area_raises(self):
        """Test that negative area raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            ConcentrationTime.giandotti(
                area_km2=-50.0, length_km=10.0, elevation_diff_m=300.0
            )

    def test_giandotti_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_km must be positive"):
            ConcentrationTime.giandotti(
                area_km2=50.0, length_km=0, elevation_diff_m=300.0
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

    def test_giandotti_negative_elevation_raises(self):
        """Test that negative elevation difference raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="elevation_diff_m must be positive"
        ):
            ConcentrationTime.giandotti(
                area_km2=50.0, length_km=10.0, elevation_diff_m=-300.0
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


class TestKerbyKirpich:
    """Tests for Kerby-Kirpich composite method."""

    def test_kerby_kirpich_typical_values(self):
        """Kerby on the overland segment plus Kirpich on the rest of the flow path."""
        ov_length = 0.25
        ov_slope = 0.008
        retardance = 0.40
        fp_length = 5.25
        fp_slope = 0.005

        tc = ConcentrationTime.kerby_kirpich(
            overland_length_km=ov_length,
            overland_slope_m_per_m=ov_slope,
            retardance=retardance,
            flow_path_length_km=fp_length,
            flow_path_slope_m_per_m=fp_slope,
        )

        t_overland = ConcentrationTime.kerby(ov_length, ov_slope, retardance)
        t_channel = ConcentrationTime.kirpich(fp_length - ov_length, fp_slope)

        assert abs(tc - (t_overland + t_channel)) < 0.01

    def test_kerby_kirpich_known_value(self):
        """Test Kerby-Kirpich against hand-calculated reference value."""
        tc = ConcentrationTime.kerby_kirpich(
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            retardance=0.40,
            flow_path_length_km=5.25,
            flow_path_slope_m_per_m=0.005,
        )

        # t_overland ≈ 35.1 min, t_channel (5.0 km) ≈ 108.9 min → total ≈ 144.0 min
        assert 135.0 < tc < 146.0

    def test_kerby_kirpich_equals_sum_of_parts(self):
        """Verify composite equals kerby() + kirpich() on the channel segment."""
        ov_length = 0.15
        ov_slope = 0.005
        retardance = 0.20
        fp_length = 3.15
        fp_slope = 0.010

        tc_composite = ConcentrationTime.kerby_kirpich(
            overland_length_km=ov_length,
            overland_slope_m_per_m=ov_slope,
            retardance=retardance,
            flow_path_length_km=fp_length,
            flow_path_slope_m_per_m=fp_slope,
        )

        t_overland = ConcentrationTime.kerby(ov_length, ov_slope, retardance)
        t_channel = ConcentrationTime.kirpich(3.0, fp_slope)

        assert abs(tc_composite - (t_overland + t_channel)) < 0.01

    def test_kerby_kirpich_channel_low_slope_adjustment(self):
        """Test low-slope adjustment is applied to the flow path slope."""
        fp_slope = 0.001  # Below threshold → adjusted to 0.0015

        tc = ConcentrationTime.kerby_kirpich(
            overland_length_km=0.10,
            overland_slope_m_per_m=0.005,
            retardance=0.40,
            flow_path_length_km=5.10,
            flow_path_slope_m_per_m=fp_slope,
        )

        # Compute expected: kerby uses 0.005 (no adj), kirpich uses 0.0015
        t_overland = ConcentrationTime.kerby(0.10, 0.005, 0.40)
        t_channel_adj = ConcentrationTime.kirpich(5.0, 0.0015)
        t_channel_raw = ConcentrationTime.kirpich(5.0, 0.001)

        # Should match the adjusted calculation
        assert abs(tc - (t_overland + t_channel_adj)) < 0.01
        # Should differ from raw (unadjusted) kirpich
        assert abs(tc - (t_overland + t_channel_raw)) > 1.0

    def test_kerby_kirpich_overland_dominates(self):
        """Flow path barely longer than the overland segment → about kerby alone."""
        ov_length = 0.30
        ov_slope = 0.005
        retardance = 0.60
        fp_length = 0.31  # Channel segment of 0.01 km
        fp_slope = 0.05

        tc = ConcentrationTime.kerby_kirpich(
            overland_length_km=ov_length,
            overland_slope_m_per_m=ov_slope,
            retardance=retardance,
            flow_path_length_km=fp_length,
            flow_path_slope_m_per_m=fp_slope,
        )

        t_overland = ConcentrationTime.kerby(ov_length, ov_slope, retardance)

        # Channel contribution should be negligible
        assert abs(tc - t_overland) / t_overland < 0.05

    def test_kerby_kirpich_channel_dominates(self):
        """Very short overland → result approximately equals kirpich alone."""
        ov_length = 0.01  # Very short overland
        ov_slope = 0.008
        retardance = 0.10
        fp_length = 10.0
        fp_slope = 0.010

        tc = ConcentrationTime.kerby_kirpich(
            overland_length_km=ov_length,
            overland_slope_m_per_m=ov_slope,
            retardance=retardance,
            flow_path_length_km=fp_length,
            flow_path_slope_m_per_m=fp_slope,
        )

        t_channel = ConcentrationTime.kirpich(fp_length, fp_slope)

        # Overland contribution should be negligible
        assert abs(tc - t_channel) / t_channel < 0.05

    @pytest.mark.parametrize(
        ("slope_ov", "slope_fp", "hydrolog_min", "published_min"),
        [
            # Roussel et al. (2005), TxDOT 0-4696-2, supplement; TxDOT Hydraulic
            # Design Manual, ch. 4, section 11: 50 ft of drop over the mile
            (0.02, 50.0 / 5280.0, 56.5, 57.0),
            # Cleveland et al. (2012), TxDOT 0-6382-P1, low-slope example: 1.1 ft
            # over the mile, both slopes below 0.002 and offset by 0.0005
            (0.0003, 1.1 / 5280.0, 138.9, 140.0),
        ],
    )
    def test_kerby_kirpich_reproduces_the_published_examples(
        self, slope_ov, slope_fp, hydrolog_min, published_min
    ):
        """The worked examples of the method's sources: 500 ft of overland flow on
        pasture (N = 0.40) at the head of a flow path of one mile (5280 ft) from the
        divide to the outlet.

        Roussel, M.C., Thompson, D.B., Fang, X., Cleveland, T.G., and Garcia, C.A.
        (2005). Time-parameter estimation for applicable Texas watersheds. TxDOT
        Research Report 0-4696-2, supplement; Texas Department of Transportation
        (2019), Hydraulic Design Manual, ch. 4, section 11: about 25 + 32 = 57 min.

        Cleveland, T.G., Thompson, D.B., Fang, X., and Li, M.-H. (2012). Guidance
        for estimation of time of concentration in Texas for low-slope conditions.
        TxDOT Product 0-6382-P1: about 53 + 87 = 140 min.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OutsideTypicalRange)
            tc = ConcentrationTime.kerby_kirpich(
                overland_length_km=0.1524,
                overland_slope_m_per_m=slope_ov,
                retardance=0.40,
                flow_path_length_km=1.609344,
                flow_path_slope_m_per_m=slope_fp,
            )

        assert tc == pytest.approx(hydrolog_min, abs=1.0)
        assert tc == pytest.approx(published_min, abs=2.0)

    @pytest.mark.parametrize("flow_path_length_km", [0.25, 0.20])
    def test_kerby_kirpich_flow_path_not_longer_than_overland_raises(
        self, flow_path_length_km
    ):
        """The flow path includes the overland segment: it must be longer."""
        with pytest.raises(InvalidParameterError) as excinfo:
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=flow_path_length_km,
                flow_path_slope_m_per_m=0.005,
            )

        assert excinfo.value.details == {
            "option": "flow_path_length_km",
            "reason": "exclusive_minimum",
            "exclusive_minimum": 0.25,
            "value": flow_path_length_km,
        }

    def test_kerby_kirpich_zero_overland_length_raises(self):
        """Test that zero overland length raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="overland_length_km must be positive"
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_negative_overland_length_raises(self):
        """Test that negative overland length raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="overland_length_km must be positive"
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=-0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_zero_flow_path_length_raises(self):
        """Test that zero flow path length raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="flow_path_length_km must be positive"
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=0,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_negative_flow_path_length_raises(self):
        """Test that negative flow path length raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="flow_path_length_km must be positive"
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=-5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_zero_overland_slope_raises(self):
        """Test that zero overland slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError,
            match="overland_slope_m_per_m must be positive",
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_negative_overland_slope_raises(self):
        """Test that negative overland slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError,
            match="overland_slope_m_per_m must be positive",
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=-0.008,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_zero_flow_path_slope_raises(self):
        """Test that zero flow path slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError,
            match="flow_path_slope_m_per_m must be positive",
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0,
            )

    def test_kerby_kirpich_negative_flow_path_slope_raises(self):
        """Test that negative flow path slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError,
            match="flow_path_slope_m_per_m must be positive",
        ):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=-0.005,
            )

    def test_kerby_kirpich_zero_retardance_raises(self):
        """Test that zero retardance raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="retardance must be positive"):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=0,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )

    def test_kerby_kirpich_negative_retardance_raises(self):
        """Test that negative retardance raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="retardance must be positive"):
            ConcentrationTime.kerby_kirpich(
                overland_length_km=0.25,
                overland_slope_m_per_m=0.008,
                retardance=-0.40,
                flow_path_length_km=5.25,
                flow_path_slope_m_per_m=0.005,
            )


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
        assert hasattr(CT, "kerby_kirpich")


# Arguments of each formula inside every typical range of the method; a case replaces
# one of them.
INSIDE = {
    "kirpich": {"length_km": 5.0, "slope_m_per_m": 0.05},
    "nrcs": {"length_km": 5.0, "slope_m_per_m": 0.02, "cn": 72},
    "giandotti": {"area_km2": 200.0, "length_km": 15.0, "elevation_diff_m": 300.0},
    "faa": {"length_km": 0.15, "slope_m_per_m": 0.02, "runoff_coeff": 0.6},
    "kerby": {"length_km": 0.10, "slope_m_per_m": 0.005, "retardance": 0.40},
    "kerby_kirpich": {
        "overland_length_km": 0.10,
        "overland_slope_m_per_m": 0.005,
        "retardance": 0.40,
        "flow_path_length_km": 5.1,
        "flow_path_slope_m_per_m": 0.005,
    },
}


def range_warnings(method: str, parameter: str, value: float) -> list[dict]:
    """The details of the range warnings of a formula with one argument changed."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        getattr(ConcentrationTime, method)(**{**INSIDE[method], parameter: value})
    return [
        warning.message.details
        for warning in caught
        if isinstance(warning.message, OutsideTypicalRange)
    ]


class TestParameterRangeWarnings:
    """The typical ranges of the formulas, each from the data or the literature of its
    method: a value just outside a bound warns with the published bounds, a value on
    a bound (bounds are included) or inside does not."""

    @pytest.mark.parametrize(
        ("method", "parameter", "value", "minimum", "maximum"),
        [
            # Kirpich (1940): the slopes of his 7 Tennessee watersheds, 3-10 %
            ("kirpich", "slope_m_per_m", 0.0299, 0.03, 0.10),
            ("kirpich", "slope_m_per_m", 0.1001, 0.03, 0.10),
            # Mockus (1961): CN 50-95 in the lag equation
            ("nrcs", "cn", 49.9, 50.0, 95.0),
            ("nrcs", "cn", 95.1, 50.0, 95.0),
            # Giandotti (1934): basins of 170-70 000 km2
            ("giandotti", "area_km2", 169.9, 170.0, 70000.0),
            ("giandotti", "area_km2", 70000.1, 170.0, 70000.0),
            # FAA (1970), table I: C up to 0.95
            ("faa", "runoff_coeff", 0.951, 0.0, 0.95),
            # Kerby (1959): up to 1200 ft, slopes below 1 %, N 0.02-0.80
            ("kerby", "length_km", 0.367, 0.0, 0.366),
            ("kerby", "slope_m_per_m", 0.0101, 0.0, 0.01),
            ("kerby", "retardance", 0.0199, 0.02, 0.80),
            ("kerby", "retardance", 0.8001, 0.02, 0.80),
            # Kerby-Kirpich: Kerby's overland flow, the main channels (flow paths from
            # the divide) of 92 Texas watersheds (Roussel et al. 2005): 1.6-80 km,
            # slopes 0.002-0.02
            ("kerby_kirpich", "overland_length_km", 0.367, 0.0, 0.366),
            ("kerby_kirpich", "retardance", 0.0199, 0.02, 0.80),
            ("kerby_kirpich", "retardance", 0.8001, 0.02, 0.80),
            ("kerby_kirpich", "flow_path_length_km", 1.599, 1.6, 80.0),
            ("kerby_kirpich", "flow_path_length_km", 80.01, 1.6, 80.0),
            ("kerby_kirpich", "flow_path_slope_m_per_m", 0.00199, 0.002, 0.02),
            ("kerby_kirpich", "flow_path_slope_m_per_m", 0.0201, 0.002, 0.02),
        ],
    )
    def test_a_value_just_outside_a_range_warns_with_its_bounds(
        self, method, parameter, value, minimum, maximum
    ):
        assert range_warnings(method, parameter, value) == [
            {
                "method": method,
                "parameter": parameter,
                "field": parameter,
                "value": value,
                "minimum": minimum,
                "maximum": maximum,
            }
        ]

    @pytest.mark.parametrize(
        ("method", "parameter", "value"),
        [
            ("kirpich", "slope_m_per_m", 0.03),
            ("kirpich", "slope_m_per_m", 0.10),
            ("nrcs", "cn", 50),
            ("nrcs", "cn", 95),
            ("giandotti", "area_km2", 170.0),
            ("giandotti", "area_km2", 70000.0),
            ("faa", "runoff_coeff", 0.95),
            # no lower bound any more: 0.10 had no source
            ("faa", "runoff_coeff", 0.05),
            ("kerby", "length_km", 0.366),
            ("kerby", "slope_m_per_m", 0.01),
            ("kerby", "retardance", 0.02),
            ("kerby", "retardance", 0.80),
            # no lower bounds any more: 0.01 km and 0.001 had no source
            ("kerby", "length_km", 0.005),
            ("kerby", "slope_m_per_m", 0.0005),
            ("kerby_kirpich", "overland_length_km", 0.366),
            ("kerby_kirpich", "overland_length_km", 0.005),
            ("kerby_kirpich", "retardance", 0.02),
            ("kerby_kirpich", "retardance", 0.80),
            ("kerby_kirpich", "flow_path_length_km", 1.6),
            ("kerby_kirpich", "flow_path_length_km", 80.0),
            ("kerby_kirpich", "flow_path_slope_m_per_m", 0.002),
            ("kerby_kirpich", "flow_path_slope_m_per_m", 0.02),
        ],
    )
    def test_a_value_on_a_bound_does_not_warn(self, method, parameter, value):
        assert range_warnings(method, parameter, value) == []

    @pytest.mark.parametrize(
        ("method", "parameter", "value"),
        [
            # The former thresholds, which had no published source (2026-11-04)
            ("kirpich", "length_km", 100.0),  # was 0.001-80 km
            ("nrcs", "length_km", 50.0),  # was 0.03-30 km
            ("nrcs", "slope_m_per_m", 0.20),  # was 0.001-0.15
            ("giandotti", "length_km", 500.0),  # was 1-300 km
            ("giandotti", "elevation_diff_m", 5000.0),  # was 20-3000 m
            ("faa", "length_km", 5.0),  # was 0.015-3 km
            ("faa", "slope_m_per_m", 0.15),  # was 0.005-0.10
            ("kerby_kirpich", "overland_slope_m_per_m", 0.02),  # was 0.001-0.01
        ],
    )
    def test_a_removed_range_no_longer_warns(self, method, parameter, value):
        assert range_warnings(method, parameter, value) == []
