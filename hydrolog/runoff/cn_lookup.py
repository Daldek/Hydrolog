"""
Curve Number lookup tables based on USDA-NRCS TR-55.

This module provides CN values for various combinations of:
- Hydrologic Soil Group (HSG): A, B, C, D
- Land cover type and hydrologic condition

Reference:
- USDA-NRCS TR-55: Urban Hydrology for Small Watersheds
- National Engineering Handbook, Part 630, Chapter 9
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Union

from hydrolog.exceptions import InvalidParameterError


class HydrologicCondition(Enum):
    """
    Hydrologic condition representing vegetation density and treatment.

    Attributes
    ----------
    POOR : str
        Poor hydrologic condition (sparse vegetation, heavy grazing).
    FAIR : str
        Fair hydrologic condition (moderate cover).
    GOOD : str
        Good hydrologic condition (dense vegetation, light grazing).
    """

    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"


class LandCover(Enum):
    """
    Land cover types for CN lookup.

    Based on USDA-NRCS TR-55 land cover classifications.
    """

    # Agricultural
    FALLOW = "fallow"
    ROW_CROPS = "row_crops"
    SMALL_GRAIN = "small_grain"
    PASTURE = "pasture"
    MEADOW = "meadow"

    # Natural
    BRUSH = "brush"
    FOREST = "forest"
    HERBACEOUS = "herbaceous"

    # Developed
    FARMSTEAD = "farmstead"
    RESIDENTIAL_LOW = "residential_low"  # 1-2 acre lots, 12-20% impervious
    RESIDENTIAL_MEDIUM = "residential_medium"  # 1/4-1/2 acre, 25-38% impervious
    RESIDENTIAL_HIGH = "residential_high"  # 1/8 acre or less, 65% impervious
    COMMERCIAL = "commercial"  # 85% impervious
    INDUSTRIAL = "industrial"  # 72% impervious
    OPEN_SPACE = "open_space"  # Parks, lawns, golf courses

    # Impervious
    PAVED = "paved"
    GRAVEL = "gravel"
    DIRT = "dirt"

    # Water
    WATER = "water"


# CN lookup tables from TR-55
# Format: {(LandCover, HydrologicCondition): {"A": cn, "B": cn, "C": cn, "D": cn}}
# For land covers without condition variation, use None as condition key

_CN_TABLE: Dict[
    Tuple[LandCover, Optional[HydrologicCondition]], Dict[str, int]
] = {
    # Agricultural - Fallow (bare soil)
    (LandCover.FALLOW, None): {"A": 77, "B": 86, "C": 91, "D": 94},
    # Agricultural - Row crops (straight row)
    (LandCover.ROW_CROPS, HydrologicCondition.POOR): {"A": 72, "B": 81, "C": 88, "D": 91},
    (LandCover.ROW_CROPS, HydrologicCondition.FAIR): {"A": 69, "B": 79, "C": 86, "D": 90},
    (LandCover.ROW_CROPS, HydrologicCondition.GOOD): {"A": 67, "B": 78, "C": 85, "D": 89},
    # Agricultural - Small grain
    (LandCover.SMALL_GRAIN, HydrologicCondition.POOR): {"A": 65, "B": 76, "C": 84, "D": 88},
    (LandCover.SMALL_GRAIN, HydrologicCondition.FAIR): {"A": 64, "B": 75, "C": 83, "D": 87},
    (LandCover.SMALL_GRAIN, HydrologicCondition.GOOD): {"A": 63, "B": 75, "C": 83, "D": 87},
    # Agricultural - Pasture/grassland
    (LandCover.PASTURE, HydrologicCondition.POOR): {"A": 68, "B": 79, "C": 86, "D": 89},
    (LandCover.PASTURE, HydrologicCondition.FAIR): {"A": 49, "B": 69, "C": 79, "D": 84},
    (LandCover.PASTURE, HydrologicCondition.GOOD): {"A": 39, "B": 61, "C": 74, "D": 80},
    # Agricultural - Meadow (continuous grass)
    (LandCover.MEADOW, None): {"A": 30, "B": 58, "C": 71, "D": 78},
    # Natural - Brush/shrub
    (LandCover.BRUSH, HydrologicCondition.POOR): {"A": 48, "B": 67, "C": 77, "D": 83},
    (LandCover.BRUSH, HydrologicCondition.FAIR): {"A": 35, "B": 56, "C": 70, "D": 77},
    (LandCover.BRUSH, HydrologicCondition.GOOD): {"A": 30, "B": 48, "C": 65, "D": 73},
    # Natural - Forest/woods
    (LandCover.FOREST, HydrologicCondition.POOR): {"A": 45, "B": 66, "C": 77, "D": 83},
    (LandCover.FOREST, HydrologicCondition.FAIR): {"A": 36, "B": 60, "C": 73, "D": 79},
    (LandCover.FOREST, HydrologicCondition.GOOD): {"A": 30, "B": 55, "C": 70, "D": 77},
    # Natural - Herbaceous (weeds, grass mix)
    (LandCover.HERBACEOUS, HydrologicCondition.POOR): {"A": 68, "B": 79, "C": 86, "D": 89},
    (LandCover.HERBACEOUS, HydrologicCondition.FAIR): {"A": 49, "B": 69, "C": 79, "D": 84},
    (LandCover.HERBACEOUS, HydrologicCondition.GOOD): {"A": 39, "B": 61, "C": 74, "D": 80},
    # Developed - Farmstead
    (LandCover.FARMSTEAD, None): {"A": 59, "B": 74, "C": 82, "D": 86},
    # Developed - Residential (low density, 1-2 acre lots)
    (LandCover.RESIDENTIAL_LOW, None): {"A": 46, "B": 65, "C": 77, "D": 82},
    # Developed - Residential (medium density, 1/4-1/2 acre)
    (LandCover.RESIDENTIAL_MEDIUM, None): {"A": 57, "B": 72, "C": 81, "D": 86},
    # Developed - Residential (high density, 1/8 acre or smaller)
    (LandCover.RESIDENTIAL_HIGH, None): {"A": 77, "B": 85, "C": 90, "D": 92},
    # Developed - Commercial (85% impervious)
    (LandCover.COMMERCIAL, None): {"A": 89, "B": 92, "C": 94, "D": 95},
    # Developed - Industrial (72% impervious)
    (LandCover.INDUSTRIAL, None): {"A": 81, "B": 88, "C": 91, "D": 93},
    # Developed - Open space (parks, lawns)
    (LandCover.OPEN_SPACE, HydrologicCondition.POOR): {"A": 68, "B": 79, "C": 86, "D": 89},
    (LandCover.OPEN_SPACE, HydrologicCondition.FAIR): {"A": 49, "B": 69, "C": 79, "D": 84},
    (LandCover.OPEN_SPACE, HydrologicCondition.GOOD): {"A": 39, "B": 61, "C": 74, "D": 80},
    # Impervious - Paved (parking, roads)
    (LandCover.PAVED, None): {"A": 98, "B": 98, "C": 98, "D": 98},
    # Impervious - Gravel roads
    (LandCover.GRAVEL, None): {"A": 76, "B": 85, "C": 89, "D": 91},
    # Impervious - Dirt roads
    (LandCover.DIRT, None): {"A": 72, "B": 82, "C": 87, "D": 89},
    # Water
    (LandCover.WATER, None): {"A": 100, "B": 100, "C": 100, "D": 100},
}


@dataclass
class CNLookupResult:
    """
    Result of CN lookup operation.

    Attributes
    ----------
    cn : int
        Curve Number value (1-100).
    hsg : str
        Hydrologic Soil Group used (A, B, C, or D).
    land_cover : LandCover
        Land cover type used.
    condition : HydrologicCondition | None
        Hydrologic condition used (if applicable).
    """

    cn: int
    hsg: str
    land_cover: LandCover
    condition: Optional[HydrologicCondition]


def get_cn(
    hsg: str,
    land_cover: Union[LandCover, str],
    condition: Optional[Union[HydrologicCondition, str]] = None,
) -> int:
    """
    Get Curve Number for a given HSG and land cover combination.

    Parameters
    ----------
    hsg : str
        Hydrologic Soil Group ("A", "B", "C", or "D").
    land_cover : LandCover | str
        Land cover type (enum or string name).
    condition : HydrologicCondition | str | None, optional
        Hydrologic condition for land covers that support it.
        If None and condition is required, defaults to FAIR.

    Returns
    -------
    int
        Curve Number (1-100).

    Raises
    ------
    InvalidParameterError
        If HSG or land cover is invalid.

    Examples
    --------
    >>> get_cn("B", LandCover.FOREST, HydrologicCondition.GOOD)
    55

    >>> get_cn("C", "pasture", "fair")
    79

    >>> get_cn("A", LandCover.PAVED)
    98
    """
    # Validate and normalize HSG
    hsg = hsg.upper()
    if hsg not in ("A", "B", "C", "D"):
        raise InvalidParameterError(
            f"Invalid HSG: '{hsg}'. Must be one of: A, B, C, D"
        )

    # Convert string to LandCover enum if needed
    if isinstance(land_cover, str):
        try:
            land_cover = LandCover(land_cover.lower())
        except ValueError:
            # Try matching by name
            try:
                land_cover = LandCover[land_cover.upper()]
            except KeyError:
                valid = [lc.value for lc in LandCover]
                raise InvalidParameterError(
                    f"Invalid land cover: '{land_cover}'. Valid options: {valid}"
                )

    # Convert string to HydrologicCondition if needed
    if isinstance(condition, str):
        try:
            condition = HydrologicCondition(condition.lower())
        except ValueError:
            valid = [hc.value for hc in HydrologicCondition]
            raise InvalidParameterError(
                f"Invalid condition: '{condition}'. Valid options: {valid}"
            )

    # Look up CN value
    # First try with specific condition
    key = (land_cover, condition)
    if key in _CN_TABLE:
        return _CN_TABLE[key][hsg]

    # Try without condition (for land covers that don't vary)
    key_none = (land_cover, None)
    if key_none in _CN_TABLE:
        return _CN_TABLE[key_none][hsg]

    # If condition was None but land cover requires it, default to FAIR
    if condition is None:
        key_fair = (land_cover, HydrologicCondition.FAIR)
        if key_fair in _CN_TABLE:
            return _CN_TABLE[key_fair][hsg]

    # Land cover not found
    raise InvalidParameterError(
        f"No CN data for land cover '{land_cover.value}' "
        f"with condition '{condition.value if condition else None}'"
    )


def lookup_cn(
    hsg: str,
    land_cover: Union[LandCover, str],
    condition: Optional[Union[HydrologicCondition, str]] = None,
) -> CNLookupResult:
    """
    Look up Curve Number with full result details.

    Parameters
    ----------
    hsg : str
        Hydrologic Soil Group ("A", "B", "C", or "D").
    land_cover : LandCover | str
        Land cover type (enum or string name).
    condition : HydrologicCondition | str | None, optional
        Hydrologic condition for land covers that support it.

    Returns
    -------
    CNLookupResult
        Result with CN value and lookup parameters.

    Examples
    --------
    >>> result = lookup_cn("B", "forest", "good")
    >>> print(f"CN={result.cn} for HSG {result.hsg}")
    CN=55 for HSG B
    """
    # Normalize inputs
    hsg = hsg.upper()

    if isinstance(land_cover, str):
        try:
            land_cover = LandCover(land_cover.lower())
        except ValueError:
            land_cover = LandCover[land_cover.upper()]

    if isinstance(condition, str):
        condition = HydrologicCondition(condition.lower())

    cn = get_cn(hsg, land_cover, condition)

    return CNLookupResult(
        cn=cn,
        hsg=hsg,
        land_cover=land_cover,
        condition=condition,
    )


def get_cn_range(land_cover: Union[LandCover, str]) -> Dict[str, Tuple[int, int]]:
    """
    Get the range of CN values for a land cover type across all HSGs.

    Parameters
    ----------
    land_cover : LandCover | str
        Land cover type.

    Returns
    -------
    dict
        Dictionary with HSG as key and (min_cn, max_cn) tuple as value.

    Examples
    --------
    >>> ranges = get_cn_range(LandCover.FOREST)
    >>> print(f"HSG A: {ranges['A']}")
    HSG A: (30, 45)
    """
    if isinstance(land_cover, str):
        try:
            land_cover = LandCover(land_cover.lower())
        except ValueError:
            land_cover = LandCover[land_cover.upper()]

    result: Dict[str, Tuple[int, int]] = {}

    for hsg in ("A", "B", "C", "D"):
        cn_values = []

        # Collect all CN values for this land cover and HSG
        for (lc, cond), cn_dict in _CN_TABLE.items():
            if lc == land_cover:
                cn_values.append(cn_dict[hsg])

        if cn_values:
            result[hsg] = (min(cn_values), max(cn_values))

    return result


def list_land_covers() -> Dict[str, str]:
    """
    List all available land cover types.

    Returns
    -------
    dict
        Dictionary with land cover enum names as keys and values.
    """
    return {lc.name: lc.value for lc in LandCover}


def calculate_weighted_cn(
    cn_area_pairs: list[Tuple[int, float]],
) -> float:
    """
    Calculate area-weighted average CN for a watershed with multiple land covers.

    Parameters
    ----------
    cn_area_pairs : list[tuple[int, float]]
        List of (CN, area) tuples. Areas can be in any unit (km², ha, etc.)
        as long as they're consistent.

    Returns
    -------
    float
        Weighted average CN.

    Raises
    ------
    InvalidParameterError
        If no valid areas provided or CN out of range.

    Examples
    --------
    >>> # 60% forest (CN=55), 40% pasture (CN=69)
    >>> calculate_weighted_cn([(55, 60.0), (69, 40.0)])
    60.6
    """
    if not cn_area_pairs:
        raise InvalidParameterError("cn_area_pairs cannot be empty")

    total_area = 0.0
    weighted_sum = 0.0

    for cn, area in cn_area_pairs:
        if not 1 <= cn <= 100:
            raise InvalidParameterError(f"CN must be 1-100, got {cn}")
        if area < 0:
            raise InvalidParameterError(f"Area cannot be negative, got {area}")

        total_area += area
        weighted_sum += cn * area

    if total_area <= 0:
        raise InvalidParameterError("Total area must be positive")

    return weighted_sum / total_area
