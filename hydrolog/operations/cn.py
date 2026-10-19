"""Operations of the group ``cn``: Curve Number tables and weighting (TR-55).

Wrappers over :func:`~hydrolog.runoff.get_cn`, :func:`~hydrolog.runoff.get_cn_range`
and :func:`~hydrolog.runoff.calculate_weighted_cn`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, cast, get_args

from hydrolog._serialization import JsonResultMixin
from hydrolog.catalog.envelope import Notice, OperationOutput
from hydrolog.exceptions import InvalidParameterError
from hydrolog.operations._common import (
    check_choice,
    option_error,
    real_number,
    select_group,
)
from hydrolog.runoff import (
    HydrologicCondition,
    LandCover,
    calculate_weighted_cn,
    get_cn,
    get_cn_range,
)

__all__ = [
    "CnBounds",
    "CnEntry",
    "CnList",
    "CnLookup",
    "CnRange",
    "CnWeighted",
    "cn_list",
    "cn_lookup",
    "cn_range",
    "cn_weighted",
]

Hsg = Literal["A", "B", "C", "D"]
Condition = Literal["poor", "fair", "good"]
LandCoverName = Literal[
    "fallow",
    "row_crops",
    "small_grain",
    "pasture",
    "meadow",
    "brush",
    "forest",
    "herbaceous",
    "farmstead",
    "residential_low",
    "residential_medium",
    "residential_high",
    "commercial",
    "industrial",
    "open_space",
    "paved",
    "gravel",
    "dirt",
    "water",
]

HSG_GROUPS: tuple[str, ...] = get_args(Hsg)
CONDITIONS: tuple[str, ...] = get_args(Condition)
LAND_COVERS: tuple[str, ...] = get_args(LandCoverName)

_FRACTION_SUM_TOLERANCE = 1e-3


@dataclass
class CnLookup(JsonResultMixin):
    """One CN read from the TR-55 tables.

    Attributes
    ----------
    cn : int
        Curve Number for AMC II.
    hsg : str
        Hydrologic soil group, ``"A"``-``"D"``.
    land_cover : str
        Land cover class (value of :class:`~hydrolog.runoff.LandCover`).
    condition : str or None
        Hydrologic condition as requested (``None`` when not given).
    condition_applied : str or None
        Condition the CN belongs to: the requested one, ``"fair"`` when a
        condition-dependent cover was looked up without a condition, ``None`` for
        covers with a single value.
    """

    cn: int
    hsg: str
    land_cover: str
    condition: str | None
    condition_applied: str | None


@dataclass
class CnEntry(JsonResultMixin):
    """One row of the TR-55 table.

    Attributes
    ----------
    land_cover : str
        Land cover class.
    condition : str or None
        Hydrologic condition of the row (``None`` for single-value covers).
    cn : dict of str to int
        CN of the soil groups ``"A"``-``"D"``.
    """

    land_cover: str
    condition: str | None
    cn: dict[str, int]


@dataclass
class CnList(JsonResultMixin):
    """The whole TR-55 table.

    Attributes
    ----------
    hsg : list of str
        Soil groups of the columns.
    entries : list of CnEntry
        One row per land cover and hydrologic condition.
    """

    hsg: list[str]
    entries: list[CnEntry]


@dataclass
class CnBounds(JsonResultMixin):
    """Lowest and highest CN of a land cover in one soil group.

    Attributes
    ----------
    minimum, maximum : int
        Bounds over the hydrologic conditions.
    """

    minimum: int
    maximum: int


@dataclass
class CnRange(JsonResultMixin):
    """CN range of one land cover.

    Attributes
    ----------
    land_cover : str
        Land cover class.
    conditions : list of str
        Hydrologic conditions the range spans (empty for single-value covers).
    by_hsg : dict of str to CnBounds
        Bounds per soil group.
    """

    land_cover: str
    conditions: list[str]
    by_hsg: dict[str, CnBounds]


@dataclass
class CnWeighted(JsonResultMixin):
    """Area-weighted Curve Number.

    Attributes
    ----------
    cn : float
        Weighted CN, ``sum(cn_i * w_i) / sum(w_i)``.
    n_parts : int
        Number of parts.
    total_area : float or None
        Sum of the given areas (their unit); ``None`` when shares were given.
    shares : list of float
        Share of each part in the total weight (sums to 1).
    """

    cn: float
    n_parts: int
    total_area: float | None
    shares: list[float] = field(default_factory=list)


def _conditions(land_cover: LandCover) -> list[str]:
    """Hydrologic conditions with their own table row (empty: a single row)."""
    if all(low == high for low, high in get_cn_range(land_cover).values()):
        return []
    found: list[str] = []
    for condition in HydrologicCondition:
        try:
            get_cn("A", land_cover, condition)
        except InvalidParameterError:
            continue
        found.append(condition.value)
    return found


def cn_lookup(
    *,
    hsg: Hsg,
    land_cover: LandCoverName,
    condition: Condition | None = None,
) -> OperationOutput:
    """Curve Number from the TR-55 tables (``cn lookup``).

    Parameters
    ----------
    hsg : {"A", "B", "C", "D"}
        Hydrologic soil group.
    land_cover : str
        Land cover class (see :data:`LAND_COVERS`).
    condition : {"poor", "fair", "good"}, optional
        Hydrologic condition; ``fair`` is assumed for condition-dependent covers
        when it is omitted, and it is ignored for single-value covers.

    Returns
    -------
    OperationOutput
        :class:`CnLookup`; an info notice says when the condition was defaulted or
        ignored.

    Raises
    ------
    InvalidParameterError
        If ``hsg``, ``land_cover`` or ``condition`` is not an allowed value.
    """
    group = check_choice("hsg", hsg, HSG_GROUPS)
    cover = check_choice("land_cover", land_cover, LAND_COVERS)
    if condition is not None:
        check_choice("condition", condition, CONDITIONS)
    cn = get_cn(group, cover, condition)
    conditional = bool(_conditions(LandCover(cover)))
    applied = (condition or "fair") if conditional else None
    notices: list[Notice] = []
    if conditional and condition is None:
        notices.append(
            Notice(
                "info",
                "condition_defaulted",
                f"No hydrologic condition given for {cover!r}: 'fair' was used.",
            )
        )
    elif not conditional and condition is not None:
        notices.append(
            Notice(
                "info",
                "condition_ignored",
                f"{cover!r} has a single CN: condition {condition!r} was ignored.",
            )
        )
    result = CnLookup(
        cn=cn,
        hsg=group,
        land_cover=cover,
        condition=condition,
        condition_applied=applied,
    )
    return OperationOutput(result, notices)


def cn_list() -> CnList:
    """The whole TR-55 table (``cn list``).

    Returns
    -------
    CnList
        One entry per land cover and hydrologic condition, each with the CN of the
        soil groups A-D.
    """
    entries: list[CnEntry] = []
    for land_cover in LandCover:
        conditions: list[str | None] = [*_conditions(land_cover)] or [None]
        for condition in conditions:
            entries.append(
                CnEntry(
                    land_cover=land_cover.value,
                    condition=condition,
                    cn={hsg: get_cn(hsg, land_cover, condition) for hsg in HSG_GROUPS},
                )
            )
    return CnList(hsg=list(HSG_GROUPS), entries=entries)


def cn_range(*, land_cover: LandCoverName) -> CnRange:
    """CN range of a land cover (``cn range``).

    Parameters
    ----------
    land_cover : str
        Land cover class (see :data:`LAND_COVERS`).

    Returns
    -------
    CnRange
        Lowest and highest CN per soil group over the hydrologic conditions.

    Raises
    ------
    InvalidParameterError
        If ``land_cover`` is not an allowed value.
    """
    cover = check_choice("land_cover", land_cover, LAND_COVERS)
    bounds = {
        hsg: CnBounds(minimum=low, maximum=high)
        for hsg, (low, high) in get_cn_range(cover).items()
    }
    return CnRange(
        land_cover=cover,
        conditions=_conditions(LandCover(cover)),
        by_hsg=bounds,
    )


def _weights_from_parts(
    parts: list[dict[str, Any]],
) -> tuple[list[float], list[float], bool]:
    """CN values, weights and the weight kind (``True``: shares) of ``parts``."""
    cn_values: list[float] = []
    weights: list[float] = []
    kinds: set[str] = set()
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            raise option_error(
                "parts",
                "type",
                f"Option 'parts[{index}]' must be an object with 'cn' and "
                "'area' or 'fraction'",
                index=index,
            )
        unknown = sorted(set(part) - {"cn", "area", "fraction"})
        if unknown:
            raise option_error(
                "parts",
                "unknown_key",
                f"Option 'parts[{index}]' has unknown keys: {', '.join(unknown)}",
                hint="Allowed keys: cn, area, fraction.",
                index=index,
                keys=unknown,
            )
        if part.get("cn") is None:
            raise option_error(
                "parts", "required", f"Option 'parts[{index}]' needs 'cn'", index=index
            )
        kind = [key for key in ("area", "fraction") if part.get(key) is not None]
        if len(kind) != 1:
            raise option_error(
                "parts",
                "one_of",
                f"Option 'parts[{index}]' needs exactly one of 'area' and 'fraction'",
                index=index,
                groups=[["area"], ["fraction"]],
            )
        kinds.add(kind[0])
        cn_values.append(real_number("parts", part["cn"], index=index))
        weights.append(real_number("parts", part[kind[0]], index=index))
    if len(kinds) > 1:
        raise option_error(
            "parts",
            "conflict",
            "Option 'parts' mixes 'area' and 'fraction' weights",
            hint="Give all parts either 'area' or 'fraction'.",
        )
    return cn_values, weights, kinds == {"fraction"}


def _weights_from_lists(
    cn_values: list[float], areas: list[float] | None, fractions: list[float] | None
) -> tuple[list[float], list[float], bool]:
    """CN values, weights and the weight kind of two parallel lists."""
    shares = fractions is not None
    name = "fractions" if shares else "areas"
    values = fractions if shares else areas
    assert values is not None
    if len(values) != len(cn_values):
        lengths: dict[str, Any] = {"cn_values": len(cn_values), name: len(values)}
        raise option_error(
            name,
            "length_mismatch",
            f"{len(values)} {name} for {len(cn_values)} cn_values",
            **lengths,
        )
    cns = [real_number("cn_values", item, index=i) for i, item in enumerate(cn_values)]
    weights = [real_number(name, item, index=i) for i, item in enumerate(values)]
    return cns, weights, shares


def cn_weighted(
    *,
    parts: list[dict[str, Any]] | None = None,
    cn_values: list[float] | None = None,
    areas: list[float] | None = None,
    fractions: list[float] | None = None,
) -> CnWeighted:
    """Area-weighted Curve Number (``cn weighted``).

    Give exactly one of ``parts``, ``cn_values`` with ``areas``, or ``cn_values``
    with ``fractions``.

    Parameters
    ----------
    parts : list of dict, optional
        Objects ``{"cn": ..., "area": ...}`` or ``{"cn": ..., "fraction": ...}``.
    cn_values : list of float, optional
        CN of each part, 1-100.
    areas : list of float, optional
        Area of each part (any consistent unit, >= 0).
    fractions : list of float, optional
        Share of each part, 0-1; must sum to 1 within 0.001.

    Returns
    -------
    CnWeighted
        The weighted CN (as computed by
        :func:`~hydrolog.runoff.calculate_weighted_cn`), the number of parts, the
        total area and the share of each part.

    Raises
    ------
    InvalidParameterError
        If the combination of options is wrong (``reason = "one_of"`` or
        ``"conflict"``), the lists differ in length, a CN is outside 1-100, an
        area is negative or all areas are zero, a share is outside 0-1, or the
        shares do not sum to 1.
    """
    select_group(
        {
            "parts": parts,
            "cn_values": cn_values,
            "areas": areas,
            "fractions": fractions,
        },
        {
            "parts": ("parts",),
            "areas": ("cn_values", "areas"),
            "fractions": ("cn_values", "fractions"),
        },
    )
    if parts is not None:
        cns, weights, shares = _weights_from_parts(parts)
        name = "parts"
    else:
        assert cn_values is not None
        cns, weights, shares = _weights_from_lists(cn_values, areas, fractions)
        name = "fractions" if shares else "areas"
    for index, (cn, weight) in enumerate(zip(cns, weights)):
        if not 1 <= cn <= 100:
            raise option_error(
                name if parts is not None else "cn_values",
                "minimum" if cn < 1 else "maximum",
                f"CN must be 1-100, got {cn} (part {index})",
                index=index,
                value=cn,
            )
        if weight < 0 or (shares and weight > 1):
            kind = "Share" if shares else "Area"
            limits = "within 0-1" if shares else "non-negative"
            raise option_error(
                name,
                "minimum" if weight < 0 else "maximum",
                f"{kind} of part {index} must be {limits}, got {weight}",
                index=index,
                value=weight,
            )
    total_weight = sum(weights)
    if shares and abs(total_weight - 1.0) > _FRACTION_SUM_TOLERANCE:
        raise option_error(
            name,
            "fraction_sum",
            f"Shares must sum to 1 (tolerance {_FRACTION_SUM_TOLERANCE}), got "
            f"{total_weight:.6g}",
            hint="Give absolute values or percentages as areas instead.",
            sum=total_weight,
        )
    if total_weight <= 0:
        raise option_error(
            name,
            "zero_total",
            "The total area of the parts must be positive",
            hint="Give at least one part with a positive area.",
        )
    # calculate_weighted_cn is annotated with int CN but averages any real number.
    pairs = cast(list[tuple[int, float]], list(zip(cns, weights)))
    return CnWeighted(
        cn=calculate_weighted_cn(pairs),
        n_parts=len(cns),
        total_area=None if shares else total_weight,
        shares=[weight / total_weight for weight in weights],
    )
