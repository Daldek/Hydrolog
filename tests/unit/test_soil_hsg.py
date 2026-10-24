"""Unit tests for hydrolog.soil.hsg (HSG classification and area statistics).

Ported from the Kartograf 0.8.0 tests of ``kartograf.hydrology.hsg`` (ADR-025).
"""

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

from hydrolog.exceptions import InvalidParameterError, MissingDependencyError
from hydrolog.soil import hsg_from_rasters, hsg_statistics
from hydrolog.soil.hsg import (
    HSG_CODES,
    HSG_DESCRIPTIONS,
    HsgGroupStatistics,
    HsgStatistics,
    classify_hsg,
    hsg_statistics_array,
)
from hydrolog.soil.texture import (
    TEXTURE_TO_HSG,
    classify_usda_texture,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestHsgConstants:
    """Tests for the HSG encoding and descriptions."""

    def test_codes_encode_groups_a_to_d_as_one_to_four(self):
        """Test the raster encoding shared with Kartograf (0 stays no data)."""
        assert HSG_CODES == {"A": 1, "B": 2, "C": 3, "D": 4}

    def test_every_group_has_a_polish_description(self):
        """Test that all groups have a non-empty Polish description."""
        assert list(HSG_DESCRIPTIONS) == list(HSG_CODES)
        for text in HSG_DESCRIPTIONS.values():
            assert "infiltracja" in text


class TestClassifyHsg:
    """Tests for classify_hsg."""

    @pytest.mark.parametrize(
        ("clay", "sand", "silt", "expected"),
        [
            (50, 900, 50, 1),  # sand -> A
            (200, 400, 400, 2),  # loam -> B
            (300, 300, 400, 3),  # clay loam -> C
            (450, 200, 350, 4),  # clay -> D
        ],
    )
    def test_g_per_kg_amounts(self, clay, sand, silt, expected):
        """Test the four groups from SoilGrids-style g/kg amounts."""
        result = classify_hsg([clay], [sand], [silt])

        assert result.tolist() == [expected]

    def test_unit_does_not_matter(self):
        """Test that percent and g/kg amounts give the same groups."""
        percent = np.array([[5.0, 20.0], [30.0, 45.0]])
        sand = np.array([[90.0, 40.0], [30.0, 20.0]])
        silt = np.array([[5.0, 40.0], [40.0, 35.0]])

        assert np.array_equal(
            classify_hsg(percent, sand, silt),
            classify_hsg(10 * percent, 10 * sand, 10 * silt),
        )

    def test_keeps_shape_and_returns_uint8(self):
        """Test that a 2-D int16 raster pair gives a 2-D uint8 grid."""
        clay = np.full((3, 4), 450, dtype=np.int16)
        sand = np.full((3, 4), 200, dtype=np.int16)
        silt = np.full((3, 4), 350, dtype=np.int16)

        result = classify_hsg(clay, sand, silt)

        assert result.shape == (3, 4)
        assert result.dtype == np.uint8
        assert np.all(result == 4)

    def test_scalar_amounts(self):
        """Test that plain numbers give a 0-d result."""
        assert int(classify_hsg(200, 400, 400)) == 2

    def test_texture_mapping_deviates_from_tr55_as_in_adr_025(self):
        """Test sandy_loam -> B and clay_loam / silty_clay_loam -> C (TR-55: A, D)."""
        sandy_loam = classify_hsg([10], [65], [25])
        clay_loam = classify_hsg([35], [30], [35])
        silty_clay_loam = classify_hsg([35], [10], [55])

        assert (sandy_loam.tolist(), clay_loam.tolist()) == ([2], [3])
        assert silty_clay_loam.tolist() == [3]

    def test_agrees_with_scalar_texture_and_table_on_whole_simplex(self):
        """Test classify_hsg == TEXTURE_TO_HSG[classify_usda_texture] on 5151 points."""
        points = [
            (clay, sand, 100 - clay - sand)
            for clay in range(0, 101)
            for sand in range(0, 101 - clay)
        ]
        clay, sand, silt = (
            np.array(axis, dtype=np.float64) for axis in zip(*points, strict=False)
        )

        result = classify_hsg(clay, sand, silt)

        expected = [
            HSG_CODES[TEXTURE_TO_HSG[classify_usda_texture(c, s, si)]]
            for c, s, si in points
        ]
        assert result.tolist() == expected

    def test_group_counts_on_the_g_per_kg_simplex_match_kartograf(self):
        """Test the points per group over the whole g/kg simplex (501 501 points).

        Reference: Kartograf 0.8.0 (ADR-025). Pins the texture -> HSG table together
        with the texture boundaries: moving sandy_loam to A, or clay_loam to D (the
        TR-55 table), changes these counts.
        """
        clay, sand = np.meshgrid(np.arange(1001.0), np.arange(1001.0))
        inside = clay + sand <= 1000
        clay, sand = clay[inside], sand[inside]
        silt = 1000 - clay - sand

        result = classify_hsg(clay, sand, silt)

        counts = np.bincount(result, minlength=5)
        assert counts.tolist() == [0, 22650, 192205, 96970, 189676]

    def test_nan_and_infinite_cells_are_no_data(self):
        """Test that NaN and +/-Inf in any input give 0, without warnings."""
        nan, inf = float("nan"), float("inf")
        clay = np.array([450.0, nan, 450.0, 450.0, -inf, 450.0])
        sand = np.array([200.0, 200.0, nan, 200.0, 200.0, 200.0])
        silt = np.array([350.0, 350.0, 350.0, inf, 350.0, 350.0])

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = classify_hsg(clay, sand, silt)

        assert result.tolist() == [4, 0, 0, 0, 0, 4]

    def test_all_zero_triplet_is_no_data(self):
        """Test that a cell with zero clay, sand and silt is a gap."""
        assert classify_hsg([0, 450], [0, 200], [0, 350]).tolist() == [0, 4]

    def test_zero_clay_with_sand_or_silt_is_not_a_gap(self):
        """Test that only an all-zero triplet is a gap: pure sand or silt is soil."""
        clay = np.array([[0.0, 0.0, 0.0]])
        sand = np.array([[1000.0, 0.0, 0.0]])
        silt = np.array([[0.0, 1000.0, 0.0]])

        pure_sand, pure_silt, gap = classify_hsg(clay, sand, silt)[0].tolist()

        assert (pure_sand, pure_silt, gap) == (1, 2, 0)  # sand -> A, silt -> B

    def test_tagged_nodata_masks_only_its_own_input(self):
        """Test that a nodata tag applies to its input, not to the others."""
        clay = np.array([300.0, 100.0])
        sand = np.array([300.0, 300.0])
        silt = np.array([400.0, 600.0])

        clay_tagged = classify_hsg(clay, sand, silt, nodata=(300.0, None, None))
        sand_tagged = classify_hsg(clay, sand, silt, nodata=(None, 300.0, None))

        assert clay_tagged.tolist() == [0, 2]  # only clay 300 is masked
        assert sand_tagged.tolist() == [0, 0]  # sand 300 occurs in both cells

    def test_negative_nodata_fill_is_masked_before_validation(self):
        """Test that -32768 fills (int16 nodata) give 0 and are not an error."""
        clay = np.full((3, 3), 300, dtype=np.int16)
        sand = np.full((3, 3), 300, dtype=np.int16)
        silt = np.full((3, 3), 400, dtype=np.int16)
        clay[1, 1] = -32768  # nodata in clay only
        for amounts in (clay, sand, silt):
            amounts[2, 2] = -32768  # nodata in all three

        result = classify_hsg(clay, sand, silt, nodata=(-32768, -32768, -32768))

        assert result[0, 0] == 3  # clay loam -> C
        assert result[1, 1] == 0
        assert result[2, 2] == 0
        assert np.count_nonzero(result) == 7

    def test_shared_classifier_masks_tag_nan_and_zero_triplets(self):
        """Test tag, NaN and all-zero cells together (Kartograf shared classifier)."""
        clay = np.array([[450.0, -1.0, 0.0, np.nan]], dtype=np.float32)
        sand = np.array([[200.0, 200.0, 0.0, 200.0]], dtype=np.float32)
        silt = np.array([[350.0, 350.0, 0.0, 350.0]], dtype=np.float32)

        result = classify_hsg(clay, sand, silt, nodata=(-1.0, None, None))

        assert result.dtype == np.uint8
        assert result.tolist() == [[4, 0, 0, 0]]

    @pytest.mark.parametrize("name", ["clay", "sand", "silt"])
    def test_untagged_negative_amount_raises(self, name):
        """Test that a negative amount that is not nodata raises."""
        amounts = {
            "clay": np.array([200.0, 200.0]),
            "sand": np.array([400.0, 400.0]),
            "silt": np.array([400.0, 400.0]),
        }
        amounts[name][1] = -5.0

        with pytest.raises(InvalidParameterError, match=f"{name} must not be") as e:
            classify_hsg(**amounts)

        assert e.value.details["option"] == name

    def test_shape_mismatch_raises(self):
        """Test that inputs of different shapes raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError, match="same shape"):
            classify_hsg(np.zeros((2, 2)), np.zeros((2, 3)), np.zeros((2, 2)))

    def test_nodata_must_have_one_value_per_input(self):
        """Test that a nodata tuple of the wrong length raises."""
        with pytest.raises(InvalidParameterError, match="nodata"):
            classify_hsg([1.0], [1.0], [1.0], nodata=(0.0, 0.0))  # type: ignore[arg-type]


class TestHsgStatisticsArray:
    """Tests for hsg_statistics_array."""

    def test_counts_areas_and_percents(self):
        """Test a 2x2 grid of 5x5 km cells: 2x A, 1x B, 1x C."""
        hsg = np.array([[1, 1], [2, 3]], dtype=np.uint8)

        stats = hsg_statistics_array(hsg, cell_area_m2=25e6)

        assert [stats.groups[g].count for g in "ABCD"] == [2, 1, 1, 0]
        assert stats.groups["A"].area_ha == pytest.approx(5000.0)
        assert stats.groups["B"].area_ha == pytest.approx(2500.0)
        assert stats.groups["A"].area_m2 == pytest.approx(50e6)
        assert stats.groups["A"].percent == pytest.approx(50.0)
        assert stats.groups["B"].percent == pytest.approx(25.0)
        assert stats.groups["D"].percent == 0.0
        assert stats.total_area_m2 == pytest.approx(100e6)
        assert stats.valid_area_m2 == pytest.approx(100e6)

    def test_groups_use_cells_with_data_nodata_uses_all_cells(self):
        """Test percent of the groups = share of valid area, nodata = of the total."""
        hsg = np.array([[2, 0, 0, 0], [2, 0, 0, 0]], dtype=np.uint8)

        stats = hsg_statistics_array(hsg, cell_area_m2=1e4)

        assert stats.groups["B"].percent == 100.0
        assert stats.groups["B"].count == 2
        assert stats.nodata.count == 6
        assert stats.nodata.percent == 75.0
        assert stats.nodata.area_ha == pytest.approx(3 * stats.groups["B"].area_ha)
        assert stats.valid_area_m2 == pytest.approx(2e4)

    def test_all_no_data_has_zero_group_percents(self):
        """Test that a grid without data gives 0 % for the groups, 100 % no data."""
        stats = hsg_statistics_array(np.zeros((2, 2), dtype=np.uint8), 100.0)

        assert all(group.percent == 0.0 for group in stats.groups.values())
        assert stats.nodata.percent == 100.0
        assert stats.valid_area_m2 == 0.0

    def test_cell_area_per_row(self):
        """Test one cell area per row (geographic rasters): area follows the row."""
        hsg = np.array([[1, 2], [1, 1]], dtype=np.uint8)

        stats = hsg_statistics_array(hsg, cell_area_m2=[100.0, 300.0])

        assert stats.groups["A"].area_m2 == pytest.approx(100 + 300 + 300)
        assert stats.groups["B"].area_m2 == pytest.approx(100)
        assert stats.groups["A"].count == 3

    def test_cell_area_per_cell(self):
        """Test a cell area array of the shape of the grid."""
        hsg = np.array([[1, 2], [1, 1]], dtype=np.uint8)
        areas = np.array([[10.0, 20.0], [30.0, 40.0]])

        stats = hsg_statistics_array(hsg, areas)

        assert stats.groups["A"].area_m2 == pytest.approx(10 + 30 + 40)
        assert stats.groups["B"].area_m2 == pytest.approx(20)

    def test_share_weights_the_areas_and_selects_the_counted_cells(self):
        """Test that cells count with their share inside the area; share 0 = absent."""
        hsg = np.array([[1, 2, 2], [0, 0, 1]], dtype=np.uint8)
        share = np.array([[0.5, 1.0, 0.0], [1.0, 0.5, 0.0]])

        stats = hsg_statistics_array(hsg, cell_area_m2=100.0, share=share)

        assert stats.groups["A"].area_m2 == pytest.approx(50.0)
        assert stats.groups["A"].count == 1  # the A cell with share 0 is not counted
        assert stats.groups["B"].area_m2 == pytest.approx(100.0)
        assert stats.groups["B"].count == 1
        assert stats.nodata.area_m2 == pytest.approx(150.0)
        assert stats.nodata.count == 2
        assert stats.total_area_m2 == pytest.approx(300.0)
        assert stats.groups["A"].percent == pytest.approx(50.0 / 150.0 * 100)
        assert stats.nodata.percent == pytest.approx(50.0)

    def test_zero_share_everywhere_gives_zero_areas_and_percents(self):
        """Test that an area missing the grid gives zeros, not a division error."""
        hsg = np.array([[1, 2], [0, 3]], dtype=np.uint8)

        stats = hsg_statistics_array(hsg, 100.0, share=np.zeros((2, 2)))

        assert stats.total_area_m2 == 0.0
        assert all(g.count == 0 and g.percent == 0.0 for g in stats.groups.values())
        assert stats.nodata.percent == 0.0

    @pytest.mark.parametrize("seed", range(4))
    def test_invariants_on_random_grids(self, seed):
        """Test that areas, percents and counts add up on random grids."""
        rng = np.random.default_rng(seed)
        hsg = rng.integers(0, 5, size=(17, 23)).astype(np.uint8)
        row_areas = rng.uniform(100.0, 2000.0, size=17)
        share = rng.uniform(0.0, 1.0, size=(17, 23))
        share[rng.random((17, 23)) < 0.3] = 0.0
        weight = row_areas[:, None] * share

        stats = hsg_statistics_array(hsg, row_areas, share=share)

        everything = [*stats.groups.values(), stats.nodata]
        assert sum(c.area_m2 for c in everything) == pytest.approx(stats.total_area_m2)
        assert stats.total_area_m2 == pytest.approx(weight.sum())
        assert stats.valid_area_m2 == pytest.approx(weight[hsg > 0].sum())
        assert sum(g.area_m2 for g in stats.groups.values()) == pytest.approx(
            stats.valid_area_m2
        )
        assert sum(g.percent for g in stats.groups.values()) == pytest.approx(100.0)
        assert stats.nodata.percent == pytest.approx(
            100 * (1 - stats.valid_area_m2 / stats.total_area_m2)
        )
        assert sum(c.count for c in everything) == int(np.count_nonzero(share))
        for name, code in HSG_CODES.items():
            assert stats.groups[name].area_m2 == pytest.approx(
                weight[hsg == code].sum()
            )
        for cell in everything:
            assert cell.area_ha == pytest.approx(cell.area_m2 / 1e4)

    @pytest.mark.parametrize(
        "hsg",
        [
            np.array([[1.0, 2.0]]),  # not integer codes
            np.array([[1, 5]]),  # code above D
            np.array([[1, -1]], dtype=np.int16),  # negative code
        ],
    )
    def test_invalid_hsg_raises(self, hsg):
        """Test that anything but integer codes 0-4 is rejected."""
        with pytest.raises(InvalidParameterError, match="hsg"):
            hsg_statistics_array(hsg, 100.0)

    @pytest.mark.parametrize(
        "cell_area",
        [0.0, -1.0, float("nan"), [100.0, 100.0, 100.0], np.ones((3, 3)), "big"],
    )
    def test_invalid_cell_area_raises(self, cell_area):
        """Test that non-positive, non-finite or misshapen cell areas are rejected."""
        hsg = np.ones((2, 2), dtype=np.uint8)
        with pytest.raises(InvalidParameterError, match="cell_area_m2"):
            hsg_statistics_array(hsg, cell_area)

    @pytest.mark.parametrize(
        "share",
        [
            np.ones((2, 3)),  # wrong shape
            np.full((2, 2), 1.5),  # above 1
            np.full((2, 2), -0.1),  # below 0
            np.full((2, 2), np.nan),  # not a number
        ],
    )
    def test_invalid_share_raises(self, share):
        """Test that a share must have the grid shape and values from 0 to 1."""
        hsg = np.ones((2, 2), dtype=np.uint8)
        with pytest.raises(InvalidParameterError, match="share"):
            hsg_statistics_array(hsg, 100.0, share=share)


class TestHsgStatisticsSerialization:
    """Tests for the JSON form of HsgStatistics."""

    def test_to_dict_layout(self):
        """Test the field names and order of the JSON document."""
        stats = hsg_statistics_array(np.array([[1, 2, 0]], dtype=np.uint8), 100.0)

        data = stats.to_dict()

        assert list(data) == ["groups", "nodata", "total_area_m2", "valid_area_m2"]
        assert list(data["groups"]) == ["A", "B", "C", "D"]
        assert list(data["groups"]["A"]) == ["count", "area_m2", "area_ha", "percent"]
        assert data["groups"]["A"] == {
            "count": 1,
            "area_m2": 100.0,
            "area_ha": 0.01,
            "percent": 50.0,
        }
        assert data["nodata"]["count"] == 1
        assert data["total_area_m2"] == 300.0

    def test_json_round_trip(self):
        """Test that to_json() is valid JSON equal to to_dict()."""
        stats = hsg_statistics_array(np.array([[1, 4], [3, 0]], dtype=np.uint8), 62.5)

        assert json.loads(stats.to_json()) == stats.to_dict()

    def test_group_statistics_are_results_too(self):
        """Test that a single group serialises on its own."""
        group = HsgGroupStatistics(count=2, area_m2=10.0, area_ha=0.001, percent=5.0)

        assert group.to_dict() == {
            "count": 2,
            "area_m2": 10.0,
            "area_ha": 0.001,
            "percent": 5.0,
        }
        assert isinstance(
            hsg_statistics_array(np.zeros((1, 1), dtype=np.uint8), 1.0), HsgStatistics
        )


class TestRasterExtraIsOptional:
    """The numpy-only modules work without rasterio and pyproj (extra [raster])."""

    def test_importing_the_package_loads_no_raster_library(self):
        """Test that rasterio and pyproj are imported lazily, only when used."""
        code = (
            "import sys\n"
            "import hydrolog.soil\n"
            "from hydrolog.soil import classify_hsg\n"
            "assert classify_hsg([200], [400], [400]).tolist() == [2]\n"
            "assert 'rasterio' not in sys.modules and 'pyproj' not in sys.modules\n"
        )
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

        result = subprocess.run(
            [sys.executable, "-c", code], env=env, capture_output=True, text=True
        )

        assert result.returncode == 0, result.stderr

    @pytest.mark.parametrize("missing", ["rasterio", "pyproj"])
    def test_raster_functions_raise_missing_dependency_error(
        self, monkeypatch, tmp_path, missing
    ):
        """Test MissingDependencyError with the install hint when the extra is
        absent."""
        monkeypatch.setitem(sys.modules, missing, None)  # makes the import fail

        with pytest.raises(MissingDependencyError) as from_rasters:
            hsg_from_rasters(
                tmp_path / "clay.tif",
                tmp_path / "sand.tif",
                tmp_path / "silt.tif",
                tmp_path / "hsg.tif",
            )
        with pytest.raises(MissingDependencyError) as statistics:
            hsg_statistics(tmp_path / "hsg.tif")

        for caught in (from_rasters.value, statistics.value):
            assert caught.code == "missing_dependency"
            assert caught.hint == "pip install hydrolog[raster]"
            assert caught.details["package"] == missing
