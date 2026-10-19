"""Tests for WatershedParameters and from_dict() methods."""

import json

import pytest

from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import (
    TerrainAnalysis,
    WatershedGeometry,
    WatershedParameters,
)
from hydrolog.time import ConcentrationTime


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

        with pytest.raises(
            InvalidParameterError, match="perimeter_km must be positive"
        ):
            WatershedParameters(**minimal_data)

    def test_validation_invalid_elevations(self, minimal_data: dict) -> None:
        """Test validation rejects max <= min elevation."""
        minimal_data["elevation_max_m"] = 100.0  # less than min (150.0)

        with pytest.raises(
            InvalidParameterError, match="elevation_max_m.*must be greater"
        ):
            WatershedParameters(**minimal_data)

    def test_validation_invalid_cn(self, minimal_data: dict) -> None:
        """Test validation rejects CN outside 0-100 range."""
        minimal_data["cn"] = 150

        with pytest.raises(InvalidParameterError, match="cn must be 0-100"):
            WatershedParameters(**minimal_data)

    def test_validation_negative_slope(self, minimal_data: dict) -> None:
        """Test validation rejects negative slope."""
        minimal_data["mean_slope_m_per_m"] = -0.01

        with pytest.raises(
            InvalidParameterError, match="mean_slope_m_per_m must be non-negative"
        ):
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

    def test_calculate_tc_nrcs_requires_cn(self) -> None:
        """Test that NRCS method requires CN."""
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
            params.calculate_tc(method="nrcs")

    def test_calculate_tc_nrcs_with_cn(self) -> None:
        """Test NRCS method with CN."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            mean_slope_m_per_m=0.025,
            cn=72,
        )

        tc = params.calculate_tc(method="nrcs")

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

    def test_calculate_tc_unknown_method(
        self, params_with_slope: WatershedParameters
    ) -> None:
        """An unknown method is an InvalidParameterError that is also a ValueError."""
        with pytest.raises(InvalidParameterError, match="Unknown method") as caught:
            params_with_slope.calculate_tc(method="unknown")

        assert isinstance(caught.value, ValueError)
        assert caught.value.details == {
            "option": "method",
            "reason": "choice",
            "allowed": [
                "kirpich",
                "nrcs",
                "giandotti",
                "faa",
                "kerby",
                "kerby_kirpich",
            ],
            "value": "unknown",
        }

    @pytest.mark.parametrize(
        "method, missing",
        [
            ("nrcs", ["cn"]),
            ("faa", ["runoff_coeff", "overland_length_km", "overland_slope_m_per_m"]),
            ("kerby", ["retardance", "overland_length_km", "overland_slope_m_per_m"]),
            (
                "kerby_kirpich",
                [
                    "retardance",
                    "overland_length_km",
                    "overland_slope_m_per_m",
                    "channel_length_km",
                    "channel_slope_m_per_m",
                ],
            ),
        ],
    )
    def test_calculate_tc_missing_fields_are_named(
        self, params_with_slope: WatershedParameters, method: str, missing: list[str]
    ) -> None:
        """Every missing field is named in the error, which is also a ValueError."""
        with pytest.raises(InvalidParameterError) as caught:
            params_with_slope.calculate_tc(method=method)

        assert isinstance(caught.value, ValueError)
        assert caught.value.details == {
            "reason": "missing_field",
            "method": method,
            "missing": missing,
        }
        assert all(name in str(caught.value) for name in missing)

    def test_calculate_tc_lists_only_the_missing_fields(self) -> None:
        """Fields that are set are not reported as missing."""
        params = WatershedParameters(
            area_km2=45.0,
            perimeter_km=32.0,
            length_km=12.0,
            elevation_min_m=150.0,
            elevation_max_m=520.0,
            retardance=0.4,
            overland_length_km=0.25,
            channel_length_km=5.0,
        )

        with pytest.raises(InvalidParameterError) as caught:
            params.calculate_tc(method="kerby_kirpich")

        assert caught.value.details["missing"] == [
            "overland_slope_m_per_m",
            "channel_slope_m_per_m",
        ]

    def test_calculate_tc_giandotti_with_a_mean_elevation_of_zero(self) -> None:
        """0 m a.s.l. is a mean elevation, not "mean elevation not given".

        The elevation difference of Giandotti is mean - outlet = 30 m. With ``or`` the
        zero was replaced by the middle of the range (35 m): H = 65 m.
        """
        params = WatershedParameters(
            area_km2=150.0,
            perimeter_km=60.0,
            length_km=20.0,
            elevation_min_m=-30.0,
            elevation_max_m=100.0,
            elevation_mean_m=0.0,
        )

        tc = params.calculate_tc(method="giandotti")

        expected = ConcentrationTime.giandotti(
            area_km2=150.0, length_km=20.0, elevation_diff_m=30.0
        )
        assert tc == pytest.approx(expected, rel=1e-12)
        middle_of_range = ConcentrationTime.giandotti(
            area_km2=150.0, length_km=20.0, elevation_diff_m=65.0
        )
        assert tc != pytest.approx(middle_of_range)

    def test_calculate_tc_giandotti_defaults_the_mean_to_the_middle_of_the_range(
        self,
    ) -> None:
        """Without a mean elevation H = (max - min) / 2."""
        params = WatershedParameters(
            area_km2=150.0,
            perimeter_km=60.0,
            length_km=20.0,
            elevation_min_m=100.0,
            elevation_max_m=300.0,
        )

        expected = ConcentrationTime.giandotti(
            area_km2=150.0, length_km=20.0, elevation_diff_m=100.0
        )
        assert params.calculate_tc(method="giandotti") == pytest.approx(expected)

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


# The watershed of the review: a 10 km channel (slope 2.0 %) in a catchment with a
# 2.5 % land slope, whose overland flow path is 200 m long (slope 1.0 %).
REVIEW_WATERSHED = {
    "name": "Zlewnia X",
    "area_km2": 45.0,
    "perimeter_km": 32.0,
    "length_km": 12.0,
    "elevation_min_m": 150.0,
    "elevation_max_m": 520.0,
    "mean_slope_m_per_m": 0.025,
    "channel_length_km": 10.0,
    "channel_slope_m_per_m": 0.02,
    "cn": 72,
    "runoff_coeff": 0.5,
    "retardance": 0.4,
    "overland_length_km": 0.2,
    "overland_slope_m_per_m": 0.01,
}


class TestConcentrationTimeInputsOfAWatershed:
    """What ``calculate_tc`` feeds to each formula (TR-55 land slope, overland flow).

    FAA (1966, 2013) and Kerby (1959) are overland flow formulas: Kerby derived his
    for paths of up to 366 m (1200 ft; Roussel et al. 2005, TxDOT Report 0-4696-2),
    and the library warns for FAA outside 0.015-3 km. The length and slope of the
    channel gave a time far outside their range for every catchment with a channel.
    The NRCS lag equation takes the average land slope Y of the watershed, not the
    slope of the flow path (TR-55, chapter 3; NEH Part 630, chapter 15).
    """

    @pytest.fixture
    def watershed(self) -> WatershedParameters:
        return WatershedParameters.from_dict(REVIEW_WATERSHED)

    @staticmethod
    def without(*names: str) -> WatershedParameters:
        data = {k: v for k, v in REVIEW_WATERSHED.items() if k not in names}
        return WatershedParameters.from_dict(data)

    def test_faa_times_the_overland_flow_not_the_channel(
        self, watershed: WatershedParameters
    ) -> None:
        """FAA: 155.3 min (10 km "sheet flow", warned) -> 27.7 min (0.2 km)."""
        with pytest.warns(UserWarning) as warned:
            channel = ConcentrationTime.faa(
                length_km=10.0, slope_m_per_m=0.02, runoff_coeff=0.5
            )
        assert channel == pytest.approx(155.27, abs=0.01)  # what it used to return
        assert "length_km=10.0" in str(warned[0].message)

        tc = watershed.calculate_tc("faa")

        assert tc == pytest.approx(27.67, abs=0.01)
        assert tc == pytest.approx(
            ConcentrationTime.faa(length_km=0.2, slope_m_per_m=0.01, runoff_coeff=0.5)
        )

    def test_kerby_times_the_overland_flow_not_the_channel(
        self, watershed: WatershedParameters
    ) -> None:
        """Kerby: 173.2 min (10 km, two range warnings) -> 32.8 min (0.2 km)."""
        with pytest.warns(UserWarning):
            channel = ConcentrationTime.kerby(
                length_km=10.0, slope_m_per_m=0.02, retardance=0.4
            )
        assert channel == pytest.approx(173.23, abs=0.01)  # what it used to return

        tc = watershed.calculate_tc("kerby")

        assert tc == pytest.approx(32.77, abs=0.01)
        assert tc == pytest.approx(
            ConcentrationTime.kerby(length_km=0.2, slope_m_per_m=0.01, retardance=0.4)
        )

    def test_the_overland_flow_inputs_are_inside_the_range_of_the_formulas(
        self, watershed: WatershedParameters
    ) -> None:
        """No range warning: the overland path is what the formulas were made for."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            watershed.calculate_tc("faa")
            watershed.calculate_tc("kerby")

    def test_nrcs_takes_the_land_slope_before_the_channel_slope(
        self, watershed: WatershedParameters
    ) -> None:
        """NRCS: 463.9 min (Y = 2.0 % of the channel) -> 414.9 min (Y = 2.5 %)."""
        channel_slope = ConcentrationTime.nrcs(
            length_km=10.0, slope_m_per_m=0.02, cn=72
        )
        assert channel_slope == pytest.approx(463.85, abs=0.01)  # the former result

        tc = watershed.calculate_tc("nrcs")

        assert tc == pytest.approx(414.88, abs=0.01)
        assert tc == pytest.approx(
            ConcentrationTime.nrcs(length_km=10.0, slope_m_per_m=0.025, cn=72)
        )
        assert tc / channel_slope - 1 == pytest.approx(-0.106, abs=0.001)

    def test_kirpich_still_takes_the_channel_slope_first(
        self, watershed: WatershedParameters
    ) -> None:
        assert watershed.calculate_tc("kirpich") == pytest.approx(
            ConcentrationTime.kirpich(length_km=10.0, slope_m_per_m=0.02)
        )
        assert watershed.calculate_tc("kirpich") == pytest.approx(105.71, abs=0.01)

    def test_the_slope_falls_back_in_the_order_of_each_method(self) -> None:
        """NRCS: mean, channel, relief; Kirpich: channel, mean, relief."""
        no_mean = self.without("mean_slope_m_per_m")
        no_channel = self.without("channel_slope_m_per_m")
        neither = self.without("mean_slope_m_per_m", "channel_slope_m_per_m")
        relief = (520.0 - 150.0) / (10.0 * 1000.0)

        assert no_mean.tc_parameters("nrcs")["slope_m_per_m"] == 0.02
        assert no_channel.tc_parameters("nrcs")["slope_m_per_m"] == 0.025
        assert neither.tc_parameters("nrcs")["slope_m_per_m"] == pytest.approx(relief)
        assert no_mean.tc_parameters("kirpich")["slope_m_per_m"] == 0.02
        assert no_channel.tc_parameters("kirpich")["slope_m_per_m"] == 0.025
        assert neither.tc_parameters("kirpich")["slope_m_per_m"] == pytest.approx(
            relief
        )

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("kirpich", {"length_km": 10.0, "slope_m_per_m": 0.02}),
            ("nrcs", {"length_km": 10.0, "slope_m_per_m": 0.025, "cn": 72}),
            (
                "giandotti",
                {"area_km2": 45.0, "length_km": 10.0, "elevation_diff_m": 185.0},
            ),
            (
                "faa",
                {"length_km": 0.2, "slope_m_per_m": 0.01, "runoff_coeff": 0.5},
            ),
            (
                "kerby",
                {"length_km": 0.2, "slope_m_per_m": 0.01, "retardance": 0.4},
            ),
            (
                "kerby_kirpich",
                {
                    "overland_length_km": 0.2,
                    "overland_slope_m_per_m": 0.01,
                    "retardance": 0.4,
                    "channel_length_km": 10.0,
                    "channel_slope_m_per_m": 0.02,
                },
            ),
        ],
    )
    def test_tc_parameters_are_what_the_formula_receives(
        self, watershed: WatershedParameters, method: str, expected: dict
    ) -> None:
        """``calculate_tc`` is the formula applied to ``tc_parameters``, by design."""
        import warnings

        arguments = watershed.tc_parameters(method)

        assert arguments == pytest.approx(expected)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            formula = getattr(ConcentrationTime, method)
            assert formula(**arguments) == watershed.calculate_tc(method)

    def test_tc_parameters_report_the_same_errors_as_calculate_tc(self) -> None:
        bare = self.without("runoff_coeff", "overland_length_km", "cn")

        with pytest.raises(InvalidParameterError) as unknown:
            bare.tc_parameters("bogus")
        with pytest.raises(InvalidParameterError) as missing:
            bare.tc_parameters("faa")

        assert unknown.value.details["reason"] == "choice"
        assert missing.value.details["missing"] == [
            "runoff_coeff",
            "overland_length_km",
        ]

    @pytest.mark.parametrize("method", ["faa", "kerby"])
    def test_the_error_for_missing_overland_flow_says_what_to_do(
        self, method: str
    ) -> None:
        """No silent substitution of the channel: the hint names the alternatives."""
        data = self.without("overland_length_km", "overland_slope_m_per_m")

        with pytest.raises(InvalidParameterError) as caught:
            data.calculate_tc(method)

        assert caught.value.details["missing"] == [
            "overland_length_km",
            "overland_slope_m_per_m",
        ]
        assert "kerby_kirpich" in caught.value.hint
        assert "overland_length_km" in caught.value.hint

    def test_a_watershed_without_a_channel_is_timed_by_its_length(self) -> None:
        """Kirpich, NRCS and Giandotti use ``length_km`` when there is no channel."""
        data = self.without("channel_length_km", "channel_slope_m_per_m")

        assert data.tc_parameters("kirpich")["length_km"] == 12.0
        assert data.tc_parameters("nrcs")["length_km"] == 12.0
        assert data.tc_parameters("giandotti")["length_km"] == 12.0
        # the overland flow formulas do not depend on the channel at all
        assert data.tc_parameters("faa")["length_km"] == 0.2


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
