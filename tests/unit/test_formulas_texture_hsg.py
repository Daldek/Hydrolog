"""The texture -> HSG table against its spec, its sources and Kartograf's (CMP §6).

``src/hydrolog/_data/tables/texture_hsg.csv`` agrees with TR-55 appendix A read from
the PDF's text layer (``tests/oracles/tr55_hsg_text_layer.csv``) on every row that
cites TR-55, differs from it exactly on the rows the spec documents as deviations,
and equals Kartograf 0.8.2's ``TEXTURE_TO_HSG`` (frozen, CMP-6.4) on all twelve; the
reference cases check each row against the source it cites (CMP-6.1).
"""

import csv
from pathlib import Path

import pytest

from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    ReferenceCase,
    assert_case,
    assert_limits,
    load_cases,
    range_cases,
    read_frozen_oracle,
    run_case,
    type_cases,
)
from hydrolog.soil.texture import (
    TEXTURE_CLASSES,
    TEXTURE_HSG,
    TEXTURE_TO_HSG,
    texture_to_hsg,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "hsg-cases.json"
ORACLES = ROOT / "tests" / "oracles"
DEVIATIONS = {
    "sandy_loam": ("A", "B"),
    "clay_loam": ("D", "C"),
    "silty_clay_loam": ("D", "C"),
}
"""TR-55's group and the table's, where the table follows NEH 630 ch. 7."""


def _table() -> dict[str, dict[str, str]]:
    path = ROOT / "src" / "hydrolog" / "_data" / "tables" / "texture_hsg.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["texture_class"]: row for row in csv.DictReader(handle)}


def _tr55() -> dict[str, str]:
    path = ORACLES / "tr55_hsg_text_layer.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["texture_class"]: row["hsg"] for row in csv.DictReader(handle)}


def test_the_table_is_tr55_appendix_a_but_for_the_documented_rows():
    table, tr55 = _table(), _tr55()

    assert list(table) == list(TEXTURE_CLASSES)
    assert set(tr55) == set(TEXTURE_CLASSES) - {"silt"}
    for name, group in tr55.items():
        row = table[name]
        if name in DEVIATIONS:
            assert (group, row["hsg"]) == DEVIATIONS[name]
            assert row["source"].startswith("NEH 630 ch. 7"), name
        else:
            assert row["hsg"] == group, name
            assert row["source"] == "TR-55 (1986) appendix A, p. A-1", name
    assert table["silt"]["hsg"] == table["silt_loam"]["hsg"] == "B"


def test_kartograf_0_8_2_has_the_same_table():
    oracle = read_frozen_oracle(ORACLES / "kartograf_0_8_2_texture_hsg.csv")

    assert {row["texture_class"]: row["hsg"] for row in oracle.rows} == TEXTURE_TO_HSG


def test_the_order_of_falling_ksat_is_kartografs_rawls_table():
    """The spec's order of Rawls et al. (1982) is that of Kartograf's Ksat values."""
    oracle = read_frozen_oracle(ORACLES / "kartograf_0_8_2_texture_hsg.csv")
    ksat = {
        row["texture_class"]: float(row["rawls_1982_ksat_cm_h"])
        for row in oracle.rows
        if row["texture_class"] != "silt"
    }
    from hydrolog.soil.texture import _FALLING_KSAT

    assert list(_FALLING_KSAT) == sorted(ksat, key=lambda name: -ksat[name])
    assert len(set(ksat.values())) == len(ksat)


@pytest.mark.parametrize(
    "case", [p.values[0] for p in range_cases(TEXTURE_HSG) + type_cases(TEXTURE_HSG)]
)
def test_ranges_and_types(case: Case):
    run_case(TEXTURE_HSG, as_standard(texture_to_hsg), case, ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, "texture_hsg"), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(TEXTURE_HSG, as_standard(texture_to_hsg), case, ERRORS)


def test_limits():
    assert_limits(TEXTURE_HSG, as_standard(texture_to_hsg), ERRORS)


def test_an_unknown_class_is_refused_with_the_choices():
    with pytest.raises(InvalidParameterError) as caught:
        texture_to_hsg("peat")

    assert caught.value.details["reason"] == "invalid_choice"
    assert caught.value.details["option"] == "texture_class"
    assert caught.value.details["choices"] == list(TEXTURE_CLASSES)
