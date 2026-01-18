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


class TestSCSLag:
    """Tests for SCS Lag equation."""

    def test_scs_lag_typical_values(self):
        """Test SCS Lag equation with typical watershed parameters."""
        # Arrange
        length_m = 8200.0
        slope_percent = 2.3
        cn = 72

        # Act
        tc = ConcentrationTime.scs_lag(
            length_m=length_m, slope_percent=slope_percent, cn=cn
        )

        # Assert - SCS Lag (metric) gives ~363 min for these parameters
        assert 350.0 < tc < 380.0

    def test_scs_lag_higher_cn_gives_shorter_tc(self):
        """Test that higher CN (less retention) gives shorter tc."""
        length_m = 5000.0
        slope_percent = 3.0

        tc_low_cn = ConcentrationTime.scs_lag(
            length_m=length_m, slope_percent=slope_percent, cn=60
        )
        tc_high_cn = ConcentrationTime.scs_lag(
            length_m=length_m, slope_percent=slope_percent, cn=85
        )

        assert tc_high_cn < tc_low_cn

    def test_scs_lag_cn_100(self):
        """Test SCS Lag with CN=100 (no retention)."""
        tc = ConcentrationTime.scs_lag(length_m=5000.0, slope_percent=2.0, cn=100)

        # Should still return a positive value
        assert tc > 0

    def test_scs_lag_steeper_slope_shorter_tc(self):
        """Test that steeper slope gives shorter tc."""
        length_m = 5000.0
        cn = 75

        tc_gentle = ConcentrationTime.scs_lag(
            length_m=length_m, slope_percent=1.0, cn=cn
        )
        tc_steep = ConcentrationTime.scs_lag(
            length_m=length_m, slope_percent=5.0, cn=cn
        )

        assert tc_steep < tc_gentle

    def test_scs_lag_zero_length_raises(self):
        """Test that zero length raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="length_m must be positive"):
            ConcentrationTime.scs_lag(length_m=0, slope_percent=2.0, cn=75)

    def test_scs_lag_negative_slope_raises(self):
        """Test that negative slope raises InvalidParameterError."""
        with pytest.raises(
            InvalidParameterError, match="slope_percent must be positive"
        ):
            ConcentrationTime.scs_lag(length_m=5000, slope_percent=-2.0, cn=75)

    def test_scs_lag_cn_too_low_raises(self):
        """Test that CN < 1 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="cn must be in range 1-100"):
            ConcentrationTime.scs_lag(length_m=5000, slope_percent=2.0, cn=0)

    def test_scs_lag_cn_too_high_raises(self):
        """Test that CN > 100 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="cn must be in range 1-100"):
            ConcentrationTime.scs_lag(length_m=5000, slope_percent=2.0, cn=101)


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


class TestConcentrationTimeImport:
    """Test module imports."""

    def test_import_from_time_module(self):
        """Test that ConcentrationTime can be imported from hydrolog.time."""
        from hydrolog.time import ConcentrationTime as CT

        assert CT is not None
        assert hasattr(CT, "kirpich")
        assert hasattr(CT, "scs_lag")
        assert hasattr(CT, "giandotti")
