"""The temperature indices against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/meteo-indices-cases.json`` (CMP-6.1). The
functions are given to the assertions through :func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import numpy as np
import pytest
from hypothesis import given

from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.statistics import degree_days
from hydrolog.statistics.meteo_temperature import DEGREE_DAYS, daily_degree_days

from ._formula_checks import as_standard
from ._warszawa import DATES, TMEAN

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "meteo-indices-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = ((DEGREE_DAYS, daily_degree_days),)


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


def _published() -> list[object]:
    return [
        pytest.param(spec, function, case, id=f"{spec.name}-{case.case_id}")
        for spec, function in FAMILY
        for case in load_cases(CASES, spec.name)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function", "case"), _published())
def test_reference_cases(spec: FormulaSpec, function, case: ReferenceCase):
    assert_case(spec, as_standard(function), case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=lambda x: str(x))
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@given(inputs=strategies(DEGREE_DAYS))
def test_degree_days_properties(inputs):
    function = as_standard(daily_degree_days)
    assert_property_contract(DEGREE_DAYS, function, inputs, ERRORS)
    assert_properties(DEGREE_DAYS, function, inputs, ERRORS)


def test_a_heating_threshold_above_the_reference_temperature_is_refused():
    """CMP-9.1 (2): a limit above the base summed 18 - 19 = -1 a day, -365 a year."""
    days = np.arange(np.datetime64("2001-01-01"), np.datetime64("2002-01-01"))

    with pytest.raises(InvalidParameterError) as caught:
        degree_days(
            days,
            tmean_c=np.full(days.size, 19.0),
            heating_base_c=18.0,
            heating_limit_c=20.0,
        )

    assert caught.value.details["reason"] == "precondition_failed"
    assert caught.value.details["constraint"] == "heating_limit_not_above_base"


def test_the_series_records_the_version_of_its_formula():
    envelope = run_command(
        "meteo temperature",
        {
            "index": "degree_days",
            "dates": [str(day) for day in DATES[:366]],
            "tmean_c": TMEAN[:366].tolist(),
        },
    ).to_dict()

    assert envelope["formula_versions"] == {"degree_days": DEGREE_DAYS.formula_version}
