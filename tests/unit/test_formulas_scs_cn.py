"""The SCS-CN formulas against their specs (Nogat CMP §6): generated and published.

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/scs-cn-cases.json`` (CMP-6.1); the limits
hold the exact rational oracles (CMP-6.2). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import math
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    ReferenceCase,
    assert_case,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.runoff import AMC, SCSCN
from hydrolog.runoff.scs_cn import (
    AMC_CONVERSION,
    RETENTION,
    RUNOFF,
    amc_curve_number,
    potential_retention,
    runoff_depths,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "scs-cn-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (RETENTION, potential_retention),
    (RUNOFF, runoff_depths),
    (AMC_CONVERSION, amc_curve_number),
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


@given(inputs=strategies(RETENTION))
def test_retention_properties(inputs):
    assert_property_contract(
        RETENTION, as_standard(potential_retention), inputs, ERRORS
    )
    assert_properties(RETENTION, as_standard(potential_retention), inputs, ERRORS)


@given(inputs=strategies(RUNOFF))
def test_runoff_properties(inputs):
    assert_property_contract(RUNOFF, as_standard(runoff_depths), inputs, ERRORS)
    assert_properties(RUNOFF, as_standard(runoff_depths), inputs, ERRORS)


@given(inputs=strategies(AMC_CONVERSION))
def test_amc_properties(inputs):
    assert_property_contract(
        AMC_CONVERSION, as_standard(amc_curve_number), inputs, ERRORS
    )
    assert_properties(AMC_CONVERSION, as_standard(amc_curve_number), inputs, ERRORS)


def test_a_missing_value_no_longer_zeroes_the_rest_of_the_storm():
    """TRIAGE T11: a NaN made every later cumulative runoff 0; now it is refused."""
    with pytest.raises(InvalidParameterError) as caught:
        SCSCN(cn=72).effective_precipitation([10.0, math.nan, 30.0, 40.0])

    assert caught.value.details["reason"] == "outside_physical_range"
    assert caught.value.details["option"] == "precipitation_mm"


@pytest.mark.parametrize("depths", [-10.0, [30.0, -20.0, 40.0]])
def test_a_negative_depth_is_refused(depths):
    """TRIAGE T11: a negative depth was taken as no rain; now it is refused."""
    with pytest.raises(InvalidParameterError) as caught:
        SCSCN(cn=72).effective_precipitation(depths)

    assert caught.value.details["reason"] == "outside_physical_range"


def test_a_long_storm_matches_its_total_summed_exactly():
    """Trap many_small_terms: 100 000 steps of 0.001 mm against one exact total."""
    steps = np.full(100_000, 0.001)
    exact_total = math.fsum(steps)

    storm = runoff_depths(steps, 98.0, 0.2)
    single = runoff_depths([exact_total], 98.0, 0.2)

    assert_within(
        storm.total_effective_mm,
        single.total_effective_mm,
        rel=1e-9,
        reason="the cumulative sum of 1e5 steps differs from fsum by about 1e5 ulp "
        "of 100 mm, below 2e-9 mm",
    )


def test_the_amc_conversion_stays_within_its_stated_deviation_from_neh_table():
    """The deviation the spec of scs_cn_amc declares against NEH 630-10 table 10-1.

    A hand-written test: the generator compares a formula with one published value
    per case, not a whole table with a bound (CMP-6.5).
    """
    cases = {
        (case.inputs["amc"], case.inputs["cn"]): case.expected["cn_adjusted"]
        for case in load_cases(CASES, "scs_cn_amc")
        if case.case_id.startswith("neh630")
    }

    for (amc, cn), table in cases.items():
        assert abs(amc_curve_number(float(cn), str(amc)) - int(table)) <= (
            2 if amc == "I" else 1
        )


def test_the_wrapper_keeps_a_total_a_number_and_a_series_an_array():
    total = SCSCN(cn=72).effective_precipitation(50.0)
    series = SCSCN(cn=72).effective_precipitation([10.0, 15.0, 25.0])

    assert isinstance(total.effective_mm, float)
    assert isinstance(series.effective_mm, np.ndarray)
    assert_within(
        float(np.sum(series.effective_mm)),
        total.total_effective_mm,
        rel=1e-12,
        reason="the same 50 mm in one or three steps: only the order of the sums "
        "differs",
    )


def test_amc_ii_keeps_the_cn_and_i_and_iii_convert_it():
    scs = SCSCN(cn=72)

    assert scs.adjust_cn_for_amc(AMC.II) == 72
    assert scs.adjust_cn_for_amc(AMC.I) == 53
    assert scs.adjust_cn_for_amc(AMC.III) == 86


def test_the_formulas_record_their_versions():
    with recording() as used:
        SCSCN(cn=80).effective_precipitation(50.0, amc=AMC.III)

    assert used == {
        "scs_cn_amc": AMC_CONVERSION.formula_version,
        "scs_cn_retention": RETENTION.formula_version,
        "scs_cn_runoff": RUNOFF.formula_version,
    }
