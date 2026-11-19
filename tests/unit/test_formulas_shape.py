"""The shape indicators of a watershed against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the limits hold
the decimal oracles, the exact shapes and the identities between the indicators
(CMP-6.2). No open source prints a worked example of them, so they are ``oracle
only``.
"""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog.exceptions import InvalidParameterError
from hydrolog.morphometry import WatershedGeometry
from hydrolog.morphometry.geometric import (
    SPECS,
    circularity_ratio,
    compactness_coefficient,
    elongation_ratio,
    form_factor,
    lemniscate_ratio,
)
from hydrolog.nogat_formulas import (
    Case,
    FormulaSpec,
    assert_limits,
    assert_properties,
    assert_property_contract,
    assert_within,
    range_cases,
    run_case,
    strategies,
    type_cases,
)

pytestmark = pytest.mark.formula

FUNCTIONS = {
    "form_factor": form_factor,
    "compactness_coefficient": compactness_coefficient,
    "circularity_ratio": circularity_ratio,
    "elongation_ratio": elongation_ratio,
    "lemniscate_ratio": lemniscate_ratio,
}
FAMILY = tuple((spec, FUNCTIONS[spec.name]) for spec in SPECS)


def _generated() -> list[object]:
    return [
        pytest.param(spec, function, case.values[0], id=f"{spec.name}-{case.id}")
        for spec, function in FAMILY
        for case in range_cases(spec) + type_cases(spec)
    ]


@pytest.mark.parametrize(("spec", "function", "case"), _generated())
def test_ranges_and_types(spec: FormulaSpec, function, case: Case):
    run_case(spec, function, case, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s in SPECS])
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, function, ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=[s.name for s in SPECS])
@given(data=st.data())
def test_properties(spec: FormulaSpec, function, data):
    inputs = data.draw(strategies(spec))
    assert_property_contract(spec, function, inputs, ERRORS)
    assert_properties(spec, function, inputs, ERRORS)


def test_the_watershed_gives_the_formulas_of_its_inputs():
    geometry = WatershedGeometry(area_km2=37.22, perimeter_km=40.89, length_km=16.05)

    indicators = geometry.get_shape_indicators()

    assert indicators.form_factor == form_factor(37.22, 16.05)
    assert indicators.compactness_coefficient == compactness_coefficient(37.22, 40.89)
    assert indicators.circularity_ratio == circularity_ratio(37.22, 40.89)
    assert indicators.elongation_ratio == elongation_ratio(37.22, 16.05)
    assert indicators.lemniscate_ratio == lemniscate_ratio(37.22, 16.05)


@pytest.mark.parametrize(
    ("inputs", "formula", "constraint"),
    [
        # a perimeter shorter than the circle's of the same area: A and P of
        # different outlines
        (
            {"area_km2": 45.0, "perimeter_km": 23.0, "length_km": 12.0},
            "compactness_coefficient",
            "isoperimetric",
        ),
        # an area larger than the circle of radius L about the outlet
        (
            {"area_km2": 45.0, "perimeter_km": 32.0, "length_km": 3.0},
            "form_factor",
            "within_reach",
        ),
    ],
)
def test_an_impossible_watershed_is_refused(inputs, formula, constraint):
    with pytest.raises(InvalidParameterError) as refused:
        WatershedGeometry(**inputs)

    assert refused.value.details["reason"] == "outside_physical_range"
    assert refused.value.details["formula"] == formula
    assert refused.value.details["constraint"] == constraint


def test_a_circle_is_the_reference_of_the_indicators():
    """A circle of diameter L: Cz = Ck = Ce = k = 1 and Cf = pi/4 (the sources'
    anchor of each index)."""
    geometry = WatershedGeometry(
        area_km2=math.pi * 4.0, perimeter_km=math.pi * 4.0, length_km=4.0
    )

    indicators = geometry.get_shape_indicators()

    for value, exact in (
        (indicators.compactness_coefficient, 1.0),
        (indicators.circularity_ratio, 1.0),
        (indicators.elongation_ratio, 1.0),
        (indicators.lemniscate_ratio, 1.0),
        (indicators.form_factor, math.pi / 4.0),
    ):
        assert_within(
            value, exact, rel=2e-15, reason="the float circle: pi rounded once"
        )


def test_the_formulas_record_their_versions():
    with recording() as used:
        WatershedGeometry(45.0, 32.0, 12.0).get_shape_indicators()

    assert used == {spec.name: spec.formula_version for spec in SPECS}
