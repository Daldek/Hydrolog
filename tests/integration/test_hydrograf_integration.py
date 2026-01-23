"""
Integration tests for Hydrograf ↔ Hydrolog data exchange.

These tests simulate the complete workflow of receiving watershed parameters
from Hydrograf's API and processing them through Hydrolog's hydrological
calculations.
"""

import json
import pytest

from hydrolog.morphometry import WatershedParameters, WatershedGeometry, TerrainAnalysis
from hydrolog.runoff import HydrographGenerator, SCSCN
from hydrolog.precipitation import BetaHietogram, HietogramResult
from hydrolog.time import ConcentrationTime


class TestHydrografIntegration:
    """Test suite for Hydrograf API integration."""

    @pytest.fixture
    def hydrograf_api_response(self) -> dict:
        """
        Simulate a typical API response from Hydrograf's /delineate-watershed endpoint.

        This represents real morphometric parameters calculated from DEM and cells.
        """
        return {
            "name": "Zlewnia potoku Mokry",
            "area_km2": 45.3,
            "perimeter_km": 32.1,
            "length_km": 12.5,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "elevation_mean_m": 340.0,
            "mean_slope_m_per_m": 0.025,
            "channel_length_km": 14.2,
            "channel_slope_m_per_m": 0.018,
            "cn": 72,
            "source": "Hydrograf",
            "crs": "EPSG:2180",
        }

    @pytest.fixture
    def hydrograf_minimal_response(self) -> dict:
        """Simulate a minimal API response with only required fields."""
        return {
            "area_km2": 23.5,
            "perimeter_km": 22.0,
            "length_km": 8.0,
            "elevation_min_m": 200.0,
            "elevation_max_m": 450.0,
        }

    def test_full_workflow_json_to_hydrograph(self, hydrograf_api_response: dict):
        """
        Test complete integration workflow:
        JSON API response → WatershedParameters → HydrographGenerator → Result
        """
        # 1. Simulate receiving JSON from Hydrograf API
        json_string = json.dumps(hydrograf_api_response)

        # 2. Parse into WatershedParameters
        params = WatershedParameters.from_json(json_string)

        # 3. Verify parsed values
        assert params.name == "Zlewnia potoku Mokry"
        assert params.area_km2 == 45.3
        assert params.cn == 72
        assert params.source == "Hydrograf"

        # 4. Calculate concentration time
        tc_min = params.calculate_tc(method="kirpich")
        assert tc_min > 0

        # 5. Generate hydrograph
        generator = HydrographGenerator(
            area_km2=params.area_km2,
            cn=params.cn,
            tc_min=tc_min,
        )
        hietogram_gen = BetaHietogram()
        hietogram = hietogram_gen.generate(total_mm=50.0, duration_min=60, timestep_min=5)
        result = generator.generate(hietogram)

        # 6. Verify result
        assert result.peak_discharge_m3s > 0
        assert result.time_to_peak_min > 0
        assert result.total_volume_m3 > 0
        assert result.runoff_coefficient > 0
        assert result.runoff_coefficient < 1

    def test_from_dict_preserves_all_fields(self, hydrograf_api_response: dict):
        """Test that all fields from API response are correctly parsed."""
        params = WatershedParameters.from_dict(hydrograf_api_response)

        # Required fields
        assert params.area_km2 == 45.3
        assert params.perimeter_km == 32.1
        assert params.length_km == 12.5
        assert params.elevation_min_m == 150.0
        assert params.elevation_max_m == 520.0

        # Optional fields
        assert params.name == "Zlewnia potoku Mokry"
        assert params.elevation_mean_m == 340.0
        assert params.mean_slope_m_per_m == 0.025
        assert params.channel_length_km == 14.2
        assert params.channel_slope_m_per_m == 0.018
        assert params.cn == 72
        assert params.source == "Hydrograf"
        assert params.crs == "EPSG:2180"

        # Computed properties
        assert params.relief_m == 370.0  # 520 - 150
        assert abs(params.width_km - 3.624) < 0.001  # 45.3 / 12.5

    def test_to_geometry_conversion(self, hydrograf_api_response: dict):
        """Test conversion to WatershedGeometry for shape analysis."""
        params = WatershedParameters.from_dict(hydrograf_api_response)
        geom = params.to_geometry()

        assert isinstance(geom, WatershedGeometry)
        assert geom.area_km2 == params.area_km2
        assert geom.perimeter_km == params.perimeter_km
        assert geom.length_km == params.length_km

        # Verify shape indicators calculation works
        indicators = geom.get_shape_indicators()
        assert indicators.form_factor > 0
        assert indicators.compactness_coefficient > 0
        assert indicators.circularity_ratio > 0

    def test_to_terrain_conversion(self, hydrograf_api_response: dict):
        """Test conversion to TerrainAnalysis for terrain analysis."""
        params = WatershedParameters.from_dict(hydrograf_api_response)
        terrain = params.to_terrain()

        assert isinstance(terrain, TerrainAnalysis)
        assert terrain.elevation_min_m == params.elevation_min_m
        assert terrain.elevation_max_m == params.elevation_max_m
        assert terrain.length_km == params.length_km

        # Verify slope parameters calculation works
        slopes = terrain.get_slope_parameters()
        assert slopes.watershed_slope_percent > 0

    def test_tc_calculation_methods(self, hydrograf_api_response: dict):
        """Test all concentration time calculation methods."""
        params = WatershedParameters.from_dict(hydrograf_api_response)

        # Kirpich (uses channel_length and channel_slope)
        tc_kirpich = params.calculate_tc(method="kirpich")
        assert tc_kirpich > 0

        # NRCS (requires CN)
        tc_scs = params.calculate_tc(method="nrcs")
        assert tc_scs > 0

        # Giandotti
        tc_giandotti = params.calculate_tc(method="giandotti")
        assert tc_giandotti > 0

        # All methods should give reasonable values (>10 min)
        # Note: Giandotti can give larger values for medium-sized catchments
        for tc in [tc_kirpich, tc_scs, tc_giandotti]:
            assert tc > 10

    def test_minimal_response_workflow(self, hydrograf_minimal_response: dict):
        """Test workflow with minimal required fields only."""
        params = WatershedParameters.from_dict(hydrograf_minimal_response)

        # Should calculate slope from relief/length when not provided
        tc_min = params.calculate_tc(method="kirpich")
        assert tc_min > 0

        # Geometry conversion should still work
        geom = params.to_geometry()
        assert geom.area_km2 == 23.5

    def test_round_trip_serialization(self, hydrograf_api_response: dict):
        """Test that data survives round-trip serialization."""
        # Parse
        params1 = WatershedParameters.from_dict(hydrograf_api_response)

        # Serialize and parse again
        json_str = params1.to_json()
        params2 = WatershedParameters.from_json(json_str)

        # Compare
        assert params1.area_km2 == params2.area_km2
        assert params1.cn == params2.cn
        assert params1.name == params2.name
        assert params1.relief_m == params2.relief_m

    def test_handles_extra_fields_gracefully(self, hydrograf_api_response: dict):
        """Test that unknown fields from API are ignored without errors."""
        # Add extra fields that Hydrolog doesn't know about
        hydrograf_api_response["some_future_field"] = "value"
        hydrograf_api_response["nested"] = {"data": 123}
        hydrograf_api_response["watershed_id"] = "uuid-123"

        # Should not raise exception
        params = WatershedParameters.from_dict(hydrograf_api_response)

        # Known fields should still work
        assert params.area_km2 == 45.3
        assert params.cn == 72

    def test_water_balance_integration(self, hydrograf_api_response: dict):
        """Test SCS-CN water balance calculations with Hydrograf data."""
        params = WatershedParameters.from_dict(hydrograf_api_response)

        # Calculate water balance
        scs = SCSCN(cn=params.cn)
        precipitation_mm = 80.0
        result = scs.effective_precipitation(precipitation_mm)

        # Verify calculations
        assert result.total_effective_mm < precipitation_mm  # Effective < Total
        assert result.total_effective_mm > 0
        assert result.retention_mm > 0
        assert result.initial_abstraction_mm > 0

        # Verify runoff coefficient
        runoff_coeff = result.total_effective_mm / precipitation_mm
        assert 0 < runoff_coeff < 1

    def test_multiple_watersheds_batch_processing(self):
        """Test processing multiple watersheds (batch mode)."""
        # Simulate batch response from Hydrograf
        watersheds_data = [
            {
                "name": "Zlewnia 1",
                "area_km2": 25.0,
                "perimeter_km": 20.0,
                "length_km": 8.0,
                "elevation_min_m": 100.0,
                "elevation_max_m": 400.0,
                "cn": 65,
            },
            {
                "name": "Zlewnia 2",
                "area_km2": 50.0,
                "perimeter_km": 35.0,
                "length_km": 15.0,
                "elevation_min_m": 150.0,
                "elevation_max_m": 600.0,
                "cn": 75,
            },
            {
                "name": "Zlewnia 3",
                "area_km2": 100.0,
                "perimeter_km": 50.0,
                "length_km": 20.0,
                "elevation_min_m": 200.0,
                "elevation_max_m": 800.0,
                "cn": 80,
            },
        ]

        results = []
        hietogram_gen = BetaHietogram()
        hietogram = hietogram_gen.generate(total_mm=50.0, duration_min=60, timestep_min=5)

        for data in watersheds_data:
            params = WatershedParameters.from_dict(data)
            tc = params.calculate_tc(method="kirpich")

            generator = HydrographGenerator(
                area_km2=params.area_km2,
                cn=params.cn,
                tc_min=tc,
            )
            result = generator.generate(hietogram)
            results.append({
                "name": params.name,
                "qmax": result.peak_discharge_m3s,
                "tc": tc,
            })

        # Verify all processed
        assert len(results) == 3

        # Larger watersheds should generally have higher peak flows
        # (with similar CN and precipitation)
        assert results[2]["qmax"] > results[0]["qmax"]


class TestHydrografDataValidation:
    """Test validation of data from Hydrograf."""

    def test_invalid_cn_raises_error(self):
        """Test that invalid CN from API raises appropriate error."""
        invalid_data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            "cn": 150,  # Invalid: must be 0-100
        }

        with pytest.raises(Exception):  # InvalidParameterError
            WatershedParameters.from_dict(invalid_data)

    def test_negative_area_raises_error(self):
        """Test that negative area raises error."""
        invalid_data = {
            "area_km2": -10.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }

        with pytest.raises(Exception):
            WatershedParameters.from_dict(invalid_data)

    def test_elevation_max_less_than_min_raises_error(self):
        """Test that max elevation < min elevation raises error."""
        invalid_data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 520.0,  # Higher
            "elevation_max_m": 150.0,  # Lower
        }

        with pytest.raises(Exception):
            WatershedParameters.from_dict(invalid_data)

    def test_missing_required_field_raises_error(self):
        """Test that missing required field raises error."""
        incomplete_data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            # Missing: length_km, elevation_min_m, elevation_max_m
        }

        with pytest.raises(Exception):
            WatershedParameters.from_dict(incomplete_data)

    def test_nrcs_without_cn_raises_error(self):
        """Test that NRCS method without CN raises error."""
        data = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
            # No CN provided
        }

        params = WatershedParameters.from_dict(data)

        with pytest.raises(Exception):
            params.calculate_tc(method="nrcs")
