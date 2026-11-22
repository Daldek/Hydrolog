"""The TR-55 curve number table against its spec and its two transcriptions (CMP-2.5).

``src/hydrolog/_data/tables/tr55_cn.csv`` is accepted when the transcription of the
PDF's text layer (``tests/oracles/tr55_cn_text_layer.csv``) and the table typed for
Hydrolog 0.8.1 (``tests/oracles/tr55_cn_hydrolog_0_8_1.csv``) agree with it cell by
cell, except the rows the spec explains (TRIAGE T12).
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
    run_case,
    type_cases,
)
from hydrolog.runoff import get_cn
from hydrolog.runoff.cn_lookup import TR55_CN, table_curve_number

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

ROOT = Path(__file__).parents[2]
CASES = ROOT / "tests" / "fixtures" / "formulas" / "cn-table-cases.json"
DROPPED = {("row_crops", "fair"), ("small_grain", "fair")}
"""Cells of Hydrolog 0.8.1 without a source: the mean of poor and good."""


def _rows(path: Path) -> dict[tuple[str, str], tuple[str, ...]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            (row["land_cover"], row["condition"]): tuple(row[g] for g in "ABCD")
            for row in csv.DictReader(handle)
        }


TABLE = _rows(ROOT / "src" / "hydrolog" / "_data" / "tables" / "tr55_cn.csv")
TEXT_LAYER = _rows(ROOT / "tests" / "oracles" / "tr55_cn_text_layer.csv")
HYDROLOG_0_8_1 = _rows(ROOT / "tests" / "oracles" / "tr55_cn_hydrolog_0_8_1.csv")


def test_the_table_is_the_text_layer_of_tr55():
    for key, cns in TEXT_LAYER.items():
        assert TABLE[key] == cns, key


def test_herbaceous_is_the_pasture_row_and_water_is_98():
    for condition in ("poor", "fair", "good"):
        assert TABLE[("herbaceous", condition)] == TABLE[("pasture", condition)]
    assert TABLE[("water", "")] == ("98",) * 4


def test_the_typed_table_of_0_8_1_agrees_but_for_the_unsourced_cells():
    assert set(HYDROLOG_0_8_1) - set(TABLE) == DROPPED
    for key, cns in TABLE.items():
        assert HYDROLOG_0_8_1[key] == cns, key


@pytest.mark.parametrize(
    "case", [p.values[0] for p in range_cases(TR55_CN) + type_cases(TR55_CN)]
)
def test_ranges_and_types(case: Case):
    run_case(TR55_CN, as_standard(table_curve_number), case, ERRORS)


@pytest.mark.parametrize(
    "case", load_cases(CASES, "tr55_cn"), ids=lambda case: case.case_id
)
def test_reference_cases(case: ReferenceCase):
    assert_case(TR55_CN, as_standard(table_curve_number), case, ERRORS)


def test_limits():
    assert_limits(TR55_CN, as_standard(table_curve_number), ERRORS)


@pytest.mark.parametrize("cover", ["row_crops", "small_grain"])
def test_a_cover_without_a_fair_row_needs_its_condition(cover):
    """TRIAGE T12: no condition is chosen for the user where TR-55 has no fair row."""
    with pytest.raises(InvalidParameterError) as missing:
        get_cn("B", cover)
    with pytest.raises(InvalidParameterError) as fair:
        get_cn("B", cover, "fair")

    assert missing.value.details == {
        "option": "condition",
        "reason": "required",
        "allowed": ["poor", "good"],
    }
    assert fair.value.details["reason"] == "choice"
    assert fair.value.details["allowed"] == ["poor", "good"]


def test_a_cover_with_a_fair_row_takes_it_without_a_condition():
    assert get_cn("C", "pasture") == get_cn("C", "pasture", "fair") == 79
