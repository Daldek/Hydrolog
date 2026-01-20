"""Tests for WatershedParameters and from_dict() methods."""

import json

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import (
    TerrainAnalysis,
    WatershedGeometry,
    WatershedParameters,
)


class TestWatershedParameters:
    """Tests for WatershedParameters dataclass."""

    @pytest.fixture
    def minimal_data(self) -> dict:
        """Minimal required data for WatershedParameters."""
        return {
            "area_km2": 45.3,
            "perimeter_km": 32.1,
            "length_km": 12.5,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }

    @pytest.fixture
    def complete_data(self) -> dict:
        """Complete data with all fields for WatershedParameters."""
        return {
            "name": "Test Watershed",
            "area_km2": 45.3,
            "perimeter_km": 32.1,
            "length_km": 12.5,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "elevation_mean_m": 340.0,
            "mean_slope_m_per_m": 0.025,
            "channel_length_km": 15.0,
            "channel_slope_m_per_m": 0.018,
            "cn": 72,
            "source": "Hydrograf",
            "crs": "EPSG:2180",
        }

    def test_create_minimal(self, minimal_data: dict) -> None:
        """Test creating WatershedParameters with minimal data."""
        params = WatershedParameters(**minimal_data)

        assert params.area_km2 == 45.3
        assert params.perimeter_km == 32.1
        assert params.length_km == 12.5
        assert params.elevation_min_m == 150.0
        assert params.elevation_max_m == 520.0
        assert params.name is None
        assert params.cn is None

    def test_create_complete(self, complete_data: dict) -> None:
        """Test creating WatershedParameters with all data."""
        params = WatershedParameters(**complete_data)

        assert params.name == "Test Watershed"
        assert params.area_km2 == 45.3
        assert params.cn == 72
        assert params.source == "Hydrograf"

    def test_width_km_property(self, minimal_data: dict) -> None:
        """Test width_km calculated property."""
        params = WatershedParameters(**minimal_data)

        expected_width = 45.3 / 12.5  # A / L
        assert params.width_km == pytest.approx(expected_width, rel=1e-6)

    def test_relief_m_property(self, minimal_data: dict) -> None:
        """Test relief_m calculated property."""
        params = WatershedParameters(**minimal_data)

        expected_relief = 520.0 - 150.0  # max - min
        assert params.relief_m == expected_relief

    def test_validation_negative_area(self, minimal_data: dict) -> None:
        """Test validation rejects negative area."""
        minimal_data["area_km2"] = -10.0

        with pytest.raises(InvalidParameterError, match="area_km2 must be positive"):
            WatershedParameters(**minimal_data)

    def test_validation_zero_perimeter(self, minimal_data: dict) -> None:
        """Test validation rejects zero perimeter."""
        minimal_data["perimeter_km"] = 0.0

        with pytest.raises(InvalidParameterError, match="perimeter_km must be positive"):
            WatershedParameters(**minimal_data)

    def test_validation_invalid_elevations(self, minimal_data: dict) -> None:
        """Test validation rejects max <= min elevation."""
        minimal_data["elevation_max_m"] = 100.0  # less than min (150.0)

        with pytest.raises(InvalidParameterError, match="elevation_max_m.*must be greater"):
            WatershedParameters(**minimal_data)

    def test_validation_invalid_cn(self, minimal_data: dict) -> None:
        """Test validation rejects CN outside 0-100 range."""
        minimal_data["cn"] = 150

        with pytest.raises(InvalidParameterError, match="cn must be 0-100"):
            WatershedParameters(**minimal_data)

    def test_validation_negative_slope(self, minimal_data: dict) -> None:
        """Test validation rejects negative slope."""
        minimal_data["mean_slope_m_per_m"] = -0.01

        with pytest.raises(InvalidParameterError, match="mean_slope_m_per_m must be non-negative"):
            WatershedParameters(**minimal_data)


class TestWatershedParametersFromDict:
    """Tests for WatershedParameters.from_dict() method."""

    def test_from_dict_minimal(self) -> None:
        """Test creating from dict with minimal data."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }
        params = WatershedParameters.from_dict(data)

        assert params.area_km2 == 45.0
        assert params.perimeter_km == 32.0
        assert params.length_km == 12.0
        assert params.elevation_min_m == 150.0
        assert params.elevation_max_m == 520.0

    def test_from_dict_complete(self) -> None:
        """Test creating from dict with all fields."""
        data = {
            "name": "Test",
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "elevation_mean_m": 340.0,
            "cn": 72,
            "source": "Hydrograf",
        }
        params = WatershedParameters.from_dict(data)

        assert params.name == "Test"
        assert params.cn == 72
        assert params.source == "Hydrograf"

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Test that from_dict ignores unknown keys."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "unknown_field": "ignored",
            "another_unknown": 123,
        }
        params = WatershedParameters.from_dict(data)

        assert params.area_km2 == 45.0
        assert not hasattr(params, "unknown_field")

    def test_from_dict_missing_required_key(self) -> None:
        """Test that from_dict raises error for missing required keys."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            # missing length_km
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }

        # Can raise either KeyError or TypeError depending on implementation
        with pytest.raises((KeyError, TypeError)):
            WatershedParameters.from_dict(data)


class TestWatershedParametersFromJson:
    """Tests for WatershedParameters.from_json() method."""

    def test_from_json(self) -> None:
        """Test creating from JSON string."""
        json_str = """
        {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "cn": 72
        }
        """
        params = WatershedParameters.from_json(json_str)

        assert params.area_km2 == 45.0
        assert params.cn == 72


class TestWatershedParametersToDict:
    """Tests for WatershedParameters.to_dict() method."""

    def test_to_dict_excludes_none(self) -> None:
        """Test that to_dict excludes None values."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
        )
        d = params.to_dict()

        assert "area_km2" in d
        assert "name" not in d  # None value excluded
        assert "cn" not in d  # None value excluded

    def test_to_dict_includes_set_values(self) -> None:
        """Test that to_dict includes explicitly set values."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            cn=72,
            source="Test",
        )
        d = params.to_dict()

        assert d["cn"] == 72
        assert d["source"] == "Test"


class TestWatershedParametersRoundTrip:
    """Tests for to_dict/from_dict round-trip."""

    def test_round_trip_minimal(self) -> None:
        """Test round-trip with minimal data."""
        original = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
        )

        d = original.to_dict()
        restored = WatershedParameters.from_dict(d)

        assert restored.area_km2 == original.area_km2
        assert restored.perimeter_km == original.perimeter_km
        assert restored.length_km == original.length_km

    def test_round_trip_complete(self) -> None:
        """Test round-trip with complete data."""
        original = WatershedParameters(
            name="Test",
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            elevation_mean_m=340.0,
            mean_slope_m_per_m=0.025,
            cn=72,
            source="Hydrograf",
        )

        json_str = original.to_json()
        restored = WatershedParameters.from_json(json_str)

        assert restored.name == original.name
        assert restored.cn == original.cn
        assert restored.source == original.source


class TestWatershedParametersToGeometry:
    """Tests for WatershedParameters.to_geometry() method."""

    def test_to_geometry(self) -> None:
        """Test conversion to WatershedGeometry."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
        )

        geom = params.to_geometry()

        assert isinstance(geom, WatershedGeometry)
        assert geom.area_km2 == 45.0
        assert geom.perimeter_km == 32.0
        assert geom.length_km == 12.0


class TestWatershedParametersToTerrain:
    """Tests for WatershedParameters.to_terrain() method."""

    def test_to_terrain_minimal(self) -> None:
        """Test conversion to TerrainAnalysis with minimal data."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
        )

        terrain = params.to_terrain()

        assert isinstance(terrain, TerrainAnalysis)
        assert terrain.elevation_min_m == 150.0
        assert terrain.elevation_max_m == 520.0
        assert terrain.length_km == 12.0

    def test_to_terrain_with_optionals(self) -> None:
        """Test conversion to TerrainAnalysis with optional data."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            elevation_mean_m=340.0,
            channel_length_km=15.0,
        )

        terrain = params.to_terrain()

        assert terrain.elevation_mean_m == 340.0
        assert terrain.channel_length_km == 15.0


class TestWatershedParametersCalculateTc:
    """Tests for WatershedParameters.calculate_tc() method."""

    @pytest.fixture
    def params_with_slope(self) -> WatershedParameters:
        """Parameters with slope for tc calculation."""
        return WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
        )

    def test_calculate_tc_kirpich(self, params_with_slope: WatershedParameters) -> None:
        """Test tc calculation with Kirpich method."""
        tc = params_with_slope.calculate_tc(method="kirpich")

        assert tc > 0
        assert isinstance(tc, float)

    def test_calculate_tc_uses_channel_length(self) -> None:
        """Test that tc uses channel_length_km when available."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,  # watershed length
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
            channel_length_km=15.0,  # longer channel
        )

        tc_with_channel = params.calculate_tc(method="kirpich")

        # Create params without channel_length
        params_no_channel = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
        )
        tc_no_channel = params_no_channel.calculate_tc(method="kirpich")

        # tc should be longer with longer channel
        assert tc_with_channel > tc_no_channel

    def test_calculate_tc_scs_lag_requires_cn(self) -> None:
        """Test that SCS Lag method requires CN."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
            # no CN
        )

        with pytest.raises(InvalidParameterError, match="CN is required"):
            params.calculate_tc(method="scs_lag")

    def test_calculate_tc_scs_lag_with_cn(self) -> None:
        """Test SCS Lag method with CN."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
            cn=72,
        )

        tc = params.calculate_tc(method="scs_lag")

        assert tc > 0

    def test_calculate_tc_giandotti(self) -> None:
        """Test Giandotti method."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            elevation_mean_m=340.0,
        )

        tc = params.calculate_tc(method="giandotti")

        assert tc > 0

    def test_calculate_tc_unknown_method(self, params_with_slope: WatershedParameters) -> None:
        """Test that unknown method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown method"):
            params_with_slope.calculate_tc(method="unknown")

    def test_calculate_tc_slope_from_relief(self) -> None:
        """Test tc calculation with slope calculated from relief."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            # no slope provided - should calculate from relief/length
        )

        tc = params.calculate_tc(method="kirpich")

        assert tc > 0


class TestWatershedGeometryFromDict:
    """Tests for WatershedGeometry.from_dict() method."""

    def test_from_dict(self) -> None:
        """Test creating WatershedGeometry from dict."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
        }
        geom = WatershedGeometry.from_dict(data)

        assert geom.area_km2 == 45.0
        assert geom.perimeter_km == 32.0
        assert geom.length_km == 12.0

    def test_from_dict_ignores_extra_keys(self) -> None:
        """Test that from_dict ignores extra keys."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,  # extra key
            "source": "Hydrograf",  # extra key
        }
        geom = WatershedGeometry.from_dict(data)

        assert geom.area_km2 == 45.0

    def test_from_dict_missing_key(self) -> None:
        """Test that from_dict raises KeyError for missing keys."""
        data = {
            "area_km2": 45.0,
            # missing perimeter_km and length_km
        }

        with pytest.raises(KeyError):
            WatershedGeometry.from_dict(data)


class TestTerrainAnalysisFromDict:
    """Tests for TerrainAnalysis.from_dict() method."""

    def test_from_dict_minimal(self) -> None:
        """Test creating TerrainAnalysis from dict with minimal data."""
        data = {
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "length_km": 12.0,
        }
        terrain = TerrainAnalysis.from_dict(data)

        assert terrain.elevation_min_m == 150.0
        assert terrain.elevation_max_m == 520.0
        assert terrain.length_km == 12.0

    def test_from_dict_with_optionals(self) -> None:
        """Test creating TerrainAnalysis from dict with optional data."""
        data = {
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "length_km": 12.0,
            "elevation_mean_m": 340.0,
            "channel_length_km": 15.0,
        }
        terrain = TerrainAnalysis.from_dict(data)

        assert terrain.elevation_mean_m == 340.0
        assert terrain.channel_length_km == 15.0

    def test_from_dict_ignores_extra_keys(self) -> None:
        """Test that from_dict ignores extra keys."""
        data = {
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "length_km": 12.0,
            "area_km2": 45.0,  # extra key
            "cn": 72,  # extra key
        }
        terrain = TerrainAnalysis.from_dict(data)

        assert terrain.elevation_min_m == 150.0

    def test_from_dict_missing_key(self) -> None:
        """Test that from_dict raises KeyError for missing keys."""
        data = {
            "elevation_min_m": 150.0,
            # missing elevation_max_m and length_km
        }

        with pytest.raises(KeyError):
            TerrainAnalysis.from_dict(data)
