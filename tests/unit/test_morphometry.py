"""Tests for morphometry module."""

import math

import numpy as np
import pytest

from hydrolog.morphometry import (
    WatershedGeometry,
    GeometricParameters,
    ShapeIndicators,
    TerrainAnalysis,
    ElevationParameters,
    SlopeParameters,
    HypsometricCurve,
    HypsometricResult,
)
from hydrolog.exceptions import InvalidParameterError


class TestWatershedGeometry:
    """Tests for WatershedGeometry class."""

    def test_basic_parameters(self):
        """Test basic geometric parameters."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        assert geom.area_km2 == 45.0
        assert geom.perimeter_km == 32.0
        assert geom.length_km == 12.0

    def test_width_calculation(self):
        """Test width calculation W = A / L."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # W = 45 / 12 = 3.75 km
        assert abs(geom.width_km - 3.75) < 0.01

    def test_get_parameters(self):
        """Test get_parameters returns correct dataclass."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
        params = geom.get_parameters()

        assert isinstance(params, GeometricParameters)
        assert params.area_km2 == 45.0
        assert params.perimeter_km == 32.0
        assert params.length_km == 12.0
        assert abs(params.width_km - 3.75) < 0.01

    def test_form_factor(self):
        """Test form factor calculation Cf = A / L²."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # Cf = 45 / 144 = 0.3125
        assert abs(geom.form_factor() - 0.3125) < 0.001

    def test_form_factor_circular(self):
        """Test form factor for circular watershed."""
        # For a circle: L = diameter = 2r, A = πr²
        # Cf = πr² / (2r)² = π/4 ≈ 0.785
        r = 5.0
        area = math.pi * r**2
        length = 2 * r  # diameter
        perimeter = 2 * math.pi * r

        geom = WatershedGeometry(
            area_km2=area, perimeter_km=perimeter, length_km=length
        )

        assert abs(geom.form_factor() - math.pi / 4) < 0.01

    def test_compactness_coefficient(self):
        """Test Gravelius compactness coefficient."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # Cz = P / (2 * sqrt(π * A)) = 32 / (2 * sqrt(π * 45))
        expected = 32.0 / (2.0 * math.sqrt(math.pi * 45.0))
        assert abs(geom.compactness_coefficient() - expected) < 0.001

    def test_compactness_coefficient_circular(self):
        """Test compactness coefficient for circular watershed = 1.0."""
        r = 5.0
        area = math.pi * r**2
        perimeter = 2 * math.pi * r
        length = 2 * r

        geom = WatershedGeometry(
            area_km2=area, perimeter_km=perimeter, length_km=length
        )

        assert abs(geom.compactness_coefficient() - 1.0) < 0.01

    def test_circularity_ratio(self):
        """Test Miller's circularity ratio."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # Ck = 4πA / P² = 4π * 45 / 32²
        expected = (4.0 * math.pi * 45.0) / (32.0**2)
        assert abs(geom.circularity_ratio() - expected) < 0.001

    def test_circularity_ratio_circular(self):
        """Test circularity ratio for circular watershed = 1.0."""
        r = 5.0
        area = math.pi * r**2
        perimeter = 2 * math.pi * r
        length = 2 * r

        geom = WatershedGeometry(
            area_km2=area, perimeter_km=perimeter, length_km=length
        )

        assert abs(geom.circularity_ratio() - 1.0) < 0.01

    def test_elongation_ratio(self):
        """Test Schumm's elongation ratio."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # Ce = (2/L) * sqrt(A/π) = (2/12) * sqrt(45/π)
        expected = (2.0 / 12.0) * math.sqrt(45.0 / math.pi)
        assert abs(geom.elongation_ratio() - expected) < 0.001

    def test_elongation_ratio_circular(self):
        """Test elongation ratio for circular watershed = 1.0."""
        r = 5.0
        area = math.pi * r**2
        perimeter = 2 * math.pi * r
        length = 2 * r  # diameter

        geom = WatershedGeometry(
            area_km2=area, perimeter_km=perimeter, length_km=length
        )

        assert abs(geom.elongation_ratio() - 1.0) < 0.01

    def test_lemniscate_ratio(self):
        """Test Chorley's lemniscate ratio."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)

        # Cl = L² / (4A) = 144 / 180 = 0.8
        assert abs(geom.lemniscate_ratio() - 0.8) < 0.001

    def test_get_shape_indicators(self):
        """Test get_shape_indicators returns correct dataclass."""
        geom = WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=12.0)
        indicators = geom.get_shape_indicators()

        assert isinstance(indicators, ShapeIndicators)
        assert indicators.form_factor == geom.form_factor()
        assert indicators.compactness_coefficient == geom.compactness_coefficient()
        assert indicators.circularity_ratio == geom.circularity_ratio()
        assert indicators.elongation_ratio == geom.elongation_ratio()
        assert indicators.lemniscate_ratio == geom.lemniscate_ratio()

    def test_invalid_area(self):
        """Test that non-positive area raises error."""
        with pytest.raises(InvalidParameterError, match="area_km2"):
            WatershedGeometry(area_km2=0, perimeter_km=32.0, length_km=12.0)

    def test_invalid_perimeter(self):
        """Test that non-positive perimeter raises error."""
        with pytest.raises(InvalidParameterError, match="perimeter_km"):
            WatershedGeometry(area_km2=45.0, perimeter_km=-1.0, length_km=12.0)

    def test_invalid_length(self):
        """Test that non-positive length raises error."""
        with pytest.raises(InvalidParameterError, match="length_km"):
            WatershedGeometry(area_km2=45.0, perimeter_km=32.0, length_km=0)


class TestTerrainAnalysis:
    """Tests for TerrainAnalysis class."""

    def test_basic_parameters(self):
        """Test basic terrain parameters."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        assert terrain.elevation_min_m == 150.0
        assert terrain.elevation_max_m == 520.0
        assert terrain.length_km == 12.0

    def test_relief(self):
        """Test relief calculation."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        assert terrain.relief_m == 370.0

    def test_relief_ratio(self):
        """Test relief ratio calculation."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        # Rh = 370 / 12000 = 0.0308
        assert abs(terrain.relief_ratio - 0.0308) < 0.001

    def test_default_mean_elevation(self):
        """Test default mean elevation as midpoint."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        # Default: (150 + 520) / 2 = 335
        assert terrain.elevation_mean_m == 335.0

    def test_custom_mean_elevation(self):
        """Test custom mean elevation."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
            elevation_mean_m=340.0,
        )

        assert terrain.elevation_mean_m == 340.0

    def test_default_channel_length(self):
        """Test default channel length equals watershed length."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        assert terrain.channel_length_km == 12.0

    def test_custom_channel_length(self):
        """Test custom channel length."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
            channel_length_km=15.0,
        )

        assert terrain.channel_length_km == 15.0

    def test_watershed_slope(self):
        """Test watershed slope calculation."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
        )

        slope_pct, slope_m = terrain.watershed_slope()

        # slope_m = 370 / 12000 = 0.0308
        assert abs(slope_m - 0.0308) < 0.001
        assert abs(slope_pct - 3.08) < 0.1

    def test_channel_slope(self):
        """Test channel slope calculation."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
            channel_length_km=15.0,
        )

        slope_pct, slope_m = terrain.channel_slope()

        # slope_m = 370 / 15000 = 0.0247
        assert abs(slope_m - 0.0247) < 0.001
        assert abs(slope_pct - 2.47) < 0.1

    def test_get_elevation_parameters(self):
        """Test get_elevation_parameters returns correct dataclass."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
            elevation_mean_m=340.0,
        )
        params = terrain.get_elevation_parameters()

        assert isinstance(params, ElevationParameters)
        assert params.elevation_min_m == 150.0
        assert params.elevation_max_m == 520.0
        assert params.elevation_mean_m == 340.0
        assert params.relief_m == 370.0

    def test_get_slope_parameters(self):
        """Test get_slope_parameters returns correct dataclass."""
        terrain = TerrainAnalysis(
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            length_km=12.0,
            channel_length_km=15.0,
        )
        params = terrain.get_slope_parameters()

        assert isinstance(params, SlopeParameters)
        assert params.watershed_slope_percent > 0
        assert params.channel_slope_percent > 0

    def test_mean_elevation_from_dem(self):
        """Test mean elevation calculation from DEM."""
        elevations = np.array([100, 150, 200, 250, 300])
        mean_elev = TerrainAnalysis.mean_elevation_from_dem(elevations)

        assert mean_elev == 200.0

    def test_mean_elevation_from_dem_weighted(self):
        """Test weighted mean elevation calculation."""
        elevations = np.array([100, 200, 300])
        weights = np.array([1, 2, 1])  # Middle value has double weight

        mean_elev = TerrainAnalysis.mean_elevation_from_dem(elevations, weights)

        # Weighted mean: (100*1 + 200*2 + 300*1) / 4 = 200
        assert mean_elev == 200.0

    def test_invalid_elevation_order(self):
        """Test that max <= min raises error."""
        with pytest.raises(InvalidParameterError, match="elevation_max_m"):
            TerrainAnalysis(
                elevation_min_m=520.0,
                elevation_max_m=150.0,
                length_km=12.0,
            )

    def test_invalid_mean_elevation(self):
        """Test that mean outside range raises error."""
        with pytest.raises(InvalidParameterError, match="elevation_mean_m"):
            TerrainAnalysis(
                elevation_min_m=150.0,
                elevation_max_m=520.0,
                length_km=12.0,
                elevation_mean_m=600.0,  # Above max
            )

    def test_invalid_length(self):
        """Test that non-positive length raises error."""
        with pytest.raises(InvalidParameterError, match="length_km"):
            TerrainAnalysis(
                elevation_min_m=150.0,
                elevation_max_m=520.0,
                length_km=0,
            )


class TestHypsometricCurve:
    """Tests for HypsometricCurve class."""

    def test_basic_properties(self):
        """Test basic hypsometric properties."""
        elevations = np.array([100, 150, 200, 250, 300])
        hypso = HypsometricCurve(elevations)

        assert hypso.elevation_min == 100.0
        assert hypso.elevation_max == 300.0
        assert hypso.relief == 200.0

    def test_uniform_distribution(self):
        """Test hypsometric curve for uniform elevation distribution."""
        # Linear distribution should give HI ≈ 0.5
        elevations = np.linspace(100, 500, 1000)
        hypso = HypsometricCurve(elevations)

        hi = hypso.hypsometric_integral()

        assert 0.45 < hi < 0.55  # Should be close to 0.5

    def test_generate_curve(self):
        """Test curve generation."""
        elevations = np.array([100, 150, 200, 250, 300])
        hypso = HypsometricCurve(elevations)

        rel_h, rel_a = hypso.generate_curve(n_points=11)

        assert len(rel_h) == 11
        assert len(rel_a) == 11
        assert rel_h[0] == 0.0
        assert rel_h[-1] == 1.0
        assert rel_a[0] == 1.0  # All area above minimum
        assert rel_a[-1] <= 0.2 + 0.01  # Small area above maximum

    def test_mean_elevation(self):
        """Test mean elevation calculation."""
        elevations = np.array([100, 150, 200, 250, 300])
        hypso = HypsometricCurve(elevations)

        mean_elev = hypso.mean_elevation()

        assert mean_elev == 200.0

    def test_mean_elevation_weighted(self):
        """Test weighted mean elevation."""
        elevations = np.array([100, 200, 300])
        areas = np.array([1.0, 2.0, 1.0])
        hypso = HypsometricCurve(elevations, cell_areas=areas)

        mean_elev = hypso.mean_elevation()

        # Weighted mean: (100*1 + 200*2 + 300*1) / 4 = 200
        assert mean_elev == 200.0

    def test_elevation_at_percentile(self):
        """Test elevation at percentile."""
        elevations = np.linspace(100, 500, 100)
        hypso = HypsometricCurve(elevations)

        median = hypso.elevation_at_percentile(50)

        # Should be close to middle elevation
        assert 290 < median < 310

    def test_analyze(self):
        """Test complete analysis."""
        elevations = np.linspace(100, 500, 1000)
        hypso = HypsometricCurve(elevations)

        result = hypso.analyze()

        assert isinstance(result, HypsometricResult)
        assert len(result.relative_heights) == 101
        assert len(result.relative_areas) == 101
        assert 0.4 < result.hypsometric_integral < 0.6
        assert 290 < result.elevation_mean_m < 310
        assert 290 < result.elevation_median_m < 310

    def test_young_watershed(self):
        """Test hypsometric integral for young (convex) watershed."""
        # High elevations dominate - HI > 0.6
        elevations = np.array([400] * 70 + [300] * 20 + [200] * 7 + [100] * 3)
        hypso = HypsometricCurve(elevations)

        hi = hypso.hypsometric_integral()

        assert hi > 0.6

    def test_old_watershed(self):
        """Test hypsometric integral for old (concave) watershed."""
        # Low elevations dominate - HI < 0.4
        elevations = np.array([100] * 70 + [200] * 20 + [300] * 7 + [400] * 3)
        hypso = HypsometricCurve(elevations)

        hi = hypso.hypsometric_integral()

        assert hi < 0.4

    def test_n_points_property(self):
        """Test n_points property of result."""
        elevations = np.linspace(100, 500, 100)
        hypso = HypsometricCurve(elevations)

        result = hypso.analyze(n_points=51)

        assert result.n_points == 51

    def test_invalid_empty_elevations(self):
        """Test that empty elevations raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            HypsometricCurve(np.array([]))

    def test_invalid_cell_areas_length(self):
        """Test that mismatched cell_areas raises error."""
        elevations = np.array([100, 200, 300])
        areas = np.array([1.0, 2.0])  # Wrong length

        with pytest.raises(InvalidParameterError, match="must match"):
            HypsometricCurve(elevations, cell_areas=areas)

    def test_invalid_percentile(self):
        """Test that invalid percentile raises error."""
        elevations = np.array([100, 200, 300])
        hypso = HypsometricCurve(elevations)

        with pytest.raises(InvalidParameterError, match="percentile"):
            hypso.elevation_at_percentile(150)

    def test_invalid_n_points(self):
        """Test that n_points < 2 raises error."""
        elevations = np.array([100, 200, 300])
        hypso = HypsometricCurve(elevations)

        with pytest.raises(InvalidParameterError, match="n_points"):
            hypso.generate_curve(n_points=1)


class TestWatershedParameters:
    """Tests for WatershedParameters dataclass."""

    # -- Helpers ---------------------------------------------------------
    @staticmethod
    def _base_dict(**overrides: object) -> dict:
        """Return minimal valid dict with optional overrides."""
        d: dict = {
            "area_km2": 45.0,
            "perimeter_km": 32.0,
            "length_km": 12.0,
            "elevation_min_m": 150.0,
            "elevation_max_m": 520.0,
        }
        d.update(overrides)
        return d

    @staticmethod
    def _base_params(**overrides: object) -> "WatershedParameters":
        from hydrolog.morphometry.watershed_params import WatershedParameters

        d = TestWatershedParameters._base_dict(**overrides)
        return WatershedParameters.from_dict(d)

    # -- New fields: basic construction ----------------------------------
    def test_new_fields_default_none(self):
        """New optional fields default to None."""
        from hydrolog.morphometry.watershed_params import WatershedParameters

        p = self._base_params()
        assert p.runoff_coeff is None
        assert p.retardance is None
        assert p.overland_length_km is None
        assert p.overland_slope_m_per_m is None
        assert p.Lc_km is None
        assert p.manning_n is None
        assert p.urban_pct is None
        assert p.forest_pct is None

    def test_new_fields_set_via_constructor(self):
        """New fields can be set via constructor."""
        from hydrolog.morphometry.watershed_params import WatershedParameters

        p = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            runoff_coeff=0.6,
            retardance=0.40,
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            Lc_km=8.0,
            manning_n=0.035,
            urban_pct=10.0,
            forest_pct=40.0,
        )
        assert p.runoff_coeff == 0.6
        assert p.retardance == 0.40
        assert p.overland_length_km == 0.25
        assert p.overland_slope_m_per_m == 0.008
        assert p.Lc_km == 8.0
        assert p.manning_n == 0.035
        assert p.urban_pct == 10.0
        assert p.forest_pct == 40.0

    # -- from_dict / to_dict round-trip with new fields ------------------
    def test_from_dict_new_fields(self):
        """from_dict correctly reads new fields."""
        p = self._base_params(
            runoff_coeff=0.5,
            retardance=0.20,
            overland_length_km=0.30,
            overland_slope_m_per_m=0.005,
            Lc_km=6.0,
            manning_n=0.04,
            urban_pct=5.0,
            forest_pct=55.0,
        )
        assert p.runoff_coeff == 0.5
        assert p.retardance == 0.20
        assert p.Lc_km == 6.0
        assert p.manning_n == 0.04
        assert p.urban_pct == 5.0
        assert p.forest_pct == 55.0

    def test_to_dict_includes_new_fields(self):
        """to_dict includes new fields when set."""
        p = self._base_params(runoff_coeff=0.7, Lc_km=8.0)
        d = p.to_dict()
        assert d["runoff_coeff"] == 0.7
        assert d["Lc_km"] == 8.0

    def test_to_dict_excludes_none_new_fields(self):
        """to_dict excludes None-valued new fields."""
        p = self._base_params()
        d = p.to_dict()
        assert "runoff_coeff" not in d
        assert "retardance" not in d
        assert "Lc_km" not in d
        assert "manning_n" not in d

    def test_round_trip_json_with_new_fields(self):
        """JSON round-trip preserves all new fields."""
        from hydrolog.morphometry.watershed_params import WatershedParameters

        p1 = self._base_params(
            runoff_coeff=0.65,
            retardance=0.40,
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            Lc_km=7.5,
            manning_n=0.035,
            urban_pct=12.0,
            forest_pct=30.0,
        )
        json_str = p1.to_json()
        p2 = WatershedParameters.from_json(json_str)

        assert p2.runoff_coeff == p1.runoff_coeff
        assert p2.retardance == p1.retardance
        assert p2.overland_length_km == p1.overland_length_km
        assert p2.overland_slope_m_per_m == p1.overland_slope_m_per_m
        assert p2.Lc_km == p1.Lc_km
        assert p2.manning_n == p1.manning_n
        assert p2.urban_pct == p1.urban_pct
        assert p2.forest_pct == p1.forest_pct

    def test_from_dict_backward_compatible(self):
        """from_dict with old-style dict (no new fields) still works."""
        d = self._base_dict(cn=72, source="Hydrograf")
        from hydrolog.morphometry.watershed_params import WatershedParameters

        p = WatershedParameters.from_dict(d)
        assert p.cn == 72
        assert p.runoff_coeff is None

    # -- Validation for new fields ---------------------------------------
    def test_invalid_runoff_coeff_zero(self):
        """runoff_coeff=0 is rejected."""
        with pytest.raises(InvalidParameterError, match="runoff_coeff"):
            self._base_params(runoff_coeff=0.0)

    def test_invalid_runoff_coeff_above_1(self):
        """runoff_coeff > 1.0 is rejected."""
        with pytest.raises(InvalidParameterError, match="runoff_coeff"):
            self._base_params(runoff_coeff=1.5)

    def test_invalid_retardance_negative(self):
        """Negative retardance is rejected."""
        with pytest.raises(InvalidParameterError, match="retardance"):
            self._base_params(retardance=-0.1)

    def test_invalid_overland_length_km_zero(self):
        """overland_length_km=0 is rejected."""
        with pytest.raises(InvalidParameterError, match="overland_length_km"):
            self._base_params(overland_length_km=0.0)

    def test_invalid_overland_slope_negative(self):
        """Negative overland_slope_m_per_m is rejected."""
        with pytest.raises(InvalidParameterError, match="overland_slope_m_per_m"):
            self._base_params(overland_slope_m_per_m=-0.01)

    def test_invalid_Lc_km_zero(self):
        """Lc_km=0 is rejected."""
        with pytest.raises(InvalidParameterError, match="Lc_km"):
            self._base_params(Lc_km=0.0)

    def test_invalid_manning_n_negative(self):
        """Negative manning_n is rejected."""
        with pytest.raises(InvalidParameterError, match="manning_n"):
            self._base_params(manning_n=-0.01)

    def test_invalid_urban_pct_above_100(self):
        """urban_pct > 100 is rejected."""
        with pytest.raises(InvalidParameterError, match="urban_pct"):
            self._base_params(urban_pct=101.0)

    def test_invalid_forest_pct_negative(self):
        """Negative forest_pct is rejected."""
        with pytest.raises(InvalidParameterError, match="forest_pct"):
            self._base_params(forest_pct=-1.0)

    # -- calculate_tc: FAA -----------------------------------------------
    def test_calculate_tc_faa(self):
        """FAA method produces a positive tc value."""
        p = self._base_params(
            runoff_coeff=0.6,
            mean_slope_m_per_m=0.02,
        )
        tc = p.calculate_tc(method="faa")
        assert tc > 0

    def test_calculate_tc_faa_missing_runoff_coeff(self):
        """FAA raises ValueError when runoff_coeff is missing."""
        p = self._base_params(mean_slope_m_per_m=0.02)
        with pytest.raises(ValueError, match="runoff_coeff"):
            p.calculate_tc(method="faa")

    # -- calculate_tc: Kerby ---------------------------------------------
    def test_calculate_tc_kerby(self):
        """Kerby method produces a positive tc value."""
        p = self._base_params(
            retardance=0.40,
            mean_slope_m_per_m=0.008,
        )
        tc = p.calculate_tc(method="kerby")
        assert tc > 0

    def test_calculate_tc_kerby_missing_retardance(self):
        """Kerby raises ValueError when retardance is missing."""
        p = self._base_params(mean_slope_m_per_m=0.008)
        with pytest.raises(ValueError, match="retardance"):
            p.calculate_tc(method="kerby")

    # -- calculate_tc: Kerby-Kirpich -------------------------------------
    def test_calculate_tc_kerby_kirpich(self):
        """Kerby-Kirpich method produces a positive tc value."""
        p = self._base_params(
            retardance=0.40,
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            channel_length_km=5.0,
            channel_slope_m_per_m=0.005,
        )
        tc = p.calculate_tc(method="kerby_kirpich")
        assert tc > 0

    def test_calculate_tc_kerby_kirpich_missing_retardance(self):
        """Kerby-Kirpich raises ValueError when retardance is missing."""
        p = self._base_params(
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            channel_length_km=5.0,
            channel_slope_m_per_m=0.005,
        )
        with pytest.raises(ValueError, match="retardance"):
            p.calculate_tc(method="kerby_kirpich")

    def test_calculate_tc_kerby_kirpich_missing_overland_length(self):
        """Kerby-Kirpich raises ValueError when overland_length_km is missing."""
        p = self._base_params(
            retardance=0.40,
            overland_slope_m_per_m=0.008,
            channel_length_km=5.0,
            channel_slope_m_per_m=0.005,
        )
        with pytest.raises(ValueError, match="overland_length_km"):
            p.calculate_tc(method="kerby_kirpich")

    def test_calculate_tc_kerby_kirpich_missing_overland_slope(self):
        """Kerby-Kirpich raises ValueError when overland_slope_m_per_m is missing."""
        p = self._base_params(
            retardance=0.40,
            overland_length_km=0.25,
            channel_length_km=5.0,
            channel_slope_m_per_m=0.005,
        )
        with pytest.raises(ValueError, match="overland_slope_m_per_m"):
            p.calculate_tc(method="kerby_kirpich")

    def test_calculate_tc_kerby_kirpich_missing_channel_length(self):
        """Kerby-Kirpich raises ValueError when channel_length_km is missing."""
        p = self._base_params(
            retardance=0.40,
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            channel_slope_m_per_m=0.005,
        )
        with pytest.raises(ValueError, match="channel_length_km"):
            p.calculate_tc(method="kerby_kirpich")

    def test_calculate_tc_kerby_kirpich_missing_channel_slope(self):
        """Kerby-Kirpich raises ValueError when channel_slope_m_per_m is missing."""
        p = self._base_params(
            retardance=0.40,
            overland_length_km=0.25,
            overland_slope_m_per_m=0.008,
            channel_length_km=5.0,
        )
        with pytest.raises(ValueError, match="channel_slope_m_per_m"):
            p.calculate_tc(method="kerby_kirpich")

    # -- calculate_tc: unknown method ------------------------------------
    def test_calculate_tc_unknown_method(self):
        """Unknown method raises ValueError with descriptive message."""
        p = self._base_params()
        with pytest.raises(ValueError, match="Unknown method"):
            p.calculate_tc(method="nonexistent")

    # -- Existing methods still work (regression) ------------------------
    def test_calculate_tc_kirpich_still_works(self):
        """Kirpich method still works after extension."""
        p = self._base_params(mean_slope_m_per_m=0.025)
        tc = p.calculate_tc(method="kirpich")
        assert tc > 0

    def test_calculate_tc_giandotti_still_works(self):
        """Giandotti method still works after extension."""
        p = self._base_params()
        tc = p.calculate_tc(method="giandotti")
        assert tc > 0


class TestMorphometryImport:
    """Test module imports."""

    def test_import_all_classes(self):
        """Test that all classes can be imported."""
        from hydrolog.morphometry import (
            WatershedGeometry,
            GeometricParameters,
            ShapeIndicators,
            TerrainAnalysis,
            ElevationParameters,
            SlopeParameters,
            HypsometricCurve,
            HypsometricResult,
        )

        assert WatershedGeometry is not None
        assert TerrainAnalysis is not None
        assert HypsometricCurve is not None
