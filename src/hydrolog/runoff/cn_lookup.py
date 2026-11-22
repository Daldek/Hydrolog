"""
Curve numbers of the USDA-NRCS TR-55 tables for a soil group and a land cover.

The table is the data file ``src/hydrolog/_data/tables/tr55_cn.csv`` (Nogat CMP-2.5):
TR-55 (USDA-SCS 1986, 2nd ed.) tables 2-2a (urban areas, p. 2-5), 2-2b (cultivated
agricultural lands, p. 2-6) and 2-2c (other agricultural lands, p. 2-7); ``herbaceous``
takes the pasture row of table 2-2c, as footnote 1 of table 2-2d directs for range in
humid regions; water is CN 98 (NEH 630 ch. 9, p. 9-1). Row crops and small grain are
the straight-row rows, in poor and good condition only: TR-55 has no fair condition
for them. The lookup is declared by its spec :data:`TR55_CN` (``tr55_cn``), the
area-weighted CN by the Tier B row :data:`WEIGHTED_CN`.
"""

import csv
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final

from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog._serialization import JsonResultMixin
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Constraint,
    FormulaSpec,
    Limit,
    Output,
    Properties,
    Range,
    Source,
    Table,
    TierBSpec,
    Values,
    Variable,
)


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
    WOODS_GRASS = "woods_grass"  # Orchard or tree farm, 50% woods and 50% pasture

    # Developed
    FARMSTEAD = "farmstead"
    RESIDENTIAL_LOW = "residential_low"  # 2 acre lots, 12% impervious
    RESIDENTIAL_MEDIUM = "residential_medium"  # 1/3 acre lots, 30% impervious
    RESIDENTIAL_QUARTER_ACRE = "residential_quarter_acre"  # 1/4 acre, 38% impervious
    RESIDENTIAL_HIGH = "residential_high"  # 1/8 acre or less, 65% impervious
    COMMERCIAL = "commercial"  # 85% impervious
    INDUSTRIAL = "industrial"  # 72% impervious
    OPEN_SPACE = "open_space"  # Parks, lawns, golf courses

    # Impervious
    PAVED = "paved"
    PAVED_ROAD_OPEN_DITCHES = "paved_road_open_ditches"  # Including right-of-way
    GRAVEL = "gravel"
    DIRT = "dirt"

    # Water
    WATER = "water"


_TABLE_PATH = Path(__file__).resolve().parents[1] / "_data" / "tables" / "tr55_cn.csv"
_HSG = ("A", "B", "C", "D")
_NONE = "none"


def _read_table() -> dict[tuple[str, str], dict[str, int]]:
    with _TABLE_PATH.open(encoding="utf-8", newline="") as handle:
        return {
            (row["land_cover"], row["condition"] or _NONE): {
                group: int(row[group]) for group in _HSG
            }
            for row in csv.DictReader(handle)
        }


_ROWS: Final = _read_table()
"""CN of each soil group by (land cover, condition); ``none`` for a single row."""

_CN_TABLE: Final[dict[tuple[LandCover, HydrologicCondition | None], dict[str, int]]] = {
    (
        LandCover(cover),
        None if condition == _NONE else HydrologicCondition(condition),
    ): (cns)
    for (cover, condition), cns in _ROWS.items()
}

_TR55 = Source(
    citation="USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical "
    "Release 55, 2nd ed. (210-VI-TR-55, June 1986)",
    locator="tables 2-2a, 2-2b and 2-2c, pp. 2-5 to 2-7; table 2-2d, footnote 1, "
    "p. 2-8",
    url="https://www.hydrocad.net/pdf/TR-55%20Manual.pdf",
)


def _cn(x: Values) -> int:
    return _ROWS[(x.choice("land_cover"), x.choice("condition"))][x.choice("hsg")]


def _groups_in_order(run: Callable[..., Values]) -> None:
    for cover, condition in _ROWS:
        cns = [
            run(hsg=group, land_cover=cover, condition=condition).integer("cn")
            for group in _HSG
        ]
        assert cns == sorted(cns), (cover, condition, cns)


TR55_CN: Final = FormulaSpec(
    name="tr55_cn",
    title="Curve number of a soil-cover complex from the TR-55 tables",
    function="hydrolog.runoff.cn_lookup.table_curve_number",
    family="classification",
    equation="CN = T(land cover, condition, hydrologic soil group), T the TR-55 table",
    latex=r"CN = T(\text{cover}, \text{condition}, \text{HSG})",
    variables=(
        Variable(
            name="hsg",
            symbol=r"\text{HSG}",
            unit="-",
            kind="choice",
            description="Hydrologic soil group.",
            choices=_HSG,
        ),
        Variable(
            name="land_cover",
            symbol=r"\text{cover}",
            unit="-",
            kind="choice",
            description="Land cover class of Hydrolog.",
            choices=tuple(cover.value for cover in LandCover),
        ),
        Variable(
            name="condition",
            symbol=r"\text{condition}",
            unit="-",
            kind="choice",
            description="Hydrologic condition; none for a cover of a single row.",
            choices=("poor", "fair", "good", _NONE),
        ),
    ),
    outputs=(
        Output(
            name="cn",
            unit="-",
            kind="integer",
            symbol="CN",
            description="Curve number for ARC II and Ia = 0.2 S.",
            physical=Range(low=1.0, high=100.0),
        ),
    ),
    constraints=(
        Constraint(
            name="row_in_table",
            cls="precondition",
            check=lambda x: (x.choice("land_cover"), x.choice("condition")) in _ROWS,
            text="the table has a row of the land cover in the condition",
            source=_TR55,
            satisfied={"land_cover": "forest", "condition": "good"},
            violated={"land_cover": "row_crops", "condition": "fair"},
        ),
    ),
    sources=(
        _TR55,
        Source(
            citation="USDA-NRCS (2004). National Engineering Handbook, Part 630 "
            "Hydrology, Chapter 9: Hydrologic Soil-Cover Complexes",
            locator="p. 9-1: impervious and water surfaces are always assigned a CN "
            "of 98",
            url="https://www.hydrocad.net/neh/630ch9.pdf",
        ),
    ),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="groups_in_order",
                text="CN does not fall from group A to D in any row",
                check=_groups_in_order,
            ),
        ),
    ),
    validation=(
        "NEH 630-9 (p. 9-1) derives the CN of its complexes from annual floods of "
        "small agricultural watersheds of one soil group and one cover; the table "
        "gives no error statistic"
    ),
    formula_version=1,
    status="referenced",
    conventions=(
        "ARC (AMC) II and Ia = 0.2 S (TR-55 tables 2-2a to 2-2c, footnote 1)",
        (
            "herbaceous is the pasture, grassland or range row of table 2-2c, as "
            "footnote 1 of table 2-2d directs for range in humid regions; table "
            "2-2d itself (arid and semiarid rangelands) is not used"
        ),
        (
            "row crops and small grain are the straight-row rows of table 2-2b, poor "
            "and good only: TR-55 has no fair condition for them"
        ),
        "water is CN 98 (NEH 630-9 p. 9-1), not the 100 of some texts",
    ),
    no_traps_reason=(
        "a lookup of categorical keys: no numeric class limit and no series"
    ),
    reference_cases=("tests/fixtures/formulas/cn-table-cases.json",),
    tables=(
        Table(
            path="src/hydrolog/_data/tables/tr55_cn.csv",
            sha256="781fdd02b39aa868571ec09cb92516716a79c0d74a77640fe810e794cfd3a6e8",
            source=_TR55,
            comparison=(
                "tests/oracles/tr55_cn_text_layer.csv (transcribed from the PDF's "
                "text layer by tests/oracles/transcribe_tr55_cn.py) against "
                "tests/oracles/tr55_cn_hydrolog_0_8_1.csv (typed for Hydrolog 0.8.1), "
                "compared by tests/unit/test_formulas_cn_table.py"
            ),
        ),
    ),
    base={"land_cover": "pasture", "condition": "fair"},
)


def table_curve_number(hsg: str, land_cover: str, condition: str) -> int:
    """Return the curve number of a soil-cover complex, spec tr55_cn.

    Parameters
    ----------
    hsg : {"A", "B", "C", "D"}
        Hydrologic soil group.
    land_cover : str
        Land cover class (:class:`LandCover` value).
    condition : {"poor", "fair", "good", "none"}
        Hydrologic condition; ``none`` for a cover of a single row.

    Returns
    -------
    int
        Curve number.

    Raises
    ------
    InvalidParameterError
        If a choice is unknown or the table has no such row.
    """
    x = checked_inputs(TR55_CN, hsg=hsg, land_cover=land_cover, condition=condition)
    return checked_outputs(TR55_CN, {"cn": _cn(x)}).integer("cn")


SPECS: Final = (TR55_CN,)
"""The Tier A formula of the module."""

WEIGHTED_CN: Final = TierBSpec(
    name="weighted_cn",
    function="hydrolog.runoff.cn_lookup.calculate_weighted_cn",
    definition="CN_w = sum(A_j CN_j) / sum(A_j), the area-weighted mean CN of the "
    "parts",
    convention="areas or shares in any one unit; a part of zero area counts nothing",
    source=Source(
        citation="USDA-NRCS (2004). National Engineering Handbook, Part 630 Hydrology, "
        "Chapter 10",
        locator="example 10-4, p. 10-12 (also KZGW 2017 eq. 6.3)",
        url="https://www.hydrocad.net/neh/630ch10.pdf",
    ),
)

TIER_B: Final = (WEIGHTED_CN,)
"""The Tier B formula of the module (CMP-2.2)."""


@dataclass
class CNLookupResult(JsonResultMixin):
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
    condition: HydrologicCondition | None


def get_cn(
    hsg: str,
    land_cover: LandCover | str,
    condition: HydrologicCondition | str | None = None,
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
        Hydrologic condition for land covers that support it. Without it a cover
        with a fair row takes FAIR; row crops and small grain, which TR-55 gives in
        poor and good condition only, need it. Ignored for a cover of one row.

    Returns
    -------
    int
        Curve Number (1-100), of spec ``tr55_cn``.

    Raises
    ------
    InvalidParameterError
        If HSG or land cover is invalid, or the cover has no row in the condition
        (``details.reason`` ``required`` without a condition, ``choice`` with
        another; ``details.allowed`` lists its conditions).

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
        raise InvalidParameterError(f"Invalid HSG: '{hsg}'. Must be one of: A, B, C, D")

    # Convert string to LandCover enum if needed
    if isinstance(land_cover, str):
        land_cover_str: str = land_cover
        try:
            land_cover = LandCover(land_cover_str.lower())
        except ValueError:
            # Try matching by name
            try:
                land_cover = LandCover[land_cover_str.upper()]
            except KeyError:
                valid = [lc.value for lc in LandCover]
                raise InvalidParameterError(
                    f"Invalid land cover: '{land_cover_str}'. Valid options: {valid}"
                ) from None

    # Convert string to HydrologicCondition if needed
    if isinstance(condition, str):
        try:
            condition = HydrologicCondition(condition.lower())
        except ValueError:
            valid = [hc.value for hc in HydrologicCondition]
            raise InvalidParameterError(
                f"Invalid condition: '{condition}'. Valid options: {valid}"
            ) from None

    conditions = [c for (cover, c) in _ROWS if cover == land_cover.value]
    if conditions == [_NONE]:
        return table_curve_number(hsg, land_cover.value, _NONE)
    wanted = condition.value if condition is not None else "fair"
    if wanted not in conditions:
        reason = "choice" if condition is not None else "required"
        raise InvalidParameterError(
            f"TR-55 gives '{land_cover.value}' in the conditions {conditions} only: "
            + ("give one of them" if condition is None else f"not '{wanted}'"),
            details={"option": "condition", "reason": reason, "allowed": conditions},
        )
    return table_curve_number(hsg, land_cover.value, wanted)


def lookup_cn(
    hsg: str,
    land_cover: LandCover | str,
    condition: HydrologicCondition | str | None = None,
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
        land_cover_str2: str = land_cover
        try:
            land_cover = LandCover(land_cover_str2.lower())
        except ValueError:
            land_cover = LandCover[land_cover_str2.upper()]

    if isinstance(condition, str):
        condition = HydrologicCondition(condition.lower())

    cn = get_cn(hsg, land_cover, condition)

    return CNLookupResult(
        cn=cn,
        hsg=hsg,
        land_cover=land_cover,
        condition=condition,
    )


def get_cn_range(land_cover: LandCover | str) -> dict[str, tuple[int, int]]:
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
        land_cover_str3: str = land_cover
        try:
            land_cover = LandCover(land_cover_str3.lower())
        except ValueError:
            land_cover = LandCover[land_cover_str3.upper()]

    result: dict[str, tuple[int, int]] = {}

    for hsg in ("A", "B", "C", "D"):
        cn_values = []

        # Collect all CN values for this land cover and HSG
        for (lc, _cond), cn_dict in _CN_TABLE.items():
            if lc == land_cover:
                cn_values.append(cn_dict[hsg])

        if cn_values:
            result[hsg] = (min(cn_values), max(cn_values))

    return result


def list_land_covers() -> dict[str, str]:
    """
    List all available land cover types.

    Returns
    -------
    dict
        Dictionary with land cover enum names as keys and values.
    """
    return {lc.name: lc.value for lc in LandCover}


def calculate_weighted_cn(
    cn_area_pairs: list[tuple[int, float]],
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
