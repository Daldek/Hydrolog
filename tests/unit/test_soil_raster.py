"""Unit tests for hydrolog.soil.raster (HSG GeoTIFF input/output, extra [raster]).

Ported from the Kartograf 0.8.0 tests of ``kartograf.hydrology.hsg`` (ADR-025). The
tests are skipped when ``rasterio`` or ``pyproj`` is not installed.
"""

import json
import math

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
pyproj = pytest.importorskip("pyproj")

from rasterio.transform import Affine, from_origin  # noqa: E402

from hydrolog.exceptions import (  # noqa: E402
    InputDataError,
    InvalidParameterError,
    NotFoundError,
    OutputError,
)
from hydrolog.soil.hsg import hsg_statistics_array  # noqa: E402
from hydrolog.soil.raster import (  # noqa: E402
    HsgRasterResult,
    hsg_from_rasters,
    hsg_statistics,
)

_WGS84_A = 6378137.0
_WGS84_E2 = (1 / 298.257223563) * (2 - 1 / 298.257223563)


def _write_raster(
    path, data, *, crs="EPSG:2180", transform=None, nodata=None, **options
):
    """Write a single-band GeoTIFF with the dtype of ``data``."""
    if transform is None:
        transform = from_origin(500000, 600000, 250, 250)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        dtype=data.dtype,
        count=1,
        width=data.shape[1],
        height=data.shape[0],
        crs=crs,
        transform=transform,
        nodata=nodata,
        **options,
    ) as dst:
        dst.write(data, 1)
    return path


def _write_truncated(path, dtype, low, high):
    """Write a compressed, tiled 400 x 400 raster of random values, cut in half."""
    rng = np.random.default_rng(0)
    data = rng.integers(low, high, size=(400, 400)).astype(dtype)
    _write_raster(
        path, data, compress="deflate", tiled=True, blockxsize=256, blockysize=256
    )
    content = path.read_bytes()
    path.write_bytes(content[: len(content) // 2])
    return path


def _soil(tmp_path, clay, sand, silt, *, shape=(4, 5), **kwargs):
    """Write clay, sand and silt rasters (int16; scalar amounts fill ``shape``)."""
    paths = []
    for name, amount in (("clay", clay), ("sand", sand), ("silt", silt)):
        data = np.broadcast_to(np.asarray(amount, dtype=np.int16), shape).copy()
        paths.append(_write_raster(tmp_path / f"{name}.tif", data, **kwargs))
    return paths


def _read(path):
    with rasterio.open(path) as src:
        return src.read(1)


def _hsg_raster(tmp_path, data, name="hsg.tif", **kwargs):
    """Write an HSG raster (uint8, nodata 0), by default 100 m cells in EPSG:2180."""
    kwargs.setdefault(
        "transform", from_origin(450000, 550000 + 100 * len(data), 100, 100)
    )
    return _write_raster(
        tmp_path / name, np.asarray(data, dtype=np.uint8), nodata=0, **kwargs
    )


def _graticule_area_m2(west, south, east, north):
    """Exact area (m2) of a lon/lat rectangle on the WGS84 ellipsoid (authalic)."""

    def q(latitude):
        s = math.sin(math.radians(latitude))
        e = math.sqrt(_WGS84_E2)
        return (1 - _WGS84_E2) * (
            s / (1 - _WGS84_E2 * s * s) - math.log((1 - e * s) / (1 + e * s)) / (2 * e)
        )

    return _WGS84_A**2 / 2 * math.radians(east - west) * (q(north) - q(south))


def _assert_close(actual, expected):
    """Compare two ``to_dict()`` documents, floats approximately."""
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        if isinstance(value, dict):
            _assert_close(actual[key], value)
        else:
            assert actual[key] == pytest.approx(value), key


class TestHsgFromRasters:
    """Tests for hsg_from_rasters."""

    def test_writes_an_hsg_geotiff_on_the_grid_of_the_inputs(self, tmp_path):
        """Test the output profile: uint8, nodata 0, Deflate, grid of the inputs."""
        paths = _soil(tmp_path, 450, 200, 350, shape=(20, 20))  # clay -> D
        out = tmp_path / "hsg.tif"

        result = hsg_from_rasters(*paths, out)

        with rasterio.open(out) as src:
            assert src.dtypes == ("uint8",)
            assert src.count == 1
            assert src.nodata == 0
            assert src.profile["compress"].lower() == "deflate"
            assert src.crs.to_string() == "EPSG:2180"
            assert src.transform == from_origin(500000, 600000, 250, 250)
            data = src.read(1)
        assert data.shape == (20, 20)
        assert np.all(data == 4)
        assert result == HsgRasterResult(
            output_path=out,
            shape=(20, 20),
            crs="EPSG:2180",
            counts={"A": 0, "B": 0, "C": 0, "D": 400, "nodata": 0},
        )

    def test_band_tags_as_in_kartograf(self, tmp_path):
        """Test the band tags LAYER_NAME and LAYER_DESCRIPTION."""
        out = tmp_path / "hsg.tif"

        hsg_from_rasters(*_soil(tmp_path, 200, 400, 400), out)

        with rasterio.open(out) as src:
            assert src.tags(1) == {
                "LAYER_NAME": "Hydrologic Soil Group",
                "LAYER_DESCRIPTION": "HSG classification: 1=A, 2=B, 3=C, 4=D",
            }

    def test_every_group_and_no_data_in_one_raster(self, tmp_path):
        """Test the classes of a mixed raster and the counts per class."""
        clay = np.array([[50, 200, 300], [450, 0, 100]], dtype=np.int16)
        sand = np.array([[900, 400, 300], [200, 0, 300]], dtype=np.int16)
        silt = np.array([[50, 400, 400], [350, 0, 600]], dtype=np.int16)
        paths = [
            _write_raster(tmp_path / f"{n}.tif", a)
            for n, a in (("clay", clay), ("sand", sand), ("silt", silt))
        ]
        out = tmp_path / "hsg.tif"

        result = hsg_from_rasters(*paths, out)

        # sand A, loam B, clay loam C / clay D, all-zero gap, silt loam B
        assert _read(out).tolist() == [[1, 2, 3], [4, 0, 2]]
        assert result.counts == {"A": 1, "B": 2, "C": 1, "D": 1, "nodata": 1}
        assert result.shape == (2, 3)

    def test_unit_of_the_inputs_does_not_matter(self, tmp_path):
        """Test that percent rasters (float) give the HSG of the g/kg rasters."""
        grams = _soil(tmp_path, 450, 200, 350)
        percent = [
            _write_raster(
                tmp_path / f"{n}_pct.tif", np.full((4, 5), v, dtype=np.float32)
            )
            for n, v in (("clay", 45.0), ("sand", 20.0), ("silt", 35.0))
        ]

        hsg_from_rasters(*grams, tmp_path / "a.tif")
        hsg_from_rasters(*percent, tmp_path / "b.tif")

        assert np.array_equal(_read(tmp_path / "a.tif"), _read(tmp_path / "b.tif"))
        assert np.all(_read(tmp_path / "a.tif") == 4)

    def test_all_zero_inputs_are_all_no_data(self, tmp_path):
        """Test that an all-zero triplet is a gap in every cell."""
        out = tmp_path / "hsg.tif"

        result = hsg_from_rasters(*_soil(tmp_path, 0, 0, 0), out)

        assert np.all(_read(out) == 0)
        assert result.counts["nodata"] == 20

    def test_tagged_nodata_masks_cells(self, tmp_path):
        """Test that a nodata tag makes the cell a gap in the output."""
        clay = _write_raster(
            tmp_path / "clay_tagged.tif",
            np.full((4, 5), -1, dtype=np.int16),
            nodata=-1,
        )
        _, sand, silt = _soil(tmp_path, 0, 200, 350)
        out = tmp_path / "hsg.tif"

        hsg_from_rasters(clay, sand, silt, out)

        assert np.all(_read(out) == 0)

    def test_int16_nodata_in_some_cells_only(self, tmp_path):
        """Test that SoilGrids-style -32768 cells become gaps, the rest is classified."""
        arrays = {}
        for name, fill in {"clay": 300, "sand": 300, "silt": 400}.items():
            data = np.full((3, 3), fill, dtype=np.int16)
            if name == "clay":
                data[1, 1] = -32768  # nodata in clay only
            data[2, 2] = -32768  # nodata in all three
            arrays[name] = _write_raster(tmp_path / f"{name}.tif", data, nodata=-32768)
        out = tmp_path / "hsg.tif"

        hsg_from_rasters(arrays["clay"], arrays["sand"], arrays["silt"], out)

        hsg = _read(out)
        assert hsg[0, 0] == 3  # clay loam -> C
        assert hsg[1, 1] == 0
        assert hsg[2, 2] == 0
        assert np.count_nonzero(hsg) == 7

    def test_nan_masks_cells_without_a_tag(self, tmp_path):
        """Test that NaN cells of an untagged float raster become gaps."""
        arrays = []
        for name, fill in {"clay": 300.0, "sand": 300.0, "silt": 400.0}.items():
            data = np.full((3, 3), fill, dtype=np.float32)
            if name == "sand":
                data[1, 1] = np.nan
            arrays.append(_write_raster(tmp_path / f"{name}.tif", data))
        out = tmp_path / "hsg.tif"

        hsg_from_rasters(*arrays, out)

        hsg = _read(out)
        assert hsg[1, 1] == 0
        assert np.all(np.delete(hsg.reshape(-1), 4) > 0)

    def test_untagged_negative_amounts_raise_input_data_error(self, tmp_path):
        """Test that a negative fill without a nodata tag is a data error."""
        data = np.full((4, 5), 200, dtype=np.int16)
        data[1, 1] = -9999
        clay = _write_raster(tmp_path / "clay_negative.tif", data)
        _, sand, silt = _soil(tmp_path, 0, 400, 400)
        out = tmp_path / "out" / "hsg.tif"

        with pytest.raises(InputDataError, match="clay must not be negative") as e:
            hsg_from_rasters(clay, sand, silt, out)

        assert "nodata" in e.value.hint
        assert e.value.details == {"layer": "clay", "value": -9999.0}
        assert not out.parent.exists()

    def test_different_shape_raises_input_data_error(self, tmp_path):
        """Test that rasters of different size are rejected, nothing is written."""
        clay, _, silt = _soil(tmp_path, 450, 200, 350, shape=(20, 20))
        sand = _write_raster(tmp_path / "sand.tif", np.full((20, 10), 200, np.int16))
        out = tmp_path / "out" / "hsg.tif"

        with pytest.raises(
            InputDataError, match="clay and sand rasters differ in shape"
        ) as e:
            hsg_from_rasters(clay, sand, silt, out)

        assert e.value.code == "data_error"
        assert e.value.details == {"property": "shape", "layers": ["clay", "sand"]}
        assert not out.parent.exists()  # the directory appears only on success

    def test_different_crs_raises_input_data_error(self, tmp_path):
        """Test that rasters in different CRS are rejected."""
        clay, sand, _ = _soil(tmp_path, 450, 200, 350)
        silt = _write_raster(
            tmp_path / "silt.tif", np.full((4, 5), 350, np.int16), crs="EPSG:2178"
        )

        with pytest.raises(InputDataError, match="clay and silt rasters differ in CRS"):
            hsg_from_rasters(clay, sand, silt, tmp_path / "hsg.tif")

    def test_shifted_grid_raises_input_data_error(self, tmp_path):
        """Test that a grid shifted by half a cell is a transform mismatch."""
        clay, _, silt = _soil(tmp_path, 450, 200, 350)
        sand = _write_raster(
            tmp_path / "sand.tif",
            np.full((4, 5), 200, np.int16),
            transform=from_origin(500125, 600000, 250, 250),
        )

        with pytest.raises(InputDataError, match="differ in transform") as e:
            hsg_from_rasters(clay, sand, silt, tmp_path / "hsg.tif")

        assert e.value.details["property"] == "transform"
        assert "gdalwarp" in e.value.hint

    def test_transforms_within_a_millionth_of_a_cell_are_the_same_grid(self, tmp_path):
        """Test that float noise in the origin does not make the grids differ."""
        clay, _, silt = _soil(tmp_path, 450, 200, 350)
        sand = _write_raster(
            tmp_path / "sand.tif",
            np.full((4, 5), 200, np.int16),
            transform=from_origin(500000 + 250e-9, 600000, 250, 250),
        )
        out = tmp_path / "hsg.tif"

        hsg_from_rasters(clay, sand, silt, out)

        assert np.all(_read(out) == 4)

    def test_missing_input_raises_not_found(self, tmp_path):
        """Test NotFoundError for an input that does not exist."""
        _, sand, silt = _soil(tmp_path, 450, 200, 350)

        with pytest.raises(NotFoundError, match="clay raster does not exist") as e:
            hsg_from_rasters(tmp_path / "missing.tif", sand, silt, tmp_path / "o.tif")

        assert e.value.code == "not_found"

    def test_unreadable_input_raises_input_data_error(self, tmp_path):
        """Test InputDataError for a file that is not a raster."""
        clay, sand, silt = _soil(tmp_path, 450, 200, 350)
        clay.write_text("this is not a GeoTIFF")

        with pytest.raises(InputDataError, match="Cannot read the clay raster"):
            hsg_from_rasters(clay, sand, silt, tmp_path / "hsg.tif")

    def test_truncated_input_raises_input_data_error(self, tmp_path):
        """Test that a truncated download is an InputDataError, not a raw GDAL error."""
        _, sand, silt = _soil(tmp_path, 0, 300, 400, shape=(400, 400))
        clay = _write_truncated(tmp_path / "clay_cut.tif", np.int16, 100, 400)
        out = tmp_path / "out" / "hsg.tif"

        with pytest.raises(
            InputDataError, match="Cannot read the data of the clay"
        ) as e:
            hsg_from_rasters(clay, sand, silt, out)

        assert "truncated" in e.value.hint
        assert not out.parent.exists()

    @pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
    def test_input_without_crs_raises_input_data_error(self, tmp_path):
        """Test that a raster without CRS is rejected (areas would be unknown)."""
        clay, sand, _ = _soil(tmp_path, 450, 200, 350)
        silt = _write_raster(
            tmp_path / "silt.tif", np.full((4, 5), 350, np.int16), crs=None
        )

        with pytest.raises(InputDataError, match="no coordinate reference system"):
            hsg_from_rasters(clay, sand, silt, tmp_path / "hsg.tif")

    def test_output_must_not_be_an_input(self, tmp_path):
        """Test that the output cannot overwrite an input raster."""
        clay, sand, silt = _soil(tmp_path, 450, 200, 350)
        before = sand.read_bytes()

        with pytest.raises(InvalidParameterError, match="sand input raster") as e:
            hsg_from_rasters(clay, sand, silt, sand)

        assert e.value.details["option"] == "output_path"
        assert sand.read_bytes() == before

    def test_creates_missing_directories_and_replaces_an_existing_file(self, tmp_path):
        """Test the output directory, the replaced file and the absence of leftovers."""
        paths = _soil(tmp_path, 450, 200, 350)
        out = tmp_path / "deep" / "er" / "hsg.tif"
        out.parent.mkdir(parents=True)
        out.write_text("stale")

        hsg_from_rasters(*paths, out)

        assert np.all(_read(out) == 4)
        assert [p.name for p in out.parent.iterdir()] == ["hsg.tif"]

    def test_unwritable_output_raises_output_error(self, tmp_path):
        """Test OutputError (io_error) when the output directory cannot be made."""
        paths = _soil(tmp_path, 450, 200, 350)
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory is needed")

        with pytest.raises(OutputError, match="Cannot write the HSG raster") as e:
            hsg_from_rasters(*paths, blocker / "hsg.tif")

        assert e.value.code == "io_error"
        assert blocker.read_text() == "a file where a directory is needed"

    def test_result_is_json_serializable(self, tmp_path):
        """Test the JSON form of the result."""
        out = tmp_path / "hsg.tif"

        result = hsg_from_rasters(*_soil(tmp_path, 450, 200, 350), out)

        data = json.loads(result.to_json())
        assert data == {
            "output_path": out.as_posix(),
            "shape": [4, 5],
            "crs": "EPSG:2180",
            "counts": {"A": 0, "B": 0, "C": 0, "D": 20, "nodata": 0},
        }

    def test_output_feeds_hsg_statistics(self, tmp_path):
        """Test that the written raster summarises to the counts of the result."""
        clay = np.array([[50, 200], [450, 0]], dtype=np.int16)
        sand = np.array([[900, 400], [200, 0]], dtype=np.int16)
        silt = np.array([[50, 400], [350, 0]], dtype=np.int16)
        paths = [
            _write_raster(tmp_path / f"{n}.tif", a)
            for n, a in (("clay", clay), ("sand", sand), ("silt", silt))
        ]
        out = tmp_path / "hsg.tif"

        result = hsg_from_rasters(*paths, out)
        stats = hsg_statistics(out)

        for group in "ABCD":
            assert stats.groups[group].count == result.counts[group]
            assert stats.groups[group].area_m2 == pytest.approx(
                result.counts[group] * 250 * 250
            )
        assert stats.nodata.count == result.counts["nodata"] == 1


class TestHsgStatistics:
    """Tests for hsg_statistics without a bbox."""

    def test_counts_and_percents(self, tmp_path):
        """Test counts and percents of a 2x2 raster: 2x A, 1x B, 1x C."""
        path = _hsg_raster(
            tmp_path,
            [[1, 1], [2, 3]],
            transform=from_origin(450000, 560000, 5000, 5000),
        )

        stats = hsg_statistics(path)

        assert [stats.groups[g].count for g in "ABCD"] == [2, 1, 1, 0]
        assert stats.groups["A"].percent == pytest.approx(50.0)
        assert stats.groups["B"].percent == pytest.approx(25.0)

    def test_projected_crs_uses_the_affine_cell_area(self, tmp_path):
        """Test a metric CRS: 2x2 raster over 10x10 km -> 5x5 km cells = 2500 ha each."""
        path = _hsg_raster(
            tmp_path,
            [[1, 1], [2, 3]],
            transform=from_origin(450000, 560000, 5000, 5000),
        )

        stats = hsg_statistics(path)

        assert stats.groups["A"].area_ha == pytest.approx(5000.0)
        assert stats.groups["B"].area_ha == pytest.approx(2500.0)
        assert stats.total_area_m2 == pytest.approx(100e6)

    def test_no_data_entry(self, tmp_path):
        """Test that the groups use the cells with data and no data uses all cells."""
        path = _hsg_raster(tmp_path, [[2, 0, 0, 0], [2, 0, 0, 0]])

        stats = hsg_statistics(path)

        assert stats.groups["B"].percent == 100.0
        assert stats.groups["B"].count == 2
        assert stats.nodata.count == 6
        assert stats.nodata.percent == 75.0
        assert stats.nodata.area_ha == pytest.approx(3 * stats.groups["B"].area_ha)

    def test_geographic_crs_area_is_geodetic_not_square_degrees(self, tmp_path):
        """Test that an EPSG:4326 raster is measured on the ellipsoid (vs exact area)."""
        res = 0.0022457  # ~250 m in latitude
        data = np.full((100, 100), 2, dtype=np.uint8)
        path = _hsg_raster(
            tmp_path, data, crs="EPSG:4326", transform=from_origin(22.7, 52.5, res, res)
        )
        expected_m2 = _graticule_area_m2(22.7, 52.5 - 100 * res, 22.7 + 100 * res, 52.5)

        stats = hsg_statistics(path)

        assert stats.groups["B"].count == 10000
        assert stats.groups["B"].area_m2 == pytest.approx(expected_m2, rel=1e-4)
        assert stats.groups["B"].area_ha == pytest.approx(expected_m2 / 1e4, rel=1e-4)
        assert stats.groups["B"].percent == 100.0

    def test_geographic_cell_area_follows_the_latitude_of_the_row(self, tmp_path):
        """Test that the cells of a row at a lower latitude are larger."""
        res = 0.05
        data = np.array([[1] * 10] * 10 + [[2] * 10] * 10, dtype=np.uint8)  # A north
        path = _hsg_raster(
            tmp_path, data, crs="EPSG:4326", transform=from_origin(20.0, 60.0, res, res)
        )

        stats = hsg_statistics(path)

        north = _graticule_area_m2(20.0, 59.5, 20.5, 60.0)
        south = _graticule_area_m2(20.0, 59.0, 20.5, 59.5)
        assert stats.groups["A"].area_m2 == pytest.approx(north, rel=2e-4)
        assert stats.groups["B"].area_m2 == pytest.approx(south, rel=2e-4)
        assert stats.groups["A"].area_m2 < stats.groups["B"].area_m2

    def test_length_unit_of_the_crs_is_converted_to_metres(self, tmp_path):
        """Test a CRS in US survey feet: 100 x 100 ft cells are 929 m2, not 10 000."""
        path = _hsg_raster(
            tmp_path,
            np.ones((10, 10), dtype=np.uint8),
            crs="EPSG:2278",
            transform=from_origin(3000000, 13000000, 100, 100),
        )

        stats = hsg_statistics(path)

        assert stats.total_area_m2 == pytest.approx(100 * 1e4 * 0.3048006096012192**2)

    def test_not_an_hsg_raster_raises_input_data_error(self, tmp_path):
        """Test that a float raster or codes above 4 are not an HSG raster."""
        floats = _write_raster(tmp_path / "f.tif", np.full((2, 2), 1.0, np.float32))
        wide = _write_raster(tmp_path / "w.tif", np.array([[1, 9], [2, 3]], np.uint8))

        for path in (floats, wide):
            with pytest.raises(InputDataError, match="not a valid HSG raster") as e:
                hsg_statistics(path)
            assert e.value.details == {"path": str(path)}

    @pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
    def test_raster_without_crs_raises_input_data_error(self, tmp_path):
        """Test that areas cannot be given for a raster without CRS."""
        path = _write_raster(tmp_path / "x.tif", np.ones((2, 2), np.uint8), crs=None)

        with pytest.raises(InputDataError, match="no coordinate reference system"):
            hsg_statistics(path)

    def test_rotated_geographic_raster_is_rejected(self, tmp_path):
        """Test that per-row cell areas are not applied to a rotated raster."""
        path = _write_raster(
            tmp_path / "rot.tif",
            np.ones((5, 5), np.uint8),
            crs="EPSG:4326",
            transform=from_origin(22.7, 52.5, 0.01, 0.01) * Affine.rotation(5),
        )

        with pytest.raises(InputDataError, match="Rotated rasters"):
            hsg_statistics(path)

    def test_missing_file_raises_not_found(self, tmp_path):
        """Test NotFoundError for a path that does not exist."""
        with pytest.raises(NotFoundError, match="does not exist"):
            hsg_statistics(tmp_path / "nope.tif")

    def test_unreadable_file_raises_input_data_error(self, tmp_path):
        """Test InputDataError for a file that is not a raster."""
        path = tmp_path / "text.tif"
        path.write_text("this is not a GeoTIFF")

        with pytest.raises(InputDataError, match="Cannot read the HSG raster"):
            hsg_statistics(path)

    def test_truncated_file_raises_input_data_error(self, tmp_path):
        """Test that a truncated download is an InputDataError, not a raw GDAL error."""
        path = _write_truncated(tmp_path / "hsg_cut.tif", np.uint8, 0, 5)

        with pytest.raises(
            InputDataError, match="Cannot read the data of the HSG"
        ) as e:
            hsg_statistics(path)

        assert "truncated" in e.value.hint


class TestHsgStatisticsBbox:
    """Tests for hsg_statistics with a bbox (cells count with their share inside)."""

    @staticmethod
    def _edge_raster(tmp_path):
        # 4 x 4 cells of 100 m; column 0 without data, one A cell (NE corner)
        data = np.full((4, 4), 2, dtype=np.uint8)
        data[:, 0] = 0
        data[0, 3] = 1
        return _hsg_raster(
            tmp_path, data, transform=from_origin(450000, 550400, 100, 100)
        )

    def test_cells_count_with_their_share_inside_the_bbox(self, tmp_path):
        """Test the bbox as the area: edge cells are cut, the areas add up to it."""
        path = self._edge_raster(tmp_path)
        # 300 x 300 m = 9 ha, cutting every edge cell in half
        bbox = (450050, 550050, 450350, 550350)

        stats = hsg_statistics(path, bbox=bbox, bbox_crs="EPSG:2180")

        assert stats.nodata.area_ha == pytest.approx(1.5)  # 50 x 300 m
        assert stats.groups["A"].area_ha == pytest.approx(0.25)  # 50 x 50 m
        assert stats.groups["B"].area_ha == pytest.approx(7.25)
        everything = [*stats.groups.values(), stats.nodata]
        assert sum(s.area_ha for s in everything) == pytest.approx(9.0)
        assert stats.total_area_m2 == pytest.approx(90000.0)
        assert stats.nodata.percent == pytest.approx(100 / 6)
        assert stats.groups["A"].percent == pytest.approx(2500 / 75000 * 100)
        assert (stats.groups["A"].count, stats.groups["B"].count) == (1, 11)

    def test_bbox_crs_defaults_to_the_crs_of_the_raster(self, tmp_path):
        """Test that bbox without bbox_crs is read in the CRS of the raster."""
        path = self._edge_raster(tmp_path)
        bbox = (450050, 550050, 450350, 550350)

        assert (
            hsg_statistics(path, bbox=bbox).to_dict()
            == hsg_statistics(path, bbox=bbox, bbox_crs="EPSG:2180").to_dict()
        )

    def test_bbox_covering_the_raster_equals_no_bbox(self, tmp_path):
        """Test that a bbox around the whole raster changes nothing."""
        path = self._edge_raster(tmp_path)

        around = hsg_statistics(path, bbox=(0, 0, 1e6, 1e6), bbox_crs="EPSG:2180")

        assert around.to_dict() == hsg_statistics(path).to_dict()

    @pytest.mark.parametrize(
        "bbox",
        [
            (450230, 559130, 451070, 559870),  # inside
            (449500, 558000, 450400, 559500),  # cuts the west and south edges
            (450700, 559500, 452500, 561000),  # cuts the east and north edges
            (449000, 558000, 452000, 561000),  # encloses the raster
            (450000, 558800, 451500, 560000),  # exactly the raster
            (450000, 559000, 450010, 559010),  # one tenth of a cell
        ],
    )
    def test_shares_match_the_exact_overlap_of_aligned_bboxes(self, tmp_path, bbox):
        """Test the cut cells against the analytic overlap (bbox edges on the 1/10 grid)."""
        rng = np.random.default_rng(5)
        codes = rng.integers(0, 5, size=(12, 15), dtype=np.uint8)
        path = _hsg_raster(
            tmp_path, codes, transform=from_origin(450000, 560000, 100, 100)
        )
        x_edges = 450000 + 100 * np.arange(16)
        y_edges = 560000 - 100 * np.arange(13)
        overlap_x = np.clip(
            np.minimum(x_edges[1:], bbox[2]) - np.maximum(x_edges[:-1], bbox[0]),
            0,
            None,
        )
        overlap_y = np.clip(
            np.minimum(y_edges[:-1], bbox[3]) - np.maximum(y_edges[1:], bbox[1]),
            0,
            None,
        )
        shares = np.outer(overlap_y, overlap_x) / 100**2

        stats = hsg_statistics(path, bbox=bbox, bbox_crs="EPSG:2180")

        expected = hsg_statistics_array(codes, 100.0**2, share=shares)
        _assert_close(stats.to_dict(), expected.to_dict())

    def test_bbox_outside_the_raster_gives_zero_areas(self, tmp_path):
        """Test that a disjoint bbox, or one only touching the raster, counts nothing."""
        path = self._edge_raster(tmp_path)

        for bbox in (
            (460000, 560000, 461000, 561000),
            (450400, 550000, 451000, 550400),
        ):
            stats = hsg_statistics(path, bbox=bbox)

            assert stats.total_area_m2 == 0.0
            assert all(g.count == 0 for g in stats.groups.values())
            assert stats.nodata.count == 0
            assert stats.nodata.percent == 0.0

    def test_block_size_does_not_change_the_result(self, tmp_path, monkeypatch):
        """Test that the bbox mask built in blocks of one row equals the whole mask."""
        rng = np.random.default_rng(11)
        codes = rng.integers(0, 5, size=(30, 40), dtype=np.uint8)
        path = _hsg_raster(
            tmp_path, codes, transform=from_origin(450000, 560000, 100, 100)
        )
        bbox = (450333, 557123, 453777, 559456)
        whole = hsg_statistics(path, bbox=bbox)

        monkeypatch.setattr("hydrolog.soil.raster._MAX_BLOCK_SUBCELLS", 1)
        in_blocks = hsg_statistics(path, bbox=bbox)

        assert in_blocks.to_dict() == whole.to_dict()
        assert whole.total_area_m2 == pytest.approx(3444 * 2333, rel=0.01)

    def test_bbox_in_a_geographic_crs_on_a_projected_raster(self, tmp_path):
        """Test a lon/lat bbox on an EPSG:2180 raster against its ellipsoidal area."""
        path = _hsg_raster(
            tmp_path,
            np.full((40, 40), 2),
            transform=from_origin(450000, 560000, 100, 100),
        )
        to_lonlat = pyproj.Transformer.from_crs(
            "EPSG:2180", "EPSG:4326", always_xy=True
        )
        lon, lat = to_lonlat.transform(452000, 558000)  # centre of the raster
        bbox = (lon - 0.012, lat - 0.008, lon + 0.012, lat + 0.008)

        stats = hsg_statistics(path, bbox=bbox, bbox_crs="EPSG:4326")

        expected = _graticule_area_m2(*bbox)
        assert stats.groups["B"].area_m2 == pytest.approx(expected, rel=0.01)
        assert stats.total_area_m2 == stats.valid_area_m2

    def test_bbox_in_a_projected_crs_on_a_geographic_raster(self, tmp_path):
        """Test an EPSG:2180 bbox on an EPSG:4326 raster against its plane area."""
        res = 0.0022457
        path = _hsg_raster(
            tmp_path,
            np.full((100, 100), 3),
            crs="EPSG:4326",
            transform=from_origin(22.7, 52.5, res, res),
        )
        to_2180 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
        x, y = to_2180.transform(22.7 + 50 * res, 52.5 - 50 * res)  # centre
        bbox = (x - 3000, y - 4000, x + 3000, y + 4000)  # 6 x 8 km

        stats = hsg_statistics(path, bbox=bbox, bbox_crs="EPSG:2180")

        assert stats.groups["C"].area_m2 == pytest.approx(48e6, rel=0.02)
        assert stats.groups["C"].percent == 100.0

    @pytest.mark.parametrize(
        "bbox",
        [
            (1, 2, 3),
            (1, 2, 3, 4, 5),
            (1, 2, 1, 4),  # min_x == max_x
            (5, 2, 1, 4),  # min_x > max_x
            (1, 4, 3, 2),  # min_y > max_y
            (1, 2, float("nan"), 4),
            (1, 2, float("inf"), 4),
            ("a", 2, 3, 4),
        ],
    )
    def test_invalid_bbox_raises(self, tmp_path, bbox):
        """Test that anything but min_x < max_x, min_y < max_y numbers is rejected."""
        path = self._edge_raster(tmp_path)

        with pytest.raises(InvalidParameterError, match="bbox") as e:
            hsg_statistics(path, bbox=bbox)

        assert e.value.details["option"] == "bbox"

    def test_bbox_crs_without_bbox_raises(self, tmp_path):
        """Test that a CRS without a bbox is an error, not a silently ignored option."""
        path = self._edge_raster(tmp_path)

        with pytest.raises(InvalidParameterError, match="without bbox"):
            hsg_statistics(path, bbox_crs="EPSG:2180")

    def test_unknown_bbox_crs_raises(self, tmp_path):
        """Test that an unknown CRS name is an InvalidParameterError."""
        path = self._edge_raster(tmp_path)

        with pytest.raises(InvalidParameterError, match="Unknown bbox_crs") as e:
            hsg_statistics(path, bbox=(1, 2, 3, 4), bbox_crs="not-a-crs")

        assert e.value.details["option"] == "bbox_crs"
