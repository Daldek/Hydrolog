"""Unit tests for hydrolog.precipitation.interpolation module."""

import pytest
import numpy as np

from hydrolog.precipitation.interpolation import (
    Station,
    ThiessenResult,
    IDWResult,
    IsohyetResult,
    thiessen_polygons,
    inverse_distance_weighting,
    areal_precipitation_idw,
    isohyet_method,
    arithmetic_mean,
)
from hydrolog.exceptions import InvalidParameterError


class TestStation:
    """Tests for Station dataclass."""

    def test_create_station(self):
        """Test creating a station."""
        station = Station(
            station_id="S1",
            x=100.0,
            y=200.0,
            precipitation_mm=25.5,
            elevation_m=350.0,
        )
        assert station.station_id == "S1"
        assert station.x == 100.0
        assert station.y == 200.0
        assert station.precipitation_mm == 25.5
        assert station.elevation_m == 350.0

    def test_create_station_no_elevation(self):
        """Test creating station without elevation."""
        station = Station("S1", 0, 0, 30.0)
        assert station.elevation_m is None


class TestThiessenPolygons:
    """Tests for thiessen_polygons function."""

    @pytest.fixture
    def three_stations(self):
        """Create three test stations."""
        return [
            Station("S1", 0, 0, precipitation_mm=20.0),
            Station("S2", 10, 0, precipitation_mm=30.0),
            Station("S3", 5, 8, precipitation_mm=40.0),
        ]

    def test_equal_areas(self, three_stations):
        """Test with equal polygon areas."""
        areas = {"S1": 10.0, "S2": 10.0, "S3": 10.0}
        result = thiessen_polygons(three_stations, areas)

        # Equal weights = arithmetic mean
        expected = (20.0 + 30.0 + 40.0) / 3.0
        assert result.areal_precipitation_mm == pytest.approx(expected)

        # Check weights
        for sid in areas:
            assert result.station_weights[sid] == pytest.approx(1.0 / 3.0)

    def test_unequal_areas(self, three_stations):
        """Test with unequal polygon areas."""
        areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}
        result = thiessen_polygons(three_stations, areas)

        # Weighted average
        total_area = 45.0
        expected = (20.0 * 15 + 30.0 * 20 + 40.0 * 10) / total_area
        assert result.areal_precipitation_mm == pytest.approx(expected)

        # Check weights
        assert result.station_weights["S1"] == pytest.approx(15.0 / 45.0)
        assert result.station_weights["S2"] == pytest.approx(20.0 / 45.0)
        assert result.station_weights["S3"] == pytest.approx(10.0 / 45.0)

    def test_contributions(self, three_stations):
        """Test that contributions sum to areal precipitation."""
        areas = {"S1": 15.0, "S2": 20.0, "S3": 10.0}
        result = thiessen_polygons(three_stations, areas)

        contribution_sum = sum(result.station_contributions_mm.values())
        assert contribution_sum == pytest.approx(result.areal_precipitation_mm)

    def test_single_station(self):
        """Test with single station covering entire area."""
        stations = [Station("S1", 0, 0, precipitation_mm=35.0)]
        areas = {"S1": 50.0}
        result = thiessen_polygons(stations, areas)

        assert result.areal_precipitation_mm == pytest.approx(35.0)
        assert result.station_weights["S1"] == pytest.approx(1.0)

    def test_empty_stations(self):
        """Test that empty stations list raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            thiessen_polygons([], {"S1": 10.0})

    def test_unknown_station_id(self, three_stations):
        """Test with unknown station ID in areas."""
        areas = {"S1": 10.0, "S2": 10.0, "UNKNOWN": 10.0}
        with pytest.raises(InvalidParameterError, match="unknown station IDs"):
            thiessen_polygons(three_stations, areas)

    def test_partial_areas(self, three_stations):
        """Test with partial station coverage."""
        # Only two stations have areas (third is outside watershed)
        areas = {"S1": 15.0, "S2": 20.0}
        result = thiessen_polygons(three_stations, areas)

        expected = (20.0 * 15 + 30.0 * 20) / 35.0
        assert result.areal_precipitation_mm == pytest.approx(expected)


class TestInverseDistanceWeighting:
    """Tests for inverse_distance_weighting function."""

    @pytest.fixture
    def two_stations(self):
        """Create two test stations."""
        return [
            Station("S1", 0, 0, precipitation_mm=20.0),
            Station("S2", 10, 0, precipitation_mm=40.0),
        ]

    def test_midpoint(self, two_stations):
        """Test IDW at midpoint between two stations."""
        result = inverse_distance_weighting(two_stations, 5, 0, power=2)

        # At midpoint, both weights should be equal
        assert result.station_weights["S1"] == pytest.approx(0.5)
        assert result.station_weights["S2"] == pytest.approx(0.5)

        # Average of 20 and 40
        assert result.areal_precipitation_mm == pytest.approx(30.0)

    def test_closer_to_s1(self, two_stations):
        """Test IDW closer to S1."""
        result = inverse_distance_weighting(two_stations, 2, 0, power=2)

        # S1 should have higher weight
        assert result.station_weights["S1"] > result.station_weights["S2"]
        # Result should be closer to S1's value (20)
        assert 20.0 < result.areal_precipitation_mm < 30.0

    def test_at_station(self, two_stations):
        """Test IDW exactly at a station location."""
        result = inverse_distance_weighting(two_stations, 0, 0, power=2)

        # Should return S1's value exactly
        assert result.areal_precipitation_mm == pytest.approx(20.0)
        assert result.station_weights["S1"] == pytest.approx(1.0)

    def test_power_effect(self, two_stations):
        """Test effect of power parameter."""
        # At point (3, 0), closer to S1
        result_p1 = inverse_distance_weighting(two_stations, 3, 0, power=1)
        result_p2 = inverse_distance_weighting(two_stations, 3, 0, power=2)
        result_p4 = inverse_distance_weighting(two_stations, 3, 0, power=4)

        # Higher power = more weight to nearest station = lower value (closer to 20)
        assert result_p4.areal_precipitation_mm < result_p2.areal_precipitation_mm
        assert result_p2.areal_precipitation_mm < result_p1.areal_precipitation_mm

    def test_max_distance(self, two_stations):
        """Test max_distance parameter."""
        # S2 is at (10, 0), distance from (2, 0) is 8
        result = inverse_distance_weighting(
            two_stations, 2, 0, power=2, max_distance=5
        )

        # Only S1 should be included
        assert "S1" in result.station_weights
        assert "S2" not in result.station_weights
        assert result.areal_precipitation_mm == pytest.approx(20.0)

    def test_max_distance_no_stations(self, two_stations):
        """Test max_distance with no stations in range."""
        with pytest.raises(InvalidParameterError, match="No stations within"):
            inverse_distance_weighting(two_stations, 50, 50, power=2, max_distance=5)

    def test_empty_stations(self):
        """Test that empty stations list raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            inverse_distance_weighting([], 0, 0, power=2)

    def test_invalid_power(self, two_stations):
        """Test that non-positive power raises error."""
        with pytest.raises(InvalidParameterError, match="must be positive"):
            inverse_distance_weighting(two_stations, 5, 0, power=0)

        with pytest.raises(InvalidParameterError, match="must be positive"):
            inverse_distance_weighting(two_stations, 5, 0, power=-1)


class TestArealPrecipitationIDW:
    """Tests for areal_precipitation_idw function."""

    def test_uniform_precipitation(self):
        """Test with uniform precipitation."""
        stations = [
            Station("S1", 0, 0, precipitation_mm=30.0),
            Station("S2", 10, 0, precipitation_mm=30.0),
            Station("S3", 5, 10, precipitation_mm=30.0),
        ]
        grid_x = np.linspace(0, 10, 11)
        grid_y = np.linspace(0, 10, 11)
        xx, yy = np.meshgrid(grid_x, grid_y)

        result = areal_precipitation_idw(stations, xx.flatten(), yy.flatten())
        assert result == pytest.approx(30.0, rel=0.01)

    def test_gradient_precipitation(self):
        """Test with precipitation gradient."""
        stations = [
            Station("S1", 0, 0, precipitation_mm=20.0),
            Station("S2", 10, 0, precipitation_mm=40.0),
        ]
        # Grid along x-axis
        grid_x = np.linspace(0, 10, 11)
        grid_y = np.zeros(11)

        result = areal_precipitation_idw(stations, grid_x, grid_y)
        # Should be close to arithmetic mean (30) for uniform grid
        assert result == pytest.approx(30.0, rel=0.05)

    def test_mismatched_arrays(self):
        """Test that mismatched array lengths raise error."""
        stations = [Station("S1", 0, 0, precipitation_mm=25.0)]
        with pytest.raises(InvalidParameterError, match="same length"):
            areal_precipitation_idw(
                stations, np.array([0, 1, 2]), np.array([0, 1])
            )

    def test_empty_grid(self):
        """Test that empty grid raises error."""
        stations = [Station("S1", 0, 0, precipitation_mm=25.0)]
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            areal_precipitation_idw(stations, np.array([]), np.array([]))


class TestIsohyetMethod:
    """Tests for isohyet_method function."""

    def test_two_zones(self):
        """Test with two zones (three isohyets)."""
        isohyets = np.array([20.0, 30.0, 40.0])
        fractions = np.array([0.4, 0.6])  # 40% in zone 1, 60% in zone 2

        result = isohyet_method(isohyets, fractions)

        # Zone 1 avg: (20+30)/2 = 25
        # Zone 2 avg: (30+40)/2 = 35
        # Weighted: 25*0.4 + 35*0.6 = 10 + 21 = 31
        assert result.areal_precipitation_mm == pytest.approx(31.0)

    def test_uniform_zones(self):
        """Test with uniform zone distribution."""
        isohyets = np.array([10.0, 20.0, 30.0, 40.0])
        fractions = np.array([1 / 3, 1 / 3, 1 / 3])

        result = isohyet_method(isohyets, fractions)

        # Zone avgs: 15, 25, 35
        # Mean: (15 + 25 + 35) / 3 = 25
        assert result.areal_precipitation_mm == pytest.approx(25.0)

    def test_single_zone(self):
        """Test with single zone."""
        isohyets = np.array([20.0, 30.0])
        fractions = np.array([1.0])

        result = isohyet_method(isohyets, fractions)
        assert result.areal_precipitation_mm == pytest.approx(25.0)

    def test_fractions_not_sum_to_one(self):
        """Test that fractions not summing to 1 raises error."""
        isohyets = np.array([20.0, 30.0, 40.0])
        fractions = np.array([0.3, 0.3])  # Sum = 0.6

        with pytest.raises(InvalidParameterError, match="must sum to 1.0"):
            isohyet_method(isohyets, fractions)

    def test_negative_fractions(self):
        """Test that negative fractions raise error."""
        isohyets = np.array([20.0, 30.0, 40.0])
        fractions = np.array([1.5, -0.5])

        with pytest.raises(InvalidParameterError, match="non-negative"):
            isohyet_method(isohyets, fractions)

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise error."""
        isohyets = np.array([20.0, 30.0, 40.0])  # 3 isohyets = 2 zones
        fractions = np.array([0.3, 0.3, 0.4])  # 3 fractions

        with pytest.raises(InvalidParameterError, match="Expected 2"):
            isohyet_method(isohyets, fractions)

    def test_single_isohyet(self):
        """Test that single isohyet raises error."""
        with pytest.raises(InvalidParameterError, match="at least 2"):
            isohyet_method(np.array([30.0]), np.array([]))


class TestArithmeticMean:
    """Tests for arithmetic_mean function."""

    def test_three_stations(self):
        """Test arithmetic mean with three stations."""
        stations = [
            Station("S1", 0, 0, precipitation_mm=20.0),
            Station("S2", 10, 0, precipitation_mm=30.0),
            Station("S3", 5, 8, precipitation_mm=40.0),
        ]
        result = arithmetic_mean(stations)
        assert result == pytest.approx(30.0)

    def test_single_station(self):
        """Test with single station."""
        stations = [Station("S1", 0, 0, precipitation_mm=35.0)]
        result = arithmetic_mean(stations)
        assert result == pytest.approx(35.0)

    def test_equal_values(self):
        """Test with equal precipitation values."""
        stations = [
            Station("S1", 0, 0, precipitation_mm=25.0),
            Station("S2", 10, 0, precipitation_mm=25.0),
        ]
        result = arithmetic_mean(stations)
        assert result == pytest.approx(25.0)

    def test_empty_stations(self):
        """Test that empty stations list raises error."""
        with pytest.raises(InvalidParameterError, match="cannot be empty"):
            arithmetic_mean([])


class TestMethodComparison:
    """Compare different interpolation methods."""

    @pytest.fixture
    def test_stations(self):
        """Create test stations for comparison."""
        return [
            Station("S1", 0, 0, precipitation_mm=20.0),
            Station("S2", 10, 0, precipitation_mm=30.0),
            Station("S3", 10, 10, precipitation_mm=40.0),
            Station("S4", 0, 10, precipitation_mm=25.0),
        ]

    def test_methods_produce_reasonable_values(self, test_stations):
        """Test that all methods produce values within station range."""
        min_p = min(s.precipitation_mm for s in test_stations)
        max_p = max(s.precipitation_mm for s in test_stations)

        # Arithmetic mean
        am = arithmetic_mean(test_stations)
        assert min_p <= am <= max_p

        # Thiessen
        areas = {"S1": 25, "S2": 25, "S3": 25, "S4": 25}
        thiessen = thiessen_polygons(test_stations, areas)
        assert min_p <= thiessen.areal_precipitation_mm <= max_p

        # Isohyet
        isohyets = np.array([20.0, 30.0, 40.0])
        fractions = np.array([0.5, 0.5])
        isoh = isohyet_method(isohyets, fractions)
        assert min_p <= isoh.areal_precipitation_mm <= max_p
