"""The areal precipitation formulas against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/areal-precipitation-cases.json``
(CMP-6.1); the limits hold the exact oracles (CMP-6.2). The functions are given to the
assertions through :func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

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
from hydrolog.precipitation import (
    Station,
    arithmetic_mean,
    inverse_distance_weighting,
    isohyet_method,
    thiessen_polygons,
)
from hydrolog.precipitation.interpolation import (
    AREAL_MEAN,
    IDW,
    ISOHYET,
    THIESSEN,
    areal_mean_precipitation,
    idw_precipitation,
    isohyet_precipitation,
    thiessen_precipitation,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = (
    Path(__file__).parents[1]
    / "fixtures"
    / "formulas"
    / "areal-precipitation-cases.json"
)
FAMILY: tuple[tuple[FormulaSpec, object], ...] = (
    (AREAL_MEAN, areal_mean_precipitation),
    (THIESSEN, thiessen_precipitation),
    (IDW, idw_precipitation),
    (ISOHYET, isohyet_precipitation),
)
NAMES = [spec.name for spec, _ in FAMILY]


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


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_limits_and_oracles(spec: FormulaSpec, function):
    assert_limits(spec, as_standard(function), ERRORS)


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_drawn_inputs_keep_the_contract(spec: FormulaSpec, function):
    @given(inputs=strategies(spec))
    def check(inputs):
        assert_property_contract(spec, as_standard(function), inputs, ERRORS)
        assert_properties(spec, as_standard(function), inputs, ERRORS)

    check()


_DEPTH = st.floats(0.0, 1825.0)
_AREA = st.floats(0.0, 1.0e4)
_COORDINATE = st.floats(-1.0e6, 1.0e6)


@st.composite
def _gauges(draw: st.DrawFn, spec: FormulaSpec) -> dict[str, object]:
    """Inputs whose arrays agree in length, with some area or zone."""
    count = draw(st.integers(1, 40))
    depths = draw(st.lists(_DEPTH, min_size=count, max_size=count))
    if spec is THIESSEN:
        areas = draw(st.lists(_AREA, min_size=count, max_size=count))
        return {"precipitation_mm": depths, "polygon_areas_km2": [*areas[:-1], 1.0]}
    if spec is ISOHYET:
        zones = draw(st.lists(_AREA, min_size=count, max_size=count))
        return {
            "isohyet_values_mm": [*depths, draw(_DEPTH)],
            "zone_areas_km2": [*zones[:-1], 1.0],
        }
    if spec is IDW:
        return {
            "station_x_m": draw(st.lists(_COORDINATE, min_size=count, max_size=count)),
            "station_y_m": draw(st.lists(_COORDINATE, min_size=count, max_size=count)),
            "precipitation_mm": depths,
            "target_x_m": draw(_COORDINATE),
            "target_y_m": draw(_COORDINATE),
            "power": draw(st.floats(0.1, 100.0)),
        }
    return {"precipitation_mm": depths}


@pytest.mark.parametrize(("spec", "function"), FAMILY, ids=NAMES)
def test_gauges_that_agree_keep_their_properties(spec: FormulaSpec, function):
    """Hand-written: the generator draws each array apart, so nearly every draw of a
    formula of several arrays fails the precondition on their lengths; here they
    agree and the properties are exercised."""

    @given(inputs=_gauges(spec))
    def check(inputs):
        assert_property_contract(spec, as_standard(function), inputs, ERRORS)
        assert_properties(spec, as_standard(function), inputs, ERRORS)

    check()


def test_a_large_power_no_longer_overflows():
    """Ordinary defect: d**p raised OverflowError (p = 200, d of 500 m) and an
    underflow ZeroDivisionError (d = 1e-9 m, p = 40); the weights are relative to the
    nearest gauge now."""
    gauges = [Station("A", 500.0, 0.0, 10.0), Station("B", 0.0, 700.0, 20.0)]
    far = inverse_distance_weighting(gauges, 0.0, 0.0, power=200.0)
    near = inverse_distance_weighting(
        [Station("A", 1e-9, 0.0, 10.0), Station("B", 2e-9, 0.0, 20.0)],
        0.0,
        0.0,
        power=40.0,
    )

    assert_within(
        far.areal_precipitation_mm,
        10.0,
        abs=1e-12,
        reason="(500/700)^200 = 1e-29: the far gauge's weight vanishes",
    )
    assert_within(
        near.areal_precipitation_mm,
        (10.0 + 20.0 * 2.0**-40) / (1.0 + 2.0**-40),
        rel=1e-14,
        reason="the weights 1 and 2^-40 of distances 1e-9 and 2e-9 m",
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda: arithmetic_mean([Station("A", 0, 0, -5.0), Station("B", 1, 0, 20.0)]),
        lambda: thiessen_polygons(
            [Station("A", 0, 0, 10.0), Station("B", 1, 0, 20.0)], {"A": -1.0, "B": 2.0}
        ),
        lambda: isohyet_method(np.array([-10.0, 10.0]), np.array([1.0])),
        lambda: inverse_distance_weighting([Station("A", 0, 0, float("nan"))], 1, 1),
    ],
    ids=["negative-depth", "negative-area", "negative-isohyet", "nan-depth"],
)
def test_impossible_values_are_refused(call):
    """Ordinary defects: a negative depth, area or isohyet and a NaN gave a result."""
    with pytest.raises(InvalidParameterError) as caught:
        call()

    assert caught.value.details["reason"] == "outside_physical_range"


def test_isohyet_fractions_that_miss_one_are_weighted_by_their_sum():
    """The fractions within 1e-3 of one were not renormalised (a bias up to 0.1 %);
    the zones are weighted by their share of the sum now (KZGW 2017, eq. 2.2)."""
    result = isohyet_method(np.array([10.0, 20.0, 40.0]), np.array([0.5, 0.4995]))

    assert_within(
        result.areal_precipitation_mm,
        (15.0 * 0.5 + 30.0 * 0.4995) / 0.9995,
        rel=1e-15,
        reason="the area-weighted mean of the two zones, rounded once per term",
    )


def test_the_functions_compute_through_the_specs_and_record_their_versions():
    gauges = [Station("A", 0.0, 0.0, 25.0), Station("B", 10.0, 0.0, 35.0)]
    with recording() as used:
        arithmetic_mean(gauges)
        thiessen_polygons(gauges, {"A": 1.0, "B": 3.0})
        inverse_distance_weighting(gauges, 3.0, 0.0)
        isohyet_method(np.array([10.0, 20.0]), np.array([1.0]))

    assert used == {
        spec.name: spec.formula_version for spec in (AREAL_MEAN, THIESSEN, IDW, ISOHYET)
    }
