"""Hydrologic Soil Groups (HSG) from soil texture, and HSG area statistics.

Turns clay, sand and silt contents into the Hydrologic Soil Groups A-D of the
SCS-CN method (USDA-NRCS TR-55, National Engineering Handbook Part 630, Chapter 7)
through the USDA texture triangle (USDA Soil Survey Manual) and the texture -> HSG
table of :mod:`hydrolog.soil.texture`, and summarises HSG grids as areas per group.

Ported from Kartograf 0.8.0 (``kartograf.hydrology.hsg``, Kartograf ADR-025).
The HSG encoding of rasters is identical to Kartograf: ``uint8``, ``1..4`` for
``A..D`` and ``0`` for no data.

This module needs NumPy only; reading and writing GeoTIFFs is in
:mod:`hydrolog.soil.raster` (extra ``hydrolog[raster]``).

Notes
-----
HSG is the soil input of the SCS-CN method: curve numbers
(:func:`hydrolog.runoff.cn_lookup.get_cn`) are looked up per land cover and HSG,
and the areas per group of :func:`hsg_statistics_array` are the weights of
:func:`hydrolog.runoff.cn_lookup.calculate_weighted_cn`.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.soil.texture import (
    HSG_CODES,
    _amounts,
    _reject_negative,
    _texture_codes,
    texture_to_hsg_array,
)

__all__ = [
    "HSG_CODES",
    "HSG_DESCRIPTIONS",
    "HsgGroupStatistics",
    "HsgStatistics",
    "classify_hsg",
    "hsg_statistics_array",
]

#: Polish descriptions of the Hydrologic Soil Groups (as in Kartograf).
HSG_DESCRIPTIONS: dict[str, str] = {
    "A": "Duża infiltracja - gleby piaszczyste, mały potencjał spływu",
    "B": "Umiarkowana infiltracja - gleby gliniaste, umiarkowany spływ",
    "C": "Mała infiltracja - gliny ilaste, duży spływ",
    "D": "Bardzo mała infiltracja - gleby ilaste, bardzo duży spływ",
}

_NODATA_CODE = 0
_M2_PER_HA = 10_000.0


@dataclass
class HsgGroupStatistics(JsonResultMixin):
    """
    Statistics of one Hydrologic Soil Group (or of the no-data class).

    Attributes
    ----------
    count : int
        Number of cells of the group (with a non-zero share inside the area).
    area_m2 : float
        Area of the group [m²] (cell areas weighted by their share inside the
        area).
    area_ha : float
        The same area [ha].
    percent : float
        Share of the group [%]: of the area *with data* for groups A-D, of the
        *whole* area for the no-data class. ``0.0`` when that area is zero.
    """

    count: int
    area_m2: float
    area_ha: float
    percent: float


@dataclass
class HsgStatistics(JsonResultMixin):
    """
    Area statistics of an HSG grid.

    The areas of the four groups and of the no-data class add up to
    ``total_area_m2``.

    Attributes
    ----------
    groups : dict[str, HsgGroupStatistics]
        Statistics of the groups ``"A"``, ``"B"``, ``"C"`` and ``"D"``; the percent
        is the share of the area with data.
    nodata : HsgGroupStatistics
        Cells without data (class 0: a gap in an input); the percent is the share
        of the whole area.
    total_area_m2 : float
        Area of all cells inside the area [m²].
    valid_area_m2 : float
        Area of the cells with data (groups A-D) [m²].
    """

    groups: dict[str, HsgGroupStatistics]
    nodata: HsgGroupStatistics
    total_area_m2: float
    valid_area_m2: float


def _nodata_mask(
    values: NDArray[np.float64], nodata: float | None
) -> NDArray[np.bool_]:
    """
    Boolean mask of cells that carry no usable value.

    Covers NaN/Inf (which survive any arithmetic and would otherwise be classified
    as soil) plus the raster's own nodata tag, when it has one.
    """
    mask = ~np.isfinite(values)
    if nodata is not None:
        mask |= values == nodata
    return mask


def classify_hsg(
    clay: ArrayLike,
    sand: ArrayLike,
    silt: ArrayLike,
    *,
    nodata: tuple[float | None, float | None, float | None] = (None, None, None),
) -> NDArray[np.uint8]:
    """
    Hydrologic Soil Group codes from clay, sand and silt amounts.

    The texture comes from the raw amounts by exact arithmetic
    (:func:`hydrolog.soil.texture.classify_usda_texture_array` compares them with
    their total, with no unit conversion and no division) and is mapped to the HSG
    with :data:`hydrolog.soil.texture.TEXTURE_TO_HSG`. Cells that carry no usable
    soil data get ``0``.

    Parameters
    ----------
    clay : array_like
        Clay amounts (any unit shared by the three inputs, e.g. g/kg as in
        SoilGrids, or percent).
    sand : array_like
        Sand amounts, in the same unit and of the same shape.
    silt : array_like
        Silt amounts, in the same unit and of the same shape.
    nodata : tuple of (float or None), optional
        The nodata values of the clay, sand and silt rasters (their tags); ``None``
        for an input without a nodata value, by default ``(None, None, None)``.

    Returns
    -------
    NDArray[np.uint8]
        HSG codes in the shape of the inputs: ``1..4`` for ``A..D`` (see
        :data:`HSG_CODES`), ``0`` for no data.

    Raises
    ------
    InvalidParameterError
        If the inputs differ in shape or are not numeric, ``nodata`` is not a
        triple, or a cell with data holds a negative amount.

    Notes
    -----
    A cell is no data (``0``) when

    - any of its three amounts is NaN or infinite,
    - any of its amounts equals the nodata value of its input, or
    - all three amounts are zero (the SoilGrids convention for a gap).

    Pure sand or pure silt (clay ``0`` with a non-zero sand or silt) is real soil
    and gets a class. Negative amounts are rejected only in cells with data: a
    negative nodata fill (e.g. ``-32768``) is masked first, an untagged negative
    value is an error.

    Examples
    --------
    >>> classify_hsg([450, 50, 0], [200, 900, 0], [350, 50, 0]).tolist()  # g/kg
    [4, 1, 0]
    """
    clay_a, sand_a, silt_a = _amounts(clay, sand, silt)
    if len(nodata) != 3:
        raise InvalidParameterError(
            f"nodata must hold one value per input (clay, sand, silt), got {nodata!r}",
            details={"option": "nodata"},
        )

    no_data = (
        _nodata_mask(clay_a, nodata[0])
        | _nodata_mask(sand_a, nodata[1])
        | _nodata_mask(silt_a, nodata[2])
    )
    no_data |= (clay_a == 0) & (sand_a == 0) & (silt_a == 0)

    # Cells without data never reach the classifier, so NaN/Inf and nodata fills
    # cannot raise warnings or a negative-amount error.
    amounts = [np.where(no_data, 0.0, values) for values in (clay_a, sand_a, silt_a)]
    for name, values in zip(("clay", "sand", "silt"), amounts, strict=True):
        _reject_negative(name, values)

    hsg = texture_to_hsg_array(_texture_codes(amounts[0], amounts[1], amounts[2]))
    return np.where(no_data, _NODATA_CODE, hsg).astype(np.uint8)


def _cell_areas(
    cell_area_m2: float | ArrayLike, shape: tuple[int, ...]
) -> NDArray[np.float64]:
    """Cell areas as a ``float64`` array that broadcasts to ``shape``."""
    try:
        areas = np.asarray(cell_area_m2, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise InvalidParameterError(
            "cell_area_m2 must be a number or an array of numbers",
            details={"option": "cell_area_m2"},
        ) from exc
    if areas.ndim == 1 and len(shape) == 2 and areas.shape[0] == shape[0]:
        areas = areas[:, np.newaxis]  # one value per row
    elif areas.ndim != 0 and areas.shape != shape:
        raise InvalidParameterError(
            f"cell_area_m2 must be a number, one value per row or an array of shape "
            f"{shape}, got shape {areas.shape}",
            details={"option": "cell_area_m2"},
        )
    if not (np.isfinite(areas).all() and (areas > 0).all()):
        raise InvalidParameterError(
            "cell_area_m2 must be finite and positive",
            details={"option": "cell_area_m2"},
        )
    return areas


def _cell_shares(share: ArrayLike, shape: tuple[int, ...]) -> NDArray[np.float64]:
    """``share`` as a ``float64`` array of ``shape`` with values in 0-1."""
    try:
        shares = np.asarray(share, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise InvalidParameterError(
            "share must be an array of numbers", details={"option": "share"}
        ) from exc
    if shares.shape != shape:
        raise InvalidParameterError(
            f"share must have the shape of hsg {shape}, got {shares.shape}",
            details={"option": "share"},
        )
    if not ((shares >= 0) & (shares <= 1)).all():
        raise InvalidParameterError(
            "share must hold values from 0 to 1", details={"option": "share"}
        )
    return shares


def hsg_statistics_array(
    hsg: ArrayLike,
    cell_area_m2: float | ArrayLike,
    *,
    share: ArrayLike | None = None,
) -> HsgStatistics:
    """
    Area statistics of an HSG grid.

    Parameters
    ----------
    hsg : array_like
        Integer HSG codes: ``1..4`` for ``A..D``, ``0`` for no data (the output of
        :func:`classify_hsg`).
    cell_area_m2 : float or array_like
        Area of one cell [m²]: a number for equal cells; for a 2-D ``hsg`` a 1-D
        array with one value per row (the cell area of a geographic raster depends
        on the latitude only); or an array of the shape of ``hsg``.
    share : array_like, optional
        Share (0-1) of every cell inside the area of interest, of the shape of
        ``hsg``; cells partly outside count with their share. By default every
        cell counts completely.

    Returns
    -------
    HsgStatistics
        Count, area and percent per group, and the no-data class.

    Raises
    ------
    InvalidParameterError
        If ``hsg`` is not an integer array of codes 0-4, or ``cell_area_m2`` or
        ``share`` is invalid or does not match the shape of ``hsg``.

    Notes
    -----
    The percent of the groups A-D is the share of the area *with data*; the percent
    of the no-data class is the share of the *whole* area. The areas of all five
    classes add up to ``total_area_m2``. Percents are ``0.0`` when their reference
    area is zero.

    Examples
    --------
    >>> hsg = [[1, 2, 2, 2], [0, 0, 0, 0]]
    >>> stats = hsg_statistics_array(hsg, cell_area_m2=100.0)
    >>> stats.groups["B"].area_m2, stats.groups["B"].percent
    (300.0, 75.0)
    >>> stats.nodata.percent
    50.0
    """
    codes = np.asarray(hsg)
    if codes.dtype.kind not in "iu":
        raise InvalidParameterError(
            f"hsg must be an integer array of codes 0-{len(HSG_CODES)}, "
            f"got dtype {codes.dtype}",
            details={"option": "hsg"},
        )
    if codes.size and (int(codes.min()) < 0 or int(codes.max()) > len(HSG_CODES)):
        raise InvalidParameterError(
            f"hsg codes must be in 0-{len(HSG_CODES)}, got values from "
            f"{int(codes.min())} to {int(codes.max())}",
            details={"option": "hsg"},
        )
    areas = _cell_areas(cell_area_m2, codes.shape)

    if share is None:
        weight = np.broadcast_to(areas, codes.shape)
        touched = None
    else:
        shares = _cell_shares(share, codes.shape)
        weight = areas * shares
        touched = shares > 0

    total_m2 = float(np.sum(weight))
    valid_m2 = float(np.sum(weight[codes > _NODATA_CODE]))

    def statistics_of(code: int, reference_m2: float) -> HsgGroupStatistics:
        selected = codes == code
        area_m2 = float(np.sum(weight[selected]))
        counted = selected if touched is None else selected & touched
        return HsgGroupStatistics(
            count=int(np.count_nonzero(counted)),
            area_m2=area_m2,
            area_ha=area_m2 / _M2_PER_HA,
            percent=area_m2 / reference_m2 * 100 if reference_m2 > 0 else 0.0,
        )

    return HsgStatistics(
        groups={
            name: statistics_of(code, valid_m2) for name, code in HSG_CODES.items()
        },
        nodata=statistics_of(_NODATA_CODE, total_m2),
        total_area_m2=total_m2,
        valid_area_m2=valid_m2,
    )
