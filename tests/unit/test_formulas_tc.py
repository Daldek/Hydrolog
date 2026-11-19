"""The time of concentration formulas against their specs (Nogat CMP §6).

Range, type and property tests are generated from the specs (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/tc-cases.json`` (CMP-6.1); the limits hold
the decimal oracles (CMP-6.2), the power laws and the steps of the low-slope offset. The
functions are given to the assertions through :func:`as_standard` (ADR-0050, point 3).
"""

import warnings
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from hypothesis import given

from hydrolog._formula_versions import recording
from hydrolog._formulas import ERRORS
from hydrolog._warnings import OutsideTypicalRange
from hydrolog.morphometry import WatershedParameters
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
from hydrolog.time import ConcentrationTime
from hydrolog.time.concentration import (
    FAA,
    GIANDOTTI,
    KERBY,
    KERBY_KIRPICH,
    KIRPICH,
    NRCS,
    SPECS,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "tc-cases.json"
FAMILY: tuple[tuple[FormulaSpec, object], ...] = tuple(
    (spec, getattr(ConcentrationTime, spec.name)) for spec in SPECS
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


@given(inputs=strategies(KIRPICH))
def test_kirpich_properties(inputs):
    function = as_standard(ConcentrationTime.kirpich)
    assert_property_contract(KIRPICH, function, inputs, ERRORS)
    assert_properties(KIRPICH, function, inputs, ERRORS)


@given(inputs=strategies(NRCS))
def test_nrcs_properties(inputs):
    function = as_standard(ConcentrationTime.nrcs)
    assert_property_contract(NRCS, function, inputs, ERRORS)
    assert_properties(NRCS, function, inputs, ERRORS)


@given(inputs=strategies(GIANDOTTI))
def test_giandotti_properties(inputs):
    function = as_standard(ConcentrationTime.giandotti)
    assert_property_contract(GIANDOTTI, function, inputs, ERRORS)
    assert_properties(GIANDOTTI, function, inputs, ERRORS)


@given(inputs=strategies(FAA))
def test_faa_properties(inputs):
    function = as_standard(ConcentrationTime.faa)
    assert_property_contract(FAA, function, inputs, ERRORS)
    assert_properties(FAA, function, inputs, ERRORS)


@given(inputs=strategies(KERBY))
def test_kerby_properties(inputs):
    function = as_standard(ConcentrationTime.kerby)
    assert_property_contract(KERBY, function, inputs, ERRORS)
    assert_properties(KERBY, function, inputs, ERRORS)


@given(inputs=strategies(KERBY_KIRPICH))
def test_kerby_kirpich_properties(inputs):
    function = as_standard(ConcentrationTime.kerby_kirpich)
    assert_property_contract(KERBY_KIRPICH, function, inputs, ERRORS)
    assert_properties(KERBY_KIRPICH, function, inputs, ERRORS)


@pytest.mark.parametrize(
    ("length_km", "slope_m_per_m", "cn"),
    [(1.178052, 0.0479, 63.0), (8.2, 0.023, 72.0), (15.88, 0.082, 65.0)],
)
def test_the_nrcs_constant_is_the_exact_metric_one(length_km, slope_m_per_m, cn):
    """TRIAGE T8: in SI units NEH 630-15 eq. 15-4b is 100 / 7068.86 = 0.0141466.

    7068.86 = 1900 * 0.3048**0.8 * 25.4**0.7 exactly; Hydrolog up to 0.8.1 multiplied
    by 0.01416, 0.095 % more on every result (NEH's example: 1.1457 h instead of
    1.1446 h). The constant of the result, tc / (l[m]**0.8 (S[mm] + 25.4)**0.7
    Y[%]**-0.5), must be the exact one.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        tc_min = ConcentrationTime.nrcs(
            length_km=length_km, slope_m_per_m=slope_m_per_m, cn=cn
        )
    with localcontext(prec=50):
        exact = 100 / (
            Decimal(1900)
            * Decimal("0.3048") ** Decimal("0.8")
            * Decimal("25.4") ** Decimal("0.7")
        )
        retention_mm = Decimal(25400) / Decimal(cn) - 254
        factors = (
            (Decimal(length_km) * 1000) ** Decimal("0.8")
            * (retention_mm + Decimal("25.4")) ** Decimal("0.7")
            / (100 * Decimal(slope_m_per_m)).sqrt()
        )
        constant = Decimal(tc_min) / factors

    assert_within(
        float(constant),
        float(exact),
        rel=1e-13,
        reason="the constant of a float64 result against the decimal one at 50 "
        "digits; 0.01416 is 9.5e-4 away",
    )


def test_a_notice_on_a_watershed_names_the_field_of_the_input():
    """The GUI marks a field by ``details.field``: Kirpich's length is the flow path."""
    watershed = WatershedParameters(
        area_km2=37.22, flow_path_length_km=15.88, flow_path_slope_m_per_m=0.0114
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        watershed.calculate_tc("kirpich")

    found = {
        (item.message.details["parameter"], item.message.details["field"])
        for item in caught
        if isinstance(item.message, OutsideTypicalRange)
    }
    assert found == {
        ("area_km2", "area_km2"),
        ("length_km", "flow_path_length_km"),
        ("slope_m_per_m", "flow_path_slope_m_per_m"),
    }


def test_the_formulas_record_their_versions():
    with recording() as used, warnings.catch_warnings():
        warnings.simplefilter("ignore", OutsideTypicalRange)
        ConcentrationTime.kirpich(length_km=1.0, slope_m_per_m=0.05)
        ConcentrationTime.nrcs(length_km=1.0, slope_m_per_m=0.05, cn=70)
        ConcentrationTime.giandotti(
            area_km2=200.0, length_km=20.0, elevation_diff_m=300.0
        )
        ConcentrationTime.faa(length_km=0.1, slope_m_per_m=0.02, runoff_coeff=0.5)
        ConcentrationTime.kerby(length_km=0.1, slope_m_per_m=0.005, retardance=0.4)
        ConcentrationTime.kerby_kirpich(
            overland_length_km=0.1,
            overland_slope_m_per_m=0.005,
            retardance=0.4,
            flow_path_length_km=5.0,
            flow_path_slope_m_per_m=0.005,
        )

    assert used == {spec.name: spec.formula_version for spec in SPECS}
