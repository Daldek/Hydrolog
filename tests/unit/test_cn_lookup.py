"""Tests for CN lookup module (TR-55 tables)."""

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.runoff.cn_lookup import (
    CNLookupResult,
    HydrologicCondition,
    LandCover,
    calculate_weighted_cn,
    get_cn,
    get_cn_range,
    list_land_covers,
    lookup_cn,
)


class TestGetCN:
    """Tests for get_cn function."""

    def test_forest_good_condition_all_hsg(self):
        """Test forest CN values for all HSG groups (TR-55 values)."""
        assert get_cn("A", LandCover.FOREST, HydrologicCondition.GOOD) == 30
        assert get_cn("B", LandCover.FOREST, HydrologicCondition.GOOD) == 55
        assert get_cn("C", LandCover.FOREST, HydrologicCondition.GOOD) == 70
        assert get_cn("D", LandCover.FOREST, HydrologicCondition.GOOD) == 77

    def test_forest_poor_condition(self):
        """Test forest CN values for poor condition."""
        assert get_cn("A", LandCover.FOREST, HydrologicCondition.POOR) == 45
        assert get_cn("B", LandCover.FOREST, HydrologicCondition.POOR) == 66
        assert get_cn("C", LandCover.FOREST, HydrologicCondition.POOR) == 77
        assert get_cn("D", LandCover.FOREST, HydrologicCondition.POOR) == 83

    def test_pasture_all_conditions(self):
        """Test pasture CN values across conditions."""
        # HSG B
        assert get_cn("B", LandCover.PASTURE, HydrologicCondition.POOR) == 79
        assert get_cn("B", LandCover.PASTURE, HydrologicCondition.FAIR) == 69
        assert get_cn("B", LandCover.PASTURE, HydrologicCondition.GOOD) == 61

    def test_paved_surfaces(self):
        """Test paved surfaces have CN=98 for all HSG."""
        for hsg in ("A", "B", "C", "D"):
            assert get_cn(hsg, LandCover.PAVED) == 98

    def test_water_bodies(self):
        """Test water bodies have CN=100 for all HSG."""
        for hsg in ("A", "B", "C", "D"):
            assert get_cn(hsg, LandCover.WATER) == 100

    def test_residential_high_density(self):
        """Test high density residential (65% impervious)."""
        assert get_cn("A", LandCover.RESIDENTIAL_HIGH) == 77
        assert get_cn("B", LandCover.RESIDENTIAL_HIGH) == 85
        assert get_cn("C", LandCover.RESIDENTIAL_HIGH) == 90
        assert get_cn("D", LandCover.RESIDENTIAL_HIGH) == 92

    def test_commercial(self):
        """Test commercial areas (85% impervious)."""
        assert get_cn("A", LandCover.COMMERCIAL) == 89
        assert get_cn("B", LandCover.COMMERCIAL) == 92
        assert get_cn("C", LandCover.COMMERCIAL) == 94
        assert get_cn("D", LandCover.COMMERCIAL) == 95

    def test_meadow_no_condition_required(self):
        """Test meadow doesn't require condition."""
        assert get_cn("B", LandCover.MEADOW) == 58
        assert get_cn("C", LandCover.MEADOW) == 71

    def test_string_inputs(self):
        """Test that string inputs work correctly."""
        assert get_cn("b", "forest", "good") == 55
        assert get_cn("C", "pasture", "fair") == 79
        assert get_cn("A", "paved") == 98

    def test_uppercase_string_enum_name(self):
        """Test uppercase enum name strings."""
        assert get_cn("B", "FOREST", "GOOD") == 55

    def test_lowercase_hsg(self):
        """Test lowercase HSG input."""
        assert get_cn("a", LandCover.FOREST, HydrologicCondition.GOOD) == 30
        assert get_cn("d", LandCover.PAVED) == 98

    def test_invalid_hsg_raises(self):
        """Test that invalid HSG raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            get_cn("E", LandCover.FOREST)
        assert "Invalid HSG" in str(exc_info.value)

    def test_invalid_land_cover_raises(self):
        """Test that invalid land cover raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            get_cn("B", "invalid_cover")
        assert "Invalid land cover" in str(exc_info.value)

    def test_invalid_condition_raises(self):
        """Test that invalid condition raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            get_cn("B", LandCover.FOREST, "excellent")
        assert "Invalid condition" in str(exc_info.value)

    def test_default_condition_fair(self):
        """Test that condition defaults to FAIR when not provided."""
        # Forest without condition should use FAIR
        cn_explicit = get_cn("B", LandCover.FOREST, HydrologicCondition.FAIR)
        cn_default = get_cn("B", LandCover.FOREST)
        assert cn_explicit == cn_default == 60


class TestLookupCN:
    """Tests for lookup_cn function."""

    def test_returns_result_object(self):
        """Test that lookup_cn returns CNLookupResult."""
        result = lookup_cn("B", LandCover.FOREST, HydrologicCondition.GOOD)
        assert isinstance(result, CNLookupResult)

    def test_result_contains_correct_values(self):
        """Test result contains all lookup parameters."""
        result = lookup_cn("B", "forest", "good")

        assert result.cn == 55
        assert result.hsg == "B"
        assert result.land_cover == LandCover.FOREST
        assert result.condition == HydrologicCondition.GOOD

    def test_result_no_condition(self):
        """Test result when no condition is used."""
        result = lookup_cn("A", LandCover.PAVED)

        assert result.cn == 98
        assert result.condition is None


class TestGetCNRange:
    """Tests for get_cn_range function."""

    def test_forest_range(self):
        """Test CN range for forest (varies by condition)."""
        ranges = get_cn_range(LandCover.FOREST)

        # HSG A: poor=45, fair=36, good=30
        assert ranges["A"] == (30, 45)
        # HSG D: poor=83, fair=79, good=77
        assert ranges["D"] == (77, 83)

    def test_paved_range_single_value(self):
        """Test CN range for paved (no variation)."""
        ranges = get_cn_range(LandCover.PAVED)

        for hsg in ("A", "B", "C", "D"):
            assert ranges[hsg] == (98, 98)

    def test_string_input(self):
        """Test string input for land cover."""
        ranges = get_cn_range("forest")
        assert "A" in ranges
        assert "D" in ranges


class TestListLandCovers:
    """Tests for list_land_covers function."""

    def test_returns_all_land_covers(self):
        """Test that all land cover types are listed."""
        covers = list_land_covers()

        assert "FOREST" in covers
        assert "PASTURE" in covers
        assert "PAVED" in covers
        assert "WATER" in covers
        assert "COMMERCIAL" in covers

    def test_returns_dict_with_values(self):
        """Test that values are the enum values."""
        covers = list_land_covers()

        assert covers["FOREST"] == "forest"
        assert covers["PAVED"] == "paved"


class TestCalculateWeightedCN:
    """Tests for calculate_weighted_cn function."""

    def test_single_land_cover(self):
        """Test weighted CN with single land cover."""
        result = calculate_weighted_cn([(55, 100.0)])
        assert result == 55.0

    def test_equal_areas(self):
        """Test weighted CN with equal areas."""
        # 50% CN=60, 50% CN=80 -> average = 70
        result = calculate_weighted_cn([(60, 50.0), (80, 50.0)])
        assert result == 70.0

    def test_different_areas(self):
        """Test weighted CN with different areas."""
        # 60% forest (CN=55), 40% pasture (CN=69)
        # Weighted = (55*60 + 69*40) / 100 = (3300 + 2760) / 100 = 60.6
        result = calculate_weighted_cn([(55, 60.0), (69, 40.0)])
        assert abs(result - 60.6) < 0.01

    def test_multiple_covers(self):
        """Test weighted CN with multiple land covers."""
        # 30 km² forest (CN=55), 20 km² pasture (CN=69), 10 km² residential (CN=85)
        # Total = 60 km²
        # Weighted = (55*30 + 69*20 + 85*10) / 60 = (1650 + 1380 + 850) / 60 = 64.67
        result = calculate_weighted_cn([(55, 30.0), (69, 20.0), (85, 10.0)])
        assert abs(result - 64.67) < 0.01

    def test_empty_list_raises(self):
        """Test that empty list raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            calculate_weighted_cn([])
        assert "empty" in str(exc_info.value).lower()

    def test_invalid_cn_raises(self):
        """Test that invalid CN raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            calculate_weighted_cn([(150, 100.0)])
        assert "CN must be 1-100" in str(exc_info.value)

    def test_negative_area_raises(self):
        """Test that negative area raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            calculate_weighted_cn([(55, -10.0)])
        assert "negative" in str(exc_info.value).lower()

    def test_zero_total_area_raises(self):
        """Test that zero total area raises error."""
        with pytest.raises(InvalidParameterError) as exc_info:
            calculate_weighted_cn([(55, 0.0)])
        assert "positive" in str(exc_info.value).lower()


class TestLandCoverEnum:
    """Tests for LandCover enum."""

    def test_agricultural_covers(self):
        """Test agricultural land cover types exist."""
        assert LandCover.FALLOW.value == "fallow"
        assert LandCover.ROW_CROPS.value == "row_crops"
        assert LandCover.SMALL_GRAIN.value == "small_grain"
        assert LandCover.PASTURE.value == "pasture"
        assert LandCover.MEADOW.value == "meadow"

    def test_natural_covers(self):
        """Test natural land cover types exist."""
        assert LandCover.BRUSH.value == "brush"
        assert LandCover.FOREST.value == "forest"
        assert LandCover.HERBACEOUS.value == "herbaceous"

    def test_developed_covers(self):
        """Test developed land cover types exist."""
        assert LandCover.RESIDENTIAL_LOW.value == "residential_low"
        assert LandCover.RESIDENTIAL_MEDIUM.value == "residential_medium"
        assert LandCover.RESIDENTIAL_HIGH.value == "residential_high"
        assert LandCover.COMMERCIAL.value == "commercial"
        assert LandCover.INDUSTRIAL.value == "industrial"


class TestHydrologicConditionEnum:
    """Tests for HydrologicCondition enum."""

    def test_conditions_exist(self):
        """Test all condition types exist."""
        assert HydrologicCondition.POOR.value == "poor"
        assert HydrologicCondition.FAIR.value == "fair"
        assert HydrologicCondition.GOOD.value == "good"


class TestCNTableConsistency:
    """Tests for CN table consistency and TR-55 compliance."""

    def test_cn_increases_with_hsg(self):
        """Test that CN increases from A to D for all land covers."""
        for land_cover in LandCover:
            try:
                cn_a = get_cn("A", land_cover)
                cn_b = get_cn("B", land_cover)
                cn_c = get_cn("C", land_cover)
                cn_d = get_cn("D", land_cover)

                # CN should increase or stay same from A to D
                assert cn_a <= cn_b <= cn_c <= cn_d, (
                    f"CN not increasing for {land_cover.value}: "
                    f"A={cn_a}, B={cn_b}, C={cn_c}, D={cn_d}"
                )
            except InvalidParameterError:
                # Some land covers may require condition
                pass

    def test_cn_decreases_with_better_condition(self):
        """Test that CN decreases with better hydrologic condition."""
        covers_with_condition = [
            LandCover.FOREST,
            LandCover.PASTURE,
            LandCover.BRUSH,
            LandCover.OPEN_SPACE,
        ]

        for land_cover in covers_with_condition:
            for hsg in ("A", "B", "C", "D"):
                cn_poor = get_cn(hsg, land_cover, HydrologicCondition.POOR)
                cn_fair = get_cn(hsg, land_cover, HydrologicCondition.FAIR)
                cn_good = get_cn(hsg, land_cover, HydrologicCondition.GOOD)

                assert cn_poor >= cn_fair >= cn_good, (
                    f"CN not decreasing with better condition for "
                    f"{land_cover.value}, HSG {hsg}: "
                    f"poor={cn_poor}, fair={cn_fair}, good={cn_good}"
                )

    def test_all_cn_in_valid_range(self):
        """Test all CN values are in range 1-100."""
        for land_cover in LandCover:
            for hsg in ("A", "B", "C", "D"):
                for condition in [None] + list(HydrologicCondition):
                    try:
                        cn = get_cn(hsg, land_cover, condition)
                        assert 1 <= cn <= 100, (
                            f"CN out of range for {land_cover.value}, "
                            f"HSG {hsg}, condition {condition}: CN={cn}"
                        )
                    except InvalidParameterError:
                        # Expected for invalid combinations
                        pass
