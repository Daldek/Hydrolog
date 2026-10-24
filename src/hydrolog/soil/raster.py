"""GeoTIFF input and output of the HSG computation (extra ``hydrolog[raster]``).

Builds an HSG GeoTIFF from clay, sand and silt rasters and summarises an HSG
GeoTIFF as areas per Hydrologic Soil Group. The classification itself is
:func:`hydrolog.soil.hsg.classify_hsg`; this module only reads and writes rasters.

Ported from Kartograf 0.8.0 (``kartograf.hydrology.hsg``, Kartograf ADR-025) without
its download, version store and reprojection logic: the three inputs must already
share one grid (see :func:`hsg_from_rasters`).

``rasterio`` and ``pyproj`` are imported lazily, so importing this module needs
neither; the functions raise :class:`~hydrolog.exceptions.MissingDependencyError`
when the extra is not installed::

    pip install hydrolog[raster]
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from hydrolog._atomic import atomic_output
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import (
    InputDataError,
    InvalidParameterError,
    MissingDependencyError,
    NotFoundError,
    OutputError,
)
from hydrolog.soil.hsg import (
    HSG_CODES,
    HsgStatistics,
    classify_hsg,
    hsg_statistics_array,
)

__all__ = ["HsgRasterResult", "hsg_from_rasters", "hsg_statistics"]

# Statistics area: each cell is split into _SUBCELLS x _SUBCELLS parts to measure its
# share inside the bbox (precision 1 % of a cell).
_SUBCELLS = 10
# Upper bound of the sub-cell mask of one block of rows [pixels]; the bbox window is
# processed in blocks so that a large raster does not need one huge mask.
_MAX_BLOCK_SUBCELLS = 50_000_000
# Points per edge of the densified bbox outline.
_EDGE_POINTS = 64

_NODATA_CODE = 0
_RASTER_EXTRA_HINT = "pip install hydrolog[raster]"
_SAME_GRID_HINT = (
    "Resample the three rasters onto one grid (same CRS, extent and cell size), "
    "e.g. with gdalwarp."
)


@dataclass
class HsgRasterResult(JsonResultMixin):
    """
    Result of :func:`hsg_from_rasters`.

    Attributes
    ----------
    output_path : Path
        The HSG GeoTIFF that was written.
    shape : tuple[int, int]
        Raster size as ``(rows, columns)``.
    crs : str
        Coordinate reference system of the raster (``"EPSG:2180"`` or WKT).
    counts : dict[str, int]
        Number of cells per class: ``"A"``, ``"B"``, ``"C"``, ``"D"`` and
        ``"nodata"`` (class 0).
    """

    output_path: Path
    shape: tuple[int, int]
    crs: str
    counts: dict[str, int]


@dataclass(frozen=True)
class _Grid:
    """Shape, CRS and affine transform of a raster."""

    shape: tuple[int, int]
    crs: Any
    transform: Any


def _import_raster_libs() -> tuple[Any, Any]:
    """Import ``rasterio`` and ``pyproj``.

    Raises
    ------
    MissingDependencyError
        If the ``raster`` extra is not installed.
    """
    try:
        import pyproj
        import rasterio  # type: ignore[import-untyped]
    except ImportError as exc:
        raise MissingDependencyError(
            "HSG rasters need the optional packages rasterio and pyproj "
            "(extra 'raster')",
            hint=_RASTER_EXTRA_HINT,
            details={"extra": "raster", "package": exc.name},
        ) from exc
    return rasterio, pyproj


def _open_raster(rasterio: Any, path: Path, label: str) -> Any:
    """Open a raster for reading.

    Raises
    ------
    NotFoundError
        If ``path`` does not exist.
    InputDataError
        If GDAL cannot read it as a raster.
    """
    if not path.exists():
        raise NotFoundError(
            f"The {label} raster does not exist: {path}",
            details={"path": str(path), "layer": label},
        )
    try:
        return rasterio.open(path)
    except rasterio.errors.RasterioError as exc:
        raise InputDataError(
            f"Cannot read the {label} raster {path}: {exc}",
            details={"path": str(path), "layer": label},
        ) from exc


def _grid_of(src: Any, path: Path, label: str) -> _Grid:
    """Grid of an open raster; a raster without a CRS is rejected."""
    if src.crs is None:
        raise InputDataError(
            f"The {label} raster {path} has no coordinate reference system",
            hint="Assign the CRS to the raster first (e.g. with gdal_edit.py -a_srs).",
            details={"path": str(path), "layer": label},
        )
    return _Grid((int(src.height), int(src.width)), src.crs, src.transform)


def _read_band(
    rasterio: Any,
    src: Any,
    path: Path,
    label: str,
    window: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> NDArray[Any]:
    """First band of an open raster, or of the window ``((row0, row1), (col0, col1))``.

    Raises
    ------
    InputDataError
        If the data cannot be read (e.g. a truncated file).
    """
    try:
        band: NDArray[Any] = src.read(1, window=window)
    except rasterio.errors.RasterioError as exc:
        raise InputDataError(
            f"Cannot read the data of the {label} raster {path}: {exc}",
            hint="The file may be truncated or corrupted.",
            details={"path": str(path), "layer": label},
        ) from exc
    return band


def _same_transform(first: Any, second: Any) -> bool:
    """Whether two affine transforms agree within a millionth of a cell."""
    tolerance = 1e-6 * max(abs(first.a), abs(first.b), abs(first.d), abs(first.e))
    return all(
        abs(a - b) <= tolerance for a, b in zip(first[:6], second[:6], strict=True)
    )


def _check_same_grid(
    first_label: str, first: _Grid, second_label: str, second: _Grid
) -> None:
    """Raise if two rasters differ in shape, CRS or transform."""
    layers = [first_label, second_label]
    if first.shape != second.shape:
        raise InputDataError(
            f"The {first_label} and {second_label} rasters differ in shape: "
            f"{first.shape} vs {second.shape} (rows, columns)",
            hint=_SAME_GRID_HINT,
            details={"property": "shape", "layers": layers},
        )
    if first.crs != second.crs:
        raise InputDataError(
            f"The {first_label} and {second_label} rasters differ in CRS: "
            f"{first.crs.to_string()} vs {second.crs.to_string()}",
            hint=_SAME_GRID_HINT,
            details={"property": "crs", "layers": layers},
        )
    if not _same_transform(first.transform, second.transform):
        raise InputDataError(
            f"The {first_label} and {second_label} rasters differ in transform "
            f"(extent or cell size): {tuple(first.transform)[:6]} vs "
            f"{tuple(second.transform)[:6]}",
            hint=_SAME_GRID_HINT,
            details={"property": "transform", "layers": layers},
        )


def _is_same_file(first: Path, second: Path) -> bool:
    """Whether two paths name the same file (also when one does not exist yet)."""
    try:
        return first.samefile(second)
    except OSError:
        return first.resolve() == second.resolve()


def _write_hsg_geotiff(
    rasterio: Any, output_path: Path, hsg: NDArray[np.uint8], grid: _Grid
) -> None:
    """Write HSG classes as ``uint8`` GeoTIFF (nodata 0) with the band tags.

    The file appears atomically (written aside, then renamed), and the directory
    only now, so a failed input leaves nothing behind.

    Raises
    ------
    OutputError
        If the file cannot be written.
    """
    profile = {
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "height": grid.shape[0],
        "width": grid.shape[1],
        "crs": grid.crs,
        "transform": grid.transform,
        "nodata": _NODATA_CODE,
        "compress": "deflate",
    }
    classes = ", ".join(f"{code}={name}" for name, code in HSG_CODES.items())
    try:
        with (
            atomic_output(output_path) as temporary,
            rasterio.open(temporary, "w", **profile) as dst,
        ):
            dst.write(hsg, 1)
            dst.update_tags(
                1,
                LAYER_NAME="Hydrologic Soil Group",
                LAYER_DESCRIPTION=f"HSG classification: {classes}",
            )
    except OSError as exc:
        raise OutputError(
            f"Cannot write the HSG raster {output_path}: {exc}",
            details={"path": str(output_path), "reason": "output_unwritable"},
        ) from exc


def hsg_from_rasters(
    clay_path: str | Path,
    sand_path: str | Path,
    silt_path: str | Path,
    output_path: str | Path,
) -> HsgRasterResult:
    """
    Write an HSG GeoTIFF computed from clay, sand and silt rasters.

    Each cell is classified with :func:`hydrolog.soil.hsg.classify_hsg` from the raw
    values of the three rasters (any unit shared by them, e.g. the g/kg of
    SoilGrids). The nodata value of every input is taken from its tag only (no tag
    means no nodata value); NaN/Inf cells and cells that are zero in all three
    inputs are gaps (class 0).

    Parameters
    ----------
    clay_path : str or Path
        Clay raster (the first band is read).
    sand_path : str or Path
        Sand raster, on the same grid.
    silt_path : str or Path
        Silt raster, on the same grid.
    output_path : str or Path
        HSG GeoTIFF to write (missing directories are created, an existing file
        is replaced).

    Returns
    -------
    HsgRasterResult
        Output path, raster shape, CRS and the number of cells per class.

    Raises
    ------
    MissingDependencyError
        If ``rasterio`` or ``pyproj`` is not installed (``pip install
        hydrolog[raster]``).
    NotFoundError
        If an input raster does not exist.
    InputDataError
        If an input cannot be read, has no CRS, the three inputs differ in shape,
        CRS or transform, or a cell with data holds a negative amount that is not
        marked as nodata.
    InvalidParameterError
        If ``output_path`` is one of the input files.
    OutputError
        If the output cannot be written.

    Notes
    -----
    The output is a single-band ``uint8`` GeoTIFF with the grid of the inputs,
    Deflate compression and nodata ``0``; ``1..4`` are the groups ``A..D``. The
    band tags are ``LAYER_NAME="Hydrologic Soil Group"`` and
    ``LAYER_DESCRIPTION="HSG classification: 1=A, 2=B, 3=C, 4=D"`` (as in Kartograf).
    Inputs are not resampled: bring them onto one grid first (e.g. with
    ``gdalwarp``); transforms that agree within a millionth of a cell are accepted.

    Examples
    --------
    >>> result = hsg_from_rasters(
    ...     "clay.tif", "sand.tif", "silt.tif", "hsg.tif"
    ... )  # doctest: +SKIP
    >>> result.counts  # doctest: +SKIP
    {'A': 0, 'B': 120, 'C': 80, 'D': 0, 'nodata': 0}
    """
    rasterio, _ = _import_raster_libs()
    layers = {
        "clay": Path(clay_path),
        "sand": Path(sand_path),
        "silt": Path(silt_path),
    }
    output = Path(output_path)
    for label, path in layers.items():
        if _is_same_file(path, output):
            raise InvalidParameterError(
                f"output_path must not be the {label} input raster: {output}",
                details={"option": "output_path"},
            )

    amounts: dict[str, NDArray[Any]] = {}
    nodata: dict[str, float | None] = {}
    first_label = ""
    grid: _Grid | None = None
    for label, path in layers.items():
        with _open_raster(rasterio, path, label) as src:
            layer_grid = _grid_of(src, path, label)
            if grid is None:
                first_label, grid = label, layer_grid
            else:
                _check_same_grid(first_label, grid, label, layer_grid)
            amounts[label] = _read_band(rasterio, src, path, label)
            nodata[label] = src.nodata
    assert grid is not None

    try:
        hsg = classify_hsg(
            amounts["clay"],
            amounts["sand"],
            amounts["silt"],
            nodata=(nodata["clay"], nodata["sand"], nodata["silt"]),
        )
    except InvalidParameterError as exc:
        raise InputDataError(
            f"Invalid soil amounts in the input rasters: {exc}",
            hint="Mark the fill value of the rasters as their nodata value.",
            details={
                "layer": exc.details.get("option"),
                "value": exc.details.get("value"),
            },
        ) from exc

    _write_hsg_geotiff(rasterio, output, hsg, grid)

    per_code = np.bincount(hsg.ravel(), minlength=len(HSG_CODES) + 1)
    counts = {name: int(per_code[code]) for name, code in HSG_CODES.items()}
    counts["nodata"] = int(per_code[_NODATA_CODE])
    return HsgRasterResult(
        output_path=output,
        shape=grid.shape,
        crs=grid.crs.to_string(),
        counts=counts,
    )


def _geographic_row_cell_areas(
    transform: Any, first_row: int, last_row: int
) -> NDArray[np.float64]:
    """
    Geodetic area (m2) of one cell in each of the rows ``first_row:last_row``.

    For a CRS in degrees the affine determinant is square degrees, not square
    metres. The area of a cell on the ellipsoid depends on the latitude only (all
    cells of a row are congruent), so one polygon per row is enough.

    Raises
    ------
    InputDataError
        If the transform is rotated or sheared (the cells of a row would differ).
    """
    from pyproj import Geod

    tolerance = 1e-9 * abs(transform.a)
    if abs(transform.b) > tolerance or abs(transform.d) > tolerance:
        raise InputDataError(
            "Rotated rasters in a geographic CRS are not supported",
            hint="Resample the raster onto a north-up grid first.",
        )
    geod = Geod(ellps="WGS84")
    areas = np.empty(last_row - first_row, dtype=np.float64)
    for index, row in enumerate(range(first_row, last_row)):
        lon0, top = transform * (0, row)
        lon1, bottom = transform * (1, row + 1)
        area, _ = geod.polygon_area_perimeter(
            [lon0, lon1, lon1, lon0], [bottom, bottom, top, top]
        )
        areas[index] = abs(area)
    return areas


def _row_cell_areas(
    src: Any, pyproj: Any, first_row: int, last_row: int
) -> NDArray[np.float64]:
    """Area (m2) of one cell in each of the rows ``first_row:last_row``."""
    if src.crs.is_geographic:
        return _geographic_row_cell_areas(src.transform, first_row, last_row)
    # Projected CRS: the affine area, converted from the CRS length unit to metres.
    axes = pyproj.CRS.from_wkt(src.crs.to_wkt()).axis_info
    unit = float(axes[0].unit_conversion_factor) if axes else 1.0
    cell_m2 = abs(src.transform.determinant) * unit**2
    return np.full(last_row - first_row, cell_m2, dtype=np.float64)


def _bbox_outline(
    bbox: tuple[float, float, float, float],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Densified outline of a bbox (counter-clockwise from the south-west corner)."""
    min_x, min_y, max_x, max_y = bbox
    steps = np.linspace(0.0, 1.0, _EDGE_POINTS, endpoint=False)
    dx, dy = max_x - min_x, max_y - min_y
    xs = np.concatenate(
        [
            min_x + steps * dx,
            np.full(steps.size, max_x),
            max_x - steps * dx,
            np.full(steps.size, min_x),
        ]
    )
    ys = np.concatenate(
        [
            np.full(steps.size, min_y),
            min_y + steps * dy,
            np.full(steps.size, max_y),
            max_y - steps * dy,
        ]
    )
    return xs, ys


def _bbox_shares(
    src: Any,
    pyproj: Any,
    bbox: tuple[float, float, float, float],
    bbox_crs: str | None,
) -> tuple[tuple[int, int, int, int], NDArray[np.float64]]:
    """
    Share (0-1) of every raster cell inside ``bbox``, for the cells it can touch.

    The bbox outline (densified edges) is transformed to the raster CRS and
    rasterized on a grid ``_SUBCELLS`` times finer; the share of a cell is the part
    of its sub-cells inside. Only the window of the raster that the outline can
    touch is evaluated (in blocks of rows), so the work and memory depend on the
    bbox, not on the raster.

    Returns
    -------
    window : tuple of int
        ``(first_row, last_row, first_col, last_col)``; cells outside it have a
        share of 0 (an empty window when the bbox misses the raster).
    shares : NDArray[np.float64]
        Shares of the cells of the window.

    Raises
    ------
    InvalidParameterError
        If the bbox cannot be transformed to the raster CRS.
    """
    from rasterio.features import (  # type: ignore[import-untyped]
        geometry_mask,
    )
    from rasterio.transform import (  # type: ignore[import-untyped]
        Affine,
    )

    xs, ys = _bbox_outline(bbox)
    if bbox_crs is not None:
        to_raster = pyproj.Transformer.from_crs(
            bbox_crs, src.crs.to_wkt(), always_xy=True
        )
        xs, ys = to_raster.transform(xs, ys)
    if not (np.isfinite(xs).all() and np.isfinite(ys).all()):
        raise InvalidParameterError(
            f"bbox cannot be transformed from {bbox_crs} to the CRS of the raster",
            details={"option": "bbox"},
        )

    cols, rows = ~src.transform * (xs, ys)
    first_col = max(math.floor(float(cols.min())), 0)
    last_col = min(math.ceil(float(cols.max())), src.width)
    first_row = max(math.floor(float(rows.min())), 0)
    last_row = min(math.ceil(float(rows.max())), src.height)
    if first_col >= last_col or first_row >= last_row:
        return (0, 0, 0, 0), np.zeros((0, 0), dtype=np.float64)

    n_cols = last_col - first_col
    ring = [(float(x), float(y)) for x, y in zip(xs, ys, strict=True)]
    polygon = {"type": "Polygon", "coordinates": [[*ring, ring[0]]]}
    block_rows = max(1, _MAX_BLOCK_SUBCELLS // (n_cols * _SUBCELLS * _SUBCELLS))
    shares = np.zeros((last_row - first_row, n_cols), dtype=np.float64)
    for start in range(first_row, last_row, block_rows):
        stop = min(start + block_rows, last_row)
        inside = geometry_mask(
            [polygon],
            out_shape=((stop - start) * _SUBCELLS, n_cols * _SUBCELLS),
            transform=src.transform
            * Affine.translation(first_col, start)
            * Affine.scale(1 / _SUBCELLS),
            invert=True,
        )
        shares[start - first_row : stop - first_row] = inside.reshape(
            stop - start, _SUBCELLS, n_cols, _SUBCELLS
        ).mean(axis=(1, 3))
    return (first_row, last_row, first_col, last_col), shares


def _checked_bbox(
    bbox: Any, bbox_crs: str | None, pyproj: Any
) -> tuple[float, float, float, float] | None:
    """Validate ``bbox`` as four floats, or return ``None`` when no bbox is given."""
    if bbox is None:
        if bbox_crs is not None:
            raise InvalidParameterError(
                "bbox_crs was given without bbox", details={"option": "bbox_crs"}
            )
        return None
    try:
        min_x, min_y, max_x, max_y = (float(value) for value in bbox)
    except (TypeError, ValueError) as exc:
        raise InvalidParameterError(
            "bbox must be four numbers: min_x, min_y, max_x, max_y",
            details={"option": "bbox"},
        ) from exc
    if not all(math.isfinite(v) for v in (min_x, min_y, max_x, max_y)):
        raise InvalidParameterError(
            "bbox coordinates must be finite", details={"option": "bbox"}
        )
    if min_x >= max_x or min_y >= max_y:
        raise InvalidParameterError(
            f"bbox needs min_x < max_x and min_y < max_y, got "
            f"({min_x}, {min_y}, {max_x}, {max_y})",
            details={"option": "bbox"},
        )
    if bbox_crs is not None:
        try:
            pyproj.CRS.from_user_input(bbox_crs)
        except pyproj.exceptions.CRSError as exc:
            raise InvalidParameterError(
                f"Unknown bbox_crs {bbox_crs!r}", details={"option": "bbox_crs"}
            ) from exc
    return min_x, min_y, max_x, max_y


def hsg_statistics(
    hsg_path: str | Path,
    *,
    bbox: Sequence[float] | None = None,
    bbox_crs: str | None = None,
) -> HsgStatistics:
    """
    Area statistics of an HSG GeoTIFF, optionally inside a bounding box.

    Parameters
    ----------
    hsg_path : str or Path
        HSG GeoTIFF: integer codes ``1..4`` for ``A..D`` and ``0`` for no data
        (:func:`hsg_from_rasters`, Kartograf).
    bbox : sequence of float, optional
        Area of interest ``(min_x, min_y, max_x, max_y)``; by default the whole
        raster. Cells cut by its edges count with the share inside (a SoilGrids
        grid reaches beyond the catchment). Axis order is x = easting / longitude,
        y = northing / latitude.
    bbox_crs : str, optional
        CRS of ``bbox`` (e.g. ``"EPSG:2180"``); by default the CRS of the raster.

    Returns
    -------
    HsgStatistics
        Count, area and percent per group and for the no-data class; the areas of
        all classes add up to the area of interest.

    Raises
    ------
    MissingDependencyError
        If ``rasterio`` or ``pyproj`` is not installed (``pip install
        hydrolog[raster]``).
    NotFoundError
        If ``hsg_path`` does not exist.
    InputDataError
        If the file cannot be read, has no CRS or is not an HSG raster (not integer
        codes 0-4).
    InvalidParameterError
        If ``bbox`` or ``bbox_crs`` is invalid, or ``bbox_crs`` is given without
        ``bbox``.

    Notes
    -----
    Areas are in square metres / hectares regardless of the raster CRS: for a
    geographic CRS (SoilGrids output is EPSG:4326) cell areas are computed
    geodetically per raster row on the WGS84 ellipsoid, not from the affine
    determinant, which would give square degrees. For a projected CRS the affine
    cell area is used (converted to metres if the CRS unit is not the metre), so
    the distortion of the projection is ignored.

    A ``bbox`` that does not overlap the raster is not an error: all counts and
    areas are zero (check ``total_area_m2``).

    Examples
    --------
    >>> stats = hsg_statistics("hsg.tif")  # doctest: +SKIP
    >>> stats.groups["B"].area_ha  # doctest: +SKIP
    2500.0
    """
    rasterio, pyproj = _import_raster_libs()
    area = _checked_bbox(bbox, bbox_crs, pyproj)
    path = Path(hsg_path)
    with _open_raster(rasterio, path, "HSG") as src:
        _grid_of(src, path, "HSG")  # rejects a raster without CRS
        if area is None:
            window = (0, int(src.height), 0, int(src.width))
            shares = None
        else:
            window, shares = _bbox_shares(src, pyproj, area, bbox_crs)
        first_row, last_row, first_col, last_col = window
        row_areas = _row_cell_areas(src, pyproj, first_row, last_row)
        if first_row < last_row and first_col < last_col:
            codes = _read_band(
                rasterio,
                src,
                path,
                "HSG",
                window=((first_row, last_row), (first_col, last_col)),
            )
        else:  # a bbox that misses the raster
            codes = np.zeros((0, 0), dtype=np.uint8)

    try:
        return hsg_statistics_array(codes, row_areas, share=shares)
    except InvalidParameterError as exc:
        raise InputDataError(
            f"{path} is not a valid HSG raster: {exc}",
            hint="Expected integer codes 0-4 (0 = no data, 1..4 = A..D).",
            details={"path": str(path)},
        ) from exc
