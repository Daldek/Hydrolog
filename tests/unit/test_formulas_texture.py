"""The USDA texture classification against its spec, its table and its oracles (CMP §6).

Range, type and property tests are generated from the spec ``usda_texture``
(CMP-6.5); the reference cases are the Soil Survey Manual's (2017) of
``tests/fixtures/formulas/texture-cases.json`` (CMP-6.1); the table is compared with
its two transcriptions (CMP-2.5); Kartograf 0.8.2's classifier, run once on every
integer composition in percent and in g/kg, is the frozen oracle (CMP-6.4) and the
table evaluated in exact rationals the oracle of a different form (CMP-6.2). The
traps of the family (CMP-6.6) are the class limits and gaps.
"""

import csv
import functools
import math
import warnings
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    load_cases,
    range_cases,
    read_frozen_oracle,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.soil.hsg import classify_hsg
from hydrolog.soil.texture import (
    TEXTURE_CLASSES,
    TEXTURE_NAMES,
    USDA_TEXTURE,
    classify_usda_texture,
    classify_usda_texture_array,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "texture-cases.json"
ORACLES = ROOT / "tests" / "oracles"
TABLE = ROOT / "src" / "hydrolog" / "_data" / "tables" / "usda_texture_classes.csv"
LOAM = TEXTURE_CLASSES["loam"]

Row = tuple[str, int, Fraction, Fraction, Fraction, str, Fraction, int]
"""Class, alternative, clay, sand and silt coefficients, relation, percent, page."""


def _rows(path: Path) -> set[Row]:
    """The rows of a transcription as a set, numbers as exact fractions."""
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            (
                row["texture_class"],
                int(row["alternative"]),
                Fraction(row["clay"]),
                Fraction(row["sand"]),
                Fraction(row["silt"]),
                row["relation"],
                Fraction(row["percent"]),
                int(row["page"]),
            )
            for row in csv.DictReader(handle)
        }


_RELATIONS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}
TABLE_ROWS = sorted(_rows(TABLE), key=str)
"""The rows of the package table, in a fixed order."""


def _rational_class(clay: int, sand: int, silt: int) -> list[str]:
    """The classes whose rows hold, from the package table, in exact rationals.

    A different form from the code: shares as fractions of the total, each row
    ``a clay% + b sand% + c silt% <relation> k`` read literally.
    """
    total = Fraction(clay + sand + silt)
    share = {
        "clay": 100 * Fraction(clay) / total,
        "sand": 100 * Fraction(sand) / total,
        "silt": 100 * Fraction(silt) / total,
    }
    holds: dict[tuple[str, int], bool] = {}
    for name, alternative, a, b, c, relation, k, _ in TABLE_ROWS:
        value = a * share["clay"] + b * share["sand"] + c * share["silt"]
        key = (name, alternative)
        holds[key] = holds.get(key, True) and _RELATIONS[relation](value, k)
    return sorted({name for (name, _), held in holds.items() if held})


@functools.cache
def _grid(total: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Every integer (clay, sand, silt) with the given sum, clay then sand rising."""
    clay = np.repeat(np.arange(total + 1), np.arange(total + 1, 0, -1))
    sand = np.concatenate([np.arange(total + 1 - c) for c in range(total + 1)])
    return clay, sand, total - clay - sand


def _expanded_gkg() -> Iterator[tuple[int, int, int]]:
    """(clay, sand, code) of every g/kg composition of Kartograf's run-length file."""
    oracle = read_frozen_oracle(ORACLES / "kartograf_0_8_2_texture_gkg.csv")
    for row in oracle.rows:
        clay, start, end = int(row["clay"]), int(row["sand_from"]), int(row["sand_to"])
        for sand in range(start, end + 1):
            yield clay, sand, int(row["code"])


# --- the table and its transcriptions (CMP-2.5) -----------------------------------


def test_the_table_is_both_transcriptions_of_the_manual():
    """The data file equals the two independent transcriptions, row for row."""
    table = _rows(TABLE)
    first = _rows(ORACLES / "usda_texture_classes_first.csv")
    second = _rows(ORACLES / "usda_texture_classes_second.csv")

    assert first == second
    assert table == first
    assert len(table) == 41
    assert {row[0] for row in table} == set(TEXTURE_CLASSES)


@pytest.mark.parametrize("total", [100, 1000])
def test_the_classes_partition_the_triangle(total):
    """Every integer composition satisfies the rows of exactly one class."""
    clay, sand, silt = _grid(total)
    step = 1 if total == 100 else 97  # a sample of the g/kg grid in rationals
    for c, s, si in list(zip(clay, sand, silt, strict=True))[::step]:
        assert len(_rational_class(int(c), int(s), int(si))) == 1, (c, s, si)


# --- oracles (CMP-6.2, CMP-6.4) -----------------------------------------------------


def test_kartograf_0_8_2_on_every_integer_percent_composition():
    oracle = read_frozen_oracle(ORACLES / "kartograf_0_8_2_texture_percent.csv")
    clay, sand, silt = (oracle.floats(name) for name in ("clay", "sand", "silt"))

    codes = classify_usda_texture_array(clay, sand, silt)

    assert oracle.metadata["classes"] == " ".join(
        f"{code}={name}" for name, code in TEXTURE_CLASSES.items()
    )
    assert len(oracle.rows) == 5151
    assert codes.tolist() == oracle.floats("code").astype(int).tolist()


def test_kartograf_0_8_2_on_every_integer_g_per_kg_composition():
    expanded = np.array(list(_expanded_gkg()), dtype=np.int64)
    clay, sand, silt = _grid(1000)

    codes = classify_usda_texture_array(clay, sand, 1000 - clay - sand)

    assert len(expanded) == 501501
    assert expanded[:, 0].tolist() == clay.tolist()
    assert expanded[:, 1].tolist() == sand.tolist()
    assert codes.tolist() == expanded[:, 2].tolist()
    assert (silt >= 0).all()


def test_the_percent_grid_times_ten_is_a_subgrid_of_the_g_per_kg_grid():
    percent = read_frozen_oracle(ORACLES / "kartograf_0_8_2_texture_percent.csv")
    gkg = {(clay, sand): code for clay, sand, code in _expanded_gkg()}

    for row in percent.rows:
        assert gkg[(10 * int(row["clay"]), 10 * int(row["sand"]))] == int(row["code"])


def test_the_table_in_rationals_agrees_on_the_percent_grid():
    clay, sand, silt = _grid(100)

    codes = classify_usda_texture_array(clay, sand, silt)

    expected = [
        TEXTURE_CLASSES[_rational_class(int(c), int(s), int(si))[0]]
        for c, s, si in zip(clay, sand, silt, strict=True)
    ]
    assert codes.tolist() == expected


@given(
    st.tuples(
        st.integers(0, 10**6), st.integers(0, 10**6), st.integers(0, 10**6)
    ).filter(lambda amounts: sum(amounts) > 0)
)
@example((200, 600, 200))
@example((270, 380, 350))
@example((0, 0, 1))
def test_the_table_in_rationals_agrees(amounts):
    """On drawn integer amounts, scalar and array agree with the exact rationals."""
    clay, sand, silt = amounts
    found = _rational_class(clay, sand, silt)

    assert found == [classify_usda_texture(clay=clay, sand=sand, silt=silt)]
    assert TEXTURE_NAMES[int(classify_usda_texture_array(clay, sand, silt))] == found[0]


# --- generated tests (CMP-6.5) -------------------------------------------------------


@pytest.mark.parametrize(
    "case", [p.values[0] for p in range_cases(USDA_TEXTURE) + type_cases(USDA_TEXTURE)]
)
def test_ranges_and_types(case: Case):
    run_case(USDA_TEXTURE, as_standard(classify_usda_texture), case, ERRORS)


@given(inputs=strategies(USDA_TEXTURE))
def test_properties(inputs):
    function = as_standard(classify_usda_texture)
    assert_property_contract(USDA_TEXTURE, function, inputs, ERRORS)
    assert_properties(USDA_TEXTURE, function, inputs, ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, "usda_texture"), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(USDA_TEXTURE, as_standard(classify_usda_texture), case, ERRORS)


def test_limits():
    assert_limits(USDA_TEXTURE, as_standard(classify_usda_texture), ERRORS)


# --- traps (CMP-6.6) ------------------------------------------------------------------


def _at_limit(row: Row) -> list[tuple[int, int, int]]:
    """Integer g/kg compositions on the line of a row: a clay + b sand + c silt = k."""
    _, _, a, b, c, _, k, _ = row
    clay, sand, silt = _grid(1000)
    twice = (2 * Fraction(x) for x in (a, b, c))  # whole numbers: 0, 2, 3 or 4
    weights = [int(x) for x in twice]
    line = weights[0] * clay + weights[1] * sand + weights[2] * silt == int(20 * k)
    return [
        (int(x), int(y), int(z))
        for x, y, z in zip(clay[line], sand[line], silt[line], strict=True)
    ]


@pytest.mark.parametrize(
    "row",
    TABLE_ROWS,
    ids=lambda row: f"{row[0]}-{row[1]}-{row[5]}{row[6]}",
)
def test_every_row_of_the_table_at_its_limit_and_just_beyond(row):
    """On the limit of a row and one g/kg of clay or sand beyond, the class is exact.

    The points lie on the line a clay + b sand + c silt = k of the row (integer
    g/kg, every seventeenth); the code must give the class of the rows read
    literally in rationals, so an inclusive bound (``<=``, ``>=``) keeps the point
    in its class and an exclusive one (``<``, ``>``) puts it in the neighbour.
    """
    points = list(_at_limit(row))[::17]
    assert points, row
    for clay, sand, silt in points:
        for moved in (
            (clay, sand, silt),
            (clay + 1, sand - 1, silt),
            (clay, sand + 1, silt - 1),
        ):
            if min(moved) < 0:
                continue
            assert classify_usda_texture(*moved) == _rational_class(*moved)[0], moved


@pytest.mark.parametrize(
    ("clay", "sand", "silt", "on", "below"),
    [
        (20.0, 60.0, 20.0, "sandy_clay_loam", "sandy_loam"),
        (27.0, 38.0, 35.0, "clay_loam", "loam"),
    ],
)
def test_clay_twenty_and_twenty_seven_percent_belong_to_the_clayier_class(
    clay, sand, silt, on, below
):
    """TRIAGE T17: 'to less than 20' and 'to less than 27' exclude the bound.

    A composition a resolvable distance below the bound is in the other class; one
    unit in the last place of a non-integer amount may fall on either side (a
    convention of the spec).
    """
    assert classify_usda_texture(clay, sand, silt) == on
    assert classify_usda_texture(math.nextafter(clay, 0), sand, silt) == below
    assert classify_usda_texture(clay, sand, silt + 1e-9) == below


def test_a_gap_is_refused_or_kept_as_no_data():
    """NaN is refused by the spec; the array variant keeps no-data cells as loam."""
    with pytest.raises(InvalidParameterError) as caught:
        classify_usda_texture(clay=math.nan, sand=40.0, silt=40.0)
    nan, inf = math.nan, math.inf

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        codes = classify_usda_texture_array(
            [nan, 5.0, inf, 0.0, 45.0],
            [40.0, nan, 1.0, 0.0, 20.0],
            [40.0, 5.0, 1.0, 0.0, 35.0],
        )
        groups = classify_hsg(
            [nan, 5.0, inf, 0.0, 45.0],
            [40.0, nan, 1.0, 0.0, 20.0],
            [40.0, 5.0, 1.0, 0.0, 35.0],
        )

    assert caught.value.details["reason"] == "outside_physical_range"
    assert codes.tolist() == [LOAM, LOAM, LOAM, LOAM, TEXTURE_CLASSES["clay"]]
    assert groups.tolist() == [0, 0, 0, 0, 4]


# --- behaviour changed by the spec ---------------------------------------------------


def test_a_zero_total_is_refused_not_loam():
    """The class of no soil is undefined: precondition positive_total (ADR-0066)."""
    with pytest.raises(InvalidParameterError) as caught:
        classify_usda_texture(clay=0, sand=0, silt=0)

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "positive_total"


def test_huge_amounts_are_classified_without_overflow():
    big = 1e307
    assert classify_usda_texture(clay=4 * big, sand=4 * big, silt=2 * big) == "clay"


def test_the_formulas_record_their_versions():
    with recording() as scalar:
        classify_usda_texture(clay=20, sand=40, silt=40)
    with recording() as array:
        classify_usda_texture_array([20], [40], [40])
    with recording() as groups:
        classify_hsg([20], [40], [40])

    assert scalar == array == {"usda_texture": 1}
    assert groups == {"usda_texture": 1, "texture_hsg": 1}
