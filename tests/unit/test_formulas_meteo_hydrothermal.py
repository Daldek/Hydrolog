"""Sielianinov's coefficient and its classes against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/meteo-indices-cases.json`` (CMP-6.1); the
limits hold the oracle in exact fractions (CMP-6.2). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import pytest
from hypothesis import given

from hydrolog._formulas import ERRORS
from hydrolog.catalog import run_command
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
from hydrolog.statistics.meteo_hydrothermal import (
    SIELIANINOV,
    SIELIANINOV_CLASS,
    sielianinov_class,
    sielianinov_coefficient,
)

from ._formula_checks import as_standard
from ._warszawa import DATES, TMEAN, P

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "meteo-indices-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (SIELIANINOV, sielianinov_coefficient),
    (SIELIANINOV_CLASS, sielianinov_class),
)


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


@given(inputs=strategies(SIELIANINOV))
def test_coefficient_properties(inputs):
    function = as_standard(sielianinov_coefficient)
    assert_property_contract(SIELIANINOV, function, inputs, ERRORS)
    assert_properties(SIELIANINOV, function, inputs, ERRORS)


@given(inputs=strategies(SIELIANINOV_CLASS))
def test_class_properties(inputs):
    function = as_standard(sielianinov_class)
    assert_property_contract(SIELIANINOV_CLASS, function, inputs, ERRORS)
    assert_properties(SIELIANINOV_CLASS, function, inputs, ERRORS)


def test_the_series_records_the_versions_of_its_formulas():
    envelope = run_command(
        "meteo hydrothermal",
        {
            "dates": [str(day) for day in DATES[:731]],
            "precipitation_mm": P[:731].tolist(),
            "tmean_c": TMEAN[:731].tolist(),
        },
    ).to_dict()

    assert envelope["formula_versions"] == {
        "sielianinov_class": SIELIANINOV_CLASS.formula_version,
        "sielianinov_coefficient": SIELIANINOV.formula_version,
    }
