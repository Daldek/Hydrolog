"""USDA soil texture triangle and the texture -> Hydrologic Soil Group mapping.

Classifies soil texture from clay, sand and silt contents with the canonical
USDA texture triangle (USDA Soil Survey Manual, Handbook 18) and maps the 12
texture classes to the Hydrologic Soil Groups (HSG) A-D of the SCS-CN method
(USDA-NRCS TR-55, National Engineering Handbook Part 630, Chapter 7).

The classifier and the texture -> HSG table are ported from Kartograf 0.8.0
(``kartograf.hydrology.hsg``, Kartograf ADR-025), where the HSG computation was
developed; computation needed for hydrology lives in Hydrolog.

Notes
-----
- **Amounts, not shares.** The rules compare the *amounts* of clay, sand and silt
  with their total and never divide them, so the classification does not depend on
  the unit (percent, g/kg, ...) as long as the three amounts share it. Every
  comparison is evaluated in ``float64``; integer inputs (the g/kg of SoilGrids) are
  therefore classified exactly, also on the boundaries of the triangle, where a
  computed share (``clay / total * 100``) would fall on either side by rounding.
- **First match wins.** On a few boundaries two rules both hold (for example
  ``clay = 27 %`` with ``20 < sand <= 45``: ``loam`` and ``clay_loam``); the
  order of the rules decides, as specified in Kartograf ADR-025.
- **Zero total is loam.** Cells whose amounts sum to zero carry no soil at all and
  are pinned to ``loam`` explicitly (the zeros would otherwise fall into the
  ``sand`` rule). :func:`hydrolog.soil.hsg.classify_hsg` masks such cells as
  no data.
- **Deviation from TR-55.** :data:`TEXTURE_TO_HSG` is deliberately milder than the
  TR-55 table: ``sandy_loam`` is B (TR-55: A) and ``clay_loam`` and
  ``silty_clay_loam`` are C (TR-55: D). These are transitional classes whose real
  group also depends on soil structure; the middle group is conservative for the
  SCS-CN method (Kartograf ADR-025, decision b). Changing the table changes the
  curve numbers of every consumer.
"""

import math
from collections.abc import Callable
from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog.exceptions import InvalidParameterError

__all__ = [
    "TEXTURE_CLASSES",
    "TEXTURE_NAMES",
    "TEXTURE_TO_HSG",
    "classify_usda_texture",
    "classify_usda_texture_array",
    "texture_to_hsg",
    "texture_to_hsg_array",
]

#: USDA texture class name -> class code (1-12). Code 0 is reserved for "no data".
TEXTURE_CLASSES: dict[str, int] = {
    "sand": 1,
    "loamy_sand": 2,
    "sandy_loam": 3,
    "loam": 4,
    "silt_loam": 5,
    "silt": 6,
    "sandy_clay_loam": 7,
    "clay_loam": 8,
    "silty_clay_loam": 9,
    "sandy_clay": 10,
    "silty_clay": 11,
    "clay": 12,
}

#: Class code (1-12) -> USDA texture class name (reverse of :data:`TEXTURE_CLASSES`).
TEXTURE_NAMES: dict[int, str] = {code: name for name, code in TEXTURE_CLASSES.items()}

#: Texture class -> Hydrologic Soil Group letter (Kartograf ADR-025; milder than
#: TR-55 for ``sandy_loam``, ``clay_loam`` and ``silty_clay_loam``, see module notes).
TEXTURE_TO_HSG: dict[str, str] = {
    "sand": "A",
    "loamy_sand": "A",
    "sandy_loam": "B",  # TR-55: A; A/B depending on soil structure
    "loam": "B",
    "silt_loam": "B",
    "silt": "B",
    "sandy_clay_loam": "C",
    "clay_loam": "C",  # TR-55: D; C/D depending on soil structure
    "silty_clay_loam": "C",  # TR-55: D; C/D depending on soil structure
    "sandy_clay": "D",
    "silty_clay": "D",
    "clay": "D",
}

# Hydrologic Soil Group letter -> raster code. Public home: hydrolog.soil.hsg
# (HSG_CODES); defined here because the texture -> HSG lookup below needs it and
# hydrolog.soil.hsg imports this module.
HSG_CODES: Final[dict[str, int]] = {"A": 1, "B": 2, "C": 3, "D": 4}

_LOAM: Final = TEXTURE_CLASSES["loam"]

_Amounts = NDArray[np.float64]
_Rule = Callable[[_Amounts, _Amounts, _Amounts, _Amounts], NDArray[np.bool_]]

# Canonical USDA texture triangle (Soil Survey Manual) - the SINGLE source of truth
# of the scalar and of the vectorised classifier (Kartograf ADR-025). In percent of
# clay (c), sand (s) and silt (si), first matching rule wins:
#
#   1. sand             si + 1.5*c < 15
#   2. loamy_sand       si + 1.5*c >= 15 and si + 2*c < 30
#   3. sandy_loam       (7 <= c <= 20 and s > 52 and si + 2*c >= 30)
#                       or (c < 7 and si < 50 and si + 2*c >= 30)
#   4. silt             si >= 80 and c < 12
#   5. silt_loam        (si >= 50 and 12 <= c < 27) or (50 <= si < 80 and c < 12)
#   6. loam             7 <= c <= 27 and 28 <= si < 50 and s <= 52
#   7. sandy_clay_loam  20 <= c < 35 and si < 28 and s > 45
#   8. clay_loam        27 <= c < 40 and 20 < s <= 45
#   9. silty_clay_loam  27 <= c < 40 and s <= 20
#  10. sandy_clay       c >= 35 and s > 45
#  11. silty_clay       c >= 40 and si >= 40
#  12. clay             c >= 40 and s <= 45 and si < 40
#
# A predicate gets 100 x the amounts (``c``, ``s``, ``si``) and their total ``u``:
# the share of clay in percent is ``c / u``, so "k percent" is ``k * u``. The
# rules therefore compare amounts and never divide them, which keeps every
# comparison exact.
_USDA_RULES: tuple[tuple[str, _Rule], ...] = (
    ("sand", lambda c, s, si, u: si + 1.5 * c < 15 * u),
    (
        "loamy_sand",
        lambda c, s, si, u: (si + 1.5 * c >= 15 * u) & (si + 2 * c < 30 * u),
    ),
    (
        "sandy_loam",
        lambda c, s, si, u: (
            ((c >= 7 * u) & (c <= 20 * u) & (s > 52 * u) & (si + 2 * c >= 30 * u))
            | ((c < 7 * u) & (si < 50 * u) & (si + 2 * c >= 30 * u))
        ),
    ),
    ("silt", lambda c, s, si, u: (si >= 80 * u) & (c < 12 * u)),
    (
        "silt_loam",
        lambda c, s, si, u: (
            ((si >= 50 * u) & (c >= 12 * u) & (c < 27 * u))
            | ((si >= 50 * u) & (si < 80 * u) & (c < 12 * u))
        ),
    ),
    (
        "loam",
        lambda c, s, si, u: (
            (c >= 7 * u)
            & (c <= 27 * u)
            & (si >= 28 * u)
            & (si < 50 * u)
            & (s <= 52 * u)
        ),
    ),
    (
        "sandy_clay_loam",
        lambda c, s, si, u: (c >= 20 * u) & (c < 35 * u) & (si < 28 * u) & (s > 45 * u),
    ),
    (
        "clay_loam",
        lambda c, s, si, u: (c >= 27 * u) & (c < 40 * u) & (s > 20 * u) & (s <= 45 * u),
    ),
    (
        "silty_clay_loam",
        lambda c, s, si, u: (c >= 27 * u) & (c < 40 * u) & (s <= 20 * u),
    ),
    ("sandy_clay", lambda c, s, si, u: (c >= 35 * u) & (s > 45 * u)),
    ("silty_clay", lambda c, s, si, u: (c >= 40 * u) & (si >= 40 * u)),
    ("clay", lambda c, s, si, u: (c >= 40 * u) & (s <= 45 * u) & (si < 40 * u)),
)


def _build_hsg_lookup() -> NDArray[np.uint8]:
    """Lookup table texture code (0-12) -> HSG code (0 = no data, 1-4 = A-D)."""
    lookup = np.zeros(len(TEXTURE_CLASSES) + 1, dtype=np.uint8)
    for name, code in TEXTURE_CLASSES.items():
        lookup[code] = HSG_CODES[TEXTURE_TO_HSG[name]]
    return lookup


_HSG_OF_TEXTURE: Final = _build_hsg_lookup()


def _amounts(
    clay: ArrayLike, sand: ArrayLike, silt: ArrayLike
) -> tuple[_Amounts, _Amounts, _Amounts]:
    """Clay, sand and silt as ``float64`` arrays of one shape.

    Raises
    ------
    InvalidParameterError
        If a value is not numeric or the shapes differ.
    """
    arrays = []
    for name, values in (("clay", clay), ("sand", sand), ("silt", silt)):
        try:
            arrays.append(np.asarray(values, dtype=np.float64))
        except (TypeError, ValueError) as exc:
            raise InvalidParameterError(
                f"{name} must contain only numbers",
                details={"option": name},
            ) from exc
    shapes = [array.shape for array in arrays]
    if not shapes[0] == shapes[1] == shapes[2]:
        raise InvalidParameterError(
            f"clay, sand and silt must have the same shape, got {shapes[0]}, "
            f"{shapes[1]} and {shapes[2]}",
            details={"options": ["clay", "sand", "silt"]},
        )
    return arrays[0], arrays[1], arrays[2]


def _reject_negative(name: str, values: _Amounts) -> None:
    """Raise if ``values`` holds a negative amount (NaN is not negative)."""
    negative = values < 0
    if negative.any():
        lowest = float(values[negative].min())
        raise InvalidParameterError(
            f"{name} must not be negative, got {lowest}",
            details={"option": name, "value": lowest},
        )


def _texture_codes(clay: _Amounts, sand: _Amounts, silt: _Amounts) -> NDArray[np.uint8]:
    """Texture class codes (1-12) of validated ``float64`` amounts of one shape."""
    total = clay + sand + silt
    c, s, si = 100 * clay, 100 * sand, 100 * silt
    masks = [rule(c, s, si, total) for _, rule in _USDA_RULES]
    codes = [TEXTURE_CLASSES[name] for name, _ in _USDA_RULES]
    selected = np.select(masks, codes, default=_LOAM)

    # The rules cover the whole simplex, but cells with a zero total are not soil
    # at all - pin them to "loam" explicitly instead of letting the zeros fall
    # into the "sand" rule (NaN totals end up here as well).
    return np.where(total > 0, selected, _LOAM).astype(np.uint8)


def classify_usda_texture(clay: float, sand: float, silt: float) -> str:
    """
    Classify soil texture according to the USDA texture triangle.

    Canonical USDA texture triangle (Soil Survey Manual), the same rule list as
    the vectorised :func:`classify_usda_texture_array`.

    Parameters
    ----------
    clay : float
        Clay amount [%] (or any unit shared by the three arguments, e.g. g/kg).
    sand : float
        Sand amount, in the same unit.
    silt : float
        Silt amount, in the same unit.

    Returns
    -------
    str
        USDA texture class name (a key of :data:`TEXTURE_CLASSES`).

    Raises
    ------
    InvalidParameterError
        If an amount is not a finite number or is negative.

    Notes
    -----
    The amounts are compared with their total, so they need not sum to 100 and any
    consistent unit works. Amounts summing to 0 (no data) return ``"loam"``.

    Examples
    --------
    >>> classify_usda_texture(clay=5, sand=90, silt=5)
    'sand'
    >>> classify_usda_texture(clay=450, sand=200, silt=350)  # g/kg
    'clay'
    """
    values = []
    for name, value in (("clay", clay), ("sand", sand), ("silt", silt)):
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise InvalidParameterError(
                f"{name} must be a number, got {value!r}", details={"option": name}
            ) from exc
        if not math.isfinite(number) or number < 0:
            raise InvalidParameterError(
                f"{name} must be a finite number >= 0, got {number}",
                details={"option": name, "value": number},
            )
        values.append(np.array([number], dtype=np.float64))
    code = int(_texture_codes(values[0], values[1], values[2])[0])
    return TEXTURE_NAMES[code]


def classify_usda_texture_array(
    clay: ArrayLike, sand: ArrayLike, silt: ArrayLike
) -> NDArray[np.uint8]:
    """
    Classify soil texture for arrays (vectorised).

    Uses the same canonical rule list as :func:`classify_usda_texture`, evaluated
    in ``float64`` on the amounts and their total: a share is never computed
    (``clay / total * 100`` rounds, so a value exactly on a boundary of the
    triangle - silt + 2 * clay = 300 g/kg, clay = 270 g/kg - would fall on either
    side by the rounding). Integers (the g/kg of SoilGrids) are therefore
    classified exactly by the rules.

    Parameters
    ----------
    clay : array_like
        Clay amounts [%] (or any unit shared by the three arguments, e.g. g/kg).
    sand : array_like
        Sand amounts, in the same unit and of the same shape.
    silt : array_like
        Silt amounts, in the same unit and of the same shape.

    Returns
    -------
    NDArray[np.uint8]
        Texture class codes (1-12, see :data:`TEXTURE_CLASSES`) in the shape of
        the inputs. Cells whose amounts sum to 0 (no data) get ``loam``.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in shape, hold non-numeric values or hold a
        negative amount.

    Notes
    -----
    NaN amounts do not raise: a NaN total is not positive, so the cell gets
    ``loam`` like a zero total. Use :func:`hydrolog.soil.hsg.classify_hsg` to turn
    such cells into no data.

    Examples
    --------
    >>> codes = classify_usda_texture_array([5, 55], [90, 25], [5, 20])
    >>> [TEXTURE_NAMES[int(code)] for code in codes]
    ['sand', 'clay']
    """
    clay_a, sand_a, silt_a = _amounts(clay, sand, silt)
    for name, values in (("clay", clay_a), ("sand", sand_a), ("silt", silt_a)):
        _reject_negative(name, values)
    return _texture_codes(clay_a, sand_a, silt_a)


def texture_to_hsg(texture_class: str) -> str:
    """
    Map a USDA texture class to its Hydrologic Soil Group.

    Parameters
    ----------
    texture_class : str
        USDA texture class name (a key of :data:`TEXTURE_CLASSES`).

    Returns
    -------
    str
        Hydrologic Soil Group letter: ``"A"``, ``"B"``, ``"C"`` or ``"D"``.

    Raises
    ------
    InvalidParameterError
        If ``texture_class`` is not one of the 12 USDA classes.

    Examples
    --------
    >>> texture_to_hsg("sandy_loam")
    'B'
    """
    try:
        return TEXTURE_TO_HSG[texture_class]
    except (KeyError, TypeError) as exc:
        raise InvalidParameterError(
            f"Unknown texture class {texture_class!r}",
            details={"option": "texture_class", "allowed": list(TEXTURE_CLASSES)},
        ) from exc


def texture_to_hsg_array(texture: ArrayLike) -> NDArray[np.uint8]:
    """
    Map an array of texture class codes to Hydrologic Soil Group codes.

    Parameters
    ----------
    texture : array_like
        Integer texture class codes: 1-12 (see :data:`TEXTURE_CLASSES`) or 0 for
        no data.

    Returns
    -------
    NDArray[np.uint8]
        HSG codes in the shape of ``texture``: 1-4 for A-D, 0 for no data.

    Raises
    ------
    InvalidParameterError
        If ``texture`` is not an integer array or holds codes outside 0-12.

    Examples
    --------
    >>> texture_to_hsg_array([1, 4, 8, 12, 0]).tolist()
    [1, 2, 3, 4, 0]
    """
    codes = np.asarray(texture)
    if codes.dtype.kind not in "iu":
        raise InvalidParameterError(
            f"texture codes must be integers, got dtype {codes.dtype}",
            details={"option": "texture"},
        )
    if codes.size and (
        int(codes.min()) < 0 or int(codes.max()) >= len(_HSG_OF_TEXTURE)
    ):
        raise InvalidParameterError(
            f"texture codes must be in 0-{len(TEXTURE_CLASSES)}, got values from "
            f"{int(codes.min())} to {int(codes.max())}",
            details={"option": "texture"},
        )
    return np.asarray(_HSG_OF_TEXTURE[codes])
