"""Lutz's estimation of Nash's n and K against its spec (Nogat CMP §6).

Range, type and property tests are generated from the spec (CMP-6.5); the reference
cases are those of ``tests/fixtures/formulas/lutz-cases.json`` (CMP-6.1), the second a
discrepancy skipped with its cause (CMP-5.2); the limits hold the decimal oracle
(CMP-6.2), the gamma density of scipy.stats (CMP-6.3) and the power laws. The function
is given to the assertions through :func:`as_standard` (ADR-0050, point 3).
"""

from pathlib import Path

import pytest
from hypothesis import given
from scipy.optimize import brentq

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
    assert_within,
    load_cases,
    range_cases,
    run_case,
    strategies,
    type_cases,
)
from hydrolog.runoff import NashIUH
from hydrolog.runoff.nash_iuh import (
    LUTZ,
    URBAN,
    _peak_product,
    lutz_parameters,
    urban_regression_parameters,
)

from ._formula_checks import as_standard

pytestmark = pytest.mark.formula

CASES = Path(__file__).parents[1] / "fixtures" / "formulas" / "lutz-cases.json"
EXAMPLE = {
    "L_km": 4.3,
    "Lc_km": 2.7,
    "slope": 0.03,
    "manning_n": 0.025,
    "urban_pct": 0.0,
    "forest_pct": 33.6,
}
"""KZGW (2017) Ex. 6.2 as the arguments of ``NashIUH.from_lutz``."""


@pytest.mark.parametrize("case", range_cases(LUTZ) + type_cases(LUTZ))
def test_ranges_and_types(case: Case):
    run_case(LUTZ, as_standard(lutz_parameters), case, ERRORS)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in load_cases(CASES, "lutz")]
)
def test_reference_cases(case: ReferenceCase):
    assert_case(LUTZ, as_standard(lutz_parameters), case, ERRORS)


def test_limits_and_oracles():
    assert_limits(LUTZ, as_standard(lutz_parameters), ERRORS)


@given(inputs=strategies(LUTZ))
def test_lutz_properties(inputs):
    function = as_standard(lutz_parameters)
    assert_property_contract(LUTZ, function, inputs, ERRORS)
    assert_properties(LUTZ, function, inputs, ERRORS)


def test_the_delegated_root_finder_finds_a_known_root():
    """DELEGATED nash_shape_root: brentq finds N = 2.55 from f(2.55) on [1.1, 20]."""
    target = _peak_product(2.55)

    root = brentq(lambda n: _peak_product(n) - target, 1.1, 20.0, xtol=1e-6)

    assert_within(
        root,
        2.55,
        abs=1e-6,
        reason="brentq stops within xtol = 1e-6 of the root (scipy.optimize.brentq)",
    )


@pytest.mark.parametrize(
    ("n", "printed"),
    [
        (1.10, 0.076),
        (1.50, 0.242),
        (2.00, 0.368),
        (2.55, 0.471),
        (3.00, 0.541),
        (3.50, 0.610),
        (3.88, 0.658),
        (4.00, 0.672),
        (4.50, 0.729),
        (5.00, 0.781),
        (6.00, 0.877),
        (7.00, 0.964),
        (7.99, 1.042),
    ],
)
def test_the_shape_function_matches_kzgw_table_c2(n, printed):
    """KZGW (2017), Table C.2, pp. 132-133: f(N) = tp up, printed to 3 decimals."""
    assert_within(
        _peak_product(n),
        printed,
        abs=0.0005,
        reason="half a unit of the table's third decimal",
    )


def test_the_shares_of_urban_and_forest_land_cannot_exceed_the_area():
    """TRIAGE T2: U + W > 100 % was computed before 0.9.0; it is refused now."""
    with pytest.raises(InvalidParameterError) as caught:
        NashIUH.from_lutz(**{**EXAMPLE, "urban_pct": 40.0, "forest_pct": 61.0})

    details = caught.value.details
    assert (details["reason"], details["constraint"], details["option"]) == (
        "outside_physical_range",
        "shares_within_catchment",
        "forest_pct",
    )


@pytest.mark.parametrize(
    ("argument", "value", "reason"),
    [
        ("L_km", float("nan"), "outside_physical_range"),
        ("Lc_km", float("inf"), "outside_physical_range"),
        ("slope", 0.0, "outside_physical_range"),
        ("manning_n", True, "invalid_type"),
        ("urban_pct", -0.5, "outside_physical_range"),
        ("urban_pct", 150.0, "outside_physical_range"),
        ("forest_pct", -5.0, "outside_physical_range"),
        ("Lc_km", 0.0, "outside_physical_range"),
        ("manning_n", 0.0, "outside_physical_range"),
    ],
)
def test_a_refusal_names_the_argument_of_from_lutz(argument, value, reason):
    with pytest.raises(InvalidParameterError) as caught:
        NashIUH.from_lutz(**{**EXAMPLE, argument: value})

    assert (caught.value.details["option"], caught.value.details["reason"]) == (
        argument,
        reason,
    )


def test_a_centroid_beyond_the_main_stream_is_refused_on_lc():
    with pytest.raises(InvalidParameterError) as caught:
        NashIUH.from_lutz(**{**EXAMPLE, "Lc_km": 4.4})

    details = caught.value.details
    assert (details["option"], details["constraint"]) == (
        "Lc_km",
        "centroid_within_length",
    )


def test_from_lutz_gives_the_estimate_of_the_spec():
    with recording() as versions:
        cascade = NashIUH.from_lutz(**EXAMPLE)
    estimate = lutz_parameters(
        length_km=4.3,
        centroid_length_km=2.7,
        slope_m_per_m=0.03,
        manning_n=0.025,
        urban_pct=0.0,
        forest_pct=33.6,
    )

    assert (cascade.n, cascade.k_min) == (estimate.n, estimate.k_min)
    assert versions == {"lutz": 1}


# --- the urban regression of Rao, Delleur and Sarma (spec nash_urban_regression) ---


@pytest.mark.parametrize("case", range_cases(URBAN) + type_cases(URBAN))
def test_urban_ranges_and_types(case: Case):
    run_case(URBAN, as_standard(urban_regression_parameters), case, ERRORS)


def test_urban_limits_and_oracles():
    assert_limits(URBAN, as_standard(urban_regression_parameters), ERRORS)


@given(inputs=strategies(URBAN))
def test_urban_properties(inputs):
    function = as_standard(urban_regression_parameters)
    assert_property_contract(URBAN, function, inputs, ERRORS)
    assert_properties(URBAN, function, inputs, ERRORS)


def test_from_urban_regression_gives_the_estimate_of_the_spec():
    with recording() as used:
        cascade = NashIUH.from_urban_regression(
            area_km2=26.9, effective_precip_mm=10.0, duration_h=1.0, urban_fraction=0.32
        )
    estimate = urban_regression_parameters(26.9, 10.0, 1.0, 0.32)

    assert (cascade.n, cascade.k_min) == (estimate.n, estimate.k_min)
    assert used == {"nash_urban_regression": URBAN.formula_version}


def test_an_impervious_fraction_of_one_is_refused():
    with pytest.raises(InvalidParameterError) as caught:
        NashIUH.from_urban_regression(1.3, 1.305, 0.167, urban_fraction=1.0)

    assert caught.value.details["reason"] == "outside_physical_range"
    assert caught.value.details["option"] == "urban_fraction"
