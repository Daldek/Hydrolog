"""KZGW 2017's reference cases of quantile_interval_delta (Nogat CMP-6.1).

The cases of ``tests/fixtures/formulas/flood-interval-cases.json``: the upper
bounds of KZGW's one-sided 84 % intervals (example 3.2, table 3.9; example 3.3, table
3.12; table 2.3), each case with its printed precision, the source's intermediate
roundings and its conventions. The function is given to the assertion through
:func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import pytest

from hydrolog._formulas import ERRORS
from hydrolog.nogat_formulas import ReferenceCase, assert_case, load_cases
from hydrolog.statistics.intervals import (
    QUANTILE_INTERVAL_DELTA,
    quantile_interval_delta,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

TESTS = Path(__file__).parents[1]
CASES = TESTS / "fixtures" / "formulas" / "flood-interval-cases.json"


@pytest.mark.parametrize(
    "case",
    load_cases(CASES, QUANTILE_INTERVAL_DELTA.name),
    ids=lambda case: case.case_id,
)
def test_reference_cases(case: ReferenceCase):
    assert_case(
        QUANTILE_INTERVAL_DELTA, as_standard(quantile_interval_delta), case, ERRORS
    )
