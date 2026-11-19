"""USDA soil texture triangle and the texture -> Hydrologic Soil Group mapping.

Classifies soil texture from clay, sand and silt amounts with the twelve classes of
the USDA texture triangle (spec :data:`USDA_TEXTURE`, ``usda_texture``) and maps the
classes to the Hydrologic Soil Groups (HSG) A-D of the SCS-CN method (spec
:data:`TEXTURE_HSG`, ``texture_hsg``). Both tables are data files (Nogat CMP-2.5),
declared with their sources and SHA-256 by the specs, whose cards are in
``docs/FORMULAS.md``:

- ``hydrolog/_data/tables/usda_texture_classes.csv``: the class definitions of the
  Soil Survey Manual (Soil Science Division Staff 2017, USDA Agriculture Handbook 18,
  ch. 3, pp. 122-124, Fig. 3-7 p. 125), one row per inequality
  ``a clay + b sand + c silt <relation> k percent of clay + sand + silt``; a class
  holds where every row of one of its alternatives holds (sandy loam and silt loam
  have two).
- ``hydrolog/_data/tables/texture_hsg.csv``: the group of each class with the source
  it follows.

The classifier and the table were ported from Kartograf 0.8.0
(``kartograf.hydrology.hsg``, Kartograf ADR-025), where the HSG computation was
developed; computation needed for hydrology lives in Hydrolog. Kartograf 0.8.2 gives
the same class on every integer composition in percent and in g/kg (the frozen
oracles of ``tests/oracles/``).

Notes
-----
- **Amounts, not shares.** The rows compare the *amounts* of clay, sand and silt
  with their total and never divide them, so the classification does not depend on
  the unit (percent, g/kg, ...) as long as the three amounts share it. Every
  comparison is evaluated in ``float64`` after scaling the three amounts by one power
  of two (exact); integer amounts (the g/kg of SoilGrids, lab percentages) are
  therefore classified exactly, also on the limits of the classes, where a computed
  share (``clay / total * 100``) would fall on either side by rounding.
- **No ties.** The twelve definitions do not overlap and leave no gap: every
  composition belongs to exactly one class. "X to less than Y percent" includes X
  and excludes Y: clay 20 % with more than 52 % sand is ``sandy_clay_loam``
  (sandy loams have "7 to less than 20 percent clay"), and clay 27 % with 28 to less
  than 50 % silt is ``clay_loam`` (loam has "7 to less than 27 percent clay").
- **A zero total has no texture.** :func:`classify_usda_texture` refuses amounts
  that sum to zero (precondition ``positive_total``). The array variant
  :func:`classify_usda_texture_array` gives such a cell, and a cell with a NaN or an
  infinite amount, the code of ``loam`` as a no-data placeholder (Tier B
  ``usda_texture_codes``), which :func:`hydrolog.soil.hsg.classify_hsg` masks as no
  data.
- **The groups are a hybrid of TR-55 and NEH 630.** :data:`TEXTURE_TO_HSG` follows
  TR-55 (1986, appendix A, p. A-1) for eight classes and the "typical" textures of
  NEH 630 ch. 7 (2009, p. 7-2) for three: ``sandy_loam`` is B where TR-55 has A
  (a stricter group, a higher curve number), ``clay_loam`` and ``silty_clay_loam``
  are C where TR-55 has D (a milder group, a lower curve number); ``silt``, which
  TR-55 does not list, takes the B of silt loam (Kartograf ADR-025, decision b).
  Changing the table changes the curve numbers of every consumer.

Examples
--------
>>> classify_usda_texture(clay=5, sand=90, silt=5)
'sand'
>>> classify_usda_texture(clay=450, sand=200, silt=350)  # g/kg
'clay'
>>> classify_usda_texture(clay=27, sand=38, silt=35)  # "27 to less than 40"
'clay_loam'
>>> texture_to_hsg("sandy_loam")
'B'
"""

import csv
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from hydrolog._formula_versions import record
from hydrolog._formulas import checked_inputs, checked_outputs
from hydrolog.exceptions import CalculationError, InvalidParameterError
from hydrolog.nogat_formulas import (
    Constraint,
    FormulaSpec,
    Limit,
    Oracle,
    Output,
    Properties,
    Range,
    Scaling,
    Source,
    Table,
    TierBSpec,
    Tolerance,
    Values,
    Variable,
)

__all__ = [
    "TEXTURE_CLASSES",
    "TEXTURE_HSG",
    "TEXTURE_NAMES",
    "TEXTURE_TO_HSG",
    "USDA_TEXTURE",
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

# Hydrologic Soil Group letter -> raster code. Public home: hydrolog.soil.hsg
# (HSG_CODES); defined here because the texture -> HSG lookup below needs it and
# hydrolog.soil.hsg imports this module.
HSG_CODES: Final[dict[str, int]] = {"A": 1, "B": 2, "C": 3, "D": 4}

_LOAM: Final = TEXTURE_CLASSES["loam"]
_TABLES: Final = Path(__file__).resolve().parents[1] / "_data" / "tables"

_Amounts = NDArray[np.float64]

_RELATIONS: Final = {
    "<": np.less,
    "<=": np.less_equal,
    ">": np.greater,
    ">=": np.greater_equal,
}


@dataclass(frozen=True)
class _Inequality:
    """A row of the class table: ``clay c + sand s + silt si <relation> percent``."""

    clay: float
    sand: float
    silt: float
    relation: str
    percent: float


def _read_classes() -> dict[str, tuple[tuple[_Inequality, ...], ...]]:
    """Read the alternatives of each class (in code order), each a tuple of rows."""
    alternatives: dict[str, dict[str, list[_Inequality]]] = {
        name: {} for name in TEXTURE_CLASSES
    }
    path = _TABLES / "usda_texture_classes.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["relation"] not in _RELATIONS:
                raise ValueError(f"{path}: unknown relation {row['relation']!r}")
            alternatives[row["texture_class"]].setdefault(
                row["alternative"], []
            ).append(
                _Inequality(
                    clay=float(row["clay"]),
                    sand=float(row["sand"]),
                    silt=float(row["silt"]),
                    relation=row["relation"],
                    percent=float(row["percent"]),
                )
            )
    return {
        name: tuple(tuple(rows) for rows in by_alternative.values())
        for name, by_alternative in alternatives.items()
    }


def _read_groups() -> dict[str, str]:
    """Read the group of each class, in code order, from the data file."""
    with (_TABLES / "texture_hsg.csv").open(encoding="utf-8", newline="") as handle:
        groups = {row["texture_class"]: row["hsg"] for row in csv.DictReader(handle)}
    return {name: groups[name] for name in TEXTURE_CLASSES}


_CLASSES: Final = _read_classes()
"""The rows of every class of ``usda_texture_classes.csv``, by alternative."""

#: Texture class -> Hydrologic Soil Group letter, from ``texture_hsg.csv`` (spec
#: :data:`TEXTURE_HSG`; TR-55 appendix A with three classes of NEH 630 ch. 7, see
#: the module notes).
TEXTURE_TO_HSG: dict[str, str] = _read_groups()


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
    """Class codes (1-12) of finite, non-negative amounts; 0 where no class holds.

    The amounts are first scaled by one power of two, so that the largest lies in
    [0.5, 1): exact in binary, and no product below can overflow. A row holds where
    ``100 (a clay + b sand + c silt) <relation> k (clay + sand + silt)``: for integer
    amounts (total below 10**13) every operand is an integer below 2**53 times that
    power of two, so every comparison is exact. A zero total satisfies no class.
    """
    _, exponent = np.frexp(np.maximum(np.maximum(clay, sand), silt))
    clay, sand, silt = (np.ldexp(x, -exponent) for x in (clay, sand, silt))
    total = clay + sand + silt
    holds = []
    for alternatives in _CLASSES.values():
        found = np.zeros(total.shape, dtype=np.bool_)
        for rows in alternatives:
            every = np.ones(total.shape, dtype=np.bool_)
            for row in rows:
                amount = 100 * (row.clay * clay + row.sand * sand + row.silt * silt)
                every &= _RELATIONS[row.relation](amount, row.percent * total)
            found |= every
        holds.append(found)
    return np.select(holds, list(TEXTURE_CLASSES.values()), default=0).astype(np.uint8)


_SSM_2017 = Source(
    citation="Soil Science Division Staff (2017). Soil Survey Manual. USDA "
    "Agriculture Handbook No. 18 (minor amendments February 2018). USDA-NRCS, "
    "Washington, DC",
    locator="ch. 3, 'Definitions of Soil Texture Classes and Subclasses', pp. 122-124 "
    "(sands and loamy sands p. 122, sandy loams p. 123, loam to clay p. 124); the "
    "textural triangle, Fig. 3-7, p. 125",
    url="https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo113168/pdf/"
    "GOVPUB-A-PURL-gpo113168.pdf",
)
_SOILGRIDS = Source(
    citation="ISRIC - World Soil Information (2026). SoilGrids FAQ, 'Which soil "
    "properties are predicted': clay, sand and silt of the fine earth in g/kg",
    locator="the data Kartograf downloads for Hydrolog's soil hsg: integers 0 to 1000 "
    "g/kg; soil texture takes percent (0 to 100) or g/kg",
    url="https://www.isric.org/explore/soilgrids/faq-soilgrids",
)
_SCALE_FREE = (
    (5, 90, 5),
    (20, 60, 20),
    (19, 61, 20),
    (27, 38, 35),
    (26, 39, 35),
    (0, 70, 30),
    (0, 85, 15),
    (7, 45, 48),
    (45, 20, 35),
    (12, 8, 80),
)
"""Compositions in percent, among them points on class limits, for ``unit_free``."""


def _unit_free(run: Callable[..., Values]) -> None:
    for clay, sand, silt in _SCALE_FREE:
        here = run(clay=float(clay), sand=float(sand), silt=float(silt))
        for factor in (10.0, 1000.0, 2.0**-7, 3.0):
            there = run(clay=clay * factor, sand=sand * factor, silt=silt * factor)
            assert there.choice("texture_class") == here.choice("texture_class"), (
                clay,
                sand,
                silt,
                factor,
            )


def _amount(name: str, what: str) -> Variable:
    return Variable(
        name=name,
        symbol=rf"m_\mathrm{{{name}}}",
        unit="shared unit",
        description=f"Amount of {what} of the fine earth, in any unit the three "
        "amounts share (percent, g/kg); they need not sum to 100.",
        physical=Range(
            low=0.0,
            high=float("inf"),
            test_high=10_000.0,
            test_reason="ten times the largest amount of the ecosystem's data, 1000 "
            "g/kg of SoilGrids; the class depends on the shares only",
        ),
        applicability="unstated",
        typical=Range(low=0.0, high=1000.0, source=_SOILGRIDS),
    )


USDA_TEXTURE: Final = FormulaSpec(
    name="usda_texture",
    title="USDA soil texture class of clay, sand and silt amounts",
    function="hydrolog.soil.texture.classify_usda_texture",
    family="classification",
    equation="class = the class C of the table usda_texture_classes.csv for which "
    "every row (a, b, c, relation, k) of one alternative holds: 100 (a clay + b sand "
    "+ c silt) relation k (clay + sand + silt)",
    latex=r"\mathrm{class} = C \iff \exists j\ \forall (a, b, c, \sim, k) \in "
    r"T_{C,j}:\ 100\,(a\,m_\mathrm{clay} + b\,m_\mathrm{sand} + c\,m_\mathrm{silt}) "
    r"\sim k\,(m_\mathrm{clay} + m_\mathrm{sand} + m_\mathrm{silt})",
    variables=(
        _amount("clay", "clay (< 0.002 mm)"),
        _amount("sand", "sand (0.05 to 2 mm)"),
        _amount("silt", "silt (0.002 to 0.05 mm)"),
    ),
    outputs=(
        Output(
            name="texture_class",
            unit="-",
            kind="choice",
            symbol=r"\mathrm{class}",
            description="USDA texture class, one of the twelve of the Soil Survey "
            "Manual.",
            choices=tuple(TEXTURE_CLASSES),
        ),
    ),
    constraints=(
        Constraint(
            name="positive_total",
            cls="precondition",
            check=lambda x: x.real("clay") + x.real("sand") + x.real("silt") > 0,
            text="clay + sand + silt > 0",
            source=_SSM_2017,
            satisfied={"clay": 0.0, "sand": 5e-324, "silt": 0.0},
            violated={"clay": 0.0, "sand": 0.0, "silt": 0.0},
        ),
    ),
    sources=(_SSM_2017,),
    properties=Properties(
        units="homogeneous",
        scalings=(
            Scaling(
                name="shared_unit",
                inputs={"clay": 1.0, "sand": 1.0, "silt": 1.0},
                outputs={},
                tolerance=Tolerance(
                    abs=0.0,
                    reason="a class is not a number: the limit unit_free asserts the "
                    "same class",
                ),
            ),
        ),
        limits=(
            Limit(
                name="unit_free",
                text="multiplying the three amounts by one positive factor (10 from "
                "percent to g/kg, 1000, 3, a power of two) leaves the class unchanged, "
                "also on the limits of the classes",
                check=_unit_free,
            ),
        ),
    ),
    validation="none: the classes are defined by the Manual, not fitted to "
    "observations",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "amounts in any unit the three share (percent, g/kg), compared with "
            "their total: the class depends on the shares of clay + sand + silt "
            "only, which need not be 100 % (organic matter and gravel are outside "
            "the fine earth)"
        ),
        (
            "USDA separates: sand 0.05 to 2 mm, silt 0.002 to 0.05 mm, clay below "
            "0.002 mm (the PTG 2008 Polish classes use the same limits); the "
            "twelve classes cover every composition of the triangle, so no amount "
            "has an applicability range (unstated)"
        ),
        (
            "'X to less than Y percent' is X <= share < Y, 'more than X' is > X, "
            "'X or more' is >= X, 'X or less' is <= X, 'more than 20 to 45 "
            "percent sand' (clay loam) is 20 < sand <= 45, as the Manual words "
            "each class"
        ),
        (
            "the sand ranges the Manual also gives in words, sands 'more than 85 "
            "percent sand' and loamy sands 'between 70 and 90 percent sand', are "
            "implied by their other inequalities (silt + 1.5 clay < 15 gives sand "
            "> 85; silt + 1.5 clay >= 15 and silt + 2 clay < 30 give 70 < sand <= "
            "90) and are not rows of the table"
        ),
        (
            "float64 throughout, the amounts scaled by one power of two first; "
            "exact for integer amounts (total below 10**13); other amounts within "
            "a few units in the last place of a class limit may fall on either "
            "side of it, and where rounding lets two classes hold the first in the "
            "table's order is taken"
        ),
        (
            "a zero total has no texture and is refused (precondition "
            "positive_total); the array variant pins it to loam as no data (Tier B "
            "usda_texture_codes)"
        ),
    ),
    assumptions=(
        (
            "the amounts are of the fine earth (< 2 mm) of a mineral soil; the "
            "Manual's subclasses by sand size (coarse sand, fine sandy loam, ...) "
            "are not given"
        ),
    ),
    traps={
        "class_limit": "tests/unit/test_formulas_texture.py::"
        "test_every_row_of_the_table_at_its_limit_and_just_beyond: each row's limit "
        "on the integer percent and g/kg grids and one g/kg beyond, against the "
        "Manual's inclusive or exclusive wording; clay 20 and 27 % moved by "
        "math.nextafter",
        "gap_propagation": "tests/unit/test_formulas_texture.py::"
        "test_a_gap_is_refused_or_kept_as_no_data: NaN is refused "
        "(outside_physical_range); a NaN or infinite amount of the array variant "
        "gives its cell the loam placeholder and classify_hsg masks it as no data",
    },
    reference_cases=("tests/fixtures/formulas/texture-cases.json",),
    oracles=(
        Oracle(
            kind="frozen",
            description="Kartograf 0.8.2, kartograf.hydrology.hsg."
            "classify_usda_texture_array (its own copy of the rules), on all 5,151 "
            "integer percent and 501,501 integer g/kg compositions",
            test="tests/oracles/kartograf_0_8_2_texture_percent.csv and "
            "tests/oracles/kartograf_0_8_2_texture_gkg.csv (written once by "
            "tests/oracles/kartograf_texture_oracle.py), compared by "
            "tests/unit/test_formulas_texture.py",
            conventions=(
                "both: amounts compared with their total in float64, no division",
                (
                    "both classify a composition, not a share; the grids have no "
                    "zero total"
                ),
            ),
        ),
        Oracle(
            kind="exact",
            description="the package table evaluated in exact rationals "
            "(fractions.Fraction) on both integer grids and on drawn integer "
            "compositions",
            test="tests/unit/test_formulas_texture.py::"
            "test_the_table_in_rationals_agrees",
        ),
    ),
    tables=(
        Table(
            path="src/hydrolog/_data/tables/usda_texture_classes.csv",
            sha256="b957a339f36ec7c0ee82ec1f25e286e401f26afeffa85dcccca24f9a4e61c381",
            source=_SSM_2017,
            comparison="tests/oracles/usda_texture_classes_first.csv (typed from the "
            "Manual's text by the author of the spec) against "
            "tests/oracles/usda_texture_classes_second.csv (typed independently by a "
            "second agent from the same pages), compared with the data file by "
            "tests/unit/test_formulas_texture.py",
        ),
    ),
    base={"clay": 20.0, "sand": 40.0, "silt": 40.0},
)


def classify_usda_texture(clay: float, sand: float, silt: float) -> str:
    """Return the USDA texture class of clay, sand and silt amounts, spec usda_texture.

    Parameters
    ----------
    clay : float
        Clay amount, in any unit the three amounts share (percent, g/kg).
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
        If an amount is not a finite number or is negative, or the three sum to
        zero (``details.reason`` of the spec).
    """
    x = checked_inputs(USDA_TEXTURE, clay=clay, sand=sand, silt=silt)
    amounts = (np.array([x.real(name)]) for name in ("clay", "sand", "silt"))
    code = int(_texture_codes(*amounts)[0])
    outputs = {"texture_class": TEXTURE_NAMES.get(code, "")}
    return checked_outputs(USDA_TEXTURE, outputs).choice("texture_class")


_TR55_APP_A = Source(
    citation="USDA-SCS (1986). Urban Hydrology for Small Watersheds, Technical "
    "Release 55, 2nd ed. (210-VI-TR-55, June 1986)",
    locator="appendix A, p. A-1, 'Disturbed soil profiles': HSG by soil texture, "
    "after Brakensiek and Rawls (1983)",
    url="https://www.hydrocad.net/pdf/TR-55%20Manual.pdf",
)
_NEH_630_7 = Source(
    citation="USDA-NRCS (2009). National Engineering Handbook, Part 630 Hydrology, "
    "Chapter 7: Hydrologic Soil Groups (210-VI-NEH, January 2009)",
    locator="p. 7-2: the textures groups A to D 'typically' have; group B "
    "'loamy sand or sandy loam', group C 'loam, silt loam, sandy clay loam, clay "
    "loam, and silty clay loam', well aggregated silt may be B",
    url="https://www.hydrocad.net/neh/630ch7.pdf",
)
_RAWLS_1982 = Source(
    citation="Rawls, W. J., Brakensiek, D. L. and Saxton, K. E. (1982). Estimation "
    "of soil water properties. Transactions of the ASAE 25(5): 1316-1320, 1328",
    locator="Table 2: saturated hydraulic conductivity of eleven texture classes "
    "(no silt), quoted with the same values by MassDEP (2008), Massachusetts "
    "Stormwater Handbook, vol. 3, ch. 1, table 2.3.3, and by Kartograf 0.8.2 "
    "RAWLS_1982_KSAT_CM_H",
    access="author-provided",
)
_FALLING_KSAT = (
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
)
"""The classes of Rawls et al. (1982, Table 2) in the order of falling Ksat."""


def _not_milder_as_ksat_falls(run: Callable[..., Values]) -> None:
    groups = [run(texture_class=name).choice("hsg") for name in _FALLING_KSAT]
    assert groups == sorted(groups), list(zip(_FALLING_KSAT, groups, strict=True))


TEXTURE_HSG: Final = FormulaSpec(
    name="texture_hsg",
    title="Hydrologic soil group of a USDA texture class",
    function="hydrolog.soil.texture.texture_to_hsg",
    family="classification",
    equation="HSG = G(texture class), G the table texture_hsg.csv: TR-55 appendix A, "
    "with sandy loam B and clay loam and silty clay loam C as NEH 630 ch. 7's "
    "typical textures and silt B as silt loam",
    latex=r"\mathrm{HSG} = G(\mathrm{class})",
    variables=(
        Variable(
            name="texture_class",
            symbol=r"\mathrm{class}",
            unit="-",
            kind="choice",
            description="USDA texture class (spec usda_texture).",
            choices=tuple(TEXTURE_CLASSES),
        ),
    ),
    outputs=(
        Output(
            name="hsg",
            unit="-",
            kind="choice",
            symbol=r"\mathrm{HSG}",
            description="Hydrologic soil group, from A (low runoff potential) to D "
            "(high).",
            choices=tuple(HSG_CODES),
        ),
    ),
    sources=(_TR55_APP_A, _NEH_630_7),
    properties=Properties(
        units="unit_specific",
        limits=(
            Limit(
                name="not_milder_as_ksat_falls",
                text="along the classes in the order of falling saturated hydraulic "
                "conductivity of Rawls et al. (1982), sand, loamy sand, sandy loam, "
                "loam, silt loam, sandy clay loam, clay loam, silty clay loam, sandy "
                "clay, silty clay, clay, the group never gets milder (NEH 630 ch. 7 "
                "assigns the groups by falling Ksat; silt has no value)",
                check=_not_milder_as_ksat_falls,
                source=_RAWLS_1982,
            ),
        ),
    ),
    validation="none stated: TR-55 derives its texture groups from Brakensiek and "
    "Rawls (1983) for disturbed profiles; NEH 630 ch. 7 gives typical textures, "
    "not a fit",
    formula_version=1,
    status="referenced",
    conventions=(
        (
            "TR-55 appendix A gives the groups of disturbed soil profiles (urban "
            "areas, no significant compaction); the table applies them to every soil"
        ),
        (
            "documented deviations from TR-55 appendix A: sandy loam B (TR-55 A), "
            "clay loam and silty clay loam C (TR-55 D), as NEH 630 ch. 7 p. 7-2 names "
            "the typical textures of groups B and C (Kartograf ADR-025, decision b): "
            "stricter than TR-55 for sandy loam, milder for the two clay loams"
        ),
        (
            "silt, which TR-55 does not list, takes the group of silt loam, B; NEH "
            "630 ch. 7 p. 7-2 puts well aggregated silt in group B"
        ),
        (
            "NEH 630 ch. 7 would put loam and silt loam (and, by Ksat, silt) in C "
            "and loamy sand in B; the table keeps TR-55's groups for them (open "
            "question of ADR-0066)"
        ),
    ),
    assumptions=(
        (
            "the group of a texture alone: no water table, impermeable layer, rock "
            "fragments, bulk density or structure (NEH 630 ch. 7, table 7-1)"
        ),
    ),
    no_traps_reason="a lookup of a categorical key: no numeric class limit and no "
    "series",
    reference_cases=("tests/fixtures/formulas/hsg-cases.json",),
    oracles=(
        Oracle(
            kind="frozen",
            description="Kartograf 0.8.2, kartograf.hydrology.hsg.TEXTURE_TO_HSG "
            "(its own copy of the table, ADR-025)",
            test="tests/oracles/kartograf_0_8_2_texture_hsg.csv (written once by "
            "tests/oracles/kartograf_texture_oracle.py), compared by "
            "tests/unit/test_formulas_texture_hsg.py",
        ),
    ),
    tables=(
        Table(
            path="src/hydrolog/_data/tables/texture_hsg.csv",
            sha256="f8e1d4b427ae6bb4c0abf7afbbbf9a70f3c32c42de0b5fe5a0ee2157daebef4a",
            source=_TR55_APP_A,
            comparison="tests/oracles/tr55_hsg_text_layer.csv (read from the PDF's "
            "text layer by tests/oracles/transcribe_tr55_hsg.py) and "
            "tests/oracles/kartograf_0_8_2_texture_hsg.csv (Kartograf 0.8.2's "
            "table), compared with the data file by "
            "tests/unit/test_formulas_texture_hsg.py",
        ),
    ),
)


def texture_to_hsg(texture_class: str) -> str:
    """Return the Hydrologic Soil Group of a USDA texture class, spec texture_hsg.

    Parameters
    ----------
    texture_class : str
        USDA texture class name (a key of :data:`TEXTURE_CLASSES`).

    Returns
    -------
    str
        Hydrologic Soil Group letter, from ``"A"`` to ``"D"``.

    Raises
    ------
    InvalidParameterError
        If ``texture_class`` is not a string or not one of the USDA classes.
    """
    x = checked_inputs(TEXTURE_HSG, texture_class=texture_class)
    group = TEXTURE_TO_HSG[x.choice("texture_class")]
    return checked_outputs(TEXTURE_HSG, {"hsg": group}).choice("hsg")


SPECS: Final = (USDA_TEXTURE, TEXTURE_HSG)
"""The Tier A formulas of the module."""


def classify_usda_texture_array(
    clay: ArrayLike, sand: ArrayLike, silt: ArrayLike
) -> NDArray[np.uint8]:
    """
    Classify soil texture for arrays (vectorised), Tier B ``usda_texture_codes``.

    The rows of the spec ``usda_texture``, evaluated cell by cell in ``float64`` on
    the amounts and their total: a share is never computed (``clay / total * 100``
    rounds, so a value exactly on a class limit - silt + 2 * clay = 300 g/kg,
    clay = 270 g/kg - would fall on either side by the rounding). Integers (the g/kg
    of SoilGrids) are therefore classified exactly.

    Parameters
    ----------
    clay : array_like
        Clay amounts (any unit shared by the three arguments, e.g. g/kg or percent).
    sand : array_like
        Sand amounts, in the same unit and of the same shape.
    silt : array_like
        Silt amounts, in the same unit and of the same shape.

    Returns
    -------
    NDArray[np.uint8]
        Texture class codes (1-12, see :data:`TEXTURE_CLASSES`) in the shape of
        the inputs. A cell without soil data - its amounts sum to 0, or one of them
        is NaN or infinite - gets the code of ``loam`` as a placeholder.

    Raises
    ------
    InvalidParameterError
        If the arrays differ in shape, hold non-numeric values or hold a
        negative amount.
    CalculationError
        If rounding leaves a cell with data in no class (non-integer amounts within
        a few units in the last place of a corner of the triangle).

    Notes
    -----
    NaN and infinite amounts and a zero total do not raise: use
    :func:`hydrolog.soil.hsg.classify_hsg` to turn such cells into no data.

    Examples
    --------
    >>> codes = classify_usda_texture_array([5, 55], [90, 25], [5, 20])
    >>> [TEXTURE_NAMES[int(code)] for code in codes]
    ['sand', 'clay']
    >>> classify_usda_texture_array([0, 270], [0, 380], [0, 350]).tolist()  # g/kg
    [4, 8]
    """
    clay_a, sand_a, silt_a = _amounts(clay, sand, silt)
    for name, values in (("clay", clay_a), ("sand", sand_a), ("silt", silt_a)):
        _reject_negative(name, values)
    with np.errstate(invalid="ignore", over="ignore"):
        data = (
            np.isfinite(clay_a)
            & np.isfinite(sand_a)
            & np.isfinite(silt_a)
            & (clay_a + sand_a + silt_a > 0)
        )
        empty = np.zeros_like(clay_a)
        codes = _texture_codes(
            np.where(data, clay_a, empty),
            np.where(data, sand_a, empty),
            np.where(data, silt_a, empty),
        )
    lost = data & (codes == 0)
    if lost.any():
        where = np.unravel_index(int(np.argmax(lost)), lost.shape)
        raise CalculationError(
            f"no texture class holds for clay = {clay_a[where]!r}, sand = "
            f"{sand_a[where]!r}, silt = {silt_a[where]!r}: rounding at a corner "
            "of the triangle",
            details={"formula": USDA_TEXTURE.name, "index": [int(i) for i in where]},
        )
    record(USDA_TEXTURE.name, USDA_TEXTURE.formula_version)
    return np.where(data, codes, _LOAM).astype(np.uint8)


def texture_to_hsg_array(texture: ArrayLike) -> NDArray[np.uint8]:
    """
    Map an array of texture class codes to HSG codes, Tier B ``texture_hsg_codes``.

    The groups of the spec ``texture_hsg`` (:data:`TEXTURE_TO_HSG`) as raster codes.

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
    record(TEXTURE_HSG.name, TEXTURE_HSG.formula_version)
    return np.asarray(_HSG_OF_TEXTURE[codes])


TIER_B: Final = (
    TierBSpec(
        name="usda_texture_codes",
        function="hydrolog.soil.texture.classify_usda_texture_array",
        definition="the class of spec usda_texture, cell by cell, as its code 1-12 "
        "(TEXTURE_CLASSES)",
        convention="a cell without soil data - zero total, a NaN or an infinite "
        "amount - gets the code of loam (4) as a placeholder, which classify_hsg "
        "masks as no data; a negative amount is refused",
        source=_SSM_2017,
    ),
    TierBSpec(
        name="texture_hsg_codes",
        function="hydrolog.soil.texture.texture_to_hsg_array",
        definition="the group of spec texture_hsg of each texture code, as the "
        "raster code 1-4 for A-D",
        convention="texture code 0 (no data) gives 0; a code outside 0-12 is refused",
        source=_TR55_APP_A,
    ),
)
"""The Tier B formulas of the module (CMP-2.2)."""
